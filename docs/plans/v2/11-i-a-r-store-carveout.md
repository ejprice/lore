# 11-i-a-r — floor-calibration: THE STORE CARVE-OUT
size ~0.03–0.04 wu · wave L · depends: 11-i-a merged (`c7983e8`) · **DEPLOY: no** (nothing served changes)
law: DESIGN-LAW §3, §5 (store idioms), §6, §12 · repo `CLAUDE.md` **THE CONSUMER LAW + THE TRUST DOCTRINE**, incl. its `### TRUST — THE HARD DEFINITION` subsection
minted: operator ruling 2026-07-28 · ledger row `6e09610b`

## Why this packet exists
11-i-b priced at **~0.31**, over the ≥0.30 split clause — and the work pushing it over is
exactly the work that crosses the 11-i-a / 11-i-b ownership line: schema and store, which
11-i-a owns and 11-i-b may not edit. Carving it out returns b to **~0.28–0.29 whole**, in
its proper character (pure runner arithmetic against a frozen store), and restores the
clean audit split that made 11-i-a's cold audit work.

**Sequence is binding: a-r → 11-i-b's contract → 11-i-b's build.** The `adopt=True` guard
(§3.2) in particular must land BEFORE b's contract, so that contract is written *against
the refusal* rather than around it.

## Mission
Add the measurement-row columns the rulings require and 11-i-a did not ship, plus the
columns blind consumer informants named as blocking their input contract; resolve two
disclosed-but-unruled store behaviours. **Nothing served changes.** The engine still runs
only when explicitly invoked; the existing constants keep serving exactly as today.

**The Consumer Law is what makes this a packet rather than housekeeping:** a render can
rename, merge or re-word later — it can **never serve a distinction the row never
recorded**. An under-recorded row silently caps how honest lore is ever able to be about
why it is declaring an absence. And under the hard definition now in `CLAUDE.md`, a bound
is a FACT (the set, the predicate, the time) — **facts this table does not currently carry
cannot be named in any render 11-ii writes.**

---

## Scope IN

### 1. The measurement-row columns
`FLOOR_MEASUREMENT_COLUMNS` is **14 names** (re-derived 2026-07-28 by importing
`loremaster.store.surreal_schema`, not by reading a report): `head_identity`,
`head_revision`, `state`, `non_adoption_cause`, `note`, `floor`, `ci_low`, `ci_high`,
`adopted_n`, `instrument_version`, `corpus_content_digest`, `embedding_schema_fingerprint`,
`trigger`, `created_at`.

Everything below is **absent**. Two provenance classes, kept visibly distinct **because
they were derived independently and that independence is the evidence** — the scout worked
forward from the shipped schema, the sidecar backward from the rulings, and blind
informants arrived from consumer need without seeing either.

#### (a) RULING-REQUIRED — the rulings named them; 11-i-a did not ship them
Source: `receipts/2026-07-28-packet11ib/REPORT-fable-design-11ib-2.md` §7 RAISED-1 ·
`REPORT-scout-11ib-1.md` §A-9, §B-6.

| datum | why |
|---|---|
| `batch` | ruling **R-C**: *"pin `batch=None` explicitly and RECORD it in the measurement row"* |
| `n_resamples`, `method`, `B` | the bootstrap's own parameters; without them two rows are incomparable |
| `scipy_version`, `numpy_version` | ruling **R-G** — and see the ⚠ below |
| `k_prime` | C9's pre-registered capture depth |
| the **bars tuple** (false-fire ≤, catch ≥) | pre-registration is only as good as its receipt |
| gate triples (N-curve / stability) | C2, C4 |
| F2 null-rate + applied gap | the noise-vs-real-move calibration |
| sensitivity floor | R2.5 |
| degeneracy telemetry (`ci_distinct_candidate_values`, `ci_modal_mass`, `floor_rank`, `floor_tail_depth`) | F7.2; the S1 no-regret pins |
| per-group results | R3 |
| run cost (embeds, wall-clock) | D5 |
| C9/C13 drop diagnostics, split by cause | the drop rate is uninterpretable without them |
| the C11 probe manifest | in-row ≤ the proposed 1 MB bound; side-table decision deferred to R2 review |
| `statistic`, `scope` as queryable fields **on rows** | F6 / RAISED-2 — shipped on heads, absent on rows, so a never-adopted row's axes are recoverable only by digest-matching |

