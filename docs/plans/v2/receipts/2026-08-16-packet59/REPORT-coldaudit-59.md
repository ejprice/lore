# REPORT-coldaudit-59 — cold REFUTE audit, packet 59 (fastmcp 3.x migration)

brief-base v14 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **Demanded vs. have:** `uv run pytest -n auto` full-suite (✓); `./scripts/scratch_copy.sh` for the
  baseline (✓); `scripts/typecheck.sh` · `uv run ruff check .` · `pending_contract_gate.py --currency`
  (✓); the TEST store `ws://127.0.0.1:18000` (✓ OPEN); Read of the diff/design/contract/reports (✓);
  lore tools (`ToolSearch "+lore"`, ✓, index fresh at claim — git_ref `ee4bced`). READ-ONLY on the
  repo, WRITABLE = scratch + this report (✓). **No blocker.**
- **Model attestation (brief-carried, cannot self-read):** `claude-opus-4-8` (Opus 4.8), `opus48-worker`
  pin. ✓
- **Tool honesty:** lore_index (freshness), lore_comms (register/claim). `bash grep` used for the
  retired-name sweep + count reconciliation (non-symbol textual seams + rename-exhaustiveness — two of
  the three sanctioned grep cases). One lore weakness observed: `lore_comms heartbeat` failed against
  the PROD store `:18500` ("no close frame received or sent") — transient backend websocket error,
  unrelated to the audit; the report is the durable record. Will re-file if it recurs.

## SUMMARY BLOCK
- state: **done** — verdict rendered below.
- receipt line: brief-base v14 read · brief project v7 read
- **Graded:** `ee4bced404af1bd17fa756e84ff96a4625d9f82d` (the uncommitted build over it) ·
  HEAD-at-report: `ee4bced404af1bd17fa756e84ff96a4625d9f82d` · **SAME (0 behind)**.
- **VERDICT: GO** — with ONE builder-missed residual to action first (R1 / F1: C5/FG8 transport-mode
  rider) + FLAG-4 routed to the security audit. Zero-new-delta reproduced EXACTLY (baseline 448 /
  migrated 450 / comm-23 = the 2 adjudicated pending-39 nodes / 0 missed / 0 fixed); both load-bearing
  pins mutation-proven on the delivered tree; wire suite 8/8; ruff GREEN; builder's code adds 0 mypy
  errors; every currency red pre-existing/out-of-scope/contract-author's.
- Packages considered: none — audit renders a verdict, specifies no mechanism. (The build's package
  choices — fastmcp replace, mcp keep_with_trigger — were verified against the design/inventory, not
  re-decided.)
- Reuse ledger: none — no new reusable symbol introduced (audit).
- receipt POINTERS: §DELTA (zero-new-delta reproduction) · §GATES (re-run tails) · §MIDDLEWARE
  (B1–B8) · §DELETION-RECONCILIATION · §MUTATION · §FINDING-C5 · §RESIDUALS.

## SCRATCH / CLEANUP (operator — "don't abandon a worktree")
Two `scratch_copy.sh` copies were created (baseline delta + mutation proofs) and are NOT auto-removable
from this session (`rm` is permission-gated). Disposable (regenerable via `./scripts/scratch_copy.sh`) —
reclaim the disk when convenient:
- `/home/ejprice/scratch/pkt59-baseline` (322M — ee4bced source, the delta baseline)
- `/home/ejprice/scratch/pkt59-mutation` (295M — migrated source, the mutation proofs)
The two mutations are captured verbatim in §MUTATION, so the proofs reproduce without these dirs. Real
repo: server.py md5 `0a84eb31` UNCHANGED throughout (all mutations were in scratch); no git-state
mutation; only `REPORT-coldaudit-59.md` added.

## CONFIRMED FINDING (builder MISSED it — surfaced for lead adjudication)

