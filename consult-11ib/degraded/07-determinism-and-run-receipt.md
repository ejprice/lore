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

The verb was run twice on the live corpus. Both runs' settled-index start/end checks passed.

**Determinism: deterministic.**

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
| determinism | `deterministic` |

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
