# REPORT — adversary-07 (CONTRACT-ADVERSARY, packet 07: store error-honesty)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — the core invariants are STRONG (every plausible-wrong
  build I threw at the runtime leg died), but a **routing-is-not-sharing clone survives the
  whole contract** (F0), and the removed-behavior inventory is materially wrong (F1).
- **P1 HEADLINE — a wrong build SURVIVES:** `inline_predicate` (a runtime multi-statement
  check that clones the `;`-logic instead of calling the shared `_assert_envelope_integrity`)
  passes all 6 runtime-leg tests [REPRODUCED, scratch]. It defeats ONE-IMPLEMENTATION *and*
  silently breaks the `;`-in-literal known-bound re-open trigger, which is keyed on the
  runtime leg. This is the #102/#120 class, reproduced inside the contract meant to consolidate.
- **P1 (the rest): reference build satisfies 8/8** (satisfiability receipt); wrong builds
  `only_escapes`(3F), `keys_on_begin`(2F), `all_query`(1F), `ignore_method`(1F) — **all killed.**
- **Quantifier table §A · Reach table §B** (below). **P-PKG:** agree with author — SDK ships no
  statement splitter (`sql_adapter.SqlAdapter` is a naive `.split(";")` joiner); bespoke + reuse
  `_assert_envelope_integrity` is sound.
- **MISSING PINS:** F0 (predicate-sharing not mutation-proven — BLOCKER) · F5 (runtime
  receiver-blindness, the two-leg keystone, is UNPINNED — every test uses `connection`) · F2
  (no pin that a multi-statement string *containing a quoted literal* stays flagged).
- **REQUIRED CORRECTION:** F1 — "5 scattered per-module pins" is a FICTION (exactly ONE exists,
  `TestNoMultiStatementDdlRidesABareQuery`, floor_cal+lease); the offline leg is NOT its
  subsumer (the pre-existing retry-escape lint/guard is). Deletion is SAFE on the current tree
  (verified) but must be re-adjudicated, not asserted.
- **FIXTURE-DISCRIMINATION:** runtime leg discriminates all 4 plausible wrong builds ✓; #124
  generator-reach genuinely DERIVED (11 via `inspect`; the hand-list has 9, missing lease+floor) ✓;
  #124 positive control is a PARALLEL copy (F3) and declared-side over-inclusion is unguarded (F4).
