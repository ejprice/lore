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

## ROUND 2 (lead brief ~02:30Z; measured 2026-09-30 on HEAD `0b0011b` + fix3 r2 + round-1 full patch `85a4d2e1…`)

**SUMMARY:**
- **State:** done, no STOP. Every derived KeepStore data-write boundary has a KeepStore-level wrap pin. `add_household_member`'s wrap was mutation-proven, and 9 stale docstring sites were fixed (F-1..F-3 plus 6 more found by sweep).
- **Deviations:**
  - (1) ⚠ **Memory admission gate violated once.** The `keeps.py` mutation run started at MemAvailable **18 GiB** (< 20). I noticed only after it finished (5 failed / 61 passed, cgroup-capped at 16G, no kill). The next run was admission-gated with a wait loop and started at 28 GiB.
  - (2) The docstring sweep went beyond the three flagged sites. Each extra site carried the same false "laundered by `_dispatch_keep`" claim.
- **Decisions needed:** R2-F1 below, a residual bound for the sidecar. Not a STOP.

### R2-1. Derived boundary table (instrument: `derive_keep_writes.py`, pasted in R2-5)
The boundaries are derived by AST over `KeepStore`'s methods in `loremaster/loremaster/keeps.py`. A write sink is either (a) `self._query(<stmt>)` whose literal text begins with CREATE/RELATE/UPDATE/DELETE/UPSERT/INSERT/BEGIN, or (b) any `execute_transaction(...)` call.
- **Instrument gap, found and fixed during the run:** the first pass keyed only on sink (a) and MISSED `create_keep` and `get_or_create_keyed`, whose writes are composed transactions. Sink (b) closed that gap.

| boundary (method) | write | inside `wrap_store_rejection(KeepStoreError, …)` | pin that fails if it leaks a raw `SurrealStoreError` |
|---|---|---|---|
| `create_keep` | TXN (CREATE + RELATE) | yes | `test_engine_rejection_seam.py::TestEngineRejectionWrappingBehaviourIsPreserved::test_a_raw_store_error_surfaces_as_the_domain_error[keep-create_keep]` |
| `get_or_create_keyed` | TXN (CREATE + RELATE) | yes | `…[keep-get_or_create_keyed]` |
| `add_household_member` | RELATE | yes | `…[keep-add_household_member]` (**mutation-proven**, R2-2) |
| `remove_household_member` | DELETE | yes | `…[keep-remove_household_member]` |
| `set_rank` | UPDATE | yes | `…[keep-set_rank]` |
| `set_keeper` | UPDATE | yes | `…[keep-set_keeper]` |
| `delete_keep` | DELETE | yes | `…[keep-delete_keep]` |
| `ensure_ready` | TXN (DDL) | **no, by design** (§11 item 1: every `ensure_ready` is un-wrapped) | not a FR-2 boundary. Its fault fate is now pinned by round 1's generated CLI pin, whose injection point IS `ensure_ready`. |

- **Coverage is a checked variable:** `TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_invocation_map[keep]` asserts that the AST-derived set of methods referencing `wrap_store_rejection` EQUALS the fault-injection invocation map. That map also carries `list_keeps_for_member`, a born-wrapped READ.
- **Injection:** `_inject_store_error` patches `keeps.run_query` / `keeps.execute_transaction` with a raw `SurrealStoreError`. A leaked wrap therefore surfaces as a non-`KeepStoreError`.

### R2-2. Mutation receipt (`scripts/mutation_proof.py`, KeepStore-level file only)
- **Setup:** `cp -a keeps.py → keeps.py.bak`. The mutation replaced `add_household_member`'s `with wrap_store_rejection(KeepStoreError, "could not add member …"):` with `if True:` (body unchanged).
- **Declared RED (5, from `--collect-only` ids, before the run):** `test_a_raw_store_error_surfaces_as_the_domain_error[keep-add_household_member]`; `test_dropping_LAYER1_reclassify_moves_every_routed_path[keep-add_household_member]`; `test_dropping_LAYER2_wrap_store_rejection_moves_every_routed_path[keep-add_household_member]`; `test_the_routed_set_equals_the_invocation_map[keep]`; `test_the_routed_set_equals_the_known_wrapping_verbs[keep]`.
- **Result:** **5 failed, 61 passed. "PROOF HELD — the declared RED set fired EXACTLY."** The tool restored the tree byte-exact (md5 `6945cb55…`), and `cmp keeps.py keeps.py.bak` was clean.
- The CLI test was not in this run, so the RED comes from the KeepStore-level pins, as the brief required.

### R2-3. Docstring edits (writable set: docstrings of the two files ONLY)
- **Proof they are docstring-only:** each file's AST, with every docstring blanked, is equal before and after (`AST-EQUAL-MODULO-DOCSTRINGS` for both). `ruff check` on both files is clean.
- **Residual sweep:** a bare awk pattern over both files for `laundered by ``_dispatch_keep``` / `_dispatch_keep`` catches` / `_dispatch_keep`` does NOT` / `except KeepStoreError` returned **0 hits**.

Verdict on every `_dispatch_keep` mention in the two files:

| file · test / site | verdict | edit |
|---|---|---|
| `test_keeps_cli.py` module docstring (`_dispatch_keep` wiring are REAL; readies the principal table) | true, kept | — |
| `test_keeps_cli.py` `# routing pin passes at stub…` | a comment, not a docstring (outside the writable set), true | — |
| `test_keeps_cli.py` the rank-ASSERT test ("laundered by `_dispatch_keep`") | FALSE after §11 | → "laundered by the one lore-adm fault handler at `_dispatch` (63c am-37 §11)" |
| `test_keeps_cli.py` "(`_dispatch_keep` readied the empty…)" | true, kept | — |
| `test_keeps_cli.py::…test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero` (**F-1**) | FALSE: "Doubles as a CLI-level guard" | catching frame → `_dispatch` (§11). States the missed-wrap property is NOT pinned here and names the R2-1 pin `…[keep-add_household_member]` plus `TestTheRoutedSetIsDerivedAndComplete`. |
| `test_keeps_cli.py::…test_a_nonexistent_keep_is_a_loud_exit_1` (**F-2**) | catching frame stale | → "which the one handler at `_dispatch` (63c am-37 §11) does NOT catch" |
| `test_keep_remediation_cli_61.py` module docstring (**F-3**) | FALSE: "whose `except KeepStoreError` launders" | → laundered by the one handler at `_dispatch` (am-37 §11) |
| `…test_the_new_verbs_are_registered_in_the_keep_handler_table` | FALSE: "(and its `KeepStoreError` launder)" / "would mis-launder" | → "(the KeepStore route)" / "would mis-route them", plus a one-line note that faults on every route go to `_dispatch`. **Reading flag:** the old "mis-launder" rationale no longer holds after §11, so I restated the pin's purpose as ROUTING. Its assertion (membership of `_KEEP_VERB_HANDLERS`) is unchanged. |
| `…` unknown new-keeper test ("guard laundered by `_dispatch_keep`") | FALSE | → "by the one handler at `_dispatch` (63c am-37 §11)" |
| `…` set-keeper ghost-keep test ("`KeepNotFoundError` laundered by `_dispatch_keep`") | FALSE | → same |
| `…` delete-keep ghost-keep test (same claim) | FALSE | → same |
| `test_keep_remediation_cli_61.py` `# delete-keep's own _dispatch_keep readies the keep slice` | a comment, true | — |

