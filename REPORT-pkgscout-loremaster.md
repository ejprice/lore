# REPORT-pkgscout-loremaster

**All findings below were measured on 2026-07-25 against worktree
`/home/ejprice/PycharmProjects/lore-pkt11i` at commit `6654be0`
(branch `pkt11i-floor-calibration-dark`).** Every "is" in this report is an "was, at that
sha" — re-derive before acting.

---

## SUMMARY BLOCK

```
brief-base v6 read
state: done-with-deviations
```

**Deviations**
- Coverage is partial by construction (41,334 LOC / 56 files). Honest statement below.
- I delegated *location* of hand-rolls in three file groups to three read-only Explore
  subagents and did every *library* verification myself. One subagent over-claimed
  ("fence-width formula duplicated three times"); I re-derived it and corrected it in
  §T3.4 — the primitives ARE shared, only a one-line expression is cloned.
- I ran `uv run --with <pkg>` ephemeral overlays and one `podman run --rm` against
  `localhost/lore:latest`. Nothing in the tree, the lockfile, or the image was changed.

**Coverage statement — what I read, and what I did NOT**
- **Read myself, in full or near-full:** `auth.py`, `calibration/counting.py`,
  `calibration/engine.py` (docstring + probe loop), `embedding.py`, `index/paths.py`,
  `sanitise.py`, `store/query_text.py`, `logging_setup.py` (head), `diff.py` (docstring),
  `shellout.py` (threat-model head), `index/sqlite_resilient.py` (docstring),
  `memory/ledger.py` (head), `config.py` (`resolve_secret`, `load_config`, `AuthConfig`),
  `index/snapshots.py` (`capture_git_identity` + `_run_git_rev_parse`), `scout.py`
  (`CommandSubscriber.run` / `_backoff`), `server.py` (`build_asgi_app`,
  `_EagerStartupLifespan._acquire_eager_lease_with_retry`, `_render_age` constants,
  `build_mcp_server` FastMCP construction), `search.py` (`_wait_for_fresh`),
  `map.py` (`_page_rank`), `store/surreal.py` (`_analyze_query` region).
- **Located by subagent, spot-verified by me where it changed a verdict:** `server.py`
  (~1,900 of 8,633 lines read line-by-line; the rest grep-swept for every named
  category — the unread regions most at risk are `build_app_context` ~530 lines and the
  comms action handlers), `render.py`, `store_read.py`, `read_file.py`, `extension.py`,
  `store/*`, `graph*.py`, `impact.py`, `symbols.py`, `tasks/messages/briefs/findings/agents.py`
  (cross-cutting machinery only — domain state machines deliberately skipped).
- **NOT covered at all:** `index/indexer.py` (2,041), `index/watcher.py` (1,141),
  `index/surreal_manifest.py`, `index/reconcile.py`, `index/records.py`, `index/schema.py`,
  `index/cli.py`, `index/manifest.py`, `memory/local.py` (1,351), `memory/backend.py`,
  `source/*`, `agent_ref.py`, `calibration/baseline.py`. **A fourth Explore sweep over
  `index/` + `memory/` was launched and had not returned when this report was
  committed** — see §DEFERRED. Treat those ~6,000 LOC as UNSWEPT.

**Ranked verdicts** (rank = what a wrong choice costs, not swap satisfaction)

