# 33 — Memory reconciler + maintenance engine (operator-directed 2026-07-11) (formerly PKT-25)
size ~0.35 wu · wave F · depends: v1.0 (deterministic tier); packet 29 loresage (LLM tier)
lead: **Opus; Fable design sidecar at the CONTRACT-TIME autonomy fork** (operator roster 2026-07-14 — INDEX; sidecar mechanics in repo CLAUDE.md → Orchestration)
law: DESIGN-LAW §9 (memory contract), §10 (generated-text honesty applies to proposals), §14 · TDD contract pause for the autonomy ruling · DEPLOY: yes

## Mission
Operator ruling (2026-07-11, external-review gap-2 discussion): author discipline is
NOT a durability mechanism — "I've seen memory drift, and I've seen Claude ignore or
forget to update things." Machine-maintain the memory table: detect rot, repair what
is deterministically repairable, propose what needs judgment, escalate the rest.
Supersedes my earlier "agents manage supersession explicitly" assessment (wrong — it
contradicts the friction-masking evidence lore itself is built on).

## Scope IN — deterministic tier (no LLM; can ship before packet 29)
- **Proactive drift sweep**: promote the recall-time ref-hash check to a scout-side
  sweep — a memory nobody recalls must still get its drift flag. Drifted rows render
  flagged AND appear in a maintenance view.
- **Dead-ref detection**: memory cites a chunk/symbol that no longer exists → graph
  lookup; auto-demote (stops boosting/injecting per §9) + suggest the nearest current
  symbol (rename-following via graph + embedding similarity).
- **Near-duplicate clustering**: embedding similarity across live rows → consolidation
  candidates (flag only in this tier).
- **Machine-minted uncertainty (the #4 pull-back-in)**: unresolvable conflicts/dead
  refs mint `kind=uncertainty` records, `created_by=reconciler`, linked to the
  affected rows.
- **Escalation**: everything the engine flags but cannot fix files into the findings
  queue — one maintenance loop for code and memory alike.

## Scope IN — LLM tier (loresage; write-side ONLY — the read path stays LLM-free)
- Contradiction adjudication among flagged candidates → supersession/invalidation
  PROPOSALS; consolidation merge drafts; drift-repair drafts. All non-destructive,
  provenance-stamped, `(ai)`-marked where rendered. **Every proposal carries its
  verdict AND rationale** (the decision-trace requirement, gap-3 discussion
  2026-07-11) — an unexplained machine decision is unauditable and unreviewable.
- **Mechanism RULED (operator, 2026-07-11): loresage SINGLE-SHOT calls, not an
  Agent-SDK loop, not consumer-tasking.** The deterministic tier assembles the full
  evidence bundle (memories + cited chunks at current hashes + graph facts); the LLM
  call is prompt→structured-verdict on that bundle. Agent-SDK upgrade of this one seam
  is a contained later option if adjudication quality misses WITH the bundle. The
  visible propose queue remains the consumer-resolvable fallback lane — the machine
  never waits on an agent showing up.

## OPERATOR FORK (contract-time ruling — pause the TDD cycle for it)
Autonomy level per action class: **flag-only** / **propose (agent or operator
approves)** / **auto-apply with full audit trail** (supersession makes auto-apply
reversible). Likely split verdict: auto-apply for deterministic demotions, propose for
LLM outputs — present with receipts from the deterministic tier's first live sweep.

## Scope OUT
- Reflection (session-experience synthesis) — harness-owned unless the operator says
  otherwise. Any read-path LLM involvement — permanently out (anti-hallucination prime).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
`lore_recall` drift/demote render behavior at HEAD (the §9 pins are the contract this
engine must not break); packet 32's expiry sweep state (this engine and packet 32 share the
sweep scaffold — build once).

## Exit
Full gates + cold audit; deploy BOTH; smoke: a deliberately-drifted memory, a
dead-ref memory, and a near-duplicate pair each get detected + dispositioned per the
ruled autonomy levels; findings filed for the escalation class; INDEX row + Log.
