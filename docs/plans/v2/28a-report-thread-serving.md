# 28a — Report/thread serving: ordered, section-aware, chronological (#163 ⊃ #160)
size ~0.25 wu · wave F (parallel-safe beside 28) · depends: packet 14 (#162 dedup FIRST — #163 names it prerequisite); v1.0
law: DESIGN-LAW §1 (client law — the thread is a served render; counted elision, honest
misses), §3 (any ordering influence disclosed) · DEPLOY: yes

## Mission
Finding #163 (self-described PACKET, 2026-07-21; subsumes #160): the archived-receipts
corpus is now semantically searchable, but **a retrieved chunk arrives WITHOUT its
header** — SUPERSEDED banners and dates cannot reach a semantic-search consumer, so
archived dated records read as current. Serve retrieved chunks as an **ordered,
section-aware, chronological THREAD** (the chunker already computes the breadcrumb;
nothing serves it), and graph reports to the findings/commits/symbols they cite, so an
agent reading history can see WHEN and WHETHER it was superseded.

## Scope IN (from #163's body — the packet session prices the exact cut)
- Serve each hit with its section breadcrumb + document date/banner state (the
  already-computed metadata, surfaced — not new derivation).
- A thread affordance: expand a hit into its document-ordered neighbourhood
  chronologically, budget-capped with counted elision (client law).
- Graph edges from archived reports to the findings/commits/symbols they cite (the
  `refers` family), so `story`/impact-style reads can reach provenance.
- The brief-base v6 mitigation ("date claims where you make them") stays — this packet
  makes the SERVER honest so the protocol rule stops being the only guard.

## Scope OUT
- Any map/impact semantic change (DESIGN-LAW §2). Summary synthesis (packet 34).
- Fixing duplicate indexing — packet 14 (#162) owns it and MUST land first.

## Entry check
`lore_findings` → #163 open, #162 resolved (else STOP — the dedup is prerequisite);
re-run #162's own query as the receipt (the bannered archive is the only hit); the
chunker's breadcrumb metadata confirmed present on live hits.

## Exit
Full gates + cold audit (served surface); deploy BOTH; smoke: a query hitting an
archived report serves its banner state + breadcrumb, and its thread expansion reads in
document order with dates; #163 resolved; INDEX row + Log.
