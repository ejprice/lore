# REPORT — cold-audit-39-w23 (packet 39 RE-CUT, wave 2+3 COLD AUDIT)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done** — independently re-ran every gate + mutation-refuted the security boundary on
  the SHIPPED build. **VERDICT: GO.**
- **VERDICT: GO** — gates GREEN (re-run by me, counts below); currency gate PASS (empty-registry
  pass-through, no RED_ORPHANED); the read-only guard security boundary is mutation-SOLID (all 4
  wrong-builds caught, each reddening exactly its discriminating pin, restore byte-identical); the
  5 out-of-writable-set fixes are each correct + narrow + directly-caused; removed-behavior is
  fully accounted for and the removed-name sweep is clean.
- deviations: none in my own work (read-only auditor; only writable artifact = this report +
  disposable `/tmp` scratch).
- **Packages considered:** none — no mechanism specified (I graded; I shipped no code). I READ
  `fastmcp==3.4.7` installed behaviour (`FastMCP(auth=)` = server-side incoming provider) and the
  `PrincipalKeyStore.verify`/`mint` source to settle the migration-wire hashing claim — verdicts
  from READ source, not expectation.
- **Reuse ledger:** none — I authored no shipped symbols.
- **Graded:** `feea77a9b8067e5fccbfee1354583cc31a0ad5e0` · HEAD-at-report:
  `feea77a9b8067e5fccbfee1354583cc31a0ad5e0` · **SAME**. Tree UNCOMMITTED (24 changed/untracked,
  the build per the brief). All three prior reports (builder/adversary/contract) graded the same sha.
- decisions-needed (for the lead — NONE block the GO; each is a disclosed disposition already
  surfaced by the builder/contract):
  1. **Ratify the 5 out-of-writable-set fixes.** I confirm all 5 correct/narrow/directly-caused;
     the ratification decision itself is the lead's (§3).
  2. **`config.keys` / `ApiKeyVerifier` / `build_api_key_verifier` disposition** (delete vs
     keep-with-pin vs add a migration-reject like `tls_terminated_upstream` got). Genuinely
     orphaned from the auth path; cleanly disclosed. Operator/scope call (§4, R2).
  3. **OBSERVATION-A** (the one wave-1 `token_verifier.py` edit, `super().__init__`) touched a
     "frozen" module — RULED authorized by the contract (note-for-builder); wave-1 stays green
     (41p). Confirmed benign; flagged for lead awareness (§5).
- receipt pointers: gate re-runs → §1; guard mutation-refute table → §2; the 5-fix scrutiny →
  §3; removed-behavior adjudication → §4; observations/residuals → §5; scratch provenance → §0.

---

## §0. Scratch provenance (#140)
Security-boundary wrong-builds constructed in `./scripts/scratch_copy.sh /tmp/cold39-scratch`
(provenance asserted by the tool). Printed receipt:
```
loremaster  -> /tmp/cold39-scratch/loremaster/loremaster/__init__.py
lorerunes   -> /tmp/cold39-scratch/lorerunes/lorerunes/__init__.py
```
Both resolve UNDER the scratch root — the mutations grade the scratch tree, not the original. The
uncommitted build files (readonly_guard.py, posture.py, the new contract test files) came across
(verified `ls`). Baseline `test_readonly_guard.py` in scratch = **8 passed** (correct-build
positive control). Guard file restored byte-identical after mutations (`diff -q` clean). Test store
`ws://127.0.0.1:18000` (spike, systemd `active`); never `:18500`. `/tmp/cold39-scratch` is a
disposable scratch-copy tree — left for lead inspection, safe to discard.

---

## §1. Gates — RE-RUN BY ME (not trusted from the reports)

