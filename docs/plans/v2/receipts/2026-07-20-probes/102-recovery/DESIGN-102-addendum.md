# DESIGN-102 addendum — post-audit rulings: deadline semantics, dead marker, positional selection

> **SUPERSEDED — DATED RECORD.** This is the #102 design record as written in July 2026,
> archived at `1666856` under the archive-don't-delete law (`968883d`, #153). It is preserved
> as EVIDENCE of the reasoning of its time, not as a description of the code today.
> Retired symbols it names, which NO LONGER EXIST: `_apply_mint`, `_TXN_CONFLICT_BACKOFF_SECONDS`.
> The retry substrate shipped at `9d29111`; read `loremaster/store/_txn.py` for what is real.


brief-base v2 read
design-consultant · 2026-07-13 · status: FINAL for the three audit questions + R14.
Inputs: `REPORT-audit-102.md` (read in full, residuals table included), the built loop
(`_txn.py:744-771`), the live captures in `scratchpad/audit/probe_shapes.py` /
`probe_domain_live.py`. Supplements `DESIGN-102-final.md`.

## Verdict table

1. **R1 (B1):** candidate **(a) — attempt floor**, with FLOOR = the existing
   `_MAX_TXN_CONFLICT_ATTEMPTS` (5). Zero new constants; the pre-#102 five-attempt
   guarantee is restored BY CONSTRUCTION. Exact predicate below. (b) rejected: its
   worst case (64 × 9.56 s ≈ 10 min) is indefensible and needs a NEW bounding
   constant; (c) rejected: it scales off a noisy measurement (1.78/1.96/9.56 s — 5×
   variance across three runs of the SAME apply).
2. **R2 (B2):** marker becomes `"must conform to"` (REPLACING `"assert"`, not
   appending). The real deliverable is the INSTRUMENT: a live-engine classification
   suite — every `_ERROR_CLASS_*` marker ships with a [real]-tier pin that PROVOKES
   its class against spike-surreal, plus cross-controls. A marker without a
   provocation pin is presumed fiction.
3. **R3 (B3):** the domain selector becomes semantic — root cause = the FIRST failed
   entry whose text is non-empty and carries NO cascade marker; degrade to the LAST
   entry when every entry is cascade. Composes into `_rollback_verdict` as one
   three-way witness. #93's pins are rewritten to live-captured shapes; finding #93
   itself gets superseded in the ledger.
4. **R14:** the unit pins are SUFFICIENT. The live 8-way gate guards the contract,
   not the mechanism; do NOT make it jitter-sensitive, add NO symmetry pin. The
   survey probe gains a deterministic-backoff comparison arm as the honest live
   instrument — a measurement artifact, not a per-commit gate.

---

## Ruling 1 — deadline semantics (B1, the blocker)

### What the deadline is actually FOR — and what it was never for