### F1 — C5/FG8 transport-mode rider dropped on BOTH halves (moderate; benign TODAY, fragile forward)
Design **§5b-C5** rules the transport mode **"PRESERVE+PIN EXPLICITLY — set the mode to match today's
behaviour; do NOT inherit a possibly-different fastmcp default"**, and design **§9-FG8** names "served
transport mode differs from pre-migration" as a false-green scenario. The build:
1. **Does NOT set the mode explicitly.** `build_asgi_app` calls `mcp.http_app(path=…,
   host_origin_protection=True, allowed_hosts=…)` with **no `stateless_http=`**. Verified in installed
   fastmcp 3.4.7 source: `http_app(stateless_http=None)` resolves via
   `fastmcp/server/mixins/transport.py:304-305` to `fastmcp.settings.stateless_http`, whose default
   (`fastmcp/settings.py:340`) is `False` (stateful) — but is overridable by the `FASTMCP_STATELESS_HTTP`
   env var. So the served mode is now **inherited from fastmcp's global setting**, the exact thing C5
   forbids.
2. **No executing pin asserts the served mode.** The contract's SECTION F REQUIRES it
   (`test_fastmcp_migration.py:1598-1599`: "the served transport mode matches pre-migration (stateful:
   a mcp-session-id is minted — C5 / FG8)"), but the SECTION F @wire tests are `pytest.skip`
   placeholders, and the executing wire fixture `test_migration_wire.py` **omits the session-id/mode
   assertion** entirely (its 5 test classes cover tools/list, version, trace-∀, host/auth, once-per-
   process — never the mode). The only `mcp-session-id` mint assertion in the tree lives in
   `_auth_fixtures.py:708-711` / `test_auth_identity_seam.py`, which are **pending-39 committed-RED** —
   so nothing GREEN pins the mode.
- **Impact:** NO behaviour break today — `fastmcp.settings.stateless_http` defaults `False`, so the
  served mode IS stateful (matches pre-migration), and zero-new-delta is intact. The risk is purely
  latent: a fastmcp default flip on upgrade, or a stray `FASTMCP_STATELESS_HTTP` in a deploy env,
  silently changes the mode with every gate green — precisely the FG8 false-green C5 exists to close.
- **Recommended fix (cheap):** pass `stateless_http=False` explicitly in the `http_app()` call, AND add
  the session-id-minted assertion to `test_migration_wire.py` (a `.post()` probe already exists — assert
  the response carries an `mcp-session-id` header). Or the lead may ACCEPT-with-trigger (re-open when 39
  flips to stateless), matching how FLAG-4 was handled — but it should be a DELIBERATE ruling, not an
  unnoticed drop.

## NOTES (not blockers)

### N1 — server.py md5 provenance: delivered tree ≠ builder's cited "restored byte-exact" md5
Current working-tree `server.py` md5 = **`0a84eb31…`**. The builder's report cites **`89eb7e9…`** three
times as the "restored byte-exact" post-mutation-proof state (§ZERO-NEW-DELTA, §Phase 5). That md5
matches NEITHER the current tree (`0a84eb31`) NOR HEAD `ee4bced` (`31d012c9`). The `/tmp` backup is gone.
So either the builder edited server.py AFTER its last md5 receipt, or the receipt is mis-transcribed.
**Consequence for this audit:** I do not trust the builder's mutation-proof receipts — I RE-RAN both
mutation proofs against the *delivered* tree myself (§MUTATION). The delivered tree is what I grade.

### N2 — FLAG-4 (dropped secret-safe boot-failure message) is a REAL un-adjudicated DUAL gap — CORROBORATED
The deleted `_EAGER_BUILD_FAILED_MESSAGE` carried a security behaviour (a FIXED phrase on
`lifespan.startup.failed` so a credentialed boot exception could not leak into uvicorn's unredacted
startup log). The design DUAL (§5b-C1..C5 / §5c-D1..D7) does NOT adjudicate it — so its deletion is a
NEW inventory item, correctly surfaced by the builder as FLAG-4. Under the native `lifespan=`,
`_eager_build_with_retry` re-raises the last exception on total boot failure → Starlette/uvicorn logs it,
potentially unredacted. **The security-auditor owns the ruling; I NOTE it here as a confirmed real gap,
not builder over-caution.** (Builder recommends ACCEPT-with-trigger; agreed as reasonable given
pre-production + local-boot-log-only exposure.)

---

## BODY (receipts) — _[being filled incrementally; runs in flight]_

### §MIDDLEWARE — B1–B8 preserved (read of `git diff ee4bced -- server.py`)
`ToolTraceMiddleware.on_call_tool` (replacing `TracingFastMCP.call_tool`):
- **B2** (outcome always wins): returns `call_next(context)` result unchanged; trace-emit failure caught
  by `except Exception` → `logger.exception("trace.emit.failed")`. ✓
