# 32 — Memory maintenance: decay/expiry sweeps (formerly PKT-19)
size ~0.15 wu · wave F (parallel-safe) · depends: v1.0
law: DESIGN-LAW §9 (memory contract — the ref-shape/boost invariants bound here) · DEPLOY: yes

## Mission
The P7 punt: importance defaults-by-kind and reinforcement-on-recall shipped;
**decay/expiry sweeps** did not. Build the scout-side maintenance sweep.

## Scope IN
- Expiry: kind=`ongoing` rows past expires_at stop boosting/injecting (honest recall
  with include_superseded-style audit visibility — never silent deletion; supersession
  model law).
- Importance decay per the P7 defaults design (reinforcement-on-recall already
  counteracts it — the sweep only decays, never deletes).
- Sweep is idempotent, logged, and its last-run age surfaces in lore_index.

## Scope OUT
- Any recall wire-shape change (DESIGN-LAW §9: the chunk-key ref shape is a consumer
  contract). Spectron backend work (invite-gated, INDEX pool item 12).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
`lore_recall include_superseded` audit path green at HEAD; ledger write-through
untouched by design (memories remain the only non-derivable data).

## Exit
Full gates + cold audit; deploy BOTH; smoke: an expired `ongoing` memory stops
injecting but remains auditable; INDEX row + Log.