The deadline bounds the **latency cost of contention resolution in the fast-txn
regime** — the regime where retries are numerous and cheap and an attempt count is a
meaningless proxy (the original #102 analysis). It was NEVER a bound on total call
latency: the caller's FIRST attempt is not the retry policy's to ration — a clean
9.56 s bulk apply takes 9.56 s with no retry policy involved at all. B1 happened
because the implementation let the deadline ration exactly that: the caller's own
execution time. A budget cannot meaningfully govern spend that happens before the
first decision it makes.

Two regimes, two meaningful guarantees:
- **Fast txn (ms attempts):** wall-clock deadline is the right budget — 2.0 s ≈ 45×
  the measured N=32 p99 (audit's survey reproduction). Unchanged.
- **Slow txn (seconds/attempt):** a wall-clock budget smaller than one attempt is
  incoherent as a retry budget; the meaningful guarantee is ATTEMPTS — which is
  precisely the pre-#102 contract (5, regardless of wall time) that B1 regressed.

One predicate covers both regimes with zero new constants:

### The exact give-up predicate

```python
# evaluated AFTER the attempt, BEFORE any sleep (as built — audit R3: bounded
# overshoot of one backoff + one round-trip, verdicted acceptable):
give_up = (
    attempt >= _TXN_CONFLICT_ATTEMPT_CEILING
    or (elapsed >= deadline and attempt >= _MAX_TXN_CONFLICT_ATTEMPTS)
)
```

The deadline may only cut retries AFTER the floor is met. Never sleep into a doomed
raise (preserved from the built shape).

### Constants, each with its justification (the #102 trap, honoured)

| constant | value | justification — kind of evidence |
|---|---|---|
| FLOOR = `_MAX_TXN_CONFLICT_ATTEMPTS` | 5, UNCHANGED | **Not a tuned constant — it IS the pre-#102 behavioural contract**, i.e. the non-regression baseline itself. Five attempts sufficed for every caller for the repo's entire pre-#102 life, and the audit's R11 measures 2-way p99 = 2 attempts — 2.5× headroom. Constraint 1 is satisfied for free: same name, same value, `briefs.py:108/:178` untouched; the constant gains the honest role "guaranteed attempt floor" and its docstring is rewritten to say so (derived-from-behaviour). |
| deadline default | 2.0 s, unchanged | Measured: 45× N=32 p99 (survey, audit-reproduced 2900 mints / 0 exhaustions). |
| ceiling | 64, unchanged | Structural runaway backstop; audit R4 verdicts both the mechanism and its prose honest. |

**Worst cases, stated so nobody re-derives them wrong:** fast regime — ~deadline +
one backoff + one RTT (unchanged). Slow regime — FLOOR × attempt-duration + 4 sleeps
(the 9.56 s apply: ≈ 48 s under sustained conflict), which is EXACTLY the pre-#102
worst case: non-regression by definition, not by tuning. Changing that envelope is
out of #102's scope and would need an operator ruling plus a measurement.

### Per-call deadline?

The PARAMETER stays per-call (`deadline_seconds`, exists today); the DEFAULT stays
global; **no call site overrides it now.** With the floor in place, slow transactions
need no override — and 16 sites each minting a bespoke unmeasured deadline is the
#102 trap multiplied by 16. A site earns an override only with its own measurement.

### The pins (the fixture family B1 exposed as non-discriminating)

The audit named it exactly: no fake in the deadline family has non-zero attempt
duration. Required pins, all against a fake whose `query_raw` actually takes time:

1. **Slow-attempt sustained conflict** (attempt duration > deadline): exactly FLOOR
   attempts, then `TxnContentionExhaustedError` with `attempts == FLOOR`. (The
   audit's `probe_deadline_defect.py` CASE 1, promoted to a pin.)
2. **The regression's exact shape:** slow attempt, conflict on attempt 1, success on
   attempt 2 → MUST SUCCEED (this is what broke `test_surreal_apply.py`).
3. Fast-fake family kept as the positive control (deadline governs, ~34 attempts).
4. **Invariant pin:** the typed error can NEVER carry `attempts < FLOOR`.

Mutation proof: revert the predicate to `elapsed >= deadline` alone → pins 1 and 2 go
RED. A deadline pin whose fakes are all instant is decoration — that is the lesson B1
adds to the fixture law.

## Ruling 2 — the dead ASSERT marker (B2)

### The fix

`_ASSERT_VIOLATION_MARKER = "must conform to"` — bare, anchor-free, case-insensitive
membership as today; the substring is the live 3.1.5 capture's own text
(`probe_classifier_control.py`: "…but field must conform to: …"). **Replace
`"assert"`, do not append it**: a marker that has never matched real engine output
documents a fictional engine; keeping it would assert, without evidence, that some
path says "assert". If a future engine version says it, the instrument below will
tell us — loudly.

### The instrument (the actual ruling — the marker is just the fix)

**Standing rule: a classifier marker ships only with a live-engine pin that provokes
its class; a marker without a provocation pin is presumed fiction.** Concretely, a
[real]-tier classification suite against spike-surreal that:

1. **Provokes each class** through the real seam: an ASSERT breach (schema-violating
   write) → asserts label `assert violation`; a type-coercion failure → `field
   coercion`; the retryable conflict is already live-pinned by the concurrency
   family; query-too-complex (#66) provoked via the recursion-depth shape (mark slow
   if costly — but it must exist; #66's own probe file is the recipe).
2. **Cross-discriminates** (the probe-needs-a-control law): each provocation asserts
   its OWN label AND the absence of every sibling label. This specifically proves
   `"must conform to"` does not also live in the coercion text — the collision that
   would silently merge two classes.
3. **Feeds the unit fixtures**: every scripted-fake engine text used by unit pins is
   DERIVED from a live capture and carries a provenance comment (engine version,
   capture date, probe file). Never typed from memory — the `_SENSITIVE_ENGINE_TEXT`
   fixture that said "assertion" is #107's lesson verbatim: the fixture encoded a
   believed engine, and the belief was wrong for the repo's entire life.

Version-coupling is a FEATURE: an engine upgrade that rewords its error text should
fail this suite at gate time (exactly like the `nextval` name smoke), not silently
degrade every label to "unspecified rejection" for another six months.

Constraint check: the retryable label and the marker-first branch are untouched;
briefs.py's gate keys only on the retryable label — unaffected.

## Ruling 3 — the semantic domain selector (B3)

My Q-A ruling said "positional selection is banned outright… the selector must be
semantic, never positional" — and then grandfathered `[0]` for the domain branch on
#93's authority. **#93's premise is false on the live engine** (audit capture:
pre-offender entries are `ERR` "not executed due to a failed transaction", not `OK`).
The ban now applies to both branches, no exemptions.

### The precise rule (one three-way witness in `_rollback_verdict`)

```
_rollback_verdict(failed_statements) -> (kind, root_cause_entry)

1. CONFLICT  — any entry carries _RETRYABLE_CONFLICT_MARKER
               → (CONFLICT, first marker-bearing entry).        [UNCHANGED —
               audit-confirmed correct and genuinely discriminating]
2. DOMAIN    — root cause = the FIRST entry whose raw text is non-empty AND
               carries NO cascade marker. First-in-order because statements run
               in order: the earliest SUBSTANTIVE rejection is the root; anything
               substantive after it is downstream of a already-doomed txn.
3. DEGRADE   — every failed entry is cascade/empty → (DOMAIN, LAST failed
               entry), which classifies to "unspecified rejection". Honest: no
               substantive engine text exists; the last entry (the COMMIT abort)
               is the engine's own final word. This PRESERVES the existing
               all-cascade pin's observables (test_surreal_store.py:2420-2432 —
               "statement 3 of 3", "unspecified rejection").
```

**Cascade markers — live-captured, with provenance, never typed from memory** (the
Ruling-2 instrument applies to these too). From `probe_shapes.py`'s capture the two
bare substrings are:
- `"was not executed due to"` — covers BOTH observed non-execution notices ("…a
  failed transaction" before the offender, "…a cancelled transaction" after it);
- `"aborted due to a prior error"` — the COMMIT abort notice.

The builder pins the exact strings from the capture run, not from this document —
this document is prose, and prose is not an instrument.

Note the conflict branch runs FIRST, so a "Cannot COMMIT: Transaction conflict …
can be retried" entry is claimed by branch 1 before the abort-notice marker could
ever misread it. Ordering inside the verdict is load-bearing; say so at the code.

### What happens to #93

- **Its INTENT survives, corrected:** "name the root cause, not the last cascade"
  becomes "name the earliest SUBSTANTIVE entry". Its IMPLEMENTATION (`[0]`) retires.
- **Its pins are REWRITTEN to live shape, fixtures derived from real captures**
  (`probe_shapes.py` output → fixture constants with provenance comments). Three
  fixture shapes, minimum — position diversity per the fixture law:
  1. offender is the FIRST statement (substantive at index 0 — no preceding cascade;
     a legal live shape, keeps the selector honest at the boundary);
  2. offender mid-transaction, preceding `ERR` cascades + following "cancelled" +
     abort — **the discriminating shape: a `[0]`-picker MUST fail it** (mutation
     proof: re-point the selector at `[0]`, watch it go red; also `[-1]` → red).
     The pin asserts the LABEL and the ORDINAL (the audit's live case: the raise
     said "statement 2 of 4" when the offender was statement 3 — the ordinal is
     part of the served surface and part of the pin);
  3. the all-cascade degrade shape (existing pin's observables preserved).
- **The ledger row:** finding #93 gets superseded/annotated — the corrected rule and
  the false-premise receipt go in the row, so no future session resurrects `[0]` or
  `[-1]` from the old finding text. Operator/lead item.

### Composition check

Yes — one witness, still: the retry decision reads `kind == CONFLICT`; the raise
reads `(kind, root_cause_entry)`; the server-side log names the same entry. The
#93-class divergence (retry sees all entries, label sees one) remains structurally
impossible, and B3's disease (a semantically wrong pick shared consistently) is now
cured at the selector, the only place it can be.

## R14 — is the jitter's guard sufficient? YES. Do not touch the live gate.

Honest answer, as requested: **the three unit pins are the correct and sufficient
guard; the live 8-way gate must NOT be made jitter-sensitive; no pin is added.**

- The live pin guards the CONTRACT (distinct, consecutive numbers, zero failures at
  8-way). Jitter is MECHANISM, not contract. That the contract holds at N=8 even
  under lockstep mutation is not a gap in the gate — it is headroom the deadline +
  ceiling bought, and headroom is the point.
- A live gate that discriminates jitter would have to fail RELIABLY under the
  lockstep mutation. The audit measured 5/5 green at 8-way; pushing N until lockstep
  fails probabilistically would create a flaky mutation instrument — and a mutation
  proof that sometimes passes teaches people to ignore red. The house law is that a
  pin must be DEMONSTRABLY red under its mutation; a probabilistic red fails that
  bar by construction.
- The mechanism's guard is real: all 3 unit pins proven RED under the lockstep
  mutation (audit receipt, `mutate_lockstep.py`: 3 failed / 24 passed). That is the
  strongest deterministic instrument available for a randomised mechanism.
- **The honest LIVE instrument for "does jitter matter" is the survey probe, not a
  gate:** add a deterministic-backoff comparison arm to
  `survey_txn_contention_102.py` (same N ladder, backoff reverted, side-by-side
  attempt distributions). Run at phase checkpoints. If that arm ever shows lockstep
  exhaustion or ceiling-clustering at N=32, the 32-way case has BECOME a natural
  jitter-sensitive gate and gets promoted on that measurement — not before, and not
  for symmetry.

## Flags (surfaced, not fixed — owners named)

1. **B4/P6 is the most dangerous residual in the audit**: `DESIGN-LAW.md:75` (+ the
   2026-07-10 receipt doc) still names the DELETED `findings.py::_apply_mint` — whose
   id-derived deterministic jitter IS the #102 defect — as "the reference pattern for
   any new hot-row minting". That line will actively teach the next agent to clone
   the bug. Outside my writable set and outside the diff; operator item, urgency
   above its B4 grouping.
2. Finding #93 ledger row supersession (Ruling 3) — lead/operator item.
3. Audit R12: the "3 log-capture tests fail under parallel" known-open note did not
   reproduce across three full-suite runs — stale; whoever owns the known-opens list
   should retire it before it excuses a real failure.
4. Constraint tension R8 stands as designed: `briefs.py:677` remains the single named
   message-branch exemption until finding #108 closes — unchanged by these rulings.
