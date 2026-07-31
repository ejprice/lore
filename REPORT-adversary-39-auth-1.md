# REPORT-adversary-39-auth-1 — packet 39 Google-OAuth CONTRACT, adversarially graded

brief-base v9 read

- **VERDICT: CONTRACT INSUFFICIENT.** 45 wrong builds constructed; **33 killed, 12 SURVIVED**
  with **422/422 pins green**. Nine distinct missing pins follow, each written out as
  runnable test code in §10 and each PAIRED (green on my correct reference build, red on
  its named wrong build).
- **P1 headline (the BLOCKER): `WB30` — the hosted read-only guard installed as an instance
  attribute after `FastMCP._setup_handlers` captured the bound `call_tool`.** All 422 pins
  green; the guard fires for `mcp.call_tool(...)` and **never runs on the served path**.
  Proved end-to-end with a paired wire probe (§4.1): a real Google principal, real verifier,
  real MCP session, `tools/call lore_remember` → correct build returns *"refused in the
  HOSTED_OAUTH posture"*; WB30 dispatches into the tool. **The entire §7 read-only posture is
  decorative in production and nothing in the contract can see it.**
- **Two more fail-OPEN survivors:** `WB34` — `build_mcp_server` swallowing `PostureConfigError`
  serves an internet-facing lore with **no auth at all** (the boot refusal is pinned only on
  `resolve_posture`, never on the thing that boots). `WB33` — `host_is_loopback` hardcoded True
  admits `HOSTED_OAUTH` on a `0.0.0.0` bind (every loremaster fixture uses `127.0.0.1`: a
  parameter-value monoculture on `server.host`).
- **A survivor that breaks the EXISTING deployment:** `WB28` — `EdgePolicy.allowed_hosts`
  ignoring the configured bind host. Design §5 rules `LAN_BEARER` legal on a NON-loopback bind
  and the contract asserts it; no `derive_edge_policy` pin ever uses one, so the W7 421-trap
  the packet exists to catch is wide open one posture over.
- **SATISFIABILITY RECEIPT — DISCHARGED.** Reference build → **422 passed / 0 failed**,
  `uv run ruff check .` → **All checks passed!**, including the post-cleanup leg (§3).
  `loremaster.__file__ = /home/ejprice/scratch/adv39/loremaster/loremaster/__init__.py`.
  Both pins the author flagged as possibly unsatisfiable are satisfiable, and their
  re-aimed mutual-satisfiability question (§9 item 7) resolves YES.
- **P4:** the author's 33-GREEN enumeration reproduces EXACTLY, item for item (§7.1).
  Baseline 389 RED / 33 GREEN / 422 collected reproduces at HEAD `b5730f3`.
- **P6 corpse sweep:** the author's §8 "exact edits outside my writable set" list is
  **INCOMPLETE by 3 sites** — proven by running the reference build against the rest of the
  suite: 4 collateral reds, only 1 of them listed (§8).
- **P-PKG diff (§2):** one `bespoke` verdict — `google-auth` — has an EMPTY read column on
  **both** sides. Neither the author nor I read it. One command settles it; escalated.
- **Concurrent repo edit noticed:** HEAD moved 6e9e845 → **b5730f3** mid-run and
  `test_auth_composition.py` gained a prose-only row-14→row-15 fix. Behaviourally inert;
  re-verified (§7.2).
- **⚠ Tool honesty:** the lore MCP tools are **absent from my toolset** (finding #294
  reproduces). Every structural claim here rests on bare anchor-free `grep` + `Read`, said
  out loud. §1.
- Receipts: §2 P-PKG · §3 satisfiability · §4 wrong builds · §5 P1b quantifier table ·
  §6 P2 perturbations · §7 P4 · §8 P6/P6b · §9 residuals · §10 the pins, as code.

---

## 1. Capability check (brief-base §4 — first thing in the report)

| Demanded | What I have | What I did instead | What a lead must change |
|---|---|---|---|
| `ToolSearch "select:mcp__lore_lore__lore_search,…"` — lore-first for structure | **The lore MCP tools are NOT in my toolset.** The brief's exact select-list returned `No matching deferred tools found`; a keyword query (`lore search code symbol impact`) also returned nothing. | **Bare, anchor-free `grep` + `Read` for every structural question** — the SDK, `auth.py`, `server.py`, `config.py`, the six `ToolAnnotations` constants, the corpse sweep. Said out loud per the dogfood protocol. | The `contract-adversary` agent definition needs the lore tools. This is the SECOND independent reproduction of finding **#294** in this packet (the contract author reported the same absence, §1 of `REPORT-contract-39-auth-1.md`). Two agents, same wave, same crippling. |
| `lore_findings action=report` for friction | Not reachable (same cause). | Recorded here for the lead to file. | — |
| Everything else (Write/Bash/Read/Grep, `scratch_copy.sh`, the venv) | Available. | — | — |

**Consequence:** my P6 corpse sweep and the deleted-code enumeration in §8 rest on greps, not
on `lore_impact`. I ran each with **no prefix and no call-paren anchor** and give `file:line`
plus an individual verdict per hit — no "the rest are fine".

**A second honesty note, on P6b specifically.** The role spec requires the deleted-code
enumeration to happen *before* reading the Phase-0 inventory. **I could not honour that
ordering**: the inventory is §8 of the design doc, and the design doc is the spec I was
briefed to read. I read it first. §8.2 therefore reports a *contaminated* diff, and I say so
there rather than claiming an independence I did not have. What I could still do — and did —
is run the reference build against the rest of the suite and let the FAILURES enumerate the
consumers empirically, which is an instrument the frame cannot bias.

---

## 2. P-PKG — my own survey, built first, then diffed against the author's

Every row's read column names an installed file I opened or a value I executed, never an
expectation. Rows are ordered mechanism-first.

| # | Mechanism the contract specifies | Library | What I **READ / RAN** | My verdict |
|---|---|---|---|---|
| 1 | Token-verifier protocol · session identity · 401 challenge · RFC 9728 discovery | `mcp` **1.27.2** (`importlib.metadata.version` → `1.27.2`) | `server/auth/provider.py`; `server/auth/middleware/bearer_auth.py` **in full** — `authorization_context()` returns exactly `(client_id, claims["iss"], subject)`, and `BearerAuthBackend.authenticate` *also* rejects on `auth_info.expires_at < int(time.time())`; `RequireAuthMiddleware.__call__` (401 `invalid_token`, 403 `insufficient_scope`) and `_send_auth_error` (`resource_metadata=` behind `# pragma: no cover`); `server/auth/settings.py`; `server/auth/routes.py::build_resource_metadata_url` + `create_protected_resource_routes`; `server/fastmcp/server.py` lines 147–239 and 950–1043 | **replace** |
| 2 | Host/Origin DNS-rebinding validation | `mcp.server.transport_security` | `TransportSecuritySettings` + `TransportSecurityMiddleware._validate_host` / `_validate_origin` **in full**. ⚠ **The fact that shapes the whole EdgePolicy and is in NEITHER of the author's rows:** a `"h:*"` entry matches only when the presented Host **contains a colon** (`host.startswith(base + ":")`). A policy that emits only `:*` forms therefore **421s a port-less Host** — which is exactly what a reverse proxy forwards. Both the bare hostname and the `:*` form are required. | **replace_with_adapter** |
| 3 | TTL positive/negative caches | `cachetools` **7.1.6** — **INSTALLED** (`cachetools.__version__` executed in the scratch venv) | `TTLCache`; used it in the reference build for both caches | **replace** (author's B1 is RESOLVED — verified, not relayed) |
| 4 | Outbound HTTP + hermetic double | `httpx` **0.28.1** | `MockTransport` async-handler support; `AsyncClient.is_closed`; `Timeout`; `Limits` | **keep** |
| 5 | Google **access**-token introspection | `google-auth` | **NOTHING. It is not installed (`importlib.util.find_spec("google")` → `None`) and I did not read it.** I inherit the claim exactly as the author does. | **bespoke — read column EMPTY on both sides. ESCALATED (§9-E1).** |
| 6 | Email normalisation (NFKC → casefold → strip) | `email-validator`; stdlib `unicodedata` | `lorerunes/pyproject.toml` (`dependencies = []`, stdlib-only by workspace law); executed `unicodedata.normalize("NFKC", "İSTANBUL@x.com").casefold()` to confirm the ruled order is a **one-line** stdlib call | **bespoke** — and the reference build shows the "gap" costs one line, so the workspace constraint is free |
| 7 | ⚑ **Email SYNTAX validation for the roster (R7)** — a mechanism NEITHER table carries as its own row | stdlib `email.utils.parseaddr`; `email-validator` | **Executed `parseaddr` on all five R7 malformed shapes.** It accepts a bare domain (`'firehawktransam.org'` → `('', 'firehawktransam.org')`) and, worse, **strips the whitespace out of the forged fixture line**, turning `` "``` admin@evil.example  event=… ok ```" `` into a single "address". It cannot supply R7's refusal semantics. `email-validator` is not installed and is barred by the stdlib-only rule anyway. | **bespoke** — same verdict the author reached, now with the read receipt the row lacked |
| 8 | Roster change detection | `watchdog` **6.0.0** | Its observer model (thread + queue per watched **tree**) | **bespoke, minimal** |
| 9 | Running an ASGI **lifespan** in a test | `asgi-lifespan`; `httpx.ASGITransport` | Not installed; `httpx/_transports/asgi.py` carries no lifespan handling. **But I executed the author's 30-line `running_asgi_app` against the real session manager: 16/16 identity-seam pins green.** | **keep_with_trigger** (I DISAGREE mildly with the author's `escalate for install`: the stand-in is proven, so the trigger is "the first pin needing lifespan STATE the stand-in does not model") |
| 10 | ⚑ Host allow-listing as an OUTER middleware — a row neither table carries | `starlette.middleware.trustedhost.TrustedHostMiddleware` | **Read `__call__` in full.** It does `host = headers.get("host","").split(":")[0]` — it **discards the port**, so it cannot express the `:*`/exact distinction the SDK's layer needs — and it answers **400**, not the 421 the contract pins. It also sits OUTSIDE the transport, where the SDK's own check would still run. | **correctly NOT used** — the SDK layer is the right instrument |
| 11 | ⚑ Origin enforcement — a row neither table carries | `starlette.middleware.cors.CORSMiddleware` | **Read `__call__` in full.** A disallowed Origin does **not** stop the request: `simple_response` still calls the wrapped app and merely omits the CORS headers. It therefore **cannot** provide design §6's load-bearing property (*403 before any credential is parsed, zero outbound Google calls*). | **keep the hand-rolled `OriginValidationMiddleware`** — correct, and now with a reason instead of an assumption |

