# REPORT — migration-author

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done (incl. a REVISION PASS folding the lead-verified hand-roll inventory — §Revision below)
- **deviations:**
  - ⚠ **§5b OVERTURNED in the revision pass:** my first draft adjudicated `_EagerStartupLifespan`
    PRESERVE+PIN; the lead-verified inventory shows it + `_ProcessLifespanGuard` are a ~150 LOC DELETE
    (fastmcp's once-per-process ref-counted `lifespan=` obviates them). Now spike-gated (§6.6-1), a real
    KEEP/DELETE fork. This is the biggest change; the first-draft PRESERVE survives only as the NO-GO branch.
  - INDEX row PLACED just-before-39 (minimal hard constraint); my own recommendation (before 54)
    is ESCALATED as D2 rather than encoded in the row position — the running wave-D D&D track is not
    mine to resequence unilaterally.
  - Packet 39's INDEX `Depends on` cell NOT edited (outside writable set) — FLAGGED as D3.
- **Packages considered:** `fastmcp>=3.4,<4` — verdict **replace** the façade class
  (`mcp.server.fastmcp.FastMCP` → `fastmcp.FastMCP`), **keep** `mcp` for `mcp.types`. Read basis: the
  spike read fastmcp 3.4.7 installed source (`inspect.getsource`); blast-radius did the pypi/docs pass;
  the contract re-reads installed 3.x source before pinning. This IS packages-over-hand-rolling working
  in reverse-retirement: `TracingFastMCP` hand-rolled a trace funnel because `mcp` had no middleware;
  `fastmcp` now provides one, so the bespoke subclass retires.
- **Reuse ledger:** 1 new reusable symbol SPECIFIED (not built) — the `on_call_tool` trace middleware.
  | new symbol | lore query run | returned | disposition |
  |---|---|---|---|
  | trace `on_call_tool` middleware | `lore_get_symbol TracingFastMCP` + `_record_tool_trace` | `TracingFastMCP.call_tool` is the SOLE trace funnel today; `_record_tool_trace` is the write policy | HAND-ROLL the funnel (middleware) BUT **REUSE `_record_tool_trace` unchanged** (M4) — no second emission path; the build's DRY ledger must re-prove this |
- **Graded:** n/a — this is DESIGN AUTHORSHIP, not a verdict over another artifact's code. (HEAD-at-report
  `41287c5`; I authored a new doc + an INDEX row, graded nothing.)
- **decisions-needed:** NONE — D1–D4 all RULED by the operator 2026-08-15 (§Finalization): D1 STANDALONE
  deploy · D2 BUILD NOW (immediate next build) · D3 39's `Depends on` gains `59` (lead edits on commit) ·
  D4 `mcp` TRANSITIVE (opposite my recommendation) + 2 build-time caveats + full-`fastmcp`-umbrella line.
- **receipt POINTERS:**
  - Deliverable 1 (design doc) → `docs/design/2026-08-15-fastmcp-3x-migration.md`
  - Deliverable 2 (INDEX row) → `docs/plans/v2/INDEX.md` row `| 59 |` (inserted before the `| 39 |` row)
  - Coupling→migration map → design §3 · removed-behaviour inventory → design §5 · acceptance gates →
    design §6 · packet-39 sequencing → design §7 · 4.0-later → design §8 · self-attack → design §9 ·
    escalations → design §11.

---

## What I built (deliverable)

A packet-59 DESIGN doc a tdd contract author can build from, plus its INDEX row. The packet:
**migrate lore's MCP server off the official `mcp` SDK's bundled `FastMCP`
(`from mcp.server.fastmcp import FastMCP`) to the standalone `fastmcp>=3.4,<4` package** — a pure
substrate swap with NO served-behaviour change, delivering the middleware substrate packet 39's
enforcement will be authored on.

Load-bearing facts, all from the committed receipts + memory (cited section-exactly in the doc, built
on, not re-derived) and GROUNDED against live reads at HEAD `41287c5`:
- fastmcp 3.x WRAPS mcp v1 → **KEEP `mcp`; `mcp.types` imports do NOT move** (blast-radius §0/§2d).
- Production surface is ONE file (`server.py`); auth is bespoke ASGI, zero SDK coupling (blast-radius §1a/§2a).
- The spike MEASURED (lead-verified) that fastmcp 3.4.7 `on_call_tool` refuses on the wire and
  `on_list_tools` hides on the wire, and packet-39's `get_access_token()` seam SURVIVES stateful +
  stateless (spike §Q1/§Q2/§Q3) — so this migration dissolves 39's four-adversary-pass dead-on-wire blocker.
- 4.0 is the LATER, larger step (mcp SDK v2 + sessionless protocol) — a separate future packet (§8).