| # | Symbol | Library | Verdict |
|---|---|---|---|
| P1 | `auth.BearerAuthMiddleware` + `AuthVerifier` | `mcp.server.auth` (installed 1.27.2) | **REPLACE-WITH-ADAPTER** — the hand-roll silently disables the SDK's session-owner binding |
| P2 | `calibration.counting.AsyncClaudeTokenCounter` | `anthropic` (new dep) | **REPLACE** — 3 measured defects the SDK doesn't have |
| P3 | `calibration.counting.load_api_key` | `python-dotenv` (installed 1.2.2) | **REPLACE** — measured to MISS `export KEY=…`; live bug |
| P4 | 4 private backoff policies, none jittered | `tenacity` (already IN THE IMAGE) | **REPLACE-WITH-ADAPTER** — #102's class, in a population #202 did not cover |
| P5 | `server._EagerStartupLifespan` (~234 LOC) | `starlette.routing.Router(lifespan=)` (installed 1.2.0) | **REPLACE-WITH-ADAPTER** |
| P6 | `index.snapshots.capture_git_identity` | `dulwich` (new dep) | **REPLACE-WITH-ADAPTER** — oracle-verified byte-equal |
| P7 | `map.MapEngine._page_rank` | `networkx.pagerank` (+numpy/scipy) | **FORK → operator** (see §P7; nx's *default* tol changes served order) |
| P8 | `server.AppContext._find_key_cycle` | `graphlib` (stdlib, zero cost) | **REPLACE** |
| P9 | `pydantic-settings` declared-but-unused; `websockets` imported-but-undeclared | — | **DEPENDENCY-HYGIENE DEFECT** |
| T3 | `_render_age`, `_path_similarity`, SurrealQL DDL/query builders, `sanitise.py`, `query_text.py` | `humanize`, `difflib`, `sqlglot` | **KEEP / GENUINELY BESPOKE** — reasons in §T3 |

**Decisions needed (operator)**
1. **P7 PageRank/networkx** — swap and accept a numeric-behaviour change on a served
   ranking, or KEEP with a re-open trigger? My recommendation: KEEP, trigger below.
2. **P6 dulwich** — the image *now carries git* (`/usr/bin/git`, verified), so this is an
   architecture call (retire the exec-seam exemption), not an outage fix. Worth it?
3. **P9 `pydantic-settings`** — adopt `YamlConfigSettingsSource` for `load_config`, or
   delete the declared dependency? Either is fine; the status quo (declared, unused) is not.
4. **The ~6,000 unswept LOC** in §DEFERRED — commission a follow-up sweep?

**Tool honesty.** lore's index watches the MAIN checkout, **not** this worktree (#125), so
**every structural fact in this report came from grep/Read/subagent reads of the worktree, not
from the lore graph.** I did not use `lore_search`/`lore_impact` at all — using it here would
have described a different tree. This is the documented #125 fallback, stated out loud as the
dogfood protocol requires. I filed no friction row: #125 is already ledgered.

**Receipt pointers** — §P1 (SDK source cites), §P2 (wire-capture receipt), §P3 (measured
diff), §P4 (site table), §P6 (oracle equality run), §P7 (15-configuration divergence table),
§SCOPE (7 defects/risks outside this mission).

---

## P1 — `loremaster.auth` hand-rolls the MCP SDK's own auth seam, and loses a security control doing it

**Symbols:** `loremaster.auth.AuthVerifier`, `loremaster.auth.ApiKeyVerifier`,
`loremaster.auth.BearerAuthMiddleware`; installed at `loremaster.server.build_asgi_app`.

**What it does.** `AuthVerifier` is an ABC with one method, `verify(token) -> identity | None`.
`ApiKeyVerifier` matches a presented bearer token against a set of named keys with
`hmac.compare_digest`. `BearerAuthMiddleware` is a plain ASGI app that extracts
`Authorization: Bearer …`, calls `verify`, and either 401s or delegates.

**The library.** `mcp.server.auth` — **already a direct dependency** (`mcp[cli]>=1.27`,
installed 1.27.2). It ships the identical seam: `mcp.server.auth.provider.TokenVerifier`
(Protocol: `async verify_token(token) -> AccessToken | None`),
`mcp.server.auth.middleware.bearer_auth.BearerAuthBackend` (a starlette
`AuthenticationBackend` doing the same header parse and `bearer ` prefix strip), and
`RequireAuthMiddleware` (401/403 with a spec-shaped `WWW-Authenticate`).

**What I actually read.** `[library-verified, mcp 1.27.2]`
`.venv/lib/python3.14/site-packages/mcp/server/auth/middleware/bearer_auth.py` in full;
`mcp/server/auth/provider.py::TokenVerifier`; `mcp/server/fastmcp/server.py` (the
`token_verifier` → `AuthenticationMiddleware(backend=BearerAuthBackend(...))` wiring, and
`RequireAuthMiddleware` mounting); `mcp/server/streamable_http_manager.py`
`_handle_stateful_request` and its `_session_owners` dict.
`[source-verified]` `loremaster/loremaster/auth.py` in full;
`loremaster.server.build_asgi_app`; `loremaster.server.build_mcp_server`'s `FastMCP(...)` call;
`loremaster.config.AuthConfig`.

**The finding, and why it outranks everything else here.** This is not a style complaint.
`FastMCP(...)` in `build_mcp_server` is constructed with **no** `token_verifier` and **no**
`auth=AuthSettings(...)`, so the SDK's `AuthenticationMiddleware` never runs and
`scope["user"]` is never an `AuthenticatedUser`. In
`streamable_http_manager._handle_stateful_request`:

```python
user = scope.get("user")
requestor = authorization_context(user) if isinstance(user, AuthenticatedUser) else None
...
if requestor != self._session_owners.get(request_mcp_session_id):
    # A session can only be used with the credential that created it.
```

With lore's middleware, `requestor` is **always `None`** and every `_session_owners[sid]` is
stored as `None`, so `None != None` is never true and **the check never fires**. The SDK's
"a session can only be used with the credential that created it" control is silently off.

`loremaster.config.AuthConfig.keys` is a `list[AuthKey]` and its docstring advertises
"rotate a developer out" — i.e. multi-identity deployments are a designed feature. In such a
deployment, holder-of-key-B who learns key-A's `mcp-session-id` can drive A's session. The
gate lore *did* build (a valid bearer is still required) holds; the per-session binding the
SDK ships does not. **[source-verified + library-verified]**

**Verdict: REPLACE-WITH-ADAPTER.** The adapter is small and the seam already exists:

- Keep `ApiKeyVerifier`'s key set + `hmac.compare_digest` + `build_api_key_verifier` — that
  logic is correct and the constant-time loop is the right call.
- Make it satisfy `mcp.server.auth.provider.TokenVerifier`: `async def verify_token(self,
  token) -> AccessToken | None`, returning `AccessToken(token=token, client_id=<identity>,
  scopes=[...])` instead of a bare identity string. ~15 lines.
- Pass it as `FastMCP(..., token_verifier=..., auth=AuthSettings(...))` and delete
  `BearerAuthMiddleware`. The SDK then installs `AuthenticationMiddleware` +
  `RequireAuthMiddleware` and the session binding starts working.

**Risk of the swap.** The 401 body/headers change shape (the SDK sends a JSON
`{"error": "invalid_token", ...}` body and an RFC-shaped `WWW-Authenticate`, where lore sends
`b"Unauthorized"` + `Bearer realm="loremaster"`). `loremaster/tests/test_auth.py` will need
re-pinning. `AuthSettings` requires an `issuer_url`/`resource_server_url`, which is a real
config addition for a localhost deploy — **this is the genuine gap, and it is the reason the
verdict is ADAPTER rather than a clean REPLACE**; confirm `AuthSettings` can be satisfied for
a no-OAuth static-key deployment before committing to it.

**The control that would prove the swap.** A test that (a) authenticates with key A, captures
the returned `mcp-session-id`, (b) re-issues the same request with key B and that session id,
and (c) asserts a `404 "Session not found"`. **Run that test against the CURRENT tree first —
it must go GREEN-as-in-"the request succeeded", i.e. RED as a security assertion.** That is
the mutation proof that this finding is real and not my reading of the SDK.

**KEEP, separately: `OriginValidationMiddleware`.** I checked starlette 1.2.0's middleware
set (`cors.py`, `trustedhost.py`, …): `TrustedHostMiddleware` gates the **Host** header, not
**Origin**, and `CORSMiddleware` omits CORS headers for a disallowed origin rather than
rejecting the request. Neither implements "absent Origin → allow, non-loopback Origin →
403". **GENUINELY BESPOKE** — verdict KEEP. `[library-verified, starlette 1.2.0]`

---

## P2 — `AsyncClaudeTokenCounter` is a hand-rolled Anthropic API client with three defects the official SDK does not have

**Symbols:** `loremaster.calibration.counting.AsyncClaudeTokenCounter.count`,
`AsyncClaudeTokenCounter._sleep_backoff`, `loremaster.calibration.counting.TerminalCountError`.
Consumer: `loremaster.calibration.engine.CalibrationEngine._count_live_total` /
`_probe_loop`.

**What it does.** POSTs `{"model": …, "messages": [{"role":"user","content": text}]}` to
`https://api.anthropic.com/v1/messages/count_tokens` over a raw `httpx.AsyncClient`, retries
429/5xx with a deterministic exponential backoff honouring `Retry-After`, and raises
`TerminalCountError` on any other 4xx.

**The library.** `anthropic` (**not currently installed** — I tested via
`uv run --with anthropic`, version **0.120.0**). `AsyncAnthropic().messages.count_tokens(
model=…, messages=[…])` returns a typed `MessageTokensCount`.

**What I actually read.** `[library-verified, anthropic 0.120.0]` I introspected
`AsyncAnthropic.__init__` (has `max_retries: int = 2`, `http_client`, `timeout`),
`BaseClient._calculate_retry_timeout`, `BaseClient._should_retry`,
`BaseClient._parse_retry_after_header` (all read as source), and I captured the SDK's real
wire shape through an `httpx.MockTransport`. `[source-verified]` `counting.py` in full;
`engine.py`'s `_probe_loop`.

**Measured wire shape of the SDK** (captured, not assumed):
```
URL   : https://api.anthropic.com/v1/messages/count_tokens        # identical to lore's
METHOD: POST                                                       # identical
BODY  : {"messages":[{"role":"user","content":"hello world"}],"model":"claude-sonnet-5"}
HDRS  : x-api-key, anthropic-version: 2023-06-01, content-type: application/json,
        + user-agent + 9 x-stainless-* telemetry headers
```
The body is **semantically identical but not byte-identical** — the SDK serialises
`messages` before `model`; lore serialises `model` before `messages`.

**The three defects in the hand-roll, each measured against the SDK's source:**

1. **`_sleep_backoff` has NO jitter.** `min(RETRY_BASE_DELAY_S * (2**attempt),
   RETRY_MAX_DELAY_S)` is deterministic, so N concurrent counters retry in lockstep. The
   SDK's `_calculate_retry_timeout` ends with `jitter = 1 - 0.25 * random(); timeout =
   sleep_seconds * jitter`. This is the **#102 deterministic-jitter defect class**, alive in
   a module that the #102 remediation (and #202's disposition) never touched.
2. **408 and 409 are misclassified as TERMINAL, and that permanently kills the calibration
   probe.** `count` retries only `429` or `>= 500`; every other status raises
   `TerminalCountError`. The SDK's `_should_retry` retries `408` (request timeout) and `409`
   (lock timeout) explicitly, and also obeys an `x-should-retry` header. Consequence chain,
   source-verified: a single 408 from a proxy → `TerminalCountError` →
   `CalibrationEngine._probe_loop`'s `except TerminalCountError: self._handle_terminal_
   endpoint_error(exc); return` → **the probe loop exits for the process lifetime and drift
   detection is off until the container restarts.** It degrades quietly (the committed
   constant is still served), which is exactly why nobody would notice.
3. **`Retry-After` in HTTP-date form falls through to plain exponential.**
   `float(retry_after)` raises `ValueError` on `Wed, 21 Oct 2015 07:28:00 GMT`, which is
   caught and ignored. The SDK's `_parse_retry_after_header` falls back to
   `email.utils.parsedate_tz`. Minor — the Anthropic API sends the integer form — but it is
   a gap the library closes for free.
   *(Minor 4th: `count` calls `_sleep_backoff` on the FINAL attempt too, so retry exhaustion
   always costs one extra sleep of up to `RETRY_MAX_DELAY_S`. Cosmetic; noted for
   completeness.)*

**Verdict: REPLACE.** The package does the job — this is side 1 of the operator's rule, and
the hand-roll is carrying real bugs the upstream doesn't, which is precisely the
worked-example shape (`timesfm` LoRA) the rule was written from.

**The named cost, and the reason this is not a drop-in.**
`loremaster/tests/test_calibration_counting.py::TestRequestShapeParity::
test_wire_shape_is_byte_identical_to_survey_counter` asserts the request body is
**byte-identical** to `scripts/token_survey.py::ClaudeTokenCounter`'s, and that the
application-level header set matches in keys and values. Both assertions go RED on the swap
(key order; `x-stainless-*`). **Do not "fix" that by loosening the pin — that pin exists so
every measured count stays comparable to the generation-anchored `baseline.json` forever.**
The correct wave is: move BOTH sides to the SDK in one commit, and re-pin parity as
*semantic* (parsed-JSON equality of the body + equality of `url`, `method`,
`anthropic-version`, and the api-key header), not byte-identity. If `scripts/` is another
scout's territory (#201 says it is), this needs cross-packet sequencing — flagging, not
deciding.

**The control that would prove the swap.** Two legs. (a) An oracle-equality test: drive both
the old counter and the SDK path through one `httpx.MockTransport` and assert the parsed
bodies are equal dicts and the three load-bearing headers match. (b) A live leg against the
real endpoint on one baseline corpus file, asserting the SDK's `input_tokens` equals
`baseline.json`'s `claude_tokens` for that file — that is the only check that proves the
constant stays anchored.

---

## P3 — `load_api_key` hand-parses a `.env` file and MISSES the `export` form (a live bug)

**Symbol:** `loremaster.calibration.counting.load_api_key`.

**What it does.** Prefers `os.environ["ANTHROPIC_API_KEY"]`; otherwise reads
`~/docker/mcp/.env` line by line and takes the value from the first line that
`startswith("ANTHROPIC_API_KEY=")`.

**The library.** `python-dotenv` — **already installed (1.2.2) and already in the shipped
image**, arriving transitively via `pydantic-settings`. `dotenv.dotenv_values(path)` returns
the parsed mapping.

**Measured, not argued.** I wrote a fixture `.env` containing
`export ANTHROPIC_API_KEY='sk-ant-export-form'` and ran both parsers over it:

```
dotenv:    sk-ant-export-form
hand-roll: None
```

`[library-verified, python-dotenv 1.2.2]` + `[source-verified]` (I transcribed the loop from
`load_api_key` verbatim for the comparison leg).

**Why this matters.** `export KEY=value` is the normal shape for a `.env` a human also
`source`s from a shell. If the operator's `~/docker/mcp/.env` uses it, `load_api_key` raises
`RuntimeError`, `CalibrationEngine` never probes, and lore silently serves the committed
constant forever — the same quiet-degradation shape as P2 defect 2. I did **not** read the
operator's actual `.env` (a secrets file; out of my writable set and none of my business), so
I cannot say whether it bites today — **only that the parser cannot read a form the file is
allowed to contain.** That is enough to fix.

`load_api_key` also differs from `resolve_secret` (`loremaster.config`) in stripping
whitespace off the env value; `resolve_secret`'s docstring says a secret is deliberately
never stripped. Two secret-resolution policies, disagreeing — a ONE-IMPLEMENTATION smell
worth folding into the same fix.

**Verdict: REPLACE.** `from dotenv import dotenv_values` and read the key out of the mapping;
the env-first preference stays. ~6 lines net. Zero new dependency weight (already in the
image), though it should become a **declared** direct dep rather than a transitive one.

**The control that would prove the swap.** A table-driven test over four fixture `.env`
bodies — plain `KEY=v`, `export KEY=v`, `KEY='v'` with a trailing comment, and a
`# KEY=commented` line — asserting the resolved value for each. Add the RED leg first: the
`export` row fails on the current tree.

---

## P4 — Four private backoff policies, none of them jittered, in the population #202 did not cover

`#202` dispositioned `store._txn.retry_on_conflict` as KEEP, and I agree with that
disposition entirely — it is proven, mutation-guarded, has a runtime guard keyed on its
`__code__` frames, and it is the **only** backoff in the tree with jitter
(`_txn_conflict_backoff_seconds` → `random.uniform(0, window)`). This finding is about the
**other** population: the sites that never route through it.

`[source-verified]` — I derived this table from `grep -rn 'asyncio.sleep\|time.sleep'` over
`loremaster/loremaster/**.py` and read each hit's enclosing function:

| Symbol | Shape | Jitter? | Bound |
|---|---|---|---|
| `scout.CommandSubscriber._backoff` | `min(base * 2**attempt, cap)`, base 0.5s cap 30s | **NO** | attempts unbounded (loop reconnects forever) |
| `server._EagerStartupLifespan._acquire_eager_lease_with_retry` | **fixed** `asyncio.sleep(2.0)`, 5 attempts | **NO** | not exponential at all |
| `calibration.counting.AsyncClaudeTokenCounter._sleep_backoff` | `min(1.0 * 2**attempt, 30)` | **NO** | 6 attempts |
| `calibration.engine.CalibrationEngine._probe_loop` | `min(start * 2**attempt, cap)` | **NO** | unbounded (retries forever, by design) |
| *(reference)* `store._txn._txn_conflict_backoff_seconds` | full-jitter exponential | **YES** | attempt ceiling + deadline |

Four independent re-derivations of one policy, all missing the property the fifth has.
`scout`'s is the one that bites hardest: a store restart drops every subscriber's socket at
the same instant, and every one of them reconnects on an identical 0.5 → 1 → 2 → 4s ladder.
That is a thundering herd against the very store that just came back up.

**The library.** `tenacity` — **version 9.1.4, already installed AND already present in the
shipped `localhost/lore:latest` image** (verified by `podman run --rm`; it arrives
transitively via `langchain-core` ← `langchain-text-splitters`). Adopting it costs **zero
image weight** — only an honest direct-dependency declaration.
`[library-verified, tenacity 9.1.4]` I introspected `BaseRetrying.__init__` and confirmed:
- `AsyncRetrying(sleep=…, stop=…, wait=…, retry=…, before_sleep=…, reraise=…)` — note
  **`sleep` is an injectable parameter**, which is what every one of these four sites needs
  (they all inject a fake sleep for tests; that is why they hand-rolled in the first place,
  and tenacity closes that gap directly).
- `wait_exponential_jitter(initial, max, exp_base, jitter)` and
  `wait_random_exponential(multiplier, max, exp_base, min)` — both give the missing property.
- `stop_after_attempt`, `stop_never`, `retry_if_exception_type` all present.

**Verdict: REPLACE-WITH-ADAPTER, with an important structural caveat.**

The adapter is not "wrap each site in `@retry`". Per this repo's ONE-IMPLEMENTATION law and
the explicit lesson that **routing is not sharing**, the correct shape is **one lore-owned
backoff-policy module** that builds tenacity `AsyncRetrying` instances from named policies
(`RECONNECT`, `EAGER_STARTUP`, `EXTERNAL_HTTP`, …), and four call sites that *use* it — not
four call sites that each construct their own `wait_exponential_jitter(...)` with their own
literals. Otherwise you have replaced four hand-rolled policies with four
tenacity-shaped ones and changed nothing that matters.

**Do NOT fold `_txn.retry_on_conflict` into it.** #202's disposition stands: its
classify-and-signal contract, its `RetryableConflictSignal` protocol, and the runtime guard
keyed on its frames are load-bearing and proven. The re-open trigger #202 carries is the one
that governs it; this finding does not touch it.

**The control that would prove the swap.** The mutation proof this repo already demands of
shared things: change the shared policy's jitter constant (or its `exp_base`) and assert
**every** call site's timing pin goes RED. A site that stays green is a private copy wearing
the shared name — which is exactly how eleven `_query` seams passed for correct in #120.
Second leg: a statistical pin per site — 100 simulated attempt-0 delays must not all be
equal (that single assertion is what none of the four current sites can pass).

---

## P5 — `_EagerStartupLifespan` hand-builds the ASGI lifespan protocol; starlette already composes lifespans

**Symbols:** `loremaster.server._EagerStartupLifespan` (~234 LOC), especially
`_drive_lifespan` (~112 LOC) and `_shutdown_inner`.

**What it does.** Intercepts the `lifespan` ASGI scope so lore's heavy build runs eagerly at
process startup rather than lazily on the first MCP session. To do that it hand-defines the
six `lifespan.*` message-type string constants and the five ASGI type aliases (the source
comment concedes these are "byte-for-byte identical" duplicates of the ones in
`loremaster/auth.py`), spawns the inner app as an `asyncio.Task`, and bridges `receive`/`send`
through **two `asyncio.Queue`s** so it can sequence its own work around the inner lifespan.

**The library.** `starlette` — **already installed (1.2.0) and already a transitive
dependency via `mcp`**, and `mcp.server.fastmcp`'s `streamable_http_app()` *returns a
Starlette app*. `[library-verified, starlette 1.2.0]` I confirmed
`starlette.routing.Router.__init__(..., lifespan: Lifespan[Any] | None = None)` and that a
`Router` instance exposes `lifespan_context`. The composition idiom — build a
`Starlette(routes=[Mount("/", app=inner)], lifespan=combined)` whose `combined`
`@asynccontextmanager` does `async with inner.router.lifespan_context(app): <take eager
lease>; yield; <release>` — replaces the entire queue bridge with a `with` statement.

**Verdict: REPLACE-WITH-ADAPTER.** ~234 LOC → roughly 30, and the hand-rolled ASGI protocol
constants and duplicated type aliases go with it. The adapter is the eager-lease
sequencing itself (take after inner startup, release before inner shutdown), which is lore's
own policy and stays lore's code.

**Risk.** Real, and this is why the verdict is not a bare REPLACE: the current code reports
`lifespan.startup.failed` on a failed eager build and deliberately caches nothing so a later
startup retries. Starlette's lifespan-context path raises out of startup instead. The failure
semantics must be re-established explicitly, and `loremaster/tests/test_eager_startup.py` and
`test_eager_startup_survives_unparseable_file.py` are the existing pins that define what
"correct" means here — read them **before** the implementation, per the tests-before-code law.

**The control that would prove the swap.** The two existing eager-startup test modules must
pass unchanged, plus one added pin: a deliberately-failing build must produce
`lifespan.startup.failed` (not an unhandled exception), and a *subsequent* startup on the same
process must still attempt the build.

---

## P6 — `capture_git_identity` shells out to `git`; `dulwich` reads the same values in-process

**Symbols:** `loremaster.index.snapshots.capture_git_identity`,
`loremaster.index.snapshots._run_git_rev_parse`.

**What it does.** Runs `git -C <root> rev-parse HEAD` and `git -C <root> rev-parse
--abbrev-ref HEAD` via `subprocess`, never raising, mapping git's `HEAD` detached-sentinel to
`None`.

**The library.** `dulwich` — pure-Python git, **not currently installed** (tested via
`uv run --with dulwich`, version **1.2.12**).

**Oracle equality, measured on this worktree** `[library-verified, dulwich 1.2.12]`:
```
dulwich HEAD         : 6654be08629f2c7f915e0021aa23c0da28efd5dc
git     rev-parse HEAD: 6654be08629f2c7f915e0021aa23c0da28efd5dc   ← identical
dulwich active_branch : pkt11i-floor-calibration-dark
git --abbrev-ref HEAD : pkt11i-floor-calibration-dark              ← identical
non-git directory     : dulwich.errors.NotGitRepository
```
Note this ran **inside a linked git worktree** (`.git` is a *file* naming an external
gitdir) and dulwich resolved it correctly — the topology most likely to break a
pure-Python implementation.

I also read `dulwich.porcelain.active_branch`'s source: it raises `IndexError` on a floating
(detached) HEAD and `ValueError` when the ref is not a local branch, so the adapter's
`except (NotGitRepository, KeyError, IndexError, ValueError): return None` is ~10 lines and
reproduces `capture_git_identity`'s never-raises contract.

**Verdict: REPLACE-WITH-ADAPTER — but read the honest caveats before deciding.**

*The case for.* This is the **only** shell-out in the shipped packages. `loremaster/shellout.py`
(566 LOC of AST gate) exists solely to police it, and `SANCTIONED_EXEC_MODULES` holds exactly
one entry: `index/snapshots.py`. Removing the shell-out lets that allowlist go **empty** —
a strictly stronger and simpler invariant ("no shipped module reaches a spawner, no
exceptions") than "no shipped module reaches a spawner except this one, whose internals the
scan cannot see". The gate itself should **stay** (its job is future shell-outs, per its own
written threat model), but its exemption disappears.

*The case against — and I will not overstate this.* **The shipped image DOES carry
`/usr/bin/git`** (verified: `podman run --rm --entrypoint sh localhost/lore:latest -c
'command -v git'` → `/usr/bin/git`). So #131's specific failure is already closed at the image
layer; this is an architecture improvement, **not** an outage fix, and any framing of it as
"prevents #131 recurring" would be false. **It also does NOT fix #134** — #134 is that a
worktree's `.git` file names an absolute host gitdir *outside* the container's `/workspace`
mount, and dulwich would fail to reach that path exactly as the git binary does.

**The control that would prove the swap.** A differential test over a corpus of repository
shapes — normal checkout, linked worktree, detached HEAD, packed-refs-only, bare repo,
non-git dir, nonexistent path — asserting `dulwich_capture(p) == subprocess_capture(p)` for
every one. Keep the subprocess implementation in the *test* as the oracle, delete it from
production. That is the only version of this swap I would sign off on: the shapes above are
where a pure-Python git reader earns or loses its keep, and I verified only three of them.

---

## P7 — `_page_rank` vs `networkx.pagerank`: oracle-equal at a tight tolerance, DIVERGENT at the library default. **Operator fork.**

**Symbol:** `loremaster.map.MapEngine._page_rank` (~23 executable lines), with
`_DAMPING = 0.85` and `_PAGE_RANK_ITERATIONS = 50`.

**What it does.** Personalized PageRank by explicit power iteration over a dict adjacency
list, redistributing dangling mass by the personalization vector each round, iterating a
**fixed** 50 times. Its docstring pins a determinism contract: sorted iteration order so
floating-point summation order — and therefore the served ranking — is identical across runs.

**The library.** `networkx.pagerank(G, alpha=, personalization=, dangling=, max_iter=, tol=)`
(tested at **3.6.1**). Note its default path dispatches to `_pagerank_scipy` and **raises
`ModuleNotFoundError` without numpy+scipy** — so this swap drags numpy and scipy in.

**What I measured** `[library-verified, networkx 3.6.1 / numpy 2.5.1 / scipy 1.18.0]`. I
transcribed `_page_rank` verbatim, generated random directed graphs with dangling nodes, and
compared against `nx.pagerank(..., dangling=personalization)`:

*At `tol=1e-13, max_iter=500` (n=120, 17 dangling nodes):*
```
mass mine: 1.0   mass nx: 1.0
ORDER IDENTICAL: True
max abs diff: 1.63e-13
```
**The two implementations are the same algorithm.** The hand-roll is not doing anything
exotic; nx reproduces it exactly.

*At networkx's **DEFAULT** `tol=1e-6, max_iter=100`, 15 configurations:*

| n | seeds 1, 7, 13, 42, 99 |
|---|---|
| 40 | order identical ×5 |
| 120 | order identical ×5 |
| **400** | **order DIVERGES ×5** (max abs diff 3.6e-6 … 1.1e-5) |

**Every 400-node configuration diverged.** A real project easily has 400 modules. So a naive
`nx.pagerank(G, alpha=0.85, personalization=p, dangling=p)` **changes the order of lore's
served map** at production scale — silently, and only for large projects, which is the
worst possible discovery path.

**Verdict: FORK — operator decides. My recommendation is KEEP + RE-OPEN TRIGGER.**

*Why I lean KEEP.* The hand-roll is ~23 executable lines, tested, and deterministic **by
construction** (fixed iteration count + sorted summation). The library version's
determinism would rest on numpy/scipy floating-point reproducibility plus a
correctly-chosen `tol`, and its default configuration measurably changes a **served
surface** at real scale. Trading 23 lines of provably-deterministic code for a ~100MB
dependency pair and a new tolerance-tuning obligation is not obviously the better trade —
this is the "the package does the job, but the job includes a property the package's
defaults do not give you" shape.

*Why the operator might overrule me, legitimately.* The cardinal rule leans toward the
package; #201 already proposes numpy/scipy/sklearn for the calibration statistics, so the
weight may land anyway; and §P8's graph work (BFS closure, liveness, dead-code, cycle
detection) would ride the same dependency. If networkx lands for the **whole graph layer**
at once, `_page_rank` should go with it rather than being the one hold-out.

