brief-base v16 read · brief project v7 read

# REPORT-contract-63c-i-a-a28b — the amendment-32/33 fold of the 63c-i-a contract (a28 → a28b)

## SUMMARY BLOCK
- **state:** done-with-deviations (D-1…D-8, §4). Two rulings landed MID-FOLD and are folded: **am-33** (`f66a190`: FK-a28b-1 Reading 1 + the rename `TxnUniqueViolationError` + the U-sdk pin-the-miss) and **58 am-7** (`01565f9`: the scanner — domain + partition, the F-4 re-key); directives #17084 / #17087 acked.
- **deviations:** D-1 `_CONFLICT_CLASS` bound dynamically (the unbuilt class) · D-2 K3 re-keyed to the class · D-3 K9 non-vacuity amended per am-32 §1.1 item 5 · D-4 ONE spec dict for the SHAPE pin only · D-5 one `noqa` to keep K6 AST-equal · D-6 `_spy_registry_queries` lives in a28 · D-7 `test_retry_seam.py` joins the a28 bound · D-8 mid-fold rulings → the mutation batch re-run on the final contract. FK-a28b-4: lead #17087 "the exact sets" read as the PARTITION now (vs am-7's "ONE set first").
- **Packages considered:** `surrealdb` 2.0.0 errors — READ `errors.py` (`AlreadyExistsError` properties → `_detail_field(self.details, "<Kind>", …)`) + LIVE probe (§A.1): the record-id collision IS typed (`AlreadyExistsError.record_id`), the UNIQUE-index collision is NOT (`InternalError`, `details=None`) → `replace_with_adapter` for R (typed branch), `bespoke` text markers for U (confined to the ONE classifier, am-33; the SDK limitation is pinned as a KNOWN BOUND) · stdlib `contextvars` (per-call mint marker), `typing.get_args` (annotation-derived perturbation) — `replace` (used) · pytest-repeat: not installed; the 20-consecutive law is serial whole-session runs (`conc20_a28b.sh`).
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** ~40 new test-local symbols, all dispositioned (§11); lore_search not used (fallback: read by hand, said)
- **Graded:** n/a — contract author (base: checkpoint `169925f`; the folded contract a28 `d334042`; HEAD-at-report `0f69efa`; 63c production byte-identical `169925f`→HEAD, checked at `0f69efa`)
- **decisions-needed:** FK-a28b-2 (the classification enum when there is nothing to classify → `None`; `mixed` names N) · FK-a28b-3 (the unclassified refusal's non-field integers — excluded from pin (2)) · FK-a28b-4 (ONE set vs the partition now — picked the partition per #17087) · F-5 (a leg on an undefined target table raises) · 58 am-7 §3 item 4's "one scanner" pin has no owner · F-9: 58-r3's untracked files are the only currency orphans
- **RED @ `169925f`:** **106 failed / 814 passed** over A + B + 19a + 19b + RS (final files), every red for the ruled reason, and the set is IDENTICAL to the SAT's fixed set (§5, §8) · **Mutation:** run 2 (final contract) **20/20 wrong builds killed** — 19 exact both ways + MB4 (one extra correct red); run 1: MA3 degenerate (re-declared MA3b) (§6) · **Concurrency:** 20/20 consecutive green on the reference, twice (§7) · **SAT:** full suite, ONE tree both ways: reference `342 failed / 11893 passed`, base `448 / 11783`; **red on the reference only 0**; the fixed set == the RED@169925f set (106, programmatic equality); all 342 shared reds adjudicated (58: 119 · 64b-i: 119 + its two converted suites 104; 5 message diffs, none 63c); **63c-attributable 0** (§8) · **Currency:** bound `packet-63c-i-a-a28-contract` UPDATED (+ a28b, + retry_seam on `TxnUniqueViolationError`); `--currency` (fleet-policy workers; forwarded `-n` refused, so waited for quiet): ruff GREEN · typecheck / pytest RED_ORPHANED — **every orphan in packet 58's untracked r3 files; a28b-attributable 0** after fixing 2 mypy lines of my own the gate caught (§9)
- **receipt pointers:** §F forks · §0 capability · §1 required-green · §2 per-item · §3 DUAL + corpse sweep · §4 deviations · §5 RED · §6 mutations · §7 concurrency · §8 SAT · §9 currency · §P1c · §DUAL(P6b) · §FLAGS (F-1…F-9) · §10 BUILDER CONSTRAINTS · §11 DRY · §13 attack list · §A instruments verbatim

## §F FORKS (written BEFORE the pins that depend on them)

### FK-a28b-1 — am-32 §1.2 (keeps' CAS narrowed to `TxnRecordExistsError`) is FALSE on the engine for keeps' door: keeps' conflict is a UNIQUE-INDEX conflict, not a record-id conflict — and its text carries no `already exists`
**Measured 2026-09-26, spike-surreal `surrealdb-3.2.4+20260803.93ab219`, instrument `probe_exists_texts.py` pasted verbatim in §A.1, output §A.1b:**

| leg | door | what the engine serves |
|---|---|---|
| R-txn | record-id collision in `BEGIN…COMMIT` (the `execute_transaction` path) | `ERR: 'Database record \`t:x\` already exists'` |
| R-sdk | record-id collision via `query()` (the `run_query` path — the agent CREATE) | `surrealdb.errors.AlreadyExistsError`, `kind='AlreadyExists'`, `details={'kind': 'Record', 'details': {'id': 't:x'}}`, `record_id='t:x'` |
| **U-txn** | **UNIQUE-index collision in `BEGIN…COMMIT` — keeps' `get_or_create_keyed` shape (fresh ULID id, same `keep.key`)** | **`ERR: "Database index \`k_key\` already contains 'dup', with record \`k:one\`"`** — NO `already exists` |
| U-sdk | the same via `query()` | `surrealdb.errors.InternalError`, `kind='Internal'`, `details=None` — NOT `AlreadyExistsError` |
| T-sdk | `DEFINE TABLE` of an existing table via `query()` | `AlreadyExistsError`, `details.kind='Table'`, `record_id=None`, `table_name='t'`, `str="The table 't' already exists"` |
| T-txn | the same inside `BEGIN…COMMIT` | `ERR: "The table 't' already exists"` |
| CONTROL | an ASSERT rejection inside `BEGIN…COMMIT` | `ERR: 'Found -1 for field \`n\`, with record \`a:1\`, but field must conform to: $value > 0'` |

`keeps.get_or_create_keyed` mints a FRESH client ULID per call (`keep_id = str(ULID())`) and races on the UNIQUE `keep.key` index — so its conflict is the U-txn shape. am-32 §1.1 item 3 names ONE marker, `already exists` ("§A.5b's `str(cause)`"), which is the R-txn/R-sdk shape only. **A literal am-32 build — keeps narrowed to `except TxnRecordExistsError:` with only the `already exists` marker — no longer catches keeps' real conflict: two concurrent registers into a new session would serve `KeepStoreError` to the loser instead of the winner's keep.** (The existing contract's RS-2 8-way handler race drives exactly this conflict every round, so such a build would red RS-2 — the ruling is not silently shippable, but it is unbuildable as written.)

Two readings, which produce different code:
- **Reading 1 (my pick):** the class is *"the write's identity is already taken — re-read, the winner is there"*, over BOTH engine identity shapes: a record-id collision (`already exists` on a `Database record` text; `AlreadyExistsError` with `record_id` on the SDK path) AND a UNIQUE-index collision (`already contains` on a `Database index` text). ONE label, ONE class, ONE mapping helper — am-32's design unchanged, its marker set widened by one live-verified substring. R-6's "ONE predicate for both CAS doors" then holds literally. The Table/DDL already-exists stays OUT of the class on BOTH paths: the probe shows the 3.2.x texts DIFFER (`The table 't' already exists` vs `Database record \`…\` already exists`), which is am-32 §1.1 item 3's own conditional for NOT carrying the table bound — so the marker must be specific enough to exclude the table text, and pin (c) is generated over both paths.
- **Reading 2:** the class stays record-id-only (am-32 literal); keeps' door is NOT narrowed (R-6 stays two predicates, ledgered as a bound), and §W item 3 is withdrawn.

**RULED 2026-09-26 by amendment 33 (`f66a190`): Reading 1, and the class RENAMED `TxnUniqueViolationError` (this report says `TxnRecordExistsError` only where it quotes the pre-am-33 state).** My pick had been Reading 1 — it is am-32's own stated intent (§1.2: "both doors decide from ONE class"), costs one marker, and Reading 2 re-opens R-6. Every keeps-door pin below is written for Reading 1; under Reading 2 exactly those pins (named in §2, rows W3/W1-u) would be withdrawn and nothing else changes. Escalated to the lead (one native message) before any pin was written; continuing on the pick (not a BLOCKER).

### FK-a28b-2 — amendment 31's owner fields when there is NOTHING to classify (written before the population pins)
am-32 §2.1 rules "`None` iff the read was gated off". `owner_classification` is `Literal["operator","foreign","mixed","unclassified"] | None`, and a store with ZERO owned-but-unscoped agents has no owner to classify: none of the four members is true. Two readings: **(A, my pick)** the classification is `None` when the agent read ran but found no owned-but-unscoped row (the enum's `None` also means "no owner"); `distinct_owner_principals` is the measured `0`. **(B)** a fifth member (e.g. `"none"`) so `None` stays strictly "not read". Pinned on A (`_POPULATIONS["P_message"]`, `_RS1_COUNTS`, the gating pin's `owner_classification is None` leg, the success legs). Under B only those expectations change.
Also under this fork: amendment 31 names the sentences for `operator` ("owned by the operator …", no count), `foreign` ("owned by N other principal(s)") and `unclassified` (no count); **`mixed` is unruled.** The EXISTING contract already constrains it (`test_agent_governance_63c_i_a.py::…test_R_Q5_1…[mixed-owners]` requires "owned by the operator" + "E3" in the mixed text — my reference first failed it, §SAT). My pick: the mixed sentence names N (`_OWNER_SENTENCE_STATES_N["mixed"] = True`).

### FK-a28b-3 — the UNCLASSIFIED refusal carries integers that are no field (pin (2) ⊆)
`principals._operator_unresolved` serves "(N principals, M admins)" — measured, but no `MigratePreconditionCounts` field. am-31 says "pin (2) holds unchanged" and is silent on this sentence. Two readings: (A, my pick) pin (2)'s domain EXCLUDES the unclassified population (it stays in the served-fields pin and pin (1)) — surfaced here, not ruled by me; (B) the unresolved-operator counts become fields too. Pinned on A (`_UNCLASSIFIED_POPULATION`, commented in the file).

### Note (not a fork): R-3 was constructible
am-32 §5 R-3 said: build the tokenless winner THROUGH the handler seam, or STOP. Probed on the reference (`credentialed_app_context`, `holder["email"] = None`): an empty-subject token registers OWNERLESS through `AppContext.comms(action="register")` (render: "⚠ registered OWNERLESS …", row `owner_principal NONE, scope NONE`). So the control is re-keyed, not stopped (§2 row R-3).

### FK-a28b-4 — ONE set or TWO? (lead directive #17087 vs packet 58 amendment 7 §0 row 2) — written before the scanner re-edit
58 am-7 §0 row 2 / §2 rules: *"63c-i-a lands the DOMAIN half … with ONE set … Between 63c-i-a's landing and 58's delta, RS-5 and keeps sit in the ONE set with `has_guard` = by-type / by-tuple … 58's delta moves them."* The lead's directive #17087 (acked) says: *"Fold am-7 into your scanner pins NOW (the exact sets plus the completeness in both directions)"* and states RS-5 / keeps are TYPED-SAFE. Two readings that produce different code: **(A)** ONE set now (am-7 literal), the partition is 58's delta; **(B, my pick — the later, addressed instruction, and strictly stronger)** the PARTITION now: `_GUARDED_CAS_DOORS` (a handler exhaustion CAN reach → must carry the passthrough) and `_TYPED_CAS_CATCHES` (disjoint by type), BOTH exact both ways, their union == the derived domain; RS-5 and keeps land in `_TYPED_CAS_CATCHES`, `record_measurement` in `_GUARDED_CAS_DOORS`. Under (B) 58's delta shrinks to `tasks.py::claim_task` + the runtime cross-check + the union completeness over translators/passthroughs (am-7 §1). ⚠ Cross-packet: contract-58-r2's `test_reanchor_58_r2_cas_runtime.py` reads `test_retry_seam._TYPED_CAS_CATCHES` — under (B) it now exists without `claim_task` (58's entry); its red there stays 58's (§FLAGS F-3). Escalated in ONE native message; continuing on (B).

## §0 Capability check (brief-base §4)
- lore: registered (`contract-63c-i-a-a28b` / `63c-20260924` / contract / ≤20m); ledger signals #17082 (FK-a28b-1) and #17085 (the scanner collision); lead directives #17084 (am-33) and #17087 (58 am-7) drained and ACKED; finding **#509** filed (mutation_proof's restore is not signal-safe — measured twice this run, §6). lore_search was NOT used for code structure: every structural read was `awk`/`sed`/`Read` over the files am-32 names (grep/rg hook-blocked, #473), and the DRY queries of §11 were not run — said here (fallback; no tool failure occurred, I did not try, so nothing filed for it).
- The live probes and every pytest ran against the TEST store `ws://127.0.0.1:18000` only (`surrealdb-3.2.4+20260803.93ab219`). `:18500` never touched; the TEI embedder never called (FakeEmbedder harness).
- Required first read done: `docs/reference/surrealdb-31-capabilities.md` §0–§3 (incl. the #497 RETURN-in-transaction paragraph), §5; §6+ skimmed by heading. brief-base v16 read in full.
- brief-base §2 says "never commit"; the spawn brief orders ONE commit — the brief wins (precedence), stated here.

## §1 Required-green enumeration (written BEFORE the pins; re-checked by SAT §8)
A correct a28b build keeps GREEN:
1. **The whole existing 63c-i-a contract as amended** — a19 / a19a / a19b / a28 (minus the DUAL rows of §3) / `test_agent_governance_63c_i_a.py` / `test_agent_registry.py` / the 63b-ii-a message migrate · enforcement · send-scope · capability suites / `test_comms_tool.py` — **both helper shapes** (`_governed_world` for the migrate half, `credentialed_app_context` for the register half; every new pin here uses one of the two, never a third).
2. **Single-principal stores unchanged on EVERY governed table**: legacy agent / memory / message backfills proceed and stamp (a28 FORK-1 legs, a19a clean-store legs); the new gating pin's `both-defined` rows and the success legs assert the proceeding runs serve MEASURED counts, not refusals.
3. **The shared driver's other classes unchanged**: `TxnGovernedConflictError` still the governed-conflict class (K9's non-vacuity leg puts it in the "propagates unchanged" half); an ASSERT / coercion / unspecified rejection still EXACTLY the base `TxnDomainRejectionError` (§1.3 pin (c)'s controls, both raise sites); transport / exhausted contention unchanged (K4, keeps twin passthrough legs); `test_retry_seam.py` / `test_surreal_store.py` green on the reference.
4. **keeps**: `test_keeps_store.py` (incl. the fault-injection wrap pin — a bare `SurrealStoreError` at `keeps.execute_transaction` still surfaces `KeepStoreError`) and the REAL 8-way unique-key convergence.
5. **58's §HELD part 3 / am-6 (`_ROLLBACK_LOG_TIERS`) coexistence**: none of my pins reads `_log_rollback` or a log level; none of 58's pins (per am-6 §"Pin it like this") reads `_classify_engine_error`'s labels or `_domain_rejection_error`'s classes. File-level collision only (both edit `store/_txn.py`) — §FLAGS F-1, order in §10.
Receipts: §8.

## §2 Per-item table (am-32 §W order; file **A** = `test_fixwave_a28b_63c_i_a.py` (NEW), **B** = `test_fixwave_a28_63c_i_a.py`, **RS** = `test_retry_seam.py`, **19a** = `test_fixwave_a19a_63c_i_a.py`)
| §W | item / K-probe / MP | pin(s) | wrong build killed (mutation, §6) | receipt |
|---|---|---|---|---|
| 1 | (a)(b) + am-33's pin (c): the class, both raise sites, GENERATED over live shapes {record R, index U, table T, ASSERT} × {run_query (sdk), execute_transaction (txn)} — am-33's `{R,U}×{sdk,txn}` + its three controls `{T-sdk, T-txn, ASSERT-txn}` (+ ASSERT-sdk) | A `TestTheDriverTypesAnIdentityTakenRejection63cIAa28b::test_am32_1_3_ab_every_raise_site_types_exactly_the_identity_taken_rejection[<4 situations>-<2 paths>]` (8; identity-taken ⇒ the class, else EXACTLY the base; no raw value echoed) | MA2 (txn marker reworded: 1 red, run_query legs green — the paths are INDEPENDENT), MA3b (index marker removed), MA4 (class never built) | §6 |
| 1 | am-33 (a) pin the miss — the SDK does NOT type a unique-index collision (U-sdk = untyped `InternalError`, `details is None`; no index kind among the derived `AlreadyExistsError` kinds) | A `TestTheSdkDoesNotTypeAUniqueIndexCollision63cIAa28b::test_am33_KNOWN_BOUND_a_unique_index_collision_is_an_untyped_InternalError` (GREEN at 169925f by design; reds the day the SDK types it — the docstring names the re-open trigger verbatim from am-33) | — (a pin-the-miss: its "mutation" is an SDK upgrade) | §5 |
| 1 | (c) the discriminator, typed beats text, GENERATED over the SDK's `AlreadyExistsError` detail kinds (derived from its own source) × {engine wording, the other kind's wording} | A `TestTheTypedDiscriminatorDecidesOnTheRunQueryPath63cIAa28b::test_am32_1_3_c_the_unique_violation_class_iff_the_sdk_says_the_record_id_is_taken[<5 kinds>-<2 wordings>]` + `…_the_sdk_kind_domain_is_derived_and_non_vacuous` (constructed at unit level — the report says which: **unit**; the live Table DDL door IS reachable through `run_query` and is ALSO pinned live in row 1: `table-already-exists-run_query`) | MA1 (typed branch deleted: 5 reds, exactly the reworded legs) | §6 |
| 2 | RS-5 by class — K9 generated (`_CONFLICT_CLASS = TxnUniqueViolationError`, the declared deviation), K7 AST-equal, K2 / K4 AST-equal, K3 re-keyed (deviation D-2) | A `TestK9…::test_K9_create_outcome[<derived class>-<landed>]` (16) + `test_K9_the_derived_error_domain_is_non_vacuous` (am-32 §1.1 item 5 amended) · `TestK7…` · `TestK2…` · `TestK4…` · `TestK3…` | MA5 (RS-5 catches the base class — Reading A: 2 reds), MS1 (catches exhaustion in a Tuple), MA8 (keys on the engine text — K3 + K9), MA4 (K7) | §6 |
| 3 | keeps' CAS narrowed to the ONE class (R-6) — the keeps twin of K9 over the SAME derived domain + the REAL unique-key conflict | A `TestKeepsCasDecidesFromTheOneClass63cIAa28b::test_am32_1_2_keeps_returns_the_winner_iff_the_unique_violation_class_and_a_winner[<class>-<winner>]` (16) + `…the_REAL_unique_key_conflict_converges_eight_way` (8-way × 20) | MA6 (keeps catches broad = 169925f's door: exactly the 5 non-conflict × winner legs), MA3b / MA4 (the real 8-way) | §6, §7 |
| 4 | the guarded-CAS scanner (58 am-7: the DOMAIN + the PARTITION, FK-a28b-4 pick B) — DERIVED key (caught class resolved by import, Tuple elements included; a re-read = an awaited same-class method carrying a `SELECT` literal; guard = exhaustion cannot reach the handler, by `issubclass`) + both doors in the canonical set | RS `_discover_cas_handlers` (the domain) → `_discover_guarded_cas_handlers` (DOORS: exhaustion can reach) + `_discover_typed_cas_catches` (SAFE-BY-TYPE); `_GUARDED_CAS_DOORS` gains **`floor_calibration/store.py::record_measurement` — found by the derived key on its first run, unlisted before it**; NEW `_TYPED_CAS_CATCHES` = {`agents.py::register`, `keeps.py::get_or_create_keyed`}; NEW `test_the_typed_catch_enumeration_matches_the_canonical_set_and_the_partition_is_complete` (exact both ways + disjoint + union == domain); F-4 re-key (U-9) | MS1 (RS-5 catches a Tuple naming exhaustion → it becomes a DOOR: both exact-set pins red), MA6 (keeps catches broad → both exact-set pins red), MS2 (record_measurement drops its tuple guard → the guard + structural legs red for that door, 58 am-7 §3 item 3's static half) | §6; RED@169925f §5 |
| 5 | FK-ADV-2 Reading A — `None` iff the read was gated off ∀ outcomes; describe names every measured non-zero problem | B `TestAFieldIsNoneIffItsReadWasGatedOff63cIAa28b`: `…_a_field_is_None_iff_its_read_was_gated_off[<3 tables>-<4 shapes>]` (12, GENERATED) + `…_the_read_partition_covers_every_field` (completeness) + `…_a_verb_level_refusal_on_message_names_every_measured_problem` + `…_one_more_half_pair_row_moves_its_count_and_sentence[agent\|message]` + `…_the_message_leg_refusal_serves_measured_agent_zeros` + `…_success_serves_the_measured_object[agent\|message]` | MB1 (verb omits message problems), MB2 (am-31 literal: message fields `None` on a verb refusal), MB3 (am-31 control literal: agent fields `None` on the leg refusal) | §6 |
| 6 | am-31 fold — eight fields via `model_fields`; pin (1) BY ANNOTATION + completeness | B `TestTheMeasuredCountsAreTypedFields63cIAa28`: shape pin (8 ruled names + annotations) · `test_am32_every_field_has_a_perturbation_by_annotation` · `…_pin1_every_field_is_exercised_by_some_population` · served-fields[5 pops] · pin (1)[19 generated (field, population) cases] · pin (2)[4 pops + RS-1] · `_assert_complete` on every population | MB4 (owner sentence keyed on the operator object), MB5 (foreign N not from the field), MF1 (a third field TYPE — completeness reds), MF2 (the enum grows — the owner-sentence table's completeness reds) | §6 |
| 7 | C2 — K8 (+ shapes) and K1 (replacing RS-3's 3-method spy) | A `TestK1…` (AST-equal) · `TestK8…` (AST-equal) · `TestC2EveryForeignShapeIsDeniedWithZeroRegistryQueries63cIAa28b::test_am32_C2_foreign_shapes_x_probe_kinds[<4 shapes>]` (3 foreign + the householded-in-THIS-keep control) · B RS-3 re-keyed to the seam spy (DUAL U-1) | MC1 (gate skipped for ANY keeper: K8 + `keeper-of-another-keep` red, `householded-in-another-keep` green — the shapes discriminate) | §6 |
| 8 | C1 — K6 with K5 as legs; completeness from `_REGISTRY_CLASSES` | A `TestK5…` · `TestK6…` (AST-equal) · `test_am32_C1_every_registry_class_is_provoked_post_mint_or_exempt_with_evidence` (the legs' parametrisation READ from the collected marks == `_CAUSE_CLASS`; ∪ exemptions == a28's derived `_REGISTRY_CLASSES`) · `test_am32_C1_evidence_an_invalid_identity_is_refused_before_any_mint` | MD2 (a new `AgentRegistryError` subclass → the completeness pin reds) | §6 |
| 9 | R-1 (post-mint refusal count == `_ROUNDS`) · R-2 (retired name gone) · R-3 (tokenless winner via the handler) · R-4 (corpse) | B RS-2 (`_arm_per_call_mint_marker` + `_minted_then_outcome`, a per-task ContextVar) · A `test_am32_R2_the_created_only_flag_is_gone_from_the_package` (bare pattern, package-wide, positive control) · B sequential race `[tokenless-winner-control]` · 19a lines 14–16 / 582–583, B module comment | ME1 (handler serialised → no post-mint refusal → RS-2's R-1 leg reds ALONE), MD3 (the name re-mentioned in a docstring) | §6, §7 |

## §3 DUAL — every pin deleted, re-keyed or re-worded (each carries an in-place comment)
| # | site | old | new | virtue | verdict |
|---|---|---|---|---|---|
| U-1 | B RS-3 `…zero_registry_reads` | `_count_calls` spies on `_select_row` / `preflight` / `register` (a 3-method hand-list) + the mint | the registry's ONE seam spy (`_spy_registry_queries` on `AgentRegistry._query`, now defined in B verbatim from §A.2 and imported by A) + the mint counter | "ZERO registry reads before the gate" | PRESERVED-with-pin, WIDENED (am-32 §4 C2: every one of the three methods rides `_query`; a read through any other method — W3a/b/c — is now seen). Bound (am-32's own): a read on ANOTHER connection is outside the seam. |
| U-2 | B RS-2 non-vacuity | `refusal_rounds >= 1` (ANY refusal, pre-mint preflight refusals included) | `post_mint_refusal_rounds == _ROUNDS` (a register that raised AFTER its own mint returned, every round) | "the race ran" | PRESERVED, STRENGTHENED (am-32 §5 R-1 — the assertion now performs the check the docstring promised) |
| U-3 | B sequential race `[tokenless-winner-control]` | X' = a DIRECT registry register (`ctx.agent_registry.register`) | X' = a HANDLER register with an empty-subject token (`holder["email"] = None` around `ctx.comms(action="register")`) | "the ownerless winner leaves K kept by P, never deleted" (the β bound) | PRESERVED, re-keyed to a real pin-the-miss (am-32 §5 R-3): when β refuses the handler's ownerless register, the fixture's "X' must WIN" reds with a KNOWN-BOUND message |
| U-4 | B shape pin `test_am30_the_counts_model_has_exactly_the_ruled_fields` | exactly 6 names, `[None]*6`, `list(range(6))` | the 8 ruled names + their ruled ANNOTATIONS (`_RULED_FIELD_SPEC`); values derived from the annotations | "the model carries exactly the ruled fields" | PRESERVED, WIDENED to am-31 (am-32 §3 F-1). The spec dict is read ONLY by the shape pin (deriving a shape from the model it checks is a tautology — §DEVIATIONS D-4) |
| U-5 | B `_POPULATIONS` / `_RS1_COUNTS` / `None_means[clean-memory-proceeds]` | six-key dicts | eight-key dicts, each `_assert_complete`d against `model_fields` | "the served fields ARE the measured counts" | PRESERVED; am-31's two fields added with measured values (F-2) |
| U-6 | B pin (1) `test_am30_pin1_perturbing_a_field_moves_the_reason[<field>]` | parametrised over the hand-list `_RULED_COUNT_FIELDS`, int `+ _PERTURBATION` only, a population loop inside | `[<field>-<population>]` GENERATED (collection-time from `model_fields` when the model exists), moved BY ANNOTATION (int / Literal swap); the "exercised" leg split out as `…_every_field_is_exercised_by_some_population`; + an "only this field moved" leg | "a reason derived from the served model moves with it" | PRESERVED-with-pin, re-keyed (am-32 §3 F-3); ids CHANGED (a DUAL re-key, not AST-equal to a28) |
| U-7 | B pin (2) | ⊆ strips row-id samples + citations; ⊇ over the 6 | + the principal-id sample shape `(first N named`; ⊇ via `_states_its_count` (the owner count only where the ruled sentence names it — FK-a28b-2) | "every integer is a field value / every measured count is stated" | PRESERVED (am-31: "pin (2) holds unchanged"); the unclassified population is EXCLUDED from pin (2) (FK-a28b-3) |
| U-8 | 19a module docstring lines 14–16, `…EVERY_driven_register…` docstring (582–583); B section comment (143–148) | "created-only compensation for the race" / "a compensated injected race" / "tokenless (ownerless, direct-registry) winner" | prose follows the mechanism (compensation DELETED; the tokenless winner through the handler) | — | prose only (am-32 §5 R-4; P6 corpse sweep §5) |
| U-9 | RS `TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_transactional_doors_never_re_read_after_exhaustion` | a HAND list of 4 doors (`findings-transition`, `findings-annotate`, `tasks-transition`, `TASKS-SUPERSEDE-unpinned`), guards found by `ast.Name == TxnContentionExhaustedError` | parametrised over `_GUARDED_CAS_DOORS` (ids = the door keys), guards read through the SAME `_caught_classes` (Tuple elements included); a listed door must be REACHABLE by exhaustion (else it belongs in `_TYPED_CAS_CATCHES`) | "a guard must RE-RAISE, never re-read" | PRESERVED-with-pin, WIDENED (58 am-7 §3 item 1): the four old doors still checked; `record_measurement`'s Tuple guard now covered; ids CHANGED |
| U-10 | RS `_GUARDED_CAS_DOORS` + the enumeration pin | ONE set (the 5 doors) | the DOOR half of the partition (+ `record_measurement`) beside a NEW `_TYPED_CAS_CATCHES` (RS-5, keeps) | "every guarded CAS door is known" | PRESERVED, SPLIT (58 am-7 §0 rows 1a/1b; FK-a28b-4) |
No pin was DELETED. No production-behaviour pin was weakened.

### P6 corpse sweep — BARE, anchor-free patterns over `loremaster/tests/*.py` (awk, grep hook-blocked): `compensat|created-only|created_only|minted_by_this_call|left behind|#4b|delete-keep --keep`, case-insensitive — every hit, individually
| hit (file:line at the a28b commit) | verdict |
|---|---|
| 19a:15 (module docstring, rewritten) | FIXED (R-4) — now says the compensation was DELETED |
| 19a:321 DUAL comment "NO LONGER compensated" | current |
| 19a:456–457 spy docstring DUAL | current |
| 19a:590, 592 (docstring of `…EVERY_driven_register…`, the DUAL sentence) | current (the "a compensated injected race" sentence above them is FIXED, R-4) |
| 19a:635–637 DUAL comments | current |
| 19a:832 deleted-pin DUAL comment | current |
| 19b:21, 23 module docstring DUAL | current |
| 19b:80 `test_KP1_…_is_never_compensated` (name) | current (true) |
| 19b:603–605, 612 DUAL block | current |
| B:13, 111, 145, 149 (149 = the R-3 re-worded section comment), 214, 222, 270, 277 | current (describe the removal / R-1 / R-3) |
| A:20, 832, 1034, 1062, 1068, 1072–1074, 1085 | current (K5's class name `…Compensates`; the R-2 pin itself) |
No ASSERTION pins the retired mechanism; the R-2 pin now REQUIRES its deletion from production.

## §4 DEVIATIONS (each with its kill re-proven, §6)
- **D-1 `_CONFLICT_CLASS` (am-32 §1.1 item 5's declared deviation, bound dynamically).** §A.2 wrote `_CONFLICT_CLASS = TxnDomainRejectionError`; am-32 rules `TxnUniqueViolationError`. A static import of the unbuilt class would make the file uncollectable at `169925f` (a collection ImportError proves nothing), so A binds `_CONFLICT_CLASS = vars(_txn_module).get("TxnUniqueViolationError", _UnbuiltUniqueViolationError)` — the stand-in is NOT a `SurrealStoreError`, so at `169925f` the non-vacuity pin reds by the class's NAME and nothing passes for it. The static reference lives in the `TYPE_CHECKING` block (currency). Kill re-proven: MA5 (Reading-A build) → exactly `K9[TxnDomainRejectionError-row-landed]` + `K9[TxnGovernedConflictError-row-landed]`.
- **D-2 K3 re-keyed to the class.** Under Reading B the conflict IS the class, so §A.2's forged base `TxnDomainRejectionError` would now (correctly) propagate and K3 would red on a correct build. The forge raises `_CONFLICT_CLASS(...)` with a REWORDED message and a non-SDK `RuntimeError` cause; the property (class, never text) is unchanged. Kill re-proven: MA8 (RS-5 keys on `"already exists" in str(__cause__)`) → K3 + `K9[TxnUniqueViolationError-row-landed]`.
- **D-3 `test_K9_the_derived_error_domain_is_non_vacuous` amended per am-32 §1.1 item 5** (contains the conflict class AND ≥1 non-conflict `TxnDomainRejectionError` sibling, `TxnGovernedConflictError`). RED@169925f for the ruled reason (§5).
- **D-4 the shape pin keeps ONE spec dict** (`_RULED_FIELD_SPEC`, 8 names → annotations). am-32 §3 says "no hand-list of names anywhere in the contract"; a SHAPE pin must compare the model against the RULING, and a shape derived from the model it checks is a tautology. Every behaviour pin iterates `model_fields`; every population is `_assert_complete`d against `model_fields`; pin (1)'s cases are generated from `model_fields` at collection time when the model exists (the spec is the collection-time fallback at `169925f` only). Written here for the adversary to grade.
- **D-5 lint-clean rewraps of the AST-equal probes** — `ruff format` only (AST-invariant), plus ONE `# noqa: PLC0207` where `ruff --fix` had rewritten `statement.split()[0]` → `split(maxsplit=1)[0]` inside `_arm_keep_write_spy` (semantically equal, AST-different — reverted to the §A.2 text). AST receipt §A.3: 15 symbols EQUAL, exactly the 3 declared DIFFs (D-1/D-2/D-3), control self-compare EQUAL.
- **D-6 `_spy_registry_queries` lives in B** (verbatim §A.2 text) and A imports it — so RS-3's DUAL re-key (U-1) and K1/K8 share ONE helper (DRY) with no import cycle.
- **D-8 two rulings landed MID-FOLD and are folded:** amendment 33 (`f66a190`, FK-a28b-1 → Reading 1 + the rename `TxnRecordExistsError` → `TxnUniqueViolationError` + the U-sdk pin-the-miss) and packet 58 amendment 7 (`01565f9`, the scanner: ONE set first, the F-4 re-key). The first mutation batch ran on the pre-rename contract; **the whole batch was RE-RUN on the renamed contract** (§6 is run 2; run 1's receipts are summarised there), and the 20-consecutive and SAT runs are on the final files.
- **D-7 test_retry_seam.py registered in the a28 bound** — a large shared file; the masking bound is written INTO the registry comment (§9).

## §5 RED @ `169925f` (production)
Main tree, HEAD `cc5e395` (the am-33 / 58 am-7 commits are docs only); 63c production byte-identical to `169925f` (`git diff --quiet 169925f -- <the six 63c files>` ✓; the tree's only production drift is #503's uncommitted `testing/loopback.py`, not 63c). Final files, under the watchdog (`red_main_3`): `COLUMNS=4000 pytest -n 8 --tb=line -rfE` over A + B + 19a + 19b + RS → **107 failed, 816 passed** (A 24 · B 76 · 19a 2 · 19b 2 · RS 3) on the ONE-set scanner; after the FK-a28b-4 partition the RS reds are **2** — the door enumeration (keeps is a DOOR at `169925f`: broad catch + tuple guard) and the typed-catch enumeration + completeness (RS-5 absent, keeps not typed) — re-run on the final RS file: `2 failed, 13 passed` for the scanner classes. **Final RED@169925f (`red_main_4`, the final files, under the watchdog): `106 failed, 814 passed`** (A 24 · B 76 · 19a 2 · 19b 2 · RS 2) — programmatically IDENTICAL to the SAT's red-at-base-only set (§8). The U-sdk pin-the-miss is GREEN at `169925f` by design. Every red, by reason:
| n | pin(s) | served failure head | right reason? |
|---|---|---|---|
| 4 | A (a)(b) identity-taken × 2 paths | `… an identity-taken rejection must raise TxnUniqueViolationError …; got TxnDomainRejectionError` | yes (unbuilt class) |
| 2 | A (c) `Record-*` | `AlreadyExistsError(kind=Record…) … must raise TxnUniqueViolationError` | yes |
| 1 | A K9 non-vacuity | `TxnUniqueViolationError must be a SurrealStoreError subclass in loremaster.store._txn: [...]` | yes |
| 1 | A K7 | `TxnDomainRejectionError: SurrealDB agent query rejected … (unspecified rejection)` — the loser gets the raw engine error | yes (RS-5 unbuilt) |
| 1 | A K3 | `_UnbuiltUniqueViolationError: … (reworded)` | yes (the stand-in propagates — no class to catch) |
| 5 | A keeps twin `[<non-conflict domain class>-winner-landed]` | `… keeps must serve KeepStoreError after ONE create — never the winner …` | yes (169925f keeps returns a coincidental winner — the DUAL-dropped behaviour) |
| 1 | A R-2 | `… minted_by_this_call survives at ['keeps.py:114', …]` | yes |
| 2+2 | A K1, K6-foreign | `AgentIdentityConflictError: agent 'worker' … role ```secretrole```` (served to carol) | yes (preflight before the gate) |
| 1+3 | A K8, C2 foreign shapes ×3 | the four probes are NOT all `GovernedDenied` (the role/spawned_by/retired leak) | yes |
| 3 | A K5 ×3 | `([], ['keep:…'])` — the session keep deleted | yes (the compensation) |
| 34 | B am-30/31/32 counts + gating pins | `loremaster.governed.MigratePreconditionCounts does not exist — amendments 30/31 …` | yes (unbuilt) |
| 15 | B served / pin (2) / None / gating … | `MigrateGovernedResult has no \`preconditions\` field — amendment 30 …` | yes |
| 16 | B A2 | `DID NOT RAISE SurrealStoreError` | yes (a28, unchanged) |
| 11 | B RS-2, sequential ×2, RS-3, ORDER, RS-5 ×2, FORK-1, FORK-2, A5, A4 docstring | as a28 §5 (e.g. RS-2 "6/20 rounds left agent rows whose scope does not resolve") | yes (a28, unchanged) |
| 2+2 | 19a EXECUTES golden + runtime property; 19b KP2/KP3 | as a28 §5 | yes (a28, unchanged) |
| 2 | RS door enumeration + typed-catch enumeration/completeness | `doors with NO entry: ['keeps.py::get_or_create_keyed']` / `entries naming a catch that is not found (or is now a DOOR): ['agents.py::register', 'keeps.py::get_or_create_keyed']` (the keeps + floor-calibration handlers WERE found — the new key's reach at HEAD) | yes (RS-5 unbuilt, keeps not narrowed) |
GREEN at `169925f` by design: the U-sdk pin-the-miss, the 4 NOT-identity driver legs (the base class — required-green), (c)'s 8 non-`Record` legs, the SDK-kind non-vacuity leg, K2 / K4 (169925f re-raises), K9's 16 generated cases (169925f catches nothing — every forged class propagates; the domain lacks the conflict class, which the non-vacuity pin reds), K6 race legs (169925f never deleted a FOUND keep), the keeps real 8-way and its `TxnUniqueViolationError`/passthrough/no-winner legs, C1 completeness + evidence, the gating pin's 4 target-undefined raises, RS's other 12 guarded-CAS legs.

## §6 Mutation proofs — declare-then-diff, BOTH ways (`scripts/mutation_proof.py` in the REFERENCE copy)
Declared sets: `mut/declared_a28b.py` (§A.4): first written `2026-09-26 19:02:07` (before run 1, MA1 at `19:02:36`); MA3b appended `19:05:52` (after MA3's degenerate run, before any MA3b run); ME1 appended before its run; run-2 additions (targets + MS1's structural leg + MS2) at `20:00:15`, before run 2 (`20:00:29`); MS1 / MA6 RE-DECLARED at `20:23:42` for the partitioned scanner (FK-a28b-4), before their run-2c runs (`20:23:54`). Ids verified against `--collect-only` by the driver (§A.5: an uncollected declared id aborts that mutation — never a pass). Targets: A + B + the two RS scanner classes (178 tests after the partition), `-n 8` (run 2) / `-n 4` (run 2c); ME1 only the three race pins (its lock would deadlock the nested-register fixtures). Every run restored byte-exact (the tool's md5 = `ref_prod_backup2/MD5SUMS`, the renamed reference). `loremaster.__file__` in the copy: `…/scratchpad/ref/loremaster/loremaster/__init__.py` (scratch_copy provenance ✓).

**Run 2 is the receipt (the FINAL, renamed contract).** Run 1 (pre-rename, ONE-set scanner, 168 targets) is summarised at the end. ⚠ Two watchdog kills (host MemAvailable 15.6 / 15.0 GB, foreign tenants) interrupted run 2 mid-MD3 and run 2b mid-MD3: **each left MD3's docstring mutation STRANDED in the reference's `keeps.py`** (mutation_proof's restore is not signal-safe) — both times caught by an md5 diff against the content backup and restored byte-exact from it (`ref_prod_backup2`, the renamed reference), BEFORE any later run; filed **#509**. MD3 then re-ran cleanly in run 2c.
| mut | wrong build | declared | observed (run 2 / 2c) | verdict |
|---|---|---|---|---|
| MA1 | the typed `AlreadyExistsError` branch deleted (text decides on the run_query path) | (c) `[<5 kinds>-reworded]` | 5 failed / 173 | **HELD** |
| MA2 | the transactional RECORD marker pair reworded | (a)(b) `[record-id-collision-execute_transaction]` | 1 / 177 | **HELD** — the run_query record leg stayed GREEN: typed ≠ text, the paths are INDEPENDENT (am-33 §(a): "R-txn RED, R-sdk GREEN") |
| MA3b | the INDEX marker pair removed (1-tuple kept) | (a)(b) unique-index × BOTH paths, keeps REAL 8-way, B RS-2, B RS-5 handler | 5 / 170 | **HELD** — am-33 §(a): "U-sdk AND U-txn RED (no typed leg exists for U)"; and a literal-am-32 build breaks keeps' real CAS + the whole handler race |
| MA4 | `_domain_rejection_error` never builds the class | 11: (a)(b) ×4, (c) Record ×2, keeps 8-way, RS-2, RS-5 ×2, K7 | 11 / 167 | **HELD** — ONE class, both CAS doors fail together (R-6 proven by mutation) |
| MA5 | RS-5 also catches the BASE class (Reading A) | K9 `[TxnDomainRejectionError-row-landed]`, `[TxnGovernedConflictError-row-landed]` | 2 / 176 | **HELD** |
| MA6 | keeps catches broad (the 169925f door, tuple-guarded) | door enumeration, typed enumeration, keeps twin `[<5 non-conflict>-winner-landed]` | 7 / 168 | **HELD** (re-declared for the partition) |
| MS1 | RS-5 catches `(TxnUniqueViolationError, TxnContentionExhaustedError)` | door enumeration, typed enumeration, K9 `[TxnContentionExhaustedError-row-landed]` | 3 / 172 | **HELD** (re-declared) — the scanner reads Tuple elements; the handler moves halves |
| MS2 | `record_measurement` drops exhaustion from its tuple guard | `guard[record_measurement]`, F-4 structural `[record_measurement]` | 2 / 173 | **HELD** — 58 am-7 §3 item 3's static half |
| MA8 | RS-5 keys on `"already exists" in str(__cause__)` | K3, K9 `[TxnUniqueViolationError-row-landed]` | 2 / 176 | **HELD** — D-2's re-keyed K3 kills the text-keyed build |
| MB1 | the verb-level refusal omits the message problems | verb-level pin, one-more `[message]` | 2 / 176 | **HELD** |
| MB2 | am-31 literal: message fields `None` on a verb-level refusal | verb-level pin, one-more `[message]` | 2 / 176 | **HELD** |
| MB3 | am-31 control literal: agent fields `None` on the message-LEG refusal | served `[P_message]`, pin (1) ×4 `[*-P_message]`, pin (2) `[P_message]`, the leg-refusal pin | 7 / 171 | **HELD** |
| MB4 | the owner sentence keyed on "operator object is None", not the enum | pin (1) `[owner_classification-P_unclassified]` | 2: + `[owner_classification-P_mixed]` | **FAILED — prediction miss, EXTRA kill** (both runs): P_mixed's swap target is the NEXT member, `unclassified`; with an operator resolved the mutant falls to the mixed branch → the reason does not move. A correct kill I did not predict (never re-declared: a set written after seeing is the tautology) |
| MB5 | the `foreign` N rendered from a private `len(...)` | pin (1) `[distinct_owner_principals-P_foreign]` | 1 / 177 | **HELD** |
| MC1 | the gate skipped for ANY keeper | K8, C2 `[keeper-of-another-keep]` | 2 / 176 | **HELD** — `householded-in-another-keep` stayed green: the shapes DISCRIMINATE |
| MD2 | a new `AgentRegistryError` subclass | C1 completeness | 1 / 177 | **HELD** |
| MD3 | the retired name re-mentioned in a keeps docstring | R-2 | 1 / 174 | **HELD** (run 2c) |
| ME1 | the handler's register critical section serialised (no race) | RS-2 | 1 failed, 2 passed | **HELD** — `only 0/20 rounds met a POST-MINT refusal` (the R-1 leg, alone) |
| MF1 | a third field TYPE (`note: str \| None`) joins the model | 42 (by rule, `_mf1_declared`) | 42 / 133 | **HELD** — completeness reds wherever a population must cover `model_fields` |
| MF2 | the classification enum grows a member | shape pin, perturbation-completeness | 2 / 173 | **HELD** |
**Summary (run 2, final contract): 20 wrong builds, 19 HELD exactly + 1 (MB4) killed with one extra correct red — 20 of 20 killed.** Run 2's MA1–MD2 ran before the FK-a28b-4 partition; none of them touches a CAS handler's class, so the partition cannot move their sets (MA5 / MA8 keep RS-5 disjoint from exhaustion). Run 1 (pre-rename): the same 19 of 19 final builds killed + MA3 DEGENERATE (my edit left a bare 2-string tuple — the classifier iterated CHARACTERS; re-declared as MA3b) + the same MB4 extra kill; logs `mut/run1_logs/`. Not replayed: the adversary's W-builds (am-32: the AST-equal probes carry their own grading; CLAUDE.md 2026-09-26: the author never replays a grader's builds).

## §7 Concurrency receipt
- **Reference, FINAL files, 20 consecutive SERIAL invocations** (`conc20_a28b.sh`, §A.6, `-n 4`): `run 1 … run 20: 4 passed` each — **ALL 20 CONSECUTIVE GREEN** (a first 20/20 also on the pre-rename files). Each = B RS-2 (20 rounds × 8-way, incl. the R-1 leg: every round met a post-mint refusal) + B RS-5 handler (20 × 8) + B RS-5 registry (20 × 8) + A keeps REAL unique-key (20 × 8) — R-1's `== _ROUNDS` held in 800/800 rounds across the two batches. ⚠ The two conc20 batches ran WITHOUT the watchdog wrapper (short `-n 4` runs, host at 24 GB) — disclosed.
- Checkpoint `169925f`: RS-2 red (6/20 stranded rounds in the §5 run), RS-5 ×2 red (raw `TxnDomainRejectionError`); the keeps real 8-way GREEN at `169925f` (its broad catch converges) and RED on a literal-am-32 build (MA3b).

## §8 SAT — the contract is satisfiable by a known-correct build (full suite, ONE tree both ways)
- **Trees:** `ref` = `./scripts/scratch_copy.sh` copy of the main tree + my reference build (a28's `reference_fix.patch` + the §A.2 interdiff; renamed per am-33); `base` = `ref/scripts/scratch_copy.sh` copy OF `ref` with the six 63c production files `git checkout`-ed (each `git diff --quiet 169925f` ✓). `diff -rq` (excluding caches/venv/.git): the two trees differ in EXACTLY the six 63c production files; tests byte-identical (the final a28b / a28 / a19a / retry_seam files synced into both). Provenance: `ref` → `…/scratchpad/ref/loremaster/loremaster/__init__.py`, `base` → `…/scratchpad/base/loremaster/loremaster/__init__.py` (scratch_copy's own assertion, both).
- **Runs** (`-n 4`, `COLUMNS=4000 --tb=line -rfE`, both under the operator-ruled watchdog `guarded_a28b.sh`; 2026-09-26 20:42–21:30, in parallel on a quiet host):
  - **base (checkpoint production): `448 failed, 11783 passed, 63 skipped, 3 xfailed` (47m38s)**
  - **ref (my reference): `342 failed, 11893 passed, 63 skipped, 3 xfailed` (46m56s)**
- **Both-way diff** (`sat_compare.py`, §A.10 — ids read from pytest's own summary section, split at the first `" - "`; 448 = 342 + 106 and 342 = 342 + 0 reconcile): **red on the reference ONLY: 0** · **red at base, green on the reference: 106 — IDENTICAL to the §5 RED@169925f set** (programmatic set equality ✓: A 24 · B 76 · 19a 2 · 19b 2 · RS 2) · **red in both: 342**, adjudicated by file:
  | files | reds | owner |
  |---|---|---|
  | `test_supersede_reanchor_58.py` 44 · `test_reanchor_58_r2_rulings.py` 27 · `test_task_guarded_shell_58.py` 15 · `test_reanchor_58_r2_probes.py` 12 · `test_reanchor_58_r2_cas_runtime.py` 6 · `test_task_claimable_partition_58.py` 5 · `test_reanchor_58_r2_am2.py` 3 · `scripts/test_forgery_door_sweep.py` 3 · `test_reanchor_58_r2_scale.py` 2 · `test_blocks_edge.py` 1 · `test_task_read_surface.py` 1 | 119 | packet 58's contract (r1 + r2) — `packet-58-contract` bound |
  | `test_governed_substrate_64b.py` 26 · `test_findings_migrate_64b.py` 26 · `test_findings_governance_64b.py` 24 · `test_findings_identity_64b.py` 22 · `test_findings_schema_64b.py` 17 · `test_findings_enforcement_64b.py` 4 | 119 | packet 64b-i's contract (untracked) — `packet-64b-i-contract` bound |
  | `test_comms_footer.py` 76 · `test_mcp_server.py` 28 | 104 | 64b-i's two CONVERTED suites (uncommitted, `ImportError: cannot import name 'arm_finding_identity' from '_finding_fakes'` — 64b §HELD part B) — same bound |
- **Every shared red's served text compared across the trees** (`sat_messages.py`, §A.11 — normalised for per-run ids, DB names, timings and the tree path): 342 shared, 0 with an empty message, **5 differing — each adjudicated:** (1) `test_findings_migrate_64b…CONTROL_without_the_trap…[finding]` and (2) `…trap_refuses_byte_inert…[memory]` — the repr gains the am-30/31 `preconditions` field (the reference's model); both fail for 64b's own unbuilt reason on BOTH trees (`finding` not supported / `memory` proceeds past owned-but-unscoped rows); (3) `test_governed_substrate_64b…the_only_production_Resource_constructor` — the same pre-existing site `governed.py::authorize_guarded`, line 493 → 511 (the am-30/31 model inserted above it); (4) `test_reanchor_58_r2_rulings…heal_READS…` — a random websocket key; (5) `test_supersede_reanchor_58…direct_dependents…` — random ids. **No shared red changes shape because of the 63c build. 63c-attributable reds on the reference: 0.** No `#503` shape (`test_migration_wire`) appeared in either run; no #486 shape.
- **Targeted SAT** (before the full run; the four changed files + every required-green suite of §1, 16 files): **2651 passed, 0 failed** on the reference (`ref_targeted_2`, 7m02s).
- **Killed attempts, disclosed (F-8):** two `-n 12` (base) and two `-n 4` (base + ref, run in parallel) full-suite attempts were SIGKILLed by the watchdog at 30 s – 7 min (host MemAvailable 14.7–15.7 GB from foreign tenants); no counts were taken from them (`sat_old/`, `sat_*_killed_*`).

## §9 Currency
- **Bound UPDATED, never a second one:** `packet-63c-i-a-a28-contract` (`scripts/pending_contracts.yaml`) now also owns `test_fixwave_a28b_63c_i_a.py` and `test_retry_seam.py` via the runtime-inert `TYPE_CHECKING` reference to `loremaster.store._txn.TxnUniqueViolationError` (mypy at the final tree: EXACTLY one `attr-defined` line per new file, symbol-named; a28 / a19a / a19b keep the am-30 pair); owner / trigger / ruling lines extended to am-31/32/33 + 58 am-7. The masking bound of registering the shared `test_retry_seam.py` is written into the entry (D-7 / F-3). Staged as HEAD + ONLY this entry (§A.8 — the working copy holds no other packet's hunk for this file at commit time, but the stager is the rule). `--verify-registry`: parses.
- **Worker cap (the brief's question): the gate REFUSES a forwarded `-n` (#503, committed `f21a885` / `e53b837`) and resolves `-n {workers}` from the fleet policy itself** — so neither the forwarded cap nor my override was possible; I **waited for quiet** instead (the quiet-gated `currency_runner.sh`, §A.12, under the operator-ruled watchdog). Attempt 1 (21:32) was SIGKILLed by the watchdog at 36 s (host 13.5 GB); **attempt 2 (21:33:51 → 21:49:11) completed**:
```
  typecheck    RED_ORPHANED — 9 residual(s) with NO owner
  ruff         GREEN
  pytest       RED_ORPHANED — 79 residual(s) with NO owner
CURRENCY   : FAIL — RED with nobody's name on it: typecheck, pytest
```
- **Every orphan, adjudicated:** pytest — **79 / 79 in packet 58's r3 contract, UNTRACKED and in flight** (`test_reanchor_58_r3_convergence.py` 41 · `_tiers.py` 16 · `_am6.py` 8 · `_cas_seam.py` 6 · `_probes.py` 6 · `_relate.py` 2 — not yet in any bound; 58's bookkeeping, flagged to the lead); **a28b-attributable: 0** (no id in A / B / 19a / 19b / RS). typecheck — 7 in the same six 58-r3 files, and **2 were MINE**: `test_retry_seam.py` `_discover_cas_handlers`'s local `doors` annotation still named the 3-tuple after the FK-a28b-4 partition (a real defect of my edit, caught by the gate). **Fixed** (`dict[str, tuple[str, int, bool, bool]]`; annotation-only — no runtime change, so the SAT / mutation / pytest receipts stand) and **re-proven**: `pending_contract_gate.py --currency --legs typecheck` → `RED_ORPHANED — 7`, all seven in the 58-r3 files, **a28b-attributable 0** (a leg subset is never a deploy receipt — stated; the pytest leg is attempt 2's, the ruff leg GREEN there and `ruff check` clean on my four files after the fix).

## §P1c — reach table for every new ∀ pin / instrument
| instrument | set it should cover | reach derived or hand-list? | coverage a checked variable? | effect or proxy? | proven by mutation? |
|---|---|---|---|---|---|
| A (a)(b) situations × raise sites | every engine situation that IS / is NOT identity-taken × both driver raise sites | the two raise sites are the driver's ONLY two (`run_query`, `_run_verified_transaction` — `_domain_rejection_error`'s docstring); the 4 situations are a hand table of LIVE engine facts (probed, §A.1) | no — ⚠ BOUND: a new engine identity shape (e.g. a relation's `IN/OUT` unique edge) is not in the table; re-open trigger: the first new UNIQUE index or deterministic-id CREATE on a table whose conflict is handled as a CAS | EFFECT (the raised class) | MA2, MA3b, MA4 |
| A (c) SDK kinds | every `AlreadyExistsError` detail kind | DERIVED from the SDK's own source (`_detail_field(self.details, "<Kind>", …)` per property) + a non-vacuity leg | yes (a new SDK kind joins unedited) | EFFECT | MA1 |
| A K9 / keeps twin | every store-error class the CREATE / create txn can raise | DERIVED (`vars(loremaster.store._txn)` subclasses of `SurrealStoreError`) | yes — non-vacuity requires the conflict class + a non-conflict domain sibling + transport | EFFECT (served outcome, CREATE count) | MA4/MA5/MS1/MA8 (K9), MA6 (twin) |
| A keeps real 8-way | the engine's REAL unique-key conflict | one live construction, 8-way × 20 | n/a (a construction, not a domain) | EFFECT | MA3b, MA4 |
| A C2 shapes | the principal's relation to THIS keep | hand table of 4 (am-32 §4 C2's enumeration of the gate's inputs) + the not-foreign control | no — BOUND: a fifth relation (e.g. a pending household invite, if one is ever modelled) is outside; re-open trigger: the day `KeepStore` gains a membership state other than keeper/member | EFFECT (served class/text + zero seam queries) | MC1 (the shapes discriminate: keeper red, householded-elsewhere green) |
| A K1/K8 seam spy | every registry read | the ONE seam `AgentRegistry._query` (every registry read rides `run_query` through it) | the positive control proves the spy SEES reads | EFFECT-ish (queries issued) | adversary's W3a/b/c (not replayed — am-32: AST-equal probes carry their grading) |
| A C1 completeness | every `AgentRegistryError` class | DERIVED (a28 `_REGISTRY_CLASSES`) vs provoked ∪ evidenced-exempt; the legs READ from the collected marks | yes | n/a (completeness) | MD2 |
| A R-2 retired name | every production `.py` | `rglob` of the package + positive control (`keeps.py` scanned, >10 files) | yes | text (a BARE pattern — prose included, by design) | MD3 |
| B gating pin | table × store shape × field | tables = the three leg tables; shapes = the am-32 four; fields = `model_fields` via a NAME-SUFFIX partition (`*_messages` → the message read) with its own completeness pin | partition: yes; tables/shapes: hand (am-32's enumeration) | EFFECT (served `None`-ness) | MB2, MB3, MF1 |
| B pin (1) | (field, population) where the field is measured and named | GENERATED from `model_fields` (collection time) × `_ALL_POPULATIONS`; "every field exercised" completeness pin | yes | EFFECT (served field + reason) | MB3, MB4, MB5, MF1 |
| B am-31 completeness | every field annotation; every classification member | DERIVED (`typing.get_args` over the model) | yes | n/a | MF1, MF2 |
| A U-sdk pin-the-miss | the SDK's typing of an index collision | the live U shape + the derived AlreadyExists kinds | n/a | EFFECT (the cause's class/kind/details) | n/a — reds on an SDK change (its re-open trigger) |
| RS F-4 structural pin (re-keyed) | every canonical door's guard chain | `_GUARDED_CAS_DOORS` × the SAME `_caught_classes` | the canonical set's exactness is the enumeration pin | STRUCTURAL | MS1, MS2 |
| RS scanner (repaired) | every handler that catches a store error and re-reads | caught classes RESOLVED BY IMPORT (Name / Attribute / Tuple elements); "re-read" = an awaited same-class method whose body carries a `SELECT` literal (derived from the method, not its name) | exact set both ways vs `_GUARDED_CAS_DOORS` | STRUCTURAL (a proxy for "re-reads") — ⚠ BOUND (58 am-7 §1 keeps it, named): a re-read through a helper outside the class, or a SELECT built without a literal, is invisible — 58 am-5 (C)'s runtime leg is the instrument that does not care | MS1, MS2; the enumeration's RED@169925f shows the new reach (keeps + floor-calibration doors FOUND) |
| B RS-2 R-1 leg | every round of the race | per-call ContextVar marker set by the WIRED mint's wrapper, read per gather child | yes (== `_ROUNDS`) | EFFECT (a raise after the mint returned) | ME1 |

## §DUAL (P6b) — removed behaviour
am-32 removes ONE production behaviour: keeps' CAS "a non-conflict rejection whose key coincidentally resolves returns the winner" — **dropped deliberately** (am-32 §1.2: W7's family inside keeps). Pinned as a RED on the build that keeps it (keeps twin `[<non-conflict>-winner-landed]`, MA6 = exactly the 169925f door). The retired `minted_by_this_call` flag: dropped deliberately (am-28 §F-1), R-2 pins the deletion. No other production behaviour is removed by the fold; the test-side DUAL is §3.

## §FLAGS
- **F-1 `store/_txn.py` — FILE-level collision with packet 58 §HELD part 3 (`_ROLLBACK_LOG_TIERS`).** Both edit `_txn.py`. **RULED by packet 58 amendment 7 §4 (`01565f9`) while this fold ran:** the tier table is re-keyed by CLASS and `TxnUniqueViolationError` → WARNING — 58's delta, not a28b's. **No semantic overlap with my pins:** none reads `_log_rollback` or a log level; none of 58's reads `_classify_engine_error`'s labels. Order: 63c-i-a first (58 am-7 §0 row 2); 58's tier table then keys on the class a28b's builder lands.
- **F-2 `test_retry_seam.py` — the guarded-CAS scanner collision with packet 58 am-5. RULED by 58 am-7 (`01565f9`) while this fold ran:** ONE instrument — 63c's DOMAIN (a28b's import-resolved classes incl. Attribute/Tuple, the derived re-read, the whole tree) + 58's PARTITION (door iff the class closure contains exhaustion, else `_TYPED_CAS_CATCHES`); **63c-i-a lands a28b's scanner with ONE set first** (RS-5, keeps and `record_measurement` listed; RS-5 / keeps' guard "by type", `record_measurement`'s "by tuple"); 58's §HELD is a DELTA (the partition, the two moves, a union completeness pin), never a second scanner. Folded here, per lead directive #17087 (FK-a28b-4, pick B): the DOMAIN + the PARTITION — `_GUARDED_CAS_DOORS` (+ `record_measurement`, am-7's message) and `_TYPED_CAS_CATCHES` (RS-5, keeps), both exact both ways, disjoint, union == the derived domain; and am-7 §3 item 1's F-4 re-key (below). **Left to 58's delta:** `tasks.py::claim_task` in `_TYPED_CAS_CATCHES` (58's production), am-7 §1's wider completeness over translators / passthroughs, the runtime↔static cross-check (§3 item 2), and item 4's "exactly ONE scanner function in the test tree" AST pin (am-7 §3 lists it without an owner — a question for the lead).
- **F-3 `test_retry_seam.py` registered under the a28 bound** — a shared ~7.8k-line file; every red in it partitions as expected until the bound self-destructs (D-7; written into the registry comment). ⚠ 58 am-7: contract-58-r2's `test_reanchor_58_r2_cas_runtime.py` imports `_TYPED_CAS_CATCHES`, RED until 58's delta — that file is 58's registry's, not this bound's.
- **F-4 FOLDED (58 am-7 §3 item 1):** `test_the_transactional_doors_never_re_read_after_exhaustion` was a HAND list of four doors keyed on `ast.Name == TxnContentionExhaustedError` (blind to Tuple guards). Re-keyed to `_GUARDED_CAS_DOORS` and the SAME `_caught_classes` derivation; a by-type door needs no guard; every earlier clause catching exhaustion must be a bare `raise` (DUAL row U-9).
- **F-5 residual (pre-existing, not 63c's pins): a leg whose OWN target table is undefined RAISES** (`--table agent` on a store without `agent`: `TxnDomainRejectionError … governed scope count rejected`; `--table message` without `message` likewise). Loud, not silent; the gating pin tolerates exactly this and nothing else. Should it answer "nothing to migrate" instead? Operator/sidecar (R-a28b-3).
- **F-6 mixed-owner sentence** — am-31 names no `mixed` sentence; the existing `test_agent_governance…[mixed-owners]` constrains it ("owned by the operator" + "E3"). Pinned on my pick (FK-a28b-2).
- **F-7 a foreign working-copy change set sits in the main tree** (not mine, NOT staged): #503's files (`testing/loopback.py`, `test_loopback_serving.py`, `test_migration_wire.py`, `scripts/{concurrent_wire_acceptance.py,gates.yaml,pending_contract_gate.py,wave_gate.py,_pytest_sessions.py}`), 64b's files, `test_comms_footer.py` / `test_mcp_server.py`, and 64b's hunk in `scripts/pending_contracts.yaml`. Staged by path / by hunk; `git diff --cached` verified (§commit).
- **F-9 packet 58's r3 contract files are UNTRACKED and unregistered** (`test_reanchor_58_r3_{convergence,tiers,am6,cas_seam,probes,relate}.py`): at currency they are the ONLY orphans (79 pytest + 7 typecheck) — 58's bookkeeping, not this bound's; surfaced for the lead.
- **F-8 host memory vs the operator-ruled watchdog (reading (a)):** the host's own MemAvailable swings 12.9–35 GB without me (two SurrealDB stores ~18 GB RSS, several Postgres clusters, a foreign `mobile-pricepaper-smoke` pytest fleet). Two `-n 12` and two `-n 4` full-suite attempts were killed by the watchdog (receipts §8) before a quiet window; the adversary's DV-5 observed the same.

## §10 BUILDER CONSTRAINTS (every name / placement / order the pins require)
Carried unchanged: a28 §10 items 1, 2, 4–9 (item 8 amended below); a19b / a19a carried items as a28 lists them.
1. **`loremaster.store._txn`** (the ONE driver): `class TxnUniqueViolationError(TxnDomainRejectionError)` — EXACTLY that name (amendment 33), module-level, a generic message, NO attribute parsed from raw text; ONE label (`_ERROR_CLASS_UNIQUE_VIOLATION = "unique violation — the record id or a unique index value is already taken; re-read the row"`, am-33 — the pins read the CLASS, not the label text); `_domain_rejection_error` maps the label → the class (the ONE place). Classification: **`run_query` path TYPED for the record shape** — an `AlreadyExistsError` with `record_id is not None` → the class; an `AlreadyExistsError` of any other kind → NOT the class (the unspecified base), **whatever its text says** (pin (c)'s reworded legs); **text markers only inside `_classify_engine_error`**, two noun-bearing pairs (am-33): `("database record", "already exists")` and `("database index", "already contains")` — the index pair applies on BOTH paths (the SDK serves an untyped `InternalError` for it — the U-sdk pin-the-miss), and NEITHER pair may match `The table '…' already exists`. Live-verify both on `:18000` (the probe is §A.1). The ASSERT / coercion / governed / unspecified classifications are unchanged.
2. **RS-5 (`AgentRegistry.register`)**: the CREATE catches `TxnUniqueViolationError` ONLY (no Tuple, no base class, no text test — K3/K9/MA5/MA8/MS1); re-read `_select_row(id)`; exists → the existing re-register path with THIS call's writes (K7/K9 `model`); absent → the caught error propagates UNCHANGED after exactly ONE CREATE; every other class propagates unchanged after ONE CREATE.
3. **keeps (`KeepStore.get_or_create_keyed`)**: narrow to `except TxnUniqueViolationError:`; the confirmation re-read (`get_by_key`) + re-raise-if-absent unchanged; everything else goes to the wrap (transport / contention pass through; other store errors → `KeepStoreError`) after ONE create transaction. Keeps' existing pins read FIRST (am-32 §1.2 rider): `test_keeps_store.py`'s fault-injection pin injects a bare `SurrealStoreError` and expects `KeepStoreError` — stays green, no re-key (measured on the reference).
4. **Delete** `keeps.minted_by_this_call`, `_MINTED_BY_THIS_CALL` and EVERY prose mention of the name anywhere in the package (R-2 scans bare, case-insensitive).
5. **am-31 fields** on `MigratePreconditionCounts` (a28 §10 item 8's model), in THIS order after the six: `distinct_owner_principals: int | None = None`, `owner_classification: Literal["operator", "foreign", "mixed", "unclassified"] | None = None` (the shape pin compares annotations by `==`). Populated through the normal constructor, looked up by name at call time (a28 item 8). `owner_classification` is `None` when the agent read did not run OR found no owned-but-unscoped row (FK-a28b-2); `distinct_owner_principals` = distinct owners over the owned-but-unscoped agent rows (measured `0` when none).
6. **FK-ADV-2 Reading A**: every count field `None` IFF its read was gated off (agent facts iff `agent` is defined; message facts iff `--table message` AND `message` defined) on EVERY outcome — refusal, leg refusal, success. The describe (ONE render over the model) names every MEASURED NON-ZERO problem in check order: agent problems → dangling senders → message half-pairs, **on the verb-level refusal too** (with the verb's any-table remedy, never the leg's "before migrating `message`"); the owner sentence keys ONLY on `owner_classification` (+ `distinct_owner_principals` where the sentence names a count: `foreign`, `mixed`) — never on whether an operator object resolved (MB4); the `foreign` N is the FIELD (MB5); principal ids render only inside `(first N named: …)`. The `mixed` sentence must ALSO carry "owned by the operator" and "E3" (the existing `test_agent_governance…[mixed-owners]` pin). No integer outside a field, a row-id sample (`First N of M … shown`) or a principal-id sample (`(first N named`) in a refusal on the four pin-(2) populations.
7. **Order vs packet 58** (58 am-7 §0 row 2): 63c-i-a lands FIRST — the partitioned scanner as written here (FK-a28b-4); the build must make RS-5 and keeps SAFE BY TYPE (narrowed catches) so they land in `_TYPED_CAS_CATCHES`; 58's §HELD lands after as a DELTA (`claim_task`, the runtime cross-check), never a second scanner. `_txn.py`: 58's `_ROLLBACK_LOG_TIERS` keys on this class (WARNING) — 58's, not pinned here.
8. Lint: `_classify_engine_error` gains branches (the reference needed `# noqa: PLR0911`, 8 returns).

## §11 DRY ledger (new reusable symbols — all test-local)
lore_search was NOT run for these (§0) — fallback: the helpers were checked by reading a28 / a19a / `_governed_contract` / `_surreal_harness` by hand.
| new symbol | query | found | disposition |
|---|---|---|---|
| `_spy_registry_queries` (B) | read a28 `_count_calls` | a28 `_count_calls` wraps a NAMED method | LANDED from §A.2 verbatim; ONE copy, imported by A |
| `_arm_per_call_mint_marker`, `_minted_then_outcome`, `_MINT_RETURNED` (B) | read a19a `_spy_the_mint`, a28 `_spy_delete_keep` | per-CALL attribution needs a ContextVar; neither helper attributes | HAND-ROLLED |
| `_RULED_FIELD_SPEC`, `_literal_members`, `_perturbation_kind`, `_perturbed_value`, `_states_its_count`, `_collection_time_fields`, `_assert_complete`, `_OWNER_SENTENCE_STATES_N` (B) | read a28's am-30 plumbing | a28 `_perturbed_counts_class` (int-only) | EXTENDED `_perturbed_counts_class` in place (by annotation); the rest are am-32 §3 plumbing |
| `_seed_foreign_owner_population`, `_seed_mixed_owner_population`, `_seed_unclassified_owner_population`, `_seed_both_half_pairs`, `_seed_message_half_pair_behind_a_migratable_agent` (B) | a19 `_seed_foreign_principals`, a19a `_seed_migrated_senders` | seeders of other shapes | HAND-ROLLED on REUSED parts |
| `_GATED_READS`, `_STORE_SHAPES`, `_read_of`, `_read_ran` (B) | — | — | am-32 §2.2 domain plumbing |
| `_SITUATIONS`, `_driver_handles`, `_raise_through`, `_sdk_already_exists_kinds`, `_RaisingConnection`, `_already_exists`, `_run_query_raises` (A) | read `_governed_contract.store_handle` | `store_handle` builds a StoreHandle + acquire counter; `run_query`/`execute_transaction` take the three callables directly | HAND-ROLLED (3-line adapters) |
| `_UnbuiltUniqueViolationError`, `_CONFLICT_CLASS_NAME`, `_KEEPS_PASSTHROUGH`, `_C2_SHAPES`, `_shape_carol`, `_CAUSE_CLASS`, `_NOT_REACHABLE_POST_MINT`, `_RETIRED_NAME` (A) | — | — | test-local constants / fixture |
| `_module_of`, `_caught_classes`, `_issues_a_read` (RS) | read RS `_enclosing_callable`, the `_QUERY_SEAMS` derivation | — | HAND-ROLLED — the scanner's own parts; 58's delta EXTENDS them (58 am-7 corrects my earlier "REPLACE" to EXTEND); the re-keyed F-4 pin REUSES `_caught_classes` (one derivation) |

## §13 What the NARROW ADVERSARY DELTA should attack
1. **am-33's one class over two shapes** — a build with only the record pair (MA3b measured: keeps' real 8-way + RS-2/RS-5 red); a marker so broad it swallows a table / ASSERT text (the (a)(b) controls); a build that adds a typed branch for the index shape that the SDK cannot provide (the U-sdk pin-the-miss).
2. **K9's `_CONFLICT_CLASS` binding (D-1)** and **K3's re-key (D-2)** — still the lifted property?
3. **The FK-ADV-2 gating pin's domain** — tables × shapes are am-32's enumeration; the field partition is a NAME-SUFFIX rule (completeness-pinned, but a message-read field NOT named `*_messages` would be misfiled — try it).
4. **pin (1)'s generated cases vs FK-a28b-2/3** — `_states_its_count` exempts `distinct_owner_principals` under `operator`/`unclassified`; verify `mixed` really names N (`distinct-P_mixed` case).
5. **The scanner (§P1c bound + F-2/F-4)** — a re-read through a helper outside the class; a SELECT built without a literal; the by-type early return in the re-keyed F-4 pin (a door whose handler is typed-disjoint but whose try ALSO holds a re-reading exhaustion clause).
6. **C2 shapes** — a fifth relation; a gate keyed on "the caller's OWN session keep exists".
7. **R-1 ContextVar marker** — a correct build that ever produces a round with zero post-mint refusals (a flake = a STOP). Evidence: 20 consecutive × 20 rounds (§7).
8. **The unclassified exclusion from pin (2)** (FK-a28b-3) — a non-field integer in the unclassified text is not caught by pin (2).

## §A Instruments (VERBATIM — the scratch trees are disposable by design)

### §A.1 the live engine probe (FK-a28b-1) — `probe_exists_texts.py` md5 `501f9618dcab41a8f66d00908a00da0c`
```python
"""contract-63c-i-a-a28b PROBE (not a pin): the engine's already-exists shapes on the TEST store :18000.

Legs (each on a throwaway database, removed at the end):
  R-txn   a record-id collision (CREATE t:x twice) inside BEGIN/COMMIT via query_raw -> per-statement raw result text
  R-sdk   the same collision as a single statement via query() -> SDK exception class / kind / details / str
  U-txn   a UNIQUE-index collision (fresh ids, same key) inside BEGIN/COMMIT -> per-statement raw result text
  U-sdk   the same UNIQUE collision via query() -> SDK exception class / kind / details / str
  T-sdk   a bare DEFINE TABLE of an existing table via query() -> class / kind / details / str (the DDL door)
  T-txn   the same bare DEFINE TABLE inside BEGIN/COMMIT -> raw text
  CONTROL an ASSERT violation via query_raw -> raw text (must NOT carry the record-exists substring)
"""

from __future__ import annotations

import asyncio
import uuid

from surrealdb import AsyncSurreal

URL = "ws://127.0.0.1:18000/rpc"


def describe(error: BaseException) -> str:
    return (f"{type(error).__module__}.{type(error).__name__} kind={getattr(error, 'kind', None)!r} "
            f"details={getattr(error, 'details', None)!r} record_id={getattr(error, 'record_id', 'n/a')!r} "
            f"table_name={getattr(error, 'table_name', 'n/a')!r} str={str(error)!r}")


def failed(response: dict) -> list[str]:
    return [f"[{index}] {entry.get('status')}: {entry.get('result')!r}"
            for index, entry in enumerate(response.get("result") or [])]


async def main() -> None:
    database = f"probe_a28b_{uuid.uuid4().hex[:12]}"
    connection = AsyncSurreal(URL)
    await connection.connect()
    await connection.signin({"username": "root", "password": "spikeroot"})
    await connection.query("DEFINE NAMESPACE IF NOT EXISTS lore_test")
    await connection.use("lore_test", database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await connection.use("lore_test", database)
    try:
        await connection.query("DEFINE TABLE t SCHEMALESS; DEFINE TABLE k SCHEMAFULL; "
                               "DEFINE FIELD key ON k TYPE string; DEFINE INDEX k_key ON k FIELDS key UNIQUE; "
                               "DEFINE TABLE a SCHEMAFULL; DEFINE FIELD n ON a TYPE int ASSERT $value > 0;")
        await connection.query("CREATE t:x CONTENT { v: 1 }")
        await connection.query("CREATE k:one CONTENT { key: 'dup' }")
        response = await connection.query_raw("BEGIN; CREATE t:x CONTENT { v: 2 }; COMMIT;", {})
        print("R-txn  ", failed(response))
        try:
            await connection.query("CREATE t:x CONTENT { v: 3 }")
            print("R-sdk   NO RAISE")
        except Exception as error:  # noqa: BLE001
            print("R-sdk  ", describe(error))
        response = await connection.query_raw("BEGIN; CREATE k:two CONTENT { key: 'dup' }; COMMIT;", {})
        print("U-txn  ", failed(response))
        try:
            await connection.query("CREATE k:three CONTENT { key: 'dup' }")
            print("U-sdk   NO RAISE")
        except Exception as error:  # noqa: BLE001
            print("U-sdk  ", describe(error))
        try:
            await connection.query("DEFINE TABLE t")
            print("T-sdk   NO RAISE")
        except Exception as error:  # noqa: BLE001
            print("T-sdk  ", describe(error))
        response = await connection.query_raw("BEGIN; DEFINE TABLE t; COMMIT;", {})
        print("T-txn  ", failed(response))
        response = await connection.query_raw("BEGIN; CREATE a:1 CONTENT { n: -1 }; COMMIT;", {})
        print("CONTROL", failed(response))
        print("VERSION", await connection.version())
    finally:
        await connection.query(f"REMOVE DATABASE {database}")
        await connection.close()


asyncio.run(main())
```

### §A.1b its output (spike-surreal :18000, 2026-09-26) — `probe_exists_texts.out` md5 `4212462aa148655ecacb86f3a380c7cd`
```text
R-txn   ['[0] OK: None', "[1] ERR: 'Database record `t:x` already exists'", "[2] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'"]
R-sdk   surrealdb.errors.AlreadyExistsError kind='AlreadyExists' details={'details': {'id': 't:x'}, 'kind': 'Record'} record_id='t:x' table_name=None str='Database record `t:x` already exists'
U-txn   ['[0] OK: None', '[1] ERR: "Database index `k_key` already contains \'dup\', with record `k:one`"', "[2] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'"]
U-sdk   surrealdb.errors.InternalError kind='Internal' details=None record_id='n/a' table_name='n/a' str="Database index `k_key` already contains 'dup', with record `k:one`"
T-sdk   surrealdb.errors.AlreadyExistsError kind='AlreadyExists' details={'details': {'name': 't'}, 'kind': 'Table'} record_id=None table_name='t' str="The table 't' already exists"
T-txn   ['[0] OK: None', '[1] ERR: "The table \'t\' already exists"', "[2] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'"]
CONTROL ['[0] OK: None', "[1] ERR: 'Found -1 for field `n`, with record `a:1`, but field must conform to: $value > 0'", "[2] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'"]
VERSION surrealdb-3.2.4+20260803.93ab219
```

### §A.2 the reference build over a28's reference (a28 `reference_fix.patch` md5 `0abdf6d85342aec8af41572a2d4d0ba9`, extracted from the committed a28 report and md5-verified, THEN this interdiff; renamed per am-33) — every SAT / mutation / concurrency receipt of run 2 ran on it — `a28b_over_a28_reference.patch` md5 `95935c21984a2cba506b8a9d81a5ff78`
```diff
diff -ru a/loremaster/loremaster/agents.py b/loremaster/loremaster/agents.py
--- a/loremaster/loremaster/agents.py	2026-09-26 19:26:58.153583328 -0400
+++ b/loremaster/loremaster/agents.py	2026-09-26 20:42:20.681537197 -0400
@@ -93,7 +93,7 @@
     SurrealConnectionError,
     SurrealStoreError,
     TxnContentionExhaustedError,
-    TxnDomainRejectionError,
+    TxnUniqueViolationError,
     _SurrealConnection,
     bootstrap_session,
     execute_transaction,
@@ -948,7 +948,7 @@
                     f"CONTENT ${_ROW_CONTENT_PARAM}",
                     {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
                 )
-            except TxnDomainRejectionError:
+            except TxnUniqueViolationError:
                 # amendment 29 RS-5: a concurrent identical first register won the CREATE — re-read and
                 # take THE re-register path (preflight decides a differing role/spawned_by).
                 if await self._select_row(agent_id) is None:
diff -ru a/loremaster/loremaster/governed.py b/loremaster/loremaster/governed.py
--- a/loremaster/loremaster/governed.py	2026-09-26 19:26:58.153583328 -0400
+++ b/loremaster/loremaster/governed.py	2026-09-26 20:42:20.684537275 -0400
@@ -22,7 +22,7 @@
 from collections.abc import Iterator
 from dataclasses import dataclass
 from pathlib import Path
-from typing import TYPE_CHECKING, Any
+from typing import TYPE_CHECKING, Any, Literal
 
 from pydantic import BaseModel, ConfigDict
 
@@ -107,6 +107,8 @@
     dangling_sender_messages: int | None = None
     owned_but_unscoped_messages: int | None = None
     scoped_but_ownerless_messages: int | None = None
+    distinct_owner_principals: int | None = None
+    owner_classification: Literal["operator", "foreign", "mixed", "unclassified"] | None = None
 
 
 @dataclass(frozen=True)
@@ -431,9 +433,7 @@
     audit: Any
     pre_read_row: dict[str, Any] | None
 
-    def fragments(
-        self, set_fragment: str | None, params: dict[str, Any] | None = None
-    ) -> list[TxnFragment]:
+    def fragments(self, set_fragment: str | None, params: dict[str, Any] | None = None) -> list[TxnFragment]:
         """The guarded mutation as composable fragments with the conflict guard IN-STORE (§2.2 step 2).
 
         ``LET $gw_hit = (UPDATE|DELETE type::record('<t>', $gw_id) [SET <set>] WHERE (<guard>)
@@ -498,9 +498,7 @@
         url=store.url,
         noun="governed pre-read",
         label="governed.pre_read.rejected",
-        statement=(
-            f"SELECT owner_principal, owner_agent, scope FROM type::record('{table}', $gw_id)"
-        ),
+        statement=(f"SELECT owner_principal, owner_agent, scope FROM type::record('{table}', $gw_id)"),
         params={"gw_id": row_id},
         logger=logger,
     )
@@ -581,9 +579,7 @@
     # authorize_guarded; the conflict guard moves IN-STORE (the LET/THROW GuardedPlan.fragments
     # emits), so the Python ``row_count == 0 → GovernedConflict`` branch is DELETED (unreachable —
     # the THROW fires first, §2.5). The store's typed TxnGovernedConflictError maps → GovernedConflict.
-    plan = await authorize_guarded(
-        subject, action, table=table, row_id=row_id, audit=audit, store=store
-    )
+    plan = await authorize_guarded(subject, action, table=table, row_id=row_id, audit=audit, store=store)
     statement_text, merged_params = compose(*plan.fragments(set_fragment))
     # ONE verified BEGIN…COMMIT through the injected driver (acquire #2), inside write_guard so the
     # F5 runtime seam attributes it to this guarded frame. A THROW'd governed conflict aborts the
diff -ru a/loremaster/loremaster/keeps.py b/loremaster/loremaster/keeps.py
--- a/loremaster/loremaster/keeps.py	2026-09-26 19:26:58.153583328 -0400
+++ b/loremaster/loremaster/keeps.py	2026-09-26 20:42:20.682537224 -0400
@@ -80,9 +80,9 @@
 from loremaster.store._txn import (
     _CONNECTION_ERRORS,
     SurrealConnectionError,
-    SurrealStoreError,
     TxnContentionExhaustedError,
     TxnFragment,
+    TxnUniqueViolationError,
     _SurrealConnection,
     bootstrap_session,
     compose,
@@ -590,12 +590,7 @@
                     drop=self._drop_connection,
                     url=self._url,
                 )
-            except (SurrealConnectionError, TxnContentionExhaustedError):
-                # Transport / exhausted contention belongs to the retry/lifecycle layer — it is
-                # NOT a UNIQUE conflict, and must NEVER be swallowed by the CAS re-read (store-ref
-                # §5: re-read a genuine CONFLICT, never a dropped socket).
-                raise
-            except SurrealStoreError:
+            except TxnUniqueViolationError:
                 # The hot-row CAS (store-ref §5): a concurrent ``register`` may have minted this
                 # UNIQUE key between our read-miss and this CREATE. If the key now resolves, that
                 # IS the conflict → return the winner, never a second row. If it still does not,
diff -ru a/loremaster/loremaster/principals.py b/loremaster/loremaster/principals.py
--- a/loremaster/loremaster/principals.py	2026-09-26 19:26:58.153583328 -0400
+++ b/loremaster/loremaster/principals.py	2026-09-26 20:42:20.683537249 -0400
@@ -1092,7 +1092,7 @@
     if table not in _MIGRATE_VALID_TABLES:
         return _not_supported(table, store_was_read=False)
     preconditions = await _agent_migration_preconditions(store, table=table)
-    counts = _measured_counts(preconditions, table)
+    counts = await _measured_counts(preconditions, principal_store)
     refusal = await _verb_level_refusal(preconditions, counts, principal_store)
     if refusal is not None:
         result = _refused(table, refusal)
@@ -1107,19 +1107,35 @@
     return dataclasses.replace(result, preconditions=counts)
 
 
-def _measured_counts(preconditions: AgentMigrationPreconditions, table: str) -> Any:
-    """THE measured counts (amendment 30): the agent reads ran at the verb for every valid table; the message
-    reads only for ``--table message`` (``None`` = not measured)."""
+async def _measured_counts(
+    preconditions: AgentMigrationPreconditions, principal_store: PrincipalStore
+) -> Any:
+    """THE measured counts (amendments 30/31/32): a field is ``None`` iff its read was gated off."""
     from loremaster.governed import MigratePreconditionCounts
 
-    message = table == MESSAGE_TABLE
+    agent = preconditions.agent_facts_read
+    message = preconditions.message_facts_read
+    owners = {str(owner) for _row_id, owner in preconditions.owned_unscoped}
+    classification: str | None = None
+    if agent and owners:
+        operator = await resolve_operator_principal(principal_store)
+        if operator is None:
+            classification = "unclassified"
+        elif owners == {operator.id}:
+            classification = "operator"
+        elif operator.id in owners:
+            classification = "mixed"
+        else:
+            classification = "foreign"
     return MigratePreconditionCounts(
-        unscoped_agents=preconditions.unscoped_count,
-        owned_but_unscoped_agents=len(preconditions.owned_unscoped),
-        scoped_but_ownerless_agents=len(preconditions.ownerless_scoped),
+        unscoped_agents=preconditions.unscoped_count if agent else None,
+        owned_but_unscoped_agents=len(preconditions.owned_unscoped) if agent else None,
+        scoped_but_ownerless_agents=len(preconditions.ownerless_scoped) if agent else None,
         dangling_sender_messages=len(preconditions.dangling_senders) if message else None,
         owned_but_unscoped_messages=len(preconditions.messages_owned_unscoped) if message else None,
         scoped_but_ownerless_messages=len(preconditions.messages_scoped_ownerless) if message else None,
+        distinct_owner_principals=len(owners) if agent else None,
+        owner_classification=classification,
     )
 
 
@@ -1330,6 +1346,8 @@
     unscoped_count: int
     owned_unscoped: tuple[tuple[Any, Any], ...]
     ownerless_scoped: tuple[Any, ...]
+    agent_facts_read: bool = False
+    message_facts_read: bool = False
     dangling_senders: tuple[tuple[Any, Any], ...] = ()
     messages_owned_unscoped: tuple[Any, ...] = ()
     messages_scoped_ownerless: tuple[Any, ...] = ()
@@ -1450,6 +1468,8 @@
             else:
                 messages_scoped_ownerless.append(row.get("id"))
     return AgentMigrationPreconditions(
+        agent_facts_read=AGENT_TABLE in defined,
+        message_facts_read=table == MESSAGE_TABLE and MESSAGE_TABLE in defined,
         unscoped_count=unscoped_count,
         owned_unscoped=_by_id(owned_unscoped),
         ownerless_scoped=_by_id(ownerless_scoped),
@@ -1470,38 +1490,37 @@
 
 
 def _owned_unscoped_part(
-    owned_unscoped: tuple[tuple[Any, Any], ...], operator: Principal | None, count: int
+    owned_unscoped: tuple[tuple[Any, Any], ...], operator: Principal | None, counts: Any
 ) -> str:
-    """The §2.1 owned-but-unscoped part, with the DERIVED diagnosis (amendment 19 D-3 F-1 / amendment 20
-    §8.4): who owns the rows — the operator (the E3 population), named other principals (bounded by the
-    same constant — amendment 20 §8.2), or, when the operator is unresolvable, NOBODY classified (any of
-    them may BE the operator)."""
-    head = f"{count} agent row(s) carry an owner but no scope (§2.1)"
+    """The §2.1 owned-but-unscoped part — the owner sentence DERIVED from ``owner_classification`` and
+    ``distinct_owner_principals`` (amendment 31); principal ids are SAMPLES."""
+    head = f"{counts.owned_but_unscoped_agents} agent row(s) carry an owner but no scope (§2.1)"
     sample = _id_sample([row_id for row_id, _owner in owned_unscoped])
-    if operator is None:
+    classification = counts.owner_classification
+    if classification == "unclassified":
         return (
             f"ALSO: {head}; their owners are UNCLASSIFIED — with the operator unresolved, any of them may "
             f"BE the operator. {sample}"
         )
-    # Owners compare and render by the SDK's own ``str(RecordID)`` — ``Principal.id`` is that same
-    # rendering (``_row_to_principal``) — so no id is hand-parsed (finding #248).
-    owners = [str(owner) for _row_id, owner in owned_unscoped]
-    operator_owned = sum(1 for owner in owners if owner == operator.id)
-    others = sorted({owner for owner in owners if owner != operator.id})
-    parts = [f"{head}."]
-    if operator_owned:
-        parts.append(
-            f"{operator_owned} of them are owned by the operator — registered by a pkt-62–63b image; "
-            "see amendment-1 E3."
+    operator_id = operator.id if operator is not None else None
+    others = sorted({str(owner) for _row_id, owner in owned_unscoped if str(owner) != operator_id})
+    named = [sanitise_line(owner) for owner in others[:_REFUSAL_ID_SAMPLE_SIZE]]
+    if classification == "operator":
+        owner_sentence = (
+            "They are owned by the operator — registered by a pkt-62–63b image; see amendment-1 E3."
+        )
+    elif classification == "foreign":
+        owner_sentence = (
+            f"They are owned by {counts.distinct_owner_principals} other principal(s) "
+            f"(first {len(named)} named: {', '.join(named)})."
         )
-    if others:
-        named = [sanitise_line(owner) for owner in others[:_REFUSAL_ID_SAMPLE_SIZE]]
-        parts.append(
-            f"{count - operator_owned} are owned by {len(others)} other principal(s) "
+    else:
+        owner_sentence = (
+            "They are owned by the operator — registered by a pkt-62–63b image; see amendment-1 E3 — AND by "
+            f"other principal(s): {counts.distinct_owner_principals} distinct owner(s) "
             f"(first {len(named)} named: {', '.join(named)})."
         )
-    parts.append(sample)
-    return " ".join(parts)
+    return " ".join([f"{head}.", owner_sentence, sample])
 
 
 async def _verb_level_refusal(
@@ -1522,9 +1541,7 @@
             parts.append(
                 await _operator_unresolved(principal_store, purpose="to classify the rows below") + "."
             )
-        parts.append(
-            _owned_unscoped_part(preconditions.owned_unscoped, operator, counts.owned_but_unscoped_agents)
-        )
+        parts.append(_owned_unscoped_part(preconditions.owned_unscoped, operator, counts))
     if preconditions.ownerless_scoped:
         count = counts.scoped_but_ownerless_agents
         parts.append(
@@ -1533,6 +1550,7 @@
         )
     if not parts:
         return None
+    parts.extend(_message_problem_parts(preconditions, counts))
     parts.append(
         f"(The store holds {counts.unscoped_agents} agent row(s) with no scope in total.) Adjudicate "
         "these "
@@ -1541,21 +1559,10 @@
     return " ".join(parts)
 
 
-def _message_leg_refusal(preconditions: AgentMigrationPreconditions, counts: Any) -> str | None:
-    """The message leg's row-fact refusal (amendments 23 FK-2, 24 §2 door #2, 25, 26), or ``None``: ONE
-    refusal naming EVERY problem present, in :func:`_agent_migration_preconditions`' check order —
-    dangling senders, then each message half-pair — each with its true count and a bounded sample (THE
-    one :data:`_REFUSAL_ID_SAMPLE_SIZE`, per list). Byte-inert: nothing is stamped, the sound rows
-    included (one statement, one verdict). ORDER-class, not store-class: it refuses ``message`` only."""
+def _message_problem_parts(preconditions: AgentMigrationPreconditions, counts: Any) -> list[str]:
+    """Every MEASURED, NON-ZERO message problem, in check order (amendment 32 §2.1)."""
     parts: list[str] = []
-    if preconditions.unscoped_count > 0:
-        parts.append(
-            f"cannot migrate `message` rows before the `agent` table is migrated "
-            f"({counts.unscoped_agents} un-migrated (NONE-scope) agent(s) remain) — a message's "
-            "owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 "
-            "agent-first ORDER); run migrate-governed for `agent` first."
-        )
-    if preconditions.dangling_senders:
+    if counts.dangling_sender_messages:
         dangling = preconditions.dangling_senders
         shown = [
             f"{sanitise_line(str(message_id))} (sender {sanitise_line(str(sender))})"
@@ -1563,8 +1570,7 @@
         ]
         parts.append(
             f"{counts.dangling_sender_messages} legacy message(s) name a dangling sender — their `sender` "
-            "link "
-            "resolves to "
+            "link resolves to "
             f"no agent row, so no owner can be derived from it. First {len(shown)} of {len(dangling)} "
             f"shown: {', '.join(shown)}."
         )
@@ -1580,11 +1586,29 @@
             "carry a scope but no owner",
         ),
     ):
-        if ids:
+        if count:
             parts.append(
                 f"{count} message row(s) {fact} — a half-applied store (one column of the governed "
                 f"pair was stamped without the other). {_id_sample(ids)}"
             )
+    return parts
+
+
+def _message_leg_refusal(preconditions: AgentMigrationPreconditions, counts: Any) -> str | None:
+    """The message leg's row-fact refusal (amendments 23 FK-2, 24 §2 door #2, 25, 26), or ``None``: ONE
+    refusal naming EVERY problem present, in :func:`_agent_migration_preconditions`' check order —
+    dangling senders, then each message half-pair — each with its true count and a bounded sample (THE
+    one :data:`_REFUSAL_ID_SAMPLE_SIZE`, per list). Byte-inert: nothing is stamped, the sound rows
+    included (one statement, one verdict). ORDER-class, not store-class: it refuses ``message`` only."""
+    parts: list[str] = []
+    if preconditions.unscoped_count > 0:
+        parts.append(
+            f"cannot migrate `message` rows before the `agent` table is migrated "
+            f"({counts.unscoped_agents} un-migrated (NONE-scope) agent(s) remain) — a message's "
+            "owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 "
+            "agent-first ORDER); run migrate-governed for `agent` first."
+        )
+    parts.extend(_message_problem_parts(preconditions, counts))
     order_parts = parts[:1] if preconditions.unscoped_count > 0 else []
     row_parts = parts[len(order_parts) :]
     if not row_parts:
diff -ru a/loremaster/loremaster/store/_txn.py b/loremaster/loremaster/store/_txn.py
--- a/loremaster/loremaster/store/_txn.py	2026-09-26 19:26:58.147583172 -0400
+++ b/loremaster/loremaster/store/_txn.py	2026-09-26 20:42:20.689537406 -0400
@@ -102,7 +102,7 @@
     AsyncHttpSurrealConnection,
     AsyncWsSurrealConnection,
 )
-from surrealdb.errors import ErrorKind, ServerError, SurrealError
+from surrealdb.errors import AlreadyExistsError, ErrorKind, ServerError, SurrealError
 from websockets.exceptions import WebSocketException
 
 from lorerunes import reclassify
@@ -217,6 +217,15 @@
     """
 
 
+class TxnUniqueViolationError(TxnDomainRejectionError):
+    """The write's IDENTITY is already taken (amendment 32 §1): a record-id collision, or a UNIQUE-index
+    collision on a natural key. The winner's row is there — a compare-and-set caller re-reads it.
+
+    A SUBCLASS of :class:`TxnDomainRejectionError` (every existing ``except`` keeps catching it); a generic
+    message; NO attribute parsed from the raw text (ledger #31).
+    """
+
+
 class RetryableConflictSignal(Exception):
     """An attempt callable's way of telling :func:`retry_on_conflict` "the engine
     reported a RETRYABLE write-write conflict; try again".
@@ -610,6 +619,9 @@
     "governed conflict — the guarded row moved between authorization and the write; "
     "re-authorize and re-issue"
 )
+_ERROR_CLASS_UNIQUE_VIOLATION = (
+    "unique violation — the record id or a unique index value is already taken; re-read the row"
+)
 _ERROR_CLASS_UNSPECIFIED = "unspecified rejection"
 
 # The substrings (verified live — see the module docstring's ``ASSERT``/coercion
@@ -630,6 +642,10 @@
 # ("governed_conflict:<t>:<id>") — the classification key. The `<t>:<id>` suffix is free-form
 # forensics that rides only the server-side rollback log, never the raised message (rider ii).
 _GOVERNED_CONFLICT_MARKER = "governed_conflict:"
+# amendment 32 §1 (+ FK-a28b-1): the two live-verified identity-taken texts (3.2.4, probe_exists_texts.py):
+# a record-id collision "Database record `t:x` already exists" and a UNIQUE-index collision "Database index
+# `k` already contains 'v', with record `k:1`". A table-level "The table 't' already exists" matches neither.
+_UNIQUE_VIOLATION_MARKERS = (("database record", "already exists"), ("database index", "already contains"))
 
 # The correlation hint appended to every classified rollback message, so an
 # operator holding only the (deliberately generic) exception text can still
@@ -637,7 +653,7 @@
 _SERVER_LOG_HINT = "see the server log for the full engine detail"
 
 
-def _classify_engine_error(raw_result: object) -> str:
+def _classify_engine_error(raw_result: object) -> str:  # noqa: PLR0911 - one label per engine class
     """Classify a rolled-back statement's raw engine result into a short,
     GENERIC label — never a slice of ``raw_result`` itself.
 
@@ -666,12 +682,17 @@
         one-line defensive check, not a load-bearing one, and removing it buys
         nothing.
     """
+    if isinstance(raw_result, AlreadyExistsError):
+        # Typed beats text (amendment 32 §1.1 item 3): the SDK's own discriminator decides.
+        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED
     text = str(raw_result)
     if _is_retryable_conflict_text(text):
         return _ERROR_CLASS_RETRYABLE_CONFLICT
     lowered = text.lower()
     if _GOVERNED_CONFLICT_MARKER in lowered:
         return _ERROR_CLASS_GOVERNED_CONFLICT
+    if any(all(part in lowered for part in marker) for marker in _UNIQUE_VIOLATION_MARKERS):
+        return _ERROR_CLASS_UNIQUE_VIOLATION
     if _ASSERT_VIOLATION_MARKER in lowered:
         return _ERROR_CLASS_ASSERT_VIOLATION
     if _FIELD_COERCION_MARKER in lowered:
@@ -693,6 +714,8 @@
     """
     if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:
         return TxnGovernedConflictError(message)
+    if error_class == _ERROR_CLASS_UNIQUE_VIOLATION:
+        return TxnUniqueViolationError(message)
     return TxnDomainRejectionError(message)
```

### §A.3 AST receipt instrument (the K-probes landed vs the adversary's §A.2, extracted verbatim — md5 `6b8ec7f0ea371b11c8119f6b4c531c4e` = the report's stated md5) — `ast_receipt.py` md5 `cbe2982564bc472b114dc25f544af465`
```python
"""ast_receipt.py <adversary K-probe file> <landed file> [<landed helper file>...]: AST-equality receipt per K symbol.
Compares ast.dump(include_attributes=False) of each top-level def/class/assign by NAME. Controls: a symbol known to
differ (K3, the deviation) must report DIFF, and an identity comparison of the adversary file with itself must be EQUAL."""
import ast, sys

def symbols(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    out[target.id] = ast.dump(node, include_attributes=False)
    return out

adversary = symbols(sys.argv[1])
landed = {}
for path in sys.argv[2:]:
    for name, dump in symbols(path).items():
        landed.setdefault(name, dump)
for name in sorted(adversary):
    if name.startswith(("Test", "test_", "_")):
        verdict = "EQUAL" if landed.get(name) == adversary[name] else ("ABSENT" if name not in landed else "DIFF")
        print(f"{verdict:6} {name}")
self_check = symbols(sys.argv[1]) == adversary
print(f"CONTROL self-compare EQUAL: {self_check}")
```

### §A.3b its output (final files) — `ast_receipt.out` md5 `308356175547e561f8b84af47adc1d0c`
```text
EQUAL  TestK1TheGateReadsNoRegistryRowThroughANYDoor
EQUAL  TestK2AGenuineCreateRejectionIsRaisedOnce
DIFF   TestK3TheConflictIsClassifiedByClassNotText
EQUAL  TestK4ATransportFailureIsNeverAReRegister
EQUAL  TestK5NoRefusalClassCompensates
EQUAL  TestK6NoRegisterPathRemovesOrWritesKeepState
EQUAL  TestK7TheRaceLoserIsServedTheSequentialSecondCall
EQUAL  TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied
EQUAL  TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould
DIFF   _CONFLICT_CLASS
EQUAL  _DIM
EQUAL  _KEEP_SAFE_VERBS
EQUAL  _STORE_ERROR_CLASSES
EQUAL  _arm_keep_write_spy
EQUAL  _forge
EQUAL  _keep_rows
EQUAL  _spy_registry_queries
DIFF   test_K9_the_derived_error_domain_is_non_vacuous
CONTROL self-compare EQUAL: True
```

### §A.4 the DECLARED mutation set (append-only; every block timestamped before its run) — `mut/declared_a28b.py` md5 `1e8336fc3883c19245bf681d5f26d98f`
```python
"""contract-63c-i-a-a28b — DECLARED mutation set (written BEFORE any mutation run; ids from --collect-only).

Each entry: file (reference-relative), anchor (exact, once), replacement, DECLARED red node ids, targets.
Declared 2026-09-26 (timestamp appended by the driver on first read).
"""

A = "loremaster/tests/test_fixwave_a28b_63c_i_a.py::"
B = "loremaster/tests/test_fixwave_a28_63c_i_a.py::"
RS = "loremaster/tests/test_retry_seam.py::"
TXN = "loremaster/loremaster/store/_txn.py"
AGENTS = "loremaster/loremaster/agents.py"
KEEPS = "loremaster/loremaster/keeps.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
GOVERNED = "loremaster/loremaster/governed.py"
SERVER = "loremaster/loremaster/server.py"

AB = A + "TestTheDriverTypesAnIdentityTakenRejection63cIAa28b::test_am32_1_3_ab_every_raise_site_types_exactly_the_identity_taken_rejection"
SDK = A + "TestTheTypedDiscriminatorDecidesOnTheRunQueryPath63cIAa28b::test_am32_1_3_c_the_unique_violation_class_iff_the_sdk_says_the_record_id_is_taken"
K9 = A + "TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould::test_K9_create_outcome"
KEEPS_TWIN = A + "TestKeepsCasDecidesFromTheOneClass63cIAa28b::test_am32_1_2_keeps_returns_the_winner_iff_the_unique_violation_class_and_a_winner"
KEEPS_8WAY = A + "TestKeepsCasDecidesFromTheOneClass63cIAa28b::test_am32_1_2_the_REAL_unique_key_conflict_converges_eight_way"
RS2 = B + "TestTheRaceNeverStrandsAScope63cIAa28::test_RS2_eight_way_registers_never_strand_a_scope"
RS5H = B + "TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error"
RS5R = B + "TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_eight_identical_first_registers_all_succeed_at_the_registry"
COUNTS = B + "TestTheMeasuredCountsAreTypedFields63cIAa28::"
GATED = B + "TestAFieldIsNoneIffItsReadWasGatedOff63cIAa28b::"
GUARD = RS + "TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_every_door_guards_the_typed_error_ABOVE_its_rollback_handler"

DEFAULT_TARGETS = [
    "loremaster/tests/test_fixwave_a28b_63c_i_a.py",
    "loremaster/tests/test_fixwave_a28_63c_i_a.py",
    RS + "TestNoGuardedCasHandlerReinterpretsExhaustedContention",
    RS + "TestEveryGuardedCasDoorPropagatesExhaustionUNREAD",
]
DOORS_STRUCT = RS + "TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_transactional_doors_never_re_read_after_exhaustion"

MUTATIONS: dict[str, dict] = {
    "MA1-typed-branch-deleted": dict(
        file=TXN,
        anchor=(
            "    if isinstance(raw_result, AlreadyExistsError):\n"
            "        # Typed beats text (amendment 32 §1.1 item 3): the SDK's own discriminator decides.\n"
            "        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED\n"
        ),
        replacement="",
        declared=[f"{SDK}[{kind}-reworded]" for kind in ("Database", "Namespace", "Record", "Session", "Table")],
    ),
    "MA2-record-marker-reworded": dict(
        file=TXN,
        anchor='("database record", "already exists")',
        replacement='("database record", "already existz")',
        declared=[f"{AB}[record-id-collision-execute_transaction]"],
    ),
    "MA3-index-marker-removed": dict(
        file=TXN,
        anchor=', ("database index", "already contains")',
        replacement="",
        declared=[
            f"{AB}[unique-index-collision-run_query]",
            f"{AB}[unique-index-collision-execute_transaction]",
            KEEPS_8WAY,
            RS2,
            RS5H,
        ],
    ),
    "MA4-class-never-built": dict(
        file=TXN,
        anchor="    if error_class == _ERROR_CLASS_UNIQUE_VIOLATION:\n        return TxnUniqueViolationError(message)\n",
        replacement="",
        declared=[
            f"{AB}[record-id-collision-run_query]",
            f"{AB}[record-id-collision-execute_transaction]",
            f"{AB}[unique-index-collision-run_query]",
            f"{AB}[unique-index-collision-execute_transaction]",
            f"{SDK}[Record-engine-wording]",
            f"{SDK}[Record-reworded]",
            KEEPS_8WAY,
            RS2,
            RS5H,
            RS5R,
            A + "TestK7TheRaceLoserIsServedTheSequentialSecondCall::test_K7_the_loser_writes_its_own_mutable_fields",
        ],
    ),
    "MA5-rs5-catches-the-base-class": dict(
        file=AGENTS,
        anchor="            except TxnUniqueViolationError:\n",
        replacement="            except (TxnUniqueViolationError, TxnUniqueViolationError.__mro__[1]):\n",
        declared=[f"{K9}[TxnDomainRejectionError-row-landed]", f"{K9}[TxnGovernedConflictError-row-landed]"],
    ),
    "MA6-keeps-catches-broad": dict(
        file=KEEPS,
        anchor="            except TxnUniqueViolationError:\n",
        replacement=(
            "            except (SurrealConnectionError, TxnContentionExhaustedError):\n"
            "                raise\n"
            "            except TxnUniqueViolationError.__mro__[2]:\n"
        ),
        declared=[
            f"{KEEPS_TWIN}[{cls}-winner-landed]"
            for cls in ("SurrealStoreError", "TxnDomainRejectionError", "TxnEnvelopeViolationError",
                        "TxnGovernedConflictError", "TxnParamCollisionError")
        ],
    ),
    "MS1-rs5-catches-exhaustion-in-a-tuple": dict(
        file=AGENTS,
        anchor="            except TxnUniqueViolationError:\n",
        replacement="            except (TxnUniqueViolationError, TxnContentionExhaustedError):\n",
        declared=[f"{GUARD}[agents.py::register]", f"{K9}[TxnContentionExhaustedError-row-landed]",
                  f"{DOORS_STRUCT}[agents.py::register]"],
    ),
    "MA8-rs5-keys-on-the-engine-text": dict(
        file=AGENTS,
        anchor="            except TxnUniqueViolationError:\n",
        replacement=(
            "            except TxnUniqueViolationError as record_exists:\n"
            "                if \"already exists\" not in str(record_exists.__cause__):\n"
            "                    raise\n"
        ),
        declared=[
            A + "TestK3TheConflictIsClassifiedByClassNotText::test_K3_a_reworded_conflict_still_takes_the_re_register_path",
            f"{K9}[TxnUniqueViolationError-row-landed]",
        ],
    ),
    "MB1-verb-level-omits-message-problems": dict(
        file=PRINCIPALS,
        anchor="    parts.extend(_message_problem_parts(preconditions, counts))\n    parts.append(\n        f\"(The store holds",
        replacement="    parts.append(\n        f\"(The store holds",
        declared=[
            GATED + "test_am32_a_verb_level_refusal_on_message_names_every_measured_problem",
            GATED + "test_am32_one_more_half_pair_row_moves_its_count_and_sentence[message]",
        ],
    ),
    "MB2-am31-literal-message-fields-None-on-verb-refusal": dict(
        file=PRINCIPALS,
        anchor="        result = _refused(table, refusal)\n",
        replacement=(
            "        result = _refused(table, refusal)\n"
            "        counts = counts.model_copy(update=dict.fromkeys((\"dangling_sender_messages\", "
            "\"owned_but_unscoped_messages\", \"scoped_but_ownerless_messages\")))\n"
        ),
        declared=[
            GATED + "test_am32_a_verb_level_refusal_on_message_names_every_measured_problem",
            GATED + "test_am32_one_more_half_pair_row_moves_its_count_and_sentence[message]",
        ],
    ),
    "MB3-am31-control-agent-fields-None-on-leg-refusal": dict(
        file=PRINCIPALS,
        anchor="    return dataclasses.replace(result, preconditions=counts)\n",
        replacement=(
            "    if table == MESSAGE_TABLE and refusal is None and result.refused:\n"
            "        counts = counts.model_copy(update=dict.fromkeys((\"unscoped_agents\", \"owned_but_unscoped_agents\", "
            "\"scoped_but_ownerless_agents\", \"distinct_owner_principals\")))\n"
            "    return dataclasses.replace(result, preconditions=counts)\n"
        ),
        declared=[
            COUNTS + "test_am30_the_served_fields_are_the_measured_counts[P_message]",
            COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[unscoped_agents-P_message]",
            COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[dangling_sender_messages-P_message]",
            COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[owned_but_unscoped_messages-P_message]",
            COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[scoped_but_ownerless_messages-P_message]",
            COUNTS + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[P_message]",
            GATED + "test_am32_the_message_leg_refusal_serves_measured_agent_zeros",
        ],
    ),
    "MB4-owner-sentence-keyed-on-the-operator-object": dict(
        file=PRINCIPALS,
        anchor='    if classification == "unclassified":\n',
        replacement="    if operator is None:\n",
        declared=[COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[owner_classification-P_unclassified]"],
    ),
    "MB5-foreign-N-not-from-the-field": dict(
        file=PRINCIPALS,
        anchor='f"They are owned by {counts.distinct_owner_principals} other principal(s) "',
        replacement='f"They are owned by {len(others)} other principal(s) "',
        declared=[COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[distinct_owner_principals-P_foreign]"],
    ),
    "MC1-gate-skipped-for-any-keeper": dict(
        file=SERVER,
        anchor="            if existing_keep is not None:\n",
        replacement=(
            "            if existing_keep is not None and not await keep_store.list_keeps_for_keeper(principal.email):\n"
        ),
        declared=[
            A + "TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied::test_K8_foreign_probes_by_a_principal_who_keeps_another_session",
            A + "TestC2EveryForeignShapeIsDeniedWithZeroRegistryQueries63cIAa28b::test_am32_C2_foreign_shapes_x_probe_kinds[keeper-of-another-keep]",
        ],
    ),
    "MD2-a-new-registry-class": dict(
        file=AGENTS,
        anchor="class IllegalAgentStatusError(AgentRegistryError):\n",
        replacement=(
            "class AgentQuotaError(AgentRegistryError):\n    \"\"\"a28b mutation: a new registry class.\"\"\"\n\n\n"
            "class IllegalAgentStatusError(AgentRegistryError):\n"
        ),
        declared=[A + "test_am32_C1_every_registry_class_is_provoked_post_mint_or_exempt_with_evidence"],
    ),
    "MD3-retired-name-mentioned": dict(
        file=KEEPS,
        anchor="            The existing or freshly-minted :class:`Keep` bearing ``key``.\n",
        replacement="            The existing or freshly-minted :class:`Keep` bearing ``key`` (minted_by_this_call is gone).\n",
        declared=[A + "test_am32_R2_the_created_only_flag_is_gone_from_the_package"],
    ),
    "MF2-enum-grows": dict(
        file=GOVERNED,
        anchor='Literal["operator", "foreign", "mixed", "unclassified"]',
        replacement='Literal["operator", "foreign", "mixed", "unclassified", "orphaned"]',
        declared=[
            COUNTS + "test_am30_the_counts_model_has_exactly_the_ruled_fields",
            COUNTS + "test_am32_every_field_has_a_perturbation_by_annotation",
        ],
    ),
}


def _mf1_declared(collected: list[str]) -> list[str]:
    """MF1 (a third field TYPE joins the model) — the declared set by RULE over the collected ids (report §6)."""
    reds = [
        COUNTS + "test_am30_the_counts_model_has_exactly_the_ruled_fields",
        COUNTS + "test_am32_every_field_has_a_perturbation_by_annotation",
        COUNTS + "test_am30_pin1_every_field_is_exercised_by_some_population",
        COUNTS + "test_am30_None_means_not_measured[clean-memory-proceeds]",
        GATED + "test_am32_a_verb_level_refusal_on_message_names_every_measured_problem",
        GATED + "test_am32_the_message_leg_refusal_serves_measured_agent_zeros",
        GATED + "test_am32_success_serves_the_measured_object[agent]",
        GATED + "test_am32_success_serves_the_measured_object[message]",
    ]
    reds += [cid for cid in collected if cid.startswith(COUNTS + "test_am30_the_served_fields_are_the_measured_counts[")]
    reds += [cid for cid in collected if cid.startswith(COUNTS + "test_am30_pin1_perturbing_a_field_moves_the_reason[")]
    reds += [cid for cid in collected if cid.startswith(COUNTS + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[")]
    for combo in ("agent-both-defined", "agent-agent-only", "memory-both-defined", "memory-agent-only",
                  "message-both-defined"):
        reds.append(GATED + f"test_am32_a_field_is_None_iff_its_read_was_gated_off[{combo}]")
    return reds


MUTATIONS["MF1-a-third-field-type"] = dict(
    file=GOVERNED,
    anchor='    owner_classification: Literal["operator", "foreign", "mixed", "unclassified"] | None = None\n',
    replacement=(
        '    owner_classification: Literal["operator", "foreign", "mixed", "unclassified"] | None = None\n'
        "    note: str | None = None\n"
    ),
    declared_rule=_mf1_declared,
)


# ---- MA3b (declared 2026-09-26 after MA3 ran DEGENERATE — removing the second marker left a bare 2-string tuple
# (no trailing comma), so the classifier iterated CHARACTERS and matched every text: a broken build, not a pin
# gap). MA3b keeps the 1-tuple. Declared set unchanged from MA3, written before any MA3b run. ----
MUTATIONS["MA3b-index-marker-removed"] = dict(MUTATIONS["MA3-index-marker-removed"], replacement=",")

# ---- ME1 (declared 2026-09-26 ~19:15, before any ME1 run): the handler's register critical section SERIALISED
# per AppContext (an asyncio.Lock), so no register races another: the dup name's role conflicts are refused by
# preflight BEFORE the mint → zero post-mint refusals → RS-2's R-1 non-vacuity leg (and ONLY it) reds. The
# anchor/replacement are GENERATED (the whole block re-indented) into work/ME1-*.{anchor,replacement}. Targets are
# ONLY the three race pins: every nested-register fixture (a winner registered INSIDE the mint) would deadlock on
# the lock — a harness property of this mutation, not a pin result.
MUTATIONS["ME1-handler-serialised"] = dict(
    file=SERVER,
    anchor=None,
    replacement=None,
    declared=[RS2],
    targets=[RS2, RS5H, RS5R],
)


# ---- RE-RUN 2 (declared 2026-09-26 ~20:00, BEFORE any run-2 mutation, after amendment 33's rename and packet 58
# amendment 7 §3 item 1's F-4 re-key): the whole set re-runs on the renamed contract (anchors renamed with it, no
# declared set changed by the rename) with the RS behavioural class added to the targets (MS1 gains the re-keyed
# structural pin, declared above); MS2 is new — packet 58 am-7 §3 item 3's mutation, the static half: the
# calibration door drops its tuple guard → both scanner legs red for that door. ----
MUTATIONS["MS2-record-measurement-drops-its-tuple-guard"] = dict(
    file="loremaster/loremaster/floor_calibration/store.py",
    anchor="        except (SurrealConnectionError, TxnContentionExhaustedError):\n",
    replacement="        except (SurrealConnectionError,):\n",
    declared=[f"{GUARD}[floor_calibration/store.py::record_measurement]",
              f"{DOORS_STRUCT}[floor_calibration/store.py::record_measurement]"],
)

# ---- RE-DECLARED 2026-09-26 20:23 (mtime), BEFORE any run on the PARTITIONED scanner (FK-a28b-4, lead #17087): RS-5 /
# keeps are in _TYPED_CAS_CATCHES now, so a mutation that makes either reachable by exhaustion reds BOTH exact-set
# pins (the door enumeration gains it; the typed enumeration loses it) — never the per-door guard legs, which are
# parametrised over the canonical DOORS only. ----
ENUM_DOORS = RS + "TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set"
ENUM_TYPED = (RS + "TestNoGuardedCasHandlerReinterpretsExhaustedContention::"
              "test_the_typed_catch_enumeration_matches_the_canonical_set_and_the_partition_is_complete")
MUTATIONS["MS1-rs5-catches-exhaustion-in-a-tuple"]["declared"] = [
    ENUM_DOORS, ENUM_TYPED, f"{K9}[TxnContentionExhaustedError-row-landed]"]
MUTATIONS["MA6-keeps-catches-broad"]["declared"] = [
    ENUM_DOORS, ENUM_TYPED,
    *[f"{KEEPS_TWIN}[{cls}-winner-landed]" for cls in ("SurrealStoreError", "TxnDomainRejectionError",
      "TxnEnvelopeViolationError", "TxnGovernedConflictError", "TxnParamCollisionError")]]
```

### §A.5 the mutation driver — `mut/drive_a28b.py` md5 `94bddeafa5456816df65ef243abd08e9`
```python
"""drive_a28b.py <reference-root> [NAME ...] — run scripts/mutation_proof.py for each declared mutation in the
REFERENCE copy (never the main tree), declared set from declared_a28b.py (written before any run). Asserts every
declared id is COLLECTED first (an id that is not collected is a typo, never a pass). Prints one verdict line per
mutation + the tool's exit code; the tool itself restores byte-exact and diffs both ways."""

import datetime
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import declared_a28b as spec  # noqa: E402

root = pathlib.Path(sys.argv[1])
names = sys.argv[2:] or list(spec.MUTATIONS)
python = str(root / ".venv/bin/python")
collected = [
    line.strip()
    for line in subprocess.run(
        [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--collect-only", *spec.DEFAULT_TARGETS],
        cwd=root, capture_output=True, text=True, check=False,
    ).stdout.splitlines()
    if "::" in line
]
work = pathlib.Path(__file__).parent / "work"
work.mkdir(exist_ok=True)
for name in names:
    mutation = spec.MUTATIONS[name]
    declared = mutation["declared_rule"](collected) if "declared_rule" in mutation else mutation["declared"]
    missing = [cid for cid in declared if cid not in collected]
    if missing:
        print(f"{name}: DECLARED ids NOT COLLECTED (typo) {missing}")
        continue
    if mutation["anchor"] is not None:  # ME1: pre-generated files in work/
        (work / f"{name}.anchor").write_text(mutation["anchor"])
        (work / f"{name}.replacement").write_text(mutation["replacement"])
    targets = mutation.get("targets", spec.DEFAULT_TARGETS)
    command = [
        "python3", str(root / "scripts/mutation_proof.py"),
        "--file", mutation["file"],
        "--anchor-file", str(work / f"{name}.anchor"),
        "--replacement-file", str(work / f"{name}.replacement"),
        *[item for cid in declared for item in ("--expect-red", cid)],
        "--", python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", os.environ.get("WORKERS", "8"), "-rfE", *targets,
    ]
    started = datetime.datetime.now().isoformat(timespec="seconds")
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    (work / f"{name}.log").write_text(result.stdout + "\n--- stderr ---\n" + result.stderr)
    verdict_lines = [line for line in (result.stdout + result.stderr).splitlines()
                     if any(word in line for word in ("PROVEN", "MISMATCH", "unexpected", "still GREEN", "restored",
                                                      "passed", "failed", "anchor"))]
    print(f"{name} [{started}] exit={result.returncode} declared={len(declared)}")
    for line in verdict_lines[-6:]:
        print(f"    {line[:300]}")
```

### §A.5b the ME1 anchor/replacement generator (run inline, before ME1's first run)
```python
S = pathlib.Path("<scratchpad>")
src = (S / "ref_prod_backup/server.py").read_text()   # the backed-up REFERENCE server.py (md5 514b3872…, unchanged by the rename)
i = src.index("        session_keep_bare: str | None = None\n        keep_store = self._keep_store\n")
j = src.index("        now = datetime.now(UTC)\n", i)
anchor = src[i:j]
assert src.count(anchor) == 1
body = "".join(("    " + line if line.strip() else line) for line in anchor.splitlines(keepends=True))
replacement = '        async with self.__dict__.setdefault("_a28b_serial", asyncio.Lock()):  # ME1: serialise\n' + body
(S / "mut/work/ME1-handler-serialised.anchor").write_text(anchor)
(S / "mut/work/ME1-handler-serialised.replacement").write_text(replacement)
```

### §A.6 the 20-consecutive concurrency driver — `conc20_a28b.sh` md5 `373d099073594987dbb6f2159402bc7a`
```bash
#!/usr/bin/env bash
# conc20_a28b.sh <tree> <n>: <n> consecutive, SERIAL invocations of the a28b concurrency pins in <tree> (store-ref §5:
# a concurrency pin is cleared only by 20 consecutive greens). Each invocation = RS-2 (20 rounds x 8-way, incl. the R-1
# post-mint-refusal leg) + RS-5 handler (20 x 8) + RS-5 registry (20 x 8) + the keeps REAL unique-key 8-way (20 x 8).
# Stops at the FIRST non-green invocation (a red is a STOP, never "flaky"). Prints one line per run with the pass count.
set -uo pipefail
tree=$1; n=$2
cd "$tree" || exit 2
ids=(
  "loremaster/tests/test_fixwave_a28_63c_i_a.py::TestTheRaceNeverStrandsAScope63cIAa28::test_RS2_eight_way_registers_never_strand_a_scope"
  "loremaster/tests/test_fixwave_a28_63c_i_a.py::TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28"
  "loremaster/tests/test_fixwave_a28b_63c_i_a.py::TestKeepsCasDecidesFromTheOneClass63cIAa28b::test_am32_1_2_the_REAL_unique_key_conflict_converges_eight_way"
)
for run in $(seq 1 "$n"); do
  out=$(.venv/bin/python -m pytest -q -p no:cacheprovider -n 4 -rfE "${ids[@]}" 2>&1)
  code=$?
  tail_line=$(printf '%s\n' "$out" | tail -1)
  echo "run $run: exit=$code :: $tail_line"
  if [ "$code" -ne 0 ] || ! printf '%s' "$tail_line" | awk '/4 passed/ && !/failed/ {ok=1} END {exit !ok}'; then
    printf '%s\n' "$out" | tail -40
    echo "STOP at run $run"
    exit 1
  fi
done
echo "ALL $n CONSECUTIVE GREEN"
```

### §A.7 the operator-ruled watchdog (host MemAvailable < 15 GB → kill the run's PROCESS TREE by PID; positive control: `FLOOR_GB=9999` on a 3-level `sleep 300` tree → exit 137, the whole tree killed, 0 survivors) — `guarded_a28b.sh` md5 `3940003ac0efd22bb68eaaf6d719200d`
```bash
#!/usr/bin/env bash
# guarded_a28b.sh <dir> <logfile> -- <command...>: run <command> in <dir> under the operator-ruled watchdog (2026-09-26:
# host MemAvailable < 15 GB → kill the run's whole PROCESS TREE, by PID — never a pattern, #228). 8 s poll. Watchdog
# events go to <logfile>.watchdog (never the run's own log). Exit = the command's exit, or 137 if the watchdog fired.
set -uo pipefail
dir=$1; log=$2; shift 2; [ "$1" = "--" ] && shift
floor_kb=$((${FLOOR_GB:-15} * 1024 * 1024))
cd "$dir" || exit 2
"$@" > "$log" 2>&1 &
root=$!
echo "$(date -Is) started pid=$root: $*" >> "$log.watchdog"
tree() { local p=$1; echo "$p"; for c in $(ps -o pid= --ppid "$p" 2>/dev/null); do tree "$c"; done; }
fired=0
while kill -0 "$root" 2>/dev/null; do
  avail=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  if [ "$avail" -lt "$floor_kb" ]; then
    pids=$(tree "$root" | tr '\n' ' ')
    echo "$(date -Is) MemAvailable ${avail} kB < ${floor_kb} kB — killing tree: $pids" >> "$log.watchdog"
    kill -TERM $pids 2>/dev/null; sleep 5; kill -KILL $(tree "$root") 2>/dev/null
    fired=1; break
  fi
  sleep 8
done
wait "$root"; code=$?
[ "$fired" -eq 1 ] && code=137
echo "$(date -Is) exit=$code" >> "$log.watchdog"
exit "$code"
```

### §A.7b the quiet-gated SAT runner — `sat_runner.sh` md5 `ce1a506e6f41c11bc0870173d36f5868`
```bash
#!/usr/bin/env bash
# sat_runner.sh: run the full suite on base then ref (ONE tree both ways), each under guarded_a28b.sh (the operator-ruled
# 15 GB MemAvailable watchdog). Before each attempt, WAIT FOR QUIET: host MemAvailable ≥ ${QUIET_GB:-22} GB on 3
# consecutive 20 s checks. A watchdog kill (137) retries that tree after waiting again, up to ${ATTEMPTS:-4} attempts.
set -uo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f02af35b-1f1a-4627-9124-a9bae7a2a67a/scratchpad
quiet_kb=$((${QUIET_GB:-22} * 1024 * 1024))
wait_quiet() {
  local ok=0
  while [ "$ok" -lt 3 ]; do
    avail=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    if [ "$avail" -ge "$quiet_kb" ]; then ok=$((ok + 1)); else ok=0; fi
    sleep 20
  done
}
for tree in base ref; do
  for attempt in $(seq 1 "${ATTEMPTS:-4}"); do
    wait_quiet
    echo "$(date -Is) $tree attempt $attempt starting" >> "$S/sat_runner.log"
    COLUMNS=4000 "$S/guarded_a28b.sh" "$S/$tree" "$S/sat_${tree}_a${attempt}.log" -- \
      .venv/bin/python -m pytest -q -p no:cacheprovider -n "${WORKERS:-4}" --tb=line -rfE
    code=$?
    echo "$(date -Is) $tree attempt $attempt exit=$code :: $(tail -1 "$S/sat_${tree}_a${attempt}.log" | cut -c1-200)" >> "$S/sat_runner.log"
    [ "$code" -ne 137 ] && break
  done
done
echo "$(date -Is) SAT RUNNER DONE" >> "$S/sat_runner.log"
```

### §A.8 the registry stager (HEAD + ONLY the a28 entry; another packet's uncommitted hunk is never staged) — `stage_registry.py` md5 `6fa44d063ef03f94b5613450ddadd288`
```python
"""stage_registry.py: write HEAD's scripts/pending_contracts.yaml with ONLY the a28 entry replaced by the working
copy's (the working copy also carries another packet's uncommitted hunk, which must NOT be staged)."""

import pathlib
import subprocess

OUT = pathlib.Path("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f02af35b-1f1a-4627-9124-a9bae7a2a67a/scratchpad/pending_contracts.staged.yaml")
work = pathlib.Path("scripts/pending_contracts.yaml").read_text()
head = subprocess.run(["git", "show", "HEAD:scripts/pending_contracts.yaml"], capture_output=True, text=True, check=True).stdout


def span(text: str) -> tuple[int, int]:
    start = text.index("# Packet 63c-i-a a28 fix-pass contract (contract-63c-i-a-a28, 2026-09-26")
    lines = text[start:].split("\n")
    kept: list[str] = []
    for index, line in enumerate(lines):
        if index > 0 and line and not line.startswith((" ", "#", "-")):
            break
        if index > 0 and line.startswith("- id:") and "a28" not in line:
            break
        if index > 0 and line.startswith("# ") and kept and kept[-1] == "":
            break
        kept.append(line)
    while kept and kept[-1] == "":
        kept.pop()
    return start, start + len("\n".join(kept))


head_start, head_end = span(head)
work_start, work_end = span(work)
OUT.write_text(head[:head_start] + work[work_start:work_end] + head[head_end:])
print(OUT)
```

### §A.9 the lint rewrap helper (scratch; comment / docstring / bare-literal lines only; code never touched) — `rewrap.py` md5 `c3433acc973f4261d285fe28a790a99b`
```python
"""rewrap.py <file> [limit]: split over-long COMMENT / DOCSTRING-PROSE lines at the last space before ``limit``,
carrying the tail onto a new line with the same indentation (and the same ``#``/``#:`` prefix for comments).
Code lines are never touched; a line with no safe split point is left and reported. Scratch lint helper."""

import re
import sys
import tokenize
import io

path, limit = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 110
source = open(path, encoding="utf-8").read()
# lines that are inside a STRING token spanning >1 line (docstrings / multi-line prose) — safe to split
prose_lines: set[int] = set()
for token in tokenize.generate_tokens(io.StringIO(source).readline):
    if token.type == tokenize.STRING and token.start[0] != token.end[0]:
        prose_lines.update(range(token.start[0] + 1, token.end[0]))  # not the opening line (it has code)
lines = source.split("\n")
out: list[str] = []
left = []
for number, line in enumerate(lines, start=1):
    pending = [line]
    result: list[str] = []
    while pending:
        current = pending.pop(0)
        if len(current) <= limit:
            result.append(current)
            continue
        comment = re.match(r"^(\s*#:?\s?)", current)
        if comment and current.lstrip().startswith("#"):
            prefix = comment.group(1)
        elif number in prose_lines or current.lstrip().startswith('"""'):
            prefix = re.match(r"^(\s*)", current).group(1)
        elif re.match(r'^\s*f?"[^"]*"\s*$', current):
            # a bare (implicitly concatenated) string literal: split into two literals
            indent = re.match(r"^(\s*)", current).group(1)
            body = current.strip()
            is_f = body.startswith("f")
            quote_open = 2 if is_f else 1
            cut = current.rfind(" ", len(indent) + quote_open + 1, limit)
            brace_depth = current[:cut].count("{") - current[:cut].count("}")
            if cut <= 0 or brace_depth != 0 or current[cut + 1 :].strip() in ('"', ""):
                result.append(current)
                left.append(number)
                continue
            head = current[: cut + 1] + '"'
            tail = indent + ("f" if is_f else "") + '"' + current[cut + 1 :]
            result.append(head)
            pending.insert(0, tail)
            continue
        else:
            result.append(current)
            left.append(number)
            continue
        cut = current.rfind(" ", len(prefix) + 1, limit + 1)
        if cut <= len(prefix):
            result.append(current)
            left.append(number)
            continue
        result.append(current[:cut].rstrip())
        pending.insert(0, prefix + current[cut + 1 :])
    out.extend(result)
open(path, "w", encoding="utf-8").write("\n".join(out))
if left:
    print("UNSPLIT lines (original numbering):", left)
```

### §A.10 the SAT both-way diff — `sat_compare.py` md5 `0debd7e6f8879c8afd7e95523bfa5fe3`
```python
"""sat_compare.py <base.log> <ref.log>: the ONE-tree-both-ways SAT diff over pytest `-rfE` summaries. Prints the tail of
each run, red-on-the-reference-only / red-at-base-only / red-in-both counts, the red-in-both split by FILE, and every
reference-only and base-only id (each must be adjudicated individually)."""

import collections
import pathlib
import re
import sys


def reds(path: str) -> tuple[set[str], str]:
    text = pathlib.Path(path).read_text(errors="replace")
    summary = text[text.rindex("short test summary info"):]  # ONLY pytest's own summary section
    # a node id may contain spaces inside its [...] parameters: split at the FIRST " - " (mutation_proof's rule)
    ids = {line.split(" ", 1)[1].split(" - ", 1)[0] for line in summary.splitlines() if line.startswith(("FAILED ", "ERROR "))}
    raw = len(re.findall(r"^(?:FAILED|ERROR) ", summary, re.MULTILINE))
    if raw != len(ids):
        print(f"  ⚠ {path}: {raw} summary lines vs {len(ids)} distinct ids")
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed)", line)]
    return ids, (tail[-1] if tail else "<no tail>")


base, base_tail = reds(sys.argv[1])
ref, ref_tail = reds(sys.argv[2])
print("base:", base_tail)
print("ref :", ref_tail)
print(f"red on the reference ONLY: {len(ref - base)} · red at base ONLY (fixed by the reference): {len(base - ref)} · red in both: {len(base & ref)}")
by_file = collections.Counter(node.split("::")[0] for node in base & ref)
for name, count in sorted(by_file.items()):
    print(f"  both  {count:4d}  {name}")
for node in sorted(ref - base):
    print("  REF-ONLY ", node)
fixed = collections.Counter(node.split("::")[0] for node in base - ref)
for name, count in sorted(fixed.items()):
    print(f"  fixed {count:4d}  {name}")
```

### §A.10b its output — `sat_compare.out` md5 `d70827d937be5030c064eb29320d8e76`
```text
base: 448 failed, 11783 passed, 63 skipped, 3 xfailed, 9 warnings in 2858.02s (0:47:38)
ref : 342 failed, 11893 passed, 63 skipped, 3 xfailed, 9 warnings in 2816.37s (0:46:56)
red on the reference ONLY: 0 · red at base ONLY (fixed by the reference): 106 · red in both: 342
  both     1  loremaster/tests/test_blocks_edge.py
  both    76  loremaster/tests/test_comms_footer.py
  both     4  loremaster/tests/test_findings_enforcement_64b.py
  both    24  loremaster/tests/test_findings_governance_64b.py
  both    22  loremaster/tests/test_findings_identity_64b.py
  both    26  loremaster/tests/test_findings_migrate_64b.py
  both    17  loremaster/tests/test_findings_schema_64b.py
  both    26  loremaster/tests/test_governed_substrate_64b.py
  both    28  loremaster/tests/test_mcp_server.py
  both     3  loremaster/tests/test_reanchor_58_r2_am2.py
  both     6  loremaster/tests/test_reanchor_58_r2_cas_runtime.py
  both    12  loremaster/tests/test_reanchor_58_r2_probes.py
  both    27  loremaster/tests/test_reanchor_58_r2_rulings.py
  both     2  loremaster/tests/test_reanchor_58_r2_scale.py
  both    44  loremaster/tests/test_supersede_reanchor_58.py
  both     5  loremaster/tests/test_task_claimable_partition_58.py
  both    15  loremaster/tests/test_task_guarded_shell_58.py
  both     1  loremaster/tests/test_task_read_surface.py
  both     3  scripts/test_forgery_door_sweep.py
  fixed    2  loremaster/tests/test_fixwave_a19a_63c_i_a.py
  fixed    2  loremaster/tests/test_fixwave_a19b_63c_i_a.py
  fixed   76  loremaster/tests/test_fixwave_a28_63c_i_a.py
  fixed   24  loremaster/tests/test_fixwave_a28b_63c_i_a.py
  fixed    2  loremaster/tests/test_retry_seam.py
```

### §A.11 the shared-red message comparison — `sat_messages.py` md5 `9422f770c0c1b54829ad32b415b31b70`
```python
"""sat_messages.py: for the reds SHARED by both SAT trees, compare the served failure text after normalising per-run
noise (hex / ULID ids, test DB names, timings, the tree's own path) — a shared red whose message CHANGES between the
checkpoint and the reference is a red the build moved, and must be adjudicated, not waved through."""
import re
S = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f02af35b-1f1a-4627-9124-a9bae7a2a67a/scratchpad/"


def msgs(tree: str) -> dict[str, str]:
    text = open(S + f"sat_{tree}_a1.log", errors="replace").read()
    summary = text[text.rindex("short test summary info"):]
    out = {}
    for line in summary.splitlines():
        if line.startswith(("FAILED ", "ERROR ")):
            node, _, msg = line.split(" ", 1)[1].partition(" - ")
            msg = msg.replace("/scratchpad/base/", "/scratchpad/TREE/").replace("/scratchpad/ref/", "/scratchpad/TREE/")
            msg = re.sub(r"[0-9a-f]{8,}|[0-9A-HJKMNP-TV-Z]{26}|test_\d+_[0-9a-f]+|\d+\.\d+s|0x[0-9a-f]+", "#", msg)
            out[node] = re.sub(r"[A-Za-z0-9_\-]{30,}", "#", msg)
    return out


base, ref = msgs("base"), msgs("ref")
shared = set(base) & set(ref)
empty = [node for node in shared if not base[node] or not ref[node]]
differ = sorted(node for node in shared if base[node] != ref[node])
print(f"shared {len(shared)} · empty-message {len(empty)} · messages differing after normalisation {len(differ)}")
for node in differ:
    print("DIFF", node)
    print("   base:", base[node][:300])
    print("   ref :", ref[node][:300])
```

### §A.12 the quiet-gated currency runner — `currency_runner.sh` md5 `8c85904e7be6dc8befef7932972131c3`
```bash
#!/usr/bin/env bash
# currency_runner.sh: `pending_contract_gate.py --currency` on the main tree under the watchdog, quiet-gated
# (MemAvailable >= QUIET_GB on 3 consecutive 20 s checks), up to ATTEMPTS attempts on a watchdog kill (137).
set -uo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f02af35b-1f1a-4627-9124-a9bae7a2a67a/scratchpad
quiet_kb=$((${QUIET_GB:-26} * 1024 * 1024))
for attempt in $(seq 2 $((${ATTEMPTS:-4} + 1))); do
  ok=0
  while [ "$ok" -lt 3 ]; do
    avail=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    if [ "$avail" -ge "$quiet_kb" ]; then ok=$((ok + 1)); else ok=0; fi
    sleep 20
  done
  echo "$(date -Is) currency attempt $attempt starting" >> "$S/currency_runner.log"
  "$S/guarded_a28b.sh" /home/ejprice/PycharmProjects/lore "$S/currency_${attempt}.log" -- uv run python scripts/pending_contract_gate.py --currency
  code=$?
  echo "$(date -Is) currency attempt $attempt exit=$code" >> "$S/currency_runner.log"
  [ "$code" -ne 137 ] && break
done
```

### §A.11b the shared-red message comparison's output (head — the 5 differing reds)
```text
shared 342 · empty-message 0 · messages differing after normalisation 5
DIFF loremaster/tests/test_findings_migrate_64b.py::TestAnOwnedButUnscopedRowIsAHalfPairForEveryUnownedLegacyTable::test_CONTROL_without_the_trap_the_same_store_backfills[finding]
   base: AssertionError: MigrateGovernedResult(table='finding', scanned=None, backfilled=0, already_migrated=None, refused=True, reason="migrat...essage` and `brief` (`brief`'s backfill lands at packet 63c-ii; task/finding land at 64); nothing was read or written")
   ref : AssertionError: MigrateGovernedResult(table='finding', scanned=None, backfilled=0, already_migrated=None, refused=True, reason="migrat...(`brief`'s backfill lands at packet 63c-ii; task/finding land at 64); nothing was read or written", preconditions=None)
DIFF loremaster/tests/test_findings_migrate_64b.py::TestAnOwnedButUnscopedRowIsAHalfPairForEveryUnownedLegacyTable::test_the_trap_refuses_byte_inert_naming_count_and_ids[memory]
   base: AssertionError: --table memory PROCEEDED past owned-but-unscoped rows: MigrateGovernedResult(table='memory', scanned=3, backfilled=3, already_migrated=0, refused=False, reason=None)
   ref : AssertionError: --table memory PROCEEDED past owned-but-unscoped rows: MigrateGovernedResult(table='memory', scanned=3, backfilled=3, already_migrated=0, refused=False, reason=None, preconditions=MigratePreconditionCounts(unscoped_agents=0, owned_but_unscoped_agents=0, scoped_but_ownerless_agents=0,
DIFF loremaster/tests/test_governed_substrate_64b.py::TestResourceFromRowDerivesTheTable::test_resource_from_row_is_the_only_production_Resource_constructor
   base: AssertionError: production constructs lorerunes.Resource outside governed.resource_from_row (#414/#415 — the table must be DERIVED from the row id, in ONE place): [('loremaster/loremaster/governed.py', 'authorize_guarded', 493)]
   ref : AssertionError: production constructs lorerunes.Resource outside governed.resource_from_row (#414/#415 — the table must be DERIVED from the row id, in ONE place): [('loremaster/loremaster/governed.py', 'authorize_guarded', 511)]
DIFF loremaster/tests/test_reanchor_58_r2_rulings.py::TestAHealStoreFaultIsLOUD::test_the_heal_READS_what_the_backfill_minted_in_the_SAME_boot
   base: AssertionError: ['= connection is CONNECTING', '> GET /rpc HTTP/1.1', '> Host: 127.0.0.1:18000', '> Upgrade: websocket', '> Connection: Upgrade', '> Sec-WebSocket-Key: Ol/rjz1F7K+PHdyYamGLtA==', ...]
   ref : AssertionError: ['= connection is CONNECTING', '> GET /rpc HTTP/1.1', '> Host: 127.0.0.1:18000', '> Upgrade: websocket', '> Connection: Upgrade', '> Sec-WebSocket-Key: gi8Qt9Qge1yJCxIMWC1WNg==', ...]
DIFF loremaster/tests/test_supersede_reanchor_58.py::TestEveryDependentFollowsTheWorkToTheSuccessor::test_direct_dependents_of_X_is_EMPTY_and_of_the_successor_is_the_whole_set
   base: AssertionError: assert ['#...d93a11d', ...] == []
   ref : AssertionError: assert ['#...b9a7b58', ...] == []
```
