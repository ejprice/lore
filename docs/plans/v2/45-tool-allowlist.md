# 45 — Tool allowlist (= multi-user Part 2; resolves #296) (wave-D mint, 2026-08-02)
size 0.25–0.35 →SPLIT AT KICKOFF if over (sizing law) · wave D · depends: wave C done · DEPLOY: yes (both)
spec: docs/design/2026-08-01-multi-user-lore-proposal.md §Part 2 (the whole design — this file only points) · rulings: docs/design/2026-08-02-dnd-graph-scope-rulings.md §1

## Mission
`tools:` section in `lore.yaml` enables/disables built-in tools per deploy. A disabled
tool is NEVER REGISTERED — absent from `tools/list` AND uncallable by the SDK's own
dispatch (#296 option 2A, verified at SDK source in the spec). Resolves **#296**, thereby
unblocking packet 39; gates the `lore-dnd` surface (rulings doc §4 is the first consumer).

## Scope IN (spec §Part 2 carries the mechanics; headlines only)
- The `_tool` config-consulting indirection replacing `mcp.tool` at all 15 sites — ONE
  decision point, never 15 per-tool obligations.
- **The cost centre: served prose becomes a FUNCTION of the enabled set** — `_INSTRUCTIONS`
  and every tool description (they cross-reference neighbours). The
  every-lore-token-is-a-live-tool pin is SATISFIED, not waived.
- The ~9 `tools[name]`-indexing pins (spec lists them) survive via the recommended
  default: absent `tools:` ⇒ all built-ins; deny-by-default WITHIN the section.
- Enabled set validated against the DECLARED UNIVERSE (`_ALL_BUILTIN_TOOL_NAMES`) —
  unknown name fails boot loudly.
- **Fix the collision-guard universe bug here**: `_register_extension_tools`'s guard must
  check the declared universe, not the registered set (else a disabled built-in's name is
  claimable by an extension).
- 2B: generate the commented-out sample section from the universe.

## Scope OUT
- Extension discovery (packet 46). Principals/keys (48/49). Packet 39's per-principal
  dynamic filtering — composition rule in spec §Part 2 ⚠ (partition input = the
  registered set).

## Kickoff rulings (operator, 2026-08-13 — design `docs/design/2026-08-13-packet45-served-prose-derivation.md`)
- **SIZING = ONE packet** (a–h), ⅓ emergent reserve. The mechanism/prose seam is a FALSE
  seam (the every-token pin couples instructions + all 15 descriptions), so the coupled
  core cannot be cut; the only separable items (2B sample-gen, deploy) are too small to
  justify a second packet's ritual.
- **FORK A (IDENTITY over-claim) = config-authorable IDENTITY/preamble field** on
  `LoreConfig`, **default = today's exact `_INSTRUCTIONS` identity string** (byte-exact →
  CL3 stays green). The served IDENTITY line over-claims "code+docs+graph RAG, durable
  memory, fleet ledgers" on a REDUCED surface and no `lore_`-token pin catches it (a
  Trust Leg-1 defect). lore-dnd authors its true identity in packet 54. **SCOPE ADD.**
- **FORK B (empty enabled set) = LEGAL at the config layer**; boot loud-fails ONLY if the
  TOTAL served surface `(built-ins ∩ enabled) ∪ extension-tools` is empty (keeps the
  spec-required empty-set coverage fixture constructible; supports a future extension-only
  instance).
- **Design spine:** `build_instructions(enabled)` refactor of `_INSTRUCTIONS`;
  `build_instructions(ALL)` reproduces today's string BYTE-EXACT (CL3 is the anchor — do
  NOT reparametrize CL3/CL1). Coherence = ONE biconditional (served `lore_` tokens ==
  enabled built-ins) + structural pins (no gutted header / dangling arrow) + anti-vacuity.
  RE-1: promote `_ALL_BUILTIN_TOOL_NAMES` to prod as ONE object (test-side imports it).
  RE-2: #333 typecheck-RED baseline is operator-accepted → report a green-DELTA.

## Entry check
Wave C closed (INDEX). `lore_findings` → #296 not-resolved. Spec §Part 2 read in full.

## Exit
Full gates + contract → adversary → build → cold audit. Exact-set pin parametrised over
configs BOTH directions with a non-trivial subset AND an empty set (anti-vacuity guarded);
instructions pin biconditional. Mutation-prove the filter (a disabled tool absent on the
wire, live probe). Deploy BOTH; #296 resolved with a production receipt.
