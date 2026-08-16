# REPORT-spike-59 — packet-59 fastmcp 3.x migration spike (the 3 §6.6 GO/NO-GO gates)

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4)
- **Demanded vs. have:** the brief needs `uv` (present), network to install `fastmcp>=3.4,<4`
  (worked — install authorized as this packet's D4 dependency, pre-production), a writable
  scratch dir + `scripts/` + `REPORT-spike-59.md` (all writable), and the lore tools (loaded via
  `ToolSearch "+lore"`). **Nothing was un-satisfiable — the mission ran end to end.** No blocker.
- **Model attestation (brief-carried, I cannot self-read):** `claude-opus-4-8` (Opus 4.8), pinned
  via the opus48-worker definition. `$CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8` corroborates.

## SUMMARY BLOCK
- state: **done**
- verdicts: **ITEM 1 GO · ITEM 2 GO · ITEM 3 GO** (all three §6.6 `[inferred]` payoffs CONFIRMED
  on a REAL uvicorn/TCP wire; measured 2026-08-15 at HEAD `faa68b2`; fastmcp==3.4.7, mcp==1.29.0).
- deviations:
  - Item 1 adds a **CONCURRENT-sessions** leg beyond the brief's N sequential sessions (the real
    multi-client condition for the ref-count) — high-value, [measured] once-per-process holds.
  - Item 1's negative control surfaced a **bonus finding** (fastmcp fails LOUD if the lifespan is
    not delegated) — reported as a build de-risk, scoped precisely (loud at first WIRE request).
- Packages considered: **`fastmcp` (`>=3.4,<4`, resolved 3.4.7)** — verdict **replace** the façade
  (`mcp.server.fastmcp.FastMCP` → `fastmcp.FastMCP`) / **keep `mcp` transitively** (fastmcp-slim
  pins `mcp<2.0`). READ: installed 3.4.7 source via `inspect.getsource`/`inspect.signature` —
  `FastMCP.__init__`, `FastMCP.http_app`, `FastMCP._lifespan_manager`,
  `fastmcp.server.http.create_streamable_http_app`, `HostOriginGuardMiddleware`, `fastmcp.settings`.
- Reuse ledger: 4 new symbols, all THROWAWAY spike-local ASGI wrappers (`OriginValidationMiddleware`,
  `BearerAuthMiddleware`, `NaiveLifespanEatingMiddleware`, `CountingVerifier`) — the first two are
  FAITHFUL repros of `loremaster/auth.py`'s wrappers (cited), none reusable production code. No
  production symbol introduced. Full ledger → §DRY.
- Graded: `faa68b2` · HEAD-at-report: `faa68b2` · SAME. (Design doc authored at `41287c5`; the only
  commits `41287c5..faa68b2` are docs — NO `server.py`/`auth.py`/`pyproject` change — so the design's
  live-read coupling sites are unchanged at my measurement HEAD.)
- decisions-needed:
  - **A build-time config RIDER, not a fork (flag for the lead/contract):** enabling
    `host_origin_protection` adds **Host** validation lore does not have today — the build MUST set
    `allowed_hosts` for lore's real proxied topology (TLS terminated upstream by nginx-ingress,
    `auth.py:13`) or it will 421 legitimate production traffic. See §Item 3 flag.
- receipt POINTERS:
  - Harness (durable, re-runnable): `scripts/fastmcp_migration_spike.py` (lead commits — I do not run git)
  - Per-item measurement + controls → §Item 1 / §Item 2 / §Item 3 (verbatim tails)
  - Source-read mechanism citations → §Source facts
  - Load-bearing snippets pasted verbatim → §Instruments

---

## Attestation & environment  [measured 2026-08-15]
- **Model:** `claude-opus-4-8`.
- **Isolated uv project** at `/tmp/fastmcp-spike-59-work/` (NOT lore's tree — nothing under
  `loremaster/`/`loresigil/`/`lorescribe/`/`lorerunes/`, `pyproject.toml`, or `uv.lock` touched).
  Resolved pins (`fastmcp>=3.4,<4`):
  ```
  fastmcp==3.4.7   mcp==1.29.0   starlette==1.6.0   uvicorn==0.52.3   httpx==0.28.1
  pydantic==2.13.4   python 3.12.13
  ```
  (The live lore tree has `mcp==1.27.2` installed per blast-radius §3; my fresh resolve pulled
  `mcp==1.29.0` — BOTH satisfy fastmcp-slim's transitive `mcp<2.0,>=1.24.0` pin. fastmcp's
  middleware/lifespan/transport-security behavior is unchanged across 1.27–1.29.)
