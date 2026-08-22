# Packet 39 RE-CUT — hosted-security OAuth for lore (resource-server model, standalone fastmcp)

**Author:** design-sidecar-39-2 (Fable), 2026-08-21, at working tree `9a10604` (branch
`feat/surreal-unification`).
**Nature:** DOC + recommendations. The operator RULES; this doc records the rulings already
made, recommends where a recommendation is asked for, and surfaces the residual forks (§11).
**Authority folded in:** operator ruling `#5092` (provider count — single-provider MVP,
extendable seam) and the lead's consolidated GO directive `#5098` (rulings 1–5), both on
`lore_comms` session `pkt39-recut`; the 2026-08-21 provider-approach ruling in lore memory
(`lore_recall("oauth providers")`); the 2026-08-21 packet-39 resume-state memory.
**Supersedes (in scope) the stale parts of** `docs/design/2026-07-31-packet39-google-oauth.md`
(R1–R16). That doc's rulings are adjudicated item-by-item in §9; where this doc and it
disagree, THIS doc governs — the disagreements are driven by three things that landed AFTER it:
the 48/49 principal substrate, the packet-59 standalone-fastmcp migration, and the operator's
dismissal of the "configurable issuer = downgrade attack" rationale.

**Evidence base (READ, not recalled — READ-THE-DOCS-THEN-VERIFY law; the two scout reports are
archived at `docs/plans/v2/receipts/2026-08-21-packet39-recut/`):**
- `receipts/2026-08-21-packet39-recut/REPORT-scout-fastmcp-oauth-39.md` — fastmcp 3.4.7 OAuth
  surface, per-capability framework-vs-handroll verdicts, all cited to installed source
  (`.venv/.../fastmcp`).
- `receipts/2026-08-21-packet39-recut/REPORT-scout-router-module-39b.md` — the resource-server
  REFRAME + the multi-provider seam target; the fastmcp-vs-SDK stack discrepancy flag.
- HEAD `loremaster/loremaster/server.py` (`build_mcp_server`, `build_asgi_app`,
  `_register_tools`, `ToolTraceMiddleware`, the `readOnlyHint` partition ~`:10444`),
  `loremaster/loremaster/auth.py` (current api-key gate), `loremaster/loremaster/principals.py`
  + `principal_keys.py` + the `principal`/`principal_key` DDL in `store/surreal_schema.py`.
- `docs/reference/surrealdb-31-capabilities.md` (store law; §1.8 the `option<>` UNIQUE fact).

**Consumer Law + Trust Doctrine bind every surface this doc pins** (errors, renders, the
refused-tool listing, teaching prose). lore's consumers are AGENTS.

---

> ## ⚠ SUPERSEDING UPDATE 2026-08-21 — THIS PACKET IS NOW READ-ONLY HOSTED; ALL WRITE → THE RBAC PACKET
> Read this before anything below. After F4 was ruled, the operator commissioned a foundational
> **authorization model** — `docs/design/2026-08-21-lore-authorization-model.md` (per-row
> ownership + a 5-tier scope lattice + one in-process PDP over the SurrealDB graph) — because
> coarse role-gated write is both useless (members can't write their own comms/memory/tasks) and
> unsafe (no row isolation) for lore's multi-writer tools. Consequences for THIS packet, operator-RULED:
> - **The `HOSTED_OAUTH` surface is READ-ONLY.** Hosted principals (member AND admin) reach the
>   read-only code/docs corpus only; every mutating tool is refused to every hosted principal.
> - **ALL hosted write moves to the RBAC packet** — member row-scoped write AND admin superuser.
>   **The F4 role-gated-write ruling below is SUPERSEDED** (admin does NOT get hosted write here).
> - **`LOOPBACK` + `LAN_BEARER` are UNCHANGED** — the trusted local/LAN fleet keeps full write (it
>   is the coordination substrate; RBAC tightens it later, not now). The earlier **F7 api-key
>   role-gating is deferred to RBAC** (LAN api-keys keep full write).
> - **Forward-compat SEAMS this packet MUST still ship** (so RBAC is not a rewrite): (1) the
>   resolved identity carries `principal.role` AND an optional `(principal, agent)` binding;
>   (2) `role → capability` stays a FUNCTION, never a hardcoded `admin = +lore:write`, so RBAC
>   extends it; (3) the #295 middleware is the coarse TOOL-capability layer, designed to COMPOSE
>   with RBAC's row-level PDP (two layers, both must pass — neither preempts the other).
> - **⚠ DEPLOY COUPLING (RULED): NO 39-alone rebuild/redeploy.** 39's build may complete (green
>   gates, read-only) and SIT; the first hosted deploy is 39 + RBAC together (read + row-scoped
>   write). There is never a read-only-hosted production interim.
>
> **Effect on the sections below:** §0 Q4, §3.3, §3.5, §7, §9, §13 describe the now-SUPERSEDED F4
> role-gated write; they are kept for provenance and marked at point of use. **Current truth:
> hosted = READ-ONLY, write = RBAC. Where a section and this banner disagree, THIS BANNER GOVERNS.**

---

## 0. Ruling summary — the re-cut deltas

| # | Question | Ruling (authority) | Maps onto prior R# |
|---|---|---|---|
| Q1 | Identity model for the MVP | **"email now, seam later."** Single-provider Google MVP admits by the VERIFIED Google email (**`email_verified == true` is an EXPLICIT admission precondition** — operator ruling `#5100.F1`) and REUSES packet-48's shipped `principal.subject` column — no new schema now. The `(issuer,sub)` `oauth_identity` child table is a DOCUMENTED named-re-open-trigger seam, built at provider #2 (operator `#5098.1`) | supersedes R10/R11 identity + R12 substrate |
| Q2 | Multi-provider architecture | lore is a **RESOURCE SERVER** verifying bearer tokens (`LoreTokenVerifier`), NOT an OAuthProxy/authz-server. No `/authorize` on lore, no hand-rolled login router. MVP = single provider (Google). Multi-provider SEAM = fastmcp-native `RemoteAuthProvider(authorization_servers=[…])` + `MultiAuth`/issuer-branch multi-verifier (reuse `AzureJWTVerifier` for MS). Broker = OPTIONAL/`keep_with_trigger` (`#5098.2`, scout 39b §4) | reframes prior R2/R4's implicit single-IdP |
| Q3 | Which fastmcp stack | **STANDALONE `fastmcp` 3.4.7** (`FastMCP(auth: AuthProvider)`, `mcp.http_app()`) — NOT the mcp-SDK FastMCP the prior §4/§6 wired (`auth=AuthSettings/issuer_url/token_verifier`). Rewrite §4/§6 (`#5098.3`, scout 39b §6.1) | **supersedes prior §4/§6 wiring** |
| Q4 | Enforcement (#295) | **⚠ SUPERSEDED by the RBAC model (see banner): hosted is READ-ONLY; write → RBAC. The role-gated-write text in this cell is retired.** ~~Read-only is the FLOOR, not the ceiling (operator ruling `#5100.F4`).~~ The DURABLE part that survives: ONE default-deny `on_list_tools`/`on_call_tool` middleware keyed on `ToolAnnotations.readOnlyHint` gates hosted principals to read-only tools; it is the coarse TOOL-capability layer that COMPOSES with RBAC's row-level PDP. Original F4 text follows for provenance: ONE default-deny guard (a `on_list_tools`/`on_call_tool` middleware) keyed on lore's EXISTING `ToolAnnotations.readOnlyHint` **AND the principal's role/scope**: a mutating tool is refused UNLESS the principal carries `lore:write` (minted from `principal.role == admin`). VISIBILITY + dispatch gated; **coverage is a CHECKED VARIABLE**; the #295 EFFECT pin GAINS A ROLE AXIS (member denied+invisible, admin allowed+visible). This is the packet-59 seam that dissolves the WB30→WB100 wire-dead class (`#5098.4` + `#5100.F4`, scout 39a EXTEND-3) | **supersedes R13/R16 + the blanket read-only framing** |
| Q5 | Config substrate | Framework-native kwargs from lore's env-file idiom (`_resolve_env_file`→`--env-file` per-slug `.env`); `base_url` in `lore.yaml`; composition root reads env→builds provider→`FastMCP(auth=…)`. DB-stored OAuth config is OPTIONAL, not built (ruling C', `#5098.5`, scout 39a EXTEND-4) | **supersedes R12** (roster) + prior §5 config |