The full text is in the delta patch (46 changed lines; `diff --git` touches exactly those two files).

### R2-4. Runs, gates, patches
- **Targeted six files on the fix3 r2 base** (full patch + docstrings; admission-gated at MemAvailable 28 GiB; `-n 8`, `--timeout=300`, 16G cgroup): **25 failed, 180 passed.** The FAILED set is **IDENTICAL** to round 1's two runs (17 from `red.log` + 8 from `base58.log`, diffed by node id), so the docstring edits moved no node.
- `uv run ruff check .`: All checks passed!
- `--currency --legs typecheck,ruff`, verbatim:
  ```
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (…) · packet-64b-i-contract (…)
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
  CURRENCY   : FAIL — claimed but never run: pytest
  exit=1
  ```
  83 → 83, RED_ORPHANED 0. The FAIL is the `--legs` mode's unrun pytest leg (see §6).

| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.docstrings.delta.patch` (ONLY `test_keeps_cli.py` + `test_keep_remediation_cli_61.py`) | HEAD `0b0011b` + full (`85a4d2e1…`) | `afa519cf7c4eca5241a060ca80cbc367` | OK (temp index = HEAD + full `--cached`) |
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.full2.patch` (full + docstrings) | HEAD `0b0011b` | `e915b90f7f58712e164608a7fc8d2002` | OK (temp index = HEAD) |

The docstring delta is disjoint from the builder's `principals.py`-only delta, so the two compose.

