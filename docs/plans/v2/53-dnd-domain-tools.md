# 53 — dnd domain tools (wave-D mint, 2026-08-02)
size ~0.20 wu · wave D · depends: 50, 51, 52-series · DEPLOY: no (54 deploys)
frame: docs/design/2026-08-02-dnd-graph-scope-rulings.md §5 + §6 (the composition ruling is the law of this packet)

## Mission
The served dnd surface: **rules retrieval + general parameterized graph-FILTER tools —
NO per-mechanic composed tools, no server-side rules interpretation** (operator ruling,
rulings doc §1.6). The client LLM composes: search the rule → read it → filter the graph.

## Scope IN
- Declarative `ToolSpec`s via the extension framework (never hardcoded decorators):
  `dnd_get_spell(name, book?)` — one row per book that ships the name; the render names
  the book/edition, never "the" Fireball · `dnd_spells(class?, level?, ritual?, school?,
  book?)` · `dnd_monsters(type?, cr_max?, cr_min?, fly?, swim?, habitat?, book?)` ·
  `dnd_get_entity(name, kind?)` for features/subclasses/items/conditions. 50's ruled doc
  finalizes the list.
- Every render names edition; 2014-mechanic queries name the base-rules bound.
- **Both trust legs per served surface** (repo CLAUDE.md hard definition): Leg-1 scope
  diff baked into each render template; Leg-2 forgery pins CONSTRUCTED from store-deps ×
  {stale, empty, wrong-instance, partial} — byte-diff against healthy; identical bytes =
  STOP.
- Acceptance: the level-4 Moon Druid trace (rulings doc §6) end-to-end on the live test
  store, including the retrieval-ranking leg.

## Scope OUT
- New generic tools; allowlist mechanics (45); instance config (54).

## Entry check
52-series landed with oracle pins green; 51's store serving on :18000.

## Exit
Full gates + adversary + cold audit; consumer-agent battery with keyed honesty probes
ending in the routing test (CALL_AGAIN vs ROUTE_AROUND — a ROUTE_AROUND on an honest
render is a FAILED acceptance to fix, per the Trust Doctrine).
