# REPORT-pkgscout-loresigil

## SUMMARY BLOCK

`brief-base v6 read`

- **state**: done
- **deviations**: none. Read-only respected — no code/test/config/`pyproject.toml` touched; this
  report is the only file written.
- **coverage**: all 12 production files of `loresigil/loresigil/` read in full (3,901 LOC, verified
  by `wc -l`, measured 2026-07-25 at `6654be0`). Every candidate below was probed empirically
  against the named library version; no verdict rests on an assumption about a library.
- **tool honesty**: lore's index watches the MAIN checkout, not this worktree (#125). **Every
  structural answer here came from `grep` + `Read` in the worktree, stated as a fallback per the
  dogfood protocol.** `lore_*` was not consulted — for a 12-file read-in-full scope the index would
  have answered about a different tree, which is worse than honest grep. No friction filed: this is
  #125 working as documented, not a new gap.
- **provenance receipt (#140)**: probes import the worktree, asserted not assumed —
  `loresigil.resilient.__file__ = /home/ejprice/PycharmProjects/lore-pkt11i/loresigil/loresigil/resilient.py`,
  `is_relative_to(lore-pkt11i) == True`. The worktree has its own `.venv`.

### Ranked verdicts — ordered by what a WRONG CHOICE COSTS, not by convenience

| # | Symbol | Library | Verdict | Cost if left/got wrong |
|---|---|---|---|---|
| 1 | `resilient.compute_backoff_delay` | `tenacity.wait_exponential_jitter` | **KEEP loop + FIX (hand-roll jitter)** | **LIVE DEFECT: zero jitter → correlated retry herd into the 429 guard** |
| 2 | `resilient.split_to_fit` | `tokenizers` `.offsets` | **REPLACE-WITH-ADAPTER** | Silent vector-quality loss: **over-splits 60%** (32 pieces where 20 fit), diluting mean-pool |
| 3 | `resilient.mean_pool` | `numpy` 2.5.1 | **REPLACE-WITH-ADAPTER** | Correct today; 2.8× on the hottest per-input path |
| 4 | `batching.run_in_windows` | `aiometer` 1.0.0 | **REPLACE-WITH-ADAPTER** | Window barrier stalls throughput; **no rate limiting exists at all** |
| 5 | `batching.build_batches` | `more_itertools.constrained_batches` | **REPLACE** | Low: byte-identical over 3,000 randomised trials |
| 6 | `_post` / `request_fn` `.json()` | `orjson` 3.11.9 (already in `uv.lock`) | **REPLACE** | 5.4× decode on the real 32×2048 payload (20.9 ms → 3.8 ms) |
| 7 | L2 norm: `mean_pool` vs `testing._vector_for` | stdlib `math.hypot` | **FIX (ONE IMPLEMENTATION)** | Two impls of one policy; they **disagree** at overflow/underflow |
| 8 | `resilient.quarantine_vector` | `numpy` | **KEEP + trigger** | Only 1.4× — conversion eats the gain |
| 9 | `voyage_context._split_usage_by_doc` | `apportionment` 1.0 | **KEEP + trigger** | Package matches output but is a research toolkit |
| 10 | `voyage_batch.encode_batch_jsonl` / `_iter_jsonl` | `jsonlines` | **GENUINELY BESPOKE** | Nothing to gain; stdlib is the right size |
| 11 | `tokens.VoyageTokenCounter` DCL | `functools.cache` | **KEEP + trigger** | Cosmetic |
| 12 | Retry *orchestration* (2 loops) | `tenacity` / `stamina` | **KEEP + RE-OPEN TRIGGER** (#202 model) | Churning proven, guarded, domain-shaped code is the worse trade |

### Decisions needed from the operator

1. **#1 is a live defect, not a packaging preference.** Fixing it breaks an existing exact-equality
   test pin (`test_voyage_context.py:556`, `recorded_delays == [compute_backoff_delay(0)]`). Fix now
   or ledger? My recommendation: **fix now** — see §1 for why the 2-line hand-roll is the *correct*
   side of the packages rule here.
2. **#2 changes vector values** for any input that ever hits the sub-split path. It is a quality
   *improvement*, but it is not byte-identical to what is in the corpus today. Re-index required, or
   accept mixed provenance?
3. **#4** adds a dependency to gain rate limiting loresigil currently does not have. Adopt
   `aiometer`, or hand-roll a semaphore and stay dependency-free (the semaphore does not give the
   rate limiter)?

### Receipt pointers
- §1 jitter measurement · §2 over-split + non-ASCII offset probe · §3 equivalence table (2.776e-17)
- §4 barrier-stall timing · §5 3,000-trial differential · §7 overflow divergence table
- §13 out-of-mission findings raised under scope law

---

## Method note — what "library-verified" means in this report

Every `[library-verified]` claim below was produced by executing the library **in this worktree's
interpreter** against **loresigil's own imported production symbols**, not read from documentation.
Where the docs and the measurement disagreed, the measurement won and the disagreement is reported
(§2 is exactly such a case, and it would have produced a wrong recommendation had I trusted the doc).

Marks: **[source-verified]** = read in `loresigil/` at `6654be0` · **[library-verified]** = executed,
version named · **[my judgement]** = my call, not a measurement.

---

## 1. `resilient.compute_backoff_delay` — **the retry ladder has NO JITTER**

**What it does** [source-verified]: `min(BACKOFF_BASE_S * BACKOFF_GROWTH**attempt, BACKOFF_CAP_S)`
= `min(1.0 * 2**n, 30.0)`. It is the **shared** delay formula: `resilient.ResilientEmbedder._backoff`
and `voyage_context.VoyageContextEmbedder._backoff` both call it. The sharing is genuine and good —
this is the DRY seam working.

**The defect.** The formula is **purely deterministic** [library-verified, measured]:

```
loresigil compute_backoff_delay — 3 draws per attempt:
  attempt 0: [1.0, 1.0, 1.0]      attempt 3: [8.0, 8.0, 8.0]
  attempt 1: [2.0, 2.0, 2.0]      attempt 4: [16.0, 16.0, 16.0]
  attempt 2: [4.0, 4.0, 4.0]      attempt 5: [30.0, 30.0, 30.0]

tenacity 9.1.4 wait_exponential_jitter(initial=1, max=30, exp_base=2, jitter=1):
  attempt 1: [1.807, 1.449, 1.868]   attempt 4: [8.664, 8.674, 8.459]
  attempt 2: [2.656, 2.953, 2.269]   attempt 5: [16.255, 16.298, 16.899]
  attempt 3: [4.992, 4.667, 4.522]   attempt 6: [30.0, 30.0, 30.0]
```

I grepped the whole package for any randomisation: **`grep -rn "random\|jitter\|uniform"
loresigil/loresigil/` returns hits ONLY inside `data/voyage4_tokenizer.json` (BPE vocabulary
entries — `"Ġjitter": 84392` etc.). Zero hits in any `.py` file.** [source-verified]

**Why it costs.** `run_in_windows` puts 2 (TEI) or 4 (cloud/context) requests in flight
concurrently. A 429 — which `resilient.py`'s own docstring names as "the TEI 64-concurrency DOS
guard" — hits all in-flight requests at once. Every one then retries at **exactly** t+1s, t+3s,
t+7s, t+15s, t+31s. The herd that triggered the rate limit re-forms, in lockstep, five times. The
concurrency is modest so this is a degradation not an outage — but it is the precise failure shape
this repo's own `CLAUDE.md` §"ONE IMPLEMENTATION" records as costing an incident (#102's
deterministic jitter, cloned into a sibling with a *different* wrong jitter).

**Which side of the packages rule?** I investigated rather than assumed, and the answer is
**hand-roll the 2 lines** — the correct side of the rule:

- `tenacity`'s wait strategies are **not standalone delay functions**. `wait_exponential_jitter`
  takes a `RetryCallState`. It is callable with a stub exposing only `attempt_number`
  [library-verified — that is how I produced the table above] — but relying on "only that attribute
  is read" is coupling to an unpinned implementation detail [my judgement].
- Adopting tenacity's *loop* is item #12 and I recommend against it.
- So the package does not do **this** job (a pure `int -> float` delay), and the rule's second side
  applies: hand-roll the gap, minimal surface, maximal verifiability.

**Recommended fix** — one function, both call sites already route through it:

```python
_BACKOFF_JITTER_S: float = 1.0   # full-jitter band added to each delay

def compute_backoff_delay(attempt: int, *, rng: random.Random | None = None) -> float:
    base = min(BACKOFF_BASE_S * (BACKOFF_GROWTH**attempt), BACKOFF_CAP_S)
    return base + (rng or random).uniform(0.0, _BACKOFF_JITTER_S)
```

**The existing pins constrain the fix — and they react DIFFERENTLY.** There are exactly two, and I
read both [source-verified]:

| pin | assertion | under `base + uniform(0, 1.0)` | under AWS-style full jitter `uniform(0, base)` |
|---|---|---|---|
| `test_voyage_context.py:556` | `recorded_delays == [compute_backoff_delay(0)]` — **exact equality** | **BREAKS** | **BREAKS** |
| `test_resilient.py::test_backoff_is_exponential` | `delays[0] < delays[1] < delays[2]` — **strict monotonic** | survives, but see ⚠ | **BREAKS routinely** |

⚠ The monotonic pin survives the additive band only *just*: with base 1/2/4 and a 1.0 band, delay₀
∈ [1,2] and delay₁ ∈ [2,3] — the bands **touch at exactly 2.0**, so `delays[0] < delays[1]` is
theoretically violable (measure-zero for a continuous uniform, but the strict `<` is doing real
work). Widen the band beyond 1.0, or adopt full jitter, and that pin fails **routinely** — it would
be diagnosed as flakiness, which `CLAUDE.md` records as a builder verdict that is never permitted.

This is why the jitter band width is not a free parameter: **it is pinned by an existing test whose
author was pinning something else.** The additive `uniform(0, 1.0)` form I recommend is the widest
band compatible with the current suite.

**Proving controls** (both required):
1. **Mutation proof of sharing** (`CLAUDE.md`: routing is not sharing) — change
   `_BACKOFF_JITTER_S`, assert **both** `ResilientEmbedder` and `VoyageContextEmbedder` retry pins
   move. A caller that stays green owns a private copy.
2. **A statistical pin, not an equality pin**: over N draws at one attempt, assert
   `len(set(delays)) > 1` and `base <= d <= base + jitter`. The *reason* the current code has no
   jitter is that the surviving pin is an exact equality — **the test shape forbids the fix**. This
   is the "tests written before a semantic change certify the OLD world" pattern from `CLAUDE.md`:
   the suite is green partly *because* it asserts the deterministic corpse.

> ⚠ **Operator decision #1**: the fix requires rewriting `test_voyage_context.py:556` from an
> equality to a range/statistical assertion, and consciously accepting the band-width bound above.
> That is a semantic change to load-bearing tests and belongs to you, not to me.

---

## 2. `resilient.split_to_fit` — character bisection over-splits by 60%

**What it does** [source-verified]: recursively bisects a string **at the character midpoint** until
every piece's token count fits the cap. Consumers: `TEIEmbedder._presplit` (the client-side
pre-split on *every* document path) and `ResilientEmbedder._embed_over_length` (the 422 backstop).
Its output is then **mean-pooled back into one vector** — so piece count directly determines how
much a vector is diluted.

