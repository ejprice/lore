# REPORT-security-59 — packet-59 fastmcp 3.x migration SECURITY audit

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Model attestation (brief-carried, cannot self-read):** `claude-opus-4-8` (Opus 4.8),
  `opus48-worker` pin. ✓
- **Demanded vs. have:** Read of the writable/audit set — `server.py` (599KB, read by symbol via
  `lore_get_symbol` + targeted `Read`/grep), `auth.py`, `logging_setup.py`, `config.py`,
  `store/{surreal,_txn,lease}.py`, `embedding.py`, `test_migration_wire.py`,
  `test_eager_startup.py`, design §5b, `REPORT-{builder,spike}-59.md`, and the installed
  `fastmcp`/`uvicorn` source (✓). lore tools (`ToolSearch "+lore"`, ✓ loaded). Report-only; I
  edit no code. **No blocker — the audit ran end to end.**
- **Tool honesty (SAID OUT LOUD, dogfood §3):** the lore **prod** store `ws://127.0.0.1:18500/rpc`
  flapped repeatedly this session — `lore_search`, several `lore_get_symbol`, and BOTH attempts to
  file a `lore_findings` friction row failed with `no close frame received or sent` / bare-UUID
  errors (some `lore_get_symbol` calls in the same window succeeded, so it is intermittent, not a
  hard outage). I fell back to direct `Read` + `bash grep` for every structural fact below (a
  sanctioned fallback: non-symbol textual seams + exhaustiveness of error-string sites). **The
  friction finding could NOT be filed** (store down at both attempts) — its full text is preserved
  in §FRICTION for the lead to file when the store recovers.

## SUMMARY BLOCK
- state: **done**
- verdict on the migration's security surface: **NO HIGH/CRITICAL FINDING.** The Host/Origin/Bearer
  gates are correct and FAIL-CLOSED; auth composition and lifespan delegation are preserved (wire-proven
  8/8 by builder-59). Two LOW findings + two verified-clean areas, below.
- **FLAG 4 verdict: builder-59's ACCEPT-with-trigger is SOUND** (LOW severity). The migration does
  NOT weaken the PRIMARY secret control (`SecretStr` at every resolution seam, #211 — unchanged); it
  drops a belt-and-suspenders layer whose only residual value is a narrow, pre-production,
  local-boot-log, total-failure-only window. I recommend a cheap OPTIONAL hardening (§F1) but do not
  require a re-pin.
- deviations: none (report-only, in-scope).
- Packages considered: **none — no mechanism specified** (auditor; I built nothing).
- Reuse ledger: **none** (no new symbol introduced — report-only).
- Graded: `ee4bced` · HEAD-at-report: `ee4bced` · **SAME.** (Audited the uncommitted working tree
  over `ee4bced404af1bd17fa756e84ff96a4625d9f82d`; `git merge-base --is-ancestor` confirms same base.
  server.py/auth.py/logging_setup/config/store are working-tree-modified per `git status` — that IS
  the migration under audit.)
- decisions-needed for lead-59: (1) FLAG 4 — ACCEPT the drop (my rec) vs. adopt the §F1 hardening;
  (2) whether to promote `LORE_ALLOWED_HOSTS` to a validated `ServerConfig` field + reject `*` before
  the hosted/off-fleet deploy (§F2) — a packet-39 hand-off, surfaced not buried.
- receipt POINTERS: §F4 (FLAG-4 leg-by-leg, source-cited) · §F1/§F2 (findings) · §CLEAN-1/§CLEAN-2
  (verified-no-defect) · §FRICTION (unfiled lore finding).

---

## Findings, ranked by severity

### [LOW] F4 — the dropped secret-safe boot-failure message: the re-raised exception IS logged unredacted, but there is (by design) almost nothing secret to leak

**Location:** `loremaster/server.py::_eager_build_with_retry` (re-raises last exc);
`loremaster/logging_setup.py::configure_logging` (redaction scope);
`loremaster/store/surreal.py:499,509` + `store/lease.py:318,325` + `store/_txn.py:1215,1232,1494`
(exception strings embedding the URL); the deleted `_EagerStartupLifespan._EAGER_BUILD_FAILED_MESSAGE`.
**CWE:** CWE-532 (Insertion of Sensitive Information into Log File).

**The mechanism, source-confirmed (not inferred):**
1. On total boot failure (all FP-07 attempts exhausted), `_eager_build_with_retry` **RE-RAISES the last
   exception** (fail-closed). The native fastmcp `lifespan=` lets it propagate.
2. **uvicorn logs it UNREDACTED.** `uvicorn/lifespan/on.py:37` logs via `logging.getLogger("uvicorn.error")`;
   line 97 does `self.logger.error("Exception in 'lifespan' protocol\n", exc_info=exc)` (full traceback),
   and lines 121/134 log a `lifespan.startup.failed` `message` (Starlette formats the traceback into it).
3. **The redaction backstop does NOT reach that logger.** `configure_logging` attaches `RedactingFilter`
   ONLY to `LORE_NAMESPACES = ("loremaster","loresigil","lorescribe")` and **deliberately leaves the root
   logger untouched** so as not to fight uvicorn's handler (`logging_setup.py` docstring lines 42–47 +
   616–617). `uvicorn.error` is outside those namespaces ⇒ no filter ⇒ raw text.
