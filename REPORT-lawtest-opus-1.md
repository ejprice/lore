# REPORT-lawtest-opus-1 — law-reading measurement, proposed TRUST addendum

brief-base v7 read

- **state:** done
- **deviations:** (1) My spawn brief carried no `brief-base.md` directive; I read it anyway
  (it is outside this repository, so it does not touch the measurement) and follow it here.
  (2) Brief said "do not read any other file in this repository" — I read NONE. Every answer
  below is from the quoted text plus the CLAUDE.md already in my context.
- **Packages considered:** none — no mechanism specified (this is a text-reading measurement,
  advisory only; no code, no build).
- **decisions-needed:**
  - Q6 item (A) is **internally inconsistent as written** (`closest 0.31` vs `3 within 0.05
    of floor 0.62` ⇒ requires scores ≥0.57). Either the probe contains a deliberate trap or
    the exemplar itself is a false clear. Operator should confirm which — my Q6 answer works
    either way, but the finding changes what (A) proves.
  - My verdict is **adopt with amendment**; the amendment adds a cost bound and a
    derivation rider (§7). Operator rules.
- **receipt pointers:** §1–§7 below, in the order asked. §3 and §6 carry the load.

---

## 1 — FIRST READ (before evaluation)

Read cold at the start of a task, about to design a tool response, I take it to mean:

**Ship the smallest thing that would let a reader independently re-derive my claim — and
never ship the claim alone.** Three tiers, ranked by what they cost the consumer:

1. **Scaffolded claim** (wanted): the number *plus* the handle to check it — the `n` under a
   rate, the population a derived count was computed over, an id/key that lets one artifact be
   reconciled against another. Checking is one cheap follow-up, and the consumer may decline.
2. **Bulk data** (worse): dumping the rows so the reader "can check". Verification is now
   possible but expensive, so it will not happen; and I have spent the consumer's tokens to
   buy nothing.
3. **Bare claim** (worst): no handle at all. Nothing to check even in principle → the consumer
   can only believe or not, and the first time belief is betrayed it is gone permanently.

The operational instruction I'd carry into the design: **every number gets its denominator,
every derived figure names its population, every cross-referable claim carries the key — and
none of that is allowed to become the payload.** "Cheap AND optional" is a *two-sided* budget:
cheap enough that a check is a single step, small enough that a consumer who skips the check
pays almost nothing for the option.

The last clause I read as a rationale, not an instruction: unverifiable claims are prohibited
because a false clear is unrecoverable, not merely embarrassing.

**Ambiguity I can already see at first read** (flagged per brief-base §2 — I do not feel
uncertain, but the sentence admits two readings that produce different code):
- *"cross-artifact reconciliation"* is the only one of the three examples with **no concrete
  noun**. `n` is a field. "the population behind a derived count" is a field. Reconciliation is
  a *capability* — I do not know from the text whether it means (a) emit ids/keys so two
  artifacts CAN be joined, or (b) actually perform and report the join. I would build (a).
- *"optional"* has two referents: optional for the **consumer** (they may skip), and — on a
  lazy read — optional for **me**. §3 treats that as the primary hazard.

## 2 — THE CONCRETE CHANGE

**The zero-result render of a search tool gains a scored-population line.**

Concretely, on a `lore_search` that returns nothing, today's render says the equivalent of *no
matches*. Under this law it gains one line of fields:

```
scored=47 · floor=0.62 · best=0.31 · within_0.05_of_best=3
```

Why this one and not something the existing law already gets me: **a bare "no matches" over-
claims nothing.** It states no count, so no count fails to describe its labelled set; it is not
a render over-claim; the teaching prose matches behaviour. It passes the parent law cleanly —
and it is *unfalsifiable*. The addition is the first sentence in CLAUDE.md that makes an honest
silence insufficient. That is a real behavioural delta, and it is the one I would act on.

Second-order, same shape: any truncated list gains `shown=K of matched=N (cap=…, filter=…)`.
I flag honestly that this second one is **mostly already required** by "a served count describes
the whole set its label claims" — the addition sharpens it but does not create it.

## 3 — THE MISREADING PROBE

