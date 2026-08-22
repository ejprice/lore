# REPORT — scout-fastmcp-oauth-39

brief-base v14 read
brief project v7 read
intended model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done**
- deviations: none (read-only scout; only writable file is this report)
- **Packages considered:** `fastmcp==3.4.7` — the framework under evaluation; verdict per-capability below (§4). Net: **USE-FRAMEWORK for authN, token→identity, per-component authZ/visibility, and single-IdP interactive login; HAND-ROLL-THE-GAP only for (a) multi-IdP *interactive* login routing and (b) the composition-root that maps env→provider-kwargs and (iss,sub)→principal.** All verdicts backed by installed source I opened (cited), not docs.
- **Reuse ledger:** n=0 new reusable symbols introduced (research report; specifies mechanism, builds none). The design recommendations name framework symbols to REUSE (`MultiAuth`, `RemoteAuthProvider`, `require_scopes`/`restrict_tag`, per-component `auth=`, `get_access_token`) and lore's own `_resolve_env_file`.
- **Graded:** target is the installed package `fastmcp==3.4.7` at `/home/ejprice/PycharmProjects/lore/.venv/lib/python3.14/site-packages/fastmcp` (a version, not a repo sha — the claims are about the dependency, not repo code). Repo HEAD-at-report: `9a10604` (feat/surreal-unification). No repo artifact was graded.
- **Provenance receipt (which tree I read):** the authoritative install is the project venv, `fastmcp==3.4.7` (METADATA `Version: 3.4.7`). Seven `/tmp/*-scratch` venvs also carry 3.4.7 identically. All line cites below are against the project-venv copy.
- decisions-needed (for operator / packet-39 re-cut):
  1. **Read-only posture seam:** per-component `auth=` AuthCheck vs a single `on_list_tools`/`on_call_tool` middleware. I recommend the middleware (DRY, keys off the `ToolAnnotations.readOnlyHint` lore ALREADY sets). Operator/lead to ratify.
  2. **Multi-IdP interactive login:** federate through ONE broker OAuthProxy (WorkOS/Auth0/Keycloak — all ship as providers) vs hand-roll a front-router composite AuthProvider. I recommend the broker. Operator to weigh cost of standing up a broker vs a bespoke router.
  3. **Principal key:** key on `(issuer, sub)` (Azure: `(tid, oid)`), resolve `email` as an *attribute*, not the join key — because verified email is NOT uniform across Google+Azure (evidence §EXTEND-2). Operator to confirm the identity model.
- receipt pointers: claims → §VERIFY; design answers → §EXTEND-1..4; framework-vs-handroll → §4; comms seqs → §COMMS TEST.

---

## COMMS TEST
- **outbound** (signal → lead-39-recut, thread `comms-test`): seq **#5087** ("sent #5087 [signal] → lead-39-recut").
- **peer** (directive → design-sidecar-39-2, thread `comms-test-peer`): seq **#5088** ("sent #5088 [directive] → design-sidecar-39-2 · recipients must ack"). Peer's ack of #5088 is owed BY design-sidecar-39-2 to me; agent↔agent durable *send* succeeded (the ledger minted the seq + registered the ack debt). Whether the peer drains+acks is async and outside this run.
- **inbound / ack owed by me:** at my drain (turn boundary, after sends) → **"no unread messages"**. lead-39-recut sent me no directive; I owe no ack. (Register auto-acked project brief v7.)
- register receipt: "registered scout-fastmcp-oauth-39 (session pkt39-recut, role scout) — status active; brief 'project' v7 ack recorded (via register)".

---

## VERIFY — verdict per inherited claim
Method: re-derived each claim against installed source (not the recon, not gofastmcp.com). Files opened: `server/auth/auth.py`, `.../providers/google.py`, `.../providers/azure.py`, `.../providers/jwt.py`, `.../oauth_proxy/proxy.py`, `.../providers/oci.py`, `.../__init__.py`, `.../utilities/authorization.py`, `server/server.py`, `server/dependencies.py`, `server/middleware/middleware.py`, `server/http.py`, and the SDK `mcp/server/auth/provider.py`.

