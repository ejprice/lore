brief-base v25 read · brief project v7 read

# ADVERSARY3: contract-adversary round 3, packet 66 (SDK3), graded 2026-11-08

## SUMMARY BLOCK
- **State:** done-with-deviations.
- **VERDICT: CONTRACT INSUFFICIENT.** One missing pin: **MP-1**, the R4 refused-file naming pin drives only the realtime sweep, and a build that drops the bound from the batch-sweep arm passes. Bucket: PINNED PROPERTY, NEW CASE, and a REPEAT CLASS of round 2's MP-A ("both sweep shapes"). Also one RIDER GAP (R26-3), a residual and not a missing pin: the B-2 pin has no letter-led leg, so its letter-led wrong builds die only on other files' pins, one of them incidentally (residual R18).
- **P1 headline:** I ran 45 wrong builds: 18 replays and 27 new builds.
  - **Replays:** 17 of 18 are KILLED. The exception is `x18_double`, which survives as it did in round 2 (NO ROUND).
  - **R20-A3's control `wb_r11_sleepdrift`:** first real replay. KILLED by the A3 pin itself, and also by 19 A4 sharing pins.
  - **New survivors:**
    - `lm1_handloop` (landmine 1): green on 738/738 retry-file tests. **Behaviourally invisible.**
    - `b3_no_bound_batch`: **MP-1**.
    - `lm7_private_loop_capped`, `a3_floor16`, `streaming_false`: residuals, each with a receipt.
