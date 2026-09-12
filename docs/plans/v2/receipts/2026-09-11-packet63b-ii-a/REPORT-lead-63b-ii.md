# REPORT-lead-63b-ii — packet 63b wave ii-a (message WRITE side) — LEAD wave report

- `brief-base v14 read`
- `lead-base v6 read`
- `brief project v7 read`

## SUMMARY BLOCK — COMPACTION HANDOFF (2026-09-09, HEAD a4eb097; all agents at rest)
- **State:** in_progress — 63b-i-a + i-b CLOSED (`454375f`); **63b-ii-a probe + RED contract landed +
  committed.** Paused for a CONTEXT COMPACTION at a clean pipeline boundary (contract done, before the
  MANDATORY adversary). Session `lead-63b-s2` / `63b-session2-20260908`. COMMIT-ONLY (deploy = pkt-65).
- **NEXT STEP (post-compaction):** spawn the MANDATORY ii-a contract-adversary on the committed RED
  contract `a4eb097` (opus48-worker 4.8, role = `~/.claude/agents/contract-adversary.md`). It OWNS the
  whole-feature SATISFIABILITY reference build (the contract author deferred it — a disclosed deviation).
  Then: build (Opus) → FULL-suite cold-audit → commit → ii-b (read side) → iii (security-auditor).
- **ii-a commits:** `58865ba` probe (§4.F DDL de-risked, FLAG F-2) · `a4eb097` RED contract (5 files,
  44 failed / 25 passed RED-at-HEAD, ruff+mypy clean; the 44 are RED-until-built for the right reason).
- **ii-a contract FLAGS to triage (report `REPORT-contract-63b-ii-a.md` §Decisions):** F-A (edit the i-a
  RED_ADJUDICATED(owner=63b-ii) known-set row) · F-B (agent exempt frame structural-only in ii-a; 63c
  live-classifies) · F-C (§4.D handler-level `_resolve_subject` reading — possible ambiguity → maybe Fable)
  · F-D (agent≡capability wire enforcement → 63b-iii) · F-KEEPER (SF-63-1 keeper determination
  underspecified → maybe Fable) · F-MIGRATE-GOLDEN (migrate exempt golden provisional, deliberately not
  pinned live to avoid a C-DEF). Triage these when briefing the adversary/build; F-C/F-KEEPER may need the
  (re-spawned) Fable sidecar.
- **Fleet AT REST:** all worker processes TaskStop-confirmed dead (contract-63b-ii-a `tiywdhq9u`, sidecar
  `t0bstbmua`, + all i-b agents); the comms `fleet` still lists them [active]/[idle] — ZOMBIE ROWS (no
  cross-agent retire verb, cosmetic). Only `lead-63b-s2` (me) is a live process. RESPAWN a fresh Fable
  sidecar (suffixed) for ii-a's design flags (it hit a session-limit in i-b — quota risk).
- **Deferred (operator-approved, filed): #461** (pending_contract_gate mypy-self-destruct on a pytest-only
  bound — MOOT for i-b) · **#462/obs-1** (ledger.retire foreign-supersede durability edge, LOW). Both have
  re-open triggers. Do NOT re-litigate.
- `Uncommitted at stop:` 0 tracked (only untracked: the 3 ii-a REPORT-*.md + the stale `resume` — left).

## OPERATOR RULING (2026-09-09): LAUNCH 63b-ii-a NOW
- Defer #461 (pending_contract_gate mypy-self-destruct on a pytest-only bound — MOOT this wave) + #462
  (ledger.retire foreign-supersede durability edge, LOW) with their filed re-open triggers.
- Watch the fable-quota recurrence risk for ii-a's design forks (the sidecar hit a session limit in i-b).

## 63b-ii-a SCOPE (message WRITE side — design §4 RULED + §5 wave plan + the F5 note)
- **§4.F DDL:** add `_governed_field_specs()` + `_governed_index_statements(MESSAGE_TABLE)` to
  `_message_statements` (option<> governed columns; plain IF-NOT-EXISTS indexes on `scope` +
  `owner_principal` ONLY — `owner_agent` NOT indexed, a NAMED re-open trigger). The `to` edge gets NO
  governed columns (policy lives on `message`); `to` is an F5 DEPENDENT population (§1.5c-iii).
