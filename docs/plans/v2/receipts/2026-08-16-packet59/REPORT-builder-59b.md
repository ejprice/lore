# REPORT-builder-59b — packet 59 fastmcp 3.x migration FIX WAVE

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Model attestation:** `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8` (Opus 4.8, opus48-worker
  pin) — read from env, not introspected. ✓
- **Demanded vs. have:** Read/Edit on the writable set (✓); `uv run pytest -n auto` full suite +
  the TEST store `ws://127.0.0.1:18000` (✓ — required for the wire pins); `scripts/typecheck.sh`,
  `uv run ruff check .`, `pending_contract_gate.py --currency` (✓); lore tools via `ToolSearch +lore`
  (✓, loaded); installed `fastmcp`/`mcp`/`uvicorn` source for the #107-class "read then verify"
  checks (✓). **No blocker.**
- **Content backup (mutating an uncommitted tree — standing law):** `cp -a` of the writable set to
  `/tmp/builder-59b-backup/` BEFORE any edit. Delivered md5s: server.py `0a84eb31…` (matches
  coldaudit N1), auth.py `512ac687…`, config.py `fc7f2905…`, test_migration_wire.py `d0a65d27…`,
  fastmcp_migration_spike.py `d81562459…`, test_fastmcp_migration.py `b879dd00…`. HEAD `ee4bced`.
