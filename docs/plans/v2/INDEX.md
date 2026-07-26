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

## State of record (verified 2026-07-23, after packet 03a-2 — DONE, 03a CLOSED)
- Branch `feat/surreal-unification` @ **0223291** (not pushed).
- ⚠ **THE SUITE HAS A COMMITTED RED CONTRACT — read this before you run pytest.** The RED
  contract for packets 03/03a/03b is COMMITTED (`efef2b3`, 400 pins; **+ the one-line #173
  C-DEF fix** `_seed_agents` CREATE→UPSERT at `42eeedc`; **+ the operator-authorized 03a-2
  amendments** at `50d65a0`/`f04729c` — see the Log). **Packet 03 (STORE) GREEN** (`df59f76`;
  `test_comms_schema` + `test_surreal_schema`, scoped 304/0). **Packets 03a-1 (send + drain +
  `AgentRefLike` home) and 03a-2 (ack + derived waiting state) GREEN + DONE**, so
  `test_message_ledger.py` is now **180 passed / 0 failed / 12 skipped** (all 12 skips are
  `[fake]`-leg; **zero `[real]`-leg skips**). Still EXPECTED RED: the dispatch/render pins in
  `test_comms_tool.py` (**149 failed / 554 passed**, measured `f04729c`) and
  `test_comms_promise_registry.py` — both are 03b's contract. **A 03b session does NOT start
  from 0 failures.**