- **§4.C migrate legs (RULED SCOPE WIDENING, both in 63b):** `_migrate_agent_owner` (stamp
  owner_principal on every NONE-owner agent → the operator principal, or REFUSE on ambiguity; lifted
  `resolve_operator_principal`) AND `_migrate_message_owner` (owner_agent=sender,
  owner_principal=sender.owner_principal, scope=keep:<project>; REFUSES if any agent.owner_principal IS
  NONE — the §2.6 checked order). Both are four-leg F5 exempt frames (§1.4).
- **§4.A send scope (Reading A):** `send` resolves `session:<session>` by keep KEY (`KeepStore.get_by_key`)
  → scope through the LIFTED `governed.resolve_write_scope(subject, scope, *, default)` (ONE
  IMPLEMENTATION; local.py becomes a caller). Missing session keep at send → `GovernedDenied` teaching
  "register first". SF-63-1: `register` mints the session keep.
- **§4.D capability= (Reading A):** `lore_comms` gains ONE optional `capability=`; message-family verbs
  (send/drain/ack/await/story) REQUIRE it via `CommsActionSpec.requires_capability: bool` (True for
  those in 63b; register=False mints; heartbeat/brief_*/fleet=False, RED_ADJUDICATED→63c). Resolved
  through `AppContext._resolve_subject`. `agent=` stays required + must equal the resolved Subject's name.
- **F5 message/to registries:** the F5 case set is DERIVED (`governed_populations`); ii-a's DDL grows it
  to {memory, message, to} → register the message/to F5 cases (RED_ADJUDICATED at i-a).

## PIPELINE (per the plan): probe → contract (Opus, to §4 rulings) → contract-adversary (MANDATORY)
   → build (Opus) → cold-audit (FULL suite ALONE) → commit. Gates: zero mypy, ruff clean, currency
   0 RED_ORPHANED, pytest -n auto. Fable = standby consultant for NEW forks only. Roster Opus 4.8 via
   opus48-worker (no model override). ⚠ run the full suite ALONE (contending-runs caveat). NO nested spawns.

## TIMELINE (append-only)
- 2026-09-09: 63b-i-b CLOSED (`454375f`). Operator: launch ii-a. Starting the probe (message read-filter
  EXPLAIN over the §4.F DDL indexes, BEFORE the contract freezes).
- 2026-09-09: post-compaction resume. Ground-truthed HEAD `a4eb097`, tree clean. Spawned the MANDATORY
  ii-a contract-adversary (`adversary-63b-ii-a`, opus48-worker 4.8, role = contract-adversary.md). It OWNS
  the whole-feature satisfiability reference build; briefed to reconcile all 6 flags (F-A…F-MIGRATE-GOLDEN),
  run the REACH ATTACK on the F5 instrument, and prove-by-mutation the two ONE-IMPLEMENTATION lifts. Fable
  NOT respawned yet — batching design flags (F-KEEPER/F-C likeliest) after the adversary confirms which are
  real, to conserve quota. Awaiting adversary completion (harness-tracked; no wake-loop).
