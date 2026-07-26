# Client-Needs Consult: "No Strong Match" Verdicts in Semantic Code Search

**Informant:** Sonnet 5, answering as a first-person consumer of code-search tools, not as
a proxy for one. **Blind per instructions** — no repository files read, no codebase
searched, no attempt made to identify or investigate the system this consult is about.

**A note on introspection quality, up front, because the brief asked for it explicitly and
it matters more than any individual answer below:** I do not have episodic memory of
specific past tool calls in specific past sessions — each conversation starts without
recall of prior ones unless something was written to a file I later read. So where I say
"I have been burned by X," that is not a citation of a remembered incident; it is a
description of a behavioral tendency I can attest to from how I actually process ambiguous
tool output *within* a session — including, honestly, from watching myself compose this
very report and noticing which claims I'd hedge and which I'd act on directly. I mark this
distinction inline as REMEMBERED-PATTERN (a tendency I can point to in my own behavior,
even without a specific episode) versus CONSTRUCTED (a preference I'm reasoning to now,
for the first time, under this prompt). An informant who can't tell these apart is worse
than none — so I'm not going to smooth over the difference for a cleaner-sounding report.

---

## 1. The verdict itself

CONSTRUCTED, but with a load-bearing REMEMBERED-PATTERN underneath it: when a tool tells me
"no results" with nothing else, my default move — reliably, not occasionally — is to
distrust the boolean and go find another way to check. That's not because I've reasoned
through this tool's calibration; it's because a bare negative is *unfalsifiable* from where
I sit. I can't tell "searched everything, found nothing above threshold" apart from
"searched a stale index," "query malformed," "auth silently failed," or "threshold is set
wrong for this corpus." All five produce the identical string. A verdict I can't
distinguish from four failure modes isn't evidence, it's a shrug with confidence framing.

What would actually earn the trust to *act* on "no strong match" — i.e., to stop and not
reach for grep:

- **The near-miss hits, not just the boolean.** Show me the top-K results and their scores
  even though they're below threshold, with the threshold printed alongside. "Closest hit:
  0.31 (threshold 0.62)" lets me apply my own judgment to the gap — a 0.31 next to a 0.62
  threshold reads very differently than a 0.58 next to a 0.62 threshold, and only one of
  those should make me stop looking. A tool that swallows the near-misses to give me a
  clean "no match" is hiding exactly the information I'd use to override it when it's
  wrong.
- **Scope, not just score.** How many chunks/files did this actually run over, and does
  that match my expectation of the corpus's size. This catches the "searched a stale or
  partial index" failure mode, which a threshold number alone cannot.
- **A calibration provenance flag** — is the threshold in effect actually measured for
  *this* corpus, or a fallback default. This is where question 2 lives, but it belongs
  attached to every verdict, not queried separately.

What would **not** earn trust: elaboration without falsifiability. A paragraph explaining
the methodology doesn't help if I still can't see the near-miss scores; a confidence label
("high confidence: no match") is just the boolean wearing a costume unless I can see what
it's confident *about*. Trust here is earned by giving me the raw material to check the
tool's homework cheaply, not by the tool asserting its own rigor more emphatically.

## 2. The unmeasured states

CONSTRUCTED. Let me actually test each of the six against the question "would I act
differently if I knew this state versus a different one," because that's the only honest
filter for whether a distinction is real to me or just the tool narrating its internals.

- **Never measured**, **measurement failed**, **corpus too small to measure**, **feature
  disabled** — I checked each pair against "does my next action differ," and for all four
  of these the answer is the same action: *there is no calibrated threshold currently
  backing this verdict, so treat "no strong match" as weak evidence, not as absence-proof,
  and fall back to my own judgment on raw hits (or grep, for exhaustiveness-sensitive
  questions).* I cannot construct a scenario where knowing *which* of these four is true
  changes what I do next, in-task. They collapse to one bucket for me: **UNCALIBRATED**.