## Grounding (live reads, dogfood protocol)
I used lore-first for all structure questions: `lore_recall` (decision + spike memory), `lore_index`
(fresh; git_ref `41287c5`), `lore_get_symbol` / `lore_read` on `TracingFastMCP`, `TracingFastMCP.call_tool`,
`_record_tool_trace`, `build_mcp_server`, `build_asgi_app`, `_EagerStartupLifespan`. This corrected the
blast-radius report's possibly-drifted line numbers (branch moved `562c9bd`→`91fc30e`→`06b7142`→`41287c5`)
and let me build the removed-behaviour inventory from the ACTUAL code, not inherited line refs.

**Grep fallback SAID OUT LOUD (sanctioned case (c), cross-cutting textual map):** I used `bash grep`
over `INDEX.md` — a 1881-line / 96k-token markdown doc — to locate the packet TABLE rows and packet-39
references (a non-symbol, cross-cutting textual seam lore's symbol graph does not index). This is the
sanctioned "cross-cutting multi-question map" fallback, not a lore weakness — no friction filed.

## The two swaps + removed-behaviour inventory (DUAL law — design §5)
The design does the removed-behaviour inventory the brief asked for, adjudicating each behaviour
PRESERVE+PIN / DROP / OLD-BUG / SPEC-SILENT:
- **`TracingFastMCP.call_tool` subclass → `on_call_tool` middleware** (§5a): 8 behaviours (B1 wire
  funnel ∀ tools; B2 outcome-always-wins + loud-invisible failure; B3 `ok`-latch excluding
  `CancelledError`; B4 the **shielded + bounded `finally`** — required because the request is still
  under MCP's anyio cancel scope inside middleware; B5–B8 the emitter's substrate change). `_record_tool_trace`
  is REUSED.
- **`streamable_http_app()` → `http_app(path=)` + lifespan propagation** (§5b): C2 (the
  `_EagerStartupLifespan` must enter fastmcp's `http_app()` lifespan or the session manager never
  inits — HIGHEST WIRE RISK) + C4/C5 bespoke Origin/Bearer unchanged + C6 explicit transport-mode pin.
- Constructor P6/P7 (§5c): `version=` ctor kwarg replaces the `_mcp_server.version` reach; host/port
  repoint to `config.server`; the "must be the tracing subclass" pin REWRITES to "must install the
  trace middleware".

## Adversarial self-attack (design §9) — what would ship FALSE-GREEN
Eight FG scenarios, each with a discriminating pin folded into the acceptance gates. Headliners:
- **FG1 (the #131/#139 class, biggest risk):** in-memory-transport tests never run the ASGI lifespan,
  so "the container serves NOTHING" passes the whole suite green. → REQUIRED in-image conformance run
  + a REAL uvicorn wire smoke (§6.1/§6.2).
- **FG2 (reach attack):** the middleware funnel coverage is now a CHECKED variable, not "by
  construction"; if it fires for built-ins but not `add_tool`-registered extension tools, extension
  calls silently stop tracing. → wire smoke traces a built-in AND an extension tool. **Second-pass
  refinement:** the prod extension registry ships EMPTY (packet 46), so the pin must register the
  **packet-47a fake-domain fixture** to have an extension tool to funnel — folded into §6.2.
- **FG3:** the cancellation/`ok`-latch dropped in the rewrite corrupts the numerator. → the pins are
  re-authored (not deleted) and mutation-proven.
- **FG5 (the DUAL trap):** a contract written for the fastmcp world that never checks the old world's
  virtues survived — the §5 inventory + contract-adversary deleted-code enumeration is the mitigation.
- **FG7 (second-pass):** the pending-39 tests import `mcp.server.fastmcp`; keeping `mcp` (M2/D4) keeps
  them COLLECTING — the migration must run the full collection once and gate "zero-new-delta vs #333".

## Two unmeasured bounds carried, NOT closed (design §6.4 — brief requirement)
Per the spike's own §Q3 rider: (1) real OAuth verification path (tokeninfo POST) — spike used a static
`TokenVerifier`; (2) long-lived token-refresh — spike used a single non-refreshing token. Both are
packet 39's to close; carried as PIN-THE-MISS bounds with re-open triggers pointing at 39. Mitigation
for 39: adopt `fastmcp.server.dependencies.get_access_token()` (hardened request-scope-first superset).

## Packet-39 sequencing (design §7) — proposal, 39's file untouched
39's enforcement should be authored on `on_call_tool` (refuse-before-body) + `on_list_tools` (hide) —
the TWO-hook requirement (a port of only `on_call_tool` drops the visibility half). KEEP 39's
per-request AuthContext/PermissionResolver identity model; DROP the scoped ToolManager subclass + R16
`_setup_handlers` AST pins + `test_wire_discipline.py`; RE-EXPRESS the F3 session-resumption pin as
per-request identity isolation; CARRY the derived-∀-EFFECT pin (now load-bearing — middleware
reintroduces placement as a free variable, the WB48 class). Building 39 before this migration = building
it twice (blast-radius §7.5).

## Revision pass — folded `REPORT-handroll-inventory.md` (lead-verified, directive #4212)
The lead handed off the exhaustive hand-roll inventory (to be archived to
`receipts/2026-08-15-fastmcp-migration/`). Folded BEYOND the blast-radius baseline, per the directive:
- **#8/#9 lifespan apparatus → DELETE (~150 LOC).** `_ProcessLifespanGuard` + `_EagerStartupLifespan`
  exist SOLELY to paper over the mcp SDK's per-session lifespan re-entry; fastmcp's once-per-process
  ref-counted `lifespan=` obviates both. `[inferred]` → SPIKE-VALIDATION gate §6.6-1 (GO ⇒ delete;
  NO-GO ⇒ keep). Overturns my §5b draft; also deletes the `_lore_eager_guard` attr (§5c-D5). INDEX row
  + §0 M11 updated.
- **#3 `transport_security` UNSET = a SILENT security gap TODAY** (zero framework Host/DNS-rebinding
  validation) → fastmcp `host_origin_protection` closes it = a migration BENEFIT (§5b-C3′, §6.6-3, §0
  M12). Carried the §3 Origin-ORDERING caveat as spike-item §6.6-2: does `host_origin_protection` run
  BEFORE the TokenVerifier? If after, the bespoke Origin layer stays outermost for packet-39 §8 R9's
  "zero outbound Google call" property only.
- **#5 `mcp._tool_manager` → `_local_provider` is a HARD BREAK in fastmcp 3.x (loud=good).** §3 P9 now
  REPLACE onto the public `mcp.get_tool(name)` / `FastMCP(on_duplicate="error")`.
- **#184 re-open trigger (b) RESOLVED** (§7 provenance, §0 M13): packet 39's enforcement is the SECOND
  non-telemetry consumer of the `call_tool` seam, so the previously-03b-REFUSED migration is now
  sanctioned and the #102 law makes it a SHARED middleware substrate. Lead annotated #184 → 59.
- Also folded #14 (`running_asgi_app` → `asgi-lifespan` `LifespanManager`, packet 39 §14-ruled) into §4.
The three new spike-validation items (§6.6) are cleanly separated from the PROVEN set (the existing
spike's measured GO) — per the directive's "add to the SPIKE-VALIDATION gates, not the proven set."

## Finalization — D1–D4 rulings applied (directive #4214)
The operator ruled all four escalations; recommendations → rulings across §0 (M8/M9), §3, §7, §11, §13
and the live INDEX row:
- **D1 STANDALONE deploy** (rebuild+recreate + in-image gate) — my recommendation, ruled.
- **D2 BUILD NOW, ahead of the wave-D queue** — packet 59 is the IMMEDIATE NEXT BUILD (exceeds my
  "before 54" recommendation). INDEX row status marks it; table position (before 39) keeps the hard
  constraint.
- **D3** — 39's `Depends on` gains `59`; the LEAD makes the one-cell edit on 39's row at commit.
- **D4 `mcp` TRANSITIVE** (opposite my "keep explicit" recommendation): REPLACE `"mcp[cli]>=1.27"` with
  `"fastmcp>=3.4,<4"`; `mcp` rides via `fastmcp-slim`'s `mcp<2.0` pin. Two build-time caveats added
  (§11-D4): (a) the transitive pin is BARE `mcp` — no `[cli]` extra — so the build confirms nothing
  reaches mcp's `[cli]` deps, else re-add explicitly; (b) `mcp.types` is now an undeclared direct import,
  operator-ACCEPTED and noted. Pending-39 tests still COLLECT (mcp still installed transitively) — full
  collection run once, zero-new-delta vs #333.
- **Clarifying line added** (§3): the dependency is the FULL `fastmcp` umbrella
  (`= fastmcp-slim[client,server]` + opt-in extras), NOT `fastmcp-slim` directly; lore needs NO extras
  (LLM-SDK / apps / code-mode / tasks) — `fastmcp[tasks]` etc. only if a future feature needs it.

Ready for the lead to archive the receipts + commit the packet (incl. the 39 `Depends on` edit).

## No scope narrowing
Nothing dropped or declared out of scope. The genuine forks (deploy posture, exact slot, 39's
dependency cell, mcp dep line) are ESCALATED in design §11, not silently resolved. The size estimate
(~0.25–0.30 wu →split if ≥0.30 at kickoff) and the exact 3.x accessor shapes (verify at contract) are
named bounds in design §12.
