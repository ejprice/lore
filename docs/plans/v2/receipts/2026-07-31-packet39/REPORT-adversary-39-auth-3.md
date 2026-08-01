# REPORT-adversary-39-auth-3 — third adversary pass on the packet-39 Google-OAuth contract

`brief-base v9 read`

*All measurements in this report were taken 2026-07-31 against lore contract commit
`af74611` (`feat/surreal-unification`), MCP SDK **1.27.2**, Python 3.14.6. Every
"passes"/"reds" claim below is dated to that sha; nothing here is a present-tense claim
about a later tree.*

---

## SUMMARY BLOCK

- **state:** done-with-deviations · **VERDICT: CONTRACT INSUFFICIENT**
- **P1 HEADLINE — one wrong build SURVIVED 472/472 and it is a BLOCKER.** `WB93` moves
  WB30's exact shape onto the `tools/list` route that **R13 just made load-bearing**:
  the scoped `ToolManager` stops filtering, and the filter is installed instead as a
  post-construction instance attribute `mcp.list_tools = _scoped_list_tools`. Every
  `list_tools` pin drives `mcp.list_tools()` **in process** and goes green; on the
  **wire**, `_setup_handlers` holds the BOUND original, and a hosted Google principal's
  real `tools/list` returns **15 tools incl. all six mutating ones** (control leg on the
  correct build: 9 tools, zero leaked). §4.1.
- Three further survivors, each with a proven perturbation pair: **WB71** (`host_is_loopback`
  as a spelling set — `127.0.0.2`/`127.0.1.1` refuse to boot), **WB72** (the hosted
  `list_tools` advertises an UNANNOTATED tool it will refuse), **WB74** (extension
  annotation CLASS unpinned — spec-silent).
