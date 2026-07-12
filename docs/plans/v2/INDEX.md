# lore v2 — DeadReckoning+ · PACKET INDEX (plan of record, restructured 2026-07-10)

This replaces the monolithic resume-doc chain (`~/.claude/plans/lore-v2-*-RESUME.md`)
as the forward plan. The remaining work is decomposed into **work packets** (PKT-01…23),
each sized to build inside ONE session (≈0.1–0.35 P7-window-units) with a fresh context
that loads only: repo CLAUDE.md (auto) · this INDEX · its own packet file · the
DESIGN-LAW sections the packet names · the spec files the packet points at. Nothing else.

Sources folded in (extraction receipts in `receipts/`): MASTER-PLAN.md (§-references
below point into it) · the P7/P8a–P8e/SLATE/DETECTION resume docs · all 9 docs/design
specs · both docs/orchestration records · docs/eval records · LORE_EXTERNAL_REVIEW.md
(2026-07-10). The old resume docs remain as history; **their still-live content lives
HERE now** — a packet session must not need to read them.

## Declared targets (operator)
- **Replace the odoo-code MCP** (declared 2026-07-11): lore serves the Odoo corpus
  (~20k+ files / ~53k chunks) as its code-intelligence surface. The Odoo track:
  PKT-18 (cross-tier compare) → PKT-27 (scale certification) → Odoo onboarding packet
  (pool item 19). Live-DB introspection stays with odoo-dev by design.

## State of record (verified 2026-07-10)
- Branch `feat/surreal-unification` @ **f0616ed** (not pushed). Full suite at last
  lead-run: **3184 passed / 1 skipped**.