- **B3** (`ok` latch): `ok=False`, latched `True` only after `call_next` returns, **no `except` arm**. ✓
- **B4** (shield+bounded): `anyio.CancelScope(shield=True)` + `anyio.fail_after(_TRACE_EMIT_TIMEOUT_SECONDS)`
  in the `finally` — preserved VERBATIM. ✓
- **B8** (latency): measured around `call_next`. ✓
- **B1/B7** (declared identity, one funnel): reads `context.message.name` + `context.message.arguments`;
  `_record_tool_trace` REUSED as ONE module-level function (M4) — the middleware calls it once per
  dispatch; no second emission path. ✓
- **B5** mechanism change: `fastmcp_context is None` ⇒ DEBUG + return (in-process/no-store). ✓
- **B6**: `_trace_write_store` AttributeError ⇒ WARNING + return. ✓
- **B7** correlator mechanism change: `get_http_headers().get(_TRACE_TRANSPORT_SESSION_HEADER)` — `{}`
  when no HTTP request → `None`, not a crash. ✓
- Construction (D4/D7): `FastMCP(name, instructions, lifespan, version=_resolve_version(),
  middleware=[ToolTraceMiddleware()])`; old `mcp._mcp_server.version` reach + `_lore_eager_guard` attr
  DELETED. host/port NOT ctor kwargs (D2). ✓

### §DELETION-RECONCILIATION (tdd Phase 7) — deleted set ⊆ planned DELETE set + 1 flagged extra
Deleted symbols (from the diff): `_ProcessLifespanGuard` (C2), `_EagerStartupLifespan` (C2),
`TracingFastMCP` subclass (§5a → `ToolTraceMiddleware`), `_lore_eager_guard` attr (D5), plus the
supporting `_Scope/_Message/_Receive/_Send/_ASGIApp` ASGI aliases + `_LIFESPAN_*` protocol constants
(used ONLY by the deleted interceptor). All within the design §5b-C2 "~150-LOC apparatus" DELETE scope.
`_record_tool_trace` re-homed (not deleted); `_build_context`/`_app_context`/`_tool` signature-changed
(not deleted). **The one behaviour-carrying extra deletion — `_EAGER_BUILD_FAILED_MESSAGE` — was
correctly FLAGGED (FLAG-4 / N2), not silently dropped.** No UNFLAGGED extra deletion. ✓

### §RETIRED-NAME-SWEEP (bare, anchor-free, over `loremaster/loremaster/` + `scripts/`)
CLEAN — no dead twins. Two inert hits: (a) `scripts/test_search_score_survey.py:52`
`<answer>_ProcessLifespanGuard</answer>` (search-survey answer-string test DATA, not a symbol
reference — builder noted); (b) `server.py:9862` a PROVENANCE docstring in `_eager_build_with_retry`
("Re-homed from `_EagerStartupLifespan._acquire_eager_lease_with_retry`") — historical citation of a
deleted symbol, cosmetic. `TracingFastMCP` / `_lore_eager_guard` / `streamable_http_app` / `request_ctx`
/ `_EAGER_BUILD_FAILED_MESSAGE`: 0 prod hits. ✓

### §P9 collision guard
Local `registered_extension_names: set[str]` + `_ALL_BUILTIN_TOOL_NAMES` universe; raises `ValueError`
on collision with a built-in (enabled OR disabled) or an already-registered extension. The discriminating
leg (reserves DISABLED built-in names, which `on_duplicate` cannot see) is preserved with an explanatory
comment. `mcp.add_tool(wrapper, name=…)` → `mcp.tool(name=…, description=…, annotations=…)(wrapper)`
(coupling #2). No `on_duplicate="error"` (FLAG-5 — deliberate; the universe check is the pinned +
discriminating mechanism). ✓

