# REPORT-adversary-39-auth-4 — fourth adversary pass on the packet-39 Google-OAuth contract

`brief-base v9 read`

*Every measurement in this report was taken **2026-07-31** against lore contract commit
`c02d12a` on `feat/surreal-unification`, MCP SDK **1.27.2**, Python **3.14.6**, in scratch
trees minted by `./scripts/scratch_copy.sh`. Every "survives"/"reds" claim is dated to that
sha. Nothing here is a present-tense claim about a later tree.*

---

## SUMMARY BLOCK

- **state:** done-with-deviations · **VERDICT: CONTRACT INSUFFICIENT**
- **P1 HEADLINE — the class is NOT dead. `WB100` is a FOURTH DOOR in the same corridor.**
  The filter installed by rebinding `FastMCP.list_tools` **on the CLASS** after construction:
  `vars(mcp)` is clean (R16 instrument 1 blind), and in a **fresh process — the production
  shape, exactly one composed server** — a hosted Google principal's `tools/list` returns
  **15 tools including all six mutating ones** (correct build: 9). Worse than a clean
  survivor: it is **FLAKY-GREEN — 5 of 10 full-contract runs were 473/473**, because pytest
  constructs many servers per worker and only the FIRST is wire-dead. §4.1
- **Eight more wrong builds survive 473/473, each with a reference-build control.** Four are
  **REGRESSIONS caused by the R16 restructure itself** (the posture module went 70 → 49 pins;
  the report claims the 49 "cover what the 70 did" — measurably false): **WB106** forged
  `client_id` reaches `lore_remember` · **WB40** the served refused-set section is a
  hand-list again · **WB109** deny-by-default became deny-everything-NEW · **WB111** every
  unauthenticated local call is refused. Plus **WB103** (`resources/read` + `prompts/get`
  ungoverned) · **WB105** (`all_registered_tools()` scoped) · **WB110** · **WB104**. §4
- **SATISFIABILITY RE-DISCHARGED on THIS contract: 473 passed / 0 failed**, and **473/0 again
  after `ruff check --fix`**. `loremaster.__file__ = /home/ejprice/adv39-4/ref/loremaster/loremaster/__init__.py`. §3
- **Packages considered:** `mcp` 1.27.2 client stack → ⚑ **replace** (read
  `mcp/client/streamable_http.py::streamable_http_client(url,*,http_client=)` +
  `mcp/client/session.py::ClientSession.list_tools/call_tool` signatures — `WireSession`
  hand-rolls a JSON-RPC client the SDK ships) · `httpx.ASGITransport` → **keep** (read
  `_transports/asgi.py`) · `asgi_lifespan` → **keep, correctly adopted** · `cachetools`,
  `watchdog`, `email-validator`, `google-auth` → **agree with §2, no new read** · AST scanning →
  **bespoke, house idiom** (19 test modules already do it). §2
- **Prior-survivor re-run: 10 rebuilt, 8 killed, 2 alive** — `WB31` (truncated cache key,
  unadjudicated across FOUR passes) and ⚑ `WB40` (**regressed** — its killing pin was deleted). §5
- **P1b quantifier table: 17 invariants; 6 ∀-over-inputs, 11 guarded, 9 guarded rows carry a
  SURVIVING wrong build.** §6
- **P2:** two perturbation pairs proven both legs — the wire-discipline gate is defeated by
  **renaming a file** (identical content GREEN outside the glob, RED inside), and the WB93 pin
  discriminates in isolation but not in a module run. §7
- **P4:** the lead's `467 / 432 / 35` and the contract's `473 / 432 / 41` are the SAME run at
  two SCOPES (± `test_wire_discipline.py`'s 6). Both reproduce. §9
- **decisions-needed:** `WB31` (four passes unadjudicated) · the LOOPBACK edge-policy weakening
  the new wire pin forces · whether `resources/*`+`prompts/*` are in scope for the posture guard.
- **Receipt pointers:** §3 satisfiability · §4.1 the blocker · §4.2–4.9 survivors · §5 prior
  re-run · §6 quantifier table · §7 perturbation · §8 P6/P6b diff · §10 residuals · §12 the
  instruments, pasted verbatim.

---

## 1. Capability check (brief-base §4 — first, because a lead cannot see my toolset)

| Demanded by the brief | What I actually have | What I did instead | What a lead must change |
|---|---|---|---|
| `ToolSearch "select:mcp__lore_lore__lore_search,mcp__lore_lore__lore_impact"` | **Absent.** Two attempts: the brief's exact select-list → `No matching deferred tools found`; a keyword query (`lore search code symbols impact index`) after the `lore_lore` server had announced its instructions block → also nothing. | **Bare, anchor-free `grep` + `Read`** for every structural question (§8's sweep, the SDK reads, the deleted-pin diff), plus the two frame-independent instruments: the reference build run against the rest of the suite, and 21 wrong builds. **I claim graph-backed exhaustiveness nowhere.** | Finding **#294**, **fourth independent reproduction in this packet** (contract author, adversaries 1, 3, and now 4). The `contract-adversary` agent definition needs the lore tools; a smaller brief is not the fix. |
| `lore_findings action=report` | Not reachable (same cause). | Recorded here for the lead to file. | — |
| `SendMessage` | **Absent** (`ToolSearch "select:SendMessage"` → nothing). | Report file only; I cannot notify or stand by in a fleet. | Same agent-definition fix. |
| Everything else (Read/Write/Bash/Grep/Glob, `scratch_copy.sh`, the venv) | Available. | — | — |

**Deviation:** I read `REPORT-contract-39-auth-1.md` §2 (the package table) early, so my **P-PKG
is not frame-independent this pass**. Said plainly rather than dressed up as an independent
enumeration. My **P6b enumeration IS independent** — it is a name-level diff of the posture
module at `af74611` against `c02d12a`, derived from `git show`, before I read the report's
account of the restructure's coverage (§8.2).

---

## 2. P-PKG — my table, then the diff

### The mechanisms the R16 revision ADDS (the only ones not already surveyed at passes 1–3)

| mechanism | libraries evaluated | what I **READ** | verdict |
|---|---|---|---|
| **Driving a real MCP session against the assembled ASGI app** (`_auth_fixtures.WireSession` / `wire_session`) | `mcp` **1.27.2** client stack (installed, same dist) · `httpx` 0.28.1 `ASGITransport` (installed) | `mcp/client/streamable_http.py` — `streamable_http_client(url, *, http_client: httpx.AsyncClient | None = None, terminate_on_close: bool = True)` (signature introspected; the deprecated `streamablehttp_client` wraps it and constructs its own client). `mcp/client/session.py` — `ClientSession.__init__(read_stream, write_stream, …)`, `list_tools(cursor=None, *, params=None) -> ListToolsResult`, `call_tool(name, arguments=None, …) -> CallToolResult`. `mcp/shared/memory.py` — `create_client_server_memory_streams` (in-memory pair; **not** applicable, it bypasses the ASGI stack, which is the whole point of R16). | ⚑ **replace_with_adapter.** `WireSession` hand-rolls: the JSON-RPC envelope, `mcp-session-id` threading, `notifications/initialized`, and result parsing (`json.loads(body)["result"]["tools"]`). `streamable_http_client(http_client=httpx.AsyncClient(transport=ASGITransport(app=...)))` + `ClientSession` drives the SAME assembled app through the SDK's own client and returns **typed** `ListToolsResult`/`CallToolResult`. **This matters beyond tidiness: the hand-roll forces `mcp.settings.json_response = True`, so the "wire" R16 pins is the JSON-response wire and production's default is SSE (§10-R4).** |
| **Deriving the SDK's bound-handler names** (`sdk_bound_handler_names`) | stdlib `ast` + `inspect` · `astroid` (installed, via the repo's dead-code tooling) | `FastMCP._setup_handlers` source (printed, §4.1); `astroid` offers inference, not a registration model. | **bespoke — correct, and no library does this.** But its PARSE is under-specified: §4.10. |
| **AST-scanning test modules for forbidden call shapes** (`test_wire_discipline`) | `ruff` (no custom-rule plugin API) · `flake8` plugins (not installed) · stdlib `ast` | The repo already carries **19** `ast.parse`/`ast.walk` test-tree scanners (`test_retired_symbols.py`, `test_secret_typing.py`, `test_render_seam_pins.py`, …). | **bespoke, house idiom — agree.** Consistent with the repo's own instrument style; not a rogue hand-roll. |
| **Selecting the governed module set** (`POSTURE_MODULE_GLOB`) | stdlib `pathlib.Path.glob` | — | ⚑ **bespoke, and the WRONG PREDICATE** — a filename glob is a name-list wearing a wildcard. §7.1 proves it defeated by a rename. |
| **The unscoped registry accessor** (`all_registered_tools()`) | `mcp.server.fastmcp.tools.tool_manager.ToolManager` | `ToolManager.list_tools` = `list(self._tools.values())`. | **bespoke — correct** (it is a one-line un-override; there is nothing to install). |

### DIFF against `REPORT-contract-39-auth-1.md` §2 / design §14