> ⚠ **Ruling R-G is premised on a FALSE fact.** It states the row *"already carries `B`,
> `N`, `method`"* and builds its version-column obligation on that. **None of the three
> exist** (verified by import). This is not only a dropped rider — it is a ruling resting on
> an unchecked premise, which is why neither the scout's nor the sidecar's authors caught
> the gap earlier, and why every entry above cites its source rather than asserting itself.

#### (b) CONSUMER-NAMED — from the 2026-07-28 consult, `CONSULT-SYNTHESIS-11ib.md` §3
Four blind informants reasoning about what they needed to build 11-ii's input contract.
**Overlap with (a) is corroboration, not duplication** — bars, library versions and
per-group results were named from both directions.

| datum | informant | why it blocks |
|---|---|---|
| a **corpus-change MAGNITUDE** datum | Opus (U1) | **§2 — the packet's largest item** |
| the **admissible band** (acceptance as a function of candidate floor) | Opus | without it the legs do not *identify* the floor, they merely fail to reject it — the acceptance table cannot be told from decoration |
| a **non-corpus staleness axis** (TEI endpoint identity is *printed in the receipt* but not a column) | Opus | a floor goes stale with an unchanged corpus |
| a **closed `trigger` vocabulary** | Opus + sidecar RAISED-6 (independent) | `option<string>`, no ASSERT; 11-ii is the packet that starts writing non-`manual` values, and history cannot be aggregated by cause without string archaeology |
| the **legal state transitions** (8 states pinned, no transitions) | Opus + cold reader | *"an input contract cannot be written against an enum alone"* |
| the **legacy `embedding_schema_fingerprint`**, or an explicit record that it is unrecoverable | Opus + Sonnet + cold | it is the premise the whole legacy↔portable comparison rests on; its absence is why the commensurability bound must say the scales *cannot be checked* rather than *do not coincide* |

### 2. U1 — THE RE-MEASURE THRESHOLD IS **MEASURED**, NEVER INVENTED (operator ruling, 2026-07-28)
**The finding.** `corpus_content_digest` is a whole-corpus digest: it changes on a
one-character edit to one chunk in ~23k. So *"digest changed"* fires on essentially every
commit, and nothing anywhere says how much change warrants paying a full re-measurement. A
scheduler built strictly on the current spec is either **skip** or **re-measure everything,
constantly**. Found by `informant-opus-11ib`, which flagged that its own pre-registered
trigger was *satisfied* and that it hit this only by trying to build the contract.

**The operator's ruling dissolves the design fork: this is a MEASUREMENT, not a judgement.**
*How much deviation before the floor is stale?* — that is an empirical question about this
corpus and this embedder, and the answer is the re-measurement trigger. **Do not invent a
constant.** The repo has receipts against exactly that (§5's clock-constant rejection; the
invented-constant class the whole design keeps killing).

**What this packet owes — the DATUM, not the threshold:**
- a corpus-delta magnitude recorded alongside the digest — chunk-level added/removed/edited
  counts, or a partial/per-tier digest set, sufficient to place a run on a deviation axis.
- **It must be DERIVED from the same walk that computes the digest**, never restated beside
  it. A magnitude that can diverge from its own digest is scaffolding that lies — worse than
  none, because it makes a false skip *more* convincing (`CLAUDE.md`, the hard definition).

**The named decision point** (the measure-then-tune law requires one, or it is a can-kick):
the threshold is derived once a **floor-vs-deviation sensitivity curve** exists — floor
movement as a function of delta magnitude, over successive real corpora. **Owner: 11-i-b's
R2 run is the first instrument that can emit it**, since it already holds every response-best
cosine for the whole pool at zero marginal embed cost. Until that curve exists, 11-ii's
scheduler MUST NOT ship an invented threshold; the honest interim is measure-on-every-change
with the cost recorded, and the cost is itself the argument for the curve.

⚠ This packet does **not** decide the threshold, the axis units, or the scheduler's policy.
It records what makes them measurable. Anything more is 11-ii's, on the curve.

### 3. The two behavioural items

#### 3.1 The corpus-growth classifier
`enumerate_calibration_pool` issues `LIMIT counted_total + 1`; a corpus that GREW between the
count and the walk returns `limit` rows and is classified `CalibrationPoolTruncatedError` →
`measurement_failed`. **An ordinary indexing event during a run therefore reports a corpus
that merely MOVED as a failed measurement** — a false incident from the one instrument this
packet family exists to build.

