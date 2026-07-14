# lore v2 — DeadReckoning+ · PACKET INDEX (plan of record, restructured 2026-07-10, re-sequenced 2026-07-14)

This replaces the monolithic resume-doc chain (`~/.claude/plans/lore-v2-*-RESUME.md`)
as the forward plan. The remaining work is decomposed into **work packets, numbered in
EXECUTION ORDER (01…41)** — files sort in the order they run. Each is sized to build
inside ONE session with a fresh context that loads only: repo CLAUDE.md (auto) · this
INDEX · its own packet file · the DESIGN-LAW sections the packet names · the spec files
the packet points at. Nothing else.

**Numbering law (operator-ruled 2026-07-14):** the old PKT-xx ids are RETIRED for
forward work and reserved for history — the Log, finding notes, memories, and commit
messages cite them, and the table's *was* column is the decoder. Every packet file's
header carries "(formerly PKT-xx)". Mid-sequence insertions (splits at kickoff, packets
minted by a design) take LETTER SUFFIXES (13a/13b, 26a/26b) — the top-level 01–41
sequence is never renumbered again. Completed work keeps its historical id
(`PKT-06-ledger-verbs.md`; comms C0/C1 are recorded in `comms-subsystem.md` + the Log).
THIS TABLE is authoritative over any stale wave letter in a packet file's header.

Sources folded in (extraction receipts in `receipts/`): MASTER-PLAN.md (§-references
below point into it) · the P7/P8a–P8e/SLATE/DETECTION resume docs · all 9 docs/design
specs · both docs/orchestration records · docs/eval records · LORE_EXTERNAL_REVIEW.md
(2026-07-10). The old resume docs remain as history; **their still-live content lives
HERE now** — a packet session must not need to read them.