| row | their verdict | mine | delta |
|---|---|---|---|
| `mcp` SDK (verifier/401/session) | replace | replace | agree |
| `mcp.server.transport_security` | replace_with_adapter | replace_with_adapter | agree — and see §4.9, the LOOPBACK branch is where it is now *unpinned* |
| `httpx` / `MockTransport` | keep | keep | agree |
| `httpx.ASGITransport` | keep_with_trigger | **the trigger has FIRED a second time** | The named trigger was *"the first auth pin needing cookies, redirects or multipart"*. It should have been *"the first pin needing a full MCP session"* — which R16 is. `ASGITransport` + the SDK's own `streamable_http_client` is the adapter. **New finding, not in their table.** |
| `asgi-lifespan` | escalate → installed & adopted | verified adopted, twin deleted | agree (`running_asgi_app` returns a real `LifespanManager`) |
| `cachetools` / `watchdog` / `email-validator` / `google-auth` | as §2 | **no new read this pass** — inherited from passes 1–3, stated as inherited | no delta claimed |
| **the MCP CLIENT stack** | ⚑ **not surveyed on either side** | **replace_with_adapter** | ⚑ **the R16 revision specified a mechanism the SDK ships and neither side asked.** A builder will build `WireSession` exactly as written. |

---

## 3. THE SATISFIABILITY RECEIPT, re-discharged on THIS contract

Predecessors' receipts are void (the posture module was rewritten and a module was added). I
built the reference implementation by porting pass-3's production files into a **fresh
`scratch_copy.sh` tree at `c02d12a`** and adding what R16 newly demands: `all_registered_tools()`
on the scoped manager, worst-case `_EXTENSION_TOOL_ANNOTATIONS`, and a LOOPBACK
`transport_security` (see §4.9 — that last one is itself a finding).

```
$ ./scripts/scratch_copy.sh /home/ejprice/adv39-4/ref        # exit 0, provenance asserted
$ cd /home/ejprice/adv39-4/ref && uv run python -c "import loremaster,lorerunes;..."
PROVENANCE loremaster: /home/ejprice/adv39-4/ref/loremaster/loremaster/__init__.py
PROVENANCE lorerunes:  /home/ejprice/adv39-4/ref/lorerunes/lorerunes/__init__.py
```

`CONTRACT` = `lorerunes/tests` + the eight loremaster modules **including
`test_wire_discipline.py`** ⇒ **473 collected = 472 contract pins + the pre-existing
`lorerunes/tests/test_smoke.py`**.

```
$ uv run pytest $CONTRACT -p no:randomly -n auto -q --tb=line
473 passed in 7.59s
```

**The post-ruff leg** (the harder half — the orphaned imports that deleting
`BearerAuthMiddleware` forces):

```
$ uv run ruff check .          → Found 1 error.  [*] 1 fixable
$ uv run ruff check --fix .    → Found 1 error (1 fixed, 0 remaining).
$ uv run ruff check .          → All checks passed!
$ uv run pytest $CONTRACT -p no:randomly -n auto -q --tb=line
473 passed in 7.85s
```

**The contract is SATISFIABLE, 0-failed, before and after the lint cleanup.** No C-DEF.

---

## 4. P1 — wrong builds. **21 run; 9 SURVIVE 473/473.**

Harness discipline (mechanism pasted §12.1): every patch anchor must match **exactly once**
(hard error otherwise), and every run's COLLECTED total is compared against 473, so a mutation
that fails to land or that breaks collection cannot be mistaken for a survivor. Every survivor
below carries a **CONSEQUENCE PROBE with a reference-build control**, because a survivor that
does not differ observably from the correct build is not a finding.

| build | what it does | verdict |
|---|---|---|
| **WB100** | `FastMCP.list_tools` rebound **on the CLASS** after construction | ⚑ **SURVIVES — BLOCKER** |
| **WB106** | posture guard short-circuits on `client_id.startswith("api_key:")` | ⚑ **SURVIVES — regression, pin deleted** |
| **WB40** | the served refused-set section is a hand-list | ⚑ **SURVIVES — regression, pin deleted** |
| **WB109** | read-only classification is a hand-list of the nine core names | ⚑ **SURVIVES — orphan, pin deleted** |
| **WB111** | unauthenticated CALL refused; LIST still unfiltered | ⚑ **SURVIVES — orphan, pin deleted** |
| **WB110** | hosted refusal section installed in LAN_BEARER too | ⚑ **SURVIVES — orphan, pin deleted** |
| **WB103** | `resources/*` + `prompts/*` carry no posture scoping | ⚑ **SURVIVES** |
| **WB105** | `all_registered_tools()` is itself scoped | ⚑ **SURVIVES** |
| **WB104** | LOOPBACK allows the public hostname (protection ON) | ⚑ **SURVIVES** |
| WB101 | `mcp.__class__` swapped after construction | killed (3 red) |
| WB102 | `all_registered_tools()` served as the hosted list | killed (3 red) |
| WB107 | `tools/list` scoped, `tools/call` not (WB93 mirror) | killed (14 red) |
| WB108 | instance-attribute shadow on `read_resource` | killed (4 red) — **instrument 1's positive receipt** |
| WB112 | `_tool_manager` ← a `ToolManager` subclass overriding nothing | killed (27 red) — **but NOT by the pin the docstring names**, §4.10 |
| WB113 | the lowlevel `request_handlers` table rewritten unscoped | killed (3 red) |
| WB114 | 7 of 9 read tools refused with an off-marker message | killed (2 red) — **by the resolver seam, not by the posture ∀**, §6-I5 |
| WB30 / WB48 / WB93 | the three prior blockers | killed (19 / 13 / 7 red) |
| WB71 / WB72 / WB74 / WB50 / WB50b / WB51 / WB55 / WB61c | prior survivors | killed, §5 |
| WB31 | truncated sha512 cache key | ⚠ **SURVIVES** — unchanged residual, §10-R1 |

### 4.1 ⚑ WB100 — THE BLOCKER: the fourth door is the CLASS attribute

**The reasoning that finds it, and it is the pin's own failure message that points at the
door.** `TestNoInstanceAttributeShadowsABoundHandler` tells the builder, verbatim:

> *"The sanctioned spelling is a SUBCLASS override (wire-live by construction) or the scoped
> ToolManager."*

A builder who is told "not an instance attribute — use the class" and half-follows it reaches
for `FastMCP.list_tools = _scoped` rather than authoring a subclass. That is WB100. Its
mechanism is measured at source:

```
$ uv run python -c "import inspect; from mcp.server.fastmcp import FastMCP; print(inspect.getsource(FastMCP._setup_handlers))"
    def _setup_handlers(self) -> None:
        self._mcp_server.list_tools()(self.list_tools)
        self._mcp_server.call_tool(validate_input=False)(self.call_tool)
        ...
```

`self.list_tools` is a **bound method object captured at construction**; it holds `__func__`,
so rebinding the class attribute afterwards changes nothing on the wire — and never touches
`vars(mcp)`.

**FRESH-PROCESS WIRE PROOF, with the reference build as the control** (`wire_probe.py`, §12.3 —
it constructs **exactly one** composed server, which is the production shape; a pytest process
constructs dozens):

```
=== REFERENCE BUILD (control) ===
PROVENANCE loremaster.__file__ = /home/ejprice/adv39-4/ref/loremaster/loremaster/__init__.py
WIRE tools/list served 9 tools: ['lore_dead_code','lore_diff','lore_get_symbol','lore_impact',
                                 'lore_map','lore_read','lore_recall','lore_search','lore_verify']
WIRE leaked MUTATING tools: []
WIRE tools/call lore_remember refused=True

=== WB100 (wrong build) fresh process ===
PROVENANCE loremaster.__file__ = /home/ejprice/adv39-4/wbtree/loremaster/loremaster/__init__.py
WIRE tools/list served 15 tools: [... incl. lore_claim_task, lore_comms, lore_findings,
                                  lore_index, lore_remember, lore_tasks]
WIRE leaked MUTATING tools: ['lore_claim_task','lore_comms','lore_findings','lore_index',
                             'lore_remember','lore_tasks']
```

**Why the contract cannot see it — and this is the sharpest part.** In pytest the class patch is
installed by the FIRST `build_mcp_server` call in each worker process; from the SECOND
construction onward the patched class method IS what `_setup_handlers` binds, so the build is
**wire-LIVE for every server except the first**. Production constructs exactly one.
**THE FIXTURE GUARANTEES THE ONE CONDITION UNDER WHICH THE BUG IS INVISIBLE**, in the literal
words of this repo's own law.

Measured, **10 full-contract runs on WB100**:

```
# 5 runs, default (pytest-randomly ON), -n auto
2 failed, 471 passed  |  473 passed  |  1 failed, 472 passed  |  2 failed, 471 passed  |  473 passed
# 3 runs, -p no:randomly, -n auto
1 failed, 472 passed  |  473 passed  |  1 failed, 472 passed
# 2 earlier runs, -p no:randomly, -n auto, in two independent scratch trees
473 passed            |  473 passed
```

**5 of 10 runs are a clean 473/473.** When it does red, it is a SINGLE pin
(`test_a_hosted_principal_is_not_offered_refused_tools_on_the_wire`) — one red in 473 that
vanishes on re-run, which is the exact shape CLAUDE.md's *"a failing test is a STOP; 'flaky' is
not a builder's verdict"* law exists to stop, and the exact shape a builder talks past.

**The pair, both legs (P2 discipline):**

```
$ PIN=...::test_a_hosted_principal_is_not_offered_refused_tools_on_the_wire
=== CONTROL LEG: the isolated pin on the REFERENCE build ===   1 passed in 0.65s
=== WRONG LEG: the SAME isolated pin on WB100 ===              1 failed in 0.68s
=== the whole posture MODULE on WB100 ===                     49 passed in 3.06s
```