### The DIFF against `REPORT-contract-39-auth-1.md` §2

| Row | Author | Me | Disposition |
|---|---|---|---|
| `mcp` SDK | replace | replace | **agree** |
| `transport_security` | replace_with_adapter | replace_with_adapter | **agree on the verdict; my read column adds the load-bearing `:*`-needs-a-colon fact** the EdgePolicy shape depends on |
| `cachetools` | "replace, **BLOCKED on install**" | replace — **verified installed at 7.1.6 and exercised** | **resolved**; design §15-B1 stands |
| `httpx` | keep | keep | **agree** |
| `google-auth` | bespoke, "claim INHERITED not verified" | bespoke, **I did not read it either** | ⚠ **the one empty read column in the packet, on BOTH sides.** §9-E1 |
| `email-validator` | bespoke, forced by workspace law | bespoke | **agree** |
| `watchdog` | bespoke, minimal | bespoke, minimal | **agree** |
| `asgi-lifespan` | escalate for install | **keep_with_trigger** (the stand-in is proven by execution) | **mild disagreement, lead's call — not a defect either way** |
| `httpx.ASGITransport` | keep_with_trigger | keep_with_trigger | **agree** |
| **email SYNTAX validation** | folded into normalisation, no read | **own row, `parseaddr` executed** | **gap in the author's table, same verdict** |
| **TrustedHostMiddleware** | absent | own row, source read | **gap in both; verdict unchanged** |
| **CORSMiddleware** | absent | own row, source read | **gap in both; verdict unchanged** |

**No mechanism the contract specifies is one a library already provides.** The three rows
neither table carried all confirm the bespoke/keep choices rather than overturning them.

---

## 3. THE SATISFIABILITY RECEIPT (repo law — a contract ships with one)

I built the full reference implementation, because grading the contract required it.

**Scratch provenance (standing law — print the file, or the verdict names no tree):**

```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch/adv39
scratch copy READY: /home/ejprice/scratch/adv39
  loremaster  -> /home/ejprice/scratch/adv39/loremaster/loremaster/__init__.py
  loresigil   -> /home/ejprice/scratch/adv39/loresigil/loresigil/__init__.py
  lorescribe  -> /home/ejprice/scratch/adv39/lorescribe/lorescribe/__init__.py
  lorerunes   -> /home/ejprice/scratch/adv39/lorerunes/lorerunes/__init__.py

$ ./scripts/scratch_copy.sh --verify-only /home/ejprice/scratch/adv39   # re-run at close-out
scratch copy VERIFIED: /home/ejprice/scratch/adv39
```

**Leg 1 — 0-failed against the correct build** (contract files copied byte-exact from HEAD
`b5730f3`, including the concurrent prose fix of §7.2):

```
$ cd /home/ejprice/scratch/adv39 && uv run pytest <the 7 loremaster contract modules> lorerunes/tests -q -p no:randomly
422 passed in 9.58s
loremaster.__file__ = /home/ejprice/scratch/adv39/loremaster/loremaster/__init__.py
lorerunes.__file__  = /home/ejprice/scratch/adv39/lorerunes/lorerunes/__init__.py
```

**Leg 2 — the HARDER leg: still 0-failed AFTER the cleanups ruff demands.** Deleting
`BearerAuthMiddleware`/`AuthVerifier` forces `from abc import ABC, abstractmethod` out; my
first-cut build then tripped 21 ruff errors (13 × `E402`, 4 × `I001`, 1 × `F401`
(`dataclasses`), 1 × `PLR2004`, 2 × `PLR0911`). After the full cleanup — imports hoisted,
orphan deleted, the magic `200` constant-ised, and **`verify_token` factored twice to get
under `PLR0911`'s 6-return ceiling**:

```
$ uv run ruff check .
All checks passed!
$ uv run pytest <the same set> -q -p no:randomly
422 passed in 9.23s
```

⚠ **One friction the builder WILL hit, named so it is met deliberately:** the surface the
contract demands drives `LoreTokenVerifier.verify_token` to **7 return statements**, one over
the repo's live `PLR0911` ceiling. It is satisfiable (I factored `_api_key_principal` and
`_google_verdict` out), but a builder who writes the obvious straight-line version gets a
lint failure that looks like a contract problem and is not.

**The two pins the author was least confident about (§9 item 6) — both SATISFIABLE:**
`test_an_unchanged_roster_is_not_re_read` (chmod-with-mtime-untouched) and
`test_an_expired_token_is_not_served_from_the_positive_cache` (2.5 s real sleep) both pass
in the 422. **Their re-aimed mutual-satisfiability question (§9 item 7) resolves YES:**
`test_an_unchanged_roster_is_not_re_read` and `test_an_unreadable_roster_denies_everyone` are
green in the SAME run — the distinguishing input really is the mtime, and a signature of
`(st_mtime_ns, st_size, st_ino)` satisfies both. **No contract defect there.**

---

## 4. P1 — 45 wrong builds. 33 killed, 12 SURVIVED.

Harness: `/home/ejprice/scratch/adv39_wrong_builds.py` (mechanism pasted verbatim in §10.1;
every survivor's patch pasted verbatim in §10.2). It restores the reference build byte-exact,
applies ONE mutation, runs the REAL contract, and carries the two guards this repo has
receipts for: **an anchor that does not match exactly once is a hard error** (a patch that
silently fails to land grades the correct build and reads as a survivor), and **every run's
COLLECTED total is compared to the baseline's** (a syntax break collects nothing and prints
`1 error`, which a failure count reads as "killed"). `not_comparable = 0` on all three batches.

```
BASELINE (reference build): 422 passed, 0 failed, 422 collected
```

### 4.0 The killed 33 — each with the pin that killed it

