# REPORT — design-sidecar-39-2 (packet 39 RE-CUT, hosted-security OAuth)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** (2026-08-21) — re-cut design doc DELIVERED + REVISED for the F1/F4 rulings:
  **`docs/design/2026-08-21-packet39-recut-oauth.md`** (§0 rulings Q1–Q5 mapped to R1–R16,
  resource-server model on standalone fastmcp, Google MVP reusing `principal.subject`,
  `oauth_identity` child-table seam, role-gated enforcement, §9 superseded/removed inventory,
  §11 fork rulings, §13 contract-pin list). Both scout reports + GO directive (#5098) + the
  F1/F4 operator rulings (#5100) folded. Standing by for the fresh contract/adversary pass.
- **REV 2 (operator #5100, F1/F4):** F1 email-keyed admission CONFIRMED + `email_verified==true`
  made an explicit admission precondition (§3.2, §1, §13). **F4 ROLE-GATED WRITE** reverses the
  doc's original "no hosted write": read-only is now the FLOOR, `principal.role==admin`→`lore:write`
  grants write, `member` stays read-only. Woven through §0/§1/§3.3/§3.5/§7/§9/§13; the #295 EFFECT
  pin gained a member-vs-admin role axis (admin leg = the real positive control). NEW fork **F7**
  surfaced (§11): role-gating applies to api-key principals too (a member api-key is read-only in
  auth-on postures; LOOPBACK/auth-off is unaffected — fleet keeps writing) — I implemented
  Reading A per the explicit §3.5 directive and flagged Reading B for operator veto.
- (orientation phase, earlier this session:) comms test complete; forks pre-surfaced. Superseded by the delivered doc.
- deviations:
  - Did NOT deep-read adversary reports 1–4 — SKIMMED for the one root cause per brief ("don't drown"); root cause captured from design §16/§17 + INDEX (WB30→WB100 = `_setup_handlers` construction-time binding ⇒ live-in-process / dead-on-wire). fastmcp middleware seam RESOLVES it.
  - Have NOT yet read `REPORT-scout-fastmcp-oauth-39.md` (not yet located as committed) — the FastMCP native-OAuth provider/config facts remain PROVISIONAL (brief's own caveat) until it lands.
- Packages considered: none — no mechanism specified this turn (orientation only). The prior design's package verdicts (§14) are inherited inputs, not re-decided here.
- Reuse ledger: none — no new symbols introduced this turn.
- Graded: n/a — no verdict rendered on another artifact this turn (orientation, not audit). HEAD-at-report: `9a10604`.
- decisions-needed (updated 2026-08-21 after the operator provider-count ruling `#5092`, folded in §O-5; the real fork list ships with the design doc, gated on the scout):
  1. **Schema fork (CENTRAL) — RESOLVED by operator (#5092):** the identity model is ruling-C-shaped: principal keyed by email, **principal 1—\* oauth_identity, `(issuer,sub)`→principal**; one provider now = one oauth_identity row, relation supports N. §O-1(a) (new child table) is the ruled shape. ⚠ **ONE residual sub-tension I must surface (§O-5):** the shipped 48/49 substrate uses a single `principal.subject` column (`get_by_subject`/`set_subject`), NOT the child table — so the operator's "costs ~nothing" premise meets a shipped single-column substrate. Building `oauth_identity` now is a clone-`principal_key` build (moderate, not nil); the interaction with the vestigial `principal.subject` needs a design call (retire vs repurpose). Framed for the operator, not silently decided.
  2. **Admission flow (sub-question, still open):** how a first login binds to a principal — admin pre-creates by email, first token's verified email → bind `(issuer,sub)` (re-introduces `email_verified` as security-load-bearing), vs admin pre-registers `(issuer,sub)`. To settle in the doc. Detail §O-2.
  3. **Enforcement-mechanism supersession — CONFIRMED by ruling (#5092) + fastmcp §7:** R13/R16 apparatus (scoped `ToolManager`, `_setup_handlers` pins, `test_wire_discipline.py`) SUPERSEDED by packet-59 `on_call_tool`/`on_list_tools` middleware; enforcement is provider-agnostic (acts on resolved principal). DROP/RE-EXPRESS/CARRY list per §O-3. No open fork — mechanical.
  4. **Config substrate — RESOLVED by operator (#5092):** R12 flat-file roster SUPERSEDED by 48/49 principal DB; OAuth *server* config is **framework-native kwargs from lore.yaml + lore-secrets**, provider-selection a config-shaped seam (2nd provider = a config block, not a rewrite). Do **NOT** build DB-stored configs (ruling C' stays optional). Detail §O-4/§O-5.
  5. **Multi-auth do-now-vs-defer (pre-ruled conditional, held for scout):** easy on fastmcp (≤ threshold, judged vs scout's effort/mechanism finding) → do now; else → clean seam + NAMED re-open trigger (PIN-THE-MISS). My recommendation waits on `REPORT-scout-fastmcp-oauth-39.md`. Detail §O-5.
- receipt POINTERS:
  - comms test → §COMMS TEST below (seqs 5086 / 5088 / 5089)
  - principal substrate → `loremaster/loremaster/principals.py` (`PrincipalStore`, `set_subject`, `get_by_subject`); DDL `loremaster/loremaster/store/surreal_schema.py::_principal_statements` / `_principal_key_statements`; key store `loremaster/loremaster/principal_keys.py::PrincipalKeyStore.verify`
  - store law for the subject key → `docs/reference/surrealdb-31-capabilities.md` §1.8 (UNIQUE over `option<>` — multiple NONE coexist; non-NONE unique on CREATE **and** the fill UPDATE)
  - prior design → `docs/design/2026-07-31-packet39-google-oauth.md` (R1–R16, §7 enforcement, §8 removed-behavior, §9 pins, §14 packages)
  - enforcement seam 39 inherits → `docs/design/2026-08-15-fastmcp-3x-migration.md` §7

---

## COMMS TEST
- **register:** `design-sidecar-39-2` (session `pkt39-recut`, role design-sidecar, model fable, spawned_by lead-39-recut, cadence ≤6h) — OK; auto-acked project brief v7 on register.
- **outbound:** `lore_comms send grade=signal → lead-39-recut` thread `comms-test` → **sent #5086**.
- **inbound (drained + acked):**
  - **#5088** [directive] scout-fastmcp-oauth-39 → me, thread `comms-test-peer` ("peer ping") — **acked** (note "received").
  - **#5089** [directive] lead-39-recut → me, thread `comms-test-inbound` ("lead→agent durable") — **acked** (note "received").
- Round-trip proven BOTH directions (agent↔agent and lead→agent durable). First drain was empty (directives arrived after); re-drained at the next turn boundary and acked, exactly as briefed.

---

## ORIENTATION — what I read, and the forks I already see

Reads completed at HEAD `9a10604`: store reference §0–§5 (incl. §1.8, the exact `principal.subject` UNIQUE-over-`option<>` semantics); the prior design doc IN FULL (R1–R16, threat model, topology, auth path, config, posture, read-only enforcement, removed-behavior inventory, contract pins, kill switches, operator-side, bounds, packages, contract-pass + two adversary escalations); the 48/49 principal substrate (`principals.py`, the `principal`/`principal_key` DDL, `principal_keys.py` surface, the `lore-adm` CLI); `docs/design/2026-08-15-fastmcp-3x-migration.md` §7; INDEX row 39 + Log.

### §O-1 — The schema fork (CENTRAL, needs an operator ruling)
The packet-48 `principal` table (`_PRINCIPAL_FIELD_SPECS` + `_principal_statements`) carries **exactly one** identity-binding column:
- `subject: option<string>` UNIQUE — the docstring: *"the value fastmcp's `get_access_token()` surfaces as `AccessToken.client_id` — Google OAuth `sub` or an API-key name … starts NONE, filled by `set_subject` when packet 39 admits the login."* This is **Model B, 1 principal ↔ 1 subject.**

Ruling **B** (multiple providers concurrently) + ruling **C** (one principal may hold >1 OAuth identity: Google + MS → the one principal) require **principal 1—\* oauth_identity**. A single `option<string>` UNIQUE column cannot hold both a Google `sub` and a Microsoft `sub` for one principal. So the re-cut must resolve one of:
- **(a) New child table** `oauth_identity` (principal 1—\* oauth_identity), each row `(issuer, subject)` UNIQUE, `record<principal>` owner link — mirrors the *existing* `principal_key` 1—\* pattern (49 already did exactly this shape for API keys). `principal.subject` is then retired/repurposed, or kept only as a denormalised convenience. This is the clean fit for rulings B+C and reuses a proven store idiom.
- **(b) Keep the single `subject`** and accept 1 OAuth identity per principal — contradicts ruling C. Not viable unless the operator narrows C.

Note the API-key identity is ALREADY a 1—\* child (`principal_key`, owned by `record<principal>`, resolved by `PrincipalKeyStore.verify → Principal + key name`). So option (a) makes OAuth identities symmetric with API-key identities — arguably the most consistent design. **Store-law check (§1.8):** a `(issuer, subject)` composite UNIQUE over two REQUIRED columns is a plain UNIQUE (no `option<>` in the key) — clean, no multiple-NONE subtlety. This is well-supported.

### §O-2 — Identity-key tension: email (ruling C) vs (issuer, sub) (scout recon)
- Ruling C: principal keyed by **EMAIL**, dedup by email. The 48/49 schema agrees — `email` is the REQUIRED UNIQUE admission key; `set_subject`/`get_by_subject` are the runtime binding.
- Scout recon (provisional): key the OAuth identity by **`(issuer, sub)`** because `sub` is universally present and stable, while `email` is provider-populated/best-effort and hinges on `email_verified`.
- These are NOT actually in conflict IF option §O-1(a) is taken: the **principal** stays email-keyed (admission), and each **oauth_identity** child is keyed by `(issuer, sub)` (runtime). The email→principal link is the admission decision (admin pre-creates by email); the `(issuer, sub)`→oauth_identity→principal link is the login decision. The open question the operator must rule: **how does a first Google login find its principal?** Options: match the token's verified email to a pre-created principal's email, then bind `(issuer, sub)`; OR require the admin to pre-register the `(issuer, sub)` directly. The email-match path re-introduces `email_verified` as security-load-bearing (a Workspace/consumer-Google variance the prior design already had to handle). This is a real fork — detail belongs in the design doc.

### §O-3 — Enforcement mechanism: R13/R16 SUPERSEDED by packet-59 middleware
The prior design's read-only enforcement (§7, R13, R16) was built on `mcp.server.fastmcp` internals — a scoped `ToolManager` subclass whose `get_tool`/`list_tools` gate, plus a battery of `_setup_handlers` AST pins to catch the "dead-on-wire" class (WB30→WB48→WB93→WB100). **Packet 59 (DONE + DEPLOYED 2026-08-16) migrated lore onto standalone `fastmcp>=3.4,<4`, whose `on_call_tool` (refuse-before-body) + `on_list_tools` (hide from `tools/list`) middleware gate ON THE WIRE.** Per fastmcp §7, the re-cut:
- **DROP:** scoped `ToolManager` subclass, R16 `_setup_handlers` AST pins, `test_wire_discipline.py` (referent gone — the construction-time-binding root cause is dissolved).
- **KEEP:** per-request `AuthContext`/`PermissionResolver` identity model (forward-compatible).
- **RE-EXPRESS:** F3 session-resumption pin → per-request identity-isolation pin.
- **CARRY (load-bearing, NOT redundant):** the derived-∀-EFFECT pin (observe `call_next`/`run` never entered on refusal) — middleware REINTRODUCES placement as a free variable (the WB48 class).
- Enforce read-onlyness on **BOTH** hooks — `on_call_tool` alone silently drops the #295 VISIBILITY half.
- Principal seam: read via `fastmcp.server.dependencies.get_access_token()` (spike-proven stateful+stateless; hardened superset; closes the token-refresh bound). The `#295` "gate VISIBILITY not invocation" structural leg is OWNED by this packet (INDEX, operator 2026-08-09).

### §O-4 — What survives / is superseded / is new (PRELIMINARY map)
- **SUPERSEDED:** R12 (flat-file email roster) → the 48/49 `principal` DB (standing Log override). R13/R16 enforcement apparatus → fastmcp middleware (§O-3). The kill-switch "delete roster line" → `lore-adm suspend/delete` + `principal.status` (49's verbs already exist).
- **LIKELY SURVIVE (re-anchored onto the new substrate):** R2 (reuse Price Paper GCP client — but ruling B needs an MS/Entra client too, a new fork), R3/R4 (hostname + hades SNI edge + lore-caddy), R5 (`client_id` inline non-secret), R6 (Origin policy under M-1), R7 (no domain rule — now a principal-admission concern, not a roster parser), R8 (read-only derived from `ToolAnnotations.readOnlyHint`), R9 (Host/Origin one-derivation), R10 (identity minting — re-cut for N providers), R15 (`host_is_loopback` fail-closed predicate), the three-posture model (LOOPBACK/LAN_BEARER/HOSTED_OAUTH — but LAN_BEARER's roster is now `principal_key`).
- **NEW (from rulings B/C/C' + fastmcp):** the N-provider `MultiAuth` router question (the recon flags: fastmcp `MultiAuth` accepts tokens from N verifiers but owns only ONE interactive OAuth-proxy login route → "Google OR Microsoft INTERACTIVE login" is a GAP needing a router/per-IdP sub-apps — ruling B fork); the OAuth-server-config home (C' — framework kwargs vs lore-adm DB); the admission-on-first-login flow (§O-2).

### §O-5 — Operator ruling 2026-08-21 (provider count) — FOLDED (ledger #5092)
Resolves the multi-provider fork (ruling B). Design now proceeds UNDER these, not toward them:
1. **MVP ships ONE OAuth provider only** — Google (prior R2: reuse Price Paper GCP client) unless I surface a reason to change. Do NOT implement multi-auth in the MVP build.
2. **Design MUST stay EXTENDABLE to N providers** — identity model, config, and enforcement all provider-agnostic.
3. **Pre-ruled conditional (I make the call, threshold stated):** multi-auth EASY on fastmcp (judged vs the scout's effort/mechanism finding) → DO it now; else → keep the OPTION OPEN as a clean seam and DEFER with a NAMED re-open trigger (deferral / PIN-THE-MISS law). Escalate only if genuinely ambiguous.
4. **Identity model stays ruling-C-shaped REGARDLESS:** principal keyed by email; principal 1—\* oauth_identity; `(issuer,sub)`→principal. One provider now = one oauth_identity row per principal; the relation supports N.
5. **Config:** single-provider kwargs from `lore.yaml` + lore-secrets; provider selection is a config-shaped seam (2nd provider = a config block, not a rewrite). Do NOT build DB-stored OAuth configs (ruling C' stays optional).
6. **Enforcement** (fastmcp AuthCheck / `on_call_tool`/`on_list_tools` middleware) is already provider-agnostic (acts on the resolved principal, not the IdP) — no change.

**⚠ The one thing the ruling's "costs ~nothing" premise does NOT account for, which I will surface in the design doc (not silently absorb):** the ruled child-table `oauth_identity` model is NOT the shape the 48/49 substrate SHIPPED. Packet 48 built `principal.subject` as a SINGLE `option<string>` UNIQUE column with `get_by_subject`/`set_subject` as 39's admission/fill primitives (its docstring: *"Google OAuth `sub` or an API-key name"*). Moving OAuth identities to a `(issuer,sub)` child table means:
- a NEW `oauth_identity` table + DDL slice + a store class (cleanly cloneable from the shipped `PrincipalKeyStore` 1—\* pattern — moderate, well-trodden, but NOT nil),
- a decision on the now-vestigial `principal.subject`: **retire** it (it is shipped and referenced by 48/49 code/tests — a delete/replace with a removed-behaviour inventory) vs **repurpose/leave** it (e.g. a denormalised "primary subject" convenience, or keep it ONLY for the api-key-name binding while OAuth moves to the child table).

Neither is "~nothing", but the child-table path is the right extendable shape and reuses a proven idiom. I'll carry this as an explicit design decision (with the removed-behaviour adjudication if `principal.subject` is retired) and flag the premise to the operator so they can correct the estimate or narrow scope if they intended the MVP to just use the shipped single-column `subject` for now (a legitimate cheaper option: single `principal.subject` for the single-provider MVP + the child table as a NAMED-re-open-trigger seam for provider #2 — this is the "keep the option open, defer with a trigger" shape the ruling itself blesses in point 3, applied to the SCHEMA rather than the login route).

### Standing tensions remaining (post-ruling)
- **Schema build size vs "~nothing" premise** (§O-5 ⚠) — surface to operator; my recommendation ships in the doc.
- **Admission flow / `email_verified` as security-load-bearing** if first-login binds by verified email (§O-2) — to settle in the doc.
- **R2 second-provider console cost** — moot for the single-provider MVP (Google client already proven); re-arms only if multi-auth is done-now.

---

## STATUS
Standing by for: (1) `REPORT-scout-fastmcp-oauth-39.md` (hard input, ruling A — also gates my multi-auth easy-vs-defer call, §O-5.3), (2) the operator/lead "write the design doc" ask (lead directed: hold the full doc until the scout's report lands). Idle-between-questions is benign and expected. When asked, deliverable is a re-cut design doc under `docs/design/` per the brief's scope list, designed UNDER the #5092 ruling.
