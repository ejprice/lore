> **SYNTHETIC EXHIBIT — no value in this document is a measurement**

# 08 — Probe drops by cause, and the validity floors

*C13 (the self-retrieval match key) and C9 (the empty absent leg). Every drop below is dropped
AND counted — no probe is silently discarded, and no dropped probe contributes a synthetic
`0.0`.*

## Self-retrieval drops — the `self-supervised-answered` pool (n = 456)

A probe self-retrieves when the probe's own SOURCE CHUNK appears in the `k' = 30` hit capture,
matched on **`point_id` equality**. It is a drop when it does not.

| cause | dropped | rate |
|---|---|---|
| `source_chunk_absent_from_kprime` — the source chunk was not retrieved anywhere in the top `k'` | 23 | `23 / 456` = `0.050439` |
| `sibling_chunk_same_file_only` — a DIFFERENT chunk from the same file was retrieved; the source chunk was not | 12 | `12 / 456` = `0.026316` |
| `holdout_file_exclusion_applied` — the probe ran under the file-scoped hold-out exclusion, so its source chunk was structurally unreachable | 10 | `10 / 456` = `0.021930` |
| **total self-retrieval drop** | **45** | `45 / 456` = **`0.098684`** |

Gate: the run is recorded `measurement_failed` if the self-retrieval drop rate exceeds **20%**.
`0.098684 ≤ 0.20` — **PASS**.

Surviving probes: `456 − 45` = **411**. That is the `adopted_n` written to the row in `05` — the
ACTUAL surviving count, not a nominal ladder rung.

**Why the match key is stated.** The 12 `sibling_chunk_same_file_only` drops are exactly the
probes a file-path match key would have scored as self-retrieval HITS. Under path matching this
run would have reported `33 / 456` = `0.072368` instead of `0.098684` — a drop rate understated
by a quarter, against a 20% gate. Self-retrieval is CHUNK-scoped; the hold-out exclusion is
FILE-scoped; the two scopes differ by design and are not interchangeable.

## Absent-leg drops — the `hold-out-absent` pool (n = 567)

The absent leg takes, per probe, the max cosine over the first `k` of the NON-source hits in the
`k'` capture. A probe whose `k'` hits ALL came from its own source file contributes NO absent
sample.

| cause | dropped | rate |
|---|---|---|
| `kprime_all_hits_from_source_file` | 34 | `34 / 567` = `0.059965` |
| **surviving absent samples** | **533** | — |

The `MIN_ABSENT_SAMPLES` floor is evaluated AFTER these drops, on 533, not on 567.

## Identifier pool

15 probes, 0 drops, 15 surviving. The pool is the first 15 identities in ascending
`sha512_hex(identity)` order, so a single corpus insertion changes membership by at most one.

## Validity floors, evaluated on post-drop counts

| floor | required | this run | met |
|---|---|---|---|
| `MIN_ANSWERED_PROBES` | 30 | 411 | ✓ |
| `MIN_IDENTIFIER_PROBES` | 15 | 15 | ✓ (at the floor) |
| `MIN_ABSENT_SAMPLES` | 30 | 533 | ✓ |

Had any of the three failed, the run would have been recorded `insufficient_corpus` and no head
would have been adopted.

## The probe manifest and the paired decomposition

The row persists a probe manifest: **456** `(point_id, probe_text_sha512)` pairs over the run's
answered pool, written in the same row-write as the measurement.

Within each run, the paired-decomposition check compares the floor computed over the surviving
manifest subset against the floor computed over the full pool:

| run | surviving subset | full pool | equal | paired floor | full floor | equal |
|---|---|---|---|---|---|---|
| 1 | 456 | 456 | ✓ | `0.456789` | `0.456789` | ✓ |
| 2 | 456 | 456 | ✓ | `0.456801` | `0.456801` | ✓ |

Run 2's surviving subset is the full pool because the corpus digest was unchanged between the
runs (`07`). The paired equality is a WITHIN-run identity; it says nothing about run 1 and run 2
agreeing with each other, which is `07`'s question and has a different answer.
