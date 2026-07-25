# Packet 11-i — client-needs consult: the absence verdict and its calibration

**Run 2026-07-25** by `lead-11i-b`, on the operator's direction (*"REMEMBER — the consumers of lore
are agents, not humans. What does an agent want? Ask them."*). Method: `docs/design/2026-07-06-client-needs-consult.md`
(models as introspective informants about their own tool-UX needs; operator-directed 2026-07-06).
Precedent: `docs/design/2026-07-04-map-test-segregation.md`.

**Informants — three, independent, blind:** `consult-opus-11i` (Opus), `consult-sonnet-11i`
(Sonnet 5), `consult-fable-11i` (Fable). Each was forbidden to read any repository file, given the
same five questions in the same words, and told nothing about lore, packet 11-i, the design, or the
existence of the other two. Reports archived beside this file at close-out; until then they are at
the worktree root as `REPORT-consult-{opus,sonnet,fable}-11i.md`.

**Why this consult, when 11-i is dark.** 11-i changes no served byte — but it freezes the state
domain and the measurement row's field list, and those permanently bound what 11-ii is ever able to
tell an agent. Choosing them by designer intuition is a serving decision made a packet early by the
wrong party. The Consumer Law names the right party.

---

## 0. Contamination disclosure — read before weighting anything below

All three informants had this repo's `CLAUDE.md` auto-loaded into context; none could prevent that.
**Opus alone flagged which of its own answers that might have seeded**, unprompted: its emphasis on
staleness/freshness as the dominant trust variable, because the file carries "check, then trust" and
describes an index freshness surface. It reported a live impulse to go look at that surface and did
not.

Carrying that honestly: **the freshness/currency finding (§1.4) is the one unanimous result that has
a plausible common seed in a file all three read, so it is the weakest of the unanimous set** — it
should be treated as corroborated-but-contaminated. The near-miss, margin-pair, CI-refusal and
inline-delivery findings have no counterpart in that file and are clean.

---

## 1. Unanimous — 3 of 3, independently

### 1.1 Show the near-misses, always. This is the deciding evidence, not a courtesy.
All three ranked it first, for the identical reason none of them could have copied: the sub-threshold
hits are what discriminate *"the tool understood me and the thing is absent"* from *"my query landed
in the wrong region of embedding space."* A bare verdict is **unfalsifiable**, and all three said
unfalsifiable output is what they route around.

- Opus: *"Suppressing weak hits to look decisive is the worst possible trade here."*
- Fable: *"if the near-misses are semantically adjacent — right domain, wrong specifics — I believe
  the absence… If the near-misses are random garbage, I know my query embedding went somewhere
  weird, and I rephrase."* Marked `[remembered]` — a behavioural receipt, not a preference.
- Sonnet: *"A tool that swallows the near-misses to give me a clean 'no match' is hiding exactly the
  information I'd use to override it when it's wrong."*

### 1.2 The margin pair is the ONLY number shape wanted — and all three invented the same render
Asked what numbers to serve, three blind informants independently produced the same two-number format:

| informant | proposed render |
|---|---|
| Opus | `best 0.38 · floor 0.52` |
| Sonnet | `Closest hit: 0.31 (threshold 0.62)` |
| Fable | `Best 0.41 vs bar 0.63` |

The threshold **alone** is near-useless to all three — unitless, model-dependent, and they have no
calibrated intuition for it. **The margin is the information; the absolutes are its carriers.**
Opus adds a warning that matters for this repo specifically: do not replace the pair with an
adjective ("well below"), because hand-written qualitative prose beside a number is exactly where
tool output drifts out of sync with tool behaviour. *Numbers derived from the comparison are safer
than words describing it* — the same law `CLAUDE.md` states as "prose that describes behaviour must
be DERIVED from the behaviour."

### 1.3 Confidence interval: NO. Unanimous, unhedged, and with the same argument.
This is the most decision-relevant result in the consult. All three refused the CI as a served
value, and all three gave the same reason independently — **serving the CI delegates the tool's own
decision to a party with strictly less information.**

