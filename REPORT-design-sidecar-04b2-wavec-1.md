# REPORT-design-sidecar-04b2-wavec-1 — wave-C design rulings: the split · ESC-5's mechanism · #268's instrument

brief-base v9 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** (all three rulings issued in-reply to `lead-04b2-wavec`, 2026-08-01; this
  file is their durable record) — **agent remains STANDING BY for follow-ups**; its
  idle-between-questions state is benign per standing law.
- deviations: (1) spawn brief said "no design doc unless asked"; the idle-gate hook —
  keyed on this exact filename — demanded the artifact, and brief-base §1's measured
  reply-loss receipts back it, so the file exists and the deviation is disclosed here and
  in-reply. (2) `ugrep` absent in my shell; textual sweeps ran `grep`, all on non-symbol
  seams (grep's honest territory).
- Packages considered: none — no mechanism specified beyond those already ruled
  (`networkx`/`graphlib` routed by predecessor §B4; the footer seam ruled §B5).
- decisions-needed: none for the lead; three ⚠ OPERATOR-REVIEWABLE items in §4.
- receipt pointers: §1 the split · §2 ESC-5's mechanism + the (b)-elimination derivation ·
  §3 the #268 instrument · §4 operator-reviewable · findings #300/#301 (the forks, filed by
  `contract-04b2-wavec-1`) · `REPORT-contract-04b2-wavec-1.md` (the escalation this rules
  on; archive both under `docs/plans/v2/receipts/` at wave close-out).

**Authority:** operator-delegated design authority (same delegation as
`receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md`). These are RULINGS.
Written 2026-08-01 against `feat/surreal-unification` @ `04ede45`. Where a number is cited
it is the contract author's derivation (their report, section named) or my own live read —
labelled which, throughout.

---

# §1 · RULING 1 — THE SPLIT: C1 + C3 ship THIS wave; C2 → 04b-3 wholesale