- typecheck: **36 mypy errors** — all in the RED 03b contract test files (`test_comms_tool.py` 31,
  `test_comms_promise_registry.py` 3: forward refs to `_render_comms_*` / new `comms(...)` kwargs)
  + 2 pre-existing frozen-contract `no-any-return` (`test_message_ledger.py:1716/1736`, untouched);
  **ZERO in any production file** (03a-1's `messages.py`/`agent_ref.py`/`briefs.py` are clean).
  Global mypy-zero returns when 03b builds its surface — the TEST-ONLY split's structural property,
  not a regression (operator deferral 2026-07-23). Skill suite **117 passed** (unaffected); ruff clean.
- **Packet 02a shipped NO deploy and is not owed one — it is TEST-ONLY.** Production was
  byte-identical throughout (`server.py` md5 `1caac4bd…` unchanged across every probe by
  three independent parties), so the deployed image below still matches HEAD's production
  code exactly. Do not read the unchanged image hash as a stale deployment.
- Deployed: **BOTH containers recreated on an image baking HEAD** — lore-lore (:9202)
  and DI (:9201). The deploy now GATES ITSELF: `verb_start` runs an artifact probe
  (required container binaries, derived from source) + a workspace-honesty probe
  (a watched root with a `.git` MUST serve a non-null branch), on all three start
  paths; a failure STOPS the deploy. Live receipt: `container binaries OK (git)` ·
  `workspace honesty OK (1 watched root(s) served)` on both. `lore_index()` serves
  `git_branch: feat/surreal-unification` + the real ref.
  15-tool surface; cosine substrate live; floor **0.50649** (STALE — measured over 214
  files, now 291; #87, packets 10/11); P7→P8d′, SLATE S1–S7, the closure wave,
  PKT-06/C0, PKT-28 C1, the #102 retry-substrate chain, **packet 01**, **01a**,
  **packet 02** (comms render architecture) and **packet 02a** (promise-instrument
  hardening) all CLOSED.
  Hashes are as-of-verification snapshots (image `ae0e78d9a504`); the authoritative
  deployment check is always RELATIVE (protocol, Boot 4).
- Standing eval bar: **35-pair set, pinned claude-sonnet-4-5-20250929, client metrics**
  (accuracy ≥33/35 · tokens-per-correct ≈1375-era · taxed-calls ≈0). 11-pair calls-leg
  retired. Last receipts: 33/35 · 6.46 calls · 1440.8 tok (2026-07-07).
- Test store: spike-surreal ws://127.0.0.1:18000; production store :18500 — NEVER
  pointed at by tests. Both systemd/quadlet-managed, auto-start on boot.
- **ENGINE: SurrealDB 3.2.1 on BOTH stores (migrated from 3.1.5 on 2026-07-22)** —
  receipts in the store reference §0 (ff7128e): prod byte-identical (174,161 rows /
  20 tables), full suite behaviour-identical across engines, #107 re-probed, SDK 2.0.0
  unchanged. 3.1.5-probed facts KEEP their provenance labels — re-probe on contact.
  Sole rollback: the verified 3.1.5 backup at /backups/lore/surreal-pre-3.2.1-20260721
  (RocksDB format is forward-only). New static vendor tiers indexed (`surrealdb-docs`,
  `surrealql-tests` @ v3.2.0 tag) — corpus now 2764 files by design.
  Substrate: **#167 RESOLVED 2026-07-22** by a verified fingerprint reconcile (all
  17,287 chunks proven non-null + cosine 1.000000 vs fresh re-embeds on all three
  tiers; measured safe-stamp with rollback recorded; restart clean, no re-trigger).
  The durable fixes are the **#171 ruled design → packets 11a/11b** (⊃ #168/#169,
  adopts #170; certified at scale in 24). Cosine floor legitimately stale
  post-reconcile (#161 → packets 10/11); traces still serve total=0 (#147 → 03b).

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
**A SCOPE BOUNDARY THAT RESTS ON "X IS ALREADY COVERED" IS A PREMISE, NOT A FACT — IT
BECOMES AN ENTRY CHECK WITH A PROBE (operator-ruled 2026-07-19, packet 02a).** Whenever a
packet's IN/OUT list excludes something because another instrument, packet, or layer is
believed to handle it ("outside a `render_line` template", "the CORE scanner owns that",
"mypy catches it"), that belief is TESTED at kickoff — one probe, one receipt — before the
exclusion is honoured. Receipt: 02a's scope said *"outside a `render_line` template"* on the
assumption those were covered; they were not (an f-string template was invisible to every
scanner, and `mypy` does NOT enforce `LiteralString`/PEP 675 here). A REAL in-scope hole was
thereby formally ruled OUT of scope, and surfaced only at cold audit — a full NO-GO cycle
later. An untested coverage premise is how a defect acquires an alibi.
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
| 01a | **artifact-conformance — run the suite IN the deployed image** (#139) | — | pre | 0.25 (measure-first) | 01 | **DONE + DEPLOYED 2026-07-16** (c90df55/b528ac1/a35cdca/062bf60; image **f25c18976b2b**, both containers; in-image suite 5545/0; no 01b split; **#141 drift closed in the running artifact**) |
| 02 | comms-render-architecture (#104 step-0, #103, #100, #101) | PKT-28 C2a | C | 0.40 | — | **DONE + DEPLOYED 2026-07-19** (image **ae0e78d9a504**, both containers; d3c899f→05a8bb2; cold-audit GO + F1 fixed; live-wire smoke PASS; promise HARDENING split → 02a) |
| 02a | comms-promise-instrument-hardening (full §9.7 per-entry executable-predicate proofs + `safe_str` literal-coverage closure `_SAFE_STR_LITERAL_RESIDUAL`) | — | C | 0.20 (ran ~4×) | 02 | **DONE 2026-07-19** (a2e9a70→ceac2d0, 6 commits; TEST-ONLY, **no deploy** — production byte-identical, `server.py` md5 unchanged throughout; scoped gates 34→117) |
| 03 | **comms STORE** — message/`to` slices, `DEFINE SEQUENCE`, `ENFORCED`, the relation-table policy flip + dirty-store migration pins; **#146 adjudication + 3.2.1 re-probes** | PKT-28 C2b | C | 0.20 | 02 | **DONE 2026-07-23** (df59f76; scoped 304/0, blast 432/0; cold-audit GO; #146 accept-with-trigger; TEST-ONLY, no deploy; 03a unblocked) |
| 03a-1 | **comms ledger SEND + drain** — `messages.py` foundations + `AgentRefLike` home + `send` + drain/peek; ≥8-way send concurrency | — | C | 0.20 | 03 | **DONE 2026-07-23** (2d1f75d→42eeedc; cold-audit GO, [real] leg graded; 140 passed / 31 red=03a-2 stubs; #173 fix; TEST-ONLY, no deploy) |
| 03a-2 | **comms ledger ACK + WAITING** — ack (4-way disambiguation), derived waiting state; 16-way ack concurrency (**closes 03a**; drain landed in 03a-1) | — | C | 0.15 | 03a-1 | **DONE 2026-07-23** (`853a95b`→`0223291`; cold-audit GO, [real] leg graded 31 pins / 0 silent skips; 180 passed / 12 skipped; 20/20 16-way ack concurrency; **closes 03a**; TEST-ONLY, no deploy) |
| 03b | **comms SURFACE** — `lore_comms` dispatch + renders/promises + drain telemetry; **#145/#147 kickoff probes, #143 adjudication; DEPLOYS BOTH** | — | C | 0.30 →split | 03a ✅ | **✅ DONE + DEPLOYED 2026-07-26** (task `b7f89c12`). Suite **6937/0**, typecheck 0 all members (**global mypy-zero DISCHARGED**, 36→0), ruff, skill 117, concurrency 20/20. Both containers on `b46bc1d5`; every deploy receipt green on production. **#147 CLOSED with a production receipt** (traces 0→664, ordinals distinct+increasing). Client battery PASS 3/3 floor + all 3 population models. Inherited 6 design-ruled items all discharged. Residuals routed with named decision points: 05 (#190/#183/#214, DD-2.a, DD-4.c) · 06 (#193 retention, join-quality receipt) · 05-or-06 (#195 injection). |
| 04 | comms-blocks-footer (blocks edge, fleet cols, #105) | PKT-28 C2c | C | 0.20 | 03 | open |
| 05 | comms-await-story (await, story, CLI, idle-gate v2; #89 #121 #149) | PKT-28 C3 | C | 0.30 →split | 04 | open |
| 06 | comms-protocol-drill (brief-base v3 + THE DRILL) | PKT-28 C4 | C | 0.25 | 05 | open |
| 07 | store-error-honesty: CLASSIFICATION (#118, #119, #144 — the #124 rediagnosis) | PKT-30 | L ∥ | 0.20 | — | open |
| 07a | store-error-honesty: RECOVERY + DEGRADATION (#164 reconnect-on-bounce, #128; #126/#127 adjudication) | — | L ∥ | 0.20 | 07 rec. (same seam) | open |
| 08 | astroid-shadow (#24; containerfile roles → 37) | PKT-08 | L ∥ | 0.15 | — | open |
| 09 | surface-residues (#15, #64, #80, #82, #84–#86, #88, #92, docs truth) | PKT-03 | L ∥ | 0.20 | — | open |
| 10 | floor-calibration-design (#83, #87, #161, #179) | PKT-01 | L | 0.15 | — | **design DONE 2026-07-24; F3 → client consult** |
| 10-d | **weak-match DISARM** (#176/#179/#180 — confidence surfaces dark NOW; trust doctrine, Addendum E1) | — | L | 0.05 | — (independent) | **✅ DONE + DEPLOYED 2026-07-26** (built/audited/merged `be4c591` 2026-07-24; deploy RODE 03b's — both containers on `b46bc1d5`). Live receipt from the running artifact: `lore_index()` serves `cosine_floor.state="disabled"` with the note naming #83/#176/#179/#180. ⚠ **The disarm MASKS #176/#179/#180, it does not FIX them** (`d7a1ce5`) — the per-instance calibration that resolves them is 11-i/11-ii; those findings stay OPEN. |
| 11-i | floor-calibration: DARK MACHINERY (engine + store + in-container runner + R2 lab validation; serving untouched, no deploy) | PKT-02 | L | 0.20 → split 11-i-a ~0.15 / 11-i-b ~0.24 | 10 ruled | **DESIGN RULED 2026-07-26** (23 decisions: RULINGS-2026-07-25.md; Addendum F-r2 §R1–R10; S1 measured NOT DEGENERATE). **11-i-a CONTRACT PHASE IN FLIGHT — branch `pkt11-i-a-floor-machinery`, worktree, UNMERGED, nothing deployed.** Contract `d6c0dd4` → adversary **INSUFFICIENT** (9 of 14 wrong builds survived at 143/0) → fix wave `e8aa8f4`: **186 collected**, satisfiability **186 / 925 / 561, all 0-failed** against a reference build, lead-verified. Deps adopted `38c9774`; **#198** consolidated `ea7406e`; **#238 closed** (`docs/eval` now gated, 190 tests). Rulings: `receipts/2026-07-26-packet11i-build/RULINGS-2026-07-26-{bootstrap,contract-11ia,adversary}.md`. **BUILDER NOT STARTED.** Open: the corpse-sweep marker-vs-teaching discriminator, and Q3 (is a `head_identity`-less measurement row acceptable at the store layer). **11-i-b not started** |
| 11-ii | floor-calibration: CUTOVER (chokepoint wiring + serving swap + retirement sweep; resolves #83/#87/#161/#179) | PKT-02 | L | 0.15 | 11-i landed | open |
| 42 | **PREVENT THE LEAK, DELETE THE SANITIZER** — `SecretStr` everywhere + allowlist the 13 `.get_secret_value()` unwraps, then DELETE the entropy catch-all. Kills audit R2 (12.4% of function names erased from tracebacks), #227 and both its accepted bounds. | — | L | 0.20 | — (independent) | **open — SHIPS NEXT (operator, 2026-07-26)** |
| 11a | embedding-reconciliation CONTRACT (#171 FULLY-RULED design ⊃ #168/#169, adopts #170) | — | L | 0.20 | — (design ruled) | open |
| 11b | embedding-reconciliation BUILD (reconciler + resolve extraction + #170 hash; `rebuild_all` retires, hard-cutover rename) | — | L | 0.25 →split if 11a measures over | 11a ruled | open |
| 12 | detection-contract (#10, #11, #27; rides 11b's extracted resolve seam) | PKT-04 | L | 0.15 | 11b rec. | open |
| 13 | detection-build | PKT-05 | L | →split | 12 ruled | open |
| 14 | config-derive-excludes (#26, #28, #72 corpus pollution + #162 archive-twin dedup) | PKT-09a | L ∥ | 0.20 | — | open |
| 15 | config-boot-validation (+ dead fields, #12) | PKT-09b | L ∥ | 0.20 | — | open |
| 16 | surreal-ops-hardening (#109, #110, #113, #114, #116, #117) | PKT-31 | L ∥ | 0.15 | — | open |
| 17 | worktree-overlay-design (#125; delta-only RULED) | PKT-33 | L | 0.15 | — (#136 FIXED 2026-07-14) | open |
| 18 | ledger-retirement (singular-store ruling) | PKT-24 | M | 0.20 | — (before 20 finalizes, 22 ships) | open |
| 19 | **deploy-architecture DESIGN** (#166 one-toolchain ⊃ #165; partitions the old rework — #13, scaffold, verbs — into minted 19b+ builds ≤0.25 each) | PKT-11 | M | 0.15 | — (builds inherit 14/15) | open — REDESIGNATED 2026-07-22 |
| 20 | migration-machinery (Shape D) | PKT-12 | M | 0.30 →split | §8 Q1–Q4 ruled at kickoff; 19; 18 | open |
| 21 | single-node-drills (§8.6 + watcher skip-path) | PKT-10a | M | 0.15 | — | open |
| 22 | di-migration + **v1.0 SHIP (single-node)** | PKT-13 | M | 0.25 | 19, 20, 18, GO/NO-GO | open |
| 23 | worktree-overlay-build (#125) | PKT-34 | O | 0.25 | 17 ruled; before 26 completes | open |
| 24 | odoo-scale-certification (MRO/ORM assessment defines 25) | PKT-27 | O ∥ | 0.30 →split | 13 rec.; v1.0 | open |
| 25 | odoo-onboarding-design (XML extractor, MRO capture, tiers, cutover) | PKT-32 | O | 0.15 | 24 receipts | open |
| 26 | odoo-onboarding-build (26a, 26b, … minted by 25) | PKT-35+ | O | ≤0.25 each | 25 ruled | open |
| 27 | cross-tier-compare (Odoo 15→19 prep) | PKT-18 | O ∥ | 0.25 | v1.0 | open |
| 28 | graph-search-v11 (#3, #70, #155; + #20/#37/#40/#41 candidates) | PKT-17 | F | 0.35 →split | v1.0 | open |
| 28a | report/thread serving (#163 ⊃ #160 — section-aware chronological threads + report graph) | — | F ∥ | 0.25 | 14 (#162 first); v1.0 | open |
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
12. **Spectron**: the DOCS are now PUBLIC + indexed as lore tier `spectron-docs` (2026-07-23, 143 .mdx) — the design half of the re-decision is UNBLOCKED: run the spike list (MASTER-PLAN §6 P7) against the REAL docs, not the 2026-07-02 Fable study. The `ghcr.io/surrealdb/spectron` BINARY may still be gated (the "on invite" trigger applies only to RUNNING it). Superseded verdict: `lore_recall("spectron status update")`.
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
    `is_transaction_conflict` when surrealdb-py 3.0.0 ships (alphas a1–a4 exist as of
    2026-07-16, NOT adopted — reference §0). Watch the release.
22. **#154 + #157 — legacy citation debt** (dead SPEC paths + 51 dangling report names +
    116 line-number cites in the test tree). Recurrence is CLOSED by the archive law;
    the legacy tail is inert. Decision point: wave-L kickoff — one hygiene mini-packet,
    or accept-with-trigger.
23. **#156 — exemption evidence is unexecutable (DESIGN item):** every allowlist can
    carry a false justification forever ("no assertion can read English"); both
    adversaries blessed a false one by inspection. The fix is a property to INVENT
    (executable exemption evidence) — per roster law it needs an Opus design pass that
    attacks its own design, not a builder. Operator schedules.
24. ~~**Message id form (03a-1 residual):** `uuid4().hex` vs `ulid()`~~ — **RULED (operator,
    2026-07-23): use `ULID`.** Time-sortable for a future pkt-05 `since=` cursor; pre-deployment, so
    no records to migrate. Implemented `13da377`: `message.id = str(ULID())` (python-ulid 4.0.1,
    client-side mint, dep on `loremaster/pyproject.toml`), aligning with the contract's stated
    `bare ulid` intent. Verified: bareness pin green both legs, full file 140/31/9 unchanged, ruff
    clean, mypy +0.

## Watch list (no packet; verify-on-contact)
- **NO WORKTREES UNTIL WORKTREES WORK (operator, 2026-07-14).** Do not use git worktrees for lore
  work — agents, audits, mutation probes — until they actually work. Still broken: **#134** (lore
  cannot be DEPLOYED against a worktree: `.git` is a FILE naming a host gitdir outside the mount)
  and **#125** (lore cannot INDEX an uncommitted worktree; packets 17/23 build the overlay).
  ✅ **#136 is FIXED** (bbe367f) — the retry guard no longer goes blind out-of-tree; packets 17/23
  are UNBLOCKED. Full law: repo CLAUDE.md.
- **#140 — A `cp -a` COPY NEVER RUNS ITS OWN PRODUCTION CODE.** It imports `loremaster` from the
  ORIGINAL checkout (the copied `.venv` carries an editable `.pth` with an absolute path home), and
  `cp -a` preserves mtimes so the stale `__pycache__` carries the ORIGINAL `co_filename` too. **A
  mutation proof or reference build made in a naive copy is grading the tree it was supposed to be
  isolated from — and nothing tells you.** Packet 01's exposure was NIL (all 13 agent reports
  audited: every mutation proof either PYTHONPATH-shadowed with `loremaster.__file__` VERIFIED, or
  mutated the real tree with a content backup) — **that was the habit working, not the tooling.**
  THE LAW: **prove which tree you are testing, or you are not testing anything** (repo CLAUDE.md).
- #124 (engine first-write race) — **rediagnosis pending: #144 says the "lost rows" were
  retryable conflicts hidden by statement[0]-only validation, not an engine defect.**
  Packet 07 settles it; until then #124 stays acknowledged-watch; packet 16's #109
  conflict metric is its observability support.
- **#159** (24 non-passing tests once, unreproduced ×5; evidence destroyed by tail-only
  echo) — watch. Trigger: on ANY anomalous run, preserve the FULL output before
  re-running; a green claim needs the passed-count tail, an anomaly needs the whole body.
- ⚠ **lore-lore runs on a HAND-ROLLED /source mount — NOT restart-durable until the
  packet-19 deploy architecture (#165/#166) lands** (migration lead, 2026-07-22). A
  recreate before then needs the hand mount reapplied; treat any lore-lore restart as
  an operator-visible step, not routine.
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
- 2026-07-14 · **#136 FIXED (operator-directed, commit bbe367f) — packets 17/23 UNBLOCKED.** The #102
  retry seam's runtime SDK-escape guard reported GREEN in any out-of-tree copy while its POSITIVE
  CONTROLS went RED. Root cause, TWO heads: it classifies frames by `co_filename` but compared them
  against roots derived from `__file__` PATHS — identical in the checkout, divergent in a copy.
  (1) the copied `.venv`'s editable `.pth` names the ORIGINAL absolute path, so production executes
  from the original tree and NO frame ever matched the watched root ⇒ zero observations ⇒ "no escapes"
  was true *the way "no unicorns escaped" is true*; (2) `cp -a` preserves mtimes ⇒ stale `__pycache__`
  ⇒ even the test functions' code objects carry the ORIGINAL path ⇒ the controls' staged escape was
  unmatchable ⇒ RED, beside that GREEN.
  FIX (the general form, operator-ruled): **A GATE MUST NEVER RETURN A VERDICT IT CANNOT SUBSTANTIATE.**
  `artifact_root()` derives the watched root from the IMPORTED MODULE (where code RUNS);
  `_require_a_root_the_code_runs_from()` cross-checks it against a live witness's `co_filename` and
  RAISES on divergence; `require_observations()` RAISES on zero observations — *blindness wearing
  cleanliness*. Lead-mutation-proven both legs + a positive control. 404 in-tree (was 399) · 9/9 in a
  copy · suite **5556/0** · ruff · mypy 0. The poison state is now UNREACHABLE.
  **RESIDUAL #140, bigger than the bug:** a `cp -a` copy never runs its own production code — the guard
  was merely the first instrument to NOTICE, being the only one that compares what it WATCHES against
  what actually RAN. THIRD instance of one law (#24, #139, #140): **prove which tree you are testing.**
- 2026-07-15 · **PACKET 01a CODE DONE — cold-audit GO; the DEPLOY is the operator's call.** `conform` verb +
  `conformance_run.sh` + `conformance_provenance.py` run the BAKED suite IN the deployed image, import-provenance
  gated (each member resolves to a BAKED root — /app or site-packages — NOT the /workspace mount; `.resolve()`→
  `is_relative_to`, mutation-proven). Measurement: **5545 passed**, the ONLY divergence a (b)-class mypy
  dev-toolchain meta-test (shells `uv run mypy`, needs a writable env) now opting out with a reasoned skipif;
  **ZERO artifact defects** — the two predicted are already closed (#131 git baked in, #107 unseeable by any
  suite). Contract-first: RED contract b528ac1 (30 pins), cold contract-adversary (built wrong guards → +4
  pins), Opus builder, cold REFUTE audit **GO** (coverage EXACT host 5566 == in-container 5566; both pins
  mutation-proven w/ positive controls; provenance-aborts-pytest chain proven; #141 lock pin discriminates).
  **Operator-EXPANDED with #141**: the image built via `uv pip install ./members` resolved FRESH and DRIFTED
  from uv.lock (mcp/starlette/uvicorn/sqlglot newer — untested in prod) → now `uv sync --locked --all-packages`
  (deps pinned to the lock + pytest baked; conformance == the LITERAL artifact). Wired as the post-`podman build`
  step, OFF `start`. Commits c90df55 (image) / b528ac1 (contract) / a35cdca (harness). #139 RESOLVED; #141 ack'd
  (fix committed, LIVE image still drifted until rebuild+recreate — the operator's production-touching deploy).
- 2026-07-19 · **PACKET 02 KICKOFF + operator SPLIT.** Opus contract author wrote the RED contract for
  #104/#103/#100/#101 + the promise-guard core (~1000 lines; new files test_comms_render_architecture.py +
  test_comms_promise_registry.py, migrated test_comms_tool.py to the new render signatures). Lead-verified a
  correct RED against CLEAN production (22 pins red for the right reason — `auto_ack_at_register` TypeError,
  missing STANDING_BRIEF, unconditional skew tail, `brief v` fleet cell; 11 guard-rails green). **The author
  measured the real work at ~3–4× the 0.20 est → OPERATOR RULED SPLIT:** 02 keeps ALL render work (#104 typed
  applicability + role accessor + #103 heartbeat generalization incl. the REAL `subscribed_name_skew` store
  method + 3 §9.4 tails + fleet cell rename) + #100 + #101 + the promise-guard CORE (delivers the exit smoke);
  new **02a** takes only the promise instrument's advanced hardening (not smoke-critical). ⚠ Delivery note: the
  author left its throwaway reference impl IN the production files and reported them "restored byte-exact" — they
  weren't (uncommitted, +136/−61 in server.py); lead reverted to clean HEAD + preserved the reference. #101 looks
  already-closed by 4c2efbf (3/3 green under full `-n auto`). Ledger row c2009c94.
- 2026-07-16 · **PACKET 01a DEPLOYED (operator-approved).** Rebuilt `localhost/lore:latest` from HEAD 062bf60
  via `uv sync --locked --all-packages` → image **f25c18976b2b** (LORE_VERSION v0.4-226-g062bf60); deps now
  match uv.lock live (mcp 1.27.2 / starlette 1.2.0 / uvicorn 0.48.0 / pytest 9.0.3 baked). `conform` GREEN
  against :latest BEFORE recreate (provenance all /app, 5545 passed). Both containers recreated on it from
  captured CreateCommands + boot-smoked GREEN (Uvicorn serving :9202/:9201, reconcile clean); `lore_index`
  serves branch feat/surreal-unification @ 062bf60. #139 + #141 RESOLVED. Old image 6d599942cc69 kept as
  rollback. The #141 drift is now closed in the RUNNING ARTIFACT, not just the recipe.
- 2026-07-19 · **PACKET 02 DONE + DEPLOYED (comms render architecture).** Image **ae0e78d9a504**
  (both containers, from HEAD 2b69616 via `uv sync --locked --all-packages`; conform **5596/0**
  in-artifact, provenance-asserted). Closes **#104** (STANDING_BRIEF role via ONE accessor — 4
  standing surfaces mutation-proven; renders take TYPED applicability `auto_ack_at_register`, ZERO
  name-comparison residual; `_brief()` monoculture default removed; promise-guard CORE), **#103**
  (heartbeat generalized to subscribed-name skew §5.3; §9.4 three name-conditioned tails; fleet cell
  `brief`→`project`; new BOUNDED `subscribed_name_skew`), **#100** (created_by removed), **#101**
  (confirmed fixed-by-4c2efbf). **LIVE-WIRE SMOKE PASS:** deployed heartbeat renders the non-'project'
  skew line truthfully with the explicit `name=` teach. Full contract-first cycle: Opus contract →
  contract-adversary (satisfiability **736/0**, closed a small-N cap/collapse gap) → Opus builder →
  cold REFUTE audit (**GO** on behavior; caught **F1** — `subscribed_name_skew` Q2 `id IN` was a full
  `brief` TableScan on EVERY heartbeat, green at every builder gate because the contract pinned query
  COUNT not PLAN; measured 6.1× at 11× rows) → **F1 FIXED** (`FROM $ids` direct record-access + an
  EXPLAIN-plan invariant pin, mutation-proven). Commits **d3c899f→05a8bb2** (+ ceb90ac spec residual,
  2b69616 report cleanup). Gates: full-repo **5611/0**, skill **117/0**, mypy 0, ruff clean. **OPERATOR
  SPLIT:** the promise-instrument ADVANCED hardening (full §9.7 per-entry predicate proofs + the
  `safe_str` literal-coverage closure) → **packet 02a**. Rollback image `f25c18976b2b` (lore:pre-pkt02)
  retained. Smoke artifacts: session `pkt02smoke` agents + brief in the prod comms store (documented,
  smoke_p8b precedent). Ledger row c2009c94 done. NEXT = **packet 03** (comms-message-graph).
- 2026-07-19 · **PACKET 02a DONE — TEST-ONLY, NO DEPLOY** (a2e9a70→ceac2d0, 6 commits; full
  suite **5694/0**, +83 = exactly the scoped suite's 34→117; skill 117; mypy 0; ruff clean;
  `server.py` md5 UNCHANGED throughout, verified by lead + 2 audits). §9.7 is now MECHANIZED:
  16 executable emit/no-emit proofs driving the real renders, with `registered ⟺ proven` a
  CHECKED invariant — a promise cannot be registered without proving its predicate gates it.
  The `safe_str` residual was closed, then GENERALIZED to **deny-by-default**: an unknown AST
  shape now FAILS LOUD (file:line + `ast.dump`) instead of silently becoming a placeholder.
  **THE LESSON, and it is not the code: 5 of the 8 defects were CLAIMS STATED AS REASONS AND
  NEVER EXECUTED** — an exemption comment asserting "BoolOp yields a bool" (`"" or "prose"` →
  `'prose'`) hid the commonest Python default idiom in plain sight; a bounded sweep then
  EXECUTED all 18 opaque-half claims and found **3 more false**. Every condemning measurement
  is now an executable pin, so no retired claim can be re-asserted from memory. Two defects
  were **vacuous proofs INSIDE the anti-vacuity instrument** (a marker that was a sibling's
  prefix passed 40/40 on a wrong build) — found by cold audit, not by any builder gate.
  3 audit passes (each NO-GO, each productive); 3 bounds PINNED w/ re-open triggers; #143
  ledgered (cross-satisfaction cannot see a k-specific prefix weakening — the mutation
  discipline is NOT retired by it). Operator ruled 2 scope expansions + 2 process laws:
  **coverage-premise entry checks** (a scope boundary resting on "X is already covered" is a
  PREMISE — probe it at kickoff; 02a's own scope line gave a real hole a formal alibi) and
  **DESIGN-LAW §15** (instrument packets route through the contract-adversary). Sized 0.20,
  ran ~4× — the holes were not visible until the instrument existed, so it could not have
  split at kickoff. NEXT = **packet 03** (comms-message-graph), unblocked all along (deps 02).
- 2026-07-19/20 · **PACKET 03 CONTRACT PHASE DONE — packet SPLIT THREE WAYS, no code written.**
  Contract written IN FULL then sized (operator-directed), adversary-graded, fixed: **400 pins,
  committed RED @ efef2b3**. Sizing walked 0.25 → 0.6-0.8 → 0.7-0.9 → the 03 half alone 0.55, every
  number measured by the author, never estimated by the lead → **03 STORE (0.20) · 03a LEDGER
  (0.35) · 03b SURFACE (0.30, deploys)**. Store is its own packet because it is the ONLY part
  changing behaviour for code already in production (101,479 live edge rows, endpoint-audited: zero
  poisoned, zero ghosts — the DATA is safe, the MECHANISM is the risk).
  **THE ENGINE SHIPS `ENFORCED`** — a declarative RELATE endpoint guard, on our floor since 2.0.3 —
  and this repo's own store reference had asserted an app-level check was "the only guard". FALSE.
  Five live probes and a cold audit never found it; **one doc page found it in minutes**, on the
  operator's "read the docs, probes only confirm" directive. Store reference corrected in three
  passes (§6.3/6.4/6.5 + a FALSE §3 root-cause rule of our own + §6.6 "claims we are the sole source
  for"). #105 ruled to stay in 04 with the exposure widened there; broadcast = ALL NON-RETIRED; the
  waiting state is **DERIVED, never stored** (both the design sentence AND shipped behaviour struck).
  Adversary: **8 wrong builds passed the ledger contract 57/0**, all now mutation-proven RED; B1's
  root cause was a FIXTURE CORRELATION, not a missing assertion. One defect neither author nor
  adversary could see (both graded in scratch copies holding the reference build): the contract
  poisoned a SHARED fixture module, making **6 pre-existing suites UNCOLLECTABLE — ~1220 tests gone,
  tail reading "no tests collected"** (#133's shape). Fixed; collection clean at 6079/0.
  New findings **#144-#149**; agent-comms MEASUREMENT recorded in docs/orchestration (self-armed
  watchers deliver MID-CHAIN; a 4-model consult was FALSIFIED 0-for-2 where testable).
  NEXT = **packet 03 (the STORE)**, fresh session.
- 2026-07-20 · **#150 DONE — TEST-ONLY, NO DEPLOY, ZERO PRODUCTION DRIFT** (`6be78d6`→`9e226e5`,
  10 commits; blob-hash tree over `loremaster/loremaster/` IDENTICAL at `8c96451` and HEAD).
  The test harness hand-rolled an un-retried session bootstrap — **the TWELFTH copy of the #120
  shape, and the correction to this Log's own "eleven hand-rolled copies deleted" line above**:
  the #102 chain deleted eleven in PRODUCTION and never swept the harness, because the gate that
  found the eleven scans production ONLY. `connect_admin` (21 callers / 35 importers, both counts
  DERIVED at assert time and pinned as a strict subset) now routes through `bootstrap_session`;
  teardown's `use()` + REMOVE share ONE composed budget through `retry_on_conflict`; the private
  marker/budget/backoff are DELETED and the harness owns no conflict-retry policy at all.
  **Instruments, not just fixes:** the bootstrap gate now scans the TEST TREE with a
  **receiver-blind AND method-blind** deny leg (the SDK ships `query_raw` beside `query` — a
  `{query,execute}` allowlist was the six-defeats table's own row) + a one-row **site-count**
  allowance, measured fallout **ZERO**; the `use()` leg stays receiver-keyed on purpose (`use` is
  an English verb) and its bound is **PINNED with a named re-open trigger**, not silently
  inherited. Graders earned their keep: a contract-blind diff reader found teardown running TWO
  uncomposed 2.0s budgets (**measured 3.812s**) that nobody else saw, and a cold audit built a
  wrong build — `connect_admin` with three independent budgets — that **passed the contract
  17/17**; both now RED. Also fixed: `scripts/typecheck.sh` reported **3 errors instead of 55**
  depending on cwd (`a59d759`; exit code was always honest, the OUTPUT lied). New finding **#151**
  (bootstrap_session passes no retry `label`, and `retry_on_conflict`'s docstring FALSELY claims
  it "has its own attribution" when it logs nothing) — deliberately OPEN by operator ruling, with
  a tripwire pin that reddens the day it is closed. NEXT = **packet 03 (the STORE)**, unchanged.
- 2026-07-21 · **#151 + #152 CLOSED — the wave that kept regenerating its own defect class.**
  **#151** (`352db0e` + `98980bd`): `bootstrap_session` called `retry_on_conflict` three times
  with NO `label`/`url`, so an exhausted bootstrap raised *"see the server log for the full
  engine detail"* over a record holding `{attempts, elapsed_seconds}` — **a message promising a
  receipt that did not exist**, with `__cause__` None. Now every one of the **eleven** owners
  threads its OWN url (two — `SurrealStore`, `TaskLedger` — were missing from the lead's
  hand-list and were found only because operator ruling R2 made `url` REQUIRED, so the type
  system enumerated the population a grep could not). Scout's three seams are label-attributed;
  the exemption allowlist is down to `execute_transaction` alone. **THREE INDEPENDENT GRADERS
  EACH FOUND A DISTINCT HOLE THE PREVIOUS ONE MISSED:** adversary #1, a missing QUANTIFIER — a
  build hardcoding the url passed **489/0 with ZERO delta across all 6079 tests**; adversary #2,
  a missing HALF — a behaviourally-perfect build with the false docstring intact scored
  **515/0**; and the cold audit, a FALSE exemption clause (*"the engine's text rides the
  traceback"* — measured false) that **both adversaries had blessed by INSPECTION and neither had
  MEASURED**. That last one is **#156**: an exemption's evidence is an assertion about runtime
  behaviour, and the §10 gate checks it for presence and a 60-char floor because *"no assertion
  can read English"* — so **every allowlist in this repo can carry a false justification
  forever**. Final: 35 pins, **531/0** scoped, **1168/0** structural, full suite **5722 passed**
  (+63) with the packet-03 RED unmoved at 309/166.
  **#152** (`ee0bec2` `9601455` `e81a3ff` `db9973b`): ~350 citation sites adjudicated per-site by
  seven readers; **~87% were PROVENANCE and deliberately LEFT ALONE** (their verdict tables are
  the archived record of why). ~54 false "RED today" claims retired to past tense naming **13+
  distinct closing commits**, each derived by `git log -S`, never assumed.
  **THE ROOT CAUSE IS NOW LAW (`968883d`, #153):** the old rule mandated an address *and* mandated
  its destruction — *"delete all before any image build"* — so **57 report names were cited and
  only 3 resolved**. Reports are now ARCHIVED into `docs/plans/v2/receipts/<date>-<packet>/`;
  three archives landed (`7d2ff44` `1666856` `b3e7687`) and resolving citations went 3 → 9. The law
  also fixes the two forms this wave watched fail live: **cite the archived path, and cite SYMBOLS
  not LINE NUMBERS** — one fix shifted three scout seams and falsified nine citations TWICE, so
  renumbering would have shipped stale within the same session.
  **THE LESSON, and it is the reason this entry is long: the fix kept regenerating the defect.**
  Landing the labels falsified two caller enumerations; shifting scout falsified nine line cites;
  archiving the reports falsified a claim that they were untracked; archiving the #102 design docs
  **broke `test_retired_symbols` for 13 commits** because the lead ran the changed and
  blast-radius suites but NOT the structural pins. Nine times a hand-list lost to the tree (twice
  the lead's own); the CWD trap fired nine times, once SILENTLY returning 0 where 26 was true.
  Every one was caught by the NEXT grader, never by a gate. So the wave stopped extending lists
  and started **inverting** them — name what is EXEMPT, not what is covered — which is
  "allowlist the safe" applied to prose. Deliberately NOT built: the citation allowlist pin,
  because on day one it needs a **51-entry exemption list**, in the wave that discovered
  exemption evidence is unguarded (**#157**, with a named re-open trigger).
  New findings **#153** (report-protocol root cause, FIXED in law) · **#154** (dead SPEC paths) ·
  **#155** (an unfiled obligation living in a test docstring) · **#156** · **#157** (the legacy
  tail, deliberate). NEXT = **packet 03 (the STORE)**, unchanged.
- 2026-07-21 · **#151/#152 CLOSE-OUT — the final cold audit said NO-GO, and it was right.**
  The entry above was written before the wave's own audit reported. That audit CONFIRMED #151's
  behaviour fixed end-to-end (all six seams driven to exhaustion; label + url + engine text
  present; a positive control reproducing the pre-fix empty record) and then returned **NO-GO on
  the wave's PROSE**: seven false claims of the exact class the wave existed to close, two born in
  its own commits, all green at ruff/mypy/the full suite because no gate reads English.
  **The worst was in STANDING LAW and it was the lead's.** `CLAUDE.md` claimed archiving the
  #150-wave reports "made **15 citations** resolve at a stroke". Measured: **1** — seven of the
  eight reports were cited zero times. The 15 came from counting bare AGENT-NAME mentions
  (`blindreader-150 F3`) and reporting them as report ADDRESSES. **Two populations conflated into
  one count — #102/#120 verbatim, inside the law written to stop it, by the lead who had just
  written "re-derive it yourself" into four agent briefs.** Same figure had gone into #153 and a
  commit message simultaneously. Corrected at `7d20afe`, WITH the story of its own falseness left
  in the file; ledger correction **#158**. Also fixed: a false line citation shipped into
  PRODUCTION by the #151 fix itself (`:1242` was a docstring line; the raise was at `:1293` — the
  number was copied from the pre-fix tree by the commit that moved it).
  **Then the lead broke the same gate twice.** `2a080e0` archived a report naming retired symbols
  with no SUPERSEDED banner and re-broke `test_retired_symbols` — the identical defect
  `db9973b`'s own message confesses to, eight commits earlier, still in the log. Caught only
  because the auditor **re-verified at the new HEAD** ("a cold auditor does not accept 'fixed' as a
  claim") — and it could catch it because the lead had archived its report WHILE IT WAS STILL
  WRITING: the copy acted on was 546 lines, the complete one 690, and the 144 unread lines held the
  gate failure. Fixed `7e52af9`. **Two rules out of it:** archive a report only AFTER its author is
  reaped; and after repairing a prose instance, **re-run the bare grep and confirm the count went to
  ZERO** — never repair from a report's list (the fixed-one-missed-the-sibling shape hit three times
  in this wave alone).
  **Also:** `git add -A` tracked 61 files / 397K of `scratchpad/`, breaking an invariant
  `pyproject.toml:35` had stated for months with nothing enforcing it — now in `.gitignore`
  (`7383342`), mechanical rather than remembered.
  **brief-base bumped to v6 GLOBALLY** (operator-directed): a report is a DURABLE artifact; **a
  retrieved chunk arrives without its header, so date claims WHERE YOU MAKE THEM**; cite durable
  addresses and SYMBOLS not line numbers. ⚠ `~/.claude` is **not** a git repo, so v6 is unversioned
  on disk — operator informed, decision deferred (the `lore-deploy` symlink-into-a-repo pattern is
  the precedent).
  **The archived reports turned out to be SEMANTICALLY SEARCHABLE already** — `lore.yaml` includes
  `**/*.md`, so archiving IS ingestion (receipt: an adversary's mutation proof retrieved mid-file at
  sim 0.57). Three rows out of that: **#161** (cosine floor stale — corpus 214→353, lore says so
  itself), **#162** (an UNBANNERED `scratchpad/` twin outranked the bannered archive), and **#163**
  (PACKET: serve chunks as an ordered, section-aware, chronological THREAD + graph reports to
  findings/commits/symbols — subsumes #160; the chunker already computes the breadcrumb, nothing
  serves it; #162 must land first).
  Final: 22 commits · full suite **5722 passed** (+63) with packet-03's RED unmoved at 309/166
  (attributed 309/309, incl. one non-obvious `test_surreal_schema.py` site) · ruff clean ·
  typecheck 55/5 baseline · #151 + #152 RESOLVED · open: #153–#159, #161–#163.
  NEXT = **packet 03 (the STORE)**, unchanged.
- 2026-07-22 · **SURREALDB 3.2.1 MIGRATION CONFIRMED (Fable consult, verifying the migration
  session's work):** both stores 3.1.5→3.2.1; prod byte-identical (174,161 rows/20 tables);
  suite behaviour-IDENTICAL across engines (the substring conflict-classifier demonstrably still
  fires — the suite IS the probe); #107 re-probed; vendor doc tiers indexed (corpus 2764 by
  design); reference §0 = ff7128e; #164 wedge mitigated by recreate; findings #164–#166 filed.
- 2026-07-22 · **SLOTTING RULING (operator; sizing-checked):** #144+#164 split packet 07 →
  **07 CLASSIFICATION / 07a RECOVERY** (both 0.20); **#166 (⊃ #165) REDESIGNATES 19 as
  deploy-architecture DESIGN** (0.15, mints 19b+ ≤0.25 — a design problem never reaches a
  builder); **28a minted** (#163 threads, dep 14/#162); #146→03 · #145/#147/#143→03b probes ·
  #149→05 · #155→28 · #162→14; #154/#157 pool 22 · #156 pool 23 (DESIGN) · #159 watch; 03a/03b
  gain →split marks (0.35/0.30 ≥ law); #153/#158 resolved (law + correction landed); **#167
  filed** (schema rebuild stuck failed/fingerprint-mismatch, serving old fingerprint).
- 2026-07-22 · SESSION: both stores migrated 3.1.5→**3.2.1** (prod 174,161 rows byte-identical;
  backup /backups/lore/; ref doc→3.2.1). **SurrealDB docs + CI-verified specs indexed as lore
  static tiers `surrealdb-docs`/`surrealql-tests`** (v3.2.0; 1st static-tier use → deploy defects
  **#165** /source-mount + **#166** two-toolchain-arch). **#167 RESOLVED** (hand-stamped fingerprint
  f6e2ee34) → **embedding-schema RECONCILIATION design #171** (docs/design/2026-07-22-…, FULLY RULED,
  ⊃#168/#169, adopts #170; awaiting planner). CLAUDE.md→agents search the tiers; new **#164–#171**.
  ⚠ **lore-lore on a HAND-ROLLED /source mount — NOT restart-durable pre-#165/#166**; 210→218 symlink.
- 2026-07-22 · **#171 SLOTTED (Fable planner; sizing-checked): packets 11a (contract, 0.20) +
  11b (build, 0.25) minted in wave L BEFORE 12/13** — the ruled design is a spec-to-implement;
  Q5 ruled it its own packet; 12/13 now ride 11b's extracted `ChunkerRegistry.resolve` and #10's
  retroactivity composes with the routing sweep (my earlier same-day 12/13 folds REVISED — the
  design supersedes them). 24 certifies the reconciler at 53k. Mount hazard → watch list.
- 2026-07-23 · SESSION: (1) **lore is now the SOURCE OF TRUTH for project memory** — the lore-deploy
  SKILL.md gained a bootstrap+migration protocol; this repo's flat auto-loaded `MEMORY.md` (17KB, 51
  topic files) MIGRATED into lore byte-exact (2 independent oracles; finding **#172**), `MEMORY.md`
  slimmed to a 1.9KB bootstrap; repo+skill instructions carry the standing rule. (2) **Spectron docs
  indexed as static tier `spectron-docs`** (143 .mdx / 1467 chunks, surrealdb/docs @ 9d42eba) — pool
  item 12 design-half UNBLOCKED, verdict memory superseded. New-static-tier gotcha: `acquire` reads
  the un-mounted corpora `source` (#165/#166) → index HOST-SIDE (`--tier`) then recreate; `.mdx`
  already-mapped ⇒ fingerprint unchanged (f6e2ee34), no re-embed/stamp fix.
- 2026-07-23 · **PACKET 03 (comms STORE) DONE — TEST+STORE only, NO deploy** (df59f76 schema ·
  10d8de4 receipts). One file: `surreal_schema.py` gains the `message` node + `to` delivery edge +
  `message_seq` native sequence + `generate_message_ddl()`, and the **relation-table POLICY FLIP** —
  `_define_relation_table` extended (ONE impl, not a fork) to emit `DEFINE TABLE OVERWRITE … TYPE
  RELATION IN … OUT … [ENFORCED] SCHEMAFULL`; all four edges flip bare-`IF NOT EXISTS`→typed-OVERWRITE
  (only `to` ENFORCED). Contract efef2b3 (400 pins); scoped **304/0**, blast-radius **432/0**, ruff
  clean; 03a `test_message_ledger.py` stays RED unchanged; typecheck `surreal_schema.py` clean, 55→54
  (all residual in the RED 03a/03b contract — TEST-ONLY split; global-zero returns when 03a/03b build).
  **3.2.1 re-probes:** #349 dup-`(in,out)` still a LOUD err (edge count 1, no silent dedupe) → dedupe-
  before-RELATE holds; #308 no packet-03 pin leans (warm conns). **#146 adjudicated (lead): bare
  `DEFINE SEQUENCE IF NOT EXISTS message_seq`, no BATCH/START → hazard dormant; accept-with-trigger =
  the day any sequence gains/changes BATCH/START.** Full contract-first cycle: committed RED contract →
  Opus builder → cold REFUTE audit **GO** (independent gates + own mutation matrix restored byte-exact +
  edge-directions verified against real RELATE sites; residuals R1–R5 all adjudicated, none escalated).
  Prod-touching flip lands at 03b's deploy (dirty-store pins verify row preservation). NEXT = **03a
  (the LEDGER)**, now unblocked. Minor: R3 `question`/`ack_note` offline TYPE-unpinned but ∀-guard- +
  live-covered (met deliberately); R4 typecheck-gate read = "writable file clean + no new errors".
- 2026-07-23 · **PACKET 03a SPLIT AT KICKOFF** (0.35 → split, operator-confirmed) into **03a-1**
  (SEND path + `AgentRefLike` home + module foundations; ≥8-way send concurrency — THIS session) and
  **03a-2** (drain/peek, ack + four-way disambiguation, derived waiting state; 16-way ack concurrency —
  closes 03a). New bootable files `03a-1-comms-ledger-send.md` / `03a-2-comms-ledger-consume.md`; the
  `03a-comms-message-ledger.md` file stays the shared reference (split banner added). Entry check
  CLEARED (HEAD f90bbf0, store slice live, 180 pins RED for the right reason, :18000 healthy,
  coverage-premise render→03b CONFIRMED). Ledger: umbrella `54634b3d`→03a-1 `6804b707` (in_progress);
  03a-2 `96f9f3a0` (blocked_by 03a-1); 03b rewired onto 03a-2 (task `b7f89c12`; transient successor
  `618cd45d` retired to wontfix — `supersede` drops `blocked_by`, so 03b was re-created with the dep).
- 2026-07-23 · **PACKET 03a-1 DONE — send + drain + `AgentRefLike` home + foundations (TEST-ONLY,
  no deploy).** Commits 2d1f75d (AgentRefLike → `loremaster/agent_ref.py`, briefs re-exports) →
  e6b9b81 (`messages.py` MessageLedger: send = `sequence::nextval` + CREATE + N×RELATE in ONE txn,
  all-or-nothing ghost guard + `ENFORCED` backstop, dedupe-by-identity; + drain/peek) → 0cff06d (seam
  registration) → 42eeedc (#173 C-DEF `_seed_agents` CREATE→UPSERT). **drain pulled into 03a-1** (11
  send pins call `drain(peek=True)`) → **03a-2 is now `ack` + `awaiting_answer`**. Cold-audit **GO**:
  [real] leg GRADED (§7.8 residual CLOSED, 0 silent skips); 4 mutation proofs w/ positive controls;
  #173 fix proven non-weakening. Full ledger file **140 passed / 31 red** (all 03a-2 `NotImplementedError`
  stubs) **/ 9 skipped**; send-concurrency **20/20** ×3; ruff clean; writable-prod mypy-0; retry_seam
  503; brief_ledger 120. Receipts `docs/plans/v2/receipts/2026-07-23-packet03a1/`. #173 resolved.
  NEXT = 03a-2. uuid-vs-ulid id → decision pool 24.
- 2026-07-23 · **pool #24 RULED (operator): message id → ULID.** Follow-up to 03a-1: `message.id`
  `uuid4().hex` → `str(ULID())` (python-ulid 4.0.1, client-side; dep on `loremaster/pyproject.toml`,
  root pyproject zero-diff). Time-sortable for pkt-05 `since=`; pre-deploy, no migration. Commit
  `13da377`; lead-verified (small-fix path — diff + re-run): bareness pin both legs, full file
  140/31/9 unchanged, ruff clean, mypy +0. Follow-up report archived in receipts/2026-07-23-packet03a1/.
- 2026-07-23 · **PACKET 03a-2 DONE — ack + derived waiting state; 03a CLOSED (TEST-ONLY, no deploy).**
  Commits `853a95b` (ack = write-once CAS + 4-way disambiguation, three set-based statements;
  `awaiting_answer` = ruling 9's read-time derivation) → `f0f3e79` (design rulings) → `50d65a0`
  (audit residuals R1+R8) → `f04729c` (the ruled `sender != me` conjunct) → `0223291` (receipts).
  Ledger file **180 passed / 12 skipped / 0 failed**; retry_seam 503; ruff clean; typecheck held at
  36 (31/3/2 — **all in 03b's RED contract test files, zero in any production module**, per the
  2026-07-23 operator ruling deferring global mypy-zero to 03b's end). 16-way ack concurrency
  **20/20 consecutive**, re-derived independently by the cold audit. Driver sharing proven by
  MUTATION (6/6 legs follow the moved `_RETRYABLE_CONFLICT_MARKER`), not by inspection.
  Cold-audit **GO**, `[real]` leg graded: **31 real-leg pins execute, 0 silent skips.**
  **THREE DEFECTS the builder gates could not see, all found after green:**
  (a) **R1, a FALSE GATE** — `test_the_derivation_writes_NOTHING` promised to catch a build that
  "stamps an `agent` column (or any row)" and asserted only ROW COUNTS; injecting ruling 9's struck
  stored state verbatim (`UPDATE agent SET status='input_required'`) passed the whole `[real]` leg
  86/0. Closed at the **statement seam** + a receiver-blind content leg — NOT by counting more
  tables (enumerating the forbidden is the defeat this repo has now paid for seven times). The
  content leg earns its place: a write SMUGGLED INSIDE A SELECT SUBQUERY is legal SurrealQL that
  lands [PROBED 3.2.1], defeats the seam leg, and is caught by content. **Operator-authorized
  amendment** to the immutable contract (precedent `42eeedc`); pins 85→91, no assertion weakened.
  (b) **R8** — `_ack_entries` tested `not in stored_stamps` BEFORE `in won_stamps`, so a CAS WINNER
  whose edge vanished mid-call was reported `not_addressed`. Ladder re-ordered by strength of
  evidence. Latent (#105 clause), never correct.
  (c) **R2, design-ruled** — a SELF-ADDRESSED follow-up discharged the asker's own debt
  (false-NOT-waiting, the invisible direction ruling 9 refuses). The existing pin is NAMED for this
  unconditionally but its fixture could not reach the door. Fourth conjunct `sender != me` RULED IN
  by design-comms; the docstring had ALREADY promised it. Ruling 7 intact — self-addressed messages
  still DELIVER (positive control passes UNDER the mutation, so it is independent of the conjunct).
  **DESIGN RULINGS (design-comms, delegated authority — the consumer is an agent fleet):**
  `docs/plans/v2/03a-2-consume-path-design-rulings.md` — 6 rulings + a delta table.
  **INHERITED BY 03b** (rows 1–11 of that table): both `message` indexes (`seq`, `(sender, question)`)
  BEFORE its deploy — production carries zero message rows until then, so the index build is free
  exactly once; the deliveries-SELECT bounding; pins for duplicate-seq, thread-level debt (both
  directions), read-order + short-circuit; and a **binding RENDER LAW** — ack-nudges key on
  `acked_at` never `seen_at`, queue counts say "unread" not "unactioned".
  **NEW FINDING #175** (store, latent): `UPDATE <edge> … WHERE in IN $ids` **silently matches ZERO
  rows** on 3.2.1 while the identical SELECT matches; adding `out = $x` makes it work. Shipped code
  unaffected (every such UPDATE carries `out = $agent`); the hazard is any future message-scoped
  edge write. Mechanism UNVERIFIED — disposition: re-probe with the UNIQUE index dropped, then land
  the confirmed fact in the store reference §2/§6.6.
  Receipts `docs/plans/v2/receipts/2026-07-23-packet03a2/` (six waves; the auditor's report carries
  an **archive-correction header** — its mypy distribution summed to 48 beside its own correct 36).
  **NEXT = 03b** (task `b7f89c12`, now unblocked) — it ships the surface AND deploys both containers.
- 2026-07-24 · **03b CONTRACT PHASE STRUCK + RESET (operator; #181).** The prior orchestrator's
  contract authors built their own reference builds then wrote the tests, self-certifying both waves;
  both adversary verdicts (INSUFFICIENT) were never re-run after the fix waves. Reverted to the 03a-2
  close at `0941aab` (verified 160F/1205P/12s trusted RED · mypy 36/0-prod · ruff clean); corpus tagged
  `pkt03b-tainted-corpus`; reports struck-bannered. Re-run: blind design re-derivation → clean contract
  phase (authors never build references; the adversary builds + re-grades every wave) → client acceptance.
- 2026-07-24 · **PACKET 10 DESIGN DONE + PACKET 10-d BUILT, AUDITED & MERGED (not deployed).** Operator
  ruled the architecture (floor in SurrealDB; container detects staleness, container fixes it,
  new floor stored — no outside caller) and delegated the detail forks to the design sidecar.
  Design `docs/design/2026-07-24-floor-calibration.md` (R1–R8 + Addenda A–E): staleness is now a
  MEASURED quantity (fresh floor's CI disjoint from the adopted one's) — the inherited 10% churn
  threshold is DELETED, not re-tuned; one disjointness test governs adoption, per-tier upgrade and
  #180's per-hit floor. F1/F2/F4/F5/F6 decided-by-delegation; **F3 re-routed from an operator fork
  to a CLIENT CONSULT** (the 2026-07-06 precedent already ruled weak-match signalling a client
  question — the lead mis-routed it and the operator caught it); consult runs AFTER 11-i on R2's
  measured divergence ("we need to measure first"). Under the new TRUST DOCTRINE the sidecar ruled
  **DISARM NOW**: packet **10-d** darkens both confidence surfaces (`_COSINE_WEAK_MATCH_FLOOR =
  None`) — built (`bdb7929`), cold-audited **GO** (`d5345ad`), **MERGED to this branch 2026-07-24
  (operator-authorized, 03b agent concurring), STILL NOT DEPLOYED** — the running image continues to
  serve the confident-wrong surfaces until a deploy ships. 10-d's deploy is intended to RIDE 03b's
  rather than force a second hazardous lore-lore recreate (#165/#166). ⚠ `smoke_p8b` check 8 asserts
  `cosine_floor.state == "disabled"` and is therefore **RED against the currently-deployed image BY
  DESIGN** — it IS the deploy gate, not a defect. Packet 11 SPLIT → **11-i** (dark machinery, no deploy) / **11-ii** (cutover + a §C5
  consumer battery as ruled acceptance). ⚠ **The trap, carried into 11-ii:** the disarm MASKS #176,
  it does not fix it — `_format_result` still has no `disarmed_by_drift` term, so arming the floor
  re-opens it instantly. New findings: **#176** (per-hit no drift gate), **#179** (foreign-instance
  constant), **#180** (best-of-response floor served per-hit — the basis mismatch), **#185**
  (`scratch_copy.sh` does not git-isolate a copy made from a WORKTREE; Python provenance passes
  while git commands hit the real worktree). #178 resolved as the lead's own duplicate of #179.
  R3 (drift/stamp fields go dark with the floor) ADJUDICATED — accept, re-open trigger = 11-ii.
  Also fixed in passing: the `TeammateIdle` gate could not see a worktree-assigned agent's committed
  report (`14a987b`) — it false-nudged every packet-10 agent; a gate that refuses honest work is a
  gate that gets switched off. Receipts: `REPORT-{fable-design-pkt10,builder-10d,audit-10d-cold}.md`
  (to archive at close-out) + `docs/design/2026-07-24-floor-calibration.md`.
- 2026-07-24 · **03b CONTRACT PHASE CERTIFIED — both waves SUFFICIENT (the recovered packet).**
  Surface `57d8677`: 4 adversary passes, 52 wrong builds, 6 blockers→0, satisfiability 1209/0
  post-lint, CL3's paragraph allowlist terminates the teaching regress. Telemetry `f6cb14a`:
  5 rounds, ~60 builds, the signature-bound double + MP-A..I close the outcome×store×subject
  matrix, one accepted bound with named trigger. Process held end-to-end: authors built NO
  references; adversaries built from rulings contract-blind-until-frozen; every ambiguity ruled
  same-day in-tree. NEXT = merged-build gate over the post-merge tree (incl. 10/10-d), then builder.
- 2026-07-24 · **MERGED-BUILD GATE GO + SESSION BOUNDARY.** Both references composed clean onto the
  post-merge tree (0 anchor failures / 0 conflicts); the gate caught a C-DEF escape first-try (CL3
  had never met a correct build; the reference's un-ruled prose edit → B-OBL-1) — corrected: full
  6532/0 · typecheck 0 all members (global mypy-zero PROVEN; RG-R3 settled) · ruff · skill 117.
  Nine 03b reports archived to receipts. Build phase = a FRESH session per the packet file's
  BUILD-PHASE HANDOFF section (fresh Opus builder, withheld set, obligations, battery, deploy).
- 2026-07-26 · **03b DONE + DEPLOYED.** Build → 2 cold audits + 2 contract-blind reads → 5 fix waves →
  client battery → deploy BOTH. Suite **6937/0** (scripts/ now in testpaths — both new guards were
  ungated), global mypy-zero discharged, every production receipt green: round-trip, hostile body
  fenced (5 forgeries in body, 0 unfenced), broadcast by membership, E-S5(c) skew both paths, 88 trace
  rows with distinct ordinals, and the elision re-ask **obeyable end-to-end across 54 messages**.
  **#147 closed with a production receipt** (0→664). **THE BATTERY EARNED ITS KEEP**: it caught a
  forged in-fence row counted as delivered 2/3 runs — with the fence MECHANICALLY CORRECT, so 6609
  tests and four cold passes all missed it; every other instrument checked that the fence was
  APPLIED, only this one asked whether a real LLM was still fooled. Cost $1.50. NEW LAW: the rider is
  part of the ruling (6 instances); filing a rule does not install it (#194 recurred 3× incl. inside
  its own instrument). NEXT = 04.
- 2026-07-26 · **11-i DESIGN RULED + SECURITY FIX WAVE MERGED** (`c192cb4`, ff to main). 11-i: S1
  measured **NOT DEGENERATE** with the mechanism derived (modal mass capped at ≈63.5% by
  `(1−1/N)^N→1/e`; measured 25.8–64.8%) · client consult, 3 blind informants, unanimous **refuse the
  served CI** · all 23 decisions ruled (RULINGS-2026-07-25.md) after the operator declined a queue —
  20 derived from standing directives, 3 genuine lead calls. Fix wave **#210/#207/#211** shipped
  through 2 cold audits: charset `fullmatch` + AST class instrument · 5 unjittered backoffs onto one
  full-jitter policy · `SecretStr` end-to-end + traceback render AND scrub (8 `exc_info` sites had
  been logging NOTHING). **THE GRADING CAUGHT 5 DEFECTS NO BUILDER GATE COULD SEE**, incl. a 100%
  breakage live at the tip that three gates missed *simultaneously* (`scripts/` outside `testpaths`,
  mypy never analysing it, and the covering test monkeypatching the broken function away), and a
  redactor false-positive found only because an auditor ran from a UUID-bearing path. **Post-merge
  1 failed / 7065 passed — failure set IDENTICAL to the pre-merge baseline taken from main**; the
  109 mypy errors resolved with 03b's implementation. **The #210 class instrument caught a CLONE of
  its own defect ON MERGE** (`c192cb4`) — first live catch, not a pin. NEW LAW: #229 (a range is not
  stronger than an equality — 4 hollow pins, 3 agents, 1 lead ruling) · #224/#225/#228 (a count, a
  negative search, a `pgrep -f` watcher — all claims whose scope is implicit in the instrument that
  produced it; one watcher had waited on ITSELF for 13.5h). NEXT = **42** (operator: prevent the leak,
  delete the sanitizer — 12.4% of function names are hidden from logs today).
- 2026-07-26 · **BRANCH/DIFF-AWARENESS CONSULT** (operator question → input to packet 17). Three
  independent positions (Sonnet 5 · Opus 5 · Fable lead — lead's committed to file before reading
  either return; receipts `docs/plans/v2/receipts/2026-07-26-branch-diff-consult/`, SYNTHESIS.md
  carries the forks). Unanimous: never re-serve textual diff (git is the engine; all three, as
  consumers, would route around a re-serve) · the servable half is GRAPH-over-the-delta ("git
  answers what did I change; git cannot answer what does what I changed TOUCH"; changed-symbol
  inventory ~free on the overlay's own merge-base enumeration) · NO git-ref mode on `lore_diff`
  (two identity spaces under one verb; its snapshot rows already render git_branch@git_ref — a
  primed misread, filed **#232**) · ref-vs-ref for unchecked-out refs NEVER, re-open trigger named
  (a wave needing structural comparison of two sibling worktrees' deltas, or Odoo onboarding).
  Fork awaiting operator ruling: v1 scope — Opus "graph over the delta" (inventory + delta-scoped
  search + batched BASE-SERVED impact/tests behind the numbered caveat; Fable concurs) vs Sonnet
  "inventory only, rest inherits the v2 disposition". Packet 17/23 docs untouched — the ruling
  lands there.
- 2026-07-26 · **BRANCH/DIFF CONSULT FORK RULED** (same day): operator ruled v1 = **graph over
  the delta** (Opus Option 1 — changed-symbol inventory in the registration render, delta-scoped
  search, batched BASE-served impact/tests behind the NUMBER-bearing caveat). Recorded as a ruled
  constraint block in packet 17's doc; unanimous consult positions (no textual re-serve · no
  `lore_diff` ref mode (#232) · ref-vs-ref never + re-open trigger · the three-identity trust
  riders) adopted there as constraints-to-cite. Packet 23 inherits via packet 17's spec.
- 2026-07-26 · **BRANCH/DIFF CONSULT, SECOND WAVE RULED** (rounds 2–5, same three-model method,
  lead position committed blind each round; receipts `docs/plans/v2/receipts/2026-07-26-branch-diff-consult/`
  — FOLLOWUP-*.md verbatim, SYNTHESIS-2.md consolidates). Operator escalated four scenarios
  (hosted multi-user · agent-worktree fleets · local inotify scouts post-split · two scouts on
  one branch); each FALSIFIED a stated absolute — incl. the pushed-only bound all three
  participants asserted — and strengthened the design. **ADOPTED IN FULL into packet 17's second
  ruled block:** view identity **(parent, ref|path, feed-instance)** · SINGLE WRITER PER VIEW
  (branch name never a key; the two-dev-on-staging race made inexpressible; lore never merges
  trees — push/pull is git's channel) · declared agent-granular sessions, no default view or
  disambiguation · feed-typed honesty (scout-fed requires a POSITIVE heartbeat, designed in 17)
  · isolation pinned on TWO legs with named discriminating fixtures (same-file three-sibling;
  same-relative-path ingestion routing + control) · ephemeral-vs-standing lifetimes · ≥8-way
  pins · 39 seam list named (write grants, base read-only to scouts, content trust, revocation).
  **Scenario A re-ruled: standing multi-ref visibility IN for the hosted design, build deferred**
  (narrows the morning bullet; the compare-verb never + no lore_diff ref mode stand). Meta-finding
  recorded: topology-shaped absolutes ("which topology am I picturing?"). Packets 36/38/39
  inherit their named seams; 23 inherits via 17.
- 2026-07-26 · **10-d ROW CORRECTED — it was DEPLOYED, the row said "open — ships FIRST"** (operator
  caught it at 04 kickoff). 10-d merged `be4c591` 2026-07-24 and its deploy RODE 03b's, exactly as
  the 2026-07-24 Log entry planned; nobody flipped the row. Three instruments agree: the merge
  commit, both containers on `b46bc1d5`, and the RUNNING artifact's own `lore_index()` serving
  `cosine_floor.state="disabled"`. ⚠ The disarm MASKS #176/#179/#180 — they stay OPEN for 11-i/11-ii.