**The measurement** [library-verified: `tokenizers` 0.23.1, the pinned `voyage4_tokenizer.json`, on
code-shaped input of 12,000 chars / 4,000 tokens, cap=200]:

| | pieces | concat == source | max tokens/piece | time |
|---|---|---|---|---|
| hand-rolled `split_to_fit` | **32** | True | **126** (cap 200) | 0.0266 s |
| offsets adapter | **20** | True | **200** (cap 200) | 0.0051 s (**5.3×**) |

Character bisection is blind to token density, so it halves past the point of need: it produced 32
pieces averaging 126 tokens against a 200 cap. That is **60% more pieces than necessary**, and every
extra piece is (a) an extra input in the request and (b) an extra vector diluting the mean-pool. The
degradation is silent — nothing measures it.

**The trap I would have shipped had I trusted the docs.** The obvious library answer is
`Tokenizer.enable_truncation(max_length, stride=...)` with `Encoding.overflowing`. **Measured, it
does not do the job** [library-verified]:

```
stride= 0: primary=200 overflow_windows=0 covered=200  full=2400  FULL_COVERAGE=False
stride=16: primary=200 overflow_windows=0 covered=200  full=2400  FULL_COVERAGE=False
```

It **truncates** — 200 of 2,400 tokens — and populates no overflow windows in this configuration.
Recommending it would have silently discarded 92% of every over-length input. This is the brief's
"does the job is verified by investigation" clause earning its keep.