- Opus: *"if the interval is wide enough to matter, the tool should have declined to adopt the
  threshold."*
- Sonnet: *"honest but not actionable from me; it's actionable from whoever tunes the tool."*
- Fable: *"I will not do statistics on a search tool's calibration mid-task… handing me raw error
  bars is delegating the tool's own judgment upward into scarcer context."*

**Sample count** collapses the same way (2 of 3 reject outright; Sonnet would take it only
pre-digested into a coarse tier; Opus only as a tripwire when small). **Raw dates** likewise: all
three want *a comparison the tool already performed*, never a timestamp — "calibrated before 214
files changed" (Opus) / "corpus has grown since" (Sonnet) / "calibration predates 60% of the current
corpus" (Fable).

### 1.4 The state must ride INLINE on the search response ⚠ (see §0 — contaminated)
All three, emphatically, and Fable marked it `[remembered]` and *absolute*: they will not make a
second status call mid-task to learn whether the first tool's verdict was load-bearing.

- Fable: *"If it isn't inline, it doesn't exist."*
- Opus: *"provenance that lives elsewhere is provenance that doesn't exist… I do not chase metadata
  across tool calls when a shell command settles it."*
- Sonnet: *"it belongs attached to every verdict, not queried separately."*

Coverage/scope belongs in the same clause — all three named an unseen stale-or-partial index as the
failure mode that renders identically to true absence from outside.

### 1.5 Silence beats a hedged verdict — and it is what MAKES the verdict a signal
All three answered the sharper question the same way: when the tool cannot substantiate a verdict,
withhold **the verdict layer**, not the data. Return ranked hits with their low scores visible and
no existence claim. Not a hedge — a hedge is worse than silence, because it occupies the slot and
must still be reasoned about.

Fable calls this *"the design's keystone"* and *"the strongest single opinion in this report"*:
> *"caveated verdicts train me that the sentence 'no strong match' sometimes means something and
> sometimes doesn't, which means it never means anything, which destroys the calibrated case too.
> The sentence must be reserved for the regime where it's backed. Silence in the uncalibrated regime
> is what makes the verdict a signal in the calibrated one."*

### 1.6 The trust loss is CATEGORICAL, not proportional
All three describe the same mechanism, which is sharper than the Trust Doctrine's current wording:
one ground-truthed false negative does not reduce trust by a percentage — **it kills the verdict
class outright**, permanently, including the correct instances.

- Fable `[remembered]`: *"One ground-truthed false 'all clear' and I re-verify that tool's clears
  forever after."*
- Opus: *"A tool whose negatives require verification has no negatives"* — and is strictly worse than
  grep, because you pay for it *and* grep anyway.
- Sonnet: the loss is the ability to *retroactively audit* which past verdicts were backed.

### 1.7 The error is asymmetric, so the floor must be
A weak hit shown costs one read and is discarded in seconds. A true hit suppressed below the floor
costs the entire search **and is never learned about**. Opus and Fable both derive the same design
consequence — bias toward showing the weak hit with an honest label; tune hard for
precision-of-the-negative even at heavy cost to how often the verdict gets issued.

> Fable: *"A verdict that appears rarely and is always right is a verdict I'll build behavior on.
> One that appears always and is usually right is one I'll route around."*

---

## 2. The six states — what the consumer actually distinguishes

All three collapsed the set. They did not collapse it to the same cardinality, and the disagreement
is informative rather than noise.

| tool state | Opus (4 surfaces) | Sonnet (2 + 1) | Fable (3) | verdict |
|---|---|---|---|---|
| measured & adopted | verdict live | CALIBRATED | Calibrated | **served, 3/3** |
| never measured | no verdict available | UNCALIBRATED | Uncalibrated | **collapses, 3/3** |
| measured, not adopted | no verdict available | UNCALIBRATED | Uncalibrated | **collapses, 3/3 — but see §2.1** |
| measurement failed | announced once, never laundered | UNCALIBRATED | Uncalibrated | collapses, but the FACT is load-bearing (3/3) |
| corpus too small | no verdict *possible* (structural) | UNCALIBRATED | Small corpus | **2/3 keep it distinct** |
| measuring now | only with retry semantics | keep (retry-later) | fold in | **split 1/1/1** |
| feature disabled | keep (human-actionable) | fold in | fold in | 1/3 |