- **RED honesty ✓** (3 RED behavioural `assert None`, not AttributeError, right reason) · **corpse
  sweep CLEAN** (no test pins the retired #118/#119 world) · **item 4 VERIFIED LIVE** (4/4 on 3.2.4).
- **Packages considered:** `surrealdb` SDK statement splitter — READ installed
  `surrealdb/request_message/sql_adapter.py` (naive `.split(";")`, no statement-count check) →
  **bespoke**, reuse `_txn._assert_envelope_integrity` (`keep_with_trigger` on the SDK). Diff vs
  author: agree.
- **Reuse ledger:** none — I introduced no production symbols (adversary writes findings only;
  all probes/reference-builds live in `/tmp/adv07-scratch` + `/tmp/adv07-probes`).
- **Graded:** `82e2587` · `git rev-parse HEAD` = `82e2587` · **SAME**.
- **Receipt pointers:** wrong-build matrix §C · #124 probe §D · envelope bound §E · removed-behavior
  §F1 · item-4 live run §G · scratch reference build `/tmp/adv07-scratch/loremaster/tests/_sdk_guard.py`.

---

## A. P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| # | Invariant | ∀-over-inputs / guarded | Receipt |
|---|---|---|---|
| 1 | Runtime: a bare `.query()` carrying >1 statement is flagged | **∀** over *executed* `.query()` calls — the guard intercepts every call on the class | reference flags BEGIN-envelope + non-BEGIN pair + `;`-in-literal (§C); `only_escapes` & `keys_on_begin` wrong builds killed |
| 2 | Runtime: single-statement `.query()` is NOT flagged | control (∀) | `all_query` wrong build killed by this control (§C) |
| 3 | Runtime: multi-statement `query_raw` is NOT flagged | **guarded** on `method == "query"` | `ignore_method` wrong build killed by the `query_raw` control (§C) |
| 4 | Runtime: the multi-statement verdict comes from the SHARED predicate | **guarded — and UNPROVEN** | **F0 — `inline_predicate` clone SURVIVES (§C).** No mutation binds the runtime leg to `_assert_envelope_integrity`. |
| 5 | Offline: no production bare-`.query()` site passes a static multi-statement literal | **guarded** — `_talks_to_surrealdb` (import) × `_is_connection_receiver` (NAME) × `ast.Constant` (static) | positive control fires on a planted literal; joint blind spot F6 (oddly-named receiver / composed string walk through) |
| 6 | #124: every `*_TABLE`/`*_RELATION` constant value ∈ the declared-table set | **∀** over derived constants; both sides DERIVED | positive control flags a ghost (§D); generator-reach genuinely derived (11 via `inspect`) |

Guarded rows 3, 4, 5 each carry their door-build receipt. Row 4 is the one that walked through.

## B. P1c — REACH TABLE (per instrument: reach source · coverage-checked · effect/proxy · one-source-by-mutation)

| Instrument | reach: DERIVED vs hand-list | coverage a CHECKED variable? | EFFECT vs PROXY | ONE source proven by MUTATION | verdict |
|---|---|---|---|---|---|
| **Runtime multi-stmt leg** (builder-authored in `_sdk_guard._guard`) | DERIVED — class-wrapped, **receiver-BLIND** (proven §C) | inherited from the retry guard's `test_every_production_sdk_call_site_was_OBSERVED_by_the_guard` — but that pin is `_is_connection_receiver`-bound and checks *observation*, not *multi-stmt exercise* | **EFFECT** (observes the real call + its arg) | **NO — F0: a private clone survives** | **MISSING PIN (F0)** |
| **Offline multi-stmt leg** (`_bare_query_multi_statement_literal_sites`) | `_talks_to_surrealdb` DERIVED; **`_is_connection_receiver` is a NAME-list**; static-literal only | positive control sees a literal; **no `observed==derived` grow-check** for this leg | EFFECT (static AST literal) | offline calls the real predicate *in its own source* → sharing by construction | receiver-name + composed-string bound (F6; inherited, documented) |
| **#124** (`_ddl_generators`/`_declared_tables`/`_table_constants`) | DERIVED — `inspect.getmembers` + `vars()` (NOT the 9-entry hand-list) | generator-reach pin + 2 anti-vacuity pins | EFFECT (reads generator OUTPUT) | n/a (no cross-caller policy) | derived ✓; residuals F3 (parallel-copy control), F4 (declared-side over-inclusion unguarded) |
| **Runtime receiver-blindness** (the two-leg keystone) | intrinsic (class wrap) | — | — | — | **UNPINNED (F5)** — every contract test uses a `connection`-named receiver |

Legs run: **empirical** for the runtime leg (built the reference + 5 wrong variants in scratch, ran the contract against each) and for #124 (ran the real helpers against wrong derivations). **Construction-inspection** for the offline leg's `_is_connection_receiver`/`_talks_to_surrealdb` reuse (read source; it calls the real predicate in-line).

---

## MISSING PINS (each: the test that should exist + the defect it catches)

### F0 — BLOCKER. The runtime leg's use of `_assert_envelope_integrity` is not mutation-proven (routing-is-not-sharing).
- **Defect it catches:** a builder who inlines a `;`-check into `_sdk_guard._guard` instead of
  calling `_txn._assert_envelope_integrity` — a private copy wearing the shared name. It is
  **behaviourally identical on the 4 contract fixtures**, so it passes the entire contract
  (`inline_predicate`: **6 passed**, §C). Two consequences, both real:
  1. ONE-IMPLEMENTATION is defeated silently (the contract's own stated goal — §5 of the report,
     builder-job item 2 "REUSE … not clone").
  2. **The `;`-in-literal KNOWN-BOUND re-open trigger breaks.** That trigger fires when someone
     makes `_assert_envelope_integrity` literal-aware. The trigger is measured by
     `test_the_semicolon_in_a_literal_is_a_KNOWN_BOUND`, which drives the **runtime** leg. If the
     runtime leg is a clone, mutating the shared predicate does NOT reach it, the pin stays GREEN,
     and the divergence is silent — "a trigger nobody measures is a hope," here a trigger measuring
     a clone.
- **Pin that should exist:** monkeypatch `loremaster.store._txn._assert_envelope_integrity` to a
  verdict-inverting stub (e.g. flag a *single*-statement string), drive a single-statement bare
  `.query()`, and assert `report.multi_statement_violations` now fires — RED on a clone, GREEN only
  if the runtime leg genuinely calls the shared predicate. (Note the builder must import the
  predicate at call-time, not capture it at import, or the monkeypatch cannot reach it — that is
  itself part of proving the share.) The offline leg + `compose` should be swept into the same
  mutation proof, mirroring the existing `test_the_two_scans_SHARE_their_predicates_rather_than_cloning_them` (`test_retry_seam.py`).

### F5 — the runtime leg's RECEIVER-BLINDNESS (the two-leg design's keystone) is unpinned.
- The whole justification for accepting the offline leg's `_is_connection_receiver` NAME-limit is
  "the runtime leg patches the class, so it is receiver-blind" (report §5; offline-leg docstring
  `test_the_scan_actually_SEES_a_multi_statement_literal`). **No contract test exercises it** —
  every runtime test uses a receiver literally named `connection`.
- **Reproduction (green on the correct build):** I drove a multi-statement `.query()` on a receiver
  named `db` under the reference build — flagged (§C). So the property HOLDS and a pin is trivially
  satisfiable.
- **Defect it catches:** any future refactor that moves the multi-statement verdict out of the
  class-wrapper into something receiver-name-bound, silently re-opening the offline leg's blind
  spot at runtime. **Severity note:** the current class-wrap mechanism makes this hard to break via
  the prescribed implementation path, so this is a cheap keystone-proving pin, ranked below F0.
- **Pin that should exist:** `test_a_multi_statement_bare_query_on_an_oddly_named_receiver_is_flagged`
  (the `db`-receiver case I ran).

### F2 — no pin that a multi-statement string CONTAINING a quoted literal stays flagged.
- The known-bound pin proves `"RETURN 'a;b'"` (a `;` inside a literal) IS flagged. But the two
  multi-statement fixtures (`_MULTI_STATEMENT_QUERY`, `_MULTI_STATEMENT_NO_BEGIN_QUERY`) contain **no
  quotes**. Under the current quote-blind predicate, `"CREATE a SET x='v'; CREATE b SET y='w'"` IS
  flagged (§E) — but the moment the `;`-in-literal re-open trigger is acted on (detector made
  literal-aware), a buggy literal-aware parser could over-strip and wave a genuine
  multi-statement-with-quotes through, and **no fixture would catch it.**
- **Defect it catches:** a literal-aware detector that stops flagging real multi-statement strings
  bearing quotes. **Bounded:** only bites a future literal-aware builder; the current build reuses
  the quote-blind predicate, so it is GREEN today.
- **Pin that should exist:** a multi-statement fixture whose statements contain a quoted literal
  (`"CREATE a SET x='v'; CREATE b SET y='w'"`), asserted flagged.

---

## REQUIRED CORRECTION (P6b removed-behavior inventory)

### F1 — "5 scattered per-module pins" is a FICTION; the offline leg is NOT their subsumer.
Independent enumeration (grep of the whole test tree, §F1):
- There is **exactly ONE** `TestNoMultiStatementDdlRidesABareQuery`, in
  `test_floor_calibration_schema.py`, covering **floor_calibration.store + lease** (2 modules, one
  class). The claim that "`comms_schema` / `message_ledger` / `graph_surreal` carry their own
  separate copies" (report §3, sidecar §Fork, `test_retry_seam.py:9442-9450`) is **unsubstantiated
  — those pins do not exist** (verified: only one file holds the `attr in {"query","query_raw"}`
  AST shape).
- The existing pin checks a **BROADER** property than the new offline leg: it bans **all** direct
  `.query()`/`.query_raw()` on any non-`self` receiver in those 2 modules. The new offline leg only
  flags `.query()` (not `query_raw`) with a **static multi-statement literal**. So "the offline leg
  is the consolidation target whose coverage is a strict superset" is **FALSE** in three dimensions
  (query_raw, single-statement direct query, runtime-composed multi-statement).
- **The actual subsumer is the pre-existing retry-escape guard** (`_unseamed_sdk_call_sites` lint +
  the receiver-blind autouse runtime guard), which already bans every SDK call outside the driver
  across all `_talks_to_surrealdb` modules — floor_cal + lease included.
- **Deletion IS SAFE on the current tree** (verified §F1): both modules import surrealdb+`_txn`
  (scanned by the lint) and hold only `connection`-named direct receivers (signin/close, both in
  the SAFE set) — everything else routes through the seam. The only *narrowing* is the old pin's
  `not-self` receiver breadth vs the replacements' `_is_connection_receiver` NAME-limit, which has
  **zero current impact** (no oddly-named direct receivers) and is the repo-wide accepted bound.
- **Required:** correct the removed-behavior adjudication before the builder deletes — name the ONE
  real pin, state that the **retry-escape lint/guard** (not the offline leg) preserves its
  route-through-seam coverage, and adjudicate the `not-self`→`_is_connection_receiver` narrowing
  deliberately (accept-with-note, per this repo's own instrument lesson). Do not ship the "5 pins /
  strict superset" prose — it is exactly the un-derived count this repo has the most receipts against.

---

## RESIDUALS (individual verdicts)

- **F3 — #124 positive control is a PARALLEL copy.** `test_a_planted_undeclared_constant_would_redden_the_invariant`
  re-implements the invariant's comparison (`if value not in declared` appears **twice** in the
  file, §D) instead of calling a shared helper. It proves "a dict-comp flags a ghost," not that the
  *invariant's own* expression is exercised. Weak in practice (an inverted invariant self-catches by
  going RED at HEAD-green). **Verdict: minor; factor the comparison into one helper both call.**