### R2-F1. Residual bound for the sidecar (a flag, not a STOP)
- **What is covered:** today's boundaries are all covered, but the coverage population is "methods that REFERENCE `wrap_store_rejection`" (`_methods_routing_through_seam`), not "methods that WRITE". A NEW KeepStore write method written with NO wrap would join neither the routed set nor the invocation map, so no pin reds. The `expected_wrappers` set is a hand-list.
- **Why §11 matters here:** before §11, such a leak on a CLI path at least tracebacked through `_dispatch_keep`, incidentally and only where a CLI test drove a rejection. After §11 it exits 1 with a `lore-adm:` line. So §11 removes that incidental CLI-side signal for FUTURE unwrapped write methods, not for any existing one.
- **Proposed class pin (not written; the brief scopes me to docstrings):** assert that the AST-derived KeepStore write set (R2-5's instrument, minus `ensure_ready`) ⊆ `_methods_routing_through_seam(keeps_module, "KeepStore")`.
- **Re-open trigger:** the next KeepStore write method.

### R2-5. Instrument (pasted verbatim; the scratch copy is disposable)
```python
"""Derive KeepStore's WRITE boundaries from production by AST (fixup-tests-63c-i-a-2 round 2).
A write boundary = a KeepStore method containing a ``self._query(<stmt>, ...)`` whose statement text
(str / f-string / concatenation, literal parts joined) begins with a write verb, OR any
``execute_transaction(...)`` call (a transaction is a write by construction). For each, report
whether every such call sits lexically inside ``with wrap_store_rejection(KeepStoreError, ...)``."""
import ast, sys
from pathlib import Path

WRITE_VERBS = ("CREATE", "RELATE", "UPDATE", "DELETE", "UPSERT", "INSERT", "BEGIN")

def literal_text(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(literal_text(v) if isinstance(v, ast.Constant) else "{}" for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return literal_text(node.left) + literal_text(node.right)
    return "<dynamic>"

def is_wrap(item: ast.withitem) -> bool:
    call = item.context_expr
    return (isinstance(call, ast.Call) and getattr(call.func, "id", getattr(call.func, "attr", "")) == "wrap_store_rejection"
            and call.args and getattr(call.args[0], "id", "") == "KeepStoreError")

tree = ast.parse(Path(sys.argv[1]).read_text())
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "KeepStore")
for method in cls.body:
    if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
        continue
    found = []
    def walk(node, wrapped):
        for child in ast.iter_child_nodes(node):
            w = wrapped or (isinstance(child, (ast.With, ast.AsyncWith)) and any(is_wrap(i) for i in child.items))
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "_query"
                    and child.args):
                text = literal_text(child.args[0]).lstrip()
                if text.upper().startswith(WRITE_VERBS) or text == "<dynamic>":
                    found.append((child.lineno, text.split()[0] if text.split() else text, w))
            if isinstance(child, ast.Call) and getattr(child.func, "id", getattr(child.func, "attr", "")) == "execute_transaction":
                found.append((child.lineno, "TXN(execute_transaction)", w))
            walk(child, w)
    walk(method, False)
    if found:
        print(f"{method.name}: " + ", ".join(f"L{l} {verb} wrapped={w}" for l, verb, w in found))
```
Output at `0b0011b`+r2: `ensure_ready: L286 TXN wrapped=False · create_keep: L508 TXN wrapped=True · get_or_create_keyed: L594 TXN wrapped=True · add_household_member: L679 RELATE wrapped=True · remove_household_member: L748 DELETE wrapped=True · set_rank: L782 UPDATE wrapped=True · set_keeper: L856 UPDATE wrapped=True · delete_keep: L922 DELETE wrapped=True`.

## ROUND 3: am-37 §12 (commit `4e3a96c`) test side, the derived wrap-coverage pin
*Measured 2026-09-30 in scratch `fixup2`, on HEAD `0b0011b` + full2 (`e915b90f…`). Full3 also `apply --check`s at main HEAD `e1d36d5`, which adds no loremaster/scripts changes over `0b0011b`.*

**SUMMARY:**
- **State:** done, no STOP fired (STOP 1, 3 and 4 are all checked below).
- **Deviations:** none. Everything lives in `test_engine_rejection_seam.py`, so no helper module was created.
- **Decision for the builder, a two-reading trigger:** the new `delete` fault-injection invocation lands on the FIRST principals-seam call, the `get_by_email` READ that opens `delete`. The pin therefore requires `delete`'s wrap to enclose its store calls FROM THAT READ ON, not the TXN alone. The reference did exactly that, and every a19b/63a delete pin stayed green (see STOP 1).
  - Reading A (TXN-only wrap) leaves `test_a_raw_store_error_surfaces_as_the_domain_error[principal-delete]` red.
  - §12's TXN-only placement is the STOP-1 fallback only, and STOP 1 did not fire. So I picked reading B, the whole-body wrap, as KeepStore's verbs do.
- **Admission gate:** a wait-loop before EVERY run. The three pytest runs and the mutation run started at MemAvailable 22 GiB each. No slip.

### R3-1. STOP 1: `wrap_store_rejection` passes non-`SurrealStoreError` through UNTOUCHED (it does not fire)
`loremaster/loremaster/store/_txn.py::wrap_store_rejection`:
```python
    return reclassify(
        passthrough=(SurrealConnectionError, TxnContentionExhaustedError),
        catch=(SurrealStoreError,),
        make_error=lambda: domain_error(context),
    )
```
`lorerunes/lorerunes/engine_rejection.py::reclassify` (docstring: "every other exception propagates unchanged — this manager never uses a bare `except Exception`"):
```python
    try:
        yield
    except passthrough:
        raise
    except catch as error:
        raise make_error() from error
```
Live MRO checks:
- `PrincipalHasKeepsError` → `PrincipalStoreError → RuntimeError`, `issubclass(…, SurrealStoreError) = False`.
- `PrincipalOwnsGovernedRowsError` → the same, `False`.
- So a whole-body `delete` wrap passes both refusals through by class.

Empirical confirmation: with the reference wraps, `test_fixwave_a19b_63c_i_a.py`, `test_principal_delete_governed_63a.py` and `test_principal_delete_cascade_61.py` all passed (R3-4).

### R3-2. The edits (`loremaster/tests/test_engine_rejection_seam.py` only)
- **Derivation (the R2-5 instrument promoted into the file, beside `TestTheRoutedSetIsDerivedAndComplete`):**
  - `_dispatch_store_classes()` finds the `build_*_store` calls in `principals._dispatch`'s AST. It resolves each factory's module through the `from … import` that binds it in `principals.py` (default: `principals`), then the class through the factory's own return annotation. Result at base: {`PrincipalStore`, `PrincipalKeyStore`, `KeepStore`}.
  - `derived_write_boundaries(case)` covers two sinks:
    - (a) `_query(<stmt>)` / `run_query(statement=<stmt>)`, a write unless its literal text opens with a READ verb (`SELECT`/`RETURN`/`INFO`). **Allowlist the safe:** a dynamic or placeholder-led statement is a write.
    - (b) any `execute_transaction(...)`.
  - Each sink records whether it sits lexically inside `wrap_store_rejection(<that store's error>, …)`.
  - `_EXEMPT_WRITE_METHODS` has exactly two entries, each with a reason: `ensure_ready` (DDL; its fate is pinned by round 1's CLI pin) and `_query` (the seam, whose statement is its caller's; every caller is itself a sink).
  - The governed-migration legs are module functions, not store methods, so they are outside the domain by construction (§12 item 1).
- **`TestEveryDerivedWriteBoundaryIsWrapped`** (new):
  - `test_the_write_boundary_sits_inside_its_stores_wrap[<label>::<method>]` is parametrized at COLLECTION over ∀ reached store ∀ derived boundary. A new boundary, or a store with no `_StoreCase`, therefore reds BY NAME.
  - `test_the_store_set_is_derived_from_dispatch_and_every_store_has_a_case` (non-vacuity plus completeness).
  - `test_POSITIVE_CONTROL_the_walker_sees_wraps_and_the_exemptions_are_live[<label>]` checks that the walker sees ≥1 wrapped sink per store. It also checks that each exemption names a method that really writes unwrapped, so there are no dead or stale exemptions.
- **Re-keyed expectation:** `_StoreCase.expected_wrappers` is now a PROPERTY: the derived write set ∪ `_DECLARED_READ_WRAPPERS[label]`. The old constructor hand-list `frozenset(<invocation map>)` was removed from all three cases. The declared read-wrappers are only `keep: list_keeps_for_member`, with its 61b-w2 D1 reason.
  - New `TestTheRoutedSetIsDerivedAndComplete::test_the_invocation_map_equals_the_derived_expectation[<label>]`: the fault-injection map must equal the derived expectation.
- **Invocation map grew by 4:**
  - `principal`: `set_status(email=KEEPER, status="suspended")`, `set_expires(email=KEEPER, expires_at=None)`, `delete(email=MEMBER)`.
  - `principal_key`: `revoke(email=KEEPER, name="laptop")`.
  - Each flows through the existing ∀ pins (`test_a_raw_store_error…`, `test_transport_faults_propagate_untouched`, LAYER1, LAYER2).
- `ruff check` is clean. Collection: 107 tests.

### R3-3. RED on the full2 base (no production wraps)
- **Declared** before the run, as a predicate over `--collect-only` ids:
  - 20 seam nodes:
    - the boundary pin for `principal::{delete,set_expires,set_status}` and `principal_key::revoke`;
    - `test_the_routed_set_equals_the_{invocation_map,known_wrapping_verbs}[principal|principal_key]`;
    - `test_a_raw_store_error…`, LAYER1 and LAYER2 for `principal-{delete,set_expires,set_status}` / `principal_key-revoke`.
  - Plus round 1's 17 known reds (`test_principals_cli` ×15 and the fates both-ways pin, which await the §11 production edit; the lease evidence pin is owned by packet 58).
- **Observed** (8 files, see R3-4): **37 failed, 293 passed. UNEXPECTED_RED 0, DECLARED_BUT_GREEN 0.**
- The boundary pin reds on EXACTLY the four §12 boundaries. `principal::create`, `principal::set_subject`, `principal_key::mint` and all 7 keep boundaries are green.

### R3-4. GREEN on the throwaway reference + STOP 3 + mutation
- **Reference build:** `cp -a` of `principals.py` / `principal_keys.py`, then the 4 wraps in the existing message shape:
  - `set_status`: the UPDATE.
  - `set_expires`: both branches.
  - `delete`: from `get_by_email` through the TXN.
  - `revoke`: the UPDATE.
- **Reference run** (the same 8 targeted files, found by filename awk for `a19b|principal_delete|principal_keys`: `test_engine_rejection_seam.py test_exhaustion_fates.py test_principals_cli.py test_fixwave_a19b_63c_i_a.py test_principal_delete_governed_63a.py test_principal_delete_cascade_61.py test_principal_keys_store.py test_principal_keys_schema.py`): **17 failed, 313 passed.** The failed set EQUALS round 1's 17 exactly (diffed both ways: 0 / 0), so all 20 round-3 reds went green and nothing else moved.
- **STOP 3 (58 catch-site scanner / fates) does not fire.** In the reference run the fates both-ways failure message names only `principals.py::_dispatch_migrate_governed`, `…::_dispatch_report_unmigrated` and the `…::_dispatch` row, which are round 1's §11-pending reds. No row or site is keyed to `set_status` / `set_expires` / `delete` / `revoke`, and the `with` adds no `except`.
- **STOP 4 (a `principal_keys.py` writable-set gap):** I did not take the declared-pending form. `revoke` is pinned as an ordinary member, because §12 item 2 assigns the `revoke` wrap to this fold's production side. If the builder cannot touch `principal_keys.py`, only `[principal_key::revoke]` and its three ∀ siblings stay red, by name. That is the lead's call.
- **Fifth-wrap mutation** (`scripts/mutation_proof.py` on the reference): `PrincipalStore.create`'s `with wrap_store_rejection(PrincipalStoreError, "could not create principal …"):` was replaced by `if True:`.
  - Declared: `[principal::create]` boundary pin, `routed_set_equals_the_invocation_map[principal]`, `…known_wrapping_verbs[principal]`, `raw_store_error[principal-create]`, and LAYER1/LAYER2 `[principal-create]`.
  - Result: **6 failed, 101 passed, "PROOF HELD — the declared RED set fired EXACTLY"**. The tool restored the file byte-exact, and `cmp` against the `cp -a` backup was clean.
- **Restore:** both production files were copied back from the full2 backups, and `cmp` was clean for both. The r3 delta touches exactly one file, the test file.

### R3-5. Gates and patches
- `uv run ruff check .`: All checks passed!
- `--currency --legs typecheck,ruff`: typecheck RED_ADJUDICATED **83** (unchanged, owned), ruff GREEN, pytest NOT_RUN (by design of `--legs`), RED_ORPHANED 0.

| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.r3.delta.patch` (ONLY `loremaster/tests/test_engine_rejection_seam.py`) | HEAD + full2 (`e915b90f…`) | `c377c11ecf04697f6098da1780ca8ade` | OK |
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.full3.patch` (full2 + round 3) | HEAD `0b0011b` (also main `e1d36d5`) | `299467bad167496a1e3bbc3c96b8a034` | OK at both |

- **Ordering (§12 STOP 2):** the test side lands FIRST; it reds by name on the four at fix3-as-is, as R3-3 shows. The four production wraps follow.
- **Composition:** the r3 delta is disjoint from `principals.py` / `principal_keys.py`, so it composes with builder-fix4's delta and with the later wrap builder's.

## ROUND 4: am-37 §13 A–D + §13.1 test side (commits `ce2b4bd` + `d6cdd0b`). FINAL
*Measured 2026-09-30 15:13–16:48Z in scratch `fixup4` = HEAD `564983b` + fix5 patch (md5 `5f2d7c43…` verified). `loremaster.__file__` resolves inside `fixup4`. This replaces the PARTIAL section of `04a4149`.*

**SUMMARY:**
- **State:** done.
- **All four classes plus §13.1 are pinned:**
  - **RED on the fix5 base, exactly as declared:** 209 declared from `--collect-only` before the run, all observed red, 0 missed. The only undeclared reds were 34 that are adjudicated to packet 64b-i (below).
  - **GREEN on one combined throwaway reference:** 0 attributable reds.
  - **Mutation proofs:** all 5 held, at least 1 per class.
  - **Gates:** ruff clean; typecheck 83 → 83 (all adjudicated); RED_ORPHANED 0.
- **Deviations:**
  1. **B and D were delegated** to two Opus sub-agents, each in its own scratch copy on the same base. Both hand-backs are transcribed at `…/scratchpad/REPORT-sub-63c13-{b,d}-1.md`, because their Write tool refused report files. I merged their test files, made the §13.1 edits myself, and re-ran every receipt in `fixup4`. None of their scratch-copy runs is the receipt of record.
  2. **Three defects in my own ROUND-4 pins, found by my own receipts and fixed before the final runs:**
     - (a) Round 1's generated sweep gave `--table` a placeholder value. Under C's validator that is refused before the injected fault, so the argv derivation now takes a member of the production-validated domain (`_VALIDATED_OPTION_DOMAINS`).
     - (b) The lifecycle pin counted the engine text, which legitimately appears twice. It now counts the log RECORD.
     - (c) **M-A2 v2 PROOF FAILED:** the pointer pin stayed GREEN with the stderr handler removed, because A(ii)'s `caused by` line alone carried the engine text. It is re-keyed to the log-record line carrying `engine_error` + `error_class`; M-A2 v3 held.
  3. **D's `defined_fields` reads go through an `Any` alias** (the #461 typed reach-around), so the production RED is a test failure rather than an unadjudicated mypy error.
  4. **Two reference defects** (a mis-merged `stamped_count`, and a `map_of` noun that did not name `INFO FOR DB`) surfaced in the v1 reference run and were fixed in the throwaway reference. The v2/v3 receipts are over the fixed reference.
- **Serialization (lead ~15:10Z):**
  - Every pytest and mutation run went through `…/scratchpad/gate.sh::gated_run`: an exclusive `flock` on ONE lock file, held for the whole run.
  - Inside the lock it waits until MemAvailable ≥ 20 GiB AND no other pytest process is alive.
  - Every final run's `ADMITTED` line is in its log (e.g. base 16:11:09 at 28 GiB, reference 16:13:39 at 25 GiB, both with 0 other pytest processes).
  - I stopped the workers' stale queued runners by PID once §13.1 invalidated their test files, and restored `sub-d`'s production with a `cmp` check.
- **Graded:** n/a (author). Base `564983b` + `5f2d7c43`. Full4 also `apply --check`s at main HEAD `51d6acf`.
- **Decisions needed:** none new. Two flags follow.

### Per-class table (receipts: base = `…/scratchpad/baseALL.log` v2 + `baseCLI.log`; reference = `refALL.log` v2 + `refCLI.log`; mutations = `mutB.log`, `mutD.log`, `mA1.log`, `mA2.log` v3, `mC1.log`)
| class | pin | clause | RED at fix5 (declared = observed) | reference | mutation |
|---|---|---|---|---|---|
| A | `test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_cause_of_every_laundered_fault_is_printed[verb × fault]`: 17 verbs derived from the parser × the §11 tuple derived by AST from `_dispatch`'s one tuple-`except`, each fault carrying a typed `__cause__`, injected at `ensure_ready` | §13 A (ii) | 85: no `caused by` line | GREEN | — |
| A | `…::test_the_server_log_pointer_resolves_to_stderr[verb]`: the seam's rejection RECORD, with its `extra` keys derived by AST from `_txn._raise_attempt_failure`, and the seam's own `_domain_rejection_error` | §13 A (i) | 17: no record on stderr | GREEN | **M-A2** (drop `addHandler`): 18 declared, fired EXACTLY (v3) |
| A | `…::test_repeated_invocations_do_not_duplicate_the_log_line` (LIFECYCLE) | §13 A (i) | 1 | GREEN | M-A2 |
| A | `…::TestNoWrapContextOverClaimsItsCause::…[<file>::<fn>::<line>]` ∀ `wrap_store_rejection` call in the package (derived; 16 sites on base, 17 on the reference with the F-5 wrap) | §13 A / F-13 | 3: `principals.py::create`, `::set_subject`, `principal_keys.py::mint` | GREEN | **M-A1** (re-add "already" to `create`): exactly that id |
| C | `test_principals_cli.py::TestHonestLabels`: field renamed; the retired name in NO package source (bare scan); receipt key + stderr sentence `[0,3]`; `--table` help derived ∀ `--table` verb (derived from the parser); invalid `--table` refused with zero store I/O ∀ `--table` verb | §13 C F-4, N-3/F-15 | 8 | GREEN | **M-C1** (`report-unmigrated` skips the validator): exactly `[report-unmigrated]` |
| C | `test_engine_rejection_seam.py::TestEveryWrappedBoundaryDocumentsItsWrapError[<store>::<boundary>]`, over round 3's derived domain | §13 C N-2/F-10 | 4: the §12 four | GREEN | — |
| B | `test_fail_closed_shapes_63c_13b.py` (89 collected):<br>• allowlist walker, now **exactly THREE**: `group_all_count`, `rows_of`, `map_of` (§13.1);<br>• the two INFO readers are PLAIN pins now, not xfail;<br>• every allowlisted helper must itself be derived;<br>• `rows_of` contract;<br>• **`map_of` contract** (non-dict / bad `tables`/`fields` sub-map → raise);<br>• F-6, F-7, F-1, `_as_rows` → fault;<br>• **`delete` on a malformed `INFO FOR DB` answer raises and never runs the cascade** (the fail-OPEN guard, 5 shapes + control);<br>• **B-D2** `authorize_guarded` wrong-shaped pre-read raises (7 shapes);<br>• F-5 (live store) | §13 B + §13.1 items 1–2 | 73 | GREEN | **B mutation** (`rows_of` member-raise → the old silent filter): 14 declared (12 from sub-b + the 2 `authorize_guarded` row shapes), fired EXACTLY |
| D | `test_preboot_schema_precondition_63c_13d.py` (25 collected):<br>• derived legs and SET columns + bare-pattern equality;<br>• ∀ leg × column `REMOVE FIELD` on a minted `:18000` DB → the refusal names exactly that column, in the ruled **one-backtick-span-per-column** form (§13.1 item 3, enforced by `_ONE_SPAN_PER_COLUMN`), with zero writes (3 instruments);<br>• positive control;<br>• `defined_fields`;<br>• **the ONE-DERIVATION pin** (§13.1 item 5): all fields removed → the refused set EQUALS the leg's own SET clause | §13 D + §13.1 items 3/5 | 17 | GREEN | **D mutation** (`if missing:` → `if False:`): 10 declared (7 dirty + 3 one-derivation), fired EXACTLY |

**Base-run diff (v2):**
- 1287 collected (the 20 targeted files below); 243 failed.
- DECLARED_BUT_GREEN = 0.
- UNEXPECTED = 34, all in `test_governed_substrate_64b.py` (packet 64b-i's contract: "UNBUILT: …resource_from_row / classify_zero_row_cas / GovernedInvisible", adjudicated to `packet-64b-i-contract` in the currency).
- The packet-58 lease evidence pin is owned and declared.

**Reference run (v2):** 35 failed, 1249 passed.
- The 35 are the IDENTICAL 34 substrate ids (`cmp` of the sorted id lists) plus the packet-58 lease pin.
- 0 reds are attributable to §13 / §13.1.
- `refCLI.log` after the pointer-pin re-key: 216 passed, 0 failed.

**Targeted set** (awk over the CLI-driving files, the §13 surfaces, and the B/D neighbours; no full suite):
`test_principals_cli`, `test_engine_rejection_seam`, `test_keeps_cli`, `test_keep_remediation_cli_61`, `test_exhaustion_fates`, `test_fixwave_a28c`, `a28`, `a28b`, `a19`, `a19a`, `a19b`, `test_governed_migration_63a`, `test_principal_keys_store`, `test_principal_delete_governed_63a`, `test_principal_delete_cascade_61`, `test_principals_store`, `test_governed_routing_63a`, `test_governed_substrate_64b`, and the two new files.

### STOP-DUAL re-keys (checked; none needed in other files)
- **A:**
  - No exactly-one-line pin exists in the CLI-driving test files.
  - The four `test_keeps_cli.py` `err.startswith("lore-adm:")` pins stayed GREEN on the reference, because they are domain refusals with no seam log line. Not re-keyed.
- **B / §13.1-2:** no test feeds `_as_rows` / `_table_exists` a non-list/non-dict expecting absent/NotFound. The only `governed.run_query` forgery (`test_governed_substrate_64b.py::…test_authorize_guarded_refuses_a_pre_read_row_from_another_table`) forges a well-shaped list, so it is unaffected.
- **C:** the retired name has 0 test-tree hits. It is guarded by the new positive pin instead.
- **D:** the a28c `defined_tables` pin asserts membership; `_RULED_FIELD_SPEC` is untouched and was GREEN on the reference.
- **Own pins re-keyed this round** (my files): round 1's sweep argv (`_VALIDATED_OPTION_DOMAINS`), and the lifecycle and pointer pins (deviation 2).

### Flags
- **F-A (for the builder):** in the reference, the §11 handler prints ` ← caused by:` lines. Under the pointer pin the seam's record line and the cause line both carry the engine text, which is by design. The `≥1 record line` assertion is what isolates §13 A (i).
- **F-D (store law, §13.1 item 4):** the two facts sub-d probed live are recorded in `…/scratchpad/REPORT-sub-63c13-d-1.md` (instrument `…/scratchpad/subd_probe_remove_field.py`). Per §13.1 item 4 the BUILDER lands them in `docs/reference/surrealdb-31-capabilities.md`; outside my writable set.
- The throwaway combined reference (`…/scratchpad/ref-ALL.r4.patch`, md5 `dc1b705aedf86e80073daf675f4dbc85`) is a satisfiability host, never a spec. Its D column set is a hand map, which the one-derivation pin cannot distinguish while the map is correct (that is §13.1 item 5's point). The audit's add-a-column mutation is the receipt that the pin fires.

### Gates and patches (cut 16:48Z, production at base, `cmp`-verified)
- `uv run ruff check .`: All checks passed!
- `--currency --legs typecheck,ruff` (16:48Z): typecheck RED_ADJUDICATED **83** (unchanged), ruff GREEN, pytest NOT_RUN by design of `--legs`, RED_ORPHANED 0.

| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.r4.delta.patch` (tests only: `test_principals_cli.py`, `test_engine_rejection_seam.py`, new `test_fail_closed_shapes_63c_13b.py`, new `test_preboot_schema_precondition_63c_13d.py`) | HEAD `564983b` + fix5 `5f2d7c43` | `ab711142bf1204cfe7395e4038bc9b88` | OK |
| `…/scratchpad/fixup-tests-63c-i-a-2.full4.patch` (fix5 + r4) | HEAD `564983b` (also main `51d6acf`) | `7ab76f3611bedf69eddc4df943cbbc67` | OK at both |

The r4 delta touches no production file, so it composes with the §13 / §13.1 production builder's delta.

### Instruments (surviving)
- The pins themselves are the instruments: the AST derivations of the §11 tuple, the seam `extra` keys, the wrap sites, the `--table` verbs, the allowlist walker, the leg statements and the SET columns. All are committed in the test files.
- `…/scratchpad/red_diff.py` (the declared-vs-observed differ, pasted in §8) and `…/scratchpad/declare_all.py` (the combined declaration predicate) are scratch; the predicate is summarised in the table above.

## ROUND 5: FLAG-1 resolver + the arity probe (lead ~17:25Z; source `REPORT-builder-63c-i-a-fix6.md` §3, `c8c3435`)
*Measured 2026-09-30 17:41–17:47Z in scratch `fixup5` = HEAD `a7e0707` + fix6 full patch (md5 `3132f699…` verified). `loremaster.__file__` resolves inside `fixup5`. Tests only.*

**SUMMARY:**
- **State:** done.
- **FLAG-1 closed:** D's file no longer holds a second resolver. `am34_5` is GREEN, every D pin is GREEN, and D's mutation proof holds on fix6.
- **Arity probe rewritten:** with the `_rows_stamped` `noun=` default REMOVED in a throwaway, typecheck stays at 83, ruff stays GREEN, and B's pins pass 85/85. The builder can drop the default.
- **Deviations:** none.
- **Graded:** n/a (author). Base `a7e0707` + fix6.

| item | edit (test file) | receipt |
|---|---|---|
| FLAG-1 | `test_preboot_schema_precondition_63c_13d.py::_leg_statements` no longer calls `eval(compile(ast.Expression(...)))`. New `_render_statement` reads the statement from its OWN literal parts: str `Constant`, f-string parts, `+` concatenation, and bare module-global `str` Names, looked up in `vars(principals)` and never evaluated. Any other part fails LOUD. | (a) Byte-identical to the old eval for all 3 legs (agent/memory/message): scratch comparer `…/scratchpad/compare_render.py`, whose eval lives outside the tree. (b) `_scanner_candidates` over the whole tree: walkers `{_catch_sites.py::catch_sites_in}`, resolvers `{_catch_sites.py::resolved_by_import}`, i.e. exactly one each. (c) **RED with the fix6-as-is D file swapped back in:** `am34_5` fails naming `test_preboot_schema_precondition_63c_13d.py::_leg_statements` as a second resolver (`r5.am34_5.asis.log`); the r5 file was restored and `cmp`-checked. (d) Targeted run over the D file + `test_retry_seam.py` + the B file + `test_principals_cli.py`: **1004 passed, 0 failed** (`r5.run.log`, admitted 17:43:58Z at 53 GiB, 0 other pytest). (e) **D mutation:** the fix6 anchor is `_schema_predates_refusal`'s `if not missing: return None`, changed to `if True:`. It declared 10 (7 dirty + 3 one-derivation) and **PROOF HELD** (`r5.mutD.log`); production `cmp`-equal to fix6 afterwards. |
| ARITY | `test_fail_closed_shapes_63c_13b.py::_call_rows_stamped` now calls through an `Any`-typed binding (`function: Any = principals._rows_stamped`), so both arity branches type-check against every signature the probe tolerates. The `# type: ignore[call-arg,unused-ignore]` is gone. | `cp -a` throwaway: `def _rows_stamped(update_result: Any, *, noun: str) -> int:` with the default removed. All 3 production callers already pass `noun=` (lines at `fix6`: the memory, agent and message legs). Result: `--currency --legs typecheck,ruff` gives typecheck **RED_ADJUDICATED 83** (unchanged from the 83 with the default), ruff GREEN, and the B file **85 passed** (`r5.nodefault.B.log`). Production restored and `cmp`-equal to fix6. |

- **The lesson, as a question:** *"does the helper I am adding to the test tree walk ASTs, and did I put `test_retry_seam.py` in my targeted set?"*
  - `test_retry_seam.py` owns the tree-wide one-walker/one-resolver property.
  - Its scanner derives candidates by SHAPE across `tests` too (a function naming both `eval` and `Expression` is a resolver).
  - So any AST-walking helper added to the test tree must be run against it. Round 4's targeted set omitted it, so the red went unowned through two rounds.
  - (Receipt for that omission: FLAG-1, found by builder-fix6, not by me.)
- **Also for the builder** (fix6's production comment): `_BACKFILL_UPDATE_NOUN`'s comment says *"the default only labels the raised message"*. When the default is removed, that comment and the constant go with it.

| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.r5.delta.patch` (tests only: `test_preboot_schema_precondition_63c_13d.py`, `test_fail_closed_shapes_63c_13b.py`) | HEAD `a7e0707` + fix6 `3132f699` | `5ef35641295e40cc8e143f647fe2784e` | OK |

**Gates:** `uv run ruff check .` All checks passed. Currency (typecheck, ruff) is 83 / GREEN, RED_ORPHANED 0. Every run was serialized through `gate.sh::gated_run`.

## ROUND 6: am-37 §13.3 test side (commit `07549f7`; the FINAL capped round)
*Measured 2026-10-01 00:40–02:05Z in scratch `fixup6` = HEAD `e56a3d8` + fix6 final (patch md5 `bec29190…` verified). `loremaster.__file__` resolves inside `fixup6`. The throwaway reference `refR6` was made with `scratch_copy.sh` (never a `cp -a` of a synced tree; provenance resolves inside `refR6`).*

**SUMMARY:**
- **State:** done.
- **RED at bec29190:** 131 declared before the run from `--collect-only` plus a static reading; all 131 red, 0 missed.
  - The only undeclared reds are 28 `test_mcp_server.py` findings tests (`AppContext.findings() … 'capability'`, packet 64b-i, adjudicated to `packet-64b-i-contract`).
- **Reference:** GREEN except those SAME 28 ids (`cmp`-identical id lists).
- **Mutations:** all 9 held, at least 1 per new pin class; F-1 is exempt beyond mutation E (§13.3 item 1 (c)).
- **Gates:** ruff clean; typecheck 83 → 83 (owned); RED_ORPHANED 0.
- **Deviations:**
  - (1) The admission gate's process check was narrowed to LORE pytest processes (`gate.sh` v2; v1 kept as `gate.v1.sh`). A foreign project's long-lived pytest (`mobile-pricepaper-smoke`) held the v1 "any pytest" check closed for 50 minutes, while MemAvailable was 42 GiB. CLAUDE.md's rule is ONE **lore** pytest session; the ≥ 20 GiB memory gate is unchanged. Every admission line is in its log.
  - (2) STOP-DUAL re-keys in `test_secret_leak_vectors.py` and `_logging_fixtures.py` (below).
  - (3) Two derivation reach gaps in my own first draft were caught by the first reference run and fixed (below).
- **Decisions needed:** none. The two readings below are flagged for the builder or audit.

### Per-item table (file: NEW `loremaster/tests/test_am37_13_3_63c_i_a.py`, 108 collected at base)
| item | pin(s) | declared RED at bec29190 (= observed) | reference | mutation (on `refR6`, `scripts/mutation_proof.py`, all PROOF HELD) |
|---|---|---|---|---|
| 1 F-1 | `TestTheSetParserIsCompleteOrRaises`. The corpus: blind-5's cases + RETURN-in-a-call, SET-in-a-string, an unbalanced `)` in a string, `+=`, quoted and double-quoted commas/WHERE, and all four end keywords. Each must give the EXACT set OR raise; a subset fails. Must-raise cases: open paren, open quote, trailing item without `=`, no SET. The shipped three parse exactly. | 7: subquery-WHERE, RETURN-in-a-call, SET-in-a-string, unbalanced-paren, `+=`; open-paren and open-quote return a prefix instead of raising | GREEN | exempt (§13.3 item 1 (c): §13.1's one-derivation pin + mutation E) |
| 2 F-2 | `TestTheCliSinkIsRedacted`: the CLI handler carries `RedactingFilter`; `scrub_text` is public and is the filter's own call; a 128-hex run is redacted; CONTROL ×4 (64-hex, 127-hex, 16-hex, a ULID) untouched; `_fault_line` scrubs the error and every cause; the end-to-end stderr record is scrubbed | 9 | GREEN | **F2-sink** (drop `addFilter`): 2 ids · **F2-hash** (drop the 128-hex sub): 3 ids |
| 3 #527 | `TestTheCauseWalkTerminates`: the 2-cycle cell runs in a CHILD process with a 512 MiB address-space cap and a timeout (the unbounded base walk must not grow inside a pytest worker); CONTROL: plain chain unchanged; CONTROL: `__context__` never walked | 1 | GREEN | **527** (drop the `seen` guard): 1 id |
| 4 #528 | `TestTheReportCountValidatesItsOwnTable`: a direct call with an invalid table raises and the `run_query` spy records zero calls | 1 | GREEN | **528** (validator → `if False`): 1 id |
| 5 F-3 | `TestEveryPostWriteShapeReadSaysItLanded`, GENERATED. ∀ store reached by `_dispatch` ∀ derived write boundary (round 3's §12 derivation) whose shape read takes a write result (a bound name OR an inline write-sink call), + `principals::_rows_stamped`: `landed=True`. Plus non-vacuity, the ONE template byte-exact ×3, and a CONTROL (an unlanded read keeps its text). | 7 boundary ids + 3 template ids | GREEN | **F3** (drop `landed=True` on `set_status`): exactly `[principal::set_status]` |
| 6 F-5 | `TestTheReportRemedyIsDerived` ∀ table the report validator accepts | 1: `[brief]` | GREEN | **F5** (remedy always names migrate): exactly `[brief]` |
| 7 F-6 | `TestEveryShapeReadNamesItsRead`, GENERATED over call sites: `rows_of` / `map_of` / `group_all_count` everywhere, `_as_rows` inside an owning class, and `<OwnerClass>._as_rows(...)` anywhere (owner = a class whose `_as_rows` delegates to `rows_of`, derived). Plus: the wrappers require `noun` (keyword-only, no default). | 19: 12 principals/principal_keys sites + 6 `keeps.py` `PrincipalStore._as_rows` sites + the wrapper pin | GREEN | **F6** (restore `_as_rows`' default noun): exactly the wrapper pin |
| 8 F-7 | `TestGovernedStatementErrorTracebacks`: the class exists (`RuntimeError`, not `ValueError`) and is NOT in the AST-derived §11 tuple; the REAL parser's raise on an unreadable literal reaches `main()` as a traceback; CONTROL: a `ValueError` still launders to exit 1 | 2 | GREEN | **F7** (add it to the tuple): exactly those 2 |
| 9 #31 | `TestTheNotSupportedProseIsDerived`: the invalid-name refusal lists exactly `_MIGRATE_VALID_TABLES`; the brief refusal's "today:" list equals the derived migrate legs | 0 (GREEN at base, hand-correct today) | GREEN | **31** (drop `message` from the brief prose): exactly that pin, which proves it discriminates |

### STOP-DUALs re-keyed (test side, this commit)
- **`test_secret_leak_vectors.py`:** 41 bare `_scrub_text` → `scrub_text`. That covers the import, the monkeypatch-by-name routing pin, the kept-names list and A19's body pin.
  - The public seam is resolved PER CALL through a module-level `scrub_text()` resolver (`vars(logging_setup).get("scrub_text")`), never a static import. On bec29190 the file therefore still collects, and each of its 28 `scrub_text`-touching test functions reds on its own for the right reason. The 131 declared include those reds; the AST-derived list is in `…/scratchpad/r6.declared2.txt`.
  - This also keeps mypy free of an unadjudicated `attr-defined` red, the round-5 lesson's sibling.
- **`_logging_fixtures.py`:** 2 prose mentions renamed.
- **`test_secret_typing.py`:** needed no edit. Its two scanner pins red on the reference ONLY via the import, so the rename fixed them.

### Reach gaps in my own draft, caught by the first reference run (v1) and fixed before the receipts of record
- **F-6:** the first draft scanned only modules defining a delegating `_as_rows`. It MISSED `keeps.py`'s six `PrincipalStore._as_rows(...)` calls; the reference's required noun turned them into 40 runtime `TypeError`s. The derivation now includes `<OwnerClass>._as_rows` receivers.
- **F-3:** the first draft followed only write results bound to a NAME. It now also takes a shape read whose argument contains a write-sink call inline.
  - **Fact for the record:** §13.3 item 5 says *"KeepStore's six `_as_rows` post-write sites"*. The derivation shows those six (`_read_membership`, `get_by_key`, `get_keep`, `list_household`, `list_keeps_for_keeper`, `list_keeps_for_member`) are `SELECT` reads, not post-write reads. So they are in F-6's domain (noun) and NOT in F-3's (landed). "By derivation, not by list" decided it.

### Readings (two-reading triggers, flagged)
- **F-5:**
  - §13.3 item 6 writes the rule as membership of `_MIGRATE_VALID_TABLES`. That set contains `brief`, which `migrate-governed` REFUSES ("does not yet migrate `brief`"), so the literal reading still sends a `brief` operator to a refusing verb.
  - The pin follows the property sentence ("names a table the MIGRATE verb accepts"), with "accepts" = has a derived migrate LEG (`test_preboot…::_LEGS`). `[brief]` reds on base under that reading.
  - My reference used a hand `_MIGRATED_TABLES` (a SAT host only). The builder should derive it.
- **F-2:** the reference's 128-hex pattern is bounded by non-hex on both sides. The CONTROL cells (64- and 127-hex untouched) pin that it does not over-redact git or sha256 hashes. The builder owes the §13.3 item 2 `sha512` producer sweep.

### Runs (every one through `gate.sh::gated_run`: one flock, ≥ 20 GiB, no other LORE pytest, a 16G cgroup, `-n 8`)
- **Targeted set** (`…/scratchpad/r6.files`): the new file, `test_retry_seam.py` (the round-5 lesson), the `logging_setup` covering tests found by an awk scan (`test_caplog_isolation`, `test_logging_setup`, `test_mcp_server`, `test_secret_leak_vectors`, `test_secret_resolution_seam`, `test_secret_typing`), `test_principals_cli`, the D and B files, and `test_engine_rejection_seam`. 2273 collected.
- **Base (v2):** 159 failed (131 declared + 28 owned 64b-i), 2112 passed; DECLARED_BUT_GREEN 0. Admitted 01:50:36Z at 39 GiB.
- **Reference (v2):** 28 failed (the identical 64b-i ids), 2243 passed. Admitted 01:56:12Z at 42 GiB.
- **Mutation logs:** `…/scratchpad/r6mut/*.log`, each "PROOF HELD — the declared RED set fired EXACTLY", tree restored byte-exact.

### Gates and patches
- `uv run ruff check .`: All checks passed.
- `--currency --legs typecheck,ruff`: typecheck RED_ADJUDICATED **83** (unchanged), ruff GREEN, RED_ORPHANED 0.

| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.r6.delta.patch` (tests only: new `test_am37_13_3_63c_i_a.py`, `test_secret_leak_vectors.py`, `_logging_fixtures.py`) | HEAD `e56a3d8` + fix6 `bec29190` | `2aff7c3a46be9bd92ab3c42868cb47ee` | OK |
| `…/scratchpad/fixup-tests-63c-i-a-2.full6.patch` (fix6 + r6) | HEAD `e56a3d8` (also main `64d308a`) | `ca4598259d2727b95c6dff877edc27ad` | OK at both |

The throwaway reference, for the record only (never shipped; a SAT host, never a spec): `…/scratchpad/ref-R6.patch` (vs HEAD, md5 `5a5d7358…`); generators `r6_make_ref.py` + `r6_callsites.py`.
