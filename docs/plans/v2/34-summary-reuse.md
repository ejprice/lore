# 34 — Semantic summary reuse (operator-promoted 2026-07-11) (formerly PKT-26)
size ~0.25 wu · wave F · depends: packet 29 loresage (synthesis); packet 35 aggregates helpful, not blocking
law: DESIGN-LAW §1 (signal-per-token is the currency), §3 (measured thresholds; disclosure), §10 (generated-text honesty) · DEPLOY: yes

## Mission
The Spectron T2 idea, lore-shaped: reuse LLM-synthesized answer summaries across
semantically-similar queries, with DETERMINISTIC invalidation via citation hashes.
Benefit lands in the ruled client currency: a good summary answers intent in ~100
tokens where the raw hit set costs 1–2k, and saves the follow-up turns.

## Ruled constraints (operator, 2026-07-11)
- Serving form: **`(ai summary, derived <date>, N sources)` + its citations,
  ADDITIVE alongside live hits — never replacing them, never inside source fences.**
- Render-memoization flavor (5a) is DROPPED — do not build latency caching here.

## Scope IN
- **Post-hoc synthesis, never blocking**: after a response ships, a background
  loresage job writes a compact rollup of what it established, stored with its full
  citation set (chunk keys + content hashes) + query embedding as the semantic key.
- **Match**: cosine against the stored key above a MEASURED threshold (survey-derived
  per the floor-calibration pattern — never guessed; the per-corpus calibration
  machinery from packet 11 is the template).
- **Invalidation, deterministic**: serve only while EVERY cited hash is live-current;
  one drift → drop + queue regeneration. (Shares the drift machinery with packet 33.)
- **Budget/caps**: synthesis is rate-limited + budget-capped via the loresage config;
  cache rows are derivable data in the store (§14-clean) with size/age eviction.
- **Adoption gate**: 35-pair bar re-run — accuracy holds, tokens-per-correct improves;
  transcript check that summaries are used, not distrusted (the #7 trust lesson).

## Scope OUT
- Any latency/render memoization (dropped). Any serving of a summary whose citation
  set cannot be hash-verified (fail to live hits, silently — no, LOUDLY: the summary
  lane just absent, live hits unchanged).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
loresage live (packet 29); if packet 35 landed, pull its repeat-query aggregates to pick
the synthesis targets; else start with map/impact-shaped orientation queries.

## Exit
Full gates + cold audit; deploy BOTH; smoke: ask, get live hits; re-ask a paraphrase,
get the marked summary + citations above live hits; touch a cited file, re-ask,
summary gone until regenerated; INDEX row + Log.
