# PKT-21 — Hosted security for the split topology (design first)
size ~0.30 wu · wave G · depends: PKT-20 (external-review ordering) · gates PKT-23's exposure story
law: DESIGN-LAW §12 · driver: LORE_EXTERNAL_REVIEW.md gap 5 · DEPLOY: per design outcome

## Mission
Bearer + origin checks exist; everything else is deferred debt the external review
names: OAuth/Dynamic Client Registration, tenant/context isolation, delegated
principals, edge-level scope enforcement. The split MCP must not serve beyond trusted
environments until this lands. Design pass FIRST — the operator scopes what v1.2
actually needs vs what waits.

## Scope IN
- Threat-model + design doc: who can reach the mcp role, with what identity, scoped
  how (per-role creds from PKT-07 are the substrate; per-project namespace isolation
  already exists — state what it does and does not guarantee).
- Operator fork, briefed with recommendations: (a) OAuth/DCR now vs Bearer+TLS+network
  perimeter documented as the v1.2 posture; (b) multi-tenant scope grants (Spectron
  justified-OUT earlier — re-justify or keep out).
- Implement the operator-approved subset; refuse-and-point guards for the rest (a
  split deploy outside the documented posture fails loudly, not silently).

## Scope OUT
- UI auth specifics beyond what the approved design dictates (PKT-22/23 consume it).

## Entry check
Read the current auth surface (auth.py, tls_terminated_upstream disposition from
PKT-09) before designing; verify what PKT-10's e2e documented about exposure.

## Exit
Design ruled + approved subset built with full gates + cold audit; the exposure
posture documented in README/deploy docs; INDEX row + Log.
