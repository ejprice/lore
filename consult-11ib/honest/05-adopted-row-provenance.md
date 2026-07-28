> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 05 — The adopted row's typed provenance fields

*C6(e). Field names, ordering and the two closed enums are read from the shipped schema
(`loremaster/loremaster/store/surreal_schema.py`). Only the values are synthetic.*

## The adopted `floor_measurement` row — all 14 shipped columns, in write order

`FLOOR_MEASUREMENT_COLUMNS` is the single source of truth for this list.

| # | column | type | value |
|---|---|---|---|
| 1 | `head_identity` | `string` (REQUIRED) | `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef` |
| 2 | `head_revision` | `option<int>` | `12` |
| 3 | `state` | `string`, closed | `measured` |
| 4 | `non_adoption_cause` | `option<string>`, closed | `NONE` |
| 5 | `note` | `option<string>` | `NONE` |
| 6 | `floor` | `option<float>` | `0.456789` |
| 7 | `ci_low` | `option<float>` | `0.404040` |
| 8 | `ci_high` | `option<float>` | `0.505050` |
| 9 | `adopted_n` | `option<int>` | `411` |
| 10 | `instrument_version` | `option<string>` | `0.0.0-SYNTHETIC` |
| 11 | `corpus_content_digest` | `option<string>` | `fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210` |
| 12 | `embedding_schema_fingerprint` | `option<string>` | `SYNTHETIC-EXHIBIT-FINGERPRINT-0123456789abcdef` |
| 13 | `trigger` | `option<string>` | `manual` |
| 14 | `created_at` | `datetime` (REQUIRED) | `1234-05-06T07:08:09Z` |

Row id: `floor_measurement:synthetic0000000001`.

Reading notes that are properties of the schema, not of this run:

- `head_identity` is REQUIRED (ruling O7): the history is append-only, so a row that cannot name
  its own scope is unattributable forever. There is no `DEFAULT` — a default would fabricate an
  identity.
- `non_adoption_cause` is set **only** on `measured_not_adopted`. It is `NONE` here because the
  head was adopted.
- `note` is mandatory unless `state` is `measured`. It is `NONE` here for that reason. It is
  free text; nothing in 11-i renders it.
- `adopted_n` is the ACTUAL surviving probe count, never a nominal ladder rung. `411` is
  `456 − 45` — see `08`.
- `trigger` is an open `option<string>` today: nothing in the schema closes its vocabulary.
  This run wrote `manual`.

## The adopted `floor_head` row

| column | value |
|---|---|
| `revision` | `12` |
| `measurement` | `floor_measurement:synthetic0000000001` |
| `adopted_at` | `1234-05-06T07:08:09Z` |
| `axes.scope` | `SYNTHETIC_SCOPE` |
| `axes.statistic` | `response_best_cosine` |
| `axes.query_shape` | `any` |

`scope` and `statistic` are always serialised into the head identity; `query_shape` defaults to
`any`. The axis columns live on `floor_head`. **They are not columns on `floor_measurement`** —
a measurement row's only link to its axes is the one-way `head_identity` digest above.

## The two closed enums, verbatim from the shipped schema

`FLOOR_STATES` (8, exactly pinned):

`unmeasured` · `measuring` · `measured` · `measured_not_adopted` · `invalidated_remeasuring` ·
`measurement_failed` · `insufficient_corpus` · `disabled`

`FLOOR_NON_ADOPTION_CAUSES` (5, exactly pinned):

`head_retained_overlap` · `catch_bar_unmet` · `substrate_indiscriminate` · `interval_degenerate` ·
`stability_gate_unmet`

`substrate_indiscriminate` (a CORPUS property) and `interval_degenerate` (an INSTRUMENT property)
are distinct values by ruling: collapsing them would let an instrument artifact be served as a
confident corpus claim.

---

## What this row does NOT carry

The following are proposed additions. **They are NOT in the shipped schema as of 2026-07-28** —
no column exists for any of them, and the values in the right column are what this run would
have written had they existed. They are listed so that this consult can judge whether the
shipped field set is sufficient BEFORE the additive valve closes.

| proposed column | would have been | required by |
|---|---|---|
| `batch` | `NONE` (explicitly pinned) | ruling R-C |
| `n_resamples` (`B`) | `2345` | D1 / D8 pre-registration |
| `method` | `bca` | D1 / D8 |
| `scipy_version` | `0.0.0-SYNTHETIC` | ruling R-G |
| `numpy_version` | `0.0.0-SYNTHETIC` | ruling R-G |
| `k_prime` | `30` | C9 |
| bars tuple | false-fire `≤ 0.05`, catch `≥ 0.60` | §7 persistence |
| gate triples (false-fire rate, hold-out catch, n per group) | see `01`, `02` | §7 persistence / R3 |
| F2 null-rate + applied gap | null-rate `0.020202`, applied gap `0.010101` | F2 |
| sensitivity floor | `0.434343` | R2.5 / F2 |
| `ci_distinct_candidate_values` | `123` | F7.2 degeneracy telemetry |
| `ci_modal_mass` | `0.212121` | F7.2 |
| `floor_rank` | `234` | F7.2 |
| `floor_tail_depth` | `45` | F7.2 |
| per-group results | the whole of `02` | §7 persistence |
| run cost (embeds, wall-clock) | `23456` embeds, `3456.789` s | D5 / §7 |
| C9/C13 drop diagnostics | the whole of `08` | C9 / C13 |
| C11 probe manifest | 456 `(point_id, probe_text_sha512)` pairs | C11 |
| paired-decomposition floor + surviving-subset size | `0.456789`, `456` | D4 |
| anchored-excluded count | `39` | C2 |
| corpus snapshot counts (file / chunk / per-tier) | `1234` files, `23456` chunks | §7 persistence |
| axis columns (`statistic`, `scope`) on the measurement row | `response_best_cosine`, `SYNTHETIC_SCOPE` | F6 / decision 5 |
| the **LEGACY** instrument's `embedding_schema_fingerprint` | unrecorded — no such value exists | nothing yet; see below |

⚠ **The last row is different from the others and is called out because it is not on anyone's
list.** Every other row above is a column some ruling already requires. The legacy instrument's
fingerprint is required by nothing — and its absence is exactly why `02`'s bound (iii) has to
say the two instruments' scales *cannot be checked* for coincidence rather than *do not*
coincide. A reader cannot verify the premise the package's own comparison rests on. Recording
it, or recording explicitly that it is unrecoverable, is a writer-spec decision this consult
should make.

Everything in that table exists in this package only as prose in these documents. A distinction
the row never recorded is a distinction no later render can serve.