**What does work: `.offsets`, one tokenization.** The make-or-break question is offset semantics —
byte offsets would corrupt every non-ASCII input under `str` slicing. Verified [library-verified]:

| input | chars | bytes | last offset | char semantics? |
|---|---|---|---|---|
| `héllo wörld ünicode` | 19 | 22 | 19 | **True** |
| `日本語のテキストです` | 10 | 30 | 10 | **True** |
| `emoji 🚀🔥 mixed ascii` | 20 | 26 | 20 | **True** |
| `naïve café résumé` | 17 | 21 | 17 | **True** |

Offsets are **character** offsets. One subtlety worth recording: for the emoji string, concatenating
*per-token* offset spans does **not** rebuild the source (`contiguous_rebuild_ok=False`) — the
pre-tokenizer leaves gaps. The adapter is safe anyway **because it slices contiguous ranges of the
original string** (`text[start:end]` where `end = offsets[i][0]`) rather than joining per-token
spans. Roundtrip verified on all three hostile corpora [library-verified]:

```
cjk    pieces= 38 concat_ok=True max_tok=64 over_cap=0
emoji  pieces= 47 concat_ok=True max_tok=64 over_cap=0
mixed  pieces= 43 concat_ok=True max_tok=64 over_cap=0
```

**Verdict: REPLACE-WITH-ADAPTER.** `tokenizers` (already a declared dependency) does the hard part —
exact tokenization with a character-offset map. The gap is the windowing loop: **~10 lines**.

