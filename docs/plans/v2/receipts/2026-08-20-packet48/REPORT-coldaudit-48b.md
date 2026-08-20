# REPORT — coldaudit-48b (COLD AUDIT, REFUTE mode; Wave 48-B: `principal` table + `PrincipalStore`)

`brief-base v14 read` · `brief project v7 read`

## SUMMARY BLOCK
- **VERDICT: GO.** The uncommitted 48-B build over HEAD `90426f1` is correct: 56 contract pins GREEN
  live (independently reproduced, 64 collected), all 14 load-bearing mutations discriminate, gates
  green-delta, the #120 seam gate OBSERVES `PrincipalStore`, and the #107 dirty-store fixture is the
  correct shape. No blocking defect survived the REFUTE pass.
- **Graded:** `90426f1` · HEAD-at-report `90426f1` · **SAME** (graded HEAD `90426f1` + the uncommitted
  working tree; `git merge-base --is-ancestor 90426f1 HEAD` = HEAD is `90426f1`). The build is not yet
  committed; I graded the working tree.
- **Scratch provenance (PROVE-WHICH-TREE, #140):** `loremaster.__file__ =
  /tmp/ca48b-scratch2/loremaster/loremaster/__init__.py` (INSIDE scratch, via `.venv/bin/python`);
  `scratch_copy.sh` exit 0. The scratch's `principals.py` + `surreal_schema.py` are **byte-identical**
  to the real tree, and the mutation_proof restore md5 (`b25db52…`) == real-tree
  `surreal_schema.py` md5 — my proofs graded the ACTUAL build.
- **Packages considered:** none — an audit of internal store-layer seams (`run_query` /
  `execute_transaction` / `bootstrap_session` / `_define_*`); no mechanism specified, no package to
  prefer (agrees with builder + adversary + design).
- **M1/M10 adjudication:** M1 — the contract §3 declared set undercounts by 1 (`mig_legacy` also
  reddens); **BENIGN over-protection**, a contract-doc nit, not a code/pin defect (§Adjudication). M10 —
  non-provable by single anchor because `_row_to_principal` uses `row.get()` for the `option<>`
  columns (design §5); **ACCEPTABLE, design-mandated double-guard**, hides no mapping gap (§Adjudication).
- **1 anomaly, run to ground, non-blocking:** my full mutation driver reported **M6 FAIL** — a
  **stale-`__pycache__` false-FAIL in `mutation_proof.py`** (the #140 class), NOT a pin/build defect.
  The role-derivation pin DOES discriminate the frozen ASSERT: proven by (a) a fresh-subprocess re-run
  with cleared cache (1 failed = reddens correctly) and (b) re-running M6 through `mutation_proof.py`
  after clearing `__pycache__` (PROOF HELD, exit 0). The failure direction is SAFE (stale cache runs the
  CORRECT code → can only manufacture false-FAILs, never a false-PASS), so every PASS remains
  trustworthy. Filed as friction **#390**.
- **decisions-needed (operator, non-blocking — the build implements the RULED defaults, flip-pins in place):**
  1. **F1b `set_subject` fill-once vs unconditional** — built UNCONDITIONAL (design §5). Discriminator
     `test_idempotent_re_fill_of_own_current_subject_succeeds` (M13 flips it).
  2. **subject non-empty ASSERT** — built KEEP (design §3). Pin
     `test_empty_string_subject_rejected_while_none_is_accepted` deletes if dropped to bare `option<string>`.
- **Message to lead:** `STATE: done · REPORT: REPORT-coldaudit-48b.md · VERDICT GO — 64 pins green, 14/14
  mutations discriminate (M6 was a mutation_proof pycache flake #390, verified), seam gate observes
  PrincipalStore, #107 fixture correct; 5 non-blocking residuals`.

---

## Gate re-runs (independent, paste tails with passed-COUNTS)

### 1. All 56 contract pins GREEN (live, `ws://127.0.0.1:18000`)
```
$ uv run python -m pytest -n auto \
    loremaster/tests/test_principals_schema.py \
    loremaster/tests/test_principals_store.py \
    'loremaster/tests/test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore' -q
................................................................ [100%]
64 passed in 5.87s     # EXIT=0
```
64 = 36 (schema) + 17 (store) + 11 (migration class; 8 pre-existing + 3 new principal). The contract's
"56 pins" = 36 + 17 + the 3 NEW migration pins. Reproduces build §2. Live legs hit `:18000` only.

### 2. ruff
```
$ uv run ruff check .
All checks passed!     # RUFF_EXIT=0
```

### 3. typecheck (green-DELTA)
```
$ bash scripts/typecheck.sh    # MYPY_EXIT=1
total ': error:' lines: 191
errors in principals.py / surreal_schema.py / test_surreal_schema.py / test_retry_seam.py: NONE
```
**0 mypy errors from any touched file.** The 191 total is the packet-39 auth-WIP baseline (#333-adjudicated,
a ruled owned RED bound per repo CLAUDE.md), UNCHANGED by this build. Green-delta confirmed.

### 4. No regressions (changed-surface suites)
```
$ uv run python -m pytest -n auto \
    loremaster/tests/test_surreal_schema.py loremaster/tests/test_surreal_store.py \
    loremaster/tests/test_retry_seam.py -q
869 passed, 1 warning in 24.68s     # EXIT=0
```
The 1 warning is the pre-existing `_empty_subscription` RuntimeWarning (unrelated, per build §3).
`test_surreal_store.py` (which holds every consumer of the `generate_ddl` fold + the migration class)
and `test_surreal_schema.py` (EXPECTED_TABLES + `_generated_ddl` registry) both fully green. Per brief I
did NOT run the full suite (~446 auth-WIP reds, #333-adjudicated).

### 5. Mutation proofs (M1–M15) — scratch, provenance-asserted
Ran my own reconstruction of the build §7 driver (`ca_mutations.py`) against a `scratch_copy.sh` tree.
```
PASS M1  PASS M2  PASS M3  PASS M4  PASS M5  [M6 see below]  PASS M7  PASS M8
PASS M9  PASS M11 PASS M12 PASS M13 PASS M14 PASS M15        (13/14 in the driver run)
```
Every PASS = `mutation_proof.py` observed the declared RED set fire EXACTLY (byte-exact restore each).
**M6** reported FAIL in the sequential driver — run to ground as a `mutation_proof.py` stale-`__pycache__`
artifact (§Anomaly), then CONFIRMED discriminating:
```
$ (cleared __pycache__) .venv/bin/python scripts/mutation_proof.py --file …surreal_schema.py \
    --anchor "<role ASSERT f-string>" --replacement "<frozen literal>" \
    --expect-red …test_changing_the_role_tuple_changes_the_emitted_ASSERT -- pytest …
1 failed in 0.37s
PROOF HELD — the declared RED set fired EXACTLY: [test_changing_the_role_tuple_changes_the_emitted_ASSERT]
```

---

## The #120 shared-seam runtime gate — PrincipalStore is OBSERVED (not exempted)

The registry entries the builder added to `test_retry_seam.py` (`_SEAM_REJECTION_EVENTS["PrincipalStore"]
= "principal.query.rejected"`, `_SEAM_REJECTION_NOUNS["PrincipalStore"] = "principal query"`) are the
**sanctioned enrollment, not a dodge** — and coverage is a CHECKED VARIABLE, verified live:
```
$ (import test_retry_seam)
DISCOVERED SEAM COUNT: 14
PrincipalStore in set: True
_MIN_KNOWN_SEAMS: 13
PrincipalStore in _SEAM_REJECTION_EVENTS: True -> principal.query.rejected
PrincipalStore in _SEAM_REJECTION_NOUNS: True -> principal query
all seams: [AgentRegistry, BriefLedger, DiffEngine, FindingLedger, FloorCalibrationStore,
  LocalMemoryBackend, MessageLedger, PrincipalStore, SnapshotStamper, SurrealCodeGraph,
  SurrealLeaseStore, SurrealManifest, SurrealStore, TaskLedger]
```
- `_QUERY_SEAMS` (test_retry_seam.py:694) is **DERIVED** from the live AST scan
  `_discover_query_seams()` (rglob over the package for any class owning `async def _query`), NOT a
  hand-list. So the moment `PrincipalStore._query` exists it is auto-parametrized into EVERY seam pin
  (retry marker, floor, ceiling, classification). The registry supplies the EXPECTED labels for coverage
  that already happens automatically — omitting them KeyErrors the classification pins (the 2 the builder
  saw redden), it does not EXEMPT the seam.
- `_MIN_KNOWN_SEAMS=13`, scan finds 14 ≥ 13 → the anti-vacuity floor holds (a growth from 13 to 14 with
  the floor unchanged is fine; the floor is a lower bound, its failure message asks for a deliberate raise
  only when seams are CONSOLIDATED). `test_every_discovered_seam_can_be_constructed` guarantees no
  discovered seam silently falls out.
- **Routing-is-sharing confirmed by CODE + mutation:** `PrincipalStore._query` (principals.py:313-331)
  delegates to `store._txn.run_query` with `noun="principal query"`, `label="principal.query.rejected"`
  and NO private retry/classification. The retry-seam mutation pins run against `PrincipalStore` and pass
  (regression suite §4, 869 green). `PrincipalStore` introduces zero query/retry/classification policy.

---

## M1 / M10 adjudication (brief §2)

**M1 — declared set undercounts by 1; BENIGN.** M1 flips the principal FIELD emitter
`OVERWRITE`→`IF NOT EXISTS`. My driver ran M1 with the builder's 4-node declared set
(`field_ovr`, `no_field_ifne`, `mig_widen`, `mig_legacy`) → **PASS** (all 4 fire exactly). The contract §3
M1 row declares only 3 (omits `mig_legacy`). `mig_legacy` DOES redden because, under `IF NOT EXISTS`, the
deploy's re-apply no-ops → the narrow status ASSERT stays in force → the legacy row's `UPDATE … SET status
= widened_value` is rejected → `test_the_legacy_principal_row_survives_and_stays_writable` fails. That is
the pin correctly catching a real regression (the migration did not happen) — **harmless over-protection,
a contract §3 documentation nit** (the matrix could add `mig_legacy`), NOT a code or pin defect. The
adversary independently observed the same under-declaration (adversary §6). **Verdict: GO, benign.**

**M10 — non-provable by single anchor; ACCEPTABLE (design-mandated).** M10 = "`get_by_*` uses `SELECT *`
instead of the explicit projection". It is not single-anchor discriminating against THIS build because
`_row_to_principal` (principals.py:532-551) uses `row.get(…)` for the three `option<>` columns
(`subject`/`display_name`/`expires_at`). Under `SELECT *` (which OMITS a NONE `option<>` column — store
law §2), `row.get()` returns `None` rather than raising `KeyError`, so the behavior pins stay green. The
store is **double-guarded**: an explicit projection (`_READ_PROJECTION`, used in all three reads) AND
`.get()`. A single regression (either `SELECT *` alone, or `row[…]` alone) is survived by the other guard;
only BOTH together break it. This is a robustness STRENGTH mandated by design §5, not a gap — and the
engine behavior is pinned at the schema layer by `test_select_star_OMITS_the_none_option_column_the_control`.
I read `_row_to_principal`: it maps all 8 columns correctly (`row[…]` for id/email/status/role, `.get()`
for the options + created_at). **No mapping gap. Verdict: GO, acceptable, design-mandated.**

---

## The M6 anomaly, run to ground (why it is not a defect)

The driver reported `FAIL4 M6` — `mutation_proof.py` said "mutation LANDED (anchor matched exactly once)"
then "1 passed" then "PROOF FAILED — declared RED stayed GREEN (observed=[])". A frozen role ASSERT should
redden `test_changing_the_role_tuple_changes_the_emitted_ASSERT`. I did NOT reason past this — I measured:
1. **Manual repro with `importlib.reload`:** frozen-role build → `after != before` is **False**,
   `"mutation_probe_role" in after` is **False** → both pin assertions SHOULD fail (redden).
2. **Fresh pytest subprocess with `__pycache__` cleared:** the pin **FAILS (1 failed)** with the exact
   assertion `adding a role changed no emitted DDL` — i.e., it reddens correctly.
3. **`mutation_proof.py` re-run for M6 after clearing `__pycache__`:** **PROOF HELD, exit 0.**

Root cause: back-to-back mutate→restore cycles on ONE file (M1–M6 all mutate `surreal_schema.py`) within
mtime second-granularity left a stale `.pyc`; M6's pytest subprocess loaded bytecode from a prior mutation,
so the role spec ran UNMUTATED and the pin passed. This is the #140 stale-bytecode class biting the
instrument. **The failure direction is SAFE:** stale cache runs the CORRECT code, so it can only manufacture
false-FAILs (a pin staying green), never a false-PASS (stale cache cannot make a pin redden). Therefore the
builder's 14/14 PASS and my 13/14 driver PASSes remain trustworthy. Filed **finding #390** (suggested
hardening: `mutation_proof.py` should clear the target module's `__pycache__` before its pytest leg).

---

## Diff adjudication (REFUTE — reading the diff for a defect the green pins miss)

**Schema slice (`surreal_schema.py`, +116) — CORRECT.**
- FIELD `OVERWRITE`, TABLE/INDEX `IF NOT EXISTS` — verified in the diff (`_define_field` OVERWRITE;
  `_define_table`/`_unique_index` IF NOT EXISTS) and by M1 (field), M2 (index). Both indexes UNIQUE
  (`principal_email`, `principal_subject`) — M3/M4 redden on plainify.
- `status`/`role` ASSERTs derive **at CALL TIME** in `_principal_statements()` from `_PRINCIPAL_STATUSES`
  / `_PRINCIPAL_ROLES` (the `_floor_measurement_statements` idiom, ruling A) — NOT re-frozen. Mutation-
  provable: M5/M6 freeze → the derivation pins redden (M6 confirmed §Anomaly).
- `generate_principal_ddl` FOLDED into `generate_ddl` (diff line 1711, after `_finding_counter_statements()`)
  — M8 reddens `test_principal_is_FOLDED_into_the_global_generate_ddl` on removal.
- `subject` is `option<string>` + `_NON_EMPTY_STRING_ASSERT` (skipped-on-NONE, fires on present empty
  string) — M7 (subject→required) reddens the two-NONE-coexist load-bearing pins.
- Closed domains are **principal-SPECIFIC** (`_PRINCIPAL_STATUSES=(active,suspended)`,
  `_PRINCIPAL_ROLES=(member,admin)`) — NEVER the `_AGENT_*` tuples (R3). M15 (widen roles → superadmin)
  reddens the QUANTIFIER `exact_set` + `plausible` pins — the authz-leak the adversary r2 flagged is CLOSED.

**PrincipalStore (`principals.py`, NEW +603) — CORRECT.**
- CONTENT writes OMIT `subject`/`role`/`display_name`/`expires_at` when None (create:375-383) → the columns
  take DDL DEFAULT / NONE. Reads use the EXPLICIT `_READ_PROJECTION`, never `SELECT *` (415/429/444).
- `set_subject` is UNCONDITIONAL (no `AND subject IS NONE`; 512-513) — F1b=A ruled default (M13 flips it).
- `_row_to_principal` uses `row.get()` for the 3 `option<>` columns (545-549); `row[…]` for required.
- NO new retry/classification/query policy — `_query` routes through `run_query` (§seam gate).
- **Load-bearing except-ordering, VERIFIED:** `create`/`set_subject` catch
  `(SurrealConnectionError, TxnContentionExhaustedError)` FIRST and re-raise, THEN wrap `SurrealStoreError`
  → `PrincipalStoreError`. I verified via lore that BOTH are subclasses of `SurrealStoreError`
  (`_txn.py:120`, `:156`) — so a transport fault / exhausted contention during a write CANNOT masquerade
  as a fake "email or subject already exists" UNIQUE collision. The ordering is correct and load-bearing.
  `set_status` needs no wrap (client-side validates against the shared `_PRINCIPAL_STATUSES`, and status
  is not UNIQUE), and raises `PrincipalNotFoundError` on empty rows — correct.

**Dirty-store migration (#107 class) — CORRECT SHAPE.** `_dirty_principal_store_with_narrowed_status`
(test_surreal_store.py:5533) applies the slice → OVERWRITEs `status` to a NARROWER set (OLD-world stand-in)
→ **CREATEs the legacy row UNDER the narrow definition** (line 5566-5570), THEN the pins deploy the widening
(re-apply, 5591). The legacy row is written under the OLD DDL, exactly the store-reference §1.4/§1.6 shape —
NOT the trap of writing it after the full DDL (which would see no hazard). Narrowed/widened/legacy values
are DERIVED from `_PRINCIPAL_STATUSES` with a `len>=2` anti-vacuity guard. The positive control
(`test_the_migrated_principal_status_still_rejects_out_of_domain`) proves the ASSERT is WIDER not GONE.

**F6 co-edits (test_surreal_schema.py, +3) — CORRECT, no over-relax.** (a) import `generate_principal_ddl`;
(b) `EXPECTED_TABLES += "principal"` — consumed as `EXPECTED_TABLES <= tables` (SUBSET, line 548), so
adding principal TIGHTENS (now requires principal ∈ tables), never relaxes; (c) register
`"generate_principal_ddl": generate_principal_ddl()` in `_generated_ddl()` — ADDS a guard-check entry
(strengthening). All three are completeness co-edits. The builder made 3 (not the 2 the contract flagged);
the third (the import) is a mechanical prerequisite for (c). No inventory pin is over-relaxed.

**mypy alias (`_RowList`/`_PrincipalList`) — no behavior change.** principals.py:168-169 are pure module-
scope type aliases resolving `list` where the `list` CRUD method shadows the builtin. Verified: they carry
no runtime behavior; the fix is `return`-annotation resolution only.

**Removed-behavior (the fold changes `generate_ddl` output).** The only prod consumer is
`surreal.py:551` (`SurrealStore.ensure_ready`), which now creates the principal table — intended (Variant A).
No test asserts exact full `generate_ddl` text; the two other `generate_ddl` hits in the test tree
(test_blocks_edge.py:681, test_surreal_store.py:1843) are COMMENTS, and EXPECTED_TABLES is a subset check.
Regression suite (§4) green over all of test_surreal_store.py + test_surreal_schema.py.

**Adversary r2 residuals (2) — remain non-blocking, unchanged by the build.** (a) the routing/mutation
guard's reach is "≥1 field", not "∀ fields" — mitigated because the clause pins enforce OVERWRITE ∀ over
the emitted string, so the observable #107 property holds even for a hand-written field. (b)
`test_create_with_explicit_non_default_role_and_status_round_trips` names `status`/`suspended` in its
docstring but only exercises `role` (create has no `status` param) — a served-prose over-claim, 1-line
docstring trim. Both are as the adversary described; the build did not change their status. Non-blocking.

---

## RESIDUALS (each individually verdicted; all NON-BLOCKING, GO stands)

| # | Residual | Verdict |
|---|---|---|
| R1 | `mutation_proof.py` stale-`__pycache__` false-FAIL under rapid same-file mutate→restore (my M6). Safe direction (false-FAIL only). Filed **#390**. | **Non-blocking** — harness friction, not a build/contract defect; the pin verifiably discriminates. |
| R2 | Contract §3 M1 declared set undercounts by 1 (`mig_legacy` also reddens). | **Non-blocking** — benign over-protection; contract-doc nit. The pin set is STRONGER than the matrix documents. |
| R3 | `_row_to_principal` docstring (principals.py:535) lists `created_at` under "`row[…]` — always present", but the code uses `row.get(_COL_CREATED_AT)` (guarded loud by `_require_aware_utc`). | **Non-blocking** — served-prose nit; no behavior impact (created_at is non-`option`, `.get()`+None-raise is defensively identical). A 1-word docstring fix. |
| R4 | Adversary r2 residual (a): routing-guard reach ≥1-field not ∀-field. | **Non-blocking** — mitigated by clause pins enforcing OVERWRITE ∀; lead did not require closing it. |
| R5 | Adversary r2 residual (b): `role_and_status` pin docstring over-claims `status`/`suspended`. | **Non-blocking** — 1-line docstring trim; `role` IS discriminated (WB8c). |

---

## Appendix — scratch disposition
`/tmp/ca48b-scratch2` is a `scripts/scratch_copy.sh` provenance-asserted throwaway (disposable by design;
`rm` was sandbox-denied, safe to delete). My mutation driver `ca_mutations.py` lives at its root (a copy of
build §7's driver — the durable instrument is that report + this one; both re-run against a fresh
`scratch_copy.sh` copy). No git worktree created (repo standing law). I mutated only the SCRATCH tree, never
the real working tree (schema + principals verified byte-identical between scratch and real tree, §Summary).
