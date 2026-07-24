brief-base v6 read

# DESIGN-03b-recertification — the re-certification protocol for packet 03b's contract phase

**Authority:** design-comms-03b-r2 (Fable design sidecar, packet 03b — successor to
design-comms-03b; delegated design authority per the 03a-2 precedent). These are RULINGS the
lead implements; anything that is operator authority (scope, spend, weakening a committed
assertion) is framed as a FORK in RC10, with a recommendation.
**Read at:** working tree `6bfe820` (clean), 2026-07-24. Every claim below is dated to that SHA
unless it names another.
**Sources (cited, not re-transcribed):** `docs/plans/v2/03b-comms-message-surface.md` ·
`docs/plans/v2/03b-comms-surface-design-rulings.md` (S1–S8) ·
`docs/plans/v2/03a-2-consume-path-design-rulings.md` · `~/.claude/agents/contract-adversary.md` ·
the seven packet reports (repo-root at `6bfe820`; to be archived under
`docs/plans/v2/receipts/2026-07-24-packet03b/` per the archive law — all citations below use the
report NAME + section, which survives the move) · repo CLAUDE.md (C-DEF law, quantifier law,
fixture-discrimination law, "every artifact gets an adversary", the two-wave escalation tell).
**Operator context, governing:** the packet is declared suspect (contract authors certified
their own contracts); and *"Sonnet 5, opus and fable agents are the consumers of Lore, not
humans. THEY need to be satisfied with 03b… They are the client."* Both directives are treated
as standing law here.

---

## RC0 — The taint, sized precisely (the remedy must fit the disease)

The operator's charge is correct at the layer that matters, and the protocol below is built on
an exact map of WHERE it bites. Re-derived from the commit graph at `6bfe820`
(`git log 0223291..6bfe820`) and the seven reports:

| bucket | content | certification it actually has | disposition |
|---|---|---|---|
| **B1 — pre-adversary corpus** (`3b8866a`…`db225d4`, frozen at `45cc161`): the 296-pin committed base + amendments 1–10 + D9/D10 + the 41-pin telemetry contract (`a774c8f`) | **Independently graded, twice.** Both contract-adversaries graded the frozen corpus AT `45cc161`: surface INSUFFICIENT (32/41 wrong builds survived), telemetry INSUFFICIENT (11 survived). Both adversaries ALSO built their own reference implementations and independently confirmed satisfiability of this corpus (surface: 1092/0 "on first run, no iteration on the contract"; telemetry: 41/41 with the E4/R10 sequencing caveat). The operator's P2-confirms-the-fix condition on amendments 1–10 was DISCHARGED by the surface adversary's §4 perturbation pass. | **Authority RETAINED** — as "graded-insufficient-then-amended". The pins stand; the holes were named. Nothing in B1 is struck. |
| **B2 — the post-adversary delta** (exactly four test commits: `7bc6a08` surface fix wave +28 pins; `00a92dd` R5-outcome-2; `86abf1e` telemetry fix wave +12 pins & 2 strengthenings & 7 cross-suite amendments; `6bfe820` the 8th-edit fix) | **Author-only.** Satisfiability 1162/0 and 1022/0, mutation tables 34/34 and 13-row — all produced by each wave's own author against its own reference build. **No adversary has ever seen B2.** The scope grant's "each mutation-proven" condition was discharged by the AUTHORS, i.e. not discharged in the sense the law intends. | **Authority SUSPENDED** — not presumed wrong, presumed UNGRADED. This is the re-certification's target. |
| **B3 — the receipts themselves** (871/0 · 1063/0 · 1092/0 · 1162/0 · 41/0 · 1022/0 + the mutation batteries) | Author-graded throughout. Note honestly: the author reference builds DID catch real committed defects pre-adversary (D1, D3, D7, D9) — the receipts are not worthless as evidence of diligence. They are worthless as CERTIFICATION, because builder≠grader was violated at exactly the layer the C-DEF law assigns to the adversary ("the adversary's own reference build … is the natural instrument"). | **STRUCK as certification, RETAINED as history + reproduction recipes** (RC6). |
| **B4 — the design rulings** (S1–S8, D2/D3/D10, E2/E3, WB9 correction, MP9, R5-outcome-2; 03a-2 R1–R6) | Sidecar-authored from design sources + own probes; the load-bearing measured facts were independently corroborated (the S7 rung fact re-derived by the telemetry adversary with a STRONGER instrument; the WB9 defect in S7's own table was found by the adversary and conceded/re-ruled — the system catching its own design authority). | **Authority RETAINED**, with three narrow items adjudicated in RC5. |

**The one thing NOBODY has ever done, in any bucket:** run ALL EIGHT suites against ONE
reference build. Every satisfiability receipt in this packet's history — author's and
adversary's alike — was a per-wave silo (three surface files, or five telemetry-side files).
The seam between the two waves (both contracts constrain `server.py`'s dispatcher; the drain
render and the drain annotation live in the same handler; the E4/R10 sequencing coupling; the
R8 fake-signature parity) has never been co-satisfied anywhere. RC2.5 makes this the packet's
final satisfiability gate.

---

## RC1 — Verdict on the lead's proposal

**ADOPTED, with corrections.** All three legs are the right instruments. The corrections, each
argued in its section:

1. (a)'s "from the design rulings ALONE" is under-specified in a way that would manufacture
   dozens of false over-pin findings — the ruled vocabulary partially lives in the contract
   *by reference* ("the committed broadcast variant"), so a truly contract-blind builder cannot
   match ruled templates byte-exactly. RC2.1 defines the CANON precisely, including a
   lead-prepared vocabulary extract.
2. (a)'s adjudication path ("fix the pin / escalate the ambiguity") is two categories short.
   The record proves FOUR outcomes exist: pin defect, ruling ambiguity, **reference-build
   defect** (the prior telemetry adversary's own reference violated three rulings — E1/E2/E3 of
   REPORT-contract-telemetry-03b-fix), and **ruling defect** (D3: a design-doc-prescribed
   instrument was a false gate in both directions). RC2.3 gives the four-way taxonomy and the
   adjudicator.
3. (a) re-runs the whole historical battery; that duplicates independently-bought coverage and
   dilutes depth. RC2.4 focuses fresh P1/P2 depth on the UNGRADED delta (B2), makes the 43
   named prior survivors a mechanical regression leg, and updates rather than re-derives the
   quantifier tables — with a fresh-frame safeguard.
4. (a) as written never tests the inter-wave seam. RC2.5 adds the merged-build all-8-suite
   gate, which also proves the packet's global-mypy-zero exit is REACHABLE before any builder
   is briefed.
5. (b) is right but mis-weighted: the coverage direction (ruled requirement → live pin) is the
   high-yield half; pin→clause runs at group granularity. RC3 also gives (b) two jobs the
   proposal missed: sampling the struck author mutation receipts back into evidence, and
   discharging the authorization-condition debt.
6. (c) is made checkable: a keyed scenario battery derived from the ruled teaching
   obligations, three clients (the operator's named population: one Sonnet, one Opus, one
   Fable), graded against keys authored BEFORE any client runs, with GATE semantics defined by
   failure class. RC4.

---

## RC2 — Leg A: the blind-reference re-grade (two agents, one per wave)

### RC2.1 The canon — what the blind builder may read

The reference build is constructed from the CANON and nothing else:

- `docs/plans/v2/03b-comms-message-surface.md` (packet, amendments 1–10, adversary-wave
  rulings, scope grant, standing authorization);
- `docs/plans/v2/03b-comms-surface-design-rulings.md` (S1–S8 complete, incl. the S8
  escalation rulings — note `_annotate_trace` IS named in S8-E2, so the enrichment-helper
  symbol is canon, not a contract invention);
- `docs/plans/v2/03a-2-consume-path-design-rulings.md` (rows 1–11 + the render law);
- `docs/plans/v2/comms-subsystem.md` + DESIGN-LAW cited sections +
  `docs/reference/surrealdb-31-capabilities.md` (store law, first read, per standing law);
- **the vocabulary extract** — a lead-prepared data file listing the classified template
  literals and markers (the `_REGISTERED`/`_PROMISE_FREE` string sets) verbatim. Rationale:
  S4 ratifies "the committed classified vocabulary" as law but quotes only most of it; the
  broadcast variant, the `(+{more} more)` cap variant and the unknown-seq teach exist
  byte-exactly only in the registry file. The extract is the law's appendix, prepared
  MECHANICALLY by the lead (template/marker strings only — no fixtures, no drivers, no
  assertions), so blindness to everything overfit can live in is preserved;
- this document (RC5's ratifications);
- the production tree at `6bfe820`.

**Explicitly withheld until the freeze receipt exists:** the eight contract/test files, the
five author reports, the two prior adversary reports, and ALL SIX existing scratch trees
(`scratch-03b-refbuild`, `scratch/surface03bfix`, `scratch/ct-telemetry-fix`,
`scratch/lore-refbuild-03b`, `scratch/adv03b`, `scratch/adv-telemetry-03b`). The author
scratch trees are the authors' own reference builds — the exact frame under test; the prior
adversary trees carry contract-fitted choices (the telemetry one demonstrably violated three
rulings). The lead should name all six as do-not-open in the briefs; the agents' tool-honesty
sections are the receipt.

### RC2.2 Mechanics and receipts

1. Fresh `scripts/scratch_copy.sh` tree; provenance printed (standing law).
2. Build the wave's reference FROM THE CANON. Surface agent: S4/S5 + D9's two wirings
   (`CommsConfig.drain_limit`, `AppContext.message_ledger` — canon via the packet's amendment
   record). Telemetry agent: rows F/G + the S7 ladder + the S8-E2 call-site raise + RC5.2's
   register/heartbeat annotation + a minimal drain IF the surface build is not yet available
   (the merge in RC2.5 supersedes it).
3. **Freeze:** sha256 over the build's production diff, written into the report BEFORE any
   contract file is opened. The report carries the blindness receipt line:
   *"contract files first opened after freeze `<sha256>`"*.
4. Only then: open the contracts, run the wave's suites against the frozen build.
   Surface owns {`test_comms_tool.py`, `test_comms_promise_registry.py`,
   `test_message_ledger.py`}; telemetry owns {`test_trace_telemetry.py`,
   `test_surreal_schema.py`, `test_surreal_store.py`, `test_surreal_fakes.py`,
   `test_mcp_server.py`}. (That is the full 8-suite scope of the lead's 367/1234/12 baseline,
   partitioned; `_surreal_harness.py`'s Part-B docstring repair rides the telemetry bucket.)
5. Every RED against the frozen build enters the adjudication queue (RC2.3). The build may be
   amended ONLY after the red is adjudicated — never to silently chase green (an unadjudicated
   build amendment is the author's overfit re-created by the grader).

### RC2.3 Adjudication of reds — the four-way taxonomy, and who rules

A pin RED against a rulings-faithful build is exactly one of:

| category | meaning | disposition |
|---|---|---|
| **(i) pin defect** — the pin enforces the author-build's incidental choice, not any ruling (the D1 class) | reference-overfit confirmed | Fix requires editing a frozen committed assertion, and removing/loosening an assertion is a WEAKENING ⇒ **operator authorization, per item** (batched per RC10-F2), each with a mutation proof of what the corrected pin still catches. |
| **(ii) ruling ambiguity** — two faithful readings of a ruling sentence produce different code | spec defect, not a judgment call (standing law) | **Sidecar rules the reading** (this office), in writing, and the pin or the build conforms. Same channel as D2/E2. |
| **(iii) reference defect** — the blind builder misread or missed a ruling | the pin is right | Builder amends the build, cites the ruling clause, re-runs. Logged; three or more category-(iii) reds from one ruling section = a legibility flag on that section (route to (ii)). |
| **(iv) ruling defect** — the ruling as written is unsatisfiable or a false gate (the D3 class) | design defect in this office's own law | **Sidecar re-rules with receipts** — the D3 discipline is binding: EXECUTE the check before conceding or insisting; the concession is written into the rulings doc in place. |

**Positive-control obligation (P0, binding):** before any red is adjudicated category (i), the
adversary must show the same pin GREEN on a minimally-adjusted build that adopts the
contract's reading — proving the red is a divergence of reading, not a builder error. A red
with no such control is category (iii) by default.

**Adjudicator:** this sidecar, receipts-first, with two hard outs: any adjudication that
weakens a committed assertion goes to the operator (always), and any party may appeal any
adjudication to the operator. The conflict of interest (this office authored the rulings it
may have to adjudicate against) is real and is answered the way D3 answered it: by executed
receipts, not by authority — and by the operator's appeal channel.

**Honest limits of this leg, stated so nobody over-trusts it:** the blind build discriminates
overfit only where faithful builders DIVERGE. Overfit on a choice every reasonable builder
makes identically stays green (bounded by RC3's traceability), and under-pinning is invisible
to satisfiability entirely (bounded by RC2.4's delta-P1 and RC3's coverage direction). The
three legs are a set; none is sufficient alone.

### RC2.4 The battery — delta-focused, with a mechanical regression leg

1. **Fresh doors FIRST, on the B2 delta** (the 28 surface fix-wave pins + R5-outcome-2; the 12
   telemetry fix-wave pins + 2 strengthenings + 7 cross-suite amendments + the 8th edit).
   Minimum ≥10 fresh wrong builds per wave, invented BEFORE opening any prior report — the
   P6b two-stage discipline applied to frontier generation, so the prior W/MP lists do not
   re-install the old frontier. History says this is where the yield is: every fix wave in
   this repo's record has shipped at least one new hole (amendment R3 closed the `acked_at`
   axis and left the grade axis open → W41; the telemetry fix author self-caught a false gate
   in its own MP7 mid-wave). Known candidate doors the adversaries may start from but must not
   stop at: send/ack/brief_*/fleet annotation coverage (S7 item 2 says "every comms row" —
   only register/heartbeat/drain are pinned); the fix-wave pins' own fixture monocultures
   (P2-perturb them); the 12 skips' skip-reasons.
2. **Then the regression leg:** open the prior adversary reports and re-EXECUTE all 43 named
   survivors (32 surface W-builds + 11 telemetry WBs — each is a single (old,new) replacement,
   reconstructible from the reports by design) against the current frozen corpus. Every one
   must now go RED at a named pin. Also re-execute a sample of the previously-CAUGHT doors
   (≥5 per wave) to prove no fix wave un-killed one.
3. **Quantifier table, updated not re-derived:** start from the prior adversary's P1b table
   (that frame is the adversarial frame, not the author's — inheriting it does not inherit
   the author's blind spot), re-classify every row a fix wave touched, and ADD rows for every
   invariant the delta introduced. Every GUARDED row carries a door receipt, per the role spec.
4. **P2 perturbation on the delta's load-bearing fixtures**, both legs (perturbed-green-on-
   correct + red-on-wrong), per the role spec.
5. **RED-honesty of the final baseline:** re-derive the lead's 367/1234/12 (never inherit it),
   then classify all failures in the wave's bucket by exception type + message into buckets;
   every bucket gets a verdict; any collection error, fixture error, or failure not
   attributable to a genuinely-absent production symbol is a finding.

### RC2.5 The merged gate — the leg nobody has ever run

After both blind builds freeze and their reds are adjudicated: **merge the two blind builds**
(they collide essentially at `server.py`'s dispatcher and the drain handler — the collision IS
the test) and run **all eight suites against the one merged build**. Requirements:

- Expected result: `(1234 + 367) passed / 0 failed / 12 skipped` — the graders re-derive the
  expectation from their own baseline runs; the struck author receipts (1162, 1022) serve one
  last honest purpose as PREDICTIONS to reconcile against, and any discrepancy is investigated,
  not absorbed.
- The C-DEF harder leg on the merged build: `ruff` clean and `./scripts/typecheck.sh` at
  **global mypy-ZERO** — this is the first demonstration that 03b's owned exit criterion is
  reachable at all (the record already proved neither wave alone pays it:
  REPORT-contract-surface-03b-fix §5).
- The timing/concurrency-class pins get the 20-consecutive discipline on the merged build
  (repo law: a single green never clears a concurrency test): the 8-way seq mint, the MP3
  400-session lifetime pair, the cancellation pair, the latency fast/slow pair.
- The 12 skips are audited: each skip reason re-verified live at `6bfe820` ([fake]-leg-only
  expected per the INDEX; a skip whose reason has silently changed is a finding).
- Merge conflicts between the two builds (one function, two contracts' demands) are FINDINGS
  in their own right — they are inter-wave contract contradictions, the C-DEF class at the
  packet scale, and exactly what this gate exists to surface before a builder hits them.

Environment: spike-surreal `ws://127.0.0.1:18000` only; `:18500` is production and is never
pointed at (standing law).

---

## RC3 — Leg B: the traceability + receipt-sampling audit (one agent, distinct frame)

A separate fresh grader (not either adversary — different frame: structural, not empirical),
with everything as input (rulings, packet, reports, contracts). Four deliverables:

1. **The requirement register (the high-yield direction):** enumerate every ruled requirement
   — S1–S8 sub-clauses, both delta tables (A–I; 03a-2 rows 1–11), amendments 1–10, the
   adversary-wave rulings (WB9/E3-revisited/MP9/R5-outcome-2), MP1–MP11, B1/B2 + C1–C9 +
   M1–M8 + m1–m6, the render law's clauses, and the standing teaching obligations — one row
   each (~120 rows), mapped to the LIVE pin(s) that enforce it, verdict per row:
   live / partial / missing. The mapping is re-derived from the pins themselves — the
   reports' MP→pin and W→pin tables are author claims and are verified, never relayed (P4).
   Every "missing" row is a finding.
2. **Pin-group → clause traceability (the reverse direction), at test-class granularity:**
   every test class in the B2 delta traces to the ruling/finding it enforces; any class
   tracing only to an author report's un-ratified choice is flagged into RC5's ratification
   channel. Spot drill-down to pin level where a class mixes provenances.
3. **Receipt sampling — struck receipts re-earned by independent re-execution:** re-run ALL
   author mutation claims guarding BLOCKER-class invariants (the B1/B2 no-op-fix pins, MP1's
   seq-int flip, MP3's interlock pair, the D1 gate's self-attack) plus ≥1 randomly-chosen row
   from EVERY author battery (the 17, the 5, the 8, the 34, the telemetry-fix table, the D10
   door proofs) — the verification law's "one random receipt re-run per batch", scaled to the
   suspicion. Each re-run: apply the described mutation to the merged reference, confirm RED
   at the named pin, restore.
4. **Authorization-condition discharge table:** every operator authorization in this packet
   carried conditions ("strengthen-only", "mutation-proven before landing", "the
   contract-adversary's P2 confirms the fix wave"). One row per authorized amendment: the
   condition, who discharged it, with what instrument. Conditions discharged only by the
   amendment's own author are marked OPEN and closed by this leg's re-execution or leg A's
   P2. This is the formal answer to the operator's charge: the debt is named per item and
   paid per item.

---

## RC4 — Leg C: the client-acceptance instrument (Q3 answered exactly)

**Premise made testable:** DESIGN-LAW §1.5 and every S-ruling assume the render is where the
LLM learns the contract. No pass in this packet's history has ever tested pedagogy — the
adversaries graded discrimination, not teachability. The operator's directive makes this a
first-class gate.

### Shape

- **Three clients, one per named consumer model: one Sonnet, one Opus, one Fable** — the
  operator's verbatim client population. Independent contexts, no shared state, fresh agents
  that have never touched 03b. Their context is REPRESENTATIVE of a real fleet agent, not
  sterile: brief-base + the served tool description + the served `_INSTRUCTIONS` comms
  paragraph (both captured from the merged reference build). Withheld: the rulings docs, the
  packet, the contracts, the seven reports, this document.
- **Inputs:** staged transcripts generated by driving the FROZEN merged reference build
  through scripted flows via the real dispatcher, capturing served strings verbatim. The
  transcripts are committed as fixtures beside the battery.
- **Task per stage:** *"You are agent `<name>` in session `<s>`. Here is what `lore_comms`
  just returned. State your next comms action(s) as exact tool calls, and one sentence of
  why."* Free-text confusion notes invited after each stage.

### The keyed battery (~12 scenarios, each keyed to a ruled teaching obligation)

| # | scenario | key source | pass = the client… |
|---|---|---|---|
| 1 | drain serves `ACK REQUIRED: #71 — lore_comms action=ack seqs=[71]` | S4.2 trailer; C3's runnable-command litmus | issues that ack (seqs=[71]), acks nothing else, does not treat ack as a reply |
| 2 | elision `+5 more unread — re-run with limit=5` | S4.2 elision arithmetic | re-runs drain with limit=5; knows the shown rows will NOT re-serve |
| 3 | `peeked 2 of 7 pending — nothing stamped…` | S4.2 peek header; S5 | knows the rows are still unread; re-runs without peek to consume |
| 4 | own question sent; teach line served; client drafts a self-note on the thread | S4.1 question teach; 03a2-R2 | knows its own send never clears the debt |
| 5 | two questions batched on ONE thread; one partial reply arrives | S5 thread-debt; 03a2-R5 | knows the thread debt cleared; RE-ASKS on that thread |
| 6 | client must ask two unrelated questions | S5 one-thread-one-debt | uses two threads |
| 7 | client must notify the whole fleet | S5 `to=[]` | broadcasts with `to=[]` |
| 8 | client has a 5000-char payload | S5 body cap | writes a report/finding, passes refs, body under cap |
| 9 | re-served acked row + `ALREADY ACKED: #82 — no action owed` | S4.2 trailer; 03a2-R6 | takes no action on #82 |
| 10 | ack result carries the unknown-seq teach | S4.3 | recovers per the taught text, does not blind-retry |
| 11 | `not addressed to you: #9 — …no delivery to {name}` | S4.3 | does not retry discharging another agent's mail |
| 12 | rows with ` (task T-9)` vs ` (thread q:cap)` vs bare cells | S4.2 context cell; D2 | attributes each row to the right conversation and replies on the right thread |

Scenarios deliberately include the ERROR/edge renders (10, 11) — agents meet those alone, with
no human to ask. **The keys are authored by the lead FROM THE RULINGS and reviewed by this
sidecar BEFORE any client runs** — so the key cannot be fitted to responses.

### Gate semantics (the operator's "satisfied" made checkable)

- A keyed-scenario failure is confirmed by ONE clean-context re-run (2-of-2 fail = finding;
  1-of-2 = flagged flaky-advisory). A failure by ANY of the three models is a finding — the
  operator named all three as the client; "the other two passed" is not clearance.
- Findings classify: **(F1)** the client acted against, or failed to perform, something a
  RULED teach claims to teach → **GATE**: the contract phase does not close while any F1 is
  unadjudicated. Adjudication (this sidecar): amend the teach/render (design ruling →
  contract amendment through the normal authorization channel) | accept as a named bound with
  a re-open trigger. **(F2)** confusion on something the rulings deliberately DEFER (e.g. the
  per-row question marker → packet 05, Residual 1) → routed to the owning packet's entry
  check; re-opening 03b scope for it is an operator fork. **(F3)** idiosyncratic model error
  not attributable to any specific render ambiguity → advisory, recorded.
- **The battery + keys + transcripts are COMMITTED as a reusable eval** (a script under the
  repo, not prose in a report), so packets 04/05/06 re-run it on their render additions — the
  instrument outlives the packet, per the ship-the-instrument-with-the-law rule.

### Ordering note

(C) consumes the merged reference build, so it runs after RC2.5's build exists. If an F1
adjudication amends a render, the amendment re-runs the affected RC2 slice (mechanical) and
the affected scenarios. Expected one round; a second full round = escalate to the operator
(two-wave tell).

---

## RC5 — Q2: what retains authority, and three ruling-level adjudications

**The S/D/E rulings retain authority** (bucket B4, RC0): their provenance is design sources +
the sidecar's own executed probes, not the contract; the two independent adversaries
corroborated the load-bearing measured facts (S7 rung re-derived with a stronger instrument)
and, where a ruling was defective, found it (WB9) — and the office conceded with receipts
(D3, WB9). That is insulation by verification, not by trust. Three narrow items:

1. **RC5.1 — S4's ratification of "the committed vocabulary" is retained,** with the note
   that the vocabulary's byte-exact text lives partly in the registry file; RC2.1's extract
   is the operational consequence. No re-derivation.
2. **RC5.2 — RULED NOW (this office's S7 stewardship): register and heartbeat annotation is
   REQUIRED, in scope.** The telemetry fix wave pinned it (MP4) on the author's reading of S7
   item 2 with an explicit "if the operator rules it out-of-scope, drop the pin" — left
   unruled until now. Ruling: S7 item 2's join ("the register-first spawn protocol means a
   fleet agent's FIRST lore call binds its key") is TRUE only if `register` itself annotates
   — `register` has `requires_registration=False` and does not ride the dispatcher's
   touch-annotate branch, so without the explicit `_annotate_trace(agent=…, session=…)` in
   `_comms_register`, a non-draining agent is permanently unattributable and the S7 join
   claim is served prose over a dead mechanism. The MP4 pins are the enforcement; the blind
   telemetry reference MUST implement it (RC2.2 item 2). Corollary noted for leg A's
   delta-P1: S7 item 2 says "every comms row" — send/ack/brief_*/fleet annotation is
   currently UNPINNED; whether to pin in 03b or ledger it with a trigger is an expected
   RC2.4 finding, adjudicated when concrete.
3. **RC5.3 — two stale prose items in the rulings doc, flagged not re-ruled:** Residual 8's
   mypy claim is measured-false twice over (adversary R2; fix-wave §5: the true split is
   90-structural/6-cross-wave at that wave's HEAD) — the correction lands as a one-line doc
   amendment at close-out, citing those receipts; and S3 part 1's marker table describes the
   pre-amendment-7 elision marker — superseded by the committed prose-disjointness meta-test,
   note only. Neither is a ruling re-derivation.

**No S/D/E ruling is ordered re-derived.**

---

## RC6 — Q4: disposition of the self-certified receipts

**Struck as certification; preserved as history and as reproduction recipes.** Precision
matters in both directions:

- The strike applies to the FIVE author reports (`REPORT-contract-surface-03b`, `-03b-2`,
  `-03b-fix`, `REPORT-contract-telemetry-03b`, `-03b-fix`) and ONLY to their certification
  claims (satisfiability counts, mutation tables, "done" states). Their escalations and
  findings (D1–D10, E1–E4, Part B) are real evidence regardless of who certified — D1 was
  found BY an author build. Over-striking would destroy genuine record.
- The TWO adversary reports are independent grades and get **no strike** — they are the
  strongest evidence in the packet.
- **Marking (lead executes at archive time, per the archive-with-header law):** each of the
  five author reports gains this header line when `git mv`'d into
  `docs/plans/v2/receipts/2026-07-24-packet03b/`:

  > ⚠ RECEIPTS STRUCK AS CERTIFICATION (operator ruling 2026-07-24): the satisfiability and
  > mutation receipts in this report were produced by the contract's author against its own
  > reference build — builder≠grader violated at the certification layer, and no adversary
  > re-graded the wave this report certifies. Retained as history and reproduction recipes;
  > findings/escalations herein remain evidence. Certification of record:
  > DESIGN-03b-recertification.md (this directory) + the recert reports named in the INDEX Log.

- One INDEX Log line records the strike and the re-certification's start.
- The struck counts keep exactly one legitimate use: RC2.5's reconciliation predictions.

---

## RC7 — Q5: is re-certification anywhere WEAKER than re-authorship?

**No rewrite is ordered.** Reasoning: the corpus's independently-verified strengths are real
and substantial (both adversaries' "what I could not break" sections; the context-cell family;
the coverage-as-checked-variable pins; the #107 dirty-store pin the telemetry adversary called
the best in the file) — re-authorship would discard verified strength to re-buy unverified
strength, which is strictly worse than grading the delta. The suspect layer (B2) is four
commits with named, bounded content; grading it is cheaper and stronger than rewriting it.

**But the re-authorship trigger is NAMED now, so it is met deliberately** (two-wave
escalation law): if leg A on a wave's delta produces **(i)** ≥3 confirmed category-(i)
reference-overfit pins in one suite, or **(ii)** fresh-door survival >25% on that delta, or
**(iii)** ANY surviving no-op-fix-shaped door (the B1/B2 class) — then that wave's fix-wave
layer is re-authored by a fresh contract author under the standard adversary cycle, not
patched a third time. That decision is an operator fork (RC10-F3) with this trigger as the
recommendation.

---

## RC8 — Q6: what the lead's proposal missed (consolidated)

1. **The merged-build all-8-suite gate** (RC2.5) — the inter-wave seam has never been
   co-satisfied; also the only pre-builder proof that global mypy-zero is reachable.
2. **The vocabulary-extract problem** (RC2.1) — without it, contract-blindness manufactures
   false over-pin findings on every template ruled by reference.
3. **The four-way adjudication taxonomy** (RC2.3) — reference defects and ruling defects are
   both measured realities in this packet's own record.
4. **The authorization-condition debt** (RC3.4) — conditions on operator grants that were
   discharged only by their own beneficiaries, now named and paid per item.
5. **Fresh-frame protection for delta-P1** (RC2.4.1) — invent doors before opening the prior
   W/MP lists, or the re-grade inherits the old frontier.
6. **The survivor-regression leg as a mechanical, named deliverable** (RC2.4.2) — all 43
   prior survivors re-executed, plus a no-un-kill sample of previously-caught doors.
7. **Freeze discipline:** from re-cert start, the eight suites are frozen at `6bfe820`; any
   edit voids the affected leg and restarts it. The record shows "the contract now FREEZES"
   has been declared twice and followed by four more waves — this time the freeze is the
   protocol's precondition, not its epilogue.
8. **The consolidated builder-obligations register:** the seven reports carry load-bearing
   builder obligations that are about to be archived (D9's two wirings; E1/E2/E3; R8's fake
   update; the E4/R10 sequencing coupling — rows C/D and F/G/H must land under one builder
   brief or in a ruled order; the mypy cross-wave truth; the prose corpses of
   REPORT-adversary-telemetry-03b §6.2 which the builder must retire; the stale
   `test_retry_seam.py` comment; the two store-reference facts from
   REPORT-contract-telemetry-03b §7.1 — landed at `7f23223`, verify). The lead assembles ONE
   register (each row source-cited); leg B verifies its completeness against the reports.
   This is the #152/#153 lesson applied prospectively.
9. **The 12 skips audited** (RC2.5) — skipped pins are ungraded surface.
10. **Quarantine of the six existing scratch trees** (RC2.1) — the author trees are the frame
    under test; blind builders must not seed from any of them.

---

## RC9 — Ordering, roster, expected volumes

**Order:** Phase 0 (lead): freeze declaration · vocabulary extract · scratch quarantine ·
obligations register draft. Phase 1 (parallel): leg A surface + leg A telemetry (blind builds
→ freeze → satisfiability → adjudication queue) ‖ leg B. Phase 2: adjudications + any
authorized amendments → merged gate (RC2.5). Phase 3: leg C off the merged build → F1
adjudications (loop bound: one round). Phase 4: close-out — final merged gate re-run if
anything amended, obligations register finalized, receipts marked + archived, INDEX row/Log.

**Roster (never reuse prior names):** `adversary-recert-surface-03b`,
`adversary-recert-telemetry-03b` (both per the contract-adversary role spec + this doc's
deltas, Opus), `tracer-03b` (leg B, Opus), `client-sonnet-03b` / `client-opus-03b` /
`client-fable-03b`. Six agents + at most one amendment author (fresh name) if RC7's trigger
does not fire.

**Expected adjudication volume, pre-declared so nobody panics or over-trusts:** 5–20 reds per
blind build, mostly name/value bindings; if reds exceed ~40 on either wave, the canon was cut
too narrow — pause, re-cut the canon (a protocol-level control), do not grind adjudications.

---

## RC10 — Forks for the operator (recommendations attached, decisions not mine)

- **F1 — spend:** six to seven agents plus a possible amendment wave. Recommend: approve; the
  packet gates a deploy to BOTH containers and the alternative is trusting B2 ungraded.
- **F2 — the weakening channel:** confirmed category-(i) overfit pins require editing frozen
  committed assertions (weakenings — outside every standing grant). Recommend: adjudicated
  items travel as ONE batched authorization request, per-item mutation proofs attached,
  operator rules item-by-item in one sitting.
- **F3 — re-authorship trigger** (RC7): if tripped, recommend re-authorship over a third
  patch wave, per the two-wave law.
- **F4 — leg C scope-expanding findings** (F2-class): recommend routing to the owning
  packet's entry check (05/06) rather than re-opening 03b, unless the finding shows a 03b
  render actively TEACHES WRONG (that is F1, gated here).
- **F5 — the receipts marking** (RC6): executing the strike headers is recommended as
  lead-executed under the operator's existing suspect declaration; flagged here in case the
  operator wants to word the marking personally.

---

## Residuals & tool honesty

- Residual 1: this document adjudicates process for packet 03b only; whether the
  builder≠grader-at-certification rule becomes standing law for future packets (i.e. the
  C-DEF satisfiability instrument is ALWAYS the adversary's build, with author builds
  demoted to pre-flight) is a CLAUDE.md-level process amendment — operator's, recommended,
  not ruled here.
- Residual 2: leg C's battery, once committed, should be named in packet 04/06's entry
  checks by the lead (a deferral with no named consumer is a can-kick).
- Residual 3: the lead's 367/1234/12 baseline is treated as measured per the brief; RC2.4.5
  orders its independent re-derivation anyway (re-derive every number you inherit — including
  this one).

**Tool honesty:** every file read was point-read from brief-supplied paths; no code-structure
search was needed, so lore was not consulted (nothing here depends on index freshness). Three
read-only probes were run and are cited where used: `git log --oneline 0223291..6bfe820`
(the commit bucketing in RC0), `grep -rn "_annotate_trace" docs/` (the S8-E2 canon fact in
RC2.1 — a non-symbol textual seam, the honest-grep category), and `ls` over the receipts
directory + repo root (RC6's marking mechanics). No suites were run (brief constraint). No
lore friction encountered; nothing filed.
