# REPORT — scout-router-module-39b

brief-base v14 read
brief project v7 read
intended model: claude-sonnet-5

## SUMMARY BLOCK
- state: **done**
- deviations: none (read-only scout; only writable file is this report). Register+signal was the only comms ceremony.
- **Packages considered:** (the router question is a package-fit survey; full table + cites §3)
  `fastmcp==3.4.7 RemoteAuthProvider` — **replace** (the native resource-server multi-AS router; `authorization_servers: list[...]`) ·
  `fastmcp MultiAuth` — **replace** (verifier-multiplex) ·
  `fastmcp JWTVerifier / AzureJWTVerifier` — **replace_with_adapter** (the MS/Entra JWKS verifier; lore's roster admission wraps it) ·
  `fastmcp KeycloakAuthProvider / WorkOSTokenVerifier / Auth0Provider` (brokers) — **keep_with_trigger** (only if operator elects to run/pay for a broker) ·
  `mcp==1.27.2 create_protected_resource_routes` — **replace** (equivalent lower-level multi-AS route builder if lore stays on the SDK's FastMCP) ·
  `authlib==1.7.2 OAuth.register` — **bespoke** (verdict = REJECT-for-this-model: it is a relying-party *interactive-login* router; lore's resource-server model has no login route to route) ·
  `oauthlib / requests-oauthlib` — **bespoke** (REJECT; low-level primitives, subsumed by fastmcp) ·
  `starlette==1.2.0 Router/Mount` — **bespoke** (REJECT-as-auth-router; a transport path-mounter, not an IdP router) ·
  `Caddy edge (lore-caddy, R4)` — **keep_with_trigger** (stays transport-only; stock Caddy cannot verify OAuth bearer tokens).
- **Reuse ledger:** none — research report; specifies a seam TARGET, introduces no new reusable symbol. All named symbols are framework symbols to REUSE (`RemoteAuthProvider`, `MultiAuth`, `AzureJWTVerifier`) or lore's existing `LoreTokenVerifier` design.
- **Graded:** target is installed packages `fastmcp==3.4.7`, `mcp==1.27.2`, `authlib==1.7.2`, `starlette==1.2.0` in the project venv (a version set, not a repo sha — claims are about dependencies + the design doc, not repo product code). Graded: `9a10604` · HEAD-at-report: `9a10604` · SAME. No repo product artifact was graded.
- **THE REFRAME (load-bearing — read before the answers):** packet 39's design makes lore a **RESOURCE SERVER that VERIFIES bearer tokens** (`LoreTokenVerifier`, design §4), NOT an OAuth **authorization server / OAuthProxy**. The prior scout (`REPORT-scout-fastmcp-oauth-39.md`) analysed the OAuthProxy model — "two login endpoints", broker federation. **In the resource-server model the interactive-login-routing problem does not exist** (claude.ai does the OAuth dance with the IdP; lore never hosts `/authorize`). Multi-provider therefore = **multi-VERIFIER + multi-AS advertising**, both of which fastmcp ships. No hand-rolled front-router is warranted.
- decisions-needed (for lead / design-sidecar / operator):
  1. **fastmcp-vs-SDK auth-wiring discrepancy (flag).** Design §4/§6 describes wiring against the **mcp SDK's** FastMCP (`auth=AuthSettings(issuer_url=…)`, `token_verifier=…`), but lore's HEAD `server.py:68` imports the **standalone `fastmcp` 3.4.7** (`FastMCP(auth: AuthProvider)`, `mcp.http_app()`). Different auth APIs. Reconcile which stack the single-provider build targets — it decides the exact symbols the multi-provider seam later reuses. Multi-AS advertising is native in BOTH (see §3), so the reframe/recommendation is stable either way.
  2. **Broker vs direct-verify** for provider #2: run a broker (Keycloak/WorkOS/Auth0 — one issuer, one JWKS) vs verify Google+MS directly (two verifier branches). Recommendation §4: direct-verify is lower-op-cost and fully packaged; broker is a `keep_with_trigger`.
- receipt pointers: candidate table → §3; direct answers 1–4 → §4; seam-target recommendation → §4 (Q4); comms seqs → §5.

---

## 1. Capability check (brief-base §4)
Tools available and sufficient: Bash (read installed source under `.venv/`), Read, lore tools, comms. No blocker. All source cites below are from files I opened this session in the project venv `/.venv/lib/python3.14/site-packages/` and in-tree `loremaster/`. Nothing in the brief demanded a capability I lack.

## 2. Ground truth established (source-verified this session)
- **lore imports the standalone `fastmcp` 3.4.7**, not the mcp SDK's FastMCP: `from fastmcp import Context, FastMCP` `[source-verified: loremaster/loremaster/server.py:68]`. The ASGI app is built by `build_asgi_app` (`server.py:12360`) from `mcp.http_app(path=…, transport="http", stateless_http=…)` (`server.py:12403`), wrapped in lore's own `OriginValidationMiddleware` and (when auth enabled) `BearerAuthMiddleware` (`server.py:12413-12417`). **Today lore passes NO auth provider to `FastMCP`; the api-key gate is a hand-rolled ASGI wrapper** (`loremaster/loremaster/auth.py`: `BearerAuthMiddleware:208`, `ApiKeyVerifier:104`). `[source-verified]`
- **Installed, auth-relevant** (`uv pip list`): `fastmcp 3.4.7`, `fastmcp-slim 3.4.7`, `mcp 1.27.2`, `authlib 1.7.2`, `oauthlib 3.3.1`, `requests-oauthlib 2.0.0`, `joserfc 1.7.4`, `pyjwt 2.13.0`, `cachetools 7.1.6`, `httpx 0.28.1`, `starlette 1.2.0`, `uvicorn 0.48.0`. **NOT installed:** `python-social-auth`/`social-core`, `fastapi-users`, `fastapi`, `mcpauth`, `authgear`. `[library-verified]`
- **packet 39 architecture = resource server** (design `docs/design/2026-07-31-packet39-google-oauth.md` §4): one `LoreTokenVerifier.verify_token`, two branches (api-key, Google-tokeninfo-POST); `AuthSettings(issuer_url, resource_server_url, required_scopes)`; RFC 9728 protected-resource metadata; **no `/authorize`/`/token`/DCR on lore.** `[source-verified: design §4, §6]`
- **R4 edge (`lore-caddy`) is unbuilt and transport-only**: no `deploy/` dir, no `Caddyfile`, no `forward_auth` anywhere in-tree (grep hits are all docs). Design §R4 = hades SNI-passthrough → lore-caddy (TLS-terminate, reverse_proxy to `127.0.0.1:9202`), `everything else → 404`. `[source-verified: design §R4; repo grep]`

## 3. Candidate table
Fit is judged for lore's **resource-server** model (verify a bearer token; advertise the IdP(s) that issue valid ones). "Installed" = present in the project venv.

| Candidate (module / package / infra) | Installed? | Fit for lore's fastmcp resource-server | API / source cite (opened this session) | Verdict |
|---|---|---|---|---|
| **fastmcp `RemoteAuthProvider`** | ✅ 3.4.7 | **EXACT** — a `TokenVerifier` + `authorization_servers: list[AnyHttpUrl]`; serves RFC 9728 protected-resource metadata advertising **all** listed AS. `FastMCP(auth=…)` accepts it directly. Docstring itself cites "Azure AD full URI scopes vs short-form." | `auth.py:413-507` (`__init__` list arg :431; `create_protected_resource_routes(..., authorization_servers=self.authorization_servers)` :493-496); `FastMCP.__init__(auth: AuthProvider)` `server.py:329` | **replace** |
| **fastmcp `MultiAuth`** | ✅ 3.4.7 | verifier-multiplex: `verify_token` tries each source in order, first non-None wins, exceptions→non-match. This is "try Google, then Microsoft." Routes come only from an optional `server`, so wrap it in RemoteAuthProvider (or lore's own metadata route) for the AS advertising. | `auth.py:510-634` (loop :598-610; routes delegate to server :620-634) | **replace** |
| **fastmcp `JWTVerifier` / `AzureJWTVerifier` / `AzureProvider`** | ✅ 3.4.7 | the MS/Entra side: JWKS-fetch + RS/ES/PS/HS signature validation + issuer/audience checks. `AzureJWTVerifier` derives `issuer`/`jwks_uri` from `tenant_id` — the genuinely hard crypto, packaged. lore's roster admission wraps the verified identity. | `jwt.py:195` (`JWTVerifier`, `issuer`/`audience` :131-164); `azure.py:39` (`AzureProvider`), issuer/jwks derivation :224-245, `AzureJWTVerifier`/B2C :290+ | **replace_with_adapter** |
| **fastmcp brokers: `KeycloakAuthProvider`, `WorkOSTokenVerifier`, `Auth0Provider`** | ✅ 3.4.7 | a broker collapses N IdPs → 1 issuer/JWKS. `KeycloakAuthProvider(RemoteAuthProvider)` and `WorkOSTokenVerifier(TokenVerifier)` are **resource-server-native**. Cleanest identity model, but adds an operational component to run (Keycloak) or pay for (WorkOS/Auth0). | `keycloak.py:15`, `workos.py:31`/`126`, `auth0.py:39` | **keep_with_trigger** (trigger: operator elects to stand up/pay for a broker, or >2 IdPs) |
| **mcp SDK `create_protected_resource_routes(authorization_servers=[...])`** | ✅ 1.27.2 | the SDK's own multi-AS RFC 9728 route builder (what fastmcp's RemoteAuthProvider wraps). The equivalent path **if** the build lands on the SDK's FastMCP (design §4 wording). Multi-AS is a `list[AnyHttpUrl]` here too. | `mcp/server/auth/routes.py:211` (`authorization_servers: list[AnyHttpUrl]`); `AuthSettings.issuer_url` is singular but only feeds the AS-metadata/OAuthProvider path — `settings.py:15-26` | **replace** (SDK-path equivalent) |
| **authlib `OAuth.register` (starlette_client)** | ✅ 1.7.2 | the canonical **multi-provider relying-party** router: `oauth.register('google', …)` + `oauth.register('microsoft', …)`, `create_client(name)`, per-provider `authorize_redirect`/`authorize_access_token`. But this drives lore DOING interactive login — the OAuthProxy model lore does **not** adopt. Its `authlib.jose` (RFC 7519/7517/7515) is a lower-level JWT-validate alternative to fastmcp's `JWTVerifier`. | `integrations/base_client/registry.py:44` (`create_client`), `:81` (`register`); `authlib/jose/` (rfc7519/7517/7515) | **bespoke** = REJECT-for-this-model (would only fit if lore became the AS) |
| **oauthlib / requests-oauthlib** | ✅ 3.3.1 / 2.0.0 | low-level OAuth1/2 request-signing/parsing primitives; no resource-server token-verify router and no MCP integration. Everything useful here is already packaged one level up by fastmcp. | pkg present; no resource-server verifier surface | **bespoke** = REJECT (subsumed) |
| **starlette `Router` / `Mount`** | ✅ 1.2.0 | a transport-level path router. It can mount two ASGI sub-apps at two prefixes — but in the resource-server model there is no per-IdP login sub-app to mount, so it is not an "IdP router" at all. (In the OAuthProxy model it produces the "two-endpoints" shape the prior scout rejected; that shape is moot here.) | starlette routing (`Mount`, `Router`) — installed; not an auth primitive | **bespoke** = REJECT-as-auth-router |
| **Caddy edge (`lore-caddy`, R4) — infra we would RUN** | ▲ unbuilt | SNI-passthrough + TLS-terminating reverse proxy. Stock Caddy **cannot verify an OAuth bearer token** (the token is in the `Authorization` header; only the app's verifier can validate it). Routing "by IdP" at the edge doesn't map to the resource-server model. A `caddy-security`/`forward_auth`-to-an-OAuth-verifier build would be a bespoke add with no advantage over verifying in-app. | design §R4 (transport-only, `everything else → 404`); no in-repo config | **keep_with_trigger** (stays transport; re-open only if per-tenant hostname isolation is ever required) |

---

## 4. Direct answers

### Q1 — Framework-native routing (the Starlette router IS a module). Re-examine "two endpoints." What exactly breaks?
**In lore's actual (resource-server) architecture, the "two endpoints" objection is MOOT — there is no per-IdP login route to place behind a Starlette `Router`/`Mount` in the first place.** `[my judgement, grounded in source]` The prior scout's rejection was correct *for the OAuthProxy model it was analysing* (where each `OAuthProxy` owns singular AS paths `/authorize`, `/token`, `/register`, `/.well-known/oauth-authorization-server`, and two of them collide — `create_streamable_http_app` wires exactly one auth, confirmed by the prior scout). But packet 39 does not make lore an authorization server. `[source-verified: design §4]`

What actually happens in the resource-server model when you add provider #2:
- **MCP OAuth discovery (RFC 9728 protected-resource metadata) natively supports MULTIPLE authorization servers** — `authorization_servers` is a JSON array. fastmcp's `RemoteAuthProvider` takes `authorization_servers: list[AnyHttpUrl]` and serves them all `[library-verified: fastmcp auth.py:431, 493-496]`; the mcp SDK's `create_protected_resource_routes` takes the same list `[library-verified: mcp routes.py:211]`. So **the single `.well-known/oauth-protected-resource/mcp` endpoint advertises Google AND Microsoft with no collision and no second endpoint.**
- **No DCR path collision**, because lore hosts no DCR endpoint (it is not an AS). The client registers with Google/MS directly.
- The one thing that is **not** in our control: whether the claude.ai connector UI lets a human *choose* between two advertised authorization servers. The protocol permits it; the client's behaviour is a claude.ai question, not a lore code question. If claude.ai will only consume a single AS per connector, the operator configures one connector per IdP (each pointing at the same lore, presenting whichever token) — and lore's verifier accepts both. Either way, **lore needs no router; it needs a multi-issuer verifier + a two-element `authorization_servers` list.**

**Verdict on Starlette Router/Mount:** it is a router module we USE (for mounting the MCP app at its path — lore already does), but it is **not the answer to multi-IdP auth**, because auth in this model is a header-borne token the app verifies, not a URL prefix the edge routes. `bespoke`/reject-as-auth-router.

### Q2 — Existing Python packages
- **`authlib 1.7.2` (installed)** — the canonical multi-provider OAuth *client*: `OAuth().register('google', …)` / `.register('microsoft', …)` / `create_client(name)` `[library-verified: registry.py:44/81]`. **This is the right tool for the wrong model** — it routes *interactive login* for an app that is the relying party. lore is not; claude.ai is. Its `authlib.jose` JWT-validation is a usable lower-level alternative to fastmcp's `JWTVerifier`, but fastmcp packages JWKS-fetch/caching/issuer/audience at a higher level, so authlib.jose would be a step *down*.
- **`oauthlib`/`requests-oauthlib` (installed)** — low-level primitives, no resource-server router, subsumed by fastmcp. Reject.
- **NOT installed:** `python-social-auth`/`social-core`, `fastapi-users` (both are Django/FastAPI relying-party login frameworks — same wrong-model as authlib, plus a framework lore doesn't use), `mcpauth`, `authgear`. A missing dep is grounds to ESCALATE for install — but none of these fit the resource-server model, so **none warrants an install request.** `[my judgement]`
- **The best-fit "existing package" is `fastmcp` itself** (already a direct dependency): `MultiAuth` + `RemoteAuthProvider` + `AzureJWTVerifier` produce something you hand straight to `FastMCP(auth=…)` `[library-verified: server.py:329]`.

### Q3 — The broker as the packaged router, and infra we already run
- **(a) Broker providers as "the router module":** yes — a broker is the packaged way to collapse Google-or-MS into one issuer. fastmcp ships `KeycloakAuthProvider(RemoteAuthProvider)` (**resource-server-native** — exactly lore's model) `[library-verified: keycloak.py:15]`, plus `WorkOSTokenVerifier`/`Auth0Provider`. **Self-hosted Keycloak** = a container we run (like the surreal stores) that federates Google+MS upstream; lore then verifies one issuer's JWTs against one JWKS — the cleanest identity model (one `iss`, one `sub` namespace, uniform verified email). **SaaS broker** (WorkOS/Auth0) = zero infra to run, a per-MAU bill, an external dependency in the auth path. Verdict: **`keep_with_trigger`** — a real, packaged option, but it adds an operational component that direct two-verifier dispatch does not need for just two IdPs. Trigger to adopt: operator wants a managed "add an IdP without code", or the IdP count grows past ~2, or cross-IdP identity-merge complexity (prior scout §EXTEND-2) becomes painful.
- **(b) The edge router we already have (Caddy):** **no.** `[source-verified: design §R4]` The R4 lore-caddy is SNI-passthrough + TLS-terminate + `reverse_proxy 127.0.0.1:9202`, `everything else → 404` — pure transport, and not yet built (no `deploy/` in-tree). Stock Caddy cannot verify an OAuth bearer token; the token lives in the `Authorization` header and only lore's verifier can validate it against Google/Entra. Routing "by IdP" at the edge would require either a `caddy-security`/`forward_auth` build (bespoke, and still needs an in-app verifier behind it) or per-IdP hostnames to separate backends (the "two-endpoints" anti-pattern, pointless when one app verifies both). **The edge stays the transport router it already is; auth stays in the app.** `keep_with_trigger` (re-open only if per-tenant hostname isolation is ever required).

### Q4 — VERDICT + single seam target
**There IS an existing module set that does the job; no multi-provider front-router should be hand-rolled.** Ranked, real candidates for the deferred seam:

1. **`fastmcp.RemoteAuthProvider(authorization_servers=[google, microsoft], token_verifier=<multiplexer>)`** — the native multi-AS advertiser. `replace`. `[library-verified: auth.py:413-507]`
2. **`fastmcp.MultiAuth(verifiers=[…])`** (or a thin `iss`-branch inside lore's `LoreTokenVerifier`) — the verification multiplexer. `replace`. `[library-verified: auth.py:510-634]`
3. **`fastmcp.AzureJWTVerifier(tenant_id=…, required_scopes=…)`** — the MS/Entra verifier (JWKS crypto), wrapped by lore's roster admission. `replace_with_adapter`. `[library-verified: azure.py:224-245, 290+]`
4. **A broker (`KeycloakAuthProvider` / `WorkOSTokenVerifier`)** — if the operator elects it. `keep_with_trigger`. `[library-verified: keycloak.py:15]`

**Single recommendation — what the seam should TARGET:**
> Build the single-provider MVP so that its RFC 9728 protected-resource metadata is produced by **`fastmcp.RemoteAuthProvider`** (or, on the SDK path, `create_protected_resource_routes`) with `authorization_servers=[google_issuer]`, and its verification by lore's `LoreTokenVerifier`. Then **provider #2 is (i) one more element in the `authorization_servers` list and (ii) one more issuer-keyed branch/verifier** — the Microsoft branch REUSING `fastmcp.AzureJWTVerifier` for the JWKS crypto, with lore's roster admission applied to the verified identity exactly as for Google. The multiplex is `MultiAuth(verifiers=[…])` or a single `iss`-dispatch in `LoreTokenVerifier`.

The **only** legitimately bespoke surface is the **roster-admission policy** — *which* verified `(iss, sub)`/email lore admits — which is lore domain logic (packages can't decide it), minimal, and already pinned by the design's fail-closed roster contract (R12/R7). That is the rule working as intended (side 2), not a hand-rolled router. **A multi-provider "front-router" is unnecessary and should not be written**; if a future requirement forces lore to become an authorization server (interactive login hosted BY lore), re-open with authlib's `OAuth.register` as the packaged relying-party router and escalate the security review — but nothing in packet 39 requires that.

**Evidence-backed statement of what would be hand-rolled if the rule's side-2 ever fired:** nothing in the multi-provider path, because every hard piece (multi-AS advertising, JWT/JWKS verification, verifier multiplexing) is shipped by `fastmcp` and reachable from lore's `FastMCP(auth=…)`. I checked: fastmcp `RemoteAuthProvider`/`MultiAuth`/`JWTVerifier`/`AzureJWTVerifier`/brokers (all installed, all read), the mcp SDK's `create_protected_resource_routes`, authlib's client registry + jose, oauthlib, and Starlette routing. The gap the operator feared ("hand-roll a multi-provider OAuth front-router") **does not exist in this architecture.**

---

## 5. Comms note
- register seq: `register scout-router-module-39b (session pkt39-recut, role scout) — status active; project brief v7 auto-acked`.
- signal → lead-39-recut, thread `router-scout`: seq **#5096** ("registered (Sonnet respawn), starting router-module check.").
- heartbeat: one (milestone note — architecture established + fastmcp multi-provider primitives confirmed).
- inbound / ack owed: none drained; no directive received; I owe no ack.
- closing signal (report path) → lead-39-recut: sent at exit (seq in the send result).

## 6. Scope-law flags raised (not folded in)
1. **fastmcp-vs-mcp-SDK auth-wiring discrepancy** (decisions-needed #1): design §4/§6 wires the mcp SDK's FastMCP (`auth=AuthSettings`, `token_verifier=`); HEAD `server.py:68` uses standalone `fastmcp` 3.4.7 (`FastMCP(auth: AuthProvider)`). A builder taking §4 literally against the imported package will hit an API mismatch. Reconcile before the single-provider build. (Multi-AS advertising is native in both stacks, so this scout's recommendation is stable regardless.)
2. **The prior scout's report analyses a different architecture** (OAuthProxy/interactive-login) than packet 39 adopts (resource-server). Its broker-federation recommendation is sound but answers "if lore were the AS"; the resource-server reframe here supersedes it for the multi-provider-seam question. Both reports should be read together, with this one governing the seam target.

_End of report._
