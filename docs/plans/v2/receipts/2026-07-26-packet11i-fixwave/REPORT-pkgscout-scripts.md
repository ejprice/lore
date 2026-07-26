# REPORT-pkgscout-scripts — package-vs-hand-roll sweep of `scripts/`

## SUMMARY BLOCK

`brief-base v6 read`

**State:** done.

**Deviations:**
- None to the writable set (this report only; no code/test/config/lockfile touched).
- Package probes ran in **ephemeral `uv run --no-sync --with …` overlays** on this worktree; `uv.lock` untouched. Verified via `git status` clean at start.

**Coverage statement (measured 2026-07-25 at `b4eb32a`, worktree `lore-pkt11i`):** all **6 production files / 3,590 LOC** under `scripts/` read IN FULL (`token_survey.py` 1591 · `search_score_survey.py` 988 · `snapshot_gc.py` 437 · `survey_txn_contention_102.py` 223 · `calibration_baseline.py` 193 · `scratch_provenance.py` 158). **NOT read:** the 5 co-located `scripts/test_*.py` files (~1,787 LOC) except by grep; `scratch_copy.sh` / `typecheck.sh` (shell, outside the 6-file count) skimmed only. I read `loremaster/loremaster/calibration/counting.py` and `loremaster/tests/test_calibration_counting.py` because a scripts/ finding pointed there.

**Ranked verdicts** (rank = cost of a wrong call, highest first):

