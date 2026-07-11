# PKT-15 — Enrichment worker: llm_summary → BM25
size ~0.30 wu · wave F · depends: PKT-14
law: DESIGN-LAW §10 (binding: `(ai summary)` marking, never in source fences, BM25-only) · spec: MASTER-PLAN §2 · DEPLOY: yes

## Mission
The dead-reckoning generate_docstring pattern, retrieval-serving: a scout-side
background worker finds symbols lacking docstrings (chunk metadata knows), writes a
1–3 line summary via loresage, stores it provenance-stamped (model + ts) as
`chunk.llm_summary`, BM25-indexed — retrieval improves for undocumented code. Closes
the external review's "generate docstring: No" gap on lore's terms.

## Scope IN
- Worker: rate-limited, resumable (it's just rows), opt-in per project, budget-capped
  (max_per_sweep); runs after sweeps in the scout role.
- llm_summary lands in the existing BM25 index field set (the schema has carried it
  since P2 — verify, then light up).
- Render marking `(ai summary)` everywhere it can surface (search hits, get_symbol,
  read adjacency) — hostile fixtures for the new render path (repo law).
- Undocumented findings seeding (a summary can seed a kind=undocumented finding so the
  fix lands in code) — the finding side only; detectors proper are PKT-16.
- Enrichment traces stamped with token/model/cost (PKT-14's hooks).

## Scope OUT (recorded deferrals — do not build)
- Vector-side re-embedding with summaries: v1.2+ (schema-fingerprint implications).
- Docstring as a separate weighted BM25 field: PKT-17.

## Entry check
PKT-14 landed; a real undocumented module identified on the lore corpus as the smoke
target.

## Exit
Full gates + cold audit; deploy BOTH; smoke: enrichment sweep on the undocumented
module → a BM25 query that previously missed now hits, marked `(ai summary)`;
INDEX row + Log.