- **Measuring right now** is genuinely different, and I'd keep it separate. It's the one
  state that's *transient and actionable in a different way* — it tells me a better answer
  might exist soon, so if the query matters enough I could retry later in the session
  rather than permanently downgrading my trust in this tool's verdicts. Collapsing this
  into UNCALIBRATED would cost me that option.
- **Measured but not adopted** is the interesting one, and my honest answer is: it *should*
  be distinguishable in principle, because it implies a judgment call happened that I don't
  have visibility into — but in practice it only earns its keep if the tool tells me what's
  running *instead*. "Not adopted" with no elaboration is indistinguishable from "never
  measured" to me — both mean UNCALIBRATED, act accordingly. "Not adopted, falling back to
  a fixed default of 0.5" is a different, more useful thing, but at that point what's doing
  the work isn't the state label, it's the fallback value being disclosed. So: the six-way
  taxonomy is mostly the tool talking to itself. What I'd actually want exposed is a
  two-way split (CALIBRATED vs UNCALIBRATED) plus the one genuinely orthogonal bit
  (measuring-in-progress, worth a retry-later flag) plus, only when it's cheap, *why*
  uncalibrated in one word — not because I'll act on the reason today, but because a
  recurring "measurement failed" on the same corpus across a session is itself a signal
  worth being able to notice, whereas "corpus too small" isn't going to change no matter
  how many times I ask.

## 3. Numbers in your context

CONSTRUCTED, and the brief is right that this is the question where hedging produces a
useless answer, so: mostly no, with one exception.

- **Threshold value**: marginal yes, but only as one number on the same line as the
  top-hit score — that pairing is what makes it useful (see Q1). As a value reported in
  isolation, without a score to compare it to, it's inert.
- **Confidence interval**: no. I don't have a calibrated intuition for what CI width should
  change my behavior for an arbitrary embedding/corpus pair, and I won't reliably reason
  well about it mid-task — I'd either ignore it or, worse, pattern-match "wide interval ⇒
  suspicious" without any real basis for the cutoff. This is a number that's honest but not
  actionable *from me*; it's actionable from whoever tunes the tool. If it matters, fold it
  into a coarser signal (see next point) rather than handing me raw statistics to
  interpret on the fly.
- **Sample count**: same logic — not as a raw N, because I don't reliably know what N is
  "enough" for this domain. But I'd take it pre-digested: N and CI both compress cleanly
  into a confidence *tier* on the calibration itself (e.g. well-calibrated vs
  thin-sample), which is a one-word thing I can actually act on ("thin-sample" nudges me
  toward not fully trusting a negative, the same direction as UNCALIBRATED but weaker).
  Raw statistics cost context and buy me nothing I couldn't get from the tier.
- **Date measured**: this is the one I'd protect, and it surprised me a little to land
  here — but the reasoning holds up: staleness is something I can reason about directly
  and specifically, in a way I can't for a CI. If the corpus has grown or the embedding
  model changed since the threshold was measured, that's a concrete, first-class reason to
  distrust the current verdict, and it's the kind of drift-between-measurement-and-reality
  bug that's easy to introduce silently and expensive to catch. But I don't want a raw
  timestamp on every result — I want it surfaced as a **staleness delta, and only when
  it's notable** ("calibrated 40 days ago; corpus has grown since" — or nothing at all if
  it hasn't). A quiet, accurate date costs nothing to carry but shouldn't cost me a line
  of context on every green result.

**The "it depends" axis, stated precisely:** a number earns context space in proportion to
how directly and cheaply I can turn it into a *different next action* — not in proportion
to how statistically informative it is. Threshold-next-to-score: acts directly, keep it
compressed. CI and sample count: don't act on them raw, fold into a tier. Date: acts
directly but rarely, so surface only on the rare occasion it's actionable (staleness),
silent otherwise. A rich number I can't act on is worse than a blunt tier I can, because
the rich number still has to be read.

## 4. The failure that loses you