> **This resolves a DISCLOSED, UNRULED TRADE — not a hidden defect.** The 11-i-a builder
> wrote the hazard into the code verbatim (*"the margin is a TRADE, disclosed rather than
> tuned … nothing in the contract decides it, and widening it to fit a fixture is not a
> derivation"*) and refused to tune it. That is `WHEN YOU CANNOT CLOSE A HOLE, PIN IT`
> working exactly as written, and the packet doc says so because misrepresenting good prior
> work is its own defect.

**Ruled fix** (sidecar FU1.2): on `len == limit`, **RE-COUNT and classify from store state** —
moved ⇒ count mismatch / discard-requeue; count-stable-yet-overfull ⇒ genuine truncation ⇒
failed; a re-count failure propagates as itself. Growth never reaches a row, so this is **not**
a new non-adoption cause. Hosted store-side as ONE classifier (two callers are coming — the
ONE-IMPLEMENTATION law). Amends C8's operational words; the frozen truncation fixture must mock
**both** reads, and a growth fixture is added.

#### 3.2 The `adopt=True` guard
`adopt=True` on a state other than `measured` is always a caller bug, and post-11-ii it would
serve a floor from a row that measured nothing. Home: `_validate_domain` (the shipped
cross-field home — a store ASSERT cannot see a parameter). Four refusal fixtures + a positive
control + the `Raises:` docstring in the same diff (that surface was wrong once already —
cold-audit R4). **Lands before 11-i-b's contract.**

#### 3.3 The frozen-fixture edits both of the above require
Enumerated in the contract, not here.

---

## Scope OUT — surface to the operator if encountered
- **Any serving change whatsoever.** No chokepoint wiring, no `lore_index` behaviour change,
  no verdict or per-hit gate change, no constant retirement. If a change here would alter a
  served byte, **stop and escalate** — the split exists to keep this half dark.
- **All runner arithmetic, probes, captures and the R2 verb** — 11-i-b's, unchanged.
- **The re-measure THRESHOLD itself** (§2) — measured later, on the curve.
- **The `shown` field's semantics** — **a DESIGNER decision (operator ruling 2026-07-28)**,
  routed to the design sidecar, not settled by this packet or by a builder. Context: the
  consult's Fable informant found the exhibit marking hits `shown` on rows where the caller
  was served an *absence*. ⚠ Verified against the tree: the real `HitCapture` carries **no
  `shown` field** — so this is a writer-spec question for what 11-i-b builds, **not** a defect
  in shipped code.

## Entry check
1. **FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`.** This packet
   is entirely a schema change; **#107 was a 100% production outage whose answer was already in
   that file.** Cite it, never re-transcribe. The DDL decision rule it carries and this packet
   depends on: **FIELD → `OVERWRITE`; plain TABLE → `IF NOT EXISTS`; INDEX/ANALYZER → never
   `OVERWRITE`; `ALTER` is a trap, not the migration verb.**
2. Read `CLAUDE.md`'s `### TRUST — THE HARD DEFINITION`. Every column here exists so a bound
   can be stated as a FACT; a builder who does not know that will add fields without knowing
   what makes one load-bearing.
3. Suite baseline **declared before the run**, red set diffed BOTH ways (the 2026-07-28
   baseline caught a defect that would otherwise have been attributed to a sibling packet).
4. spike-surreal up — **`:18000`, the TEST store. NEVER `:18500`** (#177).

## Exit
TDD per repo law: contract (Opus) → **contract-adversary** → build (Opus) → cold audit.
- **Per-key write → read → present pins.** Every column is written, read back, and asserted
  present. A column that silently dies at a future schema edit is the failure this packet is
  paying to prevent.
- **The additive valve is `DEFINE FIELD OVERWRITE`** — and the contract must say so, so a
  builder discovering a gap extends rather than improvises.
- **A SATISFIABILITY RECEIPT before any builder sees the contract**: prove it goes 0-failed
  against a known-correct build (the C-DEF class — 20 pins once shipped RED on a correct
  build inside an otherwise-strong contract). Include the harder leg: still satisfiable after
  the cleanups lint will demand.
- **No deploy.** Findings stay OPEN — they resolve in 11-ii when the mechanism serves.

**THE ADVERSARY'S QUESTION FOR THIS PACKET** — ask it of the contract before the builder does:
*a build could add all of these columns and leave every one of them NULL forever, and the
suite would pass.* The pins must force each column's **fate**, not its existence: written by a
real path, read back, and — for the derived ones (§2's magnitude, the admissible band) —
**proven to move when the thing they describe moves.** Existence is not a pin.
