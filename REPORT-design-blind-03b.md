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
  — ~~but NO send/drain/ack render pins exist~~ **[CORRECTED — see ERRATUM item 1: the
  committed promise registry fixes the render VOCABULARY and forces it into `server.py`;
  only behavioural shape pins are absent. B3–B5 are semantics grafted onto the committed
  templates per the amended doc's §A-GRAFT.]**
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

---

## ERRATUM (2026-07-24, post-adjudication — appended after the lead admitted
`DIFF-adjudication-03b.md` as the certified interface to the struck record)

Two claims in this report / the rulings doc were probed FALSE by the adjudication; both
are corrected in the amended rulings doc (§G amendment log) and recorded here because
this report is the durable artifact that carried them:

1. **"NO send/drain/ack render pins exist" — FALSE at the template layer.** True only of
   behavioural SHAPE pins. The committed promise registry already fixes the render
   vocabulary as registered template literals, and `test_no_dead_registry_entries` /
   `test_registered_iff_proven` FORCE every registered literal into `server.py` — the
   committed wording is obligatory, not advisory. My "targeted" read of the registry file
   (classification mechanics + KNOWN BOUNDs, not the entry list as a vocabulary spec) is
   the miss; it is the structural cost of blindness the diff step exists to pay. The
   rulings doc's B3–B5 wording is superseded by §A-GRAFT (semantics graft onto committed
   templates); the one genuine conflict (fenced bodies vs the committed inline `{body}`
   slot) is fork FK-1 — PENDING-OPERATOR at fold time; since RULED: FENCE (see POSTSCRIPT).
2. **Doc §0.F6 / T8 "the T-series is amendment-free" — FALSE.** Derived from
   `test_surreal_store.py` alone; two committed pins in files outside that read set go
   RED under the T-series (probed, adjudication §P9):
   `test_surreal_schema.py::…test_trace_core_scalar_fields_are_defined` (old scalar
   types for `hit_count`/`session`) and
   `test_surreal_fakes.py::test_record_trace_signature_matches_real_store` (exact 7-name
   list). Both fixes are strengthen-only, mutation-proven, batched as fork FK-3 —
   PENDING-OPERATOR at fold time; since RULED/authorized (see POSTSCRIPT). The narrow per-key claim about `test_surreal_store.py` itself
   stands.

Lesson, stated for the next blind derivation: an "amendment-free" claim is a claim about
EVERY committed file, and must be grepped tree-wide (bare, anchor-free) against the
changed surface's names — not derived from the one contract file the design happened to
read. Same class as the repo's two-populations counting law.

Minor corrections folded in the same pass (full record: rulings doc §G): T5.3's
cancellation concession under-claimed its own `finally` mechanism (AC-06, probed —
`finally` placement now load-bearing + pinned); B10 row 1's "the R2 pin is still owed"
was false at the reset baseline (AC-25 — both pins exist; do not re-author); B4.2's
unconditional thread cell contradicted my own B3.2 principle (AC-22 → new ruling B14).
New rulings added at the adjudication's routing: B12 (per-verb dispatcher-serves-render
pin class — the no-op-fix door my self-attack missed), B13 (peek renders no trailer),
B14 ({context} cell), B15 (elision arithmetic), T2.1 (the 06-read trace index inside the
free window). All fork-dependent elements carry FK-n markers mapping to
DIFF-adjudication §6.

**POSTSCRIPT (same day, final pass):** the FK batch is now RULED as the adjudication
recommends (operator granted the lead fork authority — packet file §OPERATOR GRANT
(second), `1e3a249`); every FK marker in the rulings doc updated PENDING-OPERATOR →
RULED (FK-1 = FENCE). The operator TRUST DOCTRINE (packet file §grant + lore memory
`cd4c22c3`) is folded as new §C5 + battery tasks 12–15: four keyed honesty probes
(failure-admission, count-consistency, teaching-vs-behavior, and the CALL_AGAIN /
ROUTE_AROUND routing test, graded, never waived). The rulings doc is the settled
contract-phase spec; §G carries the complete amendment record.
