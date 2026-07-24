# REPORT-design-blind-11i — independent blind review of the ruled floor-calibration design

brief-base v6 read

- **state:** done
- **deviations:** none. The two withheld files (`REPORT-fable-design-11i.md`, `REPORT-scout-11i.md`) were
  NOT opened by me or by either delegated verifier; both verifiers were briefed with an explicit
  prohibition and both affirmed compliance unprompted.
- **decisions-needed:** 25 (§7). Six of them block a builder on day one (§7.0). Three are amendments to
  RULED text, not blanks (§5 C1/C3, §6.P1) — they need a short addendum, not a Q&A.
- **VERDICT: SOUND-BUT-UNDER-SPECIFIED** (§8). Confidence high on the checklist, medium on the one
  statistical risk that could escalate it (§6.S1).
- **receipt pointers:** false assertions §4 · design-vs-design contradictions §5 · statistical residuals §6 ·
  the 25-item contract-freeze checklist §7 · out-of-brief items raised under scope law §9.
- All measurements and source reads in this report are dated **2026-07-24**, against worktree
  `/home/ejprice/PycharmProjects/lore-pkt11i` at `7671f6f` (base `d0ee2be`). Nothing here is "current"
  in any later sense.

---

## 1. What I read, and what I did not

Read in full: `~/.claude/orchestration/brief-base.md` (v6) · repo `CLAUDE.md` (incl. THE CONSUMER LAW +
THE TRUST DOCTRINE) · `docs/design/2026-07-24-floor-calibration.md` R1–R8 + Addenda A/B/C/D/E, all 1176
lines · `docs/plans/v2/11-i-floor-calibration-dark-machinery.md` · `docs/reference/surrealdb-31-capabilities.md`
(via a delegated section-exact read; §1.1/§1.3/§1.5/§2/§3/§5 quoted back to me verbatim).

Source read directly by me: `loremaster/loremaster/search.py` (the cosine-floor block, `CosineFloorMeasurement`,
`_cosine_floor_drift_note`, `apply_cosine_floor_drift_check`, `_cosine_absence_verdict`,
`SearchPipeline._to_result`) · `scripts/search_score_survey.py` (module docstring, `choose_cosine_floor`,
`VerdictSample`, `sample_identifier_queries`, `survey`, `_default_output_dir`) ·
`loremaster/loremaster/store/surreal_schema.py::_CHUNK_FIELD_SPECS` · `loremaster/loremaster/store/surreal.py::SurrealStore.scroll`
· `loremaster/loremaster/index/records.py::point_id` · `Containerfile` · `loremaster/loremaster/config.py`
(model inventory).

Delegated (two read-only verifiers, results spot-checked by me where load-bearing): the caller-set /
seam / dependency questions in §4 and §7, and the plan/law/reference document questions.

**Tool honesty (brief-base §4):** I used `lore_get_symbol` for `point_id` and `lore_index` for the
freshness/branch check; **everything else was grep/Read.** That is a deliberate fallback and I am saying
so: (a) the graph indexes the MAIN checkout at `d0ee2be`, and my questions were mostly *non-symbol textual
seams* (does a doc sentence match a field list; does a comment name a live method) and *exhaustiveness*
questions (is this the only caller; is there any embed wrapper) — the two of the three sanctioned
fallback cases; (b) `lore_index()` at 2026-07-24T17:23Z reported `last_sweep` age 547 s and the watched
root at `d0ee2be`, so the index was current for the unmodified files I asked about. I did not file a
friction row: no lore weakness was routed around, only a class of question the graph does not own.

