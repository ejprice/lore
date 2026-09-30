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

## ROUND 4: am-37 §13 A–D test side (commit `ce2b4bd`). ⚠ PARTIAL, state: waiting:memory-admission
*Written 2026-09-30 ~15:15Z. Scratch `fixup4` = HEAD `564983b` + fix5 patch (md5 `5f2d7c43…` verified); `loremaster.__file__` resolves inside `fixup4`. Receipts are PENDING on the host memory gate. The lead extended the deadline (~15:15Z) and asked for this partial commit so the authored work is durable.*

**SUMMARY:**
- **State:** waiting:memory-admission. All four classes' pins are written. ruff and mypy are clean on every touched file. The patches are cut. RED/GREEN/mutation receipts are PENDING.
- **Deviations:**
  - (1) Classes B and D were delegated to two Opus sub-agents, each in its own scratch copy (`sub-b`, `sub-d`) on the same base. I merged their new test files. Their hand-back reports are transcribed at `…/scratchpad/REPORT-sub-63c13-d-1.md`, and B's is summarised below; their Write tool refused report files.
  - (2) I changed D's test to read `defined_fields` through an `Any` alias (the #461 typed reach-around). This avoids 4 unadjudicated mypy errors; the production RED stays a test failure.
- **Serialization (lead requirement ~15:10Z):**
  - One shared admission helper, `…/scratchpad/gate.sh::gated_run`: an exclusive `flock` on ONE lock file, held for the whole run. Inside the lock it waits until MemAvailable ≥ 20 GiB AND no other pytest process is alive (a process-table check that holds even for a runner that never took the lock).
  - Every pytest and mutation run goes through it: mine, and both workers' (they were told at ~15:10Z and both confirmed adopting it).
  - Observed: my base run was admitted at 15:13:13Z (avail 20 GiB, others 0) and held the lock, while sub-d's runner waited on `flock` (`lsof` shows one holder).
  - ⚠ Sub-b's hand-back says it killed a flock PID (3797612) it believed was its own waiter. Serialization held regardless (the process-table check plus the single live holder above). Named for the record.
- **Decisions needed** (from the workers; details below): **B-D1** (operator), **B-D2** (implementation requirement), **D-fork** (a backtick reading).

