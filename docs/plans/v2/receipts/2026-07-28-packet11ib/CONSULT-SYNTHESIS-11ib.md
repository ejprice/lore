# Consumer consult — packet 11-i-b, the R2 evidence package

**Run 2026-07-28 by `lead-11ib`**, on the operator's direction: *"lore's consumers are models
(Sonnet 5, Opus 5, Fable 5) and their opinion matters. Consult them about the output they require
for maximum effectiveness and minimising wasted tokens. They MUST TRUST lore."*

Method: `docs/design/2026-07-06-client-needs-consult.md`, with two deviations designed by
`fable-design-11ib-2` (§5.2) — task-grounded keyed retrieval instead of pure introspection, and a
degraded-variant control leg. Battery adversarially attacked before any informant ran
(`REPORT-adversary-exhibit-11ib-1.md`, verdict INSUFFICIENT → fix wave → 10 keys).

Informants: `informant-opus-11ib` (Opus, honest) · `informant-sonnet-11ib` (Sonnet 5, **degraded**)
· `informant-fable-11ib` (Fable, appendix) · `informant-cold-11ib` (cold reader, honest).
Pre-registrations locked before any package was opened.

---

## 0. Bounds — read before weighting anything below

- **The cold-reader leg is COMPROMISED, by its own report.** It carries the full project
  `CLAUDE.md`, and stated plainly that it *"is not a valid test"* of the package's
  "readable-without-context" claim for that population. It traced each term it caught itself
  understanding anyway. **Its vocabulary signal is discounted; its structural signal is not** — and
  the structural signal produced this consult's sharpest trust finding (§2.3).
  ⚠ **We cannot currently run a genuinely cold reader from inside this repo**: every spawnable
  agent arrives with the project's law loaded. Either the README's readability claim is removed, or
  it is tested somewhere that constraint does not hold.
- **All four informants disclosed contamination when asked** (question 0.0, added this run). The
  2026-07-25 consult discovered its contamination afterwards, from one volunteer. Measuring it did
  not remove it — it made it weightable.
- **Two informants flagged specific answers as possibly context-shaped**, unprompted: Sonnet on why
  it went hunting for the run1/run2 mismatch, Opus on the phrasing of its Q2 answer. Both said the
  underlying gap was real and specific. Recorded as corroborated-but-contaminated.
- **The battery's mechanical grader OVERSTATES its own discrimination.** Sonnet refused key 6
  correctly on the degraded package using the surviving scope sentence, while the grader — keyed on
  the removed prohibition string — scored that key as failed. **A careful reader out-performed the
  grader.** Do not cite the fix wave's scoreboard as a measure of what the battery catches.

## 1. The verdicts

| informant | package | verdict | 0.1 trigger hit? |
|---|---|---|---|
| Opus | honest | **CALL_AGAIN**, U1 escalated as a design fork | no — satisfied |
| Fable | appendix | **CALL_AGAIN**, two slots escalated as riders | no — satisfied |
| cold reader | honest | **CALL_AGAIN scoped to exactly 3 data**; ROUTE_AROUND for the rest | no — reconstructible, not absent |
| Sonnet | **degraded** | **ROUTE_AROUND** | **not literally hit** — said so rather than claiming credit |

**The control worked.** Degraded → ROUTE_AROUND; honest and appendix → CALL_AGAIN. The battery
discriminates at the VERDICT level, which is the level the acceptance is defined at.

Sonnet's ROUTE_AROUND was **not** for the reason we degraded the package. It routed around because
*"a named dependency [is] contradicted by the package's own data, next to a named-but-missing
adjudicator."* The instrument caught something better than what it was built to catch.

---

## 2. THE RESULT: agents trust what they can CHECK

Every convergent finding points one way, and it is not "serve more".

### 2.1 The mechanism, in the informants' own words
- **Fable** would cut two-thirds of the package's bytes but **refuses to cut the cross-artifact
  count redundancy** — *"why 1.9 was checkable and why the verdict is CALL_AGAIN instead of 'trust
  me'."*
- **Opus** on what must never go: the `n` on every rate and the `k / n` beside every decimal —
  *"what let me re-check every number instead of trusting it"* — and `05`'s "what this row does NOT
  carry" inventory, *"the single reason my verdict is CALL_AGAIN rather than ROUTE_AROUND."*
- **Sonnet** routed around a package whose stated verdict its own arithmetic contradicted.
- **Opus's pre-registered dealbreaker**: two-directional labelled error rates, because a floor
  without them is *"an unfalsifiable number"* — the identical conclusion the 2026-07-25 consult
  reached unanimously, reached again blind, by a different model, under different framing.

**Corollary, and it inverts an engineering instinct:** the BULK DATA is what to cut (a model cannot
check it and should not spend context reading it); the REDUNDANCY that looks like waste is what
makes the numbers falsifiable. Cut evidence, keep scaffolding.

### 2.2 THE HIGHEST-VALUE SINGLE CHANGE (Opus, Q2) — the admissible band
> Report the acceptance legs as a **FUNCTION of the candidate floor** — the set of floors that pass
> both bars, with `ci_low`/`ci_high` and the selected point marked — instead of as one row at one
> value.

Today the package shows that the adopted floor clears both bars. It does **not** show that any
other floor would have failed them. **If a wide band also clears them, the legs do not IDENTIFY the
floor — they merely fail to reject it, and the acceptance table supplies the APPEARANCE of
validation while the selection ladder carries the whole load.** A reader cannot distinguish those
two worlds.

- **Costs nothing**: a re-aggregation of data the run already holds; zero extra embeds (the
  precedent the package sets for itself elsewhere).
