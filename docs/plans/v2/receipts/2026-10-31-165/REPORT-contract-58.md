brief-base v16 read · brief project v7 read

# REPORT — contract-58 (packet 58: supersede RE-ANCHORS its dependents · task guarded-append shell · #130)

## SUMMARY BLOCK
- **State: done-with-deviations** — contract for packet 58 committed (tests only); satisfiable (reference build: full suite set-equal to the HEAD baseline, 0 attributable failures); 14/14 mutation proofs HELD; RED@HEAD = 68, all right-reason.
- Deviations: (1) FORK-A/FORK-C surfaced → RULED mid-flight by amendment 1 (`f4e96b4`), contract re-keyed; (2) `scripts/test_forgery_door_sweep.py` DUAL-edited under my reading of "existing task-ledger test" (§FLAGS 3); (3) `scripts/esc1_write_path_cycle_closure.py` breaks post-build typecheck — outside my set, exact edit in §FLAGS 1; (4) one `pkill -f` touched only my own shell (§FLAGS 6).
- Packages considered: none — no production mechanism specified (the reference build extends shipped seams only).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 5 new reusable test symbols, all dispositioned (§DRY LEDGER; the EXPLAIN walker REUSED).
- Graded: n/a
- Decisions needed: (a) #130 `owner=`-only query over a superseded row — spec-silent, unpinned (§DECISIONS 1); (b) the boot heal's single-transaction size vs `TXN_STATEMENT_HARD_CAP` on a large legacy population (§DECISIONS 2).
- Receipts: entry checks §1 · forks §FORKS · per-ruling §RULINGS · required-green §REQUIRED-GREEN · DUAL §DUAL · reach §REACH · SAT §SAT · mutations §MUTATION · RED@HEAD §RED · gates §GATES · held patch §HELD (385-line diff, `git apply --check` clean on the shared tree 2026-09-26) · builder constraints §BUILDER CONSTRAINTS · doors §CANDIDATE DOORS · reference build §APPENDIX-REF.

