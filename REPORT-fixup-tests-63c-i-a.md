brief-base v18 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done. All three ruled test-side edits landed in the scratch copy on the fix2 build, with RED/GREEN receipts and mutation proofs. There are no production edits.
- **Deviations:** (1) This report is committed by me, because the spawn brief orders it. brief-base §2 says "never commit", and the brief takes precedence. (2) The satisfiability control M1 for §1 was run by hand (cp -a, mutate, run, restore, cmp) because `mutation_proof.py` requires a non-empty `--expect-red` set.
- **Packages considered:** none. The work is test-side AST derivation inside an existing pin, with no new mechanism. `ast` is stdlib.
- **Odoo-20 portability:** n/a (no Odoo seam touched).
- **Reuse ledger:** 2 new test-private helpers (`_import_aliases`, `_called_name`), both dispositioned in §DRY.
- **Graded:** n/a. No verdict on anyone else's artifact. Built on HEAD `60a369c` + fix2 patch md5 `01fd04715160fab72f80b06d2126421d`.
- **Decisions needed:** **D-1.** A sibling of am-14 §1's class sits in the per-entry unsymboled-count self-destruct leg. It is latent: no real shared path carries an allowance. It fails loud, as a false alarm. Fix it in the builder's matcher wave, or pin it as a bound? See §SIBLING.
- **Receipt pointers:** §EDITS (per-edit table) · §CURRENCY · §PATCHES · §SIBLING · §DRY · §INSTRUMENTS.

**Who has to do what (the builder, same 63c-i-a commit):**
- (a) Change `partition_mypy` to admit an error if ANY entry for its path admits it. am-14 §1 gives the exact edit. Then decide `entry_for`: at the fix2 base its only caller is `partition_mypy` (checked with awk).
- (b) fix2 §FORKS F-c edit 1 in `principals.py::_dispatch_migrate_governed`: the except-tuple must read exactly `(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)`, in that order.

With (a) and (b) landed, all three edits are GREEN. Proven in scratch: the M1 and E1 legs below.

## CAPABILITY CHECK
Everything the brief asks for was available. grep/rg are hook-blocked, so all searches used awk. I did not use lore for the structure questions. The spec named exact symbols and line anchors, and awk plus reading the files was sufficient (fallback case (b)/(c): non-symbol textual anchors). No lore friction to file.

## SETUP (receipts)
- Scratch: `…/c4f63f4e-…/scratchpad/fixup`, created with `scripts/scratch_copy.sh`. `git reset --hard && git clean -fd` gave empty status. fix2 applied cleanly (md5 verified before applying).
- `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c4f63f4e-cadc-4aef-b4e7-5bdac64dbf45/scratchpad/fixup/loremaster/loremaster/__init__.py`, which is the scratch copy, not the main tree.
- am-37 §9 exists (`731a84f`) and was applied. It wins where it adds to am-14 §2 (the import-alias rider plus its control).
- Admission: MemAvailable was 26.7–27.5 GiB at every run (gate is ≥ 20). Every pytest run was capped with `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 … --timeout=300`, used `-n` ≤ 8, and was targeted (never the full suite).

## EDITS

