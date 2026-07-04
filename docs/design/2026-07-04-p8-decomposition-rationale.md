# REPORT — P8 execution decomposition (Fable planning review, 2026-07-04)

Deliverable landed in the plan (`get-an-understanding-of-ancient-sloth.md`, block
"**P8 EXECUTION DECOMPOSITION (Fable review, 2026-07-04)**", inserted immediately
after the P8 amendment blocks). This report records the sizing evidence, the
dependency analysis, and the alternatives rejected.

## 1. What I counted from the P7 evidence (the window-unit yardstick)

Source: `scratchpad/P7-KICKOFF-PREP.md` (the live state file of the single P7
orchestrator window, close header + four dated state blocks) and lore-v2-RESUME.md.

One P7 window (**defined as 1.0 window-unit**) demonstrably held:
- **~25 agents** spawned/ground-truth-verified/released (11 by cycle-1 close alone;
  contract/green/fake/audit/scout/calibration agents through four waves).
- **14–15 commits** (close header: "14 commits from 0fa738b"; brief says 15).
- **~6 contract/green build cycles**: doubles+parity, MemoryBackend contract, local
  Surreal backend, task ledger + CAS tools, cutover, P7-tail polish — plus the
  token-survey side-stream and the DI scout.
- **3 cold audits + 2 fix cycles** (wave-1 audit FIX-FIRST → fix cycle 1 →
  re-audit SHIP; cutover audit; polish audit), each audit a fresh opus context.
