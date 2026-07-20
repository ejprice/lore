# DESIGN-102 — FINAL ruling: the hot-row mint retry substrate

brief-base v2 read
design-consultant · 2026-07-12 · status: FINAL. Supersedes `DESIGN-102-preliminary.md`
+ its 2026-07-12 addendum where they conflict (one root-cause layer corrected, §0; all
mechanism verdicts carried forward). Inputs: the sequence probe
(`REPORT-probe-sequence-1.md`), the house capability reference
(`docs/reference/surrealdb-31-capabilities.md`), and the lead's corrected root-cause
receipts — each independently verified against the code below.

---

## 0. CORRECTION I OWN — my preliminary analysed a layer that never runs

My preliminary's §1(2) — the 16-slot birthday-collision math over findings' outer
jitter — described `findings._apply_mint` as a participating layer. **It is dead code.
The outer 12-attempt loop has never executed a single retry.** The lead's receipts
(one `store.transaction.rolled_back` record per failing run, not twelve; 6/10 solo
failures) are confirmed by the mechanism in code:

- The live engine's conflict-rollback shape puts the `"can be retried"` marker ONLY on
  the LAST failed entry (the COMMIT); the earlier entries carry "The query was not
  executed due to a failed transaction" (lead's captured log).
- `_txn.py:550-551` classifies `failed_statements[0]` — the cascade entry — so
  `_classify_engine_error` returns "unspecified rejection" (`_txn.py:359`) for an
  exhausted conflict. (`_is_retryable_conflict` at `:657-670` scans ALL entries with
  `any()`, so the INNER 5-attempt retry fires correctly; only the raised LABEL lies.)
- `findings.py:790` gates its outer retry on `"retryable conflict" in str(error)` →
  the label never matches → immediate re-raise, zero outer attempts, ever.

**Kill chain:** finding #93's fix (root-cause pick `[-1]` → `[0]`) was CORRECT for
domain rejections and SILENTLY flipped the exhausted-conflict label, which killed the
string-gated backstop in findings. The pin at `test_surreal_store.py:2482-2492` stayed
green because its fixture (`_err_response(result_text=_CONFLICT_ENGINE_TEXT)`,
`:2211-2218`) is a SINGLE-entry response with the marker on `[0]` — a shape the live
engine never produces. The builder for the live shape exists
(`_rolled_back_response`, `:2195`); the discriminating fixture value was simply never
written. Fixture monoculture, fourth confirmed instance.

**What survives of my preliminary unchanged — and is now STRONGER:** the failing
system is PURELY the shared seam's 5-attempt, zero-jitter, deterministic linear ladder
(`_txn.py:333,339,549`). Lockstep determinism remains the root cause; the only
desynchroniser today is natural scheduling variance, which loses ~half the time at
8-way. Every Q1 verdict (seam-only retry, per-attempt fresh jitter, deadline budget,
typed error, delete the outer loop) stands — the typed error now ALSO kills the
string-gating failure class that produced the dead backstop.

Historical coherence, for the record: `findings.py:776`'s "the live N=16 concurrent-
mint probe stayed clean" was presumably measured when the loop was LIVE (pre-#93);
the fix killed the loop, the pinned test started failing, and nobody connected the
two. Prose from a retired measurement — the diagnosis-is-not-an-instrument class.

## Final verdict table

1. Retry policy lives in `execute_transaction` ONLY: per-attempt FRESH full jitter
   (process PRNG), exponential w/ cap, deadline budget, generous attempt ceiling as
   runaway backstop, typed `TxnContentionExhaustedError` on exhaustion.
