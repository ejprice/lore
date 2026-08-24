# REPORT-design-sidecar-62

**SUMMARY BLOCK**
- `brief-base v14 read` · `brief project v7 read`
- state: **done** — doc **v5** (3 wave-2 contract ESCs resolved); standing by for contract-phase follow-ups
- v5 — 3 wave-2 contract ESCs (#7032 ack'd): **ESC-1 stamp_owner home = loremaster, NOT lorerunes** — I OVERRODE the contract-author+lead (A) lean: lorerunes is for CROSS-MEMBER policy (both stamp_owner consumers are loremaster = intra-member → a shared loremaster module) AND it is I/O-orchestration not a general predicate (#222 "resolution stays out of lorerunes"); only the general `parse_credential` predicate qualifies for lorerunes. Corrected R1.1 / scope-line item 3 / W2.6. Contract's BEHAVIORAL pins STAND; the stamp_owner-HOME pins need a targeted relocation revision before adversary. **ESC-2** confirm DEFER the explicit clear-hash revoke verb (retire is the ruled revocation path; re-open trigger = rotate-without-retire need / first non-fleet consumer). **ESC-3** confirm ENFORCED-WHEN-SET for `capability_expires_at` (defaults never/unset, but honored if set — a decorative field fails the trust doctrine); aligns with operator's SF-2, no new escalation. Sharpened SF-2/W2-R4 wording to match. Operator (via lead) had already ruled SF-1=ADOPT + SF-2=lifecycle-scoped+optional-seam (recorded in W2.7).
- v3 correction (#7022 ack'd): re-derived the count myself (grep of `record<{PRINCIPAL_TABLE}>` specs) — THREE existing links (`principal_key.principal`:1908, `keep.keeper`:2037, `audit.actor_principal`:2187 [61a-w4, dangle]); `agent.owner_principal` is the **FOURTH**, not the third. Corrected R3.1/R3.2/I4/scope-line; DANGLE preserved; flagged the delete docstring's own stale "TWO".

## v4 — WAVE-2 ADDENDUM (mechanism (A) concrete shape; consult #7027 ack'd)
Grounded in a read of `principal_keys.py` (`PrincipalKeyStore`) + `agents.py` (`AgentRegistry.register`).
- **Crux (item 1) ANSWERED:** capability = a VERIFIED credential (server hash-checks it), NOT a spoofable claim — sound + sufficient; PrincipalKeyStore is the proof-by-precedent. It rides a tool ARGUMENT because the transport is shared (only per-call channel). **SF-1 (confirm):** refines §3.2.2 to "never from an UNVERIFIED arg; a verified credential arg is admissible" — owner stamp still never from `owner=`/`as_agent=` claims.
- **Presentation (item 1):** a dedicated `capability=<name:secret>` arg (NOT overloading `agent=` — leak risk); display `agent=` stays a no-authority label.
- **Storage (item 2) RULED:** `agent.capability_hash : option<string>` UNIQUE — a FIELD on the agent row (1:1 cardinality; minted atomically in register's create branch; binding check reuses Fork-3 `owner_principal` on the same row; reuses AgentRegistry's `_query` seam). NOT a new store, NOT extending PrincipalKeyStore. **DRY:** extract `lorerunes.parse_credential` shared by both verifies (mutation-proven); `sha512_hex` reused; no-oracle/no-cache discipline pinned in both.
- **Mint/lifetime/revocation (item 3):** mint-once-on-create (re-register never rotates a live secret), secret returned once, never persisted. **SF-2 (confirm):** lifetime = AGENT-LIFECYCLE-scoped (no clock TTL) — the (principal,agent) binding check makes a leaked capability useless without the owner's transport token, so R1.3's leak-window is subsumed; optional `capability_expires_at` seam for defense-in-depth. No-cache → revocation/retire denies on the NEXT call.
- **agent_of (item 4) SF-3 (note, not a fork):** the transport token NEVER carries an agent (verified), so `agent_of(token)` correctly stays `None` — NOT filled; the real seam is a new `resolve_agent(capability, token) -> agent_id|None`, fail-closed None=DENY (R1.4 relocates here).
- **Wave scope (item 5) RULED:** ONE wave — mechanism + its security pins + prose together (splitting pins from mechanism ships an unverified mechanism = trust-doctrine violation). 63/64 per-tool reach legs stay RED_ADJUDICATED (cross-packet).
- **Per-item security-auditor attack surface** enumerated (W2.1–W2.4/W2.6): §3.2.2 fuzz; cross-principal capability replay → binding DENY; preimage/timing/injection; retire/revoke next-call-deny; fail-closed resolution.
- **Flagged (not a 62-build task):** the fleet spawn-brief must capture register's one-time secret + present it every call — an orchestration/pkt-65 obligation; pre-cutover nothing breaks (62 unserved).
- decisions for lead→operator: **SF-1** (confirm §3.2.2 refinement), **SF-2** (confirm lifecycle-scoped lifetime); SF-3 is a note. None MAJOR-blocking.
- deviations: none
- Packages considered: none — no mechanism specified (design doc; the authz-package survey
  was already done in authorization-model §11, cited not re-run)
- Reuse ledger: none (design doc, no new symbols)
- Graded: n/a (design ruling, not a verdict on another artifact)
- decisions-needed: **none open** — F1=(A) confirmed (premise HIGH-verified); F2=real local
  principal via api-key (sentinel overridden/retired, I5 added); F3/F4 ratified. Ack'd #7019.
- deliverable: `docs/design/2026-08-24-packet62-agent-identity-rulings.md` (v2)

## v2 fold (operator rulings, 2026-08-24; directive lore_comms #7019, ack'd)
- **F1 (A) confirmed** — client-arch premise HIGH-verified (Mcp-Session-Id one-per-connection,
  server-assigned; claude.ai = one OAuth per user; `lore_comms register` is already the pattern).
  §9 sibling-anti-spoof stays IN-scope, met by (A) modulo accepted own-capability residual.
- **F2 real-local-principal-via-api-key** (operator OVERRODE my sentinel; sentinel WITHDRAWN).
  Worked (a) drops the no-credential branch → `stamp_owner` has ONE path (SIMPLER); (b) pkt-65
  provisions operator principal + `lore-adm mint-key` + `.mcp.json` reconfig + posture flip (DEPLOY,
  not 62-build); (c) §8-tightening = pkt-65 deploy, posture.py UNCHANGED, ⚠ 65 must flip
  code+posture+key ATOMICALLY or fail-closed lockout; (d) I5 added. NOTE recorded: pre-cutover
  fleet runs the old no-auth image, nothing breaks mid-development, 62 must NOT touch the live fleet.
- **F3/F4 ratified**; F3 principal-delete DANGLE-tolerated for owned agents.
- Added a **FINAL PACKET-62 SCOPE LINE** (builds vs explicit non-obligations) for the contract author.

## What I ruled (each fork = recommendation + rationale + riders in the doc)

- **Fork 3 — `owns` edge shape (RULED, not major):** scalar field link
  `agent.owner_principal : record<principal>`, NOT a RELATION edge. Precedent: packet-60
  Fork-A (`keep.keeper`) + store-ref §4 (traversal never index-served → keep scalars as
  fields) + 61's two-indexed-field owner representation. **The three "agent" notions are ONE
  = the comms registry id** `uuid5("lore://agent/{session}/{name}")`; 61's IR already binds
  `owner_agent = record(AGENT_TABLE, agent_id)` and `Subject.agent_id` is that id. Riders:
  new `record<principal>` link ⇒ update `PrincipalStore.delete` cascade + exact-set pin
  (`test_principal_keys_schema.py` — the delete docstring already flags this); `option<>` on
  the populated `agent` table; dirty-store migration pin.

- **Fork 1 — mint mechanism (⚠ MAJOR, escalate):** §3.3's "each agent = own connection + own
  token" does NOT match reality — no MCP client (Claude Code shared `.mcp.json`, claude.ai
  connector) presents a per-subagent transport credential; the bearer carries the PRINCIPAL,
  not the agent. So never-self-declared agent identity can't ride the token. Operator chooses:
  **(A)** app-layer per-agent capability secret minted at register (prevents sibling-spoof;
  only as strong as the agent's own context) or **(B)** principal-is-the-boundary, sibling-
  agent = self-declared label + ACCEPTED BOUND (matches reality; moves §9 sibling-anti-spoof
  to accepted). Cross-principal isolation holds under both. Recommend (A) if the capability
  rides the `agent=` seam cheaply, else (B).

- **Fork 2 — local-fleet crux (coupled; confirm):** local fleet = plain-HTTP loopback, NO
  credential; `register` self-declares agent. Recommend: 62 shapes mechanism+invariants for
  HOSTED/LAN; on LOOPBACK (single trust domain, §8 already-ruled interim) governed writes
  stamp a well-known SENTINEL local-principal + self-declared owner_agent so 63/64 function
  locally unbroken. Follows §8 → confirm-not-decide. Riders: named sentinel w/ re-open
  trigger; hosted 2×2 cross-principal isolation pin non-negotiable; loopback bound said-out-loud.

- **Fork 4 — 62↔63 boundary (RULED):** 62 lands the mechanism + the anti-injection invariant
  as a DERIVED reach pin (from `partition_tools_by_population`, not a hand-list) whose
  per-tool legs are RED_ADJUDICATED (owner+trigger "63/64 retrofits <tool>") and go green
  tool-by-tool as 63/64 add owner/scope columns. 62 fuzzes only the tools it wires
  (`lore_comms register`); the reach pin catches a bypassing tool across the packet boundary.

## Also in the doc
- Removed-behavior inventory I1–I4 for retiring packet-48's non-wiring guard (each
  adjudicated; the docstring prose itself must be edited + retired-prose grep sweep as a
  close-out step — P8d rendered-prose law).
- Roll-up of what contract/adversary/security-auditor must pin.

## Load-bearing ground-truths (read this session)
- `.mcp.json` = `http://127.0.0.1:9202/mcp`, no auth (loopback, no per-agent credential).
- `agents.py:598 register` → `agent_id = uuid5(NAMESPACE_URL, "lore://agent/{session}/{name}")` — self-declared.
- `pdp.py:249 OwnerAgentEq.to_surql` → `owner_agent = type::record(AGENT_TABLE, $agent_id)` (61 already unified).
- `pdp.Subject(principal_id, agent_id, role, visible_keep_ids)`; owner columns still absent from governed tables (63/64).
- `token_verifier.py::agent_of` → None today; fail-closed (None = DENY) documented for 62.
- `principals.py:636 delete` docstring flags the new-`record<principal>`-link revisit verbatim.

## Confidence flags
- HIGH: loopback/no-credential, register self-declaration, 61 IR unification, delete-cascade forward-scope (all read from tree).
- MEDIUM: "no MCP client presents a per-subagent transport credential" — external client behavior, can't probe from repo; the operator/security-auditor must confirm, and Fork 1 turns on it.

Standing by for follow-up design questions (via lore_comms / SendMessage; at rest between them).
