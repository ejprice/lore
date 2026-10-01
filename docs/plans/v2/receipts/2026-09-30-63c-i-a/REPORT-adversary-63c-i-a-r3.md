# REPORT-adversary-63c-i-a-r3 — contract-adversary DELTA pass on revision 3 of the 63c-i-a contract

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations · **VERDICT: CONTRACT INSUFFICIENT** (measured 2026-09-24 against `39935f6`). **Prior floor: 7/7 adversary-r2 survivors KILLED, each EXACTLY on its declared pin(s)** (N1, N1c, N2, N3, N4, N4h, N5, N10 + controls N1b, N4ctl — §4.1). **But 5 NEW wrong builds survive r3's own instruments** (X1, X2, X3, R5, FX1 — §4.2/§4.3), each with a kill-pin proven GREEN on my reference and RED on only its build (§6).
- **Graded:** `39935f6` · HEAD-at-report: `26ff7bb` · DIFFERENT (4 ahead: `83050b9`, `2a23fc3`, `2fd3351`, `26ff7bb` — lead report + plan docs; `git diff --stat 39935f6 26ff7bb -- loremaster lorerunes lorescribe loresigil scripts` is EMPTY, so no pin or symbol this verdict rests on moved).
- **deviations:** (1) wrong builds run through my declare-then-diff lane driver, not `mutation_proof.py` (multi-edit / declared-to-survive — §0); (2) three safe-direction mispredictions recorded, not re-declared (X6, R1, R2 — §8 R-7).
- **Packages considered:** stdlib `inspect`/`ast`/`re`; `unittest.mock.patch` / `MonkeyPatch.setattr` (single-target) → bespoke sweep justified; `gc.get_referrers` (probed: reaches class dicts) → keep_with_trigger for the sweep's stated bound; engine `INFO FOR` parse vs the DDL regexes → keep_with_trigger (our own emitter format). Diff vs author: none on verdicts (§9).
- **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none (no repo symbols added; scratch instruments pasted verbatim, §A). Author's "18 new substrate symbols, all dispositioned" re-counted from their §DRY: 18 ✓.
- **P1b (§5):** 12 invariants — 7 ∀-SAFE with killed door-builds; **5 GUARDED → MISSING**: Q1 decision consumers (X1), Q5 bound one-source (X2), Q7 fake parity first-register-only (FX1), Q8 guard spelling (X3), Q10 FORK-A premise (R5). **P1c (§6a):** 15 instruments — 4 MISSING PIN rows (decision-pin consumer hand-list · FORK-C proxy · id-bound not mutation-proven · FORK-A premise proxy); all others SAFE; empirical legs on every row but the shape normaliser (C).
- **MISSING PINS (§6):** **MP-1** SKIP-gate call site is no consumer leg (X1 — the ROUTING-IS-NOT-SHARING class again, one call site up; recommend GATING) · **MP-2** the id bound is read, never perturbed (X2 — literal twin; recommend GATING) · **MP-3** FORK-C guard pin observes a spelling, not the silent-skip effect (X3; recommend GATING-adjacent — the builder's own edit) · **MP-4** FORK-A bound's premise "emits no relation" unpinned (R5; NON-GATING) · **MP-5** parity matrix drives first registers only (FX1; NON-GATING) · MP-P1 prose (coverage_124 `_emit` docstring false after the dim rider).
- **SAT (own reference, written independently of `ref_build_r3.py`):** 22 contract files `2807 passed`; **FULL SUITE ALONE `-n 12`: `11405 passed, 62 skipped, 3 xfailed` — 0 failed, exit 0** (= the author's count); ruff clean after the lint cleanups; built-world gate = exactly 11 SELF-DESTRUCTs, 0 real mypy errors (§2, §7).
- **RED@HEAD (§1):** 42-file consumer set, r3 vs r2 tests on HEAD production: **0 HEAD-greens turned red; 77 new reds, all new ids, all right-reason** (author's claim confirmed); FORK-C guard holds (0 fake-consumer reds). Author over-claim: parity "36 rows" is 34 (R-1); author's run set `r3b_files.txt` not pasted (R-2).
- **DUAL (§3/§3.1):** my 20-row independent enumeration vs the author's D1–D17 — no ungrounded author row; no virtue lost by any fold (item 9 folds verified; the `dim` rider restored AND pinned — R4 KILLED); one stale docstring introduced (MP-P1); D7 silent on a virtue that survives elsewhere (R-5). **Corpse sweep (§11):** 58 hits, every one individually OK.
- **decisions-needed:** MP-1…MP-5 classification (my recommendation per pin in §6; sidecar rules) · R-3 fork: is `_REFUSAL_ID_SAMPLE_SIZE = 10` normative (I'd pick "any positive bound + a sanity ceiling").
- **Receipt pointers:** §0 capability · §1 RED · §2/§2.1 SAT · §3 DUAL · §4 wrong builds · §5 P1b · §6 MISSING PINS · §6a P1c · §7 pending_contracts · §8 residuals · §9 P-PKG · §10 P-PORT · §11 corpses · §A instruments (verbatim).

---

## 0. Capability check (brief-base §4)
- Reachable, measured 2026-09-24: lore MCP (`lore_comms register` + `heartbeat` succeeded), `git`, `uv run
  pytest/ruff`, `scripts/scratch_copy.sh`, `scripts/pending_contract_gate.py`, the test store
  `ws://127.0.0.1:18000`. I never touched `:18500` or the production TEI embedder.
- **grep/rg are hook-blocked (#473).** Every textual sweep here is `awk` over `git ls-files` or scratch trees — said
  per brief-base §4.
- **`scripts/mutation_proof.py`** takes a required `--expect-red` set and one anchor; most of my builds are multi-edit
  and several are DECLARED to survive (an empty expected-RED set). They run through my own declare-then-diff lane
  driver (`run_lane3.sh` + `my_wbs3.py`, §A), which keeps the tool's discipline: the expected-RED set is resolved from
  `pytest --collect-only -q` BEFORE any wrong-build run and diffed BOTH ways. Deviation from the brief's "use
  `mutation_proof.py`", same as adversary-r2 §0.
- Store reference `docs/reference/surrealdb-31-capabilities.md` read first (the six-fact header, §0, §1.1–1.2). This
  wave is test substrate + the i-a registry/migrate; the only engine facts I lean on are §1.1 (OVERWRITE lands) and
  §1.4 (a whole-row UPDATE re-validates), both cited by the contract under grade, neither re-probed.
- Host memory: `free -g` available 34 GB before the first run; every pytest session of mine ran alone (other
  projects' small pytest processes were present on the box — not mine, not lore's).

## 3. DUAL — my independent enumeration of the r3 diff's deletions (written BEFORE opening the author's §DUAL)
Method: `git diff 88205a4 39935f6 -- loremaster lorerunes scripts` (2603 lines), every `-` hunk read; awk listing of
deleted `def`/`class Test` lines. Production is untouched by r3 (`git diff --stat 88205a4 39935f6 -- loremaster/loremaster
lorerunes` is empty). Each row: what was deleted/replaced · the virtue it carried · where (if anywhere) it survives.

| # | deleted / replaced (file · symbol) | virtue it carried | my verdict before reading §DUAL |
|---|---|---|---|
| E1 | `_governed_contract`: `_GOVERNED_FIELD_SPECS_EMITTER`, `_DEFINE_RELATION_EMITTER`, `_schema_string_constants`, `_resolve_schema_table`, `_governed_node_tables`, `_governed_relation_tables`; `governed_populations(schema_source=)` → `governed_populations(*, emitted_ddl=)` | (a) an OUTPUT, never a hand list; (b) F-TRAP-1: a lone `owner_principal` never joins; **(c) node membership keyed on CALLERS of `_governed_field_specs` — so a table whose trio was HAND-ROLLED (not via the ONE emitter) did NOT join, and the exact five-set pin reddened** | (a) kept (growth pins); (b) kept (full-trio rule, pinned both ways); **(c) DROPPED on purpose** (amendment-4 "separation of concerns": a hand-rolled trio IS governed data; emitter provenance is "W1-1's rewrite kill-pin's job"). ⚠ W1-1's rewrite pin covers `agent` only — see §3.1 for whether `memory`/`message` keep an emitter-provenance pin |
| E2 | `test_memory_enforcement_63b_ia::test_a_relation_over_a_RE_EXPORTED_endpoint_joins_and_a_non_str_re_export_does_not` (deleted) | a re-exported endpoint joins; a non-`str` re-export does not; a literal control | re-export/literal: emitted bytes are identical → spelling no longer exists (carried by the relation-leg params + the real five-set). Non-`str` leg: meaningless at DDL level. **No virtue lost.** |
| E3 | `test_memory_enforcement_63b_ia::test_the_population_derivation_reach_is_a_checked_variable` — Python-source fixtures → DDL text; the `NotImplementedError` → `pytest.fail` guard removed | baseline == {memory}; growth; relation join; F-TRAP-1 exclusion | all four assertions kept (merged `grown != baseline and widget in grown`); guard message cosmetic. **No loss.** |
| E4 | `test_message_enforcement_63b_ii_a::test_the_population_set_is_an_OUTPUT_not_a_hand_list` — source → DDL | "message joins only when it CALLS `_governed_field_specs`" | re-keyed to "only when it carries the full trio" (E1(c) again) + a NEW "`to` must not join while neither endpoint governed" leg. |
| E5 | `patch_shared_object_everywhere` r2 body (name ∧ identity, `getattr(module, attribute) is original`, bare module names returned) | never clobbers an unrelated same-named attribute; non-vacuity via the callers' `assert patched` / `startswith("lorerunes")` | identity-alone preserves "never clobbers a different object"; non-vacuity moved INTO `expect_in` (raises). One construction-only difference: `getattr` also saw PEP 562 module `__getattr__` attributes, `vars()` does not — **no production module defines a module-level `__getattr__`** (awk over `git ls-files` of all members: 0 hits), so moot today. |
| E6 | `_logging_fixtures._rebind_everywhere` inline `sys.modules`/`vars`/`is` loop → `module_level_bindings_of` | by-identity reach over module namespaces | byte-equivalent loop (same `TypeError` skip). **No loss.** |
| E7 | `test_secret_typing::TestTheBlanknessPredicateIsGENUINELYSHARED._patch_everywhere` (name-keyed, `hasattr`, `raising=False`, `patched >= 1`) | import-style agnostic; a private copy is caught; non-vacuous | kept (identity sweep + `expect_in=("lorerunes",)` raises); the old name-keyed false CLEAR is gone; leg 3's formerly UNCHECKED second call is now checked. **Strengthened.** |
| E8 | `test_engine_rejection_seam::_patch_everywhere` (module-level, name-keyed) + its two `assert patched` | "covers a direct import AND a call-time delegator"; non-vacuous | direct import: identity sweep. Call-time delegator: a delegator that imports at call time reads the (patched) home binding → still moves. Non-vacuity: `expect_in` at `lorerunes` / `loremaster.store._txn`. **No loss** (verified empirically by the SAT run: §2). |
| E9 | `test_ddl_write_target_coverage_124::_ddl_generators` / `_emit` bodies → delegate | derived generator set; `dim` passed whenever present | kept by `schema_ddl_generators` / `emit_schema_ddl` (post-rider). ⚠ **its `_emit` docstring now says "passing ``dim`` only if it REQUIRES one" — FALSE after amendment-5's rider** (the shared helper passes it whenever present). Prose defect, §6 MP-P1. |
| E10 | `test_principal_keys_schema::_all_schema_ddl` (`dir()` + `callable`, `dim` whenever present) → `emitted_schema_ddl(dim=NONDEFAULT_DIM)` | NONDEFAULT_DIM threaded; every `generate_*_ddl` | threading kept (rider restored, and pinned by the synthetic DIM pin); membership narrowed `callable` → `isfunction` — the amendment-5 stated bound. |
| E11 | `test_comms_footer::…moves_EVERY_members_refusal` — `assert patched` → `expect_in=("loremaster.agents",)`; failure prose "a member that survives is running its own copy … the only test that tells DRY from looks-DRY" → honest-bound text | non-vacuity; the accusation | non-vacuity kept (raises); accusation replaced by the two-cause honest text (MP-G rider 2). **No loss.** |
| E12 | `test_agent_registry::…identifier_decision_is_the_SHARED_is_legal_identifier` — r2 single body (register + refuse-policy) → consumer axis | per-field; register refuses + zero rows; refuse-policy raises; `startswith("lorerunes")` non-vacuity | every r2 leg kept per consumer; skip-policy + fake legs NEW; non-vacuity → `expect_in`. The r2 refuse-policy BASELINE kept. **No loss.** |
| E13 | regex-twin pin: `assert any(startswith("lorerunes"))` → `expect_in`; `pytest.raises` → try/else + honest message | identity sweep of the pattern object + zero rows | kept. |
| E14 | blank-role pin: `assert patched` → `expect_in`; fake leg NEW | register refuses under mutated `is_blank` | kept + extended. |
| E15 | keep_scope formatter pin: `assert patched` → `expect_in`; lying accusation → honest text | stamped scope moves | kept (and the MP-G false RED is gone — measured, §4). |
| E16 | R-Q5-1: 2 fixed traps + "EVERY trap id named" → three populations reading `principals._REFUSAL_ID_SAMPLE_SIZE` | count beside noun; every id named; byte-inert | below-cap/at-cap keep "every id"; above-cap INVERTS it to exactly `bound` (the r2 MP-C contradiction removed). |
| E17 | exempt-token: inline shape asserts → `_assert_the_backfill_statement_shape` (R-6 normalise) | ONE scope-keyed UPDATE, all three `SET`s; token == executed | token==executed unchanged (`_normalise_statement` is exactly the old `" ".join(split())` — read); shape normalises `;` and `\s*=\s*` only. **No widening** (its wrong-statement controls stay red). |
| E18 | `_comms_fakes.FakeAgentRegistry.register` inline XOR → `_refuse_what_the_writer_refuses` (+ identity + blank legs) | the A3 XOR raise | moved verbatim; NEW legs added. |
| E19 | heartbeat control docstring (E2-bis) | prose | prose only. |
| E20 | `scripts/pending_contracts.yaml` r2 entry edits + new r3 entry | adjudication | §7. |

### 3.1 DIFF of my E1–E20 against the author's §DUAL D1–D17 (read AFTER §3 was written)
- **Author rows ungrounded in the diff:** none. D1↔E16, D2↔E12, D3↔E5, D4↔E11, D5↔E13/E14/E15, D6↔E6, D7/D8↔E1, D9↔E3/E4, D10↔E2, D11↔E7, D12↔E8, D13↔E9, D14↔E10, D15↔E14, D16↔E17, D17 (the dim rider) — present in mine as the E9/E10 "post-rider" note.
- **Mine, absent from theirs:**
  - **E1(c)** — the retired resolver's "node membership keyed on CALLERS of `_governed_field_specs`" (a hand-rolled trio did NOT join). D7 lists only virtues (1)+(2). The virtue is dropped DELIBERATELY by amendment-4 ("separation of concerns"), and I checked where emitter provenance now lives per governed table (awk over `git ls-files loremaster/tests`): `agent` → `test_agent_owns_principal_schema.py` W1-1 rewrite kill-pin; `memory` → `test_governed_schema_63a.py` (monkeypatches `surreal_schema._governed_field_specs` and demands the memory slice move); `message` → `test_message_governed_ddl_63b_ii_a.py` (same shape). **Verdict: virtue survives for the whole known set; the author's DUAL row is merely silent on it — prose gap, not a lost pin.** (For a FUTURE governed table no per-table provenance pin exists until its packet writes one — pre-existing, same as before r3.)
  - **E9** — `test_ddl_write_target_coverage_124::_emit`'s NEW docstring ("passing ``dim`` only if it requires one") is FALSE since amendment-5's rider (the shared `emit_schema_ddl` passes it WHENEVER present). The author applied the rider to the helper and its pin but left the delegating docstring stating the retired rule. → §6 MP-P1 (prose, the #P8d natural-language class).
  - **E5** — PEP 562 reach difference (`getattr` vs `vars`): moot, 0 production `def __getattr__` at module level.
  - **E18** — not a deletion (moved verbatim); no row needed.
- **Net:** no virtue lost by any fold; one stale prose line introduced (E9).

## 9. P-PKG — my table FIRST (built from the r3 diff before reading the author's `Packages considered:` detail), then the diff
| mechanism r3 specifies / introduces | candidates | what I READ | verdict |
|---|---|---|---|
| identity-alone binding sweep (`module_level_bindings_of` → `patch_shared_object_everywhere` / `_rebind_everywhere`) | `unittest.mock.patch`, `pytest.MonkeyPatch.setattr` (single dotted target — adversary-r2 §9 read both installed signatures); stdlib **`gc.get_referrers`** | probed live 2026-09-24: `gc.get_referrers(f)` for a function bound in a module, a class body and a closure returns 3 referrers, all `dict` (module/class namespaces) — it reaches class attributes the module sweep cannot, but rebinding inside arbitrary referrer containers is not a safe mutation | **bespoke — justified** (no package rebinds every binding of one object). `gc.get_referrers` is the natural instrument for the helper's stated re-open trigger (a correct build holding the object in a class attribute); not needed today. |
| emitted-DDL reading (`_DEFINE_FIELD_ON_RE`, `relation_endpoints`, extended `_DEFINE_RELATION_RE`) | a SurrealQL parser package (none installed/known); the ENGINE's own parse (`INFO FOR DB/TABLE` after applying the DDL to a virgin test DB — the tree already normalises INFO via `_governed_contract.schema_snapshot_from_info`) | `schema_snapshot_from_info`'s docstring ("definition strings taken VERBATIM — no parse, no regex"); `_define_field` / `_define_relation_table` are the only emitters of those statement forms | **keep_with_trigger** — the text is OUR generators' fixed format, relation parsing fails CLOSED, and the exact five-set pin reds any node-leg format drift on the known tables. Trigger: the first governed DDL emitted by a path other than `_define_field` / `_define_relation_table` (then the engine-INFO route is the honest parser). |
| generator discovery (`inspect.getmembers(surreal_schema, inspect.isfunction)` + naming contract) | stdlib `inspect` | installed `inspect.getmembers` / `isfunction` | **stdlib, in-house fold** — correct (amendment-5 FORK-B); `isfunction` bound stated. |
| AST allowlist scan over `AGENT_NAME_PATTERN` reads | stdlib `ast`; `libcst`/`astroid` (not needed for a Load-context name/attr walk) | `_pattern_decision_sites` source | **stdlib bespoke** — fine; reach REUSES `parse_production_trees` + `assert_scan_reached_every_member`. |
| the fake's shared-predicate routing / guard | none (routing to `lorerunes`) | `_comms_fakes` diff | n/a — REUSE of `lorerunes.is_blank` / `is_legal_identifier`. |
| id bound (`principals._REFUSAL_ID_SAMPLE_SIZE`) | none (a constant) | amendment-4 MP-C | n/a. |

**Diff vs the author's line** (`stdlib ast/inspect/re/types/sys; MonkeyPatch.setattr single target; no production mechanism`): agreement on every verdict. Mine adds two considered-and-rejected alternatives the author did not name (`gc.get_referrers` for the sweep's bound; the engine's INFO parse for the DDL reader), each `keep_with_trigger`, neither a defect. No `bespoke` verdict on either side rests on an unread API.

## 10. P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` — the lore repo; my own seam enumeration over the r3 tests and fixtures found 0 Odoo models/fields/methods/views/ACLs/ORM paths. Author's line matches (0 = 0).

## 11. P6 — corpse sweep (awk, BARE patterns, every `git ls-files` path; measured 2026-09-24 at `83050b9`)
Patterns (r3's retired names): `_schema_string_constants|_resolve_schema_table|_governed_node_tables|_governed_relation_tables|_GOVERNED_FIELD_SPECS_EMITTER|_DEFINE_RELATION_EMITTER|schema_source|_patch_everywhere|RE_EXPORTED_endpoint` → **58 hits in 19 files.** Each, individually:
- `loremaster/tests/_governed_contract.py:952` — MP-G docstring naming the retired copies' false clear · **OK (history in prose)**.
- `loremaster/tests/_governed_contract.py:2238`, `:2239` — the DUAL comment listing the retired resolver symbols · **OK (DUAL)**.
- `loremaster/tests/_governed_contract.py:2320` — `governed_populations` docstring: "RENAMED from r2's ``schema_source``" · **OK (DUAL)**.
- `loremaster/tests/test_agent_governance_63c_i_a.py:550` — MP-G self-test banner · **OK (prose)**.
- `loremaster/tests/test_engine_rejection_seam.py:674` — DUAL comment at the deleted helper · **OK (DUAL)**.
- `loremaster/tests/test_memory_enforcement_63b_ia.py:1241` — DUAL docstring naming the deleted re-export pin · **OK (DUAL)**.
- `loremaster/tests/test_memory_enforcement_63b_ia.py:1267`, `:1271` — `test_the_old_SOURCE_parameter_is_refused_loudly` asserting `schema_source=` raises `TypeError` · **OK — the one LIVE use, and it asserts the corpse is DEAD**, not that it works.
- `loremaster/tests/test_secret_typing.py:1367` — DUAL comment · **OK (DUAL)**.
- `docs/design/2026-09-24-packet63c-amendment-2.md:16`, `:25` — ruling text naming the r2 resolver fix · **OK (dated ruling, superseded by amendment-4)**.
- `docs/design/2026-09-24-packet63c-amendment-3.md:85`, `:87`, `:89`, `:90`, `:92`, `:150`, `:160` — F-3 / F-5 rulings naming the copies · **OK (dated ruling)**.
- `docs/design/2026-09-24-packet63c-amendment-4.md:96`, `:97`, `:176` — MP-D / §W naming the retirement · **OK (the ruling that retires them)**.
- `docs/plans/v2/receipts/2026-08-23-packet61/REPORT-contract-61a-w2.md` (1) and `docs/plans/v2/receipts/2026-09-04-packet63b/REPORT-{adversary-63b-i-a-2 (2), build-63b-i-a (1), contract-63b-i-a-2 (1), contract-63b-i-b (1)}.md` — archived receipts · **OK (archived history, dated)**.
- Repo-root `REPORT-adversary-63c-i-a.md` (5), `REPORT-adversary-63c-i-a-r2.md` (12), `REPORT-contract-63c-i-a-r2.md` (6), `REPORT-contract-63c-i-a-r3.md` (6), `REPORT-lead-63c.md` (1) — the wave's own reports · **OK (history; the lead archives them)**.
- **No corpse: no live test asserts a retired name WORKS; no production file names any of them.**

## 7. FOCUS 5 — `scripts/pending_contracts.yaml` (r2 entry edits + the new r3 entry)
- **Edits read** (`git diff 88205a4 39935f6 -- scripts/pending_contracts.yaml`, +48/−1): r2 entry — `test_agent_registry.py` gains `missing_symbols: ["register.session_keep_id"]` (the parity matrix's direct kwarg call); NEW `_comms_fakes.py` row (`missing_symbols: ["lorerunes.is_legal_identifier"]` + `no-any-return` ×1, the FORK-C guarded import). NEW entry `packet-63c-i-a-contract-r3` — `test_agent_governance_63c_i_a.py`, `attr-defined` ×1 (`principals._REFUSAL_ID_SAMPLE_SIZE`). Owner (the i-a build), trigger (the constant resolves), ruling (amendment-4 §MP-C) all concrete and real.
- **At HEAD** (scratch `…/scratchpad/head` = `83050b9`, provenance `…/scratchpad/head/loremaster/loremaster/__init__.py`), `pending_contract_gate.py --currency --legs typecheck,ruff`: **`typecheck RED_ADJUDICATED — 17 residual(s), owned by: packet-63c-i-a-contract-r2 · packet-63c-i-a-contract-r3`** · **`ruff GREEN`** · `CURRENCY: FAIL — claimed but never run: pytest`. Reproduces the author's §GATES exactly (17).
- **On the built world** (scratch `…/scratchpad/built` = `83050b9` + my `my_ref_build.py`, which includes the builder's granted guard deletion; provenance `…/scratchpad/built/loremaster/loremaster/__init__.py`; ruff `All checks passed!`), same command: **`typecheck RED_ORPHANED — 11 residual(s)`, ALL ELEVEN `SELF-DESTRUCT`** — 9 r2 files "produced NO mypy errors", 1 r2 symbol `lorerunes.is_legal_identifier` "now RESOLVES", 1 r3 file "produced NO mypy errors". **No real mypy error on the build.** Matches the author's §SAT (11).
- **#461 (would any entry self-destruct WRONGLY?):** no. Every registered file is mypy-red at HEAD (17 residuals, all adjudicated), so the no-errors leg cannot fire before the build. Partial builds discharge exactly the claims they make false: the constant alone discharges only the r3 entry (its reopen_trigger says so); the kwarg alone discharges the kwarg-only files; the `_comms_fakes.py` row discharges when the predicate exists, whether or not the guard is deleted yet (the guarded import is typed once the symbol exists) — correct, the guard's removal is the conditional PIN's job, not mypy's.
- **Verdict: honest, and both entries self-destruct exactly on the built world.** Process note (unchanged from r2): the builder deletes BOTH entries in the build commit; currency forces it.

## 2. SATISFIABILITY — my OWN reference (`my_ref_build.py`, §A.1)
- **Instrument:** adversary-r2's `my_ref_build.py` (its §A.1, the r2 reference I am the independent successor of — NOT the r3 author's `ref_build_r3.py`, which I did not read before building) + three r3 legs of mine: `principals._REFUSAL_ID_SAMPLE_SIZE = 10` USED by the slice (`owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]`); the builder's ONE granted test-tree edit (the fake's `try/except ImportError` deleted, amendment-5 FORK-C rider 3); the lint-demanded cleanups (`agents.py` unused `import re` — F401; one E501 wrap in `principals.py` the r3 edit's longer slice produced). Scratch `…/scratchpad/ref` via `scratch_copy.sh`, committed there as branch `adv3-ref`. Provenance: `loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad/ref/loremaster/loremaster/__init__.py`, `lorerunes.__file__ = …/scratchpad/ref/lorerunes/lorerunes/__init__.py`; `is_legal_identifier("fixer-b"), is_legal_identifier("fixer-b\n")` → `True False`.
- **Lint AFTER the cleanups:** `uv run ruff check .` → `All checks passed!` (so SAT holds after the lint-demanded edits, the C-DEF harder leg).
- **The 22 contract files** (`files.txt` = every `test_*.py` `0b8ce37..39935f6` touches + `test_comms_wiring.py`), `pytest -n 8`, alone: **`2807 passed, 4 warnings in 317.68s` — 0 failed, 0 errors.** Measured 2026-09-24 against tests at `39935f6`.
- Full suite ALONE `-n 12`: §2.1 (run after the lane, so no two pytest sessions of mine overlap).

## 4. P1 — wrong builds (the headline)
**Method.** Lane `…/scratchpad/ref` (provenance as §2), every build applied ON TOP of `adv3-ref` by `my_wbs3.py` (exactly-once anchors — a no-op edit aborts), reset between builds (`git checkout -f adv3-ref && git clean -fd`). DECLARED expected-RED ids resolved from `collected3.txt` (`pytest --collect-only -q` over the 22 files → **2807 ids**) BEFORE any wrong-build run; `run_lane3.sh` diffs observed vs declared BOTH ways from junit (§A). One pytest session at a time, `-n 8`. Measured 2026-09-24, tests at `39935f6`.

### 4.1 The prior pass's 7 survivors (adversary-r2 §4.2) + its 2 controls — ALL KILLED, each EXACTLY on its declared pin(s)
| build | the door (r2) | tail (22 files) | verdict · the pin(s) that killed it |
|---|---|---|---|
| **N1** | server home keeps `AGENT_NAME_PATTERN.fullmatch`; refuse policy calls the predicate directly | `3 failed, 2804 passed` | **KILLED exactly 3/3** — `…SHARED_is_legal_identifier[name-skip-policy]`, `[session-skip-policy]`, `TestTheIdentifierPatternIsReadOnlyForProseOutsideLorerunes63cIA::test_no_production_module_outside_lorerunes_DECIDES_with_the_pattern` |
| N1b (ctl) | as N1 with `.match` | `3 failed, 2804 passed` | KILLED exactly 3/3 (same three; no longer needs `test_anchored_pattern_seam.py` — r2 R-9 closed) |
| **N1c** | home = private DRIFTED `re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}")` | `2 failed, 2805 passed` | **KILLED exactly 2/2** — the two skip-policy legs (the AST scan is blind by design; its threat model says so) |
| **N2** | A3 XOR only inside the CREATE branch | `2 failed, 2805 passed` | **KILLED exactly 2/2** — `…refused_on_the_RE_REGISTER_path_too[owner-without-keep]`, `[keep-without-owner]` |
| **N3** | refusal joins ALL ids | `1 failed, 2806 passed` | **KILLED exactly 1/1** — `test_R_Q5_1_…[above-cap]` |
| **N4** | new `owns(agent→memory)` relation, KEYWORD endpoints | `1 failed, 2806 passed` | **KILLED exactly 1/1** — `test_the_derived_population_set_grows_to_memory_message_to` (the emitted-DDL resolver sees it; spelling no longer exists) |
| N4ctl (ctl) | the same relation, positional | `1 failed, 2806 passed` | KILLED exactly 1/1 (same pin) — N4 and N4ctl now get the SAME verdict: the r2 spelling asymmetry is gone |
| **N4h** | N4 + `enforced=True` + a `KNOWN_RELATION_EDGES` row | `1 failed, 2806 passed` | **KILLED exactly 1/1** — the five-set pin (the relation now JOINS the population, so the exact set reds) |
| **N5** | the fake stamps `'WRONG'` / `'keep:WRONG'` | `2 failed, 2805 passed` | **KILLED exactly 2/2** — parity matrix `[pair-both-set]`, `[pair-alpha-none]` |
| **N10** | re-register HEALS a NONE-scope row's `scope` + `owner_agent` | `2 failed, 2805 passed` | **KILLED exactly 2/2** — `test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row[alpha-register]`, `[legacy-seed]` |

**7/7 prior survivors KILLED** (r2's MP-A, MP-B, MP-C, MP-D, MP-E, MP-F closed empirically; MP-G in §4.2 X4/X5). Every kill fired EXACTLY the declared set: 0 unexpected reds, 0 declared-still-green.

### 4.2 New wrong builds against r3's instruments (declared BEFORE the run; tails over the 22 files, 2807 tests)
| build | instrument attacked | the door | tail | verdict |
|---|---|---|---|---|
| **X1** | A4-bis consumer set (item 1) | `_comms_traffic_line`'s SKIP gate stops reading the home and decides with a private DRIFTED `re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", …)` (admits `.` TODAY) | **`2807 passed`** | **SURVIVES** (declared: survives) → **MP-1** |
| **X2** | MP-C named bound (item 5) | `_REFUSAL_ID_SAMPLE_SIZE = 10` defined, but the slice restates the literal `[:10]` — two sources that agree at birth | **`2807 passed`** | **SURVIVES** (declared) → **MP-2** |
| **X3** | FORK-C conditional guard pin (item 8) | the guard is KEPT post-build, spelled `except Exception:` | **`2807 passed`** | **SURVIVES** (declared) → **MP-3** |
| X3b (ctl) | same | the guard kept as ruled (`except ImportError`) — "builder forgot the deletion" | `1 failed, 2806 passed` | KILLED exactly — `test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists` |
| X4 | MP-G (item 6) | a CORRECT build: `agents.py` binds `is_blank`, `is_legal_identifier`, `keep_scope` under ALIASES | `2807 passed` | **GREEN as declared** — r2's MP-G false RED is gone (all four identity-sweep pins in that file follow the aliases) |
| X5 | MP-G | a PRIVATE `def keep_scope` in `agents.py` WEARING the shared name (import dropped) | `1 failed, 2806 passed` | KILLED exactly — `test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter` |
| X5b | MP-G | a private copy under ANOTHER name (`_private_scope`) | `1 failed, 2806 passed` | KILLED exactly — same pin |
| X6 | A4-bis AST allowlist | the home decides with `re.fullmatch(AGENT_NAME_PATTERN.pattern, value)` — a `.pattern` read, the scan's SAFE shape | `4 failed, 2803 passed` | KILLED — declared the 2 skip-policy legs; **also** `[name-refuse-policy]`, `[session-refuse-policy]` (the refuse policy reads the home — my misprediction, safe direction). The AST scan stays green on it, BY DESIGN (the mutation pin owns this door). |
| X7 | NF-2 (item 2) | the identity MOVE only on the CREATE path | `26 failed, 2781 passed` | KILLED exactly 26/26 — every `[<corpus shape>-{name,session}]` leg |
| X8 | MP-F (item 4) | re-register heals ALL THREE columns (takeover door) | `2 failed, 2805 passed` | KILLED exactly — mint-once `[alpha-register]`, `[legacy-seed]` |
| X9 | parity matrix (item 8) | the REAL α CREATE stamps `owner_agent` only when an owner is present (§2.2: always self) | `1 failed, 2806 passed` | KILLED exactly — parity `[pair-alpha-none]` (the fake stamps self unconditionally) |
| R1 | resolver growth + FORK-A (item 7) | a NEW `generate_widget_ddl` emitting the full trio through the ONE emitter | `3 failed, 2804 passed` | KILLED — declared five-set + FORK-A gap pin (both fired); **also** `test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned::test_the_record_principal_link_set_matches_the_cascade_adjudication` (a new `record<principal>` link — a third consumer of the SHARED corpus moving; safe direction) |
| R2 | generator REACH (naming contract) | the same slice from `build_widget_ddl` (NOT `generate_*_ddl`) + a `WIDGET_TABLE` constant | `2 failed, 2805 passed` | KILLED — by `test_ddl_write_target_coverage_124.py::TestEveryTableConstantIsDeclared::test_every_table_constant_value_is_a_declared_table` + `…TestTheCoverageInvariantDiscriminates::test_a_planted_undeclared_constant_would_redden_the_invariant`. Formally declared `[]` (survive); I revised the prediction in my session notes (NOT in a file, so unverifiable by a reader) before its run after reading #124's invariant, and did not re-declare — **recorded as my misprediction**. Consequence: the naming-contract bound is CLOSED by #124's ∀ pin for any table that has a `*_TABLE` constant (the house idiom). |
| R3 | FORK-A pin-the-miss (CLOSE leg) | `ALL_DDL_GENERATORS` gains lease + floor_calibration (the gap closes) | `1 failed, 2806 passed` | KILLED exactly — `test_KNOWN_BOUND_the_ALL_DDL_GENERATORS_hand_list_gap_is_EXACTLY_lease_and_floor_calibration` |
| R4 | FORK-B dim rider | `emit_schema_ddl` passes `dim` only when REQUIRED | `1 failed, 2806 passed` | KILLED exactly — `test_emit_threads_dim_WHENEVER_present_and_fails_closed_on_any_other_required_parameter` |

**Kill-pin pairs (P0 controls), `test_adv_r3_killpins.py` (§A.4), `-n 4`, measured 2026-09-24:** on `adv3-ref` → **`13 passed`** (4 kill-pins + 9 tests the file collects from the imported `TestAgentMigrateScopeKeyed63cIA` class — harmless). On X1 → `1 failed, 12 passed` (`test_KP_X1_…`). On X2 → `1 failed, 12 passed` (`test_KP_X2_…`). On X3 → `1 failed, 12 passed` (`test_KP_X3_…`). On X3b → `1 failed, 12 passed` (`test_KP_X3_…` — the effect pin ALSO catches the ruled guard shape, so it is a strict superset of the conditional source-text pin). On FX1 (§4.3) → `1 failed, 12 passed` (`test_KP_FX1_…`). Each wrong build reddens ONLY its own pin.

## 5. P1b — QUANTIFIER TABLE (r3's invariants; each GUARDED row carries a receipt)
Door-builds: §4 (lane `ref`, 22 files, 2807 tests) and §4.3 (batch 2). Measured 2026-09-24, tests at `39935f6`.

| # | invariant (ruling) | pinned as | class · receipt |
|---|---|---|---|
| Q1 | the identity DECISION is `lorerunes.is_legal_identifier` for EVERY consumer (A4-bis) | decision mutation × {register, refuse-policy, skip-policy (= the HOME `_is_comms_charset_legal`), fake} × {name, session}; + AST allowlist on `AGENT_NAME_PATTERN` reads | **GUARDED by a hand-list of consumer ENTRY POINTS — MISSING one CALL SITE.** N1/N1b/N1c/X6 KILLED. **X1 SURVIVES 2807/0:** the SKIP gate itself (`_comms_traffic_line`) bypasses the home with a private drifted regex; the pin probes the home, never the gate, and the AST scan cannot see a regex that never names the pattern. A4-bis says the SKIP gate "reads the home and is NOT rewired" — that clause has no pin. → **MP-1** |
| Q2 | register refuses a hostile identity ∀ paths (NF-2) | 13 corpus shapes × {name, session} on the RE-register of a legacy row | **∀ — SAFE.** X7 (MOVE on CREATE only) KILLED 26/26. |
| Q3 | the A3 XOR refusal ∀ paths (MP-B) | both mixed pairs after a consistent first register | **∀ — SAFE.** N2 KILLED 2/2. |
| Q4 | mint-once ∀ rows (MP-F) | α row + legacy-seed row, credentialed re-register | **∀ over rows — SAFE on the REAL writer.** N10 (heal 2) and X8 (heal 3) KILLED 2/2. **On the FAKE: guarded by "first register"** — see Q7. |
| Q5 | the refusal names the FULL count + `min(bound, count)` ids ∀ N (MP-C) | 3 populations: 2, bound, bound + 15 | **∀ over N — SAFE** (N3 KILLED). **But "the bound is ONE named source" is GUARDED by the constant's birth value:** X2 (constant 10 + literal `[:10]`) SURVIVES 2807/0 — the pin READS the constant but never PERTURBS it, so a restated literal that agrees at birth is invisible (the author's LIT10 build differs in the literal's VALUE, which is why it was caught). → **MP-2** |
| Q6 | the sharing instrument moves ∀ bindings of THE object and never a different object (MP-G) | 5 synthetic self-tests + every sharing pin | **∀ over binding NAMES — SAFE.** X4 (all-alias CORRECT build) GREEN; X5 (private copy wearing the name) and X5b (other name) KILLED; IM3n (the ONE finder finds nothing) — §4.3. Stated bound: module-level bindings only (class attr / container / closure) — pinned in the docstring with a re-open trigger. |
| Q7 | the fake mirrors the writer ∀ inputs (MP-E + F-2) | 34-row parity matrix (4 pairs + 13 × 2 hostile + 4 blank roles = 34 collected ids; the author's "36" is an over-count, §8 R-3) through real + fake, FIRST register only | **GUARDED by "first register".** N5 and X9 KILLED. **FX1** (the FAKE heals an unstamped row on RE-register — N10's door, fake-side) — §4.3 → **MP-5** if it survives. |
| Q8 | the fake's HEAD-RED guard does not outlive its premise (FORK-C rider 2) | AST: no `except` handler naming `ImportError` once the predicate exists | **GUARDED by one SPELLING of the guard.** X3b (the ruled spelling kept) KILLED; **X3 (`except Exception:` kept) SURVIVES 2807/0** — the pin observes source TEXT, not the effect (a silent skip when the predicate is absent). → **MP-3** |
| Q9 | the governed population = ∀ tables whose EMITTED DDL carries the full trio ∪ relations touching them (MP-D) | emitted-DDL resolver over every `generate_*_ddl`; exact five-set; growth/partial/relation/fail-closed pins; inventory cross-check | **∀ — SAFE.** N4/N4ctl/N4h/R1 KILLED; R2 (misnamed generator) KILLED by #124's constant-coverage ∀ pin. |
| Q10 | the ALL_DDL_GENERATORS gap is EXACTLY {lease, floor_calibration} and is "not a live hole" (FORK-A) | exact-set pin-the-miss | **the SET is ∀ — SAFE** (R1 grow and R3 close both KILLED). **The PREMISE ("neither emits a relation") is unpinned:** R5 — §4.3 → **MP-4** if it survives. |
| Q11 | `dim` threaded whenever present (FORK-B rider) | synthetic generators, required + defaulted | **SAFE.** R4 KILLED. |
| Q12 | the backfill shape is normalised, never widened (R-6) | 4 correct spellings pass, 3 wrong fail | SAFE — author's R6 (normaliser widened back to raw) PROOF HELD 3/3; I did not re-run it (construction: `_statement_shape` only strips one `;` and rewrites `\s*=\s*`; its wrong-statement controls fail on the WHERE/column text, which normalisation cannot supply). C-leg only. |

## 6a. P1c — REACH TABLE (every instrument r3 introduces, modifies, or leans on)
Axes: **reach** DERIVED vs hand-list · **coverage** a checked variable (fails closed) · **effect** vs proxy · **one source** proven by MUTATION. Leg: **E** = empirical (a wrong build in scratch + kill-pin pair), **C** = construction-inspection.

| instrument | reach | coverage checked? | effect / proxy | one source by mutation | verdict · leg |
|---|---|---|---|---|---|
| `governed_populations(*, emitted_ddl=)` — node leg (full trio over `DEFINE FIELD … ON <t>`) | DERIVED: the corpus is every `generate_*_ddl` (by inspection); the trio names derived from `_governed_field_specs()` | yes — exact five-set (equality); growth pins; partial-trio pinned both ways | effect (emitted ARTIFACT text) | trio names read from the ONE emitter | **SAFE · E** (R1 grow KILLED; N4/N4ctl/N4h KILLED). Node-leg regex drift fails OPEN for a NEW table but the exact five-set reds it for every known one (C). |
| — relation leg (`relation_endpoints`, IN/OUT parsed) | DERIVED from emitted `TYPE RELATION` statements | yes — FAILS CLOSED on an unparseable statement (pinned) + anti-vacuity (≥ 1 relation) | effect | the one parser `_DEFINE_RELATION_RE` (extended, not copied) | **SAFE · E** (N4 keyword spelling KILLED — spelling no longer exists) |
| generator corpus `schema_ddl_generators` / `emit_schema_ddl` / `emitted_schema_ddl` | DERIVED by the naming contract + `isfunction` (stated bound) | anti-vacuity (≥ 10); fail-closed on unsuppliable params (pinned); a misnamed generator is caught by #124's constant-coverage ∀ pin | effect | ONE home, three consumers — the author's GD1/GD2; my R1 red a THIRD consumer (`principal_keys` cascade) → sharing observed | **SAFE · E** (R2 misnamed KILLED by #124; R4 dim KILLED) |
| FORK-A pin-the-miss (`…gap_is_EXACTLY_lease_and_floor_calibration`) | the gap SET is derived (composition-aware) | yes — reds on GROW (R1) and CLOSE (R3) | **PROXY for the claim it carries**: the pin observes the unswept SET; its docstring's load-bearing premise ("neither emits a relation — not a live hole") is unobserved | n/a | set: **SAFE · E** (R1, R3). Premise: **R5 — §4.3** |
| relation-inventory ↔ population cross-check | `KNOWN_RELATION_EDGES` (hand-list, pre-existing) ∩ derived nodes | anti-vacuity (≥ 1 touching edge) | effect | n/a | **SAFE · E** (N4h: the inventory row + population now agree; the five-set reds the new member) |
| `patch_shared_object_everywhere` (identity alone, `expect_in`) + `module_level_bindings_of` (the ONE finder) | DERIVED: every module-level binding that `is` the object, over `sys.modules` | yes — `expect_in` RAISES if the home was not patched (the #194 landing check) | effect (every calling pin observes behaviour move) | ONE finder shared with `_rebind_everywhere` — author IM3; my IM3n §4.3 | **SAFE · E** (X4 alias GREEN, X5/X5b KILLED); bound (module namespaces only) stated + re-open trigger |
| decision-mutation pin `…SHARED_is_legal_identifier[{field}-{consumer}]` | **HAND-LIST of 4 consumer ENTRY POINTS** (`_IDENTIFIER_DECISION_CONSUMERS`) | no — a production call site that decides outside those entry points is unobserved | effect (each consumer's refusal/skip observed) | proves sharing for the 4 entry points only | **MISSING PIN — MP-1 · E.** X1 (the SKIP gate `_comms_traffic_line` bypasses the home with a private drifted regex) → **2807 passed / 0 failed**; KP-X1 kills it. |
| AST allowlist scan (`_pattern_decision_sites`) | DERIVED: every production member via `parse_production_trees` + `assert_scan_reached_every_member` | yes — anti-vacuity (≥ 1 `.pattern` prose read), 7 positive / 5 negative synthetic controls | structural (a static PROXY for "decides") — by design; the mutation pin is its effect twin | n/a | **SAFE for its stated threat model · E** (N1/N1b KILLED). Stated blind spots, measured: a private regex (N1c/X1) and a `.pattern`-text decision (X6) — the allowlist is keyed on the ATTRIBUTE, not its use, so `re.fullmatch(AGENT_NAME_PATTERN.pattern, v)` passes it; at the home X6 is killed by the mutation pin, at a non-listed call site it is MP-1's door. |
| FORK-C conditional guard pin (`test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists`) | one SPELLING: an `ExceptHandler` whose type (or tuple member) is the NAME `ImportError` | anti-vacuity at HEAD (the scan must see today's guard) | **PROXY: source text.** The property is "no silent skip of the identity leg once the predicate exists"; `except Exception`, a bare `except:`, `builtins.ImportError`, or `getattr(lorerunes, …, None)` keep the skip and pass | n/a | **MISSING PIN — MP-3 · E.** X3 (`except Exception:` kept) → **2807 passed**; KP-X3 (effect: predicate made unimportable → a hostile fake register must not succeed) kills X3 AND X3b. |
| R-Q5-1 id-bound pin (reads `principals._REFUSAL_ID_SAMPLE_SIZE`) | derived (reads the constant) | yes — 3 populations incl. bound + 15 | effect (the served reason) | **NOT proven by mutation**: the pin never perturbs the constant, so a restated literal that agrees at birth is a second source nobody can see | **MISSING PIN — MP-2 · E.** X2 → **2807 passed**; KP-X2 (constant patched to 3, 18 traps → exactly 3 ids) kills it. |
| parity matrix (real vs fake) | 34 derived rows (shared corpus × fields + pairs + blank roles) | yes — absolute assertions on the two consistent pairs | effect (outcome class + stamps read back) | n/a | **SAFE for FIRST register · E** (N5, X9 KILLED). RE-register path: FX1 — §4.3 |
| NF-2 / MP-B / MP-F pins | shared `_HOSTILE_IDENTIFIERS` corpus × fields; both mixed pairs; α + legacy rows | yes | effect (`SELECT *` byte-identity) | n/a | **SAFE · E** (X7, N2, N10, X8 KILLED) |
| backfill shape normaliser `_statement_shape` | n/a | its own wrong-statement controls | effect on text | reuses `_normalise_statement` for equality | SAFE · C (+ author's R6) |
| `pending_contracts.yaml` / `pending_contract_gate.py` (relied on) | derived from the live mypy transcript | yes — self-destruct both directions | effect | n/a | **SAFE · E** (§7, both worlds) |
| `test_ddl_write_target_coverage_124` #124 constant-coverage pin (relied on — closes the generator-naming bound) | DERIVED both sides (`vars(surreal_schema)` constants; every `generate_*_ddl`) | positive control (planted constant) | effect | shares the corpus via FORK-B | **SAFE · E** (R2 KILLED by it). ⚠ its `_emit` docstring is now FALSE — MP-P1. |

### 4.3 Batch 2 (declared BEFORE the run from `collected3b.txt` — 2901 ids over the 22 files + `test_enforced_relations.py` + `test_derivation_source_unification.py`)
| build | instrument attacked | the door | tail | verdict |
|---|---|---|---|---|
| **R5** | FORK-A pin-the-miss premise | `_lease_statements` appends `_define_relation_table("holds", LEASE_TABLE, TASK_TABLE)` — an UN-ENFORCED relation inside an ALREADY-unswept emitter, over no governed table | **`2882 passed, 19 skipped`** over 24 files (incl. the ∀-ENFORCED and "EXACTLY the six known edges" inventory files) | **SURVIVES** (declared) → **MP-4**. KP-R5: ref `14 passed`; R5 `1 failed, 13 passed` (`test_KP_R5_the_pinned_unswept_emitters_emit_NO_relation`) |
| **FX1** | parity matrix (item 8) | the FAKE heals an unstamped row on RE-register (`scopes` + `owners` stamped when `scopes` is NONE) — N10's door, fake-side | **`2807 passed`** | **SURVIVES** (declared) → **MP-5**. KP-FX1: ref green; FX1 `1 failed, 12 passed` |
| IM3n | the ONE binding-finder (MP-G / D6) | `module_level_bindings_of` returns `[]` | `4 failed, 77 passed` (governance file, 81 ids) | KILLED exactly 4/4 — the 3 identity self-tests + `test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter` (reproduces the author's IM3 claim in narrow form; `test_the_callers_EXPECTATION_is_enforced…` correctly stays GREEN — it asserts a raise, which an empty finder also produces) |

## 6. MISSING PINS — each: the test that should exist · the defect it catches · the wrong build that passes · its receipt
All receipts measured 2026-09-24, lane `ref` (my reference `adv3-ref` + the build), tests at `39935f6`. "2807/0" = the 22 contract files at `-n 8`: **`2807 passed`**, 0 failed/errors (junit diff, §A.3). Kill-pins: `test_adv_r3_killpins.py` (§A.4), GREEN on `adv3-ref` and RED on exactly their build. My recommended class per pin uses amendment-4's vocabulary; **the sidecar rules**.

**MP-1 — the SKIP gate's CALL SITE is not a consumer leg (A4-bis's "NOT rewired" clause has no pin). Recommend GATING (one parametrize value).**
- *Test that should exist:* add a `traffic-line` consumer to `_IDENTIFIER_DECISION_CONSUMERS` probing `AppContext._comms_traffic_line` THROUGH its gate: BASELINE, a legal attribution (`fixer-b`) is looked up once; under the decision mutation (shared `is_legal_identifier` rejects it) it is looked up ZERO times — KP-X1's shape (a spy `agent_registry` counting `get_agent` calls). The same leg for the REFUSE policy's callers is already covered by the footer pin (pattern-object mutation); the SKIP side has no such caller-level pin.
- *Defect:* ROUTING IS NOT SHARING one call site up. The pin probes the decision HOME (`_is_comms_charset_legal`) and assumes both policies keep reading it; a gate that decides privately is invisible to the mutation pin (it never calls the home) and to the AST scan (a private regex never names `AGENT_NAME_PATTERN`). Divergent TODAY in X1: a dotted attribution (`fixer.b`) now passes the gate and costs a registry round trip — R8's "a value that cannot BE a name is never looked up" read budget broken for that class.
- *Wrong build that passes:* **X1** — `_comms_traffic_line`: `not AppContext._is_comms_charset_legal(attribution)` → `re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", attribution) is None` → **2807/0**. KP-X1 GREEN on ref, RED on X1.

**MP-2 — the id bound is READ but never PERTURBED: a restated literal that agrees at birth survives. Recommend GATING (the builder writes exactly this line).**
- *Test that should exist:* R-Q5-1 gains a mutation leg: `monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 3)`, seed 3 + 15 traps → the reason names the full count (18) and EXACTLY 3 ids (KP-X2's shape).
- *Defect:* amendment-4 MP-C's rider — *"a NAMED constant … no literal `[:10]`"* — is unpinned. A build defining `_REFUSAL_ID_SAMPLE_SIZE = 10` and slicing `[:10]` holds ONE policy in TWO sources; the next change to either diverges silently (ONE IMPLEMENTATION: prove sharing by MUTATION). The author's LIT10 build (literal 10 beside constant **3**) was caught only because its VALUES differed — the birth-identical twin is the realistic one.
- *Wrong build that passes:* **X2** — `owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]` → `owned_unscoped_ids[:10]` (constant still defined = 10) → **2807/0**. KP-X2 GREEN on ref, RED on X2.

**MP-3 — the FORK-C guard pin observes one SPELLING, not the effect. Recommend GATING-adjacent (it is the builder's one granted edit; replace or augment the pin before the build).**
- *Test that should exist:* an EFFECT pin — once `lorerunes.is_legal_identifier` exists, `monkeypatch.delattr(lorerunes, "is_legal_identifier")` and a HOSTILE fake register (`"fixer-b\n"`) must NOT succeed (any exception is fine; `fake.db.agents` stays empty) — KP-X3's shape. It subsumes the source-text pin (it also reds X3b, the ruled spelling).
- *Defect:* the rider's property is "the guard must not outlive its premise" — i.e. no silent skip of the identity leg. The AST pin checks only for an `except` naming `ImportError`; `except Exception:`, a bare `except:`, `except builtins.ImportError`, or a `getattr(lorerunes, "is_legal_identifier", None)` read all keep the silent skip and pass.
- *Wrong build that passes:* **X3** — the builder "deletes" the guard by widening it to `except Exception:` → **2807/0**. KP-X3 GREEN on ref, RED on X3 and on X3b.

**MP-4 — the FORK-A KNOWN BOUND's PREMISE is unpinned: a relation added inside an already-unswept emitter is a live hole with the pin green. Recommend NON-GATING (test substrate; lands before the cold audit).**
- *Test that should exist:* beside the exact-set pin, assert `relation_endpoints(emit_schema_ddl(g)) == {}` for each pinned unswept generator (KP-R5), with the same KNOWN-BOUND message and re-open trigger. (Equivalently: define "unswept" as "emits a relation the sweep cannot see" and pin THAT set to ∅.)
- *Defect:* the bound is justified in its own docstring as *"neither emits a relation today, so the reach is a hidden constant, not a live hole"*. The pin watches the SET of unswept emitters, which does not change when an already-unswept emitter gains a relation — so the ∀-ENFORCED pins (`test_enforced_relations.py`, which sweep only `ALL_DDL_GENERATORS`) never see the new edge, the "EXACTLY the six known edges" inventory never sees it, and the pin-the-miss stays green. The claim that makes the bound safe is exactly the claim nobody observes.
- *Wrong build that passes:* **R5** — `_lease_statements` appends an un-ENFORCED `holds(lease → task)` relation → **`2882 passed, 19 skipped`** over the 22 files + `test_enforced_relations.py` + `test_derivation_source_unification.py`. KP-R5 GREEN on ref, RED on R5.

**MP-5 — the parity matrix drives FIRST registers only; the fake's RE-register path is unmirrored. Recommend NON-GATING.**
- *Test that should exist:* parity rows on the RE-register path: (α register, then a credentialed re-register) and (consistent register, then each mixed pair) — compare outcome class + stamps, real vs fake (KP-FX1's shape).
- *Defect:* THE QUANTIFIER LAW on MP-E: "the fake mirrors the writer" is measured ∀ inputs but only on the CREATE door. A fake that heals an unstamped row on re-register (the N10 door that the REAL writer is now pinned against) would let every fake-driven test observe a scope the production writer never stamps.
- *Wrong build that passes:* **FX1** — the fake stamps `scopes`/`owners` on re-register when `scopes` is NONE → **2807/0**. KP-FX1 GREEN on ref, RED on FX1.

**MP-P1 — PROSE (the P8d natural-language class).** `loremaster/tests/test_ddl_write_target_coverage_124.py::_emit` docstring now reads *"passing ``dim`` only if it requires one"* — FALSE since amendment-5's rider: the delegate `emit_schema_ddl` passes `dim` WHENEVER present (and `test_emit_threads_dim_WHENEVER_present…` pins it). *Fix:* "whenever the generator has a ``dim`` parameter". No wrong build needed; read at `39935f6`.

### 2.1 Full suite ALONE, `-n 12`, on my reference (measured 2026-09-24 21:50:33–21:59:32 EDT)
- Lane `…/scratchpad/ref` reset to `adv3-ref` (0 dirty paths), provenance `…/scratchpad/ref/loremaster/loremaster/__init__.py`; 33 GB available at launch; no other lore pytest on the box (the only lore-matching process was the lead's report watcher, a shell loop).
- **`11405 passed, 62 skipped, 3 xfailed, 7 warnings in 536.93s (0:08:56)` — 0 failed, 0 errors, exit 0.** Identical to the author's §SAT count (11405/62/3) on an INDEPENDENTLY written reference; it includes the builder's one granted test-tree edit (the guard deletion) and holds AFTER the lint-demanded cleanups (ruff clean).

## 1. P7 — RED honesty, reproduced (measured 2026-09-24; production at HEAD `83050b9` = `39935f6`'s)
- **Instrument:** scratch `…/scratchpad/head` (`scratch_copy.sh`, provenance `…/scratchpad/head/loremaster/loremaster/__init__.py`). Run set `redset.txt` = my 22 contract files ∪ every test file importing `_comms_fakes` / `_enforced_relations_scaffold` / `_rebind_everywhere` / `patch_shared_object_everywhere` / `governed_populations` / `module_level_bindings_of` (awk-derived; **42 files**). Two runs, `-n 8`, one at a time, same production: tests at `39935f6` vs tests at `88205a4` (`git checkout 88205a4 -- loremaster/tests`, restored after; 0 tracked dirty paths). Diff by `red_diff.py` (§A.5). ⚠ The author's own r3b run set (`r3b_files.txt`, "22 files", 2576 collected) is NOT pasted in their report, so their §RED numbers cannot be re-run verbatim; I re-derived the set by property instead (R-2).
- **Tails:** r3 tests `170 failed, 3705 passed, 23 skipped, 51 errors`; r2 tests `97 failed, 3665 passed, 23 skipped, 51 errors`.
- **Diff:** **HEAD-green on r2 turned RED on r3: 0.** NEW red ids (absent on r2): **77** — `TestTheFakeRegistryMirrorsTheWriter63cIA` 34 · `TestAHostileNamedLegacyAgentCannotReRegisterButStillTouches63cIA` 26 · decision pin consumer legs + re-keyed blank `[register]` 9 · MP-B/MP-F 4 · R-Q5-1 ×3 populations 3 · AST allowlist 1. Red on both: 144. r2-red ids gone on r3: 4 — exactly the re-keyed ones (`test_R_Q5_1_…` unparametrised, `test_the_blank_role_rule_is_the_SHARED_is_blank`, `…SHARED_is_legal_identifier[name]`, `[session]`). red→green: 0. **Author's claim "every new red is a new pin; zero greens turned red" — CONFIRMED** (their 40 r3a + 36 r3b new ids + the re-keyed blank `[register]` = 77).
- **FORK-C's accommodation measured:** the 11 `_comms_fakes` consumer files are inside the run set; 0 of their HEAD-green tests turned red — the guard does what amendment-5 ruled.
- **Right reason, every new red (junit messages, shape-classified):** 38 × `TypeError … unexpected keyword argument 'session_keep_id'` (the whole parity matrix — the real side is called first — + MP-B/MP-F); 26 × the labelled `RED-at-HEAD (right reason): … refused by the STILL-PRESENT charset ASSERT` (NF-2); 11 × `AttributeError: module … has no attribute …` (`lorerunes.is_legal_identifier`, `principals._REFUSAL_ID_SAMPLE_SIZE`); 1 × blank `[register]` "behaviour did not move" (HEAD has no shared blank decision in `register`); 1 × the AST allowlist naming `server.py`'s `AGENT_NAME_PATTERN.fullmatch`. **No red for a wrong reason.** Note (prose, not a defect): the parity class docstring says the identity rows are also red "on the fake side" at HEAD — at HEAD they red on the REAL side first (the kwarg), so the fake-side reason is never reached; harmless.

## 8. Residuals (each with an individual verdict)
- **R-1 · author over-claim (P4):** §ITEMS row 8 and the `39935f6` commit message say the parity matrix has **36** rows; it collects **34** (`collected3.txt`: 4 pairs + 26 hostile + 4 blank). The author's own §RED says "parity matrix 34". · **Fix the count in the archived report/commit prose; no test impact.**
- **R-2 · lost instrument (brief-base §1):** the author's `r3b_files.txt` (the run set behind "146 failed, 2406 passed … over the same 22 files") is not pasted; the claim is un-rerunnable verbatim. My property-derived 42-file set reproduces the load-bearing half ("0 greens turned red"). · **Paste the list when archiving.**
- **R-3 · fork (spec-silent on the VALUE):** amendment-4 MP-C writes `_REFUSAL_ID_SAMPLE_SIZE = 10` in a parenthetical; the contract pins that a named constant is USED (after MP-2) but not its value, so `= 1000` passes (the author's C3 "pin follows" is this). Reading (a): the value is illustrative — any positive bound; reading (b): 10 is normative. **I would pick (a) plus an upper sanity bound (e.g. ≤ 20) so an operator-facing message stays bounded without restating the constant** — sidecar's call.
- **R-4 · stated blind spot, measured:** the AST allowlist is keyed on the ATTRIBUTE (`.pattern`), not its USE — `re.fullmatch(AGENT_NAME_PATTERN.pattern, v)` passes it (X6). At the home the mutation pin kills it (X6 KILLED); at a call site outside the consumer list it is MP-1's door. · **Covered once MP-1 lands; no separate pin needed.**
- **R-5 · DUAL prose gap:** D7 omits the retired resolver's virtue (c) (node membership keyed on `_governed_field_specs` CALLERS); it survives in per-table emitter-provenance pins (`test_governed_schema_63a.py`, `test_message_governed_ddl_63b_ii_a.py`, W1-1) — §3.1. · **OK; one sentence in D7 would make that visible.**
- **R-6 · node-leg format drift fails OPEN for a NEW table** (construction): a `DEFINE FIELD` spelling `_DEFINE_FIELD_ON_RE` misses would silently keep a new governed table out; the exact five-set reds it for every KNOWN table. · **Accepted-by-construction** (the text is our own `_define_field` output); re-open trigger = P-PKG row 2's.
- **R-7 · my mispredictions (declared sets, not re-declared):** X6 (+2 refuse-policy legs — the refuse policy reads the home), R1 (+1 `principal_keys` cascade pin — a third consumer of the shared corpus), R2 (declared survive; killed by #124). All in the SAFE direction (more reds than declared), none changes a verdict.
- **R-8 · my instrument quirk:** `test_adv_r3_killpins.py` imports `TestAgentMigrateScopeKeyed63cIA` for its `_seed_clean_legacy`, so pytest also collects that class (9 extra tests in every kill-pin run). The pair logic is unaffected (each build reddens only its own KP). · **Noted.**
- **R-9 · parity-class docstring:** see §1 last note. · **Prose, harmless.**
- **R-10 · MP-P1** (coverage_124 `_emit` docstring false after the rider) — §6.
- **R-11 · lore friction:** none hit this run (lore MCP reachable throughout; register/heartbeat/drain all succeeded). grep/rg hook-blocked (#473, pre-existing) — awk used everywhere, said in §0.

## A. Instruments (pasted VERBATIM — scratch-only; my writable set is this report)
Scratch root for every path: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad`. Lanes `ref`, `head`, `built` were each made by `./scripts/scratch_copy.sh` (provenance asserted by the tool and re-printed by each driver). `files.txt` = `git diff --name-only 0b8ce37 39935f6 -- 'loremaster/tests/test_*.py'` + `loremaster/tests/test_comms_wiring.py` (22 files); `redset.txt` = that ∪ the awk-derived consumer files (42).

### A.1 `my_ref_build.py`
```python
"""adversary-63c-i-a-r2 — an INDEPENDENT reference (believed-correct) 63c-i-a build.

Written from the production source + amendment-2 §A1–A4, NOT from the r2 author's ref_build_r2.py.
Base legs (Q3 drop, W1-1 routing, Q5 scope-keyed migrate + row precondition) re-use the PRIOR
adversary's §A.1 anchors (b46d3f2 — a different author than the contract under grade); the A2/A3/A4
legs are my own.

Usage: uv run --no-project python my_ref_build.py <scratch-root>
Each edit asserts its anchor occurs exactly once (a silent no-op edit is a failed setup — #194).
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


def create(rel: str, body: str) -> None:
    path = ROOT / rel
    assert not path.exists(), f"{rel} already exists"
    path.write_text(body)


SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
AGENTS = "loremaster/loremaster/agents.py"
SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
RUNES_INIT = "lorerunes/lorerunes/__init__.py"

# ---- Q3: drop name/session/role ASSERTs (KEEP status) -------------------------------------------
edit(
    SCHEMA,
    '    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("session", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),\n    ("model"',
    '    ("name", _CHUNK_STRING_TYPE, ""),\n'
    '    ("session", _CHUNK_STRING_TYPE, ""),\n'
    '    ("role", _CHUNK_STRING_TYPE, ""),\n    ("model"',
)
# ---- W1-1: the governed triple comes only from the ONE emitter ----------------------------------
edit(SCHEMA, '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1', "    # packet 62, Fork 1")
edit(
    SCHEMA,
    "    statements.append(\n"
    "        _plain_index(\n"
    "            AGENT_TABLE,\n"
    '            f"{AGENT_TABLE}_owner_principal",\n'
    "            _AGENT_OWNER_PRINCIPAL_INDEX_FIELDS,\n"
    "        )\n"
    "    )\n",
    "    statements += [\n"
    "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
    "        for name, type_expr, constraint in _governed_field_specs()\n"
    "    ]\n"
    "    statements += _governed_index_statements(AGENT_TABLE)\n",
)
edit(SCHEMA, '_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS = ("owner_principal",)\n', "")

# ---- A4: the identifier DECISION + the pattern MOVE to lorerunes ---------------------------------
create(
    "lorerunes/lorerunes/identifiers.py",
    '"""The comms identity charset — ONE pattern, ONE decision (63c-i-a amendment-2 A4)."""\n\n'
    "from __future__ import annotations\n\n"
    "import re\n\n"
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n\n\n'
    "def is_legal_identifier(value: str) -> bool:\n"
    '    """Whether ``value`` matches ``AGENT_NAME_PATTERN`` IN FULL (``fullmatch``, finding #210)."""\n'
    "    return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
)
edit(
    RUNES_INIT,
    "from lorerunes.engine_rejection import reclassify\n",
    "from lorerunes.engine_rejection import reclassify\n"
    "from lorerunes.identifiers import AGENT_NAME_PATTERN, is_legal_identifier\n",
)
edit(RUNES_INIT, "__all__ = [\n", '__all__ = [\n    "AGENT_NAME_PATTERN",\n    "is_legal_identifier",\n')
edit(
    AGENTS,
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n',
    "AGENT_NAME_PATTERN = _RUNES_AGENT_NAME_PATTERN  # re-export (A4: the pattern lives in lorerunes)\n",
)
edit(
    AGENTS,
    "from lorerunes import parse_credential\n",
    "from lorerunes import AGENT_NAME_PATTERN as _RUNES_AGENT_NAME_PATTERN\n"
    "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
)
edit(AGENTS, "from loremaster.render import render_attributed\n", "from loremaster.render import render_attributed, render_fenced\n")
edit(
    SERVER,
    "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
    "        return is_legal_identifier(value)\n",
)

# ---- A4 register MOVE (teaching) + A3 XOR + A2 stamp --------------------------------------------
edit(
    AGENTS,
    "class AgentIdentityConflictError(AgentRegistryError):",
    "class InvalidAgentIdentityError(AgentRegistryError):\n"
    '    """A register argument violates the agent identity rules (63c-i-a §4.2 MOVE)."""\n\n\n'
    "class AgentIdentityConflictError(AgentRegistryError):",
)
edit(
    AGENTS,
    "        owner_principal_id: str | None = None,\n    ) -> AgentRegisterResult:",
    "        owner_principal_id: str | None = None,\n        session_keep_id: str | None = None,\n    ) -> AgentRegisterResult:",
)
edit(
    AGENTS,
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
    '        for field_name, value in (("name", name), ("session", session)):\n'
    "            if not is_legal_identifier(value):\n"
    "                raise InvalidAgentIdentityError(\n"
    '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase letters, "\n'
    "                    f\"digits, '_' or '-', 1-64 chars, starting with a letter or digit); nothing was \"\n"
    '                    f"written — register again with a legal {field_name}. The rejected value was:\\n"\n'
    '                    f"{render_fenced(value)}"\n'
    "                )\n"
    "        if is_blank(role):\n"
    "            raise InvalidAgentIdentityError(\n"
    '                "agent role must not be blank — nothing was written; register again with a role "\n'
    "                \"(e.g. 'builder')\"\n"
    "            )\n"
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
)
edit(
    AGENTS,
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n",
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n"
    '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n'
    '                "scope": keep_scope(session_keep_id) if session_keep_id is not None else None,\n',
)
edit(
    SERVER,
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n        )\n        now = datetime.now(UTC)\n        registered_age_s",
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n"
    "            session_keep_id=(\n"
    '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n'
    "            ),\n"
    "        )\n        now = datetime.now(UTC)\n        registered_age_s",
)

# ---- Q5: scope-keyed 3-column migrate + §2.1 row precondition (prior adversary §A.1 anchors) ------
edit(
    PRINCIPALS,
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, principal_store)\n",
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, keep_store, principal_store)\n",
)
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
)
edit(
    PRINCIPALS,
    "    from loremaster.governed import MigrateGovernedResult, governed_exempt\n\n    operator = await resolve_operator_principal(principal_store)\n",
    "    from lorerunes.pdp import keep_scope\n\n"
    "    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt\n\n"
    "    operator = await resolve_operator_principal(principal_store)\n",
)
edit(
    PRINCIPALS,
    "    unmigrated = await _owner_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _owner_count(store, AGENT_TABLE, none=False)\n",
    "    unmigrated = await _scope_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _scope_count(store, AGENT_TABLE, none=False)\n",
)
edit(
    PRINCIPALS,
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) \"\n"
    "        \"WHERE owner_principal IS NONE\"\n"
    "    )\n",
    "    owned_unscoped = await run_query(\n"
    "        acquire=store.acquire,\n"
    "        drop=store.drop,\n"
    "        url=store.url,\n"
    "        noun=\"governed agent row precondition\",\n"
    "        label=\"governed.agent_precondition.rejected\",\n"
    "        statement=(\n"
    "            f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"\n"
    "        ),\n"
    "        params={},\n"
    "        logger=logger,\n"
    "    )\n"
    "    owned_unscoped_ids = [str(row) for row in (owned_unscoped or [])]\n"
    "    if owned_unscoped_ids:\n"
    "        return MigrateGovernedResult(\n"
    "            table=AGENT_TABLE,\n"
    "            scanned=unmigrated + already,\n"
    "            backfilled=0,\n"
    "            already_migrated=already,\n"
    "            refused=True,\n"
    "            reason=(\n"
    "                f\"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope \"\n"
    "                f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal or half-applied store; \"\n"
    "                \"adjudicate these rows by hand before migrating (§2.1)\"\n"
    "            ),\n"
    "        )\n"
    "    project_keep = await keep_store.get_or_create_keyed(\n"
    "        key=PROJECT_KEEP_KEY, type=\"project\", keeper_email=operator.email, name=\"lore\"\n"
    "    )\n"
    "    project_scope = keep_scope(project_keep.id.partition(\":\")[2] or project_keep.id)\n"
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner), \"\n"
    "        \"owner_agent = id, scope = $scope WHERE scope IS NONE\"\n"
    "    )\n",
)
edit(
    PRINCIPALS,
    "            statement=backfill_statement,\n            params={\"owner\": operator_id},\n",
    "            statement=backfill_statement,\n            params={\"owner\": operator_id, \"scope\": project_scope},\n",
)

# ---- r3 (amendment-4 MP-C): the refusal's id bound is a NAMED module constant, USED by the slice ----
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n",
    "#: The refusal names at most this many offending row ids (ruling §6 'ids, bounded'; amendment-4 MP-C).\n"
    "_REFUSAL_ID_SAMPLE_SIZE = 10\n\n\n"
    "async def _migrate_agent_owner(\n",
)
edit(
    PRINCIPALS,
    "owned_unscoped_ids[:10]",
    "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]",
)
# ---- r3 (amendment-5 FORK-C rider 3): the builder's ONE granted test-tree edit — delete the guard --
FAKES = "loremaster/tests/_comms_fakes.py"
edit(
    FAKES,
    "        try:\n"
    "            from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n"
    "        except ImportError:  # HEAD-RED accommodation — delete once the build lands the predicate\n"
    "            return None\n"
    "        return is_legal_identifier\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n",
)
print("adversary-r3 reference build applied (r2 legs + MP-C constant + FORK-C guard deletion)")
# ---- lint-demanded cleanups (the SAT receipt must hold AFTER them) ---------------------------------
edit(AGENTS, "import logging\nimport re\nimport secrets\n", "import logging\nimport secrets\n")
edit(
    PRINCIPALS,
    "                f\"({', '.join(owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE])}) — a multi-principal or half-applied store; \"\n",
    "                f\"({', '.join(owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE])}) — a multi-principal or \"\n"
    "                \"half-applied store; \"\n",
)
print("lint cleanups applied")
```

### A.2 `my_wbs3.py`
```python
"""adversary-63c-i-a-r3 — wrong builds applied ON TOP of my independent reference (adv3-ref).

Usage: uv run --no-project python my_wbs3.py <scratch-root> <WB-id> [--declared]
  --declared   print the DECLARED expected-RED node ids (resolved against collected3.txt — the
               `pytest --collect-only -q` output of the 22 contract files, taken BEFORE any wrong-build
               run) and exit.
Each edit asserts its anchor occurs exactly once (a no-op mutation is a failed setup — #194).
A DECLARED set of [] means my prediction is that the build SURVIVES (or, for X4, that it is CORRECT).
"""

import sys
from pathlib import Path

SCR = Path("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad")
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
FAKES = "loremaster/tests/_comms_fakes.py"
SCAFFOLD = "loremaster/tests/_enforced_relations_scaffold.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
ENF = "test_message_enforcement_63b_ii_a.py"

# DECLARED expected-RED sets — (file fragment, [node fragments ALL required]). Written BEFORE any run.
SHARED_DECISION = "test_the_identifier_decision_is_the_SHARED_is_legal_identifier"
DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # --- the prior pass's 7 survivors (+ N1b, N4ctl controls) ---
    "N1": [(REG, [SHARED_DECISION, "skip-policy"]),
           (REG, ["test_no_production_module_outside_lorerunes_DECIDES_with_the_pattern"])],
    "N1b": [(REG, [SHARED_DECISION, "skip-policy"]),
            (REG, ["test_no_production_module_outside_lorerunes_DECIDES_with_the_pattern"])],
    "N1c": [(REG, [SHARED_DECISION, "skip-policy"])],
    "N2": [(GOV, ["test_an_inconsistent_provenance_pair_is_refused_on_the_RE_REGISTER_path_too"])],
    "N3": [(GOV, ["test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent", "above-cap"])],
    "N4": [(ENF, ["test_the_derived_population_set_grows_to_memory_message_to"])],
    "N4ctl": [(ENF, ["test_the_derived_population_set_grows_to_memory_message_to"])],
    "N4h": [(ENF, ["test_the_derived_population_set_grows_to_memory_message_to"])],
    "N5": [(REG, ["test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps", "pair-both-set"]),
           (REG, ["test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps", "pair-alpha-none"])],
    "N10": [(GOV, ["test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row"])],
    # --- new wrong builds against r3's instruments ---
    "X1": [],   # SKIP gate (_comms_traffic_line) bypasses the home with a private DRIFTED regex
    "X2": [],   # MP-C: the named constant exists but the slice restates the literal 10 (two sources)
    "X3": [],   # FORK-C: the fake's guard is KEPT post-build, widened to `except Exception`
    "X3b": [(REG, ["test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists"])],  # control
    "X4": [],   # CORRECT build: agents binds keep_scope + is_legal_identifier + is_blank under ALIASES
    "X5": [(GOV, ["test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter"])],  # private same-NAMED copy
    "X5b": [(GOV, ["test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter"])],  # private copy, other name
    "X6": [(REG, [SHARED_DECISION, "skip-policy"])],  # home decides with re.fullmatch(PATTERN.pattern, v)
    "X7": [(GOV, ["test_a_hostile_legacy_row_is_refused_on_re_register_and_still_touches"])],  # NF-2 create-only
    "X8": [(GOV, ["test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row"])],
    "X9": [(REG, ["test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps", "pair-alpha-none"])],
    "R1": [(ENF, ["test_the_derived_population_set_grows_to_memory_message_to"]),
           (ENF, ["test_KNOWN_BOUND_the_ALL_DDL_GENERATORS_hand_list_gap_is_EXACTLY_lease_and_floor_calibration"])],
    "R2": [],   # the same governed slice from a generator NOT named generate_*_ddl
    "R3": [(ENF, ["test_KNOWN_BOUND_the_ALL_DDL_GENERATORS_hand_list_gap_is_EXACTLY_lease_and_floor_calibration"])],
    "R4": [(ENF, ["test_emit_threads_dim_WHENEVER_present_and_fails_closed_on_any_other_required_parameter"])],
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


def append(rel: str, text: str) -> None:
    path = ROOT / rel
    path.write_text(path.read_text() + text)


if "--declared" in sys.argv:
    collected = (SCR / "collected3.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

XOR = (
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
)
IDENTITY_CHECK = (
    '        for field_name, value in (("name", name), ("session", session)):\n'
    "            if not is_legal_identifier(value):\n"
    "                raise InvalidAgentIdentityError(\n"
    '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase letters, "\n'
    "                    f\"digits, '_' or '-', 1-64 chars, starting with a letter or digit); nothing was \"\n"
    '                    f"written — register again with a legal {field_name}. The rejected value was:\\n"\n'
    '                    f"{render_fenced(value)}"\n'
    "                )\n"
)
HOME_REF = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
    "        return is_legal_identifier(value)\n"
)
REFUSE_ROUTE = "        if not AppContext._is_comms_charset_legal(value):\n            raise ValueError(\n"
REFUSE_DIRECT = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415\n\n"
    "        if not is_legal_identifier(value):\n            raise ValueError(\n"
)
GUARD_DELETED = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n"
)
WIDGET_SLICE = (
    '\n\nWIDGET_TABLE = "widget"\n\n\n'
    "def {name}() -> str:\n"
    '    """adversary-r3: a NEW governed slice (the full trio through the ONE emitter)."""\n'
    "    statements = [_define_table(WIDGET_TABLE)]\n"
    "    statements += [\n"
    "        _define_field(WIDGET_TABLE, name, type_expr, constraint=constraint)\n"
    "        for name, type_expr, constraint in _governed_field_specs()\n"
    "    ]\n"
    '    return ";\\n".join(statements) + ";\\n"\n'
)

if WB == "N1":
    edit(SERVER, REFUSE_ROUTE, REFUSE_DIRECT)
    edit(SERVER, HOME_REF, "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n")
elif WB == "N1b":
    edit(SERVER, REFUSE_ROUTE, REFUSE_DIRECT)
    edit(SERVER, HOME_REF, "        return AGENT_NAME_PATTERN.match(value) is not None\n")
elif WB == "N1c":
    edit(SERVER, REFUSE_ROUTE, REFUSE_DIRECT)
    edit(SERVER, HOME_REF, '        return re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", value) is not None\n')
elif WB == "N2":
    edit(AGENTS, XOR, "")
    edit(AGENTS, "        if existing_row is None:\n            # packet 62 W2.3",
         "        if existing_row is None:\n"
         + "\n".join(("    " + line) if line else line for line in XOR.split("\n"))
         + "            # packet 62 W2.3")
elif WB == "N3":
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids")
elif WB in ("N4", "N4ctl", "N4h"):
    call = {
        "N4": "_define_relation_table(OWNS_RELATION, in_table=AGENT_TABLE, out_table=MEMORY_TABLE)",
        "N4ctl": "_define_relation_table(OWNS_RELATION, AGENT_TABLE, MEMORY_TABLE)",
        "N4h": "_define_relation_table(OWNS_RELATION, in_table=AGENT_TABLE, out_table=MEMORY_TABLE, enforced=True)",
    }[WB]
    edit(SCHEMA, 'BRIEFED_RELATION = "briefed"\n', 'BRIEFED_RELATION = "briefed"\nOWNS_RELATION = "owns"\n')
    edit(SCHEMA,
         "    statements: list[str] = [\n"
         "        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)\n"
         "    ]\n",
         "    statements: list[str] = [\n"
         "        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)\n"
         "    ]\n"
         f"    statements.append({call})\n")
    if WB == "N4h":
        edit(SCAFFOLD, "    MEMBER_OF_RELATION: (PRINCIPAL_TABLE, KEEP_TABLE),\n}\n",
             '    MEMBER_OF_RELATION: (PRINCIPAL_TABLE, KEEP_TABLE),\n    "owns": (AGENT_TABLE, "memory"),\n}\n')
elif WB == "N5":
    edit(FAKES, "            self.db.owner_agents[agent_id] = agent_id\n",
         "            self.db.owner_agents[agent_id] = 'WRONG'\n")
    edit(FAKES, "            self.db.scopes[agent_id] = keep_scope(session_keep_id) if session_keep_id is not None else None\n",
         "            self.db.scopes[agent_id] = 'keep:WRONG'\n")
elif WB == "N10":
    edit(AGENTS, "        new_model = model if model is not None else existing.model\n",
         "        if existing_row.get(\"scope\") is None and session_keep_id is not None:\n"
         "            await self._query(\n"
         "                f\"UPDATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) SET scope = $heal_scope, \"\n"
         "                f\"owner_agent = type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM})\",\n"
         "                {_ROW_ID_PARAM: agent_id, \"heal_scope\": keep_scope(session_keep_id)},\n"
         "            )\n"
         "        new_model = model if model is not None else existing.model\n")
elif WB == "X1":
    # The SKIP gate stops reading the decision HOME and decides with a private DRIFTED regex (admits '.').
    edit(SERVER,
         "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n",
         "        if attribution is None or re.fullmatch(r\"[a-z0-9][a-z0-9_.-]{0,63}\", attribution) is None:\n")
elif WB == "X2":
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids[:10]")
elif WB == "X3":
    edit(FAKES, GUARD_DELETED,
         "        try:\n"
         "            from lorerunes import is_legal_identifier  # noqa: PLC0415\n"
         "        except Exception:  # noqa: BLE001\n"
         "            return None\n"
         "        return is_legal_identifier\n")
elif WB == "X3b":
    edit(FAKES, GUARD_DELETED,
         "        try:\n"
         "            from lorerunes import is_legal_identifier  # noqa: PLC0415\n"
         "        except ImportError:\n"
         "            return None\n"
         "        return is_legal_identifier\n")
elif WB == "X4":
    # A CORRECT build: the three shared objects bound under ALIASES in agents.py (ordinary hygiene).
    edit(AGENTS, "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
         "from lorerunes import is_blank as _is_blank\n"
         "from lorerunes import is_legal_identifier as _is_legal_identifier\n"
         "from lorerunes import keep_scope as _format_keep_scope\n"
         "from lorerunes import parse_credential\n")
    edit(AGENTS, "            if not is_legal_identifier(value):\n", "            if not _is_legal_identifier(value):\n")
    edit(AGENTS, "        if is_blank(role):\n", "        if _is_blank(role):\n")
    edit(AGENTS, '"scope": keep_scope(session_keep_id) if', '"scope": _format_keep_scope(session_keep_id) if')
elif WB == "X5":
    append(AGENTS, '\n\ndef keep_scope(keep_id: str) -> str:\n    """adversary: a PRIVATE copy wearing the SHARED name."""\n    return f"keep:{keep_id}"\n')
    edit(AGENTS, "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
         "from lorerunes import is_blank, is_legal_identifier, parse_credential\n")
elif WB == "X5b":
    append(AGENTS, '\n\ndef _private_scope(keep_id: str) -> str:\n    """adversary: a PRIVATE copy under another name."""\n    return f"keep:{keep_id}"\n')
    edit(AGENTS, '"scope": keep_scope(session_keep_id) if', '"scope": _private_scope(session_keep_id) if')
elif WB == "X6":
    # The home decides by re-running the pattern TEXT (a `.pattern` prose read — the AST scan's safe shape).
    edit(SERVER, HOME_REF, "        return re.fullmatch(AGENT_NAME_PATTERN.pattern, value) is not None\n")
elif WB == "X7":
    # NF-2 door: the identity MOVE only on the CREATE path (a hostile legacy row re-registers).
    edit(AGENTS, IDENTITY_CHECK, "")
    edit(AGENTS, "        if existing_row is None:\n            # packet 62 W2.3",
         "        if existing_row is None:\n"
         + "\n".join(("    " + line) if line else line for line in IDENTITY_CHECK.split("\n"))
         + "            # packet 62 W2.3")
elif WB == "X8":
    # MP-F takeover door: a credentialed re-register heals ALL THREE columns of an unstamped row.
    edit(AGENTS, "        new_model = model if model is not None else existing.model\n",
         "        if existing_row.get(\"scope\") is None and session_keep_id is not None:\n"
         "            await self._query(\n"
         "                f\"UPDATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) SET scope = $heal_scope, \"\n"
         "                f\"owner_agent = type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}), \"\n"
         "                f\"owner_principal = type::record('principal', $heal_owner)\",\n"
         "                {_ROW_ID_PARAM: agent_id, \"heal_scope\": keep_scope(session_keep_id),\n"
         "                 \"heal_owner\": owner_principal_id},\n"
         "            )\n"
         "        new_model = model if model is not None else existing.model\n")
elif WB == "X9":
    # The real α CREATE stamps owner_agent only when an owner is present (ruling §2.2 says: always self).
    edit(AGENTS, '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n',
         '                "owner_agent": RecordID(AGENT_TABLE, agent_id) if owner_principal_id is not None else None,\n')
elif WB == "R1":
    append(SCHEMA, WIDGET_SLICE.format(name="generate_widget_ddl"))
elif WB == "R2":
    append(SCHEMA, WIDGET_SLICE.format(name="build_widget_ddl"))
elif WB == "R3":
    edit(SCAFFOLD, '    "generate_keep_ddl": generate_keep_ddl,\n}\n',
         '    "generate_keep_ddl": generate_keep_ddl,\n'
         '    "generate_lease_ddl": __import__("loremaster.store.surreal_schema", fromlist=["x"]).generate_lease_ddl,\n'
         '    "generate_floor_calibration_ddl": __import__("loremaster.store.surreal_schema", fromlist=["x"]).generate_floor_calibration_ddl,\n'
         "}\n")
elif WB == "R4":
    # Revert the amendment-5 FORK-B rider: pass dim only when REQUIRED (the r3b-draft narrowing).
    edit(SCAFFOLD,
         '        if parameter.name == "dim":\n            kwargs["dim"] = dim\n            continue\n',
         '        if parameter.name == "dim" and parameter.default is inspect.Parameter.empty:\n'
         '            kwargs["dim"] = dim\n            continue\n')
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### A.3 `my_wbs3b.py`
```python
"""adversary-63c-i-a-r3 — BATCH 2 wrong builds (on top of adv3-ref). Same contract as my_wbs3.py.

Usage: uv run --no-project python my_wbs3b.py <scratch-root> <WB-id> [--declared]
Declared sets resolved from collected3b.txt (collect-only over files3b.txt, taken BEFORE any batch-2 run).
"""

import sys
from pathlib import Path

SCR = Path("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad")
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
LOGFIX = "loremaster/tests/_logging_fixtures.py"
GOV = "test_agent_governance_63c_i_a.py"

DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # R5: an un-ENFORCED relation inside an ALREADY-unswept emitter (lease), over no governed table.
    # Prediction: SURVIVES the 22 contract files AND the enforced-relation inventory files.
    "R5": [],
    # IM3n: THE one binding-finder finds nothing -> both instruments' consumers must red (narrow reproduction
    # of the author's IM3 over the MP-G self-tests only: every self-test that patches THE object raises via
    # expect_in or sees nothing moved).
    # FX1: the FAKE heals an unstamped row on RE-register (N10's door, in the fake). Prediction: SURVIVES —
    # the parity matrix drives FIRST registers only.
    "FX1": [],
    "IM3n": [
        (GOV, ["TestThePatchSharedObjectInstrument63cIA", "test_an_ALIASED_binding_of_the_shared_object_MOVES"]),
        (GOV, ["TestThePatchSharedObjectInstrument63cIA", "test_a_private_copy_under_ANOTHER_name_does_NOT_move"]),
        (GOV, ["TestThePatchSharedObjectInstrument63cIA", "test_a_private_copy_WEARING_THE_SHARED_NAME_does_NOT_move"]),
        (GOV, ["TestTheRegistryProvenanceSeam63cIA", "test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter"]),
    ],
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (SCR / "collected3b.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

if WB == "R5":
    edit(SCHEMA,
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n    return statements\n",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n"
         "    statements.append(_define_relation_table(\"holds\", LEASE_TABLE, TASK_TABLE))\n"
         "    return statements\n")
elif WB == "IM3n":
    edit(LOGFIX,
         "    bindings: list[tuple[str, Any, str]] = []\n    for module_name, module in list(sys.modules.items()):\n",
         "    bindings: list[tuple[str, Any, str]] = []\n    return bindings\n"
         "    for module_name, module in list(sys.modules.items()):\n")
elif WB == "FX1":
    edit("loremaster/tests/_comms_fakes.py",
         "        # status resets to active unconditionally (retired already excluded above).\n",
         "        if self.db.scopes.get(agent_id) is None and session_keep_id is not None:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n"
         "        # status resets to active unconditionally (retired already excluded above).\n")
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### A.4 `run_lane3.sh`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r3 lane driver: for each WB, reset LANE to adv3-ref, resolve the DECLARED expected-RED
# set from collected3.txt (collect-only, taken BEFORE any wrong-build run), apply the build, run the 22
# contract files (-n 8, one pytest session at a time), diff observed vs declared BOTH ways, restore.
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad
LANE=$1; shift
cd "$S/$LANE"
echo "[$LANE] provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
for WB in "$@"; do
  git checkout -q -f adv3-ref && git clean -qfd -e REPORT-sidecar-63c.md
  uv run --no-project python "$S/my_wbs3.py" "$S/$LANE" "$WB" --declared > "$S/decl3_$WB.txt" || { echo "$WB: DECLARE FAILED"; continue; }
  uv run --no-project python "$S/my_wbs3.py" "$S/$LANE" "$WB" || { echo "$WB: APPLY FAILED"; continue; }
  echo "== $WB landed: $(git diff --shortstat)"
  timeout 2400 uv run pytest -n 8 -q -p no:cacheprovider --tb=short --junitxml="$S/wb3_$WB.xml" $(cat $S/files.txt) > "$S/wb3_$WB.log" 2>&1
  echo "== $WB tail: $(tail -n 1 $S/wb3_$WB.log)"
  uv run --no-project python - "$WB" <<'PY'
import sys, xml.etree.ElementTree as ET
S="/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad"
wb=sys.argv[1]
declared=set(open(f"{S}/decl3_{wb}.txt").read().split("\n"))-{""}
def nid(tc):
    cn=tc.get("classname"); parts=cn.split(".")
    mod_idx=next(i for i,p in enumerate(parts) if p.startswith("test_"))
    path="/".join(parts[:mod_idx+1])+".py"; rest="::".join(parts[mod_idx+1:])
    return f"{path}::{rest}::{tc.get('name')}" if rest else f"{path}::{tc.get('name')}"
root=ET.parse(f"{S}/wb3_{wb}.xml").getroot()
total=sum(1 for _ in root.iter("testcase"))
observed={nid(tc) for tc in root.iter("testcase") if tc.find("failure") is not None or tc.find("error") is not None}
unexpected=sorted(observed-declared); still_green=sorted(declared-observed)
verdict = "SURVIVES (0 red)" if not observed else ("KILLED — declared set fired EXACTLY" if not unexpected and not still_green else "KILLED (set differs from declaration)")
print(f"== {wb} VERDICT: {verdict}; observed={len(observed)} declared={len(declared)} testcases={total}")
for n in unexpected: print(f"   UNEXPECTED-RED {n}")
for n in still_green: print(f"   DECLARED-STILL-GREEN {n}")
PY
done
git checkout -q -f adv3-ref && git clean -qfd -e REPORT-sidecar-63c.md
```

### A.5 `run_lane3b.sh`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r3 lane driver: for each WB, reset LANE to adv3-ref, resolve the DECLARED expected-RED
# set from collected3.txt (collect-only, taken BEFORE any wrong-build run), apply the build, run the 22
# contract files (-n 8, one pytest session at a time), diff observed vs declared BOTH ways, restore.
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad
LANE=$1; FILES=$2; shift 2
cd "$S/$LANE"
echo "[$LANE] provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
for WB in "$@"; do
  git checkout -q -f adv3-ref && git clean -qfd -e REPORT-sidecar-63c.md
  uv run --no-project python "$S/my_wbs3b.py" "$S/$LANE" "$WB" --declared > "$S/decl3b_$WB.txt" || { echo "$WB: DECLARE FAILED"; continue; }
  uv run --no-project python "$S/my_wbs3b.py" "$S/$LANE" "$WB" || { echo "$WB: APPLY FAILED"; continue; }
  echo "== $WB landed: $(git diff --shortstat)"
  timeout 2400 uv run pytest -n 8 -q -p no:cacheprovider --tb=short --junitxml="$S/wb3b_$WB.xml" $(cat $FILES) > "$S/wb3b_$WB.log" 2>&1
  echo "== $WB tail: $(tail -n 1 $S/wb3b_$WB.log)"
  uv run --no-project python - "$WB" <<'PY'
import sys, xml.etree.ElementTree as ET
S="/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad"
wb=sys.argv[1]
declared=set(open(f"{S}/decl3b_{wb}.txt").read().split("\n"))-{""}
def nid(tc):
    cn=tc.get("classname"); parts=cn.split(".")
    mod_idx=next(i for i,p in enumerate(parts) if p.startswith("test_"))
    path="/".join(parts[:mod_idx+1])+".py"; rest="::".join(parts[mod_idx+1:])
    return f"{path}::{rest}::{tc.get('name')}" if rest else f"{path}::{tc.get('name')}"
root=ET.parse(f"{S}/wb3b_{wb}.xml").getroot()
total=sum(1 for _ in root.iter("testcase"))
observed={nid(tc) for tc in root.iter("testcase") if tc.find("failure") is not None or tc.find("error") is not None}
unexpected=sorted(observed-declared); still_green=sorted(declared-observed)
verdict = "SURVIVES (0 red)" if not observed else ("KILLED — declared set fired EXACTLY" if not unexpected and not still_green else "KILLED (set differs from declaration)")
print(f"== {wb} VERDICT: {verdict}; observed={len(observed)} declared={len(declared)} testcases={total}")
for n in unexpected: print(f"   UNEXPECTED-RED {n}")
for n in still_green: print(f"   DECLARED-STILL-GREEN {n}")
PY
done
git checkout -q -f adv3-ref && git clean -qfd -e REPORT-sidecar-63c.md
```

### A.6 `kp_pairs.sh`
```bash
#!/usr/bin/env bash
# Kill-pin pairs: for each build (REF = the reference itself), reset the lane to adv3-ref, apply the build
# (my_wbs3.py / my_wbs3b.py), copy the kill-pins in, run ONLY the kill-pin file, print the tail + reds.
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad
cd "$S/ref"
echo "provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
for WB in "$@"; do
  git checkout -q -f adv3-ref && git clean -qfd
  case "$WB" in
    REF) ;;
    FX1|R5|IM3n) uv run --no-project python "$S/my_wbs3b.py" "$S/ref" "$WB" >/dev/null ;;
    *) uv run --no-project python "$S/my_wbs3.py" "$S/ref" "$WB" >/dev/null ;;
  esac
  cp "$S/test_adv_r3_killpins.py" loremaster/tests/
  timeout 900 uv run pytest -n 4 -q -p no:cacheprovider -rf loremaster/tests/test_adv_r3_killpins.py > "$S/kp_$WB.log" 2>&1
  echo "== KP on $WB: $(tail -n 1 $S/kp_$WB.log)"
  awk '/^FAILED/{print "   " $1 " " $2}' "$S/kp_$WB.log"
done
git checkout -q -f adv3-ref && git clean -qfd
```

### A.7 `test_adv_r3_killpins.py`
```python
"""adversary-63c-i-a-r3 — kill-pins for the wrong builds that SURVIVE the r3 contract (scratch-only).

Each pin is proven by the PAIR: GREEN on my independent reference (adv3-ref) and RED on exactly its wrong
build (my_wbs3.py). Copied into <lane>/loremaster/tests/ only for the proof runs; never the repo.
"""

from __future__ import annotations

import re
import types
from typing import Any

import pytest
from _comms_fakes import FakeAgentRegistry
from _governed_contract import AGENT_TABLE, patch_shared_object_everywhere, seed_agent_governed
from _surreal_harness import run
from loremaster.agents import AgentRegistryError
from test_agent_governance_63c_i_a import (  # noqa: F401 - pytest fixtures imported by name
    TestAgentMigrateScopeKeyed63cIA,
    _migrate_agent,
    agent_migrate_world,
)

from loremaster import principals


# --- KP-X1: the SKIP gate itself (not only its home) moves with the ONE identity decision ------------
class _SpyRegistry:
    """Counts registry lookups; resolves nobody (so the traffic line is honest silence either way)."""

    def __init__(self) -> None:
        self.lookups: list[str] = []

    async def get_agent(self, name: str, *, session: str | None = None) -> Any:
        self.lookups.append(name)
        raise AgentRegistryError(f"no agent {name!r}")


async def test_KP_X1_the_traffic_line_SKIP_gate_moves_with_the_shared_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_comms_traffic_line``'s charset gate (Ruling 5.2's SKIP policy) must decide with the ONE shared
    decision. BASELINE: unpatched, the legal 'fixer-b' IS looked up (one registry read). MUTATION: the
    shared ``is_legal_identifier`` rejects 'fixer-b' → the gate must SKIP it (zero registry reads). A gate
    that decides with a private regex keeps looking it up — a second decider at the SKIP call site."""
    import lorerunes
    from loremaster.server import AppContext

    baseline_spy = _SpyRegistry()
    baseline_self = types.SimpleNamespace(agent_registry=baseline_spy, message_ledger=None)
    await AppContext._comms_traffic_line(  # noqa: SLF001
        baseline_self, agent=None, session=None, attributions=("fixer-b",)
    )
    assert baseline_spy.lookups == ["fixer-b"], f"BASELINE: the legal name was not looked up: {baseline_spy.lookups}"

    shared = lorerunes.is_legal_identifier
    patch_shared_object_everywhere(
        monkeypatch, "is_legal_identifier", shared, lambda value: value != "fixer-b" and shared(value)
    )
    spy = _SpyRegistry()
    mutated_self = types.SimpleNamespace(agent_registry=spy, message_ledger=None)
    await AppContext._comms_traffic_line(  # noqa: SLF001
        mutated_self, agent=None, session=None, attributions=("fixer-b",)
    )
    assert spy.lookups == [], (
        "the _comms_traffic_line SKIP gate still looked up a value the SHARED decision now rejects — the "
        f"gate decides with something other than lorerunes.is_legal_identifier (lookups={spy.lookups})"
    )


# --- KP-X2: the refusal's id bound MOVES with the named constant (one source, proven by mutation) ----
async def test_KP_X2_the_refusal_bound_moves_with_REFUSAL_ID_SAMPLE_SIZE(
    agent_migrate_world: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Perturb ``principals._REFUSAL_ID_SAMPLE_SIZE`` to 3, seed 3 + 15 traps: the refusal must name
    EXACTLY 3 ids. A build that defines the constant but slices with a restated literal ``[:10]`` names 10
    — two sources of one policy that agree only at birth (amendment-4 MP-C: 'no literal [:10]')."""
    principal_store, keep_store, connection, env, _operator = agent_migrate_world
    monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 3)
    await TestAgentMigrateScopeKeyed63cIA._seed_clean_legacy(connection, count=1)  # noqa: SLF001
    trap_ids = [f"owned_trap_{index:03d}" for index in range(18)]
    for index, trap_id in enumerate(trap_ids):
        await seed_agent_governed(
            connection, row_id=trap_id, name=f"owned-legacy-{index}", session="dead-session",
            owner_principal=f"other_principal_{index}", owner_agent=None, scope=None,
        )
    before = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    result = await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
    after = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    assert result.refused is True and after == before
    reason = str(result.reason or "")
    assert re.search(r"\b18\s+(?:agent\s+)?rows?\b", reason), reason
    named = [trap_id for trap_id in trap_ids if trap_id in reason]
    assert len(named) == 3, (
        f"the refusal did not follow the NAMED bound (patched to 3): it named {len(named)} ids — the slice "
        f"restates a literal instead of reading _REFUSAL_ID_SAMPLE_SIZE: {reason[:300]!r}"
    )


# --- KP-X3: EFFECT, not source text — the fake never silently skips its identity leg -----------------
async def test_KP_X3_the_fake_never_silently_skips_the_identity_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Post-build, the fake's identity leg has NO silent-skip path: with the shared predicate made
    UNIMPORTABLE, a hostile-named fake register must not SUCCEED (any exception is fine — an ImportError
    is the honest outcome). A guard of ANY shape (``except ImportError``, ``except Exception``, a
    ``getattr(..., None)``) that turns absence into "skip the check" registers the hostile name."""
    import lorerunes

    monkeypatch.delattr(lorerunes, "is_legal_identifier")
    fake = FakeAgentRegistry()
    registered = False
    try:
        await fake.register("fixer-b\n", session="wave7", role="builder")
        registered = True
    except Exception:  # noqa: BLE001 - any refusal/ImportError is the non-silent outcome
        pass
    assert not registered and fake.db.agents == {}, (
        "the fake REGISTERED a hostile name while the shared identity predicate was unavailable — a "
        "surviving guard turns 'predicate absent' into 'skip the check' (amendment-5 FORK-C: the guard "
        "must not outlive its premise, whatever its except-clause spells)"
    )


# --- KP-FX1: the fake mirrors the writer on the RE-register path too (mint-once ∀ rows, both sides) ----
async def test_KP_FX1_fake_and_real_agree_after_a_credentialed_re_register_of_an_alpha_row() -> None:
    """α register (None, None), then a credentialed RE-register (owner + keep) on BOTH the real registry and
    the fake: the governed stamps must agree afterwards (the real writer is mint-once ∀ rows — MP-F)."""
    from _surreal_harness import drop_database
    from test_agent_registry import TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA as Harness

    registry, admin_connection, env = await Harness._real_registry()  # noqa: SLF001
    try:
        first = await registry.register("fixer-b", session="wave7", role="builder")
        await registry.register(
            "fixer-b", session="wave7", role="builder", owner_principal_id="alice_pid",
            session_keep_id="sessionkeep7",
        )
        bare = str(first.agent.id).split(":", 1)[-1]
        row = (await run(
            admin_connection,
            f"SELECT owner_principal, scope FROM type::record('{AGENT_TABLE}', $id)", {"id": bare},
        ))[0]
        real = (row.get("owner_principal"), row.get("scope"))
    finally:
        await admin_connection.close()
        await registry.close()
        await drop_database(env)
    fake = FakeAgentRegistry()
    fake_first = await fake.register("fixer-b", session="wave7", role="builder")
    await fake.register(
        "fixer-b", session="wave7", role="builder", owner_principal_id="alice_pid", session_keep_id="sessionkeep7",
    )
    fake_id = str(fake_first.agent.id).split(":", 1)[-1]
    fake_pair = (fake.db.owners.get(fake_id), fake.db.scopes.get(fake_id))
    assert real == (None, None), f"REAL: the α row was stamped on re-register: {real!r}"
    assert fake_pair == (None, None), (
        f"FAKE diverges from the writer on the RE-register path (mint-once ∀ rows): fake={fake_pair!r} "
        f"real={real!r}"
    )


# --- KP-R5: the FORK-A KNOWN BOUND's PREMISE is pinned, not only its set ------------------------------
def test_KP_R5_the_pinned_unswept_emitters_emit_NO_relation() -> None:
    """The pin-the-miss says the unswept set is EXACTLY {lease, floor_calibration} and that this is 'a
    hidden constant, not a live hole' BECAUSE neither emits a relation. That premise must be pinned too:
    a relation added INSIDE an already-unswept emitter leaves the unswept SET unchanged (pin green) while
    the ∀-ENFORCED relation pins (which sweep only the ALL_DDL_GENERATORS hand-list) never see it."""
    from _enforced_relations_scaffold import emit_schema_ddl, relation_endpoints, schema_ddl_generators

    generators = schema_ddl_generators()
    for name in ("generate_lease_ddl", "generate_floor_calibration_ddl"):
        relations = relation_endpoints(emit_schema_ddl(generators[name]))
        assert relations == {}, (
            f"{name} — an emitter OUTSIDE the ALL_DDL_GENERATORS sweep — now emits relation(s) "
            f"{sorted(relations)}: the pinned KNOWN BOUND is a LIVE hole (no ∀-ENFORCED pin sees them)"
        )
```

### A.8 `red_diff.py`
```python
"""adversary-63c-i-a-r3 — RED@HEAD diff: r3 tests (39935f6) vs r2 tests (88205a4), both on HEAD production.

Reports: totals per side; ids GREEN on r2 and RED on r3 (a HEAD-green turned red — the claim is ZERO);
ids RED on r3 that did not exist on r2 (new pins); ids RED on r2 no longer present on r3 (re-keyed/deleted).
"""

import xml.etree.ElementTree as ET
from collections import Counter

S = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/42ef9125-d680-49f0-9453-ae0e5fdf6f49/scratchpad"


def load(path: str) -> dict[str, str]:
    outcome: dict[str, str] = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        node = f"{tc.get('classname')}::{tc.get('name')}"
        if tc.find("failure") is not None or tc.find("error") is not None:
            outcome[node] = "red"
        elif tc.find("skipped") is not None:
            outcome[node] = "skip"
        else:
            outcome[node] = "green"
    return outcome


r3, r2 = load(f"{S}/red_r3.xml"), load(f"{S}/red_r2.xml")
print("r3 totals:", Counter(r3.values()), "| r2 totals:", Counter(r2.values()))
turned = sorted(n for n in r3 if r3[n] == "red" and r2.get(n) == "green")
new_red = sorted(n for n in r3 if r3[n] == "red" and n not in r2)
gone_red = sorted(n for n in r2 if r2[n] == "red" and n not in r3)
still_red = sorted(n for n in r3 if r3[n] == "red" and r2.get(n) == "red")
healed = sorted(n for n in r3 if r3[n] == "green" and r2.get(n) == "red")
print(f"HEAD-green on r2 turned RED on r3: {len(turned)}")
for n in turned:
    print("   TURNED", n)
print(f"NEW red ids (absent on r2): {len(new_red)} · red on both: {len(still_red)} · r2-red ids gone on r3: {len(gone_red)} · red→green: {len(healed)}")
by_class = Counter(n.split("::")[0].rsplit(".", 1)[-1] for n in new_red)
for cls, count in by_class.most_common():
    print(f"   new-red class {cls}: {count}")
for n in gone_red:
    print("   GONE", n)
for n in healed:
    print("   HEALED", n)
```

### A.9 one-off probes (verbatim)
```bash
# collected3.txt — the declaration universe, taken BEFORE any wrong-build run (lane ref @ adv3-ref):
uv run pytest -q --collect-only -p no:cacheprovider $(cat $S/files.txt) | awk '/::/' > $S/collected3.txt      # 2807 ids
uv run pytest -q --collect-only -p no:cacheprovider $(cat $S/files3b_R5.txt) | awk '/::/' > $S/collected3b.txt # 2901 ids
# reference contract run + full suite (lane ref @ adv3-ref, alone):
uv run pytest -n 8 -q -p no:cacheprovider --tb=line --junitxml=$S/ref_contract.xml $(cat $S/files.txt)   # 2807 passed
uv run pytest -n 12 -q -p no:cacheprovider --tb=short --junitxml=$S/full_sat.xml                           # 11405 passed, 62 skipped, 3 xfailed
# gate currency (lane head = 83050b9; lane built = 83050b9 + my_ref_build.py):
uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff
# RED@HEAD (lane head): r3 tests, then `git checkout 88205a4 -- loremaster/tests`, r2 tests, then restore:
uv run pytest -n 8 -q -p no:cacheprovider --tb=line --junitxml=$S/red_r3.xml $(cat $S/redset.txt)
uv run pytest -n 8 -q -p no:cacheprovider --tb=line --junitxml=$S/red_r2.xml $(cat $S/redset.txt)
# gc.get_referrers reach probe (P-PKG row 1):
uv run python -c 'import gc, types; m=types.ModuleType("m"); f=lambda v: v; m.x=f
class C: y=f
g=(lambda: f); print(len(gc.get_referrers(f)), sorted({type(r).__name__ for r in gc.get_referrers(f)}))'   # 3 ['dict']
# corpse sweep (§11): awk over every `git ls-files` path, bare pattern:
#   /_schema_string_constants|_resolve_schema_table|_governed_node_tables|_governed_relation_tables|_GOVERNED_FIELD_SPECS_EMITTER|_DEFINE_RELATION_EMITTER|schema_source|_patch_everywhere|RE_EXPORTED_endpoint/
```

---

## VERDICT: CONTRACT INSUFFICIENT
Five concrete missing pins (§6), each with a wrong build that passes all 2807 tests of the 22 contract files (R5: 2882 + 19 skipped over 24 files) and a kill-pin proven GREEN on my independent reference and RED on only that build. The prior pass's floor is fully closed (7/7 killed exactly), the contract is satisfiable on an independent reference over the FULL suite (11405/0), and its RED is honest (0 greens turned red, 77 right-reason new reds). MP-1, MP-2 and MP-3 are cheap (one parametrize leg / one monkeypatch leg / one effect test) and touch what the builder builds; MP-4 and MP-5 are test-substrate and can land beside the build, before the cold audit — the sidecar rules the classes.