| # | Candidate (symbol) | Verdict | Package |
|---|---|---|---|
| 1 | `token_survey.ClaudeTokenCounter` + `MultiModelClaudeCounter` — **and its committed twin** `calibration.counting.AsyncClaudeTokenCounter` | **REPLACE** | `anthropic` (official SDK) |
| 2 | `token_survey.load_api_key` **×2** (twin in `calibration.counting`) | **REPLACE** | `python-dotenv` |
| 3 | `survey_txn_contention_102._connect` (11th/12th hand-rolled session bootstrap) + `._unique_database` | **REPLACE-WITH-ADAPTER** | in-repo seam, not a package |
| 4 | Survey statistical core (`choose_cosine_floor`, `weighted_percentile`×2, `percentile`, `summarize*`) | **REPLACE** (known #201/#198 — not re-derived) | `scikit-learn`/`scipy`/`numpy` |
| 5 | Markdown table emitters ×3 (`build_markdown_summary`, `build_yardstick_markdown`, `build_markdown_report`) | **REPLACE-WITH-ADAPTER** | `tabulate` |
| 6 | `snapshot_gc._parse_iso8601` (Z→+00:00 rewrite) | **DELETE — stdlib already does it** | stdlib (3.11+) |
| 7 | `token_survey.FileDiscovery._dir_excluded` | **REPLACE-WITH-ADAPTER** (low payoff — say so) | `pathspec` |
| 8 | `search_score_survey.parse_eval_questions` — bare `ElementTree` vs the repo's own `defusedxml` policy | **REPLACE-WITH-ADAPTER** | `defusedxml` (already a dev dep) |
| 9 | `token_survey.recommended_ceiling` float-drift dance | **REPLACE** | stdlib `decimal` |
| 10 | `SurveyRunner` progress plumbing / `_write_row` / `_write_jsonl` | **KEEP + RE-OPEN TRIGGER** | `tqdm`/`rich` available, not worth it |
| 11 | `scratch_provenance.py` (whole file), identity-pinned predicate imports, the D1/D2 bars, `stratum_sample_size`, `every_nth`, `partition_snapshots`/`is_total_wipe`, `_CountingConnection`, `compute_agreement`, `compare_to_baseline` | **GENUINELY BESPOKE** | — |
| 12 | `argparse`, `random.Random(seed).sample`, `concurrent.futures`, `time.monotonic` | **KEEP** (stdlib IS the library) | — |

**PORT-vs-RE-DERIVE split for the survey core:** see §PORT-VS-RE-DERIVE. Short form — **RE-DERIVE the arithmetic third** (floor sweep, percentiles, group summaries); **PORT VERBATIM the domain two-thirds** (the three `is`-identity production imports, the pre-registered bars, anchor masking, the capture pipeline, the sampler, the eval-XML miner, the report/JSONL writers, the `VerdictSample`/`HitCapture`/`GroupCosineSummary` shapes). **Two convention seams must be settled BEFORE any np one-liner lands** (§C1, §C2) — a naive dissolve silently picks one side.

**Decisions needed (operator):**
1. **D-A** — Adopt `anthropic` SDK for BOTH token counters (deletes the documented clone + its parity test's reason to exist)? Recommend YES; proving control named in §1.
2. **D-B** — `scripts/search_score_survey.py` hardcodes **`ws://127.0.0.1:18500` = PRODUCTION** with **no `--url` override**. Add one? (out-of-mission finding, §F1)
3. **D-C** — `summarize()` mixes TWO median conventions inside ONE object (§C1). Which survives the port?
4. **D-D** — Do the ~50 never-gated `scripts/` tests (#199) get added to `testpaths` as part of 11-i? Nothing here is gate-verified, including the `is`-identity pins.

**Tool honesty:** lore's index watches the MAIN checkout, not this worktree (#125), so **every structural answer here came from `Read` + `grep` in the worktree, not from `lore_search`/`lore_impact`** — said out loud per §4. I did not file a friction row: this is #125's known bound, already ledgered, not a new gap. All citations are **symbols, never line numbers**.

**Claim labels used throughout:** **[source-verified]** = read in this worktree at `b4eb32a` · **[library-verified: <pkg> <version>]** = probed against the installed package this sitting · **[my judgement]**.

---

## 1. The Claude token counter — ONE IMPLEMENTATION violated, and the copies have ALREADY diverged

**Verdict: REPLACE** (both copies) with the official `anthropic` SDK.

### 1.1 The duplication is documented, deliberate, and load-bearing

`loremaster/loremaster/calibration/counting.py`'s own module docstring **[source-verified]**:

> "The `count_tokens` REQUEST SHAPE … is IDENTICAL to `token_survey.ClaudeTokenCounter` … This module does **NOT** import from `scripts/` (not a package); **it replicates the shape and the constants**, and the parity test is what guarantees they stay in lock-step."

That is the `#102` shape stated in prose: a *pattern cloned* rather than a *function called*, with a test as the mitigation. Duplicated across the two files **[source-verified]**: `ANTHROPIC_COUNT_TOKENS_URL`, `ANTHROPIC_VERSION`, `ANTHROPIC_API_KEY_ENV`, `DEFAULT_ENV_FILE`, `MAX_RETRIES`, `RETRY_BASE_DELAY_S`, `RETRY_MAX_DELAY_S`, the `_payload` wrapping, the whole retry loop, the `_sleep_backoff` method, and `load_api_key` **verbatim**.

### 1.2 The mitigation does not cover the thing that drifted — and it HAS drifted

`loremaster/tests/test_calibration_counting.py::TestRequestShapeParity::test_wire_shape_is_byte_identical_to_survey_counter` asserts **[source-verified]**: same method, same URL, byte-identical body, and full application-level header-key-set parity.

It asserts **nothing** about the retry budget, the backoff curve, or **error classification**. And error classification is exactly where the two copies have already separated **[source-verified]**:

| behaviour | `scripts/token_survey.ClaudeTokenCounter` | `calibration.counting.AsyncClaudeTokenCounter` |
|---|---|---|
| non-retryable 4xx | raises bare `RuntimeError` | raises **`TerminalCountError`** (typed subclass, added so a caller can STOP) |
| retry exhaustion | `RuntimeError` | `RuntimeError` (deliberately kept plain to preserve the distinction) |

A caller of the calibration counter can distinguish "bad key, stop" from "transient outage, retry". A caller of the survey counter **cannot** — the fix reached one copy and not the other, and **the green parity test cannot see it**. This is `#102` reproduced inside the code that documents itself as guarded against `#102`. **[source-verified]**

### 1.3 The package does the job — verified by reading the installed API, not assumed

**[library-verified: `anthropic` 0.120.0]**, probed this sitting in an ephemeral overlay:

- `client.messages.count_tokens(...)` exists; parameters include `messages`, `model`, `system`, `tools`, `thinking`, `tool_choice`, `extra_headers`, `timeout`. Result type `MessageTokensCount` has exactly one field: **`input_tokens`** — the identical value both hand-rolls parse out of the JSON body.
- **Retries are built in and configurable**: `DEFAULT_MAX_RETRIES = 2`; `Anthropic(max_retries=6)` is honoured (probed — `c.max_retries == 6`). Retryable set: connection errors, 408, 409, 429, ≥500.
- **Backoff honours `Retry-After`**: read from `anthropic._base_client.BaseClient._calculate_retry_timeout` — if the header parses and is `0 < retry_after <= 60`, it sleeps exactly that; otherwise exponential `INITIAL_RETRY_DELAY(0.5) * 2**n` capped at `MAX_RETRY_DELAY(8.0)`, **with jitter** (`1 - 0.25*random()`).
- **Typed exceptions replace the string-matching**: `RateLimitError`, `APIStatusError`, `APIConnectionError`, `AuthenticationError`, `BadRequestError` — the `TerminalCountError` distinction becomes `except anthropic.APIStatusError` vs `except anthropic.APIConnectionError`, off-the-shelf.
- **The threading model is unchanged**: the sync client's transport is `SyncHttpxClientWrapper`, which **is an `httpx.Client`** (probed `isinstance(...) is True`). `MultiModelClaudeCounter` already shares one `httpx.Client` across the `ThreadPoolExecutor` today, so sharing one `Anthropic()` client is the same shape, not a new one. **[my judgement, grounded in both probes]**
- `AsyncAnthropic` exists for the `calibration_baseline.py` async path — no shape change there either.

The `claude-api` skill's own guidance, read this sitting, is unambiguous on both halves: *"use `messages.count_tokens`, never `tiktoken`"*, and *"The Anthropic SDK automatically retries rate limit (429) and server errors (5xx) with exponential backoff… **Only implement custom retry logic if you need behavior beyond what the SDK provides.**"* — with **"Don't reimplement SDK functionality"** listed as a named pitfall.

### 1.4 Backoff-curve deltas the port must decide (not blockers, but name them)

**[library-verified vs source-verified comparison]**

| knob | hand-rolled (both copies) | `anthropic` 0.120.0 |
|---|---|---|
| max retries | 6 | 2 default → pass `max_retries=6` |
| base delay | 1.0 s | 0.5 s |
| max delay | 30.0 s | 8.0 s |
| jitter | **none** (deterministic `1.0 * 2**attempt`) | ±25% |
| `Retry-After` cap | 30 s | 60 s |

The hand-roll has **no jitter** — the exact deterministic-jitter defect class `#102`/DESIGN-LAW calls out, here in a 4-worker pool hitting one endpoint. The SDK's jitter is a strict improvement. The shorter max delay (8 s vs 30 s) is the one knob to think about under sustained 429s; the SDK still obeys a server `Retry-After` up to 60 s, which is the path that actually matters for Anthropic rate limits. **[my judgement]**

### 1.5 Risk, and the proving control

**The risk that matters:** `calibration_baseline.py` generates a **committed, generation-anchored `baseline.json`**. If the SDK's request differs in any way that changes the server-computed count, every downstream calibration number moves silently.

**The control — an oracle already exists in-repo, byte-exact, no new fixture needed.** `loremaster/loremaster/calibration/baseline.json` carries per-file `claude_tokens` **and** `sha256` over a **frozen** corpus (`load_corpus()`). So:

> Re-count the frozen calibration corpus through `anthropic.AsyncAnthropic().messages.count_tokens(...)` and assert **every per-file `input_tokens` equals the committed baseline's `claude_tokens`**, with the `sha256` re-checked to prove the corpus bytes are the ones the baseline was built from. Pin as a test. A single mismatch is a STOP.

This is the same shape as the operator's TimesFM checkpoint-translator precedent: swap the implementation, gate it with a byte-exact equality control against an artifact you already trust. It costs one test function and one API run over a small frozen corpus.

**Consequence to state plainly:** once both counters route through the SDK there is **one implementation**, so `TestRequestShapeParity` has nothing left to compare and should be **deleted, not ported** — replaced by the baseline-equality pin above. A parity test between two copies is a monument to the duplication; removing the duplication is what retires it. **[my judgement]**

### 1.6 What must NOT be swept along

`token_survey`'s **concurrency structure is deliberate and documented** — `_measure_one`'s docstring says the per-file worker holds at most one in-flight request so `max_workers` bounds *total* concurrent Anthropic calls across all models, not per-model **[source-verified]**. Keep the `ThreadPoolExecutor` + sequential per-model loop exactly as is. Swap only the counter class (operator's rule (a): **minimal surface** — a bridge, not a parallel re-implementation). Rewriting this into `AsyncAnthropic` + `gather` would be a *reshape*, not a package adoption, and would dissolve a documented invariant.

---

## 2. `load_api_key` — hand-rolled `.env` parsing, twice

**Verdict: REPLACE** with `python-dotenv` **[library-verified: `python-dotenv` 1.2.2]**.

Present **verbatim in both files** **[source-verified]** — `token_survey.load_api_key` and `calibration.counting.load_api_key` (whose docstring says *"Mirrors `token_survey.load_api_key`"*). The implementation:

```
stripped.startswith(f"{ANTHROPIC_API_KEY_ENV}=") → split("=", 1)[1].strip().strip("'\"")
```

Inputs this mishandles that `dotenv_values()` handles: a leading `export ` (the operator's own documented usage in `snapshot_gc.py`'s docstring is `set -a; . file; set +a` — an `export`-shaped world), inline `#` comments, multi-line/quoted values, escape sequences, and `KEY = value` spacing. The env file is `~/docker/mcp/.env`, authored by hand — every one of those is a live shape. **[my judgement on likelihood; the parsing gaps themselves are source-verified]**

Replacement is `dotenv_values(env_file).get(ANTHROPIC_API_KEY_ENV)`, preserving the "prefer an already-exported var" precedence and the "never log the value" property (both are caller-side, unchanged).

**Note the cluster:** items 1 and 2 are the same cluster and should land in one change — collapsing to the SDK is what makes it natural to collapse the key loading too, since `Anthropic()` resolves `ANTHROPIC_API_KEY` from the environment itself. The minimal shape is: `load_dotenv(env_file, override=False)` once at CLI entry, then a bare `Anthropic()`.

---

## 3. `survey_txn_contention_102` — the session bootstrap, hand-rolled again

**Verdict: REPLACE-WITH-ADAPTER** — the gap is an in-repo seam, not a package.

`scripts/survey_txn_contention_102._connect` **[source-verified]**:

```
connection = AsyncSurreal(URL); await connection.signin({...}); await connection.use(NAMESPACE, database)
```

This repo's `CLAUDE.md` documents that `_query` had **ten** hand-rolled copies and that the **session bootstrap** (`DEFINE NAMESPACE` / `use()` / `DEFINE DATABASE`) carries an **eleventh** in `scout.py` that no `_query`-keyed scan could see. **`scripts/` carries another one.** I am *not* asserting a corrected total — re-deriving that count is precisely the mistake the law warns about; I am reporting **one more instance, at `survey_txn_contention_102._connect`, that a `_query`-keyed enumeration cannot see** because it lives in a directory outside `testpaths` and spells the seam differently. **[source-verified]**

Second, smaller instance in the same file: `_unique_database()` returns `f"survey102_{os.getpid()}_{uuid.uuid4().hex}"` — a clone of `loremaster/tests/_surreal_harness.unique_database()`, which returns `f"test_{os.getpid()}_{uuid.uuid4().hex}"` and whose docstring carries the concurrency-safety rationale the clone drops **[source-verified]**. Same policy, two copies, different prefix.

Because this script *deliberately* drives the real `execute_transaction` seam to measure it, the adapter must be careful: **the probe's value is that it uses production's connection path**. The right fix is to route the bootstrap through whatever shared seam packet 11-i settles on and keep `_CountingConnection` (which is genuinely bespoke — see §5) wrapping it. **Prove the sharing by mutation**: change the shared bootstrap's marker and this script's connect must change with it, or it is a private copy wearing the shared name.

---

## 4. The survey statistical core — NOT re-derived (owning the split instead)

Per the brief I do **not** re-derive #201's five items. Two things I *did* find that sit on top of them, and that a naive "dissolve into np one-liners" would silently resolve:

### C1 — `summarize()` mixes TWO median conventions inside ONE object **(decision D-C)**

`token_survey.summarize` **[source-verified]**:

- `file_median = statistics.median(ratios)` → **interpolating**: for even *n*, the mean of the two middle values, a number that **may not appear in the data**.
- `file_p5 = percentile(ratios, PCT_P5)` and `file_p95 = percentile(ratios, PCT_P95)` → `weighted_percentile` → **nearest-rank**: always an **observed** value.

So a single `RatioSummary` reports its median under one convention and its p5/p95 under another. Meanwhile `search_score_survey.summarize_cosine_group` uses `percentile(scores, 50.0)` — **nearest-rank** — for *its* median **[source-verified]**. The two surveys therefore disagree with each other about what "median" means, and one of them disagrees with itself.

**Why this matters to 11-i:** #201 pins `np.percentile(method="inverted_cdf")` as the nearest-rank equivalent. Dissolving `summarize` to that method **silently changes `file_median`** on every even-*n* project. Dissolving it to `np.median` (the obvious one-liner) silently changes p5/p95. **Either direction moves a served number**, and no gate would catch it — `scripts/` tests never run (#199).

**Recommendation [my judgement]:** unify on **nearest-rank** (`method="inverted_cdf"`) everywhere, because (a) it is what `search_score_survey` already uses, (b) it is what #201 measured, (c) it is what `choose_cosine_floor`'s candidate-set discipline requires (candidates must be *observed* values), and (d) an observed value is defensible in a served report where an interpolated one is a synthetic number. But this **changes `file_median`** — so it needs an explicit operator ruling and a before/after receipt, not a quiet re-derivation.

### C2 — the weighted percentile's accumulator convention

`weighted_percentile` computes `total_weight = math.fsum(...)` (exact) but accumulates `cumulative += weight` (naive) **[source-verified]**. At `pct=100` the two can disagree by float error; the function's trailing `return ordered[-1][0]` absorbs that case, so **this is benign today**. I flag it only because `np.quantile(weights=)` has its own accumulation convention, and "our two copies and numpy all agree" is a claim the port must *prove*, not assume — the randomized-equality control #201 already established is the right instrument, extended to cover `pct ∈ {0, 100}` and duplicated weights.

**Also note:** the two `weighted_percentile` copies are written differently but are semantically identical. `token_survey`'s returns the first value whose cumulative weight reaches `pct/100 * n`; `survey_txn_contention_102`'s picks index `max(1, ceil(pct/100 * n)) - 1`. For uniform weights these are the same function. **[source-verified — traced by hand, both paths]** Confirms #198's "both copies deletable" and adds that they are *behaviourally* one policy, so the deletion is safe rather than merely tidy.

---

## PORT-VS-RE-DERIVE (the explicit split the brief asked for)

Against the six production files, not just the survey. **The load-bearing half is the second column.**

### RE-DERIVE on library primitives (delete the hand-roll)

| Item | Onto |
|---|---|
| `choose_cosine_floor`'s candidate sweep (production role) | `sklearn.metrics.roc_curve` — #201, proven exactly equal 20/20 |
| `weighted_percentile` ×2 · `percentile` | `np.quantile(weights=)` / `np.percentile(method="inverted_cdf")` — #198 |
| `GroupCosineSummary` / `RatioSummary` arithmetic (mean/median/p5/p95) | np one-liners — **but settle C1 first** |
| the bootstrap harness (unwritten) | `scipy.stats.bootstrap` |
| `ClaudeTokenCounter` · `MultiModelClaudeCounter` · `_sleep_backoff` · the retry loop | `anthropic` SDK (§1) |
| `load_api_key` ×2 | `python-dotenv` (§2) |
| `_parse_iso8601`'s `Z` rewrite | stdlib `datetime.fromisoformat` (§6) |
| `recommended_ceiling`'s `ceil(round(x*100,6))/100` | `decimal.Decimal.quantize(ROUND_CEILING)` (§9) |
| the three markdown table emitters | `tabulate` (§5) |
| `_dir_excluded`'s two-flavour matcher | `pathspec` (§7) |

### PORT VERBATIM — genuinely domain, and expensive to "modernise"

**This is the half where a wrong call is silent and expensive. Naming it is half the mission.**

1. **The three `is`-identity production imports** — `_cosine_absence_predicate`, `_has_verbatim_identifier_anchor`, `_query_tokens`, re-exported at module scope in `search_score_survey` **specifically so the survey runs the SAME function object production runs**, pinned by `TestPredicateParityWithProduction` **[source-verified, incl. the comment block explaining that a paraphrase is how the ≤5%/≥60% bars silently drifted]**. **Any "cleanup" that inlines, wraps, re-implements, or even *re-imports differently* decouples the survey from production and the drift is invisible.** ⚠ And per #199 **these pins have never executed in any gate** — the one instrument guarding this is currently unarmed.
2. **The pre-registered bars** — `D2_MAX_FALSE_FIRE_RATE`, `D2_MIN_NONSENSE_CATCH_RATE`, `D1_MIN_MEDIAN_SPREAD`. Deliberately named constants, *not* CLI defaults, so a run cannot quietly override them; amending them post-hoc un-pre-registers the rule **[source-verified — the module docstrings say exactly this]**. Port the values AND the not-a-CLI-flag property.
3. **Anchor masking as an INPUT to the sweep** — `choose_cosine_floor` scores false-fire and catch through the production *predicate*, never a bare `cosine < floor`. An anchored sample contributes zero regardless of floor. The roc_curve port must feed **negated cosines of the non-anchored samples only**, then rescale to full-set denominators (#201 §R9.1 item 2). Losing the mask turns the sweep into a different statistic that still looks fine.
4. **`VerdictSample` / `HitCapture` / `QueryCapture` / `GroupCosineSummary` shapes** — the dataclass *shapes* carry the report contract even where their arithmetic dissolves.
5. **The capture pipeline** — `capture_query`, `survey`, `_make_store`, `_make_embedder`, and specifically the documented **READ-ONLY** property (never calls `ensure_ready()`, which is a DDL write transaction) **[source-verified]**. Preserve that; it is an audit finding, not an accident.
6. **`sample_identifier_queries` + `every_nth`** — "sorted qualified names, every Nth", `int(i*len/count)` floor. Deterministic by design; `np.linspace` is *not* the same index set. #201 notes `every_nth` is D2-retired — if it is retired, delete it; if it survives, port it verbatim. Do **not** "modernise" it into linspace.
7. **`parse_eval_questions`** — but see §8, it should route through `defusedxml`.
8. **`stratum_sample_size`** — `min(size, max(ceil(f*size), min(min_sample, size)))`. Bespoke sampling policy; `sklearn.model_selection` has nothing with this floor-and-cap rule.
9. **`sample_stratified`'s seeded determinism** — one `random.Random(seed)`, strata visited in sorted key order, path-sorted within. The reproducibility contract lives in the *ordering*, not the RNG. If the port moves to `numpy.random.Generator` (#201 §R9.2), the **replay control must prove the same seed still yields the same file set**, or the "same seed reproduces the same sample" docstring becomes false.
10. **`snapshot_gc`'s safety semantics** — `partition_snapshots` (inclusive-on-keep boundary), `is_total_wipe`, `SnapshotClassificationError` (refuse the WHOLE partition on one unparseable timestamp, never partial), the dry-run default. Pure domain safety logic; nothing to install.
11. **`scratch_provenance.py` — the entire file.** `ProvenanceGuard.verdict`, `MemberProvenance`, `import_member`, the `POISON_HEADLINE`, the `sys.path.insert` that makes the guard resolve imports the same way the agent's own run will. This is finding #140 encoded; it is pure stdlib (`importlib`, `pathlib`) and there is no package that answers "is this scratch copy grading the original tree". **GENUINELY BESPOKE — leave it completely alone.**
12. **`_CountingConnection`** in the contention probe — could nominally be `unittest.mock.MagicMock(wraps=)`, but the explicit wrapper is honest about counting exactly `query_raw` and passing `check_response_for_error` straight through. A mock would be *less* verifiable in a measurement instrument. **GENUINELY BESPOKE.**
13. **`compute_agreement` / `compare_to_baseline` / `max_pairwise_relative_delta` / `resolve_available_models` / `filter_by_model`** — dict/set glue over domain questions ("did every model count this file", "did the endpoint drift since last week"). pandas would be a heavier dependency doing the same thing less legibly. **GENUINELY BESPOKE.**

**Coarse quantum [my judgement]:** I agree with #201 §R9.4's "roughly the arithmetic third dissolves, the domain two-thirds carries" **for `search_score_survey.py`**. Extended across all six files the dissolving fraction is **smaller**, not larger — because `snapshot_gc.py` and `scratch_provenance.py` (595 LOC combined) are ~95% domain, and `token_survey.py`'s dissolving part is dominated by the *counter* (§1), not the statistics.

---

## 5. Markdown table emitters ×3 — `tabulate`

**Verdict: REPLACE-WITH-ADAPTER** **[library-verified: `tabulate` 0.10.0]** — `tabulate(rows, headers=..., tablefmt="github")` emits exactly the `| a | b |` + `|---|---|` shape all three emitters hand-build.

Three separate hand-rolled emitters **[source-verified]**: `token_survey.build_markdown_summary`, `token_survey.build_yardstick_markdown`, `search_score_survey.build_markdown_report`. Between them ~150 LOC of f-string column arithmetic.

**The concrete hazard, not just tidiness:** in `build_markdown_summary`, the divider is

```
divider = "|" + "|".join(["---"] * 11) + "|"
```

— an **11 hardcoded against a header string listing 11 columns by hand**. Add a column to `header` and the divider silently mismatches; nothing checks it, and per #199 no test runs. That is a served-surface defect generator of exactly the class this repo's CLAUDE.md says clusters in "natural-language surfaces whose consistency with code no gate checks". `tabulate` derives the divider from the data, making the class unreachable rather than merely unlikely.

**Second hazard in the same function family:** `build_yardstick_markdown` demotes the nested report's H1 by **string surgery** — `if model_lines[0].startswith("# "): model_lines = model_lines[1:]` **[source-verified]**. It works only because `build_markdown_summary` happens to start with `# `. Composing rendered markdown by slicing its first line is fragile; the adapter should have `build_markdown_summary` take a heading level (or return sections) rather than have the caller amputate its output.

**Adapter size:** small — the `_fmt`/`f"{x:.4f}"` formatting stays (tabulate's `floatfmt` would also do it, but keeping our formatter preserves exact byte output, which is the cheaper migration). Ranked 5th because the reports are consumed by agents and a malformed table degrades a **served surface**, but nothing currently miscomputes.

---

## 6. `snapshot_gc._parse_iso8601` — the workaround is dead weight

**Verdict: DELETE. The stdlib already does it.**

```
if normalised.endswith("Z"): normalised = f"{normalised[:-1]}+00:00"
return datetime.fromisoformat(normalised)
```

**[library-verified: CPython 3.14.6, probed this sitting]** — on this interpreter:

```
datetime.fromisoformat('2026-07-04T22:42:00Z')      → datetime(2026,7,4,22,42, tzinfo=timezone.utc)
datetime.fromisoformat('2026-07-04T22:42:00+00:00') → same
datetime.fromisoformat('2026-07-04T22:42:00')       → naive (as _to_aware_utc expects)
```

`fromisoformat` gained full ISO-8601 parsing including a trailing `Z` in **Python 3.11**; the repo pins `requires-python = ">=3.14"` **[source-verified]**. The rewrite is therefore unreachable-as-necessary code. Delete the `Z` branch and call `fromisoformat` directly; `_to_aware_utc` still handles the naive case, and `parse_epoch`'s error wrapping is unchanged.

**Do NOT reach for `dateutil`/`pendulum` here** — that is the wrong side of the rule. The stdlib does the job; adding a dependency to replace a workaround for something the stdlib already handles would be churn.

**Control:** the existing round-trip cases (`Z`, `+00:00`, naive, and a malformed string that must still raise `ValueError` → `SnapshotClassificationError`) pinned as a test. Cheap, and it would go RED today if someone ran it on <3.11.

---

## 7. `FileDiscovery._dir_excluded` — `pathspec`, with an honest low-payoff note

**Verdict: REPLACE-WITH-ADAPTER — but this is the weakest item on the list and I am saying so.**

`_dir_excluded` implements two pattern flavours **[source-verified]**: a pattern containing `/` is matched against the path relative to the project root; a bare-name pattern is matched against the basename at any depth. **That is gitignore semantics, exactly.**

**[library-verified: `pathspec` 1.1.1]** — I ran the repo's real pattern set through `PathSpec.from_lines('gitwildmatch', ...)` this sitting. All 11 cases agree with the hand-roll, including the load-bearing DI case:

| path | pathspec | hand-roll (traced) |
|---|---|---|
| `.git`, `a/b/.git` | True | True (basename at any depth) |
| `__pycache__`, `x/__pycache__` | True | True |
| `odoo-custom-wt-1`, `a/odoo-custom-wt-1` | True | True (glob on basename) |
| **`demand/data/models`** | **True** | **True** (anchored) |
| **`demand/src/demand/models`** | **False** | **False** ← the case the DI manifest depends on |
| `other/demand/data/models` | False | False (anchored ≠ suffix match) |
| `validation/artifacts` | True | True |
| `src/normal` | False | False |

**Adapter:** keep `os.walk` + in-place `dirnames[:]` pruning (pathspec does not prune); swap only the predicate — ~3 lines. One caveat to carry: gitwildmatch distinguishes directory patterns via a trailing `/`, and `match_file` on a slash-less path is treated as a file. No current pattern uses a trailing slash, so this is a latent difference, not a live one — the adapter should either normalise dir paths with a trailing `/` or pin the current behaviour.

**Honest assessment [my judgement]:** the hand-roll is ~12 lines and, as measured, **correct**. The payoff is (a) shedding maintenance of a matcher whose semantics people get wrong, and (b) removing a platform-dependence: `fnmatch.fnmatch` normalises via `os.path.normcase`, which is identity on Linux/macOS but case-folds and converts separators on Windows — so the predicate's behaviour is OS-dependent where `pathspec`'s is not. The repo is Linux/macOS, so **this is a portability note, not a live bug**. Rank it accordingly; if 11-i is short on budget, this is the first item to drop.

---

## 8. `parse_eval_questions` — bare `ElementTree` against the repo's own `defusedxml` policy

**Verdict: REPLACE-WITH-ADAPTER** — the package is **already a dev dependency**; the policy is already this repo's.

`scripts/search_score_survey.py` does `import xml.etree.ElementTree as ET` and `ET.parse(xml_path)` **[source-verified]**.

The repo has an explicit, documented XML policy **[source-verified]**: `lorescribe/lorescribe/xml_generic.py` imports `from defusedxml.ElementTree import fromstring as safe_fromstring, iterparse as safe_iterparse`, and its docstring names the threat — *"defusedxml raises (e.g. EntitiesForbidden)… refuses to expand internal entities"* — with entity-bomb/XXE called out as "Defense 2". `pyproject.toml` carries `types-defusedxml` in the dev group.

So this is not "add a package" — it is **one module routing around a policy the rest of the tree follows**. The input today is a committed repo file (`loremaster/evaluation.xml`), so exposure is low; but the fix is a one-line import swap, and the *reason* to make it is ONE IMPLEMENTATION (one XML-parsing policy, applied everywhere) rather than the threat model.

⚠ **Out of my mission but found by the same grep, raised per scope law:** `docs/eval/evaluation_harness_p8a.py` also uses bare `import xml.etree.ElementTree as ET` **[source-verified]**. Not my scope to fix or judge — surfacing it.

---

## 9. `recommended_ceiling` — the float-drift dance is what `decimal` is for

**Verdict: REPLACE** with stdlib `decimal`.

```
# Round before ceil so float drift (1.70 -> 169.9999) does not bump the value.
return math.ceil(round(max_p95 * 100.0, 6)) / 100.0
```

**[source-verified]** — the comment *admits* it is fighting binary float representation, and the `round(..., 6)` is a magic-tolerance guess. `decimal.Decimal(str(max_p95)).quantize(Decimal("0.01"), rounding=ROUND_CEILING)` expresses the intent ("round up to 2dp") directly and is exact by construction — no tolerance to guess, no drift to compensate for.

This is small, but it produces **`CLAUDE_PER_VOYAGE_CEILING`** — a served constant that multiplies every token budget. A one-ULP difference at a boundary changes a shipped number. **Control:** table-driven test over boundary values (`1.70`, `1.7000001`, `1.699999`, `1.6999999999`) asserting both implementations agree, then keep the table pinned on the `decimal` version.

---

## 10. Progress / IO plumbing — KEEP + RE-OPEN TRIGGER

**Verdict: KEEP**, with triggers named. This is the `#202`-shaped disposition: found, considered, deliberately not churned.

- **`SurveyRunner` progress** (`PROGRESS_EVERY`, `progress_callback`, `--progress-file` append) — `tqdm` 4.67.3 and `rich` 15.0.0 are both already resolvable in the lock. But the current design writes progress to **stderr AND a file**, which is what a long unattended survey actually needs; `tqdm` targets a TTY and degrades to noise when redirected. The hand-roll is ~10 lines and fits the Unix-philosophy rule the repo follows. **RE-OPEN TRIGGER:** if the survey ever grows an interactive/TTY mode, or a second progress consumer, adopt `rich.progress` rather than adding a third emitter.
- **`concurrent.futures.ThreadPoolExecutor` + `Lock`** — stdlib IS the library. KEEP.
- **`argparse`** across all four CLIs — `click`/`typer` are present transitively, but argparse does the job, and swapping four CLIs is pure churn with a behaviour-change surface (`typer` changes `--help` text and error exit codes). **KEEP. RE-OPEN TRIGGER:** if a script grows subcommands or shared option groups across files, revisit.
- **`_write_jsonl` / `to_row` / `json.dumps`** — `jsonlines` exists but adds nothing over `json.dumps(...) + "\n"`. KEEP.

**⚠ One flagged inefficiency, not a package matter [source-verified]:** `SurveyRunner._write_row` opens and closes the JSONL file **for every single measurement row**, inside the write lock:

```
with self._write_lock:
    with self._jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(measurement.to_row()) + "\n")
```

A 933-file × 3-model run is ~2,800 open/close cycles serialised behind one lock. The fix is holding the handle open for the run's lifetime (the `ProjectResult` loop already brackets it). Raising it because scope law says to; it is a real inefficiency in committed code and I am not the one to decide whether 11-i touches it.

---

## OUT-OF-MISSION FINDINGS (scope law — raised, not buried, not fixed)

**F1 — `scripts/search_score_survey.py` defaults to PRODUCTION with no override. (decision D-B)**
`DEFAULT_SURREAL_URL = "ws://127.0.0.1:18500/rpc"` **[source-verified]** — and `:18500` is production `lore-surreal` per this repo's `CLAUDE.md` and `MEMORY.md` ("never point a test at :18500"). Its `build_arg_parser` exposes only `--eval-xml`, `--out-dir`, `--summary-filename`, `--jsonl-filename` — **there is no `--url`, `--namespace`, or `--database` flag** **[source-verified]**. By contrast `snapshot_gc.py`, which targets the same store, exposes all three. The survey is documented and (as far as I read) genuinely read-only — it never calls `ensure_ready()` — so this is not a live data-loss risk. But a production URL that a run *cannot* redirect is one edit away from being one. **Recommend adding `--url`/`--namespace`/`--database` with the current values as defaults.**

**F2 — connection coordinates duplicated across two scripts.**
`search_score_survey.py` and `snapshot_gc.py` each carry their own `DEFAULT_URL`/`NAMESPACE`/`DATABASE`/`USER_ENV`/`PASSWORD_ENV`/`DIM` constants with identical values **[source-verified]**. Both deliberately bypass `loremaster.config.load_config` for a documented reason (it eagerly requires `ANTHROPIC_API_KEY`). The *reason* is sound; the *duplication* is a second copy of a connection policy. The right fix is a narrow shared seam (a `load_config`-lite that skips the eager key), not a third copy — this is a DESIGN decision, escalating rather than proposing an edit.

**F3 — #199 restated with a consequence, because it changes how everything above should be read.**
`pyproject.toml` `testpaths = ["lorescribe/tests", "loresigil/tests", "loremaster/tests"]` **[source-verified]** — `scripts/` is absent. So **none** of `scripts/test_*.py` (~1,787 LOC, ~50 tests) has ever run in a gate. The consequence for this mission specifically: **the `is`-identity pins in `TestPredicateParityWithProduction`** — the single instrument standing between the survey's predicate and production's — **have never executed**. Every "this is tested" reassurance about `scripts/` in this report should be read as "there exists a test file", not "a gate verified it". (D-D.)

**F4 — the `noqa: UP037` quoted-annotation receipts.**
`SurveyRunner._measure_one` carries `# noqa: UP037` with a comment saying unquoting *"would drop this string from the `ast.Constant` set this pinned survey tool's byte-identity receipt walks"* **[source-verified]**. I did not chase what walks it. Flagging because **any port of `token_survey.py` risks silently breaking a byte-identity receipt that lives outside the file** — whoever executes 11-i must find that walker before reformatting these annotations.

---

## What I did NOT do (bounds on this report)

- I did **not** run any script, hit the Anthropic API, or connect to either SurrealDB store. Every package claim is from reading installed source/signatures in an ephemeral overlay; every code claim is from reading the worktree.
- I did **not** re-derive #201's five items or re-verify their measurements — the brief forbade it and I honoured it. Where I cite them (§4, §PORT-VS-RE-DERIVE) I am building on them, not re-checking them.
- I did **not** read the ~1,787 LOC of `scripts/test_*.py`. That matters most for §PORT-VS-RE-DERIVE item 1 and §C1: I can see *which* pins exist by name via grep, but I have not read what they assert. **A contract author porting this core must read them; my split is derived from the production code's structure, not from its tests.**
- `lore_search`/`lore_impact` were **not used at all** — the index watches the main checkout, not this worktree (#125). Every structural claim is grep/Read in `lore-pkt11i` at `b4eb32a`.

---

*Written 2026-07-25 against worktree `/home/ejprice/PycharmProjects/lore-pkt11i`, branch `pkt11i-floor-calibration-dark`, at commit `b4eb32a`. Package versions probed this sitting: `anthropic` 0.120.0 · `python-dotenv` 1.2.2 · `pathspec` 1.1.1 · `tabulate` 0.10.0 · CPython 3.14.6. numpy/scipy/scikit-learn are ABSENT from the current environment (probed) — #201's items require adding them, which the operator has authorised.*