- **Tool honesty:** grep used for uncommitted-tree exhaustiveness (line numbers drift on an
  uncommitted migration — a sanctioned grep case, said out loud). fastmcp/mcp source READ directly
  (dependency behaviour = #107 read-then-verify law).

## SUMMARY BLOCK
- state: **done-with-deviations** (all 8 items fixed + pinned + mutation-proven; ruff GREEN, typecheck
  ==baseline, currency clean of our orphans, full suite zero-new-delta 450/0-error CONFIRMED)
- receipt line: brief-base v14 read · brief project v7 read
- deviations: (1) F2 conversion lives in a NEW wrapper `_eager_build_or_operator_safe_error` at
  the lifespan boundary, NOT inside `_eager_build_with_retry` as the brief's literal text implies —
  because two EXISTING contract pins (`test_fastmcp_migration` `pytest.raises(SurrealStoreError)`,
  `test_backoff_seam` `pytest.raises(RuntimeError)`) REQUIRE the helper to re-raise the ORIGINAL
  exception, which I may not weaken. Fully satisfies F2's security intent; breaks no pin. (2) The
  §6.2 mode placeholder in the restricted contract file was NOT un-skipped — its fixture is
  module-local to `test_migration_wire.py` (moving it to conftest is out of my writable set); I
  implemented the RUNNABLE mode pins in `test_migration_wire.py` instead (the same pattern every
  other §6.2 assertion already follows). See §DEVIATIONS.
- Graded: base `ee4bced` (uncommitted migration over it) · HEAD-at-report: `ee4bced` · SAME.
- Packages considered: none new — no new mechanism; `get_http_headers(include=)` /
  `http_app(stateless_http=)` are the INSTALLED fastmcp API, verified by reading
  `.venv/.../fastmcp/server/dependencies.py` + `server/http.py` + `utilities/logging.py` (#107
  read-then-verify). `urlsplit` = stdlib (userinfo parse); `AfterValidator` = pydantic (already a dep).
- Reuse ledger: see §DRY-LEDGER — 3 new symbols, all dispositioned.
- decisions-needed: none (F2 architecture + §6.2-placement are deviations I resolved with the
  clearly-correct reading; flagged, not left open).
- receipt POINTERS: §F1 · §R1 · §F2 · §F3 · §F5 · §ITEM6 · §ITEM7 · §ITEM8 · §GATES · §DEVIATIONS · §DRY-LEDGER.

## PER-FINDING FIXES (file:line + RED→GREEN mutation receipts)

### F1 [HIGH] transport_session correlator (finding #381)
- **FIX:** `server.py::_record_tool_trace` — `get_http_headers(include={_TRACE_TRANSPORT_SESSION_HEADER}).get(...)`
  (was bare `get_http_headers().get(...)`). Docstring comment corrected (it claimed the None was only
  the no-request case; the real cause is the default exclude set). VERIFIED against installed
  `fastmcp/server/dependencies.py:410-464`: default `include_all=False` exclude set contains
  `"mcp-session-id"` (:447); `include` subtracts it back (:450); already lowercase so the :452 sanity
  check passes.
- **PIN:** `test_migration_wire.py::TestTheTransportSessionCorrelatorIsCaptured` — a full stateful raw
  wire session (`raw_session_tool_call`: initialize→initialized→tools/call) records `transport_session`
  == the minted `mcp-session-id`, read back from the REAL `trace` table. `trace_rows()` projection
  extended with `transport_session`.
- **MUTATION PROOF:** revert to bare `get_http_headers()` → the pin RED (correlator None ≠ session id;
  the row lands, so it fails on the equality assert, not the found_row assert — the two RED causes are
  distinguished). Restore → GREEN.

### R1 [MOD] transport MODE explicit (coldaudit R1 / design §5b-C5 / FG8)
- **FIX:** `server.py::build_asgi_app` — `mcp.http_app(..., stateless_http=False)` (was absent →
  inherited `fastmcp.settings.stateless_http`, an env-overridable default). VERIFIED default resolves
  via installed `fastmcp/server/http.py` + settings; `_host_matches` `*`-handling read for item 8.
- **PINS:** `test_migration_wire.py::TestTheServedTransportModeIsExplicitlyStateful` —
  (a) UNIT spy on `http_app` kwargs asserts `stateless_http is False` (the DISCRIMINATING pin: the
  wire session-id pin is green even without the fix since fastmcp defaults to stateful, so it does not
  discriminate the CODE change); (b) WIRE `post()` asserts a stateful `initialize` mints an
  `mcp-session-id` response header (the coldaudit/§6.2 mode assertion, a regression guard).
- **MUTATION PROOF:** remove `stateless_http=False` → the UNIT spy pin RED (`captured.get(...)` is None).
  Restore → GREEN.

### F2 [MED] boot-failure redaction restored (supersedes flag-4; operator ruling 30e56ac8)
- **FIX:** re-added `server.py::_EAGER_BUILD_FAILED_MESSAGE` + NEW wrapper
  `_eager_build_or_operator_safe_error` (the native `lifespan=` now calls it). On total (`Exception`)
  failure it (a) `logger.error("eager startup build failed", exc_info=exc)` through lore's REDACTING
  sink, then (b) `raise RuntimeError(_EAGER_BUILD_FAILED_MESSAGE) from None` — fixed phrase, chained
  cause suppressed. `_eager_build_with_retry` UNCHANGED (still re-raises the original — the FP-07
  contract). See §DEVIATIONS for WHY the wrapper, not the helper. `except Exception` (not
  `BaseException`) so `CancelledError` propagates for graceful shutdown; covers the whole measured
  leak surface (`SurrealConnectionError` etc. are Exception subclasses — security-59 F4).
- **PIN:** `test_eager_startup.py::TestEagerBuildFailureMessageDoesNotLeakSecrets` (re-added — the file
  is a live test again, not a pure tombstone; its "ONE REMOVED BEHAVIOUR" narrative updated to
  RESTORED). Three legs: fixed-phrase raised (not str(exc)); no credential in the full formatted
  traceback (proves `from None`); the real detail logged with `exc_info` on lore's sink (both halves).
- **MUTATION PROOF:** replace `raise RuntimeError(...) from None` with `raise` → the message + traceback
  legs RED (credentialed URL leaks into both), the redacted-detail leg stays GREEN. Restore → GREEN.

### F3 [LOW-MED] guard a None request_context
- **FIX:** `server.py::_record_tool_trace` — guard `fastmcp_context is None or fastmcp_context.request_context is None`
  → same quiet DEBUG no-op (was: dereferenced `.request_context.lifespan_context` unguarded, a loud
  `trace.emit.failed`/AttributeError if `request_context` is None, which fastmcp types `RequestContext | None`).
- **PIN:** `test_migration_wire.py::TestTraceEmitGuardsANoneRequestContext` (self-contained unit).
- **MUTATION PROOF:** drop the `request_context is None` leg → pin RED with
  `AttributeError: 'NoneType' object has no attribute 'lifespan_context'`. Restore → GREEN.

### F5 [LOW] stale prose
- **FIX:** `server.py::LoreServer.run` logging comment — removed the retired
  `mcp.server.fastmcp.utilities.logging.configure_logging` name AND the false "FastMCP.__init__ runs
  logging.basicConfig with a root RichHandler" claim. VERIFIED: fastmcp 3.x calls `configure_logging`
  at IMPORT (`fastmcp/__init__.py:23`) targeting the non-propagating `fastmcp` logger, NOT root, NOT
  basicConfig, NOT in `__init__` (`fastmcp/utilities/logging.py`). Rewrote as verified defence-in-depth.
  (Natural-language surface — no gate; verified-against-source per the #107 law.)

## §ITEM6 — currency cleanup
- **spike (`scripts/fastmcp_migration_spike.py`):** 19 mypy errors → **0** (`MYPYPATH=scripts uv run mypy
  scripts/fastmcp_migration_spike.py` → "Success: no issues found"). Fixes: typed `headers` locals
  (`_origin`/`_bearer`), `int(getsockname()[1])`, `Iterator[str]`/`AsyncIterator[...]`/`tuple[_ASGIApp, Any]`
  return annotations, a `_Item1Counters` TypedDict (kills the `int | None` `+=`/assignment/subtraction
  errors), `app: _ASGIApp` annotation, and `build(protection: bool) -> Any` (narrowing `bool | str` →
  `bool` fixes the `host_origin_protection` arg-type). No behaviour change (measurement instrument).
- **`test_fastmcp_migration.py:163`:** `return cast(type[Middleware], cls)` (+ `from typing import Any, cast`)
  — mechanical `no-any-return` fix, NOT an assertion change (the `issubclass` runtime check unchanged).

## §ITEM7 — HARDENING security-F1 (reject inline-credential URLs)
- **FIX:** `config.py` — new `_reject_url_userinfo` predicate + `CredentialFreeUrl = Annotated[str,
  AfterValidator(_reject_url_userinfo)]`, applied to BOTH `SurrealConfig.url` and `EmbeddingConfig.base_url`.
  A `user:pass@host` (or `user@host`) userinfo component → `ValidationError` at config LOAD.
- **PIN:** `test_config.py::TestUrlUserinfoIsRejected` — 5 tests: base_url rejected, surreal.url rejected
  (a DIFFERENT field — the shared predicate guards both), username-only rejected, + 2 positive controls
  (credential-free URL accepted; default surreal.url credential-free).
- **MUTATION PROOF:** revert `base_url` to plain `str` → exactly the 2 base_url pins RED, the surreal pin
  + both controls GREEN (proves the fields are independently guarded and the predicate discriminates).
  Restore → GREEN.

## §ITEM8 — KEEP + PIN wildcard (operator wants `*` = allow-all)
- **VERIFIED (no code change needed):** `_resolve_allowed_hosts` already passes a raw `*` through into
  the allowlist; fastmcp `_host_matches` (`server/http.py:157`) treats `*` as match-all, so with
  `host_origin_protection=True` (strict) an arbitrary Host is served (not 421). Confirmed by reading the
  installed source AND empirically by the wire pin.
- **PINS:** `test_migration_wire.py::TestTheAllowedHostsWildcardAndDefault` (fixture refactored into a
  reusable `_serve_migration_wire(..., allowed_hosts_env=...)` helper): (a) `LORE_ALLOWED_HOSTS='*'` →
  an arbitrary/spoofed Host is NOT 421; (b) UNSET → a spoofed Host IS 421 (default-protective, kept).
  The two-leg contrast IS the discrimination.
- **NOT DONE (operator-declined, per brief DO-NOT):** did NOT promote the knob to a `ServerConfig` field;
  did NOT reject `*` (security-59 F2 overruled).

## DEVIATIONS
1. **F2 conversion in a NEW wrapper, not inside `_eager_build_with_retry`.** The brief's item-3 text
   ("`_eager_build_with_retry` now just `raise last_exc`. FIX: on exhaustion, restore BOTH…") reads as
   "convert inside the helper." Two readings that would produce different code:
   (a) convert inside `_eager_build_with_retry` — but `test_fastmcp_migration.py:1394`
   `pytest.raises(SurrealStoreError)` and `test_backoff_seam.py:379` `pytest.raises(RuntimeError)`
   REQUIRE the helper to re-raise the ORIGINAL exception type; converting there to
   `RuntimeError(fixed)` breaks the `SurrealStoreError` pin (a plain RuntimeError is not a
   SurrealStoreError) — a contract pin I may not weaken.
   (b) convert at the lifespan boundary (a wrapper the lifespan calls), leaving the helper re-raising
   the original. This is exactly where the DELETED `_EagerStartupLifespan._drive_lifespan` did the
   conversion. **I picked (b).** It fully satisfies F2's security intent AND breaks no pin. Flagged
   because it deviates from the brief's literal wording; no operator escalation needed (the security
   requirement is met without weakening any pin).
2. **§6.2 mode placeholder NOT un-skipped in the contract file.** `test_fastmcp_migration.py`'s
   `test_wire_smoke_is_specified_not_yet_runnable` skip cannot be un-skipped without the
   `migration_wire` fixture, which is module-local to `test_migration_wire.py` (moving it to conftest
   is outside my writable set). I implemented the runnable mode pins in `test_migration_wire.py` — the
   SAME pattern every other §6.2 assertion (host-origin, auth, once-per-process) already follows (their
   contract placeholders also remain skipped with runnable twins in `test_migration_wire.py`). No
   assertion weakened.
3. **F3 pin home.** F3's natural home (the middleware/context scaffolding) is in the restricted
   contract file, and F3 is not in the brief's "security-F1/wildcard/F2" writable-pin list. I placed a
   self-contained F3 unit pin in `test_migration_wire.py` (explicitly writable). It needs no server;
   the module's `pytest.mark.wire` marks it, but it still runs in the default `-n auto` suite.

## DRY-LEDGER
| new symbol | lore/grep query run | what it returned | disposition |
|---|---|---|---|
| `_reject_url_userinfo` + `CredentialFreeUrl` (config.py) | grep `userinfo\|\.username\|urlsplit\|reject_url` over `loremaster/loremaster/*.py` + `lorerunes/` | no existing URL-userinfo validator anywhere (auth.py uses `urlsplit` for Origin HOSTNAME only) | HAND-ROLLED (nothing found). Both call sites are in ONE member (`loremaster.config`), so a shared predicate in config.py (mirroring the `SlugStr`/`is_blank` idiom) is the DRY home — NOT lorerunes (which is the CROSS-member home + out of my writable set). Applied to both fields via ONE `Annotated` type → prove-sharing-by-mutation confirmed (revert base_url → only base_url pins RED). |
| `_eager_build_or_operator_safe_error` (server.py) | read `_eager_build_with_retry` + its callers + the deleted `_EagerStartupLifespan._drive_lifespan` pre-image | the retry helper re-raises the original (pinned); the deleted apparatus did the secret-safe conversion in the lifespan handler | HAND-ROLLED — re-homes the deleted `_drive_lifespan` conversion (a POLICY: secret-safe boot failure) as the lifespan's operator-safe layer over the helper. Not a clone of the helper; a distinct concern that MUST live outside the helper (the helper's re-raise-original is pinned). |
| `_EAGER_BUILD_FAILED_MESSAGE` (server.py) | grep pre-image (`git show HEAD:server.py`) | the identical constant existed pre-migration; deleted by the migration | RE-ADDED (restoring a deleted constant, operator-ruled). Not a new invention. |

