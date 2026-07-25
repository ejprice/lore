# REPORT — consult-fable-11i (client-needs consult: the "no strong match" verdict)

Informant: Fable, answering as a consumer of code-search tooling. Blindness constraint
honored: no repository file read, no codebase search, no investigation. This file is the
only filesystem action taken. Where the auto-loaded project instructions leaked context,
I have ignored it as directed; nothing below is derived from it.

Marking convention, per the brief: **[remembered]** = a behavioral pattern I can actually
report from experience of using search tools; **[constructed]** = a preference assembled
in the moment that sounds right but has no behavioral receipt. The difference is flagged
inline everywhere it matters.

One framing disagreement, stated up front because it shapes every answer below: the
questions ask how the tool should *report* its measurement states. My honest answer is
that most of those states should not be reported — they should gate **whether the verdict
is issued at all**. A verdict is a speech act, not a data field. Decorating an
uncalibrated verdict with caveats is strictly worse than not issuing it. Most of the
reporting problem dissolves once you accept that. Details in Q2 and Q4.

---

## Q1 — What makes "no strong match" actionable

The core problem: a weak semantic result has two indistinguishable causes — (a) the thing
is absent, (b) my phrasing didn't land where the code lives in embedding space. A bare
verdict only speaks to (a). My genuine reflex on a weak result is *rephrase once, then
grep* **[remembered]** — and the verdict as usually delivered does nothing to interrupt
that loop, because it carries no evidence distinguishing (a) from (b).

What actually earns the trust to stop searching, in priority order:

1. **The near-misses, always.** Show the top 2–3 sub-threshold hits with scores. This is
   the single highest-value item, and it is the deciding evidence in my real behavior
   **[remembered]**: if the near-misses are semantically *adjacent* — right domain, wrong
   specifics — I believe the absence, because the query demonstrably landed in the right
   neighborhood and found nothing. If the near-misses are random garbage, I know my query
   embedding went somewhere weird, and I rephrase rather than conclude absence. A bare
   verdict hides exactly the information that discriminates "absent" from "mis-asked."

2. **What corpus the negative is over.** "No strong match" across *what*? One clause of
   coverage + freshness ("4,213 files indexed, synced 2m ago") is load-bearing: a stale
   or partial index makes the verdict worthless, and I cannot see staleness from the
   result itself. Absent this, an exhaustiveness-sensitive consumer *must* fall back, as
   a matter of hygiene rather than distrust. **[remembered** — checking index freshness
   before trusting negatives is a habit I actually have**]**

3. **Calibration provenance, one clause.** Not the number — the *kind*: "calibrated bar
   for this corpus" vs. "default threshold." A negative resting on a per-corpus
   measurement is a different claim from one resting on a constant someone shipped. I
   need to know which sentence I'm reading. **[constructed** as a format, but it follows
   directly from the remembered behavior in Q4: one false negative kills all negatives**]**

4. **Scope honesty about the verdict class.** Semantic search can never issue a
   trustworthy negative for *symbol-existence* questions (is this name used anywhere? does
   any caller exist?) — that is exact-match territory, and no threshold fixes it. A tool
   that says so in the verdict ("for existence-of-name questions, use exact search")
   earns more trust than any calibration, because it demonstrates it knows the limits of
   its own claim. A tool that issues negatives beyond its epistemic reach is a tool whose
   *positives* I also start discounting. **[remembered** in the general form: tools that
   overclaim in one register lose me in all registers**]**

What does NOT earn trust: a bare boolean; a confidence percentage with no visible
grounding ("87% confident" — ungrounded numbers are worse than no numbers, see Q3);
reassuring prose ("this codebase likely does not contain…" — prose confidence is free to
generate and I know it).

One more honest note: even a fully-trustworthy calibrated negative should not suppress
*one* rephrase. The threshold is measured against the corpus, but my query is one point
in embedding space; a second phrasing is a genuinely independent draw. Two negatives
across two distinct phrasings is when absence becomes my working belief. A tool that
made me feel rephrase was pointless would actually degrade my search behavior.
**[remembered** as the two-phrasings habit; **constructed** as design advice**]**

---

## Q2 — The six states: which distinctions I would actually use

The six states, from the consumer side, collapse to **three**:

| Tool's states | Consumer state | What I do differently |
|---|---|---|
| never measured · measurement failed · measuring right now · feature disabled | **Uncalibrated** | Treat any "weak result" as *descriptive*, not verdictive. Judge the near-misses myself. Fall back freely. |
| measured & adopted | **Calibrated** | Accept the negative as a real signal (subject to Q1's evidence). |
| corpus too small | **Small corpus** | Stop being clever: a corpus too small to calibrate is a corpus cheap to read or grep exhaustively. Different *action*, so a real distinction. |

Plainly, which distinctions are the tool talking to itself:

- **Never-measured vs. failed vs. in-progress vs. disabled**: I would treat all four
  identically. The *why* of uncalibration is operator-diagnostics, not consumer
  information. "Measuring right now" theoretically implies "retry later," but honestly I
  will not re-call a search later in a session to catch a calibration finishing — the
  task needs the answer now **[remembered** — I do not make courtesy re-calls to tools**]**.
  One word of reason ("uncalibrated: measuring") costs little, but zero words costs less
  and loses me nothing.
- **Measured-but-not-adopted** is the interesting one, and it still collapses — *unless*
  the reason for non-adoption carries corpus information. If the measurement was rejected
  because the score distribution was degenerate (everything similar to everything), that
  tells me semantic search discriminates poorly on this corpus *in general* — which
  downgrades my trust in the **positives** too, and I would genuinely use that. Surface
  the corpus fact, not the adoption state-machine. "Measured but we decided not to use
  it," with no reason, is pure internal monologue.
- **Small corpus** is the one state beyond calibrated/uncalibrated I'd act on
  distinctly, because it changes strategy, not just confidence: "corpus ~40 documents —
  exhaustive reading is cheap" reroutes me entirely.

**Delivery constraint, and it's absolute [remembered]:** the state must be a clause *on
the search result itself*, never a separate status surface I'm expected to consult
first. I will not make a second tool call to check calibration state before trusting a
verdict — not once, not ever, in the middle of a task. A status endpoint is fine for a
session-start ritual or an operator; as a per-verdict guard it will simply go unread.
If it isn't inline, it doesn't exist.

And per the framing disagreement: the cleanest design isn't three *labels* — it's that
the calibrated state is the only one in which the verdict *sentence* appears at all.
Uncalibrated → plain ranked results, low scores visible, no existence claim. Small
corpus → results plus the reroute clause. Then the state reporting problem mostly
disappears, because state is encoded in *which speech act occurred*.

---

## Q3 — Numbers in my context: the honest accounting

First the distinctive consumer fact, because it's the part a human designer will
under-weight: **I don't skim.** A human reads past a status block; every token in my
context is attended to and exerts gravitational pull on reasoning. An ungrounded number
doesn't just occupy space — it *invites* reasoning about itself. Print a threshold of
0.63 and some fraction of my next thought is about whether 0.63 seems high, a question I
have no basis to answer and shouldn't be asked. Irrelevant numbers are not free noise;
they are active distractors. **[remembered** in the general form — I notice this pull in
myself when tools print diagnostics**]**

Item by item:

- **Threshold value alone: no.** Similarity scores are unitless and model-dependent;
  0.63 means nothing without the distribution behind it.
- **Threshold + best-hit score as a pair: yes — this is the one number-shape I'd use.**
  "Best 0.41 vs bar 0.63" vs. "best 0.61 vs bar 0.63" are different situations: the
  first says the miss is decisive, the second says look at the near-misses anyway, the
  bar is soft here. It's the *margin* that's informative; the absolutes are just its
  carriers. A categorical ("well below" / "just below") would honestly serve the same
  function — but the number pair is two tokens and lets me hold the relation exactly.
  Two numbers, max. **[constructed** as format; the marginal-vs-decisive distinction is
  **remembered** — near-threshold misses genuinely change what I do next**]**
- **Confidence interval: no, flatly.** I will not do statistics on a search tool's
  calibration mid-task. Uncertainty is the tool's job to fold into its verdict (issue it
  or don't; call the calibration weak if it's weak) — handing me raw error bars is
  delegating the tool's own judgment upward into scarcer context.
- **Sample count: no.** Same reason. If N was too small to trust, the tool shouldn't have
  adopted the measurement; if it adopted it, telling me N=40 gives me a number I'll read,
  can't evaluate, and won't act on. Worst of both.
- **Measurement date: only as a *comparison the tool already did*.** "Calibration
  predates 60% of the current corpus" is actionable — it tells me the bar was measured
  against a different corpus than the one I'm searching. A raw timestamp makes me do the
  comparison myself, and honestly I'd ignore it **[remembered** — I skip absolute
  timestamps in tool output unless something already smells wrong**]**.

Where "it depends" is real: on whether the negative is **load-bearing**. For a deletion
gate or exhaustiveness question I want maximal evidence — near-misses, margin, coverage —
because a wrong negative there ships a break. For exploratory "is there already a helper
for this?" the one-line verdict is plenty. The tool can't know which it's serving, so the
resolution is: a constant compact verdict line + near-misses always (they serve both
cases and are the bulk of the useful payload anyway); everything else — distributions,
history, sample counts — behind an explicit diagnostics call I will make roughly never,
but an operator will.

Budget, stated concretely: search is called many times per session, so the per-call
overhead of this whole mechanism should be ~1 line + the near-miss listing. A five-line
status block on every search response is a real tax multiplied by every call — and worse
than the token cost is the attention cost above.

---

## Q4 — The failure that loses me