- **F4 — #124 declared-side over-inclusion is unguarded.** A `_declared_tables()` that unions in
  every constant value defeats the invariant **and passes both anti-vacuity legs** (`CHUNK_TABLE ∈
  declared`, `len ≥ 20` still hold — §D). Requires corrupting the test helper (not a production
  regression), so low severity. **Verdict: note; the realistic production regression — new
  constant, no `generate_ddl` — IS caught.**
- **F6 — the two-leg joint reach blind spot.** A NEW bare-`.query()` site with (a) an oddly-named
  receiver OR (b) a runtime-composed multi-statement string, that no test executes with a
  multi-statement string, is caught by **neither** leg (offline: receiver-name + static-literal
  only; runtime: executed-only). **Verdict: INHERITED from the retry-escape guard and DOCUMENTED —
  an accepted bound, not a new defect.** Named because the reach table demands it.
- **Minor — production-frame scoping of the runtime check is unpinned.** The contract does not pin
  that the multi-statement check is scoped to production frames (`site is not None`) like the escape
  check. A build that flags harness-issued multi-statement bare `.query()` calls passes all 6
  contract tests but would break other autouse-guarded tests at build time (self-correcting).
  **Verdict: note.**

## CONFIRMED-GOOD (I tried to break these and could not)

- **Runtime-leg discrimination.** 4 plausible wrong builds (`only_escapes`, `keys_on_begin`,
  `all_query`, `ignore_method`) each killed by the fixture the author named — the orthogonality
  ("flagged even inside the driver"), the non-BEGIN discriminator, the single-statement control, and
  the `query_raw` control all genuinely discriminate (§C).
