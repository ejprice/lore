# REPORT — contract-39-w1b (packet 39 re-cut, WAVE-1 CLOSE-OUT)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — currency AFTER confirmed `CURRENCY : PASS`, ZERO RED_ORPHANED (§Currency)
- mission: retire the 7 PREMATURE wave-3 forward pins from `loremaster/tests/test_auth.py` that the currency gate flagged RED_ORPHANED; preserve the still-valid keepers; clean orphaned constants/imports/docstring; file the wave-3 re-cut obligation. Do NOT commit.
- deviations:
  - Renamed test class `TestRetiredAuthSurfaceIsGone` → `TestKeptAuthSurfaceIsExported` (re-home of the surviving kept-names export check). Disclosed; no cross-module consumer (grep-confirmed).
  - FLAG (not edited — out of the "keep untouched" set): 4 residual `Design §8 row N` citations in the KEEP-untouched keeper classes point at the OLD 2026-07-31 doc's inventory, not the re-cut's §9. Left untouched per brief; exact re-anchor edit named in §Residual-citations.
- Packages considered: none — no mechanism specified (pure test-pin removal + prose cleanup).
- Reuse ledger: none (no new reusable symbol introduced; only deletions + a class rename).
- Graded: 50fb230 · HEAD-at-report: 50fb230 · SAME
- decisions-needed: none
- wave-3 re-cut obligation filed: **lore finding #395** (area `packet-39-wave-3`, joins cold-audit R2)
- receipt pointers: BEFORE/AFTER suite → §Suite; wave-1 contract → §Wave1-contract; ruff → §Ruff; typecheck → §Typecheck; currency BEFORE/AFTER → §Currency; what-removed-vs-preserved → §Removed-vs-preserved; cleanup → §Cleanup.

## §Capability check (brief-base §4)
Everything the brief demanded was satisfiable with the granted tools (Read/Edit/Write/Bash, lore
MCP loaded via `ToolSearch "+lore"`, comms register/send, findings report). Writable set honoured:
only `loremaster/tests/test_auth.py`, the lore finding, and this report were touched. No commit.

## §Removed-vs-preserved (each with reasoning)

### REMOVED — the 7 premature wave-3 forward pins (all in `test_auth.py`)
Design `docs/design/2026-08-21-packet39-recut-oauth.md` §9 assigns these REMOVALS to WAVE 3 (the
standalone-fastmcp composition, §2/§8): `BearerAuthMiddleware` **dropped-and-replaced by
`FastMCP(auth=…)`**, `AuthVerifier` ABC **dropped**, `tls_terminated_upstream` retired with the
wave-3 config surface. Per the DUAL law (removed-behaviour pins are written WHEN the removal lands,
not before) these asserted absences of symbols that still exist by design today — so they were
perpetually RED and RED_ORPHANED at the currency gate. Removed:

- `TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_importable_from_loremaster_auth`
  (parametrized `BearerAuthMiddleware`, `AuthVerifier` → 2 cases)
- `TestRetiredAuthSurfaceIsGone::test_the_retired_name_is_not_exported`
  (parametrized `BearerAuthMiddleware`, `AuthVerifier` → 2 cases)
- `TestAuthConfigRetiresTlsTerminatedUpstream::test_the_retired_field_is_not_a_model_field`
- `TestAuthConfigRetiresTlsTerminatedUpstream::test_a_config_still_carrying_the_retired_flag_fails_to_load`
- `TestAuthConfigRetiresTlsTerminatedUpstream::test_the_failure_names_the_retired_field_and_the_fix`

These CANNOT be manifest-adjudicated (confirmed by reading `scripts/pending_contract_gate.py`
`partition_pytest`: pytest residuals match by FILE via `registered_paths`; a `files:` manifest
entry REQUIRES a `missing_symbols`/`unsymboled_codes` mypy residual, and `test_auth.py` is
mypy-clean). Removal was the only correct close-out.

