# REPORT-lead-63b — packet 63b (comms MESSAGE family, governed) — LEAD wave report

- `brief-base v14 read`
- `lead-base v6 read`
- `brief project v7 read`

## CHECKPOINT (2026-09-04, operator-directed pause; HEAD 6738402)
- **State:** 63b-i-a (F5) CLOSED. **63b-i-b BUILT (6738402) — mechanism CORRECT (747/0 target
  modules), NOT yet CLOSED**: a cross-cutting reconciliation fix-wave + 1 design fork remain (HANDOFF
  below + the archived REPORT-build-63b-i-b.md §REGRESSIONS). Durable: `lore_recall("63b-i-b build handoff")`.
- `Verdicts acted on:` F5 cold-audit GO @81250d8 (SAME→acted); i-b re-adversary INSUFFICIENT @61dc97f
  (SAME→revised+closed). No STALE acted on.
- `Directives:` rulings/forks routed via the design sidecar (§1.9/§5.1/§2.5 addenda, all committed) +
  AskUserQuestion (the pause fork); 0 prose-duplicated.
- `Rulings:` sidecar §1.9/§5.1/§2.5 all in the committed design doc; 0 body-only.
- `Agents:` ~18 spawned across i-a+i-b; all TaskStopped/retired at checkpoint; ledger rows are zombies
  (no cross-agent retire verb — known limitation). 0 left-running at exit.
- `Uncommitted at stop:` 0 (the stale untracked `resume` file pre-dates this session — left as-is).

