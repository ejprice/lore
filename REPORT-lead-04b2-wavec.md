# REPORT-lead-04b2-wavec — the lead's orchestration rulings, packet 04b-2 wave C

Running log. The DESIGN rulings live in `REPORT-design-sidecar-04b2-wavec-1.md` (Fable
sidecar, operator-delegated authority); this file carries the LEAD's rulings — assignment,
sequencing, acceptance, and routing. Both archive to
`docs/plans/v2/receipts/` at wave close-out.

Written against `feat/surreal-unification` @ `a88e7c5`.

---

## L-1 · C3 COMES BACK TO ITS AUTHOR — not forward to a builder

**Ruling.** `contract-04b2-wavec-1` reported C3 authored (42 tests in
`loremaster/tests/test_comms_footer.py`, ruff clean, mypy clean) but **explicitly NOT
builder-ready**, and declined to claim a satisfiability receipt: 34 failed / 887 passed,
of which **28 are `NotImplementedError` from nine harness helpers it did not finish**.

**The refusal is correct and I rule with it, not against it.** Those 28 reds fail
*identically* against a correct build and a wrong one, so they discriminate nothing — a
builder handed C3 today would be TRAPPED between a contract it cannot satisfy and code it
may not edit. That is the C-DEF class this repo has already paid for (finding #133; the
20-RED-pins-on-a-correct-build receipt).

**The author offered two options; I take the first and decline the second.** Finish the
harness → produce a real receipt. I decline "treat the file as a pin SPECIFICATION for
whoever does": a spec handed onward is precisely how an unfinished contract becomes
someone else's trap, and the author who holds the reasoning is the cheapest finisher.

**Sequencing:** C3 finished (with its receipt) → then C1, carrying the sidecar's §2 seven
riders and the TIGHTENED #268 instrument (comparative form; **not** a transcribed
constant). No builder sees either contract until its reds are red BY DESIGN and the author
can name which wrong build each one kills.

## L-2 · THREE INHERITED FACTS CORRECTED — all three stick

Found by the contract author while authoring C3. Recorded here because each contradicts a
document this packet told its agents to trust.

1. **04a residual R-5 names a STALE SYMBOL.** `_comms_dispatch` **does not exist**. The
   real defect is `AppContext.comms`, whose `Raises:` omits `MessageLedgerError`. The
   packet text is wrong; the lead corrects it at close-out, citing the author.
2. **R-12 is DISCHARGED GREEN, not a build item.** The tool-seam teaching for `brief_ack`
   already existed; only the PIN was missing. The residual described work that was already
   done.
3. **A self-authored C-DEF, caught by running the file** — `_BASELINE_DUTY_VOCABULARY`
   shipped as an empty tuple, making SECTION E assert *"the vocabulary is empty"*, RED on
   a correct build. Fixed and recorded in the constant's own comment. This is recorded as
   a RECEIPT, not a demerit: it is the contract author running its own contract, which is
   the only instrument that finds this class.

## L-3 · CROSS-SLICE SEAM ROUTED TO 04b-3 AS A BINDING RIDER

The author measured that **the footer's counts and C2's fleet columns are THE SAME TWO
NUMBERS** (R4). It defined `MessageLedger.pending_traffic` and pinned it by mutation.

