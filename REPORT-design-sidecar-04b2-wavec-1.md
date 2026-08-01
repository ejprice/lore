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
- decisions-needed: none for the lead; eight ⚠ OPERATOR-REVIEWABLE items in §6.
- receipt pointers: §1 the split · §2 ESC-5's mechanism + the (b)-elimination derivation ·
  §3 the #268 instrument · §4 the gate-definition ruling (thread `q:04b2-gate-definition`,
  on the lead's §L-4 measurement) · §5 the footer-seam rulings (thread `q:04b2-footer-seam`:
  §B5 pin overturned on #305, C-DEF 5 resolved for R8, the resolution architecture ruled) ·
  §6 operator-reviewable · findings #300/#301/#305 (filed by `contract-04b2-wavec-1`) ·
  `REPORT-contract-04b2-wavec-1.md`, `REPORT-lead-04b2-wavec.md` §L-4 and
  `REPORT-refbuild-c3-1.md` (the escalations this rules on; archive all under
  `docs/plans/v2/receipts/` at wave close-out).

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

# §4 · RULING 4 (follow-up, 2026-08-01, thread `q:04b2-gate-definition`) — THE GATE STAYS ABSOLUTE; THE PACKET-39 BOUND BECOMES AN INSTRUMENT, NOT A NARROWING; ZERO PACKET-39 FILES ARE TOUCHED

**The question (lead's §L-4, their measurement):** `./scripts/typecheck.sh` FAILED at HEAD,
102 errors / 11 files merged, every one packet-39 territory, every error `attr-defined` on
symbols that do not exist yet; the full suite additionally carries packet-39's **444
designed-RED pins** (INDEX row: 480 pins / 444 RED / 36 GREEN, *rest of suite 7705
passed / 0 failed*). Predecessor §B6 line 1 ("full gates green") read literally means
04b-2 can never deploy until packet 39 builds — which is BLOCKED on operator decision
#296, indefinitely. The lead declined to narrow the gate and routed the definition here.
⚠ The lead's four candidate readings never arrived (ledger drain empty — a second
channel-loss datum this session); the candidates below are enumerated independently.

**Two ground-truth facts that decide the shape (read this session, `04ede45`+):**
1. The INDEX packet-39 row records **four adversary passes, ALL INSUFFICIENT, and an
   operator override holding the door rather than running a fifth**. Those 11 contract
   files are **operator-held territory pending #296** — any remedy that edits them
   trespasses on an operator fork.
2. The packet-39 close-out line records suite state and `ruff clean` but **never
   adjudicated mypy** — the red typecheck at HEAD is an UNRECORDED bound, silently
   inherited, not a ruled acceptance. (Its contract files import the missing symbols
   function-locally — read at `test_hosted_readonly_posture.py` — so collection survives
   and the 444 are behavioral REDs; only mypy is structurally red.)

**RULED:**
1. **The gate DEFINITION does not move.** "Zero mypy errors including test trees" stays
   absolute law; no config override, no per-line ignores, no testpaths quarantine, no
   redefinition of green. The lead's refusal to narrow is confirmed.
2. **The red state is adjudicated as an ACCEPTED BOUND of the out-of-authority shape**
   (deferral shape 2): the only clean closure — building packet 39, or re-authoring its
   contract to the mypy-clean idiom `test_query_tasks_bounded` documents (`_ids(**filters)`
   pattern) — lives inside operator-held files behind #296. **Named decision point: #296 /
   packet-39 build start.** Per standing law, an accepted bound is PINNED, never prose.