**Proving controls**: (a) `"".join(pieces) == text` over a hostile corpus (CJK, emoji, combining
marks, mixed) — the invariant the current docstring already promises; (b) `max(count(p)) <= cap` for
every piece; (c) a **discrimination** pin — assert piece count is within +1 of the theoretical
minimum `ceil(total_tokens/cap)`, which the *current* implementation **fails** (32 vs 20). Without
(c) the swap looks like a no-op and its whole value is untested.

> ⚠ **Operator decision #2**: this changes vector values for any input that has ever taken the
> sub-split path. Better vectors, but not the ones in the corpus.

---

## 3. `resilient.mean_pool` — numpy, with the guard kept

**What it does** [source-verified]: dimension-agreement check → component-wise sum in a nested
Python loop → divide by count → `math.sqrt(sum(c*c))` → divide. Returns `None` on empty, ragged, or
zero-norm. **It is correct** — I checked the maths, the guards, and the failure modes; this is not a
bug report.

**Why it is hot**: `TEIEmbedder._embed_with` calls `mean_pool(grouped[i])` for **every input**,
including the overwhelmingly common **single-piece** case — so a normal 2,048-dim document pays
~8,000 interpreted float ops to re-normalise an already-normalised vector.

**Measured** [library-verified: numpy 2.5.1, dim 2048, 3,000 iterations, against the imported
production `mean_pool`]:

| case | hand-rolled | numpy adapter | speedup |
|---|---|---|---|
| 1×2048 (the common TEI path) | 1.113 s | 0.394 s | **2.8×** |
| 4×2048 | 2.127 s | 0.771 s | **2.8×** |

**Equivalence**: max abs difference **2.776e-17** across 160 cases (piece counts 1–8, dim 2048) —
sub-ULP for unit-magnitude components. Edge-case parity holds exactly:

```
ragged   hand=None  adapter=None
zeronorm hand=None  adapter=None
empty    hand=None  adapter=None
```

**The adapter is required, and here is precisely why** [library-verified]: my first attempt delegated
the ragged check to numpy and **crashed** —

```
ValueError: setting an array element with a sequence. The requested array has an
inhomogeneous shape after 1 dimensions. The detected shape was (2,) + inhomogeneous part.
```

`np.asarray` **raises** on ragged input in numpy 2.x rather than building an object array. So the
existing explicit `any(len(v) != dim ...)` guard **cannot be delegated** — it must be kept, with
numpy doing only the arithmetic. A naive "just use numpy" swap turns a documented `None` return into
an uncaught `ValueError` on the exact defence-in-depth path the docstring exists for.

**Verdict: REPLACE-WITH-ADAPTER** — gap = the ragged/zero-norm guards, ~6 lines, all already written.

**Proving control**: tolerance-stated equality (`max |hand - new| < 1e-15`) over randomised piece
sets **including** the 1-piece case, plus the three `None` parities above as explicit pins. Note
`test_response_validation.py` already pins ragged→`None` — that existing test **is** the control
that catches the crash, and it must be run against the swap.

