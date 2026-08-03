# 56 — `lore-dnd` GO-LIVE (auth + exposure; friends may now connect) (wave-D mint, 2026-08-03)
size ~0.15 wu · wave D (tail) · depends: 54 soak complete, 49, 39, 07a · DEPLOY: yes (config + exposure)
architecture: docs/design/2026-08-03-wave-d-architecture.md §9 · allowlist notes: docs/design/2026-08-02-dnd-graph-scope-rulings.md §4

## Mission
Take the soaked local instance off-LAN: auth wired, hades exposure live, every
first-non-local-exposure gate discharged. Packet 39's "REQUIRED before off-LAN" clause is
honored HERE — nothing before this packet is reachable off-LAN.

## Scope IN
- Auth wiring on the dnd instance: claude.ai principals per packet 39's built posture;
  keys minted via 49's CLI; `lore_findings` ENABLED for principals per the ruled
  enumeration — its write path rides 39's per-principal gating (record the note in the
  instance lore.yaml).
- **The #236/#138 consult — MANDATORY before exposure** (standing trigger: dangling-edge
  ghost sweep + the exec-seam threat model).
- Operator-side, verify-only here: hades SNI/Caddy route · claude.ai connector secret.
- Smoke: register a real principal → mint a key → run the Moon-Druid acceptance through
  the claude.ai path end-to-end → a revoked key denied on the NEXT verification (live).

## Scope OUT
- Any extension/tool/schema change (50–53 own those); any new auth design (39 owns it).

## Entry check
Operator declares the 54 soak done (their call, in the Log); 39 deployed with write
gating live; 07a landed (#164 closed — outside users must never meet the reconnect
defect); 49's CLI mints against the production principal table.

## Exit
Off-LAN reachable via claude.ai; all smoke legs green with production receipts;
#236/#138 consult recorded; go-live Log line; findings resolved with receipts.