### PRESERVED with judgment
- `TestRetiredAuthSurfaceIsGone::test_the_kept_names_are_still_exported` — **KEPT** and re-homed
  into the renamed class `TestKeptAuthSurfaceIsExported`. It is a VALID keep-check TODAY:
  `ApiKeyVerifier` / `OriginValidationMiddleware` / `build_api_key_verifier` are still exported
  from `loremaster.auth` (it is one of the 25 green pins AFTER). Its stale comment ("The CONTROL
  for the pins above…") was rewritten — the absence pins it referenced are gone; it now stands as
  a standalone export-surface check. Reason to keep: it reddens if a rewrite empties/reshapes
  `__all__` — a real guard independent of the wave-3 removals.
- `TestAuthConfigRetiresTlsTerminatedUpstream::test_a_config_without_the_retired_flag_loads` —
  **REMOVED with the class.** It was the POSITIVE CONTROL for the 3 removed retirement pins; once
  they go it controls nothing (asserting a clean config loads is already covered by
  `TestBuildApiKeyVerifierFromConfig`). Its re-cut belongs to wave 3 as the control for the
  re-cut retirement pins (recorded in finding #395).

### KEPT UNTOUCHED (verified still green, imported by siblings)
`TestApiKeyVerifierIsPreservedVerbatim`, `TestBuildApiKeyVerifierFromConfig`,
`TestOriginValidationMiddlewareIsPreserved`, `_RecordingApp`, `_drive` (the last two imported by
`test_eager_startup` / `test_mcp_server` — NOT broken; both suites' import surface untouched).

## §Cleanup (orphaned constants / imports / docstring)
- Constant `RETIRED_AUTH_NAMES` — **removed** (only consumers were the 2 removed absence pins;
  `grep` confirmed no cross-module import).
- Constant `RETIRED_AUTH_CONFIG_FIELD` — **removed** (only consumers were the 3 removed retirement
  pins; grep-confirmed local-only).
- Constant `KEPT_AUTH_EXPORTS` — **KEPT** (consumed by the preserved kept-names export check). Its
  header comment ("both lists are the CONTRACT; the deletion half…") rewritten to describe only
  the kept list and point at the wave-3 re-cut.
- Import `ValidationError` (from `pydantic`) — **removed** (only used by the deleted retirement
  pins; `SecretStr` stays, `AuthConfig`/`AuthKey` stay — all still consumed by keepers).
- Module docstring — **trimmed**: dropped the "three jobs" framing (jobs 2 RETIRED-surface + 3
  CONFIG-boundary no longer live here) and the stale "kept-with-pin surface: … absence pins … the
  tls_terminated_upstream config-migration guard" claim. Replaced with a dated (2026-08-22) SCOPE
  note + a "WHAT IS NOT HERE, AND WHY" note explaining the wave-3 deferral and pointing at finding
  #395. E1/E1a provenance and the `_drive`/`_RecordingApp` public-by-use warning preserved.
- Trailing provenance: added a `# RETIRED (wave-1 close-out, contract-39-w1b)` marker recording the
  removed tls class + its wave-3 destination, beside the existing E1a GoogleOAuthConfig marker.

## §Residual-citations (FLAG — left untouched per brief scope)
Anchor-free grep for `§8` in the file leaves 4 residual hits, each in a KEEP-untouched keeper class,
each a verdict below (P8d rename-sweep discipline — individual verdicts, no wholesale classification):
- `test_auth.py` `TestApiKeyVerifierIsPreservedVerbatim` docstring `"Design §8 rows 3, 10 and 11"` —
  STALE-BUT-CORRECT: cites the archived 2026-07-31 doc's inventory; the re-cut equivalents are §9.
- `TestApiKeyVerifierIsPreservedVerbatim.test_non_ascii_token_returns_none_not_typeerror` comment
  `"Design §8 row 3"` — same.
- `TestBuildApiKeyVerifierFromConfig` docstring `"Design §8 row 10"` — same.
- `TestOriginValidationMiddlewareIsPreserved` docstring `"Design §8 rows 4 and 13"` + its
  `test_non_http_scope_passes_through_untouched` comment `"Design §8 row 4"` — same.
Recommendation (NOT applied — these classes are in the brief's "keep untouched" set): a future
touch re-anchors `§8 row N` → the re-cut `§9` inventory rows (ApiKeyVerifier kept-with-pin,
OriginValidationMiddleware kept). Not a gate concern (prose citations are unchecked); surfaced so it
is a deliberate, not silent, inheritance.

## §Suite (test_auth.py BEFORE → AFTER)
BEFORE (`50fb230`, `pytest -n auto`): **7 failed, 26 passed** — the 7 failures were exactly the
RED_ORPHANED set (2× not-importable, 2× not-exported, 3× tls retirement).
AFTER: **25 passed** in 4.34s (33 collected − 7 removed forward pins − 1 removed orphaned control).
```
.........................                                                [100%]
25 passed in 4.34s
```

## §Wave1-contract (still green)
`pytest loremaster/tests/test_token_verifier.py loremaster/tests/test_oauth_identity_seam.py -n auto`:
```
............................................                             [100%]
44 passed in 6.78s
```

## §Ruff
`uv run ruff check .` → `All checks passed!`

## §Typecheck
`bash scripts/typecheck.sh` (exit 0): lorerunes/lorescribe/loresigil/skills/docs-eval/scripts all
OK; loremaster reports the SINGLE pre-existing adjudicated residual (no new error):
```
loremaster/tests/_auth_fixtures.py:759: error: Unexpected keyword argument "http_client" for "build_mcp_server"  [call-arg]
Found 1 error in 1 file (checked 212 source files)
```
This is the RED_ADJUDICATED bound owned by `packet-39-pending-build` (wave-3 wires
`build_mcp_server(http_client=)`). Unchanged by this work.

## §Currency (BEFORE → AFTER)
BEFORE (`50fb230`, `scripts/pending_contract_gate.py --currency`):
`CURRENCY : FAIL` — `pytest RED_ORPHANED — 7 residual(s) with NO owner` (all 7 in `test_auth.py`,
the exact set removed above); `typecheck RED_ADJUDICATED — 1 residual` (owned, fine); `ruff GREEN`.

AFTER (`50fb230` + this uncommitted edit): **`CURRENCY : PASS — every claimed gate is GREEN or
OWNED`**. The 7 RED_ORPHANED are gone:
```
  typecheck    RED_ADJUDICATED — 1 residual(s), owned by: packet-39-pending-build (... http_client seam ...)
  ruff         GREEN
  pytest       GREEN
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
```
ZERO RED_ORPHANED confirmed. The remaining `typecheck RED_ADJUDICATED` is the single owned
wave-3 `http_client` bound (expected, not a failure of this gate's ADJUDICATION invariant).