- **Transport honesty (§6.2 / FG1):** every probe ran over a REAL `uvicorn.Server` on a `127.0.0.1`
  TCP port with `lifespan="on"` (forces the ASGI lifespan protocol — a server that cannot run it
  fails loudly, never silently skips it), driven by a real `fastmcp.Client` (streamable-HTTP) and
  raw `httpx` for header-spoof probes. **The in-memory transport was NEVER used** — it skips the ASGI
  lifespan, so it would prove nothing about Item 1.
- **Reproducibility:** the full harness ran **4×** with byte-identical verdicts and measurements.
- **Method (per the #107 read-then-verify law):** each fastmcp mechanism was first READ from installed
  3.4.7 source (§Source facts), THEN confirmed empirically with a positive AND a negative control.

---

## Item 1 — lifespan-apparatus DELETE (§6.6-1 / §5b-C2 / M11) → **GO**

**Claim under test:** fastmcp enters the user `lifespan=` EXACTLY ONCE PER PROCESS at ASGI startup,
with ref-counted teardown correct, in the SERVED (stateful, `stateless_http=False`) mode — AND lore's
bespoke Origin/Bearer ASGI wrappers delegate the `lifespan` scope so it actually runs.

**Setup:** `FastMCP(lifespan=heavy_lifespan)` where `heavy_lifespan` (standing in for lore's ~150-LOC
eager watcher/reconcile build) increments module-level `enter`/`exit` oracle counters and mints a
`boot-N` id on entry. `inner = mcp.http_app(path="/mcp", stateless_http=False)`, wrapped in FAITHFUL
repros of lore's production stack `BearerAuthMiddleware(OriginValidationMiddleware(inner))` — both of
which pass non-`http` (lifespan) scopes straight through (`auth.py:230-231`, `:312-313`).

**Verbatim tail (final canonical run):**
```
[faithful/lifecycle-1] eager enter (pre-request) : 1
[faithful/lifecycle-1] 4 SEQUENTIAL wire sessions boot_ids : ['boot-1', 'boot-1', 'boot-1', 'boot-1']
[faithful/lifecycle-1] enter after sequential : 1
[faithful/lifecycle-1] 4 CONCURRENT wire sessions boot_ids : ['boot-1', 'boot-1', 'boot-1', 'boot-1']
[faithful/lifecycle-1] enter after concurrent : 1
[faithful/lifecycle-1] exit count after shutdown : 1
[faithful/lifecycle-2] enter after a 2nd process lifecycle : 2  boot_id=boot-2  (control: instrument is LIVE, not stuck)
[naive/neg-control] enter before=2 after=2 (delta 0); tool saw boot_id=None
ITEM 1 VERDICT: GO
```

**Reading the oracles:**
- **Once per process:** `eager enter == 1` (the lifespan ran at STARTUP, before any request — eager),
  and it STAYS 1 across 4 sequential + 4 concurrent wire sessions; every one of the 8 sessions read
  the same `boot-1` id. A per-SESSION re-entry (the old mcp-SDK behavior the guard exists to paper
  over) would have driven `enter` to 8 and minted distinct boot ids. It did not.
- **Ref-counted teardown correct:** `exit == 1` after a clean shutdown — one enter, one exit.
- **POSITIVE CONTROL (the counter WOULD move on re-fire):** a 2nd full process lifecycle drove
  `enter` to `2` with a fresh `boot-2` — so the "1" above is a real measurement, not a stuck instrument.
- **NEGATIVE CONTROL (delegation is load-bearing):** a `NaiveLifespanEatingMiddleware` that answers the
  ASGI lifespan protocol itself and does NOT delegate → `enter` delta `0` (user lifespan never ran) and
  the tool saw `boot_id=None`. This is exactly the FG1-class blind spot; the faithful pass-through is
  what makes the lifespan run.

**BONUS finding (build de-risk, scoped precisely):** under the naive wrapper, the very first WIRE tool
call raised — LOUDLY — `RuntimeError: FastMCP's StreamableHTTPSessionManager task group was not
initialized … ensure you are setting lifespan=mcp_app.lifespan in your parent app` (from
`fastmcp/server/http.py:87,108`). So a migration that mis-wires the lifespan **fails loud at the first
wire request, not silently**. ⚠ SCOPE: this loud failure is at first WIRE request; it does NOT fire on
the **in-memory** transport (which never reaches the session manager the same way), so §6.1 in-image
conformance + §6.2 wire smoke remain REQUIRED — the loud-fail is a safety net, not a substitute.

**Verdict: GO** → the `_ProcessLifespanGuard` + `_EagerStartupLifespan` + `_lore_eager_guard` attr
(~150 LOC) CAN be deleted; the heavy build moves into `lifespan=` (FP-07 bounded-retry re-homed
inside it), per §5b-C2 / M11.
**Fallback that fires on NO-GO (did NOT fire):** KEEP the guard/interceptor (§5b-C2 PRESERVE branch).

**Scope bound (honest):** I proved the NEW-world property (fastmcp = once-per-process), which is what
the DELETE requires. I did NOT independently re-measure the OLD mcp-SDK's per-session re-entry (the
guard's original premise) — it is cited from the hand-roll inventory, not re-measured here. The DELETE
is safe because the new substrate provides the property natively, regardless of the old one's exact shape.

---

## Item 2 — Origin/Host guard ordering vs the TokenVerifier (§6.6-2 / §5b caveat) → **GO** (guard BEFORE verifier)

**Claim under test:** does fastmcp's `host_origin_protection` run BEFORE the `TokenVerifier`? (The
packet-39 §8 R9 "zero outbound Google call" property: a cross-origin attacker rejected BEFORE credential
parse.) NO-GO (runs after) ⇒ bespoke Origin layer STAYS outermost.