**Adopted:** the contract author's three-contract boundary (their §1.4). **Wave
assignment:** C1 (ESC-5 · the chain render · R10(iii) · #268 · **plus #302's exact-equality
pin over `_TASK_ACTIONS`/`_FINDING_ACTIONS`/`_COMMS_ACTIONS`** — cheapest while C1 mints
the new action) and C3 (footer per predecessor §B5 · `agent`/`session` params ·
`_INSTRUCTIONS` · #219's four prose sites · R-5 · R-12) ship in THIS wave — **two
contracts, one author, written sequentially** (worktrees banned #134; shared-tree hazard),
**each contract gets its own adversary pass before its builder** (the 2026-07-28 no-skip
law). #279 rides the build phase per predecessor §B3, untouched. **The deploy is the wave
EXIT after BOTH**, behind predecessor §B6's gate unchanged (+#253-verify, +#260 at the
recreate). **C2 (R4 columns + S1-a + S2) moves to 04b-3 as one unit**, S1-a's
with-or-before-columns ordering preserved inside 04b-3.

**This explicitly NARROWS predecessor §B1 Level 2** (one consolidated wave over nine
items): (1) one wave, two contracts; (2) the fleet surface leaves the wave. Reason: the
predecessor consolidated without the sizing measurement; the author then derived it —
`TaskLedger.transitive_blockers` has 0 prod / 0 test consumers (their `lore_impact` +
ugrep, report §1.1), so the critical-path render MINTS a served surface, a contract of
`test_blocks_edge.py` order — and the whole-surface satisfiability receipt is one the
author cannot honestly produce (the C-DEF class, #133). The operator-ruled SIZING FENCE
("the split is the ruled default") is the more specific law once that measurement exists.

**Why C2 leaves — the deploy-critical test:** deploy-critical means *the deploy is
defective without it*. The only strict entry condition ever ruled is ESC-5 (predecessor
§B6). Deferring C2 leaves `AppContext._render_comms_fleet` untouched at HEAD, so the
deploy serves the fleet surface production serves today — no NEW false clear opens.
Contrast ESC-5, where the deploy itself first exposes the defective surface. Cost accepted
knowingly: **S2's `⚠ STALE` badge (ruled-wrong over-claim) keeps serving until 04b-3** —
§4 item 1. Pulling S2 alone into this wave was considered and rejected: it edits the same
row-render R4's columns edit (re-cutting the seam the C2 boundary exists not to cut
twice), and render changes in this repo are never a-few-lines-cheap.

**Granted in writing:** the satisfiability receipt is **scoped per-contract** — each
contract's receipt covers its own slice plus the pre-existing suites its seams touch,
including #133's harder post-ruff leg.

**Falsifier:** if `_comms_footer` proves to require editing `_render_comms_fleet` itself
(the author measured it touches the three dispatchers' exits only), the C2/C3 boundary
bleeds — STOP and return, never silently widen.

---

# §2 · RULING 2 — ESC-5's MECHANISM: (c) over-fetch by one; (b) is ELIMINATED, not a fallback

**Ruled: (c).** The disclosure line exists **iff a further matching row truly exists**.
Statement path (`blocked is None`): purchased by `LIMIT cap+1` — one extra ROW on the same
read, no second round trip. Blocked path: free — `query_tasks` already materialises
`selected` in full; the fact is `len(selected) > cap`. Grammar is **existence, not
quantity**, uniform across both filter paths. No count is ever served on a caller-limited
listing.

**The decisive derivation — (b) does not close ESC-5 at all:**
`TestACappedListingDISCLOSESNothingAboutItsOwnBOUND` deletes only when the two worlds'
bytes DIFFER. Under (b), "there may be more" is emitted whenever the window is full — and
in the complete world (population exactly `_ANSWER_CAP`, limit `_ANSWER_CAP`) the window
is ALSO full, so both worlds still render byte-identically, the pin stays green, and the
bound is not closed. Conditioning (b)'s emission on actual surplus IS (c) with vaguer
prose. (a) buys a `count()` second read on the served path — the axis two rulings already
rejected — plus §11.1's failed-count-renders-`0` forgery debt. **(c) is the unique
mechanism that closes ESC-5 without the second read**, and it carries the strongest Leg-2
property: bytes differ exactly when the worlds differ, both directions. The line's ABSENCE
is a derived TRUE completeness claim (absence-with-rows always means a completed read —
a failed read throws loud first, T2), which is fact-shaped, not the OVERRULE-2(a)
disclaimer shape.

**#301's docstring contradiction, resolved — one policy, two epistemic states:** the
disclosure serves **what the responder actually KNOWS**. Caller-limited listing → responder
holds an existence bit → (c)'s grammar (docstring sentence 1). Display-cap elision over a
FULLY MATERIALISED set → responder holds the real surplus → R9's counted grammar
`+K more — re-run with limit=N`, **with K DERIVED from `len(materialised) − shown` —
the docstring's "fed by a store-side count" clause is OVERRULED; no `count()` read exists
anywhere in this design.** Not two grammars for one property: the form is a function of
the caller's own visible input (did I pass `limit`?), never hidden internals. Conditional:
if the current task render has no display cap, no counted line is owed this wave — the
contract author verifies which world `server.py` is in. **Named trigger:** if a future
packet bounds the no-limit read, the counted line degrades to the existence grammar in the
SAME edit.

**Placement — the ledger serves the fact as a TYPED field:** `query_tasks` returns a small
typed result (rows + `more: bool`; author names it). The blocked path already holds the
fact; renders take typed applicability and never re-compute (house law); the plain-list
pin `TestNoTOTALIsServedThatWasNotMEASURED` anticipated exactly this deletion path, and a
number-free wrapper acquires NO §11.1 failed-count construction (the bit rides the same
read as the rows — no separate failure state to forge; state that derivation where the pin
was). **Pre-authorised fallback, trigger named:** if the reference build shows the type
change rippling disproportionately, seam-side `limit+1` behind ONE shared helper (plain-
list pin then stays green verbatim) — reported as a deviation, never adopted silently.

**Riders C1 must carry (same breath as the ruling):**
1. The bound class DELETES per its own instruction, with the wave-report sentence it
   demands. Successor pin: partial world renders the line, complete world does not,
   normalised bytes differ in exactly the line — both directions.
2. A blocked-path two-world leg — the sandwich fixture yields it free (true answer 6,
   `limit=_ANSWER_CAP=5` ⇒ line; `generous_cap` ⇒ no line).
3. `more` mutation-proven BOTH ways (force-True / force-False), declared-RED sets from
   `--collect-only` (#194/#196).
4. Exact-field-set pin on the wrapper (rows, more — nothing else, deny-by-default),
   docstring: *adding any count field acquires §11.1's failed-count construction first*.
5. Pin the EMITTED statement: `LIMIT` bound to cap+1, served rows ≤ cap; `limit=None`
   still emits NO LIMIT (the `$k = NONE` hazard guard survives) and serves NO line —
   pinned, or the line becomes noise on complete answers.
6. `test_the_LIMIT_bounds_the_ROWS_READ…` survives verbatim (growth comparison; cap+1 is
   constant at both sizes). Any pin asserting the bound limit EQUALS the caller's value is
   re-authored citing this ruling.
7. Run `scripts/forgery_door_sweep.py` — confirm no interaction with the #274
   statement-shape family (expected none: it guards the backfill's no-LIMIT reads).
   Verify, don't assume.

**Falsifier:** a measured `LIMIT k+1` engine misbehaviour (store reference documents none;
its only LIMIT hazard is the NONE binding, guarded), or #274's family proving to pin
query-path LIMIT values — then the re-authoring is deliberate and cited.

---

# §3 · RULING 3 — #268: option (ii) CONFIRMED, instrument tightened to the comparative form

**The lead's composition argument survives attack:** SIDECAR CAUTION C1 bans
`rows-read ≤ f(limit)` because an UPPER bound would forbid the correct build's
deliberately-unbounded scan. An exhaustion assertion DEMANDS the scan — it pins the very
property C1 protects (`query_tasks`' own docstring carries the same clause). **(ii), not
(i).** (i) remains honest-but-probabilistic, dominated once a deterministic instrument
exists.

**Tightening — not `rows_read == 66`, but the comparative form** (the file's own idiom,
`test_the_LIMIT_bounds_the_ROWS_READ…`):

> `rows_read(status=open, blocked=False, limit=generous_cap)` **==**
> `rows_read(status=open, blocked=False)` — *the cap did not shrink the scan*

with the idiom's non-vacuity guards (`rows > 0`; both answers == `true_answer_size`), on
`measure_store_traffic` (reach already a checked variable — `require_full_reach`, T4).
Why not the constant: the instrument counts rows across the WHOLE transaction (the
`$rows` echo + the blocker read + LET/BEGIN/COMMIT), so the true constant is
derived-from-transaction-shape, reddens on innocent refactors with a message about scan
truncation (the P2 false-gate shape), and a constant transcribed from a run is the #194
tautology wearing a number. The comparative form is self-normalising, deterministic
against #268's named mutation (capped side reads fewer), contains no `f(limit)` at all,
and keeps the existing outcome assertions (`capped == unlimited`, the premise guard).
Mutation re-proof per #229: both declared REDs from `--collect-only`, diffed both ways.

**#268's body correction** (it currently instructs its taker to break the pin;
`lore_findings` cannot edit bodies — #129): at wave close, **resolve #268** with the note
*"closed by the traffic-equality exhaustion leg (sidecar ruling, wave C); the finding's
own CHEAPEST FIX was proven backwards — see #300's derivation; do not implement as
written"* — and **resolve #300 with the same receipt**.

**Falsifier:** `measure_store_traffic` unable to give per-call readings for two separate
invocations without cross-contamination (nothing in the T4 class suggests it) — then the
derived-constant form, derivation shown in the docstring, never transcribed from a run.

---

# §4 · ⚠ OPERATOR-REVIEWABLE (none blocking under the standing delegation)
1. **C2's deferral leaves the `⚠ STALE` badge — ruled-wrong over-claim — serving in
   production until 04b-3 deploys.** Rationale: pre-existing, dated, ruled bound; not a
   lie this deploy mints; extracting S2 alone re-cuts the R4 seam. Want it sooner ⇒ S2
   returns as its own slice, knowingly.
2. **The grammar ruling overrules "fed by a store-side count"** inside a ruled class
   docstring's R9 paraphrase — K is now derived from the materialised set; no `count()`
   read exists. I judge this preserves R9's grammar while pinning its feed to derivation;
   an operator may read it as amending R9.
3. **Predecessor §B1 Level 2 narrowed** (two contracts; fleet surface → 04b-3) on the
   sizing fence + the author's measurement — flagged because it re-scopes a
   same-authority ruling.

---
*Written 2026-08-01 by `design-sidecar-04b2-wavec-1` (Fable, long-running design sidecar)
against `feat/surreal-unification` @ `04ede45`. Grounds: the contract author's report
(measurements theirs, cited by section), predecessor sidecar rulings §B1–B6, packet
§r6/§C1/§04b-2/INHERITED/SWEEP, findings #268/#300/#301/#302 read from the live ledger,
the five named test classes and `TaskLedger.query_tasks`/`_candidate_statement` read
verbatim, and the store reference §2/§3/§6/§7 (read before ruling on statement shape, per
standing law). No git command was run; this file is my only tree write.*