The pin discriminates **alone** and stops discriminating **the moment any earlier test in the
module constructs a server**. That is order-dependent green, not coverage.

### 4.2 ⚑ WB106 — REGRESSION: the guard keys on the client_id STRING again

`test_a_write_scope_is_what_permits_not_the_client_id_shape` existed at **`af74611`** and is
**absent at `c02d12a`** — deleted by the R16 restructure, with no successor (`grep -rn
"write_scope_is_what_permits" --include=*.py .` → **zero hits**). It was an **in-process** pin
using `as_principal` + `call_and_capture`, and R16 instrument 2 bans both helpers in the posture
module — so it was deleted rather than re-homed. **R16's own discipline caused the loss.**

Consequence, with control (`consequence.py forged`, §12.4):

```
--- REF control ---  forged client_id REFUSED by the posture guard    -> guard keys on the SCOPE
--- WB106 ---        FORGED client_id got PAST the posture guard -> ToolError raised BELOW it
                     (Error executing tool lore_remember: 1 validation error ...) -> keys on the STRING
```

The forged token carries `scopes=[lore:read]` only, and reaches `lore_remember`'s body. This is
pass-1's **WB25**, killed at 422, killed at 448, killed at 472, **alive at 473.**

> ⚠ There is no *wire* way to present an adversarial principal shape, because on the wire the
> verifier mints the `AccessToken`. **A whole class of assertions is expressible only in
> process, and R16 removed the place to put them.** That is a cost the restructure did not price.

### 4.3 ⚑ WB40 — REGRESSION: the served refused-set section is a hand-list again

Killed at pass 2 by `test_the_refused_set_section_is_DERIVED_from_the_annotations` — a
**mutation proof** (flip the shared `_READ_ONLY_ANNOTATIONS` constant; a derived section must
follow, a hand-list will not). That pin was deleted at `c02d12a`. Its supposed successor,
`test_the_refused_clause_names_EXACTLY_the_refused_set`, compares the clause against the derived
set **at today's annotation values**, which a hand-list satisfies exactly.

I rebuilt the deleted instrument (`section_mutation.py`, §12.6):

```
=== REF (control) ===  after flipping the SHARED read-only annotation, the served refused
                       clause names 15 of 15 tools
=== WB40 ===           after flipping the SHARED read-only annotation, the served refused
                       clause names  6 of 15 tools
```

**PROVE SHARING BY MUTATION** is standing law in this repo; the one pin in the contract that
performed it on a served natural-language surface was deleted.

### 4.4 ⚑ WB109 — deny-by-default became deny-everything-NEW

`test_a_newly_registered_read_only_tool_is_permitted` (present at `af74611`) was the CONTROL for
`..._is_born_refused`: a newly contributed tool that DOES declare `readOnlyHint=True` must be
callable. Deleted, no successor. WB109 classifies read-only by a hand-list of the nine core
names and passes 473/473.

```
--- REF control ---  a NEW read-only tool is CALLABLE by a hosted principal (correct)
--- WB109 ---        a NEW read-only tool is REFUSED -> deny-by-default became deny-everything-NEW
```

### 4.5 ⚑ WB111 — every unauthenticated local call refused, list unaffected

`test_no_token_at_all_is_not_refused` (parametrised over tools, LOOPBACK posture) is deleted.
Its only replacement, `test_the_loopback_posture_serves_the_full_surface_unauthenticated`, reads
the **LIST** route. WB111 keeps the list unfiltered and refuses at the **LOOKUP**.

```
--- REF control ---  unauthenticated call reached the tool body (ToolError below the guard) (correct)
--- WB111 ---        unauthenticated call REFUSED -> every local single-user session loses the write tools
```

That is a 100% break of today's shipping single-user deployment, green on all 473.

### 4.6 ⚑ WB110 — the hosted refusal section served in LAN_BEARER

`test_the_section_is_absent_in_lan_bearer_posture` is deleted; only the loopback leg survives.

```
--- REF control ---  LAN_BEARER instructions carry the HOSTED refusal section: False
--- WB110 ---        LAN_BEARER instructions carry the HOSTED refusal section: True
```

A trust-doctrine lie: an api-key principal on the LAN is TAUGHT that six tools it can call are
refused. It stops using them. Under the Consumer Law that is a served over-claim.

### 4.7 ⚑ WB103 — the posture guard governs 2 of the 7 handlers its own derivation names

`sdk_bound_handler_names()` returns **seven** routes at 1.27.2. The contract's posture
invariants cover **`tools/list` and `tools/call`**. `resources/list`, `resources/read`,
`prompts/list`, `prompts/get`, `list_resource_templates` are ungoverned — and lore registering
none today is a fact about today, not a property.

WB103 registers one mutating capability behind a resource and a prompt. All 473 green:

```
  resources/list     status=200 refused=False -> {"resources":[{"name":"_wipe","uri":"lore://admin/wipe",...
  resources/read     status=200 refused=False -> {"contents":[{"uri":"lore://admin/wipe","text":"wiped"}]}
  prompts/list       status=200 refused=False -> {"prompts":[{"name":"lore_admin_wipe",...
  prompts/get        status=200 refused=False -> {"description":"Perform the mutating action ...
```

A hosted read-only Google principal performed the mutating action. **This is the quantifier
attack landing on R16's own derived set**: the derivation is ∀ over seven routes; the invariant
is guarded to the two routes *with wrong-build receipts against them*. The honesty pin is even
named `test_the_derivation_sees_the_routes_that_have_receipts`.

### 4.8 ⚑ WB105 — the "unaffected by an ambient principal" pin never establishes one

`test_the_accessor_is_unaffected_by_an_ambient_hosted_principal` opens a `wire_session` and then
reads `wire.mcp._tool_manager.all_registered_tools()` **after** the request has completed — the
SDK sets and resets `auth_context_var` *inside* request handling, so there is no ambient
principal at the moment the assertion runs. A **failure message that promises a check the
assertion does not perform.**

```
--- REF control ---  all_registered_tools(): outside a principal=15  under a READ-ONLY principal=15
--- WB105 ---        all_registered_tools(): outside a principal=15  under a READ-ONLY principal= 9
```

WB105 passes 473/473. Consequence: every derivation built on the accessor silently NARROWS
under a hosted principal, so the ∀ pins go **vacuous rather than red** — which is the exact
failure the pin's own comment says it exists to prevent.

### 4.9 ⚑ WB104 — and the reference build itself: LOOPBACK's edge policy is unpinned, and the new wire pin FORCES a weakening

`_auth_fixtures.wire_session` hardcodes `Host: lore.firehawktransam.org` in **every** posture.
The new pin `test_the_loopback_posture_serves_the_full_surface_unauthenticated` therefore forces
the LOOPBACK build to accept that Host. **Today it does not:**

```
$ uv run python /home/ejprice/adv39-4/today_loopback.py      # repo tree, c02d12a, no packet-39 build
PROVENANCE /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
TODAY loopback transport_security = (True, ['127.0.0.1:*', '[::1]:*', 'localhost:*'])
```

FastMCP auto-enables DNS-rebinding protection whenever the bind host is loopback (source read,
`FastMCP.__init__`). Only two builds satisfy the new pin, and **both pass 473/473**:

```
=== A. my reference build (protection DISABLED for loopback) ===
loopback transport_security = (False, [])
  Host: 127.0.0.1:9202           -> 200
  Host: lore.firehawktransam.org -> 200
  Host: evil.attacker.example    -> 200          ⚠ today this is 421
=== B. WB104 (protection ON + the public hostname allowed) ===
loopback transport_security = (True, ['127.0.0.1:*','[::1]:*','localhost:*',
                                      'lore.firehawktransam.org','lore.firehawktransam.org:*'])
  Host: evil.attacker.example    -> 421
```

`TestLoopbackPostureIsUnchanged` guards against the loopback deploy **acquiring** a gate it never
had; nothing guards against it **losing** one it does have. A **P6b orphaned virtue of the SDK
default**, and the contract's own fixture is what pushes the builder over it.

### 4.10 The shadowing pin's three claimed bounds — VERIFIED INDIVIDUALLY

The docstring names three things it deliberately does not cover and asserts each is caught
elsewhere. The brief asked me to verify each; a bound asserted and false is worse than unstated.

| claimed bound | claim | verdict |
|---|---|---|
| *"a swapped `_tool_manager` (caught by the scoped-manager identity pin)"* | caught there | ⚠ **FALSE for the case that matters.** WB112 swaps in `class _InertToolManager(ToolManager): pass`. `isinstance` holds and `type(m) is not ToolManager` holds, so `test_the_composed_server_installs_a_SCOPED_tool_manager` **PASSES**: `uv run pytest <identity pin> <TestNoInstanceAttributeShadowsABoundHandler> → 6 passed`. The build is killed (27 red) **only by the wire pins**. The property survives; the attribution does not. |
| *"a rewritten low-level handler table (wire-visible, so the wire pins catch it)"* | caught there | ✅ **TRUE.** WB113 rewrites `request_handlers[ListToolsRequest]` to serve the unscoped registry → **killed (3 red)**, all three wire pins. |
| *"a subclass override (the sanctioned spelling, wire-live by construction)"* | wire-live | ✅ **TRUE at source.** `_setup_handlers` binds `self.<name>`, which resolves through the MRO at construction, so a subclass override is what gets registered. Confirmed by WB101's mirror image: a `__class__` swap **after** construction is wire-DEAD and is killed (3 red) by the wire pins. |

### 4.11 The handler derivation's own bounds — measured, not argued

