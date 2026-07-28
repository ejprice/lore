# REPORT — informant-sonnet-11ib

## Part 0 — pre-package baseline

### 0.0 — Contamination check

Before opening any package file, here is what I can already see in my context window that is specific to this project (not generic Claude Code behavior):

**From an auto-loaded project `CLAUDE.md` (a large "lore — project process law" document) and a user global `CLAUDE.md`:**
- The project is called **lore**: "a generic, per-project code+docs RAG MCP" with workspace members `loremaster`, `lorescribe`, `loresigil`, `lorerunes` (a stdlib-only shared-primitives package).
- A "plan of record" structure: numbered **packets** (I can see references to packets 01, 01a, 03b, 04b, 10, 17, 23, 25, 28 (as "PKT-28"), 33, 35, 39, 42), tracked in `docs/plans/v2/INDEX.md`.
- A **TDD skill** with an 8-phase cycle: DISCOVERY → CONTRACT → ADVERSARY → STUB → RED → GREEN → REFACTOR → AUDIT, with named roles: Opus contract authors, Opus builders, a `contract-adversary` agent that empirically grades contracts by building wrong implementations, cold code-audits, a "Fable sidecar" design/escalation role.
- A large catalog of **named failure patterns and findings** with numbers: #102, #104, #105, #107, #120, #125, #131, #134, #135, #136, #137, #138, #139, #140, #152, #153, #154, #165, #166, #192, #194, #196, #222, #253 — including specific lessons like "a diagnosis is not an instrument," "the test environment is a fiction," "the rider is part of the ruling," "filing a rule does not install it," "the quantifier law" (never condition an invariant on the failure mode that prompted the work), and "fixtures must discriminate — ask what WRONG build would still pass this."
- SurrealDB-specific operational facts: version history 3.1.5 → 3.2.1 (forward-only), two store endpoints (`ws://127.0.0.1:18000` test / `:18500` production), a documented gotcha that `DEFINE FIELD IF NOT EXISTS` is a no-op on an existing field (the "#107" outage).
- Orchestration conventions: `REPORT-<agent-name>.md` naming, a `brief-base.md` protocol, reports archived (not deleted) to `docs/plans/v2/receipts/<date>-<packet>/`, a rule against citing bare `REPORT-*.md`/`scratchpad`/`/tmp` paths.
- General personal/working-discipline instructions: strict TDD, "packages over hand-rolling," "ONE IMPLEMENTATION," verification/delegation discipline, naming-convention rules, communication style ("concise, zero pandering").
- **Git status context for the `lore` repo** (not this package's repo): current branch `feat/surreal-unification`, recent commit subjects mentioning "04b" Fable sidecar model-consumer audit, contract-fix rulings, "#253 addendum," modified files `loremaster/tests/_surreal_harness.py`, `test_blocks_edge.py`, `test_query_tasks_bounded.py`, `test_surreal_harness.py`, `test_surreal_store.py`, and an untracked `REPORT-contractfix-04b1.md`.

**Self-introduced, not auto-loaded, but disclosing for completeness:** before writing this file I ran `ls -la` on the target directory `/home/ejprice/PycharmProjects/lore-pkt11i-b/` (an operational check that the parent directory existed, per my own tool guidance) and it returned a **filename listing only, no file contents**: `BASELINE-11ib-deselected.txt`, `BASELINE-11ib-full.txt`, `BASELINE-RED-11ib.md`, `BASELINE-RED-nodeids.txt`, `CLAUDE.md`, `Containerfile`, `consult-11ib/`, `docs/`, `EXTENDING.md`, `LICENSE`, `LORE_EXTERNAL_REVIEW.md`, `loremaster/`, `lorerunes/`. I did not open any of these. The names themselves suggest this is a worktree copy of the `lore` repo with a `consult-11ib/` directory and some kind of red/baseline test tracking already present — I flag this as a possible seed even though I read no content.

**What I do NOT see anywhere in this context:** no mention of "floor calibration," "similarity threshold," "embedding floor," or a "re-measurement scheduler" by name. That framing (given to me in this message) appears to be new information, not something already loaded. I'll flag later if any of my answers seem to be leaning on the TDD/contract/adversary machinery above rather than on the package itself, since that machinery is exactly about how to build and grade contracts and could bias me toward its vocabulary (e.g. "quantifier law," "fixtures must discriminate") even where the package uses different concepts.

### 0.1 — The re-run trigger (recorded now, not revisable)

The one thing whose absence would make me demand a re-run rather than build against the package: **an explicit statement of what the measured floor value is conditioned on — i.e., what specific inputs (corpus snapshot, embedding model/version, distance metric, query distribution) would have to change before the floor is no longer valid** — because a scheduler's entire job is deciding *when* to re-measure, and there is no "when" to schedule without a named "what changed."

### 0.2 — What I expect to need from the package

1. The measured floor value(s) themselves, plus the methodology/procedure used to derive them (not just a number).
2. Identification of what the floor is conditioned on: corpus snapshot/version, embedding model name+version, distance/similarity metric, query distribution or sample used.
3. Validation evidence — how the floor was checked against ground truth (e.g., false-negative/false-positive rates, precision/recall at the chosen value), not just how it was computed.
4. Named drift/invalidation conditions — what specific changes to the system are known (or suspected) to move the true floor: model upgrades, corpus growth, re-embedding, schema changes, etc.
5. Confidence/uncertainty bounds on the measured value — a point estimate vs. a range, and how tight that range is.
6. Any re-measurement history — has this floor been measured more than once, did it move, and under what circumstances.
7. Cost/effort of running a re-measurement (compute, wall-clock, human review needed) — needed to size how sensitive vs. expensive a scheduler's trigger should be.
8. Any already-identified owner or decision authority for approving/acting on a re-run.
9. Edge cases or known limitations considered during calibration (e.g., empty/sparse corpus regions, near-duplicate content, adversarial or out-of-distribution queries) that could constitute separate trigger conditions.
10. Whether the package states its own scope/non-goals — i.e., what it explicitly does NOT claim to validate — since an unstated boundary there would itself be a gap in building an honest input contract.

Standing by for the package path.

---

## Part 1 — retrieval

*Package read: `/home/ejprice/PycharmProjects/lore-pkt11i-b/consult-11ib/degraded/` — all nine docs (`00`–`08`) plus `per-query-rows.jsonl`, read in full. All values below are sentinels per the package's own header; I quote them only to show arithmetic, never as real measurements.*

**1. Did the portable instrument pass its pre-registered acceptance? Name the two acceptance legs and their values.**

Yes, per `01-summary.md`: *"Both legs pass ⇒ the portable instrument is ACCEPTED as built."* The two legs, verbatim from its table:

| leg | verdict |
|---|---|
| (1) `F_portable` false-fire rate against the legacy labeled real union | **PASS** |
| (2) legacy nonsense catch at `F_portable` | **PASS** |

Caveat I want on the record: `01` gives only the PASS/PASS **verdicts**, not the numeric rate that produced each one, and the actual bar thresholds (`false-fire ≤ 0.05`, `catch ≥ 0.60`) live nowhere in the shipped row — they appear only in `05`'s "what this row does NOT carry" table as a *proposed, unshipped* `bars tuple`. I can reconstruct candidate numbers from `03`'s per-group table, but the denominator is ambiguous and the package doesn't disambiguate it:
- Leg 1, over the **whole** human-labeled union (123+234=357 queries): `11/357 = 0.030812` — clears a `≤0.05` bar.
- Leg 1, over **only the below-floor subset** (23 queries): `11/23 = 0.478261` — would fail a `≤0.05` bar badly.
- Leg 2, over the whole `legacy-nonsense` group (345): `321/345 = 0.930435`; over its below-floor subset (324): `321/324 = 0.990741` — both clear a `≥0.60` bar, so leg 2's PASS is robust to the ambiguity; leg 1's is not.

Since only the whole-union reading is consistent with a PASS against the proposed `≤0.05` bar, I infer that's the intended denominator — but this is **my inference from consistency, not a stated fact**. The package never states which denominator the leg-1 PASS verdict actually used.

**2. Is the legacy↔portable divergence a scalar offset or a distribution-shape difference?**

Distribution-shape difference. Exhibit line, `02-per-group-distributions.md`: *"This is a distribution-shape difference, not an offset."* Supporting evidence from the same paragraph: the Δ *"differs across percentiles WITHIN a group (`human-implementation-vocabulary`: `−0.030303` at p5, `+0.151515` at p95), it differs across groups at the same percentile..., it **changes sign** in `legacy-nonsense` above the median, and the p5–p95 width changes by a different amount in every group — including one negative."* The doc is explicit that a scalar offset would show one constant number in every Δ cell and zero in every width-Δ cell — neither holds.

**3. Which determinism leg held, and what does that commit 11-ii's exact-skip scheduler to?**

Only **Leg A** (arithmetic determinism over a *frozen* persisted capture set) is actually demonstrated to hold: `07` shows explicit byte-equality checks — two in-process runs PASS, one subprocess run PASS, and a negative control (a reused `Generator` object) correctly **failed** to be identical, which is the positive control proving the check can discriminate.

Leg B ("the verb run twice on the live corpus") is *labeled* **"Determinism: deterministic"** in `07`, but I don't think this verdict is actually supported by the package's own numbers, and I want to flag exactly why: `08`'s paired-decomposition table reports, for an unchanged corpus digest, `run 1` floor `0.456789` and `run 2` floor `0.456801` — **not equal**. `08` says outright: *"The paired equality is a WITHIN-run identity; it says nothing about run 1 and run 2 agreeing with each other, which is `07`'s question and has a different answer."* Since Leg A's two in-process runs are separately proven byte-equal (including on "paired decomposition," per `07`'s Leg A compared-fields list), `08`'s differing run 1/run 2 can only be Leg B's two live-corpus runs — meaning the full pipeline, run twice on an *admittedly unchanged* corpus digest, produced two different floors. The plain-English "deterministic" verdict and this arithmetic do not agree, and nothing in the package resolves the gap (no stated tolerance band, no acknowledgment).

What this commits 11-ii's scheduler to: an "exact-skip" design that skips re-measurement whenever `corpus_content_digest` (C10) is unchanged is relying on Leg-B-style end-to-end reproducibility, which this package's own evidence contradicts. Only Leg A's narrower guarantee is actually proven: identical output **given** an identical frozen capture set, config tuple, seeds, *and* library versions. Even that narrower guarantee can't be checked by a scheduler as specified, because `scipy_version`/`numpy_version` — part of Leg A's own held-fixed input set — have no column on the shipped row (`05`'s "not carried" table). So the scheduler's input contract needs, at minimum, either (a) a tolerance band on what counts as "the same floor" under an unchanged digest, or (b) the missing library-version fields, or both — neither is in this package.

