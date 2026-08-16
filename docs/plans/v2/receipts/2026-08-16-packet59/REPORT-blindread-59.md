# REPORT-blindread-59 — contract-blind diff read of packet 59 (fastmcp 3.x substrate swap)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done (report-only; I never fix). Blindness intact — read NO withheld file.
- **Model:** claude-opus-4-8 (env `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8`; opus48-worker pin — attested, not introspected).
- **Deviations:** none. (lore_comms heartbeat hit a transient `:18500` store error mid-run — retried; not a finding.)
- **Packages considered:** none — no mechanism specified (auditor). I *read* installed `fastmcp` 3.x source to VERIFY a code claim (`get_http_headers` header-exclusion) — that read is the basis of F1.
- **Reuse ledger:** none (no new symbols introduced).
- **Graded:** worktree (UNCOMMITTED changes to `server.py`, atop `ee4bced`) · HEAD-at-report: `ee4bced` · SAME base. My verdict is over the working-tree `server.py`, which is modified-but-uncommitted; the diff IS that uncommitted delta.
- **Findings:** 6 (1 HIGH silent regression · 1 MED confirming+EXTENDING the builder's known one · 2 LOW · 1 LOW stale-prose · 1 NOTE new-rejection-surface). Plus 1 central un-diff-provable ASSUMPTION the acceptance must prove.
- **Decisions-needed:** none from me — F1/F2 are defects to route to the builder; the operator/lead owns severity.
- **Receipt pointers:** F1 → §Findings/F1 (server.py:10075 + `.venv/…/fastmcp/server/dependencies.py:447`); F2 → §Findings/F2; FILES-READ RECEIPT at end.

---

## Frame
I read the PRODUCTION diff (`git diff ee4bced -- server.py`; auth.py is byte-identical at base and worktree — the whole migration is in `server.py`), the pre-images of every deleted block (`git show ee4bced:server.py` via the diff), and the touched worktree functions in full. Orientation only: design §0–§3. My question is never "does it satisfy the contract" — it is *"for every input the migrated code receives, what is its FATE, and what did the deleted code DO that the new code does not?"*

The reshape is: DELETE `_ProcessLifespanGuard` (ref-counted per-process lease) + `_EagerStartupLifespan` (~150-LOC ASGI lifespan interceptor) + the `TracingFastMCP(FastMCP)` subclass; REPLACE with fastmcp's native `lifespan=` (+ `_eager_build_with_retry` for boot resilience) and a `ToolTraceMiddleware(on_call_tool)`; move host/port to the uvicorn call site, `version=`/mount-path/`host_origin_protection` to the fastmcp ctor + `http_app()`.

---

## FINDINGS (behaviour present-at-base / absent-now / replacement / why it matters)

### F1 — HIGH · SILENT REGRESSION: every trace row's `transport_session` correlator is now ALWAYS `None`
- **Present at `ee4bced`:** `_record_tool_trace` read the transport correlator off the RAW request headers:
  `request = getattr(request_context, "request", None); headers = getattr(request, "headers", None); transport_session = headers.get("mcp-session-id") …` — so a streamable-HTTP call's `mcp-session-id` was captured and stored.
- **Absent now (worktree `server.py:10075`):** `transport_session = get_http_headers().get(_TRACE_TRANSPORT_SESSION_HEADER)` where `_TRACE_TRANSPORT_SESSION_HEADER = "mcp-session-id"` (`server.py:9926`).
- **What replaces it — and why it's dead:** fastmcp's `get_http_headers()` is called with its DEFAULT `include_all=False`. I READ the installed source (`.venv/lib/python3.14/site-packages/fastmcp/server/dependencies.py:410-464`): with `include_all=False` the exclude set contains **`"mcp-session-id"`** (line 447, under `# MCP-related headers`). So `get_http_headers()` NEVER returns that key, and `.get("mcp-session-id")` is **`None` for every traced HTTP call** — not just the no-request case the docstring anticipates.
- **Why it matters:**
  1. It is a SILENT telemetry regression on a TRUST surface. The `transport_session` column is persisted on every trace row (`store/surreal.py:780,858`; `store/surreal_schema.py:725 TRACE_TRANSPORT_SESSION_FIELD`); the new server writes it `NULL` forever, so the correlator data is permanently lost for this deployment's window even though no reader queries it *today* (the index is "deliberately-withheld" per `surreal_schema.py:1131`).
  2. It is a **#107-class prose-vs-behaviour lie**: the new docstring (diff lines 397-400 / `server.py`) asserts *"MEASURED, never declared — the transport correlator off the request headers … an absent correlator reads None, not a crash."* The code never measures it — the header is stripped by the dependency it calls. The comment correctly handles the `{}`-when-no-request case and MISSES that the header is excluded even WITH a request.
- **The fix (for the builder, not me):** `get_http_headers(include={"mcp-session-id"})` (line 449-450 shows `include` subtracts from the exclude set) or `include_all=True`.
- **Verdict:** CONFIRMED (I byte-read the exclude set and the call site; no test run needed).

### F2 — MEDIUM · CONFIRMS + EXTENDS the builder's known dropped behaviour (eager-build-failure redaction)
The builder already found the fixed-phrase secret-non-leak. I confirm it and report that the reshape dropped **BOTH halves** of the deliberate redaction split, not only the phrase.
- **Present at `ee4bced`** (`_EagerStartupLifespan._drive_lifespan`, deleted block, pre-image diff lines ~955-968): on retry-budget exhaustion it did TWO things:
  (a) `logger.error("eager startup build failed", exc_info=last_exc)` — logged the REAL detail (traceback, which can carry a credentialed `surreal.url`/`base_url`) through **lore's redaction-backstopped sink**; and
  (b) `send({"type": lifespan.startup.failed, "message": _EAGER_BUILD_FAILED_MESSAGE})` — a FIXED operator-safe phrase to uvicorn, *because uvicorn logs the startup-failed message UNREDACTED* (that rationale is verbatim in the deleted `_EAGER_BUILD_FAILED_MESSAGE` comment, diff lines 783-790).
- **Absent now:** `_eager_build_with_retry` (`server.py:9851+`) on exhaustion does `raise last_exc` — nothing else. Between attempts it logs `logger.warning(… , extra={attempt,max_attempts})` with **no `exc_info`**. So on final failure:
  - (a) the redacted operator diagnostic (`logger.error(exc_info=…)`) is **GONE** — the only record of *why* startup failed is whatever uvicorn/Starlette prints;
  - (b) the raw exception now propagates into fastmcp's `lifespan=` → Starlette lifespan startup failure → **uvicorn logs the traceback UNREDACTED**, and uvicorn's error logger is NOT on lore's redacting sink (server.py:2208 comment: lore's scoped handler "does not touch uvicorn's root"; the sink is `propagate=False`, lore-namespace-only).
