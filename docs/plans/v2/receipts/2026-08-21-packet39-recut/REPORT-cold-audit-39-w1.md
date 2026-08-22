# REPORT — cold-audit-39-w1 (packet 39 RE-CUT, wave-1 COLD AUDIT)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done** — VERDICT **GO**. I independently re-ran every gate and mutation-refuted the
  shipped build against the threat model. The build is correct; the 1 mypy error and 7 pytest-RED
  are correctly wave-3-adjudicated; removed-behavior is clean (keepers preserved & green).
- deviations: none (read-only auditor; my only writes are scratch probes + this report).
- **Packages considered:** none — no mechanism specified (audit only; I built no shipped symbol).
- **Reuse ledger:** none — I authored no shipped symbol (auditor builds only scratch instruments).
  The mutation-probe driver (a load-bearing instrument) is pasted VERBATIM in Appendix A per
  brief-base §1 (it lived in a disposable `/tmp` scratch).
- **Graded:** `50fb230` · HEAD-at-report: `50fb230` · **SAME** (build files untracked/staged, contract frozen; nothing moved under me).
- decisions-needed (none blocks the build; routed):
  - **R1 (CLOSE-OUT → LEAD):** the gate-currency check FAILS on 23 typecheck + 3 pytest **SELF-DESTRUCT** orphans — spent `packet-39-pending-build` registry bounds this wave's own work discharged. The lead MUST prune `scripts/pending_contracts.yaml` at commit (keep only the still-live `_auth_fixtures.py → build_mcp_server.http_client` bound; delete the rest). NOT a code defect; NOT in the builder's writable set.
  - **R2 (WAVE-3 → contract-author):** the deleted `GoogleOAuthConfig`/resource-path config-validation virtues (blank client_id fails closed; non-https resource URL refused) are dropped-deliberately (config = wave 3) and ARE on the contract's wave-3 deferred list — confirm they get re-pinned in wave-3's `OAuthProviderConfig`/`AuthConfig` contract. Tracked, not silently lost.
- receipt pointers: gate re-runs → §Gate re-runs; the 1-mypy refutation → §Refute-1; the 7-RED refutation → §Refute-2; threat-model probes → §Refute-3 (+ Appendix A driver); removed-behavior → §Removed-behavior; DRY → §DRY; currency → §Currency; E2 → §E2; verdict+residuals → §Verdict.

---

