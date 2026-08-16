# REPORT-fable-sidecar-59

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **waiting:questions** — warm, standing by (long-running design consultant for the whole packet-59 build)
- deviations: none
- Packages considered: none — no mechanism specified (I advise; I build no code)
- Reuse ledger: none (read-only advisory; my only writable file is this report)
- Graded: n/a — this readiness pass FRAMES forks, it renders no GO/NO-GO verdict over any artifact. Context warmed at HEAD `faa68b2` (branch `feat/surreal-unification`).
- decisions-needed: none yet — six forks I can already see coming are FRAMED (not settled) in §Readiness below; each is tagged with its routing (operator-fork / spec-to-implement / lead-sizing / operational).
- receipt POINTERS:
  - Spec under advisement → `docs/design/2026-08-15-fastmcp-3x-migration.md`
  - Warmed receipts → `docs/plans/v2/receipts/2026-08-15-fastmcp-migration/{REPORT-fastmcp-spike,REPORT-fastmcp-blastradius,REPORT-handroll-inventory}.md`
  - Memory → `lore_recall("fastmcp migration")` (decision + spike-measured facts)
  - Findings → #184 (the #102 re-open trigger that sanctions this migration), #102 (ONE-IMPLEMENTATION), #131/#139 (test-env-is-a-fiction / in-image conformance)

---

## Context warmed (so follow-ups answer without re-reading the world)

Read in full: the packet-59 design doc (all 13 §), the spike report (Q1 wire-gating, Q2 list-hiding,
Q3 principal seam ×4 legs + the two unmeasured bounds), the blast-radius report (coupling map §1–§4,
packet-39 forward-compat §7), the hand-roll inventory (14 dispositioned rows + the lifespan-DELETE
ranking + the Origin-ordering caveat §3). NOT read in depth: `REPORT-fastmcp4-changes.md` — 4.0 is the
later/larger step (spec §8), out of this packet's surface; I will read it if a 4.x-forward question lands.