4. The re-raised `SurrealConnectionError` embeds **`{self._url!r}`** (surreal.py:499/509), and
   `self._url` is `config.surreal.url` **verbatim** (surreal.py:410 `self._url = url` ← server.py:7214/9091
   `url=config.surreal.url`). The `{error}` tail (surreal.py:510) interpolates the underlying transport error.

**Why this is LOW, not HIGH — the primary control is UNCHANGED and stronger than the filter:**
- The **real credentials never enter lore's own exception strings.** The surreal password is a `SecretStr`
  resolved by `resolve_secret` (config.py:793) and unwrapped in **exactly one place** —
  `store/_txn.py:986 signin_credentials`, `password.get_secret_value()` handed straight to `connection.signin`,
  **interpolated into no log or error in the package** (its docstring says so, verified). The username is
  deliberately non-secret and interpolated nowhere. The embedding `api_key` is likewise `SecretStr`
  (`embedding.py:79`), and `make_embedder_from_config` touches no network at construction (only `.probe()` does).
- `SurrealConnectionError` interpolates only `url`, `namespace`, `database` — **no secret among them** when the
  documented discipline is followed. `SurrealConfig`'s docstring is explicit: root credentials are referenced
  **by env-var NAME, never inlined**; `surreal.url`/`base_url` are plain host:port URLs.