## §Capability check (brief-base §4)
Everything the brief demanded was satisfiable. The spike-surreal test store `ws://127.0.0.1:18000`
was reachable (every admission/contract pin ran live); `scratch_copy.sh` ran and ASSERTED provenance
(`loremaster.__file__ = /tmp/cold39w1_2097580/loremaster/loremaster/__init__.py`, INSIDE the scratch
root — a naive `cp` would have graded the ORIGINAL tree, #140); lore tools loaded via
`ToolSearch "+lore"`; `lore_comms` register/send worked. `Grep`/`Glob` are disabled session-wide, so
all textual sweeps used `git diff`/`grep`-in-`Bash` (legitimate dogfood §3b/c cases: non-symbol
textual seams + the diff frame the delete/reshape law requires — said out loud here). No impossibility.

**Tool honesty:** lore was used for the packet-39 rulings recall + `lore_get_symbol build_mcp_server`
(the one where-is question); everything else was direct `Read` of brief-named paths + `Bash` gates.

---

## §Gate re-runs (MY counts, not the builder's — live store `ws://127.0.0.1:18000`, `-n auto`)

| gate | command | MY result | builder claimed | verdict |
|---|---|---|---|---|
| wave-1 contract | `pytest test_token_verifier.py test_oauth_identity_seam.py -n auto` | **44 passed / 0 failed** (6.81s) | 44 passed | ✅ matches |
| normaliser | `pytest lorerunes/tests/test_email_normalisation.py -n auto` | **22 passed / 0 failed** (4.11s) | 22 passed | ✅ matches |
| ruff | `uv run ruff check .` | **All checks passed!** | clean | ✅ matches |
| typecheck | `bash scripts/typecheck.sh` | **1 error** (`_auth_fixtures.py:759`), lorerunes/lorescribe/loresigil/scripts all 0 | 1 (119→1) | ✅ matches — refuted §Refute-1 |
| test_auth | `pytest test_auth.py -n auto` | **7 failed / 26 passed** | 7 RED, 26 keepers green | ✅ matches — refuted §Refute-2 |
| #295 instrument | `pytest test_refusal_observes_effect.py -n auto` | **7 passed / 1 skipped** | green (kept) | ✅ still green |

All counts have a passed-COUNT in the tail (no "no tests ran" pipe-lie). Every gate reproduces the
builder/contract claims exactly.

---

## §Refute-1 — the 1 mypy error IS a genuine wave-3 forward-reference (NOT a masked live defect)

`loremaster/tests/_auth_fixtures.py:759` — `Unexpected keyword argument "http_client" for "build_mcp_server"`.

Refutation, four legs, all confirmed:
1. **The signature genuinely lacks the param** (not a mypy false-positive): `lore_get_symbol build_mcp_server` → `def build_mcp_server(server: LoreServer) -> Any` (`loremaster/loremaster/server.py:10259`). No `http_client` kwarg. mypy is correct.
2. **DEAD AT RUNTIME today.** Line 759 is the `posture == "hosted"` arm of a ternary in `wire_session` (`_auth_fixtures.py:758-762`). The SOLE live caller of `wire_session` across the whole test tree is `test_refusal_observes_effect.py:141`, which calls `wire_session(tmp_path, posture="loopback", principal=None, ...)` → the `else build_mcp_server(server)` arm. The hosted arm never executes today. Confirmed the #295 instrument is GREEN (7 passed / 1 skipped), so nothing exercises the dead arm at runtime.
3. **PRE-EXISTING, not introduced by this wave.** `git show HEAD:_auth_fixtures.py` carries the identical `build_mcp_server(server, http_client=spy.client())` call at line 872 (it moved to 759 only because E1b AST-removed orphaned entry points above it). RED before `50fb230`, RED after.
4. **The `type: ignore` was CORRECTLY refused.** A `# type: ignore[call-arg]` on 759 would silence mypy while MASKING the real signal that wave-3 composition must give `build_mcp_server` (or the verifier construction) the injected-`http_client` seam (design §4.3/§8). The adjudicated-red is the honest state.

**It IS owned (adjudicated, not orphaned).** `scripts/pending_contracts.yaml` `packet-39-pending-build`
(finding #306) registers `_auth_fixtures.py → build_mcp_server.http_client` (line 100), reopen trigger
"packet 39's build start … self-destructs as its file goes green at that build" — the wave-3 seam is
the closure. The currency tool did NOT list line 759 as an orphan (it still matches the bound), so
this red is correctly owned. ✅ REFUTED — genuine wave-3 forward-reference.

## §Refute-2 — the 7 test_auth pytest-RED ARE genuine wave-3 forward pins (pre-existing #333)

The 7 RED are `TestRetiredAuthSurfaceIsGone` (`AuthVerifier`/`BearerAuthMiddleware` × not-importable/not-exported = 4) + `TestAuthConfigRetiresTlsTerminatedUpstream` (× 3).

- They pin the recut's INTENDED wave-3 DELETION of the hand-roll gate + the `tls_terminated_upstream` flag. They are RED because the targets STILL EXIST: `auth.py:89 class AuthVerifier`, `auth.py:208 class BearerAuthMiddleware`, `config.py:395 tls_terminated_upstream: bool = True`.
- **This wave did NOT touch the code they pin.** `git status` shows `loremaster/loremaster/auth.py` and `config.py` UNCHANGED. So the wave cannot have broken them.
- **Pre-existing.** `git show HEAD:test_auth.py` carries all three classes (`RETIRED_AUTH_NAMES` line 64, `TestRetiredAuthSurfaceIsGone` line 108, `TestAuthConfigRetiresTlsTerminatedUpstream` line 444). E1a REDUCED test_auth RED 25→7 by retiring the stale-MODEL pins; these 7 forward pins survived on purpose. They go GREEN when wave-3 deletes the hand-roll. ✅ REFUTED — forward pins, not broken-by-this-wave.

## §Refute-3 — LoreTokenVerifier correctness (independent mutation probes on the SHIPPED build)

I ran 5 mutation probes against the **shipped** `token_verifier.py` / `lorerunes` (NOT the adversary's
reference build) in the provenance-asserted scratch copy. Each declared its RED node ids BEFORE the run
and paired every RED with a surviving positive CONTROL (a probe needs a control). Driver in Appendix A.

| # | property (threat model) | mutation on shipped code | declared-RED fired | control survived | verdict |
|---|---|---|---|---|---|
| A | `role → capability` is a real FUNCTION (anti-premature-RBAC; hosted read-only ∀ role) | `hosted_scopes_for_role` → `{read,write} if role=="admin"` | `test_hosted_admin_is_ALSO_read_only_regardless_of_role` RED | `test_hosted_member_gets_read_only_scope` GREEN | ✅ HELD |
| B | `lorerunes.normalize_email` is SHARED (admission ROUTES through it) | `normalize_email` → `return value` | loremaster `test_admission_normalisation_matches_a_lowercase_stored_principal` RED **AND** 12 lorerunes normaliser pins RED | (single-symbol mutation reddens BOTH members) | ✅ HELD |
| C | aud check is not decorative (rejects different-client token) | aud guard → presence-only (`if not aud:`) | `test_different_client_aud_is_denied` RED | `test_matching_aud_is_admitted` GREEN | ✅ HELD |
| D1 | `email_verified` accepts Google's STRING `"true"` | `_is_verified` → `value is True` | `test_email_verified_string_and_bool_representations` RED (1 of 5 params: the `"true"` admit) | 4 params GREEN | ✅ HELD |
| D2 | `email_verified` DENIES string `"false"` | `_is_verified` → `bool(value)` | `test_email_verified_string_and_bool_representations` RED (1 of 5 params: the `"false"` deny) | 4 params GREEN | ✅ HELD |

All 5 HELD. B is the ROUTING-IS-NOT-SHARING proof: mutating the ONE `lorerunes` symbol reddens a
loremaster admission pin, so admission genuinely CALLS the shared symbol (not a private copy). Every
mutation was restored byte-exact (driver asserts `read_text()==original`).

The remaining threat-model properties are covered by the 44/44 green contract + a direct source read
(no additional mutation needed — each is already discriminated by a pin the adversary proved catches
its wrong build):
- **token in POST body, never URL** — `_call_tokeninfo` uses `client.post(url, data={"access_token": token})` (`token_verifier.py:394`); pinned GREEN by `test_token_never_appears_in_the_request_url`.
- **401 negative-cached / 5xx fails-closed-not-cached-positive / malformed-not-cached** — split at `_call_tokeninfo:398-405` + `_verified_identity:357-360`; pinned GREEN by `test_401_is_negative_cached`, `test_5xx_is_not_cached`, `test_transient_5xx_then_success_admits`, `test_malformed_json_denied_and_not_cached`.
- **email_verified BEFORE principal lookup** — check at `_verified_identity:367` precedes `_admit`; pinned GREEN by `test_email_verified_false_is_denied_before_principal_lookup` (CountingPrincipalStore.lookup_calls==0).
- **active/suspended/expired denied; admission NEVER cached** — `_admit:460-463` (no cache); pinned GREEN by the suspended/expired pins + `test_admission_is_never_cached_suspend_takes_effect_next_request` (call_count==1 = verdict cached, second request denied = admission re-checked).
- **#206 per-principal mint routes `PrincipalKeyStore.verify`** — `verify_token:260`; pinned GREEN by `test_api_key_branch_routes_through_principal_key_store_verify` (monkeypatch verify→None ⇒ deny).
- **`agent_of` typed accessor, fail-closed** — `agent_of:160-183` reads `claims.get("agent")`, returns `None` when absent/unbound; pinned GREEN by `test_agent_of_is_the_typed_fail_closed_accessor` + `test_minted_identity_exposes_the_agent_binding_seam`.

---

## §Removed-behavior — INDEPENDENT enumeration + adjudication (contract-blind diff frame)

I enumerated the retired pins from the archived files (staged `R`) and the `git diff` of the two
modified test files myself — NOT from the builder's inventory — then adjudicated each virtue.

### Wholesale-archived files (6 loremaster + 2 lorerunes, `git mv` to `docs/plans/v2/receipts/2026-08-21-packet39-recut/`)
| archived file | virtue | adjudication |
|---|---|---|
| `test_google_token_verifier.py` | the OLD verifier contract (odoo-code port; `make_verifier`; `lorerunes.SCOPE_READ`/`is_admitted`) | **preserved-with-pin** → SUPERSEDED by the fresh `test_token_verifier.py` (44 pins, stronger) |
| `test_auth_composition.py` | SDK `mcp` composition + `derive_edge_policy` | **dropped-deliberately** (§9; composition = wave 3, standalone-fastmcp rewrite) |
| `test_auth_identity_seam.py` | SDK `StreamableHTTPSessionManager` wire-shadow class + `Posture` | **dropped-deliberately** (§9 R16 — middleware seam dissolves the wire-shadow class) |
| `test_permission_resolver_seam.py` | OLD `PermissionResolver` / `auth_context_from_access_token` | **dropped-deliberately** (not in recut design) |
| `test_hosted_readonly_posture.py` | OLD #295 posture on SDK `_setup_handlers` | **dropped-deliberately** (§9 R13/R16; wave-2 re-cuts #295 on the fresh middleware) |
| `test_allowlist_roster.py` | R12 flat-file roster | **dropped-deliberately** (§9 R12 DROPPED — admission is now the 48/49 `principal` DB) |
| `lorerunes/…/test_roster_parser.py` | R12 roster parser | **dropped-deliberately** (R12 DROPPED) |
| `lorerunes/…/test_posture.py` | OLD posture derivation (`derive_posture`/`SCOPE_READ`) | **dropped-deliberately, virtue deferred** — posture is KEPT in fresh design §6 (future lorerunes fn, NEW scope names) → wave-3 re-cut (builder E1c flagged; lead's call) |

Each archived file references ONLY retired-model symbols or a dropped design row. None carried a
keeper. Confirmed by the removed-name sweep being clean of live references (below).

### `test_auth.py` deleted pins (via `git diff HEAD`)
| deleted pin(s) | virtue | adjudication |
|---|---|---|
| `test_the_new_token_verifier_is_exported` / `..._satisfies_the_sdk_token_verifier_protocol` | the verifier is exported & satisfies the fastmcp `TokenVerifier` protocol | **preserved-with-pin** — the NEW verifier lives in `loremaster.token_verifier` (E4); the fresh contract subclasses `TokenVerifier` and drives `verify_token` 44× (behavioural protocol proof). The deleted pins targeted the retired `loremaster.auth.LoreTokenVerifier` (§9). |
| `TestGoogleOAuthConfigFailsClosed` (blank/missing client_id, blank roster, **non-https resource URL**, unknown-keys forbidden) | config fail-closed: a blank client_id / non-https resource URL is unconstructible | **dropped-deliberately (config = wave 3)** — `GoogleOAuthConfig` retired (§9); the virtue is on the contract's wave-3 deferred list (`OAuthProviderConfig`/`AuthConfig`). ⚠ **R2**: a real security virtue — MUST be re-pinned in wave 3 (tracked, not silently lost). |
| `TestLoreConfigCrossChecksTheResourcePath` (path match / mismatch refused / no-path refused) | resource-metadata path cross-check | **dropped-deliberately (wave 3)** — §13 group 6 `.well-known`/`resource_metadata=`; deferred. |

### `_auth_fixtures.py` deleted symbols (E1b, via `git diff HEAD`)
`rewrite_roster` (R12), `make_verifier` (OLD verifier factory → replaced by fresh `make_lore_token_verifier`),
`DEFAULT_API_KEYS`, `sdk_bound_handler_names` (SDK internals, §9 R13/R16), `as_principal` — all orphaned
entry points for the retired model. **Adjudication: dropped-deliberately** (dead model). The
model-AGNOSTIC core (`tokeninfo_payload`/`TokeninfoSpy`/`admitted_payload`/constants + the `wire_session`
harness) correctly STAYS — the live #295 instrument `test_refusal_observes_effect` imports `wire_session`
and is GREEN (verified). ✅

### Keepers — PRESERVED, GREEN, and STILL PINNING (the delete/reshape dual)
- `TestApiKeyVerifierIsPreservedVerbatim`: **constant-time** (`test_uses_constant_time_comparison` spies `auth.hmac.compare_digest`, asserts it is called — still discriminating), **all-keys-no-early-out** (timing-oracle pin), **empty-key** (`test_empty_token_returns_none`, `..._empty_configured_key_value_is_rejected_at_construction`, `..._add_empty_key_value_is_rejected...`), **SecretStr** (#211 — keepers hold keys as `SecretStr`; auth.py:115/157). All GREEN (26 passed).
- `TestBuildApiKeyVerifierFromConfig` (env read, fail-loud), `TestOriginValidationMiddlewareIsPreserved` (loopback/spoofed-loopback/malformed-ipv6-403-not-500). GREEN.
- `auth.py` is UNCHANGED this wave (git status), so these keepers pin untouched code — their green is a genuine preserved virtue, not an accident of the reshape.

**Removed-name sweep (my own, anchor-free):** `AuthVerifier`/`BearerAuthMiddleware` residuals = the LIVE
current LAN gate in `auth.py`/`server.py` + its live tests (deferred to wave 3, brief-directed — not
broken). `GoogleOAuthConfig`/`make_verifier`/`SCOPE_READ`/`Posture`/`derive_edge_policy`/`PermissionResolver`
= zero LIVE references after the archival (they lived only in the archived files / adjudicated stale
tests). No production change introduces a retired-name reference. ✅

---

## §DRY / reuse (verified)
- **`cachetools.TTLCache`**, not a hand-rolled dict-with-timestamps — `token_verifier.py:79,244` (`TTLCache(maxsize=…, ttl=…, timer=self._clock)`). ✅
- **shared `lorerunes.normalize_email`** — mutation probe B proves admission routes through the ONE symbol (loremaster admission pin reds when the lorerunes symbol is mutated). ✅
- **`role → capability` FUNCTIONS in `lorerunes`** (`scopes.py` `hosted_scopes_for_role`/`lan_scopes_for_role`), imported by the verifier — probe A proves it is a real function (hardcoding `admin ⇒ +write` reds the anti-premature-RBAC pin). ✅
- **`sha512_hex` reused** for the cache key (not a hand-rolled `hashlib` clone, #102/#120) — `token_verifier.py:82,344`. ✅

---

## §Currency — the gate-currency check (a CLOSE-OUT item, not a code defect)
`uv run python scripts/pending_contract_gate.py --currency` → **FAIL** (typecheck RED_ORPHANED 23,
pytest RED_ORPHANED 3, ruff GREEN). **Every one of the 26 orphans is a `SELF-DESTRUCT`** — a
`packet-39-pending-build` registry bound that THIS wave's own work discharged:
- archived files (`test_allowlist_roster.py`, `test_auth_composition.py`, …) → "does not exist / produced NO mypy errors — DELETE its registry entry";
- `test_auth.py` → "produced NO mypy errors" (E1a cleaned it 6→0);
- `lorerunes.normalize_email` (3 sites) → "now RESOLVES — the bound is discharged".

This is the registry mechanism working as DESIGNED (its reopen trigger: "each entry self-destructs as
its file goes green at that build"). It is **NOT** a fresh red-with-nobody's-name (the disease the
check hunts), and the one genuinely-live red (`_auth_fixtures.py:759`) is still OWNED. **R1 (→ LEAD):**
prune `scripts/pending_contracts.yaml` at commit — delete the discharged entries, keep only
`_auth_fixtures.py → build_mcp_server.http_client` (the live wave-3 forward bound) — so the next session
inherits a PASS/RED_ADJUDICATED currency check, not a stale FAIL. Outside the builder's writable set.

## §E2 — the flagged api-key write-scope reading is CORRECT per the ratified design
The build mints `{lore:read, lore:write}` for LAN/api-key principals (reading A). The ratified design
banner (`docs/design/2026-08-21-packet39-recut-oauth.md:35-59`) GOVERNS and states: hosted = READ-ONLY
for member AND admin; "LAN api-keys keep full write (F7 role-gating deferred to RBAC)"; "THIS BANNER
GOVERNS" on any disagreement. The stale role-gated text in the body (§3.3 line 257, F4/F7) is
explicitly superseded. The contract author's E2 flag was correct diligence; the build implemented the
banner-governed reading. **No defect.** (`test_api_key_principal_keeps_full_write` correctly pins write.)

---

## §Verdict — **GO**

Wave 1 is correct and ready to commit. Gates re-run green (my counts: contract 44/0, normaliser 22/0,
ruff clean); the 1 mypy error and 7 pytest-RED are genuine, pre-existing, correctly-adjudicated wave-3
forward references (not masked live defects, `type: ignore` correctly refused); every threat-model
property mutation-refuted against the shipped build with controls; removed-behavior independently
enumerated and clean (keepers preserved & green, deletions adjudicated, #295 instrument green); DRY
seams proven shared by mutation; E2 matches the ratified design banner.

### Residual table (each defect + where it routes) — none blocks the build
| # | severity | item | routes to |
|---|---|---|---|
| R1 | close-out (must-do at commit) | gate-currency FAILs on 26 SELF-DESTRUCT orphans (spent `packet-39-pending-build` bounds discharged by this wave); prune `scripts/pending_contracts.yaml`, keep only the live `build_mcp_server.http_client` bound | **LEAD** (registry owner; not in builder writable set) |
| R2 | wave-3 (confirm re-pin) | deleted config fail-closed virtues (blank client_id / non-https resource URL refused; resource-path cross-check) are dropped-deliberately (config = wave 3) — ensure re-pinned in wave-3's `OAuthProviderConfig`/`AuthConfig` contract | **contract-author (wave 3)** — already on the deferred list; tracked |
| — | informational | E1a/E1b/E1c/E1d escalations (test_auth split, `_auth_fixtures` part-retirement, lorerunes posture re-cut, frozen-contract annotations) already surfaced by builder+contract; E1d resolved (contract annotated behaviour-preserving); E2/E3/E4 resolved | **LEAD** to disposition E1a–E1c at close-out |

Scratch copy `/tmp/cold39w1_2097580` is disposable (`scratch_copy.sh`) — discard after reading; nothing
durable lives only there (the driver is in Appendix A).

---

## Appendix A — the mutation-probe driver (verbatim; the §Refute-3 instrument)
Ran at `/tmp/cold39w1_2097580/run_cold_mutations.py` (scratch, provenance-asserted). Each probe: back up
bytes → one `str.replace` (SystemExit if the anchor is absent — no silent no-op, #194) → run declared-RED
node(s) + control → restore byte-exact + assert restore. Declared-RED node ids fixed BEFORE the run.

```python
"""Cold-audit mutation probes against the SHIPPED build (packet 39 wave 1)."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCOPES = ROOT / "lorerunes/lorerunes/scopes.py"
NORM = ROOT / "lorerunes/lorerunes/email_normalisation.py"
TV = ROOT / "loremaster/loremaster/token_verifier.py"
TEST_TV = "loremaster/tests/test_token_verifier.py"
TEST_NORM = "lorerunes/tests/test_email_normalisation.py"

def run_node(node: str) -> bool:
    proc = subprocess.run(
        ["uv","run","python","-m","pytest",node,"-q","-p","no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True)
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    ok = proc.returncode == 0
    print(f"      [{'PASS' if ok else 'FAIL'}] {node.split('::')[-1]}  ::  {tail}")
    return ok

def mutate(path: Path, old: str, new: str) -> str:
    src = path.read_text()
    if old not in src:
        raise SystemExit(f"ANCHOR ABSENT in {path.name}: {old!r}")
    path.write_text(src.replace(old, new, 1)); return src

def restore(path: Path, original: str) -> None:
    path.write_text(original)
    assert path.read_text() == original, f"restore failed for {path}"

def probe(name, path, old, new, expect_red, expect_green) -> bool:
    print(f"\n=== {name} ===")
    original = mutate(path, old, new)
    try:
        red_ok = True
        print("  declared-RED (must FAIL under mutation):")
        for node in expect_red:
            if run_node(node): red_ok = False
        print("  control-GREEN (must PASS under mutation):")
        green_ok = True
        for node in expect_green:
            if not run_node(node): green_ok = False
    finally:
        restore(path, original)
    verdict = red_ok and green_ok
    print(f"  --> {name}: {'HELD' if verdict else 'PROOF FAILED'}")
    return verdict

results = {}
results["A role->cap function"] = probe(
    "A. hosted_scopes_for_role hardcodes admin=+write", SCOPES,
    "    return frozenset({LORE_READ})\n\n\ndef lan_scopes_for_role",
    '    return frozenset({LORE_READ, LORE_WRITE}) if role == "admin" else frozenset({LORE_READ})\n\n\ndef lan_scopes_for_role',
    [f"{TEST_TV}::TestMintedIdentityCarriesRoleAndSeams::test_hosted_admin_is_ALSO_read_only_regardless_of_role"],
    [f"{TEST_TV}::TestMintedIdentityCarriesRoleAndSeams::test_hosted_member_gets_read_only_scope"])
results["B shared normaliser routing"] = probe(
    "B. normalize_email -> identity (no fold)", NORM,
    'return unicodedata.normalize("NFKC", value).casefold().strip()', "return value",
    [f"{TEST_TV}::TestAdmission::test_admission_normalisation_matches_a_lowercase_stored_principal", f"{TEST_NORM}"],
    [])
results["C aud vs client_id"] = probe(
    "C. aud check -> presence-only", TV,
    "if not aud or aud != self._google_client_id:", "if not aud:",
    [f"{TEST_TV}::TestGoogleVerification::test_different_client_aud_is_denied"],
    [f"{TEST_TV}::TestGoogleVerification::test_matching_aud_is_admitted"])
results["D1 email_verified is-True"] = probe(
    "D1. _is_verified -> `value is True` only", TV,
    'if value is True:\n        return True\n    return isinstance(value, str) and value.strip().lower() == "true"',
    "return value is True",
    [f"{TEST_TV}::TestAdmission::test_email_verified_string_and_bool_representations"], [])
results["D2 email_verified bool()"] = probe(
    "D2. _is_verified -> `bool(value)`", TV,
    'if value is True:\n        return True\n    return isinstance(value, str) and value.strip().lower() == "true"',
    "return bool(value)",
    [f"{TEST_TV}::TestAdmission::test_email_verified_string_and_bool_representations"], [])

print("\n\n=========== SUMMARY ===========")
for k, v in results.items():
    print(f"  {'HELD ' if v else 'FAILED'} :: {k}")
sys.exit(0 if all(results.values()) else 1)
```

**Observed output (all 5 HELD):**
```
A. hosted_scopes_for_role hardcodes admin=+write: HELD  (admin pin FAIL, member control PASS)
B. normalize_email -> identity: HELD  (loremaster admission pin FAIL + 12 lorerunes pins FAIL)
C. aud check -> presence-only: HELD  (different-client FAIL, matching-aud control PASS)
D1. _is_verified -> `value is True`: HELD  (email_verified param FAIL 1/5, 4 PASS)
D2. _is_verified -> `bool(value)`: HELD  (email_verified param FAIL 1/5, 4 PASS)
```