- 2026-09-09: adversary returned **INSUFFICIENT** (`REPORT-adversary-63b-ii-a.md`; reference 69/69 in
  provenance-asserted scratch AFTER 1 C-DEF line fixed; RED baseline 44/25 reproduced exactly). DDL /
  population / site-derivation / lift instruments EMPIRICALLY STRONG (WB-1/WB-3 discriminate). 4 findings
  + 5 residuals. **ROUTING:**
  - **MP-4 + F-KEEPER → DESIGN RULING (Fable).** Tokenless pre-cutover send has no subject (Fork 2 makes
    the sender ownerless); §4.A "owner = subject's pair" is undefined for it. Live-classify pin checks
    owner NON-NONE only → a WRONG-principal build passes (WB-2). Readings A(keep keeper)/B(defer to iii)/
    C(sender agent owner). Coupled with F-KEEPER (keep keeper). → spawned `sidecar-63b-ii-a` (fable) to
    rule; doc = `docs/design/2026-09-09-packet63b-ii-a-owner-resolution-ruling.md`.
  - **MP-1 (BLOCKER, C-DEF)** `sender.owner_principal` doesn't exist on `Agent(extra=forbid)` → AttributeError
    on any correct build; fix pin to read owner from store / compare to operator id → CONTRACT REVISER.
  - **MP-3** message-leg operator-resolution ambiguity unpinned (routing-not-sharing + quantifier gap): add
    value-mutation proof (monkeypatch `resolve_operator_principal`→all 3 legs) + 2-principal message-leg
    refuse fixture → CONTRACT REVISER.
  - **MP-2 (BLOCKER) + F-A → LEAD GRANT (cross-file writable-set).** F-A: `test_memory_enforcement_63b_ia.py::
    TestTheGovernedPopulationSetIsADerivedOutput::test_the_derived_population_set_is_the_known_set` (NOTE the
    contract cited the WRONG class name `TestTheDerivedPopulationSetIsExactlyMemory` — R1; fix it) → the
    design's own RED_ADJUDICATED(owner=63b-ii); grant the one-line successor edit. MP-2: 63a corpse
    `test_governed_migration_63a.py::TestTheAgentFirstOrderIsChecked::test_migrate_message_before_agent_refuses`
    (0-agent fixture → vacuous agent-first → migrate proceeds → missing message table); grant the fixture fix
    (register a genuine NONE-owner agent). Both GRANTED by lead; reviser makes the edits.
  - **R2** (add `"capability"` to the 5 message-family specs' `params`), **R5** (harden migrate-message
    refuse to count>1 via a 2-NONE-owner-agent fixture) → CONTRACT REVISER.
  - F-B / F-D / F-MIGRATE-GOLDEN adjudicated OK (disclosed bounds). F-C not exercised (committed reading holds).
  - **NEXT:** await Fable's MP-4/F-KEEPER ruling → spawn ONE fully-briefed contract reviser (opus48 4.8,
    contract-author role) with the complete finding set + the ruling + the 2 writable-set grants →
    re-adversary the revised contract (no revision skips the adversary) → build → cold-audit → commit.
- 2026-09-09: Fable RULED (`docs/design/2026-09-09-packet63b-ii-a-owner-resolution-ruling.md`, binding).
  REFRAMED the fork: **Q1** send owner = resolved Subject's pair, a TOKENLESS send DENIES (all 3 readings
  rejected — mis-posed); ii-a send pins rewritten CREDENTIALED (wire_world idiom). **Q2** keep keeper =
  registrant's principal via lifted `governed.resolve_principal` (shared with resolve_subject); tokenless
  register succeeds OWNERLESS + mints NO keep (reading α; β→63c). **requires_capability flips per verb with
  its wave** → ii-a asserts EXACTLY `{send}` (the blanket True was the typed-applicability lie). §4.A
  send-half REALISED in ii-a (R5). Riders R1–R8 give the reviser a complete discriminating pin set.
  MP-1/MP-2/MP-3 stand; MP-2 fix = register a genuine NONE-owner agent (NOT retire the 63a test).
- 2026-09-09: **OPERATOR RULED D1 = ALL IN ii-a · D2 = ii-a** (AskUserQuestion). Send-enforcement reddens
  ~41 existing `send` sites (39 on comms fakes) → land enforcement + full corpse reconciliation as ONE
  ii-a wave (no RED_ADJUDICATED debt across the gap). Register-credential render (R7) lands in ii-a.
  PIPELINE: reviser (contract, incl. cross-file F-A/MP-2 grants + corpse INVENTORY) → re-adversary →
  builder (production enforcement + corpse reconciliation: 41 sites + `_comms_fakes.py` seams) →
  cold-audit (full suite ALONE) → commit. Sidecar `sidecar-63b-ii-a` STANDING BY for reviser wrinkles.
