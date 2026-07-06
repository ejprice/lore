# What lore's clients actually need — the three-model consult

**Date:** 2026-07-06 (P8d′, post gate re-run) · **Status:** Fable synthesis recorded;
Sonnet-5 + Opus informant sections pending (briefed BLIND to this document).
**Operator framing (verbatim intent):** LLMs — Sonnet 5, Opus, Fable — are lore's
clients; their needs are the priority. Identify what *enables* them to do the best
work possible, then engineer lore to serve that. This reframes the P8d A/B gate
(which measures calls/tokens against a pre-flip baseline) into client-value terms.
**Method precedent:** docs/design/2026-07-04-map-test-segregation.md — models as
introspective informants about their own tool-UX needs, operator-directed.

---

## Fable synthesis (first-hand: a full orchestration session consuming these tools,
## plus the P8d/P8d′ eval transcripts as usage logs)

### 1. Trust dominates everything — a tool that can lie is worse than no tool
The single wrong "dead, 0 refs" verdict (finding #53) cost more than one answer: it
taxed every future impact answer with corroboration. The session's own ledger shows
the disease progressing (#47, #48 — agents routing to grep on staleness *fear*
before any defect was confirmed). Once a client distrusts a tool, every call becomes
two, and no efficiency engineering wins that back. **Highest-value property: every
response is either true or explicitly uncertain.** The flip's honest-render work
(caveats, teach-misses, fenced bodies) is the foundation; it outranks any call-count.

### 2. The scarce resource is context, not calls — and it's information DENSITY
Every response occupies the client's window permanently. The optimization is
answer-per-token, not brevity: one 500-token response that settles a question beats
three 150-token responses that triangulate it, because each extra call also costs a
reasoning interruption (re-orient, re-decide, re-parse). The inverse also holds:
un-asked-for content actively degrades attention. Schema economy is the same point
at load time — the 14-tool surface cut every client's per-session schema cost ~3x.

### 3. Good calls vs bad calls — the distinction the A/B gate cannot see
- **Good calls convert to correctness:** lore_verify before answering (chosen
  rigor); a teach-notice retry that lands ("nearest path: X" → next call correct).
  Clients WANT to spend these.
- **Bad calls are mechanical taxes:** the elision two-step — ask for k, budget drops
  some, notice says raise-to-N, re-ask for what was already asked. The client learns
  NOTHING from the round trip. 8 of 11 gate tasks paid it.
The client-correct metrics: **output tokens per correct answer** and **taxed calls**
(mechanical re-asks), not total calls. The 11-pair calls-leg measured, in part,
nostalgia for one-call verbs whose speed was partly silence.

### 4. Stable canonical addressing is load-bearing in a way humans underrate
Finding #52's real harm wasn't a wrong eval answer — the tool was TEACHING clients a
false name (loremaster.loremaster.X), which clients then propagate into briefs,
memories, and commits. Labels/citations/keys are identifiers clients build mental
state on; drift corrupts that state silently.

### 5. Affordances beat doctrine — teach in the response, at the moment of need
The instructions block matters less than responses that carry their own next step.
Session evidence: the "raise budget to ~N" in-response hint gets USED; the
instructions LADDER ordering caused redundant cross-checks (models corroborating a
correct impact answer with map/search "because ladder" — a measured component of the
gate residual).

### Fable's derived engineering proposals
- **T10 — elide DEPTH, not BREADTH:** when the search response budget binds, keep
  ALL k hits visible with the tail as one-line stubs (identity + score + path)
  instead of dropping whole hits. The stub carries exactly the information the
  re-query was for, so the second call mostly disappears — cheaper than raising the
  default (T7), which just moves the cliff and pays tokens on every task.
- **Ladder authority line:** one instructions sentence — impact is authoritative for
  consumer/coverage questions; corroborate only on a miss — deletes the
  redundant-check habit.
- **Keep the verify rigor** (good calls; trimming them optimizes the metric against
  the client).
- **Going-forward measurement:** the 35-pair surface-neutral set, graded by client
  metrics (accuracy; tokens-per-correct-answer; taxed-calls ≈ 0) — the 11-pair
  calls-leg retires as god-metric with this rationale.

---

## Sonnet 5 informant section
*(pending — REPORT-informant-sonnet.md, briefed blind)*

## Opus informant section
*(pending — REPORT-informant-opus.md, briefed blind)*

## Synthesis + operator ruling
*(pending)*