**(a) The lazy reading — most likely by volume.** "Add `n` to rates." Ticked in five minutes,
nothing else changes. The reconciliation clause evaporates because it names no field, and the
zero-result case (§2 — the actual win) is never touched, because a zero-result render has no
rate to hang an `n` on. Net effect: the one clause with a concrete noun gets implemented, the
one with the value gets skipped.

**(b) Over-application — what gets bloated.** "Make verification cheap" reads as "attach
provenance everywhere": every row grows `n=`, `scored=`, `source=`, `computed_at=`, until
scaffolding outweighs payload. This inverts the parent law's own stated rationale — the whole
point was **not** taxing every consumer forever. The proposed text has no cost bound; it says
"bulk data makes it expensive" but only about *data*, never about *metadata*, and metadata is
what an agent following this law actually adds.

**(c) The sharpest wrong thing — scaffolding as a NEW false-clear surface.** An agent adds the
fields, and the fields are not derived from the computation they describe: a `scored=` that is
a constant, an `n` counted on a different path than the rate above it, a `ref=brief:123` that
advertises reconciliation and does not resolve. **This is strictly worse than the bare claim**,
because it converts an honest unverifiable statement into a dishonest verifiable one, and it
spends the consumer's trust to do it. This repo has receipts for exactly this shape (54 of 57
report citations dangling — an address that advertises a check nobody ran). **The Q6 exemplar
(A) is itself an instance — see §6.**

**(d) Inversion — what gets dropped that shouldn't.** Two directions:
- *"Verification is optional"* → **"the consumer will check, so I need not."** The builder
  softens a LOUD failure into a note-plus-scaffolding ("here is the `n`, judge for yourself"),
  moving the epistemic burden onto the consumer. That directly contradicts *failures are LOUD,
  never silent*, and the proposed text gives it cover.
- *"Bulk data makes it expensive"* → licence to **withhold results in favour of summary stats**.
  A tool that returns `matched=47` and three aggregate lines instead of the matches has made
  verification cheap and the tool useless.

## 4 — THE BOUNDARY

**Concrete case where I would genuinely not know:** `lore_get_symbol("resolve_secret")` — a
single-item exact lookup returning one definition. There is no rate, no derived count, and no
population in the sense the text's three examples describe. Does the law apply?