- **Runs used:** 58 pytest runs, all scoped: 45 mutation runs, 5 controls (union a/b, instrument, B3 probe, B-2) and 8 probes (streaming ×2, skip-delta ×4, untargeted-58 ×2). 0 full-contract-set runs; the P0 control is the union of every wrong-build selection (878 nodes, plus B-2's 629). Per-run list in §RECEIPTS.
- **Reference result:** reference copy `adv3/base`, TREE=4dd680c2… (= sdk3r7/ref).
  - Union control: 858 + 20 passed, 0 failed.
  - B-2 control: 629/629 passed, EXIT=0.
  - The r7 20× loop: 20/20 EXIT=0, 33 passed each, all TREE=4dd680c2…
- **Satisfiability spot-check (item 9): HOLDS.** Under a full re-parse, red@ref ∖ red@HEAD = ∅.
  - Two checker gaps in `reddiff.py` were found and closed by construction (§SATISFIABILITY): it drops 11 space-bearing ids, and it counts a skip as green. Neither hides a red.
  - Four untargeted packet-58 files read the deleted `TXN_STATEMENT_HARD_CAP`. They show identical red sets on HEAD and on the reference: 65 = 65.
- **Packages considered:**
  - tenacity 9.1.4: replace. Read `__init__.py`: `BaseRetrying._local` (threading.local) holds iter_state/statistics.
  - SDK 3.0.0 `AsyncQueryBuilder.first()`: does NOT fit C10. Read `builders.py`: `.first()` returns `None` on no statements, which is exactly the `c10_first_or_none` wrong build. So the fail-closed hand-roll is the justified gap.
  - scipy 1.18.0 `stats.kstest`: keep A3's bespoke min/max (MEDIUM: power reasoning, not run).
  - Full table in §P-PKG.
- **Odoo-20 portability:** n/a, no Odoo seam touched.
- **Reuse ledger:** none. No production symbols; probes and builds are scratch only.
- **Graded:** `150b85b` (contract tests; TREE 29c56751…) · HEAD-at-report: `3374a6b` · DIFFERENT (1 behind). Docs only: `git diff --stat 150b85b 3374a6b -- loremaster/tests loremaster/loremaster loresigil` is empty.
- **Decisions needed:**
  - (1) **Landmine 1 (operator):** adopt the proven one-line narrowing of `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES` to `{"tenacity.asyncio"}` with the build (an attribution check, so it needs operator approval), or keep it as a named cold-audit diff check. §LANDMINE 1.
  - (2) **MP-1 routing (lead):** a round-8 one-line parametrise, or a builder chokepoint requirement.
- **Pointers:** §REPLAY · §NEW BUILDS · §MISSING PINS · §LANDMINE 1 · §P1b · §P1c · §RESIDUALS · §RECEIPTS.
- **Capability check:**
  - `lore_index(reconcile=True)` hit the MCP 300 s idle timeout, although the server-side sweep finished (status read: last_sweep 3.5 s). Filed as **#582**.
  - Structure questions this run used grep, by the dogfood protocol's case (c), cross-cutting maps.
  - Every haiku-runner ran the queue script directly rather than through its runner wrapper, so there are no `RAN:`/`LOG=` lines. I verified every result from the per-build logs' own `TREE=`/`EXIT=`/count lines instead.

## ROUTING TABLE (written before the first sweep)
| step | tier | who | reason |
|---|---|---|---|
| read rulings R1–R27, RULING-2/6, r7 REPORT, ADVERSARY2 | 3 | me | the frame I grade |
| provenance assert of the reference; tree_id per tree | 1 | me inline | one command each, critical path |
| r7 loop result (20 logs) | 1 | me inline | small; read all |
| design wrong builds, anchors, declared reds | 3 | me | adversarial judgment |
| run each build (`mutation_proof.py`) and the controls | 1 | haiku-runner ×9 queues | test runs |
| killed/survived verdict per build | 3 | me | grading |
| F-a fakes vs installed SDK | 3 | me | a sampled draft would miss a shape the SDK cannot produce |
| corpse sweep (12 patterns) | 1 | me, one parallel batch | small; read all |
| short probes (skip delta, streaming mask, B3 pair, multi-statement) | 1 | me inline | seconds each, on my critical path |

Fan-out: haiku 8 · sonnet 0 · peak 4. Inline runs: 14 short scoped ones (seconds each: skip-delta ×4, untargeted-58 ×2, streaming probe ×2, B3 probe ×3, fb_txn ×1, multi-statement probe ×1, collect-only ×2).

## REPLAY (round 1 + round 2 wrong builds → round-7 contract)
**Rebase method:** each build's production diff was read from `adv/builds/*` (vs `adv/base`) and `adv2/builds/*` (vs `adv2/myref`), then re-applied by anchor to the r7 reference through `scripts/mutation_proof.py`. Anchors match exactly once, verified before the run. Content is restored md5-exact; every log's POST-RESTORE TREE equals its pre-run TREE.
- `wb_r11_sleepdrift` was re-expressed natively as `wait = edge/2 + full_jitter/2`, with edge = tenacity's own `wait_exponential`, so no `**` reaches the perimeter scan.
- `chk_a19_bare`, `chk_c10` and `wb_f12_correct` were satisfiability CHECK builds, not wrong builds. They are superseded by round 7's both-ways receipt and were not replayed.

| build (origin) | rebased mutation | killed by (observed reds) | verdict | log |
|---|---|---|---|---|
| statement-cap kept (r1 MP1) | `compose` refuses >5000 statements beside the row cap | `test_sdk3_row_bound::TestNoStatementCapSurvives` ×2 | KILLED | `wb_r1_stmtcap` (2F/7P) |
| `wb_f14_sniff` (r1) | run_query: only write-verb statements unknown | L3 read leg + read-timeout leg | KILLED | `wb_r1_f14_sniff` (2F/6P) |
| one-owner overrides (r1 MP3) | `PrincipalStore.ensure_ready` loses `ensure_ready_operation` | `TestEveryNamedLongOperationOutlivesTheDefaultTimeout` startup-DDL leg | KILLED | `wb_r1_overrides_one` (1F/1P) |
| `wb_attempts20` (r1) | `ReconnectOptions(attempts=20)` | `TestRecoveryLatencyAfterALongOutage` | KILLED | `wb_r1_attempts20` (1F) |
| `wb_attempts5` (r1) | `attempts=5` | same | KILLED | `wb_r1_attempts5` (1F) |
| `wb_guard_safe` (r1) | `_sdk_guard.SAFE_CONNECTION_METHODS` += insert/batch/relate/upsert/select | `TestTheGuardsSafeSetHoldsNoWriteCapableDoor` | KILLED | `wb_r1_guard_safe` (1F/12P) |
| `wb_batch_selector` (r1) | root cause = first failure whose TEXT lacks the cascade phrase | T6 cascade-text legs ×3 | KILLED | `wb_r1_batch_selector` (3F/7P) |
| `wb_f17_nobare` (r1) | keep lookup `StringRecordId(keep_id)` even for bare text | 12 record_ids nodes (keeper refusal ×3, round-trip ×3, any-form find, registered-agent ×4, non-word) | KILLED | `wb_r1_f17_nobare` (12F/34P) |
| `wb_mr2` (r1) | `one_statement_result` returns the SDK list | 10 (result_shapes ×4 + datetimes ×2 + LIVE wake + scout CAS + seam refusals) | KILLED | `wb_r1_mr2` (10F/4P) |
| `wb_refuse_after` (r1) | envelope refusal moved after the send | `TestTheSeamRefusesAnythingButOneStatement` ×4 | KILLED | `wb_r1_refuse_after` (1F/4E) |
| `wb_domain_unknown` (r2) | single-statement domain rejection → `SurrealOutcomeUnknownError` | `test_a_single_statement_throw_is_not_retried` (the F-b pins `TestAServerAnsweredErrorIsADefiniteFailure` ×2 stay green: they drive NotAllowed, not domain; residual R13) | KILLED | `wb_r2_domain_unknown` (1F/9P) |
| `wb_f14_timeout_definite` (r2) | a `TransportTimeoutError` raised as definite | read-timeout + write-timeout legs | KILLED | `wb_r2_f14_timeout_definite` (2F/4P) |
| `wb_f18_abort` (r2 MP-A survivor) | `_landed_after_unknown` re-raises an unknown that did not land | MP-A `[unknown-NOT-landed-batch]` + `[…-realtime]` | **KILLED (MP-A closed)** | `wb_r2_f18_abort` (2F/12P) |
| `wb_r11_sleepdrift` (r2 MP-B survivor; R20-A3 control) | `wait = w/2 + full_jitter/2` | **A3 `TestFullJitterReachesBothTailsOfTheWindow`** + 19 A4 sharing pins + factory pin (21 reds) | **KILLED (A3 control fires)** | `wb_r2_sleepdrift` (21F/716P) |
| `wb_r11_text` (r2) | `retry=` signal AND marker text | 56 (marker-move ×17, driver ×5, exhaustion ×2, …) | KILLED | `wb_r2_text` (56F/681P) |
| `wb_r11_text_or` (r2) | `retry=` signal OR marker text | 34 (old-text-stops ×17, bootstrap ×16, scout) | KILLED | `wb_r2_text_or` (34F/703P) |
| `wb_rs7_direct` (r2) | `upsert` loops `_query` per record, no cap | `TestAnUpsertBatchRidesTheRowCap` over-cap leg | KILLED | `wb_r2_rs7_direct` (1F/19P) |
| `wb_x18_double` (r2) | nested `PrincipalStore` closed twice | — | SURVIVES. NO ROUND (idempotent close, no observable effect; as round 2) | `wb_r2_x18_double` (3P) |

## NEW BUILDS (round 3)
| build | landmine | mutation | result | verdict |
|---|---|---|---|---|
| `lm1_handloop` | 1 | `retry_on_conflict` = hand `while` loop. It calls `backoff.full_jitter(...)` for its wait object and sleeps `asyncio.sleep(wait(state))` from `_txn` | **738 passed**, 0 failed (native_retry, retry_seam, retry_policy, txn_classification, backoff_seam, scout CAS) | **SURVIVES. Behaviourally invisible** (§LANDMINE 1) |
| `lm1_under_instrument` | 1 | same, against the PROPOSED narrowed instrument | 26 failed / 712 passed. The window, A3, decorrelation, A1-resolved, A4 txn, 19 seam-sharing pins and both live 16-way families go red | instrument kills it |
| (instrument control) | 1 | narrowed instrument, reference production | **738 passed**, EXIT=0 | 0 over-fire |
| `a2_never_retry_live_only` | 2 / A2 | `retry=retry_if_exception_type(())`, run against ONLY T2 + test_retry_seam's two live 16-way families | 4 of 4 red | KILLED. T1/T2 do not pass vacuously |
| `deadline_ignored` | 2 | `stop_after_delay(_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS)` (the per-call deadline is ignored) | 2 red (`test_the_attempt_floor_survives_a_deadline_shorter_than_one_attempt`, retry_policy deadline leg) | KILLED |
| `a3_half` | 2 / A3 | `full_jitter/2` (uniform(0, w/2)) | 22 red incl. A3 upper tail, window | KILLED |
| `a3_wexpjitter` | 2 / A3 | `wait_exponential_jitter(initial=base, max=cap, jitter=base)` | 22 red incl. window, A3 | KILLED |
| `a3_floor16` | 2 / A3 | `max(full_jitter, w/16)` | **737 passed** | SURVIVES. NO ROUND (A3's stated threshold admits a floor below w/8; residual R3) |
| `classifier_false` | 2 / P1c-3 | `_is_retryable_conflict_kind` → `False` | 6 red: T2 ×2, test_retry_seam 16-way ×2, scout CAS, SDK live conflict typing | KILLED. Sharing proven |
| `retry_unknown` | 2 | `retry=` also retries `SurrealOutcomeUnknownError` | 6 red (write/read in-flight, both timeouts, L3) | KILLED |
| `fb_txn_domain_unknown` | 4 | transaction-path domain rejection → unknown | 7 red (T3/T4/T6 family) | KILLED |
| `q6_drift_read_half` | 4 / Q6 | drift note = `"…outcome unknown: {exc} — safe to re-run"` | `TestAnUnknownDriftFilingIsServedAsUnknown` red | KILLED, but for the missing "verify", not for "safe to re-run" (residual R8) |
| `c10_first_or_none` | 3 | `run()` returns `results[0] if list and non-empty else None` | 3 fail-closed legs red | KILLED |
| `c10_first_statement_only` | 3 | `run()` sends only the text before the first `;` | live later-failure leg red | KILLED |
| `c10_swallow_later` | 3 | `run()` catches the later failure and re-reads statement 1 | live later-failure leg red | KILLED |
| `mono_slice` | 6 | `record_text` slices `str(RecordID)` (right only when bracketed) | 5 record_ids red, incl. letter-led and digit-led legs | KILLED |
| `b2_owner_slice` / `b2_idsample_slice` | 6 / B-2 | B-2 renderers slice `str(RecordID)` (right for digit-led and non-word, wrong for letter-led) | dedicated B-2 pin GREEN on both; killed elsewhere (idsample: 9 a19/a19b reds; owner: 1 incidental a28 integer-scan red) | KILLED; rider gap (residual R18) |
| `lm7_private_loop_capped` | 7 / RS7 | `upsert` = private cap check + a per-record `UPSERT` loop over `_query` | **20 passed** | SURVIVES. NO ROUND (0 production callers; residual R1) |
| `edges_names_page` | 8 | `name_rows[:1000]` | B4 `TestNoBatchedEdgeDangles` red | KILLED |
| `edges_nodes_page` | 8 | `node_rows[:500]` | B4 red | KILLED |
| `edges_refers_page` | 8 | `refers_rows[:2500]` | edge-COUNT pin + searchable red | KILLED |
| `edges_derivation_drop` | 8 | `_derive_edges` returns `edges[:-1]` | edge-COUNT pin **stays green** (its oracle IS the derivation); 5 `test_graph` derivation pins red | KILLED elsewhere. The oracle-sharing bound is real and covered (residual R7) |
| `b3_no_bound_realtime` | 4 / R4 | realtime arm serves `_FAILED_STORE_REASON` without the cap | B3 red | KILLED |
| `b3_no_bound_batch` | 4 / R4 | batch arm (`_commit_batch_file`) serves no bound | **B3 passes (1 passed)** | **SURVIVES → MP-1** |
| `streaming_false` | F11 | `SURREAL_STREAMING = False` | CF4 **passes** | SURVIVES. NO ROUND: the seam's drop-on-timeout masks streaming. Proven by construction (§P1b row 17, residual R4) |

## MISSING PINS
| id | the wrong build that survives + receipt | the pin that would kill it | defect it catches | tag |
|---|---|---|---|---|
| **MP-1** | `b3_no_bound_batch`: the batch-sweep arm (`Indexer._commit_batch_file`'s `except SurrealStoreError`) serves `_FAILED_STORE_REASON` with no row-cap bound. `wb_b3_no_bound_batch.log`: B3 1 passed. **Pair proven** with `adv3/probes/test_adv3_b3_batch_probe.py` (pasted below): reference **2/2 green** (`probe_b3_reference.log`); this build reddens **exactly `[batch]`** (`wb_b3_batch_probe_pair.log`, PROOF HELD); CONTROL: the realtime-arm build reddens **exactly `[realtime]`** (`wb_b3_realtime_probe_control.log`, PROOF HELD). So the legs reach two distinct production arms. | `TestARefusedFileIsNamedOnTheServedStatus` parametrised over the sweep shape (`batch` / `realtime`). Equivalently, the probe: one per-file commit raises `TxnRowCapExceededError` naming a cap of 1009; `index_all()` under `batch={"mode": mode}` with a `supports_batch` embedder; the refused file's served reason (`index.failed_reason:<tier>:<path>`, what `index_status` serves) names 1009. | An agent indexing a large file under a batch-capable embedder (voyage_cloud / voyage_context, `supports_batch=True`; `auto` mode picks batch above the chunk threshold) is told the file "failed" with no bound. It cannot tell a row-cap refusal (do not retry; split the file) from a transient fault. R4 rider (3) + R17: the count does not describe its set. | **PINNED PROPERTY, NEW CASE · REPEAT CLASS (round-2 MP-A: "both sweep shapes")**. CLASS: *a per-file store fault's served fate AND its reason are decided identically in both sweep shapes*. CHOKEPOINT: one helper shared by the two cloned `except SurrealStoreError` arms (`_index_chunks` and `_commit_batch_file`: `_landed_after_unknown` → `refused_reason` → log → `_mark_file_failed`, byte-for-byte twins in the reference). SIBLINGS TRIED: realtime arm (killed), batch arm (survives), MP-A's three outcome classes × both shapes (killed). SIBLINGS NOT TRIED: the embed-failure arm (`_FAILED_EMBED_REASON`) in batch vs realtime; the static-snapshot index path. Reachability: this deployment's TEI embedder has `supports_batch=False` (base default), so the batch arm is reachable today only on the shipped voyage backends. |
| (MP-2 → residual R18, NOT a missing pin) | `b2_idsample_slice` / `b2_owner_slice` slice `str(RecordID)`: right for digit-led and non-word keys, wrong for letter-led ones. The dedicated B-2 pin `TestTheMigrationRefusalRenderersServeBareKeys` ×2 **stays GREEN on both**, because it feeds digit-led + non-word keys only. Both builds die elsewhere. id_sample: 9 a19/a19b live hostile-id legs (`wb_b2_idsample_slice.log`, 9F/620P). Owner names: ONE a28 integer-scan pin, `test_am30_pin2_every_count_in_the_reason_is_a_field_value[P_foreign]`, which reads stray digit runs `[9, 7, 7]` out of the mangled names. That is an incidental proxy, not an id check (`wb_b2_owner_slice.log`, 1F/628P). Control `control_b2.log`: 629/629. | add one LETTER-LED key to each of B-2's two legs (R26-3 rider: "served-id pins keep their letter-led and non-word legs") | the served id of a letter-led principal (~72% of principals) is mangled in the migration refusal. Today it is caught only by a pin that goes green whenever the mangled residue holds no digit run | RIDER GAP (R26-3). NO ROUND by the one-question rule (no build survives the contract). Cheap, so recommended for round 8 |

## LANDMINE 1: "tenacity in name only": BEHAVIOURALLY INVISIBLE
- **The build:** `lm1_handloop` replaces the native `AsyncRetrying` in `retry_on_conflict` with a hand-written `while` loop.
  - It keeps every observable law: the ONE factory's wait object `backoff.full_jitter(base, cap)` called with a stand-in state; the same stop predicate; `_exhausted` for the one record; `asyncio.sleep` from `_txn`.
  - Result: **738/738 green** across native_retry, retry_seam, retry_policy, txn_classification and backoff_seam, plus the scout CAS. That includes A4 (the factory IS called) and the `_POW_ALLOWLIST` perimeter (no `**`).
  - So **no behaviour pin can see it**, and none should. R18's "native" is a property of HOW the loop is built, not of anything a user, the app, the books or the stock see. **It is not a missing pin by the one-question rule.**
- **Why the contract cannot see it:** `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES = {"loremaster.store._txn", "tenacity.asyncio"}` deliberately admits a sleep issued from `_txn` (the hand-rolled HEAD driver's site), so that HEAD's pins stay green. That admission is exactly the door.
- **Proven instrument (pair, both legs):** narrow the set to `{"tenacity.asyncio"}` (a one-line change to an EXISTING runtime instrument; no source scan).
  - Reference: **738/738 green** (`instr_lm1_reference.log`, TREE=cf20cdc7… = base + that one line).
  - `lm1_handloop`: **26 red** (`wb_lm1_under_instrument.log`).
  - Bound: gameable by a hand loop that calls tenacity's private `_portable_async_sleep`. Honest-developer threat model only.
  - It turns HEAD's currently-green driver pins RED at HEAD, so it must land WITH the build (an F6 `red_nodeids` entry or the build commit).
- **Recommendation (the operator decides):**
  - It is an attribution check ("who issued the sleep"), i.e. spelling-adjacent. Global law puts a check on how code is written behind operator approval, so I do not add it.
  - Option A: approve the narrowing as a standing instrument (proven, 0 over-fire).
  - Option B: make it a **named cold-audit diff check**: "`retry_on_conflict` and scout `run` contain no loop around the attempt; tenacity's `AsyncRetrying` IS the loop; no `wait(...)` called outside tenacity".
  - My recommendation is A plus B. A is cheap and already measured. B is the fallback if A is refused.
- **Sibling NOT TRIED:** the same hand loop in scout's reconnect ladder. Scout pins observe its injected `sleep=`, which is not attributed by module at all, so the narrowing would not reach it. B is the only instrument there.

## P1b QUANTIFIER TABLE
| # | invariant | ∀ / guarded | receipt |
|---|---|---|---|
| 1 | a retryable conflict is retried, at every seam and both txn paths | ∀ (16 seams + bootstrap + scout + txn) | `r2_text` 56 red; `classifier_false` 6 red |
| 2 | a never-retrying driver cannot pass the live contention premises | ∀ (A2 controls on the sleep seam) | `a2_never_retry_live_only` 4/4 live nodes red |
| 3 | anything but the signal is never retried (incl. a transport-unknown) | ∀ | `retry_unknown` 6 red; `r2_text_or` 34 red |
| 4 | every slept backoff ∈ [0, min(cap, base·2^(n−1))) and the window grows | ∀ attempts | `a3_wexpjitter`, `a3_half` red |
| 5 | full jitter reaches both tails (A3) | **guarded** by a fixed attempt index and fixed thresholds w/8, 7w/8 | `r2_sleepdrift`, `a3_half` red; `a3_floor16` **survives** (floor < w/8 admitted, stated bound, NO ROUND) |
| 6 | the loop is tenacity's (R18) | **guarded by nothing behavioural** | `lm1_handloop` survives 738/738 → §LANDMINE 1 |
| 7 | the per-call deadline bounds THIS call | ∀ | `deadline_ignored` 2 red |
| 8 | an unknown commit is never served failed; one file's fault never stops the sweep | ∀ outcome classes × both shapes | `r2_f18_abort` red ×2 |
| 9 | a refused file is named WITH its bound | **guarded: realtime shape only** | `b3_no_bound_batch` survives → **MP-1** |
| 10 | a server-answered error is definite (F-b) | ∀ over both seams' domain branches | `r2_domain_unknown` 1 red; `fb_txn_domain_unknown` 7 red |
| 11 | every transport failure on a request is unknown (F14) | ∀ | `r1_f14_sniff`, `r2_f14_timeout_definite` red |
| 12 | rows are the one strain bound | ∀ | `r1_stmtcap` red |
| 13 | upsert rides the row cap | ∀ over the over-cap door; a private capped loop passes | `r2_rs7_direct` red; `lm7_private_loop_capped` survives (NO ROUND) |
| 14 | every batched graph table lands its derived rows | ∀ over 4 tables (count pin: refers/answers_to; B4: names/nodes) | `edges_{names,nodes,refers}_page` red |
| 15 | harness `run()` answers statement 1 and fails closed | ∀ over list / non-list / later failure | 3 C10 builds red |
| 16 | served/compared id text is right for every key shape | ∀ at record_text (mono_slice red); **guarded at B-2** to digit-led + non-word keys | `mono_slice` 5 red; both `b2_*_slice` builds killed only on other files (R18) |
| 17 | a timed-out write under the factory never lands (F11) | **guarded by the seam's drop-on-timeout** | `streaming_false` survives. **By construction** (`probe_streaming_both.log` vs `probe_streaming_keeponly.log`): with the socket KEPT on a timeout, `streaming=False` → CF4 RED ("COMMITTED anyway"), `streaming=True` → GREEN. CF4 fires in the only world where the cause matters → NO ROUND |
| 18 | guard safe set ∩ write doors = ∅ | ∀ (derived) | `r1_guard_safe` red |
| 19 | named overrides for every derived owner; reconnect forever | ∀ (derived owner set) | `r1_overrides_one`, `r1_attempts20/5` red |
| 20 | a write renderer serves write advice | **guarded: D1 batch renderer only** for "no 'safe to re-run'" | drift sibling: the note must say "unknown"+"verify"; my build died for the missing "verify". A "verify AND safe to re-run" drift note NOT TRIED. Dedup backstop (`_file_drift_finding_deduped`) → residual R8 |
| 21 | nested store closed once | not pinned for "once" | `r2_x18_double` survives (NO ROUND) |

## P1c ENFORCEMENT / REACH TABLE (instruments the contract stands up)
| rule / instrument | chokepoint | reach: derived or hand-list | effect vs proxy | sharing by mutation (run) | spelling? | legs |
|---|---|---|---|---|---|---|
| sleep seam `_driver_sleeps.record_driver_sleeps` | `asyncio.sleep` module attribute + `sys._getframe(1)` caller module | **hand-list** `DRIVER_SLEEP_CALLER_MODULES` (2 entries) | effect (what was slept), but the list's `_txn` entry admits a hand loop | — | caller-module attribution is spelling-adjacent | empirical (`lm1_*`) |
| A4 one wait factory | `loresigil.backoff.full_jitter` | **declared 2 sites** (R27-6 accepted) | effect (sentinel slept) | yes: `r2_sleepdrift`, `a3_half`, `a3_wexpjitter` redden 19 per-seam pins + factory pins | no | empirical |
| A4 escapes, beyond the declared direct `wait_*` construction | — | — | — | (i) a hand loop that CALLS the factory (`lm1_handloop`, 738 green); (ii) a wrapper whose output equals the factory's at SENTINEL scale, `max(factory, w/16)` (`a3_floor16`, 737 green) | — | empirical. **The declared escape is NOT the only one** |
| conflict classification | `_is_retryable_conflict_kind` → `is_retryable_conflict_error` / `_rollback_verdict` | one predicate | effect (live T2) | yes: `classifier_false` reddens both txn paths, both 16-way families, scout CAS | no | empirical |
| F14/F-b ladder | `_raise_attempt_failure` + txn `_attempt` domain raise | 2 sites | effect | n/a | no | empirical |
| refused-file reason | **two cloned arms** (`_index_chunks`, `_commit_batch_file`) | — | effect at one arm only | **no: two sources of truth** → MP-1 | no | empirical |
| row cap | `compose` | one | effect | n/a | no | empirical |
| `_sdk_guard` doors | `_is_door` (derived from the SDK) | derived | effect | n/a | no | empirical (`r1_guard_safe`) |
| C10 `run()` rule | `_surreal_harness.run` (staged) | one | effect (fakes + live) | n/a | no | empirical ×3 |
| edge-count oracle | re-runs the pure derivation | derived | effect for the write; **shares** the derivation | n/a | no | empirical (`edges_derivation_drop`: count pin green, test_graph red) |
| MP-C both-ways diff (`reddiff.py`) | regex over the summary section | — | proxy gaps: (a) `\S+?` drops 11 space-bearing ids; (b) `green = collected − red` counts skips as green | checked: under a full parse red@ref ∖ red@HEAD = ∅; the 1-node skip delta is a NEW node | no | empirical (`probes/reddiff_check.out`, skip probe) |
| id text | `record_text` (+ 4 private homes: `governed._bare`, `keeps/principal_keys._record_id_part`, `floor_calibration._bare_record_id`) | 5 homes | effect at record_text (mono_slice red) | **not demanded** (residual R12, repeat of round-2 P-PRIOR) | no | empirical + inspection |
| catch-site walker reach (R14) | `_catch_sites` | derived (approved scanner) | — | — | approved | not attacked this round |

## RESIDUALS (one verdict each; none reopens a round)
- **R1:** `lm7_private_loop_capped` survives every pin.
  - It is NO ROUND: `upsert` has 0 production callers.
  - The reference itself still builds private UPSERT SQL in `upsert`, so R27-2(a) is BUILDER work.
  - Named cold-audit check: the R27-2 row-builder mutation must redden the upsert pins AND B1.
  - In-tree prior art for the batched overwrite form R27-2/X13 asks about: `graph_surreal`'s `INSERT INTO name $rows ON DUPLICATE KEY UPDATE value = $input.value`.
- **R2:** `x18_double`. NO ROUND (idempotent).
- **R3:** A3 admits a floor below w/8 (`a3_floor16`, 737 green). It is the ruled false-red trade (3e-15). NO ROUND.
- **R4:** F11 / CF4 is masked by the seam's drop-on-timeout; proven to fire when the socket is kept. NO ROUND. Builder note: changing timeout→drop makes `SURREAL_STREAMING` load-bearing, and CF4 guards it.
- **R5:** `sdk3r7/reddiff.py` drops ids containing spaces, 11 per log; it should use `mutation_proof.parse_red_node_ids`. A checker gap, NO ROUND. The conclusion holds.
- **R6:** `reddiff.py` counts skipped as green. The one-node delta, `test_mint_unknown_outcome_note_q1::…[SurrealOutcomeUnknownError]`, is a node new on SDK 3 (skip by design), not a HEAD-green node. NO ROUND.
- **R7:** The edge-count oracle shares the derivation. Derivation defects are pinned by `test_graph` (5 red). Stated bound, NO ROUND.
- **R8:** "A write renderer never serves read advice" is pinned only at the D1 batch renderer. The drift sibling is backstopped by dedup. NO ROUND; a "verify + safe to re-run" drift variant was NOT TRIED.
- **R9:** A1's caplog sees only propagating loggers. A per-attempt record on a `propagate=False` logger was NOT TRIED: implausible, and only operator-visible. NO ROUND.
- **R10:** The author's P-PKG table omits `AsyncQueryBuilder.first()`, a name match with the wrong semantics (returns `None` on no statements). The verdict is unchanged. NO ROUND.
- **R11:** `loresigil.backoff.jittered_backoff_delay` constructs the same `wait_random_exponential(...)` as `full_jitter` (two homes for one law until packet 68). Builder could delegate. NO ROUND.
- **R12:** Five id-text homes in the reference (P-PRIOR, repeat of round 2). Builder collapses them to RecordID parts / `record_text`. NO ROUND.
- **R13:** The F-b pins `TestAServerAnsweredErrorIsADefiniteFailure` ×2 drive the NotAllowed/auth branch, not the domain branch. The domain→unknown builds die on the T-family instead. The class name over-claims its reach. NO ROUND.
- **R14:** B-2's backtick leg cannot fire on SDK 3.0.0, whose `str()` never emits backticks. A strip-⟨⟩ renderer passes today and is caught the day the SDK pin bumps to 3.0.1. NO ROUND.
- **R15 (F-a, landmine 5):** the doubles' `async def query` returns a coroutine; SDK 3.0.0 `query()` returns an `AsyncQueryBuilder` awaitable.
  - grep finds 0 production uses of `.first()` / `.into()` / `create_task(…query…)`, so no production door sees the difference today.
  - The conflict doubles' `QueryError(…, details={"kind": "TransactionConflict"})` matches the SDK's `is_transaction_conflict` (`errors.py`: `_detail_kind(self.details) == "TransactionConflict"`), with a live witness (`TestTheSdkTypesALiveTransactionConflict`).
  - The multi-statement shape was re-probed: `[7]`, `[7, 8]`, a later THROW raises (`probes/multi_statement_rerun.out`).
  - Re-open trigger: the first production use of a builder-only method or of `create_task` on `query()`.
- **R16:** Four untargeted packet-58 files read the deleted `TXN_STATEMENT_HARD_CAP`: `test_reanchor_58_r2_am2`, `_r2_probes`, `_r3_probes`, `test_supersede_reanchor_58`. They give 65 red on both HEAD and reference (identical sets), so they are owned by packet 58 (R12 F19), not by 66. Flag: confirm that they are in the INDEX provisional red list.
- **R17:** Finding #582 (lore_index reconcile timeout).
- **R18:** B-2 has no letter-led leg, so the R26-3 rider is unmet. Letter-led wrong builds die only on a19/a19b (robust) and on one a28 integer scan (incidental). See the §MISSING PINS row. NO ROUND; a cheap round-8 fix.

## P-PKG (built before reading the author's table, then diffed)
| mechanism | library | what I READ | verdict | author r7 |
|---|---|---|---|---|
| conflict retry loop | tenacity 9.1.4 `AsyncRetrying` | installed `tenacity/__init__.py` L237–315 (`_local = threading.local()`; `iter_state` and `statistics` are per-thread, not per-call, so one object shared across concurrent coroutines shares them; the reference builds one per call, correct) | replace | replace (agree) |
| wait law | `wait_random_exponential` via `backoff.full_jitter` | ref `loresigil/backoff.py` (`full_jitter`; `jittered_backoff_delay` duplicate, R11) | replace | agree |
| stop / exhaustion | `stop_any`/`stop_all`, `retry_error_callback` | ref `_txn.retry_on_conflict` | replace | agree |
| sleep observation | tenacity `sleep=` vs the `asyncio.sleep` patch | `_driver_sleeps.py` (bespoke frame attribution: production passes no `sleep=`, so the patch is the only seam) | keep_with_trigger (trigger: production exposes `sleep=`) | not listed (gap, NO ROUND) |
| A3 distribution | scipy 1.18.0 `stats.kstest` (installed, version read) | power reasoning: a w/16 floor shifts the CDF by ≤1/16; the KS critical value at n=256, α≈3e-15 is ≈0.20 (MEDIUM: computed, not run) | keep bespoke min/max | — |
| harness first statement | SDK 3.0.0 `AsyncQueryBuilder.first()` | `connections/builders.py` L1870–1875: `if not values: return None` | bespoke fail-closed is the justified gap (name match, wrong semantics: it IS `c10_first_or_none`) | "probed; replace" without `.first()` (gap, R10) |
| query shape | SDK `query()` | `async_template.py` L216–242 docstring + live probe rerun | as ruled | agree |
| batched overwrite (R27-2) | engine `INSERT … ON DUPLICATE KEY UPDATE` | in-tree `graph_surreal.py` names batch | candidate for R27-2(a); builder probes per X13 | not listed |

## P-PRIOR
The contract demands no new rule-deciding production symbol beyond `backoff.full_jitter` (R20-A4).
- `full_jitter`: its owner and twin is `jittered_backoff_delay`, in the same module (residual R11).
- The reference's id-text helpers: 5 homes (residual R12).
- The reference's indexer failure ladder: cloned in two arms. That clone is MP-1's chokepoint.
- Searches: grep over `loremaster/loremaster`, `loresigil` (said, dogfood case (c)).

## P-PORT
n/a: lore is not an Odoo tree. `Odoo-20 portability: n/a — no Odoo seam touched`.

## P6 CORPSE SWEEP (`loremaster/tests`, 272 tracked files; 12 patterns)
Each hit with a verdict:
- `_txn_conflict_backoff_seconds` ×5: `test_retired_symbols.py:429` (retired-name registry, CORRECT); `_driver_sleeps.py:3`, `test_backoff_seam.py:137,712`, `test_retry_seam.py:83` (prose naming the retirement, CORRECT).
- `RetryError` ×1: `test_sdk3_retry_policy.py:10` (states it is never what a caller sees, CORRECT).
- `_RETRYABLE_CONFLICT_KIND` ×7: `test_surreal_harness.py:137,1549`, `test_retry_seam.py:143,309,312,332` (prose recording the retirement, CORRECT); `test_retry_seam.py:3766` (`_MARKER_NAME` string, a pre-existing marker test; it passes on the reference (control 858 green), CORRECT).
- `TXN_STATEMENT_HARD_CAP` ×20:
  - `_surreal_fakes.py:110`: `getattr(...) or` fallback; the reference has `TXN_ROW_HARD_CAP`, so the cap branch is dead. CORPSE-SAFE.
  - `test_ingest_entity_seam.py:591`, `test_surreal_apply.py:1505`, `test_sdk3_index_batching.py:5`, `test_reanchor_58_r3_convergence.py:12`: prose.
  - `test_reanchor_58_*` and `test_supersede_reanchor_58` live reads ×14: packet 58's dormant pins. Red on HEAD and reference alike (R16).
- `_record_shared_jitter`, `_JitterRecorder`, `_conflict_sleep`, `_conflict_wait`, `_connect_wait`, `SDK_MAJOR`: 0 hits each (retired cleanly).
- `_backoff_delay` ×23 in `test_backoff_seam.py` + `test_calibration_engine.py`: the packet-68 shim sites (`CalibrationEngine._backoff_delay`), out of 66 by R18. CORRECT.
- `str(RecordID` ×51: the round-6 C9 sweep owns these. Not re-adjudicated this round (NOT TRIED individually); mono_slice and f17 show the record_ids chokepoint pins live.

## SATISFIABILITY (item 9)
- **Receipts:** `final_head2.log` TREE=29c56751… 729F/8894P/45s/3xf/4E EXIT=1; `final_ref2.log` TREE=4dd680c2… 438F/9209P/46s/3xf EXIT=1; pristine TREE=2f5cbb32… 642F/8956P. All valid.
- **Full re-parse** (`probes/reddiff_check.py`, mutation_proof's parser): HEAD 729, pristine 642, ref 438. The same 11 space-bearing ids are dropped by `reddiff.py`'s regex in all three. red@ref ∖ red@HEAD = **∅**.
- **Skip delta** (ref 46 vs HEAD 45): `test_mint_unknown_outcome_note_q1::test_a_proven_fault_keeps_the_not_landed_message`. The reference has 2 NEW parameters, `[SurrealOutcomeUnknownError]` (skipped) and `[TxnRowCapExceededError]` (passed). Every HEAD parameter keeps its outcome (inline `-v` on both trees). No HEAD-green node lost.
- **Untargeted statement-cap readers:** identical 65-node red sets on HEAD and reference (R16).
- **No REFERENCE BUG found** in the sampled nodes; the reference passed 878/878 of my union control.

## Round-8 scope (brief item 10)
Round 8 already carries the F6 gate contract, the Q7 re-run plus the raising leg, the `_FactoryMutation` fold and the cumulative inventory. That is sufficient for those items. Add:
- **MP-1** (one parametrise);
- the **R26-3 rider gap** at B-2 (one letter-led key; residual R18);
- the **landmine-1 operator decision**. If the decision is A, round 8 owns the one-line `_driver_sleeps` narrowing plus its RED@HEAD registration.

The fold of `_FactoryMutation` into `_driver_sleeps` is the natural moment for the narrowing.

## LOOP COST
- Adversary round 3 (budget R25: adversary rounds 4–5 remain).
- 58 pytest runs, all scoped (itemised in the summary block). 8 haiku-runner spawns, about 2.5 h wall.

## RECEIPTS
- **Runner:** `adv3/runwb.sh` (pasted below) runs `scripts/mutation_proof.py` inside a provenance-verified tree. Each log opens with `tree_id.sh` and `loremaster.__file__`, and ends with `EXIT=` and the POST-RESTORE TREE.
- **Trees:** `adv3/builds/t1…t5`, each from `adv3/mkbuild.sh` (rsync of `adv3/base` + `uv sync --all-packages` + `scratch_copy.sh --verify-only`); `loremaster.__file__` inside its own tree.
- **Per-build table:** `adv3/runs_table.txt` (name | pre-TREE | EXIT | count | tree | post-TREE). Every pre-TREE equals the post-TREE.
- **Controls:**
  - `logs/control_base_a.log` (858 passed, EXIT=0, TREE=4dd680c2…).
  - `logs/control_base_b.log` (20 passed, EXIT=0).
  - `logs/instr_lm1_reference.log` (738 passed, EXIT=0, TREE=cf20cdc7…).
  - `logs/probe_b3_reference.log` (2 passed, EXIT=0).
  - `logs/control_b2.log` (629 passed, EXIT=0, TREE=4dd680c2…).
- **Probes:** `probes/multi_statement_rerun.out`, `probes/reddiff_check.{py,out}`, `logs/probe_streaming_{both,keeponly}.log`, `logs/untargeted58_{ref,head}.log`, `probes/test_adv3_b3_batch_probe.py`.
- **Specs** (declared before the runs, ids from `--collect-only` in `collect_base.txt`): `adv3/wb/<name>/{target,anchor,repl,expect,tests}`; generators `mkspecs.py`, `mkspecs2.py`, `mkspecs3.py`.

### Instruments (pasted verbatim, per brief-base §1)
`adv3/runwb.sh`:
```bash
#!/usr/bin/env bash
set -u
T="$1"; N="$2"; TO="${3:-300}"; NW="${4:-4}"
A=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d68febab-e1d4-4ed2-95a0-0ded042fa32c/scratchpad/adv3
W="$A/wb/$N"; LOG="$A/logs/wb_$N.log"
EXP=(); while IFS= read -r l; do [ -n "$l" ] && EXP+=(--expect-red "$l"); done < "$W/expect"
mapfile -t TESTS < "$W/tests"
{
  echo "WB=$N TREE-UNDER-TEST(before mutation):"; ~/.claude/orchestration/tree_id.sh "$T"
  "$T/.venv/bin/python" -c "import importlib.metadata as m, loremaster; print('loremaster.__file__=' + loremaster.__file__, 'surrealdb=' + m.version('surrealdb'), 'tenacity=' + m.version('tenacity'))"
  cd "$T" && python3 /home/ejprice/PycharmProjects/lore/scripts/mutation_proof.py --file "$(cat $W/target)" \
    --anchor-file "$W/anchor" --replacement-file "$W/repl" "${EXP[@]}" -- \
    systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    "$T/.venv/bin/python" -m pytest -q -rfE -p no:cacheprovider --timeout="$TO" -n "$NW" "${TESTS[@]}"
  echo "EXIT=$?"
  echo "POST-RESTORE:"; ~/.claude/orchestration/tree_id.sh "$T" | tail -1
} > "$LOG" 2>&1
```
The landmine-1 instrument (the one-line narrowing, applied in `builds/t5/loremaster/tests/_driver_sleeps.py`):
```python
DRIVER_SLEEP_CALLER_MODULES: frozenset[str] = frozenset({"tenacity.asyncio"})  # ADV3 PROBE (landmine-1 instrument)
```
The `lm1_handloop` replacement for `retry_on_conflict`'s `AsyncRetrying` block:
```python
    wait = backoff.full_jitter(_TXN_CONFLICT_BACKOFF_BASE_SECONDS, _TXN_CONFLICT_BACKOFF_CAP_SECONDS)
    attempt_number = 0
    while True:
        attempt_number += 1
        try:
            return await attempt()
        except RetryableConflictSignal as signal:
            if attempt_number >= _TXN_CONFLICT_ATTEMPT_CEILING or (
                time.monotonic() - started >= deadline and attempt_number >= _MAX_TXN_CONFLICT_ATTEMPTS
            ):
                done = __import__("concurrent.futures", fromlist=["Future"]).Future()
                done.set_exception(signal)
                _exhausted(__import__("types").SimpleNamespace(attempt_number=attempt_number, outcome=done))
            await __import__("asyncio").sleep(wait(__import__("types").SimpleNamespace(attempt_number=attempt_number)))
```
The streaming-mask probe (two edits to `_txn.py` in `builds/t3`, content-backed-up and restored md5-exact): `SURREAL_STREAMING = False`, plus `if type(error).__name__ != 'TransportTimeoutError': await drop(connection)` in `_raise_attempt_failure`. Result: `CF4` red "COMMITTED anyway". With `SURREAL_STREAMING = True` and the same keep: green.

MP-1's pin, as a proven probe (`adv3/probes/test_adv3_b3_batch_probe.py`):
```python
import pytest
import test_indexer_bulk_sweep as bulk_suite
from _surreal_harness import unique_database
from loremaster.store import _txn

_CAP = 1009

def _row_cap_once(real):
    remaining = [1]
    async def _wrapped(*args, **kwargs):
        if remaining[0] <= 0:
            return await real(*args, **kwargs)
        remaining[0] -= 1
        raise _txn.TxnRowCapExceededError(
            f"composed transaction writes 4242 rows, over the {_CAP}-row cap per transaction — refused before "
            f"anything was sent to the server")
    return _wrapped

@pytest.mark.parametrize("mode", ["batch", "realtime"])
async def test_a_row_cap_refusal_names_its_bound_in_either_sweep_shape(tmp_path, monkeypatch, mode):
    live = tmp_path / "live"
    paths = bulk_suite._build_corpus(live, count=3)
    config = bulk_suite._config(slug=unique_database(), live_path=live, batch={"mode": mode})
    trio = bulk_suite._trio()
    embedder = bulk_suite.RecordingBatchFlatEmbedder(dim=bulk_suite._DIM, supports_batch=True)
    indexer = bulk_suite._make_indexer(config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap")
    monkeypatch.setattr(trio.store, "apply", _row_cap_once(trio.store.apply))
    await indexer.index_all()
    reasons = {path: await trio.manifest.meta_get(f"index.failed_reason:custom:{path}") for path in paths}
    refused = {path: reason for path, reason in reasons.items() if reason}
    assert len(refused) == 1, f"{mode}: premise — exactly one file refused: {reasons!r}"
    (reason,) = refused.values()
    assert str(_CAP) in reason, f"{mode}: the refused file's served reason {reason!r} does not name the row cap"
```

## PROGRESS LOG (2026-11-08)
- Reads: brief-base v25, store reference (cited), rulings R1–R27, sidecar RULING-2/6, r7 REPORT, ADVERSARY2. lore registered.
- The r7 loop finished 20/20 during my run. Not re-run.
- Base verified (TREE 4dd680c2… = sdk3r7/ref; test tree = HEAD 150b85b's except the staged C10 `run()` rule). P0 union control green.
- 9 runner queues: t1 (8), t2 (12), t3 (11 + 1 + 2), t4 (6), t5 (instrument pair), B-2 (3). All trees restored byte-exact.
- Housekeeping (2026-11-08): three haiku-runner watcher loops (`until ! pgrep -f queue_t{1,2,3}.sh`) matched their own command lines and never exited, which is brief-base §5 bound 5. Their queues had finished and every log carries `EXIT=`. I killed them (pids 2509331/2509390/2509468). A fourth runner hit the same trap and stopped its own watcher. Recommendation for the `haiku-runner` definition: watch a PID or the log's `EXIT=` line, never `pgrep -f <pattern in own cmdline>`.
- Scratch trees `adv3/base` and `adv3/builds/t1…t5` remain in place for the lead to keep or discard. t1–t4 are at TREE=4dd680c2… (restored). t5 = base plus the one-line landmine-1 instrument (TREE=cf20cdc7…).