---

## 4. `batching.run_in_windows` — a window barrier, not a bounded pool

**What it does** [source-verified]: `for window in chunks(items, N): await asyncio.gather(*window)`.
Its docstring justifies the shape against *unbounded* gather ("a plain gather over all items would
peak at len(items)") — a true statement that compares to the wrong alternative. It never considers a
semaphore, so a **slow item stalls its entire window** while the pool sits idle.

**Measured** [library-verified: aiometer 1.0.0; 8 items, one slow (0.4 s) + seven fast (0.05 s),
concurrency 2]:

```
run_in_windows (fixed-window barrier): 0.552s  results=[0,10,20,30,40,50,60,70]
aiometer.run_all(max_at_once=2)      : 0.426s  results=[0,10,20,30,40,50,60,70]
ORDER PRESERVED by aiometer: True    speedup=1.30x
theoretical optimum with 2 in flight : 0.400s
```

Order is preserved — the non-negotiable requirement, since every caller stitches results back by
position. aiometer lands within 6% of optimum; the barrier loses 38%. This is a mild skew; real
embedding batches skew far harder (the TEI docstring records ~14 s for a near-cap 8k-token input
against sub-second small batches), so the real-world gap is larger than 1.30× [my judgement — I did
not measure against the live TEI box].

**The larger point: loresigil has NO rate limiting.** It is purely reactive — send until the server
says 429, then back off (without jitter, §1). `aiometer.run_all(async_fns, *, max_at_once,
max_per_second)` [library-verified signature] provides proactive limiting in the same call that
replaces the pool. That directly addresses the cause of §1's herd rather than only its symptom.

**Verdict: REPLACE-WITH-ADAPTER.** aiometer does the pool + the rate limit; the gap is a thin
`functools.partial` wrapper to adapt `worker(item)` to aiometer's zero-arg thunks (~4 lines). A
stdlib `asyncio.Semaphore` also fixes the stall in ~6 lines but gives **no** rate limiting — that is
the operator's trade.

**Proving control — it already exists**: `test_batching.py::TestRunInWindowsBoundsConcurrency::
test_never_exceeds_concurrency_bound` asserts `peak == concurrency` exactly, by instrumenting live
in-flight count. That is a genuine discriminating pin and `max_at_once=2` satisfies it. Add an
ordering pin over a deliberately skewed delay profile (the current alignment test uses a uniform
`square` worker, so it cannot distinguish ordered from unordered completion).

> ⚠ **Operator decision #3**: adopt `aiometer` (new dependency, gains rate limiting) or hand-roll a
> semaphore (no new dependency, no rate limiting).

---

## 5. `batching.build_batches` → `more_itertools.constrained_batches` — byte-identical

**What it does** [source-verified]: order-preserving greedy pack of indices under a dual cap (token
budget **and** text count), emitting a lone over-budget input as its own batch rather than dropping
it.

**`more_itertools.constrained_batches(iterable, max_size, max_count=None, get_len=len,
strict=True)`** is the same function. Differential-tested [library-verified: more_itertools 11.1.0]:

```
trials=3000  mismatches=0  trials_with_over_budget_item=2109
```

3,000 randomised trials over `n ∈ [0,40]`, token counts drawn from `{1,5,50,500,5000,9000}`,
`max_tokens ∈ {100,1000,8192,262144}`, `max_texts ∈ {1,3,32,128}`. **Zero mismatches**, and 2,109 of
those trials contained an over-budget item — the exact edge case `build_batches`' docstring calls out.

The `strict` flag is the one thing to get right [library-verified]:

```
strict=True  on a lone over-budget item -> raises ValueError("item size exceeds maximum size")
strict=False on a lone over-budget item -> [[0]]        # == build_batches' documented behaviour
```

The default is `strict=True`. **`strict=False` is required** — it is the parameter that preserves
"never dropped and never merged". A swap that takes the default would convert a documented,
tested, load-bearing degradation path into a crash.

**Verdict: REPLACE** (low risk, low reward — honest framing: this is a ~15-line function that
already works; the gain is deleting it and inheriting upstream's tests). `more_itertools` would be a
new direct dependency.

**Proving control**: keep all six existing `test_batching.py` `build_batches` pins pointed at the
new call, and add an explicit `strict=False` over-budget pin so a future "clean up the odd kwarg"
edit goes RED.

---

## 6. `orjson` for response decode — 5.4×, and it is already in the lock

**What it does** [source-verified]: `response.json()` (httpx → stdlib `json`) in
`TEIEmbedder._make_request_fn`, `VoyageCloudEmbedder._make_request_fn`, and
`VoyageContextEmbedder._post`. Every embedding response is a large float-dense JSON array.

**Measured on the real payload shape** — 32 texts × 2,048 float components, 1.35 MB
[library-verified: orjson 3.11.9]:

```
DECODE x20: stdlib=0.419s  orjson=0.077s  speedup=5.4x   (per response 20.9ms -> 3.8ms)
```

**17 ms per response**, on every response, on the hottest path in the package. `orjson` is
**already resolved in `uv.lock`** (`name = "orjson"` at line 959, pulled transitively) — this costs
no new dependency, only `orjson.loads(response.content)` in place of `response.json()`.

Also measured, the JSONL encode side of `voyage_batch.encode_batch_jsonl` (20k lines):
`stdlib=0.044s orjson=0.011s` = **3.9×**, but **`identical_bytes=False`** — orjson emits compact
separators (`{"custom_id":"id-0"`) where stdlib emits spaced (`{"custom_id": "id-0"`). Semantically
identical JSON, different bytes. Since a batch input file is uploaded and never byte-compared, this
is safe [my judgement] — but it is **not** a byte-exact swap and must not be sold as one. At the
documented 100K-line cap the saving is ~0.16 s: real but minor.

**Verdict: REPLACE** for the decode path (clear win, zero dependency cost). Encode path: optional.

**Proving control**: a parity pin asserting `orjson.loads(raw) == json.loads(raw)` on a fixture
containing floats, `null`s, and nested envelopes for **all three** wire shapes (bare TEI list,
cloud `data[].embedding`, contextualized `data[i].data[j].embedding`).

⚠ **The exception hierarchy is load-bearing and I verified it rather than assuming it**
[library-verified, orjson 3.11.9]: `orjson.JSONDecodeError.__mro__` is
`[JSONDecodeError, JSONDecodeError, ValueError, Exception, BaseException, object]` and
`issubclass(orjson.JSONDecodeError, ValueError) is True` — confirmed live by catching
`orjson.loads(b'{bad')` as a `ValueError`. This matters because **both** retry loops degrade a
malformed 2xx body to `None` via `except (ValueError, KeyError, TypeError)`. Had orjson raised
outside that hierarchy, the swap would have converted a documented degrade-never-crash path into an
uncaught exception on the corpus-poisoning branch. **Pin this subclass relationship explicitly** —
otherwise a future orjson major could silently re-open it.

---

## 7. Two L2 normalisations of one policy — a ONE IMPLEMENTATION violation

`loresigil` normalises vectors to unit length in **two** places, **two different ways**, with **two
different degenerate-case answers** [source-verified]:

| site | norm | zero-norm behaviour |
|---|---|---|
| `resilient.mean_pool` | `math.sqrt(sum(c*c for c in mean))` | returns `None` |
| `testing.FakeEmbedder._vector_for` | `math.hypot(*components)` | emits canonical unit axis `[1,0,…]` |

They are not equivalent [library-verified]:

```
voyage-scale unit (dim2048)        sqrt=0.9999999999999999   hypot=0.9999999999999999   AGREE=True
FakeEmbedder-scale (~9.2e18,dim8)  sqrt=2.602152954766495e19 hypot=2.602152954766495e19 AGREE=True
overflow probe 1e200 x8            sqrt=inf                  hypot=2.82842712474619e+200 AGREE=False
underflow probe 1e-200 x8          sqrt=0.0                  hypot=2.82842712474619e-200 AGREE=False
```

`math.hypot` is overflow/underflow-safe; `sqrt(sum(c*c))` is not. **At voyage vector scales they
agree, so this is latent, not live** — and `mean_pool`'s underflow would produce `norm == 0.0`,
hitting its own zero-norm guard and returning `None` (fail-safe, not corrupting). I am not claiming
a live bug.

I am claiming this is exactly the shape `CLAUDE.md` §"ONE IMPLEMENTATION" legislates against: **two
call sites needing the same policy (L2-normalise + handle degeneracy), cloned rather than shared,
and already divergent in both the algorithm and the degenerate-case contract.** The divergence
arrived before anyone noticed there was a policy.

**Verdict: FIX** — one `l2_normalise(components) -> list[float] | None` helper using `math.hypot`
(stdlib does the job; no package needed). The two sites differ on the degenerate case, so that
difference must be made an explicit parameter or an explicit adjudication, not left implicit.

**Proving control**: mutation proof — change the shared helper's degenerate return and assert
**both** call sites' pins move. Per `CLAUDE.md`, a caller that stays green is a private copy wearing
the shared name.

---

## 8–11. KEEP verdicts, with triggers

**8. `quarantine_vector` → numpy — KEEP + RE-OPEN TRIGGER.**
Measured [library-verified]: **1.4×** only (0.178 s → 0.127 s over 3,000 × 2,048-dim). The
`np.asarray` conversion consumes most of the gain, because the input is a Python list from the JSON
decoder. All parities hold (`nan`/`inf`/`allzero`/`shortdim`). **Not worth the churn on its own.**
*Trigger*: if §6 (orjson) or a future change ever delivers vectors as a numpy array or buffer, the
conversion disappears and this becomes free — revisit **together with** §3, never alone.

**9. `voyage_context._split_usage_by_doc` → `apportionment` — KEEP + RE-OPEN TRIGGER.**
The hand-rolled largest-remainder (Hamilton) apportionment is **correct** — I verified the algorithm
and that shares sum to exactly `total_tokens`. A package exists and **reproduces loresigil's output
exactly** on the tie cases [library-verified: apportionment 1.0]:

```
weights=[1,1,1]   total=10 -> apportionment: [4,3,3]      loresigil: [4,3,3]  (sum=10)
weights=[1,1]     total=3  -> apportionment: [2,1]        loresigil: [2,1]    (sum=3)
weights=[5,5,5,5] total=6  -> apportionment: [2,2,1,1]    loresigil: [2,2,1,1](sum=6)
```

But: `apportionment` 1.0 is a **voting-theory research toolkit** (martinlackner), it pulls in numpy,
and it exposes a `TiesException` path where loresigil's index-order tie-break is silent and total.
Taking a research dependency to replace 12 correct, pinned lines is the worse trade [my judgement].
*Trigger*: if a second apportionment site ever appears in the codebase, extract a shared helper —
and reconsider the package then.

**10. `encode_batch_jsonl` / `_iter_jsonl` → `jsonlines` — GENUINELY BESPOKE.**
I read what the code actually does: it is not generic JSONL handling. `encode_batch_jsonl` enforces
loresigil's *domain* rules — id/body length agreement, duplicate-`custom_id` detection, the 100K
line cap, the 1 GiB byte cap — and only incidentally emits JSONL. `jsonlines` is file-object-oriented
and would need `io.BytesIO` wrapping to touch bytes, replacing 5 lines of stdlib with an import and
an adapter while covering none of the validation that is the function's actual purpose. Nothing to
gain. (The `orjson` encode note in §6 applies to the one `json.dumps` line inside it.)

**11. `VoyageTokenCounter` double-checked locking → `functools.cache` — KEEP + trigger.**
The class-level `_tokenizer` + `_lock` + re-check-inside-lock is a hand-rolled thread-safe singleton.
A module-level `@functools.cache def _load_tokenizer()` is simpler and thread-safe. Purely cosmetic,
correct as written, and touching it risks a load-order regression for no measurable gain.
*Trigger*: if a second pinned artifact ever needs the same load-once treatment, extract then.

---

## 12. Retry orchestration → `tenacity` / `stamina` — **KEEP + RE-OPEN TRIGGER** (the #202 model)

There are two hand-rolled retry loops: `ResilientEmbedder._request_with_retry` and
`VoyageContextEmbedder._request_with_retry` [source-verified]. The brief names #202 as the model for
dispositions, and this is the item it fits.

**Why keeping is right:**
- They **already share** the policy that must agree — `is_retryable_status`, `compute_backoff_delay`,
  `quarantine_vector` are imported, not cloned. `voyage_context.py`'s module docstring explicitly
  records *why* it cannot reuse `ResilientEmbedder` wholesale (per-**document** atomicity vs
  per-**text** salvage: splitting a doc's chunks into per-chunk requests would silently change what
  context each chunk was embedded with). That is a real, documented domain constraint.
- The classification is **three-way** — retryable / permanent / 422-needs-sub-split — plus a fourth
  malformed-2xx path. `tenacity` and `stamina` model a **two-way** exception-based retry predicate.
  The three-way shape can be forced into it, but that is a rewrite of proven, tested code to fit a
  library's frame [my judgement].
- Both loops return `None` on permanent failure rather than raising — the degrade-never-crash
  contract the whole package is built on. Exception-driven libraries invert that.

**Verified in favour of a future swap** [library-verified]: `tenacity` 9.1.4 accepts an injectable
`sleep` on both `BaseRetrying` and `AsyncRetrying` — so loresigil's `sleep_fn` determinism seam
**would** survive adoption. `stamina` 26.1.0 has `set_testing()` for the same purpose. The blocker is
the classification shape, not the test seam.

***Re-open trigger***: a **third** retry loop appearing in `loresigil` — at that point the shared-
helper approach is being outgrown and a library's frame is worth the rewrite. Until then, three
imported helpers across two documented-different loops is the better trade.

**Note the split from §1**: keeping the *orchestration* does **not** justify keeping the *missing
jitter*. §1 is a defect in the shared helper; §12 is a judgement about the loops around it. They are
independent decisions and I have kept them so deliberately.

---

## 13. Raised under scope law — found in scope, not this mission's

Per `CLAUDE.md` (scope belongs to the operator) — surfaced, not actioned, not buried:

1. **`TEIEmbedder.probe` mutates another object's private attribute.** It assigns
   `self._document_resilient._max_input_tokens = effective_cap` and the same for
   `_query_resilient` [source-verified]. This reaches through `ResilientEmbedder`'s encapsulation
   from outside. If `ResilientEmbedder` ever caches or derives anything from that value at
   construction, the mutation silently desynchronises. Suggested fix: a
   `ResilientEmbedder.set_max_input_tokens()` method, or make the cap a callable the wrapper reads
   per call.
2. **`mean_pool` is called on single-element groups on the TEI common path.**
   `TEIEmbedder._embed_with` pools even when `grouped[i]` has exactly one vector — re-normalising an
   already-L2-normalised vector, ~8,000 interpreted float ops per document for a mathematical no-op
   (modulo float error). A `if len(g) == 1: return g[0]` short-circuit is a bigger win than §3's
   2.8× on the dominant case, and is independent of any library choice.
3. **No proactive rate limiting anywhere** — see §4. Reactive-only 429 handling, which combined
   with §1's zero jitter is the full herd shape.
4. **`EmbedResult.vectors: list[list[float] | None]`** carries embeddings as Python float lists
   end-to-end. At 2,048 dims a `list[float]` costs roughly 8× a `float32` numpy array in memory and
   is slow to move across seams. This is a **design** question about the package's public contract,
   not a package swap, so I am flagging rather than recommending [my judgement].
5. **~~`test_resilient.py` appears to have 0 tests~~ — WITHDRAWN, this was my own bad grep.**
   Re-checked with a corrected pattern: `test_resilient.py` contains **16 tests** across 6 test
   classes [source-verified]. My first `grep -c` anchored on `^def test` and missed indented class
   methods. Recorded rather than deleted because it is a receipt for the brief's own warning:
   an anchored grep systematically misses exactly what it is aimed at, and I nearly shipped a
   non-finding as a finding. No coverage gap exists here.

---

## Appendix — reproduction

All probes were run as heredocs against the worktree venv, in the form:

```bash
cd /home/ejprice/PycharmProjects/lore-pkt11i
uv run --no-sync --with <pkg> python - <<'PY'   # numpy | more-itertools | tenacity | stamina | aiometer | apportionment
...
PY
```

`--no-sync --with` leaves `pyproject.toml` and `uv.lock` untouched, per the brief. `orjson`,
`tenacity`, `tokenizers`, `httpx` and `pydantic` were already resolved in the environment and
needed no `--with`. Package versions as executed **2026-07-25 at `6654be0`**: numpy 2.5.1 ·
more_itertools 11.1.0 · tenacity 9.1.4 · stamina 26.1.0 · aiometer 1.0.0 · apportionment 1.0 ·
orjson 3.11.9 · tokenizers 0.23.1 · httpx 0.28.1 · pydantic 2.13.4.

Timings are single-run wall clock on this box and are indicative, not benchmark-grade; the
equivalence and parity results are exact and reproducible.