- **#124 generator-reach is genuinely DERIVED**, not a hand-list-plus-2: `_ddl_generators()` finds
  **11** via `inspect.getmembers`; `_enforced_relations_scaffold.ALL_DDL_GENERATORS` is **9**,
  genuinely missing `generate_lease_ddl` + `generate_floor_calibration_ddl` (§D). The derivation
  makes that omission unrepresentable, exactly as claimed.
- **#124 both sides derived; anti-vacuity real.** `declared` = 26 tables parsed from generator
  output; `CHUNK_TABLE ∈ declared`, `len ≥ 20` hold; the 10 named write-target constants are all
  present. The realistic regression (new constant, no `generate_ddl`) reddens the invariant.
- **RED honesty (P7).** 3 RED / 5 GREEN reproduced at HEAD; the 3 RED are behavioural
  (`assert None` via the `getattr` shim), not `AttributeError` — the file stays collectable and the
  RED is for the right reason (the `multi_statement_violations` surface is unbuilt). `intercepted=3`
  shows the guard already OBSERVES the call.
- **Corpse sweep (P6) CLEAN.** No test asserts the retired #118/#119 world (`"assert"` marker,
  `failed_statements[0]`/`[-1]` positional selection, the fictional `"fulfil the following
  assertion"` text). Production confirms the fix landed: `_ASSERT_VIOLATION_MARKER = "must conform
  to"`, semantic `_domain_root_cause`, `_CASCADE_NOT_EXECUTED_MARKER` (`_txn.py`).