- **It is the missing CONTROL.** The package has a deliberate failing control for determinism and a
  counterfactual for the match key. Its load-bearing claim has neither.
- It is `FIXTURES MUST DISCRIMINATE` pointed at a threshold instead of a test suite.

### 2.3 The cold reader's finding — the claim that cannot be checked at all
Asked which single unresolved item most limited its use of the document, it chose neither
attribution nor the undefined symbols, but **"the ladder"** — the selection procedure, never
formally specified:

> the ladder underlies the one safety argument (bound iv) that makes the acceptance PASS/PASS
> non-circular, and I can't independently verify it without knowing what the sweep does.

The package's central claim rests on an argument whose foundation the document never defines. This
and §2.2 are the same defect seen from two sides: **the acceptance is not shown to be
discriminating, and the procedure that would let a reader check it is not specified.**

---

## 3. WHAT 11-i-b MUST RECORD — named by consumers, not derived from rulings

A render can rename, merge or re-word later; **it can never serve a distinction the row never
recorded.** Each item below was named by an informant reasoning about what it needed.

| # | datum | who | why it blocks trust |
|---|---|---|---|
| 1 | **A corpus-change MAGNITUDE datum** (chunk-level delta count, partial/per-tier digest, or a measured slope) | Opus **[NEW]** | The re-measure branch has NO threshold — only the skip branch does. A whole-corpus digest changes on a one-character edit to 1 chunk in 23456, so a scheduler built on the spec is either "skip" or "re-measure everything, constantly". **The sharpest gap in the consult, and nobody on the authoring side found it.** |
| 2 | **The admissible band** (per-candidate-floor acceptance rates) | Opus Q2 | §2.2 — without it the acceptance table cannot be told from decoration |
| 3 | **The bars, persisted** (`≤0.05` false-fire, `≥0.60` catch) | Opus + Sonnet | They live in PROSE. Two runs cannot be compared, and the leg-1 denominator is ambiguous between readings that PASS and readings that FAIL badly |
| 4 | **`scipy_version` / `numpy_version`** | Sonnet | They are part of the only determinism guarantee actually proven — absent, a scheduler **cannot check** the guarantee it depends on |
| 5 | **Per-group results** | Opus | Nobody can see one group degrade while the aggregate holds — precisely the signal that should trigger a re-measure |
| 6 | **A closed `trigger` vocabulary** | Opus + Fable sidecar (independent) | 11-ii is the packet that starts writing non-`manual` values; an open string means history cannot be aggregated by cause without string archaeology |
| 7 | **A non-corpus staleness axis** (TEI endpoint identity is PRINTED but not a column) | Opus | A floor can go stale with an unchanged corpus |
| 8 | **The legal state transitions** (8 states are pinned; no transitions are) | Opus + cold | *"An input contract cannot be written against an enum alone"* |
| 9 | **The legacy `embedding_schema_fingerprint`, or an explicit record that it is unrecoverable** | Opus + Sonnet + cold | It is the premise the whole legacy↔portable comparison rests on |
| 10 | **A definition of `shown`** | Fable + Opus | Fable: the flag marks hits `shown` on rows where the caller was served an ABSENCE. ⚠ Verified against the tree: the real `HitCapture` has **no `shown` field** — this is a WRITER-SPEC caution for what b builds, **not** a defect in shipped code |

**Not in the shipped 14 columns:** every one of 1–10.

## 4. Token economy — converging, and against instinct

| | CUT | NEVER CUT |
|---|---|---|
| Opus | ~80% of the JSONL (24 rows × 30 hits; *"I used one row and read 12 of its 30 hits"*); 8 of 10 probe pairs; duplicated validity-floor table; the bare `F_portable − F_legacy` scalar | the three-population table; the four bounds **IN SITU** (not appendixed); the path-matching counterfactual; the "does NOT carry" inventory; the four commitments; **the `n` on every rate** |
| Fable | JSONL ranks 3–30 (~⅔ of bytes); 7/10 probe pairs; 4/6 group tables | population table; bounds; determinism pair; **cross-artifact redundancy** |
| Sonnet | `04-probe-texts.md` entirely (*"zero scored content"*); JSONL bulk except boundary rows | the "not carried" table; **the 07/08 determinism pair — only meaningful together**; population table |
| cold | most per-percentile tables; most of the 18-row "not carried" table | the bound callouts; population table; the "commits 11-ii to" bullets |

**Unanimous keep: `00`'s three-population table** (*"a consumer that picks the wrong one gets a
wrong denominator with no error anywhere"*). Opus: highest value-per-byte in the package by a
distance. **Unanimous cut: the bulk sample data.**

⚠ **Opus on `04-probe-texts.md`, worth its own line:** *"the worst byte-for-byte in the package"* —
it costs ~6.7 KB, embeds a *"do not answer these"* instruction every reader must spend attention
obeying, and, **measured on itself this run, injects real out-of-package facts into a reader's
context.**

## 5. Escalated by informants rather than silently resolved
- **Opus U1** (design fork): the re-measure threshold — item 1 above.
- **Fable**: the fingerprint-CHANGE rule is nowhere stated, and one commitment's literal *"and on
  nothing else"* wording EXCLUDES it; the F2 gap has no row address.
- **Sonnet**: no tolerance band for the digest/floor mismatch; `MIN_IDENTIFIER_PROBES` cleared
  **exactly at its floor (15/15)** — a fragile pass.
- **cold**: no per-state behaviour spec for 7 of 8 states; "the ladder" unspecified.