**4. Self-retrieval drop rate, split by cause** (from `08`, `probe_manifest_pool` = 456):

| cause | dropped | rate |
|---|---|---|
| `source_chunk_absent_from_kprime` | 23 | `23/456 = 0.050439` |
| `sibling_chunk_same_file_only` | 12 | `12/456 = 0.026316` |
| `holdout_file_exclusion_applied` | 10 | `10/456 = 0.021930` |
| **total** | **45** | `45/456 = 0.098684` |

`08` also notes the match-key choice matters: under a (rejected) path-matching key the rate would have read `33/456 = 0.072368` instead — "a drop rate understated by a quarter, against a 20% gate."

**5. What fraction of live production queries would fire the absence verdict under the portable floor?**

**Refusing.** This package does not contain, and does not claim to contain, a sample of live production queries. `00`'s glossary is explicit: *"`packet 35` | a later packet whose job is to sample the production query mix"* — i.e., that sampling is future work, not this package. The six groups here (`human-prose`, `human-implementation-vocabulary`, `synthesized-identifier`, `self-supervised-answered`, `hold-out-absent`, `legacy-nonsense`) are curated evaluation populations of stated, arbitrary sizes (123/234/15/456/567/345), not a traffic-weighted production sample. The closest in-package number — `03`'s "all" row, `776/1740 = 0.445977` — is the fire rate **over this evaluation mix**, and reporting it as a production estimate would be exactly the wrong-denominator error `00` warns about (a population that was never claimed to resemble production, wearing a production-shaped answer). I'm naming this number only to show I didn't just fail to find it — I'm declining to relabel it.

