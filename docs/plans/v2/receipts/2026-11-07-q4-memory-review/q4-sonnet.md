# Q4 — Sonnet answer (verbatim summary + key points; delivered as text, Write refused for subagents)

brief-base v25 read. lore MCP down → grep/Read at HEAD 5562925; Agent Memory claims are the study's ("per study"); nothing measured.

## SUMMARY
- U1 importance: DROP reinforcement now (HIGH); do NOT fold category decay into ranking (MED); SERVE AGE (created_at/expires_at) so the consumer judges freshness; stop rendering `importance` until something ranks by it (MED).
- U2 kind→category: no stored category (MED); if ever needed, one derived fn `category_of(kind)`: ongoing=context, decision=identity, fact/gotcha/uncertainty=knowledge. `decision` = identity.
- U3 Stop-hook capture: NOT now (HIGH); reopen on first measured durable fact lost for want of a lore_remember + a render that serves provenance.
- D1 drop `_reinforce` + REINFORCEMENT_STEP: DROP (HIGH), with removed-behavior inventory.
- D2 `lens`: DROP from protocol/impl/fake/pin (HIGH) — MCP tool never exposed it; building it would duplicate read_filter scoping.
- D3 `memory_category`: DROP column, RecalledMemory field, `_row_to_recalled` read (HIGH); store-ref migration rule + dirty-store verify.
- D4 Spectron intent: DROP prose, KEEP the `MemoryBackend` Protocol (HIGH); supersede stale "SPECTRON STATUS UPDATE (2026-07-23)" lore memory.
- A1 provenance-safe supersession: ADOPT mapped to `trust` (authoritative/experiential) (MED-HIGH) — literal source.kind is always "operator" so it would never fire. Refuse-vs-mint = operator fork; recommends MINT `uncertainty`; response must name the outcome.
- A2 auto-recall hooks: ADAPT (MED); cost M + identity ruling (hooks have no registered Subject; recall needs a verified capability). SessionStart = query-less standing set (live decision/gotcha, capped, bound-stated) first; UserPromptSubmit only after measuring tokens/precision; fail loud.
- E1 (HIGH): render serves no created_at/valid_from/expires_at/supersedes/superseded_by/trust though RecalledMemory carries them → serve them (S).
- E2 (MED-HIGH): lore_recall exposes no include="superseded"/as_of though backend implements both → audit trail unreachable by agents; expose or render a counted bound.
- E3 (HIGH, moot after D1): reinforcement isn't in the ledger → rebuild/restore silently resets served importance.
- E4 (MED): later — chain read, LLM-free write-time dup/supersession candidate flag, derived_from, housekeeping report.
- E5: nothing else in lore becomes redundant; Agent Memory is unusable as a backend.

## Code facts it verified (grep/Read)
- Kinds = 5 (IMPORTANCE_DEFAULTS_BY_KIND): decision 0.9, gotcha 0.8, ongoing 0.7, uncertainty 0.6, fact 0.5.
- recall orders by fused rrf_score then `_reinforce` (UPDATE … importance = min(1, importance+step)) under write_guard; ledger untouched.
- **lore_recall is registered `_READ_ONLY_ANNOTATIONS` (readOnlyHint/idempotentHint true) while it writes — a false annotation today.**
- lore_remember `trust` is caller-asserted; source kind always "operator". No invalidate tool; only `remember(supersedes=)` closes a note.
- ONGOING_DEFAULT_TTL 7 days already ≈ Agent Memory `context` expiry.

## U1 reasoning
importance 1.00 reads as "matters/reliable", is neither (study: 15/16 served at 1.00; ranking ignores it) → unnamed-wrong. Decay as multiplier: knowledge ×0.995/day = 0.86@30d, ~0.16@1y; with rank-based RRF scores (spread unmeasured) GUESS it would reorder by age, a silent heuristic. lore has better staleness signals (explicit supersession, lore_ref drift). Fork: (a) read-time decay in ranking (measure first; render must name it; one fn feeds rank+render) vs (b) stop serving importance + serve age — picks (b).

## D1 removed-behavior inventory
+0.05 bump (dropped: ranks nothing, saturates, not durable) · read-path write under write_guard("_reinforce") (dropped; recall becomes truly read-only → readOnlyHint true) · governed-write allowlist entry `_REINFORCE_ENTRY`/`_effect_reinforce` + its test in test_memory_enforcement_63b_ia.py (dropped with site) · pins: whole test_memory_reinforce_63a_iv.py, test_bump_persists…, test_reinforcement_caps_at_one, REQUIRED_REINFORCEMENT_STEP (test_memory_backend.py), fake `_reinforce` (_memory_fakes.py), _governed_contract.py commentary · "recall never bumps an unreadable row" preserved trivially · NEW replacement pin: recall issues NO mutating statement (remember = positive control) · docstrings rewritten (bare sweep: reinforc, bump, importance) · importance column stays (authored value), no migration. Caveat: grep-derived; lore_impact before deleting.

## A1 design points needing ruling
(a) refuse vs mint `uncertainty` (rec: mint); (b) minted row's owner/scope under 63 governance + deterministic id from both ids; (c) tool must name the outcome (today returns id only); (d) optional derived_from. Bound: trust is caller-asserted → guards accident not hostility; enforce at the shared backend seam.

## Build order
1. Cleanup packet D1–D4 (deletions; D1 inventory = contract spine; pin "recall issues no mutating statement").
2. E1 + E2 bound, then A1.
3. A2 after identity ruling + token/precision measurement.

## Not measured
No lore_impact/search; vendor docs unread; RRF spread unmeasured; hooks-in-subagents unverified (GUESS).
