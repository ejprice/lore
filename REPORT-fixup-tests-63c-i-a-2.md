brief-base v18 read · brief project v7 read

# REPORT — fixup-tests-63c-i-a-2 (test side of 63c am-37 §11, R2-1)

## SUMMARY BLOCK
- **State:** done. Tests only; no production file ships. Measured 2026-09-30 on fix3 r2 (patch md5 `f5897681…`) over HEAD `0b0011b`.
- **Deviations:** (1) the pin also scripts `principal_keys.build_principal_key_store` (a third fake) so the sweep never opens a socket; the brief names two factories (§Readings R1). (2) The reference build was an in-place `cp -a`/`cmp`-guarded edit of the scratch copy's `principals.py`, not a separate sub-copy. It was restored byte-exact before and after, and the patches were cut before it (§4).
- **Packages considered:** none. No mechanism was specified. argparse introspection is stdlib, and the only helper is the repo's own `scripts/mutation_proof.py`.
- **Odoo-20 portability:** n/a. No Odoo seam touched.
- **Reuse ledger:** 5 new test-local symbols (`_subparsers_action`, `_derived_verbs`, `_option_argv`, `_minimal_argv`, `_ScriptedStore`, plus the `_run_verb_against`/`_assert_laundered` helpers). All are private to `test_principals_cli.py` and have no existing twin. The argparse-derivation helpers are the first of their kind in the tree (awk sweep for `_SubParsersAction` in the tests found none).
- **Graded:** n/a (author, not grader). Built on `0b0011b` + r2. HEAD-at-report is `0b0011b`, SAME.
- **Decisions needed:** (a) three test DOCSTRINGS in files outside my writable set teach the retired FR-2 D1 policy. One of them also claims a guard that §11 removes (§5 F-1). Who edits them? (b) I read the role boundary as allowing my mutation proof of my own pin (§Readings R2).
- **Receipt pointers:** RED §2 · reference GREEN + mutation §3 · STOP checks §1 · currency §6 · patches §7 · instrument §8.