| # | Edit | Ruling | RED/GREEN receipt (measured at `60a369c`+fix2) | Mutation proof |
|---|---|---|---|---|
| §1 | `scripts/test_pending_contract_gate.py`, new section "3a". Adds fixture `shared_path_gate`: two bounds, ONE path, different symbols, with a precondition assert that the path really is shared. Adds `test_shared_path_error_is_expected_when_ANY_entry_admits_it[named-by-first-entry / named-by-second-entry]` and the CONTROL `test_shared_path_error_naming_neither_entrys_symbol_is_unexpected`. | 58 am-14 §1 (property: ∀e: EXPECTED iff ∃ entry for the path that admits e) | **RED:** `[named-by-second-entry]`. Assertion: `'FixtureOtherPlaceholder' is registered by one of the two entries … must consult EVERY entry`, meaning the error landed in `unexpected`. That is the right reason: first-match `Registry.entry_for` returns bound 1's entry, which does not list the symbol. `[named-by-first-entry]` and the control are GREEN (1 failed, 2 passed). | **M1** (ruled fix, `any(entry.admits …)` over every path entry): **44 passed / 0 failed**. This is the satisfiability receipt, run by hand and restored via `cp -a` + `md5sum -c` + `cmp`. **M2** (LAST-match): PROOF HELD, declared RED = {`[named-by-first-entry]`}, fired exactly. The param over both positions is what catches the positional wrong build. **M3** (file-only over the path union): PROOF HELD, declared RED = {new control + the 4 pre-existing file-only guards}, fired exactly. |
| §2 | `loremaster/tests/test_retry_seam.py`. `_RESOLVER_NAMES` deleted. The one prose mention left is the docstring's account of why it was deleted. `_scanner_candidates` now works in three steps. (1) Resolvers are derived by shape (`eval` ∧ `Expression`). (2) "Resolver-reaching" is the fixed point over `ast.Call` names across all scanned trees, with import aliases resolved first (`_import_aliases`: `from m import f as g` → `f`; `import a.b as c` → `b`; attribute calls key on the attribute). (3) Walker = finds handlers ∧ (names a `_txn` store class ∨ is resolver-reaching). Two controls added: `test_am14_2_…THROUGH_A_FRONT_is_derived` and `test_am37_9_…THROUGH_AN_IMPORT_ALIAS_is_derived` (`from … import … as hr` and `import … as home` + `home.home_resolver(...)`). The class docstring's BOUND now reads: dynamic dispatch / class tree spelled without naming it / resolves without `eval`. Fronts and aliases are explicitly outside it. `_catch_sites.py` is untouched (md5 matches fix2). | 58 am-14 §2 + 63c am-37 §9 (rider wins) | **GREEN on fix2: 4 passed** (the class). **Old pin RED on fix2**, measured by running the pre-edit file under a temp name that was then deleted: `catch-handler walkers [] — exactly ONE may exist` (1 failed, 1 passed). That is the defect am-14 §0.2 describes. | **P1**: planted `planted_walker_via_front` in `_catch_sites.py`, which calls the `resolve_caught` front. The old hand-list could NOT have seen this. PROOF HELD: main pin RED, message names both walkers. **P2**: planted second `eval`+`Expression` resolver. PROOF HELD: main pin RED, message names both resolvers. **P3**: alias resolution removed from the pin (`aliases.get(…)` → `call.func.id`). PROOF HELD: only the alias control goes RED (the from-alias walker drops; the module-alias walker survives, as predicted). **P4**: closure iteration removed. PROOF HELD: {main pin, front control} RED. The main pin reddens because `catch_sites_in` reaches the resolver only through `resolve_caught`. All restores were confirmed byte-exact with `cmp`. |
| §3 | `loremaster/tests/_exhaustion_fates.py` `REGISTERED_FATES`, new row `"principals.py::_dispatch_migrate_governed": (Fate("cli-exit", "principals", ("stderr", "returns-named-outcome"), catches="(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)"),)`. Inserted in sorted position before its sibling `_dispatch_report_unmigrated`, with a comment citing am-37 §8.1 / am-14 §3 and the one-commit rider. | 63c am-37 §8.1 (option A; the row's owner is the site's owner) + 58 am-14 §3 riders 1–2 | **RED now, right reason:** `test_every_non_derived_site_has_a_row_and_every_row_a_site`, message `Rows whose sites became PASSTHROUGH/TRANSLATE or vanished — DELETE them: {'principals.py::_dispatch_migrate_governed': 1}`. At fix2 the tuple still catches `SurrealConnectionError`, which is not in the exhaustion domain, so there is no site for the row. The builder must land edit 1 in the same commit. | **E1** (the builder's edit 1 applied in scratch: `SurrealConnectionError` → `SurrealStoreError`): PROOF HELD. The both-ways pin and the row-matching pin go GREEN. The only red left is the pre-existing lease one (next row). Checked untruncated with `-vv`: that failure lists exactly 4 `store/lease.py` items and 0 `principals` items, so the new row's evidence HOLDS on the site. **E2** (edit 1 with member order drifted to `(PrincipalStoreError, SurrealStoreError, KeepStoreError, ValueError)`): PROOF HELD. `test_every_row_is_matched_to_ITS_site_by_the_caught_expression` goes RED with row vs site catches shown. This is rider 1's exactness, order included. |
| — | Pre-existing red, not mine: `test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS` (4 `store/lease.py` items, `logs-error-class` evidence). | — | RED on fix2 **without** my row too (1 failed, 27 passed). The path is registered under 58's bound in `scripts/pending_contracts.yaml` (entry `loremaster/tests/test_exhaustion_fates.py`; its prose names lease fates as that bound's). | — |

