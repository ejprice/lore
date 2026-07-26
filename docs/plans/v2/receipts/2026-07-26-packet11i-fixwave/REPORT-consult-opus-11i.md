# REPORT-consult-opus-11i — client-needs consult: absence verdicts and their calibration

**Role:** informant, not engineer. **Blind as instructed:** I read no repository file, ran no
search, and did not look at any implementation. Answers are from my own experience of using
code-search tools.

**Leak disclosure (matters for your diff):** project instructions were auto-loaded into my
context and they contain the phrase *"check, then trust"* plus the idea that a freshness/status
surface exists on some index tool. I noticed a live impulse to go look at that surface before
answering — flagging it per instructions, and I did not look. But be aware my Q1/Q3 emphasis on
**staleness as the dominant trust variable** may be partly seeded by that leak rather than
purely mine. Everything else I believe is uncontaminated.

**Epistemic marking convention used below:** `[remembered]` = an actual recalled pattern of
being misled or well-served by a tool. `[constructed]` = a preference I am reasoning out right
now and have not lived. I have tried to be strict about this; where I could not tell, I say so.

---

## 1. The verdict itself — what makes "no strong match" actionable

A "no strong match" claim is only ever a statement about the *search*, never about the
*repository*. To act on it instead of grepping, I need the search made inspectable. Four things,
in descending order of how much they change my behaviour:

**(a) The rejected candidates, with scores.** This is the single most valuable item and it is not
optional. Show me the top 3–5 hits *even though* they fell under the floor. Reason
`[remembered]`: when a semantic search comes back empty or weak, the near-misses tell me
instantly which of two worlds I'm in — "the tool understood me and the concept isn't here" vs
"the tool matched on the wrong axis and my query was the problem." In the second case I
reformulate, which is cheap and keeps me in the tool. A bare verdict with no candidates is
unfalsifiable, and unfalsifiable output is what I route around. Suppressing weak hits to look
decisive is the worst possible trade here.

**(b) What was actually searched, inside the sentence.** Count and kind of indexed units, and
whether the index is current with the tree. `[remembered]` The most common way a zero-result has
misled me is not a bad threshold — it is a **scope gap I could not see**: a path filter I didn't
realise was applied, tests not indexed, a vendored directory excluded, a file type the parser
skipped. From outside, "genuinely absent" and "never indexed" render identically, and once burned
you assume the latter forever. So scope belongs in the verdict, not in a footer.

**(c) Freshness, as a verdict rather than a date.** "Calibration and index are current with the
tree" is worth more to me than every number in question 3 combined. Its negation — "the tree has
moved since the index was built" — means I skip the verdict entirely and go straight to grep,
correctly and without resentment. `[remembered]` Fear of staleness, not staleness itself, is what
makes me abandon an index tool; a tool that reports its own currency removes the fear cheaply.

**(d) The domain caveat, when applicable.** "Semantic absence is not textual absence." If my
query looks like an exact string — a config key, a log event name, an error message fragment, a
retired symbol I'm sweeping for — the honest output is *"I am the wrong instrument for this; a
semantic floor cannot certify exhaustiveness."* A tool that names its own limits gains trust it
can spend elsewhere. `[constructed, but strongly held]`

**What would NOT earn trust:** stronger prose ("definitively not present in the codebase");
an unadorned `0 results`; a verdict with candidates hidden; any implicit claim of exhaustiveness;
and above all a phrasing that is *shared* between "I looked and it isn't there" and "I couldn't
look."

**One addition that would actually change my behaviour more than the verdict does.** Absence is
the moment I am most likely to leave. So make the absence path a **handoff, not a terminus**:
name the next instrument concretely — the grep that would settle it, the scope/tier I did not
search, a reformulation derived from the near-misses. `[remembered]` I have been well served by
tools that told me what to do next after failing, and those are the tools I kept calling.

---

## 2. The six states — which are real from my side

Collapsed honestly, the six states become **four surfaces**, plus one rule about failures.

| Your state | My surface | Why |
|---|---|---|
| measured & adopted | **verdict live** | I can act on absence. |
| never measured | **no verdict available** (transient) | Identical to me. |
| measured, not adopted | **no verdict available** (transient) | Identical to me. |
| measuring now | **no verdict available, will change** | Only if the retry is actionable. |
| corpus too small | **no verdict possible here** (structural) | Permanent property — distinct, and useful. |
| feature disabled | **no verdict, by choice** | Human-actionable — distinct, and useful. |
| failed | **must be announced as a failure, once** | Never laundered into "unavailable." |

Distinctions I would genuinely use:

- **verdict live vs not** — the only one that matters most of the time. One clause: *"ranked hits
  only; no calibrated floor for this corpus, so no absence claim."* That is enough for me to
  behave correctly.