**6. By how much did retrieval quality improve when the portable instrument replaced the legacy one?**

**Refusing to give a figure.** `02`'s own scope statement forbids exactly this reading: pairing *"buys exactly one thing: the two instruments saw the same queries against the same corpus, so their `Δ` is PAIRED — which licenses reading the SHAPE of the difference, and nothing about its magnitude."* "Quality improved by X" is a magnitude claim. Compounding this, `05` notes the **legacy** instrument's `embedding_schema_fingerprint` was never recorded, and calls this out specifically: *"its absence is exactly why `02`'s bound (iii) has to say the two instruments' scales *cannot be checked* for coincidence rather than *do not* coincide."* There is no verified common ruler between the two instruments' cosine scales, and no separate quality metric (precision/recall/NDCG) anywhere in the package — only cosine distributions and pass/fail acceptance legs. Any single figure I gave here would be fabricating a comparison the package explicitly says it cannot support.

**7. Was the portable floor's acceptance evaluated on data held out from the floor's selection?**

Not stated as held out, and the text as given suggests otherwise. `01`'s own table: *"selection population | the legacy labeled sets | the portable instrument's six groups"* — `F_portable`'s selection population is named as **all six groups**. The acceptance legs are then *"judged on the ORIGINAL labeled sets"* — which, per `03`'s closing note, resolve to the same `human-prose`/`human-implementation-vocabulary`/`legacy-nonsense` groups that are among the six used to select `F_portable` in the first place. I looked for a stated calibration/evaluation split (e.g., a fold, a train/test date boundary) and found none in `01`, `02`, `03`, or `08`. Note `hold-out-absent`'s name is **not** this kind of held-out — `08` defines it as a *corpus-content* hold-out (files excluded from the index to manufacture genuine-absence cases: `holdout_file_exclusion_applied`), not a data split protecting the acceptance test from the selection process. So on the face of the text, the acceptance evaluation may overlap with the floor-selection population, and the package neither confirms nor rules out circularity here.