### §GATES — re-run tails (2026-08-16, working tree over `ee4bced`)
⚠ **METHOD NOTE (my error, disclosed):** my first pass ran the migrated full suite + the baseline full
suite + the gates CONCURRENTLY against the one test store `:18000`. That manufactured 400–625 spurious
store-contention ERRORs in both runs (`test_surreal_*`, `test_mcp_server`, `test_migration_wire` all
timing out under 3× load). **I discarded those and re-ran each suite SERIALLY, alone.** The clean
numbers below are the ones I grade on.
- `uv run ruff check .`: **GREEN** (exit 0). ✓
- `scripts/typecheck.sh`: RED — but a **HEAD-vs-migrated diff proves ZERO new errors from the builder's
  code.** I ran `typecheck.sh` in the ee4bced scratch (md5 `31d012c9`) and against the working tree:

  | file group | HEAD (`ee4bced`) | migrated | delta |
  |---|---|---|---|
  | lorerunes test tree (3 files) | 89 | 89 | 0 |
  | loremaster | 102 in 8 files | 103 in **9** files | **+1 (`test_fastmcp_migration.py:163`)** |
  | spike script | 19 | 19 | 0 |
  | **`_auth_fixtures.py` (builder-EDITED)** | **3** | **3** | **0** |

  The ONLY new typecheck error is `test_fastmcp_migration.py:163` — the CONTRACT file (does not exist at
  HEAD; the builder may not edit it), a `no-any-return` on `_trace_middleware_class()`. server.py is
  mypy-CLEAN. The 3 `_auth_fixtures.py` errors are IDENTICAL at HEAD (lines 637/638 = packet-39 symbols
  `LoreTokenVerifier`/`GoogleOAuthConfig`; 872 = hosted `http_client` — all at lines the builder did NOT
  change), so the builder's `_auth_fixtures.py` edit is mypy-NEUTRAL. **Builder's "0 errors in my code":
  VERIFIED.**
- `pending_contract_gate.py --currency`: **FAIL**, but the failing legs decompose cleanly:
  - **typecheck RED_ORPHANED = 20** (store-independent, trustworthy): `test_fastmcp_migration.py:163`
    (1) + `scripts/fastmcp_migration_spike.py` (19). Exactly the builder's FLAG-2 set. The pending-39 +
    lorerunes reds are RED_ADJUDICATED (registered), NOT orphaned. The spike's 19 are LATENT-at-HEAD
    (fastmcp uninstalled at HEAD → mypy skipped its body; the dep swap surfaced them) — a real orphan
    the lead must adjudicate (fix or register), NOT the builder's writable set.
  - **pytest RED_ORPHANED = 490** — ⚠ **CONTAMINATED** (this currency run overlapped my concurrent
    suites). Re-running the currency gate CLEAN below; the builder's claim is 4 pre-existing orphans.

### §DELTA — zero-new-delta reproduction (clean, serial runs) — ✅ REPRODUCED EXACTLY
- **Migrated (working tree, clean serial run):** `uv run --no-sync pytest -n auto` → **450 failed / 0
  error** (PYTEST_EXIT=1) — matches the builder's Phase-6 450.
- **Baseline (`ee4bced` scratch, fastmcp venv held constant, clean serial run):** **448 failed / 0
  error** — matches the builder's HEAD-baseline 448 EXACTLY.
- **New-failure set (`comm -23` of the sorted migrated − baseline node sets) = EXACTLY 2:**
  1. `test_auth_composition.py::TestLoopbackPostureIsUnchanged::test_no_auth_settings_are_configured`
  2. `test_auth_identity_seam.py::TestLoopbackPostureServesWithoutCredentials::test_an_unauthenticated_initialize_succeeds`
  Both files ARE registered `packet-39-pending-build` in `scripts/pending_contracts.yaml` (RED_ADJUDICATED,
  not orphans); the breaks are `mcp.settings` reaches in their OWN test code, which packet 39 re-authors.
- **`comm -13` (fixed/gone) = 0.** **NO new failure the builder missed; NO regression outside the 2
  adjudicated pending-39 nodes.** The builder's zero-new-delta claim is INDEPENDENTLY VERIFIED against a
  true `ee4bced` baseline.

