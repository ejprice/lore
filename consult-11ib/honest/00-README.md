> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# R2 floor-calibration evidence package — contents

Nine artifacts. Every number in every artifact is a sentinel: drawn from a visibly artificial
family so that no value can be quoted anywhere as a lore measurement. R2 has not run.

| file | what it carries |
|---|---|
| `00-README.md` | this map, the population names, and the term glossary |
| `01-summary.md` | both floors, their selection receipts, the two pre-registered acceptance legs, the run's measured population, and the acceptance's independence bound |
| `02-per-group-distributions.md` | response-best cosine distributions for the six measurement groups under both instruments, with per-percentile deltas — and the commensurability bound that governs every delta on the page |
| `per-query-rows.jsonl` | the per-query rows themselves (deterministic sample) |
| `03-anchor-rates.md` | verbatim-anchor rate per group |
| `04-probe-texts.md` | ten self-supervised probe texts beside ten human questions |
| `05-adopted-row-provenance.md` | the adopted measurement row's typed fields with values, the two closed enums behind them, and what the row does NOT carry |
| `06-per-hit-decomposition.md` | the per-hit cosine distribution and the over-flag decomposition |
| `07-determinism-and-run-receipt.md` | the determinism control's verdict, and the run's provenance receipt |
| `08-drop-diagnostics.md` | probe drops by cause, and the validity floors |

## THREE populations, three names — never call any of them just "answered"

Three different counts in this package could each loosely be called "the answered set". They are
different sizes over different things, and a consumer that picks the wrong one gets a wrong
denominator with no error anywhere. Each has ONE name, used at every site:

| name | value | what it counts | where it is the denominator |
|---|---|---|---|
| **`answered_probes`** | **411** | self-supervised PROBES surviving the self-retrieval drops | `MIN_ANSWERED_PROBES`; `adopted_n` on the row (`05`, `08`) |
| **`probe_manifest_pool`** | **456** | self-supervised PROBES attempted — the size of the `self-supervised-answered` group, and the probe manifest's length | every drop rate in `08` |
| **`verdict_not_fired_queries`** | **964** | QUERIES, across all six groups, whose absence verdict did not fire | every rate in `06` |

`411 = 456 − 45` (the drops, `08`). `964 = 1740 − 776` (the fires, `03`). The three are not
interchangeable in any direction.

## The bounds, and where each one lives

Every bound in this package sits **inside the claim it governs**, not in an appendix. There is no
bounds section; if you are looking for one, you have the wrong package.

| bound | what it limits | lives in |
|---|---|---|
| **(i)** survey mix, not live traffic | every rate in the package — none is a live-traffic estimate | `06` (with the numbers), `01` ×2, `03` |
| **(ii)** shown-k slice only | the per-hit numbers cover ranks 1–10 of a `k' = 30` capture | `06` |
| **(iii)** the two instruments are not commensurable | every `Δ` in `02`; the headline scalar in `01` | `02` (before the first table), `01` |
| **(iv)** acceptance is not held out from selection | both acceptance legs | `01` (beside the acceptance table) |

## Terms used in this package

Packet-internal references, glossed here so this package is readable without 11-i-b's context.

| term | meaning |
|---|---|
| `B4` | the hot-row mint rule: the head row is contended on and advanced under one retry driver; also the additive-column (`OVERWRITE`) escape valve |
| `C2` | the anchored-excluded accounting rule |
| `C6` | the ruling that fixes this evidence package's six parts, (a)–(f) |
| `C9` | the `k'` capture depth and the empty-absent-leg rule (a probe whose `k'` hits all come from its own source file contributes no absent sample) |
| `C10` | the exact-skip change-detection datum: `corpus_content_digest` over the corpus's ascending-id chunk walk |
| `C11` | the probe-manifest persistence rule (manifest stored in-row) |
| `C12` | identifier-probe sampling: the first 15 identities in ascending `sha512_hex(identity)` order |
| `C13` | the self-retrieval match key: the HIT's `point_id` must equal the probe's source-chunk `point_id`; path matching is not self-retrieval |
| `D1` | the design clause listing what a run reports: floor point, interval, N, B, method |
| `D4` | the paired ruler-vs-measurand decomposition: the floor over the surviving manifest subset must equal the floor over the full pool |
| `D5` | run-cost persistence: embeds and wall-clock are recorded on the row |
| `D8` | pre-registration: the bars are fixed before the run, not chosen after seeing it |
| `E5` | the determinism MUST-PROVE rule: WHICH leg held must be recorded as a typed value from a closed enum, never as the unqualified word "deterministic" |
| `F2` | the null-rate / applied-gap calibration that decides whether a floor move is noise or real |
| `F4.2` | the `insufficient_corpus` predicate over the three validity floors |
| `F6` | the head-identity axes (`scope`, `statistic`, `query_shape`) |
| `F7.2` | degeneracy telemetry: whether the selected interval is an artifact of too few distinct candidate values |
| `O7` | the ruling making `head_identity` a REQUIRED column |
| `R2` | the one dual-instrument lab-validation run this package reports |
| `R2.5` | the sensitivity-floor requirement |
| `R3` | the per-group results persistence requirement |
| `R-G` | the ruling requiring `scipy`/`numpy` versions on the row |
| `R-PACKAGE` | the gate population over which two floors' decisions are compared for agreement |
| `#180` | the over-flag rider: the fraction of SHOWN hits below the floor, split best-hit vs mid-list |
| `packet 35` | a later packet whose job is to sample the production query mix |
| `11-ii` | the next packet: it wires this measurement to a scheduler and a served surface |
| `§7` | the design's persistence clause — what a run must write down |
| `SURVEY_K` | the shown slice, 10 — the hits a caller actually sees |
| `k'` | the capture depth, 30 — hits the instrument records, of which only the first `SURVEY_K` were shown |

## How the sentinel values are built

- Every **independently chosen** real value is either an ascending digit run
  (`0.123456`, `0.234567`, `0.345678`, `0.456789`) or a two-digit repunit
  (`0.ababab` — e.g. `0.313131`, `0.696969`). Every independently chosen count is a
  strictly monotone digit run (`12`, `123`, `234`, `345`, `456`, `567`, `987`).
- Every **derived** value — a sum, a difference, a rate, a remainder — is the exact
  arithmetic consequence of its inputs, and therefore usually carries no signature at all.
- Rates are always shown as `k / n` beside their decimal. The fraction is exact; the decimal
  is rounded to six places, so independently rounded components may miss their rounded total
  by one unit in the last place.
- Field names, the artifact list, the state enum and the non-adoption-cause enum are REAL —
  read from the shipped schema. Only the values are synthetic.