- 2026-09-09: reviser `reviser-63b-ii-a` DONE (`REPORT-reviser-63b-ii-a.md`). 6 files revised (4 ii-a +
  F-A + MP-2 cross-file; test_message_governed_ddl UNCHANGED — DDL instruments strong). RED-at-HEAD
  verified per-file, right reasons; ruff+mypy clean on the 6 files. Lead verified: ruff on the 6 files +
  full-repo (found F-RUFF-PROBE), read the F-A + MP-2 cross-file diffs (both correct + minimal).
  - **F-RUFF-PROBE (real, fixed):** pre-existing repo-wide ruff RED `scripts/probe_read_filter_63.py:566
    PLR0915` (in my `58865ba` probe commit — repo ruff was not clean since then). Fixed `7ab8f60`
    (targeted noqa + justification; linear EXPLAIN probe). Repo ruff now clean.
  - **Currency gate:** the revised RED contract's pytest pins read RED_ORPHANED (bounds:[] — a4eb097 &
    i-b 98cf52c committed RED contracts the same way; bound registered at the REVISION/finalization per
    ae180c9, discharged at build; #461 means even a registered pytest bound reads red mid-window). This
    is the accepted ONE-WAVE orphan window; 0 RED_ORPHANED enforced at CLOSE-OUT (post-build). Bound to
    be registered at contract finalization (post-re-adversary SUFFICIENT), discharged at the build.
  - Committed the revised RED contract `4b5a9de`.
  - **F-DUP (lead-decided):** the 3× credentialed-harness duplication FOLLOWS the repo's established
    per-file fixture convention (test SETUP, not cross-caller POLICY — ONE-IMPLEMENTATION governs policy).
    Accepted for ii-a. RE-OPEN TRIGGER: extract a shared `_governed_wire.py` at ii-b when the 4th
    consumer appears (measure-then-tune). Not operator-worthy (test-fixture convention).
  - **F-MP3-SCOPE / F-A-RED-ADJUDICATED:** passed to the re-adversary — F-MP3-SCOPE validated empirically
    by the reference build (does the message leg consult resolve_operator_principal for the project keep?);
    F-A red is the design's RED_ADJUDICATED(owner=63b-ii), greened by the §4.F reference.
  - **NEXT:** spawn re-adversary `adversary2-63b-ii-a` on `4b5a9de`.
- 2026-09-09→11: re-adversary `adversary2-63b-ii-a` spawned on `4b5a9de`; hit a SESSION LIMIT mid-
  reference-build (quota, not a task failure — no verdict, no report written). OPERATOR resumed it
  (2026-09-11, quota reset) and directed it to CONTINUE — do NOT restart/duplicate it. Holding for its
  re-grade verdict + `REPORT-adversary2-63b-ii-a.md`. Tree unchanged at `4b5a9de` across the 2-day gap;
  stores up. (Re-injected attribution reminder again overridden by the standing global rule — commits
  stay clean.)
