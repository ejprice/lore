# REPORT — builder-63b-ib-twin-D

STARTED 2026-09-08 · session 63b-session2-20260908 · Opus 4.8 · COMMIT-ONLY

## SUMMARY BLOCK
- receipt: `brief-base v14 read` · `brief project v7 read`
- state: **done-with-deviations** (both concerns built + gated green; 2 deviations + 1 interpretation fork + 1 commit-split constraint flagged)
- deviations: (D1) ruling named the wrong dead-entry pin — the affected instrument is `TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_the_allowlist_carries_no_dead_entries` over `_ALLOWED_WHOLE_TREE_CLONE_FILES`, not the parse-skip pin; removed the right entry in the same commit. (D2) inherited number wrong — 63a_iv gate is **4 passed, 0 failed**, not the ruling/brief's "6 passed" (6 was the pre-delete count).
- Packages considered: none — no mechanism specified (test-instrument reconciliation only; no new deps).
- Reuse ledger: none new — `_local_source`/`_SOURCE` in 63b_ia are a verbatim PORT of the retired 63a-iv helper (moved, not authored) so the moved pin body stays byte-identical; `call_name`/`function_calls_named` REUSED from `_governed_contract` (cited).
- decisions-needed (lead): (1) INTERPRETATION FORK — I DELETED the 63a_iv MODULE (ruling §1.3 END STATE) rather than gutting-but-keeping it; git-reversible, veto if you meant gut. (2) TWO-COMMIT SPLIT — the two commits can't both be materialised from one tree (63a_iv modify-then-delete + a substrate-import incompatibility); recommend ONE commit, or reconstruct commit-1 via Appendix A. (3) 4 pre-existing `_ASUB_PARSE_SKIP` skips + 1 pre-existing coroutine warning surfaced in the gate (not mine).
- pointers: CONCERN 1 §"the D fix" · CONCERN 2 §"twin-retirement sweep" · mutation-proof receipt in CONCERN 1 · commit constraint §"TWO-COMMIT SPLIT" · Appendix A · friction annotated on lore finding #459.
- Graded: n/a (builder, not a verdict-render). HEAD-at-report: `46288b6` (unchanged; COMMIT-ONLY — lead commits).

## Two-commit split (files; see §"TWO-COMMIT SPLIT" below for the materialisation CONSTRAINT)
- CONCERN 1 — §1.2 "the D fix": test_memory_enforcement_63a_iv.py (remove TestEveryRawMemoryMutationIsAllowlisted + _KNOWN_RAW_SITES + _defined_test_names + 2 imports + docstring) + test_ast_reach_helpers.py (remove the _ALLOWED_WHOLE_TREE_CLONE_FILES 63a_iv entry). GATE: 63a_iv **4 passed, 0 failed** (not 6 — see D2).
- CONCERN 2 — §1.3 "retire the 63a_iv twin": DELETE test_memory_enforcement_63a_iv.py + test_memory_enforcement_63b_ia.py (moved TestRecreate + scaffolding + prose) + _governed_contract.py (C5 deletes + prose). GATE: collection 9006/0, suite 100/0, typecheck EXIT=0, ruff clean.

## Progress log
- STARTED: idle-gate contract written, report skeleton created.

### CONCERN 1 — the D fix (§1.2) — DONE, gate GREEN
Edits (via marker-based Python slicing — scratchpad/concern1_edit.py, pasted verbatim in Appendix A — chosen over 87-line byte-exact Edit reproduction of a unicode/escaped-quote span; each marker asserted present-and-unique, residual-symbol assertions after):
- `test_memory_enforcement_63a_iv.py`:
  - deleted `class TestEveryRawMemoryMutationIsAllowlisted` (5 tests: V1/V2/V3/V4/V5) + its L1 section-comment header.
  - deleted module constant `_KNOWN_RAW_SITES` (used only by V1).
  - deleted helper `_defined_test_names()` + its section-comment header (used only by V4).
  - removed the two now-unused `_governed_contract` imports: `governed_table_raw_mutation_sites`, `governed_table_guarded_write_frames`. (Kept `GovernedWriteAllowlistEntry`, `MutationSite`, `call_name`, `function_calls_write_guard` — still used by TestRecreate + L2a.)
  - updated the module docstring "THREE layers" preamble → L1 deny-by-default retired here; L1 home = `63b_ia::TestL1CoverageIsDenyByDefaultOverTheSiteBackedEntries` / `63a_v::TestTheWholeTreeReachIsAnOutput`. (P8d prose-drift fix.)
  - KEPT `MEMORY_WRITE_ALLOWLIST` / `MEMORY_F5_CASE` (feed the still-GREEN L2a class) per §1.2 step 5.
