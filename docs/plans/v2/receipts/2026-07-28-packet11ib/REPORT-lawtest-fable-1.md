# REPORT-lawtest-fable-1 — law-text reading test: the "cheap and optional verification" addition

brief-base v7 read
state: done
deviations: none — read-only; this report is my only written file. Brief did not name brief-base as a first step; I read it anyway per standing law and say so here.
Packages considered: none — no mechanism specified
decisions-needed: adopt-with-amendment recommended (§7); exact replacement wording given there
receipt pointers: §6 (discrimination pair analysis, incl. the pair the brief's own pair does not isolate) · §7 (amendment text)

Answers in the required order. Q1 was written before Q2–Q7 were considered.

---

## 1 — First read (what it requires me to do)

When I design a served surface, every derived claim I serve must carry the small handle
that would let a consuming agent verify *that one claim* cheaply, if it chooses to: a rate
carries its `n`; a derived count names the population it was computed over; artifacts that
describe the same thing carry enough shared identity to be reconciled against each other.
I must not achieve this by attaching the underlying data wholesale — that makes checking
expensive, which defeats the point. And I must never serve a claim with no verification
path at all. The target state: consumers normally *skip* verification, and the reason they
safely can is that any single claim could be spot-checked at trivial cost.

## 2 — The concrete change

Concrete field: a no-consumers render from an impact-style tool. Without the addition I
would serve `no consumers found` (honest, loud). With it I would serve
`no consumers found (0 hits across 412 indexed reference edges; graph synced 2m ago)` —
the population (412 edges) and currency stamp are the scaffolding that lets a consumer
distinguish "genuinely unconsumed" from "the search was degenerate" without re-running
anything. The existing trust law alone never made me add the `412`; only the addition does.

## 3 — The misreading probe

- **Over-application (bloat):** an agent bolts `(n=…, pop=…, synced=…)` onto *every line*
  of *every* render — including claims that are self-verifying from what is already on
  screen. The scaffolding becomes the bulk data the text warns against, and every consumer
  pays the token tax the parent law exists to prevent. The text gives no stopping rule, so
  a diligent agent has no licensed place to stop.
- **Inversion (the dangerous one):** "verification stays **OPTIONAL**" read as optional
  *for the producer*. The parent law demands prose match **measured** behavior; this
  addition can be read as relaxing "measured" to "measurable" — *I gave you the `n`,
  checking is your job now.* Worst form: a mechanically sprinkled or copied-through `n`
  that was never itself measured. That is scaffolding that lies, and it makes the false
  clear *more* convincing — the addition's own "dies permanently" failure, armored by
  compliance with the addition.
- **Second inversion:** "the property to engineer is **not checkability as such**" read as
  license to *drop* checkability work without replacing it with anything.
- **Lazy reading:** "add `n=` to numbers" as a checkbox. "Cross-artifact reconciliation"
  is undefined in the text; a hurried agent either skips it or invents citation cross-links
  (a known dangling-address generator in this repo).

## 4 — The boundary

A count served *alongside its full members*: `3 results` followed by the 3 results. Is
that a "derived count" owing a population ("3 of 47 scored"), or is it self-verifying —
the consumer counts three lines? The text says "the population behind every *derived*
count" and does not say what counts as derived. Same ambiguity for non-numeric served
claims: does a reject message ("name must be non-blank") or a verbatim-recalled memory owe
scaffolding, and what would it even be?

What I would do: apply the askable test the text implies but never states — *"what would
it cost the consumer to spot-check just this claim from what's on screen?"* If the answer
is "a glance," no scaffolding; if "re-run my query," add the handle. For a one-render
detail I would decide by that test and note it; for a whole *class* of surface (e.g. all
reject prose) I would surface the fork rather than settle it silently.

## 5 — The theatre test

Honest answer: **partially.** For most of what the parent law already governs — loud
failure, no over-claiming, label-matches-set — I would have done the same thing anyway;
those clauses already force honesty. The addition's real marginal behavior is narrower
than its word count: it changes *which fields I include*, specifically the population /
`n` / near-miss fields I would previously have judged to be noise and omitted (the `412`
in §2, the `47 candidates; 3 within 0.05` in §6). That is a real delta, but it is one
sentence of delta carried by an ~80-word paragraph. The skip-verification framing and the
"dies permanently" clause are rationale, not behavior — I can find no decision they change
that the operative clause doesn't already change.

## 6 — Discrimination

- **(A)** passes: the failure is loud, and every claim carries its handle — the floor
  (0.62) makes "no matches" checkable against the closest score (0.31), the population
  (47 scored) rules out a degenerate search, the near-miss count (3 within 0.05) prices a
  re-query. A consumer can spot-check any of it from the render alone. Cheap and optional.
- **(B)** fails: "Confidence: high" is an unverifiable claim — no floor, no scores, no
  population, nothing it could be checked against. "The index was consulted" asserts a
  whole-set property with no handle on the set. Only blind belief is on offer, which is
  exactly the state the addition says dies at the first false clear.

So yes, the law separates them — **but so does the parent law, on its own.** B already
violates "no render over-claims" and "teaching prose matches measured behavior"; this pair
therefore does not isolate the addition's marginal content. The pair that does:
**(A)** vs **(A′)** `No matches above threshold (floor 0.62).` — honest, loud,
non-over-claiming, passes every clause of the existing law; fails only the addition,
because it offers no handle for "was the search degenerate?" (no population, no closest
score). The addition's whole job is separating A from A′. It does.

## 7 — Verdict

**Adopt with amendment.** The insight is real and it changed a concrete field choice (§2,
§6 A-vs-A′). But as written it is stated as properties, not as a question an agent can ask
mid-task (this repo's own LEVER law predicts properties don't install); it leaves the
producer-side inversion door open (§3); and roughly half its words are rationale the
parent law already carries.

Exact replacement text:

> **Trust is what lets a consumer SKIP verification — so every served claim carries the
> one cheap handle needed to spot-check it** (the `n` behind a rate, the population behind
> a derived count, the floor behind a miss) — never the bulk data behind it, and never a
> bare claim, which demands blind belief and dies at the first false clear. The askable
> form: *"what would it cost the consumer to check just this line?"* — if the answer is
> "re-run my query," the handle is missing. Optional is the **consumer's** option only:
> the producer still measures everything it serves.

Shorter sentence that does most of the work (if length must be minimal):

> **Every served claim carries the one cheap handle a consumer would need to spot-check
> it (`n`, population, floor) — never the bulk data, never a bare claim.**

The one-sentence form loses the producer-inversion guard (§3's most dangerous misreading),
so I recommend the three-sentence form. If forced to one sentence, append ", and the
producer has still verified it" — six words that close the worst door.

---

## 8 — FOLLOW-UP (stamped 2026-07-28): a hard, decidable definition of trust for an MCP

**Derivation path, declared first for the anti-anchoring audit:** I did not start from the
reviewed paragraph. I started from constraint 5 (the consumer is an LLM deciding inside one
response, no priors) plus the observable that actually governs my own behavior as a tool
consumer: I corroborate or route around a response exactly when I cannot tell the tool's
answer from the tool's failure. Then I dualized this repo's own lever — "what WRONG BUILD
would still pass this test?" — onto the serving side. The comparison to the paragraph is in
§8.6, after the definition, in that order deliberately.

### 8.1 The definition

**A response is trustworthy when no failure of the tool could have forged it.**

Expanded: for every way the tool can degrade — stale index, wrong tree, empty store, silent
truncation, coerced/malformed query, partial permission view — the response a consumer holds
is *distinguishable, from its text alone*, from what that degraded run would have served.
Trust is not a property of being right; it is the property that **being wrong could not have
looked like this.** That is the only property an amnesiac consumer can use: with no memory
and no priors, it can safely act without corroborating *only* on what failure cannot mimic.

### 8.2 The decision procedure (constraint 1)

Per served surface, askable mid-task:

> **"What degraded run of this tool would serve a response indistinguishable from this
> healthy one?"**

- Every mode you can name gets ONE of: a loud, *distinct* error — or content in the healthy
  response that excludes it (provenance: what set was consulted, measured when, by what
  method).
- Each resolution is **pinned mechanically**: a fixture CONSTRUCTS the failure (don't
  reconcile the index; empty the store; force truncation) and asserts the served response
  DIFFERS legibly from the healthy one. This is a byte-diff of two captured responses —
  fully decidable, no judgment call.
- **Coupling rule** (the structural form of §3's find): the excluding content must be
  produced *by the run it describes* — a sync-age read from the store's clock at query
  time, an `n` counted in this scan. Content copied from config, cache, or a prior run is
  forge-armor: the degraded run carries the same handle, and the pin above will catch it
  (the constructed failure serves identical bytes → RED).

**Bound, stated honestly:** the failure-mode inventory is never provably complete —
absolute non-forgeability is unattainable (a bug replaying a cached healthy response
verbatim forges anything). So ACHIEVED is defined *relative to the written inventory*,
per this repo's pin-the-bound law, with the standing re-open trigger in §8.3. That is not
a weakness of the definition; it is the definition refusing to over-claim about itself.

### 8.3 The goal, in the achievement sense (constraint 4)

- **Trust of whom:** the consuming LLM agent, per response.
- **About what:** that acting on the response *without corroboration* is safe.
- **Measured how:** producer-side — the surface's failure-mode inventory exists as a
  written artifact and every entry's distinguishability pin is green. Consumer-side — the
  existing acceptance instrument (consumer-agent batteries, CALL_AGAIN vs ROUTE_AROUND,
  packet 03b §C5): no new machinery needed; this definition plugs into it.
- **ACHIEVED (yes/no, self-decidable):** inventory written + all pins green. An agent
  finishing a surface can answer this about its own work and be right.
- **LOST:** one **false clear** — any corroboration, audit, or downstream failure that
  contradicts a served response that looked healthy. That event is a STOP, not a bug to
  quietly fix: it *names an inventory gap* and mints the missing entry + pin.

### 8.4 What it excludes (constraint 2)

Surfaces that are honest, accurate, and NOT trustworthy under this definition:

1. **`No matches found.`** on a healthy index with genuinely no matches. Honest. True. Not
   trustworthy: byte-identical to what the same tool serves over a stale index, a wrong
   watched root, or an empty store. Its truth is a fact about the world that the response
   gives the consumer no way to distinguish from the tool's most common failure.
2. **Scaffolded-but-decoupled:** `0 hits (412 edges, synced 2m ago)` where the sync-age is
   read from a stamp the degraded path also serves. Richer, still forgeable — fails the
   coupling rule and its pin.

(2) is the case the reviewed paragraph cannot exclude, which matters for §8.6.

### 8.5 Does it reduce to existing law? (constraint 3)

No — and the boundary is sharp. Existing law ("failures are LOUD, counts describe their
set, prose matches measured behavior") governs **failures the tool detects** and the
honesty of what it says. This definition governs **failures the tool does NOT detect** —
degradations that produce healthy-*looking* output. An MCP can satisfy every existing
clause perfectly — every caught error loud, every count accurate, all prose measured — and
still serve §8.4's example 1, because staleness was never detected and honesty was never
violated. The addition is exactly: *the success path must be non-forgeable by the failure
paths.* That is not in the current law.

### 8.6 Anti-anchoring comparison (required declaration)

**Independent in derivation; overlapping in prescription; contradicts the paragraph at one
load-bearing point; and it relocates the aim.**

- *Overlap:* the paragraph's scaffolding (`n`, population, floor) is usually the very
  content that does the excluding in §8.2. Both laws would produce response (A) from §6.
- *Contradiction:* the paragraph, complied with to the letter, ADMITS scaffolding that was
  never measured — my §3 inversion required an added guard clause to close. Under this
  definition that case is excluded **by construction**: decoupled scaffolding fails its
  distinguishability pin, no guard clause needed. A definition that structurally forbids
  the worst misreading of the other is not a restatement of it.
- *Relocation:* the paragraph aimed at the consumer's **checking cost**; the property that
  actually licenses skipping the check is **forge-resistance**. Cheap verification is a
  *consequence* (the excluding content sits in the response, so the "check" is a glance),
  not the target. The paragraph's own strongest clause — "dies permanently at the first
  false clear" — was pointing at the right thing: **the false clear, not the check-cost,
  is the load-bearing event**, and the definition should be built on it. So: not aiming at
  the *wrong* property, but aiming at its shadow.
- *LEVER check on my own output:* the definition ships AS an askable question (§8.2), and
  it is the consumer-dual of a question agents in this repo already ask, so it installs on
  existing reflexes. It still satisfies constraint 1 because the question's answer is
  settled by a byte-diff fixture, not by feel.

### 8.7 Exact CLAUDE.md text

> **TRUST, DEFINED (operator, 2026-07-28): a response is trustworthy when no failure of
> the tool could have forged it.** The consumer is an LLM with one response and no priors;
> it can act without corroborating only on what failure cannot mimic. `No matches found.`
> — honest, true — is untrustworthy while a stale index serves the same bytes. Askable,
> per surface: **"what degraded run (stale index, wrong tree, empty store, truncation,
> coerced query) would serve THIS response?"** Every nameable mode gets a loud *distinct*
> error, or excluding content in the response (what set, measured when, by what method) —
> produced BY the run it describes, never copied from config or cache — plus a pin that
> CONSTRUCTS the failure and asserts the served response differs. **ACHIEVED** = the
> surface's failure-mode inventory is written and every entry's pin is green — a builder
> can answer this about its own surface, yes or no. **LOST** = one false clear (a
> corroboration contradicts a healthy-looking response) — a STOP that names an inventory
> gap and mints its pin, never a quiet fix. The inventory is a pinned bound, never
> provably complete; its standing re-open trigger is every false clear, audit find, and
> vendor gotcha.

(~160 words. If it must shrink, cut the parenthetical failure-mode list and the example
sentence — in that order; the example is worth more than the list.)

*Stamped 2026-07-28, lawtest-fable-1, follow-up to the §1–§7 reading test above.*

---

## 9 — HEAD-TO-HEAD vs `lawtest-opus-1` (stamped 2026-07-28)

Position up front: **two concessions, one refusal, each with a receipt.** Verdict is (c),
complementary, with the exact division in §9.4 — and I concede the *definition sentence*
to Opus while refusing its *stopping rule*.

### 9.1 — Q1: the stopping rule, and my bound

**Partial concession.** My §8 procedure as first stated — "enumerate the failure modes" —
is an open brainstorm, and Opus's attack lands on that form: an open enumeration of bad
worlds is forbidden-set shaped. My "never provably complete" bound was the smell of that
shape, and it can now be substantially closed — **but not by Opus's move. By combining
both moves:**

Derive the inventory instead of listing it. A surface's failure modes are generated by its
**stateful dependencies** — the external state the handler reads (index, store, filesystem,
clock, subprocess), which is a small set **readable off your own code** (Opus's own step-1
insight, aimed at the right target) — crossed with a fixed degradation algebra:
**{stale, empty, wrong-instance, partial}**. Dependencies × algebra is safe-set shaped:
small, enumerable, derivable (this repo's `registration_sites.py` precedent — derive sites
from a property, don't hand-list them; the dependency list is AST-scannable and pinnable).
Residual incompleteness — degradations outside the algebra — remains, bounded by the
false-clear re-open trigger. So: the bound shrinks from "unknown unknowns of an open
brainstorm" to "novel degradation verbs," which is as closed as this gets.

**Does Opus's shape remove the need for the inventory? No — and this is the refusal.**
Its diff runs over *sincere self-description*, and undetected degradation is *precisely*
the divergence between sincere self-description and runtime reality. See §9.2.

### 9.2 — Q2: does Opus's test catch #107? **No. Your reading is confirmed, and it's worse than that.**

"Write the question you ACTUALLY answered — *you always know this; it is a fact about your
own code*" is **false exactly where this repo's two production outages lived.** The
question actually answered is a fact about **runtime state**; the code's *belief* about
runtime state is the thing degradation falsifies:

- **#107:** the actual predicate was the engine's live ASSERT, which the `IF NOT EXISTS`
  no-op left stale. The author's step-1 would sincerely write the widened predicate. Diff:
  clean. Consumer: wrong in a way the response did not name.
- **#131:** step-1 would sincerely write "I read git provenance." The image had no git;
  the OSError was swallowed. Diff: clean. Same result.

**So Opus's definition and Opus's procedure come apart:** the definition correctly
classifies both responses as untrustworthy (unnamed wrongness), while the procedure
certifies them DONE. The stopping rule is unsound with respect to its own definition. It
is this repo's recipe/cake law: step-1-from-source proves the RECIPE; only content read
back from live state proves the CAKE. To make step 1 honest under degradation you must
render self-description *produced by the run it describes* (my coupling rule) — and
knowing WHICH parts of self-description can silently diverge from source is the
dependency-derived inventory of §9.1. The diff needs my machinery to be sound; it cannot
replace it.

### 9.3 — Q3: does allowlist-the-safe govern the inventory? Genuine reading

**It governs my first form; it does not govern the derived form — because they are
different kinds of object.** The six defeated instruments were *gates over adversarial
spelling-spaces*: their job was to block every spelling of a forbidden thing, one missed
spelling = silent total failure, and the space of spellings is unbounded. The
dependency-derived inventory is a *coverage ledger over a cooperating system's own
architecture*: the generator set (what state this code reads) is small, closed, and
readable off the code — it IS the safe-set side; each entry closed has standalone value
(unlike a name-list, where value is all-or-nothing); and a miss has a built-in detector
(the false clear) rather than silence. Opus invoked the right law against the wrong
object — but it was aimed at the form I actually wrote, so the attack did real work: it
forced §9.1's derivation. Credit where due.

### 9.4 — Q4: verdict — **(c) complementary**, with the division exact

**Concession 2: Opus's definition sentence is the better umbrella.** There is a case mine
misses that Opus's catches: **healthy-path scope mismatch** — the tool does exactly what
it was designed to do, but the design answers a narrower question than the label implies
(search silently excludes tests; consumer assumes the whole tree). No failure forged
anything, so my definition passes it; the consumer is wrong in an unnamed way, so Opus's
fails it — correctly. Mine covers only the degraded path; Opus's sentence covers both.
Its "trust does not require being right" (a named bound that gets hit breaks no trust) and
"a hedge is not a bound" clauses are also correct and worth keeping verbatim.

**Division of labour — both gates are per-surface, at build time:**

| | **Opus's diff** | **My forgery pins** |
|---|---|---|
| path | HEALTHY: design ≠ label | DEGRADED: runtime ≠ design |
| runs | once per surface, at design: question-answered (set/predicate/time, from source) vs question-implied; every delta → render fields | once per surface, at build: dependencies (from code) × {stale, empty, wrong-instance, partial} → one constructed-failure fixture each, served bytes must differ legibly |
| stopping rule | no delta ⇒ done — **valid here**, because on the healthy path source IS ground truth | all derived cells pinned ⇒ done; algebra gaps bounded by false-clear trigger |
| blind spot | #107/#131 — sincere self-description diffs clean | scope mismatch — no failure exists to construct |
| joint seam | the diff's rendered deltas ARE self-description; the coupling rule (produced by the run, never config/cache) is what keeps them honest under degradation — pinned by the fixtures |

Builder's order: diff first (it decides *what the render must say*), pins second (they
prove *the render can't be forged saying it*).

### 9.5 — Q5: cost

**Affordable, because neither is per-render.** Both gates are per-surface, build-time,
one-shot: the diff is minutes of prose plus render fields; the pins are fixtures — the
only expensive half, and they were already the cost of my §8 alone. The render fields
overlap almost entirely (Opus's "time you computed over" IS my coupling stamp), so
adopting both adds **one design question and zero runtime cost** over adopting either.
Per-render burden: unchanged — the same fields either law would have mandated. If forced
to cut one anyway: keep the pins on surfaces with stateful dependencies, keep the diff
everywhere (it's nearly free) — but nothing measured here forces that cut.

**Merged CLAUDE.md text, if the lead wants one artifact** (Opus's sentence as umbrella,
both procedures as the two legs, ~130 words):

> **TRUST, DEFINED: a consumer who acts on a response WITHOUT CHECKING cannot be wrong in
> a way the response did not name.** A named bound that gets hit breaks no trust; a hedge
> names nothing ("may be incomplete" is not a bound). Two gates, per surface, at build
> time: **(1) the diff** — write the question you actually answered (exact set, predicate,
> time) against the question your label implies; every delta goes in the render; no delta,
> done. **(2) the forgery pins** — the diff trusts your self-description, and degradation
> falsifies it sincerely (#107, #131): derive the surface's stateful dependencies from the
> code, cross with {stale, empty, wrong-instance, partial}, pin each — construct the
> failure, assert the served response differs legibly, and every self-describing field is
> produced BY the run it describes, never copied. **ACHIEVED** = diff clean + derived pins
> green. **LOST** = one false clear → STOP; it names the missing cell and mints its pin.

*Stamped 2026-07-28, lawtest-fable-1, head-to-head follow-up to §8.*
