# Orchestration context retrospective — P8d session (2026-07-06)

**Author:** p8d-lead (Fable, the session's orchestrator), operator-directed.
**Data basis:** this session — ~21 agent lifecycles (6 wave/fix builders, 5 auditors,
1 scout, 1 migrator, 1 eval author, 1 eval runner, 1 designer, quick-win/probe/misc),
15 commits, 4 cold audits, 2 full redeploys, 1 A/B gate run. Estimates are honest
approximations; I cannot meter my own window precisely.

## 1. Where the lead's context actually went (ranked)

| # | Sink | Est. share | Nature |
|---|---|---|---|
| 1 | Reading agent reports & audit reports for verification | ~30–35% | ~10 full reads at 60–270 lines each; needed for rulings, but most lines were receipts I only spot-checked |
| 2 | Composing spawn briefs | ~20–25% | ~21 briefs × 500–1500 words; ~40% was standing-law boilerplate (now killed by brief-base v1), the rest mission content often TRANSCRIBED from docs I'd already read (scout report → builder briefs) |
| 3 | Boot state (resume doc, plan, design law, baseline, memories) | ~15% | Load-bearing; not waste |
| 4 | My own verification runs (gate tails, diffs read, greps, polls) | ~10% | Tails are cheap; full-diff reads are the cost. Two self-inflicted wounds: a `cd` that poisoned a command chain, and a piped pytest that hid "no tests ran" |
| 5 | Ledger/findings bookkeeping | ~5% | ~40 single-row MCP calls (create/claim/transition/acknowledge/resolve), each burning a call + result for one row |
| 6 | Stale idle notifications & duplicate completion messages | ~3–5% | ~25 injected messages; each also costs a full turn of mine to dismiss |
| 7 | Deploy/process operations | ~3% | Fine |

Two structural observations:
- **The same content crosses my window up to four times**: I read a source doc → transcribe
  into a brief → the agent's report restates it → I re-read the report to verify. Sinks 1+2
  are one problem: *content transits the lead instead of flowing agent-to-agent through disk*.
- **Push is the enemy; pull is fine.** Everything push-shaped (teammate messages, idle
  notifications) is either noise or arrives stale behind the artifact. Everything pull-shaped
  (report files, the state file, ledgers, bounded watches) worked. The lead's ideal inbound
  is: *nothing, until I ask, and then a compact rollup*.

## 2. Short-term fixes (implementable now, before any lore feature)

**F1 — Structured report contract (brief-base v2).** Every report MUST open with a capped
summary block: receipt line · state (done/blocked/deviation) · deviations list (one line
each) · decisions-needed list · receipts as file:line POINTERS (never re-pasted). The lead
reads the block always, the body only on demand (rulings, audits, spot-checks). Expected
saving: half of sink 1.

**F2 — Spec-pointer briefs.** Proven twice this session (scout report → wave briefs went
through my window; designer spec → builder briefs will not). Rule: any content that exists
in a disk artifact is POINTED AT ("execute SPEC 1 of <file>"), never transcribed. The
scout/designer writes once; N builders read directly. Expected saving: most of sink 2's
remaining cost.

**F3 — Delegated verification mechanics.** A cheap verifier agent re-runs the receipt
checklist (gates, greps, string probes) and reports one line per item + failures verbatim.
The lead keeps judgment reads (risky hunks, audit verdicts, deviation rulings) and stops
re-running mechanical receipts inline. Guard: the verifier's "all green" is a claim —
the lead still spot-checks one item per batch, randomly chosen.

**F4 — Batch ledger etiquette.** Until lore grows batch ops (below): group transitions at
cycle close into as few calls as the API allows; never interleave single-row bookkeeping
through a build cycle.

**F5 — Notification discipline (already law, restated).** A stale notification for an
already-stopped agent gets zero tool calls and a one-line dismissal. Codified in the
comms section.

## 3. Lore-native candidates (for the fresh-Fable review to pressure-test against the plan)

**L1 — Orchestration rollup read (`lore_tasks action=rollup` or a `lore_fleet` view).**
The lead's poll: ONE call returning "since <cursor>: N tasks transitioned (ids→states),
M findings filed (numbers+subjects), K reports registered (paths)" — compact, rendered,
cursor-based. Replaces reading N individual results. Fits the plan's render doctrine
(summarised value objects, never dumps) and rides tables that already exist (task,
finding). The operator's "message bus" instinct, made pull-based and durable — a push
bus would re-create the advisory-inbox problem inside lore.

**L2 — Batch mutations on task/finding ledgers.** create-many (deps wired), transition-many,
acknowledge/resolve-many with per-item notes. Cuts sink 5 by ~5×. Schema-neutral.

**L3 — Report registration (`lore_report register/list`).** Agents register their report
(path, agent, phase, summary-block text) as a row; the lead's rollup (L1) then carries the
summary blocks — the lead reads ONE rollup instead of N files for the always-read part.
The full files stay on disk for on-demand depth. This is the durable, compact analogue of
completion messages — and unlike SendMessage it cannot be lost or arrive stale.

**L4 — Bounded await (`lore_tasks action=await`, sibling/ledger condition, timeout).**
Replaces hand-rolled bash until-loops for AGENT-side waits (the lead's own waits are fine
as bash watches). Plan already has LIVE SELECT machinery scoped for split mode (P0 S11,
P5 command rows) — this is a thin read-side wrapper, not new infrastructure.

**L5 — NOT recommended: a push message bus.** The failure mode this session was never
transport absence — SendMessage exists. It was (a) push-into-context is unreliable in this
harness by open bug, and (b) even when delivered, push pollutes the receiver's window on
the SENDER's schedule. Lore's leverage is durable pull with compact renders (L1–L3), not
another push channel. The reviewer should challenge this conclusion explicitly.

## 4. What stays with the lead regardless

Rulings on deviations, audit-verdict consumption, semantic-law questions, commit
composition, operator escalations, and the state file. None of these delegates; the goal
of F1–F4/L1–L4 is to strip everything ELSE away so the lead's window is spent here.
