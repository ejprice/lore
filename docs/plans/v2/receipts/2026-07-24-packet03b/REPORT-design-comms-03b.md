brief-base v6 read

# REPORT-design-comms-03b — kickoff rulings delivered; STANDING BY (long-running sidecar)

## SUMMARY BLOCK
- state: **done (kickoff Q1–Q4) — agent remains ACTIVE, standing by for follow-ups** (long-running
  design sidecar per spawn brief; idle-between-questions is benign, do not wake-loop).
- deviations: (1) spawn brief named my writable set as the design doc ONLY; this report file is
  written per brief-base §1's supply-an-address rule after the idle-gate demanded it — it carries
  POINTERS, no new content. (2) none other.
- decisions-needed: **none for the rulings** (all within delegated design authority). Two priced
  deferrals the lead may carry to the operator: drain-row question-marker → packet 05 (doc
  Residual 1); wiring `record_trace` for non-comms tools → follow-up packet (doc Residual 2).
- receipt POINTERS (the deliverable): `docs/plans/v2/03b-comms-surface-design-rulings.md`
  — S1 coverage-premise probe (EXECUTED 2026-07-23 @ `6a66671`, 5 legs incl. both controls, PASS)
  · S2 #145 disposition (two gate pins + bound/trigger) · S3 #143 adjudication (bound stays; two
  static strengthening pins) · S4 served shapes (send/drain/ack, verbatim) · S5 INSTRUCTIONS text
  · **S6 v2 (re-ruled 2026-07-24 after the operator's all-tools widening): one seam
  (`TracingFastMCP.call_tool`), one writer, global `trace_seq`, annotation channel; v1's
  `comms_calls` counter + drain notice line RETIRED** · **S7 caller identity at the generic seam
  (transport-session key + data-derived join, self-attack table)** · #147 diagnosis (never wired;
  corroborated by `docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md`)
  · Residuals 1–9 (2 resolved-by-widening; 4 upgraded) · delta table A–I (F/G/H at v2).
- answers sent to team-lead via SendMessage 2026-07-23 (`9f510f11…`) and 2026-07-24 (`4f56f02c…`);
  the doc, not the messages, is the record.

## Body
This agent writes no code and no tests; the design doc above is the whole deliverable. Notable
findings surfaced there (measured at `6a66671`, 2026-07-23): the committed ACK-REQUIRED proof
fixtures are an `acked_at` monoculture (a grade-only build passes them — discriminating pin
mandated, doc S4.2/Residual 3); the value-carried-promise bound's pin under-enforces its own
docstring (`"{msg}"`-only — ∀-ban mandated, doc S3/Residual 5); 03a2-R6 clause 3 over-claimed
render-layer self-explanation (corrected by the ALREADY-ACKED trailer, doc S4.2). No ledger row
was named in my brief → board untouched per brief-base §5.