## §0 Capability check (brief-base §4)
- Idle-gate contract file: WRITTEN — `/tmp/claude-idle-gate-lore/297217bd-cb03-409c-ac95-0eb7ca9bf74b-contract-58.contract` = `{"artifact": "REPORT-contract-58.md"}` (session id taken from the lead's scratchpad path; this agent has no `$CLAUDE_SESSION_ID`).
- lore: REACHABLE. `lore_index()` 2026-09-26 ~14:02Z: 3843 files, watched root `/workspace` @ `feat/surreal-unification` `1206233`. Registered on `lore_comms` as `contract-58` (session `63c-20260924`, cadence ≤20m).
- grep/rg hook-blocked (#473): every textual sweep in this report used `awk` — said so where used.
- Brief-base §2 says "never commit"; the spawn brief orders ONE commit — spawn brief wins (precedence), not a deviation.

## §1 Entry checks (P58 "Entry check", RELATIVE facts, measured 2026-09-26 at `1206233`)
1. `lore_verify loremaster.tasks.TaskLedger._guarded_append_fragment` → `not_found`. Extraction not yet done — item 2 is 58's.
2. `supersede_task` read (`TaskLedger.supersede_task`, `_supersede_fragment`): composes stamp + THROW + CREATE + successor RELATEs; NOTHING touches dependents. #356/#130 unresolved.
3. **Strand reproduced LIVE** on the TEST store `ws://127.0.0.1:18000` (engine `surrealdb-3.2.4+20260803.93ab219`), throwaway DB, by the committed instrument `scripts/probe_reanchor_58.py` (exit 0):
   ```
   A: Y.blocked_by=['2b424fd9a75644b19405e149fe7cd580'] edge X->Y=True edge X'->Y=False claim(Y).claimed=False direct_dependents(X)=['49bffadf79e84e39a1776a0b92e74ab8']
   A: WORLD = STRAND (pre-58: #356 reproduced)
   A control: ordinary waiter freed by done — instrument can see a win
   ```
   Same probe, kickoff §1 FLAG discharged — the `array::map` + `IF … THEN … ELSE … END` closure spelling WORKS on 3.2.4 inside the guarded shell composed through production `compose`/`execute_transaction` (order kept, `[old, old]`→`[new]`, `[old, new]`→`[new]`); the `{ } ELSE { }` block spelling works too; a zero-match guarded rewrite THROWs and rolls a preceding witness CREATE back (control); `DELETE blocks WHERE in = $old` removes exactly old's outgoing edges and an unrelated edge survives (control). The fallback (client-computed array + CAS) is NOT needed.
4. Cross-module DRY ledger row: see §FINDINGS (checked below).
5. Suite/currency at HEAD: see §GATES.

## §FORKS — surfaced (brief-base §2: two readings → both written, pick stated)
**BOTH RULED while this contract was in flight** — `docs/design/2026-09-26-packet58-amendment-1.md` @ `f4e96b4` (sidecar-64): FORK-A = **A1** (+ a served `reblocked` subset); FORK-C = **R1 CLOSED in-txn** (closing guard → typed teaching refusal, NO auto-retry) and **R2 a NAMED bound HEALED at boot** (`_reanchor_stragglers` beside the backfill) + an index rider (held patch). The contract was re-keyed to the amendment (§RULINGS rows A1/R1/R2/IDX). Original fork text kept below as provenance.

### FORK-A — superseding a TERMINAL predecessor X (`done`/`wontfix`) — DECISION NEEDED (operator)
`supersede_task` has no status guard (read `TaskLedger.supersede_task` at `1206233`): a `done` X can be
superseded today. F-2 rules on the DEPENDENT's status; nothing rules on X's. Two readings, different code:
- **(A1, my pick — P58 Mission is literally ∀: "every dependent Y (`blocked_by ∋ X`) follows the work to X'")** re-anchor ∀ dependents whatever X's status. Consequence: superseding a DONE X **re-blocks** its dependents (X' is open) — an `open` Y that was claimable becomes unclaimable until X' resolves; a `claimed`/`in_progress` Y keeps working (blocked_by gates only claims).
- **(A2)** refuse supersede of a terminal X, or skip re-anchor when X is terminal (Y keeps pointing at a done X, which resolves). A2 needs a status guard in the stamp CAS (race with a concurrent `→done`).
The contract pins A1 ONLY in `test_supersede_reanchor_58.py::TestSupersedeOfATerminalPredecessor` (one class — delete it if A2 is ruled). Every other pin is fork-independent.

### FORK-C — the "strand impossible" claim holds only for SEQUENTIAL interleavings — DECISION NEEDED (operator)
P58 Provenance: *"re-anchor makes the strand impossible"*. Under concurrency it does not, by construction of the kickoff §1 shape (dependents pre-read, then per-dependent fragments):
- **R1 (constructible, PINNED):** a `create_task(Y, blocked_by=[X])` that COMMITS after supersede's dependents read and BEFORE its transaction → Y is not in the fragment list → Y stranded on a superseded X. The contract pins the OUTCOME ∀ builds: *after `supersede_task` returns, no row's `blocked_by` names X* — OR it raises a `TaskLedgerError` and nothing changed. (Cheap fix inside the kickoff's shape: one closing guard statement `IF <any row still names $old> { THROW }` → rollback → refuse/retry. The derived cap absorbs the +1 automatically.)
- **R2 (NOT closable by 58's re-anchor, NOT pinned):** `create_task`'s R10(ii) superseded-blocker pre-check runs OUTSIDE its transaction; a create whose pre-check sees X live but COMMITS after the supersede → Y stranded; and under snapshot isolation two genuinely concurrent txns (create reads X live / supersede scans dependents) are write-skew — neither writes a key the other writes, so neither conflicts. Closing it needs create's txn to WRITE something the supersede writes (a design choice). **Recommendation:** 58 pins R1; R2 + write-skew become a NAMED, PINNED bound (a finding with the re-open trigger "any strand observed on `:18500` whose blocker was superseded after 58 deployed"), not a builder improvisation (design-problem rule).

## §RULINGS — per-ruling table (ruling · pin · wrong build killed · receipt)
Files: `S` = `loremaster/tests/test_supersede_reanchor_58.py` · `G` = `…/test_task_guarded_shell_58.py` · `P` = `…/test_task_claimable_partition_58.py` · `R` = `…/test_supersede_render_58.py` (HELD — ships with the patch) · support = `…/_reanchor_58_support.py` (not collected). RED@HEAD column measured 2026-09-26 at `5d549a1` (§RED).

| ruling | pin (class::test) | wrong build killed | RED@HEAD |
|---|---|---|---|
| P58 IN-1 / F-2 re-anchor ∀ | `S::TestEveryDependentFollowsTheWorkToTheSuccessor::*` (9 dependents: open, blocked, in_progress, done, wontfix, dual [X,Other], a SUPERSEDED dependent + its #174-inheriting successor, raw-forced claimed) | skip-terminal; skip-superseded; rebuild-list-drops-Other; append-X'-at-end; column-only (no edge); leftover X→Y edge; doubled edge | RED (4 of 5; bystander GREEN = negative control) |
| IN-1 note | `S::TestEachDependentCarriesTheReanchorNote::*` | note on X / X'; creator-as-actor (SUPERSEDER ≠ CREATOR); Python-merged provenance (prior events rewritten); no `updated_at` | RED (2 of 3) |
| §7.7 typed carrier | `S::TestTheSupersedeItselfIsUnchanged::test_the_result_*` | `str` return; `reanchored` from a post-write read (always `[]`) | RED |
| dedupe (§2 rider) | `S::TestTheRewireDedupes::*` — legacy `[X,X]` → `[X']` + ONE edge; legacy phantom untouched | un-distinct rewrite; RELATE per entry; phantom rewritten/edged | RED |
| atomicity (Exit) | `S::TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[{row_update,edge_create}-k={1,2,3}]` — server-side `DEFINE EVENT … THROW` injection at dependent k; byte snapshot; armed-event control + un-injected completion control | per-dependent txn; stamp committed before rewire | RED (6) |
| cycle (IN-1) | `S::TestACycleClosingRewireIsRefusedWhole::*` (+ 2 controls) | cycle check over the UN-rewired graph; refuse-on-any-legacy-cycle | RED |
| amendment 1 R1 | `S::TestAConcurrentCreateIsRefusedNotStranded` — create injected at the ONE `_apply` seam; typed teaching refusal; byte-inert vs the at-apply snapshot; exactly ONE `_apply` (no auto-retry); second call re-anchors both (control) | pre-read-only rewire (strands Y2); ledger auto-retry; silent success | RED |
| F-1 derived cap | `S::TestTheHubBoundIsDERIVED::*` — accessor == `(HARD_CAP − fixed)//per` with fixed/per MEASURED off a `compose` spy at N=1,2,3 (linearity checked) for K∈{0,2}; cap−1/cap succeed; cap+1 refused byte-inert, teaching, never the bare compose text; in-suite MUTATION (pad the shell +1 statement → cap moves); WARN crossing sized from the same measurement → exactly ONE WARNING with `statement_count`, supersede succeeds; below-threshold → none | literal cap; formula not derived from the builder; refusal after a write; compose's generic error served; WARN as refusal | RED |
| backfill no-op | `S::TestTheBootBackfillAfterAReanchorIsANoOp::*` | column-only re-anchor (backfill would mint X'→Y) | GREEN@HEAD — a wrong-58-build discriminator (docstring says so) |
| amendment 1 R2 heal | `S::TestTheBootHealReanchorsStragglers::*` — raw stragglers over TWO chains, three rows → `count == 3` (not chains, not blockers); idempotent + silent second boot; 3-hop → HEAD; done head → claimable | no heal; stop at first successor; count chains; re-log every boot; leftover old edge | RED (3 of 4; idempotence GREEN@HEAD) |
| amendment 1 A1 | `S::TestSupersedeOfATerminalPredecessorA1::*` — `reblocked` == exactly the previously-claimable (open, unowned, other blockers terminal: Y, Y2) — not W (waits on an open row), not Z (claimed); open X → `reblocked == []`; claim pre-read race (below) | status branch; silent re-block; reblocked ≠ subset | RED |
| 58 breaks claim's "blocked_by immutable" | `S::…A1::test_a_claim_whose_PRE_READ_predates_the_reanchor_can_NOT_win` — supersede injected at the claim's `_apply` | count-compare CAS on a stale pre-read list | RED |
| required-green | `S::TestRequiredGreen::*` — zero dependents (only the K successor edge); #174 inherit/clear/replace with a dependent; 4-way double-supersede race → one winner, re-anchored ONCE; **a CONSTRUCTED pre-read-passing loser** (the winner commits at the loser's `_apply`) → `IllegalTransitionError`, nothing left behind (added after mutation M1 showed the gather race never reaches the in-txn CAS); superseded X never unblocks | regressions of #174 / the stamp CAS / R10; a stamp CAS whose THROW is gone | mixed (see §RED) |
| §3 / #489 one producer | `G::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::*` + `G::TestTheScannerSeesAHandRolledClone::*` (4 discriminators) | a 4th hand-rolled clone (57's future assign/release included) | RED (2 of 3) |
| §4 seam | `G::TestTheShellIsTheSeam64aGoverns::*` — kw-only names; `where_conjuncts` parenthesised (SEMANTIC: a true-OR + false conjunct must THROW; control writes); `event=None` appends nothing | unparenthesised join; positional params | RED |
| §4 rider i (sharing) | `G::TestSharingIsProvenByMutationALWAYSTHROW::*` (per caller, selective by event action, + control) and `G::TestSharingIsProvenByMutationTHEAPPEND::*` (all 4 callers + the boot heal) | private copy wearing the shared name; routing without sharing | RED |
| claim through the shell | `G::TestClaimWinGainsAnEventLossWritesNothing::*` — win +1 `claim` event; loss ∈ {owned, blocked, superseded, wontfix} → `ClaimResult(False)`, byte-identical row | raise-on-loss; event on loss | win RED; losses GREEN (preserved-with-pin) |
| §4 rider iii/iv | `G::TestParamNamesDoNotCollideAcrossComposedShells`, `G::TestUpdatedAtIsStampedByTheShellForEveryCaller`, `G::TestTheClaimCASStillDecidesOnlyOnce` (8-way) | colliding names; unstamped re-anchor; loser event | RED / RED / GREEN |
| #130 (a) reading B | `P::TestASupersededRowMatchesNoStatusFilter`, `P::TestASupersededRowIsInNeitherPartition` (+ unfiltered/get/render marker preserved) | superseded served under `status=`, `blocked=False`, `blocked=True` | RED (preserved leg GREEN) |
| #130 both directions | `P::TestEverythingServedAsClaimableIsClaimableAndViceVersa::*` — ∀ served → claim WINS; refused ∉ served (+ CAS control on each refused row); completeness | served-but-refused; over-exclusion | RED (completeness GREEN) |
| #130 (c) | `P::TestTheClaimLossRenderNamesSupersession::*` — own-supersession branch + LEGACY strand (raw seed) | "cleaning up" the branch as dead | GREEN (pinned, not built) |
| held render | `R::*` — N=0 byte-identical; N=3 names all + count; K line iff reblocked; `STRANDED` absent from `server.py` (bare sweep); end-to-end through the tool seam | post-write `direct_dependents` render; kept warning | RED until the patch |
| held index rider | `R::TestTheBlockedByElementIndexServesContainment::*` — DDL emits `FIELDS blocked_by.*`; EXPLAIN IndexScan; control: REMOVE INDEX → TableScan (the walker is `test_keeps_schema.TestTheKeeperIndexFires`, reused) | plain `FIELDS blocked_by` (silent `[]` trap) | RED until the patch |

## §REQUIRED-GREEN — correct builds prior rulings require green (63c am-14's lesson), enumerated FIRST
Each is either an explicit pin in this contract or an existing suite the SAT run keeps green (§SAT):
1. **05b / #174** successor sentinel inherit / `[]` / `[ids]` — `S::TestRequiredGreen::test_the_174_*` (with a live dependent) + existing `test_blocks_edge.py::TestSupersedeCarriesBlockedBy174` (DUAL-accessor only).
2. **R10(ii)** refuse a superseded blocker at create — existing `test_blocks_edge.py::TestASupersededBlockerIsNotASilentBlackHole` (unchanged; its `test_a_DEPENDENT_created_BEFORE…` still holds: the dependent now waits on the OPEN successor).
3. **R10 rejected reading** (superseded ≠ terminal) — `S::TestRequiredGreen::test_a_superseded_X_still_does_not_UNBLOCK_its_dependents`.
4. **The claim CAS** (exactly one winner; owner-identity readback) — `G::TestTheClaimCASStillDecidesOnlyOnce` (8-way) + existing `test_task_ledger.py` race suites.
5. **The stamp CAS** (double supersede → one successor, loser rolls back WHOLE) — `S::TestRequiredGreen::test_a_DOUBLE_supersede_race_*` (4-way, re-anchors once) + existing `test_task_ledger.py::test_concurrent_supersede_creates_exactly_one_successor`.
6. **`transitive_blockers`** + the backfill + edge ≡ column ∀ rows — existing `test_blocks_edge.py` SECTIONS F/K; `S` asserts the mirror ∀ rows after every re-anchor shape.
7. **`FindingLedger._guarded_append_fragment` UNCHANGED** — `G::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer` keeps findings at exactly one producer; existing `test_findings.py` untouched.
8. **#7 chain visibility** — unfiltered `query`/`get` + `[superseded → id]` marker: `P::…::test_the_unfiltered_query_and_get_STILL_serve_it_with_the_chain`.
9. **The #174 render clause** — `R::test_N0_is_byte_identical_to_the_pre58_render` (with a K=2 blocked_by clause).

## §DUAL — removed-behaviour inventory (enumerated FIRST from the reference diff, THEN diffed against kickoff §7's 10 seeds)
My own enumeration (B1–B20) over the reference build's diff (`tasks.py`, held `server.py`/`_task_fakes.py`/`surreal_schema.py`); `§7.n` = the kickoff seed it matches; **NEW** = not in §7.

| # | behaviour (old → new) | §7 | adjudication |
|---|---|---|---|
| B1 | `supersede_task -> str` → `SupersedeResult(successor_id, reanchored, reblocked)` | 7.7 (+ am-1 `reblocked`) | CHANGED API, pinned (`S::…test_the_result_is_the_typed_carrier`). Every caller adjudicated: dispatcher (held patch), the fake (held patch), 15 test sites (DUAL rows D4–D7), `scripts/esc1_write_path_cycle_closure.py` (FLAG — outside my writable set; exact edit in §FLAGS). |
| B2 | supersede writes NOTHING to dependents → rewrites each dependent's `blocked_by`, stamps `updated_at`, appends a note | (mission) | the ruled change; pinned ∀ (S). |
| B3 | "no PRODUCTION path deletes a `blocks` edge" (test_blocks_edge Leg-1 prose, derived at `af3551c`) → supersede + the boot heal DELETE X's outgoing edges | **NEW** | dropped-deliberately (A-174: re-point = DELETE + RELATE; store ref §2 "UPDATE of an edge endpoint is a silent no-op"). The Leg-1 prose in `test_blocks_edge.py` is now FALSE → **FLAG** for the build/audit wave (a docstring claim, not an assertion; I did not rewrite another packet's Leg-1 analysis). |
| B4 | `direct_dependents(X)` after a supersede = the stranded ids → `[]` | 7.2 | CHANGED by construction; pinned (`S::…test_direct_dependents_of_X_is_EMPTY…`). Its docstring ("dependency transfer … DEFERRED, because blocked_by is immutable") is stale → builder rewrites (BUILDER CONSTRAINTS). |
| B5 | render STRANDED warning → re-anchored receipt + K line; render no longer reads `direct_dependents` | 7.1 (+ am-1) | dropped-deliberately + replaced; pinned in R (held). |
| B6 | a LOSING claim commits an empty UPDATE → THROW + rollback, caught in `claim_task` | 7.4 | served `ClaimResult` PRESERVED-WITH-PIN (`G::…test_a_LOSS_is_a_RESULT_with_ZERO_writes_and_NO_event[×4]`). **NEW sub-item:** the catch must not swallow a NON-CAS rollback (a false "not claimable") — pinned `G::TestAClaimThatFailsForANonCASReasonIsLOUD`. |
| B7 | a claim WIN wrote no provenance event → +1 `{actor, action: claim, at}` | 7.3 | ADDED; pinned. The fake's claim does not append one (lockstep drift, FLAG — no pin reads the fake's claim events). |
| B8 | three hand-rolled task shells → ONE | 7.6 | pinned structurally + by in-suite mutation (G). Their "mirrors `_supersede_fragment`'s shape" docstrings → builder rewrites. |
| B9 | `query status=<s>` / `blocked=True|False` served superseded rows → EXCLUDED; unfiltered + `get` keep them | 7.5 | dropped-deliberately (#130 reading B); preserved leg pinned. **Spec-silent:** an `owner=`-only query — NOT pinned, decision needed (§DECISIONS). |
| B10 | `ensure_ready` = DDL + backfill → + the straggler heal (1 extra SELECT every boot; +1 SELECT + 1 txn when stragglers exist) | **NEW** (am-1 R2) | ruled (amendment 1); boot traffic change is a measured cost, not a regression — SAT shows no boot-traffic pin reddened (§SAT). |
| B11 | `TaskLedger._apply` emitted no size telemetry → emits the SAME `store.apply.transaction` / `store.apply.large_transaction` records as `SurrealStore.apply` (reference build routes through `SurrealStore._log_transaction_size`, ONE policy) | **NEW** (kickoff F-1 rider iv) | ADDED; pinned by the WARN-crossing pin. |
| B12 | `_refuse_a_cycle(pending)` → `(pending, overlay=None)` | **NEW** | EXTENDED in place (reference) — a design choice for the builder; the pin is the behaviour (cycle refused whole). |
| B13 | `_relate_fragment(pairs)` → `(pairs, *, prefix="rel")` (two RELATE fragments in one txn collide on `rel{i}_*`) | **NEW** | EXTENDED in place (reference); builder's choice. |
| B14 | supersede txn O(K) → `5 + K + 3N` statements (reference) | 7.8 | the F-1 cap + WARN log name it; pinned (derived). |
| B15 | supersede pre-reads: row + blocker checks → + dependents read (+ other-blocker statuses when X is terminal) | **NEW** | accepted cost (≤2 round trips); unpinned by design (a count pin would freeze the builder's read shape). |
| B16 | superseding a terminal X left dependents unblocked → RE-BLOCKS them (A1) | **NEW** (am-1) | ruled A1; pinned + served (`reblocked`). |
| B17 | a re-anchored dependent's `updated_at` stamps → re-appears in the next rollup window | 7.9 | ACCEPTED (kickoff §2); pinned via `updated_at` stamped. |
| B18 | no `blocked_by` index → `task_blocked_by ON FIELDS blocked_by.*` | **NEW** (am-1 index rider) | held patch; pinned with EXPLAIN + control. |
| B19 | the fake's supersede touched no dependent → lockstep re-anchor + `SupersedeResult` (call-time import) | **NEW** | held patch. |
| B20 | `claim_task`'s *"blocked_by never changes after creation"* (and `MIRROR_IMMUTABLE_VERBS`' comment in `test_blocks_edge.py`) → FALSE after 58 | **NEW** | the claim CAS must decide on the CURRENT column — pinned (`S::…A1::test_a_claim_whose_PRE_READ_predates_the_reanchor_can_NOT_win`); the prose is the builder's to rewrite. |
| 7.10 | R10(iii) `superseded_blockers` render | 7.10 | PRESERVED for legacy strands; pinned by raw seed (`P::TestTheClaimLossRenderNamesSupersession`). |

**Diff against §7:** all 10 seeds matched (7.1–7.10). NEW beyond §7: B3, B6-sub, B10, B11, B12, B13, B15, B16, B18, B19, B20.

### Existing-test DUAL edits (brief: "DUAL comment + a report row each")
| row | file · test | old pin | new pin | why |
|---|---|---|---|---|
| D1 | `test_task_read_surface.py::TestSupersedeWARNSWhenThePredecessorHasDEPENDENTS::test_superseding_a_task_with_dependents_NAMES_them_and_the_SUCCESSOR` | dependent still `blocked_by == [predecessor]` ("WARN, never rewrite") | dependent `blocked_by == [successor]` | 58 discharges R10(iv) (B2) |
| D2 | `test_task_read_surface.py::TestTheCLAIMRenderNamesTheSUPERSEDEDBlockerCase::test_a_claim_blocked_by_a_SUPERSEDED_task_names_it_AND_its_successor` | strand built through the verbs | strand RAW-seeded (legacy) | the verbs can no longer strand (B2); render property unchanged |
| D3 | `test_task_read_surface.py::TestTheSupersededBlockerFactIsTYPEDStateNotARenderSideRead::test_a_LOSS_carries_the_superseded_blockers_ON_THE_RESULT` | same | same | same |
| D4 | `test_task_ledger.py` — 5 bind sites + 2 race partitions + the module docstring | `supersede_task` result used as `str` | read via `_reanchor_58_support.successor_of` (both worlds) | B1 |
| D5 | `test_blocks_edge.py` — 7 bind sites | same | same | B1 |
| D6 | `test_task_read_surface.py` decoy site | same | same | B1 |
| D7 (held) | `test_mcp_server.py::…::test_superseded_task_in_leg1_renders_the_chain_marker` | fake result used as `str` | `.successor_id` | B1 via the fake (held patch; `test_mcp_server.py` may be 63c-adjacent — one-line edit, flagged) |

## §REACH — P1c on every ∀ pin (the set, derived or not; coverage checked; a grown set reds)
| ∀ pin | the set | derived from | coverage CHECKED by | a GROWN set reds? |
|---|---|---|---|---|
| edge ≡ column ∀ rows (`support.assert_edge_mirrors_column_for_every_row`) | every task row of the DB | `SELECT … FROM task` (store truth) | returns the row count; `S` asserts it == `row_count()` | yes — every new row is in the next read; doubled edges visible (compared as sorted LISTS) |
| every dependent rewired / noted / stamped (`S` main world) | the dependents of X | `direct_dependents(X)` BEFORE the supersede — the fixture self-checks it equals the labelled set | the fixture assertion (a label the store does not list, or a listed row with no label, reds) | yes — a new dependent shape added to the fixture is covered by the same loops |
| no row names X after a successful supersede (R1; hub pins) | every task row | `all_columns()` | the scan IS the set | yes |
| one producer per guarded-append ledger (`G`) | every `.py` under the shipped package root | `Path(loremaster.__file__).parent.rglob` + the THROW∧UPDATE∧(append) classification | `test_the_derived_class_covers_both_known_ledgers` (a floor: tasks + findings must be FOUND) + 5 synthetic discriminators | yes — a new module with a guarded-append producer joins the class automatically; a 2nd producer anywhere in a class module reds |
| sharing (`G` ALWAYS-THROW / APPEND) | the four callers (transition, stamp, claim, re-anchor) + the boot heal | kickoff §4 names them (a ruled list, not derived — BOUND stated) | each leg asserts the wrapper SAW its action (`perturbed >= 1` / the mark on the new event) — a caller that bypasses the shell reds by name | partially — a NEW caller of the shell is not auto-enumerated (it is caught by the one-producer scan only if it hand-rolls; a new caller routing correctly needs no pin). Named bound. |
| #130 status sweep | `TASK_STATUSES` | the ledger's own vocabulary constant | `test_the_status_sweep_covered_every_status` (the leaking statuses must be in the sweep) | yes — a new status joins the sweep |
| #130 "served ⇒ claimable" | the served `status=open, blocked=False` set | the served answer | `attempted == len(served) >= len(claimable)` | yes |
| ∀ claim-loss shapes (`G` loss param) | {owned, blocked, superseded, wontfix} | hand-list of the CAS's refusal causes (BOUND: the CAS has these four conjuncts + the new column CAS) | parametrised ids | no — a 5th refusal cause needs a new id (named bound) |
| hub cap (`S`) | cap−1 / cap / cap+1 for K∈{0,2} | `max_reanchor_dependents(K)`, itself checked against the MEASURED composition | the accessor-vs-measurement pin + the in-suite padding mutation | yes — a changed builder moves the measured cap; a literal reds |

## §BUILDER CONSTRAINTS (what the contract forces that the kickoff text alone does not)
1. **Extra shell parameters must DEFAULT.** The contract calls `_guarded_append_fragment` with exactly the kickoff §4 names. The reference build needed a per-call namespace (N re-anchor shells in one txn); it added `namespace: str | None = None` (minted when absent). Kickoff §4 is silent on how the LET var/params get their INDEX with no index parameter — **your choice, but it must default** (64a calls the shell with §4's names).
2. **The claim CAS must decide on the CURRENT column** (58 makes `blocked_by` mutable; the claim path's own docstring leans on immutability). Reference: one more `where_conjunct`: `blocked_by = $clm_blocked_by` (the pre-read list).
3. **`claim_task` must not swallow a NON-CAS rollback** (B6-sub). Reference re-derives legitimacy after a rollback (row still open ∧ unowned ∧ unsuperseded ∧ same column ∧ every blocker terminal ⇒ the loss is inexplicable ⇒ re-raise).
4. **R1 refusal**: a `TaskLedgerError` subclass naming X, saying "nothing changed", teaching "retry" — and exactly ONE `_apply` per call (no ledger retry loop). Reference classifies by re-reading `direct_dependents(X)` after the rollback (changed set ⇒ the straggler refusal).
5. **Hub refusal**: a `TaskLedgerError` naming X, N (=cap+1) and the cap; "nothing changed"; raised BEFORE any write; never the bare compose text.
6. **The WARN is the house telemetry record** (a WARNING carrying `statement_count`). Reference routes `TaskLedger._apply` through `SurrealStore._log_transaction_size` — ONE policy; do not clone the threshold compare.
7. **The heal**: note `{actor: "boot-heal", action: "dependency_reanchored", from, to: <chain HEAD>, at, reason: "straggler"}`, INFO `task.backfill.stragglers_reanchored` with `count` = distinct rows healed, silent at 0, through the ONE shell.
8. **Prose owed by the build** (no gate checks it — CLAUDE.md rename/reshape law): `claim_task`'s "blocked_by never changes after creation"; `direct_dependents`' "dependency transfer … DEFERRED"; `_transition_fragment`/`_supersede_fragment` "mirrors …'s shape"; the held render's docstring (done in the held diff); `test_blocks_edge.py` Leg-1 "no PRODUCTION path deletes one" + `MIRROR_IMMUTABLE_VERBS`' comment (FLAG — see §FLAGS).
9. **`SupersedeResult.reanchored` and `.reblocked` are sorted id lists** (the pins compare sorted; the render prints them in the order given).

## §SAT — satisfiability receipt (reference build; FULL suite ALONE; after lint)
- **Instrument:** a `./scripts/scratch_copy.sh` copy at `5d549a1`, restored to HEAD for every file not mine (peers' uncommitted `agents.py`/`principals.py`/`server.py`/`governed.py`/`keeps.py`/`identifiers.py` edits reverted IN THE COPY), + this contract's files + the reference build (`tasks.py`, §APPENDIX-REF) + the held patch (§HELD) + the out-of-set `esc1` one-liner (§FLAGS). Provenance receipt, printed before each run: `loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e4535cbd-3721-4331-86b4-97de76e53aac/scratchpad/ref58/loremaster/loremaster/__init__.py`.
- **Lint first (the "still 0 after lint" leg):** `uv run ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → every leg OK (`lorerunes/lorescribe/loresigil/loremaster/skills/docs/eval/scripts OK · shellcheck OK (7 tracked .sh)`), TC_EXIT=0.
- **Run 1** (pre-adjudication, 2026-09-26 14:39Z): `124 failed, 11592 passed, 62 skipped, 3 xfailed in 372.04s` — 107 in the four `*_63c_i_a` contract files, 1 `test_agent_registry[handler]`, **16 caused by 58** → every one adjudicated: DUAL D8–D12 (existing task-ledger tests), the held link5 driver (D11), the probe's two secret-seam trips (fixed at source — the probe now reuses an allowlisted origin, mints nothing, reads no env), and the claim sharing pin re-keyed to "did not win" after B6.
- **Run 2** (post-lint, 2026-09-26 14:54Z→15:00:52Z, `uv run pytest -n auto`, alone — lane checked by a process-table gate, 15 GB watchdog armed, never fired): **`108 failed, 11609 passed, 62 skipped, 3 xfailed, 7 warnings in 374.33s`**. No `Resource busy` line (#486 not observed).
- **The 108 are the HEAD baseline, set-equal:** the same 108 node ids run in a CLEAN HEAD copy (`scratch_copy.sh` → `head58`, `git checkout -- . && git clean`) → `108 failed, 439 passed in 31.15s`; `comm` both ways → **0 reference-only failures, 0 HEAD-only failures.** They are 63c-i-a's contract-ahead REDs (`test_fixwave_a19{,a,b}_63c_i_a.py` 100, `test_agent_governance_63c_i_a.py` 7) + `test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_blank_role_rule_is_the_SHARED_is_blank[handler]` — all RED at `5d549a1` before any 58 change. **⇒ 0 failures attributable to 58's contract or its reference build.** (Brief rule: *"There are 108 failing tests unrelated to our present scope"* — they belong to 63c-i-a's in-flight build.)

## §HELD — the held integration patch (kickoff §8; amendment 1 index rider) — VERBATIM
**Why held:** `server.py` (+ `surreal_schema.py` per amendment 1) are 63c-shared; the lead applies this AFTER 63c-i-a commits and BEFORE 58's build. It also carries the test edits whose RED/GREEN flips with the patch (the new `test_supersede_render_58.py`, the link5 driver D11, `test_mcp_server.py` D7) and the fake's lockstep (`_task_fakes.py`, B19 — call-time `SupersedeResult` import so nothing becomes uncollectable before the build).
**Between the patch and the build** (a window the lead should keep SHORT — apply the patch, then build): EVERY dispatcher-driven supersede test is RED for the right reason — the patched `AppContext.tasks` reads `.successor_id` off the pre-build `str` (`AttributeError`, real ledger: e.g. `test_task_read_surface.py`'s supersede render classes, `R::TestTheRenderEndToEnd`) or the patched fake imports `SupersedeResult` at call time (`ImportError`, fake-driven: e.g. `test_mcp_server.py` D7). The pure-render pins (`R::TestTheRenderIsTheReanchorReceipt`, link5, slot inventory) and the index pins go GREEN with the patch alone. Measured only in the combined reference (patch + build = GREEN, §SAT); the patch-only intermediate state was NOT run — stated, not assumed.

**Re-verify on the final 63c base (steps):**
1. `git fetch && git log --oneline -3` — confirm 63c-i-a's commit is in; `git diff --stat <this contract's commit> HEAD -- loremaster/loremaster/server.py loremaster/loremaster/store/surreal_schema.py loremaster/tests/_task_fakes.py loremaster/tests/test_link5_render_containment.py loremaster/tests/test_mcp_server.py` — if any moved, re-anchor the hunks by SYMBOL (`AppContext.tasks` supersede branch, `AppContext._render_supersede_result`, `_task_statements`, `FakeTaskLedger.supersede_task`, the link5 `P("_render_supersede_result", …)` entry, `test_superseded_task_in_leg1_renders_the_chain_marker`).
2. `git apply --check <patch>` then `git apply <patch>`.
3. Sweep, bare and anchor-free (CLAUDE.md rename law), over `loremaster/`: `STRANDED` → 0 hits in `server.py`; `direct_dependents(` → no call in the supersede branch of `AppContext.tasks`.
4. `uv run pytest -q loremaster/tests/test_supersede_render_58.py loremaster/tests/test_link5_render_containment.py loremaster/tests/test_render_slot_inventory.py loremaster/tests/test_mcp_server.py -k "supersede or render or slot"` — the pure-render pins GREEN; the end-to-end + D7 RED with `SupersedeResult` import errors (pre-build) — a PASSED count in the tail, never a bare exit.
5. After 58's build: the same set GREEN, then the full suite alone.

```diff
diff --git a/loremaster/loremaster/server.py b/loremaster/loremaster/server.py
index 4b401d4..fe10f0d 100644
--- a/loremaster/loremaster/server.py
+++ b/loremaster/loremaster/server.py
@@ -4551,13 +4551,14 @@ class AppContext:
             rendered, writes = AppContext._render_task_transition(task, actor), 1
         elif action == _TASK_ACTION_SUPERSEDE:
             predecessor = _require_arg(task_id, "task_id")
-            successor_id = await self.task_ledger.supersede_task(
+            superseded = await self.task_ledger.supersede_task(
                 predecessor,
                 subject=_require_arg(subject, "subject"),
                 description=_require_arg(description, "description"),
                 created_by=_require_arg(created_by, "created_by"),
                 blocked_by=blocked_by,
             )
+            successor_id = superseded.successor_id
             # #174: SURFACE the successor's resolved blocked_by so a rewire that forgot
             # its override (or inherited stale deps) is seen at once — the harm #174 fixes
             # is VISIBILITY. Read it back from the ledger (the authoritative resolution),
@@ -4567,7 +4568,8 @@ class AppContext:
                 AppContext._render_supersede_result(
                     predecessor,
                     successor_id,
-                    await self.task_ledger.direct_dependents(predecessor),
+                    superseded.reanchored,
+                    superseded.reblocked,
                     successor.blocked_by,
                 ),
                 1,
@@ -4827,51 +4829,43 @@ class AppContext:
     def _render_supersede_result(
         task_id: str,
         successor_id: str,
-        dependents: list[str],
+        reanchored: list[str],
+        reblocked: list[str],
         successor_blocked_by: list[str],
     ) -> str:
-        """Render a supersession, WARNING about the dependents it just stranded (R10(iii)).
-
-        Supersession is NOT terminal (ruling R10 refused to make it so — the work MOVED,
-        it did not finish), so the claim CAS keeps counting the predecessor as unresolved
-        and every task blocked on it becomes unclaimable **forever**, silently: nobody in
-        the fleet ever learns it, and those tasks' owners simply find work that never
-        becomes claimable. R10(ii) closed the at-CREATE door; this is the door reachable
-        only when the supersede happens AFTER the dependents already exist.
-
-        ⚠ It **NAMES** them rather than counting them: the caller's next move is to
-        re-point those rows at the successor, and it cannot do that from a number. And it
-        **WARNS, never rewrites** — dependency transfer is R10(iv) and is DEFERRED,
-        because it would break the post-creation immutability of ``blocked_by`` that the
-        claim path rides.
-
-        ⚠ The warning fires only when something was actually stranded. A sentence appended
-        to every supersede is an imperative riding a verdict that is not true — the shape
-        ruling R8 split apart — and a warning that always fires is a warning nobody reads.
-        """
-        # #174: NAME the successor's resolved blocked_by (each id contained via
-        # render_attributed — its elements are unconstrained caller ids) so a rewire that
-        # forgot its override, or inherited a stale dependency, is visible at once. Empty
-        # (the common no-dependency reframe) appends nothing — the render is byte-unchanged.
+        """Render a supersession and the dependents it RE-ANCHORED (packet 58, #356).
+
+        The ledger rewires every dependent of the predecessor to the successor in the SAME
+        transaction, so nothing is stranded; this render is the RECEIPT — it names the
+        re-anchored rows (from ``SupersedeResult.reanchored``, the PRE-write list; a post-write
+        ``direct_dependents`` read is ``[]`` by construction) and, per amendment 1 (FORK-A),
+        the subset that was CLAIMABLE before and now waits on the open successor
+        (``reblocked``) — a consequence served, never silent. Both lines are absent when
+        their list is empty, so a no-dependent reframe renders byte-unchanged.
+        """
         blocked_clause = ""
         if successor_blocked_by:
             named = ", ".join(
                 render_attributed(blocker) for blocker in successor_blocked_by
             )
             blocked_clause = f", blocked_by [{named}]"
-        superseded = (
+        lines = [
             f"superseded task {render_attributed(task_id)}; "
             f"successor {render_attributed(successor_id)} (status open{blocked_clause})"
-        )
-        if not dependents:
-            return superseded
-        return (
-            f"{superseded}\n"
-            f"⚠ {len(dependents)} task(s) blocked on {render_attributed(task_id)} are now "
-            f"STRANDED — it can never resolve, so they can never become claimable: re-point "
-            f"them at {render_attributed(successor_id)}: "
-            f"{[render_attributed(dependent) for dependent in dependents]}"
-        )
+        ]
+        if reanchored:
+            lines.append(
+                f"re-anchored {len(reanchored)} dependent(s) from {render_attributed(task_id)} "
+                f"to {render_attributed(successor_id)}: "
+                f"{[render_attributed(dependent) for dependent in reanchored]}"
+            )
+        if reblocked:
+            lines.append(
+                f"⚠ {len(reblocked)} of them were claimable and are now blocked on "
+                f"{render_attributed(successor_id)} (it is open): "
+                f"{[render_attributed(dependent) for dependent in reblocked]}"
+            )
+        return "\n".join(lines)
 
     @staticmethod
     def _render_task_transition(task: Task, actor: str | None) -> str:
diff --git a/loremaster/loremaster/store/surreal_schema.py b/loremaster/loremaster/store/surreal_schema.py
index d3c77b6..9242083 100644
--- a/loremaster/loremaster/store/surreal_schema.py
+++ b/loremaster/loremaster/store/surreal_schema.py
@@ -364,6 +364,8 @@ _TASK_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
 # The ``task`` column the plain status index is built on (the fleet-visible
 # ``query_tasks(status=...)`` filter).
 _TASK_STATUS_FIELD = "status"
+# Packet 58 index rider: the dependency-list column (its element path is indexed).
+_TASK_BLOCKED_BY_FIELD = "blocked_by"
 
 # --- P8b ``finding`` table (lore's durable, fleet-visible FINDING ledger) ------
 #
@@ -1477,6 +1479,12 @@ def _task_statements() -> list[str]:
     statements.append(
         _plain_index(TASK_TABLE, f"{TASK_TABLE}_{_TASK_STATUS_FIELD}", (_TASK_STATUS_FIELD,))
     )
+    # Packet 58 amendment 1 (index rider): the ELEMENT-PATH index (store ref §2) serves
+    # ``blocked_by CONTAINS $x`` — direct_dependents, the supersede's closing guard and the
+    # boot straggler heal — as an IndexScan instead of a TableScan of the task table.
+    statements.append(
+        _plain_index(TASK_TABLE, f"{TASK_TABLE}_{_TASK_BLOCKED_BY_FIELD}", (f"{_TASK_BLOCKED_BY_FIELD}.*",))
+    )
     statements.append(
         _define_relation_table(BLOCKS_RELATION, TASK_TABLE, TASK_TABLE, enforced=True)
     )
diff --git a/loremaster/tests/_task_fakes.py b/loremaster/tests/_task_fakes.py
index 867dc54..628e8b8 100644
--- a/loremaster/tests/_task_fakes.py
+++ b/loremaster/tests/_task_fakes.py
@@ -642,7 +642,7 @@ class FakeTaskLedger:
         description: str,
         created_by: str,
         blocked_by: list[str] | None = None,
-    ) -> str:
+    ) -> Any:
         await asyncio.sleep(0)
         old_task = self._require(task_id)
         # A superseded task is terminal-like: it can never be superseded again,
@@ -679,6 +679,34 @@ class FakeTaskLedger:
             created_at=now,
         )
         self.db.tasks[new_id] = successor
+        # Packet 58 lockstep: every dependent follows the work to the successor (re-anchor).
+        reanchored: list[str] = []
+        reblocked: list[str] = []
+        predecessor_terminal = old_task.status in ("done", "wontfix")
+        for dependent in list(self.db.tasks.values()):
+            if dependent.id == new_id or task_id not in dependent.blocked_by:
+                continue
+            others = [b for b in dependent.blocked_by if b != task_id]
+            was_claimable = (
+                predecessor_terminal
+                and dependent.status == STATUS_OPEN
+                and dependent.owner is None
+                and dependent.superseded_by is None
+                and all(
+                    b in self.db.tasks and self.db.tasks[b].status in ("done", "wontfix")
+                    for b in others
+                )
+            )
+            rewired = list(dict.fromkeys(new_id if b == task_id else b for b in dependent.blocked_by))
+            object.__setattr__(dependent, "blocked_by", rewired)
+            object.__setattr__(dependent, "updated_at", now)
+            dependent.provenance.setdefault("events", []).append(
+                {"actor": created_by, "action": "dependency_reanchored", "from": task_id,
+                 "to": new_id, "at": now.isoformat()}
+            )
+            reanchored.append(dependent.id)
+            if was_claimable:
+                reblocked.append(dependent.id)
         old_task.superseded_by = new_id
         # PKT-06 §1: a supersession is fleet-visible activity too — stamp the
         # OLD row's updated_at (the successor is a fresh create, deliberately
@@ -687,7 +715,11 @@ class FakeTaskLedger:
         old_task.provenance.setdefault("events", []).append(
             {"actor": created_by, "action": "supersede", "successor": new_id, "at": now.isoformat()}
         )
-        return new_id
+        from loremaster.tasks import SupersedeResult  # call-time: absent before packet 58's build
+
+        return SupersedeResult(
+            successor_id=new_id, reanchored=sorted(reanchored), reblocked=sorted(reblocked)
+        )
 
 
 # --------------------------------------------------------------------------- #
diff --git a/loremaster/tests/test_link5_render_containment.py b/loremaster/tests/test_link5_render_containment.py
index a520986..5b0818b 100644
--- a/loremaster/tests/test_link5_render_containment.py
+++ b/loremaster/tests/test_link5_render_containment.py
@@ -2180,19 +2180,25 @@ def _probes() -> list[RenderProbe]:
                     _forge(Task, forge=g, blocked_by=["walked"]),
                     TransitiveBlockers.model_construct(ids=["walked"], truncated=True, max_depth_used=2)),
         ]),
+        # ⚠ DUAL (packet 58 held patch, contract-58): the render's signature gained ``reblocked``
+        # (amendment 1 FORK-A) and ``dependents`` became the PRE-write ``reanchored`` list; each
+        # branch is driven with forgery-carrying tokens — the NEW re-blocked line on its own call.
+        # REPORT-contract-58.md §DUAL D11.
         P("_render_supersede_result", lambda g: [
             _served(
                 "_render_supersede_result", _tok(g, "sup", "task_id"), _tok(g, "sup", "successor_id"),
-                [], [],
+                [], [], [],
             ),
             _served("_render_supersede_result", _tok(g, "sup", "task_id"), _tok(g, "sup", "successor_id"),
-                    [_tok(g, "sup", "dependent")], []),
+                    [_tok(g, "sup", "dependent")], [], []),
+            _served("_render_supersede_result", _tok(g, "sup", "task_id"), _tok(g, "sup", "successor_id"),
+                    [_tok(g, "sup", "dependent")], [_tok(g, "sup", "reblocked")], []),
             # #174: the successor_blocked_by door on its OWN branch (a reframe that kept/
             # replaced a dependency) — dependents empty so the `(status open, blocked_by
             # [...])` clause is the only door, forgery-carrying to discharge the
             # served-free-text hostile-fixture law for the new render branch.
             _served("_render_supersede_result", _tok(g, "sup", "task_id"), _tok(g, "sup", "successor_id"),
-                    [], [_tok(g, "sup", "blocker")]),
+                    [], [], [_tok(g, "sup", "blocker")]),
         ]),
         P("_render_task_transition", lambda g: [
             _served(
diff --git a/loremaster/tests/test_mcp_server.py b/loremaster/tests/test_mcp_server.py
index f28d12f..f4b79ea 100644
--- a/loremaster/tests/test_mcp_server.py
+++ b/loremaster/tests/test_mcp_server.py
@@ -7306,9 +7306,11 @@ class TestRollupDispatch:
         self, rollup_ctx: AppContext
     ) -> None:
         old_id = await rollup_ctx.task_ledger.create_task("s", "d", created_by="me")
-        new_id = await rollup_ctx.task_ledger.supersede_task(
+        # ⚠ DUAL (packet 58, held patch): the fake's ``supersede_task`` returns ``SupersedeResult``
+        # in lockstep with the ledger (kickoff §7.7) — read its successor id. REPORT-contract-58.md §DUAL D7.
+        new_id = (await rollup_ctx.task_ledger.supersede_task(
             old_id, subject="s2", description="d2", created_by="me"
-        )
+        )).successor_id
         rendered = _render_text(await getattr(rollup_ctx, "tasks")(action="rollup"))
         assert (
             f"- [superseded → {new_id}] {render_attributed('s')} "
diff --git a/loremaster/tests/test_supersede_render_58.py b/loremaster/tests/test_supersede_render_58.py
new file mode 100644
index 0000000..91809fe
--- /dev/null
+++ b/loremaster/tests/test_supersede_render_58.py
@@ -0,0 +1,132 @@
+"""HELD-PATCH contract for packet **58** — the served supersede render + the ``blocked_by.*`` index rider.
+
+*Authored 2026-09-26 by ``contract-58`` against ``5d549a1``; it ships WITH the held integration patch
+(``REPORT-contract-58.md`` §HELD) because ``server.py`` / ``surreal_schema.py`` are 63c-shared: before the
+patch lands every pin here is RED for the right reason (the old render still says STRANDED and takes a
+``direct_dependents`` list; the index does not exist).*
+
+Spec: kickoff rulings ``docs/design/2026-09-26-packet58-kickoff-rulings.md`` @ ``c8d3241`` §6 row "the render
+(held patch)" + §7 item 1; amendment 1 ``docs/design/2026-09-26-packet58-amendment-1.md`` @ ``f4e96b4``
+(FORK-A's ``reblocked`` K line; the index rider + its EXPLAIN pin with a control).
+
+The render is a PURE function over the ledger's ``SupersedeResult`` (the PRE-write lists): a render that
+re-read ``direct_dependents(X)`` after the write would always see ``[]`` and lie by omission.
+"""
+
+from __future__ import annotations
+
+import importlib
+from pathlib import Path
+from typing import Any
+
+import test_keeps_schema as keeps_schema  # module-qualified: its Test* classes must not be re-collected here
+from _reanchor_58_support import (
+    CLAIMANT,
+    CREATOR,
+    create,
+    drive_to,
+    ledger58,
+    raw,
+)
+from _surreal_harness import SurrealEnv
+from loremaster.render import render_attributed
+from loremaster.store.surreal_schema import TASK_TABLE, generate_task_ddl
+from loremaster.tasks import STATUS_DONE, TaskLedger
+from test_blocks_edge import _tool_seam
+
+__all__ = ["ledger58"]
+
+SERVER_SOURCE = Path(importlib.import_module("loremaster.server").__file__ or "")
+_PLAN = keeps_schema.TestTheKeeperIndexFires  # the ONE plan walker (``_operators`` / ``_scans_table``)
+
+
+def _render(*args: Any) -> str:
+    from loremaster.server import AppContext
+
+    return str(AppContext._render_supersede_result(*args))  # noqa: SLF001 - the pure render under test
+
+
+def _base(task_id: str, successor_id: str, blocked_by: list[str]) -> str:
+    """Today's no-dependent render, byte for byte (the #174 clause included) — the N=0 oracle."""
+    clause = ""
+    if blocked_by:
+        clause = f", blocked_by [{', '.join(render_attributed(b) for b in blocked_by)}]"
+    return (
+        f"superseded task {render_attributed(task_id)}; "
+        f"successor {render_attributed(successor_id)} (status open{clause})"
+    )
+
+
+class TestTheRenderIsTheReanchorReceipt:
+    def test_N0_is_byte_identical_to_the_pre58_render(self) -> None:
+        assert _render("x-58", "s-58", [], [], []) == _base("x-58", "s-58", [])
+        assert _render("x-58", "s-58", [], [], ["b1", "b2"]) == _base("x-58", "s-58", ["b1", "b2"])
+
+    def test_N3_names_every_reanchored_dependent_and_the_count(self) -> None:
+        rendered = _render("x-58", "s-58", ["d1", "d2", "d3"], [], [])
+        assert rendered.startswith(_base("x-58", "s-58", [])), rendered
+        assert "re-anchored 3 dependent(s)" in rendered, rendered
+        for dependent in ("d1", "d2", "d3"):
+            assert dependent in rendered, rendered
+
+    def test_the_reblocked_line_is_present_IFF_non_empty_and_names_only_the_subset(self) -> None:
+        plain = _render("x-58", "s-58", ["d1", "d2"], [], [])
+        assert "were claimable" not in plain, plain
+        rendered = _render("x-58", "s-58", ["d1", "d2"], ["d2"], [])
+        line = [part for part in rendered.split("\n") if "were claimable" in part]
+        assert len(line) == 1 and "d2" in line[0] and "d1" not in line[0] and "1 of them" in line[0], rendered
+
+    def test_the_STRANDED_warning_is_gone_from_the_server(self) -> None:
+        """Removed-behaviour seed §7.1 (dropped-deliberately: the strand no longer occurs).  A BARE,
+        anchor-free sweep of the served module's text — prose carries no structural anchor."""
+        assert "STRANDED" not in SERVER_SOURCE.read_text(encoding="utf-8")
+
+
+class TestTheRenderEndToEnd:
+    async def test_a_supersede_through_the_tool_seam_serves_the_receipt(
+        self, ledger58: tuple[TaskLedger, SurrealEnv]
+    ) -> None:
+        ledger, _env = ledger58
+        old = await create(ledger, "X, finished")
+        await drive_to(ledger, old, STATUS_DONE)
+        claimable = await create(ledger, "Y — claimable before", [old])
+        other = await create(ledger, "an open blocker")
+        waiting = await create(ledger, "W — already waiting on an open row", [old, other])
+        rendered = await _tool_seam(ledger).tasks(
+            action="supersede", task_id=old, subject="X'", description="d", created_by=CREATOR
+        )
+        assert "re-anchored 2 dependent(s)" in rendered and claimable in rendered and waiting in rendered
+        reblocked = [line for line in rendered.split("\n") if "were claimable" in line]
+        assert len(reblocked) == 1 and claimable in reblocked[0] and waiting not in reblocked[0], rendered
+        assert not (await ledger.claim_task(claimable, CLAIMANT)).claimed
+
+
+class TestTheBlockedByElementIndexServesContainment:
+    """Amendment 1 index rider: ``DEFINE INDEX … FIELDS blocked_by.*`` (store ref §2: the element path is
+    the ONLY spelling that serves containment; a plain ``FIELDS blocked_by`` IndexScans ``=`` and returns
+    ``[]`` — the silent trap)."""
+
+    def test_the_task_ddl_emits_the_ELEMENT_PATH_index(self) -> None:
+        ddl = generate_task_ddl()
+        assert "FIELDS blocked_by.*" in ddl, "the index must be on the ELEMENT path `blocked_by.*`"
+
+    async def test_CONTAINS_is_an_IndexScan_with_the_index_and_a_TableScan_without(
+        self, ledger58: tuple[TaskLedger, SurrealEnv]
+    ) -> None:
+        ledger, _env = ledger58
+        blocker = await create(ledger, "a blocker")
+        await create(ledger, "a dependent", [blocker])
+        statement = f"SELECT id FROM {TASK_TABLE} WHERE blocked_by CONTAINS $x EXPLAIN"
+        plan = await raw(ledger, statement, {"x": blocker})
+        assert "IndexScan" in _PLAN._operators(plan) and not _PLAN._scans_table(plan, TASK_TABLE), (
+            f"`blocked_by CONTAINS $x` is not index-served: {_PLAN._operators(plan)}"
+        )
+        # CONTROL — the SAME statement with the index removed IS a TableScan (the walker can see one).
+        index_rows = await raw(ledger, f"INFO FOR TABLE {TASK_TABLE}")
+        names = [name for name in (index_rows or {}).get("indexes", {}) if "blocked_by" in name]
+        assert len(names) == 1, f"expected exactly one blocked_by index: {names}"
+        await raw(ledger, f"REMOVE INDEX {names[0]} ON TABLE {TASK_TABLE}")
+        control = await raw(ledger, statement, {"x": blocker})
+        assert _PLAN._scans_table(control, TASK_TABLE), (
+            f"CONTROL failed: without the index the walker saw no TableScan: {_PLAN._operators(control)}"
+        )
```

## §FLAGS (outside my writable set — the exact edit, never made)
1. **`scripts/esc1_write_path_cycle_closure.py`** (a `supersede_task` caller; B1) — breaks `typecheck: scripts` once the build lands. Exact edit (proven in the reference copy, typecheck → all legs OK):
   ```diff
   -        d_successor = await ledger.supersede_task(
   +        d_successor = (await ledger.supersede_task(
                "leg_d", subject="D2", description="successor of leg_d",
                created_by="probe-esc1-closure-1",
   -        )
   +        )).successor_id
   ```
   Owner: the 58 builder (it is a caller the build breaks).
2. **`test_blocks_edge.py` module docstring, TRUST Leg-1 row 1** says *"no PRODUCTION path deletes one [a blocks edge] … DERIVED 2026-07-29 at `af3551c`"* — FALSE after 58 (supersede + the boot heal DELETE edges; B3). It is another packet's Leg-1 analysis, so I did not rewrite it; the builder/auditor must (the rename/reshape law: prose no gate checks). Same file: `MIRROR_IMMUTABLE_VERBS`' comment leans on "blocked_by … IMMUTABLE afterwards" (B20).
3. **Writable-set reading I took, stated:** `scripts/test_forgery_door_sweep.py` is a test OF `TaskLedger.ensure_ready`; I treated it as an "existing task-ledger test file" and made the DUAL edit D12 there. If the lead reads the brief's set as `loremaster/tests/` only, revert D12 and hand the two-line change to the builder — the pin is RED post-build either way (it demands exactly 4 boot doors; the ruled heal adds a 5th).
4. **`scripts/probe_reanchor_58.py`** is written under `scripts/` per kickoff §8's boundary table (which the brief makes binding) — not a test file; stated as the reading taken.
5. **Peers' uncommitted WIP is live in the shared tree** (`agents.py`, `principals.py`, `server.py`, `governed.py`, `keeps.py`, `lorerunes/identifiers.py`, `test_loopback_serving.py`, 64b files). My HEAD measurements were taken in CLEAN copies, never against that WIP. The typecheck currency run over the shared tree shows 5 residuals that are NOT mine (`test_loopback_serving.py` ×1, `test_no_raw_listener_in_test_trees.py` ×1, `skills/lore-deploy/tests/test_loopback_home.py` ×2 + their import-untyped) — owners: the 64b / #466 lanes.
6. **Process slip, self-reported:** one `pkill -f` (to stop my own mis-scoped lane watcher) violated "kill by PID only"; its pattern matched only my own shell (exit 144) — no other process was touched. Every later stop was by PID.
7. **The fake's claim appends no `claim` event** (B7 lockstep drift) — no pin reads the fake's claim provenance; flagged, not pinned.

## §DECISIONS NEEDED
1. **#130 `owner=`-only query over a superseded row** — spec-silent (kickoff §5 rules `status=` + `blocked`); NOT pinned. Recommend: serve it (an owner asking "what do I hold" should see a held-then-superseded row, decorated) — i.e. leave as today.
2. **Heal transaction size** — amendment 1's heal composes EVERY straggler into ONE boot transaction; a large legacy population on `:18500` could exceed `TXN_STATEMENT_HARD_CAP` and FAIL THE BOOT loudly (per-straggler shell 2 stmts + relate 1). Not ruled, not pinned. Recommend: the 65 cutover smoke counts stragglers BEFORE the deploy (`SELECT count() FROM task WHERE blocked_by CONTAINSANY (SELECT VALUE record::id(id) FROM task WHERE superseded_by IS NOT NONE)`); if > ~1600, rule a batched heal (each straggler's rewrite is independent, so batching is safe here, unlike the supersede).

## §CANDIDATE DOORS (wrong builds I could NOT kill, or killed only partially — for the adversary)
1. **A new shell CALLER is not auto-enumerated** by the sharing pins (they cover the ruled four + the heal). A future verb that routes correctly needs no pin; one that hand-rolls is caught by the one-producer scan ONLY if it emits `UPDATE` and `THROW` literally in one function (a clone split across two helpers, one emitting the UPDATE and another the THROW, evades the per-function scan — module-level constants are pooled, functions are not).
2. **The claim-loss parametrisation is a hand-list** of four refusal causes; a fifth CAS conjunct gets no loss pin automatically.
3. **R2 write-skew** is not constructible in-suite (genuinely concurrent snapshot txns) — pinned only via the boot heal. A build whose closing guard is correct but whose heal is never CALLED from `ensure_ready` is killed (the heal pins boot via `ensure_ready`).
4. **The WARN pin keys on a `statement_count` attribute** — a build logging the warning under a different structured field would fail a correct-in-spirit build (over-tight, not a door).
5. ~~`reblocked` ignores a superseded-but-open dependent~~ — **CLOSED while writing this report**: the A1 fixture gained V (open, unowned, itself superseded → NOT reblocked) and V' (its #174 successor inheriting [X] → reblocked). Remaining: `reblocked` is pinned for a `done` X only; a `wontfix` X is covered by the same terminal predicate but not by its own fixture.

## §DRY LEDGER (brief-base §6 — new reusable symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_reanchor_58_support.py` readers (`column`, `all_columns`, `edge_pairs`, `snapshot`, `events_of`, `raw_seed_row`, …) | `lore_search("blocks edge set column mirror helper test")` + read `test_blocks_edge.py` SECTION C | `test_blocks_edge._edge_blockers_of` / `_column_blockers_of` / `_assert_mirror` (per-TASK, set-based) | HAND-ROLLED as ONE shared support module for the three 58 files: the existing helpers are PER-ROW and SET-based (they cannot see a doubled edge — the defect class 58 must catch); importing a fixture module's privates would also re-collect its Test classes. |
| `guarded_shell_producers` (AST scanner) | `lore_search("AST scan string constants THROW producer one implementation pin")` | per-file AST pins exist (`test_mcp_server.py` exact-set, `_SCANNED_MEMBERS` scans) — none classify guarded-CAS producers | HAND-ROLLED (no existing scanner answers "which functions emit a guarded CAS"). |
| `_ShellPerturbation` | — (test-local mutation wrapper) | — | HAND-ROLLED, file-local. |
| plan walker for the EXPLAIN pin | `lore_search("EXPLAIN plan IndexScan TableScan walker test")` | `test_keeps_schema.TestTheKeeperIndexFires._operators/_scans_table` | REUSED (module-qualified import). |
| `ApplyHook` (constructed interleaving at `_apply`) | `lore_search("inject concurrent writer between pre-read and transaction test hook")` | 63-rulings' "injected-handle idiom" (prose); no reusable helper found | HAND-ROLLED in the support module, fail-closed (`fired`). |

**Packages considered:** none — no production mechanism specified; the contract pins store behaviour already probed (`scripts/probe_reanchor_58.py`) and every reference-build mechanism extends a shipped seam (`_relate_fragment`, `_refuse_a_cycle`, `compose`, `SurrealStore._log_transaction_size`, `resolve_existing_rows`).

## §MUTATION — every load-bearing pin, declared-then-diffed BOTH ways (`scripts/mutation_proof.py`)
Run from the reference copy root (`loremaster.__file__` inside `…/scratchpad/ref58`, §SAT); scope = the four 58 files; every declared set was written from `pytest --collect-only` ids BEFORE the run that graded it; the tree was restored byte-exact after each (`md5 2caca98b53813f0deb76211d3a3ed354` re-verified after every batch).

| # | mutation (production, reference build) | declared RED | verdict |
|---|---|---|---|
| M1 | shell THROW → `RETURN NONE` | 4 ALWAYS-THROW sharing legs · where_conjuncts · constructed pre-read-passing loser · the one-producer scan (tasks.py stops being a producer) ×2 | **HELD** (run 3) |
| M2 | shell `provenance.events +=` removed | note pin · 4-way race notes · heal count · where_conjuncts control · APPEND sharing ×2 · claim-WIN event · derived-class floor · constructed loser | **HELD** (run 2) |
| M3 | #130 `superseded_by IS NONE` partition clause removed | P: status sweep · blocked=False · blocked=True · served⇒WON · refused∉served | **HELD** |
| M4 | derived cap → literal `1665` | accessor[K=2] · in-suite padding MUTATION · at-cap[K=2] | **HELD** |
| M5 | R1 closing guard removed | R1 refusal | **HELD** |
| M6 | cycle overlay removed (check over the UN-rewired graph) | cycle refusal · backfill-after-refused | **HELD** |
| M7 | claim `blocked_by = $pre-read` CAS conjunct removed | A1 claim pre-read race | **HELD** |
| M8 | dependents' `X'→Y` RELATE removed | edge mirror · dedupe · phantom · backfill no-op · hub ×4 · #174 ×3 · 4-way race · A1 all-status · constructed loser · atomicity edge-injection ×3 | **HELD** (run 2) |
| M9 | `DELETE blocks WHERE in = $old` removed | edge mirror · dedupe · phantom · hub ×4 · #174 ×3 · 4-way race · A1 all-status · constructed loser | **HELD** |
| M10 | heal stops at the FIRST successor | 3-hop → HEAD · done-head frees | **HELD** |
| M11 | `reblocked` over-inclusive | A1 reblocked · R end-to-end K line | **HELD** |
| M12 | a 4th hand-rolled guarded shell added to `tasks.py` | one-producer ×2 | **HELD** |
| M13 | claim swallows EVERY rollback | claim-loud (B6) | **HELD** |
| M14 | index rider removed (held `surreal_schema.py`) | R index DDL · R EXPLAIN | **HELD** |

**What the proofs FOUND (not just confirmed):**
- **Run 1, M1: a non-discriminating pin.** With the shell's THROW disabled, `TestRequiredGreen::test_a_DOUBLE_supersede_race…` (4-way `gather`) stayed GREEN — its losers lose at the SEQUENTIAL pre-read (`superseded_by is not None`), never reaching the in-transaction stamp CAS. Fixed by a CONSTRUCTED pin (`…::test_a_loser_that_PASSED_its_pre_read_rolls_back_WHOLE_via_the_in_txn_CAS`: the winner commits at the loser's `_apply`). Run 2 then showed the gather race is **timing-dependent under M1** (RED this time) — it can be declared neither way, so it is deselected for M1 only (stated in the driver) and stays a required-GREEN pin on correct builds.
- **Runs 1, M2/M8: my PREDICTIONS were incomplete, the pins were right** — the one-producer scan correctly stops seeing a shell that no longer appends/THROWs; the edge-CREATE atomicity injections correctly have nothing to fire on once the RELATE is gone. Declarations corrected BEFORE run 2 (reasoning recorded in the driver's comments).
- Receipts: `…/scratchpad/mutations_run.log` (run 1), `mutations_run2.log` (run 2), `mutations_run3_M1.log` (M1: `PROOF HELD — the declared RED set fired EXACTLY: [8 ids]`) — scratch paths, cited as where the lead can read them this session; the DRIVER below is the durable instrument.

Driver (pasted VERBATIM — brief-base §1 instrument rule):
```python
#!/usr/bin/env python3
"""contract-58 mutation-proof driver — every load-bearing pin, declared-then-diffed BOTH ways.

Runs ``scripts/mutation_proof.py`` once per mutation against the REFERENCE BUILD in a
``scratch_copy.sh`` copy (cwd).  Each mutation's expected-RED set was written down from
``pytest --collect-only`` ids BEFORE the first run (mutation_proof's own bound).  Exit non-zero if any
proof fails.  Usage (from the scratch copy root): ``uv run python <this> [M1 M2 ...]``.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

S = "loremaster/tests/test_supersede_reanchor_58.py"
G = "loremaster/tests/test_task_guarded_shell_58.py"
P = "loremaster/tests/test_task_claimable_partition_58.py"
R = "loremaster/tests/test_supersede_render_58.py"
TASKS = "loremaster/loremaster/tasks.py"
SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
SCOPE = [S, G, P, R]

HUB_MIRROR = [
    f"{S}::TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-1-0]",
    f"{S}::TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-1-2]",
    f"{S}::TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-0]",
    f"{S}::TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-2]",
]
SENTINEL_174 = [
    f"{S}::TestRequiredGreen::test_the_174_sentinel_still_resolves_the_SUCCESSOR_while_dependents_are_rewired[{v}]"
    for v in ("inherit", "clear", "replace")
]
DOUBLE_RACE = f"{S}::TestRequiredGreen::test_a_DOUBLE_supersede_race_reanchors_EXACTLY_ONCE_to_the_WINNER"
EDGE_MIRROR = f"{S}::TestEveryDependentFollowsTheWorkToTheSuccessor::test_the_edge_mirrors_the_column_for_EVERY_row_and_no_edge_leaves_X"
DEDUPE = f"{S}::TestTheRewireDedupes::test_a_legacy_duplicate_X_X_becomes_ONE_successor_entry_and_ONE_edge"
PHANTOM = f"{S}::TestTheRewireDedupes::test_a_legacy_PHANTOM_entry_is_left_untouched_and_carries_no_edge"
A1_ALL = f"{S}::TestSupersedeOfATerminalPredecessorA1::test_every_status_is_rewired_including_claimed"

MUTATIONS: dict[str, dict[str, object]] = {
    "M1-shell-THROW-disabled": {
        # The 4-way GATHER race is timing-dependent under THIS mutation (GREEN in run 1, RED in run 2:
        # its losers sometimes lose at the sequential pre-read, never reaching the in-txn CAS), so it
        # can be declared neither way; deselected here, stated in the report. It stays a required-GREEN
        # pin on correct builds; the CONSTRUCTED pre-read-passing loser is the deterministic discriminator.
        "deselect": [DOUBLE_RACE],
        "file": TASKS,
        "anchor": """        guard = f"IF array::len(${variable}) == 0 {{ THROW '{throw_message}' }}\"""",
        "replacement": """        guard = f"IF array::len(${variable}) == 0 {{ RETURN NONE }}\"""",
        "red": [
            f"{G}::TestSharingIsProvenByMutationALWAYSTHROW::test_TRANSITION_routes_through_the_shell",
            f"{G}::TestSharingIsProvenByMutationALWAYSTHROW::test_the_SUPERSEDE_STAMP_routes_through_the_shell",
            f"{G}::TestSharingIsProvenByMutationALWAYSTHROW::test_the_REANCHOR_routes_through_the_shell",
            f"{G}::TestSharingIsProvenByMutationALWAYSTHROW::test_CLAIM_routes_through_the_shell",
            f"{G}::TestTheShellIsTheSeam64aGoverns::test_where_conjuncts_are_each_PARENTHESISED_and_AND_joined",
            # run 1 finding: the 4-way gather race stays GREEN (its losers lose at the sequential
            # pre-read) — replaced as the discriminator by the constructed pre-read-passing loser:
            f"{S}::TestRequiredGreen::test_a_loser_that_PASSED_its_pre_read_rolls_back_WHOLE_via_the_in_txn_CAS",
            # run 1: the shell no longer emits THROW, so the one-producer scan (correctly) stops seeing it:
            f"{G}::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_the_derived_class_covers_both_known_ledgers",
            f"{G}::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_the_task_ledgers_one_producer_IS_the_shell",
        ],
    },
    "M2-shell-append-removed": {
        "file": TASKS,
        "anchor": """            sets.append(f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${event_param}]")""",
        "replacement": """            pass""",
        "red": [
            f"{S}::TestEachDependentCarriesTheReanchorNote::test_exactly_ONE_new_event_per_dependent_naming_X_X_prime_and_the_SUPERSEDER",
            DOUBLE_RACE,
            f"{S}::TestTheBootHealReanchorsStragglers::test_a_boot_heals_every_straggler_to_its_successor_and_COUNTS_them",
            f"{G}::TestTheShellIsTheSeam64aGoverns::test_where_conjuncts_are_each_PARENTHESISED_and_AND_joined",
            f"{G}::TestSharingIsProvenByMutationTHEAPPEND::test_transition_stamp_claim_and_reanchor_events_all_come_from_the_shell",
            f"{G}::TestSharingIsProvenByMutationTHEAPPEND::test_the_BOOT_HEAL_note_comes_from_the_shell_too",
            f"{G}::TestClaimWinGainsAnEventLossWritesNothing::test_a_WIN_appends_ONE_claim_event_naming_the_owner_and_stamps_updated_at",
            # run 1: the shell no longer appends, so the scan (correctly) drops tasks.py from the class:
            f"{G}::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_the_derived_class_covers_both_known_ledgers",
            f"{S}::TestRequiredGreen::test_a_loser_that_PASSED_its_pre_read_rolls_back_WHOLE_via_the_in_txn_CAS",
        ],
    },
    "M3-130-partition-clause-removed": {
        "file": TASKS,
        "anchor": """            exclude_superseded=status is not None or blocked is not None,""",
        "replacement": """            exclude_superseded=False,""",
        "red": [
            f"{P}::TestASupersededRowMatchesNoStatusFilter::test_no_status_filter_serves_a_superseded_row",
            f"{P}::TestASupersededRowIsInNeitherPartition::test_blocked_False_excludes_superseded_rows",
            f"{P}::TestASupersededRowIsInNeitherPartition::test_blocked_True_excludes_superseded_rows",
            f"{P}::TestEverythingServedAsClaimableIsClaimableAndViceVersa::test_every_row_served_as_claimable_is_WON_by_a_claim",
            f"{P}::TestEverythingServedAsClaimableIsClaimableAndViceVersa::test_nothing_the_CAS_refuses_is_served_as_claimable",
        ],
    },
    "M4-cap-literal": {
        "file": TASKS,
        "anchor": """        return (TXN_STATEMENT_HARD_CAP - fixed) // per""",
        "replacement": """        return 1665""",
        "red": [
            f"{S}::TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[2]",
            f"{S}::TestTheHubBoundIsDERIVED::test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap",
            f"{S}::TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-2]",
        ],
    },
    "M5-R1-closing-guard-removed": {
        "file": TASKS,
        "anchor": """            closing,\n        ]""",
        "replacement": """        ]""",
        "red": [f"{S}::TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES_retry"],
    },
    "M6-cycle-overlay-removed": {
        "file": TASKS,
        "anchor": """        await self._refuse_a_cycle({new_id: dependencies}, overlay=rewired)""",
        "replacement": """        await self._refuse_a_cycle({new_id: dependencies})""",
        "red": [
            f"{S}::TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed",
            f"{S}::TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_REFUSED_supersede_the_backfill_mints_nothing",
        ],
    },
    "M7-claim-column-CAS-removed": {
        "file": TASKS,
        "anchor": """                f"{_COL_BLOCKED_BY} = ${_CLAIM_BLOCKED_BY_PARAM}",\n""",
        "replacement": "",
        "red": [f"{S}::TestSupersedeOfATerminalPredecessorA1::test_a_claim_whose_PRE_READ_predates_the_reanchor_can_NOT_win"],
    },
    "M8-dependent-RELATE-removed": {
        "file": TASKS,
        "anchor": """            self._relate_fragment([(new_id, dependent) for dependent in dependent_ids], prefix="rar"),\n""",
        "replacement": "",
        "red": [
            EDGE_MIRROR, DEDUPE, PHANTOM,
            f"{S}::TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_reanchor_the_backfill_mints_nothing_and_records_nothing",
            *HUB_MIRROR, *SENTINEL_174, DOUBLE_RACE, A1_ALL,
            f"{S}::TestRequiredGreen::test_a_loser_that_PASSED_its_pre_read_rolls_back_WHOLE_via_the_in_txn_CAS",
            # run 1: the edge-CREATE injection has no RELATE to fire on, so the supersede SUCCEEDS:
            *[f"{S}::TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[edge_create-k={k}]" for k in (1, 2, 3)],
        ],
    },
    "M9-X-edge-DELETE-removed": {
        "file": TASKS,
        "anchor": """            statements=[f"DELETE {BLOCKS_RELATION} WHERE in = ${_REANCHOR_OLD_RECORD_PARAM}"],""",
        "replacement": """            statements=[],""",
        "red": [
            EDGE_MIRROR, DEDUPE, PHANTOM, *HUB_MIRROR, *SENTINEL_174, DOUBLE_RACE, A1_ALL,
            f"{S}::TestRequiredGreen::test_a_loser_that_PASSED_its_pre_read_rolls_back_WHOLE_via_the_in_txn_CAS",
        ],
    },
    "M10-heal-stops-at-first-successor": {
        "file": TASKS,
        "anchor": """            seen: set[str] = set()\n            while task_id in successor and task_id not in seen:\n                seen.add(task_id)\n                task_id = successor[task_id]\n            return task_id""",
        "replacement": """            return successor.get(task_id, task_id)""",
        "red": [
            f"{S}::TestTheBootHealReanchorsStragglers::test_a_three_hop_chain_reanchors_to_the_HEAD",
            f"{S}::TestTheBootHealReanchorsStragglers::test_a_DONE_head_frees_the_straggler",
        ],
    },
    "M11-reblocked-over-inclusive": {
        "file": TASKS,
        "anchor": """            if all(status_by_id.get(b) in TERMINAL_STATUSES for b in blockers):""",
        "replacement": """            if True:""",
        "red": [
            f"{S}::TestSupersedeOfATerminalPredecessorA1::test_reblocked_names_exactly_the_previously_CLAIMABLE_dependents",
            f"{R}::TestTheRenderEndToEnd::test_a_supersede_through_the_tool_seam_serves_the_receipt",
        ],
    },
    "M12-a-4th-hand-rolled-shell": {
        "file": TASKS,
        "anchor": """_CLAIM_ALREADY_MESSAGE = "claim lost the compare-and-set\"""",
        "replacement": """_CLAIM_ALREADY_MESSAGE = "claim lost the compare-and-set"


def _assign_fragment_clone(row_id: str) -> list[str]:
    return [
        "LET $a = (UPDATE task SET owner = 'x', provenance.events += [$e])",
        f"IF array::len($a) == 0 {{ THROW '{row_id}' }}",
    ]""",
        "red": [
            f"{G}::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_every_guarded_append_ledger_has_ONE_producer",
            f"{G}::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_the_task_ledgers_one_producer_IS_the_shell",
        ],
    },
    "M13-claim-swallows-every-rollback": {
        "file": TASKS,
        "anchor": """            if await self._still_claimable(task_id, blocked_by):\n                raise""",
        "replacement": """            pass""",
        "red": [f"{G}::TestAClaimThatFailsForANonCASReasonIsLOUD::test_an_injected_rollback_on_a_CLAIMABLE_row_raises_rather_than_losing"],
    },
    "M14-index-rider-removed": {
        "file": SCHEMA,
        "anchor": """    statements.append(\n        _plain_index(TASK_TABLE, f"{TASK_TABLE}_{_TASK_BLOCKED_BY_FIELD}", (f"{_TASK_BLOCKED_BY_FIELD}.*",))\n    )""",
        "replacement": "",
        "red": [
            f"{R}::TestTheBlockedByElementIndexServesContainment::test_the_task_ddl_emits_the_ELEMENT_PATH_index",
            f"{R}::TestTheBlockedByElementIndexServesContainment::test_CONTAINS_is_an_IndexScan_with_the_index_and_a_TableScan_without",
        ],
    },
}


def main(selected: list[str]) -> int:
    failures = []
    for name, spec in MUTATIONS.items():
        if selected and name.split("-")[0] not in selected:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            anchor = Path(tmp) / "anchor.txt"
            replacement = Path(tmp) / "replacement.txt"
            anchor.write_text(str(spec["anchor"]))
            replacement.write_text(str(spec["replacement"]))
            command = [
                "uv", "run", "python", "scripts/mutation_proof.py",
                "--file", str(spec["file"]),
                "--anchor-file", str(anchor),
                "--replacement-file", str(replacement),
            ]
            for node in spec["red"]:  # type: ignore[attr-defined]
                command += ["--expect-red", node]
            deselect = [arg for node in spec.get("deselect", []) for arg in ("--deselect", node)]  # type: ignore[attr-defined]
            command += ["--", "uv", "run", "pytest", "-n", "auto", "-q", "-p", "no:cacheprovider", *deselect, *SCOPE]
            print(f"\n===== {name} =====", flush=True)
            completed = subprocess.run(command, check=False, capture_output=True, text=True)
            tail = (completed.stdout + completed.stderr).strip().splitlines()[-14:]
            print("\n".join(tail), flush=True)
            print(f"===== {name}: exit {completed.returncode} =====", flush=True)
            if completed.returncode != 0:
                failures.append(name)
    print(f"\nFAILED PROOFS: {failures or 'none'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

## §RED — the declared RED set at HEAD (measured 2026-09-26 at `5d549a1`, in a CLEAN HEAD copy + exactly this commit's files)
`uv run pytest -n auto` over the three new files + every DUAL-edited file + the two secret-seam scans → **`68 failed, 734 passed, 1 skipped`**:
- **64 of the 86 new-file tests — every one a missing 58 mechanism.** Across all 68 REDs the one-line tracebacks classify 67 as 22 `AttributeError` (no `_guarded_append_fragment` / `max_reanchor_dependents` / `.reanchored` / `.reblocked` on a `str`), 36 `AssertionError` (no re-anchor / note / edge / heal / #130 exclusion; a superseded row served as claimable; the 4 DUAL pins' new world), 9 `Failed: DID NOT RAISE` (no atomic rollback to inject into; no cycle / R1 / hub refusal). Per class: `S` 44 · `G` 15 · `P` 5 (full per-class counts reproduced from `final_red_head.log`: TestTheHubBoundIsDERIVED 10 · TestTheSupersedeIsONETransaction 6 · TestRequiredGreen 6 · TestSharingIsProvenByMutationALWAYSTHROW 5 · TestEveryDependentFollowsTheWorkToTheSuccessor 4 · TestSupersedeOfATerminalPredecessorA1 4 · TestACycleClosingRewireIsRefusedWhole 3 · TestTheBootHealReanchorsStragglers 3 · TestTheShellIsTheSeam64aGoverns 3 · 2 each: TestASupersededRowIsInNeitherPartition, TestEachDependentCarriesTheReanchorNote, TestEachLedgerModuleHasExactlyONEGuardedAppendProducer, TestEverythingServedAsClaimableIsClaimableAndViceVersa, TestSharingIsProvenByMutationTHEAPPEND, TestTheRewireDedupes, TestTheSupersedeItselfIsUnchanged · 1 each: TestAConcurrentCreateIsRefusedNotStranded, TestASupersededRowMatchesNoStatusFilter, TestClaimWinGainsAnEventLossWritesNothing, TestParamNamesDoNotCollideAcrossComposedShells, TestTheBootBackfillAfterAReanchorIsANoOp, TestUpdatedAtIsStampedByTheShellForEveryCaller).
- **4 DUAL-edited existing pins, RED because their new world needs the build:** D1 `test_task_read_surface.py::…::test_superseding_a_task_with_dependents_NAMES_them_and_the_SUCCESSOR` (not re-anchored) · D10 `test_blocks_edge.py::TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask::test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED` (no heal) · D12 ×2 `scripts/test_forgery_door_sweep.py` (4 boot doors, the heal is the 5th).
- **GREEN at HEAD by design** (the other 22 new-file tests): negative controls, preserved-with-pin claim losses, the scanner discriminators, the #130 completeness/preserved legs, the 8-way claim race, the claim-LOUD pin (a rollback propagates today), the backfill no-op discriminators (docstring says why). Every other DUAL-edited existing pin (D2–D6, D8, D9, D11-held) is GREEN at HEAD — the both-worlds accessor / raw legacy seeds.
- **Typecheck residuals** (`attr-defined` on the three ruled symbols in `test_supersede_reanchor_58.py`): OWNED — `scripts/pending_contracts.yaml` bound `packet-58-contract` (self-destructs when the build lands the symbols).

## §GATES (this commit, measured in the clean HEAD copy `head58` = `5d549a1` + exactly the committed files)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → **typecheck `RED_ADJUDICATED` — 7 residuals owned by `packet-58-contract`; ruff `GREEN`**; pytest `NOT_RUN` (the brief forbids a bare `--currency`; the pytest leg is §RED + §SAT). In the SHARED tree the same check additionally shows peers' uncommitted residuals (§FLAGS 5) — not mine.
- `uv run python scripts/pending_contract_gate.py --verify-registry` → registry OK; self-destruct liveness: 1 import-checked absent · 2 UNCHECKED (owner `TaskLedger` attribute paths are not module-importable — the gate's own stated bound).
- `uv run ruff check` over every file I touched → `All checks passed!`.
- Probe: `uv run python scripts/probe_reanchor_58.py` → exit 0 (§1).
- Reference build (not committed): ruff repo-wide clean · `./scripts/typecheck.sh` all legs OK · full suite set-equal to the HEAD baseline (§SAT) · the final 58 + DUAL files `985 passed, 1 skipped, 0 failed`.

## §APPENDIX-REF — the reference build (the SAT + mutation instrument) — VERBATIM, NOT A SPEC
Built by the contract author ONLY to prove the contract satisfiable and to host the mutation proofs. **It is not the design and the builder should not copy it** — the rulings + this contract govern; several choices here (`namespace` param, `_supersede_fragments` helper, `overlay` on `_refuse_a_cycle`, `prefix` on `_relate_fragment`, the claim `_still_claimable` re-derivation, routing telemetry through `SurrealStore._log_transaction_size`) are one satisfying shape among several (BUILDER CONSTRAINTS say which properties are forced). Diff against `5d549a1`, post-lint; includes the out-of-set `esc1` one-liner (§FLAGS 1). `md5(tasks.py) = 2caca98b53813f0deb76211d3a3ed354`.

```diff
diff --git a/loremaster/loremaster/tasks.py b/loremaster/loremaster/tasks.py
index 8b2e01b..fd75eb0 100644
--- a/loremaster/loremaster/tasks.py
+++ b/loremaster/loremaster/tasks.py
@@ -99,6 +99,7 @@ from loremaster.agent_existence import (
 from loremaster.render import render_attributed
 from loremaster.store._txn import (
     _CONNECTION_ERRORS,
+    TXN_STATEMENT_HARD_CAP,
     SurrealConnectionError,
     SurrealStoreError,
     TxnContentionExhaustedError,
@@ -362,6 +363,19 @@ _RELATE_TO_PARAM_FMT = "rel{index}_to"
 # store itself). Both are WARNING because both name a pre-existing DATA defect an operator
 # can act on.
 _BACKFILL_PHANTOM_EVENT = "task.backfill.phantom_blocker_skipped"
+_HEAL_EVENT = "task.backfill.stragglers_reanchored"
+_HEAL_ACTOR = "boot-heal"
+_HEAL_REASON = "straggler"
+_ACTION_REANCHORED = "dependency_reanchored"
+_ACTION_CLAIM = "claim"
+_PROV_FROM = "from"
+_PROV_REASON = "reason"
+_REANCHOR_OLD_PARAM = "ra_old"
+_REANCHOR_NEW_PARAM = "ra_new"
+_REANCHOR_OLD_RECORD_PARAM = "ra_old_rec"
+_STRAGGLER_MESSAGE = "a dependent appeared while this supersede was being prepared"
+_REANCHOR_ALREADY_MESSAGE = "re-anchor matched zero rows"
+_CLAIM_ALREADY_MESSAGE = "claim lost the compare-and-set"
 _BACKFILL_CYCLE_EVENT = "task.backfill.legacy_cycle_minted"
 
 
@@ -492,6 +506,24 @@ class ClaimResult(BaseModel):
     superseded_blockers: dict[str, str] = Field(default_factory=dict)
 
 
+class SupersedeResult(BaseModel):
+    """The outcome of :meth:`TaskLedger.supersede_task` (packet 58).
+
+    Attributes:
+        successor_id: The freshly-minted successor's id.
+        reanchored: The dependents whose ``blocked_by`` named the predecessor and now name
+            the successor (the PRE-write list, sorted).
+        reblocked: The subset of ``reanchored`` that was CLAIMABLE before (open, unowned,
+            every other blocker terminal) and is blocked by the open successor after.
+    """
+
+    model_config = ConfigDict(extra="forbid")
+
+    successor_id: str
+    reanchored: list[str] = Field(default_factory=list)
+    reblocked: list[str] = Field(default_factory=list)
+
+
 class TaskLedgerError(RuntimeError):
     """Base class for every error :class:`TaskLedger` raises."""
 
@@ -521,6 +553,14 @@ class UnknownBlockerError(TaskLedgerError, UnknownRowError):
     """
 
 
+class TaskHubBoundError(TaskLedgerError):
+    """A supersede would re-anchor more dependents than one transaction can carry (58 F-1)."""
+
+
+class SupersedeRaceError(TaskLedgerError):
+    """A dependent appeared between the supersede's pre-read and its transaction (58 R1)."""
+
+
 class TaskCycleError(TaskLedgerError):
     """Raised when a requested write would put a task on a ``blocked_by`` CYCLE.
 
@@ -896,6 +936,7 @@ class TaskLedger:
         )
         logger.debug("task.schema.ready", extra={"database": self._database})
         await self._backfill_blocks_edges()
+        await self._reanchor_stragglers()
 
     async def _backfill_blocks_edges(self) -> None:
         """Mint the ``blocks`` edges the EXISTING ``blocked_by`` columns already imply.
@@ -1122,6 +1163,11 @@ class TaskLedger:
         both land or neither does, and two racers can never both win.
         """
         statement_text, merged_params = compose(*fragments)
+        from loremaster.store.surreal import SurrealStore  # noqa: PLC0415 - reuse the ONE telemetry policy
+
+        SurrealStore._log_transaction_size(  # noqa: SLF001
+            sum(len(fragment.statements) for fragment in fragments), len(merged_params)
+        )
         await execute_transaction(
             statement_text,
             merged_params,
@@ -1287,7 +1333,10 @@ class TaskLedger:
         """
         cap = self._validated_limit(limit)
         statement, params = self._candidate_statement(
-            status=status, owner=owner, limit=None if blocked is not None else cap
+            status=status,
+            owner=owner,
+            limit=None if blocked is not None else cap,
+            exclude_superseded=status is not None or blocked is not None,
         )
         fragments = [
             f"LET ${_QUERY_ROWS_VAR} = ({statement})",
@@ -1346,7 +1395,7 @@ class TaskLedger:
 
     @staticmethod
     def _candidate_statement(
-        *, status: str | None, owner: str | None, limit: int | None
+        *, status: str | None, owner: str | None, limit: int | None, exclude_superseded: bool = False
     ) -> tuple[str, dict[str, Any]]:
         """The candidate ``SELECT``: the caller's equality filters, pushed into the store.
 
@@ -1369,6 +1418,8 @@ class TaskLedger:
         if owner is not None:
             clauses.append(f"{_COL_OWNER} = ${_QUERY_OWNER_PARAM}")
             params[_QUERY_OWNER_PARAM] = owner
+        if exclude_superseded:
+            clauses.append(f"{_COL_SUPERSEDED_BY} IS NONE")
         statement = f"SELECT * FROM {TASK_TABLE}"
         if clauses:
             statement = f"{statement} WHERE {' AND '.join(clauses)}"
@@ -1489,7 +1540,20 @@ class TaskLedger:
             raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
         blocked_by = [str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())]
 
-        await self._apply([self._claim_fragment(task_id, owner, blocked_by)])
+        event = {
+            _PROV_ACTOR: owner,
+            _PROV_ACTION: _ACTION_CLAIM,
+            _PROV_AT: datetime.now(UTC).isoformat(),
+        }
+        try:
+            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
+        except (SurrealConnectionError, TxnContentionExhaustedError):
+            raise
+        except SurrealStoreError:
+            # The CAS matched zero rows — a LOSS — unless the row is STILL claimable, in which case
+            # the rollback came from something else and serving "not claimable" would be a false clear.
+            if await self._still_claimable(task_id, blocked_by):
+                raise
 
         # The winner is decided by OWNER IDENTITY ALONE on the post-CAS read:
         # ``owner`` is written solely by the guarded claim CAS (from ``NONE``,
@@ -1513,8 +1577,62 @@ class TaskLedger:
             claimed=won, task=updated, superseded_blockers=superseded_blockers
         )
 
+    async def _still_claimable(self, task_id: str, blocked_by: list[str]) -> bool:
+        row = await self._select_row(task_id)
+        if row is None or str(row.get(_COL_STATUS)) != STATUS_OPEN:
+            return False
+        if row.get(_COL_OWNER) is not None or row.get(_COL_SUPERSEDED_BY) is not None:
+            return False
+        current = [str(b) for b in (row.get(_COL_BLOCKED_BY) or ())]
+        if current != blocked_by:
+            return False
+        if not current:
+            return True
+        rows = self._as_rows(
+            await self._query(
+                f"SELECT {_ID_KEY}, {_COL_STATUS} FROM array::map($sc_ids, "
+                f"|$v| type::record('{TASK_TABLE}', $v))",
+                {"sc_ids": sorted(set(current))},
+            )
+        )
+        statuses = {self._bare_id(r.get(_ID_KEY)): str(r.get(_COL_STATUS)) for r in rows}
+        return all(statuses.get(b) in TERMINAL_STATUSES for b in current)
+
     @staticmethod
-    def _claim_fragment(task_id: str, owner: str, blocked_by: list[str]) -> TxnFragment:
+    def _guarded_append_fragment(
+        row_id: str,
+        *,
+        event: dict[str, Any] | None,
+        set_parts: Sequence[str] = (),
+        params: Mapping[str, Any],
+        where_conjuncts: Sequence[str] = (),
+        preamble: Sequence[str] = (),
+        throw_message: str,
+        namespace: str | None = None,
+    ) -> TxnFragment:
+        """The ONE task-side guarded, server-side-append CAS shell (packet 58)."""
+        namespace = namespace or f"ga{uuid4().hex[:12]}"
+        id_param = f"{namespace}_gid"
+        event_param = f"{namespace}_gev"
+        variable = f"{namespace}_ghit"
+        sets = [*set_parts, f"{_COL_UPDATED_AT} = time::now()"]
+        bound: dict[str, Any] = {**params, id_param: row_id}
+        if event is not None:
+            sets.append(f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${event_param}]")
+            bound[event_param] = event
+        where = " AND ".join(f"({conjunct})" for conjunct in where_conjuncts)
+        where_clause = f" WHERE {where}" if where else ""
+        guarded = (
+            f"LET ${variable} = (UPDATE type::record('{TASK_TABLE}', ${id_param}) SET "
+            f"{', '.join(sets)}{where_clause})"
+        )
+        guard = f"IF array::len(${variable}) == 0 {{ THROW '{throw_message}' }}"
+        return TxnFragment(statements=[*preamble, guarded, guard], params=bound)
+
+    @staticmethod
+    def _claim_fragment(
+        task_id: str, owner: str, blocked_by: list[str], event: dict[str, Any]
+    ) -> TxnFragment:
         """The atomic-claim fragment: LET-resolve blockers, then the guarded CAS.
 
         ``$clm_resolved`` binds the blocker record-ids that have reached a
@@ -1545,30 +1663,32 @@ class TaskLedger:
             f"WHERE record::id({_ID_KEY}) IN ${_CLAIM_BLOCKED_BY_PARAM} "
             f"AND {_COL_STATUS} IN ${_CLAIM_TERMINAL_PARAM})"
         )
-        guarded_claim = (
-            f"UPDATE type::record('{TASK_TABLE}', ${_CLAIM_ID_PARAM}) SET "
-            f"{_COL_OWNER} = ${_CLAIM_OWNER_PARAM}, "
-            f"{_COL_STATUS} = ${_CLAIM_CLAIMED_PARAM}, "
-            f"{_COL_CLAIMED_AT} = time::now(), "
-            f"{_COL_UPDATED_AT} = time::now() "
-            f"WHERE {_COL_STATUS} = ${_CLAIM_OPEN_PARAM} "
-            f"AND {_COL_OWNER} IS NONE "
-            f"AND {_COL_SUPERSEDED_BY} IS NONE "
-            f"AND array::len(array::distinct({_COL_BLOCKED_BY})) = "
-            f"array::len(${_CLAIM_RESOLVED_VAR})"
-        )
-        return TxnFragment(
-            statements=[resolve_blockers, guarded_claim],
+        return TaskLedger._guarded_append_fragment(
+            task_id,
+            event=event,
+            set_parts=[
+                f"{_COL_OWNER} = ${_CLAIM_OWNER_PARAM}",
+                f"{_COL_STATUS} = ${_CLAIM_CLAIMED_PARAM}",
+                f"{_COL_CLAIMED_AT} = time::now()",
+            ],
             params={
-                _CLAIM_ID_PARAM: task_id,
                 _CLAIM_OWNER_PARAM: owner,
                 _CLAIM_BLOCKED_BY_PARAM: blocked_by,
-                # Sorted so the bound list is deterministic; membership is
-                # order-insensitive regardless.
                 _CLAIM_TERMINAL_PARAM: sorted(TERMINAL_STATUSES),
                 _CLAIM_OPEN_PARAM: STATUS_OPEN,
                 _CLAIM_CLAIMED_PARAM: STATUS_CLAIMED,
             },
+            where_conjuncts=[
+                f"{_COL_STATUS} = ${_CLAIM_OPEN_PARAM}",
+                f"{_COL_OWNER} IS NONE",
+                f"{_COL_SUPERSEDED_BY} IS NONE",
+                # 58: blocked_by is MUTABLE (re-anchor) — decide on the column the pre-read saw.
+                f"{_COL_BLOCKED_BY} = ${_CLAIM_BLOCKED_BY_PARAM}",
+                f"array::len(array::distinct({_COL_BLOCKED_BY})) = array::len(${_CLAIM_RESOLVED_VAR})",
+            ],
+            preamble=[resolve_blockers],
+            throw_message=_CLAIM_ALREADY_MESSAGE,
+            namespace="clm",
         )
 
     # -- state machine ------------------------------------------------------
@@ -1740,21 +1860,12 @@ class TaskLedger:
         ``summary``/``report_path`` (PKT-06 §4(d) — atomic with the status
         flip, already validated by :meth:`_validate_done_summary`).
         """
-        set_parts = [
-            f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}",
-            f"{_COL_UPDATED_AT} = time::now()",
-            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_TRANSITION_EVENT_PARAM}]",
-        ]
+        set_parts = [f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}"]
         params: dict[str, Any] = {
-            _TRANSITION_ID_PARAM: task_id,
             _TRANSITION_STATUS_PARAM: target,
-            _TRANSITION_EVENT_PARAM: event,
             _TRANSITION_EXPECTED_FROM_PARAM: expected_from,
         }
         if release:
-            # The ONLY ways into ``open`` are creation and this release edge; a
-            # released task must be unowned/unclaimed for the claim CAS (which
-            # checks ``owner IS NONE`` alongside ``status = open``) to see it.
             set_parts.append(f"{_COL_OWNER} = NONE")
             set_parts.append(f"{_COL_CLAIMED_AT} = NONE")
         if target == STATUS_DONE:
@@ -1762,18 +1873,18 @@ class TaskLedger:
             set_parts.append(f"{_COL_REPORT_PATH} = ${_TRANSITION_REPORT_PATH_PARAM}")
             params[_TRANSITION_SUMMARY_PARAM] = summary
             params[_TRANSITION_REPORT_PATH_PARAM] = report_path
-        guarded_transition = (
-            f"LET ${_TRANSITION_UPDATED_VAR} = (UPDATE "
-            f"type::record('{TASK_TABLE}', ${_TRANSITION_ID_PARAM}) SET "
-            f"{', '.join(set_parts)} "
-            f"WHERE {_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM} "
-            f"AND {_COL_SUPERSEDED_BY} IS NONE)"
-        )
-        guard_updated = (
-            f"IF array::len(${_TRANSITION_UPDATED_VAR}) == 0 "
-            f"{{ THROW '{_TRANSITION_ALREADY_MESSAGE}' }}"
+        return TaskLedger._guarded_append_fragment(
+            task_id,
+            event=event,
+            set_parts=set_parts,
+            params=params,
+            where_conjuncts=[
+                f"{_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM}",
+                f"{_COL_SUPERSEDED_BY} IS NONE",
+            ],
+            throw_message=_TRANSITION_ALREADY_MESSAGE,
+            namespace="tr",
         )
-        return TxnFragment(statements=[guarded_transition, guard_updated], params=params)
 
     @staticmethod
     def _validate_done_summary(
@@ -1881,7 +1992,7 @@ class TaskLedger:
         description: str,
         created_by: str,
         blocked_by: list[str] | None = None,
-    ) -> str:
+    ) -> SupersedeResult:
         """Reframe a task: create a fresh open successor, stamp the old row.
 
         The successor CREATE and the old-row stamp ride ONE ``BEGIN … COMMIT``
@@ -1970,7 +2081,27 @@ class TaskLedger:
         # ONE implementation): a phantom/superseded blocker or a column cycle is refused
         # atomically before any write. Both short-circuit on empty deps (no wire cost).
         await self._reject_unusable_blockers([(entry, entry) for entry in dependencies])
-        await self._refuse_a_cycle({new_id: dependencies})
+        dependents = await self._dependent_rows(task_id)
+        cap = self.max_reanchor_dependents(len(dependencies))
+        if len(dependents) > cap:
+            raise TaskHubBoundError(
+                f"task {render_attributed(task_id)} has {len(dependents)} dependents; one supersede "
+                f"re-anchors at most {cap} dependents (the store's transaction bound, derived) — "
+                f"refused, nothing changed. This is a pinned KNOWN BOUND (packet 58 F-1); a hub "
+                f"this size is not expected in the fleet — file it, and the bound's re-open trigger "
+                f"is this refusal"
+            )
+        dependent_ids = [str(row[_ID_KEY]) for row in dependents]
+        rewired = {
+            str(row[_ID_KEY]): list(
+                dict.fromkeys(
+                    new_id if str(b) == task_id else str(b) for b in (row.get(_COL_BLOCKED_BY) or ())
+                )
+            )
+            for row in dependents
+        }
+        await self._refuse_a_cycle({new_id: dependencies}, overlay=rewired)
+        reblocked = await self._previously_claimable(row, dependents, task_id)
 
         now = datetime.now(UTC)
         content = self._new_task_content(subject, description, dependencies, created_by, now)
@@ -1985,13 +2116,17 @@ class TaskLedger:
             # ride ONE transaction: RELATE comes AFTER the CREATE so the ENFORCED ``out``
             # endpoint (the fresh successor) exists, and the loser of a raced supersede
             # rolls back the WHOLE txn (stamp + CREATE + RELATEs) — ZERO orphan edges.
+            note = {
+                _PROV_ACTOR: created_by,
+                _PROV_ACTION: _ACTION_REANCHORED,
+                _PROV_FROM: task_id,
+                _PROV_TO: new_id,
+                _PROV_AT: now.isoformat(),
+            }
             await self._apply(
-                [
-                    self._supersede_fragment(task_id, new_id, content, event),
-                    self._relate_fragment(
-                        [(blocker, new_id) for blocker in dependencies]
-                    ),
-                ]
+                self._supersede_fragments(
+                    task_id, new_id, content, event, dependencies, dependent_ids, note
+                )
             )
         except SurrealConnectionError:
             # A genuine transport fault — never a lost race; propagate untouched
@@ -2016,8 +2151,215 @@ class TaskLedger:
                     f"task {render_attributed(task_id)} is already superseded by "
                     f"{settled.get(_COL_SUPERSEDED_BY)!r} and cannot be superseded again"
                 ) from error
+            if sorted(await self.direct_dependents(task_id)) != sorted(dependent_ids):
+                raise SupersedeRaceError(
+                    f"a task blocked on {render_attributed(task_id)} was created while this "
+                    f"supersede was being prepared — nothing changed; retry the supersede"
+                ) from error
             raise
-        return new_id
+        return SupersedeResult(
+            successor_id=new_id, reanchored=sorted(dependent_ids), reblocked=sorted(reblocked)
+        )
+
+    @staticmethod
+    def _rewrite_set_part(old_param: str, new_param: str) -> str:
+        return (
+            f"{_COL_BLOCKED_BY} = array::distinct(array::map({_COL_BLOCKED_BY}, |$b| "
+            f"IF $b = ${old_param} THEN ${new_param} ELSE $b END))"
+        )
+
+    def _supersede_fragments(
+        self,
+        old_id: str,
+        new_id: str,
+        content: dict[str, Any],
+        event: dict[str, Any],
+        dependencies: Sequence[str],
+        dependent_ids: Sequence[str],
+        note: dict[str, Any],
+    ) -> list[TxnFragment]:
+        """The WHOLE supersede transaction — the ONE builder the send AND the cap count use."""
+        retire = TxnFragment(
+            statements=[f"DELETE {BLOCKS_RELATION} WHERE in = ${_REANCHOR_OLD_RECORD_PARAM}"],
+            params={
+                _REANCHOR_OLD_PARAM: old_id,
+                _REANCHOR_NEW_PARAM: new_id,
+                _REANCHOR_OLD_RECORD_PARAM: RecordID(TASK_TABLE, old_id),
+            },
+        )
+        rewires = [
+            TaskLedger._guarded_append_fragment(
+                dependent,
+                event=note,
+                set_parts=[self._rewrite_set_part(_REANCHOR_OLD_PARAM, _REANCHOR_NEW_PARAM)],
+                params={},
+                where_conjuncts=[f"{_COL_BLOCKED_BY} CONTAINS ${_REANCHOR_OLD_PARAM}"],
+                throw_message=_REANCHOR_ALREADY_MESSAGE,
+                namespace=f"ra{index}",
+            )
+            for index, dependent in enumerate(dependent_ids)
+        ]
+        closing = TxnFragment(
+            statements=[
+                f"IF (SELECT count() FROM {TASK_TABLE} WHERE {_COL_BLOCKED_BY} CONTAINS "
+                f"${_REANCHOR_OLD_PARAM} GROUP ALL)[0].count > 0 {{ THROW '{_STRAGGLER_MESSAGE}' }}"
+            ],
+            params={},
+        )
+        return [
+            self._supersede_fragment(old_id, new_id, content, event),
+            self._relate_fragment([(blocker, new_id) for blocker in dependencies]),
+            retire,
+            *rewires,
+            self._relate_fragment([(new_id, dependent) for dependent in dependent_ids], prefix="rar"),
+            closing,
+        ]
+
+    def max_reanchor_dependents(self, successor_blocked_by_count: int) -> int:
+        """The largest dependent count ONE supersede can re-anchor — DERIVED from the builder."""
+        dependencies = [f"cap-probe-b{index}" for index in range(successor_blocked_by_count)]
+
+        def _count(dependents: int) -> int:
+            fragments = self._supersede_fragments(
+                "cap-probe-old", "cap-probe-new", {}, {}, dependencies,
+                [f"cap-probe-d{index}" for index in range(dependents)], {},
+            )
+            return sum(len(fragment.statements) for fragment in fragments)
+
+        fixed = _count(0)
+        per = _count(1) - fixed
+        return (TXN_STATEMENT_HARD_CAP - fixed) // per
+
+    async def _dependent_rows(self, task_id: str) -> list[dict[str, Any]]:
+        rows = self._as_rows(
+            await self._query(
+                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_STATUS}, {_COL_OWNER}, "
+                f"{_COL_SUPERSEDED_BY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
+                f"WHERE {_COL_BLOCKED_BY} CONTAINS ${_DEPENDENTS_ID_PARAM}",
+                {_DEPENDENTS_ID_PARAM: task_id},
+            )
+        )
+        return sorted(rows, key=lambda row: str(row[_ID_KEY]))
+
+    async def _previously_claimable(
+        self, predecessor: Mapping[str, Any], dependents: Sequence[Mapping[str, Any]], old_id: str
+    ) -> list[str]:
+        if str(predecessor.get(_COL_STATUS)) not in TERMINAL_STATUSES:
+            return []
+        others = sorted(
+            {
+                str(b)
+                for row in dependents
+                for b in (row.get(_COL_BLOCKED_BY) or ())
+                if str(b) != old_id
+            }
+        )
+        status_by_id: dict[str, str] = {}
+        if others:
+            rows = self._as_rows(
+                await self._query(
+                    f"SELECT {_ID_KEY}, {_COL_STATUS} FROM array::map($pc_ids, "
+                    f"|$v| type::record('{TASK_TABLE}', $v))",
+                    {"pc_ids": others},
+                )
+            )
+            status_by_id = {self._bare_id(r.get(_ID_KEY)): str(r.get(_COL_STATUS)) for r in rows}
+        claimable: list[str] = []
+        for row in dependents:
+            if str(row.get(_COL_STATUS)) != STATUS_OPEN or row.get(_COL_OWNER) is not None:
+                continue
+            if row.get(_COL_SUPERSEDED_BY) is not None:
+                continue
+            blockers = [str(b) for b in (row.get(_COL_BLOCKED_BY) or ()) if str(b) != old_id]
+            if all(status_by_id.get(b) in TERMINAL_STATUSES for b in blockers):
+                claimable.append(str(row[_ID_KEY]))
+        return claimable
+
+    async def _reanchor_stragglers(self) -> None:
+        """Amendment 1 R2: heal every row still naming a superseded task, to its chain HEAD."""
+        superseded = self._as_rows(
+            await self._query(
+                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} "
+                f"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE"
+            )
+        )
+        if not superseded:
+            return
+        successor = {str(r[_ID_KEY]): str(r[_COL_SUPERSEDED_BY]) for r in superseded}
+
+        def _head(task_id: str) -> str:
+            seen: set[str] = set()
+            while task_id in successor and task_id not in seen:
+                seen.add(task_id)
+                task_id = successor[task_id]
+            return task_id
+
+        stragglers = self._as_rows(
+            await self._query(
+                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
+                f"WHERE {_COL_BLOCKED_BY} CONTAINSANY $hs_ids",
+                {"hs_ids": sorted(successor)},
+            )
+        )
+        if not stragglers:
+            return
+        heads = sorted({_head(old) for old in successor})
+        existing = await resolve_existing_rows(self._query, TASK_TABLE, heads)
+        now = datetime.now(UTC).isoformat()
+        olds: dict[str, int] = {}
+        fragments: list[TxnFragment] = []
+        rewrites: list[TxnFragment] = []
+        relates: list[tuple[str, str]] = []
+        healed: set[str] = set()
+        for row in sorted(stragglers, key=lambda r: str(r[_ID_KEY])):
+            straggler = str(row[_ID_KEY])
+            present = {str(b) for b in (row.get(_COL_BLOCKED_BY) or ())}
+            for old in dict.fromkeys(str(b) for b in (row.get(_COL_BLOCKED_BY) or ())):
+                if old not in successor:
+                    continue
+                head = _head(old)
+                if head not in existing:
+                    continue
+                if old not in olds:
+                    index = len(olds)
+                    olds[old] = index
+                    fragments.append(
+                        TxnFragment(
+                            statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $hs{index}_rec"],
+                            params={
+                                f"hs{index}_old": old,
+                                f"hs{index}_new": head,
+                                f"hs{index}_rec": RecordID(TASK_TABLE, old),
+                            },
+                        )
+                    )
+                index = olds[old]
+                rewrites.append(
+                    TaskLedger._guarded_append_fragment(
+                        straggler,
+                        event={
+                            _PROV_ACTOR: _HEAL_ACTOR,
+                            _PROV_ACTION: _ACTION_REANCHORED,
+                            _PROV_FROM: old,
+                            _PROV_TO: head,
+                            _PROV_AT: now,
+                            _PROV_REASON: _HEAL_REASON,
+                        },
+                        set_parts=[self._rewrite_set_part(f"hs{index}_old", f"hs{index}_new")],
+                        params={},
+                        where_conjuncts=[f"{_COL_BLOCKED_BY} CONTAINS $hs{index}_old"],
+                        throw_message=_REANCHOR_ALREADY_MESSAGE,
+                        namespace=f"hr{len(rewrites)}",
+                    )
+                )
+                if head not in present:
+                    relates.append((head, straggler))
+                    present.add(head)
+                healed.add(straggler)
+        if not healed:
+            return
+        await self._apply([*fragments, *rewrites, self._relate_fragment(relates, prefix="hrel")])
+        logger.info(_HEAL_EVENT, extra={"database": self._database, "count": len(healed)})
 
     @staticmethod
     def _supersede_fragment(
@@ -2044,29 +2386,25 @@ class TaskLedger:
         ``IllegalTransitionError``) + ZERO orphan rows — the CREATE can never
         outlive a stamp that did not land.
         """
-        stamp_old = (
-            f"LET ${_SUPERSEDE_STAMPED_VAR} = (UPDATE "
-            f"type::record('{TASK_TABLE}', ${_SUPERSEDE_OLD_ID_PARAM}) SET "
-            f"{_COL_SUPERSEDED_BY} = ${_SUPERSEDE_NEW_ID_PARAM}, "
-            f"{_COL_UPDATED_AT} = time::now(), "
-            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_SUPERSEDE_EVENT_PARAM}] "
-            f"WHERE {_COL_SUPERSEDED_BY} IS NONE)"
-        )
-        guard_stamped = (
-            f"IF array::len(${_SUPERSEDE_STAMPED_VAR}) == 0 "
-            f"{{ THROW '{_SUPERSEDE_ALREADY_MESSAGE}' }}"
+        stamp = TaskLedger._guarded_append_fragment(
+            old_id,
+            event=event,
+            set_parts=[f"{_COL_SUPERSEDED_BY} = ${_SUPERSEDE_NEW_ID_PARAM}"],
+            params={},
+            where_conjuncts=[f"{_COL_SUPERSEDED_BY} IS NONE"],
+            throw_message=_SUPERSEDE_ALREADY_MESSAGE,
+            namespace="sup",
         )
         create_successor = (
             f"CREATE type::record('{TASK_TABLE}', ${_SUPERSEDE_NEW_ID_PARAM}) "
             f"CONTENT ${_SUPERSEDE_CONTENT_PARAM}"
         )
         return TxnFragment(
-            statements=[stamp_old, guard_stamped, create_successor],
+            statements=[*stamp.statements, create_successor],
             params={
+                **stamp.params,
                 _SUPERSEDE_NEW_ID_PARAM: new_id,
                 _SUPERSEDE_CONTENT_PARAM: content,
-                _SUPERSEDE_OLD_ID_PARAM: old_id,
-                _SUPERSEDE_EVENT_PARAM: event,
             },
         )
 
@@ -2244,7 +2582,7 @@ class TaskLedger:
         )
 
     @staticmethod
-    def _relate_fragment(pairs: Sequence[tuple[str, str]]) -> TxnFragment:
+    def _relate_fragment(pairs: Sequence[tuple[str, str]], *, prefix: str = "rel") -> TxnFragment:
         """The ``blocks`` mirror: one ``RELATE`` per ``(blocker, blocked task)`` pair.
 
         Direction is escalation **E-1**'s — ``RELATE $blocker->blocks->$task``, so ``in``
@@ -2260,8 +2598,8 @@ class TaskLedger:
         statements: list[str] = []
         params: dict[str, Any] = {}
         for index, (blocker, blocked) in enumerate(pairs):
-            from_param = _RELATE_FROM_PARAM_FMT.format(index=index)
-            to_param = _RELATE_TO_PARAM_FMT.format(index=index)
+            from_param = f"{prefix}{index}_from"
+            to_param = f"{prefix}{index}_to"
             statements.append(
                 f"RELATE ${from_param}->{BLOCKS_RELATION}->${to_param}"
             )
@@ -2321,7 +2659,11 @@ class TaskLedger:
                 f"id — the ids may be perfectly good; retry, and escalate if it persists"
             ) from error
 
-    async def _refuse_a_cycle(self, pending: Mapping[str, Sequence[str]]) -> None:
+    async def _refuse_a_cycle(
+        self,
+        pending: Mapping[str, Sequence[str]],
+        overlay: Mapping[str, Sequence[str]] | None = None,
+    ) -> None:
         """Refuse a write that would put one of ``pending``'s tasks on a ``blocked_by`` cycle.
 
         ⚠⚠ **THE WALK IS OVER THE ``blocked_by`` COLUMN, CLIENT-SIDE, AND IT CANNOT BE THE
@@ -2362,6 +2704,8 @@ class TaskLedger:
             node: set(refs)
             for node, refs in (await self._bounded_dependency_graph(seeds)).items()
         }
+        for node, refs in (overlay or {}).items():
+            graph[node] = set(refs)
         for task_id, blockers in pending.items():
             graph[task_id] = set(blockers)
         minted = set(pending)
diff --git a/scripts/esc1_write_path_cycle_closure.py b/scripts/esc1_write_path_cycle_closure.py
index 94d3514..517967c 100644
--- a/scripts/esc1_write_path_cycle_closure.py
+++ b/scripts/esc1_write_path_cycle_closure.py
@@ -416,10 +416,10 @@ async def legacy_continuum() -> None:  # noqa: PLR0915 - a linear construction+m
         await closure_leg(connection, ledger, m3, "boundary-4 POST create_many (deep B*)")
 
         # -- construction 2c: supersede_task on a task WITH dependents -------
-        d_successor = await ledger.supersede_task(
+        d_successor = (await ledger.supersede_task(
             "leg_d", subject="D2", description="successor of leg_d",
             created_by="probe-esc1-closure-1",
-        )
+        )).successor_id
         await diff_boundary(connection, "boundary-5 supersede leg_d")
         await closure_leg(connection, ledger, "leg_e", "boundary-5 dependent of superseded")
         await closure_leg(connection, ledger, task_f, "boundary-5 dependent of superseded")
```

## §BASE — which tree every number describes
All measurements: `5d549a1` (+ this commit's files). HEAD at commit time: `80409f4` (1 commit ahead: `scripts/restore_prod_dump.py`, `scripts/test_restore_prod_dump.py`, `REPORT-probe-64.md` — disjoint from `tasks.py`, `server.py`, the schema and every file this contract touches; derived by `git diff --stat 5d549a1 80409f4`). No number here was re-measured at `80409f4`.