The docstring claims a hand-list *"would miss the eighth handler an SDK upgrade binds"*, implying
the derivation would not. I ran the **production derivation** against eight plausible
`_setup_handlers` shapes by monkeypatching `inspect.getsource` (`derivation_shapes.py`, §12.5):

| SDK shape | result | the honesty pin (`{call_tool,list_tools} ⊆ set`) |
|---|---|---|
| today (control) | **FULL** 7 names | green (correct) |
| an eighth handler added, same shape | **FULL** 8 names, finds `elicit` | green — ✅ **the docstring's claim is TRUE** |
| handlers bound through a **loop** over names | **LOUD** — `assert names` fires | ✅ anti-vacuity works |
| tools inline, the **rest delegated to a helper** | ⚠ **SHORT** — 2 of 7; 5 handlers silently dropped | **stays GREEN** |
| the tool routes delegated, the rest inline | ⚠ SHORT — 5 of 7 | would RED |
| a handler renamed private but still bound | ⚠ SHORT — 1 of 7 | would RED |
| bound via a **local alias** (`lowlevel = self._mcp_server`) | ⚠ **SHORT** — 3 of 7 | **stays GREEN** |
| an unrelated `self.settings` in the body | FULL + 1 spurious (`settings`) | green — harmless (over-inclusion is safe here) |

**Two of eight shapes go silently SHORT while the honesty pin stays green**, dropping 4–5 routes
from every ∀ built on the derivation. The anti-vacuity control is `assert names` (non-empty), not
`assert names == what the SDK actually binds` — and there IS a way to assert the latter (§11-N1).

---

## 5. Prior-survivor re-run (brief requirement) — 10 rebuilt, 8 killed, 2 alive

| build | origin | what it does | verdict at `c02d12a` |
|---|---|---|---|
| **WB30** | pass-1 blocker | guard as a post-construction instance attribute | ✅ killed (19 red) |
| **WB48** | pass-2 blocker | guard runs AFTER the tool body | ✅ killed (13 red) |
| **WB93** | pass-3 blocker | `mcp.list_tools = _scoped` | ✅ killed (7 red) |
| **WB71** | pass-3 | `host_is_loopback` as a spelling set | ✅ killed (3 red — the 127/8 grid) |
| **WB72** | pass-3 | hosted list filters `is False`, not `is not True` | ✅ killed (1 red — the unannotated fixture) |
| **WB74** | pass-3 | extension annotation class optimistic | ✅ killed (1 red — the equality pin) |
| **WB50** | pass-2 | refused clause names every tool | ✅ killed (1 red) |
| **WB50b** | pass-2 | read-ladder clause empty | ✅ killed (1 red) |
| **WB51** | pass-2 | `host_is_loopback` fails OPEN on unparseable | ✅ killed (5 red) |
| **WB55** | pass-2 | `required_scopes=[]` for LAN_BEARER only | ✅ killed (1 red) |
| **WB61c** | pass-2 | both normalisation sites hand-rolled | ✅ killed (1 red) |
| **WB40** | pass-1 (killed at pass 2) | refused-set section is a hand-list | ⚑ **SURVIVES — REGRESSION**, §4.3 |
| **WB31** | passes 1–3 residual | truncated sha512 cache key | ⚠ **SURVIVES**, §10-R1 |
| WB29 / WB73 / WB88 / WB61 / WB61b | prior "survives, no consequence" | — | **NOT re-run this pass.** Prior passes adjudicated each as behaviourally equivalent or as the auditor's own probe fault; nothing in the R16 diff touches their seams. **Stated as inherited, not re-measured.** |
| WB33 / WB34 / WB28 / WB35 / WB41 / WB42 / WB42b / WB45 / WB54 | pass-1/2 survivors, killed at pass 2/3 | — | **NOT re-run.** Their killing pins live in `test_auth_composition.py` / `test_allowlist_roster.py` / `test_auth_identity_seam.py`; the R16 diff only DELETED from `test_hosted_readonly_posture.py` (composition grew 65→81, additive). I attacked the deletion set exhaustively instead (§8.2). **Stated as reasoned, not measured.** |

---

## 6. P1b — THE QUANTIFIER TABLE (every invariant; every guarded row with a receipt)

| # | invariant | ∀-over-inputs / guarded | receipt |
|---|---|---|---|
| **I1** | No mechanism governing the served surface is dead on the wire | ⚑ **GUARDED — by the SPELLING** (`name not in vars(mcp)`), not by the property *"the registered handler is still what `getattr(mcp,name)` resolves to"* | ⚑ **WB100 SURVIVES** (§4.1). The runtime staleness predicate fires on WB100 **and** WB101 **and** WB108; `vars(mcp)` fires only on WB108 (§11-N1 receipt). |
| **I2** | Every posture assertion is proven on the wire | ⚑ **GUARDED — by the module NAME** (`test_*posture*.py`; today it matches exactly ONE file) | ⚑ Perturbation pair §7.1: byte-identical in-process posture module GREEN as `test_auth_scoping.py`, RED as `test_scoping_posture.py`. |
| **I3** | The handler set the ∀s range over is the set the SDK binds | ⚑ **GUARDED — by the parse SHAPE** + the two routes with receipts | ⚑ §4.11: 2 of 8 plausible SDK shapes go SHORT *and* leave the honesty pin green. |
| **I4** | ∀ registered mutating tool × non-write principal → refused **on the wire** | **∀-over-the-registry** (derived from `all_registered_tools()`, non-empty asserted) | WB30/WB48/WB93/WB102/WB107/WB113 all killed. |
| **I5** | ∀ read tool × hosted principal → NOT refused | ⚑ **GUARDED — by the refusal MESSAGE's wording** (`refusal_marker() not in body`), not by the tool having RUN | WB114 (7 of 9 read tools refused with an off-marker message) → killed, **but by `test_permission_resolver_seam`, not by the posture ∀**. The posture module's own "not refused" ∀ is wording-guarded; it survives on someone else's pin. |
| **I6** | The posture guard keys on the WRITE SCOPE, not on the principal's shape | ⚑ **UNGUARDED — pin deleted at `c02d12a`** | ⚑ **WB106 SURVIVES** (§4.2). |
| **I7** | deny-by-default ≠ deny-everything-NEW | ⚑ **UNGUARDED — pin deleted** | ⚑ **WB109 SURVIVES** (§4.4). |
| **I8** | No token ⇒ the full surface at **CALL**, not only at LIST | ⚑ **GUARDED — to the LIST route** | ⚑ **WB111 SURVIVES** (§4.5). |
| **I9** | The hosted refusal section is absent in every non-hosted posture | ⚑ **GUARDED — to LOOPBACK** (the LAN_BEARER leg was deleted) | ⚑ **WB110 SURVIVES** (§4.6). |
| **I10** | The posture guard governs every security-relevant SDK route | ⚑ **GUARDED — to `tools/*`** (2 of the 7 derived handlers) | ⚑ **WB103 SURVIVES** (§4.7). |
| **I11** | `all_registered_tools()` is unscoped ∀ ambient principal | ⚑ **GUARDED — the pin reads it outside any request context** | ⚑ **WB105 SURVIVES** (§4.8). |
| **I12** | The LOOPBACK edge policy is no weaker than today's | ⚑ **UNPINNED entirely** | ⚑ **WB104 SURVIVES**, and my reference build had to weaken it to go green (§4.9). |
| **I13** | The served refused/read clauses are DERIVED from the annotations | ⚑ **GUARDED — by value-equality at today's annotations** (the mutation proof was deleted) | ⚑ **WB40 SURVIVES** (§4.3). |
| **I14** | The positive-cache key is the full digest | ⚑ **UNPINNED** (known, four passes) | ⚠ **WB31 SURVIVES** (§10-R1). |
| **I15** | ∀ (token, tokeninfo, allowlist) → `None` or a COMPLETE `AccessToken` | **∀-over-inputs** (`assert_verification_outcome_is_total` on every verification) | WB61c killed (1 red); mutating the `TokeninfoSpy` fake reds 9 pins (§10-P5). |
| **I16** | ∀ roster line → emitted / merged-and-reported / rejected-and-reported | **∀-over-inputs** (shared helper + anti-vacuity on the candidate set) | Reference build 473/0 exercises every fate; passes 1–3 receipts stand. Not separately attacked this pass. |
| **I17** | `host_is_loopback` is a PREDICATE over 127/8, fail-closed on the unknown | **∀-over-a-grid** (127.0.0.2 / 127.0.1.1 / 127.255.255.254 in; 126.255.255.255 / 128.0.0.1 out) | WB71 killed (3 red), WB51 killed (5 red). |

**6 ∀-over-inputs · 11 guarded · 9 guarded rows carry a SURVIVING wrong build.**

---

## 7. P2 — fixture perturbation, both legs, with correct-build controls

### 7.1 The wire-discipline gate is defeated by a FILE RENAME

`POSTURE_MODULE_GLOB = "test_*posture*.py"` matches exactly **one** file:

```
$ uv run python -c "from pathlib import Path; print(sorted(x.name for x in Path('loremaster/tests').glob('test_*posture*.py')))"
['test_hosted_readonly_posture.py']
```

`test_auth_composition.py` (81 pins — including R16 instrument 1 itself), `test_auth_identity_seam.py`
and `test_auth.py` are **not governed**. I wrote a new module carrying two in-process posture
assertions, one of them the *verbatim* shape the gate's own docstring forbids
(`await mcp.list_tools()`), and ran the gate against the same bytes under two names:

```
# as loremaster/tests/test_auth_scoping.py  (outside the glob)
$ uv run pytest loremaster/tests/test_wire_discipline.py -p no:randomly -q     → 6 passed in 0.34s
$ uv run pytest loremaster/tests/test_auth_scoping.py    -p no:randomly -q     → 2 passed in 0.74s

# same file, renamed loremaster/tests/test_scoping_posture.py  (inside the glob)
$ uv run pytest loremaster/tests/test_wire_discipline.py -p no:randomly -q     → 2 failed, 6 passed
    FAILED ...test_no_posture_assertion_calls_a_handler_in_process[test_scoping_posture.py]
    FAILED ...test_no_posture_module_imports_the_in_process_helpers[test_scoping_posture.py]
```

**Both legs proven.** The gate is receiver-blind (good) and **module-name-KEYED** (the class this
repo has six receipts against). The anti-vacuity pin only catches deleting/renaming the *existing*
module; a *new* module is invisible while the old one still matches. Answer to the brief's
question: **for `test_hosted_readonly_posture.py` the discipline is ENFORCED; everywhere else in
the contract it is a convention that happens to be obeyed today** (grep of the other three
modules for handler calls: only two prose mentions inside docstrings, no calls).

### 7.2 The WB93 pin discriminates only in isolation — §4.1's pair

Control leg (reference build, isolated) **1 passed**; wrong leg (WB100, isolated) **1 failed**;
same pin inside its own module on WB100 **49 passed**. The perturbation that blinds it is *any
earlier test in the process that constructs a server*.

### 7.3 Fixture values named by the contract's §9 item 5

`GOOGLE_ACCESS_TOKEN_LIFETIME_S`, `*_SUBJECT`, `GRANTED_SCOPE_STRING`, `PUBLIC_HOSTNAME` were
perturbed at passes 1–3 with pairs. **Not re-perturbed this pass** — the R16 diff does not touch
those seams. Stated as inherited. The R16-specific load-bearing fixtures I DID interrogate:
`POSTURE_MODULE_GLOB` (§7.1, **finding**), `refusal_marker()` (§6-I5, wording-guarded),
`wire_session`'s hardcoded `Host` (§4.9, **finding**), `wire_session`'s
`json_response = True` (§10-R4), `register_unannotated` (load-bearing — WB72 dies on it).

---

## 8. P6 / P6b

### 8.1 P6 — corpse sweep, bare anchor-free patterns, every hit with an individual verdict

Patterns run with **no prefix and no call-paren anchor** over `*.py *.toml *.yaml *.yml *.txt`,
excluding `REPORT-*`, `docs/plans/`, `receipts/`, `.venv/`:
`BearerAuthMiddleware` · `AuthVerifier` · `tls_terminated_upstream` · `_MUTATING_TOOLS` ·
`write_scope_is_what_permits` · `call_and_capture` · `as_principal`.

| hit | verdict |
|---|---|
| `loremaster/loremaster/auth.py` — docstring ×2, `__all__` ×2, `class AuthVerifier`, `class ApiKeyVerifier(AuthVerifier)`, `class BearerAuthMiddleware`, `__init__` docstring | **the code being deleted** — §8 rows 9/13/14. |
| `loremaster/loremaster/server.py` `:9825` docstring, `:9863`/`:9865` the wiring | **the code being deleted** — row 13. |
| `loremaster/loremaster/config.py` `:24`, `:348`, `:355` | **the field being deleted + its prose** — rows 7/12. |
| `loremaster/tests/test_eager_startup.py:599,610` | ⚑ **LIVE CORPSE, on the handoff list** (row 1). Reds on the reference build. |
| `loremaster/tests/test_mcp_server.py:3926,3928,3933,3944` | ⚑ **LIVE CORPSE, NOT on §8's list.** Reds on the reference build (2 pins). Adversary passes 1 and 3 flagged it; still absent from §8. |
| `loremaster/tests/test_config.py:350,360` | ⚑ **LIVE CORPSE, on the handoff list** (row 4 covers the field). Reds on the reference build. |
| `loremaster/tests/test_auth.py:4,13,65,66,68,111,547` | **NOT a corpse** — pins the names as RETIRED; RED today and correct. |
| `loremaster/tests/test_auth_composition.py:20,326,376` | **NOT a corpse** — prose explaining the retirement. |
| `loremaster/tests/test_mcp_server.py:1172,1185,1709` (`_MUTATING_TOOLS`) | ⚑ **LIVE CORPSE**, handoff row 2 says DELETE. **It does not red on the reference build** (subset check), so nothing forces the deletion. Unchanged from pass 3. |
| `loremaster/tests/test_hosted_readonly_posture.py:46,50,91,122,238,240,241,255,280,458` | **NOT a corpse** — `_MUTATING_TOOLS` in prose only; `EXPECTED_MUTATING_TOOLS` is the new anchor. |
| `loremaster/loremaster/calibration/corpus/comment_light_python.py.txt:200,207` | ⚠ **DO NOT EDIT** — frozen calibration corpus; editing perturbs the token baseline. Correctly named on the handoff table. |
| `write_scope_is_what_permits` | ⚑ **ZERO HITS** — the deletion §4.2 rests on, confirmed by grep. |
| `call_and_capture` / `as_principal` — `_auth_fixtures.py:935,947`, `test_wire_discipline.py:74`, `test_permission_resolver_seam.py` ×12 | **NOT corpses** — the sanctioned in-process helpers and their one legitimate consumer, exactly as R16 designs. |

### 8.2 P6b — the DELETED PINS, enumerated independently, then diffed

The R16 revision is a **delete/replace** of the posture module (70 → 49 pins), so P6b applies to
the deleted TESTS. I enumerated both name sets from `git show` and diffed **before** reading the
report's account of the restructure:

```
$ git show af74611:loremaster/tests/test_hosted_readonly_posture.py > /tmp/old_posture.py
$ comm -23 <old names> <new names>      # 24 deleted; 20 added
```

| deleted pin | successor | verdict |
|---|---|---|
| `test_a_google_principal_cannot_call_a_mutating_tool` | `…_on_the_wire` | **preserved (strengthened)** |
| `test_a_google_principal_is_NOT_refused_a_read_only_tool` | `…_read_tool_on_the_wire` | **preserved** |
| `test_a_hosted_principal_does_not_see_refused_tools_in_list_tools` | `…_is_not_offered_refused_tools_on_the_wire` | **preserved (strengthened)** |
| `test_an_api_key_principal_is_NOT_refused_a_mutating_tool` | `…_on_the_wire` | **preserved** |
| `test_an_api_key_principal_sees_the_full_surface` | `…_is_offered_the_full_surface_on_the_wire` | **preserved** |
| `test_an_extension_tool_is_annotated_non_read_only` | `…_carries_the_exact_worst_case_annotations` | **preserved (strengthened)** |
| `test_an_extension_tool_is_refused_for_a_hosted_principal` | `…_on_the_wire` | **preserved** |
| `test_an_extension_tool_remains_callable_via_an_api_key` | `…_on_the_wire` | **preserved** |
| `test_a_tool_registered_with_no_annotations_is_born_refused` | `test_an_unannotated_tool_is_born_refused_on_the_wire` | **preserved** |
| `test_a_permitted_read_tool_body_IS_entered_for_a_hosted_principal` | `test_the_recorder_CAN_see_a_body_execute` | **preserved (renamed)** |
| `test_no_refused_tool_body_is_ever_entered_for_a_hosted_principal` | `…_on_the_wire` | **preserved** |
| `test_the_same_synthetic_tool_is_refused_WITHOUT_running_when_hosted` | `test_a_no_argument_mutating_tool_is_refused_without_running` | **preserved** |
| `test_the_read_surface_is_exactly_the_named_read_only_tools` | `test_the_derived_readable_set_equals_the_named_read_tools` | **preserved** |
| `test_the_refusal_is_a_structured_tool_error_not_an_unhandled_exception` | `test_the_refusal_is_a_structured_tool_error` | **preserved** |
| `test_the_refusal_names_the_posture_from_the_enum` | `test_the_refusal_names_the_posture_and_the_tool` | **preserved (widened)** |
| `test_every_refused_tool_is_named_inside_that_section` | `test_the_refused_clause_names_EXACTLY_the_refused_set` | **preserved (widened to equality)** |
| `test_the_instructions_still_name_every_registered_tool_in_hosted_posture` | `test_the_instructions_still_name_every_registered_tool` | **preserved** |
| `test_an_unauthenticated_lookup_is_unfiltered` (HOSTED posture) | `test_the_loopback_posture_serves_the_full_surface_unauthenticated` (LOOPBACK) | **preserved by a different instrument — reach NARROWED** from hosted-with-no-principal to loopback. A build differing between the two is covered by `test_mcp_server`'s registration pins. **Adjudicated: acceptable, stated.** |
| `test_the_registered_surface_is_the_same_in_every_posture` | `test_the_scoped_manager_exposes_all_registered_tools` + the loopback wire pin | **legitimately retired** (under R13 the SERVED surface differs by design) — but note the surviving pin is HOSTED-only, and WB105 shows it reads outside a principal. **Adjudicated: covered, with I11's caveat.** |
| ⚑ `test_a_write_scope_is_what_permits_not_the_client_id_shape` | **NONE** | ⚑ **ORPHANED — WB106 (§4.2)** |
| ⚑ `test_a_newly_registered_read_only_tool_is_permitted` | **NONE** | ⚑ **ORPHANED — WB109 (§4.4)** |
| ⚑ `test_no_token_at_all_is_not_refused` | LIST route only | ⚑ **ORPHANED — WB111 (§4.5)** |
| ⚑ `test_the_section_is_absent_in_lan_bearer_posture` | LOOPBACK leg only | ⚑ **ORPHANED — WB110 (§4.6)** |
| ⚑ `test_the_refused_set_section_is_DERIVED_from_the_annotations` | value-equality only | ⚑ **ORPHANED — WB40 (§4.3)** |

