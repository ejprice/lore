# REPORT-contract-63a-v — F5 reach = whole-tree scan + migrate-governed triple (RED contract)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done** (RED-for-the-right-reason contract shipped; satisfiability receipt attached)
- deviations: (1) built the whole-tree SCANNER + both-ways OBSERVER as test infra (like 63a-iv's substrate) — RED-at-HEAD isolates the UNBUILT `governed.governed_exempt` production mechanism, not a stubbed scanner (see §DELTA rationale); (2) FIXED a pre-existing F5 scanner PRECISION defect the whole-tree scan surfaced (prose false-positive), finding **#447** (see §PRECISION); (3) scratch dir `/tmp/cav63av_2261028` could not be `rm`'d (sandbox denied) — disposable, not a worktree.
- Packages considered: none — no new production mechanism specified. All new code is test infra using stdlib `ast` / `tomllib` / `sys._getframe`, mirroring in-tree precedents (`scripts/registration_sites.py::declared_members`, `tests/_sdk_guard.py`'s `co_filename` walk). No package would replace an AST/stack-walk test instrument.
- Reuse ledger: see §DRY (5 new substrate symbols + 1 refactor, all dispositioned).
- Graded: n/a — contract author, not a verdict-rendering audit. (HEAD graded/authored at `b20d100`.)
- decisions-needed: **ONE fork escalated** — the design's both-ways `(file,symbol)` cross-check is UNSOUND for fragment-builder writes; resolved by keying runtime classification on label-OR-valid-exempt with `origin_site` used ONLY for the exempt-token match. See §FORK. (Non-blocking — contract ships with the chosen reading.)
- receipt POINTERS: substrate → `_governed_contract.py` §"F5 WHOLE-TREE REACH"; pins → `test_memory_enforcement_63a_v.py`; RED/GREEN delta → §DELTA; satisfiability → §SAT; mutation plan → §MUTATION; precision fix → §PRECISION.

---

## §MAP — ruled item (§10.9-A CORRECTION) → pin

| ruled item | pin(s) in `test_memory_enforcement_63a_v.py` | HEAD |
|---|---|---|
| **1. L1 file set = OUTPUT of a whole-tree scan (from-truth roots, NOT a hand-list)** | `test_the_whole_tree_derived_set_is_the_known_four_sites` · `test_migrate_memory_scope_is_now_within_f5_reach` · `test_every_whole_tree_site_is_in_the_allowlist` · `test_the_scan_roots_are_derived_from_workspace_members_not_a_hand_list` · `test_a_governed_write_in_any_member_grows_the_reach_and_the_scan_is_precise` | GREEN (from-truth; mutation-proves a hand-list build) |
| **2. L1↔L2 BOTH-WAYS cross-check** | `test_the_classifier_*` (4 controls both directions) · `test_the_observer_patch_set_is_derived_from_the_allowlist` · **`test_the_live_migration_write_is_attributed`** | RED (live migration unclassified at HEAD) + GREEN controls |
| **3. migrate-governed = allowlist's SECOND evidence-backed triple** | **`test_the_governed_exempt_mechanism_is_built`** · **`test_migrate_memory_scope_enters_governed_exempt`** · `test_migrate_memory_scope_updates_only_none_scope_rows` (WHERE scope IS NONE) · `test_every_tree_allowlist_entry_has_a_real_evidencing_pin` | 2 RED + 2 GREEN |
| **4. scanner parametrised by TABLE (63b/64 reuse)** | `test_scanning_for_a_different_table_finds_that_table_not_memory` | GREEN |
| **(surfaced) scanner precision — prose is not a statement** | `test_a_prose_f_string_naming_a_verb_and_the_table_is_not_a_mutation_site` | GREEN (invariant for #447) |

## §DELTA — RED/GREEN at HEAD (`b20d100`)

Across the 3 F5 modules (`test_memory_enforcement_63a_v.py` + the 2 untouched 63a-iv modules): **3 RED, 26 GREEN**.

The **3 RED-for-the-right-reason** (all isolate the UNBUILT production mechanism the builder's GREEN wires):
1. `test_the_governed_exempt_mechanism_is_built` — `governed.governed_exempt`/`active_exempt` do not exist.
2. `test_migrate_memory_scope_enters_governed_exempt` — L2a structural: `_migrate_memory_scope` runs its backfill UPDATE outside any attribution frame.
3. `test_the_live_migration_write_is_attributed` — L2b runtime: the REAL `migrate_governed` backfill is observed **`('run_query','UPDATE',('loremaster/loremaster/principals.py','_migrate_memory_scope'))`** and is **UNCLASSIFIED** (no label, no exempt). ⚠ Its ANTI-VACUITY leg PASSED — the observer's reach genuinely extends to `principals` and it SAW the migration write originating in `_migrate_memory_scope` (the exact coverage the cold audit found MISSING). The RED is the classification, not the reach.

The 26 GREEN are the from-truth whole-tree derivation, the discriminators, the classifier controls (both directions), the table-parametrisation, the statement-shape/justification pin, the evidencing-pin leg, the observer-patch-set-derived meta-reach pin, the precision invariant, and the **entire untouched 63a-iv local.py coverage** (L1 3-site + L2a/L2b member pins).

**Rationale for building the scanner (not stubbing it):** F5 is an INSTRUMENT that grades production; the instrument (AST scanner, seam observer) is test infra the contract author builds — exactly as 63a-iv built `governed_table_raw_mutation_sites` / `observe_governed_table_writes`. The DEFECT (#446) is a production write uncovered by the instrument; the FIX is (a) rebuild the instrument to be from-truth [contract] and (b) wire the production so it is classified [builder]. So RED lives in production (`governed_exempt` unbuilt), and the from-truth/discriminator legs are GREEN once the instrument works — and mutation-prove that a WRONG build does not pass.

## §SAT — satisfiability receipt

Reference build (the builder's GREEN, minimal) applied in a **provenance-asserted scratch** (`./scripts/scratch_copy.sh`):
- `governed.py`: add `_ACTIVE_EXEMPT` contextvar + `active_exempt()` + `@contextmanager governed_exempt(name)` (mirrors the shipped `write_guard`).
- `principals.py::_migrate_memory_scope`: import `governed_exempt`, wrap the backfill `run_query(...)` in `with governed_exempt("migrate-governed"):`.

Receipt: `loremaster.__file__ = /tmp/cav63av_2261028/loremaster/loremaster/__init__.py` (**grading the scratch, not the original — #140-safe**). F5 modules on the reference build → **29 passed, 0 failed**. ruff clean on the reference build (incl. the auto-fixed quoted-annotation nit). All 3 RED pins flip GREEN; nothing else moves. Harder leg (C-DEF): satisfiable after ruff — no orphaned imports introduced.

## §MUTATION — mutation-proof plan (what WRONG build still passes?)

- **RELOCATED HIDDEN CONSTANT** (a builder hand-lists `[local.py, principals.py]` or local.py-only instead of deriving roots from members): FAILS `test_the_scan_roots_are_derived_from_workspace_members_not_a_hand_list` (roots ≠ member-derived set) AND `test_a_governed_write_in_any_member_grows_the_reach…` (a write in the SECOND synthetic member `beta` is NOT derived by a local-only scanner).
- **OBSERVED-NOT-DERIVED** (an L1 blind spot — a runtime write L1 didn't derive, e.g. concat-assembled, running unguarded): FAILS `test_a_bare_unattributed_write_is_unclassified` (label None + no exempt ⇒ unclassified) and, live, `test_the_live_migration_write_is_attributed`'s deny-by-default leg.
- **DERIVED-NOT-OBSERVED / observer reach a hidden constant** (a build whose observer patch-set drops `principals`): FAILS `test_the_observer_patch_set_is_derived_from_the_allowlist` AND the live migration test's anti-vacuity leg (the write would never be observed).
- **BORROWED EXEMPT TOKEN** (a foreign site laundering a governed write through `governed_exempt("migrate-governed")` from a different origin): FAILS `test_a_borrowed_exempt_token_is_unclassified` ((file,symbol) mismatch).
- **DROPPED WHERE-GUARD** (a migrate that grows a non-NONE-scope write — a seizure): FAILS `test_migrate_memory_scope_updates_only_none_scope_rows`.
- **ORPHAN-ON-REMOVAL** (remove `_MIGRATE_ENTRY` from the allowlist): FAILS `test_every_whole_tree_site_is_in_the_allowlist` (migrate's derived site becomes an orphan). Live-proven: with the entry removed, `derived - allowlist = {migrate}` → red.
- **TABLE HARDCODE** (a memory-hardcoded scanner): FAILS `test_scanning_for_a_different_table_finds_that_table_not_memory`.
- **SCANNER PROSE REGRESSION** (loosen the matcher back): FAILS `test_a_prose_f_string_naming_a_verb_and_the_table_is_not_a_mutation_site` AND the exact-4-site whole-tree pin (`principals.py::delete` phantom reappears).

## §PRECISION — the defect the whole-tree scan surfaced (finding #447)

The whole-tree scan's FIRST live run derived **5** sites, not 4: a phantom `principals.py::delete DELETE`. Root cause: F5's OLD static matcher `\b(UPSERT|UPDATE|DELETE)\s+(?:type::record\(|\{?\w)` matched a verb followed by ANY word — so `principals.py::delete`'s SF-63-5 refusal message *"…they own N governed {MEMORY_TABLE} row(s) … the delete is refused"* matched (`delete` + `is`) as a memory DELETE. INVISIBLE while F5 scanned only local.py; surfaced the instant the whole-tree scan reached principals.py — the same reach-expansion-reveals-latent-bug shape as #446 itself.

FIX (in scope — a phantom cannot be sanely classified; adding a bogus allowlist entry would be a false clear): replaced `_RAW_MUTATION_STMT`+`_targets_table` with `_raw_mutation_of_table`, requiring the verb's OPERAND to BE the table (`type::record('<t>'|{HINT}) | <t> | {HINT}`). PRESERVED (verified): the 3 local.py sites; the #444 dynamic-table bound; the docstring exclusion. PINNED as an invariant: `TestTheScannerRejectsProseNamingAVerb` + the exact-4-site pin. Impact was LOW (no production effect — a phantom would only force a bogus entry or a spurious red). Finding **#447** filed.

## §FORK — escalated design ambiguity (non-blocking; chosen reading shipped)

**Design §10.9-A CORRECTION step 2** says the L2 observer "records each observed mutation's originating `(file, symbol)` from the call stack" and the pin "diffs both ways: observed-not-derived → RED; derived-not-observed → RED". Taken literally (the observed origin must MATCH an L1-derived *literal* site), this is **UNSOUND for fragment-builder writes**: L1 derives a site by the STATEMENT-LITERAL's enclosing function (`_upsert_fragment`), but at runtime the seam is called by a DIFFERENT frame (`remember`, after `_upsert_fragment` has returned the composed fragment). A naive `origin_site ∈ L1-derived-set` check would RED every fragment-builder write.

**Chosen reading (shipped):** runtime classification (the uniform L2b rule) is `label is not None` OR (`exempt` names an allowlist entry whose site == the stack `origin_site`). `origin_site` is consulted ONLY for the exempt-token `(file,symbol)` match (design step 4's "a site borrowing another's token fails the match") — which is sound because migrate-governed is SELF-CONTAINED (the literal AND the seam call are both in `_migrate_memory_scope`, so origin == literal site). The observed-not-derived leg is realised as "unguarded escape → unclassified → RED" (a write with no label and no valid exempt), which catches the design's own example (a concat-assembled statement running unguarded). The derived-not-observed leg is realised as the DERIVED observer patch-set + the live migration anti-vacuity (the observer's reach a checked variable).

**Alternative (rejected):** match `origin_site` against the allowlist `frames` (seam-callers) rather than literal sites — buildable but adds a second matching channel with no extra defect-catching over label-based classification for the guarded writes. **Recommendation:** ship the chosen reading; it preserves every INTENT (from-truth reach, borrowed-token caught, escape caught) without the fragment-builder false-positive. Flagging for the adversary/design authority in case a stricter literal reading is intended — if so, the fix is to add the `frames`-match channel (mechanics above), not to change the pins' verdicts.

## §DRY — reuse ledger

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `function_calls_named(src, fn, called)` | grep `function_calls_write_guard` | one caller (63a-iv L2a) | **EXTENDED** — generalised the existing `function_calls_write_guard` to a channel-agnostic scan; `function_calls_write_guard` now delegates to it (ONE implementation; behaviour identical → 63a-iv green). |
| `governed_table_raw_mutation_sites_in_tree` | reuses `governed_table_raw_mutation_sites` per-file | the local.py-scoped scanner | **REUSED** the per-file scanner (the #444 bound + prose fix + docstring exclusion inherited); the tree wrapper only adds from-truth root walking. |
| `derive_member_source_roots` / `declared_workspace_members` | read `scripts/registration_sites.py::declared_members` | the from-truth `[tool.uv.workspace] members` seam | **HAND-ROLLED** the test-tree analog (the script is not importable test infra; same pyproject read, cited). |
| `_originating_prod_site` | read `tests/_sdk_guard.py` `_judge`/`co_filename` walk | the immediate-caller stack idiom | **HAND-ROLLED** mirroring `_sdk_guard`'s walk (that guard is a different instrument; a shared walker was not warranted — cited). |
| `TreeMutationSite` / `TreeWriteAllowlistEntry` / `classify_tree_observed_write` / `seam_modules_for_tree_allowlist` | n/a (new dataclasses/helpers) | — | **HAND-ROLLED** — the whole-tree analogs of `MutationSite`/`GovernedWriteAllowlistEntry`; kept SEPARATE from the local.py types deliberately so 63a-iv is untouched (file-keyed sites need a file field). |

`ObservedWrite` gained 2 DEFAULTED fields (`exempt`, `origin_site`) — the 63a-iv construction is unchanged (EXTENDED in place, not forked). `observe_governed_table_writes` gained `extra_modules` (default None ⇒ old behaviour) — EXTENDED in place.

**Sharing proven by MUTATION:** `function_calls_write_guard` delegating to `function_calls_named` is exercised by the untouched 63a-iv L2a pins (still green). The per-file scanner is shared: the precision fix in `_raw_mutation_of_table` changes BOTH the local.py scan (63a-iv) and the tree scan (63a-v) — verified 63a-iv still derives exactly its 3 sites.

## §DEVIATIONS
- Built the whole-tree scanner + both-ways observer as test infra (rationale in §DELTA) — not a stubbed scanner. RED isolates the unbuilt production mechanism.
- FIXED finding #447 (scanner prose false-positive) in this wave — required (a phantom cannot be classified), pinned as an invariant.
- Scratch `/tmp/cav63av_2261028` left on disk (sandbox denied `rm`); disposable, not a git worktree.

## §GATES
- `test_memory_enforcement_63a_v.py` + 63a-iv modules @ HEAD: **3 failed, 26 passed** (the 3 are the RED-until-built production-gap pins).
- Reference build (scratch, provenance-asserted): **29 passed, 0 failed**; `loremaster.__file__` in scratch.
- `uv run ruff check .` → **All checks passed!**
- `bash scripts/typecheck.sh` → **exit 0** (Success across all members incl. test trees).
- Regression: substrate consumers + 61 modules → **207 passed**; `test_mcp_server.py` → **667 passed**; `test_agent_capability_reach` + `test_425_stamp_owner_63a` → **15 passed**. 0 failed.