### Per-class pins (all RED/GREEN columns are DECLARED; runs pending)
| class | pin (file::class) | §13 clause | declared RED at fix5, and why | reference | mutation (prepared) |
|---|---|---|---|---|---|
| A | `test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_cause_of_every_laundered_fault_is_printed[verb × fault]`: 17 derived verbs × the §11 tuple (5, derived from `_dispatch`'s one tuple-`except` by AST), each fault with a typed `__cause__` injected at `ensure_ready` | A (ii) | ×85: the handler prints `{error}` only, with no `caused by` line | expected GREEN (ref-AC) | — |
| A | `…::test_the_server_log_pointer_resolves_to_stderr[verb]`: the seam's rejection record, whose `extra` keys are derived by AST from `_txn._raise_attempt_failure`, plus the seam's own `_domain_rejection_error` | A (i) | ×17: no handler renders `engine_error` onto stderr | expected GREEN | M-A2: drop `addHandler` → the 17 + the lifecycle pin |
| A | `…::test_repeated_invocations_do_not_duplicate_the_log_line` (LIFECYCLE: two `main()` calls, the engine line exactly once each, no "Logging error") | A (i) | ×1 | expected GREEN | M-A2 |
| A | `test_principals_cli.py::TestNoWrapContextOverClaimsItsCause::test_the_wrap_context_names_the_operation_not_a_guessed_cause[<file>::<fn>::<line>]`, over every `wrap_store_rejection` call in the package (16 sites) | A / F-13 | ×3: `principals.py::create`, `::set_subject`, `principal_keys.py::mint` | expected GREEN | M-A1: re-add "already" to `create` → exactly that id |
| C | `test_principals_cli.py::TestHonestLabels`: field renamed (dataclass fields); the retired name in NO package source (bare scan); receipt key + stderr sentence `[0,3]`; `--table` help derived from `_MIGRATE_VALID_TABLES` ∀ `--table` verb (derived from the parser); invalid `--table` refused with ZERO store I/O ∀ `--table` verb (spy); non-vacuity | C (F-4, N-3/F-15) | ×8 | expected GREEN | M-C1: `report-unmigrated` skips the validator → exactly `[report-unmigrated]` |
| C | `test_engine_rejection_seam.py::TestEveryWrappedBoundaryDocumentsItsWrapError[<store>::<boundary>]`, over round 3's derived domain | C (N-2/F-10) | ×4: `principal::{set_status,set_expires,delete}`, `principal_key::revoke` | expected GREEN | — |
| B | `test_fail_closed_shapes_63c_13b.py` (66 collected; by sub-b): the allowlist walker over `principals.py`/`governed.py` shape-testers; the `rows_of` contract; F-6 `_rows_stamped`; F-7 `_governed_select`; F-1 `delete.cascaded`; `_as_rows` non-list → fault ×3 setters + delete; F-5 leftover-read wrap (the one live-store pin) | B | 48 declared (`…/scratchpad/subb.declared_red.txt`) | expected GREEN on `sub-b.reference.patch` | 12-id mutation (`subb.mut.declared.txt`) |
| D | `test_preboot_schema_precondition_63c_13d.py` (22 collected; by sub-d): the leg domain derived via `governed_exempt(statement=…)`; columns parsed from each leg's own SET clause and diffed against a bare-pattern read; ∀ leg × column `REMOVE FIELD` on a minted `:18000` DB → the refusal names exactly that column with zero writes (3 instruments); positive control; `defined_fields` rides the preconditions | D | 14 declared (`…/scratchpad/subd-declared-red.txt`) | expected GREEN on `sub-d.reference.patch` | 7-id mutation (`if missing:` → `if False:`) |

### STOP-DUAL re-keys (each checked)
- **A:**
  - The bare awk over the four CLI-driving test files (`test_principals_cli`, `test_keeps_cli`, `test_keep_remediation_cli_61`, `test_comms_cli`) finds NO exactly-one-line pin.
  - Four `err.startswith("lore-adm:")` pins in `test_keeps_cli.py` (`test_remove_household_refuses_to_remove_the_keeper`, `test_create_keep_without_name_is_rejected_for_name_requiring_types`, `test_create_keep_dm_with_a_name_is_rejected`, `test_create_keep_with_an_unknown_keeper_is_loud_and_nonzero`) are domain refusals with no seam log line, so they are predicted to survive. The reference run (pending) decides; any that reddens is re-keyed to `in` in this commit.
- **B:** none found (sub-b's awk over `_rows_stamped`/`_as_rows`/`_governed_select`/`TypeError`).
- **C:** a bare-pattern sweep of the retired name `unsound_sender_messages` over `loremaster/tests/**` (and scripts, skills) found ZERO hits. Nothing re-keyed; instead the new positive pin (`test_the_retired_name_survives_in_no_served_source`) guards the package. The remaining hits at `ce2b4bd` are production-only (`principals.py` ×14, `governed.py` ×2) plus am-37's own history (×6, which §13 C keeps).
- **D:** none needed. The a28c `test_am34_4_the_preconditions_carry_the_defined_table_set` asserts membership, not the exact field set. `_RULED_FIELD_SPEC` is untouched.

### Decisions surfaced by the workers (verbatim in substance)
- **B-D1, operator ruling:**
  - `PrincipalStore._table_exists` does `info.get("tables", {}) if isinstance(info, dict) else {}`, so a non-dict `INFO FOR DB` answer reads as "table absent". `delete` then SKIPS the SF-63-5 owned-row guard, which fails OPEN.
  - `_agent_migration_preconditions` is a third, correct but cloned, shape policy.
  - Both sit outside the ruled two-helper allowlist. Sub-b holds them as `xfail(strict=True)` pending a ruling.
  - Options: (a) a third ruled helper for INFO maps, widening the allowlist to three (sub-b recommends this), or (b) re-scope the pin and ledger `_table_exists` as a defect.
- **B-D2, implementation requirement:** `governed.authorize_guarded` coerces a wrong-shaped pre-read to "row absent" (`[]` / `{}`), so the allowlist pin reds it by name. The reference routes it through `rows_of`. §13 B does not list it.
- **D-fork:** the refusal text `<c1>, <c2>` can mean one backtick span around the list or one span per column. The pins accept both, and sub-d would pick one span per column.
- **D store facts (probed on `:18000`, not yet in `docs/reference/`):**
  - `INFO FOR TABLE` on an UNDEFINED table returns empty maps, not an error. The field read must stay behind the `INFO FOR DB` gate.
  - An UPDATE of a removed field on a SCHEMAFULL table is silent over 0 rows and raises over ≥1 row.
- **D flag:** its reference uses a hand column map (satisfiability only). The builder must derive the columns from the statement. A "refusal follows a mutated SET clause" pin was NOT TRIED.

### Gates and patches (cut 15:14Z, production at base, `cmp`-verified)
- `uv run ruff check .`: All checks passed!
- `--currency --legs typecheck,ruff` (15:14:49–15:15:08Z, production at base throughout): typecheck RED_ADJUDICATED **83** (unchanged, so the new tests add 0 mypy errors), ruff GREEN, pytest NOT_RUN by design of `--legs`, RED_ORPHANED 0.

| patch | base | md5 | `git apply --check` |
|---|---|---|---|
| `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/39327f47-9890-466d-ba82-57c754558a73/scratchpad/fixup-tests-63c-i-a-2.r4.delta.patch` (tests only: `test_principals_cli.py`, `test_engine_rejection_seam.py`, new `test_fail_closed_shapes_63c_13b.py`, new `test_preboot_schema_precondition_63c_13d.py`) | HEAD `564983b` + fix5 `5f2d7c43` | `346e746d6fbb3bdd1ca105a47036d59e` | OK |
| `…/scratchpad/fixup-tests-63c-i-a-2.full4.patch` (fix5 + r4) | HEAD `564983b` | `ff70ecb2e9ef38fb934f22a310bfb11d` | OK |

The reference patches (throwaway, never shipped) are `…/scratchpad/ref-AC.patch` (`b22ef5cb…`), `sub-b.reference.patch` (`ff5b5258…`) and `sub-d.reference.patch` (`d418c9a5…`).

### PENDING (armed behind the gate, serialized)
1. A+C: the base run over 14 targeted files (admitted 15:13:13Z), then the ref-AC run over the same 14, then the mutations M-A1, M-A2, M-C1.
2. B: the RED run on `sub-b`, then its chain (reference GREEN, 12-id mutation, restore + `cmp`).
3. D: `subd_runner.sh` (base run, reference run, 7-id mutation, restore + `cmp`).
The receipts land in this section when they complete; any change to a test re-cuts the patches.
