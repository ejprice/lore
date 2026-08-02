# 46 — Extension discovery wiring (wave-D mint, 2026-08-02)
size ~0.15 wu · wave D · depends: 45 · DEPLOY: no (dark until an extension exists; 54 lights it)
spec: docs/design/2026-08-01-dnd-rules-rag-proposal.md §4-C item 2 · framework: loremaster/extension.py (11 seams, COMPLETE and UNWIRED — 0 production register_extension call sites)

## Mission
`extensions:` in `lore.yaml` actually instantiates registered `Extension`s at boot
(registry/entry-point lookup in the config path) and routes them through the existing
`_register_extension_tools`. Closes the discovery gap that keeps the framework unproven.

## Scope IN
- Config model: `extensions:` section (pydantic, `extra="forbid"` on the wire).
- Discovery: name → Extension class → instantiate → `register_extension`. A config naming
  an unknown extension FAILS BOOT LOUDLY (teaching error naming the known set).
- Collision behaviour composes with 45's fixed universe-guard.
- Pins: unknown-name boot failure (positive control: a registered test extension boots);
  a config with no `extensions:` is byte-identical serving to today (regression leg).

## Scope OUT
- The ingest write-fragment seam (packet 47 — it does not exist in the 11 seams).
- Any real extension (50+). Allowlist mechanics (45).

## Entry check
45 landed (its universe-guard fix is this packet's premise). `lore_index()` fresh.

## Exit
Full gates + adversary + cold audit. Mutation proof: break discovery, watch the
unknown-name pin AND the boots-with-extension pin go RED (declared set from
--collect-only first).
