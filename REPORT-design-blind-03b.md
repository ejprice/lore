# REPORT-design-blind-03b — fresh (blind) 03b design rulings, r2

brief-base v6 read

- state: **done** — `docs/plans/v2/03b-design-rulings-r2.md` written; blindness held (no struck file opened; one near-miss disclosed below as a non-event).
- deviations: none. Writable set honoured (two files). No git mutation.
- decisions-needed (operator/lead): **E1** eval spend · **E2** stale packet label in committed contract (authorize with the contract wave) · **E3** drain skew block (ruled IN — confirm) · **E5** telemetry failure-posture reading of DESIGN-LAW §14 · **E6** fastmcp migration = NO for 03b (ledger it) · **E8** drain's unbounded pending read → findings row.
- doc structure: §0 entry-state facts F1–F7 · A surface B1–B11 · B telemetry T1–T8 · C client acceptance C1–C4 · D self-attack D1–D15 · E escalations E1–E9 · F residuals F1–F5.
- probe receipts: FastMCP subclass-override interception (control + wire-path + error legs) — §Probes below; mcp==1.27.2 confirmed; `RequestContext.request` = transport request (mcp-session-id reachable), read from installed SDK source.
- key novel rulings: all-tools trace via `TracingFastMCP.call_tool` override (T1) · trace schema delta all-`option`, global `trace_seq` native sequence (T2/T3) · declared-only identity + transport correlator, no guessing (T4) · awaited-inline emission, tool outcome always wins (T5) · uniform fenced drain bodies (B4) · ACK REQUIRED keyed on `acked_at`, window-scoped (B4.4) · retired-recipient reject + `set_status` closed vocabulary (B2) · per-action `limit_cap` on `CommsActionSpec` (B6) · consumer-eval gate, floor-model pinned, machine-graded (C).
- inherited-law compliance: 03a-2 rows 1–11 disposition table (B10); R1-deferral honoured (no per-row question markers); #143 adjudicated as standing bound (B8.5); the `{msg}` promise-registry KNOWN BOUND made a design constraint (B8.4).

---

## Blindness accounting

Read at `git show 0223291:` — packet 03b file, comms-subsystem.md, 03a-2 rulings,
store reference, packet 03 file, `test_comms_tool.py`, `test_comms_promise_registry.py`,
`test_surreal_store.py` (targeted). Read from working tree (untainted per brief):
DESIGN-LAW.md, the garden design plan, production `server.py`/`messages.py`/`agents.py`/
`briefs.py`/`agent_ref.py`/`render.py`/`sanitise.py`/`store/surreal.py`/
`store/surreal_schema.py`/`config.py`, installed `mcp` package source, and the PERMITTED
`REPORT-scout-147-traces.md` (facts only; its design prescriptions were read as flagged
forks and re-derived independently — where my rulings agree with its recommendations
(all-tools, global sequence, subclass-override, ride-the-trace-table) the agreement is
derived in the doc from law + probes, not adopted by citation alone).
**Not read:** any repo-root `REPORT-*.md`, the struck rulings doc, anything else under
`receipts/2026-07-24-packet03b/`, `INDEX.md` at HEAD, tag `pkt03b-tainted-corpus`, any
post-`0223291` commit content, any working-tree test file (git status shows the struck
session modified seven test files and deleted `test_trace_telemetry.py` — none opened;
committed-contract reads were all at `0223291`).
Near-miss disclosure: none — no struck file was opened even partially.

## Probes (all this session, 2026-07-24, with controls)

1. **FastMCP subclass-override interception** (installed `mcp==1.27.2`, repo venv):
   base-class CONTROL recorded nothing; subclass override intercepted (a) direct
   `call_tool`, (b) the lowlevel wire handler captured at `__init__`
   (`request_handlers[CallToolRequest]` → bound override), (c) a raising tool (override
   ran; `ToolError` surfaced). 3/3 legs + control. This is T1's load-bearing fact.
2. **No middleware API on FastMCP 1.27.2** — read from installed source
   (`_setup_handlers` is the sole registration; no `add_middleware`/hook attrs), 
   corroborating the scout's measurement independently.
3. **`RequestContext.request` carries the transport request for streamable-http**
   (read: `mcp/shared/context.py`, `lowlevel/server.py` request_ctx population,
   `streamable_http.py` `ServerMessageMetadata(request_context=request)` +
   `MCP_SESSION_ID_HEADER`) — T4's transport-correlator channel.
4. **Cheap scout re-verifications:** bare anchor-free grep for `record_trace` (definition
   + prose + tests only — zero production callers, matching scout §2); committed
   trace-pin shape check (per-key, not exact-shape → T-series is amendment-free, doc §0.F6).

## What the lead should know first

- The committed contract at `0223291` already pins the nine-action set, the three new
  specs, broadcast semantics, dispatcher forwarding, and the config-driven drain default
  — **but NO send/drain/ack render pins exist**. Every render shape in B3–B5 is NEW and
  says so; the contract phase + adversary own pinning them.
- Production `messages.py` already implements 03a-2 R2's conjunct and R4's
  order/short-circuit; **R3's bounding and both message indexes are open builder work**,
  and the index free window closes at 03b's deploy (doc §0.F2, B10 rows 2–3).
- `CommsConfig` lacks `drain_limit` (committed pin requires it) — B6.
- The doc's one deliberate divergence from the `0223291` comms-subsystem tool table:
  drain carries the heartbeat skew block via a SHARED helper (B4.1, escalated as E3);
  drain does NOT carry `since=` (packet 05, kickoff ruling 6) nor per-row question
  markers (operator R1 deferral).

Final pointer: the deliverable is `docs/plans/v2/03b-design-rulings-r2.md`; this report
is its provenance + receipts. Both files are the only writes this session made.
