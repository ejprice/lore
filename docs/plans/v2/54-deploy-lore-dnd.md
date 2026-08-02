# 54 — Deploy `lore-dnd` + go-live (wave-D mint, 2026-08-02)
size ~0.15 wu · wave D · depends: 39, 49, 53, 07a · DEPLOY: yes (the new instance)
allowlist rationale: docs/design/2026-08-02-dnd-graph-scope-rulings.md §4 (the ruled 15-tool enumeration — write it into the instance lore.yaml)

## Mission
The second lore instance: slug `dnd` (hyphen-free, slug law), database `dnd` in the
shared store, existing image, shared TEI embedder; corpus as a `watch: static,
provider: local_directory` tier over the dndlorescraper output, version-stamped per
scrape (`.crawl-state.json` is the change detector).

## Scope IN
- Instance `lore.yaml`: the ruled allowlist (5 generic + `dnd_*`; 10 disabled WITH the
  false-clear rationale recorded — rulings doc §4); `extensions: [dnd]`; auth per packet
  39 (claude.ai principals; keys minted by 49's CLI).
- **Always-on posture**: a systemd/quadlet unit (surreal-stores precedent) — the
  on-demand lore-deploy lifecycle does not fit an instance serving claude.ai users. If
  the packet-19 deploy architecture has landed by then, adopt its shape instead; do not
  build both.
- **MANDATORY before exposure: the #236/#138 consult** (standing first-non-local-
  deployment trigger — dangling-edge ghost sweep + the exec-seam threat model).
- Smoke: register a real principal, mint a key, run the Moon-Druid acceptance query
  through the claude.ai path end-to-end; a revoked key denied live.
- Operator-side (not this packet's build, verify only): hades SNI/Caddy route · claude.ai
  connector secret.

## Scope OUT
- Any extractor/tool/schema change (50–53 own those). lore-lore's own deploy (#165/#166
  untouched).

## Entry check
39 deployed with write gating live; 07a landed (#164 closed — outside users must not meet
the reconnect defect); 53's battery green.

## Exit
Instance live and reachable via claude.ai; deploy gates (artifact + workspace-honesty
probes) green on the new container; `lore_index()` honest on the dnd corpus; go-live Log
line + findings resolved with production receipts.