| # | Wrong build | first killer |
|---|---|---|
| WB01 | F3 verbatim odoo-code port: no `subject`, no `claims` | `test_google_token_verifier::…::test_a_listed_verified_principal_is_admitted` (25 pins) |
| WB02 | **F3 false clear** — `subject` from a CONSTANT (the client id) | `TestIdentityMinting::test_the_google_subject_comes_from_the_sub_claim` (4) |
| WB03 | F3 partial — `claims` set, `subject` unset | (25) |
| WB04a | **F4** in the shared predicate (`if not roster: return True`) | `lorerunes…::test_an_empty_roster_denies_every_principal` (1) |
| WB04b | **F4 at odoo-code's exact CALL SITE** (`if roster and not is_admitted(...)`) | `test_a_roster_that_goes_empty_denies_a_cached_principal_immediately` (17) |
| WB05 | silently-shorter roster (skip the malformed line) | `test_every_principal_is_denied_when_the_roster_is_broken[parse-refused]` (20) |
| WB06 | **401-vs-5xx collapse** (negative-cache any non-200) | `test_a_transient_upstream_failure_is_NOT_cached[ise]` (5) |
| WB07 | transport fault negative-cached too | `test_a_transport_fault_is_NOT_cached[connect-timeout]` (4) |
| WB08 | `email_verified` any-truthy | `test_falsy_and_absent_shapes_are_denied[str-false]` (2) |
| WB09 | `readOnlyHint == False` instead of `is not True` | `test_a_tool_registered_with_no_annotations_is_born_refused` (1) |
| WB10 | read-only guard reads a HAND-LIST of tool names | `test_a_tool_registered_with_no_annotations_is_born_refused` (1) |
| WB11 | **scope check TOO STRICT** — the design's own literal wording | (64) |
| WB12 | scope check TOO LOOSE (substring) | `test_a_scope_merely_containing_the_word_email_is_not_enough` (1) |
| WB13 | **S5 re-opened** — roster stat on the cache-MISS path only | `test_re_adding_a_principal_re_admits_them` (12) |
| WB14 | revocation "fixed" by FLUSHING the token cache | `test_a_revoked_principal_with_a_cached_token_is_denied_immediately` (4) |
| WB15 | roster re-READ on every verification | `test_an_unchanged_roster_is_not_re_read` (1) |
| WB16 | **`transport_security` left unset (the 421 trap)** | `test_the_composed_server_uses_the_derived_transport_security_settings` (9) |
| WB17 | TWO Origin policies (claude origins outer-only) | `test_the_claude_origin_passes_BOTH_origin_layers` (1) |
| WB18 | **expiry unit swap** (`expires_in` as absolute) | (65) |
| WB19 | `aud` skipped when ABSENT | `test_a_missing_aud_is_a_hard_reject_not_a_skipped_check` (1) |
| WB20 | api-key compare re-implemented inline | `test_the_api_key_branch_routes_through_ApiKeyVerifier` (1) |
| WB21 | token in the URL query string | (45) |
| WB22 | Origin guard narrowed to `/mcp` | `test_the_discovery_route_is_also_origin_guarded` (1) |
| WB23 | resolver consulted, output DISCARDED | `test_a_tool_outside_the_resolved_permitted_set_is_refused` (3) |
| WB24 | empty `permitted` read as falsy | `test_an_empty_permitted_set_permits_NOTHING` (1) |
| WB25 | guard keyed on `client_id.startswith("api_key:")` | `test_a_write_scope_is_what_permits_not_the_client_id_shape` (1) |
| WB26 | `.well-known` served in every non-loopback posture | `test_the_well_known_document_is_absent_in_lan_bearer_posture` (1) |
| WB27 | `HOSTED_OAUTH` accepted on a non-loopback bind (at the pure function) | `test_every_input_combination_matches_the_spec_table[False-True-google_oauth-False-True]` (8) |
| WB32 | api-key branch checked AFTER Google | `test_a_valid_api_key_is_admitted_without_any_outbound_call` (4) |
| WB43 | api-key branch skipped when google is configured | (7) |
| WB44 | **Google branch mints WRITE scope** | (24) |
| WB46 | roster ERROR dumps every principal's address | `test_a_forged_roster_line_cannot_be_read_as_a_log_event` (2) |
| WB47 | positive cache MODULE-GLOBAL again | `test_caches_are_per_instance_not_module_global` (1) |

**This is a strong contract on everything it aimed at.** Every one of the seven wrong builds
the brief told me to attack first was killed, most by several independent pins, and the two
"false clear" variants of F3 (WB02/WB03) died at BOTH the unit and assembled-app layers.

### 4.1 ⚑ SURVIVOR `WB30` — THE BLOCKER, with its paired control

**The mutation:** the dispatch guard is not on `TracingFastMCP.call_tool`; it is installed
after construction as `mcp.call_tool = _guarded`. `FastMCP.__init__` calls `_setup_handlers`,
which registers **the bound method** — `self._mcp_server.call_tool(validate_input=False)(self.call_tool)`
(SDK `server/fastmcp/server.py:308`) — so the lowlevel/WIRE path keeps calling the ORIGINAL,
unguarded one while `mcp.call_tool(...)` in a test is guarded.

**Contract verdict: 422 passed, 0 failed.** Every one of the 55 `test_hosted_readonly_posture`
pins is green, because every one of them calls `mcp.call_tool(...)` directly.

**The paired wire probe** (`adv39_wire_probe.py`, §10.3 verbatim) drives a real hosted MCP
session — real `LoreTokenVerifier`, real Google token through the real tokeninfo spy, real
`initialize` + `notifications/initialized` + `tools/call` over the assembled ASGI app:

```
# LEG 1 — correct reference build
loremaster.__file__ = /home/ejprice/scratch/adv39/loremaster/loremaster/__init__.py
status=200
body={"jsonrpc":"2.0","id":9,"result":{"content":[{"type":"text","text":"lore_remember is refused
  in the HOSTED_OAUTH posture: it can write, and this principal holds read scope only. The read
  surface remains available: lore_dead_code, lore_diff, …"}],"isError":true}}
VERDICT: the hosted read-only guard FIRED on the wire path

# LEG 2 — WB30 applied (all 422 contract pins still green)
loremaster.__file__ = /home/ejprice/scratch/adv39/loremaster/loremaster/__init__.py
status=200
body={"jsonrpc":"2.0","id":9,"result":{"content":[{"type":"text","text":"Error executing tool
  lore_remember: 1 validation error for rememberArguments\ntext\n  Field required …"}],"isError":true}}
VERDICT: the hosted read-only guard *** DID NOT FIRE on the wire path ***
```

The WB30 body is `lore_remember`'s own **argument validation** — the guard never ran and the
tool was dispatched. This is CLAUDE.md's own law, verbatim: *"a runtime gate is an invariant
only over code it actually RUNS — so check coverage as a variable."* The contract checks the
gate; it never checks its reach.

### 4.2 The other eleven survivors, each with an individual verdict

| # | Survivor | Production consequence | Verdict |
|---|---|---|---|
| **WB34** | `build_mcp_server` catches `PostureConfigError` → falls back to `LOOPBACK` | An incoherent config, or a roster that fails to load at boot, yields a server with **NO auth wired at all**. If lore-caddy is already pointed at it, that is an **unauthenticated internet-facing lore**. R11/R12 say "refuse to BOOT"; the pinned instrument is `resolve_posture`, a function that is not what boots. | **MISSING PIN M2 — BLOCKER (fail-OPEN)** |
| **WB33** | `resolve_posture` hardcodes `host_is_loopback=True` | `HOSTED_OAUTH` boots on a `0.0.0.0` bind — lore itself listening on the whole LAN/world instead of behind lore-caddy on loopback (design R4 / investigation M-2: *"instant whole-LAN exposure"*). `lorerunes` pins `derive_posture(host_is_loopback=False)` → refusal, but **nothing pins the MAPPING** from `config.server.host` to that boolean, and every loremaster fixture uses `127.0.0.1`. | **MISSING PIN M3 — BLOCKER-adjacent; a textbook parameter-value monoculture** |
| **WB28** | `EdgePolicy.allowed_hosts` ignores `config.server.host` | `LAN_BEARER` is explicitly legal on a non-loopback bind (`lorerunes…::test_todays_enabled_api_key_config_is_lan_bearer` asserts it for `host_is_loopback=False`). With rebinding protection ON and `allowed_hosts` hardcoded to loopback, **every LAN request is answered 421** — the exact W7 trap, one posture over, on the deployment shape that exists TODAY. Invisible because every EdgePolicy fixture binds loopback. | **MISSING PIN M4 — BLOCKER-adjacent** |
| **WB42 / WB42b** | the raw token logged on the **ADMITTED** path (labelled and unlabelled) | Design §8 row 5's property is *"the presented credential value is NEVER logged"*; the pin drives **only a 401**. Quantifier law, verbatim. I measured lore's own scrubber: `token=<v>` IS redacted, but **`_scrub_text('admitted ya29.a0AfSECRET')` returns it unchanged** (the scrubber matches only LABELLED shapes, by design). So the unlabelled shape puts a live Google access token in the container log on every successful hosted verification. | **MISSING PIN M5 — HIGH** |
| **WB41** | roster change detection keyed on `st_size` only | An operator swapping one principal for another of the same byte length is not detected — the departed principal keeps access indefinitely. **Every shipped revocation fixture changes the file's LENGTH**, so nothing can see it. | **MISSING PIN M6 — MODERATE** |
| **WB40** | the hosted-instructions refused-set section is a HAND-LIST | Design §7 says the section is *"GENERATED from the registered annotations (never prose beside them)"*. `test_every_refused_tool_is_named_inside_that_section` compares the section against `EXPECTED_MUTATING_TOOLS` — the same hand list the wrong build hardcodes, so the pin is a tautology. The day a tool is added, the served instructions teach a stale refused set. This is the exact class CLAUDE.md's "A DIAGNOSIS IS NOT AN INSTRUMENT" section was written for. | **MISSING PIN M7 — MODERATE (served-surface honesty / trust doctrine)** |
| **WB35** | the `LOOPBACK` edge policy also carries the claude.ai origins | `LOOPBACK` installs NO auth. Trusting `https://claude.ai` there means a page served from that origin can reach an unauthenticated local lore. `derive_edge_policy` is never asserted for `LOOPBACK` by any pin. | **MISSING PIN M8 — LOW-MODERATE** |
| **WB45** | `AuthSettings.required_scopes = []` | Behaviourally equivalent **today** (every minted token carries `lore:read`), but it silently deletes the SDK's scope enforcement — a defence-in-depth layer that only matters the day a verifier branch mints a scopeless token. Design §6 names the value; nothing asserts it. | **MISSING PIN M9 — LOW (cheap; I wrote and paired it)** |
| **WB31** | the token-cache key is a **truncated** sha512 (first 8 hex chars) | Design §4 rules *"SHA-512 of the token as the only cache key"*. Truncation gives a 32-bit key: a token colliding with a previously-rejected one is denied without asking Google. `test_a_token_that_is_a_prefix_of_a_cached_token_is_not_admitted` pins a token PREFIX, not the digest LENGTH, so it cannot see this. | **RESIDUAL R1 — real ruling violation, no cheap BEHAVIOURAL pin exists** (a collision is not constructible without a preimage). Honest options: a structural pin that the key expression is a full `hexdigest()`, or accept-and-ledger with a named re-open trigger. **Operator/lead call, not mine.** |
| **WB29** | the last-known-good roster is kept in memory when the file disappears | The mutation removes only the in-memory invalidation; the `OSError` arm still returns `None`, so every principal is still denied. A restored file gets a new inode/mtime, so the stale set can never be served. | **RESIDUAL R2 — BEHAVIOURALLY EQUIVALENT. Not a finding, and I will not contort a pin to detect a difference with no observable consequence.** |