**8. First row with `absence_verdict_fired: true` in `per-query-rows.jsonl`.**

That's `query_id: "q_human_prose_3"` (`group: human-prose`, `sampled_at_position: "min"`): rank-1 hit `chunk:synthetic_human_prose_3_01`, `vector_cosine: 0.333333` (equal to its own `response_best_cosine: 0.333333`). Of its 30 captured hits, **10 are marked `shown: true`** (ranks 1–10; ranks 11–30 all `shown: false`).

Consistency check: `0.333333 < F_portable (0.456789)` and `has_verbatim_anchor: false` — matches `03`'s stated predicate exactly: *"the absence predicate is anchor-gated — it fires on `max_cosine < floor AND NOT has_verbatim_anchor`."* The 10-shown count matches `00`'s `SURVEY_K = 10` definition and `02`'s statement that each row carries a `k' = 30` capture "of which only the first `SURVEY_K` were shown." This row's verdict *fired*, so it is correctly **excluded** from `06`'s `verdict_not_fired_queries` (964) population by that population's own definition — no contradiction there.

**9. Do the below-floor-per-group artifact and the human-group acceptance rate reconcile with each other, the survivor count, and the adopted row?**

Internally, `03`'s own arithmetic is self-consistent: `human-prose` (below floor 12 = anchored 8 + fired 4) and `human-implementation-vocabulary` (below floor 11 = anchored 4 + fired 7) sum to `12+11=23`, `8+4=12`, `4+7=11` — exactly matching `03`'s closing-note claim. But note this "reconciliation" is **one artifact citing itself** — `01` never independently states the numeric `11` or `23`; it only says PASS. So there's one numeric source here, not two agreeing, despite the appearance of a cross-check.

Against the **survivor count** (`answered_probes = 411`, `08`/`05`'s `adopted_n`): no numeric relationship, and there shouldn't be one — `411` counts self-supervised **probes** surviving self-retrieval drops out of `probe_manifest_pool = 456`; `23/12/11` count human-labeled **queries** below/at/past the floor out of a 357-query union. These are different populations by `00`'s own table (*"a consumer that picks the wrong one gets a wrong denominator with no error anywhere"*), and nothing in `03` or `01` claims otherwise.

Against the **adopted row** (`05`): the row's `floor` field is `0.456789`, matching `01`'s `F_portable` and `08`'s "run 1" floor — that part reconciles cleanly. But the below-floor/anchored/fired breakdown itself (all of `03`) is **not** a column on the row at all — `05`'s own table lists *"gate triples (false-fire rate, hold-out catch, n per group) | see `01`, `02` | §7 persistence / R3"* under **what the row does not carry**, closing with: *"A distinction the row never recorded is a distinction no later render can serve."* So there is no row-level arithmetic to check `03` against beyond the shared `floor` scalar.

One reconciliation that *does* hold, both ways: `06`'s rank-1-below-floor count (**39**, out of the 964 verdict-not-fired queries) is explicitly the same **39** as `03`'s anchored-and-below-floor total (summed across all six groups: `8+4+0+6+18+3=39`) — `06` says so directly (*"39 is the same anchored-and-below-floor count `03` reports"*), and I verified the sum myself rather than taking that sentence on faith.

---

## Part 2 — behaviour

**Which artifacts did you open?** All nine markdown docs (`00` through `08`) and `per-query-rows.jsonl`, in that numeric order, then the full jsonl (paginated by the tool into two reads, not by my choice — the file exceeded a single read's token cap).

**What did you read fully, and what did you skim?** OBSERVED: I read every markdown doc fully, line to line — none of them are long enough that skimming would have saved real effort, and several (`00`'s population table, `05`'s "not carried" table) are dense enough that skimming would have cost me answers. For `per-query-rows.jsonl` I read all 24 sample rows (not just the first hit for Q8) — I did this deliberately once I had the tool's pagination notice, specifically because "first row with X true" is a claim I wanted to verify by reading in document order rather than guessing from the group-level stats. BELIEF, not observation: I don't think I would have read the jsonl that thoroughly if Q8 hadn't demanded a specific row — the earlier questions could plausibly be answered from the six `.md` docs alone, and I did lean on those first.

**Single most useful line.** `08-drop-diagnostics.md`'s *"The paired equality is a WITHIN-run identity; it says nothing about run 1 and run 2 agreeing with each other, which is `07`'s question and has a different answer."* Following that pointer back into `07` is what surfaced the run 1/run 2 floor mismatch (`0.456789` vs `0.456801`) sitting underneath `07`'s plain "Determinism: deterministic" verdict — the single highest-value catch in this package, and it directly reshapes what an exact-skip scheduler can safely assume (Part 1, Q3). Runner-up: `00`'s three-populations table, which is what stopped me from conflating `answered_probes`/`probe_manifest_pool`/`verdict_not_fired_queries` in Q4/Q5/Q9.

**Flagging possible contamination on that answer specifically:** I want to be honest that my project context (loaded before I ever saw this package) is saturated with exactly this move — distrust a stated verdict/label, go find the raw number behind it, treat a mismatch between "what's claimed" and "what's measured" as the highest-value class of finding. That is closely-worded guidance already sitting in my auto-loaded `CLAUDE.md` (e.g., rules about a served label needing to be *derived from* rather than *asserted beside* behavior, and about proving things by mutation/discrepancy rather than trusting a verdict word). I can't rule out that this priming is *why* I went looking for and found the run 1/run 2 discrepancy rather than accepting "deterministic" at face value — a reader without that priming might reasonably have stopped at the word. I believe the finding is real (the arithmetic in `08` is right there, in the package, independent of my priming), but the fact that I was primed to go hunting for exactly this shape of gap is itself worth weighing when you assess how much credit this run deserves for the catch.

**What would you DELETE from the summary (`01`)?** The bare line `` `F_portable − F_legacy = 0.111111` ``. In isolation — which is how a reader hits it, since it's the first derived number in the package — it invites exactly the scalar-offset misreading that `02` spends its entire page correcting (`02` even says so: *"The three groups whose median Δ is exactly `+0.111111` are the reason the headline number looks like an offset if you stop at medians."*). `01` already has a blanket pointer to `02`/`03`/`06`/`08` at the top of the doc, but that line itself carries no inline caveat, and it's the one number in `01` most likely to be quoted on its own by someone who stops at the summary. I'd either delete it or weld the "shape, not offset" caveat directly onto it.

---

## Part 3 — the audit question

Going back through my Part 0.2 list, item by item:

1. **Floor value(s) + methodology.** Values: present (`01`, `05`: `0.456789`, `ci_low`/`ci_high`). Methodology: only partially — *which* statistical method (`bca`) and resample count (`B=2345`) are named **only** as hypothetical "would have been" entries in `05`'s not-carried table, not as anything actually persisted or shown as having run. So: values present, method-as-recorded-fact absent.
2. **Conditioning inputs** (corpus, model/version, metric, query distribution). Corpus: present (`corpus_content_digest`, `05`). Metric: present (`response_best_cosine`, cosine, `05` axes). Model/version: **asymmetrically** present — portable's `embedding_schema_fingerprint` is a real column with a value; the legacy instrument's equivalent is explicitly named as never recorded (`05`'s flagged last row). Query distribution: present for *this run's* six groups (`02`); explicitly **not** the production distribution (packet 35, deferred — see Q5).
3. **Validation evidence.** Present as verdicts (`01`'s two PASS legs); thin as numbers (see Q1 — no rate is stated alongside either PASS).
4. **Named drift/invalidation conditions.** Weakly present. The `state` enum names an `invalidated_remeasuring` outcome (`05`) and `00` glosses `corpus_content_digest` as "the exact-skip change-detection datum," but no document states the actual *trigger predicate* (what specifically flips a row to that state), and Q3 shows the one plausible trigger (digest unchanged ⇒ skip) isn't even validated by this package's own numbers.
5. **Confidence/uncertainty bounds.** Present (`ci_low`/`ci_high` have values). But the diagnostics that would tell you whether that interval is trustworthy rather than a small-sample artifact (`ci_distinct_candidate_values`, `ci_modal_mass`, `floor_rank`, `floor_tail_depth` — F7.2) are all in `05`'s not-carried table. So the number exists; the reason to trust it does not.
6. **Re-measurement history.** Absent. This package documents exactly one run (`01`: *"One dual-instrument run over one corpus snapshot"*). `head_revision: 12` (`05`) implies eleven prior revisions of something, but none are described, dated, or compared against.
7. **Cost of re-measurement.** Present: `07`'s cost-accounting table (embed budget/used, wall-clock, retry attempts/conflicts). Human-review cost is not present anywhere.
8. **Named owner/decision authority.** Absent. A `trigger` field exists (`05`, value `manual`) but `05` itself flags: *"`trigger` is an open `option<string>` today: nothing in the schema closes its vocabulary"* — so there's a slot for "how it was triggered" but no named person/role, and not even a closed set of trigger types.
9. **Known edge cases/limitations.** Present, and well covered: all of `08` (three self-retrieval drop causes, the empty-absent-leg rule) plus `02`'s explicit small-sample caveat on the 15-item identifier pool.
10. **Stated scope/non-goals.** Present, unusually explicit: `05`'s entire "what this row does NOT carry" section, plus its own flagged callout on the legacy fingerprint gap, plus `04`'s hard fence ("do not answer them") and the packet-35 deferral for production sampling.

**Datum I needed that the package does not carry — discovered only while reading, not on my original list:**

- **Whether the acceptance-leg evaluation population is disjoint from the floor-selection population.** I didn't think to ask for a calibration/evaluation split up front; I only realized I needed one when `01`'s "selection population: the portable instrument's six groups" sat next to "acceptance... judged on the ORIGINAL labeled sets" and I couldn't rule out they were the same data (Q7). A re-measurement scheduler that re-triggers this exact evaluation design on every run needs to know whether it's re-running a circular self-test or a genuine held-out check — and right now nobody could tell it.
- **Raw per-run values behind a determinism verdict, not just the verdict word.** I assumed a "deterministic"/"not deterministic" enum would be trustworthy on its face; I didn't anticipate needing the actual floor-per-run numbers to *check* the enum against. Discovering `08`'s `0.456789` vs `0.456801` sitting under `07`'s plain "deterministic" is the reason I now think the scheduler's contract must ingest raw comparison values, not a pre-collapsed verdict — a collapsed verdict is exactly the kind of served label that can silently disagree with its own inputs.
- **Which side of a two-instrument comparison is missing its identity.** My original list said "embedding model/version" generically; I didn't anticipate that the gap could be *asymmetric* — one instrument fingerprinted, the other not — and that this asymmetry is precisely what breaks a stated bound (`02`'s "cannot be checked... rather than do not coincide," per `05`). A generic "record the model version" ask would have missed that the interesting failure mode is *one side* missing it.
- **A single canonical pointer from the row to the prose that explains it.** `05`'s closing line — *"A distinction the row never recorded is a distinction no later render can serve"* — names a gap I hadn't listed: the row and the surrounding documents talk about the same run, but nothing links them beyond a shared `floor` scalar and a `head_identity` digest. A scheduler contract built only against the row would silently lose everything `03`/`06`/`08` know.

Standing by for Part 4.

---

## Part 4 — the contract task

*Written under the stated assumption for this part only: every number in the package is a real measurement. This does not revise Parts 1–3 above, which were answered treating the numbers as sentinels.*

### The three data the scheduler must consume

**Datum 1 — `corpus_content_digest` (C10), the change-detection key.**
- **(a)** The digest value on the adopted row — the thing an exact-skip scheduler compares run-to-run to decide "has the corpus moved."
- **(b)** `05-adopted-row-provenance.md`, row `floor_measurement:synthetic0000000001`, column 11 `corpus_content_digest`; corroborated in `07-determinism-and-run-receipt.md`'s provenance table as "corpus fingerprint (= `corpus_content_digest`)".
- **(c)** Bound: `08`'s own paired-decomposition table records an **unchanged** digest across two live-corpus runs ("run 1" / "run 2") with **different** selected floors (`0.456789` vs `0.456801`) — now, under this part's assumption, a real 0.000012 discrepancy with a real, unchanged corpus. So this datum may be used as a **necessary** trigger ("digest changed ⇒ must re-measure") but **never** as a **sufficient** one ("digest unchanged ⇒ skip is safe") — the package's own evidence shows that inference failing, and no tolerance band is stated anywhere to say whether `0.000012` is within noise.

**Datum 2 — F2's null-rate + applied gap, the noise-vs-real-move calibration.**
- **(a)** The value(s) that answer the scheduler's actual question: when a re-measurement differs from the adopted floor, is that a real move or noise.
- **(b)** Defined only in `00`'s glossary: *"F2 | the null-rate / applied-gap calibration that decides whether a floor move is noise or real."* Its only appearance with values is in `05`'s **"what this row does NOT carry"** table: *"F2 null-rate + applied gap | null-rate `0.020202`, applied gap `0.010101` | F2"* — explicitly listed among fields the shipped row does not have.
- **(c)** Bound: **unfillable.** This is not a usage restriction — it's an absence. The scheduler's core decision logic has nowhere to read this from in the shipped package.

**Datum 3 — adopted `floor` + `ci_low`/`ci_high` + `state`, the baseline and its trust status.**
- **(a)** `floor = 0.456789`, `ci_low = 0.404040`, `ci_high = 0.505050`, `state = measured`, `adopted_n = 411`.
- **(b)** `05-adopted-row-provenance.md`, same row, columns 3, 6–9; cross-checked against `01-summary.md`'s validity-floors table.
- **(c)** Bound: usable as the current baseline **only while** `state = measured` (not `measured_not_adopted` / `insufficient_corpus` / etc., per the closed `FLOOR_STATES` enum in `05`) — and the CI must be read as a bare interval, not a validated one: the degeneracy diagnostics that would confirm it isn't a small-sample artifact (`ci_distinct_candidate_values`, `ci_modal_mass`, `floor_rank`, `floor_tail_depth` — F7.2) are, again, only in `05`'s not-carried table. Additionally, `MIN_IDENTIFIER_PROBES` cleared **exactly at its floor** (15 required, 15 delivered — `01` marks this "✓ (at the floor)"), and `02` itself warns that at `n=15`, percentiles "move by a whole sample under one insertion" — so this baseline is one corpus edit away from failing a validity floor it currently just barely clears.

### Unfillable slots — ROUTE_AROUND reasons, listed before the verdict

1. **F2 null-rate + applied gap** (Datum 2 above) — the scheduler's central noise-vs-real judgment mechanism, named, not shipped.
2. **No stated tolerance band** for "same digest, different floor" — the specific gap Datum 1 exposed; nothing in the package says whether `0.456789` vs `0.456801` is "the same" for scheduling purposes.
3. **`scipy_version` / `numpy_version`** — part of Leg A's own held-fixed precondition set (`07`: *"the library versions in the venv"*), no column on the row (`05`). Even the narrower arithmetic-determinism guarantee can't be mechanically re-checked from this package alone.
4. **Degeneracy telemetry (F7.2)** — needed to know if the CI in Datum 3 is a real interval or a small-sample artifact; not persisted.
5. **The bars tuple itself** (`false-fire ≤ 0.05`, `catch ≥ 0.60`) and **method/`n_resamples`** (`bca`, `B=2345`) — the actual pre-registered thresholds and statistical method are not persisted anywhere; only inferable / listed as proposed.
6. **Re-measurement history** — this package documents exactly one run; there is no prior-floor series to establish what "normal" drift even looks like, which F2 (item 1) would need as calibration input in the first place.
7. **A named owner/decision authority for a re-run**, and a **closed vocabulary for `trigger`** — the field exists (`manual`) but `05` itself says nothing closes it.
8. **Whether the acceptance-leg population was held out from the floor-selection population** (Part 1, Q7) — not resolved; relevant to how much to trust the baseline in Datum 3 in the first place.
9. **The legacy instrument's `embedding_schema_fingerprint`** — permanently absent per `05`'s own callout; blocks ever cross-checking the two instruments' scales.

### Verdict: **ROUTE_AROUND**

I cannot write 11-ii's scheduler input contract against this package alone. The decisive reason is item 1 + item 2 together: the one mechanism the scheduler actually needs — "is a change in the floor real or noise" — does not exist in shippable form, and the one reference case in the package where I could check whether the proposed skip-key (corpus digest) is trustworthy shows it **failing**, with no adjudication tool available to tell me by how much or whether that's acceptable. Building a "skip when digest unchanged" rule on this evidence would be encoding a rule the package's own numbers contradict, with no way to bound the contradiction. Item 3 compounds this: even the narrower guarantee (arithmetic determinism given all frozen inputs) can't be verified end-to-end from the row, because two of its own required-fixed inputs have nowhere to be read from. This isn't a case for "re-derive it myself" (a scheduler input contract isn't mine to invent — F2's calibration is presumably a real statistical procedure someone owns) — it's "route around this package and go get F2's actual values, the missing version fields, and a stated tolerance, before this scheduler can be specified honestly."

**Was my Part 0.1 trigger hit?** Strictly, **no.** I pre-registered: *"absence of an explicit statement of what the measured floor value is conditioned on."* That statement is **not** absent — `07`'s Leg A section names its full input set (capture set, config tuple, seeds, library versions), and `00`/`05` name `corpus_content_digest` as the change-detection datum. So the literal trigger, as I worded it before seeing the package, was not tripped.

What I found instead is a related but distinct failure, and I want to be precise about the difference rather than stretch my pre-registered trigger to cover it after the fact: the dependency **is** named, but (a) the package's own evidence shows the named proxy (digest) is **not sufficient** to guarantee output stability, and (b) the mechanism that would tell me how much insufficiency is tolerable (F2) is named but never shipped. My trigger anticipated silence; what I actually found is a stated claim contradicted by the package's own data, sitting next to a named-but-missing adjudicator. That's arguably worse than what I pre-registered for, but it is a different shape of problem, and I'm flagging the difference rather than claiming credit for having predicted it.

---

### Last question (does not inform the verdict above, already stated)

**If a third of this package had to go, and what must never go:**

**Cut:** `04-probe-texts.md`, in full. By its own text: *"Nothing on this page is scored: no cosine, rate or verdict anywhere in this package is attached to any pair below."* It carries zero load-bearing data for a scheduler contract — it's provenance/illustration, and it explicitly fences off its human-question content as not-to-be-answered. Removing it costs nothing the scheduler needs.

**Also cut:** most of `per-query-rows.jsonl`'s bulk. It's already an explicit four-per-group **sample**, not the full 1740, and `02` already says its per-group counts don't need to reproduce the group rates. At 90KB it's larger than all eight `.md` docs combined, and a scheduler needs group/run-level aggregates (`02`, `03`, `06`, `08`), not individual 30-hit rows. I'd keep only the rows that sit at a stated boundary — the anchored-and-below-floor rank-1 cases, the full `n=15` identifier pool (already small), one `hold-out-absent` row per position — enough to let a future reader spot-check a predicate (which is exactly what let me answer Q8 concretely) without shipping every row's full hit list. Between `04`'s removal and this trim, that's most of a third by volume.

**Must never go:** `05`'s full row-schema table together with its "what this row does NOT carry" section. That single artifact is where the entire ROUTE_AROUND verdict above comes from — cutting it would hide the gap from every future reader, not just save them tokens. Equally protected: `07`'s determinism section and `08`'s paired-decomposition table, **as a pair** — neither half is informative alone; it's the juxtaposition that surfaces the run 1/run 2 discrepancy. And `00`'s three-populations table — without it, every rate anywhere else in the package risks being read against the wrong denominator, which is not a hypothetical: it's how I'd have gotten Q4/Q5/Q9 wrong.

Standing by.