- **Item 4 VERIFIED LIVE (not accepted on the report's word).** `TestResidualRejectionStillLaunders`
  + `TestRecursionDepthClassificationAtRecallSeam` = **4 passed on 3.2.4** (§G), including
  `test_bypassing_both_clamps_still_raises_a_classified_store_error`, which runs the REAL
  `hybrid_search`/`recall` with clamps bypassed and asserts the laundered `"query too complex"` label
  — GREEN only if the engine still emits `"recursion depth"`. So the branch is **genuinely LIVE** on
  3.2.4 and "no change" is correct. (The sidecar's Opt-3, premised on a dead branch, is moot, as the
  author found.)

---

## PROBE RECORD

### §C — wrong-build matrix (runtime leg), reference build in `/tmp/adv07-scratch`
Reference impl I built (satisfiability receipt): `GuardReport.multi_statement_violations: list[SdkEscape]`
+ in `_guarded`, when `site is not None` and `method == "query"` and `_is_multi_statement(args)` (which
calls `_txn._assert_envelope_integrity`), append. Provenance asserted: `loremaster.__file__` →
`/tmp/adv07-scratch/loremaster/loremaster/__init__.py`.

```
# reference (correct build): all 6 runtime + 2 offline pass
8 passed, 564 deselected

# wrong builds, TestBareQueryMustCarryExactlyOneStatement (6 tests):
reference        : 6 passed
only_escapes     : 3 failed, 3 passed   # gate the check on `not allowed` → orthogonality tests die
keys_on_begin    : 2 failed, 4 passed   # key on "BEGIN" → non-BEGIN pair + ;-in-literal die
all_query        : 1 failed, 5 passed   # flag every .query() → single-statement control dies
ignore_method    : 1 failed, 5 passed   # flag regardless of method → query_raw control dies
inline_predicate : 6 PASSED  <-- SURVIVES (F0): clones the ;-logic, never calls the shared predicate
```
Receiver-blindness (F5) — a `db`-named receiver's multi-statement `.query()` under reference:
`1 passed` (flagged) → property holds, pin is satisfiable, but no contract test covers it.

### §D — #124 pin reach/vacuity (real helpers, `/tmp/adv07-probes/probe_124_and_envelope.py`)
```
generate_*_ddl DERIVED (11): [...generate_lease_ddl, generate_floor_calibration_ddl,...]
ALL_DDL_GENERATORS (9): [...]   missing lease? True   missing floor? True
declared tables (26); table/relation constants (26); undeclared at HEAD: {}
ATTACK 2 (poison declared with all constant values): undeclared={} (invariant fooled)
   declared-side anti-vacuity STILL passes (CHUNK_TABLE in, len>=20) -> F4 not caught
ATTACK 3: 'if value not in declared' appears 2x -> positive control is a parallel copy (F3)
```

### §E — envelope-integrity bound (`_txn._assert_envelope_integrity`, the offline predicate)
```
flagged=False  'SELECT 1'                              (single)
flagged=False  'SELECT 1;'                             (single, one trailing ;)
flagged=True   'BEGIN;\nRETURN 1;\nCOMMIT;'            (multi envelope)
flagged=True   'RETURN 1;\nRETURN 2'                   (multi, non-BEGIN)
flagged=True   "RETURN 'a;b'"                          (; in literal — KNOWN BOUND, false positive)
flagged=True   "CREATE a SET x='v'; CREATE b SET y='w'" (multi WITH quotes — currently caught; F2 is the future-literal-aware gap)
flagged=False  "CREATE a SET x='v w'"                  (single, quoted, no internal ;)
```

### §F1 — removed-behavior enumeration
```
Files with the AST pin banning direct .query()/.query_raw(): loremaster/tests/test_floor_calibration_schema.py  (ONLY ONE)
floor_calibration/store.py & store/lease.py: both `from surrealdb import ...` + `from loremaster.store._txn import ...`  (=> scanned by retry-escape lint)
Direct SDK receivers in those modules: only `connection.signin(...)` / `connection.close(...)` (SAFE set) — everything else routes through the seam.
```

### §G — item 4 live run (spike-surreal 3.2.4)
```
tests/test_surreal_store.py::TestResidualRejectionStillLaunders ...................... 2 passed
tests/test_memory_backend.py::TestRecursionDepthClassificationAtRecallSeam ........... 2 passed
4 passed in 1.01s
```

---

## Scratch artifacts (for the lead — cleanup decision)
- `/tmp/adv07-scratch` — a `scratch_copy.sh` copy of the repo (provenance asserted), carrying my
  reference build + 5 wrong-variant switch in `tests/_sdk_guard.py` and one appended probe test in
  `tests/test_retry_seam.py`. Disposable by design; safe to `rm -rf`. **No repo file was mutated.**
- `/tmp/adv07-probes/probe_124_and_envelope.py` — the #124 + envelope probe (pasted-verbatim-equivalent
  above; regenerable). Not committed (a `/tmp` path per brief-base is unrecoverable — the receipts
  that matter are inline in §C–§G).