---

## 5. P1b — THE QUANTIFIER TABLE (every invariant, every guarded row with a receipt)

| # | Invariant | ∀-over-inputs or GUARDED? | Receipt |
|---|---|---|---|
| A | **Auth ∀** — every `(token, tokeninfo-response, allowlist)` → `None` or a complete, allowlist-consistent `AccessToken` | **∀-over-outcomes**, enforced by `assert_verification_outcome_is_total` on every verification in `test_google_token_verifier` | Door-builds attempted through 8 independently hostile fields (WB08/11/12/18/19/44 + malformed/degenerate) — **all killed**. ⚠ narrow bound: the helper is applied via `_VerifierProbe`, so the 43 pins in `test_allowlist_roster` (which call `verify_token` directly) are outside it. Not exploited by any build I could construct. |
| B | **Posture ∀** — every registered tool classified; every non-read-only tool refused for every non-write principal | **GUARDED — by the ENTRY POINT.** The universal is over tools and principals but not over *call paths*; every pin uses `mcp.call_tool(...)` | ⚑ **BLOCKER receipt: `WB30` survives 422/422**, and the paired wire probe (§4.1) shows a real hosted principal dispatching `lore_remember` over the served path. → **M1** |
| C | **Roster fail-closed ∀** — whenever the roster is not a loadable file with ≥1 valid entry, EVERY principal is denied, whatever made it unloadable | **∀-over-principals × 6 broken states × both cache paths** — genuinely universal over CAUSES, as the module docstring claims | WB04a/WB04b/WB05 all killed; WB46 killed. Door-build WB29 survives but is **behaviourally equivalent** (§4.2). |
| D | **Revocation immediacy (S5)** — a revoked principal is denied on the FIRST verification after the edit, cache hits included | **GUARDED — by the CHANGE-DETECTION SIGNAL.** Quantified over principals and cache states; silent about *what change the build watches* | WB13/WB14/WB15 killed. ⚑ **`WB41` survives**: every revocation fixture changes the file LENGTH, so a size-keyed build is indistinguishable. → **M6** |
| E | **Identity distinctness (F3)** | **∀ over 4 ordered principal pairs, through the ASSEMBLED app** | WB01/WB02/WB03 all killed at two layers each. Strongest property in the contract. |
| F | **Hosted principals cannot write** | **GUARDED — pinned as TWO HALVES that are never composed.** Half 1: the verifier mints `[lore:read]` (unit). Half 2: the guard refuses non-write (synthetic `AccessToken` injected into the contextvar). No pin drives a real Google token through the real app to a mutating tool. | WB44 killed (half 1). ⚑ **`WB30` survives** by breaking the *join* (§4.1). → **M1** |
| G | **One EdgePolicy derivation feeds both layers (R9)** | **GUARDED — by the BIND HOST and the POSTURE.** Equality + behavioural pins exist, but only for `127.0.0.1` binds and only for `HOSTED`/`LAN_BEARER` | WB16/WB17 killed. ⚑ **`WB28` survives** (bind host ignored) and ⚑ **`WB35` survives** (`LOOPBACK` never asserted). → **M4, M8** |
| H | **Boot refuses an unloadable roster / an incoherent posture (R11/R12)** | **GUARDED — by the SEAM.** Asserted only on `resolve_posture`, never on `build_mcp_server`/`build_asgi_app` | ⚑ **`WB34` survives** — the refusal never reaching the thing that boots is a fail-OPEN. → **M2** |
| I | **The loopback claim** — `HOSTED_OAUTH` requires a loopback bind | **GUARDED — by a fixture MONOCULTURE.** The pure function is pinned over all 48 cross-product points; the config→primitives mapping is pinned only at `server.host == "127.0.0.1"` | WB27 killed at the pure function. ⚑ **`WB33` survives** at the mapping. → **M3** |
| J | **The presented credential is never logged** | **GUARDED — by the FAILURE PATH.** `test_the_raw_token_never_appears_in_a_log_record` drives only a 401 | ⚑ **`WB42` and `WB42b` both survive**; scrubber probe shows the unlabelled shape reaches the log verbatim. → **M5** |
| K | **The token travels in the BODY, never the URL** | **∀ over the recorded request** | WB21 killed by 45 pins. |
| L | **Every roster INPUT LINE has exactly one fate** | **∀-over-lines**, all three fates fixture-FORCED, anti-vacuity guard on the helper | WB05 killed; merge fate forced by a 2-in-1-out fixture. Exemplary. |
| M | **ONE normaliser, both sides of the seam** | **∀ at the seam** (capitalised roster line vs lowercase Google email, driven through the verifier) | No door-build found. The mutation proof (change the normaliser ⇒ both members redden) is owed by the BUILDER, per §10 of the author's report — not discharged here and not discharged by them. |
| N | **The refusal is a structured `ToolError`, distinguishable from a permission filter** | **∀ over both refusal types** | WB23/WB24/WB25 killed. |
| O | **`required_scopes` is the ruled value** | **UNPINNED entirely** | ⚑ **`WB45` survives.** → **M9** |
| P | **The served instructions match the served behaviour** | **GUARDED — by comparing a hand list to a hand list** | ⚑ **`WB40` survives.** → **M7** |
| Q | **The cache key is the whole token's SHA-512** | **GUARDED — a token-PREFIX pin, not a digest-LENGTH pin** | ⚑ **`WB31` survives** — no cheap behavioural pin exists. → **R1** |

**Nine of seventeen invariants are guarded rather than universal, and eight of those nine
carry a surviving door-build.** That is the verdict.

---

## 6. P2 — fixture perturbation, with the correct-build control leg on every row

The role spec forbids reporting a perturbation without proving the pair. Every proposed pin
in §10.4 was run BOTH ways. Perturbations live in a scratch COPY
(`/home/ejprice/scratch/adv39/loremaster/tests/test_adv39_missing_pins.py`), never the repo.

```
$ uv run pytest loremaster/tests/test_adv39_missing_pins.py -q -p no:randomly     # CORRECT build
14 passed in 1.81s
```

| Perturbation of a load-bearing fixture | Wrong build it exposes | RED on the wrong build | GREEN on the correct build |
|---|---|---|---|
| `caplog` sweep moved from the **401** path to the **ADMITTED** path | WB42b | `1 failed` | ✅ (included in the 14) |
| roster edit made **byte-length-preserving** (`dana.whitfield@pricepaper.com` → `…@pricepaper.net`) | WB41 | `1 failed` | ✅ |
| boot refusal asserted at `build_mcp_server` instead of `resolve_posture` | WB34 | `1 failed, 1 passed` (the control leg held) | ✅ |
| `server.host` moved off the `127.0.0.1` monoculture — 3 non-loopback + 3 loopback spellings | WB33 | `3 failed, 3 passed` (loopback control held) | ✅ |
| `derive_edge_policy` driven with a **non-loopback** bind | WB28 | `1 failed` | ✅ |
| `derive_edge_policy` asserted for the **LOOPBACK** posture | WB35 | `1 failed` | ✅ |
| instructions section checked after registering a **NEW** mutating tool | WB40 | `1 failed` | ✅ |
| `mcp.settings.auth.required_scopes` asserted | WB45 | `1 failed` | ✅ |

### Fixture-discrimination verdicts (every load-bearing fixture, individually)

