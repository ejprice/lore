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

> ⚠ **CORRECTED BY FINDING #307, and the correction is against ME.** That `102 / 8 files`
> is **ONE LEG's summary**, not the total — merged across the runner's legs it is **191
> errors across the 11 files** in the table below, which is why the table does not sum to
> 102. My "every error is `attr-defined`" is also too strong: it is **190 of 198**. I took
> a number off a runner tail and promoted it to the headline of a finding whose entire
> lesson is that unverified numbers propagate — with the contradicting table sitting
> directly underneath it. A builder re-derived it and caught me. The per-file table below
> is correct and is the number to use; #307 is the durable record. Left in place rather
> than silently rewritten, because the failure is the point.

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
| **C1 contract** | ~~fix wave landed, 69 pins~~ → **COMPLETE at 81 pins**; `action=get` MINTED (Ruling 8, all six riders), ref build **81/0**, seam suites **1572/0** (`f4a9f52`). **DELTA ADVERSARY IN FLIGHT**, not pending | `contract-04b2-wavec-2` (live, standing by for delta findings) · `adversary-c1-delta-1` (live) |
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

### ⚠ FOUR CONCRETE ITEMS OWED FROM THE C3 FIX WAVE (`39db35c`, its §5.2/§6.1/§9/§7)
1. **The wrong-build DRIVER lives ONLY in the scratch tree** at `/home/ejprice/scratch-c3-ref`.
   It carries **25 receipts and exits 0**, and it is the instrument that proves C3 kills what
   the adversary found. It is pasted VERBATIM in `REPORT-contract-04b2-c3fix-1.md` §9, which
   is committed — **so it is recoverable, not lost.** But `git mv` it into `scripts/` before
   that tree is discarded: a driver that exists only in a scratch directory is unrecoverable
   by construction the moment someone cleans up. Its author could not commit it (`scripts/**`
   was outside its writable set).
2. **A BUILD REQUIREMENT the contract now imposes** (§5.2): the receipt required one repair
   to the reference build — MP-6's ambiguity classification. The builder must land it.
3. **R-4's co-edit** (§6.1) lands the `_INSTRUCTIONS` paragraph byte-exact in
   `test_comms_tool.py`, so **CL3's terminating pin is RED at HEAD until the builder ships**.
   Shared file; other agents will see that red and must not "fix" it.
4. **SECTION D now drives a LIVE store** (§7.4) — a new test dependency, ~12s under `-n auto`.
   Plus four non-blocking decisions in §7 for whoever takes the build.

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

---

## L-6 · RESUME POINT (supersedes L-5's state table) — stop before the cold audit

Written at `0d24c12` by `lead-04b2-wavec` on an operator instruction to **stop before the
cold audit**. L-5's rulings L-1..L-4 still stand; **this section replaces its STATE table
and its owed-items list.** Read this one.

### THE ONE-LINE STATE
**Both contracts are complete and adversary-graded. C1 is BUILT. C3's build is blocked on a
single missing test-double method.** Nothing has been deployed; production is still on image
`e91e37b9`, unchanged since kickoff.

### ⛔ THE SINGLE BLOCKER — resolve this first
`FakeMessageLedger` has **no `pending_traffic` method**, and SECTION D's "fake" leg calls it
via `_pending_traffic_for`. **Without it C3 cannot COLLECT** — not fail, *collect*.

**RULED (lead): it belongs to the CONTRACT side (`contract-04b2-c3fix-1`), NOT the builder.**
`loremaster/tests/_message_fakes.py` is **out of `builder-c3-1`'s writable set**. The reason
is load-bearing: SECTION D's own clause says a delegating double *"cannot launder a wrong
production statement"*, so the fake must carry an **INDEPENDENT** count — and the fake is
what OBSERVES the build, so a builder authoring it would be grading its own work and that
independence would be fictional. Same law that kept the reference build away from the builder.
If `contract-04b2-c3fix-1` is gone when you resume, spawn a **contract-side** agent to add it.
Do NOT hand it to the builder.

