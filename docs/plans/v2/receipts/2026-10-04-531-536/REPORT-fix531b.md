brief-base v18 read · brief project v7 read

# REPORT — fix531b (#531 follow-up: mint revoke remedy + schema IF NOT EXISTS bound)

## SUMMARY
- **State:** done-with-deviations. Two commits: **`28395e0`** (Fix 1) and **`0f81bd7`** (Fix 2), both on `feat/surreal-unification`, both with no attribution trailers.
- **Deviation 1:** the post-Fix-2 targeted run (`green3`) started at MemAvailable **18.7 GiB**, below the brief's 20 GiB floor. It ran under the 16G cgroup cap: 588 passed, no cap kill. Disclosed, not repeated.
- **Deviation 2:** pin (b) also checks that the served revoke argv parses through the real `lore-adm` parser. That is beyond the brief's (a)/(b)/(c); I added it because a hand-typed command in a remedy is a door. There is also one extra pin, `test_a_remedy_without_landed_is_refused`, because `rows_of` now refuses `remedy=` without `landed=True` (§1.2).
- **Deviation 3 (scope reading):** Fix 2 applied the bound at every site carrying the same claim (16 docstring edits, one file). It also corrected two false mechanism claims next to them: "all tables are `IF NOT EXISTS`" in the module docstring, and "relation tables are `IF NOT EXISTS`" in 4 generator docstrings. All prose. §2.3.
- **Packages considered:** `shlex` (stdlib), read via `shlex.join`/`shlex.split` round-trip, probed live against `build_parser()`. Verdict `replace`: used for argv quoting instead of hand-quoting. `string.Formatter().parse` (stdlib) is used in the slot-count pin. No other mechanism.
- **Odoo-20 portability:** n/a, no Odoo seam touched.
- **Reuse ledger:** 1 new symbol (`governed._LANDED_DEFAULT_REMEDY`), dispositioned in §4.
- **Graded:** n/a (builder report, no verdict on someone else's artifact).
- **Decisions needed:** none blocking. Readings and residuals are in §5. New friction **#533** filed: the currency gate under `--legs` renders the excluded pytest as ORPHAN/FAIL.
- **Receipts:** §1 Fix 1 RED/GREEN/mutation · §2 Fix 2 + sweep table · §3 gates · §5 residuals.

## 0. Capability check
Every demand was satisfiable: lore MCP loaded via `ToolSearch "+lore"`, awk in place of grep (#473), `systemd-run --user --scope`, `uv`, git commit. Nothing was skipped.

Fallbacks:
- Docstring-pin discovery used awk over `loremaster/tests` (`__doc__` / `ast.get_docstring`), a non-symbol textual seam.
- `lore_impact` was used for covering tests of `rows_of` and `PrincipalKeyStore.mint`. It returned 104 covering tests each, with 89 elided. The mint profile rode the bare-name fallback (a union), so the targeted set is the brief's named set plus the docstring scanner.

## 1. Fix 1: the mint remedy (`28395e0`)

**Design as built:**
- `governed._LANDED_SHAPE_FAULT` stays the ONE template. Its last clause is now `{remedy}`.
- New `governed._LANDED_DEFAULT_REMEDY = "verify the stored state before re-running"`.
- `rows_of(result, *, noun, landed=False, remedy=None)`: with `remedy=None`, the default renders byte-identical to the pre-change text. `_shape_fault` takes `remedy`.
- `rows_of` raises `ValueError` if `remedy` is passed without `landed=True`. A plain read's text has no remedy clause, so the remedy would otherwise be silently dropped.
- `PrincipalKeyStore._as_rows` threads `remedy`. `PrincipalStore._as_rows` is untouched (§5.1).
- `PrincipalKeyStore.mint` passes:
  `key {name!r}'s secret was never shown, so revoke it (`<shlex.join([_CLI_PROG, "revoke-key", "--email", email, "--name", name])>`) and mint a new key`.
  `email` is in scope in `mint`, so the command is complete. `_CLI_PROG` is imported from `principals`, the one home of the console-script name, already imported by this module.
  Verb argv read from `principals.build_parser` (`_with_email("revoke-key", …)` + `--name`, required). Live probe: `parse_args(['revoke-key','--email','dev.531+keys@example.org','--name','work laptop'])` → `{'command': 'revoke-key', 'email': …, 'name': 'work laptop', 'config': None}`.

**Pins** (`loremaster/tests/test_am37_13_3_63c_i_a.py`):
- `TestEveryPostWriteShapeReadSaysItLanded::test_the_one_landed_template` was updated to the slotted `_LANDED_TEMPLATE` with the default remedy filled in.
- (a) `…::test_a_site_passing_no_remedy_serves_the_default_text_byte_identical` [str, None, non-dict-member]: compares against `_LANDED_DEFAULT_TEXT`, which is the pre-change text written out, not derived from the template.
- (c) `…::test_the_template_has_exactly_one_remedy_slot`: `string.Formatter().parse` fields == `[noun, remedy, type]`, and the template is byte-equal to `_LANDED_TEMPLATE`.
- `…::test_a_passed_remedy_replaces_the_default_clause` and `…::test_a_remedy_without_landed_is_refused`.
- (b) `TestALandedThenFaultedMintNamesTheRevokeRemedy::test_the_fault_names_lore_adm_revoke_key_for_the_landed_key`: 4 wrong shapes × 2 (email, name) pairs, one of which needs shell quoting (`work laptop`). The fake `_query` asserts it got a CREATE and counts landing (#194). The pin asserts:
  - `LANDED`;
  - the exact `shlex.join` argv;
  - "never shown" and "mint a new";
  - the generic text is absent;
  - the served backticked command parses through the real `p_module.build_parser()` to `revoke-key` with that email and name.

**Runs.** Every run used `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider` with the target set below. No other lore pytest was live; the one other pytest on the box was a mobile-pricepaper-smoke run.

Target set: `test_am37_13_3_63c_i_a.py test_fail_closed_shapes_63c_13b.py test_principal_keys_store.py test_principals_cli.py test_engine_rejection_seam.py test_schema_fold_coverage.py`.

| run | tree | result |
|---|---|---|
| baseline | HEAD `ffdcd8b` (+ #486 WIP in other test files, uncommitted, present for every run) | **574 passed** in 23.14s, exit 0 |
| RED | pins only, test file alone | **11 failed, 94 passed**, exit 1 |
| GREEN | after the production edit | **588 passed** in 19.59s, exit 0 |
| GREEN 2 | after the parser-roundtrip strengthening | **588 passed** in 22.38s, exit 0 |

RED reasons, distinct `E` lines:
- `AssertionError: ['noun', 'type']` (no slot);
- `TypeError: rows_of() got an unexpected keyword argument 'remedy'` ×2;
- 8× `the revoke remedy for 'laptop'|'work laptop' is missing: … verify the stored state before re-running`.

Pin (a) was green on HEAD by design: it preserves today's text. 588 − 574 = 14 new tests = 3 (a) + 1 (c) + 1 passed-remedy + 1 refused + 8 (b).

**Mutation proof of (a).** `_LANDED_DEFAULT_REMEDY` got a trailing `.`, applied from a `cp -a` content backup in my scratchpad. The landing was confirmed by an awk print of the mutated line. Result on the test file: **6 failed, 99 passed** — exactly the 3 `…default_text_byte_identical` + 3 `test_the_one_landed_template`. Restored, and `cmp` confirmed byte-exact. The mutation was made in the REAL tree, so there is no provenance question.

## 2. Fix 2: the schema docstring bound (`0f81bd7`, prose only)

### 2.1 What the reference says, verified against the code before writing
- Store reference §1.1 "The decision rule": FIELD → `OVERWRITE`; INDEX, ANALYZER, plain TABLE and SEQUENCE → `IF NOT EXISTS`; TABLE (RELATION) → `OVERWRITE`.
- §6.1 "The `IF NOT EXISTS` lie": re-defining an existing object with `IF NOT EXISTS` and a different body returns OK and keeps the old definition. The vendor docs say it errors, which is false.
- §1.4: `OVERWRITE` converges the schema, never the data.
- §1.5: an index `OVERWRITE` rebuilds and crashes boot on a dim change; an analyzer `OVERWRITE` leaves indexes stale.

Code, read at `0f81bd7`:
- `_define_table` → `DEFINE TABLE IF NOT EXISTS … SCHEMAFULL`;
- `_unique_index` → `DEFINE INDEX IF NOT EXISTS …`;
- `_define_field` → `OVERWRITE`;
- `_define_relation_table` → `OVERWRITE`.

The reference and the code agree.

Live DDL probe: `generate_task_ddl`, `generate_brief_ddl`, `generate_graph_ddl` and `generate_message_ddl` each emit `DEFINE TABLE OVERWRITE <rel> TYPE RELATION` for their relation tables. `generate_ddl` emits `DEFINE SEQUENCE IF NOT EXISTS trace_seq` and `DEFINE ANALYZER IF NOT EXISTS code_ident`. `generate_principal_key_ddl` emits 1 `IF NOT EXISTS` table + 2 `IF NOT EXISTS` indexes.

### 2.2 The principal_key slice (the brief's named site)
`_principal_key_statements` keeps its idempotence sentence. It now adds that the re-run converges FIELD definitions only. A changed table or index definition (for example a third column in a UNIQUE index, or a dropped `UNIQUE`) is not applied to a store that already has it, citing §1.1 "The decision rule" and §6.1 "The `IF NOT EXISTS` lie". Such a change needs an explicit migration. The module docstring now carries the full bound as **"The `IF NOT EXISTS` bound"**, and every other site points at it, so the full statement is written once.

### 2.3 Bare sweep (`awk 'tolower($0) ~ /idempotent|safe no-op/'` over `surreal_schema.py`)
Pre-edit there were 36 hit lines (HEAD `28395e0`). The table below lists every post-edit hit at `0f81bd7` (line · symbol · verdict).

| line @0f81bd7 | symbol | verdict |
|---|---|---|
| 12, 13, 20 | module docstring | **BOUNDED.** Rewritten: §1.1 decision rule + "The `IF NOT EXISTS` bound" + §1.4/§1.5/§6.1. Also CORRECTED the old "Tables … are `IF NOT EXISTS`" (false for relation tables). |
| 637 | comment near the brief-ack section | N/A. "Idempotent re-ack" is DML/app semantics, not DDL re-apply. |
| 689 | comment, `briefed` UNIQUE index | N/A. Same re-ack semantics. |
| 1026 | `_define_table` | **BOUNDED.** "(idempotent; a CHANGED definition is not applied …)". |
| 1067 | `_define_sequence` | ALREADY-BOUNDED. Its body states that a changed BATCH/START never migrates (#146). Left unchanged. |
| 1081 | `_define_schemaless_table` | **BOUNDED.** |
| 1086 | `_define_schemaless_table` body, "UPSERTed idempotently" | N/A. DML. |
| 1093, 1103 | `_define_field` | TRUE. It is the converging (`OVERWRITE`) side, and the body already states schema-not-data. Left unchanged. |
| 1152 | `_unique_index` | **BOUNDED.** |
| 1256 | `_meta_statements`, "upsert idempotently by key" | N/A. DML. |
| 1277 | `_remove_field`, "idempotent; no-op when absent" | TRUE. REMOVE always applies when the field is present, so no migration claim is made. Left unchanged. |
| 1705 | `_briefed_statements`, "idempotent-re-ack backstop" | N/A. App semantics. |
| 1897, 1901, 1903 | `generate_ddl` | **BOUNDED + CORRECTED.** It said `IF NOT EXISTS` for "tables"; now "plain tables/indexes/analyzer/sequences" and `OVERWRITE` for relation tables and fields. |
| 1958, 1961 | `generate_manifest_ddl` | **BOUNDED.** |
| 1983, 1986 | `generate_memory_ddl` | **BOUNDED.** |
| 2014, 2017 | `generate_task_ddl` | **BOUNDED + CORRECTED.** The `blocks` relation table is `OVERWRITE`. |
| 2041, 2043 | `generate_finding_ddl` | **BOUNDED.** |
| 2065, 2068 | `generate_principal_ddl` | **BOUNDED.** |
| 2136, 2138 | `_principal_key_statements` | **BOUNDED** (§2.2, the full statement). |
| 2171, 2173 | `generate_principal_key_ddl` | **BOUNDED.** |
| 2470, 2473 | `generate_agent_ddl` | **BOUNDED.** |
| 2497, 2500 | `generate_brief_ddl` | **BOUNDED + CORRECTED.** The `briefed` relation table is `OVERWRITE`. |
| 2525, 2531 | `generate_message_ddl` | **BOUNDED.** It already said the relation table converges; added the other direction (changed `message` table, index or sequence → explicit migration). |
| 2545, 2555, 2558 | `generate_graph_ddl` | **BOUNDED + CORRECTED.** `refers`/`answers_to` are `OVERWRITE`. The summary line "— idempotent." (2545) is left as is; the body carries the bound. |

**Docstring pins:** awk over `loremaster/tests` found one test that reads `surreal_schema` slice docstrings: `_schema_fold_guard.scan_stale_emptiness_prose` (via `test_schema_fold_coverage.py`, in the target set). Its closed phrase set (`KNOWN_EMPTINESS_PHRASES`) was checked; the new prose uses none of those phrases. Post-edit targeted run (`green3`): **588 passed** in 22.82s, exit 0. That run is Deviation 1.

## 3. Gates
- `uv run ruff check .` → `All checks passed!` (after both commits).
- `ruff format`: the test file is format-clean. `governed.py` and `principal_keys.py` were already format-dirty at HEAD (checked via `git show HEAD:<f> | ruff format --check -`), so I did not reformat them. Formatting is not a manifested gate.
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`, after `0f81bd7`:
  - `typecheck RED_ADJUDICATED — 83 residual(s)`, owned by packet-58-contract and packet-64b-i-contract.
  - `ruff GREEN`.
  - `pytest NOT_RUN`, excluded by `--legs` → **RED_ORPHANED 0.**
  - The gate still prints `ORPHAN: gate 'pytest' … NOT RUN` / `CURRENCY: FAIL` and exits 1 for the deliberately excluded leg. Filed as **#533**.
- `scripts/typecheck.sh`: 82 + 1 = 83 errors. An awk filter for `governed.py|principal_keys.py|test_am37_13_3_63c_i_a` over its output → **0 lines**. None of the reds are in the touched files.

## 4. DRY ledger
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `governed._LANDED_DEFAULT_REMEDY` | `lore_impact loremaster.governed.rows_of` (consumers: `authorize_guarded`, both `_as_rows`, `_governed_select`, `_rows_stamped`) + a read of `_LANDED_SHAPE_FAULT` | the default clause lived as a literal inside the template | **EXTENDED `governed._LANDED_SHAPE_FAULT`**: the template is unchanged as the one text, and the default clause is lifted into a named constant beside it |

The revoke argv reuses `principals._CLI_PROG` (REUSED) and stdlib `shlex.join`; no new helper.

## 5. Residuals, readings, observations (surfaced, not acted on)
1. **Reading fork:** the brief said "thread `remedy` through `PrincipalKeyStore._as_rows` (and `PrincipalStore._as_rows` only if it shares the signature)", and the file list said "+ `principals.py` only if `_as_rows` threading requires it".
   - Reading A: it shares the signature, so thread it there too.
   - Reading B: thread it only if a caller requires it.
   I picked **B**. No `PrincipalStore` caller passes a remedy, so a parameter there would be dead. `principals.py` is untouched. If A was meant, it is a one-line change plus a pass-through.
2. **`mint`'s `if not rows:` branch** raises `PrincipalKeyStoreError("… vanished immediately after it was created")`. That is a CREATE `RETURN AFTER` answering `[]`. Whether the key landed in that case is unknown, and the text gives no revoke remedy. It is the same class as #531 (a landed-or-maybe-landed mint with an unshown secret). Not touched, because it is outside "no other site changes". Operator call.
3. **`test_comms_schema.py::test_in_and_out_are_never_hand_declared`** cites `surreal_schema.py:454's own docstring`, a line-number citation. It was already stale before this change: line 454 at `ffdcd8b` is `_PRINCIPAL_ROLES = PRINCIPAL_ROLES`, not a docstring. Fix 2 shifts the lines again. It should cite the symbol instead. Outside my writable set.
4. **#533** (filed): the currency gate under `--legs` renders the excluded pytest leg as ORPHAN and FAIL, exit 1.
5. Every run executed against a tree carrying #486's uncommitted WIP (`conftest.py`, `_surreal_harness.py` and others). Baseline and after were measured on the same WIP, so the counts are comparable. The WIP was never staged.
6. **Class lift** (global "fix the CLASS" rule):
   - *Property:* a landed fault's remedy repairs the state that sink's committed write leaves.
   - *Domain:* every `rows_of(…, landed=True)` call site, derived by `_landed_population`.
   - Today only `mint` leaves an unrepairable-by-default state: an unshown secret. `principal create`'s collision is covered by the default ("verify the stored state").
   - The remaining open member is §5.2.