**Unanimous within the table: `never measured` vs `measured but not adopted` is the tool talking to
itself.** All three said so in those terms, unprompted.

**On `corpus too small` (2/3, and with the strongest rationale):** Opus and Fable both keep it
because it changes *strategy*, not just confidence — a corpus too small to calibrate is a corpus
cheap to read or grep exhaustively. Fable: *"Stop being clever."* That is an action change, which is
the filter all three applied.

**On `measuring now`:** Fable rejects it on a `[remembered]` behavioural claim — *"I do not make
courtesy re-calls to tools"* — and Opus keeps it only if the retry is genuinely actionable. Only
Sonnet wants it unconditionally. A served state spent here buys little.

### 2.1 THE FINDING THAT LANDS ON THE PROBE RUNNING RIGHT NOW
Two of three informants — blind to each other, blind to lore, and with no knowledge that a
degeneracy measurement was in flight — **independently carved out the same single exception** to
"non-adoption is internal monologue":

> **Opus:** *"if the rejection reason was degenerate measurement / insufficient separation, that is
> the same information as 'corpus too small' and should be said in those words — as a property of
> the corpus, not as a state of the tool's decision process."*
>
> **Fable:** *"If the measurement was rejected because the score distribution was degenerate
> (everything similar to everything), that tells me semantic search discriminates poorly on this
> corpus in general — which downgrades my trust in the positives too, and I would genuinely use
> that. Surface the corpus fact, not the adoption state-machine."*

Both named **degeneracy** as the one non-adoption reason worth serving, and both said serve it **as
a corpus property, not a tool state.** `probe-bootstrap-11i-b` is at this moment measuring whether
this design's interval is degenerate on exactly this corpus. Whatever it returns, the consumer-facing
answer is already ruled by its own clients.

---

## 3. Unique findings — one each, all three worth carrying

**Sonnet — the calibration axis nobody has.** The threshold is calibrated per corpus, per embedding
model, per prompt — *and not per query shape*. A single symbol name, a natural-language sentence, an
error-message fragment and a vague "where is the thing that does X" have no reason to produce
comparably-shaped score distributions in the same embedding space. If they don't, one numeric
threshold is *simultaneously too strict for one query style and too loose for another, while
reporting identical confidence for both.* Sonnet calls the named axes "one axis short," and ranks
this as its single highest-value addition. **Note for §4: this collides directly with the
head-pointer key decision 11-i-a is about to freeze.**

**Fable — the verdict is a speech act, and the sentence overclaims.** Two claims are available and
they are not the same: *"no result scored above this corpus's calibrated bar"* (a claim about **the
search** — always true when issued, and it composes with the agent's own judgment) versus *"this is
not in the corpus"* (a claim about **the world**, which a threshold on one query's similarity cannot
license). The brief's own phrasing — and this packet's — reads as the second while only the first is
earned. *"That gap is precisely where the trust-killing false negative comes from: not from a
mis-measured threshold, but from a sentence that overclaims relative to its mechanism."* Fable's
constructive corollary, offered as the higher-value spend if only one is affordable: **internal
query expansion** ("nothing cleared the bar under N distinct phrasings") does more for a trustworthy
negative than any refinement of calibration-state reporting, because it automates the rephrase loop
all three informants run manually.

**Opus — is the boolean the right primitive at all?** Its stated disagreement with the framing:
given the evidence bundle (margin, near-misses, scope, freshness, next instrument), *"I do not need
the tool's boolean at all; I will form the verdict myself, and better than a global scalar can,
because I know what I am hunting and the tool does not."* A single corpus-wide floor must serve
queries of wildly different specificity, so it is necessarily wrong at the tails — which is where
existence questions live. Position: **ship the evidence; make the verdict an optional convenience;
never let the verdict be the only thing rendered.** Calibration remains necessary — it is what
licenses the `floor` number in the margin pair — but it is *infrastructure for the pair, not the
product.*