Not run: the test suite (the tree carries ~394 inherited contract-RED failures, pinned at
`docs/plans/v2/receipts/2026-07-24-packet11i/BASELINE-RED.md`), `scripts/search_score_survey.py` (#177),
and anything touching a store.

---

## 2. The load-bearing question, answered

> Could a competent Opus builder implement packet 11-i from this design without making a materially
> consequential choice the design does not determine?

**No — decisively no.** Six choices block on day one, each one producing materially different code, and
none of them is settled by the design or the packet:

1. **How many probes does R2 run?** The packet says *fixed-N, "cost is O(probes), NEVER O(corpus)"*;
   D2 says *"R2 embeds the full derivable-text pool once."* On lore's 2959-file corpus these differ by
   three or four orders of magnitude in embeds and searches.
2. **What is `k′`?** Never stated, and load-bearing in three independent ways (§7.7).
3. **What is in the portable answered union?** Its composition silently sets the strictness of the
   pre-registered 5% false-fire bar (§7.9).
4. **How is the B≥1000 bootstrap actually computed?** Re-running `choose_cosine_floor` per resample —
   which the design mandates and ONE IMPLEMENTATION forbids cloning — is O(B·N²) with no numpy/scipy in
   the dependency closure (§7.13). Naive = does not finish.
5. **What is the ≥98% stability gate's denominator?** Three readings, materially different bars (§7.14).
6. **Which store does R2 read?** Lore's corpus exists only in production `:18500`; the packet's own
   entry check forbids `:18500` (§5 C9).

A builder who resolves any of these silently — and brief-base §2 is explicit that ambiguity resolves
itself invisibly — ships a defensible-looking artifact that answers a different question from the one
the design asked.

---

## 3. The good news, stated plainly and first

The **mechanisms are right**, and several are better than what they replace:

- Replacing a threshold with a *measurement* (D3: stale ≡ "a fresh measurement lands disjoint from the
  adopted interval") is the correct answer to the operator's "measured, not inherited" directive, and it
  genuinely subsumes the #74 class that churn was blind to.
- Making the floor an **interval** and letting one comparison govern adoption, per-tier upgrade and
  staleness (D6) is real consolidation, not repackaging.
- The **identity-keyed sampler** (D2) is correct in its choice of key: `point_id` is insertion-independent
  AND edit-surviving, which a content hash would not be. The self-caught correction preserved in D2
  (the phantom `embedding_text_sha512`) is the discipline working.
- **A1's fail-safe inversion** (unevaluated ⇒ disarmed) closes a real fail-open hole that I verified at
  source, and it was found by the design's own author reading their own §7 critically.
- The design **repeatedly names its own biases with direction** (§3's self-supervision optimism, the
  hold-out twin residual, D4's ruler-and-measurand honesty). That is rare and it is what made this
  review tractable.

Nothing below is a claim that the design is misconceived. It is a claim that it is not yet a work order.

---

## 4. False assertions found (a gap makes a builder ask; a false assertion makes a builder confidently do the wrong thing)

**FA1 — B3: "the churn cursor counts chunk re-embed commits at the ONE shared embed wrapper
(#169/11a already route every embed through it) — hook that seam, never a parallel counter." FALSE at
`7671f6f`.**
No such wrapper exists. Verified: at least three distinct embed-call paths — `Indexer._embed_records`
(the realtime chunk path), the batch path (`submit_batch_documents` / `submit_batch_document_chunks` /
`fetch_batch_results`), and `memory/local.py`'s own embedder instance. `loremaster/loremaster/embedding.py`
is a config→embedder *constructor* seam, not an embed-call wrapper. The single wrapper is FUTURE work:
`docs/design/2026-07-22-embedding-schema-reconciliation.md` describes it in the future tense, and
`docs/plans/v2/INDEX.md` lists both **11a and 11b as status `open`** (11b is the packet that would
deliver both #169's shared wrapper and #170's persisted per-chunk hash). The sentence is written in the
present tense about work that has not been built. It is partially defused by D0 retiring the churn leg —
but D3 still needs *some* "did at least one chunk change since the last measurement" signal, and B3 is
the only place the design says where such a signal comes from.

**FA2 — D2: "Every input is in the scrolled payload (`SurrealStore.scroll` is `SELECT * OMIT embedding` —
verified), so membership is computed at measurement time by calling the existing function." FALSE.**
`records.point_id`'s inputs are `(slug, tier, file_path, chunk_type, identity, sub_ordinal, key_version)`.
`surreal_schema._CHUNK_FIELD_SPECS` declares `tier, file_path, chunk_type, identity, sub_ordinal,
content_hash, mtime_ns, line_start, line_end, source_text, ident_text, llm_summary, metadata, embedding`
— **no `slug`, no `key_version`.** Two of seven inputs are absent from the payload.
The *goal* is reachable by a better route the design did not name: the row's **id IS the point_id**
(`SurrealStore.upsert` writes `{"id": record.point_id, …}`), so membership is a property of `row["id"]`
and needs no recomputation. But that route carries its own landmine, and the design does not warn about
it: `row["id"]` is a **`RecordID` object**, `str()` of a uuid-shaped RecordID yields
`chunk:⟨3f1b2c4a-…⟩` **with angle brackets** (established by live probe of the installed SDK), only
`.id` / `SurrealStore._bare_id` strips it correctly — and `_bare_id` is used only on the
`hybrid_search`/`_to_candidates` path, **never** from `scroll`. **No production `scroll` caller reads
`row["id"]` at all**, and `loremaster/tests/_surreal_fakes.py` documents in its own comment that it
**deliberately does not model the `id` key** on scroll rows. That is a textbook instance of this repo's
own law: the fixture guarantees the one condition under which the bug is invisible. `docs/reference/
surrealdb-31-capabilities.md` says only that "`str(RecordID)` round-trips"; the angle-bracket behaviour
for non-simple id components is documented nowhere in-tree.

**FA3 — D1: "Bootstrap costs ZERO embeds: it is arithmetic over already-captured cosines, so
interval-carrying is free at any N." Half-true, and the false half is the operative one.**
Zero embeds: true. **"Free at any N": false.** `choose_cosine_floor` scores every admissible candidate
floor against every union sample and every nonsense sample; candidate floors are the union's own
distinct observed values, so one invocation is O(U·(U+A)). Re-running it B≥1000 times per N-point, at
N up to pool size, is O(B·N²). And there is **no numpy and no scipy** anywhere in the dependency
closure (checked all four `pyproject.toml` files) and **no bootstrap/CI helper anywhere in the tree**
(the only in-tree "bootstrap" is `_txn.bootstrap_session`, the SurrealDB session DDL). A naive
implementation of the ruled instruction does not finish on a corpus-scale pool.

**FA4 — B2: "Per-run cost is CONSTANT-BOUNDED, not corpus-proportional … order tens of query embeds …
independent of corpus size." Superseded and never retracted.**
B2's guarantee rests explicitly on "Probe counts are fixed-N by design (R3 minimums)". D0 retires the
fixed-N minimums as the N rule and D2 replaces R2's probe count with "the full derivable-text pool".
D5 partially re-opens the cost question ("measured at R2") but never withdraws B2's constant-cost
claim, which was the entire answer to the operator's "often stale ⇒ thrash" concern.

**FA5 — packet `11-i…dark-machinery.md` Entry check: "`lore_findings` → #83, #87, #161, #179 open."
FALSE for three of four.** Queried the ledger 2026-07-24: **#83 acknowledged**, **#87 acknowledged**,
**#179 acknowledged**, #161 open. A builder running the entry check literally
(`lore_findings action=query status=open`) sees none of the three and must decide whether the entry
check has failed.

**FA6 — repo defect, not the design (raised under scope law).** The packet-10-d comment block in
`loremaster/loremaster/search.py` (above `_COSINE_WEAK_MATCH_FLOOR`) says the `None` value is read by
"the gates in `_cosine_absence_verdict` and `SearchPipeline._format_result` — both already read it".
**`SearchPipeline._format_result` does not exist.** The gate is `SearchPipeline._to_result`
(`_format_result` matches no `def` in `search.py`; the only similar name is the extension seam
`self._server.format_result`). This is a dead symbol name in prose, shipped by a wave that passed a
cold audit — precisely the class `CLAUDE.md`'s rename-sweep section exists to catch. The design's own
§1.2 and finding #179 both cite `_to_result` correctly, so the design is right and the code comment is
wrong.

---

## 5. Design-vs-design contradictions (five addenda in one day, each amending the last)

**C1 — the cost model, three-way.** B2 "constant-bounded, independent of corpus size" ↔ D2 "R2 embeds
the full derivable-text pool once" ↔ packet Scope IN "fixed-N stratified probes (cost is O(probes),
NEVER O(corpus))". This is the single most consequential open question in step 2, and the packet's
wording actively licenses a builder to *reject* D2.

**C2 — the head-pointer key.** B4: "plus **one minted head pointer per scope**." D6: "The engine's
served unit generalizes to **(statistic, point, CI, scope)** … A future per-hit floor is another
statistic with its OWN interval and its OWN disjointness-staleness … one more row." A head minted per
`scope` collides the moment a second statistic exists. The schema is 11-i's; the second statistic is
#180's likely fix. Deciding this after the table ships is a migration.

**C3 — the state set is specified against a model D3 deleted.** §7's closed set contains
`stale_remeasuring` = "*leg fired; run queued/in flight*", and B6-F4 rules the per-hit flag
"**LIVE-on-the-old-floor under churn staleness** until adoption swaps it". D0/D3 retire the churn leg
entirely and redefine staleness as a **post-measurement** verdict ("a fresh measurement lands disjoint
from the adopted interval"). Under D3 there is no such thing as churn staleness, and — except for leg 1
— you cannot be *stale* before you have measured. D3 nonetheless says "the F4/B6 per-hit dispositions
carry over unchanged", carrying forward a disposition whose second half is defined over a deleted
concept. (E1 has since darkened the per-hit flag outright, making that half doubly moot.) 11-i writes
the `state` field's domain, so this reaches the schema.

**C4 — `insufficient_corpus` lost its definition.** §7 defines it as "min samples unreachable"; R3
supplies the minima (≥30 answered / ≥15 identifier / ≥30 absent); **D0 retires "the fixed-N minimums as
the N rule"** and supplies no replacement trigger. The state survives; its predicate does not.

**C5 — the pre-registered acceptance denominator, stated twice, differently.** §3 and R2: F_portable's
false-fire "measured against the **legacy labeled real union**" (56 samples). C6(a): "F_portable's
false-fire measured against the **HUMAN-labeled union**" (35 prose + 6 implementation-vocabulary = 41;
the 15 identifier probes are corpus-synthesized, as C1 itself establishes). Same bar, two denominators.
It happens not to bite at the 2026-07-07 numbers (≤2 failures passes under both) but a pre-registered
bar with two stated denominators is not pre-registered.

**C6 — §7's caching instruction stands unmarked after A1 convicted it.** A1: "My own §7 as first
committed inherited a milder copy of the defect ('in-process cached, refreshed on status reads and
adoptions')." §7's text is unchanged. D8a *is* marked in place as superseded; §7 is not.

**C7 — the packet's DEPLOY flag vs. "in-container".** Packet header: **"DEPLOY: no (nothing served
changes)"**; Exit: "**No deploy** — prove the machinery with the lab-validation verb". Scope IN and
B7.5: "Portable runner, **in-container**" / "an **in-container** one-shot verb". Per `CLAUDE.md`'s
Deploy section the container **bakes** the code and the mount is read-only reference, so new code cannot
run in-container without an image build. There *is* a reading that reconciles them — the
`lore_deploy.py conform` precedent runs the baked suite in an **ephemeral** container from a
freshly-built image without recreating anything — but the design and packet never name it, and the
three readings (deploy lore-lore / ephemeral container / host run) differ in code, in blast radius,
and in whether a row is written to a production store.

**C8 — the packet has not been updated for Addendum D at all.** Its "Binding architecture" section
names the binding design as "**R1–R8 + Addenda A and B**". Its Scope IN describes step 2 in pre-D7
terms. It contains **no mention** of: the bootstrap interval, `B≥1000`, the N-noise curve, the ≥98%
stability gate, hash-stable sampling, the paired decomposition, per-run cost capture, or disjoint-CI —
i.e. **none of the six deliverables D7 explicitly assigns to 11-i step 2**. The only D-era content
present is the determinism pin, which arrived via E5. Meanwhile the C5 and E6 packet edits (F3's
re-framing as a client consult; E5's fallback sentence) *have* landed — so the packet was maintained
against Addenda C and E and skipped D. Its size is likewise stale: D7 says "**11-i grows ~0.20 →
~0.25–0.30**"; the packet header and the INDEX row both still say **0.20**.

**C9 — the entry check forbids the only store that holds the corpus R2 must measure.** Entry check:
"spike-surreal up (**:18000 — the TEST store. NEVER :18500, which is production**)". Scope IN: "Lab
validation on **lore's instance** … **This is also #161's overdue re-measure**". Lore's 2959-file corpus
lives in the production lore-surreal at `:18500` (confirmed by `lore_index()`, 2026-07-24: 2959 files
indexed, watched root `/workspace` @ `d0ee2be`); `:18000` holds per-test throwaway databases. Building
an equivalent corpus in `:18000` means a full ~3000-file embed run that appears in no packet's scope.

---

## 6. The pre-registered values: attackable? implementable?

| bar | stated precisely enough to ATTACK? | stated precisely enough to IMPLEMENT? |
|---|---|---|
| bootstrap `B ≥ 1000` | yes | yes as a number — **no** as a procedure (§7.13) |
| "central 90% interval" | yes | yes (percentile [p5, p95]) |
| **≥98% decision-agreement** (D2 stability gate) | **no — denominator unstated** | **no** |
| false-fire **≤ 5%** | yes for the legacy run; **no** for the portable one — union composition unfixed (§7.9) | no |
| catch **≥ 60%** | yes (legacy: /15; portable: /N hold-outs) | yes, once `k′` exists |
| self-retrieval drop **≤ 20%** | yes | needs `k′` and "retrieve its own *chunk*" vs *file* |
| `D1_MIN_MEDIAN_SPREAD = 0.05` | yes | **unclear whether the portable instrument evaluates it at all** |
| min samples 30/15/30 | — | **retired by D0, still cited by R3 and §7** |
| churn tolerance 10% | — | **retired by D0** |
| R8 p5↔p10 separation | — | **superseded by D6 (marked)** |

Four statistical residuals the contract-adversary should own, none of which the design names:

**S1 (the one that could escalate my verdict) — the floor is a TAIL order statistic, and the
nonparametric bootstrap is not consistent for extreme order statistics.** Receipt: the 2026-07-07
adoption recorded false-fire **1/56**, i.e. **exactly one** union sample sits strictly below the chosen
floor — the floor is approximately the 2nd-smallest order statistic of the union, and its value is one
real sample's own cosine (`search.py`'s stamp comment: "0.50649 is a REAL sample's own measured cosine
(the 'transitive ripple rollup for impact depth>1' probe)", which is indeed an entry in
`IMPLEMENTATION_VOCABULARY_QUERIES`). Bootstrapping a statistic that deep in the tail yields a lumpy —
possibly **degenerate** — interval. Both of D2/D3's pre-registered rules fail *silently* under a
degenerate CI: the ≥98% decision-agreement gate passes trivially at `ci_low == ci_high` and adopts the
**smallest N tried**; and D3's disjoint-CI adoption fires on *any* movement at all, so the claim that
"hysteresis falls out free" inverts into maximal flapping. This is exactly the "what wrong build would
this fixture still pass?" question, applied to a bar instead of a fixture.

**S2 — the self-retrieval drop gate is a selection filter, not just an instrument check.** R3 drops any
answered probe that fails to retrieve its own chunk in top-`k′`. That retains only *easy* probes, biasing
the answered distribution **upward** — the same direction as §3's honestly-named self-supervision
optimism, compounding it, and pushing the floor **up** toward more false absence verdicts. §3 names its
bias; R3 introduces a second one and names it only as a sanity check.

**S3 — the two arms fed to `choose_cosine_floor` are deterministically ordered and paired.** If both legs
come from one `k′` capture, the absent leg is a max over a strict subset of the answered leg's hits, so
`absent ≤ answered` **for every probe, always**. The legacy nonsense arm was an independent sample; the
portable arm is a paired, dominated one. Whether that is intended, and what it does to the meaning of the
5%/60% pair, is nowhere discussed.

**S4 — pool members are not iid.** lore indexes summary *and* source chunks per symbol, and many chunks
per file. A bootstrap that resamples chunks as if independent produces a CI that is **too narrow** — and
that CI is the gate on the 11-ii cutover.

**S5 — the one dataset that could dry-run S1–S4 no longer exists.** `search.py`'s own stamp comment
records the adoption run's artifacts at `scratchpad/survey_out_74w/search_score_survey_summary.md +
.jsonl`. Verified 2026-07-24: `scratchpad/survey_out_74w/` is **absent** from the main checkout. Per
`CLAUDE.md`/#154 a `scratchpad/` path is unrecoverable by construction. So the bootstrap's behaviour
cannot be pre-tested against the data that produced 0.50649, and R2 will be the first and only
observation. **That makes committing R2's per-query jsonl to a tracked path a hard requirement, not a
nicety** — C6(b) requires publishing it *to the consult*; nothing requires committing it.

---

## 7. Contract-freeze checklist — 25 named decisions

### 7.0 The six that block day one
6, 7, 9, 13, 14, 19 below. Ranked by "how much code changes if you guess wrong": **6 > 13 > 19 > 9 > 7 > 14.**

### Store / schema (B7 step 1)
1. **Head-pointer key:** per `scope` (B4) or per `(statistic, scope)` (D6)? Decide before the table ships.
2. **Which corpus-snapshot fields survive D0.** Specifically: is there still a `churn_cursor`, and if so
   derived from what? The seam B3 names does not exist (FA1). If the answer is "11-ii's problem", say so
   — B4's OVERWRITE rule makes additive fields safe, so deferring is legitimate *if stated*.
3. **Single-flight lease semantics: expiry and crash recovery.** §5 forbids clock constants ("quiescence
   over clocks; no invented cooldown constant"); a lease with no expiry deadlocks permanently when its
   holder dies. Nothing in R1–R8 or A–E addresses lease release. This is a genuine hole, not a blank.
4. **Does the `state` field carry a closed-set ASSERT, and what is the domain?** §7's set is written
   against the retired churn model (C3). New table ⇒ an ASSERT is safe here (no rows to migrate), which is
   an argument *for* pinning it — but the set must be re-derived under D3 first.
5. **Where per-probe records live.** D4's paired decomposition needs the *previous* run's `point_id` set
   and probe-text shas. §7's field list has no probe-level storage and D7 adds only "paired-stat fields".
   A row carrying thousands of probe entries is a schema decision. (Note: in 11-i there is no previous run
   to pair against, so this code is untestable except synthetically — say so in the contract.)

### Runner / measurement (B7 step 2 as reworked by D7)
6. **R2's pool size** — full derivable-text pool (D2) or fixed-N (packet / B2)? (C1)
7. **`k′`.** Load-bearing three ways: it sets the absent leg's distribution (a deeper capture raises absent
   maxima and lowers catch), it sets the self-retrieval gate's leniency (deeper ⇒ more marginal probes
   retained ⇒ S2 worsens), and C6f's per-hit stats are defined over "the SHOWN-k slice only". Also note
   `SurrealStore.hybrid_search` clamps `k` to `_MAX_HYBRID_K`.
8. **Which hit set the ANSWERED leg maxes over** — shown-`k` (what production serves) or captured-`k′`.
9. **The portable answered union's composition.** Self-supervised only, or + identifier probes, and how
   many now that fixed-N is retired? This is not cosmetic: `_cosine_absence_predicate` is
   `max_cosine < floor and not has_verbatim_anchor`, so **anchored identifier samples contribute a
   constant zero to the false-fire numerator while enlarging its denominator** — their share silently
   sets the effective strictness of the pre-registered 5% bar, and it differs between F_legacy (15/56 =
   27%) and any portable union.
10. **The hash-stable sampler's inclusion threshold in steady state, and whether the row persists `N` (a
    count) or a threshold (a fraction).** Fixed N ⇒ a threshold that moves with corpus size ⇒ membership
    churn, the exact defect D2 was written to remove. Fixed threshold ⇒ N drifts away from the
    gate-certified N. The design pins neither and does not notice the tension.
11. **Probe-text derivation:** which `chunk_type` values count as code vs doc; whether both the summary
    and source chunk of one symbol may enter the pool (see S4); whether `llm_summary` is ever used.
12. **The bootstrap's resampling unit** — paired at the probe (both legs move together) or independent per
    arm. D1's "jointly" admits both and they give different CI widths.
13. **The bootstrap's implementation, which is a DESIGN question and must not reach a builder.** D1
    mandates re-running `choose_cosine_floor` per resample; that object is identity-pinned against
    production and ONE IMPLEMENTATION forbids a private twin. But O(B·N²) in pure Python with no
    numpy/scipy (verified) does not finish at pool scale. The three exits — (a) escalate for a numpy/scipy
    install (the packages-over-hand-rolling rule's *first* side), (b) write a sort-based sweep that
    computes all candidate floors' rates in one pass and **prove it byte-equal to `choose_cosine_floor`
    on the same inputs**, (c) cap the bootstrap's N — are not equivalent, and (b) needs the equality proof
    written into the contract as a pin.
14. **The ≥98% stability gate's denominator.** "≥98% of the union's samples": answered union only /
    answered + absent / everything including anchored samples that can never flip at any floor? The
    answered union alone makes the gate nearly free (its samples sit mostly above the floor by
    construction); adding anchored samples inflates agreement mechanically. Also state that the agreement
    is in-sample, and what "decision" means (presumably `_cosine_absence_predicate` at `ci_low` vs
    `ci_high`).
15. **What happens if the stability gate never passes at any N up to pool size.** It is an entry condition
    for 11-ii. E5 ruled the determinism pin's RED case in advance precisely so nobody improvises; the gate
    deserves the same.
16. **What triggers `insufficient_corpus` now** (C4).
17. **Is R1's `calibration.extra_answered_queries` / `extra_absent_queries` `lore.yaml` hook built in
    11-i?** There is **no `calibration` section in `LoreConfig` today** and the config models are
    `extra="forbid"` strict, so this is a schema change with its own contract.
18. **Does the portable instrument evaluate the D1 substrate gate (`D1_MIN_MEDIAN_SPREAD = 0.05`) at all?**

### Lab validation (B7 step 5 / R2)
19. **Which store R2 reads** (C9).
20. **How "in-container" reconciles with "DEPLOY: no"** — deployed image, ephemeral `podman run --rm` from
    a fresh build (the `lore_deploy.py conform` precedent), or host run (C7).
21. **Does R2 write its calibration row into that store?** A dark row in production is defensible; it is
    still a production write from a packet whose header says nothing changes. Say which.
22. **The acceptance denominator: legacy union (56) or human-labeled union (41)** (C5). Fix it *in the
    pre-registration*, before the run.
23. **What moves out of `scripts/` into the package, and what happens to the existing identity pins.**
    `Containerfile` copies `pyproject.toml`, `uv.lock`, `lorescribe/`, `loresigil/`, `loremaster/` —
    **`scripts/` does not ship in the image.** So `choose_cosine_floor`, the D1/D2 bars,
    `every_nth`, `parse_eval_questions`, `NONSENSE_QUERIES`, `IMPLEMENTATION_VOCABULARY_QUERIES` and
    `token_survey.percentile` (imported by the survey via a `sys.path` insert) are all unavailable
    in-container today. `loremaster/evaluation.xml` *is* in the image (it rides `COPY loremaster/`), but
    `DEFAULT_EVAL_XML` resolves it relative to `scripts/`. §7 says the script "becomes a thin CLI over
    the same engine" — the packet's Scope IN never mentions this migration, and it is not small.
24. **Where R2's per-query jsonl is COMMITTED** (S5). Prefer a tracked
    `docs/plans/v2/receipts/<date>-11i/` path or a committed regenerating script; a `scratchpad/` path is
    the failure that already happened once.

### Documentation
25. **Ship an amendment ledger with the design.** Six statements are silently superseded and still read as
    live: §1.2's "the per-hit flags and the substrate keep serving" (retired by E1, which landed at
    `be4c591` — `_COSINE_WEAK_MATCH_FLOOR` is `None` in this tree today); §5's churn leg (D0/D3); §7's
    caching instruction (A1); §7's state table (D3); R3's fixed-N minimums (D0); B2's constant-cost
    guarantee (D2). The doc already demonstrates the fix in D8a ("superseded-in-part by Addendum E,
    ruling E4") — apply it to the other six. This matters beyond tidiness: brief-base §1 is explicit that
    **a retrieved chunk arrives without its header**, and this document is destined for the index.

---

## 8. VERDICT

### SOUND-BUT-UNDER-SPECIFIED — 25 named decisions (§7).

The mechanisms are right and in several places better than what they replace (§3). Nothing in the ruled
design is *misconceived*; what is missing is the settling pass that turns five same-day addenda into one
work order. Three of the 25 are amendments to **ruled text** rather than unfilled blanks — C1 (the design
asserts two incompatible cost models), C3 (§7's state set is specified against a model D3 deleted), and
C8 (the packet omits every D7 deliverable it owns) — so the checklist must be executed as a short
addendum plus a packet rewrite, **not** as a builder's Q&A session. That is the honest shape of the
answer; I am not hedging toward NEEDS-REPAIR, because every one of those three is repaired by choosing
between options the design already contains.

**Confidence:** high on §4, §5 and §7 — every item there is grounded in a source read or a document
quotation, and the six day-one blockers are not judgement calls. Medium on §6.S1, which is the only place
I am reasoning about statistics rather than reading code.

**What would change my verdict to NEEDS-REPAIR:** a bootstrap dry-run showing the CI is routinely
**degenerate** (`ci_low == ci_high`) or spans fewer than ~3 distinct candidate values. That would break
D2's stability gate and D3's disjoint-CI adoption *simultaneously and silently* — the design's central
innovation would need replacing, not parameterising. Because S5 destroyed the historical dataset, the
cheapest instrument for this is a synthetic one: draw 56 answered and 15 absent cosines with the shape the
2026-07-07 run reported (one union sample below the floor, catch 15/15) and bootstrap
`choose_cosine_floor` over them. That costs one function and no store access, and it should be run
**before** the contract is authored, not discovered at R2.

**What would move it to NOT-IMPLEMENTABLE-AS-RULED:** nothing I found. Every obstacle here has at least
one buildable exit.

---

## 9. Residuals raised under scope law (I decide only to surface them)

- **R1.** `search.py`'s 10-d comment names `SearchPipeline._format_result`, which does not exist (FA6).
  One-line fix; the class it belongs to is the one `CLAUDE.md` says survives every gate.
- **R2.** The packet's entry check asserts a finding status that is wrong for 3 of 4 findings (FA5).
- **R3.** `loremaster/tests/_surreal_fakes.py` deliberately does not model `id` on scroll rows, and no
  production `scroll` caller reads it. D2's sampler will be the first — so the fake must be extended, and
  extending a fake to match a not-yet-written consumer is where "the test environment is a fiction"
  usually starts.
- **R4.** `docs/reference/surrealdb-31-capabilities.md` documents that `str(RecordID)` round-trips but
  does **not** document the angle-bracket wrapping for uuid-shaped id components. Establishing that took
  a live probe. Given the file is a *required first read* for every store change, the omission is worth a
  line in it.
- **R5.** The INDEX's 11-i row (0.20 wu) and the packet header (0.20 wu) both contradict D7's own
  re-estimate ("~0.20 → ~0.25–0.30"), and D7's estimate was made *before* the C1 pool-size question was
  settled. If C1 resolves toward the full pool, ~0.30 looks optimistic again.
- **R6.** 10-d is **merged but not deployed** (INDEX Log, 2026-07-24: "STILL NOT DEPLOYED"). So the
  running lore-lore and the DI instance are, as of this report, still serving the three confident-wrong
  surfaces E1 was ruled to darken — and `lore_index()` at 2026-07-24T17:23Z still renders
  `cosine_floor.floor = 0.50649`, `state = "stale"`, confirming it. E5 ruled that "every day the disarm
  waits serves confident-wrong output". Not 11-i's work; nobody else appears to be holding it.
- **R7.** D5's contingency (i), the probe-embed cache, is E4-promoted to *the* ruled response to measured
  cost and E4 records it is "ALSO a determinism instrument … load-bearing for E5". E5's fallback then
  leans on it. But the cache is scheduled for 11-ii (D7), while the determinism pin it backstops is a
  must-prove in **11-i**. If the pin goes RED in 11-i, the designed fallback's second leg is not built
  yet. The within-CI leg still holds, so this is a soft edge, not a break — but the contract should say
  which leg 11-i is actually allowed to land on.
