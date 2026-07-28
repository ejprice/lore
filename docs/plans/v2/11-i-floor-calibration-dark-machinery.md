# 11-i — Per-corpus floor calibration · DARK MACHINERY (findings #83, #87, #161, #179)
size ~0.20 wu · wave L · depends: packet 10 ruled · **DEPLOY: no** (nothing served changes)
law: DESIGN-LAW §3, §5 (store idioms), §6, §12
split provenance: packet 11 split at kickoff per its own ≥0.30 clause — design doc
`docs/design/2026-07-24-floor-calibration.md` §B8, operator-approved 2026-07-24. The
per-half sizes here are the lead's split of B8's ">0.30"; B8 sized the whole, not the halves.
Re-check at kickoff.

⚠ **DESIGN RULED 2026-07-26 — read the rulings BEFORE this file's older prose:** all 23
decisions are ruled in `receipts/2026-07-24-packet11i/RULINGS-2026-07-25.md` (+ Addendum
F-r2 §R1–R10 in the design doc); S1 measured NOT DEGENERATE. The INDEX row re-splits the
BUILD → **11-i-a (~0.15) / 11-i-b (~0.24)** at kickoff. Two findings ride the build order
(slotted 2026-07-26):
- **#198** — `weighted_percentile` is hand-rolled TWICE and this packet would add a THIRD
  consumer: consolidate to ONE implementation BEFORE the new consumer lands (ONE-
  IMPLEMENTATION law).
- **#201** — the floor-calibration statistical core is a hand-rolled reimplementation of
  sklearn/scipy/numpy primitives (named root cause of the affordability crisis, the
  undiagnosed hang, and the percentile duplication). The contract phase applies packages-
  over-hand-rolling per the RULINGS' disposition — and if the RULINGS are silent on a given
  primitive, adjudicate it there before any bespoke statistical code is extended.

## Mission
Build the measurement machinery and its store, **with the serving surface untouched**.
Executes B7 steps 1, 2 and 5 of the ruled design. Nothing in this packet changes what any
user or agent sees: the existing constants keep serving exactly as they do today, and the
new engine runs only when explicitly invoked. Independently landable and independently
auditable — that is the whole point of the split.

## Binding architecture (operator ruling 2026-07-24 — do not re-open)
The floor is store state in SurrealDB, recalculated by the RUNNING CONTAINER when stale;
no outside caller in the durable path. Full ruling: `lore_recall("operator ruling cosine
floor SurrealDB container")` (kind=decision). Design: `docs/design/2026-07-24-floor-calibration.md`
R1–R8 + Addenda A and B.

## Scope IN
- **Engine + store (B7.1):** floor-calibration engine module per the B5 seams; schema per
  B4; append-only measurement rows (these also carry the F6 tuning history) + one minted
  head pointer per scope. Head mint and single-flight lease are HOT ROWS → `_txn.retry_on_conflict`
  ONLY. Do not hand-roll a retry, a backoff, or a jitter at this seam — the repo has
  receipts (#102/#120) of exactly that going wrong in two different ways.
- **Portable runner, in-container (B7.2, R1/R3):** fixed-N stratified probes (cost is
  O(probes), NEVER O(corpus)); answered + hold-out legs; identity-pinned predicate, bars
  and dominance rule.
- **Lab validation on lore's instance (B7.5, R2):** an in-container one-shot verb. **This
  is also #161's overdue re-measure** — the first honest floor this repo has had since the
  embedding schema moved.

## Scope OUT (surface to operator if encountered)
- **Any serving change whatsoever.** No chokepoint wiring, no `lore_index` behaviour change,
  no verdict or per-hit gate change, no constant retirement. All of that is 11-ii. If a
  change here would alter a served byte, stop and escalate — the split exists to keep this
  half dark.
- Verdict grammar/wording (ruled law — meaning NO UNILATERAL CHANGE, not "the operator
  picks it"). F3 is a **CLIENT CONSULT**, not an operator fork: the models that consume the
  tool decide what serves them (operator ruling of 2026-07-06, carried in
  `docs/design/2026-07-06-weak-match-discrimination.md`; method in
  `docs/design/2026-07-06-client-needs-consult.md`). Outcome recorded in the packet 10
  design doc §C3. Nothing in this packet needs it.
- Reranker/utility-predictor confidence layers (packet 28 territory).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this packet
defines a table and fields; #107 was a 100% production outage whose answer was already in
that file. Cite it, never re-transcribe. The DDL decision rule it carries and this packet
depends on: **plain TABLE → `IF NOT EXISTS`; FIELD → `OVERWRITE`; INDEX/ANALYZER → never
`OVERWRITE`; `ALTER` is a trap, not the migration verb.** ⚠ If the schema ever grows a
RELATION table or a SEQUENCE, the rule INVERTS for the first and carries a migration
residual (#146) for the second — re-read §1 before adding either.
- packet 10 ruling recorded (F3 may still be open — it does not gate this half).
- suite snapshot green at current HEAD; spike-surreal up (**:18000 — the TEST store. NEVER
  :18500, which is production**; see #177).
- `lore_findings` → #83, #87, #161, #179 open; #4 is RESOLVED (P8d W3) — packet 11's old
  "fold #4's fix if still open" step is already satisfied and needs no work.

## Exit
TDD per repo law; hostile fixtures for any new render of stored text; contract-adversary
before the builder; cold audit. **No deploy** — prove the machinery with the lab-validation
verb and the suite. Report the measured floor and its provenance (probe strategy, corpus,
embedder+prompt fingerprint, date) as a receipt. INDEX row + Log. Findings stay OPEN — they
resolve in 11-ii when the mechanism actually serves.

**THE DETERMINISM CONTROL IS A MUST-PROVE PIN (lead's GO condition, affirmed in Addendum
E5).** The exact-skip scheduler — "measure at every CHANGED post-sweep, skip unchanged" —
rests on an unchanged corpus reproducing its measurement bit-identically. That property is
ASSERTED, not yet verified: prove it, and mutation-prove the pin.
**A RED pin here is NOT a stop** (ruled in advance so nobody improvises): the honest risk is
TEI inference nondeterminism — GPU batch-composition floating point can break bit-exactness
at the embedder, which is the instrument's fault and not the design's. If bit-exactness
fails, the exact-skip's rationale falls back from *"bit-identical"* to *"within-CI by
construction"* — an unchanged corpus's re-measurement differs only by instrument noise, and
the disjoint-CI adoption test absorbs it (no adoption, no flap, and still no threshold) —
and the E4-promoted probe-embed cache RESTORES bit-exactness for unchanged probes by
construction. **Record in the run receipts WHICH leg held.** Do not report "deterministic"
without saying which.

**R2's measurement is a HANDOFF, not just an exit receipt — two downstream decisions block
on it (operator ruling 2026-07-24: "we need to measure first"):**
1. **The F3 client consult runs AFTER this packet, before 11-ii**, so the models judge on
   R2's real divergence between the self-supervised and human-probe floors rather than on
   hypotheticals. Publish that divergence in a form a consult can be shown.
2. **#180's fix (basis mismatch) is a design choice that wants the same discipline.** Its
   magnitude — how often a best-of-response-calibrated floor over-flags mid-list hits — is
   UNMEASURED. If R2's instrument can cheaply emit the per-hit cosine distribution alongside
   the per-response maxima, capture it here: that is the number the 11-ii design decision
   needs, and packet 35 is the only other place it comes from. If it cannot, say so — do not
   synthesise it.