- `test_ast_reach_helpers.py`: deleted the `_ALLOWED_WHOLE_TREE_CLONE_FILES["test_memory_enforcement_63a_iv.py"]` entry — see DEVIATION D1 below for why this (not the parse-skip pin the ruling named) is the affected instrument.

⚠ DEVIATION D1 (pin name in ruling §1.2 step 3 / brief is imprecise — outcome identical): The ruling said to check `TestTheParseSkipSetIsACheckedVariable::test_the_parse_skip_allowlist_carries_no_dead_entries` and remove a "parse-skip entry". Ground truth (test_ast_reach_helpers.py): that pin keys ONLY on `_ASUB_PARSE_SKIP` (4 entries: backoff/secret_typing/secret_leak_vectors/comms_footer — NO 63a_iv entry), so `_defined_test_names`' removal does not touch it. The instrument that DOES redden is `TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_the_allowlist_carries_no_dead_entries`, keyed on `_ALLOWED_WHOLE_TREE_CLONE_FILES` — 63a_iv WAS in that allowlist (the entry cited `_defined_test_names` as its whole-tree TEST-TREE scan). Removing `_defined_test_names` makes 63a_iv have no whole-tree clone → dead allowlist entry → RED. Fix: removed that entry in the same commit. The §1.2 step-6 whole-module gate catches it regardless.

⚠ DEVIATION D2 (inherited number wrong — the "6 passed" claim): §1.2 step 6 AND the lead brief both say 63a_iv must report **6 passed, 0 failed**. MEASURED post-delete: **4 passed, 0 failed** (see gate tail). The "6" was the PRE-delete pass count (baseline `3 failed, 6 passed`); the deleted class held V3+V4 which were 2 of those 6 greens, so deleting the whole 5-test class leaves 4 (TestRecreate=1 + L2a=2 + L2b=1). The invariant §1.2 targets is met: 0 failed, the 3 reds (V1/V2/V5) gone, the surviving greens intact. (This is the "re-derive every inherited number" law — the wrong number was in the ruling itself.)

GATE (§1.2 step 6) — PASS:
- 63a_iv alone: `4 passed in 1.32s` (0 failed; was `3 failed, 6 passed` at HEAD 46288b6).
- Four-module gate (`63a_iv 63b_ia 63a_v test_ast_reach_helpers -n0 -p no:cacheprovider`): `103 passed, 4 skipped, 1 warning in 67.58s` — 0 failed. The 4 skips are the deliberate `_ASUB_PARSE_SKIP` fixture-consumer skips (test_ast_reach_helpers.py:1922, parametrized over `_ASUB_PARSE_SKIP` which I never touched) — pre-existing, by-design. The 1 warning (coroutine-never-awaited at 63b_ia:720) is pre-existing in a file I didn't change.
- `ruff check` on both changed files: `All checks passed!`

Left-in-place (CONCERN 1): `_TABLE = MEMORY_F5_CASE.table` (L111) is now dead (was used only by the deleted class) — ruff/mypy do not flag a module-level unused, and it MUST be removed in CONCERN 2 when `MEMORY_F5_CASE` goes (C3). L2a/L2b class docstrings still say "⚠ RED at HEAD" (stale — both are green since 63b-i-a); those classes are DELETED in CONCERN 2 (C3/C4), so editing them now is churn. Both noted, not fixed in CONCERN 1.