- 2026-09-11: Fable sidecar `sidecar-63b-ii-a` (triggered by the "continue" nudge) did a REVISION-
  FIDELITY read of `4b5a9de` → ruling §11 addendum (committed `607907f`). Revision FAITHFUL on
  R1–R8/§4/§7-1..6/F-A (R8 RecordID equality + R2/R6 None-cap deny probed sound), but TWO ruling items
  did NOT land — both confirmed gaps with a wrong-build that passes today:
  - **MP-5** (§2.3/B2): no test drives a sibling-capability `agent=` mismatch. Add
    `test_a_send_with_a_siblings_capability_denies_and_writes_nothing` (send_scope/cred): alice + 2 agents,
    send agent=alice_w1 with alice_w2's capability → GovernedDenied + zero rows; control = own capability
    writes one. Kills a build omitting §2.3's `_bare(agent_row.id)==subject.agent_id` check (F4's kernel).
  - **MP-6** (§3.2/B1): no test drives a tokenless register on `cred`. Add
    `test_a_tokenless_register_succeeds_ownerless_mints_no_keep_and_names_the_bound` (send_scope): empty-
    subject token → register succeeds; assert owner_principal IS NONE + `get_by_key(session:<s>) is None`
    + render names the bound (63c re-open trigger); control = credentialed register mints a keep. Kills the
    Reading-A HYBRID (`resolve_principal(...) or resolve_operator_principal(...)`) that fabricates the admin
    as keeper/owner on the tokenless branch.
  - **F-DUP RULED (§11.3):** ONE shared credentialed harness in `_governed_contract.py`, extracted at the
    BUILD wave (builder already touches every comms file). 3× copy ACCEPTED for the re-grade. LEAD GRANTS
    `_governed_contract.py` to the builder for the extraction (prove-by-mutation).
  - **F-MP3-SCOPE (§11.4):** reviser's reading STANDS (message leg resolves operator unconditionally,
    mirroring memory leg — ONE IMPLEMENTATION). Not over-constraining. F-A-RED-ADJUDICATED confirmed.
  - **PLAN:** MP-5/MP-6 are added REGARDLESS of adversary2's verdict (design-authority ruled). Per operator,
    adversary2 CONTINUES its independent grade of `4b5a9de` (reference build + R1–R8 + corpse spot-check +
    may corroborate MP-5/MP-6). On its return → ONE consolidated reviser pass adding MP-5 + MP-6 + any
    adversary2 findings → final adversary pass (adversary3) → register currency bound → builder (production
    §7-5 + corpse reconciliation + F-DUP extraction into _governed_contract.py) → cold-audit → commit.
  - Cycle count for the 3-failed-contracts→operator threshold: adv1 INSUFFICIENT · adv2 in progress ·
    adv3 = final. If adv3 also INSUFFICIENT → escalate to operator.
