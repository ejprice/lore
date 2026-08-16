# REPORT-fable-sidecar-59b

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **waiting:questions** — re-warmed, standing by. Long-running design consultant for the whole
  packet-59 fastmcp-3.x migration build; re-spawn of the stopped `fable-sidecar-59` (whose 6 forks I
  inherit + update below).
- deviations:
  - (tool-honesty, brief-base §4) env `CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8` + `CLAUDE_CODE_CHILD_SESSION=1`
    → this process appears to run on **Opus 4.8**, while my brief says "Model: Fable". I registered
    `model=fable` per the brief. Does NOT affect advisory quality; flagged so the lead knows which model
    is actually framing these forks.
- Packages considered: none — no mechanism specified (I advise; I build no code).
- Reuse ledger: none (read-only advisory; my only writable file is this report).
- Graded: n/a — a readiness/framing pass; renders no GO/NO-GO over any artifact. Context warmed
  2026-08-15 at HEAD `ee4bced` (branch `feat/surreal-unification`).
- decisions-needed: none are MINE to settle. Post-spike-59, two prior forks are SETTLED (F1
  lifespan-DELETE = GO; F6 Origin-*ordering* = fastmcp guard runs outermost). The still-LIVE design
  forks: **(a) Origin defense-in-depth keep-vs-drop** (new, unlocked by the ordering result),
  **(b) P9 collision policy** (`get_tool` vs `on_duplicate="error"`), **(c) `test_wire_discipline.py`
  delete-vs-rewrite**, **(d) sizing/split** — all FRAMED in §Forks, none settled.
