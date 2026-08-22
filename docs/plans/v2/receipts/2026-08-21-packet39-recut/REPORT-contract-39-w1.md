# REPORT — contract-39-w1 (packet 39 RE-CUT, wave-1 contract author)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done — REVISED round 1** (post-adversary #394 INSUFFICIENT → the 4 surviving wrong builds now pinned; see §Revision round 1). RED contract + stubs; collectable; behaviourally RED; 5 decisions escalated.
- deviations:
  - Stub lives in a NEW module `loremaster/loremaster/token_verifier.py` (brief said "your call") — isolates the fresh contract from the retired `loremaster.auth.LoreTokenVerifier` symbol the prior contract expected (E4).
  - Reused `_auth_fixtures.py`'s **model-agnostic** machinery by import (DRY) rather than re-creating it — couples the fresh contract to a module whose model-SPECIFIC parts must be retired (E1).
- **Packages considered:** `fastmcp==3.4.7` — `TokenVerifier` base + `AccessToken` → **replace/use-framework** (subclassed as the verifier base, minted as the identity — READ `.venv/.../fastmcp/server/auth/auth.py:54-57,366-410`); `GoogleTokenVerifier` → **bespoke (hand-roll)** for Google authN, READ `.venv/.../fastmcp/server/auth/providers/google.py:57-201` → fails 3 BLOCKER props (finding **#393**). `httpx.MockTransport` (already a dep) → **reuse** (the tokeninfo transport spy). `cachetools.TTLCache` → the builder's (design §4.2), not built here. See §Packages.
- **Reuse ledger:** 5 new symbols, all dispositioned (§DRY ledger). Reused: `_auth_fixtures.{tokeninfo_payload,TokeninfoSpy,admitted_payload,…}`, `PrincipalStore`, `PrincipalKeyStore.verify`, `_surreal_harness.*`, fastmcp `TokenVerifier`/`AccessToken`.
- **Graded:** fastmcp==3.4.7 (a package version, not a repo sha) + the prior-contract STALE verdict · HEAD-at-report: `50fb230` · base I worked at: `50fb230` (SAME).
- decisions-needed (escalations, all durable in this report — none blocks the build):
  - **E1** — the prior 2026-07-31 SDK-FastMCP 39 contract must be ARCHIVED by the lead (it collides with the fresh contract; §E1).
  - **E2** — api-key write-scope reading under the read-only-hosted banner (I pinned "LAN keeps full write"; one pin flips if ruled otherwise; §E2).
  - **E3** — the `(principal, agent)` seam SHAPE is under-specified for wave-1 (I pinned a minimal `claims["agent"]=None`; §E3).
  - **E4** — confirm the stub's home (`token_verifier.py` vs `auth.py`; §E4).
  - **#393** — GoogleTokenVerifier reuse→bespoke verdict flip (design §12 listed it USE-FRAMEWORK; source refutes for Google authN). Filed as finding #393.
- receipt pointers: pin inventory → §Pin inventory; fixtures → §Fixtures; deferred → §Deferred; RED/GREEN receipt → §Receipts; escalations → §E1-E4 + finding #393.

---

## Revision round 1 (post-adversary adversary-39-w1 / finding #394 — INSUFFICIENT → addressed)
The adversary confirmed the contract SATISFIABLE (ref build 37/37) and STRONG (17/21 wrong builds caught, seam not vacuous) but found **4 wrong builds passing the whole contract** — one BLOCKER-class. All four are now pinned (no redesign; +7 test items, `agent_of` accessor):

| adversary find | wrong build it lets through | new pin(s) |
|---|---|---|
| **MISSING PIN #1 (BLOCKER)** | WB4a `bool(email_verified)` ADMITS the string `"false"` (unverified admitted); WB4b `email_verified is True` DENIES the string `"true"` (100% real-login denial) | `TestAdmission::test_email_verified_string_and_bool_representations` (parametrized over `"true"`/`True`/`"false"`/`False`/absent — admit iff genuinely verified) + the string-`"false"` fate added to the Auth ∀ deny set |
| **MISSING PIN #2 (low)** | WB20 Google `client_id=sub` (the fastmcp `google.py:176` reuse trap) | `TestGoogleVerification::test_google_client_id_is_the_configured_oauth_client_not_the_sub` (client_id == GOOGLE_CLIENT_ID, ≠ sub) |
| **MISSING PIN #3 (optional)** | WB21 `scopes=[lore:read, "lore:bogus"]` | the two hosted scope pins + the ∀ admit fate strengthened to `set(scopes) == {lore:read}` (exact set) |

**Sidecar rulings folded** (lore_comms #5106): #393 CONFIRMED (Google authN hand-rolled; the 3 property-pins — token-not-in-URL, aud-vs-client, 401/5xx-split — each retain a discriminating control: token-IS-transmitted; matching-aud-admits; 5xx-fails-closed-and-not-cached-positive + transient-503-then-200-admits; the "expired/invalid rejects" control is `test_401_is_negative_cached`). **E3 CONFIRMED** — the `(principal, agent)` seam is now read through ONE typed accessor `agent_of(token) -> str | None` (`loremaster/token_verifier.py`, not scattered `claims["agent"]`), with **fail-closed** semantics documented for packet 62 (a missing/unbound agent → `None` → packet-62 agent-scoped ops treat `None` as DENY); `test_agent_of_is_the_typed_fail_closed_accessor` proves it READS a bound agent (not a constant None) and fail-closes on absent, and the seam pin still asserts the slot EXISTS (anti-WB14).

Round-1 receipts (at `50fb230`): **44 collected / 0 errors**; `pytest` → **40 failed (behavioural RED) / 4 passed** (the 3 seam pins + the `agent_of` unit — GREEN-now, guard existing behaviour); `ruff check` **All checks passed!**. A DELTA adversary pass follows (standing law). E1/E2/E4 + finding #393 unchanged.

## E1 cleanup (post-GREEN-build; executes design §9's adjudicated removed-behaviour inventory — NOT committed)
Directive #5114 (thread w1-contract-e1). GOAL: retire the STALE 2026-07-31 SDK-FastMCP contract + drive packet-39 mypy toward zero before the cold audit, keeping ALL keepers + wave-1 pins green.

**mypy DELTA (`scripts/typecheck.sh`, at `50fb230`):** loremaster **50 → 1**, lorerunes **69 → 0** (total **119 → 1**). ruff **All checks passed** across every touched file.

- **E1a — `test_auth.py`:** retired the stale `GoogleOAuthConfig`/resource-path/new-`LoreTokenVerifier`-in-`auth` pins (`TestGoogleOAuthConfigFailsClosed`, `TestLoreConfigCrossChecksTheResourcePath`, + 2 pins in `TestRetiredAuthSurfaceIsGone`); fixed imports; added a superseded-header docstring note. Kept: `TestApiKeyVerifierIsPreservedVerbatim`, `TestBuildApiKeyVerifierFromConfig`, `TestOriginValidationMiddlewareIsPreserved`, the retired-hand-roll absence pins, `TestAuthConfigRetiresTlsTerminatedUpstream`, and `_drive`/`_RecordingApp` (public-by-use). test_auth mypy **6 → 0**; **26 keepers green**.
- **E1b — `_auth_fixtures.py`:** AST-removed the ORPHANED old-model entry points (`make_verifier`, `DEFAULT_API_KEYS`, `rewrite_roster`, `sdk_bound_handler_names`, `as_principal`, `call_and_capture`) + the now-unused `Iterator` import. mypy **3 → 1** (637/638 gone). ⚠ **SCOPE FINDING:** `_auth_fixtures.py` is NOT purely the stale-39 module — its wire/ASGI/roster harness (`wire_session` → `hosted_auth_block`/`write_roster`/`base_config_payload`/`running_asgi_app`/`stub_heavy_startup`) is LIVE shared infra imported by `test_refusal_observes_effect.py` (a GREEN pkt59-era #295 auth-independent instrument). So E1b could only retire the orphaned entry points; the harness STAYS.
- **E1c — lorerunes:** `git mv` `test_posture.py` + `test_roster_parser.py` → `docs/plans/v2/receipts/2026-08-21-packet39-recut/` with superseded-headers. lorerunes mypy **69 → 0**; lorerunes suite **23 green**.
- **E1d — frozen wave-1 contract:** annotated all fixture params (`PrincipalStores` alias; behaviour-preserving — no assertion/pin changed, so the adversary SUFFICIENT verdict holds). test_token_verifier mypy **40 → 0**; wave-1 contract **44 green** (build is GREEN).

**THE 1 mypy error that REMAINS (adjudicated-red, named per directive):** `loremaster/tests/_auth_fixtures.py:759` — `Unexpected keyword argument "http_client" for "build_mcp_server"`. **PRE-EXISTING** (present in the before-run, was line 872). It is in the KEPT `wire_session`'s HOSTED-posture branch (`build_mcp_server(server, http_client=spy.client())`); `build_mcp_server(server: LoreServer)` has no `http_client` param post-pkt59, and the live consumer `test_refusal_observes_effect` uses `posture="loopback"` (never the http_client path — so it's dead-at-runtime today, green). **OUT of E1 scope:** `build_mcp_server` is the builder's prod file, and a `# type: ignore` would MASK the real signal that wave-3 composition must give `build_mcp_server` (or the verifier construction) the injected-`http_client` seam (design §4.3/§8). Recommend wave-3/builder resolves.

**`test_auth.py` — 7 pytest-RED that REMAIN (not mypy; flagged, NOT retired):** `TestRetiredAuthSurfaceIsGone` (BearerAuthMiddleware/AuthVerifier not-importable/not-exported ×4) + `TestAuthConfigRetiresTlsTerminatedUpstream` (×3). These are **WAVE-3 FORWARD-LOOKING pins** — they pin the re-cut's intended deletion of the hand-roll (`BearerAuthMiddleware`/`AuthVerifier`) and the `tls_terminated_upstream` flag when `auth.py`/`AuthConfig` are rewritten for composition (§8/§9). They were RED before E1 (pre-existing #333 bound), are NOT stale (they pin intended behaviour), and are NOT keepers I broke. E1a REDUCED test_auth RED **25 → 7** by retiring the stale-model pins.

**Removed-name sweep (anchor-free, per P8d law — every residual verdicted):** `as_principal` / `call_and_capture` / `rewrite_roster` → **zero references** (fully removed). `make_verifier` / `GoogleOAuthConfig` / `sdk_bound_handler_names` → residuals are ALL **prose** (my E1a/E1b docstrings + retirement notes + the `test_wire_discipline.py` tombstone's historical prose) — no live import or call. Individually confirmed.

**Deviations / scope notes:** (1) 6 stale sibling files (`test_auth_composition`, `test_auth_identity_seam`, `test_google_token_verifier`, `test_allowlist_roster`, `test_hosted_readonly_posture`, `test_permission_resolver_seam`) were ALREADY `git mv`'d to receipts by a prior step (staged `R`) — not my doing. (2) `test_wire_discipline.py` is already a superseded-header TOMBSTONE (pkt59) — left as-is (no real `_auth_fixtures` import). (3) `test_refusal_observes_effect.py` is NOT retired — it is a LIVE GREEN #295 instrument. (4) **NOT committed** (cold audit follows). Backup of the mutation set at `/tmp/e1-backup-contract39w1/` (uncommitted-tree insurance).

## Deliverables (writable set)
- `loremaster/loremaster/token_verifier.py` — the `LoreTokenVerifier` interface STUB (`verify_token` raises `NotImplementedError`; full `__init__` + the minted-`AccessToken` contract in the docstring). NOT the implementation.
- `loremaster/tests/_token_verifier_fixtures.py` — the fresh contract's plain helpers + re-exported model-agnostic `_auth_fixtures` machinery.
- `loremaster/tests/test_token_verifier.py` — §13 groups **1, 2, 3** + the **Auth ∀** + the design **ADD** (34 pins).
- `loremaster/tests/test_oauth_identity_seam.py` — §13 group **7**, the child-table PIN-THE-MISS seam (3 pins, GREEN-now / RED-on-regression).
- this report.

## Receipts (RED/GREEN, at `50fb230`, post-revision-round-1)
- `uv run python -m pytest --collect-only` → **44 tests collected, 0 collection errors** (behaviourally collectable, not ImportError). (Round 0 was 37; +7 = 5 `email_verified` params + the `client_id` pin + the `agent_of` unit.)
- `uv run python -m pytest loremaster/tests/test_token_verifier.py loremaster/tests/test_oauth_identity_seam.py` → **40 failed, 4 passed in 12.07s**.
  - The 40 fail BEHAVIOURALLY on `NotImplementedError` from the stub (round-0 sampled tail confirmed the exception is `token_verifier.py NotImplementedError`, reached AFTER the live-store setup ran — create_principal / mint_credential succeeded against `ws://127.0.0.1:18000`). This is the RED contract-first state.
  - The 4 PASS by design: the 3 `test_oauth_identity_seam.py` PIN-THE-MISS seam pins (guard the shipped single-`subject` model → GREEN now, RED when `oauth_identity` is added) **plus** `test_agent_of_is_the_typed_fail_closed_accessor` (a pure unit over the real `agent_of` accessor — GREEN now, guards its read + fail-closed behaviour).
- `uv run ruff check` (all 4 files) → **All checks passed!** (I001 auto-fixed; F811 avoided by defining the `principal_stores` fixture LOCALLY in the test file per the house idiom; F401 covered by `__all__` re-export in the fixtures module).
- Satisfiability receipt (0-failed on a correct build): **deferred to the contract-adversary's reference build** (design §13 — the adversary must BUILD the fix to grade the contract anyway).

---

## The load-bearing discovery (finding #393) — READ-THE-DOCS-THEN-VERIFY paid off at CONTRACT time

The design's default (§4.1/F3) was to REUSE fastmcp `GoogleTokenVerifier` for Google crypto/HTTP. A contract-time READ of the installed source (`.venv/.../fastmcp/server/auth/providers/google.py`) **refutes fit for 3 BLOCKER properties** the design pins:
1. **Token in URL, not body** — `client.get(tokeninfo, params={"access_token": token})` (`google.py:108-112`). Violates "token never in a URL" (the journal-leak the threat model names). NOT wrappable (the HTTP call is inside the framework method).
2. **No aud-vs-client_id check** — it rejects only a *missing* `aud` (`:123-133`), never compares to a configured client_id (it has no client_id param, `:57-90`). A different-client token is ACCEPTED — a confused-deputy hole.
3. **No 401-vs-5xx split** — any non-200 → `None` (`:114-119`); malformed JSON → `None` (`:196-201`). lore's cache cannot split negative caching by observing its return.

The design's §4.1/§9/F3 AUTHORISED exactly this fallback ("hand-roll the tokeninfo POST only with a cited READ"). **This report is that cited read.** So Google verification is HAND-ROLLED (packages-over-hand-rolling side-2), and the wave-1 group-2 pins are written as PROPERTIES at the `LoreTokenVerifier` boundary (driven via an injected `httpx` transport spy) so that a build naively reusing `GoogleTokenVerifier` REDs. Filed as **finding #393** (capability_gap, packet39-oauth). The builder still USES fastmcp for the `TokenVerifier` base + `AccessToken` minting + `get_access_token` (wave 2/3) — only Google authN is bespoke.

---

## Pin inventory (grouped; each: assertion · discrimination — the WRONG build it catches · expected-RED node id)

All expected-RED node ids are under `loremaster/tests/test_token_verifier.py::` unless noted. All 34 are RED against the stub; each discriminates against a specific wrong build on the adversary's reference build.

### Group 1 — Admission (design §3.2 / §13 g1) — `TestAdmission`
| pin (node id) | asserts | discriminates against |
|---|---|---|
| `test_active_principal_is_admitted` | active principal + verified/aud-matching token → AccessToken, subject==email | POSITIVE CONTROL (the verifier can say yes) |
| `test_no_principal_is_denied` | verified identity, no principal row → None | a build treating a verified token as admission |
| `test_suspended_principal_is_denied` | status=suspended → None | a build checking existence but not status |
| `test_expired_principal_is_denied` | expires_at in the past → None | a build ignoring expiry |
| `test_future_expiry_principal_is_admitted` | expires_at in the future → admitted | CONTROL (expiry is a real comparison, not reject-if-set) |
| `test_email_verified_false_is_denied_before_principal_lookup` | F1: email_verified=false → None AND `CountingPrincipalStore.lookup_calls==0` | a build that keys admission BEFORE checking email_verified (ordering) |
| `test_email_verified_absent_is_denied` | email_verified absent → None | a build guarding `==False` but letting `None`/absent through |
| `test_returning_login_fast_path_equals_email_result` | returning (subject-bound) login == first (email) login identity | a build whose get_by_subject fast-path resolves wrong / to None (denies returning users) |
| `test_admission_is_never_cached_suspend_takes_effect_next_request` | suspend mid-session → next request None, WHILE the Google verdict cache HIT (call_count stable) | a build caching the ADMISSION decision |
| `test_admission_normalisation_matches_a_lowercase_stored_principal` | mixed-case Google email admits against a lowercase-stored principal (via shared lorerunes.normalize_email) | a build comparing raw strings; the shared-mutation half of the normaliser pin |

### Group 2 — Google verification (design §4.1 / §13 g2, HAND-ROLLED per #393) — `TestGoogleVerification`
| pin | asserts | discriminates against |
|---|---|---|
| `test_different_client_aud_is_denied` | **BLOCKER**: aud==OTHER_OAUTH_CLIENT_ID (real, different client), principal exists, email_verified true → None | fastmcp GoogleTokenVerifier (accepts any non-empty aud, #393) — proves aud is not decorative |
| `test_absent_aud_is_denied` | aud omitted → None | a build skipping the aud check when the key is missing |
| `test_matching_aud_is_admitted` | aud==configured client_id → admitted | CONTROL (aud check ≠ reject-everything) |
| `test_missing_email_scope_is_denied` | scope without email + email absent → None | a build admitting without a verified email to key on |
| `test_sub_is_extracted_and_used_as_the_runtime_subject` | claims["sub"]==Google sub AND get_by_subject(sub) resolves after login | a build using email-as-sub or leaving sub None (the odoo-code port bug) |
| `test_token_never_appears_in_the_request_url` | **BLOCKER**: token not in any request URL, IS transmitted in body/auth header | fastmcp GoogleTokenVerifier (token in URL query, #393) |
| `test_401_is_negative_cached` | second call after a 401 makes NO new outbound | a build re-hitting Google on every bad token |
| `test_5xx_is_not_cached` | second call after a 5xx makes a FRESH outbound | a build caching a 5xx (locks a valid token out) — #393: fastmcp collapses 401/5xx |
| `test_transient_5xx_then_success_admits` | 503 then 200 → ultimately admits | a build negative-caching the 503 into a permanent denial |
| `test_malformed_json_denied_and_not_cached` | 200 non-JSON → None, not cached | a build caching a malformed result or crashing |
| `test_expires_at_is_absolute_not_relative` | minted expires_at is an ABSOLUTE unix ts ~lifetime in the future | the unit trap: storing relative `expires_in` (3599→1970) → 100% denial |
| `test_expired_token_is_not_served_from_cache` | after the clock passes expiry, a cache-HIT re-verifies (fresh outbound) | a build serving a stale-valid positive-cache entry |

### Group 3 — Identity mint #206 (design §3.3 / §13 g3) — `TestApiKeyIdentityMint`
| pin | asserts | discriminates against |
|---|---|---|
| `test_api_key_resolves_to_the_principal_not_the_key_name` | api-key → subject==principal email, client_id==`api_key:{email}`, key name NOT the identity | a build minting identity from the key name |
| `test_two_keys_of_one_human_are_one_principal` | **#206**: two keys of one principal → one subject + one client_id | a build keying on the key name (two identities) |
| `test_distinct_principals_get_distinct_identity` | two humans → distinct subject + client_id | a constant/collapsed subject (F3 at the verifier level) |
| `test_api_key_branch_routes_through_principal_key_store_verify` | monkeypatch `verify`→None → api-key auth denies (control: admits before) | ROUTING-IS-NOT-SHARING: a build hand-rolling its own hash check under the driver |
| `test_a_google_token_falls_through_to_the_google_branch` | colon-free Google token, no google_client_id → None | a build whose api-key branch mis-admits a non-api-key credential |

### The design ADD (role-as-data / seam / role→capability function) — `TestMintedIdentityCarriesRoleAndSeams`
| pin | asserts | discriminates against |
|---|---|---|
| `test_hosted_member_gets_read_only_scope` | hosted member → scopes has lore:read, NOT lore:write | a build granting hosted write |
| `test_hosted_admin_is_ALSO_read_only_regardless_of_role` | **anti-premature-RBAC**: hosted admin → NOT lore:write | a build hard-coding `admin ⇒ +lore:write` (jumping to RBAC) |
| `test_minted_identity_carries_the_role_as_data` | member → claims["role"]=="member" | a build dropping role (RBAC can't act) |
| `test_minted_identity_carries_the_admin_role_as_data` | admin → claims["role"]=="admin" | value monoculture (a build hard-coding one role value) |
| `test_minted_identity_exposes_the_agent_binding_seam` | claims has "agent" key, value None (packet-62 seam) | a build with no room for the (principal, agent) seam — SOFT, see E3 |
| `test_api_key_principal_keeps_full_write` | **FLAGGED (E2)**: api-key → scopes has lore:write | a build read-only-ing api-keys (LAN keeps full write; flip if E2 ruled otherwise) |

### The Auth ∀ (design §13) — `TestAuthQuantifier`
- `test_every_google_fate_is_none_or_a_wellformed_access_token` — every denial fate (aud-mismatch, aud-absent, email_verified-false, email_verified-absent, no-email-scope, no-principal) → None; the single admit fate → a well-formed AccessToken mapping to the active principal, carrying role, deriving NO write from role. FORCES each fate with a fixture (no ∀-helper evaluated only where the branch can't fire). Discriminates: a third fate (exception / half-shape) or a scope-derived-from-role on the hosted branch.

### Group 7 — child-table SEAM (design §3.6 / §13 g7) — `test_oauth_identity_seam.py`
- `test_principal_ddl_defines_a_single_subject_column` · `test_no_oauth_identity_table_exists_yet` · `test_schema_module_defines_no_oauth_identity_generator`. GREEN now (guard the shipped single-issuer model); each RED-on-regression the day `oauth_identity` is added, carrying the re-open-trigger message (the migration the adder then owes). PIN-THE-MISS instrument (findings #137/#138 class).

---

## Fixtures — why each discriminates (fixture-monoculture law)
- **≥2 distinct emails** (OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL, UNLISTED_EMAIL) and **≥2 distinct api-key names/secrets** — so a build branching on a single value cannot pass (the #206 and distinct-principal pins need two).
- **member AND admin** principals exercised (the role-as-data + read-only-regardless-of-role pins) — a build hard-coding one role value reds.
- **`OTHER_OAUTH_CLIENT_ID`** — a real, well-formed, DIFFERENT Google client, so "aud is not decorative" is a genuine negative, not a malformed token.
- **`tokeninfo_payload` emits Google's REAL shape** — string-typed numerics, `expires_in` (relative) AND `exp` (absolute) consistently, scope as full URIs — so the expires_at unit-trap and the scope-form traps are reachable (reused from `_auth_fixtures`, which exists FOR these traps).
- **`TokeninfoSpy` records every outbound request** (url, content, headers, call_count) — so token-not-in-URL and the cache-split (via a delta on call_count, robust to in-call retry) are provable.
- **The admission path runs against the REAL 48/49 stores** (unique throwaway DB) — so `option<> subject` UNIQUE, `set_subject` idempotence, and status/expiry are the engine's real behaviour, not a fake's.
- **`CountingPrincipalStore`** — the only way to prove the ORDERING property (email_verified denied before principal lookup), which a plain None-deny cannot distinguish.

## DRY ledger (new reusable symbols)
| new symbol | search run | returned | disposition |
|---|---|---|---|
| `LoreTokenVerifier` (stub) | `grep -rn LoreTokenVerifier`, `lore_get_symbol` | only the RETIRED `_auth_fixtures.make_verifier` references `loremaster.auth.LoreTokenVerifier` (never defined) | **HAND-ROLLED** (new component; the design mandates it; the retired reference is the wrong model) |
| `make_lore_token_verifier` (test factory) | read `_auth_fixtures.make_verifier` | the retired factory builds the WRONG shape (roster + ApiKeyVerifier) | **HAND-ROLLED** (recut model — principal substrate) |
| `create_principal` / `mint_credential` (test helpers) | read `test_principals_store.py` / `test_principal_keys_store.py` fixtures | those define per-file fixtures, not shared factories | **HAND-ROLLED** (thin wrappers over `PrincipalStore.create` / `PrincipalKeyStore.mint`; reuse `sha512_hex`) |
| `CountingPrincipalStore` (test double) | grep for a counting/spy store | none | **HAND-ROLLED** (ordering-proof instrument; delegates to the real store) |
| `principal_stores` (fixture) | read `_surreal_harness` fixtures | `surreal_env`/`admin_db` exist but yield raw conns, not readied principal stores | **EXTENDED** the harness helpers (`make_env`/`connect_admin`/`drop_database`) into a readied store-pair fixture |
| email normaliser | `lore` + read `lorerunes/__init__.py` | `normalize_email` is a pre-contracted `lorerunes` primitive (`test_email_normalisation.py`) NOT yet implemented | **REUSED `lorerunes.normalize_email`** (the builder implements + the shared-mutation pin proves routing) |
| scope constants | design §3.5 | `lorerunes` is the ruled home (not yet holding them) | **REUSED (as wire literals)** — pins assert the wire value; the builder reuses the lorerunes constants |

Reused verbatim (no new symbol): `PrincipalKeyStore.verify` (#206 routing), `PrincipalStore.{get_by_email,get_by_subject,set_subject,set_status,create}`, `_auth_fixtures.{tokeninfo_payload,TokeninfoSpy,admitted_payload,always_json,always_status,scripted,RecordedRequest,google_access_token,OTHER_OAUTH_CLIENT_ID,…}`, `_surreal_harness.{make_env,connect_admin,drop_database,unique_database,PRODUCTION_DIM}`, fastmcp `TokenVerifier`/`AccessToken`.

---

## Deferred to waves 2/3 (out of this file, per brief)
- **Wave 2 (#295 enforcement middleware):** §13 group 4 — the `on_list_tools`/`on_call_tool` default-deny guard keyed on `readOnlyHint` + the minted `lore:write` scope; coverage-as-checked-variable; the #295 EFFECT pin; the wire-level "X cannot resume Y's session" enforcement against the ASSEMBLED app (I pinned only the verifier-level identity-distinctness precondition).
- **Wave 3 (composition/config):** §13 groups 5 & 6 — `.well-known`/401/`resource_metadata=`, Origin/Host transport enforcement, the posture cross-product + `host_is_loopback` grid, the `OAuthProviderConfig`/`AuthConfig` pydantic models, `client_secret` handling, in-image conformance.

---

## Escalations (all durable here; none blocks the build)

### E1 — the prior 2026-07-31 SDK-FastMCP packet-39 contract must be ARCHIVED (lead/git action)
The tree carries the RETIRED prior contract, currently RED in the suite (the #333 auth-WIP bound):
- `loremaster/tests/test_auth.py` (`6e9e845`, "the Google-OAuth contract — 422 pins, 389 RED") — its Google-OAuth pins target the retired `loremaster.auth.LoreTokenVerifier`(roster + in-memory `ApiKeyVerifier`); its **`ApiKeyVerifier` constant-time/empty-key/SecretStr pins are GREEN and KEPT** (design §9; brief). Retirement must PRESERVE the ApiKeyVerifier pins and archive the rest.
- `loremaster/tests/test_auth_identity_seam.py` (`71bdd37`) + `loremaster/tests/test_auth_composition.py` (`cdec4ca`) — assert RETIRED SDK-FastMCP internals (`StreamableHTTPSessionManager` ownership tuple, `TransportSecuritySettings` 421, `_setup_handlers`, `mcp.call_tool`) that the recut §2/§7/§9 drops (R13/R16 DROPPED).
- `loremaster/tests/_auth_fixtures.py` (`130fa16`, packet-59-touched) — MIXES **model-agnostic** machinery my fresh contract REUSES (`tokeninfo_payload`/`TokeninfoSpy`/`admitted_payload`/constants) with **retired** model-specific parts (`make_verifier` roster+ApiKeyVerifier, `hosted_auth_block`, `GoogleOAuthConfig`, `wire_session`, `sdk_bound_handler_names`, `as_principal`).

**Recommendation:** archive `test_auth_identity_seam.py` + `test_auth_composition.py`; extract-and-keep test_auth.py's ApiKeyVerifier pins, archive its Google pins; KEEP `_auth_fixtures.py`'s model-agnostic core (my fresh `_token_verifier_fixtures.py` imports it) and retire its model-specific parts. My fresh stub is in a NEW module so it does NOT collide with the retired `loremaster.auth.LoreTokenVerifier` symbol (the retired import still ImportErrors as before — I did not change its RED state). ⚠ If the lead retires `_auth_fixtures.py` WHOLESALE, my fresh contract's re-export seam (`_token_verifier_fixtures.py`) needs its model-agnostic imports inlined — one file, flagged there.

### E2 — api-key write-scope under the READ-ONLY-hosted banner (I pinned a reading; flip is one pin)
The banner makes HOSTED principals read-only regardless of role (unambiguous — pinned firmly). But the banner ALSO says "LOOPBACK + LAN_BEARER are UNCHANGED — LAN api-keys keep full write (F7 role-gating deferred to RBAC)." §7's "in HOSTED_OAUTH no principal carries lore:write" reads narrowly (hosted = Google principals). Two readings of what the api-key branch MINTS in this packet:
- **(A, pinned)** api-key branch mints `{lore:read, lore:write}` — "LAN keeps full write" (banner); the wave-2 guard keys on the minted `lore:write`, so the fleet must carry it to keep writing.
- **(B)** api-key mints `{lore:read}` in packet 39 (hosted deploy is uniformly read-only until RBAC).
I pinned **(A)** in `test_api_key_principal_keeps_full_write` (clearly marked). If the lead/operator rules **(B)**, that ONE pin flips to `LORE_WRITE not in scopes`. Recommend A (banner-literal + the fleet-unaffected-on-loopback consequence F7 already accepted).

### E3 — the `(principal, agent)` seam SHAPE is under-specified for wave-1
The banner/ADD require an "optional (principal, agent) binding SEAM (forward-compat for RBAC packet 62)" but do not rule its concrete shape. I pinned a MINIMAL seam: `claims["agent"]` exists and is `None` in packet 39 (`test_minted_identity_exposes_the_agent_binding_seam`, marked SOFT). Packet 62 (server-bound (principal, agent) credentials) should rule the concrete shape; if the builder/adversary finds `claims["agent"]` too prescriptive, adjust that one pin.

### E4 — stub home: `token_verifier.py` (new module) vs `auth.py`
Design §4.1 says `class LoreTokenVerifier(fastmcp...TokenVerifier)` without ruling the module; §8 keeps `auth.py`'s `ApiKeyVerifier`/`OriginValidationMiddleware`. I put the stub in a NEW `loremaster/loremaster/token_verifier.py` (matches the one-module-per-concern idiom of `principals.py`/`principal_keys.py`, and avoids resurrecting the retired `loremaster.auth.LoreTokenVerifier` symbol prematurely). Confirm; relocating is a one-import change for the builder.

---

## Note on the design's ".subject vs .claims" framing (superseded by the hand-roll)
Design §3.1 said "read `sub` from `claims["sub"]`, NOT `.subject`" — that was a REUSE-specific fact about fastmcp GoogleTokenVerifier's OUTPUT token (which leaves `.subject` None). Since Google verification is now hand-rolled (#393), lore reads `sub` from the tokeninfo JSON `sub` field directly; I re-framed the pin as the underlying property (correct sub extraction + binding, `test_sub_is_extracted_and_used_as_the_runtime_subject`), which holds regardless of reuse-vs-handroll. The minted lore AccessToken's `subject` I set to the PRINCIPAL email (consistent with the api-key branch + #206 "identity is the principal") and `claims["sub"]` to the Google sub — a decision the design left as "principal identity" (vague); stated here.

## Ambiguity NOT escalated (design was clear enough)
- "ApiKeyVerifier consulted via PrincipalKeyStore.verify" (§4.1/§8) reads self-contradictory (two different mechanisms), but #206 (§3.3, principal_keys.py) is unambiguous that the api-key branch routes through `PrincipalKeyStore.verify`. I pinned that; ApiKeyVerifier the class stays with its kept-green test_auth pins, not called by LoreTokenVerifier.