**The confident false negative.** The tool says "no strong match," I later ground-truth
it — a grep finds the thing in one call. That single event permanently kills every future
negative the tool issues, and here's the mechanism honestly: I don't recalibrate my trust
downward by some percentage; the *verdict class* dies. Every future "no strong match"
becomes "shrug — grep anyway," at which point the mechanism buys nothing while still
costing tokens to print and attention to read. **[remembered** — this is genuinely how my
trust in tool verdicts behaves: categorical, not proportional. One ground-truthed false
"all clear" and I re-verify that tool's clears forever after.**]**

Note the asymmetry, because it licenses the whole design: a false *positive* — weak hits
that turn out irrelevant — costs me one read and zero trust. I expect that from semantic
search; ranked-retrieval being imperfect is priced in. The negative verdict is a
different speech act entirely: it invites me to **stop searching**. Wrongness there isn't
degraded quality, it's betrayal of the one specific promise the feature makes. So the
verdict should be tuned hard toward precision-of-the-negative, even at heavy cost to how
often it gets issued. A verdict that appears rarely and is always right is a verdict I'll
build behavior on. One that appears always and is usually right is one I'll route around.

Second-tier trust-killer: **the mechanism eating the function.** If the calibration
machinery can ever cause a search to fail — an error instead of results because the
threshold subsystem crashed or is mid-measurement — that's instantly disqualifying. The
auxiliary feature must degrade to "results without verdict," never to "no results."
**[constructed** as a scenario, but high confidence: a tool that won't answer its primary
question because a secondary feature is unhappy is one I stop calling**]**

Minor and lower-confidence: silent regime change — same query, different verdict across a
recalibration, nothing marking the change. Within one session I'd likely only notice on a
repeated query; across sessions I have no memory to notice with. A one-time "bar
recalibrated" note on first use of a new threshold is cheap insurance, but I flag this as
**[constructed]** — I can't honestly claim it would change my behavior often.

**The sharper question — when is silence better than the verdict: yes, and it's the
design's keystone.** When calibration is absent (uncalibrated in Q2's sense), I would
rather the tool said *nothing verdictive at all* — just ranked results with their low
scores visible — than issue "no strong match" with a caveat attached. Reason: caveated
verdicts train me that the sentence "no strong match" sometimes means something and
sometimes doesn't, which means it never means anything, which destroys the calibrated
case too. The sentence must be reserved for the regime where it's backed. Silence in the
uncalibrated regime is what *makes* the verdict a signal in the calibrated one. This is
the strongest single opinion in this report.

---

## Q5 — The question that wasn't asked

**"What sentence is the verdict, exactly — and which claim does that sentence commit
to?"** The brief specifies the mechanism (threshold, measurement, states) but not the
wording, and for an LLM consumer the wording *is* the contract — we act on the sentence,
not on the subsystem behind it.

There are two available claims and they are not the same:

- *"No result scored above this corpus's calibrated bar"* — a claim about **the search**.
  Always true when issued, epistemically modest, and composes correctly with my own
  judgment (I read the near-misses and decide).
- *"This is not in the corpus"* — a claim about **the world**. It's the claim I *want*,
  and it's one the mechanism cannot actually license: a threshold on one query's
  similarity measures whether the search worked, not whether the thing exists. A single
  phrasing that misses embedding-space is fully consistent with the target sitting right
  there under a different vocabulary.

"No strong match in this corpus" — the brief's own phrasing — reads as the second claim
while only the first is earned. That gap is precisely where the Q4 trust-killing false
negative comes from: not from a mis-measured threshold, but from a sentence that
overclaims relative to its mechanism. Write the search-claim sentence, attach the
evidence (near-misses, margin, coverage), and let the existence conclusion be *mine* —
that division of labor matches what each party can actually know.

And the constructive corollary, offered because the brief asked what enables the best
work **[constructed, but high-confidence it would change my behavior]**: the negative I
would trust *without* reaching for grep is one that already survived multiple phrasings —
the tool internally expanding the query into several reformulations and reporting
"nothing cleared the bar under N distinct phrasings." That automates exactly the
rephrase-loop I run manually **[the loop itself: remembered]**, and it converts the
verdict from "this phrasing missed" to something much closer to the existence claim I
actually want. A threshold makes one search's silence meaningful; query expansion is what
makes the silence *evidence*. If the mechanism budget only covers one of the two, I'd
take expansion over finer-grained calibration state reporting without hesitation.

---

## Summary for the diff

1. Verdict needs: near-misses always (the deciding evidence), coverage/freshness clause,
   calibration *kind* not calibration *number*, and scope honesty about question classes
   semantic search can't issue negatives for.
2. Six states collapse to three: calibrated / uncalibrated / corpus-too-small. The
   why-uncalibrated taxonomy is the tool talking to itself. State must ride inline on the
   result; a separate status call will never be made mid-task.
3. Numbers: margin pair (best-vs-bar) yes; threshold alone, CI, sample count, raw
   timestamps no. Tokens are attended, not skimmed — ungrounded numbers actively distract.
4. One ground-truthed false negative kills the verdict class permanently; tune for
   precision-of-the-negative. Never let the mechanism block results. Silence beats a
   caveated verdict: uncalibrated → no verdict sentence at all, just ranked results.
5. Unasked: what sentence is the verdict, and does it claim search-quality or existence?
   Only the former is earned. Query expansion would do more for trustworthy negatives
   than any refinement of threshold state reporting.