| gate | my command | result |
|---|---|---|
| **wave-2/3 contract** (6 files) | `pytest -q -n auto test_auth_config_recut + test_auth + test_auth_composition_recut + test_readonly_guard + test_auth_composition_wire + lorerunes/test_posture` | **90 passed / 0 failed** in 7.00s |
| **wave-1 contract** | `pytest -q -n auto test_token_verifier.py` | **41 passed** in 6.88s (super().__init__ did NOT change verify_token) |
| **loopback #295 instrument** | `pytest -q test_refusal_observes_effect.py` | **7 passed / 1 skipped** — byte-identical to the cold-audit baseline |
| **typecheck** | `./scripts/typecheck.sh` | **exit 0** — every member OK (lorerunes/lorescribe/loresigil/loremaster/skills/docs·eval/scripts/shellcheck), ZERO errors |
| **ruff** | `uv run ruff check .` | **All checks passed!** |
| **currency gate** | `python scripts/pending_contract_gate.py --currency` | **CURRENCY: PASS — every claimed gate is GREEN or OWNED** (typecheck GREEN · ruff GREEN · pytest GREEN); exit 0 |
| **migration wire** | `pytest -q -m wire test_migration_wire.py` | **14 passed** in 27.26s |

- The wave-2/3 count (90/0) matches the builder + contract claims exactly.
- **The currency-gate `pytest` leg is the FULL suite** — its command (`scripts/gates.yaml` id
  `pytest`) is `uv run pytest -q -n auto -o junit_family=xunit1 --junit-xml=…` with **no
  `-m "not wire"`** and pyproject `addopts` is only `--import-mode=importlib`, so wire-marked tests
  are INCLUDED. `pytest GREEN` ⇒ the entire tree (~8779 tests, wire included) passes. **There are
  NO unrelated failures.**
