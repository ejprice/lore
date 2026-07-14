# 35 — Trace deepening + the trace_monitor backstop (formerly PKT-20)
size ~0.30 wu →split at kickoff (sizing law) · wave F, LAST (re-waved 2026-07-14; external-review ordering preserved: traces before security/UI — this packet gates waves S and G) · depends: v1.0
law: DESIGN-LAW §1 (client law), §8 (pull-only) · spec: MASTER-PLAN §3 (friction backstop) + LORE_EXTERNAL_REVIEW.md gap 3 · DEPLOY: yes

## Mission
Today's trace rows are tool observability, not retrieval diagnosis: they cannot say
whether the vector arm, BM25, RRF, enrichment, memory boost, or reranking produced a
bad result (external review, gap 3). Deepen traces into per-stage records, then light
up the server-side friction backstop that has waited on them since the plan's §3.

## Scope IN
- Per-stage retrieval records linked to returned chunk/memory keys: which arm surfaced
  each hit, pre-fusion cosine, BM25 rank, post-enrichment disposition. Async writes,
  never in the read path's latency budget; sampling/caps measured, not guessed.
- **Serve-side facts in the record (gap-3 discussion, 2026-07-11):** served keys,
  render-section sizes, elision counts — the response-trace value WITHOUT storing
  bodies (the eval harness owns transcripts).
- **Usage-proxy aggregates:** served key followed by same-session get_symbol/read =
  "used"; rapid re-query variants = "not satisfied". Aggregated to measure render
  usefulness and feed DESIGN decisions — **explicitly never feeding ranking**
  (DESIGN-LAW §3 disclosure law + no ground-truth outcome signal).
- **Calibration synergy:** live per-hit cosine distributions from traces are exposed
  to the #83 calibration engine as a drift-evidence input (packet 10's design agent
  decides whether they inform or replace periodic re-surveys).
- Zero-hit and retry-storm aggregates in lore_index's trace section.
- **trace_monitor backstop** (created_by=trace_monitor): auto-file candidate friction
  findings from patterns agents won't report — same params_hash re-called with rapid
  variations; zero-hit followed by tool abandonment. Agent narratives + auto candidates
  feed ONE findings queue.
- Design note recording what this is NOT (Spectron trace memory: no decision/response
  traces, no ranking feedback) — honest positioning per the external review.

## Scope OUT
- Trace-feedback ranking (learning-to-rank) — v1.2+ deferred, needs eval infra.
- Prometheus /metrics — optional, operator opt-in only.

## Entry check
Trace table columns (token_cost, model) present since P2 — verify live; the standing
bar's transcripts identify one known-bad query to use as the diagnosis smoke.

## Exit
Full gates + cold audit; deploy BOTH; smoke: the known-bad query's trace answers
"which stage lost it" in one read; a synthetic retry-storm auto-files a friction
candidate; INDEX row + Log.
