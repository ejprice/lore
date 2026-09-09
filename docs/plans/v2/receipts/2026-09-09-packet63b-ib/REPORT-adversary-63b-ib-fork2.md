# REPORT-adversary-63b-ib-fork2

brief-base v14 read · brief project v7 read

## SUMMARY BLOCK
- **VERDICT: INSUFFICIENT** — the FORK-2 *pins* are strong (no wrong build survived them), but a
  KNOWN-CORRECT §2.4 build reds **≥15 pre-existing tests across 8 files** (all GREEN at HEAD). The
  contract's satisfiability receipt (34/0) was scoped to the 2 FORK-2 files and is a FALSE all-clear
  at the suite level — the C-DEF blocker class, in sibling files.
- **P1 headline:** built the §2.4 reference + 6 wrong builds in a provenance-asserted scratch copy.
  Every wrong build is caught, each by the intended pin, with clean isolation (W2→rider vi only,
  W3→rider v only, W1c→contention cell only, W5→plain×domain cell only). No wrong build waved through.
- **The blocker (B1):** §2.4-1 retypes every NON-governed domain rejection from `SurrealStoreError`
  → `TxnDomainRejectionError`. ~15 pre-existing `assert type(x) is SurrealStoreError` corpses across
  test_surreal_store / _findings / _snapshots / _brief_ledger / _agent_registry / _surreal_manifest /
  _diff / _task_ledger / _memory_backend go RED on the correct build. The contract has NO
  removed-behaviour inventory for them and NO whole-suite satisfiability run.
- **Satisfiability (2-file):** reference build → 34 passed / 0 failed, ruff+mypy clean (reproduced).
- **RED-at-HEAD:** reproduced 8 FORK-2 reds, each for the right reason. Mutation declarations
  (rider iii/v/vi) reproduced (W4/W3/W2). Injection integrity verified (`fired==1` reaches the
  composed txn; row kept on the reference, deleted at HEAD).
- Missing pins / required revisions: §"REQUIRED REVISIONS" (whole-suite satisfiability receipt +
  ~15-corpse removed-behaviour inventory + a repo-local invariant pin against the class).
- Fixture-discrimination: all FORK-2 fixtures DISCRIMINATE (proven by perturbation = the 6 wrong builds).
- Graded: `98cf52c` · HEAD-at-report: `98cf52c` · SAME.
- Packages considered: none — no library mechanism (typed exception subclass + `except` reorder +
  `_query` pre-read reuse existing seams `_domain_rejection_error` / `MemoryLedger.retire` /
  `_replay_record`). Concur with the author's line.
- decisions-needed (lead): route the contract back to add the whole-suite satisfiability receipt +
  the type-retype corpse inventory before a builder starts §2.4 (else the builder's first full gate is RED).

## CAPABILITY CHECK
- lore tools loaded via `ToolSearch "+lore"` (keyword form) — FIRST CHOICE throughout
  (`lore_get_symbol` / `lore_search` / `lore_impact`). Fallbacks SAID OUT LOUD: (1) `grep`/`rg` is
  HOOK-BLOCKED in this session (any command containing `grep`, whatever the path); (2) `lore_impact`
  for `remember`'s covering tests returned a **bare-name UNION** (907 tests, imprecise — a
  same-named-sibling collision), useless for the corpse-exhaustiveness question → fell back to a
  **Python string scan of the scratch test tree** (dogfood grep-class case (a): rename/retype
  exhaustiveness where one missed site compiles-but-breaks). This is the honest tool for a
  textual-assertion sweep, not a lore weakness — nothing filed.
- spike-surreal `ws://127.0.0.1:18000` reachable; all store-heavy runs used it (never :18500).
- Store law read (cited, not re-transcribed): `docs/reference/surrealdb-31-capabilities.md` §3 — the
  `KeyError(uuid)` in-flight-drop → `SurrealConnectionError` classification behind the transport
  injection. No store/schema/DDL changed by this grading pass.
