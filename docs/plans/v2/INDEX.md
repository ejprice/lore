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
sequence is never renumbered again. **Anomaly on record: packet 42** (operator-minted
2026-07-26) carries a number past the tail while RUNNING in wave L — by this law it would
have been a letter suffix, but it is already cited by number in the Log/ledger/commits, so
the number STANDS; its TABLE row position, not the filename sort, is its order of record.
Completed work keeps its historical id
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

## State of record (verified 2026-07-26, by the findings sweep — after 03b, 10-d, and the 11-i design + security fix wave)
- Branch `feat/surreal-unification` — **PUSHED through `d5b6ad8`** (upstream exists since the
  11-i-a merge; local runs ahead by the sweep docs commits). Since the first sweep: **42 DONE +
  DEPLOYED** (all three mid-flight riders honoured — #235's production receipt: the redactor had
  been logging the credential for every non-Bearer scheme) · **04 split → 04a DONE, then 04b
  split again → 04b-1 DONE (8256/0, test-only) / 04b-2 NEXT (deploys, carries 04a + 04b-1)** ·
  **11-i-a BUILT + AUDIT-GO + MERGED at `c7983e8` (Log 2026-07-27; worktree removed)** —
  11-i-a-r carve-out minted + claimed; 11-i-b consult done (the TRUST hard definition landed in
  CLAUDE.md), its contract next · **packet 43 minted** (operator
  ruled the D2 root fix) · **`lorerunes` minted** (the ruled home for shared code — repo
  CLAUDE.md). ⚠ Sweep #2 first recorded 11-i-a as "unmerged" from the STALE table row while Log
  + git said merged — corrected same day; re-derive state from git, not from a row.
- **The committed-RED era is OVER — the suite is fully green at HEAD.** 03b discharged
  global mypy-zero (36 → 0, all members); suite **6937/0** at the 03b close; post-11-i-merge
  honest baseline **7065 passed / 1 failed**, and that single failure (`test_retired_symbols`
  on three archived reports naming a retired brief-publish constant — main's own, named in
  `receipts/2026-07-24-packet11i/FIXWAVE-CLOSEOUT.md`) was **CLOSED by this sweep's banner
  fix** (`a7e6ea9`, scoped 16/16). ruff clean; skill suite 117 (03b close receipts).
