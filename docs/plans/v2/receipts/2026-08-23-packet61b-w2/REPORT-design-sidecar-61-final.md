# REPORT — design-sidecar-61

brief-base v14 read · brief project v7 read

**State:** done (standing by for follow-ups — a long-running design sidecar).
**Deliverable:** `docs/design/2026-08-22-packet61-pdp-audit-rulings.md` — this REPORT is a pointer,
not a copy; the substance lives in the doc (packet-60 ruling format). Sent to `lead-61` via
`lore_comms #5171` (signal).
**Deviations:** my deliverable is a design DOC, not a `REPORT-*.md`; this file exists only so the
idle-gate's v1 default resolves (my `{"artifact": null}` standing-by contract was not honored).
**Packages considered:** none — no mechanism built (design rulings only; the doc's Fork A/I rule
MECHANISMS but the packages analysis is design §11's, verified there: bespoke PDP over the graph).
**Reuse ledger:** none — no code written (design authority; the doc rules WHERE reuse must happen:
Fork B `lorerunes` core, Fork I `wrap_engine_rejection` extraction, Fork F `KeepStore` method).
**Graded:** N/A — this is a design ruling, not a verdict on another artifact.
**Decisions needed (operator, on return — 3 loud countermands + 2 durable cross-scope items):**
- Fork A — the single-brain MECHANISM (IR + two interpreters + live-store oracle vs one literal
  SurrealQL string). Ruled the IR; countermand stated.
- Fork C — `principal-private` WRITE/DELETE owner (ruled exact `(principal,agent)`; countermand to
  principal-wide within-principal collaboration).
- Fork G — the audit TRIGGER (ruled: fires when the admin bypass is load-bearing; countermand to
  every admin mutation incl. own-row).
- #400 extraction + #398/#399 invariant — cross-scope, surfaced durably (pre-blessed / law-mandated),
  not escalated.
- FR-4 — #402 keeper-on-principal-delete: ruled REFUSE-WHILE-KEEPING (countermand to cascade-delete).
  One sizing sub-choice for the lead: land the reassign-keeper/delete-keep remediation verbs in 61a-w2
  (recommended) or defer as a named follow-up (keeper-principals un-deletable meanwhile — safe).

## Receipt pointers (section — never re-pasted)
- Ruling summary table + all 12 per-fork rulings: the ruling doc, §"Ruling summary" + §"Fork A".."Fork L".
- Sizing verdict (SPLIT >0.30) + wave decomposition (61a Foundations+Audit → 61b PDP+resolver+coverage
  + security-auditor): ruling doc §"Fork L".
- Store-law compliance checklist + the 3 named live-3.2.4 probes: ruling doc §"Store-law compliance
  checklist" + §"Fork E".
- Escalation status (nothing escalated; 3 countermands + 2 durable items): ruling doc §"Escalation status".
- Ledger: #398 + #399 (recurrence invariant, Fork J), #400 (DRY extraction, Fork I), #401 (stderr,
  Fork K), task `06b195e306a34b6391174477bc7744e7` (the invariant, ruled placement=first).

Standing by. Follow-ups arrive via SendMessage wake + `lore_comms`; I will not exit or wake-loop.
