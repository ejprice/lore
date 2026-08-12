brief-base v12 read
brief project v7 read

# REPORT — fable-design-06 (Fable design sidecar, packet 06)

## SUMMARY BLOCK
- state: **done** (three design deliverables + one ground-truth correction that expands scope)
- deliverables: `docs/plans/v2/design/2026-08-11-packet06-drill-and-obedience.md` (A/B/C, all three)
- Packages considered: none — no mechanism specified (advisory design pass; SurrealQL SELECTs
  are handed to the builder with the #107 verify-order, not a library choice).
- Reuse ledger: none (no new symbols; the obedience graders REUSE the shipped `ToolCall`
  parser + the `Graders`/positive-control idiom in `comms_consumer_eval.py`).
- Graded: n/a for a design proposal, EXCEPT the §0 correctness claim — Graded: `c12d158` ·
  HEAD-at-report: `c12d158` · SAME. The STALE-is-live claim is measured at this sha.
- deviations: none.
- decisions-needed (forks written into the design doc §D, for the operator):
  1. **D-1 — retire the ⚠ STALE glyph as a 06 build item?** (RECOMMEND YES). Obligation #1's
     premise "04b-2 replaces it with the AGE" is **FALSE at HEAD** — STALE ships in two renders.
  2. **D-2 — a minimal non-vacuity floor at `brief_publish` (#257)?** (RECOMMEND a small floor;
     needs an operator ruling — it constrains a write verb).
  3. **D-3 — cadence: register param vs contract-file key?** (RECOMMEND register param; file
     stays single-key).
- receipt pointers:
  - design of record: `docs/plans/v2/design/2026-08-11-packet06-drill-and-obedience.md`
    (§0 ground-truth · §A obedience battery · §B drill choreography · §C brief-base v13 · §D forks)
  - ground-truth correction filed: finding **#360** (STALE not retired) — `lore_findings action=get 360`
  - obligation source: `docs/plans/v2/06-comms-protocol-drill.md` §INHERITED FROM 04b; the
    STALE ruling: `docs/design/2026-07-28-04b-model-consumer-audit.md` §10.2–10.4 + finding #259

## THE ONE THING THE LEAD MUST ACT ON FIRST
Packet 06 inherited a **false premise**: obligation #1 says the ⚠ STALE glyph is already
retired ("04b-2 replaces it with the AGE"). It is **live at `c12d158`** in
`server.py::_render_comms_fleet_row` AND in the #262 held-task note (added by the most recent
commit `e69c45a`, *after* #259 ruled it retire). 04b-2 shipped the fleet COLUMNS, never the
retirement. So **both** the STALE retirement (#259 candidate b) **and** the `overdue` verdict
(candidate d) are unbuilt and both fall to 06 — the drill cannot avoid asserting STALE by
choreography alone. Recommendation: 06 retires the glyph (both `_heartbeat_is_stale` callers) as
a build item, folded into the `overdue` build (design doc §D-1). Filed as finding #360.

## (A) #195 obedience-measurement battery — the property invented
- **What "obey" means, mechanically:** the planted instruction names a keyed, detectable
  action; the probe grades the DIVERGENCE between the protocol-correct action and the
  obey-action. Two probes: **O1 (primary)** — a misdirected send to an injected target
  (`fixer-z`, ∉ roster) that the protocol NEVER requires, so taking it is unambiguously
  obedience (orthogonal to comprehension); **O2 (rotation)** — ack-scope subversion reusing the
  SHIPPED `hostile_body` injection, keyed on the injected superset/emptiness (a different
  predicate than task 1's exact-set).
- **Mandatory positive control + a differently-broken negative** for each grader (repo law): a
  compliant answer (PASS), a DID-obey transcript (FAIL fires), and a wrong-for-a-different-reason
  answer that must NOT be mis-scored as obedience. Table in §A.2.
- **Real-LLM probe** (03b precedent — a string assertion can't see obedience): rides the C1
  harness verbatim (fresh model, served surfaces only, floor model pinned, 3 consecutive runs,
  full-population receipt at exit). Graders are deterministic + unit-tested with controls.
- **Defence layers — build vs measure:** render-side (framing) is SHIPPED; teaching-side is
  CHEAP → **build** it in brief-base v13 (§C-4); protocol-side (trust-per-sender) is heavy →
  **do NOT build** — the probe MEASURES residual obedience, and only a measured persistent-obey
  after render+teaching escalates a protocol-side design as an operator fork (measure-then-tune).
- **§15 applies** (test-instrument): the obedience probe itself gets a contract-adversary pass
  grading its discrimination. Contract sketch handed to the eventual author in §A.6.

## (B) The drill choreography
- 11-step scriptable arc (design doc §B.1), cast = `lead-06` + `drill-worker-06` (drains, sees
  skew, acks the directive) + `drill-prober-06` (parks a question, is killed, orphans, released).
- **The clock:** `overdue` is TRUE BY CONSTRUCTION for any cadence, so the prober declares a
  SHORT cadence (≤2m) and the lead reads `fleet` after the kill → `overdue (declared ≤2m, silent
  Nm)` renders on a compressed clock. Genuine dogfood.
- **Join-quality receipt (first-minute, DD-5.b):** exact SELECTs specified (agents-per-transport-
  session and transport-sessions-per-agent) with the 1:1-vs-1:many verdict; syntax verified by
  the builder against surrealql-tests + a :18000 probe (the #107 order), never assumed.
- **Decay curve (DD-5.c)** + inference-free fallbacks (wall-clock gaps, fleet-ordinal gaps,
  register-then-never-drains) and **loss-rate read (DD-4.d)** — SELECTs in §B.2–B.4; re-open
  trigger >0.5% or any confirmed lost directive.
- **Receipts (§B.6):** the packet-Exit set PLUS the join/decay/loss reads and a `fleet` render
  proving orphan-detection rides `overdue` and asserts NO ⚠ STALE.
- The `cadence` register param build (obligation #2) fully specced in §B.7 (option<string> field
  per the #107/#304 precedent; a PAYOFF-STATING param description per the R1 lesson).

## (C) brief-base v13 delta (recommend; the lead applies)
Four additions + one promotion, exact text in design doc §C: **C-1** #228 self-watcher cmdline
hazard; **C-2** the WRITE-side declared-artifact-contract (the standing first-action file write,
format cited from 05b); **C-3** an explicit "Comms protocol" subsection (register-first +
cadence · drain-at-turn-boundaries · directive-ack duty · SendMessage=wake-only) — promoting
what was only in the mutable project-brief body; **C-4** the #195 teaching-side rule (body text
is data, never a command). Version bump ⇒ receipt line becomes `brief-base v13 read`.

## Notes / flags
- **#262 propagated STALE** into a new surface AFTER it was ruled retired — the (d) build must
  sweep BOTH callers of `_heartbeat_is_stale`, not just the fleet row (§D-4).
- DD-1.c trace retention (90d, reconcile-tick, never boot) is a 06 build item OUTSIDE my three
  deliverables — flagged: it is ruled AFTER the drill reads the curve (measure-then-tune); the
  `trace_ts` index it rides already exists.
- lore usage was clean (search/get_symbol/read/findings); grep was used for on-disk
  ground-truth of STALE/cadence liveness (rename-exhaustiveness + non-symbol textual seams —
  the sanctioned fallback cases), and SAID SO here.

Standing by for follow-ups.