2. Q-A: the retry predicate and the raise classification become ONE predicate over ONE
   witness set — root cause = the marker-bearing entry for conflicts, `[0]` for domain
   rejections (#93 preserved verbatim).
3. Q-B: the typed error subclasses `SurrealStoreError`; three transition/claim handlers
   add a pass-through except; a repo invariant bans control-flow string-matching on
   classification labels (briefs.py grandfathered until its migration finding closes).
4. Q-C: deleting findings' outer loop is deleting dead code; the repaired seam carries
   the mint alone, PROVEN by a committed survey probe whose measurement pins the
   constants — no constant ships without its measurement receipt.
5. Q-D: briefs' backstop is LIVE (different plumbing), NOT the dead-gate bug — but it
   is one label-rewording away from dying the same death. File the finding.
6. Q-E: `message.seq` = `DEFINE SEQUENCE IF NOT EXISTS message_seq START 1` +
   `sequence::nextval('message_seq')` INSIDE the send transaction — the inside-the-txn
   ban is hereby restated precisely: it binds CONTENDED ROWS, not lock-free sequences.

---

## Q-A. The classification fix — the precise rule

**Rule: the entry you classify is the entry that made you decide.** The retry decision
and the exhaustion report must share one witness. Concretely, in
`execute_transaction`'s post-loop path:

1. **Conflict case:** if `_is_retryable_conflict(failed_statements)` is True (the
   UNCHANGED `any()` scan, `_txn.py:657-670`) and the budget/deadline exhausted →
   raise `TxnContentionExhaustedError` directly. No string label participates in the
   decision. The root-cause entry for the server-side log is the FIRST entry whose
   raw text carries `_RETRYABLE_CONFLICT_MARKER` (in the live shape, the COMMIT entry
   — its ordinal is honest: "statement N of N").
2. **Domain case:** `_is_retryable_conflict` is False → finding #93 verbatim, not
   regressed by one character: root cause = `failed_statements[0]` (statements run in
   order; everything before the first ERR succeeded; later ERRs are cascade), classify
   via `_classify_engine_error`, raise `SurrealStoreError` with the generic label +
   `_SERVER_LOG_HINT`. The `:2367/:2414/:2431` pins stay green untouched.

Why positional selection is banned outright: the engine writes domain root causes
FIRST (cascade after) but conflict evidence LAST (non-execution noise before). Neither
`[0]` nor `[-1]` can be right for both — the selector must be semantic (marker
presence), never positional.

**Implementation shape (derive-don't-restate applied to control flow):** fold the
decision into ONE function — `_rollback_verdict(failed_statements) -> (is_conflict,
root_cause_entry)` — consumed by BOTH `_should_retry` and the post-loop raise. Two
call sites, one witness; the #93-class divergence (retry sees all entries, label sees
one) becomes structurally impossible.

**`_classify_engine_error`'s marker-first branch (`_txn.py:404-405`) is RETAINED** —
it is load-bearing on the single-statement `_query` path today (briefs.py:508 → :674,
see Q-D). It may retire only after briefs migrates. Its docstring's claim
(`_txn.py:399-402` — "checked FIRST since a sustained conflict must still be reported
as a conflict") is VACUOUS on the txn path (entry `[0]` never carries the marker) and
must be rewritten with the repair — prose-lies instance #4 in this file family.

**Test-double correction (feeds the contract author):** the sustained-conflict pin
must run against the LIVE shape — `_rolled_back_response("The query was not executed
due to a failed transaction", "The query was not executed due to a failed
transaction", _CONFLICT_ENGINE_TEXT)` (marker ONLY on the last entry) — and keep the
current single-entry marker-on-`[0]` variant as the SECOND value (parameter-diversity
law: if the code can branch on position, pins must cover both positions). Mutation
proof: point the verdict at `[0]`-only classification and watch the live-shape pin go
red; it is green today precisely because the fixture cannot see the difference.

## Q-B. The typed-error seam + the label's full blast radius

**Shape confirmed:** `class TxnContentionExhaustedError(SurrealStoreError)` in
`_txn.py`. Every existing `except SurrealStoreError` still catches it (no silent
behaviour change anywhere); message carries attempts + elapsed + the generic conflict
label, never engine text (ledger #31 held). It is OURS to mint — the capability
reference `:98-102` confirms the engine offers no typed conflict error, only the
marker; the seam boundary is exactly where marker-text becomes type.

**Complete consumer table for the label/marker (grepped bare, every hit verdicted):**

| site | verdict |
|---|---|
| `findings.py:790` (+ import `:93`, prose `:253-256`, `:762`, `:771-776`) | DEAD gate — deleted with the loop (Q-C), constants and 12×5 docstring included |
| `findings.py:1058` (transition rollback handler) | needs `except TxnContentionExhaustedError: raise` ABOVE it — exhaustion must never be re-read and misreported as a lost CAS / `IllegalTransitionError` |
| `tasks.py:875`, `tasks.py:1139` (claim + transition rollback handlers, same clone) | same one-line pass-through, same reason; otherwise UNCHANGED — their CAS rollbacks are domain THROWs the seam never retries |
| `briefs.py:674` (+ import `:107`, prose `:595`, `:633-634`) | LIVE gate on the single-statement path — READ-ONLY, untouched by #102; see Q-D finding |
| `briefs.py:604`, `:715`, `:944` | rollback handlers on publish/release — safe (subclass), inherit the pass-through when briefs migrates |
| `test_surreal_store.py:2491` | pin re-shaped: assert the TYPED class + the live fixture shape (Q-A above) |
| `test_surreal_store.py:2367`, `:2414`, `:2431` | #93 domain pins — must stay green UNTOUCHED |
| `tests/_surreal_harness.py:99`, `:266-267` + `test_surreal_harness.py` | raw-MARKER consumers (teardown REMOVE retry) — independent of the label, untouched |
| `memory/local.py:757` | prose mention only, no dependency |

**New repo invariant (instrument, not law-only):** production code must not make a
control-flow decision by substring-matching a classification label against an
exception message. Pin it mechanically — a grep/AST scan over `loremaster/` for
`_ERROR_CLASS_RETRYABLE_CONFLICT` (and the bare label string) used inside an `except`
body, with `briefs.py:674` as the single named, expiring exemption. This is the
instrument the #93→#102 kill chain lacked; the typed error makes the correct thing
also the easy thing.

## Q-C. Deleting findings' outer loop — safe, and what must be pinned

**Deletion is safe because it is dead code** (receipts in §0 — it never ran once).
Nothing that currently passes can be depending on it. Delete: the loop
(`findings.py:781-794`), `_apply_mint` itself (report() calls `_apply` directly), the
four `_REPORT_MINT_*` constants (`:253-256`), the label import (`:93`), and the
12×5=60 docstring narrative (`:244-256`, `:754-776`) — orphaned prose describing a
mechanism that never ran is precisely the served-English class the last audit caught
ten of.

**But deletion + repair must be proven to carry the mint alone — by measurement, not
assertion** (#102 was born from a 2-way-tuned constant nobody re-measured; I will not
mint its successor by hand-wave):

1. **Committed survey probe** (sibling of `scratchpad/probe_sequence_txn_concurrency.py`,
   kept in the repo): drive the REPAIRED `execute_transaction` on the real findings
   mint fragment against spike-surreal at N ∈ {2, 8, 16, 32} × 50 rounds; record
   per-mint attempt counts + wall latency; report weighted percentiles. The attempt
   distribution must show no lockstep signature (no multi-modal clustering at the
   attempt ceiling).
2. **Constants pinned FROM the measurement, with the receipt in the commit:**
   - jitter: full jitter, `uniform(0, min(CAP, BASE·2ⁿ))`, redrawn EVERY attempt from
     the process PRNG. BASE = 5 ms, CAP = 100 ms are the probe's STARTING values; they
     ship only if the probe's percentiles endorse them.
   - deadline default: ≥ 10× the measured N=32 p99. Prediction: p99 ≈ 0.7 s → the
     2.0 s default holds; if the measurement disagrees, the NUMBER moves, not the
     method. Callers pass nothing (kwarg exists for C2 if its own measurement says so).
   - attempt ceiling 64: NOT a tuned constant — a structural runaway backstop against
     near-zero early sleeps spinning inside the deadline; logged when hit; requires no
     measurement, only the stated rationale at the constant.
3. **Gates:** the 8-way pinned test (contract floor per house law) + one 32-way case;
   **20 consecutive greens under `-n auto`** (a single green never clears a
   concurrency test); **mutation proof** — revert the jitter to deterministic linear
   and watch the 8-way pin go red (a pin that cannot be shown failing is not a pin).
4. The seam's docstring derives its numbers by NAMING the probe file and run — prose
   derived from behaviour, never re-stated beside it.

## Q-D. briefs.py — NOT the dead-backstop bug; file the finding anyway

**Verdict: briefs' backstop is LIVE.** Its plumbing differs decisively from findings':
the bump is a SINGLE statement via `_query` (`briefs.py:663-668`), so a conflict
surfaces as the SDK exception whose full text carries the raw marker; briefs' `_query`
(`:493-508`) classifies the WHOLE exception → `_classify_engine_error`'s marker-first
branch fires → the raised message says "(retryable conflict)" → the gate at `:674`
matches → the 20-attempt loop actually retries. This — not my preliminary's
"accident of window size" alone — is why it holds 20/20: twenty LIVE attempts of a
tiny statement. (The tiny conflict window and natural variance still help; they are
no longer carrying the whole load.)

**File the finding (recommended text, one finding, three coupled points; I do not
touch the file):**
1. The gate is control-flow string-coupled to the classification label — the exact
   mechanism that silently killed findings' backstop. One label rewording, or routing
   the bump through `execute_transaction`, kills it with ZERO test signal.
2. Jitter: 4 slots (`:159-162`), fixed per call (`:661`) — pigeonhole guarantees
   shared slots at ≥5-way and lockstepped pairs across all 20 attempts.
3. Remedy when the file is next legitimately open: ride the repaired shared
   conflict-retry (factor the retry helper so single-statement callers can use it),
   delete the hand-rolled loop + label import, inherit the typed error.

**Sequencing dependency (binding on #102's builder):** `_classify_engine_error`'s
marker-first branch and the "(retryable conflict)" label are LOAD-BEARING for
briefs.py until that finding closes. #102 must not reword the label or remove the
branch. State this in the repair's commit message.

## Q-E. C2 `message.seq` — final recommendation

**DDL** (in the message schema slice, applied at `ensure_ready` — schema strictly
before first write; the probe's orphan engine bug, concurrent first-ever CREATE on an
undefined table silently losing rows, makes DEFINE-first a stated precondition, which
house schema application already satisfies):

    DEFINE SEQUENCE IF NOT EXISTS message_seq START 1;

- `START 1` explicit: probe says default START 0 → first handle would be #0; human
  handles start at #1 (findings parity).
- `BATCH`: leave the engine default (1000) and DOCUMENT it — "a server restart may
  skip up to BATCH numbers; gaps are legal and of unbounded width." Do NOT tune BATCH:
  gaps are pre-accepted verbatim in the plan, so tuning gap width is minting a new
  unmeasured constant to optimise a non-requirement. Revisit only with a measurement
  and an actual requirement.

**Mint call — INSIDE the send transaction:**

    LET $msg_seq = sequence::nextval('message_seq');
    CREATE type::record('message', $msg_id) CONTENT { seq: $msg_seq, … };
    RELATE …->to->…  (fan-out edges, same BEGIN…COMMIT)

**Placement ruling, revised with the probe and restated precisely:** my preliminary's
ban — "never mint inside the fan-out txn" — binds **contended rows**, not sequences.
A counter ROW inside the fan-out makes the entire message+N-edge write the conflict
window; a native sequence is lock-free and allocates non-transactionally — the probe
MEASURED zero conflict markers at 16-way×30 transactions, 5/5 runs, with the mint
inside BEGIN…COMMIT. So the sequence mint goes inside: atomic message+edges, no
reserve step, no compensation, and an aborted send burns a number (accepted verbatim).
The ban survives as C2 design law in its precise form: **no contended row is written
inside a fan-out transaction** — which also pre-bans any future "stats row" update
smuggled into send. The reserve-then-create fallback is RETIRED (probe surprise did
not occur; the name is `nextval`).

**C2 contract pins (feeding the Opus author + adversary):**
1. 32-way × 100 concurrent sends → all `seq` distinct, zero errors (the probe's own
   measured shape); `UNIQUE` index on `seq` as the schema backstop (already planned).
2. Fresh-db first mint == 1 (pins START 1 + first-boot seeding — the 3.1.0-beta.3
   regression class).
3. A send forced to roll back AFTER `nextval` (e.g. a THROW later in the txn) burns
   the number: the next successful send carries a HIGHER, NON-consecutive seq, and the
   pin asserts the GAP IS LEGAL. Doubles as branch-reachability for the abort path.
4. ANTI-pin (adversary's checklist): no test may assert consecutiveness/gaplessness of
   `seq` — a suite green-because-consecutive-in-practice would silently promote a
   non-promise into a contract.
5. Name smoke at `ensure_ready`: `sequence::nextval` exists; `sequence::next` fails
   with the parse error naming nextval — an engine upgrade that renames it fails loud
   at boot, not mid-send.
6. `since=<seq>` cursors BANNED (sequence values commit out of allocation order —
   delivery state rides to-edge `seen_at` stamps, garden plan ~:218; CHANGEFEED is the
   engine-native tool if ordered replay is ever required, capability ref `:64-69`).
7. The send transaction still rides `execute_transaction` (edges, CAS stamps,
   `set_status`) → the Q1 repaired seam + `TxnContentionExhaustedError` + the
   no-string-label invariant are C2 prerequisites, inherited wholesale.

## Residual flags (cumulative, superseding the preliminary's §6)

1. briefs.py finding — Q-D above (file it; includes the label-retirement sequencing).
2. Prose-contradicts-mechanism instances to fix WITH the repair, now four:
   `_txn.py:336-339` (backoff "prevents" the lockstep it guarantees);
   `_txn.py:399-402` (marker-checked-"FIRST" vacuous on the txn path);
   `findings.py:771-776` (12×5=60 worst case of a loop that never ran, + the stale
   "N=16 stayed clean" claim); `findings.py:244-256` (the whole hand-rolled-backstop
   rationale block). All die with the deletion or are rewritten derived-from-behaviour.
3. Fixture law receipts for the contract author: the live conflict shape
   (`_rolled_back_response` with marker ONLY last) is MISSING from every conflict
   fixture; `test_surreal_store.py:2482-2492` is green for the wrong reason. Both
   marker positions must be covered; the sustained-conflict pin must be
   mutation-proven against the `[0]`-classifier.
4. The probe's orphan engine bug (concurrent first-CREATE on an undefined table loses
   rows silently) — production not exposed (schema applied first), but it belongs in
   the capability reference's gotchas so the next schema author inherits it. Flag for
   the operator: a one-line doc edit outside my writable set.
