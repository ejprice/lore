# REPORT-fastmcp-spike

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- deviations:
  - Added a 4th Q3 leg (stateless_http=True, the hosted config) beyond the brief's 3 legs — high-value, directly de-risks the actual deployment mode; [measured] pass.
  - Q1 observable is a module-level list shared via an in-thread server (still a REAL uvicorn/ASGI streamable-HTTP TCP transport, NOT in-memory; in-memory run labeled separately).
- Packages considered: this spike EVALUATES a package (fastmcp 3.4.7) rather than building production mechanism. Every extension point used is fastmcp's own documented one, READ from installed source: `fastmcp.server.middleware.Middleware` (hooks), `fastmcp.server.auth.auth.TokenVerifier` (verify_token), `fastmcp.Client` + `fastmcp.client.auth.BearerAuth`, `uvicorn` for the ASGI server. Verdict: `keep` — no hand-roll; the spike's job was to confirm fastmcp covers the need. It does.
- Reuse ledger: 4 new symbols, all THROWAWAY spike-local subclasses of fastmcp bases (`RefuseMutationMiddleware`, `HideMutationMiddleware`, `PrincipalProbeMiddleware`, `StaticTokenVerifier`) — none reusable production code; they exist only to exercise the fastmcp API. No production symbol introduced.
- Graded: n/a (this is a build-and-measure spike, not a verdict over another artifact's code; HEAD-at-report `91fc30e`).
- decisions-needed:
  - **Recommendation for packet 39 (operator/lead call):** the packet-39 seam WORKS as-is, but prefer migrating the principal read to `fastmcp.server.dependencies.get_access_token()` (strict superset). See Q3 rider. Not a blocker.
- receipt POINTERS:
  - Env/versions → §Env
  - Q1 (wire gating + control) → §Q1, harness `scratchpad/fastmcp-spike/q1_call_tool.py`
  - Q2 (list hiding + control) → §Q2, harness `q2_list_tools.py`
  - Q3 (principal seam, 4 legs) → §Q3, harness `q3_principal.py`
  - GO/NO-GO → §Verdict
  - API surprises → §API-notes; instruments pasted verbatim → §Instruments

---

## Env  [measured]
Isolated `uv` project at `scratchpad/fastmcp-spike/` (NOT lore's tree — nothing under
`loremaster/`/`loresigil/`/`lorescribe/`/`lorerunes/`, `pyproject.toml`, or `uv.lock` was
touched). Dependency pin: `fastmcp>=3.4,<4` (the 3.x migration target, not the 4.0 beta).

```
fastmcp==3.4.7        <- installed; matches migration target
mcp==1.29.0           <- the SDK fastmcp wraps
starlette==1.6.0
uvicorn==0.52.3
httpx==0.28.1
pydantic==2.13.4
python 3.12.13        (venv; host default is 3.14.6, pinned project to 3.12)
```

Re-run: `cd scratchpad/fastmcp-spike && uv run python q1_call_tool.py`
(then `q2_list_tools.py`, `q3_principal.py`). Shared harness: `spike_common.py`.

**Method/honesty:** every fastmcp symbol used was READ from the installed 3.4.7 source via
`inspect.getsource` / `inspect.signature` before use — none coded from memory or from the
brief's guessed names. Introspection findings drove the harness (see §API-notes).

---

## Q1 — Does `on_call_tool` refuse BEFORE the tool body runs, over a REAL transport?  → YES  [measured]

Setup: two tools `read_thing` (read-only) and `mutate_thing`. `mutate_thing`'s body appends
to a module-level `MUTATE_CALLS` list (the OBSERVABLE side effect — proves the body ran).
`RefuseMutationMiddleware.on_call_tool` raises `fastmcp.exceptions.ToolError` **before**
`await call_next(...)` when the tool is `mutate_thing`. Driven by a `fastmcp.Client` over a
real uvicorn/ASGI **streamable-HTTP** server on a TCP port (`http://127.0.0.1:PORT/mcp`).

Verbatim results:
```
[WIRE] refuse=True  -> mutate_thing
    client saw refusal : True  (ToolError: refused: read-only enforcement (on_call_tool))
    MUTATE_CALLS after : []            <- ORACLE: body NEVER ran
[WIRE] refuse=False -> mutate_thing  (POSITIVE CONTROL)
    client saw refusal : False
    MUTATE_CALLS after : ['mutated']   <- CONTROL: harness CAN see execution
[IN-MEMORY] refuse=True  -> refused=True,  effect=[]          (matches)
[IN-MEMORY] refuse=False -> refused=False, effect=['mutated'] (matches)
```
- **Oracle:** after a refused `mutate_thing`, `MUTATE_CALLS == []` — the body never executed.
- **Positive control (required):** with refusal disabled, `MUTATE_CALLS == ['mutated']` — the
  harness demonstrably observes body execution, so the empty result above is meaningful, not
  a blind spot.
- In-memory transport agrees (labeled separately).

**→ The "guard is live in-process but dead on the wire" failure mode does NOT occur.** The
refusal executes over real streamable-HTTP and the body is never reached.

---

## Q2 — Can `on_list_tools` hide a tool from `tools/list` on the wire?  → YES  [measured]

`HideMutationMiddleware.on_list_tools` calls `call_next`, then filters `mutate_thing` out of
the returned `Sequence[Tool]` for the hosted case. Client `list_tools()` over the wire:
```
[WIRE] hide=True  (hosted)  list_tools -> ['read_thing']                 <- filtered
[WIRE] hide=False (control) list_tools -> ['mutate_thing', 'read_thing'] <- both
```
- **Control:** without the filter both tools are advertised — so the single-tool result is
  the filter's doing, not a build artifact.

---

## Q3 — Where does fastmcp 3.x surface the principal to middleware, and does packet 39's seam survive?  [measured]

Auth stood up with a static `TokenVerifier` subclass (the documented extension point;
`FastMCP(auth=<TokenVerifier>)`), mapping one bearer token → principal
`client_id="hosted-principal-xyz"`, scopes `["read","mutate"]`. Client sends the token via
`fastmcp.client.auth.BearerAuth`. From **inside** `on_call_tool` the probe reads BOTH:
1. **`mcp.server.auth.middleware.auth_context.get_access_token()`** — packet 39's assumed seam (SDK ambient contextvar).
2. **`fastmcp.server.dependencies.get_access_token()`** — fastmcp's own accessor.

Four legs, verbatim analysis:
```
A control (no-auth -> both seams None)          : True
B stateful  SDK contextvar  -> principal        : True   (packet-39 seam)
B stateful  fastmcp dep     -> principal        : True
C bad token rejected at transport               : True  (401 Unauthorized; middleware never ran)
D stateless SDK contextvar  -> principal        : True   (packet-39 seam, hosted config)
D stateless fastmcp dep     -> principal        : True
```
Leg B/D captured principal (both seams, identical):
```json
{"client_id": "hosted-principal-xyz", "scopes": ["read","mutate"],
 "type": "fastmcp.server.auth.auth.AccessToken"}
```
- **Control A** (no auth configured): both seams read `None` — the read discriminates; it is
  not a constant.
- **Control C** (bad token): rejected at the transport with **401** before middleware runs —
  auth is enforced by fastmcp itself, upstream of the enforcement middleware.
- **Leg D** (stateless_http=True — the typical HOSTED config, fresh transport per request):
  the packet-39 seam still yields the principal.

**VERBATIM which mechanism yields the principal:** BOTH
`mcp.server.auth.middleware.auth_context.get_access_token()` (packet-39 seam) AND
`fastmcp.server.dependencies.get_access_token()` return the authenticated principal from
inside `on_call_tool`, in both stateful and stateless streamable-HTTP.

### Q3 rider — the one thing to know (trust-doctrine caveat)
These are **two DISTINCT functions** (`fmcp_gat is sdk_gat` → `False`). fastmcp's own
`get_access_token` is a **strict superset**: its docstring (read from installed source) says it
reads the principal from the **HTTP request scope FIRST**, *"which is more reliable for
long-lived connections where the SDK's auth_context_var may become stale after token refresh"*
(fastmcp issues #1863/#3095), then falls back to the SDK contextvar, then to a task snapshot.

**Bound I did NOT close (named, per the trust doctrine — this is where a false clear would
hide):** my spike exercised a **single short-lived authenticated request with a static,
non-refreshing token**. I did **NOT** reproduce a long-lived connection with mid-session
token refresh — the exact scenario fastmcp hardened its request-scope-first path against.
So "the SDK contextvar seam works over the wire" is TRUE and [measured] **for that request
shape**; it is **not** a measurement that the raw SDK contextvar stays correct under token
refresh on a long-lived hosted session. Re-open trigger: if packet 39's hosted principal uses
refreshable tokens on long-lived streamable-HTTP sessions, that case must be measured before
relying on the raw contextvar.

Also not exercised (spike scope): a real OAuth/IdP flow (used a static verifier — same
principal-surfacing path, no live IdP), and concurrent distinct principals (contextvar is
per-async-task so expected-isolated, unmeasured).

---

## Verdict — GO/NO-GO on the two hypotheses

**H1 — "fastmcp middleware gates on the wire (dissolves the dead-on-the-wire blocker)":
GO.** [measured] `on_call_tool` refuses before the tool body over real streamable-HTTP
(Q1, with a valid positive control); `on_list_tools` hides a tool from `tools/list` over the
wire (Q2, with control). The read-only enforcement posture packet 39 assumes is achievable
with fastmcp 3.x middleware. The "live in-process, dead on the wire" blocker is **dissolved**.

**H2 — "packet 39's `get_access_token` seam is portable vs must-be-rewired": PORTABLE
(GO), with a recommended upgrade.** [measured] The exact packet-39 import
`mcp.server.auth.middleware.auth_context.get_access_token()` yields the authenticated
principal from inside `on_call_tool` in both stateful and stateless streamable-HTTP. It does
**not** need rewiring to function.
**Recommendation (not a blocker):** prefer `fastmcp.server.dependencies.get_access_token()`
anyway — it is a strict superset fastmcp hardened for the long-lived/token-refresh case, and
falls back to the SDK contextvar regardless, so it can only be more robust. Adopting it also
keeps packet 39 on fastmcp's supported surface rather than reaching into the wrapped SDK's
internals. If the hosted deployment uses refreshable tokens on long-lived sessions, treat this
as the safer default and close the unmeasured-refresh bound above.

---

## API-notes — surprises vs the brief  [measured, read from installed source]
- **Two `get_access_token` functions** (the key Q3 finding): the SDK's
  `mcp.server.auth.middleware.auth_context.get_access_token` (raw contextvar read) and
  fastmcp's own `fastmcp.server.dependencies.get_access_token` (request-scope-first superset).
  Distinct objects. The brief assumed only the former.
- **TokenVerifier** is the right extension point: `fastmcp.server.auth.auth.TokenVerifier`,
  subclass and implement `async def verify_token(self, token: str) -> AccessToken | None`.
  `FastMCP(auth=<TokenVerifier>)` wires it directly — no OAuth provider needed for bearer.
  (An `InMemoryOAuthProvider` also exists but is a full OAuth flow — overkill for enforcement.)
- **Middleware surface:** `fastmcp.server.middleware.Middleware`; hooks `on_call_tool`,
  `on_list_tools`, etc. Params arrive as `context.message` (a `CallToolRequestParams` with
  `.name`/`.arguments` for calls; a `ListToolsRequest` for lists). Refuse by raising
  `fastmcp.exceptions.ToolError` before `call_next`. `on_list_tools` returns a filterable
  `Sequence[Tool]`.
- **Transport:** `mcp.http_app(path="/mcp", transport="http")` is streamable-HTTP; default
  path is `/mcp`; `stateless_http=True` is a param on `http_app`. Client auto-selects
  `StreamableHttpTransport` from an `http://` URL; bearer via `fastmcp.client.auth.BearerAuth`.
- **Auth is enforced upstream of middleware:** a bad/absent bearer against an authed server
  is a 401 at the transport; enforcement middleware only ever sees authenticated requests.

## Instruments  [pasted so the claims are re-runnable without the scratch tree]
The load-bearing harness is 4 files in `scratchpad/fastmcp-spike/`. Because scratch trees are
disposable, the two smallest are pasted here verbatim; `spike_common.py` and `q3_principal.py`
are larger — re-create by re-running the introspection in §API-notes or see the scratch dir
while it exists. The middleware/verifier core (the part a reader needs to trust Q1/Q3):

```python
# from spike_common.py  (verbatim core)
MUTATE_CALLS: list[str] = []

class RefuseMutationMiddleware(Middleware):
    def __init__(self, refuse): self.refuse = refuse
    async def on_call_tool(self, context, call_next):
        if self.refuse and context.message.name == "mutate_thing":
            raise ToolError("refused: read-only enforcement (on_call_tool)")  # BEFORE call_next
        return await call_next(context)

class HideMutationMiddleware(Middleware):
    def __init__(self, hide): self.hide = hide
    async def on_list_tools(self, context, call_next):
        tools = await call_next(context)
        return [t for t in tools if t.name != "mutate_thing"] if self.hide else tools

class PrincipalProbeMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        from mcp.server.auth.middleware.auth_context import get_access_token as sdk_gat  # packet-39 seam
        from fastmcp.server.dependencies import get_access_token as fmcp_gat            # fastmcp's own
        rec = {}
        try:   t = sdk_gat();  rec["sdk_contextvar"]     = None if t is None else {"client_id": t.client_id, "scopes": list(t.scopes)}
        except Exception as e: rec["sdk_contextvar"]     = f"RAISED {type(e).__name__}: {e}"
        try:   t = fmcp_gat(); rec["fastmcp_dependency"] = None if t is None else {"client_id": t.client_id, "scopes": list(t.scopes)}
        except Exception as e: rec["fastmcp_dependency"] = f"RAISED {type(e).__name__}: {e}"
        PRINCIPAL_CAPTURE[context.message.name] = rec
        return await call_next(context)

class StaticTokenVerifier(TokenVerifier):
    def __init__(self, token, client_id, scopes):
        super().__init__(); self._token, self._client_id, self._scopes = token, client_id, scopes
    async def verify_token(self, token):
        return AccessToken(token=token, client_id=self._client_id, scopes=self._scopes) if token == self._token else None

# serve_http: mcp.http_app(path="/mcp", transport="http", stateless_http=...) run under
# uvicorn.Server in a daemon thread; poll server.started; Client(url, auth=BearerAuth(tok)).
```
