> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 07 — The determinism control, and the run's provenance receipt

## Leg A — arithmetic determinism (suite pin, unconditional)

Held fixed: a persisted capture set (n = 234 cosines with anchor flags, including a
continuous-statistic sibling), the config tuple (bars, ladder, `B`, `k'`), the
per-`(scope, leg, N)` seed derivation, and the library versions in the venv.

Compared: the ENTIRE derived output — selection triple, `ci_low`/`ci_high`, ladder
`(N, ci_width, agreement)` triples, F2 null-rate and applied gap, sensitivity floor,
degeneracy telemetry, paired decomposition — as identical float64 BYTES, across two in-process
runs AND one subprocess run.

| leg-A check | result |
|---|---|
| two in-process runs, byte-equal on every field | **PASS** |
| subprocess run (hash-seed independence), byte-equal | **PASS** |
| failing control: one `Generator` object reused across both runs must NOT be bit-identical | **PASS** (differed, as required) |

## Leg B — end-to-end reproduction (the verb run twice on the live corpus)

### Pre-conditions, asserted rather than assumed

| pre-condition | run 1 | run 2 | equal |
|---|---|---|---|
| settled-index start/end checks | pass | pass | — |
| `corpus_content_digest` | `fedcba98…3210` | `fedcba98…3210` | ✓ |
| `embedding_schema_fingerprint` | `SYNTHETIC-EXHIBIT-FINGERPRINT-0123456789abcdef` | same | ✓ |
| distinct measurement rows created | `floor_measurement:synthetic0000000001` @ `1234-05-06T07:08:09Z` | `floor_measurement:synthetic0000000002` @ `1234-05-06T09:10:11Z` | ✓ two rows, two ids, two timestamps |

The last row is the anti-vacuity check: two runs that produced one row would have proved nothing.

### The verdict — typed, from the closed three-value enum

## `determinism_leg = within_ci_by_construction`

The three permitted values are `bit_identical_cold`, `bit_identical_via_cache` and
`within_ci_by_construction`. This run recorded the third: **the two runs' derived payloads are
NOT byte-equal.**

Probe-embed cache hits, run 2: **0**. There is no embedding cache in this packet, so
`bit_identical_via_cache` was not available as an outcome and byte-inequality cannot be
explained by a warm cache.

Because bytes differed, both of the following had to hold or the run would have been recorded
`measurement_failed` with a finding:

| required condition | bar | measured | verdict |
|---|---|---|---|
| (i) the two runs are NOT disjoint under the F2-calibrated adoption test — fresh-vs-fresh, no adoption would fire, no flap | `\|Δfloor\|` < F2-calibrated gap `0.010101` | `\|Δfloor\|` = `0.000012` | **PASS** |
| (ii) decision agreement between the two floors over the L1 R-PACKAGE gate population (this run: all 1740 queries) | `≥ 0.98` | `1739 / 1740` = `0.999425` | **PASS** |

### Per-field deltas, run 1 → run 2

| field | run 1 | run 2 | Δ |
|---|---|---|---|
| `floor` | `0.456789` | `0.456801` | `+0.000012` |
| `ci_low` | `0.404040` | `0.404063` | `+0.000023` |
| `ci_high` | `0.505050` | `0.505084` | `+0.000034` |
| sensitivity floor | `0.434343` | `0.434388` | `+0.000045` |
| `adopted_n` | `411` | `411` | `0` |

### What this verdict commits 11-ii to

**The exact-skip scheduler may not rest on byte-reproduction of a measurement.** This run
demonstrates that two runs over a byte-identical corpus produce different derived payloads, so:

1. Change detection must key on `corpus_content_digest` equality — the C10 datum, persisted on
   every row — and on nothing else. Digest equal ⇔ zero chunks added, removed or edited ⇔ skip.
2. Any 11-ii logic that infers "nothing changed" by comparing a fresh floor to the adopted floor
   is invalid: the floors differ run-to-run even when nothing changed.
3. Any 11-ii logic that treats a re-measured floor's difference from the adopted one as evidence
   of corpus drift is invalid for the same reason; the F2-calibrated gap (`0.010101` here) is the
   only threshold that separates noise from a real move.
4. The `bit_identical_cold` outcome is what would license a stricter scheduler. It was not
   obtained, and reporting this run as "deterministic" without the qualifier would license
   exactly the design this run rules out.

## The run's provenance receipt (stdout, both runs)

| field | value |
|---|---|
| `loremaster.__file__` | `/SYNTHETIC/site-packages/loremaster/__init__.py` |
| store URL | `ws://SYNTHETIC-STORE:00000/rpc` |
| namespace | `SYNTHETIC_NS` |
| database | `SYNTHETIC_DB` |
| `LORE_VERSION` | `0.0.0-SYNTHETIC` |
| image digest | `sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef` |
| git commit | `0123456789abcdef0123456789abcdef01234567` |
| git tree dirty | `false` |
| corpus fingerprint | `fedcba9876543210…` (= `corpus_content_digest`) |
| TEI endpoint identity | `SYNTHETIC-ENDPOINT` |
| `scipy` | `0.0.0-SYNTHETIC` |
| `numpy` | `0.0.0-SYNTHETIC` |
| `determinism_leg` | `within_ci_by_construction` |
| probe-embed cache hits | `0` |

All three store coordinates are printed because all three were supplied explicitly; the verb
carries no default coordinate of any kind and refuses to run without one. A `(None, None)` git
identity is a hard refusal, not an empty field — this receipt's git line can never be blank.

### Cost accounting

| item | value |
|---|---|
| `--max-embeds` budget | `34567` |
| embeds used | `23456` |
| budget remaining | `11111` |
| wall-clock | `3456.789` s |
| `retry_on_conflict` attempts | `12` |
| conflicts observed | `3` |
| retry budgets exhausted | `0` |