### WHAT IS BUILT vs NOT
| | state |
|---|---|
| **C1 contract** | ✅ 90 pins, 2 adversary passes + delta, `54a29dd` |
| **C1 BUILD** | ✅ **90 passed / 0 failed, first attempt, zero contract edits** — `0ff05ed` (`server.py` +379, `tasks.py` +195) |
| **C3 contract** | ✅ 217 collected, 3 adversary passes, `0d24c12` ⚠ *collected ≠ passed — no run-count was ever produced for the third pass* |
| **C3 BUILD** | ⛔ blocked on the fake above |
| **gate currency** | ✅ `6974bdc` + the currency mode |
| **cold audit / deploy / close-out** | ❌ not started |
| **C2 (fleet columns)** | ruled OUT → 04b-3 |

### ⚠ THE FLEET DOES NOT SURVIVE THIS SESSION — RE-SPAWN, do not look for them
Every agent named here is an in-session teammate. **A resuming lead in a NEW session inherits
NONE of them.** Their REPORTS are committed and are the durable artifact; the agents are not.
Re-spawn from the briefs described in those reports. In particular `builder-c3-1` is *mid-build*
as this is written — its work exists only in its own context, so **assume C3's build must be
re-run from `0d24c12`** unless a later commit says otherwise.

### ⚠⚠ SPAWN THE FABLE DESIGN SIDECAR FIRST — before any design question arises
**This is operator-directed and it is not optional.** Design questions in this repo do NOT go
to the operator; they go to a **long-running Fable design sidecar**. The operator corrected the
lead on exactly this, twice, in this session — *"I'm not the lore consumer. Agents are. So stop
asking me questions like this. Start a long running Fable design side car. Ask it."*

**How to spawn it (the pattern is standing law, `CLAUDE.md` THE FABLE-SIDECAR PATTERN):**
- **ONCE per session**, as a **`general-purpose` agent on `fable`** — **NEVER a fork** (forks
  inherit orchestrator identity).
- **LONG-RUNNING for the whole packet.** Front-load its brief: the design question, exact file
  pointers, and a standing instruction to **STAND BY** after each answer. Never respawn per
  question; if you must respawn, suffix the name.
- Its idle-between-questions state is **BENIGN — never wake-loop it**.
- ⚠ **It must PERSIST to `REPORT-design-sidecar-<name>.md` and then send a SHORT ledger
  message pointing at it.** This session lost an entire set of its rulings because the brief
  said *"reply in TEXT (no file)"* — see #303. A ruling that exists only in a message body is
  a ruling the next session never meets.
- ⚠ **It needs a WAKE.** The ledger is durable but pull-only; a directive sent without a native
  `SendMessage` sits unread. The lead lost hours to exactly this on the D-6 ruling.

**WHAT TO ASK IT, AND ON WHAT BASIS — THE CONSUMER LAW:**
**lore's clients are AGENTS — Claude/Sonnet/Opus/Fable — never humans.** Every served surface
(renders, counts, errors, teaching prose, tool descriptions) is read by an LLM that learns the
contract FROM what is served. **Frame every question to the sidecar in those terms**, and require
its rulings to be justified the same way: *what does a Claude consumer learn from these bytes,
and can it act on them without checking?* This session's best rulings all turned on that framing
— ESC-5's grammar (existence, not quantity), the chain render staying id-only because enrichment
is ERGONOMICS not a TRUST repair, minting `action=get` because #89's own author had fallen back to
a raw SELECT against production, and #319's false `limit` description that teaches agents away from
the very affordance ESC-5 makes honest. **Its acceptance instrument is the routing probe —
CALL_AGAIN vs ROUTE_AROUND — and a ROUTE_AROUND on an honestly-rendered surface is a FAILED
acceptance to fix, never a waived answer.**

**It has already ruled 10 times this wave** (`REPORT-design-sidecar-04b2-wavec-1.md` §§1–10).
Read those before asking anything — three of them (7, 9, 10) converged independently on the same
answer, and it twice took accountability for its own defective riders rather than editing them
silently.

