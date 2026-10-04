brief-base v18 read · brief project v7 read

**SUMMARY**
- **State:** done. #536 fixed in `6e37dd5`, which touches only `loremaster/tests/test_am37_13_3_63c_i_a.py`. #536 is resolved with that sha.
- **Deviations:** none. Capability check: every demand in the brief was satisfiable.
- **Packages considered:** none. No new mechanism; the fix routes onto the existing in-repo `_logging_fixtures.parse_production_trees`.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** 1 new symbol, `_package_trees`, dispositioned in §DRY: REUSED `parse_production_trees`.
- **Decisions needed:** none. One two-readings note is in §Readings, with my pick stated.
- **Receipts:**
  - §RED→GREEN: the targeted pair, before and after.
  - §Equivalence: old and new scans give equal results.
  - §Mutations: 3 of 3 held.
  - §Gates: ruff and typecheck.
  - The scratch tree's provenance is in §Mutations.

## What changed (`6e37dd5`, file `loremaster/tests/test_am37_13_3_63c_i_a.py`)
- **New `_package_trees()`:** a module-level function under `@functools.cache`. It calls `_logging_fixtures.parse_production_trees(include_scripts=False)`, keeps only the keys under the `_PACKAGE` prefix and re-keys them relative to `_PACKAGE`. The prefix is derived from `_PACKAGE` relative to the repo root, not a hardcoded string.
  - **Checked reach:** it asserts that the narrowed key set equals `{p.relative_to(_PACKAGE) for p in _PACKAGE.rglob("*.py")}`. That is a path listing, with no parse and no read. If the shared parser ever stops reaching this package, the test goes red instead of every F-6 pin passing vacuously.
- **The three offenders now consume `_package_trees()`:**
  - `_row_reader_owner_classes`
  - `_shape_reader_call_sites`
  - `TestEveryShapeReadNamesItsRead::test_the_row_reader_wrappers_require_noun`
- **Site ids are unchanged:** they were `f"{path.relative_to(_PACKAGE)}::…"` and are now `f"{relative}::…"`, with the same string. Every assertion is byte-identical.
- No allowlist entry was added, and `test_ast_reach_helpers.py` was not touched.

## §Readings (two readings of "keep EXACTLY their assertions' meaning: same domain")
- **(A) Picked:** the domain stays the loremaster package, `_PACKAGE`, exactly as before. The shared parser's whole-workspace output is narrowed to that package.
- **(B) Not picked:** widen the scan to every workspace member, which is what `parse_production_trees` returns natively. That would change the domain: other members' `rows_of`-family calls would become F-6 sites. The brief forbids that.

## §RED→GREEN (targeted, `-n 8 --timeout=300`, `MemoryMax=16G` scope, MemAvailable ≥ 27.8 GiB, no other pytest live)
Command: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider loremaster/tests/test_ast_reach_helpers.py loremaster/tests/test_am37_13_3_63c_i_a.py`

| Run | Result |
|---|---|
| **BEFORE**: the original file, restored byte-exact (`cmp`) from a `cp -a` backup, at HEAD `2ebfbf1` | `1 failed, 188 passed, 4 skipped`. The only failure is `test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives` |
| **AFTER** | `189 passed, 4 skipped`, EXIT=0 |

- Both runs collected 193 tests.
- No test newly fails.
- After the fix, `_whole_tree_clone_offenders()` returns `{}`.

## §Equivalence (2026-10-04, before commit)
I loaded the original file and the migrated one side by side as modules:
- `_row_reader_owner_classes()` is equal in both: `{'PrincipalKeyStore', 'PrincipalStore'}`.
- `_SITES` is equal in both: 31 sites, with the same keys and the same `has_noun` values.

## §Mutations (scratch copy `scratchpad/tree` from `./scripts/scratch_copy.sh`, EXIT 0)
- **Provenance:** `loremaster.__file__` = `…/scratchpad/tree/loremaster/loremaster/__init__.py`, which is inside the copy.
- **Byte-exact copy:** the copy's am37 file `cmp`-equals the migrated file.
- **Method:** each proof was run with `scripts/mutation_proof.py`. The expected-red ids were declared from `--collect-only` before any run, and the tool diffs the red set both ways.

| # | Leg it proves | Mutation (production) | Declared red | Result |
|---|---|---|---|---|
| M1 | `_row_reader_owner_classes`: keeps.py has no `_as_rows` of its own, so the site is found only through the owner path | `keeps.py` `get_by_key`: `noun="keep lookup by key",` → `nouns=` | `test_the_call_passes_noun[keeps.py::get_by_key::627]` | PROOF HELD, `1 failed, 138 passed`, restored byte-exact |
| M2 | `_shape_reader_call_sites` (the reader-call leg) | `principals.py` `_table_exists`: `noun="INFO FOR DB (table-existence probe)"` → `nouns=` | `test_the_call_passes_noun[principals.py::_table_exists::466]` | PROOF HELD, `1 failed, 138 passed`, restored byte-exact |
| M3 | `test_the_row_reader_wrappers_require_noun` | `principal_keys.py` `PrincipalKeyStore._as_rows`: `noun: str` → `noun: str = "rows"` | that test | PROOF HELD, `1 failed, 138 passed`, restored byte-exact |

**Reach-assertion probe, with a control:**
- I monkeypatched `_logging_fixtures.parse_production_trees` to drop `keeps.py`. The assertion fired: `missing: ['keeps.py', 'visible_keeps.py']`. The probe's suffix filter also dropped `visible_keeps.py`, so the assertion named both.
- With the real parser restored, the control returned 75 files.

## §Gates (2026-10-04, after the edit)
- `uv run ruff check .` → `All checks passed!`.
- `./scripts/typecheck.sh` → EXIT 1, with 82 errors in 31 files (loremaster) plus 1 error (scripts), so 83 in total.
  - That equals the adjudicated baseline in `REPORT-coldaudit-486.md` §5.
  - **0 errors are in `test_am37_13_3_63c_i_a.py`.**
- ⚠ **FLAG:** `ruff format --check` would reformat this file. The original file at `2ebfbf1` reformats too, so the drift predates this fix. Format is not a manifested gate, and the brief limited this commit to the fix, so I did not reformat. The operator or lead decides whether to clean it up.

## §DRY ledger
| New symbol | Lookup run | What it returned | Disposition |
|---|---|---|---|
| `_package_trees` | Read `test_ast_reach_helpers.py` (the pin and its allowlist), then `_logging_fixtures.py`. Ran an awk over `loremaster/tests/test_*.py` for `parse_production_trees(` adopters. | `parse_production_trees` is the ONE shared parser. Adopters narrow its output inline, e.g. `test_exhaustion_fates.py` and `test_governed_substrate_64b.py`. No shared "single package" accessor exists. | **REUSED `_logging_fixtures.parse_production_trees`**. The helper adds only this file's package narrowing and its reach check. |

**Fallback said out loud:** the adopter search used awk, not lore. The brief named the exact files, and the question was a textual call-site census, which is one of the grep-honest cases. I filed no lore friction.

## Flags for the lead
- The pre-existing `ruff format` drift in this file (§Gates).
- **Possible follow-up, not done:** `parse_production_trees` has no single-member or `roots=` parameter, so this fix narrows the whole-workspace parse in the test. This file parses the workspace once per process (cached), which was cheap here (33 s for the pair). The allowlist prose in `test_ast_reach_helpers.py` already names "gains a `roots=` parameter" as a re-open trigger for other files.
- My scratch copy is at `scratchpad/tree`. It is disposable, and nothing in it is cited as durable.