- **Packages considered:** `mcp` SDK 1.27.2 — read `fastmcp/tools/tool_manager.py` (whole
  file: `call_tool` = `tool = self.get_tool(name); … await tool.run(...)`), `fastmcp/server.py`
  `_setup_handlers`/`list_tools`/`call_tool`/`instructions`, `lowlevel/server.py`
  `_tool_cache`/`_get_cached_tool_definition`/`call_tool`, `auth/middleware/bearer_auth.py`
  `required_scopes` — **replace** (R13's data-dependency claim CONFIRMED at source);
  per-tool scope filtering: grepped `mcp/server/fastmcp/tools/` for `scope` → **zero hits**,
  `required_scopes` is route-level only → **bespoke** subclass is correct and MINIMAL;
  `asgi_lifespan` 2.1.0 — read `_manager.py` signature + verified `running_asgi_app` returns
  a real `asgi_lifespan._manager.LifespanManager` (it even raises `sniffio.AsyncLibraryNotFoundError`
  outside an async context, as the library does) → **replace, correctly done, no twin**;
  `cachetools` → **replace**; `httpx` MockTransport → **keep**; `email-validator` → **NOT
  INSTALLED, and never surveyed by either side** for the roster address parser (§2);
  `watchdog` → **bespoke minimal** (agree). Full diff §2.
- **SATISFIABILITY RE-DISCHARGED, twice, on TWO structurally different correct builds:**
  variant A **472 passed / 0 failed**, and again **472/0 after `ruff --fix`**; variant B
  (resolver decision inside the scoped lookup) **472 passed / 0 failed**. §3.
- **RED baseline reproduced independently: 472 collected, 439 failed, 33 passed** — matches
  the lead's derivation exactly. 366 of 439 are `ImportError` (the right reason); every
  non-ImportError red inspected and honest. §7.
- **MISSING PINS:** N1 wire `tools/list` (BLOCKER) · N2 unannotated tool absent from the
  hosted list · N3 `127.0.0.0/8` resolves · N4 the ∀ effect pin's reach stops at `Tool.run` ·
  N5 a pre-existing security gate REDS on every correct build and is on nobody's handoff
  list · N6 the contract pins a refusal ORDER no ruling states. §6.
- **P2:** perturbation pair proven both legs — perturbed pins **4 passed** on the correct
  build, **4 failed** on WB71+WB72, while the **shipped contract stayed 472/0 on the same
  wrong builds**. §5.
- **P5:** the `TokeninfoSpy` fake mutated → **9 pins red**. The fakes can fail. §9.
- **P0, self-caught:** (a) my variant-B `cp -a` tree was importing `ref` (#140) — one false
  472/472 discarded and rebuilt as content-swap; (b) `WB75`'s "survival" was an artifact of
  variant A shielding it — re-run on variant B it dies 23 reds; (c) `WB88`'s carve-out never
  fired (fixture tokens are ~146 chars, threshold 200) — positive control `CTRL88` fires 23
  reds. §10.
- **decisions-needed:** N5 (adjudicate `auth=` against the R26 seam gate) · N6 (rule the
  refusal order) · WB74 (rule the extension annotation class).
- **Receipt pointers:** §3 satisfiability · §4.1 the blocker + control · §4.2–4.4 survivors ·
  §5 perturbation pair · §6 the pins to write · §8 the §8-handoff diff · §11 instruments,
  pasted verbatim.

---

## 1. Capability check (brief-base §4 — first, because a lead cannot see my toolset)

- **What was demanded:** the brief's `ToolSearch "select:mcp__lore_lore__lore_search,
  mcp__lore_lore__lore_impact"`, with an instruction to say so if absent.
- **What I actually have:** `ToolSearch` resolves **no** `mcp__lore_lore__*` tools. Two
  attempts, one before and one after the MCP servers finished connecting (the second after
  the `lore_lore` server had announced its instructions block, so this is not a race):
  `No matching deferred tools found`, both times.
- **What I did instead:** bare, anchor-free `grep` for every structural question (§8's
  corpse sweep, the SDK reads, the consumer set), plus the instrument the brief named — the
  reference build run against the rest of the suite, which is frame-independent in a way no
  grep is. **I do not claim graph-backed exhaustiveness anywhere in this report.**
- **Also absent: `SendMessage`.** `ToolSearch "select:SendMessage"` → `No matching deferred
  tools found`. I cannot notify the lead, cannot register in a comms fleet, and cannot ack a
  directive. **This report is my only channel** — which is exactly why brief-base §1 says to
  write the file regardless of what a brief names as the deliverable.
- **What a lead must change:** **finding #294 now reproduces on FOUR consecutive
  `contract-adversary` runs** (auth-1, auth-2, this pass, plus the 2026-07-28 instance the
  agent definition note records). The `contract-adversary` agent definition lists `ToolSearch`
  but the lore tools are not reachable through it. This is a defect in the agent DEFINITION,
  not in any brief; writing it into briefs a fifth time will not fix it. I also cannot file it
  through `lore_findings` — for the same reason.

**Deviation, declared:** my writable set is this report, so the instruments in §11 could not
be committed to `scripts/`. They are pasted **verbatim** instead (brief-base §1 route (b)).
Their scratch home `/home/ejprice/adv39-3/` is disposable by design; **do not cite it.**

---

## 2. P-PKG — my own survey, built before opening theirs, then diffed

Built from the installed trees, not from the design's table. Read column = what I actually
opened or executed.

| # | Mechanism the contract specifies | Package | What I READ / RAN | My verdict |
|---|---|---|---|---|
| 1 | Token-verifier protocol, 401 + `resource_metadata`, session identity, `.well-known` | `mcp` 1.27.2 | `server/fastmcp/server.py` lines 214 / 302–346 (`_tool_manager` construction; `_setup_handlers` registering the **bound** `self.list_tools` and `self.call_tool`; `instructions` property → `self._mcp_server.instructions`); `server/auth/middleware/bearer_auth.py:87–112` (`required_scopes` loop) | **replace** |
| 2 | **Per-principal tool scoping (R13)** | `mcp` 1.27.2 | `grep -rn scope server/fastmcp/tools/` → **0 hits**; `grep -rn required_scopes mcp/` → route-level `RequireAuthMiddleware` only. `tools/tool_manager.py` read in full — `call_tool` is `tool = self.get_tool(name); if not tool: raise; return await tool.run(...)` | **bespoke — and it is the MINIMAL gap**: subclass the SDK's own manager, override two methods. R13's data-dependency claim is TRUE at source. |
| 3 | Host/Origin rebinding validation | `mcp.server.transport_security` | `TransportSecuritySettings` fields + middleware | **replace_with_adapter** |
| 4 | TTL positive/negative caches | `cachetools` 7.1.6 | installed; exercised by the reference build's both caches, 472/472 | **replace** |
| 5 | Google tokeninfo transport | `httpx` | `MockTransport` used as the spy; POST-body idiom | **keep** |
| 6 | Google opaque **access**-token validation | `google-auth` | **not installed in this venv** (`find_spec('google.auth')` → `No module named 'google'`); the contract's table records an ephemeral `uv run --with google-auth` measurement, which I did not re-run | **bespoke** (agree — the measured read column is now earned) |
| 7 | Running an ASGI **lifespan** in a test | `asgi-lifespan` 2.1.0 | `_manager.py` signature `(app, startup_timeout=5, shutdown_timeout=5)`; asserted `type(running_asgi_app(...))` is `asgi_lifespan._manager.LifespanManager` — and it raises `sniffio.AsyncLibraryNotFoundError` outside an async context exactly as the library does | **replace — DONE, and it is genuinely the package, not a re-implementation wearing its name.** The brief's question, answered by execution. |
| 8 | Roster change detection | `os.stat` vs `watchdog` | reference build's `(st_mtime_ns, st_size, st_ino)`; watchdog is a thread+queue per watched TREE | **bespoke, minimal** (agree) |
| 9 | **Roster address SYNTAX validation** (`exactly one @`, non-empty local + domain) | `email-validator` | `find_spec('email_validator')` → **NOT INSTALLED** | ⚑ **survey gap — see below** |
| 10 | Email normalisation (NFKC → casefold → strip) | `unicodedata` (stdlib) | `lorerunes/emails.py` | **bespoke** (agree; stdlib is the package) |

### The DIFF against design §14 / `REPORT-contract-39-auth-1.md` §2

- **Rows 1, 3, 4, 5, 6, 8, 10 — agree**, and row 7 is now *executed* rather than asserted.
- **Row 2 has NO ROW ON THEIR SIDE.** R13 introduces a whole mechanism — a posture-scoped
  `ToolManager` — after the §14 table was written, and §16 does not add one. The verdict
  is nevertheless **correct** (`bespoke`): I measured that the SDK's tool layer has zero
  scope awareness. **Not a defect in the answer; a gap in the artifact.** A survey that
  stops being updated when a design ruling adds a mechanism is exactly the "a correction is
  a specification too — survey it" case.
- **Row 9 is the real P-PKG finding.** Both surveys fold roster-line syntax validation into
  *"`lorerunes` — extend"* with a read column naming only `blankness.py::is_blank`. Address
  syntax parsing is a well-known package's job (`email-validator`), and **no read column on
  either side names it**. The design's stdlib-only constraint on `lorerunes` is a *real* and
  *stated* reason a package cannot live in that module — but it is **not** a reason the
  validation could not live in `loremaster` and call one. **Verdict: escalate, do not
  hand-wave.** The operator should rule whether `email-validator` gets installed and the
  parser becomes `lorerunes` (shape check only) + `loremaster` (address validity), or whether
  the bespoke parser stands with the stdlib-only constraint written into the row.
  ⚠ I am NOT asserting the package does the job — I did not read its API, because it is not
  installed and I may not install it. That is precisely the escalation the two-sided rule
  requires, and it is the honest state of the read column.

---

## 3. THE SATISFIABILITY RECEIPT, re-discharged on THIS contract — twice

Predecessors' receipts are void (24 pins are new). I built the R13/R14/R15 reference build
by porting pass-2's production files into a `scratch_copy.sh` tree and implementing R13
(scoped `ToolManager` + `HOSTED_READ_LADDER_MARKER`), R14 (`_register_extension_tools`
synthesizes `ToolAnnotations(readOnlyHint=False, …)`) and R15 (`lorerunes.host_is_loopback`).

```
$ ./scripts/scratch_copy.sh /home/ejprice/adv39-3/ref          # exit 0, provenance asserted
$ cd /home/ejprice/adv39-3/ref && uv run python -c "import loremaster, lorerunes; ..."
loremaster: /home/ejprice/adv39-3/ref/loremaster/loremaster/__init__.py
lorerunes:  /home/ejprice/adv39-3/ref/lorerunes/lorerunes/__init__.py
```

`CONTRACT` is verbatim from `REPORT-contract-39-auth-1.md` §14.6 (`lorerunes/tests` +
seven loremaster modules), i.e. **472 collected = 471 contract pins + the pre-existing
`lorerunes/tests/test_smoke.py`**. That decomposition is stated here because a bare "472"
looks like 472 new pins and it is not.

**Variant A** — the posture decision in `get_tool`; the resolver stays in the async wrapper,
which pre-invokes `mcp._tool_manager.get_tool(name)` to force the ruled refusal order:

```
$ /home/ejprice/adv39-3/run_contract.sh /home/ejprice/adv39-3/ref -p no:randomly -n auto -q --tb=line
472 passed in 7.84s
```

**The post-ruff leg** (the harder half — the orphaned imports deleting `BearerAuthMiddleware`
forces):

```
$ uv run ruff check .            → Found 1 error (unsorted imports in server.py)
$ uv run ruff check --fix .      → Found 1 error (1 fixed, 0 remaining)
$ uv run ruff check .            → All checks passed!
$ /home/ejprice/adv39-3/run_contract.sh … → 472 passed in 7.51s
```

**Variant B** — a structurally different, equally legal reading: the resolver's narrowed-set
decision moves INSIDE `_PostureScopedToolManager.get_tool` via a `ContextVar` the async
wrapper populates, so the wrapper raises nothing and both refusals are raised by the lookup
in the ruled order:

```
$ cp /home/ejprice/adv39-3/refbuildB/server.py loremaster/loremaster/server.py
$ uv run python -c "import loremaster;print('PROVENANCE:',loremaster.__file__)"
PROVENANCE: /home/ejprice/adv39-3/ref/loremaster/loremaster/__init__.py
$ /home/ejprice/adv39-3/run_contract.sh … → 472 passed in 7.96s
```

**Two independent correct builds, both 0-failed.** The contract is satisfiable, and the C-DEF
class is clear *within the contract's own file set* — but see **N5 (§6)**, which is a pin
OUTSIDE that set that reds on both of them.

---

## 4. P1 — wrong builds

**18 builds run this pass.** Each patch anchor must match exactly once (hard error otherwise)
and every run's COLLECTED total is compared to 472, so a mutation that fails to land, or that
breaks collection, cannot be mistaken for a survivor. Harness pasted at §11.1.

| build | what it does | verdict |
|---|---|---|
| **WB93** | list filtering installed as a post-construction `mcp.list_tools` attribute | ⚑ **SURVIVES — BLOCKER** |
| **WB71** | `host_is_loopback` is a hardcoded spelling set, not `.is_loopback` | ⚑ **SURVIVES** |
| **WB72** | hosted `list_tools` filters on `is False`, not `is not True` | ⚑ **SURVIVES** |
| **WB74** | extension annotation carries `destructiveHint=True, openWorldHint=True` | **SURVIVES (spec-silent)** |
| WB73 | instructions render reads the SCOPED list | survives, **no consequence** — §4.5 |
| WB88 | length-shaped carve-out in `_write_scoped` | survives — **my probe's fault**, §10 |
| WB70 | resolver filter placed after `super().call_tool` | killed (4 red) |
| WB70b | resolver decision computed before, RAISED after dispatch | killed (3 red) |
| WB75 | scoped manager's `call_tool` reads `_tools` directly | **invalidated** — variant A shields it, §10 |
| WB75B | same, on variant B where it is reachable | killed (23 red) |
| WB79B | the body reached via `tool.fn`, below `Tool.run` | killed (21 red) |
| WB79c | ditto, with the `TypeError` swallowed so ONLY the effect differs | killed (1 red) — §4.4 |
| WB76 | `list_tools` keyed on posture, not on scopes | killed (1 red) |
| WB77 | extension annotation grafted on in `list_tools` | killed (4 red) |
| WB86 | roster re-read failure keeps the LAST GOOD roster | killed (17 red) |
| WB87 | cached Google verdict served past `expires_at` | killed (2 red) |
| CTRL88 | the WB88 carve-out flipped so it fires (positive control) | killed (23 red) ✔ |
| WB78 | (declared, never run — placeholder anchor) | n/a |

### 4.1 ⚑ WB93 — THE BLOCKER: `tools/list` is pinned only IN PROCESS

**The reasoning that finds it.** R13's whole move is that a refused tool *is not returned*.
That makes `list_tools` a **security-relevant served surface for the first time** — before
R13 it was a convenience. Every pin on it is in
`TestTheScopedLookupIsTheEnforcementSeam`, and every one calls **`await mcp.list_tools()`**.
That is the identical entry point WB30 exploited on the call route: `FastMCP.__init__` calls
`_setup_handlers`, which registers the **bound** `self.list_tools` with the lowlevel server, so
a post-construction instance attribute is **live for the pins and dead on the wire**. The
packet added a wire pin for `tools/call` and never added one for `tools/list`.

**And the door is not exotic — the design creates friction that pushes a builder through it.**
`_install_hosted_instructions` must render the refused set from the **unscoped** registry; once
`ToolManager.list_tools` is scoped, that render has to reach past its own override (my reference
build calls `ToolManager.list_tools(mcp._tool_manager)` explicitly to get around it). A builder
who finds that awkward will naturally move the filter *up* to the FastMCP layer. If they do it by
overriding the method on the `TracingFastMCP` **subclass**, they are correct. If they do it as an
instance attribute after construction — the more obvious spelling, and the one WB30 already
proved a builder reaches for — the served surface is unguarded and **every pin stays green**.

The patch (verbatim; `list_tools` removed from the scoped manager, filter installed at
`build_mcp_server` after `mcp._tool_manager = scoped_manager`):

```python
    async def _scoped_list_tools() -> Any:
        from mcp.types import Tool as _MCPTool
        manager = mcp._tool_manager
        tools = ToolManager.list_tools(manager)
        if not manager._write_scoped():
            tools = [tool for tool in tools if manager._is_read_only(tool)]
        return [_MCPTool(name=info.name, title=info.title, description=info.description,
                         inputSchema=info.parameters, outputSchema=info.output_schema,
                         annotations=info.annotations, icons=info.icons, _meta=info.meta)
                for info in tools]

    mcp.list_tools = _scoped_list_tools  # type: ignore[method-assign]
```

**The contract's verdict on it:**

```
$ /home/ejprice/adv39-3/run_contract.sh /home/ejprice/adv39-3/ref -p no:randomly -n auto -q --tb=line
472 passed in 7.52s
```

**The consequence, over a REAL MCP session** (probe pasted §11.3 — `initialize` →
`notifications/initialized` → `tools/list`, authenticated as a live allowlisted Google
principal through the real verifier and the real transport):

```
WB93            :  WIRE tools/list : 15 tools; mutating leaked =
                   ['lore_claim_task','lore_comms','lore_findings','lore_index',
                    'lore_remember','lore_tasks']
```

**LEG 0, THE CONTROL — the same probe, same command, on the correct reference build:**

```
PROVENANCE: /home/ejprice/adv39-3/ref/loremaster/loremaster/__init__.py
WB93 reverted   :  WIRE tools/list :  9 tools; mutating leaked = []
1 passed in 0.68s
```

**Severity.** This is not "the guard is gone" — `get_tool` still refuses the call, so nothing
mutates. It is the **Consumer Law** half of R13, entirely defeated: the hosted agent is
*offered* six tools that will always refuse. Under the trust doctrine that is a served surface
that over-claims, and the documented consequence is the agent burning calls and then routing
around the MCP. R13's design text names `list_tools` filtering as one of the two halves of the
mechanism; the contract pins that half only where a test can see it.

**⚠ And the general shape, which is worth more than the pin:** the packet has now been beaten
**three times by the same defect** — WB30 (call route, wave 1), WB48 (call route, wave 2),
WB93 (list route, wave 3). Each fix pinned the *route that had just been broken*. **`tools/list`
became security-relevant the moment R13 shipped, and it inherited zero of the wire discipline
`tools/call` had earned.** The askable form for whoever writes the fix: ***"which SERVED MCP
method does this ruling newly make load-bearing, and is there a wire pin on it?"***

### 4.2 ⚑ WB71 — `host_is_loopback` as a spelling set (R15's rule not enforced)

R15 rules the predicate as *"the literal `localhost`, OR `ipaddress.ip_address(host)` parses and
`.is_loopback` holds"*. `.is_loopback` admits the whole `127.0.0.0/8` block. The contract's host
parametrisations are `["127.0.0.1","localhost","::1"]` (resolve), `["LOCALHOST","LocalHost"]`
(resolve), `["0.0.0.0","192.168.64.100","::"]` (refuse) and
`["lore.firehawktransam.org","lore-internal","example.com","","not a host"]` (refuse).
**Every accepted value is one a hardcoded set recognises**, so a set-membership build passes:

```
WB71: SURVIVES — 472 collected, 472 passed, 0 failed
```

Consequence probe (§11.2), both legs:

```
                     reference build        WB71
  127.0.0.1       -> HOSTED_OAUTH        HOSTED_OAUTH        (pinned)
  127.0.0.2       -> HOSTED_OAUTH        REFUSES TO BOOT     (UNPINNED)
  127.0.1.1       -> HOSTED_OAUTH        REFUSES TO BOOT     (UNPINNED)
  127.53.4.9      -> HOSTED_OAUTH        REFUSES TO BOOT     (UNPINNED)
  localhost       -> HOSTED_OAUTH        HOSTED_OAUTH        (pinned)
  ::1             -> HOSTED_OAUTH        HOSTED_OAUTH        (pinned)
```

This is a **fail-CLOSED** defect, which is why it matters here rather than despite it:
`127.0.1.1` is what Debian/Ubuntu put in `/etc/hosts` for the machine's own name, and an
operator who binds it gets a refusal naming `HOSTED_OAUTH` as the *nearest* posture with no
hint that the bind is the problem. Design §5's own law: *"a gate that refuses honest code is a
gate that gets SWITCHED OFF."* The `LOCALHOST`/`LocalHost` pins were added in this very revision
as the control against over-tightening R15 — and they closed the *casing* axis while leaving the
*address-block* axis, which is the one R15 actually names, wide open.

### 4.3 ⚑ WB72 — deny-by-default governs the lookup but not the SERVED list

`get_tool` refuses on `readOnlyHint is not True`; the scoped `list_tools` in WB72 filters on
`is not False`. On the stock registry the two are indistinguishable (every tool is annotated),
so:

```
WB72: SURVIVES — 472 collected, 472 passed, 0 failed
```

The only pin that registers an unannotated tool,
`test_a_tool_registered_with_no_annotations_is_born_refused`, derives its set via
`mutating_tool_names(mcp)` — which the module's own docstring correctly requires be called
**unauthenticated**, so it never observes the hosted projection. Consequence, both legs:

```
                             reference build   WB72
  advertised in list_tools :   False            True
  outcome of calling it    :   refused          refused   ← offered and always refused
```

Same class as N1, one layer down: R8's deny-by-default is pinned on the *lookup* and not on the
*served list*, and the served list is what an agent learns the contract from.

### 4.4 The ∀ effect pin's REACH stops at `Tool.run` — measured, not argued

Design R13 rider (1) claims the derived ∀ effect pin catches the raw-`_tools` side door. I tested
that claim at two depths on variant B (where the door is actually reachable — see §10):

- **`tool.run(...)` bypass (WB75B):** killed, **23 red**. The claim holds.
- **`tool.fn(...)` bypass, one level below the recorder's boundary (WB79c), with the incidental
  `TypeError` swallowed so ONLY the effect differs:**

```
$ uv run pytest -q loremaster/tests/test_hosted_readonly_posture.py::TestARefusedToolNeverRUNS
1 failed, 3 passed
FAILED …::test_the_same_synthetic_tool_is_refused_WITHOUT_running_when_hosted
  AssertionError: the refused tool's body ran before the refusal was raised — and its
  arguments were valid, so the write really happened   assert not [1]
```

`test_no_refused_tool_body_is_ever_entered_for_a_hosted_principal` — the **∀ over the whole
registry** — **PASSED**. It is blind to a body reached below `Tool.run`. What caught the bypass
is rider (2), the **single synthetic** `lore_probe_write` fixture with its own body counter.

So the honest statement of the instrument is: *the ∀ is over "`Tool.run` was entered", not over
"the body ran", and the only assertion about the body itself is at **N = 1 tool**.* That is
adequate today and it is the exact shape ("the next counter nobody wrote") R13 rider (1) was
written to avoid. **Fixable in three lines** — see N4.

### 4.5 WB73 — a survivor with NO consequence, stated so the count is honest

Computing the instructions render from the *scoped* list survives, and it is **behaviourally
identical to correct**, because `_install_hosted_instructions` runs at build time when no
principal is ambient:

```
[WB73] the refused-set clause, built with vs without an ambient principal:
  no principal ambient : …refused at call time: lore_claim_task, lore_comms, lore_findings, …
  hosted principal     : …refused at call time: lore_claim_task, lore_comms, lore_findings, …
  IDENTICAL: True
```

**Not a finding.** It is a latent coupling — the render's correctness depends on an absence
nobody asserts — and I record it as a residual (§12), not as a missing pin.

### 4.6 WB74 — the extension annotation's CLASS is unpinned (spec-silent)

R14 rules `readOnlyHint=False` on every extension tool; it says nothing about the rest of
`ToolAnnotations`. A build synthesizing `readOnlyHint=False, destructiveHint=True,
idempotentHint=True, openWorldHint=True` passes **472/472**. The consequence is a served
annotation set telling an MCP host that an in-project extension tool is *destructive* and
queries an *open external world* — both false, both things a host reasons about before calling.
**This is a design silence, not a contract miss**; §6-N7 states it as a ruling to make.

---

## 5. P2 — fixture perturbation, with the correct-build control leg

Perturbed pins written into a **scratch copy** of the test tree (§11.4), never the repo.

**Leg A — the correct reference build (without this leg a red is just a botched expectation):**

```
$ uv run pytest -q loremaster/tests/test_adv39t_perturbations.py --tb=line
4 passed in 0.63s
```

**Leg B — the same four pins on WB71 + WB72:**

```
4 failed in 0.67s
FAILED …::test_PERTURBED_a_non_dot_one_loopback_bind_still_resolves[127.0.0.2]
FAILED …::test_PERTURBED_a_non_dot_one_loopback_bind_still_resolves[127.0.1.1]
FAILED …::test_PERTURBED_a_non_dot_one_loopback_bind_still_resolves[127.53.4.9]
FAILED …::test_PERTURBED_an_unannotated_tool_is_not_offered_to_a_hosted_principal
```

**And the control that makes the pair mean something — the SHIPPED contract on those same
two wrong builds:**

```
$ /home/ejprice/adv39-3/run_contract.sh … -n auto -q --tb=no
472 passed in 7.86s
```

Four perturbed pins discriminate exactly where the shipped 472 cannot.

**Fixture-discrimination verdicts, individually:**

| fixture | verdict |
|---|---|
| host parametrisations in `TestTheBootRefusalReachesTheThingThatActuallyBoots` | ⚑ **cannot discriminate** a spelling-set build from R15's predicate — every accepted value is set-recognisable. Perturbation `127.0.0.2` blinds it; pair proven. |
| `TestTheScopedLookupIsTheEnforcementSeam` list pins | ⚑ **cannot discriminate** `is not True` from `is not False` — the stock registry has no unannotated tool. Pair proven. |
| every `list_tools` pin (entry point) | ⚑ **cannot discriminate** an in-process filter from a served one — all drive `mcp.list_tools()`. §4.1. |
| `TestARefusedToolNeverRUNS` ∀ recorder | **discriminates at `Tool.run`**; blind below it. Its one synthetic counter covers the gap at N=1. §4.4. |
| `google_principals` / `api_key_principals` | **discriminates** — two emails, two subjects, two key names. Monoculture law satisfied. |
| `EXPECTED_MUTATING_TOOLS` asserted **EQUAL** to the derived set | **discriminates** — equality, not subset; WB77's list-path graft dies on it. |
| `hosted_server(with_extension=…)` parametrised over both registration paths | **discriminates** for `readOnlyHint` (WB77 dies); **N = 1 extension, 1 tool**, and it cannot see the annotation CLASS (WB74 survives). |
| the R12 roster probes (`_RosterProbe`) | **discriminates strongly** — each establishes a healthy-roster positive control BEFORE breaking it, which is what kills WB86's keep-last-good build (17 red). |
| `TokeninfoSpy` call-count assertions | **discriminates** — WB87 and the P5 mutation both die on them. |
| `write_roster(header=…)` | **inert** — no pin ever passes `header=False`. A factory parameter no fixture exercises. Residual, §12. |
| `_TwoPrincipalEdge` wire fixture | **discriminates** on the call route (it is what kills WB30-shaped call builds) and is **the fixture N1 needs and does not have a list pin on**. |

---

## 6. THE MISSING PINS — each as *the test to write* + *the defect it catches*

**N1 — BLOCKER. `test_a_hosted_principal_does_not_see_refused_tools_over_the_WIRE`,
in `test_auth_identity_seam.py::TestTheReadOnlyGuardFiresOnTheSERVEDPath`.**
Drive `_TwoPrincipalEdge`: `initialize` → `notifications/initialized` → `tools/list` as
`edge.operator_token`; assert the returned names are exactly the read ladder. **Two controls,
neither optional:** the same `tools/list` as `API_KEY_VALUE_LOCAL_AGENT` returns the full
fifteen (or a build that filtered everyone passes), and the read ladder is non-empty (or a
build serving zero tools passes). *Catches:* **WB93** — the R13 list filter installed as a
post-construction instance attribute, live in every pin and dead on the wire, offering a
hosted agent all six mutating tools. Working probe pasted at §11.3; it needs ~5 lines of
adaptation to become the pin.

**N2 — `test_an_unannotated_tool_is_not_offered_to_a_hosted_principal`,
in `TestTheScopedLookupIsTheEnforcementSeam`.** Register an unannotated tool on a hosted
server, then assert it is absent from `list_tools()` **under an `as_principal(google…)`
block**. *Catches:* **WB72** — deny-by-default governing the lookup but not the served list.
Written and pair-proven at §11.4.

**N3 — `test_a_non_dot_one_loopback_bind_still_resolves`, parametrised
`["127.0.0.2","127.0.1.1"]`, beside `test_every_loopback_SPELLING_still_resolves_to_hosted_oauth`.**
*Catches:* **WB71** — `host_is_loopback` implemented as a spelling set rather than R15's
`.is_loopback` predicate, refusing to boot on an honest `127.0.1.1` bind. Written and
pair-proven at §11.4. (Consider also `test_a_bracketed_loopback_is_False` for `[::1]`, which
R15's rider names and no pin asserts — see §12.)

**N4 — extend `TestARefusedToolNeverRUNS::_run_entry_recorder` to wrap each registered tool's
`fn` as well as `Tool.run`**, and assert the ∀ over BOTH boundaries. *Catches:* a bypass that
reaches the body below `Tool.run`, which the registry-wide ∀ currently cannot see (§4.4,
measured: that pin PASSED while the body demonstrably ran). Three lines; it turns rider (1)'s
claim from *true-at-one-depth* into *true*.

**N5 — ⚑ C-DEF, and it is not fixable inside the contract.
`loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::
test_no_auth_header_is_built_outside_a_seam` REDS on EVERY correct build.**
Its v2 leg flags any call keyword named `headers=`/`auth=` not sourced from
`build_auth_headers()`. Design §6 rules the composition `FastMCP(…, auth=AuthSettings(…))`
— a keyword literally spelled `auth`. Reproduced on the reference build:

```
$ uv run pytest -q loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam
E   AssertionError: these sites build an outgoing auth header outside the typed seam.
    R26: route them through build_auth_headers(credential: SecretStr) …
      loremaster/server.py:8028 auth= not sourced from build_auth_headers()
1 failed
```

The prescribed remedy is nonsense for this call (`AuthSettings` is not a credential), the site
is unavoidable, and the only ways past it are to weaken a security gate or to obfuscate the
call — the two moves that gate's own threat model was written to prevent. **This is a ruling
the design owes, not a builder decision:** exempt the SDK's `auth=` parameter *by an
evidence-backed allowlist of the safe* (e.g. "a keyword `auth=` whose value is an
`AuthSettings` construction"), never by widening the deny pattern. It appears in **neither**
design §8 **nor** the contract's own re-derived handoff table — see §8.

**N6 — the contract pins a refusal ORDER that no ruling states.**
`test_the_posture_guard_and_the_resolver_are_distinguishable` requires that when a hosted
principal is refused by **both** the posture guard and the resolver, the exception is
`HostedToolRefusedError`. Under R13 the posture decision lives inside `get_tool` — reached by
the SDK **inside** dispatch — while the resolver is async and must run **above** it. **The
natural implementation therefore fails this pin**; I hit it on my first reference build:

```
FAILED …::test_the_posture_guard_and_the_resolver_are_distinguishable
E  assert False
   +  where False = isinstance(PermissionFilteredToolError("lore_remember is not in this
      principal's resolved permitted set"), <class 'loremaster.server.HostedToolRefusedError'>)
```

Two different mechanisms were needed to satisfy it (variant A pre-invokes the scoped lookup
from the wrapper; variant B moves the resolver decision into the lookup behind a `ContextVar`).
Both are legitimate; nothing tells a builder which. **Design §7/§15 rules neither the order nor
the mechanism.** Per project law — *"spec ambiguity is a defect, not a judgment call"* — this
is an escalation. *Recommendation:* keep the pin (posture-before-filter is the right teaching:
the posture refusal is un-grantable, the filter one an operator can lift) and **rule the
mechanism in the design**, naming variant B, because it keeps ONE ordered decision site
instead of two.

**N7 — a ruling, not a pin: R14 should state the FULL annotation class it synthesizes.**
*Catches:* **WB74**. Either the design names all four hint values (and the contract pins the
tuple), or it states explicitly that only `readOnlyHint` is ruled and the rest are
builder-discretion — which is a decision, and decisions get written down.

---

## 7. P4 / P7 — the author's claims, reproduced rather than relayed

**The RED baseline**, derived independently in a tree restored to `af74611` production code:

```
$ /home/ejprice/adv39-3/run_contract.sh … -p no:randomly -n auto -q --tb=no
439 failed, 33 passed in 6.59s
$ … --collect-only -q → 471 tests collected   (+1 lorerunes/tests/test_smoke.py = 472)
```

**472 / 439 / 33 — the lead's and the author's counts reproduce exactly.**

**RED honesty** — the failures are for the right reason, classified over all 439:

| reason | count | verdict |
|---|---|---|
| `ImportError` (the production symbol does not exist yet) | 366 | ✔ right reason |
| `AssertionError` | 6 | ✔ inspected: retired-symbol pins (`BearerAuthMiddleware`/`AuthVerifier` still present), `__all__` contents, `tls_terminated_upstream` still on the model |
| `pydantic ValidationError` | (within the above tail) | ✔ `LoreConfig` rejecting the `google:` block that does not exist yet |
| `TypeError` | 1 | ✔ `build_mcp_server() got an unexpected keyword argument 'http_client'` — B4's ruled signature |
| `AttributeError` | 1 | ✔ `loremaster.auth has no attribute '_new_http_client'` |

No import typo, no bad path, no fixture error. The pipe carried a COUNT in every run above.

**The 33 GREEN** are all preserved-behaviour pins, as claimed: `test_auth.py` 28 (ApiKeyVerifier
verbatim / `build_api_key_verifier` / OriginValidationMiddleware), `test_auth_composition.py` 2,
`test_auth_identity_seam.py` 1, `test_email_normalisation.py` 1, `test_smoke.py` 1.

---

## 8. P6 / P6b

### 8.1 P6 — corpse sweep, bare anchor-free patterns, every hit with an individual verdict

Patterns: `BearerAuthMiddleware`, `AuthVerifier`, `tls_terminated_upstream`, `_MUTATING_TOOLS`,
`realm=`, `realm="loremaster"` — no prefix anchor, no call-paren anchor, prose included, across
`*.py *.md *.yaml *.toml *.txt`. Reports and `docs/plans/v2/receipts/` excluded as documentation.

| hit | verdict |
|---|---|
| `loremaster/loremaster/auth.py` — module docstring ×2, `__all__` ×2, `class AuthVerifier`, `class ApiKeyVerifier(AuthVerifier)`, `class BearerAuthMiddleware`, `__init__` docstring, `_WWW_AUTHENTICATE` | **the code being deleted** — §8 rows 9/13/14 + S6. |
| `loremaster/loremaster/config.py:24` module docstring; `:348` Args; `:355` the field | **the field being deleted + its prose site** — §8 rows 7/12. |
| `loremaster/tests/test_auth.py:4,13,66,68,547` | **NOT a corpse** — these pin the names as RETIRED (`assert 'BearerAuthMiddleware' not in dir(...)`), currently RED and correct. |
| `loremaster/tests/test_hosted_readonly_posture.py:13,28,33,99,…` | **NOT a corpse** — `_MUTATING_TOOLS` appears only in prose explaining #291, and `EXPECTED_MUTATING_TOOLS` is the new anchor. |
| `loremaster/tests/test_mcp_server.py::_MUTATING_TOOLS` + `test_mutating_tools_are_not_marked_read_only` | ⚑ **LIVE CORPSE** — outside the contract's writable set; handoff row 5 says DELETE. Confirmed again this pass: it does **not** red on either reference build (it is a subset check), so nothing will force its deletion. |
| `loremaster/loremaster/calibration/corpus/comment_light_python.py.txt:200,207` | ⚠ **DO NOT EDIT** — frozen calibration corpus; editing perturbs the token baseline. Correctly named on the handoff table. |
| `loremaster/loremaster/logging_setup.py:228`, `test_secret_leak_vectors.py:543,552` (`realm=`) | **unrelated** — HTTP Digest redaction fixtures, nothing to do with packet 39. |
| `docs/plans/v2/39-hosted-security.md:31` (`tls_terminated_upstream`) | **the packet plan naming the disposition to make.** Stale after the build; a doc line, not a gate. Flagged for the close-out. |
| `lore.yaml`, `lore.yaml.sample`, `skills/lore-deploy/` | **CLEAN** — no `auth:` block, no retired field; the `extra="forbid"` migration breaks no config on this host. |
| `docs/design/2026-07-31-packet39-google-oauth.md` (all hits) | **the design doc adjudicating them.** Correct. |

### 8.2 P6b — enumeration of the code being deleted, then the diff

⚠ **Independence caveat, stated plainly:** I read design §8 before enumerating, because it is in
the same file as the R13/R14/R15 rulings the brief sent me to grade. My enumeration is therefore
**not frame-independent this pass** — passes 1 and 2 each did a genuinely blind enumeration and
diffed. What follows is a re-derivation from `auth.py` at `af74611` looking specifically for
behaviours *neither* §8 *nor* the two prior diffs name.

Behaviours found in `BearerAuthMiddleware` / `AuthVerifier`: non-HTTP scopes pass through (row 4)
· missing header → 401 (row 1) · non-Bearer scheme → 401 (row 1) · case-insensitive `bearer `
prefix (row 2) · latin-1 decode (row 3) · token taken verbatim after the 7-char prefix,
**unstripped** (pass-1 diff: equivalent to the SDK's `auth_header[7:]`) · 401 body `Unauthorized`
+ `text/plain; charset=utf-8` (row 8) · `WWW-Authenticate: Bearer realm="loremaster"` (row 1/S6)
· fail closed before the wrapped app (row 6) · every path gated (rows 7/15) · nothing logged
(row 5) · sync `verify` seam (row 9) · `ApiKeyVerifier` **is-a** `AuthVerifier` (pass-2 D2,
inert) · the verifier is consulted on **every** request with no caching.

**Two behaviours I looked for specifically and adjudicate here:**

1. **First-`authorization`-header-wins.** `_bearer_token` returns on the FIRST matching header and
   ignores any later one. **Not in §8.** Verdict: **equivalent, not a finding** — Starlette's
   `Headers.get`, which the SDK's `BearerAuthBackend` uses, also returns the first.
2. **No caching on the api-key path.** The new `LoreTokenVerifier` caches only Google's verdict;
   `_api_key_principal` runs the constant-time compare on every call. **Preserved**, and §8 row 11
   covers the class. Not a finding.

**Diff verdict: no un-adjudicated behaviour found this pass** — with the independence caveat above
carried, not swallowed.

### 8.3 The handoff list, re-verified by the instrument that found it short twice

Reference build run against the rest of the suite — the frame-independent instrument:

```
$ uv run pytest -n auto -q --tb=no -rf loremaster/tests lorerunes/tests loresigil/tests lorescribe/tests
5 failed, 8166 passed, 36 skipped, 3 xfailed in 244.53s
```

| collateral red | on the handoff table? |
|---|---|
| `test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true` | ✔ row 4 |
| `test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost` | ✔ row 1 |
| `test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated` | ✔ row 2 |
| `test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware` | ✔ row 3 |
| **`test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam`** | ⚑ **MISSED — third pass running, third time this instrument finds a site a grep could not.** N5. |

The instrument keeps earning its place: pass 1 found 3 sites the design missed, pass 2 confirmed
them, and pass 3 finds a **sixth** that no name-grep could ever have found, because the offending
token is the SDK's own parameter name.

---

## 9. P5 — can the test doubles FAIL?

| double | verdict |
|---|---|
| `TokeninfoSpy` (`httpx.MockTransport`) | ✔ **PROVEN able to fail.** Mutated `call_count` to `1 if self.requests else 0` → **9 pins red** (`TestNegativeCacheSplitsDefinitiveFromTransient` ×7, `test_two_different_tokens_do_not_share_a_cache_entry`, `…[connect-error]`). Tail: `9 failed, 463 passed in 7.47s`. |
| `_AllowOnlyResolver` | ✔ **proven able to filter** by the contract's own paired pin + its control (`test_a_tool_outside_…_is_refused` / `…_is_not_refused`). |
| `_run_entry_recorder` | ✔ has an explicit positive control (`test_the_recorder_CAN_see_a_body_execute`) — and I measured its BOUND (§4.4): it can see `Tool.run`, it cannot see `tool.fn`. |
| `_NeverServes` (uvicorn stub) | ✔ raises if constructed AND the pin asserts `not served`; both directions live. |
| `_RosterProbe` | ✔ every fail-closed pin establishes a healthy-roster admission first; WB86's 17 reds are the receipt that the probe sees the difference. |
| `_StubAppContext` / `stub_heavy_startup` | ⚠ **cannot fail, and does not need to** — it is a neutraliser, not an oracle; the pins that use it assert on auth behaviour only. Its docstring is honest about the substitution. Verdict: acceptable. |
| `CounterExtension` | ✔ a real extension contributing a real tool; WB77's 4 reds are the receipt. **N = 1 extension, 1 tool** — noted under fixtures, §5. |

---

## 10. P0 — my OWN probes' failures, all three self-caught

**(a) #140 reproduced, in my own hands.** I built variant B as `cp -a /home/ejprice/adv39-3/ref
/home/ejprice/adv39-3/refB` and got a clean `472 passed`. Then the provenance print said:

```
loremaster: /home/ejprice/adv39-3/ref/loremaster/loremaster/__init__.py     ← the ORIGINAL
```

The copied venv's editable `.pth` names the absolute source path, so **that run graded `ref`,
not `refB`.** The 472 was real and meaningless. **Discarded**; variant B was rebuilt as a
CONTENT swap into the one tree whose provenance `scratch_copy.sh` asserted, re-run, and only
then reported (§3). The harness now carries the rule as a comment so the next run cannot repeat it.

**(b) `WB75` "SURVIVES" was an artifact of my own reference build.** WB75 (the scoped manager's
`call_tool` reading `self._tools` directly) passed 472/472 on variant A — but variant A's wrapper
pre-invokes `mcp._tool_manager.get_tool(name)` to satisfy the ordering pin (N6), which raises
before `super().call_tool` is ever reached, so **the door I built was unreachable in the build I
built it against.** Re-run as `WB75B` on variant B, where it *is* reachable: **killed, 23 red.**
Reported as invalidated, not as a survivor.

**(c) `WB88`'s carve-out never fired.** `len(token) > 200` exempts nothing: `google_access_token`
mints ~146-character tokens (`ya29.a0Af` + label + 128 hex). Its "SURVIVES" says nothing about the
contract. **Positive control `CTRL88`** — the identical carve-out flipped to `< 200` so it *does*
fire — **kills 23 pins**, which proves the harness can see a broken write-scope decision. WB88 is
reported as a probe defect, not a finding. *(It does leave one true observation: the fixture
tokens are ~146 chars where real Google access tokens are longer. Nothing in this contract branches
on length, so it is inert — but it is a value monoculture, recorded in §12.)*

Every negative result above is paired: the WB93 wire probe has its correct-build leg (9 tools, 0
leaked); the WB71/WB72 consequence probes have theirs; the perturbations have leg A; the fake
mutation has the 472-green baseline it departs from.

---

## 11. The instruments (brief-base §1 — pasted, because I may not commit them)

**Recommendation, now made by three consecutive adversaries:** commit
`scripts/adv39_wrong_builds.py` (pass 1's 45-entry registry), `scripts/adv39d_new_builds.py`
(pass 2's 11), **this pass's harness + the wire probe**, and a reference build, in the wave
commit. Finding #278 is the receipt for what happens otherwise; the only reason this pass could
stand on pass 2's work in minutes is that `/home/ejprice/scratch/refbuild/` happened to survive
on disk.

### 11.1 `adv39t_wrong_builds.py` — the harness (mechanism; the per-build patches follow)

```python
#!/usr/bin/env python3
"""adv39t_wrong_builds.py — pass-3 wrong builds against the packet-39 contract.

Contract at lore HEAD ``af74611`` (472 collected).

GUARDS (both load-bearing — a mutation that does not LAND produces a green run that reads
exactly like a survivor):
  1. every anchor must match EXACTLY once, else hard error before any pytest runs;
  2. every run's COLLECTED total is compared to the baseline 472.
"""
from __future__ import annotations
import os, re, shutil, subprocess, sys
from dataclasses import dataclass
from pathlib import Path

REF = Path("/home/ejprice/adv39-3/ref")
# ⚠ THE MUTATION TREE IS ALWAYS ``ref`` — the ONE tree whose provenance was asserted
# (``loremaster.__file__`` inside it). A ``cp -a`` sibling silently imports THIS tree
# (#140), which cost this run one false 472/472 before it was caught. Variants are
# swapped in as CONTENT, never as a second checkout.
PRISTINE = Path(os.environ.get("ADV39T_PRISTINE", "/home/ejprice/adv39-3/refbuild"))
BASELINE_COLLECTED = 472

FILES = {
    "server.py": REF / "loremaster/loremaster/server.py",
    "auth.py":   REF / "loremaster/loremaster/auth.py",
    "config.py": REF / "loremaster/loremaster/config.py",
    "posture.py": REF / "lorerunes/lorerunes/posture.py",
    "emails.py":  REF / "lorerunes/lorerunes/emails.py",
}

def _pristine(key: str) -> Path:
    mangled = {"server.py": "loremaster_loremaster_server.py",
               "auth.py": "loremaster_loremaster_auth.py",
               "config.py": "loremaster_loremaster_config.py",
               "posture.py": "lorerunes_lorerunes_posture.py",
               "emails.py": "lorerunes_lorerunes_emails.py"}
    bare = PRISTINE / key
    return bare if bare.exists() else PRISTINE / mangled[key]

CONTRACT = ("lorerunes/tests loremaster/tests/test_auth.py "
            "loremaster/tests/test_google_token_verifier.py "
            "loremaster/tests/test_allowlist_roster.py loremaster/tests/test_auth_composition.py "
            "loremaster/tests/test_auth_identity_seam.py "
            "loremaster/tests/test_hosted_readonly_posture.py "
            "loremaster/tests/test_permission_resolver_seam.py").split()

@dataclass
class WrongBuild:
    name: str
    description: str
    patches: list[tuple[str, str, str]]   # (file key, anchor, replacement)

def restore() -> None:
    for key, path in FILES.items():
        shutil.copy2(_pristine(key), path)

def apply(build: WrongBuild) -> None:
    for key, anchor, replacement in build.patches:
        path = FILES[key]; text = path.read_text(); count = text.count(anchor)
        if count != 1:
            raise SystemExit(f"{build.name}: anchor matched {count} times (must be 1) in {key}\n{anchor}")
        path.write_text(text.replace(anchor, replacement, 1))

def run_contract() -> tuple[int, int, int, list[str]]:
    proc = subprocess.run(["uv","run","pytest","-p","no:randomly",*CONTRACT,"-n","auto","-q","--tb=no","-rf"],
                          cwd=REF, capture_output=True, text=True, timeout=3600)
    out = proc.stdout + proc.stderr
    def _n(pat: str) -> int:
        m = re.search(pat, out); return int(m.group(1)) if m else 0
    passed, failed, errors = _n(r"(\d+) passed"), _n(r"(\d+) failed"), _n(r"(\d+) errors?")
    node_ids = sorted({l.split(" ",1)[1].split(" ")[0] for l in out.splitlines() if l.startswith("FAILED ")})
    return passed + failed + errors, passed, failed + errors, node_ids

def main() -> int:
    wanted = set(sys.argv[1:]); restore()
    collected, passed, failed, _ = run_contract()
    print(f"  reference: {collected} collected, {passed} passed, {failed} failed")
    if (collected, failed) != (BASELINE_COLLECTED, 0):
        raise SystemExit("reference build is not clean — abort")
    survivors: list[str] = []
    for build in BUILDS:
        if wanted and build.name not in wanted: continue
        restore(); apply(build)
        collected, passed, failed, node_ids = run_contract()
        broken = "COLLECTION BROKEN" if collected != BASELINE_COLLECTED else ""
        verdict = "SURVIVES" if failed == 0 and collected == BASELINE_COLLECTED else "killed"
        if verdict == "SURVIVES": survivors.append(build.name)
        print(f"\n{build.name}: {verdict} {broken}\n  {build.description}")
        print(f"  {collected} collected, {passed} passed, {failed} failed")
        for nid in node_ids[:8]: print(f"    RED  {nid}")
        if len(node_ids) > 8: print(f"    ... and {len(node_ids)-8} more")
    restore(); print(f"\nSURVIVORS: {survivors or 'none'}")
    return 0
```

### 11.2 The three surviving patches, verbatim

```python
# WB93 — WB30's shape on the tools/list route. Two edits to server.py:
#   (a) DELETE the scoped manager's list_tools override entirely:
"    def list_tools(self) -> Any:\n"
"        tools = super().list_tools()\n"
"        if self._write_scoped():\n"
"            return tools\n"
"        return [tool for tool in tools if self._is_read_only(tool)]\n"   ->   ""
#   (b) install the filter as an instance attribute after `mcp._tool_manager = scoped_manager`:
#       (body pasted at §4.1)

# WB71 — host_is_loopback as a spelling set (lorerunes/posture.py)
'    lowered = host.strip().lower()\n'
'    if lowered == "localhost":\n        return True\n'
"    try:\n        return ipaddress.ip_address(lowered).is_loopback\n"
"    except ValueError:\n        return False\n"
    ->  '    return host.strip().lower() in {"localhost", "127.0.0.1", "::1"}\n'

# WB72 — the scoped list filters on `is not False` instead of `is not True` (server.py)
"        return [tool for tool in tools if self._is_read_only(tool)]\n"
    ->  "        return [\n            tool\n            for tool in tools\n"
        "            if getattr(tool, 'annotations', None) is None\n"
        "            or tool.annotations.readOnlyHint is not False\n        ]\n"

# WB74 — the extension annotation CLASS (server.py)
"_EXTENSION_TOOL_ANNOTATIONS = ToolAnnotations(\n"
"    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False\n)"
    ->  "_EXTENSION_TOOL_ANNOTATIONS = ToolAnnotations(\n"
        "    readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True\n)"
```

### 11.3 The WIRE `tools/list` probe — the instrument behind the blocker

Placed in the SCRATCH tree's test dir so it can import the contract's own fixtures. **This is
~5 lines away from being the N1 pin.**

```python
"""adv39-3 — the WIRE `tools/list` probe (WB93). NOT a contract pin; a scratch probe."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import pytest
from _auth_fixtures import (API_KEY_ENV_LAN_CLIENT, API_KEY_ENV_LOCAL_AGENT,
                            API_KEY_VALUE_LAN_CLIENT, API_KEY_VALUE_LOCAL_AGENT)

@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)

from _auth_fixtures import MCP_POST_HEADERS, bearer, drive, mcp_session_id, running_asgi_app
from test_auth_identity_seam import HOSTED_HOST, SESSION_HEADER, _TwoPrincipalEdge, post_mcp
from test_hosted_readonly_posture import EXPECTED_MUTATING_TOOLS

async def _wire_tools_list(app: Any, *, token: str) -> set[str]:
    opened = await post_mcp(app, token=token)
    assert opened.status == 200, f"initialize failed: {opened.status} {opened.body[:300]!r}"
    session = mcp_session_id(opened)
    hdrs = [(b"host", HOSTED_HOST), *MCP_POST_HEADERS, bearer(token),
            (SESSION_HEADER, session.encode())]
    await drive(app, method="POST", path="/mcp", headers=hdrs,
                body=b'{"jsonrpc":"2.0","method":"notifications/initialized"}')
    listed = await drive(app, method="POST", path="/mcp", headers=hdrs,
                         body=b'{"jsonrpc":"2.0","id":9,"method":"tools/list"}')
    text = listed.body.decode("utf-8", "replace")
    payload = text[text.index("{"):] if "{" in text else "{}"
    for line in text.splitlines():
        if line.startswith("data: "):
            payload = line[6:]; break
    return {t["name"] for t in json.loads(payload).get("result", {}).get("tools", [])}

async def test_PROBE_wire_tools_list_for_a_hosted_principal(tmp_path: Path) -> None:
    edge = _TwoPrincipalEdge(tmp_path)
    async with running_asgi_app(edge.app):
        over_the_wire = await _wire_tools_list(edge.app, token=edge.operator_token)
    leaked = over_the_wire & EXPECTED_MUTATING_TOOLS
    print(f"\n  WIRE tools/list : {len(over_the_wire)} tools; mutating leaked = {sorted(leaked)}")
    assert not leaked, (
        f"a hosted principal was OFFERED {sorted(leaked)} over the wire. The in-process "
        f"list_tools is filtered and the SERVED one is not — WB30's shape on the list route.")
```

### 11.4 The perturbed pins (P2) — ready to lift into the contract as N2 and N3

```python
@pytest.mark.parametrize("host", ["127.0.0.2", "127.0.1.1", "127.53.4.9"])
def test_PERTURBED_a_non_dot_one_loopback_bind_still_resolves(tmp_path: Path, host: str) -> None:
    from loremaster.config import LoreConfig, resolve_posture
    from lorerunes import Posture
    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["server"]["host"] = host
    payload["auth"] = hosted_auth_block(roster)
    assert resolve_posture(LoreConfig.model_validate(payload)) is Posture.HOSTED_OAUTH


async def test_PERTURBED_an_unannotated_tool_is_not_offered_to_a_hosted_principal(
    tmp_path: Path,
) -> None:
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server
    from test_hosted_readonly_posture import as_principal, google_principals
    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    mcp = build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))

    def _probe() -> str:
        """A newly contributed tool nobody has classified yet."""
        return "ok"

    mcp.add_tool(_probe, name="lore_probe_unannotated")
    with as_principal(google_principals("operator")):
        visible = {tool.name for tool in await mcp.list_tools()}
    assert "lore_probe_unannotated" not in visible, (
        "an UNANNOTATED tool was advertised to a hosted principal that cannot call it. "
        "R8's deny-by-default must govern the SERVED list, not only the lookup.")
```

### 11.5 The consequence prober and the runner

`adv39t_consequences.py` (§4.2/§4.3/§4.5 output) and `run_contract.sh` are short enough to
restate: the runner is `cd $ROOT && uv run pytest $CONTRACT "$@"` with `CONTRACT` verbatim from
`REPORT-contract-39-auth-1.md` §14.6; the prober prints `loremaster.__file__`, then walks
`resolve_posture` over six loopback spellings, registers an unannotated tool and reports whether
a hosted principal is *offered* it, and builds the server with and without an ambient principal
to compare the rendered refused clause. Its three probe bodies are reproduced inline at §4.2–4.5
alongside their output.

---

## 12. P1b — THE QUANTIFIER TABLE (every invariant; every guarded row with a receipt)

| # | Invariant | ∀-over-inputs or guarded? | Receipt |
|---|---|---|---|
| 1 | Every `(token, tokeninfo, roster)` triple → `None` or an admitted `AccessToken` | **∀** — every hostile field forced by its own fixture | WB87 (expired-from-cache) killed 2 red; the four `email_verified` shapes, missing `aud`, missing email, malformed JSON each have a forcing fixture |
| 2 | Every registered tool is classified, **over both registration paths** | **∀** — parametrised `[core-only, with-extension]` | WB77 (annotation grafted in `list_tools`) killed 4 red. ⚠ **N = 1 extension, 1 tool**; the annotation CLASS is unpinned (WB74 survives) |
| 3 | Every non-read-only tool is refused for every non-write principal | **∀** over the DERIVED registry × 2 google principals | CTRL88 (write-scope decision broken) killed 23 red |
| 4 | A refused tool's BODY never runs | **guarded — by the `Tool.run` BOUNDARY, not by "the body"** | ⚑ **Receipt: WB79c.** The ∀-over-registry pin **PASSED** while the body demonstrably ran (`assert not [1]` fired only on the single synthetic fixture). §4.4 → **N4** |
| 5 | A refused tool is not RETURNED by the lookup (R13 structural) | **∀** — SDK data dependency, read at source (`ToolManager.call_tool`) | WB75B (raw-`_tools` bypass) killed 23 red on variant B, where it is reachable |
| 6 | The hosted `list_tools` view equals the read ladder | ⚑ **guarded — by the IN-PROCESS entry point** | ⚑ **Receipt: WB93 SURVIVES 472/472**; the served `tools/list` returns 15 tools. **BLOCKER → N1** |
| 6b | …and deny-by-default governs that view | ⚑ **guarded — by "every tool is annotated"** | ⚑ **Receipt: WB72 SURVIVES 472/472**; an unannotated tool is advertised. **→ N2** |
| 7 | The served refused clause EQUALS the derivation, both directions | **∀** over `ALL_TOOL_NAMES` | the shipped `_READ_ONLY_ANNOTATIONS` mutation pin fires; WB50/WB50b (pass 2) both die here |
| 8 | The served read-ladder clause equals the readable set | **∀**, same instrument | as above |
| 9 | ∀ broken roster state × ∀ principal (warm and cold) ⇒ DENIED | **∀** — `BROKEN_ROSTER_SHAPES` × {cached, never-seen}, each with a healthy-roster positive control first | WB86 (keep-last-good) killed 17 red |
| 10 | Revocation is effective on the very next verification, cache hits included | **∀** over {uncached, cached-HIT, re-added, same-length edit} | the cache-HIT fixture asserts by transport call-count; no residual window |
| 11 | `host_is_loopback` fails closed on anything unparseable | ⚑ **guarded — by the SET OF SPELLINGS a classifier is certain to recognise** | ⚑ **Receipt: WB71 SURVIVES 472/472**; `127.0.0.2`/`127.0.1.1` refuse to boot. **→ N3** |
| 12 | The boot refusal reaches every boot site | **∀** over the three real entry points (`build_mcp_server`, `build_asgi_app`, `LoreServer.run`) | WB34/WB54 (pass 1) killed here; unchanged this pass |
| 13 | Distinct principals ⇒ distinct sessions (#206/F3) | **∀** over {google×google, google×api-key, key×key, anonymous} | pass-2 receipts; re-confirmed green on both reference builds |
| 14 | 401/400 negative-caches; 5xx/transport does NOT | **∀** over 4 transient statuses × 4 transport faults, distinguished by CALL COUNT | the P5 fake mutation reddens exactly these 9 — the pins are load-bearing on the count |
| 15 | ONE `EdgePolicy` feeds both enforcement points | **∀** — equality against `EdgePolicy.to_transport_security()` plus behavioural pins at both layers | pass-1 receipts; unchanged |
| 16 | A tool outside the resolver's permitted set is refused | ⚑ **guarded — the four refusal pins carry NO effect assertion** (design §9's WB48 law is stated contract-wide) | **Receipt: both door-builds died, but INCIDENTALLY.** WB70 killed by `test_the_injected_resolver_is_called_on_every_tool_dispatch` (the read tool errors without an `AppContext`, so the post-dispatch line never ran); WB70b killed by that pin plus the ORDER pin (N6). **Neither death was an effect assertion.** The pin that would kill it *on purpose*: give `test_a_tool_outside_the_resolved_permitted_set_is_refused` the `_run_entry_recorder` + a no-required-args synthetic tool, exactly as `TestARefusedToolNeverRUNS` does for the posture guard. |
| 17 | The credential never reaches a log or a URL | **∀** — caplog sweep over every record + the transport spy's full URL | unchanged; green on both reference builds |
| 18 | api-key principals retain the FULL surface | **∀** over 6 mutating tools × 2 key names, call AND list | WB76 (list keyed on posture) killed 1 red — `test_an_api_key_principal_sees_the_full_surface` |

**Five guarded rows. Three carry a SURVIVING wrong build (rows 4/6/6b/11 — four, counting 6b
separately). Row 16's two door-builds died for reasons adjacent to the property.**

---

## 13. Residuals — every one with an INDIVIDUAL verdict

| # | Residual | Verdict |
|---|---|---|
| R1 | The SDK's lowlevel `Server._tool_cache` is per-Server and **shared across principals**; a hosted principal's `tools/list` CLEARS it and repopulates with 9 entries, after which an api-key principal's `tools/call lore_remember` finds no cached definition and logs *"Tool 'lore_remember' not listed, no validation will be performed"* | **Not a security hole** — FastMCP registers `call_tool(validate_input=False)`, so the cache gates only OUTPUT validation, and lore's tools carry the same outputSchema regardless of caller. **Flagged, not pinned**: it becomes real the day anyone turns input validation on. Source: `mcp/server/lowlevel/server.py::_get_cached_tool_definition`. |
| R2 | `[::1]` bracketed and `127.0.0.2` are both named in R15's rider (`False` and `True` respectively); **neither is pinned** | `127.0.0.2` is **N3** (a real defect, WB71). `[::1]` is inert — treating a bracketed loopback as loopback is *more* permissive but still loopback, so no exposure. **Recommend pinning it anyway** as the cheap half of N3, since R15 names it. |
| R3 | `write_roster(..., header=False)` is never used by any pin | **Inert fixture parameter.** A factory affordance no test exercises; harmless, but it is decoration until something calls it. |
| R4 | `running_asgi_app`'s `LIFESPAN_TIMEOUT_S = 5.0` is exactly `LifespanManager`'s own default (`startup_timeout=5, shutdown_timeout=5`) | **Acceptable.** It is still a legitimate ONE-IMPLEMENTATION home for the policy; it simply restates the library default today. Worth a one-line docstring note so a future reader does not think 5 was measured. |
| R5 | The posture fixtures' Google tokens are ~146 characters; real Google access tokens are longer | **Inert** — nothing in the design or the reference build branches on token length (WB88 proved I could not exploit it). Recorded as a value monoculture in case a future length guard appears. |
| R6 | `test_mcp_server.py::_MUTATING_TOOLS` + `test_mutating_tools_are_not_marked_read_only` | **Live corpse; will NOT self-red.** Confirmed for the third consecutive pass: it is a subset check, so it stays green on a correct build and nothing forces its deletion. Handoff row 5 must be executed by hand. |
| R7 | `docs/plans/v2/39-hosted-security.md:31` names `tls_terminated_upstream` | **Stale prose after the build.** Not a gate; flag for the close-out sweep. |
| R8 | The design's §14 package table has **no row** for R13's scoped `ToolManager` | **Survey gap, right answer.** I measured `bespoke` is correct (SDK tool layer has zero scope awareness). §2 row 2. |
| R9 | Roster address-syntax validation was never surveyed against `email-validator` | **Escalate** — §2 row 9. Not installed, so I could not read its API; the two-sided rule says that is grounds to escalate for install authorization, never to assume either way. |
| R10 | The `hosted_server(with_extension=True)` fixture registers **one** extension contributing **one** tool | **Adequate for `readOnlyHint`** (WB77 dies), **insufficient for the annotation class** (WB74 survives). Folded into N7's ruling. |
| R11 | Finding **#294** — the lore MCP tools are unreachable from the `contract-adversary` toolset | **Fourth consecutive reproduction.** This is a defect in the agent DEFINITION. I also cannot file it via `lore_findings`, for the same reason — the lead must file it. |
| R12 | My P6b enumeration was **not** frame-independent (I read §8 first, unavoidably) | **Disclosed, not swallowed.** §8.2. Passes 1 and 2 did blind enumerations; if the lead wants a truly independent third, it needs a reader who is handed `auth.py` and nothing else. |
| R13 | The whole rest of the suite is **8166 passed / 5 failed** on the reference build | The 5 are the collateral set (§8.3). **There are no failing tests outside packet 39's blast radius.** |

---

## 14. What I did NOT find — so the SUFFICIENT half of this grade is legible

These are things I attacked and could not break, stated with how I tried:

- **R13's central structural claim is TRUE.** I read `ToolManager.call_tool` at source
  (`tool = self.get_tool(name); if not tool: raise; return await tool.run(...)`) and confirmed
  `FastMCP.call_tool`/`list_tools` read `self._tool_manager` at call time, so the manager is a
  single attribute every dispatch path shares. **Coverage as a checked variable — the dispatch
  entry points, enumerated:** (1) `FastMCP.call_tool` via the `CallToolRequest` handler ✔ scoped,
  pinned on the wire; (2) `FastMCP.list_tools` via `ListToolsRequest` ✔ scoped, **pinned only in
  process — N1**; (3) `ToolManager.call_tool` internal ✔ scoped by SDK data dependency;
  (4) `Server._get_cached_tool_definition` ✔ routes through (2) — R1; (5) `remove_tool`/`add_tool`
  — registration, not dispatch; (6) resources/prompts — **lore registers none** (grepped
  `add_resource`/`@mcp.resource`/`add_prompt`/`@mcp.prompt` in `server.py`: zero hits), so there
  is no other served dispatch surface; (7) stdio/SSE transports share the same `_mcp_server` and
  the same manager. **No path reaches a tool without the scoped lookup.** Placement genuinely
  stopped being a builder variable *for `tools/call`*.
- **The refusal-order / cross-principal / caching invariants held against everything I threw.**
  WB86, WB87, WB76, WB77, WB70, WB70b, WB75B, WB79B all died, several with double-digit red counts.
- **`running_asgi_app` is the real `asgi_lifespan.LifespanManager`** — verified by type identity
  and by its library-specific failure mode outside an async context. The pass-2 finding is closed.
- **The R14 `readOnlyHint` synthesis is properly pinned across both registration paths** — WB77's
  list-path graft dies on four pins by name.
- **The roster substrate is the strongest part of this contract.** Every fail-closed pin builds
  its own positive control before breaking anything, which is why the "resilience"-shaped fail-open
  (WB86) cannot hide.

---

## VERDICT

# CONTRACT INSUFFICIENT

One wrong build (**WB93**) passes all 472 pins while serving a hosted Google principal every
mutating tool over the real wire — WB30's shape, moved onto the `tools/list` route that R13
itself made load-bearing, with the correct-build control leg showing 9 tools and zero leaked.
Two further survivors (**WB71**, **WB72**) each have a proven perturbation pair. Six missing
pins are named in §6, four of them written out ready to lift; **N5** and **N6** are rulings the
design owes rather than tests the author can simply write.

The rest of the contract is strong, and this verdict should not be read as a rejection of it:
two independent correct builds discharge it at 472/0, the roster and cache groups killed every
door I could construct, and R13's structural claim about `tools/call` is true at source. The
gap is that R13 promoted a second served method to security-relevance and the contract pinned
it only where a test can see it.

*— adversary-39-auth-3, 2026-07-31, at `af74611`*