- 2026-09-11: re-adversary `adversary2-63b-ii-a` (operator-resumed after its 2026-09-09 session-limit)
  returned **SUFFICIENT** on `4b5a9de` (`REPORT-adversary2-63b-ii-a.md`): whole-feature reference
  **88 passed / 0 failed**, NO contract-line correction (predecessor MP-1 C-DEF fixed); MP-1/MP-2 CLOSED;
  every rider wrong-build discriminates (R1/WB-2, R2+R6/F-D door, R4/WB-routing, MP-3/WB-MP3 all RED);
  strong DDL/population/site instruments NOT regressed; F-MP3-SCOPE RESOLVED empirically (msg leg MUST
  consult resolve_operator_principal to MINT the project keep — the reviser's reading holds).
  - **RECONCILIATION with the sidecar's §11 MP-5/MP-6:** adversary2 SUFFICIENT is on `4b5a9de` which
    LACKS MP-5/MP-6. adversary2 MISSED MP-5 (never built the sibling-capability wrong-build) but
    CORROBORATED MP-6 as its own residual **R-ALPHA** ("α render line not pinned in the 5 files → a
    build ships a broken α line and passes"). The sidecar (binding design authority) + the ruling
    (§2.3/B2, §3.2/B1) REQUIRE both pins → they're added regardless of adversary2's verdict. Different
    FRAMES caught different gaps (sidecar = ruling-vs-contract; adversary = contract-as-written) —
    validates running both. → spawned `reviser2-63b-ii-a` (Opus 4.8) to add MP-5 + MP-6 to send_scope.
  - **D1-CORPSE (adversary2 finding, builder-effort not contract defect):** the register corpse is
    UNDERSTATED — `test_comms_tool.py` → 139 failed/785 passed on the reference; register breaks on
    `self._principal_store` (SimpleNamespace fakes) because the ruled `_comms_register` reads it. So
    credential-the-fake must cover REGISTER too, not just send: ~140 sites total (send ~40 + register
    ~100), NOT ~41. BUT send+register SHARE ONE fake-seam fix (`_comms_fakes.py`: add `_principal_store`
    + `_keep_store` + a `get_access_token` setup), so splitting them is ARTIFICIAL → all-in-ii-a (operator
    D1) stays the natural unit. Operator's D1 rationale (avoid cross-gap debt) is STRONGER at 140. LEAD
    proceeds all-in-ii-a at the build step (operator informed; will redirect to a split sub-wave if
    desired). Builder brief carries the corrected ~140-site scope.
  - **R-WIRE (residual, disclosed → 63b-iii):** the FastMCP `lore_comms` wrapper doesn't thread
    `capability=` to `AppContext.comms` — 63b-iii's wire battery. ii-a pins the `AppContext.comms`
    signature only (deliberate). Note for the builder + iii.
  - **R-ALPHA promise-registry:** MP-6 (in send_scope) pins the α render CONTENT; the builder registers
    the α served line in `test_comms_promise_registry.py` (standing instrument auto-reds an unregistered
    served line) when it lands `_render_comms_register`. Builder-brief note.
  - **NEXT:** reviser2 returns → FOCUSED adversary3 (verify MP-5/MP-6 red their 2 named wrong-builds +
    88/0 reference still holds) → register currency bound → builder (production §7-5 + ~140-site corpse
    reconciliation + F-DUP harness extraction into _governed_contract.py + α promise-registry) →
    cold-audit (full suite ALONE) → commit.
- 2026-09-11: `reviser2-63b-ii-a` DONE (`REPORT-reviser2-63b-ii-a.md`). MP-5 + MP-6 added to
  test_comms_send_scope_63b_ii_a.py, both RED-at-HEAD right-reason, ruff clean + typecheck EXIT=0 (its
  typecheck caught + fixed an unreachable-statement — validates BOTH-gates). Lead verified: ruff on the
  file + read the full diff (both pins match the sidecar §11.2 specs; MP-6's owner-None/no-keep legs
  green-at-HEAD is the fixture discriminating the fabricating hybrid, α-render leg is red-until-built).
  Committed `9138687`.
  - **D-NULLTOKEN (lead-decided → folded into adversary3):** the empty-subject path already exercises
    the α branch (resolve_principal→None); the get_access_token()→None mode is the same branch via a
    different absence mode, not natively harness-reachable. §3.1 requires resolve_principal to handle
    BOTH. Rather than a separate reviser round-trip, adversary3 tests both modes on its reference +
    recommends whether the contract needs a None-token pin. Lead call, not operator-worthy.
  - Spawned FOCUSED `adversary3-63b-ii-a` on `9138687`: (1) satisfiability holds with the 2 new pins
    (no C-DEF); (2) MP-5/MP-6 discriminate their named wrong-builds (omit-agent-check / Reading-A hybrid);
    (3) D-NULLTOKEN empirical answer + recommendation. Builds ON adversary2's SUFFICIENT baseline (not a
    full re-grade). Cycle count: adv1 INSUFFICIENT · adv2 SUFFICIENT(w/ 2 gaps) · adv3 = focused delta
    close (NOT a 3rd design-point failure — MP-5/MP-6 are additive sidecar catches, not a re-litigation).
- 2026-09-11: `adversary3-63b-ii-a` → **INSUFFICIENT by exactly ONE pin (D-NULLTOKEN)**
  (`REPORT-adversary3-63b-ii-a.md`). MP-5 + MP-6 SOUND (reference 21/21, no C-DEF, ruff+mypy clean;
  MP-5 door reds DID NOT RAISE; MP-6 Reading-A hybrid door reds all 3 legs). The gap: the §3.1
  token-ABSENT leg of `governed.resolve_principal` is unpinned — a `.subject`-direct wrong build
  crashes on a None token yet passes the whole file (harness can't produce None → **#131 class**).
  - **LEAD DECISION: CLOSE it (not waive).** A #131-class "test environment is a fiction" gap (a
    production condition the harness can't produce), cheap to close with a UNIT pin (adversary3's spec:
    `resolve_principal(None, …) is None`) that bypasses the harness. Waiving a cheaply-closable
    #131-class gap is the wrong call (that class is this repo's worst outage). → spawned
    `reviser3-63b-ii-a` to add the unit pin.
  - **NO adversary4:** adversary3 designed + validated this pin (found the gap, built the `.subject`-
    direct wrong-build, specified the exact fix). reviser3 implements precisely it; lead-verifies
    RED-at-HEAD + gates + spec-match. A fresh adversary grading a predecessor-designed pin is the
    receding-reach spiral the STOP-rule warns against + right-sizing-rigor. The contract is otherwise
    fully graded (adv2 full SUFFICIENT + adv3 MP-5/MP-6 sound).
  - **CURRENCY BOUND — CORRECTED PLAN: no pending_contracts.yaml registration.** The ii-a RED contract
    is pytest-only + mypy-CLEAN (getattr forward-ref idioms), and #461 makes a pytest-only bound read
    RED during the window anyway; a4eb097 (this wave's first contract) committed with `bounds:[]`. The
    intra-wave orphan window is ACCEPTED (CLAUDE.md: "bounds the orphan window to one wave"); the BUILD
    greens ALL the contract reds → CLOSE-OUT currency is 0 RED_ORPHANED with NO bound needed (no reds
    remain post-build). Bound registration is only for reds that SURVIVE the build — ii-a has none.
  - **NEXT:** reviser3 returns → lead-verify + commit → builder (production §7-5 + ~140-site corpse
    reconciliation + F-DUP harness extraction into _governed_contract.py + α promise-registry line) →
    cold-audit (full suite ALONE; verifies build + close-out currency 0 RED_ORPHANED) → commit → ii-a CLOSE.
- 2026-09-11: `reviser3-63b-ii-a` DONE — D-NULLTOKEN closed via `TestResolvePrincipalReturnsNoneForAn
  IdentitylessToken` (2 methods) in test_comms_send_scope_63b_ii_a.py: `resolve_principal(None, …) is None`
  + the empty-subject falsiness leg, both with a `_RaisingPrincipalStore` proving §3.1 decides at the SEAM
  (no store lookup). RED-at-HEAD via getattr idiom; reviser even scratch-probed (correct build greens +
  .subject-direct reds). ruff+typecheck EXIT=0. Lead verified (ruff + full diff read: clean, spec-match).
  Committed `2ad831c`. **ii-a CONTRACT COMPLETE + FULLY GRADED** (adv2 SUFFICIENT baseline `4b5a9de` ·
  MP-5/MP-6 sound `9138687` · D-NULLTOKEN `2ad831c`).
  - **BUILD PLAN:** ONE builder (Opus 4.8) does the COHERENT unit — production (§7-5, per adversary2/3's
    documented reference diff) + corpse reconciliation (D1 all-in-ii-a: credential-the-fake for send AND
    register in `_comms_fakes.py` — one shared seam fix unblocks most of the ~140 sites) + α promise-
    registry line — targeting a GREEN FULL suite. Briefed to PRIORITIZE (contract files green first, then
    corpse), cp -a backup before reporting, and FLAG+checkpoint if capacity forces a split (→ I spin a
    follow-up builder for the remaining corpse). Removed-behavior adjudication on the corpse (the sites
    certified the OLD tokenless-works world → reconcile to credentialed; flag dropped coverage).
  - **F-DUP extraction DEFERRED to an immediate follow-up** (after the core build) — it's a DRY refactor
    of the REAL-store cred harness (3× copy accepted per §11.3); independent of the corpse (fake seams).
    Keeps the core builder's context focused. `_governed_contract.py` grant held for that follow-up.
  - **COMMIT MODEL for the big build:** builder writes to the main tree (lead commits, per convention);
    on the builder's report I commit the build as logical commits (production / corpse / promise-registry)
    for durability, THEN cold-audit the committed build (REFUTE, full suite ALONE, builder≠grader) gates
    the wave CLOSE. Builder cp -a's a scratch backup before reporting (near-miss law).
- 2026-09-11: `builder-63b-ii-a` DONE (`REPORT-builder-63b-ii-a.md`). **FULL suite 11223 passed / 0
  failed / 0 errors (run ALONE)**; mypy + ruff + currency (0 RED_ORPHANED) all PASS. Diffstat: 16 files,
  1193/217 — production (6) + corpse test files (7) + 3 disclosed regression fixes; the 5 contract files
  + 2 cross-file + `_governed_contract.py` BYTE-UNTOUCHED (frozen contract + F-DUP deferral respected).
  - Lead judgment reads: R-WIRE early-close ACCEPTED (test_param_honesty FORCES the wrapper to thread
    capability= once send's spec declares it — unavoidable + forward progress; iii's behavioral battery
    untouched); the 18 in-scope regressions (register_notice/link5/principal_keys_schema) legitimate +
    disclosed; corpse adjudication (assertions preserved, 2 wrong-reason→right-reason fixes) sound.
  - Lead one-random-receipt spot-check: `test_message_governed_ddl_63b_ii_a.py` → 25 passed (matches
    the builder's receipt; §4.F wiring greened).
  - Committed the build `eafb8fd` (ONE coherent green unit — production + corpse are coupled; splitting
    = a RED intermediate). Durable (git, not scratchpad archaeology).
  - Spawned `coldaudit-63b-ii-a` (Opus 4.8, REFUTE) on `eafb8fd`: re-run ALL gates ALONE + mutation-proof
    each seam + the DUAL removed-behaviour inventory (corpse coverage preserved or gutted?) + served-
    string honesty (α/R7/keep render lines) + #107 dirty-store DDL + the 18-regression verdicts + R-WIRE.
  - Untracked test detritus (`test_*.memory.db`) left uncommitted (not staged); REPORT-*.md untracked
    (archived at wave close via git mv). **NEXT:** cold-audit GO → F-DUP extraction follow-up → ii-a
    CLOSE (INDEX Log + archive receipts). GO-with-residuals or NO-GO → triage/route.
- 2026-09-11: `coldaudit-63b-ii-a` → **GO** (`REPORT-coldaudit-63b-ii-a.md`; builder≠grader). Gates
  re-run ALONE reproduce (full suite 11223/0/0, mypy Success, ruff clean, currency 0 RED_ORPHANED);
  **7/7 mutation proofs discriminate** in provenance-asserted scratch (M1 D-NULLTOKEN, M2 agent≡subject,
  M3 Reading-A hybrid, M4 §4.F wiring, M5 routing-not-sharing, M6 OVERWRITE, M7 grant flip); DUAL corpse
  **0 assertions removed** across ~140 credentialed sites; #107 OVERWRITE/option<>/ENFORCED intact;
  served-string α deny-verbs DERIVED; 18 regressions pure-additions (PIN-THE-MISS sound). No CONFIRMED
  defect. Residuals R1–R6 all benign/ruled (read the full table per the C1 law): R1 new-column dirty-
  store DDL (trigger: first CHANGE to a governed message col) · R2/R3 → 63b-iii · R4 cosmetic 18-vs-17 ·
  R5 root hygiene (pkt-65) · #463 :18500 WS drops.
  - Lead read the FULL residual table (not just the GO). Shut down `coldaudit-63b-ii-a` (done) + earlier
    `builder-63b-ii-a` — fleet now EMPTY (only the lead).
  - **ii-a CLOSED** — INDEX Log entry committed `3f69374` (the exit ritual; cites the durable SHA chain).
    Commit chain: `58865ba`(probe)·`a4eb097`(RED contract)·`3497f2a`(ruling)·`7ab8f60`(ruff)·`4b5a9de`
    (revision)·`607907f`(§11)·`9138687`(MP-5/6)·`2ad831c`(D-NULLTOKEN)·`eafb8fd`(build)·`3f69374`(close).
  - **F-DUP DEFERRED to ii-b** (measure-then-tune: extract the shared credentialed harness into
    `_governed_contract.py` once the read-side consumer set is known; overrides the sidecar's build-wave
    timing on capacity/completeness grounds — a lead orchestration call; grant held). R5 root sweep +
    the receipt archive (`git mv` → `receipts/2026-09-11-packet63b-ii-a/`) both DEFERRED to pkt-65 image-
    build prep (reports stay at root so ii-b/iii citations resolve; archive the ii-wave batch together).
  - **NEXT = 63b-ii-b (message READ side)** per the mission, then 63b-iii (dedicated security-auditor).
    Pausing at this milestone for operator direction (active steering this session) before standing up
    the ii-b pipeline. Do NOT start 63c.