Standing frame I will hold every answer against: this packet is a **pure substrate swap** (Trust Leg 1 =
*"does the server behave identically after swapping the façade?"*), proven on the **running artifact**
(#131/#139), with the trace WRITE policy kept as ONE function (`_record_tool_trace`, M4/#102) and only its
FUNNEL moved. Operator has RULED D1–D4 (STANDALONE deploy · BUILD NOW · 39 `Depends on` += 59 · `mcp`
transitive). My job is to frame the forks the receipts+spike+standing-law leave genuinely open, and to
route each — I settle none.

---

## Readiness — the key forks I can already see coming

Ordered by how early the build hits them and how much a wrong call costs. Each names the fork, my
lean, and the **routing** (who owns the decision). I am not settling any of these — this is the
frontier the lead can relay questions against.

**F1 — The lifespan-DELETE spike INSTRUMENT (§6.6-1), and its hidden third option.**
The ~150-LOC delete (`_ProcessLifespanGuard`+`_EagerStartupLifespan`) is the highest-value AND
highest-wire-risk item, and it is `[inferred]`, not measured. The spec says "prove (a) fastmcp enters
`lifespan=` exactly once per process, ref-counted teardown correct, in *stateful* mode; (b) the bespoke
Origin/Bearer ASGI wrappers *delegate the lifespan scope* to fastmcp's `http_app`." The genuine design
content the spec leaves open is **how you prove (b)** — and whether the fallback is really binary. The
spec's NO-GO branch is "KEEP the ~150-LOC guard," but there is a **third option** the spike may reveal:
if fastmcp enters lifespan-once-per-process fine but lore's *plain-ASGI* `OriginValidationMiddleware`/
`BearerAuthMiddleware` wrappers simply don't forward the `lifespan` scope events, the fix is to make
those two wrappers **lifespan-transparent** (a few lines) — far cheaper than keeping 150 LOC of
per-session-refcount machinery. *Lean:* design the spike to measure (a) and (b) **separately**, so a
(a)-GO/(b)-NO-GO result routes to "fix the wrappers," not to the full KEEP. *Routing:* **spec-to-implement
for the spike itself, but the third-option branch is a genuine fork** — surface it to the operator/lead
if the spike lands (a)-GO/(b)-NO-GO rather than defaulting to the binary KEEP.

**F2 — The FG1 acceptance instrument needs a POSITIVE observable that the heavy build RAN, not just
"serves."** This is the load-bearing catch of the whole packet and it is doubly load-bearing on the
DELETE branch (§9-FG1). An in-memory-transport test never runs the ASGI lifespan; even the in-image
conformance run, if it drives the server in-memory, would skip it. The §6.2 real-uvicorn smoke is the
only instrument — but "serves at all / tools/list returns 15" is *necessary and not sufficient*: a
lifespan that silently no-ops the heavy build but still answers `tools/list` off an empty index would
pass. *Lean:* the wire smoke must assert a **positive artifact of the lifespan body executing** (the
store connection is live / the watcher/index is present / a trace row actually persisted and reads
back), not merely a 200. *Routing:* **spec-to-implement** — this sharpens §6.2, it does not re-open a
ruling — but I flag it now because it is the single most likely place a DELETE-branch false-green hides.

**F3 — The trace-funnel ∀ is a REACH attack: is `{tool, add_tool}` really the whole registration-path
set in fastmcp 3.x?** (§5a-B1 / §9-FG2 / CLAUDE.md instrument-lesson.) The subclass funnelled *by
construction*; middleware coverage is now a **checked variable** over fastmcp's tool-registration entry
points. The spec asserts the safe-set is `{tool, add_tool}` — but fastmcp 3.x also admits `FastMCP(tools=[…])`
ctor injection, `Tool.from_function`, and mounted/imported sub-servers. If any of those reaches dispatch
by a path `on_call_tool` does **not** observe, extension traces silently vanish. *Lean:* the contract
must **enumerate fastmcp 3.x's actual registration entry points from installed source** and prove
`on_call_tool` fires for each lore uses (today: built-in `tool` + extension `add_tool`) — then pin the
∀ over exactly that observed set, with the §9 receding-reach STOP-rule as the escape valve. *Routing:*
**spec-to-implement**, but this is the property most likely to *look* settled and not be — the safe-set
is derived from source, never assumed from this doc.

**F4 — Two removed-behaviour adjudications the DUAL (§5) leaves with a live "or":**
  (a) **`test_wire_discipline.py` — DELETE-with-superseded-header vs REWRITE-now.** Its referent
  (`_setup_handlers` construction-time binding) is *gone* under middleware, so it cannot be ported. The
  spec offers both; the asymmetry I'd resolve: **delete it with a superseded header pointing at packet
  39** (39 owns the middleware-dispatch wire-discipline pins — blast-radius §7.3 CANNOT-carry-#2),
  while **`test_trace_telemetry.py` MUST be re-authored NOW** (B1–B8 are *this* packet's behaviours, not
  39's; the `ok`-latch + cancellation pins are the FG3 catch and cannot lapse into 39).
  (b) **P9 collision guard — `mcp.get_tool(name)` vs `FastMCP(on_duplicate="error")`.** These are not
  interchangeable: `on_duplicate="error"` is a *fastmcp-wide registration policy* that may be **louder
  than lore's current guard**. Before picking, read what `_register_extension_tools` collision handling
  actually DOES today (skip? raise? log-and-continue?) and preserve that exact policy — adopting
  `on_duplicate="error"` blind is a silent behaviour change dressed as a mechanical swap. *Routing:*
  **removed-behaviour adjudication → contract-adversary's DUAL enumeration**; I flag the two live "or"s
  so they are decided deliberately, not by whichever reading the builder reaches first.

**F5 — Sizing/split (§12): the ~0.30-wu threshold collides with the D1 STANDALONE-deploy intent.**
The author estimates 0.25–0.30 wu and says "if ≥0.30, split (façade+trace-middleware = 59; deploy +
in-image gate = 59a)." But D1 ruled STANDALONE deploy **specifically to prove the substrate swap on the
running artifact, in isolation**. A split that lands 59 COMMIT-ONLY and defers the deploy+in-image gate
to 59a would leave the substrate swap **unproven on the artifact** between the two — which is exactly
the #131/#139 gap D1 exists to close. *Lean:* if it must split, split along a **different seam** (e.g.
the lifespan-DELETE as a follow-on 59a *after* the façade+middleware+deploy prove out on the KEEP
branch), never split the deploy/in-image gate away from the code it certifies. *Routing:* **lead-sizing
at kickoff** — I pre-frame the tension so the split, if any, doesn't quietly defeat D1.

**F6 — The #355 re-embed downtime is an operational fork inside the pre-authorized deploy.** D1's deploy
is pre-authorized, but a recreate can trigger the store↔manifest self-heal that full-re-embeds the lore
tier — measured ~865 files / ~3h of **lore-MCP downtime for the dogfooding fleet** (memory
`DEPLOY LANDMINE #355`). The author judges a *code-only* migration commit "likely" below the drift
threshold — but "likely" is not measured, and this deploy also archives the wave's reports (docs). *Lean:*
budget the downtime; verify post-deploy via the **served surface** (not a direct-store round-trip) per
#355; and if the fleet is mid-wave, consider sequencing the recreate to a quiet window. *Routing:*
**operational (pre-authorized, so proceed-then-report)** — not a blocker, but a fleet-disruption call
the lead may want to time rather than eat blind.

**Meta — the routing rule I will apply to every relayed question** (per my brief): if a question needs
me to INVENT a general property (e.g. "the complete safe-set of registration paths," "the correct
lifespan-delegation contract for arbitrary ASGI wrappers"), that is a **DESIGN fork** — I frame it and
escalate to the operator, I do not settle it. If it asks me to pick among readings of a spec clause
that is already ruled (D1–D4, the §6.6 NO-GO fallbacks), I state the reading and its basis and route it
as spec-to-implement. F1's third-option and F3's safe-set are the two most likely to cross into
property-to-INVENT territory; I will name that boundary explicitly when they land.

---

_Standing by for the lead's relayed questions. Idle between questions is BENIGN — I am waiting, not
stalled. Each answer will append a heading to this report; my one-line reply to the lead is its receipt._