**Ruling: this is a BINDING RIDER on 04b-3's C2 row, not a note in a report.** C2's brief
MUST say *CALL `pending_traffic`* — never re-derive the counts. ONE IMPLEMENTATION: if two
call sites need the same policy it is a function they call, and a pattern offered for
cloning is a defect offered for cloning (#102/#120). The mutation pin stays in C3, because
that pin is what makes a silent re-derivation in C2 impossible to ship.

## L-4 · THE GATE IS RED AT HEAD, AND I WILL NOT NARROW IT MYSELF

**Measured by the lead** with the canonical runner (`./scripts/typecheck.sh` — not a
combined `mypy` invocation, which this repo documents as false-erroring), at `04ede45`
plus the wave's doc/receipt commits: `typecheck: loremaster FAILED`, **exit 1**,
`Found 102 errors in 8 files (checked 180 source files)`.

Per-file, merged across the runner's legs (11 files):

| file | errors |
|---|---|
| `loremaster/tests/test_auth_composition.py` | 40 |
| `lorerunes/tests/test_roster_parser.py` | 36 |
| `lorerunes/tests/test_posture.py` | 35 |
| `loremaster/tests/test_permission_resolver_seam.py` | 20 |
| `lorerunes/tests/test_email_normalisation.py` | 18 |
| `loremaster/tests/test_hosted_readonly_posture.py` | 13 |
| `loremaster/tests/test_allowlist_roster.py` | 10 |
| `loremaster/tests/test_google_token_verifier.py` | 7 |
| `loremaster/tests/test_auth.py` | 7 |
| `loremaster/tests/_auth_fixtures.py` | 3 |
| `loremaster/tests/test_auth_identity_seam.py` | 2 |

Every error is `attr-defined` on a symbol that does not exist yet
(`loremaster.config.resolve_posture` / `PostureConfigError`; `lorerunes.Posture` /
`SCOPE_READ`), and **every file is packet 39 territory** — the hosted-security contract
whose INDEX row reads *"Contract 480 pins / 444 RED / 36 GREEN … Build never started,
deliberately"*, BLOCKED on operator decision **#296**.

**So the gate was RED before wave C touched anything.** It is red *by design*: a contract
was deliberately committed ahead of a build that is waiting on an operator decision.

**The conflict:** predecessor §B6 line 1 requires *"Full gates green with a passed-COUNT in
the pasted tail + cold audit GO"* before the deploy, and `CLAUDE.md`'s standing gate is
*"zero mypy errors including test trees"*. Read literally, **04b-2 can never deploy until
packet 39 builds** — which is blocked on a decision that may not arrive for weeks.

**Ruling: I do not narrow the gate on my own authority.** Narrowing the definition of
"green" is exactly how a gate stops being one, and this repo's receipts are full of
instruments that died by having their scope quietly reduced. Routed to the design sidecar
(thread `q:04b2-gate-definition`) with four candidate readings, none adopted, and flagged
as probably OPERATOR-REVIEWABLE since it is at least partly a scope question and scope is
the operator's.

⚠ **Corollary the wave must respect meanwhile:** no agent may report "gates green"
unqualified. Every green claim in this wave is SCOPED to its own file set and says so —
an unscoped green claim here would be false, and *"I verified it" is a claim about a
SCOPE, not a fact*.

---

## L-5 · STRUCTURED HANDOFF — written deliberately, not at exhaustion

Written at `801125c`+ by `lead-04b2-wavec`. **The next phase (two builders, a cold
audit, a production deploy) is where a degraded lead does real damage, and all of it
is still ahead.** Per the deferral law this is capacity exhaustion answered by handoff
rather than a quiet fade: everything load-bearing is committed, every ruling lives in a
tracked report rather than a message body, and every open item is on the ledger with an
owner.

### What LANDED (12 commits, all on `feat/surreal-unification`)
`04ede45` #263 · `a88e7c5` the sizing escalation + rulings 1–3 · `f67a219` lead rulings
L-1..L-4 · `025c2a9` C1 contract + receipt · `6974bdc` pending-contract gate + #312 ·
`d5c8958` C3 C-DEFs repaired · `f6d8e47` C3 builder-ready · `c5ca6f2` #308 ·
`f00923e` C1 graded INSUFFICIENT · `3488517` C3 graded INSUFFICIENT · `801125c` C1 fix
wave (69 pins) · gate-currency mode.

### STATE, per slice
| slice | state | owner |
|---|---|---|
| **C1 contract** | fix wave landed, 69 pins, ref build 1275/0. **OWES**: `lore_tasks action=get` per Ruling 8, then a **DELTA ADVERSARY** | `contract-04b2-wavec-2` (live, standing by) |
| **C3 contract** | INSUFFICIENT — 26 wrong builds. Fix wave running | `contract-04b2-c3fix-1` (live) |
| **gate currency** | DONE, committed | closed |
| **C2 (fleet columns)** | ruled OUT of this wave → 04b-3 | 04b-3 |
| **builders (C1, C3)** | NOT STARTED | — |
| **cold audit** | NOT STARTED | — |
| **deploy** | NOT STARTED — see the open question below | — |

### THE OPEN OPERATOR QUESTION — do not deploy without an answer
The operator authorised the deploy early, with sequencing: *"After the gate, back up.
Then deploy."* **What is being deployed has since changed shape**, and they were asked
but had not answered when this was written. The wave now also carries: a new gate
instrument, a **manifest inversion demoting `CLAUDE.md`'s gate section to a citation**,
and a **newly-minted served MCP action** (`lore_tasks action=get`). Ask again before the
recreate; do not treat the original nod as covering the new shape.

### THE DEPLOY SEQUENCE, as amended this wave
§B6's seven receipts stand, **plus an EIGHTH derived twice this wave**: the gate run
happens on a **QUIET, COMMITTED tree**. Measured cause — with five agents editing, the
same file gave 1 failed/41 passed committed and 40 failed/8 passed in the working tree
four minutes apart; and the currency mode's first runs caught three true-but-transient
orphans. **Noise is how an instrument gets switched off.** Order: full gates green on a
clean tree + cold audit GO → **fresh `surreal export` backup** (EXIT=0, table count,
engine success line) → rollback receipts into the Log → recreate → smoke. Never
`lore-deploy start` (#165/#166). Both `CreateCommand`s **re-derived at deploy time**.
Production was on image `e91e37b9` at kickoff.

### LEDGER RESOLVES OWED AT CLOSE-OUT
#219 · #247 (already closed in code by ruling R2 — resolve with that receipt) · #253
(verify in the deployed artifact) · #260 (`lore.yaml` lorerunes include, applied AT the
recreate) · #268 + #300 (resolve together; #268's own "cheapest fix" is PROVEN
BACKWARDS — do not implement as written) · #277 · #305 · #309/#310/#311/#313/#314/#315
route per their rulings · #89 resolves on Ruling 8's receipt, its packet-05 routing
OVERRULED. **Archive every `REPORT-*.md` by `git mv` into
`docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/` — never `rm` (#152).**

### WHAT THE NEXT LEAD SHOULD KNOW, in one paragraph
**Both contracts passed their own satisfiability receipts and were then graded
INSUFFICIENT** — C1 by 7 wrong builds, C3 by 26. A receipt proves a contract
SATISFIABLE; it never proved it SUFFICIENT, and nothing in this wave was found by
reading. Five separate defects were found by *executing*: a contract calling a verb
that does not exist, a finding whose own prescribed fix would have made its pin
permanently vacuous, a chain link left vacuous by a correct neighbouring guard (#313),
a false gate inside the fix for a false gate, and a served surface unreachable through
its own registered tool (#314). **So: run the adversary on every contract revision,
including fix waves, and never let a receipt stand in for a grade.**
