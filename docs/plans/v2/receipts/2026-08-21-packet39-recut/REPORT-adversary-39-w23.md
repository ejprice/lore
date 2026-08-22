# REPORT — adversary-39-w23 (packet 39 RE-CUT, wave 2+3 contract-adversary)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done-with-deviations** — graded the wave-2/3 contract EMPIRICALLY (built the full
  reference composition + guard + posture + config validators + auth deletions in scratch).
- **VERDICT: INSUFFICIENT** — the security boundary (the read-only guard) is SOLID (every guard
  wrong-build caught, the #295 EFFECT works), BUT the contract does **NOT** go 0-failed on the
  natural correct build as-shipped (a C-DEF), and one deny-by-default security pin is MISSING.
  Both are cheap fixes; this is the first adversary pass (no 3×-escalation).
- deviations:
  - Satisfiability was measured TWO ways because of finding #1: **89 passed / 0 failed WITH
    `SURREAL_USER`/`SURREAL_PASS` set**; **10 failed WITHOUT them** (the as-shipped fixture world).
  - Reference build required editing the FROZEN wave-1 `token_verifier.py` (super().__init__) — see
    OBSERVATION-A; this is a real build obligation, flagged not silently resolved.
- **Packages considered:** fastmcp==3.4.7 (`Middleware`/`RemoteAuthProvider`/`TokenVerifier`/
  `get_access_token`/`FastMCP(auth=)` — read installed source in `.venv/.../fastmcp/`), pydantic
  (`model_validator`/`AnyHttpUrl`), ipaddress stdlib (`host_is_loopback`) — all USE, verdicts from
  READ installed source. No new mechanism specified (I graded, did not ship).
- **Reuse ledger:** none — I authored no shipped symbols (reference build is scratch-only, discarded).
- **Graded:** `feea77a9b8067e5fccbfee1354583cc31a0ad5e0` · HEAD-at-report: `feea77a` · **SAME**.
- decisions-needed: the C-DEF (#1) and MISSING PIN (#2) route back to the contract author
  (contract → adversary → build order); OBSERVATION-A (frozen wave-1 verifier edit) needs a lead
  ruling on whether wave-2/3 may touch the frozen module or must adapt it.
- receipt pointers: satisfiability → §1; wrong-build table → §2; the two findings → §3; observations
  → §4; deviation/instrument confirmations → §5; scratch provenance → §0.

---

## §0. Scratch provenance (#140)
Reference build in `./scripts/scratch_copy.sh /tmp/adv39w23-ref` (provenance asserted by the tool).
Printed receipt:
```
loremaster.__file__ = /tmp/adv39w23-ref/loremaster/loremaster/__init__.py
lorerunes.__file__  = /tmp/adv39w23-ref/lorerunes/lorerunes/__init__.py
```
Both resolve UNDER the scratch root — the reference build grades the scratch tree, not the original.
Test store `ws://127.0.0.1:18000` (spike, health OK); never `:18500`.

---

## §1. Satisfiability receipt (attack #1 — the FULL composition built)

I built a KNOWN-CORRECT reference impl of the whole wave-2/3 surface:
- `lorerunes/posture.py`: `host_is_loopback` (localhost / `ipaddress(...).is_loopback`, fail-CLOSED
  on `ValueError`) + `derive_posture` (LOOPBACK/LAN_BEARER/HOSTED_OAUTH + `PostureError` naming the
  nearest posture + field).
- `readonly_guard.py`: `on_list_tools` filters the mutating partition when the ambient principal
  lacks `lore:write`; `on_call_tool` RAISES `ToolError` (naming the tool) BEFORE `call_next`; reach
  DERIVED from `fastmcp.list_tools(run_middleware=False)` via `partition_tools_by_posture`; no
  principal ⇒ no-op.
- `config.py`: `OAuthProviderConfig` client_id via `lorerunes.is_blank`; `AuthConfig` base_url
  `urlsplit(...).scheme != "https"`; a `mode="before"` migration validator naming
  `tls_terminated_upstream` + "remove/delete"; the field DELETED.
- `auth.py`: `BearerAuthMiddleware` + `AuthVerifier` DELETED, `__all__` trimmed, `ApiKeyVerifier`
  reparented to `object`, `ABC` import removed.
- `server.py`: `_compose_auth` wires `FastMCP(auth=…)` per posture (None / bare `LoreTokenVerifier`
  / `RemoteAuthProvider(LoreTokenVerifier, authorization_servers=[…], base_url=<ORIGIN>)`) +
  installs `ReadOnlyGuardMiddleware`; `build_asgi_app` drops `BearerAuthMiddleware`, keeps
  `OriginValidationMiddleware` outermost.

**RESULT (reference build, `SURREAL_USER=root SURREAL_PASS=spikeroot`):**
```
test_auth_config_recut.py + test_auth.py + test_auth_composition_recut.py +
test_readonly_guard.py + test_auth_composition_wire.py + lorerunes/tests/test_posture.py
=> 89 passed in 3.44s   (0 failed)
```
So the contract IS satisfiable — a correct composition + guard + posture + config + auth-deletions
goes **0-failed**, INCLUDING every #295-EFFECT wire pin (they were ERROR-RED-vs-stub via a 401
`initialize`; GREEN once the composition authenticates the member AND the guard refuses).

**RESULT WITHOUT the surreal creds set (the AS-SHIPPED fixture env — see finding #1):**
```
=> 10 failed, 79 passed   (all 10 fail: KeyError 'SURREAL_USER' at build_principal_store)
```

---

## §2. Wrong-build sweep (attack #2 — weighted on the guard/security boundary)

Every wrong build was constructed in scratch against the reference; the CAUGHT column names the pin
that reddened (verbatim node ids run). CAUGHT = the contract discriminates; **SURVIVED = MISSING PIN.**

| # | wrong build | caught-by-pin | result |
|---|---|---|---|
| WB-A | guard runs `call_next` THEN refuses (WB48 / #295) | `test_a_hosted_mutating_tool_is_refused_and_its_body_never_runs` (STRONG leg: `effect_count()==1, expected 0`) | **CAUGHT** |
| WB-B | guard reach = HAND-LIST of the 6 built-ins (blind to synthetic) | `…is_refused_and_its_body_never_runs` + `test_served_intersection_refused_is_empty_for_a_hosted_member` | **CAUGHT** |
| WB-C | `on_list_tools` overridden but does NOT filter (refuse-but-visible) | `test_served_intersection_refused…` + `test_one_annotation_flip_moves_a_tool_across_guard_and_list` | **CAUGHT** |
| **WB-D** | guard hand-rolls `readOnlyHint is False` (NOT deny-by-default; NOT the shared partition) | — **NONE** — full `test_readonly_guard.py` = **7 passed** | **SURVIVED → MISSING PIN #2** |
| WB-E | `OAuthProviderConfig` ADDS a `client_secret` field (extra=forbid moot) | `test_client_secret_cannot_be_inlined` | **CAUGHT** |
| WB-F | base_url guard = `startswith("http://")` only (ws:// / schemeless slip) | `test_a_non_https_scheme_base_url_is_refused` + `test_a_non_url_base_url_is_refused` (https positive control still GREEN) | **CAUGHT** |
| WB-G | `host_is_loopback` = `startswith("127.")` + fail-OPEN on parse error | 9× `test_malformed_hosts_fail_closed_to_false[...]` (incl. `127.0.0.1.evil.com`, `localhost.evil.com`, `127.0.0.1extra`) | **CAUGHT** |
| WB-H | LAN_BEARER wired as `RemoteAuthProvider` (serves a .well-known it can't honour) | `test_lan_bearer_wires_a_bare_token_verifier_not_a_remote_auth_provider` + `test_wellknown_is_absent_in_lan_bearer` | **CAUGHT** |
| WB-I | client_id blank check via bare truthiness `if not client_id` (whitespace slips) | `test_whitespace_only_client_id_is_refused` (empty-string pin still GREEN — genuine discrimination) | **CAUGHT** |

The removed-behavior discrimination (`BearerAuthMiddleware`/`AuthVerifier` still importable;
`tls_terminated_upstream` still a field) is already proven by the RED-vs-stub baseline (7 fails) →
GREEN-on-delete → so those pins discriminate. The kept-surface control
(`TestKeptAuthSurfaceIsExported`) is present and stays GREEN.

---

## §3. Findings (numbered — each with the surviving wrong build / RED-on-correct receipt)

### FINDING #1 — C-DEF (satisfiability): compose-unit + transport fixtures do not thread SURREAL credentials
**10 pins RED on the CORRECT build**, all `KeyError: 'SURREAL_USER'` at
`config.py::resolve_config_value` ← `build_principal_store(config)` ← `_compose_auth`:
```
test_auth_composition_recut.py :: test_the_injected_http_client_param_exists
                               :: test_hosted_wires_the_lore_token_verifier_as_the_fastmcp_auth
                               :: test_hosted_auth_is_a_remote_auth_provider_advertising_authorization_servers
                               :: test_hosted_installs_the_read_only_guard_middleware
                               :: test_lan_bearer_wires_a_bare_token_verifier_not_a_remote_auth_provider
test_auth_composition_wire.py  :: test_wellknown_is_served_200_and_anonymous
                               :: test_unauthenticated_post_401_carries_resource_metadata
                               :: test_disallowed_origin_is_403_with_zero_outbound_provider_calls
                               :: test_wrong_host_is_refused
                               :: test_wellknown_is_absent_in_lan_bearer
```
**Root cause.** These pins construct the composed server (`_recut_auth_fixtures.build_composed_mcp`
and `test_auth_composition_wire._hosted_app`) from `base_config_payload`, whose `surreal` block is
the DEFAULT (`user_env="SURREAL_USER"`, `password_env="SURREAL_PASS"`). Any correct `build_mcp_server`
that wires `FastMCP(auth=…)` must construct the verifier's `PrincipalStore`/`PrincipalKeyStore` from
`config.surreal` (the contract author's OWN documented composition-coupling assumption), which
resolves those creds at construction. In the test env `SURREAL_USER`/`SURREAL_PASS` are **UNSET**
(verified: no pytest-env plugin, no autouse conftest, not exported by the shell; sibling tests that
need them set them THEMSELVES — `test_ingest_entity_seam.py:1105` monkeypatches them; the WIRE
harness `_open_hosted_wire_admission` sets `LORE_TEST_SURREAL_USER/_PASS`). So the correct build
`KeyError`s and the satisfiability receipt (design §13: "0-failed against a known-correct build")
is UNMEETABLE as the fixtures are shipped.
**Why it's a contract defect, not a build defect.** `resolve_secret` is designed to FAIL on a
blank/missing var; a build that tolerated a missing surreal cred (placeholder password) would be a
security smell and would bypass the one secret-resolution seam. The natural build resolves eagerly.
The fix lives in the CONTRACT fixtures, not production code.
**FIX (small, ~2 lines each):** thread the test-store creds into `build_composed_mcp` (hosted+LAN)
and `_hosted_app` (and its LAN sibling) — either `monkeypatch.setenv("SURREAL_USER"/"SURREAL_PASS")`
(as `test_ingest_entity_seam` does) or point `config.surreal.user_env/password_env` at the
`_surreal_harness` env names the harness already sets. Loopback needs nothing (it returns before
building stores — `test_loopback_installs_no_auth_provider` passed WITHOUT creds).

### FINDING #2 — MISSING PIN: deny-by-default is not enforced against the GUARD (ROUTING-IS-NOT-SHARING)
**Surviving wrong build: WB-D.** A guard that classifies mutating as `readOnlyHint is False`
(instead of the deny-by-default `is not True`, i.e. NOT routing through the shared
`partition_tools_by_posture`) passes the **entire** `test_readonly_guard.py` — 7 passed — because
every synthetic fixture tool is annotated with an EXPLICIT `readOnlyHint=False`
(`_register_synth_tools`, `_prepare_read_only`/`_prepare_mutating`). No fixture registers a mutating
tool with `readOnlyHint=None` (unannotated). Consequence: a build whose guard hand-rolls its own
classification (the exact ROUTING-IS-NOT-SHARING / "private copy wearing the shared name" defect
class this repo has the most receipts against) ships GREEN while a future UNANNOTATED tool is
**callable + visible to a hosted member** — deny-by-default (design §7: "None = unclassified lands
in `mutating`") silently violated.
The contract's stated defense ("partition CLASSIFICATION is pinned elsewhere — NOT duplicated") only
holds IF the guard USES the partition; nothing forces it. Repo law demands "prove sharing by
MUTATION" for exactly this.
**FIX:** add one hosted-wire fixture registering a synthetic mutating tool with
`ToolAnnotations(readOnlyHint=None)` (or no annotations at all) and assert it is
refused-AND-invisible to a hosted member (reuse `assert_tool_refused_and_did_not_run` +
`served_tool_names`). That single fixture reddens WB-D and forces the guard onto the deny-by-default
partition.

---

## §4. Observations (not blocking the verdict on their own, but the lead should see them)

### OBSERVATION-A — the FROZEN wave-1 `LoreTokenVerifier` cannot be composed as-is (build obligation)
`token_verifier.py::LoreTokenVerifier.__init__` **never calls `super().__init__()`**, so the fastmcp
`TokenVerifier` base attributes (`required_scopes`, `base_url`) are never set. Handing it to
`FastMCP(auth=…)` or wrapping it in `RemoteAuthProvider(token_verifier=verifier)` (both REQUIRED by
the composition pins, design §8) raises `AttributeError: 'LoreTokenVerifier' object has no attribute
'required_scopes'` (RemoteAuthProvider.__init__ reads it unconditionally). My reference build fixed
it with `super().__init__(required_scopes=None)` (None so fastmcp does not double-enforce against the
MINTED `lore:read` scope). This IS surfaced by the compose-unit pins (they fail until fixed, once
finding #1's creds are provided) — so it is a build obligation the contract DOES catch, not a missing
pin. BUT it requires editing a module that is FROZEN and was graded SUFFICIENT by the wave-1
adversary (`REPORT-adversary-39-w1.md`). **Lead ruling needed:** may wave-2/3 edit
`token_verifier.py`, or must the composition adapt it externally? (I recommend the one-line
`super().__init__` in the verifier — an adapter would be a second wrapper for no benefit.)

### OBSERVATION-B — minor: the "zero-outbound" leg of the Origin pin is non-discriminating
`test_disallowed_origin_is_403_with_zero_outbound_provider_calls` sends a hostile Origin with **no
bearer**, so no outbound tokeninfo call happens on EITHER a correct or a wrong build — the
`spy.call_count == 0` assertion passes vacuously. The pin's real discriminator is the STATUS
(403 Origin-outermost vs 401 credential-first), which works. But the advertised "zero outbound
provider calls" property (Origin rejected BEFORE any provider call) is not actually exercised: a
truly discriminating leg would send a VALID bearer + hostile Origin and assert the tokeninfo spy saw
0 calls. Minor (the status leg carries the pin); worth a one-line fixture upgrade.

---

## §5. Confirmations demanded by the brief

- **Deviation (a) — enforce-wire ERROR-RED-vs-stub → GREEN-at-build is NOT vacuous:** CONFIRMED. The
  4 hosted-wire #295 pins are RED against the stub (wire 401s), GREEN on the correct guard (7/7), and
  RED on WB-A/WB-B/WB-C. They discriminate a WORKING guard from a broken one.
- **Deviation (b) — the LAN-guard-wire-pin DROP is justified:** CONFIRMED. LAN api-key full-write is
  pinned at the verifier level (`test_token_verifier.py::test_api_key_principal_keeps_full_write`,
  line 981) and the guard's respect for `lore:write` is exercised by the loopback no-op pin
  (`test_loopback_has_the_full_surface`) + the member-refused wire pins.
- **Loopback #295 instrument preserved:** CONFIRMED. `test_refusal_observes_effect.py` = **7 passed /
  1 skipped** against the reference build — byte-identical to the cold-audit baseline; the recut
  `_auth_fixtures.wire_session` left the loopback/LAN branches untouched.
- **#295 EFFECT (attack #3):** the effect pins assert the BODY did not run (invocation counter == 0
  via `assert_tool_refused_and_did_not_run`), NOT merely a refusal marker — WB-A (run-then-refuse)
  reddens on `effect_count()==1`. Positive control (`test_a_read_only_tool_is_visible_and_its_body_runs`)
  proves the harness SEES a body execute (counter==1). SOUND.
- **P1b quantifier (Posture ∀):** the refusal fate is FORCED with a synthetic mutating fixture and
  the service fate with a synthetic read-only fixture (real fixtures, not a ∀ helper). The EFFECT is
  proven on the synthetic tool (built-in bodies need the live AppContext — the documented #295
  pattern), and reach is registry-derived so built-ins are covered transitively. Adequate; the one
  quantifier HOLE is the unannotated case (FINDING #2).
- **P1c reach attack:** the coverage/reach check is the SYNTHETIC-tool refusal (a tool ∉ the built-in
  set), reach DERIVED from `list_tools(run_middleware=False)`. WB-B (hand-list) is CAUGHT. The
  design's stricter "assert observed set EQUALS the registry" pin is not shipped as a distinct
  test, but the synthetic-tool check catches the primary hand-list defect; adequate.
- **P2 fixture perturbation + probe-needs-control:** every reject pin has a passing positive control
  (`_valid_oauth`, `test_https_base_url_is_accepted`, empty-vs-whitespace client_id, the
  kept-surface control, the clean-config control). WB-F/WB-I confirm the discriminators fire only on
  the wrong build, not vacuously.

---

## §6. Verdict

**INSUFFICIENT.** The read-only enforcement guard — the security boundary this wave IS — is SOLID:
every guard wrong-build (run-then-refuse, hand-list reach, refuse-but-visible) is caught, the #295
EFFECT discipline works, and config/posture/removed discriminators all fire. But:
1. **FINDING #1 (C-DEF):** the contract does not go 0-failed on the natural correct build — the
   compose-unit + transport fixtures don't thread SURREAL creds (10 pins RED). The satisfiability
   receipt is unmeetable as shipped.
2. **FINDING #2 (MISSING PIN):** deny-by-default is not enforced against the guard — a hand-rolled
   `is False` guard (ROUTING-IS-NOT-SHARING) passes the whole enforcement contract and admits
   unannotated tools to a hosted member.

Both are cheap, well-scoped fixes for the contract author (fixture cred-threading; one
`readOnlyHint=None` fixture). OBSERVATION-A additionally needs a lead ruling (edit the frozen wave-1
verifier vs adapt it). Route #1 + #2 back to the contract author (contract → adversary → build);
re-run this adversary on the revision.

---

## §7. DELTA PASS — round 2 (revised contract, directive #5132, thread w23-adversary-delta)

**VERDICT: SUFFICIENT.** The contract-39-w23 round-1 revision closes BOTH round-1 findings and the
security boundary did not regress. Graded by re-using the round-1 reference composition overlaid onto
a FRESH scratch of the revised tree.

- **Scratch provenance (delta):** `./scripts/scratch_copy.sh /tmp/adv39w23-ref2`;
  `loremaster.__file__ = /tmp/adv39w23-ref2/loremaster/loremaster/__init__.py` (resolves under the
  scratch root). Revised contract files taken fresh from the tree; my 6 reference PRODUCTION files
  overlaid (the round-1 revision touched only contract/fixtures — config.py/server.py stub stats
  unchanged, so the reference builds on the same stubs).

- **(a) C-DEF #1 CLOSED — correct build 0-failed with `SURREAL_USER`/`SURREAL_PASS` UNSET.** Ran the
  full wave-2/3 set under `env -u SURREAL_USER -u SURREAL_PASS` → **90 passed / 0 failed** (was 89,
  +1 = the new deny-by-default pin). The fixtures now thread the test-store creds via ONE shared seam
  (`_auth_fixtures.surreal_block_for_test_store` + `set_test_store_creds`, pointing
  `config.surreal.{user_env,password_env}` at the wire `*_env` vars the seam sets; `wire_session`
  refactored onto the same seam — no fork). The satisfiability receipt is now MEETABLE without any
  externally-set env.

- **(b) MISSING PIN #2 CLOSED — the new deny-by-default pin DISCRIMINATES precisely.**
  `test_an_unclassified_tool_is_denied_by_default_for_a_hosted_member` registers a synthetic tool
  with `readOnlyHint=None`. Against the correct `is not True` guard it PASSES (part of the 90/0).
  Against the WB-D wrong guard (`readOnlyHint is False`, i.e. NOT the deny-by-default partition) the
  full `test_readonly_guard.py` = **1 failed / 7 passed** — and the ONE failure is exactly that pin,
  via the #295 EFFECT (`refusal_marker absent … Body: 'SYNTH-BODY-RAN-W23'` — the unclassified body
  RAN). It reds ONLY on that wrong build (no over-pinning of a legit build).

- **(c) Boundary still SOLID (no regression under the creds-seam refactor).** Spot-checked against
  the revised contract: WB-A (run-then-refuse / #295) → `test_a_hosted_mutating_tool_is_refused_and_its_body_never_runs`
  reds; WB-B (hand-list reach) → that pin + `test_served_intersection_refused_is_empty_for_a_hosted_member`
  red. Restore-clean re-run: correct build = **90 passed / 0 failed**.

- **(d) No NEW wrong build opened by the creds-seam refactor.** The seam threads TEST-STORE creds
  (via the wire `*_env` names + `_surreal_harness` root creds, monkeypatch-restored); it does NOT
  touch the composition's cred-RESOLUTION path (the build still calls `resolve_secret` /
  `resolve_config_value` — a build that resolved the WRONG var would still fail). It does not mask a
  real credential failure: the compose-unit/transport pins never dial the store (lazy construction),
  and the HOSTED WIRE path still performs REAL principal-DB admission against `ws://127.0.0.1:18000`,
  so a genuinely-broken credential there surfaces as a failed admission → 401 → a RED wire pin. The
  shared seam is one home (no fork), consistent with ONE-IMPLEMENTATION.

- **OBSERVATION-A (unchanged, still open for the BUILD leg):** the frozen wave-1 `LoreTokenVerifier`
  still lacks `super().__init__()`; my reference build supplies it (`super().__init__(required_scopes=None)`).
  The revised CONTRACT does not (and need not) address this — it is a build obligation the compose-unit
  pins DO surface (AttributeError until fixed). Lead ruling still wanted on edit-frozen-module vs adapt.
- **OBSERVATION-B (unchanged, minor):** the zero-outbound leg of the Origin pin remains
  non-discriminating (no bearer ⇒ no outbound on either build; the 403-vs-401 status leg carries it).
  Not a blocker; a one-line fixture upgrade (valid bearer + hostile Origin) would make it real.
