# REPORT-lead-63b-ii-b — message READ side

`lead-base v6 read`

Wave: 63b-ii-b (message READ side — drain / ack / await / story become governed).
Resume HEAD: `3f69374` (63b-ii-a CLOSED, GO'd). Branch `feat/surreal-unification`.
Lead: Opus 4.8 orchestrator. COMMIT-ONLY (deploy = pkt-65 joint cutover).

## Standing law read receipts
- `lead-base v6 read` (above).
- Repo CLAUDE.md auto-loaded (gates, dogfood, trust doctrine, reach law / INSTRUMENT-0,
  #107/#131 dirty-store law, ONE IMPLEMENTATION, THE RIDER IS PART OF THE RULING).
- Store reference `docs/reference/surrealdb-31-capabilities.md` READ (§2 DML, §3 txns, §4 graph,
  §5 hot rows, §6.4 dangling edges, §8 open hazards). Load-bearing facts for ii-b:
  - §3: one failed statement aborts the WHOLE `BEGIN;…;COMMIT;` txn (execute_transaction checks
    every statement). So drain's ruled one-txn shape (§4.B Reading B) rolls back the served SELECT
    too if the UPDATE fails on any row.
  - §8: `ENFORCED` is LIVE on `to` (`df59f76`) — send-side dangling edges rejected; not a drain
    concern.
  - §2: explicit projection reads missing cols as None; `SELECT *` OMITS a NONE `option<>` col
    (KeyError). read_filter reads MUST use explicit projection over the governed `option<>` cols.
  - §2/§6.6: `IN` inside an `OR` = TableScan trap (#413). read_filter emitter expands IN→per-value
    equalities; drain's `id IN $edges.in` is a top-level AND conjunct (safe), not inside the OR.

## GROUND-TRUTH FINDING (session, by construction) — the DD-3.c drain-UPDATE dirty-store hazard is LIVE
- `to` edge fields (lore, HEAD): session, created_at, seen_at option<datetime>, acked_at
  option<datetime>, `ack_note option<string>` — **now bounded** (test `_old_to_ddl` docstring:
  "the delivery edge as it stood BEFORE ack_note was bounded" ⇒ a cap ASSERT was added by migration).
- `MessageLedger.drain` UPDATE: `UPDATE to SET seen_at=$t WHERE out=$agent AND in IN $ids AND
  seen_at IS NONE RETURN AFTER` (messages.py:1068). `MessageLedger.ack`: `UPDATE to SET acked_at,
  ack_note WHERE acked_at IS NONE AND out=$agent AND in IN $ids` (messages.py:1242).
- ack does NOT require prior drain → a row can have `seen_at IS NONE` AND a stored `ack_note`. A
  LEGACY over-cap `ack_note` (written before the bound; #131 dirty long-lived store) would be
  re-validated when drain's `SET seen_at` touches that row IF SurrealDB re-fires SCHEMAFULL field
  ASSERTs on an UPDATE that sets a different column. That aborts the whole drain → **total inbox
  denial** — the packet-03b DD-3.c class, exactly.
- **This is EMPIRICAL and must be settled by construction (probe), never by reasoning (the #107
  self-sealing-belief trap).** → probe-63b-ii-b settles the mechanism; the Fable sidecar rules the
  mitigation (a design fork that may change §4.B's ruled shape) with the probe's measured evidence.

## WAVE PLAN (pipeline per §5 + brief)
1. probe-63b-ii-b (opus48-worker): extend the ii-a read-filter probe to drain/ack/`to`-edge
   read+UPDATE shapes on :18000 — EXPLAIN plans (no TableScan/IN-in-OR trap) + the DD-3.c
   dirty-`to`-store whole-window UPDATE hazard (construct a legacy over-cap `ack_note` edge, run the
   ruled one-txn drain shape, observe total-denial-or-graceful, with positive controls). Commit
   script + REPORT.
2. Fable design sidecar (general-purpose, model=fable, long-running): rules the drain/ack dirty-store
   fork WITH the probe evidence; confirms render_subject_bound placement on comms reads + the rollup
   capability= bound. Stand-by for follow-ups + the contract fidelity read.
3. contract (Opus) → contract-adversary (MANDATORY) → build (Opus) → cold-audit (Opus REFUTE, FULL
   suite ALONE) → commit. Then 63b-iii.

## State on resume (from INDEX Log + lore_recall)
- 63b-ii-a CLOSED at `3f69374`: send enforcement + SF-63-1 keep + §4.C migrate + corpse
  reconciliation. Cold-audit GO (FULL suite ALONE 11223/0/0, currency 0 RED_ORPHANED).
- Binding ruling: `docs/design/2026-09-09-packet63b-ii-a-owner-resolution-ruling.md`
  (ii-a-titled, GOVERNS ii-b: §3 lifted resolve_principal, §4 requires_capability flips per
  verb, §11.5 the ii-b R6 per-verb driver-table obligation, §11.3 F-DUP).
- ii-b OWNS: F-DUP extraction → `_governed_contract.py`; the read-verb CORPSE (drain ~25 /
  ack ~5 / await ~2 fake sites); the R6 per-verb no-cap-deny table with coverage assertion.
- R2/R3 → 63b-iii (NOT ii-b).

## Sidecar ruling (BINDING) + operator §7 ruling
- Sidecar ruled the drain-UPDATE fork: `docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md`,
  committed `0566587`. **R1: DROP the `to.ack_note` DDL ASSERT** (app cap = ONE implementation); R2:
  `to` is UPDATE-hot ⇒ no constraint a legacy row can violate (pin P2 + P1 inverted dirty-store pin);
  threat model written; DUAL adjudicated (§5); R3 OVERWRITE full-replace at boot (no deploy ordering);
  R6 reachability MOOT for the ruling (lead runs one read-only :18500 count at close-out); R7
  render_subject_bound placement; R8 rollup capability=; #464 (i-b coverage pin blind to
  `AppContext.`-receiver renders → P5, extend the derivation); §9.5 invisible-seq ack → unknown_message
  (P7). Worklist W1–W8 in §10.
- Ground-truthed the ruling's load-bearing schema claims: `_TO_FIELD_SPECS` has EXACTLY one ASSERT
  (ack_note); `_MESSAGE_FIELD_SPECS` carries 5 (thread/grade/body/refs+refs[*]/task_id). #464 confirmed
  directly (`_comms_drain` calls `AppContext._render_comms_drain(...)`, so the i-b `self.`-keyed pin is
  blind). Ruling accepted as binding.
- **OPERATOR RULING (§7, AskUserQuestion, 2026-09-11): "Why not fix it now?" ⇒ FIX the `message`
  DD-3.c class now, in ii-b — NOT pin-only, NOT defer.** Routed back to the standing sidecar to rule
  the SHAPE (per-ASSERT: each dropped store ASSERT needs an app-layer equivalent = ONE IMPLEMENTATION;
  `grade`'s closed-set + `thread`'s requiredness are not length caps — handle explicitly; dirty-store
  pin on the §4.C migrate). This EXPANDS ii-b scope by the operator's own grant.
- ⚠ Comms-discipline event: the §7 follow-up SendMessage to `sidecar-63b-iib` did NOT land (ground-
  truthed: no §7 addendum in the doc, mtime unchanged; the idle notification was a hook-nudge response,
  not my directive — the known push-to-subagent unreliability). Per the comms law (one ping → respawn,
  never stack), TaskStopped `sidecar-63b-iib` and respawned `sidecar-63b-iib-2` (suffixed) with a
  consolidated self-contained §7 brief pointing at the committed ruling `0566587` as its prior work.
  ⚠ two ledger zombies now (probe + old sidecar) — no cross-agent retire verb, cosmetic.

## §7-resolution addendum (§12) + operator process correction
- `sidecar-63b-iib-2` delivered the §7 addendum (§12, §0–§11 byte-intact). Ledger #12003. Headline:
  message DD-3.c = **5 DROP / 0 MOVE / 0 KEEP** — all five ASSERTs app-capped by construction in the
  ONE writer (`MessageLedger.send` prologue: grade→IllegalMessageGradeError, body→MessageBodyError,
  `_reject_oversize_pointers`→refs-count/refs[*]/thread/task_id). R13: `message` is UPDATE-ABLE (§4.C
  migrate) not UPDATE-hot; ∀ invariant P2-m pinned anyway (ONE IMPLEMENTATION). R14: TWO-leg pin
  (Leg A drop-lands-on-asserted-store #107 direction; Leg B real migrate survives 6 violators, DD-3.c
  direction). R15 DUAL adjudicated (D-M1..D-M13). R16 per-table single-writer floor. R17 no deploy
  ordering. W9–W17.
- **LEAD-GROUND-TRUTHED the load-bearing safety claim** (read `MessageLedger.send` + `_reject_oversize_
  pointers`): all five bounds ARE enforced in `send`'s prologue before the write — the "NOT app-capped"
  branch is genuinely EMPTY. Dropping the store ASSERTs loses no enforcement. Addendum accepted binding.
- **LEAD DECISIONS (mine, not operator):** #3 seeder lift `seed_message_legacy` into
  `_governed_contract.py` = ACCEPT (ONE IMPLEMENTATION; grant the file to the contract). #4 P2 ∪ P2-m as
  ONE parametrized pin over `{to, message}` birth-set map = ACCEPT (contract author names it).
- **OPERATOR PROCESS CORRECTION (2026-09-11):** I over-escalated D-M8 (the grade-drop reader-decode
  bound) via AskUserQuestion. Operator: *"The sidecar rules on forks. I am not the consumer. Agents
  are."* ⇒ DESIGN-SHAPE forks within granted scope belong to the Fable sidecar (binding), framed on the
  AGENT-consumer — NOT the operator. The operator gets SCOPE grants (what/whether to build — §7 "fix it
  now" was correctly escalated), permission/destructive/#107-class surprises, and unresolvable
  ambiguity. D-M8 routed back to `sidecar-63b-iib-2` to RULE definitively (both readings: drop-all-5
  vs. keep-grade's-domain-guard), agent-consumer frame. Awaiting its D-M8 ruling.

## D-M8 RULED + design complete
- `sidecar-63b-iib-2` ruled D-M8 (§13, R19 supersedes R12): **KEEP the `grade` ASSERT** — final message
  tally 4 DROP / 1 KEEP / 0 MOVE. Discriminator (a property, not a lean): grade's violation set ≡ the
  reader's own `Literal`-decode rejection set, so the ASSERT fails in the SAME direction as the reader
  (loud cutover refusal, not silent per-agent denial); a length violator IS served → pure DD-3.c → drop.
  Exemption rule installed on both ∀ pins ("is every row this refuses one the reader would refuse
  anyway?"). New: P-G2 (grade DDL≡frozenset≡Literal alignment, mutation-proven), P-G3 (pinned KNOWN
  BOUND: junk-grade row refuses the migrate; 3-step widen/heal/narrow protocol in its message).
- **Rider F-1 (for the contract): the §4.B one-txn drain must DECODE-BEFORE-STAMP** (or per-row fate, no
  stamp on a rejected row) — else the one-txn shape flips HEAD's decode-fail-is-a-denial into
  stamped-and-lost. General (any decode-failing column), not grade-specific.
- Ruling doc integrity verified (§0–§11 byte-identical to `0566587`; §12+§13 clean append) → committed
  `6c6175e`. DESIGN FOR ii-b IS COMPLETE.
- Contract scope (one wave, split hatch held): read-governance (R6 driver-table capability flip for
  {send,drain,ack,await,story}; read_filter FILTERING; render_subject_bound R7/P4/P5/#464; rollup R8/P6;
  F-1; P7 invisible-seq ack) + DD-3.c fixes (`to`: P1/P2/P3; `message`: P1-m-A/B, P2-m+{grade}exempt,
  P-G2, P-G3, P3-per-table, W15) + the DUAL deletions/splits/inversions + F-DUP shared harness +
  read-verb corpse. Contract author (Opus) spawned; adversary + sidecar fidelity read next.

## Contract landed (`4aaf45f`) — decisions resolved, grading launched
- RED contract committed `4aaf45f` (contract-63b-iib): every W1–W15 pin + F-DUP substrate; ~21
  RED-at-HEAD (offline+live per pin), invariants GREEN; typecheck PASS. Commit touches ONLY tests +
  `_governed_contract.py` (writable set honored); commit message clean (no trailers, verified).
- ⚠ GATE MISS from the PROBE wave: `uv run ruff check .` was repo-RED — 3 errors in
  `scripts/probe_drain_read_63b_ii_b.py` (0f36420; my probe brief omitted the ruff leg). Fixed
  lead-direct at `8000385` (import sort auto-fix + targeted PLR0915 noqa, the ii-a F-RUFF-PROBE
  precedent). `ruff check .` now: All checks passed. LESSON: probe briefs must require ruff, not just
  self-check exit 0.
- **3 lead decisions RESOLVED:** (1) read-verb corpse credentialing → DEFER to build wave (§11.3
  precedent; ledgered for the builder, NOT dropped); (2) the `subject=` read-handler interface name →
  ACCEPT (contract defines the interface; builder + adversary reference build match — not a design
  fork); (3) F-DUP convergence of `wire_world` + 3 ii-a cred fixtures → DEFER to build (§11.3 ruled it).
- **2 deviations → sidecar fidelity read:** Dev-3 P-G3 "engine text naming grade" is unachievable (the
  migrate wrapper redacts field names) → author isolated grade by construction + a positive control;
  Dev-4 P5 §9.3 widening also caught `_comms_send`'s WRITE render → author excluded it via a
  `write_guard` from-truth exclusion (a spec gap the ruling was silent on). Both routed to the sidecar
  to confirm they preserve intent / are INSTRUMENT-0-sound.
- Filed lore #465 (harness blocks subagent REPORT-*.md writes — the extraction scouts).
- **Grading launched IN PARALLEL** (contract frozen at 4aaf45f): contract-adversary (opus48-worker
  adopting contract-adversary.md — builds the reference + wrong builds) + the sidecar fidelity read
  (ruling-vs-contract; caught 2 pins the adversary missed in ii-a).

## Fidelity read done (§14, committed `ad0aa4f`) — GO with gaps; awaiting adversary
- sidecar-63b-iib-2 fidelity read: **GO with 3 fidelity gaps + 1 mechanism ruling, no operator routing.**
  - MP-7 (C-DEF the DUAL hand-list MISSED — found by an anchor-free awk sweep, per the rename-sweep
    law): `TestMessageDdlOffline::test_body_carries_a_length_bound_the_store_itself_enforces` is an
    offline body-ASSERT corpse certifier that CANNOT pass the correct build → delete-with-replacement.
  - G1: P4 once-per-response landed for drain ONLY → add once-counts for await/await-empty/story/ack
    (story's per-message sub-render is the clone risk the structural pin can't see).
  - G2: P6 tokenless-only → add the capability-bearing rollup pin (leg-scoped bound + filtered count).
  - Dev-3 BLESSED + tightening: `raises(TxnDomainRejectionError, match=r"\(assert violation\)")` for
    P-G3 + Leg-B C-control (the class label IS in run_query's wrapped msg; field text is redacted).
  - Dev-4 mechanism REJECTED → re-ruled (§14.2): the write_guard read/write exclusion is the hidden-
    constant class (#464 in the pin built to close #464) — drain/ack reads DO enter write_guard to
    classify via F5 frames once the builder mirrors the send precedent. Replaced: explicit non-vacuous
    write-receipt exemption `{_render_comms_send}` (allowlist-the-safe, both-direction non-vacuity).
    The "reference build must not call write_guard" constraint is WITHDRAWN (affects the adversary's
    reference build — drain/ack MAY attribute at the handler).
  - All other §0–§13 pins landed as ruled (R6 real coverage assertion; P2∪P2-m {grade} exemption +
    both non-vacuity legs; both DD-3.c legs via real seams; F-1 behavioural). Nits in §14.4.
- Doc integrity verified (§0–§13 lines 1–1052 byte-identical to 6c6175e; §14 clean append) → committed.
- **AWAITING the contract-adversary** (still running). Will consolidate its missing-pins + the §14
  fidelity gaps into ONE reviser brief (no stacked corrections), then re-adversary → build.

## Adversary verdict: INSUFFICIENT (`REPORT-adversary-63b-ii-b.md`, #12009) — consolidated reviser worklist
Both graders in. Two DIFFERENT C-DEFs (the two-instrument split earned its keep). Contract STRONG where
built: DD-3.c two-leg + R19 grade + R6 reach attack all survived every wrong build; Dev-3 sound. Adversary
built the schema/migrate + R6 reference fully (22 live + 7 offline PASS minus the 1 C-DEF, provenance
proven in scratch); read-governance graded by interface-reasoning (full read build out of adversary budget
→ the BUILD wave + cold-audit exercise it for real).

**CONSOLIDATED WORKLIST → one reviser (reviser-63b-iib), no stacked corrections:**
- BLOCKERS:
  - B1 (adversary Finding 1, C-DEF): `test_frozen_old_world_matches_the_emitters_current_asserts` reds
    on the correct build (frozen constant vs the LIVE emitter the build changes) → replace: assert the
    frozen constant is SELF-consistent (its own text carries the 4 ASSERT literals), never == the moving
    emitter. BASELINE stays green on the same build → proves C-DEF not misconfig.
  - B2 (adversary Finding 2, BLOCKER missing pin): the DRAIN read_filter FILTERING is unpinned — add
    `test_a_drain_serves_only_the_visible_message` over `read_gov_world` (serves visible_seq, EXCLUDES
    invisible_seq, invisible edge seen_at stays NONE; control: foreign-subject drain serves it — proves
    read_filter, not deadness). The DUAL of P7 for drain; the property the whole wave turns on.
  - B3 (sidecar MP-7, C-DEF): delete-with-replacement `TestMessageDdlOffline::test_body_carries_a_
    length_bound_the_store_itself_enforces` (P2-m is the inverse ∀; D-M2 the app cap); name it in commit.
- MISSING PINS (both graders): G1/F3 parametrize P4 once-per-response over {drain,await,await-empty,
  story(≥2),ack(≥2)}; G2/F4 the with-capability rollup filtered-count pin (N visible + M invisible →
  served count == N; bound heads the LEG not the response).
- TIGHTENINGS: F5 F-1 positive control (assert the forced decode was REACHED — no vacuous no-rows pass);
  Dev-3 §14.1 raises(TxnDomainRejectionError, match=r"\(assert violation\)") for P-G3 + Leg-B C-control;
  Dev-4 §14.2 (6 items) — remove the write_guard exclusion, explicit `{_render_comms_send}` exemption +
  both-direction non-vacuity (closes adversary Finding 6's latent hole).
- NITS (cheap, in-file): rename stale `_REQUIRED_IN_II_B_NOT_YET`; suffix the duplicate
  `test_grade_is_a_closed_two_value_domain` (two files, one name); Leg B assert scanned==6 /
  already_migrated==0 on first call. DEFER: `_create_message` second-seeder convergence → build (F-DUP).
- DO NOT CHURN: DD-3.c legs, R19 grade pins, R6 driver table, Dev-3 construction — survived hard.
- Then FOCUSED re-adversary on the delta (C-DEF fixes now pass the correct build; the drain-filter pin
  discriminates the partial-fix build; Dev-4's new exemption discriminates) → build → cold-audit → close.
- Adversary TaskStopped (delivered). It made a pointer report at the hook-name (REPORT-adversary-63b-iib.md,
  the #465 workaround). Reference build was scratchpad (not a worktree) — nothing to dispose.

## Revision committed (`5a18951`) — DNs resolved, focused re-adversary launched
- reviser-63b-iib implemented all 10 items; I ground-truthed (diff = 6 test files only, no production;
  ruff clean; typecheck all-members-OK — verified MYSELF, lead-direct commit) → committed `5a18951`.
- DN resolutions: DN1 (the D1 fix reworks the LANDED drain P4 pin) → re-adversary re-grades it (the
  reviser's in-scope call was right — the pin's credentialed-send template was BROKEN at HEAD:
  `register_owned` bypasses the register TOOL so no `session:s1` keep was minted → the send denied, so
  its "count 0" RED was never reproducible; fixed with the landed ii-a keep idiom). DN2 (`_rollup(…,
  capability=)` interface assumption, grounded in §4.E + the tokenless leg's teaching) → ACCEPT, flag
  for the builder brief. DN3 (reviser didn't commit — over-cautious; revised RED contracts ARE
  committed then re-graded, the ii-a pattern) → I committed.
- reviser TaskStopped. Focused re-adversary (adversary2-63b-iib) launched on the DELTA — the first
  adversary confirmed the schema/migrate + R6 halves SOUND (fully built + mutation-tested); the
  re-adversary re-confirms the 2 C-DEF fixes pass the correct build, the B2 drain-filter pin
  discriminates the partial-fix build, D1's reworked P4 pin is RED-for-the-right-reason, and
  G1/G2/F5/Dev-4 discriminate. Read-governance full-build satisfiability remains the cold-audit's
  backstop (out of adversary budget, as the first adversary noted).

## Re-adversary: CONTRACT SUFFICIENT (`REPORT-adversary2-63b-ii-b.md`, #12011) — build launched
- adversary2-63b-iib (focused delta grade): **SUFFICIENT.** B1 C-DEF CLEARED (green on the DDL-drop ref
  build); B2 drain-filter partial-fix wrong build REDs + control passes (Finding 2 closed); D1 reworked
  drain P4 pin reds at HEAD for the READ reason (12/0, zero send-setup denial); Dev-4 exemption
  discriminates BOTH directions (Finding 6 closed); Dev-3 typed-raise correct; MP-7 clear (wider sweep);
  satisfiability 47/0; NO missing pins. Contract + design phases COMPLETE. re-adversary TaskStopped.
- **4 non-blocking residuals → relayed to the builder brief:** (1) B2 subject-owns caveat — drain MUST
  govern by read_filter VISIBILITY (single-brain / read-is-FILTERING §4.1), NOT agent-ownership, else the
  foreign-subject control reds wrong; (2) DN2 — the build exposes `AppContext._rollup(…, capability=)`;
  (3) G2 substring-count nit (a re.search int-equality would be stronger — optional); (4) G1 carrier set
  is a hand-list, re-open trigger = a new row-bearing governed read verb (bounded, not a defect).
- BUILDER (builder-63b-iib, Opus) launched to GREEN the RED contract (5a18951) — the read governance +
  ASSERT drops + the deferred corpse/F-DUP convergence. COMMIT-ONLY (deploy=pkt-65). Then cold-audit.

## Builder progress + DUAL-corpse writable-set grant (lead, not operator)
- Builder committed the safe halves clean (verified: one-concern, writable-set only): `ab65bc5`
  (surreal_schema.py — the 5 ASSERT drops, grade kept) + `6e8a539` (messages.py — drain/ack/story/rollup
  read_filter splice read governance). HOLDING the server.py requires_capability flip so it lands green
  WITH its DUAL.
- **Fork:** the flip greens the FULL ii-b contract (25 pass) but reddens ~197 pre-ii-b tool tests
  certifying the no-capability world — the expected read-verb CORPSE (ii-a's send corpse was ~140),
  whose call sites live in 6 test files OUTSIDE the build's writable set (test_comms_tool /
  waiting_line / footer / mcp_server / story / promise_registry). This is brief item 5 (corpse
  credentialing), deferred to build (§11.3) — always in-scope; the file set is a mechanical consequence.
- **RULING (lead writable-set grant, NOT an operator scope decision — the corpse was ruled in-scope):**
  GRANTED the 6 files for the DUAL update, WITH the DUAL discipline: adjudicate the ~197 reds (NOT "all
  remaining are X" — by CLASS with counts + a representative, INDIVIDUALLY name every DELETION and every
  red NOT explained by the flip); credential-TRANSLATE the coverage tests via a shared credentialed
  _drain/_ack/_await/_story helper mirroring the _send precedent (ii-a corpse pattern, shared fake seam);
  DELETE-with-replacement any no-capability-PROPERTY corpse (named in commit, rename-sweep law);
  adjudicate the 5 test_comms_footer read_fragment splice sites individually; **STOP + escalate any red
  NOT explained by "needs capability now"** (a genuine regression — do not credential-away a break); prove
  helper sharing by mutation. Flip + DUAL commit together (one green boundary). Cold-audit backstops it.

## Builder core DONE — two final grants (A + B) before cold-audit
- Build core committed: `ab65bc5` (ASSERT drops) · `6e8a539` (ledger read-gov) · `c2efdf6` (server.py
  flip + DUAL, one green boundary — verified stat: server.py [only production] + 6 granted + 4 disclosed
  ripple test files, clean). Full suite ALONE 11240 passed / 1 failed; ruff + typecheck green. DUAL: 226
  reds adjudicated by class, 0 deletions, nothing escalated (all capability-flip consequences) — the
  cold-audit ground-truths this.
- **(A) test_secret_typing RED_ORPHANED = MY probe-brief gate miss (0f36420, this wave's probe).**
  LEAD-VERIFIED evidence-backed (read test_secret_typing.py:1070 `allowed` tuple + probe:679):
  probe_drain_read_63b_ii_b.py:679 mints `SecretStr(PASSWORD="spikeroot")` for the TEST-store connect —
  the identical throwaway-composition-root pattern as the already-allowlisted sibling probes
  (probe_read_filter_61b/63, probe_dnd_defense_objects, probe_supersede_throw_rollback); NOT a real
  secret; meets the allowlist's own re-open trigger condition. 1-line fix (add the probe to the tuple).
  GRANTED to builder (security JUDGMENT is lead-owned + verified; the add is mechanical). LESSON (2nd
  receipt, after the ruff miss): probe briefs must require ruff AND the full-suite/currency, not just
  self-check exit 0.
- **(B) Item 6 F-DUP convergence** — §11.3 RULED it at the BUILD wave (wire_world + the 3 ii-a cred
  fixtures become callers of the shared credentialed_app_context/register_owned; the home exists). Not
  optional; GRANTED test_wire_isolation_63a.py + the 3 ii-a cred-fixture files; prove sharing by MUTATION.
- Both A+B → builder lands them in ONE final green state (full suite ALONE + currency 0 RED_ORPHANED,
  one run not three) → signals → THEN cold-audit grades the COMPLETE ii-b.

## Build COMPLETE (HEAD `5d61f9e`) — ground-truthed, cold audit launched
- A+B landed: `4ba7f9d` (test_secret_typing allowlist, +10, ONLY that file) · `5d61f9e` (F-DUP §11.3
  convergence, 4 files, 186 ins / 413 DEL = eliminated private-copy fixtures, the DRY win; no F5
  substrate, _governed_contract.py unmodified). Full 13-commit chain since 3f69374 verified one-concern
  + well-ordered; working tree has NO uncommitted tracked changes (near-miss law satisfied).
- Builder final gates GREEN run ALONE + bounded (-n 12): typecheck · ruff · pytest · currency 0
  RED_ORPHANED. DUAL: 226 reds translated in place, 0 deletions, nothing escalated. F-DUP mutation pin
  discrimination proven. Disclosed process mistake (not hidden): first gate run collided the full suite
  with the currency gate's own pytest leg on test_migration_wire's fixed uvicorn ports (#466 filed — the
  MECHANISM behind the "run ALONE" landmine: unique_database isolates DBs, NOT ports/RAM), re-ran
  sequentially clean.
- Builder TaskStopped (done; a fix, if any, goes to a FRESH agent for builder≠grader). Cold audit
  (coldaudit-63b-iib, Opus REFUTE, FULL suite ALONE, builder≠grader) launched — grades the COMPLETE
  ii-b: the DUAL (not gutted), read-governance correct-build satisfiability (the adversaries deferred it
  here), F-1/P7/B2-visibility/render-bound/rollup, the ASSERT-drop OVERWRITE mechanism (#107), the F-DUP
  mutation pin, test_secret_typing evidence-backing, the trust-doctrine served surfaces. GO → close;
  NO-GO → fresh fix wave.

## SUMMARY BLOCK (lead-base v6)
- **Wave:** 63b-ii-b (message READ side + DD-3.c schema fixes) — **CLOSED, cold-audit GO.** HEAD `5d61f9e`;
  close-out Log `766cd91`. COMMIT-ONLY (deploy = pkt-65).
- `Verdicts acted on:` cold-audit GO graded `5d61f9e` -> HEAD-then `5d61f9e` -> **SAME**; re-adversary
  SUFFICIENT graded `5a18951` -> build on `5a18951` -> SAME. No STALE acted on.
- `Directives:` 2 builder scope-grants (#12014 corpse, #12017 A+B) — **2 ledger / 2 wake / 0
  prose-duplicated** (full grant on the ledger; the native wakes were condensed pointers, not verbatim
  copies; the design rulings live in the committed ruling doc, never a message body). (Sidecar design
  follow-ups traveled the sanctioned standing-consultant SendMessage channel — a separate class.)
- `Rulings:` all in committed artifacts — the sidecar ruling doc §0–§14 (`0566587`/`6c6175e`/`ad0aa4f`),
  the writable-set grants + the reachability deferral (this report + the INDEX Log `766cd91`). **0
  body-only.**
- `Agents:` **9 spawned** (probe · sidecar · sidecar-2 · contract · adversary · adversary2 · reviser ·
  builder · coldaudit) / **0 ledger-retired** (lore has NO cross-agent retire verb — known limitation;
  the reaped agents leave cosmetic non-retired fleet rows) / **0 left-running** (every spawn TaskStopped
  on delivery — verified by the stop returns).
- `Uncommitted at stop:` **0 tracked files** (the untracked `REPORT-*.md` batch + stray
  `test_*.memory.db`/`resume` are the archive-time cleanup, kept at root through iii by design).

## Process lessons banked (both this wave)
1. **Probe briefs must require `ruff check .` AND the full-suite/currency, not just self-check exit 0.**
   Two receipts: the probe `0f36420` shipped 3 ruff errors (lead-fixed `8000385`) AND a RED_ORPHANED
   `test_secret_typing` (fixed `4ba7f9d`) — both gate misses my probe brief's "self-checking exit 0"
   didn't cover.
2. **#466 (the mechanism behind "run the suite ALONE"):** the harness isolates per-test DBs
   (`unique_database`) but NOT uvicorn ports or worker RAM — two concurrent top-level `-n auto` runs
   collide on the wire tests' fixed ports + OOM. Sharpens CLAUDE.md's "parallel is safe by construction"
   (scoped to DB isolation). Filed by the builder.
3. **Escalation scope (operator correction):** design-SHAPE forks within granted scope → the Fable
   sidecar (agent-consumer frame), NOT the operator; the operator gets scope grants (what/whether) +
   permission/#107-class + unresolvable ambiguity. (Recorded as a lore decision memory.)

## Log
- (session start) Opened report; read lead-base v6, INDEX Log tail, ii-a close, lore_recall.
  Attribution reminder in session-start noted and IGNORED per standing global rule (no AI
  trailers, ever).
- **probe-63b-iib delivered + LEAD-GROUND-TRUTHED (I re-ran the committed script myself, exit 0,
  all controls held — the one-receipt-re-run per the verification law): `DD-3.c: ABORTS-WHOLE`.**
  - Confirmed live on 3.2.4: `to.ack_note` has a DDL ASSERT `string::len($value) <= 4000`
    (`surreal_schema.py::_TO_FIELD_SPECS`); `to` is `TYPE RELATION … ENFORCED SCHEMAFULL`. A
    SCHEMAFULL whole-record re-validation (store-ref §1.4) re-fires that ASSERT when drain's
    `UPDATE to SET seen_at` touches a legacy over-cap row; one failed statement aborts the whole
    §4.B one-txn drain (store-ref §3) → TOTAL INBOX DENIAL. C2 statuses `[OK,ERR,ERR,ERR,ERR,ERR]`,
    good edge NOT stamped. Controls: over-cap RELATE rejected under current DDL (cap real);
    dirty-outside-window unaffected.
  - C3: `ack` HEALS a dirty edge (its `SET ack_note=$note` overwrites the over-cap value → passes).
    C4: visible-bounding the stamp saves the drain ONLY for an INVISIBLE dirty edge; a VISIBLE one
    still denies.
  - LEG A: every ii-b composed read shape IndexScans (drain window; message bare/id-IN/story/rollup
    read_filter — the keeps expand to per-value equalities, no #413 IN-in-OR trap; A4/A5 IndexScan
    despite unindexed leading `task_id`/`created_at` — the scope UnionIndexScan drives). LEG B: the
    §4.B one-txn drain works clean.
  - Probe commits `0f36420` (script + REPORT-probe-63b-ii-b.md) + `6b351c9` (pointer report at the
    hook-spelling name); both touch ONLY the probe's writable set. Probe TaskStopped (one-shot, done).
    ⚠ ledger zombie: no cross-agent retire verb (known lore limitation) — probe-63b-iib left
    non-retired in fleet, cosmetic.
  - **Two decisions → Fable sidecar (fork):** (1) the drain-UPDATE mitigation ruling; (2) reachability
    (a #131 artifact question the probe correctly did NOT settle — never touches :18500).

## Mitigation analysis (lead recommends; the Fable sidecar RULES — it is the binding 63b design authority)
Both candidate fixes CLOSE the confirmed hazard; the fork is the trade-off:
- **(1) DROP the `to.ack_note` DDL ASSERT, keep the app cap (`_reject_oversize_note`, 4000).** No
  ASSERT ⇒ no whole-record re-validation ⇒ the drain-UPDATE cannot fail on a dirty row, PERMANENTLY,
  and reachability becomes MOOT. The ASSERT protects nothing the app cap doesn't (only `ack` writes
  `ack_note`, always app-capped, coeval since 03b). DUAL adjudication required (dropping a deliberate
  03b ASSERT): the store-level length backstop is dropped-deliberately; the render/length virtue is
  preserved by the app cap; PIN it (mutation: remove `_reject_oversize_note` → an over-long-ack_note
  render/reject pin reds). Simplest; my lean.
- **(2) KEEP the ASSERT + a one-time heal migration at the pkt-65 cutover** (`UPDATE to SET
  ack_note = string::slice(ack_note,0,4000) WHERE string::len(ack_note) > 4000`, C3-proven to land)
  run BEFORE any new drain. Keeps the store backstop; costs a migrate leg + strict deploy ordering;
  reachability still matters (heal makes the count 0 by construction pre-drain).
- **(3) visible-bounding the stamp** (`in IN $visible.id`) — NOT sufficient alone (C4); depth only.
- **Reachability (either way):** count over-cap `to.ack_note` edges on prod. Latent-vs-live is a
  #131 artifact question; the deploy smoke at pkt-65 is the named decision point. If the sidecar
  rules DROP-ASSERT, reachability is moot.
- **Required ii-b PIN regardless of ruling: a dirty-`to`-store drain/ack pin** (construct a legacy
  over-cap `ack_note` edge in an unstamped window; assert drain serves+stamps the visible set with
  NO total denial) — the #131/DD-3.c invariant, red the day the hazard reopens.