- **Deployed image f891c89e212d** on BOTH containers (lore-lore :9202, DI :9201).
  14-tool surface; cosine substrate live; floor **0.50649** (4-group survey + drift
  trigger); P7→P8d′, SLATE S1–S7, and the closure wave (#74–#79, #81) all CLOSED.
- Standing eval bar: **35-pair set, pinned claude-sonnet-4-5-20250929, client metrics**
  (accuracy ≥33/35 · tokens-per-correct ≈1375-era · taxed-calls ≈0). 11-pair calls-leg
  retired. Last receipts: 33/35 · 6.46 calls · 1440.8 tok (2026-07-07).
- Test store: spike-surreal ws://127.0.0.1:18000 (podman start after reboot).
  Production store :18500 — NEVER pointed at by tests.

## Packet protocol (read once — this is the whole ritual)
**Boot:** (1) repo CLAUDE.md auto-loads (process law: gates, TDD, orchestration,
deploy, store idioms — packets never restate it). (2) Read this INDEX + your packet +
the DESIGN-LAW.md sections your packet lists. (3) Start lore if down (`lore-deploy`
skill), then `lore_index()` freshness, `lore_findings status=open`, `lore_tasks` —
mint/claim your ledger rows. (4) Run your packet's ENTRY CHECK; if ground truth
contradicts the packet, STOP and surface — never build on a stale premise.

**Exit:** gates green (scoped pytest + `scripts/typecheck.sh` + ruff) → cold REFUTE
audit for wave commits → one-concern commits → deploy if the packet says DEPLOY
(rebuild + recreate BOTH, never restart) → resolve/file findings with notes → flip
your row in the Status table below + append ≤5 lines to the Log at the bottom →
ledger rows done. **No new resume docs, ever.** State of record = git + this INDEX +
the lore ledger.

**Scope:** the packet's IN list is the grant; anything else found en route is
surfaced to the operator (repo law). Packet files are STATIC — scope changes are an
operator ruling recorded as an edit to the packet + a Log line.

## Sequence + status
Operator-ruled order (2026-07-07): floor calibration first (Option B), then detection,
then ledger verbs, then P8e → P8f → v1.0 → P9 → P10. `∥` = parallel-safe with its wave.
**Resequenced 2026-07-11 (operator, see Log): the agent-comms subsystem — PKT-06 (C0)
then PKT-28 (C1–C5) — now precedes PKT-01 floor-calibration.**

| # | Packet | Wave | Size | Depends on | Status |
|---|--------|------|------|-----------|--------|
| 01 | floor-calibration-design | A | 0.15 | — | open (after comms) |
| 02 | floor-calibration-build | A | 0.30 | 01 ruled | open |
| 03 | surface-residues (#84–#88, #64, #80, #82, docs truth) | A ∥ | 0.20 | — | open |
| 04 | detection-contract | B | 0.15 | — | open |
| 05 | detection-build | B | 0.35 | 04 ruled | open |
| 06 | ledger-verbs (row f38f3b96) — C0 of agent-comms | C | 0.30 | — | **done** |
| 28 | agent-comms C1–C5 (C0 done+deployed; Phase-0 render-safety foundation done @ c30edd6 commit-only; C1 registry+briefs NEXT) | C | ~1.4 phased | 06 | **NEXT** |
| 07 | role-wiring (all\|mcp\|scout + creds) | D | 0.30 | — | open |
| 08 | containerfile-astroid (#24) | D ∥ | 0.25 | — | open |
| 09 | config-dynamism (ruled #13 table, #72, #12) | D ∥ | 0.35 | — | open |
| 10 | drills + split-topology e2e | D | 0.30 | 07, 08 | open |
| 24 | ledger-retirement (singular-store ruling) | D ∥ | 0.20 | — (before 12, 13) | open |
| 11 | lore-deploy-rework (finding #13, scaffold) | E | 0.30 | 09 | open |
| 12 | migration-machinery (Shape D, N1/N2/N3/N6) | E | 0.30 | §8 Q1–Q4 answered | open |
| 13 | DI-migration + **v1.0 SHIP** | E | 0.25 | 11, 12, GO/NO-GO | open |
| 14 | loresage package | F | 0.25 | v1.0 | open |
| 15 | enrichment-worker | F | 0.30 | 14 | open |
| 16 | detectors + raise_issue escalation | F ∥ | 0.25 | v1.0 | open |
| 17 | graph/search v1.1 (#70, #3, RELATE, PageRank) | F ∥ | 0.35 | v1.0 | open |
| 18 | cross-tier compare (Odoo 15→19 prep) | F ∥ | 0.25 | v1.0 | open |
| 19 | memory maintenance (decay/expiry sweeps) | F ∥ | 0.15 | v1.0 | open |
| 25 | memory reconciler (det. tier + loresage tier) | F | 0.35 | v1.0; 14 for LLM tier | open |
| 26 | semantic summary reuse (5b, promoted) | F | 0.25 | 14; 20 helpful | open |
| 27 | Odoo-scale ingest certification (gap 6) | F ∥ | 0.30 | 05 rec.; pull-earlier OK | open |
| 20 | trace-deepening + trace_monitor backstop | G | 0.30 | v1.0 | open |
| 21 | hosted-security (design first) | G | 0.30 | 20 | open |
| 22 | ui-foundation | G | 0.30 | 20 | open |
| 23 | ui-graph-explorer + Agent-SDK chat | G | 0.35 | 21, 22 | open |

External-review ordering constraint (2026-07-10, adopted): **UI ships after trace and
authorization models stabilize** — hence wave G's internal order.

## Operator decision pool (each blocks nothing until its packet arrives)
1. **PKT-04 fork:** prose-ish suspect flag — in-text vs metadata + serve-time injection.
2. **PKT-12 entry gate:** migration §8 Q1–Q4 (docs/design/2026-07-04-migration-concurrency.md:317-333). Rec: Q1=(a)+(b), Q2=confirm ns/db-only, Q3=accept seconds-long freeze, Q4=dry-run Phase A first.
3. **PKT-13:** Shape-D GO/NO-GO after Phase A; deferred retire confirmation; post-soak shared-Qdrant orphan cleanup + `QDRANT__SERVICE__API_KEY` removal from lore.env.
4. ~~SQLite memory-ledger exception~~ **RULED (operator, 2026-07-11): SurrealDB is the
   SINGULAR durable store for lore data — the SQLite ledger retires in ALL modes**
   (external review gap 1 + the k8s/split contradiction found in discussion: MASTER-PLAN
   §1 says both "stateless → N replicas" and "ledger on MCP host"; SQLite cannot ride
   stateless replicas). Execution = **PKT-24** (writer/backfill removal, parity receipt,
   store-level backup posture, resilient-open honesty); PKT-12's N1 reshaped (replay
   semantics move into the N3 driver); PKT-07's fork dissolved. DESIGN-LAW §14 carries
   the ruling. v0.3 ledger files stay frozen as the migration import source until
   post-soak.
5. **#49 instructions sizing** (575 tok vs plan ~350; full surface 8,245 claude-equiv vs ~2.5k estimate). REC: ACCEPT — the 35-pair bar is the arbiter.
6. **detail_level reshape** (§5 `detail: refs|signatures|source`) — ruled out of P8d; place in PKT-17 or REJECT.
7. **T7** search default budget 1100→~1600 · **T8** `memories=` param (possibly mooted by T3) · **T9** re-expose what_imports/tests_for (NOT recommended; only if the bar re-misses) — docs/design/2026-07-06-p8dprime-fix-specs.md:480-491.
8. **D4 rename** served fused `score` → `fusion_rank` (ledgered at weak-match close). Fits PKT-03 if approved.
9. **Air-gapped opt-out** for the hard Anthropic-key boot requirement (revisit-later TODO, P8a:110).
10. **Verify rebuild-caveat**: harder gate than caveat-during-rebuild? (P8c:154).
11. **Watcher skip-path posture** ack (store blip during live-drain skip kills the watcher worker — P8e-RESUME item 3).
12. **Spectron**: waitlist standing; backend re-decision on invite (spike list in MASTER-PLAN §6 P7).
13. **DI doc-content import** (DECISIONS.md/GOTCHAS.md → kind-tagged memories) — separate content migration, schedule ad hoc.
14. **#55 investigation row**: fresh-session ToolSearch can't resolve lore tools (2nd recurrence) — dedicate a row.
15. **Upstream report** of the mcp-builder TextContent serialization bug (docs/eval/2026-07-04-p8a-baseline.md:123).
16. ~~Response/render caching~~ **RULED (operator, 2026-07-11):** flavor (a) render
    memoization DROPPED — no latency need at this time; do not build. Flavor (b)
    summary reuse PROMOTED → **PKT-26** (serving form ruled: `(ai summary)` marked,
    additive, citation-hash-gated).
17. **PKT-25 autonomy ruling** (contract-time): flag-only vs propose vs
    auto-apply-with-audit, per reconciler action class.
18. **Retrieval-liveness as a dead-code corroborator** (gap-3 discussion,
    2026-07-11): once PKT-20 links traces→chunks, "never served in N months AND zero
    prod refs" is a strictly stronger dead signal. Cheap byproduct; strike or keep —
    if kept, rides PKT-20's exit as an extra dead_code caveat line, still HEURISTIC-
    bannered.
19. **Odoo onboarding packet — sequencing + scope** (after PKT-27 receipts): XML
    reference extractor (framework-mediated calls — the dead-code truth prerequisite,
    memory: odoo-target-needs-xml-reference-extractor), **MRO + ORM metadata capture
    per PKT-27's assessment** (operator-flagged: _inherit/_inherits model merges,
    field-string refs, super()-chain dispatch), manifest/csv chunker extensions, tier
    layout (odoo15-core/odoo19-core static + custom live), cutover from odoo-code per
    the struck parity matrix. Operator schedules; wants its own design pass.

## Watch list (no packet; verify-on-contact)
- Findings whose live state needs a ledger check at next boot: #1 (indirect-coverage,
  acknowledged-canonical), #2 (tests_for misses config.py — a bug), #3 (routed PKT-17),
  #4 (routed PKT-02), #10 (routed PKT-04), #12 (routed PKT-09), #34 (routed PKT-03), #48.
- **Wave-A boot duty:** the pre-P8d open-finding inheritance (#14–#16, #20–#22,
  #26–#29, #33, #35, #37, #40–#42, #44, #47…) is NOT individually routed here — the
  first wave-A session triages the live open set: route each to a packet, the pool, or
  an operator wontfix. No silent drops.
- Open research note (no evidence either way in literature/vendor practice): whether
  displaying scores to tool-using LLM consumers helps — our three-model consult remains
  the only direct data (weak-match external validation, element d).
- Graph composition invariant + hot-row `_apply_mint` pattern + two-step recreate —
  now in DESIGN-LAW.md; cite it, don't rediscover.
- `scratchpad/` at repo root is finding #72 corpus pollution — fixed by PKT-09;
  until then keep session artifacts OUT of the repo root.

## Log (append-only; ≤5 lines per entry)
- 2026-07-10 · plan restructured into 23 packets by the Fable lead; sources extracted
  with receipts; old resume chain retired as history. Awaiting operator strike/approval.
- 2026-07-11 · external-review gap-1 discussion → OPERATOR RULING: SurrealDB is the
  singular durable store; SQLite ledger retires (PKT-24 added; PKT-07 fork dissolved;
  PKT-12 N1 reshaped; DESIGN-LAW §14). MASTER-PLAN §1's "ledger stays" clause is
  OVERRIDDEN by this ruling.
- 2026-07-11 · gap-2 discussion → operator corrections: author discipline is not a
  durability mechanism — PKT-25 memory reconciler added (deterministic + loresage
  tiers; #4 uncertainty-minting rides it); personalized-PageRank seeding into PKT-17
  ("borrow this"); response-cache candidate pooled (item 16). Tri-temporal stays out
  (conclusion agreed, my cost argument retracted).
- 2026-07-11 · gap-2 close + gap-3 + gap-6: 5(a) render memoization DROPPED, 5(b)
  promoted → PKT-26; PKT-20 gains serve-side facts + usage-proxy aggregates +
  calibration synergy; PKT-25 proposals carry rationale; PKT-06 mandatory-done-summary
  proposal. OPERATOR TARGET DECLARED: replace the odoo-code MCP → PKT-27 scale
  certification added + Odoo-track pool item 19; gap 6 is certification, not
  positioning.
- 2026-07-11 · OPERATOR RESEQUENCING: agent-comms subsystem — PKT-06 (C0) + new
  **PKT-28** (C1–C5) — jumps AHEAD of PKT-01 floor-calibration. SurrealDB-backed durable
  store-and-forward PULL comms: new `lore_comms` tool (exact-set pin 14→15), `await`
  BUILT, graph nodes agent/message/brief + edges to/briefed/blocks, append-only struck
  as a requirement. Plan of record: ~/.claude/plans/one-of-claude-codes-nifty-garden.md.
- 2026-07-11 · **PKT-06 (C0 of agent-comms) LANDED + DEPLOYED.** Four ledger verbs
  (rollup / create_many all-or-nothing / resolve_many+acknowledge_many / mandatory
  done-summary+report_path) on the existing lore_tasks/lore_findings surface (zero new
  tools). Cold audit caught a render row-forgery → `_sanitise_line` promoted to shared
  `loremaster/sanitise.py` (finding #34→#90) + a registry-driven injection meta-test.
  Gates 809/0 · mypy 0 · ruff clean · cold re-audit GO. Commits 78b1fa6 (seam) + f80e95a
  (verbs); image **cd7c07a11534** on lore-lore (DI on-demand, picks up on next start);
  smoke green (arc + mandatory-summary + live forgery-guard); row f38f3b96 done. NEXT =
  PKT-28 **C1** (registry + briefs). #90 routes tree-wide render-hygiene → PKT-03.
- 2026-07-12 · **PKT-28 Phase 0 (render-safety foundation) LANDED @ c30edd6, COMMIT-ONLY**
  (operator: C1 session deploys both containers). SafeLine/Rendered seam + AST template/mint
  pins + subprocess-mypy meta-test + 3 live-forgeable wraps pulled forward (#90→#92). Cold
  audit NO-GO (mypy does NOT enforce LiteralString/PEP 675) → fix waves → GO; suite 3846/0;
  #7061 edge probe SAFE. Spec: docs/design/2026-07-11-render-safety-foundation-ruling.md (v3).
- 2026-07-12 · **PKT-28 C1 (registry + briefs) LANDED + DEPLOYED.** `lore_comms` is the 15th
  tool (exact-set pin 14→15): register / heartbeat / brief_get / brief_publish / brief_ack /
  fleet, over new `agent` / `brief` / `briefed` / `brief_counter` slices + `agents.py`
  (AgentRegistry) + `briefs.py` (BriefLedger). Commits **cfb36d2** (store) + **7917eaf**
  (surface) + **9176bcd** (spec v4); image **98259483ed80** on lore-lore (DI on-demand, picks
  up on next start); suite **4757 passed / 1 skipped / 3 xfailed** (+911 = the comms suite,
  every delta accounted); mypy 0 · ruff clean. Smoke GO on the live surface: bootstrap
  register → brief served at register (fenced, ack via=register) → briefed edge → coverage/skew
  session-tagged → fleet header sums → hostile agent name REFUSED by the charset guard →
  hostile brief body stayed inside a 5-backtick fence.
  **FIVE defects, none caught by a builder gate — all found by cold audit:** (1) the version
  mint hard-errored under real contention (TOCTOU + a jitter seed derived from the CONTENDED
  ROW's id → every racer slept the same duration and re-collided in lockstep; budget < racer
  count) → per-name counter-row UPSERT, holds 8/16/32-way; (2) coverage/skew silently ignored
  session scoping — the scoped branch was DEAD CODE; (3) fleet never grouped by session, so
  two different agents named `fixer-b` rendered identically; (4) `brief_counter` was never
  DECLARED; (5) fleet/coverage/skew/unknown-agent counts were computed over the 200-row
  DISPLAY-capped window while claiming to describe the fleet (a header contradicting itself in
  one line). Spec **v4** now states the law generally: *a served count is computed over the
  WHOLE set its label claims to describe; display caps bound rows rendered, never the numbers
  beside them* — and records the hot-row invariant *a retry's jitter source must be unique per
  RACER, never derived from the contended row's identity*.
  Also: `coverage()` 2N+1 → **flat 2 queries** (417→8 end-to-end at N=205), oracle-equal.
  Findings: **#93 `_txn.py` root-cause misclassification RESOLVED by a concurrent session**
  (93a9aab). **OPEN → next wave: #94** (fleet's per-row ack loop: 407 queries @limit=200; the
  new grouped helper collapses it to 2) and **#95** (the unknown-agent line says "active
  agents:" but lists/counts the NON-RETIRED set). NEXT = PKT-28 **C2** (message graph +
  blocks: send/drain/ack + `_comms_footer`).
- 2026-07-12 · **PKT-28 C1 follow-up wave: #94 / #95 / #96 FIXED + DEPLOYED** (image
  **6e8f2c3091fd**; commits **8e3c27f** perf · **2cd78d5** label+process-law · **354da70**
  skew). Suite **4815 passed / 1 skipped / 3 xfailed** (+58, zero regressions) · mypy 0 ·
  ruff clean. Live smoke on the deployed surface: `non-retired agents: none` (bootstrap)
  and `…: aa, bb, cc`; first-ever publish renders `3 non-retired agents behind head v1 —
  3 unbriefed` (no fabricated v0); fleet ack queries FLAT at 3/3/3 (limit 5 / 50 / 200
  with 205 agents), oracle-equal to the old per-row path.
  **NEW PROCESS LAW — "Every artifact gets an adversary" (repo CLAUDE.md).** C1 shipped 5
  defects no builder gate caught; measured provenance: 3 were tests NEVER WRITTEN, 1 was a
  SPEC that prescribed the bug, 1 was a real gate a builder talked past as "flaky". Only the
  CODE had an adversary — the spec, the contract and the brief each had one author and zero
  graders. Now: a cold Opus **CONTRACT adversary** grades the TESTS before any builder starts;
  a failing test is a STOP ("flaky" is not a builder's verdict); spec ambiguity is an
  ESCALATION; every load-bearing pin is MUTATION-PROVEN.
  **It paid for itself on both runs.** Run 1: the #94 contract went green (561 passed, exit 0)
  with the defect fully intact — every pin tested a new method *nothing required the code to
  call* — plus 2 surviving mutants (a cross-session agent-name LEAK, and the bootstrap
  empty-roster branch). Run 2: it built a WRONG #96 fix that passed **489/489 + ruff + mypy +
  the AST pins** (remainder group counted VERSIONS not AGENTS → groups summing to 5 under a
  label saying 8 — the counting law broken inside the very line #96 exists to fix); root cause
  of the miss was the same small-N blind spot that produced 3 of C1's 5 defects.
  Spec now **v6**: §9.4 rewritten, §5.3 gains the version-naming corollary (*a render may only
  name a version that EXISTS — read, never arithmetic; litmus: a version a reader could not
  `brief_get` is a fabricated fact*), §9 gains a law-over-grammar PRECEDENCE rule.
  OPEN: **#97** (`limit` lacks ge=1) · **#98** (publish() never self-acks, so the AUTHOR is
  always counted behind on its own brief — and the zero-behind branch is unreachable through
  the tool; operator fork: self-ack `via="publish"`?) · **#99** (fleet header says "N agents"
  where N is non-retired — the last label inconsistency). NEXT = PKT-28 **C2**.
