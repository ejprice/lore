# PKT-18 — Cross-tier compare (Odoo 15→19/20 migration prep)
size ~0.25 wu · wave O ∥ (re-waved 2026-07-14; 15→19 prep feature, NOT an onboarding prerequisite — may slip to F) · depends: v1.0
law: DESIGN-LAW §1 (client law), §12 · spec: MASTER-PLAN §6 "Cross-tier compare" (operator-directed 2026-07-03) · DEPLOY: yes

## Mission
ONE lore project holds both ERP versions as tiers (static odoo15-core/odoo19-core,
live odoo19-custom); agents compare a symbol or module across tiers in ONE call.
**No new tool**: a `tiers=` parameter on `lore_diff`.

## Scope IN
- `lore_diff(tiers=("A","B"), target=…)`, two granularities, both citation-first:
  (a) **symbol compare** (qualified name): each tier's stored definition — signature,
  content_hash, cited span — side by side with a same/differs verdict per chunk (hash
  compare is free; C1 tier coexistence is pinned all the way down);
  (b) **file/module rollup** (path prefix or omitted): only-in-A / only-in-B /
  differing-by-sha512, token-budgeted rollup like lore_map.
- Reuse lore_diff's snapshot-diff rendering (tier-diff = same shape, tiers for times).
- Tier pairs validate against configured roots (teaching miss on typos).
- Graded honest-emptiness: a tier mid-rebuild NEVER yields a silent "missing in B".
- Zero schema change (reads chunks + manifest + per-tier name-nodes that already exist).

## Scope OUT
- Any Odoo-specific extractor (the XML extractor is the Odoo extension's, later).
- Until this ships, the documented convention stands: get_symbol FQN fan-out returns
  all tiers; agents compare manually.

## Entry check
A two-tier fixture project (small, committed test fixture — not the live Odoo corpus)
exercising same/differs/missing per tier.

## Exit
Full gates + cold audit; deploy BOTH; instructions/description teach the tier mode
(structural pins updated in step); smoke on the fixture; INDEX row + Log.