TEST-SIDE symbols (scaffolding, not production policy — no cross-caller policy to duplicate):
`_serve_migration_wire` (test_migration_wire.py) is a REFACTOR of the existing fixture body into a
reusable helper (REDUCES duplication — the fixture now delegates to it); `raw_session_tool_call`
(test method) is new because the spike's `_wire_session` uses the fastmcp `Client`, which does not
expose the minted session id (F1 needs raw httpx to observe it); `_Item1Counters` (spike TypedDict)
is a local typing helper. None encode reusable policy.

## GATES (final tails)
- **ruff** (`uv run ruff check .`): `All checks passed!` ✓
- **typecheck** (`./scripts/typecheck.sh`): loremaster leg `Found 102 errors in 8 files` == HEAD
  `ee4bced` baseline (my touched files add ZERO; `:163` orphan GONE); `scripts` leg
  `Success: no issues found in 44 source files` (spike 19→0); other legs OK; shellcheck OK. The 102
  are all pre-existing pending-39 (`test_auth_composition` `resolve_posture`/`Posture`/`SCOPE_READ`
  etc.), RED_ADJUDICATED per the currency gate.
- **currency** (`scripts/pending_contract_gate.py --currency`):
  - typecheck: **RED_ADJUDICATED** (191 residual, owned by `packet-39-pending-build`) — my spike(19)
    + `:163`(1) typecheck ORPHANS are GONE (they were the only orphaned typecheck reds per coldaudit R2/R3).
  - ruff: **GREEN**.
  - pytest: **RED_ORPHANED = 4** — EXACTLY the coldaudit's pre-existing set (R4/R5), none mine:
    `test_comms_footer` · `test_ast_reach_helpers` · `test_secret_typing` ·
    `test_surreal_harness::…docstring_counts…`. (These are pre-existing owners'-debt orphans, RED at
    `ee4bced`; out of my writable set.)
