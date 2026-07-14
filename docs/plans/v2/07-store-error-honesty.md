# 07 — Store error-honesty (#118, #119, #128) (formerly PKT-30)
size ~0.20 wu · wave L (parallel-safe) · depends: none
law: repo CLAUDE.md store-reference law (**READ `docs/reference/surrealdb-31-capabilities.md`
FIRST**) · "a probe needs a control" · fixtures must encode shapes the ENGINE actually emits
(the #119 lesson: pins passed only because their fixtures encoded a shape SurrealDB never
sends) · DEPLOY: yes

## Mission
The error renders lie to the LLM. Every schema-ASSERT violation in production history has
been served as an "unspecified rejection", every rolled-back multi-statement txn misnames
its root cause, and one contended row kills a whole batch verb. Fix classification at the
seam so served errors teach the truth.

## Scope IN
- **#118** — `_ERROR_CLASS_ASSERT_VIOLATION` greps for the word 'assert' but SurrealDB
  3.1.5's real ASSERT text says 'must conform to'. Fix the classifier; fixtures are
  PROBE-DERIVED from the live engine (spike-surreal), not authored from memory; positive
  control = a real ASSERT violation classified correctly, negative control = a domain
  rejection NOT classified as an ASSERT.
- **#119** — `failed_statements[0]` is a CASCADE entry on the live engine, so root-cause
  extraction must skip cascades to the true failing statement. Same probe-derived fixture
  law. #93's pins get re-grounded against real engine shapes in the same pass.
- **#128** — server.py's batched finding resolve/acknowledge: TxnContentionExhaustedError /
  SurrealStoreError on one item must degrade PER-ITEM (best-effort contract the verbs
  already promise), never kill the whole batch response. Concurrency pin under real
  contention (20-consecutive law).
- **#126 / #127 adjudication**: fix-or-acknowledge-with-named-reopen-trigger, each with a
  written verdict (both are latent-by-design today; the verdict is the deliverable, a fix
  only if the verdict says so).

## Scope OUT
- The `_txn` substring→typed-check swap (#111) — pooled until surrealdb-py 3.0.0 ships.
- Any retry-policy change (the #102 seam is CLOSED; this packet touches classification
  and batch degradation only).

## Entry check
Read the store reference FIRST (repo law). `lore_findings` → #118 #119 #128 open. Probe
spike-surreal :18000 for the real ASSERT text and the real failed_statements cascade shape
BEFORE writing any fixture — commit the probe transcripts as receipts.

## Exit
Full gates + cold audit (error renders are served surface); deploy BOTH; smoke: a live
ASSERT violation on the deployed surface serves its real reason; findings resolved with
notes; INDEX row + Log.
