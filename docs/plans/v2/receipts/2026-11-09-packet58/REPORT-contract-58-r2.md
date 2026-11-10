brief-base v16 read · brief project v7 read

# REPORT — contract-58-r2 (packet 58 contract revision: adversary-58 MP1–MP18 + SD1–SD3 + amendments 2/3)

## SUMMARY BLOCK
- **State: done-with-deviations** — contract r2 committed (tests only): adversary-58's MP1–MP18 + SD1–SD3 + amendments 2/3/4/5 landed; 24 of the adversary's 25 graded probes AST-EQUAL (PR18 re-keyed per am-3 §1 ERRATUM); 49 declared wrong builds, **0 survive** (45 exact/included + 1 hang as declared + 3 mismatches individually adjudicated, §MUTATION); SAT on plain HEAD + §HELD + reference: `2 failed, 11859 passed` → both reds one ruling-vs-pin collision fixed by §HELD part 3 (`8 passed` both sides) ⇒ 0 attributable; lint 0; RED@HEAD 119, all right-reason and OWNED (`packet-58-contract`).
- Deviations: D-FORK2 (Reading A pursued ~40 min, REJECTED by am-5, fully undone before commit) · D-RSHELD (`test_retry_seam.py` re-key → §HELD per lead #17066) · D-PR18/D-HEALBUILDS/D-PR5 (re-keyed or re-expressed, kills re-proven) · D-PAD (`RETURN` truncates a transaction — finding #497) · D-BASE (plain HEAD per #17055) · D-LANE (lane lifted mid-run by #17068; two disclosed slips).
- Packages considered: `ast` (stdlib) for every scan; no library provides the heal packer (arithmetic over `compose`'s own count) or the injection harness — bespoke test instruments only, each reusing an in-house seam (§DRY LEDGER).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 8 ledger rows (new test-support symbols + 2 reuses), all dispositioned (§DRY LEDGER — queries run post-hoc, stated).
- Graded: n/a (a contract, not a verdict) — measured against HEAD `43b8d16`; committed on `99dbe49` (docs + a28 contract since — no 58 file moved); §HELD `git apply --check` clean on the shared tree at `99dbe49`.
- Decisions needed: FORK-3 (is an ASSERT/coercion rollback ERROR or WARNING? — unpinned; and am-3 §3's WARNING reaches 63's governed-conflict THROW — my reading yes, §HELD part 3) · FORK-4 (`[A,A,X]` dedupe scope, unpinned) · F-r2-2 (64b × the (C) registry + the §HELD `test_retry_seam` re-key collide — sequencing) · F-r2-9 (the sweep's mypy-clean pin RED until build, a cost of #17055's per-file ownership).
- Receipts: forks §FORKS · required-green §REQUIRED-GREEN · per-item §ITEMS · AST §AST · deviations §DEVIATIONS · reach §P1c · DUAL §DUAL · builder constraints §BUILDER CONSTRAINTS · held §HELD · flags §FLAGS · DRY §DRY LEDGER · mutations §MUTATION · RED@HEAD §RED@HEAD · SAT §SAT · currency §CURRENCY · reference §REFERENCE · instruments §INSTRUMENTS.
- Findings filed: #494 (enumerator helper-indirect bound — now moot for the door test, kept for the record) · #497 (store ref: RETURN inside a transaction).

## §0 Capability check (brief-base §4)
- Idle-gate contract: `/tmp/claude-idle-gate-lore/051e3520-9705-4d88-80c5-a1b8b25785f7-contract-58-r2.contract` = `{"artifact": "REPORT-contract-58-r2.md"}`.
- lore reachable; registered `contract-58-r2` (session `63c-20260924`, cadence ≤20m, spawned_by lead-63c-2).
- grep/rg hook-blocked (#473): every textual sweep below is `awk`/`sed` — a fallback, said out loud.
- Required first read done: `docs/reference/surrealdb-31-capabilities.md` (whole file).
- Adversary instruments extracted VERBATIM from `9f2f580:REPORT-adversary-58.md` §INSTRUMENTS; md5 of each extraction equals the md5 the adversary recorded: `build_ref58.py 5915c12e` · `wrong_builds.py 790e0309` · `am2_builds.py 0bf51844` · `test_adversary58_probes.py 2cf0d5f4` · `batch2 1328e035` · `batch3 cdb99104` — so every kill below is re-proven against the adversary's OWN wrong builds, not paraphrases.

## §FORKS — surfaced (brief: write it FIRST, one message, continue on unaffected work)

### FORK-1 — SD3 (`_GUARDED_CAS_DOORS` gains `tasks.py::claim_task`) contradicts decision 3 (claim catches the TYPE)
- **Fact (read, `test_retry_seam._discover_guarded_cas_handlers`):** a door is an `except SurrealStoreError` handler (matched by `ast.Name` id) whose body calls a `_select*` method. A handler of type `TxnClaimLostError` is NOT matched.
- **Amendment 3 §3 (decision 3):** `claim_task` "catches the TYPE (`TxnClaimLostError`), never the text, and runs its post-CAS owner read as today". Under that design the loss is caught by type, every OTHER rollback propagates (loud — B6-sub holds with no re-read), so `claim_task` has **no** `except SurrealStoreError` re-read handler ⇒ it is **not a door** ⇒ an exact-set canonical entry `tasks.py::claim_task` REDS every build that follows decision 3 literally.
- **Amendment 3 §6 SD3:** "`_GUARDED_CAS_DOORS` gains `tasks.py::claim_task` … (the door is NEW: claim's rollback handler now re-reads state)" — written against the adversary's reference, whose claim caught `SurrealStoreError` and re-read (`_still_claimable`), i.e. the pre-decision-3 shape.
- **Reading A (my pick):** decision 3 governs the mechanism; SD3's premise ("claim's rollback handler re-reads") is false for the ruled mechanism. The canonical set stays UNCHANGED, and the exact-set pin then *enforces* the typed catch (a build that falls back to a broad `except SurrealStoreError` + re-read reds `test_the_door_enumeration_matches_the_canonical_set` — the pin becomes the "catches the TYPE" guard for free). Plus a behavioural pin: a claim loss re-typed as a plain `TxnDomainRejectionError` must make `claim_task` RAISE, not serve a loss (a text-matching ledger would still serve a loss).
- **Reading B:** add the entry per SD3's letter — forces every builder to keep a (purposeless) `except SurrealStoreError` + `_select*` handler beside the typed catch.
- **Status:** proceeding on A; one message sent to the lead; will switch to B if ruled before commit.
- **RULED 2026-09-26 by amendment 4 (`fd6497d`, sidecar-64): Reading A.** `_GUARDED_CAS_DOORS` stays at five; SD3 withdrawn; the enumerator WIDENS (typed + tuple catches, partitioned by hierarchy into doors vs a new exact set `_TYPED_CAS_CATCHES = {tasks.py::claim_task}`); behavioural + hierarchy pins. Landed in `test_retry_seam.py` (§DUAL D15).

### FORK-2 — amendment 4's `claim_task ∈ _TYPED_CAS_CATCHES` requires the typed loss handler to RE-READ inline (a shape the rulings do not otherwise demand)
- **Fact (measured, widened scan over HEAD `8c1c1a0` and over my reference):** the widened enumeration (am-4: "every `except <Name>` / tuple handler **whose body re-reads (`_select*` inline)**") finds exactly the five SurrealStoreError doors on both trees. A decision-3 claim written the way am-3 §3 words it — `except TxnClaimLostError: pass`, then "runs its post-CAS owner read **as today**" (`_get_or_raise`, AFTER the `try`) — has NO re-reading handler, so it is invisible to the enumerator and `_TYPED_CAS_CATCHES = {claim_task}` REDS it (and am-4's own non-vacuity rule, "both sets non-empty", cannot be met by any build of that shape).
- **Reading A (my pick, pinned):** am-4's letter governs — the typed loss handler re-reads inline (e.g. `except TxnClaimLostError: if await self._select_row(task_id) is None: raise`), which makes the reviewer-visible list non-vacuous and keeps a future re-parenting of `TxnClaimLostError` under a contention-bearing base a DERIVED door. Recorded as BUILDER CONSTRAINT BC-r2-3; the reference build takes this shape.
- **Reading B:** the enumeration also counts a typed handler that SWALLOWS (no re-raise) with no inline re-read (a "reinterpretation point"), leaving the owner read after the `try`. Changes the enumerator's property (a swallow, not a re-read) and would enumerate non-CAS swallowing handlers package-wide (not measured).
- **Status:** proceeding on A; one message to the lead.
- **RULED 2026-09-26 by amendment 5 (`67bf2cc`): Reading A REJECTED; C + B.** Lead STOP #17065 drained ~40 min into Reading A; everything A-shaped was undone before any commit (§DEVIATIONS D-FORK2). (C) = the runtime ∀ (`test_reanchor_58_r2_cas_runtime.py`); (B) = the class-keyed static index (`test_retry_seam.py` re-key — HELD-patch class per lead #17066, so it is in §HELD, not this commit).

### FORK-3 — amendment 3 §3's "ERROR stays for engine faults": is an ASSERT/coercion rollback an "engine fault" (ERROR) or a domain rejection (WARNING)?
- Pinned only the unambiguous legs: a claim loss logs at DEBUG (8-way, 0 WARNING/ERROR); a lost TRANSITION race (a THROW) logs exactly `[WARNING]`. NOT pinned either way: an `ASSERT`/coercion-rooted rollback. My reference keys WARNING on the engine's THROW prefix (`An error occurred:`, PROBED 3.2.4 this session) and leaves ASSERT/coercion at ERROR. Low; for the lead/sidecar.

### FORK-4 — kickoff §1 vs §6 on `[A, A, X]` (adversary E11)
- §1 prescribes `array::distinct(array::map(…))` over the WHOLE column (collapses the legacy duplicate of A); §6's fixture text says "only the X entry rewritten". Not pinned either way (§DUAL E11). Low.

## §REQUIRED-GREEN — correct builds the rulings require green (enumerated FIRST — adversary §SAT's list, then r2's additions)
All measured GREEN on the r2 reference (§SAT) — none is in the reference's red set:
1. **05b / #174 successor sentinel** inherit / `[]` / `[ids]` — `test_blocks_edge.py::TestSupersedeCarriesBlockedBy174`, `S::TestRequiredGreen::test_the_174_*`.
2. **The claim CAS** (exactly one winner, owner-identity readback) — `test_task_ledger.py` race suites, `G::TestTheClaimCASStillDecidesOnlyOnce` (8-way), and r2's `RU::TestAClaimLossIsDEBUGNeverAnAlarm::test_an_8_way_race_…` (one winner is asserted there too).
3. **`transitive_blockers`** — `test_blocks_edge.py` sections F/K, `test_task_read_surface.py`.
4. **The findings ledger's `_guarded_append_fragment`** — `test_findings*.py` + `G::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer` (findings stays at one producer UNDER THE WIDENED SCAN — module constants referenced by a findings function now count; measured still one).
5. **57's future consumer shape** — `G::TestTheShellIsTheSeam64aGoverns` (kw-only signature) — no 57 test exists (bound).
6. **r2 additions:** a correct packer that fits 4999 statements in ONE chunk (AM2C — `PR18r2` keyed to the packer's own prediction, never `chunks == 2`); a correct build that derives the F-1 cap by BUILDING real fragments (SD1 — the r2 `G_PARAM` counts shell outputs that REACHED `compose`); the ruled order backfill → heal (SD2 — D12 + `RU_ORDER` + the armed-door pin all require it); `claim_task` NOT a door (am-4 — `_GUARDED_CAS_DOORS` unchanged); every other THROW rollback at WARNING, the claim loss at DEBUG (am-3 §3); a size WARN from a legitimately large heal chunk (am-2 (b): "that is the WARN doing its job") — the six-blocker pin EXCLUDES `statement_count`-carrying records from its "no warning" leg for exactly this reason (first run: a correct 5004-statement… chunk logged `store.apply.large_transaction`, a false red on my own pin — fixed before any grading run).

## §ITEMS — per adversary item / SAT defect / amendment clause (pin · wrong build killed · receipt)
Files: `S` = `test_supersede_reanchor_58.py` · `G` = `test_task_guarded_shell_58.py` · `P` = `test_task_claimable_partition_58.py` · `PRB` = `test_reanchor_58_r2_probes.py` · `SC` = `test_reanchor_58_r2_scale.py` · `A2` = `test_reanchor_58_r2_am2.py` · `RU` = `test_reanchor_58_r2_rulings.py` · `D` = `scripts/test_forgery_door_sweep.py` · `RS` = `test_retry_seam.py`. Receipt column = the wrong-build driver line (§MUTATION) — every build there is the adversary's own (`wrong_builds.py` md5 `790e0309`) where its anchor still applies, else re-expressed (`…r`, §DEVIATIONS).

| item | pin | wrong build killed | receipt |
|---|---|---|---|
| MP1 (E5) supersede fault laundered as R1 | `PRB::test_PR1_…` (AST-equal) | WB1 | §MUTATION WB1 exact |
| MP2 K-blind cap | `PRB::test_PR2_…` + `RU::TestTheHubCapFollowsKAcrossFloorBoundaries[0,1,2,3,per,per+1]` (am-3 §1 iv: accessor == composed cap at each K; cap succeeds; cap+1 teaches, byte-inert) + `SC::test_PR16_…` (the harm) | WB2 (WB2a control: 0 reds) | WB2 exact (5 reds: PR2, PR16, K∈{3,per,per+1}) |
| MP3 heal counts pairs / first blocker only | `PRB::test_PR3_…` | WB3r, WB4r | exact |
| MP4 doubled heal edge | `PRB::test_PR4_…` | WB5r | exact |
| MP5 phantom head (am-3 §5) | `PRB::test_PR5_…` (boot survives) + `RU::TestAPhantomChainHeadIsSkippedAndRECORDED` (skipped, byte-identical, ONE WARNING naming task_id/blocker_id/phantom_head_id, count==1, re-recorded next boot, hand-fix CONTROL heals) | WB6r | exact (PR5 stays GREEN on WB6r — under am-3 the chunk's ENFORCED rejection is isolated, so only the RU pin sees it; §DEVIATIONS D-PR5) |
| MP6 #130 under LIMIT | `PRB::test_PR6_…` | WB7 | exact |
| MP7 wontfix reblocked | `PRB::test_PR7_…` | WB8 | exact |
| MP8 legacy loop (am-3 §4) | `PRB::test_PR8_…` + `RU::TestOnlyACycleThroughXPrimeIsRefused` (loop member untouched; CONTROLS: explicit `X'←Y` refused whole; INHERITED loop through X' refused whole) | WB9 (over-refusal); K4 (under-refusal: both controls red) | exact |
| MP9 scanner reach | `PRB::test_PR9_…` (AST-equal; GREEN because G's scanner now pools referenced module constants — §DUAL D13) + `RU::TestEveryComposedGuardedWriteCameFromTheShell` (RUNTIME: every composed UPDATE/UPSERT came from the shell; reach = AST-derived `_apply` callers ⊆ observed) | WB12r (AST legs), K7r (runtime leg + 8 others) | exact |
| MP10 WARN policy shared | `PRB::test_PR13_…` | WB14 | exact |
| MP11 shared hard cap | `PRB::test_PR14_…` | WB15 | exact |
| MP12 note `at` | `PRB::test_PR12_…` | WB16 | exact |
| MP13 hand-rolled RELATE (D9 over-claim) | `RU::TestEveryRELATEComesFromTheSharedFragment` (compose ∩ `_relate_fragment` spy) | K16 | exact |
| MP14 claim-loss ERROR (am-3 §3) | `PRB::test_PR10_…` + `RU::TestAClaimLossIsDEBUGNeverAnAlarm` (8-way: 0 WARNING/ERROR, exactly 7 DEBUG rollbacks; CONTROL transition lost race == [WARNING]; typed-catch behavioural; one-literal AST pin) | CL1, CL2, CL3, CL4 | exact |
| MP15 am-2 (a) owner= | `A2::test_PR20_…` + `RU::TestAHeldSupersededRowUnderOwnerQueries` (blocked=False excludes, get decorated, holder's transition refused naming the successor) | WB18 | exact |
| MP16 heal chunking (am-3 §1) | `A2::test_PR18r2_…` (re-keyed) · `A2::test_PR19_…` · `SC::test_PR17_…` · `RU::…SIX_blockers…` (cap+1 over 6 blockers, one boot, every chunk ≤ cap, `chunks` == composed heal txns, second boot silent) · `RU::…MUTATION_padding…` (pad the shell → accessor AND packer move) | AM2L (am-2's literal sizing) | exact |
| MP17 fake lockstep | `RU::TestTheFakeReanchorsInLockstepWithTheReal[fake,real]` | FAKE (loop removed) | exact |
| MP18 superseded_by loop | `PRB::test_PR15_…` (bounded) + `RU::TestASupersededByCycleIsBoundedAndRECORDED` (recorded `straggler_chain_cycle` each boot, NO write/note) | WB17r (hang), WB17b (cycle treated as a head), K10 | WB17r HANG; others exact |
| SD1 over-tight shell count | `G::TestParamNamesDoNotCollideAcrossComposedShells` re-keyed to shell outputs REACHING `compose` (§DUAL D14) | K7r reds it (no marked reanchor event reaches compose) | exact |
| SD2 unruled heal order | D12 prose now cites am-3 §2 (§DUAL D12) + `RU::…READS_what_the_backfill_minted…` + the armed-door pin | K17r (4 reds incl. D's SWALLOW leg) | exact |
| SD3 → am-4 → **am-5 (C)** runtime ∀ | `CR = test_reanchor_58_r2_cas_runtime.py`: `TestTheDrivenSetIsTheDerivedSet` (driver registry == `derive_cas_verbs`, both ways) + `TestExhaustedContentionPropagatesUNREADFromEveryCASVerb[7 verbs]` (injection → typed error unchanged, ONE seam call, ZERO reads after; CONTROL: a REAL lost race → the verb's ruled verdict) | TRNOGUARD, CLDOOR5b, STALE (a new shell verb, undriven), FO1/FO2 (heal) | §MUTATION |
| am-5 (B) class-keyed index — **§HELD** (lead #17066: `test_retry_seam.py` is held-patch class) | `RS._classify_cas_handlers` (every non-pass-through clause of a derived CAS verb, incl. bare/tuple; names resolved; door iff closure ∋ TxnContentionExhaustedError) + `_TYPED_CAS_CATCHES` {claim_task, _reanchor_stragglers} + `TestTheClassKeyedIndexPartitionsEveryCASHandler` (exact typed set, non-vacuity, 5 discriminators, unresolvable → loud, out-of-scope → nothing) | CLDOOR5, CLDOOR5b, CL3, CLREPARENT, TRNOGUARD | §MUTATION (run on the SAT tree, §HELD applied) |
| am-5 §3 cross-check (B)×(C) | `CR::TestTheRuntimeSetAndTheStaticIndexAgree` (listed ⊆ driven; driven ⊆ classified) | STALE reds CR_DRIVEN (reach), CLREPARENT/CLDOOR5 red (B) while (C) stays green — the two layers see different things, exactly why both exist | §MUTATION |
| am-4 hierarchy (kept by am-5) | `RU::TestTheClaimLostHierarchy` | CLREPARENT | exact |
| am-3 §2 store fault LOUD | `RU::TestAHealStoreFaultIsLOUD::test_every_heal_door_after_the_backfill_RAISES[store,transport]` (doors DERIVED by faulting k = 1… until a boot completes; each faulted boot writes nothing) + D's UNEDITED loudness assertions | FO1 (fail-open apply), FO2 (am-2's over-broad fail-open) | exact |
| am-3 §2 domain rejection isolated | `RU::…DOMAIN_rejection_is_isolated_WARNED_and_healed_next_boot` (population = measured chunk + 1; ONE WARNING naming the chunk's rows; other chunk heals; next boot heals the rest) | K11r (count) — and FO-inverse is FO1 | exact |
| index rider (am-1) on production statements (adversary R6) | `PRB::test_PR11_…` ×3 | IDX (rider removed) | exact |

## §AST — the landed probes are AST-EQUAL to the adversary's (am-17's rule), with controls
Instrument `ast_receipt.py` — pasted VERBATIM in §INSTRUMENTS. Run 2026-09-26 against the extracted adversary files (md5-verified, §0):
```
EQUAL x24   (test_reanchor_58_r2_probes.py: _boot, _chain, _seed_chain, PR1..PR15;
             test_reanchor_58_r2_scale.py: PR16, PR17; test_reanchor_58_r2_am2.py: _boot, _stragglers, PR19, PR20)
MISSING x1  test_reanchor_58_r2_am2.py::test_PR18_am2_ruled_shape_cap_plus_one_of_ONE_blocker_heals_in_two_chunks
            — deliberate: re-keyed as test_PR18r2_… (§DEVIATIONS D-PR18)
controls OK: re-wrap EQUAL (_boot); one-token mutation DIFFERENT (test_PR1_…)
```
Only the import blocks differ (unused names dropped; `Any` added where the adversary's file imported it). Positive control: a single `assert` → `assert not` edit compares DIFFERENT (the comparator sees a one-token change). Negative control: an inserted comment compares EQUAL (formatting is admitted).

## §DEVIATIONS (each with its kill re-proven)
- **D-PR18** — `test_PR18_am2_…` NOT landed; amendment 3 §1 ERRATUM retires its `chunks == 2` literal. Re-keyed `A2::test_PR18r2_…`: `chunks` must equal the chunk count a greedy packer needs for the MEASURED heal shape (`measure_heal_shape`: 1/2/3 stragglers, compose-spied, linearity-checked). Kill re-proven: AM2L (am-2's supersede-sized chunks) → RED; the correct packer → GREEN (AM2C's world).
- **D-HEALBUILDS** — the adversary's heal wrong builds (WB3/4/5/6/17, K7/9/11/17) do not anchor on amendment 3's heal (my reference's heal is a packer, not the single transaction they were written against). Re-expressed as `WB3r/WB4r/WB5r/WB6r/WB17r/WB17b/K7r/K9r/K11r/K17r` over the SAME behaviour each named (§INSTRUMENTS `wb58r2.py` carries the exact edits). Every one re-proven exact (§MUTATION).
- **D-PR5** — PR5 lands AST-equal but is no longer a sufficient pin for MP5: under am-3's domain-rejection isolation a phantom-RELATE chunk rolls back quietly, so PR5 (boot survives + column unchanged) is GREEN on WB6r. The am-3 §5 pin `RU::TestAPhantomChainHeadIsSkippedAndRECORDED` is the discriminator (RED on WB6r).
- **D-PAD** — the r1 in-suite padding mutation appends `RETURN NONE`. MEASURED (3.2.4, this session): a `RETURN` inside the composed `BEGIN…COMMIT` ends the transaction's work early — the heal's rows silently stay stranded and the NEXT boot heals them (first reading `c = [5, 9, 18]`, non-linear). r2's padding uses `LET $pad58r2 = NONE`. The r1 pin (`S::TestTheHubBoundIsDERIVED::test_MUTATION_…`) only COUNTS statements, so its `RETURN NONE` is harmless there — left unchanged, flagged (§FLAGS).
- **D-LANE** — the brief's "ONE lore pytest session at a time" was LIFTED mid-run by lead #17068 (#466 fixed: `6566ba6`/`e6e17d8`). Before the lift: my first batch ran alone (lane checked clear at start, not re-checked per build — disclosed); one 15-second scoped run started while a peer's run was live (my gate printed busy and I did not stop — a slip, disclosed). After the lift: every full suite at `-n 12` with the 15 GB tree-kill watchdog. **Also a slip:** one `kill` over a cmdline-matched PID list hit my own shell (the #228 self-match, exit 144) — no other process touched; every later stop by explicit PID.
- **D-BASE** — the brief's SAT base was "HEAD + the 63c patch `b23f3e43`"; lead directive #17055 (drained mid-run) moved it: the patch is COMMITTED as `169925f`, the base is plain HEAD. My first reference tree was `ccdad34` + the patch; the SAT/RED runs below are on plain HEAD (§SAT names each tree).
- **D-FORK2 (WITHDRAWN)** — I proceeded on FORK-2 Reading A (constrain claim's typed handler to re-read inline) for ~40 minutes; amendment 5 (`67bf2cc`) REJECTED it and the lead relayed STOP (#17065). Everything Reading-A-shaped is undone: the reference claim is `except TxnClaimLostError: pass` exactly as decision 3 rules; BC-r2-3 is withdrawn; the re-read-keyed enumerator (`scratch rs_readingA_withdrawn.patch`) was never committed. Nothing Reading-A-shaped is in this commit (no DUAL note owed — it never reached a committed file).
- **D-RSHELD** — lead #17066 classifies `test_retry_seam.py` as HELD-PATCH class: the am-5 (B) re-key is in §HELD (appended to r1's patch), applied in my scratch trees for SAT, the wrong builds and the (B)×(C) cross-check; `CR::TestTheRuntimeSetAndTheStaticIndexAgree` imports the index at CALL time so it is RED-for-the-right-reason (not uncollectable) until §HELD lands.

## §P1c — REACH (every ∀ pin r2 adds or relies on; adversary's 6 understated rows re-graded)
| instrument | reach (the set) | derived? | coverage checked? | effect vs proxy | verdict |
|---|---|---|---|---|---|
| one-producer AST scan (`G`) — **was understated (WB12)** | every function + module scope of every package module; a function now INCLUDES the strings of module constants it references by name | modules DERIVED (`rglob`); producer = THROW∧UPDATE per scope incl. referenced constants | floor (tasks + findings found) + 5 synthetic discriminators + PR9 | PROXY (source) — paired with the runtime pin below | closed for the module-constant door; **bound**: a template built by a HELPER function's return value (a call, not a name) still escapes the AST leg — the runtime leg sees it |
| runtime guarded-write pin (`RU`, MP9 — NEW) | every transaction `compose` receives while every task write verb runs | the verb set is DERIVED (AST: `TaskLedger` methods calling `_apply`) | `derived ⊆ observed` asserted — a new `_apply` caller no leg drives REDS | EFFECT (the composed transaction) | SAFE over code it RUNS; bound: a write that bypasses `compose` (raw `_query`) is outside it — the retry-seam SDK guard's territory |
| derived hub cap — **was understated (WB2/WB15)** | K ∈ {0,1,2,3,per,per+1} × {cap, cap+1} | `per`/`fixed` MEASURED per K off `compose` | K=per always crosses a floor boundary (per is measured) | EFFECT | + PR14 (shared cap mutated in-suite) |
| heal packer (NEW) | every straggler of every superseded blocker | population derived from the store; shape MEASURED (`measure_heal_shape`) | chunk count == prediction; every chunk ≤ cap; `chunks` == composed heal txns | EFFECT | bound: prediction model is linear (fixed + per·rows, checked at n=3) — a builder whose chunk cost is non-linear in rows reds the linearity assert loudly, never silently |
| heal store-fault doors (NEW) | every `_query`/`_apply` call the heal makes AFTER the backfill | DERIVED by faulting k = 1… until a boot completes | `doors == k−1 ≥ 2` | EFFECT | bound: a heal store call not through `_query`/`_apply` is uncounted (D's seam-identity sweep covers the read door) |
| WARN telemetry — **was understated (WB14)** | every task transaction | n/a | one crossing + one below (S) | EFFECT + PR13 mutation (silence the shared policy) | closed |
| edge ≡ column helper — **fixtures were understated (WB5)** | every row | DERIVED | `row_count` | EFFECT | closed by PR4's dedupe shape |
| boot heal ∀ stragglers — **was understated (WB3–WB6)** | rows with superseded blockers | DERIVED | multi-blocker rows (PR3), already-head (PR4), phantom (RU), cycle (RU), 6/10 blockers | EFFECT | closed for the named shapes |
| guarded-CAS index (`RS`, **re-keyed by am-5 (B), §HELD**) — was keyed on a SHAPE (`except SurrealStoreError` + inline `_select*`) | every NON-pass-through `except` clause (Name / tuple / bare) of every DERIVED CAS verb (`derive_cas_verbs` — the SAME set (C) drives) | DERIVED verbs; caught names RESOLVED to classes (unresolvable → loud); door iff closure ∋ TxnContentionExhaustedError | both exact sets; non-vacuity; 5 discriminators; the (B)×(C) cross-check both ways | PROXY (source) — its EFFECT twin is (C) | the helper-indirected re-read bound (#494) is MOOT for the door test (re-reads are no longer consulted — (C) observes them at runtime); **new bound**: `derive_cas_verbs` sees a CAS verb only if it calls `_apply` and reaches a shell by same-module method calls — a CAS without the shell is the one-producer pin's catch; a single-statement CAS door is listed by name (`SINGLE_STATEMENT_CAS_DOORS`, am-5 names the one) |
| runtime ∀ (`CR`, am-5 (C) — NEW) | every DERIVED CAS verb (7 on the reference) | DERIVED (`derive_cas_verbs`) | registry == derived, BOTH ways (a new verb undriven reds by name; a stale driver reds) | EFFECT (injection at the verb's own seam; reads/retries counted) | bound: a runtime gate is an invariant only over code it RUNS — reach made a checked variable by the derivation |
| D9 routing pin (`test_blocks_edge`) — **message over-claimed (K16)** | supersede + one hop | hand-shaped | presence only | PROXY | superseded by `RU::TestEveryRELATEComesFromTheSharedFragment` (EFFECT); D9's prose left as r1 wrote it — FLAG for the builder |
| claim-lost literal pin (NEW) | every package module's non-docstring string literals | DERIVED | `_txn` must hold it exactly once (a floor) | PROXY | + the behavioural typed-catch pin (EFFECT) |

## §DUAL — r2's removed/changed-behaviour rows (continuing r1's B/D numbering) + the adversary's three missing items
| row | behaviour (old → new) | adjudication |
|---|---|---|
| **E5** (adversary P6b) | `supersede_task`'s except ladder re-raised a non-lost-race store fault AS-IS → the new R1 classification must not launder it | PRESERVED-WITH-PIN (am-1 R1: the teaching refusal is for the straggler cause only) — `PRB::test_PR1_…` |
| **E11** (adversary P6b) | a re-anchor of `[A, A, X]` collapses the LEGACY duplicate of the OTHER blocker too (`array::distinct` over the whole column) → `[A, X']` | **SPEC-TENSION, NOT PINNED either way**: kickoff §1 prescribes `array::distinct(array::map(…))` over the column (collapses A's duplicate); kickoff §6's fixture text says "only the X entry rewritten". Benign for the CAS (T5 dedupe tolerance). Decision for the lead/sidecar (low); a builder may take either. |
| **B21 — the claim-loss log** (adversary NEW DOOR) | pre-58: a losing claim committed an empty UPDATE and logged NOTHING → post-58 (THROW shell): a rolled-back txn, `store.transaction.rolled_back` | am-3 §3: DEBUG (typed `TxnClaimLostError`), never WARNING/ERROR — PRESERVED-WITH-PIN the old world's silence at operator levels (`RU` 8-way + `PRB::PR10`) |
| B22 | every OTHER THROW-rooted rollback logged at ERROR → WARNING | am-3 §3 ruled; pinned for the transition lost race (`RU` CONTROL). ⚠ An ASSERT/coercion rollback ("engine fault"?) is NOT pinned — two readings (§FLAGS F-r2-4) |
| B23 | the boot heal: one transaction (am-1) → greedy chunks by the heal's own count (am-3 §1) | ruled; pinned (MP16 rows) |
| B24 | am-2's "the boot never fails on a heal fault" → a heal STORE fault RAISES; a chunk's DOMAIN rejection is isolated | ruled (am-3 §2); pinned |
| B25 | a phantom / cyclic chain head: am-1 would fail the boot → skipped + recorded every boot | ruled (am-3 §5); pinned |
| B26 | claim loss typed (`claim_lost:<id>` → `TxnClaimLostError`) — `_txn` gains a class and a classifier branch | ruled; pinned (hierarchy + one-literal + typed catch) |
| **D12** (r1 row, re-adjudicated) | `scripts/test_forgery_door_sweep.py` — the heal's read is door 5, LAST | order now RULED (am-3 §2); prose updated; assertions unchanged |
| **D13** | `G.guarded_shell_producers` — a function's strings now include referenced module constants | widening (MP9); every existing discriminator unchanged + green |
| **D14** | `G::TestParamNamesDoNotCollide…` — `calls.count(...) == 3` on a SHELL spy → marked events REACHING `compose` | SD1 (over-tight pin) |
| **D15 (§HELD)** | `RS._discover_guarded_cas_handlers` — keyed on `except SurrealStoreError` + an inline `_select*` re-read → am-5 (B): every non-pass-through clause (Name / tuple / bare) of every DERIVED CAS verb, caught names resolved, door iff the class closure holds exhausted contention; `has_guard` = an EARLIER clause names the typed error; + `_TYPED_CAS_CATCHES` {claim_task, _reanchor_stragglers} + `TestTheClassKeyedIndexPartitionsEveryCASHandler` | am-4 + am-5; lead #17066 (HELD class). The five canonical doors are unchanged; ⚠ between §HELD and the build `tasks.py::transition`/`supersede_task` are NOT derived (no shell yet) → the door exact-set pin is RED in that window, for the right reason |
| **D18 (§HELD part 3)** | `test_surreal_store.py::TestDomainRejectionErrorType::…governed_conflict_throw…` — `caplog.at_level(logging.ERROR)` → `logging.DEBUG` | am-3 §3 (THROW-rooted rollback → WARNING); the rider's property is server-side survival. GREEN both sides |
| **D17** | `ApplyHook.__init__(ledger: TaskLedger …)` → `ledger: Any` (the (C) family drives the finding ledger's `_apply` too); two `type: ignore[method-assign]` removed (unused) | test-support typing only |
| **D16** | `TYPE_CHECKING` ownership blocks in `G`, `P`, `test_blocks_edge.py`, `test_task_read_surface.py`, `D` | directive #17055 (own every 58 red); runtime-inert, no pin changed |

## §BUILDER CONSTRAINTS (r1's list §BUILDER CONSTRAINTS 1–9 stands; r2 adds)
- **BC-r2-1 (esc1, from r1 §FLAGS 1 — the builder's item):** `scripts/esc1_write_path_cycle_closure.py` — wrap `ledger.supersede_task(…)` as `(await ledger.supersede_task(…)).successor_id` (r1's exact diff; proven in my reference: typecheck scripts leg OK). ⚠ Its RUN has exited 1 since #174 (`[boundary-5] successor is born with NO dependencies`) — a pre-existing corpse assertion, not 58's; surfaced by the adversary, still unowned (§FLAGS).
- **BC-r2-2 (the ONE counting function, am-3 §1):** the supersede accessor and the heal packer consume ONE statement counter; the accessor BUILDS the fixed part for the caller's K. Pinned by effect (padding moves both), not by a name — the builder names it.
- **BC-r2-3 (am-3 §3 as refined by am-5):** `claim_task` catches `TxnClaimLostError` BY TYPE (any body — am-5 rejects dictating it); every other store error propagates; exhausted contention propagates UNREAD (the (C) injection pins it). The throw message is `claim_lost:<task id>` built from ONE literal (tasks.py ≤ 1, `_txn` exactly 1). ~~re-read inline~~ WITHDRAWN (am-5).
- **BC-r2-9 (am-5 (B), §HELD index):** the heal's chunk isolation `except TxnDomainRejectionError` is classified SAFE-BY-TYPE under the verb that contains it; `_TYPED_CAS_CATCHES` lists `tasks.py::_reanchor_stragglers` — a builder that moves that `try` into a helper method changes the derived key (the helper then must be a derived CAS verb, i.e. call `_apply` and reach the shell, and the exact set + the (C) registry re-keyed with it).
- **BC-r2-4 (am-3 §2):** order `_backfill_blocks_edges` → `_reanchor_stragglers`; a heal store fault RAISES (read AND apply); only `TxnDomainRejectionError` from a chunk's apply is isolated (WARNING `task.backfill.straggler_chunk_rejected`, extra `chunk` + `rows`); a compose cap refusal or a single over-cap row RAISES.
- **BC-r2-5 (am-3 §5):** phantom head → WARNING `task.backfill.straggler_phantom_head` (extra `task_id`, `blocker_id`, `phantom_head_id`), the WHOLE row skipped (byte-identical), excluded from `count`; a `superseded_by` cycle → WARNING `task.backfill.straggler_chain_cycle` (extra `task_id`), bounded, no write.
- **BC-r2-6 (am-3 §1 / am-2 (b)):** the heal's INFO `task.backfill.stragglers_reanchored` carries `count` (ROWS healed) and `chunks` (heal transactions composed), once per boot, silent when nothing healed.
- **BC-r2-7 (am-3 §3):** `_log_rollback` level: claim-lost → DEBUG; other THROW-rooted → WARNING; else ERROR (my reference detects THROW-rooted by the engine's `An error occurred:` prefix, PROBED 3.2.4 this session — a builder may choose another classification that meets the pins).
- **BC-r2-8 (RETURN inside a transaction):** do not use `RETURN` as a padding/no-op statement in a composed transaction — measured to end the transaction's work early (§DEVIATIONS D-PAD).

## §HELD — the held integration patch, RE-DERIVED at HEAD `43b8d16` (2026-09-26)
**Three parts, applied together (`held_r2 = r1 §HELD ‖ the am-5 (B) re-key ‖ the am-3 §3 capture-level fix`; md5 `16790e3a98ae4a7c2847f5ddbc8355ab`):**
1. **r1's §HELD, UNCHANGED** — `REPORT-contract-58.md` §HELD (committed at `5a43aeb`, lines 173–557 of that file; md5 of the extracted diff `dbba9753cbe960cda178f42687039c2d`): `server.py` (supersede branch + `_render_supersede_result`), `surreal_schema.py` (the `blocked_by.*` index rider), `_task_fakes.py` (lockstep + `SupersedeResult`), `test_link5_render_containment.py`, `test_mcp_server.py` (D7), the new `test_supersede_render_58.py`. Nothing in r2's rulings (am-2..am-5) touches those hunks.
2. **NEW — `loremaster/tests/test_retry_seam.py`, amendment 5 (B)** (lead #17066: held-patch class, a repo-wide instrument other in-flight contracts run against). VERBATIM below (md5 of this part `…` — see the line after the fence).

3. **NEW — `loremaster/tests/test_surreal_store.py`, one capture level** (`TestDomainRejectionErrorType::test_a_governed_conflict_throw_via_the_transaction_seam_raises_the_typed_error`, the §2.5 rider-ii positive control): `caplog.at_level(logging.ERROR)` → `logging.DEBUG`, DUAL-commented. WHY (SAT-found, §SAT): amendment 3 §3 moves a THROW-rooted rollback's `store.transaction.rolled_back` from ERROR to WARNING, so on a correct 58 build this pin's ERROR-level capture no longer sees the (still server-side) forensics → its ×2 parametrisation is the ONLY red of the whole SAT suite. The rider's property is "the forensics survive SERVER-SIDE", never "at ERROR". Not in my writable set (a 63-series store pin, not a task-ledger test) → held. **GREEN both sides:** on HEAD (`8 passed`) and on the SAT tree with the reference (`8 passed`), so it may land any time before the build. (This is also FORK-3's scope question in the concrete: am-3 §3's "every other THROW-rooted rollback → WARNING" reaches 63's governed-conflict THROW too; my reading = yes, per the ruling's general clause.)

**Receipts (re-derived, not inherited):**
- `git apply --check` of `held_r2` on a CLEAN tree at HEAD `66868bc` → clean (all 7 files); applied in `scratch/sat` for SAT and every wrong build. The 63c-i-a patch `b23f3e43` is COMMITTED (`169925f`) — `git apply --check -R` of it on HEAD succeeds — so per lead #17055 it is NOT applied on top (D-BASE).
- `git apply --check` of all three parts on the SHARED tree (HEAD `a124c5a` + the in-flight 63c amendment-28 fix-pass WIP + peers' untracked files, 2026-09-26 ~20:05Z) → clean; and on the clean HEAD copy (`43b8d16` + this commit's files) → clean.
- Hunks vs 63c: disjoint (r1's measurement stands; the only 63c file §HELD edits is `server.py`, whose supersede branch 63c does not touch).
- ⚠ **Collision with contract-64b's pending commit — TWO files:** `test_mcp_server.py` (r1's D7 hunk; known) and **`test_retry_seam.py`** — `REPORT-contract-64b.md` row G2 WIDENS the SAME door property (recognising `classify_zero_row_cas`) and MERGES `findings.py::_transition` + `annotate` into `_run_guarded`. The (B) re-key here and 64b's G2 edit the same function and the same exact set. **The lead must sequence them; whichever lands second re-bases onto the other** (and `derive_cas_verbs` then derives `findings.py::_run_guarded` — the (C) registry's two findings drivers must be re-keyed with it; §FLAGS F-r2-2).

**Re-verify on the final base (steps — the 63c patch changes again in the amendment-28 fix pass):**
1. `git fetch && git log --oneline -3`; `git diff --stat <this commit> HEAD -- loremaster/loremaster/server.py loremaster/loremaster/store/surreal_schema.py loremaster/tests/_task_fakes.py loremaster/tests/test_link5_render_containment.py loremaster/tests/test_mcp_server.py loremaster/tests/test_retry_seam.py` — if any moved, re-anchor the hunks by SYMBOL (`AppContext.tasks` supersede branch, `_render_supersede_result`, `_task_statements`, `FakeTaskLedger.supersede_task`, `test_superseded_task_in_leg1_renders_the_chain_marker`, `_discover_guarded_cas_handlers` / `_GUARDED_CAS_DOORS`).
2. `git apply --check` part 1 then part 2; then `git apply` both.
3. Bare sweeps (CLAUDE.md rename law) over `loremaster/`: `STRANDED` → 0 hits in `server.py`; `_select` no longer appears in `_discover_guarded_cas_handlers`' door criterion (the re-read key is retired).
4. `uv run pytest -q loremaster/tests/test_retry_seam.py -k "GuardedCas or ClassKeyed or ExhaustionUNREAD"` BEFORE the build: EXPECTED RED = `test_the_door_enumeration_matches_the_canonical_set` (tasks transition/supersede not derived — no shell yet) + `test_the_TYPED_catches_match_their_canonical_set` (no typed claim catch yet) + `test_both_partitions_are_non_empty_and_disjoint`; the discriminators GREEN. After the build: all GREEN, then `test_reanchor_58_r2_cas_runtime.py` GREEN (incl. the (B)×(C) cross-check).

**Part 3, VERBATIM** (md5 `15f38e319cb8d3c25456084dda4989b1`):
```diff
diff --git a/loremaster/tests/test_surreal_store.py b/loremaster/tests/test_surreal_store.py
index c7387fb..0634da2 100644
--- a/loremaster/tests/test_surreal_store.py
+++ b/loremaster/tests/test_surreal_store.py
@@ -1014,7 +1014,13 @@ class TestDomainRejectionErrorType:
         statement, params = compose(
             TxnFragment(statements=['THROW "governed_conflict:probe_t:target_row"'], params={})
         )
-        with caplog.at_level(logging.ERROR):
+        # ⚠ DUAL (packet 58 contract r2 — §HELD part 3, contract-58-r2, 2026-09-26): this capture USED to
+        # be `logging.ERROR`. Packet 58 amendment 3 §3 (docs/design/2026-09-26-packet58-amendment-3.md
+        # @ 7266c1b) rules a THROW-rooted rollback logs at WARNING (a claim loss at DEBUG; ERROR stays for
+        # engine faults), so a correct 58 build records this governed-conflict THROW's forensics at WARNING
+        # and an ERROR-level capture no longer sees them. The rider-ii property is "the forensics survive
+        # SERVER-SIDE", never "at ERROR" — capture every level. REPORT-contract-58-r2.md §HELD part 3.
+        with caplog.at_level(logging.DEBUG):
             with pytest.raises(SurrealStoreError) as exc:
                 await seam(statement, params, acquire=_acquire, drop=_drop, url=env.url)
         assert isinstance(exc.value, governed_type), (
```

**Part 2, VERBATIM:**
```diff
diff --git a/loremaster/tests/test_retry_seam.py b/loremaster/tests/test_retry_seam.py
index 6508735..f20da78 100644
--- a/loremaster/tests/test_retry_seam.py
+++ b/loremaster/tests/test_retry_seam.py
@@ -6782,51 +6782,108 @@ _GUARDED_CAS_GUARD = "TxnContentionExhaustedError"
 _GUARDED_CAS_RE_READ = "_select"
 
 
-def _discover_guarded_cas_handlers() -> dict[str, tuple[str, int, bool]]:
-    """Every guarded-CAS door: ``{"<module>::<function>": (file, lineno, has_guard)}``.
-
-    The PROPERTY, from the AST: an ``except SurrealStoreError`` handler whose body re-reads
-    state. ``has_guard`` is whether the SAME ``try`` also catches
-    :class:`TxnContentionExhaustedError` — which, because ``except`` clauses are tried in
-    order and the typed error SUBCLASSES ``SurrealStoreError``, is the only thing standing
-    between "exhausted" and "re-read and reinterpreted".
+def _is_pass_through(handler: ast.ExceptHandler) -> bool:
+    """A clause whose body is exactly a bare ``raise`` hands the error on untouched — not a reading."""
+    body = handler.body
+    return len(body) == 1 and isinstance(body[0], ast.Raise) and body[0].exc is None
+
+
+def _caught_names(handler: ast.ExceptHandler) -> list[str]:
+    """The class NAMES a clause catches: a ``Name``, each ``Name`` of a TUPLE, ``BaseException`` if bare."""
+    if handler.type is None:
+        return ["BaseException"]
+    if isinstance(handler.type, ast.Name):
+        return [handler.type.id]
+    if isinstance(handler.type, ast.Tuple):
+        return [
+            element.id if isinstance(element, ast.Name) else ast.unparse(element)
+            for element in handler.type.elts
+        ]
+    return [ast.unparse(handler.type)]
+
+
+def _classify_cas_handlers(
+    source: str, key: str, cas_functions: set[str], resolve: Callable[[str], object]
+) -> dict[str, dict[str, tuple[str, int, bool]]]:
+    """Every NON-pass-through ``except`` clause inside a guarded-CAS function, PARTITIONED BY THE CAUGHT
+    CLASS'S HIERARCHY (packet 58 amendment 5 (B) @ 67bf2cc).
+
+    ⚠ DUAL (packet 58 contract r2 — §HELD, contract-58-r2, 2026-09-26): the discovery USED to key on a code
+    SHAPE — an ``except SurrealStoreError`` (``ast.Name`` id) whose body re-reads inline (``_select*``).
+    Amendment 5 retires the re-read key (a handler is found by what it CATCHES, never by what its body
+    looks like) and the name key (a narrower class, a TUPLE and a bare ``except`` are all enumerated).
+    Scope: every ``try`` inside a DERIVED guarded-CAS verb (``_reanchor_58_support.derive_cas_verbs`` —
+    the SAME set the runtime ∀ family drives, so the two layers range over one set by construction).
+    Each caught name is RESOLVED to its class (a name that does not resolve → loud, never skipped); a
+    clause is a DOOR iff some caught class can hold exhausted contention
+    (``issubclass(TxnContentionExhaustedError, caught)``; bare → ``BaseException``), else SAFE-BY-TYPE.
+    ``has_guard`` = an EARLIER clause of the same ``try`` names the typed error.
     """
     doors: dict[str, tuple[str, int, bool]] = {}
-    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
-        if "__pycache__" in path.parts:
+    typed: dict[str, tuple[str, int, bool]] = {}
+    tree = ast.parse(source)
+    for function in ast.walk(tree):
+        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
             continue
-        key = path.relative_to(_PACKAGE_ROOT).as_posix()
-        tree = ast.parse(path.read_text(encoding="utf-8"))
-        parents: dict[int, ast.AST] = {}
-        for parent in ast.walk(tree):
-            for child in ast.iter_child_nodes(parent):
-                parents[id(child)] = parent
-        for node in ast.walk(tree):
+        where = f"{key}::{function.name}"
+        if where not in cas_functions:
+            continue
+        for node in ast.walk(function):
             if not isinstance(node, ast.Try):
                 continue
-            caught = {
-                handler.type.id
-                for handler in node.handlers
-                if isinstance(handler.type, ast.Name)
-            }
+            above: set[str] = set()
             for handler in node.handlers:
-                if not (
-                    isinstance(handler.type, ast.Name)
-                    and handler.type.id == "SurrealStoreError"
-                ):
-                    continue
-                re_reads = any(
-                    isinstance(call, ast.Call)
-                    and isinstance(call.func, ast.Attribute)
-                    and call.func.attr.startswith(_GUARDED_CAS_RE_READ)
-                    for call in ast.walk(handler)
-                )
-                if not re_reads:
-                    continue
-                scope = _enclosing_callable(handler, parents)
-                where = getattr(scope, "name", "<lambda>") if scope else "<module>"
-                doors[f"{key}::{where}"] = (key, handler.lineno, _GUARDED_CAS_GUARD in caught)
-    return doors
+                names = _caught_names(handler)
+                if not _is_pass_through(handler):
+                    classes = [resolve(name) for name in names]
+                    unresolved = [n for n, c in zip(names, classes, strict=True) if not isinstance(c, type)]
+                    assert not unresolved, f"{where}:{handler.lineno} catches unresolvable {unresolved}"
+                    is_door = any(
+                        issubclass(TxnContentionExhaustedError, cast("type", caught)) for caught in classes
+                    )
+                    partition = doors if is_door else typed
+                    guarded = _GUARDED_CAS_GUARD in above
+                    previous = partition.get(where)
+                    partition[where] = (key, handler.lineno, guarded and (previous is None or previous[2]))
+                above.update(names)
+    return {"doors": doors, "typed": typed}
+
+
+def _classified_cas_handlers() -> dict[str, dict[str, tuple[str, int, bool]]]:
+    """:func:`_classify_cas_handlers` over the shipped package's DERIVED guarded-CAS verbs, each caught
+    name resolved in its own module's namespace (``builtins`` for the bare/``Exception`` family)."""
+    import builtins
+
+    from _reanchor_58_support import derive_cas_verbs
+
+    cas_functions = derive_cas_verbs(_PACKAGE_ROOT)
+    found: dict[str, dict[str, tuple[str, int, bool]]] = {"doors": {}, "typed": {}}
+    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
+        if "__pycache__" in path.parts:
+            continue
+        key = path.relative_to(_PACKAGE_ROOT).as_posix()
+        if not any(entry.startswith(f"{key}::") for entry in cas_functions):
+            continue
+        module = importlib.import_module("loremaster." + key[: -len(".py")].replace("/", "."))
+
+        def _resolve(name: str, _module: object = module) -> object:
+            return getattr(_module, name, getattr(builtins, name, None))
+
+        partition = _classify_cas_handlers(path.read_text(encoding="utf-8"), key, cas_functions, _resolve)
+        found["doors"].update(partition["doors"])
+        found["typed"].update(partition["typed"])
+    return found
+
+
+def _discover_guarded_cas_handlers() -> dict[str, tuple[str, int, bool]]:
+    """Every guarded-CAS door: ``{"<module>::<function>": (file, lineno, has_guard)}`` — the DOOR
+    partition of :func:`_classified_cas_handlers` (packet 58 amendment 5 (B); see its docstring).
+    ``has_guard`` is whether an EARLIER clause of the SAME ``try`` catches
+    :class:`TxnContentionExhaustedError` — which, because ``except`` clauses are tried in order and the
+    typed error SUBCLASSES ``SurrealStoreError``, is the only thing standing between "exhausted" and
+    "re-read and reinterpreted".
+    """
+    return _classified_cas_handlers()["doors"]
 
 
 # The canonical set of guarded-CAS doors, as an EXACT SET (the house idiom — one list, one
@@ -6845,6 +6902,19 @@ _GUARDED_CAS_DOORS = {
     "tasks.py::supersede_task": "IllegalTransitionError — 'already superseded by someone else'",
 }
 
+# ⚠ DUAL (packet 58 contract r2 — §HELD; amendment 5 (B) @ 67bf2cc): the SECOND derived partition — a
+# non-pass-through clause of a guarded-CAS verb whose caught class CANNOT hold exhausted contention (a
+# TxnDomainRejectionError subtree) is SAFE BY TYPE.  EXACT SET, so every classified handler is on a
+# reviewer-visible list; a re-parenting of its class under a contention-bearing base flips it into the
+# door set BY DERIVATION (it then reds as a door with no entry).  The runtime ∀ family
+# (test_reanchor_58_r2_cas_runtime.py) drives every entry of BOTH sets — the cross-check, both ways.
+_TYPED_CAS_CATCHES = {
+    "tasks.py::claim_task": "TxnClaimLostError — a lost claim, served as ClaimResult",
+    "tasks.py::_reanchor_stragglers": (
+        "TxnDomainRejectionError — a heal chunk's domain rejection, isolated + WARNING (am-3 §2)"
+    ),
+}
+
 
 class TestNoGuardedCasHandlerReinterpretsExhaustedContention:
     """**adversary P-3 — the BLOCKER item B left standing in three other doors.**"""
@@ -6894,6 +6964,78 @@ class TestNoGuardedCasHandlerReinterpretsExhaustedContention:
         )
 
 
+class TestTheClassKeyedIndexPartitionsEveryCASHandler:
+    """Packet 58 amendment 5 (B) — §HELD, contract-58-r2.  The SAFE-BY-TYPE exact set, non-vacuity, and
+    the scanner's own discriminators (§2 of the amendment).  The hierarchy pins and the (B)×(C)
+    cross-check live in 58's own files (``test_reanchor_58_r2_rulings.py``,
+    ``test_reanchor_58_r2_cas_runtime.py``)."""
+
+    def test_the_TYPED_catches_match_their_canonical_set(self) -> None:
+        typed = _classified_cas_handlers()["typed"]
+        assert typed.keys() == _TYPED_CAS_CATCHES.keys(), (
+            f"the SAFE-BY-TYPE CAS handlers changed.\n  found, unlisted: "
+            f"{sorted(typed.keys() - _TYPED_CAS_CATCHES.keys())}\n  listed, not found: "
+            f"{sorted(_TYPED_CAS_CATCHES.keys() - typed.keys())}"
+        )
+
+    def test_both_partitions_are_non_empty_and_disjoint(self) -> None:
+        found = _classified_cas_handlers()
+        assert found["doors"] and found["typed"], {k: sorted(v) for k, v in found.items()}
+        assert not found["doors"].keys() & found["typed"].keys()
+
+    @pytest.mark.parametrize(
+        ("handlers", "expected"),
+        [
+            pytest.param(
+                "    except SurrealStoreError:\n        pass\n", ("doors", False), id="broad-no-guard-DOOR"
+            ),
+            pytest.param(
+                "    except TxnContentionExhaustedError:\n        raise\n"
+                "    except SurrealStoreError:\n        pass\n",
+                ("doors", True), id="broad-guarded-DOOR",
+            ),
+            pytest.param(
+                "    except TxnClaimLostError:\n        pass\n", ("typed", False), id="typed-SAFE-listed"
+            ),
+            pytest.param("    except:\n        pass\n", ("doors", False), id="bare-except-is-a-DOOR"),
+            pytest.param(
+                "    except (SurrealStoreError, ValueError):\n        pass\n",
+                ("doors", False),
+                id="tuple-DOOR",
+            ),
+        ],
+    )
+    def test_the_discriminators(self, handlers: str, expected: tuple[str, bool]) -> None:
+        source = "async def f(self):\n    try:\n        await self._apply([])\n" + handlers
+        found = _classify_cas_handlers(source, "synthetic.py", {"synthetic.py::f"}, self._resolve)
+        partition, guarded = expected
+        assert list(found[partition]) == ["synthetic.py::f"], found
+        assert found[partition]["synthetic.py::f"][2] is guarded
+        other = "typed" if partition == "doors" else "doors"
+        assert not found[other], found
+
+    def test_an_unresolvable_name_is_LOUD_and_a_non_CAS_function_is_out_of_scope(self) -> None:
+        source = (
+            "async def f(self):\n    try:\n        await self._apply([])\n"
+            "    except NoSuchError:\n        pass\n"
+        )
+        with pytest.raises(AssertionError, match="unresolvable"):
+            _classify_cas_handlers(source, "synthetic.py", {"synthetic.py::f"}, self._resolve)
+        out_of_scope = _classify_cas_handlers(source, "synthetic.py", set(), self._resolve)
+        assert out_of_scope == {"doors": {}, "typed": {}}
+
+    @staticmethod
+    def _resolve(name: str) -> object:
+        import builtins
+
+        stand_in = type("TxnClaimLostError", (txn_module.TxnDomainRejectionError,), {})
+        return {
+            "SurrealStoreError": txn_module.SurrealStoreError,
+            "TxnContentionExhaustedError": TxnContentionExhaustedError,
+            "TxnClaimLostError": getattr(txn_module, "TxnClaimLostError", stand_in),
+        }.get(name, getattr(builtins, name, None))
+
+
 class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:
     """The BEHAVIOURAL half of P-3 — because a guard can exist and guard NOTHING.
 
```
md5(part 2) = 5b5f2d8f42d312952bc790096fdf3b06 · md5(held_r2 = part1‖part2) = 395c50e241f27b7ad295d3b5c6c6f62a

## §FLAGS (outside my writable set, or cross-packet — the exact edit/decision, never made silently)
- **F-r2-1 esc1 (builder item, r1 §FLAGS 1 — unchanged):** `scripts/esc1_write_path_cycle_closure.py` `(await ledger.supersede_task(…)).successor_id` (applied in my scratch trees; typecheck scripts leg OK there). ⚠ Its RUN exits 1 at HEAD since #174 (`[boundary-5] successor is born with NO dependencies`) — a pre-existing corpse assertion outside every gate, still unowned (adversary §RESIDUALS R2).
- **F-r2-2 64b × (C) registry:** 64b-i's pending build MERGES `findings.py::_transition` + `annotate` into `_run_guarded` and adds identity kwargs. `derive_cas_verbs` follows automatically; `test_reanchor_58_r2_cas_runtime.DRIVERS`' two findings keys + drivers do NOT — they RED (by name, as designed) the day 64b lands until 64b's builder re-keys them. Same for the §HELD (B) re-key vs 64b's G2 row in `test_retry_seam.py` (§HELD collision note). Lead's sequencing call.
- **F-r2-3 D9's false prose (adversary K16):** `test_blocks_edge.py`'s supersede-routes-through pin claims *"a hand-rolled RELATE in a helper still reds"* — its assertion is presence-only. The claim is now TRUE of `RU::TestEveryRELATEComesFromTheSharedFragment`, not of D9; D9's message should say so (r1's line; I left it — a one-line prose fix for the builder or the next contract touch).
- **F-r2-4 r1's padding mutation uses `RETURN NONE`** (`S::TestTheHubBoundIsDERIVED::test_MUTATION_…`): harmless there (it only counts statements) but the pattern is a trap (finding #497 — a `RETURN` truncates a composed transaction and commits the prefix). Suggest `LET $pad = NONE` at the next touch.
- **F-r2-5 store reference gap:** finding **#497** (RETURN-in-transaction) — docs-only, for whoever next edits `docs/reference/surrealdb-31-capabilities.md`.
- **F-r2-6 other lanes' currency ORPHANs (not 58's):** at HEAD `66868bc` + my files, `--currency --legs typecheck,ruff` rendered 16 SELF-DESTRUCT orphans on the `packet-64b-i-contract` and `packet-63c-i-a-a28-contract` bounds (their registered files are uncommitted/untracked in the shared tree, so a clean HEAD copy sees them missing). Owners: contract-64b / the a28 lane. My own 6 residuals there (`_reanchor_58_support.py` ×4 typing, `test_reanchor_58_r2_rulings.py` ×2 `list-item`) were FIXED before commit.
- **F-r2-7 `pending_contracts.yaml` in the SHARED tree also carries contract-64b's UNCOMMITTED block.** My commit stages ONLY my hunk (HEAD's file + my `packet-58-contract` entry, staged from a blob; the working tree keeps 64b's block untouched).
- **F-r2-9 the sweep's own mypy-clean pin is RED until the build** (`scripts/test_forgery_door_sweep.py::TestThisInstrumentIsTYPECHECKED`): the #17055 ownership block (a static reference to the unbuilt `SupersedeResult`) is by construction a mypy error in that file, and this pin runs mypy over it. Owned, self-destructs with the build; the cost is that the pin cannot catch a NEW mypy error in the sweep in the window. Alternative if the lead prefers: drop the block + the file's registration and move D12's two reds' ownership elsewhere — there is no other mechanism: the registry owns pytest reds per FILE and a file is registrable only through a mypy error.
- **F-r2-8 registered-file breadth:** directive #17055's ownership is per FILE, so `test_blocks_edge.py`, `test_task_read_surface.py` and `scripts/test_forgery_door_sweep.py` are now wholly OWNED by `packet-58-contract` until the build — any NEW red in those files before then renders RED_ADJUDICATED under 58's name. Bound, named; it self-destructs with the build.

## §DRY LEDGER (brief-base §6 — new reusable symbols this revision introduces)
⚠ Honest provenance: the `lore_search` queries below were RUN at report time (2026-09-26 ~18:35Z), AFTER the symbols were written — each returned MY new symbol as its top hit (the index had picked them up), plus the pre-existing candidates named. The "what it returned" column is therefore what I had READ before writing (the named files — r1's tests, the adversary's instruments, `test_retry_seam` §8c), not a pre-write search result. A pre-write search was not run; stated, not dressed up.
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_reanchor_58_support.ComposeSpy` | `lore_search("spy on compose composed transaction statements test")` | r1's per-test `_spy` closures in `S::TestTheHubBoundIsDERIVED._composed_count` and the adversary's PR2 | HAND-ROLLED ONCE in the support module (r2's five compose-spying pins call it); r1's closures left as r1 wrote them (a refactor of committed pins is not this revision's) |
| `seed_stragglers` / `measure_heal_shape` / `predicted_chunks` / `boot` | `lore_search("seed stragglers superseded blocker bulk")` | adversary batch-3 `_stragglers` (scratch) + r1's `_superseded_chain` | `seed_stragglers` = the adversary's `_stragglers` shape, promoted to the ONE support copy (PR19/PR20 keep their AST-equal local copy — am-17) |
| `derive_cas_verbs` + `CAS_SHELL` / `SHELL_LEDGER_MODULES` / `SINGLE_STATEMENT_CAS_DOORS` | `lore_search("derive guarded CAS verbs shell callers AST")` | `test_retry_seam._discover_guarded_cas_handlers` (shape-keyed), G's `guarded_shell_producers` | HAND-ROLLED — ONE derivation consumed by BOTH (C) and the §HELD (B) re-key, so the two layers range over one set by construction (am-5 §3) |
| `Injection` (C) | `lore_search("inject exhausted contention at apply seam test")` | `test_retry_seam`'s fake-connection doors (`_AckConnection`), r1's `ApplyHook` | HAND-ROLLED (a real-ledger seam wrapper that COUNTS reads/retries after the fault — neither existing tool counts) |
| `_HealDoors` (RU) | same | the forgery door sweep (`scripts/forgery_door_sweep.py`, seam-identity) | HAND-ROLLED, narrow (arms after the backfill — pins the ruled order while sweeping the heal's doors); the sweep stays the wide instrument |
| `_classify_cas_handlers` / `_classified_cas_handlers` / `_TYPED_CAS_CATCHES` (§HELD) | read `test_retry_seam` §8c | the shape-keyed discovery | EXTENDED in place (the same function family, re-keyed per am-5), never a second enumerator |
| `_docstring_nodes` reuse | — | G's helper | REUSED (imported by RU) |
| `parse_production_trees` | lead #17068 | `_logging_fixtures.parse_production_trees` | REUSED (the literal scan routes through it) |

**Packages considered:** `ast` (stdlib) for every scan — `libcst`/`semgrep` not installed (adversary §P-PKG read the metadata; not re-derived); the heal packer is integer arithmetic over `compose`'s own count (no package applies); `networkx`/`graphlib` untouched (r1's cycle detector reused). Verdict: `bespoke` only for test instruments, each reusing an in-house seam.

## §MUTATION — every r2 pin, killed by a DECLARED wrong build (declare-then-diff, both ways)
**Instrument:** `wb58r2.py` (pasted VERBATIM in §INSTRUMENTS; md5 at the final run `c4176c3e…`, + the one post-run `CLTUPLE` build → `cb34783a…`). Host: the SAT tree `scratch/sat` = HEAD `66868bc` + `held_r2` (§HELD) + the reference (§REFERENCE) + the esc1 one-liner + this commit's files; `loremaster.__file__` = `…/051e3520-…/scratchpad/sat/loremaster/loremaster/__init__.py`. Scope per build = every r2 + r1 58 file + D + the three §HELD `test_retry_seam` classes (183 tests). Every declared set was written from `--collect-only` ids (`collected_final.txt`) BEFORE the run; every anchor asserted to match EXACTLY once; every mutated file asserted CHANGED and restored byte-exact (md5) after each build. Run 2026-09-26 18:16Z→18:58Z at `-n 12` (concurrent lore sessions allowed — lead #17068).
**Headline: 49 builds · 45 EXACT/INCLUDED as declared · 1 HANG as declared · 3 mismatches, each adjudicated below — 0 builds survive the contract.** The adversary's own survivors (WB1, WB2, WB7, WB8, WB9, WB14, WB15, WB16, K16, WB18 — verbatim anchors) and every re-expressed heal/claim build are killed.

| build | mode | declared RED | observed | verdict |
|---|---|---|---|---|
| WB1 | exact | 1 | 1 failed, 182 passed in 25.37s | **EXACT** (both ways) |
| WB2a | exact | 0 | 183 passed in 26.41s | **EXACT** (both ways) |
| WB2 | exact | 5 | 5 failed, 178 passed in 24.23s | **EXACT** (both ways) |
| WB7 | exact | 1 | 1 failed, 182 passed in 23.17s | **EXACT** (both ways) |
| WB8 | exact | 1 | 1 failed, 182 passed in 25.28s | **EXACT** (both ways) |
| WB9 | exact | 2 | 2 failed, 181 passed in 25.60s | **EXACT** (both ways) |
| WB14 | exact | 1 | 1 failed, 182 passed in 25.85s | **EXACT** (both ways) |
| WB15 | exact | 1 | 1 failed, 182 passed in 26.13s | **EXACT** (both ways) |
| WB16 | exact | 1 | 1 failed, 182 passed in 22.90s | **EXACT** (both ways) |
| K16 | exact | 1 | 1 failed, 182 passed in 22.96s | **EXACT** (both ways) |
| WB18 | exact | 1 | 1 failed, 182 passed in 24.77s | **EXACT** (both ways) |
| K4 | exact | 4 | 4 failed, 179 passed in 22.63s | **EXACT** (both ways) |
| K10 | exact | 3 | 3 failed, 180 passed in 24.51s | **EXACT** (both ways) |
| WB3r | exact | 1 | 1 failed, 182 passed in 23.65s | **EXACT** (both ways) |
| WB4r | exact | 1 | 1 failed, 182 passed in 22.01s | **EXACT** (both ways) |
| WB5r | exact | 1 | 1 failed, 182 passed in 22.28s | **EXACT** (both ways) |
| WB6r | exact | 1 | 1 failed, 182 passed in 21.33s | **EXACT** (both ways) |
| WB12r | exact | 2 | 2 failed, 181 passed in 20.74s | **EXACT** (both ways) |
| WB17r | hang | PR15 + RU cycle must not return | HANG rc=-9 | **HANG as declared** |
| WB17b | exact | 1 | 1 failed, 182 passed in 21.08s | **EXACT** (both ways) |
| K7r | exact | 8 | 12 failed, 171 passed in 20.77s | **MISMATCH** — unexpected RED: TestExhaustedContentionPropagatesUNREADFromEveryCASVerb::test_the_typed_error_propagates_u, TestTheDrivenSetIsTheDerivedSet::test_every_derived_CAS_verb_has_a_driver_and_every_driver, TestTheRuntimeSetAndTheStaticIndexAgree::test_every_statically_listed_handler_is_runtime_d, TestTheClassKeyedIndexPartitionsEveryCASHandler::test_the_TYPED_catches_match_their_canoni |
| K9r | exact | 3 | 3 failed, 180 passed in 21.65s | **EXACT** (both ways) |
| K11r | exact | 7 | 7 failed, 176 passed in 21.60s | **EXACT** (both ways) |
| K17r | exact | 5 | 5 failed, 178 passed in 22.82s | **EXACT** (both ways) |
| AM2L | exact | 3 | 3 failed, 180 passed in 26.56s | **EXACT** (both ways) |
| FO1 | exact | 3 | 5 failed, 178 passed in 21.59s | **MISMATCH** — unexpected RED: TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_, TestTheClassKeyedIndexPartitionsEveryCASHandler::test_the_TYPED_catches_match_their_canoni |
| FO2 | exact | 5 | 5 failed, 178 passed in 21.70s | **EXACT** (both ways) |
| CL1 | exact | 1 | 1 failed, 182 passed in 21.47s | **EXACT** (both ways) |
| CL2 | exact | 1 | 1 failed, 182 passed in 22.75s | **EXACT** (both ways) |
| CL3 | exact | 3 | 3 failed, 180 passed in 23.14s | **EXACT** (both ways) |
| CL4 | exact | 3 | 3 failed, 180 passed in 22.25s | **EXACT** (both ways) |
| FAKE | exact | 1 | 1 failed, 182 passed in 21.95s | **EXACT** (both ways) |
| IDX | exact | 3 | 3 failed, 180 passed in 22.26s | **EXACT** (both ways) |
| CLDOOR5 | exact | 4 | 4 failed, 179 passed in 23.89s | **EXACT** (both ways) |
| CLDOOR5b | exact | 5 | 5 failed, 178 passed in 25.27s | **EXACT** (both ways) |
| TRNOGUARD | exact | 3 | 3 failed, 180 passed in 24.49s | **EXACT** (both ways) |
| STALE | exact | 3 | 3 failed, 181 passed in 25.29s | **EXACT** (both ways) |
| CLREPARENT | exact | 3 | 1 failed, 182 passed in 21.43s | **MISMATCH** — declared-but-GREEN: TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_, TestTheClassKeyedIndexPartitionsEveryCASHandler::test_the_TYPED_catches_match_their_canoni |
| K1 | include | 1 | 19 failed, 164 passed in 22.92s | **INCLUDED** (+18 further reds listed, include mode) |
| K2 | include | 1 | 1 failed, 170 passed, 12 errors in 22.40s | **INCLUDED** (+12 further reds listed, include mode) |
| K3 | include | 2 | 12 failed, 171 passed in 21.93s | **INCLUDED** (+10 further reds listed, include mode) |
| K5 | include | 1 | 2 failed, 181 passed in 23.44s | **INCLUDED** (+1 further reds listed, include mode) |
| K6 | include | 1 | 6 failed, 177 passed in 22.66s | **INCLUDED** (+5 further reds listed, include mode) |
| K8 | include | 2 | 8 failed, 175 passed in 21.59s | **INCLUDED** (+6 further reds listed, include mode) |
| K12 | include | 1 | 1 failed, 182 passed in 25.12s | **INCLUDED** (+0 further reds listed, include mode) |
| K13 | include | 1 | 1 failed, 182 passed in 24.06s | **INCLUDED** (+0 further reds listed, include mode) |
| K14 | include | 1 | 1 failed, 182 passed in 23.79s | **INCLUDED** (+0 further reds listed, include mode) |
| K15 | include | 1 | 1 failed, 182 passed in 24.22s | **INCLUDED** (+0 further reds listed, include mode) |
| CLTUPLE | exact | 4 | 4 failed, 179 passed in 23.62s | **EXACT** (both ways) |

**The three mismatches, each adjudicated individually:**
- **K7r** (re-anchor through a PRIVATE clone) — declared 8, observed 12: the 4 extra reds are r2's NEW instruments catching it too, from a different side — `derive_cas_verbs` no longer sees the boot heal reach the shell (its re-anchor goes through the clone), so `CR::TestTheDrivenSetIsTheDerivedSet` (a stale driver), `CR::…[tasks.py::_reanchor_stragglers]` (stale), `CR::TestTheRuntimeSetAndTheStaticIndexAgree` and the §HELD `test_the_TYPED_catches_match_their_canonical_set` (the heal's typed catch left the derived set) all RED. Legitimate extra kills — my declaration predated the (C)/(B) layers' reach over this build. Not a pin defect.
- **FO1** (the heal's chunk catch widened to `SurrealStoreError` — am-2's fail-open apply) — declared 3, observed 5: the §HELD (B) index classifies the widened catch as a DOOR (its class holds exhausted contention), so the door exact set and the typed exact set both RED. Legitimate extra kill (exactly the index's job).
- **CLREPARENT** (`TxnClaimLostError` re-parented under `SurrealStoreError`) — declared 3, observed 1 (`RU::TestTheClaimLostHierarchy`): the two index legs stayed GREEN, and they are RIGHT to — re-parenting the claim class under the BASE store error does not put `TxnContentionExhaustedError` under it, so the typed catch still cannot hold exhaustion. **My prediction was wrong, not the index.** The flip the index must see is a catch WIDENED to a contention-bearing class → added build **CLTUPLE** (`except (TxnClaimLostError, SurrealStoreError)`), declared AFTER this observation (stated), run alone: **EXACT** (4 reds: both index sets, `G_LOUD`, `RU_TYPED`).
- **Batch-1 history (superseded, disclosed):** an earlier run of 43 builds on a `ccdad34`-based reference tree (before am-4/am-5) scored 41 exact + 2 prediction misses (K7r's r1 padding pin stays GREEN because the STAMP still pads the cap — declaration dropped for the final run; K17r additionally reds the MP9 runtime pin — declaration added). The first launch of that run had a parser bug (captured log lines starting `ERROR ` read as node ids) — killed, fixed, re-run; the killed partial is not counted.
- **SD1 / PR9 before-after receipts (same reference, r1 vs r2 test file):** r1's `G` → `TestParamNamesDoNotCollideAcrossComposedShells` RED (`assert (4 == 3)` — the derivation's own shell calls counted) and `PR9` RED (`'Ledger._assign_fragment' in {…}` false — the module-constant clone unseen); r2's `G` → both GREEN, plus the routed literal scan GREEN (`3 passed`).
- **mutation_proof.py not used for the multi-edit builds** (it takes one anchor); `wb58r2.py` implements the same both-ways diff and exact-once anchor discipline over several edits (the adversary's `wb_driver.py` precedent). Stated, not a gap.

## §RED@HEAD — measured 2026-09-26 at HEAD `43b8d16` (clean copy `scratch/head` + exactly this commit's files; no §HELD, no build)
`uv run pytest -n 12` over every 58 file + every DUAL-edited file + `test_ast_reach_helpers.py` → **`119 failed, 413 passed, 5 skipped`** (log `red_at_head.log`). Per file: S 44 · G 15 · P 5 · `test_blocks_edge` 1 (D10) · `test_task_read_surface` 1 (D1) · D 3 · PRB 12 · SC 2 · A2 3 · RU 27 · CR 6.
- **r1's 68 unchanged** (S/G/P/D10/D1/D12×2 — r1 §RED's classification stands) **+ 1 NEW in D:** `TestThisInstrumentIsTYPECHECKED::test_mypy_is_clean_over_the_sweep_and_its_contract` — reddened BY the directive-#17055 ownership block (`if TYPE_CHECKING: from loremaster.tasks import SupersedeResult` is a mypy error, which the sweep's own mypy-clean pin sees). OWNED, self-destructs with the build; the cost (that pin is blind to a NEW mypy error in the sweep until 58 builds) is §FLAGS F-r2-9.
- **r2's 50 new reds, all right-reason** (first exception per failure): 24 `AssertionError` (no re-anchor / heal / note / partition / typed log / derived verbs — each message names the missing mechanism), 11 `AttributeError` (`max_reanchor_dependents` ×6, `.reanchored`/`.reblocked` on a `str` ×3, `TxnClaimLostError` ×1, `_TYPED_CAS_CATCHES` not yet in `test_retry_seam` — §HELD ×1), 6 `AssertionError` (K-cap: "a supersede with one more dependent composed NO more statements" — first run read `ZeroDivisionError`, replaced by that teaching assert before this commit), 4 `Failed: DID NOT RAISE` (PR1: no fault to launder; the typed-catch pin; the two cycle-refusal controls — nothing is re-anchored, so nothing cycles), 1 `IndexError` (PR12, AST-equal: `notes[0]` — no note exists).
- **GREEN at HEAD by design — exactly 8 of r2's 58 collected tests** (derived: `comm` of the collected ids vs the red ids): PR5, PR9, PR10, PR13, PR15 (no heal / no task WARN / a silent empty-UPDATE loss at HEAD — each asserts the ABSENCE of a defect a wrong 58 build introduces; PR9 is GREEN because r2's scanner reach fix is in the test file) and the three CR drivers for `findings.py::_transition`, `findings.py::annotate`, `briefs.py::_relate_briefed` (those guarded CAS doors exist at HEAD and already propagate exhaustion unread — the property holds; 58 adds the four task verbs). Plus `test_ast_reach_helpers.py` GREEN (the routed literal scan is no whole-tree clone — lead #17068).
- **Ownership:** every file above is registered in `scripts/pending_contracts.yaml` bound `packet-58-contract` (§CURRENCY).

## §SAT — satisfiability on the RIGHT base (full suite; every red individually adjudicated)
- **Tree:** `scratch/sat` = HEAD `43b8d16` (the 63c-i-a build is COMMITTED at `169925f` — lead #17055: plain HEAD, the patch NOT re-applied; `git apply --check -R` of `b23f3e43` on HEAD succeeds) + `held_r2` parts 1–2 + the reference (§REFERENCE) + the esc1 one-liner + this commit's files (+ `pending_contracts_r2.yaml`). **Provenance printed by the runner:** `loremaster.__file__ = …/051e3520-…/scratchpad/sat/loremaster/loremaster/__init__.py`.
- **Run:** `uv run pytest -n 12 -q -rfE --tb=line` (concurrent lore sessions allowed, lead #17068; 15 GB tree-kill watchdog armed — never fired; no `Resource busy` line → #486 not observed), 2026-09-26 (wall 24:57, per pytest):
  **`2 failed, 11859 passed, 62 skipped, 3 xfailed, 9 warnings in 1497.67s (0:24:57)`**.
- **The 2 reds, adjudicated:** both are `test_surreal_store.py::TestDomainRejectionErrorType::test_a_governed_conflict_throw_via_the_transaction_seam_raises_the_typed_error[execute_transaction|execute_read_transaction]` → `AssertionError: the raw THROW text did not reach the server-side rollback log` — **58-attributable (a ruling-vs-existing-pin collision, not a build defect):** am-3 §3 moves THROW-rooted rollbacks to WARNING; this 63-series pin captured at ERROR. Resolved by **§HELD part 3** (capture every level; the rider's property is server-side survival, not the level) — re-run on the SAT tree with part 3: `8 passed` (the whole class); on HEAD: `8 passed`.
- **⇒ 0 red attributable to the contract or the reference once §HELD (all three parts) is applied; 0 unrelated reds on this base** (the 7 `restore_prod_dump`/`concurrent_wire_acceptance` HEAD reds the brief named were fixed upstream at `441f3b0`; the #466 contract-ahead reds turned GREEN at `6566ba6`/`e6e17d8` — neither appears). Not "set-equal to a baseline": every red is named above.
- **Lint on the SAT tree (the "still 0 after lint" leg):** `uv run ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → every leg OK (`lorerunes · lorescribe · loresigil · loremaster · skills · docs/eval · scripts · shellcheck OK (7 tracked .sh)`), exit 0 — so on the BUILT world every `TYPE_CHECKING` ownership reference resolves and the `packet-58-contract` bound self-destructs as designed.
- **Required-green (§REQUIRED-GREEN) all inside the 11859 passed** (none in the red set).

## §CURRENCY — directive #17055 (own every 58 red, r1 AND r2; prove RED_ADJUDICATED)
**Instrument:** `uv run python scripts/pending_contract_gate.py --currency -- -n 12` (ALL three manifested gates: typecheck, ruff, the FULL pytest suite), in the clean HEAD copy `scratch/head` = HEAD `43b8d16` + exactly this commit's files (the registry = HEAD's + this commit's `packet-58-contract` entry). Provenance: `…/scratchpad/head/loremaster/loremaster/__init__.py`.
- **Run 1 — FAIL, my miss:** typecheck `RED_ADJUDICATED` (23 owned) · ruff `GREEN` · pytest `RED_ORPHANED — 6`: every orphan in `test_reanchor_58_r2_cas_runtime.py`, which I had not registered (its pins reach the shell dynamically, so it had no mypy error to own). Fixed: a runtime-inert `TYPE_CHECKING` reference to `TaskLedger._guarded_append_fragment` + its registry row. The other 113 reds were already owned, and NO non-58 red existed at HEAD.
- **Run 2 — PASS:**
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 24 residual(s), owned by: packet-58-contract (owner: packet 58 (…) — the 58 builder, serial after 63c-i-a; trigger: the packet-58 build lands TaskLedger.max_reanchor_dependents, …
  ruff         GREEN
  pytest       RED_ADJUDICATED — 119 residual(s), owned by: packet-58-contract (…)
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
```
  119 pytest residuals == §RED@HEAD's 119 exactly (r1's 68 + the sweep's mypy-clean pin + r2's 50). The bound self-destructs on the built world: on the SAT tree every leg of `typecheck.sh` is clean (§SAT), so each registered file then "produced NO mypy errors" and the gate DEMANDS the entry's deletion with the build.
- **Registered files (11):** S, G, P, PRB, SC, A2, RU, CR, `test_blocks_edge.py`, `test_task_read_surface.py`, `scripts/test_forgery_door_sweep.py` (§FLAGS F-r2-8/F-r2-9 for the breadth/cost).
- **Staging:** HEAD moved to `99dbe49` before commit and gained contract-a28's registry entry; the committed `pending_contracts.yaml` = HEAD `99dbe49`'s file with ONLY the `packet-58-contract` entry replaced (`--verify-registry` OK on exactly that file). contract-64b's uncommitted block in the shared working tree is NOT staged (§FLAGS F-r2-7).

## §REFERENCE — the reference build (SAT + mutation host) — NOT A SPEC
= adversary-58's `build_ref58.py` (VERBATIM in `9f2f580:REPORT-adversary-58.md` §INSTRUMENTS, md5 `5915c12e` — extracted byte-exact, §0) **then** contract-58-r2's `build_ref58_r2.py` (amendment-3 deltas, VERBATIM below), then `ruff check --fix` (import order), over HEAD's `tasks.py` / `store/_txn.py`. Result md5: `tasks.py 762287a6497ece6bcf16fb87343f0158` · `_txn.py 1bf4521f81644de03de04d1b24f38cdb`. Choices here (the `An error occurred:` THROW-root test, the per-distinct-blocker heal DELETE, `_heal_row_fragments`, `StragglerHealPackerError`, …) are ONE satisfying shape; the builder follows the rulings + BUILDER CONSTRAINTS, not this. Using the adversary's build as the base (rather than r1's reference) is deliberate: the adversary's `wrong_builds.py` anchors then apply VERBATIM, so its survivors are re-killed on their own terms.

## §INSTRUMENTS — pasted VERBATIM (brief-base §1: the instruments behind this report's claims)
Scratch root (session-local, NOT durable — hence pasted): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/051e3520-9705-4d88-80c5-a1b8b25785f7/scratchpad/`. To re-run: `./scripts/scratch_copy.sh <dest>` → check out the base → `rebuild_ref.sh <dest>` (needs `held_r2.patch` = r1 §HELD ‖ this report's §HELD parts 2 and 3; `adv/build_ref58.py` extracted from `9f2f580:REPORT-adversary-58.md` §INSTRUMENTS (md5 `5915c12e`); `build_ref58_r2.py`; `pending_contracts_r2.yaml` = HEAD's registry + this commit's `packet-58-contract` entry) → `run_wb.sh` / `run_full.sh`.

### `build_ref58_r2.py` (md5 `bdb404c4129b48937106960d96954cad`)
```python
#!/usr/bin/env python3
"""contract-58-r2's REFERENCE BUILD — amendment-3 deltas layered over adversary-58's ``build_ref58.py``.

Usage: build_ref58_r2.py <scratch-root>   (run AFTER build_ref58.py on the same root)
Scratch instrument ONLY (a SAT + mutation host, never a spec).  Every edit asserts its anchor
occurs exactly once (#194: a mutation/build that does not LAND is a loud failure).
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster/loremaster/tasks.py"
TXN = ROOT / "loremaster/loremaster/store/_txn.py"
sources = {TASKS: TASKS.read_text(), TXN: TXN.read_text()}


def sub(path: Path, old: str, new: str) -> None:
    count = sources[path].count(old)
    assert count == 1, f"{path.name}: anchor found {count}x: {old[:90]!r}"
    sources[path] = sources[path].replace(old, new)


# =============================== _txn.py (am-3 decision 3) ===============================
sub(
    TXN,
    "class RetryableConflictSignal(Exception):\n",
    '''class TxnClaimLostError(TxnDomainRejectionError):
    """A task claim's guarded CAS matched ZERO rows and THREW ``claim_lost:`` (packet 58 am-3 §3).

    A ROUTINE outcome (the fleet's most common contention result), classified by the typed marker
    so the ledger catches the TYPE and :func:`_log_rollback` records it at DEBUG, never ERROR.
    """


class RetryableConflictSignal(Exception):
''',
)
sub(
    TXN,
    '_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"\n',
    '_ERROR_CLASS_CLAIM_LOST = "claim lost — another claimant or a state change won the compare-and-set"\n'
    '_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"\n',
)
sub(
    TXN,
    '_GOVERNED_CONFLICT_MARKER = "governed_conflict:"\n',
    '_GOVERNED_CONFLICT_MARKER = "governed_conflict:"\n'
    "# packet 58 am-3 §3: the typed marker the task claim shell THROWs on a lost CAS.\n"
    '_CLAIM_LOST_MARKER = "claim_lost:"\n'
    "# The engine's prefix for a THROW-rooted statement result (probed 3.2.4: "
    "`An error occurred: <message>`).\n"
    '_THROW_ROOT_MARKER = "an error occurred:"\n',
)
sub(
    TXN,
    "    if _GOVERNED_CONFLICT_MARKER in lowered:\n        return _ERROR_CLASS_GOVERNED_CONFLICT\n",
    "    if _GOVERNED_CONFLICT_MARKER in lowered:\n        return _ERROR_CLASS_GOVERNED_CONFLICT\n"
    "    if _CLAIM_LOST_MARKER in lowered:\n        return _ERROR_CLASS_CLAIM_LOST\n",
)
sub(
    TXN,
    "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n        return TxnGovernedConflictError(message)\n",
    "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n        return TxnGovernedConflictError(message)\n"
    "    if error_class == _ERROR_CLASS_CLAIM_LOST:\n        return TxnClaimLostError(message)\n",
)
sub(
    TXN,
    '''    logger.error(
        "store.transaction.rolled_back",
        extra={
            "statement_index": root_cause.index,''',
    '''    text = str(root_cause.raw_result).lower()
    if _classify_engine_error(root_cause.raw_result) == _ERROR_CLASS_CLAIM_LOST:
        level = logging.DEBUG
    elif text.startswith(_THROW_ROOT_MARKER):
        level = logging.WARNING
    else:
        level = logging.ERROR
    logger.log(
        level,
        "store.transaction.rolled_back",
        extra={
            "statement_index": root_cause.index,''',
)

# =============================== tasks.py ===============================
sub(
    TASKS,
    "    TxnContentionExhaustedError,\n    TxnFragment,\n",
    "    TxnClaimLostError,\n    TxnContentionExhaustedError,\n    TxnDomainRejectionError,\n    TxnFragment,\n",
)
sub(
    TASKS,
    '_HEAL_SKIPPED_EVENT = "task.backfill.straggler_skipped"\n',
    '_HEAL_PHANTOM_HEAD_EVENT = "task.backfill.straggler_phantom_head"\n'
    '_HEAL_CHAIN_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n'
    '_HEAL_CHUNK_REJECTED_EVENT = "task.backfill.straggler_chunk_rejected"\n',
)
sub(
    TASKS,
    '_CLAIM_LOST_MESSAGE = "task claim lost its compare-and-set"\n',
    '_CLAIM_LOST_THROW = "claim_lost:"\n',
)
sub(
    TASKS,
    "            throw_message=_CLAIM_LOST_MESSAGE,\n",
    '            throw_message=f"{_CLAIM_LOST_THROW}{task_id}",\n',
)
sub(
    TASKS,
    '''        except SurrealStoreError:
            fresh = await self._select_row(task_id)
            if fresh is None:
                raise
            if await self._still_claimable(fresh, blocked_by):
                raise

        # The winner''',
    '''        except TxnClaimLostError:
            pass  # a ROUTINE loss (am-3 §3): typed, never text-matched; the owner read decides

        # The winner''',
)
sub(
    TASKS,
    "        await self._reanchor_stragglers()\n        await self._backfill_blocks_edges()\n",
    "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
)
sub(
    TASKS,
    '''        fixed = _count(0)
        per = _count(1) - fixed''',
    '''        fixed = _count(0)
        per = _count(1) - fixed
        # (the ONE counting function is _composed_statement_count; _count routes through it)''',
)
sub(
    TASKS,
    '''            return sum(len(fragment.statements) for fragment in fragments)

        fixed = _count(0)''',
    '''            return TaskLedger._composed_statement_count(fragments)

        fixed = _count(0)''',
)
sub(
    TASKS,
    "class TransitiveBlockers(BaseModel):\n",
    '''class StragglerHealPackerError(TaskLedgerError):
    """ONE straggler's heal fragments alone exceed the transaction cap — a packer bug (am-3 §1)."""


class TransitiveBlockers(BaseModel):
''',
)

# The heal: replace the single-transaction body with the am-3 packer (whole method).
start_marker = "    async def _reanchor_stragglers(self) -> None:\n"
end_marker = '        logger.info(_HEAL_EVENT, extra={"database": self._database, "count": len(healed)})'
src = sources[TASKS]
start = src.index(start_marker)
end = src.index(end_marker, start) + len(end_marker)
HEAL = '''    @staticmethod
    def _composed_statement_count(fragments: Sequence[TxnFragment]) -> int:
        """THE one statement counter (am-3 §1): the count ``compose`` checks against its hard cap."""
        return sum(len(fragment.statements) for fragment in fragments)

    @staticmethod
    def _heal_delete_fragment(olds: Mapping[str, Sequence[str]], prefix: str) -> TxnFragment:
        """One ``DELETE`` per distinct superseded blocker in a chunk, scoped to that chunk's rows."""
        statements: list[str] = []
        params: dict[str, Any] = {}
        for index, (old, dependents) in enumerate(sorted(olds.items())):
            statements.append(
                f"DELETE {BLOCKS_RELATION} WHERE in = ${prefix}{index}_in AND out IN ${prefix}{index}_out"
            )
            params[f"{prefix}{index}_in"] = RecordID(TASK_TABLE, old)
            params[f"{prefix}{index}_out"] = [RecordID(TASK_TABLE, d) for d in dependents]
        return TxnFragment(statements=statements, params=params)

    @staticmethod
    def _heal_row_fragments(
        dependent: str, moves: Sequence[tuple[str, str]], heads: Sequence[str], at: str, prefix: str
    ) -> list[TxnFragment]:
        fragments = TaskLedger._reanchor_fragments(
            [(dependent, old, head) for old, head in moves],
            actor=_HEAL_ACTOR, at=at, reason=_HEAL_REASON, prefix=prefix,
        )
        if heads:
            fragments.append(TaskLedger._relate_fragment([(h, dependent) for h in heads]))
        return fragments

    async def _reanchor_stragglers(self) -> None:  # noqa: PLR0912, PLR0915 - reference build only
        """Boot heal (am-1 R2; am-2 (b) as corrected by am-3 §1/§2/§5): a GREEDY packer sized by the
        heal's OWN composed count; a chunk's DOMAIN rejection is isolated; store faults RAISE."""
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE"
            )
        )
        successor = {str(r.get(_ID_KEY)): str(r.get(_COL_SUPERSEDED_BY)) for r in rows}
        if not successor:
            return
        stragglers = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_BLOCKED_BY} CONTAINSANY $hs_ids",
                {"hs_ids": sorted(successor)},
            )
        )
        if not stragglers:
            return

        def _head(start: str) -> tuple[str, bool]:
            seen = {start}
            current = successor[start]
            while current in successor:
                if current in seen:
                    return current, True
                seen.add(current)
                current = successor[current]
            return current, False

        chain = {old: _head(old) for old in successor}
        existing = await resolve_existing_rows(
            self._query, TASK_TABLE, sorted({head for head, cyclic in chain.values() if not cyclic})
        )
        plans: list[tuple[str, list[tuple[str, str]], list[str]]] = []
        for straggler in sorted(stragglers, key=lambda r: str(r.get(_ID_KEY))):
            dependent = str(straggler.get(_ID_KEY))
            columns = [str(b) for b in (straggler.get(_COL_BLOCKED_BY) or ())]
            final = list(columns)
            moves: list[tuple[str, str]] = []
            heads: list[str] = []
            skip = False
            for old in dict.fromkeys(b for b in columns if b in successor):
                head, cyclic = chain[old]
                if cyclic:
                    logger.warning(
                        _HEAL_CHAIN_CYCLE_EVENT,
                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    continue
                if head not in existing:
                    logger.warning(
                        _HEAL_PHANTOM_HEAD_EVENT,
                        extra={
                            "database": self._database,
                            "task_id": dependent,
                            "blocker_id": old,
                            "phantom_head_id": head,
                        },
                    )
                    skip = True
                    continue
                moves.append((old, head))
                if head not in final:
                    heads.append(head)
                final = list(dict.fromkeys(head if b == old else b for b in final))
            if moves and not skip:
                plans.append((dependent, moves, heads))
        if not plans:
            return
        at = datetime.now(UTC).isoformat()
        cap = _txn_module.TXN_STATEMENT_HARD_CAP
        chunks: list[list[tuple[str, list[tuple[str, str]], list[str]]]] = []
        current: list[tuple[str, list[tuple[str, str]], list[str]]] = []
        current_olds: set[str] = set()
        current_count = 0
        for plan in plans:
            dependent, moves, heads = plan
            row_cost = self._composed_statement_count(
                self._heal_row_fragments(dependent, moves, heads, at, "hpk")
            )
            olds = {old for old, _head_id in moves}

            def _delete_cost(new_olds: set[str], row: str = dependent) -> int:
                return self._composed_statement_count(
                    [self._heal_delete_fragment({o: [row] for o in new_olds}, "hpd")]
                )

            added = row_cost + _delete_cost(olds - current_olds)
            if current and current_count + added > cap:
                chunks.append(current)
                current, current_olds, current_count = [], set(), 0
                added = row_cost + _delete_cost(olds)
            if added > cap:
                raise StragglerHealPackerError(
                    f"straggler {render_attributed(dependent)}'s heal alone composes {added} statements, "
                    f"over the {cap}-statement cap — a packer bug, refused loudly"
                )
            current.append(plan)
            current_olds |= olds
            current_count += added
        if current:
            chunks.append(current)
        healed = 0
        for index, chunk in enumerate(chunks):
            by_old: dict[str, list[str]] = {}
            pairs: list[tuple[str, str, str]] = []
            relates: list[tuple[str, str]] = []
            for dependent, moves, heads in chunk:
                for old, head in moves:
                    by_old.setdefault(old, []).append(dependent)
                    pairs.append((dependent, old, head))
                relates.extend((head, dependent) for head in heads)
            fragments = [
                self._heal_delete_fragment(by_old, f"hc{index}d"),
                *self._reanchor_fragments(
                    pairs, actor=_HEAL_ACTOR, at=at, reason=_HEAL_REASON, prefix=f"hc{index}r"
                ),
            ]
            if relates:
                fragments.append(self._relate_fragment(relates))
            try:
                await self._apply(fragments)
            except TxnDomainRejectionError:
                logger.warning(
                    _HEAL_CHUNK_REJECTED_EVENT,
                    extra={
                        "database": self._database,
                        "chunk": index,
                        "rows": [plan[0] for plan in chunk],
                    },
                )
                continue
            healed += len(chunk)
        if healed:
            logger.info(
                _HEAL_EVENT,
                extra={"database": self._database, "count": healed, "chunks": len(chunks)},
            )'''
sources[TASKS] = src[:start] + HEAL + src[end:]

sub(TXN, "def _classify_engine_error(raw_result: object) -> str:\n",
    "def _classify_engine_error(raw_result: object) -> str:  # noqa: PLR0911 - reference build only\n")

for path, text in sources.items():
    path.write_text(text)
print("ref58-r2 deltas applied:", TASKS, TXN)
```

### `wb58r2.py` (md5 `cb34783a4245cdd33f4a274814c731eb`)
```python
#!/usr/bin/env python3
"""contract-58-r2 WRONG-BUILD driver — declare-then-diff BOTH ways, over contract-58-r2's reference.

Usage (from the scratch tree root): uv run python wb58r2.py [BUILD ...]
Every build is a list of (file, anchor, replacement) edits, each anchor asserted to occur EXACTLY
once (#194: a mutation that does not land is a loud failure).  Adversary-58's own builds
(``wrong_builds.py`` md5 790e0309) are reused VERBATIM where their anchors still apply to this
reference; heal/claim builds are re-expressed (suffix ``r``) because amendment 3 reshaped the heal.

DECLARED sets were written 2026-09-26 BEFORE the first run of each build (node ids from
``pytest --collect-only``, not from output).  Modes: ``exact`` = observed RED set must EQUAL the
declared set (unexpected reds AND declared-but-green both fail); ``include`` = every declared id must
be RED, extra reds are LISTED (used only for adversary K-builds already killed by the r1 contract,
re-run as a regression check — stated, never passed off as an exact proof).  ``hang`` = the build
must exceed the timeout (rc 124).  Files are restored byte-exact after every build (md5 checked).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "adv"))
from wrong_builds import BUILDS as ADV  # noqa: E402  (adversary-58's verbatim builds)

T = "loremaster/loremaster/tasks.py"
X = "loremaster/loremaster/store/_txn.py"
F = "loremaster/tests/_task_fakes.py"
SCH = "loremaster/loremaster/store/surreal_schema.py"

P = "loremaster/tests/test_reanchor_58_r2_probes.py"
SC = "loremaster/tests/test_reanchor_58_r2_scale.py"
A2 = "loremaster/tests/test_reanchor_58_r2_am2.py"
RU = "loremaster/tests/test_reanchor_58_r2_rulings.py"
S = "loremaster/tests/test_supersede_reanchor_58.py"
G = "loremaster/tests/test_task_guarded_shell_58.py"
PP = "loremaster/tests/test_task_claimable_partition_58.py"
D = "scripts/test_forgery_door_sweep.py"
CR = "loremaster/tests/test_reanchor_58_r2_cas_runtime.py"
RS = "loremaster/tests/test_retry_seam.py"
RS_CLASSES = [f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention",
              f"{RS}::TestTheClassKeyedIndexPartitionsEveryCASHandler",
              f"{RS}::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD"]
SCOPE = [P, SC, A2, RU, S, G, PP, D, CR, *RS_CLASSES]

K_TEST = f"{RU}::TestTheHubCapFollowsKAcrossFloorBoundaries::test_at_K_the_accessor_is_the_composed_cap_cap_succeeds_and_cap_plus_1_teaches"
DOOR = f"{RU}::TestAHealStoreFaultIsLOUD::test_every_heal_door_after_the_backfill_RAISES"
PACK = f"{RU}::TestTheHealPacksByItsOwnComposedCount"
CLAIMLOG = f"{RU}::TestAClaimLossIsDEBUGNeverAnAlarm"
PR = {n: f"{P}::{name}" for n, name in [
    (1, "test_PR1_a_genuine_store_fault_is_not_laundered_into_the_R1_retry_teaching"),
    (2, "test_PR2_the_cap_moves_with_K_across_a_floor_boundary"),
    (3, "test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once"),
    (4, "test_PR4_a_straggler_already_naming_the_head_gets_ONE_entry_and_ONE_edge"),
    (5, "test_PR5_a_phantom_chain_head_does_not_fail_the_boot"),
    (6, "test_PR6_status_open_with_a_limit_is_not_short_while_claimable_rows_exist"),
    (7, "test_PR7_a_WONTFIX_predecessor_reports_its_reblocked_dependent"),
    (8, "test_PR8_a_dependent_on_a_legacy_loop_does_not_block_the_supersede"),
    (10, "test_PR10_a_routine_claim_loss_logs_no_ERROR"),
    (12, "test_PR12_the_note_at_is_the_supersede_time"),
    (13, "test_PR13_the_task_WARN_rides_the_ONE_telemetry_policy"),
    (14, "test_PR14_the_accessor_follows_the_shared_hard_cap"),
    (15, "test_PR15_a_superseded_by_loop_does_not_hang_the_boot"),
]}
PR11 = [f"{P}::test_PR11_production_containment_statements_are_index_served[{i}]"
        for i in ("direct_dependents", "R1_closing_guard_count", "heal_containsany")]
PR16 = f"{SC}::test_PR16_a_hub_at_the_accessors_cap_with_K3_is_never_the_bare_compose_error"
PR17 = f"{SC}::test_PR17_the_boot_heal_at_scale_does_not_fail_the_boot"
PR18R2 = f"{A2}::test_PR18r2_cap_plus_one_of_ONE_blocker_heals_in_the_PACKERS_predicted_chunks"
PR19 = f"{A2}::test_PR19_cap_plus_one_stragglers_over_TEN_blockers_all_heal_in_ONE_boot"
PR20 = f"{A2}::test_PR20_owner_query_serves_a_held_superseded_row_and_status_excludes_it"
RU_SIX = f"{PACK}::test_cap_plus_1_stragglers_over_SIX_blockers_all_heal_in_ONE_boot_every_chunk_within_the_cap"
RU_PAD = f"{PACK}::test_MUTATION_padding_the_shell_moves_the_packer_AND_the_accessor"
RU_REJ = f"{RU}::TestAHealStoreFaultIsLOUD::test_a_chunk_DOMAIN_rejection_is_isolated_WARNED_and_healed_next_boot"
RU_ORDER = f"{RU}::TestAHealStoreFaultIsLOUD::test_the_heal_READS_what_the_backfill_minted_in_the_SAME_boot"
RU_PHANTOM = f"{RU}::TestAPhantomChainHeadIsSkippedAndRECORDED::test_phantom_head_skipped_recorded_every_boot_sibling_healed_and_hand_fix_heals"
RU_CYCLE = f"{RU}::TestASupersededByCycleIsBoundedAndRECORDED::test_a_cycle_is_recorded_each_boot_and_never_rewrites_the_straggler"
RU_8WAY = f"{CLAIMLOG}::test_an_8_way_race_logs_NO_warning_or_error_for_its_7_losers"
RU_TRANS = f"{CLAIMLOG}::test_CONTROL_a_lost_TRANSITION_race_still_logs_at_WARNING"
RU_TYPED = f"{CLAIMLOG}::test_the_ledger_catches_the_TYPE_never_the_text"
RU_LOOP = f"{RU}::TestOnlyACycleThroughXPrimeIsRefused::test_the_legacy_loop_is_untouched_and_Y_follows_the_work"
RU_EXPLICIT = f"{RU}::TestOnlyACycleThroughXPrimeIsRefused::test_CONTROL_a_successor_explicitly_blocked_by_its_dependent_is_REFUSED_whole"
RU_INHERIT = f"{RU}::TestOnlyACycleThroughXPrimeIsRefused::test_CONTROL_an_INHERITED_blocker_that_closes_a_loop_through_X_prime_is_REFUSED"
RU_RELATE = f"{RU}::TestEveryRELATEComesFromTheSharedFragment::test_the_supersede_composes_only_shared_fragment_RELATEs"
RU_RUNTIME = f"{RU}::TestEveryComposedGuardedWriteCameFromTheShell::test_every_verb_composes_guarded_writes_only_through_the_shell"
RS_DOORS_EXACT = f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set"
RS_TYPED_EXACT = f"{RS}::TestTheClassKeyedIndexPartitionsEveryCASHandler::test_the_TYPED_catches_match_their_canonical_set"
RS_GUARD_TRANSITION = f"{RS}::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_every_door_guards_the_typed_error_ABOVE_its_rollback_handler[tasks.py::transition]"
RS_UNREAD_TRANSITION = f"{RS}::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_transactional_doors_never_re_read_after_exhaustion[tasks-transition]"
CR_PARAM = f"{CR}::TestExhaustedContentionPropagatesUNREADFromEveryCASVerb::test_the_typed_error_propagates_unread_and_a_real_loss_is_the_ruled_verdict"
CR_HEAL = f"{CR_PARAM}[tasks.py::_reanchor_stragglers]"
CR_DRIVEN = f"{CR}::TestTheDrivenSetIsTheDerivedSet::test_every_derived_CAS_verb_has_a_driver_and_every_driver_a_derived_verb"
RU_HIER = f"{RU}::TestTheClaimLostHierarchy::test_the_claim_lost_class_cannot_hold_exhausted_contention"
RU_FAKE = f"{RU}::TestTheFakeReanchorsInLockstepWithTheReal::test_a_done_X_reanchors_and_reblocks_on_both[fake]"
G_ONE = f"{G}::TestEachLedgerModuleHasExactlyONEGuardedAppendProducer"
G_PARAM = f"{G}::TestParamNamesDoNotCollideAcrossComposedShells::test_three_reanchors_the_stamp_and_two_successor_edges_compose"
G_LOUD = f"{G}::TestAClaimThatFailsForANonCASReasonIsLOUD::test_an_injected_rollback_on_a_CLAIMABLE_row_raises_rather_than_losing"
S_HEAL = f"{S}::TestTheBootHealReanchorsStragglers"
D_LOUD = f"{D}::TestTheDoorSweepOverTheRealLedger::test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD"
D_SWALLOW = f"{D}::TestTheDoorSweepOverTheRealLedger::test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT"


def adv(name: str) -> list[tuple[str, str, str]]:
    return [(T, old, new) for old, new in ADV[name]]


CLONE_METHOD = '''    @staticmethod
    def _composed_statement_count(fragments: Sequence[TxnFragment]) -> int:'''

BUILDS: dict[str, dict] = {
    # ---- adversary survivors whose anchors still apply (verbatim) ------------------------------
    "WB1": {"edits": adv("WB1_launder_any_rollback_as_R1"), "mode": "exact", "red": [PR[1]]},
    "WB2a": {"edits": adv("WB2a_legit_two_statement_R1_guard"), "mode": "exact", "red": []},
    "WB2": {"edits": adv("WB2_cap_ignores_K_on_the_legit_layout"), "mode": "exact",
            "red": [PR[2], PR16, f"{K_TEST}[3]", f"{K_TEST}[per]", f"{K_TEST}[per+1]"]},
    "WB7": {"edits": adv("WB7_130_client_side_postfilter"), "mode": "exact", "red": [PR[6]]},
    "WB8": {"edits": adv("WB8_reblocked_done_only"), "mode": "exact", "red": [PR[7]]},
    "WB9": {"edits": adv("WB9_cycle_minted_all_pending"), "mode": "exact", "red": [PR[8], RU_LOOP]},
    "WB14": {"edits": adv("WB14_warn_threshold_cloned"), "mode": "exact", "red": [PR[13]]},
    "WB15": {"edits": adv("WB15_literal_hard_cap_copy"), "mode": "exact", "red": [PR[14]]},
    "WB16": {"edits": adv("WB16_note_at_constant"), "mode": "exact", "red": [PR[12]]},
    "K16": {"edits": adv("K16_dependent_relates_hand_rolled"), "mode": "exact", "red": [RU_RELATE]},
    "WB18": {"edits": adv("WB18_owner_filter_excludes_superseded"), "mode": "exact", "red": [PR20]},
    "K4": {"edits": adv("K4_cycle_over_unrewired_graph"), "mode": "exact",
           "red": [f"{S}::TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed",
                   f"{S}::TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_REFUSED_supersede_the_backfill_mints_nothing",
                   RU_EXPLICIT, RU_INHERIT]},
    "K10": {"edits": adv("K10_heal_stops_at_first_hop"), "mode": "exact",
            "red": [f"{S_HEAL}::test_a_three_hop_chain_reanchors_to_the_HEAD",
                    f"{S_HEAL}::test_a_DONE_head_frees_the_straggler", RU_CYCLE]},
    # ---- adversary heal/claim builds RE-EXPRESSED over amendment 3's heal (§DEVIATIONS) --------
    "WB3r": {"edits": [(T, "            healed += len(chunk)\n",
                        "            healed += sum(len(plan[1]) for plan in chunk)  # WB3r: pairs\n")],
             "mode": "exact", "red": [PR[3]]},
    "WB4r": {"edits": [(T, "                final = list(dict.fromkeys(head if b == old else b for b in final))\n",
                        "                final = list(dict.fromkeys(head if b == old else b for b in final))\n"
                        "                break  # WB4r: first superseded blocker only\n")],
             "mode": "exact", "red": [PR[3]]},
    "WB5r": {"edits": [(T, "                if head not in final:\n                    heads.append(head)\n",
                        "                if True:  # WB5r\n                    heads.append(head)\n")],
             "mode": "exact", "red": [PR[4]]},
    "WB6r": {"edits": [(T, "                if head not in existing:\n", "                if False:  # WB6r\n")],
             "mode": "exact", "red": [RU_PHANTOM]},
    "WB12r": {"edits": [(T, '_CLAIM_LOST_THROW = "claim_lost:"\n',
                         '_CLAIM_LOST_THROW = "claim_lost:"\n'
                         '_ASSIGN_GUARD_FMT = "IF array::len(${var}) == 0 {{ THROW \'{msg}\' }}"\n'),
                        (T, CLONE_METHOD, '''    @staticmethod
    def _assign_fragment(task_id: str, owner: str) -> TxnFragment:
        """WB12r: a 57-shaped 4th hand-rolled guarded append whose guard lives in a module constant."""
        return TxnFragment(
            statements=[
                f"LET $asg_upd = (UPDATE type::record('{TASK_TABLE}', $asg_id) SET owner = $asg_owner, "
                f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [$asg_ev])",
                _ASSIGN_GUARD_FMT.format(var="asg_upd", msg="assign lost"),
            ],
            params={"asg_id": task_id, "asg_owner": owner, "asg_ev": {}},
        )

''' + CLONE_METHOD)],
              "mode": "exact",
              "red": [f"{G_ONE}::test_every_guarded_append_ledger_has_ONE_producer",
                      f"{G_ONE}::test_the_task_ledgers_one_producer_IS_the_shell"]},
    "WB17r": {"edits": [(T, "                if current in seen:\n                    return current, True\n", "")],
              "mode": "hang", "red": [PR[15], RU_CYCLE]},
    "WB17b": {"edits": [(T, "                if current in seen:\n                    return current, True\n",
                         "                if current in seen:\n                    return current, False  # WB17b\n")],
              "mode": "exact", "red": [RU_CYCLE]},
    "K7r": {"edits": [(T, '''            fragments.append(
                TaskLedger._guarded_append_fragment(
                    dependent,
                    event=note,''', '''            fragments.append(
                TaskLedger._private_reanchor(
                    dependent,
                    event=note,'''),
                      (T, CLONE_METHOD, '''    @staticmethod
    def _private_reanchor(row_id: str, *, event: Any, set_parts: Any, params: Any,
                          where_conjuncts: Any, throw_message: str, namespace: str) -> TxnFragment:
        """K7r: routing-not-sharing — a private guarded append for the re-anchor."""
        merged = {**params, f"{namespace}_id": row_id, f"{namespace}_ev": dict(event)}
        return TxnFragment(
            statements=[
                f"LET ${namespace}_upd = (UPDATE type::record('{TASK_TABLE}', ${namespace}_id) SET "
                f"{', '.join(set_parts)}, updated_at = time::now(), provenance.events += [${namespace}_ev] "
                f"WHERE " + " AND ".join(f"({c})" for c in where_conjuncts) + ")",
                f"IF array::len(${namespace}_upd) == 0 {{ THROW '{throw_message}' }}",
            ],
            params=merged,
        )

''' + CLONE_METHOD)],
            "mode": "exact",
            "red": [f"{G}::TestSharingIsProvenByMutationALWAYSTHROW::test_the_REANCHOR_routes_through_the_shell",
                    f"{G}::TestSharingIsProvenByMutationTHEAPPEND::test_transition_stamp_claim_and_reanchor_events_all_come_from_the_shell",
                    f"{G}::TestSharingIsProvenByMutationTHEAPPEND::test_the_BOOT_HEAL_note_comes_from_the_shell_too",
                    f"{G_ONE}::test_every_guarded_append_ledger_has_ONE_producer",
                    f"{G_ONE}::test_the_task_ledgers_one_producer_IS_the_shell",
                    G_PARAM,
                    RU_PAD, RU_RUNTIME]},  # r1's S padding pin REMOVED (batch 1: the stamp moves the cap)
    "K9r": {"edits": [(T, "        if not stragglers:\n            return\n",
                       "        if not stragglers:\n"
                       '            logger.info(_HEAL_EVENT, extra={"database": self._database, "count": 0, "chunks": 0})\n'
                       "            return\n")],
            "mode": "exact",
            "red": [f"{S_HEAL}::test_a_second_boot_changes_NOTHING_and_is_SILENT", RU_SIX, PR19]},
    "K11r": {"edits": [(T, "            healed += len(chunk)\n",
                        "            healed = len({h for plan in chunk for _o, h in plan[1]})  # K11r: chains\n")],
             "mode": "exact",
             "red": [f"{S_HEAL}::test_a_boot_heals_every_straggler_to_its_successor_and_COUNTS_them",
                     PR[3], RU_SIX, PR18R2, PR19, RU_PAD, RU_REJ]},
    "K17r": {"edits": [(T, "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
                        "        await self._reanchor_stragglers()\n        await self._backfill_blocks_edges()\n")],
             "mode": "exact", "red": [D_SWALLOW, f"{DOOR}[store]", f"{DOOR}[transport]", RU_ORDER, RU_RUNTIME]},
    # ---- amendment 3 wrong builds ----------------------------------------------------------------
    "AM2L": {"edits": [(T, "            if current and current_count + added > cap:\n",
                        "            if current and len(current) >= self.max_reanchor_dependents(0):  # AM2L\n")],
             "mode": "exact", "red": [RU_SIX, PR19, PR18R2]},
    "FO1": {"edits": [(T, "            except TxnDomainRejectionError:\n                logger.warning(\n                    _HEAL_CHUNK_REJECTED_EVENT,",
                       "            except SurrealStoreError:  # FO1: fail-open apply\n                logger.warning(\n                    _HEAL_CHUNK_REJECTED_EVENT,")],
            "mode": "exact", "red": [f"{DOOR}[store]", f"{DOOR}[transport]", CR_HEAL]},
    "FO2": {"edits": [(T, "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
                       "        await self._backfill_blocks_edges()\n        try:\n            await self._reanchor_stragglers()\n"
                       "        except Exception:  # noqa: BLE001 - FO2: am-2's over-broad fail-open\n"
                       '            logger.warning("task.backfill.straggler_heal_failed")\n')],
            "mode": "exact", "red": [D_LOUD, D_SWALLOW, f"{DOOR}[store]", f"{DOOR}[transport]", CR_HEAL]},
    "CL1": {"edits": [(X, "    if _classify_engine_error(root_cause.raw_result) == _ERROR_CLASS_CLAIM_LOST:\n        level = logging.DEBUG\n    elif",
                       "    if")],
            "mode": "exact", "red": [RU_8WAY]},
    "CL2": {"edits": [(X, "    elif text.startswith(_THROW_ROOT_MARKER):\n        level = logging.WARNING\n", "")],
            "mode": "exact", "red": [RU_TRANS]},
    "CL3": {"edits": [(T, "        except TxnClaimLostError:\n            pass",
                       '        except SurrealStoreError as error:  # CL3: text-matching\n'
                       '            if "claim lost" not in str(error):\n                raise')],
            "mode": "exact", "red": [RU_TYPED, RS_DOORS_EXACT, RS_TYPED_EXACT]},
    "CL4": {"edits": [(T, '            throw_message=f"{_CLAIM_LOST_THROW}{task_id}",\n',
                       '            throw_message="task claim lost its compare-and-set",  # CL4\n'),
                      (T, "        except TxnClaimLostError:\n            pass",
                       "        except TxnDomainRejectionError:  # CL4: untyped loss\n            pass")],
            "mode": "exact", "red": [RU_8WAY, RU_TYPED, G_LOUD]},
    "FAKE": {"edits": [(F, "        for dependent in list(self.db.tasks.values()):\n            if dependent.id == new_id",
                        "        for dependent in []:  # FAKE: lockstep removed\n            if dependent.id == new_id")],
             "mode": "exact", "red": [RU_FAKE]},
    "IDX": {"edits": [(SCH, '''    statements.append(
        _plain_index(TASK_TABLE, f"{TASK_TABLE}_{_TASK_BLOCKED_BY_FIELD}", (f"{_TASK_BLOCKED_BY_FIELD}.*",))
    )''', "")], "mode": "exact", "red": PR11},
}
# ---- amendment 5 (C)+(B) wrong builds --------------------------------------------------------------
BUILDS.update({
    "CLDOOR5": {"edits": [(T, "        except TxnClaimLostError:\n            pass", "        except SurrealStoreError:  # CLDOOR5\n            pass")],
                "mode": "exact", "red": [RS_DOORS_EXACT, RS_TYPED_EXACT, G_LOUD, RU_TYPED]},
    "CLDOOR5b": {"edits": [(T, "        except TxnContentionExhaustedError:\n            raise\n        except TxnClaimLostError:\n            pass",
                            "        except SurrealStoreError:  # CLDOOR5b: broad, and NO guard above it\n            pass")],
                 "mode": "exact", "red": [RS_DOORS_EXACT, RS_TYPED_EXACT, G_LOUD, RU_TYPED, f"{CR_PARAM}[tasks.py::claim_task]"]},
    "TRNOGUARD": {"edits": [(T, "        except TxnContentionExhaustedError:\n            # A genuine conflict outlived the retry budget — this is NOT a lost\n"
                                "            # CAS (finding #102): the row may be untouched and this transition\n"
                                "            # perfectly legal, so it must never be re-read and misreported as\n"
                                "            # an IllegalTransitionError below. Propagate untouched.\n            raise\n", "")],
                  "mode": "exact", "red": [RS_GUARD_TRANSITION, RS_UNREAD_TRANSITION, f"{CR_PARAM}[tasks.py::transition]"]},
    "STALE": {"edits": [(T, CLONE_METHOD, '''    async def _assign(self, task_id: str, owner: str) -> None:
        """STALE: a NEW guarded-CAS verb (57-shaped) that routes through the shell — with no runtime driver."""
        await self._apply([TaskLedger._guarded_append_fragment(
            task_id, event=None, set_parts=["owner = $asg_owner"], params={"asg_owner": owner},
            where_conjuncts=["owner IS NONE"], throw_message="assign lost",
        )])

''' + CLONE_METHOD)],
              "mode": "exact", "red": [CR_DRIVEN, f"{CR_PARAM}[tasks.py::_assign]", RU_RUNTIME]},
    # declared AFTER the final run (2026-09-26 ~19:00Z): CLREPARENT showed a re-parenting under the BASE
    # store error cannot flip the typed catch (exhaustion is still not a TxnClaimLostError); the flip the
    # index must see is a catch WIDENED to a contention-bearing class — here, a tuple.
    "CLTUPLE": {"edits": [(T, "        except TxnClaimLostError:\n            pass", "        except (TxnClaimLostError, SurrealStoreError):  # CLTUPLE\n            pass")],
                "mode": "exact", "red": [RS_DOORS_EXACT, RS_TYPED_EXACT, G_LOUD, RU_TYPED]},
    "CLREPARENT": {"edits": [(X, "class TxnClaimLostError(TxnDomainRejectionError):", "class TxnClaimLostError(SurrealStoreError):")],
                   "mode": "exact", "red": [RU_HIER, RS_DOORS_EXACT, RS_TYPED_EXACT]},
})

# ---- adversary K-builds (already killed by the r1 contract): regression check, INCLUDE mode --------
for name, must in {
    "K1_reanchor_outside_the_supersede_txn": [f"{S}::TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES_retry"],
    "K2_skip_terminal_dependents": [f"{S}::TestSupersedeOfATerminalPredecessorA1::test_every_status_is_rewired_including_claimed"],
    "K3_literal_cap": [PR[14], f"{K_TEST}[2]"],
    "K5_no_dedupe_in_rewrite": [f"{S}::TestTheRewireDedupes::test_a_legacy_duplicate_X_X_becomes_ONE_successor_entry_and_ONE_edge"],
    "K6_note_actor_missourced": [f"{S}::TestEachDependentCarriesTheReanchorNote::test_exactly_ONE_new_event_per_dependent_naming_X_X_prime_and_the_SUPERSEDER"],
    "K8_130_partition_unchanged": [PR[6], PR20],
    "K12_R1_auto_retry": [f"{S}::TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES_retry"],
    "K13_reblocked_ignores_other_blockers": [f"{S}::TestSupersedeOfATerminalPredecessorA1::test_reblocked_names_exactly_the_previously_CLAIMABLE_dependents"],
    "K14_no_R1_closing_guard": [f"{S}::TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES_retry"],
    "K15_claim_cas_on_stale_preread": [f"{S}::TestSupersedeOfATerminalPredecessorA1::test_a_claim_whose_PRE_READ_predates_the_reanchor_can_NOT_win"],
}.items():
    BUILDS[name.split("_")[0]] = {"edits": adv(name), "mode": "include", "red": must}



def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def run(name: str, spec: dict) -> dict:
    files = {Path(f) for f, _o, _n in spec["edits"]}
    backup = {f: f.read_bytes() for f in files}
    digests = {f: md5(f) for f in files}
    try:
        for file, old, new in spec["edits"]:
            text = Path(file).read_text()
            count = text.count(old)
            assert count == 1, f"{name}: anchor found {count}x in {file}: {old[:80]!r}"
            Path(file).write_text(text.replace(old, new))
        for f in files:
            assert md5(f) != digests[f], f"{name}: {f} unchanged — the mutation did not land"
        timeout = 240 if spec["mode"] == "hang" else 1500
        proc = subprocess.run(
            ["timeout", "-s", "KILL", str(timeout), "uv", "run", "pytest", "-n", "12", "-q", "-rfE",
             "-p", "no:cacheprovider", *SCOPE, *spec.get("extra_scope", [])],
            capture_output=True, text=True, check=False,
        )
        out = proc.stdout + proc.stderr
        (HERE / "wb_out").mkdir(exist_ok=True)
        (HERE / "wb_out" / f"{name}.log").write_text(out)
        # Only pytest's short-summary lines name a node id ("FAILED a::b - msg"); a captured LOG line
        # ("ERROR    loremaster.store._txn:…") also starts with "ERROR " — the first run's parser bug.
        reds = sorted({line.split(" ", 1)[1].split(" - ")[0].strip() for line in out.splitlines()
                       if line.startswith(("FAILED ", "ERROR ")) and "::" in line.split(" ", 2)[1]})
        tail = [line for line in out.splitlines() if " passed" in line or " failed" in line][-1:]
        declared = sorted(spec["red"])
        if spec["mode"] == "hang":
            ok = proc.returncode in (124, 137, -9)
            verdict = f"HANG rc={proc.returncode}" if ok else f"NO HANG rc={proc.returncode}"
            return {"build": name, "ok": ok, "verdict": verdict, "tail": tail}
        unexpected = sorted(set(reds) - set(declared))
        still_green = sorted(set(declared) - set(reds))
        ok = not still_green and (spec["mode"] == "include" or not unexpected)
        return {"build": name, "mode": spec["mode"], "ok": ok, "declared": len(declared),
                "still_green": still_green, "unexpected": unexpected, "tail": tail}
    finally:
        for f, content in backup.items():
            f.write_bytes(content)
            assert md5(f) == digests[f], f"{name}: {f} NOT restored byte-exact"


def main(selected: list[str]) -> int:
    results = []
    for name, spec in BUILDS.items():
        if selected and name not in selected:
            continue
        result = run(name, spec)
        results.append(result)
        print(json.dumps(result), flush=True)
    failed = [r["build"] for r in results if not r["ok"]]
    print(f"BUILDS NOT PROVEN: {failed or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

### `ast_receipt.py` (md5 `880d05f70c648136dd3092935a223eff`)
```python
#!/usr/bin/env python3
"""AST-equality receipt: each adversary probe function vs the landed function of the same name.

Usage: ast_receipt.py <adversary.py> <landed.py> [<adversary.py> <landed.py> ...]
Compares ast.dump(include_attributes=False) of every top-level (async) function the ADVERSARY file
defines (probes AND helpers) against the landed file's same-named function.  Prints EQUAL / DIFFERENT /
MISSING per name.  Controls (run with --controls): a one-literal mutation of a landed probe must be
DIFFERENT (positive control — the comparator can see a change), and a pure re-wrap (reformatted
whitespace/comments) must be EQUAL (negative control — lint re-wraps are admitted, am-17).
"""
import ast
import sys


def functions(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def compare(adversary: str, landed: str) -> list[tuple[str, str]]:
    a = functions(open(adversary).read())
    b = functions(open(landed).read())
    return [(name, "EQUAL" if b.get(name) == dump else ("MISSING" if name not in b else "DIFFERENT"))
            for name, dump in a.items()]


def controls(adversary: str) -> None:
    src = open(adversary).read()
    name, dump = next(iter(functions(src).items()))
    rewrapped = src.replace("\n\n\n", "\n\n\n# a comment the AST cannot see\n", 1)
    assert functions(rewrapped)[name] == dump, "NEGATIVE CONTROL FAILED: a comment changed the AST"
    mutated = src.replace("assert ", "assert not ", 1)
    changed = [n for n, d in functions(mutated).items() if d != functions(src)[n]]
    assert changed, "POSITIVE CONTROL FAILED: a mutated assertion compared EQUAL"
    print(f"controls OK: re-wrap EQUAL ({name}); one-token mutation DIFFERENT ({changed[0]})")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--controls":
        controls(args[1])
        sys.exit(0)
    bad = 0
    for adversary, landed in zip(args[::2], args[1::2]):
        for name, verdict in compare(adversary, landed):
            print(f"{verdict:9} {landed.rsplit('/', 1)[-1]}::{name}")
            bad += verdict != "EQUAL"
    sys.exit(1 if bad else 0)
```

### `probes/throw_text.py` (md5 `bb85a6a9222103e0a4220ce39cb403e3`)
```python
"""Probe: the raw engine result text of a THROW-rooted rollback vs an ASSERT rollback (3.2.4, :18000 throwaway DB)."""
import asyncio, logging, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, unique_database, drop_database, PRODUCTION_DIM
from loremaster.tasks import TaskLedger
import loremaster

records = []
class H(logging.Handler):
    def emit(self, r): records.append(r)
logging.getLogger("loremaster").addHandler(H()); logging.getLogger("loremaster").setLevel(logging.DEBUG)

async def main():
    print("loremaster.__file__", loremaster.__file__)
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    await ledger.ensure_ready()
    try:
        t = await ledger.create_task("s", "d", blocked_by=[], created_by="p")
        from loremaster.tasks import TxnFragment
        await ledger._apply([ledger._transition_fragment(t, "done", "in_progress", {"actor": "p", "action": "transition", "to": "done", "at": "x"}, None, None)] if False else [TxnFragment(statements=["LET $v = (UPDATE task SET status='x' WHERE false)", "IF array::len($v) == 0 { THROW 'claim_lost:abc' }"], params={})])
    except Exception as e:
        print("RAISED", type(e).__mro__[:3], e)
    try:
        await ledger._apply([TxnFragment(statements=["CREATE task:zz SET status = 'nonsense-status'"], params={})])
    except Exception as e:
        print("RAISED2", type(e).__mro__[:3], e)
    for r in records:
        if r.getMessage() == "store.transaction.rolled_back":
            print(r.levelname, repr(r.engine_result))
    await ledger.close(); await drop_database(env)
asyncio.run(main())
```

### `probes/return_in_txn.py` (md5 `cde3ab7803151ae8a80231ab06dcc70d`)
```python
"""Probe (3.2.4, :18000 throwaway DB): does `RETURN NONE` inside a composed BEGIN…COMMIT stop later statements?"""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, unique_database, drop_database, PRODUCTION_DIM
from loremaster.tasks import TaskLedger
from loremaster.store._txn import TxnFragment

async def main():
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    await ledger.ensure_ready()
    try:
        for label, pad in (("RETURN NONE", "RETURN NONE"), ("LET (control)", "LET $pad = NONE")):
            await ledger._query("DEFINE TABLE IF NOT EXISTS probe_ret SCHEMALESS", {}); await ledger._query("DELETE probe_ret", {})
            await ledger._apply([TxnFragment(statements=["CREATE probe_ret:a SET v = 1", pad, "CREATE probe_ret:b SET v = 2"], params={})])
            rows = await ledger._query("SELECT VALUE record::id(id) FROM probe_ret", {})
            print(f"{label}: rows after = {sorted(rows)}")
    finally:
        await ledger.close(); await drop_database(env)
asyncio.run(main())
```

### `rebuild_ref.sh` (md5 `82655b9bafb53232e94cce312479db04`)
```bash
#!/usr/bin/env bash
# Reset the scratch tree to HEAD, then: 63c patch + §HELD + adversary build_ref58 + contract-58-r2 am-3 deltas
# + the esc1 one-liner (REPORT-contract-58.md §FLAGS 1) + contract-58-r2's test files.
set -euo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/051e3520-9705-4d88-80c5-a1b8b25785f7/scratchpad
T=${1:-$S/ref}
cd $T
git checkout -q -- . && git clean -fdq -e .venv
P63=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f11f841f-5a48-4be4-9ef4-db7b181287ba/scratchpad/builder-63c-i-a-fix.patch
git apply --check -R $P63 2>/dev/null || git apply $P63   # committed at 169925f: plain HEAD already has it
git apply $S/held_r2.patch
python3 $S/adv/build_ref58.py $T >/dev/null
python3 $S/build_ref58_r2.py $T >/dev/null
uv run ruff check -q --fix loremaster/loremaster/tasks.py loremaster/loremaster/store/_txn.py
awk '/^diff --git a\/scripts\/esc1/{f=1} f' $S/ref_r1.patch | git apply
$S/sync.sh $T
md5sum loremaster/loremaster/tasks.py loremaster/loremaster/store/_txn.py loremaster/tests/_task_fakes.py loremaster/loremaster/store/surreal_schema.py
```

### `sync.sh` (md5 `7702388de039c0e20e7ed5bf82454f1d`)
```bash
#!/usr/bin/env bash
# copy contract-58-r2's working files from the shared tree into a scratch tree ($1)
set -euo pipefail
cd /home/ejprice/PycharmProjects/lore
for f in loremaster/tests/_reanchor_58_support.py loremaster/tests/test_task_guarded_shell_58.py \
  loremaster/tests/test_supersede_reanchor_58.py loremaster/tests/test_task_claimable_partition_58.py \
  loremaster/tests/test_reanchor_58_r2_probes.py loremaster/tests/test_reanchor_58_r2_scale.py \
  loremaster/tests/test_reanchor_58_r2_am2.py loremaster/tests/test_reanchor_58_r2_rulings.py \
  scripts/test_forgery_door_sweep.py loremaster/tests/test_reanchor_58_r2_cas_runtime.py \
  loremaster/tests/test_blocks_edge.py loremaster/tests/test_task_read_surface.py ; do cp "$f" "$1/$f"; done
cp /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/051e3520-9705-4d88-80c5-a1b8b25785f7/scratchpad/pending_contracts_r2.yaml "$1/scripts/pending_contracts.yaml"
```

### `run_wb.sh` (md5 `62d6ae9b77d71881343726aa8019a08f`)
```bash
#!/usr/bin/env bash
# Runs the wrong-build driver in its OWN process group; a 5 s watchdog kills that group by its numeric
# PGID (never a name pattern) if MemAvailable drops below 15 GB.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/051e3520-9705-4d88-80c5-a1b8b25785f7/scratchpad
cd $S/sat
# lane: concurrent lore sessions are SAFE since #466 (6566ba6/e6e17d8) — run at -n 12 (MEMORY landmine, 2026-09-26)
setsid uv run python $S/wb58r2.py "$@" >> $S/wb_run.log 2>&1 &
drv=$!
while kill -0 $drv 2>/dev/null; do
  a=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo)
  if [ "$a" -lt 15 ]; then echo "WATCHDOG MemAvailable=${a}G — killing PGID $drv" >> $S/wb_run.log; kill -KILL -- -$drv; fi
  sleep 5
done
wait $drv; echo "DRIVER EXIT $?" >> $S/wb_run.log
```

### `run_full.sh` (md5 `0e6ef4e5406ce61ea45e0b416ec6b70e`)
```bash
#!/usr/bin/env bash
# run_full.sh <tree> <log> <cmd...> — run in its OWN process group; a 5 s watchdog kills that group (numeric PGID)
# below 15 GB MemAvailable (the process TREE, per lead #17068).
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/051e3520-9705-4d88-80c5-a1b8b25785f7/scratchpad
tree=$1; log=$2; shift 2
cd $tree
echo "provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')" > $log
setsid "$@" >> $log 2>&1 &
pid=$!
while kill -0 $pid 2>/dev/null; do
  a=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo)
  if [ "$a" -lt 15 ]; then echo "WATCHDOG MemAvailable=${a}G — killing PGID $pid" >> $log; kill -KILL -- -$pid; fi
  sleep 5
done
wait $pid; echo "EXIT $?" >> $log
```

### `lane_busy.sh` (md5 `6fdbeb9b6ee1bbdfcf6ca1440af66e89`)
```bash
#!/usr/bin/env bash
# Prints lore pytest processes (comm-keyed, never args-text-keyed: #228). Exit 0 = busy, 1 = clear.
me=$$; found=1
for pid in $(ps -eo pid=,comm= | awk '$2 ~ /^(uv|python[0-9.]*|pytest)$/ {print $1}'); do
  [ "$pid" = "$me" ] && continue
  args=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null) || continue
  cwd=$(readlink /proc/$pid/cwd 2>/dev/null)
  case "$args" in *pytest*) ;; *) continue ;; esac
  case "$args $cwd" in *PycharmProjects/lore*|*-home-ejprice-PycharmProjects-lore*) echo "$pid $cwd :: ${args:0:160}"; found=0 ;; esac
done
exit $found
```

### `lane_wait.sh` (md5 `f4e7fe82b42b28f345f3167cfe44ea54`)
```bash
#!/usr/bin/env bash
# Wait (≤90 min) until NO other lore pytest runs — two consecutive clear checks 15 s apart. Exit 97 = timed out.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/051e3520-9705-4d88-80c5-a1b8b25785f7/scratchpad
deadline=$(( $(date +%s) + 5400 )); clear=0
while [ $(date +%s) -lt $deadline ]; do
  if $S/lane_busy.sh >/dev/null; then clear=0; else clear=$((clear+1)); fi
  [ $clear -ge 2 ] && exit 0
  sleep 15
done
exit 97
```