- Scratch provenance (#140): `loremaster.__file__ =
  .../scratchpad/ref63bib_1788917867/loremaster/loremaster/__init__.py` (INSIDE the copy — printed
  as a receipt; `scratch_copy.sh` asserted it non-zero).

---

## THE BLOCKER — B1: a correct §2.4 build reds ~15 pre-existing tests; the satisfiability receipt is 2-file-scoped

**The defect the missing pin catches:** §2.4-1 makes `_txn._domain_rejection_error` return the new
`TxnDomainRejectionError` for the NON-governed label (instead of a plain `SurrealStoreError`). That
retypes EVERY non-governed domain rejection (ASSERT/coercion/`type::` reject) routed through
`run_query` AND `_run_verified_transaction`. A large family of pre-existing tests asserts the *exact*
type `assert type(exc_info.value) is SurrealStoreError` on a domain rejection — those become
`TxnDomainRejectionError` and go RED. The contract's satisfiability receipt ran only the 2 FORK-2
files, so it never saw them; the author's report claims *"the ruled shape is cleanly buildable, so the
contract stays satisfiable AFTER any lint cleanup"* — that claim is FALSE at the suite level.

**Measured (reference build = faithful §2.4, run against sibling files; the FULL command + output in
the PROBE RECORD below):** 15 RED / GREEN-at-HEAD, spot-checked 3 individually + 2 more
(`governed_conflict_throw` params + `TestRecordTraceErrorPosture`) — ALL fail with the identical
reason `assert <class 'TxnDomainRejectionError'> is SurrealStoreError`, and ALL pass at HEAD:

| file::test (the corpse) | line | reason |
|---|---|---|
| test_surreal_store.py::TestDomainRejectionErrorType::test_the_domain_rejection_helper_maps_the_governed_label_to_the_typed_error | 912 | asserts `_domain_rejection_error(non-governed)` is *exactly* `SurrealStoreError` — the OLD invariant §2.4-1 INVERTS ("only the governed label maps to the typed subclass") |
| test_surreal_store.py::TestDomainRejectionErrorType::test_single_statement_domain_rejection_raises_store_error | ~857 | `type(x) is SurrealStoreError` on a live ASSERT reject |
| test_surreal_store.py::TestDomainRejectionErrorType::test_a_governed_conflict_throw_via_the_transaction_seam_raises_the_typed_error[execute_transaction / execute_read_transaction] | — | non-governed leg asserts exact `SurrealStoreError` |
| test_surreal_store.py::TestQueryMessageHygiene::test_domain_rejection_message_never_echoes_the_raw_engine_text | — | hygiene INTENT preserved; incidental `type(x) is SurrealStoreError` breaks |
| test_surreal_store.py::TestRecordTraceErrorPosture::test_domain_rejection_raises_store_error_and_keeps_connection | 4393 | `type(x) is SurrealStoreError` |
| test_memory_backend.py::TestQueryClassifiedErrorPosture::test_domain_rejection_message_never_echoes_the_raw_engine_text | 1714 | (empirically RED first) |
| test_findings.py::TestQueryClassifiedErrorPosture::test_domain_rejection_message_never_echoes_the_raw_engine_text | 1221 | same class |
| test_snapshots.py::TestQueryClassifiedErrorPosture::…domain_rejection_message… | 1085 | same class |
| test_diff.py::TestQueryClassifiedErrorPosture::…domain_rejection_message… | 785 | same class |
| test_task_ledger.py::TestQueryClassifiedErrorPosture::…domain_rejection_message… | 1715 | same class |
| test_surreal_manifest.py::TestQueryClassifiedErrorPosture::…domain_rejection_message… | — | same class |
| test_surreal_manifest.py::TestSetState::test_out_of_domain_state_is_rejected_loudly | 439 | domain reject via `_query`, `type(x) is SurrealStoreError` |
| test_brief_ledger.py::TestBriefLedgerConnectionLifecycle::test_domain_rejection_never_echoes_the_raw_engine_text | 1588 | same class |
| test_agent_registry.py::TestAgentRegistryConnectionLifecycle::test_domain_rejection_never_echoes_the_raw_engine_text | 983 | same class |

Plus 2 un-run candidates at `test_graph_surreal.py:2766,3007` (same `type(x) is SurrealStoreError`
grep hits) → true blast radius ~15-17 tests / ~9 files.

**None is a real regression** — every one's behavioural intent (message hygiene / non-connection
classification / connection kept) is PRESERVED; only the *incidental exact-type* check breaks. They
are corpses (CLAUDE.md rename/reshape law: "tests written before a semantic change certify the OLD
world"). The retype from `SurrealStoreError` to a SUBCLASS is caught only by exact-type checks;
`isinstance(x, SurrealStoreError)` and `except SurrealStoreError` are unaffected (the ruling's own
argument, correct).

**Why this is the contract's gap, not just the lead's wave-sequencing:** the contract-adversary
role's C-DEF leg requires proving the contract goes 0-failed against a known-correct build, *including
the harder leg*. The author scoped that to 2 files and reported 34/0 — an "I verified it" that is a
claim about a SCOPE, not a fact. The removed-behaviour inventory swept only the compensation PROSE
(rider vii, keyed on `inspect.getsource(remember)` — reach = ONE method) while the actual blast radius
of §2.4-1 is the whole test tree's domain-rejection exact-type assertions. This is INSTRUMENT-0's
reach class: the sweep's reach is a hidden constant far narrower than the change it guards.

### REQUIRED REVISIONS (the pins/receipts the author must add before a builder starts)
1. **A WHOLE-SUITE satisfiability receipt** (or at minimum: the reference build run against every
   `_txn._domain_rejection_error` consumer + every `type(x) is SurrealStoreError` site). 34/0 on 2
   files is not a satisfiability proof for a change with suite-wide blast radius.
2. **A removed-behaviour inventory** enumerating the ~15 exact-type corpses, each adjudicated
   PRESERVED-WITH-PIN with the mechanical edit: `type(x) is SurrealStoreError` →
   `type(x) is TxnDomainRejectionError` (or `isinstance(x, SurrealStoreError)` where only "is a store
   error, not a connection error" is meant). These edits ship in the SAME wave as §2.4-1 (a green full
   gate is otherwise impossible). The corpse at `test_surreal_store.py:912` is the sharpest — it asserts
   the exact invariant §2.4-1 inverts; leaving it is a green-suite-asserts-the-corpse (here RED) trap.
3. **A repo-local invariant pin** (the "defect class → invariant" rule): an AST/scan pin asserting NO
   test does `type(<x>) is SurrealStoreError` on a domain-rejection fixture — so the next domain-error
   subclass does not re-open this class. (Belt to the whole-suite braces.)

---

## P1b — QUANTIFIER TABLE (every FORK-2 invariant: ∀-over-inputs vs guarded-by-failure-mode)

| invariant | classification | receipt |
|---|---|---|
| **compensation is domain-scoped** (rider i/ii) | **∀ over {plain,supersede}×{transport,domain}** — every cell FORCED by fixture (2×2 parametrize), NOT keyed to the one debugged shape | HEAD reds only `(supersede,transport)`; W5 (drop `plan` guard) reds only `(plain,domain)` — proving the plain×domain cell is non-vacuous and forces a real plain-remember domain rejection (`_poison_note_text`), not n/a |
| **exhausted contention keeps the row** (rider iv behavioural) | **guarded-by-cause** (contention), but the guard is the ALLOWLIST-safe form: KEEP unless `isinstance(TxnDomainRejectionError)` | W1c (compensate on contention too) reds ONLY the contention cell; W1s (broad `except SurrealStoreError`) reds transport+contention+2×2-transport+source pin. The contention cell is the load-bearing discriminator for "allowlist the safe, don't enumerate the forbidden." |
| **typed classification is the gate** (rider iii/iv source) | ∀ — `_domain_rejection_error` is the ONE mapping both raise sites route through | W4 (mapping → plain SurrealStoreError) reds `test_the_one_mapping_helper…` AND the 2×2 `(supersede,domain)` control leg → ROUTING-IS-SHARING proven by mutation |
| **pair-guarded replay close** (rider v / FLAG-1b) | ∀ over {same-owner, cross-owner} — both forced (positive control + skip leg) | W3 (drop pair guard) reds ONLY the cross-owner skip leg; same-owner control stays green |
| **retire-P makes a foreign supersede survive rebuild** (rider vi / FLAG-2a) | guarded-by-STATE (cross-owner lifecycle), green-at-HEAD; the discriminator is the (b)-without-(a) mutation | W2 (pair guard without retire-P) reds ONLY rider vi → proves rider vi is a REAL pin whose failing case is demonstrable, and the SOLE guard for "(a) shipped" (rider v stays green under W2) |
| **cancellation keeps the row** (§2.2 named keep-cause) | **∀ by construction** — the compensation is `except Exception`, and `asyncio.CancelledError` is a `BaseException`, so it NEVER reaches the delete. No cell needed (a cell would trivially pass). CONSIDERED, non-issue. | — |
| **byte-identical rebuild fidelity** (i-b, unchanged by FORK-2) | ∀ over lifecycle states | retire-P (a) does NOT regress it — reference 34/0 includes `test_rebuild_preserves_every_governance_and_lifecycle_stamp` |

Every guarded row carries a surviving-or-killed receipt. No cell is vacuously green.

## P1c — REACH TABLE (each guard/scan the contract introduces or relies on)

| instrument | reach DERIVED vs hand-list | coverage a checked variable | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|
| `_arm_one_shot_txn_fault` (transport injection) | reach = "first `BEGIN` `query_raw` after arming" — gated on the txn SHAPE | `assert counter["fired"]==1` IS the coverage check (fault MUST reach the seam) | EFFECT (ledger-row outcome + replay convergence), not a proxy | n/a (test fixture) | **SOUND** — verified: fires on the composed txn AFTER `ledger.record(S)` (HEAD deletes post-fire; reference keeps + replays) |
| the 2×2 failure-CAUSE set | **HAND-LIST** {transport, domain} (+ contention cell) — a new cause does not auto-join | not a checked variable | effect | — | **RESIDUAL R3** — mitigated: the compensation ALLOWLISTS one safe class, so any un-enumerated cause is KEPT by construction (the reach gap cannot produce a wrong-compensation for an honest build) |
| rider vii prose sweep (`test…comment_no_longer_teaches…`) | reach = `inspect.getsource(remember)` — **ONE method** (a hidden constant) | no | proxy (string presence) | — | **THIS IS B1's root** — the §2.4-1 retype's real reach is the whole test tree's exact-type assertions; the sweep covers one method's comment. The tree-wide BARE grep for "supersede-scoped" is correctly deferred to the cold audit (author flagged), but the TYPE-retype corpse sweep is missing entirely |
| rider iv source pin (`…gates_on_the_typed_domain_rejection_class`) | reach = `remember` source contains `"TxnDomainRejectionError"` | no | **PROXY** (name presence — a comment mention passes) | — | **RESIDUAL R2** — a build referencing the name in a comment while gating on enumerate-forbidden would pass THIS pin, but the behavioural contention cell (W1c) catches it. Belt covered by braces; not a blocker |
| pair-guard (rider v) | reach = the ONE composed close in `_replay_record` | forced by the cross-owner fixture | effect (P's `valid_until` + WARNING) | mutation: W3 reds it | **SOUND** |

Legs run: injection + 2×2 + pair-guard + source-pin were EMPIRICAL (wrong builds in scratch). The prose-sweep reach was construction-inspection + the whole-suite reference run that MEASURED its blind spot (B1).

## MISSING PINS (concrete, name + defect)
- **The whole-suite satisfiability receipt + the ~15-corpse removed-behaviour inventory (B1) — the
  blocker.** Defect it catches: a builder implementing §2.4 faithfully hits a RED full gate with no
  roadmap of which tests to update. Named tests in the B1 table.
- **A repo-local invariant pin** asserting no test exact-type-checks `SurrealStoreError` on a domain
  rejection. Defect: the next domain-error subclass silently re-opens the corpse class.
- (Optional, R2) strengthen the rider iv source pin from name-presence to an AST check that the
  `except` body names `TxnDomainRejectionError` and NO transport type — OR rely on the contention cell
  (already present). Not required; noted.

## FIXTURE-DISCRIMINATION VERDICTS (perturbation = the 6 wrong builds; each has the correct-build control = 34/0)
- 2×2 cells DISCRIMINATE: W5 reds `(plain,domain)`, HEAD reds `(supersede,transport)` — no cell is len≡sum or monoculture.
- transport/contention cells DISCRIMINATE: W1c reds contention-only; W1s reds both. `fired==1` prevents a never-fired false pass.
- rider v/vi DISCRIMINATE: W3 reds v-only, W2 reds vi-only (clean isolation, no cross-talk).
- rider iii DISCRIMINATES: W4 reds the mapping pin + the routed 2×2 control leg.
- No fixture passes a plausible wrong build. (The wrong builds ARE the P2 perturbations, each paired with the 34/0 correct-build control.)

## REPRODUCED RED / MUTATION / CORPSE VERDICTS
- **RED-at-HEAD (P7):** 8 FORK-2 reds / 5 green, each red for the RIGHT reason (row deleted on
  transport+contention; `TxnDomainRejectionError` unbuilt; comment teaches "supersede-scoped"; foreign
  P closed by the unguarded replay close). Full tail in PROBE RECORD.
- **Satisfiability (P4):** reference → 34 passed / 0 failed (2 files) + ruff clean + mypy clean. The
  author's 34/0 and "no orphaned imports" REPRODUCED.
- **Mutation declarations (P4):** rider iii (W4) → mapping pin + 2×2 domain leg red; rider v (W3) →
  cross-owner skip leg red; rider vi (W2) → foreign-rebuild pin red. All three REPRODUCED exactly as
  the author declared.
- **Corpse sweep (P6):** the FORK-2 files carry NO corpse of the OLD compensation (34/0). But the
  §2.4-1 RETYPE has a wide corpse surface in SIBLING files (B1) — the corpse sweep the contract owed.

## RESIDUALS (each an individual verdict, per scope law)
- **R2 (source-pin name-presence):** rider iv's source pin is a name-presence proxy; covered by the
  behavioural contention cell. Not a blocker; optionally harden to an AST no-transport-type check.
- **R3 (2×2 cause-set is a hand-list):** mitigated by allowlist-the-safe (any un-enumerated cause is
  kept by construction). Not a blocker.
- **R4 (production exact-type consumers):** the §2.4-1 retype is behaviourally safe for
  `except SurrealStoreError` / `isinstance` (verified by reasoning + the ruling's own argument), but
  the build wave should confirm NO PRODUCTION site does `type(e) is SurrealStoreError` on a domain
  rejection (the test-side sweep found only tests; a production sweep is cheap insurance). Surfaced,
  not resolved.
- **FLAG-A (author, accepted):** `TestDomainRejectionErrorType` placed in the atomicity file instead
  of `test_surreal_store.py` (author's writable-set constraint). I graded its EFFICACY where it is
  (strong — W4 reds it). Not docked for placement, per the lead's frontier note. NOTE: the SAME file
  (`test_surreal_store.py`) is where 6 of the B1 corpses live — the writable-set boundary that forced
  FLAG-A is the same boundary that hid the corpses; the satisfiability run would have surfaced them.

---

## PROBE RECORD (commands + real output)

### Instrument: the parametrized reference/wrong-build patcher (durable — pasted so the claim is re-runnable)
`patch_ref.py <MODE> <SCRATCH>` reads PRISTINE `_txn.py`/`local.py` from the main repo, applies the
mode's edits (unique-anchor `str.replace`, fails loud on a non-unique/absent anchor), writes into the
provenance-asserted scratch copy. MODES: `ref` (correct §2.4), `w1c` (compensate contention too),
`w1s` (broad `except SurrealStoreError`), `w2` (pair-guard without retire-P), `w3` (retire-P without
pair-guard), `w4` (mapping → plain `SurrealStoreError`), `w5` (drop the `plan is not None` guard).
Faithful §2.4 realization = `TxnDomainRejectionError(SurrealStoreError)` + `TxnGovernedConflictError`
reparented to it + `_domain_rejection_error` returns the typed class + `remember` gates the
compensation on `isinstance(error, TxnDomainRejectionError)` + retires P after commit
(`MemoryLedger.retire`) + `_replay_record` pre-reads P's owner and closes only on a pair match else
WARNING+skip. (Script body committed under the session scratchpad; the diff shape matches the author's
REFERENCE BUILD DIFF, cross-checked.)

### P7 — RED at HEAD (98cf52c), FORK-2 pins only
`uv run pytest <both files> -n0 -k "<6 FORK-2 classes>"` → **8 failed, 5 passed, 21 deselected**.
Failures (each right reason): transport/contention/2×2[True-transport-True] = `new ledger ids: set()`
(row DELETED after `fired==1`); rider iii×2 + rider iv source = `TxnDomainRejectionError is UNBUILT`;
rider vii = comment contains "supersede-scoped"; rider v = foreign P `valid_until` SET (unguarded
cross-owner close). 5 green = the 3 non-red 2×2 cells + rider v same-owner control + rider vi.

### W0 — satisfiability (correct reference, full FORK-2 contract)
`PROVENANCE loremaster.__file__ = .../ref63bib_1788917867/loremaster/loremaster/__init__.py`
`uv run pytest <both files> -n0` → **34 passed in 7.92s**. `ruff check` → All checks passed.
`mypy <2 files>` → Success: no issues found in 2 source files.

### Wrong-build battery (full FORK-2 pin set per mode; `--tb=no -q`)
- **W2 (pair-guard b WITHOUT retire-P a):** `1 failed, 12 passed` — ONLY
  `TestAForeignSupersedeSurvivesARebuild::test_an_admin_bypass_foreign_supersede_stays_closed_after_rebuild`.
  ⇒ rider vi is a real pin; its green-at-HEAD exception is justified; sole guard for "(a) shipped."
- **W3 (retire-P a WITHOUT pair-guard b):** `1 failed, 12 passed` — ONLY
  `TestTheReplayCloseIsPairGuarded::test_a_cross_owner_replay_close_is_skipped_with_a_warning`.
- **W1c (compensate contention too):** `1 failed, 12 passed` — ONLY
  `TestTransportAndContentionKeepTheSupersedeLedgerRow::test_exhausted_contention…keeps_the_ledger_row`.
  ⇒ the contention cell is the allowlist-the-safe discriminator (type built + referenced, so source
  pin GREEN; only the behavioural cell catches it).
- **W1s (broad `except SurrealStoreError`):** `4 failed` — transport + contention +
  2×2[True-transport-True] + `…gates_on_the_typed_domain_rejection_class`.
- **W4 (`_domain_rejection_error` → plain SurrealStoreError):** `2 failed` —
  `TestDomainRejectionErrorType::test_the_one_mapping_helper…` + 2×2[True-domain-False]
  (ROUTING-IS-SHARING: both raise sites route the one helper).
- **W5 (drop `plan is not None`):** `1 failed` — ONLY 2×2[False-domain-True] (compensates plain×domain).

### B1 — whole-suite corpse blast radius (reference build, sibling files)
`uv run pytest <9 sibling files> -n auto -k "<domain/rejection/posture/typed…>"` → **15 failed, 95
passed in 13.75s**. Node list in the B1 table. Spot-check (`--tb=line`, 5 nodes) → identical reason
`assert <class 'loremaster.store._txn.TxnDomainRejectionError'> is SurrealStoreError`; the SAME 3
nodes run against HEAD (main repo) → **3 passed** — proving corpse (green-at-HEAD, red-only-on-correct-
build), not a patch artifact.

### The patcher instrument (verbatim — brief-base §1; scratch is disposable)
```python
#!/usr/bin/env python3
"""Apply the §2.4 reference build (or a named WRONG build) onto a scratch copy.

Usage: patch_ref.py <MODE> <SCRATCH_ROOT>
Reads PRISTINE _txn.py / local.py from the MAIN repo, applies the mode's edits,
writes into the scratch copy. MODES:
  ref   full correct §2.4 (typed class + domain-scoped compensation + retire-P (a) + pair-guard (b))
  w1c   ref BUT compensation ALSO deletes on TxnContentionExhaustedError (rider iv contention cell)
  w1s   ref BUT compensation catches SurrealStoreError broadly (transport+contention deleted)
  w2    ref BUT NO retire-P (a)  → pair-guard (b) without (a)   (rider vi)
  w3    ref BUT NO pair-guard (b) → retire-P (a) without (b)    (rider v)
  w4    ref BUT _domain_rejection_error returns plain SurrealStoreError for non-governed (rider iii)
  w5    ref BUT compensation drops the `plan is not None` guard (compensates plain×domain) (rider ii)
"""
import sys, pathlib

MODE, SCRATCH = sys.argv[1], pathlib.Path(sys.argv[2])
MAIN = pathlib.Path("/home/ejprice/PycharmProjects/lore")
TXN = "loremaster/loremaster/store/_txn.py"
LOC = "loremaster/loremaster/memory/local.py"

txn = (MAIN / TXN).read_text()
loc = (MAIN / LOC).read_text()

def sub(text, old, new, label):
    if old not in text:
        raise SystemExit(f"PATCH-FAIL[{label}]: anchor not found")
    if text.count(old) != 1:
        raise SystemExit(f"PATCH-FAIL[{label}]: anchor not unique ({text.count(old)})")
    return text.replace(old, new)

# ---- _txn.py: define TxnDomainRejectionError + reparent TxnGovernedConflictError (ALL modes) ----
txn = sub(
    txn,
    "class TxnGovernedConflictError(SurrealStoreError):",
    'class TxnDomainRejectionError(SurrealStoreError):\n'
    '    """A non-retryable DOMAIN rejection — the store said the write is ILLEGAL and rolled\n'
    '    back (reference build, close-out rulings §2.4-1). Subclasses SurrealStoreError so every\n'
    '    existing ``except SurrealStoreError`` keeps catching it; distinct from SurrealConnectionError\n'
    '    (transport, UNKNOWN outcome) and TxnContentionExhaustedError, so only IT is compensated.\n'
    '    """\n\n\n'
    'class TxnGovernedConflictError(TxnDomainRejectionError):',
    "txn.type",
)

# ---- _txn.py: the ONE mapping helper returns the typed domain error (NOT for w4) ----
if MODE != "w4":
    txn = sub(
        txn,
        "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n"
        "        return TxnGovernedConflictError(message)\n"
        "    return SurrealStoreError(message)\n",
        "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n"
        "        return TxnGovernedConflictError(message)\n"
        "    return TxnDomainRejectionError(message)\n",
        "txn.mapping",
    )

# ---- local.py: import the typed class (ALL modes) ----
loc = sub(
    loc,
    "    TxnContentionExhaustedError,\n    TxnFragment,\n    TxnGovernedConflictError,\n",
    "    TxnContentionExhaustedError,\n    TxnDomainRejectionError,\n    TxnFragment,\n    TxnGovernedConflictError,\n",
    "loc.import",
)

# ---- local.py: the compensation gate ----
OLD_COMP = (
    "                    # #441 compensation is SUPERSEDE-SCOPED (design §2.2 step 4 describes the\n"
    "                    # COMPOSED supersede flow): delete the durable ledger row ONLY when a guarded\n"
    "                    # close was composed (``plan is not None``). A PLAIN ``remember`` (no supersede)\n"
    "                    # must KEEP its ledger row on a store failure — that is the FP-06 durability\n"
    "                    # guarantee (the ledger is the copy a Surreal failure/wipe cannot touch; a later\n"
    "                    # restore re-embeds it), pinned by\n"
    "                    # test_memory_backend.py::TestDurabilityWriteThrough. Compensating a plain\n"
    "                    # remember would delete the exact row FP-06 exists to preserve.\n"
    "                    if plan is not None and self._ledger is not None:\n"
    "                        self._ledger.delete(memory_id)\n"
)
COMMENT = (
    "                    # #441 compensation is DOMAIN-scoped (close-out rulings §2.4-2): a store\n"
    "                    # rejection is a promise the store will never honour -> compensate; an\n"
    "                    # unknown/unlanded outcome (transport/contention/cancellation) keeps the\n"
    "                    # authoritative ledger row and replay converges (§2.3).\n"
)
if MODE in ("ref", "w4"):
    GATE = ("                    if (\n"
            "                        isinstance(error, TxnDomainRejectionError)\n"
            "                        and plan is not None\n"
            "                        and self._ledger is not None\n"
            "                    ):\n"
            "                        self._ledger.delete(memory_id)\n")
elif MODE == "w1c":
    GATE = ("                    if (\n"
            "                        isinstance(error, (TxnDomainRejectionError, TxnContentionExhaustedError))\n"
            "                        and plan is not None\n"
            "                        and self._ledger is not None\n"
            "                    ):\n"
            "                        self._ledger.delete(memory_id)\n")
elif MODE == "w1s":
    GATE = ("                    if (\n"
            "                        isinstance(error, SurrealStoreError)\n"
            "                        and plan is not None\n"
            "                        and self._ledger is not None\n"
            "                    ):\n"
            "                        self._ledger.delete(memory_id)\n")
elif MODE == "w5":
    GATE = ("                    if isinstance(error, TxnDomainRejectionError) and self._ledger is not None:\n"
            "                        self._ledger.delete(memory_id)\n")
else:  # w2, w3 keep the correct ref gate
    GATE = ("                    if (\n"
            "                        isinstance(error, TxnDomainRejectionError)\n"
            "                        and plan is not None\n"
            "                        and self._ledger is not None\n"
            "                    ):\n"
            "                        self._ledger.delete(memory_id)\n")
loc = sub(loc, OLD_COMP, COMMENT + GATE, "loc.comp")

# ---- local.py: retire-P (a) after the composed txn commits (NOT for w2) ----
if MODE != "w2":
    loc = sub(
        loc,
        "                    raise\n        return memory_id\n",
        "                    raise\n"
        "            if plan is not None and supersedes is not None and self._ledger is not None:\n"
        "                self._ledger.retire(supersedes, valid_until=now.isoformat(), superseded_by=memory_id)\n"
        "        return memory_id\n",
        "loc.retire",
    )

# ---- local.py: pair-guarded replay close (b) (NOT for w3) ----
OLD_CLOSE = (
    "        if isinstance(supersedes, str):\n"
    "            fragments.append(\n"
    "                TxnFragment(\n"
    "                    statements=[\n"
    "                        f\"UPDATE type::record('{MEMORY_TABLE}', $rc_pred) \"\n"
    "                        f\"SET {_COL_VALID_UNTIL} = $rc_close_ts, {_COL_SUPERSEDED_BY} = $rc_succ \"\n"
    "                        f\"WHERE {_COL_SUPERSEDED_BY} IS NONE OR {_COL_SUPERSEDED_BY} = $rc_succ\"\n"
    "                    ],\n"
    "                    params={\n"
    "                        \"rc_pred\": supersedes,\n"
    "                        \"rc_close_ts\": created_at,\n"
    "                        \"rc_succ\": record.memory_id,\n"
    "                    },\n"
    "                )\n"
    "            )\n"
)
if MODE != "w3":
    NEW_CLOSE = (
        "        if isinstance(supersedes, str):\n"
        "            _pred_rows = self._as_list(await self._query(\n"
        "                f\"SELECT {_COL_OWNER_PRINCIPAL}, {_COL_OWNER_AGENT} \"\n"
        "                f\"FROM type::record('{MEMORY_TABLE}', $rc_pred)\",\n"
        "                {\"rc_pred\": supersedes},\n"
        "            ))\n"
        "            _pred = _pred_rows[0] if _pred_rows else {}\n"
        "            _sp = _pred.get(_COL_OWNER_PRINCIPAL)\n"
        "            _sa = _pred.get(_COL_OWNER_AGENT)\n"
        "            _sp = getattr(_sp, \"record_id\", None) or (str(_sp).split(\":\")[-1] if _sp is not None else None)\n"
        "            _sa = getattr(_sa, \"record_id\", None) or (str(_sa).split(\":\")[-1] if _sa is not None else None)\n"
        "            if _sp == owner_principal and _sa == owner_agent:\n"
        "                fragments.append(\n"
        "                    TxnFragment(\n"
        "                        statements=[\n"
        "                            f\"UPDATE type::record('{MEMORY_TABLE}', $rc_pred) \"\n"
        "                            f\"SET {_COL_VALID_UNTIL} = $rc_close_ts, {_COL_SUPERSEDED_BY} = $rc_succ \"\n"
        "                            f\"WHERE {_COL_SUPERSEDED_BY} IS NONE OR {_COL_SUPERSEDED_BY} = $rc_succ\"\n"
        "                        ],\n"
        "                        params={\n"
        "                            \"rc_pred\": supersedes,\n"
        "                            \"rc_close_ts\": created_at,\n"
        "                            \"rc_succ\": record.memory_id,\n"
        "                        },\n"
        "                    )\n"
        "                )\n"
        "            else:\n"
        "                logger.warning(\n"
        "                    \"memory.replay.close.pair_mismatch predecessor=%s successor=%s\",\n"
        "                    supersedes,\n"
        "                    record.memory_id,\n"
        "                    extra={\"predecessor\": supersedes, \"successor\": record.memory_id},\n"
        "                )\n"
    )
    loc = sub(loc, OLD_CLOSE, NEW_CLOSE, "loc.pairguard")
else:
    if OLD_CLOSE not in loc:
        raise SystemExit("PATCH-FAIL[w3.check]: close anchor missing")

(SCRATCH / TXN).write_text(txn)
(SCRATCH / LOC).write_text(loc)
print(f"PATCHED mode={MODE} -> {SCRATCH}")
```
