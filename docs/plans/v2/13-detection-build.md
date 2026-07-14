# 13 — Chunker detection layer · BUILD + DEPLOY (formerly PKT-05)
size ~0.35 wu →split at kickoff (sizing law) · wave L (re-waved 2026-07-14) · depends: packet 12 ruled · recommended before packet 24 (Odoo file zoo)
law: DESIGN-LAW §11, §12 · DEPLOY: yes (both containers)

## Mission
Build the packet 12 contract through the TDD 5-phase cycle (STUB → RED → GREEN → REFACTOR):
identify-based dispatch as default authority, config override as tier-1 escape hatch,
binaries skipped, prose-ish → text chunker + suspect flag (per the operator's placement
ruling) + WARN in logs and index status, fail-loud key validation (#11), the ruled #10
retroactivity behavior.

## Scope IN
- Detection module + wiring into indexer routing; the bcba046 override path untouched
  as precedence tier 1.
- index_status/log surfacing of suspect-flag counts (silent anything = cardinal failure).
- Resolve findings #10 and #11 with receipts.
- Re-chunk announcement flow if the #10 ruling requires it (DESIGN-LAW §11: announce
  before executing).

## Scope OUT (surface, don't build)
- New chunkers of any kind; Odoo manifest/csv_access extensions (future Odoo extension).
- Re-embedding policy changes.

## Entry check
packet 12 contract tests exist and are RED; suite snapshot green otherwise; spike-surreal up.

## Exit
Full gates + cold audit; deploy BOTH; smoke: a shebang script, a .yml/.yaml pair, a
binary, and a prose-ish straggler all route/skip/flag correctly on the live instance;
findings resolved; INDEX row + Log.