**Five orphaned virtues, each with a surviving wrong build.** The contract report's §18 claim —
*"the 49 wire pins cover what the 70 in-process ones did and the three routes that defeated
them"* — is **measurably false**: five of the 24 deletions have no successor, and each is worth a
BLOCKER-adjacent defect.

### 8.3 The §8 handoff list, re-verified by the frame-independent instrument

```
$ cd /home/ejprice/adv39-4/ref && uv run pytest loremaster/tests lorerunes/tests \
      loresigil/tests lorescribe/tests -n auto -q --tb=no -rf
5 failed, 8167 passed, 36 skipped, 3 xfailed, 1 warning in 261.28s (0:04:21)
```

| collateral red on the correct build | on §8's handoff table? |
|---|---|
| `test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true` | ✔ row 4 covers the field |
| `test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost` | ✔ row 1 |
| `test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated` | ✔ row 2's file, but this pin is **not named**; a builder reading §8 would not know to rewrite it |
| `test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware` | same |
| **`test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam`** | ⚑ **STILL MISSED — fourth pass, and it was pass-3's N5.** `grep -rn "secret_typing" REPORT-contract-39-auth-1.md docs/design/2026-07-31-packet39-google-oauth.md` → **zero hits.** A finding raised by an adversary and never landed in the contract. |

---

## 9. P4 / P7 — the author's claims, reproduced rather than relayed

**Baseline reproduced at `c02d12a`, repo tree:**

```
$ uv run pytest $CONTRACT --collect-only -q | tail -1     → 473 tests collected in 0.44s
$ uv run pytest $CONTRACT -n auto -q --tb=no | tail -1    → 432 failed, 41 passed in 6.64s
```

**The 467/435 vs 473/441 discrepancy is a SCOPE difference, not an error.** The lead's commit
message says `467 collected / 432 RED / 35 GREEN`; `REPORT-contract-39-auth-1.md` §18 says
`473 / 432 / 41`. 473 − 467 = 6 = `test_wire_discipline.py`'s pin count; 41 − 35 = 6, same six.
**Both numbers are right about different file sets.** This is CLAUDE.md's own *"I verified it is a
claim about a SCOPE"* law, live: the lead's `CONTRACT` variable omitted the new module. Neither
document says which scope it used. **Residual R2.**

**The 41 GREEN enumerated individually** (`-rp`, full list captured): 12 ×
`TestApiKeyVerifierIsPreservedVerbatim` · 7 × `TestOriginValidationMiddlewareIsPreserved` · 3 ×
`TestBuildApiKeyVerifierFromConfig` · 3 × `TestRetiredAuthSurfaceIsGone::test_the_kept_names_are_still_exported` ·
2 × `TestLoopbackPostureIsUnchanged` · 2 × `TestLoreConfigCrossChecksTheResourcePath` · 1 ×
`test_a_config_without_the_retired_flag_loads` · 1 × `test_an_unauthenticated_initialize_succeeds` ·
1 × `test_the_homograph_fixture_is_actually_a_homograph` · 1 × `lorerunes/tests/test_smoke.py` ·
**6 × `test_wire_discipline`** · **2 × `TestNoInstanceAttributeShadowsABoundHandler`**
(`test_no_shadowing_in_any_posture[loopback]`, `test_the_derivation_sees_the_routes_that_have_receipts`).
**Reconciles to 41 exactly.**

**The brief's check on the two new GREENs — confirmed, with one correction:**

- `test_no_shadowing_in_any_posture[loopback]` **is** a negative invariant, green on the null
  build, and **it CAN red**: WB108 (an instance-attribute shadow of `read_resource`) reds it and
  its three siblings. ✅ characterisation confirmed. ⚠ **But its reach is `vars()` only** —
  WB100 and WB101 both walk past it, and only the wire pins carry the positive weight (which
  WB100 defeats half the time). So *"green today, load-bearing after the build"* is true; *"the
  class is killed"* is not.
- `test_the_derivation_sees_the_routes_that_have_receipts` is a pure SDK check with no production
  dependency, green forever unless the SDK moves. **It CAN red**: two of the eight shapes in
  §4.11 would red it. ✅ characterisation confirmed. Its bound is that it names exactly the two
  routes with receipts, which is why §4.11's other two SHORT shapes stay green.

**RED honesty:** 432 reds inspected in bulk by failure class — the overwhelming majority are
`ImportError`/`AttributeError` on symbols the builder has yet to write (the right reason). The
reference build turns **all 432 green**, which is the strongest available proof that none of them
was red for an import typo, a bad path, or a fixture error.

---

## 10. Residuals — every one with an INDIVIDUAL verdict

- **R1 — `WB31`, the truncated positive-cache key. FOUR passes unadjudicated.** Design §4 rules
  *"SHA-512 of the token as the only cache key"*; `[:8]` gives a 32-bit key, so a token colliding
  with a previously-**ADMITTED** one is served that principal's verdict. Survives 473/473. No
  cheap behavioural pin exists (a collision needs a preimage). **Honest options unchanged:** a
  structural pin that the key expression is a full `hexdigest()`, or accept-and-ledger with a
  named re-open trigger. ⚑ **This is now the fourth consecutive pass raising it. It needs an
  operator ruling, not a fifth adversary.**
- **R2 — the 467/473 count split.** Two documents, two scopes, neither stating which. Verdict:
  **fix by naming the scope**, not by changing a number. §9.
- **R3 — `test_secret_typing.py::…::test_no_auth_header_is_built_outside_a_seam` still off every
  handoff list.** Reds on the correct build; found at pass 3, absent from the contract at pass 4.
  Verdict: **add to §8 with an exact edit.** §8.3.
- **R4 — the "wire" the contract pins is the JSON-response wire; production's is SSE.**
  `wire_session` sets `mcp.settings.json_response = True`; `grep -rn json_response
  loremaster/loremaster/ lore.yaml* skills/lore-deploy` → **zero hits**, so production runs the
  SDK default (`False` ⇒ `text/event-stream`). Verdict: **LOW severity, real bound** — the
  posture content is encoding-independent, but no pin ever drives the encoding production uses.
  Adopting the SDK's `ClientSession` (§2) removes this for free.
- **R5 — `_MUTATING_TOOLS` in `test_mcp_server.py` still does not red on a correct build.**
  Handoff row 2 says delete it; nothing forces the deletion. Verdict: **carry as a manual
  close-out item**, unchanged from pass 3.
- **R6 — the shadowing pin's bound-A attribution is FALSE.** *"a swapped `_tool_manager` (caught
  by the scoped-manager identity pin)"* — WB112 passes that pin. Verdict: **fix the docstring**
  (the property IS guarded, by the wire pins); an asserted-and-false bound is worse than an
  unstated one.
- **R7 — `_install_hosted_instructions` in my reference build still reaches past the override**
  (`ToolManager.list_tools(mcp._tool_manager)`) even though `all_registered_tools()` now exists.
  Nothing in the contract requires the render to consume the sanctioned accessor. Verdict:
  **not a contract defect on its own** (the served output is identical), but it means R16
  instrument 3's stated purpose — *removing the friction* — is **not pinned at the one call site
  the friction was diagnosed at.** Worth one line in the builder's brief.
- **R8 — P5, can the doubles FAIL?** `TokeninfoSpy` mutated (`call_count` → `1 if self.requests
  else 0`) → **9 pins red** (`TestNegativeCacheSplitsDefinitiveFromTransient` ×7,
  `test_two_different_tokens_do_not_share_a_cache_entry`, `…[connect-error]`); tail `9 failed,
  464 passed in 8.13s`; fixture restored byte-exact (md5 `7fd2498e…` matches the repo).
  `wire_session`/`WireSession` **proven able to fail** (WB93 → 7 red, WB30 → 19 red through it).
  `sdk_bound_handler_names`'s anti-vacuity assert **proven able to fire** (§4.11 "LOUD" row).
  `_run_entry_recorder` carries its own in-suite positive control. `register_unannotated`
  **proven load-bearing** (WB72 dies on it and on nothing else). ✅ **All five doubles can fail.**