CONSTRUCTED, but I want to be precise about *why* this is the answer rather than just
asserting it.

The worst failure isn't the tool being wrong on some inputs — every heuristic is wrong
sometimes, and I can budget for that if I know the error rate is roughly stable and
roughly disclosed. The worst failure is **an uncalibrated guess presented with the exact
same surface confidence as a calibrated verdict**, so that I can't tell after the fact
which of my past "no strong match — I'll take the tool's word for it" moments were backed
by real measurement and which were a fallback threshold quietly doing its best. The damage
isn't local to the one wrong answer — it's that I lose the ability to retroactively audit
*which* verdicts to trust, so I end up either distrusting all of them (the tool becomes
decorative — I grep everything anyway, and the semantic layer was wasted engineering) or
trusting all of them including the bad ones (worse). Either way the mechanism has actively
made things worse than having no verdict-layer at all, because a plain ranked-hits list
without an interpretive "no match" claim wouldn't have created a false belief for me to
act on and later have to unlearn — usually downstream, after I've already told a user
"this doesn't exist in the codebase" and been wrong.

**The sharper version, answered directly: yes**, there is a case where I'd rather the tool
said nothing — specifically, whenever its own confidence in the calibration is below
whatever bar it uses to call itself CALIBRATED. In that state I want the *verdict layer*
withheld, not the underlying data — give me the raw ranked hits and let me apply judgment,
same as I'd do if I already distrusted the claim. I don't mean literal silence; I mean
don't dress an unconfident guess as a confident claim. Withholding costs me nothing (I
fall back to exactly the behavior I'd use anyway on a claim I don't trust). A wrong verdict
costs me a belief I have to carry, act on, and eventually discover was false — usually at a
worse moment than right now. Degrading gracefully to "I don't know, here's the raw
evidence" beats guessing confidently, for the same reason it beats guessing confidently in
any other context.

A secondary failure worth naming, lower severity but same family: verdict instability
across near-identical rewordings of the same query against the same corpus, with no
visible reason. That doesn't just cost me one wrong answer — it teaches me the verdict
tracks query phrasing more than corpus truth, which is a subtler but comparably corrosive
way to lose trust in the whole surface.

## 5. What we did not ask

Two things, one I'll flag briefly and one I'll answer properly.

Briefly: there's no feedback path in the question set — when I act on a "no strong match"
and then find the thing anyway via grep, is there anywhere for that to go back to the
tool's calibration? Not something I need mid-task, but relevant to "engineer the tool to
serve the best work," so worth naming even unanswered.

The one I'll actually answer: **the setup states the threshold is measured "per corpus,
per embedding model, per prompt used to embed" — but says nothing about per *query shape*,
and I think that's a real gap, not a missing nice-to-have.** A threshold calibrated against
some representative query distribution is being applied uniformly to whatever I actually
type — a single symbol name, a full natural-language sentence, an error-message fragment
pasted verbatim, a vague "where is the thing that does X." I have no basis to assume those
four produce comparably-shaped score distributions in the same embedding space, and if they
don't, the same numeric threshold is simultaneously too strict for one query style and too
loose for another, *while reporting identical confidence for both*. This is the same
failure shape as Q4 (uniform confidence hiding non-uniform reliability) but on a different
axis — not "is the threshold calibrated at all" but "calibrated for what I'm actually
asking." If I had to prioritize one addition to the measurement work described in the
brief, it's this: either measure per query-shape bucket, or at minimum disclose which
query-shape the threshold was validated against, so a mismatch is something I could
in-principle notice rather than something invisible by construction.

I don't think the mechanism is solving the wrong problem — per-corpus threshold
calibration is a reasonable answer to "similarity scores aren't comparable across
embedding spaces." My disagreement is narrower: the six-state calibration taxonomy in the
brief is more granular than the consumer-facing surface needs (Q2), and the corpus/model/
prompt calibration axes named in the brief are one axis short of the one that would most
directly explain a confusing false negative if I hit one.
