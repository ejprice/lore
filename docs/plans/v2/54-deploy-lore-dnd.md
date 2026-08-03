# 54 — Deploy `lore-dnd` LOCALLY (operator soak; no auth) (reshaped 2026-08-03)
size ~0.15 wu · wave D · depends: 53 only (auth moved to the tail — 56 carries go-live) · DEPLOY: yes (the new instance, LAN-only)
architecture: docs/design/2026-08-03-wave-d-architecture.md §9 · allowlist rationale: docs/design/2026-08-02-dnd-graph-scope-rulings.md §4

## Mission
The second lore instance, LAN-LOCAL: slug `dnd` (hyphen-free), database `dnd` in the
shared store, existing image, shared TEI embedder. **The operator soaks it via a local
MCP connection before ANY auth or exposure work** (operator ruling, 2026-08-03 — the
identity tail 48/49/39/07/07a and go-live 56 all come after this packet).

## Scope IN
- Instance `lore.yaml`: the ruled allowlist (5 generic + `dnd_*`, 10 disabled with the
  false-clear rationale recorded); `extensions: [dnd]`; TWO static roots, built-in
  local_directory provider for both (`provider:` is unread — architecture §9): prose
  tier at `dndlorescraper/output` (`**/*.md`), machine tier at `output-graph`
  (`**/*.jsonl`, claimed by the extension, never chunked/embedded).
- **Always-on posture**: a systemd/quadlet unit (surreal-stores precedent) — the
  on-demand lore-deploy lifecycle does not fit a soak. If packet 19's deploy
  architecture has landed by then, adopt its shape instead; never build both.
- Local `.mcp.json` wiring for the operator's sessions; smoke = the Moon-Druid
  acceptance trace against the running instance.

## Scope OUT
- ALL auth (48/49/39), hades exposure, #236/#138 consult, findings write-gating — packet
  56 owns go-live. No off-LAN reachability leaves this packet.

## Entry check
53 landed (battery green); 55's machine tier current for the full corpus; both stores up.

## Exit
Instance live on LAN; deploy gates green; `lore_index()` honest on the dnd corpus;
operator-soak handoff note in the Log (what to try, where findings go).