- **full suite** (`uv run pytest -n auto`): **450 failed, 9859 passed, 51 skipped, 3 xfailed, 0 error**
  in 229.92s. **Zero-new-delta CONFIRMED**: 450 == the coldaudit's migrated baseline (450 failed /
  0 error), so my fixes add ZERO new failure; the 2 comm-23 pending-39 delta nodes
  (`test_auth_identity_seam::…unauthenticated_initialize…`,
  `test_auth_composition::…no_auth_settings…`) are present and are the ONLY delta vs `ee4bced` (448);
  NO failure in any touched file (server.py/config.py/test_migration_wire/test_config/
  test_eager_startup/spike/test_fastmcp_migration). My 14 new pins are all in the 9859 passed.
  **AUTHORITATIVE re-run (clean, `-p no:cacheprovider`): 450 failed / 9859 passed / 0 error in
  232.80s; the sorted FAILED list has ZERO touched-file nodes and the 2 pending-39 delta nodes
  present** (`/tmp/fullsuite-59b-failed.txt` — the durable receipt; the run is reproducible via
  `uv run pytest -n auto`). Failure breakdown (all pre-existing pending-39 + 4 owners'-orphans):
  test_auth_composition 82 · test_google_token_verifier 75 · test_hosted_readonly_posture 57 ·
  test_allowlist_roster 46 · test_auth 25 · test_auth_identity_seam 19 · test_permission_resolver_seam
  14 · lorerunes/test_roster_parser (pending-39 roster) · + test_surreal_harness/test_secret_typing/
  test_comms_footer/test_ast_reach_helpers (the 4 orphans, 1 each).

There are 450 failing tests unrelated to our present scope (all pre-existing pending-39 contract +
4 owners'-debt orphans, RED at `ee4bced`; unchanged by this wave). They are the packet-39 build's
own RED contract, not defects introduced here.

## FINAL MD5s (post-fix; for provenance/traceability, coldaudit-N1 style)
- `server.py` `9dd24ef1…` (delivered `0a84eb31…`) · `config.py` `b5318a7d…` (delivered `fc7f2905…`)
- `fastmcp_migration_spike.py` `aba9f472…` (delivered `d8156245…`) ·
  `test_migration_wire.py` `ab2fbb8b…` (delivered `d0a65d27…`)
- `test_config.py` `b756461c…` · `test_eager_startup.py` `9a24a8cf…` ·
  `test_fastmcp_migration.py` `35abc780…` (delivered `b879dd00…`)
- `auth.py` `512ac687…` — **UNTOUCHED** (== delivered). auth.py was in the writable set for the
  userinfo-reject, but that validation belongs in `config.py` (the URL fields live there — located
  via lore/grep), so auth.py needed no change.
- Content backup of the delivered writable set at `/tmp/builder-59b-backup/` (standing law).
