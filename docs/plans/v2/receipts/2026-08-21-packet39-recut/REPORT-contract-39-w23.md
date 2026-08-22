# REPORT — contract-39-w23 (packet 39 RE-CUT, wave 2+3 contract author)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done — REVISED round 1** (adversary-39-w23 INSUFFICIENT #5130 → 2 cheap fixes applied;
  security boundary was SOLID — see §Revision round 1). All 7 §13 groups authored (config/removed/
  posture-derive/composition/enforcement + the wire halves), behaviourally RED-confirmed, gate-clean.
  ESC-1 GRANTED (#5123) → hosted wire harness recut; ESC-2 no-field (pinned); MERGE confirmed. Ready
  for the DELTA adversary pass.
- deviations:
  - **Enforce-wire (#295 EFFECT) pins are ERROR-RED against the stub, not clean-behavioural-RED**:
    they drive an authenticated hosted SDK session, which needs the composition's `FastMCP(auth=…)`
    to authenticate a bearer + `build_asgi_app` to drop `BearerAuthMiddleware` (builder GREEN work I
    may not write). Against the stub the hosted `initialize` 401s (measured), so the pins RED by the
    wire failing to establish → GREEN once the composition lands. The transport-posture pins ARE
    clean-behavioural-RED (raw-ASGI anonymous `drive()`). (§Pin inventory wire groups.)
  - **Posture stub + contract under `lorerunes/`** (design §6 "posture derivation lives in lorerunes")
    — the brief's "under loremaster/tests/" is loose; the explicit "posture derivation" stub grant governs.
  - **`test_config.py:399` (DUAL-law corpse pin)** asserts the retired `tls_terminated_upstream`
    default — the BUILDER retires it in the GREEN commit that removes the field. Not in my writable set.
  - **`_auth_fixtures.write_roster` / `ROSTER_FILENAME` are now DEAD** (roster retired, design §9 R12) —
    left in place (no live consumer; ruff-clean), safe for the builder to delete.
  - **Composition-coupling assumption (documented):** the recut hosted wire admits via
    `config.surreal` → the composed verifier's `PrincipalStore` (the natural composition root, since
    the AppContext is lifespan-built/stubbed). If the builder sources the verifier's stores
    otherwise, one harness line adjusts — the adversary's reference build settles it.
- **Packages considered:** fastmcp==3.4.7 (Middleware/RemoteAuthProvider/TokenVerifier/get_access_token/
  mcp.auth — USE-FRAMEWORK, read installed source); pydantic (config validation — USE); ipaddress
  stdlib (host_is_loopback — USE-STDLIB); lorerunes.is_blank (REUSE); httpx.MockTransport +
  `_surreal_harness`/`_refusal_effect`/`wire_session` (REUSE). Full detail → §Packages considered.
- **Reuse ledger:** 7 new reusable symbols/families, all dispositioned (§DRY ledger — HAND-ROLLED
  with the query that proves the search; EXTENDED `AuthConfig` + `hosted_auth_block`/`wire_session`
  recut in place — NO fork of the shared wire harness; verbatim-reused set listed).
- **Graded:** n/a (contract author, not a verdict-renderer) — authored at HEAD `feea77a` (SAME).
- decisions-needed: **none blocking** (ESC-1/ESC-2/MERGE all ruled #5123). Residual for the lead:
  prune `pending_contracts.yaml` `packet-39-pending-build` at commit (self-destructs — §Pending-bound
  discharge); flag `test_config.py:399` to the builder (corpse pin).
- gate receipts (HEAD `feea77a`, POST-revision-round-1): ruff **All checks passed** (full tree);
  typecheck **fully GREEN** every member (pending bound DISCHARGED 1→0); wave-2/3 set **90 collected
  / 0 errors → 49 RED / 41 GREEN** (+1 vs round 0 = the deny-by-default pin); the LOOPBACK consumer
  (`test_refusal_observes_effect`) **STAYS 7 passed / 1 skipped** (the lead's hard constraint —
  byte-identical to the cold-audit baseline); compose+transport **stub-RED preserved** (the C-DEF
  cred fix helps only the CORRECT build); no regressions (test_config **91✓**, migration
  **57p/4s✓**, test_mcp_server asgi/bearer/origin **5✓**, full tree **8233 collected**).
- receipt pointers: escalations+rulings → §Escalations; group map → §Plan; per-group pins+discrimination
  → §Pin inventory; the harness recut → §Harness recut; removed-behavior + corpse flag → §Removed-behavior
  notes; pending-bound → §Pending-bound discharge; DRY → §DRY ledger.
- **NEXT (lead):** the MANDATORY contract-adversary pass (standing law: contract → adversary → build)
  grades this contract + supplies the satisfiability receipt, THEN a builder.

---

## §Revision round 1 (adversary-39-w23 INSUFFICIENT #5130 → addressed; security boundary was SOLID)
The adversary graded the security boundary SOLID (every guard wrong-build caught, #295 EFFECT works)
and found 2 cheap fixes — both applied; nothing else changed (the guard/security pins are untouched).

- **#1 (C-DEF) — the compose-unit + transport fixtures now thread the test-store creds.** MEASURED:
  `SURREAL_USER`/`SURREAL_PASS`/`LORE_TEST_SURREAL_USER` are UNSET in this env, so on the CORRECT
  build the composed verifier's `PrincipalStore` (built FROM `config.surreal` at the composition root)
  `resolve_secret`'d to a KeyError → 10 pins unsatisfiable-as-shipped. FIX: ONE shared seam in
  `_auth_fixtures` — `surreal_block_for_test_store(env)` (points `config.surreal` at the test store,
  creds by the wire `*_env`) + `set_test_store_creds(monkeypatch)` (sets those to the
  `_surreal_harness` root creds, monkeypatch-restored). `recut_config` (compose-unit) + `_hosted_app`
  + the LAN transport pin point `config.surreal` at the test store; the two test files carry an
  autouse `_thread_test_store_creds` fixture. `wire_session` (already self-threading) was refactored
  onto the SAME `surreal_block_for_test_store` seam (DRY, no second copy). So the CORRECT build now
  resolves store creds WITHOUT externally-set env; the stub-RED state is UNCHANGED (verified below).
- **#2 (deny-by-default) — added the `readOnlyHint=None` pin.** `test_readonly_guard.py::
  TestReadOnlyGuardOnTheHostedWire::test_an_unclassified_tool_is_denied_by_default_for_a_hosted_member`:
  a synthetic tool with `readOnlyHint` UNSET (None) is refused AND invisible to a hosted member
  (partition keys on `readOnlyHint is not True`, server.py:10451). A hand-rolled `readOnlyHint is
  False` guard ADMITS it (None is not False) and passes every other enforcement pin — only this reds it.
- **OBSERVATION-A (RULED, note for the BUILDER — I do NOT build it):** the wave-1
  `loremaster/token_verifier.py::LoreTokenVerifier` is missing `super().__init__`; the wave-2/3 BUILD
  MAY add it (composition-correctness to wire into `FastMCP(auth=…)` — "frozen" governed the
  contract-phase pins, not integration adaptation). The builder re-runs the wave-1 contract
  (`test_token_verifier.py`) after to confirm it STAYS green (`super().__init__` must not change
  `verify_token` behaviour).
- **ESC-2 rider (#5126) — already satisfied, no change:** `OAuthProviderConfig` has `client_id`
  (required, feeds the #393 aud check), NO `client_secret`/`client_secret_env`, and `extra="forbid"`
  loudly refuses a stray inline secret.

Receipts (revised, at HEAD `feea77a`): ruff clean; wave-2/3 set **90 collected / 0 errors → 49 RED /
41 GREEN** (the +1 vs round 0 is the deny-by-default pin); the LOOPBACK consumer STAYS **7 passed /
1 skipped**; the compose+transport **stub-RED preserved** (8 RED — the cred fix helps only the
CORRECT build). A DELTA adversary pass follows (standing law).

## §Capability check (brief-base §4)
Everything the brief demanded is satisfiable EXCEPT one writable-set gap (ESC-1): the wire-driven
enforcement + transport-posture pins require the shared `wire_session` hosted harness recut, and
`_auth_fixtures.py` is not in my granted writable set. lore tools loaded via `ToolSearch "+lore"`;
`lore_comms` register/send work; the test store `ws://127.0.0.1:18000` is the admission substrate
(the wave-1 contract runs live against it). `Grep`/`Glob` are disabled session-wide — textual
sweeps use `grep`-in-`Bash` (said out loud). No other impossibility.

---

## §Escalations

> **✅ ALL RULED by the lead (`lore_comms` #5123, thread w23-contract):** ESC-1 GRANTED reading (A)
> — I recut `_auth_fixtures.py`'s hosted wire in place (no fork, loopback preserved). ESC-2 ruled
> **no-field** (my reading A — lore is a resource server holding no client_secret). JUDGMENT: **MERGE**
> confirmed. The forks below are kept for provenance; the resolution + receipts are §Harness recut +
> the wire-group pin inventory.

### ESC-1 — the hosted WIRE harness must be recut (BLOCKER for the enforcement+composition wire pins; writable-set + DRY)
`wire_session` + `hosted_auth_block` in `loremaster/tests/_auth_fixtures.py` still carry the
**STALE 2026-07-31 shape**: `hosted_auth_block` emits `mode: "google_oauth"` + a `google` block
with `resource_server_url` + `allowed_emails_file` (a flat-file roster via `write_roster`) — which
is INVALID under the recut `AuthConfig` (`mode: Literal["api_key","hosted_oauth"]`, `oauth` block,
`base_url`, `extra="forbid"`), and admits via a roster FILE, not the 48/49 `principal` table the
recut uses. The wave-1 contract author flagged this (E1, `REPORT-contract-39-w1.md`): wave 1 could
only retire orphaned entry points; the harness itself STAYS stale.

Every **#295 EFFECT** enforcement pin and every **transport-posture** pin (`.well-known`/401/
Origin/Host) MUST drive the REAL wire against the RECUT hosted app + principal-DB admission (the
#295 law is why a unit test is insufficient — WB48 passed a proxy pin while the body executed; and
`_auth_fixtures` notes the SDK auth branch is `pragma: no cover`). So the hosted wire harness needs:
(1) the recut config shape, (2) a principal created in the app's store (a unique test DB on
`ws://127.0.0.1:18000`, threaded through the config `surreal` block), (3) the tokeninfo spy
returning that principal's admitted payload, (4) `build_mcp_server(server, http_client=…)` +
`mcp._token_verifier` (the composition seam this wave builds).

Two options, both needing a ruling because `_auth_fixtures.py` is outside my writable set and
`wire_session` is the SHARED SDK-client-over-ASGI wire harness (ONE-IMPLEMENTATION law forbids a
fork — a second copy in a new fixtures module is copy #2):
- **(A, recommended)** grant me `_auth_fixtures.py` (the hosted branch of `wire_session` +
  `hosted_auth_block` + the roster→principal-DB swap) to recut to the resource-server model.
  Keeps ONE wire harness; the loopback path (the GREEN #295 instrument) is untouched.
- **(B)** assign the harness recut to a separate owner/task; I consume it.

**Without ESC-1** I can author ~5 of 7 groups now (config, removed-behavior, posture-derivation,
unit-composition, unit-enforcement/coverage); the wire-driven #295 EFFECT + transport-posture pins
wait on the harness.

### ESC-2 — `client_secret` config representation (design fork; I pin the no-field reading)
Design §6 shows `client_secret` as a COMMENT ("env-ref only, resolved at composition root — NEVER
inline"), NOT a field on `OAuthProviderConfig`. And the wave-1 hand-rolled tokeninfo verifier needs
NO client_secret at all (lore is a RESOURCE SERVER; the tokeninfo POST validates with just the
access_token — `LoreTokenVerifier.__init__` takes no secret). Two readings:
- **(A, recommended)** NO `client_secret` field; "never inline" = `OAuthProviderConfig`
  (`extra="forbid"`) REFUSES an inline `client_secret` key (ValidationError). Strongest form (the
  secret cannot even be NAMED in lore's config), and consistent with the secret-less wave-1 build.
- **(B)** a `client_secret_env: str` field (env-var NAME, lore's `*_env` idiom) — but the secret
  would be configured-and-unused in packet 39.
I pin **(A)** and flag; the flip to (B) is one field + one pin.

### JUDGMENT — merge vs split
Recommend **MERGE** (one wave), conditional on ESC-1. The 7 groups are tightly coupled
(composition installs the enforcement middleware; posture/config feed it; removed-behavior IS the
config/auth deletion), so a split creates artificial seams on the SAME files (server.py, config.py,
auth.py, the wire harness) — worse than merging. The contract is gradeable per-group (each group has
its own fixtures + discrimination rationale), so size does not defeat the adversary; only shallowness
would, and I have the budget to pin each rigorously. **Fallback if ESC-1 → (B)/deferred:** split
harness-INDEPENDENT (config / removed-behavior / posture-derivation / unit-composition /
unit-enforcement) now, harness-DEPENDENT (enforce-wire / posture-wire) after the harness owner
recuts `wire_session`.

---

## §Plan — group map (§13 groups, HEEDING the READ-ONLY-hosted banner: NO role-axis write)

Harness-INDEPENDENT (unblocked — authoring now):
- **G-CONFIG** (§6/§13 g6): `OAuthProviderConfig` + recut `AuthConfig` (pydantic, `extra="forbid"`).
  R2: blank/whitespace `client_id` refused; `base_url` https-only; `client_secret` not-inline
  (ESC-2 reading A). Positive controls.
- **G-REMOVED** (#395 + §9): DELETE-absence pins for `BearerAuthMiddleware`/`AuthVerifier`
  (not-importable + not-in-`__all__`) + kept-names control; `tls_terminated_upstream` retirement
  (not-a-field + fails-to-load + message-names-field-AND-fix + clean-config control). → `test_auth.py`.
- **G-POSTURE-DERIVE** (§6/§13 g5): the `derive_posture` pure function (LOOPBACK/LAN_BEARER/
  HOSTED_OAUTH + typed refusal on an incoherent posture, naming nearest+fix) + `host_is_loopback`
  127/8 grid + fail-closed on exception. → `lorerunes`.
- **G-COMPOSE-UNIT** (§8): `build_mcp_server` gains `http_client` kwarg (discharges the pending
  bound `_auth_fixtures.py:759`); `FastMCP(auth=…)` wired per posture; `ReadOnlyGuardMiddleware`
  installed. Assembled in-process (no full wire).
- **G-ENFORCE-UNIT** (§7/§13 g4): the readOnlyHint partition → coverage-as-checked-variable
  (registry == guard's observed set; a new unguarded mutating tool reds); one-annotation-flip feeds
  guard+list+render.

Harness-DEPENDENT (ESC-1 GRANTED → BUILT via the `_auth_fixtures.py` recut — §Harness recut):
- **G-ENFORCE-WIRE** (§7/§13 g4): #295 EFFECT — a mutating tool refused AND body-not-run for a
  hosted principal (NO role axis — every hosted principal is read-only) via
  `assert_tool_refused_and_did_not_run`; positive control = a read-only tool visible AND its body
  runs; one-annotation-flip; loopback full surface; `served ∩ refused = ∅` on the wire.
- **G-POSTURE-WIRE** (§13 g5): `.well-known` 200 anonymous in HOSTED_OAUTH / absent in LAN_BEARER;
  401 carries `resource_metadata=`; disallowed Origin → 403 ZERO outbound; wrong Host refused.

(All seven groups authored — per-group RED/GREEN receipts below.)

## §Pin inventory (grows per group; RED/GREEN receipts at the base sha)

### G-CONFIG — `loremaster/tests/test_auth_config_recut.py` (R2 re-pin) — **RED confirmed** (5 fail / 8 pass)
Stub: `OAuthProviderConfig` + recut `AuthConfig` fields in `config.py` (validators absent → behavioural RED).
| pin | asserts | discriminates against | state |
|---|---|---|---|
| `test_a_wellformed_provider_block_constructs` | valid block constructs | POSITIVE CONTROL | GREEN |
| `test_blank_client_id_is_refused` | `client_id=""` → ValidationError | no non-blank validator | RED |
| `test_whitespace_only_client_id_is_refused` | `client_id="   "` → ValidationError | a bare `if not client_id` (a space is truthy) — forces `lorerunes.is_blank` | RED |
| `test_client_secret_cannot_be_inlined` | inline `client_secret` refused (extra="forbid") | ESC-2(B): a build that added a client_secret field | GREEN-now guard (RED if a secret field is added) |
| `test_an_unknown_provider_key_is_refused` | stray key refused | extra="forbid" control (≠ the client_secret key) | GREEN-now guard |
| `test_provider_kind_is_a_closed_domain` | `kind="azure"` refused | `kind: str` (dead posture accepted) | GREEN-now guard |
| `test_https_base_url_is_accepted` | https base_url constructs | POSITIVE CONTROL | GREEN |
| `test_http_base_url_is_refused` | `http://` refused | no scheme validator | RED |
| `test_a_non_https_scheme_base_url_is_refused` | `ws://` refused | a `not startswith("http://")` guard (ws passes) — forces positive https check | RED |
| `test_a_non_url_base_url_is_refused` | schemeless refused | a value silently advertised as-is | RED |
| `test_a_bare_api_key_auth_block_still_validates` | DUAL: existing LAN config validates, mode defaults api_key | a rewrite dropping backward-compat | GREEN |
| `test_mode_is_a_closed_domain` | stale `"google_oauth"` mode refused | `mode: str` | GREEN-now guard |
| `test_allowed_origins_carries_the_configured_extra_origins` | allowed_origins round-trips | a build dropping the field | GREEN |

### G-REMOVED — `loremaster/tests/test_auth.py` (finding #395 re-cut) — **RED confirmed** (7 fail / 26 pass — the exact #395 node names)
No stub (contract-first via the still-present symbols/field). `TestKeptAuthSurfaceIsExported` is the indispensable CONTROL.
| pin | asserts | state |
|---|---|---|
| `TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_importable_from_loremaster_auth[BearerAuthMiddleware\|AuthVerifier]` | `not hasattr(auth, name)` | RED (×2) |
| `TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_exported[BearerAuthMiddleware\|AuthVerifier]` | `name not in auth.__all__` | RED (×2) |
| `TestAuthConfigRetiresTlsTerminatedUpstream::test_the_retired_field_is_not_a_model_field` | not in `AuthConfig.model_fields` | RED |
| `…::test_a_config_still_carrying_the_retired_flag_fails_to_load` | a config with the flag → ValidationError | RED |
| `…::test_the_failure_names_the_retired_field_and_the_fix` | message names field AND fix (remove/delete) — not the bare extra="forbid" | RED |
| `…::test_a_clean_config_without_the_flag_still_loads` | POSITIVE CONTROL — clean config loads | GREEN |
| `TestKeptAuthSurfaceIsExported` (kept) | ApiKeyVerifier/OriginValidationMiddleware/build_api_key_verifier stay exported | GREEN (the control) |

⚠ DUAL-law corpse pin: **`loremaster/tests/test_config.py::TestAuthConfig::test_tls_terminated_upstream_flag_defaults_true`** (line 399) certifies the OLD world — it errors on the deleted attribute. **The builder MUST retire it in the same GREEN commit that removes the field.** (Not in my writable set; flagged here.)

### G-POSTURE-DERIVE — `lorerunes/tests/test_posture.py` (design §6) — **RED confirmed** (24 fail / 1 pass)
Stub: `lorerunes/lorerunes/posture.py` (`Posture`/`PostureError` real; `host_is_loopback`/`derive_posture` raise NotImplementedError).
- `TestHostIsLoopback`: 127/8 GRID true (incl. 127.0.0.2 / 127.255.255.254 — vs a spellings set); LAN/public/`0.0.0.0`/hostnames false; malformed FAIL-CLOSED false (incl. `127.0.0.1.evil.com` / `127.0.0.1extra` vs `startswith("127.")`; `localhost.evil.com` vs substring) — RED.
- `TestDerivePostureCoherent`: LOOPBACK / LAN_BEARER (host-agnostic) / HOSTED_OAUTH each FORCED — RED.
- `TestDerivePostureRefusesIncoherent`: hosted-no-oauth / hosted-non-loopback / disabled-non-loopback → PostureError naming the nearest posture (from the enum) + the field — vs a silent-default build — RED.
- `TestPostureEnumIsAClosedDomain`: exactly {LOOPBACK, LAN_BEARER, HOSTED_OAUTH} — GREEN-now guard.

### G-COMPOSE-UNIT — `loremaster/tests/test_auth_composition_recut.py` (design §8) — **RED confirmed** (4 fail / 2 pass)
Stubs: `build_mcp_server` gains `http_client` kwarg (server.py — DISCHARGES the pending bound); `ReadOnlyGuardMiddleware` (readonly_guard.py). Harness-light: assembles the composed mcp in-process via `_recut_auth_fixtures.build_composed_mcp`, inspects `mcp.auth` / `mcp.middleware` (no wire, no store connect).
| pin | asserts | discriminates against | state |
|---|---|---|---|
| `test_the_injected_http_client_param_exists` | `build_mcp_server(…, http_client=…)` no TypeError | a build dropping the param (reintroduces the pending mypy error) | GREEN-now guard (discharges bound) |
| `test_hosted_wires_the_lore_token_verifier_as_the_fastmcp_auth` | hosted `mcp.auth` reachable, wraps a LoreTokenVerifier | stub (auth None) / a non-lore verifier | RED |
| `test_hosted_auth_is_a_remote_auth_provider_advertising_authorization_servers` | hosted `mcp.auth` is a `RemoteAuthProvider` (serves .well-known) | wiring a bare TokenVerifier hosted (no .well-known → connector can't discover) | RED |
| `test_hosted_installs_the_read_only_guard_middleware` | `ReadOnlyGuardMiddleware` in hosted `mcp.middleware` | composing hosted auth without the guard (banner violated) | RED |
| `test_lan_bearer_wires_a_bare_token_verifier_not_a_remote_auth_provider` | LAN `mcp.auth` is a bare LoreTokenVerifier, NOT RemoteAuthProvider | auth None (no LAN gate) / a RemoteAuthProvider (wrong .well-known) | RED |
| `test_loopback_installs_no_auth_provider` | loopback `mcp.auth is None` | over-wiring auth on loopback (breaks local sessions) | GREEN-now guard |

### G-ENFORCE-UNIT — `loremaster/tests/test_readonly_guard.py` (design §7) — **GREEN-now structural guards** (2 pass)
Partition CLASSIFICATION is already pinned (`test_mutating_set_derivation.py` / `test_tool_allowlist.py` / `test_mcp_server.py`) — NOT duplicated. The NEW packet-39 obligation is the GUARD, whose substance is wire-level (§G-ENFORCE-WIRE below).
| pin | asserts | discriminates against | state |
|---|---|---|---|
| `test_the_guard_is_a_fastmcp_middleware` | `issubclass(ReadOnlyGuardMiddleware, Middleware)` | an ASGI wrapper / plain class (never invoked by fastmcp dispatch) | GREEN-now guard |
| `test_the_guard_overrides_both_the_list_and_call_hooks` | both `on_list_tools` + `on_call_tool` in the class dict | a guard overriding only `on_call_tool` (refuses a call but leaves mutating tools VISIBLE — the #295 structural-leg omission) | GREEN-now guard |

---

### G-POSTURE-WIRE — `loremaster/tests/test_auth_composition_wire.py` (§13 g5) — **RED confirmed** (4 fail / 1 pass)
Transport posture on the ASSEMBLED app, driven by raw-ASGI anonymous `drive()` (no SDK session, no principal) → clean behavioural-RED against the stub (the pre-recut `build_asgi_app` 401s every anonymous request via BearerAuthMiddleware + serves no RFC 9728 metadata).
| pin | asserts | discriminates against | state |
|---|---|---|---|
| `test_wellknown_is_served_200_and_anonymous` | GET `.well-known/oauth-protected-resource/mcp` (no bearer) → 200 | BearerAuthMiddleware-gated (401) / unrouted (404) | RED (got 401) |
| `test_unauthenticated_post_401_carries_resource_metadata` | unauth POST /mcp → 401 with `resource_metadata=` (RFC 9728) | the hand-rolled `Bearer realm="loremaster"` 401 (no resource_metadata) | RED |
| `test_disallowed_origin_is_403_with_zero_outbound_provider_calls` | hostile Origin → 403 AND tokeninfo spy `call_count==0` | BearerAuthMiddleware OUTERMOST (401s no-bearer first) — proves Origin-outermost + zero-outbound | RED (got 401) |
| `test_wrong_host_is_refused` | non-allowlisted Host → ≥400 (native `host_origin_protection`) | a build that turns host_origin_protection off | GREEN-now guard |
| `test_wellknown_is_absent_in_lan_bearer` | LAN GET `.well-known` → 404 (no AS to advertise) | a LAN deploy advertising a .well-known it can't honour | RED (got 401) |

### G-ENFORCE-WIRE — `loremaster/tests/test_readonly_guard.py` (§13 g4, #295 EFFECT) — **RED confirmed** (4 fail / +loopback pass)
Drive the RECUT hosted `wire_session` (real member admitted against a throwaway principal DB) + a SYNTHETIC mutating tool + the shared `_refusal_effect.assert_tool_refused_and_did_not_run` helper. ⚠ ERROR-RED against the stub: the hosted `initialize` 401s (the composition's `FastMCP(auth=…)` is unwired + `build_asgi_app` still ships BearerAuthMiddleware — builder GREEN work), so the wire fails to establish → GREEN once the composition authenticates the member AND the guard refuses. NO role axis (banner) — every hosted principal is read-only.
| pin | asserts | discriminates against | state |
|---|---|---|---|
| `test_a_hosted_mutating_tool_is_refused_and_its_body_never_runs` | a synthetic mutating tool refused AND `effect_count()==0` (body never ran) | WB48 (run-then-refuse, identical text, counter==1) AND a hand-list reach (a synthetic tool ≠ the 6 built-ins → still refused = reach DERIVED from the registry) | RED (401) |
| `test_served_intersection_refused_is_empty_for_a_hosted_member` | synthetic mutating INVISIBLE, synthetic read-only VISIBLE (served∩refused=∅) | a guard that refuses calls but doesn't filter the list (#295 structural leg) | RED (401) |
| `test_a_read_only_tool_is_visible_and_its_body_runs` | POSITIVE CONTROL: read-only tool visible + body runs (harness sees execution) | a guard that over-refuses read-only tools | RED (401) |
| `test_one_annotation_flip_moves_a_tool_across_guard_and_list` | SAME name visible+runs (read-only) vs invisible (mutating) — one partition feeds guard+list | a guard/list keyed on two sources | RED (401) |
| `test_loopback_has_the_full_surface` | loopback (no principal) → mutating tool visible + body runs (guard is a NO-OP) | a guard that refuses when `get_access_token()` is None (breaks every local session) | GREEN-now guard |

⚠ **DROPPED (with reason, per the ban on silent narrowing):** a LAN-api-key-full-surface WIRE pin.
Its api-key MECHANISM differs stub-vs-build (stub: `config.keys` + BearerAuthMiddleware; build:
`PrincipalKeyStore.verify` of a `<name:secret>` credential), so one pin cannot be RED-against-stub
AND GREEN-at-build. LAN full-write is pinned at the VERIFIER level in wave-1
(`test_token_verifier.py::test_api_key_principal_keeps_full_write`); the GUARD's respect for
`lore:write` is exercised by the loopback no-op guard + the member-refused pins. If the lead wants a
dedicated LAN-guard wire pin, it needs a minted `PrincipalKeyStore` credential — flagged, not silently skipped.

---

## §Harness recut (ESC-1 GRANTED, reading A) — `_auth_fixtures.py`, NO fork, loopback preserved
- **`hosted_auth_block`** recut to the standalone shape (mode `hosted_oauth`, `oauth` block,
  `base_url`, `allowed_origins`; NO `mode: google_oauth` / `resource_server_url` / `allowed_emails_file`
  roster). `client_secret` absent (ESC-2 A).
- **`wire_session`** hosted branch: REAL principal-DB admission (design §9 R12) — a UNIQUE throwaway
  test DB on `ws://127.0.0.1:18000` threaded through `config.surreal`, an admitted member `principal`
  pre-created there (by email, subject unbound → the verifier binds the Google sub on first login),
  the tokeninfo spy returning its `admitted_payload`, `LORE_ALLOWED_HOSTS` set for the proxied Host;
  cleanup drops the DB + restores env. Refactored into `_open_hosted_wire_admission` /
  `_force_wire_verdict` / `_tokeninfo_spy_for` / `_wire_client_params` helpers (PLR complexity gates).
- **verdict seam recut:** `mcp.auth.token_verifier` (hosted) / `mcp.auth` (LAN), replacing the retired
  `mcp._token_verifier` — a no-op until the composition wires auth.
- **NO FORK:** the ONE shared wire harness is edited in place; `_recut_auth_fixtures.build_composed_mcp`
  reuses `_auth_fixtures.hosted_auth_block` (the earlier duplicate `recut_hosted_auth_block` removed).
- **Loopback + LAN branches UNCHANGED.** RECEIPT: `test_refusal_observes_effect` (the live GREEN #295
  instrument, loopback) STAYS **7 passed / 1 skipped** — byte-identical to the cold-audit baseline.
- **`write_roster` / `ROSTER_FILENAME` now DEAD** (roster retired) — left in place, ruff-clean, safe
  for the builder to delete.

---

## §Removed-behavior notes + the DUAL-law corpse flag
- **`BearerAuthMiddleware` + `AuthVerifier`** deleted from `auth.py` (design §9): absence pins in
  `test_auth.py::TestRetiredAuthSurfaceIsGone` (RED). **KEPT** (control + design §8): `ApiKeyVerifier`,
  `OriginValidationMiddleware`, `build_api_key_verifier` — `TestKeptAuthSurfaceIsExported` (GREEN).
  ⚠ `build_api_key_verifier`/`ApiKeyVerifier`/`config.keys` are KEPT but the recut auth path routes
  api-keys through `PrincipalKeyStore.verify` (wave-1), so they may become orphaned — a builder/lead
  disposition, flagged (not a contract pin).
- **`tls_terminated_upstream`** retired (design §9): `test_auth.py::TestAuthConfigRetiresTlsTerminatedUpstream`
  (not-a-field / fails-to-load / message-names-field-AND-fix / clean-config control) — RED.
  ⚠ **DUAL-law corpse pin: `loremaster/tests/test_config.py::TestAuthConfig::test_tls_terminated_upstream_flag_defaults_true`**
  (line 399) asserts `config.auth.tls_terminated_upstream is True` — it certifies the OLD world and
  ERRORS (AttributeError) the moment the builder removes the field. **The builder MUST retire it in
  the same GREEN commit that removes the field.** Not in my writable set; flagged here per the
  rename-sweep law ("grep the test tree for assertions pinning retired names/strings").

## §Pending-bound discharge (`_auth_fixtures.py:759`)
Adding `http_client` to `build_mcp_server` cleared the mypy error `Unexpected keyword argument
"http_client"` — MEASURED gone (`uv run mypy loremaster/tests/_auth_fixtures.py` → 0 occurrences).
The `scripts/pending_contracts.yaml` `packet-39-pending-build` bound (its sole remaining `files:`
entry) now SELF-DESTRUCTS (its premise — the error — is gone), so the currency gate will flag it
RED_ORPHANED. **→ LEAD:** prune that entry at commit (registry-owned; the cold audit routed the same
prune-at-commit as R1). This is the instrument working, not a defect.

## §DRY ledger (new reusable symbols)
| new symbol | lore query / read | returned | disposition |
|---|---|---|---|
| `OAuthProviderConfig` (config model) | `lore_search`/grep "GoogleOAuthConfig"/oauth config | the old `GoogleOAuthConfig` is retired (archived §9); no live oauth config model | HAND-ROLLED (design §6 mandates; extra="forbid" from `_StrictModel`) |
| `AuthConfig` recut fields (mode/oauth/base_url/allowed_origins) | read `config.py` AuthConfig | the live AuthConfig (enabled/keys/tls…) | EXTENDED `loremaster.config.AuthConfig` |
| `Posture`/`PostureError`/`derive_posture`/`host_is_loopback` (lorerunes.posture) | scout map + grep (wholly unbuilt); archived `lorerunes/test_posture.py` used retired scope names | none live | HAND-ROLLED (recut, design §6; `host_is_loopback` REUSES stdlib `ipaddress` — no hand-rolled IP parsing) |
| `ReadOnlyGuardMiddleware` (loremaster.readonly_guard) | scout map (wholly unbuilt) | none | HAND-ROLLED; subclasses fastmcp `Middleware` (framework base REUSED); its derivation source is the existing `partition_tools_by_posture` (REUSED — not a second partition) |
| `recut_config`/`build_composed_mcp` (`_recut_auth_fixtures.py`, compose-unit) | read `_auth_fixtures.hosted_auth_block` | the shared recut config blocks | REUSES `_auth_fixtures.hosted_auth_block`/`lan_bearer_auth_block`/`base_config_payload` (the earlier duplicate `recut_hosted_auth_block` was REMOVED — no fork) |
| `_open_hosted_wire_admission`/`_force_wire_verdict`/`_tokeninfo_spy_for`/`_wire_client_params` (`_auth_fixtures.py`) | recut of `wire_session` in place | the stale hosted branch (roster + `mcp._token_verifier`) | EXTENDED the shared `wire_session` IN PLACE (no fork — ESC-1 A); helpers extracted to satisfy the PLR complexity gates; REUSE `_surreal_harness.{make_env,connect_admin,drop_database,unique_database,PRODUCTION_DIM}` + `PrincipalStore` |
| `hosted_auth_block` recut (`_auth_fixtures.py`) | in-place recut | the stale 2026-07-31 shape | EXTENDED in place (recut to the standalone shape; drops the roster) |

Reused verbatim (no new symbol): `partition_tools_by_posture`, `lorerunes.is_blank` (builder — the client_id blank check), `_auth_fixtures.{base_config_payload,GOOGLE_CLIENT_ID,GOOGLE_EMAIL_SCOPE_URI,RESOURCE_SERVER_URL,CLAUDE_AI_ORIGIN,slug,drive,running_asgi_app,stub_heavy_startup,TokeninfoSpy,WELL_KNOWN_PATH,json_rpc_initialize,…}`, `_surreal_harness.*` (the store harness — reused, not cloned), `_refusal_effect.assert_tool_refused_and_did_not_run` (the #295 helper, consumed by the enforce-wire pins), `PrincipalStore`, fastmcp `Middleware`/`RemoteAuthProvider`/`TokenVerifier`/`get_access_token`, `httpx.MockTransport`.

## §Packages considered
- **fastmcp==3.4.7** — `Middleware` base (ReadOnlyGuardMiddleware), `RemoteAuthProvider`/`TokenVerifier`
  (composition type checks), `get_access_token` (the guard's ambient-principal read — builder), `mcp.auth`
  (the composition seam) — **USE-FRAMEWORK** (read installed source via the scout map §5/§7/§8 +
  `.venv/.../fastmcp/server/{middleware/middleware.py,auth/auth.py,dependencies.py}`).
- **pydantic** — `OAuthProviderConfig`/`AuthConfig` validation — **USE** (`extra="forbid"` via `_StrictModel`; the fail-closed validators are builder GREEN work).
- **ipaddress (stdlib)** — `host_is_loopback` — **USE-STDLIB** (`ip_address(host).is_loopback` — no hand-rolled IP parsing; design R15).
- **lorerunes.is_blank** — the blank-client_id check (builder) — **REUSE** (the ONE blankness rule, shared with `resolve_secret`).
- **httpx.MockTransport** — the composition-unit `http_client` sentinel — **REUSE** (already a dep).