- receipt POINTERS:
  - Spec under advisement → `docs/design/2026-08-15-fastmcp-3x-migration.md` (all 13 §, esp. §5a/§5b/§5/§6.6/§7/§9/§11/§12)
  - Prior sidecar (forks F1–F6, superseded-updated here) → `REPORT-fable-sidecar-59.md` (repo root, pending archive)
  - Warmed receipts → `docs/plans/v2/receipts/2026-08-15-fastmcp-migration/{REPORT-fastmcp-spike,REPORT-handroll-inventory,REPORT-migration-author}.md`; spike-59 result via lead brief (`REPORT-spike-59.md`, not yet read directly — will read on a detailed F1 question)
  - Memory → `lore_recall("fastmcp migration")` (decision + spike-measured facts + #184 resolution)
  - Findings → #184 (re-open trigger (b) fired → sanctions this migration), #102 (ONE-IMPLEMENTATION), #131/#139 (test-env-is-a-fiction / in-image conformance)

---

## Re-warmed — what I read, and the DELTA since REPORT-fable-sidecar-59

Read in full this session: brief-base v14, project brief v7, the packet-59 spec (all 13 §), the prior
sidecar report (F1–F6 + Meta), the DECISION + spike-measured memories, `REPORT-fastmcp-spike.md`
(Q1 wire-gating / Q2 list-hiding / Q3 principal seam ×4 legs + the two unmeasured bounds), and
`REPORT-handroll-inventory.md` (14 dispositioned rows, the ~150-LOC lifespan-DELETE ranked #1,
the §3 Origin-ordering caveat). NOT re-read in depth: `REPORT-fastmcp-blastradius.md` and
`REPORT-fastmcp4-changes.md` (4.0 is the later/larger step, spec §8) — I pull them if a
blast-radius or 4.x-forward question lands.

**Two things moved since the prior sidecar wrote F1–F6, and they reshape the frontier:**

1. **The §6.6 SPIKE IS DONE + lead-verified — all 3 `[inferred]` items GO** (`REPORT-spike-59.md`,
   harness `scripts/fastmcp_migration_spike.py`; per my spawn brief, not yet read line-by-line):
   - (1) fastmcp enters `lifespan=` **once per process** → the ~150-LOC delete
     (`_ProcessLifespanGuard` + `_EagerStartupLifespan` + `_lore_eager_guard`) is GREEN. **This
     retires prior F1** (incl. its "third option" — no wrapper-transparency fallback is needed).
   - (2) `host_origin_protection` runs **BEFORE** the `TokenVerifier` (R9 ordering is fastmcp-native)
     → the bespoke Origin layer is **NOT required outermost for ordering**. **This retires the
     *ordering* half of prior F6.**
   - (3) a spoofed `Host` header → **421** with `host_origin_protection` on → the today-open
     Host/DNS-rebinding gap (C3′) closes as a banked BENEFIT.
   - ⚠ **BUILD-RIDER carried from the spike:** `host_origin_protection` defaults **OFF**, and once on
     it is strict — the build MUST set `allowed_hosts` (+ `allowed_origins`) for the **nginx-ingress**
     fronting prod, or prod serves **421** on every request. This is a config-completeness pin, not a
     code pin — easy to green-at-gate on the dev host (loopback allowed) and 421 in the image. It
     belongs in the §6.2 wire smoke AND the §6.1 in-image auth suite with a NON-loopback Host.

2. **`contract-59` §0 re-verify surfaced a coupling site the design P-table OMITTED:**
   `Context[Any, AppContext, Any]` is **NOT subscriptable** in fastmcp 3.x → ~16 `Context[...]`
   annotation sites collapse to bare `Context`. Mechanical, spec-to-implement — but it is a real
   removed-behaviour item (a typing surface) the §3/§12 P-table did not enumerate (§12 P14 mentions
   `Context` *injection* staying annotation-based, not the *subscripting* loss). Flagged so the DUAL
   inventory carries it rather than the builder discovering it as a mypy break.

---

## Forks — the live frontier (prior F1–F6 updated for the spike-59 result)

Ordered by how early the build hits them / cost of a wrong call. My lean + routing; I settle none.

**LF-A (NEW, unlocked by spike-59) — Origin layer: keep bespoke for DEFENSE-IN-DEPTH, or drop it?**
Spike-59 proved fastmcp's `host_origin_protection` runs outermost and rejects spoofed Host (421), so
the bespoke `OriginValidationMiddleware` is no longer *required* for the packet-39 R9 "reject before
credential parse" ordering. The genuine remaining question is a **design trade, not a fact**: is
keeping the bespoke Origin layer as a second, independent check worth its maintenance cost now that
the framework covers the property? *Two readings that produce different code:* **(i) DROP** — one
Origin authority (fastmcp), fewer LOC, no divergence risk; the bespoke layer's distinctive behaviours
(absent-Origin allowed, loopback allow, fail-closed-on-bad-IPv6) must be reproduced by
`allowed_origins`/`allowed_hosts` config or adjudicated as DROP with a reason. **(ii) KEEP** —
defense-in-depth: two independent Origin gates, but now you own reconciling their allow-lists (a
config that passes one and fails the other is a new silent-inconsistency surface). *Lean:* **DROP**,
BUT only after the DUAL inventory adjudicates each bespoke-Origin behaviour (absent-Origin,
loopback, bad-IPv6 fail-closed) item-by-item — "the old code allowed absent-Origin" is a behaviour
that must be preserved-with-pin or dropped-deliberately, never silently lost to a framework default.
*Routing:* **removed-behaviour adjudication → contract-adversary DUAL**; if the operator values
defense-in-depth as policy, that's an operator fork — I frame it, I don't rule it.

**LF-B (was F4b) — P9 collision policy: `await mcp.get_tool(name) is not None` vs `FastMCP(on_duplicate="error")`.**
Not interchangeable. `_tool_manager` is GONE in 3.x (renamed `_local_provider`) → the current guard
HARD-BREAKS loudly (good). But `on_duplicate="error"` is a *fastmcp-wide registration policy* that may
be **louder than lore's current guard**. *The trigger:* before picking, the build reads what
`_register_extension_tools`'s collision handling DOES today (skip / raise / log-and-continue) and
preserves that exact policy. Adopting `on_duplicate="error"` blind is a silent behaviour change dressed
as a mechanical swap. *Lean:* prefer the **public `get_tool` probe** (it re-expresses the *existing*
guard 1:1) unless the today-policy is already "raise on duplicate", in which case `on_duplicate="error"`
is the DRYer match. *Routing:* **spec-to-implement, gated on reading today's policy** — a genuine fork
only if today's policy and `on_duplicate="error"` disagree.

**LF-C (was F4a) — `test_wire_discipline.py`: DELETE-with-superseded-header vs REWRITE-now.**
Its referent (`_setup_handlers` construction-time binding) is GONE under middleware; it cannot be
ported. *Lean (asymmetric, unchanged):* **DELETE it with a superseded-header pointing at packet 39**
(39 owns the middleware-dispatch wire-discipline pins — blast-radius §7.3 CANNOT-carry-#2), WHILE
**`test_trace_telemetry.py` is re-authored NOW** (B1–B8 are *this* packet's behaviours; the `ok`-latch
+ cancellation pins are the FG3 catch and cannot lapse into 39). *Routing:* **removed-behaviour
adjudication → contract-adversary DUAL** — flagged so it's decided deliberately, not by first reading.

**LF-D (was F3) — the trace-funnel ∀ is a REACH attack: is `{tool, add_tool}` the WHOLE
registration-path set in fastmcp 3.x?** The subclass funnelled *by construction*; middleware coverage
is now a **checked variable** (CLAUDE.md instrument-lesson). The spec asserts the safe-set is
`{tool, add_tool}`, but 3.x also admits `FastMCP(tools=[…])` ctor injection, `Tool.from_function`, and
mounted/imported sub-servers. *Lean:* the contract **enumerates 3.x's actual registration entry points
from installed source** and proves `on_call_tool` fires for each path lore uses (today: built-in
`tool` + extension `add_tool`), pinning the ∀ over exactly that observed set, with the §9 receding-reach
STOP-rule as the escape valve. *Routing:* **spec-to-implement** — but the property most likely to LOOK
settled and not be; the safe-set is derived from source, never assumed from the doc. §9's FG2 (trace a
built-in AND an extension tool on the wire) is the discriminating instrument.

**LF-E (was F2) — FG1 needs a POSITIVE observable that the heavy build RAN, not just "serves".**
Doubly load-bearing on the DELETE branch: an in-memory transport never runs the ASGI lifespan, and even
the in-image conformance run skips it if it drives the server in-memory. "serves / tools/list returns
15" is *necessary, not sufficient* — a lifespan that silently no-ops the heavy build but answers
`tools/list` off an empty index passes. *Lean:* the §6.2 real-uvicorn wire smoke must assert a
**positive artifact of the lifespan body executing** (store connection live / watcher+index present /
a trace row persisted and read back), not merely a 200. *Routing:* **spec-to-implement** (sharpens
§6.2) — the single most likely place a DELETE-branch false-green hides now that the guard is deleted.

**LF-F (was F5) — sizing/split (§12) must not defeat D1.** Author estimates 0.25–0.30 wu; if ≥0.30 the
sizing law says split. But D1 ruled STANDALONE deploy *specifically to prove the substrate swap on the
running artifact in isolation* (#131/#139). A split that lands 59 commit-only and defers deploy+in-image
gate to 59a leaves the swap **unproven on the artifact** between the two — the exact gap D1 closes.
*Lean:* if it must split, split along a **different seam** (e.g. lifespan-DELETE as a follow-on 59a
*after* façade+middleware+deploy prove out), NEVER split the deploy/in-image gate from the code it
certifies. *Routing:* **lead-sizing at kickoff** — pre-framed so a split can't quietly defeat D1.

**LF-G (was F6, ops half) — #355 re-embed downtime inside the pre-authorized deploy.** D1's deploy is
pre-authorized, but a recreate can trigger the store↔manifest self-heal that full-re-embeds the lore
tier — ~865 files / ~3h of lore-MCP downtime for the dogfooding fleet (memory `DEPLOY LANDMINE #355`).
Author judges a *code-only* migration commit "likely" below the drift threshold, but "likely" ≠
measured, and this deploy also archives the wave's reports (docs). *Lean:* budget the downtime; verify
post-deploy via the **served surface** (not a direct-store round-trip) per #355; sequence the recreate
to a quiet fleet window if mid-wave. *Routing:* **operational (pre-authorized → proceed-then-report)** —
a timing call, not a blocker.

**LF-H (NEW) — the `Context[...]`→`Context` de-subscripting (contract-59 §0).** ~16 sites, mechanical,
but a removed-behaviour surface the P-table omitted. *Lean:* fold it into the DUAL inventory as a
DROP-the-parameterization item (the injection contract is unchanged; only the *typing* narrows), and
confirm 3.x injection is still **annotation-based** (not `Depends()`-based as in 4.0 — spec §12 P14).
*Routing:* **spec-to-implement**, no fork — flagged for inventory completeness so it isn't a surprise
mypy break mid-build.

**Meta — my routing rule (per brief):** a question that needs me to INVENT a general property (the
complete safe-set of registration paths; the correct lifespan-delegation contract for arbitrary ASGI
wrappers) is a **DESIGN fork** → I frame it and escalate to the operator, I do not settle it. A question
that picks among readings of an already-ruled clause (D1–D4, the now-GO §6.6 gates) → I state the
reading + basis and route it spec-to-implement. LF-A and LF-D are the two nearest the invent/implement
boundary; I name that boundary explicitly when either lands.

---

---

## Q1 (2026-08-15) — contract-59's three design forks: framing + recommendation

Grounded on: `REPORT-contract-59.md` (read in full), the live collision guard
`server.py::_register_extension_tools` + its docstring (read at HEAD `ee4bced`), the §6.6 spike-59
GO result, and the handroll inventory §3. The lead's frame holds: **the contract pins the OUTCOMES
either way, so none of these is a correctness fork** — each is a code-shape / policy call, which
lowers the stakes and means the answer should be right-sized, not over-built.

### FORK 1 — LF-A Origin defense-in-depth: keep BOTH bespoke-Origin + fastmcp, or DEDUP?

**This is NOT primarily a defense-in-depth question — it is a behaviour-preservation MEASUREMENT that
most likely COLLAPSES the fork.** Reframe it that way before it reaches the operator, because the
"two independent Origin checks for depth" reading obscures the actual decisive variable.

The bespoke `OriginValidationMiddleware` has THREE distinctive ACCEPT behaviours (handroll inventory
§1 row 3, verified): **absent-Origin allowed · loopback allowed · fail-closed on bad IPv6.** fastmcp's
`host_origin_protection` covers a strict SUPERSET of the *threat* surface (Host + Origin +
DNS-rebinding vs the bespoke layer's Origin-only). So the two are NOT peers catching the same class
independently — fastmcp dominates on coverage; the only thing the bespoke layer has that fastmcp may
not is those three ACCEPT semantics.

The decisive unknown, which must be MEASURED against installed fastmcp 3.x source/behaviour (the #107
read-then-verify law — never assumed): **does `host_origin_protection`, configured, reproduce
absent-Origin-allowed, loopback-allowed, and bad-IPv6-fail-closed?** The riskiest of the three is
**absent-Origin**: browser-oriented Origin protections frequently REQUIRE an Origin header, but most
MCP clients — including the dogfooding fleet connecting over streamable-HTTP — send NONE. The contract
PINS "absent-Origin allowed" as an outcome (§5 C3), so:

- **If fastmcp REJECTS absent-Origin (or can't be configured to allow it):** the fork COLLAPSES — the
  bespoke Origin layer is **KEPT for that property**, forced, not chosen (exactly the design's own
  §6.6 Origin-ordering caveat pattern: "keep bespoke for the one property fastmcp doesn't give"). No
  operator ruling needed; dropping it would 403 every no-Origin fleet request. fastmcp then owns only
  Host/DNS-rebinding (C3′).
- **If fastmcp reproduces all three accept behaviours** via `allowed_origins`/config: THEN it is a
  genuine dedup-vs-depth **policy** call → operator / packet-39 owns it. **My lean: DROP the bespoke
  Origin layer.** Rationale — fastmcp is a strict superset on threat coverage, so a second Origin-only
  check adds little marginal security; meanwhile keeping two separately-maintained Origin allow-lists
  is a silent-inconsistency surface (a config that passes one and fails the other), which is the
  ONE-IMPLEMENTATION concern applied to the *"what Origin is allowed"* policy. Packet 39's R9 "reject
  before credential parse / zero outbound Google call" property is already satisfied by fastmcp running
  outermost (spike-59 Item-2 GO), so DROP does not regress R9.

**Routing:** genuine operator/packet-39 ruling ONLY in the equivalent-behaviours branch; forced (no
ruling) in the behaviour-gap branch. So **put it to the operator WITH the measurement attached**, not
as an abstract "defense-in-depth y/n" — the measurement likely removes the choice. Whichever way, the
bespoke Origin behaviours (absent/loopback/bad-IPv6) each get an item-by-item DUAL adjudication
(preserved-with-pin or dropped-deliberately — never silently lost to a framework default). Low stakes
(outcomes pinned) → the build measures fastmcp's Origin semantics as a normal step and reports; don't
spin machinery on it.

### FORK 2 — P9 collision policy. **CONCUR with contract-59, + ONE reach-robust nuance.**

contract-59 is correct and now fully grounded in the live code: `_register_extension_tools` **raises
`ValueError`** (fail-closed) when `spec.name in _ALL_BUILTIN_TOOL_NAMES` (the DECLARED UNIVERSE —
INCLUDING built-ins this deploy's `tools:` allowlist DISABLED) OR the name is already registered. Its
own docstring records WHY `on_duplicate`/`add_tool` is insufficient: their default is **warn-and-keep
the first registration — a SILENT shadow**, and they only see the REGISTERED set, so they cannot
reserve a DISABLED built-in's name (packet-45 L2-4). So `on_duplicate="error"` ALONE fails the
disabled-name leg — CONCUR, keep the universe check + a public/sync registered-names path.

Two nuances to ADD (invited):

1. **Preserve the RESPONSE, not just the detection.** Today it RAISES `ValueError` *before* `add_tool`,
   with a specific message. The public/sync replacement must reproduce **raise-before-register**
   (fail-closed), not skip/warn. The contract pins both legs as outcomes — good — but the build note
   is: the sync path is a locally-accumulated `registered_names` set (seed with
   `_ALL_BUILTIN_TOOL_NAMES`, add each extension name after it registers, membership-check before),
   because `_register_extension_tools` is SYNC and fastmcp's `get_tool` is ASYNC (contract coupling
   #4). That keeps the reservation predicate ONE expression — universe ∪ already-registered — matching
   the current two-clause check 1:1.

2. **ALSO set `FastMCP(on_duplicate="error")` as a reach-robust BACKSTOP (not a replacement).** This is
   the CLAUDE.md instrument-lesson applied: lore's guard only runs INSIDE `_register_extension_tools`
   — it certifies only that one registration path. `on_duplicate="error"` is a RUNTIME guard the
   framework enforces over **every** registration path (built-in decorators, any future path), turning
   fastmcp's silent warn-and-keep default into a loud failure. It cannot reserve disabled-built-in
   names (only lore's universe check can), so the two are complementary: lore's universe check adds
   what the framework can't know; `on_duplicate="error"` adds coverage over paths lore's check doesn't
   run on. Cost: one ctor kwarg. **Caveat before adopting:** the build must confirm lore never
   LEGITIMATELY registers the same name twice (it doesn't by design — but verify, per LF-B's
   read-today's-policy gate); if a legitimate re-registration exists, drop this nuance. Mark it
   OPTIONAL — contract-59's core rec stands with or without it.

### FORK 3 — `test_wire_discipline.py` fate. **CONCUR: delete-with-superseded-header (tombstone).**

The premise (`_setup_handlers` construction-time binding → dead-on-wire) genuinely dissolves under
middleware — there is no referent to port — and an immediate rewrite is premature because 39's posture
modules don't exist yet (rewriting now = pinning against an unbuilt design = building twice). CONCUR.

**The DUAL check that makes the delete SAFE (and the one thing to state in the tombstone):** the
general property `test_wire_discipline.py` existed to protect — *"post-construction registration is
LIVE on the wire, not dead"* — is **PRESERVED by THIS packet**, re-expressed: §6.2/FG2 traces a
built-in AND an `add_tool` extension tool over REAL uvicorn (a positive wire-liveness assertion),
and D7 pins the middleware is actually installed. So the tombstone does NOT leave the wire-liveness
virtue unguarded in the gap between 59 and 39 — it survives in a different instrument. That is the
"old world's virtue survived the rewrite" leg of the DUAL, and it PASSES. The superseded-header should
say: premise dissolved (`_setup_handlers` binding gone under middleware) · wire-liveness re-expressed
by FG2/D7 in THIS packet · the *scoped/per-principal* wire discipline handed to packet 39's posture
modules. contract-59 already retains the right anti-regression pin (`TracingFastMCP` stays retired) +
a hand-off placeholder — that is the correct residual. No change needed; just ensure the header
carries those three clauses so a future reader meets the bound deliberately.

**Routing summary:** F2 + F3 are **spec-to-implement, CONCUR** (F2 with an optional backstop nuance).
F1 is a **measurement that likely collapses the fork**; its residual (equivalent-behaviours branch) is
a genuine **operator/packet-39 policy ruling** — put it to the operator WITH the fastmcp Origin-accept
measurement attached, not before.

---

---

## Q2 (2026-08-15) — adversary FINDING ①-OC (FP-07 re-home: named helper vs inline). **Lean: (a) ACCEPT.**

Grounded on: the lead's transcription of `REPORT-adversary-59b.md §①-OC` + a live verify —
`_acquire_eager_lease_with_retry` exists TODAY as an async **method** on `_EagerStartupLifespan`
(`server.py:12434`, the class the migration DELETES). Routing: this IS a property-to-invent-baked-into-
a-pin fork → operator ruling; I frame + lean, I settle nothing.

**The reframe that decides it: this pin is NOT inventing a structure — it is PRESERVING one that
exists today, across a forced re-home.** FP-07 bounded-retry is already a NAMED, runnable unit
(`_EagerStartupLifespan._acquire_eager_lease_with_retry`). The migration deletes its host class, so
the retry MUST move somewhere; the pin requires it move to a NAMED module-level helper
(`_eager_build_with_retry`) rather than dissolve into the `lifespan=` closure. So the "correct-inline
build" the adversary measured is not a fully-correct build by repo standards — it is a build that has
**regressed** an existing named-runnable-unit into an anonymous closure. Under the DUAL, "the retry is
a named runnable unit" is an existing property, and preserving it with a pin is the DEFAULT, not an
over-reach. The over-constraint framing is technically accurate (the pins can't distinguish
correct-inline from wrong-single-shot) but its resolution is: we do not WANT to permit inline, because
inline sacrifices the runnable proof.

**Why the named unit is load-bearing, not shape-for-shape's-sake:** it is the only runnable target for
the **routing-is-not-sharing mutation proof on the shared `backoff`** (CLAUDE.md ONE-IMPLEMENTATION /
prove-sharing-by-MUTATION / the reach-attack "coverage is a CHECKED variable" lesson). Mutate the
shared backoff constant → the named-unit pin must redden. Inline the loop into the closure and that
mutation proof degrades to the §6.2 wire SKIP — losing FP-07's backoff as a checked variable exactly
when the DELETE branch makes the lifespan the serving hot path. That is adversary-59's original ① gap,
re-opened.

**Why (b) is a false economy WITHIN THIS CONTRACT:** (b)'s structure-agnostic pin is nominally more
"behavioural," but it is not a better instrument here — it needs the coupling-#3 heavy-build stub seam
the contract DISCLAIMS, so within the contract as-written it degrades to the §6.2 real-uvicorn SKIP
(build-provided fixture). A behavioural pin that is a skip is not more behavioural than a runnable
structural pin; it is *less tested*. So (b) trades a runnable unit-level checked variable for a
placeholder, and re-opens ①. The purity principle (pin behaviour, not structure) is real repo law, but
it presumes the behavioural pin is RUNNABLE; here it is not.

**The honesty note the operator should rule consciously (the C-DEF smell):** (a) does mean a
behaviourally-correct inline build fails 3 of 4 retry pins — a correct-build-goes-RED signature. The
acceptance is legitimate ONLY because the pin encodes a real repo INVARIANT (shared retry policy must
be mutation-provable ⇒ must have a named target) AND that structure already exists today, so the pin
forbids a regression rather than demanding an invention. The contract's explicit **"inline →
escalate"** note is the correct PIN-THE-MISS treatment: a future builder who wants to inline meets the
bound deliberately, with its rationale attached, and can re-open. Compliance cost is ~one
extract-method the code already reflects.

**One named re-open trigger (measure-then-tune, not a reason to relax now):** coupling #3 obliges the
build to supply a NEW stub-the-lifespan hook anyway (`stub_heavy_startup` reaches the deleted guard).
IF that hook turns out to let the retry be driven under fault at UNIT level, then (b)'s
structure-agnostic pin becomes RUNNABLE (not a skip) and regains its appeal — at which point relaxing
to a behavioural pin over the named-or-inline unit would be strictly better. That is a build-time
re-open trigger to revisit ①-OC, NOT a reason to relax the ruling now (the seam is disclaimed today,
so today (b) = skip).

**Net recommendation to the operator:** **ACCEPT (a)** — concur with the adversary. It preserves an
existing named-runnable-unit + its backoff mutation proof, costs a trivial already-satisfied
extract-method, is honestly disclosed as an "inline → escalate" bound, and keeps the contract
SUFFICIENT → straight to build. (b) is a false economy under this contract (degrades to a skip,
re-opens ①); revisit only if the coupling-#3 hook later makes a runnable behavioural pin free.

---

_Standing by for the lead's next relayed question. Idle between questions is BENIGN — I am waiting, not
stalled; my idle-gate contract declares `{"artifact": null}`. Each answer appends a heading here; my
one-line reply to the lead is its receipt._
