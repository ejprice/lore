brief-base v16 read · brief project v7 read

# REPORT-contract-63c-i-a-a28 — contract for the 63c-i-a fix pass (amendments 26–30)

## SUMMARY BLOCK
- **state:** done-with-deviations (D-1…D-6, §4)
- **deviations:** D-1 one targeted run overlapped two FOREIGN lore pytest sessions (disclosed, re-run clean) · D-2 the M02 / M03 wrong builds as first written were degenerate / partial (M02b / M03b re-run; both receipts kept) · D-3 `test_message_enforcement_63b_ii_a.py` edited (the A5 golden — in my writable set, a pre-existing file) · D-4 the reference's `principals.py` was `ruff format`ted (scratch only) · D-5 KP1/KP2/KP3 re-keyed, no longer AST-equal to the adversary's graded probes (DUAL) · D-6 mutation batch paused mid-run for the lead's lane re-order (#17067).
- **Packages considered:** none — no mechanism specified (pins; the one new production model is the ruling's own `MigratePreconditionCounts`, a pydantic `BaseModel` per amendment 30's `model_fields`)
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 18 new test-local symbols, all dispositioned (§11); lore_search FAILED on 2 of 3 DRY queries (#495) — fallback said
- **Graded:** n/a — contract author (base: checkpoint `169925f`; HEAD-at-report `3861050`; 63c production byte-identical `169925f`→`3861050` — the only `loremaster/loremaster` drift is #466's `testing/loopback.py`)
- **decisions-needed:** FK-a28-3 (am-30 pin (2) vs amendment 20's owner-diagnosis integers) and FK-a28-4 (does a `--table message` verb-level refusal restate the message counts?) — both NON-blocking, pins written agnostic (§F)
- **RED @ `169925f` (production):** 45 failed / 118 passed over the 4 changed files, every RED for the ruled reason (§5) · **SAT:** full suite on ONE tree both ways — reference 207 red / base 252 red; red-on-reference-only **0**; the 45 fixed; all 207 shared reds adjudicated (58: 86 · 64b: 119 · 2 non-63c tree scans); **63c-attributable 0** (§8) · **Concurrency:** 20/20 consecutive invocations green on the reference (each = 3 pins × 20 rounds × 8-way); checkpoint strands 4/20 and 6/20 rounds (§7)
- **Mutation:** 18/18 final wrong builds killed (declare-then-diff, both ways); 5 first-attempt receipts kept (2 extra-kill prediction misses, 1 degenerate build, 1 other-pin kill, 1 REAL pin gap closed — pin (2) gained ⊇) (§6)
- **Currency:** bound `packet-63c-i-a-a28-contract` (via amendment 30's ruled pair; FK-a28-2/#461 resolved by am-30). `--currency`: typecheck RED_ADJUDICATED · ruff GREEN · pytest RED_ORPHANED 6 — **all 6 in contract-58-r2's untracked `test_reanchor_58_r2_cas_runtime.py`; a28 orphans 0** (§9)
- **receipt pointers:** §F forks · §1 required-green · §2 per-item table · §3 DUAL · §4 deviations · §5 RED · §6 mutation proofs · §7 concurrency · §8 SAT · §9 currency · §10 BUILDER CONSTRAINTS · §11 DRY ledger · §12 residuals · §13 narrow-adversary attack list · §A instruments verbatim

## §0 Capability check (brief-base §4)
- lore: registered (`contract-63c-i-a-a28` / `63c-20260924` / contract / ≤20m). `lore_search` served a bare `SurrealDB query failed against 'ws://127.0.0.1:18500/rpc': '<uuid>'` on 2 of 3 DRY-ledger queries, twice each → filed **#495**; code structure otherwise read by `Read`/`awk` (grep is hook-blocked, #473) — said here.
- The brief's CURRENCY demand was **unmeetable by construction** at spawn: amendments 26–29 introduce no new symbol, and a pytest-only RED is unregistrable (#461 — annotated with this recurrence). **Resolved** mid-run by amendment 30, whose ruled pair (`MigratePreconditionCounts`, `MigrateGovernedResult.preconditions`) gives the #461/lead-#17055 static-reference shape (§9). No mypy error was manufactured.
- One `rm -rf` (a `__pycache__` in my own scratch) was permission-DENIED; re-done without it (the anchor check skips non-mutation dirs). Nothing retried by another route.

## §F FORKS (written BEFORE the pins that depend on them)

### FK-a28-1 — amendment 28 Addendum A4: where are the measured precondition counts served? → **RULED: Reading B (amendment 30, directive #17062, acked)**
Asked 2026-09-26 (thread `q:63c-a28-A4`, #17061) with Reading A (counts in `reason`) as my pick. Amendment 30 ruled B: ONE nested model `MigratePreconditionCounts` (six `int | None` fields) on `MigrateGovernedResult.preconditions`, the `reason` text DERIVED from the fields. My Reading-A pin was deleted before any commit (it was never committed; no DUAL needed) and replaced by the am-30 pins (§2 row 11).

### FK-a28-2 — the brief's CURRENCY requirement vs #461 → **RESOLVED by amendment 30**
Measured at spawn: `PendingContractRegistry` only owns a pytest RED in a file that also carries a mypy error naming a missing symbol (`pending_contract_gate.py::PendingContractRegistry._entries_must_state_a_claim` + the "produced NO mypy errors" self-destruct leg). Amendments 26–29 name no new symbol, so the a28 REDs were unownable without manufacturing an error. Amendment 30's ruled pair is a genuine not-yet-built symbol; three files carry it in a runtime-inert `if TYPE_CHECKING:` block (§9). ⚠ Stated plainly: for `test_fixwave_a19a`/`a19b` the pair is a PROXY for "the a28 build landed" (their REDs are about the race / KP2-3, not the model); that is the 58/64b precedent (lead directive #17055), and it is flagged for the adversary (§13 item 9).

### FK-a28-3 — amendment 30 pin (2) vs amendment 20 §8.4's owner diagnosis (NOT blocking; pins written agnostic)
Amendment 30: *"The bounded id samples … are the ONLY integers `reason` may carry that are not in the fields."* But the standing §2.1 diagnosis (amendment 20 §8.4, pinned by a19's R-Q5-1 `_assert_the_derived_diagnosis`) serves *"N of them are owned by the operator"* and *"N are owned by K other principal(s) (first k named …)"* — `K` and the operator-owned `N` are not among the six fields. Two readings:
- **(a) (my pick):** pin (2) scopes to the COUNT clauses of the six populations; the owner-classification sub-clause is a derived diagnosis (am-20), not a precondition count, and keeps its integers.
- **(b):** the owner diagnosis must drop its integers or gain fields — which would re-open am-20's pins.
My pin (2) uses populations whose owners are ALL the operator (P_agent), so its one diagnosis integer equals `owned_but_unscoped_agents` and the pin does not rule the fork either way. Also stripped as non-counts (stated in `_NON_COUNT_SHAPES`): the id-sample phrase, and CITATION shapes (`§2.1`, `pkt-62–63b`, `amendment-1`, `E3`) that today's prose carries.

### FK-a28-4 — does a VERB-level refusal on `--table message` restate the message counts? (NOT blocking; pins agnostic)
On `--table message` the shared read measures the message facts BEFORE the verb-level §2.1 check, so under am-30/am-22 §4 they are measured → the typed fields carry them. Am-30 says "the reason text DOES restate the counts"; am-27 FORK-2 says the verb-level refusal "stays a separate, earlier answer". My pick: the typed fields carry every measured count; the verb-level `reason` restates only its own clauses. Pins are written so both readings pass: pin (2) is ⊆ (no stray integers), pin (1) runs on populations whose served refusal owns the clause, and the FORK-2 verb-level pin forbids only the message leg's own refusal (`before migrating \`message\``), not a restated count.

### Note (not a fork): am-30 says `MigrateGovernedResult` stays `extra="forbid"` — it is a frozen `@dataclass` (governed.py), not a pydantic model; the forbid property is pinned on `MigratePreconditionCounts` (pydantic, per the ruling's `model_fields`). Placement `loremaster.governed` is my pick (beside `MigrateGovernedResult`; unruled) — a builder constraint (§10).

## §1 Required-green enumeration (written BEFORE the pins; re-checked by SAT)
A correct a28 build keeps GREEN:
1. The whole 63c-i-a contract as amended through a19/a19a/a19b, minus the DUAL-deleted pins (§3): `test_fixwave_a19_63c_i_a.py`, `test_fixwave_a19a_63c_i_a.py`, `test_fixwave_a19b_63c_i_a.py`, `test_agent_governance_63c_i_a.py`, `test_agent_registry.py`, the 63b-ii-a message migrate / enforcement / send-scope suites, `test_comms_tool.py` — both helper shapes (`_governed_world`, `credentialed_app_context`).
2. Single-principal stores unchanged on EVERY governed table: legacy agent / memory / message backfills proceed and stamp; idempotent re-runs (a28 FORK-1's second run backfills 0 on every leg); memory-only stores migrate memory.
3. Tokenless register mints no keep; every registry refusal precedes the mint (#485, a19a runtime property + refusal fixtures); the credentialed success path mints ONE keep; KP4 (the race serves the registry's teaching); KP13; KP14 (a failed mint is loud).
4. The SF-63-1 foreign denial still denies (now BEFORE any registry read); the keeper's household proceeds; the post-mint re-check still denies a keep minted meanwhile.
5. The message leg's refusals (dangling, both halves) stay byte-inert with `None` receipts; the ORDER-only refusal text is unchanged when no row fact is present.
Receipts: §8 (targeted 1572 passed / 0 failed on the reference; full suite §8).

## §2 Per-item table
File: **a28** = `loremaster/tests/test_fixwave_a28_63c_i_a.py` (NEW). Wrong builds = §6.
| # | ruling item | pin(s) | wrong builds killed |
|---|---|---|---|
| 1 | am-28 §F-1 NO compensation — RS-2 | a28 `TestTheRaceNeverStrandsAScope63cIAa28::test_RS2_eight_way_registers_never_strand_a_scope` (8-way `asyncio.gather`, one principal, fresh session per round, 20 rounds; ∀ rows `scope` = THE live session keep; `delete_keep` spy = 0; non-vacuity: every round refused ≥1) | M01 |
| 2 | am-28 §F-1 recipe + Addendum A1 | a28 `…::test_the_sequential_race_keeps_the_keep_and_serves_the_teaching[handler-winner-found-the-keep \| tokenless-winner-control]` (winner re-keyed to a same-principal HANDLER register that FOUND K; ownerless winner = the tokenless control; served == registry teaching; K resolves; a third register FINDS K) | M01, M02b |
| 3 | am-28 KP1 re-key | a19b `test_KP1_…` (winner is a handler register that mints; this call finds; winner `scope` == live K) | M01 |
| 4 | am-28 §F-2 ORDER — RS-3 | a28 `TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28::test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads` (role / spawned_by / retired / absent → 4 byte-identical `GovernedDenied`; `_select_row`/`preflight`/`register`/`get_or_create_keyed` = 0 calls; tables byte-identical) + `…_CONTROLS_…` (householded bob proceeds + re-registers; keeper still taught the role) | M03, M03b, M04, M05 |
| 5 | am-28 §F-2 ORDER | a28 `…::test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register` (fresh + existing session) · `…::test_the_POST_MINT_recheck_denies_a_keep_minted_meanwhile_by_another_principal` | M03b, M05 · M06 |
| 6 | am-29 RS-5 | a28 `TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error` (per round: 1 first / 1 re-register / 2 conflicts, no store error, ONE row) + `…::test_RS5_eight_identical_first_registers_all_succeed_at_the_registry` | M07 |
| 7 | am-27 FORK-1 | a28 `TestBackfilledIsMeasuredOnEveryLeg63cIAa28::test_FORK1_backfilled_equals_the_rows_the_run_changed[<leg>]` — parametrised over a19a's DERIVED `_migrate_legs()`, memory included; a leg with no population fails by name | M08 |
| 8 | am-26 + am-29 F-8 | a28 `TestTheMessageLegServesOneRefusalInCheckOrder63cIAa28::test_am26_RS1_…` (RS-1 verbatim; per-clause count) · **audit F-8 on the door-#2 pin itself:** a19b `TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[…]` re-keyed to `a28._clause_count` (each half's count INSIDE its own clause) | M10, M10r, M16 |
| 9 | am-27 FORK-2 + F-8 | a28 `…::test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal` (2/3/4/5 — every clause a DIFFERENT count, attributed inside its own clause; control: migrate agent → the rest) · `…::test_FORK2_the_verb_level_refusal_stays_a_separate_EARLIER_answer` | M09, M10, M16 |
| 10 | am-28 A5 | a28 `TestTheMessageBackfillGuardsTheSender63cIAa28::test_A5_…` (one unsound sender PER CONJUNCT + dangling + ownerless) + golden `test_message_enforcement_63b_ii_a.py::_MIGRATE_MESSAGE_GOLDEN` (executed-golden pin a19a `test_the_message_backfill_EXECUTES_the_golden`) | M14, M15 |
| 11 | am-28 A2 | a28 `TestAWrongShapedDependencyFailsClosed63cIAa28::test_A2_an_unexpected_INFO_FOR_DB_shape_raises_byte_inert[table × {list,str,keyless-dict}]` (12) + `…_a_non_list_precondition_row_answer_…[{agent,message} × {dict,str}]` (4); landed-counter (#194) + control | M11, M12 |
| 12 | am-28 A4 / am-30 | a28 `TestTheMeasuredCountsAreTypedFields63cIAa28`: `…_the_counts_model_has_exactly_the_ruled_fields` · `…_the_served_fields_are_the_measured_counts[P_agent\|P_message]` · `…_None_means_not_measured[invalid-table\|clean-memory-proceeds]` · pin (1) `…_pin1_perturbing_a_field_moves_the_reason[<6 fields>]` (identity-sweep rebind of THE model to a perturbing subclass; landed check) · pin (2) `…_pin2_every_count_in_the_reason_is_a_field_value[P_agent\|P_message\|RS-1]` · pin (3) a19b KP2/KP3 read the fields · docstring `…test_A4_no_docstring_claims_a_refusal_scans_nothing` | M13, M17, M18, M19 |
| 13 | am-28 DUAL deletions | §3 | — |

## §3 DUAL — every pin deleted, re-keyed or re-worded (each carries an in-place DUAL comment)
| # | site | old | new | virtue | verdict |
|---|---|---|---|---|---|
| U1 | a19a `test_the_RACE_compensation_deletes_only_a_keep_this_call_created[created-by-this-call\|found-pre-existing]` (the CREATED-ONLY pin) | the race's created keep is deleted; a found keep is not | DELETED (in-place DUAL comment) | (a) "a keep the race created is removed so the next principal keeps the session" (b) "a found keep is never deleted" | (a) DROPPED deliberately — mechanism removed (am-28 §F-1: its only principal-bearing trigger strands the winner; audit F-2/P5); the tokenless case is the named β bound, re-pinned as a28's tokenless control; (b) PRESERVED-with-pin, widened ∀ keeps (a28 `delete_keep` spy = 0) |
| U2 | a19b `TestAFailedCompensationIsNamedToTheCaller63cIAa19b::test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line` (the #4b APPENDED-REMEDY-LINE pin and the FAILED-DELETE pin — one test) | failed delete → teaching + ONE "LEFT BEHIND … `lore-adm delete-keep`" line | DELETED (in-place DUAL comment) | (a) teaching verbatim, same class (b) remedy line (c) delete attempted | (a) PRESERVED by construction (KP4 + a28 sequential served==registry); (b) DROPPED — nothing deletes, so nothing is left behind by a failed delete (am-28 Addendum (3); audit F-5/F-7/F-9 MOOT); (c) INVERTED (never called) |
| U3 | a19a `_RegisterPropertySpy` race branch + `test_EVERY_driven_register_meets_the_runtime_property` race leg | race ⇒ "keep byte-identical after the compensation" | race ⇒ refusal after ONE mint, minted keep LEFT (`not keep_identical`) | "only the race may refuse after a mint" | PRESERVED; the "compensated" half DROPPED with the mechanism |
| U4 | a19b `test_KP1_…` | ownerless registry-level winner mints; assert keep survives | handler winner mints; assert keep survives AND winner `scope` == live K | "the concurrent winner's keep survives" | PRESERVED-with-pin, re-keyed (am-28 §F-1 DUAL + Addendum A1: the ownerless winner was blind to F-1) |
| U5 | a19b `test_KP2_…` / `test_KP3_…` | true count read from prose | + the typed field (`dangling_sender_messages` / `scoped_but_ownerless_agents`) | the prose legs | PRESERVED; field leg ADDED (am-30 pin (3)) |
| U6 | `test_message_enforcement_63b_ii_a.py::_MIGRATE_MESSAGE_GOLDEN` | `… WHERE scope IS NONE AND owner_principal IS NONE` | `… AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE` | CD-1's target conjuncts | PRESERVED (unchanged, first); sender guard APPENDED (am-28 A5) |
| U8 | a19b door-#2 `test_a_message_half_pair_refuses_the_message_leg_byte_inert` | `len(ids) in stated` (the count anywhere in the reason) | the count INSIDE its own clause (`a28._clause_count`) | "the TRUE count of each half is stated" | PRESERVED-with-pin, re-keyed (audit F-8 / am-29: M10 swapped the halves and the old assertion stayed green; M10r reds all three cases) |
| U7 | a19a module comment "the concurrent race is compensated by deleting ONLY a keep this call CREATED"; a19b module docstring | prose | re-worded (DUAL) | — | prose follows the mechanism |

## §4 DEVIATIONS
- **D-1** My first targeted reference run (`ref_targeted.log`, 638 passed) overlapped two FOREIGN lore pytest sessions (a lead `redhead` baseline + a gated verify) — I checked the table and ran anyway. Every later run went through the lane waiter (§A.1); the targeted re-run (1572 passed) and all RED/mutation/concurrency runs were lane-clear.
- **D-2** M02 as first written keyed its guard on list truthiness; `SELECT count() … GROUP ALL` returns `[{'count': 0}]` on 3.2.4 (probed, §A.8 — both an empty filter and an empty table), so it never deleted — a degenerate wrong build, not a pin gap. M02b keys on the count value. M03 left the read-only `get_by_key` in place (a reads-but-doesn't-gate build): RS-3 caught it, the ORDER pin (which checks the read order) correctly did not; M03b removes the read too (the true checkpoint order). Both first receipts kept (§6).
- **D-3** `_MIGRATE_MESSAGE_GOLDEN` edited (A5) — in `loremaster/tests/**`, but a pre-existing oracle file; DUAL in place.
- **D-4** The reference build's `principals.py` was `ruff format`ted in the scratch copy (anchors re-derived after, §A.6). Scratch only.
- **D-5** KP1/KP2/KP3 re-keyed — no longer AST-equal to the adversary's graded probes (a19b's §3 receipt no longer covers them).
- **D-6** The lead re-ordered the lane (#17067) mid-batch: the driver loop was stopped after M03 (the in-flight mutation finished and restored byte-exact — `md5sum -c` OK over all five production files) and resumed after refactor-466's acceptance run.

## §5 RED @ `169925f` (production) — main tree, HEAD `66868bc`, 63c production byte-identical to `169925f`
`uv run pytest -n 12 … test_fixwave_a28 … a19a … a19b … test_message_enforcement_63b_ii_a` → **45 failed, 118 passed** (lane-clear 13:51:56). Reasons (deduplicated `--tb=line`):
| count | pin(s) | the served failure (verbatim head) | right reason? |
|---|---|---|---|
| 12 | A2 INFO shapes | `DID NOT RAISE SurrealStoreError` (fail-open `else {}`) | yes |
| 4 | A2 row shapes | `DID NOT RAISE SurrealStoreError` (`_governed_select` fail-open) | yes |
| 7 | am-30 served / pin1 ×6 … | `loremaster.governed.MigratePreconditionCounts does not exist — amendment 30 …` | yes (unbuilt) |
| 7 | am-30 pin2 ×3, None ×2, … | `MigrateGovernedResult has no \`preconditions\` field — amendment 30 …` | yes (unbuilt) |
| 2 | sequential race ×2 | `the session keep K must SURVIVE the refused register: []` | yes (the compensation) |
| 1 | RS-2 | `amendment 28 §F-1: 4/20 rounds left agent rows whose scope does not resolve …` | yes |
| 1 | RS-3 | `role-conflict: ('AgentIdentityConflictError', "… role ```secretrole``` …")` | yes (the leak) |
| 1 | ORDER | `['preflight', 'mint', 'get_by_key:session:s-order', 'register', …]` | yes |
| 2 | RS-5 ×2 | `TxnDomainRejectionError: SurrealDB agent query rejected …` (7 per round at the registry) | yes |
| 1 | FORK-1 agent | `backfilled=3 but 2 row(s) changed` | yes (audit F-3) |
| 1 | FORK-2 | `positions=[70, -1, -1, -1]` (ORDER refusal alone) | yes (audit F-4) |
| 1 | A5 | `a message whose SENDER is ownerless/unscoped or dangling was stamped` | yes |
| 1 | docstring | `MigrateGovernedResult's docstring still claims … before any scan` | yes |
| 1 | a19a runtime property | `race … refused=True, mints=1, injected=True, keep_identical=True` (compensated) | yes |
| 1 | a19a EXECUTES golden | `CD-1: the message backfill must execute THE golden` (no sender guard) | yes |
| 2 | a19b KP2 / KP3 | `amendment 30: the refusal must serve preconditions.<field>` | yes |
GREEN at `169925f` by design (required-green or discriminating only on wrong builds): KP1 (this call FOUND the keep — the checkpoint never deleted a found keep), RS-3 CONTROLS, post-mint re-check, am-26 RS-1, FORK-2 verb-level, FORK-1 memory/message.

## §6 Mutation proofs — declare-then-diff, both ways (`scripts/mutation_proof.py`, run in the reference copy)
Declared sets: `mut/declared.py` (§A.5), ids verified against `--collect-only` (163 collected) BEFORE any run; timestamps `13:38:55` (M01–M17 first declared), `13:39:22` (KP13 removed from M05 before any run), `13:47:08` (M10/M13/M16 anchors re-derived after the reference format pass + M18/M19 added, before any run), `13:58:42` (M02b/M03b added after M02/M03 ran — see D-2), `14:57:35` (M19r, after pin (2) gained ⊇), `15:28:31` + `15:28:42` (M10r, after the a19b door-#2 re-key; its two single-half cases added by reasoning before the run). Target: the four changed files, `-n 8`; M01/M02/M02b add `-k "not RS5"` (two concurrent deletes race a `KeepNotFoundError` into an RS-5 caller nondeterministically; RS-5 is graded by M07). Each run restored byte-exact (the tool's own receipt + `md5sum -c` over all five production files).
| mut | wrong build | declared RED | observed | verdict |
|---|---|---|---|---|
| M01 | the checkpoint-class compensation, unguarded (delete on any post-mint refusal) | RS-2, sequential ×2, a19a runtime, KP1 | 5 failed / 156 passed | **HELD** |
| M02 | guarded delete keyed on `if not scoped` | sequential[tokenless], a19a runtime | 161 passed | **FAILED — degenerate wrong build** (D-2: `count() GROUP ALL` → `[{'count': 0}]` on 3.2.4, §A.8; it never deletes) |
| M02b | guarded delete keyed on the count VALUE (am-28's rejected alternative) | sequential[tokenless], a19a runtime | 2 failed | **HELD** |
| M03 | the deny branch removed, the read-only READ left | RS-3, ORDER | RS-3 red; ORDER green | **FAILED — prediction miss** (D-2): a reads-but-doesn't-gate build keeps the read ORDER; RS-3 is the pin that kills it |
| M03b | the true checkpoint order (gate + read removed: preflight → mint → gate) | RS-3, ORDER | 2 failed | **HELD** |
| M04 | the gate READS THE REGISTRY first (`_select_row` before `get_by_key`) | RS-3 | 1 failed | **HELD** (the denials stay byte-identical — only the registry-read spy sees it) |
| M05 | the gate MINTS (`get_or_create_keyed` in place of the read) | RS-3, ORDER, a19a runtime + 6 refusal fixtures + handler-order | 12 failed: the 10 declared + a19a `test_CONTROL_a_valid_register_mints_exactly_one_keep` + a19b KP1 | **FAILED — extra reds, each a correct kill** (the second mint trips the CONTROL's "exactly one mint" and KP1's call count) |
| M06 | the post-mint re-check dropped | post-mint re-check | 1 failed | **HELD** |
| M07 | the registry's CREATE conflict re-raised (no re-read) | RS-5 ×2 | 2 failed | **HELD** |
| M08 | agent `backfilled` = the scope-keyed pre-count | FORK-1[agent] | 1 failed | **HELD** |
| M09 | the ORDER refusal served ALONE (the checkpoint's FORK-2 behaviour) | FORK-2 | 5 failed: FORK-2 + pin1[dangling, owned_msg, scoped_msg, unscoped] | **FAILED — extra reds, each a correct kill** (the ORDER-only text has no message clauses and renders the count from `preconditions.unscoped_count`, not the model) |
| M10 | the two half clauses' counts SWAPPED (F-8) | FORK-2, RS-1 | 2 failed | **HELD** (a19b's door-#2 pin stays green — the F-8 gap the audit named; FORK-2 is the pin that sees it) |
| M10r | M10 re-run after a19b's door-#2 re-key (U8) | FORK-2, RS-1, a19b door-#2 ×3 | 5 failed | **HELD** |
| M11 | `INFO FOR DB` fail-open (`else {}`) | A2 INFO ×12 | 12 failed | **HELD** |
| M12 | `_governed_select` fail-open | A2 rows ×4 | 4 failed | **HELD** |
| M13 | the verb refusal does not restate `unscoped_agents` | pin1[unscoped_agents] | 1 failed | **HELD** |
| M14 | sender guard without `sender.scope IS NOT NONE` | A5, a19a EXECUTES golden | 2 failed | **HELD** |
| M15 | sender guard without `sender.owner_principal IS NOT NONE` | A5, a19a EXECUTES golden | 2 failed | **HELD** |
| M16 | dangling clause AFTER the half-pairs | FORK-2, RS-1 | 2 failed | **HELD** |
| M17 | a docstring claims "before any scan" again | docstring pin | 1 failed | **HELD** |
| M18 | half clauses render `len(ids)` (private ints), not the model | pin1[owned_msg, scoped_msg] | 2 failed | **HELD** |
| M19 | message counts never measured (`None`) | served[P_message], pin1 ×3, pin2[P_message], pin2[RS-1], KP2 | 7 failed; pin2 ×2 STAYED GREEN; FORK-2 + RS-1 red (undeclared) | **FAILED — a REAL GAP in pin (2)**: it was ⊆-only, so a reason rendering `None` passed it. Pin (2) gained its ⊇ leg (every measured non-zero count is stated) |
| M19r | M19 re-run after the ⊇ leg (FORK-2 / RS-1 now declared — declared-after-seeing, said so) | 9 ids | 9 failed | **HELD** |
Summary: **18 of 18 final wrong builds killed** (M01, M02b, M03b, M04–M18, M10r, M19r); 5 first-attempt receipts kept honestly: 2 prediction misses in the extra-kill direction (M05, M09), 1 degenerate wrong build (M02), 1 reads-but-doesn't-gate build killed by the other pin (M03), 1 real pin gap closed (M19 → pin (2) ⊇). ⚠ M01–M18 ran BEFORE pin (2)'s ⊇ leg existed; the leg can only ADD reds to them (M09 and M13 would each gain `pin2[…]`), never remove one.

## §7 Concurrency receipt
- **Reference, 20 consecutive invocations** (`conc20.sh`, serial, lane-clear, `-k "RS2 or RS5"`): `run 1 … run 20: 3 passed, 34 deselected` — **20/20**. Each invocation runs RS-2 (20 rounds × 8-way handler registers), RS-5 handler (20 × 8) and RS-5 registry (20 × 8).
- **Checkpoint `169925f`**: RS-2 stranded **6/20** rounds (red3, 13:0x) and **4/20** rounds (red_final, 13:51) — every stranded round strands ALL 5 of the session's agents (the audit measured 2/20, 8/20, 11/20). RS-5: raw `TxnDomainRejectionError` in every round (7 of 8 identical registry calls per round).
- ⚠ The reference's MIGRATE code (`governed.py` / `principals.py`, the am-30 model) was edited DURING runs 9–20; the register path (`server.py`, `agents.py`, `keeps.py`) was byte-stable for all 20 (last edited before run 1) — the three pins exercise only the register path.
- ⚠ Bound: the RS-2 RED on the checkpoint is probabilistic per invocation (~5/20 stranded rounds measured); the DETERMINISTIC twin is the sequential leg (§2 row 2), RED every time.

## §8 SAT — the contract is satisfiable by a known-correct build
Reference = `./scripts/scratch_copy.sh` copy of the main tree (untracked 58-r2/64b tests included), production patched per §A.3 (`reference_fix.patch`, md5 `0abdf6d85342aec8af41572a2d4d0ba9`), `loremaster.__file__` = `…/scratchpad/ref/loremaster/loremaster/__init__.py`.
- Targeted (lane-clear): the four changed files + a19, agent governance, agent registry, 63b-ii-a message enforcement / migrate / send-scope, `test_comms_tool.py` → **1572 passed, 0 failed**.
- ruff: `All checks passed!` (reference production + tests). typecheck (reference): my files clean; red only on 58's registered contract files.
- **Full suite, ONE tree, both ways** (`-n 12`, 15 GB watchdog, 2026-09-26): the reference copy vs a `base` copy cut FROM the reference (`scratch_copy.sh`, so the tests and the untracked 58-r2 / 64b files are byte-identical) with the five production files restored to HEAD (`git checkout --` inside the copy; `cmp` == main tree).
  - **base (HEAD production):** `252 failed, 11757 passed, 63 skipped, 3 xfailed` (17m55s)
  - **reference:** `207 failed, 11802 passed, 63 skipped, 3 xfailed` (23m18s)
  - `comm` of the sorted FAILED ids: **red on the reference only: 0** · **red at base, green on the reference: 45** (a28 41 · a19a 2 · a19b 2 — exactly §5's RED set) · **red in both: 207**, adjudicated individually by file:
    | file | reds | owner |
    |---|---|---|
    | `test_supersede_reanchor_58.py` 44 · `test_task_guarded_shell_58.py` 15 · `test_reanchor_58_r2_probes.py` 13 · `test_task_claimable_partition_58.py` 5 · `test_reanchor_58_r2_am2.py` 3 · `test_reanchor_58_r2_scale.py` 2 · `scripts/test_forgery_door_sweep.py` 2 · `test_task_read_surface.py` 1 · `test_blocks_edge.py` 1 | 86 | packet 58's contract (r1 committed `5a43aeb` + r2 untracked) — `packet-58-contract` bound |
    | `test_governed_substrate_64b.py` 26 · `test_findings_migrate_64b.py` 26 · `test_findings_governance_64b.py` 24 · `test_findings_identity_64b.py` 22 · `test_findings_schema_64b.py` 17 · `test_findings_enforcement_64b.py` 4 | 119 | packet 64b-i's contract (untracked) — `packet-64b-i-contract` bound |
    | `test_ast_reach_helpers.py::…test_no_unallowlisted_whole_tree_parser_clone_survives` | 1 | 64b's untracked `test_findings_identity_64b.py::_routing_markers` / `test_governed_substrate_64b.py::_resource_construction_sites` (message read, §A run 2026-09-26) — not 63c |
    | `test_secret_typing.py::…test_every_unwrap_site_has_an_evidence_backed_entry` | 1 | `scripts/restore_prod_dump.py::build_auth_headers` — the known restore-seam class (audit F-6; the lead's fixer) — not 63c |
  - **63c-attributable reds on the reference: 0.**
- After the full runs, two TEST-ONLY strengthenings landed (pin (2)'s ⊇ leg, §6 M19; a19b door-#2's per-clause re-key, §3 U8). Both files re-run: reference — a28 `47 passed`, a19b `32 passed`; checkpoint (main tree) — the three pin (2) cases `3 failed` (already in §5's 45), a19b `2 failed, 30 passed` (KP2/KP3 only — the door-#2 build attributes correctly, so its re-key adds no RED at `169925f`). The §5 RED set is unchanged at 45.
- `loremaster.__file__` receipts: reference `…/scratchpad/ref/loremaster/loremaster/__init__.py`; base `…/scratchpad/base/loremaster/loremaster/__init__.py`.

## §9 Currency
Bound `packet-63c-i-a-a28-contract` (§A.7) owns `test_fixwave_a28_63c_i_a.py`, `test_fixwave_a19a_63c_i_a.py`, `test_fixwave_a19b_63c_i_a.py` via the runtime-inert `TYPE_CHECKING` references to `loremaster.governed.MigratePreconditionCounts` + `MigrateGovernedResult.preconditions` (mypy at HEAD: exactly two `attr-defined` lines per file, both symbol-named). `test_message_enforcement_63b_ii_a.py` has NO RED at the checkpoint (the golden's RED lands in a19a) and is NOT registered. `--verify-registry`: parses; `MigrateGovernedResult.preconditions` ×3 UNCHECKED (owner not importable — the same shape as `TaskLedger.*`). `--currency` receipt (lore-scoped lane, main tree at `a124c5a` + the fleet's uncommitted work, `-n 12`, 2026-09-26 ~15:20, EXIT=1):
```
  typecheck    RED_ADJUDICATED — 44 residual(s), owned by: packet-58-contract (…) · packet-64b-i-contract (…) · packet-63c-i-a-a28-contract (owner: packet 63c-i-a fix pass (amendments 26-30) — the a28 fix builder; trigger: the fix build lands loremaster.governed.MigratePreconditionCounts and MigrateGovernedResult.preconditions — …)
  ruff         GREEN
  pytest       RED_ORPHANED — 6 residual(s) with NO owner
      ORPHAN: loremaster/tests/test_reanchor_58_r2_cas_runtime.py :: …TestTheDrivenSetIsTheDerivedSet::test_every_derived_CAS_verb_has_a_driver_and_every_driver_a_derived_verb
      ORPHAN: loremaster/tests/test_reanchor_58_r2_cas_runtime.py :: …test_the_typed_error_propagates_unread_and_a_real_loss_is_the_ruled_verdict[tasks.py::_reanchor_stragglers | claim_task | supersede_task | transition]  (4)
      ORPHAN: loremaster/tests/test_reanchor_58_r2_cas_runtime.py :: …TestTheRuntimeSetAndTheStaticIndexAgree::test_every_statically_listed_handler_is_runtime_driven_and_every_driven_verb_is_indexed
CURRENCY   : FAIL — RED with nobody's name on it: pytest
```
**a28-attributable RED_ORPHANED: 0** — every a28 pytest RED (a28 41 · a19a 2 · a19b 2) partitioned as EXPECTED under `packet-63c-i-a-a28-contract`. The 6 orphans are ALL in `test_reanchor_58_r2_cas_runtime.py` — contract-58-r2's UNTRACKED, in-flight file (packet 58 amendment 5, `67bf2cc`), not yet in `packet-58-contract`'s file list; flagged to the lead, not mine to register. The committed registry is HEAD's + my bound ONLY (`--verify-registry --registry <HEAD+a28>` parses; the peer's uncommitted hunks in the same file are NOT staged).

## §10 BUILDER CONSTRAINTS (every name / placement / order the pins require)
Carried (still binding): a19b §10 items 1, 4 (KP4 / KP14), 5, 6 (as amended below), 8, 9; a19a's `preflight` signature; `_agent_migration_preconditions` is THE shared function (rebound by name); `_REFUSAL_ID_SAMPLE_SIZE` is THE bound. a19b §10 items 2, 3 and 7 (created-only compensation, created-from-the-mint's-return, door #4b) are **RETIRED** with the mechanism.
1. **`AppContext._comms_register` ORDER (am-28 §F-2):** resolve principal → (principal present) **`self._keep_store.get_by_key(f"session:{session}")` FIRST** (the read-only gate: keep exists ∧ caller not householded → `governed.GovernedDenied` with the unchanged SF-63-1 text, byte-identical for every name) → `self.agent_registry.preflight(...)` → `self._keep_store.get_or_create_keyed(...)` (the mint, called BY NAME on the wired store) → the post-mint visibility re-check (KEPT) → `self.agent_registry.register(...)`. The gate performs NO registry read (`_select_row` / `preflight` / `register`) and NO mint for a foreign principal.
2. **No compensation:** the `except _AgentRegistryError` delete branch is DELETED; nothing on the register path calls `KeepStore.delete_keep`; the registry's refusal propagates unchanged. `keeps.minted_by_this_call` / `_MINTED_BY_THIS_CALL` and the flag set in `get_or_create_keyed` are dead — delete them (am-28 §F-1). The docstring's ORDER paragraph names BOTH properties (no store side effect on a preflight refusal; no agent fact past the gate) and BOTH residuals (the tokenless-winner race → β at i-b; a keep minted by another principal between the gate and the mint).
3. **RS-5 (am-29):** in `AgentRegistry.register`, the first-register CREATE catches the store's rejection **by class** (the reference catches `TxnDomainRejectionError` and requires the re-read row to EXIST before re-entering; never message text), re-reads, and takes the EXISTING re-register path (the reference re-enters `self.register(...)` with the same arguments, so `preflight` decides a differing role/`spawned_by`). No handler-level retry. ⚠ **Named decision point (am-29):** if the unique-id conflict is not ONE classified branch, STOP and route to i-b; the two RS-5 pins then stay owned-red.
4. **Migrate verb (am-28 A2):** `INFO FOR DB` answering a non-dict or a dict without `tables` → raise a `SurrealStoreError` (or subclass) whose text contains `INFO FOR DB` and the received type's `__name__`; `_governed_select` answering a non-list → raise a `SurrealStoreError` naming the received type. Both byte-inert. The precondition row reads stay `SELECT id, …` statements through `principals.run_query` (the forgery keys on that).
5. **FORK-1:** every leg's `backfilled` = the rows its UPDATE stamped (`_rows_stamped(<UPDATE result>)`), agent and memory included. The legs stay the functions opening `governed_exempt("migrate-governed", …)` (a19a `_migrate_legs` derives them).
6. **FORK-2 / am-26 / F-8:** the message leg's ORDER guard, dangling senders and both halves are ONE refusal, in that order; each clause's count immediately precedes its noun (`N un-migrated …`, `N legacy message(s) name a dangling sender`, `N message row(s) carry an owner but no scope`, `N … carry a scope but no owner`); the ORDER-only refusal text is unchanged; the verb-level refusal stays separate and earlier and never carries the message leg's own "…before migrating \`message\`" remedy.
7. **A5:** the message UPDATE is EXACTLY `_MIGRATE_MESSAGE_GOLDEN` (the sender guard appended after CD-1's conjuncts).
8. **am-30:** `class MigratePreconditionCounts(BaseModel)` in **`loremaster.governed`**, `ConfigDict(extra="forbid", frozen=True)`, fields in THIS order: `unscoped_agents, owned_but_unscoped_agents, scoped_but_ownerless_agents, dangling_sender_messages, owned_but_unscoped_messages, scoped_but_ownerless_messages`, each `int | None = None`. `MigrateGovernedResult.preconditions: MigratePreconditionCounts | None = None` (last field). Populated on EVERY valid-table result (refused or proceeding): the agent counts always (measured at the verb), the message counts only for `--table message` (else `None`); `None` for an invalid table. **Constructed through the normal constructor** (never `model_construct`) and **looked up by name at call time** (the pin rebinds the class by identity in every module — a class captured in a closure/default argument is out of the sweep's reach). Every count clause in `reason` renders FROM the model instance (ONE render function taking the model); the verb-level refusal restates `unscoped_agents`. Docstrings of `MigrateGovernedResult`, `principals._refused`, `principals.migrate_governed` must not claim a refusal returns "before any scan".
9. **Cross-packet:** 64b-i's contract adds `principals._migrate_finding_scope` (a `governed_exempt("migrate-governed")` leg). When it lands, a28's FORK-1 pin reds by name ("has no FORK-1 population") — the checked variable working; the 64b builder adds a population to `_LEG_POPULATIONS`.

## §11 DRY ledger (new reusable symbols — all test-local, a28 unless noted)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_outcome` | `lore_search("test helper that awaits a call and returns the exception class name and text or OK")` ×2 | **store error both times (#495)** — fallback: read the audit's `probe_coldaudit.py::_served` | HAND-ROLLED (test-local twin of a scratch probe helper that lives in no importable module) |
| `_spy_delete_keep`, `_count_calls` | `lore_search("monkeypatch spy counting calls to a store method in governed contract tests")` ×2 | **store error (#495)**; read a19a `_spy_the_mint` / `_count_connection_acquires` by hand | HAND-ROLLED — `_spy_the_mint` is mint-specific with a race hook; `_count_connection_acquires` counts `_ensure_connection` only |
| `_rows_changed` | `lore_search("count rows that changed between two SELECT * snapshots byte diff")` | `diff.py::count_snapshots` (unrelated) | HAND-ROLLED (a19b's D2 pin inlines a scope-count delta, not a byte-diff) |
| `_session_keep_ids`, `_live_keep_scopes`, `_agent_scopes`, `_eight_way_register_calls` | — (fixture data / reads) | — | fixture reads, not policy |
| `_clause_count` | — | a19a `_stated_integers` (whole-reason) | EXTENDED in spirit: per-clause attribution F-8 needs (a19a's helper kept for the whole-reason legs) |
| `_forge` | — | a19 `_redirect_the_shared_preconditions` (swaps a handle, not an answer) | HAND-ROLLED (answer-shape forgery; landed-counter per #194) |
| `_counts_model`, `_counts`, `_perturbed_counts_class`, `_count_integers`, `_population_identifiers` | — | `_governed_contract.patch_shared_object_everywhere` | REUSED the identity sweep for the perturbation; the rest are am-30 pin plumbing |
| `_seed_agent_leg/_memory_leg/_message_leg`, `_seed_rs1`, `_seed_fork2`, `_seed_agent_population`, `_seed_fail_open_population` | — | a19/a19a seeders | HAND-ROLLED on REUSED parts (`seed_*` from `_governed_contract`, a19a `_seed_migrated_senders`) |
| a19b `_a28_count` | — | — | field read + fail-by-name |

## §12 Residuals (each with a verdict)
| # | residual | verdict |
|---|---|---|
| R-1 | `_scope_count`'s docstring says "A `count() … GROUP ALL` over an empty set returns no row" — FALSE on 3.2.4 (probed, §A.8: `[{'count': 0}]` for an empty filter AND an empty table); harmless (the code handles both) | stale prose, production (not my writable set) — flag for the builder / a docs-truth pass |
| R-2 | the CLI (`_dispatch_migrate_governed`) catches `SurrealConnectionError`/`ValueError` but not a plain `SurrealStoreError` or `_rows_stamped`'s `TypeError` → A2's raise reaches the operator as a traceback (loud, not clean) | surfaced; not ruled — operator/sidecar |
| R-3 | `_scope_count` itself answers a non-list with `0` — the A2 fail-open class, not named by A2 (which names `INFO FOR DB` and `_governed_select`) | surfaced (same class); not pinned |
| R-4 | FK-a28-3 / FK-a28-4 (§F) | decisions for the sidecar; pins agnostic |
| R-5 | the tokenless-winner race leaves K kept with no scoped agent (am-28 residual) — pinned as the CONTROL (K survives, keeper = P); closes at β (i-b) | named bound |
| R-6 | `ruff` over the whole tests dir flags ONE foreign line: `loremaster/tests/_logging_fixtures.py:286` E501 (the #466 builder's uncommitted edit) | not mine; surfaced |
| R-7 | lore_search store errors (#495) | filed |

## §13 What the NARROW ADVERSARY DELTA should attack (am-28 §Process)
1. **RS-2's reach:** it observes rows of ONE principal in fresh sessions; a build that deletes only when ≥2 principals… (none plausible) — and whether 20 rounds × 8 is enough to red the checkpoint deterministically (measured ~20–30%/round; the sequential leg is the deterministic twin).
2. **A guarded-delete variant** that keys on `member_of`/household instead of scoped rows (M02b keys on scoped agents) — does the tokenless control red it?
3. **A gate that reads the registry through a door the spy does not wrap** (e.g. `resolve_holder`, `get_agent`, a raw `_query`): RS-3 counts `_select_row`/`preflight`/`register` + the mint only.
4. **A gate that mints a DIFFERENT key first** or mints then deletes (M05 covers `get_or_create_keyed` on the same key).
5. **Byte-identity under timing:** a denial whose text embeds a per-call value (no current build does).
6. **RS-5:** a build that retries in the HANDLER (the registry still leaks at registry level → RS-5 registry pin reds) — confirm; and one that catches ALL `TxnDomainRejectionError` without the existence re-read (would swallow a genuine rejection — no pin constructs a non-conflict rejection on CREATE).
7. **am-30 pin (1)'s reach:** a build that captures `MigratePreconditionCounts` in a default argument / closure is outside the identity sweep (the helper's stated bound) — would red as "never landed" (loud), not pass.
8. **FK-a28-3 / FK-a28-4** fixtures (a foreign-owned P_agent; a `--table message` verb refusal).
9. **The proxy ownership** (FK-a28-2): a19a/a19b are owned via the am-30 pair — a build landing ONLY the model would discharge the bound while the race pins stay red (they would then read RED_ORPHANED at currency — loud, not silent).

## §A Instruments (verbatim — the scratch trees are disposable by design)

### §A.1 `lane_clear.sh` (the audit's §A.4 waiter, re-used; `lane_clear_n.sh` = the same with the consecutive-clear count as `$2`) — md5 `8605a4e68445c17db19bf8a434943c1d`
```bash
#!/usr/bin/env bash
# Lore-scoped lane waiter (coldaudit-63c-i-a-2 §A.4, re-used): clear when no uv/python/pytest EXECUTABLE with a lore
# cwd/argv running a pytest session exists (2 checks 10 s apart). Keyed on comm, never on a wrapper's text (#228).
end=$(( $(date +%s) + ${1:-3600} )); clear=0
while [ "$(date +%s)" -lt "$end" ]; do
  n=0
  for p in $(ps -eo pid=,comm= | awk '$2 ~ /^(uv|python.*|pytest)$/{print $1}'); do
    c=$(readlink /proc/$p/cwd 2>/dev/null); a=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
    case "$c $a" in *PycharmProjects/lore*|*PycharmProjects-lore*) case "$a" in *pytest*) n=$((n+1));; esac;; esac
  done
  if [ $n -eq 0 ]; then clear=$((clear+1)); else clear=0; fi
  [ $clear -ge 2 ] && { echo "LORE-LANE-CLEAR $(date +%T)"; exit 0; }
  sleep 10
done; echo "LORE-LANE-TIMEOUT $(date +%T)"; exit 1
```

### §A.2a `guarded.sh` (15 GB-available PID watchdog) — md5 `2611e7e0d393b7cc65255a364c179b0d`
```bash
#!/usr/bin/env bash
# guarded.sh <dir> <logfile> -- <command...>: run in <dir> with a 15 GB-available PID watchdog (8 s poll).
DIR=$1; LOG=$2; shift 2; [ "$1" = "--" ] && shift
cd "$DIR" || exit 99
"$@" > "$LOG" 2>&1 &
PID=$!
( while kill -0 $PID 2>/dev/null; do A=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ "$A" -lt 15 ]; then echo "WATCHDOG KILL avail=${A}G" >> "$LOG"; pkill -TERM -P $PID; kill -TERM $PID; fi; sleep 8; done ) &
wait $PID; echo "EXIT=$?" >> "$LOG"
```

### §A.2b `conc20.sh` (the 20-consecutive concurrency driver) — md5 `efb3f539bfc3d0aa51fea453ab2079ab`
```bash
#!/usr/bin/env bash
# conc20.sh <tree> <tag> <n>: <n> consecutive invocations of the a28 concurrency pins (RS-2 + both RS-5), serial.
SP=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e8143e2c-9066-4565-b312-8d8862ec462c/scratchpad
TREE=$1; TAG=$2; N=${3:-20}
$SP/lane_clear.sh 3600 || exit 1
for i in $(seq 1 $N); do
  $SP/guarded.sh $TREE $SP/$TAG-$i.log -- uv run pytest -p no:xdist -q -p no:cacheprovider --tb=line \
    loremaster/tests/test_fixwave_a28_63c_i_a.py -k "RS2 or RS5"
  echo "run $i: $(awk '/passed|failed/' $SP/$TAG-$i.log | tail -1)" >> $SP/$TAG.summary
done
echo DONE >> $SP/$TAG.summary
```

### §A.3 `reference_fix.patch` — the reference build: the five production files vs HEAD, the tree every SAT / mutation / concurrency receipt ran on (re-cut after the last run: byte-identical) ⚠ `principals.py` carries a `ruff format` pass (D-4) — md5 `0abdf6d85342aec8af41572a2d4d0ba9`
```diff
diff --git a/loremaster/loremaster/agents.py b/loremaster/loremaster/agents.py
index ec100c2..6e261f7 100644
--- a/loremaster/loremaster/agents.py
+++ b/loremaster/loremaster/agents.py
@@ -93,6 +93,7 @@ from loremaster.store._txn import (
     SurrealConnectionError,
     SurrealStoreError,
     TxnContentionExhaustedError,
+    TxnDomainRejectionError,
     _SurrealConnection,
     bootstrap_session,
     execute_transaction,
@@ -941,11 +942,22 @@ class AgentRegistry:
                 # so a never-changed agent still has an honest declaration instant.
                 _COL_STATUS_SET_AT: self._status_set_at_for(STATUS_ACTIVE, None, None, now),
             }
-            await self._query(
-                f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
-                f"CONTENT ${_ROW_CONTENT_PARAM}",
-                {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
-            )
+            try:
+                await self._query(
+                    f"CREATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) "
+                    f"CONTENT ${_ROW_CONTENT_PARAM}",
+                    {_ROW_ID_PARAM: agent_id, _ROW_CONTENT_PARAM: content},
+                )
+            except TxnDomainRejectionError:
+                # amendment 29 RS-5: a concurrent identical first register won the CREATE — re-read and
+                # take THE re-register path (preflight decides a differing role/spawned_by).
+                if await self._select_row(agent_id) is None:
+                    raise
+                return await self.register(
+                    name, session=session, role=role, model=model, spawned_by=spawned_by,
+                    task_id=task_id, cadence=cadence, owner_principal_id=owner_principal_id,
+                    session_keep_id=session_keep_id,
+                )
             created = await self._select_row(agent_id)
             if created is None:
                 raise AgentRegistryError(
diff --git a/loremaster/loremaster/governed.py b/loremaster/loremaster/governed.py
index dd7730e..6adcfc1 100644
--- a/loremaster/loremaster/governed.py
+++ b/loremaster/loremaster/governed.py
@@ -24,6 +24,8 @@ from dataclasses import dataclass
 from pathlib import Path
 from typing import TYPE_CHECKING, Any
 
+from pydantic import BaseModel, ConfigDict
+
 from loremaster.store._txn import (
     TxnFragment,
     TxnGovernedConflictError,
@@ -91,6 +93,22 @@ class GuardedWriteResult:
     audited: bool
 
 
+class MigratePreconditionCounts(BaseModel):
+    """The governed-migration precondition counts a run MEASURED (packet 63c-i-a, amendment 30). ``None`` =
+    not
+    measured on this run; a number = measured. The refusal ``reason`` restates them, derived from THESE
+    fields."""
+
+    model_config = ConfigDict(extra="forbid", frozen=True)
+
+    unscoped_agents: int | None = None
+    owned_but_unscoped_agents: int | None = None
+    scoped_but_ownerless_agents: int | None = None
+    dangling_sender_messages: int | None = None
+    owned_but_unscoped_messages: int | None = None
+    scoped_but_ownerless_messages: int | None = None
+
+
 @dataclass(frozen=True)
 class MigrateGovernedResult:
     """Receipts of a ``lore-adm migrate-governed`` run over ONE table (design §1.2 item 5 /
@@ -101,8 +119,9 @@ class MigrateGovernedResult:
     the receipt. The read-only PREVIEW is the separate ``report-unmigrated`` verb.
 
     ``scanned`` / ``already_migrated`` are ``None`` on EVERY refusal (packet 63c-i-a, amendment 22
-    §4 / amendment 24 FK-a): a refusal returns before any scan of the target table, so those counts
-    were NOT MEASURED — a ``0`` there would be a served count describing no set. ``backfilled`` stays
+    §4 / amendment 24 FK-a / amendment 28 A4): a refusal serves ``None`` for any count it did not
+    measure and states, in ``reason``, the counts its precondition DID read — so those two — a ``0`` there
+    would be a served count describing no set. ``backfilled`` stays
     an ``int``: a refusal stamped nothing, which IS measured (``0``). On a proceeding run
     ``backfilled`` is the number of rows the backfill actually stamped."""
 
@@ -112,6 +131,7 @@ class MigrateGovernedResult:
     already_migrated: int | None
     refused: bool
     reason: str | None = None
+    preconditions: MigratePreconditionCounts | None = None
 
 
 @dataclass(frozen=True)
diff --git a/loremaster/loremaster/keeps.py b/loremaster/loremaster/keeps.py
index a2ef4d0..49b721f 100644
--- a/loremaster/loremaster/keeps.py
+++ b/loremaster/loremaster/keeps.py
@@ -109,28 +109,6 @@ logger = logging.getLogger(__name__)
 _KEEP_READ_PROJECTION = "id, keeper, type, name, created_at"
 _MEMBER_OF_READ_PROJECTION = "in, out, rank, since"
 
-#: The non-field attribute :meth:`KeepStore.get_or_create_keyed` sets on the keep it returns when THAT
-#: call's own CREATE won (packet 63c-i-a, #485 / amendment 22 §1.2 + amendment 24 FK-b). Read ONLY through
-#: :func:`minted_by_this_call`.
-_MINTED_BY_THIS_CALL = "minted_by_this_call"
-
-
-def minted_by_this_call(keep: object) -> bool:
-    """Whether ``keep`` was CREATED by the :meth:`KeepStore.get_or_create_keyed` call that returned it.
-
-    ``True`` only when that call's own CREATE won the mint; a keep the call merely FOUND (read by key, or
-    re-read as a concurrent winner after a UNIQUE conflict) reads ``False``. Derived from the mint's OWN
-    return — never a pre-read, which a concurrent winner makes a TOCTOU (amendment 24 FK-b). The register
-    handler's created-only compensation reads this: it may delete a keep its call created, never one it
-    found (that keep belongs to another registration).
-
-    The flag rides the returned :class:`Keep` as a non-field ``__dict__`` attribute (``Keep`` is frozen).
-    Measured on the installed pydantic 2.13.4 (2026-09-26): ``==``, ``model_dump`` and ``model_dump_json``
-    ignore it, so no caller comparing or serialising keeps observes it; ``model_copy`` carries it.
-    """
-    return getattr(keep, _MINTED_BY_THIS_CALL, False) is True
-
-
 class Keep(BaseModel):
     """A single collaboration space in the durable ``keep`` store.
 
@@ -560,9 +538,7 @@ class KeepStore:
             name: An optional human label.
 
         Returns:
-            The existing or freshly-minted :class:`Keep` bearing ``key``. :func:`minted_by_this_call`
-            reads ``True`` on it iff THIS call's CREATE won (never for a keep read by key or re-read as
-            a concurrent winner).
+            The existing or freshly-minted :class:`Keep` bearing ``key``.
 
         Raises:
             KeepStoreError: No principal carries ``keeper_email``, OR the store rejected the create.
@@ -632,9 +608,6 @@ class KeepStore:
             created = await self.get_keep(keep_id)
             if created is None:  # pragma: no cover - a just-committed row must read back
                 raise KeepStoreError(f"created keyed keep {keep_id!r} did not read back")
-            # THIS call's CREATE won the mint — reported on the returned object, read through
-            # :func:`minted_by_this_call` (the register handler's created-only compensation, #485).
-            object.__setattr__(created, _MINTED_BY_THIS_CALL, True)
             return created
 
     async def get_by_key(self, key: str) -> Keep | None:
diff --git a/loremaster/loremaster/principals.py b/loremaster/loremaster/principals.py
index 575b68d..ed30234 100644
--- a/loremaster/loremaster/principals.py
+++ b/loremaster/loremaster/principals.py
@@ -81,6 +81,7 @@ from __future__ import annotations
 
 import argparse
 import asyncio
+import dataclasses
 import logging
 import secrets
 import sys
@@ -145,9 +146,7 @@ if TYPE_CHECKING:
     # (``from __future__`` string) annotation, so ``PrincipalKeyStore`` need not be
     # imported at runtime — its module imports THIS one (``Principal``), and a runtime
     # import here would be a cycle.
-    _VerbHandler = Callable[
-        [argparse.Namespace, "PrincipalStore", "PrincipalKeyStore"], Awaitable[int]
-    ]
+    _VerbHandler = Callable[[argparse.Namespace, "PrincipalStore", "PrincipalKeyStore"], Awaitable[int]]
 
     # The keep-verb handler signature (dict-dispatched by :func:`_dispatch_keep`). Keep
     # verbs route through a :class:`~loremaster.keeps.KeepStore` — which COMPOSES its own
@@ -512,8 +511,7 @@ class PrincipalStore:
         # masquerade as a UNIQUE collision). Finding #400: routed through the ONE seam.
         with wrap_store_rejection(
             PrincipalStoreError,
-            f"could not create principal {email!r}: a principal with that email "
-            f"or subject already exists",
+            f"could not create principal {email!r}: a principal with that email or subject already exists",
         ):
             result = await self._query(
                 f"CREATE {PRINCIPAL_TABLE} CONTENT $content RETURN AFTER",
@@ -521,9 +519,7 @@ class PrincipalStore:
             )
         rows = self._as_rows(result)
         if not rows:
-            raise PrincipalStoreError(
-                f"principal {email!r} vanished immediately after it was created"
-            )
+            raise PrincipalStoreError(f"principal {email!r} vanished immediately after it was created")
         return self._row_to_principal(rows[0])
 
     async def get_by_subject(self, subject: str) -> Principal | None:
@@ -563,9 +559,7 @@ class PrincipalStore:
         filters client-side.
         """
         rows = self._as_rows(
-            await self._query(
-                f"SELECT {_READ_PROJECTION} FROM {PRINCIPAL_TABLE} ORDER BY {_COL_CREATED_AT}"
-            )
+            await self._query(f"SELECT {_READ_PROJECTION} FROM {PRINCIPAL_TABLE} ORDER BY {_COL_CREATED_AT}")
         )
         return [self._row_to_principal(row) for row in rows]
 
@@ -593,12 +587,9 @@ class PrincipalStore:
             PrincipalNotFoundError: No principal carries ``email``.
         """
         if status not in _PRINCIPAL_STATUSES:
-            raise ValueError(
-                f"principal status must be one of {list(_PRINCIPAL_STATUSES)}, got {status!r}"
-            )
+            raise ValueError(f"principal status must be one of {list(_PRINCIPAL_STATUSES)}, got {status!r}")
         result = await self._query(
-            f"UPDATE {PRINCIPAL_TABLE} SET {_COL_STATUS} = $status "
-            f"WHERE {_COL_EMAIL} = $email RETURN AFTER",
+            f"UPDATE {PRINCIPAL_TABLE} SET {_COL_STATUS} = $status WHERE {_COL_EMAIL} = $email RETURN AFTER",
             {"status": status, "email": email},
         )
         rows = self._as_rows(result)
@@ -984,11 +975,7 @@ def _render_principal_line(principal: Principal) -> str:
     hostile value cannot forge a phantom row: a survived newline collapses to a space).
     ``status`` / ``role`` are closed-domain (DDL-validated) and rendered directly;
     ``expires_at`` is an engine-typed datetime."""
-    display_name = (
-        safe_str(principal.display_name)
-        if principal.display_name is not None
-        else _ABSENT_FIELD
-    )
+    display_name = safe_str(principal.display_name) if principal.display_name is not None else _ABSENT_FIELD
     return "  ".join(
         [
             safe_str(principal.email),
@@ -1105,16 +1092,35 @@ async def migrate_governed(
     if table not in _MIGRATE_VALID_TABLES:
         return _not_supported(table, store_was_read=False)
     preconditions = await _agent_migration_preconditions(store, table=table)
-    refusal = await _verb_level_refusal(preconditions, principal_store)
+    counts = _measured_counts(preconditions, table)
+    refusal = await _verb_level_refusal(preconditions, counts, principal_store)
     if refusal is not None:
-        return _refused(table, refusal)
-    if table == MEMORY_TABLE:
-        return await _migrate_memory_scope(store, keep_store, principal_store)
-    if table == AGENT_TABLE:
-        return await _migrate_agent_owner(store, keep_store, principal_store)
-    if table == MESSAGE_TABLE:
-        return await _migrate_message_owner(store, keep_store, principal_store, preconditions)
-    return _not_supported(table, store_was_read=True)
+        result = _refused(table, refusal)
+    elif table == MEMORY_TABLE:
+        result = await _migrate_memory_scope(store, keep_store, principal_store)
+    elif table == AGENT_TABLE:
+        result = await _migrate_agent_owner(store, keep_store, principal_store)
+    elif table == MESSAGE_TABLE:
+        result = await _migrate_message_owner(store, keep_store, principal_store, preconditions, counts)
+    else:
+        result = _not_supported(table, store_was_read=True)
+    return dataclasses.replace(result, preconditions=counts)
+
+
+def _measured_counts(preconditions: AgentMigrationPreconditions, table: str) -> Any:
+    """THE measured counts (amendment 30): the agent reads ran at the verb for every valid table; the message
+    reads only for ``--table message`` (``None`` = not measured)."""
+    from loremaster.governed import MigratePreconditionCounts
+
+    message = table == MESSAGE_TABLE
+    return MigratePreconditionCounts(
+        unscoped_agents=preconditions.unscoped_count,
+        owned_but_unscoped_agents=len(preconditions.owned_unscoped),
+        scoped_but_ownerless_agents=len(preconditions.ownerless_scoped),
+        dangling_sender_messages=len(preconditions.dangling_senders) if message else None,
+        owned_but_unscoped_messages=len(preconditions.messages_owned_unscoped) if message else None,
+        scoped_but_ownerless_messages=len(preconditions.messages_scoped_ownerless) if message else None,
+    )
 
 
 #: The ruled VALID ``--table`` set (amendment 22 F-1 / amendment 23 FK-3): the governed tables amendment
@@ -1124,8 +1130,9 @@ _MIGRATE_VALID_TABLES = (AGENT_TABLE, MEMORY_TABLE, MESSAGE_TABLE, BRIEF_TABLE)
 
 
 def _refused(table: str, reason: str) -> MigrateGovernedResult:
-    """A refusal receipt. ``scanned`` / ``already_migrated`` are ``None`` — every refusal returns before
-    any scan of the target table, so those counts were NOT MEASURED (amendment 22 §4 / amendment 24
+    """A refusal receipt. ``scanned`` / ``already_migrated`` are ``None`` — a refusal serves ``None`` for any
+    count it did not measure, and states in ``reason`` the counts its precondition DID read (amendment 22 §4 /
+    amendment 24
     FK-a: a ``0`` would be a served count describing no set); ``backfilled`` is the measured ``0``.
 
     A ``refused=True`` result writes NOTHING: every refusal returns before any keep mint or stamp. (A leg
@@ -1247,7 +1254,7 @@ async def _migrate_memory_scope(
     # golden the F5 classifier's leg 2 matches) AND the executed statement.
     backfill_statement = f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"
     with governed_exempt("migrate-governed", statement=backfill_statement):
-        await run_query(
+        stamped = await run_query(
             acquire=store.acquire,
             drop=store.drop,
             url=store.url,
@@ -1260,7 +1267,7 @@ async def _migrate_memory_scope(
     return MigrateGovernedResult(
         table=MEMORY_TABLE,
         scanned=unmigrated + already,
-        backfilled=unmigrated,
+        backfilled=_rows_stamped(stamped),
         already_migrated=already,
         refused=False,
     )
@@ -1278,9 +1285,7 @@ async def _scope_count(store: StoreHandle, table: str, *, none: bool) -> int:
         url=store.url,
         noun="governed scope count",
         label="governed.scope_count.rejected",
-        statement=(
-            f"SELECT count() FROM {table} WHERE scope IS {'NONE' if none else 'NOT NONE'} GROUP ALL"
-        ),
+        statement=(f"SELECT count() FROM {table} WHERE scope IS {'NONE' if none else 'NOT NONE'} GROUP ALL"),
         params={},
         logger=logger,
     )
@@ -1343,7 +1348,11 @@ async def _governed_select(store: StoreHandle, *, noun: str, label: str, stateme
         params={},
         logger=logger,
     )
-    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
+    if not isinstance(rows, list):
+        raise SurrealStoreError(
+            f"the {noun} read answered a {type(rows).__name__}, not a list of rows — nothing was migrated"
+        )
+    return [row for row in rows if isinstance(row, dict)]
 
 
 def _by_id(values: list[Any]) -> tuple[Any, ...]:
@@ -1386,7 +1395,12 @@ async def _agent_migration_preconditions(
         params={},
         logger=logger,
     )
-    defined = info.get("tables", {}) if isinstance(info, dict) else {}
+    if not isinstance(info, dict) or "tables" not in info:
+        raise SurrealStoreError(
+            f"INFO FOR DB answered a {type(info).__name__} without a `tables` map — the governed-migration "
+            "preconditions cannot be read, so nothing was migrated"
+        )
+    defined = info["tables"]
     unscoped_count = 0
     owned_unscoped: list[tuple[Any, Any]] = []
     ownerless_scoped: list[Any] = []
@@ -1455,12 +1469,13 @@ def _id_sample(ids: tuple[Any, ...] | list[Any]) -> str:
     return f"First {len(shown)} of {len(ids)} ids shown: {', '.join(shown)}."
 
 
-def _owned_unscoped_part(owned_unscoped: tuple[tuple[Any, Any], ...], operator: Principal | None) -> str:
+def _owned_unscoped_part(
+    owned_unscoped: tuple[tuple[Any, Any], ...], operator: Principal | None, count: int
+) -> str:
     """The §2.1 owned-but-unscoped part, with the DERIVED diagnosis (amendment 19 D-3 F-1 / amendment 20
     §8.4): who owns the rows — the operator (the E3 population), named other principals (bounded by the
     same constant — amendment 20 §8.2), or, when the operator is unresolvable, NOBODY classified (any of
     them may BE the operator)."""
-    count = len(owned_unscoped)
     head = f"{count} agent row(s) carry an owner but no scope (§2.1)"
     sample = _id_sample([row_id for row_id, _owner in owned_unscoped])
     if operator is None:
@@ -1490,7 +1505,7 @@ def _owned_unscoped_part(owned_unscoped: tuple[tuple[Any, Any], ...], operator:
 
 
 async def _verb_level_refusal(
-    preconditions: AgentMigrationPreconditions, principal_store: PrincipalStore
+    preconditions: AgentMigrationPreconditions, counts: Any, principal_store: PrincipalStore
 ) -> str | None:
     """The verb-level store refusal (amendment 19 D-1 / 20 §8.4 / 22 F-2 / 24 door #1), or ``None``.
 
@@ -1507,26 +1522,39 @@ async def _verb_level_refusal(
             parts.append(
                 await _operator_unresolved(principal_store, purpose="to classify the rows below") + "."
             )
-        parts.append(_owned_unscoped_part(preconditions.owned_unscoped, operator))
+        parts.append(
+            _owned_unscoped_part(preconditions.owned_unscoped, operator, counts.owned_but_unscoped_agents)
+        )
     if preconditions.ownerless_scoped:
-        count = len(preconditions.ownerless_scoped)
+        count = counts.scoped_but_ownerless_agents
         parts.append(
             f"{count} agent row(s) carry a scope but no owner — a half-applied store (one column of the "
             f"governed pair was stamped without the other). {_id_sample(preconditions.ownerless_scoped)}"
         )
     if not parts:
         return None
-    parts.append("Adjudicate these rows by hand before migrating ANY governed table; no row was stamped")
+    parts.append(
+        f"(The store holds {counts.unscoped_agents} agent row(s) with no scope in total.) Adjudicate "
+        "these "
+        "rows by hand before migrating ANY governed table; no row was stamped"
+    )
     return " ".join(parts)
 
 
-def _message_leg_refusal(preconditions: AgentMigrationPreconditions) -> str | None:
+def _message_leg_refusal(preconditions: AgentMigrationPreconditions, counts: Any) -> str | None:
     """The message leg's row-fact refusal (amendments 23 FK-2, 24 §2 door #2, 25, 26), or ``None``: ONE
     refusal naming EVERY problem present, in :func:`_agent_migration_preconditions`' check order —
     dangling senders, then each message half-pair — each with its true count and a bounded sample (THE
     one :data:`_REFUSAL_ID_SAMPLE_SIZE`, per list). Byte-inert: nothing is stamped, the sound rows
     included (one statement, one verdict). ORDER-class, not store-class: it refuses ``message`` only."""
     parts: list[str] = []
+    if preconditions.unscoped_count > 0:
+        parts.append(
+            f"cannot migrate `message` rows before the `agent` table is migrated "
+            f"({counts.unscoped_agents} un-migrated (NONE-scope) agent(s) remain) — a message's "
+            "owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 "
+            "agent-first ORDER); run migrate-governed for `agent` first."
+        )
     if preconditions.dangling_senders:
         dangling = preconditions.dangling_senders
         shown = [
@@ -1534,23 +1562,35 @@ def _message_leg_refusal(preconditions: AgentMigrationPreconditions) -> str | No
             for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]
         ]
         parts.append(
-            f"{len(dangling)} legacy message(s) name a dangling sender — their `sender` link resolves to "
+            f"{counts.dangling_sender_messages} legacy message(s) name a dangling sender — their `sender` "
+            "link "
+            "resolves to "
             f"no agent row, so no owner can be derived from it. First {len(shown)} of {len(dangling)} "
             f"shown: {', '.join(shown)}."
         )
-    for ids, fact in (
-        (preconditions.messages_owned_unscoped, "carry an owner but no scope"),
-        (preconditions.messages_scoped_ownerless, "carry a scope but no owner"),
+    for ids, count, fact in (
+        (
+            preconditions.messages_owned_unscoped,
+            counts.owned_but_unscoped_messages,
+            "carry an owner but no scope",
+        ),
+        (
+            preconditions.messages_scoped_ownerless,
+            counts.scoped_but_ownerless_messages,
+            "carry a scope but no owner",
+        ),
     ):
         if ids:
             parts.append(
-                f"{len(ids)} message row(s) {fact} — a half-applied store (one column of the governed "
+                f"{count} message row(s) {fact} — a half-applied store (one column of the governed "
                 f"pair was stamped without the other). {_id_sample(ids)}"
             )
-    if not parts:
-        return None
-    parts.append("Adjudicate these messages by hand before migrating `message`; no row was stamped")
-    return " ".join(parts)
+    order_parts = parts[:1] if preconditions.unscoped_count > 0 else []
+    row_parts = parts[len(order_parts) :]
+    if not row_parts:
+        return order_parts[0].rstrip(".") if order_parts else None
+    row_parts.append("Adjudicate these messages by hand before migrating `message`; no row was stamped")
+    return " ".join(order_parts + row_parts)
 
 
 def _rows_stamped(update_result: Any) -> int:
@@ -1623,7 +1663,7 @@ async def _migrate_agent_owner(
         "owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE"
     )
     with governed_exempt("migrate-governed", statement=backfill_statement):
-        await run_query(
+        stamped = await run_query(
             acquire=store.acquire,
             drop=store.drop,
             url=store.url,
@@ -1636,7 +1676,7 @@ async def _migrate_agent_owner(
     return MigrateGovernedResult(
         table=AGENT_TABLE,
         scanned=unmigrated + already,
-        backfilled=unmigrated,
+        backfilled=_rows_stamped(stamped),
         already_migrated=already,
         refused=False,
     )
@@ -1647,6 +1687,7 @@ async def _migrate_message_owner(
     keep_store: KeepStore,
     principal_store: PrincipalStore,
     preconditions: AgentMigrationPreconditions,
+    counts: Any,
 ) -> MigrateGovernedResult:
     """Backfill every legacy (NONE-scope, NONE-owner) ``message`` row's owner from its SENDER + scope to
     the project keep (§4.C / §2.6). OWNED-BY-LINK: ``owner_agent = sender``, ``owner_principal =
@@ -1674,15 +1715,7 @@ async def _migrate_message_owner(
 
     from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt
 
-    if preconditions.unscoped_count > 0:
-        return _refused(
-            MESSAGE_TABLE,
-            f"cannot migrate `message` rows before the `agent` table is migrated "
-            f"({preconditions.unscoped_count} un-migrated (NONE-scope) agent(s) remain) — a message's "
-            "owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 "
-            "agent-first ORDER); run migrate-governed for `agent` first",
-        )
-    row_refusal = _message_leg_refusal(preconditions)
+    row_refusal = _message_leg_refusal(preconditions, counts)
     if row_refusal is not None:
         return _refused(MESSAGE_TABLE, row_refusal)
     operator = await resolve_operator_principal(principal_store)
@@ -1710,7 +1743,8 @@ async def _migrate_message_owner(
     backfill_statement = (
         f"UPDATE {MESSAGE_TABLE} SET owner_agent = sender, "
         "owner_principal = sender.owner_principal, scope = $scope "
-        "WHERE scope IS NONE AND owner_principal IS NONE"
+        "WHERE scope IS NONE AND owner_principal IS NONE "
+        "AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE"
     )
     with governed_exempt("migrate-governed", statement=backfill_statement):
         stamped = await run_query(
@@ -1748,16 +1782,12 @@ def build_parser() -> argparse.ArgumentParser:
             "Every verb executes directly; only `list`/`list-keys` are reads."
         ),
     )
-    parser.add_argument(
-        "--config", default=None, help="path to the project lore.yaml (store coordinate)"
-    )
+    parser.add_argument("--config", default=None, help="path to the project lore.yaml (store coordinate)")
     subcommands = parser.add_subparsers(dest="command", required=True)
 
     def _with_email(name: str, help_text: str) -> argparse.ArgumentParser:
         sub = subcommands.add_parser(name, help=help_text)
-        sub.add_argument(
-            "--email", required=True, help="the principal's email (its admission key)"
-        )
+        sub.add_argument("--email", required=True, help="the principal's email (its admission key)")
         return sub
 
     add = _with_email("add", "create a principal")
@@ -1768,9 +1798,7 @@ def build_parser() -> argparse.ArgumentParser:
         default=None,
         help="the authorization role (default: member, least-privilege)",
     )
-    add.add_argument(
-        "--expires", default=None, help="an optional ISO-8601 expiry instant (omitted = never)"
-    )
+    add.add_argument("--expires", default=None, help="an optional ISO-8601 expiry instant (omitted = never)")
 
     subcommands.add_parser("list", help="list every principal")
 
@@ -1810,9 +1838,7 @@ def build_parser() -> argparse.ArgumentParser:
         choices=list(_KEEP_TYPES),
         help="the keep flavour (closed domain, server-validated)",
     )
-    create_keep.add_argument(
-        "--keeper", required=True, help="the keeper (owner) principal's email"
-    )
+    create_keep.add_argument("--keeper", required=True, help="the keeper (owner) principal's email")
     create_keep.add_argument(
         "--name",
         default=None,
@@ -1845,9 +1871,7 @@ def build_parser() -> argparse.ArgumentParser:
         "set-keeper", help="reassign a keep's keeper (owner) to a new principal"
     )
     set_keeper.add_argument("--keep", required=True, help="the keep's id")
-    set_keeper.add_argument(
-        "--new-keeper", required=True, help="the new keeper (owner) principal's email"
-    )
+    set_keeper.add_argument("--new-keeper", required=True, help="the new keeper (owner) principal's email")
 
     delete_keep = subcommands.add_parser(
         "delete-keep", help="delete a keep and cascade its household edges (irreversible)"
@@ -1991,9 +2015,7 @@ async def _cmd_create_keep(args: argparse.Namespace, keep_store: KeepStore) -> i
     if args.type in _KEEP_NAME_REQUIRED_TYPES and args.name is None:
         raise ValueError(f"--name is required for --type {args.type}")
     if args.type in _KEEP_NAME_FORBIDDEN_TYPES and args.name is not None:
-        raise ValueError(
-            f"--name is not valid for --type {args.type} (a dm keep has no name concept)"
-        )
+        raise ValueError(f"--name is not valid for --type {args.type} (a dm keep has no name concept)")
     keep = await keep_store.create_keep(keeper_email=args.keeper, type=args.type, name=args.name)
     print(keep.id)
     return 0
diff --git a/loremaster/loremaster/server.py b/loremaster/loremaster/server.py
index 81d8aaa..dc743dc 100644
--- a/loremaster/loremaster/server.py
+++ b/loremaster/loremaster/server.py
@@ -6725,12 +6725,27 @@ class AppContext:
         # register, never a conditional splat), so the registry stamps ``scope`` from the SAME
         # keep the SF-63-1 gate below checks.
         session_keep_bare: str | None = None
-        # 63c-i-a (#485 / amendment 22 §1): EVERY refusal the registry can raise without a write —
-        # identity, blank role, retired, role / spawned_by conflict — is decided HERE, BEFORE the
-        # session-keep mint below, by THE registry's own ``preflight`` (one decision, no handler copy).
-        # A refused register therefore never makes its caller keeper of a session it never joined
-        # (SF-63-1 would then deny the next principal). The pair check is deferred to ``register``
-        # (``session_keep_id`` omitted: the keep does not exist yet).
+        keep_store = self._keep_store
+        foreign_denial = (
+            f"session {session!r} is kept by another principal — you are not householded in "
+            "it; its keeper must run `lore-adm add-household` for you before you register "
+            "into this session"
+        )
+        from loremaster.visible_keeps import resolve_visible_keeps  # noqa: PLC0415
+
+        if principal is not None:
+            if keep_store is None:  # pragma: no cover - a governed AppContext always wires one
+                raise governed.GovernedDenied(
+                    "no keep store is wired — a governed register cannot mint its session keep"
+                )
+            # amendment 28 §F-2: the READ-ONLY SF-63-1 gate — BEFORE any registry read, so a foreign
+            # principal learns nothing about another principal's agents (63-rulings §6).
+            existing_keep = await keep_store.get_by_key(f"session:{session}")
+            if existing_keep is not None:
+                existing_bare = str(existing_keep.id).split(":", 1)[-1]
+                visible = await resolve_visible_keeps(keep_store, member_email=principal.email)
+                if keep_scope(existing_bare) not in visible:
+                    raise governed.GovernedDenied(foreign_denial)
         await self.agent_registry.preflight(
             agent,
             session=session,
@@ -6738,78 +6753,27 @@ class AppContext:
             spawned_by=spawned_by,
             owner_principal_id=principal_bare,
         )
-        minted_session_keep = False
-        keep_store = self._keep_store
         if principal is not None:
-            if keep_store is None:  # pragma: no cover - a governed AppContext always wires one
-                raise governed.GovernedDenied(
-                    "no keep store is wired — a governed register cannot mint its session keep"
-                )
-            # SF-63-1 — get-or-create the session keep, kept by THIS registrant's principal (the
-            # first registrant with a principal keeps it; the keeper's own later agents join it — the
-            # idempotent CAS on the UNIQUE keep.key, store-ref §1.8).
+            assert keep_store is not None
             session_keep = await keep_store.get_or_create_keyed(
                 key=f"session:{session}", type="session", keeper_email=principal.email, name=session
             )
-            # SF-63-1 foreign gate — a principal NOT householded in the (existing) session keep is
-            # DENIED, naming the SESSION + the add-household remedy but NOT the keeper's identity
-            # (63-rulings §6 existence-leak stance). It runs BEFORE register, so a rejected register
-            # writes NO agent row (#97). The keeper's own agents pass (auto-householded on mint).
-            from loremaster.keeps import minted_by_this_call  # noqa: PLC0415
-            from loremaster.visible_keeps import resolve_visible_keeps  # noqa: PLC0415
-
-            # "created" comes from the mint's OWN return (amendment 24 FK-b) — never a pre-read,
-            # which a concurrent winner would turn into a TOCTOU.
-            minted_session_keep = minted_by_this_call(session_keep)
             session_keep_bare = str(session_keep.id).split(":", 1)[-1]
             visible = await resolve_visible_keeps(keep_store, member_email=principal.email)
             if keep_scope(session_keep_bare) not in visible:
-                raise governed.GovernedDenied(
-                    f"session {session!r} is kept by another principal — you are not householded in "
-                    "it; its keeper must run `lore-adm add-household` for you before you register "
-                    "into this session"
-                )
+                raise governed.GovernedDenied(foreign_denial)
             kept_by_me = session_keep.keeper_id == principal_bare
-        try:
-            result = await self.agent_registry.register(
-                agent,
-                session=session,
-                role=role,
-                model=model,
-                spawned_by=spawned_by,
-                task_id=task_id,
-                cadence=cadence,
-                owner_principal_id=principal_bare,
-                session_keep_id=session_keep_bare,
-            )
-        except _AgentRegistryError as refusal:
-            # The race residual (amendment 22 §1.2): a CONCURRENT conflicting register landed between
-            # ``preflight`` and ``register``, so the registry refused AFTER the mint. Compensate
-            # CREATED-ONLY — delete the session keep iff THIS call's own CREATE minted it, never a keep
-            # it merely found (that one is another registration's session). BOUND: if the delete
-            # itself fails the keep is left behind — served, not hidden (amendment 24 #4b); RE-OPEN
-            # TRIGGER: a keep observed left behind after a refused register.
-            if minted_session_keep and keep_store is not None and session_keep_bare is not None:
-                try:
-                    await keep_store.delete_keep(keep_id=session_keep_bare)
-                except Exception as delete_error:  # noqa: BLE001 - the registry's refusal stays the outcome
-                    # amendment 24 #4b: a FAILED delete leaves the keep behind, denying the next
-                    # principal — so the CALLER learns it, not only the server log. The refusal it asked
-                    # about SURVIVES verbatim (same object, same class, its text first — the delete error
-                    # never replaces it, adversary N8) with exactly ONE appended line naming the
-                    # left-behind keep by its store-minted bare id and its remedy verb (``lore-adm
-                    # delete-keep --keep`` accepts a bare id); the caller's own parameters stay out.
-                    logger.warning(
-                        "comms.register.compensation_failed",
-                        extra={"keep_id": session_keep_bare, "error_class": type(delete_error).__name__},
-                    )
-                    refusal.args = (
-                        f"{refusal}\nALSO: this refused register minted session keep {session_keep_bare} "
-                        "and could not delete it — it is LEFT BEHIND and would deny the next principal's "
-                        "register into this session; remedy: "
-                        f"`lore-adm delete-keep --keep {session_keep_bare}`",
-                    )
-            raise
+        result = await self.agent_registry.register(
+            agent,
+            session=session,
+            role=role,
+            model=model,
+            spawned_by=spawned_by,
+            task_id=task_id,
+            cadence=cadence,
+            owner_principal_id=principal_bare,
+            session_keep_id=session_keep_bare,
+        )
         now = datetime.now(UTC)
         registered_age_s = int((now - result.agent.registered_at).total_seconds())
         brief: Brief | None
```

### §A.4 `drive.sh` (mutation driver) — md5 `945eaaf2ca732250a71458a3b6a1e949`
```bash
#!/usr/bin/env bash
# drive.sh <M...>: run scripts/mutation_proof.py in the reference copy for each named mutation, declared set from
# declared.py (written before any run). One pytest session at a time (the caller holds the lore lane).
SP=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e8143e2c-9066-4565-b312-8d8862ec462c/scratchpad
cd $SP/ref || exit 99
FILES="loremaster/tests/test_fixwave_a28_63c_i_a.py loremaster/tests/test_fixwave_a19a_63c_i_a.py loremaster/tests/test_fixwave_a19b_63c_i_a.py loremaster/tests/test_message_enforcement_63b_ii_a.py"
for M in "$@"; do
  D=$SP/mut/$M
  EXPECT=$(cd $SP/mut && python3 -c "from declared import DECLARED; print(' '.join('--expect-red '+n for n in DECLARED['$M']))")
  K=$(cd $SP/mut && python3 -c "from declared import K_FILTER; print(K_FILTER.get('$M',''))")
  if [ -n "$K" ]; then KARGS=(-k "$K"); else KARGS=(); fi
  md5_before=$(md5sum "$(cat $D/file)" | cut -d' ' -f1)
  uv run python scripts/mutation_proof.py --file "$(cat $D/file)" --anchor-file $D/anchor --replacement-file $D/replacement \
     $EXPECT -- uv run pytest -n 8 -q -p no:cacheprovider --tb=no -rf "${KARGS[@]}" $FILES > $D/result.log 2>&1
  rc=$?
  md5_after=$(md5sum "$(cat $D/file)" | cut -d' ' -f1)
  echo "$M rc=$rc restored=$([ "$md5_before" = "$md5_after" ] && echo yes || echo NO) :: $(tail -3 $D/result.log | tr '\n' ' ' | cut -c1-300)" >> $SP/mut/SUMMARY.txt
done
```

### §A.5 `declared.py` (DECLARED RED sets — timestamps in §6) — md5 `ab3871e5be36fb843f75653ba9757abc`
```python
#: per-mutation -k filter (M01: two concurrent compensations race delete_keep → KeepNotFoundError reaches an RS-5
#: caller nondeterministically — excluded so the diff stays deterministic; RS-5 is graded by M07).
K_FILTER = {"M01_unguarded_delete": "not RS5", "M02_guarded_delete": "not RS5", "M02b_guarded_delete_counts": "not RS5"}
"""DECLARED RED sets for the a28 mutation proofs — written BEFORE any mutation run (ids from --collect-only)."""
A28 = "loremaster/tests/test_fixwave_a28_63c_i_a.py::"
A19A = "loremaster/tests/test_fixwave_a19a_63c_i_a.py::"
A19B = "loremaster/tests/test_fixwave_a19b_63c_i_a.py::"
RACE = A28 + "TestTheRaceNeverStrandsAScope63cIAa28::"
RS5 = A28 + "TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28::"
F2 = A28 + "TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28::"
F1 = A28 + "TestBackfilledIsMeasuredOnEveryLeg63cIAa28::"
ORD = A28 + "TestTheMessageLegServesOneRefusalInCheckOrder63cIAa28::"
A5 = A28 + "TestTheMessageBackfillGuardsTheSender63cIAa28::"
A2 = A28 + "TestAWrongShapedDependencyFailsClosed63cIAa28::"
TYPED = A28 + "TestTheMeasuredCountsAreTypedFields63cIAa28::"
RUNTIME = A19A + "TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property"
KP1 = A19B + "test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated"
SEQ = RACE + "test_the_sequential_race_keeps_the_keep_and_serves_the_teaching"
REFUSAL_CASES = [
    "InvalidAgentIdentityError-blank-empty", "InvalidAgentIdentityError-blank-spaces",
    "InvalidAgentIdentityError-blank-ideographic", "AgentIdentityConflictError-role-conflict",
    "AgentIdentityConflictError-spawned-by-conflict", "RetiredAgentError-retired",
]
DECLARED = {
    "M01_unguarded_delete": [RACE + "test_RS2_eight_way_registers_never_strand_a_scope",
        SEQ + "[handler-winner-found-the-keep]", SEQ + "[tokenless-winner-control]", RUNTIME, KP1],
    "M02_guarded_delete": [SEQ + "[tokenless-winner-control]", RUNTIME],
    "M03_preflight_first_no_readonly_gate": [F2 + "test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads",
        F2 + "test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register"],
    "M04_gate_reads_the_registry": [F2 + "test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads"],
    "M05_gate_mints": [F2 + "test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads",
        F2 + "test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register", RUNTIME,
        *[A19A + "TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[" + c + "]" for c in REFUSAL_CASES],
        A19A + "TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_handler_decides_with_preflight_BEFORE_the_mint"],
    "M06_no_post_mint_recheck": [F2 + "test_the_POST_MINT_recheck_denies_a_keep_minted_meanwhile_by_another_principal"],
    "M07_registry_no_reread": [RS5 + "test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error",
        RS5 + "test_RS5_eight_identical_first_registers_all_succeed_at_the_registry"],
    "M08_agent_backfilled_precount": [F1 + "test_FORK1_backfilled_equals_the_rows_the_run_changed[_migrate_agent_owner]"],
    "M09_order_refusal_alone": [ORD + "test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal"],
    "M10_half_counts_swapped": [ORD + "test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal",
        ORD + "test_am26_RS1_dangling_and_half_pair_are_ONE_refusal_dangling_first"],
    "M11_info_fail_open": [A2 + f"test_A2_an_unexpected_INFO_FOR_DB_shape_raises_byte_inert[{t}-{s}]"
        for t in ("agent", "memory", "message", "brief") for s in ("keyless-dict", "list", "str")],
    "M12_select_fail_open": [A2 + f"test_A2_a_non_list_precondition_row_answer_raises_byte_inert[{t}-{s}]"
        for t in ("agent", "message") for s in ("dict", "str")],
    "M13_verb_count_not_served": [TYPED + "test_am30_pin1_perturbing_a_field_moves_the_reason[unscoped_agents]"],
    "M14_sender_guard_scope_conjunct_dropped": [A5 + "test_A5_an_ownerless_or_dangling_senders_message_is_never_stamped",
        A19A + "TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_the_message_backfill_EXECUTES_the_golden"],
    "M15_sender_guard_owner_conjunct_dropped": [A5 + "test_A5_an_ownerless_or_dangling_senders_message_is_never_stamped",
        A19A + "TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_the_message_backfill_EXECUTES_the_golden"],
    "M16_dangling_after_half_pairs": [ORD + "test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal",
        ORD + "test_am26_RS1_dangling_and_half_pair_are_ONE_refusal_dangling_first"],
    "M17_docstring_claims_no_scan": [TYPED + "test_A4_no_docstring_claims_a_refusal_scans_nothing"],
    "M18_half_clause_from_private_ints": [TYPED + f"test_am30_pin1_perturbing_a_field_moves_the_reason[{f}]"
        for f in ("owned_but_unscoped_messages", "scoped_but_ownerless_messages")],
    "M19_message_counts_never_measured": [TYPED + "test_am30_the_served_fields_are_the_measured_counts[P_message]",
        *[TYPED + f"test_am30_pin1_perturbing_a_field_moves_the_reason[{f}]"
          for f in ("dangling_sender_messages", "owned_but_unscoped_messages", "scoped_but_ownerless_messages")],
        TYPED + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[P_message]",
        TYPED + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[RS-1]",
        A19B + "test_KP2_the_dangling_sender_sample_reads_THE_constant"],
    "M02b_guarded_delete_counts": [SEQ + "[tokenless-winner-control]", RUNTIME],
    "M03b_checkpoint_order_gate_read_removed": [
        F2 + "test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads",
        F2 + "test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register"],
    # M19r: re-run AFTER pin (2) gained its ⊇ leg (M19 exposed the one-directional gap). FORK-2 / RS-1 are added
    # because M19's FIRST run showed them red — declared-after-seeing, SAID SO (report §6); the re-run's point is
    # that pin (2) now fires on P_message and RS-1.
    "M19r_message_counts_never_measured": [TYPED + "test_am30_the_served_fields_are_the_measured_counts[P_message]",
        *[TYPED + f"test_am30_pin1_perturbing_a_field_moves_the_reason[{f}]"
          for f in ("dangling_sender_messages", "owned_but_unscoped_messages", "scoped_but_ownerless_messages")],
        TYPED + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[P_message]",
        TYPED + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[RS-1]",
        A19B + "test_KP2_the_dangling_sender_sample_reads_THE_constant",
        ORD + "test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal",
        ORD + "test_am26_RS1_dangling_and_half_pair_are_ONE_refusal_dangling_first"],
    # M10r: re-run AFTER a19b's door-#2 pin was re-keyed to per-clause attribution (audit F-8) — its
    # both-halves case must now red too.
    "M10r_half_counts_swapped": [ORD + "test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal",
        ORD + "test_am26_RS1_dangling_and_half_pair_are_ONE_refusal_dangling_first",
        *[A19B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[" + h + "]"
          for h in ("both-halves", "owned-unscoped", "scoped-ownerless")]],
}
if __name__ == "__main__":
    import sys
    for node in DECLARED[sys.argv[1]]:
        print(node)
```

### §A.6a every mutation's file / anchor / replacement (dumped from `mut/M*/`) — md5 `448806f9cb71c8d80ff736d5a659fbdc`
```text
==== M01_unguarded_delete :: loremaster/loremaster/server.py
---- ANCHOR
        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )
---- REPLACEMENT
        try:
            result = await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )
        except _AgentRegistryError:
            if keep_store is not None and session_keep_bare is not None:
                await keep_store.delete_keep(keep_id=session_keep_bare)
            raise

==== M02_guarded_delete :: loremaster/loremaster/server.py
---- ANCHOR
        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )
---- REPLACEMENT
        try:
            result = await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )
        except _AgentRegistryError:
            if keep_store is not None and session_keep_bare is not None:
                scoped = await self.agent_registry._query(
                    "SELECT count() FROM agent WHERE scope = $s GROUP ALL", {"s": keep_scope(session_keep_bare)}
                )
                if not scoped:
                    await keep_store.delete_keep(keep_id=session_keep_bare)
            raise

==== M02b_guarded_delete_counts :: loremaster/loremaster/server.py
---- ANCHOR
        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )
---- REPLACEMENT
        try:
            result = await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )
        except _AgentRegistryError:
            if keep_store is not None and session_keep_bare is not None:
                scoped = await self.agent_registry._query(
                    "SELECT count() FROM agent WHERE scope = $s GROUP ALL", {"s": keep_scope(session_keep_bare)}
                )
                if not (scoped and scoped[0].get("count")):
                    await keep_store.delete_keep(keep_id=session_keep_bare)
            raise

==== M03_preflight_first_no_readonly_gate :: loremaster/loremaster/server.py
---- ANCHOR
            if existing_keep is not None:
                existing_bare = str(existing_keep.id).split(":", 1)[-1]
                visible = await resolve_visible_keeps(keep_store, member_email=principal.email)
                if keep_scope(existing_bare) not in visible:
                    raise governed.GovernedDenied(foreign_denial)
---- REPLACEMENT

==== M03b_checkpoint_order_gate_read_removed :: loremaster/loremaster/server.py
---- ANCHOR
            existing_keep = await keep_store.get_by_key(f"session:{session}")
            if existing_keep is not None:
                existing_bare = str(existing_keep.id).split(":", 1)[-1]
                visible = await resolve_visible_keeps(keep_store, member_email=principal.email)
                if keep_scope(existing_bare) not in visible:
                    raise governed.GovernedDenied(foreign_denial)
---- REPLACEMENT

==== M04_gate_reads_the_registry :: loremaster/loremaster/server.py
---- ANCHOR
            existing_keep = await keep_store.get_by_key(f"session:{session}")
---- REPLACEMENT
            await self.agent_registry._select_row(self.agent_registry._agent_id(session, agent))
            existing_keep = await keep_store.get_by_key(f"session:{session}")

==== M05_gate_mints :: loremaster/loremaster/server.py
---- ANCHOR
            existing_keep = await keep_store.get_by_key(f"session:{session}")
---- REPLACEMENT
            existing_keep = await keep_store.get_or_create_keyed(
                key=f"session:{session}", type="session", keeper_email=principal.email, name=session
            )

==== M06_no_post_mint_recheck :: loremaster/loremaster/server.py
---- ANCHOR
            session_keep_bare = str(session_keep.id).split(":", 1)[-1]
            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)
            if keep_scope(session_keep_bare) not in visible:
                raise governed.GovernedDenied(foreign_denial)
---- REPLACEMENT
            session_keep_bare = str(session_keep.id).split(":", 1)[-1]

==== M07_registry_no_reread :: loremaster/loremaster/agents.py
---- ANCHOR
            except TxnDomainRejectionError:
                # amendment 29 RS-5: a concurrent identical first register won the CREATE — re-read and
                # take THE re-register path (preflight decides a differing role/spawned_by).
                if await self._select_row(agent_id) is None:
                    raise
---- REPLACEMENT
            except TxnDomainRejectionError:
                # amendment 29 RS-5: a concurrent identical first register won the CREATE — re-read and
                # take THE re-register path (preflight decides a differing role/spawned_by).
                raise

==== M08_agent_backfilled_precount :: loremaster/loremaster/principals.py
---- ANCHOR
    return MigrateGovernedResult(
        table=AGENT_TABLE,
        scanned=unmigrated + already,
        backfilled=_rows_stamped(stamped),---- REPLACEMENT
    return MigrateGovernedResult(
        table=AGENT_TABLE,
        scanned=unmigrated + already,
        backfilled=unmigrated,
==== M09_order_refusal_alone :: loremaster/loremaster/principals.py
---- ANCHOR
    parts: list[str] = []
    if preconditions.unscoped_count > 0:
        parts.append(---- REPLACEMENT
    parts: list[str] = []
    if preconditions.unscoped_count > 0:
        return (
            f"cannot migrate `message` rows before the `agent` table is migrated "
            f"({preconditions.unscoped_count} un-migrated (NONE-scope) agent(s) remain)"
        )
    if preconditions.unscoped_count > 0:
        parts.append(
==== M10_half_counts_swapped :: loremaster/loremaster/principals.py
---- ANCHOR
            "carry an owner but no scope",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry a scope but no owner",---- REPLACEMENT
            "carry a scope but no owner",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry an owner but no scope",
==== M10r_half_counts_swapped :: loremaster/loremaster/principals.py
---- ANCHOR
            "carry an owner but no scope",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry a scope but no owner",---- REPLACEMENT
            "carry a scope but no owner",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry an owner but no scope",
==== M11_info_fail_open :: loremaster/loremaster/principals.py
---- ANCHOR
    if not isinstance(info, dict) or "tables" not in info:
        raise SurrealStoreError(
            f"INFO FOR DB answered a {type(info).__name__} without a `tables` map — the governed-migration "
            "preconditions cannot be read, so nothing was migrated"
        )
    defined = info["tables"]---- REPLACEMENT
    defined = info.get("tables", {}) if isinstance(info, dict) else {}
==== M12_select_fail_open :: loremaster/loremaster/principals.py
---- ANCHOR
    if not isinstance(rows, list):
        raise SurrealStoreError(
            f"the {noun} read answered a {type(rows).__name__}, not a list of rows — nothing was migrated"
        )
    return [row for row in rows if isinstance(row, dict)]---- REPLACEMENT
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
==== M13_verb_count_not_served :: loremaster/loremaster/principals.py
---- ANCHOR
        f"(The store holds {counts.unscoped_agents} agent row(s) with no scope in total.) Adjudicate "---- REPLACEMENT
        "Adjudicate "
==== M14_sender_guard_scope_conjunct_dropped :: loremaster/loremaster/principals.py
---- ANCHOR
        "AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE"---- REPLACEMENT
        "AND sender.owner_principal IS NOT NONE"
==== M15_sender_guard_owner_conjunct_dropped :: loremaster/loremaster/principals.py
---- ANCHOR
        "AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE"---- REPLACEMENT
        "AND sender.scope IS NOT NONE"
==== M16_dangling_after_half_pairs :: loremaster/loremaster/principals.py
---- ANCHOR
    if preconditions.dangling_senders:
        dangling = preconditions.dangling_senders
        shown = [
            f"{sanitise_line(str(message_id))} (sender {sanitise_line(str(sender))})"
            for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]
        ]
        parts.append(
            f"{counts.dangling_sender_messages} legacy message(s) name a dangling sender — their `sender` "
            "link "
            "resolves to "
            f"no agent row, so no owner can be derived from it. First {len(shown)} of {len(dangling)} "
            f"shown: {', '.join(shown)}."
        )
    for ids, count, fact in (
        (
            preconditions.messages_owned_unscoped,
            counts.owned_but_unscoped_messages,
            "carry an owner but no scope",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry a scope but no owner",
        ),
    ):
        if ids:
            parts.append(
                f"{count} message row(s) {fact} — a half-applied store (one column of the governed "
                f"pair was stamped without the other). {_id_sample(ids)}"
            )
---- REPLACEMENT
    for ids, count, fact in (
        (
            preconditions.messages_owned_unscoped,
            counts.owned_but_unscoped_messages,
            "carry an owner but no scope",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry a scope but no owner",
        ),
    ):
        if ids:
            parts.append(
                f"{count} message row(s) {fact} — a half-applied store (one column of the governed "
                f"pair was stamped without the other). {_id_sample(ids)}"
            )
    if preconditions.dangling_senders:
        dangling = preconditions.dangling_senders
        shown = [
            f"{sanitise_line(str(message_id))} (sender {sanitise_line(str(sender))})"
            for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]
        ]
        parts.append(
            f"{counts.dangling_sender_messages} legacy message(s) name a dangling sender — their `sender` "
            "link "
            "resolves to "
            f"no agent row, so no owner can be derived from it. First {len(shown)} of {len(dangling)} "
            f"shown: {', '.join(shown)}."
        )

==== M17_docstring_claims_no_scan :: loremaster/loremaster/principals.py
---- ANCHOR
    """A refusal receipt. ``scanned`` / ``already_migrated`` are ``None`` — a refusal serves ``None`` for any---- REPLACEMENT
    """A refusal receipt, returned before any scan. ``scanned`` / ``already_migrated`` are ``None`` — a refusal serves ``None`` for any
==== M18_half_clause_from_private_ints :: loremaster/loremaster/principals.py
---- ANCHOR
                f"{count} message row(s) {fact} — a half-applied store (one column of the governed "---- REPLACEMENT
                f"{len(ids)} message row(s) {fact} — a half-applied store (one column of the governed "
==== M19_message_counts_never_measured :: loremaster/loremaster/principals.py
---- ANCHOR
    message = table == MESSAGE_TABLE
    return MigratePreconditionCounts(---- REPLACEMENT
    message = False
    return MigratePreconditionCounts(
==== M19r_message_counts_never_measured :: loremaster/loremaster/principals.py
---- ANCHOR
    message = table == MESSAGE_TABLE
    return MigratePreconditionCounts(---- REPLACEMENT
    message = False
    return MigratePreconditionCounts(
```

### §A.6b `regen.py` (anchors re-derived after the reference format pass; M18/M19) — md5 `fdf1f1e97e6c873d02dc06a7a24ecd36`
```python
"""Regenerate the anchors the reference's format pass broke (M10/M13/M16) and add M18/M19 (am-30 wrong builds)."""
import os
SP = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e8143e2c-9066-4565-b312-8d8862ec462c/scratchpad"
P = "loremaster/loremaster/principals.py"
src = open(f"{SP}/ref/{P}").read()
M = {}
a = '''            "carry an owner but no scope",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry a scope but no owner",'''
b = '''            "carry a scope but no owner",
        ),
        (
            preconditions.messages_scoped_ownerless,
            counts.scoped_but_ownerless_messages,
            "carry an owner but no scope",'''
M["M10_half_counts_swapped"] = (a, b)
M["M13_verb_count_not_served"] = (
    '''        f"(The store holds {counts.unscoped_agents} agent row(s) with no scope in total.) Adjudicate "''',
    '''        "Adjudicate "''')
i = src.index("    if preconditions.dangling_senders:\n        dangling = preconditions.dangling_senders")
j = src.index("    order_parts = parts[:1] if preconditions.unscoped_count > 0 else []")
block = src[i:j]
k = block.index("    for ids, count, fact in (")
M["M16_dangling_after_half_pairs"] = (block, block[k:] + block[:k])
M["M18_half_clause_from_private_ints"] = (
    '''                f"{count} message row(s) {fact} — a half-applied store (one column of the governed "''',
    '''                f"{len(ids)} message row(s) {fact} — a half-applied store (one column of the governed "''')
M["M19_message_counts_never_measured"] = (
    "    message = table == MESSAGE_TABLE\n    return MigratePreconditionCounts(",
    "    message = False\n    return MigratePreconditionCounts(")
for name, (anchor, replacement) in M.items():
    assert src.count(anchor) == 1, (name, src.count(anchor))
    os.makedirs(f"{SP}/mut/{name}", exist_ok=True)
    open(f"{SP}/mut/{name}/file", "w").write(P)
    open(f"{SP}/mut/{name}/anchor", "w").write(anchor)
    open(f"{SP}/mut/{name}/replacement", "w").write(replacement)
decl = open(f"{SP}/mut/declared.py").read()
decl = decl.replace('A4 = A28 + "TestARefusalServesWhatItMeasured63cIAa28::"',
                    'TYPED = A28 + "TestTheMeasuredCountsAreTypedFields63cIAa28::"')
start = decl.index('    "M13_verb_count_not_served":')
end = decl.index('    "M14_sender_guard_scope_conjunct_dropped":')
decl = decl[:start] + '    "M13_verb_count_not_served": [TYPED + "test_am30_pin1_perturbing_a_field_moves_the_reason[unscoped_agents]"],\n' + decl[end:]
start = decl.index('    "M17_docstring_claims_no_scan":')
end = decl.index("}\nif __name__")
decl = decl[:start] + '''    "M17_docstring_claims_no_scan": [TYPED + "test_A4_no_docstring_claims_a_refusal_scans_nothing"],
    "M18_half_clause_from_private_ints": [TYPED + f"test_am30_pin1_perturbing_a_field_moves_the_reason[{f}]"
        for f in ("owned_but_unscoped_messages", "scoped_but_ownerless_messages")],
    "M19_message_counts_never_measured": [TYPED + "test_am30_the_served_fields_are_the_measured_counts[P_message]",
        *[TYPED + f"test_am30_pin1_perturbing_a_field_moves_the_reason[{f}]"
          for f in ("dangling_sender_messages", "owned_but_unscoped_messages", "scoped_but_ownerless_messages")],
        TYPED + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[P_message]",
        TYPED + "test_am30_pin2_every_count_in_the_reason_is_a_field_value[RS-1]",
        A19B + "test_KP2_the_dangling_sender_sample_reads_THE_constant"],
''' + decl[end:]
open(f"{SP}/mut/declared.py", "w").write(decl)
print("ok")
```

### §A.6c `regen2.py` (M02b / M03b) — md5 `a222609ecd0769eaacf3cec32cb0fda4`
```python
"""M02 corrected (the guarded delete keys on the count VALUE — count() GROUP ALL returns [{'count': 0}] on 3.2.4,
probed, so the first M02 never deleted: a degenerate wrong build) and M03b (the TRUE checkpoint order: the whole
read-only gate removed, its get_by_key read included — M03 as first written left the read in place)."""
import os
SP = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e8143e2c-9066-4565-b312-8d8862ec462c/scratchpad"
F = "loremaster/loremaster/server.py"
src = open(f"{SP}/ref/{F}").read()
m02 = open(f"{SP}/mut/M02_guarded_delete/replacement").read()
old = "                if not scoped:\n"
assert m02.count(old) == 1
os.makedirs(f"{SP}/mut/M02b_guarded_delete_counts", exist_ok=True)
open(f"{SP}/mut/M02b_guarded_delete_counts/file", "w").write(F)
open(f"{SP}/mut/M02b_guarded_delete_counts/anchor", "w").write(open(f"{SP}/mut/M02_guarded_delete/anchor").read())
open(f"{SP}/mut/M02b_guarded_delete_counts/replacement", "w").write(
    m02.replace(old, "                if not (scoped and scoped[0].get(\"count\")):\n"))
gate = '''            existing_keep = await keep_store.get_by_key(f"session:{session}")
            if existing_keep is not None:
                existing_bare = str(existing_keep.id).split(":", 1)[-1]
                visible = await resolve_visible_keeps(keep_store, member_email=principal.email)
                if keep_scope(existing_bare) not in visible:
                    raise governed.GovernedDenied(foreign_denial)
'''
assert src.count(gate) == 1
os.makedirs(f"{SP}/mut/M03b_checkpoint_order_gate_read_removed", exist_ok=True)
open(f"{SP}/mut/M03b_checkpoint_order_gate_read_removed/file", "w").write(F)
open(f"{SP}/mut/M03b_checkpoint_order_gate_read_removed/anchor", "w").write(gate)
open(f"{SP}/mut/M03b_checkpoint_order_gate_read_removed/replacement", "w").write("")
decl = open(f"{SP}/mut/declared.py").read()
decl = decl.replace('K_FILTER = {"M01_unguarded_delete": "not RS5", "M02_guarded_delete": "not RS5"}',
                    'K_FILTER = {"M01_unguarded_delete": "not RS5", "M02_guarded_delete": "not RS5", '
                    '"M02b_guarded_delete_counts": "not RS5"}')
end = decl.index("}\nif __name__")
decl = decl[:end] + '''    "M02b_guarded_delete_counts": [SEQ + "[tokenless-winner-control]", RUNTIME],
    "M03b_checkpoint_order_gate_read_removed": [
        F2 + "test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads",
        F2 + "test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register"],
''' + decl[end:]
open(f"{SP}/mut/declared.py", "w").write(decl)
print("ok")
```

### §A.7 the registry bound (appended to `scripts/pending_contracts.yaml`) — md5 `bc78d6460bb7dfc6a4501dd9027fa32b`
```yaml
# Packet 63c-i-a a28 fix-pass contract (contract-63c-i-a-a28, 2026-09-26, checkpoint 169925f — lead directive
# #17055, the #461 shape). Amendments 26–29 rule ORDER changes, a deletion and behavioural fixes (no new symbol);
# amendment 30 rules the ONE new symbol pair — `MigratePreconditionCounts` + `MigrateGovernedResult.preconditions`.
# Each file below names that pair STATICALLY in a runtime-inert `if TYPE_CHECKING:` block, so this bound OWNS both
# the typecheck lines and every RED-at-169925f pytest leg in those files (REPORT-contract-63c-i-a-a28.md §RED).
# The pair is a PROXY for "the a28 fix pass landed": the same builder lands every pinned behaviour in one pass.
# SELF-DESTRUCTS: the day the build lands the pair, every file stops erroring — delete this entry WITH the build.
- id: packet-63c-i-a-a28-contract
  owner: packet 63c-i-a fix pass (amendments 26-30) — the a28 fix builder
  reopen_trigger: the fix build lands loremaster.governed.MigratePreconditionCounts and
    MigrateGovernedResult.preconditions — then every file below stops erroring, this entry self-destructs and must
    be deleted with the build
  ruling: docs/design/2026-09-26-packet63c-amendment-26.md + amendment-27 (40c188d) + amendment-28 (eb75f57,
    17c52b7) + amendment-29 (a92d33e) + amendment-30; contract receipts REPORT-contract-63c-i-a-a28.md §RED
    (archived with the wave)
  rationale: contract-ahead — the a28 pins are written against the checkpoint 169925f (cold audit NO-GO) before the
    fix builder runs; a pytest-only behavioural RED is unregistrable (#461, routed to packet 09b), so the files
    carrying one name amendment 30's ruled pair statically (never a manufactured error)
  files:
  - path: loremaster/tests/test_fixwave_a28_63c_i_a.py
    missing_symbols:
    - loremaster.governed.MigratePreconditionCounts
    - MigrateGovernedResult.preconditions
  - path: loremaster/tests/test_fixwave_a19a_63c_i_a.py
    missing_symbols:
    - loremaster.governed.MigratePreconditionCounts
    - MigrateGovernedResult.preconditions
  - path: loremaster/tests/test_fixwave_a19b_63c_i_a.py
    missing_symbols:
    - loremaster.governed.MigratePreconditionCounts
    - MigrateGovernedResult.preconditions
```

### §A.8 `probe_count_empty.py` — output: `EMPTY-SET [{'count': 0}] | CONTROL [{'count': 1}] | EMPTY-TABLE [{'count': 0}]` (spike-surreal 3.2.4, 2026-09-26) — md5 `bc56ee4042f9218ce8b321c73e056a3b`
```python
"""Probe (store-ref §2 claim): what does `SELECT count() FROM t WHERE <false> GROUP ALL` return on the test store?
Control: the same statement over a matching row. Throwaway database, reaped. NEVER :18500."""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database

async def main() -> None:
    env = make_env(database=unique_database(), dim=8)
    assert "18000" in env.url, env.url
    conn = await connect_admin(env)
    try:
        await run(conn, "DEFINE TABLE probe_t SCHEMALESS")
        await run(conn, "CREATE probe_t:one SET scope = 'keep:x'")
        empty = await run(conn, "SELECT count() FROM probe_t WHERE scope = 'keep:nothing' GROUP ALL")
        control = await run(conn, "SELECT count() FROM probe_t WHERE scope = 'keep:x' GROUP ALL")
        await run(conn, "DEFINE TABLE probe_empty SCHEMALESS")
        empty_table = await run(conn, "SELECT count() FROM probe_empty GROUP ALL")
        print("EMPTY-SET", repr(empty), "| CONTROL", repr(control), "| EMPTY-TABLE", repr(empty_table))
    finally:
        await conn.close()
        await drop_database(env)

asyncio.run(main())
```

### §A.9a `rewrap.py` (lint helper) — md5 `a8cbec4b0ba03fb3b45e4b4860536eef`
```python
"""Re-wrap over-long COMMENT and triple-quoted-string lines at a width (code lines are reported, not touched)."""
import io, sys, tokenize

WIDTH = 110

def string_lines(source: str) -> set[int]:
    lines: set[int] = set()
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.STRING and tok.string.lstrip("rbfuRBFU").startswith(('"""', "'''")):
            lines.update(range(tok.start[0], tok.end[0] + 1))
    return lines

def split(line: str, prefix: str) -> list[str]:
    out = []
    while len(line) > WIDTH:
        cut = line.rfind(" ", len(prefix) + 1, WIDTH + 1)
        if cut <= len(prefix):
            break
        out.append(line[:cut].rstrip())
        line = prefix + line[cut + 1 :]
    out.append(line)
    return out

for path in sys.argv[1:]:
    source = open(path).read()
    docs = string_lines(source)
    new, code = [], []
    for number, line in enumerate(source.split("\n"), start=1):
        if len(line) <= WIDTH:
            new.append(line); continue
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("#"):
            new.extend(split(line, indent + "# "))
        elif number in docs and not stripped.startswith(('"""', "f\"", "assert", "return")) or (number in docs and stripped.startswith('"""')):
            new.extend(split(line, indent))
        else:
            new.append(line); code.append(f"{path}:{number}")
    open(path, "w").write("\n".join(new))
    for site in code:
        print("CODE", site)
```

### §A.9b `splitstr.py` (lint helper) — md5 `718861109d25c8ccab104b9ea159a7e3`
```python
"""Split an over-long single-literal code line (``f"…"`` / ``"…"`` + optional trailing punctuation) into two
adjacent literals at a space; the f-prefix is kept only on a part carrying a placeholder."""
import re, sys
WIDTH = 110
pattern = re.compile(r'^(?P<indent>\s*)(?P<lead>\)?,?\s*)?(?P<prefix>f?)"(?P<body>.*)"(?P<tail>[,)]*\s*)$')
for path in sys.argv[1:]:
    lines = open(path).read().split("\n")
    out = []
    for line in lines:
        match = pattern.match(line) if len(line) > WIDTH else None
        if not match or match.group("lead"):
            out.append(line); continue
        indent, prefix, body, tail = match.group("indent"), match.group("prefix"), match.group("body"), match.group("tail")
        room = WIDTH - len(indent) - 3
        cut = body.rfind(" ", 0, room)
        if cut <= 0:
            out.append(line); continue
        first, second = body[: cut + 1], body[cut + 1 :]
        mark = lambda part: "f" if prefix and "{" in part else ""
        out.append(f'{indent}{mark(first)}"{first}"')
        out.append(f'{indent}{mark(second)}"{second}"{tail}')
    open(path, "w").write("\n".join(out))
```
