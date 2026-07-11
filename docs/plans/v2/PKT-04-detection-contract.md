# PKT-04 — Chunker detection layer · CONTRACT (operator-agreed feature, ruled 2026-07-06)
size ~0.15 wu · wave B · depends: none (runs after wave A per operator sequencing)
law: DESIGN-LAW §11 (chunkers opt-in guard), §12 · TDD skill CONTRACT phase — pauses for review

## Mission
Contract-first design for autodetecting file type and routing to the EXISTING hardwired
chunkers. No new chunkers: the existing set is CONFIRMED sufficient (2026-07-06 census,
both corpora; odoo-mcp generic carry-over complete). Chonkie/tree-sitter long tail
parked MUCH later — do not reopen.

## Ruled design (memory: chunker-coverage-and-detection-plan — binding)
- The **`identify` package** (pre-commit's tagger: curated extension→tags so .yml≡.yaml,
  shebang interpretation, binary peek; fit verified 2026-07-06) is the default dispatch
  authority.
- The **bcba046 config-override wiring stays** as the tier-1 operator escape hatch.
- Binaries skipped. Prose-ish stragglers → text chunker + **suspect flag** + WARN in
  logs/index_status.

## Open fork → OPERATOR (with the contract review)
Suspect-flag placement: **in-text** vs **metadata + serve-time injection**. Present both
with token/honesty trade-offs and a recommendation.

## Folds (part of this contract, not separate work)
- **Finding #11** — dot-less `chunkers` extension keys boot clean but silently never
  route → fail-loud validation is part of the dispatch contract.
- **Finding #10** — route-change non-retroactivity: sha-based reconcile skip never
  re-dispatches unchanged files after a route change (DI's yaml needed manual reindex).
  The contract must state the retroactivity behavior (auto re-dispatch on route change,
  or an explicit announced re-chunk per DESIGN-LAW §11) — operator picks.

## Entry check
- `lore_findings`: #10, #11 open. Scouts on the dispatch seam BEFORE writing the
  contract: chunkers registry, bcba046 wiring, indexer routing (lore-first).
- `identify` package importable in the project venv (else escalate for install
  authorization — never hand-roll the tagger; packages-over-hand-rolling law).

## Exit
Contract tests written (RED) + design note recording the operator's two rulings (suspect
placement; #10 retroactivity); PKT-05 unblocked; INDEX row + Log.