## HANDOFF — 63b-i-b RECONCILIATION FIX-WAVE (next session: finish this → cold-audit → i-b CLOSE → ii/iii)
Full spec + exact fixes: `docs/plans/v2/receipts/2026-09-04-packet63b/REPORT-build-63b-i-b.md` §REGRESSIONS.
The i-b BUILD (6738402) is correct (747/0; the builder caught+fixed 2 reference bugs — B an R4
`.update()` false-positive, C a #131-class FP-06 durability bug). The full-suite gate (#452) surfaced
15 cross-cutting reconciliations, ALL OUT of the build's 5-file writable set:
- **Class A (10) — render instruments:** `_render_recalled_memories` now takes `*, subject` + the new
  `render_subject_bound` break the general render-coverage/forgery harnesses
  (`test_link5_render_containment.py` [6], `test_render_slot_inventory.py` [4]). FIX: teach the harness
  to pass a forged Subject when driving `_render_recalled_memories` + register `render_subject_bound`
  as a driven render (#420 coverage-as-checked-variable grows).
- **Class D (3) — stale 63a_iv twin:** `test_memory_enforcement_63a_iv.py::TestEveryRawMemoryMutationIsAllowlisted`
  certifies the OLD raw-mutation world (superseded by 63b_ia's effect-based L1-coverage tests, GREEN
  with the build). FIX: DELETE it (builder rec) or update its allowlist DATA — a delete-vs-update ruling.
- **secret-typing (1):** the committed i-b probe `scripts/probe_supersede_throw_rollback.py:110` mints
  a SecretStr outside the `test_secret_typing` allowlist → adjudicate its origin (like 63a fix2/fix6).
- **typecheck (3 errors):** `test_memory_f5_registration_63b_ib.py:286/287/292` — an `assert … is not
  None` union-attr narrowing (`ObservedEffect|None`).
- **C-RESIDUAL DESIGN FORK (sidecar, non-blocking):** #441 compensation is now supersede-scoped
  (builder's C-fix, sound, matches design §2.3's LOW-bound). Fork: narrow to domain-rejection-only
  (never on transport)? Builder recommends supersede-scoped for now.
Then: full suite green + `pending_contract_gate.py --currency` 0 RED_ORPHANED + a cold-audit
(builder≠grader, FULL suite) GO → i-b CLOSED → INDEX Log + milestone. Then 63b-ii-a/ii-b/iii.

## SUMMARY BLOCK (updated as the packet runs — final numbers at close)

- **State:** in_progress — **63b-i-a (F5) CLOSED**. **63b-i-b** RED contract COMMITTED (6f64649,
  26 RED-at-HEAD, satisfiability 70/0 under Reading A incl. #436 byte-identity 8/8; probe caught the
  §2.2 gap #456 → RULED §2.5 9a42ef4). Adversary INSUFFICIENT (1st i-b fail): F1 (BLOCKER C-DEF,
  probe-confirmed) — the rescope pin asserts the RAW marker 'governed_conflict' (underscore), but
  §2.5 keeps raw text OUT of the exception (fixed label 'governed conflict' + rider-ii hygiene) →
  unsatisfiable on a correct §2.5 build; candidate 2 (no _txn classification unit pin); candidate 3
  (render coverage pin HARDCODES _render_recalled_memories vs §3.3-ii derive). Adversary STALLED
  before the wrong-build matrix + #436 QUANTIFIER attack. REVISED (61dc97f) by contract-63b-i-b-3
  (reviser -2 STALLED, respawned -3 liveness-first): F1 SPLIT at honest layers (store-layer
  TxnGovernedConflictError + governed-layer GovernedConflict via guarded_write, no raw marker) +
  _txn classification unit pin (test_surreal_store/test_retry_seam) + render-coverage DERIVED (§3.3-ii).
  RED-at-HEAD 27+ right-reason; satisfiability 25/0 §2.5-compliant no-hang; ruff clean. Full
  re-adversary (61dc97f) INSUFFICIENT (2nd i-b fail of 3): all 3 fixes DISCRIMINATE + #441 matrix +
  §2.5 pinned + 80/0 satisfiability, but ONE hole (#436 QUANTIFIER): _seed_dirty_lifecycle seeds
  scope="server" MONOCULTURE → a scope-collapse replay passes (no scope-diversity guard, unlike
  owner). Reviser-4 adding test_the_dirty_store_carries_scope_diversity + a distinct grantable scope
  + proving discrimination. Reviser-4 CLOSED it (187201c): scope-diversity guard + agent-private seed;
  discrimination PROVEN (adversary's exact scope-collapse wrong build now reds the fidelity byte-diff;
  guard anti-vacuous). **i-b CONTRACT COMPLETE + adversary-satisfied.** i-b BUILD next (proven 5-file
  reference: governed.py/memory/ledger.py/memory/local.py/server.py/store/_txn.py, 80/0). Then
  cold-audit → checkpoint. Commits: design 0280757/e4b8945/103c661/9a42ef4; probe f6db0ba;
  contract 519c0bb→72fc220; build 81250d8; cleanup b2f9b0e; i-b contract 6f64649.

## OPERATOR DIRECTIVE (2026-09-04): PAUSE when 63b-i-b is DONE — update state/memory/docs, commit
  everything + PUSH, write a startup prompt for the next session (63b-ii onward), retire comms, exit.
  → drive i-b through cold-audit GO + commit, THEN checkpoint. Do NOT start ii-a.

## Wave 63b-i-a — F5 cold-audit GO (81250d8, REFUTE, builder≠grader)
- Independent gates: full repo suite 11077 passed / 0 failed; currency PASS 0 RED_ORPHANED; ruff +
  typecheck clean; F5 contract 33/0 serial NO HANG; migrated 27/0. Mechanism REFUTE-probed +
  mutation-proven: effect detection verb/shape-agnostic; exempt 4 legs independent; #454 re-entry
  closed; populations + coverage checked-variables. Residuals dead-code/prose-currency only.
- Cold-audit beat the builder's disclosure (C1 "read the residual table"): found 3 MORE dead fns
  the builder left (seam_modules_for_tree_allowlist / _module_for_repo_relative_file /
  _originating_prod_site) — (d) is a clone-able #446 trap for ii-a → delete before ii-a.
- Cleanup deferred: (c) _defined_test_names DRY dedup (tracked by the allowlist flag → 63b later),
  (e) optional latent-double-arm pin.

## Wave 63b-i-a — F5 BUILT (81250d8), cold-audit running
- Build: the §1.9 mechanism (ExemptToken class-CM + sys._getframe(1) origin; function-local migrate
  statement; ensure_ready write_guard; _sdk_guard hook+__wrapped__; verb/shape-agnostic effect
  detector = persistent dispatcher + query_raw-only observation, 4-leg+label-effect classifier,
  derived grammar, AST populations, constructed oracle). 20 RED pins → GREEN (33/0 no hang).
- ⚠ The full-suite gate CAUGHT a #452-class cross-cutting regression (validating the mandate): the
  contract's new test-tree evidencing scan tripped test_ast_reach_helpers' whole-tree-clone detector
  (pre-existing at 72fc220 — reviser+adversaries ran scoped runs, never the full suite). Lead-direct
  1-line _ALLOWED_WHOLE_TREE_CLONE_FILES reconciliation (evidence-backed test-tree enumeration, same
  class as _iv/_v; re-open trigger). Currency gate re-run PASS.
- Builder disclosed 2 prose-currency RESIDUALS (dead _mutation_verb_for_table w/ stale R4-c docstring;
  observe_ docstring "at HEAD" staleness) → cold-audit adjudicates blocker-vs-cleanup.

## Wave 63b-i-a — CONTRACT SUFFICIENT (2 adversary passes)
- 1st adversary INSUFFICIENT (2 missing pins + F-TRAP-3) → sidecar §1.9 ruled 5 items → reviser
  fixed all + found&fixed 2 more C-DEFs → 2nd adversary SUFFICIENT (independent: all wrong builds
  red, quantifier ∀ real, exempt legs independent under ExemptToken reshape, oracle dict-equality,
  60/0 satisfiability NO HANG). Builder gotchas locked (for the build brief): query_raw-ONLY
  observer via __wrapped__ (lore #454); persistent dispatcher + registry; governed_exempt class-CM
  sys._getframe(1) origin → ExemptToken; function-local migrate statement; constructed ensure_ready
  oracle w/ query_raw rpc-envelope snapshot; classifier duck-types ExemptToken.

## Wave 63b-i-a adversary verdict (REPORT-adversary-63b-i-a.md @ 519c0bb) — INSUFFICIENT
- **2 missing pins** (contract-completeness, author adds): (1) classifier must ENFORCE a label
  frame's effect predicate ∀ label frame (a "bless any labeled write" build passes all 30 —
  re-widens the #138/R2 hand-set-label bound); (2) governed_populations() reach must be a CHECKED
  VARIABLE (hardcoded {memory} passes — §1.6-vii has no committed instrument; the fifth-defeat
  lesson inside the population instrument).
- **1 borderline C-DEF (F-TRAP-3):** ensure_ready oracle compares DDL-string names vs engine's
  `embedding.*`/`labels.*` → correct build reds (#131/#107 "test env is a fiction" class).
- **perf RESOLVED — reference-build bug (observer re-entry .query→patched .query_raw), CLOSED,
  lore #454.** Fix: observe query_raw ONLY + read via unwrapped __wrapped__.
- **Design-wording traps + gotchas (→ sidecar #9007):** F-TRAP-1 (§1.5c-iii derive from
  _governed_field_specs callers), F-TRAP-2 (§1.4 function-local not module constant — the
  _MIGRATE_GOLDEN docstring teaches the trap), GOTCHA-B (persistent dispatcher+registry),
  GOTCHA-C (origin capture at exempt context-entry — stack walk lands on _txn.py; ⚠ possible
  governed.py writable-set widening beyond "exempt API only" — the ONE fork for the sidecar).
- Satisfiability: 57/0 vs a correct reference (30/30 serial 9.26s NO HANG), 6 pin-forced fixes.
- `Verdicts acted on:` (none yet)
- `Directives:` 0 ledger / 1 wake (sidecar split-coupling q, #9001) / 0 prose-duplicated
- `Rulings:` all 5 forks ruled in docs/design/2026-09-03-packet63b-design.md (committed 0280757) — 0 body-only
- `Agents:` spawned: design-sidecar-63b [standby], probe-63b [STOPPED-stalled], probe-63b-2 [done+STOPPED], contract-63b-i-a [STOPPED-stalled-twice, work externalized], refbuild-63b-i-a [nested by contract author, hung+dead], adversary-63b-i-a [running]. Stopped-dead confirmed via TaskStop: probe-63b, probe-63b-2, contract-63b-i-a; refbuild already dead. Left-running=0. Ledger-retired=0 (no cross-agent retire verb — zombie rows, cosmetic).

## Commits (63b, on feat/surreal-unification)
- `0280757` docs — 63b design rulings (sidecar authoritative)
- `f6db0ba` chore — message read-filter probe over real emitter (feeds 63b-ii)
- `e4b8945` docs — §5.1 split addendum (i-a→i-b)
- `519c0bb` test — **63b-i-a RED contract** (F5 effect-based root-fix; 30 tests, 17 RED-right-reason; migrations shed R4-a/R4-c + observer-patch-set)

## Stall recovery (63b-i-a contract, 2026-09-03) — LESSON
The contract author spawned a NESTED sub-agent (refbuild-63b-i-a) for the C-DEF satisfiability
receipt. That refbuild's contract run HUNG (16min on the store-heavy tail: effect observer ×
store round-trips × concurrency); the completion wake never fired → BOTH agents stalled waiting.
I ground-truthed the dead gate process (PID 3377404), woke the contract author (it recovered,
diagnosed: **46/57 passed under the reference build, effect pins green → contract SATISFIABLE**;
the hang = an observer re-entrancy/perf bug, NOT unsatisfiability), then it stalled AGAIN.
TaskStopped both; committed the verified RED contract; handed the definitive satisfiability
receipt + the perf investigation to the adversary. **LESSON (carry to i-b/ii contracts): NO
nested sub-agent spawns for satisfiability — run it INLINE + BOUNDED (serial + timeout), or let
the adversary's own reference build serve. A nested spawn's hung run breaks the wake chain.**

## Open question for the adversary (perf/re-entrancy)
The F5 observer diff must use `event.original` (the UNWRAPPED SDK door, §1.8) — refbuild's hang
was almost certainly the wrong-door re-entrancy deadlock. Adversary confirms reference-build-bug
(CLOSED, builder gotcha) vs DESIGN-flaw (observer armed during an N-way contention battery →
lock serializes it → escalate to sidecar). Its correct-reference bounded run is the test.

## Timeline addendum
- 2026-09-03 pm: design ruled+committed (0280757); split i-a→i-b confirmed (§5.1, e4b8945);
  probe done+committed (f6db0ba); F5 RED contract written, gates green, 17 RED-right-reason,
  committed 519c0bb after a nested-spawn stall recovery; adversary-63b-i-a spawned (grade +
  definitive satisfiability + perf investigation, INLINE + BOUNDED).
- `Uncommitted at stop:` n/a (running)
- **Decisions needed:** none for operator (sidecar has authority). One split-coupling q pending WITH the sidecar.

## Authoritative design (docs/design/2026-09-03-packet63b-design.md @ 0280757) — RULED

- **§1 F5 root-fix (headline):** detection is an EFFECT (before/after STATE DIFF of the governed
  table via SELECT * + INFO FOR TABLE), observed at the SDK connection class via a NEW `_sdk_guard`
  hook — verb/shape/table-AGNOSTIC (kills R4-a substring + R4-c INSERT..ON DUPLICATE/CREATE/RELATE).
  `governed_exempt` → STATEMENT-scoped, 4 independent legs (name ∧ golden text ∧ effect predicate ∧
  origin site). L1 DEMOTED to a coverage floor with a vendor-DERIVED grammar (SURREALQL_STATEMENT_
  KEYWORDS, currency-pinned to surrealdb-docs). Population set DERIVED from surreal_schema
  (`_governed_field_specs` callers ∪ relation tables with a governed endpoint). §1.7 = precise
  change-table vs 10.9-A CORRECTION. Closes #444/#445/#448/#449 (delete R4-a/R4-c bound pins).
- **§2 #441 supersede atomicity:** `authorize_guarded` (Python leg, deny-first, NO effect) → ledger
  record → ONE composed execute_transaction [guarded close FRAGMENT + audit + successor UPSERT] with
  the conflict guard IN-STORE (`LET $hit=(UPDATE…RETURN AFTER); IF array::len($hit)=0 { THROW
  "governed_conflict:…" }` — spec-proven to abort the whole txn). guarded_write = authorize_guarded +
  fragments + execute (ONE impl; Python row_count==0 branch DELETED as dead). Ledger compensation on
  txn failure. Cross-store 2PC bound + compensation window named+pinned.
- **§3 #436/#453 + #437:** ledger metadata gains owner/scope/created_at/valid_until/superseded_by;
  NEW `MemoryLedger.retire`; `_replay_record` reconstructs faithfully incl. same-owner supersede
  closes → kills the revive-on-rebuild bug (#453). "Block member reads behind re-migrate" REJECTED.
  #437 = ONE `AppContext.render_subject_bound(subject)` line on EVERY governed read render incl. the
  empty case; NO withheld counts (existence leak).
- **§4 six forks (binding):** A send scope by keep KEY via lifted `governed.resolve_write_scope` · B
  drain/ack ONE-txn (§4.3 letter) · C **BOTH agent.owner_principal AND message migrate legs in 63b
  (RULED SCOPE WIDENING — see below)** · D capability= via `CommsActionSpec.requires_capability`,
  register mints, agent-name ≡ capability-name · E story/rollup splice filter + rollup msg leg names
  its bound (never a count) · F message governed DDL is NOT at HEAD — 63b-ii adds `_governed_field_
  specs`+`_governed_index_statements(MESSAGE_TABLE)`; `to` is a dependent (not column-governed) pop.

## ⚠ RULED SCOPE WIDENING (within sidecar's delegated authority — carried as a named brief line)

§4.C: **63b ships BOTH migrate legs** — `_migrate_agent_owner` (agent.owner_principal, a pkt-62
column that already EXISTS on agent; single-principal-precondition stamp to the operator principal)
AND `_migrate_message_owner` (owner_agent=sender, owner_principal=sender.owner_principal, scope=
keep:<project>; refuses if any agent.owner_principal IS NONE — the §2.6 checked order). Both are
four-leg F5 exempt frames. DERIVED from §0(b)/§2.1/§2.6; NOT a new operator scope grant. 63c's
SEPARATE job stays agent-as-a-governed-POPULATION (scope + fleet filtering).

## Wave plan (sidecar §5 cut; lead orchestration)

- **63b-i SPLIT — CONFIRMED by sidecar §5.1 addendum (2026-09-03):** i-a (§1 F5 instrument) → i-b
  (§2 #441 + §3 #436/#453/#437). F5-first (build the net before the fish); one-way dependency.
  - **i-a writable set:** governed.py (exempt API only), principals.py (_migrate_memory_scope:
    statement constant + kwarg), memory/local.py (ensure_ready label + _recreate flip only),
    tests/_governed_contract.py, tests/_sdk_guard.py, tests/test_memory_enforcement_* (+ delete
    R4-a/R4-c pins). Q1 refinement: `ensure_ready` becomes a labelled DDL frame (else the DDL leg
    is unsatisfiable — every fixture calls ensure_ready at construction). Population @HEAD = {memory};
    message/to = RED_ADJUDICATED(owner=63b-ii).
  - **i-b writable set:** governed.py (authorize_guarded/GuardedPlan split), memory/local.py
    (remember/invalidate/_replay_record/_build_content), memory/ledger.py (retire/delete), server.py
    (recall render + render_subject_bound), the F5 allowlist DATA, tests/test_memory_* for #441/#436/
    #437. i-b EXCLUDES the F5 instrument (a change it needs there is a STOP-and-flag).
  - **STATUS:** contract-63b-i-a spawned (F5 RED contract).
- **63b-ii-a** — message write side (§4.F DDL, §4.C migrate legs, SF-63-1 session keep at register,
  §4.D capability=, §4.A send scope stamp; F5 message/to registries GREEN for send). Probe-63b-2's
  message read_filter EXPLAINs feed ii.
- **63b-ii-b** — message read side (§4.B drain/ack one-txn, §4.E story/rollup+await, render_subject_
  bound on comms reads, F5 registries GREEN for drain/ack).
- **63b-iii** — dedicated security-auditor over the wire (§6 target, F3 fixture, Leg-2 forgery table,
  SF-63-1 headline).
- Each wave = full pipeline (contract → contract-adversary MANDATORY → build → cold-audit FULL suite
  → commit); iii adds the security-auditor. Currency gate solo at every close-out (#452 lesson).

## Context established (2026-09-03, HEAD cedb20d)

- 63a is CLOSED at `cedb20d` (currency green, 0 RED_ORPHANED). 63b builds on the 6 substrate
  seams: `governed.resolve_subject` / `read_filter` / `guarded_write(store=StoreHandle)` /
  `_governed_field_specs`+`_governed_index_statements` / `migrate-governed`+`LegacyMapping` /
  the F* pin families; plus `AppContext._resolve_subject` composition root (63a-ii).
- **Authority model (operator 2026-09-03):** the Fable design sidecar is AUTHORITATIVE for 63b
  design/forks/ambiguity. Escalate to operator only after 3 FAILED CONTRACTS at a design point,
  or a permission/scope grant, or a destructive/#107-class surprise. This OVERRIDES CLAUDE.md's
  default escalation triggers for 63b.
- **63b scope (design doc + lore_recall authoritative):** route message family
  (send/drain/ack/await/story + rollup msg leg) through 63a seams UNCLONED; `capability=` identity
  arg + register→session-keep binding (SF-63-1); message-row migration (legacy → owner_agent=sender
  + owner_principal=sender.owner_principal, single-principal PRECONDITION-refuse backfill) + DDL
  (owner_principal/owner_agent option<record>, scope option<string> via _define_field OVERWRITE;
  IF-NOT-EXISTS indexes on scope + owner_principal ONLY — owner_agent NOT indexed, named re-open
  trigger); the F5 RUNTIME ROOT-FIX (task 571ef1a / #449 — headline, property to invent → Fable
  rules); bounds #436 (replay governance-stamp loss), #437 (render Subject-scope line), #441
  (supersede close-first atomicity → §10.9-D authorize-first-execute-later).
- COMMIT-ONLY (deploy = pkt-65 joint cutover); must NOT break the live pre-retrofit fleet.

## Pipeline per wave

probe (extend scripts/probe_read_filter_63.py → MESSAGE table, EXPLAIN=IndexScan, P-controls,
BEFORE contract freezes) → contract (Opus, to Fable's ruling) → contract-adversary (MANDATORY) →
build (Opus) → cold-audit (Opus REFUTE, FULL repo suite / currency gate as regression scope —
finding #452 lesson: cross-cutting audits MUST run full suite) → DEDICATED security-auditor
(cross-principal wire isolation, design §6) → commit. Roster Opus 4.8 via opus48-worker (no
model override). A failing contract routes back to Fable; 3rd failed contract → operator.

## Environment caveats

- Prod store :18500 throwing transient WebSocket resets (#422) — ledger/memory writes may need a
  retry (hit it on first register). Test store ws://127.0.0.1:18000 unaffected.
- In-process subagent spawns were STALLING in prior sessions — watch for ~3-4 min of no
  report/tree activity → TaskStop + respawn (suffixed name) + tight incremental-write brief.
- Untracked `resume` file at repo root (Aug 27, pre-dates this session) — a stale handoff doc;
  left as-is, flag at close (not mine to delete without operator).

## Timeline / decisions (append-only)

- 2026-09-03: Registered lead-63b (session packet63b). Read all required base + design + store
  refs. Spawned design-sidecar-63b (general-purpose model=fable) with the front-loaded 5-fork
  ruling brief (F5 runtime root-fix / #441 atomicity / #436 replay + #437 render / message-family
  ambiguities / wave structure).