## Bottom line
The runtime multi-statement invariant and the #124 constant pin are **well-constructed** — I could
not make a plausible-wrong *behaviour* survive them. The contract fails on **sharing** and
**inventory**: the one guard the whole ONE-IMPLEMENTATION story rests on (the runtime leg calling the
shared predicate) is never mutation-proven, so a clone ships green (F0), and the deletion it licenses
is justified by a count that does not exist (F1). Fix F0 (the mutation-share pin) and F1 (re-adjudicate
the deletion against the real subsumer); add F5 and F2 as cheap keystone/bound pins. Then this is a
strong contract.

**CONTRACT INSUFFICIENT.**

---

# DELTA RE-GRADE (2026-08-17, after contract-author-07's fix wave)

**VERDICT: CONTRACT SUFFICIENT.** Every gap I raised is closed; the two I ranked as
required (F0, F1) are closed *correctly*, verified empirically — not narrow-patched. The
residuals I ranked as acceptable (F4, F6, Minor) are left documented, which I confirm is right.

**Graded (delta):** working tree at HEAD `82e2587` with `test_retry_seam.py` modified +
`test_ddl_write_target_coverage_124.py` present · SAME base.

### F0 (BLOCKER) — CLOSED, and I re-ran my own reproduction to prove it.
Two mutation-share pins added: `test_the_runtime_leg_shares_the_txn_predicate_by_mutation`
(runtime) and `test_the_offline_leg_shares_the_txn_predicate_by_mutation` (offline). Each
monkeypatches `_txn._assert_envelope_integrity` to a verdict-inverting stub and asserts a
**single**-statement bare `.query()` now flags — GREEN only if the leg reads the shared
predicate **at call time**. I synced the new contract into `/tmp/adv07-scratch` and re-ran my
prior `inline_predicate` clone (the one that passed all 6 before):
```
reference build          : 12 passed          (satisfiability preserved w/ new pins)
inline_predicate CLONE   : test_the_runtime_leg_shares_the_txn_predicate_by_mutation FAILED
                           (1 failed, 8 passed)   <-- the exact clone that SURVIVED before is now KILLED
```
The runtime pin's RED reason at HEAD is behavioural (`assert None`, surface unbuilt), not an
error. It also enforces call-time import (an import-captured reference the monkeypatch can't
reach stays RED — correct: an import-captured copy is a clone in the dimension that matters,
and it is the dimension the `;`-in-literal re-open trigger depends on). The offline-share pin
carries a pre-mutation control (single NOT flagged) so the flip is real. **F0 genuinely shut.**