3. **The pin is a GATE WRAPPER + PENDING-CONTRACT REGISTRY, committed under `scripts/`,
   touching ZERO packet-39 files:**
   - a registry file naming: the exempted FILES (the 11), the missing SYMBOLS
     (`loremaster.config.resolve_posture` / `PostureConfigError` / `lorerunes.Posture` /
     `SCOPE_READ`, completed by the builder from the mypy output), the owning packet, and
     the re-open trigger (#296) — a bound stated as FACTS, not a disclaimer;
   - a wrapper that runs the canonical gates and enforces, DENY-BY-DEFAULT: every mypy
     error line must name a registered file AND a registered symbol; every pytest failure
     must lie inside a registered file; anything else ⇒ FAIL loud. Counts served in the
     tail (*"7705+wave passed · 444 pending-build(packet-39/#296) · mypy 0 outside the
     registered set"*) — the §B6 line-1 receipt in its explicit form;
   - **self-destruction:** if a registered file stops erroring/failing (the build
     started), the wrapper REFUSES until the registry entry is deleted with the fix —
     the bound cannot outlive its premise, per the #137/#138 pattern;
   - positive controls owed by its builder: an injected error OUTSIDE the registry must
     fail the wrapper; an injected unregistered-symbol error INSIDE a registered file
     must fail it; a correct-tree run must pass. A probe needs a control.
4. **§B6 line 1 is AMENDED to its explicit form** (same-authority amendment, flagged
   operator-reviewable): *"full gates green under the pending-contract wrapper, with the
   partition counts in the pasted tail."* The lead's interim corollary (every green claim
   scoped-and-said) stays in force until the wrapper lands, and the wrapper is
   **deploy-critical** (the gate is literally unsatisfiable without it), hence
   fence-legal for this wave. Its second consumer is already minted: 04b-3 deploys after
   this and inherits the same red HEAD.
5. **A finding is owed** (lead or wrapper-builder files it): packet-39's close-out never
   adjudicated the mypy-red it left at HEAD — the unrecorded-bound defect this wave
   discovered. Provenance, not blame.

**Candidates REJECTED, each with its reason:** (A) scope-exclude packet-39 from
`typecheck.sh`/`testpaths` — a silent quarantine; ungated instruments are hopes with
filenames, and packet-39's 36 GREEN pins would stop being enforced. (B) literal reading,
deploy blocked until packet 39 builds — transfers the ruled deploy's authority to an
unrelated packet's timeline; a gate that can never be green stops informing anyone and is
already dead in practice (every wave-C agent scopes its greens). (C) per-line
`type: ignore` ×102 or mypy config overrides — line/config-level narrowing that also masks
FUTURE defects in those files, uncounted. (D) re-author packet-39's contract to the
mypy-clean house idiom — the remedy I would otherwise prefer, REJECTED HERE because the
files are operator-held after four INSUFFICIENT adversary passes and will be revised at
build anyway; editing them now trespasses on #296. (E-manual) the lead hand-diffs observed
failures against the packet-39 file list at deploy time — honest once, but a diagnosis is
not an instrument, and 04b-3 re-derives or inherits silently. (F) revert packet-39's
contract commit — overturns a deliberate operator-adjacent commit and makes the contract
invisible to every index and sweep; scope grab, named not taken.

**Falsifiers:** (a) any packet-39 record proving the mypy-red state WAS explicitly
adjudicated with a different mechanism ⇒ defer to it; (b) the wrapper's per-symbol
discrimination proving unbuildable from mypy's output ⇒ fall back to file-exact +
error-code-exact with the residual stated in the registry; (c) #296 resolving before this
wave's deploy ⇒ the registry empties at the build and the wrapper degrades to a
pass-through over the plain gates (keep it — 04b-3 and every future pending contract are
its consumers).

**Bounds on this ruling's own inputs:** the gate measurement is the lead's (§L-4, canonical
runner), not re-run here; I read ONE packet-39 contract file's import shape and the INDEX
row — the wrapper-builder re-derives the full 11-file shape and the symbol set before
committing the registry. Where the lead's four unseen candidates contain a reading not
covered by A–F, the lead should resend it — this ruling is open to a candidate it never saw.

---

# §5 · RULING 5 (follow-up, 2026-08-01, thread `q:04b2-footer-seam`) — THE NEUTRALISATION PIN RETIRES; THE CONTRACT PIN YIELDS TO R8; THE REGISTRY IS THE ONE RESOLUTION SEAM

Grounds read this session: finding #305 (the by-construction measurement) ·
`REPORT-refbuild-c3-1.md` in full (the five C-DEFs, the both-ways C-DEF-5 construction,
§2.2/§3.1b) · packet §RULINGS ROUND 3 R8 verbatim · predecessor §B5.

## 5.1 · Q1 (#305) — §B5's neutralisation pin is OVERTURNED; the closure is provenance, and it is now pinned as a CHAIN

**Predecessor §B5 pin (1) — "a footer-shaped forgery renders NEUTRALISED" — is overturned,
explicitly and with the reason said aloud:** it fails every §B5-compliant build, measured by
construction (#305: `sanitise_line` collapses CONTROL characters and does nothing to
same-line text — the forged instruction survives verbatim, backticks included). §B5 derived
"neutralised" from the row-forgery case (multi-line stored text, where the seam DOES
defang) and stated it over the footer case — DD-3.c's quantifier shape, exactly as the
finding says. A pin that is RED on every correct build is the C-DEF class; it cannot stand.

**#305 option (a) is ADOPTED — with one correction to the finding's own residual claim.**
The finding says a build that *"exact-matches then renders the CALLER'S RAW STRING re-opens
the vector completely."* **Overstated:** after a TRUE exact match, the raw string is
byte-equal to a registered name, and registered names are charset-clean by construction
(`AGENT_NAME_PATTERN` fullmatch at registration — the #210 fix). Raw-echo-after-exact-match
is therefore byte-identical to registry-echo and is NOT a vector. **The real vectors are
(i) a render WITHOUT a successful resolution and (ii) a match that is not exact
(normalised / heuristic / fuzzy).** The load-bearing invariant is a three-link CHAIN, each
link pinned:
1. **Registration enforces the charset** (`fullmatch`, no space/backtick/`=`/newline) —
   already pinned in the comms contract (#210's receipts);
2. **The match is EXACT, never heuristic** — `test_the_fallback_matches_EXACTLY_never_
   heuristically`, which refbuild measured VACUOUS today (C-DEF 1) and which MUST be made
   non-vacuous by the harness repair;
3. **No resolution ⇒ no footer** (unmatched silence) + the positive control that a benign
   REGISTERED identity DOES reach the footer — without which "cannot reach" is satisfied
   by "nothing ever reaches", the exact vacuous state refbuild caught live.
The provenance pin (`…REGISTERED_name_never_the_RAW_caller_string`) STAYS as belt — it
makes the safety argument local — but the contract's docstring must not claim raw-echo-
post-match is exploitable; it is not, and a false threat model mis-spends the next
auditor's attention (a gate needs a threat model).

**§B5's seam CONSTRUCTION stands; its role is demoted from closure to discipline.** The
footer still builds through `render_line`/`Rendered` with the isinstance pin and the
mutation proof — but the mutation proof's declared-RED set is RE-POINTED (the forgery pin
is dead; the swap-to-bare-f-string now reddens the isinstance pin and the template-literal
pin). Rationale for keeping it: uniformity (every served comms line rides one seam — a
bare-f-string footer is a new pattern inviting #102-style cloning), and the runtime
control-char assert is free. **Named re-open trigger, generalising #305(b):** the day any
footer slot carries text that is not (a registry-charset-gated name ∨ a derived int ∨ a
literal constant), the containment question re-opens as a footer-specific decision — the
seam alone is KNOWN-insufficient for same-line text, measured.

**T3's packet text is amended at close-out** per #305(a): the footer's forgery is closed
by the identity charset + provenance chain, not by the render seam.

## 5.2 · Q2 (C-DEF 5) — the CONTRACT yields; R8(2) stands; the dead pin is re-authored as the BUDGET pin

`registry_reads == 0` contradicts an OPERATOR ruling whose cost line prices the exact read
it forbids (*"one charset-gated registry read per identity-less write"* — R8, verbatim).
The hierarchy is not close: **the pin yields.** But what the pin PROTECTED survives —
R1's rejection of per-attribution scans and heuristic sweeps — restated as the budget pin,
with the quantifier law applied (every world forced by a fixture, not one):

| world | reads | footer |
|---|---|---|
| no attribution value supplied at all | **0** | none |
| value FAILS the charset gate (space/`=`/backtick/…) | **0** — the gate is what "charset-gated" MEANS: no read for a value that cannot be a name | none |
| value passes charset, UNREGISTERED | **≤ 1** | none |
| value passes charset, REGISTERED | **≤ 1** | third-person, no drain imperative, coupling disclosed on the field (R8(2) verbatim) |

Plus the ceiling: **at most ONE registry read per call, on every path** — that is the pin
that still kills the build R1 rejects. ⚠ The "silence half" of the old pin is kept but
CORRECTLY SCOPED: an omitted `agent=` is silent only when the attribution value resolves
to nothing — under R8(2) a registered `created_by` legitimately footers third-person; a
pin asserting unconditional silence for omitted `agent=` would re-contradict the ruling
one world over.

## 5.3 · Q3 — the ARCHITECTURE is ruled: the REGISTRY is the one resolution seam; the harness is a defect, not a design

**Reading A stands: identity resolution goes through `agent_registry.get_agent`** — R1
verbatim ("resolved through the registry"), R8's cost line names a REGISTRY read, and ONE
IMPLEMENTATION: name→row resolution has exactly one home. Reading B (resolution via the
message ledger's view of the `agent` table) would mint a SECOND copy of name resolution —
#102's shape — and is REJECTED. Refbuild's sentence is adopted as the finding: *"the
harness, not the ruling, is currently deciding the architecture"* — as of this ruling it
no longer does. **The C3 harness's id convention (`f"agent:{name}"`) and its empty
registry are adjudicated CONTRACT DEFECTS** (C-DEFs 1–3, plus C-DEF 4's one-line import),
to be landed IN the contract by its author per refbuild §6's plugin — including the second
half of C-DEF 1 (the two fakes must agree on the registry's uuid5 id; in production the
`to` edge points at the `agent` row). The three pins refbuild measured as passing
VACUOUSLY are re-read by the author after the repair, per its list.

**Riders routed to the builder's brief** (refbuild found them; a brief that omits them
buys a fix wave): the `test_comms_tool` charset-prose constraint (§4.1 — keep *"must stay
in the safe charset"*, drop the false clause), the `test_blocks_edge::_tool_seam` wiring
co-edit (§4.2 — empty fakes, NOT a missing-service guard; a silently-skipped footer is
confident silence), the CL1 vocabulary constraint (§4.3 — the footer paragraph may use
none of the seven duty words), and the 23-call-site unbound-dispatcher rewrite (§2.1).

**The scratch tree** `/home/ejprice/scratch-c3-ref` holds the only copy of the reference
build (worktree-abandonment law, applied to scratch): **keep it until the real C3 build
lands** — it is the diff oracle — then discard; the load-bearing instrument
(`c3_harness_repair.py`) is already pasted verbatim in refbuild §6 and survives either way.

**Falsifiers:** 5.1 — a footer path found rendering ANY value that did not ride the
three-link chain (⇒ the containment question re-opens immediately, not at the trigger);
5.2 — a measured R8(2) path needing a second read (⇒ back here, the ceiling is ruled, not
assumed); 5.3 — a production consumer found resolving names outside the registry (⇒ #102
escalation, not a quiet third copy).

---

# §6 · ⚠ OPERATOR-REVIEWABLE (none blocking under the standing delegation)
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
4. **§B6 line 1 amended to its explicit form** (Ruling 4): "full gates green" is now
   "green under the pending-contract wrapper, partition counts in the pasted tail". This
   grazes the operator-ruled "zero mypy errors" sentence — I judge it instrumentation of
   an already-unmeetable reading, not narrowing, but the operator should see it.
5. **Packet-39's files were left untouched and #296 un-waited-for** (Ruling 4) — the
   bound self-destructs at the build. If the operator prefers the contract re-authored to
   the mypy-clean idiom NOW (option D), that is their fork to re-open.
6. **Packet-39's close-out left an unadjudicated red typecheck at HEAD** — a process
   finding about an operator-adjacent packet, owed a ledger row (Ruling 4 item 5).
7. **Predecessor §B5's neutralisation pin overturned** (Ruling 5.1) — a same-authority
   overturn, on a by-construction measurement (#305). The seam construction itself stands,
   demoted to discipline; the closure is the charset+provenance chain.
8. **T3's packet text amended at close-out** (Ruling 5.1) — the footer's forgery closure
   is re-attributed from the render seam to the identity chain. T3 was ruled under the
   operator's trust principle; the amendment narrows its mechanism claim to what is
   measured, not its requirement.

---
*Written 2026-08-01 by `design-sidecar-04b2-wavec-1` (Fable, long-running design sidecar)
against `feat/surreal-unification` @ `04ede45`. Grounds: the contract author's report
(measurements theirs, cited by section), predecessor sidecar rulings §B1–B6, packet
§r6/§C1/§04b-2/INHERITED/SWEEP, findings #268/#300/#301/#302 read from the live ledger,
the five named test classes and `TaskLedger.query_tasks`/`_candidate_statement` read
verbatim, and the store reference §2/§3/§6/§7 (read before ruling on statement shape, per
standing law). No git command was run; this file is my only tree write.*