**Opus, second — phrase the verdict to survive QUOTATION.** Verdicts get relayed upward and lose
their qualifiers in transit: *"no strong match among 412 indexed Python files, index current"*
becomes *"it's not there"* by the second retelling — **and the relaying agent is the one doing the
compressing.** So scope and currency go *inside* the sentence, not adjacent to it, so that a
truncated quote stays true. Any provenance in a separate field or footer will be stripped by the
first agent who summarises it. This is a serving-surface law with a schema consequence.

**Fable, second — the mechanism must never eat the function.** If calibration can ever cause a
search to *fail* (error instead of results because the threshold subsystem crashed or is
mid-measurement), that is instantly disqualifying. The auxiliary feature degrades to "results
without verdict," never to "no results." Directly relevant to 11-i's fail-safe default and to the
single-flight lease's missing expiry.

**Sonnet, second — there is no feedback path.** An agent acts on "no strong match," then finds the
thing via grep. Nothing carries that back to calibration. Raised, not folded in.

---

## 4. What this binds in 11-i — the lead's reading, not the informants'

The informants answered about a tool. Mapping their answers onto this packet's frozen decisions is
mine, and is flagged as such.

1. **The CI is INTERNAL machinery, and that materially re-prices the S1 fork.** 3/3 refuse it as a
   served value. So the bootstrap interval exists solely to drive adoption / per-tier upgrade /
   staleness. **If `probe-bootstrap-11i-b` returns DEGENERATE, no served surface loses anything** —
   the loss is confined to an internal decision mechanism, which is a replacement problem, not a
   client-facing regression. This should be carried into the sidecar's Q1 pricing of the fork.
2. **The 8-state set may stay as an internal taxonomy, but the SERVED PROJECTION is ~3 and must be
   typed, not rendered ad hoc.** Otherwise 11-ii hand-rolls the collapse at seven call sites and the
   prose drifts from the mechanism — the exact defect class `CLAUDE.md`'s "A DIAGNOSIS IS NOT AN
   INSTRUMENT" section exists to stop. The projection is a function of the state, pinned once.
3. **`measured_not_adopted` needs a typed non-adoption REASON on the row** — because 2/3 informants
   independently said the state is internal monologue *unless* the reason is degeneracy/insufficient
   separation, which they would act on, and which must render as a corpus property. This is a schema
   requirement landing in **11-i-a**, not a render decision deferrable to 11-ii.
4. **The row must persist what makes the staleness DELTA computable** — the corpus state at
   measurement (file/chunk counts, embedding fingerprint), because 3/3 want a comparison rather than
   a date. The design already captures a corpus snapshot; the consult confirms the snapshot is the
   load-bearing part and the timestamp is not.
5. **Inline delivery is an architecture constraint on the head pointer, not a render preference.**
   3/3 will not make a status call. The floor and its state must be readable on the *search* path,
   cheaply, per call. If the design priced head-pointer reads as an `lore_index` render, that pricing
   is wrong.
6. **Sonnet's query-shape axis collides with the head-pointer key — and that key freezes in
   11-i-a.** The blind review already flagged that a head keyed on `scope` alone collides with D6 the
   moment a second *statistic* exists, and that deciding it after the table ships is a migration. The
   consult adds a second candidate dimension (query shape) from the client side. **The key must be
   decided against both, now.** Routed to the sidecar as Q3, amended.

---

## 5. Method note — what this consult cost and whether to run more

Three agents, no repo access, one question set, ~15 minutes wall-clock. The convergence was strong
enough that a fourth informant would likely have been redundant on §1 and useful only on the §2
split. **The instrument worked because the questions were answerable from the informants' own
experience without any knowledge of the system** — which is also why it could be run blind, and why
it could be run *before* a designer framed it. Where a question requires knowing lore's internals to
answer, this instrument does not apply and a design agent is the right tool.

The one methodological weakness is recorded in §0 and is structural: informants cannot be isolated
from the project instructions file, so any question whose answer that file discusses is contaminated
by construction. Framing questions to avoid its subject matter is the only available mitigation.
