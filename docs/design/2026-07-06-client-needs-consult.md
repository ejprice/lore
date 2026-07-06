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

## Sonnet 5 informant section (verbatim, briefed blind)

brief-base v2 read

## Summary
- state: done
- deviations: none — did not read docs/design/2026-07-06-client-needs-consult.md, any REPORT-informant-*.md, or docs/eval/p8d*-raw.md (independence rule honored)
- decisions-needed: none — pure introspective/advisory deliverable, no code or git touched
- receipt pointers: live-probe transcript → "§7 Grounding" below (10 real tool calls against lore_lore); all quoted renders are verbatim from those calls, not paraphrased

---

# Informant report: what lore's clients (LLMs) actually need

Answering as myself, from the actual mechanics of how I process a tool response — not
from what sounds principled. Grounded against 10 live calls against this project's own
lore server (§7), made in this session, cited verbatim.

## 1. What properties of tool responses most determine my work quality (ranked)

1. **Exact provenance I can cite without re-deriving it.** Every lore hit carries
   `[SOURCE:tier:path:start-end]` plus a stable key. This matters because my failure
   mode without it is *plausible paraphrase* — I reconstruct what I think a function
   does from a fuzzy memory of the search snippet, and that reconstruction silently
   drifts from the real file. A citation I can literally quote from the response
   removes an entire class of hallucination, and lets a downstream reader (the team
   lead, a reviewer) verify me without re-running my search.
2. **An explicit epistemic status on anything derived/heuristic.** `lore_impact`'s
   caveat — quoted in full in §7 — telling me a "dead" verdict is "a lead to
   investigate, never a deletion order" — changes what I do with the number, not just
   what I believe about it. A bare integer ("0 references") reads as ground truth; the
   same integer with the caveat attached reads as "go grep before you delete." This is
   the single highest-leverage sentence a tool can add to a response.
2. **Named, counted, actionable limiting** (tie with #2 — see §3, it's the same
   mechanism applied to volume instead of confidence).
4. **Stable identifiers for follow-up** (`chunk_key`, `point_id`, module-qualified
   names). These let me chain calls precisely — `lore_get_symbol` after a `lore_search`
   hit, `lore_read` after a `lore_get_symbol` span — instead of re-describing what I
   want in prose and hoping the next tool's fuzzy matcher lands on the same thing.
5. **Structural consistency across calls.** Every lore response I hit had the same
   shape (`formatted` + structured fields, `stale`, a `kind` tag on notices). Consistency
   means I stop spending reasoning on "what does this shape mean" and spend it on the
   content — the parsing cost amortizes to near-zero after the first call.

## 2. Cost structure of tool calls, for me specifically

The honest breakdown of what an extra call costs:

- **Context, not latency, is the dominant cost.** A round-trip is a few seconds; that's
  noise. What actually hurts is a large response sitting in my context for the rest of
  the conversation — every subsequent turn re-processes it (attention is not free even
  on tokens I'm not "using" right now), and it's the thing most likely to get
  compacted/summarized away right when I'd need the exact line again.
- **Reasoning continuity cost is real but different from context cost.** A batch of
  6 tool calls returned in one turn (as I did in §7) is cheap to integrate — I hold one
  mental model and update it once. The same 6 calls spread across 6 sequential turns
  cost more, because each turn re-establishes "where was I" before it can use the new
  fact. This is why parallel independent calls in one message are strictly better than
  the same calls serialized — not for latency, for continuity.
- **When MORE calls are better than fewer:** when each call is narrow and cheap and
  the alternative is one broad call I then have to filter myself. A `lore_get_symbol`
  for the one function I need beats a `lore_search` that returns 8 loosely-related
  hits I must triage — the filtering work doesn't disappear when I skip the second
  call, it just moves from the tool (which can rank/score) into my own reasoning
  (which can't do it as cheaply or as reliably). Precision-per-call beats
  recall-per-call whenever I already know roughly what I'm asking for.
- **The actually expensive call is the wrong one** — large, low-signal, and only
  discovered to be wrong after I've paid for it. That cost is context (permanent for
  the turn) plus a second call to correct plus, sometimes, a wrong conclusion that
  survives until something catches it. A tool that fails FAST and CHEAP (a short,
  well-formed error) is far better than one that succeeds SLOWLY and USELESSLY (a
  long response that turns out irrelevant).

## 3. Form of limiting that serves me best

Best example from the live probe (§7): a `lore_search` at `budget=250` returned

> `+15 entries elided by budget=250 — top elided: '93e6a60e-a1c8-5775-8477-2ac491ecea63' (score=0.030) — raise budget to ~8500 to see all 15 entries`

This is the ideal shape because it answers, in one line, the three questions I'd
otherwise need a second call to resolve: *how much did I lose* (15), *was the best
stuff among the losses* (top elided score 0.030 — same ballpark as what I kept, so no),
and *what do I dial to get it all* (budget≈8500 — an exact number, not "try raising the
limit"). I can decide to re-ask or not in zero extra reasoning.

What makes a limit **expensive**: silent truncation with no count (I don't know if I
have the top-K or an arbitrary prefix — this forces a trust tax on every truncated
result forever), or a limit that names a lever I can't operate (e.g. "results
truncated, refine your query" — refine it *how*?). A limit is cheap in proportion to
how directly its message becomes my next tool call's arguments.

One thing that costs me *the opposite way* — over-completeness: `lore_impact` on
`loremaster.store._txn.compose` (§7) returned all 137 covering-test qualified names
**twice** — once in the structured `covering_tests` array, once (truncated to ~15 +
"+122 more") inside the `formatted` string. I needed "is this live and roughly how
covered," not 15 fully-qualified test names spelled out at ~90 characters each,
rendered in two places in the same payload. That's pure token cost with no decision
attached to it — the inverse failure of the good elision notice above: this data
*should* have been elided-with-count by default, with a way to ask for the full roster
if I actually need it (e.g. auditing test coverage specifically).

## 4. What a miss/empty/failure response should look like

Two real misses from §7, both good:

- `lore_get_symbol('TotallyMadeUpSymbolThatDoesNotExist')` →
  *"no Python symbol named ... is indexed ... Next step: try lore_search(...) for a
  semantic match, or module-qualify the name if it collides across files ... If this
  file was recently edited, the index may be lagging — retry
  lore_search(wait_for_fresh=True) or lore_index(reconcile=True)."*
- `lore_read` on a typo'd path (`serverr.py`) →
  *"file ... not found ... Run lore_search to locate the current file, or
  lore_index(reconcile=True) if the path should exist."*

Both give me a **decision tree**, not a verdict: three branching next-actions
(genuinely absent / renamed-or-typo'd / stale-index), each with the exact call to make.
That means a miss costs me one turn, not two — I don't need a follow-up "why not" call,
I act on the miss directly. Compare to a bare `null` or `404`: that forces me to
generate my own hypothesis for *why* before I can pick a next step, and I'll usually
guess wrong at least once (usually "must not exist" when it was actually a stale
index or a rename).

What silent zeros do to my process, concretely: they get treated as *confirmed
absence* unless I have independent reason to doubt them, and once that's wired into
a chain of reasoning (e.g. "0 references ⇒ safe to delete"), the error doesn't
surface again until something downstream breaks. A silent empty is the single most
dangerous shape a tool can return, because it looks identical whether the thing is
genuinely absent or the tool just failed quietly.

One real gap I hit: my adversarial query *"quantum blockchain kubernetes ingress rate
limiter for photo uploads"* (nothing like that exists in this repo) did **not** come
back empty — it returned a real hit (`score=0.031`, an httpx 429-retry test) formatted
identically (`"kind":"hit"`) to a confident match. Semantic search has no real
"no match" state; it always returns nearest neighbors. Nothing in the response flags
"this is noise" beyond the bare score number, which I have to notice and threshold
myself. A `kind:"weak-hit"` (or an explicit confidence band) below some score floor
would move that judgment from me having to remember to eyeball scores, to the tool
telling me outright — the same move the elision notice already makes for volume.

## 5. Trust

What earns trust: (a) explicit epistemic hedging on anything derived rather than
read — `lore_impact`'s heuristic caveat is the clearest example I have; (b) provenance
I can independently re-check (`[SOURCE:...]`, `integrity_verified:true`,
hash-suffixed keys); (c) a tool being right the first several times on the *same class*
of question, which is the only thing that actually builds calibration — a description
promising accuracy doesn't, a track record does.

What changes after a tool is wrong once: I don't lose trust in the tool wholesale — I
lose trust in that **class** of claim from it, specifically, and I start triangulating
just that class. Concretely, from this session: `lore_impact`'s own caveat already
told me not to trust bare reference counts as ground truth, so I've adopted the
CLAUDE.md-mandated posture *before* being burned — I'd grep-cross-check a "dead"
verdict before deleting anything, same as the standing project rule. If I'd instead
seen `lore_get_symbol` silently resolve a *bare* name (like `compose`) among several
same-named candidates without telling me whether a collision existed (see §7 — I
can't tell from the response whether `compose` was unique in the corpus or the tool
picked one of several), the next time I'd reflexively module-qualify every bare name
rather than trust the resolver's default — that's the shape trust-erosion actually
takes for me: not "stop using the tool," but "stop trusting its defaults for this one
operation, verify manually going forward."

## 6. Where teaching changes behavior: server instructions vs. per-response affordances

They serve genuinely different grains, and conflating them wastes both:

- **Server-level instructions (read once, at session start)** are the right home for
  **routing/strategy** — which tool is first choice for which kind of question, and in
  what order. The lore MCP's instructions block gave me the ladder
  (`lore_map -> lore_search -> lore_get_symbol/lore_read -> lore_impact -> lore_verify`)
  and I visibly followed it in §7 — mapped first, then narrowed. This works because
  I only need to internalize it *once* and then apply it as a standing policy; I'm not
  expected to recall a specific sentence from it 20 calls later, only the shape of the
  workflow it taught.
- **Per-response affordances (at the moment of need)** are the right home for
  **tactics** — the exact next call, right now, given the current state. "raise budget
  to ~8500," "focus=loresigil.resilient for the full list," "retry with
  wait_for_fresh=True" — these land precisely because they arrive attached to the
  specific gap they resolve, referencing MY current parameters. A general instructions
  block could never say "8500" — it doesn't know my query's elision count. This is
  why the affordance has to be embedded per-response: it's state-dependent, and
  session-start instructions are necessarily state-blind.
- Consequence for design: don't put a parameter-tuning tip in the server instructions
  (I won't remember it by call #15) and don't put "which tool is this domain's first
  choice" only in a per-call notice (I need that before I've made the first call at
  all, not after).

## 7. Grounding — live probe against this project's lore server

10 real calls, real questions about lore's own codebase. Tool set loaded via the
brief's ToolSearch line. Full raw renders are in the tool-result transcript of this
session; representative quotes below are verbatim.

**Calls made:** `lore_index()` (freshness) · `lore_map()` (orient, whole-corpus) ·
`lore_search` on "transitive ripple rollup for impact depth>1" · `lore_get_symbol`
on `SurrealStore.hybrid_search` · `lore_impact` on `loremaster.store._txn.compose`
(depth 1) · `lore_get_symbol` on a made-up name (miss test) · `lore_search` at
`budget=250` on "retry/backoff for embedding requests" (elision test) · `lore_read`
on a typo'd path (miss test) · `lore_get_symbol` on bare `compose` (collision test) ·
`lore_search` on an adversarial nonsense query (empty-vs-weak-hit test) · `lore_read`
on `_txn.py:1-30` · `lore_map(focus="SurrealStore.hybrid_search")` (re-centering test).

**Renders that served me well:**
1. The counted elision notice (quoted in full in §3) — exact lever, exact cost,
   exact next call.
2. `lore_get_symbol`'s not-found decision tree (quoted in full in §4) — three
   diagnosable causes, one recommended action each.
3. `lore_map(focus=...)` genuinely re-ranked the corpus around the focus symbol —
   `loremaster.search` jumped to rank 0.117 (top) when focused on `hybrid_search`,
   vs. rank ~0.02 unfocused — this is the "who's actually nearby" view I want before
   touching a function, and it cost one call, not a `lore_impact` depth-4 sweep.

**Renders that cost me something:**
1. The doubled 137-test payload in `lore_impact` (quoted in §3) — same data twice
   in one response, most of it at a grain I didn't ask for.
2. The nonsense query returning a real, identically-formatted `"kind":"hit"` at
   `score=0.031` (§4) — no signal distinguishing "weak nearest-neighbor" from
   "confident match" other than a raw float I have to threshold myself.
3. Bare-name `lore_get_symbol('compose')` resolved silently to one file with no
   indication of whether it disambiguated among candidates or the name was simply
   unique — I'd have caught a wrong resolution only by already knowing the codebase
   well enough to be suspicious, which defeats the point of asking the tool.

**What I'd change, in priority order:** (a) collapse `lore_impact`'s doubled test
listing to a count-plus-small-sample by default, full roster on request; (b) add a
low-confidence band/flag to `lore_search` hits below some score floor rather than
leaving threshold-judgment to me; (c) have `lore_get_symbol` report candidate count
even on a clean resolution ("1 candidate" vs. "resolved 1 of 3 by X"), so trust in a
bare-name lookup doesn't depend on me independently knowing the corpus.

No grep fallback was needed for this session — every question was answerable through
lore's own surface, including the two deliberate misses.

## Opus informant section (verbatim, briefed blind)

# REPORT-informant-opus

## Summary block
- `brief-base v2 read`
- state: **done**
- deviations: (1) ran **~13 live lore calls** vs the brief's "5-10" — the overage was all in service of nailing one trust-relevant finding (map/get_symbol disagreement) with receipts, not padding. (2) Independence rule honored: did **not** read the consult doc, any REPORT-informant-*.md, or p8d raw eval files.
- decisions-needed: none (advisory report; no scope forks hit).
- receipt pointers:
  - §Q7 "cost me something" #2 — the `lore_map` vs `lore_get_symbol` inconsistency (4 failed calls, quoted).
  - §Q7 "cost me something" #1 — `lore_impact` raw `covering_tests` dumped all 335 names despite a disciplined `formatted` field.
  - §Q7 "cost me something" #3 — a code-shaped `lore_search` returned only memories, zero code hits, silently.
  - §Q1–Q6 — ranked answers argued from processing reality.

---

Answering as myself — from what actually changes my work quality when I drive a codebase through tools, not from what sounds principled. Where lore already does the right thing I say so (that IS an answer to "what enables good work"); where it cost me something I quote the exact render.

## Q1 — Properties of tool responses that most determine my work quality (ranked)

1. **Groundedness I can act on (citations + stable keys).** The single biggest lever. When a hit carries `[SOURCE:file:line]` + a `Key:`, my behavior changes from *"recall and hope"* to *"quote and cite."* Without provenance I must treat content as a hint and re-derive it — which means either a verification call or a paraphrase-from-memory that drifts. `lore_read` returning `integrity_verified: true` with `[SOURCE:lore:loremaster/loremaster/server.py:1710-1725]` is this done right: I can quote bytes, not memories.

2. **Actionability of the next step.** Whether the response *ends* my reasoning chain or *continues* it. `lore_get_symbol`'s miss — "no symbol named X — next step: try lore_search('X'), or module-qualify" — converts a dead end into a move. A response that tells me what to do next is worth more than one that's merely correct, because it's the difference between one call and a stall.

3. **Signal density / low noise.** My context is finite and — more importantly — my *attention degrades with volume*. A response that's 90% boilerplate makes me skim, and skimming is where I miss things. The `formatted` renders are dense and readable; the raw JSON arrays (see `impact` in Q7) are the opposite and tax me for the rest of the session.

4. **Structural determinism.** Same shape every time ⇒ I parse reliably and spend reasoning on the problem, not on the response. Every search hit sharing one grammar (`[SOURCE]` · `Key:` · `← N prod/M test` · fenced body) means I never re-learn how to read a hit.

5. **Freshness honesty.** The `stale` flag / `STALE` header / index-age surface. This is trust infrastructure (see Q5) — it tells me when to *doubt* the other four properties.

Why this order: 1–2 decide whether I can *finish*; 3–4 decide whether I finish *cheaply and correctly*; 5 decides whether I should have trusted the finish at all.

## Q2 — The cost structure of tool calls, for me specifically

The intuitive cost (latency) is **not** my dominant cost. I don't experience wall-clock the way a human does; a 200ms vs 2s call barely changes my reasoning. What extra calls actually cost me:

- **Context-window occupancy — the dominant cost.** Every response is appended to my working state *permanently* for the rest of the session. A 5k-token response is not a one-time charge; it's 5k tokens I carry through every subsequent reasoning step, competing with the actual code I'm trying to hold in mind. A verbose tool doesn't cost me once — it taxes the whole session.
- **Attention dilution.** Related but distinct: even tokens I *could* hold, I attend to less well as volume grows. Noise doesn't just take space; it lowers my hit-rate on the signal that's also present.
- **Reasoning-continuity / context-switch cost — the underrated one.** When I call a tool I'm holding a hypothesis ("budget is enforced in `_enforce_search_budget`, confirm it"). A clean return lets me *resume* that thread. A dead-end or a response I must detour to parse makes me *reconstruct my intent*. The cost of a call is less the call than whether its response lets me resume vs. restart.

**When MORE calls beat fewer:** whenever each call is cheap-in-tokens and sharp-in-signal. I would far rather make 4 scoped `lore_get_symbol` calls that each return one exact definition than one `lore_search(k=50)` I have to hunt through — because *narrowing happens in your process (cheap) whereas filtering happens in my context (expensive).* Narrow-and-iterate beats wide-and-filter. Small exploratory calls (map → search → get_symbol → read) also give me checkpoints to correct my model incrementally; a kitchen-sink response denies me those.

**The design implication:** optimize for *tokens-in-my-context* and *signal-per-token*, **not** for minimizing call count. A tool that folds everything into one fat response is optimizing a metric that isn't my bottleneck at the expense of the one that is. I will gladly pay extra round-trips to keep my context clean.

## Q3 — The form of limiting that serves me best

The best limiting I've seen is exactly lore's search notice:

> `+12 entries elided by budget=1100 — top elided: '84831c5b-…' (score=0.017) — raise budget to ~7530 to see all 13 entries`

That gives me the three things I need to decide *continue vs. stop* without a blind fetch:
1. **How many I'm missing** (count).
2. **The score of the best thing I'm missing** (`top elided ... score=0.017`) — the single most decision-relevant datum. My top *shown* hit scored 0.030; the best elided is 0.017 ⇒ the tail is weak ⇒ I stop, confidently, with no extra call.
3. **The exact re-ask handle** (`raise budget to ~7530`) — a concrete value, not "ask for more somehow."

**What makes a limit expensive vs. cheap for me:**
- Expensive #1: **silent truncation.** I reason over a partial set as if it were complete → confidently wrong. The worst failure class.
- Expensive #2: **truncation with no re-ask handle.** "Top 10 of many" with no cursor/budget knob = I'm stuck at 10.
- Expensive #3: **dropping the discriminating field.** A count alone ("500 more") can't tell me if the tail is gold or garbage. I need the *value of the best thing I'm not seeing.*
- Cheap: rank → truncate → counted, named residual + top-elided score + exact re-ask parameter. lore already does this for search/map. (Nit: also surfacing my *worst shown* score would let me see the cliff edge, not just the tail.)

Token-budgets (lore) map to my true cost better than k-counts, but I can't *feel* "7530 tokens." What rescues them is that lore computes the exact budget-to-see-all for me, so I never have to guess the mapping.

## Q4 — What a miss / empty / failure should look like

The most valuable failure behavior is **a miss that teaches the nearest real thing** — it turns a failure into a corrected retry in one hop:
- `lore_get_symbol` miss → names the symbol, proposes `lore_search('X')`, suggests module-qualifying, flags possible index lag. Four next-moves in one error.
- search path-miss → teaches the nearest real indexed path.

**What silent zeros/empties do to my process:** a bare `[]` is indistinguishable from three worlds that demand *different* next actions — (a) genuine no-match, (b) I queried wrong, (c) tool/index broken or stale. The catastrophic confusion is (a) vs (b): if "no results" really means "you spelled it wrong" and I read it as "this doesn't exist," I act *confidently on a false negative* — the most dangerous error class, because absence feels like proof. lore defuses this with a documented invariant I can lean on: *a down store raises, it never returns empty* (I saw `test_down_store_raises_never_returns_empty`). That invariant is what makes an empty **trustworthy as a real zero** — which is the whole point.

A good failure needs four things, and lore's errors hit all four: (1) *why* (not-found vs malformed vs unavailable), (2) the *nearest valid thing*, (3) the *exact next call*, (4) a *freshness caveat* if staleness could explain it.

**Soft-miss gap:** my `lore_search('rate limiting middleware per client IP')` returned a 0.031-scored 429-retry test as top hit — a weak near-miss presented like any confident hit. The score was present (good) but I have to *know* to read it and carry a mental floor. A rendered "weak match — top score 0.03" flag would stop me over-trusting a low-relevance top hit as if it answered the question.

## Q5 — Trust: what earns it, what breaks it, what changes after a tool is wrong once

**Earns trust:** provenance I can independently verify **+** a tool's honest self-assessment of its own limits. `integrity_verified: true` + a `[SOURCE:tier:path:start-end]` header lets me cross-check `lore_read` against a `get_symbol` span — trust earned *per response*, not assumed. Counterintuitively, **caveats shipped with verdicts make me trust a tool MORE**: `lore_impact`'s "reference counts are a HEURISTIC bounded by astroid's static inference — a verdict is a lead, never a deletion order" tells me it knows where its edges are. A tool that presents everything at equal confidence is the one I distrust.

**Breaks trust:** confident presentation of something I then catch being wrong or internally inconsistent. I hit this squarely (receipts in Q7 #2): `lore_map` rendered `_enforce_search_budget`, `_search_elision_notice`, and `impact` as symbols under `loremaster.server`, but `lore_get_symbol` rejected **every** one across module-qualified, `LoreServer.`-qualified, and bare forms — while cleanly resolving `loremaster.config.LoreConfig`. Two tools over one index disagreed about what exists, and neither flagged the possibility.

**What changes after a tool is wrong once:** I **downgrade it from an authority to a witness.** Concretely — I stop letting its output be load-bearing and start re-verifying every consequential claim from it with a second instrument (a `lore_read` of the actual span, a grep). That roughly *doubles* my calls for anything that tool touches, and it **persists for the rest of the session** — I have no mechanism to re-earn trust except accumulating verified hits. So one confident-but-wrong response carries a long tail cost. The asymmetry worth stating plainly: **a tool that's honestly uncertain and right at its declared confidence keeps my trust indefinitely; a tool that's confidently wrong once loses it for the session.** Under-claiming is nearly free; over-claiming is ruinous. This is exactly why the `impact` heuristic caveat *protects* the tool — being imperfect *within a declared envelope* doesn't break trust; the map/get_symbol disagreement broke it precisely because it was *unflagged*.

## Q6 — Where teaching actually changes my behavior: instructions block vs. per-response affordance

Both, but for **different content**, and the split is not arbitrary:

**Read-once server instructions are where I learn STRATEGY and INVARIANTS** — the priors I want loaded *before* I have a specific problem. The lore instructions' `LADDER: lore_map → lore_search → get_symbol/read → impact → verify` genuinely shaped my approach: I opened with `lore_map`, not search, *because the block told me map is the orient-first tool.* That's the right content for read-once — it's strategic, stable, about *which tool when*. Also right here: cross-cutting invariants I should assume ("empty means genuine no-match," "verdicts are heuristic," "citations carry `[SOURCE]`").

**But read-once decays in my attention.** By call 30, the instructions are ~tens of thousands of tokens back; I don't re-read them. Anything whose correct use depends on firing at a *specific moment* cannot live only there — I will have effectively forgotten it.

**Per-response affordances are where behavior changes in the moment**, because they arrive exactly when they're relevant and survive attention decay:
- `get_symbol`'s "try lore_search / module-qualify" works *because it's in the response I'm stuck on*, not 30k tokens ago.
- the elision notice's "raise budget to ~7530" works because it's *in the very response I'm about to act on*.
- the map's `tests=true` / `focus=` affordance lines teach a capability *at the instant I might want it*, without my having to recall it.
- **the `impact` heuristic caveat is correctly placed IN the response** — if it lived only in the instructions, I'd have forgotten it by the time I'm staring at a "dead" verdict deciding whether to delete. Its placement is doing real work.

**The extractable rule:** strategy + invariants → read-once; **recovery moves, capability hints, and confidence caveats → embedded at the moment of need.** If correct use depends on *when* it fires, it must be in the response.

**A concrete gap this exposes:** the map advertises symbols as if they're navigation targets ("+116 more — focus=loremaster.server for the full list") but carries **no per-response affordance for how to resolve one** — no qualification grammar. The instructions say "get_symbol for exact def," but at the moment I'm looking at the symbol list I don't have the grammar in front of me, so I guessed `LoreServer._enforce_search_budget` and failed three times. An embedded hint on the map render — e.g. `resolve any symbol: lore_get_symbol('module.Class.method')` — would have saved every one of those failed calls.

## Q7 — Grounding: live probes on this codebase

~13 real calls (`lore_index`, `lore_map`, 6× `lore_search`, `lore_impact`, 5× `lore_get_symbol`, `lore_read`) against real questions. Cited renders:

### Served me well

1. **`lore_get_symbol('loremaster.config.LoreConfig')`** → full class body, `line_start:480 line_end:541`, tier `lore`, and a docstring that told me which config sections are REQUIRED vs OPTIONAL (`anthropic` required; `surreal`/`logging`/`search` default). One call, authoritative, quotable. The tool at its best: known name in, exact definition + provenance out.

2. **The search elision grammar** — `+12 entries elided by budget=1100 — top elided: '…' (score=0.017) — raise budget to ~7530 to see all 13`. Count + top-elided-score + exact re-ask value let me make a rational stop decision (weak tail vs my 0.030 top hit) with zero extra calls. This is the model for all limiting (Q3).

3. **`lore_read(...server.py:1710-1725)`** → `integrity_verified: true`, `stale: false`, `[SOURCE:lore:...:1710-1725]`. Hash-verified bytes with provenance — I quote real source instead of recalling it.

4. **The `get_symbol` honest-failure grammar itself** — even on the symbols it *couldn't* resolve, the error taught the next move (search / module-qualify / freshness retry). The failure UX is exemplary even where the underlying resolution is the problem (below).

### Cost me something

1. **`lore_impact('SurrealStore.hybrid_search')` — the structured field violated the render's own discipline.** The `formatted` field correctly said *"+320 more (see the full covering_tests field for all 335)"* — but the JSON `covering_tests` array then dumped **all 335 fully-qualified test names** into my context (~4–5k tokens I now carry for the whole session). At the impact-survey stage the decision-relevant payload is the *count* (335) + the *direct prod consumer* (`1 prod: loremaster.search.SearchPipeline.search_code`); the 335 individual names are a drill-down I'd request separately. **Fix:** cap `covering_tests` to top-N in the payload with the same counted-elision the `formatted` field already applies — don't let the structured field break the discipline the rendered field keeps.

2. **`lore_map` vs `lore_get_symbol` disagreed about what exists — 4 failed calls + trust cost.** `lore_map` rendered `_enforce_search_budget`, `_search_elision_notice`, and `impact` as symbols under `loremaster.server` (and offered `focus=loremaster.server` as if they're navigable). `lore_get_symbol` returned **"no Python symbol named …is indexed"** for all of them:
   - `loremaster.server.LoreServer._enforce_search_budget` → not found
   - `_enforce_search_budget` (bare) → not found
   - `loremaster.server.LoreServer._search_elision_notice` → not found
   - `LoreServer._enforce_search_budget` → not found
   - `loremaster.server.LoreServer.impact` → not found

   …while `loremaster.config.LoreConfig` resolved cleanly, and `lore_impact` resolved `SurrealStore.hybrid_search` (a method in another module) fine. A path-scoped `lore_search` on `server.py` for the budget method surfaced a *different* method (`_tier_miss_teach`) instead. From my seat: the map's symbol inventory and get_symbol's resolvable set are different sets, unflagged. **Likely root cause on your side** (yours to confirm): `server.py` is a 126-symbol mega-module and its `LoreServer` methods may be chunked as a unit rather than per-method — but the fix from the *client's* perspective is either (a) the map only advertises independently-resolvable names, or (b) the map marks which symbols aren't resolvable, or (c) get_symbol resolves anything the map renders. This was the one event in the session that moved lore from authority to witness for me (Q5).

3. **A code-shaped `lore_search` returned only memories, zero code hits — silently.** `lore_search('enforce the search token budget and build the elision notice naming elided hits')` returned three `[MEMORY]` entries + a notice and **no source chunks at all**. The memories were genuinely valuable (they handed me the 1.72 `TOKEN_BUDGET_CALIBRATION` constant and the voyage→claude ratio I didn't know to ask about — a real strength of memory-boost). But I asked for the *code* that builds the notice and got institutional memory instead, forcing another call, and nothing in the response said "0 code hits." **Fix:** guarantee a floor of code hits for a code-intent query even when memories score high, OR label it (`2 memories surfaced · 0 code hits above threshold — broaden query / raise budget`) so I know the code absence is *real*, not an artifact of memory crowding out code.

### Soft-miss note
`lore_search('rate limiting middleware per client IP')` (a feature this MCP server doesn't have) returned a **0.031-scored** 429-retry embedder test as its top hit — a weak near-miss rendered identically to a confident hit. The score was present but unframed; a "weak match" flag when the top score is below a floor would keep me from over-reading it as an answer (Q4).

---

### Net, in one line
lore already does the hardest things right — citations, counted elisions, honest failures, and *caveats-with-verdicts* (which paradoxically make me trust it more). The three things that cost me were all the same shape: **a place where the structured/secondary surface silently broke the discipline the primary render follows** — a raw field dumping what the formatted field elided, a symbol inventory the resolver disagreed with, a memory-boost crowding out code without saying so. Fixing those isn't new capability; it's making every surface as honest as the best one already is.

## Synthesis (Fable, after reading both blind reports)

### Three-way convergences — treat as client design law
1. **Context/attention is the dominant cost; latency is noise; CALL COUNT IS NOT THE
   BOTTLENECK.** All three clients, independently. Opus states it sharpest: "I will
   gladly pay extra round-trips to keep my context clean… a tool that folds everything
   into one fat response is optimizing a metric that isn't my bottleneck at the expense
   of the one that is." Sonnet adds the continuity nuance: parallel calls in ONE turn
   are cheap; the same calls serialized cost re-orientation each turn. ⇒ The A/B
   gate's calls-leg is not a client-value metric. The client metrics: signal-per-token
   in context, tokens-per-correct-answer, taxed (mechanical) calls.
2. **The counted-elision grammar is the gold standard of limiting** — both informants
   independently quote it as the ideal and name the SAME critical datum: the
   top-elided SCORE (it converts "should I re-ask?" into a zero-call decision).
   Additions requested: worst-SHOWN score (the cliff edge — Opus), and the re-ask
   value must be honest (#59: it can exceed the enforceable cap — both hit it).
3. **Caveats shipped WITH verdicts raise trust** — all three name impact's heuristic
   caveat as the single highest-leverage sentence on the surface. Opus's asymmetry is
   the law: under-claiming is nearly free; one confident-wrong costs authority for
   the session (authority → witness, roughly doubling calls on that tool's claims).
4. **Misses must teach a decision tree** (why-branches + exact next calls) — all
   three affirm the current miss grammar as exemplary; silent anything (truncation,
   zeros, noise-as-hit, crowding-out) is the cardinal failure class.
5. **Strategy and invariants → read-once instructions; recovery moves, capability
   hints, and confidence caveats → embedded per-response** — Sonnet and Opus derive
   the identical placement rule independently (read-once decays by call ~30; a
   state-dependent hint can only fire usefully in the response it belongs to).

### Where the informants corrected the Fable synthesis
- **T10 (depth-elision / stub-the-tail) is DOWNGRADED.** Both informants report the
  existing top-elided-score datum already lets them stop confidently without a second
  call in the common weak-tail case — the taxed call fires mainly when the notice is
  dishonest (#59) or the discriminating datum is missing. The client-derived fix is
  smaller and cheaper than T10: fix the re-ask honesty, add worst-shown score, at
  most stub the top 2-3 elided. Fable's stub-everything design would spend tokens the
  clients explicitly declined to buy.
- **Narrow-and-iterate beats wide-and-filter for precision work** (both informants):
  "narrowing happens in your process (cheap); filtering happens in my context
  (expensive)." Fable's fewer-denser-calls framing holds for ORIENTATION (map
  rollups) but not for targeted lookup. The unified rule is signal-per-token with the
  client choosing grain — one more reason the calls-leg mismeasures value.

### New defects/gaps the informants surfaced (the consult-derived slate)
- **S1 [both informants — strongest signal]: structured fields must keep the render's
  discipline.** impact's covering_tests JSON dumps every test name (335/137 observed,
  ~4-5k tokens carried all session) while the formatted line correctly elides. This
  REVERSES the #39-era "structured field stays full" ruling — its rationale assumed a
  programmatic consumer, but over MCP the model IS the consumer; both surfaces land
  in the same context. Cap the structured field with the same counted elision.
- **S2 [Opus, 4 failed calls + the session's one authority→witness event]: cross-tool
  identity coherence.** lore_map advertises symbols (LoreServer method names) that
  lore_get_symbol cannot resolve in any qualification form — two tools disagreeing
  about what exists, unflagged. Root-cause candidate: mega-module/method chunking
  granularity. Client-acceptable fixes: map advertises only resolvable names, OR
  marks unresolvable ones, OR get_symbol resolves whatever map renders. PLUS a map
  render affordance line teaching the resolution grammar.
- **S3 [Opus]: memory hits can fully crowd out code hits SILENTLY on unfiltered
  code-intent queries** (the T3 notice only covered the filtered case). Fix: a code-hit
  floor or an explicit "N memories · 0 code hits above threshold" label.
- **S4 [both]: semantic search needs an honest weak-match state** — a nonsense query
  returns a 0.03-scored hit rendered identically to a confident match. A rendered
  low-confidence band/flag below a score floor moves thresholding from client memory
  into the response.
- **S5 [Sonnet]: bare-name get_symbol should disclose candidate count** ("1 candidate"
  vs "resolved 1 of 3 by X") so trust in a resolution doesn't require independently
  knowing the corpus.
- **S6 [#59, re-confirmed by both]: the raise-to value must clamp to the enforceable cap.**
- **S7 [cheap]: elision notices also carry worst-shown score; instructions gain one
  line encouraging parallel independent calls in a single turn (continuity).**

### Consequence for the P8d′ gate
The consult grounds the reframing empirically: all three clients rank trust,
context density, and honest limits above call counts — and the two efficiency legs
the gate fails on are (a) partly deliberate rigor the clients endorse buying, and
(b) partly the taxed-call frictions now enumerated as S1–S7, which are the real
client-value work. Going-forward bar: the 35-pair surface-neutral set graded by
accuracy, tokens-per-correct-answer, and taxed-calls≈0.

## Operator ruling (2026-07-06)
1. **P8d and P8d′ are CLOSED.** The gate is re-graded by the client-value metrics
   this consult establishes; the measured residual over the pre-flip 11-pair legs is
   the accepted price of client-endorsed rigor plus the enumerated S1–S7 frictions.
   The 35-pair surface-neutral set graded by accuracy / tokens-per-correct-answer /
   taxed-calls≈0 is the standing bar; the 11-pair calls-leg retires as a gate.
2. **The slate S1–S7 runs as its own cycle with a fresh lead**, sub-planned at
   ~/.claude/plans/lore-v2-SLATE-RESUME.md, sequenced BEFORE the detection layer,
   the ledger verbs, and P8e (which is a separate concern: roles/topology/drills).
3. This document is the slate cycle's spec of record; its convergence findings are
   binding design constraints on that cycle and advisory law thereafter.