## Declared targets (operator)
- **Goals ladder (ruled 2026-07-14):** (1) lore on DI locally → (2) lore on Odoo locally
  → (3) eventually lore in the cloud for Odoo. Comms stays top priority (Claude Code
  native comms broken by open bug #50779); results-impacting / LLM-impeding bugs get
  fixed on the way; client/server pushed to wave S (verified: nothing on the v1.0
  critical path needs it); WebUI last. **v1.0 = the single-node local ship.**
- **Replace the odoo-code MCP** (declared 2026-07-11): lore serves the Odoo corpus
  (~20k+ files / ~53k chunks) as its code-intelligence surface. The Odoo track
  (wave O): packet 23 worktree overlay ∥ 24 (scale certification) → 25 (onboarding
  design) → 26a+ (onboarding build); 27 (cross-tier compare) rides ∥. Live-DB
  introspection stays with odoo-dev by design.

## State of record (verified 2026-07-14, after packet 01)
- Branch `feat/surreal-unification` @ **5053bb0** (not pushed). Full suite at last
  lead-run: **5551 passed / 0 failed** (`-n auto`, the standing runner); skill suite
  **89 passed**; mypy 0 / 141 files; ruff clean.
- Deployed: **BOTH containers recreated on an image baking HEAD** — lore-lore (:9202)
  and DI (:9201). The deploy now GATES ITSELF: `verb_start` runs an artifact probe
  (required container binaries, derived from source) + a workspace-honesty probe
  (a watched root with a `.git` MUST serve a non-null branch), on all three start
  paths; a failure STOPS the deploy. Live receipt: `container binaries OK (git)` ·
  `workspace honesty OK (1 watched root(s) served)` on both. `lore_index()` serves
  `git_branch: feat/surreal-unification` + the real ref.
  15-tool surface; cosine substrate live; floor **0.50649** (STALE — measured over 214
  files, now 291; #87, packets 10/11); P7→P8d′, SLATE S1–S7, the closure wave,
  PKT-06/C0, PKT-28 C1, the #102 retry-substrate chain, and **packet 01** all CLOSED.
  Hashes are as-of-verification snapshots (image `6d599942cc69`); the authoritative
  deployment check is always RELATIVE (protocol, Boot 4).
- Standing eval bar: **35-pair set, pinned claude-sonnet-4-5-20250929, client metrics**
  (accuracy ≥33/35 · tokens-per-correct ≈1375-era · taxed-calls ≈0). 11-pair calls-leg
  retired. Last receipts: 33/35 · 6.46 calls · 1440.8 tok (2026-07-07).
- Test store: spike-surreal ws://127.0.0.1:18000; production store :18500 — NEVER
  pointed at by tests. Both systemd/quadlet-managed, auto-start on boot.

## Packet protocol (read once — this is the whole ritual)
**Boot:** (1) repo CLAUDE.md auto-loads (process law: gates, TDD, orchestration,
deploy, store idioms — packets never restate it). (2) Read this INDEX + your packet +
the DESIGN-LAW.md sections your packet lists **+ every FIRST READ your packet names —
`docs/reference/surrealdb-31-capabilities.md` is MANDATORY before touching the store,
schema, DDL, or store-reading code (#107 was a 100% outage whose answer was already in
it; when in doubt, read it)**. (3) Start lore if down (`lore-deploy`
skill), then `lore_index()` freshness, `lore_findings status=open`, `lore_tasks` —
mint/claim your ledger rows. (4) Run your packet's ENTRY CHECK; if ground truth
contradicts the packet, STOP and surface — never build on a stale premise.
**Entry checks assert RELATIVE facts** (deployed code CONTAINS commits X; suite green
at HEAD) — **never pinned snapshots** ("image hash Y still deployed"); snapshot hashes
live in receipts and the Log only (operator, 2026-07-14 — a pinned-hash entry check
false-STOPped packet 01 the first time it ran; any rebuild rots an absolute pin).
Operator kickoff: **load `docs/plans/v2/KICKOFF.md` at session start** — it is the
standing spawn prompt and encodes this ritual.

**Exit:** gates green (scoped pytest + `scripts/typecheck.sh` + ruff) → cold REFUTE
audit for wave commits → one-concern commits **at NATURAL BOUNDARIES throughout the
session, not only at exit (repo CLAUDE.md commit-boundary law: the working tree is
never the only copy of finished work)** → deploy if the packet says DEPLOY
(rebuild + recreate BOTH, never restart) → resolve/file findings with notes → flip
your row in the Status table below + append ≤5 lines to the Log at the bottom →
ledger rows done. **No new resume docs, ever.** State of record = git + this INDEX +
the lore ledger.

**Scope:** the packet's IN list is the grant; anything else found en route is
surfaced to the operator (repo law). Packet files are STATIC — scope changes are an
operator ruling recorded as an edit to the packet + a Log line.

**Sizing law (operator-ruled 2026-07-14):** target ≤0.25 wu per packet; any packet at
≥0.30 is SPLIT AT ITS KICKOFF into sub-packets with their own entry/exit (table rows
marked "→split"); every session plans ~⅓ context reserve for emergent findings (C1
receipts: every phase spawned follow-up waves). One packet per session — anything found
en route is surfaced/ledgered, never absorbed.

**Roster (operator-ruled 2026-07-14): the packet lead is OPUS by default — Fable context
is not spent on orchestration.** The judgment that once demanded a heavier lead is now
procedural law (contract-adversary, cold audits, satisfiability receipts, mutation
proofs) that any lead RUNS rather than IS. Fable appears in exactly two shapes:
(a) the **long-running design sidecar** on the packets whose header says
`lead: Opus + Fable design sidecar` (10, 17, 25, 33, 35, 39 — design authorship only;
the operator rules on its doc); (b) the **escalation valve**, on named triggers ONLY:
two consecutive failed fix-waves at the same gate · any surprise touching production
(:18500 or a deployed surface — the #107 class) · a spec-ambiguity escalation the packet
cannot resolve · a cold-audit NO-GO whose residuals imply cross-packet redesign.
Sidecar mechanics (general-purpose agent, never a fork; spawned ONCE and kept alive so
follow-ups answer from loaded context) live in repo CLAUDE.md → Orchestration.
**ROSTER AMENDED (operator, 2026-07-14, packet 01): the roster is OPUS END TO END —
Opus contract authors · OPUS BUILDERS · Opus contract-adversary · Opus cold audits ·
Opus lead. Sonnet is retired from the builder slot.** And the half that binds the LEAD:
**a DESIGN problem never reaches a builder.** If a contract's central requirement is a
property to INVENT rather than a spec to IMPLEMENT, it escalates to the operator as a
fork, or goes to an Opus author who must adversarially ATTACK ITS OWN DESIGN before
shipping — never to a builder with "work out the general form". Packet 01's receipts (an
Opus author's v1 scanner AND a Sonnet builder's v2 both defeated the same way; v3 held
only after the operator reframed the problem) are in repo CLAUDE.md → the roster clause.
Corollary: when one class of defect survives TWO waves, STOP briefing a third fix and
escalate the DESIGN.

## Sequence + status
**Operator-ruled order (2026-07-14, local-first), numbered as it runs:** 01 ledger
triage → 02–06 comms completion (wave C) → 07–17 local correctness (wave L:
results-impacting / LLM-impeding bugs) → 18–22 DI local = **v1.0 SHIP at 22**,
single-node (wave M) → 23–27 Odoo local (wave O) → 28–35 remaining features (wave F)
→ 36–39 cloud for Odoo (wave S — pull-forward on operator call) → 40–41 UI (wave G,
lowest). `∥` = parallel-safe with its wave. `→split` = splits at kickoff per the
sizing law. *was* = the retired PKT-id (decoder for Log/findings/memories).

| # | Packet (file) | was | Wave | Size | Depends on | Status |
|---|---------------|-----|------|------|-----------|--------|
| 01 | ledger-triage + lore_index watched-path/branch line | PKT-29 | pre | 0.15 | — | **DONE 2026-07-14** (image 6d599942cc69, both containers) |
| 01a | **artifact-conformance — run the suite IN the deployed image** (#139) | — | pre | 0.25 (measure-first) | 01 | open — **NEXT** |
| 02 | comms-render-architecture (#104 step-0, #103, #100, #101) | PKT-28 C2a | C | 0.20 | — | open (after 01a) |
| 03 | comms-message-graph (send/drain/ack, seq) | PKT-28 C2b | C | 0.25 | 02 | open |
| 04 | comms-blocks-footer (blocks edge, fleet cols, #105) | PKT-28 C2c | C | 0.20 | 03 | open |
| 05 | comms-await-story (await, story, CLI, idle-gate v2; #89 #121) | PKT-28 C3 | C | 0.30 →split | 04 | open |
| 06 | comms-protocol-drill (brief-base v3 + THE DRILL) | PKT-28 C4 | C | 0.25 | 05 | open |
| 07 | store-error-honesty (#118, #119, #128; #126/#127 adjudication) | PKT-30 | L ∥ | 0.20 | — | open |
| 08 | astroid-shadow (#24; containerfile roles → 37) | PKT-08 | L ∥ | 0.15 | — | open |
| 09 | surface-residues (#15, #64, #80, #82, #84–#86, #88, #92, docs truth) | PKT-03 | L ∥ | 0.20 | — | open |
| 10 | floor-calibration-design (#83, #87) | PKT-01 | L | 0.15 | — | open |
| 11 | floor-calibration-build | PKT-02 | L | 0.25 | 10 ruled | open |
| 12 | detection-contract (#10, #11, #27) | PKT-04 | L | 0.15 | — | open |
| 13 | detection-build | PKT-05 | L | →split | 12 ruled | open |
| 14 | config-derive-excludes (#26, #28, #72 corpus pollution) | PKT-09a | L ∥ | 0.20 | — | open |
| 15 | config-boot-validation (+ dead fields, #12) | PKT-09b | L ∥ | 0.20 | — | open |
| 16 | surreal-ops-hardening (#109, #110, #113, #114, #116, #117) | PKT-31 | L ∥ | 0.15 | — | open |
| 17 | worktree-overlay-design (#125; delta-only RULED) | PKT-33 | L | 0.15 | — | open |
| 18 | ledger-retirement (singular-store ruling) | PKT-24 | M | 0.20 | — (before 20 finalizes, 22 ships) | open |
| 19 | lore-deploy-rework (finding #13, scaffold; all-mode only) | PKT-11 | M | 0.30 →split | 14, 15 | open |
| 20 | migration-machinery (Shape D) | PKT-12 | M | 0.30 →split | §8 Q1–Q4 ruled at kickoff; 19; 18 | open |
| 21 | single-node-drills (§8.6 + watcher skip-path) | PKT-10a | M | 0.15 | — | open |
| 22 | di-migration + **v1.0 SHIP (single-node)** | PKT-13 | M | 0.25 | 19, 20, 18, GO/NO-GO | open |
| 23 | worktree-overlay-build (#125) | PKT-34 | O | 0.25 | 17 ruled; before 26 completes | open |
| 24 | odoo-scale-certification (MRO/ORM assessment defines 25) | PKT-27 | O ∥ | 0.30 →split | 13 rec.; v1.0 | open |
| 25 | odoo-onboarding-design (XML extractor, MRO capture, tiers, cutover) | PKT-32 | O | 0.15 | 24 receipts | open |
| 26 | odoo-onboarding-build (26a, 26b, … minted by 25) | PKT-35+ | O | ≤0.25 each | 25 ruled | open |
| 27 | cross-tier-compare (Odoo 15→19 prep) | PKT-18 | O ∥ | 0.25 | v1.0 | open |
| 28 | graph-search-v11 (#3, #70; + #20/#37/#40/#41 candidates) | PKT-17 | F | 0.35 →split | v1.0 | open |
| 29 | loresage package | PKT-14 | F | 0.25 | v1.0 | open |
| 30 | enrichment-worker | PKT-15 | F | 0.30 →split | 29 | open |
| 31 | detectors-escalation (raise_issue) | PKT-16 | F ∥ | 0.25 | v1.0 | open |
| 32 | memory-maintenance (decay/expiry sweeps) | PKT-19 | F ∥ | 0.15 | v1.0 | open |
| 33 | memory-reconciler (det. tier + loresage tier) | PKT-25 | F | 0.35 →split | v1.0; 29 for LLM tier | open |
| 34 | summary-reuse (5b, promoted) | PKT-26 | F | 0.25 | 29; 35 helpful | open |
| 35 | trace-deepening + trace_monitor backstop (gates S+G) | PKT-20 | F LAST | 0.30 →split | v1.0 | open |
| 36 | role-wiring (all\|mcp\|scout + creds; regains role verbs from 19) | PKT-07 | S | 0.30 →split | — | open |
| 37 | containerfile-roles + image slimming | PKT-08b | S | 0.20 | 36 | open |
| 38 | split-topology-e2e | PKT-10b | S | 0.20 | 36, 37 | open |
| 39 | hosted-security (design first; REQUIRED before off-LAN) | PKT-21 | S | 0.30 →split | 35 | open |
| 40 | ui-foundation | PKT-22 | G | 0.30 →split | 35, 39 | open |
| 41 | ui-graph-chat (+ Agent-SDK chat) | PKT-23 | G | 0.35 →split | 39, 40 | open |

Done history: **PKT-06 ledger-verbs (comms C0)** and **comms C1 (registry + briefs)**
— see the Log; `comms-subsystem.md` is the shared reference for packets 02–06.
External-review ordering constraint (2026-07-10, adopted): **UI ships after trace and
authorization models stabilize** — hence packet 35 closing wave F and wave S preceding G.

## Operator decision pool (each blocks nothing until its packet arrives)
1. **Packet 12 fork (was PKT-04):** prose-ish suspect flag — in-text vs metadata + serve-time injection.
2. **Packet 20 entry gate (was PKT-12):** migration §8 Q1–Q4 (docs/design/2026-07-04-migration-concurrency.md:317-333). Rec: Q1=(a)+(b), Q2=confirm ns/db-only, Q3=accept seconds-long freeze, Q4=dry-run Phase A first. **Ruled at wave-M kickoff — the ONE operator ruling on the v1.0 critical path.**
3. **Packet 22 (was PKT-13):** Shape-D GO/NO-GO after Phase A; deferred retire confirmation; post-soak shared-Qdrant orphan cleanup + `QDRANT__SERVICE__API_KEY` removal from lore.env.
4. ~~SQLite memory-ledger exception~~ **RULED (operator, 2026-07-11): SurrealDB is the
   SINGULAR durable store for lore data — the SQLite ledger retires in ALL modes**
   (external review gap 1 + the k8s/split contradiction found in discussion: MASTER-PLAN
   §1 says both "stateless → N replicas" and "ledger on MCP host"; SQLite cannot ride
   stateless replicas). Execution = **packet 18** (was PKT-24: writer/backfill removal,
   parity receipt, store-level backup posture, resilient-open honesty); packet 20's N1
   reshaped (replay semantics move into the N3 driver); packet 36's fork dissolved. DESIGN-LAW §14 carries
   the ruling. v0.3 ledger files stay frozen as the migration import source until
   post-soak.
5. ~~#49 instructions sizing~~ **RULED (operator, 2026-07-14): ACCEPT the overage.** The arbiter is the
   35-pair bar, not a token target. ⚠ Both circulating figures were STALE RUMORS: the INDEX said 575, #49's
   body said ~538 — **MEASURED 2026-07-14 it is 717 Claude tokens / 1743 chars** (both predated the 14→15
   tool surface). AND the bar that justifies ACCEPT has never been run against that surface (last receipt
   2026-07-07; lore_comms landed 2026-07-12) — operator-agreed re-run rides pool item 20 / ledger row
   73516abe.
6. **detail_level reshape** (§5 `detail: refs|signatures|source`) — ruled out of P8d; place in packet 28 or REJECT.
7. **T7** search default budget 1100→~1600 · **T8** `memories=` param (possibly mooted by T3) · **T9** re-expose what_imports/tests_for (NOT recommended; only if the bar re-misses) — docs/design/2026-07-06-p8dprime-fix-specs.md:480-491.
8. **D4 rename** served fused `score` → `fusion_rank` (ledgered at weak-match close). Fits packet 09 if approved.
9. **Air-gapped opt-out** for the hard Anthropic-key boot requirement (revisit-later TODO, P8a:110).
10. **Verify rebuild-caveat**: harder gate than caveat-during-rebuild? (P8c:154).
11. **Watcher skip-path posture** ack (store blip during live-drain skip kills the watcher worker — P8e-RESUME item 3).
12. **Spectron**: waitlist standing; backend re-decision on invite (spike list in MASTER-PLAN §6 P7).
13. **DI doc-content import** (DECISIONS.md/GOTCHAS.md → kind-tagged memories) — separate content migration, schedule ad hoc.
14. ~~#55 investigation row~~ **MINTED by packet 01** (row a6f38fc0, pairs #22 + #55): fresh-session
    ToolSearch can't resolve lore tools. NB it resolved FINE this session with a healthy container — the
    failure is INTERMITTENT, which is the hardest shape and why it has recurred twice unrooted.
15. **Upstream report** of the mcp-builder TextContent serialization bug (docs/eval/2026-07-04-p8a-baseline.md:123).
16. ~~Response/render caching~~ **RULED (operator, 2026-07-11):** flavor (a) render
    memoization DROPPED — no latency need at this time; do not build. Flavor (b)
    summary reuse PROMOTED → **packet 34** (was PKT-26; serving form ruled:
    `(ai summary)` marked, additive, citation-hash-gated).
17. **Packet 33 autonomy ruling** (was PKT-25; contract-time): flag-only vs propose vs
    auto-apply-with-audit, per reconciler action class.
18. **Retrieval-liveness as a dead-code corroborator** (gap-3 discussion,
    2026-07-11): once packet 35 links traces→chunks, "never served in N months AND zero
    prod refs" is a strictly stronger dead signal. Cheap byproduct; strike or keep —
    if kept, rides packet 35's exit as an extra dead_code caveat line, still HEURISTIC-
    bannered.
19. ~~Odoo onboarding packet — sequencing + scope~~ **SCHEDULED 2026-07-14: this is now
    packet 25 (design pass, after packet 24's receipts) + 26a+ (build packets minted by
    the design), wave O.** Scope carried into packet 25's file: XML reference extractor,
    MRO + ORM metadata capture per packet 24's assessment, manifest/csv chunker
    extensions, tier layout, cutover from odoo-code per the struck parity matrix.
20. **#73 eval-fixture maintenance** (corpus-dependent ground truths go stale as the
    tree grows) — decision point: next standing-bar eval run.
21. **#111 typed conflict check** — switch `_txn`'s substring match to
    `is_transaction_conflict` when surrealdb-py 3.0.0 ships. Watch the release.

## Watch list (no packet; verify-on-contact)
- ~~Wave-A boot duty~~ **SUPERSEDED 2026-07-14: packet 01 owns the full triage** — its
  packet file carries the operator-approved finding→destination routing table (every
  open + acknowledged row, individually; no silent drops), the stale-row resolves
  (#97/#98/#99/#107 fixed-but-open, #34/#90 superseded-by-#92, #112, #106→#124 dedupe),
  and the dead task-row closes.
- #124 (engine first-write race) stays acknowledged-watch; packet 16's #109 conflict
  metric is its observability support.
- Open research note (no evidence either way in literature/vendor practice): whether
  displaying scores to tool-using LLM consumers helps — our three-model consult remains
  the only direct data (weak-match external validation, element d).
- Graph composition invariant + hot-row minting retry pattern + two-step recreate —
  now in DESIGN-LAW.md; cite it, don't rediscover.
- `scratchpad/` at repo root is finding #72 corpus pollution — fixed by packet 14;
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
- 2026-07-13 · **PKT-28 C1 CLOSE-OUT: #97/#98/#99 + a SEVEN-instance render-honesty sweep +
  a 100% PRODUCTION OUTAGE (#107) and its fix.** Deployed image **b0fce6904fc5** (both
  containers); commits **f36120b** (comms) + **060dbda** (store). Live-verified on the real
  wire: publish self-acks its author (#98) · `limit` teaches/clamps and mutates nothing on
  rejection (#97) · `fleet: N non-retired agents`, and an all-retired scope no longer claims
  "no agents registered" (#99) · a non-`project` first-publish teaches `brief_ack` instead of
  a register-ack that never runs (8th) · the catch-up teach names its brief, so following it
  reads the RIGHT one (10th).
  **THE OUTAGE (#107) — the lesson of the phase.** #98 widened `briefed.via`'s ASSERT. It
  shipped with **1040 comms tests green, a cold code audit GO, and the contract-adversary
  passing — and broke `brief_publish` 100% in production**: `DEFINE FIELD IF NOT EXISTS` is a
  NO-OP on an existing field, so the change never migrated. **No gate could see it: every test
  mints a virgin throwaway DB, so no test in this repo had EVER applied a schema change to an
  EXISTING store.** A fixture that guarantees a clean slate cannot test what only happens on a
  dirty one — and every long-lived deployment is a dirty one. **The deploy smoke was the only
  instrument that caught it.** Fixed: `_define_field` → `DEFINE FIELD OVERWRITE` (the store
  now CONVERGES to the code on every `ensure_ready()`; it self-migrated production on boot).
  Indexes/analyzers/tables stay `IF NOT EXISTS` — MEASURED: `DEFINE INDEX OVERWRITE` re-validates
  a populated HNSW index and RAISES (boot crash); an analyzer OVERWRITE never re-tokenises a
  built FULLTEXT index (silent recall bug). The naive "OVERWRITE everything" fix would have
  taken the server down a different way.
  **The gotcha was ALREADY IN `docs/reference/surrealdb-31-capabilities.md` and nobody read it**
  — and SurrealDB's own docs contain a FALSE claim (`IF NOT EXISTS` on an existing object "will
  return an error"; it silently no-ops) that would lead a careful reader to think this bug is
  impossible. Law added (CLAUDE.md): read the dependency's docs FIRST, then VERIFY them — the
  docs named the mechanism, only the probe caught them lying. `ALTER` was rejected with
  receipts (it cannot CREATE a field; `ALTER … IF EXISTS` silently no-ops → it would have
  reintroduced #107 on the fresh-DB path).
  **PROCESS SHIPPED THIS PHASE:** the reusable **`contract-adversary`** agent (grades the TESTS
  before any builder starts — 4 runs, 4 blockers, incl. against an Opus contract) · contract
  authors → **Opus** (operator) · **pytest-xdist** (846s→88s; it also EXPOSED #101 and #102) ·
  "a diagnosis is not an instrument" · "a probe needs a control" · "read the residual table,
  not just the summary block".
  **OPEN → C2, in order: #104** (render architecture — name the ROLE, type the applicability,
  kill the fixture monoculture; C2's STEP 0, before any new renders) · **#102** (hot-row mint
  drains under N-way contention — a worktree kickoff prompt exists; blocks `message.seq`) ·
  then #103 (heartbeat generalization, spec v8 ruled) · #105 (dangling-edge landmine) · #100
  (`created_by` identity split) · #101 (log-capture isolation). NEXT = PKT-28 **C2**.
- 2026-07-14 · **#102 CHAIN CLOSED** (#33→#102→#122, + #108 #120): ONE retry seam
  (`retry_on_conflict`/`bootstrap_session`/`run_query`, eleven hand-rolled copies deleted)
  merged @ 634da1c (9d29111 code · b649f28 law · f72beeb reference); suite **5385/0** `-n auto`,
  399-pin contract, 20/20 concurrency. Trail: adversary→satisfiability gate born, 2 cold audits,
  2 blind reads. C2 `message.seq` = native sequence (task f86af162). NEXT = **C2** (step 0 #104).
- 2026-07-14 · **OPERATOR LOCAL-FIRST RE-SEQUENCE** (goals: DI local → Odoo local → cloud-for-
  Odoo eventually): waves now C(comms)→L(correctness)→M(DI=v1.0 SINGLE-NODE)→O(Odoo local)→
  F(features)→S(cloud)→G(UI); sizing law ≤0.25/split-at-0.30; C2 split C2a/C2b/C2c; new PKT-29
  (triage) 30 (store error-honesty) 31 (surreal ops) 32/35+ (Odoo onboarding) 33/34 (#125
  worktree overlay, RULED first-class DELTA-ONLY) 08b/10b (split-off halves). Row df2b5345.
- 2026-07-14 · **PACKETS RENUMBERED IN EXECUTION ORDER (operator):** files now `01-…41-…`,
  one per session; PKT-ids RETIRED to history (the table's *was* column is the decoder; every
  file header carries "formerly PKT-xx"). Comms phases C2a–C4 became step files 02–06 over the
  shared `comms-subsystem.md`; PKT-09 split into 14/15; insertions take letter suffixes
  (13a, 26a) — the top-level sequence never renumbers again. Log/receipts keep old ids.
- 2026-07-14 · **ROSTER RULING (operator): OPUS leads every packet by default** — Fable =
  long-running design sidecar on 10/17/25/33/35/39 + escalation valve on named triggers only
  (protocol §Roster). Sidecar pattern codified in repo CLAUDE.md → Orchestration: general-
  purpose (never fork), spawned once, standing by for SendMessage follow-ups from loaded
  context. comms-subsystem ruling 7 + the 2026-07-12 CLAUDE.md roster line amended in place.
- 2026-07-14 · **ENTRY CHECKS ARE RELATIVE (operator):** packet 01's first live run
  false-STOPped on a pinned image hash (b0fce6904fc5 superseded by a HEAD-baking rebuild,
  byte-verified). Law added to protocol Boot 4: entry checks assert relative facts (deployed
  ⊇ cited commits), never pinned snapshots; packet 01 + state-of-record amended. Packet 01
  proceeding (Opus session, first KICKOFF.md boot — STOP-and-surface worked as designed).
- 2026-07-14 · **PACKET 01 DONE + DEPLOYED** (image `6d599942cc69`, BOTH containers; 13 commits
  `3415041`→`5053bb0`; suite **5551/0**, skill **89**, mypy 0, ruff clean). Ledger triage: open
  findings **60+ → 0** (18 resolved w/ receipts, 46 acknowledged with an INDIVIDUAL destination
  note, 7 dead task rows closed, #22+#55 investigation row minted). **#125 honesty line LIVE:**
  `lore_index()` serves each watched root + its real git branch/ref, the served INSTRUCTIONS tell
  agents to look, and the DEPLOY now gates the ARTIFACT (binaries + non-null branch) on all three
  start paths — it would have REFUSED the old image.
  **#131 — git was NEVER IN THE IMAGE.** `capture_git_identity` shells out; the binary was absent,
  the OSError was swallowed into a silent `(None, None)`, so EVERY production snapshot's git_ref
  has been empty for months, invisible because no render shows it. The honesty line would have
  shipped as `branch: null` in the only environment it exists for — #107's shape exactly (the
  fixture guarantees the one condition under which the bug is invisible: tests run where git EXISTS).
  **THE EXEC-SEAM CHAIN — three scanners, and the lesson is the lead's, not a model's.** The image
  gate must derive which binaries the shipped code execs. v1 keyed on receiver NAMES → beaten by 4
  shapes (**an OPUS contract author wrote it**). v2 went binding-aware → closed those, opened 4 more,
  **3 REGRESSIONS** incl. one that LOST a binary v1 found (**a SONNET builder designed it — because
  the LEAD briefed a DESIGN problem as a build task**). v3 held: **receiver-blind deny + ALLOWLIST
  THE SAFE** (one sanctioned exec seam), designed by an Opus author who BUILT and ATTACKED its own
  design (2 of its own 23 invented shapes broke its first attempt). **The variable was never the
  model — it was the frame.** → OPERATOR RULING: roster is **OPUS END TO END**, and **a DESIGN
  problem never reaches a builder** (CLAUDE.md + protocol §Roster). Corollary: when a defect class
  survives TWO waves, STOP briefing a third fix and escalate the DESIGN.
  **NEW LAW SHIPPED — WHEN YOU CANNOT CLOSE A HOLE, PIN IT.** #137 (a third-party dep that spawns is
  invisible to any AST scan of our source) and #138 (4 obfuscation doors, kept open because closing
  them taxes honest code) are pinned by tests that ASSERT THE MISS and go RED if anyone closes them.
  A bound that is pinned is met deliberately; an unpinned limitation is indistinguishable from an
  unknown one. Both carry the THREAT MODEL nobody had written down: this gate is for the HONEST
  developer, NOT a boundary against a hostile author — *"a gate that refuses honest code is a gate
  that gets switched off, and then #131 happens again with nothing watching at all."*
  New: **#129** (an acknowledged finding is ANNOTATION-FROZEN — ack→ack illegal, only resolve/wontfix
  carry notes; it blocked this very triage) · **#130** (lore_tasks `status=open` serves SUPERSEDED rows
  the claim CAS refuses) · **#132** (git present but REFUSING — uid mismatch → exit 128 → the same
  silent null; installing git is necessary, NOT sufficient) · **#133** (a satisfiability receipt that
  skips the PRE-EXISTING suites the change's seam touches is not a receipt — it trapped a builder) ·
  **#134** (worktree mounts cannot deploy: `.git` is a FILE naming a host gitdir outside `/workspace`
  → packets 17/23) · **#135** (subdir-of-a-repo: host and container disagree, silently) · **#136**
  (⚠ **the #102 runtime SDK-escape guard is BLIND out-of-tree** — its 3 POSITIVE CONTROLS fail in any
  copy while its "no escapes" verdicts stay GREEN. Packets 17/23 make worktrees first-class; that is
  exactly the shape that breaks it. Route to the #102/#120 owner BEFORE 17). Pool 5 RULED (#49 ACCEPT;
  the block is **717 tok MEASURED**, not the 575/538 rumors — and the eval bar justifying it predates
  the 15-tool surface: re-run ledgered, row 73516abe). NEXT = **packet 02** (#104 render architecture).
- 2026-07-14 · **PACKET 01a MINTED (operator): run the test suite IN the deployed image (#139).**
  THE TEST ENVIRONMENT IS A FICTION — the suite runs on a dev host, production is a container, and
  EVERY difference is an unguarded gap. **Both of our worst outages lived in exactly that gap:** #131
  (the image had no git; tests run where git EXISTS) and #107 (a schema ASSERT never migrated; every
  test mints a VIRGIN db). Same root twice — *the fixture guarantees the one condition under which the
  bug is invisible.* Packet 01's probes catch the #131 INSTANCE; this catches the CLASS.
  DESIGN (operator's, settled): an EPHEMERAL container from the DEPLOYED image (`podman run --rm`),
  worktree bind-mounted, test deps at run time — the odoo-dev pattern. Image untouched (packet 37 safe).
  ⚠ THE TRAP: bind-mount the repo and `import loremaster` resolves to the MOUNTED SOURCE, not the baked
  copy — you would test the working tree again, inside a container, and learn nothing (#24 in reverse).
  The run MUST ASSERT `loremaster.__file__` is in site-packages and FAIL LOUD otherwise: mount the
  TESTS, import the ARTIFACT. ⚠ AND: do NOT curate "environment-sensitive tests" — that is the name-list
  that lost three times in packet 01. Run the WHOLE suite; host-vs-container DIVERGENCE is the signal.
  MEASURE-FIRST: the divergence count is unknowable until run; it scopes its own triage (split to 01b
  if it exceeds budget). Prediction recorded: **it will find real defects — if it finds none, suspect
  the harness.** Runs BEFORE packet 02.