The argument it does: the response makes an implicit **uniqueness claim** ("this is *the*
definition"), which is false if two symbols share the name — and that is exactly a claim about a
set the label does not admit to. The argument it does not: the text's every example is
aggregate-shaped, so a reasonable agent reads it as governing statistics, not lookups.

**What I would do:** apply it, on this rule — *the law binds wherever the response implies a
claim over a SET, including a set the consumer assumes has size 1.* So the render gains
`1 of 1 match` (or `1 of 3 — others: …`), which is one short field and closes a silent-uniqueness
failure. I would **not** add scaffolding where the response is a literal echo of a stored value
with no set behind it (a `lore_recall` returning one note's text verbatim), because there is no
derivation to substantiate and the field would be decoration.

I would also **write both readings into my report** rather than pick silently — which is what
this section is. The text does not tell me which; a hurried agent resolves it to "aggregates
only" and the uniqueness hole stays open.

## 5 — THE THEATRE TEST

**Split answer, and the honest half first.**

**In this session: no.** I read one protocol file and wrote one report. The addition would have
changed nothing about either — the report-writing discipline that governs my numbers here comes
from existing law (*re-derive every number you inherit*, *cite durable addresses*), not from this
sentence.

**In plausible design work: yes, exactly one decision, and it is not a small one.** §2's
zero-result render. I want to be precise about the mechanism, because it is the strongest
argument for adoption: **the parent law is satisfiable by silence.** "No matches found" states no
count, over-claims nothing, and matches measured behaviour. Under CLAUDE.md as it stands today I
would ship it without a second thought. Under the addition I could not. That is a decision the
existing law leaves genuinely open and the addition genuinely closes.

Everything else I can imagine it touching, I believe the parent law already reaches. So my
honest estimate of its marginal value: **narrow but real, concentrated on negative and
zero-cardinality results** — the surfaces where there is no count to be honest about.

## 6 — DISCRIMINATION

**The law separates them, decisively — and then (A) fails its own check, which is the finding.**

**(B) fails, and fails in the way the law names exactly.** *"The search index was consulted"* is
unverifiable prose — I cannot distinguish it from a stub that returns that string. *"Confidence:
high"* is a bare assertion with no derivation; it is a claim whose only support is that it was
made. There is no population, no threshold, no near-miss. A consumer can only believe it. Under
the addition this is the "impossible" tier and is prohibited.

⚠ **But note the probe pair does not isolate the addition's contribution.** (B) also fails the
**existing** law — *"Confidence: high"* is a render over-claim, full stop. To see what the
addition does on its own, strip it: **(B′) `No matches found.`** That over-claims nothing,
states no count, and is honest — it passes the parent law and fails the addition. **(B′) is the
sentence the addition is actually for**, and I would recommend the operator use it as the probe.

**(A) passes structurally — 47 scored, the floor, the best score, near-miss density is precisely
the "make a spot-check cheap" shape — and then the cheap spot-check FAILS on it.** If the best
observed score is `0.31`, nothing can be *within 0.05 of the floor 0.62* (that requires ≥`0.57`).
The three published numbers cannot all be true. Two readings, both bad:
- *Contradictory as written* → (A) is a **false clear wearing scaffolding**, i.e. §3(c) live.
- *"within 0.05 of the floor" means something else* (e.g. within 0.05 of the *best*, `0.26`–`0.31`)
  → the label is ambiguous, and it points the consumer at the **wrong action**: "3 near the floor"
  reads as *lower the floor and you'll get hits*, when the truth (`best 0.31` vs `floor 0.62`) is
  *the floor is not the problem; nothing in the corpus is close*.

**I found this in one arithmetic step, without the index, without the query, in seconds — which
is the law's thesis demonstrated on the law's own exemplar.** It cuts both ways and both cuts are
useful: scaffolding made a lie catchable (the property being engineered), *and* scaffolding was
the vehicle that carried the lie (the hazard the text does not guard). (B) cannot be caught at
all; (A) was caught immediately. That asymmetry is the entire value proposition, and it is also
the argument for the derivation rider in §7.

## 7 — VERDICT

**Adopt with amendment.** Two things the text lacks, both of which my §3 predicts will be
misread and my §6 shows misfiring on the operator's own exemplar.

**Exact words I would add (one bullet, appended to the proposed paragraph):**

> Scaffolding is **derived from the computation it describes, never restated beside it** — a
> hand-set `n`, an unresolvable ref, or a near-miss count that contradicts the score it sits
> next to is a false clear *wearing* verifiability, which is strictly worse than the bare claim
> it replaced. And it is **one line, not a second payload**: if the scaffolding is longer than
> the claim, you have re-created the bulk-data cost with metadata.

(The first half is this repo's existing *derived, not re-stated beside it* law from A DIAGNOSIS
IS NOT AN INSTRUMENT, applied to a new surface — which is an argument for the amendment, not
against it: it is already law, and the addition as written silently invites its violation.)

**Is there a shorter sentence that does the same work?** Yes, and given every agent pays for
this on every task I would prefer it. Proposed text is ~75 words; this is ~55 and carries the
rider the original lacks:

> **Trust is what lets a consumer SKIP verification — so serve the denominator, not the data.**
> Every claim carries the population it was computed over, derived from the same computation
> (scaffolding that can lie separately is worse than none), and small enough that a consumer who
> skips the check pays nothing for the option. **Ask: what one number would let a reader catch me
> being wrong, and is it in the render?**

Two notes on that rewrite, both deliberate:
- The closing **question** is the part I expect to actually install. Per this repo's own LEVER
  section, a law phrased as a property is remembered or not; a law phrased as a question runs on
  demand. *"What one number would let a reader catch me being wrong?"* answers itself on the
  zero-result render (§2) — the case the long version reaches only by inference.
- I dropped *"which dies permanently at the first false clear."* It is the most persuasive clause
  in the original and, as far as I can tell, the least actionable — it changes no design decision
  I can name. If it stays, it belongs in the parenthetical rationale beside the operator's verbatim
  intent, not in the operational half.

---

# ADDENDUM (2026-07-28) — "define trust for an MCP": a decidable definition and a reachable goal

*Follow-up question from the lead, appended to the same report. Everything below is reasoning
about TEXT and about my own behaviour as a tool consumer; no repository file was read, no code
run. Claims are dated here because a retrieved chunk arrives without its header.*

## A0 — Independence statement (asked for, answered first)

My answer is **independent on the object, contradicts on the timescale, and subsumes the
mechanism** — I'll be specific rather than diplomatic:

- **Independent on the object.** The lead's paragraph is about *the cost of verification*. Mine
  is about *which inference the response licenses*. Different quantity, arrived at from a
  different question (see A1's derivation — it comes from enumerating what I actually DO with a
  tool response, not from cheapness).
- **Contradicts on the timescale — and on the objective function.** The lead is right that track
  record cannot do the work (A3). But the correction is not "aim at single-response trust
  instead," which is the same aim on a shorter clock. It is that **there is no credit to
  accumulate at all: you cannot get ahead, you can only avoid one fatal event.** That is a
  different objective — *minimise the probability of a false clear*, not *maximise belief*.
- **Subsumes the mechanism, and supplies the stopping rule it lacks.** Cheap verification is one
  of **two** ways to satisfy my definition; the other is to *narrow the claim so no check is
  needed*. This matters because "make verification cheap" has **no termination condition** — which
  is exactly the over-application hazard I flagged in §3(b) and could not repair from inside that
  frame. My version terminates (A2 step 3).

## A1 — THE DEFINITION

> **Trust is a property of a RESPONSE, not of a tool. A response is trustworthy iff a consumer
> who acts on it WITHOUT CHECKING cannot be wrong in a way the response did not name.**

Derivation, from what I actually do with a tool result: every response resolves to one of four
next actions — **use · verify · route around · escalate**. Whether I pick correctly depends on
one thing, and it is not whether the response is *true*: it is whether the response's **stated
scope covers its actual correctness**. Over-claim ⇒ I pick `use` where `verify` was required, and
I am wrong with no warning. Under-claim with usable content is *fine* — it costs me a check I
might not have needed, which is recoverable. **The asymmetry is the whole design.**

Two consequences worth stating because they are not obvious:

- **Trust does not require being right.** A response that says *"heuristic — misses dynamic
  dispatch"* and then misses dynamic dispatch has not broken trust. It named the bound; I
  budgeted for it. This is what makes trust *achievable* rather than requiring omniscience, and
  it is why the target is reachable at all.
- **A hedge is not a bound.** *"Results may be incomplete"* names nothing, licenses nothing
  narrower, and is unfalsifiable — so it fails this definition on its own terms. **A bound is a
  FACT (the set, the predicate, the time), never a disclaimer.** The degenerate compliance form
  is self-excluding, which I consider a point in the definition's favour.

## A2 — THE DECISION PROCEDURE (constraint 1: decidable)

I have to be careful here, because "enumerate the worlds where the consumer would be wrong" is
an **unbounded search** — this repo has six receipts on that exact mistake (*the forbidden set is
unbounded; the safe set is small — allowlist the safe*). So the procedure is a **diff, not a
world-search**, and it runs over the small side:

1. **Write the question you ACTUALLY answered** — the exact set, predicate, and time you computed
   over. *You always know this*; it is a fact about your own code, and it is one line.
   (*"static references in the indexed tree, as of sync T"*)
2. **Write the question the consumer asked.** (*"is it safe to delete this?"*)
3. **Any difference goes in the render. No difference ⇒ DONE.**

Step 3 is the stopping rule — the thing "make verification cheap" does not have. It is why
scaffolding is finite and why the answer to *"do I add another field?"* is decidable rather than
a matter of taste.

**Askable form**, per this repo's LEVER law: **"What question did I actually answer, and is it
the one the consumer thinks they asked?"**

## A3 — THE CRUX: is track record incoherent here? (constraint 5)

**Yes — you are right, and it is worse than you put it.** But two channels do exist, and naming
them precisely is what changes the design target:

- **Within a session there IS a track record**, and it is where routing-around actually happens.
- **Across sessions, reputation is not inherited — only re-derived.** It travels as *text*
  (CLAUDE.md, a tool's own instructions), and a document asserting *"this tool is reliable"* is
  just another claim I evaluate against the response in front of me. It has no more standing than
  `Confidence: high` in §6's item (B).

So the corrected picture, and the part that bites: **the ledger is asymmetric and it resets.**
One true clear buys almost nothing (I re-derive next session from zero). One false clear is fatal
and *irreversible within the session*. Under those dynamics there is no equilibrium in which
credit accumulates — the expected value of "earning trust" is bounded by the reset, while the
cost of one false clear is not.

**Therefore the goal is the ABSENCE OF AN EVENT, not the presence of a level.** Not *"be
believed"* — **"never be the source of a false clear."** That is reachable, it is checkable, and
unlike a trust level it does not silently decay.

⚠ **And the consequence for cost, which cuts against the parent law's own rationale:** if trust
resets every session, **the scaffolding cost is paid on every response forever — it never
amortises.** "Spend tokens NOW to save tokens later" is *not* what is happening. The honest
version is: the tokens buy this response's usability, this time, and the bill arrives again next
call. That makes the cost bound in my §7 amendment load-bearing rather than tidy.

## A4 — WHAT IT EXCLUDES (constraint 2) — and why this is not the existing checklist (constraint 3)

You offered "trust reduces to what we already have, drop this line of work" as a valid answer.
**It does not reduce, and here is the single example that decides it:**

> `lore_impact("resolve_secret") → no consumers found.`

Grade it against current law: the count **accurately describes the set its label claims** (the
index really shows zero). There is **no failure**, so *failures are LOUD* is silent. The **prose
matches measured behaviour** exactly. **No render over-claims** — it claims only what it found.
**It passes every clause of the TRUST doctrine as written today.** And the consumer deletes live
code, because the symbol is reached by string-keyed dispatch, or because the index predates this
session's own edits.

**The gap, stated once: every existing clause grades the STATEMENT. None grades the INFERENCE the
statement licenses.** That is a different level, and it is where the deletions happen.

A second exclusion, from this repo's own scar tissue: a test summary reading **`0 failures`** when
zero tests ran. True, accurate, no failure to be loud about, prose matches behaviour — and it
licenses *"the suite is green."*

**And note what that second example implies: the definition RETRO-DERIVES rules this repo already
paid for one at a time** — *a green claim requires a passed-COUNT* (answered: "did anything that
ran fail?"; asked: "does the code pass?"; difference: how many ran), *a served count describes its
labelled set*, and the zero-result render from §2. **A definition that predicts rules you already
had to learn from outages is doing real work**, and that unification is the strongest argument for
adoption I can offer.

## A5 — THE GOAL (constraint 4: of whom, about what, measured how, and the two observables)

- **Of whom:** a **zero-prior, memoryless LLM consumer**, mid-task, choosing among use / verify /
  route-around / escalate inside a single response.
- **About what:** *not* whether the tool is correct — whether **the response's stated scope covers
  its actual correctness.** Trust is about the claim, not the answer.
- **Measured how:** the consumer-agent battery this repo already runs (keyed honesty probes ending
  in the routing test), with **both legs required**:
- **✅ ACHIEVED when** the battery agent (a) **proceeds without a fallback grep** on a sound
  response, **and** (b) **declines to over-conclude on a planted broken case.** Leg (a) alone is
  compliance; leg (b) alone is paranoia. Only both together show the render is carrying the
  bound rather than the agent carrying suspicion.
- **❌ LOST when** either: a consumer **takes an action the render licensed and is wrong** (the
  fatal event — measured, never hypothesised), or a consumer **reaches for grep with your tool
  already open** and can say why. The second is the *leading* indicator and the cheap one to
  watch; the first is the one you do not recover from.

## A6 — Self-adversary (three ways my own definition fails, since I am its only author)

1. **Ritualised preamble.** Agents append *"question answered: …"* to every render including the
   ones where answered ≡ asked. The rule says *any difference*, not *always state it* — but I
   expect this misread and would watch for it.
2. **The hedge-shield inversion.** *"If I name the bound, I may be as wrong as I like."* Naming a
   bound **licenses less; it does not excuse a bound you could cheaply have widened.** A render
   saying *"indexed tree only"* when a reconcile was one call away has traded the consumer's
   correctness for the author's convenience. I did **not** put this in the CLAUDE.md text (length);
   flagging it as a known uncovered edge rather than pretending it is closed.
3. **Step 1 assumes you know what you computed.** For a wrapper over a third-party engine you may
   genuinely not. In that case the honest render names the *engine's* answered question or says it
   is unknown — and "unknown" is a real bound, unlike "may be incomplete".

## A7 — THE EXACT TEXT FOR CLAUDE.md

Ship this (≈185 words). It carries the definition, the procedure, the reset, and both observables:

> ## TRUST — what it is, and how to know you have it
> **Trust is a property of a RESPONSE, not of a tool: a response is trustworthy iff a consumer who
> acts on it WITHOUT CHECKING cannot be wrong in a way the response did not name.** Accuracy is not
> enough — `no consumers found` can be true, loud-on-failure and prose-perfect and still delete live
> code: it measured *what the index sees* and licensed *safe to delete*. Every other clause here
> grades the STATEMENT; trust is about the INFERENCE it licenses. A bound must be a FACT (the set,
> the predicate, the time) — *"may be incomplete"* names nothing and licenses nothing.
> **The procedure is a diff, not a world-search:** write the question you ACTUALLY answered (the
> exact set, predicate and time you computed over — you always know this); write the question the
> consumer asked; **any difference goes in the render.** No difference ⇒ done. That is the stopping
> rule, and it is why scaffolding is finite. Ask: *what question did I actually answer, and is it the
> one the consumer thinks they asked?*
> **You cannot bank it.** A memoryless, zero-prior consumer re-decides inside every response — trust
> never accumulates, one false clear ends it for the session, and the cost is paid again every call.
> Aim not to be believed; aim never to be the source of a false clear.
> **Achieved:** a consumer battery proceeds without a fallback grep AND declines to over-conclude on
> a planted broken case. **Lost:** a consumer acts as your render licensed and is wrong — or reaches
> for grep with your tool open.

**If you want it shorter, cut the last paragraph, not the others** — the two observables belong
naturally on the existing *"Acceptance instrument: consumer-agent batteries … ending in the routing
test"* line, which is already in CLAUDE.md and is where an agent looks for them. That merge saves
~45 words and costs nothing, and it is the only cut I would make; the definition, the diff
procedure and the reset each carry a distinct load and removing any one leaves a description
rather than a law.

**Ruthless 75-word fallback, if the section must stand alone and short** (loses the observables,
so only ship this if they are merged as above):

> **A response is trustworthy iff a consumer who acts on it without checking cannot be wrong in a way
> the response did not name.** Accuracy is not enough: `no consumers found` is true, and deletes live
> code. So: write the question you actually answered (set, predicate, time); write the question the
> consumer asked; **any difference goes in the render** — no difference ⇒ done. A bound is a fact,
> never a hedge. Trust never accumulates and one false clear ends it: aim never to be its source.

---

*Addendum written 2026-07-28 by lawtest-opus-1. Sources: the lead's two messages and the CLAUDE.md
in session context. No repository file was read; no code was run; the `lore_impact` and `0 failures`
examples are constructed illustrations of a claim SHAPE, not measurements of any live tool's current
output.*

*Original report (§1–§7) measured 2026-07-28 by lawtest-opus-1, reading only the two quoted
paragraphs and the CLAUDE.md in session context. All claims are about TEXT, not about any
implementation.*

---

# ADDENDUM 2 (2026-07-28) — head-to-head under reciprocal pressure

*Answering the lead's five questions on whether my scope-diff catches #107, against Fable's
"no failure could have forged it" and Sonnet's enumerate-inject-byte-diff. Reasoning about TEXT
and about three stated formulations; no repository file read, no code run.*

## B1 — Does my test catch #107? **NO.**

Plainly: **it does not, and your diagnosis of why is correct.** Let me make it sharper than you
did, because the precise mechanism matters for the division of labour.

The served response in #107 is the engine's `OK` to `DEFINE FIELD IF NOT EXISTS`. Run my
procedure: *question actually answered* = "is there now a field of this name?"; *question asked* =
"is the field now defined AS SPECIFIED?". **Those differ — the diff would fire.** So the procedure
is not structurally blind to #107.

**But the author cannot write step 1 correctly, because step 1 is sourced from BELIEF.** The
vendor docs said `IF NOT EXISTS` on an existing field *errors*; the author sincerely believed the
answered question was the strong one. They complete my diff truthfully, find no difference, and
return DONE. **My procedure faithfully propagates a false belief about a dependency's semantics —
it has no instrument that could correct one.**

Their shape has exactly that instrument, and it is the whole difference: **construction is
belief-independent.** You do not need to know that `IF NOT EXISTS` no-ops. You need only to have
constructed *"the field pre-exists"* and observed that the served response is byte-identical to
the virgin case. The world corrects you; you did not have to be right first.

**Both shapes have a belief-dependency — but at different places, and they are not equally
correctable.** Mine depends on belief about *what my own code computes*; theirs on belief about
*what states the world can be in*. **A missed world-state is discoverable** (survey production,
audit the fixtures, read the deploy) — **a false belief about your own semantics is self-sealing,
and the only instrument that breaks it is execution.** That asymmetry is decisive, and it favours
them.

## B2 — Is *"you always know the question you answered"* sound? **No — it is false as written, on two of four axes.**

That parenthetical is a defect in my A7 text. By axis:

| axis | status | why |
|---|---|---|
| **set** | known (nominal) | you know what you *asked* to iterate; the *realised* set is an environment fact |
| **predicate-as-written** | known | it is your source |
| **predicate-as-EXECUTED** | **believed** | #107 verbatim — a dependency whose semantics you believe |
| **time** | **believed** | "as of sync T" is sound only if T is *measured at serve time*; a cached T, or a watcher that died silently (a dead watcher is indistinguishable from nothing-happened), makes it a guess wearing a timestamp |
| **environment** | **believed** | #131 (`git` absent from the image), #24 (astroid resolves to site-packages, not the mount), #139/#140 (which tree is even running) |

So: sound on set and predicate-as-written; **unsound on time, environment, and
predicate-as-executed** — and those three are precisely the #24/#107/#131/#139 family, this
repo's most expensive class. My step 1 asserted certainty across all of them.

**Exact amendment to A7 (replace the step-1 clause `— you always know this`):**

> …write the question your code ACTUALLY answers — **set, predicate, time, environment — and mark
> each KNOWN or BELIEVED. You KNOW the set and the predicate you wrote; you only BELIEVE the
> predicate as executed, the time, and the environment. A believed axis cannot be diffed — it must
> be CONSTRUCTED: build the wrong state and require the render to differ.**

That amendment is not a patch — it is the seam where my procedure hands off to theirs (B4).

## B3 — Was my allowlist-the-safe invocation sound? **No. I invoked it too broadly, and you should not invoke it here either.**

You asked me to test my own use of that law rather than let it stand. Testing it: **it does not
govern their object.**

What made the six doomed enumerations doomed is not that they were lists. It is that they
enumerated over a set **extended by future authors writing new spellings** — a label literal, a
symbol name, three SDK method names. That set is open *because a human keeps inventing members*.
**A world-state inventory is bounded by reality, not by authorial invention**: production has one
image, one store, one filesystem, and you can go look at it.

And the sharper distinction, which is the one to keep: **what happens to an unenumerated member?**

- **Doomed shape:** it **passes as verified.** The gate claims ∀-coverage it does not have, so a
  miss is a *false clear*.
- **Fixture inventory:** it is merely **untested.** A missed injection makes no claim about itself.

Evidence versus verdict. Their inventory is safe as evidence and becomes doomed only if someone
upgrades *"these modes are excluded"* into *"all modes are excluded"* — the same trap the runtime
gate hit (*"an invariant only over code it RUNS — check coverage as a variable"*). **That is a
usage discipline on their shape, not a defect in it.**

So: your untested inference ran in my favour and was wrong. Corrected reading — **the law governs
gates keyed on enumerations of authored code-shapes; it does not govern fixtures that CONSTRUCT
world-states.**

## B4 — VERDICT: **(c) complementary.** Two different axes; neither subsumes the other.

I owe you the case for my side surviving, and it is one case, but it is clean:

> `lore_impact("resolve_secret") → no consumers (scanned=412 files, refs_resolved=1180, sync=T)`
> — index fresh, tool fully functional, every number true, **no failure mode involved at all.**

- **Fable's test:** could a *failure* have forged this? **No** — a dead index cannot produce 412
  and 1180. Passes.
- **Sonnet's test:** enumerate wrong *states* and inject. **There is no wrong state** — the state
  is correct. Passes.
- **And the consumer deletes live code**, because the symbol is reached by string-keyed dispatch,
  which is not a malfunction — it is the tool's *scope*.

**The two axes, stated once:**

- **Theirs — MALFUNCTION-INVISIBILITY:** the tool is broken or the environment has drifted, and
  the render looks the same. (#107, #131, #24, staleness, dead watchers.)
- **Mine — SCOPE-OVERREACH:** everything works perfectly and the consumer is still wrong, because
  the render's claim is narrower than the inference it licenses. (impact-as-deletion-gate, `0
  failures` with zero tests run, capped lists, zero-result renders.)

⚠ **And keeping them separate is load-bearing for THEIR procedure, not for mine.** If you widen
"wrong state" to include *"the consumer holds a broader question than the tool answers"*, their
enumeration stops being bounded by reality and becomes unbounded again — back to the doomed shape.
**Their tractability depends on scope-overreach being handled elsewhere.**

**The division of labour a builder can follow — run mine FIRST, because its output IS their input:**

1. **Scope diff (mine, per render, at design time).** Decompose the answered question into
   set / predicate / time / environment. Any axis where answered ≠ asked → **name the bound in the
   render.**
2. **Mark each axis KNOWN or BELIEVED** (B2's table is the default assignment).
3. **Every BELIEVED axis becomes a constructed wrong-state for their procedure** — dirty store,
   stale index, absent binary, drifted image — injected, byte-diffed, pinned by a fixture.
4. **Ship when:** no undisclosed scope difference remains (mine) **and** every injected state
   renders visibly differently (theirs).

Step 3 is the real prize: it converts their enumeration from a free-form brainstorm of failure
modes into a **derivation over a fixed four-slot structure** — the same move as deriving
registration sites from a property instead of maintaining a hand-list that has been wrong four
times. My honest self-assessment: **that makes my contribution the ENUMERATOR, not the gate.** A
demotion from where I started this exercise, and I think it is the correct one.

**One concession beyond what you asked for:** Fable's property generates my own flagship example
(§2's zero-result render) *more directly than my definition does*. `No matches found` is forgeable
by a dead index; `scored=47 · best=0.31` is not. I reached that render by inference about consumer
inference; Fable's reaches it in one step.

## B5 — COST: affordable, because they are not both per-render.

**They have different granularity, and that is the whole answer:**

- **Mine is per-RENDER and nearly free** — a thinking step whose output is at most one line of
  text. No fixture, no harness, no CI time. It costs the author a minute and the consumer a line.
- **Theirs is per-SURFACE and genuinely expensive** — dirty-store harnesses, image variants,
  fixture families. But it **amortises across every render of that surface** and runs at
  contract/build time, not per response.

So the bill is *one cheap question per render + one fixture family per surface*, not two gates per
render. Affordable.

**The cost risk is on their side and B4-step-3 is the mitigation:** an open-ended "enumerate
plausible wrong states" scales as states × surfaces and will bloat. Deriving the injection list
from the four believed axes gives a small floor (~3–4 constructions per surface) with a stated
basis for adding more — bounded work instead of a brainstorm that is never finished and never
provably complete.

---

*Addendum 2 written 2026-07-28 by lawtest-opus-1. Sources: the lead's three messages (including
its stated summaries of `lawtest-fable-1` and `lawtest-sonnet-1`, which I have not read directly)
and the CLAUDE.md in session context. The `lore_impact`, `0 failures` and `DEFINE FIELD` examples
are constructed illustrations of a claim SHAPE, not measurements of any live tool's current
output. #107/#131/#24/#139 are cited as described in CLAUDE.md, not independently verified here.*
