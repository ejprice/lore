# REPORT — lawtest-sonnet-1

Reading only the TEXT supplied in the spawn brief (no other repo file read, per instructions — none of the questions below required it).

## 1 — First read, before any evaluation

Read cold, before designing a tool response, this tells me: for every served claim that has a number behind it (a rate, a derived count, an aggregate), I must attach the scaffolding that lets the *consumer* cheaply check it themselves if they choose to — the `n`, the population it was drawn from, and numbers that reconcile across related outputs. I am not being told to prove my claim to the consumer up front (that would mean dumping the underlying data), and I am not being told the consumer must verify every time (that would make trust worthless — the whole point of a trusted surface is that they usually don't). I'm being told to engineer the *middle ground*: leave a cheap, optional escape hatch. If I can't attach that scaffolding at all, the claim is in a bad category — it's asking the consumer for blind belief, and the text says that category of trust is fragile (it "dies permanently at the first false clear").

## 2 — The concrete change

One specific thing: whenever I render a "no matches" / "nothing found" / zero-result surface, I attach the *evaluated population* and the *near-miss margin* — e.g. `candidates_scored=N`, `closest_score=X`, `threshold=Y` — as sibling fields on the same response, not as a link to raw data and not omitted. That's an actual field-level change: a null/empty result gets a population count attached to it, always, even though the "interesting" number (the result set) is empty. This is the case the base TRUST paragraph's "a served count describes the whole set its label claims" doesn't force by itself — a count of zero is easy to render with no population at all ("no results"), and the addition is what specifically requires the denominator to still show up when the numerator is zero.

## 3 — The misreading probe

- **Over-application (bloat):** an agent reads "scaffolding... makes a spot-check cheap" and concludes more scaffolding is strictly better, so it starts attaching full candidate lists, raw scores, embeddings, or reconciliation trails to *every* response "just in case a consumer wants to check." That is exactly the "bulk data makes it expensive" failure the same paragraph names — the agent produces the failure mode while sincerely quoting the fix for it, because the text doesn't give a size bound on scaffolding (see §7's amendment).
- **Inversion (dropped when it shouldn't be):** "verification stays cheap and optional... for the consumer" gets silently read backward as "so *I*, the server, don't need to verify before I serve it — the consumer can check it if they care." That inverts who the optionality belongs to. The paragraph is about equipping the reader to check *my* claim, not about excusing me from checking it myself first. This is the most dangerous misreading because it looks like literal compliance ("I made it checkable!") while quietly reintroducing an unverified claim.
- **Inversion, second form:** an agent notices the population number is embarrassing (e.g., zero candidates scored, or a suspiciously round number) and omits it "because it's not really a rate" — cherry-picking exactly the case where scaffolding is most needed, while still being able to point at the letter of the rule for every case where the number looked fine.
- **Lazy reading in a hurry:** "attach an n" gets satisfied by stapling *some* integer onto the response without that integer being derived from the actual code path that produced the claim — a decorative `n` rather than a measured one. This repo's own history (PKT-28 C1, "a diagnosis is not an instrument") is full of exactly this shape: prose/numbers that describe behavior placed *beside* the behavior rather than *derived from* it. The proposed law doesn't say "derived" — it says "the population behind every derived count," trusting the word "derived" to carry weight a hurried reader will skim past.

## 4 — The boundary

A genuine unclear case: a **pure existence/boolean claim with no numeric rate at all** — e.g. `"Symbol `_apply_mint` not found."` or `"No side effects detected."` There is no rate, no derived count, no obvious "n" to attach on the face of it. Does the law bind here? Arguably yes by extension — "not found" implies an evaluated population (tiers searched, aliases checked) the same way a zero-result count does — but the text's own examples (rate, derived count, cross-artifact reconciliation) are all explicitly numeric, so nothing in the wording forces the extension.

What I would do: treat it as binding by the same logic as example (B) in §6 below — any claim that implies "we looked and found nothing" gets the same population disclosure a numeric zero would ("searched 3 tiers: exact, fuzzy, semantic; 0 candidates in each") — but I would flag this as an interpretive extension rather than silently deciding it, per this repo's own scope law (ambiguity gets surfaced, not resolved unilaterally).

## 5 — The theatre test

Partial theatre, not full theatre. The existing TRUST paragraph ("a served count describes the whole set its label claims," "no render over-claims") already forces most of what the addition asks for in the *populated* case. Where the addition is not redundant, and would change something: it is the only place that (a) explicitly names bulk-data-dump as *also* a failure, not just as an alternative virtue, which is the guardrail against the over-application misreading in §3, and (b) forces scaffolding onto the *zero/negative* case specifically (§2's concrete change), which "describes the whole set its label claims" doesn't obviously reach when the label claims an empty set. So: if I were rendering a "no matches" surface in this session, the addition would change my output — I'd add the population/near-miss fields I might otherwise have skipped since there was, in my view, "nothing to describe." That's a real, if narrow, behavioral delta.

## 6 — Discrimination

- **(A)** passes cleanly: `47 candidates scored`, `closest: 0.31`, `floor: 0.62`, `3 within 0.05 of floor` — this is exactly the scaffolding the addition asks for (population + margin), sized as a handful of fields, not a data dump. A consumer can cheaply spot-check ("is 47 plausible for this corpus? is 0.31 in the right ballpark?") or just trust it and move on — both options are live, which is the property the addition is naming.
- **(B)** fails: "consulted," "contains no relevant results," and "Confidence: high" are three assertions with zero scaffolding behind any of them — no population, no threshold, no score. There is nothing here a consumer could check without independently redoing the entire search. This is the addition's own diagnosis, close to verbatim: an unverifiable claim, leaving only blind belief.

The law **does** separate them, and it does so more precisely than the base TRUST paragraph alone would: the base paragraph's "no render over-claims" would flag (B)'s "Confidence: high" as an over-claim, but it wouldn't by itself explain *what's missing* to fix it. The addition's framing ("what would let a consumer skip verification, cheaply, if they wanted one") gives a constructive answer — add the scaffolding (A) has — rather than just a violation ("don't overclaim") with no repair instruction.

## 7 — Verdict

**Adopt with amendment.** The addition earns its place — it catches the zero-result blind spot the base paragraph doesn't force, and it's the only text that positively values a *repaired* (B), not just a rejected one. But as written it has two open holes found above: no bound on scaffolding *size* (invites the over-application bloat in §3), and no explicit statement that the server's own verification duty is separate from the consumer's optional one (invites the inversion in §3). Amendment:

> **Trust is what lets a consumer SKIP verification.** So the property to engineer is not checkability as such — it is that verification stays CHEAP AND OPTIONAL *for the consumer, never a substitute for the server's own*. Scaffolding (the `n` on every rate, the population behind every derived count including zero-count renders, cross-artifact reconciliation) makes a spot-check cheap when a consumer chooses to make one; it is a handful of fields, not a data dump — bulk data makes verification expensive, which is its own failure mode, not a stronger form of compliance. An unverifiable claim makes verification impossible, leaving only blind belief — which dies permanently at the first false clear.

**Shorter alternative, in this repo's own preferred askable form** (per `CLAUDE.md`'s "write laws as questions, not properties"):

> Before serving any claim — including a zero/negative one — ask: *could a consumer cheaply spot-check this without redoing the work, and does redoing the work themselves stay optional?* If not, attach the population/near-miss numbers that would make it so — a few fields, never the underlying bulk data.

This is shorter than the amended paragraph, and per this repo's own PKT-28 lever finding, an askable form is more likely to actually install itself at the point of use than a stated property is.

---

# FOLLOW-UP — A hard, decidable definition of trust for an MCP

Derived fresh, from the five constraints and my own experience as a tool-consuming LLM — **not** from the paragraph above. Comparison against it comes last, as instructed.

## Derivation (ignoring the reviewed paragraph)

Start from constraint 5, because it's the one that changes everything: the consumer is memoryless, single-shot, arrives with no priors, and decides within one response whether to rely on it *and whether to bother calling this tool again*. That rules out every human notion of trust (reputation earned over repeated interactions, benefit of the doubt, "they've been reliable before"). Whatever trust means here, it has to be **re-provable from the response itself, every single time, from zero**.

So ask: what, about a single response, would let a reader with zero history know whether to believe it? Introspecting on my own behavior in this transcript and generally: I don't trust a claim because it's *worded* confidently or hedged carefully. I trust it (implicitly, without checking) when I have reason to believe that **if it were wrong, it would look different.** I distrust it — regardless of how honest or well-labeled it is — when I notice that a wrong version of the world and the right version of the world would have produced the *identical text*.

That gives a test, not a description:

**THE TWIN TEST.** Take a served claim. Enumerate the tool's plausible wrong states (stale cache, empty backing store, wrong threshold, silent truncation, swallowed timeout, an off-by-one, a logic bug — anything the tool could concretely be in instead of correct). For each, ask: would this response render *differently* from the one just served? If **every** enumerated wrong state renders differently — in a way visible in the response itself, without re-deriving the answer from scratch — the claim is trustworthy. If **any** wrong state (enumerated, or later discovered) renders **identically** — a false clear — the claim was never trustworthy, no matter how accurate it happened to be at that moment.

This is mechanically testable: it's the contract-adversary's own question ("if a builder satisfied this contract perfectly but fixed nothing — or fixed it wrong — would the tests still pass?") applied to the **render** instead of the **test suite**. Enumerate wrong states, inject each one, diff the output against the correct case. A wrong state that produces an identical diff is a defect in the surface, full stop — this is the exact instrument this repo already runs on code (`mutation_proof.py`, "prove sharing by mutation," "a pin that cannot be demonstrated failing is not a pin"), pointed at served text instead of test assertions.

## Against the five constraints

1. **Decidable?** Yes, in exactly the bounded sense this repo already accepts for its other mutation gates (not exhaustive — enumerated, with a named re-open trigger for what's found later, per "WHEN YOU CANNOT CLOSE A HOLE, PIN IT"). The procedure is: enumerate wrong states → inject → diff. Pass/fail per enumerated state, not a vibe.

2. **Excludes something?** Two real, in-repo-grounded cases of *honest, accurate, and not trustworthy*:
   - **#107's exact shape** (already in this repo's law): a stale pre-migration field and a correctly-migrated field both satisfied `DEFINE FIELD IF NOT EXISTS` and rendered identically as "field present" — nothing was inaccurate, nothing lied, and it broke `brief_publish` 100% in production because the render could not distinguish the two true states.
   - **A `lore_impact`/`dead_code` result computed against a stale, unreconciled index** — this repo's own "check, then trust" protocol exists *because* a correct-looking "12 dead functions" render is textually identical whether the graph is fresh or stale. Honest today, structurally untrustworthy as a surface.

3. **Already covered by the existing checklist?** No — and #107 is the proof. #107 had a **loud failure eventually** (it broke in production), an **accurate count** (the field genuinely existed), and **matching prose** (nothing claimed otherwise) — all three checklist properties were arguably intact right up until the outage — and it was still not trustworthy, because none of "loud / accurate / matching" asks the one question that matters: *do the tool's different possible true states project onto the same text?* That question is new work, not a restatement.

4. **The goal, in the achievement sense:**
   - Trust **of**: any LLM agent calling this tool cold, no session memory, no priors beyond the tool description and this one response.
   - **About**: a specific rendered claim (a count, an existence assertion, a confidence label, a completeness claim).
   - **Measured how**: mutation-test the render — enumerate the tool's plausible wrong states, inject each, diff against the correct-case render.
   - **Observable of having it**: every enumerated wrong state renders visibly differently from correct — a field changes, a flag appears, an error surfaces — discoverable from the response alone.
   - **Observable of losing it**: any wrong state, enumerated or newly discovered in production, collapses to an indistinguishable render — a false clear. A newly discovered collapse is a re-open trigger (re-enumerate, re-test), never a retroactive pass.

5. **Survives the memoryless-LLM consumer?** Yes — by construction. This is the whole reason I started from constraint 5 rather than from "cost of verification." A property that depended on the consumer's history, patience, or accumulated goodwill would fail the moment the consumer is stateless. Distinguishability is checked once, by the builder, before the first call ever happens — it doesn't need the consumer to do anything at all.

## Anti-anchoring comparison

**Not a restatement, but not independent either — related, and I think more fundamental.** The reviewed paragraph frames trust as a *spectrum*: verification can be cheap, expensive, or impossible, and the goal is to push toward cheap. My definition is a *boolean gate* one level underneath that spectrum: **before "how expensive is verification" is even a meaningful question, verification has to be *possible at all* — i.e., a wrong state has to leave a trace.** The reviewed paragraph's own worst case — "an unverifiable claim... leaving only blind belief" — *is* my failure condition, described in the same words, but stated as a state you can fall into rather than a property you can test pre-ship. I turned that one clause into the entire definition, because it's the only part of the paragraph that is actually decidable per the operator's constraints; "cheap and optional" is a real, valuable design quality, but it's a *cost* judgment, not a *possible/impossible* one, and cost judgments aren't decidable in the same hard sense — reasonable builders will disagree on where "cheap" ends and "expensive" begins, but nobody can reasonably disagree about whether two runs produced byte-identical output.

**Verdict on the reviewed paragraph:** it wasn't aiming at the wrong property, but it was aiming at a *downstream* one and calling it "trust." I'd split it explicitly: **distinguishability (this document) is the hard trust gate — decidable, exclusionary, survives a memoryless consumer.** "Cheap and optional verification" is a real, separate, *softer* quality — call it verification ergonomics — that only becomes a meaningful question once the hard gate is already passed (a claim that's impossible to verify has no "cost of verification" to optimize; the cost is infinite). Recommendation: put the hard definition below in CLAUDE.md as the trust law; keep the reviewed paragraph (amended per §7 above) as a secondary, explicitly-labeled design-quality note, not as the definition of trust itself.

## Exact text for CLAUDE.md

> **TRUST — HARD DEFINITION (operator, 2026-07-28).** A claim is trustworthy to an LLM consumer (memoryless, single-shot, no priors) iff every plausible wrong state of the tool — enumerated, then actually mutated/injected — renders DIFFERENTLY from the correct state, visibly, with no re-derivation needed. It fails the instant any wrong state (known or newly found) renders IDENTICALLY to correct — a false clear (#107: two true world-states, one render). This survives where "loud failure + accurate count + matching prose" does not: #107 had all three and was still untrustworthy, because none of them ask whether DIFFERENT true states collapse to the SAME text. Goal: mutation-test every enumerated wrong state pre-ship; a later-discovered collapse is a re-open trigger, not a retroactive pass. Cost-of-verification (cheap vs. expensive, once distinguishable) is a separate, softer quality downstream of this gate — not the gate itself.

~135 words. Shorter alternative if brevity outweighs completeness (drops the exclusion example and the ergonomics-vs-gate split, keeps only the test):

> **TRUST TEST.** A served claim is trustworthy iff every plausible wrong state behind it — enumerated, then injected — renders visibly differently from the correct state. It is untrustworthy the instant any wrong state (known or new) renders identically — a false clear. Mutation-test the render, not just the code, before shipping.

---

# HEAD-TO-HEAD FOLLOW-UP — twin test vs. Opus's stopping rule (2026-07-28)

Adversarial, as instructed. Conceding where the concession is real.

**1 — Is the `mutation_proof.py` analogy sound? No — concede it.**
`mutation_proof.py`'s bound is mechanical: `--collect-only` enumerates every test node id, a closed set derived from the suite itself, zero judgment required. My "enumerate plausible wrong states" (stale cache, empty store, off-by-one…) is not derived from anything — it's a *curated* list built from domain judgment, which is exactly the "enumerate the forbidden" move this repo's own instrument-lesson table shows failing six times running. The only part of my procedure that's genuinely mechanically bounded, like real mutation testing, is AST-level code mutation (flip a comparator, change a constant) — and that covers logic bugs only. My two strongest exclusion examples (#107, stale-index) are *environmental* failure modes that don't come from AST mutation at all — they come from imagining operational states, the open-world kind. The analogy fails exactly where I leaned on it hardest. Opus is right.

**2 — Does Opus's test catch #107? Your reading is correct — and here's the sharper reason.**
Opus's step 1 states as an axiom: "write the question you actually answered… you always know this; it is a fact about your own code." #107 *is* the counterexample to that axiom — the author's sincere belief was that the migration applied; the true behavior (`IF NOT EXISTS` no-ops on an existing field) was the opposite, reinforced by vendor docs that actively lied the same direction. Answered honestly by someone honestly wrong, step 1 writes the same thing the consumer wanted, and step 3's diff finds nothing — not because the diff logic is broken, but because its input was false. This is structural, not a wording nit: Opus's procedure is pure reasoning — nothing in it ever executes the code — so a confidently wrong belief has no mechanism to be corrected before it's compared.
I should not overclaim the fix, though: my enumeration step has the *identical* vulnerability — if nobody knows `IF NOT EXISTS` no-ops, nobody enumerates "silent no-op on existing field" either. The real asymmetry is narrower than "mine catches it": mine has an *execution* step that can catch the bug by routine coverage even without anyone knowing the specific quirk (run every migration against a pre-existing store, not just a fresh one — ordinary hygiene this repo already names: "the test environment is a fiction… a fixture that guarantees a clean slate cannot test what only happens on a dirty one"). If that scenario is in the injected set, the *observed* behavior diverges regardless of belief. Opus's test has no analogous accidental-discovery path, because nothing in it ever runs anything.

**3 — Does mine need a consumer model? Real advantage, but not free.**
Yes on both counts. Opus's step 2 needs "the question the consumer asked" — for a tool serving an open set of callers with open intent, that's often a judgment call the tool can't safely make (assuming an intent it doesn't have is its own hazard — structurally the same shape as a contract author silently picking between two spec readings). Mine needs no consumer model: distinguishability is a property of the tool alone. But the trade cuts back the other way — a tool can be perfectly state-distinguishable (passes mine) while silently answering a narrower question than asked (only searched tier 1, never said so) — mine is blind to exactly that, and it's exactly Opus's target, and exactly what the *original* base CLAUDE.md TRUST clause ("a served count describes the whole set its label claims") was already gesturing at. The no-consumer-model property is an advantage in *cost*, bought by ceding an entire failure axis to Opus.

**4 — Verdict: complementary, not subsuming — because they instrument two independent axes.**
- **Opus = SCOPE-HONESTY.** Assumes accurate self-knowledge; checks disclosed scope against requested scope. Catches: silent narrowing, hedges that name nothing, promising more than delivered. Blind to: a sincerely wrong self-report (#107).
- **Mine = STATE-DISTINGUISHABILITY.** Assumes nothing about self-knowledge; checks whether different true internal states hide behind the same text. Catches: silent no-ops, stale-index collapse, empty-vs-broken conflation. Blind to: a tool that's perfectly self-consistent and honestly reported, but answers a narrower question than was asked.
Each fails independently of the other (shown both directions above) — that's the proof, not an assertion.

**Division of labor, concrete enough to build from:**
- **Build/ship time, per TOOL, not per render:** run the twin test. Enumerate the tool's known failure classes (start from this repo's own landmine list — staleness, empty store, off-by-one, silent truncation, swallowed exceptions — a curated checklist, not a completeness proof, same status as the contract-adversary's boundary-case list), inject each, confirm the render differs. Re-run on logic or dependency-semantics changes. Never per-call.
- **Design time, per RENDER TEMPLATE, then free per call:** run the scope-diff once, building the template — state the exact predicate/scope/time actually computed vs. the plausible ask, bake any gap into a fixed field (`scope:`, `tiers_searched:`, `n:`). Once it's in the template, every future call gets the disclosure for free.

**5 — Cost: not both per-render.**
Twin test: per-surface, build/ship time and on logic changes — never per-call (re-executing injected failure states live would multiply serving cost by the enumerated-state count). Scope-diff: per-render in principle, but cheap in practice because it's amortized into the template at design time — marginal per-call cost is a few extra fields, not a reasoning pass.

**One more jab, in the spirit asked for:** Opus's stopping rule bounds the *diff* (step 3) — genuinely cheap, genuinely mechanical. It does not bound step 2, "the question the consumer asked" — for a tool with an open set of callers, that's exactly the judgment call my enumeration step is, just relocated one line earlier. Calling step 3 "the stopping rule" is true, but it understates that step 2 is where the hard, unbounded part of the problem actually lives for both of us.

**If useful — combined law, short:**
> **TRUST — TWO AXES.** Scope-honesty (design-time, per template, free per call): state the exact predicate/scope/time you computed, diff it against what was plausibly asked, name every gap as a field. State-distinguishability (build-time, per tool, before shipping): enumerate this tool's known failure classes, inject each, confirm the render differs from correct — a collapse (enumerated or newly found) is a false clear and a re-open trigger. Neither subsumes the other: #107 passed a sincere scope-honesty check and failed distinguishability; a silently narrow search passes distinguishability and fails scope-honesty.

