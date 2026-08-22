# REPORT — builder-39-w1 (packet 39 RE-CUT, wave-1 builder)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done-with-deviations** — wave-1 contract GREEN (40 RED → 44 passed); normaliser GREEN (21 RED → 22 passed); production mypy delta zero-new; ruff clean; mypy baseline REDUCED 141 → 50 by archiving 6 wholesale-stale SDK-FastMCP tests. 4 escalations (none blocks the build).
- deviations:
  - E1 scope is MATERIALLY LARGER than the brief's 4-file enumeration: I archived 6 wholesale-stale loremaster tests; `test_auth.py` (keeper-extraction) + `_auth_fixtures.py` (part-retirement) + `lorerunes/tests/test_posture.py`/`test_roster_parser.py` (never-built OLD-design symbols) remain — see §Escalations E1a–E1c.
  - The FROZEN wave-1 contract `test_token_verifier.py` adds 40 `no-untyped-def` mypy errors (unannotated fixture params); I may not edit a frozen test — see §Escalations E1d.
  - Put the scope constants + `role → capability` FUNCTIONS in `lorerunes` (design §3.5 ruled home), not just `normalize_email` — the design rules that home for the wave-2 guard + wave-3 renderer to reuse (§DRY ledger).
- **Packages considered:** `cachetools.TTLCache` (7.1.6, declared dep) → **replace** (the verdict cache, design §4.2 — READ the installed generic `TTLCache(maxsize, ttl, timer=)` signature); `fastmcp==3.4.7` `TokenVerifier`/`AccessToken` → **replace/use-framework** (base + mint — READ `AccessToken.model_fields`: token/client_id/scopes:list[str]/expires_at:int|None/subject/claims:required); `fastmcp` `GoogleTokenVerifier` → **bespoke** (hand-rolled Google authN, #393 — READ `.venv/.../providers/google.py`, confirmed by contract author + adversary); `httpx` (dep) → **reuse** (injected client, token in POST body); `unicodedata` (stdlib) → **reuse** (NFKC in the normaliser, not hand-rolled); `hashlib` → **rejected**, reused `loremaster.index.records.sha512_hex` for the cache key (#102/#120 DRY law).
- **Reuse ledger:** 5 new reusable symbols (all in `lorerunes`), all dispositioned (§DRY ledger). Reused: `PrincipalKeyStore.verify`, `PrincipalStore.{get_by_subject,get_by_email,set_subject}`, `sha512_hex`, `cachetools.TTLCache`, `_PRINCIPAL_STATUS_ACTIVE`, fastmcp `TokenVerifier`/`AccessToken`.
- **Graded:** `50fb230` · HEAD-at-report: `50fb230` · **SAME** (base I built at; contract files untracked/frozen, unchanged).
- decisions-needed (escalations, durable in §Escalations; none blocks the build):
  - **E1a** — `test_auth.py` keeper-extraction (ApiKeyVerifier pins KEEP; retired `LoreTokenVerifier`/`GoogleOAuthConfig` pins archive) is a content edit beyond `git mv`.
  - **E1b** — `_auth_fixtures.py` model-specific part-retirement (must STAY: the live fresh contract imports its model-agnostic core) — the contract author flagged this a lead fork.
  - **E1c** — `lorerunes/tests/test_posture.py` + `test_roster_parser.py`: additional stale OLD-design tests (never-built `Posture`/`derive_posture`/`SCOPE_READ`/roster) — archive-vs-recut is a lead call (posture is KEPT in fresh design §6).
  - **E1d** — the FROZEN contract `test_token_verifier.py` violates the repo's mypy test convention (`param: Any`), adding 40 `no-untyped-def` errors I cannot fix without editing a frozen test.
- receipt pointers: RED→GREEN → §Receipts; DRY → §DRY ledger; removed-behavior (E1) → §Removed-behavior inventory; removed-name sweep → §Removed-name sweep; mutation proofs → §Mutation proofs; escalations → §Escalations.

---

## What changed (file:line)

### Production (zero-new mypy; ruff clean)
- **`loremaster/loremaster/token_verifier.py`** — implemented `LoreTokenVerifier.verify_token` + the private helpers (the stub's `__init__` shape + `agent_of` preserved verbatim). Two branches in order (design §4.1): the api-key branch (`_mint_api_key_identity`, routes `PrincipalKeyStore.verify`, #206 per-principal mint, LAN full-write), then the Google branch (`_verified_identity` → `_admit` → `_mint_google_identity`, READ-ONLY hosted). Hand-rolled Google tokeninfo (`_call_tokeninfo`: token in POST **body**, `aud == client_id`, email-scope subset, sub extraction, absolute `expires_at` via `_absolute_expiry`, string/bool `email_verified` via `_is_verified`). Verdict cache = `cachetools.TTLCache` keyed by `sha512_hex(token)`, split negative caching (400/401 → negative-cache; 5xx/transport/malformed → deny-not-cached), positive entries re-checked against the injected clock. Admission (`_admit`) is NEVER cached — re-run against the live `principal` table every request.
- **`lorerunes/lorerunes/email_normalisation.py`** (NEW) — `normalize_email = NFKC → casefold → strip` (design §3.4/§5), stdlib-only.
- **`lorerunes/lorerunes/scopes.py`** (NEW) — `LORE_READ`/`LORE_WRITE` constants + `hosted_scopes_for_role`/`lan_scopes_for_role` (design §3.5; `role → capability` FUNCTIONS, packet-39 read-only-hosted / LAN-full-write).
- **`lorerunes/lorerunes/__init__.py`** — re-export the 5 new symbols at package level (house idiom).

### E1 archival (git mv, staged, NOT committed)
- 6 wholesale-stale SDK-FastMCP tests `git mv`'d to `docs/plans/v2/receipts/2026-08-21-packet39-recut/` — see §Removed-behavior inventory.

## Receipts (RED→GREEN, at `50fb230` working tree)
- **Wave-1 verifier contract** (`test_token_verifier.py` + `test_oauth_identity_seam.py`): RED baseline **40 failed / 4 passed** → after build **44 passed / 0 failed** (`-n auto`, live store `ws://127.0.0.1:18000`). The 4 previously-green are the 3 seam PIN-THE-MISS pins + the `agent_of` unit.
- **Normaliser** (`lorerunes/tests/test_email_normalisation.py`): RED baseline **21 failed / 1 passed** → **22 passed / 0 failed**.
- **Ruff:** `uv run ruff check .` → **All checks passed!**
- **Typecheck** (`scripts/typecheck.sh`, mypy):
  - My 4 production files checked in isolation → **Success: no issues found in 4 source files** (zero-new production delta).
  - loremaster leg baseline was **141 errors in 9 files**; after the 6-file archival → **50 errors in 3 files** (91 removed). Residual 50 = 40 frozen-contract `no-untyped-def` (E1d) + 7 `test_auth.py` stale (E1a) + 3 `_auth_fixtures.py` stale (E1b). None in production; none newly introduced by my production code. (Typecheck is the ADJUDICATED packet-39 #333 auth-WIP red per CLAUDE.md; I REDUCED it, not worsened it.)
- **Changed / structural suites** (`-n auto`, live store):
  - lorerunes smoke + normalisation → **23 passed**.
  - `test_principals_store` + `test_principal_keys_store` + `test_principals_schema` + `test_principal_keys_schema` + `test_retry_seam` (the `_query` seam scan) + `test_retired_symbols` (retired-symbol hygiene pin) + `test_auth.py::TestApiKeyVerifierIsPreservedVerbatim` (the ApiKeyVerifier keepers E1 preserves) → **785 passed**.
  - Full `loremaster/tests` **collect-only** → **8232 tests collected, 0 collection errors** (the archival orphaned nothing).

## DRY ledger (new reusable symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `lorerunes.normalize_email` | `lore_search` "email normaliser" + read `lorerunes/lorerunes/`; the contract pre-contracted it (`test_email_normalisation.py`) | no impl existed (`__init__` exported only `is_blank`) | **HAND-ROLLED** (design §5 ruled `NFKC→casefold→strip`, stdlib `unicodedata` — REUSES the stdlib fold, not a hand-rolled Unicode table) |
| `lorerunes.LORE_READ` / `LORE_WRITE` | design §3.5 (ruled home); read `lorerunes/` | absent | **HAND-ROLLED** (wire scope constants; §3.5 rules ONE home so the verifier/guard/renderer cannot drift) |
| `lorerunes.hosted_scopes_for_role` | design §3.5/§ADD | absent | **HAND-ROLLED** (`role → capability` FUNCTION; packet-39 `{lore:read}` ∀ role — the anti-premature-RBAC seam; mutation-proven, §Mutation proofs) |
| `lorerunes.lan_scopes_for_role` | design §3.3/§3.5 (banner "LAN keeps full write") | absent | **HAND-ROLLED** (`role → capability` FUNCTION; packet-39 `{lore:read, lore:write}` ∀ role, F7 deferred to RBAC) |

Reused verbatim (no new symbol, with proving note):
- `PrincipalKeyStore.verify` — the #206 api-key resolution. **Proven** by the contract's `test_api_key_branch_routes_through_principal_key_store_verify` (monkeypatch `verify`→None ⇒ api-key auth denies): GREEN.
- `PrincipalStore.{get_by_subject,get_by_email,set_subject}` — admission + fill-on-login (design §3.2). GREEN across `TestAdmission`.
- `loremaster.index.records.sha512_hex` — the verdict-cache key. Reused rather than a hand-rolled `hashlib.sha512(...).hexdigest()` (the #102/#120 clone the DRY law forbids).
- `cachetools.TTLCache` — the verdict cache (design §4.2), not a hand-rolled dict-with-timestamps.
- `loremaster.store.surreal_schema._PRINCIPAL_STATUS_ACTIVE` — the active-status literal (house idiom: `principals.py`/`principal_keys.py` import this same private constant).
- `fastmcp.server.auth.{TokenVerifier,AccessToken}` — the framework base + minted identity.

The verifier's other new members (`_verified_identity`, `_admit`, `_call_tokeninfo`, `_absolute_expiry`, `_is_verified`, `_client`, `_cache_get`, `_cache_put`, `_mint_*`) are PRIVATE to the verifier (not cross-caller policy) — no shared-home question; kept local.

## Mutation proofs (load-bearing shared seams — `scripts/mutation_proof.py`, declared-RED diffed both ways, byte-exact restore)
1. **Shared normaliser routing** — mutated `lorerunes.normalize_email` body → `return value` (identity). Declared RED: `test_email_normalisation.py::...::test_mixed_case_address_folds_to_lowercase` AND `test_token_verifier.py::TestAdmission::test_admission_normalisation_matches_a_lowercase_stored_principal`. **PROOF HELD — the declared set fired EXACTLY** (both red). One mutation to the ONE lorerunes symbol reddens BOTH a lorerunes unit pin AND a loremaster admission pin ⇒ the admission path genuinely CALLS the shared symbol (not a private copy). Restored byte-exact (md5 `bed6205a…`).
2. **`role → capability` is a real function (anti-premature-RBAC)** — mutated `hosted_scopes_for_role` to `return frozenset({LORE_READ, LORE_WRITE}) if role == "admin" else frozenset({LORE_READ})` (the hardcoded `admin ⇒ +write` DEFECT). Declared RED: `test_hosted_admin_is_ALSO_read_only_regardless_of_role`. **PROOF HELD** — that pin reddened (`{lore:read, lore:write} != {lore:read}`) while `test_hosted_member_gets_read_only_scope` stayed GREEN (targeted control). Restored byte-exact (md5 `b216543a…`).

## Removed-behavior inventory (E1 — each file adjudicated; "the old code did it" BANNED)
The stale 2026-07-31 SDK-FastMCP contract (`docs/design/2026-07-31-packet39-google-oauth.md`) certifies a DEAD world (mcp-SDK `FastMCP`, R12 flat-file roster, the old `LoreTokenVerifier` in `auth.py`) superseded by the recut design §9 (R10–R16 adjudications) and my fresh contract. Adjudication:

| file | verdict | why (the property that governs) |
|---|---|---|
| `test_auth_composition.py` | **ARCHIVED** | SDK `mcp` 1.27.2 composition + `derive_edge_policy`; composition = wave 3; recut §2/§8 rewrote it onto standalone fastmcp |
| `test_auth_identity_seam.py` | **ARCHIVED** | SDK `StreamableHTTPSessionManager` internals + `lorerunes.Posture`; §9 R16 DROPPED the wire-shadow class it guards (middleware seam dissolves it) |
| `test_permission_resolver_seam.py` | **ARCHIVED** | OLD `PermissionResolver`/`auth_context_from_access_token` + `lorerunes.SCOPE_READ/SCOPE_WRITE`; not in the recut design |
| `test_hosted_readonly_posture.py` | **ARCHIVED** | OLD #295 posture on SDK `_setup_handlers` + `wire_session`; §9 R13/R16 DROPPED; wave-2 re-cuts it (fresh middleware) |
| `test_allowlist_roster.py` | **ARCHIVED** | the R12 flat-file roster; §9 **R12 DROPPED** — admission is now the 48/49 `principal` DB |
| `test_google_token_verifier.py` | **ARCHIVED** | the OLD verifier contract (odoo-code port; `make_verifier`; `lorerunes.SCOPE_READ/is_admitted`) — **SUPERSEDED by my fresh `test_token_verifier.py`** |
| `test_auth.py` | **KEPT (E1a escalated)** | MIXED: `TestApiKeyVerifierIsPreservedVerbatim` tests `loremaster.auth.ApiKeyVerifier` (STILL EXISTS, still GREEN — 785-suite receipt) — KEEP; the retired `LoreTokenVerifier`/`GoogleOAuthConfig` pins (7 mypy errors) need extraction (a content edit beyond `git mv`) |
| `_auth_fixtures.py` | **KEPT (E1b escalated)** | the live fresh contract (`_token_verifier_fixtures.py`) imports its model-AGNOSTIC core (`tokeninfo_payload`/`TokeninfoSpy`/`admitted_payload`/constants) — MUST STAY; the model-specific `make_verifier`/`wire_session` (3 mypy errors) await lead-ruled retirement |
| `lorerunes/tests/test_posture.py`, `test_roster_parser.py` | **KEPT (E1c escalated)** | OLD-design posture + R12 roster referencing never-built `Posture`/`derive_posture`/`SCOPE_READ`/roster symbols (pre-existing RED, 69 mypy errors, NOT caused by me); posture is KEPT in the fresh design §6 → archive-vs-recut is a lead call |

Every ARCHIVED file references ONLY retired symbols / a dropped design row and is superseded — none carried a keeper. Archive-don't-delete: all 6 are `git mv`'d (history preserved, citable path), not deleted.

## Removed-name sweep (anchor-free, per-file adjudication — no "all remaining hits are X")
Retired names swept bare across the LIVE tree (excluding the archive dir): `SCOPE_READ`, `SCOPE_WRITE`, `is_admitted`, `Posture`, `make_verifier`, `wire_session`, `GoogleOAuthConfig`, `derive_edge_policy`, `resolve_posture`, `PostureConfigError`, `auth_context_from_access_token`, `PermissionResolver`, `allowed_emails_file`, `AuthVerifier`, `BearerAuthMiddleware`.

| residual hit location | verdict |
|---|---|
| `loremaster/loremaster/auth.py` (`AuthVerifier`/`BearerAuthMiddleware`/`ApiKeyVerifier`) | **KEEP** — the LIVE current LAN api-key gate; brief DEFERS its deletion to WAVE 3. Not broken by my change. |
| `loremaster/loremaster/server.py` (`BearerAuthMiddleware` wiring) | **KEEP** — live wiring, deferred to wave 3. |
| `test_fastmcp_migration.py`, `test_mcp_server.py`, `test_migration_wire.py`, `test_refusal_observes_effect.py` (`BearerAuthMiddleware`/`AuthVerifier`) | **KEEP** — LIVE tests of the current gate; pass today (part of the working suite). |
| `test_auth.py`, `_auth_fixtures.py` (`GoogleOAuthConfig`/`make_verifier`/`wire_session`) | **ADJUDICATED** — see E1a/E1b (keep file, escalate the stale-part edit). |
| `test_token_verifier.py`, `_token_verifier_fixtures.py` | **BENIGN** — matches are the test-NAME substring `is_admitted` inside `_admitted` (`test_*_is_admitted`) and a docstring naming which retired symbols are NOT reused. No actual reference. |
| `lorerunes/tests/test_posture.py`, `test_roster_parser.py` (`Posture`/`SCOPE_READ`/roster) | **ADJUDICATED** — E1c (pre-existing stale OLD-design tests; not caused by me). |
| `derive_edge_policy`, `resolve_posture`, `PostureConfigError`, `auth_context_from_access_token`, `PermissionResolver` | **CLEAN** — 0 live hits after the archival (they lived only in the 6 archived files). |

Conclusion: my production change introduces NO retired-name reference; every residual is either the LIVE current gate (deferred to wave 3, brief-directed) or an adjudicated stale test file.

## Contract escalations E2/E3/E4 — how they landed
- **E2 (api-key write-scope under the read-only banner):** I implemented reading **(A)** — the api-key branch mints `{lore:read, lore:write}` (banner "LAN keeps full write", F7 deferred). `test_api_key_principal_keeps_full_write` GREEN. No further action; flip is one function (`lan_scopes_for_role`) if the operator ever rules (B).
- **E3 (`(principal, agent)` seam):** implemented via `claims["agent"]=None` + the typed `agent_of` accessor (fail-closed). `test_agent_of_is_the_typed_fail_closed_accessor` + `test_minted_identity_exposes_the_agent_binding_seam` GREEN.
- **E4 (stub home):** kept in the NEW `loremaster/loremaster/token_verifier.py` module (matches the one-module-per-concern idiom; avoids resurrecting the retired `loremaster.auth.LoreTokenVerifier` symbol).

## Escalations (durable here; none blocks the build)

### E1a — `test_auth.py` keeper-extraction (content edit beyond `git mv`)
`test_auth.py` is MIXED: keep `TestApiKeyVerifierIsPreservedVerbatim` (tests `loremaster.auth.ApiKeyVerifier`, still exists, GREEN); archive the retired `TestLoreTokenVerifier…`/`GoogleOAuthConfig` config pins (7 mypy errors, lines 153/492/504/514/527/551/563). The brief's writable set scoped E1 as `git mv`; splitting a file's content is a different operation. **Recommendation:** authorise me to split `test_auth.py` (extract the ApiKeyVerifier/OriginValidation keepers into a small `test_api_key_verifier.py`, `git mv` the stale remainder), or route it to the contract author. Removes 7 more mypy errors.

### E1b — `_auth_fixtures.py` model-specific part-retirement (lead fork, flagged by the contract author)
`_auth_fixtures.py` MUST STAY (the live fresh contract imports its model-agnostic core). Its model-specific `make_verifier`/`wire_session`/`GoogleOAuthConfig`/`hosted_auth_block`/`sdk_bound_handler_names`/`as_principal` are dead (lazy imports of retired symbols; 3 mypy errors, lines 637/638/872). The contract author's E1 explicitly flagged this a lead decision ("if the lead retires `_auth_fixtures.py` WHOLESALE, my fresh contract's re-export seam needs its model-agnostic imports inlined"). **Recommendation:** retire the model-specific functions in place (keep the model-agnostic constants/helpers) OR inline the fresh contract's re-exports then archive `_auth_fixtures.py` wholesale — a lead call; I can do either on ruling.

### E1c — `lorerunes/tests/test_posture.py` + `test_roster_parser.py` (additional stale OLD-design tests)
The anchor-free sweep surfaced two lorerunes tests the contract author's E1 did not enumerate: they assert never-built `lorerunes.Posture`/`PostureRefusal`/`derive_posture`/`SCOPE_READ`/`SCOPE_WRITE` and the R12 roster parser (69 pre-existing mypy errors, RED before my work — NOT caused by me). `test_roster_parser.py` is R12 (DROPPED, §9) → clean archive. `test_posture.py` is the OLD posture derivation, but posture is KEPT in the fresh design §6 (a future lorerunes function) using the NEW scope names — so it likely wants a wave-3 RE-CUT, not a plain archive. **Recommendation:** archive `test_roster_parser.py`; leave `test_posture.py` for a wave-3 posture re-cut (or archive it too if the lead prefers a clean lorerunes leg now). Lead's call.

### E1d — the FROZEN wave-1 contract adds 40 `no-untyped-def` mypy errors
`test_token_verifier.py` leaves its fixture/parametrize params unannotated (`principal_stores`, `email_verified`, `expect_admit`, `monkeypatch`), whereas every other loremaster test annotates them `: Any` (e.g. `test_principals_store.py`). mypy's `disallow_untyped_defs` flags all 40. I may NOT edit a frozen test. This is the ONLY non-stale contributor to the loremaster mypy leg. **Recommendation:** a mechanical, NON-behavioral annotation pass on the frozen contract's params (I can do it if the frozen-edit ban is lifted for type-only annotations), or a scoped `[[tool.mypy.overrides]]` entry (pyproject.toml is outside my writable set), or accept them as the adjudicated packet-39 red. Flagging per scope law — I did not silently annotate the frozen file.

## Note on the injected-client lifecycle rider (design §4.2)
Design §4.2 mentions a degradation rider (close the injected client → next `verify_token` recovers). The FROZEN wave-1 contract has NO such pin, so I did not implement close-detection (would be untested code); `_client()` lazily constructs+caches a fallback client when none is injected (no per-call leak). If wave-1 wants the lifecycle pin, it is a contract addition (escalate to the contract author) — flagging, not silently adding untested recovery logic.
