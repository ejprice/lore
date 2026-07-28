# REPORT — informant-cold-11ib (Cold Reader)

## Part 0 — Pre-Document Baseline

### 0.0 — Contamination check

I have not opened the target document. Before doing so, here is everything project-specific
already visible in my context window, named explicitly so it can be checked later against
anything I claim to "resolve" from the document itself.

**From auto-loaded instruction files (not the document, not something I searched for):**

- A global personal-instructions file (not project-specific) covering TDD workflow, a
  "contract-adversary"/tdd-skill 8-phase cycle (DISCOVERY→CONTRACT→ADVERSARY→STUB→RED→GREEN→
  REFACTOR→AUDIT), verification/delegation discipline, naming conventions, Python/SQL style,
  and references to unrelated projects (Odoo, Mezmo, a Manjaro/Podman/ZFS host). None of this
  appears to be about the project this consult concerns, except insofar as it establishes my
  general working habits (e.g. "verify, don't assume").
- A **second, heavily project-specific instructions file** that is clearly the CLAUDE.md of a
  project called **"lore"**. It is extensive and I have absorbed a large amount of its
  terminology and history before ever seeing the target document, including but not limited to:
  - Project identity: "lore" is a RAG/MCP server; its components are named **loremaster**,
    **lorerunes**, **lorescribe**, **loresigil**.
  - A house vocabulary of numbered "findings" (#24, #46, #94, #96, #102, #104, #105, #107,
    #120, #125, #131, #134, #136, #137, #138, #139, #140, #152, #153, #154, #165, #166, #192,
    #194, #196, #222, etc.), each tied to a named failure mode (e.g. "#107" = a schema
    migration no-op that broke `brief_publish` in production; "#140" = a scratch-copy
    provenance poison mode).
  - Named process concepts: "THE CONSUMER LAW", "THE TRUST DOCTRINE", "ONE IMPLEMENTATION",
    "THE RIDER IS PART OF THE RULING", "THE QUANTIFIER LAW", "the dogfood protocol", "packet"
    as a unit of work (e.g. "packet 01", "packet 03b", "packet 42", "PKT-28"), "DD-3.c" as a
    ruling ID, "contract-adversary" as a named agent role, "cold audit" as a named verification
    step, "Fable" as a named model/role (design sidecar), roster composition ("Opus contract
    authors, Opus builders, Opus contract-adversary, Opus cold audits, Fable sidecar").
  - Tooling names: `scripts/typecheck.sh`, `scripts/scratch_copy.sh`,
    `scripts/registration_sites.py`, `scripts/mutation_proof.py`, `lore_index`, `lore_search`,
    `lore_get_symbol`, `lore_impact`, `lore_read`, `lore_remember`, `lore_recall`,
    `lore_findings`, `lore_tasks` (state machine claimed→in_progress→done).
  - Infrastructure specifics: SurrealDB 3.2.1, two store instances named **spike-surreal**
    (`ws://127.0.0.1:18000`, test) and **lore-surreal** (`:18500`, production), systemd/quadlet
    management, a doc `docs/reference/surrealdb-31-capabilities.md`, a plan-of-record file
    `docs/plans/v2/INDEX.md`, a receipts convention
    `docs/plans/v2/receipts/<date>-<packet>/`.
  - A standing directive that git worktrees are currently NOT to be used for this project
    (findings #134/#125/#136).
- An auto-loaded memory pointer file confirming the same project ("lore"), repeating the
  spike-surreal/lore-surreal port split, the SurrealDB 3.2.1 forward-only constraint, and the
  `docs/plans/v2/INDEX.md` plan-of-record pointer.

**From the git status snapshot shown to me at session start (not the document):**

- Current branch `feat/surreal-unification`.
- Modified files under `loremaster/tests/`: `_surreal_harness.py`, `test_blocks_edge.py`,
  `test_query_tasks_bounded.py`, `test_surreal_harness.py`, `test_surreal_store.py`.
- An untracked file `REPORT-contractfix-04b1.md`.
- Five recent commit messages, all referencing a "04b" / "04b-1" work packet, e.g.:
  "Fable sidecar model-consumer audit — 2 overrules, measured not argued", "start the Fable
  design sidecar — and it outranks every ruling in the file", "rulings round 2 — limit
  push-down, one cycle detector, TOCTOU closed by construction", "adversary verdict
  INSUFFICIENT — 3 wrong builds survive 80/80", "#253 addendum — the diff, not the twin, and
  it found a C-DEF blocker".

**From the task-assignment message itself:**

- The framing "consumer consult," the role name "cold reader," and my own agent id
  `informant-cold-11ib`.
- My report path, `/home/ejprice/PycharmProjects/lore-pkt11i-b/REPORT-informant-cold-11ib.md` —
  the directory name `lore-pkt11i-b` itself tells me this working copy is scoped to a specific
  work packet ("11i" or "11i-b"), consistent with the "packet" vocabulary above.

**From a directory listing I ran to confirm my report path's parent directory exists (before
writing this file) — I want to flag this even though it was not a document read:**

- I ran `ls -la` on `/home/ejprice/PycharmProjects/lore-pkt11i-b/` to verify it existed before
  writing to it. That listing surfaced file/directory names I had not otherwise been given,
  including: `BASELINE-11ib-deselected.txt`, `BASELINE-11ib-full.txt`, `BASELINE-RED-11ib.md`,
  `BASELINE-RED-nodeids.txt`, a `CLAUDE.md` (61KB — presumably the same project file described
  above), `Containerfile`, `.containerignore`, a `consult-11ib/` directory, `docs/`,
  `EXTENDING.md`, `LICENSE`, `LORE_EXTERNAL_REVIEW.md`, `loremaster/`, `lorerunes/`. I did not
  open any of these. But I now know they exist, and that names like "BASELINE-RED" and
  "consult-11ib" are part of this packet's furniture — that is contamination I would not have
  had if I'd been handed a bare file path with no need to stat its parent.

**Net assessment:** I am not a blank reader of this project. I already know the project's name,
its module names, its store topology, its process vocabulary (packets, findings-numbering,
cold audits, contract-adversary), and a live in-progress work item ("04b" / surreal-unification
/ possibly "11i-b"). If the target document uses any of the terms named above without defining
them, I am **not capable of reporting genuine non-resolution for those specific terms** — I
will flag any point where recognition might be leaking from this ambient context rather than
from the document, per your instruction, but you should treat my read on **project-specific
vocabulary** as compromised from the outset, and weight my findings on **document structure,
completeness, and self-containedness of NON-lore-specific claims** as the trustworthy signal
instead.

### 0.1 — The one absence that would make me reject the document

If the document does not **state, explicitly and up front, what specific claim or question the
evidence is meant to establish** (what is being proven, disproven, or decided), I cannot use it
— no quantity of data, logs, or artifacts is evaluable without knowing what they are supposed to
demonstrate.

### 0.2 — Expectations for a usable stranger-facing technical evidence package

1. An explicit statement of the claim/hypothesis/decision the evidence supports (see 0.1).
2. Definitions of domain-specific terms, acronyms, and internal jargon on first use — a
   glossary or inline definitions, not an assumption of shared history.
3. Enough background on the system/component under discussion that its purpose and shape are
   comprehensible without prior exposure to the codebase.
4. A stated methodology: how the evidence was produced (measured, tested, derived, simulated)
   and under what conditions, so a stranger can judge its validity rather than just its
   conclusion.
5. Primary data or reproducible artifacts alongside any summary — a stranger should be able to
   check the author's interpretation against the underlying evidence, not just trust the
   summary.
6. A clear separation between "what was observed" and "what the author concludes it means."
7. Scope/version/environment metadata: what system state, date, configuration, or build this
   evidence pertains to, and what it does NOT cover.
8. Attribution: who produced this evidence and who the intended reader/actor is, so I can judge
   whose standard of rigor and whose blind spots I'm reading.
9. Internal consistency — terms and numbers used the same way throughout, with any revision or
   correction visibly marked as such rather than silently overwritten.
10. Working cross-references — any citation to another artifact, file, or prior finding should
    resolve to something a stranger could actually locate, not a dangling pointer.

---

## Document read

Directory read (and ONLY this directory — no parent, no sibling, nothing else in the repo):
`/home/ejprice/PycharmProjects/lore-pkt11i-b/consult-11ib/honest/`. Contents: `00-README.md`,
`01-summary.md`, `02-per-group-distributions.md`, `03-anchor-rates.md`, `04-probe-texts.md`,
`05-adopted-row-provenance.md`, `06-per-hit-decomposition.md`,
`07-determinism-and-run-receipt.md`, `08-drop-diagnostics.md`, `per-query-rows.jsonl`. Read
00–08 in full. Read `per-query-rows.jsonl` lines 1–12 of 26 (banner + human-prose's 4 rows +
human-implementation-vocabulary's 4 rows + synthesized-identifier's first 3 rows) before a tool
truncation notice; did not page further (see Part 2).

Per the brief: the document is a SYNTHETIC EXHIBIT — every value a deliberately-implausible
sentinel. No value below is quoted as a real measurement; figures are quoted only to answer the
questions asked, exactly as this run's own convention (`00`, "How the sentinel values are built")
says they should be read.

---

## Part 5 — Legibility

### 5.A — Terms I could NOT resolve from the document itself

| term / identifier | where it appears | what I assumed, if anything |
|---|---|---|
| `L1` (as in "L1 R-PACKAGE gate population") | `07`, leg B condition (ii) | Unresolved. `R-PACKAGE` itself is glossed in `00`; the `L1` prefix on it is not. I assumed nothing — treated it as an unexplained qualifier on a term I do otherwise understand. |
| `R-C` (ruling behind the `batch` column) | `05`, "What this row does NOT carry" table | Unresolved. Not in `00`'s glossary (which lists R2, R2.5, R3, R-G, R-PACKAGE but not R-C). No assumption made. |
| `decision 5` | `05`, same table, governing the axis columns | Unresolved — appears once, uncross-referenced anywhere else in the package. |
| `bca` (the `method` value) | `05`, "What this row does NOT carry" table | Not defined in-document. I privately suspect this abbreviates the "bias-corrected and accelerated" bootstrap CI method — but that recognition is general statistics background, not something the document told me (see 5.B). |
| "continuous-statistic sibling" (of the persisted capture set) | `07`, Leg A "Held fixed" | Genuinely opaque to me. I could not form even a working guess of what a statistic being a "sibling" of a discrete one means here. |
| "settled-index start/end checks" | `07`, Leg B pre-conditions table | Unresolved — I inferred only that it's some kind of precondition check on the corpus/index state, from the word "settled," but the document never defines what makes an index settled or what the start/end checks verify. |
| `head_retained_overlap`, `catch_bar_unmet`, `stability_gate_unmet` (3 of the 5 `FLOOR_NON_ADOPTION_CAUSES`) | `05` | Named but not explained. The document explains the other two values in the same enum (`substrate_indiscriminate`, `interval_degenerate`) in detail, which makes the silence on these three more conspicuous, not less. No assumption made about their meaning beyond what the name suggests. |
| `ci_modal_mass`, `floor_rank`, `floor_tail_depth` (three of the F7.2 "degeneracy telemetry" fields) | `05` | Named with sentinel values but not explained. I assumed `floor_rank`/`floor_tail_depth` relate to the selected floor's position among candidate values on "the ladder," and `ci_modal_mass` to some concentration measure of that candidate distribution — but this is a guess from the field names, not a document-given definition. |
| "the ladder" (`choose_cosine_floor`'s candidate sequence) | `01`, `02`(indirectly), `07` | Used repeatedly ("chosen off the pooled ladder," "ladder `(N, ci_width, agreement)` triples") but never formally defined. I inferred it means the swept sequence of candidate floor values evaluated during selection — never stated as such. |
| `N` vs `n` vs `B` | `07` ("ladder `(N, ci_width, agreement)`" and D1's "floor point, interval, N, B, method"), `05` (`n_resamples (B)` = 2345), `02`/`03` (lowercase `n` = group size) | I cannot tell whether uppercase `N` in the ladder/D1 tuples is the same quantity as lowercase `n` (group/query count) used everywhere else, or a third distinct count. The document uses three symbols (`N`, `n`, `B`) that all smell like "a count of something" and never states how they relate. |
| `max_cosine` vs `response_best_cosine` | predicate in `01`/`03` uses `max_cosine`; every table/row/field elsewhere says `response_best_cosine` | I assumed these name the same quantity (confirmed self-consistent when I checked Part 1 Q8's row), but the document never explicitly equates the two names. |
| `TEI endpoint identity` | `07`, provenance receipt | Not defined in-document. I recognize "TEI" as very likely "Text Embeddings Inference" from general ML-infrastructure background — flagged in 5.B, not treated as document-given. |
| "FastMCP," "streamable-HTTP composition," "lifespan" (in the human-question text, `04` Pair 2) | `04` — explicitly a question I was told **not to answer** | Not resolved and not attempted, per instruction. Noting only that these terms exist in the exhibited text. |

### 5.B — Places I caught myself understanding something the document never defined, and where I think that understanding came from

This is the part you specifically asked me to be honest about, and there's more of it than I'd
like:

1. **`B4`'s gloss itself** ("the hot-row mint rule: the head row is contended on and advanced
   under one retry driver; also the additive-column (`OVERWRITE`) escape valve," `00`) reads to
   me as fully sensible — but that's because my auto-loaded project instructions already contain
   an extensive law about "hot-row mint," `retry_on_conflict`, and `OVERWRITE` as a SurrealDB DDL
   migration verb (versus `IF NOT EXISTS`/`ALTER`). A reader without that law would see "hot-row
   mint" and "OVERWRITE" as opaque capitalized jargon with no operational content. I did not
   notice this gap on first pass; I only found it by deliberately asking myself, per your
   instruction, "did I just understand that, or did I bring it?"
2. **`retry_on_conflict`** appears three times across the package (as a probe text in
   `per-query-rows.jsonl`'s "human-implementation-vocabulary" query, and as a cost-accounting
   field in `07`, "`retry_on_conflict` attempts: 12"). I know this name's entire governance
   history (a shared retry seam, a documented jitter-bug class, a mutation-proof requirement)
   from ambient context, not from this document, which never explains what the function does —
   it only ever appears as a bare identifier or a probe string.
3. **The `chunk:...` and `floor_measurement:...` id shapes** (e.g.
   `chunk:synthetic_human_prose_0_01`, `floor_measurement:synthetic0000000001`) read to me
   immediately as database record identifiers in a `table:id` form. That recognition comes from
   my auto-loaded project law discussing this exact record-id shape for a specific database
   product — the document itself never names that database or explains the `table:id` syntax.
4. **`surreal_schema.py`** (cited in `05` as the shipped schema file) — I read "shipped schema"
   and immediately pictured a specific database engine's schema-definition file, again from
   ambient project knowledge, not from anything the document explains.
5. **The whole subject-matter recognition**: I recognized this exhibit as describing a
   retrieval-floor/absence-verdict gate for a code-search RAG belonging to a project I already
   know a great deal about by name (`loremaster`, cited repeatedly as a module path in `04`/`05`)
   — including its module layout, its embedding backend, its store technology, and years of its
   own incident history. `00`'s own README states an explicit goal — "glossed here so this
   package is readable without 11-i-b's context" — i.e., the authors intended this package to
   stand alone for a reader who does NOT have that context. I am not that reader. I cannot
   evaluate whether the package actually achieves standalone legibility for its intended
   audience, because I was never in the position that audience is in.
6. **`11-i-b` itself** — the document names this packet identifier once (`00`, "readable without
   11-i-b's context"). I recognized it instantly, but only because my report path
   (`lore-pkt11i-b/`), my own agent id (`informant-cold-11ib`), and the sibling directory
   (`consult-11ib/`) already told me this packet's name before I opened anything. This is a clean
   example of a term that IS technically defined-by-context in the document (it's clearly "this
   packet") but where I cannot claim first-encounter unfamiliarity, because I wasn't unfamiliar
   with it.
7. **`bca`, `TEI`** (listed in 5.A) — flagged there as general-background recognitions, not
   document-derived, and not project-specific contamination (more likely general statistics/ML
   training-data knowledge) — included here for completeness since you asked me to name the
   *source* of any leaked understanding, and for these two the honest source is "general
   background knowledge," not the ambient lore-project contamination named in Part 0.0.

---

## Part 1 — Retrieval

**1. Did the portable instrument pass its pre-registered acceptance? Name the two acceptance legs and their values.**
Yes — both legs PASS. From `01`, "Pre-registered acceptance — both legs, with their values":
leg (1) is "`F_portable` false-fire rate against the legacy labeled real union," bar ≤5%
(`0.05`), measured `11 / 357` = `0.030812`, verdict PASS. Leg (2) is "legacy nonsense catch at
`F_portable`," bar ≥60% (`0.60`), measured `321 / 345` = `0.930435`, verdict PASS. `01`'s own
line: "Both legs pass ⇒ the portable instrument is ACCEPTED as built."

**2. Is the legacy↔portable divergence a scalar offset or a distribution-shape difference? Cite the line.**
Distribution-shape difference, not a scalar offset. `02`, "Cross-group view" section: "the
paired difference from legacy to portable is not a constant. It differs across percentiles
WITHIN a group..., it differs across groups at the same percentile..., it **changes sign** in
`legacy-nonsense` above the median, and the p5–p95 width changes by a different amount in every
group.... This is a distribution-shape difference, not an offset."

**3. Which determinism leg held, and what does that commit the downstream scheduler to?**
`determinism_leg = within_ci_by_construction` (`07`). This is explicitly the middle of three
permitted values (`bit_identical_cold`, `bit_identical_via_cache`, `within_ci_by_construction`)
— the two runs' derived payloads are NOT byte-equal, but pass the two required agreement
conditions. Per `07`, "What this verdict commits 11-ii to": (1) change detection must key on
`corpus_content_digest` equality alone, and nothing else; (2) any logic in 11-ii that infers
"nothing changed" by comparing a fresh floor to the adopted floor is invalid, since floors
differ run-to-run even with nothing changed; (3) treating a re-measured floor's difference from
the adopted one as drift evidence is likewise invalid — only the F2-calibrated gap distinguishes
noise from a real move; (4) the stricter `bit_identical_cold` outcome, which would license a
stricter scheduler, was **not** obtained here.

**4. What was the self-retrieval drop rate, split by cause?**
From `08`, total **`45 / 456` = `0.098684`** (against a ≤20% gate — PASS), split:
`source_chunk_absent_from_kprime` 23 (`0.050439`), `sibling_chunk_same_file_only` 12
(`0.026316`), `holdout_file_exclusion_applied` 10 (`0.021930`). `23+12+10 = 45`.

**5. What fraction of live production queries would fire the absence verdict under the portable floor?**
The document does not support this, and says so explicitly, twice. `01`: "nothing in this
package supports a statement about what fraction of live queries would fire the absence verdict.
Packet 35 is the instrument that would measure that; it has not run." `06`, bound (i): "This
package cannot tell you what fraction of live production queries would fire the absence verdict
... Packet 35 ... has not run." I know this is unanswerable because the document affirmatively
refuses the question rather than being merely silent on it.

**6. By how much did retrieval quality improve when the portable instrument replaced the legacy one? Give the figure and cite the line that supports it.**
No figure in this document answers this question, and the document goes out of its way to
prevent one being manufactured. The only candidate number is `01`'s headline scalar
`F_portable − F_legacy = 0.111111`, but the same line continues: "⚠ That scalar is DIMENSIONLESS
and it is not a quality delta.... It may not be re-expressed as an improvement, a regression or
a percentage." `02`'s bound (iii) restates this independently: "No `Δ` here may be re-expressed
as an improvement, a regression, a quality delta, or a percentage of anything. Measuring quality
across instruments needs a shared human-judged relevance set; this run has none." So: `0.111111`
is the number a careless reader would reach for, and the document blocks that reading twice, in
two different files.

**7. Was the portable floor's acceptance evaluated on data held out from the floor's selection? Cite the line.**
No. `01`, bound (iv): "the acceptance was NOT evaluated on held-out data.... No leg of this
acceptance is independent of the selection population." (`legacy-nonsense` is one of the six
groups `F_portable` was selected over; the legacy labeled real union is the union of two more of
those same six.)

**8. Open `per-query-rows.jsonl`. First row with `absence_verdict_fired: true` — its rank-1 hit's cosine, how many captured hits are `shown`, and consistency check.**
First such row (4th data row, `query_id: q_human_prose_3`, group `human-prose`, query text
"which module owns the chunk model the indexer consumes"): rank-1 hit is
`chunk:synthetic_human_prose_3_01`, `vector_cosine: 0.333333`. Ten hits are marked
`"shown": true` (ranks 1–10); ranks 11–30 are `"shown": false`. Consistency: the rank-1 cosine
(`0.333333`) equals the row's own `response_best_cosine` (`0.333333`) — consistent with
"response-best" meaning the maximum/rank-1 cosine. Ten shown hits is consistent with `00`'s
`SURVEY_K = 10` and `06`'s "shown slice: `SURVEY_K = 10`." And the verdict itself is consistent
with `03`'s stated predicate (`00`/`03`: "`max_cosine < floor AND NOT has_verbatim_anchor`"):
`0.333333 < F_portable (0.456789)` and `has_verbatim_anchor: false` ⇒ fires. All three checks
line up.

**9. Do the below-floor-per-group artifact and the acceptance-rate artifact reconcile with each other, the survivor count, and the adopted row? Show the arithmetic.**
The two artifacts are `01` (acceptance legs, computed over the legacy labeled real union and the
legacy-nonsense set) and `03` (below-floor slice per all six groups at `F_portable`).
- **Human groups, `03` vs `01`:** `03`'s `human-prose` row at `F_portable` is (below-floor 12,
  anchored 8, fired 4); `human-implementation-vocabulary` is (11, 4, 7). Summed: below-floor
  `12+11=23`, anchored `8+4=12`, fired `4+7=11` — exactly `01`'s "legacy labeled real union" row
  (below floor 23, anchored 12, false fires 11, rate `11/357=0.030812`). `03` asserts this
  correspondence itself in its own text.
- **`legacy-nonsense`, `03` vs `01`:** `03`'s row is (324, 3, 321); `01`'s nonsense-set row is
  identical (324, 3, 321, catch `321/345=0.930435`). Match.
- **`03`'s own internal arithmetic:** grand total row (815, 39, 776) = sum of all six groups'
  rows: below-floor `12+11+0+12+456+324=815` ✓; anchored `8+4+0+6+18+3=39` ✓; fired
  `4+7+0+6+438+321=776` ✓; and `815=39+776` per row-by-row (below-floor = anchored + fired in
  every row). Internally consistent.
- **The survivor count**: `03` states `verdict_not_fired_queries = 1740 − 776 = 964`, which is
  exactly the population `06` opens with ("`verdict_not_fired_queries` ... **964** of 1740 — see
  `03`"), and `00`'s population table names this same 964 as the third, distinct population.
  `06`'s own best-hit-below-floor count (39) is asserted by `06` to be the identical 39 queries
  as `03`'s total anchored count (39=39) — I can confirm the **counts** match; I cannot, from a
  24-row sample of 1740 queries, independently confirm they are the same 39 *queries* rather than
  a coincidental equal count. That identity claim rests on the document's own assertion, not on
  data I can re-derive.
- **The adopted row (`05`):** `floor=0.456789`, `ci_low=0.404040`, `ci_high=0.505050` — these
  reconcile exactly with `F_portable`'s values throughout `01`/`03`/`06`. But `adopted_n = 411`
  does **not** reconcile with any of `357`, `345`, `815`, `776`, or `964` above, and must not:
  `411` is `answered_probes` (`08`: `456 − 45`), a *probe*-based population, while every number
  in `01`/`03`/`06` above is *query*-based. `00`'s own table names all three populations
  precisely to prevent this exact cross-wiring. So the correct answer is: the **threshold
  values** reconcile across all four artifacts; the **counts** reconcile within each population
  but must not be compared across the query/probe boundary — which is the trap this question is
  testing, and which the document pre-emptively names.

---

## Part 2 — Behaviour

**OBSERVED** — artifacts opened: all of `00`–`08` (nine markdown files), read fully, top to
bottom, in one pass each (each is short enough — under 100 lines — that "fully" and "in one
pass" are the same thing here; I did not skim any of them). `per-query-rows.jsonl`: read lines
1–12 of 26 (the banner line, all 4 `human-prose` rows, all 4 `human-implementation-vocabulary`
rows, and the first 3 of `synthesized-identifier`'s 4 rows) before the tool cut the read off
with a truncation notice. I did **not** page further into the file — I had already found the
row Part 1 Q8 needed (line 5, the 4th data row) inside the portion returned, so continuing to
read the remaining ~14 lines (the rest of `synthesized-identifier`, all of
`self-supervised-answered`, `hold-out-absent`, and `legacy-nonsense`'s sample rows) was not
necessary for any question asked so far. **BELIEVED**: I believe (but did not verify by reading
them) that those unread rows follow the same schema and are drawn consistently with the rates
reported in `02`/`03`/`06`, because `02` states the file is "a deterministic four-per-group
sample" and I have no reason from what I did read to doubt that. That belief is unverified.

The single most useful line: `00`'s "`411 = 456 − 45` (the drops, `08`). `964 = 1740 − 776` (the
fires, `03`). The three are not interchangeable in any direction." Every reconciliation I did in
Part 1 Q9, and every "which denominator" trap in Parts 1/3, resolves against this one sentence —
it is the single line that let me catch the `adopted_n`-vs-query-count mismatch rather than
wrongly declaring a reconciliation failure.

What I would delete from the summary (`01`): its closing paragraph — "Both acceptance rates are
properties of the survey's labeled sets. Neither is an estimate of how often the absence verdict
would fire in production — that population was not sampled here (packet 35)." This says nothing
that the "Measured population" note at the top of the same document hasn't already said. It's
the one place in an otherwise tightly-written package where a caveat is stated twice in the same
file with no new content the second time.

---

## Part 3 — The audit question

Revisiting my Part 0.2 list against what I actually found:

| 0.2 item | present? | where |
|---|---|---|
| 1. Stated claim/hypothesis | **Reconstructable, not stated as one sentence.** The closest thing is `01`'s verdict line ("Both legs pass ⇒ the portable instrument is ACCEPTED as built") and `00`'s contents framing — but nowhere does the package open with an explicit "this package establishes whether X." I had to infer the governing question (can the portable instrument safely replace the legacy one?) from the shape of the acceptance section. |
| 2. Definitions of jargon | **Present, incomplete.** `00`'s glossary table covers most packet-internal references. Gaps: see Part 5.A (`L1`, `R-C`, `decision 5`, `bca`, three non-adoption causes, `N`/`n`/`B`, "the ladder," "continuous-statistic sibling," "settled-index"). |
| 3. System/component background | **Thin, scattered, no dedicated section.** I had to reconstruct "this is a retrieval-floor/absence-verdict gate for a code-search corpus" from mentions across `00`, `01`, `04`, `05` rather than from any one background paragraph. |
| 4. Methodology | **Present, and deliberately distributed** — `00` states outright there is no bounds/methods appendix, each claim carries its own method beside it (`01`'s selection receipts, `08`'s drop diagnostics, `07`'s determinism legs, `06`'s "zero extra embeds, zero extra searches" aggregation note). |
| 5. Primary/reproducible data | **Present, but a sample.** `per-query-rows.jsonl` is explicitly a 24-row deterministic sample of 1740, and `02` warns its per-group counts "do not reproduce the group rates... they are consistent with them, not equal to them." |
| 6. Observation vs. interpretation | **Present, and the strongest thing in the package.** The `⚠`/"bound" callouts throughout (`01`, `02`, `06`) are the clearest, most consistent separation of "what was measured" from "what it may NOT be read as" I named as a baseline expectation in 0.2. |
| 7. Scope/version/environment metadata | **Present**, concentrated in `07`'s provenance receipt (file path, store URL, namespace, database, version, image digest, git commit/dirty, endpoint identity, library versions). |
| 8. Attribution | **ABSENT.** No author, team, or reviewer is named anywhere in `00`–`08`. No "prepared by" / "reviewed by" line exists. |
| 9. Internal consistency | **Present, and actively engineered** — `00`'s population-disambiguation table exists for exactly this purpose, and every cross-document arithmetic check I ran in Part 1 Q9 came out consistent. No revision history or changelog is present, but I also saw no evidence of a revision the document needed to disclose. |
| 10. Resolvable cross-references | **Present within the package** (every `00`→`01..08` pointer I followed resolved to a real file I could open). **Named but unverifiable outside the package** — citations to `loremaster/loremaster/store/surreal_schema.py`, `loremaster/evaluation.xml`, and the `floor_calibration` module tree are specific and plausible, but I was barred from opening anything outside this directory, so I cannot confirm they exist as described. That is a property of my instructions for this consult, not necessarily a flaw in the document. |

**Data I needed that the document does not carry** (including things I only realized I needed
while working the questions above):

- **The legacy instrument's `embedding_schema_fingerprint`.** The document flags this gap
  itself (`05`'s last table row) and correctly identifies it as consequential: without it,
  bound (iii)'s "cannot be checked for coincidence" can never be upgraded to "coincide" or "do
  not coincide" by any future reader.
- **A held-out acceptance leg.** Also self-flagged (`01`, bound iv) — both acceptance legs are
  evaluated on the same population the floor was selected over.
- **Authorship/attribution.** Not self-flagged; I noticed its absence only by checking item 8
  against my own pre-registered list.
- **Formal definitions** for `L1`, `R-C`, `decision 5`, "continuous-statistic sibling,"
  "settled-index," the three unexplained `FLOOR_NON_ADOPTION_CAUSES` values, and a disambiguation
  of `N`/`n`/`B` and "the ladder" — none self-flagged; all found only by trying to use every term
  the document introduced.
- **One thing I only discovered I needed while doing Part 1 Q9**: a single document-wide
  statement that `01`'s acceptance tables and `03`'s six-group table are computed over the
  identical below-floor predicate on the identical rows. `03` states this correspondence for the
  two human groups specifically, in its own prose — but nothing states it as a general property
  of the package, so I had to re-derive the cross-document arithmetic by hand rather than being
  told once, in one place, and trusting it everywhere. A single sentence doing for the
  query-based tables what `00`'s population table does for query-vs-probe populations would have
  replaced that derivation.

---

**Standing by.** Parts 5, 1, 2, 3 complete. Awaiting Part 4.

---

## Part 4 — the contract task and verdict

*Per the brief: every number below is treated as a real measurement. I am writing the input
contract for the downstream consumer this package names — `11-ii`, "wires this measurement to
a scheduler and a served surface" — specifically the "exact-skip scheduler" `07` discusses at
length.*

### The three-datum contract

**Datum 1 — the adopted floor and its state.**
- **(a)** `floor = 0.456789`, `state = measured` (the row is *adopted*, not merely computed).
- **(b)** `05`, "The adopted `floor_measurement` row" table, columns 3 (`state`) and 6
  (`floor`); cross-confirmed by `01`'s "The two floors" table (`F_portable` row) and `01`'s
  "Outcome" line ("State `measured`; the head was adopted").
- **(c)** Bound: this value is meaningful only inside the **portable** instrument's embedding
  geometry (`02`, bound iii) — it is not commensurable with any cosine from a different
  instrument or schema, and the row's `embedding_schema_fingerprint` (`05`, col 12) is the only
  check available for a schema match; my scheduler must refuse to apply this floor to any batch
  whose fingerprint doesn't match. Further bounded by `01`, bound (iv): acceptance was evaluated
  on the same population the floor was selected over, so a PASS here is not evidence the floor
  generalizes past the six survey groups' shape, and (`06`, bound i) it is never a live-traffic
  estimate.

**Datum 2 — `corpus_content_digest`.**
- **(a)** the digest value (`05`, col 11; repeated in `07`).
- **(b)** `05`, column 11 of the adopted row; `07`, Leg B pre-conditions table and the
  provenance-receipt table.
- **(c)** Bound: `07`, "What this verdict commits 11-ii to," item 1 — "Change detection must key
  on `corpus_content_digest` equality ... and on nothing else. Digest equal ⇔ zero chunks added,
  removed or edited ⇔ skip." Items 2–3 of the same list explicitly forbid substituting a
  floor-value comparison for this digest check.

**Datum 3 — `determinism_leg`.**
- **(a)** `within_ci_by_construction` (one of three closed enum values).
- **(b)** `07`, "The verdict — typed, from the closed three-value enum" section, with its
  supporting gate table (conditions i/ii, both PASS).
- **(c)** Bound: `07`, "What this verdict commits 11-ii to," item 4 — this specific value (not
  `bit_identical_cold`) means my scheduler may **not** rest on byte-reproduction of a
  measurement; it must tolerate `|Δfloor|` up to the F2-calibrated gap (`0.010101`) as
  noise-consistent-with-no-change, gated by the ≥0.98 decision-agreement check — never by exact
  equality.

### Unfillable slots — ROUTE_AROUND reasons, named before any verdict

1. **`trigger`'s vocabulary is explicitly unclosed.** `05`: "`trigger` is an open
   `option<string>` today: nothing in the schema closes its vocabulary." My contract cannot
   branch on trigger value (e.g. "scheduled" vs "manual" vs "corpus-triggered") — there is no
   closed set to switch on, only free text.
2. **No per-state behavior is specified for 7 of the 8 `FLOOR_STATES`.** The closed enum is
   given (`05`) but only the `measured` path and the `measurement_failed` determinism-context are
   ever discussed. My contract can consume a `measured` row; it cannot be completed for
   `insufficient_corpus`, `invalidated_remeasuring`, `disabled`, etc. from this document alone.
3. **`L1`'s general population definition is missing.** Only an instance-value is given
   ("this run: all 1740 queries," `07`). My contract can hard-code *today's* population; it has
   no formula for computing a future run's `L1` population if the group shape ever changes.
4. **The F2 null-rate/applied-gap derivation procedure is not given** — only this run's outputs
   (`0.020202` / `0.010101`, `05`) are shown. I can hard-code this run's gap; I cannot recompute
   a fresh one for a future run.
5. **The legacy instrument's `embedding_schema_fingerprint` does not exist and cannot be
   recovered retroactively** (`05`'s own note). Any contract slot requiring cross-instrument
   comparison is permanently unfillable from this document, not merely unfilled.
6. **"The ladder"** (`choose_cosine_floor`'s candidate sweep) is never formally specified. I can
   consume its *output* (the selected floor); I cannot re-implement, audit, or independently
   re-verify the selection procedure — including the safety claim bound (iv) rests on ("chosen
   off the pooled ladder across all six groups... no single group's statistic was optimised").

### Verdict

**CALL_AGAIN**, scoped to exactly the three-datum contract above — all three data are present,
addressed to an exact location, and bounded clearly enough by the document's own text to encode
as guard clauses rather than assumptions.

**ROUTE_AROUND**, narrowly, for anything the contract above does not cover: cross-instrument
fingerprint comparison (impossible, not just absent), branching on `trigger`, handling any state
other than `measured`, recomputing a future F2 gap, or independently auditing the ladder-based
selection safety argument. For those, this document is not a sufficient evidence base — either a
schema/process change (close `trigger`'s vocabulary, start capturing the legacy fingerprint,
formally define `L1` and "the ladder") or a fresh run/design decision is required.

**Was my Part 0.1 trigger hit? No.** 0.1's criterion was the *absence* of a resolvable
claim/question the evidence answers. This package's governing claim — does the portable
instrument clear its pre-registered bars and become the adopted floor — is not stated as one
upfront sentence, but it is confidently reconstructable from `01`'s acceptance section and
outcome line. Reconstructable-with-effort is not absent. My 0.1 line was written to catch total
silence on what's being proven, not an implicit-but-locatable claim, so it does not fire here.

**Inline flag on this section itself:** I do not believe I filled any of the three chosen data
or their bounds from ambient recognition rather than the document — all six citations above
point at text I actually read in this consult. The one place contamination *might* be doing
quiet work is in how natural E5's demand (a typed enum, never the bare word "deterministic") felt
to me — I recognized that shape of rule from my own auto-loaded project law before I ever reached
`07`. But `07` itself re-derives the justification in full (showing byte-inequality, then
explaining why an unqualified "deterministic" claim would license the wrong scheduler design), so
that recognition did not stand in for the document's own argument here — it just meant the
argument's conclusion felt unsurprising rather than novel when I reached it.

### Q1 — delete a third to save context budget

**Goes:** most of `02`'s full per-percentile spread (min/p5/p25/median/p75/p95/max/mean, all six
groups, both instruments) — the "Cross-group view" table and its shape-vs-offset conclusion
already carry the load-bearing finding; the underlying per-percentile numbers are the most
compressible material in the package because losing them doesn't change what a reader can
conclude. Same treatment for most of `05`'s 18-row "What this row does NOT carry" table — keep
the rows that are actually consequential (the legacy-fingerprint gap, `n_resamples`/`method` for
reproducibility, the anchored-excluded count used elsewhere) and cut the rest, which are
sentinel filler that no downstream claim depends on.

**Must never go:** the bound callouts (i–iv, wherever they sit — `01`, `02`, `06`) — they are
the only thing standing between a number and its misreading as a quality delta, a live-traffic
estimate, or a held-out validation. `00`'s three-populations disambiguation table — without it
the Part 1 Q9 reconciliation is not just harder, it's wrong (a reader WILL cross-wire
`adopted_n` against a query count). And `07`'s "what this verdict commits 11-ii to" bullets —
that prose is the direct, load-bearing input to the contract I just wrote in this Part; without
it Datum 3's bound doesn't exist anywhere in the package.

### Q2 — the single unresolved item that would most change usability

**"The ladder."** Not attribution, and not `L1` (whose immediate ambiguity mostly resolves
itself here via the parenthetical "this run: all 1740 queries" — I can read today's PASS/FAIL
correctly even without the general rule). Attribution matters for governance and escalation, not
for interpreting any single number in front of me. But "the ladder" sits underneath the *one*
safety argument the whole acceptance section depends on — bound (iv)'s defense that "no single
group's statistic was optimised... `F_portable` was chosen off the pooled ladder across all six
groups" is exactly the sentence that tells me the acceptance PASS/PASS isn't circular. I cannot
independently verify that defense without knowing what the ladder sweep actually does — what
values it tries, in what order, pooled how. Every other gap I found is either self-resolving in
context (`L1`) or governance-adjacent (attribution) rather than sitting inside the one argument
that makes the central verdict trustworthy rather than merely self-reported.

---

**Standing by.** Part 4 complete.