- **2 redeploys** (image rebuild → stop/rm/run → MCP smoke; smoke_v2 17/17 at close).
- Continuous operator conversation (scope rulings, GO gates, calibration
  authorization, task #6 P7-vs-P8 call).

And the window was **"far along" at close despite aggressive externalization**
(REPORT-*.md protocol, scratchpad state files, TaskStop-on-release). So 1.0 wu ≈
6 build cycles + 3 audits + 2 fix cycles + 2 redeploys, with no slack left.

**Sizing rule applied:** each component ≤ ~0.7 wu ≈ **≤4 build cycles + ~2 cold
audits + 1 fix cycle + 1 redeploy**, leaving the mandated margin for audits going
FIX-FIRST, operator conversation, and friction triage. Per-component cycle counts:

| Comp | Build cycles counted | Est. wu |
|---|---|---|
| P8a | kùzu surgery (1 big) + qdrant purge chain (1) + hygiene trio #5/#7/#9 (1 combined small wave) + trace writes (0.5) + baseline run (script, no cycle) | ~0.6 |
| P8b | verify+resolver (1, opus) + diff (1) + findings (1) + store-backed read (0.5) | ~0.65 |
| P8c | calibration engine (1.5: config gate, boot measure, caches, retry loop) + scout (1 design agent + operator session) | ~0.45 |
| P8d | surface consolidation (1 big) + teaching-miss family (1) + instructions block (0.5) + eval rewrite ~35 pairs + A/B runs (1) + FRICTION migration (0.25) | ~0.7 |
| P8e | role wiring + creds (1.5) + Containerfile/astroid-shadow (0.5) + approved config subset (≤1, operator-bounded) + drills + split e2e (1 heavy verification wave) | ~0.65 |
| P8f | lore-deploy rework (1) + migrate verb + N1/N2/N3/N6 machinery (1.5) + live DI run (0.5, operator co-driven) + §8.5 receipts + ship close (0.5) | ~0.6 |

**Total ≈ 3.65 window-units.** P8d and P8e sit at the ceiling; both carry explicit
valves (P8d′ fix window if the A/B gate fails; P8e′ if the operator approves a
large config-disposition subset).

## 2. Dependency analysis (what forced the order)

Hard edges, all honored by P8a→P8f:
1. **Eval baseline BEFORE the surface flip** (§8.3): the 23 tool-name-agnostic
   pairs must run against the live pre-flip surface. Recorded at P8a (earliest,
   before any surface drift); P8d's entry criteria require the receipts.
   House rule applied: re-measure even if an older baseline exists.
2. **Findings surface (#2) before**: (a) FRICTION.md retirement (the file's own
   header says it seeds the table); (b) #12's drift auto-file ("rides the P8
   findings surface"). Hence P8b before P8c and before P8d's retirement step.
3. **Calibration (#12) BEFORE the flip**: the re-amendment DECIDES budgeted calls
   take the caller's model name as a parameter, and defaults re-denominate
   (search ≈650→1100). Those are part of the final tool schemas — flipping first
   would reopen the surface for a second schema-breaking deploy. Hence P8c → P8d.
4. **Consolidation before instructions finalization**: the instructions block and
   per-tool descriptions reference the final names/ladder — same window (P8d),
   consolidation first within it.
5. **uuid5 helpers move before memory/store.py + Qdrant test deletion** (#8's own
   gate) — sequenced inside P8a, impact+grep gate before each deletion.
6. **#13 scout dispositions before their implementations** (P8e code, P8f
   scaffold/migrate implications) — scout runs in P8c, operator strikes the table
   there.
7. **Roles/Containerfile before migrate** (#11 swaps containers built by P8e's
   image; `start` refuse-and-point guards the reworked verbs) — P8e → P8f.
8. **Migration design's §8 operator questions (1–4) answered at P8f entry** —
   N1 posture, namespace-vs-port, serving window, DI dry-run-first.

Soft ordering (chosen, not forced): the purge (P8a) goes FIRST — it shrinks the
tree every later audit reads, removes the dual-store boot requirement (first
independently observable milestone: a Qdrant-free boot), and clears vestigial
consumers before new code piles on. Trace writes ride P8a (store plumbing, no
tool dependency) specifically to keep P8b under the ceiling.

Natural stopping points: every component ends suite-green + cold-audited +
committed, and five of six end with a redeploy of the live dogfood server (P8e's
observable is the demonstrated split topology + the still-live single-node
deploy). Each exit writes the next window's resume doc in the proven
lore-v2-RESUME.md shape.

## 3. Alternatives rejected

- **3 mega-components (surface / infra / ship):** each ≈1.2+ wu — exceeds the
  demonstrated single-window load outright; the P7 evidence says a window at 1.0
  closes with zero margin.
- **Instructions block as its own later component:** shipping a renamed surface
  without its doctrine violates the deployable-checkpoint criterion (agents would
  face new names with no ladder/teaching text); kept fused to the flip.
- **Calibration after the flip:** reopens frozen schemas (model param +
  re-denominated defaults) — two breaking deploys instead of one. Rejected per
  dependency 3.
- **Deletions last ("cleanup at the end"):** wastes every intermediate audit on
  dead code, keeps the Qdrant boot requirement alive across four windows, and
  risks new accidental consumers of doomed modules. Purge-first wins.
- **Fusing P8e+P8f (topology + migration):** both near-ceiling, and the DI
  migration is a live operation with an operator GO/NO-GO and a rollback story —
  it deserves a fresh window with full margin, not the tail of a heavy build.
- **New-verbs split into two components (verify/read vs diff/findings):** would
  make 7 components of ~0.3 each — handoff overhead (resume-doc authoring, fresh
  orchestrator boot, state re-verification) starts dominating below ~0.4 wu.
- **N4 ledger cursor for migration tail-catch-up:** already rejected in the
  design doc (membership-by-id makes catch-up incremental); recorded so no
  component re-raises it.

## 4. Flagged as not fitting the component shape

- **DI doc-content import** (DECISIONS.md/GOTCHAS.md/salvaged_memory.md →
  kind-tagged memories): explicitly out of #11's scope per the amendment; a
  per-project content migration the operator schedules separately.
- **Spectron backend re-decision:** invite-gated, unschedulable; local backend
  shipped in P7 regardless.
- **§8.8 UI smoke:** P10 scope, not P8.
- **v0.3 astroid installed-vs-mounted container fix:** folded as a VERIFY-then-fix
  item into P8e's Containerfile wave (liveness verdicts depend on it), but if it
  reproduces deeply it may need its own escalation — surfaced there.
