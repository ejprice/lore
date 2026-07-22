# 07 — Store error-honesty: CLASSIFICATION (#118, #119, #144) (formerly PKT-30; recovery half → 07a)
size ~0.20 wu · wave L (parallel-safe) · depends: none · sibling: 07a (recovery/degradation)
law: repo CLAUDE.md store-reference law (**READ `docs/reference/surrealdb-31-capabilities.md`
FIRST**) · "a probe needs a control" · fixtures must encode shapes the ENGINE actually emits
(the #119 lesson: pins passed only because their fixtures encoded a shape SurrealDB never
sends) · DEPLOY: yes

## Mission
The error renders lie to the LLM. Every schema-ASSERT violation in production history has
been served as an "unspecified rejection", every rolled-back multi-statement txn misnames
its root cause, and statement[0]-only validation hides retryable conflicts well enough to
have produced a false engine-defect diagnosis (#124). Fix classification at the seam so
served errors teach the truth. (SPLIT 2026-07-22: #128/#164/#126/#127 — the RECOVERY and
degradation half — moved to **07a** when #144+#164 arrived; both halves at ≤0.20 beats one
packet at 0.30+.)

## Scope IN
- **#118** — `_ERROR_CLASS_ASSERT_VIOLATION` greps for the word 'assert' but the engine's
  real ASSERT text says 'must conform to'. Fix the classifier; fixtures are
  PROBE-DERIVED from the live engine (spike-surreal, NOW 3.2.1 — reference §0), not
  authored from memory; positive control = a real ASSERT violation classified correctly,
  negative control = a domain rejection NOT classified as an ASSERT.
- **#119** — `failed_statements[0]` is a CASCADE entry on the live engine, so root-cause
  extraction must skip cascades to the true failing statement. Same probe-derived fixture
  law. #93's pins get re-grounded against real engine shapes in the same pass.
- **#144** (slotted 2026-07-22) — **#124 is MISDIAGNOSED**: the engine does not silently
  lose committed rows; those "successes" were retryable conflicts hidden by `query()`'s
  statement[0]-only validation. Settle the full-statement validation posture (validate
  every statement, or document the accepted bound with a pin), amend #124's row and the
  store reference's account with receipts, and verify the retry classifier sees a
  conflict reported in a LATER statement.

## Scope OUT
- **07a owns**: #164 (reconnect-on-dead-socket), #128 (per-item batch degradation),
  #126/#127 adjudication.
- The `_txn` substring→typed-check swap (#111) — pooled until surrealdb-py 3.0.0 ships.
- Any retry-policy change (the #102 seam is CLOSED; this packet touches classification
  only).

## Entry check
Read the store reference FIRST (repo law) — including §0: the engine is 3.2.1 and 3.1.5
probe labels keep their provenance; every fixture probe here runs on 3.2.1. `lore_findings`
→ #118 #119 #144 states. Probe spike-surreal :18000 for the real ASSERT text, the real
failed_statements cascade shape, AND a conflict surfaced in a non-first statement BEFORE
writing any fixture — commit the probe transcripts as receipts.

## Exit
Full gates + cold audit (error renders are served surface); deploy BOTH; smoke: a live
ASSERT violation on the deployed surface serves its real reason; findings resolved with
notes; INDEX row + Log.