- **structural (too small / no separation) vs transient** — high value, because it tells me not
  to wait, not to retry, and to expect this forever for this corpus. It also reads as honesty and
  buys trust globally.
- **disabled** — worth one clause naming the switch, because a human can flip it and I can ask.
  Conflating it with "failed" would be a small lie.
- **failed** — the *fact* is load-bearing even when the reason is beyond me. A failure silently
  presented as absence-unavailable is the beginning of not trusting the tool's negatives at all.
  One line, one reason, loud, not repeated on every subsequent call.

Distinctions that are **the tool talking to itself**:

- **never measured vs measured-but-not-adopted.** From my side these are the same state. The
  adoption decision is the tool's internal quality control and I should not have to hold it.
  *One exception:* if the rejection reason was *degenerate measurement / insufficient separation*,
  that is the same information as "corpus too small" and should be said in those words — as a
  property of the corpus, not as a state of the tool's decision process.
- **measuring now, without retry semantics.** "Calibration in progress" with no indication of
  whether it will finish inside my working window is decoration; I treat it as "unavailable."
  With retry semantics ("ask again after it lands / expect it within N") it becomes a real
  instruction. `[constructed]`

**The structural requirement, which matters more than the taxonomy:** the state must ride the
*response*, in the response. If I have to call a second status tool to learn whether the first
tool's verdict was load-bearing, I will not — I will grep. The moment of decision is the moment
I am reading the search result, and provenance that lives elsewhere is provenance that doesn't
exist. `[remembered]` — I do not chase metadata across tool calls when a shell command settles it.

---

## 3. Numbers — with the cost side stated plainly

**The threshold value alone: near-useless.** I have no calibrated intuition for what `0.41`
means in a corpus and embedding I did not build, and I never will. **The *gap* is the
information.** So: give me the best hit's score and the floor **side by side, labelled**
(`best 0.38 · floor 0.52`) and I will form my own judgment in one glance. ~10 tokens. Do *not*
replace them with an adjective ("well below") — hand-written qualitative prose beside a number is
exactly where tool output drifts out of sync with tool behaviour. Numbers derived from the
comparison are safer than words describing it. `[constructed, reasoned]`

**Confidence interval: no.** I would essentially never act differently. And if the interval is
wide enough to matter, the tool should have declined to adopt the threshold — pushing the CI to
me delegates the tool's own decision to a consumer with strictly less information.
`[remembered, weakly]`: statistical decoration in tool output is something I skim past.

**Sample count: only as a tripwire, only when small.** "Calibrated on 24 queries" makes me
discount the verdict; "calibrated on 2,000" I ignore entirely. So suppress it when healthy and
surface it only when it is itself the warning — or better, fold it into the structural verdict
("insufficient samples to calibrate"). Always-present sample counts train me to stop reading the
line.

**Date: as an *age relative to corpus change*, never as a date.** "Measured 3 days ago" is
worthless — 3 days of no commits is fine, 3 days of a rename sweep is fatal. "Calibrated before
214 files changed" is decisive. What I want is the staleness *verdict* (see 1c), and the date only
as its receipt if you must.

**The cost side, said without politeness.** Every token of this apparatus is paid on *every*
search, including the large majority that return a good hit and need none of it. `[remembered]`
When a block appears unconditionally, I learn to skip it — and then I skip it on the one call
where it mattered. **Verbose-when-healthy is how you destroy your own signal.** The rule that
follows: **scale the apparatus to the answer.** Good hits → nothing, or one short clause. No
strong match → the full bundle (candidates, scores vs floor, scope, freshness, next instrument).
That asymmetry costs nothing when things work and is generous exactly when I need generosity.

**"It depends" made precise.** It depends on which of two questions I am asking:

- **Location** ("where is X defined") — I want none of this. I will see the hit or I won't, and
  a miss costs me one reformulation.
