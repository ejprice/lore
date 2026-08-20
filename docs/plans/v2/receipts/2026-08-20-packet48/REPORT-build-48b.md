# REPORT — build-48b (Wave 48-B: the `principal` table + `PrincipalStore`)

`brief-base v14 read` · `brief project v7 read`

## SUMMARY BLOCK
- **State:** done-with-deviations (all 56 contract pins GREEN live; 14/14 mutation proofs exit-0; gates green-delta).
- **Deviations (prominent):**
  1. **`loremaster/tests/test_retry_seam.py` — OUTSIDE my writable set, edited (2 registry entries).** My new `PrincipalStore._query` seam is AUTO-DISCOVERED by that file's AST `_query` scan (the intended routing-is-sharing enrollment), which directly reddened 2 pins. Fixed minimally by registering `PrincipalStore` in `_SEAM_REJECTION_EVENTS` (`principal.query.rejected`) + `_SEAM_REJECTION_NOUNS` (`principal query`) — the SANCTIONED resolution named in that file's own comment (`test_retry_seam.py:6035-6040`: never dodge the enumeration with a bespoke seam = #120, never call it "pre-existing, ship"). Directly-caused-regression exception, brief-base §2.
  2. **`loremaster/tests/test_surreal_schema.py` F6 co-edits (IN writable set):** 3 edits (import `generate_principal_ddl`, add `"principal"` to `EXPECTED_TABLES`, register `generate_principal_ddl` in `_generated_ddl()`). Neither of the two the contract flagged actually reddened without them (contract-48b §5 confirmed) — they are completeness co-edits that STRENGTHEN coverage (mutation-proven: M8 removing the fold now also reddens the inventory pin).
  3. **`principals.py` mypy fix:** the CRUD method `list` shadows the builtin `list` in the class namespace, breaking bare `list[...]` return annotations resolved after it. Fixed with two module-scope aliases (`_RowList`, `_PrincipalList`). No behavior change.
- **Packages considered:** none — no new mechanism. Every 48-B mechanism reuses INTERNAL lore seams: `store._txn.run_query` (single-statement seam + retry), `execute_transaction` (DDL), `bootstrap_session` (connect), `retry_on_conflict` (transitive), the `_define_table`/`_define_field`/`_unique_index` DDL emitters. Store-layer machinery the fastmcp framework never covered; no package to prefer. (Read: `store._txn.run_query` signature/source, `FindingLedger` source — cited below.)
- **Reuse ledger:** 0 new POLICY symbols. `PrincipalStore`'s connection lifecycle + `_query` are CLONES of `FindingLedger` (owner idiom); the schema slice CLONES `_finding_statements`/`generate_finding_ddl` (Variant A) + `_floor_measurement_statements` (call-time ASSERT derivation). Sharing PROVEN BY MUTATION — see §4. Full ledger §6.
- **Graded:** n/a (builder — I render no verdict on another artifact). HEAD-at-report `90426f1`.
- **Receipts (pointers):** contract GREEN §2 · mutation proofs §4 · gates §5 · regression §3 · DRY ledger §6 · mutation driver verbatim §7.
- **decisions-needed (operator, non-blocking — I built the RULED defaults):**
  1. **F1b `set_subject` fill-once vs unconditional.** Built the RULED UNCONDITIONAL primitive (design §5). Discriminator pin `test_idempotent_re_fill_of_own_current_subject_succeeds` (mutation M13 proves it FLIPS if fill-once `AND subject IS NONE` is adopted).
  2. **subject non-empty ASSERT.** Built the RULED KEEP (design §3). Pin `test_empty_string_subject_rejected_while_none_is_accepted` deletes if the operator drops to bare `option<string>`.
- **Message to lead:** `STATE: done · REPORT: REPORT-build-48b.md · 56 pins GREEN live, 14/14 mutation-proofs exit0, ruff clean + typecheck 0-delta; 2 DEVIATIONS: test_retry_seam.py registry (directly-caused, sanctioned) + F6 co-edits. #2/#3 decisions-needed built as ruled defaults.`

---

## 1. What changed (file:symbol)

### Production
- **`loremaster/loremaster/store/surreal_schema.py`** (schema slice, Variant A):
  - `PRINCIPAL_TABLE = "principal"` (new module constant, beside the node-table names).
  - `_PRINCIPAL_STATUS_ACTIVE`/`_SUSPENDED` + `_PRINCIPAL_STATUSES`, `_PRINCIPAL_ROLE_MEMBER`/`_ADMIN` + `_PRINCIPAL_ROLES` — principal-SPECIFIC closed-domain tuples (R3: NEVER the `_AGENT_*` tuples).
  - `_PRINCIPAL_FIELD_SPECS` — the 5 NON-domain fields only (`email` required+non-empty; `subject` `option<string>` + non-empty ASSERT (Model B); `display_name`/`expires_at` `option<>`; `created_at` `DEFAULT time::now()`).
  - `_principal_statements()` — SCHEMAFULL table + `_define_field` per spec + `status`/`role` field-defs whose ASSERTs are **derived at CALL TIME** from the tuples (the `_floor_measurement_statements` idiom, ruling A — mutation-provable) + the two UNIQUE indexes (`principal_email`, `principal_subject`).
  - `generate_principal_ddl()` — standalone slice (`";\n".join(...)+";\n"`).
  - **`generate_ddl()` FOLD** — `statements += _principal_statements()` after `_finding_counter_statements()` (Variant A: the primary `write_store.ensure_ready()` creates the table the moment 48 ships).
- **`loremaster/loremaster/principals.py`** (NEW module):
  - Module docstring = the §6 one-column-one-identity-vocabulary standing-law clause (names `agent`, `input_required`, `_PRINCIPAL_ROLES`, `_PRINCIPAL_STATUSES`, `_TRACE_DECLARED_KEYS`).
  - `Principal(BaseModel)` — `extra="forbid", frozen=True`; `subject: str | None`.
  - `PrincipalStoreError(RuntimeError)` / `PrincipalNotFoundError(PrincipalStoreError)`.
  - `PrincipalStore` — CLONES `FindingLedger`'s connection owner idiom (`__init__`/`_ensure_connection`/`_drop_connection`/`close`/`_safe_close`/`_query`→`run_query`/`ensure_ready`→`execute_transaction`); `create` (subject OPTIONAL, omit-when-None via CONTENT), `get_by_subject`/`get_by_email` (EXPLICIT projections), `list`, `set_status`, `set_subject`; ONE `_row_to_principal` (`row[…]` required, `row.get(…)` for `option<>`).

### Co-edits (disclosed §Deviations)
- **`loremaster/tests/test_surreal_schema.py`** (F6, in writable set): import + `EXPECTED_TABLES` + `_generated_ddl()` registration.
- **`loremaster/tests/test_retry_seam.py`** (directly-caused regression, brief-base §2): `_SEAM_REJECTION_EVENTS["PrincipalStore"]="principal.query.rejected"` + `_SEAM_REJECTION_NOUNS["PrincipalStore"]="principal query"`.

Store law CITED, never re-transcribed: `surrealdb-31-capabilities.md` §1.1 (FIELD `OVERWRITE`, TABLE/INDEX `IF NOT EXISTS`), §1.3 (ALTER trap), §1.4 (`option<>` on a populated table — principal is NEW so required fields are free at creation), §2 (CONTENT writes; `SELECT *` OMITS a NONE `option<>` column → `KeyError`, explicit projection reads `None`; datetimes bind as Python datetimes).

---

## 2. All contract pins GREEN (live, `ws://127.0.0.1:18000`)

Collect counts (per file): `test_principals_schema.py` = **36**, `test_principals_store.py` = **17**, `test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore` = **11** (8 pre-existing + 3 new principal). The contract's "56 pins" = 36 + 17 + the 3 NEW migration pins.

```
$ uv run python -m pytest -n auto \
    loremaster/tests/test_principals_schema.py \
    loremaster/tests/test_principals_store.py \
    'loremaster/tests/test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore' -q
................................................................ [100%]
64 passed in 6.38s
```
(64 = 36 + 17 + 11; every principal pin GREEN — the two-NONE-coexist Model-B load-bearing pins, the UNIQUE-on-UPDATE subject-fill reject, `SELECT *`-omits-NONE control, the QUANTIFIER exact-domain + plausible-`superadmin`-reject, and the dirty-store #107 migration all green live.)

---

## 3. No regressions (covering suites)

Covering tests found via `lore_impact(generate_ddl)` → `store.surreal.SurrealStore.ensure_ready` (2 prod / 88 test refs; 753 covering tests). Ran the changed-surface suites:

```
$ uv run python -m pytest -n auto \
    loremaster/tests/test_principals_schema.py loremaster/tests/test_principals_store.py \
    loremaster/tests/test_surreal_schema.py loremaster/tests/test_surreal_store.py -q
317 passed in 20.12s

$ uv run python -m pytest -n auto loremaster/tests/test_retry_seam.py -q
605 passed, 1 warning in 11.14s     # PrincipalStore auto-enrolled as the 14th _query seam;
                                    # (warning = pre-existing _empty_subscription RuntimeWarning, unrelated)
```

Per brief, I did NOT run the full suite (the ~446 auth-WIP reds are #333-adjudicated). No unrelated test failures surfaced in the scoped suites I ran.

---

## 4. Mutation proofs (M1–M15) — 14/14 exit-0, tree restored byte-exact

Ran in a `./scripts/scratch_copy.sh` provenance-asserted copy (PROVE-WHICH-TREE):
```
scratch copy READY: /tmp/pkt48b-scratch
  loremaster  -> /tmp/pkt48b-scratch/loremaster/loremaster/__init__.py    # loremaster.__file__ receipt
```
Each mutation runs `scripts/mutation_proof.py` (anchor→replacement, exactly once; both-ways RED-set diff; byte-exact restore). Declared-RED node ids taken from `pytest --collect-only` (per #194 — declared BEFORE the run), scoped to the contract-§3 declared set per mutation. **Bound stated honestly:** scoping the run universe to the declared nodes proves each declared pin FIRES (catches the "declared-but-green"/decoration case, which is mutation_proof's load-bearing direction); the "unexpected red" direction is vacuous by construction for the scoped runs.

```
SUMMARY (14/14 PASS exit0 — driver §7)
  PASS(exit0)  M1  FIELD OVERWRITE->IF NOT EXISTS (principal-scoped .replace)
  PASS(exit0)  M2  subject INDEX IF NOT EXISTS->OVERWRITE
  PASS(exit0)  M3  drop/plainify subject UNIQUE
  PASS(exit0)  M4  drop email UNIQUE
  PASS(exit0)  M5  freeze status ASSERT (byte-identical literal — kills the derivation pin)
  PASS(exit0)  M6  freeze role ASSERT (byte-identical literal)
  PASS(exit0)  M7  subject option<string>->required string  (breaks two-NONE-coexist — Model B)
  PASS(exit0)  M8  remove principal from generate_ddl fold
  PASS(exit0)  M9  over-strict status ASSERT (accept only DEFAULT)
  PASS(exit0)  M11 create lets raw SurrealError bubble (no wrap)
  PASS(exit0)  M12 set_status silent no-op on unknown email
  PASS(exit0)  M13 set_subject gains AND subject IS NONE (fill-once — decisions-needed #2 discriminator)
  PASS(exit0)  M14 docstring drops sibling-vocabulary token
  PASS(exit0)  M15 WIDEN the ruled role domain (superadmin leak — QUANTIFIER/authz)
```
Each printed `PROOF HELD — the declared RED set fired EXACTLY: [...]` and `tree restored byte-exact`.

**Two honest observations (neither a defect in my build):**
- **M1 — the contract's §3 declared set UNDERCOUNTS by one MIG pin.** A principal FIELD→`IF NOT EXISTS` mutation reddens not only `test_a_principal_status_widening_lands_on_an_existing_store` (declared) but ALSO `test_the_legacy_principal_row_survives_and_stays_writable` (the narrow ASSERT stays in force → the legacy-row `UPDATE … SET status = widened_value` is rejected). I DECLARED the complete 4-node set (incl. the collateral) and it fired EXACTLY. This is harmless over-protection (the pins catch the wrong build harder than the matrix documents), not a code or pin defect — flagging it so the contract §3 M1 row can be corrected if desired.
- **M10 — NOT single-anchor provable against my build, and that is correct.** Contract M10 assumes `get_by_*` would `KeyError` under `SELECT *`. My `_row_to_principal` uses `row.get(…)` for the `option<>` columns (design §5's explicit ruling), so a `SELECT *` regression returns `None` rather than `KeyError` — the store is DOUBLE-guarded (explicit projection AND `.get()`). The behavior pins (`subject is None`) hold on my correct build; the schema control pin `test_select_star_OMITS_the_none_option_column_the_control` proves the engine behavior. So M10 has no single-anchor discriminating mutation against a correct build — documented, not skipped silently.

**Routing-is-sharing PROVEN BY MUTATION (the #102/#120 guard, for free):** `PrincipalStore._query` is AST-auto-discovered as the 14th `_query` seam by `test_retry_seam.py` (`_MIN_KNOWN_SEAMS=13`, now 14 ≥ 13). Its shared-marker mutation pins (`TestTheSharedRetryMarkerActuallyGates` etc.) run against `PrincipalStore` and pass — proving it retries through the SHARED `run_query`/`retry_on_conflict` driver, not a private copy. `PrincipalStore` introduces NO retry/classification/query policy of its own.

---

## 5. Gates

```
$ uv run ruff check .
All checks passed!

$ bash scripts/typecheck.sh   ; echo exit=$?
... exit=1
total ': error:' lines: 191        # UNCHANGED pre-existing baseline (packet-39 auth-WIP, #333-adjudicated)
errors in principals.py / surreal_schema.py / test_surreal_schema.py / test_retry_seam.py: NONE
```
Green-DELTA: **0 mypy errors from any file I touched.** (The exit-1 is packet-39's ruled, owned RED bound — not mine. Before my mypy-alias fix the count was 198; my 7 introduced errors are gone, leaving the 191 baseline.)

---

## 6. DRY ledger (brief-base §6 — every new reusable symbol)

| new symbol | lore query / read | found | disposition |
|---|---|---|---|
| `PrincipalStore._query` (single-statement seam) | read `findings.FindingLedger._query`, `store._txn.run_query` | the ONE shared `run_query` attempt body | **REUSED `store._txn.run_query`** (cloned `_query` wrapper — no new seam) — proven shared by the retry-seam mutation pins (§4) |
| `PrincipalStore.ensure_ready` (DDL apply) | read `FindingLedger.ensure_ready`, `store._txn.execute_transaction` | shared DDL-txn seam | **REUSED `execute_transaction`** |
| `PrincipalStore._ensure_connection`/`_drop_connection`/`close`/`_safe_close` | read `FindingLedger` owner methods, `store._txn.bootstrap_session`/`signin_credentials` | the ONE shared bootstrap + owner idiom | **CLONED verbatim from `FindingLedger`** (double-checked-lock connection owner) — no policy of its own |
| retry/backoff/classification | `_txn.retry_on_conflict` (rides `run_query`) | exists | **REUSED transitively** — 48-B hand-rolls NO retry |
| `_principal_statements`/`generate_principal_ddl` | read `_finding_statements`/`generate_finding_ddl` (Variant A) + `_floor_measurement_statements` (call-time ASSERT) | table-slice emitters | **CLONED the idiom** (structure from finding; call-time domain derivation from floor) |
| `_define_table`/`_define_field`/`_unique_index` (in the slice) | `store.surreal_schema` emitters | exist | **REUSED** (routing proven by `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters`, mutation-pinned) |
| `Principal(BaseModel)` | read `findings.Finding` | pydantic value-object idiom | **REUSED the idiom** (new principal-specific model) |
| `PrincipalStoreError`/`PrincipalNotFoundError` | read `FindingLedgerError`/`FindingNotFoundError` | error-hierarchy idiom | **REUSED the idiom** |
| `_row_to_principal`/`_as_rows`/`_to_aware_utc`/`_require_aware_utc` | read `FindingLedger._row_to_finding`/`_as_rows`/`_to_aware_utc`/`_require_aware_utc` | per-owner row-mapping/narrowing/tz-normalisation | **CLONED** (principal-columned; the tz + narrowing helpers are structurally identical) |
| `_PRINCIPAL_STATUSES`/`_PRINCIPAL_ROLES` (imported into `principals.set_status`) | read design §5 (client-side validation), `finding` local `FINDING_STATUSES` | the schema's closed-domain tuples | **REUSED the schema tuples** (client-side `set_status` validation shares the DDL's source of truth — one answer to "what is a valid status?") |
| `_RowList`/`_PrincipalList` (module aliases) | n/a (mypy shadow fix) | — | **HAND-ROLLED** 1-liners — the `list` CRUD method shadows builtin `list`; aliases resolve it at module scope |
| `_COL_*`/`_READ_PROJECTION` | read `findings._COL_*` | column-name-constant idiom | **CLONED the idiom** (principal columns) |

---

## 7. Mutation driver (VERBATIM — brief-base §1: the instrument lives only in the disposable scratch)

Run from the scratch root as `.venv/bin/python run_mutations.py`. Each entry = `(name, file, anchor, replacement, [declared-red-keys])`; node-id map in `n`. The lead may commit this to `scripts/` if a durable copy is wanted (outside my writable set).

```python
#!/usr/bin/env python3
"""Drive scripts/mutation_proof.py for packet 48-B's M1-M15 matrix (contract §3)."""
from __future__ import annotations
import subprocess, sys

PY = ".venv/bin/python"; MP = ["scripts/mutation_proof.py"]
S = "loremaster/loremaster/store/surreal_schema.py"; P = "loremaster/loremaster/principals.py"
SCH = "loremaster/tests/test_principals_schema.py"; STO = "loremaster/tests/test_principals_store.py"
MIG = "loremaster/tests/test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore"
DDL = f"{SCH}::TestThePrincipalDdlDecisionRuleIsEnforcedMechanically"
DRV = f"{SCH}::TestThePrincipalClosedDomainsAreDerivedIntoTheDdl"
RT  = f"{SCH}::TestThePrincipalRoundTrip"
n = {
 "field_ovr": f"{DDL}::test_every_field_definition_is_OVERWRITE",
 "no_field_ifne": f"{DDL}::test_no_field_definition_uses_IF_NOT_EXISTS",
 "both_idx_ifne": f"{DDL}::test_both_indexes_are_IF_NOT_EXISTS_and_never_OVERWRITE",
 "both_unique": f"{DDL}::test_both_unique_indexes_are_present_on_email_and_subject",
 "folded": f"{DDL}::test_principal_is_FOLDED_into_the_global_generate_ddl",
 "status_deriv": f"{DRV}::test_changing_the_status_tuple_changes_the_emitted_ASSERT",
 "role_deriv": f"{DRV}::test_changing_the_role_tuple_changes_the_emitted_ASSERT",
 "exact_set": f"{DRV}::test_the_ruled_status_and_role_domains_are_EXACTLY_the_closed_set",
 "dup_subj_create": f"{RT}::test_duplicate_non_none_subject_rejected_on_CREATE",
 "dup_subj_update": f"{RT}::test_duplicate_non_none_subject_rejected_on_UPDATE_fill",
 "dup_email_sch": f"{RT}::test_duplicate_email_rejected",
 "two_none_sch": f"{RT}::test_two_email_only_creates_both_none_subject_coexist",
 "omitted_opt": f"{RT}::test_omitted_option_columns_read_back_as_none_under_explicit_projection",
 "pos_control": f"{RT}::test_every_valid_status_and_role_is_accepted_positive_control",
 "plausible": f"{RT}::test_a_plausible_but_unruled_status_or_role_is_rejected_by_the_store",
 "dup_email_sto": f"{STO}::TestCreateAndRead::test_duplicate_email_raises_principal_store_error",
 "dup_subj_create_sto": f"{STO}::TestCreateAndRead::test_duplicate_non_none_subject_on_create_raises_principal_store_error",
 "two_none_sto": f"{STO}::TestCreateAndRead::test_two_email_only_creates_coexist_via_the_store_api",
 "email_only_defaults": f"{STO}::TestCreateAndRead::test_email_only_create_defaults_to_active_member_none_subject",
 "set_status_notfound": f"{STO}::TestSetStatus::test_set_status_on_unknown_email_raises_not_found",
 "idempotent": f"{STO}::TestSetSubject::test_idempotent_re_fill_of_own_current_subject_succeeds",
 "theft": f"{STO}::TestSetSubject::test_subject_theft_raises_store_error",
 "docstring": f"{STO}::TestModuleDocstringNamesBothVocabularies::test_docstring_distinguishes_principal_from_the_agent_vocabulary",
 "mig_widen": f"{MIG}::test_a_principal_status_widening_lands_on_an_existing_store",
 "mig_legacy": f"{MIG}::test_the_legacy_principal_row_survives_and_stays_writable",
}
FIELD_ANCHOR = "        _define_field(PRINCIPAL_TABLE, name, type_expr, constraint=constraint)"
SUBJ_IDX = '    statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject", ("subject",)))'
EMAIL_IDX = '    statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_email", ("email",)))'
STATUS_FS = "            f\"DEFAULT '{_PRINCIPAL_STATUS_ACTIVE}' ASSERT $value IN [{status_allowed}]\","
ROLE_FS = "            f\"DEFAULT '{_PRINCIPAL_ROLE_MEMBER}' ASSERT $value IN [{role_allowed}]\","
SUBJ_SPEC = '    ("subject", "option<string>", _NON_EMPTY_STRING_ASSERT),'
FOLD = "    statements += _principal_statements()"
ROLES_TUPLE = "_PRINCIPAL_ROLES = (_PRINCIPAL_ROLE_MEMBER, _PRINCIPAL_ROLE_ADMIN)"
CREATE_WRAP = ("        except SurrealStoreError as error:\n"
    "            # The UNIQUE backstop (email or subject) — wrap LOUD.\n"
    "            raise PrincipalStoreError(\n"
    "                f\"could not create principal {email!r}: a principal with that email \"\n"
    "                f\"or subject already exists\"\n            ) from error")
SET_STATUS_NF = ('            {"status": status, "email": email},\n        )\n'
    "        rows = self._as_rows(result)\n        if not rows:\n"
    '            raise PrincipalNotFoundError(f"no principal with email {email!r}")\n'
    "        return self._row_to_principal(rows[0])")
SET_SUBJ_UPDATE = ('                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_SUBJECT} = $subject "\n'
    '                f"WHERE {_COL_EMAIL} = $email RETURN AFTER",')
MUTATIONS = [
 ("M1", S, FIELD_ANCHOR, FIELD_ANCHOR + '.replace("OVERWRITE", "IF NOT EXISTS")',
  ["field_ovr","no_field_ifne","mig_widen","mig_legacy"]),
 ("M2", S, SUBJ_IDX, SUBJ_IDX[:-1] + '.replace("IF NOT EXISTS", "OVERWRITE"))', ["both_idx_ifne"]),
 ("M3", S, SUBJ_IDX, '    statements.append(_plain_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject", ("subject",)))',
  ["both_unique","dup_subj_create","dup_subj_update","theft"]),
 ("M4", S, EMAIL_IDX, '    statements.append(_plain_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_email", ("email",)))',
  ["both_unique","dup_email_sch","dup_email_sto"]),
 ("M5", S, STATUS_FS, "            \"DEFAULT 'active' ASSERT $value IN ['active', 'suspended']\",", ["status_deriv"]),
 ("M6", S, ROLE_FS, "            \"DEFAULT 'member' ASSERT $value IN ['member', 'admin']\",", ["role_deriv"]),
 ("M7", S, SUBJ_SPEC, '    ("subject", "string", _NON_EMPTY_STRING_ASSERT),',
  ["two_none_sch","omitted_opt","two_none_sto","email_only_defaults"]),
 ("M8", S, FOLD, "", ["folded"]),
 ("M9", S, STATUS_FS, "            \"DEFAULT 'active' ASSERT $value IN ['active']\",", ["pos_control"]),
 ("M11", P, CREATE_WRAP, "        except SurrealStoreError:\n            raise", ["dup_email_sto","dup_subj_create_sto"]),
 ("M12", P, SET_STATUS_NF, '            {"status": status, "email": email},\n        )\n'
   "        rows = self._as_rows(result)\n        return self._row_to_principal(rows[0])", ["set_status_notfound"]),
 ("M13", P, SET_SUBJ_UPDATE, '                f"UPDATE {PRINCIPAL_TABLE} SET {_COL_SUBJECT} = $subject "\n'
   '                f"WHERE {_COL_EMAIL} = $email AND {_COL_SUBJECT} IS NONE RETURN AFTER",', ["idempotent"]),
 ("M14", P, "input_required", "inputrequired", ["docstring"]),
 ("M15", S, ROLES_TUPLE, '_PRINCIPAL_ROLES = (_PRINCIPAL_ROLE_MEMBER, _PRINCIPAL_ROLE_ADMIN, "superadmin")',
  ["exact_set","plausible"]),
]
# M10 is intentionally ABSENT: _row_to_principal uses row.get() for option<> columns
# (design §5), so a SELECT-* mutation alone cannot discriminate a correct build — see §4.
results = []
for name, f, anchor, repl, keys in MUTATIONS:
    reds = [n[k] for k in keys]
    cmd = [PY, *MP, "--file", f, "--anchor", anchor, "--replacement", repl]
    for r in reds: cmd += ["--expect-red", r]
    cmd += ["--", PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", *reds]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    results.append((name, "PASS" if proc.returncode == 0 else f"FAIL{proc.returncode}"))
for name, v in results: print(f"{v:6s} {name}")
sys.exit(0 if all(v == "PASS" for _, v in results) else 1)
```

---

## Appendix — scratch disposition
`/tmp/pkt48b-scratch` was a `scripts/scratch_copy.sh` provenance-asserted copy (throwaway by design). It is LEFT IN PLACE at `/tmp/pkt48b-scratch` (my `rm -rf` was sandbox-denied) — it is disposable `/tmp` and safe to delete. The driver in §7 reproduces every proof against a fresh `scratch_copy.sh` copy. No git worktree created (repo standing law: no worktrees).