- So `SecretStr` (#211), which redacts by construction in f-strings/repr/tracebacks, is the load-bearing
  control — and it survives the migration entirely (the config/connection seam is untouched).

**The residual leak vector (the only thing the dropped fixed-message ever protected):**
- **(a) Operator inlines credentials into the plain-`str` URL** — `surreal.url = ws://root:hunter2@host/rpc`
  or an embedding `base_url` with userinfo. `url: str` / `base_url: str` are NOT validated against userinfo,
  so this is *possible* though *contrary to documented discipline*. Then the re-raised exception carries the
  credential → `uvicorn.error` logs it unredacted (`SecretStr` cannot help — a `str` URL is not a `SecretStr`).
- **(b) A dependency SDK echoes a secret in an UNCAUGHT error repr** — an auth-rejection from
  `connection.signin` is NOT in the caught set (`_CONNECTION_ERRORS`/`TxnContentionExhaustedError`, surreal.py:503),
  so it propagates uncaught and is re-raised. If the surrealdb SDK's auth-error repr echoes the signin payload
  (which contains the unwrapped password), that reaches `uvicorn.error`. This is dependency-dependent and
  **unverified** (would need a live probe of the SDK's signin-error text) — I flag it rather than assert it. The
  OLD fixed-message interceptor covered this case too (it replaced ALL boot exceptions with a fixed phrase).

**Who reads the boot log:** the local `lore-lore` container's stderr only. lore's sole consumer is the
dogfood fleet (CLAUDE.md PRE-PRODUCTION STATUS). Pre-production, local, total-boot-failure-only.

**VERDICT: ACCEPT the drop is SOUND.** Rationale: the leak requires a discipline-violating inline-cred URL
(a) or an unverified dependency echo (b), in a pre-production local-boot-log total-failure window; the primary
`SecretStr` control is unchanged; and re-introducing the deleted interceptor to catch-and-fixed-message would
restore the ~150-LOC apparatus complexity this packet correctly removed. **The re-open trigger is right
(first off-fleet / hosted consumer)** — that is exactly when a boot log becomes reachable by a non-fleet reader.

**Recommended OPTIONAL hardening (§F1 below), strictly cheaper than the interceptor** — offered, not required.

---

### [LOW] F1 — close the ONLY residual FLAG-4 vector at the source: reject userinfo in `surreal.url`/`base_url`

**Location:** `loremaster/config.py::SurrealConfig.url` / `EmbeddingConfig.base_url` (both `: str`, unvalidated).

**Why:** the entire residual leak surface in F4-(a) is "an operator put `user:pass@` in a URL that then reaches
an unredacted log." A 3-line pydantic field validator that **fails loud at config load** if the URL contains a
userinfo component (`urlsplit(url).username`/`.password` is not None) makes that scenario *unrepresentable* —
the same "close the hole cheaply / a gate needs the honest-operator threat model" pattern lore already uses.
It costs nothing on the serving hot path (validation is at load), does not reintroduce the deleted interceptor,
and turns "a credential might leak into a boot log" into "a credentialed URL never validates." This is the
**honest-operator** control (matching lore's exec-seam threat-model doctrine): it catches the operator who
inlines a credential by habit, not a hostile author.

**Failure scenario without it:** operator writes `surreal: {url: "ws://root:pw@db.internal:8000/rpc"}` (a shape
every DB tutorial teaches), SurrealDB is briefly down at container boot, all FP-07 retries exhaust,
`SurrealConnectionError("could not connect to SurrealDB at 'ws://root:pw@db.internal:8000/rpc' ...")` is
re-raised and `uvicorn.error` logs it → `root:pw` sits in the container boot log.

**Note:** this is a CONFIG-SCHEMA change (out of my writable set and arguably out of packet 59's migration
scope) — surfaced for the lead to route (adopt in 59, defer to 39, or ACCEPT F4 as-is). Not a blocker.

---

### [LOW] F2 — `LORE_ALLOWED_HOSTS` is an unvalidated ENV knob and accepts `*` (fail-open by misconfig)

**Location:** `loremaster/server.py::_resolve_allowed_hosts` + `_ALLOWED_HOSTS_ENV = "LORE_ALLOWED_HOSTS"`;
fastmcp `server/http.py::_host_matches` (line 157: `if pattern == "*" or fnmatchcase(host, pattern)`).

**Two operational footguns (neither breaks the current local deploy; both bite the hosted/off-fleet deploy):**
1. **Forget it on a proxied deploy → 421 ALL legit traffic.** TLS is terminated upstream (nginx-ingress,
   `auth.py:13`), so lore sees the PROXIED Host. With `LORE_ALLOWED_HOSTS` unset, `_resolve_allowed_hosts`
   returns just `[config.server.host]` (e.g. `127.0.0.1`); fastmcp's strict guard then 421s the proxied Host.
   This is the **correct security DIRECTION (fail-closed, LOUD — everything 421s, noticed immediately)**, but a
   validated `ServerConfig.allowed_hosts` field would be discoverable and schema-checked instead of a silent env var.
2. **`LORE_ALLOWED_HOSTS=*` (or an over-broad `*.tld`) → allow ALL hosts.** `_host_matches` treats `*` as
   match-all, re-opening the exact Host/DNS-rebinding gap the migration closes. An operator reaching for `*` to
   "make it work" silently disables the benefit.

**Recommendation (packet-39 / hosted hand-off, surfaced not buried):** promote the knob to a validated
`ServerConfig.allowed_hosts: list[str]` field and **reject a literal `*`** (an over-broad allow is a design
decision, not a config typo). builder-59 already flagged the env-vs-field point (§FLAGS 3); this adds the
`*`-fail-open leg and the fail-direction analysis.

---

## Verified-clean (no defect — checked and why, per role §8)

### [CLEAN-1] Fail-safe posture of `host_origin_protection=True` + `_resolve_allowed_hosts` is CORRECT
Answering the brief's ASSESS-1 questions directly:
- **Never fails open.** `_resolve_allowed_hosts` ALWAYS returns at least `[config.server.host]`
  (`ServerConfig.host: str` is a required field), so the list is never empty ⇒ fastmcp's
  `has_explicit_allowed_hosts` is ALWAYS true, AND `host_origin_protection=True` ⇒ `mode="strict"`; either
  condition alone forces host validation (`http.py:280,288,302`). The Host gap "cannot silently reopen"
  (matches `_resolve_allowed_hosts`'s docstring claim — verified against the fastmcp source).
- **UNSET `LORE_ALLOWED_HOSTS` (default) does NEITHER extreme.** Effective allow-set =
  `DEFAULT_HOSTS ("127.0.0.1","localhost","::1")` ∪ `[config.server.host]` ∪ `{scope server bind}` ∪ env entries
  (`http.py:308-318`). On the local deploy (bind `127.0.0.1`), a local client (Host = `127.0.0.1`) is served and
  a spoofed Host (`evil.example`) is 421'd. It is **not** "421 everything" and **not** "allow-all." On a proxied
  deploy that forgets the env, it is fail-closed/loud (F2-1).
- **The env-knob's default posture is the right (fail-closed) DIRECTION.** The only improvement is
  discoverability/validation (F2), not the default behaviour.
- **Wire-proven** (builder-59, `test_migration_wire.py`, 8/8 GREEN on real uvicorn): spoofed Host → 421
  (`test_a_spoofed_host_is_rejected_421`), legit proxied Host via the env knob → not-421
  (`test_a_legit_proxied_host_is_accepted`). Spike-59 Item 3 independently measured 421/200/OFF-gap on a real TCP wire.

### [CLEAN-2] Auth composition preserved + no bypass introduced
Answering the brief's ASSESS-2 questions directly:
- **Order preserved.** `build_asgi_app` builds `inner = mcp.http_app(path, host_origin_protection=True,
  allowed_hosts=…)`, then `OriginValidationMiddleware(inner)`, then (auth enabled)
  `BearerAuthMiddleware(Origin(inner))` → **`Bearer(Origin(http_app))`**, unchanged from the pre-migration wrap
  order (design C3/C4/F1 keep-both). A request is authenticated (401 on bad token) → bespoke-Origin-checked (403)
  → fastmcp Host/Origin-checked inside http_app (421/403) → served.
- **No bypass.** The bespoke wrappers still wrap the fastmcp app; fastmcp's own auth (`RequireAuthMiddleware`/
  `TokenVerifier`) is intentionally NOT installed in packet 59 (`FastMCP(...)` gets no `auth=` kwarg), so the
  bespoke `BearerAuthMiddleware` remains the sole Bearer gate (packet 39 replaces it — design §7). The double
  Origin check (bespoke + fastmcp) is deliberate defense-in-depth, not a regression.
- **Lifespan delegation intact.** Both bespoke wrappers pass non-`http` scopes straight through
  (`auth.py:230-231`, `:312-313`), so the ASGI `lifespan` scope reaches fastmcp's `http_app` and the native
  once-per-process lifespan runs — spike-59 Item 1 GO (negative control: a wrapper that eats the lifespan drives
  the heavy build to zero and fails loud at first request) + `test_migration_wire.py`
  `TestTheHeavyBuildRunsOncePerProcess` (build_calls == 1 across 4 concurrent + 2 sequential sessions).
- **Wire-proven** (builder-59, 8/8 GREEN): bad token → 401 (`test_a_bad_token_is_rejected_401`), bad Origin →
  403 (`test_a_bad_origin_is_rejected_403`).
- **Ordering-sensitive "zero outbound Google call" property is a PACKET-39 concern, not a 59 one.** In 59 the
  Bearer gate is bespoke and local (hmac `compare_digest`, no network — `auth.py:124`), so Bearer-outermost is
  harmless; the fastmcp-guard-before-TokenVerifier ordering (spike Item 2 GO) matters when 39 introduces the real
  OAuth verifier. No action for 59.

### [CLEAN-3] Bearer gate internals unchanged and sound (spot-check)
`ApiKeyVerifier.verify` still uses `hmac.compare_digest` on UTF-8 bytes (timing-safe, non-ASCII-safe → 401 not
500), all-keys-checked (no early-out), empty-token rejected; keys held as `SecretStr` (#211); empty key values
refused at registration (`auth.py:171`). `build_api_key_verifier` fails LOUD on an unset/empty `key_env`
(`resolve_secret` raises `KeyError`). No change in this packet touched these; no new bypass.

---

## §F4 — FLAG 4 leg-by-leg receipts (source citations)
| leg | claim | evidence |
|---|---|---|
| re-raise | total boot failure re-raises last exc | `server.py::_eager_build_with_retry` (`raise last_exc`, fail-closed after budget) |
| uvicorn logs it | unredacted, full traceback | `uvicorn/lifespan/on.py:37` (`getLogger("uvicorn.error")`), `:97` (`error(..., exc_info=exc)`), `:121/:134` (`error(message["message"])`) |
| filter misses it | `RedactingFilter` scoped to lore namespaces only | `logging_setup.py::configure_logging` (`LORE_NAMESPACES` only; root untouched — docstring 42–47, 616–617) |
| url in exc | `SurrealConnectionError` embeds `config.surreal.url` verbatim | `store/surreal.py:410` (`self._url = url`) ← `server.py:7214/9091` (`url=config.surreal.url`); msg at `surreal.py:499/509`, `lease.py:318/325`, `_txn.py:1215/1232/1494` |
| password safe | password never in lore's error strings | `store/_txn.py:986 signin_credentials` (sole `get_secret_value()`, handed to SDK, interpolated nowhere); `config.py:793 resolve_secret` (SecretStr, #211); `surreal.py:499/509` interpolate only url/ns/db |
| api_key safe | embedding key is SecretStr, no network at construction | `embedding.py:79` (`resolve_secret`), `:91-109` (construction touches no network) |
| default config safe | url/base_url are credential-free by discipline | `config.py::SurrealConfig` docstring ("credentials by env-var NAME — never inlined"); `EmbeddingConfig.base_url: str` + `api_key_env: str` |

---

## §FRICTION — lore finding I could NOT file (prod store down at both attempts; for the lead to file)
```
subject: lore_search/lore_get_symbol/lore_findings intermittently fail against prod store ws://127.0.0.1:18500/rpc mid-session
area: lore_search   category: capability_gap   created_by: security-59
body: During pkt59 security audit (2026-08-16, HEAD ee4bced), lore_search, lore_get_symbol, and
lore_findings repeatedly returned SurrealDB failures against 'ws://127.0.0.1:18500/rpc' ('no close
frame received or sent'; bare-UUID errors). Some lore_get_symbol calls in the same window succeeded,
so lore-surreal (prod) is intermittently dropping, not a hard outage. Fell back to direct Read/grep
for logging_setup.py, store/surreal.py, store/_txn.py, embedding.py, config.py, and the installed
fastmcp/uvicorn source per dogfood CLAUDE.md §3 (said out loud). Filing rather than routing around
silently (consumer law / brief project v7). Impact: an auditor cannot trust the graph for
exhaustiveness questions while the store flaps.
```
**UPDATE:** the store recovered on a third attempt — **filed as finding #380** (id
`c2368ace7f824ae68219e7f47c5875b7`, status open). The friction stands: the findings ledger itself is
unreachable while lore-surreal flaps, so the very act of filing "the store is flaky" failed twice first.

## Method note (honesty)
The uvicorn-logs-it-unredacted mechanism (F4) is **source-confirmed** (uvicorn + logging_setup reads), not
staged as a live credentialed-boot-failure — I did not deliberately boot the container with a bad DB and a
credentialed URL to capture the exact log line. That live capture would upgrade F4-(a) from "source-certain
mechanism" to "observed leak," and would settle the F4-(b) dependency question (does the surrealdb SDK's
signin-error repr echo the payload?). Recommended if the lead wants F4 measured rather than reasoned; the
verdict (ACCEPT sound) does not change either way, because the residual is pre-production regardless.