## 0. Capability check
All demanded capabilities were present. lore_comms was registered (session `63c-20260924`). grep/rg are hook-blocked (#473), so every search here was `awk` over files. The consumer sweeps in §1 are therefore textual awk scans, not `lore_impact`. I'm saying so per the dogfood protocol. That is fallback case (b): string keys like `"principals.py::…"` are non-symbol textual seams.

## 1. STOP-condition checks (am-37 §11 item 5), done BEFORE editing
| condition | check (awk over `loremaster/tests/*.py` + `scripts/*.py`) | verdict |
|---|---|---|
| 58 runtime cross-check has a driver keyed to a deleted site | The only `principals.py::` string keys in the test tree are the two `_exhaustion_fates.py` rows and `_migrate_memory_scope` (in `_governed_contract.py` / `test_memory_enforcement_63a_v.py`, which is a different function). The cross-check population is `test_reanchor_58_r3_cas_seam.listed_handlers()`, built from `test_retry_seam._GUARDED_CAS_DOORS ∪ _TYPED_CAS_CATCHES`. Neither of those sets names `principals.py`. | **Not fired.** No re-key was needed; the fallback was not taken. |
| a pin asserts a dispatcher's `except` tuple (AST / `__doc__`) | The only tuple readers are the fates rows (re-keyed here). | **Not fired.** |
| a pin drives a fault into `_dispatch_migrate_governed` and asserts the catch IN that frame | `test_fixwave_a28c_63c_i_a.py::…test_am34_4_the_cli_render_derives_the_sentence_from_the_typed_field` calls `principals._dispatch_migrate_governed(...)` directly, but only on the success path (`assert code == 0`, no fault). | **Not fired.** It is unaffected, because the frame still returns 0 on success. |

## 2. Per-edit table
| edit | §11 clause | RED on fix3-as-is (reason) | GREEN on reference build | control |
|---|---|---|---|---|
| `_exhaustion_fates.py`: delete rows `principals.py::_dispatch_migrate_governed`, `…::_dispatch_report_unmigrated`; add one row `principals.py::_dispatch` = `Fate("cli-exit","principals",("stderr","returns-named-outcome"), catches="(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)")` (string split over two lines for E501; the value was verified equal by import) | item 4, TEST SIDE | `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site` RED. The `_dispatch` row has no in-domain site, and the two dispatchers still catch `SurrealStoreError` without rows. | GREEN | The `…_matched_to_ITS_site_by_the_caught_expression` pin is GREEN on the reference build, so the `catches=` string equals `ast.unparse` of the reference tuple. |
| `test_principals_cli.py` `TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[<verb>]`. Verbs are DERIVED from `build_parser()` (17 at this sha) and argv is DERIVED per subparser. One injection point: every store factory's `ensure_ready` raises `TxnDomainRejectionError("(assert violation); see the server log")`. Asserts: the injection was reached, `rc == 1`, stderr's first line starts with `lore-adm: ` and carries the injected text, stdout is empty, no `Traceback`, and every built store is closed. | item 4, GENERATED pin | RED ×15: every principal/key verb and every keep verb. The failure is `ESCAPED TxnDomainRejectionError: …`, i.e. a traceback, never an ARGV/fixture failure. GREEN ×2: `migrate-governed` and `report-unmigrated`, whose own tuples already catch the base. | GREEN 17/17 | — |
| `…::test_CONTROL_a_transport_fault_takes_the_same_fate[<verb>]` | item 4, control 1 | GREEN 17/17 at fix3 (already-laundered class). So the domain-rejection RED is about the fault CLASS, not the harness. | GREEN 17/17 | positive control |
| `…::test_CONTROL_a_succeeding_verb_exits_0_with_empty_stderr` (`list` over an empty scripted store) | item 4, control 2 | GREEN | GREEN | negative control: the harness does not manufacture exit 1 |
| `…::test_the_derived_verb_set_is_not_vacuous` (derived ⊇ `_VERB_HANDLERS ∪ _KEEP_VERB_HANDLERS ∪ {migrate-governed, report-unmigrated}`) | rule 2 completeness | GREEN | GREEN | a derivation that shrinks reds |

**Declared-vs-observed diff (RED run, fix3-as-is):** 113 ids were collected. 16 were declared RED BEFORE the run by a predicate over the `--collect-only` ids (§8). Observed: 17 failed, 96 passed. **DECLARED_BUT_GREEN = 0.** **UNEXPECTED_RED = 1:** `test_exhaustion_fates.py::…test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS`. Its assertion list is exactly three `store/lease.py::{get,create,release_if_held}#0 … ['logs-error-class']` problems. That is 58's r4 rider, adjudicated to `packet-58-contract` (`scripts/pending_contracts.yaml`, the packet-58 entry naming `test_exhaustion_fates.py`). No problem in it names `principals`, so it is not attributable to this edit. My declaration missed it because I did not know that pre-existing owned red. I'm naming the miss rather than editing the declaration after the fact.

## 3. Reference build (throwaway, NEVER shipped) + mutation proof
- `cp -a principals.py → principals.py.fix3r2.bak`. Then I applied §11 item 4 (i)+(ii): one `try/except (PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)` in `_dispatch` around all routing, and the `except` blocks stripped from `_dispatch_keep`, `_dispatch_migrate_governed` and `_dispatch_report_unmigrated`. I did not do (iii), the docstring rewrite. The builder owns it.
- Targeted run on the reference build (`test_principals_cli.py test_exhaustion_fates.py test_keeps_cli.py test_keep_remediation_cli_61.py test_reanchor_58_r4_lease_fates.py test_reanchor_58_r3_cas_seam.py`): **9 failed, 196 passed.** All of my nodes and the fates both-ways pin are GREEN. The 9 reds are the lease evidence-HOLDS pin plus 4 lease-fates legs plus 4 CAS-population legs (findings/tasks). **Baseline at fix3-as-is over the four non-mine files: 8 failed, 84 passed, the IDENTICAL 8 node ids.** So the production edit adds 0 attributable reds, and the keeps-CLI suites are green on both builds.
- **Mutation (`scripts/mutation_proof.py`):** one keep verb bypasses the handler (`if args.command == "delete-keep": return await _dispatch_keep(args, config)` inserted before `_dispatch`'s `try:`). It was declared RED: `…test_a_domain_rejection…[delete-keep]` and `…test_CONTROL_a_transport_fault…[delete-keep]`. Result: **"PROOF HELD — the declared RED set fired EXACTLY"** (2 failed, 83 passed), and the tool restored the tree byte-exact (md5 `71336db1…`). `cmp` against my own `cp -a` backup was also clean.
- Restore: `cp -a principals.py.fix3r2.bak` → `cmp` clean. `git diff --binary HEAD | md5sum` = `85a4d2e1…`, which is the delivered full patch, so the delivered tree carries no production edit of mine.
- Provenance: `loremaster.__file__` = `…/scratchpad/fixup2/loremaster/loremaster/__init__.py` (scratch_copy.sh asserted all four members inside the copy).

## 4. Readings (two-reading triggers, written down per brief-base §2)
- **R1, the injection point.** The brief says monkeypatch `build_principal_store` / `build_keep_store`. The principal/key branch also calls `principal_keys.build_principal_key_store`, which the brief does not name.
  - Reading A: patch only the two named factories. The key store would then be real. That is harmless today, because the principal store raises first and the key store is never readied (only `close()`d). It stops being harmless if a builder reorders readiness: the sweep would then open a socket to the config URL.
  - Reading B (picked): all three factories return the same scripted fake. It is still ONE injection point (store readiness), with no network.
- **R2, the role boundary.** The brief asks me to show the pin RED "when one keep verb's route bypasses the handler". brief-base §2 forbids a contract author "building wrong implementations".
  - Reading A: that is grader duty, so refuse it.
  - Reading B (picked): it is the author's own mutation proof of its own pin. Repo CLAUDE.md §TEST SCOPE lists "contract author (RED, SAT, mutations)", it is one declared mutation through the repo instrument, and it does not replay any grader's builds.
  - If the lead reads it as A, discard §3's mutation leg. The RED/GREEN receipts stand without it.
- **Spec wording vs observation.** §11 item 4 says the pin "reds at fix3-as-is on `delete` and every keep verb". Observed: it reds on EVERY principal/key verb too (15 in total), because the injection is `ensure_ready`, which every route reaches. This matches §11 item 1's own table: the principal/key branch lets every non-transport `SurrealStoreError` through, including "any rejected `ensure_ready` DDL". It is consistent with the ruling, not a deviation.
- The argv placeholder for a non-choice option is `x@example.com` (set-expiry's required group takes `--at x@example.com`, for example). It parses, and the verb never reads it because the fault fires in `ensure_ready` first. The success control uses `list`, which takes no args.

## 5. Flags (surfaced, not edited: outside my writable set)
- **F-1 (P8d class, stale teaching + lost guard).** `test_keeps_cli.py::…test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero`'s docstring says it *"doubles as a CLI-level guard that the Q2b wrap happened: `_dispatch_keep` no longer catches raw `SurrealStoreError` (FR-2 D1), so a `KeepStore` that leaked the raw engine error would escape and crash instead of exiting 1"*. After §11 that is FALSE. The raw error is caught at `_dispatch` and exits 1, so this test no longer detects a missed wrap.
  - §11 item 1 says the missed-wrap property "stays enforced by the FR-2 wrap pins over KeepStore's write boundaries". **NOT TRIED:** I did not verify that a KeepStore-level pin covers the `add_household` RELATE wrap.
  - Proposed edit: delete the "Doubles as…" sentence and replace it with *"The missed-wrap property is pinned at KeepStore's write boundary (FR-2), not here: since 63c am-37 §11 the one lore-adm handler at `_dispatch` catches `SurrealStoreError`."*
- **F-2.** `test_keeps_cli.py::…test_a_nonexistent_keep_is_a_loud_exit_1`'s docstring says *"`_dispatch_keep` does NOT catch"* a `NotImplementedError`. It is still true (it is not in the tuple), but the catching frame is now `_dispatch`. This is wording only.
- **F-3.** `test_keep_remediation_cli_61.py`'s module docstring says keep verbs route through `_dispatch_keep` *"whose `except KeepStoreError`"*. After §11 `_dispatch_keep` has no `except`, so the docstring is stale.
- **F-4.** The fates comment I replaced carried the §8.1 provenance. My new comment says the §8.1 rows are superseded, per §11 item 4.

## 6. Currency (`uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`, no pytest)
BEFORE (fix3 r2, my edits not yet applied), verbatim tail:
```
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (…) · packet-64b-i-contract (…)
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
exit=1
```
AFTER (fix3 r2 + my edits, reference edit reverted), verbatim tail:
```
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (…) · packet-64b-i-contract (…)
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
exit=1
```
- Typecheck residuals are 83 → 83, all adjudicated, so my tests add 0 mypy errors. `uv run ruff check .` reported "All checks passed!".
- The FAIL line is the `--legs` mode's expected rendering of the unrun pytest leg (by design; the full suite is the cold audit's). Across the typecheck/ruff legs, RED_ORPHANED = 0.
- The owner texts are elided with `(…)` above. The full files are `…/scratchpad/currency-{before,after}.txt` (scratch, not durable).

## 7. Patches
| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.full.patch` (fix3 r2 + my edits) | HEAD `0b0011b` | `85a4d2e175a974633d60a81e8020d060` | OK (temp index = HEAD) |
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.delta.patch` (tests only: `_exhaustion_fates.py`, `test_principals_cli.py`) | HEAD `0b0011b` + r2 | `c216df30dddbb066752adcc5c4fec1bb` | OK (temp index = HEAD + `git apply --cached` r2) |

## 8. Instrument (pasted verbatim per brief-base §1): the declared-vs-observed RED diff
```python
"""Declared-vs-observed RED diff (fixup-tests-63c-i-a-2). Usage:
    red_diff.py declare <collected.txt> <declared.txt>   # predicate over --collect-only ids, BEFORE the run
    red_diff.py diff <declared.txt> <junit.xml>          # both ways: unexpected reds, declared reds that stayed green
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SHOULD_STAY_GREEN = ("[migrate-governed]", "[report-unmigrated]")

def declared(node_id: str) -> bool:
    if "test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[" in node_id:
        return not node_id.endswith(_SHOULD_STAY_GREEN)
    return node_id.endswith("test_every_non_derived_site_has_a_row_and_every_row_a_site")

def main() -> int:
    mode = sys.argv[1]
    if mode == "declare":
        ids = [line.strip() for line in Path(sys.argv[2]).read_text().splitlines() if "::" in line]
        red = [i for i in ids if declared(i)]
        Path(sys.argv[3]).write_text("\n".join(red) + "\n")
        print(f"collected={len(ids)} declared_red={len(red)}")
        return 0
    want = {line.strip() for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()}
    root = ET.parse(sys.argv[3]).getroot()
    observed, passed, total = set(), 0, 0
    for case in root.iter("testcase"):
        total += 1
        parts = case.get("classname", "").split(".")
        cls = parts[-1] if parts[-1][:1].isupper() else None
        mod = "/".join(parts[:-1] if cls else parts) + ".py"
        node = f"{mod}::{cls}::{case.get('name')}" if cls else f"{mod}::{case.get('name')}"
        if case.find("failure") is not None or case.find("error") is not None:
            observed.add(node)
        elif case.find("skipped") is None:
            passed += 1
    norm = lambda s: s.split("tests/")[-1]
    want_n, obs_n = {norm(w) for w in want}, {norm(o) for o in observed}
    unexpected, stayed_green = sorted(obs_n - want_n), sorted(want_n - obs_n)
    print(f"total={total} passed={passed} observed_red={len(obs_n)} declared_red={len(want_n)}")
    print(f"UNEXPECTED_RED ({len(unexpected)}):", *unexpected, sep="\n  ")
    print(f"DECLARED_BUT_GREEN ({len(stayed_green)}):", *stayed_green, sep="\n  ")
    return 0 if not unexpected and not stayed_green else 1

if __name__ == "__main__":
    raise SystemExit(main())
```
The mutation leg used the committed `scripts/mutation_proof.py` (anchor/replacement files as in §3).

## 9. Run hygiene
- Every pytest run was targeted, `-n 8`, `--timeout=300`, under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`. MemAvailable was 28–29 GiB at admission, and no other lore pytest was live.
- The new pins are hermetic: fake stores, no socket, no `:18500`, no embedder. The keeps-CLI covering tests used the `:18000` TEST store via their own fixtures.
- No worktree, no stash, no deploy, no `checkout --`.
