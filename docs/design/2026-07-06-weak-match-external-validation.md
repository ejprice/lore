# Weak-match design — external validation (deep-research digest)

**Date:** 2026-07-06 · **Trigger:** operator concern about the weak-match design's
thinking → 104-agent deep-research workflow (5 search angles, 22 sources fetched,
25 claims adversarially verified 3-vote each: 21 confirmed, 4 refuted).
**Raw result:** preserved as `research-weakmatch-validation.json` in the session
scratchpad; findings below cite primary sources only.
**Design under test:** docs/design/2026-07-06-weak-match-discrimination.md §7.4.

## Verdicts per design element

**(3) Stop featuring the fused RRF score — CONFIRMED, high confidence.**
RRF score non-informativeness is documented, by-design behavior in every major
production system: Elastic, Weaviate (rankedFusion), Qdrant, and Azure AI Search all
compute `1/(k+rank)` from rank positions only. Azure documents the fused-score
ceiling (~1/k per fused arm) that exactly matches our measured ~1/61–2/61 band, and
explicitly warns hybrid RRF output is "not conducive to minimum thresholds."
Elastic frames magnitude-blindness as the feature. 8 claims, all verified 3-0
against live vendor documentation.

**(1) Per-hit raw cosine substrate — CONFIRMED, and extensible.**
Azure's documented remedy for RRF opacity is unpacking per-arm subscores, with the
stated use case being minimum thresholds on the raw vector similarity — the same
move we made, productized. The vendors' deeper fix is magnitude-preserving fusion
itself: Weaviate's relativeScoreFusion (default since v1.24, "retains more
information"), Qdrant's DBSF. **Named future upgrade:** evaluate a relative-score
fusion swap for the SurrealDB arm composition. Caveat carried from verification:
per-hit claim-free display to an LLM consumer is inference-supported, not directly
attested vendor practice (see element d).

**(2) Hedged cosine-floor absence verdict — NEED CONFIRMED, MECHANISM CONFIRMED,
PRINCIPLE QUALIFIED.**
- Need: ICLR 2025 (Google) shows Gemini 1.5 Pro / GPT-4o / Claude 3.5 answer
  instead of abstaining on insufficient context (RAG context REDUCED Gemini's
  abstention 100%→18.6%); TMLR 2025 shows retrieval makes generators MORE
  overconfident. The signal must come from the retrieval side.
- Mechanism: production floors are applied to raw pre-fusion vector similarity
  (Azure `vectorSimilarity` threshold, pre-fusion), never to RRF output — our
  floor placement matches the only documented vendor pattern.
- Qualification: the answerability literature detects unanswerability by CONTENT
  classification, not similarity floors, and warns answerability "is difficult to
  model in terms of model confidence." Steck et al. (WWW 2024) prove cosine on
  some learned embeddings can be arbitrary; for contrastively-trained normalized
  embedders (voyage-4's class) it is documented caution, not proven arbitrariness.
  The design survives because it carries exactly the mitigations demanded: hedged
  advisory wording, corpus-measured (never universal) floor, pre-registered bars,
  identifier carve-out. **Binding amendment adopted: the floor is valid only for
  the exact embedder + prompt configuration it was measured on — any embedding
  model or prompt_name change invalidates `_COSINE_WEAK_MATCH_FLOOR` and requires
  a survey re-run** (voyage-4's asymmetric query/document prompts make the
  distributions configuration-specific).
- Verification also REFUTED (0-3) the claim that surfacing a sufficiency signal
  measurably improves outcomes — the notice is justified by documented
  failure-without-signal, not proven benefit-with-signal. Honest status.

**(c) Calibrated relevance magnitude — post-fusion reranker is the production
path** (Azure semantic ranker, separate bounded 0–4 score after RRF merge);
lightweight alternative when a cross-encoder is too heavy: a small trained
passage-utility predictor (110M BERT, AUROC 0.79 vs 0.70 for p(true), TMLR 2025 —
needs per-task training data, degrades OOD). Both are named FUTURE upgrade paths;
neither blocks the shipped design.

**(d) Displaying scores to tool-using LLM consumers — OPEN.** No surviving direct
evidence either way in the literature or vendor practice. Our three-model informant
consult (2026-07-06-weak-match-discrimination.md §3–5) remains the only direct data
on this question that we know of.

## Outcome

The design shipped as specced and measured: substrate live, verdict adopted at
floor 0.5828 on the corrected D3 carve-out (re-run receipts in the adoption
commit, 94a9568). Ledgered follow-ups from this validation: relative-score fusion
evaluation; floor↔embedder-fingerprint invariant; reranker/utility-predictor as a
future calibrated-magnitude layer.

Key sources: learn.microsoft.com/azure/search/hybrid-search-ranking ·
elastic.co reciprocal-rank-fusion reference · weaviate.io hybrid-fusion blog +
docs · qdrant.tech hybrid-queries · arxiv 2411.06037 (sufficient context, ICLR'25)
· arxiv 2502.18108 (utility predictor, TMLR'25) · arxiv 2407.18418 (abstention
survey, TACL) · arxiv 2403.05440 (Steck, WWW'24).
