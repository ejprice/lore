> Archived 2026-11-09 from the measuring session's scratchpad. `prod_memory_dump.json` (13 MB: all 286 production memory rows with embeddings) was deliberately NOT archived; regenerate it from the production store with `memlen_probe.py`. Memory ids 6d16f7f4 and d53e4404 named here were later split into one-point memories (split_from= labels).

# Memory length vs recall — measurement report (2026-11-09)

Measured by a fresh-context opus-worker for lore-0a. The harness refused the agent's own write, so lore-0a saved this file.
Lead verification: lore-0a recomputed hit@1 and hit@3 for both arms from `probe_results.json`, and they match the figures below. The code claims were checked at `memory/local.py:1105` (RRF fusion) and `:1135` (conjunctive fulltext predicate).

## Ranking path (repo HEAD eb2b771)
- `LocalMemoryBackend.recall` → `_hybrid_search` (memory/local.py:1055). It fuses an HNSW KNN arm (overfetch 40 for k=10, ef=64) with a BM25 FULLTEXT arm, using `search::rrf([...], k, 60)` (local.py:1105).
- The served score is Σ 1/(60+rank). There is no rerank, and no importance or recency weighting.
- The BM25 arm is CONJUNCTIVE: every query token must be present (`_build_fulltext_predicate`, local.py:1135), and the `code_ident` analyzer drops no stopwords. It matched 0 rows for all 15 queries in all 3 arms. Recall for natural-language questions is therefore pure vector rank: the score is 1/(60 + vector rank).
- One vector per memory. TEI pre-splits only above 8192 tokens, so both subjects are single whole-note vectors.
- The warning threshold `_MEMORY_DIGEST_WARNING_CHARS = 500` (server.py:1157) is confirmed.

## Method
- Queries were fixed in `queries.md` before any result. Subject A, 6d16f7f4 (agent `tools:` grants, ~3,025 chars): A1–A7. Subject B, d53e4404 (lore-lore deploy, ~2,147 chars): B1–B5. Distractors: D1–D3.
- All 286 live production rows, stored embeddings included, were copied into throwaway TEST-store databases (`_surreal_harness.unique_database`; schema via `ensure_ready`). Ranking used the real `_hybrid_search` and the real TEI embedder; `LORE_TEI_KEY` was loaded without being printed.
- Three databases, one changed variable each:
  - LONG: the corpus as-is;
  - ATOM_A: the corpus minus A, plus 7 A pieces;
  - ATOM_B: the corpus minus B, plus 5 B pieces.
  All three were dropped.
- The split: each body paragraph appears verbatim in exactly one piece, behind a short prefix. Pieces are 332–771 chars, so 7 of the 12 are still over 500.

## Controls (pass)
- The copy's LONG ranks match production lore_recall for 15/15 queries.
- Re-embedding each long note gives cosine 1.000000 against its stored vector.
- The test HNSW index definition is byte-identical to production's.
- HNSW rank equals brute-force cosine rank in every case.

## Results (k=10)
| q | LONG rank | LONG cos | ATOM rank | ATOM cos |
|---|---|---|---|---|
| A1 | 2 | 0.592 | 2 | 0.567 |
| A2 | 2 | 0.561 | 2 | 0.554 |
| A3 | 2 | 0.621 | 2 | 0.619 |
| A4 | 2 | 0.536 | 1 | 0.630 |
| A5 | 2 | 0.374 | 1 | 0.574 |
| A6 | 5 | 0.404 | 1 | 0.627 |
| A7 | 1 | 0.529 | 1 | 0.559 |
| B1 | 9 | 0.520 | 3 | 0.581 |
| B2 | 2 | 0.555 | 1 | 0.721 |
| B3 | 1 | 0.594 | 1 | 0.643 |
| B4 | 1 | 0.548 | 1 | 0.616 |
| B5 | 1 | 0.580 | 1 | 0.726 |

| | LONG | ATOMIC |
|---|---|---|
| hit@1 | 4/12 | 8/12 |
| hit@3 | 10/12 | 12/12 |
| mean target cosine | 0.535 | 0.618 |

- Distractors: neither subject is in the top 10 for D1–D3 in the LONG arm. In the ATOM arm, one false positive: piece B3 at rank 6 for D3.
- A1–A3 sit at rank 2 in both arms because a newer superset memory (46ec9b5e) takes rank 1. That is a ceiling set by the competition, not by length.

## Confidence and bounds
MEDIUM-HIGH that one point per memory improves rank on this path. Bounds:
- 12 queries, 2 subjects, one embedder.
- The queries were written after reading the notes.
- The BM25 arm never fired. For short exact-word queries, where it can fire, long notes may be favoured; that case is untested.
- No length threshold was measured. Pieces were 332–771 chars, so the data supports "one point per memory", not "under 500 chars".
- This is not a re-measurement of #31's digest store.

## Side effects and flags
- lore_recall is NOT read-only: `_reinforce` (local.py:931 / :1210) adds 0.05 importance to every returned row. The measurement's recalls sent up to ~159 bumps to production; most of those rows were already at 1.00. Importance does not affect ranking. Existing finding: #578.
- The served recall score carries no relevance information. It is 1/(60+rank), because the conjunctive BM25 arm is empty for question-shaped queries, so a 0.37-cosine match and a 0.72 one look alike.

## Recommendation
Split multi-point memories into one point per memory. Re-word the 500-char warning around "multiple points per memory" rather than raw length.

Receipts (this directory): queries.md, atomic_pieces.json, prod_memory_dump.json, probe_results.json, long_arm_haiku.tsv, memlen_probe.py, analyse.py.