- The pending bound is genuinely discharged: `uv run mypy loremaster/tests/_auth_fixtures.py` →
  `Success: no issues found`, **0** `http_client` occurrences (§3, fix #4).
- `partition_tools_by_posture` (server.py:10578) confirmed **deny-by-default** by reading its
  source: `readOnlyHint is True → read_only; else (None or False) → mutating`. The guard routes
  ALL classification through it (`readonly_guard._partition_mutating` → `partition_tools_by_posture`),
  so the deny-by-default property is genuinely shared, not re-spelled.

---

## §2. SECURITY BOUNDARY — mutation-refute on the SHIPPED guard (`readonly_guard.py`)

Method: 4 wrong-build variants applied to the scratch `readonly_guard.py` via an exact-match,
count-asserted mutator (a silently-missed mutation cannot masquerade as a passing pin). Each mutation
→ run `test_readonly_guard.py` → restore. Baseline (correct build) = **8 passed** (positive control).

| # | wrong build | pins reddened | verdict |
|---|---|---|---|
| **MUT1** run-then-refuse (`call_next` BEFORE the raise — #295 EFFECT) | `test_a_hosted_mutating_tool_is_refused_and_its_body_never_runs` + `test_an_unclassified_tool_is_denied_by_default_for_a_hosted_member` (both EFFECT legs — body ran, counter==1) | **2 failed / 6 passed** — CAUGHT. The raise-before-`call_next` placement is load-bearing. |
| **MUT2** hand-list reach (`_partition_mutating` returns a hardcoded built-in set, ignores the live registry) | `..._body_never_runs` + `..._unclassified_denied` + `test_served_intersection_refused_is_empty_for_a_hosted_member` + `test_one_annotation_flip_moves_a_tool_across_guard_and_list` | **4 failed / 4 passed** — CAUGHT. Reach is registry-derived (coverage is a checked variable). |
| **MUT3** refuse-but-visible (`on_list_tools` never filters) | `..._unclassified_denied` + `..._served_intersection…` + `..._one_annotation_flip…` | **3 failed / 5 passed** — CAUGHT. The invisibility (structural) leg is enforced. |
| **MUT4** `readOnlyHint is False` hole (hand-rolled classify, NOT the shared deny-by-default partition — ROUTING-IS-NOT-SHARING) | **exactly** `test_an_unclassified_tool_is_denied_by_default_for_a_hosted_member` | **1 failed / 7 passed** — CAUGHT, and ONLY that pin (no over-pinning). The adversary's finding #2, closed and discriminating. |

Restore verified byte-identical (`diff -q` clean). The specific brief demands, all confirmed:
- **Guard refuses BEFORE `call_next` (raise-first):** confirmed by MUT1 (the run-then-refuse
  inverse reddens on `effect_count()==1`), and by reading `on_call_tool` (raises `_refusal` before
  `call_next`).
- **HOSTED_OAUTH: every mutating tool refused + invisible to every hosted principal:** the baseline
  wire pins (`..._body_never_runs`, `..._served_intersection…`, `..._unclassified_denied`) pass on
  the correct build; a hosted member (no `lore:write`) is refused + cannot see the synthetic mutating
  tool. Built-in mutating tools are covered TRANSITIVELY (reach = full registry via
  `list_tools(run_middleware=False)`, classification = deny-by-default partition; MUT2 proves the
  reach is not a hand-list). Observation on the transitive coverage in §5-R5 (not a defect).
- **Read-only tool served + body-runs (positive control):**
  `test_a_read_only_tool_is_visible_and_its_body_runs` (counter==1) — proves the harness SEES a body
  execute, so the refused pins' `counter==0` is a real observation, not a dead harness.

---

## §3. THE 5 OUT-OF-WRITABLE-SET FIXES — scrutinized

### Fix #2 — `test_secret_typing.py` R26 exemption for `FastMCP(auth=…)` — **CORRECT + NARROW**
The exemption `_is_fastmcp_server_auth(node)` skips a `Call` node whose callee name == `FastMCP`.
- **Correct:** `FastMCP(auth=…)` is the fastmcp SERVER constructor — `auth=` is an INCOMING token
  verifier/provider, never an outgoing credential/header. Production usage is `server.py:10504`
  (`mcp: FastMCP = FastMCP(...)`), the server. No outgoing `httpx.Client(auth=)` exists in
  `server.py`. R26 constraint 2 excludes incoming auth by design.
- **Narrow — adversarially probed** (I ran the scanner over 7 crafted snippets):
  - FLAGGED (positive controls, gate still sees leaks): `httpx.Client(auth=cred)`,
    `httpx.AsyncClient(headers=hdr)`, bare `Client(auth=cred)`.
  - clean (correctly exempt): `FastMCP(auth=verifier)`.
  - FLAGGED (near-miss callee, exact-name not prefix): `FastMCPClient(auth=cred)`.
  - The R26 gate suite = **69 passed** (incl. its own positive controls at
    `test_the_leak_detector_can_actually_see_a_leak` and the `httpx.Client(auth=BasicAuth)` fixture).
- Two minor WIDENESS notes (§5-R1) — theoretical, no real leak path: (a) it skips the WHOLE call
  node, so a hypothetical `FastMCP(headers=leak)` would be missed — but no outgoing HTTP flows
  through the server constructor; (b) `func.attr == "FastMCP"` also exempts `mod.FastMCP(...)`.
  Under the honest-developer threat model neither is a defect: no outgoing credential is ever
  routed through a FastMCP server constructor. **This is a PATTERN exemption replacing the
  pre-existing PATH exemption (`_FASTMCP_SPIKE_EXEMPT`) — narrower than blinding a whole module.**

### Fix #3 — `test_migration_wire.py` LAN auth harness (mint a `principal_key`) — **DESIGN-CONSISTENT + GENUINELY AUTHENTICATES (not a masked pass)**
The re-cut moved LAN api-key auth off `config.keys` → the `principal_key` table
(`LoreTokenVerifier`/`PrincipalKeyStore.verify`, design §3.3/§4.1). The harness now pre-creates a
`role="member"` principal + mints its key.
- **Hashing consistency (the masked-pass risk) — CLEARED by reading both methods:** `mint` takes
  `secret_hash = sha512_hex(_DEV_KEY)` where `_DEV_KEY = "dev:wire-dev-secret-59"` (the full
  `name:secret`); `PrincipalKeyStore.verify` (principal_keys.py:494) hashes the **WHOLE presented
  string** (`sha512_hex(presented)`, docstring: "sha512_hex the WHOLE presented string") and looks
  up `WHERE hash = $h`. Same input, real match. The presented bearer IS `_DEV_KEY`, so it resolves.
- **Real admission, not a bypass:** verify splits on the first colon, rejects blank halves,
  re-checks revoked/expired/principal-active against a single `now`. The wire genuinely gates.
- **Negative control present:** `test_a_bad_bearer_token_is_rejected_401` posts `"not-the-dev-key"`
  → `verify` → `partition(...":")` no colon → `_deny("malformed-no-colon")` → 401. Confirmed by the
  14-passed run (includes this pin) + the re-cut failure message now names `FastMCP(auth=…)` as the
  live gate (not the retired BearerAuthMiddleware).
- **Mutating smoke tools run over LAN** because a LAN member api-key carries `lore:write` (wave-1
  `test_api_key_principal_keeps_full_write` — 1 passed; matches the guard docstring "LAN_BEARER
  api-key principals carry lore:write"). Consistent with the READ-ONLY-hosted re-cut (LAN full-write
  for every role; role-gated write deferred to packets 60-65).
- ⚠ This is a ~40-line auth-harness change in an end-to-end wire smoke NOT in the builder's writable
  set; it is directly-caused, disclosed, and correct. Ratification is the lead's (decision-needed #1).

### Fix #4 — `pending_contracts.yaml` → `bounds: []` — **GENUINE SELF-DESTRUCT + designed pass-through**
- `packet-39-pending-build` was the **SOLE** bounds entry (git diff: only that one id removed,
  `bounds:` → `bounds: []`). Its named reopen_trigger ("wave 3 wires `build_mcp_server(http_client=)`")
  fired — this wave wired it — so the premise (the `_auth_fixtures.py` mypy error) is gone.
- Premise genuinely discharged: `mypy _auth_fixtures.py` → 0 errors, 0 `http_client` occurrences.
- Empty-registry = designed pass-through: confirmed by the **currency gate PASS** (no RED_ORPHANED)
  AND by the gate's own self-test `test_an_EMPTY_registry_degrades_to_a_pass_through` (green, §fix#5).
  Deletion-on-self-destruct is the file's own instructed law.

### Fix #5 — `test_pending_contract_gate.py` fixture rename `Posture` → `FixturePlaceholder` — **SEMANTICS-PRESERVING**
- Why needed: the fixture used `lorerunes.Posture` as an example "must-never-resolve missing
  symbol"; this wave BUILT `lorerunes.Posture`, so it began resolving and flipped 4 healthy-verdict
  fixtures to self-destruct (the gate's liveness check `import_module` + `hasattr`).
- Rename is whole-file, case-sensitive, and preserves each discriminator: `PostureRefusal` →
  `FixturePlaceholderRefusal` (substring test intact — `FixturePlaceholder` ⊂ `FixturePlaceholderRefusal`);
  `loremaster.config.Posture` → `…FixturePlaceholder` (same-name-different-owner test intact).
- **`FixturePlaceholder` genuinely never resolves:** `import lorerunes; 'FixturePlaceholder' in
  dir(lorerunes)` → **False** (`Posture` → True, confirming the rename was necessary). A
  "MUST NEVER RESOLVE" note added so a future packet doesn't re-hit the fragility.
- Gate self-tests: **41 passed** (file-only match / substring / count cross-check / dotted-owner /
  self-destruct / empty-pass-through all still tested).

### Fix #1 — `test_mcp_server.py::TestAuthWiring` re-cut — **CORRECT (DUAL-law corpse → new truth)**
The 2 pins asserted `isinstance(app, BearerAuthMiddleware)` (deleted class → ImportError). Re-cut to
the new truth: no-auth → `mcp.auth is None` + `isinstance(app, OriginValidationMiddleware)`;
enabled-auth → `mcp.auth is not None` + `isinstance(app, OriginValidationMiddleware)`. Not a
weakening — the per-posture `mcp.auth` SHAPE is pinned in detail in `test_auth_composition_recut.py`
(part of the 90-green); this keeps the `build_asgi_app` (Origin-outermost) view. Directly-caused,
minimal, disclosed.

---

## §4. REMOVED-BEHAVIOR — contract-blind enumeration + adjudication

I enumerated the deleted code's behaviours from the `auth.py`/`config.py` DIFFS (frame = "what did
the deleted code do that this doesn't?"), independently of the contract's inventory:

| removed unit | behaviour it provided | verdict + receipt |
|---|---|---|
| `BearerAuthMiddleware` | gate every HTTP request on a valid Bearer key; 401 before the app runs (fail-closed) | **dropped-and-replaced** by `FastMCP(auth=LoreTokenVerifier)` — 401-on-bad-credential is now fastmcp's BearerAuthBackend. Pinned: `test_migration_wire::test_a_bad_bearer_token_is_rejected_401` (ran, in the 14p) + `test_auth_composition_wire::test_unauthenticated_post_401_carries_resource_metadata` (in the 90p). |
| " | the `401 + WWW-Authenticate: Bearer realm="loremaster"` challenge | **dropped-and-IMPROVED** — the re-cut 401 now carries RFC 9728 `resource_metadata=` (the old hand-roll did NOT). Pinned by `test_unauthenticated_post_401_carries_resource_metadata`. |
| " | non-HTTP (lifespan) scopes pass through untouched | **moot under the new architecture** — auth is no longer an ASGI wrapper; fastmcp handles its own lifespan. Real sessions establish (migration/composition wire pins), so startup is unaffected. |
| " | the presented key value is never logged | **preserved** — `PrincipalKeyStore.verify` launders the denial REASON to DEBUG, never the raw credential (design §F3a; read the source). |
| `ApiKeyVerifier` constant-time compare (`hmac.compare_digest`) | anti-timing-oracle secret match | **preserved by a different (sound) mechanism** — the recut path hashes the presented credential (`sha512_hex`) and looks it up by hash index; the store never sees the raw secret. The anti-timing-oracle property survives. |
| `AuthVerifier` ABC | the pluggable verifier seam | **dropped** — replaced by fastmcp's `TokenVerifier` protocol; its docstring's "rides the same BearerAuthMiddleware" claim was always false under standalone-fastmcp (old-bug-not-re-pinned). Absence pinned by `test_auth::TestRetiredAuthSurfaceIsGone`. |
| `config.auth.tls_terminated_upstream` | recorded the TLS-terminated-upstream transport axis | **dropped-and-wired** — fastmcp native `host_origin_protection` covers it; a config still carrying it fails LOUD + REMEDIABLY (config.py:492 migration validator). Pinned by `test_auth::TestAuthConfigRetiresTlsTerminatedUpstream`; corpse `test_config::test_tls_terminated_upstream_flag_defaults_true` retired with the field removal. |
| `OriginValidationMiddleware` (KEPT) | DNS-rebinding Origin allow-list; 403 before credential parse; allows absent Origin + loopback | **kept, now OUTERMOST** (design §6/§8). Pinned by `test_auth::TestOriginValidationMiddlewareIsPreserved` + `test_auth_composition_wire::test_disallowed_origin_is_403_with_zero_outbound_provider_calls`. (Adversary OBSERVATION-B on the zero-outbound leg — §5-R3.) |

**Removed-name anchor-free sweep (my own `grep`, bare patterns over `loremaster/loremaster`,
`loremaster/tests`, `lorerunes`, `scripts`; `.venv`/archives excluded).** `Grep`/`Glob` are disabled
session-wide, so I used `grep`-in-`Bash` (said out loud). Every residual hit adjudicated individually
(no "all remaining hits are X"):
- `BearerAuthMiddleware`: all hits are retirement/migration PROSE (auth.py:17, server.py:10496/12516/12557),
  the ABSENCE contract + `__all__` retirement list (test_auth.py:11/55/69/117/141), stub-vs-build
  historical discrimination in frozen contract tests (test_readonly_guard:103/129,
  test_auth_composition_wire:7/85/92/98/112/120/134/166, _auth_fixtures:426/881), the re-cut failure
  MESSAGE naming `FastMCP(auth=)` as live (test_migration_wire:79/537), and
  `scripts/fastmcp_migration_spike.py:56/114/265` — a self-contained HISTORICAL spike with its OWN
  local `class BearerAuthMiddleware` (NOT a reference to the deleted `loremaster.auth` symbol;
  `scripts` typechecks clean). ✅ No live reference teaches a retired name as the current mechanism.
- `AuthVerifier`: only retirement prose (auth.py:18) + the absence contract (test_auth.py). ✅
- `tls_terminated_upstream`: retirement prose + the migration validator naming the field to REJECT it
  (config.py:492-497) + the retirement pins + the corpse-retirement comment (test_config.py:400-401).
  ✅ No live field; a config still carrying it fails loud.

---

## §5. Observations & residuals (NONE block the GO)

- **R1 — R26 exemption wideness (minor, no leak path).** `_is_fastmcp_server_auth` skips the whole
  call node (not just `auth=`) and matches `func.attr == "FastMCP"` too. No outgoing credential
  flows through a FastMCP SERVER constructor, so neither admits a real leak under the
  honest-developer threat model. A tighter form would skip only `auth=` on a bare `FastMCP` id. Not
  a blocker.
- **R2 — `config.keys` / `ApiKeyVerifier` / `build_api_key_verifier` orphaned from the auth path.**
  My check: their ONLY production references are WITHIN `auth.py` itself (`build_api_key_verifier`
  instantiates `ApiKeyVerifier` and reads `config.keys`); no external production consumer remains
  (`build_asgi_app` dropped the BearerAuthMiddleware that called them). `config.keys` is still a
  parseable field, read only by the now-orphaned builder. This is genuine kept-but-unwired dead code,
  correctly disclosed as an operator disposition (builder decision-needed #2). ⚠ A live `lore.yaml`
  with `mode: api_key` + `keys:` now silently does NOT authenticate via `config.keys` (LAN auth is
  principal_key). Consider whether that warrants a migration-reject (as `tls_terminated_upstream`
  got) or explicit deletion — a design/operator call, not a wave defect.
- **R3 — Origin pin zero-outbound leg is non-discriminating** (adversary OBSERVATION-B, confirmed).
  `test_disallowed_origin_is_403_with_zero_outbound_provider_calls` sends a hostile Origin with NO
  bearer, so no outbound tokeninfo call happens on either build — the `call_count==0` leg passes
  vacuously; the real discriminator is the 403-vs-401 STATUS (Origin-outermost), which works. A
  one-line fixture upgrade (valid bearer + hostile Origin) would make the "zero outbound" property
  real. Minor; the status leg carries the pin.
- **R4 — OBSERVATION-A (wave-1 `token_verifier.py` edit).** `super().__init__(required_scopes=None)`
  was added to `LoreTokenVerifier.__init__` so it composes into `FastMCP(auth=)`/`RemoteAuthProvider`.
  This touched a module the wave-1 adversary graded SUFFICIENT ("frozen"). The contract RULED this
  authorized (integration adaptation, note-for-builder). I confirm wave-1 stays green (41 passed
  before AND after — the builder measured both ways; my re-run = 41 passed) and `verify_token`
  behaviour is unchanged. Benign; flagged for lead awareness.
- **R5 — built-in mutating tools are covered TRANSITIVELY, not by a direct wire EFFECT pin.** The
  wire EFFECT pins observe SYNTHETIC tools (built-in bodies need the live AppContext — the documented
  #295 pattern). Built-in coverage rests on: reach = full registry (MUT2 proves it is not a
  hand-list) × deny-by-default classification (MUT4 + the None-pin) × the partition being separately
  pinned correct (`test_mutating_set_derivation`/`test_mcp_server`). The transitive argument is sound
  (the adversary accepted it as P1c-adequate). Noted, not a defect.

---

## §6. VERDICT: **GO**

Gates GREEN (re-run by me: wave-2/3 90/0, wave-1 41, loopback 7p/1s, typecheck 0, ruff clean,
currency PASS, migration wire 14) with the FULL suite (wire included) green — no unrelated failures.
The read-only enforcement guard — the security boundary this wave IS — is mutation-SOLID: all 4
wrong-builds (run-then-refuse / hand-list reach / refuse-but-visible / `readOnlyHint is False`
deny-by-default hole) are caught, each reddening exactly its discriminating pin, and the #295 EFFECT
(body-never-runs) discipline holds. The 5 out-of-writable-set fixes are each correct + narrow +
directly-caused (the R26 credential-leak exemption adversarially probed; the migration-wire auth
proven consistent and not a masked pass). Removed-behavior is fully accounted for and the
removed-name sweep is clean. No residual blocks the commit; the three decisions-needed are disclosed
dispositions the lead/operator owns.
