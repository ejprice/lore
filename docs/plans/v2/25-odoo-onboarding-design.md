# 25 — Odoo onboarding · DESIGN (pool item 19, scheduled 2026-07-14) (formerly PKT-32)
size ~0.15 wu · wave O · depends: packet 24 receipts (the MRO/ORM assessment DEFINES this scope)
law: DESIGN-LAW §4 (graph invariants), §11 (chunkers opt-in guard), §12 · driver: **replace
the odoo-code MCP** (declared target 2026-07-11) · operator wants its own design pass

## Mission
Design (not build) lore's Odoo onboarding: everything packet 24 measured as missing between
"lore can ingest the tree" and "lore's verdicts on Odoo are trustworthy". Deliverable: a
ruled design doc that MINTS the the packet-26 series build packets (each ≤0.25 wu per the sizing law).

## Scope IN (the design covers each; packet 24's receipts decide depth)
- **XML reference extractor** — framework-mediated calls/views/actions/record refs; the
  dead-code truth prerequisite on Odoo (memory: odoo-target-needs-xml-reference-extractor).
  Shares the outbound-link extractor seam packet 28 names — coordinate, don't duplicate.
- **MRO + ORM metadata capture** per packet 24's assessment (operator-flagged):
  `_name`/`_inherit`/`_inherits` effective-model merges across modules, field-string
  references (`compute=`, `depends`, `related="a.b"`), super()-chain dispatch.
- **Manifest/csv chunker extensions** (the 2026-07-06 census named them the one future
  Odoo extension; detection layer routes them — packets 12/13).
- **Tier layout**: odoo15-core / enterprise / OCA static tiers + odoo-custom live tier;
  worktree overlays (packet 23) fork the custom tier only.
- **Cutover boundary from odoo-code**: per packet 24's operator-struck parity matrix —
  code-side tools lore covers vs the live-DB introspection surface (fields_get /
  search_read / call_kw) that stays with odoo-dev BY DESIGN.
- **Embedder/scale posture**: per policy (voyage-4-large for large corpora,
  results-trump-costs) + whatever packet 24's throughput receipts changed.

## Scope OUT
- Building ANY of it (the packet-26 series). Odoo 19 tiers (packet 27 owns cross-tier mechanics).

## Entry check
packet 24 certification receipts committed (its exit gate); packet 23 landed or in flight
(worktree overlay must precede packet 26 completion); the odoo-code MCP's tool list captured
as the parity-matrix input.

## Exit
Design doc at docs/design/2026-07-XX-odoo-onboarding.md; operator rulings recorded;
the packet-26 series packet files minted (each with entry/exit, ≤0.25); INDEX table gains the minted
rows; INDEX row + Log.