- **Why it matters:** a boot-time SurrealDB/TEI outage carrying a credential in its transport exception now leaks that credential verbatim into the container startup log — the exact leak the deleted constant existed to prevent — AND operators lose the redaction-backstopped failure detail.
- **Verdict:** CONFIRMED at the diff level (deleted vs new code paths). Whether uvicorn prints `str(exc)` for a lifespan-startup exception is the standard Starlette/uvicorn behaviour the OLD code explicitly guarded against; the acceptance smoke can confirm on the artifact.

### F3 — LOW-MED · PLAUSIBLE: the trace "no request context" classification narrowed from quiet DEBUG to a loud exception
- **Present at `ee4bced`:** `_record_tool_trace` opened with `try: request_context = request_ctx.get() except LookupError: logger.debug("trace.emit.no_request_context"); return` — a SINGLE guard that cleanly caught EVERY context-less dispatch (in-process / no-request transport) as a quiet, expected DEBUG line.
- **Absent now (`server.py` new `_record_tool_trace`):** the guard is `if fastmcp_context is None: logger.debug("…no_request_context"); return`, then it dereferences `app_context = fastmcp_context.request_context.lifespan_context`. The intermediate `.request_context` is UNGUARDED — and the code's OWN sibling `_app_context` says (diff lines 551-554) *"fastmcp types `Context.request_context` as `RequestContext | None`"*. If any dispatch yields a non-None `fastmcp_context` with a `None` `request_context`, `.lifespan_context` raises `AttributeError` that escapes this function's local `except AttributeError` (which wraps only `_trace_write_store`) and is caught by the MIDDLEWARE's outer `finally … except Exception` → `logger.exception("trace.emit.failed")` — LOUD, with a stack trace.
- **Why it matters:** an expected context-less dispatch that logged quiet DEBUG at base could log a loud `trace.emit.failed` now. It does NOT corrupt the tool outcome (exception caught, result already returned) or the trace numerator (the write is simply skipped) — observability/log-noise only.
- **Bound (why PLAUSIBLE not CONFIRMED):** it fires only IF fastmcp represents a context-less dispatch as a non-None `MiddlewareContext.fastmcp_context` with a `None` `request_context`. I did not run the suite (blindness) so I did not exercise it; the narrowing (guard tests one node, dereference walks three) is a hard diff fact — the firing is the open half.