| Fixture | Can it tell right from wrong? |
|---|---|
| `roster_of_two` (two entries, never one) | ✅ **Discriminates.** N=2 deliberately; `test_the_second_listed_principal_is_also_admitted` kills a build that closed over the first address. |
| `tokeninfo_payload` — nothing branched-on is defaulted, `exp`/`expires_in` both emitted as **strings** | ✅ **Best fixture in the contract.** It is what makes WB18 (65 kills) and WB08 catchable at all. |
| `admitted_payload` defaults `email`/`sub` | ✅ **Correct** — those are identity, not branch conditions, and the author says so. |
| `google_access_token` — `ya29.`-prefixed, ~200 chars, unique per call | ✅ Discriminates (WB21, WB31's prefix cousin, the cache-poisoning pins). |
| `EXPECTED_MUTATING_TOOLS` vs the DERIVED set, asserted **EQUAL** | ✅ **Discriminates** — equality, not the subset check #291's pin used. WB09/WB10 both die on it. |
| `EXPECTED_READ_ONLY_TOOLS` (the control set) | ✅ Kills the refuse-everything build. |
| `base_config_payload` — `server.host` **always `127.0.0.1`** | ❌ **DOES NOT DISCRIMINATE.** The monoculture WB33 and WB28 walk through. **The one fixture defect in the contract.** → M3, M4 |
| `hosted_auth_block(..., keys=True)` — the `keys=False` branch is **never called** | ⚠ **Unexercised.** Design §5 rules `keys` OPTIONAL in `google_oauth` mode; no loremaster pin builds a hosted server without them. No wrong build I constructed exploits it, but the branch is dead in the contract. Residual R3. |
| `rewrite_roster` — always changes the file LENGTH | ❌ **DOES NOT DISCRIMINATE** on the change signal. → M6 |
| `TokeninfoSpy` / `scripted` / `always_raises` | ✅ **The fake can FAIL** (P5): `always_status(401)` denies, `always_json(admitted)` admits, `scripted([503, 200])` flips mid-test. Both directions exercised in the same module. |
| `_AllowOnlyResolver` | ✅ **Proven able to filter** — `test_a_tool_outside_the_resolved_permitted_set_is_refused` reds if it cannot. Kills WB23/WB24. |
| `stub_heavy_startup` | ✅ Sound, and its docstring records the measured trap (rebinding the attribute vs mutating the shared object). My reference build hit neither. |
| `roster_stat_counter` | ✅ **Proven able to fire**: WB13 reds it (12 kills). It spies and delegates — it measures, it does not simulate. |
| `_StubAppContext` | ✅ Correctly scoped; the ENTIRE SDK auth + session stack stays real, which is what the F3 pins need. |

---

## 7. P4 — the author's claims, reproduced rather than relayed

### 7.1 The RED/GREEN baseline and the 33-GREEN enumeration

```
$ uv run pytest <the 7 loremaster modules> lorerunes/tests -q -p no:randomly --tb=no
389 failed, 33 passed in 1.76s
```

**389 RED / 33 GREEN / 422 collected — reproduces exactly.** (The brief's file list alone
yields 421; the 422nd is the pre-existing `lorerunes/tests/test_smoke.py`, which the author's
`CONTRACT` variable picks up via the whole `lorerunes/tests` directory. No discrepancy.)

I listed the 33 with `-rp` and diffed them against the author's §5 enumeration:
12 × `TestApiKeyVerifierIsPreservedVerbatim` · 3 × `TestBuildApiKeyVerifierFromConfig` ·
7 × `TestOriginValidationMiddlewareIsPreserved` · 3 × `test_the_kept_names_are_still_exported` ·
2 × `TestLoopbackPostureIsUnchanged` · 1 × `test_a_config_without_the_retired_flag_loads` ·
2 × `TestLoreConfigCrossChecksTheResourcePath` refusals · 1 × `test_an_unauthenticated_initialize_succeeds` ·
1 × `test_the_homograph_fixture_is_actually_a_homograph` · 1 × `test_smoke`.
**Item for item, 33 = 33. No over-claim, no under-claim.**

Their disclosure that the two `TestLoreConfigCrossChecksTheResourcePath` refusals are
"currently passing for the WRONG reason" is **accurate and I verified both halves**: today
they pass because the hosted `auth` block trips `extra="forbid"`; on my reference build they
pass because the cross-check fires, and their positive control `test_matching_paths_validate`
flips from RED to GREEN alongside them.

### 7.2 A concurrent repo edit I did not make, disclosed

HEAD moved **`6e9e845` → `b5730f3`** during my run ("docs(39): record the contract-pass
rulings, and two wrong builds the S5 fix invites") and `loremaster/tests/test_auth_composition.py`
acquired a **prose-only** correction (a docstring/message citation of design §8 "row 14" →
"row 15"; row 14 is the retired-`__all__` row). No assertion changed. I copied the current
file into my scratch tree and re-ran the satisfiability leg to remove the caveat: **422 passed.**
`git status` confirms **I modified nothing in the repo** other than writing this report.

---

## 8. P6 / P6b — corpse sweep and the deleted-code diff

### 8.1 P6 — bare, anchor-free sweep. Every hit, an individual verdict.

Empirically grounded: I ran the reference build against the rest of the suite, so the
consumers enumerate themselves.

```
$ uv run pytest test_eager_startup.py test_mcp_server.py test_config.py \
      test_retired_symbols.py test_secret_leak_vectors.py -q -n auto --tb=no -rf
FAILED loremaster/tests/test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated
FAILED loremaster/tests/test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost
FAILED loremaster/tests/test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware
FAILED loremaster/tests/test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true
4 failed, 967 passed in 108.66s
```

⚑ **THE AUTHOR'S §8 "EXACT EDITS OUTSIDE MY WRITABLE SET" LIST IS INCOMPLETE BY THREE SITES.**
That section claims *"Each hit found by a bare, anchor-free grep … with a per-site verdict"*.
It lists `test_eager_startup.py`'s Bearer pin, `test_mcp_server.py`'s `_MUTATING_TOOLS`, and
`test_retired_symbols.py`. It does **not** list:

| Site | Verdict |
|---|---|
| `loremaster/tests/test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost` | **LISTED (item 1) ✓** — rewrite per §8 row 13. |
| `loremaster/tests/test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated` | ⚑ **MISSED.** Imports `BearerAuthMiddleware` and asserts `not isinstance(...)`. Must be deleted or rewritten against `OriginValidationMiddleware`. |
| `loremaster/tests/test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware` | ⚑ **MISSED.** Asserts `isinstance(app, BearerAuthMiddleware)` — a live corpse asserting the retired composition. Must be rewritten (its config is a valid `LAN_BEARER` shape, so the replacement is a 401-for-keyless assertion). |
| `loremaster/tests/test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true` | ⚑ **MISSED.** Asserts the RETIRED field still exists and defaults `True`. Must be deleted. |
| `loremaster/tests/test_mcp_server.py::_MUTATING_TOOLS` + `test_mutating_tools_are_not_marked_read_only` | **LISTED (item 2) ✓** — and confirmed: it did **NOT** red on my reference build, because it is a subset check. #291's diagnosis is exactly right; deletion is the only fix. |
| `loremaster/tests/test_retired_symbols.py::_RETIRED_SYMBOLS` | **LISTED (item 3) ✓** — must gain the three names in the same commit. |
| `loremaster/loremaster/config.py:24` (module docstring naming `tls_terminated_upstream`) | **prose site, not listed.** Builder rewrites it anyway; named so the sweep catches it — this is the "natural-language surfaces no gate checks" class. |
| `loremaster/loremaster/server.py::build_asgi_app` docstring (names `BearerAuthMiddleware`) | **prose site, not listed.** Same class; must be rewritten. |
| `loremaster/loremaster/calibration/corpus/comment_light_python.py.txt:200,207` | ⚠ **DO NOT EDIT.** A frozen Python-source sample used by the token-calibration corpus. Editing it perturbs the calibration baseline for no reason. Named here precisely so a blind sweep does not "fix" it. |
| `lore.yaml`, `lore.yaml.sample`, `skills/lore-deploy/` | **CLEAN** — grepped: neither carries an `auth:` block or `tls_terminated_upstream`, so the `extra="forbid"` migration breaks no live config on this host. |
| `docs/plans/v2/39-hosted-security.md`, `docs/design/2026-07-05-p13-…`, `docs/plans/v2/receipts/…` | **leave** — historical planning/receipt records; rewriting them falsifies the record. |
| `REPORT-*.md` at the root | **leave** — live wave reports, archived at close-out. |

**None of the four collateral reds is silent** — the wave lands RED rather than green-with-a-
corpse, which is the safe direction. But the author's list is what a builder will work from,
and it is short by three.

### 8.2 P6b — deleted-code enumeration ⚠ CONTAMINATED FRAME, disclosed

I read design §8 before enumerating (§1). I therefore do **not** claim an independent
enumeration. What I can offer is what §8 does not carry, found by reading `auth.py` in full:

| Behaviour of the deleted code | In §8? | Verdict |
|---|---|---|
| `BearerAuthMiddleware` returns the token **verbatim after `"Bearer "`, unstripped** | no | **equivalent** — the SDK does `auth_header[7:]`. No regression, nothing to pin. |
| **The FIRST `Authorization` header wins; a duplicate is ignored** | no | **equivalent** — `conn.headers.get()` also returns the first. Unpinned in both worlds; residual R4, cosmetic. |
| §8 row 6's rider: *"spy inner-app asserts not-called on 401"* | **row exists, RIDER NOT DISCHARGED** | The contract's `test_an_unknown_bearer_token_is_401_and_never_reaches_a_session` asserts **status only**; there is no spy-inner-app leg for the auth 401 (there is one for Origin, in `test_auth.py`). The property survives *indirectly* (reaching the session manager without a lifespan would raise, so a 401 is evidence). **Weak but not a hole — residual R5.** This is the rider law's own shape: the clause after *"and pin it like this"* was dropped. |
| `hmac` re-export in `__all__` (§8 row 14) | row exists | ⚠ **`KEPT_AUTH_EXPORTS` does not include `"hmac"`.** A builder can drop it from `__all__` with no pin reddening — `test_uses_constant_time_comparison` only needs the module *attribute*. Cosmetic; residual R6. |
| `AuthVerifier` ABC — any third-party subclass? | — | **None.** Bare grep across the tree finds subclasses only in `auth.py` itself. Safe to delete. |
| ⚑ `build_asgi_app` previously **served** an incoherent enabled-auth config; it must now **refuse** | **NOT ADJUDICATED ANYWHERE** | This is the behaviour change WB34 exploits. → **M2.** |

---

## 9. Residuals and escalations — each with an individual verdict

- **E1 — `google-auth` has an EMPTY read column on BOTH sides.** The author disclosed
  inheriting the claim; I inherited it too (not installed, `find_spec` → `None`). This is the
  precise failure P-PKG exists to catch, and it is now two-deep. **It does not change the
  verdict** (tokeninfo introspection of an opaque access token is production-proven in
  odoo-code, and the contract pins the mechanism regardless), but the claim is unverified.
  **One command settles it:** `uv run --with google-auth python -c "from google.oauth2 import id_token; help(id_token.verify_oauth2_token)"`.
  **Lead's call.**
- **E2 — design §13's own bound bites the fixtures.** `tokeninfo_payload` always emits BOTH
  `exp` and `expires_in`, and always emits `sub`. Google's actual field set is **unverified**
  (design §13 says so). If production omits `exp`, a build reading only `exp` denies 100% of
  traffic and **no pin can see it**. Not a contract defect — the design already names the live
  probe as the settling instrument — but the build leg must run that probe **before** the
  connector goes live, and the wave plan should say so.
- **R1 — WB31, truncated cache digest.** Real ruling violation; no cheap behavioural pin
  exists. Structural pin or accept-and-ledger. **Not mine to decide.**
- **R2 — WB29, stale roster retained on `OSError`.** Behaviourally equivalent. **Not a finding.**
- **R3 — `hosted_auth_block(keys=False)` is never called.** A legitimate deployment shape
  (design §5: `keys` OPTIONAL in `google_oauth` mode) is unexercised at the loremaster seam.
  Cheap to add; no surviving build exploits it.
- **R4 — duplicate `Authorization` header** unpinned in both worlds. Cosmetic.
- **R5 — §8 row 6's spy-inner-app rider undischarged.** See §8.2.
- **R6 — `"hmac"` absent from `KEPT_AUTH_EXPORTS`.** Cosmetic.
- **R7 — the `PLR0911` friction** on `verify_token` (§3). Not a defect; a builder trap worth
  one line in the build brief.
- **R8 — the ∀ helper's reach.** `assert_verification_outcome_is_total` is applied only via
  `_VerifierProbe`; `test_allowlist_roster`'s 43 pins call `verify_token` directly and are
  outside it. No build I constructed exploits the gap. Cheap fix: route `_RosterProbe.verify`
  through the same helper.
- **R9 — the normaliser mutation proof (design §5's "prove sharing by mutation") is owed and
  undischarged** by the author (they could not — no production code existed) and by me (out of
  scope for grading the contract). **The builder owes it**, and its absence is exactly how
  "routing is not sharing" ships green.
- **R10 — finding #294 reproduces**, second instance in this packet (§1). The
  `contract-adversary` agent definition still lacks the lore tools it is required by project
  law to prefer. **Not fixed by writing smaller briefs.**
- **R11 — a concurrent editor is in the tree** (§7.2). Harmless this time; flagged because a
  contract graded at one SHA and built at another is a scope claim, not a fact.

---

## 10. The instruments (brief-base §1 — an instrument that established a load-bearing claim is a deliverable)

⚠ **DEVIATION, declared.** My writable set is this report alone, so I cannot commit these to
`scripts/`. §10.4 (the proposed pins) and §10.3 (the wire probe) are pasted **verbatim** below,
because they establish the two headline claims. The full 45-entry wrong-build registry is
**774 lines** at `/home/ejprice/scratch/adv39_wrong_builds.py` — **an unrecoverable address by
standing law.** Its mechanism and every SURVIVOR's patch are pasted below; the 33 kills are
re-derivable from §4.0's table but not byte-exactly re-runnable. **Recommendation to the lead:
`git add` that file to `scripts/adv39_wrong_builds.py` in the wave commit** (it is the third
instrument of this class this repo has nearly lost — finding #278).

### 10.1 The wrong-build harness — mechanism, verbatim

```python
SCRATCH = Path("/home/ejprice/scratch/adv39")
REFBUILD = Path("/home/ejprice/scratch/refbuild")     # cp -a of the reference build's 6 files
BASELINE_COLLECTED = 422

def restore() -> None:
    """Put the reference build back, byte-exact."""
    for filename, destination in FILES.items():
        shutil.copyfile(REFBUILD / filename, destination)
    for cache in SCRATCH.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)

def apply(build: WrongBuild) -> None:
    """Apply every patch; an anchor matching != 1 time is a HARD ERROR."""
    for filename, old, new in build.patches:
        path = FILES[filename]
        text = path.read_text()
        occurrences = text.count(old)
        if occurrences != 1:
            raise SystemExit(
                f"{build.name}: anchor matched {occurrences} times in {filename} "
                f"(must be exactly 1). The patch did NOT land; a run now would grade "
                f"the CORRECT build and read as a survivor.\nANCHOR:\n{old}"
            )
        path.write_text(text.replace(old, new))

def run_contract() -> tuple[int, int, int, str]:
    completed = subprocess.run(
        ["uv", "run", "pytest", *CONTRACT, "-q", "-p", "no:randomly", "--tb=no", "-rf"],
        cwd=SCRATCH, capture_output=True, text=True, timeout=3600,
    )
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", completed.stdout)) else 0
    failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", completed.stdout)) else 0
    return passed, failed, passed + failed, completed.stdout

# ... per build: restore(); apply(build); run_contract()
#     collected != BASELINE_COLLECTED  -> NOT COMPARABLE (its own category, non-zero exit)
#     failed == 0                      -> *** SURVIVED ***
#     else                             -> killed, naming the first FAILED node id
```

### 10.2 Every SURVIVOR's patch, verbatim (`(file, old, new)`)

```python
WB28 ("auth.py"):   "    hosts |= _host_forms(config.server.host, config.server.port)\n"  ->  ""

WB29 ("auth.py"):   "        except OSError as error:\n            self._roster = None\n"
                    "            self._roster_signature = None\n"
                ->  "        except OSError as error:\n"

WB30 ("server.py") x3:
  1. "        await _enforce_dispatch_policy(self, name)\n"  ->  ""
  2. "    _register_tools(mcp, server)\n    _install_hosted_instructions(mcp, posture)"
  -> "    _register_tools(mcp, server)\n    _install_hosted_instructions(mcp, posture)\n"
     "    _install_guard_as_instance_attribute(mcp)"
  3. "async def _enforce_dispatch_policy(mcp: Any, name: str) -> None:"
  -> "def _install_guard_as_instance_attribute(mcp: Any) -> None:\n"
     "    original = mcp.call_tool\n\n"
     "    async def _guarded(name: str, arguments: dict[str, Any]) -> Any:\n"
     "        await _enforce_dispatch_policy(mcp, name)\n"
     "        return await original(name, arguments)\n\n"
     "    mcp.call_tool = _guarded\n\n\n"
     "async def _enforce_dispatch_policy(mcp: Any, name: str) -> None:"

WB31 ("auth.py"):   '        key = hashlib.sha512(token.encode("utf-8")).hexdigest()\n'
                    "        async with self._lock:\n            if key in self._negative:"
                ->  '        key = hashlib.sha512(token.encode("utf-8")).hexdigest()[:8]\n'
                    "        async with self._lock:\n            if key in self._negative:"

WB33 ("config.py"): "        host_is_loopback=config.server.host in _LOOPBACK_BIND_HOSTS,"
                ->  "        host_is_loopback=True,"

WB34 ("server.py"): "    posture = resolve_posture(config)\n    if posture is Posture.LOOPBACK:"
                ->  "    try:\n        posture = resolve_posture(config)\n"
                    "    except Exception:\n        posture = Posture.LOOPBACK\n"
                    "    if posture is Posture.LOOPBACK:"

WB35 ("auth.py"):   "    if posture is Posture.HOSTED_OAUTH:\n        origins.update(_HOSTED_DEFAULT_ORIGINS)"
                ->  "    if posture is not Posture.LAN_BEARER:\n        origins.update(_HOSTED_DEFAULT_ORIGINS)"

WB40 ("server.py"): "    refused = _mutating_tool_names(mcp)"
                ->  '    refused = ["lore_remember", "lore_index", "lore_findings",'
                    ' "lore_comms", "lore_claim_task", "lore_tasks"]'

WB41 ("auth.py"):   "        signature = (stamp.st_mtime_ns, stamp.st_size, stamp.st_ino)"
                ->  "        signature = (0, stamp.st_size, 0)"

WB42 ("auth.py"):   inserts before the Google-branch AccessToken mint:
                    '        _logger.info("google.admitted subject=%s token=%s", verdict.subject, token)'

WB42b ("auth.py"):  inserts before the Google-branch AccessToken mint (UNLABELLED — the shape
                    lore's own scrubber cannot see):
                    '        _logger.info("google.admitted %s for subject %s", token, verdict.subject)'

WB45 ("server.py"): "        required_scopes=[SCOPE_READ],"  ->  "        required_scopes=[],"
```

**Scrubber receipt for WB42b** (why the unlabelled shape is the dangerous one):

```
$ uv run python -c "from loremaster.logging_setup import _scrub_text; ..."
'google.admitted subject=1049 token=ya29.a0AfSECRET'   -> 'google.admitted subject=1049 token=***REDACTED***'
'Authorization: Bearer ya29.a0AfSECRET'                -> 'Authorization: Bearer ***REDACTED***'
'admitted ya29.a0AfSECRET'                             -> 'admitted ya29.a0AfSECRET'      <-- UNREDACTED
```

### 10.3 `adv39_wire_probe.py` — the paired control for the BLOCKER, verbatim

```python
#!/usr/bin/env python3
"""adv39_wire_probe.py — the POSITIVE CONTROL for WB30 (the unguarded wire path).

The packet-39 contract proves the hosted read-only guard only through the IN-PROCESS
entry point ``mcp.call_tool(...)``. This probe asks the question the contract does not:
*does the guard fire on the SERVED path — a real MCP `tools/call` over the assembled
ASGI app, authenticated with a real Google token through the real verifier?*

It is run TWICE, and the PAIR is the whole instrument:
  * against the CORRECT reference build  -> the refusal must appear;
  * against WB30 -> the refusal must be ABSENT, i.e. the tool was dispatched.
A probe that cannot show the second case is worth nothing, so both legs print.

Run from the scratch tree:  uv run python ../adv39_wire_probe.py
(needs LORE_KEY_LOCAL_AGENT / LORE_KEY_LAN_CLIENT exported, as the hosted block names them)
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "adv39" / "loremaster" / "tests"))
import httpx
from _auth_fixtures import (
    MCP_POST_HEADERS, OPERATOR_EMAIL, OPERATOR_SUBJECT, PUBLIC_HOSTNAME, TokeninfoSpy,
    admitted_payload, base_config_payload, bearer, drive, google_access_token,
    hosted_auth_block, json_rpc_initialize, mcp_session_id, running_asgi_app, slug,
    stub_heavy_startup, write_roster,
)

MUTATING_TOOL = "lore_remember"

async def main(tmp: Path) -> int:
    """Drive one real hosted MCP session and call a MUTATING tool over the wire."""
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_asgi_app, build_mcp_server
    import loremaster
    print(f"loremaster.__file__ = {loremaster.__file__}")

    roster = write_roster(tmp / "lore-secrets", OPERATOR_EMAIL)
    payload = base_config_payload(slug(), tmp / "live")
    payload["auth"] = hosted_auth_block(roster)
    config = LoreConfig.model_validate(payload)
    token = google_access_token("wire")

    def _respond(request: httpx.Request) -> httpx.Response:
        if token.encode() in request.content:
            return httpx.Response(200, json=admitted_payload(email=OPERATOR_EMAIL,
                                                             sub=OPERATOR_SUBJECT))
        return httpx.Response(401)

    spy = TokeninfoSpy(responder=_respond)
    mcp = build_mcp_server(LoreServer(config), http_client=spy.client())
    mcp.settings.json_response = True
    stub_heavy_startup(mcp)
    app = build_asgi_app(mcp, config)

    host = PUBLIC_HOSTNAME.encode("ascii")
    async with running_asgi_app(app):
        opened = await drive(app, method="POST", path="/mcp",
                             headers=[(b"host", host), *MCP_POST_HEADERS, bearer(token)],
                             body=json_rpc_initialize())
        assert opened.status == 200, f"initialize failed: {opened.status} {opened.body[:300]!r}"
        session = mcp_session_id(opened)

        await drive(app, method="POST", path="/mcp",
                    headers=[(b"host", host), *MCP_POST_HEADERS, bearer(token),
                             (b"mcp-session-id", session.encode("ascii"))],
                    body=b'{"jsonrpc":"2.0","method":"notifications/initialized"}')

        called = await drive(app, method="POST", path="/mcp",
                             headers=[(b"host", host), *MCP_POST_HEADERS, bearer(token),
                                      (b"mcp-session-id", session.encode("ascii"))],
                             body=json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                                              "params": {"name": MUTATING_TOOL,
                                                         "arguments": {}}}).encode())

    body = called.body.decode("utf-8", "replace")
    refused = "read scope only" in body or "HOSTED_OAUTH posture" in body
    print(f"status={called.status}")
    print(f"body={body[:600]}")
    print(f"\nVERDICT: the hosted read-only guard "
          f"{'FIRED on the wire path' if refused else '*** DID NOT FIRE on the wire path ***'}")
    return 0 if refused else 1

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        raise SystemExit(asyncio.run(main(Path(directory))))
```

### 10.4 THE MISSING PINS, as runnable code

All nine pass on the correct reference build (`14 passed`) and each reds on its named wrong
build (§6). **`M1` is the exception and is deliberately NOT written as a unit pin below** —
see the note after the block.

```python
"""ADVERSARY-PROPOSED MISSING PINS — packet 39 (adversary-39-auth-1, 2026-07-31).

Each class names the wrong build it kills and the production consequence. Proven by the
PAIR: green on the adversary's known-correct reference build (the P0 control leg), red on
the wrong build the shipped contract waves through.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any
import pytest
import httpx
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT, API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT, CLAUDE_AI_ORIGIN, OPERATOR_EMAIL, OPERATOR_SUBJECT,
    SECOND_PRINCIPAL_EMAIL, SECOND_PRINCIPAL_SUBJECT, TokeninfoSpy, admitted_payload,
    base_config_payload, google_access_token, hosted_auth_block, lan_bearer_auth_block,
    make_verifier, slug, write_roster,
)

# A replacement address with the SAME BYTE LENGTH as SECOND_PRINCIPAL_EMAIL, so a build
# that detects roster change by st_size alone sees nothing move.
SAME_LENGTH_REPLACEMENT = "dana.whitfield@pricepaper.net"
assert len(SAME_LENGTH_REPLACEMENT) == len(SECOND_PRINCIPAL_EMAIL)


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars the hosted/LAN auth blocks reference."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


class TestTheTokenIsNotLoggedOnTheADMITTEDPathEither:
    """M5 — kills WB42/WB42b. The shipped pin drives only a 401 — the quantifier law."""

    async def test_the_raw_token_never_appears_in_a_log_record_on_success(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Design §8 row 5's property is "the presented credential value is NEVER logged" —
        # a universal over verifications, not over FAILED ones. lore's scrubber redacts
        # only LABELLED shapes ("an UNLABELLED credential in free prose is NOT redacted"),
        # so a token logged bare on the admitted path reaches the container log verbatim.
        from _auth_fixtures import always_json

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_verifier(roster_path=roster, api_keys=None, http_client=spy.client())
        token = google_access_token("admitted-never-logged")
        with caplog.at_level(logging.DEBUG):
            assert await verifier.verify_token(token) is not None, (
                "the positive control: this verification must SUCCEED, or the pin passes "
                "because nothing was admitted"
            )
        for record in caplog.records:
            assert token not in record.getMessage(), (
                f"the raw token leaked into a log record on the ADMITTED path: "
                f"{record.getMessage()!r}"
            )
            assert token not in str(record.args)


class TestRosterChangeDetectionSurvivesASameLengthEdit:
    """M6 — kills WB41. Every shipped revocation fixture changes the file's LENGTH."""

    async def test_swapping_one_address_for_another_of_equal_length_revokes(
        self, tmp_path: Path
    ) -> None:
        # An operator replacing one principal with another — the ordinary membership edit
        # — can leave the byte-count unchanged. A build whose change detection is keyed on
        # st_size then never reloads, and the departed principal keeps access indefinitely.
        import os, time

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        seen: dict[str, str] = {}

        def _respond(request: httpx.Request) -> httpx.Response:
            for candidate, email in seen.items():
                if candidate.encode() in request.content:
                    return httpx.Response(200, json=admitted_payload(
                        email=email, sub=SECOND_PRINCIPAL_SUBJECT))
            return httpx.Response(401)

        spy = TokeninfoSpy(responder=_respond)
        verifier = make_verifier(roster_path=roster, api_keys=None, http_client=spy.client())
        warm = google_access_token("same-length")
        seen[warm] = SECOND_PRINCIPAL_EMAIL
        assert await verifier.verify_token(warm) is not None

        before = roster.stat()
        roster.write_text(
            "# lore hosted-read allowlist — one Google identity per line.\n"
            "# Revoke by deleting a line; effective on the next verification.\n\n"
            f"{OPERATOR_EMAIL}\n{SAME_LENGTH_REPLACEMENT}\n", encoding="utf-8")
        forced = max(time.time(), before.st_mtime + 1.0)
        os.utime(roster, (forced, forced))
        assert roster.stat().st_size == before.st_size, (
            "the fixture must leave the file SIZE unchanged, or it is testing the "
            "size-changed path instead")

        assert await verifier.verify_token(warm) is None, (
            "a principal replaced by a DIFFERENT address of the same byte length must "
            "still be revoked — change detection keyed on st_size alone never reloads")


class TestThePostureRefusalReachesTheThingThatActuallyBoots:
    """M2 — kills WB34. The boot refusal is pinned only on ``resolve_posture`` itself."""

    def test_build_mcp_server_refuses_a_hosted_config_whose_roster_will_not_load(
        self, tmp_path: Path
    ) -> None:
        # R11/R12: "HOSTED_OAUTH refuses to BOOT unless the roster loads with >=1 valid
        # entry". The thing that boots is build_mcp_server / build_asgi_app. A build that
        # catches PostureConfigError there and degrades to LOOPBACK serves an
        # internet-facing lore with NO auth at all, and every shipped pin stays green.
        from loremaster.config import LoreConfig, PostureConfigError
        from loremaster.server import LoreServer, build_mcp_server

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        config = LoreConfig.model_validate(payload)
        roster.unlink()
        with pytest.raises(PostureConfigError):
            build_mcp_server(LoreServer(config))

    def test_a_healthy_hosted_config_still_builds(self, tmp_path: Path) -> None:
        # THE CONTROL: the refusal must not be a blanket one.
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_mcp_server

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        assert build_mcp_server(LoreServer(LoreConfig.model_validate(payload))) is not None


class TestTheLoopbackClaimIsAboutTheCONFIGUREDBindHost:
    """M3 — kills WB33. Every loremaster fixture binds ``127.0.0.1``: a value monoculture."""

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.64.100", "::"])
    def test_a_hosted_config_on_a_NON_loopback_bind_refuses_to_boot(
        self, tmp_path: Path, host: str
    ) -> None:
        # Design R4 / investigation M-2: lore must NEVER be the thing listening off
        # loopback — "--network=host + a wide bind is instant whole-LAN exposure".
        # lorerunes pins derive_posture(host_is_loopback=False) -> refusal, but nothing
        # pins the MAPPING from config.server.host to that boolean.
        from loremaster.config import LoreConfig, PostureConfigError, resolve_posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        with pytest.raises(PostureConfigError):
            resolve_posture(LoreConfig.model_validate(payload))

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
    def test_every_loopback_SPELLING_still_resolves_to_hosted_oauth(
        self, tmp_path: Path, host: str
    ) -> None:
        # THE CONTROL, and the other half of the monoculture: three spellings of the same
        # bind. A build recognising only "127.0.0.1" refuses a legitimate `localhost`
        # deployment at boot.
        from loremaster.config import LoreConfig, resolve_posture
        from lorerunes import Posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        assert resolve_posture(LoreConfig.model_validate(payload)) is Posture.HOSTED_OAUTH


class TestTheEdgePolicyAllowsTheCONFIGUREDBindHost:
    """M4 — kills WB28. Every EdgePolicy pin binds loopback, so a hardcoded set passes."""

    def test_a_lan_bearer_deployment_on_a_real_lan_address_is_not_421ed(
        self, tmp_path: Path
    ) -> None:
        # Design §5 rules LAN_BEARER legal on a NON-loopback bind (lorerunes'
        # test_todays_enabled_api_key_config_is_lan_bearer asserts exactly that). With
        # DNS-rebinding protection ON and allowed_hosts hardcoded to loopback, every LAN
        # request carries `Host: 192.168.64.100:9202` and is answered 421 — the W7 trap,
        # one posture over, 100% of traffic.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import LoreConfig, resolve_posture

        lan_host = "192.168.64.100"
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = lan_host
        payload["auth"] = lan_bearer_auth_block()
        config = LoreConfig.model_validate(payload)
        policy = derive_edge_policy(config, resolve_posture(config))
        assert any(entry.split(":")[0] == lan_host for entry in policy.allowed_hosts), (
            f"the derived edge policy must allow the CONFIGURED bind host {lan_host!r}; "
            f"allowed_hosts was {sorted(policy.allowed_hosts)}")


class TestTheLoopbackEdgePolicyDoesNotTrustClaude:
    """M8 — kills WB35. ``derive_edge_policy`` is never asserted for LOOPBACK."""

    def test_the_loopback_posture_does_not_allow_the_claude_origins(
        self, tmp_path: Path
    ) -> None:
        # LOOPBACK installs NO auth. Trusting claude.ai's origin there means a page served
        # from that origin can reach an unauthenticated local lore.
        from loremaster.auth import derive_edge_policy
        from loremaster.config import LoreConfig, resolve_posture

        config = LoreConfig.model_validate(base_config_payload(slug(), tmp_path / "live"))
        policy = derive_edge_policy(config, resolve_posture(config))
        assert CLAUDE_AI_ORIGIN not in policy.allowed_origins


class TestTheHostedInstructionsSectionIsDERIVED:
    """M7 — kills WB40. The section pin compares a hand list against a hand list."""

    def test_a_newly_registered_mutating_tool_appears_in_the_refused_set_section(
        self, tmp_path: Path
    ) -> None:
        # Design §7: the section is "GENERATED from the registered annotations (never prose
        # beside them)". A hand-listed section satisfies every shipped pin and then teaches
        # a stale refused set the day a tool is added.
        from mcp.types import ToolAnnotations
        from loremaster.config import LoreConfig
        from loremaster.server import (HOSTED_REFUSAL_SECTION_HEADING, LoreServer,
                                       build_mcp_server, _install_hosted_instructions)
        from lorerunes import Posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        mcp = build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))
        baseline = mcp.instructions or ""
        assert HOSTED_REFUSAL_SECTION_HEADING in baseline

        def _probe_write() -> str:
            """A newly contributed mutating tool."""
            return "ok"

        mcp.add_tool(_probe_write, name="lore_probe_mutating",
                     annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False))
        mcp._mcp_server.instructions = baseline.split(HOSTED_REFUSAL_SECTION_HEADING)[0]
        _install_hosted_instructions(mcp, Posture.HOSTED_OAUTH)
        section = (mcp.instructions or "").split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        assert "lore_probe_mutating" in section, (
            "a newly registered mutating tool must appear in the served refused-set "
            "section; a hand-listed section teaches a refused set that has drifted")


class TestTheRequiredScopeIsTheRuledValue:
    """M9 — kills WB45. ``required_scopes`` is never asserted anywhere."""

    def test_the_hosted_auth_settings_require_the_read_scope(self, tmp_path: Path) -> None:
        # Design §6 names the value. With required_scopes=[] the SDK's
        # RequireAuthMiddleware enforces nothing, silently removing a defence-in-depth
        # layer that is invisible while every minted token happens to carry the scope.
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_mcp_server
        from lorerunes import SCOPE_READ

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        mcp = build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))
        assert mcp.settings.auth is not None
        assert mcp.settings.auth.required_scopes == [SCOPE_READ]
```

**M1 — the BLOCKER — is deliberately NOT a unit pin.** Writing
`assert mcp.call_tool is TracingFastMCP.call_tool.__get__(mcp)` would be a name-list gate, and
this repo has six receipts against those. **The pin that should exist is the wire probe itself,
adopted into `test_auth_identity_seam.py`** — the module that already runs the real lifespan
and already holds `_TwoPrincipalEdge`:

> **`TestSessionsAreBoundToTheCredentialThatCreatedThem::test_a_hosted_principal_is_refused_a_mutating_tool_over_the_WIRE`**
> — open a real session as `edge.operator_token`, send `notifications/initialized`, then
> `tools/call {"name": "lore_remember", "arguments": {}}`, and assert the response body
> carries the `HostedToolRefusedError` teaching. **Its control, in the same class:**
> the same `tools/call` for a READ tool (`lore_search`) must NOT carry that teaching, and the
> same call as `API_KEY_VALUE_LOCAL_AGENT` must NOT be refused — otherwise a build that
> refuses everything over the wire passes.
> **The defect it catches:** any build where the guard is not on the served dispatch path.
> WB30 is one such build and it passes all 422 pins today.

The mechanics are already proven — §10.3 is that request sequence, executed, in both
directions.

---

## VERDICT

# CONTRACT INSUFFICIENT

Not because it is weak — it is the strongest contract I have graded, and it killed 33 of 45
wrong builds including every one the brief named. It is insufficient because **twelve wrong
builds survive it**, and because the survivors cluster on one recognisable shape: *the
invariant was pinned at the seam where it was reasoned about, not at the seam where it is
enforced.* The guard is pinned at `mcp.call_tool` and enforced on the wire (M1). The boot
refusal is pinned at `resolve_posture` and enforced at `build_mcp_server` (M2). The loopback
claim is pinned at the pure function and enforced on `config.server.host` (M3). The edge
policy is pinned at a loopback bind and enforced at whatever the operator configured (M4). The
secrecy sweep is pinned on the failure path and needed on every path (M5).

**Nine pins to write, all nine already written and paired in §10.4 (and §10.3 for M1).**
Route it back to CONTRACT; the fix is an afternoon, and the adversary pass on the fix wave is
not optional (operator, 2026-07-28 — receipts, same day, twice).