### C1 — Concrete providers ship; GoogleProvider/AzureProvider are OAuthProxy subclasses; pure verifiers exist
**CONFIRMED.**
- `class GoogleProvider(OAuthProxy)` — `providers/google.py:204`. ✓
- `class AzureProvider(OAuthProxy)` — `providers/azure.py:39` (docstring: "Azure (Microsoft Entra) OAuth provider … OAuth Proxy pattern"). ✓
- Pure verifiers: `class RemoteAuthProvider(AuthProvider)` — `auth.py:413`; `class TokenVerifier(AuthProvider)` — `auth.py:366`; `class JWTVerifier(TokenVerifier)` — `providers/jwt.py:195`; `class AzureJWTVerifier(JWTVerifier)` — `providers/azure.py:696`; `class GoogleTokenVerifier(TokenVerifier)` — `providers/google.py:57`. ✓
- The shipped provider roster (`server/auth/providers/`): `auth0, aws, azure, clerk, debug, descope, discord, github, google, huggingface, in_memory, jwt, keycloak, oci, propelauth, scalekit, supabase, workos` (+ `introspection`). Several are enterprise IdP **brokers** — material for EXTEND-1.

### C2 — MultiAuth tries server then verifiers in order; get_routes/well-known delegate ONLY to `server`
**CONFIRMED.**
- `class MultiAuth(AuthProvider)` — `auth.py:510`. ✓
- `verify_token` — `auth.py:591`: builds `self._sources = [server] + verifiers` (`auth.py:586-589`) and loops, returning the first non-None (`auth.py:598-610`). Each source's exception is swallowed to a non-match. ✓
- `get_routes` (`auth.py:620-624`) returns `self.server.get_routes(...)` or `[]` if no server. `get_well_known_routes` (`auth.py:626-634`) delegates to `self.server` likewise. ✓ **So exactly ONE interactive-login route-set (the `server`'s); `verifiers` contribute token verification only.** This is the load-bearing constraint for Ruling B.

### C3 — AccessToken adds `claims: dict`; email provider-populated; sub present; get_access_token at dependencies.py:467
**CONFIRMED, with two precisions the recon under-stated:**
- `class AccessToken(_SDKAccessToken)` — `auth.py:54`; adds `claims: dict[str, Any] = Field(default_factory=dict)` — `auth.py:57`. ✓
- **PRECISION A — the SDK base already has BOTH `subject` and `claims`.** `mcp/server/auth/provider.py:39` `class AccessToken(BaseModel)` has fields `token, client_id, scopes, expires_at, resource, subject: str | None ("RFC 7662/9068 sub: resource owner; unique only per issuer"), claims`. So `sub` has a first-class home (`.subject`) — **BUT** FastMCP's shipped verifiers do NOT populate it: `GoogleTokenVerifier` (`google.py:174-192`) and `JWTVerifier` (`jwt.py:586-592`) both construct `AccessToken(... claims=...)` with **no `subject=`**. ⇒ **read `sub` from `.claims["sub"]`, never `.subject`** (which stays `None`). The SDK's own comment "unique only per issuer" corroborates EXTEND-2's (iss,sub) key.
- **PRECISION B — email is populated by GoogleTokenVerifier at `google.py:182`**, inside the `174-192` AccessToken block, as `token_data.get("email") or user_data.get("email")` — i.e. **only if the `email`/`userinfo.email` scope was granted.** `GoogleProvider` defaults `required_scopes=["openid"]` (`google.py:319`), which does **NOT** include email — so by default email is `None`. `email_verified` (`google.py:183-184`) may also be `None`. So "email is provider-populated" is true but **conditional on scope**, not automatic.
- `def get_access_token() -> AccessToken | None` — `dependencies.py:467`. ✓ (This is the in-tool accessor: `get_access_token().claims["email"]`.)

### C4 — FastMCP(auth=…) ctor at server.py:329; per-component AuthCheck at list-time AND dispatch-time; on_list_tools/on_call_tool hooks
**CONFIRMED** (list cites off by a few lines; mechanism exact):
- `FastMCP.__init__(..., auth: AuthProvider | None = None, ...)` — `server/server.py:329`; stored `self.auth = auth` — `server.py:424`. ✓
- Per-component authZ is a SEPARATE axis: the tool/resource/prompt decorators take `auth: AuthCheck | list[AuthCheck] | None` (`server.py:1711, 1733, 1877, 2005, 2021, 2036`, …). ✓
- **List-time filtering** — `_list_tools` override, `server.py:687-698`: for each tool with `tool.auth is not None`, `if not await run_auth_checks(tool.auth, ctx): continue` (`server.py:693-694`) — the denied tool is **dropped from the returned `authorized` list** (⇒ invisible in `tools/list`). (Recon said 687-697; actual 687-698.) ✓
- **Dispatch-time** — `_get_tool`, `server.py:719-727`: same check; returns `None` when unauthorized, comment "Component auth - return None if unauthorized (consistent with list filtering)" (`server.py:719,724`). (Recon said 719-724; actual 719-727.) Resources mirror this (`server.py:832, 863, 910`). ✓
- Middleware hooks — `on_call_tool` `middleware/middleware.py:168`, `on_list_tools` `middleware/middleware.py:189` (recon cited 168/189 — exact). `on_list_tools` returns `Sequence[Tool]` (can drop tools); `list_tools` runs middleware via `_run_middleware` (`server.py:667-670`). ✓

### C5 — Config is constructor-kwargs only; NO FASTMCP_SERVER_AUTH env factory; OCI env reads are demo glue
**CONFIRMED** (one wording correction):
- `grep -rn "FASTMCP_SERVER_AUTH"` over the whole `fastmcp` package → **zero hits.** ✓ No env auth-factory.
- `grep -rn "os.environ|os.getenv"` over `server/auth/providers/*.py` → the ONLY hits are in `oci.py` lines 28-31 and 110-112, and **both spans are inside DOCSTRINGS** (the module docstring `oci.py:1-78`; the `OCIProvider` class docstring `oci.py:96-120`) — not executable code, and not a `__main__` block. **CORRECTION:** the recon called these "`__main__` demo glue"; they are actually *docstring example prose*. The substantive claim (no data-driven env auth config; providers are constructed from kwargs) is CONFIRMED — the correction only sharpens *how inert* the OCI env reads are.
- Corroboration that config is kwargs: `GoogleProvider.__init__`/`AzureProvider.__init__` take `client_id`/`client_secret`/`tenant_id`/`base_url`/… as explicit kwargs (`google.py:232-315`, `azure.py:99-195`); nothing reads env.

---

## EXTEND — design answers (the value-add)

### EXTEND-1 (Ruling B): cleanest framework-aligned "log in with Google OR Microsoft" on ONE FastMCP server

**The hard constraint, from source (not opinion):**
1. The HTTP app builder wires **exactly ONE** auth provider: `create_streamable_http_app(..., auth: AuthProvider | None)` calls `auth.get_middleware()` (one `BearerAuthBackend`) and `auth.get_routes(mcp_path=...)` **once** (`http.py:590-595`; SSE path identical at `http.py:454-459`). There is no "list of auths".
2. `MultiAuth` multiplexes **verification** (N verifiers) but **not interactive login** — `get_routes`/`get_well_known_routes` delegate to the single `server` (C2). So `MultiAuth(server=GoogleProxy, verifiers=[AzureJWTVerifier])` gives you: Google interactive login **plus** *accept-already-minted* Azure tokens — **not** an Azure login button.
3. Each `OAuthProxy` **is itself the authorization server** the MCP client talks to (it owns `/authorize`, `/token`, `/register`, `/.well-known/oauth-authorization-server`; mints its own FastMCP JWT and swaps it for the upstream token — `proxy.py:1804-1959`, the "token swap"). Two OAuthProxies on one app would both claim those singular AS paths. MCP's OAuth discovery (RFC 9728 protected-resource metadata → the client picks an authorization server → DCR + authorize) expects the resource to point at an AS; "choose your IdP" is not an MCP-client-native gesture.

**Evaluation of the brief's options against source:**
- **(a) mount per-IdP sub-apps / separate routes.** FastMCP has `mount()`/`import_server()`/`as_proxy()` (`server.py:2124/2230/2436), but `mount` composes tools/resources into ONE parent whose auth is still the parent app's single provider — it does not give a mounted child its own login route-set at the HTTP layer. True per-IdP isolation means two separate `create_streamable_http_app(auth=…)` ASGI apps behind a Starlette router at two path prefixes ⇒ **two MCP endpoints**, not "one server, choose IdP". Rejected for the stated goal.
- **(b) custom AuthProvider fronting N OAuthProxies.** Possible (subclass `AuthProvider`; `verify_token` tries both; `get_routes` returns the UNION of both proxies' routes under distinct `redirect_path`/issuer sub-paths; present a chooser). But you fight the singular-AS-endpoint model, must de-collide `/authorize`+`/token`+DCR, and hand-roll the chooser + per-proxy state. **This is HAND-ROLLING a router the framework deliberately doesn't provide.** Only justified if a broker is truly unavailable.
- **(c) accept tokens from N verifiers, delegate interactive login elsewhere.** This is exactly `MultiAuth`. Great for **M2M-from-many-issuers + ONE interactive login**. Not a two-login solution.

**RECOMMENDATION (framework-aligned, lowest bespoke surface):**
> **Federate, don't multiplex.** Put ONE `OAuthProxy` in front of an **identity broker that itself offers Google AND Microsoft** — FastMCP ships providers for exactly this: `WorkOSProvider`, `Auth0Provider`, `KeycloakProvider` (also `descope`, `clerk`, `scalekit`, `propelauth`). The broker owns the "Google or Microsoft" chooser; FastMCP sees one AS, one login route, one uniform token → and (bonus) the broker normalizes `email`/`email_verified`, which fixes EXTEND-2's non-uniformity for free.

Only if a broker is off the table: pattern (b), and flag it to the operator as a bespoke auth surface needing its own security review. Pattern (c)/`MultiAuth` is the right call if the real need is "one interactive login + accept M2M JWTs from other issuers." **A native two-*interactive*-login pattern does not exist; a front component is unavoidable — the recommendation is to make that component a broker you configure, not a router you write.**

### EXTEND-2 (Ruling C): can we rely on verified `email` from BOTH providers? What's the safe key?

**No — verified email is NOT uniform across Google and Azure. Source:**
- **Google:** `email` set at `google.py:182` from `token_data.get("email") or user_data.get("email")`; `email_verified` at `google.py:183-184`. Present **only if the email scope is granted** (default scopes = `["openid"]`, `google.py:319`). When granted, Google's `email`/`verified_email` are reliable and genuinely verified.
- **Azure:** the runtime verifier is a plain `JWTVerifier` (`azure.py:243`) that copies the **entire decoded access-token payload** into `claims` (`jwt.py:591`). Azure **v2 access tokens do not guarantee `email`**; the identity claims that *do* appear are `oid` (stable per-user object id), `tid` (tenant), and — when profile scopes are present — `preferred_username`/`upn` (the UPN, *email-shaped* but a directory principal name, **not** a proven mailbox and with **no verified-email semantics**). `AzureProvider._extract_upstream_claims` (`azure.py:556-627`) additionally captures `{sub, oid, tid, azp, name, given_name, family_name, preferred_username, upn, email, roles, groups}` **only for the keys the token actually carries** (`azure.py:611-613`) and stores them under `claims["upstream_claims"]` on the swapped token (`proxy.py:1950-1954`). So Azure `email` is best-effort/optional; `preferred_username`/`upn` are present-but-not-verified-email.

**SAFE identity-resolution shape (recommendation):**
1. **Join key = `(issuer, subject)`.** `issuer` = `claims["iss"]`; `subject` = `claims["sub"]` (the SDK confirms sub is "unique only per issuer" — so sub ALONE is unsafe across two IdPs). For Azure prefer the **`(tid, oid)`** pair as the stable within-Entra identity (oid is immutable; sub is per-app-per-user). Store the raw `(iss, sub)`/`(tid, oid)` as the durable principal key.
2. **`email` is a resolved ATTRIBUTE of the principal, never the join key.** Populate it from, in order: Google `claims["email"]` (with `email_verified` true), Azure `claims["upstream_claims"]["email"]` else `preferred_username`/`upn` — but **mark Azure email as unverified** unless you independently confirm it. Keying principals by email would (a) silently merge two humans who share a reused UPN/mailbox across tenants and (b) break when an email changes. Key by `(iss,sub)`; index email for lookup/display.
3. **This is where the broker (EXTEND-1) pays off twice:** a single broker issuer means one `iss`, one uniform verified-email claim, and one `sub` namespace — collapsing the whole "N identities → one principal(email)" problem into "one verified claim set." If you keep two direct IdPs, the `(iss,sub)→principal` table with email-as-attribute is the safe design; make the operator own the "same human across Google + Microsoft" merge policy (email-match is a heuristic, not proof).

### EXTEND-3 (#295): does per-component AuthCheck / on_list_tools REMOVE a denied tool (gate visibility)? Correct seam? Interaction with lore's registration?

**YES — visibility is gated, not just invocation. Source (the crux):**
- `list_tools` builds `authorized: list[Tool]`; a tool whose `run_auth_checks(tool.auth, ctx)` returns False is `continue`'d — i.e. **excluded from the list returned to the client** (`server.py:687-698`). A tool with `tool.auth is None` is always included, so enforcement is **opt-in per tool**.
- `_get_tool` (dispatch) runs the **same** check and returns `None` on denial (`server.py:719-727`), "consistent with list filtering" — so a denied tool is both **invisible in `tools/list`** and **uncallable by name**, gated by one predicate (no invisible-but-callable divergence).
- `AuthCheck` is just `Callable[[AuthContext], bool | Awaitable[bool]]` (`utilities/authorization.py:47`). `AuthContext` carries `.token` (the `AccessToken`, hence `.claims`/`.scopes`) and `.component` (the tool, hence `.tags`, `.annotations`) (`utilities/authorization.py:26-44`). Ready-made helpers ship: `require_scopes(*scopes)` (`:50`) and `restrict_tag(tag, *, scopes)` (`:62` — allows untagged tools, requires scopes for tagged ones). `run_auth_checks` is AND-logic and treats a raised non-`AuthorizationError` as denial (`:76-101`).

**This IS the correct seam for a read-only hosted posture (#295):** attach an AuthCheck that denies **mutating** tools to a read-only principal → they vanish from the listing AND become uncallable.

**Interaction with lore's registration (read from source):**
- lore registers 15 built-ins in `_register_tools(mcp, server)` — `loremaster/loremaster/server.py:10478-11450` — via a `_gated_tool(name, description, annotations)` wrapper that calls `mcp.tool(name=…, description=…, annotations=…)`. **Two facts make #295 cheap here:**
  1. lore **already tags every tool read-only vs mutating** via `ToolAnnotations` (`_READ_ONLY_ANNOTATIONS`, `_SAVE_MEMORY_ANNOTATIONS`, `_TASK_TOOL_ANNOTATIONS`, `_COMMS_TOOL_ANNOTATIONS`). So "which tools mutate" is already declared data — no re-enumeration.
  2. lore has an existing **deploy-wide** gate: `_gated_tool` skips registration entirely for tools absent from `config.tools.enabled` (a disabled tool is never registered ⇒ absent from `list_tools` and uncallable — finding #296). **But that gate is per-DEPLOY, identical for all callers — NOT per-principal.** #295 needs per-*principal* visibility, which is a different axis: the fastmcp `auth=`/AuthCheck seam.
- **Recommended integration (DRY — brief-base §6 ONE IMPLEMENTATION):** do **not** sprinkle `auth=` on N tools. Instead install ONE `Middleware` (or one shared AuthCheck factory) whose `on_list_tools` **filters out** and `on_call_tool` **denies** any tool whose `annotations.readOnlyHint` is not true when the principal lacks a write role/scope. Keying on the `ToolAnnotations` lore already sets means the policy is derived from existing declared data, changes in one place, and cannot drift per-tool. (If you prefer the per-component path, pass a single shared `read_only_guard` AuthCheck through `_gated_tool` for mutating tools — still one predicate, attached in one loop.) Prove it by mutation: flip one tool's annotation and the guard's coverage must change with it.
- ⚠ **Caveat to pin:** a tool with no guard is visible to everyone (the `tool.auth is None` fast-path). So the read-only posture must be enforced by a **default-deny middleware over the whole surface**, not by remembering to tag each new tool — otherwise a future tool ships mutating-and-unguarded. Make coverage a checked variable (assert every registered tool is seen by the guard), per lore's own "reach is a checked variable" law.

### EXTEND-4 (Ruling C'): confirm no native data-driven config; specify the framework-native config path; secrets; what "store OAuth configs in DB" adds

**Confirmed:** no native env/data-driven auth factory (C5). Providers are constructed from **explicit kwargs** at a composition root.

**Exact kwargs each provider requires (from `__init__` signatures):**
- `GoogleProvider` (`google.py:232-256`): **required** `client_id`, `base_url`; **needed in practice** `client_secret` (optional only for PKCE public clients — "When omitted, jwt_signing_key must be provided", `google.py:261-263`); **recommended** `required_scopes` incl. an email scope (default `["openid"]` gives NO email — EXTEND-2), `redirect_path` (default `/auth/callback`), `client_storage`, `jwt_signing_key`.
- `AzureProvider` (`azure.py:99-125`): **required** `client_id`, `tenant_id`, `required_scopes` (≥1 **non-OIDC** scope or it raises — `azure.py:234-241`), `base_url`; **needed** `client_secret` (same PKCE caveat); optional `identifier_uri` (default `api://{client_id}`), `base_authority` (Gov clouds), `additional_authorize_scopes` (Graph), `jwt_signing_key`.
- Pure-verifier alternative (if login is brokered/elsewhere): `AzureJWTVerifier(client_id, tenant_id, required_scopes, …)` (`azure.py:729`) + `RemoteAuthProvider(token_verifier, authorization_servers, base_url)` (`auth.py:428`); or `JWTVerifier(jwks_uri, issuer, audience, …)` (`jwt.py:195`) for a generic broker.

**Where secrets come from (framework-native, matches lore's existing idiom — cited):**
- lore-deploy already resolves per-slug secrets: `_resolve_env_file(project, explicit)` → `~/docker/mcp/lore-secrets/<slug>.env` (`skills/lore-deploy/scripts/lore_deploy.py:388-404`, `LORE_SECRETS_DIR` at `:90`), honoring `--env-file` verbatim; `_launch_container` passes it to podman as **`--env-file <env_file>`** (`lore_deploy.py:674`) → its `KEY=value` lines become the **container process env**.
- **Native path:** put `LORE_OAUTH_GOOGLE_CLIENT_ID` / `..._CLIENT_SECRET` / `LORE_OAUTH_AZURE_TENANT_ID` / … in that per-slug `.env`; the lore **composition root** (server startup — the ONE place allowed to read the environment, per lorerunes/brief-base §"secret RESOLUTION stays at composition root") reads `os.environ`, constructs `GoogleProvider(...)`/`AzureProvider(...)`/`MultiAuth(...)`, and hands the instance to `FastMCP(auth=…)` (`server.py:329`). This is packages-over-hand-rolling: FastMCP has no env-factory, so lore's composition root IS the missing adapter — a thin ~env→kwargs bridge, not a re-implementation.
- ⚠ `base_url`/`resource_base_url` are per-deployment (public URL) and belong in config, not secrets — sensibly they can live in `lore.yaml`, secrets in the `.env`.

**What "extend lore-adm to store OAuth configs in DB" would ADDITIONALLY require (so the operator can weigh it):**
- A store schema for OAuth config (per-slug: provider kind, client_id, scopes, base_url, redirect_path) — **and a secret-at-rest story for `client_secret`** (encryption/KMS, or keep the secret in the `.env` and only non-secret config in the DB — the cleaner split).
- A composition-root read path that queries the store at boot **before** constructing providers (an ordering + availability dependency: the store must be reachable at MCP boot; today auth config would be plain env, always present).
- lore-adm CRUD verbs + validation (reject an Azure config with no non-OIDC scope, etc.) + migration/DDL (see `docs/reference/surrealdb-31-capabilities.md` — `OVERWRITE` for fields, `IF NOT EXISTS` for indexes; #107 lives here).
- **Verdict:** DB-stored config buys runtime/multi-slug management but adds a schema, a secret-at-rest problem, a boot-time store dependency, and admin surface. For a first cut, **env-file kwargs (the existing idiom) is strictly simpler and framework-native**; DB storage is a later enhancement, not a prerequisite. Recommend env-first; ledger DB-config as a follow-up if multi-tenant self-service auth is actually needed.

---

## 4. Packages / framework-over-hand-rolling — verdict PER capability
Each backed by installed source I opened; `bespoke` verdicts cite a read (not a doc), per brief-base §1.

| Capability | Verdict | Basis (READ) |
|---|---|---|
| **authN (bearer token verification)** | **USE-FRAMEWORK** | `AuthProvider`/`TokenVerifier`/`JWTVerifier`/`GoogleTokenVerifier` verify tokens + advertise RFC 8414/9728 metadata (`auth.py`, `jwt.py`, `google.py`). Hand-rolling JWKS/tokeninfo is the exact wheel these reinvent. |
| **interactive OAuth login — SINGLE IdP** | **USE-FRAMEWORK** | `OAuthProxy` token-swap + DCR + consent is fully implemented (`oauth_proxy/proxy.py`, `GoogleProvider`, `AzureProvider`). No reason to hand-roll. |
| **interactive login — MULTI IdP (Google OR Microsoft) on one endpoint** | **USE-FRAMEWORK via a broker; HAND-ROLL-THE-GAP only if no broker** | One-auth-per-app (`http.py:590-595`) + MultiAuth login delegates to one server (`auth.py:620-634`) ⇒ no native two-login pattern. Framework answer = broker provider (`workos`/`auth0`/`keycloak`). A front-router composite AuthProvider is a real bespoke gap; escalate before writing it. |
| **multi-issuer M2M token acceptance** | **USE-FRAMEWORK** | `MultiAuth(verifiers=[…])` tries each verifier in order (`auth.py:591-610`). Zero bespoke. |
| **token → identity (claims/email/sub)** | **USE-FRAMEWORK for extraction; HAND-ROLL the (iss,sub)→principal mapping** | Claims delivered via `AccessToken.claims` + `get_access_token()` (`auth.py:57`, `dependencies.py:467`). But cross-IdP principal identity (which is stable, which email is verified) is lore policy the framework can't decide — a thin bespoke resolver keyed on `(iss,sub)`/`(tid,oid)`, email-as-attribute. Minimal surface, verify by test. |
| **read-only / per-principal visibility gate (#295)** | **USE-FRAMEWORK** | Per-component `auth=` AuthCheck + `run_auth_checks` filter `list_tools` and `_get_tool` (`server.py:687-727`, `utilities/authorization.py`); `restrict_tag`/`require_scopes` ship. lore adds ONE middleware keyed on its existing `ToolAnnotations`. No bespoke enforcement engine. |
| **auth config / secrets** | **USE-FRAMEWORK (kwargs) + reuse lore's env-file idiom; composition-root adapter is the only bespoke bit** | No env-factory in fastmcp (C5, grep=0). Providers take kwargs; secrets already flow via `lore_deploy.py:_resolve_env_file`→`--env-file`. The ~env→kwargs composition-root bridge is a legitimate hand-roll (the package has no such seam), minimal and testable. DB-stored config is optional scope, not required. |

**Net:** the framework covers the large majority. The only genuine HAND-ROLL-THE-GAP items are (1) a multi-IdP interactive *router* — and even that is avoidable by choosing a broker provider — and (2) two thin composition-root pieces (env→kwargs, and (iss,sub)→principal). Neither is a re-implementation of anything fastmcp ships; both are adapters/policy the package deliberately leaves to the host. Escalate item (1)'s bespoke-vs-broker choice to the operator (decisions-needed #2).

---

## Appendix — exact line anchors (installed `fastmcp==3.4.7`, project venv)
- `server/auth/auth.py`: AccessToken:54 (claims:57) · TokenVerifier:366 · RemoteAuthProvider:413,428 · MultiAuth:510 (verify_token:591, sources:586-589, get_routes:620-624, get_well_known:626-634) · OAuthProvider:637
- `server/auth/providers/google.py`: GoogleTokenVerifier:57 (verify_token:92, AccessToken/email block:174-192, email:182) · GoogleProvider:204 (default scopes ["openid"]:319)
- `server/auth/providers/azure.py`: AzureProvider:39 (init:99, JWTVerifier wiring:243, non-OIDC-scope raise:234-241) · _extract_upstream_claims:556-627 (claim_keys:597-610) · AzureJWTVerifier:696
- `server/auth/providers/jwt.py`: JWTVerifier:195 · claims=full payload:591 · client_id fallback iss/azp/sub:493-498
- `server/auth/oauth_proxy/proxy.py`: JWTIssuer wiring:680 · load_access_token/token-swap:1804-1959 (upstream_claims merge:1950-1954)
- `server/auth/providers/oci.py`: env reads are docstring-only (module docstring 1-78; class docstring 96-120); real code has no env read
- `server/server.py`: FastMCP.__init__ auth:329 (self.auth:424) · list-time filter:687-698 (run_auth_checks:693) · dispatch _get_tool:719-727 · per-component auth kwargs:1711,1733,… · mount:2124 import_server:2230 as_proxy:2436
- `server/dependencies.py`: get_access_token:467
- `server/middleware/middleware.py`: on_call_tool:168 · on_list_tools:189
- `server/http.py`: create_streamable_http_app single-auth wiring:590-595 (SSE:454-459)
- `utilities/authorization.py`: AuthContext:26 · AuthCheck type:47 · require_scopes:50 · restrict_tag:62 · run_auth_checks:76
- SDK `mcp/server/auth/provider.py`: AccessToken(BaseModel):39 (subject field "unique only per issuer")
- lore: `_register_tools` `loremaster/loremaster/server.py:10478-11450` (ToolAnnotations per tool; `_gated_tool` deploy-wide gate) · `_resolve_env_file` `skills/lore-deploy/scripts/lore_deploy.py:388-404` (LORE_SECRETS_DIR:90; --env-file launch:674)