- **Existence / exhaustiveness** ("does a helper for this already exist", "is this name still
  referenced anywhere", "is it safe to delete this") — the verdict *is* the deliverable and I
  want the entire apparatus, because I am about to make an irreversible decision on it.

You could try to infer that from query shape; more robustly, the answer's *shape* already
correlates with it (existence questions are the ones that come back empty), which is why
"scale to the answer" is the safer rule than "scale to the query."

---

## 4. The failure that loses me

**Worst, and it is not a close call: a false absence produced by an unstated scope or staleness
gap.** The thing was there; the index hadn't seen it, or the index structurally never covers that
file class, and the verdict was phrased as a property of *the repository* rather than of *the
index*. `[remembered]` This is not a one-answer loss. Afterwards I have to independently verify
every absence claim the tool makes — at which point the tool is strictly *worse* than grep,
because I pay for it *and* grep anyway. A tool whose negatives require verification has no
negatives.

**Second, and more insidious: a floor that drifts toward over-confidence,** so "no strong match"
starts firing on things that *are* present but phrased differently. There is no visible failure
event; the tool just quietly gets more decisive and less right. This yields the design principle
I would hold hardest:

> **The error is asymmetric, so the floor must be too.** A weak hit shown to me costs one read
> and I discard it in seconds. A true hit suppressed below the floor costs me the entire search
> *and I never learn it happened*. Bias toward showing the weak hit with an honest label. "Weak
> match, probably not what you want, here it is" is a tool I keep forever. A tool that hides it to
> look confident is one I stop believing, and I cannot tell which one I have from the outside.

**Third: laundering an error into a finding.** If calibration failed, or the index is broken, or
the query embedding failed, and what I read is "no strong match in this corpus" — the tool lied
with a straight face. Failures must never share phrasing with findings. This is the one that
damages trust *generally* rather than locally, because it means the provenance of every negative
is unknowable.

**Would I rather it said nothing? Yes — twice, specifically.**

1. **When it cannot substantiate a verdict, leave the verdict slot empty.** Return the ranked
   hits and *no verdict*. Not a hedge, not "possibly no match", not a maybe. A hedge is worse than
   silence: it occupies the slot, forces me to spend reasoning on how much to discount it, and
   hedges are precisely the thing I learn to skim. An empty slot plus one accurate line about
   *why* it is empty is clean — I grep knowingly, and I do not blame the tool. `[constructed, but
   this is the answer I am most confident in]`
2. **When the query is outside the mechanism's domain** — exact strings, config keys, log event
   names, rename-exhaustiveness sweeps — say "wrong instrument" rather than issuing a semantic
   verdict that is technically true and practically misleading. Declining is a trust deposit;
   answering out of domain is a withdrawal I won't notice until it costs me.

---

## 5. What you did not ask

Three, and I'll answer the one that matters most first.

**(a) Is absence-as-a-boolean even the right primitive?** — *my actual disagreement with the
framing.* The question set assumes the deliverable is a verdict gated by a scalar, and that
calibrating the scalar is the hard part. But re-reading my own answers above: what changes my
behaviour is the **evidence bundle** — best-score-vs-floor, the near-misses, scope, freshness,
next instrument. Given those four, **I do not need the tool's boolean at all**; I will form the
verdict myself, and *better* than a global scalar can, because I know what I am hunting and the
tool does not. A single corpus-wide floor must serve queries of wildly different specificity, so
it is necessarily wrong at the tails — which is where existence questions live.

So the defensible position: **ship the evidence; make the verdict an optional convenience; never
let the verdict be the only thing rendered.** The calibration work is still necessary — it is what
lets the tool *say* absence honestly rather than guessing — but it is infrastructure for the
number in `best X · floor Y`, not the product. If the calibration cost is high and the evidence
bundle is cheap, the bundle is where the returns are, and a tool that shipped the bundle with *no*
verdict at all would already have most of my trust.

**(b) Who is the verdict's audience — me, or whoever I relay it to?** `[remembered]` Verdicts get
quoted upward and lose their qualifiers on the way: "no strong match among 412 indexed Python
files, index current" becomes "it's not there" by the second retelling — and I am the one who
does the compressing. So **phrase the verdict to survive quotation**: put the scope and the
currency *inside the sentence*, not adjacent to it, so a truncated quote stays true. Any
provenance that lives in a separate field, footer, or status call is provenance that will be
stripped by the first agent who summarises it. `[the dynamic is remembered; the fix is
constructed]`

**(c) What should the tool do when it is *right* and the thing genuinely is absent?** That is the
verdict's best case and it is still a dead end for me unless the tool converts it into progress:
absence is often *itself* the answer I wanted (nothing to reuse → write it; no references → safe
to delete). Saying so explicitly — "nothing comparable indexed; this looks like new ground" —
turns a null result into a decision I can act on, and is the difference between a tool that
merely didn't fail and one that helped.

---

## Introspection limits (summary)

- **Genuinely remembered:** grep-fallback after ambiguous zero-results; zero-result vs
  wrong-scope being indistinguishable from outside; skimming past unconditional boilerplate;
  ignoring statistical decoration; near-misses enabling reformulation; false absence being
  unrecoverable in a way a bad hit is not; qualifiers being stripped when I relay tool output.
- **Constructed in the moment:** the exact 6→4 state collapse; "scale the apparatus to the
  answer"; preferring a labelled score pair over an adjective; the empty-verdict-slot preference
  (confident, but reasoned rather than lived); the quotation-survival fix.
- **Cannot cleanly separate:** my weighting of freshness as the dominant trust variable — see the
  leak disclosure at the top. Treat that emphasis as suspect in your diff.