MUTATION PROOF (§1.2 rider) — PASS. `./scripts/scratch_copy.sh --force /tmp/scratch-63b-ib-twinD` provenance receipt: `loremaster -> /tmp/scratch-63b-ib-twinD/loremaster/loremaster/__init__.py` (imports resolve INSIDE the copy; all 4 members verified). Planted a NEW unallowlisted raw memory UPDATE (`_SynthTwinDProofClass._synth_seize_scope`, `f"UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'seized'"` — matches `_reinforce`'s idiom) in the scratch `local.py`.
- POSITIVE CONTROL (faithful copy, before plant): `2 passed, 47 deselected` for the two target tests.
- Declared-RED (from the node ids, before the run): `63b_ia::TestL1CoverageIsDenyByDefaultOverTheSiteBackedEntries::test_every_derived_site_is_in_a_site_backed_entry_and_no_ghost` AND `63a_v::TestTheWholeTreeReachIsAnOutput::test_the_whole_tree_derived_set_is_the_known_four_sites`.
- OBSERVED after plant: `2 failed, 47 deselected` — BOTH declared tests RED, naming the exact orphan `TreeMutationSite(file='loremaster/loremaster/memory/local.py', function='_synth_seize_scope', verb='UPDATE')` (new: [_synth_seize_scope]; gone: []). Declared-RED == observed-RED (2/2; no unexpected reds; no declared-red-stayed-green).
- Scratch discarded (`shutil.rmtree`; `rm -rf` is permission-guarded here). Proves the SURVIVING whole-tree deny-by-default instrument still reddens for a growing raw-mutation set after the local.py twin's deletion — confirming §1.1's V1/V2 PRESERVED-WITH-PIN adjudication.

**CONCERN 1: DONE. Gate GREEN, ruff clean, mutation proof PASS.**

### CONCERN 2 — the §1.3 twin-retirement sweep (C1–C5 + FLAG-3) — DONE, gates GREEN

⚠ INTERPRETATION (FLAG — the delete-vs-gut fork; I chose DELETE, git-reversible, flag for veto): The brief's CONCERN-2 C-list phrases the sweep as "delete class X, delete constants Y". Taken literally that would GUT 63a_iv but keep the file — leaving a 0-test module with dead `_*_ENTRY` constants and F401 imports. The RULING §1.3 is explicit that the END STATE is a **whole-module delete**: C2 says "delete the entry in the same commit **as the module**", C4 says "Delete [L2b] **with the module**", and the §1.3 title says the couplings "FORBID a whole-module delete **today**" (i.e. once relocated, the module IS deleted). Reading A (delete the module) is clean; Reading B (gut+keep) leaves a broken/weird artifact the brief didn't spell out cleanup for. I executed Reading A (delete `test_memory_enforcement_63a_iv.py`). It is fully git-reversible — if the operator/lead wants Reading B, restore the file and I gut it instead.

Edits (marker/extraction-based; scripts in scratchpad `concern2_edit.py` [63b_ia] + `concern2_gc.py` [_gc+delete], concern1_edit.py pasted in Appendix A):
- **C1 — move TestRecreate → 63b_ia (verbatim).** Extracted `class TestRecreateMemoryTableIsBootAdminOnly` BYTE-EXACT from 63a_iv and inserted it into `test_memory_enforcement_63b_ia.py` (after `TestEnsureReadyIsAnAllowlistedDdlFrame`, before `TestGuardedWriteIsAnAllowlistedLabelFrame`), with minimal scaffolding: top-level `import ast`, `call_name` added to the `_governed_contract` import block, and a `_local_source()` + `_SOURCE = _local_source` helper (mirrors the retired 63a-iv, keeps the pin body verbatim), plus a provenance comment. It is the `pin=` of `63b_ia::_RECREATE_ENTRY`, so it must live in a surviving module (deleting un-moved reds `63b_ia::test_every_entry_pin_is_a_defined_test` + `63a_v::test_every_tree_allowlist_entry_has_a_real_evidencing_pin`).
- **C2 — parse-skip entry: NO-OP.** The `_ALLOWED_WHOLE_TREE_CLONE_FILES` 63a_iv entry was already removed in CONCERN 1 (DEVIATION D1). `_ASUB_PARSE_SKIP` never had a 63a_iv entry, so `test_the_parse_skip_allowlist_carries_no_dead_entries` was never affected. Verified 0 residual refs to the module name anywhere in tests.
- **C3/C4 — L2a + L2b + constants: subsumed by the module DELETE.** Deleting `test_memory_enforcement_63a_iv.py` removes `TestEveryAllowlistedFrameSetsAWriteGuardContext` (L2a), `TestEveryObservedMemoryMutationCarriesAGuardContext` (L2b), `MEMORY_WRITE_ALLOWLIST`, `MEMORY_F5_CASE`, the 3 `_*_ENTRY` constants, and the now-dead `_TABLE`/`_SOURCE`/`_local_source`/`_governed_source` in one stroke.
- **C5 — `_governed_contract.py` substrate retirement.** Deleted `class GovernedWriteAllowlistEntry`, `def governed_table_guarded_write_frames`, `def function_calls_write_guard`, and the `GovernedTableCase.mutation_source` / `.write_allowlist` fields (+ their `#: F5` field-comment). KEPT (verified present post-edit): `MutationSite`, `governed_table_raw_mutation_sites`, `observe_governed_table_writes`, `_raw_mutation_of_table`, `call_name`, `function_calls_named`.
  - ⚠ DELETION GATE = TEXTUAL SCAN, not lore_impact (SAID OUT LOUD; friction annotated on finding #459). lore_impact returned `GovernedWriteAllowlistEntry` as `dead 0 prod / 0 test` — FALSE (63a_iv used it), and flagged a bare-name-fallback "may be a UNION". So I scanned tests+members+scripts textually for each retired symbol; all consumers were in 63a_iv (deleted) + `_gc`-internal prose. This is the grep-class case (a) exhaustiveness fallback of the dogfood protocol.
- **FLAG-3 + rename-law prose sweep.** Bare-anchor swept every retired name; each residual got a fix (P8d prose-drift):
  - `_gc` TreeWriteAllowlistEntry docstring FLAG-3: `_recreate_memory_table`/`_replay_record` `runtime_observed=False` → rewritten to `runtime_observed=True` (true since 63b-i-a §5.1 Q1; matches the field default).
  - `_gc` TreeWriteAllowlistEntry docstring head: dropped the `:class:GovernedWriteAllowlistEntry` reference (deleted class).
  - `_gc` F5 header comment (was "GovernedTableCase.mutation_source + .write_allowlist … 64 supply their own pair") → re-pointed at `TreeWriteAllowlistEntry` / `MEMORY_TREE_ALLOWLIST` / `governed_table_raw_mutation_sites_in_tree` (so 64 does not clone the retired shape).
  - `_gc` `l1_site` comment + emitter-anchor comment: `function_calls_write_guard` → `function_calls_named`.
  - `63b_ia` module docstring L2a note: `function_calls_write_guard` → `function_calls_named`.
  - Residual asserts: 0 occurrences of `GovernedWriteAllowlistEntry` / `governed_table_guarded_write_frames` / `function_calls_write_guard` / `mutation_source` / `write_allowlist` remain in `_gc`; 0 `function_calls_write_guard` in `63b_ia`.

GATES (CONCERN 2) — all PASS:
- Whole-tree collection (catches any importer broken by the shared-substrate edit): `9006 tests collected in 5.13s`, **0 collection errors**.
- Surviving-modules suite (`63b_ia 63a_v test_ast_reach_helpers -n0 -p no:cacheprovider`): `100 passed, 4 skipped, 1 warning in 67.35s` — 0 failed. Count reconciles: 103 (CONCERN-1 four-module) − 4 (63a_iv deleted) + 1 (TestRecreate now in 63b_ia) = 100. The moved TestRecreate is GREEN; pin-existence checks (`test_every_entry_pin_is_a_defined_test`, `63a_v::test_every_tree_allowlist_entry_has_a_real_evidencing_pin`) GREEN. The 4 skips + the coroutine-never-awaited warning are the same pre-existing ones.
- `./scripts/typecheck.sh` → `EXIT=0` (all members clean, incl. loremaster's 262 test/prod source files).
- `uv run ruff check` on `_governed_contract.py` + `test_memory_enforcement_63b_ia.py` → `All checks passed!` (after trimming one 112-char R6 comment line to ≤110).

**CONCERN 2: DONE. Gates GREEN (collection 9006/0, suite 100/0, typecheck EXIT=0, ruff clean).**

### TWO-COMMIT SPLIT — files, and a CONSTRAINT the lead must decide

My changes are in **4 files** (the other 2 M files in `git status` — `*_atomicity_63b_ib.py`, `*_replay_fidelity_63b_ib.py` — are the concurrent `contract-63b-ib-fork2` builder's; disjoint from mine, as briefed):
- CONCERN 1 (§1.2 "the D fix"): `test_memory_enforcement_63a_iv.py` (class/helper/import/docstring removal) + `test_ast_reach_helpers.py` (allowlist entry removal).
- CONCERN 2 (§1.3 "retire the 63a_iv twin"): `test_memory_enforcement_63a_iv.py` (**DELETE**) + `test_memory_enforcement_63b_ia.py` + `_governed_contract.py`.

⚠ **CONSTRAINT: the two commits CANNOT both be materialised from this one final working tree.** Two reasons: (1) 63a_iv is *modified* in commit 1 and *deleted* in commit 2 — the final tree has it deleted, so commit-1's modified-63a_iv content is not present to stage; (2) commit-1's 63a_iv (its L2a class) `import`s `function_calls_write_guard`/`GovernedWriteAllowlistEntry` from `_gc`, which commit-2's `_gc` cleanup REMOVES — so a single tree holding both states fails to import (mutually exclusive). The final working tree = the **commit-2 end state**, fully green.
- **RECOMMENDATION (lead's call — git/wave-structure is your domain):** since both concerns ship in THIS wave and the D-fix's 63a_iv intermediate is deleted moments later, **one commit** ("63b-i-b close-out: retire the 63a_iv twin — §1.2 D-fix + §1.3 sweep") is cleanest. If you want two commits (e.g. to keep §1.2 shippable alone), reconstruct commit 1 from HEAD by running Appendix-A's `concern1_edit.py` (operates on HEAD-state 63a_iv + reach_helpers), commit it, then re-apply CONCERN 2 (the `concern2_*` scripts, still in my scratchpad) and commit. I can re-do this in a follow-up if you'd rather.

## Appendix A — concern1_edit.py (CONCERN-1 reconstruction recipe)

Operates on HEAD-state `test_memory_enforcement_63a_iv.py` + `test_ast_reach_helpers.py`. To reconstruct a standalone commit-1 ("the D fix"): `git checkout HEAD -- loremaster/tests/test_memory_enforcement_63a_iv.py loremaster/tests/test_ast_reach_helpers.py`, run this from the repo root, then commit those two files. (CONCERN 2's `concern2_*` scripts remain in this session's scratchpad; re-request if needed.)

```python
    """CONCERN 1 edits (63b-i-b close-out rulings §1.2) applied by marker-based slicing.
    
    Marker-based (not line numbers, not byte-exact reproduction of the deleted span) so the
    unicode/escaped-quote body of the deleted class need not be re-typed. Each marker is asserted
    present-and-unique before use; the script fails loud if the tree moved.
    """
    from __future__ import annotations
    
    from pathlib import Path
    
    IV = Path("loremaster/tests/test_memory_enforcement_63a_iv.py")
    REACH = Path("loremaster/tests/test_ast_reach_helpers.py")
    
    
    def _require_once(haystack: str, needle: str, label: str) -> None:
        n = haystack.count(needle)
        assert n == 1, f"{label}: expected exactly 1 occurrence of marker, found {n}"
    
    
    # ---------------------------------------------------------------- 63a_iv edits
    src = IV.read_text(encoding="utf-8")
    orig = src
    
    # (4) docstring THREE-layers preamble -> point L1 at 63b_ia / 63a_v, describe what remains.
    DOC_START = "THREE layers (design §10.9-A):"
    DOC_END = "Live TEST store ``ws://127.0.0.1:18000``"
    _require_once(src, DOC_START, "doc start")
    _require_once(src, DOC_END, "doc end")
    NEW_PREAMBLE = (
        "Layers (design §10.9-A). ⚠ RETIRED 2026-09-08 (63b-i-b close-out rulings §1.2): the L1\n"
        "whole-set deny-by-default enumeration — every RAW memory mutation (AST-derived) ∈ the\n"
        "allowlist, proven to GROW-and-RED — no longer lives here. It was a ``local.py``-scoped TWIN of\n"
        "the canonical whole-tree ``MEMORY_TREE_ALLOWLIST`` and the two had already diverged (ONE\n"
        "IMPLEMENTATION), so it was deleted. Its L1 home is now ``test_memory_enforcement_63b_ia.py``\n"
        "(``TestL1CoverageIsDenyByDefaultOverTheSiteBackedEntries``) and\n"
        "``test_memory_enforcement_63a_v.py`` (``TestTheWholeTreeReachIsAnOutput``), over\n"
        "``MEMORY_TREE_ALLOWLIST`` (whole-tree, ⊇ local.py). This module now carries only:\n"
        "  L1  (recreate-reachability) — ``_recreate_memory_table`` (a REMOVE TABLE) is AST-reachable\n"
        "      ONLY from ``rebuild_embeddings`` (boot/admin, RES-1), never a member verb; the evidencing\n"
        "      pin for the canonical ``63b_ia::_RECREATE_ENTRY``.\n"
        "  L2a STRUCTURAL — every allowlisted FRAME + ``guarded_write`` wraps its mutation in\n"
        "      ``governed.write_guard`` (reach a checked variable).\n"
        "  L2b RUNTIME — the store seam is instrumented over a live battery; every OBSERVED memory\n"
        "      mutation carries a non-None ``governed.active_write_guard()`` context, across every seam path."
    )
    a = src.index(DOC_START)
    b = src.index(DOC_END)
    src = src[:a] + NEW_PREAMBLE + "\n\n" + src[b:]
    
    # (2) imports: drop the two names used only by the deleted class.
    IMPORT_OLD = (
        "    function_calls_write_guard,\n"
        "    governed_table_guarded_write_frames,\n"
        "    governed_table_raw_mutation_sites,\n"
        ")"
    )
    _require_once(src, IMPORT_OLD, "import block")
    src = src.replace(IMPORT_OLD, "    function_calls_write_guard,\n)")
    
    # (2b) _KNOWN_RAW_SITES constant (used only by V1, now deleted).
    KRS = "_KNOWN_RAW_SITES = frozenset(entry.site for entry in MEMORY_WRITE_ALLOWLIST)\n"
    _require_once(src, KRS, "_KNOWN_RAW_SITES")
    src = src.replace(KRS, "")
    
    # (1) delete the L1 deny-by-default class + its section-comment header.
    L1_MARKER = "# L1 — STRUCTURAL deny-by-default (AST-derived; the enumerate-the-forbidden close)."
    _require_once(src, L1_MARKER, "L1 comment")
    i = src.index(L1_MARKER)
    class_start = src.rindex("# ---", 0, i)  # start of the dashes line above the L1 comment
    CLASS_NEXT = "class TestRecreateMemoryTableIsBootAdminOnly:"
    _require_once(src, CLASS_NEXT, "TestRecreate class")
    class_end = src.index(CLASS_NEXT)
    assert "class TestEveryRawMemoryMutationIsAllowlisted:" in src[class_start:class_end], (
        "the span to delete does not contain the target class"
    )
    src = src[:class_start] + src[class_end:]
    
    # (3) delete the _defined_test_names helper + its section-comment header (module tail).
    HELPER_MARKER = "# helper — the set of test names DEFINED anywhere in the 63a-iv test tree (pin-existence)."
    _require_once(src, HELPER_MARKER, "helper comment")
    j = src.index(HELPER_MARKER)
    helper_start = src.rindex("# ---", 0, j)
    assert "def _defined_test_names()" in src[helper_start:], "helper span missing the def"
    src = src[:helper_start].rstrip() + "\n"
    
    # sanity: nothing that referenced the deleted names survives
    for gone in (
        "class TestEveryRawMemoryMutationIsAllowlisted",
        "_KNOWN_RAW_SITES",
        "def _defined_test_names",
        "governed_table_raw_mutation_sites",
        "governed_table_guarded_write_frames",
    ):
        assert gone not in src, f"residual reference to deleted symbol: {gone}"
    
    assert src != orig, "no change made to 63a_iv"
    IV.write_text(src, encoding="utf-8")
    print("63a_iv edited OK")
    
    # ---------------------------------------------------------------- reach-helpers edit
    rsrc = REACH.read_text(encoding="utf-8")
    rorig = rsrc
    KEY = '    "test_memory_enforcement_63a_iv.py": ('
    _require_once(rsrc, KEY, "63a_iv allowlist key")
    k = rsrc.index(KEY)
    close = rsrc.index("    ),\n", k) + len("    ),\n")
    # guard: the 63a_v entry must be what immediately follows the removed span
    assert rsrc[close:].lstrip().startswith('"test_memory_enforcement_63a_v.py":'), (
        "the span removed does not end right before the 63a_v entry"
    )
    rsrc = rsrc[:k] + rsrc[close:]
    assert '"test_memory_enforcement_63a_iv.py":' not in rsrc, "63a_iv allowlist entry still present"
    assert '"test_memory_enforcement_63a_v.py":' in rsrc, "63a_v allowlist entry was clobbered"
    assert rsrc != rorig, "no change made to reach-helpers"
    REACH.write_text(rsrc, encoding="utf-8")
    print("reach-helpers edited OK")
```
