# REPORT — fable-sidecar-45 (packet 45 served-prose derivation + sizing)

`brief-base v13 read` · `brief project v7 read`

- **state:** done (design). Standing by for follow-ups.
- **deliverable:** `docs/design/2026-08-13-packet45-served-prose-derivation.md` (durable, tracked).
- **Packages considered:** none — no mechanism specified (design doc).
- **Reuse ledger:** none (no new production symbols; §6 points the builder at existing
  `_TOOL_NAME_TOKEN`, `partition_tools_by_posture`, `_ALL_BUILTIN_TOOL_NAMES`, `AuthConfig`).
- **Graded:** n/a (design, not a verdict).
- **decisions-needed (2 IMPORTANCE-class + 1 sizing):**
  - Fork A (IMPORTANCE) — IDENTITY line over-claims on any reduced surface and NO pin catches it
    (not a `lore_`-token). derive-from-families vs. **config-authorable preamble (rec)** vs.
    leave-constant (rejected). Trust-Doctrine call → operator's.
  - Fork B (IMPORTANCE) — empty-but-valid enabled set: BOOT or LOUD-FAIL? Rec: legal at config
    layer, loud-fail only if total served surface (built-ins∩enabled ∪ extensions) is empty.
  - Sizing (lead's call) — ONE coupled-core packet (a–f, ≈0.28–0.32) + thin 45b for (g)+(h), or
    one packet with reserve.

## Headlines a stranger needs

- **The reframe:** CL3, CL1, and the whole `TestServerInstructions` family build from the DEFAULT
  `_config` = full surface. If `build_instructions(ALL)` is byte-exact to today's `_INSTRUCTIONS`,
  they stay GREEN untouched. The derivation is **ADDITIVE** (new subset pins), not a rewrite.
- **Q1:** mechanism/prose is a FALSE seam (the every-token pin couples instructions + all 15
  descriptions in one assertion). The TRUE clean seam is config-vs-deploy: split (g) 2B sample +
  (h) deploy/#296-receipt into 45b; (h) may already belong to packet 54.
- **Q2:** `build_instructions(enabled)` from per-section builders (LADDER = ordered tool-steps
  re-joined by `->`; MEMORY = per-tool clauses; COMMS/PENDING guarded). Coherence = ONE
  biconditional token pin (whole served surface) + structural pins (no gutted header, no dangling
  arrow). Comms-block equality: do NOT reparametrize CL3 — keep it a full-set anchor; disabled
  comms is covered additively.
- **Q3:** Leg-1 finds the IDENTITY over-claim (Fork A). Leg-2 = 6 forgery pins from deps×verbs;
  the three that render byte-identical to healthy (filter-missed-a-site, extension-claims-a-
  disabled-name, IDENTITY-over-claim) are the dangerous ones.
- **Q4:** no real packet-39 conflict. Two required-edits: RE-1 single-source the promoted universe
  (prod object imported back into tests, else #291 drift), RE-2 read typecheck against #333's
  accepted RED baseline.

Full reasoning, tables, worked lore-dnd LADDER example, and symbol-anchor corrections (brief/spec
line numbers are stale — §0): in the design doc.