- **Findings ledger after this sweep: every PRE-SWEEP row (≤ #235) is resolved or
  acknowledged**, with its destination packet in the ack note AND written into the packet
  file itself. Rows filed DURING the sweep by the live WIP sessions (#236+) stay with their
  sessions to route at close-out. ⚠ Convention (packet-01 precedent, restated so no entry
  check false-STOPs): a packet entry check reading "`lore_findings` → #N open" means
  NOT-RESOLVED (open OR acknowledged); acknowledged = routed, still owed.
- Deployed: **lore-lore on image `65e36c8` (packet 05a-ii's deploy, 2026-08-10; git `5466b7b`;
  rollback `pre-05aii-rollback`=`a04a23ca`).** Ships **`await` LIVE** (the served bounded-wait
  action) + the 05a-i consume-path (drain `since=`/#183/#190/DD-2.a waiting line) + the defect-class
  prevention instruments + scout's 8-clone DRY consolidation. Live-leg SMOKE PASS (served snapshot +
  honest-empty + WAKE 21.7s). ⚠ The recreate triggered a one-time full lore-tier re-embed (~94 min,
  832 files) via the boot self-heal on a store↔manifest count drift — root-caused, filed **#355**
  (fix → follow-up); NOT recurring (a clean tier is live==expected). Everything below is INHERITED
  from the prior deploy:
- Prior deploy: **lore-lore on image `a04a23ca` (packet 05a-iii's deploy, 2026-08-08 — the FIRST 05a
  deploy; rollback `pre-05aiii-rollback`=`9debdd34`).** It ships LIVE the 04b-3/04b4/04b5 commit-only
  backlog + #321, plus 05a-iii (story · rollup messages/fleet/skew · #304 age-the-declaration ·
  comms_cli) and a **tini PID-1 init** (ENTRYPOINT — fixes bare-python-as-PID-1: signal-forwarding +
  zombie-reaping, the wedged-conmon class hit this session). serverInfo
  `pkt03b-tainted-corpus-526-g45a09cc`; `/proc/1/comm`=tini; smoke GREEN (story/rollup/fleet live).
  ⚠ **"BOTH containers" is lore-lore ONLY** — `lore-demand_intelligence` is a separate long-dead
  project (untouched); and the running lore-lore was actually on the hand-rolled **pkt03b** image
  (#165/#166), NOT the `e91e37b9`/`a6a4e5a2` this record implied — drift unreconciled (see #336). The
  detail below describes an ANCESTOR image's contents, all INHERITED by `a04a23ca`:
  superseding `b46bc1d5`. It carries: the entropy catch-all DELETION with the #235 fix (the
  before/after receipt was captured from the RUNNING production container), `SecretStr` end
  to end + ONE resolver, `lorerunes`, **and the 11-i security fix wave (#210/#207/#211) —
  the prior "commit-only, not yet deployed" warning is DISCHARGED.** Suite at 42's close:
  **7980/0**, typecheck 0 across all members, smoke all-PASS. Also live from the previous
  image and re-verified: 10-d's disarm (`cosine_floor.state="disabled"` with the honest
  note) and #147's traces. The deploy gates itself (artifact + workspace-honesty probes —
  packet 01); `lore_index()` serves the real branch/ref.
  **11-i-a's dark machinery is IN this image** (merged `c7983e8` before 42's merge base) —
  deployed but UNSERVED by design: serving untouched until 11-ii, and 11-ii MUST inherit
  audit R2 (the slice has zero production consumers, so the store law is satisfied only
  vacuously — wire the writer WITH its `ensure_ready`). ⚠ Still commit-only: only the docs
  commits after `915b7b8`.
  15-tool surface; cosine substrate live; the 0.50649 floor constant is RETIRED FROM
  SERVING (10-d disarm; #161's re-measure rides 11-i, cutover + constant retirement 11-ii).
  P7→P8d′, SLATE S1–S7, the closure wave, PKT-06/C0, PKT-28 C1, the #102 retry-substrate
  chain, packets 01, 01a, 02, 02a, 03, 03a-1/03a-2, **03b** and **10-d** all CLOSED.
  Hashes are as-of-verification snapshots; the authoritative deployment check is always
  RELATIVE (protocol, Boot 4).
- Standing eval bar: **35-pair set, pinned claude-sonnet-4-5-20250929, client metrics**
  (accuracy ≥33/35 · tokens-per-correct ≈1375-era · taxed-calls ≈0). 11-pair calls-leg
  retired. Last receipts: 33/35 · 6.46 calls · 1440.8 tok (2026-07-07).
- Test store: spike-surreal ws://127.0.0.1:18000; production store :18500 — NEVER
  pointed at by tests. Both systemd/quadlet-managed, auto-start on boot.
- **ENGINE: SurrealDB 3.2.4 on BOTH stores** (migrated off 3.1.5 → 3.2.1 on 2026-07-22,
  then carried to 3.2.4 by the quadlets' FLOATING `v3.2` tag; measured host-side 2026-08-08
  — #336, store-ref header). ⚠ `v3.2` is NOT patch-pinned, so any recreate/pull drifts the
  version silently; pinning it is an open infra decision on #336. Receipts in the store
  reference §0 (ff7128e): prod byte-identical (174,161 rows / 20 tables), full suite
  behaviour-identical across engines, #107 re-probed, SDK 2.0.0 unchanged. Probed facts KEEP
  their per-version provenance labels — re-probe on contact.
  Sole rollback: the verified 3.1.5 backup at /backups/lore/surreal-pre-3.2.1-20260721
  (RocksDB format is forward-only). New static vendor tiers indexed (`surrealdb-docs`,
  `surrealql-tests` @ v3.2.0 tag) — corpus now 2764 files by design.
  Substrate: **#167 RESOLVED 2026-07-22** by a verified fingerprint reconcile (all
  17,287 chunks proven non-null + cosine 1.000000 vs fresh re-embeds on all three
  tiers; measured safe-stamp with rollback recorded; restart clean, no re-trigger).
  The durable fixes are the **#171 ruled design → packets 11a/11b** (⊃ #168/#169,
  adopts #170; certified at scale in 24). The stale-floor tail is handled by the 10-d
  disarm (DEPLOYED) + 11-i re-measure (WIP) + 11-ii cutover; traces are LIVE (#147
  closed, 0→664 production rows) with retention owed by 06 (#193). Spectron docs added
  as static tier `spectron-docs` 2026-07-23 (+143 files atop the 2764).

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
**Operator-ruled order (2026-07-14, local-first; wave D inserted 2026-08-02, resequenced
2026-08-03 — auth to the end), numbered as it runs:** 01 ledger triage → 02–06 comms
completion (wave C) → **45–56 the D&D-extension track (wave D: 45 allowlist → 46
extension wiring → 47 ingest-seam DESIGN → 47a ingest-seam BUILD → 55 scraper transmute [∥-safe] → 50 contract-prep →
51–53 the dnd extension → 54 LOCAL deploy + operator soak → 48/49 principals+keys → 39
[pulled from wave S] → 07/07a [pulled from wave L] → 56 GO-LIVE)** → 08–17 remaining
local correctness
(wave L: results-impacting / LLM-impeding bugs) → 18–22 DI local = **v1.0 SHIP at 22**,
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
| 04a | **comms `ENFORCED` sweep + #105** — `briefed` flip (`OVERWRITE`), the app-level unknown-agent check (the ONLY layer that can teach), `publish(agent_id)` hardening, the `test_brief_ledger.py` agent-seeding fix (D1) | PKT-28 C2c | C | 0.20 | 03 | **✅ DONE 2026-07-27, TEST-ONLY + schema — NOT DEPLOYED (04b carries it).** Suite **7137/0** (EXIT=0, unpiped), typecheck OK ×3 (156 files), ruff clean; contract 50 pins, 0 failed. Cold audit **GO**, 5 defects — all natural-language/instrument, 3 fixed in-wave. #105 **RESOLVED for `to`+`briefed`** (open for `refers`/`answers_to` → 43). Adversary killed **4 wrong builds that survived 38/38**, incl. one GREENER than correct. Findings filed: #236 #239 #240 #243 #244 #245 #246 #247 #248. Ten reports archived → `receipts/2026-07-27-packet04a/`. |
| 04b | ~~comms surface (single packet)~~ **→SPLIT at kickoff 2026-07-28** into 04b-1 / 04b-2 — four operator rulings at that kickoff (optional `agent`/`session` on the three ledger tools · #247 closed HERE · `blocks` `ENFORCED`+app-precheck · directive = `acked_at IS NONE`) put it past the 0.30 threshold. ⚠ Its "**DEPLOYS BOTH** / carries 04a's schema" clause is **VOID**: 04a's code rode packet 42's image and its `briefed` flip is **LIVE in the production store**, verified read-only at this kickoff. | PKT-28 C2c | C | →split | 04a | **superseded by the two rows below** |
| 04b-1 | **task DAG + the sender guard** — `blocks` edge (`ENFORCED` from birth), `create_task` → transactional, mirror from `blocked_by`, the generalised blocker-existence pre-check, edge≡`blocked_by` + acyclicity + the `+collect` transitive read, **R11's legacy backfill**, **#247** sender guard, **#253**, 04a residuals R-1/R-2 | PKT-28 C2c | C | 0.30 | 04a | **✅ DONE 2026-07-29, TEST-ONLY + schema — NOT DEPLOYED (04b-2 carries it).** Full suite **8256/0** (EXIT=0, auditor-run; builder's 8237 + r6's 19 pins reconciles exactly), typecheck ×5 members, ruff clean. Contract **247 + 240 pins, 0 failed**. Cold audit **GO**, 1 confirmed defect (#275, contract prose) fixed in-wave. **FOUR adversary passes**; the 3rd and 4th each found MORE survivors of ONE class → operator **accepted the bound (#274)**, quantified by the audit as **2 of 4 doors** with a ~40-line derived instrument already written (**#276** → 04b-2). Sidecar S3 (the legacy-edge world deploys itself) was found only under the NEW trust definition. Findings: #253 #257–#276 filed; #257 #258 #259 #264 #266 #267 #269 #271 #272 #275 resolved/acked. 18 reports archived → `receipts/2026-07-28-packet04b1/`. |
| 04b-2 | **comms surface** — blocked-chain/critical-path render, fleet unread + unacked-directive columns (`acked_at IS NONE`, `grade='directive'`), `_comms_footer` + optional `agent`/`session` on the three ledger tools + `_INSTRUCTIONS`, **#219** (4 prose sites), 04a residuals R-5/R-12; from 04b-1's close: #274/#276, #273, ESC-1, capped-listing, S1-a; **sweep 2026-07-29 adds close-out items** #253-verify #260 #263 #268 #277 (file §SWEEP ADDITIONS) — **plus #279, and ⚠ READ THE `INHERITED FROM 04b-1` TABLE in the packet section: TEN rows it OWNS, none in the original Scope IN, each naming where its reasoning lives. #274/#276's cure is already BUILT (`scripts/forgery_door_sweep.py`) — ADOPT, do not re-derive; ESC-5 is an ENTRY CONDITION; S1-a lands WITH-or-BEFORE the new columns** | PKT-28 C2c | C | 0.25 — **SIZING FENCE ruled**: non-deploy-critical extras split to a minted 04b-3, never stretch the session | 04b-1 | **✅ DONE + DEPLOYED 2026-08-03.** C1+C3 shipped the dispatcher pending-traffic footer, optional `agent`/`session` identity (link 1b/4), MP-6, `_INSTRUCTIONS`, and minted `lore_tasks action=get`. C3 **225/0**; C-DEF fixture gap closed + non-vacuity proven; B3 attribution leak DOCUMENTED+LEDGERED (#321, bound pinned) → full Link-5 fix → 04b-3, operator ACCEPTED for the LOCAL threat model. Cold audit **GO** at `60f83f0` (225/1759/677, currency PASS, zero RED_ORPHANED). 15 findings resolved; #304/#309/#310/#319/#321/#322/#324 → 04b-3. 21 reports → `receipts/2026-08-01-packet04b2-wavec/`. **DEPLOYED on image `a6a4e5a2`** (bakes audited code, `git diff` vs `60f83f0` = 0): fresh backup `lore-prod-20260803T141930Z.surql` (3.63 GB, 22 tables) → recreate → R11 backfill minted **51** blocks-edges against prod (no error) → smoke GREEN (`action=get` teaches, `_INSTRUCTIONS` pending-traffic surface served, 15 tools). Rollback image `pre-04b2-20260803` (=`e91e37b9`). Prod now `a6a4e5a2`. |
| 04b-3 | **comms residue — MINTED 2026-08-01 by the 04b-2 design ruling (B1 level 3).** Each row carries its own decision point, per the deferral law: **#273 + #272** (`networkx.simple_cycles` replacing a MEASURED NON-DEFECT hand-roll, ONE edit — it moves networkx from test-oracle to production import, changing both the dependency group and the mypy-override scope, and it becomes a production IMAGE dep; trigger = 04b-3 kickoff or any earlier wave touching `loremaster.tasks`) · **ESC-1's MECHANISM** — ⚠ **NO LONGER CONDITIONAL: measured YES on 2026-08-01** (58 PASS / 0 FAIL, counts DERIVED, three consecutive green runs on fresh spike-surreal throwaway DBs, discriminating negative control, tree provenance printed; receipt `receipts/2026-08-01-agent-comms-fix/REPORT-probe-esc1-closure-1.md`). The ancestor closure IS persisted at write time, so the **ledger-independent write-path cycle read is ACHIEVABLE**: 04b-3 BUILDS it, and per ESC-1's own clause the known-bound pin becomes a **defect report DELETED WITH THE FIX**, not a bound to keep. Residue enumerated and expected: batch-local `create_many` siblings (no row exists pre-commit) and legacy phantoms (skip recorded at WARNING). Two facts for its builder, already measured — **no ledger verb mutates `blocked_by` after birth** (so the constructed verbs are the COMPLETE column-writing surface), and **a cycle member's edge closure contains ITSELF** (`truncated=False`), making self-reachability the usable cycle signal on the edge read · **CA-11** (write-time cycle-guard TOCTOU vs a concurrent racer — real, correctly characterised, closing it is a contract change) · **CA-12** (the cycle-graph read has no supporting index; trigger = first measured claim/cycle-read latency, or ledger growth past the dependency-bearing population) · plus anything 04b-2's SIZING FENCE ejects, recorded in its close-out with a receipt | — | C | ~0.20 | 04b-2 | **✅ DONE 2026-08-04 — CYCLE only** (Fable split → 04b4 SERVED / 04b5 INJECTION / #304→05a; CA-11 + CA-12 DEFERRED, named triggers). ESC-1 bounded-closure read + #273/#272 networkx swap; the from-minted guard reformulation was RETRACTED (variant D keeps the shared `find_blocked_by_cycle` + `_drop_one_cycle_edge`). Contract → adversary (**trilemma INSUFFICIENT → variant D**, retracts §CYCLE-FORKS) → build → cold-audit **GO** @ `496a95e` (FORK-A refuted by construction). Currency **PASS** (ruff GREEN; typecheck/pytest RED_ADJUDICATED→pkt39; zero orphaned) after a fix-wave `6fa1177` (3 probes routed through `_surreal_harness`; harness count 47→48; + 04b-2's 12 orphans folded in per operator). 213+240 green, ESC-1/MP-1 exit 0, 20/20 concurrency. **COMMIT-ONLY** (rides 05a). Reports → `receipts/2026-08-04-packet04b3/`. #326/#328/#329 resolved; #330 filed (lore-surreal restart). |
| 04b4 | **SERVED — comms served-surface + invariant hardening** (MINTED 2026-08-04 by Fable's 04b-3 decomposition): #319 served-desc derivation + sweep · #309 no-limit display cap · #310 validate-before-transform → repo invariant · #322 ∀ fixture invariant · #324 R-2/R-3/R-4 dispatcher hardening. Rulings: `receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md` §D | — | C | ~0.20 | 04b-2 | **✅ DONE 2026-08-05 — TEST+PROD, COMMIT-ONLY (rides 05a's deploy, unbuilt).** Entry-check caught #310's concrete already shipped (`0ff05ed`) → operator ruled **class-instrument only** (PIN-THE-MISS). Contract (6 RED/35 GREEN) → adversary **INSUFFICIENT** (P6 corpse `test_an_UNLIMITED_render…NO_line` contradicted #309 = a C-DEF trap for any cap<40) → fix (retire corpse + PIN-THE-MISS the #319 class bound) → adversary **delta SUFFICIENT** (trap gone cap 10&50; PIN-THE-MISS discriminates). Build greened 6 RED: #309 no-limit `query` display cap=50 + counted-elision via **shared render_line** (K DERIVED len−shown, no count(), cap at RENDER only, ruling A), #319 `note` desc names `acknowledge`, #324 R-4 `name`/`to` keyword-required +3 sites; #310 class=PIN-THE-MISS, #322 ∀ dispatch-fixture + #324 R-2/R-3 GREEN. Cold audit **GO** @ `0255901` (blast radius task/finding/comms **0-failed**, ZERO new mypy, discrimination live, byte-exact restore; lead receipt test_comms_footer 245/0 + render-hunk judgment read). Commits `3091610`→`37d4adc`→`0255901`; 9 reports → `receipts/2026-08-05-packet04b4/`. Filed **#332** (§D-#304 STALE-badge premise false → 05a), **#333** (branch typecheck RED: 191 mypy + 316 pytest, ALL pre-existing auth WIP pkt 39/45/48/49, 04b4 zero-new, operator-accepted). LOW residual: PIN-THE-MISS keys on `_derived_strict_to_action_matrix` (optional hardening; trigger = a required-for closure via a separate derivation). |
| 04b5 | **INJECTION — #321 Link-5 render-site containment** (MINTED 2026-08-04): the derived charset/render partition + a new `render_attributed` seam (**EXTRACT `sanitise.fence_width` from `render_fenced` FIRST** — it does not exist yet) + a reach-checked runtime sweep; all-or-nothing, property-to-invent (own author attacks own design). Rulings: same report §B. ⚠ **HARD PRECONDITION of packet 56 go-live** (dnd's player-reachable `lore_findings` makes the vector agent-reachable). | — | C | ~0.20 | 04b-2 | **✅ DONE 2026-08-05 — TEST+PROD code, COMMIT-ONLY (rides 05a's deploy).** Property-to-invent: `render_attributed`/`fence_width` seam; FULL-derived door routing (49 error + ~40 renders + `memory.text` fenced + search.py full route-through + 18 self-echo bare-`ValueError` + 2 `.format()` doors), reach enforced by name-blind AST scans (error-half + widened to `.format()`) + P-U/P-F/P-S render nets (coverage.py branch-obs, operator-ruled over settrace). Pipeline: contract (5 authors, 2 API-death recoveries from checkpoints) → **Fable design sidecar** (two-waves tripwire on render-reach) → build → **Opus-4.8 recheck** (caught a fabricated §SAT; operator ruled the build's green-contract gate discharges #133) → cold audit **GO** (0 leaks / 12 hostile shapes, mutation-proven non-vacuous, f-string-embed byte-safety proven by construction). Two operator all-or-nothing extensions: self-echo doors + the **`.format()` reach blind spot** (a real completeness gap the recheck AND cold audit both missed — they tested routed sites, not the net's interpolation-mechanism coverage; exposed the live caller_model door). Gates: contract **256/0**, ruff clean tree-wide, currency **PASS** (zero RED_ORPHANED; typecheck/pytest RED_ADJUDICATED→pkt39), full-suite failures **ALL auth-WIP** (#333; 04b5 zero-new). Commits `4c5930d`→`6ff51cf` (10); 18 reports → `receipts/2026-08-05-packet04b5/`. #321 + #335 resolved; impact.py:819 ratified B-5 OUT. ⚠ **DEPLOYS before pkt 56** (#321 re-open trigger). |
| 05 | comms-await-story — **SPLIT RULED 2026-07-29 (sizing directive)**: 05a wait-surface (await/story/rollup/CLI + DD-2.a/DD-4.c/R1 + #183 #190 #214 #304 [latched input_required, re-homed from 04b-3]; deploys) / 05b verbs+hooks (#89 #174 **#256 #262** + idle-gate v2 #121 #149 + #195 settle) — see file §SPLIT | PKT-28 C3 | C | ~0.30 + ~0.20 (two sessions) | 04b-2 | **05a-iii ✅ DONE+DEPLOYED 2026-08-08** (image `a04a23ca`, lore-lore, +tini PID-1 init; first 05a deploy — ships 04b-3/04b4/04b5 backlog + #321 LIVE; #304/#332 resolved). **05a-i ✅ DONE 2026-08-09** (commit-only, rides 05a-ii's deploy; `53e28fc`; #336/#342/#343 resolved; a Fable-ruled D2 reversal fixed two live #321 render injection leaks). **05a-ii ✅ DONE+DEPLOYED 2026-08-10** (image `65e36c8`/git `5466b7b`; the `await` verb — standalone `InboxAwaiter`, PEEK/no-stamp, ≤55s fixed const, agent-id-only LIVE-WHERE, DD-2.a waiting-line consumer, R-3 `action=drain` render; scout's 8 SDK-await-boundary clones DRY'd onto one `store._txn` constant; cold-audit GO; live-leg SMOKE PASS — served snapshot + honest-empty + WAKE 21.7s; #354 connect-guard fixed, #355 self-heal defect filed). **05b ✅ DONE+DEPLOYED 2026-08-11** (image `3ded8244`, lore-lore; git `3c68ca6`; rollback `pre-05b-rollback`=`65e36c8`). LIVE served: #256 `annotate` + #262 register liveness notice + #174 supersede `blocked_by`; idle-gate v2 (#149) local hook `a52576f`. Boot = delta reconcile (13 files, NO #355 hang); live SMOKE PASS all 3 served surfaces. #89 struck (04b-2), #121 preserved, #195→06; #356 re-anchor / coordination packet / report-graph→28a minted forward (cite the DRY issue). brief-base v12 + lead-base v5 landed. Commits `a52576f`/`c0071cd`/`e69c45a`/`3c68ca6`; reports `receipts/2026-08-11-packet05b/`. |
| 06 | comms-protocol-drill — **→SPLIT at kickoff 2026-08-11** (sizing ≥0.30 + the #360 scope expansion): 06a build enablers (DEPLOYS) / 06b the drill + measurements + close wave C; **three operator rulings at kickoff** (see §KICKOFF in the packet file). Lead `lead-06`. | PKT-28 C4 | C | →split | 05 | **superseded by the two rows below** |
| 06a | **comms served-surface honesty + #195 obedience battery + #257 floor + brief-base v13** — W1 fleet-render: `declared_cadence` field + `cadence` register/heartbeat param (payoff-stating desc, R1) + the `overdue (declared, silent)` verdict + **RETIRE ⚠STALE** (#360/#259b — sweep BOTH `_heartbeat_is_stale` callers: `_render_comms_fleet_row` + the #262 held-task note); W2 #195 battery (O1 misdirected-send / O2 ack-scope graders + positive-control/differently-broken controls; §15 adversary) in `comms_consumer_eval.py`; W3 #257 MINIMAL floor at `brief_publish` (token ≥3 · `is_blank` DROPPED per F-DRY · no pin); W4 brief-base **v13** (C-1 #228 / C-2 write-side artifact-contract / C-3 comms-protocol / C-4 #195 teaching rule; lead-applied). Design: `design/2026-08-11-packet06-drill-and-obedience.md` §A/§B.7/§C. Ledger `f582f0ad`. | — | C | ~0.20 | 05 | **✅ DONE + DEPLOYED 2026-08-12** (image `2c87e7b0`, lore-lore; rollback `pre-06a`=`3ded8244`; commits W2 `f9b5f2b` / W1+W3 `495e9d9`). Both workstreams contract→adversary→build→cold-audit **GO** (obedience 3 fix waves / 3 deltas → SUFFICIENT; honesty 1 adversary fix wave + a post-build contract-fix wave; 9/9 wrong builds discriminate; the new cadence free-text door CONTAINED via `render_attributed`). Served-surface **SMOKE PASS** via `lore_comms` (⚠STALE GONE on 7d/14d/30h agents; live `overdue (declared ≤1m, silent 2m)` echoing the agent's OWN cadence, F-ECHO; #257 floor rejects a 2-token brief with the served teaching error; register-cadence round-trips on the populated store). ⚠ The recreate hit a **#355 re-embed** (**865 files re-embedded, ~3h — 03:56→06:56 UTC**; code+schema went LIVE before the indexer, so comms was correct throughout — the MCP is offline only during boot). brief-base **v13** landed; #362 filed (blast-radius grep gap). |
| 06b | **THE DRILL + measurements + trace-GC + close wave C** — live drill (`lead-06`+`drill-worker-06`+`drill-prober-06`) coordinating solely through lore; join-quality receipt (DD-5.b, first-minute), decay curve → **forced-drain decision on the MEASURED curve** (not the prediction), loss-rate read (DD-4.d; re-open >0.5% or any confirmed lost directive), trace-GC (#193/DD-1.c — 90d, reconcile-tick, never boot, AFTER the curve is read). Receipts §B.6. **Wave C closes here.** Ledger `fe6e5f8a` (blocked_by 06a). | — | C | ~0.15 | 06a | **✅ DONE + DEPLOYED 2026-08-12 (trace-GC image `4320f9ae`; git `c245394`; rollback `pre-06b`=`2c87e7b0`; fast delta boot, no #355 re-embed).** THE DRILL (acceptance gate) PASSED live — 11-step arc solely through lore; **orphan → `overdue (declared ≤2m, silent 6m)` render, NO ⚠STALE**; zero-content-SendMessage proven (both drill agents 0 SendMessage); all §B.6 receipts. #195 LIVE: battery **gate PASS 3/3** + population (Fable task-10 = harness artifact #364; obedience held ∀ 3 models) + live in-fleet injection resisted. Measurements (14d prod trace): join **1:many**, **loss 0.20%** (<0.5%), **forced-drain = keep pull, no compeller** (05b5cd71 done). Trace-GC #193/DD-1.c: 90d, **E1=Reading Y** (id-batched periodic-tick purge, never boot; `DELETE…LIMIT` is a 3.2.4 parse error), Fork-A caller reach pinned; contract→adversary(INSUFFICIENT on Fork-A only)→build→cold-audit **GO** (18-pin, 1229 no-reg, zero-new mypy). #363–#366 filed; #193/#360 resolved. **WAVE C CLOSES — comms subsystem complete + acceptance-passed.** Reports → `receipts/2026-08-12-packet06b/`. |
| 57 | **task-coordination substrate** — `assign` verb + `assignee` field (distinct from claim-only `owner`) + a `reap` verb + the ownership↔liveness reconciliation surface (task-anchored query showing owner last-seen / STALE / retired, reusing the extracted `_heartbeat_is_stale`); auto-release on `retired` ONLY, never STALE. Dissolves #262's root (leads assign, agents claim) + closes the orphan/reaping gap (#357). ⚠ DESIGN packet — roster law. Design: `design/2026-08-11-task-coordination-substrate.md`; forks 2 (assign soft/hard) / 3 (owner→registry resolve) / 4 (auto-release policy) / 6 (reap verb) ruled at kickoff | — | C/L | ~0.25 | 05b | open — **MINTED 2026-08-11** (05b close-out, operator ruling) |
| 58 | **supersede RE-ANCHORS dependents (#356)** — on supersede(X→X'), rewire each dependent Y `blocked_by` X→X' via `direct_dependents`+`_relate_fragment`+`_refuse_a_cycle` + append a provenance note recording the original source; atomic (~3N txn → a HUB-supersede bound). ⚠ **CITES THE DRY ISSUE (operator-required):** extract a TASK-side guarded-append shell (tasks hand-roll it 3× vs findings' `_guarded_append_fragment`, #256), and the cross-module findings+tasks unify → home `loremaster.store` is a RELATED SEPARATE DRY item. `treat-superseded-terminal` REJECTED. Own contract→adversary→build. Design: `design/2026-08-11-task-coordination-substrate.md` §ADDENDUM A-174 | — | L | ~0.20 | 05b (#174) | open — **MINTED 2026-08-11** (the re-anchor-with-note the operator chose over refuse-and-teach; recall `lore_recall("#356 re-anchor")`) |
| 45 | **tool allowlist** (= multi-user proposal Part 2; resolves **#296**, gates `lore-dnd`; served prose becomes a function of the enabled set; collision-guard universe fix) | — | **D** | 0.30 (one packet, ⅓ reserve) | wave C done | **✅ DONE + DEPLOYED 2026-08-13** (image **`40ba206d`**, lore-lore; git `5467316`; rollback `pre-45-rollback`=`4320f9ae`). ONE packet (operator ruling); Fable design sidecar; 3 forks ruled (config-authorable IDENTITY preamble default=exact string→pkt54; empty enabled set legal, boot-fail only if TOTAL surface empty; one packet). Pipeline: contract **30 pins** → adversary **INSUFFICIENT** (E2 didn't prove cross-ref exhaustiveness — the QUANTIFIER law, 18/24 cross-refs unexercised) → revise **MP-1** (derived cross-ref coverage pin, 24 cross-refs) → delta-adversary **SUFFICIENT** → build **GREEN** (30/30, 1646 scoped `-n auto`, ruff, typecheck green-delta vs #333, **4 mutation proofs**, `build_instructions(ALL)` **byte-exact**==original 3374) → cold audit **GO, 0 defects** (all gates re-run, reduced lore-dnd surface coherent 0 disabled tokens). **#296 RESOLVED with a production receipt**: baked scoped suite **1646/1646 in the deployed image** (provenance-gated, incl. `TestDisabledToolIsUncallableOnTheWire`). Delta boot, **no #355 re-embed**; `lore_index()` serves git 5467316. Reduced-surface NL bounds → **#370** (pkt54); subagent-observability lesson → **#369**. Reports → `receipts/2026-08-13-packet45/`. |
| 46 | **extension discovery wiring** (`extensions:` in lore.yaml → `register_extension`; unknown name fails boot LOUDLY) | — | D | 0.15 | 45 | **✅ DONE 2026-08-14 — COMMIT-ONLY, NO DEPLOY** (dark until 54; `EXTENSION_REGISTRY` ships `{}`). `_discover_extensions` in `LoreServer.__init__` (all 4 prod sites route through it): full-key loop → registry lookup → instantiate → `register_extension`; unknown key fails boot LOUDLY (teaching error naming the `sorted(registry)`-derived known set, no leak); key≠name guard; packet-39 **R14 rider PAID** (ext tools `readOnlyHint=False`). Pipeline contract(9)→adversary **INSUFFICIENT** (∀-config-keys pinned at N=1)→revise(+2, **11 pins**)→delta-adversary **SUFFICIENT**→build (11 GREEN by IMPL, contract untouched, 4 mutation proofs both-way)→cold-audit **GO**. Both Trust legs live-verified (real derived known-set; empty-registry+named-ext fails LOUD, no false clear); DUAL preserved incl. the discovery-UNREACHABLE missing-slice branch kept manually pinned; store touch NONE. Fable sidecar ruled the test-migration fork (`minimal_config` default→`{}`; Cat A/B/C; caught +3 files the census missed). Gates zero-new-delta vs #333 (currency PASS, 0 RED_ORPHANED). **#371** filed (2 adversarial-only contract bounds, receding-reach STOP-rule). Commits `543ed72`+`89852b3`; reports → `receipts/2026-08-14-packet46/`. |
| 47 | **twelfth seam: ingest entity-fragment — DESIGN** (the property-to-invent: seam shape, transactionality, the two-phase ENFORCED edge lifecycle) — ⚠ DESIGN packet, roster law | — | D | 0.15 | 46 | **✅ DESIGN DONE 2026-08-14 — COMMIT-ONLY, NO DEPLOY (split → 47a for build)**. Ruled design `docs/design/2026-08-14-packet47-ingest-entity-seam-design.md` (12th `Extension` seam: `claims`/`entity_fragment`/`entity_purge_fragment`/`resolve_edges`/`ingest_backends`, composed into the per-file `store.apply` txn; two-phase ENFORCED edges; `write_stack_readied` ordering rail; fake-domain fixture). Pipeline: Fable design sidecar → **independent Opus-4.8 adversary** on the finished doc (**SHIP-WITH-FIXES, 8 findings ALL folded**, code facts re-verified live; F1 cross-book-scope corruption gap + F3 Indexer-unwired-for-`claims()` the headliners) → Fable r2 → operator rulings. **Rulings:** SPLIT · transactionality **Reading B** (entity+manifest atomicity, witness=manifest INDEXED row — the pre-transmute "chunk rolled back" pin is unrepresentable since claimed files skip chunking) · phase-2 edge resolution **FULL-SWEEP-ONLY** (incremental watcher = pinned non-feature → dissolves adversary F1 by construction & is the edition-supersession enforcement point). **Companion RULED doc** `docs/design/2026-08-14-edition-precedence-mechanism.md` (A1+B1+C1+distinct-nodes: lore-side `book_precedence` total order; **no scraper change**; consumed by 51/52b/50/53/55). Store touch NONE. Commit `26d2bde`; reports → `receipts/2026-08-14-packet47/`. |
| 47a | **twelfth seam — BUILD** (implement the ruled 47 design: contract → contract-adversary → build → cold audit; store-touching — typed entity records + RELATE edges + fake-domain DDL in the per-file txn) | — | D | 0.32–0.38 | 47 | **✅ DONE 2026-08-15 — COMMIT-ONLY, NO DEPLOY (dark until 52a/52b).** Pipeline (Opus 4.8 end-to-end): contract **40 pins** → contract-adversary **INSUFFICIENT** (3 C-DEFs RED-on-a-correct-build: P6 `pytest.raises` vs §Q2.3 fault-isolation, P13 no entity-table channel, P20 unlabeled `resolve_edges`; + a missing framework-atomicity ∀-pin; + P8 reach gap) → consolidated revision r2 → **delta-adversary SUFFICIENT** (40/40 on an 8-file reference build; every fix + new pin broken by a wrong build) → build **GREEN** `91fc30e` → cold REFUTE audit **GO** (40/40 ×5, #107 dirty-store ENFORCED-migration probe, 6 mutation proofs, 964 regression green). Operator-APPROVED seam additions **DG1** (`IngestBackend.entity_tables()` → `delete_by_tier` sink co-purge) + **DG2** (`resolve_edges → list[ResolvedScope]` + `IndexSummary.scopes_failed`); **DG3** hook = `index_all`+`rebuild_all`+`reconcile` union via one `_resolve_all_extension_edges`. **HARDENING** `06b7142` (operator-ruled cold-audit residuals): R2 loud fail-fast guard (`ready_claiming_extension` — a claim against an unready domain RAISES, converting silent SCHEMALESS auto-create corruption to a loud stop; Fable-ruled sink placement, compose-only) + R1 register-wiring pin (**#376**) + R3 served-docs seam count. Gates zero-new-delta vs #333. Residual bounds: **#375** (cli/scout full ingest lifecycle → packet-51 re-open trigger), #373/#374/#377/#378. Commits `562c9bd`(RED)+`91fc30e`(GREEN)+`06b7142`(harden); reports → `receipts/2026-08-15-packet47a/`. **52a's node-fragment ingest depends on this.** |
| 55 | **scraper TRANSMUTE build** — the machine tier (`output-graph/**/*.jsonl`): HTML cache + one full re-crawl, LLM transcriber under deterministic word-for-word fidelity gates + the corpus A/B oracles; Agent SDK on the Max subscription (transcribe-craig pattern; refuses a set API key). Executes in dndlorescraper per its `SPEC-transmute.md`; tracked here — 52a/52b entry checks name its outputs. STEP 1 = the one-page link probe | — | D | ~0.25 | — (∥-safe with 45–47) | open |
| 50 | **dnd CONTRACT-PREP** — the design is RULED (`docs/design/2026-08-03-wave-d-architecture.md` + the transmute pivot); this packet contracts 51/52a/52b/53, runs the contract-adversary on each (standing law), and rules the kickoff forks (proposal §9 3/5/7/8 + D3 + the read-the-2024-rules edition rider) | — | D | 0.15 | 47; 55 receipts | open |
| 51 | **dnd schema slice + domain store** (every edge ENFORCED + UNIQUE(in,out) + `source_book` scope from birth; scalars as indexed fields; graph-probe scripts → `scripts/`) | — | D | 0.25 | 50 ruled | open |
| 52 | **dnd extension builds: 52a machine-tier reader** (JSONL → pydantic mirror of the transmute `records` module → node fragments via the 47 seam; tombstones ingest as named bounds) **/ 52b edge resolution** — THE SUPERSESSION FUNCTION (prefer 5.5 → the 59-row rename alias → 5.0 → dangling tombstone; the reference's own edition is IGNORED — cross-edition correctness by construction; D2-pair + rename-row + per-item dangling instruments). Per-dialect grammar work GONE (transmute pivot) | — | D | ≤0.25 each | 50, 51 | open |
| 53 | **dnd domain tools** — rules retrieval + general graph FILTERS, client-side composition (NO per-mechanic composed tools); both trust legs per served surface | — | D | 0.20 | 50, 51, 52 | open |
| 54 | **deploy `lore-dnd` LOCALLY** — LAN-only local MCP connection, NO auth; operator soak (ruled 2026-08-03: the identity tail 48/49/39/07/07a moved AFTER this); ruled allowlist + two static roots (prose `output/` + machine `output-graph/`); quadlet always-on | — | D | 0.15 | 53 | open — **DEPLOYS the new instance (LAN-only)** |
| 48 | **principals substrate** — `build_store(config)` extraction FIRST (3-way copy today), then the `principal` table (never `user`) | — | D | 0.20–0.25 | 45 (∥ 46/47) | open |
| 49 | **principal CLI (1B) + per-user API keys (1C)** — 39 §4's mint, never odoo-code's; hashed keys; revocation beats cache | — | D | 0.25 | 48 | open — DEPLOYS (CLI in image) |
| 59 | **migrate MCP server → standalone `fastmcp` 3.x** (swap the server façade off `mcp.server.fastmcp` → `fastmcp>=3.4,<4`; KEEP `mcp` for `mcp.types`; `TracingFastMCP.call_tool` subclass → `on_call_tool` middleware; `streamable_http_app()` → `http_app()`; **DELETE ~150 LOC lifespan apparatus** (`_ProcessLifespanGuard`+`_EagerStartupLifespan`, spike-gated) obviated by fastmcp's once-per-process `lifespan=`; enable `host_origin_protection` — closes a today-open Host/DNS-rebinding gap; delivers the middleware substrate packet 39's enforcement is authored on — design §7). **RESOLVES #184 re-open trigger (b)** (2nd non-telemetry `call_tool` consumer; #102 shared-substrate). ⚠ #131/#139 class: acceptance REQUIRES the in-image conformance run (01a) + a real uvicorn wire smoke; INFERRED payoffs (lifespan DELETE, Origin ordering) gated on a migration spike (design §6.6). Design: `docs/design/2026-08-15-fastmcp-3x-migration.md` | — | D | 0.25–0.30 →split if ≥0.30 | — (independent; only `server.py` + deps) — **MUST precede 39** | ✅ **DONE + DEPLOYED (STANDALONE) 2026-08-16 — live-verified.** Commit `130fa16` (image `a8daccf` `:latest`, rollback `pre-59-rollback`; lore-lore recreated w/ `LORE_ALLOWED_HOSTS=*`, `lore_index` round-trips + trace middleware recording). Cycle: spike (3 §6.6 GO) → contract (2 adversary passes; **①-OC ACCEPT**) → build → Phase-7 (cold GO + security GO + **blindread caught the transport_session correlator + coldaudit the transport-mode gap — wire behaviours every green gate missed**) → fix-wave → lead re-verify **450f/9859p zero-new-delta**. in-image conformance PASSED (provenance clean; +37 image-vs-host all benign source-scan artifacts). Findings **#381** (F1, fixed) · **#382** (conformance harness) · **#383** (index 5000-stmt cap); **#184 resolved**. Conformance-harness fix `24c1863`. Reports → `receipts/2026-08-16-packet59/`. (was IMMEDIATE NEXT BUILD, D2.) MINTED 2026-08-15 (author `migration-author`). RULED: **D1 STANDALONE deploy** (rebuild+recreate + in-image gate); **D4 `mcp` TRANSITIVE** (replace the `mcp[cli]` dep with `fastmcp>=3.4,<4` — full umbrella, NOT `fastmcp-slim`; 2 build-time caveats: bare-`mcp`-no-`[cli]`, `mcp.types` undeclared-but-accepted); **D3 39's `Depends on` gains `59`** (lead edits 39's row on commit). Grounds: `receipts/2026-08-15-fastmcp-migration/` (blast-radius+§7, spike GO, 4.0-scout, handroll-inventory) + `lore_recall("fastmcp migration")`. |
| 39 | hosted-security (design first; REQUIRED before off-LAN) — **PULLED FORWARD to wave D (operator, 2026-08-02): #296 is ANSWERED by packet 45's allowlist; the contract is RE-CUT against the principal substrate (48/49 replace R12's roster file — the standing Log override) and the revision gets a FRESH adversary pass (standing law)** | PKT-21 | **D** (was S) | 0.30 →split | 45, 48, 49, 59 | **DESIGN RULED + CONTRACT WRITTEN; was BLOCKED on #296 — now UNBLOCKED by 45.** Design `docs/design/2026-07-31-packet39-google-oauth.md` (R1–R16, twelve+ rulings). Contract **480 pins / 444 RED / 36 GREEN**, rest of suite **7705 passed / 0 failed**, ruff clean; satisfiability re-discharged 0-failed on every revision. **FOUR adversary passes, all INSUFFICIENT**, each finding a real blocker every prior gate passed — one root cause (`_setup_handlers` binds at construction ⇒ post-construction installs are live in-process, DEAD ON THE WIRE): WB30 `call_tool` → WB48 guard *after* the tool body → WB93 instance attr on `list_tools` → WB100 **class** attr (flaky-green 5/10). **Build never started, deliberately.** #296's answer is scoped in `docs/design/2026-08-01-multi-user-lore-proposal.md` §2. Filed #291 #294 #295 #296. Receipts → `receipts/2026-07-31-packet39/`. Operator-side and untouched: hades SNI route · claude.ai client secret · the posture flip. **#295 STRUCTURAL LEG FOLDED IN HERE (operator, 2026-08-09):** the "a refused tool is not dispatchable — gate REGISTRATION/VISIBILITY, not INVOCATION, so there is no 'after' to place a guard in" answer (this packet's own WB30→WB100 root cause; entangles #296 + the #333 auth WIP) is OWNED BY THIS PACKET. The 2026-08-09 defect-class session builds only #295's auth-independent "observe-the-EFFECT-not-the-exception/marker" pin-invariant, and only if the designer rules it cleanly separable from auth. |
| 07 | store-error-honesty: CLASSIFICATION (#118, #119, #144 — the #124 rediagnosis) — **pulled into wave D (operator, 2026-08-02): precedes 56 go-live (renumbered 2026-08-03)** | PKT-30 | **D** (was L ∥) | 0.20 | — | **✅ DONE 2026-08-17 — TEST-ONLY, NO DEPLOY** (#118/#119 already fixed at `8f24e11` 2026-07-13, live-verified GREEN on 3.2.4, no builder needed; #144's posture settled via a two-leg mutation-proven test guard; #124 pulled in mid-packet by operator ruling and closed with a derived DDL-coverage pin). Commit `147be46`. Cold audit **GO** (independent re-derivation of every claim, incl. its own F0 mutation attack). Zero changes under `loremaster/loremaster/` — deploy skipped as a genuine no-op (nothing new to serve), same precedent as 02a/03a-1/03a-2. #118/#119/#144/#124 resolved. Reports → `receipts/2026-08-17-packet07/`. |
| 07a | store-error-honesty: RECOVERY + DEGRADATION (#164 reconnect-on-bounce + **#250 its PRODUCTION reproduction**, #128; #126/#127 adjudication) — **pulled into wave D (operator, 2026-08-02): outside users must never meet #164** | — | **D** (was L ∥) | 0.20 | 07 rec. (same seam) | **✅ DONE 2026-08-17 — DEPLOYED.** #164/#250's "wedges forever" premise did NOT reproduce at HEAD (live 20-consecutive full-bounce drill, self-heals every time; both transport-fault branches independently guarded + mutation-proven) — operator ruled FORK A = A1 (adjudicate, no new reconnect code; named re-open trigger = packet 16). #128 FIXED (`43c4ab3`): per-item degradation on contention/store-error, distinct ruled wording. #126/#127 RENEWED (latent, triggers not fired; #127 gained a mutation-proven tripwire). Cold audit caught a real defect: the ruling doc's initial root-cause line contradicted its own correction — fixed. #164/#250/#128 resolved; #126/#127 annotated. Findings #384 (140 pre-existing unrelated test failures, surfaced not chased), #385 (latent two-source classification duplication, moot unless a future A2 ships) filed for the record. Reports → `receipts/2026-08-17-packet07a/`. |
| 56 | **`lore-dnd` GO-LIVE** — auth wired (39 posture, 49 keys), hades exposure (operator-side verify), **#236/#138 consult MANDATORY before exposure**, findings write-gating note; smoke: principal → key → Moon-Druid trace via claude.ai → revoked key denied live | — | D (tail) | 0.15 | 54 soak, 49, 39, 07a | open — **DEPLOYS (exposure)** |
| 08 | astroid-shadow (#24; containerfile roles → 37) | PKT-08 | L ∥ | 0.15 | — | open |
| 09 | surface-residues — **SPLIT RULED 2026-07-29 (sizing directive)**: 09a served-surface + docs truth (#15 #64 #80 #82 #84–#86 #88 #92 #197 #208) / 09b testing hygiene (#230 #231 #244) — see file header | PKT-03 | L ∥ | ~0.20 + ~0.15 (two sessions) | — | open |
| 10 | floor-calibration-design (#83, #87, #161, #179) | PKT-01 | L | 0.15 | — | **design DONE 2026-07-24; F3 → client consult** |
| 10-d | **weak-match DISARM** (#176/#179/#180 — confidence surfaces dark NOW; trust doctrine, Addendum E1) | — | L | 0.05 | — (independent) | **✅ DONE + DEPLOYED 2026-07-26** (built/audited/merged `be4c591` 2026-07-24; deploy RODE 03b's — both containers on `b46bc1d5`). Live receipt from the running artifact: `lore_index()` serves `cosine_floor.state="disabled"` with the note naming #83/#176/#179/#180. ⚠ **The disarm MASKS #176/#179/#180, it does not FIX them** (`d7a1ce5`) — the per-instance calibration that resolves them is 11-i/11-ii; those findings stay OPEN. |
| 11-i | floor-calibration: DARK MACHINERY (engine + store + in-container runner + R2 lab validation; serving untouched, no deploy) | PKT-02 | L | 0.20 → split 11-i-a ~0.15 / 11-i-b ~0.24 | 10 ruled | **DESIGN RULED 2026-07-26** (23 decisions: RULINGS-2026-07-25.md; Addendum F-r2 §R1–R10; S1 measured NOT DEGENERATE). **11-i-a MERGED `c7983e8` 2026-07-27 (worktree removed; its dark machinery rides the deployed `e91e37b9` image UNSERVED — by design, serving untouched until 11-ii).** History: contract `d6c0dd4` (branch `pkt11-i-a-floor-machinery`) → adversary **INSUFFICIENT** (9 of 14 wrong builds survived at 143/0) → fix wave `e8aa8f4`: **186 collected**, satisfiability **186 / 925 / 561, all 0-failed** against a reference build, lead-verified. Deps adopted `38c9774`; **#198** consolidated `ea7406e`; **#238 closed** (`docs/eval` now gated, 190 tests). Rulings: `receipts/2026-07-26-packet11i-build/RULINGS-2026-07-26-{bootstrap,contract-11ia,adversary}.md`. contract `d6c0dd4` → adversary **INSUFFICIENT** (9/14 wrong builds survived) → fix wave `e8aa8f4` → build `7acbef4` → closure `0e99c1e` → **cold audit GO** `2b23862` (every predicted gate number reproduced exactly; freeze verified 22×) → audit fix wave `675aab5`. **Full suite 7571 passed / 0 failed**, lead-verified independently; typecheck 162 clean; ruff clean. Receipts + 3 RULINGS files: `receipts/2026-07-26-packet11i-build/`. ⚠ **OPEN, carried:** #241 (intermittent 2-of-114 contention STOP, mechanism unknown — 30 frozen runs green but on a DIFFERENT tree; instrument `scripts/contention_hunt.sh`) · #242 (connection-glue duplication; a naive extraction blinds the enumeration covering it) · 4 dangling `REPORT-*.md` citations pre-dating this packet, one of them in the store reference (#157's population). ⚠ **11-ii MUST INHERIT (audit R2):** the slice has ZERO production consumers, so the store law is satisfied only VACUOUSLY — wiring a writer without its `ensure_ready` gives an undeclared-table conflict storm, and for `lease` an undeclared-table READ THAT RAISES. **11-i-b not started** · task ledger row `1586bbc0` (claimed at kickoff) |
| 11-i-a-r | floor-calibration: THE STORE CARVE-OUT (the measurement-row columns 11-i-a never shipped + the corpus-growth classifier + the `adopt=True` guard) | PKT-02 | L | 0.03–0.04 | 11-i-a merged | **MINTED 2026-07-28 by operator ruling** — carved out of 11-i-b because the work pushing b over the ≥0.30 clause is exactly the work crossing the a/b ownership line. Sequence **a-r → b contract → b build**; b re-prices to ~0.28–0.29 whole, in its Q4.1 character. Scope: (a) the RULING-REQUIRED columns (R-C `batch`, R-G `scipy_version`/`numpy_version`, `B`/`N`/`method`, `k_prime`, bars tuple, gate triples, F2 null-rate + applied gap, sensitivity floor, degeneracy telemetry, per-group results, run cost, C9/C13 drop diagnostics, C11 manifest) as B4 `OVERWRITE` additions with per-key write→read→present pins; (b) the CONSUMER-NAMED data from the 2026-07-28 consult (`CONSULT-SYNTHESIS-11ib.md` §3 — ten items, **none in the shipped 14 columns**); (c) FU1.2's corpus-growth classifier; (d) FU1.3's `adopt=True` guard, landing BEFORE b's contract so the contract is written against the refusal. ⚠ **Ruling R-G is premised on the row "already carrying `B`, `N`, `method`" — verified FALSE by importing the module**; a ruling resting on an unchecked premise is why neither the scout nor the sidecar's authors caught the gap earlier. ⚠ **ONE ESCALATION, not a column**: Opus's U1 — the re-measure branch has NO threshold (a whole-corpus digest changes on a one-character edit, so a scheduler is either "skip" or "re-measure everything, constantly"); design fork, operator's. `DEPLOY: no`. Ledger row `6e09610b`. **Packet doc: `11-i-a-r-store-carveout.md`.** ⚠ **U1 is RULED A MEASUREMENT, not a design fork** (operator 2026-07-28): the re-measure threshold is DERIVED from a floor-vs-deviation sensitivity curve, never invented — this packet records the corpus-delta MAGNITUDE datum that makes the curve measurable, and 11-i-b's R2 run is its first instrument. The `shown` semantics are a DESIGNER decision, routed to the sidecar. |
| 11-ii | floor-calibration: CUTOVER (chokepoint wiring + serving swap + retirement sweep; resolves #83/#87/#161/#179) | PKT-02 | L | 0.15 | 11-i landed | open |
| 42 | **PREVENT THE LEAK, DELETE THE SANITIZER** — `SecretStr` everywhere + ONE resolver + a typed auth-header seam, then DELETE the entropy catch-all. Kills audit R2 (12.4% of function names erased from tracebacks), #227 and both its accepted bounds. | — | L | 0.20 →0.55 | — (independent) | **✅ DONE + DEPLOYED 2026-07-28** (`915b7b8`; image `e91e37b9`). Suite **7980/0**, typecheck 0 across **five** members, ruff, smoke all-PASS. Contract 11 revisions, adversary **SUFFICIENT after 5 passes**, 43 rulings. **12 defects green at every gate**, incl. a live production leak (#235), an instrument testing a COPY of its own gate, and 4 scanners silently narrowed. Mints **`lorerunes`** (4th member, the home for shared code). #222 #226 #227 #233 #235 #251 closed. |
| 43 | **DERIVATION-SOURCE UNIFICATION** (design pass FIRST) — `_derive_nodes` reads the caller's chunk set while `_derive_edges` re-reads the file fresh; a save between them makes the fragment RELATE from a node it never created. **Then** the `refers`/`answers_to` `ENFORCED` flip, which was blocked ONLY on this. + #248 `_bare_id` ONE-IMPLEMENTATION (separable at kickoff) | — | L | 0.20 | — (independent) | **open — minted 2026-07-26** (operator ruled the ROOT fix over the two local patches). Split out of 04; store facts already measured on 3.2.1 — do NOT re-probe. **DESIGN problem → Opus author who attacks its own design, never a builder.** |
| 44 | **UNGATED GROUND** — every committed instrument rides a gate: #261 docs/eval typecheck strategy + #270 markdown-it-py adoption + tool gating; sibling sweep by DERIVATION, never a list | — | L ∥ | 0.15 | — (independent) | **✅ DONE 2026-07-30, MERGED `02b0142` (ff, 29 commits) — NOT DEPLOYED (gates + tooling only).** Suite **8711/0** (36 skip, 3 xfail, reconciled to collected), typecheck **EXIT=0 across 8 legs**, ruff clean — identical pre- and post-merge. **#188 CLOSED**: 41 believed → 45 bare → **24 real** → **0**; `scripts` is now a plain typecheck root (`MYPYPATH`-scoped). `docs/eval` (the production deploy smoke) type-gated, 6 p8a relics archived; `skills` +117 into testpaths; a DERIVED shellcheck leg (caught `typecheck.sh`'s own unguarded `cd`). Instrument `scripts/gated_ground.py` + 318 pins: per-axis (LEG A types / LEG B **collector-derived**), monotonicity **STRUCTURAL** not pinned. **THREE adversary passes** (11, 12, 6 survivors — each a different class, all prior closed) + cold audit **NO-GO on 2 blockers, both fixed**. Findings #188 #261 #270 #280–#283 resolved; **#284 #285 #286 #292 #293** filed. 15 reports → `receipts/2026-07-29-packet44/`. |
| 11a | embedding-reconciliation CONTRACT (#171 FULLY-RULED design ⊃ #168/#169, adopts #170) | — | L | 0.20 | — (design ruled) | open |
| 11b | embedding-reconciliation BUILD (reconciler + resolve extraction + #170 hash; `rebuild_all` retires, hard-cutover rename) | — | L | 0.25 →split if 11a measures over | 11a ruled | open |
| 12 | detection-contract (#10, #11, #27; rides 11b's extracted resolve seam) | PKT-04 | L | 0.15 | 11b rec. | open |
| 13 | detection-build | PKT-05 | L | →split | 12 ruled | open |
| 14 | config-derive-excludes (#26, #28, #72 corpus pollution + #162 archive-twin dedup) | PKT-09a | L ∥ | 0.20 | — | open |
| 15 | config-boot-validation (+ dead fields, #12) | PKT-09b | L ∥ | 0.20 | — | open |
| 16 | surreal-ops-hardening (#109, #110, #113, #114, #116, #117; + #175 re-probe→reference, #249 RSS restart policy, #239 4.0-break→reference) | PKT-31 | L ∥ | 0.15 →**split guidance ruled 2026-07-29**: if over at kickoff, 16 keeps the ops six + #249; #175/#239 probe→reference work splits to 16b | #249's prod leg needs 07a first | open |
| 16a | package-seam-hardening (loresigil #205 split-math + #223 Retry-After; #209 watchdog fork bound+canary) | — | L ∥ | 0.15 | — | open — MINTED by the 2026-07-26 sweep (operator may strike/re-home at kickoff) |
| 17 | worktree-overlay-design (#125; delta-only RULED) | PKT-33 | L | 0.15 | — (#136 FIXED 2026-07-14) | open |
| 18 | ledger-retirement (singular-store ruling) | PKT-24 | M | 0.20 | — (before 20 finalizes, 22 ships) | open |
| 19 | **deploy-architecture DESIGN** (#166 one-toolchain ⊃ #165, #186 recurrence; partitions the old rework — #13, scaffold, verbs — into minted 19b+ builds ≤0.25 each) | PKT-11 | M | 0.15 | — (builds inherit 14/15) | open — REDESIGNATED 2026-07-22; urgency ↑ 2026-07-25 (#186: #165 recurred, 3 tiers) |
| 20 | migration-machinery (Shape D) | PKT-12 | M | 0.30 →split | §8 Q1–Q4 ruled at kickoff; 19; 18 | open |
| 21 | single-node-drills (§8.6 + watcher skip-path) | PKT-10a | M | 0.15 | — | open |
| 22 | di-migration + **v1.0 SHIP (single-node)** | PKT-13 | M | 0.25 | 19, 20, 18, GO/NO-GO | open |
| 23 | worktree-overlay-build (#125) | PKT-34 | O | 0.25 | 17 ruled; before 26 completes | open |
| 24 | odoo-scale-certification (MRO/ORM assessment defines 25) | PKT-27 | O ∥ | 0.30 →split | 13 rec.; v1.0 | open |
| 25 | odoo-onboarding-design (XML extractor, MRO capture, tiers, cutover) | PKT-32 | O | 0.15 | 24 receipts | open |
| 26 | odoo-onboarding-build (26a, 26b, … minted by 25) | PKT-35+ | O | ≤0.25 each | 25 ruled | open |
| 27 | cross-tier-compare (Odoo 15→19 prep) | PKT-18 | O ∥ | 0.25 | v1.0 | open |
| 28 | graph-search-v11 (#3, #70, #155, #252, #254 + #233's count-line render residual; + #20/#37/#40/#41 candidates) | PKT-17 | F | 0.35 →split | v1.0 | open |
| 28a | report/thread serving (#163 ⊃ #160 — section-aware chronological threads + report graph) — **DESIGN RULED 2026-08-11 (Consumer-Law-first):** a `report` graph SPINE that POINTS at the already-embedded `.md` chunks (no re-embed); `report→task/agent/finding` ENFORCED edges + the payoff `report→symbol` edge resolved against the code-graph name-table → a "reports" section in `lore_impact`; #160 label in `lore_search` = cheap early slice; only net-new = a markdown citation-extractor. `design/2026-08-11-report-graph.md` (5 forks) | — | F ∥ | 0.25 | 14 (#162 first); v1.0 | open |
| 29 | loresage package | PKT-14 | F | 0.25 | v1.0 | open |
| 30 | enrichment-worker | PKT-15 | F | 0.30 →split | 29 | open |
| 31 | detectors-escalation (raise_issue) | PKT-16 | F ∥ | 0.25 | v1.0 | open |
| 32 | memory-maintenance (decay/expiry sweeps) | PKT-19 | F ∥ | 0.15 | v1.0 | open |
| 33 | memory-reconciler (det. tier + loresage tier) | PKT-25 | F | 0.35 →split | v1.0; 29 for LLM tier | open |
| 34 | summary-reuse (5b, promoted) | PKT-26 | F | 0.25 | 29; 35 helpful | open |
| 35 | trace-deepening + trace_monitor backstop (gates S+G) | PKT-20 | F LAST | 0.30 →split | v1.0 | open |
| 36 | role-wiring (all\|mcp\|scout + creds; regains role verbs from 19; #206 session-binding fix) | PKT-07 | S | 0.30 →split | — | open |
| 37 | containerfile-roles + image slimming | PKT-08b | S | 0.20 | 36 | open |
| 38 | split-topology-e2e | PKT-10b | S | 0.20 | 36, 37 | open |
*(packet 39's row moved into the wave-D block above — pulled forward 2026-08-02; number and history unchanged.)*
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
    ToolSearch can't resolve lore tools. ⚠ **"INTERMITTENT" IS WRONG AND WAS THE REASON IT STAYED
    UNROOTED — ROOTED 2026-07-30 by packet 44 (#292, supersedes #287).** It is perfectly
    DETERMINISTIC, 8/8 in one session, split by AGENT TYPE: a definition with an explicit `tools:`
    allowlist (`tdd-contract`, `contract-adversary`) gets NO `mcp__lore_lore__*` tools; one granted
    `Tools: *` (`general-purpose`) gets them. Zero exceptions. **`ToolSearch` is necessary but NOT
    sufficient** — `tdd-contract.md` already grants it, above a comment asserting it is "the gateway
    to deferred MCP tools … see lore finding #266", and that comment is FALSE: the MCP surface must
    itself be in the grant. So #266 was diagnosed, fixed, documented and **never verified**; the
    first measurement happened in packet 44. Fix the grants, then VERIFY (the step #266 skipped),
    and fix or delete the false comment. Every untested type — `tdd-implementer`/`-stub`/
    `-refactorer`, `tdd-light-contract`, `Explore`, `Plan`, `package-scout` — is UNMEASURED, not
    assumed clear.
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
22. **#154 + #157 + #218 — legacy citation debt** (dead SPEC paths + 51 dangling report
    names + 116 line-number cites in the test tree; **#218 added 2026-07-26**: a RENAME
    breaks a symbol citation exactly as an edit breaks a line citation — the citation law
    names no rename mitigation; adjudicate together). Recurrence is CLOSED by the archive
    law; the legacy tail is inert. Decision point: wave-L kickoff — one hygiene mini-packet,
    or accept-with-trigger. ⚠ The named decision point has ARRIVED (wave L is running:
    10/10-d/11-i/42) — the fork is now DUE.
23. **#156 + #200 + #224 — the process-instrument DESIGN cluster (extended 2026-07-26):**
    #156, exemption evidence is unexecutable — every allowlist can carry a false
    justification forever ("no assertion can read English"); both adversaries blessed a
    false one by inspection. #200, nothing distinguishes operator-RULED from
    author-ASSERTED once a claim is restated — a phantom prohibition drove a whole lease
    design (twice in one packet). #224, the count/population class has no instrument —
    three instances in ONE session, with the law already in CLAUDE.md. All three are
    properties to INVENT (executable exemption evidence · provenance-of-authority marking ·
    a count-scope instrument) — per roster law they need an Opus design pass that attacks
    its own design, not a builder; one design packet could carry all three. Operator
    schedules.
24. ~~**Message id form (03a-1 residual):** `uuid4().hex` vs `ulid()`~~ — **RULED (operator,
    2026-07-23): use `ULID`.** Time-sortable for a future pkt-05 `since=` cursor; pre-deployment, so
    no records to migrate. Implemented `13da377`: `message.id = str(ULID())` (python-ulid 4.0.1,
    client-side mint, dep on `loremaster/pyproject.toml`), aligning with the contract's stated
    `bare ulid` intent. Verified: bareness pin green both legs, full file 140/31/9 unchanged, ruff
    clean, mypy +0.
25. **#242 — the connection-glue extraction (DESIGN, needs an owner; filed 2026-07-27 by
    11-i-a, escalated rather than built):** consolidating the connect/bootstrap/close copies
    is NOT a refactor — a naive extraction drops every owner out of the retry-seam gate's AST
    discovery, and the gate goes green while covering nothing (#120 pointed at its own
    instrument). The extraction ships WITH a redesigned discovery mechanism — the
    discovered-owner count a CHECKED variable against an independently derived list — design
    first, or not at all. ⚠ The glue-copy COUNT is deliberately UN-DERIVED (the row's first
    number was withdrawn as a three-population conflation; its correction note is the
    reference) — whoever owns this derives it first. Operator schedules.

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
  **⚠ SECOND INSTANCE: #241** (2026-07-27, 11-i-a head mint — 2-of-114 contention failure,
  28 tests failing together, evidence AGAIN destroyed by a tail-only capture; instrument
  `scripts/contention_hunt.sh` exists, carried in the 11-i row). The class is live.
- **#236 — pre-existing dangling-edge cleanup DEFERRED (operator, 2026-07-26: localhost-only).**
  `ENFORCED` guards future writes; existing ghosts are untouched, and calling the problem
  closed is a false all-clear. Named trigger: the FIRST non-local deployment — packets 38/39
  MUST consult #236 (with #138). Ghost count UNMEASURED; any number before the sweep is a rumour.
- **#239 — SurrealDB 4.0 UPGRADE BREAK** (deterministic edge ids on RELATE: silent overwrite
  today, hard error on 4.0 — verified via release-note #349, 04a probe P3). Reference landing
  rides packet 16. Trigger: BEFORE any 4.x adoption, sweep every RELATE site for deterministic
  ids.
- **#265 — ONE drain TIMEOUT under concurrent load** (then succeeded; the caller could only
  route around). Single occurrence — watch, do not build. Trigger: a SECOND occurrence routes
  it to 07a's transient-classification seam, with the FULL output preserved (#159's rule).
- **#184 — fastmcp standalone migration REFUSED for 03b** (telemetry rides a
  `TracingFastMCP.call_tool` subclass override). Accepted with a named re-open trigger: an
  mcp/fastmcp upgrade breaking that seam, or packet 35's trace work. Ledger task
  `b3fd31cb` is the tracking row.
- **#202 — `_txn.retry_on_conflict` is the hand-roll pattern's third instance (tenacity)**
  — raised for the record, deliberately NOT churned (the seam is mutation-proven and
  stable); re-open trigger named in the finding. Adjacent receipt: #207 consolidated the
  five OTHER backoffs onto `tenacity.wait_random_exponential`, leaving `_txn` the one
  fenced hand-roll.
- ⚠ **#185 LANDMINE — `scratch_copy.sh` does NOT git-isolate a copy made FROM A WORKTREE**
  (the copied `.git` FILE points at the real worktree; git commands in the copy mutate its
  metadata while the Python provenance assertion passes). Worktrees are banned for lore
  work anyway (above), which bounds the exposure; packet 17 dispositions the fix. Until
  then: NEVER scratch-copy from a worktree.
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
- 2026-07-27 · **11-i-a BUILT, AUDITED GO, MERGED** (`c7983e8`, pushed). Store half of the floor
  machinery: schema + head mint + `StoreLease` (`kubernetes.leaderelection` + a SurrealDB lock
  adapter) + the C8 projection. **Post-merge 7642 passed / 0 failed**, and the count RECONCILES
  EXACTLY — merge-base 7066 + ours 505 + main's 71 — so the merge lost nothing. Baseline taken from
  main at `0d06122` *immediately* before merging (7137/0). **THE ADVERSARY EARNED THE PACKET:**
  contract graded **INSUFFICIENT**, 9 of 14 wrong builds surviving at 143/0, and it found THREE
  defects in the RULED DESIGN's own wording — including a lock that **could never be created on a
  virgin store**, caught with two differently-broken controls because one would have licensed the
  wrong fix. Operator ruled **orjson** for the identity encodings, which DISSOLVED escalation E1
  rather than answering it (the ambiguity was manufactured by the bespoke encoding). #198 consolidated
  to ONE implementation in an installed package — four sites, not the two the finding named, found by
  sweeping from the grep against the lead's own hand-list; #238 closed. **NEW LAW, all learned the
  hard way: a fixture that writes its legacy row AFTER the migration cannot see the DEFAULT hazard at
  all** (the fix wave caught this in its own probe, inside the wave about prose contradicting code) ·
  **a clean auto-merge is not a correct one** — `_surreal_harness.py` merged without conflict and its
  derived counts were wrong on BOTH sides (42/26 is neither) · **deriving a served count beats
  correcting it**: F1's derivation absorbed main's new seams with no edit, which the merge was the
  first real test of. ⚠ **STILL OPEN:** **#241** (intermittent 2-of-114 contention STOP, mechanism
  unknown; 30 frozen runs green but on a DIFFERENT tree — instrument `scripts/contention_hunt.sh`) ·
  **#242** (connection-glue duplication, where a naive extraction blinds the enumeration covering it;
  its own count corrected as un-derived) · **#237**. ⚠ **11-ii MUST INHERIT:** the slice has ZERO
  production consumers, so the store law is satisfied only VACUOUSLY — wiring a writer without its
  `ensure_ready` gives an undeclared-table conflict storm, and for `lease` a READ THAT RAISES.
  **NO DEPLOY** (`DEPLOY: no`; nothing served changes). NEXT = **11-i-b**.
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
- 2026-07-26 · **04 KICKOFF — #105 RE-SCOPED BY OPERATOR RULING; the packet file was STALE.**
  Its #105 text said 03 shipped only a typed relation catching wrong-TABLE endpoints. Ground
  truth: 03 shipped `ENFORCED` on `to` (validates BOTH ends, guards the TABLE incl. `INSERT
  RELATION`) — so `send` was DONE, while `briefed`/`refers`/`answers_to` sat unguarded and the
  old text never named the last two. RULED: `ENFORCED` on all four (OVERWRITE — `IF NOT EXISTS`
  is the #107 no-op), app-check kept as the ergonomic layer; ghost CLEANUP out → **#236**
  (re-open = first non-local deploy). Operator-directed: §4's evidence is 3.1.5 and the stores
  are 3.2.1 — `ENFORCED` re-confirmed against the engine's executable spec @`v3.2.0`; P1–P4
  carried as required probes, P1 (does a dangling edge read as a ghost or `[]`?) decides the
  negative fixture and the 3.2 vendor docs still assert the reading §6.4 refuted.
- 2026-07-26 · **FINDINGS SWEEP + STATE REFRESH (operator-directed).** All 51 pre-sweep open rows
  → 0: #145/#172 RESOLVED (03b S2 pins landed; memory migration recorded); 49 acknowledged with
  destinations written INTO the packet files (04 +#219 · 05 +#174/#183/#190/#214, #195 fork settles
  at 05 kickoff · 06 +#193/#228 · 09 +#197/#208/#230/#231 · 11-i +#198/#201 · 16 +#175 · **16a
  MINTED** #205/#223/#209 · 17 +#185 · 19 +#186 · 28 +#233 · 36 +#206 (39 cites it) · 42
  +#221/#226/#235 · pool 22 +#218 (fork now DUE) · pool 23 = #156/#200/#224 design cluster · watch
  +#184/#202/#185). Acknowledged = routed; entry-check "open" = not-resolved. State of record
  refreshed (03b/10-d live on `b46bc1d5`; 11-i fix wave commit-only → rides 04/42's deploy); the
  suite's last red CLOSED (`a7e6ea9`, retired-symbols 16/16); 36's stale "14-tool" fixed;
  DESIGN-LAW verified current through §15. WIP (operator): 04 · 11-i build · 42 — ⚠ their
  mid-flight riders need a live-session ping. #236+ (filed during the sweep) stay with their sessions.
- 2026-07-26 · **04 SPLIT → 04a/04b, AND PACKET 43 MINTED (operator rulings, kickoff+discovery).**
  Discovery found two defects a builder would have inherited: the packet's `#105` scope was
  INVERTED (03 already shipped `ENFORCED` on `to`; the unguarded edges were `refers`/`answers_to`,
  which the text never named) and its transitive-read idiom was WRONG in both halves (P4:
  `@.{1..n}` is terminal-depth not the closure; `TIMEOUT` is a `SELECT` clause). Contract written
  (60 pins, 26 RED) then escalated TWO measured blockers: **D1** — `test_brief_ledger.py` never
  creates an `agent` table, so every `briefed` edge it writes is ALREADY dangling (≥29 reds on the
  flip); **D2** — `{edge.src} ⊆ {node.qualified_name}` holds for 56 modules + 8 adversarial shapes
  but is NOT STRUCTURAL. Operator ruled the ROOT fix → **packet 43**; 04a keeps `briefed` + the app
  check (P5b: `ENFORCED` CANNOT satisfy the Exit criterion — its message is withheld by the seam's
  error hygiene, so the app check is the only layer that can TEACH). Findings #236/#239/#240 +
  #243/#244/#245 filed; 197 probe-created databases reaped from the TEST store (814→617, delta
  exact). Ghost cleanup OUT (#236). NEXT = 04a build.
- 2026-07-27 · **04a DONE (TEST-ONLY + schema; 04b deploys).** Suite **7137/0** EXIT=0 · typecheck ×3
  · ruff · contract 50/0 · cold audit **GO**. **The adversary earned the packet:** 4 wrong builds
  survived 38/38 pins — incl. **W-D, GREENER repo-wide than correct (2077 vs 2073)** — all killed by
  7 added pins. Two stale-packet defects caught before a builder saw them: #105's scope was INVERTED
  (03 had already shipped `ENFORCED` on `to`; the unnamed edges were the unguarded ones) and the
  transitive-read idiom was WRONG in both halves (P4). Two more found by grading, not gates:
  `test_brief_ledger.py` had been writing dangling edges since it was written (its fixture never
  created an `agent` table), and D2's premise held for 56 modules but is NOT structural → operator
  ruled the ROOT fix → **packet 43 minted**. Cold audit's 5 defects were ALL natural-language, and
  its best find was **the same defect class inside `surrealdb-31-capabilities.md` itself** — §8
  teaching the claim §6.3 records as FALSE, in the file every store brief reads FIRST (`04da8bd`).
  #105 resolved for `to`+`briefed`. NEXT = **04b** (blocks/fleet/footer/#219; DEPLOYS BOTH, and will
  be first to ship the 11-i security wave).
- 2026-07-27 · **POST-04a: #246 BUILT+RUN, and a MEASURED memory leak on BOTH stores.**
  `scripts/zero_test_store.sh` shipped, then its FIRST real run found **three defects in ~40 lines**
  that syntax checks and a live guard test had passed: the guard keyed on a **substring of a name**
  (`pgrep -f` matched a sibling's watcher and its own checker — no pytest running), the success path
  **never verified its own effect** (restart+liveness pass just as happily over an untouched store),
  and it was a **footgun** — a fresh store bootstraps only `SURREAL_USER`, so zeroing destroyed the
  harness root user that had only ever existed because it was DEFINEd into the old store. That last
  one was **#246's own named unknown** ("whether anything depends on store persistence — the one
  thing that would break"): it was not a test, it was the credentials every test uses. Now
  self-healing; verified 61M→17K + full suite **7137/0** on a zeroed store. **#249** (supersedes
  #245): both stores grow to **20–25 GB RSS** with WORK and reclaim to **~695 MB** on restart —
  same baseline despite 43× different datasets; ~400 MB per suite run; **~44 GB reclaimed**.
  **#250**: the prod restart proved **#164 live** — lore-lore did NOT reconnect (2 calls, no heal),
  manual `podman restart` fixed it in 10s. **That blocks #249's only mitigation and promotes 07a
  from hygiene to enabling work.** NEXT = **04b**.

- 2026-07-28 · **PACKET 42 DONE + DEPLOYED** (`915b7b8`, image `e91e37b9`). The entropy catch-all is
  GONE — eight symbols, plus #227's path exemption, its four conditions and both accepted bounds.
  **The receipt, both halves, captured from the RUNNING production container:** before, it rendered
  `/tmp/ci/***REDACTED***/app.py`, `commit ***REDACTED***`, `in ***REDACTED***` — and
  `Authorization: ***REDACTED*** 8f3ka92mfLQ0zXvbNqRt`. After: the paths, SHAs and function names are
  INTACT and the credential is redacted. **Read that last pair twice — production was redacting the
  word `Token` and logging the credential** (#235), and had been for every non-Bearer scheme.
  Prevention replaced detection: `SecretStr` end to end · ONE resolver at the composition root
  (`dotenv_values(interpolate=False)` — the default rewrites `${…}` inside a secret and SHORTENS it
  on an unset var) · **`lorerunes`**, a 4th stdlib-only workspace member that is now the ruled home
  for shared code · typed auth-header seams + a gated `SecretStr` mint · per-request headers across
  all three counters · the unwrap allowlist 10→**6** (five entries were the SurrealDB *username*).
  **TWELVE defects were green at every gate**, and the number is the point: an attack corpus testing
  a **copy of its own gate** (13/13 passing with a leg deleted from the real one); **four scanners
  each holding a private root list** — #102 inside the instruments enforcing #102; a deploy guard
  blind to the member it guards; the #140 scratch guard blind to the same; `Digest` allowlisted by
  the fix itself, leaking its `response=` hash — a regression **we** introduced, caught only by the
  contract-blind reader. **R41 is the finding to remember: a mutation-proven pin was ABSENT FROM
  EVERY COMMIT** — unprotected across 5 contract revisions, 5 adversary passes, a builder, a refactor
  and 3 audits, because *a test that does not exist does not fail*. A Phase-7 auditor then
  rediscovered the identical defect from scratch, so we paid twice. **A mutation proof is evidence a
  pin WORKS, never that it SHIPPED.** Five of the lead's own rulings measured false; the registration
  count was wrong four times, which is why it is now DERIVED (`scripts/registration_sites.py`) rather
  than listed. NEXT = **04b**.
- 2026-07-27 · **FINDINGS SWEEP #2 (operator-directed re-check).** The 16 rows filed since the
  first sweep triaged; 7 open → 0: #237→11-i (convention-discriminating percentile pin) ·
  #239→16 + watch (4.0 RELATE-id break) · #247→04b kickoff (sender door) · #248→43 (`_bare_id`
  ONE-IMPLEMENTATION, separable) · #249→16 (RSS restart policy; BLOCKED by #250) · #250→07a
  (**#164 reproduced in production — 07a PROMOTED to enabling work**) · #236 accept-with-trigger
  (first non-local deploy; 38/39 consult). Frozen-ack rows homed in files: #244→09, #252→28,
  #242→pool 25 (extraction-design, needs owner); #233's 42-close leaves a count-line render
  residual in 28; #241 recorded as #159's SECOND instance (watch). State refreshed: deployed =
  `e91e37b9` (42; 11-i security wave DISCHARGED); 11-i-a ready-to-merge, unmerged worktree.
- 2026-07-27 · **CORRECTION (operator caught it): 11-i-a is MERGED, not "ready-to-merge".** The
  entry above and sweep #2's state text repeated the 11-i TABLE ROW, which was never flipped —
  while the Log's own `c7983e8` entry and git both said MERGED (all four build commits are
  ancestors of HEAD; worktree removed; the dark machinery is inside the deployed `e91e37b9`
  image, unserved by design). Also corrected: the branch HAS an upstream (pushed through
  `d5b6ad8`). Row + state block fixed. The lesson is the inherited-number law applied to STATE:
  a status cell is a claim someone wrote, git is the measurement — re-derive before repeating.
- 2026-07-28 · **04b KICKOFF → SPLIT into 04b-1 / 04b-2, on four operator rulings.** Ruled: optional
  `agent`/`session` on the three ledger tools (the footer was **NOT BUILDABLE** — they carry no caller
  identity, so *"traffic pends for YOU"* had no YOU; omitted ⇒ no footer, never a guess) · **#247 closed
  HERE**, not routed to 05 · `blocks` `ENFORCED` from birth **+** the app pre-check (a create naming a
  phantom blocker is now REFUSED where it silently made an unclaimable task — and the "no comms
  consumers" latitude does NOT cover `lore_tasks`) · directive = `acked_at IS NONE`. **Ground truth
  killed four premises:** 04a is **already DEPLOYED** (rode 42's image; its `briefed` flip verified LIVE
  in the *production store* — a migration nobody had checked, so "04b deploys both" is void) ·
  `create_task` is a bare `_query`, so "mirror inside the existing txn" was a no-op phrase ·
  `blocked_by` is fail-open at write · 04a mutation-proved ONE edge, not four. Also corrected in-file:
  the #105 table was stale AGAIN (`briefed` ✅ since 04a) in the paragraph warning about staleness, and
  "~17 return points" is **15**. #219 does **not** invert — an AST sweep of 187 prod files found ZERO
  inlined identities; it has 4 prose sites, not 2. NEXT = **04b-1**.
- 2026-07-28 · **#253 RULED INTO 04b-1 (operator).** `TaskLedger.query_tasks` issues `SELECT * FROM
  task` with **no WHERE and no LIMIT** and applies `status`/`owner`/`blocked` in a Python loop; the
  tool `limit` slices only after the whole ledger is materialised. Folded in rather than filed
  because 04b-1 already opens this ledger to mint `blocks` — plausibly the bounded blocker-resolution
  mechanism the fix wants. ⚠ **The obvious fix is WRONG, and the docstring already said so:**
  *"Blocker statuses are resolved against the full table so a blocker filtered OUT by the
  status/owner filter still counts"* — pushing the filters into the store naively mis-classifies the
  `blocked` partition, silently. Scope carries PROPERTIES, not a mechanism (a builder must not invent
  the general form), incl. the invariant the full read buys: the query partition can never disagree
  with the claim's server-side `array::len` CAS. ⚠ And the lead's own first framing was wrong — the
  unbounded read is `query_tasks`, **not** `_is_blocked`, a pure predicate that reads nothing;
  re-derived before filing, which is the only reason the right symbol is named.
- 2026-07-28 · **11-i-b KICKOFF + THE TRUST DOCTRINE GETS A HARD DEFINITION** (merged `c55792a`).
  Packet 11-i-b opened in a worktree on operator direction. Two landmines closed on entry: the
  worktree venv was **#140 poison mode 3** (`loremaster.__file__ = None`, zero workspace members —
  every test would have "passed" against no production code), and **#185 was MEASURED** (a scratch
  copy from a worktree resolves `--git-dir` to the REAL worktree while `--show-toplevel` reports the
  copy, so git writes mutate the real branch while the Python provenance assertion passes; mitigation
  both legs measured, in lore memory). Baseline pinned: 81 inherited RED, every group verdicted
  individually, **8029 passed in BOTH legs** — the equality is what made the attribution airtight.
  ⚠ The 81st was NOT a declared RED but a real 04b-1 defect (the harness docstring's DERIVED importer
  count stale at 43 vs 45) — **04b-1 has since fixed it**, confirmed by the post-merge diff.
  **Scout + Fable sidecar converged from opposite ends on ONE gap**: the shipped
  `FLOOR_MEASUREMENT_COLUMNS` is 14 names and ~12 the rulings require are ABSENT — re-derived by the
  lead by IMPORTING the module, which also showed **ruling R-G is premised on a FALSE fact** (the row
  "already carrying `B`, `N`, `method`"). Sizing reconciled to **~0.31** (Fable adjudicated the
  scout's six additions item-by-item and then said its own KEEP-WHOLE recommendation did not survive
  its own number) → **packet 11-i-a-r MINTED by operator ruling**.
  **THE CONSUMER CONSULT** (4 blind informants; battery designed by the sidecar, then **adversarially
  attacked BEFORE any informant ran — verdict INSUFFICIENT, 6 wrong packages scoring 5/5 identical to
  honest, five byte-identical on every graded surface**) returned the result that matters:
  **AGENTS TRUST WHAT THEY CAN CHECK.** Fable would delete ⅔ of the package's bytes but refuses the
  cross-artifact redundancy — *"why the verdict is CALL_AGAIN instead of 'trust me'"*; Opus's
  never-cut list is *the `n` on every rate*. Control worked: degraded → ROUTE_AROUND, honest/appendix
  → CALL_AGAIN. **Ten data the consumers named, none in the shipped columns** — sharpest is Opus's
  U1, that the re-measure branch has no threshold, which nobody on the authoring side found.
  **THE TRUST DOCTRINE NOW CARRIES A HARD, DECIDABLE DEFINITION** (CLAUDE.md, imported to this branch
  at `0acbf47`): *a response is trustworthy iff a consumer who acts on it WITHOUT CHECKING cannot be
  wrong in a way the response did not name.* Two legs — the scope diff (healthy path, design ≠ label)
  and constructed forgery pins (degraded path, runtime ≠ design) — because **each is blind exactly
  where the other is strong**, proven by putting each author's shape to the other: Opus conceded its
  procedure cannot catch #107 (step 1 is sourced from BELIEF; its own axis audit found *time*,
  *environment* and *predicate-as-EXECUTED* believed rather than known), Fable conceded its inventory's
  first form was forbidden-set shaped and DERIVED it instead, Sonnet conceded its bounding analogy was
  wrong and then found the hole in Opus's stopping rule nobody else saw. **All three conceded against
  themselves.** The lead's own proposed paragraph FAILED review 3/3 and does not ship — it was
  verification ergonomics, mislabelled "trust". Also killed: *"earning trust over time"* is not a
  strategy — reputation is not inherited across sessions, so it is won at BUILD time or not at all.
  ⚠ **The lead asserted one ranking it had not measured and the operator caught it** — right law,
  wrong object; measuring it inverted the conclusion. And **"Done" was claimed while the law sat on an
  unmerged branch no agent reads** — filing is not installing, twice in one hour, inside the law about
  exactly that. Receipts (16 files): `receipts/2026-07-28-packet11ib/`. NEXT = **11-i-a-r** (packet doc
  unwritten), then 11-i-b's contract.
- 2026-07-29 · **04b-1 DONE (TEST-ONLY + schema; 04b-2 deploys).** Suite **8256/0** EXIT=0 ·
  typecheck ×5 · ruff · contract **247+240, 0 failed** · cold audit **GO**. **The packet was
  SAVED BY A LAW THAT ARRIVED MID-SESSION:** the operator landed TRUST — THE HARD DEFINITION,
  and re-grading under its Leg 2 exposed **S3 — the legacy-edge world deploys itself**: the
  mirror is ∀ verbs FORWARD, so every pre-existing task would have served `ids=[] truncated=False`
  on live rows. It had passed a contract, an adversary, two fix waves and the lead. Ruling R11
  (backfill in `ensure_ready`) is the packet's reason for existing. **FOUR adversary passes**,
  each finding MORE survivors of one class (caps/doors/chunks) because the contract was
  **enumerating the FORBIDDEN set** — operator **accepted the bound (#274)**; the audit then
  quantified it (**2 of 4 doors**) and wrote the ~40-line derived instrument that closes it
  (**#276** → 04b-2). Also ruled: *a contract needs an ADVERSARY BEFORE A BUILDER* (`CLAUDE.md`),
  after r5 skipped one and two wrong builds got through. Dogfooding the deployed comms found four
  defects in its own surface (#257 brief body was literally `x`; #258 fleet 97% dead smoke agents,
  reaped 40→2; #259 `STALE` fires at 17m and at 391h identically; #262). Six agent definitions
  were MUTE (no `ToolSearch`) — fixed, and `brief-base` **v8** now makes every agent report what
  its brief demands but it cannot do. NEXT = **04b-2** (deploys BOTH; owns #274/#276, #273, ESC-1,
  the capped-listing false clear, and S1-a's fleet scoping WITH-or-BEFORE the new columns).
- 2026-07-29 · **FINDINGS SWEEP #3 (operator-directed, + the SIZING DIRECTIVE: packets KEEP the
  size goal — they always run over).** 14 open rows → 0: #253-verify/#260/#263/#268/#277 → 04b-2
  (file §SWEEP ADDITIONS; SIZING FENCE — non-deploy-critical extras split to a minted 04b-3) ·
  #274/#276 ack'd where 04b-1's close routed them · #254 → 28 · #255 → 11-i-b · #256/#262 → 05b ·
  #261/#270 → **44 MINTED** (ungated ground — the #188/#233/#238 class, derivation-swept) ·
  #265 → watch (2nd occurrence → 07a). **PRE-SPLITS RULED under the directive: 05 → 05a
  wait-surface / 05b verbs+hooks · 09 → 09a served-surface / 09b testing-hygiene · 16 split
  guidance (16b probes→reference) · 04b-2 fenced.** State: 04b-1 DONE 8256/0 TEST-ONLY; the
  deployed image is still `e91e37b9` — 04b-2 ships next and carries everything since.
- 2026-07-30 · **PACKET 44 DONE — UNGATED GROUND, merged `02b0142` (ff, 29 commits, NOT deployed).**
  Suite **8711/0** · typecheck **EXIT=0 across 8 legs** · ruff clean — identical pre- and post-merge.
  **#188 CLOSED and its number was the packet's own lesson: 41 believed → 45 bare → 24 real → 0.**
  21 of the 45 were import-resolution artifacts, the SAME illusion that made #261 look 6× its size
  — so `docs/eval` cost a `git mv` plus one leg-scoped `MYPYPATH`, not a cleanup. **Measure an
  ungated tree's debt WITH the leg's intended MYPYPATH, never bare** (memory saved). Landed:
  `docs/eval` (the PRODUCTION DEPLOY SMOKE) type-gated + 6 p8a relics archived · `skills` +117 into
  testpaths · a **DERIVED** shellcheck leg which on day one caught `typecheck.sh`'s OWN unguarded
  `cd` — the file whose header explains that a wrong cwd makes its output lie · `loresigil`
  discriminators → `Final[Literal[…]]` (invisible while `scripts/` was ungated; **the thesis
  producing a receipt on first application**) · `scripts/gated_ground.py` + 318 pins.
  **THE INSTRUMENT'S HISTORY IS THE FINDING.** Three adversary passes — 11, 12, then 6 survivors at
  a green contract — each a DIFFERENT class with every prior one closed. Pass 3's diagnosis stopped
  the loop: *the wave fixed the INSTANCES named, not the QUANTIFIER* (blindness pinned for 5 doors,
  holding 6/26; its dual unpinned, so a build serving `findings=1` + `is_clean=True` + a clean
  render passed all 171). That tripped the "same class survives TWO waves ⇒ escalate the DESIGN"
  rule → **R9: monotonicity by CONSTRUCTION** (`is_clean`/`exit_code`/`render()` DERIVED from
  `findings`+`blind_sources`, so an inconsistent verdict is UNREPRESENTABLE). Its author attacked
  its own design: 21 wrong builds, 6 survived, **4 were real missing pins in its own contract**.
  Cold audit then returned **NO-GO on two blockers, both inside the class the packet exists to
  close** — a CONSTRUCTED byte-identical false clear from the memo (an untracked `conftest.py` in a
  testpath ANCESTOR, loaded by a mechanism the docstring never reasoned about), and the headline
  invariant passing on a BLIND verdict. Both fixed; the second was closed AT THE SEAM (13 call
  sites), not at the two named — the fixer generalising where the audit had specified instances.
  **ROOTED EN ROUTE: the "intermittent" ToolSearch failure (open row 14) is DETERMINISTIC** — 8/8 by
  agent type; an explicit `tools:` allowlist gets no MCP tools, `Tools: *` does. `ToolSearch` is
  necessary but NOT sufficient, so **#266's fix was applied, documented with a comment asserting it
  worked, and never verified** (#292 supersedes #287). Filed: #284 (a `cp -a`/`scratch_copy.sh` of a
  WORKTREE inherits a `.git` FILE naming the original gitdir — a scratch `git add` MUTATES THE REAL
  TREE, silently) · #285 (**this repo has NO CI**, and packet 44's own Exit criterion was written
  against that phantom) · #286 · #292 · #293 (the peer instrument's deletion trigger has FIRED —
  frozen by operator ruling, edit recorded). 15 reports → `receipts/2026-07-29-packet44/`.
  ⚠ Worked in a git WORKTREE by operator override of the standing NO-WORKTREES directive (a peer
  session held the shared tree); #134 was N/A (no deploy), **#125 bit** — lore's index is blind to a
  worktree, so every structural answer came from `git grep`, said out loud in each report.
- 2026-07-31/08-01 · **packet 39 (Google OAuth) — design RULED, contract WRITTEN, build never
  started, BLOCKED on operator decision #296.** Investigation first: lore had **no** Google auth
  at all (not dormant — absent; `pricepaper` appears zero times). Ported odoo-code's *validation*
  shape, not its identity mint — that mints a constant `client_id` and discards the login it
  holds, collapsing every keyholder to one identity. **FOUR adversary passes, every one
  INSUFFICIENT, every one finding a blocker all prior gates passed**, and all four share ONE root
  cause: `FastMCP._setup_handlers` binds handlers at construction, so a post-construction install
  is live in-process and **dead on the wire** — WB30 (`call_tool`) → WB48 (guard ran *after* the
  tool body; refusal raised, effect not prevented) → WB93 (instance attr on `list_tools`, the route
  the prior fix had just made load-bearing) → WB100 (**class** attr; `vars(mcp)` clean, **flaky-green
  5/10 runs**). Two design escalations (R13, R16) both walked around. **Lead stopped at the fourth
  door by prior commitment rather than run a fifth round** — #296 is now the operator's fork, and
  its answer is scoped in `docs/design/2026-08-01-multi-user-lore-proposal.md` §2 (never REGISTER
  the tool: verified at SDK source that `list_tools`/`call_tool` both read `ToolManager._tools` at
  call time, so the class cannot recur). Final: **480 pins / 444 RED / 36 GREEN**, rest of suite
  **7705 passed / 0 failed**, ruff clean, satisfiability 0-failed on every revision. Filed **#291**
  (`_MUTATING_TOOLS` hand-list already drifted — would have left `lore_claim_task`/`lore_tasks`
  writable to remote principals) · **#294** (tdd-family agents lack the lore MCP tools —
  reproduced on **all four** agents; wants an agent-definition-family fix) · **#295** (a refusal
  pin that observes the EXCEPTION does not test that anything was PREVENTED; askable form: *"if the
  guard ran AFTER the thing it guards, would this pin still pass?"*) · **#296**. Operator override
  landed mid-flight: the user roster is **operational data, not deploy config** — mtime-watched file
  outside repo and image; the later request to store users in the DB is that ruling's own named
  re-open trigger firing, not an override. 7 reports → `receipts/2026-07-31-packet39/`. No
  worktree used. ⚠ Untouched by design, all operator-side: hades SNI route (the router also fronts
  Nextcloud, JupyterLab and odoo-code's live connector) · the claude.ai connector's client secret
  (GCP console only; Google has no DCR) · the posture flip (401s every local session unless key
  wiring ships atomically).
- 2026-08-01 · **D&D rules RAG — scoped, proposal WRITTEN, nothing ruled.** Operator asked for
  extend-vs-reuse proposals for a rules RAG over the dndlorescraper corpus (SurrealDB-native
  graph, multi-user, per-deploy tool allowlist). Three parallel read-only scouts (corpus /
  architecture reuse map / graph modelling, 6 live probes on spike-surreal 3.2.1) →
  `docs/design/2026-08-01-dnd-rules-rag-proposal.md` (`5b243ec`), reports archived at
  `receipts/2026-08-01-dnd-rag-scoping/`. Recommendation: **option C** — wire the
  complete-but-UNWIRED extension framework (0 production `register_extension` sites), D&D as its
  first real extension, second instance `lore-dnd` gated by the multi-user proposal's Part 2
  allowlist; the one new design item is the missing ingest entity-fragment seam ("twelfth seam").
  Corpus verified graph-ready (987/987 spell↔class edges from two independent sources agreeing).
  Ten forks in proposal §9; fork 10 (capabilities-doc additions) ruled + DONE at `b3ba703` — §2
  array-index `.*` rule + silent-`[]` trap · §4 "a traversal never uses a secondary index" ·
  §6.6 items 13–14 · §7 SDK string-id vs int-id row; the docs-first check caught the scout's
  "vendor-unwritten" claim on int-vs-string ids being FALSE (`record-ids.mdx` documents it) —
  correction header on the archived report. Session ended by host reboot; handoff state in
  `2026-08-01-dnd-rag-RESUME.md` (beside this INDEX). Forks 1–9 await the operator.
- 2026-08-01 · **AGENT COMMS FIXED — #294 + #292 resolved, superseded by #298. Packet 04b-2 NOT
  started.** Operator asked to fix agent comms first, then run the next comms packet, then went
  offline delegating design calls to Fable. Five probes settled the mechanism by EXECUTION: an
  agent's `tools:` block has **three** shapes, not the two #292 assumed — `*`/unrestricted and
  EXCLUSION lists (`Explore`/`Plan`, never broken, measured not assumed) both get the full
  deferred pool; an **ALLOWLIST** gets exactly its own `mcp__*` entries. So **literal
  fully-qualified MCP names inside a PRESERVED allowlist work** — the third option #292 did not
  know it had, and the one shipped, because it keeps `tdd-contract`'s deliberate no-`Edit`
  isolation. 15 lore tools (DERIVED from the live `tools/list`, never typed) added to the 5
  tdd-family agents + `contract-adversary` + `package-scout`; the false *"ToolSearch is the
  gateway (see #266)"* comment — applied, documented as working, never verified — removed from all
  7. Acceptance by execution: a real `tdd-contract` agent spawned after the edit called
  `lore_index` / `lore_comms register,send,drain` / `lore_search` with live returns, `Edit`
  absent. **SECOND, independent breakage found and fixed:** the canonical load line at
  `~/.claude/CLAUDE.md:344` named **3 tools that do not exist** — 35 dead names across 4 files
  (`CLAUDE.md`, `tdd`, `tdd-light`, `odoo-dev` skills), now 0, guarded by
  `scripts/lore_tool_name_currency.py` (asks the running server; mutation-proven both ways).
  ⚠ **TWO FALSE CLEARS PRODUCED AND CAUGHT IN-SESSION, same class both times — a narrow
  measurement written up as a general rule:** the currency instrument's first version reported a
  CLEAN `CLAUDE.md` (its `\b` anchor cannot match inside `mcp__lore_<slug>__lore_search_code`),
  and the fix's own teaching prose claimed *"ToolSearch reaches NOTHING"* when the truth is
  ToolSearch is **required-not-sufficient** and MCP entries arrive **DEFERRED** — left standing,
  an agent would have reasoned itself out of the tools it now has, reproducing #294 by BELIEF on a
  correctly-granted definition. Commits `d5ea7b0` · `e89bfa4` · `ff3b2c4`; receipts (6 reports +
  post-fix agent snapshot, since `~/.claude` is NOT version-controlled) →
  `receipts/2026-08-01-agent-comms-fix/`. **04b-2 remains `open` and unstarted** — both Fable
  sidecars and a `claude-code-guide` agent ran 60/31/17 min without returning a single reply
  (alive, ~2 min CPU, blocked in `epoll_wait`), so its design forks (B1 split · ESC-1 · #279 ·
  #273/#272 · footer `Rendered`-vs-`str` · **whether to deploy at all with the operator offline
  and `lore-lore` not restart-durable**) are ALL still unruled. Next session: re-run the sidecar
  before any 04b-2 work. Open bounds in #298: the grant is per-project (`lore_lore` slug, fails
  CLOSED elsewhere) · `Grep`/`Glob` listed by 7 definitions and delivered to none · `SendMessage`
  not grantable to an allowlist agent · `~/.claude` unversioned, so the GRANT half has no guard.
- 2026-08-01 (same session, CORRECTION) · **The agent fix SHIPPED IN THE WRONG SHAPE FIRST, and
  the sidecar overturned it.** The lead, blocked ~30 min with no sidecar reply, ruled A1 itself
  and shipped **literal `mcp__lore_lore__*` names inside the preserved allowlists** (`ff3b2c4`),
  reasoning that it kept `tdd-contract`'s deliberate no-`Edit` isolation. `design-agentfix-1` then
  returned — **by writing a report file, never by replying** (all four agents this session
  produced artifacts but never reached a turn boundary; the lead's SendMessage-based protocol saw
  nothing, which is #50779's shape from the other side) — and ruled the OPPOSITE, correctly:
  literal names are right for exactly one project and **silently wrong in every other, in a way
  byte-identical to the bug being fixed**; and the isolation being protected is INFORMATIONAL, was
  never enforced by the grant at all (`tdd-contract` already holds Write+Bash, so withholding
  `Edit` bought nothing). `security-auditor.md` — same artifact class — already ships with no
  `tools:` key. **Re-shipped as ruled: all seven lose `tools:` entirely** (`4729fb5`); the odoo
  scouts keep theirs (Odoo is not on lore; re-open trigger = a `lore.yaml` landing there); an
  EXCLUSION list was REJECTED for the blocking path as measured only on built-ins — adopting it
  unproven would re-commit #266 exactly. Accepted delta: `Agent`/nested spawning, with a named
  re-open trigger. **Acceptance is SERVER-SIDE, per standing comms law — the recipient's own
  artifact, never the agent's claim:** all seven types spawned in parallel, each called
  `lore_index` + `lore_comms register/drain`, and the lead's own `lore_comms action=fleet` shows
  **7/7 registered**. Bare sweep: zero hits for `266` and for "gateway to deferred" across
  `~/.claude/agents` + `~/.claude/skills`. Filed **#299** — standardise the MCP server name to a
  fixed `lore` (the allowlist-the-safe-set shape; `odoo-code`'s invariant name is the working
  existence proof), ADOPTED IN PRINCIPLE, **not executed**: MCP config binds at session start, so
  a mid-session rename cannot be acceptance-tested — shipping it unverified would be #266 a third
  time. **Operator ratifies on return; until then the seven stay unrestricted.**
- 2026-08-01 (same session, APPENDED CORRECTION to packet 44's entry — the Log is append-only, so
  the old line stands and this supersedes it) · **44's clause *"an explicit `tools:` allowlist gets
  no MCP tools, `Tools: *` does"* OVERGENERALISED from a wildcard-only probe.** Measured this
  session: **literal fully-qualified MCP names inside a preserved allowlist DO grant** (present and
  callable, sonnet and opus — the odoo scouts have been relying on exactly this all along); it is
  the `mcp__*` WILDCARD that expands to nothing. And a third shape exists that 44 never
  considered — EXCLUSION lists (`Explore`/`Plan`), which carry the full deferred pool. Corrected
  mechanism table in finding **#298**; receipts `receipts/2026-08-01-agent-comms-fix/`.
  ⚠ Also correcting THIS session's own first Log entry above: it says both Fable sidecars ran
  without returning. **They did return — by writing report files and by replying into an inbox that
  did not drain until the session's end**, so the lead saw silence while finished rulings sat
  undelivered. Both independently ruled A1 identically (delete `tools:`), which the lead had
  already shipped in the WRONG shape and then re-shipped correctly. The delivery failure is
  #50779's shape from the lead's side, and it is the packet-04b-2 subsystem's own reason for
  existing — worth treating as evidence for that packet rather than as session noise.
- 2026-08-01 (same session, close) · **PACKET 04b-2 DESIGN-RULED, DELIBERATELY NOT STARTED; 04b-3
  MINTED.** With the agent-comms fix landed and verified, the Fable sidecar delivered DECISION SET
  B (`receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md`; **directed to a FILE
  rather than a reply, because this session measured which channel is durable** — its A ruling was
  sent three times into an inbox that did not drain for 30+ minutes, while a sibling's identical
  ruling arrived the moment it wrote a file). **§B1 rules three levels:** L1 = record + mint (this
  session) · **L2 = the 04b-2 wave proper, ONE contract→adversary→build→audit→deploy**, scope
  consolidated from Scope IN + the ten inherited rows + sweep additions · **L3 = packet 04b-3,
  minted NOW** (#273/#272 · ESC-1's mechanism · CA-11 · CA-12), because *"a split that exists only
  in a message is a ruling the next session never meets"*. It states explicitly that stopping here
  is the CORRECT stop, not an early one, and addresses the next lead directly.
  **§B6 — NO DEPLOY, on a TECHNICAL ground, not capacity:** deploying HEAD would ship 04b-1's
  listing surface **without ESC-5's fix**, opening precisely the false-clear window whose provable
  absence made deferring ESC-5 legal (*"nothing is served until 04b-2 deploys"*) — so a deploy
  before ESC-5 lands is a **defect, not a convenience**. Production stays on `e91e37b9`; the old
  surface serves the old world honestly. The deploy becomes the next wave's EXIT behind a seven-line
  precondition gate whose riskiest named line is **the R11 backfill executing against the PRODUCTION
  store at that boot** — with a FRESH backup required (the 2026-07-28 one is not the rollback for a
  migration days later), both `CreateCommand`s **re-derived at deploy time** (never a stale capture)
  and diffed against #165's known-good mount shape, and rollback receipts written into the Log
  BEFORE the recreate. ⚠ OPERATOR-REVIEWABLE: that deploy runs a production data migration,
  unattended if the operator is still offline — the next kickoff should offer them the nod if back.
  The 04b-2 packet section now opens with a binding READ-FIRST box citing the ruling, and
  `04b-3` has an INDEX row. **NEXT SESSION STARTS AT §B1 LEVEL 2** — the packet is ruled, recorded
  and ready to build; nothing about it needs re-deriving.
- 2026-08-01 (same session, ESC-1 DISCHARGED) · **ESC-1 MEASURED YES — the decision point the packet
  named as "THIS kickoff" was MET ON TIME, by CONSTRUCTION rather than by reasoning from the
  invariant pins** (which were written for the mirror, not for the guard's read visibility). The
  ancestor closure of new dependencies IS persisted at write time: **58 PASS / 0 FAIL, counts
  DERIVED (`grep -c`), three consecutive green runs on fresh spike-surreal throwaway DBs**, with a
  **discriminating negative control** — a directly-deleted edge row caught by BOTH instruments,
  naming the exact pair, so the probe demonstrably can see a divergence — and `loremaster.__file__`
  printed to prove which tree ran (#140 discipline). **Consequence, per ESC-1's own clause: the
  ledger-independent write-path cycle read is ACHIEVABLE → the MECHANISM is 04b-3's, and the
  known-bound pin becomes a defect report DELETED WITH THE FIX, not a bound to keep.** Residue
  enumerated, both as the clause anticipated: batch-local `create_many` siblings and legacy
  phantoms (skip at WARNING). Two facts banked for 04b-3's builder: **no ledger verb mutates
  `blocked_by` after birth** (so the constructed verbs are the COMPLETE column-writing surface),
  and **a cycle member's edge closure contains ITSELF** (`truncated=False`) — self-reachability is
  the usable cycle signal on the edge read. Receipt archived beside the ruling; the packet's ESC-1
  row and the 04b-3 INDEX row both carry the verdict.
  ⚠ **HARNESS DATUM worth knowing before briefing probes:** the sidecar's `Agent`-tool subagent was
  REFUSED its own `Write` (*"Subagents should return findings as text, not write report files"*) and
  the sidecar had to persist the report itself — while teammate-spawned probes in this same session
  hit no such policy. **Spawn shape decides whether an agent can write its own receipt**, so a brief
  that says "write REPORT-x.md" is not portable across both; brief the text-return path, or expect
  the spawner to persist it.
- 2026-08-01 · **SESSION CLOSE — 12 commits, tree clean, no strays at root.** Delivered: the agent
  comms fix (#294/#292 → #298, spawn-verified 7/7 server-side), the retired-tool-name sweep (35 → 0
  across four `~/.claude` files, guarded by `scripts/lore_tool_name_currency.py`), packet 04b-2
  design-ruled end to end, 04b-3 minted, ESC-1 measured YES and discharged. Not started, by ruling:
  the 04b-2 build wave. **Next session starts at §B1 LEVEL 2** of
  `receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md`.
  **⚠ OPERATOR DECISION SET awaiting return — surface these at the next kickoff, none silently
  inherited:** (1) **#296** — packet 39 BLOCKED; per-principal tool gating inside FastMCP is
  undefendable (4 wrong builds, 1 root cause: handlers bind at construction, so post-construction
  installs are dead on the wire); recommendation is role-splitting so the hosted surface REGISTERS
  only read tools — structural, not enforced. (2) **D&D RAG forks 1–9** (`docs/design/2026-08-01-
  dnd-rules-rag-proposal.md` §9), fork 1 = the whole shape, recommendation C. (3) **#299** — rename
  the MCP server to a fixed `lore`; adopted in principle, execution deliberately deferred because
  MCP config binds at session start so a mid-session rename cannot be acceptance-tested. (4) **the
  04b-2 deploy runs the R11 production data migration, possibly unattended** — one-transaction
  additive, fresh-backup precondition, named rollback; **if production migrations should never run
  unattended, that is a standing preference worth setting once.**
  ⚠ **Posture change made under delegation, stated so it is met deliberately:** the seven fixed
  definitions now inherit the FULL session toolset (`Edit`, `Agent`, `WebFetch`, …) — grant-level
  restriction traded for prompt-level. Judged acceptable because the tdd isolation was always
  INFORMATIONAL and every one of those definitions already carried `Write`+`Bash`, so the allowlist
  was never an enforcement boundary. Re-tighten triggers: first harmful nested spawn in a tdd wave,
  or #299 landing (which makes a portable literal allowlist coherent).
  ⚠ Branch is **66 commits ahead of upstream** — not pushed this session; the operator pushes.
- 2026-08-02 · **D&D track RULED + SLOTTED: wave D (45–54) inserted after wave C; 39, 07, 07a
  pulled forward.** Option C ruled · comms completes first · hosted ON-BOX via hades to
  claude.ai (⇒ 39 + principals/keys pre-go-live) · NO dnd memory · full-power graph (fork 6
  OVERRIDDEN), seven edge families picked · composition CLIENT-SIDE (rules retrieval + graph
  filters; no per-mechanic composed tools) · edition policy = 5.0 downranked, read-the-2024-
  rules rider · dnd tool surface enumerated (5 generic + `dnd_*`; `lore_findings` ENABLED).
  Three graph-scope scouts (class/monster/crosscut) archived → `receipts/2026-08-01-dnd-graph-scope/`;
  rulings + edge catalog → `docs/design/2026-08-02-dnd-graph-scope-rulings.md`; packet files
  45–51/53/54 minted (52-series minted by 50). Forks 1/2/4/6/9 CLOSED; 3/5/7/8 + D3 at 50's
  kickoff.
- 2026-08-02 · **04b-2 WAVE C BUILT + COLD-AUDIT GO; DEPLOY PENDING OPERATOR NOD** (resume, `lead-04b2-wavec-r2`).
  Shipped C1+C3: the dispatcher pending-traffic footer, optional `agent`/`session` identity (link 1b/4), MP-6's
  honest ambiguity teaching, `_INSTRUCTIONS`, and minted `lore_tasks action=get`. C3 **225/0**; the C-DEF fixture
  gap (`get`/`blockers` unseeded in `_task_action_kwargs`) closed + 8 pins non-vacuity-proven; the fake's
  `transitive_blockers` bound DISCHARGED by the cold audit's live-store parity differential. **B3 attribution leak**
  DOCUMENTED+LEDGERED (#321, bound pin RED-when-closed) → full Link-5 provenance-containment fix → 04b-3; operator
  ACCEPTED the pre-existing exposure for the LOCAL threat model (*"document and ledger; address before comms goes in
  the wild"*). Cold audit **GO** at `60f83f0` (gates 225/1759/677, currency PASS zero RED_ORPHANED, every claim
  refuted-by-execution with controls). 15 findings resolved; #304/#309/#310/#319/#321/#322/#324 → 04b-3. 21 reports →
  `receipts/2026-08-01-packet04b2-wavec/`; wrong-build driver + audit probes → `scripts/`.
  ⚠ **DEPLOY NOT DONE:** it runs the R11 backfill as a PRODUCTION DATA MIGRATION at boot — awaiting the operator's
  specific go-ahead (fresh backup + MANUAL recreate, NEVER `lore-deploy start`, #165/#166); prod still `e91e37b9`.
  ⚠ **MODEL:** subagents ran opus-5 — no Agent-tool path to 4.8 (full-id rejected by the enum; omit/alias → opus-5);
  `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8` now set in `settings.json` for the NEXT session; this wave's work is
  verified by model-independent receipts, so nothing needs redoing.
- 2026-08-03 · **04b-2 DEPLOY — ROLLBACK RECEIPTS (written BEFORE the recreate, per §B6).** Shipping image
  `localhost/lore:latest` = `a6a4e5a2` (bakes HEAD `cde2a6c`; **loremaster/lorerunes/loresigil/lorescribe +
  Containerfile + pyproject are BYTE-IDENTICAL to the cold-audit commit `60f83f0` — verified `git diff` = 0**;
  the only changes since the audit are `scripts/` rescues + a parallel session's wave-D planning docs). ROLLBACK
  IMAGE: `localhost/lore:pre-04b2-20260803` (= `e91e37b9`, the outgoing prod). FRESH BACKUP:
  `/backups/lore/lore-prod-20260803T141930Z.surql` (3.63 GB, 22 tables, EXIT=0) — the rollback for the R11 backfill
  migration that runs at first boot on this schema. Artifact check GREEN (all 4 members baked at `/app`, wave surface
  present). RECREATE = the outgoing container's captured `CreateCommand` verbatim (`--network=host --userns=keep-id
  --user 1000:1000`, `/workspace:ro`, `/source:ro` ×2, state dir, `lore.env`, `LORE_CONFIG`) — #165's known-good
  shape, NEVER `lore-deploy start`. TO ROLL BACK: `podman rm -f lore-lore` + recreate on `pre-04b2-20260803`; if the
  migration corrupted data, `surreal import` the backup.
- 2026-08-03 · **04b-2 DEPLOYED — functional comms is LIVE on `a6a4e5a2`.** Recreated `lore-lore` on the
  new image (captured `CreateCommand` verbatim, #165's known-good `/source` shape — NOT `lore-deploy
  start`). Boot clean: `embed.probe.ok` (dim 2048), `startup.probe_gate.pass`, and **the R11 backfill
  migration ran against the PROD store minting 51 blocks-edges (`task.backfill.blocks_edges_minted`,
  no error — the #107 silent-no-op did NOT recur, the migration actually WORKED)**, watcher started.
  SMOKE GREEN: MCP `initialize` → `serverInfo.version=pkt03b-…-gcde2a6c` (the new image), 15 lore tools
  served, the wave's `_INSTRUCTIONS` pending-traffic teaching in the served instructions block, and
  `lore_tasks action=get` (Ruling 8, minted this wave) reaches the ledger and TEACHES on a missing id.
  In-image artifact check GREEN (all 4 members baked at `/app`, #139/#140/#131). Prod was `e91e37b9`,
  now `a6a4e5a2`; rollback image `pre-04b2-20260803`, backup `lore-prod-20260803T141930Z.surql` (3.63 GB).
  **NOTE:** a parallel session is committing wave-D planning docs to this branch — the deploy baked
  `cde2a6c` (docs-only descendant of the audited code; loremaster `git diff` vs `60f83f0` = 0).
- 2026-08-03 · **Wave D SPEC'D + RESEQUENCED (auth to the end) + the TRANSMUTE pivot.** Operator
  rulings: corpus splits prose/machine tiers — extraction moves to the SCRAPER as an LLM
  transcriber (HTML-first, recovers the destroyed link anchors; deterministic word-for-word
  gates; Agent SDK on the Max subscription per the MEASURED transcribe-craig pattern; spec =
  `dndlorescraper:SPEC-transmute.md`) · order now 45→46→47→55(∥)→50→51→52a/b→53→54 LOCAL
  soak→48→49→39→07→07a→56 GO-LIVE (54 split: local deploy vs 56 exposure) · cross-edition
  refs resolve via the SUPERSESSION FUNCTION (5.5 → rename-alias → 5.0 → tombstone; link's
  own edition ignored). Architecture: `docs/design/2026-08-03-wave-d-architecture.md`;
  packet 50 reshaped to contract-prep; rows 55/56 minted; rulings doc §1.8 superseded in place.
- 2026-08-04 · **04b-3 CYCLE DONE — Fable-sidecar-led, operator hands-off ("Fable makes all the
  calls; the operator is not the consumer").** Fable split the residue → 04b-3 CYCLE (ESC-1
  bounded-closure read + #273/#272 networkx swap) / mint **04b4 SERVED** / mint **04b5 INJECTION**
  (#321, HARD precond of pkt 56) / #304→05a / CA-11 + CA-12 DEFERRED w/ triggers. Two Fable
  self-retractions (§C-A edge-only guard; from-minted reformulation) were caught PRE-BUILD — by the
  contract author, then the adversary's proven TRILEMMA → variant D. Contract → adversary → build →
  cold-audit **GO** @ `496a95e`; currency **PASS** after fix-wave `6fa1177` (3 probes → `_surreal_harness`;
  + 04b-2's 12 orphans folded in per operator). COMMIT-ONLY (rides 05a). Side micro-item: **#327
  lore_comms body-cap 2000→4000** (Fable-derived value, Sonnet-built @ `4d81f76`) — **DEPLOY PENDING**
  (live-store schema migration on :18500, awaits operator go). #330 filed (lore-surreal auto-restart,
  cause unknown). Reports → `receipts/2026-08-04-packet04b3/`. All coordination ran on lore_comms.
- 2026-08-04 · **#327 cap DEPLOYED + store OOM root-caused & fixed + stores repinned to v3.2
  (operator-directed, post-04b-3).** Image **9debdd34** (manual lore-lore recreate, #165 hand-rolled
  `/source` shape — NOT lore-deploy start) bakes the lore_comms body-cap 2000→4000 (#327) AND the
  cold-audited CYCLE change `496a95e` (commit-only ride-along, now LIVE) + its networkx runtime dep.
  **O-2 gate PASSED** (a >2000-char body sent #3000 + drained INTACT → `DEFINE FIELD OVERWRITE`
  widened the live :18500 body/ack_note ASSERTs to 4000; the #107 silent-no-op did NOT recur); boot
  clean (probe_gate.pass, Uvicorn :9202), in-image provenance GREEN (#139/#140), data intact (3267
  files). Rollback image `localhost/lore:pre-327-20260804` (=`a6a4e5a2`). #327 resolved.
  **Store OOM (#331, supersedes #330):** lore-surreal was kernel-OOM-killed mid-session — two
  co-tenant Surreal stores' uncapped ~62 GiB RocksDB block caches on a 125 GiB **no-swap** box. Both
  quadlets now set `SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=8 GiB` (UNDOCUMENTED var, verified on spike
  first) + pin the floating `docker.io/surrealdb/surrealdb:v3.2` (=3.2.4) tag. Load-tested under the
  exact `-n auto` workload that caused the OOM: spike peaked **1.65 GB / 0 restarts** (was ~11 GB).
  #331 resolved. Both stores + lore-lore live and healthy.
- 2026-08-05 · **PACKET 04b4 (SERVED) DONE — commit-only, Opus end-to-end, all coordination on lore_comms.**
  Entry-check caught #310's concrete already shipped (`0ff05ed`) → operator ruled **class-instrument only**.
  Contract → adversary **INSUFFICIENT** (a P6 corpse contradicting #309 = a C-DEF trap for any cap<40) → fix
  → **delta SUFFICIENT**. Build greened 6 RED: #309 no-limit `query` display cap=50 + counted-elision via the
  shared `render_line` (K DERIVED, no `count()`, cap at RENDER only — ruling A), #319 `note` names `acknowledge`,
  #324 R-4 `name`/`to` keyword-required; #310 class + #319 class-bound = PIN-THE-MISS; #322 ∀ + R-2/R-3 GREEN.
  Cold audit **GO** @ `0255901` (04b4 blast radius 0-failed, ZERO new mypy, byte-exact restore; lead receipt
  245/0 + render-hunk read). `3091610`→`37d4adc`→`0255901`; 9 reports → `receipts/2026-08-05-packet04b4/`.
  Filed **#332** (§D-#304 STALE-badge premise false → 05a) + **#333** (branch typecheck RED **191 mypy + 316
  pytest**, ALL pre-existing auth WIP pkt 39/45/48/49 referencing not-yet-built symbols; 04b4 zero-new;
  operator ACCEPTED proceed). Builder hit the #22/#55 lore-load flake, fell back to grep + native SendMessage
  honestly. **NOT deployed** — rides 05a. NEXT comms = **04b5** (INJECTION #321, deploys before pkt 56) or **05**.
- 2026-08-05 · **PACKET 04b5 (INJECTION #321) DONE — Link-5 render-site containment, TEST+PROD, commit-only.**
  `render_attributed`/`fence_width` seam; every caller-origin byte reaching a served answer routed through
  provenance-delimited containment, reach as a CHECKED variable (name-blind AST error-scan + P-U/P-F/P-S render
  nets, coverage.py branch-obs). Operator ruled FULL door scope + fence full route-through + coverage.py +
  route-the-self-echoes + close-the-`.format()`-gap. Property-to-invent: the two-waves tripwire on render-reach →
  a **Fable design sidecar** ruled the instrument (P-U by interpolation property, NOT the `_render_` prefix — a
  six-defeats name-list). 5 contract authors (2 transient API deaths, both recovered from committed checkpoints —
  the checkpoint-every-round lesson), an **Opus-4.8 recheck** (per operator; caught a fabricated §SAT receipt →
  operator ruled the build discharges #133), build, cold audit **GO** (0 leaks / 12 hostile forgery shapes,
  mutation-proven non-vacuous). ⚠ The **`.format()` reach blind spot** (recheck + cold audit both missed it — they
  tested routed sites, not interpolation-mechanism coverage; exposed a live self-echo `caller_model` door) was
  closed as an operator all-or-nothing extension. Gates: contract 256/0, ruff clean, currency PASS (zero
  RED_ORPHANED), full-suite failures ALL auth-WIP (#333; 04b5 zero-new). `4c5930d`→`6ff51cf` (10 commits); 18
  reports → `receipts/2026-08-05-packet04b5/`. #321/#335 resolved. **NOT deployed — rides 05a; MUST deploy
  before pkt 56.** Comms lapse fixed after operator feedback (content on the ledger, wake on native). NEXT = 05.
- **05a-iii (comms READS + fleet honesty): DONE + DEPLOYED 2026-08-08, image `a04a23ca` (lore-lore).**
  Shipped: `story` (task-arc + fenced messages), rollup messages/fleet/skew sections, #304
  age-the-declaration (input_required cell aged; NONE→"unknown"; badge reads STORED status, NOT
  awaiting_answer — the DD-2 conflation D9a/D9b forbid), read-only `comms_cli`. Pipeline: contract
  adversary-**SUFFICIENT** (2 passes) → build → contract-fix (ESC-2/3/4/5/6 companion pins; 2 adjudicated
  allowlists — promise-free + SecretStr mint-origin) → cold audit **GO** @ `4fc8b70` (444 pytest/191 mypy =
  #333 auth-WIP baseline, 05a-iii **zero-new**). Deploy carried 04b-3/04b4/04b5 backlog + #321 LIVE + a
  **tini PID-1 init** (bare python was PID 1 → wedged conmon + graceless shutdown; tini confirmed
  `/proc/1/comm`). Coordination dogfooded over `lore_comms` (no SendMessage). #304/#332 resolved; filed
  #336 (store-version drift) / #337 (promise-scanner name-reach — ledger, NO pin per operator) / #338
  (test_comms_tool 5010-stmt > 5000/txn index cap). Rollback `9debdd34`. 05a-i/05a-ii/05b remain — NEXT = 05a-i/05a-ii.
- **05a-i (comms CONSUME PATH): DONE 2026-08-09 — commit-only, rides 05a-ii's deploy (operator-ruled).**
  `drain` reshaped: `since=<seq>` seen-row recovery (DD-4.c/#214; seq>since STRICT, non-stamping, bounded),
  #183 window bound (`count()…GROUP ALL`), `stamped_seqs` truth (`UPDATE…RETURN AFTER`); R1 `question` marker;
  **#190 oracle-parity invariant** (fake was 1-based vs prod `sequence::nextval START 0` — fixed to 0-based,
  closes the D4 blind spot); DD-2.a waiting line on drain+heartbeat via ONE shared helper (operator ruled USE).
  Pipeline: contract → adversary **INSUFFICIENT→delta→delta-2 SUFFICIENT** (F1-F5) → build → cold audit **NO-GO**
  (currency gate: 8 RED_ORPHANED structural/architecture pins the scoped 4-file runs missed) → fix + a
  **Fable-ruled D2 REVERSAL** (first design fork of the session): the waiting-line `thread` AND its blast sibling
  the drain-row `task_id` (#343, pre-existing/unswept) leaked plain-ASCII prose forgery through `sanitise_line`
  (control-char collapse ≠ prose containment) — a live #321 TRUST leak; both → `render_attributed`, the false-gate
  containment test strengthened with a real `_leaks` leg → re-audit **GO** (instruments mutation-proven non-vacuous;
  currency PASS zero-orphan; 1705/0/17; only the #333 auth-WIP baseline residual). `d9b151b`→`d509980`→`53e28fc`;
  receipts → `receipts/2026-08-09-packet05ai/`. #336/#342/#343 resolved; filed #341 (floating `v3.2` tag→pkt16);
  store-ref/INDEX/MEMORY reconciled to the measured 3.2.4. ⚠ RETRO (operator-requested): the packet
  repeated ≥5 previously-instrumented classes (#321 injection ×2, #306/#312 currency, false-gate,
  #156 "safe by construction", #131 unexercised-path) — ALL caught, nothing shipped; every catch was
  by CONSTRUCTION (adversary built a wrong impl, audit ran the gate, builder rendered a forgery), every
  miss by REASONING (the lead's D2 sanitise_line ruling repeated #156). Prevention filed: **#344**
  (derive ONE gate-bundle from `gates.yaml` so no stage claims green on a subset) + **#345** (Link5
  derives free-text slots from the render AST + coverage assert). Memories `2380d29b` (retro) +
  `bcef60f4` (the "argument or probe?" reflex: a containment claim is inadmissible by ruling).
  05a-ii/05b remain — NEXT = 05a-ii (await, Opus-4.8 LIVE leg).
- **DEFECT-CLASS PREVENTION WAVE (05a-i retro #344/#345 + 6 siblings): BUILT + COLD-AUDIT GO 2026-08-10 —
  commit-only `f49d668`, NOT deployed (operator: (re)build deferred to the next packet that needs it).**
  A dedicated sub-cleanup wave making ONE class un-writable by construction: *"a guard/gate/probe certifies
  only the sites it EXECUTES over, and its reach is a hidden CONSTANT, not a checked variable."* 8 instruments
  via the design's §9 ∀-mutation-proof pattern (reuse shipped idioms; prove sharing by MUTATION): **G/#344**
  `scripts/wave_gate.py` non-omittable bundle, operator-**SIMPLE** design (no `--wave=full`; `--wave <args>` =
  core-full + scoped pytest + `SCOPED RUN` honesty flag; no-args/zero-collect = error) — closes the #306/#312
  subset-green recurrence; **B/#345+#348** `render_attributed` containment + AST-derived driven-slot coverage +
  the live `Agent`/`Message.task_id` forgery door; **C/#291** `partition_tools_by_posture` (deny-by-default,
  `readOnlyHint is not True`) retiring the drifted `_MUTATING_TOOLS` hand-list; **D/#295** observe-the-EFFECT
  (`assert_tool_refused_and_did_not_run`, wire + invocation-counter) under R16; **E/#289** trailing-newline
  matrix; **F/#279** `loremaster.store._txn_coroutines` one-derivation; **H/#290** `refuse_vacuous_baseline`;
  **A-SUB/F4** `parse_production_trees` consolidation (~14 hand-rolled parsers → 1) behind **L1**, a runtime
  `builtins.compile` chokepoint (un-defeatable-by-spelling). **INSTRUMENT 0** = a GLOBAL contract-adversary
  REACH ATTACK (probe P1c, `~/.claude/agents/contract-adversary.md`). Pipeline: contract → adversary → build →
  cold audit **GO** (8 contracts green, 5/5 mutation spot-checks discriminate, diff-honesty clean). One trivial
  regression (a local `annotations` shadowing the `__future__` import, tripping the #125/#131 exec-seam scanner —
  which correctly caught it) fixed by a Sonnet agent + full-suite re-verified. Gates: **9582 passed / 444 failed
  (ALL the #333 auth-WIP baseline, RED_ADJUDICATED→pkt39; ZERO new)**, ruff clean, currency **PASS** (0
  RED_ORPHANED). Findings: **11 resolved** (#344/#345/#291/#279/#289/#290/#295/#348/#346/#347/#350); **#351
  acknowledged** as a PINNED BOUND (with #349; #337 stays ledger-only). Reports → `receipts/2026-08-09-defect-class/`
  (49). Design of record: `design/2026-08-09-defect-class-prevention.md` §1–§13. ⚠ COST RETRO (operator): a
  trivial-importance cleanup that over-spent on the G/A-SUB design spiral — lesson logged: right-size rigor to
  importance, escalate the cost/importance mismatch EARLY. NEXT = 05a-ii.
- **05a-ii (comms `await` verb + Opus-4.8 LIVE leg): DONE + DEPLOYED 2026-08-10, image `65e36c8` (lore-lore).**
  Shipped the served `await` action: standalone `InboxAwaiter` (LIVE-primary + poll-fallback, snapshot-first,
  PEEK/no-stamp per F1, ≤55s fixed const per F2, agent-id-only LIVE-WHERE per Q5(ii), final-snapshot-at-timeout,
  timeout render consumes DD-2.a's `awaiting_answer`, R-3 `action=drain` typed-applicability render). ONE
  IMPLEMENTATION (operator DRY directive): scout's 8 inline `(*_CONNECTION_ERRORS,KeyError…)` clones DRY'd onto a
  shared `store._txn._SDK_AWAIT_BOUNDARY_ERRORS`, proven-by-mutation (runtime pin + AST reach belt). Canonical
  await-design file was GONE — reconstructed from surviving sources (Fable sidecar). Pipeline: contract →
  adversary (INSUFFICIENT×2: R-2 standing-share + PIN-2 reach) → build → cold audit **NO-GO #354** (unguarded
  LIVE-connect crash — a graceful-degradation defect green at every builder gate; operator-approved fix-now) →
  ~3-line connect-guard → adversary SUFFICIENT → cold-audit delta **GO** @ `5466b7b`. Gates: scoped 1838p,
  zero-new mypy, ruff clean, currency PASS 0 RED_ORPHANED (#333 auth-WIP baseline unchanged). Deploy:
  rollback `pre-05aii-rollback`=`a04a23ca`; recreate triggered a **one-time full lore-tier re-embed** (~94 min,
  boot self-heal on a store↔manifest count drift — root-caused, **#355** filed, fix→follow-up, NOT recurring);
  live-leg **SMOKE PASS** (served snapshot + honest-empty-names-bound + WAKE 21.7s<55s). #354 resolved, #355 filed.
  Reports → `receipts/2026-08-10-packet05aii/`. Ships the 05a-i + defect-class commit-only backlog LIVE. 05b NEXT.
- **05b (comms LEDGER VERBS + HOOKS): DONE + DEPLOYED 2026-08-11, image `3ded8244` (lore-lore; git `3c68ca6`;
  rollback `pre-05b-rollback`=`65e36c8`).** LIVE served: #256 `lore_findings annotate` (status-preserving, shared
  `_guarded_append_fragment`, #104-safe, teaches discoverability) · #262 register liveness notice (discloses a
  held task's holder + STALE-derived liveness; Reading 1 disclose-not-refuse; shared `_heartbeat_is_stale`) · #174
  supersede carries `blocked_by` (sentinel inherit/clear/replace + surface + self-block refusal). idle-gate v2
  (#149, local hook — declared-artifact-contract file) `a52576f`. Per workstream: contract → adversary → build →
  cold audit; idle-gate 2 adversary rounds/5 gaps, #256 cold-audit NO-GO on an unregistered guarded-CAS door
  (fixed), verbs adversary caught an unclaimable-successor self-ref ON THE REFERENCE BUILD (pinned+refused). Boot =
  delta reconcile (13 files, **NO #355 hang**); live SMOKE PASS all 3 served surfaces. Commits
  `a52576f`/`c0071cd`/`e69c45a`/`3c68ca6`. #89 struck (04b-2); #121 preserved; #195→06 (annotated — first live
  `annotate` dogfood); resolved #149/#256/#174/#262/#359; ack→forward #356/#357/#358. **Minted forward:** the #356
  re-anchor-with-note item (⚠ MUST CITE THE DRY ISSUE — tasks hand-roll guarded-append 3× vs findings' extracted
  shell → extract a task-side shell + cross-module unify to `loremaster.store`; carries the hub-supersede txn
  bound), the coordination packet (assign verb + assignee field + reap + ownership↔liveness reconciliation; forks
  2/3/4/6 at its kickoff), report-graph→28a. **Process landed mid-wave:** brief-base **v12** (builders produce a
  DRY ledger) + lead-base **v5** (lead checks the DRY ledger + `Packages considered:`). Reports →
  `receipts/2026-08-11-packet05b/`.
- **06 (comms-protocol-drill) KICKOFF 2026-08-11 — SPLIT 06a/06b + 3 operator rulings + a scope correction.**
  Lead `lead-06`. Fable design sidecar delivered `design/2026-08-11-packet06-drill-and-obedience.md`
  (§A #195 obedience battery / §B drill choreography / §C brief-base v13) and ground-truthed a FALSE
  inherited premise → **#360**: the ⚠STALE glyph the packet believed retired is LIVE at HEAD (`c12d158`) in
  two renders — #259 ruled retirement (candidate b) but 04b-2 shipped only the columns, so the retirement
  AND the `overdue` verdict (candidate d) are both unbuilt. **SPLIT** (sizing ≥0.30 + #360): 06a build
  enablers (DEPLOYS) → 06b the drill + measurements + close wave C [ledger `f582f0ad`/`fe6e5f8a`]. Operator
  rulings: (1) split 06a/06b; (2) #257 = MINIMAL non-vacuity floor at `brief_publish` (no pin-the-miss);
  (3) RETIRE ⚠STALE in 06a (sweep both `_heartbeat_is_stale` callers). Build next: two parallel pipelines
  (W1+W3 served-surface honesty; W2 obedience battery) via `opus48-worker`; brief-base v13 lead-applied.
- **06a (comms served-surface honesty + #195 obedience battery + #257 floor + brief-base v13): DONE + DEPLOYED
  2026-08-12, image `2c87e7b0` (lore-lore; rollback `pre-06a`=`3ded8244`; git `495e9d9`).** LIVE: `declared_cadence`
  `option<>` field + `cadence` on register/heartbeat + the `overdue (declared, silent)` fleet verdict (derived,
  #104) REPLACING the retired ⚠STALE glyph on BOTH `_heartbeat_is_stale` callers (#360/#259b); a fails-closed AST
  scan bans the glyph literal (the #262 re-propagation class, closed); the #257 non-vacuity floor at `brief_publish`
  (token ≥3, `is_blank` dropped per F-DRY); and the #195 obedience battery (O1 misdirected-send / O2 ack-scope
  graders, `scripts/comms_consumer_eval.py` — SCRIPT, commit `f9b5f2b`). Pipeline per workstream: contract →
  adversary → build → cold audit **GO**. ⚠ The #195 obedience contract took **3 fix waves + 3 adversary deltas**
  (F1 multi-recipient → DF1 positional last-slot → the terminal parametrized-over-position pin with a documented
  k=5 bound) — each round a REAL hole on the trust-critical instrument, converged not spiralled. The honesty
  cadence echo is a NEW render of user free text → routed through `render_attributed` (#321/#345 containment;
  cold-audit byte-diff, no forge-through). Served-surface **SMOKE PASS** via `lore_comms` (⚠STALE GONE on 7d/14d/30h
  agents; live `overdue (declared ≤1m, silent 2m)` echoing the agent's OWN cadence, F-ECHO; #257 floor rejects a
  2-token brief with the served teaching error; register-cadence round-trips on the populated store). ⚠ The recreate
  triggered a **#355 lore-tier re-embed** (**865 files re-embedded, ~3h — 03:56→06:56 UTC** [first index.file.done
  03:57:41 → last 06:56:13; startup complete 06:56:14]; the schema self-heal + code were LIVE before it, so comms
  was correct throughout; the MCP server accepts connections only after it completes). **Process:** brief-base
  **v13** (C-1 #228 watcher / C-2 write-side artifact-contract / C-3 comms-protocol / C-4 #195 teaching rule).
  #362 filed (old-world blast-radius grep gap + adversary satisfiability scope). **06b (the DRILL + measurements +
  trace-GC + close wave C) is NEXT** and inherits v13. Reports → `receipts/2026-08-12-packet06a/`.
- **06b (comms-protocol-drill — THE DRILL + measurements + trace-GC): DONE 2026-08-12, COMMIT-ONLY
  (`26739ca` on `40744a6`; drill receipts `40744a6`; rides the next deploy).** THE DRILL — the
  subsystem's ACCEPTANCE GATE — ran live to completion (lead-06b + drill-worker-06b + drill-prober-06b,
  coordinating SOLELY through lore): register→brief→create_many-DAG→claim→mid-work skew→directive-ack→
  parked question→**kill→`overdue (declared ≤2m, silent 6m)` orphan, NO ⚠STALE**→release(supersede)→
  story+rollup; **zero coordination content on native SendMessage** (grep: both drill agents 0 SendMessage,
  all content on the ledger). #195 obedience LIVE: battery **gate PASS 3/3** floor-model + population
  (Fable task-10 FAIL adjudicated a harness answer-parser artifact #364 — obedience held on all 3 models)
  + a live lead-impersonating in-fleet injection the prober RESISTED (acked the edge, refused the body).
  Measurements (14d prod trace): join-quality **1:many DEGRADED** → inference-free instruments (DD-5.b);
  loss-rate **0.20%** (1/493, <0.5%, DD-4.d); **FORCED-DRAIN DECISION on the MEASURED curve = keep
  pull-by-standing-instruction, no compeller** (never-drain pop role-confounded; 05b5cd71 done). Trace-GC
  (#193/DD-1.c): 90d, **E1=Reading Y** (bounded id-batched purge on the periodic reconcile tick ONLY,
  never the boot sweep; `DELETE…LIMIT` PARSE-ERRORs on 3.2.4 → id-batched rides `trace_ts`), **Fork-A**
  caller reach pinned on BOTH `_periodic_reconcile` daemons (mutation-proven non-vacuous); pipeline
  contract→adversary(INSUFFICIENT on Fork-A only)→build→cold-audit **GO**; commit-only (2405 rows « 1M).
  Findings #363/#364/#365/#366 filed; #193/#360 resolved; tasks 05b5cd71 + d9395d54 + fe6e5f8a done.
  **WAVE C (the agent-comms subsystem) CLOSES HERE — deployed, working, acceptance-passed at fleet scale.**
  Reports → `receipts/2026-08-12-packet06b/`.
- **06b currency-fix (the honest wave-C close):** the REQUIRED wave-close `--currency` gate (run AFTER
  the premature close-out commit `3e38a5a`) surfaced **7 RED_ORPHANED pins** — 6 = 06a collateral (the
  #257 floor / `declared_cadence` / `_CADENCE_RE.match` #210 / the #345 render-inventory, shipped without
  06a running `--currency`), 1 = 06b's (the new trace-GC test bumped a harness importer-count pin). Operator
  ruled **fix-all-7**. Fixed (`e9c7f82`, commit-only): 6 mechanical stale-expectation updates + B2 = an
  evidence-backed `_PARSE_GATED_DOOR_FIELDS` exemption (a manifest DOOR whose only render is parse-gated →
  un-observable via a forge token) with a **mutation-proven-discriminating** control — the builder caught
  that the lead-ruled `not _leaks` predicate was VACUOUS for this vector and promoted `CONTROL_CHAR_PATTERN`.
  Lead-verified: 9 pins pass, `--currency` **PASS — 0 RED_ORPHANED** (remaining 191 mypy / 444 pytest = the
  #333 auth-WIP baseline, RED_ADJUDICATED owned by pkt39). #367/#368 resolved; #363/#364/#365/#366 open as
  follow-ups. Lesson: run `--currency` at EVERY packet close, not just the wave close. **WAVE C CLOSES CLEANLY.**
- **06b DEPLOYED 2026-08-12 (operator-requested — promoting the commit-only trace-GC + orphan-fixup to LIVE):**
  pushed `c245394` → rebuilt `localhost/lore:latest` = **image `4320f9ae`** (LORE_VERSION
  `pkt03b-tainted-corpus-585-gc245394`) → recreated lore-lore (hand-rolled double-mount, verbatim
  CreateCommand). Rollback `pre-06b` = `2c87e7b0`. Boot = **fast DELTA reconcile ~141s, NO #355 re-embed**
  (0 `index.file.done` — manifest in sync post-06a + the live watcher). Artifact VERIFIED in baked
  site-packages: `purge_traces_before` + the gated purge + `trace_retention_days` + the `.fullmatch` fixup +
  both periodic caller wirings. Static tiers loaded (`tier.skip` ×3). **E1=Reading Y confirmed in prod:**
  `files_purged=0` on the INITIAL sweep (purge gated off boot; fires on the periodic tick). ⚠ 1 file failed
  to index = **#338** (`test_comms_tool.py`, 5028>5000 stmt cap — pre-existing/benign, not a regression).
  ⚠ Served-surface regression smoke via `lore_*` is PENDING a fresh `claude --continue` session (the recreate
  severed this session's MCP connection); LOW-RISK — 06b ships no new/changed served surface (internal GC + a
  proven `.fullmatch` no-op). Prod now on `4320f9ae`.
- **2026-08-13 — packet 45 (tool allowlist) DONE + DEPLOYED; WAVE D OPENS.** `tools:` allowlist ships: a
  disabled built-in is NEVER REGISTERED (`_gated_tool` at all 15 sites), served prose (`build_instructions`
  + 15 descriptions) is now a function of the enabled set, universe single-sourced to prod, collision-guard
  checks the declared universe. Pipeline contract(30)→adversary(INSUFFICIENT: E2 quantifier gap)→MP-1
  revise→delta-adversary(SUFFICIENT)→build(GREEN, 4 mutation proofs, byte-exact instructions)→cold-audit(GO,
  0 defects). **#296 RESOLVED** with a production receipt (baked scoped suite **1646/1646 in image `40ba206d`**,
  incl. the wire test). lore-lore recreated on `40ba206d` (git `5467316`; rollback `pre-45-rollback`=`4320f9ae`),
  delta boot **no #355 re-embed**, `Uvicorn :9202` + `lore_index()` serve git 5467316. Deploy gated via
  provenance-probe + baked scoped suite (full-suite conformance skipped — RED by the pre-existing #333 auth WIP,
  same as 05a-ii/06a/06b). Filed **#369** (subagent over-deliberation → mandate incremental externalization),
  **#370** (reduced-surface NL bounds R3/R4 → pkt54). ⚠ **#338 recurred** on boot (test_comms_tool.py >5000-stmt
  cap, ~140s waste — pre-existing/benign). Reports → `receipts/2026-08-13-packet45/`. Prod now on `40ba206d`.
  **NEXT = packet 46** (extension discovery wiring; deps: 45 ✅).
- **2026-08-14 — packet 46 (extension discovery wiring) DONE; COMMIT-ONLY, NO DEPLOY (dark until 54).**
  `extensions:` in lore.yaml now instantiates registered `Extension`s at boot: `_discover_extensions`
  (`LoreServer.__init__`, iterates EVERY key) → registry lookup → `register_extension`; unknown key fails boot
  LOUDLY (teaching error naming the `sorted(registry)`-derived known set, no leak); key≠name guard; packet-39
  **R14 rider PAID** (ext tools `readOnlyHint=False`). `EXTENSION_REGISTRY` ships `{}` — discovery dark until a
  real extension (pkt 51/54). Pipeline: contract(9)→adversary **INSUFFICIENT** (∀-config-keys pinned at N=1)→
  revise(+2, **11 pins**)→delta-adversary **SUFFICIENT** (24 wrong builds; 2 adversarial-only residuals →
  **#371**, receding-reach STOP-rule)→build (11 GREEN by IMPL, contract untouched, 4 mutation proofs both-way)→
  cold-audit **GO**. Both Trust legs live-verified (real derived known-set; empty-registry+named-ext fails LOUD,
  no false clear). Fable sidecar ruled the test-migration fork (`minimal_config` default→`{}`; Cat A/B/C; caught
  +3 files the contract census missed); DUAL preserved incl. the discovery-UNREACHABLE missing-slice branch kept
  manually pinned. Store touch NONE. Gates zero-new-delta vs #333 (currency PASS, 0 RED_ORPHANED). Commits
  `543ed72`(impl+R14)+`89852b3`(migration); reports → `receipts/2026-08-14-packet46/`.
  **NEXT = packet 47** (twelfth seam: ingest entity-fragment — ⚠ DESIGN packet, roster law; deps: 46 ✅).
- **2026-08-14 — packet 47 (twelfth seam: ingest entity-fragment) DESIGN DONE; COMMIT-ONLY, NO DEPLOY; SPLIT → 47a build.**
  DESIGN packet (roster law): Fable design sidecar authored the ruled seam design → an **independent Opus-4.8 adversary**
  attacked the FINISHED doc (**SHIP-WITH-FIXES, 8 findings ALL folded** — F1: per-`source_book` scope can't restore a cross-book
  edge on any incremental path; F3: the Indexer was unwired for `claims()` — the headliners) → Fable r2 re-verified the code facts
  live. Operator rulings: SPLIT · transactionality **Reading B** (entity+manifest atomicity; the pre-transmute chunk-rollback pin
  is unrepresentable since claimed files skip chunking) · phase-2 edge resolution **FULL-SWEEP-ONLY** (incremental watcher = pinned
  non-feature → dissolves F1 by construction, and IS the edition-supersession enforcement point). Operator also RULED the
  **edition-precedence mechanism** now (A1+B1+C1+distinct-nodes: lore-side `book_precedence` book-level total order, no ties, distinct
  nodes per (source_book,slug); **no scraper change**; consumed by 51/52b/50/53/55). 2 ruled docs `docs/design/2026-08-14-*`; commit
  `26d2bde`; reports → `receipts/2026-08-14-packet47/`; store touch NONE. **NEXT = packet 47a** (12th-seam BUILD: contract→adversary→build→cold audit; deps 47 ✅; ~0.32–0.38).
- **2026-08-15 — packet 47a (twelfth-seam ingest entity-fragment) BUILD DONE; COMMIT-ONLY, NO DEPLOY (dark until 52a/52b).**
  Pipeline (Opus 4.8 end-to-end): contract **40 pins** → contract-adversary **INSUFFICIENT** — an 8-file scratch reference build found **3 C-DEFs RED on a CORRECT build** (P6 `pytest.raises` contradicts §Q2.3 fault-isolation; P13 no seam feeds the store its entity tables; P20 `resolve_edges` returns UNLABELED fragments so `scopes_failed` can't name a scope), a wrong build surviving the one-directional atomicity pins (missing framework-fail ∀-pin, QUANTIFIER law), and the P8 reach gap → **consolidated revision r2** → **delta-adversary SUFFICIENT** (40/40 on the reference build; every fix + new pin broken by a reddening wrong build) → build **GREEN** `91fc30e` → **cold REFUTE audit GO** (gates re-run 40/40 ×5, an independently-constructed #107 dirty-store ENFORCED-migration probe, 6 mutation proofs, 964 regression green, zero-new-delta).
  Two operator-APPROVED seam-surface additions the adversary compelled (amend ruled §Q1.1, doc R3 log): **DG1** `IngestBackend.entity_tables()` → `build_app_context` unions → `SurrealStore(entity_tables=)` → `delete_by_tier` co-purges each table by tier (the §7 sink was otherwise unimplementable); **DG2** `resolve_edges → list[ResolvedScope]` (scope-labeled) so F7 loud isolation names WHICH book failed. DG3 (within intent): the phase-2 hook is the `index_all`+`rebuild_all`+`reconcile` union via ONE `_resolve_all_extension_edges` (`_sweep_two_pass` is batch-only).
  **HARDENING wave** `06b7142` (operator-ruled the cold-audit residuals): **R2** a LOUD fail-fast guard — the shared compose-path dispatch `ready_claiming_extension` RAISES when a file is claimed but its extension's declared tables aren't registered, converting the latent cli/scout half-wiring's silent SCHEMALESS auto-create corruption (store §5) into a loud stop (Fable-ruled sink placement `_entity_fragment`, compose-only — DELETE/purge is self-harmless); **R1/#376** a register-wiring pin over the real `build_app_context` path (#131 class); **R3** served-docs teach twelve seams. Fable design sidecar ran the whole packet (sizing SINGLE, DG1/DG2/DG3 grounding, guard placement + scope, residual disposition). Store touch: the seam writes typed entity records + ENFORCED RELATE edges via the shared `apply`/`execute_transaction` (ONE IMPLEMENTATION, mutation-proven). Residual bounds filed with re-open triggers: **#375** (cli/scout full ingest lifecycle deferred to packet 51), #373 (P8 reach 3-root hand-list), #374 (P13 purge-outcome not channel-read), #377 (R5 reconcile cost-gate, measure-then-tune), #378 (declared-tables union cloned ×3). Commits `562c9bd`(RED contract+stubs)+`91fc30e`(GREEN)+`06b7142`(harden); reports → `receipts/2026-08-15-packet47a/`. **NEXT = packet 55** (scraper transmute [∥-safe]; deps 47a ✅).
- **2026-08-15 — packet 59 (migrate MCP server → standalone `fastmcp` 3.x) MINTED; COMMIT-ONLY, BUILD NOT STARTED.**
- **2026-08-16 — packet 59 DONE + DEPLOYED (STANDALONE, live-verified).** Commit `130fa16` (~4470 del:
  `_ProcessLifespanGuard`/`_EagerStartupLifespan`/`TracingFastMCP` deleted → fastmcp native `lifespan=` +
  `ToolTraceMiddleware`; FP-07 re-homed as the named `_eager_build_with_retry` per **①-OC ACCEPT**;
  `host_origin_protection` on, `LORE_ALLOWED_HOSTS=*` operator-ruled wildcard; `mcp` transitive via fastmcp).
  Full tdd cycle: spike (3 §6.6 GO, lead re-run) → contract (2 adversary passes) → build → 3-agent Phase-7
  audit (**blindread caught F1 transport_session-NULL** + **coldaudit caught the transport-mode gap** —
  wire behaviours the gates can't see; PR93 lesson live) → fix-wave → lead re-verify **450f/9859p
  zero-new-delta**, ruff clean, in-image conformance PASSED. Image `a8daccf` (rollback `pre-59-rollback`);
  lore-lore recreated (`LORE_VERSION=130fa16`), `lore_index` live-verified. Conformance-harness fix `24c1863`.
  Findings #381 (fixed) / #382 / #383; **#184 resolved**. Reports → `receipts/2026-08-16-packet59/`. **Unblocks 39.**
  Investigation→decision→formalization arc (Opus lead; 4 scouts): blast-radius coupling map (+§7 packet-39 forward-compat — every private `mcp` reach gets a public fastmcp replacement), 4.0-scout (4.0 = LARGE delta onto mcp-SDK-v2 + the sessionless protocol → STRENGTHENS 3.x-now/4.x-later), a **VERIFIED GO spike** (lead re-ran the harness: fastmcp 3.4.7 `on_call_tool`/`on_list_tools` middleware gates ON THE WIRE, and packet-39's `get_access_token()` seam SURVIVES stateful+stateless — retiring §7's highest-risk assumption), and an EXHAUSTIVE hand-roll inventory (14 dispositioned; top = ~150 LOC `_ProcessLifespanGuard`+`_EagerStartupLifespan` DELETE; surfaced the silent `transport_security`-unset Host/DNS-rebinding gap). RESOLVES **#184** re-open trigger (b) (packet 39 = 2nd non-telemetry `call_tool` consumer; #102). Operator rulings D1–D4: **STANDALONE deploy · BUILD NOW (immediate next, ahead of wave-D) · 39 `Depends on` += 59 · `mcp` transitive** (full `fastmcp` umbrella, NOT `fastmcp-slim`; 2 build-time caveats). Design `docs/design/2026-08-15-fastmcp-3x-migration.md`; **kickoff `docs/plans/v2/kickoff-packet59-fastmcp-migration.md`** (comms doctrine + Fable sidecar); receipts → `receipts/2026-08-15-fastmcp-migration/` (5 reports). Commits `41287c5`(scout receipts)+`aad58e8`(packet)+this(kickoff+Log). **DEFERRED, not dropped:** (a) the packet-59 BUILD — spike-gated §6.6 `[inferred]` items + standalone deploy — USE THE KICKOFF DOC; (b) the operator-approved **7-file frameworks→packages→hand-rolling** sweep (`~/.claude/CLAUDE.md` §Packages + `brief-base.md` + package-scout/tdd-contract/contract-adversary/lead-base/odoo-reuse-scout). **NEXT = packet 59 BUILD.**
- **2026-08-17 — packet 07 (store-error-honesty: CLASSIFICATION) DONE; TEST-ONLY, NO DEPLOY.** #118/#119
  turned out already-fixed at `8f24e11` (2026-07-13, inside the #102 cycle) — live-verified GREEN on
  3.2.4, resolved with no builder needed. #144's posture settled: a two-leg test guard (runtime
  `_sdk_guard` check + offline AST scan) bans any bare `.query()` carrying >1 statement, routing to the
  shared `_txn._assert_envelope_integrity` at CALL TIME (mutation-proven under attack, not a private
  clone). Operator PULLED #124's deferred (2026-07-14) DDL-coverage pin IN mid-packet — closed with a
  derived (`inspect.getmembers`) constant-level pin, and #124's row corrected (was misdiagnosed as the
  engine silently losing committed rows; reconciled against the ORIGINAL harness
  `scratchpad/102-recovery/probe_txn_control_no_sequence.py` — both probes wrapped a CREATE in bare
  `.query("BEGIN;...;COMMIT;")`, so a later-statement retryable conflict from the real auto-schema race
  never raised). Pipeline: contract → adversary (ONE INSUFFICIENT round: F0 routing-is-not-sharing +
  F1 a fabricated "5 scattered pins" count, both fixed) → build (one lead-authorized test-ordering fix) →
  cold audit **GO** (independently re-derived every claim, incl. its own F0 mutation attack in a fresh
  scratch copy). **Zero changes under `loremaster/loremaster/`** — deploy skipped as a genuine no-op
  (same precedent as 02a/03a-1/03a-2). Findings #118/#119/#144/#124 resolved. Commit `147be46`. Reports
  → `receipts/2026-08-17-packet07/`.
