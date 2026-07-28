# 04b model-consumer audit — sidecar verdicts on the ruled design (2026-07-28)

**Author:** `design-sidecar-04b` (Fable), operator-granted overrule authority (*"It may
overrule operator rulings"* — spawn brief, 2026-07-28). **Scope of every claim:** branch
`feat/surreal-unification` at `2b8aa01`, measured 2026-07-28 unless dated otherwise. No
production code exists for 04b-1 yet; every verdict lands before a builder starts, which is
the point — a contract-shape change here costs one edit; after GREEN it costs a wave.

**Evaluative frame** (operator, verbatim): *"Remember models are the consumer of lore.
Models must be happy with lore's function."* Governing law: repo `CLAUDE.md` THE CONSUMER
LAW + THE TRUST DOCTRINE; `docs/plans/v2/DESIGN-LAW.md` §1 (esp. §1.3 caveats-with-verdicts,
§1.4 misses-teach-a-decision-tree, §1.7 the trust ruling). Sharpening from project memory
(`lore_recall("trust doctrine")`, three blind informants 2026-07-25): **trust loss is
categorical, not proportional** — one ground-truthed confident-wrong kills the verdict
class outright, for every correct instance after it.

---

## §0 — Method, evidence, and what was re-derived

**Read set:** `docs/plans/v2/04-comms-blocks-footer.md` in full (incl. §04b SPLIT: R1–R7,
L1–L3, E-1–E-5); `comms-subsystem.md`; DESIGN-LAW §0/§1/§8; the four wave reports
(scout-04b-seams · contract-04b1 · contract-04b1-253 · adversary-04b1, at the repo root at
`2b8aa01`, archiving per CLAUDE.md to `docs/plans/v2/receipts/`); the served surfaces
themselves (below).

**Numbers re-derived rather than inherited (per repo law):**
- The three dispatchers' return counts: **8 (`AppContext.findings`) + 1 (`claim_task`) +
  6 (`tasks`) = 15**, re-derived by AST walk 2026-07-28 at `2b8aa01`. Confirms the scout;
  the packet's original "~17" stays wrong.
- `lore_comms`' identity contract, read from the live registration (`server.py`, the
  `name="lore_comms"` block): `agent` REQUIRED for every action; `session` REQUIRED for
  `register`, optional otherwise ("omit when your name is unique").
- The register render (`AppContext._render_comms_register`): head + brief + fenced body +
  **`"echo in your report: brief project v{version} read"`** — the render already installs
  a per-session habit line. This precedent is load-bearing for Q1.
- `_INSTRUCTIONS` (`server.py::_INSTRUCTIONS`, ~line 1461 at `2b8aa01`): the MEMORY
  paragraph names `lore_tasks`/`lore_findings`/`lore_claim_task` and teaches comms
  register/drain — nothing teaches any identity parameter on the three ledger tools
  (correct today; the parameter does not exist yet).

**Live consumer receipts (my own calls, 2026-07-28, via the served MCP tools — the raw
store was never touched):**
1. `lore_tasks action=query` (no filters) served the **entire ledger — ~110 rows** — for a
   question needing 5. #253's unbounded read, experienced as a consumer. **MEASURED.**
2. `lore_tasks action=query limit=30` was **REFUSED** with a teaching error: *"'since'/'limit'
   apply only to action='rollup' — omit them for 'query'"*. So at HEAD the served `query`
   has **no caller-visible bound at all** — which gives ruling R5 a schema implication
   nobody has stated (→ §5.2). **MEASURED.**
3. `lore_comms action=fleet` from an unregistered identity refused and NAMED the
   non-retired registry — in which **`smoke-charlie` appears twice** (same name, two
   sessions). Cross-session name ambiguity is real in this store, not hypothetical.
   **MEASURED.**
