> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 03 — Verbatim-anchor rates per group

*C6(c). The absence predicate is anchor-gated — it fires on
`max_cosine < floor AND NOT has_verbatim_anchor` — so a group's anchor rate bounds how often
the floor can matter at all in that group.*

## Rate per group (whole group)

| group | anchored | n | rate |
|---|---|---|---|
| `human-prose` | 12 | 123 | `12 / 123` = `0.097561` |
| `human-implementation-vocabulary` | 123 | 234 | `123 / 234` = `0.525641` |
| `synthesized-identifier` | 12 | 15 | `12 / 15` = `0.800000` |
| `self-supervised-answered` | 234 | 456 | `234 / 456` = `0.513158` |
| `hold-out-absent` | 23 | 567 | `23 / 567` = `0.040564` |
| `legacy-nonsense` | 3 | 345 | `3 / 345` = `0.008696` |
| **all** | **407** | **1740** | `407 / 1740` = `0.233908` |

## Where the gate actually bit — the below-floor slice at `F_portable` = `0.456789`

| group | below floor | of those, anchored (verdict suppressed) | absence verdict fired |
|---|---|---|---|
| `human-prose` | 12 | 8 | 4 |
| `human-implementation-vocabulary` | 11 | 4 | 7 |
| `synthesized-identifier` | 0 | 0 | 0 |
| `self-supervised-answered` | 12 | 6 | 6 |
| `hold-out-absent` | 456 | 18 | 438 |
| `legacy-nonsense` | 324 | 3 | 321 |
| **all** | **815** | **39** | **776** |

Answered queries in this run = `1740 − 776` = **964**. That is the denominator `06` uses.

The two human groups' rows here are the same counts `01` reports as the legacy labeled real
union (`12 + 11 = 23` below floor, `8 + 4 = 12` anchored, `4 + 7 = 11` false fires).

These rates are properties of the survey's query mix. A different query mix — production
traffic, for one — would produce different anchor rates and therefore a different rate of
absence verdicts, and this package does not measure that mix.
