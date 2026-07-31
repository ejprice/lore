# REPORT-contract-39-auth-1 — packet 39 Google-OAuth CONTRACT

brief-base v9 read

- **state:** done-with-deviations. **REVISED THREE TIMES — §14 (rulings), §16 (adversary pass 1), §17 (DELTA adversary + design R13/R14/R15).** Current counts **472 collected / 439 RED / 33 GREEN**. Earlier revision: S5 INVERTED (the residual window is now pinned CLOSED, not open); S1 accepted and pinned; B1 resolved (`cachetools` 7.1.6 installed, verified). Counts re-measured: **422 collected / 389 RED / 33 GREEN**.
- **deviation 1:** `mypy` reports **170 errors, ALL of the "symbol does not exist yet" class**, all in the 11 files this contract authored. Zero errors of any other class. Enumerated + classified in §6. `ruff` is CLEAN repo-wide.
- **deviation 2 — RESOLVED by the lead 2026-07-31:** `cachetools` is now installed (**7.1.6**, verified via `importlib.metadata`) and declared at `loremaster/pyproject.toml:39`. §7-B1 is closed.
- **deviation 3:** three files the builder MUST edit are outside my writable set; exact edits in §8.
- **deviation 4:** design §4's literal *"require `"email"` in tokeninfo's returned `scope` set"* would deny **every real Google token**. My contract pins the superset property instead. §7-B2.
- **Packages considered:** `mcp` 1.27.2 → **replace** (read `provider.py`, `bearer_auth.py`, `settings.py`, `fastmcp/server.py::streamable_http_app`, `streamable_http_manager.py`) · `mcp.server.transport_security` → **replace_with_adapter** (read `TransportSecuritySettings` + middleware source) · `httpx` 0.28.1 → **keep** (read `httpx/_transports/mock.py`, `_transports/asgi.py`) · `cachetools` → **replace, BLOCKED on install** (not installed; `importlib.metadata` raises) · `google-auth` → **bespoke, claim INHERITED not verified** (not installed; I did not read it) · `email-validator` → **bespoke, forced by workspace law** (not installed; the constraint I read is `lorerunes/pyproject.toml`'s empty `dependencies`) · `watchdog` 6.0.0 → **bespoke, deliberately minimal** · `asgi-lifespan` → **escalate for install** (not installed; hand-rolled ~30-line stand-in ships so the contract is runnable today) · `httpx.ASGITransport` → **keep_with_trigger**. Full table + read-column in §2.
- **decisions-needed:** ALL TEN RULED — see §14. **One open item: the satisfiability receipt** (§13), which only the adversary's reference build can produce. The design-doc consistency flag I raised (§14.4) was re-checked on disk and is **already fixed** by the lead's `591c00c`.
- **receipts:** pin inventory §3 · wrong-build discrimination §4 · RED/GREEN counts §5 · mypy §6 · escalations §7 · out-of-scope edits §8 · adversary brief §9 · checklist §10 · adjudication §11.

---

## 1. Capability check (brief-base §4, first thing in the report)

| Demanded by the brief | What I actually have | What I did instead | What a lead must change |
|---|---|---|---|
| *"lore's own tools are first choice … load with `ToolSearch "select:mcp__lore_lore__lore_search,…"`"* | **The lore MCP tools are NOT in my toolset.** `ToolSearch` with the brief's exact select-list returned `No matching deferred tools found`; a keyword query (`lore search code symbol index`) also returned nothing. | **Fell back to `grep` + `Read` for every code-structure question** — the SDK, `auth.py`, `server.py`, `config.py`, the six `ToolAnnotations` constants, the four `_drive` consumers, odoo-code's verifier. Said out loud here, per the dogfood protocol. | The `tdd-contract` agent definition needs the lore tools added (this is the SAME class as the 2026-07-28 `contract-adversary` finding: an agent required by project law to prefer an indexed tool while lacking the tool to reach one). |
| Friction filing via `lore_findings action=report` | Not reachable (same cause). | Recorded here for the lead to file. | — |
| Everything else (Write, Bash, gates) | Available. | — | — |

**Consequence for this contract:** the exhaustiveness claims in §8 rest on bare, anchor-free greps, not on `lore_impact`. I re-ran each grep repo-wide with no prefix or call-paren anchor (CLAUDE.md's rename-sweep rule) and give `file:line` per hit.

---

## 2. PACKAGE SURVEY — one row per mechanism this contract SPECIFIES

Done inline rather than via `package-scout`: seven of the nine are already on disk and readable (cheaper than a handoff), and I held the mechanism list from the design. The two that are NOT installed are marked as such, and I do **not** assert a limitation I could not read.

| mechanism | libraries evaluated (name + version) | what I **READ** | verdict |
|---|---|---|---|
| Token-verifier protocol, 401 challenge, session identity, `.well-known` route | `mcp` **1.27.2** (installed) | `mcp/server/auth/provider.py` (`TokenVerifier` Protocol; `AccessToken` fields `subject`/`claims`/`expires_at`/`resource`) · `middleware/bearer_auth.py` (`authorization_context()` returns **exactly** `client_id` + `claims["iss"]` + `subject`; `RequireAuthMiddleware._send_auth_error` has `resource_metadata` behind `# pragma: no cover`) · `auth/settings.py` · `fastmcp/server.py::streamable_http_app` (three `# pragma: no cover` blocks around the whole auth branch) · `streamable_http_manager.py::_handle_stateful_request` (`requestor != self._session_owners[...]` → **404 "Session not found"**) · `auth/routes.py::build_resource_metadata_url` | **replace** — the hand-rolled `BearerAuthMiddleware`/`AuthVerifier` are deleted. F3 is confirmed AT SOURCE, not inferred. |
| Host/Origin DNS-rebinding validation | `mcp.server.transport_security` (installed, same dist) | `TransportSecuritySettings` (`enable_dns_rebinding_protection` default `True`; `:*` port wildcards) · `TransportSecurityMiddleware._validate_host` (missing/unknown Host → **421**) · `_validate_origin` (absent Origin ALLOWED) · **`fastmcp/server.py:178-183` — FastMCP AUTO-ENABLES loopback-only `allowed_hosts` whenever `host in ("127.0.0.1","localhost","::1")`** | **replace_with_adapter.** The gap is ONE derivation (`EdgePolicy`) feeding both this and the kept outer middleware. **This read is the single highest-value thing in the survey** — see §4-W7: it is a 100%-production-breaking default that no loopback test can see. |
| Outbound HTTP + its test double | `httpx` **0.28.1** (installed, existing direct dep) | `httpx/_transports/mock.py` — `MockTransport.handle_async_request` awaits the handler if it returns a coroutine, i.e. **async handlers are supported**. That is what makes the "two concurrent verifications overlap" pin possible without hand-rolling a fake client. | **keep** — `httpx.MockTransport` used throughout; no fake client written. |
| TTL positive/negative caches | `cachetools` **7.1.6** — ⚠ **was NOT INSTALLED at contract time** (`importlib.metadata.version` raised `PackageNotFoundError`); **installed by the lead 2026-07-31**, commit `71a53e3`, declared at `loremaster/pyproject.toml:39`. Re-verified on disk: `import cachetools; cachetools.TTLCache` resolves. | odoo-code's production use (`code_mcp/auth.py`: `TTLCache(maxsize=500, ttl=300)` positive, `TTLCache(maxsize=1000, ttl=60)` negative) — its API surface is what the design's §14 row cites. | **replace** the dict-with-timestamps pattern. **UNBLOCKED** (§7-B1 closed). My pins deliberately assert cache BEHAVIOUR (call counts, per-instance isolation, TTL semantics) and name no library — which is exactly why this ruling landed without editing a single test. |
| Google claim validation | `google-auth` — **NOT INSTALLED**; I did **not** read it | Nothing. Design §14 asserts *"its `id_token` verifier targets ID-token JWTs; the connector presents opaque ACCESS tokens"*. **I am inheriting that claim, not measuring it.** | **bespoke (gap only)**, with the inheritance disclosed. My contract pins the tokeninfo POST-body call + the claim checks, which settles the mechanism regardless. If the lead wants the claim verified, that is one `uv run --with google-auth python -c` away. |
| Email normalisation (NFKC → casefold → strip) | `email-validator` — **NOT INSTALLED**; I did **not** read it | `lorerunes/pyproject.toml` — `dependencies = []` with a comment stating *"A third-party dependency added here is inherited by every other member, so it is a design decision, not a tidying."* | **bespoke, forced by WORKSPACE LAW, not by a capability claim.** The predicate must live in the stdlib-only shared home (it is the one thing the roster parser and the verifier must agree on). I am not asserting email-validator cannot normalise. |
| Roster change detection | `watchdog` **6.0.0** (installed, existing direct dep) | Its observer model — a thread + event queue per watched **tree**; it is the indexer's instrument in this repo. | **bespoke, deliberately minimal** — one `os.stat` mtime compare for ONE file. An observer thread for a single file is machinery with no gap to fill. Re-open if the roster becomes a directory. |
| Running an ASGI **lifespan** in a test | `asgi-lifespan` — **NOT INSTALLED** · `httpx.ASGITransport` (installed) | `httpx/_transports/asgi.py` — the string `lifespan` **does not appear**; `ASGITransport` drives HTTP scopes only. So the lifespan gap is real and measured, not assumed. | **escalate for install** (`asgi-lifespan`'s `LifespanManager` is exactly this). A ~30-line `running_asgi_app` ships in `_auth_fixtures.py` so the contract is runnable **today**; it is the piece to delete on install. |
| Driving one ASGI request in a test | `httpx.ASGITransport` (installed) | Same file — it does the job for HTTP. | **keep_with_trigger.** The suite already has `test_auth._drive`, imported at **4 call sites in 2 sibling modules**; adding a second driving mechanism would be two ways to drive one app. `_auth_fixtures.drive` extends that ONE idiom (body + headers + status). **Trigger:** the first auth pin needing cookies, redirects or multipart → migrate `_drive` AND the new driver to `ASGITransport` together. **Validated by execution, not inspection:** `test_an_unauthenticated_initialize_succeeds` drives a REAL MCP `initialize` through the composed app and returns **200 today** (§5), so the hand-built scope is proven, not hoped. |

Domain logic (not a library question): the roster admission predicate, the posture truth table, the read-only tool classification. One line each, moving on.

---

## 3. Pin inventory by group, with the ∀-property each forces

11 files, **421 new pins** (was 413 before the S5/S1 revision) (414 collected including the pre-existing `lorerunes/tests/test_smoke.py`).

| # | file | pins | ∀-property forced |
|---|---|---|---|
| 1 | `lorerunes/tests/test_email_normalisation.py` | 22 | ∀ presented/stored spelling of one identity → ONE normalised form; and ∀ homograph pair → NON-equal forms. |
| 2 | `lorerunes/tests/test_roster_parser.py` | 37 | **INPUT ACCOUNTING:** ∀ caller-supplied roster line → exactly one fate (emitted \| merged-and-reported \| rejected-and-reported). Shared helper `assert_every_roster_line_is_accounted_for`, applied to every successful parse in the module. |
| 3 | `lorerunes/tests/test_posture.py` | 70 | ∀ point of the 2×2×3×2×2 = **48-point** input cross-product → exactly one of three postures or a diagnosable refusal. Allowlist-the-safe: the expectation is written as three ACCEPT rules, so an unanticipated combination lands in "refuse" by construction. |
| 4 | `loremaster/tests/test_auth.py` (rewrite) | 53 | ∀ retired name → absent from `loremaster.auth`; ∀ preserved `ApiKeyVerifier`/`Origin` behaviour → unchanged; ∀ blank config shape → unconstructible. |
| 5 | `loremaster/tests/test_google_token_verifier.py` | 73 | **AUTH ∀:** ∀ `(token, tokeninfo-response, allowlist)` → `None` OR a complete `AccessToken` whose email the allowlist admits and whose `subject`/`claims`/`expires_at` are populated. Shared helper `assert_verification_outcome_is_total`, applied to **every** verification in the module. |
| 6 | `loremaster/tests/test_allowlist_roster.py` | 43 | ∀ principal × ∀ **six** broken roster states → DENIED and LOUD. Not conditioned on a cause. |
| 7 | `loremaster/tests/test_auth_composition.py` | 38 | ∀ posture → the discovery document is present-iff-hosted; ∀ posture → Origin is the OUTERMOST layer. |
| 8 | `loremaster/tests/test_auth_identity_seam.py` | 16 | ∀ ordered pair of distinct principals (google×google, google×api-key, api-key×api-key, anonymous×google) → B cannot resume A's session. |
| 9 | `loremaster/tests/test_hosted_readonly_posture.py` | 55 | **POSTURE ∀:** ∀ registered tool → classified; ∀ (mutating tool × non-write principal) → refused; ∀ (read tool × hosted principal) → NOT refused. |
| 10 | `loremaster/tests/test_permission_resolver_seam.py` | 14 | ∀ resolver output → enforced (a narrowed `permitted` actually filters; an EMPTY set permits nothing). |
| 11 | `loremaster/tests/_auth_fixtures.py` | — | Shared instrument: production-realistic constants, `TokeninfoSpy` (over `httpx.MockTransport`), roster writer, config builders, ASGI driver + lifespan runner. |

**Fate coverage (clause 7), each FORCED by a fixture, not assumed:**
- *emitted* — `test_realistic_roster_parses_to_its_three_principals`
- *merged-and-reported* — `test_two_lines_normalising_to_one_entry_produce_one_entry_and_one_report` (**2 inputs → 1 entry + 1 report**; outputs strictly fewer than inputs)
- *rejected-and-reported* — `test_each_malformed_shape_refuses_the_parse` × 5 shapes
- *anti-vacuity* — the helper itself asserts the candidate-line set is non-empty, so a ∀ over zero items fails rather than passes.

---

## 4. The wrong build each load-bearing pin discriminates against

**This is the deliverable that matters most.** Each row names a build that is green at every other gate.

| # | Wrong build | Why it survives everything else | The pin that reds |
|---|---|---|---|
| **W1** | **F3 verbatim port.** `AccessToken(token=…, client_id=<google id>, scopes=["email"])` — no `subject`, no `claims`. | `authorization_context` returns `('GCLIENT…', None, None)` for **every** Google user; the SDK compares two identical tuples and the binding is inert. odoo-code masks it with a downstream ACL re-check; **lore has none**. Every unit test passes. | `test_auth_identity_seam::test_a_different_listed_principal_cannot_resume_the_session` — a REAL session over the REAL composed app, hijack must 404. Backed at unit level by `assert_verification_outcome_is_total`'s `assert result.subject`. |
| **W1b** | **F3 "fixed" into a false clear:** `subject` populated from something CONSTANT (the client id, a literal, the resource URL). | Every "subject is not empty" assertion passes. Two principals still collapse. | `test_two_google_principals_mint_distinct_subjects` (unit) **and** W1's assembled-app hijack. Two instruments, because the design predicted this is the finding most likely to be mis-fixed. |
| **W1c** | `claims` populated, `subject` still `None`. | Both principals share one issuer, so the tuple is still identical. | Same two pins; `assert result.subject` is separate from `assert result.claims`. |
| **W2** | **F4 inherited fail-open** — `if allowlist: check(...)`. | An empty roster admits **every verified Google account on earth**, and no test with a populated roster can see it. | `lorerunes …::test_an_empty_roster_denies_every_principal` (predicate leg, bypassing the parser) **+** `test_allowlist_roster::test_every_principal_is_denied_when_the_roster_is_broken[empty]` (runtime leg) **+** the boot leg. Three legs, pinned separately, per R11. |
| **W3** | **Silently-shorter roster** — skip the malformed line, keep the good ones. | The operator's config "works"; two of three principals are admitted and nobody learns the third is not. | `test_one_malformed_line_invalidates_the_valid_lines_around_it` (2 good lines around 1 bad) **+** `test_a_parse_refusal_denies_the_VALID_lines_on_the_same_file` at runtime. |
| **W4** | **401-vs-5xx collapse** (`if resp.status_code != 200: reject_and_cache`). | One Google blip blacklists a **valid** token for the whole negative TTL. Both cases "deny", so a collapsed assertion passes. | TWO pins, **opposite** call-count assertions: `test_a_definitive_rejection_is_negative_cached` (2nd call → `call_count == 1`) vs `test_a_transient_upstream_failure_is_NOT_cached` (2nd call → `call_count == 2`), plus `test_a_token_recovers_after_the_outage_ends` and the reverse control `test_a_definitively_rejected_token_stays_rejected_after_a_good_response`. |
| **W5** | **Expiry unit swap** — `expires_at = int(data["expires_in"])`. | `3599` = 1970-01-01, so `RequireAuthMiddleware` rejects **every** token: 100% denial, invisible to any verifier-level test that only checks `expires_at is not None`. The mirror bug (treating `exp` as relative) yields a token valid for millennia. | `assert_verification_outcome_is_total`'s absolute-time sanity band `now ≤ expires_at ≤ now + 1 day`, **plus** `test_the_expiry_is_absolute_and_tracks_the_token_lifetime` — two DIFFERENT lifetimes, so a hardcoded constant TTL also reds. Fixture emits `exp` **and** `expires_in`, both as **strings**, exactly as Google does. |
| **W6** | **Admission evaluated only on the cache-MISS path** (odoo-code's shape). | A revoked principal keeps working for the whole cache TTL. Passes every uncached-revocation test. | `test_a_revoked_principal_with_a_CACHED_token_is_denied` — the fixture DELIBERATELY warms the cache and forces the reload through a *different* principal's miss. Control: `test_the_cached_denial_costs_zero_outbound_calls` proves the denial came from an admission check over a live cache HIT, not from a cache flush. |
| **W7** | **`transport_security` left unset.** | ⚠ **Measured at the SDK:** FastMCP auto-enables DNS-rebinding protection with `allowed_hosts=["127.0.0.1:*","localhost:*","[::1]:*"]` whenever `host` is loopback — and lore binds loopback in **every** posture. Hosted requests arrive through lore-caddy carrying `Host: lore.firehawktransam.org` → **421, 100% of production traffic**. Every loopback test passes. | `test_auth_identity_seam::test_the_public_hostname_is_accepted` (behavioural, through the live transport) + `test_auth_composition::test_the_hosted_edge_policy_allows_the_public_hostname` + the equality pin `mcp.settings.transport_security == EdgePolicy.to_transport_security()`. Control: `test_the_loopback_host_is_still_accepted`. |
| **W8** | **Two Origin policies** — claude.ai added to the outer middleware only. | Every composition pin passes; the SDK's inner Origin check 403s the real connector the moment a session is created. | `test_the_claude_origin_passes_BOTH_origin_layers` (live transport) + `test_the_hosted_edge_policy_carries_the_claude_origins`. |
| **W9** | **Bearer stays outermost.** | A hostile browser origin can make lore dial Google once per request, from lore's IP, with an attacker-chosen token. Ordering alone is not observable. | `test_a_hostile_origin_is_403_with_ZERO_outbound_google_calls` — the spy's `call_count == 0` is the property; the layer-ordering assertion is secondary. |
| **W10** | **F2 — discovery behind the gate.** | `/.well-known/…` 401s; claude.ai's connector can never begin the flow, and nothing local notices. | `test_the_well_known_document_is_served_without_any_credential` **and** `…_with_a_claude_ai_origin` (both Origin shapes, because M-1 is unmeasured) + `test_the_401_carries_a_resource_metadata_url_that_resolves` (the advertised URL is then FETCHED and must 200). |
| **W11** | **`aud` skipped when absent** (`if "aud" in data and data["aud"] != client_id`). | Passes the mismatch pin. Any token with no `aud` is admitted. | `test_a_missing_aud_is_a_hard_reject_not_a_skipped_check`, plus `_an_empty_string_aud_`, plus `_an_aud_that_is_a_prefix_of_ours_` (kills `startswith`). Negative control: a token from a **different, well-formed** OAuth client belonging to a **listed** principal. |
| **W12** | **`email_verified` bool-only.** | Every Google **Workspace** principal is denied (Workspace returns the string `"true"`). | 3 truthy shapes × admitted, 7 falsy/absent shapes × denied, parametrised. |
| **W13** | **Scope check as a tautology** (compare our own minted scopes to themselves — odoo-code's shape). | Nothing is actually checked. | `test_a_grant_without_the_email_scope_is_denied` over 4 shapes + `test_a_scope_merely_containing_the_word_email_is_not_enough` (kills substring matching). See §7-B2 for the design-wording hazard on the other side. |
| **W14** | **#291's hand-list "corrected" instead of derived.** | A subset check cannot see an omission. It already drifted once (`lore_claim_task`, `lore_tasks`). | `test_the_derived_mutating_set_equals_the_named_behaviour_fixtures` — **EQUALITY**, which is exactly what #291's pin lacked — over a set DERIVED from `await mcp.list_tools()`. Plus 12 named refusal fixtures. |
| **W15** | **Read-only guard keyed on `client_id.startswith("api_key:")`.** | Passes every posture pin. Admits anything that merely spells its client id that way. | `test_a_write_scope_is_what_permits_not_the_client_id_shape` — a forged `client_id` with only `lore:read` must still be refused. |
| **W16** | **Guard that refuses everything.** | Passes all 12 refusal pins. Hosted principals get nothing, which is the whole point of admitting them. | `test_a_google_principal_is_NOT_refused_a_read_only_tool` × 9 read tools + `test_a_newly_registered_read_only_tool_is_permitted`. |
| **W17** | **Resolver seam injected and never called.** | The default is identity, so "called" and "not called" are indistinguishable. | `test_the_injected_resolver_is_called_on_every_tool_dispatch` (call log) + `test_a_tool_outside_the_resolved_permitted_set_is_refused` (the fake must be able to FAIL) + `test_an_empty_permitted_set_permits_NOTHING` (F4's shape one layer up). |
| **W18** | **Roster read once at boot.** | Passes every in-memory pin. The operator's revocation requires a recreate — the one thing R12 exists to prevent. | `test_an_uncached_principal_added_mid_process_is_admitted` / `…_revoked_mid_process_is_denied`, both mutating a REAL file mid-process. |
| **W19** | ~~`stat` on every request~~ → **REVERSED BY THE S5 RULING (§14.1).** The wrong build is now the OPPOSITE: **`stat` on the cache-MISS path only.** | Correct for an uncached principal, and it leaves a revoked-but-CACHED principal admitted until something unrelated happens to miss. Passes every uncached-revocation pin. | `TestRevocationIsEffectiveOnTheVeryNextVerification::test_a_revoked_principal_with_a_cached_token_is_denied_immediately` (NO intervening miss; the denial is asserted to cost ZERO outbound calls, so it cannot pass because caching is broken) + `TestRosterFreshnessOnEveryVerification::test_every_verification_stats_the_roster_including_cache_hits` (mechanism). |
| **W19b** | **Revocation "fixed" by FLUSHING the token cache on every roster edit.** | Passes the denial pin. It is a different, much weaker mechanism: every live token is re-validated with Google whenever an operator saves the file — a thundering herd triggered by a text editor. | `test_the_token_cache_is_not_flushed_by_a_roster_edit` — a still-listed principal's warm token must survive an unrelated edit with ZERO outbound calls. |
| **W19c** | **Re-reading the whole roster file on every verification.** | Satisfies S5's freshness ruling perfectly and puts a file read on lore's hottest path (design R12 rules the re-read conditional on mtime). | `test_an_unchanged_roster_is_not_re_read` — implementation-agnostic instrument: the file is made unreadable with its **mtime untouched** (`chmod` moves ctime, never mtime), so a stat-and-compare build keeps serving and a re-read build denies. Control: `test_a_changed_roster_IS_re_read`. |
| **W20** | **`ApiKeyVerifier.verify` re-implemented inline.** | Every behavioural api-key pin passes while the branch carries its own timing behaviour and empty-key policy. | `test_the_api_key_branch_routes_through_ApiKeyVerifier` — neuter `ApiKeyVerifier.verify`, the branch must go dark (ROUTING IS NOT SHARING, proven by mutation inside the pin). |
| **W21** | **Token in the URL.** | Works perfectly; leaks every token into the journal at INFO. | `test_the_token_is_posted_in_the_body_and_never_in_the_url` — asserts on the RECORDED request URL and body. |
| **W22** | **`realm`-style 401 with no `resource_metadata`.** | A compliant client has no way to discover where to authenticate. The upstream branch is `# pragma: no cover`, so nothing upstream covers it either. | `test_the_401_carries_a_resource_metadata_url_that_resolves` — asserts the parameter AND fetches the URL. |

---

## 5. Counts — collected / RED / GREEN, explicitly

Commands, so the numbers are re-derivable rather than inherited:

```
CONTRACT="lorerunes/tests loremaster/tests/test_auth.py loremaster/tests/test_google_token_verifier.py \
 loremaster/tests/test_allowlist_roster.py loremaster/tests/test_auth_composition.py \
 loremaster/tests/test_auth_identity_seam.py loremaster/tests/test_hosted_readonly_posture.py \
 loremaster/tests/test_permission_resolver_seam.py"
uv run pytest $CONTRACT --collect-only -q | tail -2      # the expected-RED id source
uv run pytest $CONTRACT -n auto -q --tb=no -rp
```

Measured **2026-07-31**, working tree at parent commit `eeaca99`. **Both measurements are
kept** — the pre-ruling one because §4's wrong-build table was written against it, the
post-ruling one because it is the current state:

| metric | pre-ruling | **post-ruling (CURRENT)** |
|---|---|---|
| collected | 414 | **422** (421 new + 1 pre-existing `lorerunes/tests/test_smoke.py`) |
| **RED** | 381 | **389** |
| GREEN | 33 | **33** (the same 33 — no new pin passes by accident) |

**The +8 delta is DERIVED, not observed** (a count read off the output is the tautology
this repo has the most receipts against): −1 deleted `TestTheResidualWindowIsAKnownBound`
· −2 the two old cached-revocation pins it depended on · +4 `TestRevocationIsEffective
OnTheVeryNextVerification` · +1 `TestRosterFreshnessOnEveryVerification` (2 → 3 pins)
· +6 the S1 known-bound class (5 parametrised + 1 control) = **+8**. It reconciles exactly.

**Every one of the 33 GREEN is a preserved-behaviour pin or a fixture self-control** — verified by listing them, not by assuming:
- 12 × `TestApiKeyVerifierIsPreservedVerbatim` (design §8 rows 3/11)
- 3 × `TestBuildApiKeyVerifierFromConfig` (row 10)
- 7 × `TestOriginValidationMiddlewareIsPreserved` (rows 4/13)
- 3 × `TestRetiredAuthSurfaceIsGone::test_the_kept_names_are_still_exported` (the control for the absence pins)
- 2 × `TestLoopbackPostureIsUnchanged` (trivially true today; they become load-bearing after the build)
- 1 × `test_a_config_without_the_retired_flag_loads`
- 2 × `TestLoreConfigCrossChecksTheResourcePath` refusals — ⚠ **currently passing for the WRONG reason**: today the whole hosted `auth` block fails `extra="forbid"` (no `mode`/`google` fields yet). Their positive control `test_matching_paths_validate` is RED, so the pair only becomes meaningful together — and if the builder ships the config model WITHOUT the path cross-check, the control goes green and these two go red. Disclosed rather than hidden.
- 1 × `test_an_unauthenticated_initialize_succeeds` — **the positive control that proves the ASGI harness works**: a real MCP `initialize` through the real composed app returns 200 today.
- 1 × `test_the_homograph_fixture_is_actually_a_homograph` (proves the Cyrillic fixture really is a homograph, so the non-match pin is not passing because the fixture is simply a different address)
- 1 × pre-existing `lorerunes/tests/test_smoke.py`

**Nothing else in the suite regressed** (the modules that consume `test_auth._drive` and the annotation surface):

```
uv run pytest loremaster/tests/test_eager_startup.py -n auto -q          →  16 passed in 7.74s
uv run pytest loremaster/tests/test_mcp_server.py loremaster/tests/test_config.py \
  loremaster/tests/test_server.py loremaster/tests/test_retired_symbols.py \
  loremaster/tests/test_secret_leak_vectors.py -n auto -q                → 982 passed in 103.67s
uv run ruff check .                                                      → All checks passed!
```

### A harness defect I found and fixed BEFORE shipping (receipt, not decoration)

The first run of the lifespan-driven module died in `make_embedder_from_config` → `KeyError: LORE_TEI_KEY`. Cause: `stub_heavy_startup` originally **rebound** `mcp._lore_eager_guard`, but `build_mcp_server`'s per-SESSION lifespan closes over the guard **instance**. So the eager path was stubbed and the first MCP session still ran the REAL heavy build. Fixed by mutating the shared object's `_build` instead (`_auth_fixtures.stub_heavy_startup`, with the measurement written into its docstring). **Without the positive control (`test_an_unauthenticated_initialize_succeeds`) this would have shipped as "8 identity pins that are RED for an unrelated reason" and the builder would have chased it.**

---

## 6. mypy — 170 errors, one class, enumerated

`./scripts/typecheck.sh` → `lorerunes` 89, `loremaster` 81, others clean. Classified by shape:

| shape | count | in files |
|---|---|---|
| `Module "X" has no attribute "Y"  [attr-defined]` | 163 | the 11 authored files |
| `Unexpected keyword argument "X" for "build_mcp_server"  [call-arg]` | 3 | `http_client=` ×2, `permission_resolver=` ×1 |
| `… becomes "Any" due to an unfollowed import  [no-any-unimported]` | 4 | downstream of the missing `lorerunes` exports |

**Zero errors of any other class**, and every error is in a file this contract authored (`cut -d: -f1 | sort | uniq -c` receipt in §5's commands). Each disappears when the builder lands the named symbol; the `no-any-unimported` four disappear when `lorerunes` exports `Posture`/`PostureRefusal`/`RosterParse`/`RosterParseError`.

One genuine typing defect of mine was found and fixed rather than papered over: `_VerifierProbe.verify` returned `Any` (`no-any-return`); it now `cast`s.

**Why the tests do lazy, function-local `lorerunes` imports:** a module-level import of a not-yet-existing symbol collapses the whole file into ONE **collection error**, which yields **zero node ids** — and `scripts/mutation_proof.py` requires the expected-RED set to be declared from `--collect-only` BEFORE the run. The first collection attempt produced exactly that (6 modules, 0 ids). Function-local imports keep every module collectible so each pin fails on its own terms. A comment block in each affected file says so.

---

## 7. ESCALATIONS — 4 blockers, 6 spec-silent rulings

Per brief-base §2: *"escalating is a success state"*. I picked a reading for each and wrote the alternative down; none was resolved silently.

### Blockers (the builder cannot proceed without a decision)

**B1 — `cachetools` is NOT INSTALLED.** Design §14 rules it a new direct dep of `loremaster`; `importlib.metadata.version("cachetools")` raises `PackageNotFoundError`. Standing law: *a missing dependency is grounds to ESCALATE for install authorization, never to code around the gap.* **Recommendation:** authorise `uv add cachetools>=5` in `loremaster/pyproject.toml` in the build wave. My cache pins assert behaviour and name no library, so they do not pre-empt the ruling.

**B2 — design §4's scope check, read literally, denies every real token.** §4 says *"require `"email"` in tokeninfo's returned `scope` set"*. Google's `/tokeninfo` echoes **full scope URIs** (`https://www.googleapis.com/auth/userinfo.email`), not the bare alias a client requested. A build that implements the sentence verbatim (`"email" in scope.split()`) refuses **100% of production traffic** — the same shape as W5, from a different door. **My contract pins the SUPERSET property**: `test_a_grant_carrying_the_email_scope_is_admitted` is parametrised over **both** the full-URI form and the bare-alias form, so a correct build must accept either. ⚠ **I could not verify which form Google actually returns** (no live token; `google-auth` not installed) — this is a design-wording defect either way, and the build leg's live probe (design §13's last bullet) must settle it.

**B3 — three files the builder MUST edit are outside my writable set.** Exact edits in §8. If they are not made, the wave lands red on files I was forbidden to touch.

**B4 — `build_mcp_server` needs two new keyword-only parameters** (`http_client=`, `permission_resolver=`) that design §4/§6 imply but never name. Both are additive and optional, so the ~25 existing callers are unaffected. Without `http_client=` there is **no hermetic way to drive the assembled app** — the alternative is a live socket to `oauth2.googleapis.com` from the test suite, which the repo's own hermeticity pin forbids. Flagged rather than assumed because it changes a public signature.

### Spec-silent — operator ruling required

**S1 — ⚠ REMOVED BEHAVIOUR DESIGN §8 DOES NOT LIST: unauthenticated path enumeration.**
Today `BearerAuthMiddleware` gates **every** HTTP path, so `POST /anything` with no credential is `401`. Under the new composition the SDK wraps **only** the streamable route, so an unknown path is `404` — an anonymous caller can now enumerate which paths exist. At the public edge this is masked by lore-caddy's `everything else → 404` matcher (R4), but **`LAN_BEARER` has no caddy in front of it**. Design §8 row 7 adjudicates the *discovery* path deliberately; it does not adjudicate the *rest of the path surface*. I did **not** pin it either way. **Recommendation:** accept (the disclosure is a route list, not data) and record it as a KNOWN BOUND in the verifier docstring — but that is an operator call, not mine.

**S2 — duplicate roster lines.** R7/R12 rule that a *malformed* line refuses the whole roster and forbid "a silently-shorter list", but a DUPLICATE is not malformed — and a set-valued parser silently shortens on one. Two readings: **(a) merge-and-report**, **(b) parse refusal**. **I chose (a)** and made it observable by defining the parser's return as `RosterParse(entries, merged)` rather than a bare `frozenset`. That is also what makes clause 7's merge fate FORCEABLE rather than notional. Alternative (b) is a one-line change to `parse_roster` plus deleting `TestParseRosterMergeFate`.

**S3 — what `mode` means while `enabled` is False.** §5's table does not say. **I chose allowlist-the-safe**: `LOOPBACK` requires the default `api_key` mode, so `enabled: false` + `mode: google_oauth` is a diagnosable refusal. Alternative: mode is inert while disabled → silent `LOOPBACK`, which lets an operator believe hosted auth is configured when nothing is gated. Costs 1 of the 48 cross-product cells either way.

**S4 — `PostureRefusal`: return value or exception?** §5 says *"returning a `Posture` enum **or** a typed refusal"*. **I chose a union return** from the pure `lorerunes` function (testable, keeps `lorerunes` free of control flow), with a separate impure `loremaster.config.resolve_posture(config) -> Posture` that raises `PostureConfigError` — which is also where R12's boot-time roster check lives. Alternative: `derive_posture` raises directly.

**S5 — ⚑ RULED AND INVERTED (lead, 2026-07-31). SUPERSEDED; see §14.1.** I originally pinned the residual window OPEN as a KNOWN BOUND, faithfully following design §1 + §3-R12. The operator has **overruled that wording** — it was a performance floor, never a licence to cap revocation speed. The window is now **CLOSED**: stat on EVERY verification, denial on the FIRST verification after the edit. `TestTheResidualWindowIsAKnownBound` is **DELETED** and four inverse pins take its place. **Escalating this was the right call and the outcome proves it** — had I implemented the design silently, the packet would have shipped a capped revocation speed nobody chose.

**S6 — `WWW-Authenticate: Bearer realm="loremaster"`.** §8 row 1 supersedes the 401 *shape*; the SDK emits `error=` / `error_description=` / `resource_metadata=` and **no `realm`**. I did **not** pin `realm` (adjudication: dropped-deliberately under row 1). Grep found no consumer keying on it. Named here so the drop is a decision rather than an omission.

---

## 8. Exact edits the builder must make OUTSIDE my writable set

Each hit found by a **bare, anchor-free** grep (no prefix, no call-paren anchor), with a per-site verdict — no "all remaining hits are X".

1. **`loremaster/tests/test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost`** — imports `BearerAuthMiddleware` and asserts `isinstance(app, BearerAuthMiddleware)`. Design §8 row 13: **rewritten, not deleted**. The replacement already exists as `test_auth_composition::TestOriginIsOutermost::test_the_composed_app_is_not_wrapped_in_the_retired_bearer_middleware` + `…::test_a_hostile_origin_is_403_with_ZERO_outbound_google_calls`. **Edit:** replace the body with `assert isinstance(app, OriginValidationMiddleware)` and a 401-for-keyless assertion; keep the test NAME's intent by renaming it `test_composed_auth_app_is_origin_outermost`.
2. **`loremaster/tests/test_mcp_server.py` `_MUTATING_TOOLS`** (module-level set) and its sole consumer `test_mutating_tools_are_not_marked_read_only`. Design §7: **DELETED, not corrected** (finding #291). Coverage moves to `test_hosted_readonly_posture::test_the_derived_mutating_set_equals_the_named_behaviour_fixtures`, which uses **equality** over a derived set. **Edit:** delete both. (`_READ_ONLY_TOOLS` and its test may stay — it is a positive-direction list whose omission cannot open a hole.)
3. **`loremaster/tests/test_retired_symbols.py` `_RETIRED_SYMBOLS`** — must gain `BearerAuthMiddleware`, `AuthVerifier`, `tls_terminated_upstream`, each with its one-line reason. ⚠ **Add them in the SAME commit that deletes the production symbols** — `test_every_retired_symbol_is_really_gone` reds if a name is registered while it still exists.
4. **`loremaster/pyproject.toml`** — `cachetools>=5` (§7-B1), pending authorization.
5. **`loremaster/loremaster/server.py`'s local ASGI-alias comment** (near `_Scope`/`_ASGIApp`) explains the duplication by pointing at *"auth's copies are module-PRIVATE"*. Still true after the deletion (they belong to `OriginValidationMiddleware` now) — **no edit needed**, flagged only so the sweep does not misread it.

### Removed-behaviour inventory cross-check — what design §8 MISSED

I read `auth.py` in full and greped every consumer independently **before** reading §8 (per the adversary's P6b discipline: independent enumerations are DIFFED, never shared). Three items §8 does not carry:

| missed item | verdict I applied |
|---|---|
| **`test_auth.py` is a PROVIDER, not just a consumer.** `_drive` is imported at **4 sites** — `test_eager_startup.py` (×2) and `test_mcp_server.py` (×2). §8 lists `test_auth.py` under "consumers of the deleted symbols" only. Rewriting the file without preserving `_drive` breaks 4 green tests. | **preserved-with-pin**: `_drive` and `_RecordingApp` kept with byte-identical signatures and a ⚠ note in the module docstring saying they are public-by-use. Verified: `test_eager_startup` 16 passed, `test_mcp_server` suite 982 passed. |
| **Anonymous path enumeration** (§7-S1). | **spec-silent → operator ruling.** Not pinned either way. |
| **`realm="loremaster"`** on the challenge (§7-S6). | **dropped-deliberately** under §8 row 1's "shape superseded"; no consumer found. |

**Deliberate drops (list 1):** anonymous path enumeration is NOT on this list — it is on the ruling list. Deliberate drops are: the `realm` parameter (S6); the 401 body `Unauthorized`/`text/plain` (§8 row 8); the whole-app Bearer gate over the discovery path (row 7); the sync `AuthVerifier.verify` seam (row 9); `tls_terminated_upstream` (row 12, with its intent re-homed as the https-only validator — **pinned**); the retired `__all__` entries (row 14).

**Old-bug, NOT re-pinned:** `auth.py`'s docstring claim that an OAuth backend *"slots into the same `BearerAuthMiddleware`"* and that the seam is *"async-friendly"* (§8 row 9, F1). Both were false. Nothing in this contract asserts them.

**Open rulings (list 2):** S1–S6 above.

---

## 9. What the contract-adversary must attack (per design §9's closing paragraph)

1. **F3, and specifically the false clear.** Build the verbatim odoo-code port AND the three "fixed" variants in W1b/W1c. Does the contract catch all four? The assembled-app pin is the only instrument that can — verifier-level assertions cannot.
2. **The 401-vs-5xx split.** Build the collapsed version. Exactly two pins must red, and for opposite reasons.
3. **The §7 derivation.** Build a version that hand-lists tools. `test_the_derived_mutating_set_equals_the_named_behaviour_fixtures` should catch it — verify, because it is the pin replacing a gate that already failed once.
4. **The `EdgePolicy` seam.** Build one that computes the policy and feeds only the outer middleware. W7/W8 claim the live-transport pins catch it; that claim is untested against a real wrong build.
5. **Fixture perturbation (P2).** The values most worth mutating: `GOOGLE_ACCESS_TOKEN_LIFETIME_S` (3599), the two `*_SUBJECT` strings, `GRANTED_SCOPE_STRING`, `PUBLIC_HOSTNAME`. If perturbing a subject does not red the identity pins, they are not discriminating.
6. **SATISFIABILITY RECEIPT (the C-DEF class).** The adversary must build the reference implementation anyway — prove all **421** pins go 0-failed on it, **including after the ruff-driven orphaned-import cleanup that deleting `BearerAuthMiddleware` forces**. The two pins I am least confident are satisfiable as written (**re-aimed after the S5 revision** — the pin this bullet originally named, `test_a_cache_hit_performs_no_roster_stat`, no longer exists): `test_an_unchanged_roster_is_not_re_read` (its instrument is a `chmod` with the mtime deliberately untouched — the riskiest fixture in the contract) and `test_an_expired_token_is_not_served_from_the_positive_cache` (a 2.5 s real sleep).
7. **The mutual-satisfiability question, RE-AIMED after S5.** The old form asked whether the residual-window pin and the zero-stat pin could both hold; the S5 inversion deleted that tension. The question that replaces it is sharper: are `test_an_unchanged_roster_is_not_re_read` (unreadable + mtime UNCHANGED ⇒ keeps serving) and `test_an_unreadable_roster_denies_everyone` (unreadable + mtime MOVED ⇒ denies) simultaneously satisfiable? They are designed to be — the distinguishing input is the mtime, and a cross-reference comment sits on both — but they are the closest thing to a contradiction in this contract and the reference build should be checked against them FIRST. If they cannot both hold, that is a CONTRACT defect and it routes back to me.

**Expected-RED node ids** for `scripts/mutation_proof.py` come from `--collect-only` (§5's command), never transcribed from a run's output.

---

## 10. Realism-&-independence checklist

- ☑ **Production-realistic inputs.** Every value is a recorded production shape, not a convenience: the REUSED Price Paper OAuth client id verbatim (R2, `~/docker/mcp/.env`); Google's tokeninfo body with `exp`/`expires_in`/`email_verified` as **JSON strings** (which is what makes W5 catchable); a 3599 s lifetime; `ya29.`-prefixed ~200-char opaque tokens; 21-digit `sub` values; the live `lore.yaml`'s `127.0.0.1:9202` + `/mcp`; `https://lore.firehawktransam.org/mcp` (R3/R4); real firehawktransam.org / pricepaper.com addresses; a roster file with the comment/blank/indent structure a hand-edited file actually accumulates. **No `a@b`, no `x=1`, no round numbers chosen so the arithmetic comes out clean.**
- ☑ **Independent expected values.** Every expectation comes from the requirement, an RFC, the stdlib, or the wall clock — never from restating an implementation. `EXPECTED_METADATA_URL` is derived from **RFC 9728 §3.1's construction rule**, not from the SDK's `build_resource_metadata_url` (which would have been a tautology against the very code under test). The NFKC assertions use `unicodedata.normalize` as an independent oracle. The expiry band uses `time.time()` read by the test. `expected_posture()` restates design §5's three table rows, written as an allowlist so unanticipated combinations land in "refuse" by construction. **Tautology check applied to the §7 derivation specifically** — a purely derived expectation flips with the annotation, which is why 12 named behaviour fixtures + an equality pin sit beside it.
- ☑ **Seam / boundary coverage.** Six real handoffs, each with a real value crossing: (1) our verifier → the SDK's `authorization_context` (a live MCP session, hijack attempted); (2) `EdgePolicy` → `TransportSecuritySettings` (a live `Host: lore.firehawktransam.org` request, the 421 trap); (3) roster file bytes → normalised set → the email Google reports (a real file, capitalised on one side, lowercase on the other); (4) tokeninfo JSON strings → `AccessToken` ints; (5) outer Origin middleware → the SDK's inner Origin check (one request through both); (6) `test_auth._drive` → its 3 sibling consumer modules (re-run green). **Mocks on each side individually were explicitly not enough here** — W7 is invisible to any pin that does not drive the real transport.
- ☑ **Magnitude / sanity bound on derived outputs.** `expires_at` — the only derived numeric — gets `now ≤ expires_at ≤ now + 1 day` on **every** verification via the shared ∀ helper, plus a two-lifetime differencing pin that kills a hardcoded constant TTL. Roster counts get conservation (`len(entries) + len(merged) == len(candidate lines)`). Outbound-call counts get exact bounds in both directions.
- ☑ **Shared domain conventions, never hardcoded literals.** Scope strings come from `lorerunes.SCOPE_READ`/`SCOPE_WRITE` (the same constants production mints/checks). Posture names are read off `Posture` enum members, never spelled in prose. The hosted-instructions section is located by an imported `HOSTED_REFUSAL_SECTION_HEADING` constant, so the builder chooses the prose and the test cannot drift from it. The `derive_posture` refusal pin derives its legal field names from `inspect.signature(derive_posture)`. Configs are built with the **production** `LoreConfig.model_validate`, never a hand-rolled stand-in.
- ☑ **Hostile fixtures for rendered stored text.** The roster is operator-supplied stored free text rendered into ERROR records. Two hostile fixtures, both required to render unambiguously: a line carrying a **backtick fence run + a key=value payload shaped exactly like lore's own `event=roster.reloaded entries=99 ok` output** (a forgery), and a line carrying **ANSI escapes + tabs**. Pinned at both layers (the `lorerunes` parser refusal and the `loremaster` runtime ERROR record): the offending line must appear `repr`-quoted, the record must stay ONE line, and a raw `\x1b` must never reach the message. Plus `test_the_error_does_not_dump_the_whole_roster` — the file is a membership list, not a diagnostic payload.
- ☑ **Input accounting (totality).** `parse_roster` is a collection transform; `assert_every_roster_line_is_accounted_for` is applied to **every** successful parse in the module, all three fates are FORCED by fixtures (the merge fate produces strictly fewer outputs than inputs), and the helper refuses to run on an empty candidate set so a ∀ over nothing fails rather than passes. **Mutation proof is owed by the builder** — I cannot mutate production code that does not exist yet; the expected-RED id is `lorerunes/tests/test_roster_parser.py::TestParseRosterMergeFate::test_two_lines_normalising_to_one_entry_produce_one_entry_and_one_report`, and the mutation is "drop the merge report from `RosterParse`".

---

## 11. Files written

| path | pins | note |
|---|---|---|
| `lorerunes/tests/test_email_normalisation.py` | 22 | new |
| `lorerunes/tests/test_roster_parser.py` | 37 | new — carries the input-accounting helper |
| `lorerunes/tests/test_posture.py` | 70 | new — 48-point cross-product |
| `loremaster/tests/_auth_fixtures.py` | — | new — shared instrument (constants, `TokeninfoSpy`, ASGI driver + lifespan runner, config builders) |
| `loremaster/tests/test_auth.py` | 53 | **REWRITTEN** — the old 29 pins certified a world that is going away; `_drive`/`_RecordingApp` preserved verbatim for 4 external call sites |
| `loremaster/tests/test_google_token_verifier.py` | 73 | new — carries the Auth-∀ helper |
| `loremaster/tests/test_allowlist_roster.py` | **43** | new — real files, mutated mid-process; **S5-inverted** |
| `loremaster/tests/test_auth_composition.py` | **38** | new; **+6 for the S1 known bound** |
| `loremaster/tests/test_auth_identity_seam.py` | 16 | new — the F3 module; runs the real lifespan |
| `loremaster/tests/test_hosted_readonly_posture.py` | 55 | new — #291's fix |
| `loremaster/tests/test_permission_resolver_seam.py` | 14 | new |

No production file, `lore.yaml`, `Containerfile` or skill was touched. No git state was mutated.

---

## 12. Public API surface this contract DEFINES

The builder implements exactly this. Names the design implies but does not spell are marked ⊕.

**`lorerunes`** (stdlib-only, re-exported at package level): `normalize_email(str) -> str` · `parse_roster(str) -> RosterParse` ⊕ · `RosterParse(entries: frozenset[str], merged: tuple[MergedRosterLine, ...])` ⊕ · `MergedRosterLine(line_number, line, entry)` ⊕ · `RosterParseError(ValueError)` with `.line` / `.line_number` · `is_admitted(email: str, roster: frozenset[str]) -> bool` · `Posture` (`LOOPBACK` / `LAN_BEARER` / `HOSTED_OAUTH`) · `PostureRefusal(nearest: Posture, problems: tuple[str, ...], message: str)` ⊕ · `derive_posture(*, host_is_loopback, enabled, mode, has_keys, has_google) -> Posture | PostureRefusal` · `SCOPE_READ = "lore:read"` · `SCOPE_WRITE = "lore:write"`.

**`loremaster.config`**: `GoogleOAuthConfig(client_id, resource_server_url, allowed_emails_file)` · `AuthConfig(enabled, mode, keys, google, allowed_origins)` — `tls_terminated_upstream` DELETED with a migration message naming the field **and the fix** · `resolve_posture(LoreConfig) -> Posture` ⊕ (impure; performs R12's boot roster check) · `PostureConfigError` ⊕.

**`loremaster.auth`**: `LoreTokenVerifier(api_key_verifier=None, google=None, *, http_client=None)` · `_new_http_client() -> httpx.AsyncClient` ⊕ (the ONE construction seam — it is what makes the lifecycle-recovery pin hermetic) · `EdgePolicy(allowed_origins, allowed_hosts)` + `.to_transport_security()` ⊕ · `derive_edge_policy(config, posture) -> EdgePolicy` ⊕ · `AuthContext(subject, email, provenance, permitted)` · `PermissionResolver` Protocol · `PassThroughPermissionResolver` · `auth_context_from_access_token(AccessToken | None) -> AuthContext | None` ⊕ · `_HOSTED_DEFAULT_ORIGINS`. **KEPT:** `ApiKeyVerifier`, `build_api_key_verifier`, `OriginValidationMiddleware`, the `hmac` module attribute. **DELETED:** `BearerAuthMiddleware`, `AuthVerifier`.

**`loremaster.server`**: `build_mcp_server(server, *, http_client=None, permission_resolver=None)` ⊕ (both additive, keyword-only) · `HostedToolRefusedError(ToolError)` ⊕ · `PermissionFilteredToolError(ToolError)` ⊕ (distinct types — a consumer must be able to tell "the posture forbids this, never retry" from "your permissions do, an operator can grant it") · `HOSTED_REFUSAL_SECTION_HEADING: str` ⊕.

---

## 13. Task-2 assignment mapping (lead, 2026-07-31T03:44:55Z) — and TWO clauses I could NOT discharge

The assignment named six pin groups. All six are delivered; the contract is WIDER than six
(two further groups below). **Two clauses of the assignment are NOT discharged by this
report, and neither was in my power to discharge — they are named here so they cannot be
read as satisfied.**

| # | assignment clause | delivered | pins |
|---|---|---|---|
| 1 | allowlist predicate, **fail-closed both legs** | `lorerunes/tests/test_roster_parser.py` + `loremaster/tests/test_allowlist_roster.py`. ⚠ **FOUR legs, not two** — R11 says *every* leg: config (blank path unconstructible), boot (`TestBootRefusesAnUnloadableRoster`), runtime (`TestRosterFailsClosedAtRuntime`, ∀ principal × 6 broken states), and the BARE predicate handed an empty set directly (`TestIsAdmittedFailsClosed`) so the defence survives a refactor that bypasses the parser. | 78 |
| 2 | Google validation — `aud`, **`email_verified` 4 values**, 401-vs-5xx split | `test_google_token_verifier.py`. ⚠ **10 `email_verified` parametrisations, not 4**: 3 truthy (`True` / `"true"` / `"True"`) + 7 falsy-or-absent (`False` / `"false"` / `"False"` / `""` / `None` / `0` / **key absent**). The absent case is the one a naive `.get()` turns into `None`. | 73 |
| 3 | cache — poisoning + positive control, per-instance, **no await under lock** | `TestTokenCacheIsLiveIsolatedAndUnpoisonable` + `TestConcurrencyAndLifecycle`. **DEVIATION, stated:** design §4 says *"pin via an instrumented lock"*. I pinned it **behaviourally** instead — two concurrent verifications of different tokens must OVERLAP their outbound calls (an `asyncio.Event` gate both handlers must reach). Rationale: an instrumented-lock pin must name the lock attribute, which writes an internal into the contract; the overlap formulation names nothing and fails the same way (a lock held across the await deadlocks the gate → bounded timeout → RED). If you want the instrumented form as well, say so and I will add it. | (within 73) |
| 4 | identity / #206 — **through the ASSEMBLED app** | `test_auth_identity_seam.py` — real lifespan, real MCP `initialize`, real hijack attempt, 4 ordered principal pairs. | 16 |
| 5 | composition — `.well-known` anonymous, 401 `resource_metadata`, Origin 403 with zero outbound calls | `test_auth_composition.py` | 32 |
| 6 | posture gate — mutating tools refused hosted | `test_hosted_readonly_posture.py` (#291's fix: derived set + **equality**, not subset) | 55 |
| +7 | *(not in the assignment)* `PermissionResolver` extension seam — design §4 | `test_permission_resolver_seam.py`, incl. a NON-pass-through fake proving the seam can actually filter | 14 |
| +8 | *(not in the assignment)* retired surface, `ApiKeyVerifier`/Origin preservation, config boundary | `test_auth.py` (rewrite) | 53 |

### ⚠ NOT DISCHARGED — clause: *"Ships with a satisfiability receipt."*

A satisfiability receipt is *0-failed against a known-correct build*. **Producing one requires
BUILDING the implementation**, which my spawn brief forbids twice (*"Do not run a builder. Do
not implement"*; writable set = TEST FILES ONLY). Brief-base precedence puts the spawn brief
above a later message, so I did not build one.

**Where it must come from instead:** the `contract-adversary` must build a reference
implementation anyway in order to grade the contract — that is the natural instrument, and
CLAUDE.md names it as such. The obligation is written into §9 item 6 of this report, including
the harder leg (*still satisfiable AFTER the ruff-driven orphaned-import cleanup that deleting
`BearerAuthMiddleware` forces*) and the two pins I am least confident are satisfiable as
written. **This clause is OPEN until the adversary reports it, and the wave should not treat
the contract as approved before then.**

### ⚠ NOT DISCHARGED — ledger row for task 2

Brief-base §5 requires me to drive my own row `claimed → in_progress → done`. **I cannot: the
lore MCP tools are absent from my toolset** (§1 — three `ToolSearch` attempts across two
sessions, including the assignment-time retry, all returned `No matching deferred tools
found`). `lore_claim_task` / `lore_tasks` are among the tools I do not have.

**The lead must transition row 2 manually**, and — per the verification law — the receipt for
task 2 is **this file plus the eleven test files**, not a ledger state. The underlying gap
(a contract-authoring agent required by project law to prefer an indexed code tool while
lacking the tool to reach one) is the same class as the 2026-07-28 `contract-adversary`
finding and wants an agent-definition fix, not a smaller brief.

---

## 14. REVISION — the lead's rulings applied (2026-07-31, after the first delivery)

Ten escalations ruled. One required a contract change; nine confirmed readings I had already
taken. Every edit below is in the test tree only; no production file, design doc or git state
was touched.

### 14.1 ⚑ S5 — INVERTED. The residual window is pinned CLOSED.

**Ruling:** stat on EVERY verification, cache hits included; a revoked principal is denied on
the FIRST verification after the edit; there is no residual window. The earlier
*"one `stat` per cache-MISS"* wording was a performance floor the operator wrote carelessly,
not a licence to cap revocation speed.

| action | detail |
|---|---|
| **DELETED** | `TestTheResidualWindowIsAKnownBound::test_a_cached_principal_survives_until_the_next_cache_miss`, including its `#137/#138`-style *"if you closed this deliberately"* message — **that message is now FALSE**, because the closure IS deliberate. A pin asserting a hole that is closed is a false statement about the system, so it is deleted rather than skipped or inverted in place. A short historical note survives in the replacing class's docstring so a future reader knows the pin existed and why it went. |
| **ADDED** | `TestRevocationIsEffectiveOnTheVeryNextVerification` — 4 pins: the cached-principal denial with **no intervening miss**; the token cache is **not flushed** by a roster edit (W19b); immediate re-admission after a re-add; a roster going empty denying a warm token at once. |
| **ADDED** | `TestRosterFreshnessOnEveryVerification` — 3 pins: every verification stats (mechanism); an unchanged roster is **not re-read** (the surviving performance property); a changed roster **IS** re-read (its control). |
| **REPLACED** | `_RosterProbe.force_a_cache_miss` → `_RosterProbe.verify_expecting_a_cache_hit`. The old helper existed only to work around the residual window. The new one **asserts the outbound call-count did not move**, so every denial pin proves it was served from a genuine cache HIT — the lead's *"asserted by outbound call-count so the pin cannot pass because caching is broken"*, applied at the helper so it holds for every call site rather than one bespoke test. |
| **SIMPLIFIED** | `TestRosterFailsClosedAtRuntime::test_every_principal_is_denied_when_the_roster_is_broken` no longer drives a miss, and now asserts the denial is a cache HIT — which **strengthens** it: a broken roster must not send every live token back to Google (an operator's bad edit must not become an outbound stampede). |
| **DOCSTRING** | The module's "freshness model" section rewritten to state the ruling, cite that design §9 group 1 already carried the strong form, and name the two consequences every fixture depends on. |

**Mutation rider, written INTO the test file** (`TestRevocationIsEffectiveOnTheVeryNext
Verification`'s docstring) so it travels with the pin rather than living only here:

```
mutation: move the roster `stat` to the token-cache MISS path only
expected RED   : …TestRevocationIsEffectiveOnTheVeryNextVerification::
                     test_a_revoked_principal_with_a_cached_token_is_denied_immediately
                 …TestRosterFreshnessOnEveryVerification::
                     test_every_verification_stats_the_roster_including_cache_hits
expected GREEN : …TestRosterIsLiveRuntimeStateNotBootConfig::
                     test_an_uncached_principal_revoked_mid_process_is_denied
                 …TestRosterFreshnessOnEveryVerification::test_an_unchanged_roster_is_not_re_read
```

The GREEN half is not decoration: **a mutation that reds everything proves nothing about
WHICH property is guarded.** Ids come from `--collect-only`, diffed both ways
(`scripts/mutation_proof.py`). The builder owes the run — I cannot mutate production code
that does not exist yet.

⚠ **The one place two pins nearly contradict, flagged for the adversary.**
`test_an_unchanged_roster_is_not_re_read` asserts an unreadable roster **keeps serving**;
`test_an_unreadable_roster_denies_everyone` asserts an unreadable roster **denies**. They pin
the two sides of design R12's mtime rule — the distinguishing input is whether the mtime
MOVED — and a cross-reference comment now sits on both so neither can be "simplified" into the
other. §9 item 7 tells the adversary to check these first.

### 14.2 S1 — ACCEPTED, and pinned (you said a pin was welcome)

`TestUnknownPathsAre404NotChallenged`, 6 pins: 5 unknown paths answer **404** for an anonymous
caller, plus the control that `/mcp` is still **401**. The control is what stops the bound
widening — a build that 404'd `/mcp` would otherwise pass the whole class. The docstring cites
the ruling and design §8 row 15 (`dropped-deliberately`), and says plainly that a future
re-gating must update pin and design row together.

### 14.3 B1 — verified, not taken on trust

`cachetools` **7.1.6** installed (`importlib.metadata.version`), declared at
`loremaster/pyproject.toml:39`, `import cachetools; cachetools.TTLCache` resolves. Cache pins
unchanged — they assert behaviour and name no library, which is what let this ruling land
without touching a single test.

### 14.4 The design-doc consistency sweep — RAISED, then VERIFIED ALREADY FIXED

I flagged that §3-R12 was not the only site carrying the weak form, and that the dangerous
one was **§1's threat-model verdict** — the sentence an auditor is explicitly told to reason
from (*"so an auditor need not re-litigate intent"*). Left stale, it would have meant a future
auditor correctly identifying an immediate-revocation failure and **classifying it as
accepted**.

**Re-checked on disk after the lead's `591c00c` rather than assumed** (a fix you are told
about is a rumour until you read it):

| site | state |
|---|---|
| §1 threat-model verdict | ✅ **FIXED** — now reads *"a principal removed from the roster file is admitted on ANY later verification — BLOCKER. There is no residual window (R12, restored ruling): the roster mtime is `stat`-checked on EVERY verification, cache hits included…"* |
| §3-R12 freshness bullet | ✅ FIXED |
| §9 group 1 | ✅ needed no change — it carried the strong form all along |
| §14 packages table (`watchdog` row) | ✅ FIXED — *"one `os.stat` mtime compare per VERIFICATION"* |
| §10 kill switches, §4, §12 | ✅ consistent |

`grep -n "residual" docs/design/2026-07-31-packet39-google-oauth.md` returns **9 hits, all of
them now asserting the STRONG form or explicitly recording the supersession**. Nothing left to
do; recorded so the sweep is on the record rather than remembered.

**The durable lesson, which is the part worth keeping:** the design contradicted ITSELF before
this packet started — §9 carried the strong form while §1 and §3-R12 carried the weak one — and
a contract author following the doc faithfully will pin whichever half they read first. I read
§1 and §3-R12, so I pinned the hole OPEN. This is CLAUDE.md's #1 defect class (*natural-language
surfaces whose consistency with code no gate checks*) occurring **inside the spec that governs
the packet**, where no gate of any kind was ever going to see it. The only instrument that
caught it was escalating rather than choosing silently.

### 14.5 §8 re-verified after S5 (you asked)

**The out-of-scope edit list is UNCHANGED — no new items, none removed.** Re-derived rather
than assumed: S5 moves work inside `LoreTokenVerifier`'s roster/cache seam, which is production
code the builder writes from scratch, so it creates no new obligation in a file I cannot touch.
Re-checked all five entries by bare anchor-free grep. Items 1–3 (`test_eager_startup.py`'s
bearer-outermost pin · `test_mcp_server.py`'s `_MUTATING_TOOLS` · `test_retired_symbols.py`'s
`_RETIRED_SYMBOLS`) stand exactly as written. Item 4 (`cachetools` in `pyproject.toml`) is
**DONE** by you. Item 5 remains a no-edit note. §14.4's design-doc sites are lead/design work,
not builder work, so they are listed there rather than folded into §8.

### 14.6 Gates re-run after the revision

```
uv run ruff check .                                              → All checks passed!
./scripts/typecheck.sh                                           → 170 errors, ALL the
                                                                   "symbol does not exist yet"
                                                                   class, all in authored files
                                                                   (unchanged classes; §6)
uv run pytest loremaster/tests/test_eager_startup.py \
              loremaster/tests/test_mcp_server.py -n auto -q      → 657 passed in 104.39s
uv run pytest $CONTRACT --collect-only -q                        → 422 tests collected
uv run pytest $CONTRACT -n auto -q --tb=no                       → 389 failed, 33 passed
```

Nothing outside the contract moved. The 33 GREEN are the same 33 as before the revision —
verified, not assumed — so no new pin passes by accident.

---

## 15. Resend audit (lead resent the S5 message 2026-07-31, believing it lost)

**It was not lost — I received it and the work shipped before the resend arrived.** The
inbox bug is real, but this was a false positive on the detection side: the evidence the
lead checked was the report, and the report's §14 was (and still is) UNCOMMITTED, while the
test tree had already been committed by the lead themselves as `6e9e845` *"the Google-OAuth
contract — 422 pins, 389 RED"* — a count that only exists post-S5. **The artifact that
proved receipt was the commit the lead made, not the file they read.** Recorded because
"proof of receipt = the recipient's own artifact" only works if you check the right artifact.

I re-audited the resend line-by-line rather than assuming it matched what I did. **Nine of
ten items matched. The tenth found three real stale-prose defects — all mine.**

### The item that earned the resend: the SECOND pin to delete

The resend adds *"I missed the second in my lost message; your own §4 table found it"* —
`test_a_cache_hit_performs_no_roster_stat`. **Already handled**: the whole
`TestRosterFreshnessBudget` class (that pin + `test_each_cache_miss_stats_at_most_once`) was
replaced by `TestRosterFreshnessOnEveryVerification`, whose first pin
`test_every_verification_stats_the_roster_including_cache_hits` is its exact inverse.
Verified by bare, anchor-free grep across `loremaster/ lorerunes/ lorescribe/ loresigil/
scripts/ docs/` + the report: **zero surviving references in any test file.**

### Three stale-prose defects the audit found, now fixed

| # | defect | why it mattered | fix |
|---|---|---|---|
| 1 | `test_auth_composition.py`'s S1 docstring cited **design §8 row 14**. The doc on disk says **row 15**; row 14 is the retired-``__all__`` row. | The resend also said "row 14" — the lead wrote the message before finalising the doc. **The doc is ground truth, not the message.** Left alone, a future reader following the citation lands on an unrelated adjudication and concludes the bound was never ruled. | Corrected to **row 15**, with an inline note recording that the ruling message said 14 so the discrepancy is not silently re-introduced. |
| 2 | §9 item 6 named `test_a_cache_hit_performs_no_roster_stat` as one of the two pins least likely to be satisfiable — **a pin that no longer exists** — and said "all 413 pins". | This is the adversary's work order. Pointing it at a deleted pin wastes the one pass that grades the contract. | Re-aimed at `test_an_unchanged_roster_is_not_re_read` (its `chmod`-with-mtime-untouched instrument is now the riskiest fixture in the contract) and corrected to **421**. |
| 3 | §2's `cachetools` row still read **NOT INSTALLED / BLOCKED**. | The package survey is the artifact whose whole purpose is to be trustworthy about what was actually checked. A stale "blocked" row is the survey lying about its own subject. | Updated to **7.1.6**, commit `71a53e3`, `pyproject.toml:39`, re-verified on disk — with the original state kept visible (`was NOT INSTALLED at contract time`) rather than overwritten, since §4's wrong-build table was reasoned against it. |

**All three are the class this repo audits hardest — natural-language surfaces whose
consistency with code no gate checks — and all three were introduced by the revision that
fixed a defect of exactly the same class.** Nothing in the gates could see any of them:
ruff, mypy and pytest were green across all three.

### One item for the lead, in the design doc (not mine to edit)

`docs/design/2026-07-31-packet39-google-oauth.md` §15 still carries the S5 entry in the
**imperative, future tense**: *"The lead is instructing the contract author to INVERT the
`TestTheResidualWindowIsAKnownBound` pin — it currently ASSERTS the hole exists"*. Both
clauses are now false: the pin is deleted and the instruction is discharged. It reads as
outstanding work. Suggested replacement: *"S5 — ruled and DISCHARGED (`6e9e845`): the
residual-window pin is deleted; `TestRevocationIsEffectiveOnTheVeryNextVerification` and
`TestRosterFreshnessOnEveryVerification` replace it."*

### Counts, re-derived with the exact command (unchanged by the three fixes — they are prose)

```
CONTRACT="lorerunes/tests loremaster/tests/test_auth.py loremaster/tests/test_google_token_verifier.py \
 loremaster/tests/test_allowlist_roster.py loremaster/tests/test_auth_composition.py \
 loremaster/tests/test_auth_identity_seam.py loremaster/tests/test_hosted_readonly_posture.py \
 loremaster/tests/test_permission_resolver_seam.py"
uv run pytest $CONTRACT --collect-only -q   →  422 tests collected
uv run pytest $CONTRACT -n auto -q --tb=no  →  389 failed, 33 passed
uv run ruff check .                         →  All checks passed!
```

**§8 re-confirmed complete and exact** after the cache-seam edit — see §14.5; the list is
unchanged, item 4 (`cachetools`) discharged by the lead.

Finding **#294** acknowledged; not carried further. Ledger row 2 is the lead's to transition.

---

## 16. ADVERSARY VERDICT INSUFFICIENT → all nine missing pins closed (2026-07-31)

`REPORT-adversary-39-auth-1.md` (`892ba02`): 45 wrong builds, **12 survived all 422 pins**.
Read in full. The verdict's one-sentence diagnosis is the thing worth carrying forward, and
it indicts a habit of mine, not nine isolated oversights:

> **the invariant was pinned at the seam where it was reasoned about, not at the seam where
> it is enforced.**

The guard was pinned at `mcp.call_tool` and is enforced on the wire. The boot refusal was
pinned at `resolve_posture` and is enforced at `build_mcp_server`. The loopback claim was
pinned at the pure function and is enforced on `config.server.host`. The edge policy was
pinned at a loopback bind and is enforced at whatever the operator configured. The secrecy
sweep was pinned on the failure path and is needed on every path. **Five survivors, one
mistake, made five times.**

### The nine pins, where each landed, and the wrong build it kills

| M | Kills | New pins | Module |
|---|---|---|---|
| **M1** ⚑ BLOCKER | **WB30** — guard installed as an instance attribute after `_setup_handlers` captured the bound `call_tool`: live for a test, **dead on the wire** | 3 | `test_auth_identity_seam::TestTheReadOnlyGuardFiresOnTheSERVEDPath` |
| **M2** ⚑ fail-OPEN | **WB34** — `build_mcp_server` swallowing `PostureConfigError` → an unauthenticated internet-facing lore | 3 | `test_auth_composition::TestTheBootRefusalReachesTheThingThatActuallyBoots` |
| **M3** ⚑ fail-OPEN | **WB33** — `host_is_loopback` hardcoded `True` → `HOSTED_OAUTH` on a `0.0.0.0` bind | 9 | same class |
| **M4** | **WB28** — `EdgePolicy.allowed_hosts` ignoring the configured bind → **421 on the deployment shape that exists today** | 4 | `test_auth_composition::TestEdgePolicyIsOneDerivationFeedingBothLayers` |
| **M5** | **WB42/WB42b** — the raw token logged on the **ADMITTED** path | 2 | `test_google_token_verifier::TestTokenSecrecy` |
| **M6** | **WB41** — roster change detection keyed on `st_size` | 2 | `test_allowlist_roster::TestRosterChangeDetectionSurvivesASameLengthEdit` |
| **M7** | **WB40** — the served refused-set section is a HAND-LIST | 1 | `test_hosted_readonly_posture::TestInstructionsAreHonestAboutThePosture` |
| **M8** | **WB35** — the `LOOPBACK` edge policy trusting claude.ai | 1 | `test_auth_composition` |
| **M9** | **WB45** — `required_scopes=[]` | 1 | `test_auth_composition` |

**+26 pins, and the delta reconciles exactly:** 3 + 3 + 9 + 4 + 2 + 2 + 1 + 1 + 1 = 26;
422 + 26 = **448**.

### Three places I did NOT take the adversary's code verbatim, and why

A fix wave is written by someone who has just been told what they missed — the state most
likely to produce a narrow patch satisfying the letter of a finding. So each of these is a
*widening*, and each is stated so the delta pass can judge it:

1. **M7 — I did not import `_install_hosted_instructions`.** The proposed pin calls that
   private production function and re-runs it by hand. That would make an internal helper's
   NAME part of the contract, and it only proves the section follows **one added tool**.
   Instead the pin **monkeypatches the shared `_READ_ONLY_ANNOTATIONS` constant and
   rebuilds** — the repo's own *prove sharing by MUTATION* instrument. A derived section
   then names all fifteen tools; WB40's hand-list still names six. It forces no internal
   name and kills a larger class.
2. **M3 — I added the ENFORCEMENT leg the proposal did not have.** The adversary's M3 pins
   `resolve_posture`; but WB34's whole lesson is that `resolve_posture` is not what boots. So
   `test_build_mcp_server_also_refuses_a_non_loopback_hosted_bind` pins the same property at
   the seam that enforces it. Pinning M3 only where the adversary suggested would have
   repeated the exact mistake M2 exists to correct.
3. **M4 — I pinned BOTH Host forms, from an SDK fact neither survey's read column carried.**
   The adversary's §2 row 2 measured it: `_validate_host` matches `"h:*"` only via
   `host.startswith(base + ":")`, so a **port-less** `Host: lore.firehawktransam.org` — what
   a proxy forwards for `:443` — is **421ed by a `:*`-only policy**. My original pin used
   `host.split(":")[0] == …`, which a `:*`-only policy satisfies. Now both the bare and the
   `:*` form are required. Also parametrised the configured-bind pin over **three** addresses,
   because one value is how a monoculture starts.

### The M1 marker is derived, not typed

`hosted_refusal_marker()` reads `Posture.HOSTED_OAUTH.name` off the enum rather than
hard-coding the string. A hand-typed marker that stops matching after a rename makes a wire
pin go **green while checking nothing** — which is the same class of defect as WB30 itself.

### ⚑ §8 CORRECTED — it was short by three, and the adversary's method is the lesson

My §8 claimed a bare anchor-free grep. **The adversary got the true set by RUNNING the
reference build against the rest of the suite and letting the consumers enumerate
themselves** — an instrument the frame cannot bias, which a grep for names I already knew
structurally cannot be. Four collateral reds; I had listed one.

| # | Site | Status | Required edit |
|---|---|---|---|
| 1 | `test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost` | listed ✓ | rewrite → `OriginValidationMiddleware` outermost + 401-for-keyless |
| 2 | **`test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated`** | ⚑ **WAS MISSED** | imports `BearerAuthMiddleware`, asserts `not isinstance(...)` → delete or rewrite against `OriginValidationMiddleware` |
| 3 | **`test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware`** | ⚑ **WAS MISSED** | asserts `isinstance(app, BearerAuthMiddleware)` — a live corpse asserting the retired composition. Its config is a valid `LAN_BEARER` shape, so the replacement is a 401-for-keyless assertion |
| 4 | **`test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true`** | ⚑ **WAS MISSED** | asserts the RETIRED field still exists and defaults `True` → delete |
| 5 | `test_mcp_server.py::_MUTATING_TOOLS` + `test_mutating_tools_are_not_marked_read_only` | listed ✓ | DELETE. Confirmed by the adversary: it did **not** red on a correct build, because it is a subset check — #291's diagnosis exactly |
| 6 | `test_retired_symbols.py::_RETIRED_SYMBOLS` | listed ✓ | add `BearerAuthMiddleware`, `AuthVerifier`, `tls_terminated_upstream` **in the same commit that deletes them** |
| 7 | **`loremaster/loremaster/config.py` module docstring** (names `tls_terminated_upstream`) | ⚑ **prose site, was missed** | rewrite — the "natural-language surfaces no gate checks" class |
| 8 | **`loremaster/loremaster/server.py::build_asgi_app` docstring** (names `BearerAuthMiddleware`) | ⚑ **prose site, was missed** | rewrite |
| 9 | `loremaster/pyproject.toml` — `cachetools` | **DONE** by the lead (`71a53e3`) | — |
| — | `loremaster/loremaster/calibration/corpus/comment_light_python.py.txt:200,207` | ⚠ **DO NOT EDIT** | a frozen calibration corpus sample; editing perturbs the token baseline. Named so a blind sweep does not "fix" it |
| — | `lore.yaml`, `lore.yaml.sample`, `skills/lore-deploy/` | **CLEAN** | no `auth:` block, no retired field — the `extra="forbid"` migration breaks no live config on this host |

### `google-auth` — the empty read column, SETTLED BY EXECUTION

Both surveys carried this row with **nothing read**. Run
(`uv run --with google-auth python …`, **google-auth 2.56.2**):

| question | answer |
|---|---|
| Public API of `google.oauth2.id_token` | `verify_oauth2_token`, `verify_token`, `verify_firebase_token`, `fetch_id_token`, `fetch_id_token_credentials` |
| `verify_oauth2_token`'s own first docstring line | *"Verifies an **ID Token** issued by Google's OAuth 2.0 authorization server."* |
| Any opaque-**access**-token introspection API? | **No.** |
| ⚠ Does the string `tokeninfo` appear in the tree? | **YES** — `google/oauth2/credentials.py:55` defines `_GOOGLE_OAUTH2_TOKEN_INFO_ENDPOINT = "https://oauth2.googleapis.com/tokeninfo"` |
| Is that constant USED? | **NO.** `grep -rn _GOOGLE_OAUTH2_TOKEN_INFO_ENDPOINT` over the whole installed tree returns **exactly one line — its own definition.** Private, dead, no caller. |
| `pluggable.py`'s `tokeninfo` hits | `self._tokeninfo_username` — an executable-sourced credential's username field. Unrelated. |

**Verdict `bespoke`, now EARNED rather than inherited.** The design's substance was right —
there is no usable opaque-access-token introspection API — but the evidence is more
interesting than the claim, and worth recording precisely: **a future engineer grepping
google-auth for `tokeninfo` WILL get a hit and may conclude the library supports it.** It
does not; the constant is dead code. That is exactly the kind of fact an empty read column
hides, and it is why the column is mandatory.

### Not changed, per the lead

Satisfiability receipt **DISCHARGED** (422 passed / 0 failed on the reference build, ruff
clean, post-cleanup leg included) — §9 item 7's mutual-satisfiability question resolves YES,
and both pins I flagged as possibly unsatisfiable are satisfiable. The 33-GREEN enumeration
reproduces item for item and is untouched. Mental model rebased to `892ba02`.

### Gates after the fix wave

```
CONTRACT="lorerunes/tests loremaster/tests/test_auth.py loremaster/tests/test_google_token_verifier.py \
 loremaster/tests/test_allowlist_roster.py loremaster/tests/test_auth_composition.py \
 loremaster/tests/test_auth_identity_seam.py loremaster/tests/test_hosted_readonly_posture.py \
 loremaster/tests/test_permission_resolver_seam.py"

uv run pytest $CONTRACT --collect-only -q   →  448 tests collected
uv run pytest $CONTRACT -n auto -q --tb=no  →  415 failed, 33 passed
uv run ruff check .                         →  All checks passed!
./scripts/typecheck.sh                      →  186 errors, ALL the "symbol does not exist yet"
                                               class, all in the 11 authored files
uv run pytest test_eager_startup test_mcp_server test_config \
             test_retired_symbols test_secret_leak_vectors -n auto -q  →  971 passed
```

**33 GREEN, unchanged** — none of the 26 new pins passes by accident. One genuine typing
defect of mine surfaced and was fixed rather than ignored (`hosted_refusal_marker` returned
`Any`).

### One recommendation to the lead, from the adversary and endorsed

`git add /home/ejprice/scratch/adv39_wrong_builds.py` → `scripts/adv39_wrong_builds.py`. It is
a 774-line 45-entry wrong-build registry at an **unrecoverable address by standing law**, and
it is the instrument behind this whole grade. Finding #278 is the receipt for what happens
otherwise: the better the instrument, the more likely it dies unremarked.

---

## 17. DELTA adversary + the design change (R13/R14/R15) — third revision, 2026-07-31

`REPORT-adversary-39-auth-2.md` (`003e856`) and design `R13/R14/R15` (`d615648`), both read
in full. **10 of the 12 prior survivors killed; all nine of my previous pins discriminate.**
Insufficient again because 9 new wrong builds passed all 448 pins — and because **the design
changed underneath the posture pins, so this was a RESHAPE, not an extension.**

### The lesson, which is the whole packet in one line (finding #295)

> **Every refusal pin observed the EXCEPTION. None observed the EFFECT.**

WB48 put the guard *after* `super().call_tool`: 448/448 green, **including my new wire pin**,
whose response body carried the `HOSTED_OAUTH` marker **byte-identically to the correct
build's** — and the tool body had already executed (`invocations=1` vs `0`). Same exception,
same bytes, opposite reality. The memory row is written and the caller is then politely told
it may not write.

M1 asked *"does the guard run on the SERVED path?"* and answered it. **It never asked "does
the guard run BEFORE the thing it guards?"** — and order is not observable from a message.

**The askable form, now written into the test class so it travels with the pin:**
*"if the guard ran AFTER the thing it guards, would this pin still pass?"*

### R13 — reshaped, not extended

The design's answer is to stop guarding invocation: the guard is a **scoped LOOKUP**. Upstream
`ToolManager.call_tool` is `tool = self.get_tool(name); … await tool.run(...)` — **read at the
installed SDK** — so the run's operand *is* the lookup's return value and enforcement order is
a data dependency the SDK writes, not a sequence a builder authors. Placement stops being a
free variable after two waves in which placement was the entire defect.

| new class | what it pins |
|---|---|
| `TestARefusedToolNeverRUNS` (4) | the **derived ∀ EFFECT pin** — wraps `Tool.run` at its ENTRY (upstream of argument validation, so `arguments={}` can no longer mask a body that ran), iterates the FULL registry, asserts refusal **and** zero entries. Plus **two controls**: a synthetic no-required-arguments mutating tool proving the recorder can SEE a body execute, and a read tool proving dispatch still happens. |
| `TestTheScopedLookupIsTheEnforcementSeam` (4) | a hosted principal's `list_tools` omits refused tools · unauthenticated lookup is **unfiltered** (protects `test_mcp_server`'s exact-set pin and the local deploy) · api-key sees the full surface · the composed `_tool_manager` is a **subclass** of the SDK's, never the stock one |
| `TestExtensionToolsAreRefusedWholesale` (3) | R14 |

The ∀ effect pin is derived over the registry, so there is no "tool nobody wrote a counter
for" — and its **positive control is not optional**: a recorder that never fires would make
the ∀ vacuous on every build, WB48 included.

### R14 — a ∀ pin of mine that was FALSE on the correct build

`test_every_registered_tool_carries_an_explicit_read_only_hint` passed **only because its
fixture registered no extensions**. `_register_extension_tools` calls `add_tool(...)` with no
`annotations=`, and `ToolSpec` is `extra="forbid"` with no field to carry one. That is the
quantifier law's own shape — *a ∀ evaluated only where the branch cannot fire* — and it was in
**my** contract, in the pin whose whole job is exhaustiveness. It is now **parametrised over
the registration path** (`core-only` / `with-extension`), and `hosted_server` gained a
`with_extension` leg whose docstring records why it exists.

### R15 — the unknown branch

WB51's `except ValueError: return True` passed **all six** host pins from the previous wave.
Every one of those six is a value any classifier is certain to recognise. **The generalisable
shape, now written into the pin:** *when a contract pins only values a classifier certainly
knows, the UNKNOWN branch is unpinned — and the unknown branch is where the fail-open default
lives.* Five unrecognised hosts now refuse (including `""`, uvicorn's all-interfaces
spelling), with `LOCALHOST`/`LocalHost` as the control against over-tightening — a gate that
refuses honest configs is a gate that gets switched off.

### WB50/WB50b — a served surface that LIES, in the direction nobody pinned

My M7 pin computed `missing = [n for n in derived if n not in section]`: a **membership** check
in one direction, which a **superset** satisfies trivially. A build naming all fifteen tools as
refused served a paragraph calling `lore_search` refused *and* available in the same breath.

Both clauses are now pinned by **EQUALITY against the derivation** — over-claim and under-claim
both red. That required one new exported constant, `HOSTED_READ_LADDER_MARKER`, so the clause
split is owned by production prose rather than hardcoded in the test.

### The lead's item — the twin is deleted

`running_asgi_app`'s ~30 hand-rolled lines are gone; it is now
`asgi_lifespan.LifespanManager(app, startup_timeout=5, shutdown_timeout=5)`. It stays a
one-line **policy function** rather than being inlined at 16 call sites — one home for the
timeout policy, which the hand-roll never had at all. **Verified by execution, not inspection:**
`test_an_unauthenticated_initialize_succeeds` (the one lifespan pin green today) still passes.
My original `keep_with_trigger` verdict named the trigger; the package was installed at
`93bd193` and the trigger fired without anyone re-running the decision. Fair catch.

### Not adopted verbatim — one place, declared

The adversary's N2/N3 split the section on the literal string `"The read ladder"`, binding
production prose into a test. Mine splits on the exported `HOSTED_READ_LADDER_MARKER` and
asserts **set equality** rather than two one-directional membership checks — so a build that
names an extra tool in the *available* clause also reds. Strictly wider, and it forces no prose.

### Counts

```
CONTRACT="lorerunes/tests loremaster/tests/test_auth.py loremaster/tests/test_google_token_verifier.py \
 loremaster/tests/test_allowlist_roster.py loremaster/tests/test_auth_composition.py \
 loremaster/tests/test_auth_identity_seam.py loremaster/tests/test_hosted_readonly_posture.py \
 loremaster/tests/test_permission_resolver_seam.py"

uv run pytest $CONTRACT --collect-only -q   →  472 tests collected
uv run pytest $CONTRACT -n auto -q --tb=no  →  439 failed, 33 passed
uv run ruff check .                         →  All checks passed!
./scripts/typecheck.sh                      →  200 errors, ALL the "symbol does not exist yet"
                                               class, all in the 11 authored files
uv run pytest <6 sibling modules> -n auto   →  1018 passed
```

**+24, and the delta reconciles exactly:** N1 4 · scoped-lookup 4 · extension 3 · N2/N3 2 ·
∀-classification parametrisation +1 · N4 7 · N8 1 · N6 1 · N7 1 = **24**; 448 + 24 = 472.
**33 GREEN, unchanged for the third revision running** — no new pin passes by accident.

### For the third delta pass

Two things I would attack if I were grading this:

1. **The `Tool.run` recorder is a monkeypatch on an SDK class.** Its positive control proves
   it fires, but a build that dispatches through something other than `Tool.run` would be
   invisible to it. I could not find such a path in the installed SDK (`ToolManager.call_tool`
   is the only caller), but I did not prove the negative.
2. **`test_the_composed_server_installs_a_SCOPED_tool_manager` asserts a subclass, not a
   behaviour.** It is the cheap structural half R13 asks for; the behavioural half is the
   effect pin. If a build subclasses `ToolManager` and overrides nothing, the structural pin
   passes — and the effect pin is what must catch it. That pairing is deliberate, but it is
   the seam I would probe first.

**Still open and unchanged:** N5's design gap is now ruled (R14) and adopted. **N9 — the
truncated-cache-key ruling (adversary §10-R1) — remains an operator call and I have NOT pinned
it**: a 32-bit positive-cache key means a token colliding with a previously-ADMITTED one is
served that principal's verdict, and no cheap behavioural pin exists because a collision is not
constructible without a preimage. The honest options are a structural pin that the key
expression is a full `hexdigest()`, or accept-and-ledger with a named re-open trigger.
