# Map/impact orientation design — the P6-dogfood investigation record

**Date:** 2026-07-04 (P7 session, cycle-1 friction triage → operator-directed design study)
**Status:** BINDING on P8's tool-surface redesign (plan §6 P8 references this document).
**Implemented:** P7-tail polish wave (ledger task #6); its contract pins are the durable
form of this decision — P8 may change rendering *format*, never these *semantics*,
without a fresh operator decision + model consult.

## Why this document exists

P6 shipped `lore_map` / `lore_impact`; P7 was their first heavy live use, and four
frictions surfaced (FRICTION.md, 2026-07-03/04 entries). P8 redesigns the tool
presentation as part of the 12-tool surface consolidation — without this record, the
rationale below would live only in one session's transcript and its deletable agent
reports, and P8 would predictably re-litigate or silently regress it.

## The frictions (receipts: restated in full below; FRICTION.md retired into the finding ledger 2026-07-06)

1. The unfocused `lore_map` ranked TEST INFRASTRUCTURE on top — `_surreal_harness`,
   `_surreal_fakes`, `_extension_helpers` at ranks 1-2-4; `server.py` fifth.
2. Per-module symbol lists rendered EVERY symbol (80+ for `_surreal_fakes`), starving
   module coverage (155 modules elided) to afford symbol noise.
3. `lore_impact` on a BARE name returned correct reference counts but `tests: 0`
   (qualified form: 137 covering tests) — the tests join doesn't ride the
   `answers_to` bridge; the silent 0 reads as an answer.
4. `lore_impact` depth>1 module rollups count the TRANSITIVE ripple but read as
   direct-consumer counts — a team-lead brief mis-scoped a file because of it.

## Method

The operator directed a three-model consult (2026-07-04): Opus and Sonnet 5 — the
models doing the bulk of implementation work against these tools — answered five
design questions as introspective informants; Fable (team-lead) added its own
usage receipts from the live P7 session; the operator's hypothesis framed it.

**Operator hypothesis:** Claude knows when it wants code vs tests — code to
understand how something WORKS, tests to understand how to WIRE something in.
Segregate; maybe also down-rank.

**Fable refinement (session receipts):** tests serve THREE targeted roles — wiring
recipes, behavioral-contract discovery (test names as spec), covering-test checks —
and all three arrive with a symbol already in hand. None is an unfocused-map ask.

## Consult findings

**Unanimous (Opus, Sonnet, Fable):**
1. Unfocused orientation = production topology. Tests are never wanted first on a
   cold call. Root cause named by Sonnet: PageRank conflates "heavily depended on
   by tests" with "structurally central."
2. Tests are wanted via TARGETED calls only (`tests_for`, `focus=`, named files in
   briefs). Even under this project's "contract file is LAW, sibling X is your
   template" convention, briefs hand agents the filenames — the map adds nothing.
3. Placement beats labeling. A `[test]` tag cannot fix primacy bias ("ranked first"
   reads as "matters most" before any tag registers); down-rank-only still spends
   orientation budget interleaving noise. You have to MOVE them.
4. `focus=` resolving to a test node (or a tests/fixtures/harness-shaped query)
   must AUTO-INVERT — promote the test neighborhood to full prominence. Both
   models named this independently as the safety valve without which any default
   demotion becomes a trap.

**The divergence and its resolution:** Opus wanted hard segregation (an always-
present compact rolled-up test section — "you should know substantial scaffolding
exists"); Sonnet wanted production-only with an always-rendered announced-elision
line (budget discipline + the no-silent-caps doctrine). Resolved by making the
elision line CARRY the one-glance content — Sonnet's cost, Opus's information.

## The agreed specification

`lore_map`:
1. Test-node classification reuses the existing prod/test split the graph already
   carries for `references()`.
2. Default (unfocused or production-focused) map: test nodes are EXCLUDED FROM THE
   RENDERING, but their edges keep feeding rank mass into production nodes (a
   test-hammered module is real signal about that module).
3. An ALWAYS-RENDERED elision line — never silent:
   `test infra omitted: <top 2-3 hubs> (+K more) — tests=true to include`
4. `tests=true`: appends the compact, ROLLED-UP segregated test section.
5. `focus=` on a test node / test-shaped query: auto-invert (test neighborhood at
   full prominence).
6. `[test]` tag on any test node rendering in a mixed context (secondary insurance,
   never the primary fix).
7. Symbol caps EVERYWHERE: top-N by rank + "+K more" — budget spends on module
   breadth over symbol depth. **The cap is never a dead end** (operator concern,
   2026-07-04; plan §5's "rollup + refine guidance, no pagination" doctrine):
   7a. Every "+K more" trailer TEACHES its expansion verb by name:
       `+K more — focus=<module> for the full list`.
   7b. `focus=` on a module LIFTS that module's symbol cap (full list within
       budget) — focusing is the "I care about this one" intent signal; only
       the focused module's neighbors stay capped.
   7c. The cap N scales with `budget=` — it is a budget-allocation policy
       (breadth first), not an information ceiling; and the complete-file ask
       is honestly served by `lore_read`, which the focused view cites.

`lore_impact`:
8. The covering-tests join rides the same `answers_to` bare-name bridge as the
   reference counts (or, minimum, renders "tests unresolved for bare names —
   qualify" instead of a silent 0).
9. depth>1 module rollups are labeled TRANSITIVE (e.g. "via server.py", or a
   direct/transitive split) so they cannot be read as direct-consumer counts.

## P8 incorporation requirements (binding)

- The P7-tail contract pins implementing the spec above are semantic law for the
  P8 redesign: rendering format may change; pinned semantics may not, without a
  fresh operator decision + consult.
- The P8 `instructions` block must TEACH the model: map = production orientation;
  reach tests via `tests=true`, `focus=`, or `tests_for`.
- **Do-not-relitigate list** (each was considered and rejected with reasons above):
  down-rank-only in a unified list; silent test omission (violates the no-silent-
  caps doctrine); tag-only fixes (placement is the signal).