### RESUME SEQUENCE
1. Unblock + land **C3's build** (`builder-c3-1` is live and holding; brief is in its report §4f).
2. Collect **`adversary-c3-delta-2`**'s verdict — it graded the committed `58f2786` in scratch.
3. **COLD AUDIT** — fresh context, re-runs the gates. **Do not skip or rush it.** In this wave
   **42 wrong builds passed contracts that had already passed their own satisfiability
   receipts.** A receipt proves SATISFIABLE, never SUFFICIENT.
4. **DEPLOY** — ⚠ **ASK THE OPERATOR AGAIN.** They authorised it ("after the gate, back up,
   then deploy") *before* the wave grew a gate instrument, a `CLAUDE.md` manifest inversion,
   and a newly-minted served MCP action (`lore_tasks action=get`). The original nod does not
   cover the current shape. Sequence: clean-tree gate + cold audit GO → **fresh `surreal
   export` backup** → rollback receipts into the Log → recreate → smoke. Never `lore-deploy
   start` (#165/#166); both `CreateCommand`s **re-derived at deploy time**.
   ⚠ **EIGHTH RECEIPT, derived twice this wave: the gate run happens on a QUIET, COMMITTED
   TREE.** The same file measured 1 failed/41 passed committed and 40 failed/8 passed in the
   working tree four minutes apart.
5. **CLOSE-OUT** — below.

### CLOSE-OUT CHECKLIST (nothing here is done)
- **INDEX row + Log entry** — neither written. The packet has NO Log line for this wave.
- **Ledger resolves owed:** #219 · #247 (already closed in code by ruling R2 — resolve with
  that receipt) · #253 (verify in the deployed artifact) · #260 (`lore.yaml` lorerunes include,
  applied AT the recreate) · #268 + #300 (resolve together — ⚠ #268's own "cheapest fix" is
  PROVEN BACKWARDS; do not implement as written) · #277 · #305 (note its over-narrow scope per
  Ruling 10) · #301 #309 #310 #311 #313 #314 #315 #316 #318 #319 route per their rulings.
- **ARCHIVE all `REPORT-*.md` by `git mv`** into
  `docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/` — **never `rm`** (#152). Required
  before any image build.
- **RESCUE the wrong-build DRIVER** — it exists ONLY in scratch trees and is now in **THREE
  copies** (R-9, flagged three times). It is pasted verbatim in
  `REPORT-contract-04b2-c3fix-1.md` §9/§9b, so it is recoverable — `git mv` ONE canonical copy
  into `scripts/` before those trees are discarded.
- **Scratch trees to dispose of:** `/home/ejprice/scratch-c1-ref`, `scratch-c3-ref`,
  `scratch-adv-c1`, `scratch-adv-c1d`. Keep until their builds land, then discard.
- **#319's UNSWEPT residual** — one false served tool description was found by accident; the
  others were never swept.

### FOUR THINGS THE NEXT LEAD SHOULD NOT RE-LEARN
1. **A satisfiability receipt proves SATISFIABLE, never SUFFICIENT.** Both contracts passed
   their own receipts and were then graded INSUFFICIENT — C1 by 7 then 5 more, C3 by 26 then 4.
2. **Nothing this wave was found by reading.** Every defect came from EXECUTING: a contract
   calling a verb that does not exist, a finding whose own prescribed fix would have made its
   pin permanently vacuous, a chain link vacuous because a *correct* neighbouring guard
   shadowed its fixture (#313), three false gates an author caught in its own work, a served
   surface unreachable through its own registered tool (#314), and a forgery reaching the
   consumer verbatim on the CORRECT build (DELTA-3).
3. **Four independent rulings converged on ONE answer** (Rulings 7, 9, 10, and #319): stop
   enumerating the members you can see; **DERIVE the surface by scan** and treat anything
   outside the seam as a door named `file:line`. Every time someone wrote a list instead, it
   was wrong.
4. **The ledger is the durable channel; the native inbox is the WAKE.** Three confirmed losses
   this session, every one survived because the content was also on the ledger. A directive
   sent to only one of them either vanishes or is never read — the lead did both, once each.