*The re-open trigger, if KEEP is chosen:* **the day numpy+scipy enter the image for any
other reason (e.g. #201 landing), OR the day lore needs a second graph algorithm networkx
owns (centrality, community detection, SCC) — re-open and migrate the whole graph layer in
one wave, never this function alone.**

**The control that would prove the swap, if taken.** (a) `tol` pinned at `1e-12` or tighter
and `max_iter` raised — *not* the defaults; (b) an order-equality oracle test running both
implementations over a corpus of graphs **including at least one with ≥400 nodes** (the size
at which I measured divergence — a small-N fixture here is exactly the
non-discriminating fixture this repo's law warns about); (c) a determinism pin: same input,
20 runs, byte-identical rendered output.

---

## P8 — graph algorithms: one free stdlib swap, and one that rides P7's decision

**P8a — `server.AppContext._find_key_cycle` → `graphlib` (stdlib). Verdict: REPLACE.**
`[source-verified + library-verified, stdlib]` The symbol is a hand-written three-colour
recursive DFS (~34 lines) over a `dict[str, set[str]]`, returning the cycle path. Python's
stdlib `graphlib.TopologicalSorter.prepare()` raises `CycleError` carrying the cycle:
```
CycleError args: ('nodes are in a cycle', ['a', 'c', 'b', 'a'])
```
Zero dependency cost, stdlib-maintained, and it removes a recursive function (which on a
pathological batch could hit the recursion limit — the current code has no depth bound).
**Risk:** `graphlib` reports *a* cycle, not necessarily the *same* cycle or the same
starting node as the hand-roll, and the cycle appears in lore's error message to an agent —
so the served string changes. **Control:** pin the *set* of nodes in the reported cycle and
that the message names them, not the exact rotation.

**P8b — `graph_surreal.SurrealCodeGraph.blast_radius` / `_reverse_neighbours` /
`_reference_source_index` / `_dead_code_candidates`, and `graph.CodeGraph._liveness_sources`.**
These are a hand-rolled bounded reverse-BFS, an in-memory adjacency index, and a reachability
sweep — all things `networkx` owns (`nx.descendants_at_distance`, `nx.DiGraph.predecessors`,
reverse views). **Verdict: deferred to the P7 decision.** If networkx lands, these migrate
with it and the case is much stronger than `_page_rank` alone (they are more code and more
error-prone than a power iteration). If networkx does not land, KEEP — they are correct,
bounded, and store-backed in ways a generic in-memory graph library would not be (the BFS
issues a store query per hop; loading the whole graph into a `nx.DiGraph` is a different
performance profile, not obviously better). **I did not measure the store-query-per-hop vs
load-whole-graph trade — that is unverified and would need measuring before anyone acts.**

---

## P9 — dependency-declaration defects (found while verifying the above)

`[source-verified]`

1. **`pydantic-settings>=2.14` is a DECLARED direct dependency of `loremaster` and is
   imported NOWHERE in the workspace.** `grep -rn 'pydantic_settings' --include='*.py'
   loremaster lorescribe loresigil scripts` returns **zero** hits. It ships in the image and
   nothing uses it.
   *Either* adopt it — `[library-verified, pydantic-settings 2.14.1]` it exports
   `YamlConfigSettingsSource`, which is precisely what `loremaster.config.load_config`
   hand-rolls (`Path.read_text` → `yaml.safe_load` → `LoreConfig.model_validate`), and
   `EnvSettingsSource`/`SecretsSettingsSource`, which is what `resolve_secret` hand-rolls —
   *or* delete the declaration. Status quo is a maintenance claim on nothing.
   **My recommendation: adopt it for `load_config`.** It is a genuine "the package does the
   job" case and the dependency is already paid for. Caveat I could not settle: lore's
   `_StrictModel` uses `extra="forbid"` and `load_config` deliberately fails LOUD on an
   unresolvable secret at load time — confirm `BaseSettings` preserves both before swapping.
2. **`websockets` is imported by `loremaster.store._txn`
   (`from websockets.exceptions import WebSocketException`, used to build
   `_CONNECTION_ERRORS`) but is NOT in `loremaster/pyproject.toml`'s dependency list.** It
   arrives only transitively via `surrealdb`. If `surrealdb` ever swaps its transport,
   `_txn.py` fails at **import time** — i.e. the whole server, not one feature. One line in
   `pyproject.toml` closes it. This is not a "package vs hand-roll" finding; it is a defect I
   hit while doing the sweep, and scope law says it gets surfaced.

---

## T3 — candidates I examined and deliberately did NOT recommend replacing

Listing these matters as much as the replacements: an unexplained absence reads as an
oversight, and the next scout re-does the work.

**T3.1 — `server.AppContext._render_age` vs `humanize`. Verdict: GENUINELY BESPOKE / KEEP.**
The output is a pinned served format: largest-fit single unit, no padding, boundaries
`<120s → s`, `<120m → m`, `<48h → h`, else `d`, named in design doc §9 and carried by
`_COMMS_AGE_*_CEILING` constants. `humanize.naturaldelta` produces prose ("2 minutes"), not
`42m`. The library does not do this job. `[source-verified; humanize not introspected —
this rests on the format shape, labelled: my judgement on humanize's output form]`

**T3.2 — `AppContext._path_similarity` / `_nearest_indexed_paths` vs `difflib`.
Verdict: KEEP.** `difflib.get_close_matches` scores on character-sequence similarity; lore's
metric is `max(common leading path segments, common trailing path segments)`, which is
deliberately path-aware — `a/b/c.py` vs `x/y/c.py` scores 1 under lore's metric (same
basename) and poorly under difflib's. Different, better-targeted semantics for a
"did you mean this indexed path?" teach. **[my judgement, on read source of both]** —
I did not empirically compare their outputs on a real path corpus, and if anyone wants to
overturn this, that comparison is the experiment.

**T3.3 — the SurrealQL layer (`store/surreal_schema.py`'s ~880-LOC DDL emitter,
`store/surreal.py::_build_where` / `_build_fulltext_predicate` / `_hybrid_statement`,
`graph_surreal.py::_prefix_range_query`, `_txn.py::compose` / `_assert_envelope_integrity`).
Verdict: GENUINELY BESPOKE.** `[library-verified, sqlglot 30.8.0]` sqlglot is installed and is
the obvious candidate; I enumerated its dialects — 32 of them, ATHENA through TSQL — and
**there is no SurrealDB/SurrealQL dialect**. SurrealQL's `DEFINE FIELD OVERWRITE`,
`search::rrf`, `RELATE`, and record-id syntax are not SQL. No maintained Python SurrealQL
builder exists that I am aware of, and the `surrealdb` 2.0 SDK ships none.
This is domain code and should stay hand-rolled. Two notes, though, that are *not* package
findings: `_build_where`'s injection defence is a hand-maintained column allow-list
(`_ALLOWED_FILTER_KEYS`) — an allowlist, which is the correct posture per this repo's own
law — and `compose`/`_assert_envelope_integrity` are a hand-rolled statement-smuggling guard
whose correctness rests on regex scanning for `;`/`BEGIN`/`COMMIT`. Both are exactly the kind
of bespoke security surface that deserves its own adversarial review; that is beyond this
mission's brief and I am flagging, not auditing.

**T3.4 — `sanitise.py` (control-char class, fence sizing). Verdict: GENUINELY BESPOKE.**
The character class is a curated, documented set (C0/C1, DEL, bidi overrides and isolates,
zero-widths, U+2028/2029) chosen for a specific threat (a rendered line forging a second
citation row in an agent's context). No library encodes that policy.
**Correction to a subagent claim I was given:** one of my Explore agents reported the
fence-width formula as "duplicated three times". I re-derived it. The *primitives* ARE
shared — `loremaster.sanitise.max_backtick_run` and `MIN_FENCE_WIDTH` are imported by
`render.py`, `search.py`, and `server.py`. What is cloned is the one-line **expression**
`max(MIN_FENCE_WIDTH, max_backtick_run(x) + 1)` (in `render.render_fenced` and
`search.SearchPipeline._fence_width`), and `server.py` separately re-derives fence
*detection*. That is a much milder finding than "duplicated three times" implies — but the
`+ 1` is a render-safety **policy**, and by this repo's law a policy is a function, not an
expression to retype. Recommend promoting `fence_width(text) -> int` into `sanitise.py`
alongside the primitives it already owns. **Reporting the corrected version, and the
correction, because an un-derived count inherited from a subagent is exactly the failure
this repo's CLAUDE.md documents against itself.**

**T3.5 — `store/query_text.py`. Verdict: GENUINELY BESPOKE.** Its constants are
live-measured engine limits (117 OR-clauses / 114 AND-clauses before SurrealDB's parser
recursion limit). No library knows those. `truncate_at_word_boundary` is near-`textwrap.shorten`,
but `shorten` collapses all whitespace and appends a placeholder — different output. KEEP.

**T3.6 — `store._txn.retry_on_conflict`. Untouched — #202 owns it, and its KEEP is correct.**

**T3.7 — small stdlib wins, low value, listed for completeness.**
`server.AppContext._render_comms_skew_breakdown` counts frequencies with
`d[k] = d.get(k, 0) + 1` where `collections.Counter` exists;
`search.SearchPipeline._select_enrichment_targets` full-sorts then slices where
`heapq.nlargest` exists; `server._extension_tool_wrapper` synthesises a function signature by
assigning `__signature__`/`__annotations__` onto a closure, which is what `makefun`
(not installed) does properly. **All three: my judgement is these are below the churn
threshold** — they work, they are small, and none is a correctness risk. Recorded so the next
scout does not re-find them and think they were missed.

---

## SCOPE — things I found that are NOT this mission's, surfaced rather than buried

Per scope law, everything I noticed. None of these is mine to fix.

1. **`calibration` probe dies permanently on a 408/409** — see §P2 defect 2. This is a live
   behavioural defect independent of whether the SDK swap is taken.
2. **`load_api_key` cannot read `export KEY=…`** — see §P3. Live parser gap.
3. **`websockets` imported but undeclared** — see §P9.2. Import-time failure risk.
4. **`pydantic-settings` declared but unused** — see §P9.1.
5. **`SearchPipeline._wait_for_fresh` polls a full-table read every 50ms.**
   `_WAIT_POLL_INTERVAL_S = 0.05`, and each poll calls
   `self._manifest.all_files()` and filters in Python
   (`_all_rows_indexed_for_path`). On a large project that is up to 20 full manifest scans
   per second for the duration of a `wait_for_fresh=True` search. A path-scoped query would
   be O(rows-for-that-path). `[source-verified; I did not measure the actual cost — the
   concern is structural, the magnitude is unmeasured.]`
6. **The `_to_aware_utc` / `_require_aware_utc` family is replicated FIVE times**
   (`tasks.py`, `findings.py`, `briefs.py`, `messages.py`, `agents.py`), with a sixth
   variant in `server.AppContext._parse_rollup_since`. Two things about it:
   (a) it is a datetime-**parsing policy** cloned six ways, which is the ONE-IMPLEMENTATION
   law's exact target; and (b) **its `Z` → `+00:00` string patch is dead code on this
   Python.** `[library-verified, CPython 3.14]`
   `datetime.fromisoformat("2026-07-25T12:00:00Z")` → `2026-07-25 12:00:00+00:00`, and
   `fromisoformat` also truncates nanosecond precision without raising. The patch was needed
   before 3.11; the repo targets 3.14.
   *(One of those six, `tasks.TaskLedger._to_aware_utc_ceiling`, adds exactly one microsecond
   to compensate for nanosecond→microsecond truncation on decode — that one is real,
   load-bearing cursor arithmetic and is NOT redundant.)*
7. **`StoreReadTool._reject_uncontained` is a second, lexical-only re-implementation of the
   path-traversal guard**, and its own docstring concedes it "mirrors the lexical step (1)"
   of `SnapshotLayout._safe_path`. A **containment check is a security policy**; two copies
   means a hardening applied to one may not reach the other. Same class as items 6 — but this
   one guards a traversal, so it ranks above them.
8. **Broad ONE-IMPLEMENTATION duplication in the store layer**, located by subagent and
   **not individually verified by me** — labelling that clearly: `_ensure_connection` +
   `_drop_connection` + `_connect_lock` replicated across ~8 modules (~600 LOC aggregate);
   `_bare_id` ×6; `_as_rows` ×6–7; `_first_count`/`_extract_group_count` ×3;
   `ImpactEngine._cap` and `DiffResult._cap` as two independent copies. #120 ledgers the
   `_query` seam specifically; the **connection-lifecycle scaffolding around it appears to be
   a separate and larger population.** No package fixes this — it is an in-house extraction —
   but it belongs in the same conversation. **Counts here are the subagent's, not
   re-derived by me; treat them as leads, not measurements.**

---

## DEFERRED — the unswept remainder, with a named owner-decision

`index/indexer.py` (2,041), `index/watcher.py` (1,141), `index/surreal_manifest.py`,
`index/reconcile.py`, `index/records.py`, `index/schema.py`, `index/cli.py`,
`index/manifest.py`, `memory/local.py` (1,351), `memory/backend.py`, `source/*`,
`calibration/baseline.py`, `agent_ref.py` — **~6,000 LOC, not swept.** A fourth Explore agent
was dispatched over exactly this set and had not returned at commit time.

These are the areas most likely to hold further finds, based on what the swept files taught:
watcher **debouncing/coalescing** (`watchfiles` and `watchdog`'s own utilities both do this),
indexer **batching and concurrency control**, **file hashing / change detection**, and
`sqlite_resilient`'s **integrity-probe-and-recreate** logic. Naming them so the gap is
deliberate rather than silent, per the "pin the miss" law.

**Decision point:** the operator (or lead) decides whether to commission a follow-up sweep
over this set. I recommend yes — it is a third of the package by line count and the
concurrency/debounce surface is exactly where a hand-rolled defect is expensive.
