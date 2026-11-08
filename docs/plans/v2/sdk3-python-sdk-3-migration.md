# Packet SDK3 — Python SDK `surrealdb` 2.0.0 → 3.0.0 (on the 3.3.5 stores)

Status: CONTRACT ROUND 8 (MP-1, F6 gate contract, landmine 1 staged, cumulative inventory — §ROUND 8, newest first). Previously: CONTRACT ROUND 7 (R18/R20 native retry, R19 routing, R21/R22, R26 — §ROUND 7). Previously: CONTRACT ROUND 5 (R11 tenacity + R12 F18/C9-class/F-a/F-b/F-d/F22/X18/X19/RS7 — §ROUND 5, newest first). Previously: CONTRACT ROUND 4 (adversary round 1's MP1–MP3 + R9 D1–D3 + residuals closed — §ROUND 4, newest first). Previously: CONTRACT ROUND 3 (rulings R2–R7 pinned; §ROUND 3 below supersedes the round-1/2 forks — the round-1/2 sections stay as history). Round 1: DISCOVERY + CONTRACT (tdd Phase 0 + Phase 1), written 2026-11-07 by the SDK3 contract author
against HEAD `4624daf` (branch `feat/surreal-unification`; the brief named `c05bf3f`, HEAD moved
under another builder's commit while this ran), SDK 2.0.0 in lore's venv, SDK 3.0.0 in the
research40 scratch venv. Operator approved the packet 2026-11-07. **This contract STOPS for operator
review** (§5 forks); then `contract-adversary` grades it, then a builder implements.

Inputs: `docs/research/2026-11-07-surrealdb-3.3-4.0-for-lore.md` (SUMMARY, §B4–B6/B18, §C, §D-4/D-10,
§E 7/11/12), finding #576, `docs/reference/surrealdb-31-capabilities.md` §0a/§2/§3/§6.5.

## ROUND 8 — MP-1, B-2 letter legs, F6 gate contract, Q7, the fold, landmine 1, cumulative inventory (contract-sdk3-r7; 2026-11-08, base `3374a6b`, HEAD `942aa20` docs-only)

Answers WORKORDER-r8 (scratchpad/sdk3r8), R27 (sidecar RULING-6), R28 and R29 (sidecar RULING-7). The last contract round
in the budget (R25); adversary round 4 grades it, then BUILD. Receipts, counts and the both-ways diff: the hand-back
`scratchpad/sdk3r8/REPORT.md`. Reference: `scratchpad/sdk3r8/ref` (= the round-7 reference + the reference F6 of §R8.6 + the
STAGED C10 `run()` + the STAGED landmine-1 patch); pristine baseline `scratchpad/sdk3r8/headtree` = `3374a6b` + `lore.yaml`
(R27-7c method rider).

### R8.1 New and changed pins
| item | node(s) | kills | receipt |
|---|---|---|---|
| MP-1 (R28/R29) | `test_sdk3_refused_file_reason::TestARefusedFileNamesItsBoundInEitherSweepShape::…[batch|realtime]` (a premise per leg: the leg reaches its own arm) | an arm (`_commit_batch_file` / `_index_chunks`) serving a row-cap refusal with no bound | declared mutations `mp1_batch` → exactly `[batch]`, `mp1_realtime` → exactly `[realtime]` |
| MP-1 sibling (RULING-7 §4) | `::TestAnEmbedFailureIsServedTheSameInEitherSweepShape::…[batch|realtime]` | an arm serving a different embed-failure reason | `embed_batch`, `embed_realtime` |
| B-2 letter legs (R26-3 rider; adversary R18) | `test_sdk3_record_ids::TestTheMigrationRefusalRenderersServeBareKeys` ×2, now digit-led + non-word + LETTER-LED | a renderer slicing brackets off `str(RecordID)` (right for bracketed keys, wrong for letter-led) | `b2_idsample` (both legs: `_owned_unscoped_part` renders its ids through `_id_sample`), `b2_owner` |
| R13 (adversary) | `test_sdk3_outcome_reach::TestAServerAnsweredErrorIsADefiniteFailure::test_a_domain_rejection_on_{the_single_statement,the_transaction}_seam` | a DOMAIN rejection served as outcome-unknown (the class name over-claimed: its legs drove only NotAllowed) | `fb_domain` (single-statement); the transaction leg rides the T-family kill (adversary `fb_txn_domain_unknown`) |
| F6 gate contract (R27-4) | `scripts/test_pending_contract_gate_f6.py` ×12 — §R3.7(c)'s five semantics + R27-4's two registry legs + three consequences (per-node in a node-listed file; symbol-only files keep file-level; no typecheck self-destruct of a pytest-only file) | the wrong builds named in its docstring | RED at HEAD ×12 (the registry rejects `red_nodeids`); GREEN ×12 on the reference F6 with the existing gate suites still green |
| R27-7a Q7 | file-level proof re-run on the final tree + the RAISING mutation for the five suffix-silent files (`scratchpad/sdk3r8/mut/q7_raise.py`) | a surviving private `_bare` | receipts in the hand-back |
| R27-7d fold | `_driver_sleeps.mutate_the_wait_factory` — the ONE home; `test_retry_seam._sleeps_through_the_one_wait_factory` and `test_sdk3_native_retry._mutate_the_factory` call it | — | the 19 sharing pins + the A4 pins green on the reference |

### R8.2 Cumulative removed/rewritten-test inventory, rounds 3–8 (R22 rider 2; R27-5) — NAMED FOR THE COLD AUDIT
The cold audit's contract-blind pass reads every row here against the both-ways diff (R24 #3). Rounds 3–6: drafted from this
doc's own tables (a Sonnet draft, four rows sampled against the cited sections by the author, one fate corrected: C6-1);
round 7: §R7.2 (R7-1 … R7-8, by reference — not duplicated); round 8: R8-1 … R8-3 below. Every fact is the doc's; where
the doc states no fate the row says so.

| # | round | test (as the doc names it) | REMOVED / REWRITTEN | behaviour it certified before | fate | doc citation |
|---|---|---|---|---|---|---|
| C3-1 | 3 | `lifecycle::TestRecoveryLatencyAfterALongOutage` (L6) | REWRITTEN | UNSTATED IN DOC (round 3 gives only the new form: for all owners, 15 s outage, first call answers <= 3.0 s after the store returns; round 4 later moves outage to 45 s) | carried-by L6 (the rewritten node itself) | §R3.1 row L6; §R3.0 |
| C3-2 | 3 | retirement file `TestTheSdkTypesALiveTransactionConflict` (RP3), transactional leg | REWRITTEN | UNSTATED IN DOC (new form: runs `query_raw` -> `_failed_statements` -> `_rollback_verdict`, requires `is_transaction_conflict` on the selector's root cause; never reads `query()`) | carried-by RP3 itself (+ M-W6 declared reds RP3, T1, T2); retired-with drop-list row #2 | §R3.0; §R3.4 W6; §R3.5 row #2 |
| C3-3 | 3 | `test_sdk3_result_shapes.py` round-1/2 R7 `…every_minted_key_shape_round_trips` | REMOVED | minted key shapes (ULID, digit-led, letter-led, uuid5, path, int): type, table, key, symmetric render AND SDK-2.0 rendering | carried-by `test_sdk3_record_ids.py` (doc: "absorbs round-1/2 R7-R9"); removed because contradicted ruling R7; per-node mapping UNSTATED IN DOC | §R3.10 last bullet; §R3.0; round-1/2 table row R7 |
| C3-4 | 3 | `test_sdk3_result_shapes.py` round-1/2 R8 `TestTheIdLoreServesNamesTheEnginesKey` and R9 `TestAKeeperCannotBeDeletedWhileKeeping…` | REMOVED (moved out of result_shapes) | `Keep.id == "keep:<engine key>"` and `get_keep` finds it; a digit-led keeper principal is refused deletion while keeping | carried-by `test_sdk3_record_ids.py` ("absorbs"); K3 `TestAKeeperCannotBeDeletedWhileKeeping[installed|angle|backtick]` is the keeper pin | §R3.0 ("R7-R9 moved out"); §R3.1 row K3 |
| C4-1 | 4 | `_surreal_fakes.py::FakeSurrealStore.__init__` | REWRITTEN | statement cap in the fake | carried-by rewritten node; ruling statement cap -> row cap (R8 F12) | §R4.7 row 1 |
| C4-2 | 4 | `_surreal_fakes.py::fake_surreal_trio` | REWRITTEN | statement cap in the fake trio | carried-by rewritten node; ruling R8 F12 | §R4.7 row 2 |
| C4-3 | 4 | `test_indexer.py:255-271, :694` `_trio` kwarg | REWRITTEN (deviation, §R4.1) | fake kwarg named for the statement cap | carried-by rewritten kwarg (rename); ruling F12 | §R4.7 last statement-cap row |
| C4-4 | 4 | `test_ingest_entity_seam::TestOneImplementation::test_entity_write_reddens_with_the_shared_compose_cap` | REWRITTEN | shrinking the shared STATEMENT cap reddens the entity write | carried-by rewritten node (shrink row cap); ruling R8 F12 | §R4.7 row 3; §R4.0 MP1 row |
| C4-5 | 4 | `test_surreal_apply.py:158` P5-C2 fallback `TXN_STATEMENT_WARN_THRESHOLD = 800` | REWRITTEN (removed) | fallback constant for the statement warn | carried-by row warn (R9 D2): `test_sdk3_row_bound::TestTheSizeWarnFiresOnRows` ×2 | §R4.7 row 4; §R4.0 D2 row |
| C4-6 | 4 | `test_surreal_apply.py:191` P5-C3a fallback `TXN_STATEMENT_HARD_CAP = 5000` | REWRITTEN (removed) | fallback constant for the statement hard cap | carried-by row cap (R8 F12) pins `test_sdk3_row_bound::TestTheRowCapIsTheOneBound` | §R4.7 row 5; §R4.0 MP1 row |
| C4-7 | 4 | `test_surreal_apply::TestApplyTxnSizeTelemetry::test_apply_warns_above_statement_threshold` -> `…_above_the_row_threshold` | REWRITTEN | apply warns above the statement threshold | carried-by rewritten node (R9 D2) | §R4.7 row 6; §R4.0 D2 |
| C4-8 | 4 | `test_surreal_apply::TestComposeStatementHardCap::test_compose_raises_…` -> `TestComposeRowHardCap::…` | REWRITTEN | compose raises above the statement hard cap | carried-by `TestComposeRowHardCap` ×3 (R8 F12) | §R4.7 row 7; §R4.0 MP1 |
| C4-9 | 4 | `test_surreal_apply` `…test_compose_accepts_exactly_at_the_hard_cap` | REWRITTEN | accepts exactly at the (statement) hard cap; doc: stayed GREEN at 5,000 statements under F12 | carried-by rewritten node; ruling R8 F12 | §R4.7 row 8 |
| C4-10 | 4 | `test_surreal_apply` `…test_compose_still_succeeds_above_warn_threshold_but_below_hard_cap` | REWRITTEN | succeeds above warn threshold, below hard cap (statements) | carried-by rewritten node; ruling F12 + D2 | §R4.7 row 9 |
| C4-11 | 4 | `test_surreal_apply::TestApplyStatementHardCap…` -> `TestApplyRowHardCapNeverReachesTheServer::…` | REWRITTEN | apply refuses over the statement cap before anything is sent | carried-by `TestApplyRowHardCapNeverReachesTheServer` (R8 F12) | §R4.7 row 10; §R4.0 MP1 |
| C4-12 | 4 | `test_reanchor_58_r3_convergence.py:136` module `CAP` | REWRITTEN (collection-safe read only) | read the statement-cap constant | carried-by rewritten read; ruling F12; 58 re-size owed (F19) | §R4.7 row 11 |
| C4-13 | 4 | `test_comms_await.py:218,:222` `TestTheSharedSdkAwaitBoundaryConstant::…` -> `::test_the_boundary_catches_the_sdk_transport_error_and_not_a_keyerror` | REWRITTEN | boundary constant contains KeyError; exact-set equality | carried-by rewritten node (catches SDK transport error, lets KeyError through; exact-set dropped per F10) | §R4.7 KeyError family rows 10-11 |
| C4-14 | 4 | `test_comms_await.py:454` `_FakeLiveConnection` dead path -> `TestSocketDropNonLoss` ×2 | REWRITTEN | dead connection raises KeyError | carried-by rewritten fake (raises `ConnectionUnavailableError`) | §R4.7 KeyError family row 12 |
| C4-15 | 4 | `test_comms_await.py:461` `_FakeLiveConnection.subscribe_live` | REWRITTEN | raises KeyError | carried-by rewritten fake (raises `ConnectionUnavailableError`) | §R4.7 KeyError family row 13 |
| C4-16 | 4 | `test_comms_await.py:562,:563` `…dropping_keyerror…` -> `::test_dropping_the_transport_error_from_the_shared_constant_breaks_await_recovery` | REWRITTEN | mutation drops KeyError from the shared constant | carried-by rewritten node (mutation drops the members that catch the SDK transport error, derived from the live value) | §R4.7 rows 14-15 |
| C4-17 | 4 | `test_graph_surreal.py:2878` `TestQuerySeamSdkKeyErrorClassification` -> `TestQuerySeamSdkTransportErrorClassification::{test_an_sdk_transport_error_surfaces_as_outcome_unknown_and_heals, test_a_keyerror_propagates_as_a_bug_not_as_transport}` | REWRITTEN | KeyError -> `SurrealConnectionError` + heal | carried-by the two rewritten nodes | §R4.7 row 19 |
| C4-18 | 4 | `test_memory_ownerfold_63a_iv.py:63` `_bare_s` | REWRITTEN | partitioned `str(RecordID)` (53/200 engine ids digit-led -> latent flake on SDK 3.0.0) | carried-by rewritten helper (`.table_name` / `.id`, R7 d) | §R4.7 row 20 |
| C4-19 | 4 | `test_memory_reinforce_63a_iv.py:47` `_bare_s` | REWRITTEN | same as C4-18 | carried-by rewritten helper (R7 d); doc C8 notes the pre-existing duplicate | §R4.7 row 21; C8 |
| C4-20 | 4 | `test_memory_supersede_atomicity_63b_ib.py:772` `TestTransportAndContentionKeepTheSupersedeLedgerRow::test_a_transport_failure_on_the_composed_supersede_keeps_the_ledger_row` | REWRITTEN | injected KeyError | carried-by rewritten node (SDK transport error, surfaces as unknown, F14) | §R4.7 row 22 |
| C4-21 | 4 | `test_memory_supersede_atomicity_63b_ib.py:877` `TestCompensationIsDomainScopedAcrossShapesAndCauses[*transport*]` | REWRITTEN | injected KeyError | carried-by rewritten params (SDK transport error) | §R4.7 row 23 |
| C4-22 | 4 | `test_retry_seam.py:312,:316` `_mutate_shared_marker` consumers | REWRITTEN | setattr of `_RETRYABLE_CONFLICT_KIND` | carried-by rewritten consumers (`move_the_sdk_conflict_predicate`, rebinds `QueryError.is_transaction_conflict`); retired-with drop-list row #2 | §R4.7 rows 26-27 |
| C4-23 | 4 | `test_retry_seam.py:385` param `sdk-KeyError-routing-drop` -> `sdk-transport-inflight-drop` + new `::test_a_keyerror_propagates_as_a_bug_not_as_transport` | REWRITTEN | KeyError = transport: unknown, zero retries, drop | carried-by the renamed param + new node | §R4.7 row 28 |
| C4-24 | 4 | `test_retry_seam.py:3000,:3031,:3035` `TestScoutCommandClaimRidesTheSeam::test_a_transport_fault_still_reaches_the_reconnect_ladder[…]` | REWRITTEN | KeyError param; `raises((*_CONNECTION_ERRORS, KeyError))`; isinstance with KeyError | carried-by rewritten node (transport error; no KeyError) | §R4.7 rows 29-31 |
| C4-25 | 4 | `test_scout.py:1157` `…recovers_from_a_keyerror_inflight_drop` -> `::test_reconnect_recovers_from_an_sdk_transport_inflight_drop` | REWRITTEN | recovery from a KeyError in-flight drop | carried-by rewritten node | §R4.7 row 32 |
| C4-26 | 4 | `test_scout.py:1199,:1200,:1206` `…dropping_keyerror…` -> `::test_dropping_the_transport_error_from_the_shared_constant_breaks_recovery` | REWRITTEN | shared mutation helper drops KeyError; drop error = KeyError | carried-by rewritten node (doc: VACUOUS on REF until C1 fakes fixed) | §R4.7 rows 33-35 |
| C4-27 | 4 | `test_surreal_harness.py:1483` `TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_detection_follows_the_seams_one_conflict_kind` | REWRITTEN | literal setattr of the conflict kind | carried-by rewritten node (predicate mutation); drop-list row #2 | §R4.7 row 36 |
| C4-28 | 4 | `test_surreal_harness.py:1516` `::test_the_bootstrap_paths_detection_follows_the_seams_kind` | REWRITTEN | literal setattr | carried-by rewritten node (predicate mutation) | §R4.7 row 37 |
| C4-29 | 4 | `test_surreal_harness.py:1565` `::test_run_detection_follows_the_seams_one_conflict_kind` | REWRITTEN | literal setattr | carried-by rewritten node (predicate mutation) | §R4.7 row 38 |
| C4-30 | 4 | `test_surreal_manifest.py:1231` -> `TestQuerySeamSdkTransportErrorClassification` ×2 | REWRITTEN | KeyError classification (as graph) | carried-by the two rewritten nodes | §R4.7 row 39 |
| C4-31 | 4 | `test_surreal_store.py:2347` -> `TestQuerySeamSdkTransportErrorClassification` ×2 (a READ) | REWRITTEN | KeyError classification on a read | carried-by the two rewritten nodes | §R4.7 row 40 |
| C4-32 | 4 | `test_surreal_store.py:2375` `TestTxnSdkKeyErrorClassification` -> `TestTxnSdkTransportErrorClassification` ×2 | REWRITTEN | fake `query_raw` KeyError -> unknown + dropped once | carried-by the two rewritten nodes (transport error; KeyError propagates) | §R4.7 row 41 |
| C4-33 | 4 | `test_retry_seam.py` imports (drop #13): 2-line `AsyncEmbeddedSurrealConnection` deletion | REMOVED (PORTED from round-3 reference) | embedded-connection imports | retired-with drop-list row #13 | §R4.7 last KeyError-family row |
| C5-1 | 5 | `test_comms_await.py::TestAwaitSharesTheSdkBoundaryConstantByMutation::test_no_inline_sdk_await_boundary_tuple_survives_in_scout_or_the_awaiter` (F-d) | REMOVED (DELETED) | no bare `KeyError` inside an inline `(*_CONNECTION_ERRORS, KeyError)` tuple (AST reach check) | doc: pattern cannot occur after R6 F10 (vacuous); sibling runtime-mutation sharing pin "stays" (node id UNSTATED IN DOC); C7 prose elsewhere NOT edited (residual R5-r4) | §R5.5 F-d; §R5.0 item 6; §R4.7 C7/F-d |
| C5-2 | 5 | `test_backoff_seam.py::TestNoNewHandRolledBackoff::test_the_allowlisted_file_still_contains_what_it_was_exempted_for` (F22) | REMOVED (DELETED) | source-text check that `_txn.py` still contains what its `_POW_ALLOWLIST` exemption was for | doc: behaviour clauses kept (every declared site draws from the mutated policy; perimeter scan; positive control); `_POW_ALLOWLIST` left exempting `_txn.py` (fork F-r5-1) | §R5.5 F22; §R5.0 item 6; §R5.10 F-r5-1 |
| C5-3 | 5 | `test_retry_seam._point_at` and the counting factories (`_plain_counting_connection_factory` / `_counting_connection_factory` clones; 6 call sites: test_surreal_store ×4, _manifest ×1, _graph ×1) (C2) | REWRITTEN | patched the per-module `AsyncSurreal` name | carried-by `sdk3_shape_fakes.route_connections` (R5.0 item 10); NOT applied to ~7 other `test_retry_seam` sites, test_comms_cli, test_ingest_entity_seam, test_surreal_harness (residual R5-r5) | §R5.7 C2; §R5.0 item 10 |
| C5-4 | 5 | `test_surreal_store.py` `if TYPE_CHECKING:` import of `_RETRYABLE_CONFLICT_KIND`, helper `_ruled_a28c_store`, and the `TYPE_CHECKING` import (C3) | REMOVED | type-only import of the retired literal; unreferenced helper | doc: grep shows no reference anywhere (incl. `scripts/pending_contracts.yaml`); no behaviour pin named | §R5.7 C3; §R5.0 item 10 |
| C5-5 | 5 | `_bare_s` in `test_memory_ownerfold_63a_iv.py` and `test_memory_reinforce_63a_iv.py` (C8) | REWRITTEN | duplicated `str(RecordID)` partitioner | carried-by `sdk3_shape_fakes.bare_record_key` (`_bare_s = bare_record_key`) | §R5.7 C8 |
| C5-6 | 5 | F-a doubles: `test_retry_seam._ScriptedConnection.query`, `test_scout._FakeCommandConnection.query` ×4, `test_comms_await._FakeLiveConnection.query` ×2 | REWRITTEN | answered with SDK 2.0's bare first-statement shape | carried-by `sdk3_shape_fakes.one_statement_answer` (version-aware); its SDK-2.0 branch retired-with drop-list row #37 (builder deletes in the pin-3.0.0 commit) | §R5.4; §R5.0 item 5 |
| C6-1 | 6 | `test_sdk3_served_outcome::…::test_every_pin_row_names_a_real_behaviour_pin` (R14) | REMOVED (deleted) | each adjudication row names a real behaviour pin | retired by operator ruling R14 ("Round 5's clause that checks each 'pinned' verdict row names an existing test is REMOVED (a test about tests)"); no behaviour carried — the walker-derived reach checks stay | §R6.0 R14 |
| C6-2 | 6 | MP-C 3a: `test_retry_seam` ~47 nodes (`{'next':N} == [{'next':N}]` asserts, brief/ack doubles, scout fakes) and `test_surreal_harness` ×2 `run` identity fakes | REWRITTEN | doubles answered SDK-2-shaped | carried-by `one_statement_answer` at every `query()` return of every `test_retry_seam` double (16 sites); harness `run` identity fakes fed SDK-shaped answers (C10) | §R6.2 row 3a; §R6.8 C10 |
| C6-3 | 6 | MP-C 3b: 6 `AsyncSurreal` monkeypatches in `test_retry_seam` | REWRITTEN | patched per-module `AsyncSurreal` | carried-by `route_connections` | §R6.2 row 3b |
| C6-4 | 6 | MP-C 3c: every cloned `_bare` — 19 by helper c9-sweep-r6 + a19; `_bare_id` in `test_pdp_oracle_61b`; `_governed_contract_64.bare` (now alias); split/endswith sites in test_agent_registry, _comms_fakes, test_preboot…, test_memory_replay…, test_principals_store, test_comms_tool, test_audit_schema, test_keeps_schema, test_enforced_relations (nodes a28/a28b/a28c, comms_schema, governed_migration, agent_governance, comms_send, governed_schema, …) | REMOVED (clones deleted) / REWRITTEN (call sites) | text-split of `str(RecordID)` to get the bare key | carried-by shared helpers `sdk3_shape_fakes.record_parts` / `bare_record_key` / `same_record` | §R6.2 row 3c |
| C6-5 | 6 | MP-C 3c determinism: `_governed_contract.digit_led_record_key` + `rekey_principal` replace random engine-key comparisons | REWRITTEN | compared keys SDK 2 rendered bare (SDK 3 brackets digit-led keys, so compare failed every run on SDK 3) | carried-by fixed digit-led keys (`digit_led_record_key`, `rekey_principal`) | §R6.2 row 3c |
| C6-6 | 6 | MP-C 3d: `test_blocks_edge` ×7 via `StoreTraffic.COUNTABLE_DOORS` / `_delegating` (instrument) | REWRITTEN (instrument) | door reach derived from coroutine-only classification (SDK 2.0 doors) | carried-by rewritten `COUNTABLE_DOORS` (follows delegation through the connection class's private helpers); same 11 doors on SDK 2.0; reach stays deny-by-default (`require_full_reach`) | §R6.2 row 3d |
| C6-7 | 6 | MP-C 3f: socket-owner scans ×2 | REWRITTEN (R15: rewrite or retire) | spelling scan for socket owners | carried-by behavioural discovery (`_ensure_connection` driven once with every constructor routed to a counting factory; same 17 at HEAD and on ref) | §R6.2 row 3f |
| C6-8 | 6 | MP-C 3f: derivation RELATE regex ×3 | REWRITTEN | regex over derivation source | carried-by instrument that EXECUTES the fragment in one transaction under ENFORCED code-graph edges (live store) | §R6.2 row 3f |
| C6-9 | 6 | MP-C 3f: governed SDK-name scan | REWRITTEN (narrowed) | name scan for SDK method names | carried-by scan narrowed to receivers that are not module `ContextVar`s (+ control that the same name on another receiver still flags) | §R6.2 row 3f |
| C6-10 | 6 | MP-C 3g: `test_ingest_entity_seam` ×8 via `_ingest_entity_fixtures.FakeDomainStore.fetch_nodes` | REWRITTEN (fixture; TEST read shape, not a production regression) | read via raw `connection.query` (SDK 2 shape); SDK 3 answers `[[rows]]` so every row was filtered | carried-by routing through `_txn.run_query` (reference production unchanged: 45/45) | §R6.2 row 3g; §R6.8 F-a |
| C6-11 | 6 | MP-C 3h: `test_fixwave_a19_63c_i_a::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19` (1 node) | REWRITTEN | refusal rendering accepted the SDK `str(RecordID)` form | carried-by rewritten `_renderings` / `_forbidden_rendering` (a19 3h pin); reference bug B-2 | §R6.2 row 3h; §R6.1 row a19 3h |
| C6-12 | 6 | MP-C beyond-the-117: q1b ×6, q1c ×1 (class/kind tables) | REWRITTEN | SDK 2.0 conflict kinds; `TransactionConflict` assumed rejection/proven/unknown | carried-by rewritten tables: `TransactionConflict` ruled `retried` (fourth fate; FORK-R6-1); drop-list row #2 / R11; q1b gains `TxnRowCapExceededError` (proven), `SurrealOutcomeUnknownError` (unknown) | §R6.2 last row; §R6.7 FORK-R6-1 |
| C6-13 | 6 | MP-C beyond-the-117: `pdp_oracle` ×13 | REWRITTEN | three raw `connection.query` reads (SDK 2 shape) | carried-by the harness `run` funnel (F-a/C10 reach) | §R6.2 last row |
| C6-14 | 6 | MP-C beyond-the-117: a19a `_names` | REWRITTEN | keyed on a rendered id form | carried-by `_names` keyed on the sanitised bare key every allowed form contains | §R6.2 last row |
| R7-1 … R7-8 | 7 | see §R7.2 | — | — | — | §R7.2 |
| R8-1 | 8 | `test_sdk3_native_retry._FactoryMutation` / `test_retry_seam._sleeps_through_the_one_wait_factory` (helpers) | REWRITTEN (folded) | the one-factory mutation (R20 A4) | carried-by the same node ids through `_driver_sleeps.mutate_the_wait_factory` | §R8.1 |
| R8-2 | 8 | `test_sdk3_record_ids::TestTheMigrationRefusalRenderersServeBareKeys` ×2 | REWRITTEN (+ letter-led key) | bare-key served ids for digit-led + non-word keys | carried-by the same node ids | §R8.1 |
| R8-3 | 8 | `test_sdk3_outcome_reach::TestAServerAnsweredErrorIsADefiniteFailure` (class docstring) | REWRITTEN (scope stated; +2 domain legs) | NotAllowed-branch definiteness | carried-by the same 2 nodes + 2 new | §R8.1 |
| SVC1-1 | servicing `d78baa3` | `_surreal_harness.run` (helper) | REWRITTEN | `run` answered whatever `query()` returned (SDK 2.0: the first statement's result) | carried-by `test_surreal_harness::TestRunAnswersItsFirstStatement` ×7 (first statement's result; non-list / empty fails closed; a later statement's error surfaces) | R27-1 C10; FORK-R7-1 (§ROUND 7) |
| SVC1-2 | servicing `d78baa3` | `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES` + `NO_DRIVER_SLEEP_HINT` (helper) | REWRITTEN (narrowed to `{"tenacity.asyncio"}`) | a driver sleep attributed to any allowed caller module counted as the driver's | carried-by R29's 6 nodes (`test_sdk3_native_retry` ×4, `test_retry_seam` ×2) + scout's caller attribution in both ladder pins | R29 (riders 1–4); §R8.3 (A) |
| SVC2-1 | servicing `a5bd688` (REQ 2) | `test_backoff_seam::test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll` | REWRITTEN (AST call-spelling → behaviour) | `jittered_backoff_delay`'s body CALLS `wait_random_exponential`; the module text never names `wait_exponential_jitter` | carried-by the same node: the factory IS `wait_random_exponential(base, cap, ×2)` (equal jitter refused by exact type) + the delay draws THROUGH `full_jitter` (factory swap); mutations equal-jitter / second construction / hand-roll each RED | R11; R20 A4 |
| SVC3-1 | servicing `0ae1dea` (REQ 3) | `_surreal_fakes.TXN_ROW_HARD_CAP` statement-cap fallback | REMOVED | the fake's cap fell back to `TXN_STATEMENT_HARD_CAP` before the build | retired-with the build (§R4.1: "the builder deletes it with the build"); the cap itself carried-by `test_sdk3_row_bound::TestTheRowCapIsTheOneBound` | §R4.1 |
| SVC3-2 | servicing `0ae1dea` (REQ 3) | `_surreal_harness._RemovableDatabaseConnection.query` (protocol) | REWRITTEN (`async def` → `def … -> Awaitable[Any]`) | — (typing only; SDK 2's `query` was a coroutine function) | carried-by typecheck (2 arg-type reds gone) + `test_harness_database_lifecycle_486` green | R15 |
| SVC3-3 | servicing `0ae1dea` (REQ 3) | `pending_contracts.yaml` bound `packet-66-sdk3-contract` | REMOVED (self-destructed) | owned the two attr-defined reds of SDK-3-only names at HEAD | retired-with its own trigger (the SDK pin); currency shows no self-destruct orphan | R22 rider 3 / R24 item 6 |
| SVC-C | servicing `2834909` (REQ-C) | `test_fixwave_a28c_63c_i_a._TEXT_TEST_ALLOWLIST` | REWRITTEN (+ `record_key` row) | the exact set of text testers in `_txn` | carried-by the same scan + its positive-control derivation pin (a new tester still reds by name) | R7; R8 F16 |
| SVC-584 | `f866fbe` (#584) | 4 ledger fixtures (`supersede_world`, `dirty_world`, `rebuild_world`, `ledger_backend`) + `test_memory_backend.ledger_path` | REWRITTEN (cwd-relative path → shared tmp `ledger_path` in conftest; dead unlinks removed) | a per-test ledger file named after the slug, unlinked at teardown | carried-by the same tests (213 green) + the forced setup-failure run leaving the root clean | finding #584 |
| SVC-R30 | `078f502` (R30 rider, lead 19063) | — (3 pins added; bound `packet-66-r30-validator` added) | NONE — additions only | — | 2 refusal legs owned by node id until the builder's validator line | R30 (RULING-8 rider) |
| SVC-T2 | `3e3af09` | `SdkRequestTimeoutMixin` docstring | REWRITTEN (docstring: fake-honesty check vs SDK 3.0.0) | — | no node changed | R21/R22 F-a; R41 |
| SVC-T1 | `81f9cbd` (RULING-13 FORK T) | the eight `kill()` doubles (`_FakeLiveConnection`, `_FakeCommandConnection`, `_RaisingConnection`, `_ParkingLiveConnection`, `_ScoutFakeConnection`, `_AllMethodsConflictConnection`, `_BootstrapFailsThenHealthy`, `_ForeverConflictingKill`) | REWRITTEN (+ `SdkRequestTimeoutMixin`; `_ParkingLiveConnection.kill` parks like the SDK) | no `timeout()`; the parking double parked forever under any cap | carried-by the same nodes (796 green before the switch); post-switch mutation receipt pending | R41 (RULING-13 FORK T) |
| S9-4 | `dfa9e23` (R39 item 1) | F6 pin block comment (MP6-5 / W5 / W6) | REWRITTEN (comment only: re-open triggers + measurement) | — | no node changed; F6 61/61 green on 58fd5df | ADVERSARY5 §RE-GRADE-2 |
| SVC-F6 | `2c8877e` | `pending_contracts.yaml` bound `packet-66-f6-contract` | REMOVED (self-destructed) | owned the F6 file's one contract-ahead call-arg red | retired-with its trigger (the F6 build, 58fd5df); currency 0 orphans | R35 / R37 |
| SVC-FO | `abc3b74` | `test_am37_13_3_63c_i_a::…test_a_row_missing_a_required_column[created_at]`; `test_ingest_entity_seam::…test_commit_batch_file_delegates_to_compose` (P10b) | REWRITTEN ×2 | a missing created_at served as PrincipalKeyStoreError; `_commit_batch_file` calling `_compose_file_fragments` directly | carried-by the same nodes: SurrealStoreError (R34 / F1) with the CERTAIN note; both sweeps → `_commit_or_isolate` → `_compose_file_fragments` (R36) | R34 rider 3; R36 |
| S9-3 | F6 delta 3 `6ae8338` (R39) | — (MP6-1 ×4, MP6-2 ×4, MP6-3, MP6-4 added) | NONE — additions only; no F6 pin removed or rewritten | — | — (MP6-5 a stated bound in the pin block, no pin) | R39; ADVERSARY5 §RE-GRADE |
| S9-2 | F6 delta 2 `64fcdd6` (R35) | `scripts/test_pending_contract_gate_f6.py::test_the_render_says_a_SKIPPED_or_XFAIL_listed_id_is_KEPT[kind]` ×2 | REWRITTEN (widened: renderer × leg × kind = 12 nodes) | the KEPT note on the `--currency` render of a RED_ADJUDICATED run | carried-by the same test name over {currency, wave_full, wave_scoped} × {adjudicated, all_skip}; mutations N9 (notes only off GREEN) / wave render silent / scoped-GREEN silent each RED | R31 rider; R35 MP5-2 |
| SVC-E1 | `55d9ed0` (REQ-E part 1) | `test_sdk3_retirement_pins_66d::TestARequiredDatetimeColumnIsCheckedNeverCoerced` ×10 | REWRITTEN (R34 signature; full refusal text with `==`; +`row_id=None` leg) | refused naming row + column on the pre-R34 `row=` signature | carried-by the same class (11 nodes); mutation (tz clause dropped) RED on both naive legs | R34 (RULING-11 riders 2/3) |
| SVC-A2 | `da24469` + `b9ed293` (REQ-A, R36) | `test_exhaustion_fates` known-bound pin; `_exhaustion_fates` rows `_commit_batch_file` / `_index_chunks`; `test_sdk3_served_outcome` pin rows for the same two | REWRITTEN (pin re-keyed; bound NARROWED, asserted) · REMOVED ×4 rows (two per table) | two per-file handlers recording ONE reason; their fates / pins | carried-by the ONE site `index/indexer.py::_commit_or_isolate` (one row per table, same fate / pin) | R36 (RULING-12 fork 2 (c)); R4 rider 3 |
| S9-1 | F6 pins `c01b114` (R32) | `scripts/test_pending_contract_gate_f6.py::test_a_listed_PREFIX_admits_no_parameter_and_is_itself_stale` | REWRITTEN (tightened) | "the prefix id is reported" — any orphan naming it, a "green, delete it" line included | carried-by the same node: the stale line must say "not collected" (R31 Leg 1); mutation `m13` (prefix stale read as green) RED on it alone | R31; R32 |

Coverage (rounds 3–6, the draft's own): round 3 ×4, round 4 ×33, round 5 ×6, round 6 ×14 (57 rows). Excluded: rows ADDED
rather than removed/rewritten (am-37 3e, the bootstrap allowance), §R4.7's KEPT and DORMANT-BOUND rows, and §R3.10's
builder-routed rows (rewritten in round 4, listed there). Partial gaps the doc leaves: C3-1/C3-2 (prior behaviour unstated),
C3-3 (no per-node mapping), C5-1 (the sibling pin's node id).

### R8.3 Landmine 1 — "tenacity in name only": the STAGED instrument (A) and the cold-audit diff check (B)
- **A, staged (R29: adopted by the sidecar, OVERTURNABLE by the operator; it does NOT land in the main tree this round):**
  `scratchpad/sdk3r8/lm1_narrowing.patch` — `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES = {"tenacity.asyncio"}` with the
  threat model in the instrument (rider 1), `NO_DRIVER_SLEEP_HINT` rewritten to teach "port it, never widen this set"
  (rider 3), and scout's ladder held the same way: the ladder pins' injected `sleep` records its caller and asserts
  `tenacity.asyncio` (rider 4). It lands WITH the build as a servicing commit; the HEAD nodes it reddens go into the F6
  `red_nodeids` entry (rider 2). Proofs on the reference (patch applied): the reference green; the author's own declared
  hand-loop mutations `lm1_txn` (26 declared) and `lm1_scout` (2 declared) RED.
- **B, the cold audit's NAMED diff check (keep beside A; the only instrument for a loop that games A):** "`_txn.retry_on_conflict`
  and `scout.CommandSubscriber.run` contain NO loop around the attempt; tenacity's `AsyncRetrying` IS the loop; no wait
  object is CALLED outside tenacity (`backoff.full_jitter(...)` is passed as `wait=`, never invoked by lore)." Scout's
  ladder is reachable by B; A reaches it only through the staged caller attribution.

### R8.4 Builder notes (adversary-3 residuals and round-8 consequences; no pins)
- **MP-1 chokepoint:** ONE helper shared by the two cloned `except SurrealStoreError` arms (`_index_chunks`,
  `_commit_batch_file`): `_landed_after_unknown` → refused reason → log → `_mark_file_failed`. Prove the sharing by
  mutation at audit (break the helper ⇒ both MP-1 legs red).
- **R1 / R27-2(a):** `upsert` = ONE pure chunk-row builder composed alone (and by `replace_file_fragment` after its DELETE);
  in-tree prior art for the batched overwrite form: `graph_surreal`'s `INSERT INTO name $rows ON DUPLICATE KEY UPDATE
  value = $input.value`. The named audit check: break the row builder ⇒ the upsert pins AND B1 redden.
- **R4 (F11/CF4):** CF4 is masked by the seam's drop-on-timeout; changing timeout→drop makes `SURREAL_STREAMING`
  load-bearing, and CF4 guards it (proven by construction by adversary 3).
- **R11:** `loresigil.backoff.jittered_backoff_delay` constructs the same `wait_random_exponential(...)` as `full_jitter` —
  delegate it to `full_jitter` in 66, or fold it in packet 68 (two homes for one law until then).
- **R12:** collapse the five id-text homes (`record_text`, `governed._bare`, `keeps`/`principal_keys._record_id_part`,
  `floor_calibration._bare_record_id`) onto RecordID parts / `record_text`.
- **R14:** B-2's backtick leg cannot fire on SDK 3.0.0 (`str()` never emits backticks); it fires the day the pin moves to
  3.0.1 — a strip-⟨⟩ renderer passes today.
- **R15 (F-a):** the doubles' `async def query` returns a coroutine; SDK 3.0.0 `query()` returns an `AsyncQueryBuilder`.
  Re-open trigger: the first production use of a builder-only method (`.first()`/`.into()`) or of `create_task` on `query()`.
- **F6 (build step 0):** implement per `scripts/test_pending_contract_gate_f6.py`; write `red_nodeids` entries
  SINGLE-QUOTED in YAML (double quotes decode pytest's `\u2014` escapes into the character, and the id stops matching).
  The servicer then registers `scratchpad/sdk3r8/item5/packet66_entry.yaml` (filled; see the hand-back).

### R8.5 Forks (written down, not silently resolved)
- **FORK-R8-1 (low) — where `red_nodeids` lives.** Taken: a field of each FILE entry (RULING-6's "`red_nodeids`-only
  `PendingFile`"). Alternative: §R3.7(c)'s field on the BOUND. The F6 tests assume per-file; switching is a fixture edit.
- **FORK-R8-2 (low) — writable set.** The F6 contract is a NEW file under `scripts/` (`test_pending_contract_gate_f6.py`),
  outside round 7's writable set; taken as granted by WORKORDER-r8 item 3a + R27-4 ("its tests are contract surface").
- ~~FORK-R8-3~~ RESOLVED: WORKORDER-r8 Amendment 1 (lead, after R29) arrived mid-round and matches what was built — A
  adopted as the staged patch with riders 1–4, B kept beside it, the embed-failure arm under the same parametrisation.

### R8.6 The round-8 reference delta
1. `scripts/pending_contract_gate.py`: a reference F6 (`PendingFile.red_nodeids`; the claim validator counts it;
   `JUnitReportReader` derives node ids and the collected set; per-node partition for node-listed files, file-level
   otherwise; the pass/stale self-destruct legs on the pytest residuals; no typecheck self-destruct for a pytest-only
   entry). Satisfiability instrument only — the builder writes F6.
2. Test-side, reference only: the STAGED C10 `run()` rule (round 7) and the STAGED landmine-1 patch (§R8.3).
Pristine copies: `scratchpad/sdk3r8/ref_pristine/`.

## ROUND 7 — R18/R20 native retry, R19 routing, R21/R22, R26 (contract-sdk3-r7; 2026-11-08, graded tree HEAD `0d9b8c2`)

Answers R17 (governing test), R18 as amended by R20, R19's routing paragraph, R21 + R22 and R26 in
`docs/plans/v2/sdk3-rulings.md`. Dated 2026-11-08, measured at HEAD `0d9b8c2` (SDK 2.0.0; pristine copy
`scratchpad/sdk3r7/headtree`) and on the ROUND-7 REFERENCE (SDK 3.0.0, `scratchpad/sdk3r7/ref` = round 6's reference
+ §R7.3; `scratch_copy.sh --verify-only` VERIFIED). Receipts, counts and the both-ways diff: the contract-sdk3-r7
hand-back (`scratchpad/sdk3r7/REPORT.md`). Rounds 1–6 below are history, except §R6.2's TransactionConflict cell,
§R6.5's citation and §R6.8's draw-count note (corrected in place, dated).

### R7.1 New and changed pins
| item | node(s) | kills | RED receipt |
|---|---|---|---|
| R18 window | `test_sdk3_native_retry::TestEverySleptBackoffLiesInItsWindow` | uncapped / flat / floor-lifted window; a sleep after giving up | mutations `window`, `flat` |
| R20 A3 | `::TestFullJitterReachesBothTailsOfTheWindow` (256 sleeps at n=1: min < w/8, max > 7w/8) | `w/2 + d/2` drift (the adversary's `wb_r11_sleepdrift` shape) | mutation `drift` (author-built analogue; see R7.6 BRIEF CONFLICT) |
| R18 decorrelation | `::TestConcurrentRacersSleepDecorrelatedSequences` (16 racers) | jitter keyed on shared state | mutation `dec` |
| R20 A1 / X22 | `::TestTheDriverLogsOnlyItsTerminalDisposition` ×2 (any logger, DEBUG+) | `before_sleep_log` / per-attempt records | mutation `log` |
| R18 | `::TestANonConflictErrorIsNeverRetriedOrBackedOff` ×3 | a `retry=` wider than the signal | mutation `retry` |
| R20 Leg 2 (iv) | `::TestALambdaShapedCallerGetsTheAttemptsValue` ×2 | the caller's lambda handed to tenacity raw | mutation `lambda` |
| R20 A4 | `::TestTheOneWaitFactoryReachesEveryIn66Site` ×2 + `test_retry_seam`'s 19 per-seam/mint/control/scout-claim sharing pins (one-factory mutation) | a site building its own tenacity wait | mutations `a4txn` (20 = 20), `a4scout`; RED at HEAD (no factory) |
| scout ladder (removed-behaviour preservation) | `::TestTheSubscriberBacksOffBeforeEveryReconnect` | an immediate reconnect after a drop; no reset after a live connection | mutations `reset`, `a4scout`; RED at HEAD (factory) |
| R18 classifier sharing | T1/T2 (`test_sdk3_txn_classification::TestARetryableConflictIsRetriedAndLosesNothing` ×2) | a classifier copy | mutation `classifier` (2 = 2) |
| R20 A2 controls | `test_retry_seam` empty-claim pin, live 16-way premises ×2, anti-vacuity controls ×4 → `_driver_sleeps.record_driver_sleeps` | a never-retrying driver passing T2 vacuously | unchanged controls, observed on the sleep seam |
| A4 perimeter | `test_backoff_seam::TestNoNewHandRolledBackoff` with `_POW_ALLOWLIST` EMPTY | a private `**` window | RED at HEAD (`_txn.py` `2 ** (attempt_number - 1)`) |
| C10 | `test_surreal_harness::TestRunAnswersItsFirstStatement` ×7 | `run` answering the per-statement list, swallowing a later failure, or reading a non-list as "nothing" | RED at HEAD ×6 (reaper leg green) |
| B edge COUNT | `test_sdk3_index_batching::TestNoBatchedEdgeGoesMissing` (oracle: the astroid derivation, re-run) | a batched write losing edges | mutation `edges`; RED at HEAD on the R3 premise |
| Q6 | `test_sdk3_served_outcome::TestTheUnknownOutcomeAdviceSplitsByShape` + a write-shape assertion in the D1 batch pin | read served with write advice, write served "safe to re-run" | RED at HEAD (no unknown fate) |
| Q7 | file-level mutation proof over 36 sites (`scratchpad/sdk3r7/mut/q7_proof.py`) | a surviving `_bare` copy | proof `q7` |
| R26-1a/b/c | q1b prose + failure text (c) 'retried'; q1c `test_no_kind_exists_at_both_levels` + CONTROL | a kind at both levels leaving a door untested | control reddens by construction |
| R26-3 | key helpers in `sdk3_shape_fakes`; factory digit-led by default (one line); `letter_led_principals`; record_ids pin + letter-led leg | a digit-led monoculture | — |
| R26-4 / B-2 | `test_sdk3_record_ids::TestTheMigrationRefusalRenderersServeBareKeys` ×2 | a renderer serving `str(RecordID)` | RED at HEAD on the non-word legs |

### R7.2 am-37 inventory (R22 rider 2) — every test removed or rewritten this round
| # | test (at `0d9b8c2`) | behaviour it certified | fate |
|---|---|---|---|
| R7-1 | `test_retry_seam::TestRetryOnConflictDriver::test_every_attempt_draws_a_fresh_backoff_from_the_shared_jitter` — REMOVED | one fresh draw per retry on a 1-based growing window; slept == drawn | carried-by `test_sdk3_native_retry::TestEverySleptBackoffLiesInItsWindow::test_every_retry_sleeps_once_inside_its_growing_window` + `::TestFullJitterReachesBothTailsOfTheWindow::test_the_first_backoff_reaches_both_tails_of_its_window` |
| R7-2 | `test_retry_seam` sharing pins ×19 (16 seams, mint, positive control, scout claim) — REWRITTEN in place | the seam backs off through the shared jitter | carried-by the same node ids (one-factory mutation; `a4txn`) |
| R7-3 | `test_backoff_seam::TestEveryBackoffSharesTheOnePolicy::test_command_subscriber_shares_the_policy` — REMOVED; scout legs of `test_EVERY_declared_site_draws_from_the_mutated_policy` and `test_reverting_the_shared_policy_reddens_EVERY_site` — REWRITTEN (scout leaves `_DECLARED_SITES`) | scout's reconnect backoff draws the shared policy with its own window, drawn not fixed | carried-by `test_sdk3_native_retry::TestTheOneWaitFactoryReachesEveryIn66Site::test_the_reconnect_ladder_sleeps_the_factorys_wait` (sharing + window args); drawn-ness by composition with A3 (stated bound: A3 samples the factory through the conflict driver's window) |
| R7-4 | `test_backoff_seam::TestTheSubscribersConnectLadderSleepsTheSharedDraw::test_every_slept_connect_backoff_is_the_shared_draw` — REMOVED (R26-5) | scout's connect ladder sleeps the shared draw unchanged, on a growing attempt | carried-by the reconnect-ladder factory pin + `::TestTheSubscriberBacksOffBeforeEveryReconnect::test_a_drop_backs_off_before_reconnecting_and_a_live_connection_resets_the_ladder` |
| R7-5 | `test_backoff_seam::TestNoNewHandRolledBackoff::…exponentiates_by_a_variable` — REWRITTEN (allowlist emptied) | no private window outside `_txn.py` | carried-by itself (F-r5-1) |
| R7-6 | `sdk3_shape_fakes.one_statement_answer`'s SDK-2.0 branch — REMOVED (R21) | doubles answering SDK 2.0's bare shape at HEAD | retired-with drop-list row #37 (F-a) |
| R7-7 | `test_retry_seam::TestTheAntiVacuityControlStillFires` ×4 + `_run_contending_waves` — REWRITTEN | the wave runner's anti-vacuity control | carried-by the same node ids (`DriverSleepRecorder`) |
| R7-8 | `test_sdk3_record_ids::TestARegisteredAgentIsOwnedAndScopedByEngineIds::test_the_agent_links_its_principal_and_its_session_keeps_engine_text[angle|backtick]` — REWRITTEN (+ `key_shape`) | persisted principal link + session-keep scope through the served register path | carried-by `…[{angle,backtick}-{digit-led,letter-led}]` |

### R7.3 The round-7 reference delta (beyond round 6's)
1. `loresigil.backoff.full_jitter(base_s, cap_s)` → `wait_random_exponential(multiplier=base_s, max=cap_s, exp_base=2)`.
2. `_txn.retry_on_conflict`: ONE native `AsyncRetrying` (`stop_any(...)`, `wait=backoff.full_jitter(...)`,
   `retry=retry_if_exception_type(RetryableConflictSignal)`, `retry_error_callback` = the one exhaustion record + the typed
   error), `async def _run`; DELETED `_txn_conflict_backoff_seconds`, `_conflict_wait`, `_conflict_sleep`, the stop-peeking
   `_wait`, the `RetryError` handler.
3. `scout.CommandSubscriber.run`: ONE native `AsyncRetrying` per outage on `backoff.full_jitter`; a mid-serve drop is the
   outage's first failure (raised as a `ConnectionResetError`, a member of the ladder's own caught family — a NEW
   exception type in `run`'s `except` reddens `test_exhaustion_fates`'s site registry), so it is backed off before the
   reconnect and a live connection resets the ladder. `_txn.retry_on_conflict` keeps its annotated
   `last_conflict_cause` declaration (assigned `nonlocal` from the callback): `test_retry_seam`'s chaining pin grades
   the explanation on it. DELETED `_connect_wait`, `_backoff_delay`, `_backoff`.
4. `_txn` unknown-outcome text carries both halves of Q6's advice.
5. Test-side, reference only: `_surreal_harness.run` = the STAGED C10 rule (`scratchpad/sdk3r7/c10/run_rule.patch`, FORK-R7-1).
Pristine copies: `scratchpad/sdk3r7/ref_pristine/`. Packet 68 owns the five other loops, `jittered_fixed` and the shim.

### R7.4 Forks (written down, not silently resolved)
- **FORK-R7-1 (C10 run() rule + landing):** rule taken = the FIRST statement's result, fail closed on a non-list (R2's
  raise-on-≠1 would break 239 non-literal `run` callers incl. multi-statement generated DDL; the per-statement list would
  re-shape ~680 one-statement callers and fail the #486 reaper closed). The `run` body CANNOT land before the SDK pin:
  on SDK 2.0 it reddens every live `run` caller (version-branching it is what R21/R26-2 forbid). Recommended: the
  servicing author commits `run_rule.patch` as the first servicing commit right after the builder's SDK-pin commit.
  The version-agnostic half (`_sdk_guard._is_door`, the SDK-2-only embedded class) LANDED this round.
- **FORK-R7-2 (RS7 rider unsatisfiable as ruled):** the rider's shape (`upsert` = `apply([replace_file_fragment(...)])`)
  measured on the reference: 48 failed / 601 passed over the 8 upsert files (`TxnParamCollisionError: parameter
  'st_tier' bound by more than one fragment` for a multi-file batch; the replace DELETEs the file's other chunks).
  RULING-1: "if per-record semantics cannot ride the existing builders, THAT is the fork". Options: (a) a shared pure
  chunk-row builder both `replace_file_fragment` and `upsert` compose (one mutation reddens both); (b) per-file
  grouping with namespaced params + accepting replace semantics (fixture rewrites); (c) re-rule RS7 to delete `upsert`
  (R12's original, 90 fixture edits). Recommend (a). No pin written; the reference keeps round 6's `upsert`.
- **FORK-R7-3 (Q6 reading, low):** taken — the seam's own unknown-outcome text carries BOTH halves ("a write may have
  landed: verify before retrying; a read is safe to re-run") because the seam cannot tell a read from a write (F14) and
  no read-serving catch site exists; the write renderer serves the write half only. Alternative: per-surface advice,
  which needs a read-serving render site that does not exist.
- **FORK-R7-4 (item 5 STOPPED — schema refuses a pytest-only file):** `--verify-registry` on a probe entry naming a
  packet-66 file with no missing symbol: "names neither a missing symbol nor a code allowance — that degenerates to
  file-only matching, which waves through a genuinely NEW defect in the file" (EXIT 2). No packet-66 file holds a
  typecheck red, and a registered file with no mypy error self-destructs on the typecheck leg. F6's `red_nodeids` (R6,
  a gate change) is the owner; the drafted full entry is `scratchpad/sdk3r7/item5/`. What IS registrable was
  registered: `scripts/pending_contracts.yaml` `packet-66-sdk3-contract` holds the one packet-66 file with a TYPECHECK
  red (`test_sdk3_served_outcome.py`, the SDK-3-only `TransportTimeoutError` via a module alias — one unsymboled
  `attr-defined`); every other declared RED@HEAD file waits for F6.
- **FORK-R7-5 (low):** R22 names "the am-37 adjudication table"; the am-37 tables in the writable set adjudicate store
  CLASSES, not removed tests. Rows recorded in §R7.2; mirror into am-37 §15 at the operator's next pass with R26-1's row.
- **FORK-R7-6 (low):** A4's in-66 site set {`retry_on_conflict`, `CommandSubscriber.run`} is DECLARED; deriving it is a
  source scan (operator approval). Re-open trigger: packet 68.

### R7.5 Builder notes (outside the contract's writable set)
- Build the reference's §R7.3 shape; the pins name no tenacity class except through `loresigil.backoff.full_jitter`
  (call it as a module attribute at call time — `from … import full_jitter` defeats A4's pins).
- Driver sleeps are observed at the `asyncio.sleep` call whose IMMEDIATE caller is `loremaster.store._txn` or
  `tenacity.asyncio` (`loremaster/tests/_driver_sleeps.py`): pass no `sleep=` to the conflict driver, or sleep from `_txn`.
- Scout: keep the post-drop backoff and the per-outage reset (§R7.1 ladder pin).
- `_txn` unknown-outcome message: both Q6 halves. `principals` renderers: bare keys (B-2; a mixed-table sentence serves
  `record_text`).
- Prose sweep at build: bare `_txn_conflict_backoff_seconds`, `_JitterRecorder`, `CommandSubscriber._backoff` survive
  in docs/docstrings (`loresigil/backoff.py` module docstring cites the deleted function).

## ROUND 6 — adversary round 2 answered: MP-A, MP-B, MP-C (contract-sdk3-r6; 2026-11-07, graded tree HEAD `ef1b20b`)

Answers ruling R15 (and R13's RS7 rider, R14) in `docs/plans/v2/sdk3-rulings.md`, against adversary round 2's report
(lead-persisted at `scratchpad/sdk3r5/ADVERSARY2.md`). This is the LAST contract round in the operator's budget.
Everything below is dated 2026-11-07, measured at HEAD `ef1b20b` (SDK 2.0.0, main venv; a pristine `git archive ef1b20b`
copy is `scratchpad/sdk3r6/headtree`) and on the ROUND-6 REFERENCE (SDK 3.0.0, `scratchpad/sdk3r6/ref` =
adversary round 2's `adv2/myref` + its `chk_c10` harness + the reference deltas of §R6.4; `scripts/scratch_copy.sh
--verify-only` VERIFIED, `loremaster.__file__` inside it in every log header). Rounds 1–5 below are history and are
not rewritten, except the two drop-list rows R15 named (§R3.5 rows #21/#22, edited in place with a dated note).

### R6.0 Summary

- **MP-A** (F-r5-3): `test_sdk3_outcome_reach::TestOneFilesStoreFaultNeverStopsTheSweep` — 6 nodes (3 outcome classes ×
  batch/realtime). The two unknown-NOT-landed nodes are RED on declared mutation M-A (`_landed_after_unknown` re-raises
  an unknown that did not land, the adversary's `wb_f18_abort`); the F18 pins stay green under it (the hole they had).
- **MP-B**: `slept == drawn` added to `test_retry_seam::TestRetryOnConflictDriver::test_every_attempt_draws_a_fresh_backoff_from_the_shared_jitter`
  (RED on M-B, equal-jitter drift, 1 of 709); scout sibling
  `test_backoff_seam::TestTheSubscribersConnectLadderSleepsTheSharedDraw` (RED on M-B2 in `_connect_wait`, 1 of 57).
- **MP-C**: the 117 worked by cause (§R6.2); the property is measured over the targeted set (§R6.5).
- **RS7 rider**: `test_sdk3_row_bound::TestAnUpsertBatchRidesTheRowCap` (over-cap RED at HEAD for the intended reason —
  HEAD's `upsert` loops `_query`; control green at HEAD).
- **R14**: `test_sdk3_served_outcome::…::test_every_pin_row_names_a_real_behaviour_pin` deleted; the walker-derived
  reach checks stay.

### R6.1 New and changed pins

| item | node(s) | kills | RED receipt |
|---|---|---|---|
| MP-A | `test_sdk3_outcome_reach::TestOneFilesStoreFaultNeverStopsTheSweep::test_the_sweep_returns_and_commits_every_file_the_fault_did_not_swallow[{unknown-NOT-landed,unknown-landed,definite-refusal}-{batch,realtime}]` | a per-file arm that raises out of `index_all` for any outcome class | M-A (2 declared = 2 observed); HEAD: the 4 unknown legs RED (class missing), the 2 definite legs GREEN |
| MP-B | `test_retry_seam::TestRetryOnConflictDriver::test_every_attempt_draws_a_fresh_backoff_from_the_shared_jitter` (+`_JitterRecorder.values`) | a driver that draws and sleeps something else | M-B (1 = 1) |
| MP-B sibling | `test_backoff_seam::TestTheSubscribersConnectLadderSleepsTheSharedDraw::test_every_slept_connect_backoff_is_the_shared_draw` | scout's tenacity `wait=` consulting the policy and returning another value | M-B2 (1 = 1). Stated bound: tenacity computes `wait` before `stop`, so the connect ended by `stop()` may draw ONE unslept value |
| RS7 | `test_sdk3_row_bound::TestAnUpsertBatchRidesTheRowCap::{test_an_upsert_batch_over_the_row_cap_is_refused_before_anything_is_sent, test_control_an_upsert_batch_under_the_row_cap_is_sent}` | `upsert` outside `compose` | RED at HEAD (intended); control GREEN at HEAD |
| am-37 3e | `test_am37_13_3_63c_i_a::TestTheMintWindowNotesTheRevokeRepair` rows: `TxnRowCapExceededError` → proven-no-key (refused at BUILD time, nothing sent); `SurrealOutcomeUnknownError` → unknown-outcome | an unadjudicated store class | `test_every_generated_store_class_is_adjudicated_by_the_ruling` RED at HEAD (the classes do not exist yet — "ruled class the taxonomy no longer defines"), intended |
| a19 3h | `test_fixwave_a19_63c_i_a::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19` — `_renderings` = {engine `<string> type::record(...)`, rendered live; bare key}; `_forbidden_rendering` refuses the SDK `str(RecordID)` form where it differs | a refusal serving SDK `str()` text (R7 (d)) | RED at HEAD on the hostile-id legs (HEAD serves `str(RecordID)`), intended |

### R6.2 MP-C — the 117, by cause (verdict + owner each)

| cause | nodes | verdict | edit |
|---|---|---|---|
| 3a F-a reach | test_retry_seam ~47 (`{'next':N} == [{'next':N}]`, brief/ack doubles, scout fakes), test_surreal_harness ×2 | CONTRACT (fakes SDK-2-shaped) | every `query()` return of every double in test_retry_seam → `one_statement_answer` (16 sites, instrument `scratchpad/sdk3r6/tools/wrap_query_returns.py`, pasted in Appendix G); the two harness `run` identity fakes |
| 3b C2 reach | 6 `AsyncSurreal` monkeypatches in test_retry_seam | CONTRACT | → `route_connections` |
| 3c C9 test tree | a28/a28b/a28c, comms_schema, governed_migration, agent_governance, comms_send, governed_schema, … | CONTRACT | `sdk3_shape_fakes` widened: `record_parts` / `bare_record_key` (strips one `⟨…⟩`/backtick layer) / `same_record`; **every cloned `_bare` deleted** (19 by helper c9-sweep-r6 + a19, `_bare_id` in test_pdp_oracle_61b, `_governed_contract_64.bare` → alias of the shared helper, and the split/endswith sites in test_agent_registry, _comms_fakes, test_preboot…, test_memory_replay…, test_principals_store, test_comms_tool, test_audit_schema, test_keeps_schema, test_enforced_relations). Determinism: `_governed_contract.digit_led_record_key` + `rekey_principal` (fixed digit-led keys; SDK 2 renders them bare, SDK 3 brackets them, so the old compare fails every run on SDK 3) |
| 3d StoreTraffic | test_blocks_edge ×7 | CONTRACT (instrument) | `StoreTraffic.COUNTABLE_DOORS` follows delegation through the connection class's private helpers (SDK 3.0's `query()` is a builder whose `_make_executor` calls `self.query_raw`); `_delegating` returns the SDK's object unawaited. Same 11 doors on SDK 2.0 (measured on headtree); reach stays deny-by-default (`require_full_reach`) |
| 3e am-37 rows | test_am37 ×5 | CONTRACT | rows added (R6.1). **Reference bug found:** `_txn._PROVEN_NO_KEY_CLASSES` lacked `TxnRowCapExceededError` → builder note B-1 |
| 3f spelling scans | socket-owner scans ×2, derivation RELATE regex ×3, governed SDK-name scan | CONTRACT (R15: rewrite or retire) | socket owners DISCOVERED BY BEHAVIOUR (`_ensure_connection` driven once with every constructor routed to a counting factory; candidates = classes owning `_ensure_connection`) — same 17 at HEAD and on the ref; derivation instrument EXECUTES the fragment in one transaction under ENFORCED code-graph edges (live store; order matters is the engine's verdict); governed scan narrowed to receivers that are not module `ContextVar`s (+ a control that the same method name on another receiver still flags) |
| 3g `test_ingest_entity_seam` ×8 | 8 | **TEST read shape, NOT a production regression** | `_ingest_entity_fixtures.FakeDomainStore.fetch_nodes` read via raw `connection.query`; SDK 3 answers `[[rows]]`, every row was filtered, phase 2 resolved no edge. Routed through `_txn.run_query`. Unchanged reference production: 45/45 |
| 3h a19 | 1 | CONTRACT + reference bug | R6.1; reference: `principals._id_sample` and the owner sample serve the bare key → builder note B-2 |
| 3i `ensure_ready:timeout` | 1 | REFERENCE BUG | ref `store/surreal.py` `ensure_ready` dropped its inner `connection.timeout(...)` (the decorator already applies it) |
| 3i bootstrap allowance | 2 (red at HEAD too) | CONTRACT (round-5 self-contradiction) | `_TEST_TREE_BOOTSTRAP_ALLOWANCES` row for `test_sdk3_outcome_reach.py`'s deliberately unsigned F-b fixture |
| harness identity ×2 | 2 | CONTRACT (F-a) | see 3a |
| beyond the 117 (found by widening the targeted set to the covering tests of the reference's changes) | q1b ×6, q1c ×1, pdp_oracle ×13 | CONTRACT | **q1b/q1c**: SDK 3.0 adds engine kind `TransactionConflict` ONLY as a Query DETAIL (`QueryDetailKind.TRANSACTION_CONFLICT`; `ErrorKind` lacks it — corrected in round 7 per R26-1a, measured by the lead on the installed 3.0.0; this cell first said "top-level and Query detail", which was false); the seam RETRIES it (the SDK's conflict typing is THE authority, drop row #2/R11), so it is ruled `retried` (a fourth fate: never a rejection, never proven; sustained → `TxnContentionExhaustedError`, proven by class) — derived, see FORK-R6-1; q1b's class table gains `TxnRowCapExceededError` (proven) and `SurrealOutcomeUnknownError` (unknown). **pdp_oracle**: its three raw `connection.query` reads → the harness `run` funnel (F-a/C10 reach). **a19a**: `_names` keys on the sanitised bare key every allowed form contains (a19 owns WHICH form) |

### R6.3 Packet-doc corrections
- §R3.5 row #22 now reads **R** (R11), row #21 notes its overlap with R11 (see the rows).

### R6.4 The round-6 reference delta (beyond `adv2/myref` + `chk_c10`)
1. `store/surreal.py` `ensure_ready`: no inner `connection.timeout` (rides `ensure_ready_operation`).
2. `store/_txn.py`: `TxnRowCapExceededError` defined before, and listed in, `_PROVEN_NO_KEY_CLASSES`.
3. `principals.py`: `_id_sample` and `_owned_unscoped_part` serve bare keys from the RecordID parts.
4. `store/surreal.py` `upsert`: one fragment through `apply` → `compose` (RS7).
5. Test-side (reference only, C10 builder work): `_surreal_harness.run` is `chk_c10`'s (first statement's result).
Pristine copies of each touched reference file: `scratchpad/sdk3r6/ref_pristine/`.

### R6.5 Satisfiability receipt
Property (R15 MP-C): every node of the targeted set GREEN at HEAD (with the round-6 tests) is GREEN on the round-6
reference. Targeted set = `scratchpad/sdk3r6/target_set_r6.txt` (142 files): round 5's 129 + every test file
round 6 touched + the covering tests of every production symbol the reference changed (`lore_impact` on
`SurrealStore.upsert` / `.ensure_ready`, `_txn.proven_no_key`, `principals._id_sample` /
`_owned_unscoped_part` — bare-name unions and 0-test answers per #563, so the q1b/q1c/note-q1, surreal_store/
apply, diff, indexer, mcp_server and every importer of the shared test helpers were added by hand). Receipts,
numbers and the both-ways red-set diff: the contract-sdk3-r6 hand-back report, §Satisfiability, over
`scratchpad/sdk3r6/logs/final3_{ref,head,headpristine}.log` (each with `tree_id.sh` + `loremaster.__file__`;
round 7 corrected `final2_*` → `final3_*` per R26-5: the final2 runs were killed, final3 is the receipt).

### R6.6 Per-C-row receipt table — THE COLD AUDIT FILLS THIS (named in its brief)
Every **C** (measure-then-decide) row of the drop list gets one line. A row with no measurement is not done.

| drop-list row | measurement (command / instrument) | result (numbers, log path, TREE) | fate (R / K + keep-reason) | auditor verified (sha) |
|---|---|---|---|---|
| #8 `_to_aware_utc` ×6 | | | | |
| #9 `_CONNECTION_ERRORS` / `_SDK_AWAIT_BOUNDARY_ERRORS` tuples | | | | |
| #14 hand verification + text BEGIN/COMMIT + `execute_read_transaction` | | | | |
| #15 `_SDK_PARSE_FAILURES` guard | | | | |
| #16 `_safe_close` ×18 | | | | |
| #17 `signin_credentials` + `.signin()` + manual re-sign-in | | | | |
| #19 `"recursion depth"` text marker | | | | |
| #21 scout reconnect ladder (now on tenacity per R11) | | | | |
| #24 inlined literals in `LIVE SELECT … WHERE` | | | | |
| #25 `name.value` mirror column | | | | |
| #26 `rebuild_embeddings` REMOVE/DEFINE dance | | | | |
| any C row added after round 6 | | | | |

### R6.7 Forks (written down, not silently resolved)
- **FORK-R6-1 (low)**: q1b/q1c rule SDK 3.0's `TransactionConflict` kind as a fourth fate, `retried`, rather than
  §15's proven/unknown. Reading A (taken): the kind never reaches the mint as a rejection because the seam's
  conflict classifier retries it, so the table records the seam's classification. Reading B: add it to §15 as
  `unknown` (the pin's own failure text offers only proven/unknown). B would assert a `TxnDomainRejectionError` that
  no correct build raises — unsatisfiable — so A; the operator may re-rule am-37 §15 to name the fourth fate.
- **FORK-R6-2 (low)**: a19's refusal pins and three ruling tables (am-37, q1b kinds/classes) now go RED AT HEAD by
  design (they name SDK-3-only classes/kinds or refuse HEAD's `str(RecordID)` serving). Reading A (taken): they are
  declared RED@HEAD pins like round 5's. Reading B: version-branch them like the F-a fakes so HEAD stays green.

### R6.8 Builder notes (outside the contract's writable set)
- **tenacity never awaits a non-coroutine callable's result** (`AsyncRetrying.__call__`, `is_coroutine_callable`
  branch): `retry_on_conflict(lambda: …)` returns an UN-awaited coroutine. Wrap the attempt in an `async def`
  (adversary round 2's `_run`), or iterate `async for attempt in AsyncRetrying(...)` with the call lexically inside.
- **tenacity computes `wait` BEFORE `stop`** (`_post_retry_check_actions`). ⚠ SUPERSEDED in round 7 (R18/R20,
  R26-5): there is no draw-count pin any more — the driver's wait is tenacity's own `wait_random_exponential` (via
  `loresigil.backoff.full_jitter`), an unslept final draw is native and harmless, and the pins observe only what is
  SLEPT (`test_sdk3_native_retry`). Do NOT add a stop-peeking `wait` adapter.
- **C10**: `_surreal_harness.run` returns the ONE statement's result on SDK 3.0 (the reference's is `chk_c10`'s:
  `results[0]`); `test_surreal_harness`'s identity pins now feed it SDK-shaped answers.
- **`store/surreal.py` `ensure_ready`**: its timeout rides `long_operation` (`ensure_ready_operation`) like the other
  16 owners — no direct `connection.timeout(...)`.
- **B-1**: `TxnRowCapExceededError` ∈ `_PROVEN_NO_KEY_CLASSES` (am-37 §14: refused at build time, nothing sent).
- **B-2**: `principals._id_sample` and the migrate refusal's owner names serve `str(RecordID)` at HEAD — a C9 sibling
  R12 named ("the served refusal text in principals.py"); serve the engine form or the bare key.
- **F-a drop list**: the SDK-2.0 branch of `sdk3_shape_fakes.one_statement_answer` goes in the pin commit (unchanged);
  `_ingest_entity_fixtures.fetch_nodes` now rides `run_query`, so it needs no branch.

## ROUND 5 — R11/R12 pinned (contract-sdk3-r5 item 1; contract-sdk3-r5b items 2–12; 2026-11-07, graded tree HEAD `80d2323`)

Answers rulings R11 (tenacity) and R12 (round-4 forks F18–F22, F-a…F-d, C9 class, RS7, X18/X19) in
`docs/plans/v2/sdk3-rulings.md`. Everything below is dated 2026-11-07 and measured at HEAD `80d2323` (SDK 2.0.0, main
venv) and on a ROUND-5 REFERENCE (SDK 3.0.0, `scratchpad/sdk3r5/ref`, `scripts/scratch_copy.sh --verify-only` VERIFIED,
`loremaster.__file__` inside it in every log header). lore MCP was DOWN all round (`lore_lore` ECONNREFUSED): every
structure question used grep/Read and THE ONE catch-site walker (`_catch_sites`); no friction filed (no lore tools).
Two authors: `contract-sdk3-r5` did item 1 (the C9 pin, committed `0ac1434`) and stopped; `contract-sdk3-r5b` did
items 2–12. Round 1–4 sections below are history and are not rewritten.

### R5.0 Summary

- **New pins: 37 nodes in 3 new files + 2 extended files**, plus the round-5a C9 pin (12 nodes, `0ac1434`). 23 are RED
  at HEAD for their intended reason (declared from `--collect-only` before the run = observed, diffed both ways); the
  14 GREEN at HEAD pin behaviours HEAD already has (X18/X19, the retry driver's fate/deadline, the
  digit-led/installed legs of the C9 siblings) and are shown failing by **16 declared mutation proofs** on the r5b
  reference (§R5.9).
- **The r5b reference** = the r5a reference (r4 reference + the C9 fix) + the deltas of §R5.8 (F18 fixes, C9-sibling
  fixes, C4, R11 tenacity port). Satisfiability over the targeted set: §R5.9.
- **Forks: F-r5-1…F-r5-4 (§R5.10).** Decisions needed: RS7's 90 fixture call sites; the `_surreal_harness.run` /
  `_sdk_guard` SDK-3 adaptations that live only in the reference tree (C10).

| item | pin node id(s) | wrong build it kills | mutation receipt (§R5.9) |
|---|---|---|---|
| 1 C9 (r5a, `0ac1434`) | `test_sdk3_record_ids::TestTheOwnerClassifierRecognisesTheOperatorWhateverItsKey` ×12 | owner classifier comparing two text forms of one record | unfixed r4 code 12/12 RED (r5a report) |
| 2 F18 publish | `test_sdk3_outcome_reach::TestAnUnknownPublishNeverReleasesItsVersion::{test_a_committed_publish_whose_reply_was_lost_keeps_its_version, test_control_a_refused_create_still_releases_its_version}` | `publish` releasing the minted version on an unknown outcome (re-mints a landed version) | f18pub |
| 2 F18 indexer | `::TestAnUnknownIndexCommitIsNotServedAsFailed::{test_a_committed_file_whose_reply_was_lost_keeps_the_committed_manifest, test_the_batch_sweep_keeps_the_committed_manifest_too, test_control_a_reply_lost_before_the_commit_is_not_served_indexed}` | `_index_chunks` / `_commit_batch_file` marking a landed commit `failed` with the purged prior chunk ids; and the opposite wrong build that answers every unknown with "indexed" | f18idx, f18lie |
| 2 F18 broad (calibration) | `::TestAnUnknownDriftFilingIsServedAsUnknown::test_the_note_names_the_outcome_unknown_not_failed` | `status()` serving "drift finding filing failed" for an unknown filing | f18cal |
| 2 F18 reach | `test_sdk3_served_outcome::TestEveryStoreErrorFamilyCatchSiteIsAdjudicated` ×3 (derived set; 14 sites at HEAD-shape, 13 on r5b where `publish` is shielded) | a NEW `SurrealStoreError`-family catch site an unknown outcome reaches, with no adjudication; a stale verdict row; a pin row naming no test | derived-set pin (the walker's own reach); see §R5.1 |
| 3 C9 sibling: governed `_bare` | `test_sdk3_record_ids::TestTheGovernedGateRecognisesTheOwnerWhateverItsKey` ×6 | the gate splitting `str(RecordID)` — the row's own owner DENIED (access decision) | c9gov |
| 3 C9 sibling: refusal text | `::TestTheDanglingSenderRefusalServesTheEnginesText` ×3 | served message/sender ids `message:⟨01…⟩` instead of the engine's text | c9refusal |
| 3 C9 sibling: memory replay | `::TestTheMemoryReplayClosesThePredecessorWhateverTheOwnerKey` ×6 | the replay close comparing split rendered text — a superseded predecessor REVIVED by restore | c9mem |
| 4 F-b | `test_sdk3_outcome_reach::TestAServerAnsweredErrorIsADefiniteFailure::{test_the_single_statement_seam, test_the_transaction_seam}` | every connection-classified error (incl. a server-ANSWERED `NotAllowedError`) mapped to outcome-unknown | fb |
| 5 F-a | `sdk3_shape_fakes.one_statement_answer` in the 3 C1 doubles (`test_retry_seam._ScriptedConnection`, `test_scout._FakeCommandConnection`, `test_comms_await._FakeLiveConnection`) + drop-list row #37 | HEAD reddened by SDK-3-shaped fakes, or the reference graded by SDK-2-shaped ones | satisfiability (§R5.9) |
| 6 F-d / F22 | retired: `test_comms_await::…::test_no_inline_sdk_await_boundary_tuple_survives_in_scout_or_the_awaiter`; `test_backoff_seam::…::test_the_allowlisted_file_still_contains_what_it_was_exempted_for` | — (vacuous / spelling) | — |
| 7 R11 | `test_sdk3_retry_policy::TestTheExhaustionFateIsTheSeamsTypedError` ×3, `::TestTheDeadlineIsReadPerCall` ×2; T1/T2/RP3/`test_retry_seam` UNCHANGED on the tenacity reference | a leaked `RetryError`; a frozen/shared deadline; a per-attempt exhaustion log; a `retry=` that bypasses the seam's classifier | r11leak, r11frozen, r11perattempt, r11classifier |
| 8 X18/X19 | `test_sdk3_nested_lifecycle::TestAComposingStoreClosesItsNestedPrincipalStore` ×2, `::TestARecallDuringARebuildWaitsForIt` ×1 | a `close()` that forgets the nested `PrincipalStore`; a recall not serialised against the rebuild | x18a, x18b, x19 |
| 9 RS7 | drop-list row #38 (no pin: a deletion) | — | grep receipt §R5.6 |
| 10 C2/C3/C8/C4 | C2 `sdk3_shape_fakes.route_connections` (`test_retry_seam._point_at`, 6 counting-factory sites); C3 deleted; C8 `bare_record_key`; C4 `test_sdk3_record_ids::TestTheAuditAppendServesTheEnginesText` ×3 | C4: `append` handing back `audit:⟨01…⟩` | c4 |

### R5.1 Item 2 — F18: D1 over the `SurrealStoreError` family (14 sites) and the 39 broad sites

**Instrument:** THE ONE walker (`_catch_sites.production_catch_sites`); the round-5a census (`scratchpad/sdk3r5/census_broad.py`,
output `census_r5.tsv`: 6 NAMED, 14 STOREERR, 39 BROAD — matches R12's 14). The family derivation is now a standing pin
(`TestEveryStoreErrorFamilyCatchSiteIsAdjudicated`, beside D1's): a caught class in the family that
`SurrealOutcomeUnknownError` subclasses, reachable (no earlier clause catches it), excluding D1's transport-naming sites.
A PIN row may leave the derived set (a fix shielding it with `except SurrealOutcomeUnknownError: raise` makes it
unreachable — the behaviour pin still guards it); a VERDICT row whose site is gone is RED. ⚠ The scanner-approval
question R12 raised for D1's walker reuse applies to this widening too (operator pending).

**The 14 family sites — verdicts (r5b, each from reading the handler):**

| site | verdict |
|---|---|
| `briefs.py::publish` | **DEFECT → PINNED.** Releases the minted version on any store error; an unknown-but-landed CREATE leaves the counter one behind the row, the next publish re-mints that version and its `uuid5` CREATE collides. Reference fix: `except SurrealOutcomeUnknownError: raise` before the family catch. Pin reading per the brief: the error PROPAGATES as unknown (fork F-r5-2 names the alternative). |
| `index/indexer.py::_index_chunks` | **DEFECT → PINNED.** Marks the file `failed` with the PRIOR chunk ids after a commit that may have landed (and purged them). Reference fix: `_landed_after_unknown` re-reads the manifest; landed ⇒ `indexed`, else the existing failure path. |
| `index/indexer.py::_commit_batch_file` | **DEFECT → PINNED** (same as above, batch arm, through `index_all` two-pass). |
| `index/indexer.py::_resolve_all_extension_edges` | label-only: the scope lands in `IndexSummary.scopes_failed`, which no served surface renders (grep: only tests read it); the purge-then-RELATE re-runs idempotently on the next productive sweep; state never wrong. Not pinned; residual R5-r1. |
| `briefs.py::_relate_briefed` | re-reads the edge: a landed unknown write reports `already_acked=True` (true state, imprecise label). Not pinned. |
| `briefs.py::_release_version` | log-only, possibly false; reached only on a definite rejection once `publish` is shielded. Not pinned. |
| `floor_calibration/store.py::_fence_verdict` | wraps a READ, re-raises the original error. Not pinned. |
| `principals.py::_dispatch` | lore-adm prints the error's own message (an unknown error says so). Not pinned. |
| `store/lease.py::get` | READ → the library's non-404 "lock unavailable"; nothing created this tick. Not pinned. |
| `store/lease.py::create` | `False` = "did not win this tick", never served; a landed create is observed by the next `get()` (this identity as holder) and renewed — safe direction (no second leader). Not pinned. |
| `store/lease.py::update` | as `create`. Not pinned. |
| `store/lease.py::release_if_held` | `False` leaves the lease held until expiry (one `lease_duration` of stalled handoff) — safe direction. Not pinned. |
| `tasks.py::_reject_unusable_blockers` | READ pre-check: "NOTHING was created" is true; retry safe. Wording residual R5-r2: it says the read was "REJECTED by the store" for a transport fault too. Not pinned. |
| `tasks.py::transitive_blockers` | READ: serves no answer and says retry — honest. Same wording residual. Not pinned. |

**The 39 broad sites — my one-line verdicts** (spans extracted verbatim by `scratchpad/sdk3r5/extract_handlers.py` into
`broad39_handlers.txt`; the round-5a Sonnet draft `broad39_verdicts.tsv` agreed with these on 35/39 categories — its 4
UNSURE rows are resolved below):

| site | verdict |
|---|---|
| calibration/engine.py::_count_live_total:395 | READ (HTTP token count) → retryable `_ProbeUnavailableError`; no store write |
| calibration/engine.py::_count_live_total:398 | cleanup (`suppress` around `aclose`) |
| calibration/engine.py::_file_drift_finding_deduped:552 | **RENDERS DEFINITE → PINNED** ("drift finding filing failed" in `status()` / `index_status`) |
| calibration/engine.py::_probe_loop:354 | log-only crash guard |
| index/indexer.py::index_file:603 | the try body is the CHUNKER (no store call) — no outcome-unknown reaches it |
| index/indexer.py::_walk_and_index:1278 | same (chunker) |
| index/indexer.py::_walk_collect_tier:1650 | same (chunker) |
| index/reconcile.py::_maybe_stamp_snapshot:255 | advisory log after a successful sweep; not served |
| index/watcher.py::read_events:258 | inotify degrade; no store |
| memory/local.py::remember:707 | pass-through; compensates ONLY on `TxnDomainRejectionError`, keeps the ledger row on transport/unknown (#441) — honest |
| principal_keys.py::mint:485 | pass-through + `_mint_fault_note` ("unconfirmed" for transport) — the prior art |
| scout.py::aclose:954 | cleanup |
| scout.py::_dispatch:397 | marks the COMMAND failed with the error text — true of the command (it raised before completing); scout commands are idempotent sweeps; F20 keeps scout's raw contract. Not pinned (draft UNSURE → resolved) |
| scout.py::_open_command_connection:236 | pass-through (close, re-raise) |
| scout.py::_periodic_reconcile:900 | log-only backstop |
| scout.py::run:979 | cleanup (signal-handler `suppress`) |
| scout.py::run:986 | cleanup |
| scout.py::start:862 | pass-through (close readied, re-raise) |
| scout.py::start:865 | cleanup |
| search.py::_enrichment_lines:1415 | READ: annotates "enrichment unavailable" — honest |
| server.py::aclose:9091 | cleanup |
| server.py::aclose:9119 | cleanup |
| server.py::build_app_context:10120 | pass-through (teardown, re-raise) |
| server.py::build_app_context:10132 | cleanup |
| server.py::build_app_context:10140 | cleanup |
| server.py::build_app_context:9878 | pass-through |
| server.py::build_app_context:9882 | cleanup |
| server.py::_eager_build_or_operator_safe_error:10580 | fail-closed startup refusal; the build is idempotent at the next start; not a served write-outcome claim. Not pinned (draft UNSURE → resolved) |
| server.py::_eager_build_with_retry:10496 | pass-through (whole idempotent build retried, last error raised) |
| server.py::on_call_tool:10681 | log-only (trace emit) |
| server.py::_periodic_reconcile:10441 | log-only backstop |
| server.py::run_probe_gate:2287 | READ (embedding probe) |
| server.py::_run_schema_rebuild:10415 | `mark_rebuild_failed` for a rebuild that RAISED before finishing — true of the rebuild process; fingerprint unstamped ⇒ re-runs next start. Not pinned (draft UNSURE → resolved); residual R5-r3: if the raise was an unknown outcome on the LAST write, the status says failed for work that may be complete (self-heals by re-run) |
| server.py::run_startup_hooks:972 | pass-through |
| server.py::run_startup_hooks:979 | cleanup |
| testing/loopback.py::_loud_teardown:456 | test infrastructure, pass-through |
| testing/loopback.py::_loud_teardown:461 | test infrastructure, cleanup |
| testing/loopback.py::_run:321 | test infrastructure (crash recorded for `start()`) |
| testing/loopback.py::start:341 | test infrastructure, pass-through |

### R5.2 Item 3 — C9's class at its siblings (R12)

Probed 2026-11-07 on the 3.3.5 TEST store (`probe_engine_text.py`, Appendix F): the ENGINE renders a digit-led
alphanumeric key bare (`t:01JCXZ…`, `t:9c9operator…`) and a non-word or all-digit STRING key in backticks
(``t:`c9-op.erator` ``, ``t:`1234` ``); SDK 3.0.0 `str(RecordID)` brackets digit-led AND non-word keys with ⟨⟩; SDK
2.0.0 brackets non-word keys with ⟨⟩ (digit-led bare). Array keys (`code_node`) render identically in all three
(`probe_array_key.py`). **Consequence found by the pins: two of the siblings are ALREADY wrong at HEAD on SDK 2.0 for
non-word keys** (`non_word-installed` RED at HEAD: the governed gate denies the owner; the replay revives the
predecessor). Lore's mints never produce non-word principal/agent keys today (engine ids, uuid5 hex), so it is latent
at HEAD and becomes live for ~28 % of principals (digit-led) under SDK 3.0.

- **`governed.py` `_bare` (access decision, first priority).** Pinned; reference fix takes `.id` from a RecordID.
- **`principals.py` dangling-sender refusal text.** Pinned against the engine's own `<string> id` / `<string> sender`
  (read in-test, never restated); reference fix `record_text`. ⚠ Bound (C6): `record_text` is the parts-join, which
  equals the engine form for WORD keys only; message ids (ULIDs) and agent ids (uuid5 hex) are word keys, so it holds
  for this surface. A non-word key would need the engine's `<string>` projection (RS4's form).
- **`memory/local.py` two owner compares.** Proven by EXECUTION that the `getattr(…, "record_id", None)` guard never
  applies: `RecordID` attributes on SDK 2.0.0 = `['_escape_identifier', 'id', 'parse', 'table_name']`, on 3.0.0 =
  `['_unchecked', 'id', 'parse', 'table_name']` — no `record_id`. Every compare falls to `str(link).split(":")[-1]`.
  Pinned; reference fix takes `.id`.
- **C4 `AuditStore.append`** (item 10, same class): pinned against the engine's `<string> id`; reference fix
  `record_text`. The pre-existing 64b spy reddens on that build only incidentally (`endswith` trips on `⟩`).
- **Sibling-sweep spot check** (`c9_siblings_verdicts.tsv`, Sonnet draft, 97 rows): I checked **27 of 97** — all 4
  AT-RISK (each confirmed and pinned), all 11 SAFE rows (read; the one served array-key row probed equal), and a random
  12 of the 82 NOT-A-RECORD rows (each re-read at its line). **0 wrong.** 70 rows unchecked.

### R5.3 Item 4 — F-b

An anonymous connection (connected, `use()`d, never signed in) has every write ANSWERED by the server with
`NotAllowedError` ("Anonymous access not allowed", measured on SDK 2.0.0 and 3.0.0, `probe_notallowed.py`). At both
seams (`run_query`, `execute_transaction`) the raised error must be a `SurrealStoreError` that is NOT
`SurrealOutcomeUnknownError`. The existing THROW pins (`test_sdk3_txn_classification::TestADomainRefusalIsNotRetried…`)
already cover the domain-rejection door; F-b's door is the connection-CLASSIFIED server answer, which the "every
`is_connection_error` → unknown" wrong build (mutation fb) maps to unknown.

### R5.4 Item 5 — F-a: the doubles answer per SDK version

`loremaster/tests/sdk3_shape_fakes.py` (new, test-side): `SDK_MAJOR` from `importlib.metadata`, and
`one_statement_answer(result)` = `[result]` on SDK ≥ 3 (R2: the seam selects its one statement), `result` bare on 2.0.
Applied at the C1 doubles' return points only (`test_retry_seam._ScriptedConnection.query`,
`test_scout._FakeCommandConnection.query` ×4, `test_comms_await._FakeLiveConnection.query` ×2).

| # | what | where | fate |
|---|---|---|---|
| 37 | the SDK-2.0 branch of `sdk3_shape_fakes.one_statement_answer` (and `SDK_MAJOR`) | `loremaster/tests/sdk3_shape_fakes.py` | **R — the builder deletes it in the commit that pins `surrealdb==3.0.0`** (R12 F-a); the helper's callers stay |

### R5.5 Item 6 — F-d and F22 retirements

- **F-d:** `test_comms_await.py::TestAwaitSharesTheSdkBoundaryConstantByMutation::test_no_inline_sdk_await_boundary_tuple_survives_in_scout_or_the_awaiter`
  DELETED (its pattern — a bare `KeyError` inside `(*_CONNECTION_ERRORS, KeyError)` — cannot occur after R6 F10); the
  section comment now says so. The runtime-mutation sharing pin beside it stays. Other C7 prose (test_comms_await.py
  module docstring lines naming the KeyError arm, test_scout, test_retry_seam `_MARKER_NAME`, …) is NOT edited
  (outside this item; residual R5-r4).
- **F22:** `test_backoff_seam.py::TestNoNewHandRolledBackoff::test_the_allowlisted_file_still_contains_what_it_was_exempted_for`
  DELETED (a source-text check of `_txn.py`'s spelling), with a comment at its place. Behaviour clauses kept (every
  declared site draws from the mutated policy; the perimeter scan; its positive control). Fork F-r5-1: `_POW_ALLOWLIST`
  still exempts `_txn.py`, which needs no exemption once the draw delegates.

### R5.6 Items 7–9 — R11 tenacity, X18/X19, RS7

**R11 (with F22) — the tenacity REFERENCE** (`build_ref_r5b_tenacity.py`, Appendix F; read: installed tenacity 9.1.4
`stop.py`, `wait.py`, `retry.py`, `__init__.py`, `asyncio/__init__.py`):
- `retry_on_conflict` = a per-call `AsyncRetrying(stop=stop_any(stop_after_attempt(CEILING), stop_all(stop_after_delay(deadline),
  stop_after_attempt(FLOOR))), wait=_conflict_wait, retry=retry_if_exception_type(RetryableConflictSignal),
  sleep=_conflict_sleep)`; `RetryError` caught and translated into the unchanged exhaustion disposition (one
  `store.retry.exhausted` record with label/url/last cause; `TxnContentionExhaustedError`). Classification stays in
  `_raise_attempt_failure` / `_rollback_verdict` — `retry=` matches only the signal type (sharing, not routing).
- `_txn_conflict_backoff_seconds` stays the ONE conflict-jitter source and delegates to
  `loresigil.backoff.jittered_backoff_delay(attempt_number - 1, base_s=…, cap_s=…)` (tenacity
  `wait_random_exponential`); its private `random.uniform` draw is gone. `_conflict_wait` / `_conflict_sleep` look up
  the jitter source and `asyncio.sleep` at CALL time, so `test_retry_seam`'s recorder and sleep silencer still reach them.
- `scout`: the connect half of the reconnect ladder runs on `AsyncRetrying` (`_connect_with_backoff`, stop when
  `_running` is False, `wait` = `_backoff_delay(first_attempt + n - 1)` — the identical attempt indices the hand ladder
  used); `_backoff` stays the shared-policy site `test_backoff_seam` drives.
- **Pins:** `test_sdk3_retry_policy` (5 nodes, GREEN at HEAD and on the reference — behaviour preserved; RED by
  r11leak / r11frozen / r11perattempt). **Sharing by mutation:** r11classifier makes the seam's classifier
  (`_is_retryable_conflict_kind`) answer False → T1/T2 RED. **No "uses tenacity" pin.**
- **Removed-behaviour inventory (R11 rider), preserved-with-pin:** X21 deadline (floor 5, ceiling 64, per call, default
  read at call time) → `TestTheDeadlineIsReadPerCall` ×2 + `test_retry_seam` deadline/floor pins; X22 one exhaustion
  record with the LAST cause, nothing on a resolved conflict → `test_exhaustion_raises_the_typed_error_and_logs_only_the_last_cause`,
  `test_a_conflict_that_resolves_returns_the_value_and_logs_nothing`; the per-attempt `_log_rollback` on the
  transactional path is untouched (it lives in `_run_verified_transaction`'s attempt body, outside the driver) and stays
  pinned by `test_retry_seam`'s rollback-log pins; X23 exhaustion fate/attempt count → `type(error) is
  TxnContentionExhaustedError`, `error.attempts == calls made`.

**X18/X19** (`test_sdk3_nested_lifecycle.py`): X18 observed at the SDK's own connection class
(`AsyncWsSurrealConnection.__init__`/`close` wrapped — factory-blind); X19 name-blind (bounded settle time; no branch
on the `_rebuild_lock` attribute, unlike `test_schema_rebuild`'s race pins). GREEN at HEAD and on the reference; RED by
x18a/x18b/x19.

**RS7 — `SurrealStore.upsert` (grep, lore down):** `grep -rn '\.upsert(' loremaster/loremaster lorerunes loresigil
lorescribe scripts skills` (185 non-test `.py` files scanned) → ONE hit, `indexer.py` `self._manifest.upsert(` =
`SurrealManifest.upsert`, a different method. **0 production callers.** Test call sites of a store `.upsert(`: 90 in 7
files (test_surreal_store 51, test_surreal_fakes 25, test_symbols 6, test_floor_calibration_store 4, test_search 2,
test_extension 1, test_startup_divergence_reconcile 1); tests that pin the door itself:
`test_surreal_store::{test_reupsert_same_records_is_idempotent, test_wrong_dim_vector_rejected_loudly_at_upsert,
test_upsert_scroll_round_trips_production_shaped_metadata_top_level}` plus `FakeSurrealStore.upsert` (`_surreal_fakes`)
and its tests in test_surreal_fakes. NOT rewritten this round, and the reference keeps `upsert` (decision needed §R5.10).

| # | what | where | fate |
|---|---|---|---|
| 38 | `SurrealStore.upsert` (RS7, R12: a dead door, 0 production callers, outside batching and the row cap) | `store/surreal.py` | **R (delete)** — blocked on the 90 test seeding sites (decision needed): their behaviour pins (wrong-dim rejection, metadata round trip, idempotence) must move to `apply([replace_file_fragment(...)])` first |

### R5.7 Item 10 — test-side contradictions

- **C2:** `sdk3_shape_fakes.route_connections(monkeypatch, factory, modules=…)` rebinds every name in the named
  loremaster module(s) that is bound to `surrealdb.AsyncSurreal` or to `_txn.open_surreal_connection` — DERIVED from
  the live module objects, so it holds at HEAD (per-module `AsyncSurreal`) and after R5 (the shared factory), and it
  returns the bindings it replaced (`_point_at` asserts non-empty). Applied: `test_retry_seam._point_at`; the counting
  factories (`factory(url, **options)` → `_RealAsyncSurreal(url, **options)`) and their 6 call sites in
  test_surreal_store (4) / _manifest (1) / _graph (1). ⚠ NOT applied (same class, outside the lines C2 named): 
  `test_retry_seam` lines patching `scout_module`/`surreal_module` `AsyncSurreal` directly (≈7 sites near
  `TestScout…` / bootstrap sections), `test_comms_cli`, `test_ingest_entity_seam`, `test_surreal_harness` (residual R5-r5,
  exact edit: the same one-line `route_connections(..., modules=(<module>,))`).
- **C3:** `test_surreal_store.py`'s `if TYPE_CHECKING:` import of `_RETRYABLE_CONFLICT_KIND` and `_ruled_a28c_store`
  deleted (grep: no reference anywhere, incl. `scripts/pending_contracts.yaml`); `TYPE_CHECKING` import dropped.
- **C8:** `sdk3_shape_fakes.bare_record_key` is the one helper; both `_bare_s` definitions became
  `_bare_s = bare_record_key` (call sites untouched).
- **C4:** pinned (§R5.2).
- **C5** (`test_exhaustion_fates` "store/lease.py … FATE CHANGED ['logs-error-class']" on the reference only):
  the lease HANDLERS are byte-identical at HEAD and on the reference (`diff`: only the factory call and the
  `ensure_ready_operation` decorator changed), so the changed fate is not a lease-code change; adjudicated from the
  satisfiability run (§R5.9).
- **C6:** CONFIRMED by probe — the engine renders non-word / all-digit string keys in backticks and `record_text`
  (parts-join) does not; `record_text` is therefore a COMPARISON form (key equality), and an engine-form SERVED text for a
  key that can be non-word must come from the engine's `<string>` projection (RS4). Every surface this round fixed with
  `record_text` serves word keys only (stated bound, §R5.2).
- **C10 (new, outside the writable set):** the reference tree carries SDK-3 adaptations of two shared test helpers that
  the main tree does not — `_surreal_harness.run` selects the one statement's result (R2) and drops
  `AsyncEmbeddedSurrealConnection`; `_sdk_guard` drops it and carries an `_is_door` predicate. After the build, every
  test calling `run()` receives a per-statement list. Exact edit: make `run()` answer through
  `sdk3_shape_fakes.one_statement_answer`'s rule (version-aware), and guard the embedded-connection import.

### R5.8 The r5b reference (a satisfiability instrument, not the build)

Delta over r5a (`scratchpad/sdk3r5/reference_r5b_delta.diff`, 9 files; instruments `build_ref_r5b.py` +
`build_ref_r5b_tenacity.py`, Appendix F): `briefs.publish` shields the unknown outcome; indexer `_landed_after_unknown`
+ its two call sites; calibration unknown note; `governed._bare` from parts; principals refusal `record_text`;
memory/local owner keys from `.id`; `audit.append` `record_text`; `_txn` tenacity port + jitter delegation; scout
`_connect_with_backoff`. NOT done: RS7 deletion (keeps `upsert`), C10, the D1/F18 residuals above.

### R5.9 Receipts

Logs: `scratchpad/sdk3r5/logs/`; each opens with `tree_id.sh` and (pytest logs) `loremaster.__file__` + `surrealdb=`.

| gate | log | EXIT | count | TREE |
|---|---|---|---|---|
| RED at HEAD, the 37 new nodes (SDK 2.0.0; declared `head_declared_red.txt` from `--collect-only` BEFORE the run) | `r5_head_red.log` | 1 | **23 failed, 14 passed**; observed FAILED set == the 23 declared, diffed both ways; 0 import/collection errors | `35f7ffcb…3c92` |
| 16 mutation proofs on the r5b reference (`run_mutations.sh`, `scripts/mutation_proof.py`) | `r5_mutation_proofs.log` | 0 each | **16/16 PROOF HELD**; prod tree vs pre-run content backup: no diff | `3fdcb608…3588` (r5b ref) |
| targeted set, HEAD (129 files = r4's 73 + 56: every file touched + grep-derived covering tests of every changed symbol, `target_set.txt`) | `r5_target_head.log` | 1 | 597 failed, 8357 passed, 44 skipped, 3 xfailed, 4 errors | `35f7ffcb…3c92` |
| targeted set, r4 baseline (r4 production + THIS round's test tree, `scratch_copy.sh`-verified `base_r4`) | `r5_target_base_r4.log` | 1 | 734 failed, 8210 passed, 47 skipped, 3 xfailed, 5 errors | `a668a8d6…b4cb` |
| targeted set, r5b reference | `r5_target_ref.log` | IN FLIGHT at hand-back (99 %) | — attribution (`attribute.sh`) owed | `3fdcb608…3588` |
| a28 class ×3, r4 reference | `a28_r4ref_{1,2,3}.log` | 0/0/1 | 42/42/40 passed (2 failed, `owner_classification 'foreign'`) — the C9 flake reproduced | `a9108e3e…af43` |
| a28 class ×3, HEAD | `a28_head_{1,2,3}.log` | 0/0/0 | 42 passed ×3 | `35f7ffcb…3c92` |
| a28 class ×3, r5b reference | `a28_r5bref_{1,2,3}.log` | queued after the ref target run | — | — |
| currency `--legs typecheck,ruff` | `r5_currency.log` | 1 | ruff GREEN; typecheck RED_ORPHANED 1 (`test_sdk3_outcome_reach.py`: `connect()` call-arg) → FIXED (`connect(env.url)`) after the run; currency NOT re-run; pytest NOT_RUN (quirk) | stale (pre-fix) |

⚠ The one-line typing fix in `test_sdk3_outcome_reach.py` (`connection.connect(env.url)`) and this doc changed AFTER the HEAD/RED/mutation runs started; behaviour is identical (both SDKs' `connect(url=None)` accept the URL) but those TREE ids are formally void for the final tree.

### R5.10 Forks and decisions needed

- **F-r5-1 (F22 reach):** R12 retires `test_backoff_seam`'s source-text clause; its `_POW_ALLOWLIST` still exempts
  `_txn.py`, which needs no exemption once the draw delegates (the reference has no variable power left in it). (a) leave
  the allowlist (a standing hole for a future hand-rolled exponent in `_txn.py`, the hazard the retired clause guarded);
  (b) empty it — the perimeter then goes RED at HEAD until the build deletes the draw (an R11 pin). I implemented (a), the
  literal reading; **recommend (b) in the build commit.**
- **F-r5-2 (publish fate):** the brief and the pin say an unknown publish PROPAGATES the unknown error. A build could
  instead VERIFY (re-read the row) and return the published version. Both are D1-honest; the pin admits only the
  first. Recommend keeping propagation (the caller learns the outcome is unknown; the version is safe either way).
- **F-r5-3 (indexer verify):** the pin admits a build that either verifies (my reference) or raises the unknown error
  out of `index_file` / `index_all`; it rejects only "failed with prior ids" and "indexed without the commit". A raised
  error out of `index_all` would abort the sweep — the operator may want that ruled out.
- **F-r5-4 (scanner):** the F18 reach pin widens the D1 walker reuse R12 already raised to the operator.
- **Decision needed — RS7's 90 test seeding sites** (7 files, outside the writable set except the 3 door-pinning
  tests): R9 D3 makes them contract surface; the brief limits this round to tests that pin the door. Recommend a round-6
  item: one shared seeding helper over `apply(...)`, the 3 door pins re-keyed to `apply`, then the deletion.
- **Decision needed — C10** (shared harness helpers adapted only in the reference).

### R5.11 Routing, DRY ledger, bounds

- **Routing (written before the first sweep; the report-file write was refused by the harness, so it is carried in the
  hand-back):** test runs → haiku-runner ×7 (RED@HEAD, mutation proofs, three target-set runs, a28 ×3 ×3); the 14 + 39
  site verdicts and the sibling spot check → me (spans extracted by a script, read in full); every pin and the reference
  → me. Fan-out: haiku 7 · sonnet 0 · peak 5.
- **DRY ledger (all test-side):** `sdk3_shape_fakes.one_statement_answer` (C1/F-a; looked: grep `one_statement|SDK_MAJOR`
  in tests → only r4-d3's scratch probe → NEW, the one home); `route_connections` (C2; looked: `_count_sdk_connections`
  counts at the SDK class but cannot hand back a double → NEW, complements it); `bare_record_key` (C8; REPLACES the two
  `_bare_s` copies); `test_sdk3_outcome_reach._lose_the_reply` (looked: `test_sdk3_served_outcome._RaisingOnSecondCall`,
  `test_mcp_server._LedgerRaisingOnSecondCall` raise WITHOUT running the call — no commit-then-raise exists → NEW);
  `_UnknownFilingPort` (EXTENDS `test_calibration_engine._FakeFindingsPort`); `test_sdk3_nested_lifecycle._watch_sdk_connections`
  (near `test_surreal_store._count_sdk_connections`, which counts creations only — this also records closes; candidate to
  merge into one helper); reused as-is: `a19._governed_world`, `_governed_contract.{store_handle, member, admin,
  seed_message_legacy}`, `test_memory_replay_fidelity_63b_ib.{dirty_world, _orphan_the_successor_in_the_store, _governed_row}`,
  `test_schema_rebuild.{_WindowBarrierMemoryBackend, _make_memory_backend}`, `test_indexer(_bulk_sweep)` builders,
  `_rendered` / `_RENDERINGS` (round 4/5a).
- **Packages considered:** retry/backoff — tenacity 9.1.4 (read above) → replace_with_adapter (R11); everything else
  reuses repo instruments.
- **Bounds:** X19's unserialised leg relies on one local recall finishing within 1.5 s (measured in ms); the F-b pin
  covers the anonymous-write `NotAllowedError` door, not every server-answered class (THROW is pinned elsewhere); the
  C9-sibling pins use word keys for served text (C6).

## ROUND 4 — adversary round 1 closed (contract-sdk3-r4, 2026-11-07, graded tree HEAD `00dc152`, report-time HEAD `ee4d754`)

Answers `adversary-sdk3-r3` (graded `d84cd6c`: INSUFFICIENT on MP1–MP3) under rulings R8 and R9 (`docs/plans/v2/sdk3-rulings.md`),
plus R10/R11 (committed during this round: `1592b89`, `ee4d754`, docs only). Everything below is dated 2026-11-07. Measured at
HEAD (SDK 2.0.0, main venv) and on a ROUND-4 REFERENCE BUILD (SDK 3.0.0): the round-3 reference (`scratchpad/adv/base`) plus the
r4 deltas in §R4.9, in a `scripts/scratch_copy.sh`-verified copy (`scratchpad/sdk3r4/ref`). lore MCP was DOWN all round
(`lore_lore` ECONNREFUSED): every structure question went through grep/Read and the ONE catch-site walker; no friction filed
(no lore tools in the session). The round-1–3 sections below are history and are not rewritten.

### R4.0 Summary

- **New pins: 27 (2 new files + additions/strengthenings in 5 contract files), each RED at HEAD for its intended reason or
  shown failing by mutation; 13 r4 mutation proofs (12 HELD, 1 mis-declared — §R4.10).** New files:
  `test_sdk3_row_bound.py` (MP1/F12 + D2), `test_sdk3_served_outcome.py` (D1/MP4). Extended: `test_sdk3_connection_factory.py`
  (MP2 read siblings, MP3 ∀-owner + index, CF1 → outcome-unknown), `test_sdk3_lifecycle.py` (L3 → outcome-unknown, L6 45 s),
  `test_sdk3_record_ids.py` (RS4), `test_sdk3_native_shapes.py` (RS6), `_sdk3_proxy.py` (frame-aware hold on a large request).
- **D3 — the pre-existing pins that encode retired rulings are rewritten here** (§R4.7): the statement-cap family by this
  author; the KeyError / `_RETRYABLE_CONFLICT_KIND` / `str(RecordID)`-oracle family (39 adversary rows) by an Opus helper
  (`contract-sdk3-r4-d3`) under this author's brief; every row has its own verdict, each confirmed by a run.
- **RED at HEAD: 25 declared from `--collect-only` before the run = 25 observed, diffed both ways (5 GREEN at HEAD by design).**
- **Forks: F18–F22 (§R4.11).** F22 is a contradiction INSIDE R11 (delete the jitter draw vs keep `test_retry_seam` unchanged).

| item | pin node id(s) | wrong build it kills | mutation receipt (§R4.10) |
|---|---|---|---|
| MP1 / F12 rider | `test_sdk3_row_bound::TestNoStatementCapSurvives::{test_compose_accepts_more_than_the_retired_statement_cap_of_single_row_statements, test_apply_sends_more_than_the_retired_statement_cap_of_single_row_statements}`, `::TestTheRowCapIsTheOneBound::{…two_statement_batched_fragment_over_the_row_cap_is_refused_naming_the_cap, …single_row_statements_count_one_row_each_against_the_cap, …apply_refuses_over_the_row_cap_before_anything_is_sent}` + rewritten `test_surreal_apply::TestComposeRowHardCap` ×3, `::TestApplyRowHardCapNeverReachesTheServer`, `test_ingest_entity_seam::TestOneImplementation` | statement cap kept in `compose` (the round-3 reference) / in `SurrealStore.apply` | f12a (5 of 6 declared fired; 1 mis-declared), f12b HELD |
| D2 | `test_sdk3_row_bound::TestTheSizeWarnFiresOnRows` ×2; rewritten `test_surreal_apply::TestApplyTxnSizeTelemetry::test_apply_warns_above_the_row_threshold` | statement-only warn; statement warn beside the row warn | d2b HELD, d2a HELD |
| MP2 / F14 | `test_sdk3_lifecycle::TestACallRacingTheDropFailsLoudAndTyped::test_every_call_in_flight_at_the_drop_raises_SurrealConnectionError` (now requires the subclass); `test_sdk3_connection_factory::TestAReadWhoseOutcomeIsUnknownIsRaisedAsUnknown::{test_a_read_only_transaction_in_flight_at_a_drop, test_a_read_whose_reply_outlives_its_timeout}`; `::TestACallDuringAnOutageFailsWithinItsBound` (queued-on-reconnect → unknown) | verb sniff on the single-statement seam; verb sniff on the transaction seam | f14a HELD (3 reds), f14b HELD |
| MP3 / R5 F4b | `test_sdk3_connection_factory::TestEveryNamedLongOperationOutlivesTheDefaultTimeout::{test_every_owners_startup_ddl_survives_a_reply_slower_than_the_default_timeout, test_a_large_index_transaction_survives_a_reply_slower_than_the_default_timeout}` | one owner's `ensure_ready` without its override (round-3 reference: 16 of 17); `SurrealStore.apply` without its override | mp3a HELD, mp3b HELD |
| D1 / MP4 | `test_sdk3_served_outcome::TestTheBatchVerbNeverServesAnUnknownOutcomeAsAborted[resolve_many\|acknowledge_many]`; `::TestEveryCatchSiteThatNamesTheTransportErrorIsAdjudicated` ×2 (derived set) | batch serves unknown as "ABORTED … retry these" (HEAD and round-3 reference); a NEW rendering catch site with no behaviour pin | d1a HELD, d1b HELD |
| RS2 | `test_sdk3_lifecycle::TestRecoveryLatencyAfterALongOutage` (outage 15 → 45 s) | `attempts=20` (the adversary's survivor) | rs2 HELD |
| RS4 / F15 | `test_sdk3_record_ids::TestANonWordKeyServesTheEnginesText` | served keep id from `.table_name + ":" + .id` (the round-3 reference) | rs4 HELD |
| RS6 | `test_sdk3_native_shapes::TestTheGuardsSafeSetHoldsNoWriteCapableDoor` | `SAFE_CONNECTION_METHODS` widened with insert/batch/relate/upsert/select | rs6 HELD |

### R4.1 MP1 — F12: ONE strain bound, rows, for every composer (and the rider: a statement cap anywhere goes RED)

The round-3 reference kept `TXN_STATEMENT_HARD_CAP` live in `compose` and counted an un-annotated fragment's rows as its
statements, so the row cap bound only the indexer. Pins (all offline: `execute_transaction` replaced by a capturing no-op,
production fragment builders wherever rows ≠ statements):
- **No statement cap survives** — 5,001 single-row statements compose (premise: `TXN_ROW_HARD_CAP` > 5,001) and reach the
  transport through `SurrealStore.apply`.
- **Rows are the bound whatever the statement count** — the PRODUCTION batched chunk fragment (`replace_file_fragment`, ≤ 3
  statements) with 20 rows is refused under a shrunk cap of 7, naming 7; 3 rows compose (control). Single-row statements count
  one row each (7 at a shrunk cap of 7 compose; 8 are refused), so no composer escapes the bound. The shrink is of the ONE module
  value (`monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", …)`); a build reading a copied constant fails these pins (stated
  constraint, as B3 already imposes).
- **Not part of the contract:** a fragment's `rows` attribute (the reference's `TxnFragment.rows`) — only the effect is pinned.
- **The three pins the adversary measured are rewritten as row-cap pins** (`test_surreal_apply` TestComposeStatementHardCap →
  `TestComposeRowHardCap`, TestApplyStatementHardCapNeverReachesTheServer → `TestApplyRowHardCapNeverReachesTheServer`;
  `test_ingest_entity_seam::TestOneImplementation` shrinks `TXN_ROW_HARD_CAP`). `test_surreal_apply`'s two guarded import blocks
  no longer import `TXN_STATEMENT_HARD_CAP` / `TXN_STATEMENT_WARN_THRESHOLD`: had they stayed, deleting either name would have sent
  the WHOLE P5-C2 block to its fallback (`compose = None`, the envelope-integrity error class a placeholder) — every compose test
  in the file red for an import reason.
- **The fakes follow** (`_surreal_fakes.FakeSurrealStore` enforces the ROW cap, one row per fake statement; a transitional
  fallback to the statement constant keeps HEAD importable — the builder deletes it with the build). Consequence, DISCLOSED
  DEVIATION: the fake's keyword is renamed `txn_statement_hard_cap` → `txn_row_hard_cap`, so `test_indexer.py::_trio` and its one
  caller (`TestIndexerFailureIsolation`-area, `_trio(txn_row_hard_cap=6)`) were edited (3 lines) to keep that file importable —
  a regression my in-scope change would otherwise cause (brief-base §2). Its arithmetic is unchanged (1 row per fake statement).
- **Packet 58 (dormant, RED at HEAD on the unbuilt 58 API): stated bound, fork F19.** Only the one MODULE-LEVEL read
  (`test_reanchor_58_r3_convergence.py` `CAP = …`) is changed, to `getattr(_txn, "TXN_STATEMENT_HARD_CAP", None)`, so the file
  still COLLECTS after the builder deletes the constant (a collection error interrupts a whole pytest session). The in-test reads
  in `test_reanchor_58_r2_am2/_r2_probes/_r2_rulings/_r3_probes`, `test_supersede_reanchor_58` stay: each raises
  `AttributeError` (loud, already-RED file) once the constant is gone, and is re-sized by rows at 58's revival. Measured: the 60
  REDs of `test_reanchor_58_r3_convergence.py` on the r4 reference are exactly the round-3 reference's (diffed both ways).

### R4.2 D2 — the size WARN is a row warn

Name fixed: `store._txn.TXN_ROW_WARN_THRESHOLD` (reference value 10,000; the builder re-measures). Pins by EFFECT
(`TestTheSizeWarnFiresOnRows`): a two-statement batched fragment whose rows cross the (shrunk) threshold WARNs — a statement-count
warn is silent on two statements; 801 single-row statements (over the retired 800-statement warn) with the row threshold above
them stay QUIET — a build warning on statements beside rows fires. Read live like the cap. `test_surreal_apply`'s warn pin is
re-keyed to the row threshold.

### R4.3 MP2 — F14 holds for ALL requests

- **L3 strengthened**: the 8 in-flight `RETURN sleep(3s)` READS at a drop must each be `SurrealOutcomeUnknownError`.
- **Siblings, decided and pinned:** a read-only transaction in flight at a drop (`BEGIN; LET $wait = sleep(3s); SELECT …;
  COMMIT;` ×8) → unknown; a read whose reply outlives `with db.timeout(1)` → unknown; a request queued during a reconnect that
  times out UNSENT (CF1, store stays down) → unknown — R8 F14's grounds name "nor sent from queued" explicitly, so CF1 is
  strengthened rather than forked.
- **Scout / the inbox awaiter: NOT pinned — fork F20.** F13 keeps their raw SDK errors (W1-SCOUTKILL); whether F14's
  "every TransportError on a request" reaches them is unruled.
- Cost: L3 ~6 s; read-txn ~5 s; read timeout ~1 s.

### R4.4 MP3 — EVERY named long operation runs under its override

- **∀ startup DDL**: the owner set is DERIVED — `test_sdk3_lifecycle._owner_classes()` (AST, `test_retry_seam`
  `_discover_bootstrap_owners`) filtered at runtime to classes with a callable `ensure_ready`: 17 at the r4 reference. ONE test,
  each owner on its own database and its own proxy, CONCURRENTLY; per owner: warm call, arm a hold of default + 2 s, `ensure_ready`.
  Checked variable: the proxy counts client-to-store bytes, so each owner is classified `held` (sent traffic, the hold was
  OBSERVED on it, it survived), `connect-only` (sent NOTHING after the warm call — measured: `DiffEngine`, `SnapshotStamper`, whose
  `ensure_ready` only connects), or failed (sent traffic but the hold was not observed, or it raised). A floor (≥ 12 `held`,
  measured 15) guards the instrument; a new owner joins at collection. Kills the round-3 reference (16 of 17 owners had no
  override) and mutation mp3a (one owner's decorator removed).
- **The large index transaction**: a B1-sized file (`test_sdk3_index_batching._big_module_source(600)`) indexed through the
  served indexer of an `AppContext` whose store URL is the proxy; the reply to the first request ≥ 256 KiB is held default + 2 s;
  the file must end `indexed`. **Instrument fix found while building it:** a whole-stream hold starves the SDK keepalive pong
  (`ping_interval=30`, `ping_timeout=10`) and the SDK closes the socket ~10 s after its next ping — measured: the first version
  ended "WebSocket connection closed before a response was received". `StoreBounceProxy.hold_reply_to_large_request` is
  therefore FRAME-AWARE (data frames held, control frames forwarded). The older time-based `hold_next_response` is unchanged; it is
  safe for CF2/MP3a only because those holds start within ~1 s of a FRESH connection's open (first ping at +30 s, pong due by
  +40 s, hold ends at +32 s) — a stated bound on that instrument.
- **`REBUILD INDEX`**: no site exists (`rebuild_embeddings` is the REMOVE/DEFINE dance, drop row C#26) — stated bound.
- **Cost, stated:** ~40 s wall each (two tests, parallel under `-n`); measured 74 s for the whole override class (4 tests,
  incl. CF2/CF2c) on the r4 reference.

### R4.5 D1 / MP4 — an unknown outcome is never served as a definite failure

- **Behaviour pin** on `AppContext._resolve_or_acknowledge_many` (the renderer behind `lore_findings action=resolve_many` /
  `acknowledge_many`), both verbs: item 2 of 3 raises `SurrealOutcomeUnknownError`; its served line must name the outcome as
  unknown and say "verify" — never "aborted", never "retry these". Called directly: the tool-level path needs
  `_finding_fakes.arm_finding_identity` (does not exist at HEAD — a dormant 64b-i helper) and `test_mcp_server.
  _LedgerRaisingOnSecondCall` forwards a `subject=` keyword `FakeFindingLedger` rejects (measured TypeError), so the test carries
  its own 20-line double. The existing plain-`SurrealConnectionError` → ABORTED pin (`test_mcp_server::…test_connection_loss_
  aborts_remaining_as_render_not_raise`) is untouched (nothing was sent: ABORTED is true there).
- **Reach pin, DERIVED**: every production catch site found by THE ONE walker (`_catch_sites.production_catch_sites`, packet 58's
  approved instrument — reused, not a new scanner; flagged for the operator anyway) whose caught classes NAME
  `SurrealConnectionError` or a subclass and that `SurrealOutcomeUnknownError` reaches unshielded: a bare re-raise is derived
  (serves nothing); anything else must be adjudicated to its behaviour pin, both ways. At the r4 reference: 6 sites — 5 bare
  re-raises (`findings.annotate`, `findings._transition`, `tasks.transition`, `tasks.supersede_task`,
  `floor_calibration.record_measurement`) and 1 renderer (`server._resolve_or_acknowledge_many`). Instrument (census) in
  Appendix E.
- **BOUND — fork F18:** 53 more sites reach an unknown outcome only through a BROAD catch (25 `Exception`, 10 `BaseException`, 14
  `SurrealStoreError`-family, 4 others). Found by inspection among the 14: `briefs.BriefLedger.publish` catches
  `SurrealStoreError` after a failed apply and RELEASES the minted version ("nothing committed") — an outcome-unknown publish may
  have committed, so the version number can be re-minted.

### R4.6 RS2, RS4, RS6

- **RS2** — L6's outage is 45 s. SDK delay schedule (read: `connections/reconnect.py::ReconnectOptions.delay`): attempt 1 ~1.0 s,
  later attempts 1.8–2.0 s (capped, 10 % jitter) ⇒ `attempts=20` gives up after 35.2–39.1 s. Kills budgets ≤ 22 attempts.
  BOUND: a budget ≥ ~25 attempts survives; "forever" is unpinnable by a finite outage. Cost +30 s (L6 ~50 s).
- **RS4** — a keep row with a NON-WORD key (`keep:⟨sdk3-non-word.key⟩`, constructed: lore's own mint cannot produce one) is
  served as the engine's `<string> id` and found again by it. The two R7 (d) forms differ exactly here (F15). Premise asserted:
  the engine brackets the key. The r4 reference serves `Keep.id` from a projected `<string> id AS id_text`.
- **RS6** — `_sdk_guard.SAFE_CONNECTION_METHODS` ∩ (derived write-capable doors) = ∅ on every guarded SDK class. Write-capable =
  a door (F5 `_is_door`) that returns a builder/batch, or a coroutine with a parameter able to carry text, a record id or a table
  (`str` / `RecordID` / `StringRecordId` / `Table` at the top level of its annotation; unannotated, `*args`, `**kwargs` or an
  unresolvable hint fail CLOSED). Control: `query` is write-capable on every class. GREEN at HEAD (HEAD's list is correct); its
  RED is shown by mutation rs6. Bound: it would also refuse exempting `authenticate(token: str)` — the safe direction for a
  deny-by-default list.

### R4.7 D3 — pre-existing pins that encode retired rulings (every row individually)

**Statement-cap / warn family** (this author; adversary rows from `scratchpad/adv/p8_verdicts.tsv`, F12/WARN rows):

| file:line (adversary) | node | verdict | old → new ruling | r4 ref | HEAD |
|---|---|---|---|---|---|
| _surreal_fakes.py:297 | `FakeSurrealStore.__init__` | REWRITTEN | statement cap → row cap (R8 F12) | used by test_indexer: GREEN | GREEN |
| _surreal_fakes.py:1770 | `fake_surreal_trio` | REWRITTEN | same | GREEN | GREEN |
| test_ingest_entity_seam.py:608 | `TestOneImplementation::test_entity_write_reddens_with_the_shared_compose_cap` | REWRITTEN | shrink statement cap → shrink row cap | GREEN | RED own |
| test_surreal_apply.py:158 | P5-C2 fallback `TXN_STATEMENT_WARN_THRESHOLD = 800` | REWRITTEN (removed) | statement warn → row warn (R9 D2) | collects | collects |
| test_surreal_apply.py:191 | P5-C3a fallback `TXN_STATEMENT_HARD_CAP = 5000` | REWRITTEN (removed) | statement cap → row cap | collects | collects |
| test_surreal_apply.py:1438, :1449 | `TestApplyTxnSizeTelemetry::test_apply_warns_above_statement_threshold` → `…_above_the_row_threshold` | REWRITTEN | R9 D2 | GREEN | RED own |
| test_surreal_apply.py:1510, :1520 | `TestComposeStatementHardCap::test_compose_raises_…` → `TestComposeRowHardCap::…` | REWRITTEN | R8 F12 | GREEN | RED own |
| test_surreal_apply.py:1525, :1529 | `…test_compose_accepts_exactly_at_the_hard_cap` | REWRITTEN (the adversary's "TRAP" was right in ruling, wrong in effect: at 5,000 statements it stayed GREEN under F12) | same | GREEN | RED own |
| test_surreal_apply.py:1538, :1539 | `…test_compose_still_succeeds_above_warn_threshold_but_below_hard_cap` | REWRITTEN (same note) | same + D2 | GREEN | RED own |
| test_surreal_apply.py:1589 | `TestApplyStatementHardCap…` → `TestApplyRowHardCapNeverReachesTheServer::…` | REWRITTEN | R8 F12 | GREEN | RED own |
| test_reanchor_58_r3_convergence.py:136 | module `CAP` | REWRITTEN (collection-safe read only) | F12; 58 re-size owed (F19) | 60 RED = round-3 ref's 60 | RED (dormant) |
| test_reanchor_58_r2_am2.py:74, :81 | `test_PR18r2_cap_plus_one_of_ONE_blocker_heals_in_the_PACKERS_predicted_chunks` | DORMANT-BOUND (F19) | stays on the statement name; AttributeError after the build | RED (dormant) | RED (dormant) |
| test_reanchor_58_r2_probes.py:125 | `max_reanchor_dependents` formula test | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_reanchor_58_r2_probes.py:342 | `test_PR14_the_accessor_follows_the_shared_hard_cap` | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_reanchor_58_r2_rulings.py:154 | `…test_at_K_the_accessor_is_the_composed_cap_cap_succeeds_and_cap_plus_1_teaches` | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_reanchor_58_r2_rulings.py:204 | `…test_cap_plus_1_stragglers_over_SIX_blockers_all_heal_in_ONE_boot_every_chunk_within_the_cap` | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_reanchor_58_r2_rulings.py:236 | `…test_MUTATION_padding_the_shell_moves_the_packer_AND_the_accessor` | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_reanchor_58_r2_rulings.py:357 | `…test_a_chunk_DOMAIN_rejection_is_isolated_WARNED_and_healed_next_boot` | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_reanchor_58_r3_probes.py:177 | `test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot` | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_supersede_reanchor_58.py:591, :617 | `TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_…` (+ mutation test) | DORMANT-BOUND (F19) | same | RED (dormant) | RED (dormant) |
| test_supersede_reanchor_58.py:676, :677, :697 (UNSURE) | `…test_crossing_the_WARN_threshold_logs_ONE_warning_…` | DORMANT-BOUND (F19 + D2: re-key to the row warn at revival) | same | RED (dormant) | RED (dormant) |
| (not in the adversary's list) test_indexer.py:255–271, :694 | `_trio` kwarg | REWRITTEN (deviation, §R4.1) | fake kwarg rename | GREEN | GREEN |

The packet-58 rows were RED before this round on the unbuilt 58 API (adversary run #8/#9: the 160 base reds) — not run
individually here beyond the convergence file; their verdict is the stated bound F19.

**KeyError / literal / `str(RecordID)`-oracle family** — `contract-sdk3-r4-d3`'s table, checked by me against its logs
(`scratchpad/sdk3r4/d3/`; REF = r4-d3 copy of the round-3 reference, SDK 3.0.0; HEAD = main venv, SDK 2.0.0; "own" = fails on
its own assertion, 0 import/collection errors):

| file:line | node | verdict | old → new ruling | REF | HEAD |
|---|---|---|---|---|---|
| _exhaustion_fates.py:173 | registry row, scout run #1 (`TestTheRegistryIsTheAdjudicationBothWays::test_every_row_is_matched_to_ITS_site_by_the_caught_expression`) | KEPT-builder-dependent | the row names `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION`; a builder rename/inline edits the registry | PASS | PASS |
| _exhaustion_fates.py:174 | scout run #2 | KEPT-builder-dependent | same | PASS | PASS |
| _exhaustion_fates.py:179 | scout `_consume_live` | KEPT-builder-dependent | same | PASS | PASS |
| _exhaustion_fates.py:182 | scout `_safe_kill` | KEPT-builder-dependent | same | PASS | PASS |
| _exhaustion_fates.py:187 | inbox_awaiter `await_inbox` | KEPT-builder-dependent | same | PASS | PASS |
| _exhaustion_fates.py:190 | inbox_awaiter `_establish_live` | KEPT-builder-dependent | same | PASS | PASS |
| _exhaustion_fates.py:193 | inbox_awaiter `_consume_live` | KEPT-builder-dependent | same | PASS | PASS |
| _exhaustion_fates.py:196 | inbox_awaiter `_safe_kill` | KEPT-builder-dependent | same | PASS | PASS |
| test_comms_await.py:218 | `TestTheSharedSdkAwaitBoundaryConstant::…` → `::test_the_boundary_catches_the_sdk_transport_error_and_not_a_keyerror` | REWRITTEN | constant ∋ KeyError → an except naming the boundary catches the SDK transport error and lets a KeyError through (run, not read) | PASS | RED own |
| test_comms_await.py:222 | same node | REWRITTEN | exact-set equality dropped (F10 lets the builder re-spell) | PASS | RED own |
| test_comms_await.py:454 | `_FakeLiveConnection` dead path → `TestSocketDropNonLoss` ×2 | REWRITTEN | raises KeyError → raises `ConnectionUnavailableError` | PASS 2/2 | PASS 2/2 |
| test_comms_await.py:461 | `_FakeLiveConnection.subscribe_live` | REWRITTEN | same | PASS | PASS |
| test_comms_await.py:562 | `…dropping_keyerror…` → `::test_dropping_the_transport_error_from_the_shared_constant_breaks_await_recovery` | REWRITTEN | mutation drops the members that catch the SDK transport error (derived from the live value) | PASS | PASS |
| test_comms_await.py:563 | same | REWRITTEN | same helper | PASS | PASS |
| test_findings_adversary_pins_64b.py:153 | `test_MP5_a_revoked_household_member_is_refused_on_its_next_write` | KEPT | partitions served keep text, not `str(RecordID)` | RED (64b unbuilt) | RED (same) |
| test_findings_classes_64b.py:582 | `TestEveryAuthorizationInputIsReadPerCall` ×4 | KEPT | same | RED ×4 (unbuilt) | RED ×4 (same) |
| test_governed_substrate_64b.py:185 | `substrate_world` fixture | KEPT | partitions literal constants | file reds = 64b unbuilt + C4 | unbuilt only |
| test_graph_surreal.py:2878 | `TestQuerySeamSdkKeyErrorClassification` → `TestQuerySeamSdkTransportErrorClassification::{test_an_sdk_transport_error_surfaces_as_outcome_unknown_and_heals, test_a_keyerror_propagates_as_a_bug_not_as_transport}` | REWRITTEN | KeyError → SurrealConnectionError + heal ⇒ transport error → unknown + drop + exactly one new connection; KeyError propagates | PASS 2/2 | RED 2/2 own |
| test_memory_ownerfold_63a_iv.py:63 | `_bare_s` | REWRITTEN | `str(RecordID)` partition → `.table_name` / `.id` (R7 d); measured 53/200 engine ids digit-led → `principal:⟨9kl…⟩` on SDK 3.0.0 (latent flake) | PASS | PASS |
| test_memory_reinforce_63a_iv.py:47 | `_bare_s` | REWRITTEN | same | PASS | PASS |
| test_memory_supersede_atomicity_63b_ib.py:772 | `TestTransportAndContentionKeepTheSupersedeLedgerRow::test_a_transport_failure_on_the_composed_supersede_keeps_the_ledger_row` | REWRITTEN | injected KeyError → SDK transport error, surfaces as unknown (F14) | PASS | RED own |
| test_memory_supersede_atomicity_63b_ib.py:877 | `TestCompensationIsDomainScopedAcrossShapesAndCauses[*transport*]` | REWRITTEN | injected KeyError → SDK transport error | PASS 4/4 | PASS 4/4 |
| test_preboot_schema_precondition_63c_13d.py:353 | `world` fixture | KEPT | `operator.id` is served engine text (probe: unbracketed for its key) | PASS | PASS |
| test_retry_seam.py:312 | `_mutate_shared_marker` consumers | REWRITTEN | setattr `_RETRYABLE_CONFLICT_KIND` → `move_the_sdk_conflict_predicate` (rebinds `QueryError.is_transaction_conflict`, drop #2) | 3 PASS; `test_the_new_marker…` ×16 RED (C1), bootstrap ×32 RED (C2); all 71 PASS with SDK-3-shaped fakes | RED own |
| test_retry_seam.py:316 | same | REWRITTEN | same | same | same |
| test_retry_seam.py:385 | param `sdk-KeyError-routing-drop` → `sdk-transport-inflight-drop` + new `::test_a_keyerror_propagates_as_a_bug_not_as_transport` | REWRITTEN | KeyError = transport ⇒ transport error = unknown, zero retries, drop; KeyError propagates, one call | PASS | RED 16 own (×2) |
| test_retry_seam.py:3000 | `TestScoutCommandClaimRidesTheSeam::test_a_transport_fault_still_reaches_the_reconnect_ladder[…]` | REWRITTEN | KeyError param → transport error | PASS 3/3 | PASS 3/3 |
| test_retry_seam.py:3031 | same node | REWRITTEN | `raises((*_CONNECTION_ERRORS, KeyError))` → `raises(_CONNECTION_ERRORS)` | PASS | PASS |
| test_retry_seam.py:3035 | same node | REWRITTEN | isinstance without KeyError | PASS | PASS |
| test_scout.py:1157 | `…recovers_from_a_keyerror_inflight_drop` → `::test_reconnect_recovers_from_an_sdk_transport_inflight_drop` | REWRITTEN | KeyError drop → transport error drop | RED (C1 fake shape; its unedited sibling is RED for the same reason); PASS with SDK-3 fakes | PASS |
| test_scout.py:1199 | `…dropping_keyerror…` → `::test_dropping_the_transport_error_from_the_shared_constant_breaks_recovery` | REWRITTEN | shared mutation helper | PASS but VACUOUS on REF until C1 (its control is red) | PASS |
| test_scout.py:1200 | same | REWRITTEN | same | same | PASS |
| test_scout.py:1206 | same | REWRITTEN | drop error = transport error | same | PASS |
| test_surreal_harness.py:1483 | `TestTheHarnessRetryPolicyIsTheSeamsPolicy::test_detection_follows_the_seams_one_conflict_kind` | REWRITTEN | literal setattr → predicate mutation | PASS | RED own |
| test_surreal_harness.py:1516 | `::test_the_bootstrap_paths_detection_follows_the_seams_kind` | REWRITTEN | same | PASS | RED own |
| test_surreal_harness.py:1565 | `::test_run_detection_follows_the_seams_one_conflict_kind` | REWRITTEN | same | PASS | RED own |
| test_surreal_manifest.py:1231 | → `TestQuerySeamSdkTransportErrorClassification` ×2 | REWRITTEN | as graph | PASS 2/2 | RED 2/2 own |
| test_surreal_store.py:2347 | → `TestQuerySeamSdkTransportErrorClassification` ×2 (a READ) | REWRITTEN | as graph | PASS 2/2 | RED 2/2 own |
| test_surreal_store.py:2375 | `TestTxnSdkKeyErrorClassification` → `TestTxnSdkTransportErrorClassification` ×2 | REWRITTEN | fake `query_raw` KeyError → transport error ⇒ unknown + dropped once; KeyError propagates | PASS 2/2 | RED 2/2 own |
| (drop #13) test_retry_seam.py imports | the round-3 reference's 2-line `AsyncEmbeddedSurrealConnection` deletion, ported | PORTED | — | collects | collects |

d3 mutation proofs (its `scripts/mutation_proof.py` runs, declared sets from `--collect-only`): M1 literal restored in
`_is_retryable_conflict_kind` 69/69; M2 a KeyError→transport arm re-added in `run_query` 19/19; M3 F14 branch disabled 21/21;
M4 the boundary re-gains KeyError 1/1 — each EXIT 0, tree restored.

**Contradictions outside the writable set** (helpers in the TRAP files that are NOT the named pins, plus other files — each with
its edit, for the lead/operator; none edited): **C1** SDK-2-shaped fake answers — `test_retry_seam._ScriptedConnection.rows`
default `[{"next": 4}]` → `[[{"next": 4}]]`; `test_scout._FakeCommandConnection.query` → `[uuid]` / `[rows]` / `[[]]`;
`test_comms_await._FakeLiveConnection.query` → `[live_uuid]` / `[[]]` (exact edits in `scratchpad/sdk3r4/d3/probe/
sdk3_shape_fakes.py`; must be SDK-version-aware or they redden HEAD — fork F-a). **C2** helpers patch the per-module
`AsyncSurreal` name R5 removes: `test_retry_seam._point_at` (32 REF reds in `TestTheBootstrapClassifiesThroughTheONEAuthority`),
and the `_plain_counting_connection_factory` / `_counting_connection_factory` clones in test_surreal_store / _manifest / _graph
(count at the SDK class instead: d3's `_count_sdk_connections`). **C3** `test_surreal_store.py:137-143` TYPE_CHECKING import of
`_txn._RETRYABLE_CONFLICT_KIND` → mypy attr-defined after the build: delete it. **C4** reference gap, R7 (d): `AuditStore.append`
serves `audit:⟨01M6…⟩` via `str(RecordID)` (ULIDs are always digit-led) — red on REF only:
`test_governed_substrate_64b.py::TestAuditAppendConsumesItsFragment::test_append_builds_its_write_from_append_fragment` (builder).
**C5** `test_exhaustion_fates.py::…::test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS` red on REF only
("store/lease.py get/create/release: FATE CHANGED ['logs-error-class']" — the reference's lease edit; builder). **C6** SDK 3.0.0
`RecordID.parse("t:⟨3abc⟩").id == "⟨3abc⟩"` (parse does not unescape) and the engine renders a HYPHENATED key with BACKTICKS
(``principal:`abc-def` ``), which `record_text` does not — consistent with F15/RS4 (engine form for persisted text). **C7** prose
and vacuous scanners still naming retired arms: test_comms_await.py:16, :47, :741-743, :772-796 (an AST reach check keyed on
`KeyError` in inline tuples — now finds nothing; fork F-d), test_scout.py:892-893, test_memory_supersede_atomicity_63b_ib.py:723,
test_retry_seam.py:140, :3707 (`_MARKER_NAME="_RETRYABLE_CONFLICT_KIND"`: name half vacuous), :6577, :6726, :7943, :8533,
test_surreal_harness.py:136, scripts/probe_store_recovery_07a.py:9, :33-35. **C8** `_bare_s` exists twice (ownerfold,
reinforce), now identically fixed — pre-existing duplicate. **C9** (§R4.10) `test_fixwave_a28_63c_i_a::TestTheMeasuredCountsAreTypedFields63cIAa28`
is nondeterministically RED on both references (`owner_classification 'foreign'`) — builder, R7 (d). d3 forks: **F-a** (C1 version-aware fakes, recommended), **F-b**
(pin that a server-answered `NotAllowedError` is NOT outcome-unknown? unruled, not pinned), **F-c** (KeyError dual also pins the
connection is kept? not pinned), **F-d** (retire or re-key C7's AST reach check).

### R4.8 Drop list rows #32–#36 and removed-behaviour inventory X18–X23 (adjudication; R1 columns where they apply)

| # | what | where | native replacement | evidence | fate |
|---|---|---|---|---|---|
| 32 | `SurrealStore.upsert` — per-record `UPSERT` path outside R4 batching and the row cap (RS7) | `store/surreal.py::SurrealStore.upsert` | `apply([replace_file_fragment(...)])` | grep: ZERO production callers (the one `.upsert(` in production is `SurrealManifest.upsert`, indexer.py); 90 call sites in 7 test files (fixture seeding) | **spec-silent → builder/lead**: recommend route it through `compose` (so the row cap binds) or reduce it to a test helper; not pinned |
| 33 | 13 SDK constructions in `scripts/` that bypass the factory (RS8) | probe_dnd_defense_objects.py:621, probe_store_recovery_07a.py:133, probe_store_error_classes_07.py:47, probe_unique_nullable_48.py:259, probe_query_complexity_07.py:59, probe_governed_63c.py:763 + :778, probe_supersede_throw_rollback.py:109, probe_drain_read_63b_ii_b.py:820, probe_read_filter_61b.py:619, probe_read_filter_63.py:808, survey_txn_contention_102.py:79, probe_member_of_cascade.py:369 | `_txn.open_surreal_connection` | grep (lore down; `scripts/` is #507's seam anyway) | **builder port list**; stated bound: no pin reaches `scripts/` (the L1/L6 owner set is package-only); each is a probe/survey, so a stale script mis-measures rather than serves |
| 34 | `tasks._to_aware_utc_ceiling` +1 µs ceiling (RS11a; SDK-2.0 ns→µs truncation of `time::now()`) | `tasks.py` (`Task.updated_at`) | `PreciseDatetime` round-trips ns (R6 F3; R6b) | origin sdk-bug; defect = its own docstring (PKT-06 §1); re-probed: R6b ("ns kept", bind-back) GREEN on SDK 3.0 (round 2/3) | **C → R**: retire iff the `updated_since` exclusive-boundary behaviour tests stay green with the ceiling deleted; R1 rider (a pin failing if still needed + a mutation re-adding the truncation) is the BUILDER's to show — not run here |
| 35 | `floor_calibration._bare_record_id` (RS11b) | `floor_calibration/store.py` | — | uses `value.id` (native, not `str(RecordID)`); its NONE guard rests on `record::id(NONE)` raising, probed 3.2.1 only | **K (design)**; the 3.2.1 engine claim is un-re-probed on 3.3.5 — owed per R1 (cheap: one probe) |
| 36 | `_txn_conflict_backoff_seconds` private `uniform` draw + `retry_on_conflict` loop (R11) | `_txn` | tenacity `AsyncRetrying` + `wait_random_exponential` (via `loresigil.backoff`) | R11 (operator) | **R** per R11 — but see fork F22 (R11's own riders contradict on `test_retry_seam`'s jitter recorder) |

| X | deleted thing → behaviour it carried | adjudication |
|---|---|---|
| X18 | the 18 self-heals → `KeepStore.close` / `PrincipalKeyStore.close` also close their NESTED `PrincipalStore` (keeps.py, principal_keys.py) | preserved (the `close()` bodies are not part of the self-heal the factory replaces); unpinned — a builder deleting per-owner lifecycle code must keep them; cold-audit read item |
| X19 | `LocalMemoryBackend._rebuild_lock` (serialises `rebuild_embeddings` vs writes) | preserved, untouched by the factory; out of the reconnect path |
| X20 | statement cap → a pathological file of many single-row statements refused at 5,001 statements | dropped deliberately (R8 F12); the same file is now refused at the row cap (pinned, §R4.1) |
| X21 | `retry_on_conflict` → the wall-clock deadline (default 2.0 s, read per call) with an attempt FLOOR of 5 and a CEILING of 64 | preserved under R11 — expressible exactly: `stop_any(stop_after_attempt(64), stop_all(stop_after_delay(deadline), stop_after_attempt(5)))` (§R4.12); pinned by `test_retry_seam`'s deadline/floor pins |
| X22 | `retry_on_conflict` → ONE exhaustion record per terminal disposition (label/url/engine_error of the LAST conflict), nothing logged on a resolved conflict; `_log_rollback` per failed attempt on the transactional path | preserved under R11 (tenacity `retry_error_callback` / a `RetryError` handler); pinned by `test_retry_seam`'s exhaustion-log pins |
| X23 | `retry_on_conflict` → the exhaustion FATE: `TxnContentionExhaustedError` (a `SurrealStoreError`) raised only when the LATEST attempt was a conflict | preserved under R11 (tenacity's `RetryError` must be translated, never leaked); pinned by T1/T2 and `test_retry_seam` |

### R4.9 The round-4 reference build (a satisfiability instrument, not the build)

Delta over the round-3 reference (`scratchpad/sdk3r4/reference_r4_delta_vs_r3.diff`, 19 production files; full build diff
`scratchpad/sdk3r4/reference_build_r4.diff`): `compose` loses the statement cap; `TXN_STATEMENT_HARD_CAP` /
`TXN_STATEMENT_WARN_THRESHOLD` deleted; `TXN_ROW_WARN_THRESHOLD = 10_000`, `SurrealStore.apply` warns on rows (read live);
`_txn.long_operation(seconds)` sets a context variable that `run_query` and `_txn_query_raw` turn into `with
connection.timeout(N)` around the SDK await — ONE place applies every named override (the adversary's recommended chokepoint);
all 17 `ensure_ready` carry `ensure_ready_operation` (300 s) and `SurrealStore.apply` `index_transaction_operation` (300 s);
`server._resolve_or_acknowledge_many` catches `SurrealOutcomeUnknownError` first and serves "OUTCOME UNKNOWN … verify before
retrying"; `KeepStore` projects `<string> id AS id_text` and serves it. NOT done (builder): C4 `AuditStore.append` served id, the
D1 broad sites (F18), the scripts/ port (#33), R11's tenacity port, C1/C2 fixture shapes.

### R4.10 Receipts

Logs: `scratchpad/sdk3r4/logs/`; each opens with `tree_id.sh` and (pytest logs) `loremaster.__file__` + `surrealdb=`.

| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| RED at HEAD (SDK 2.0.0) | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q -rfE -p no:cacheprovider --timeout=400 -n 8 <head_collected.txt: 30 ids>` | `r4_head_red_final.log` (first run `r4_head_red.log`, TREE `1d12a1f0…`, same result, before the lint-only edits) | 1 | **25 failed, 5 passed**; observed FAILED set == the 25 declared (`head_declared_red.txt`, from `--collect-only`, written before the first run), diffed both ways; 0 ImportError / collection errors | `15b69cfb…acc6` (HEAD `ee4d754` + this round's uncommitted tests — the FINAL test tree; only this doc changed after) |
| mutation proofs ×13 | `scratchpad/sdk3r4/run_mutations.sh f12a f12b d2a d2b f14a f14b mp3a mp3b d1a d1b rs2 rs4 rs6` (`scripts/mutation_proof.py`, specs `scratchpad/sdk3r4/mut/<name>.{file,anchor,repl,expect,tests}`) | `r4_mutation_proofs.log` | per proof | **12 PROOF HELD (EXIT 0); f12a PROOF FAILED (EXIT 4)** — see below; every anchor re-verified present exactly once after the run (tree restored) | `70f3ddbf…8ccc` (r4 reference) |
| r4 reference, targeted set (11 contract files + every file this round edited + the grep-derived covering files of the touched symbols — 73 files, `final_set.txt`) | `scratchpad/sdk3r4/run.sh <ref> r4_final_ref.log 400 8 <73 files>` (cgroup-capped, `--timeout=400`, `-n 8`) | `r4_final_ref.log` | 1 | 657 failed, 5269 passed, 7 skipped, 3 xfailed, 2 errors; **all 11 contract files green**; attribution below | `6d7cd120…c8a0` |
| round-3 reference baseline (same set minus the 2 new files, its own HEAD-version tests) | same runner on `scratchpad/adv/base` | `r4_baseline_r3ref.log` | 1 | 708 failed, 5181 passed, 7 skipped, 3 xfailed, 2 errors | `019861de…0925` |
| 58 file after a type-only edit (`cast`) | same runner, `test_reanchor_58_r3_convergence.py` + `test_reanchor_58_r4_state.py` | `r4_58conv_ref.log` | 1 | 63 failed, 18 passed — the dormant 58 reds; collects | `a9108e3e…af43` |
| currency `--legs typecheck,ruff` (no pytest) | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `r4_currency.log` | 1 | typecheck RED_ADJUDICATED (83: packet-58 + packet-64b-i, unchanged from round 3) · ruff GREEN · **no RED_ORPHANED** · pytest NOT_RUN (the `--legs` quirk) | `1c9e97b9…6f7c` (main repo; only this packet doc changed afterwards) |

**Satisfiability — attribution (`scratchpad/sdk3r4/attribute.sh`, both runs' FAILED/ERROR ids diffed per node):** over the 53
files IDENTICAL in both trees, 2 nodes are red on the r4 reference only —
`test_fixwave_a28_63c_i_a.py::TestTheMeasuredCountsAreTypedFields63cIAa28::test_am30_pin1_perturbing_a_field_moves_the_reason`
`[owner_classification-P_mixed]` / `[unscoped_agents-P_agent]` — and NEITHER is attributable: re-run 3× on each tree that class
fails 2/4/3 times on the r4 reference and 4/3/5 on the round-3 reference (`logs/a28_{ref,base}_{1,2,3}.log`), always as
`owner_classification 'foreign' != 'operator'`. A nondeterministic RED present on BOTH references — not "flaky" by verdict: its
shape (a random engine-minted principal id; ~28 % are digit-led, which SDK 3.0.0 brackets in `str(RecordID)`) points at a
remaining `str(RecordID)`-derived comparison in the preboot owner classifier (LOW confidence, inferred, not traced) — a
reference/builder gap under R7 (d), listed as **C9** for the builder. Over the 20 files that DIFFER (rewritten this round), r4
reds ≤ round-3 reds in every file (test_retry_seam 221 vs 256, store 4 vs 6, manifest 1 vs 2, graph 8 vs 9, scout 4 vs 4,
comms_await 4 vs 7, harness 2 vs 5, entity seam 8 vs 8, 58 convergence 60 vs 60); per node, ONE id is red on r4 and absent on
r3 — `test_scout.py::…::test_reconnect_recovers_from_an_sdk_transport_inflight_drop`, the RENAMED form of a pin red on both
(C1 fake shape, §R4.7). The remaining reds are the builder-owned surfaces already listed: §R3.10 (fake shapes C1, `AsyncSurreal`
patching C2, harness), C4/C5, the dormant 58 / 64b / entity-phase-2 packets.

**f12a, stated, not re-run:** declared 6, observed 5 — `test_surreal_apply::TestComposeRowHardCap::test_compose_raises_surreal_
store_error_over_the_hard_cap` stayed GREEN. Cause (read, not guessed): that fixture is OVER the row cap (50,001 rows), and the
reference's row check runs before the body loop, so the row refusal fires first and a restored statement cap is invisible to it.
That pin guards the row refusal, not the statement cap; the declaration was wrong, the pins were not. The four pins that DO
discriminate a restored statement cap (`TestNoStatementCapSurvives` ×2, at-cap, between-warn-and-cap) and the warn pin all fired;
no unexpected red. Re-running with a corrected set would be a set transcribed after the output (`mutation_proof.py`'s own
bound), so it is left as recorded.

Mutation specs (anchor → replacement, each matched exactly once): f12a `compose` re-gains `if len(body) > 5000: raise
SurrealStoreError(...)`; f12b `SurrealStore.apply` re-gains a 5,000-statement raise; d2a warn on `statement_count > 800 or
rows > T`; d2b warn on `statement_count > T`; f14a `run_query` re-raises a non-write-verb statement's `TransportError` as plain
`SurrealConnectionError`; f14b same on `_txn_query_raw`; mp3a `principals.PrincipalStore.ensure_ready` loses its decorator; mp3b
`SurrealStore.apply` loses its decorator; d1a the batch's `except SurrealOutcomeUnknownError` catches nothing; d1b
`findings.annotate`'s transport catch translates instead of re-raising; rs2 `attempts=20`; rs4 keep id from `record_text`; rs6 SAFE
widened with insert/batch/relate/upsert/select.

### R4.11 Forks for the operator

- **F18 — D1's reach.** (a) [pinned] sites that NAME `SurrealConnectionError` (6; 1 renders); (b) also the 53 BROAD catch sites
  an unknown outcome reaches (25 `Exception`, 10 `BaseException`, 14 `SurrealStoreError`-family, 4 others), where one —
  `briefs.BriefLedger.publish` — releases a minted version after a possibly-committed publish. Recommend (b) for the 14
  `SurrealStoreError`-family sites (they decide state, like `publish`), (a) for the catch-alls; the derivation extends by
  changing `_names_the_transport_error`.
- **F19 — packet 58's re-size by rows.** Its pins weigh rows by COMPOSED STATEMENTS; at `TXN_ROW_HARD_CAP = 50,000` a "cap + 1"
  population is ~10× today's fixtures. Owner: packet 58 at revival (F12 already rules "re-size by rows"; the per-row weight and
  the fixture cost are the open part).
- **F20 — F14 over scout / the inbox awaiter.** (a) F14 is the seams' rule; F13's raw-error contract stands for the two
  subscribers; (b) it reaches every request, so scout's claim CAS (`_mark`, a write) in flight at a drop must be treated as
  unknown by its reconnect ladder. Recommend (a) plus a stated bound (a claim lost to a drop is re-polled, and the CAS makes a
  re-claim lose, S4); not pinned.
- **F21 — the size-warn and row-cap constants must be read LIVE** (the pins monkeypatch the module value, as B3 does). Not a
  ruling question unless the operator objects to the constraint.
- **F22 — R11 contradicts itself on `test_retry_seam`.** R11 deletes `_txn_conflict_backoff_seconds`'s private `uniform` draw AND
  requires `test_retry_seam.py` to stay green UNCHANGED — but `test_retry_seam._record_shared_jitter` (9 consumers) asserts the
  function exists and records draws through it, and `test_backoff_seam::…test_the_allowlisted_file_still_contains_what_it_was_
  exempted_for` asserts `"_txn_conflict_backoff_seconds"` and `"random.uniform(0, window)"` in `_txn.py`'s source. Readings:
  (a) the name survives as THE one jitter source, delegating to tenacity's `wait_random_exponential` (no private draw), and only
  `test_backoff_seam`'s source-text clause is re-keyed (its allowlist exemption expires with the draw); (b) the function goes and
  the jitter-recorder pins are retired-ruling surface (D3) to rewrite at tenacity's `wait` seam. Recommend (a): it keeps "UNCHANGED"
  true for 9 pins and leaves one scanner clause to retire with its exemption.
- d3 forks F-a…F-d (§R4.7).

### R4.12 RS9 — does tenacity 9.1.4 do `retry_on_conflict`'s job? (read: installed `tenacity/{stop,wait,retry,__init__}.py`)

Yes, with a thin adapter. **Predicate:** `retry=retry_if_exception_type(RetryableConflictSignal)` keeps the classification where
it lives (`_raise_attempt_failure` → `is_retryable_conflict_error`; `_rollback_verdict` on the transactional path), so it is
sharing, not routing. **Budget:** lore's stop is `attempts >= 64 or (elapsed >= deadline and attempts >= 5)`; tenacity expresses it
exactly as `stop_any(stop_after_attempt(64), stop_all(stop_after_delay(deadline), stop_after_attempt(5)))` (`stop_after_attempt`
compares the 1-based `attempt_number` after the failed attempt — the same count lore increments; `stop_after_delay` reads
`seconds_since_start`), with the per-call `deadline_seconds` built into a per-call `AsyncRetrying`. **Jitter:** lore draws
`uniform(0, min(0.1, 0.005·2^(n-1)))`; `wait_random_exponential(multiplier=0.005, max=0.1)` returns
`random.uniform(0, min(max, multiplier·2^(attempt-1)))` — the identical FULL-jitter law from the same module PRNG
(`wait_exponential_jitter` is equal jitter and would be wrong). **Not native:** the exhaustion disposition (one record with the
last conflict's cause, `TxnContentionExhaustedError` instead of tenacity's `RetryError`) — a `retry_error_callback` or a
`RetryError` handler. Since this was written, R11 (`ee4d754`) ruled the port; the open part is F22.

### R4.13 Brief conflict, routing, DRY ledger, bounds

- **BRIEF CONFLICT (brief-base §2 ROLE BOUNDARY):** the brief asked for each pin to be shown RED "on the adversary's surviving
  wrong build" and to reuse its wrong builds as mutation instruments. Re-running a grader's wrong builds is a forbidden transfer
  (contract author → grader) that no operator grant in the brief covers. Refused that part; each pin's discrimination is shown
  instead by `scripts/mutation_proof.py` mutations this author declared (§R4.10) — the operator-ruled R1/R2/R4/R11 riders demand
  mutation proofs of the author, which is in role. Adversary round 2 replays its own builds.
- **Routing (written before the first sweep, `scratchpad/sdk3r4/ROUTING.md`):** test runs → haiku-runner ×6 (RED@HEAD,
  mutations, final ref, baseline, currency; dev iterations inline on the critical path); the 39-row KeyError/literal/`str(RecordID)`
  family → one Opus helper (contract work stays Opus per the lore roster); every other step me. Fan-out: haiku 6 · sonnet 0 ·
  opus 1 · peak 4.
- **DRY ledger (test-side only):** `_sdk3_proxy.StoreBounceProxy.hold_reply_to_large_request` + `to_store_bytes` (EXTENDS the
  proxy; no slow-store fault elsewhere); `test_sdk3_connection_factory._ddl_owner_classes` (filters the existing derived owner set,
  reuses `test_sdk3_lifecycle._owner_classes/_construct_live_owner/_probe_call/_close_owner`); `test_sdk3_served_outcome.
  _RaisingOnSecondCall` (near-duplicate of `test_mcp_server._LedgerRaisingOnSecondCall`, which cannot drive the renderer today —
  the shared one should drop its `subject=` forward and this one be deleted); `_sites_an_unknown_outcome_reaches` (a consumer of
  THE ONE walker `_catch_sites`); `test_sdk3_native_shapes._is_write_capable_door` (builds on `_is_door`; the open round-3 item
  "move `_is_door` into `_sdk_guard`" now carries this predicate with it); `test_sdk3_row_bound._offline_store` /
  `_single_row_statements` (near-duplicates of `test_surreal_apply`'s `_offline_store` / `_synthetic_fragment` — kept apart
  because that file's imports are RED-guarded; candidates to merge into one helper module); `test_surreal_apply._txn_bound`. d3's
  helpers: `move_the_sdk_conflict_predicate` (test_retry_seam), `drop_the_sdk_transport_error_from_the_shared_boundary`
  (test_comms_await), `_count_sdk_connections` / `_outcome_unknown_type` / `_SDK_INFLIGHT_DROP_TEXT` (test_surreal_store).
- **Packages considered:** reconnect/timeout/streaming — SDK `ReconnectOptions` / `timeout()` (`connections/timeouts.py`: a
  ContextVar keyed per connection; read) → replace; retry/backoff — tenacity 9.1.4 (read, §R4.12) → replace_with_adapter (R11);
  catch-site derivation — the repo's own `_catch_sites` walker → reuse; WebSocket frame parsing in the proxy — `websockets` has a
  frame parser but it is bound to a protocol state machine and masks/unmasks per role; a 15-line length-header read for unmasked
  server frames was simpler and is stated (bespoke, test-side).

## ROUND 3 — rulings R2–R7 implemented as pins (contract-sdk3-r3, 2026-11-07, graded tree HEAD `b03c4fc`)

Round 3 supersedes the round-1/2 forks F1–F10 (ruled: `docs/plans/v2/sdk3-rulings.md` R2–R7; R7 replaces R6's
F7/F8/F9 bullets). Everything below §R3.0 is dated 2026-11-07 and measured at HEAD `b03c4fc` (SDK 2.0.0) and on a
REFERENCE BUILD (SDK 3.0.0) in a `scripts/scratch_copy.sh` copy. lore MCP was DOWN for this round
(`lore_lore` ECONNREFUSED at spawn): every structure question was answered by grep/Read (no friction filed — no
lore tools in the session).

### R3.0 Summary

- **Contract:** 9 files / **70 pins** (`loremaster/tests/test_sdk3_*.py` + `_sdk3_proxy.py`). Five NEW files —
  `test_sdk3_single_statement_seam.py` (R2), `test_sdk3_index_batching.py` (R3/R4), `test_sdk3_connection_factory.py`
  (R5/R7), `test_sdk3_record_ids.py` (R7 F8/F7; absorbs round-1/2 R7–R9), `test_sdk3_native_shapes.py` (R7 F9, R6 F5).
  Edited: lifecycle (L6 now ∀ owners, 3.0 s from the store's return), txn classification (+T6, the `db.batch()` text
  selector discriminator), retirement (RP3 now drives the transaction path through `_rollback_verdict`, R7 W6),
  result shapes (R7–R9 moved out), proxy (+`hold_next_response`, a slow store without a slow statement).
- **RED at HEAD, for the intended reason: 33 declared, from `--collect-only` before the run** (§R3.9). The 37
  GREEN-at-HEAD pins are preservation pins (behaviour SDK 3.0 breaks unless the build keeps it — measured RED on SDK
  3.0 in rounds 1/2 or by mutation here) or engine facts (F9).
- **Satisfiability: the reference build passes the whole set — 94 passed, 0 failed** (70 contract pins + the two
  engine/SDK KNOWN-BOUND classes + `test_graph_surreal::TestNamesWithValuePrefixRangeRewrite`), `loremaster.__file__`
  inside the scratch copy, SDK 3.0.0 (§R3.9). The reference build is a SATISFIABILITY instrument, not the build:
  `scratchpad/sdk3r3/reference_build.diff` (32 files) — it is correct where the pins look and deliberately partial
  elsewhere (§R3.9 "what the reference did NOT do").
- **Operator-ruled mutation proofs** (R2 sharing, R4 bound pin, F9, W6) via `scripts/mutation_proof.py` with declared
  reds: §R3.9.
- **Forks for the operator: F11–F17** (§R3.8). None blocks the adversary; each pin that depends on one says so.
- **DROP LIST** §R3.5 (31 rows) — the lead presents it before anything is deleted. **F8 query for the lead** §R3.7.

### R3.1 R2 — ONE single-statement seam that SELECTS (pins and where they live)

| id | pin | proves | HEAD | ref |
|---|---|---|---|---|
| S1 | `single_statement_seam::…test_a_two_statement_call_raises[two_scalars\|two_lists]` | two statements → `SurrealStoreError`, never transport (would drop + invite retry), never domain (engine refused nothing) | R | G |
| S2 | `…test_a_two_statement_write_is_refused_before_either_statement_runs` | refused BEFORE the wire: no row lands | R | G |
| S3 | `…test_the_connection_is_kept_after_the_refusal` | the next call answers its own scalar | R | G |
| S4 | `…TestScoutsCommandClaimHasExactlyOneWinner` | 8 subscribers race `CommandSubscriber._mark` on one pending command: exactly 7 log a lost claim | G | G |
| R1–R4, R6, R6b, R10 (+R10c) | `result_shapes` (unchanged) | rows, scalar, lost CAS `== []` and falsy, 1 of 8 racers wins, LIVE wake < 4 s | G (R6b R) | G |

Why S2 forces "refuse before sending" (an inference from two standing rules, not a choice between readings of R2): R2
says the seam raises on ≠ 1 result; the autouse runtime guard (`tests/_sdk_guard.py`, the #144 posture) already
fails any test in which a multi-statement `.query()` reaches the wire, judged by the shared
`_txn._assert_envelope_integrity` split. A seam that sent the text and refused the SDK's two-entry answer would have
run both statements (measured at HEAD: the guard ERRORs all four S-pins at teardown). The reference build calls that
same shared split before acquiring a connection, AND checks the SDK's answer length after (a comment-only text, or a
future SDK shape, still raises).
**Sharing proof (rider), mutation M-R2:** make the shared selection return the SDK's list → declared reds: R1, R2, R3,
R4, R6, R6b, R10, S2, S3, S4 (seam + scout + awaiter redden together); S1 stays green (refused before the selection).

### R3.2 R3/R4 — batched rows, one transaction, a row bound, a refused file NAMED

**Measured first (rider 2), OFFLINE** — the production pure builders composed with no socket (instrument
`probe_r3_compose_breakdown.py`, Appendix D): `loremaster/tests/test_comms_tool.py` composes to **5,113 statements**
(exactly production's figure) = chunk 511 UPSERT + 1 DELETE; file_text 1; manifest 2; graph: refers 1,858 RELATE, name
1,204 UPSERT, answers_to 1,022 RELATE, code_node 511 CREATE, 3 DELETE. **Rows written: 5,108.** Param bytes (Python
repr, a proxy): chunk 3.42 MB (the 1024-float vectors), graph 1.36 MB, file_text 0.43 MB — the vectors are ~80 %.
The synthetic fixture (600 functions × 4 calls) composes to 6,612 statements / ~6,600 rows.
**Bound chosen: ROWS**, `store._txn.TXN_ROW_HARD_CAP` (reference value 50,000 ≈ 10× the largest real file measured).
Why rows, not bytes: bytes per row are already bounded by existing caps (a chunk's tokens and the fixed vector width;
`FILE_TEXT_MAX_BYTES` for the body), and the 128 MiB WebSocket message ceiling (scout-40) sits ~25× above
test_comms_tool.py's whole payload; what scales without bound is the ROW count (graph edges per file), and every row
is index maintenance (HNSW per chunk, graph indexes per edge). The value is the builder's to re-measure against the
largest file of every indexed tier.

| id | pin | rider | HEAD | ref |
|---|---|---|---|---|
| B1 | `index_batching::TestALargeFileIndexesAndIsSearchable` | 4a: a file over the retired 5,000-statement cap (premise: rows > 5,000) lands `indexed` and the served `search` finds it | R | G |
| B2 | `…TestTheStatementCountDoesNotGrowWithRows` | **the bound pin** (4b): one request with `BEGIN` per file, and 10× the rows add ≤ 1 statement per 100 rows | R | G |
| B3 | `…TestARefusedFileIsNamedOnTheServedStatus` | 3: shrink `_txn.TXN_ROW_HARD_CAP` to 1009 → the served `lore_index` status JSON names the file AND `1009` | R | G |
| B4 | `…TestNoBatchedEdgeDangles` | 1 / store-ref §4 (#105): every `refers`/`answers_to` edge of the large file joins two existing records (`record::exists`) | R | G |

Mutation M-R4 (rider 4b): restore per-row chunk statements → declared red: B2 only (B1/B3/B4 stay green — they guard
other properties). Rider 1 (bulk-INSERT semantics against `surrealql-tests`, then a probe): the reference build's
`INSERT INTO`, `INSERT … ON DUPLICATE KEY UPDATE value = $input.value` and `INSERT RELATION INTO` were exercised live by
B1–B4 on 3.3.5; scout-40 measured 3,000 rows + 2,999 edges, dangling edges accepted, one bad row → nothing written. The
corpus read is NOT done here (lore MCP down): the builder does it (fork-free; it is the rider's first half).

### R3.3 R5 as amended by R7 — the shared factory, finite timeouts, outcome unknown

Names this contract FIXES (read with `getattr`, so a build lacking one fails that pin, not the module):
`store._txn.SURREAL_REQUEST_TIMEOUT_SECONDS` (finite; 30.0 until measured) and `store._txn.SurrealOutcomeUnknownError`
(subclass of `SurrealConnectionError`, so every existing transport handler still catches it).

| id | pin | rider | cost | HEAD | ref |
|---|---|---|---|---|---|
| CF1 | `connection_factory::TestACallDuringAnOutageFailsWithinItsBound` | 3a: store stays down → `SurrealConnectionError` within the default + 10 s | ~30 s | R | G |
| CF2 | `…TestALongOperationOutlivesTheDefaultTimeout::…startup_ddl…` | 3c: `SurrealStore.ensure_ready` survives one reply held default + 2 s (`hold_next_response`) | ~35 s | R | G |
| CF2c | `…::test_control_the_same_hold_times_out_an_ordinary_call` | control: the same hold times out a plain call | ~32 s | R | G |
| CF3 | `…TestAWriteWhoseOutcomeIsUnknownIsRaisedAsUnknown` ×3 | 2: in-flight drop (single statement, transaction) and a reply outliving `with db.timeout(1)` → `SurrealOutcomeUnknownError` | ~5 s | R | G |
| CF4 | `…TestATimedOutWriteUnderTheFactoryCommitsNothing` | R7 streaming "explicit, pinned" — **fork F11**, recommended reading (streaming ON → a timed-out write never lands) | ~5 s | R | G |
| L6 | `lifecycle::TestRecoveryLatencyAfterALongOutage` (rewritten) | 3b: ∀ owners (derived), 15 s outage, every first call answers ≤ 3.0 s after the store returns; an owner bypassing the factory (SDK default backoff) or with a finite attempt count fails it | ~20 s | R | G |
| L1/L2/L3/L4/L5 | `lifecycle` (unchanged) | idle-bounce first call ∀ owners; repeatable; racing call typed; no zombie; closed stays closed | — | L1/L2 R | G |

"Keep any >30 s pin's cost stated": CF1 ~30 s, CF2 ~35 s, CF2c ~32 s (they run in parallel under `-n 8`; the whole
factory file took 34.6 s wall on the reference).

### R3.4 R7 F8/F7, F9 native, R6 F5, W6, db.batch

**F8/F7 — `test_sdk3_record_ids.py`.** The fixture discriminates by RENDERING: `_rendered(rendering)` patches
`RecordID.__str__` to each rendering an SDK release has shipped — `angle` (3.0.0 `t:⟨k⟩`) and `backtick` (3.0.1
``t:`k` ``) — for EVERY string key (so no hunting for a digit-led id), plus `installed`. The SDK encodes a RecordID
from `table_name`/`id` (CBOR tag 8, read in both SDKs' `data/cbor.py`), so the patch never reaches the wire.

| id | pin | HEAD | ref |
|---|---|---|---|
| K0 | `TestARecordIdRoundTripsAsAValue::…value_that_was_written` — every minted key shape: equal, hashable alike (set/dict key) — retires the "RecordID is unhashable" idiom (drop list #9) | R (TypeError) | G |
| K0b | `…server_parsed_text_in_either_bracket_style…` — `StringRecordId` reads bare, ⟨⟩ and backtick text as the same record | R (no `StringRecordId` in 2.0) | G |
| K1 | `TestTheIdLoreServesNamesTheEnginesKey::…served_id[installed\|angle\|backtick]` — `Keep.id` == engine `<string> id`, found again | installed G, angle/backtick R | G |
| K2 | `…found_by_its_id_written_in_any_form` — `get_keep` accepts bare / ⟨⟩ / backtick | R | G |
| K3 | `TestAKeeperCannotBeDeletedWhileKeeping[installed\|angle\|backtick]` — served `Principal.id` is engine text; a digit-led keeper is refused deletion | installed G, others R | G |
| K4 | `TestARegisteredAgentIsOwnedAndScopedByEngineIds[angle\|backtick]` — through `AppContext._comms_register`: `agent.owner_principal` is the registrant's record, `agent.scope` the session keep's engine text | R | G |

Bound, stated: the pins prove BEHAVIOUR (served/persisted text is the engine's, under any rendering). Deleting the
`partition(":")` / `split(":")` re-parsers is a drop-list item: once served text is engine text they parse it
correctly for word keys, so no behavioural pin can tell "deleted" from "harmless" — that would be a spelling check
(operator approval needed). Not pinned: `memory/local.py` owner compare (`split(":")[-1]`), `principals` migrate
backfills, `server.py` comms-send scope, `governed._bare` → `audit.actor_email` — the adversary may demand them.

**F9 native — `test_sdk3_native_shapes.py`.** Engine fact (probed first, `probe_f9_starts_with.py`, Appendix D):
`string::starts_with(value, $p)` on 3.3.5 plans `IndexScan` alone and `BitmapOr > BitmapIndexScan×n` OR'd (2 and 3
prefixes); `string::starts_with(string::lowercase(value), $p)` (control) TableScans.
Pins: `TestTheNativePrefixMatchIsIndexServed` ×4 + control (GREEN at HEAD — the defect is gone on the ENGINE);
`TestTheModulePrefixReachIsIndexServed` ×4 on the PRODUCTION statement (`SurrealCodeGraph._prefix_range_query`):
`[max_codepoint]` is **RED at HEAD — an OLD BUG the range workaround carries**: for a prefix ending in U+10FFFF
`_prefix_upper_bound` returns None and the query falls back to an UNBOUNDED `value >= $lo`, returning every
later-sorting name (measured: `pkg.m10.sym*`…`pkg.m29.*` for prefix `pkg.m1.\U0010ffff`). The native form fixes it.
Mutation M-F9: wrap `value` in `string::lowercase` inside the production builder → declared reds: the 4 production pins.

**F5 — `TestTheSdkGuardReachesTheBuilderDoors`.** The door set is DERIVED from the SDK class: a coroutine function, or a
method whose annotated return is awaitable / async-iterable / carries a coroutine method. Measured on SDK 3.0.0:
`query, select, create, update, upsert, delete, insert, relate` (awaitable builders), `batch` (AsyncBatch.execute),
`live_of` + every coroutine. Pins: every derived door is guarded (with `query ∈ doors` as the checked variable);
a bare `.query()` outside the driver is recorded as an escape AND observed through the guard's public hook chain; a
two-statement `.query()` inside the driver is a multi-statement violation. GREEN at HEAD (2.0's doors are coroutines);
the reference build's widened guard (`_is_door`) makes them GREEN on 3.0. ⚠ The SAME coroutine-only reach exists in
`_surreal_harness.StoreTraffic.COUNTABLE_DOORS` / `uncountable_doors` (builder flag, §R3.10).

**W6 (R7 wording).** RP3's transactional leg now runs `query_raw` → `_txn._failed_statements` → `_txn._rollback_verdict`
and requires the conflict root cause the SELECTOR names to satisfy `is_transaction_conflict`; it never reads `query()`
(which raises the first failure, a `NotExecuted` notice with the predicate False — scout-40 112/112). Mutation M-W6
(the predicate answers False in the production classifier) → declared reds: RP3, T1, T2.
If the builder adopts `db.batch()`, RP3's leg re-points at the error `db.batch()` raises (said in the test).

**db.batch() CONDITIONAL (R7).** The transaction behaviour lore needs is pinned in `test_sdk3_txn_classification.py`:
T1/T2 conflict typing + retry at 16-way, nothing lost; T3 root cause at three THROW positions (kind `Thrown`, never a
cascade kind), one attempt, nothing committed; T4 text never buys a retry; **T6 (new) a THROW whose text QUOTES the
cascade notice still surfaces as `Thrown`** — read in SDK source (`connections/batch.py::_results`): `db.batch()`
selects the first failure whose message does not contain `"not executed due to a failed transaction"`, so it
skips such a THROW and reports a cascade/Cancelled/COMMIT notice instead. Expected: a `db.batch()` build FAILS T6 (not
run here: building it is the builder's measurement, per R7). Also not met by `db.batch()` as read: lore logs EVERY
failed statement server-side (`_log_rollback`) where `db.batch()` raises one error — a removed behaviour the builder
must preserve or drop deliberately (§R3.6 row X12).

### R3.5 DROP LIST — everything SDK 3.0 / engine 3.3.5 lets lore delete (the lead presents this before any deletion)

Fates: **R** retire-now-with-pin · **C** conditional-on-measurement (named) · **K** keep-with-reason. Draft by a Sonnet
sweep (scratch `sdk3r3/droplist_draft.md`, every row SDK-source-quoted), sampled and re-fated by me.

| # | what | where (symbol) | SDK/engine-native replacement | evidence | fate · pin |
|---|---|---|---|---|---|
| 1 | `KeyError`-as-transport arm | `_txn._SDK_AWAIT_BOUNDARY_ERRORS`, `run_query._attempt` / `_txn_query_raw` excepts, `_raise_attempt_failure` | `errors.ConnectionUnavailableError(TransportError)` | P1 (round 2): 4/4 in-flight → typed | **R** · RP1 (+M1 round 2) |
| 2 | bare `"TransactionConflict"` literal + `_detail_kind` decision | `_txn._RETRYABLE_CONFLICT_KIND`, `_is_retryable_conflict_kind` | `QueryError.is_transaction_conflict` | P6: 5/5 + 29/29 | **R** · RP3 (+M-W6), T1/T2 |
| 3 | 18 per-owner `AsyncSurreal(url)` + reconnect-on-next-call self-heal (#576) | every `_ensure_connection` / `_drop_connection` (17 stores + scout) | ONE factory, `ReconnectOptions(attempts=-1, retry_delay=0.5, retry_delay_max=2.0)` | R5; L1/L6 ∀ owners | **R** (simplify: the drop stays as the racing/give-up backstop, W7) · L1, L2, L6, RP2 |
| 4 | scout's unconditional non-CAS `_drop_connection` (S1) | `scout.CommandSubscriber._drop_connection` | the factory's reconnect | R6 S1 | **R** · L1 (scout is in the derived owner set) |
| 5 | `partition(":")` / `split(":")` / `_bare_id` text re-parsers of SERVED ids — **~31 sites in 3 families, not 4** | `keeps._record_id_part`/`_resolve_principal_id`, `principal_keys._record_id_part`, `principals` (803, 1527, 2196, 2197, 2292), `server` (6723, 6756, 6771, 7322), `governed._bare`, `memory/local` (1405, 1410), 7 `_bare_id` clones (findings, messages, agents, tasks, briefs, memory/local, store/surreal) | `RecordID(table, key)` from `.table_name`/`.id`; `StringRecordId(text)`; engine `<string> id` | R7 (moved, round 3: , re-cut for ruling R7) | **R** (scope: fork F16) · K1–K4 (behaviour; deletion itself unpinnable, §R3.4) |
| 6 | `str(RecordID)` as served/persisted text | `keeps._row_to_keep`, `principals._row_to_principal`, `principal_keys` mapper, `audit` return value | `.table_name + ":" + .id` / engine `<string> id` | R7 (d) | **R** · K1, K3, K4 |
| 7 | "RecordID is unhashable" → str-keyed sets/dicts | `graph_surreal` de-dupe (`unique[str(record_id)]`, `name_ids_by_key`, …), docstrings in findings/tasks/agents/briefs/store | `RecordID.__hash__` (SDK 3.0 `record_id.py`) | measured 2.0 `TypeError` | **R** · K0 |
| 8 | six cloned datetime coercers (`_to_aware_utc` ×6) | agents, briefs, findings, messages, principals, tasks | `PreciseDatetime` (a `datetime`; `astimezone` keeps `.nanosecond`, measured) | R6 S2 | **C**: before deleting each, list the columns it reads with their DECLARED types; a `string`/FLEXIBLE column keeps its string branch (§R3.6 X8). Pin R6b (ns kept) |
| 9 | `_CONNECTION_ERRORS` / `_SDK_AWAIT_BOUNDARY_ERRORS` hand-kept tuples incl. `WebSocketException` | `_txn`, consumers scout + inbox_awaiter | `TransportError` / `ConnectionUnavailableError` | R6 F10 | **C**: the two F10 measurements (§R3.7b); KeyError half is #1 |
| 10 | `>= $lo AND < $hi` prefix range + `_prefix_upper_bound` (and its max-codepoint unbounded fallback — an old bug) | `graph_surreal._prefix_range_query`, `_prefix_upper_bound` | `string::starts_with(value, $p)` (index-served on 3.3.5) | P14, `probe_f9_starts_with.py` | **R** · native_shapes ×9 (+M-F9) |
| 11 | per-row index statements + the STATEMENT cap as the strain bound (R3) | `SurrealStore.replace_file_fragment`, `SurrealCodeGraph.build_file_graph_fragment`, `_txn.TXN_STATEMENT_HARD_CAP` | one `INSERT` / `INSERT RELATION` per table; a ROW cap | R4 | **R** · B1–B4 (+M-R4); scope of the statement cap: fork F12 |
| 12 | `run_query` returning `query()`'s value raw (SDK 2.0 first-statement shape) | `_txn.run_query`, `scout._scout_query_once`, `inbox_awaiter._live_query` | SDK 3.0 per-statement list + ONE selection | R2 | **R** (replace) · S1–S4, R1–R10 (+M-R2) |
| 13 | `AsyncEmbeddedSurrealConnection` imports | `_txn` alias, `_sdk_guard.SDK_CONNECTION_CLASSES`, `_surreal_harness`, `test_retry_seam` | moved to `surrealdb-embedded` | round 2 D9 | **R** (dropped; nothing uses the embedded engine) |
| 14 | hand verification of every statement + text `BEGIN;…COMMIT;` wrappers + `execute_read_transaction` | `_txn._failed_statements`/`_parse_failed_statement`/`_rollback_verdict`/`compose` envelope; 19 `BEGIN;\n{ddl}COMMIT;` sites | `db.batch()` (one request, refuses BEGIN/COMMIT/non-final RETURN, raises root cause) | R7 conditional; `batch.py::_results` read | **C**: `db.batch()` must pass T1–T6 + per-statement rollback logging; T6 is expected to FAIL it (text selector) — then keep `compose` and file the gap upstream |
| 15 | `_SDK_PARSE_FAILURES` guard (`AttributeError`, `TypeError`, `RecursionError`) around `parse_query_error` | `_txn._parse_failed_statement` | SDK 3.0 `parse_rpc_error` now returns `InternalError` for a non-dict (the `AttributeError` arm) | source read | **C**: probe a non-dict cause, an unhashable kind, a deep chain on 3.0 — retire each arm that no longer raises |
| 16 | `_safe_close` (try close except `_CONNECTION_ERRORS`) ×18 | every owner | SDK `close()` is idempotent; `_teardown` swallows | source read | **C**: measure `close()` over a severed socket (both sever modes) never raises on 3.0 |
| 17 | `signin_credentials` + 18 `.signin()` + manual re-sign-in | `_txn.signin_credentials`, owners, scout | `auth=` provider replayed after every reconnect | `auth_provider.py` docstring | **C**: under the factory, an idle-bounce replays auth without lore (RP2 already shows replay for `signin`); adopt `auth=` if the factory owns credentials — design call for the builder |
| 18 | `_CONNECTION_ERROR_KINDS = {NotAllowed, Connection}` | `_txn.is_connection_error` | `NotAllowedError.is_invalid_auth` / `is_token_expired` | source read | **K** with trigger: W3 (NotAllowed after reconnect give-up) can no longer occur with `attempts=-1`; keep the arm until the factory is the only constructor, then re-evaluate |
| 19 | `"recursion depth"` text marker | `_txn._classify_engine_error` | `ValidationError.is_parse_error` (a superset) | source read | **C**: probe the recursion-limit rejection's `details.kind` on 3.3.5 |
| 20 | ASSERT / coercion / UNIQUE / governed THROW text markers | `_txn._classify_engine_error` | none (Internal is untyped) | P7 | **K**: still untyped on 3.3.5 (W10) |
| 21 | scout's reconnect ladder backoff | `scout.CommandSubscriber._backoff` (+ `loresigil.backoff.jittered_backoff_delay`) | SDK reconnect for the socket | `reconnect.py` | **C**: measure whether scout's ladder still fires (connect failures at boot) once the factory reconnects forever; delete the socket half only. *(Round 6, 2026-11-07: overlaps R11 — R11 already moves the ladder's hand loop onto tenacity, so the measurement decides only WHETHER a ladder survives (and how much of it); whatever survives is on tenacity with the shared full-jitter policy, never the hand loop. Pinned: `test_backoff_seam::TestTheSubscribersConnectLadderSleepsTheSharedDraw`.)* |
| 22 | `retry_on_conflict` / `_txn_conflict_backoff_seconds` | `_txn` | `tenacity.AsyncRetrying` (installed 9.1.4) + `wait_random_exponential` via `loresigil.backoff` | research §C; R10, R11, R12 F22 | **R** (R11, 2026-11-07, supersedes R10's C and round 3's K): the driver becomes a tenacity `AsyncRetrying` (stop = attempt budget / deadline; `retry=` = the seam's own classifier); `_txn_conflict_backoff_seconds` stays the ONE jitter source but delegates to tenacity's full jitter (F22). *(Row text corrected in round 6; it read K.)* |
| 23 | lease thread-bridge timeout | `store/lease._call` | `with db.timeout()` bounds an SDK await, not a thread wait | source read | **K** |
| 24 | inlined literals in `LIVE SELECT … WHERE` | `inbox_awaiter.live_select_statement`, scout | `live()` has no filter; `live_of` | source read | **K** (no native filter); hand-escaping ``agent:`{id}` `` → `escape_identifier`: **C** (an id holding a backtick) |
| 25 | `name.value` mirror column (prefix-match a RecordID id) | `graph_surreal._COL_VALUE`, schema | `string::starts_with(record::id(id), $p)` or an id range | unprobed | **C**: probe index service on 3.3.5 |
| 26 | `rebuild_embeddings` REMOVE/DEFINE two-transaction dance | `memory/local.LocalMemoryBackend.rebuild_embeddings` | blocking `REBUILD INDEX` (research B14, LOW) | not probed | **C**: measure on 3.3.5 |
| 27 | `check_response_for_error` after `query_raw` | `_txn._txn_query_raw` | already the SDK's | source | **K** (native; goes with #14 if `db.batch()` is adopted) |
| 28 | `_PROVEN_KINDS` / `_typed_kind` | `_txn` | already SDK constants | source | **K** (already native) |
| 29 | keepalive (none in lore) | — | SDK `ping_interval=30`, `ping_timeout=10` | source | **K-inherited**: new behaviour lore gets silently; a half-open peer is noticed in ~40 s. Disposition needed (recommend accept SDK default; state it in the store reference) |
| 30 | version gate (none in lore) | — | `version_check=True`, `MINIMUM 2.0.0 / MAXIMUM 5.0.0` | source | **K-inherited** (recommend accept) |
| 31 | 30 s default request timeout (none in 2.0) | — | `timeout=30.0` | R5 | ruled: finite default + named overrides (CF1, CF2) |

### R3.6 Removed-behaviour inventory (the reshape dual) — one row per behaviour a deletion removes

Adjudications: **pin** preserved-with-pin (spec clause) · **drop** dropped-deliberately (reason) · **old-bug** ·
**ruling** spec-silent → operator. Independent enumeration from the CODE at `b03c4fc`, then diffed against the drop list.

| X | deleted thing → behaviour it carried | adjudication |
|---|---|---|
| X1 | KeyError arm → a raw `KeyError` from the SDK-await boundary is transport: drop + `SurrealConnectionError` | drop (SDK 3.0 never raises it: P1, RP1); a `KeyError` from lore's own code now propagates as a bug — correct |
| X2 | KeyError arm → `inbox_awaiter` / scout recover from it (the shared-tuple mutation pins) | drop with X1; the pins asserting it (§R3.10) change with the builder |
| X3 | literal → retry decided by `details.kind == "TransactionConflict"` on BOTH paths | pin (R1/W6): RP3, T1, T2 via the SDK predicate |
| X4 | literal → a `ServerError` that is NOT a `QueryError` but carries `details.kind: TransactionConflict` was retryable | old-bug-or-dead: the engine sends conflicts as `kind: Query` (P6); spec-silent → keep `isinstance(QueryError)` |
| X5 | self-heal → an idle owner's FIRST call after a restart failed, the second healed (#576) | old-bug, fixed: L1 |
| X6 | self-heal → a call racing the drop fails once, typed; the handle is replaced | pin: L3, L4 (drop stays) |
| X7 | self-heal → after any transport error a NEW socket is built (fresh auth, fresh session) | pin: L4 (one socket, no zombie); W3 give-up path unreachable with `attempts=-1` |
| X8 | coercers → a naive datetime becomes UTC; an ISO string is parsed; unparseable → `None`; aware → UTC | ruling-if-reachable: engine returns aware PreciseDatetime (branch unreachable for `datetime` columns); the string/None branches are behaviour only for a column that can hold a string — the builder lists each coercer's columns' declared types before deletion (drop #8 C). `PreciseDatetime.replace(tzinfo=UTC)` DROPS `.nanosecond` (measured), so the naive branch, if ever reached, loses ns |
| X9 | parsers → a served id with NO `:` passes through unchanged (bare id accepted) | pin: K2 (bare/text forms via `StringRecordId`; a no-colon text is a `RecordID(table, text)` in the reference) — **spec-silent for non-keep tables** → fork F17 |
| X10 | parsers → `principals.delete` binds the id part of the served id to read kept keeps | pin: K3 |
| X11 | range → max-codepoint prefix answered with an unbounded `>=` (superset) | old-bug, fixed by native: `[max_codepoint]` RED at HEAD |
| X12 | `_failed_statements` / `_log_rollback` → every failed statement's index + raw engine text logged server-side; the raised error carries only the classified label (#31) | pin-needed if `db.batch()` replaces it: no contract pin today asserts the per-statement log (pre-existing `test_retry_seam` / rollback-log pins cover it — §R3.10 lists them for the builder) |
| X13 | per-row statements → each row its own `UPSERT`/`CREATE` (`UPSERT` = overwrite a same-id chunk; `CREATE` node fails if present) | spec-silent → **ruling-light**: batched `INSERT` FAILS on a duplicate id where `UPSERT` overwrote; after the per-file DELETE only an intra-file duplicate point id can collide. Reference used plain `INSERT` for chunks (B1 green); builder confirms point ids are unique per file or uses `ON DUPLICATE KEY UPDATE` |
| X14 | per-row `RELATE … SET` → edges written only after their endpoint `UPSERT`/`CREATE` statements | pin: B4 (no dangling edge) |
| X15 | statement cap → a pathological file refused at BUILD time with a typed `SurrealStoreError`, isolated `failed`, last-good kept | pin: B3 (now NAMED, with its bound); the per-file isolation is pre-existing (`test_indexer_surreal_integration`) |
| X16 | `run_query` returned statement[0] for a multi-statement text (silently ignoring the rest) | old-bug (#144 class): S1–S3 |
| X17 | `str(RecordID)` served ids carried SDK 2.0's own bracketing for all-digit / non-word keys (`task:⟨0199c4f1-…⟩`, #248) | ruling via F8 count (§R3.7): engine text brackets non-word keys too, so a dashed task id serves IDENTICALLY (`<string> id`); `.table_name + ":" + .id` would serve it BARE — the two R7 (d) forms differ exactly here → fork F15 |

### R3.7 For the lead

**(a) F8 read-only check on :18500 (the lead runs it; I did not touch :18500).** Field inventory: Sonnet draft
(`sdk3r3/f8_inventory.md`, 212 `DEFINE FIELD` derived by calling every `surreal_schema.generate_*_ddl()`, 122
string-bearing classified), spot-checked by me against `governed.GuardedPlan.fragments` (`target_row=f"{self.table}:{self.row_id}"`),
`governed.resolve_subject` (`principal_id=_bare(principal.id)` → `audit.actor_email`), `keeps._row_to_keep`
(`id=str(row["id"])`) — all three as described. Run in EVERY namespace/database that holds these tables (they share one
project database per ns/db); ONE read-only statement, validated on a throwaway :18000 database with controls (one
⟨⟩ scope, one backtick ref → counted 1 each; bare values → 0):

```surql
RETURN {
  agent_scope: count((SELECT id FROM agent WHERE string::contains(<string> scope, '⟨') OR string::contains(<string> scope, '`'))),
  agent_task_id: count((SELECT id FROM agent WHERE string::contains(<string> task_id, '⟨') OR string::contains(<string> task_id, '`'))),
  memory_scope: count((SELECT id FROM memory WHERE string::contains(<string> scope, '⟨') OR string::contains(<string> scope, '`'))),
  memory_supersedes: count((SELECT id FROM memory WHERE string::contains(<string> supersedes, '⟨') OR string::contains(<string> supersedes, '`'))),
  memory_superseded_by: count((SELECT id FROM memory WHERE string::contains(<string> superseded_by, '⟨') OR string::contains(<string> superseded_by, '`'))),
  message_scope: count((SELECT id FROM message WHERE string::contains(<string> scope, '⟨') OR string::contains(<string> scope, '`'))),
  message_task_id: count((SELECT id FROM message WHERE string::contains(<string> task_id, '⟨') OR string::contains(<string> task_id, '`'))),
  message_refs: count((SELECT id FROM message WHERE string::contains(<string> refs, '⟨') OR string::contains(<string> refs, '`'))),
  audit_target_row: count((SELECT id FROM audit WHERE string::contains(<string> target_row, '⟨') OR string::contains(<string> target_row, '`'))),
  audit_actor_email: count((SELECT id FROM audit WHERE string::contains(<string> actor_email, '⟨') OR string::contains(<string> actor_email, '`'))),
  audit_actor_agent_name: count((SELECT id FROM audit WHERE string::contains(<string> actor_agent_name, '⟨') OR string::contains(<string> actor_agent_name, '`'))),
  task_blocked_by: count((SELECT id FROM task WHERE string::contains(<string> blocked_by, '⟨') OR string::contains(<string> blocked_by, '`'))),
  task_superseded_by: count((SELECT id FROM task WHERE string::contains(<string> superseded_by, '⟨') OR string::contains(<string> superseded_by, '`'))),
  file_chunk_ids: count((SELECT id FROM file WHERE string::contains(<string> chunk_ids, '⟨') OR string::contains(<string> chunk_ids, '`')))
};
```
⚠ Bounds: a table that does not exist in a database raises NotFound on 3.x (drop that key for that database); free
text can contain a backtick legitimately (`message.refs`), so a non-zero count is a lead to inspect
(`SELECT id, refs FROM message WHERE … LIMIT 20`), not a verdict. Out of scope (record-typed, not strings):
`owner_principal`/`owner_agent`, `keep.keeper`, `message.sender`, `audit.actor_principal`/`actor_agent`, every edge's
`in`/`out`. Expected from the key shapes (ULID keeps, engine `[a-z0-9]` principals, uuid hex): ~0, except legacy dashed
task ids (#248) in `task.blocked_by` / `message.task_id` / `message.refs`.

**(b) F10 — the two measurements the builder owes before `WebSocketException` leaves `_CONNECTION_ERRORS`.** Both on
SDK 3.0.0 + 3.3.5 through `_sdk3_proxy.StoreBounceProxy`, each × `SeverMode.ABORT` and `SeverMode.CLOSE_FRAME`, 20 runs
each, on a connection from the shared factory:
1. **LIVE iterator over a dead socket:** `LIVE SELECT` via the seam → `subscribe_live(id)` → start iterating → `go_down()`
   (no `come_up`) → record, for 10 s, what the iterator does: raises (record the exact class and module), ends, or
   hangs; then `come_up()` and record whether it resumes (SDK 3.0 does not replay a `query()`-made LIVE — source read).
2. **`kill()` over a dead socket:** same setup → `go_down()` → `await connection.kill(id)` → record the raised class
   (and whether it waits on the reconnect, bounded by the timeout); repeat with the store back (`come_up` first) → the
   kill of a LIVE the new session never had.
Retire the arm iff no run raises a `websockets.*` class; otherwise keep it with the observed path as its reason.

**(c) F6 — `pending_contracts.yaml` pytest-only adjudication (a gate change; the builder implements).** Shape: a
`PendingBound` gains `red_nodeids: tuple[str, ...] = ()` (a `PendingFile` may then carry no mypy content). Semantics in
`pending_contract_gate.py --currency` (pytest leg only): (1) a failing node id listed under a bound →
`RED_ADJUDICATED(owner, reopen_trigger)`; (2) a failing node id not listed → `RED_ORPHANED` (unchanged); (3)
**self-destruct:** a listed node id that PASSES fails the gate ("adjudicated red `<id>` is green — delete it with the
fix"), exactly like the typecheck leg's "produced NO mypy errors"; (4) **stale:** a listed id that is not COLLECTED
(renamed/deleted) fails the gate; (5) ids are written from `pytest --collect-only -q` (pytest escapes non-ASCII in
parametrised ids), and a parametrised id is listed per parameter, never by prefix. The 33 HEAD-red ids of §R3.9 are the
first entry (owner: packet SDK3 builder; trigger: the SDK3 build lands).

### R3.8 Forks for the operator (each: the readings, my recommendation, what the pins assume)

- **F11 — R7 "the shared factory sets streaming EXPLICITLY, pinned" names no VALUE.** ON (SDK default): a timed-out
  request is cancelled (nothing commits, measured on both engines). OFF: the engine keeps running and commits.
  Recommend **ON**. CF4 pins ON; ruling OFF inverts its last assertion. ("Explicitly" itself is spelling — unpinnable
  without a source scan.)
- **F12 — R4 "the cap is re-expressed as a bound on rows or bytes": replace the STATEMENT cap everywhere, or add the row
  bound beside it?** (a) replace: `compose()`'s statement cap goes; packet 58's re-anchor packer
  (`test_reanchor_58_*`, `test_supersede_reanchor_58`) and the entity seam (`test_ingest_entity_seam` P6) are sized by
  statements and must re-size by rows; (b) add: keep 5,000 statements as a second backstop (harmless once the index is
  batched). Recommend **(a)** — statement count no longer measures strain — with 58 re-sized when it is revived (it is
  dormant, SDK3 is scheduled first). The reference kept (b) (minimal); B1–B4 hold under both.
- **F13 — R2 rider "scout._scout_query_once and inbox_awaiter._live_query are converted to the same seam".** (a) route
  them through `run_query` itself: scout's transport faults become `SurrealConnectionError`, contradicting
  W1-SCOUTKILL (its reconnect ladder catches RAW SDK types; `test_retry_seam` pins it); (b) they keep their raw-error
  contracts and call the ONE selection function `run_query` also calls. Recommend **(b)**; S4/R10 and M-R2 hold under
  both. The reference did (b).
- **F14 — "a timed-out or in-flight-dropped WRITE is raised as outcome unknown": the seam cannot tell a read from a
  write, nor a request that was sent from one parked on a reconnect** (both surface as `TransportTimeoutError`).
  Recommend: every SDK `TransportError` on a request → `SurrealOutcomeUnknownError` (a `SurrealConnectionError`
  subclass — harmless for reads). Pins assert writes only; CF1 accepts either class.
- **F15 — R7 (d) offers two text forms that DIFFER for a non-word key:** engine `<string> id` renders
  `task:⟨0199c4f1-…⟩` (bracketed, as SDK 2.0 did — #248); `.table_name + ":" + .id` renders it bare. For every key lore
  mints today (ULID, `[a-z0-9]`, hex) they agree. Recommend: the ENGINE form for anything persisted or compared with
  persisted text (it equals what SDK 2.0 wrote for legacy dashed ids), `.table_name + ":" + .id` only for display.
  The pins use word-char keys (both forms pass); the F8 count decides whether legacy bracketed rows exist.
- **F16 — R7 says "the four `partition(":")` parsers are deleted"; the sweep finds ~31 re-parse sites in three families**
  (drop list #5). Recommend deleting all of them under the same ruling (one principle).
- **F17 — text with NO `:` handed to an id-taking API** (`get_keep("01J…")`): `StringRecordId` refuses it
  (`InvalidRecordIdError`). The HEAD parsers pass a bare key through. Recommend: accept a bare key as
  `RecordID(<that API's table>, text)` (the reference does, for keeps). Unpinned beyond keeps.

### R3.9 Receipts

Logs in the lead-named scratch `scratchpad/sdk3r3/receipts/` (the reference build is `scratchpad/sdk3r3/ref`, its diff
`scratchpad/sdk3r3/reference_build.diff`). Every final log opens with `tree_id.sh`.

| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| contract @HEAD (SDK 2.0.0) | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest -q -rfE -p no:cacheprovider --timeout=300 -n 8 <the 9 test_sdk3_* files>` | `r3_head_contract_final.log` | 1 | 33 failed, 37 passed, 4 errors — the observed FAILED set equals the 33 declared ids exactly (diffed both ways); the 4 ERRORs are the autouse guard's teardown on 4 of those same 33 (S1×2, S2, S3: a multi-statement `.query()` reached the wire at HEAD) | TREE=e74c4c91…c46e (HEAD b03c4fc) |
| contract @reference (SDK 3.0.0) | same files + the 2 KNOWN-BOUND classes + `test_graph_surreal::TestNamesWithValuePrefixRangeRewrite`, `.venv/bin/python -m pytest` in the scratch copy | `r3_reference_contract.log` | 0 | **94 passed** | TREE=d83f5268…fe0f (scratch copy) |
| mutation proofs M-R2, M-R4, M-F9, M-W6 | `scratchpad/sdk3r3/mut/run_mutations.sh` (`scripts/mutation_proof.py`, declared reds in `mut/*.expect`) | `r3_mutation_proofs.log` | 0 | PROOF HELD ×4 — M-R2 10 failed/4 passed; M-R4 1/3; M-F9 4/8; M-W6 3/10 — each the declared set exactly; tree restored | TREE=d83f5268…fe0f (same scratch tree) |
| currency `--legs typecheck,ruff` | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `r3_gate_currency.log` | 1 | typecheck RED_ADJUDICATED (83, packet-58 + packet-64b-i) · ruff GREEN · **no RED_ORPHANED** · pytest NOT_RUN (the `--legs` subset still reports the unrun pytest leg — the gate quirk rounds 1/2 flagged) | TREE=e74c4c91…c46e (HEAD b03c4fc) |

Declared RED-at-HEAD set (33, from `--collect-only`, written before the run): `receipts/declared_red_head_final.txt`.
Edited after these runs: ONLY this packet doc (§R3.9 receipt cells, §R3.11) (so a re-derived TREE of the repo differs by this file
alone). A T2 flake was caught BETWEEN receipt rounds and fixed before the final runs: round-1's
`test_sixteen_way_single_statement_updates_all_commit_once` failed its own contention premise once on the reference
(32 updates, 0 conflicts — on 3.3.5 a single-statement increment conflicts ~3% of the time, so two fixed rounds saw no
conflict in ~38% of runs); its rounds are now adaptive (until a conflict, ≤ 25 rounds).
Provenance receipt of the reference: `loremaster.__file__=…/scratchpad/sdk3r3/ref/loremaster/loremaster/__init__.py`,
`surrealdb=3.0.0` (first lines of `r3_reference_contract.log`).

**What the reference build did NOT do** (satisfiability instrument, not the build; the builder owns all of it): S2
coercer deletion; the parser deletions (fixed the served text at the row mappers instead); `db.batch()`; the
`_SDK_PARSE_FAILURES`/`_safe_close`/`auth=` conditionals; port `scripts/` (21 SDK users); fix
`_surreal_harness.StoreTraffic` reach, the session-end reaper and `drop_database`'s SDK-2.0 shapes (only `run()` was
adapted); named overrides beyond `SurrealStore.ensure_ready`; the full covering-test sweep (`lore_impact` was
unavailable; the reference ran ONLY the set above — every pre-existing test that asserts an SDK 2.0 shape will be RED
on it, §R3.10).

### R3.10 Pre-existing pins / helpers that contradict a ruling (the builder changes them; outside this writable set)

- `tests/_sdk_guard.py` — `SDK_CONNECTION_CLASSES` names `AsyncEmbeddedSurrealConnection` (ImportError on 3.0); door
  reach coroutine-only (F5; reference `_is_door`).
- `tests/_surreal_harness.py` — embedded import + alias; `run()` returns `query()`'s value raw (must select its ONE
  statement); `StoreTraffic.COUNTABLE_DOORS` / `uncountable_doors` derive reach from `iscoroutinefunction` (same class
  as F5 — under 3.0 `query` is neither countable nor uncountable); the INFO-map reaper (round 2 §7).
- `tests/test_retry_seam.py` — two `AsyncEmbeddedSurrealConnection` imports; its KeyError-at-the-await-boundary pins
  and the `_SDK_AWAIT_BOUNDARY_ERRORS` shared-tuple mutation pins (R6 F10 / drop #1) — 25 retired-name hits.
- `tests/test_comms_await.py` — 24 hits on the KeyError / `WebSocketException` boundary (drop #1, #9).
- `tests/test_surreal_apply.py`, `tests/_surreal_fakes.py`, `test_ingest_entity_seam.py` P6,
  `test_reanchor_58_*`, `test_supersede_reanchor_58.py` — the STATEMENT cap (F12).
- `tests/test_graph_surreal.py::TestNamesWithValuePrefixRangeRewrite` — behaviour pins hold on the native form
  (measured on the reference); its docstrings narrate the range rewrite (prose to update).
- `tests/test_sdk3_result_shapes.py` round-1/2 R7 asserted SDK 2.0's RENDERING — contradicted R7; removed here (the
  only one inside this writable set).
Full retired-name sweep (tests tree, 207 hits in 40 files, P8 pattern in `sdk3r3/sweep/run_sweep.sh`):
`sdk3r3/sweep/out/P8_tests_pin_retired.txt` — every hit is the builder's to adjudicate; I did not adjudicate them one
by one (NOT DONE: per-hit verdicts).

### R3.11 DRY ledger (round 3 — every new reusable symbol is test-side)

| new symbol | where I looked | found | disposition |
|---|---|---|---|
| `_sdk3_proxy.StoreBounceProxy.hold_next_response` | the proxy itself; grep `delay\|latency\|hold` in `loremaster/tests` | no slow-store fault anywhere | EXTENDED `StoreBounceProxy` (one-shot hold, counted) |
| `test_sdk3_index_batching._TransactionSpy` | `_surreal_harness.StoreTraffic` (counts `query_raw` per LEDGER connection, reach-checked) | instruments one ledger's connection; the index write rides the STORE's — and its door reach is the F5 defect class | REUSED `_sdk_guard._CALL_HOOKS` (the guard's public hook chain) rather than a second wrapper; the spy is the hook |
| `test_sdk3_native_shapes._is_door` / `_doors` | `_sdk_guard.install` (coroutine-only), `_surreal_harness.StoreTraffic.COUNTABLE_DOORS` (coroutine-only) | both are the defect F5 names | HAND-ROLLED in the test because it is the derivation the ruling asks the guard to adopt; the reference build put the same predicate in `_sdk_guard` (a second copy) — **the builder moves it into `_sdk_guard` and the test imports it** (one implementation) |
| `test_sdk3_record_ids._rendered`, `_angle`, `_backtick` | grep `__str__` monkeypatches in `loremaster/tests` | none | HAND-ROLLED (test fixture) |
| `test_sdk3_index_batching._big_module_source` | `test_mcp_server._map_budget_filler_source` | small-file filler, no call graph | HAND-ROLLED |
| `test_sdk3_single_statement_seam._Ignored` | `test_sdk3_lifecycle._ignore_command` | same job | near-duplicate (4 lines) — should import `_ignore_command`; left for the adversary round |
| `test_sdk3_connection_factory._required` | — | a getattr assertion | HAND-ROLLED (test-local) |
| reused | `_governed_contract.{explain, index_served, scans_table, credentialed_app_context}`, `test_mcp_server.{_config, _make_context, _slug, _surreal_test_env}`, harness `connect_admin`/`run`/`make_env`/`unique_database`/`drop_database`, `scout._open_command_connection`, `scripts/mutation_proof.py`, `scripts/scratch_copy.sh` | | REUSED |

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

## Appendix D — round-3 instruments (verbatim; run with the SDK under test, `-I`)

### `probe_r3_compose_breakdown.py`
```python
"""SDK3 r3 / ruling R4 rider (2): OFFLINE per-table breakdown of one file's composed index transaction.

    uv run python -I probe_r3_compose_breakdown.py <repo-relative .py path> [token_divisor]

Builds the SAME producer fragments `Indexer._compose_file_fragments` builds (chunk replace,
file_text, manifest row, code graph) with the production PURE builders — no socket is opened
(every builder is documented "a PURE builder (no I/O)") — then classifies every composed
statement by verb + table and every record it writes by table. Token counting for the chunker is
approximated (len/divisor); the statement total is compared to the 5,113 measured on production.
"""
import collections, re, sys
from pathlib import Path
from pydantic import SecretStr
from lorescribe.models import ChunkContext
from lorescribe.python_ast import PythonAstChunker
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.records import chunk_to_record, sha512_hex
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.store.surreal import SurrealStore
from loremaster.store._txn import compose, TXN_STATEMENT_HARD_CAP

REPO = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/home/ejprice/PycharmProjects/lore")
rel = sys.argv[1]
divisor = int(sys.argv[2]) if len(sys.argv) > 2 else 4
source = (REPO / rel).read_text()
wiring = dict(url="ws://unused.invalid:1/rpc", namespace="n", database="d", user="u", password=SecretStr("p"))
store = SurrealStore(dim=1024, **wiring)
manifest = SurrealManifest(**wiring)
graph = SurrealCodeGraph(tier_roots={"project": REPO}, project_roots=[REPO], **wiring)
ctx = ChunkContext(slug="lore", file_path=rel, count_tokens=lambda t: max(1, len(t) // divisor), max_input_tokens=32000)
chunks = PythonAstChunker().chunk(source, ctx) if hasattr(PythonAstChunker(), "chunk") else None
h = sha512_hex(source.encode()) if "bytes" in str(sha512_hex.__annotations__) else sha512_hex(source)
records = [chunk_to_record(c, slug="lore", tier="project", file_path=rel, content_hash=h, mtime_ns=0) for c in chunks]
pairs = [(r, [0.0] * 1024) for r in records]
fragments = {
    "chunk": store.replace_file_fragment("project", rel, pairs),
    "file_text": store.file_text_fragment("project", rel, source, h),
    "manifest": manifest.replace_fragment(tier="project", file_path=rel, sha512=h, mtime_ns=0, size=len(source),
                                          n_chunks=len(records), chunk_ids=[r.point_id for r in records], state="indexed"),
    "graph": graph.build_file_graph_fragment("project", rel, chunks, module_name=rel[:-3].replace("/", ".")),
}
verb_table = re.compile(r"^\s*(DELETE|UPSERT|CREATE|RELATE|INSERT RELATION INTO|INSERT INTO|UPDATE|LET)\s+(?:type::record\('(\w+)'|\$(\w+)|(\w+))?", re.I)
by_producer = collections.Counter(); by_verb_table = collections.Counter(); relate_edges = collections.Counter()
for producer, fragment in fragments.items():
    for statement in fragment.statements:
        by_producer[producer] += 1
        m = verb_table.match(statement)
        verb = m.group(1).upper() if m else statement.split()[0].upper()
        target = (m.group(2) or m.group(4) or (f"${m.group(3)}" if m.group(3) else "?")) if m else "?"
        if target.startswith("$"):
            bound = fragment.params.get(target[1:])
            target = getattr(bound, "table_name", None) or f"{target}<{type(bound).__name__}>"
        if verb == "RELATE":
            edge = re.search(r"->\s*(\w+)\s*->", statement)
            target = edge.group(1) if edge else "?"
        by_verb_table[(producer, verb, target)] += 1
text, params = (None, None)
total = sum(by_producer.values())
print(f"file={rel} chunks={len(records)} source_bytes={len(source.encode())} divisor={divisor}")
print(f"composed statements={total} (production measured 5,113 for test_comms_tool.py) cap={TXN_STATEMENT_HARD_CAP}")
for producer, n in by_producer.items():
    print(f"  producer {producer}: {n}")
for (producer, verb, target), n in sorted(by_verb_table.items(), key=lambda kv: (kv[0][0], -kv[1])):
    print(f"    {producer:9} {verb:8} {target:22} {n}")
try:
    statement_text, merged = compose(*fragments.values())
    print(f"compose: OK text_bytes={len(statement_text.encode())} params={len(merged)}")
except Exception as error:  # noqa: BLE001 - the refusal IS the observation
    print(f"compose: REFUSED {type(error).__name__}: {str(error)[:160]}")
for producer, fragment in fragments.items():
    print(f'  params {producer}: {len(fragment.params)} repr_bytes={len(repr(dict(fragment.params)).encode())}')
```

### `probe_f9_starts_with.py`
```python
"""SDK3 r3 F9 probe: is string::starts_with index-served on 3.3.5 for the shapes lore's prefix reach
emits (1 prefix, 2-3 prefixes OR'd)? Throwaway db on the TEST store :18000, removed at the end."""
import asyncio, sys, uuid
sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/loremaster/tests")
from _governed_contract import index_served, scans_table, operators  # noqa: E402
from surrealdb import AsyncSurreal  # noqa: E402
DB = f"sdk3r3f9_{uuid.uuid4().hex[:10]}"
async def main():
    c = AsyncSurreal("ws://127.0.0.1:18000/rpc"); await c.signin({"username": "root", "password": "spikeroot"})
    await c.use("lore_test", DB)
    try:
        await c.query_raw("DEFINE TABLE name SCHEMAFULL; DEFINE FIELD value ON name TYPE string; DEFINE INDEX name_value ON name FIELDS value;")
        for i in range(300):
            await c.query_raw("CREATE name SET value = $v", {"v": f"pkg.m{i%30}.sym{i}"})
        await c.query_raw("CREATE name SET value = 'pkg.café.widget'; CREATE name SET value = 'pkg.cafés.other';")
        shapes = {
            "sw1": ("SELECT VALUE id FROM name WHERE string::starts_with(value, $a)", {"a": "pkg.m1."}),
            "sw2": ("SELECT VALUE id FROM name WHERE string::starts_with(value, $a) OR string::starts_with(value, $b)", {"a": "pkg.m1.", "b": "pkg.m2."}),
            "sw3": ("SELECT VALUE id FROM name WHERE string::starts_with(value, $a) OR string::starts_with(value, $b) OR string::starts_with(value, $c)", {"a": "pkg.m1.", "b": "pkg.m2.", "c": "pkg.café."}),
            "range2": ("SELECT VALUE id FROM name WHERE (value >= $a AND value < $ah) OR (value >= $b AND value < $bh)", {"a": "pkg.m1.", "ah": "pkg.m1/", "b": "pkg.m2.", "bh": "pkg.m2/"}),
            "control_lower": ("SELECT VALUE id FROM name WHERE string::starts_with(string::lowercase(value), $a)", {"a": "pkg.m1."}),
        }
        for label, (sql, params) in shapes.items():
            plan = (await c.query_raw(sql + " EXPLAIN", params))["result"][0]["result"]
            rows = (await c.query_raw(sql, params))["result"][0]["result"]
            print(f"{label}: index_served={index_served(plan, 'name_value')} tablescan={scans_table(plan, 'name')} rows={len(rows)} ops={operators(plan)}")
    finally:
        await c.query_raw(f"REMOVE DATABASE IF EXISTS {DB}"); await c.close()
asyncio.run(main())
```

### `probe_slow_write.py`
```python
"""Does a single-statement write with an embedded sleep() take the sleep and commit? (TEST store)"""
import asyncio, time, uuid
from surrealdb import AsyncSurreal
DB = f"sdk3r3sw_{uuid.uuid4().hex[:8]}"
async def main():
    c = AsyncSurreal("ws://127.0.0.1:18000/rpc"); await c.signin({"username": "root", "password": "spikeroot"}); await c.use("lore_test", DB)
    try:
        t = time.monotonic(); r = await c.query_raw("CREATE probe:a SET n = 1, slow = sleep(2s)"); print("create+sleep", round(time.monotonic()-t, 2), r["result"][0]["status"])
        t = time.monotonic(); r = await c.query_raw("BEGIN; CREATE probe:b SET n = 2; LET $w = sleep(2s); COMMIT;"); print("txn+sleep", round(time.monotonic()-t, 2), [e["status"] for e in r["result"]])
        print((await c.query_raw("SELECT VALUE id FROM probe"))["result"][0]["result"])
    finally:
        await c.query_raw(f"REMOVE DATABASE {DB}"); await c.close()
asyncio.run(main())
```

### `probe_f8_query.py`
```python
"""Validate the lead's F8 read-only count statement on a THROWAWAY TEST-store db (:18000) with controls:
one bracketed value per bracket style in some fields, bare values elsewhere; tables left undeclared
where lore would have them declared is NOT modelled — every table is created SCHEMALESS here."""
import asyncio, sys, uuid
from surrealdb import AsyncSurreal
DB = f"sdk3r3f8_{uuid.uuid4().hex[:8]}"
async def main():
    c = AsyncSurreal("ws://127.0.0.1:18000/rpc"); await c.signin({"username": "root", "password": "spikeroot"}); await c.use("lore_test", DB)
    try:
        for t in ("agent", "memory", "message", "audit", "task", "file"):
            await c.query_raw(f"DEFINE TABLE {t} SCHEMALESS")
        await c.query_raw("CREATE agent SET scope = 'keep:01JCX'; CREATE agent SET scope = 'keep:⟨01JCX⟩'; CREATE agent SET task_id = NONE;")
        await c.query_raw("CREATE message SET refs = ['task:abc', 'task:`0199-x`']; CREATE message SET refs = [];")
        await c.query_raw("CREATE audit SET target_row = 'memory:abc', actor_email = 'p1'")
        out = await c.query_raw(open(sys.argv[1]).read())
        print(out["result"][-1]["status"], out["result"][-1]["result"])
    finally:
        await c.query_raw(f"REMOVE DATABASE {DB}"); await c.close()
asyncio.run(main())
```

### `f8_counts.surql` = the statement in §R3.7(a)

### `run_mutations.sh` (declared reds: one node id per line in `mut/<name>.expect`, from `--collect-only`, written before the run)
```bash
#!/usr/bin/env bash
# SDK3 r3 operator-ruled mutation proofs on the reference build (R2 sharing, R4 bound pin, F9, W6).
# Declared reds: $D/mut/<name>.expect (from pytest --collect-only, written BEFORE the run).
set -u
D=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/sdk3r3
R=$D/ref
cd "$R"
~/.claude/orchestration/tree_id.sh "$R"
.venv/bin/python -c "import loremaster; print('loremaster.__file__=' + loremaster.__file__)"
PYTEST=(systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python -m pytest -q -rfE -p no:cacheprovider --timeout=300 -n 8)
run() { # name file tests...
  local name=$1 file=$2; shift 2
  local expects=(); while read -r id; do expects+=(--expect-red "$id"); done < "$D/mut/$name.expect"
  echo "=== MUTATION $name on $file"
  .venv/bin/python scripts/mutation_proof.py --file "$file" --anchor-file "$D/mut/$name.anchor" --replacement-file "$D/mut/$name.repl" "${expects[@]}" -- "${PYTEST[@]}" "$@"
  echo "MUTATION_EXIT $name=$?"
}
run r2 loremaster/loremaster/store/_txn.py loremaster/tests/test_sdk3_result_shapes.py loremaster/tests/test_sdk3_single_statement_seam.py
run r4 loremaster/loremaster/store/surreal.py loremaster/tests/test_sdk3_index_batching.py
run f9 loremaster/loremaster/graph_surreal.py loremaster/tests/test_sdk3_native_shapes.py
run w6 loremaster/loremaster/store/_txn.py loremaster/tests/test_sdk3_workaround_retirement.py loremaster/tests/test_sdk3_txn_classification.py
git -C "$R" diff --stat | tail -1
```

Mutation anchors → replacements (each matched exactly once):
- **M-r2**: `return results[0]` → ` return results `
- **M-r4**: `statements.append(f"INSERT INTO {CHUNK_TABLE} ${rows_param}")` → ` for index, row in enumerate(rows): params[f"{rows_param}{index}"] = [row] statements.append(f"INSERT INTO {CHUNK_TABLE} ${rows_param}{index}") `
- **M-f9**: `conditions.append(f"string::starts_with({_COL_VALUE}, ${key})")` → ` conditions.append(f"string::starts_with(string::lowercase({_COL_VALUE}), ${key})") `
- **M-w6**: `return isinstance(error, QueryError) and error.is_transaction_conflict` → ` return False `

### Offline breakdown output (`probe_r3_compose_breakdown.py loremaster/tests/test_comms_tool.py 4`, 2026-11-07, HEAD `b03c4fc`)
```
file=loremaster/tests/test_comms_tool.py chunks=511 source_bytes=423315 divisor=4
composed statements=5113 (production measured 5,113 for test_comms_tool.py) cap=5000
  producer chunk: 512
  producer file_text: 1
  producer manifest: 2
  producer graph: 4598
    chunk     UPSERT   chunk                  511
    chunk     DELETE   chunk                  1
    file_text UPSERT   file_text              1
    graph     RELATE   refers                 1858
    graph     UPSERT   name                   1204
    graph     RELATE   answers_to             1022
    graph     CREATE   code_node              511
    graph     DELETE   code_node              1
    graph     DELETE   refers                 1
    graph     DELETE   answers_to             1
    manifest  DELETE   file                   1
    manifest  CREATE   file                   1
compose: REFUSED SurrealStoreError: composed transaction has 5113 statements, exceeding the hard cap of 5000 statements per transaction — refused before anything was sent to the server
  params chunk: 1024 repr_bytes=3424677
  params file_text: 2 repr_bytes=433128
  params manifest: 8 repr_bytes=20843
  params graph: 13419 repr_bytes=1355523
```

### F9 probe output (3.3.5 TEST store)
```
sw1: index_served=True tablescan=False rows=10 ops=['ProjectValue', 'Filter', 'IndexScan']
sw2: index_served=True tablescan=False rows=20 ops=['ProjectValue', 'Filter', 'BitmapResolve', 'BitmapOr', 'BitmapIndexScan', 'BitmapIndexScan']
sw3: index_served=True tablescan=False rows=21 ops=['ProjectValue', 'Filter', 'BitmapResolve', 'BitmapOr', 'BitmapIndexScan', 'BitmapIndexScan', 'BitmapIndexScan']
range2: index_served=True tablescan=False rows=20 ops=['ProjectValue', 'Filter', 'BitmapResolve', 'BitmapOr', 'BitmapIndexScan', 'BitmapIndexScan']
control_lower: index_served=False tablescan=True rows=10 ops=['ProjectValue', 'TableScan']
```

## Appendix E — round-4 instruments (verbatim)

### `census_unknown.py` (run from `loremaster/tests` with the scratch tree's interpreter; the D1/F18 census of §R4.5)
```python
"""Census: production catch sites reachable by SurrealOutcomeUnknownError (unshielded), via the ONE walker."""
import sys, ast
sys.path.insert(0, ".")
from _catch_sites import production_catch_sites
from loremaster.store._txn import SurrealOutcomeUnknownError as U, SurrealConnectionError as C
sites = production_catch_sites()
named, broad = [], []
for s in sites:
    reach = any(issubclass(U, c) for c in s.caught)
    shield = any(issubclass(U, c) for c in s.earlier)
    if not reach or shield:
        continue
    explicit = any(c in (U, C) or issubclass(c, C) for c in s.caught)
    body = s.handler.body if s.handler else []
    passthrough = bool(body) and len(body) == 1 and isinstance(body[0], ast.Raise) and body[0].exc is None
    (named if explicit else broad).append((s.key, s.lineno, [c.__name__ for c in s.caught], "PASS" if passthrough else "RENDER/OTHER"))
print(f"sites_total={len(sites)} reachable_named={len(named)} reachable_broad={len(broad)}")
for r in named: print("NAMED", *r)
from collections import Counter
print("BROAD by caught:", Counter(tuple(r[2]) for r in broad).most_common())
print("BROAD passthrough:", sum(1 for r in broad if r[3]=="PASS"))
print("---- SurrealStoreError-family broad sites")
for r in broad:
    if "SurrealStoreError" in r[2] or "PrincipalStoreError" in r[2]:
        print(*r)
```

### `run_mutations.sh` (declared reds: `mut/<name>.expect`, one node id per line from `--collect-only`, written before the run; anchors/replacements in §R4.10)
```bash
#!/usr/bin/env bash
# SDK3 r4 mutation proofs on the round-4 reference build. Declared reds: $M/<name>.expect (from
# pytest --collect-only, written BEFORE the run); anchor/replacement/file/tests beside it.
set -u
R=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/sdk3r4
M=$R/mut; B=$R/ref
cd "$B"
~/.claude/orchestration/tree_id.sh "$B"
.venv/bin/python -c "import importlib.metadata as m, loremaster; print('loremaster.__file__=' + loremaster.__file__, 'surrealdb=' + m.version('surrealdb'))"
PYTEST=(systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python -m pytest -q -rfE -p no:cacheprovider --timeout=400 -n 8)
for name in "$@"; do
  expects=(); while read -r id; do expects+=(--expect-red "$id"); done < "$M/$name.expect"
  echo "=== MUTATION $name on $(cat $M/$name.file)"
  .venv/bin/python scripts/mutation_proof.py --file "$(cat $M/$name.file)" --anchor-file "$M/$name.anchor" --replacement-file "$M/$name.repl" "${expects[@]}" -- "${PYTEST[@]}" $(cat $M/$name.tests)
  echo "MUTATION_EXIT $name=$?"
done
echo "--- tree after (must be clean vs pre-run):"; git -C "$B" diff --stat | tail -1
```

## Appendix F — round-5 instruments (verbatim; run with the SDK under test)

### `probe_engine_text.py` (engine `<string>` vs SDK `str(RecordID)`, run from `loremaster/tests`)

```python
"""Probe: the engine's <string> form of record ids with lore's key shapes (TEST store only)."""
import asyncio, sys
sys.path.insert(0, ".")
from _surreal_harness import make_env, unique_database, connect_admin, drop_database, run, PRODUCTION_DIM
from surrealdb import RecordID
import importlib.metadata as md
KEYS = ["01JCXZ3Q9V8M2T5K7R4N6P1W0Y", "9c9operator0000000000", "c9-op.erator", "7ghostsender", "z0ysb7r5es9z0ysb7r5e", "1234"]
async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    assert ":18000" in env.url, env.url
    conn = await connect_admin(env)
    try:
        for key in KEYS:
            rid = RecordID("t", key)
            await run(conn, "CREATE $id", {"id": rid})
            text = await run(conn, "RETURN <string> $id", {"id": rid})
            print(f"sdk={md.version('surrealdb')} key={key!r} engine={text!r} sdk_str={str(rid)!r}")
    finally:
        await conn.close(); await drop_database(env)
asyncio.run(main())
```

### `probe_array_key.py`

```python
"""Probe: SDK str() vs engine <string> for an ARRAY record key (code_node shape), TEST store only."""
import asyncio, sys, importlib.metadata as md
sys.path.insert(0, ".")
from _surreal_harness import make_env, unique_database, connect_admin, drop_database, run, PRODUCTION_DIM
from surrealdb import RecordID
async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM); assert ":18000" in env.url
    conn = await connect_admin(env)
    try:
        for key in (["custom", "src/a.py", "mod.func"], ["custom", "9dir/x-y.py", "Q"]):
            rid = RecordID("code_node", key)
            await conn.query("CREATE $id", {"id": rid})
            text = await run(conn, "RETURN <string> $id", {"id": rid})
            print(f"sdk={md.version('surrealdb')} engine={text!r} sdk_str={str(rid)!r} same={text == str(rid)}")
    finally:
        await conn.close(); await drop_database(env)
asyncio.run(main())
```

### `probe_notallowed.py` (F-b: what an anonymous write raises)

```python
"""Probe: what an UNAUTHENTICATED connection's query raises (TEST store :18000 only), per SDK."""
import asyncio, sys, importlib.metadata as md
sys.path.insert(0, ".")
from _surreal_harness import make_env, unique_database, connect_admin, drop_database, PRODUCTION_DIM
from surrealdb import AsyncSurreal
async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    assert ":18000" in env.url
    admin = await connect_admin(env); await admin.close()
    conn = AsyncSurreal(env.url)
    await conn.connect()
    try:
        try:
            await conn.use(env.namespace, env.database)
            print("use ok")
        except Exception as e:
            print("use raised", type(e).__mro__[:4], e)
        for stmt in ("SELECT * FROM t", "CREATE t:1"):
            try:
                r = await conn.query(stmt); print(stmt, "->", r)
            except Exception as e:
                print(f"sdk={md.version('surrealdb')} {stmt} raised", [c.__name__ for c in type(e).__mro__[:5]], str(e)[:120])
    finally:
        await conn.close(); await drop_database(env)
asyncio.run(main())
```

### `extract_handlers.py` (the 39 broad spans)

```python
"""Print each listed except-handler's source (first 14 lines) from the reference tree. Args: root tsv"""
import ast, sys
from pathlib import Path
root = Path(sys.argv[1]); rows = [l.split("\t") for l in Path(sys.argv[2]).read_text().splitlines() if l.strip()]
opened = 0
for row in rows:
    key, line = row[0], int(row[1])
    rel = key.split("::")[0]
    src = (root / rel).read_text(); tree = ast.parse(src); opened += 1
    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.lineno == line:
            found = node
        if isinstance(node, ast.Try) and found is None:
            for fb in node.finalbody:
                pass
    if found is None:
        seg = "\n".join(src.splitlines()[line-1:line+8])
    else:
        seg = ast.get_source_segment(src, found) or ""
    lines = seg.splitlines()
    print(f"### {key}:{line} [{row[2]}]")
    print("\n".join(lines[:14]) + ("\n   …" if len(lines) > 14 else ""))
print(f"COVERAGE rows={len(rows)} files_opened={opened}", file=sys.stderr)
```

### `build_ref_r5b.py` (reference deltas: F18, C9 siblings, C4)

```python
"""SDK3 round-5 (r5b) REFERENCE deltas over the r5a reference (= r4 reference + C9 fix).

A satisfiability instrument, never the build. Every replacement asserts it matched exactly once, so a
re-run on an already-patched tree fails loud instead of silently no-opping.
usage: build_ref_r5b.py <ref-root> <group>   groups: f18 | c9sib | c4 | tenacity | all
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
GROUP = sys.argv[2]
PKG = ROOT / "loremaster" / "loremaster"


def patch(relative: str, old: str, new: str) -> None:
    path = PKG / relative
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    assert count == 1, f"{relative}: anchor matched {count}x: {old[:80]!r}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def f18() -> None:
    # briefs.BriefLedger.publish: an UNKNOWN outcome never releases the minted version (D1/F18).
    patch(
        "briefs.py",
        "        try:\n            await self._apply([fragment])\n        except SurrealStoreError:\n",
        "        try:\n            await self._apply([fragment])\n"
        "        except SurrealOutcomeUnknownError:\n"
        "            # F18/D1: the CREATE may have COMMITTED — releasing would re-mint this version.\n"
        "            raise\n"
        "        except SurrealStoreError:\n",
    )
    patch(
        "briefs.py",
        "    SurrealConnectionError,\n    SurrealStoreError,\n    TxnContentionExhaustedError,\n",
        "    SurrealConnectionError,\n    SurrealOutcomeUnknownError,\n    SurrealStoreError,\n"
        "    TxnContentionExhaustedError,\n",
    )
    # indexer: an UNKNOWN apply outcome is VERIFIED against the manifest before anything is marked failed.
    verify = (
        "        except SurrealStoreError as store_error:\n"
        "            from loremaster.store._txn import TxnRowCapExceededError  # noqa: PLC0415\n"
        "\n"
        "            if await self._landed_after_unknown(\n"
        "                store_error, tier={tier}, path={path}, content_hash={hash}, new_ids={ids}\n"
        "            ):\n"
        "                return IndexOutcome(\n"
        "                    tier={tier}, file_path={path}, state=STATE_INDEXED, n_chunks=len({records})\n"
        "                )\n"
    )
    old = (
        "        except SurrealStoreError as store_error:\n"
        "            from loremaster.store._txn import TxnRowCapExceededError  # noqa: PLC0415\n"
        "\n"
        "            refused_reason = (\n"
        "                f\"{_FAILED_STORE_REASON}: {store_error}\"\n"
        "                if isinstance(store_error, TxnRowCapExceededError)\n"
        "                else _FAILED_STORE_REASON\n"
        "            )\n"
        "            logger.warning(\n"
        "                \"index.file.store_failed\",\n"
        "                extra={\"tier\": tier,"
    )
    patch(
        "index/indexer.py",
        old,
        verify.format(tier="tier", path="path", hash="content_hash", ids="new_ids", records="records")
        + old.split("\n", 2)[2],
    )
    old_batch = (
        "        except SurrealStoreError as store_error:\n"
        "            from loremaster.store._txn import TxnRowCapExceededError  # noqa: PLC0415\n"
        "\n"
        "            refused_reason = (\n"
        "                f\"{_FAILED_STORE_REASON}: {store_error}\"\n"
        "                if isinstance(store_error, TxnRowCapExceededError)\n"
        "                else _FAILED_STORE_REASON\n"
        "            )\n"
        "            logger.warning(\n"
        "                \"index.file.store_failed\",\n"
        "                extra={\n"
    )
    patch(
        "index/indexer.py",
        old_batch,
        verify.format(
            tier="pf.tier", path="pf.path", hash="pf.content_hash", ids="pf.new_ids", records="pf.records"
        )
        + old_batch.split("\n", 2)[2],
    )
    patch(
        "index/indexer.py",
        "    async def _mark_file_failed(\n",
        "    async def _landed_after_unknown(\n"
        "        self, error: BaseException, *, tier: str, path: str, content_hash: str, new_ids: list[str]\n"
        "    ) -> bool:\n"
        "        \"\"\"F18/D1: after an OUTCOME-UNKNOWN apply, read the manifest back — True iff the commit landed.\"\"\"\n"
        "        from loremaster.store._txn import SurrealOutcomeUnknownError  # noqa: PLC0415\n"
        "\n"
        "        if not isinstance(error, SurrealOutcomeUnknownError):\n"
        "            return False\n"
        "        row = await self._manifest.get(tier, path)\n"
        "        return (\n"
        "            row is not None\n"
        "            and row.state == STATE_INDEXED\n"
        "            and row.sha512 == content_hash\n"
        "            and list(row.chunk_ids) == list(new_ids)\n"
        "        )\n"
        "\n"
        "    async def _mark_file_failed(\n",
    )
    # calibration: an unknown filing outcome is served as UNKNOWN, never "filing failed".
    patch(
        "calibration/engine.py",
        "        try:\n            await self._report_drift(live_total, baseline_total, ratio_shift, served)\n"
        "            return None\n",
        "        from loremaster.store._txn import SurrealOutcomeUnknownError  # noqa: PLC0415\n\n"
        "        try:\n            await self._report_drift(live_total, baseline_total, ratio_shift, served)\n"
        "            return None\n"
        "        except SurrealOutcomeUnknownError as exc:\n"
        "            logger.error(\"calibration drift finding outcome unknown\", exc_info=True)\n"
        "            return (\n"
        "                f\"drift finding outcome UNKNOWN (the write was sent; no answer came) — verify with \"\n"
        "                f\"lore_findings before re-filing: {exc}\"\n"
        "            )\n",
    )


def c9_siblings() -> None:
    # governed._bare: a record id's KEY from its parts, never a split of its rendered text.
    patch(
        "governed.py",
        "    text = str(record_id)\n    return text.split(\":\", 1)[-1] if \":\" in text else text\n",
        "    key = getattr(record_id, \"id\", None)\n"
        "    if key is not None and getattr(record_id, \"table_name\", None) is not None:\n"
        "        return str(key)\n"
        "    text = str(record_id)\n    return text.split(\":\", 1)[-1] if \":\" in text else text\n",
    )
    # principals: the dangling-sender refusal serves the engine's text for each id.
    patch(
        "principals.py",
        "            f\"{sanitise_line(str(message_id))} (sender {sanitise_line(str(sender))})\"\n",
        "            f\"{sanitise_line(record_text(message_id))} (sender {sanitise_line(record_text(sender))})\"\n",
    )
    # memory/local: the replay close compares the predecessor's owner KEYS, not split rendered text.
    for column in ("stored_owner_principal", "stored_owner_agent"):
        patch(
            "memory/local.py",
            f"            {column} = getattr({column}, \"record_id\", None) or (\n"
            f"                str({column}).split(\":\")[-1]\n"
            f"                if {column} is not None\n"
            f"                else None\n"
            f"            )\n",
            f"            {column} = (\n"
            f"                None if {column} is None\n"
            f"                else str(getattr({column}, \"id\", None) or str({column}).split(\":\")[-1])\n"
            f"            )\n",
        )


def c4() -> None:
    patch(
        "audit.py",
        "        return str(RecordID(AUDIT_TABLE, record_id))\n",
        "        return record_text(RecordID(AUDIT_TABLE, record_id))\n",
    )
    audit = PKG / "audit.py"
    text = audit.read_text(encoding="utf-8")
    if "record_text" not in text.split("class AuditStoreError")[0]:
        patch("audit.py", "class AuditStoreError(", "from loremaster.store._txn import record_text  # noqa: E402\n\n\nclass AuditStoreError(")


GROUPS = {"f18": [f18], "c9sib": [c9_siblings], "c4": [c4]}
GROUPS["all"] = [f18, c9_siblings, c4]
for step in GROUPS[GROUP]:
    step()
print(f"applied {GROUP}")
```

### `build_ref_r5b_tenacity.py` (reference delta: R11/F22)

```python
"""SDK3 r5b REFERENCE delta, R11 (+F22): retry_on_conflict on tenacity; the ONE jitter source delegates to
loresigil.backoff (tenacity wait_random_exponential); scout's connect ladder on tenacity. Satisfiability instrument
only. usage: build_ref_r5b_tenacity.py <ref-root>"""
import sys
from pathlib import Path
PKG = Path(sys.argv[1]) / "loremaster" / "loremaster"
def patch(relative, old, new):
    path = PKG / relative; text = path.read_text(encoding="utf-8"); n = text.count(old)
    assert n == 1, f"{relative}: anchor matched {n}x: {old[:90]!r}"
    path.write_text(text.replace(old, new), encoding="utf-8")
# -- the ONE conflict-jitter source: delegate, no private draw (F22) --------------------------------
patch("store/_txn.py",
"""    window = min(
        _TXN_CONFLICT_BACKOFF_CAP_SECONDS,
        _TXN_CONFLICT_BACKOFF_BASE_SECONDS * (2 ** (attempt_number - 1)),
    )
    return random.uniform(0, window)
""",
"""    # R11/F22: the draw is tenacity's wait_random_exponential through the workspace's ONE policy.
    return backoff.jittered_backoff_delay(
        attempt_number - 1,
        base_s=_TXN_CONFLICT_BACKOFF_BASE_SECONDS,
        cap_s=_TXN_CONFLICT_BACKOFF_CAP_SECONDS,
    )


def _conflict_wait(retry_state: RetryCallState) -> float:
    \"\"\"tenacity ``wait=``: the seam's ONE jitter source, looked up at CALL time (pins patch it).\"\"\"
    return _txn_conflict_backoff_seconds(retry_state.attempt_number)


async def _conflict_sleep(seconds: float) -> None:
    \"\"\"tenacity ``sleep=``: ``asyncio.sleep`` looked up at CALL time (pins silence it).\"\"\"
    await asyncio.sleep(seconds)
""")
patch("store/_txn.py", "import random\n",
      "from loresigil import backoff\nfrom tenacity import (\n    AsyncRetrying,\n    RetryCallState,\n    RetryError,\n"
      "    retry_if_exception_type,\n    stop_after_attempt,\n    stop_after_delay,\n    stop_all,\n    stop_any,\n)\n")
# -- retry_on_conflict on tenacity AsyncRetrying ---------------------------------------------------
old_loop_start = "    last_conflict_cause: BaseException | None = None\n    while True:\n        try:\n            return await attempt()\n        except RetryableConflictSignal as signal:\n            last_conflict_cause = signal.__cause__\n        attempts += 1\n        elapsed = time.monotonic() - started\n"
new_loop_start = """    retrying = AsyncRetrying(
        stop=stop_any(
            stop_after_attempt(_TXN_CONFLICT_ATTEMPT_CEILING),
            stop_all(stop_after_delay(deadline), stop_after_attempt(_MAX_TXN_CONFLICT_ATTEMPTS)),
        ),
        wait=_conflict_wait,
        retry=retry_if_exception_type(RetryableConflictSignal),
        sleep=_conflict_sleep,
    )
    try:
        return await retrying(attempt)
    except RetryError as exhausted:
        attempts = exhausted.last_attempt.attempt_number
        final_signal = exhausted.last_attempt.exception()
        last_conflict_cause = final_signal.__cause__ if final_signal is not None else None
    elapsed = time.monotonic() - started
    if True:  # the exhaustion disposition (X22/X23) — tenacity's RetryError is translated, never leaked
"""
patch("store/_txn.py", old_loop_start, new_loop_start)
patch("store/_txn.py", "    started = time.monotonic()\n    attempts = 0\n", "    started = time.monotonic()\n")
patch("store/_txn.py",
"""                attempts=attempts,
                elapsed_seconds=elapsed,
            )
        await asyncio.sleep(_txn_conflict_backoff_seconds(attempts))
""",
"""                attempts=attempts,
                elapsed_seconds=elapsed,
            ) from None
""")
# -- scout: the connect half of the reconnect ladder on tenacity -----------------------------------
patch("scout.py",
"""                try:
                    connection = await self._ensure_connection()
                except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION:
                    # The connect itself failed — back off (bounded) and retry.
                    logger.debug("command_subscriber.connect_failed", exc_info=True)
                    await self._backoff(attempt)
                    attempt += 1
                    continue
                attempt = 0  # a live connection resets the backoff ladder
""",
"""                try:
                    connection = await self._connect_with_backoff(attempt)
                except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION:
                    break  # stopped while the store was unreachable
                attempt = 0  # a live connection resets the backoff ladder
""")
patch("scout.py",
"""    async def _backoff(self, attempt: int) -> None:
""",
"""    async def _connect_with_backoff(self, first_attempt: int) -> Any:
        \"\"\"R11: connect, retrying a failed connect on tenacity with the shared full-jitter policy.\"\"\"

        def _wait(retry_state: RetryCallState) -> float:
            logger.debug("command_subscriber.connect_failed")
            return self._backoff_delay(first_attempt + retry_state.attempt_number - 1)

        retrying = AsyncRetrying(
            retry=retry_if_exception_type(_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION),
            wait=_wait,
            sleep=self._sleep,
            stop=lambda _state: not self._running,
            reraise=True,
        )
        return await retrying(self._ensure_connection)

    def _backoff_delay(self, attempt: int) -> float:
        \"\"\"The shared policy's draw for a zero-based ``attempt`` (finding #207).\"\"\"
        return backoff.jittered_backoff_delay(
            attempt, base_s=self._backoff_base_s, cap_s=self._max_backoff_s
        )

    async def _backoff(self, attempt: int) -> None:
""")
patch("scout.py",
"""        delay = backoff.jittered_backoff_delay(
            attempt, base_s=self._backoff_base_s, cap_s=self._max_backoff_s
        )
        await self._sleep(delay)
""",
"""        await self._sleep(self._backoff_delay(attempt))
""")
text = (PKG / "scout.py").read_text()
anchor = "from loresigil import backoff\n"
assert text.count(anchor) == 1, "scout backoff import"
(PKG / "scout.py").write_text(text.replace(anchor, anchor + "from tenacity import AsyncRetrying, RetryCallState, retry_if_exception_type\n"))
print("applied tenacity")
```

### `run_mutations.sh` (16 proofs; specs in `scratchpad/sdk3r5/mut/<name>.{file,anchor,repl,tests,pattern,expect}`)

```bash
#!/usr/bin/env bash
# SDK3 r5b mutation proofs on the round-5 (r5b) reference. Declared reds: $M/<name>.expect (pytest --collect-only,
# filtered by $M/<name>.pattern, written BEFORE the run); anchor/replacement/file/tests beside it.
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/sdk3r5
M=$S/mut; B=$S/ref
cd "$B"
~/.claude/orchestration/tree_id.sh "$B"
.venv/bin/python -c "import importlib.metadata as m, loremaster; print('loremaster.__file__=' + loremaster.__file__, 'surrealdb=' + m.version('surrealdb'))" 2>&1 | grep -v Warning
PYTEST=(systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python -m pytest -q -rfE -p no:cacheprovider --timeout=400 -n 6)
for name in "$@"; do
  expects=(); while read -r id; do expects+=(--expect-red "$id"); done < "$M/$name.expect"
  echo "=== MUTATION $name on $(cat $M/$name.file) (declared ${#expects[@]})"
  .venv/bin/python scripts/mutation_proof.py --file "$(cat $M/$name.file)" --anchor-file "$M/$name.anchor" --replacement-file "$M/$name.repl" "${expects[@]}" -- "${PYTEST[@]}" $(cat $M/$name.tests) 2>&1 | grep -v 'RuntimeWarning\|frozen site' | tail -12
  echo "MUTATION_EXIT $name=${PIPESTATUS[0]}"
done
echo "--- prod tree vs pre-run content backup (must be empty):"
for d in loremaster/loremaster lorerunes/lorerunes loresigil/loresigil lorescribe/lorescribe; do diff -rq --exclude=__pycache__ "$B/$d" "$S/ref_prod_r5b/$d"; done
echo "BACKUP_DIFF_DONE"
```

### `attribute.sh` (satisfiability attribution)

```bash
#!/usr/bin/env bash
# r5b attribution: FAILED/ERROR node ids on the r5b reference vs the r4 baseline (SAME test tree, r4 production) vs HEAD.
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/sdk3r5
ids() { grep -E '^(FAILED|ERROR) ' "$1" | sed -E 's/^(FAILED|ERROR) //; s/ - .*//' | sort -u; }
ids $S/logs/r5_target_ref.log > $S/red_ref.ids; ids $S/logs/r5_target_base_r4.log > $S/red_base.ids; ids $S/logs/r5_target_head.log > $S/red_head.ids
echo "red: ref=$(wc -l < $S/red_ref.ids) base_r4=$(wc -l < $S/red_base.ids) head=$(wc -l < $S/red_head.ids)"
echo "== red on r5b ref, NOT on r4 baseline (candidates; HEAD state after each):"
comm -23 $S/red_ref.ids $S/red_base.ids | while read id; do if grep -qxF "$id" $S/red_head.ids; then h=RED; else h=green; fi; echo "$id  [HEAD $h]"; done
echo "== red on r4 baseline, fixed on r5b ref: $(comm -13 $S/red_ref.ids $S/red_base.ids | wc -l)"
comm -13 $S/red_ref.ids $S/red_base.ids | awk -F'::' '{print $1}' | sort | uniq -c
```

## Appendix G — round-6 instruments (verbatim)

Every load-bearing round-6 measurement was made with these. Paths are the session scratchpad named in the brief.

### `scratchpad/sdk3r6/tools/wrap_query_returns.py`
```
"""Round-6 instrument (F-a reach): wrap every `return <expr>` of every `async def query(...)` in a test file in
`one_statement_answer(<expr>)` (skipping returns already wrapped). Prints each site; --dry to only list."""
import ast, sys
path = sys.argv[1]; dry = "--dry" in sys.argv
src = open(path).read(); lines = src.splitlines(keepends=True)
tree = ast.parse(src)
sites = []
class V(ast.NodeVisitor):
    def visit_AsyncFunctionDef(self, node):
        if node.name == "query":
            for sub in self._returns(node):
                v = sub.value
                if v is None:
                    sites.append((sub.lineno, sub.col_offset, None, None, None, None)); continue
                if isinstance(v, ast.Call) and getattr(v.func, "id", None) == "one_statement_answer":
                    continue
                sites.append((sub.lineno, sub.col_offset, v.lineno, v.col_offset, v.end_lineno, v.end_col_offset))
        self.generic_visit(node)
    def _returns(self, fn):
        out = []
        def walk(n):
            for c in ast.iter_child_nodes(n):
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                if isinstance(c, ast.Return):
                    out.append(c)
                walk(c)
        walk(fn); return out
V().visit(tree)
# apply bottom-up
offs = [0]
for l in lines: offs.append(offs[-1] + len(l))
def pos(lineno, col): return offs[lineno - 1] + len(lines[lineno - 1].encode()[:col].decode())
for (rl, rc, vl, vc, el, ec) in sorted(sites, reverse=True):
    print(f"{path}:{rl}: {lines[rl-1].strip()[:100]}")
    if dry: continue
    if vl is None:
        a = pos(rl, rc); seg = src[a:a+6]; assert seg == "return", seg
        src = src[:a] + "return one_statement_answer(None)" + src[a+6:]
    else:
        a = pos(vl, vc); b = pos(el, ec)
        src = src[:a] + "one_statement_answer(" + src[a:b] + ")" + src[b:]
if not dry: open(path, "w").write(src)
print(f"sites={len(sites)}")
```

### `scratchpad/sdk3r6/sync_tests.sh`
```
#!/usr/bin/env bash
# Sync the main tree's test tree into the r6 reference (the C10 harness + _sdk_guard stay the reference's own).
set -euo pipefail
R=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/sdk3r6
rsync -a --delete --exclude='__pycache__/' --exclude='_surreal_harness.py' --exclude='_sdk_guard.py' /home/ejprice/PycharmProjects/lore/loremaster/tests/ $R/ref/loremaster/tests/
```

### `scratchpad/sdk3r6/run_ref.sh`
```
#!/usr/bin/env bash
# usage: run.sh <build-dir> <log-path> <timeout-seconds> <nworkers> <pytest args...>
# pytest INSIDE the build's own venv under the lore cgroup cap; header = tree_id + provenance; EXIT= last.
set -u
B="$1"; LOG="$2"; TO="$3"; NW="$4"; shift 4
{
  ~/.claude/orchestration/tree_id.sh "$B"
  "$B/.venv/bin/python" -c "import importlib.metadata as m, loremaster; print('loremaster.__file__=' + loremaster.__file__, 'surrealdb=' + m.version('surrealdb'))"
  cd "$B" && systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    "$B/.venv/bin/python" -m pytest -q -rfE -p no:cacheprovider --timeout="$TO" -n "$NW" "$@"
  echo "EXIT=$?"
} > "$LOG" 2>&1
tail -1 "$LOG"; grep -E '[0-9]+ (passed|failed|error)' "$LOG" | tail -1
```

### `scratchpad/sdk3r6/run_head.sh`
```
#!/usr/bin/env bash
# usage: run_head.sh <log-path> <timeout-seconds> <nworkers> <pytest args...>  (main checkout, SDK 2.0.0)
set -u
B=/home/ejprice/PycharmProjects/lore; LOG="$1"; TO="$2"; NW="$3"; shift 3
{
  ~/.claude/orchestration/tree_id.sh "$B"
  cd "$B" && uv run python -c "import importlib.metadata as m, loremaster; print('loremaster.__file__=' + loremaster.__file__, 'surrealdb=' + m.version('surrealdb'))"
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q -rfE -p no:cacheprovider --timeout="$TO" -n "$NW" "$@"
  echo "EXIT=$?"
} > "$LOG" 2>&1
tail -1 "$LOG"; grep -E '[0-9]+ (passed|failed|error)' "$LOG" | tail -1
```

### `scratchpad/sdk3r6/loop5.sh`
```
#!/usr/bin/env bash
# 5 consecutive runs of the timing/concurrency set (T2 both paths, test_sdk3_lifecycle, MP3 x2, CF2, X19, scout CAS winner)
# on the r6 reference; stops at the first red. One log per run (tree_id + loremaster.__file__ header, EXIT= last).
R=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/sdk3r6; T=loremaster/tests
SET="$T/test_sdk3_txn_classification.py::TestARetryableConflictIsRetriedAndLosesNothing $T/test_sdk3_lifecycle.py $T/test_sdk3_connection_factory.py::TestEveryNamedLongOperationOutlivesTheDefaultTimeout $T/test_sdk3_connection_factory.py::TestALongOperationOutlivesTheDefaultTimeout $T/test_sdk3_nested_lifecycle.py::TestARecallDuringARebuildWaitsForIt $T/test_sdk3_single_statement_seam.py::TestScoutsCommandClaimHasExactlyOneWinner"
for i in 1 2 3 4 5; do
  bash $R/run_ref.sh $R/ref $R/logs/loop_$i.log 300 8 $SET > /dev/null 2>&1
  e=$(grep -E '^EXIT=' $R/logs/loop_$i.log | tail -1); c=$(grep -E '[0-9]+ (passed|failed|error)' $R/logs/loop_$i.log | tail -1)
  echo "run $i: $e | $c"
  [ "$e" = "EXIT=0" ] || { echo "STOPPED at run $i"; break; }
done
```

### Declared mutations (applied with `scripts/mutation_proof.py` in the reference; expected-RED ids taken from `--collect-only` before each run)

- **M-A** `loremaster/loremaster/index/indexer.py` — anchor:
```
        row = await self._manifest.get(tier, path)
        return (
            row is not None
            and row.state == STATE_INDEXED
            and row.sha512 == content_hash
            and list(row.chunk_ids) == list(new_ids)
        )
```
replacement:
```
        row = await self._manifest.get(tier, path)
        landed = (
            row is not None
            and row.state == STATE_INDEXED
            and row.sha512 == content_hash
            and list(row.chunk_ids) == list(new_ids)
        )
        if not landed:
            raise error  # DECLARED MUTATION M-A: an unknown that did not land propagates out of the sweep
        return landed
```
- **M-B** `loremaster/loremaster/store/_txn.py`: `        return _txn_conflict_backoff_seconds(retry_state.attempt_number)` → `… / 2 + 0.05`
- **M-B2** `loremaster/loremaster/scout.py`: `            return self._backoff_delay(first_attempt + retry_state.attempt_number - 1)` → `… / 2 + 0.01`