### F1 — CLOSED (framing corrected and accurate against my ground truth).
The runtime-leg comment block (`test_retry_seam.py` ~:9449) now: RE-DERIVES the count
independently (grep → `test_floor_calibration_schema.py` ONLY → exactly ONE pin), explicitly
retracts the "five scattered pins" as *"a FABRICATED count inherited un-derived from a
discovery summary,"* names the **retry-escape lint+guard** (not this offline leg) as the real
subsumer, and states deletion is safe with the `not-self`→`_is_connection_receiver` narrowing
*accepted-with-note*. Builder-job item 4 changed from "DELETE the scattered family" to
"OPTIONALLY delete the ONE pin … a removed-behaviour decision to adjudicate deliberately, not
a mechanical subsumption. Leaving it in place is also fine." Matches my §F1 ground truth exactly.

### F5 — CLOSED. `test_a_multi_statement_bare_query_on_an_oddly_named_receiver_is_flagged` (a `db`
receiver) added; RED at HEAD, GREEN on the reference build. The two-leg keystone is now pinned.

### F2 — CLOSED. `_MULTI_STATEMENT_WITH_QUOTES_QUERY = "RETURN 'v'; RETURN 'w'"` +
`test_a_multi_statement_string_containing_quoted_literals_is_flagged` added; RED at HEAD, GREEN
on reference. Guards the day the `;`-in-literal bound is closed by a literal-aware detector.

### F3 — CLOSED. `_undeclared_constants(constants, declared)` extracted (`test_ddl_…_124.py:107`);
both the invariant (:143) and the positive control (:189) now call it — the parallel copy is gone,
so the control exercises the invariant's own comparison. `if value not in declared` appears once.

### Residuals — confirmed still acceptable (not blocking):
- **F4** (#124 declared-side over-inclusion unguarded) — requires corrupting a test helper, not a
  production regression. Accept as noted.
- **F6** (two-leg joint reach blind spot: oddly-named receiver / runtime-composed string at an
  untested site) — INHERITED from the retry-escape guard and now explicitly DOCUMENTED in the
  offline-leg comment block. Accept.
- **Minor** (runtime check's production-frame scoping unpinned) — self-correcting at build time. Accept.

### Ground-truth receipts (delta, re-run by me — not the author's word):
```
HEAD real repo, both classes:      6 failed / (rest) passed — all 6 RED behavioural (assert None)
whole two files:                   6 failed, 575 passed        (matches the lead's count)
scratch reference build:           12 passed                   (satisfiability w/ new pins)
scratch inline_predicate clone:    runtime-share pin FAILED     (my prior reproduction, now killed)
```
Not re-verified by me (lead's own scope, stated): ruff/mypy cleanliness. Corpse sweep, item-4
live run, generator-reach derivation, and P1b/P1c/P-PKG tables from the first grade are unchanged
and still hold.

**Note (author-flagged, not mine to fix):** `DESIGN-sidecar-144-posture.md` §5.2 still carries the
same fabricated "5 pins"/subsumer framing F1 corrected in the contract — the lead is routing that
doc-fix to fable-sidecar-07 separately. It does not affect this re-grade (the *contract* is correct).

**CONTRACT SUFFICIENT.**
