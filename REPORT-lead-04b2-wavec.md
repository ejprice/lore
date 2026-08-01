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