### §MUTATION — my own re-run of the 2 mutation proofs (migrated-tree SCRATCH `pkt59-mutation`, per the READ-ONLY brief)
Scratch provenance ASSERTED: `loremaster` resolves to `/home/ejprice/scratch/pkt59-mutation/loremaster/
loremaster/__init__.py` (inside the scratch — grades its own code, #140-safe); server.py md5 `0a84eb31`
== working tree. Both mutations restored byte-exact (`0a84eb31`) after.
- **FP-07 routing (routing-is-sharing):** positive control GREEN (2 passed unmutated). Mutation —
  bypass the shared policy: `await asyncio.sleep(backoff.additive_jitter(backoff_base_s))` →
  `await asyncio.sleep(backoff_base_s)` (server.py:9910). **RESULT: BOTH routing pins REDDENED** —
  `test_backoff_seam.py::…::test_eager_lease_uses_the_ADDITIVE_policy` +
  `test_fastmcp_migration.py::TestTheEagerHeavyBuildRetriesTransientFailures::test_the_inter_attempt_
  sleep_routes_through_the_shared_backoff_policy`. So `_eager_build_with_retry` genuinely ROUTES through
  `loresigil.backoff.additive_jitter` (a hand-rolled bypass is caught). ✓
- **B4 shield:** positive control GREEN (3 passed unmutated). Mutation — delete
  `anyio.CancelScope(shield=True),` from `on_call_tool`'s `finally` (server.py:10003). **RESULT: the
  discriminating asymmetry — `test_a_scope_cancelled_dispatch_still_writes_its_row` REDDENED (no row
  under anyio level-triggered cancel), while the positive control AND the asyncio-edge sibling
  (`test_a_cancelled_dispatch_records_ok_false`) STAYED GREEN** (1 failed, 2 passed). So the shield is
  load-bearing and the pin sees its removal. ✓
- **This resolves N1:** whatever the builder's cited md5, the DELIVERED tree preserves B4 + FP-07 routing
  under my own re-run.

### §WIRE — design §6.2 wire acceptance gate independently RE-VERIFIED
The `@wire` marker is NOT deselected by default (`pyproject.toml` `addopts = "--import-mode=importlib"`
only), so `test_migration_wire.py` ran INSIDE my migrated-clean full suite — **0 wire failures there**
(the two log mentions are a websockets DeprecationWarning summary, not failures). I ALSO ran the wire
suite ALONE (store free): **8/8 passed in 56.68s** — real uvicorn, real TEST store, tools/list (15
built-ins + `bump_counter`), serverInfo.version, a built-in AND extension call each landing exactly one
trace row read back from the store, spoofed Host → 421 / legit proxied Host → not-421, bad token → 401,
bad Origin → 403, heavy build exactly once across 4 concurrent + 2 sequential sessions. ✓

### §6.6-COLLECT — the 11 pending-39 files still COLLECT
`pytest --collect-only` on the 11 registered `packet-39-pending-build` files → **479 tests collected, 0
collection errors** (design §6.6 gate SATISFIED; FLAG-1's "they still collect" is correct — the 2 new
failures are RUNTIME AttributeErrors, not collection failures).

### §FLAGS — builder FLAGS 1–5 assessed (+ my own F1)
| flag | builder's claim | my verdict |
|---|---|---|
| 1 — 2 pending-39 left | leave per writable-set; still collect | **CONFIRMED** — exactly the 2 comm-23 new failures; both registered pending-39; 479 collect clean. Lead confirms leave-vs-fix (trivial fix). |
| 2 — currency orphans | spike(19) + contract:163 typecheck; 4 pre-existing pytest | **typecheck CONFIRMED** (RED_ORPHANED = contract:163 + spike 19; pending/lorerunes RED_ADJUDICATED). pytest orphan list from clean re-run below. Both typecheck orphans are OUT of builder's writable set / the contract author's — legit lead adjudication (register or fix). |
| 3 — allowed_hosts env knob | env, not config field | **CONFIRMED reasonable** — `_resolve_allowed_hosts` reads `LORE_ALLOWED_HOSTS`; wire test proves spoofed Host→421, legit→not-421. A `ServerConfig` field would be cleaner (config-schema change, out of scope). Noted for packet 39. |
| 4 — secret-leak drop | ACCEPT-with-trigger | **CONFIRMED real un-adjudicated DUAL gap (N2)** — security-auditor owns the ruling; recommendation reasonable given pre-production + local-boot-log-only exposure. |
| 5 — P9 no `on_duplicate` | universe check is the pinned+discriminating mechanism | **CONFIRMED sound** — `on_duplicate` cannot see DISABLED built-in names; the `_ALL_BUILTIN_TOOL_NAMES` + local-set guard reserves them. Deliberate, correct. |
| **F1 (mine) — C5/FG8 transport-mode rider dropped** | (builder did NOT flag) | **NEW CONFIRMED FINDING** — see §CONFIRMED FINDING F1 above. Benign today (fastmcp default stateful), fragile forward, no green pin. Recommend cheap fix or explicit ACCEPT-with-trigger. |

### §RESIDUALS (each with a verdict — read this table, not just the summary)
Clean currency gate (re-run alone, un-contaminated): typecheck **RED_ORPHANED = 20**, ruff GREEN, pytest
**RED_ORPHANED = 4**. Every residual adjudicated:

| # | residual | verdict | disposition |
|---|---|---|---|
| R1 | **F1 — C5/FG8 transport mode not set explicit + not green-pinned** | **REAL, builder-missed** | moderate; benign today (fastmcp default stateful), fragile forward. Lead: cheap fix (`stateless_http=False` + a session-id wire assert) or explicit ACCEPT-with-trigger. **The one finding that should be actioned before this is called closed.** |
| R2 | typecheck orphan `scripts/fastmcp_migration_spike.py` (19) | pre-existing-latent, out-of-scope | LATENT at HEAD (fastmcp uninstalled → body unanalysed); dep swap surfaced it. Spike deliverable, not builder's writable set. Lead adjudicates: fix or register. |
| R3 | typecheck orphan `test_fastmcp_migration.py:163` (1, `no-any-return`) | new, contract-author's | the contract file (builder may not edit). Needs the contract author's `cast(...)` or registration. Trivial. |
| R4 | pytest orphan `test_surreal_harness.py::…docstring_counts…` | pre-existing (RED at baseline) | already RED at `ee4bced`; the +2 migration test files nudge the derived import count further, but it was failing before. Fix = update the docstring count (its owner's job). NOT a new failure. |
| R5 | pytest orphans `test_secret_typing`, `test_comms_footer`, `test_ast_reach_helpers` | pre-existing (RED at baseline) | all three present in the baseline failure set; none migration-caused. Register or fix (owners'). |
| R6 | N2 / FLAG-4 — dropped secret-safe boot-failure message | real un-adjudicated DUAL gap | security-auditor owns the ruling; ACCEPT-with-trigger reasonable (pre-production, local boot log only). |
| R7 | 2 new failures = pending-39 `mcp.settings` (`test_auth_composition`, `test_auth_identity_seam`) | adjudicated `packet-39-pending-build` | the entire zero-new-delta; both registered, still collect; packet 39 re-authors. Confirm leave-vs-fix (trivial). |
| R8 | N1 — server.py md5 `0a84eb31` ≠ builder-cited `89eb7e9` | resolved | I re-ran both mutation proofs on the DELIVERED tree; both discriminate. The delivered artifact is sound regardless of the receipt md5. Cosmetic receipt-honesty note. |
| R9 | provenance docstring in `_eager_build_with_retry` names deleted `_EagerStartupLifespan` | cosmetic | a historical "Re-homed from" citation; not a live reference. Optional scrub. |

**NO residual is a correctness break in the delivered code.** R1 is the only one that is a real
(latent) defect in the migration's own surface; the rest are pre-existing orphans, contract/spike
typing debt out of the builder's writable set, or ruled/flagged design decisions.

## FINAL VERDICT: **GO**
The migration is correct and complete against the design (§3 coupling map, §5 DUAL, §6 gates) and the
contract. Zero-new-delta is reproduced EXACTLY against a true `ee4bced` baseline (2 new failures, both
adjudicated pending-39; none missed). B1–B8 preserved with the two load-bearing pins (FP-07 routing,
B4 shield) mutation-proven on the delivered tree. Deletes are clean and reconciled (⊆ planned + 1
correctly-flagged extra). host_origin_protection wired + wire-proven (8/8); P9 guard sound;
`_record_tool_trace` reused as one emission path. ruff GREEN; the builder's own code adds zero mypy
errors; every currency red is pre-existing, out-of-scope, or the contract author's.
**Ship it, with R1 (C5/FG8) actioned or explicitly accepted by the lead first**, and R6/FLAG-4 routed
to the security audit.