**Setup:** `FastMCP(auth=CountingVerifier(...))` — a `TokenVerifier` whose `verify_token` (where the
real packet-39 OUTBOUND Google tokeninfo POST would live) increments a call counter — served via
`http_app(host_origin_protection=True, allowed_hosts=[<real bind>])`. All probes carry a VALID token.

**Verbatim tail:**
```
[probe]     bad Origin + valid token -> status=403 body='Forbidden Origin' verify_token_calls=0  (zero => guard ran first)
[pos-ctrl]  good Origin + valid token -> status=200 verify_token_calls=1  (>=1 => verifier reachable & live)
[neg-ctrl]  good Origin + BAD token  -> status=401 verify_token_calls=1  (401 => auth is the inner gate)
ITEM 2 VERDICT: GO  (guard-BEFORE-verifier)
```

**Reading the oracles (two independent signals):**
- **Guard is outermost:** a spoofed `Origin: http://evil.example` (with a VALID token) is rejected
  `403 Forbidden Origin` (fastmcp's `HostOriginGuardMiddleware` body) — AND `verify_token_calls == 0`:
  the verifier was NEVER consulted. That is the "zero outbound Google call" property, demonstrated
  DIRECTLY (verify_token is precisely where the outbound POST would sit).
- **POSITIVE CONTROL (the verifier is live, not stuck at 0):** with a loopback (allowed) Origin, the
  request reaches auth and `verify_token_calls == 1`, status 200 — so the 0 above is meaningful.
- **NEGATIVE CONTROL (auth is the INNER gate):** good Origin + BAD token → `401`, `verify_token_calls == 1`
  — the verifier runs and rejects only after the Origin guard passes.

**Source corroboration (§Source facts):** `create_streamable_http_app` does
`server_middleware.insert(0, Middleware(HostOriginGuardMiddleware, …))` AFTER extending the auth
middleware — index 0 is the OUTERMOST app-level middleware — while token enforcement is
`RequireAuthMiddleware` wrapping the route ENDPOINT (innermost). The wire result matches the source.

**Verdict: GO** → `host_origin_protection` runs BEFORE the verifier, so the spec's NO-GO condition does
NOT hold: fastmcp's own guard already satisfies R9's ordering. The bespoke Origin layer is NOT
structurally required to stay outermost FOR THE ORDERING PROPERTY (a keep-for-defense-in-depth choice
is a separate design call for the build/packet-39, which this spike informs but does not make).
**Fallback that fires on NO-GO (did NOT fire):** keep the bespoke Origin layer outermost for R9.

**Portability note:** the ordering is a PLACEMENT fact (guard middleware index 0 vs. route-level auth),
independent of the verifier implementation — packet-39's real OAuth verifier sits in the SAME
`RequireAuthMiddleware` position, so this result carries to it. (I used a static verifier, as the
original spike did; the ordering does not depend on it.)

---

## Item 3 — host_origin_protection closes the Host/DNS-rebinding gap (§6.6-3 / §5b-C3′) → **GO**

**Claim under test:** the ENABLED `host_origin_protection` actually REJECTS a spoofed `Host` header — a
check lore does NOT have today (`transport_security` unset; lore's bespoke layer validates ORIGIN, not
HOST). GO = a security benefit to bank.

**Setup:** A/B — the same spoofed-`Host` request against two servers differing ONLY in
`host_origin_protection` (`True` vs `False`), plus a legit-Host positive control on the ON server.

**Verbatim tail:**
```
[protection=ON ] spoofed Host 'evil.example' -> status=421 body='Misdirected Request'  (421 => REJECTED)
[protection=ON ] legit   Host '127.0.0.1:35011' -> status=200  (not 421 => guard lets legit through)
[protection=OFF] spoofed Host 'evil.example' -> status=200  (not 421 => ACCEPTED, the gap that exists today)
ITEM 3 VERDICT: GO
```

**Reading the oracles:**
- **PROBE (protection ON):** spoofed `Host: evil.example` → `421 Misdirected Request` (fastmcp's
  `HostOriginGuardMiddleware` host-reject body) — REJECTED.
- **POSITIVE CONTROL (guard doesn't reject everything):** a legit `Host: 127.0.0.1:<port>` → `200` —
  the guard lets legitimate traffic through.
- **NEGATIVE CONTROL = today's pre-migration state (protection OFF, the `settings` default):** the SAME
  spoofed `Host` → `200`, ACCEPTED. This is the exact Host/DNS-rebinding gap that exists today.

**Verdict: GO** → enabling `host_origin_protection` closes a real, today-open Host-spoofing gap. A
security benefit to bank in the migration.

**⚠ FLAG — a build-time config RIDER (surfaced per scope law; NOT a NO-GO):** the guard's default is
**OFF** — `fastmcp.settings.http_host_origin_protection == False` and `create_streamable_http_app`'s own
param default is `False`. (The `http_app` docstring's "auto protects localhost-bound servers" describes
the `"auto"` VALUE, not the default — the effective default is OFF.) So **the migration MUST explicitly
pass `host_origin_protection=True` (or `"auto"`)** — relying on the default banks nothing. AND, because
the enabled guard now validates the **Host** header (which lore never did), the build MUST configure
`allowed_hosts` for lore's REAL deployment topology — TLS is terminated upstream by nginx-ingress
(`auth.py:13`), so the Host header lore sees is the proxied one; an unconfigured allowlist would `421`
legitimate production traffic. This is a config item the contract/build must get right, and belongs in
the §6.1 in-image + §6.2 wire smoke acceptance (assert a legit proxied Host passes).

---

## Source facts (read from installed fastmcp 3.4.7 — the mechanism behind the wire results)
All via `inspect` against `.../site-packages/fastmcp/server/{server,http}.py`; confirmed empirically above.

- **`FastMCP.__init__`** takes `version=`, `lifespan=`, `auth=`, `middleware=`, `on_duplicate=` and
  NO `host`/`port`/`streamable_http_path` (confirms D2/C1/P6/P7 — host/port read at the uvicorn call
  site; version is a ctor kwarg; path moves to `http_app(path=)`).
- **`FastMCP.http_app(...)`** signature:
  `path, middleware, json_response, stateless_http, transport='http', event_store, retry_interval,
  host_origin_protection: HostOriginProtection|None, allowed_hosts, allowed_origins`. There is NO
  `streamable_http_app` method (C1 — it is `http_app`). `HostOriginProtection = Union[bool, Literal['auto']]`.
- **`fastmcp.settings` defaults:** `http_host_origin_protection=False`, `http_allowed_hosts=None`,
  `http_allowed_origins=None`, `stateless_http=False`, `streamable_http_path='/mcp'` (Item 3 default-OFF).
- **Ordering (Item 2)** — `create_streamable_http_app`:
  ```python
  if auth:
      auth_middleware = auth.get_middleware()
      server_middleware.extend(auth_middleware)          # auth app-level mw (non-rejecting for bearer)
      ...
      server_routes.append(Route(path, endpoint=RequireAuthMiddleware(streamable_http_app, ...)))  # token gate = INNERMOST
  ...
  if host_origin_protection is not False:
      server_middleware.insert(0, Middleware(HostOriginGuardMiddleware, allowed_hosts=..., allowed_origins=...,
                                             mode="strict" if host_origin_protection is True else "auto"))  # index 0 = OUTERMOST
  ```
- **Once-per-process (Item 1)** — `FastMCP._lifespan_manager` is genuinely ref-counted (the spec's
  guessed `_lifespan_ref_count`/`_lifespan_manager` is real; `_lifespan_manager` is a method):
  ```python
  async with self._lifespan_lock:
      if self._lifespan_result_set:
          self._lifespan_ref_count += 1
          should_enter_lifespan = False        # concurrent re-entry: DOES NOT re-run user lifespan
      else:
          self._lifespan_ref_count = 1
          should_enter_lifespan = True          # first entry: runs self._lifespan(self)
  ```
  The Starlette `lifespan` in `create_streamable_http_app` enters `server._lifespan_manager()` once per
  ASGI-app startup and holds it for the whole process (teardown shielded with `anyio.CancelScope(shield=True)`).
- **Guard reject codes (Item 2/3)** — `HostOriginGuardMiddleware.__call__`: bad Host →
  `Response("Misdirected Request", 421)`; disallowed Origin → `Response("Forbidden Origin", 403)`;
  non-`http` scope → passes straight through (like lore's wrappers). An ABSENT Origin is allowed
  (`origin = headers.get("origin")` is None → the origin block is skipped) — semantics align with
  lore's OriginValidationMiddleware on that point (relevant to C3′ adoption).

---

## Instruments (brief-base §1 — the load-bearing harness survives)
- **Durable, committed by the lead:** `scripts/fastmcp_migration_spike.py` (self-contained; re-run with
  `uv run --with 'fastmcp>=3.4,<4' --with uvicorn --with httpx python scripts/fastmcp_migration_spike.py`).
- **Load-bearing cores pasted verbatim** (the parts a reader must trust for the verdicts):

Item 1 — the faithful lifespan pass-through (item 1b) and the naive negative control:
```python
class OriginValidationMiddleware:   # faithful repro of loremaster/auth.py:272
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":              # <-- lifespan pass-through (item 1b)
            await self._app(scope, receive, send); return
        ...  # Origin allow-list (absent/loopback/configured) else 403
class BearerAuthMiddleware:          # faithful repro of loremaster/auth.py:208
    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":              # <-- lifespan pass-through (item 1b)
            await self._app(scope, receive, send); return
        ...  # Bearer verify else 401
class NaiveLifespanEatingMiddleware: # NEG control: intercepts lifespan, never delegates
    async def __call__(self, scope, receive, send):
        if scope.get("type") == "lifespan":
            while True:
                m = await receive()
                if m["type"] == "lifespan.startup":  await send({"type": "lifespan.startup.complete"})
                elif m["type"] == "lifespan.shutdown": await send({"type": "lifespan.shutdown.complete"}); return
        else: await self._app(scope, receive, send)
```

Item 2 — the verify_token call-counter (the "zero outbound" oracle):
```python
class CountingVerifier(TokenVerifier):
    async def verify_token(self, token):
        verify_calls["n"] += 1        # in real packet-39 OAuth, the OUTBOUND Google tokeninfo POST is HERE
        return AccessToken(token=token, client_id=..., scopes=...) if token == self._token else None
# probe: bad Origin + valid token -> 403 AND verify_calls == 0  => guard ran BEFORE the verifier
```

## DRY ledger (brief-base §6)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `OriginValidationMiddleware` (spike) | n/a — throwaway spike wrapper | faithful repro of prod `loremaster.auth.OriginValidationMiddleware` (read, cited auth.py:272) | HAND-ROLLED (spike-local; cannot import lore into the isolated venv; pass-through clause copied verbatim) |
| `BearerAuthMiddleware` (spike) | n/a — throwaway spike wrapper | faithful repro of prod `loremaster.auth.BearerAuthMiddleware` (read, cited auth.py:208) | HAND-ROLLED (spike-local, same reason) |
| `NaiveLifespanEatingMiddleware` | n/a — negative control | no prod analog (it is deliberately broken) | HAND-ROLLED (control instrument) |
| `CountingVerifier` | n/a — reuses spike-1 pattern | subclass of `fastmcp.server.auth.auth.TokenVerifier` (the documented seam) | HAND-ROLLED (throwaway, wraps the package's own extension point) |
No production symbol introduced — this is a MEASUREMENT-only spike (writable set: scratch + this report
+ `scripts/fastmcp_migration_spike.py`). `server.py`, `pyproject.toml`, `uv.lock`, tests untouched.

## Bottom line for the CONTRACT phase
All three §6.6 `[inferred]` payoffs are now [measured] GO at HEAD `faa68b2` (fastmcp 3.4.7). The contract
may pin: (1) delete the ~150-LOC lifespan apparatus, heavy build → `lifespan=`; (2) adopt fastmcp
`host_origin_protection` — it runs BEFORE the TokenVerifier (R9 ordering satisfied natively);
(3) enable it explicitly (default is OFF) and configure `allowed_hosts` for the nginx-ingress topology,
banking the Host/DNS-rebinding rejection lore lacks today. Per §0 scope, the contract still RE-READS the
installed 3.x source before pinning exact accessor shapes (P2/P13/P14/FG7).