**§11 fork rulings folded (operator `#5100`):** F1 CONFIRMED (email-keyed admission; `email_verified == true` an explicit precondition) · **F4 RULED — ROLE-GATED WRITE** (read-only is the floor; `admin`/`lore:write` grants hosted write; member stays read-only — reverses this doc's original "no hosted write" recommendation) · F3 LEAD-RATIFIED (reuse `GoogleTokenVerifier`) · F2/F5/F6 as dispositioned (visibility / defer / defer). The role-gated posture is woven through §1, §3.2, §3.3, §3.5, §7, §9, §13 below.

**The operator also dismissed** the prior design's "configurable issuer = downgrade attack"
rationale (`lore_recall("oauth providers")`, 2026-08-21): providers WILL be configurable/
swappable. The downgrade concern is dissolved because a provider change is an authenticated
admin op (editing the per-slug `.env` + a recreate is an operator action). So prior §4's
"issuer URL hardcoded, never config" is SUPERSEDED — the issuer is config, sourced from the
env-file, resolved only at the composition root.

---

## 1. Threat model (paste into the verifier module docstring, updated for the resource-server model)

> **Who this gate is FOR:** an operator-curated set of **principals** (rows in the packet-48
> `principal` table, admitted by email via `lore-adm`), each proving control of an
> allowlisted identity to claude.ai's OAuth connector, reaching lore's tool surface over the
> public internet — plus the existing per-principal API-key principals (local agents / LAN
> clients). lore is a **RESOURCE SERVER**: it VERIFIES a bearer token that claude.ai obtained
> from the IdP; it never runs an OAuth authorization flow itself (no `/authorize`, `/token`,
> DCR on lore). Admission = an active `principal` row exists for the verified identity;
> authorization = `principal.role`.
>
> **The authorization floor is READ-ONLY; WRITE is ROLE-GATED (operator ruling F4).** A
> `member` principal — hosted OR api-key — reaches the read surface ONLY: every mutating tool
> is invisible and uncallable to it, **provably** (§7, the #295 EFFECT pin over a member
> fixture). An `admin` principal (`principal.role == admin` → `lore:write` scope) additionally
> reaches the write surface. Write over the public internet is therefore a real, in-scope
> capability held by a deliberately small, operator-curated set of admin principals — NOT the
> whole admitted set. `principal.role ∈ {member, admin}` is packet-49's shipped closed domain;
> "member" is the read-only floor (the lead's "member/player" shorthand maps to the single
> non-admin role `member` — a THIRD role would be a new closed-domain change, a fork).
>
> **Two distinct layers, never conflated:** the PROVIDER AUTHENTICATES (verifies the token →
> a verified identity), the `principal` table AUTHORIZES (identity → active principal →
> role → scopes). A provider change is an authenticated admin op; the principal table is the
> admission authority. This layering is what dissolves the downgrade concern.
>
> **Who it is NOT for / what it does NOT provide** (carried from prior §1, still true):
> - **Per-content ACL** — every admitted principal reads the WHOLE corpus (CLAUDE.md, every
>   packet, every receipt, memory, the findings ledger — a map of this system's known bounds).
>   Admission is all-or-nothing per project; do NOT reason from "the lore repo is public"
>   (the posture must hold for pp-odoo / demand_intelligence too).
> - **An allowlisted principal who turns hostile** — a MEMBER is capped at reading (exfiltration
>   of what they read is the residual, not closable here); an ADMIN can additionally WRITE the
>   store (the accepted role-gated-write bound — confused-deputy / store-poison, §1 mechanical
>   verdicts). Admin is a deliberately small, curated set; that scoping IS the mitigation.
> - **Anthropic** — claude.ai holds the token and proxies every call. Accepted, written down.
> - **Tenancy / DoS / per-caller rate limiting** — the real client IP is not recoverable at
>   this edge (prior investigation M12). Ledgered bound.
> - **A hostile author with commit access** — findings #137/#138 (the exec/code seam) govern
>   that; their re-open triggers were consulted (this bullet is the receipt) and do NOT fire. This packet adds READERS
>   plus a small admin WRITE set (F4), but a hosted admin writes DATA (store rows: findings,
>   tasks, memory, comms — each carrying `created_by`/`actor` provenance), NEVER code — so the
>   exec-seam threat model is unchanged. (If hosted write ever reached a code/exec surface, that
>   is a NEW fork and re-fires #137/#138.)
>
> **Mechanical verdicts** (so an auditor need not re-litigate intent):
> - "a Google-verified token whose `aud` is a DIFFERENT OAuth client is accepted" — **BLOCKER**
>   (the `aud`/audience check is the only thing distinguishing OUR consent from any other app's).
> - "a token whose `email_verified` is false/absent is admitted" — **BLOCKER** (F1: verified
>   email is the admission key, so an unverified email is not an admission fact).
> - "an identity with no active `principal` row gets in" — **BLOCKER**.
> - "a suspended principal (`status = suspended`) is admitted" — **BLOCKER**.
> - "an expired principal (`expires_at` in the past) is admitted" — **BLOCKER**.
> - "a **MEMBER** principal (no `lore:write`) can see or call a mutating tool" — **BLOCKER**
>   (#295; the guard observes the EFFECT, not just the exception — §7). This is THE property
>   the role-gated floor must prove, over both hosted and api-key members.
> - "an **ADMIN** principal (`role == admin` → `lore:write`) calls a mutating tool" —
>   **INTENDED** (F4 role-gated write; write over the internet is the admin capability).
> - "an ADMIN principal's agent is prompt-injected into issuing a write (confused deputy)" —
>   **ACCEPTED BOUND**, not a lore-closable defect: the admin role IS the write trust; lore
>   cannot police an admin's own agent. Mitigation is scoping admin to the minimum set and the
>   store's own validation/provenance (writes carry `created_by`/`actor`). Re-open: if hosted
>   write ever needs per-tool or per-principal write scoping finer than the role bit.
> - "a stolen ADMIN api-key poisons the store" — **ACCEPTED BOUND**: a leaked key carries its
>   principal's role; the remedy is `lore-adm revoke-key` (hash-only storage, immediate). The
>   write consequence is why `admin` is a deliberately small set. (A leaked MEMBER key cannot
>   write at all — least-privilege limits the blast radius.)
> - "`/.well-known/oauth-protected-resource/mcp` is world-readable" — **REQUIRED** (RFC 9728).
> - "a clever attacker forges an `Origin`" — NOT a defect (the token is the gate; Origin was
>   never a control against non-browser clients).
>
> **KNOWN BOUNDS** (each pinned, each with a re-open trigger):
> - **Anonymous path enumeration** (prior ruling S1): an unknown path returns 404 not 401, so
>   the two-path route surface is enumerable where no edge fronts lore. Disclosure is a route
>   list, not data. Re-open: a route whose mere existence is sensitive.
> - **Extension tools are never hosted-servable** (prior R14): the core cannot audit a
>   project-authored extension callable, so `_register_extension_tools` registers every
>   extension tool `readOnlyHint=False` (server.py:12202, CONFIRMED at HEAD) → refused to
>   hosted principals by the same partition. Re-open: an extension needing hosted exposure ⇒
>   an explicit no-default read-only declaration on `ToolSpec` PLUS a verification story.
> - **MVP `principal.subject` holds one issuer's `sub`** — safe for ONE provider; the moment
>   provider #2 is added the durable key must become `(issuer, sub)` (§3, §5).

---

## 2. The stack reconcile (Q3) — this is the load-bearing rewrite

The prior design (§4/§6) was written against the **mcp SDK's** `FastMCP`
(`auth=AuthSettings(issuer_url=…, resource_server_url=…, required_scopes=…)`,
`token_verifier=…`, `TransportSecuritySettings`). **That API is not what lore imports.**
Packet 59 (DONE + DEPLOYED 2026-08-16) migrated lore onto the standalone `fastmcp` framework.
Ground truth at HEAD `9a10604`:

- `from fastmcp import Context, FastMCP` — `server.py:68`.
- `build_mcp_server` constructs `mcp: FastMCP = FastMCP(..., middleware=[ToolTraceMiddleware()])`
  — `server.py:10259`, the ctor at `:10366`. **No `auth=` is passed today** (api-key gating is
  the hand-rolled ASGI wrapper below).
- `build_asgi_app` builds `mcp.http_app(path=…, transport="http", stateless_http=…)`
  (`server.py:12403`), wraps it in `OriginValidationMiddleware` (`:12413`) and — when auth is
  enabled — the hand-rolled `BearerAuthMiddleware` (`:12375`, from `auth.py:208`).
- `auth.py` at HEAD (366 lines) still ships the pre-migration hand-roll: `AuthVerifier` (ABC),
  `ApiKeyVerifier`, `BearerAuthMiddleware`, `OriginValidationMiddleware`, `build_api_key_verifier`.
  **There is no `LoreTokenVerifier` yet** — the re-cut builds it as a **fastmcp `TokenVerifier`**.

**The standalone-fastmcp auth model** (scout 39a §VERIFY, all cited to installed source):
- `FastMCP.__init__(..., auth: AuthProvider | None = None)` — `fastmcp server/server.py:329`;
  `self.auth = auth` `:424`. `AuthProvider` is the fastmcp base; its subclasses are
  `TokenVerifier` (`auth.py:366`), `RemoteAuthProvider` (`auth.py:413`), `OAuthProxy`,
  `MultiAuth` (`auth.py:510`).
- `mcp.http_app()`/`create_streamable_http_app(auth=…)` wires EXACTLY ONE provider
  (`http.py:590-595`): one `BearerAuthBackend` middleware + `auth.get_routes(...)` once. There
  is no "list of auths" — this is why multi-provider is a multi-VERIFIER problem (§5), not a
  multi-app problem.
- The in-tool principal accessor is `fastmcp.server.dependencies.get_access_token()`
  (`dependencies.py:467`) → `AccessToken | None`, carrying `.claims` / `.scopes` / `.subject`.
  The 2026-08-15 spike MEASURED this works from inside fastmcp middleware, stateful AND
  stateless, on the wire (`lore_recall("fastmcp migration")`).

**So the re-cut's §4/§6:** `LoreTokenVerifier` is a `fastmcp.server.auth.auth.TokenVerifier`
subclass; the composition root hands it (wrapped per §5) to `FastMCP(auth=…)`; the SDK
`AuthSettings`/`issuer_url`/`token_verifier=`/`TransportSecuritySettings` wiring of the prior
doc is retired. `.well-known` protected-resource metadata is served by
`RemoteAuthProvider(token_verifier=LoreTokenVerifier, authorization_servers=[…])` (§4/§5), the
fastmcp-native multi-AS advertiser — which is ALREADY multi-provider-ready (a `list` arg).

---

## 3. Identity model + MVP schema (Q1) — reuse `principal.subject`, seam the child table

### 3.1 The two layers, on the shipped 48/49 substrate
- **AUTHENTICATION** (the provider): verify the bearer token → a verified identity
  `(email, sub, iss, …)` read from `AccessToken.claims` (⚠ read `sub` from `claims["sub"]`, NOT
  `.subject` — fastmcp's `GoogleTokenVerifier`/`JWTVerifier` leave `.subject` None, scout 39a
  §C3 Precision A).
- **AUTHORIZATION** (the `principal` table): `email → active principal → role → scopes`.

### 3.2 MVP admission flow (single-provider Google, "email now")
1. **Admin pre-creates** the principal by email: `lore-adm add --email <addr>` →
   `PrincipalStore.create(email=…)` (subject NONE until first login). No new schema.
2. **First Google login:** claude.ai presents a Google-verified token; `LoreTokenVerifier`
   verifies it and extracts the email + `email_verified` from `claims`. **Admission precondition
   (F1, RULED): `email_verified == true`** — a token whose email is unverified or absent is
   denied BEFORE any principal lookup (accepting Google's `email_verified` as
   security-load-bearing is the ruled trade; Google's `email_verified` is genuine when the email
   scope is granted — scout 39a §EXTEND-2; §4.1 pins the scope requirement). Then normalise the
   email (§3.4) and admit: `PrincipalStore.get_by_email(email)` → admit iff a principal exists
   AND `status == active` AND (`expires_at` is None OR in the future). On first admission, bind
   the runtime subject:
   `set_subject(email=…, subject=<google sub>)` — the packet-48 fill-on-login primitive, whose
   orchestration guard (check `get_by_subject` first, fill only a NONE row) lore owns (48
   docstring; the 2026-08-21 resume memory). Idempotent re-login is safe (setting a subject to
   its own current value is not a UNIQUE conflict — 48 `set_subject` docstring).
3. **Returning login:** `get_by_subject(<google sub>)` is the O(1) fast path; a miss falls back
   to `get_by_email`. Either way admission re-checks `status`/`expires_at` on EVERY request
   (no admission caching — see §4.4).
   > ⚠ **DESIGN DECISION (I recommend, flagging the fork in §11-F1):** admission KEY is the
   > verified EMAIL, which makes `email_verified` security-load-bearing for Google. This is
   > acceptable for Google (its `email_verified` is genuine when the email scope is granted —
   > scout 39a §EXTEND-2). The alternative (admit by `(iss,sub)` directly, email as display
   > only) is the multi-provider shape and is deferred with the child table. For a
   > single-Google MVP, email-keyed admission is the operator's ruled "email now".

### 3.3 Identity minting — PER PRINCIPAL, not per credential (#206)
The `AccessToken` the verifier mints identifies the PRINCIPAL, not the raw credential:
- **Google branch:** on admission, mint `AccessToken(token=…, client_id=<configured Google
  client_id>, scopes=<from principal.role, §3.5>, subject=<principal identity>,
  claims={"iss": <google issuer>, "email": <normalised email>, "sub": <google sub>, …})`.
- **API-key branch** (#206, from the resume memory): `PrincipalKeyStore.verify(presented) →
  KeyVerification(principal, key_name)`; mint `AccessToken(..., client_id=f"api_key:{principal.email}",
  subject=principal.email, scopes=<from principal.role, §3.5>)`. The identity is the PRINCIPAL
  (email), never the key name — a per-key mint would make two keys of one human read as two
  principals (#206).
- **⚠ Scopes are role-derived for BOTH branches (F4), NOT provider-derived.** A member api-key
  principal gets `{lore:read}`; an admin api-key principal gets `{lore:read, lore:write}` —
  exactly as for hosted principals. This is a deliberate CHANGE from this doc's original draft
  (which gave api-keys unconditional write): under role-gated write, an api-key carries its
  principal's role, nothing more (least-privilege; §3.5). Consequence in §7 / §11-F7.
- **Rider (ROUTING-IS-NOT-SHARING):** the api-key branch resolves through
  `PrincipalKeyStore.verify` (mutation: break `verify` → api-key auth pins RED).

### 3.4 Normalisation (one implementation in `lorerunes`)
`normalize_email = NFKC → casefold → strip`, applied to BOTH the admission email (`lore-adm`
already stores what the admin typed — the roster line equivalent) and the token's presented
email. This already lives / is ruled for `lorerunes` (prior §5, R12 normaliser). Pins: mixed-case
Google email admitted against a lowercase-stored principal; a Cyrillic-homograph does NOT match
its Latin lookalike; gmail dot/plus aliasing is NOT stripped (documented bound — the stored email
must be the address Google reports, verbatim-after-normalisation). **Mutation:** change the
normaliser → both the `lorerunes` unit pins AND the loremaster admission pins redden.

### 3.5 role → scopes (⚠ F4 SUPERSEDED by RBAC — see banner)
> **CURRENT TRUTH:** the HOSTED surface is read-only, so a hosted principal (member OR admin) gets
> `{lore:read}` — no hosted write scope is minted here; ALL write (member row-scoped + admin
> superuser) is RBAC's. What THIS packet still does: **mint `principal.role` into the identity
> (forward-compat, so RBAC can act on it) but do NOT act on it for hosted write** — hosted is
> uniformly read-only regardless of role. Keep `role → capability` a FUNCTION so RBAC extends it;
> do NOT hardcode `admin = +lore:write`. The `LAN_BEARER` api-key branch keeps full write
> (unchanged fleet; F7 role-gating deferred to RBAC). The original F4 table follows for provenance.

`principal.role ∈ {member, admin}` (packet-49's shipped closed domain — `_PRINCIPAL_ROLES`).
**Scope is a pure function of role, provider-agnostic:**

| `principal.role` | minted scopes | surface |
|---|---|---|
| `member` (least-privilege floor) | `{lore:read}` | read tools only — every mutating tool invisible + uncallable (§7) |
| `admin` | `{lore:read, lore:write}` | read + write |

- The **same** table governs a hosted (Google) principal and an api-key principal — a member is
  a member however they authenticate (least-privilege). The read-only guard (§7) keys on the
  tool's `readOnlyHint` AND the principal's `lore:write` scope.
- Scope constants `"lore:read"`/`"lore:write"` and the `role → scopes` map live ONCE in
  `lorerunes` (prior §6, shared policy), so the verifier that mints them, the guard that checks
  them, and the instructions renderer that names them share one home. **Mutation:** change the
  `role → scopes` map → the mint pins AND the guard pins redden.
- **`admin` is the write elevation** (no longer "reserved"): an admin principal writes over the
  internet (hosted) or the LAN (api-key). It is a deliberately small, operator-curated set
  (`lore-adm add --email … --role admin`) — the threat-model bounds in §1 (confused-deputy,
  stolen-admin-key) are the accepted cost of that capability.
- ⚠ **A tool with `readOnlyHint is not True` and a principal WITHOUT `lore:write` = refused.**
  Default-deny survives the reversal: read-only is the FLOOR, write is an explicit grant, and an
  unclassified tool (`readOnlyHint is None`) or an unscoped principal lands read-only.

### 3.6 The child-table SEAM (multi-provider, DEFERRED — PIN THE MISS)
The shipped `principal.subject` is a SINGLE `option<string>` UNIQUE column — it holds ONE
issuer's subject. This is correct for one provider (one issuer namespace). It CANNOT hold a
Google `sub` AND an Azure `oid` for the same principal (scout 39a §EXTEND-2: `sub` is "unique
only per issuer"; the safe cross-IdP key is `(iss, sub)` / `(tid, oid)`).

- **Seam (built at provider #2):** a new `oauth_identity` child table — `record<principal>`
  owner link, `(issuer, subject)` composite UNIQUE (two REQUIRED columns → a plain UNIQUE,
  store §1.8 N/A), cloning the shipped `principal_key` 1—\* pattern
  (`_principal_key_statements`, `PrincipalKeyStore`). `principal.subject` is then either
  retired (a delete/replace with a removed-behaviour inventory) or kept as a denormalised
  "primary subject". Email becomes a resolved ATTRIBUTE, not the join key (scout 39a §EXTEND-2).
- **NAMED RE-OPEN TRIGGER:** *"the day a second OAuth provider is configured"* (an operator act:
  a second provider block in the env/config). A pin in `test_principal_schema.py` ASSERTS the
  single-`subject`-column model and carries the message *"KNOWN BOUND — single-issuer only; add
  the `oauth_identity` child table before provider #2 (design §3.6). If you added a second
  provider, this pin is the migration you owe."* (the PIN-THE-MISS instrument, findings
  #137/#138 class).
- **Why not build it now:** the operator ruled "email now, seam later"; building the child table
  now is real schema+store work (a clone of `PrincipalKeyStore`) for zero MVP benefit, and the
  MVP's single Google issuer makes `principal.subject` sufficient. The seam costs one pin.

---

## 4. Auth path (Q3 rewrite) — resource-server, single-provider Google, standalone fastmcp

### 4.1 `LoreTokenVerifier` — a fastmcp `TokenVerifier`
`class LoreTokenVerifier(fastmcp...TokenVerifier)` with `async def verify_token(token) ->
AccessToken | None`, two branches in this order:
1. **API key** — constant-time via the kept `ApiKeyVerifier` semantics, resolving through
   `PrincipalKeyStore.verify` → `KeyVerification(principal, key_name)` → mint per §3.3. No network.
2. **Google** — verify the Google token, then admit per §3.2. On any non-admission → `None`
   (fastmcp maps `None` → 401).

**Google token verification — REUSE the framework, do not hand-roll the tokeninfo POST:**
- **Packages verdict (scout 39a §4): USE-FRAMEWORK.** fastmcp ships `GoogleTokenVerifier`
  (`providers/google.py:57`, `verify_token:92`) which performs the Google token→identity call
  and populates `claims["email"]`/`email_verified`/`sub` (`google.py:174-192`) — the
  framework-packaged equivalent of the prior design's hand-rolled `_validate_google_token`
  tokeninfo POST. **The re-cut REUSES `GoogleTokenVerifier` for the crypto/HTTP** and wraps it
  with lore's roster admission (the only bespoke bit — packages-over-hand-rolling side-2).
  - ⚠ **Build-leg MUST READ `google.py:57-192` and CONFIRM three things against installed
    source** (READ-THE-DOCS-THEN-VERIFY; the prior hand-roll's hard-won facts are the checklist):
    (a) it POSTs the token in the BODY, never a URL query param (httpx logs URLs at INFO — a
    query param leaked a token into a journal once, prior §4); (b) `aud`/audience is checked
    against the configured `client_id` and a MISSING `aud` is a hard reject; (c) which HTTP
    endpoint it hits and whether it needs the email scope (default `GoogleProvider` scopes are
    `["openid"]` = NO email — scout 39a §C3 Precision B; the configured `required_scopes` MUST
    include an email scope or admission has no email to key on). If `GoogleTokenVerifier` does
    NOT check `aud` the way lore needs, wrap it or add the check — the `aud` check is a BLOCKER
    property (§1), not optional.
  - **`sub` is read from `claims["sub"]`, `email` from `claims["email"]`** — never `.subject`
    (fastmcp leaves it None; scout 39a §C3-A).
- If for any reason `GoogleTokenVerifier` cannot be reused (build-leg finds it does something
  lore cannot accept), the fallback is the prior design's hand-rolled tokeninfo POST — but that
  is a `bespoke` verdict that must cite what it READ in `google.py` proving the framework does
  not fit (not a doc, not this doc). Default expectation: reuse.

### 4.2 Caches (per-verifier-instance, never module-global)
- `cachetools.TTLCache` (already a dep, 7.1.6) for Google's verdict (token SHA-512 → verified
  identity), under a lock with **no `await` while the lock is held**; raw tokens never stored
  (SHA-512 key only). Split negative caching: 401/400 (definitive invalid) → negative-cache;
  5xx / timeout / transport → `None` WITHOUT caching (a Google blip must not lock a valid token
  out). `expires_at` minted and re-checked on positive-cache read.
- **Lifecycle rider** (global CLAUDE.md test law): a degradation pin — close the injected
  client → next `verify_token` recovers (lazily replaces it) rather than erroring forever; plus
  the autouse state-leakage reset.

### 4.3 Injected `httpx.AsyncClient`
Surfaced as a NEW keyword-only param on the composition seam (prior B4). Tests use
`httpx.MockTransport`; production uses bounded `httpx.Limits` + explicit timeouts. If
`GoogleTokenVerifier` owns its own client, inject at ITS seam instead — the build leg reads its
`__init__` and picks the hermetic seam (the repo's no-live-socket-in-suite pin forbids a real
socket).

### 4.4 Admission is NEVER cached
The cache holds the PROVIDER's verdict (token → verified identity) only. Admission
(`get_by_email`/`get_by_subject` + `status`/`expires_at` checks) is evaluated on EVERY
verification against the live `principal` table — so a `lore-adm suspend`/`delete`/expiry takes
effect on the principal's NEXT request, no residual window, no redeploy. This is the 48/49
substrate delivering exactly what R12's flat-file freshness ruling was reaching for, natively.
**Riders:** a suspended-mid-session principal is denied on the next request (fixture drives a
cache HIT on the token, asserted by transport call-count, and still denies); mutation — cache the
admission decision → the immediate-denial pin reds.

---

## 5. Multi-provider seam (Q2) — fastmcp-native, DEFERRED with a named trigger

**The reframe (scout 39b, load-bearing):** because lore is a resource server, the "two
interactive-login endpoints" problem does not exist — claude.ai runs the OAuth dance; lore only
verifies. Multi-provider = (i) advertise multiple authorization servers in the RFC 9728
protected-resource metadata, and (ii) verify tokens from multiple issuers. **Both are native.**

**The seam target (built at provider #2, not now):**
1. **Multi-AS advertising:** `fastmcp.RemoteAuthProvider(token_verifier=LoreTokenVerifier,
   authorization_servers=[google_issuer, microsoft_issuer], base_url=…)` — `authorization_servers`
   is a `list[AnyHttpUrl]` served in ONE `.well-known/oauth-protected-resource/mcp` (scout 39b
   §3, `auth.py:413-507`, `:493-496`). No collision, no second endpoint.
2. **Multi-verifier:** either `fastmcp.MultiAuth(verifiers=[google_verifier, azure_verifier])`
   (tries each in order, first non-None wins — `auth.py:591-610`) OR a single `iss`-dispatch
   branch inside `LoreTokenVerifier`. The MS/Entra side REUSES `fastmcp.AzureJWTVerifier`
   (`azure.py:696`, JWKS crypto derived from `tenant_id`) — `replace_with_adapter`, lore's roster
   admission wrapping the verified identity exactly as for Google.
3. **Identity:** at provider #2 the durable key becomes `(iss, sub)` / `(tid, oid)` via the
   §3.6 `oauth_identity` child table; email is an attribute (scout 39a §EXTEND-2).
4. **Broker option** (`keep_with_trigger`): a `KeycloakAuthProvider`/`WorkOSTokenVerifier`/
   `Auth0Provider` collapses N IdPs → one issuer/JWKS (uniform verified email, one `sub`
   namespace). Adds an operational component (run Keycloak, or pay WorkOS/Auth0). Trigger:
   operator wants "add an IdP without code", or IdP count > ~2, or cross-IdP identity-merge pain.

**Do-now-vs-defer recommendation (the operator pre-ruled conditional `#5098.3`):**
> **DEFER multi-auth; keep the seam open.** The scout evidence is that multi-provider is
> genuinely EASY on fastmcp (every hard piece is shipped: multi-AS advertising, JWKS
> verification, verifier multiplexing — scout 39b §4 "the gap the operator feared does not
> exist"). BUT "easy" is the seam, not the whole job: provider #2 also needs (a) the
> `oauth_identity` child-table migration (§3.6), (b) a real MS/Entra app registration + client
> (operator console work), (c) the cross-IdP identity-merge POLICY (which is lore domain logic,
> not a framework call — scout 39a §EXTEND-2 flags "same human across Google + Microsoft" as an
> operator merge policy). None of (a)/(b)/(c) has MVP value, and (b) is operator-gated. So: build
> the MVP so the seam is `RemoteAuthProvider(authorization_servers=[google], token_verifier=
> LoreTokenVerifier)` from day one (provider #2 = one more list element + one more verifier
> branch + the child-table migration), and DEFER the second provider with the named re-open
> trigger *"the operator elects a second IdP"*. This is exactly the ruling's "keep the option
> open as a clean seam, defer with a named trigger" — I judge multi-auth EASY-as-mechanism but
> NOT-free-as-feature (child table + console + merge policy), so the ruling's OTHERWISE branch
> applies. **Escalation check:** not genuinely ambiguous → no operator escalation needed; but
> the recommendation is surfaced here for veto.

---

## 6. Config model (Q5) — env-file kwargs, composition-root adapter

**No native env-factory in fastmcp** (scout 39a §C5, grep `FASTMCP_SERVER_AUTH` = 0). Providers
are built from explicit kwargs at a composition root. lore's env-file idiom already exists:

- `_resolve_env_file(project, explicit)` → `~/docker/mcp/lore-secrets/<slug>.env`
  (`lore_deploy.py:388-404`, `LORE_SECRETS_DIR:90`), passed to podman as `--env-file` (`:674`)
  → container process env. This is the VERIFIED per-slug secret idiom (`0700` dir, `0600` files).
- **Native path:** `LORE_OAUTH_GOOGLE_CLIENT_ID` / `_CLIENT_SECRET` / `_REQUIRED_SCOPES` (incl. an
  email scope) live in that `.env`; the lore **composition root** (server startup — the ONE
  place allowed to read `os.environ`, per lorerunes/brief-base secret-resolution law) reads env,
  constructs the provider + `RemoteAuthProvider`, and hands it to `FastMCP(auth=…)`
  (`server.py` build seam). This IS packages-over-hand-rolling: fastmcp has no env-factory, so
  the composition root is the missing ~env→kwargs adapter — thin, testable, not a re-implementation.
- **`base_url`/`resource_base_url`** (the public URL, per-deployment, non-secret) live in
  `lore.yaml`; secrets stay in the `.env`.
- **Provider selection is a config-shaped seam:** the MVP config names one provider (Google); a
  second provider is a SECOND config/env block, not a code rewrite (§5). The config model carries
  a `provider` kind so the composition root dispatches on it.

**Config shape (pydantic, `extra="forbid"`, on the wire):**
```python
class OAuthProviderConfig(_StrictModel):
    kind: Literal["google"]            # extendable: add "azure" at provider #2
    client_id: str                     # public (RFC 6749 §2.2), non-blank; resolved from env-ref
    required_scopes: list[str]         # MUST include an email scope for email-keyed admission
    # client_secret: env-ref only, resolved at composition root — NEVER inline (it IS confidential)

class AuthConfig(_StrictModel):
    enabled: bool = False
    mode: Literal["api_key", "hosted_oauth"] = "api_key"
    keys: list[AuthKey] = []           # per-principal API keys (principal_key) for local/LAN
    oauth: OAuthProviderConfig | None = None
    base_url: str | None = None        # public resource URL, non-secret; https-only validator
    allowed_origins: list[str] = []
```
- ⚠ **`client_secret` is CONFIDENTIAL** (unlike the prior design's `client_id`-only world): in
  the resource-server-with-`GoogleTokenVerifier` model the secret may be needed (unless a PKCE
  public client — scout 39a §EXTEND-4 `google.py:261-263`). It is env-ref + resolved only at the
  composition root, NEVER inline in `lore.yaml`, NEVER logged (prior §4's token-in-log lesson).
  The `client_id` stays inline-friendly (public) but sourcing it from the same env block is
  simpler and fine.
- **DB-stored OAuth config: OPTIONAL, NOT built** (ruling C'). It would add a store schema, a
  secret-at-rest problem, a boot-time store dependency, and admin surface (scout 39a §EXTEND-4).
  Env-file kwargs is strictly simpler and framework-native. Ledger DB-config as a follow-up if
  multi-tenant self-service auth is ever needed.

### Posture derivation — three postures (carried, renamed to the new mode literals)
A pure function in `lorerunes` over primitives → a `Posture` enum or a typed refusal (nearest
posture + exact missing/conflicting fields; posture names enumerated FROM the enum). Called at
`build_asgi_app` / `lore_deploy.py` verbs / `load_config`.

| Posture | requires | serves |
|---|---|---|
| `LOOPBACK` | loopback host ∧ auth disabled | no auth provider — unchanged local mode |
| `LAN_BEARER` | enabled ∧ `api_key` ∧ ≥1 principal_key path | `LoreTokenVerifier` api-key branch; no `.well-known` |
| `HOSTED_OAUTH` | enabled ∧ `hosted_oauth` ∧ oauth complete ∧ **loopback host** (the proxy comes to us) | `RemoteAuthProvider(LoreTokenVerifier, authorization_servers=[…])` — both branches + `.well-known` |

Everything else is a boot refusal naming its nearest posture + exact fix (the honest-failure
idiom). `host_is_loopback` stays the prior R15 fail-closed predicate (True iff literal
`localhost` or `ipaddress.ip_address(host).is_loopback`; an exception path may NEVER return True;
pinned as a PREDICATE over a 127/8 grid, never spellings). **In `HOSTED_OAUTH` the SDK gates
`/mcp` for EVERYONE** — local agents included — so local sessions authenticate with a
per-principal API key; the deploy step that flips the posture ships in the SAME wave as the
`.mcp.json`/lore-deploy key wiring, or every local session 401s (prior §5 atomic-cutover rider).

---

## 7. Read-only hosted enforcement (Q4 / #295) — one default-deny guard, coverage checked

> **⚠ SUPERSEDED FRAMING (see banner): hosted is READ-ONLY; the role-axis write text below is
> RBAC's, not this packet's.** CURRENT TRUTH for packet 39: in `HOSTED_OAUTH` **no** principal
> carries `lore:write`, so the guard refuses EVERY mutating tool to EVERY hosted principal —
> there is no member-vs-admin write axis in this packet. The guard is the coarse **TOOL-capability
> layer** (hosted → read-only tools only); RBAC's **row-level PDP** is a SECOND layer that lands
> later and decides WHICH rows a write touches. They COMPOSE (both must pass); neither preempts the
> other, and this packet's middleware must be built so RBAC's PDP layers on without conflict. The
> #295 EFFECT discipline (observe the body did NOT run, not just the exception) still applies to
> every hosted refusal. The role-axis text below (member-vs-admin write) is RETIRED to the RBAC
> packet and kept here for provenance.

**Original F4 framing (SUPERSEDED):** read-only is the FLOOR, not the whole surface. The guard
denies a mutating tool to a principal WITHOUT `lore:write`; an `admin` principal (with `lore:write`)
is permitted. The mechanism is unchanged — the guard was always keyed on "the principal lacks
`lore:write`" — but the population that HAS write is no longer empty: it is the admin set. The
enforcement gains a **role axis** (member denied+invisible, admin allowed+visible), and the #295
EFFECT pin must FORCE both fates.

**The classification ALREADY EXISTS at HEAD, keyed on the typed annotation** (server.py
~`:10444`): a partition DERIVED from each tool's `ToolAnnotations.readOnlyHint`, **deny-by-default**
(`readOnlyHint is not True` counts as mutating — so `None` = unclassified lands in `mutating`;
`:10451`). Every built-in tool is registered with an explicit annotation
(`_READ_ONLY_ANNOTATIONS` / `_SAVE_MEMORY_ANNOTATIONS` / `_INDEX_ANNOTATIONS` /
`_TASK_TOOL_ANNOTATIONS` / `_FINDINGS_TOOL_ANNOTATIONS` / `_COMMS_TOOL_ANNOTATIONS`), and every
EXTENSION tool is registered `readOnlyHint=False` (`_register_extension_tools`, server.py:12202,
CONFIRMED at HEAD). So "which tools mutate" is already declared data over BOTH registration paths.

**The mechanism (Q4 ruling):** ONE default-deny guard — a fastmcp `on_list_tools` +
`on_call_tool` **middleware** — keyed on that partition:
- `on_list_tools` **filters out** every tool whose `readOnlyHint is not True` when the ambient
  principal (via `get_access_token()`) lacks `"lore:write"` → the tool is INVISIBLE in
  `tools/list` (gate VISIBILITY, #295's structural leg).
- `on_call_tool` **refuses** the same set → the tool is uncallable, with a structured teaching
  refusal (posture name from the enum, tool name, why, and the remaining read surface).
- lore ALREADY runs an `on_call_tool` middleware (`ToolTraceMiddleware`, server.py:10031/10366)
  — the middleware seam is proven in-tree; this adds a second (or folds into a shared one; keep
  trace WRITE policy `_record_tool_trace` as ONE function, scout §DRY).

**Why middleware, not per-component `auth=`** (scout 39a §EXTEND-3 caveat, load-bearing): a
fastmcp tool with `tool.auth is None` is ALWAYS included (`server.py:687-698` fast-path). So a
per-component approach risks a future mutating tool shipping unguarded. A default-deny middleware
over the WHOLE surface has no such hole — but only if coverage is enforced:

**COVERAGE IS A CHECKED VARIABLE (the reach law, #344/#345 + #295):**
- The guard's reach = the set of registered tools it actually evaluates. Pin: enumerate the FULL
  registry (`mcp.list_tools()` / the registration set) and assert EVERY registered tool is SEEN by
  the guard's partition — a test goes RED when the registered set GROWS but the guard's observed
  set does not. Reach is DERIVED from the registry, never a hand-list.
- **The #295 EFFECT law (NOT the exception), now over a ROLE AXIS — FORCE BOTH FATES:** for
  every mutating tool in the registry,
  - **member fixture (no `lore:write`):** the tool is INVISIBLE in `on_list_tools` AND its body
    demonstrably did NOT run under `on_call_tool` (an invocation counter asserted zero / an
    unchanged store / an absent row). A pin observing only the exception or the response body
    certifies the refusal PROSE, not the refusal (finding #295; WB48 passed 448/448 with a
    byte-identical refusal while the body EXECUTED).
  - **admin fixture (`lore:write`):** the SAME tool is VISIBLE and its body DID run (the write
    landed). **This admin leg IS the positive control** the #295 law demands — it proves the
    harness can SEE a body execute, and it is now a required behavior (role-gated write) rather
    than a synthetic no-op tool. Both legs are the quantifier law: FORCE each fate with a fixture,
    never a ∀ helper evaluated only where the branch can't fire.
  The 2026-08-15 spike proved fastmcp middleware raising before `call_next` → body never runs on
  the wire — so the placement is correct, but the effect pin stays load-bearing because middleware
  REINTRODUCES placement as a free variable (a guard that calls `call_next` THEN checks would run
  the body — the WB48 class, now in the middleware world).
- **Served-surface honesty (Consumer Law):** ONE partition function feeds ALL THREE consumers —
  the `on_call_tool` refusal, the `on_list_tools` filter, and the `instructions` render's
  refused-set section. `served ∩ refused = ∅` on the wire for a given principal (every listed
  tool callable, every refused tool unlisted). Pin: flip ONE tool's annotation in scratch → it
  moves across the guard, the list, AND the render at once, or the pin reds (WB50/WB72 class).

**What this SUPERSEDES:** the prior R13 (scoped `ToolManager` subclass lookup) and R16
(`_setup_handlers` AST no-shadow pins + `test_wire_discipline.py`) are DROPPED — their referent
was the `mcp.server.fastmcp` construction-time-binding root cause (WB30→WB100), which the
standalone-fastmcp middleware seam dissolves (it gates on the wire by construction, spike-proven).
The wire-only AST discipline invariant is no longer needed; the effect pin + coverage-as-checked
carry the guarantee.

---

## 8. Composition (standalone fastmcp)

```
build_mcp_server:  FastMCP(auth=<RemoteAuthProvider(LoreTokenVerifier, authorization_servers=[…])
                            | None per posture>, middleware=[ToolTraceMiddleware(),
                            ReadOnlyGuardMiddleware()])
build_asgi_app:    OriginValidationMiddleware( mcp.http_app(path=…, transport="http",
                            stateless_http=…) )    # BearerAuthMiddleware hand-roll RETIRED
```
- **`auth=` per posture:** `None` in `LOOPBACK`; the api-key-only `LoreTokenVerifier` (no
  `.well-known`) in `LAN_BEARER`; the full `RemoteAuthProvider(LoreTokenVerifier, …)` in
  `HOSTED_OAUTH`. fastmcp gates only the streamable route, so `.well-known` is anonymous in
  `HOSTED_OAUTH` (RFC 9728) and absent in `LAN_BEARER`.
- **The hand-rolled `BearerAuthMiddleware` (auth.py:208) is RETIRED** — auth moves into
  `FastMCP(auth=…)`. `OriginValidationMiddleware` is KEPT (outermost — rejects a disallowed
  Origin BEFORE any credential parse / outbound provider call; prior R6/R9 zero-outbound
  property). `host_origin_protection` (fastmcp's native Host/DNS-rebinding guard, enabled by
  packet 59, server.py:12365) covers the Host axis the prior design's `TransportSecuritySettings`
  was reaching for.
- **`ApiKeyVerifier` semantics are KEPT** (constant-time, all-keys-no-early-out, empty-key/empty-
  token rejection, SecretStr holding) — but now consulted INSIDE `LoreTokenVerifier`'s api-key
  branch via `PrincipalKeyStore.verify`, not as an ASGI wrapper. The `AuthVerifier` ABC +
  `BearerAuthMiddleware` are DELETED (§9).

---

## 9. Superseded / removed-behavior inventory — adjudicated item-by-item

**Prior rulings R1–R16** (`docs/design/2026-07-31-packet39-google-oauth.md`):

| R# | prior ruling | verdict in the re-cut |
|---|---|---|
| R1 | packet-35 dependency waived | **SURVIVES** (packet 35 still not a technical coupling; the exhaustive-classification pin still makes it safe). |
| R2 | reuse the Price Paper GCP client (Google) | **SURVIVES** for the single-Google MVP; the shared-blast-radius cost (deleting the client kills odoo-code too) stands. Provider #2 needs a NEW MS/Entra app (operator console) — no longer "reuse". |
| R3 | hostname `lore.firehawktransam.org` | **SURVIVES** (edge/DNS unchanged). |
| R4 | hades SNI-passthrough → lore-caddy → loopback lore | **SURVIVES** (transport-only; scout 39b confirms lore-caddy is unbuilt and stays transport). |
| R5 | `client_id` inline non-secret | **PARTIALLY SUPERSEDED**: `client_id` public/inline-friendly stays true, but it now sources from the env block with the secret; and **`client_secret` is confidential** (env-ref only) — the prior "lore holds no confidential OAuth artifact" premise no longer holds under `GoogleTokenVerifier`. |
| R6 | Origin policy under M-1 | **SURVIVES** (both-outcomes-safe; `OriginValidationMiddleware` stays outermost). |
| R7 | domain-shaped allowlist entry unconstructible | **SUPERSEDED IN MECHANISM**: there is no flat-file roster to parse; admission is `lore-adm add --email` into the `principal` table. The "no domain rule" INTENT survives as: `lore-adm` admits individual emails only (no domain admission verb). A domain rule is a new operator decision. |
| R8 | read-only derived from `ToolAnnotations.readOnlyHint` | **SURVIVES + already built** (server.py:10444 partition). |
| R9 | Host/Origin one derivation, two enforcement points | **SUPERSEDED IN MECHANISM**: fastmcp's native `host_origin_protection` (Host) + kept `OriginValidationMiddleware` (Origin) replace the SDK `TransportSecuritySettings` derivation. The property (wrong Host refused, disallowed Origin 403 zero-outbound) survives; the SDK plumbing is gone. |
| R10 | identity minting (Google + api-key branches) | **RE-CUT**: per-principal mint (#206) on the 48/49 substrate; `sub` from `claims["sub"]`; api-key via `PrincipalKeyStore.verify`. |
| R11 | allowlist fail-closed at every leg | **SUPERSEDED SUBSTRATE**: the `principal` table + `status`/`expires_at` is the admission authority; fail-closed = deny when no active principal. Boot/runtime legs re-expressed against the store (a store that is unreachable at a hosted request → deny + loud). |
| R12 | mtime-watched flat-file roster | **SUPERSEDED** by the 48/49 `principal` DB (standing Log override). Revocation = `lore-adm suspend/delete`, effective next request, no redeploy — natively (§4.4). The flat-file, its parser, mtime-stat, and the whole R12 apparatus are DROPPED. |
| R13 | scoped `ToolManager` lookup enforcement | **SUPERSEDED** by the fastmcp `on_call_tool`/`on_list_tools` middleware (§7). Referent (mcp.server.fastmcp internals) gone. |
| R14 | extension tools refused wholesale (readOnlyHint=False) | **SURVIVES + already built** (server.py:12202). |
| R15 | `host_is_loopback` fail-closed predicate | **SURVIVES** (the posture predicate is unchanged; §6). |
| R16 | `_setup_handlers` no-shadow AST pins + wire-discipline invariant | **SUPERSEDED / DROPPED**: the wire-dead-shadowing class it guarded is dissolved by the middleware seam (gates on the wire by construction). Replaced by the coverage-as-checked-variable pin + the #295 effect pin (§7). |

**The prior design's BLANKET read-only hosted posture is SUPERSEDED by role-gated write
(operator F4).** The 2026-07-31 design (its §1 "every mutating tool refuses hosted principals by
construction", §7) held that NO hosted principal could ever write. F4 reverses this: read-only is
the FLOOR; `admin` principals (`lore:write`) write. What SURVIVES is the DERIVATION (readOnlyHint
partition, R8) and the effect-observation discipline (#295); what CHANGES is the population with
write (empty → the admin set) and the enforcement predicate (`readOnlyHint is not True` →
`readOnlyHint is not True AND principal lacks lore:write`). The api-key branch's prior
unconditional-write grant is ALSO superseded — it is now role-derived (§3.3/§3.5), a
least-privilege tightening (a member api-key can no longer write in an auth-on posture).

**Prior §4/§6 (the SDK wiring)** — SUPERSEDED wholesale by §2/§8 (standalone fastmcp). Specific
deletes, adjudicated:

| old symbol / behavior | verdict |
|---|---|
| `BearerAuthMiddleware` (auth.py:208, hand-rolled ASGI gate) | **dropped-and-replaced** by `FastMCP(auth=LoreTokenVerifier)`. Its 401 + `WWW-Authenticate` behavior is now fastmcp's `BearerAuthBackend` (RFC 9728 `resource_metadata=`); pin the 401 + header through the assembled app. |
| `AuthVerifier` ABC (auth.py:89) | **dropped** — replaced by fastmcp's `TokenVerifier` protocol. Its docstring claim that an OAuth backend "slots into the same BearerAuthMiddleware" was always FALSE (prior F1); old-bug-not-re-pinned. |
| `ApiKeyVerifier` (auth.py:104) | **kept-with-pin**, re-homed: consulted inside `LoreTokenVerifier`'s api-key branch via `PrincipalKeyStore.verify` (not as an ASGI wrapper). Constant-time / empty-key / SecretStr semantics preserved; existing `test_auth` pins for those stay green. |
| `OriginValidationMiddleware` (auth.py:272) | **kept** (outermost; unchanged). |
| prior tokeninfo-POST hand-roll `_validate_google_token` | **replaced** by `GoogleTokenVerifier` (§4.1) unless the build leg's READ refutes fit. |
| SDK `AuthSettings`/`issuer_url`/`resource_server_url`/`TransportSecuritySettings` wiring | **dropped** — not the imported stack (§2). |
| prior "issuer URL hardcoded, never config" | **dropped** — operator dismissed the downgrade rationale; issuer is config, resolved at the composition root. |

"The old code did it" is a reason NOWHERE above; each kept row cites the law/property that wants
it kept. The build's removed-behavior sweep re-runs an anchor-free grep for the deleted names
(`BearerAuthMiddleware`, `AuthVerifier`, prose included) and adjudicates every residual hit
individually (no "all remaining hits are X").

---

## 10. Kill switches / operator-side / edge (carried, re-anchored)

**Per-principal revocation (common case, fastest):** `lore-adm suspend --email` /
`lore-adm delete --email` → effective on the principal's NEXT request, no recreate/rebuild/restart
(§4.4). This REPLACES R12's "delete the roster line".

**Whole-service (ordered by speed):** `systemctl --user stop lore-caddy` (public reachability
dies, loopback continues) → `podman stop lore-lore` → remove the hades SNI route (root on hades)
→ operator removes the lore connector in claude.ai. **Shared-blast-radius:** rotating/deleting the
Google client kills BOTH lore and odoo-code (R2) — never a lore-scoped switch.

**Operator-side (cannot happen without them):**
- Create the lore connector in claude.ai (URL `https://lore.firehawktransam.org/mcp`, client_id,
  **client_secret** — in GCP console / their records, not on disk we can read). BLOCKING for
  go-live.
- hades: the SNI route + optional LAN DNS (only if root escalation from ejprice-wheel fails —
  §prior-13 bound; otherwise the build does it).
- The `.mcp.json`/local-key cutover wave (flips every local session to a per-principal API key) —
  ships atomically with the posture flip.
- GCP console: NOTHING now (R2 reuse); provider #2 later needs a NEW MS/Entra app + a Google
  firehawk client (R2 migration trigger).
- Cert expiry 2026-11-25 (prior §2) — calendar it; renewal reaches both edges.

---

## 11. Fork rulings (F1/F3/F4 RESOLVED by operator `#5100`) + residual items

- **F1 — email-keyed admission / `email_verified` load-bearing — ✅ RULED (operator `#5100`):**
  email-keyed admission CONFIRMED for the single-Google MVP; `email_verified == true` is an
  EXPLICIT admission precondition (folded into §3.2 + §1 mechanical verdicts + a §13 pin).
- **F2 — `client_secret` presence — VISIBILITY (as dispositioned):** whether lore needs the
  Google `client_secret` depends on whether `GoogleTokenVerifier` runs a confidential-client or
  PKCE-public flow (scout 39a §EXTEND-4, `google.py:261-263`); the build leg READS `google.py`
  to settle it. If needed, it is a NEW confidential artifact lore holds (env-ref only). Operator
  visibility, not a blocking ruling.
- **F3 — reuse `GoogleTokenVerifier` — ✅ LEAD-RATIFIED (`#5100`):** reuse-first; the build
  confirms fit against installed source and falls back to the hand-rolled tokeninfo POST only
  with a cited READ.
- **F4 — role-gated write — ✅ RULED (operator `#5100`): ROLE-GATED WRITE.** Read-only is the
  FLOOR; `principal.role == admin` (→ `lore:write`) grants write; `member` stays read-only. This
  REVERSES this doc's original "no hosted write" recommendation. Folded into §0/§1/§3.3/§3.5/§7/
  §9/§13. (My original recommendation was wrong for the operator's intent — the write endpoint is
  wanted, gated to admins.)
- **F5 — do-now-vs-defer multi-auth (§5) — DEFERRED (as dispositioned):** easy-as-mechanism,
  not-free-as-feature (child table + MS console + merge policy). Pre-ruled conditional.
- **F6 — the `oauth_identity` child table at provider #2: retire vs keep `principal.subject` —
  DEFERRED (as dispositioned):** to that packet; named so it is met deliberately (§3.6).
- **F7 — NEW, surfaced by the F4 ruling (scope-law flag, resolved-with-recommendation):**
  role-gating scope makes api-key principals role-gated too — a **member api-key principal is now
  READ-ONLY in an auth-on posture** (LAN_BEARER / HOSTED_OAUTH), where before this doc gave
  api-keys unconditional write. Two readings:
  - **(A, my resolution)** role governs scope for ALL principals (the explicit §3.5 directive:
    `member→{read}, admin→{read,write}`, no provider exception) — cleanest, least-privilege, one
    rule. A member's key gives a member's privileges.
  - **(B)** api-keys stay the unconditional local/LAN write anchor (the prior model), role-gating
    only the hosted branch.
  I implemented **(A)** because the F4 directive stated `role→scopes` provider-agnostically. **The
  consequence the operator should confirm:** **LOOPBACK (local, auth DISABLED) is UNAFFECTED — no
  auth, full surface — so the local dogfooding fleet keeps writing.** The change bites only where
  auth is ON: a LAN client / local agent using a MEMBER principal's api-key loses write there and
  must be provisioned `--role admin` to write. **Operator: confirm (A) — role governs api-key
  scope too — OR elect (B), api-keys stay unconditionally full-surface.** (I recommend A; it is
  what the F4 directive literally says and it is least-privilege, and the fleet is unaffected on
  loopback.)

---

## 12. Packages / DRY / bounds

**Packages considered** (all verdicts from installed source the scouts READ, cited):
- `fastmcp==3.4.7` — **USE-FRAMEWORK** for authN (`TokenVerifier`/`GoogleTokenVerifier`/
  `RemoteAuthProvider`/`AzureJWTVerifier`), token→identity (`AccessToken.claims`,
  `get_access_token`), per-principal visibility (`on_list_tools`/`on_call_tool` middleware +
  `readOnlyHint`), and single-IdP verification. **HAND-ROLL-THE-GAP** only: (a) the
  `(iss,sub)`→principal resolver (lore policy — minimal, deferred to §3.6), (b) the
  env→provider-kwargs composition-root adapter (fastmcp has no env-factory — a thin bridge).
  Neither is a re-implementation.
- `cachetools>=5` (7.1.6 installed) — **replace** hand-rolled dict-with-timestamps for the token
  verdict cache.
- `httpx` (already a dep) — **keep** (verifier transport; `MockTransport` in tests).
- `lorerunes` (in-repo shared home) — **extend** (email normaliser + posture enum + scope
  constants; stdlib-only preserved).
- DB-stored OAuth config — **bespoke, NOT built** (ruling C'; env-file kwargs is simpler and
  framework-native).
- Broker providers (`Keycloak`/`WorkOS`/`Auth0`) — **keep_with_trigger** (operator elects a
  broker, or >2 IdPs).

**DRY / one-implementation:** ONE partition function (readOnlyHint → visible/refused) feeds the
guard, the listing filter, and the instructions render (§7). ONE normaliser in `lorerunes`. ONE
trace WRITE policy (`_record_tool_trace`, reused). ONE composition root reads env. Prove sharing
by mutation in every case.

**Bounds this doc could not close (named, per the trust law):**
- Exactly what `GoogleTokenVerifier` does (endpoint, `aud` check, scope requirement) — the build
  leg READS `google.py:57-192` and settles it (F2/F3). This doc asserts it EXISTS and is the
  framework-packaged tokeninfo path (scout 39a §C3), not its exact HTTP behavior.
- Whether claude.ai's connector UI lets a human CHOOSE between two advertised authorization
  servers (a claude.ai question, not a lore code question — scout 39b §Q1). Moot for the
  single-provider MVP.
- M-1 (does claude.ai send `Origin`) — designed both-ways-safe (R6); measured at first connector use.
- The prior design's un-closed operator-side bounds (hades Caddyfile content, root escalation) —
  unchanged.

---

## 13. What the contract must pin (for the fresh contract + adversary pass)

> **⚠ SUPERSEDED where it pins WRITE (see banner): hosted is READ-ONLY in this packet.** Do NOT
> write the member-vs-admin hosted-WRITE pins below (group 4's role axis, and any allowed-admin
> write fixture) — those move to the RBAC packet. KEEP: every hosted principal (member AND admin)
> is refused every mutating tool (no role axis), the #295 EFFECT discipline on those refusals,
> read-corpus access, admission, Google verification, composition/posture, and config. ADD:
> the identity output carries `principal.role` + an optional `(principal, agent)` seam;
> `role → capability` is a function (mutation: a wrong `admin=+write` in THIS packet is a defect).

Two ∀-properties govern everything (quantifier law — pin outcomes over ALL inputs, FORCE each
fate with a fixture). **⚠ The ROLE-AXIS write content below is SUPERSEDED (RBAC's) — read the
marker above:**
- **Auth ∀:** every `(token, provider-response, principal-table-state)` triple yields EITHER
  `None` OR an `AccessToken` whose identity maps to an ACTIVE principal, whose `email_verified`
  was true, and whose `scopes` are DERIVED FROM `principal.role` (`member→{lore:read}`,
  `admin→{lore:read,lore:write}`) — no third fate, no scope not implied by the role, regardless of
  which field was hostile.
- **Posture ∀ (role axis):** every registered tool — over BOTH registration paths (core +
  extension) — is classified; in an auth-on posture every non-read-only tool is
  refused-AND-invisible for every principal WITHOUT `lore:write` (member) AND permitted-AND-visible
  for every principal WITH `lore:write` (admin); the guard's coverage set EQUALS the registry
  (reach checked). Both fates FORCED with a fixture — a ∀ helper evaluated only on the member side
  is the fixture-reason pass wearing a quantifier.

Groups (each pin mutation-proven; expected-RED ids from `--collect-only`):
1. **Admission** — active principal admitted · **`email_verified == true` admitted; false OR
   absent denied BEFORE principal lookup (F1)** · no-principal denied · suspended denied · expired
   denied · `get_by_subject` fast-path == `get_by_email` result · admission NEVER cached
   (suspend-mid-session denied on next request, cache-HIT fixture asserted by transport
   call-count; cache-the-admission mutation ⇒ RED) · normaliser shared (mutate → lorerunes + admission pins red).
2. **Google verification** — `aud` mismatch/absent/different-client → deny (BLOCKER pin, a
   different-client-token fixture proves `aud` is not decorative) · email scope missing → no
   email → deny · `sub` read from `claims["sub"]` (not `.subject`) · token never in a URL
   (transport spy asserts POST body) · 401-vs-5xx negative-cache SPLIT (different assertions via
   call-count) · malformed JSON → None no-cache · expired token not served from cache.
3. **Identity mint (#206)** — api-key resolves to the PRINCIPAL (two keys of one human = one
   principal, not two); mint routes through `PrincipalKeyStore.verify` (break `verify` → RED);
   distinct principals ⇒ distinct `authorization_context`; a session/request by X not usable by Y.
4. **Enforcement (#295), ROLE AXIS — the derived ∀ EFFECT pin over member AND admin:** for every
   non-read-only tool in the registry, a **MEMBER** principal → refused AND invisible AND body
   NEVER entered (invocation counter zero / unchanged store / absent row); an **ADMIN** principal
   → visible AND body RAN (the write landed) — the admin leg IS the positive control proving the
   harness sees a body execute (no synthetic no-op tool needed) · coverage == registry (reach
   checked; a new unguarded tool reds it) · `served ∩ refused = ∅` on the wire per-principal
   (member and admin each self-consistent) · one annotation flip moves the tool across
   guard+list+render at once · an extension tool (`readOnlyHint=False`) is refused for a member
   and callable by an admin · **F7 role-gating of api-keys: a MEMBER api-key principal is DENIED a
   mutating tool; an ADMIN api-key principal is PERMITTED it** (both fates forced) · a read-only
   tool is visible+callable for member AND admin (no over-refusal).
5. **Composition/posture** — `.well-known` 200 anonymous in `HOSTED_OAUTH`, absent in
   `LAN_BEARER` · 401 carries `resource_metadata=` · disallowed Origin 403 with ZERO outbound
   provider calls (Origin outermost) · wrong Host refused (native `host_origin_protection`) · the
   posture cross-product table + `host_is_loopback` 127/8 grid.
6. **Config** — `client_secret` never inline / never logged · blank `client_id` unconstructible ·
   `base_url` https-only · boot refusal on an incoherent posture (in-image conformance, non-zero
   exit — #131/#139).
7. **The child-table SEAM pin (§3.6)** — asserts the single-`subject` model AND carries the
   named-re-open-trigger message; goes RED the day someone adds the `oauth_identity` table.

The contract ships with a **satisfiability receipt** (0-failed against the adversary's reference
build, including after the ruff-driven orphaned-import cleanup that deleting `BearerAuthMiddleware`
forces). A fresh **contract-adversary pass is mandatory** (standing law). **Escalation:** a
contract failing its adversary THREE times → operator, UNLESS the adversary's findings are minor
easy-fix nits (operator, this session).

**Live proof ladder (build/deploy leg):** `.well-known` → 200 anonymous · `POST /mcp` → 401 +
`WWW-Authenticate` whose `resource_metadata=` resolves · junk path → 404 at lore-caddy · connector
flow end-to-end (operator) · negatives: no-principal denied, different-client token denied, a write
tool refused-hosted PAIRED with the same tool succeeding via api-key (the probe can see writes).
In-image conformance asserts `loremaster.__file__` in site-packages + non-zero exit on an incoherent
posture (the artifact proves the cake, not the recipe — #107/#131/#139).

---

*Every recommendation above is a recommendation; the operator rules the §11 forks. Where this
doc and the 2026-07-31 design disagree, this doc governs (§9) — the disagreements are driven by
the 48/49 substrate, the packet-59 standalone-fastmcp migration, and the operator's dismissal of
the downgrade-attack rationale, all of which post-date the prior doc.*