**Whole targeted set** on fix2 + edits, as one run over `scripts/test_pending_contract_gate.py loremaster/tests/test_retry_seam.py loremaster/tests/test_exhaustion_fates.py`, `-n 8`: **3 failed, 747 passed, 1 warning in 14.55s**. The 3 are:
- the §1 `[named-by-second-entry]` red (the builder's matcher);
- the §3 both-ways red (the builder's edit 1);
- the pre-existing 58-owned lease evidence red.

There are no other reds.

## CURRENCY (`pending_contract_gate.py --currency --legs typecheck,ruff`, run in the scratch copy)

The before and after results are byte-identical in verdict:
```
  typecheck    RED_ORPHANED — 2 residual(s) with NO owner
      ORPHAN: loremaster/tests/test_reanchor_58_r3_cas_seam.py:93: "type[FindingLedger]" has no attribute "_run_guarded"  [attr-defined]
      ORPHAN: loremaster/tests/test_reanchor_58_r4_state.py:77: "type[FindingLedger]" has no attribute "_run_guarded"  [attr-defined]
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
CURRENCY   : FAIL — RED with nobody's name on it: typecheck · claimed but never run: pytest
EXIT 1
```
- The 2 orphans are exactly the two am-14 §1 names. They clear only when the builder's matcher lands; the test side cannot clear them, by the ruling's design.
- My edits add **0 mypy errors and 0 ruff findings**: the orphan set is unchanged and ruff is GREEN after.
- `pytest NOT_RUN` is expected, because `--legs typecheck,ruff` was used as the brief orders.

## PATCHES
| file | md5 | content |
|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c4f63f4e-cadc-4aef-b4e7-5bdac64dbf45/scratchpad/fixup-tests-63c-i-a.full.patch` | `2c88b1a990d04c2383c36a9c8bbfb36a` | `git diff --binary HEAD` in scratch = fix2 + my edits. `git apply --cached --check` on `60a369c`: OK. |
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c4f63f4e-cadc-4aef-b4e7-5bdac64dbf45/scratchpad/fixup-tests-63c-i-a.delta.patch` | `88c52be2824103ce0eaf51c3f3848350` | TESTS-ONLY delta over fix2, 3 files: `_exhaustion_fates.py` +11, `test_retry_seam.py` +151/−13, `test_pending_contract_gate.py` +97. Built as a diff against a temp index of HEAD + fix2. `git apply --cached --check` on HEAD + fix2: OK. |

## SIBLING (decision D-1: surfaced, not fixed, because it is outside my writable set and production)
**CLASS:** "one path ↔ one bound" as a hidden constant. am-14 §1 fixes it on the admission leg. It also survives in `PendingContractGate.transcript_self_destruct_findings`'s **unsymboled-count** leg, which am-14 §1 states "needs no change".
- The mechanism: per entry, `unsymboled_seen` counts errors of the allowance's code that do not name **that entry's own** symbols. On a shared path, an error naming the OTHER entry's symbol is therefore counted as "unsymboled".
- Measured with the probe in §INSTRUMENTS, on fix2's gate:
  - SHARED: entry A has 1 `attr-defined` allowance; entry B holds a symbol. Result: `SELF-DESTRUCT: … declares 1 unsymboled 'attr-defined' error(s); 2 observed`.
  - CONTROL: A alone, same genuine error. Result: no finding.
- **Direction:** LOUD. It produces a false SELF-DESTRUCT and never a silent admit.
- **Reach today:** none. Enumerating every real registry path under more than one bound gives exactly the two cas_seam/state paths, and neither entry carries `unsymboled_codes`.
- **SIBLINGS TRIED:** the admission leg (am-14 fixes it) and the unsymboled-count leg (defect, latent).
- **SIBLINGS NOT TRIED:** the per-entry "file produced NO mypy errors" leg. It reads per path, is symmetric, and looks fine by reading only; I did not probe it.
- **Recommendation:** have the builder count "unsymboled" against the UNION of every entry's symbols for the path (the same `entries_for` seam) in the matcher wave, and ship one shared-path unsymboled test beside §1's. The operator or sidecar-64 decides; a test for it is not in this delta.

A second, smaller observation: an `unsymboled_codes` allowance on entry A admits ANY same-code error in the partition, including one naming B's symbol. In the probe, SHARED shows `expected 3` even under first-match. That is admission by code, not by symbol, and it is pre-existing documented behaviour (the "falsifier (b)" allowance). I flag it only because it interacts with the shared-path case.

## DRY
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `test_retry_seam._import_aliases` | none. I fell back to awk over `loremaster/tests/` for `asname`, which returned no import-alias resolver in the test support code. | nothing | HAND-ROLLED, test-private. Ruled by am-37 §9 to live in the pin, with `_catch_sites.py` untouched (am-14 §2 "support code untouched"). |
| `test_retry_seam._called_name` | same | nothing | HAND-ROLLED, test-private, same reason. |

This is a fallback from lore to awk and I am saying so. Both helpers are test-private derivations inside the one pin they serve. If a second scanner-pin ever needs them, promote them rather than cloning.

## INSTRUMENTS (pasted verbatim, per brief-base §1)
The shared-path unsymboled probe (§SIBLING). Run with `PYTHONPATH=<tree>/scripts uv run python probe_shared_unsymboled.py`:
```python
"""Probe (fixup-tests-63c-i-a, 2026-09-30): does the per-entry unsymboled-count self-destruct leg
miscount on a path shared by two bounds? Entry A: symbol FixturePlaceholder + 1 unsymboled attr-defined.
Entry B: symbol FixtureOtherPlaceholder. Errors: A's symbol, B's symbol, one genuinely unsymboled attr-defined.
CONTROL: same errors, B's bound removed and B's error dropped -> A's count must be exactly 1 (no finding)."""
import sys
from pathlib import Path
from pending_contract_gate import MypyOutputReader, PendingContractGate, PendingContractRegistry

P = "lorerunes/tests/test_posture.py"
def err(sym): return f'{P}:1: error: Module "lorerunes" has no attribute "{sym}"  [attr-defined]'
UNSYM = f'{P}:2: error: Something without a quoted symbol  [attr-defined]'
def transcript(lines):
    return "\n".join(lines) + f"\nFound {len(lines)} errors in 1 file (checked 1 source files)\ntypecheck: loremaster FAILED\ntypecheck: shellcheck OK (7 tracked .sh)\n"
A = {"id": "a", "owner": "A", "reopen_trigger": "t", "ruling": "r", "rationale": "x",
     "files": [{"path": P, "missing_symbols": ["lorerunes.FixturePlaceholder"],
                "unsymboled_codes": [{"code": "attr-defined", "count": 1, "reason": "probe"}]}]}
B = {"id": "b", "owner": "B", "reopen_trigger": "t", "ruling": "r", "rationale": "x",
     "files": [{"path": P, "missing_symbols": ["lorerunes.FixtureOtherPlaceholder"]}]}
for label, bounds, lines in (
    ("SHARED", [A, B], [err("FixturePlaceholder"), err("FixtureOtherPlaceholder"), UNSYM]),
    ("CONTROL", [A], [err("FixturePlaceholder"), UNSYM]),
):
    gate = PendingContractGate(PendingContractRegistry.model_validate({"version": 1, "bounds": bounds}), Path("."))
    run = MypyOutputReader.read(transcript(lines))
    part = gate.partition_mypy(run)
    print(label, "expected", len(part.expected), "unexpected", len(part.unexpected))
    for finding in gate.transcript_self_destruct_findings(run):
        print(label, "FINDING:", finding[:200])
```
Output at `60a369c` + fix2:
```
SHARED expected 3 unexpected 0
SHARED FINDING: SELF-DESTRUCT: lorerunes/tests/test_posture.py declares 1 unsymboled 'attr-defined' error(s); 2 observed. …
CONTROL expected 2 unexpected 0
```

Mutation anchors and replacements, all run with `scripts/mutation_proof.py --anchor-file/--replacement-file` except M1:
- §1: anchor `found = self.registry.entry_for(error.path)` / `if found is not None and found[1].admits(error):`. Replacements:
  - M1: `found = [e for b in self.registry.bounds for e in b.files if e.path == error.path]` / `if any(entry.admits(error) for entry in found):`
  - M2: same `found` / `if found and found[-1].admits(error):`
  - M3: same `found` / `if found:`
- §2: P1 and P2 insert a planted function before `def production_catch_sites()` in `_catch_sites.py`. P3 replaces `return aliases.get(call.func.id, call.func.id)` → `return call.func.id`. P4 replaces the three-line `if name not in reaching and called & reaching:` block → `pass`.
- §3: anchor = `_dispatch_migrate_governed`'s 4-member `except (` tuple. E1 swaps `SurrealConnectionError` → `SurrealStoreError`. E2 does the same swap and also moves `SurrealStoreError` ahead of `KeepStoreError`.
- Each declared RED set was written before its run, from `--collect-only` ids, and every proof printed `PROOF HELD … fired EXACTLY` with `tree restored byte-exact`.

## FLAGS
- The main tree was not touched except for this report. #486's WIP there is unaffected: the commit stages this file only.