4. The query render served task `7b701f0ecd734bb0bff4073ecb0c405f` with
   `owner smoke - [#99 open] forged finding entry (kind friction, by attacker)` — a stored
   hostile owner value (the #99 security probe's seed) rendered inline in a served row.
   Caller free-text identities demonstrably reach serves as same-line text. **MEASURED**
   (⚠ the original "un-shaped/raw" framing here is retired — see §5.3's correction).

**Consults commissioned** (operator sanction: *"When in doubt, consult Sonnet 5, Opus 5,
and Fable 5"*): four independent subagent consults — Sonnet and Opus, one prompt per
question set, identical prompts per model, no repo access, run blind to the rulings and to
each other. I am the Fable leg. Subagent transcripts are `/tmp`-ephemeral, so the
load-bearing lines are quoted **in this doc**, which is their durable address. Diff, not
merge, per the brief — the diffs are in each section and collected in §6.

---

## §1 — Q1: the footer's caller identity (ruling R1)

**Ruling under audit:** optional `agent`/`session` on the three ledger tools, resolved
through the registry; *"agent omitted ⇒ NO footer — honest silence, never a guess."*
Rejected: heuristic resolution of `owner`/`actor`/`created_by`; a fleet-wide line.

### 1.1 What is right and stays

- **The transport premise is correct and unfixable elsewhere** (INFERRED from architecture,
  corroborated by `lore_comms`' own shape): every fleet agent shares one MCP connection;
  the server has no per-caller channel identity. Only the call payload can carry identity —
  which is exactly why `lore_comms` requires `agent=` on every action. R1's family of
  shapes is the only buildable family.
- **Never serve a guessed identity as "you"** — correct, and the consult evidence supports
  the underlying hazard (§1.3).
- **`agent` required would be wrong**: it breaks every existing caller of a tool R3 itself
  notes is *"in active fleet use"* (the no-consumers grant does not cover `lore_tasks`),
  and it couples the task ledger to comms registration for solo/non-fleet use.

### 1.2 The measured answer to "what does a Sonnet 5 agent actually do?"

Both models were given the ruled surface with the parameter description varied
(V1: payoff-stating — "…append a one-line nudge if traffic is pending for you… Omitted: no
traffic check"; V2: terse — "caller agent identity, resolved against the fleet registry"):

| probe | Sonnet | Opus |
|---|---|---|
| V1: passes `agent=`? | **yes** ("a stated free benefit… the name is already in context") | **yes, with decay risk** ("the load-bearing clause is the last three words: *Omitted: no traffic check*") |
| V2: passes `agent=`? | **no** ("I wouldn't think about it… no stated consequence") | **no** ("visibly redundant with `actor`… teaches me the field is surplus — a legacy alias") |
| after the footer fires once | habit installs, session-bounded, does not survive respawn | "the strongest signal in the whole system — response evidence beats schema prose"; erodes on compaction and on **unreinforced silence** ("twenty calls, no footer → dead tokens, I quietly drop it") |
| silent no-footer on a typo'd `agent=` | "a trust hazard by construction… I stop trusting the passive nudge and revert to polling" | "I conclude no-traffic, carry on mistyped indefinitely… and when I later find unread directives **I blame the mechanism**, not my typo, and route around the feature forever" |

**So R1's fate rides on a `Field(description=…)` string that no ruling specifies.** With a
V2-grade description — which is what an unbriefed builder writes — the parameter is passed
by nobody, the footer never fires, and *"honest silence"* is indistinguishable from
*"feature does not exist."* The lead's DOA suspicion is confirmed, measured, unanimous.

### 1.3 VERDICT

**CONCUR on R1's mechanism (optional `agent`/`session`, registry-resolved, never a guessed
"you"). OVERRULE on two clauses; two riders bind the rest.** In rank order of importance:

**OVERRULE-1 — supplied-but-unresolvable is NOT "omitted". It teaches, loudly, always.**
R1 rules the omitted case only. If the builder maps unknown/ambiguous `agent=` onto the
same silence, one typo silently kills the feature per-agent forever — and both consults
independently identified this exact silence as the moment they stop trusting the mechanism
(the categorical trust loss, not a discount). Replacement rule: `agent=` **supplied** but
unresolvable appends one loud line and NEVER fails the write —
`agent 'builder-xl' is not registered — traffic not checked; register via lore_comms
action=register` (ambiguous: `…matches N sessions — traffic not checked; pass session=`).
The existing unknown-agent teaching vocabulary (which already names registry members —
measured, §0.3) is the shared policy to route through; no new mechanism. *Pin it*: negative
fixture (typo'd `agent=` → teach line present, write still succeeds) + positive control +
the ambiguity leg (real: `smoke-charlie` ×2 measured in the production registry). An
explicit opt-in whose failure mode is indistinguishable from its no-op success is a trust
defect by construction — Opus: *"an identity that fails to resolve is never a normal
condition; it should never share a rendering with one."*

**OVERRULE-2 — the rejected-alternatives clause is overbroad: strict resolution of the
verb's REQUIRED identity field is reinstated as the fallback tier.** What R1 rightly
rejected is serving a **guess** as **"you"**. Exact-unique-match resolution served in the
**third person** is neither: `owner` (claim), `actor` (transition), `created_by`
(create/report) are already REQUIRED, already carry the registered name under the fleet
protocol, and an exact match against the registry is not a guess — on match the footer
reads `traffic pends for builder-x1: 2 unacked directives`, a TRUE sentence about a NAMED
agent whoever the caller is; no match or ambiguous ⇒ silence (normal for this tier — a
non-fleet `actor` like `operator` must not draw noise). Both consults, blind, ranked this
design **above** the ruled one — Opus: *"it removes the compliance problem instead of
trying to solve it… rides for free on a habit that cannot decay, survives compaction, and
needs nothing in the brief"*; and endorsed the grammar: *"third person is better… it names
the identity that resolved, so a wrong-but-resolving name is visible to me on sight, where
'you have 2 messages' would hide it."* Precedence: explicit `agent=` wins; fallback fires
only when `agent=` is absent; `session=` remains the explicit disambiguator (the fallback
tier has none, deliberately — ambiguity ⇒ silence).
  Two conditions, from the consults' own hazard analysis, are PART of this overrule:
  - **(a) Disclose the coupling where the field is described** (both consults, unprompted):
    one clause on `owner`/`actor`/`created_by` — *"also matched against the fleet registry;
    when it names a registered agent, mutating calls may append that agent's
    pending-traffic note."* Behaviour a description doesn't mention is behaviour an agent
    is eventually surprised by, and surprise is what kills the surface (Opus, verbatim).
  - **(b) The fallback footer carries NO imperative drain command.** Opus's on-behalf
    hazard, which nobody had seen: a lead transitioning for a builder receives
    `…— lore_comms action=drain agent=builder-x1` and *"may well drain builder-x1's inbox,
    stealing its messages"* (drain STAMPS seen). Grammar: **explicit `agent=` ⇒
    second-person actionable footer with the drain verb** (the caller asserted the
    identity); **fallback-resolved ⇒ third-person informational footer, no imperative**
    (`traffic pends for builder-x1: 2 unacked directives` — full stop). This one sentence
    of grammar closes the stolen-drain door without a mechanism.
  Cost, stated: one bounded registry read per mutating call when `agent=` is absent and the
  field value matches the identity charset (skip resolution otherwise — the charset gate is
  free); the mild possibility of a true-but-irrelevant third-person line on on-behalf
  calls. Benefit: **the footer fires on day 1 for the population already following the
  fleet protocol, with zero caller changes and zero teaching dependency.** If the operator
  declines this overrule, then RIDER-1 below stops being defence-in-depth and becomes the
  entire feature — and the feature's reach becomes exactly the reach of its teaching.

**RIDER-1 — the teaching ships in the same wave, at three surfaces, pinned.** (i) The
`agent` parameter description states the payoff and the omission consequence — the V1/V2
diff (§1.2) is a measured behaviour flip riding entirely on this string; V1's
*"Omitted: no traffic check"* clause is the load-bearing part (Opus). (ii) The register
render gains one line installing the habit with the agent's LITERAL name — Sonnet's chosen
single highest-leverage change, and the render already does exactly this shape
(`echo in your report: …`): `pass agent=builder-x1 on your lore_tasks / lore_findings /
lore_claim_task calls — it is how pending directives reach you`. (iii) One sentence in
`_INSTRUCTIONS`' MEMORY paragraph, through the declared-paragraph allowlist (the packet's
CL3 pin), never via `_COMMS_DUTY_VOCABULARY`. Acceptance instrument (§1.7 trust ruling): a
consumer-battery leg — fresh agent, register render + schema, does its next mutating call
carry `agent=`? CALL_AGAIN vs ROUTE_AROUND, per packet 03b §C5's template.

**RIDER-2 — the footer's count obeys the counting law.** Whatever fires it, the number in
the line is computed over the WHOLE pending set for that agent (never a capped window), by
a grouped, projection-narrow read — never drain's unbounded full-body SELECT ×1 per call
(#183; scout §B2's `acked_versions_for_ids` precedent). 04b-2's builder brief must carry
this; a footer that lies about a count is a confident-wrong on the highest-frequency
surface the ledger has.

---

## §2 — Q2: `ENFORCED` + pre-check refusal vs create-and-teach (ruling R3)

**VERDICT: CONCUR — hard refusal, whole batch, and it is not close.** Both consults, blind,
chose refusal emphatically (Opus: *"(A), and it is not close"*). The decisive argument is
**who pays**: (A)'s cost is bounded, immediate, and paid by the one agent holding full
context at the cheapest instant that will ever exist for the fix; (B)'s cost is deferred,
unbounded, and paid by strangers — every later agent that meets the unclaimable row
inherits a mystery it cannot distinguish from ledger corruption, and (Opus) *"once I learn
this ledger can durably contain never-claimable tasks, 'blocked' stops being information —
I second-guess every blocked row, which taxes reads that were previously free."* That is
the route-around tax, verbatim. Also structural (Opus): a batch with cross-references is a
graph — *"a graph missing an edge is not 5/6 correct; it is wrong"* — and partial
acceptance needs dependency-aware cascade semantics, complexity that breeds its own
defects. Create-and-warn's real failure mode is *"warned and skipped"*: the warning rides a
success payload an agent N calls into a plan does not re-read. The packet's Exit verb
"TEACHES" is satisfied by the refusal — teaching by refusal at the moment of full context
IS the teaching; a durable wrong row with a scrolled-away warning is not.

**Riders (contract-shape, cheap now, expensive after GREEN):**
- **R2-a — the refusal names the CARRYING ITEM on the batch path.** Consult-unanimous gap
  in the pinned skeleton `unknown {noun}(s): {identities} — {requirement}`: for
  `create_many`, each unknown id should carry its locus — `'step-schma' (item 3, key
  'step-migrate')` — inside the `{identities}` slot (the skeleton survives). Without it, a
  value appearing in two of six items is ambiguous and the first retry is a coin flip.
- **R2-b — the `{requirement}` sentence states the acceptance rule positively AND the
  no-write fact**: *"blocked_by must name existing task ids or batch keys; nothing was
  created."* The explicit no-write is what makes a plain resend known-safe without a
  reconnaissance read (Opus Q1c-5). Note the dispatcher's `key_to_id.get(ref, ref)`
  pass-through makes a typo'd temp key arrive as a "phantom id" — the caller sees its own
  typo'd token verbatim either way, which is the property that matters (§4).
- **R2-c — every unknown id at once, never first-miss-only** — already pinned
  (`test_the_refusal_NAMES_EVERY_phantom…`); recorded here because both consults named it
  independently as first-retry-critical.
- **R2-d — the create-path round-trip cost gets its E-4-style sentence.** The adversary's
  rider-asymmetry finding (P6b #6 / R-15): `create_task` goes 1 → ≥2 round trips (+N for
  the cycle walk). State it as an ACCEPTED COST with the same named re-open trigger shape
  E-4 used. An unstated cost is a surprise; a stated one is a decision.
- **R2-e — the refusal-vs-black-hole justification is a QUANTIFIER claim, and its third
  case is unruled** → §5.1 (MP-5). R3's rationale ("a loud refusal replaces a silent black
  hole") currently holds for two of three doors.

---

## §3 — Q3: the `truncated` flag (escalation ruling E-3)

**VERDICT: CONCUR on the typed result + boolean at the LEDGER seam; two amendments and one
04b-2 rider, all cheap now.** A bool is the right *ledger* surface — the decision tree
belongs at the render (§1.5: recovery moves ride each response). But a bool alone strands
the render:

- **A3-a — the result carries the effective bound.** Add `max_depth_used: int` (the bound
  the read actually ran at, default or explicit) to the typed result. Without it the render
  must import/re-derive the default to teach a re-ask, and drifts when the default changes.
  Opus flagged the exact confusion from the consumer side: 32 ids under an unstated bound
  of 32 — *"I cannot tell whether truncation was on depth or on count, and that ambiguity
  alone forces a re-run."* Self-describing results end that class. (MP-3's argument-bound
  refusals stand beside this — CONCUR with MP-3 as escalated.)
- **A3-b — the type documents the floor property.** The `+collect` traversal is
  breadth-complete at depths ≤ bound (probe §5.1 + adversary §X1: proximity-ordered,
  deduplicated closure) — so a truncated result is a valid FLOOR: *"at least these must
  resolve first."* One docstring sentence converts a merely-honest partial answer into a
  usable one (Opus: it decides *"whether I can safely use the 32 as a floor… or whether the
  partial set is untrustworthy at every level"*).
- **RIDER (04b-2, in E-3's own sentence per the rider law): the rendered truncation line
  teaches the re-ask and NEVER counts the tail.** Required shape:
  `blockers shown to depth {max_depth_used} — more exist beyond (count unknown at this
  depth); re-run with max_depth={2×bound}`. Two halves, both load-bearing: (1) the concrete
  re-ask verb collapses "investigate what to do" into "do it" (both consults; the bare
  boolean forces a mid-chain schema re-read — a full turn); (2) **the counted-elision
  grammar (§1.2) is a TRAP here** — the deeper count is unknowable to the server, so a
  builder reaching for the house `+K more` form must fabricate K. Both consults rated a
  fabricated count the worst outcome on the table (Opus: *"a tool caught inventing one
  number is untrustworthy on all of them… never emit a number the server cannot derive"* —
  the categorical trust loss again). Pin the honest form; a `+K more` render on this line
  is a defect, not a style choice.

---

## §4 — Q4: refusal rendering (escalation ruling E-2)

**VERDICT: CONCUR, unanimously and with a sharpened invariant.** Both consults judged the
asymmetry costless and self-explaining, and the uniform `abc (abc)` strictly worse — Sonnet:
pure noise implying a withheld display name; Opus: *"my first reaction is 'the renderer is
double-printing — is this a formatting defect?'… uniformity of shape purchased with
untruthfulness of content is a bad trade on a surface whose entire job is to tell me what
went wrong."* The consumer-load-bearing property both named, identically, is not shape
uniformity at all: **the refusal contains the offending value verbatim, in the exact form
the caller supplied it, round-trippable against the caller's own payload.** E-2's shape
already guarantees it. Two pins/notes:
- The verbatim-echo property is the invariant to keep pinned (the served-text-by-value pins
  carry it today; keep them value-pinned, never derived from the production formatter).
- **Corollary (Opus): ids in refusals are never elided/truncated.** A `…`-shortened id has
  failed the only load-bearing job a refusal string has. One line in the builder brief.

---

## §5 — Q5: the open hunt — where this design would still earn a route-around

Ranked. 1–3 are actionable now; 4–5 are brief/audit lines; §5.6 is the concur inventory.

### 5.1 MP-5 is UNRULED, and the packet is about to claim a black hole closed while a third door stands

The adversary measured it on a CORRECT build (REPORT-adversary-04b1 §B-3): a task blocked
on a **superseded** blocker is accepted, passes existence, passes the cycle guard, and is
unclaimable forever — every escape transition refuses (`superseded` is non-terminal to the
claim CAS, and permanently so). R3's own justification is defeated through the door it
doesn't name. Rulings recommended:

- **(i) REJECT the adversary's reading (b)** (treat `superseded_by IS NOT NONE` as terminal
  in the CAS). It looks smallest and is wrong: supersession means the work MOVED, not that
  it finished — dissolving the block silently un-blocks dependents while the successor is
  still open. That is the inverse black hole (premature claimability), quieter and worse.
- **(ii) RULE (04b-1, near-zero marginal cost): the blocker pre-check refuses a SUPERSEDED
  blocker with its own teach naming the successor.** The check already reads the blocker
  rows in one grouped query; projecting `status`/`superseded_by` alongside existence is
  free. Vocabulary: `task X is superseded by Y — block on Y instead`. This closes the
  at-create door with a recovery the agent can act on in one edit, exactly parallel to the
  phantom refusal. (A blocked_by naming a superseded task is NEVER legitimate: the CAS can
  never resolve it — the refusal is correct in all cases.)
- **(iii) RULE (04b-2, renders): the moment-of-consequence and moment-of-causation
  teaches.** Supersession can happen AFTER dependents exist — (ii) cannot close that path
  (the quantifier law: don't guard only the write that prompted the work). (a)
  `supersede_task`'s response warns when the predecessor has dependents — one 1-hop read
  the new edge makes cheap (dependents of X = `X->blocks->` out-edges, E-1's direction):
  `N tasks are blocked on the superseded task and will never unblock — supersede or
  re-create them against {successor}`. (b) `_render_claim_result`'s blocked branch resolves
  blocker statuses and names the superseded case with the same recovery. Today that branch
  serves `blocked_by [...] unresolved` — a fact, not a decision tree (§1.4).
- **(iv) Dependency-transfer on supersede** (rewriting dependents' `blocked_by` to the
  successor) is the full fix and is DEFERRED — it breaks `blocked_by`'s post-creation
  immutability, which the claim path's stated assumption rides. Named re-open trigger: the
  first fleet incident of a dependent stranded by a live supersede, or packet 05's
  await/story work touching the claim path — whichever first.

### 5.2 R5's unstated schema half: `query` still serves the whole table on the no-limit path

R5 rules the tool-level `limit` pushes down. **Measured at HEAD: `query` REFUSES `limit`**
("'since'/'limit' apply only to action='rollup'"), and an unfiltered query served me the
entire ~110-row ledger. So R5 implies a served-schema widening (limit becomes legal for
`query`) that no ruling states — and the path every existing caller is on (no limit,
because the parameter didn't exist) remains a whole-table serve even after R5 lands.
**Recommendation:** (a) widen `limit` to `query` explicitly (schema + description); (b) the
no-limit query gets a DEFAULT display cap with the house counted-elision grammar — honest
total from the store-side count, `+K more — re-run with limit=N` (§1.2; "caps are never
dead ends", §2 of DESIGN-LAW). This windows the RENDER, not the answer — distinct from the
#253 addendum's `test_the_UNFILTERED_blocked_read_is_ALLOWED_to_grow`, which is about rows
READ (a true aggregate needs them); the elision line keeps the full answer one re-ask away.
Default value operator's-call (fleet precedent: config default + hard ceiling).

### 5.3 Caller identities are hostile text, and the footer is a new render of them — measured, not hypothetical

> **⚠ CORRECTION (2026-07-28, post-`f00ebd5`; lead-measured, ruled as T3 at `5a2dca9`):**
> the "served **raw** / un-shaped" framing in this section and §0.4 is **RETIRED — too
> strong.** Measured at the seam: `safe_str`/`sanitise_line` COLLAPSE newlines, so one
> stored value cannot forge a ROW BOUNDARY; what survives verbatim is SAME-LINE text only.
> The recommendation survives sharpened, which is why the section stands: same-line
> injection in a task row is *misreading*; in the FOOTER it is an *INSTRUCTION* — agents
> obey instructions where they merely misread rows. T3 rules the footer-shaped hostile
> fixture mandatory. Read everything below through that correction.

The production ledger is serving, today, a stored owner value shaped like a finding row
(`owner smoke - [#99 open] forged finding entry (kind friction, by attacker)` — task
`7b701f0e…`, my own query, §0.4). The new surfaces this packet mints interpolate caller
identities in three places: the footer (agent name + counts), the refusal `{identities}`
slot, and OVERRULE-2's third-person line. **Rule already exists; this is its application:**
every one rides the sanitiser seam, and the hostile fixture for the footer includes a
**footer-shaped forgery in the identity value** (an `agent=` value that reads like
`— 3 directives await you — lore_comms action=drain …`). L1's `Rendered`-then-`str()`
choice is right for exactly this reason, and L1's demanded type-choice pin plus this
fixture are the two guards that keep it true. (The #99 row also confirms OVERRULE-2's
fallback is safe on hostile input: exact-match resolution of a forged string simply
resolves nothing.)

### 5.4 The `(unspecified rejection)` reachability principle — MP-3 generalised

MP-3 (concur) closes `max_depth`. The principle the builder brief should carry: **on the
new verbs, every caller-reachable engine rejection is either pre-checked into a teaching
refusal or classified into a teaching error; a raw `statement N of M was rejected
(unspecified rejection); see the server log` reaching a caller is a defect.** An
undiagnosable error is the anti-teaching surface — the agent cannot distinguish its own
mistake from a broken tool, and (consults, §1.2/§3) blames the tool. Cold-audit sweep line:
enumerate the new verbs' engine-rejection paths, assert each is laundered or pre-checked.

### 5.5 R7's composed cost, named once

R7 + its rider put the cycle walk's N column reads AND the two-read partition inside one
transaction. Fine — but create's cost is now O(chain depth) reads in one txn with no stated
bound. At the measured fleet scale (~110 tasks, chains of a handful) this is nothing;
recorded so the day someone builds a 5,000-deep DAG the surprise has an address. No action;
a bound here would be tuning without a measurement (deferral law, shape 1).

### 5.6 Concur inventory (audited, no manufactured disagreement)

| ruling | verdict | note |
|---|---|---|
| R2 (#247 closed here) | **CONCUR** | fourth pass-forward would have been a can-kick; mechanism already shared |
| R4 (unacked = `acked_at IS NONE` ∧ directive) | **CONCUR** | the one reading that surfaces an otherwise-invisible state; the others restate neighbours |
| R5 (limit push-down) | **CONCUR + §5.2 rider** | half-fix-that-reads-as-a-fix is the right frame |
| R6 (one cycle detector, tool-seam pin) | **CONCUR** | the pin at the seam is the consumer-facing half — an agent must meet ONE vocabulary |
| R7 + rider (txn snapshot; column walk) | **CONCUR** | served partition agreeing with the CAS is trust, not tidiness; §5.5 cost note |
| L1 (`Rendered`, explicit `str()`, own pin) | **CONCUR** | §5.3 supplies the hostile fixture it needs |
| L2 (batch footer iff ≥1 wrote) | **CONCUR** | same principle as claim's losing branch; write-count return is the honest instrument |
| L3 (generalise, never clone; mutation-proven) | **CONCUR** | |
| E-1 (blocker→blocks→task) | **CONCUR** | adversary X1 measured the reverse arrow 15/15 — the rider was discharged properly |
| E-2 / E-3 / E-4 / E-5 | **CONCUR** | §§3–4 riders; E-4's stated-cost shape is the model R2-d copies |
| writes-only footer trigger | **CONCUR** | a read-triggered footer is noise-as-hit — the §1.4 cardinal failure — and trains agents to ignore the line |
| MP-1/2/3/4, C-DEF E-A fix, R-e closure | **CONCUR** | in contractfix's hands; re-run the adversary on whichever #253 artifact survives the E-B merge (the adversary's own escalation — Section I + addendum have never been graded) |

---

## §6 — Consult diff (what disagreed, which is where the information was)

Unanimous (all three models incl. my leg): hard refusal on Q2; fabricated counts as the
worst trust outcome; verbatim round-trippable tokens as the refusal's one load-bearing
property; silent unresolvable-identity as a route-around trigger; V1-vs-V2 description
flipping the `agent=` behaviour; uniform `abc (abc)` worse than the asymmetric render.

Diffs that mattered:
1. **Highest-leverage Q1 fix:** Sonnet — the register-reply standing instruction (spawn-time
   channel). Opus — within the offered surfaces the same, but ranked two designs above the
   whole framing: the actor-resolution fallback (*"requires nothing"*) and a per-call
   absence nudge on every un-identified mutating call. I adopted the fallback (OVERRULE-2)
   and **rejected the per-call absence nudge**: it fires on every solo/operator call
   forever — noise-as-hit for the population that has no fleet identity — and under
   OVERRULE-2 the absence case it treats mostly disappears. The diff is recorded because
   the rejected instrument is the better answer if OVERRULE-2 is declined.
2. **The on-behalf hazard** (lead drains the builder's inbox via the footer's copy-pasteable
   command): Opus only. Adopted as OVERRULE-2(b)'s grammar split. Sonnet's counterpart
   (undisclosed coupling on a provenance field) became OVERRULE-2(a). Neither model saw the
   other's hazard — the diff, not a merge, produced the design.
3. **Habit durability:** Sonnet — session-bounded, lost on respawn. Opus — finer: lost on
   COMPACTION and on unreinforced silence, both silent. Opus's version is why RIDER-1 keeps
   all three teaching surfaces even under OVERRULE-2 (re-read surfaces survive compaction;
   the fallback needs no habit at all).
4. **Q3 floor property** (truncated set usable as "at least these first"): Opus only →
   A3-b. **Q2 item-location** in batch refusals: Opus explicit, Sonnet implicit ("which
   item/field") → R2-a.

---

## §7 — Costs of the overrules, honestly

| change | cost | who pays |
|---|---|---|
| OVERRULE-1 (loud unresolvable) | one shared-vocabulary teach line + 3 pins | 04b-2 builder, hours |
| OVERRULE-2 (fallback tier) | one charset-gated registry read per mutating `agent=`-less call; disclosure clauses on 3 field descriptions; the grammar split; ~4 pins | 04b-2 builder, a day; the store, one bounded read per write call |
| RIDER-1 (teaching, 3 surfaces + battery leg) | prose + one battery scenario | 04b-2 |
| §2 riders (item-locus, no-write clause, cost sentence) | contract edits BEFORE the builder — one skeleton-slot rendering + two sentences | contractfix, now |
| §3 amendments (`max_depth_used`, floor doc, render pin) | one field on a not-yet-built type + one 04b-2 pin | contractfix + 04b-2 |
| §5.1 (ii) superseded-blocker refusal | one projection widening + one vocabulary + pins | 04b-1 builder, hours |
| §5.1 (iii) two render teaches | two render lines + one 1-hop read | 04b-2 |
| §5.2 (query default cap + elision) | one ruling + house grammar reuse | operator ruling, then 04b-2 |

Everything above lands before a line of production code exists. The identical changes one
wave later cost a contract amendment, an adversary re-grade, and a fix wave each.

---

*Consults: 4 subagents (Sonnet ×2, Opus ×2), prompts identical per question, no repo
access, blind to the rulings; transcripts ephemeral — load-bearing lines quoted above are
the durable record. Friction filed this session: finding #254 (lore_search floor-of-one on
a path-scoped constant lookup; routed to grep and said so). My own probe failures: none
that survived to a claim — the one stat-dirty `git status` observation (`surreal_schema.py`
flagged M with an empty diff after a mutation proof's byte-exact restore) resolved on
re-read and is noted in REPORT-design-sidecar-04b.md.*

---

# Follow-up 1 (2026-07-28, post-`5a2dca9`)

*Rulings landed on the first-task verdicts: R8 (both footer overrules accepted, the
description string promoted to load-bearing), R9 (query limit + default capped render),
R10 (MP-5 closed both halves, superseded-as-terminal rejected, transfer deferred with
trigger), T1–T5. §5.3 above now carries the T3 correction: the "raw" framing is retired.*

## §8 — The fleet-corpse question (#258): what does an agent calling `fleet` actually need?

**The measured situation** (lead, 2026-07-28, deployed surface): `fleet` serves 39
non-retired agents, 38 "active" — essentially all dead packet-03b smoke agents across ≥7
sessions, 18h–2d stale. The deploy gate is the polluter: the instrument that certifies
comms degrades it on every run. The render is per-row HONEST (derived STALE, true counts,
counted elision) — which is exactly why no honesty pin catches it: every row is true; the
SURFACE is drowned. 04b-2 is about to add two more numbers per corpse.

**The consumer question decides it, and the deciding fact is structural, not a
preference.** An agent's actionable universe through the served comms surface is its
SESSION — measured from the served `send` contract itself: the `to` description reads
*"Every name is resolved in YOUR session only"*, and broadcast is *"every non-retired
teammate in your session."* An agent cannot message, nudge, await, or re-route ANY
cross-session row. For an agent consumer, every out-of-session row in the default view is
a row about someone it cannot reach — noise by construction, at any freshness. **The
corpse problem is a SCOPE problem wearing a freshness costume.** Verdict is composition
(d), four parts:

- **B1 — the cause (candidate (a), CONCUR, necessary regardless of any render change):**
  the deploy-gate smoke retires its own agents in a finally-block, and a one-shot
  operator-run backfill retires the existing corpses. An instrument that durably degrades
  the surface it certifies fails the instrument test on every run. This alone does not
  settle the render, because corpses are a PERMANENT feature of fleet data, not a smoke
  bug: leads TaskStop agents routinely and a killed agent never retires itself — the C4
  drill's own arc (*kill → orphan surfaces in fleet*) DESIGNS for corpses.
- **B2 — the surface: `fleet` defaults to the CALLER'S session.** No new parameter is
  needed to know it: `fleet` requires registration (measured — my own unregistered call
  was refused by name), so the handler holds `agent_row.session` before rendering. The
  cross-session tail collapses to ONE counted line teaching the widening re-ask
  (`+N agents in M other sessions — session=<s> to inspect one, all_sessions=true for
  everything`), per the caps-are-never-dead-ends law (DESIGN-LAW §2). The 2026-07-26
  no-consumers grant covers the default change, and 04b-2 already owns this render.
  The operator/lead observability view keeps everything, one re-ask away — and that is
  the view where corpses are INFORMATIVE.
- **B3 — do NOT freshness-filter within the session (candidate (c) REJECTED as the
  primary):** in-session, a STALE row is not noise — it is the orphan signal the
  subsystem exists to surface, and (see below) the row whose NEW columns matter most. A
  freshness window would hide exactly the rows the drill certifies. Freshness stays a
  derived ANNOTATION (`[active ⚠ STALE]`), never an exclusion. ((c) remains available as
  a secondary nicety on the explicit all-sessions view; B1+B2 mostly dissolve the need.)
- **B4 — candidate (b), the reaper: REJECTED in both forms.** Hard-delete re-arms #105
  (concur with the finding's own note — the comms design assumes agent rows are never
  hard-deleted, and deletion mints ghosts behind `ENFORCED`'s future-writes-only guard).
  Auto-retire is subtler and worse: retirement is a STATUS ANOTHER AGENT OWNS;
  heartbeat-age is evidence, not proof (an agent quiet behind a background gate run is
  this fleet's own documented benign waiting mode); and a READ verb that MUTATES rows is
  a surprise no consumer should meet. Writing a heuristic guess as durable status is the
  confident-wrong class — categorical trust loss on the registry itself. An explicit
  operator-invoked retire sweep stays legitimate (a decision, not a heuristic).
  Long-horizon registry growth is a RETENTION question, same class as the open trace-GC
  task (`d9395d54…`): deferred, named re-open trigger — roster size passes an
  operator-set bound, or the first hosted deployment (packet 39), whichever first.

**Does the answer change once the unread/unacked columns exist? Yes — the columns raise
the stakes of scoping, in both directions, which is why B2 should land WITH or BEFORE
them:**
1. **In-session, unread/unacked on a STALE row is the highest-value cell on the
   surface**: stranded directives — traffic someone must re-route or explicitly retire.
   That is a §1.4 decision tree the render can teach in one line. Under the global
   default, the identical cells on 38 unreachable corpses are unactionable numbers —
   computed, served, skimmed — training agents to ignore exactly the signal class B3
   preserves. Same cells, opposite trust outcome, decided purely by scope.
2. **Cost follows scope**: the per-row grouped reads (counting law — each cell covers its
   agent's WHOLE pending set, projection-narrow, never drain's full-body read ×N, #183)
   shrink from ≤200 displayed rows to actual-fleet-size by construction, not by tuning.

**#257's class (brief-theatre), one note:** a placeholder brief body served with full ack
ceremony has no mechanical pin that survives false positives (a one-line brief is
legitimate; `x` is only visibly theatre to a reader). Its instrument is the consumer
battery's honesty probes — *does teaching match behaviour* — where R8's rider already
lives. Named so the class is not re-derived; no new machinery recommended.

**Consult judgment: NOT contested — no consult run.** The deciding fact (the send
surface's session-scoped universe) is structural and measured, not a preference between
close options. Recorded per the consult rule in my brief.

## §9 — Rounds 2 and 3 reviewed verbatim at `5a2dca9`: nothing to overrule

R5/R6/R7 and the MP-4a rider were concurred in §5.6 and survive re-reading. On round 3:
- **T1 (answer-cap, exhausted-scan says so): CONCUR.** One pin-design caution, flagged
  not overruled: answer-cap semantics make rows-read on a `blocked=`-filtered capped
  query legitimately vary with the candidates' blocked-distribution. A future
  `rows-read ≤ f(limit)` pin on that path would be wrong BY DESIGN — the boundedness
  instrument's property stays *"does not grow with UNRELATED ledger size"*, never
  *"≤ limit."* One sentence in the builder brief keeps anyone from pinning the wrong
  invariant.
- **T2: CONCUR** (it is this audit's §5.4, ruled).
- **T3: CONCUR**, and §5.3 now carries its correction — the sharpening (same-line forgery
  is an INSTRUCTION on the footer surface) is better than my original claim.
- **T4 (reach as a checked variable): CONCUR** — the six-defeats law applied to the new
  instrument; a disclosed blind spot is still a blind spot until coverage is asserted.
- **T5 (`array::len(array::distinct(blocked_by))` in the CAS): CONCUR, and it is the
  right fix of the three available.** A schema-side distinctness ASSERT guards future
  writes only (the FLEXIBLE-array lesson) — the CAS-side fix is the only one that also
  heals LEGACY rows; and the served partition's ANY-semantics is duplicate-insensitive,
  so the two layers agree after the fix with no second change. The ≥8-way × 20 demand is
  the standing concurrency law correctly applied to a live-CAS edit.