### F4 — LOW · extension-collision guard coverage narrowed from "the whole registry" to "declared universe + this loop"
- **Present at `ee4bced`:** `if spec.name in _ALL_BUILTIN_TOOL_NAMES or mcp._tool_manager.get_tool(spec.name) is not None: raise` — the second leg queried the ACTUAL registry (catching a name already registered by ANY path).
- **Absent now (`server.py:12059-12094`):** the registry query is replaced by a loop-local `registered_extension_names: set[str]`; the guard is `spec.name in _ALL_BUILTIN_TOOL_NAMES or spec.name in registered_extension_names`. (`mcp._tool_manager` is gone in fastmcp 3.x, so this is a forced re-architecture — design §3-P9.)
- **Bound — SAFE in practice, stated for completeness:** `_register_extension_tools` has exactly ONE call site (`server.py:12007`), and there are only TWO registration paths (built-ins via `_register_tools`'s `mcp.tool(...)` at :10428, extensions via this loop at :12091), both covered by the two legs. The narrowing only bites if a future/second registration pass, or an out-of-loop `mcp.tool`/`add_tool`, ever places a name on the registry that this loop-local set cannot see — the old registry query would have caught that; the new set will not.

### F5 — LOW · stale prose left by the reshape (natural-language-surface class)
`server.py:1005-1013` (NOT in the diff — unchanged code adjacent to it) still explains the "configure logging FIRST" ordering as defending against *"build_mcp_server, which constructs FastMCP, whose `__init__` runs `logging.basicConfig` with a root RichHandler (`mcp.server.fastmcp.utilities.logging.configure_logging`)."* That names the RETIRED `mcp.server.fastmcp` class. Under standalone `fastmcp` 3.x the constructed class is different; the described `__init__` behaviour is now unverified/stale prose. The CODE ordering (configure lore logging before construction) stays safe either way, so this is a doc-accuracy flag, not a behaviour loss — but it is exactly the "consistency-with-code no gate checks" surface P8d says clusters green-at-gate defects, and the migration touched the class this prose describes.

### F6 — NOTE (intentional per M12, but a served-behaviour change worth naming): `host_origin_protection=True` adds a NEW 421 rejection surface
`build_asgi_app` now calls `mcp.http_app(path=…, host_origin_protection=True, allowed_hosts=_resolve_allowed_hosts(config))`. At base there was NO framework Host validation (`transport_security` unset). This is a NET-NEW rejection path: a request whose `Host` is not a fastmcp DEFAULT_HOST (127.0.0.1/localhost/::1), not the configured bind host, and not in `LORE_ALLOWED_HOSTS`, is now **421'd** where base served it.
- Design §1 says "the same … auth behaviour; any diff in auth posture is a DEFECT" — M12 RULES this specific change a deliberate benefit, so it is intentional. I flag it because: (a) it IS a served-behaviour change, landing on any proxied/non-loopback deploy that hasn't set `LORE_ALLOWED_HOSTS`; the loopback dogfooding deploy is covered by DEFAULT_HOSTS + bind host; (b) M12's own rider says the ordering of `host_origin_protection` vs the TokenVerifier is spike-gated — the diff enables it but does not (and cannot) establish that ordering, so "what falls through the new guard vs the Bearer layer" is delegated to acceptance.

---

## CENTRAL ASSUMPTION THE DIFF CANNOT PROVE (not a finding — a delegation the acceptance must close)
The entire ~150-LOC deletion rests on fastmcp entering `lifespan=` **ONCE PER PROCESS, eagerly at ASGI startup** (design M11). The diff cannot establish this; two legs:
- **Leg I verified BY ME (resolved — NOT a defect):** the ASGI `lifespan` scope reaches fastmcp's app. Both bespoke middlewares pass every non-HTTP scope straight through — `BearerAuthMiddleware.__call__` (`auth.py:228-232`) and `OriginValidationMiddleware.__call__` (`auth.py:310-314`) both do `if scope.get("type") != _HTTP_SCOPE_TYPE: await self._app(scope,…); return`. So `OriginValidationMiddleware(inner)` (and the Bearer wrap) do NOT swallow the lifespan — fastmcp's `http_app()` lifespan is driven by uvicorn exactly as `_EagerStartupLifespan` was. The classic "middleware swallows lifespan → heavy build never runs" bug is NOT present.
- **Leg II the acceptance still owes** (fastmcp-internal, spike/§6.6's job): that fastmcp's `lifespan=` (a) runs at container START, not lazily on the first client session (the deleted `_EagerStartupLifespan` docstring named the "dead index that looks up" failure it hoisted the build to avoid), and (b) runs EXACTLY ONCE across N concurrent MCP sessions (the deleted `_ProcessLifespanGuard`'s whole reason — otherwise a second watcher + second startup reconcile spawn, "two watchers risk manifest contention"). The acceptance must prove: with ≥2 concurrent sessions, exactly ONE probe-gate / ONE initial reconcile / ONE watcher, at process start.

Retry resilience itself IS preserved: `_eager_build_with_retry` re-homes `_acquire_eager_lease_with_retry` with the same `_DEFAULT_EAGER_MAX_ATTEMPTS=5` / `_DEFAULT_EAGER_BACKOFF_BASE_S=2.0` and the same `backoff.additive_jitter` (late-bound module attr, `loresigil.backoff`, `server.py:239`) fail-closed-after-budget policy.

## Behaviours I checked and found PRESERVED (no finding)
- host/port bind: dropped from the FastMCP ctor, but `uvicorn.Config(app, host=self._config.server.host, port=self._config.server.port,…)` (`server.py:1017-1023`) reads them from config directly — no loss (design D2).
- `version=`: `mcp._mcp_server.version = _resolve_version()` → `FastMCP(version=_resolve_version())` — resolved at construction either way.
- deleted-symbol residuals: grep of the `loremaster` package finds NO production references to `_ProcessLifespanGuard`, `_EagerStartupLifespan`, `_lore_eager_guard`, `_EAGER_BUILD_FAILED_MESSAGE`, `_LIFESPAN_*`, `streamable_http_app`, `request_ctx`, `ContentBlock` (only historical mentions inside docstrings/comments). Dropping `ContentBlock`/`MutableMapping`/`request_ctx` imports is safe (server.py no longer uses them; `MutableMapping` remains imported by `auth.py` for its own aliases).
- trace `ok` latch / cancellation shield / bounded emit: `on_call_tool` keeps the identical `ok=False → call_next → ok=True → finally{shielded+fail_after record}` shape with no `except` arm — `CancelledError` still latches `ok=False` and the tool outcome still wins (design M4).
- `_build_context` returning bare `AppContext` (was `(app_context, None)`): the second element was ALWAYS `None`, so the deleted `if client is not None: await client.close()` was dead in production; `AppContext.aclose()` teardown is preserved in the new lifespan `finally`.

---

## FILES-READ RECEIPT (every path I opened — check against the withheld set; NONE overlaps)
- `~/.claude/orchestration/brief-base.md`
- `docs/design/2026-08-15-fastmcp-3x-migration.md` (lines 1-120 — §0 rulings, §1-§3; ALLOWED orientation)
- `/tmp/pkt59-server.diff` (my own `git diff ee4bced -- server.py` output; 1158 lines — full read)
- `loremaster/loremaster/server.py` (worktree; read lines 1003-1027 + targeted greps of trace/uvicorn/registration/host-port sites; pre-images via the diff's `git show ee4bced:`)
- `loremaster/loremaster/auth.py` (lines 218-357 — Bearer/Origin `__call__` lifespan passthrough)
- `loremaster/loremaster/store/surreal_schema.py` (lines 1120-1149 — transport_session index/consumers)
- `.venv/lib/python3.14/site-packages/fastmcp/server/dependencies.py` (lines 405-474 — `get_http_headers` exclude set; dependency source, not repo code)
- `loremaster/loremaster/__init__.py`-level directory listing + git status (environment attest)

**Withheld set — CONFIRMED NOT OPENED:** `test_fastmcp_migration.py`, `test_trace_telemetry.py`, `test_wire_discipline.py`, `test_migration_wire.py`; `REPORT-contract-59{,b}.md`; `REPORT-adversary-59{,b}.md`; `REPORT-builder-59.md`. I did not run the test suite. Blindness intact.
