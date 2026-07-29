# REPORT-design-sidecar-04b — model-consumer audit of the 04b ruled design

brief-base v7 read

## SUMMARY BLOCK

- **state:** done (first task); STANDING BY for follow-ups — do not treat this report as exit.
- **deliverable:** `docs/design/2026-07-28-04b-model-consumer-audit.md` — cited, measured-vs-inferred labelled, every number re-derived (the "~17 returns" is 15, re-confirmed by AST at `2b8aa01`).
- **Q1 (R1, footer identity): CONCUR on mechanism · OVERRULE ×2 + 2 riders.** MEASURED via blind Sonnet/Opus consults: with a terse param description NEITHER model passes `agent=`; with a payoff-stating one BOTH do — R1's fate rides on an unruled `Field(description=)` string. OVERRULE-1: `agent=` supplied-but-unresolvable TEACHES loudly, never silence (both models: silent typo ⇒ route-around forever). OVERRULE-2: reinstate strict exact-match fallback on required `owner`/`actor`/`created_by`, served THIRD-PERSON, no drain imperative (closes Opus's stolen-drain hazard), coupling disclosed on the field; both consults ranked this above the ruled shape. Costs: one charset-gated registry read per identity-less write; ~7 pins; a day of 04b-2.
- **Q2 (R3, hard refusal): CONCUR** — consult-unanimous ("not close"). Riders: batch refusal names the CARRYING ITEM; requirement sentence adds "nothing was created"; create-path round-trip cost gets its E-4-style sentence (adversary R-15).
- **Q3 (E-3, truncated): CONCUR + amendments** — result gains `max_depth_used`; docstring states the floor property; 04b-2 render pin: teach the concrete re-ask and NEVER count the unknowable tail (the house `+K more` grammar is a fabrication trap here — both consults rate an invented count the worst outcome).
- **Q4 (E-2): CONCUR** — uniform `abc (abc)` measured worse (reads as a render defect, teaches a falsehood). The invariant to keep pinned: verbatim, round-trippable, never-elided offending tokens.
- **Q5 top findings:** (1) **MP-5 is UNRULED** — the superseded-blocker door defeats R3's own justification on a correct build; recommended: refuse at the pre-check (free — same grouped query) + supersede/claim render teaches; REJECT superseded-as-terminal (silently unblocks moved work). (2) **R5's unstated half** — `query` REFUSES `limit` at HEAD (measured on my own call, which also served me the whole ~110-row table); R5 implies a schema widening + the no-limit path needs a default cap with counted elision. (3) The production ledger is serving a stored forged-owner row (#99 probe) raw — the footer/refusal renders need the footer-shaped hostile fixture. (4) `(unspecified rejection)` reachability principle for the cold audit. Full ranking + concur inventory: doc §5.
- **consults run:** 4 (Sonnet ×2, Opus ×2), identical prompts per question, blind, diffed not merged. Key disagreements (doc §6): Opus alone saw the on-behalf drain-theft hazard; Sonnet alone the undisclosed-coupling hazard — the diff produced the design. Opus's per-call absence nudge REJECTED (noise for identity-less callers) but recorded as the better answer if OVERRULE-2 is declined.
- **`Packages considered:` none — no mechanism specified** (design audit; the one instrument question — consult harness — used the Agent tool, no dependency).
- **friction filed:** finding **#254** (lore_search path-scoped floor-of-one on a constant lookup → I routed to grep and said so). Also observed and self-resolved: a stat-dirty `git status` M on `surreal_schema.py` (empty diff; a mutation proof's byte-exact restore) — clean on re-read, no flag.
- **decisions-needed (operator):** rule OVERRULE-1/OVERRULE-2 (or decline 2 and promote RIDER-1 to load-bearing); rule MP-5 per §5.1; rule the query default cap (§5.2). The §2/§3 contract riders are cheapest while contractfix-04b1 is still open.
- **receipt pointers:** doc §0 (measurements + re-derivations) · §1.2 (the consult table) · §5.1–5.3 · §6 (diff) · §7 (costs).

## Body

The doc is the deliverable; this report adds only what a lead needs to route it:

1. **Timing matters more than any single verdict.** The §2 riders (item-locus in the batch
   refusal, the no-write clause) and §3 amendments (`max_depth_used` on the typed result)
   are CONTRACT-SHAPE changes. `contractfix-04b1` is open right now; landing them there is
   one edit each. After the builder goes GREEN they each cost a contract amendment + an
   adversary re-grade.
2. **MP-5 (§5.1) is the one item where the packet would otherwise ship claiming more than
   it delivers** — the exact #219 prose-vs-behaviour class, at packet scale: INDEX/Exit
   prose says the silent black hole is closed while the adversary's B-3 door stands on a
   correct build. Recommendation (ii) is 04b-1-cheap because the pre-check's grouped query
   already holds the rows.
3. **Nothing in the four E-rulings or R2/R4/R6/R7/L1–L3 needed overruling** — the concur
   inventory (§5.6) is genuine, not deference; where I checked, I checked (E-1's reverse
   arrow was discharged by the adversary's X1 measurement, 15/15).
4. The consult transcripts are `/tmp`-ephemeral; every load-bearing line is quoted in the
   doc, which is their durable address (brief-base §1 deliverable-address rule applied).

STANDING BY.

---

## Follow-up 1 (2026-07-28, post-`5a2dca9`)

- **A (correction): accepted and landed at the durable address** — doc §5.3 + §0.4 now
  carry the dated retirement of the "raw" framing; T3's sharpening (same-line forgery is
  an INSTRUCTION on the footer surface) is recorded as better than my original claim.
- **B (#258, fleet corpses): answered in full — doc §8.** Verdict: composition. B1 smoke
  retires its own agents (cause; necessary regardless). B2 `fleet` defaults to the
  CALLER'S session — no new parameter needed (fleet requires registration, measured; the
  handler already holds the caller's session) — with one counted cross-session line; the
  deciding fact is structural and MEASURED: the served `send` contract resolves names in
  the caller's session ONLY, so out-of-session rows are unreachable-by-construction noise
  for an agent. The corpse problem is a scope problem wearing a freshness costume. B3 no
  freshness EXCLUSION in-session (stale rows are the orphan signal; annotation stays).
  B4 reaper REJECTED both forms (hard-delete re-arms #105; auto-retire writes a heuristic
  guess as a status another agent owns, on a READ path); retention deferred with a named
  trigger (roster bound or first hosted deploy/packet 39). **The columns change the
  stakes, not the answer**: in-session, unacked-on-STALE is the stranded-directive signal
  (highest-value cell); cross-session it is unactionable noise — so B2 lands WITH or
  BEFORE the columns, and cost shrinks to fleet-size by construction. Consult judged NOT
  contested (structural deciding fact); none run, per the rule.
- **C (rounds 2/3): read verbatim at `5a2dca9` — NOTHING TO OVERRULE** (doc §9). T5's
  CAS-side distinct is the right fix of the three (only one healing legacy rows; the
  partition's ANY-semantics already agrees). One flagged caution, not an overrule: under
  T1's answer-cap, a future `rows-read ≤ f(limit)` pin on the blocked-filtered path would
  be wrong by design — keep the boundedness property "does not grow with UNRELATED ledger
  size". One builder-brief sentence.

STANDING BY.

---

## Follow-up 2 (2026-07-28, post-`25e2985`) — #259, the STALE badge

- **Own miss owned first (doc §10 header):** my S1-b justification interpreted the badge
  from its NAME, never its predicate — an un-derived claim inside my own ruling; the
  operator's reap-first ordering is what exposed it.
- **S1-b's CONCLUSION SURVIVES, justification replaced and STRONGER (doc §10.1):** a
  predicate measured to fire on healthy agents is disqualified from driving EXCLUSION a
  fortiori — the freshness window would today be hiding a live contract author.
  Annotation-never-exclusion stands; the annotation itself falls.
- **The badge: candidate (b) NOW (doc §10.2)** — retire `⚠ STALE`, serve the age (already
  rendered). Anchored: `DEFAULT_COMMS_STALE_HEARTBEAT_S = 600`, one boolean spanning
  1,020s to 1,407,600s. §1.3 asymmetry decides it: a measure without a verdict
  under-claims (free); a wrong verdict kills the class categorically. (a)/(c) rejected as
  rumour thresholds on a channel that measures comms cadence, not liveness; (c)
  re-openable only behind the named measurement (per-role cadence after 04b-2 traffic;
  prediction stated: the overlap won't vanish).
- **(d) is the second step, shipped WITH its consumer (doc §10.3):** declared cadence ⇒
  `overdue (declared ≤20m, silent 45m)` — a verdict TRUE BY CONSTRUCTION; no declaration
  ⇒ age only (non-adoption fails honest, unlike the badge). The R1 lesson applied to
  itself: the parameter lands in packet 06 with the drill that pays it, never before as
  dead schema. 04b-2 ships (b) alone.
- **Unacked-on-STALE (doc §10.4):** the cell's value survives — it was never the badge's;
  it is unacked-N composed with age. The badge's noise threatens only the IMPERATIVE
  teach line, which would instruct callers to re-route a live builder's traffic (the
  drain-theft sibling). Same grammar rule as R8: imperatives ride only TRUE verdicts —
  04b-2 ships the columns as measures, no stranded-imperative; the imperative arrives
  with (d)'s overdue verdict. Packet 06 owed notice: the glyph retires; orphan detection
  rides (d).

STANDING BY.

---

## Follow-up 3 (2026-07-28) — re-grade under the HARD definition (doc §11)

- **Frame verified at the working address** (`lore_recall`, myself); graded against the
  memory's text; the CLAUDE.md landing is 11-i-b's business.
- **Your first pass is right with two credits (doc §11.1):** the schema/migration legs
  and the #253 PARTITION legs already pass leg 2 (`_seed_legacy_task` + fail-closed +
  claim-agreement over edge-less rows — re-derived by grep). Every OTHER served surface
  is scope-diffed and NOT forgery-pinned. Owed constructions, tabled per dependency ×
  mode: traversal (timeout ⇒ teaching error, never partial-as-complete), fleet columns
  (failed grouped count must NOT render `0` — byte-diff vs healthy-zero must differ),
  footer explicit leg (check-FAILED ⇒ loud line, write succeeds — a NEW fourth leg of my
  own OVERRULE-1), pre-check (failed existence read ⇒ fail-CLOSED, constructed), R9's
  elision total (never invent the number).
- **THE HEADLINE (doc §11.2): the legacy-edge world deploys itself.** No backfill exists
  anywhere (grepped); production tasks carry `blocked_by` columns TODAY (my §0.1 query —
  04b-2's own row) and will have NO `blocks` edges at deploy, so the edge-riding
  traversal serves `ids=[] truncated=False` — clean, confident, wrong — on the exact
  rows the fleet is working. The partition is proven safe over that world; the traversal
  fails BOTH legs. ESCALATION with recommendation: backfill in `ensure_ready`,
  pre-filtered through the L3 existence policy (legacy phantoms meet `ENFORCED` — a
  naked backfill rolls back the whole migration), phantom skips RECORDED, forgery-pinned
  in the existing dirty-store harness. Fallback if refused: the render names the bound
  as a fact — legal, and a permanent tax (a) deletes instead.
- **Self-corrections (doc §11.3):** OVERRULE-1 gains the check-failed leg;
  OVERRULE-2(a)'s "may append" was disclaimer-shaped — replaced with the fact-shaped
  asymmetric bound (present ⇒ verified; absence asserts nothing); §10's age render
  passes both legs.
- **Consult discount (doc §11.4):** conceded — no question zero, all four in-repo.
  Graded per finding AGAINST the bias direction: the V1/V2 flip survives STRENGTHENED
  (house law biases toward passing `agent=`; both models still declined — survival under
  adverse bias beats a cold read); the two hazards survive (asymmetric findings —
  contamination manufactures unanimity, not asymmetry); Q2/Q4 survive on mechanism;
  the route-around VOCABULARY unanimity is downgraded to colour, and no verdict rested
  on it alone. Going forward: question zero in every consult; out-of-repo spawns for
  served-string claims.

STANDING BY.

---

## Follow-up 3-amended (2026-07-28) — the derivation (doc §12; law read in full at the worktree, read-only)

- **§11.0 corrected in place**: the law and receipts exist on disk (the `lore-pkt11i-b`
  worktree; later the same day, this checkout's `CLAUDE.md` too). §11's verdicts stand —
  the fuller text tightens, not changes, them.
- **The derivation exists, and only because of this repo's own prior law (doc §12.1):**
  *a stateful dependency of a served surface is an I/O SEAM reachable in its call graph,
  where the seam set is CROSS-DERIVED from the enforcement instruments that already
  police each I/O class* — store→`_txn` proven sole-door by the #136 runtime guard
  (reach a checked variable, T4); subprocess→the packet-01 exec gate; clock/fs ownable
  by the 02a deny-by-default sweep pattern. Three packets of ONE-IMPLEMENTATION are what
  make the seam registry an evidence-backed allowlist instead of a curated hope.
- **The script it implies — `scripts/forgery_sites.py` (doc §12.2):** verb axis DERIVED
  (tool registrations + the literal action-dispatch tables as walk INPUTS — the spec
  indirection is where naive walks go blind); call-graph walk ∩ seam registry → verb ×
  kind pairs; × the law's four modes → the worklist; meta-pin: every pair carries a
  constructed pin or a recorded named bound, and a no-seam verb's emptiness is ASSERTED.
  Worklist, never a verdict — registration_sites.py's posture inherited.
- **Bounds stated plainly (doc §12.3):** the walk is astroid-bounded (believed beyond the
  literal dispatch tables); the clock/fs seam rows are currently REASONING not
  construction until their sweep is built; and **no such script exists today — §11.1's
  table is the curated INTERIM, bounded and said so.** Whether the script lands as a
  small instrument packet or a 04b-2 exit-gate item is the operator's sizing call.
- **Worked example of the retiring clause (doc §12.4):** A3-a's `max_depth_used`-in-the-
  result IS the derived-`n` form; the rejected alternative (render imports the constant)
  is the restated-`n` false clear wearing verifiability. The packet and the law already
  agree there.

STANDING BY.