- **R9 — P0, my own probes' controls.** (a) Every survivor above has a **reference-build control
  leg** printed beside it; a probe that printed the same line on both builds would be worthless
  and I would have said so. (b) `wire_probe.py` was run on the correct build FIRST (9 tools,
  refused=True) before any wrong build. (c) The `--restore` path is verified by md5:
  `50b9bfb377de7510cc5b6164670513ee` for `server.py` after every batch. (d) My WB104's first
  formulation used `allowed_hosts=["*"]` and "died" — **for the wrong reason**: the SDK's
  `_validate_host` does exact-match/`base + ":"` wildcards and treats `"*"` as a literal, so the
  build 421'd everything. Self-caught; re-formulated with the real hostnames, whereupon it
  survives. A probe that fails for a mechanical reason is not a killed wrong build.
  (e) `derivation_shapes.py` includes a **control row** (today's real source ⇒ FULL) so a parse
  that returned nothing on every input could not read as a finding.
- **R10 — unrelated failures.** The reference-build full-suite run was **5 failed / 8167 passed /
  36 skipped / 3 xfailed**; all five failures are the packet-39 handoff corpses in §8.3. I saw no
  failure unrelated to packet 39.

---

## 11. THE MISSING PINS — each as *the test that should exist* + *the defect it catches*

**N1 — `test_every_registered_handler_is_still_the_one_the_object_resolves` (BLOCKER; replaces
or augments the `vars(mcp)` predicate).**
*The test:* for every entry in `mcp._mcp_server.request_handlers`, walk the closure to the bound
method it captured, and assert `registered.__func__ is getattr(mcp, registered.__name__).__func__`.
∀ posture. *The defect it catches:* **WB100** (class rebinding), **WB101** (`__class__` swap) and
**WB108** (instance attribute) — one predicate, all three, and it is a PROPERTY (*"what was
registered is what is live"*) rather than a spelling. It also closes §4.11: derive the handler set
from the same walk and cross-check it against the AST parse, so a delegated/aliased
`_setup_handlers` reds instead of going quietly SHORT. **Runnable code and its receipt are in
§12.2** — measured firing on WB100/WB101/WB108 and silent on the reference build.

**N2 — `test_a_write_scope_is_what_permits_not_the_client_id_shape`, RE-HOMED (BLOCKER).**
*The test:* the deleted pin, moved to a module the wire-discipline glob does not govern (or
driven on the wire via a `wire_session(token_factory=…)` that mints the forged shape).
*The defect:* **WB106** — a guard keyed on `client_id.startswith("api_key:")`. §4.2.

**N3 — `test_the_refused_set_section_is_DERIVED_from_the_annotations`, RE-HOMED (HIGH).**
*The test:* the deleted mutation proof — monkeypatch the shared `_READ_ONLY_ANNOTATIONS`, rebuild,
assert the served clause follows. *The defect:* **WB40** — a hand-listed served surface that
teaches a stale refused set. §4.3. (Structural pin; no wire needed, so instrument 2 does not
forbid it.)

**N4 — `test_a_newly_registered_read_only_tool_is_callable_on_the_wire` (HIGH).**
*The test:* `wire_session(..., prepare=register_read_only_probe)`, then `wire.call` it and assert
`refusal_marker() not in body`. *The defect:* **WB109** — deny-by-default becoming
deny-everything-NEW. §4.4.

**N5 — `test_an_unauthenticated_session_can_CALL_a_mutating_tool` (HIGH).**
*The test:* `wire_session(posture="loopback", principal=None)` + `wire.call("lore_remember")`,
assert not refused. Today the loopback wire session only ever LISTS. *The defect:* **WB111** —
the shipping single-user deploy losing two thirds of its tools at call time. §4.5.

**N6 — `test_the_section_is_absent_in_lan_bearer_posture` restored (MODERATE).**
*The defect:* **WB110** — an api-key LAN principal taught that tools it can call are refused
(trust-doctrine over-claim). §4.6.

**N7 — `test_the_unscoped_accessor_is_unscoped_UNDER_AN_AMBIENT_PRINCIPAL` (HIGH).**
*The test:* read `all_registered_tools()` **inside** an `as_principal(read_only_token)` block (or
from inside a tool body during a wire call). Today's pin reads it after the request has ended.
*The defect:* **WB105** — a scoped accessor makes every ∀ built on it vacuous rather than red. §4.8.

**N8 — `test_the_posture_guard_governs_every_bound_handler_or_the_registry_is_empty` (HIGH).**
*The test:* ∀ handler in `sdk_bound_handler_names()` minus the two tool routes, assert the
corresponding registry is EMPTY in every posture — with the message *"the posture guard governs
the tool manager only; a resource or prompt is a second, ungoverned surface"* — **or** drive
`resources/list`/`resources/read`/`prompts/list`/`prompts/get` on the wire for a hosted principal
and assert refusal. *The defect:* **WB103** — a mutating capability reached through
`resources/read` with status 200. §4.7.

**N9 — `test_the_loopback_posture_still_refuses_a_foreign_Host` (HIGH) + a fixture fix.**
*The test:* a loopback build must answer **421** to `Host: evil.attacker.example`. And
`wire_session` must present a posture-appropriate `Host` (loopback ⇒ `127.0.0.1:9202`) instead of
hardcoding the public hostname, so the contract stops *forcing* the weakening. *The defect:*
**WB104**, and the reference build's own concession. §4.9.

**N10 — the wire-discipline gate's module set must be DERIVED FROM A PROPERTY, not a filename
glob (HIGH).** *The test:* govern **every** module in the auth-contract set (or, better: every
test module that imports `_auth_fixtures`, or that constructs `build_mcp_server` and asserts on
refusal), and keep the receiver-blind call check. *The defect:* a posture claim proven in process
in `test_auth_composition.py` or a new module — proven invisible today by the rename pair. §7.1.

**N11 — the "was NOT refused" ∀ must observe the tool RUNNING, not the message's wording
(MODERATE).** *The test:* extend the `Tool.run` recorder to the SERVED set —
`entered == sorted(served)` after calling every served tool — rather than asserting the marker's
absence. *The defect:* **WB114**'s shape; today it survives the posture module and dies only in
`test_permission_resolver_seam`. §6-I5.

---

## 12. The instruments (brief-base §1 — pasted, because I may not commit them)

All probes lived at `/home/ejprice/adv39-4/` and in two `scratch_copy.sh` trees
(`/home/ejprice/adv39-4/ref`, `/home/ejprice/adv39-4/wbtree`). **The repo working tree was never
modified** (`git status --short` empty at start and end; `_auth_fixtures.py` md5 `7fd2498e…`
unchanged). Scratch is disposable by design, so the load-bearing instruments are pasted here.

### 12.1 The wrong-build harness (mechanism)

```python
ROOT = Path(os.environ.get("ADV39_TREE", "/home/ejprice/adv39-4/wbtree"))
REFBUILD = Path("/home/ejprice/adv39-4/refbuild")
EXPECTED_COLLECTED = 473

def restore() -> None:
    """Put every production file back to the reference build, byte-exact."""
    for path in FILES.values():
        shutil.copy(REFBUILD / path.replace("/", "_"), ROOT / path)

def patch(file_key: str, old: str, new: str) -> None:
    """Replace `old` with `new`; the anchor MUST match exactly once."""
    target = ROOT / FILES[file_key]
    source = target.read_text()
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"ANCHOR MISMATCH in {file_key}: matched {count} times, need 1")
    target.write_text(source.replace(old, new))

# run_contract() collects FIRST and compares the total to EXPECTED_COLLECTED, so a
# mutation that breaks collection cannot be reported as a survivor.
```

### 12.2 ⚑ N1's predicate — the RUNTIME handler-staleness check, with its receipts

```python
def registered_handler_targets(mcp) -> dict[str, list]:
    """request_type_name -> the bound methods the registered handler actually calls."""
    targets = {}
    for request_type, handler in mcp._mcp_server.request_handlers.items():
        seen, stack, found = set(), [handler], []
        while stack:
            candidate = stack.pop()
            if id(candidate) in seen:
                continue
            seen.add(id(candidate))
            for cell in getattr(candidate, "__closure__", None) or ():
                try:
                    value = cell.cell_contents
                except ValueError:
                    continue
                if callable(value):
                    (found if hasattr(value, "__self__") else stack).append(value)
        targets[request_type.__name__] = found
    return targets

# THE PIN:
for request_name, bound_list in registered_handler_targets(mcp).items():
    for bound in bound_list:
        if getattr(bound, "__self__", None) is not mcp:
            continue
        live = getattr(mcp, bound.__name__, None)
        assert bound.__func__ is getattr(live, "__func__", live), (
            f"{request_name}: the handler registered at construction is NOT what "
            f"{bound.__name__!r} resolves to now — it is live in process and DEAD ON "
            f"THE WIRE (WB30/WB48/WB93/WB100 class)."
        )
```

Measured (`handler_derivation_probe.py`, one composed hosted server per process):

```
=== REF (control) ===
AST derivation (7):     ['call_tool','get_prompt','list_prompts','list_resource_templates',
                         'list_resources','list_tools','read_resource']
RUNTIME derivation (7): (identical)
total request_handlers registered on the lowlevel server: 8      # the 8th is PingRequest
in RUNTIME but not in the AST parse: []   in the AST parse but not bound at runtime: []
vars(mcp) ∩ handler names: []
STALE: none
=== WB100 ===  vars(mcp) ∩ handler names: []
   STALE: ['ListToolsRequest: registered=<function FastMCP.list_tools> live=<function _scoped_list_tools>']
=== WB101 ===  vars(mcp) ∩ handler names: []
   STALE: ['ListToolsRequest: registered=<function FastMCP.list_tools> live=<function _ScopedListingFastMCP.list_tools>']
=== WB108 ===  vars(mcp) ∩ handler names: ['read_resource']
   STALE: ['ReadResourceRequest: registered=<function FastMCP.read_resource> live=<function _guarded>']
```

**`vars(mcp)` sees 1 of 3. The staleness predicate sees 3 of 3, and it is derived, not a name-list.**

### 12.3 The fresh-process wire probe (`wire_probe.py`) — abridged to its load-bearing half

```python
mcp = build_mcp_server(LoreServer(config), http_client=spy.client())   # EXACTLY ONE server
mcp.settings.json_response = True
fx.stub_heavy_startup(mcp)
app = build_asgi_app(mcp, config)
async with fx.running_asgi_app(app):
    headers = [(b"host", fx.PUBLIC_HOSTNAME.encode()), *fx.MCP_POST_HEADERS, fx.bearer(token)]
    opened = await fx.drive(app, method="POST", path=fx.MCP_PATH, headers=headers,
                            body=fx.json_rpc_initialize())
    session_headers = [*headers, (b"mcp-session-id", fx.mcp_session_id(opened).encode())]
    await fx.drive(app, ..., body=b'{"jsonrpc":"2.0","method":"notifications/initialized"}')
    listed = await fx.drive(app, ..., body=b'{"jsonrpc":"2.0","id":7,"method":"tools/list"}')
    names = sorted(t["name"] for t in json.loads(listed.body)["result"]["tools"])
    print(f"WIRE tools/list served {len(names)} tools: {names}")
```
Run as `uv run python wire_probe.py` from inside the scratch tree, with
`LORE_KEY_LOCAL_AGENT` / `LORE_KEY_LAN_CLIENT` exported. Prints `loremaster.__file__` first.

### 12.4 The surviving builds, as patches against the reference build

```python
# WB100 — the BLOCKER. list_tools() on the scoped manager becomes a pass-through, and the
# filter is installed by rebinding the SDK METHOD ON THE CLASS, after construction.
def _install_scoped_list_tools_on_the_class() -> None:
    from mcp.server.fastmcp import FastMCP as _FastMCP
    if getattr(_FastMCP, "_lore_scoped_installed", False):
        return
    _original = _FastMCP.list_tools
    async def _scoped_list_tools(self):
        tools = await _original(self)
        manager = self._tool_manager
        if getattr(manager, "_write_scoped", None) is None or manager._write_scoped():
            return tools
        readable = {t.name for t in manager.all_registered_tools()
                    if getattr(t, "annotations", None) is not None
                    and t.annotations.readOnlyHint is True}
        return [t for t in tools if t.name in readable]
    _FastMCP.list_tools = _scoped_list_tools
    _FastMCP._lore_scoped_installed = True
# ...called from build_mcp_server immediately after the TracingFastMCP(...) construction.

# WB106 — the guard short-circuits on the client_id STRING (the deleted pin's exact target).
        token = get_access_token()
        if token is None:
            return True
+       if getattr(token, "client_id", "").startswith("api_key:"):
+           return True
        return SCOPE_WRITE in token.scopes

# WB40 — the served refused-set section is a hand-list.
-   refused = _mutating_tool_names(mcp)
+   refused = ["lore_remember", "lore_index", "lore_findings", "lore_comms",
+              "lore_claim_task", "lore_tasks"]

# WB109 — read-only classification is a hand-list of the nine core names.
    @staticmethod
    def _is_read_only(tool):
        annotations = getattr(tool, "annotations", None)
        if annotations is None or annotations.readOnlyHint is not True:
            return False
+       return tool.name in _PostureScopedToolManager._CORE_READ_TOOLS

# WB111 — refuse at the LOOKUP when unauthenticated; leave the LIST unfiltered.
    def get_tool(self, name):
        tool = super().get_tool(name)
+       unauthenticated = get_access_token() is None
-       if tool is None or self._write_scoped() or self._is_read_only(tool):
+       if tool is None or (self._write_scoped() and not unauthenticated) or self._is_read_only(tool):
            return tool

# WB110 — install the hosted refusal section in every non-loopback posture.
-   if posture is not Posture.HOSTED_OAUTH:
+   if posture is Posture.LOOPBACK:
        return

# WB105 — the sanctioned unscoped accessor is itself scoped.
    def all_registered_tools(self):
-       return ToolManager.list_tools(self)
+       return self.list_tools()

# WB104 — LOOPBACK keeps rebinding protection but allows the public hostname.
    return posture, None, None, TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*",
                       "lore.firehawktransam.org", "lore.firehawktransam.org:*"],
        allowed_origins=["*"])

# WB103 — a second, unscoped surface behind the resources and prompts routes.
def _register_side_channel(mcp):
    @mcp.resource("lore://admin/wipe")
    def _wipe() -> str:
        """Perform the mutating action through the resources route."""
        return "wiped"
    @mcp.prompt(name="lore_admin_wipe")
    def _wipe_prompt() -> str:
        """Perform the mutating action through the prompts route."""
        return "wiped"
```

### 12.5 `derivation_shapes.py` — grading the parse against SDK shapes (mechanism)

```python
original = inspect.getsource
for label, source in SHAPES.items():          # SHAPES: 8 plausible _setup_handlers bodies
    inspect.getsource = lambda _o, _s=source: textwrap.dedent(_s)
    try:
        names = sdk_bound_handler_names()     # the PRODUCTION derivation, unmodified
        missing = sorted(TODAY_SET - names)
        print(("FULL " if not missing else "SHORT"), label, sorted(names),
              "receipts pin", "would RED" if not {"call_tool","list_tools"} <= names else "stays GREEN")
    except AssertionError as exception:
        print("LOUD ", label, str(exception)[:80])
    finally:
        inspect.getsource = original
```
(The eight bodies and the full output table are §4.11.)

### 12.6 `section_mutation.py` — the deleted derivation mutation proof, rebuilt

```python
server_module._READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, idempotentHint=True, openWorldHint=False)      # flip the SHARED thing
mcp = build_mcp_server(LoreServer(config))
section = (mcp.instructions or "").split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
clause = section.split(HOSTED_READ_LADDER_MARKER, 1)[0]
registered = {t.name for t in mcp._tool_manager.all_registered_tools()}
named = sorted(n for n in registered if n in clause)
print(f"the served refused clause names {len(named)} of {len(registered)} tools")
# REF: 15 of 15   |   WB40: 6 of 15
```

### 12.7 The consequence probes (`consequence.py`) — one function per survivor

`forged` (WB106) · `accessor` (WB105) · `side` (WB103) · `newtool` (WB109) ·
`lanbearer` (WB110) · `unauth` (WB111). Each prints one line and is run on the reference build
FIRST as its control; the paired outputs are quoted in §4.2–4.8. Mechanism: build a hosted
server, install an `AccessToken` via `_auth_fixtures.as_principal`, and either dispatch in
process or drive the assembled app — full sources were ~200 lines; the load-bearing bodies are
quoted inline in §4.

### 12.8 `loopback_host_probe.py` / `today_loopback.py`

```python
mcp = build_mcp_server(LoreServer(loopback_config))
settings = mcp.settings.transport_security
print((settings.enable_dns_rebinding_protection, sorted(settings.allowed_hosts)))
async with fx.running_asgi_app(build_asgi_app(mcp, config)):
    for host in (b"127.0.0.1:9202", b"lore.firehawktransam.org", b"evil.attacker.example"):
        r = await fx.drive(app, method="POST", path=fx.MCP_PATH,
                           headers=[(b"host", host), *fx.MCP_POST_HEADERS],
                           body=fx.json_rpc_initialize())
        print(f"  Host: {host.decode():28s} -> {r.status}")
```
Outputs for the three builds are §4.9.

---

## 13. What I did NOT find — so the SUFFICIENT half of this grade is legible

This contract is strong in places, and the places matter:

- **Every prior blocker stays dead.** WB30, WB48 and WB93 — three waves of the same root cause —
  are killed by 19, 13 and 7 pins respectively. The wire restructure genuinely closed those doors.
- **The R15 loopback predicate is real.** WB71 (spelling set) and WB51 (fail-open on unparseable)
  both die, on the 127/8 grid and the unknown-host grid respectively — a predicate, not a list.
- **The equality pins work.** WB50, WB50b and WB74 each die on exactly one pin, and each of those
  pins is an EQUALITY against a derivation rather than a membership check.
- **The unannotated fixture is load-bearing**: WB72 dies on it and on nothing else.
- **The `Tool.run` effect recorder has a real positive control** and WB48 cannot hide behind a
  byte-identical refusal message.
- **The satisfiability receipt is clean, twice** (pre- and post-ruff), which is not free — a
  contract this large going 473/0 against an independently-assembled build is a good sign about
  its internal consistency.
- **`test_wire_discipline` is inside `testpaths`** (`pyproject.toml` names `loremaster/tests`), so
  it is a guard that actually runs — and it carries both a positive and a negative control, which
  is more than most instruments in this repo did before it.

I could not break the roster-parsing input accounting, the tokeninfo ∀ helper, the identity seam,
the `EdgePolicy` derivation for the two gated postures, the boot-refusal reach, or the
instructions-honesty equality pins — and I tried, with 21 builds and five probes.

---

## VERDICT

# CONTRACT INSUFFICIENT

Not because the contract is weak — it is the strongest of the four revisions — but because
**R16 did not kill the class it was written to kill, and the restructure that was supposed to
kill it deleted five pins whose absence I can each demonstrate with a surviving wrong build.**

The single most important sentence in this report: **`vars(mcp)` is a SPELLING; *"the handler
registered at construction is still the one the object resolves to"* is the PROPERTY.** Pinning
the spelling produced a fourth door in four waves. Pinning the property closes WB100, WB101 and
WB108 with one assertion, and — extended to a set cross-check — closes the derivation's silent
SHORT modes too (§11-N1, §12.2). **That one pin is worth more than the other ten combined.**

Eleven missing pins, §11. Nine of them are a re-home or a widening of something the contract
already contains.
