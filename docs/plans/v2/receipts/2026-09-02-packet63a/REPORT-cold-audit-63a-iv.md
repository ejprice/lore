# REPORT-cold-audit-63a-iv — packet 63 wave 63a-iv COLD AUDIT (REFUTE, Opus 4.8)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: NO-GO** — one finding. The #439 owner-fold and the corpse dual are CLEAN and
  verified; but the F5 "GOVERNED-TABLE WRITE-ENFORCEMENT COMPLETENESS" instrument (the wave's
  central deliverable) has an **unnamed file-level reach gap**: a real governed-column memory-table
  write — `principals.py::_migrate_memory_scope` (the design-named `migrate-governed`) — sits
  OUTSIDE F5's L1 reach (scoped to `memory/local.py` by the hidden constant `mutation_source=_local_source`)
  and is uncovered on **all three F5 layers**. This is the reach-as-hidden-constant class the wave
  exists to close, and the design §10.9-A allowlist itself NAMES `migrate-governed` as an entry F5
  should carry. See §FINDING-1. LIVE severity is LOW (admin-CLI-only migration, design-correct, no
  member seizure); the driver is the over-stated completeness claim + the unnamed bound.
- state: **done**
- **Graded:** 9d06f6b · HEAD-at-report: 9d06f6b · **SAME** (HEAD == the graded build; index on
  `feat/surreal-unification` @ 9d06f6b, current, 0 in-flight).
- **#439 owner-fold — CLOSED (verified live):** independent unit probe (distinct owner ⇒ distinct
  id; same owner ⇒ dedup) + all 3 §REPRO seizure constructions + intra-principal sibling + positive
  control GREEN against provenance-asserted scratch (`loremaster.__file__ = /tmp/cav63aiv_2149907/…`).
  §D439.
- **Class-closure (F5) — mutation-proven for local.py, GAP outside it:** I injected a genuinely-new
  4th unguarded write into scratch `local.py` → L1 RED (orphan); unwired `remember` → L2a + L2b RED
  (runtime label=None). BUT the reach is a hand-picked file, and `principals.py` holds an uncovered
  memory write (§FINDING-1). §CLASS.
- **Corpse dual (7 files) — CLEAN:** assertions preserve their virtues (determinism / backward-compat
  / distinct-inputs⇒distinct-id / dedup) with the owner in the basis; golden literals INDEPENDENTLY
  reproduced by `scripts/compute_ownerfold_golden_ids_63a_iv.py` (raw uuid5, matches byte-for-byte);
  `FakeMemoryBackend.remember` folds the owner via the SAME `derive_memory_id` (P5 closed);
  `test_mcp_server` oracle folds GROUND-TRUTH owner (resolved via real `_resolve_subject`). §CORPSE.
- Packages considered: none — cold audit specifies no mechanism. (The build's stdlib `contextvars`
  write-guard choice was independently confirmed correct by the adversary; I did not re-litigate.)
- Reuse ledger: none (auditor writes no production symbols; scratch discarded).
- **Graded gate re-runs (my own, this session):** ruff clean · typecheck EXIT=0 (7 legs) · all
  `test_*63a*.py` + `test_mcp_server` **794 passed** · corpse memory suites **320 passed / 2 failed
  (both PRE-EXISTING, confirmed unrelated) / 322 collected** · 61-family + corpse-B/C **151 passed**
  · scratch 63a-iv 6 modules **26 passed**. §GATES.
- decisions-needed: **the §FINDING-1 design fork** — extend F5's reach to derive the memory-mutating
  FILE SET from production truth + allowlist `migrate-governed` with an evidence-backed pin, OR name
  an F-4 bound (PIN-THE-MISS) with rationale + re-open trigger. Touches design §10.9-A (a design
  decision — route to lead/operator).
- receipt POINTERS: verdict driver → §FINDING-1; owner-fold live → §D439; class close/gap → §CLASS;
  corpse dual → §CORPSE; gates → §GATES; residuals → §RESIDUALS.

---

## §FINDING-1 — F5 completeness reach gap: `_migrate_memory_scope` is outside L1's reach (MEDIUM; verdict driver) — filed lore finding **#446**

**Claim under audit:** F5 (design §10.9-A, `test_memory_enforcement_63a_iv.py` docstring) is
*"GOVERNED-TABLE WRITE-ENFORCEMENT COMPLETENESS … for the MEMORY table"* that *"closes the
enumerate-the-forbidden CLASS: memory write verbs were guarded ONE AT A TIME."*

**The gap (file:line):** `loremaster/loremaster/principals.py::_migrate_memory_scope` (the backfill
UPDATE at `principals.py:1187`):
```python
statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"
```
is a RAW mutation of the memory table's GOVERNED `scope` column. It is:
- **NOT guarded** — it runs through `run_query(...)` directly, never `governed.guarded_write`, and it
  is NOT wrapped in `governed.write_guard` (no attribution context).
- **INVISIBLE to F5 L1** — `MEMORY_F5_CASE.mutation_source = _local_source` (the module source of
  `memory/local.py` ONLY; `governed_table_raw_mutation_sites` reads that ONE file). `principals.py`
  is never scanned, so the site is never derived, so deny-by-default never fires for it.
- **INVISIBLE to F5 L2a** — the frame set is derived from `MEMORY_WRITE_ALLOWLIST` (3 local.py
  frames); `_migrate_memory_scope` is not an entry, so it is never checked for a `write_guard` call.
- **INVISIBLE to F5 L2b** — `observe_governed_table_writes` patches `run_query` only on
  `local_mod` and `governed_mod` (`_governed_contract.py:814-815`), never on `principals.py`'s bound
  `run_query`; and the L2b battery never exercises the migration. So even at runtime the write is
  unobserved.

So a memory-table governed-column write is uncovered on **all three F5 layers**.

**Why this is a defect, not noise (design's own words convict it):** design §10.9-A layer 3 lists the
allowlist entries F5 must carry — *"the owner-folded remember UPSERT …; `_reinforce`; …;
**`migrate-governed` (its own preconditions)**."* The build implemented 3 of these and **silently
dropped `migrate-governed`** — because §10.9-A step 1 also scopes L1 to *"every mutation site in
`memory/local.py`"*, and `migrate-governed` lives in `principals.py`, so an L1 that scans only
local.py structurally CANNOT produce it (including it in the allowlist would make it a GHOST that
reds `test_every_derived_raw_mutation_site_is_in_the_allowlist`). The design is internally
inconsistent (step 1 local.py-only vs step 3 names migrate-governed); the build resolved that tension
by dropping coverage of `migrate-governed` **without naming the resulting bound**. This is:
- **the reach-as-hidden-constant class the wave was built to close** (CLAUDE.md INSTRUMENT 0 / the
  six-defeats table): *"is the guard's reach DERIVED from production truth or a name/prefix/hand-list?"*
  Here the reach is `_local_source` — a hand-picked single file, not a derived set of the
  memory-mutating files. Production truth: memory writes exist in BOTH `local.py` AND `principals.py`.
- **an unnamed bound** — unlike the adversary's F-2/F-3 (both filed with re-open triggers), this
  file-level reach limitation is named NOWHERE (grep of every 63a-iv report: 0 hits for
  `_migrate_memory_scope` / `principals.py`). *"An unpinned known limitation is indistinguishable
  from an unknown one"* / *"THE RIDER IS PART OF THE RULING."*
- **a dropped design-named allowlist obligation** (§10.9-A layer 3's `migrate-governed` triple).

**Failure scenario:** a future edit to `_migrate_memory_scope` (or ANY new memory-table write added
to `principals.py` — e.g. the 63b message/agent migration, which will land in this same file per the
`migrate_governed` dispatch at `principals.py:1092`) that seizes/re-scopes/overwrites a governed
column passes EVERY F5 gate green — the exact "green at every gate, one-at-a-time" failure F5 exists
to prevent, re-opened one file over. The instrument reports "the memory write set is the 3 known
local.py sites" while a 4th governed-column write is live in a sibling module.

**LIVE severity is LOW, and I say so plainly:** `_migrate_memory_scope` today is admin-CLI-only
(`lore-adm migrate-governed --table memory`, run at the 65 cutover per `migrate_governed`'s
docstring), idempotent, sets `scope` ONLY on `scope IS NONE` legacy rows to the canonical project
keep, resolves THE operator principal or REFUSES (never fabricates), and routes through the injected
store driver (R4). It is design-sanctioned (§2.1/§2.2 grandfather backfill) and is TESTED by its own
gates (`test_governed_migration_63a.py`, 42 refs). There is **no member-reachable seizure** here —
this is NOT the live-isolation-hole class of the prior two NO-GOs (F1 supersede, F-A create). The
driver is purely the over-stated completeness claim + the unnamed reach bound.

**Remediation (the lead/operator's call — it touches design §10.9-A):**
- **(a) Cover it:** make F5's L1 reach a CHECKED VARIABLE — derive the set of memory-mutating
  production files from truth (not a hand-picked `_local_source`), scan `principals.py` too, and add
  `migrate-governed` as a `(site, justification, pin)` allowlist triple whose pin is its admin-CLI
  preconditions (single-operator resolution + NONE-scope-only + idempotent). This honors the design's
  step-3 entry and closes the class over the whole table. **Preferred** — it is what "completeness"
  means, and 63b will add MORE `principals.py` memory/message writes that need the same net.
- **(b) Name the bound:** add an F-4 named bound (sibling to F-2/F-3) on `governed_table_raw_mutation_sites`
  / the `MEMORY_F5_CASE` — *"F5's L1 structural reach is `memory/local.py`; the `migrate-governed`
  admin write in `principals.py` is a memory-table governed write OUTSIDE that reach, justified by
  its own admin-CLI preconditions; RE-OPEN if migrate-governed becomes member-reachable, gains a
  non-NONE-scope write, or a second memory write lands in principals.py"* — and file the finding.
  This is the minimum honest close if the operator judges the admin-CLI reach limitation acceptable.
- Either way, resolve the design §10.9-A step-1 (local.py-only) vs step-3 (names migrate-governed)
  inconsistency at the design authority.

---

## §D439 — #439 owner-fold is genuinely CLOSED (live, provenance-asserted)

Scratch: `./scripts/scratch_copy.sh /tmp/cav63aiv_2149907` → provenance asserted;
`loremaster.__file__ = /tmp/cav63aiv_2149907/loremaster/loremaster/__init__.py` (printed in every
probe below — I am grading the real owner-folded artifact, not the original tree, #140-safe).

**Root property (my own independent unit probe, NOT the builder's test):**
```
dedup (same owner)       alice/ag1 == alice/ag1 : True
cross-principal distinct alice/ag1 != bob/ag1  : True
sibling-agent  distinct alice/ag1 != alice/ag2 : True
text still folds / refs still folds            : True / True
```
`derive_memory_id` (`memory/backend.py:177`) folds `memory:{owner_principal}:{owner_agent}:{text}:{refs_stamp}`
(constants `_ID_PREFIX="memory"`, `_ID_SEPARATOR=":"` verified). `remember` (`memory/local.py:536`)
passes `owner_principal=subject.principal_id, owner_agent=subject.agent_id`; the create-path UPSERT
is keyed on that id with **no WHERE-guard** (store-ref §2 — unrepresentability from the DERIVATION,
verified in source). A distinct id ⇒ a distinct UPSERT target ⇒ no seizure, by construction.

**Integration (all 3 §REPRO constructions + control), run against the provenance-asserted scratch:**
`test_memory_ownerfold_63a_iv.py` + the other 5 63a-iv modules → **26 passed in 22.13s** in the
scratch. This exercises the REAL `remember`→store path end-to-end:
- construction 1 (cross-principal seizure + re-scope) — bob's re-remember of alice's exact text mints
  a DISTINCT id; alice's row owner/scope/`valid_until` UNCHANGED; control: bob's guarded invalidate DENIES.
- construction 2 (intra-principal sibling, LIVE-today) — worker_2 (same principal, diff agent) mints a
  DISTINCT id; worker_1's row un-re-owned.
- construction 3 (revive a retired foreign note) — bob's re-remember does not un-retire alice's note.
- positive control `TestSameAgentDedupIsPreserved` — same (principal, agent) re-save dedups in place
  (one row); no nonce/timestamp folded (anti-over-fix).

---

## §CLASS — is the class closed? (F5 mutation proofs — the fourth-verb hunt)

**F5 discriminates over local.py (proven with a genuinely-new site, not the synthetic string):**
- Injected `_auditor_fourth_unguarded_write` (a NEW raw `UPDATE type::record('{MEMORY_TABLE}', $id)
  SET scope='seized'`) into scratch `local.py` → L1 **2 failed**:
  `test_the_derived_raw_mutation_set_is_non_empty_and_is_the_known_set` +
  `test_every_derived_raw_mutation_site_is_in_the_allowlist`
  (`AssertionError: UNCLASSIFIED raw memory mutation(s) … [MutationSite(function='_auditor_fourth_unguarded_write', verb='UPDATE')]`).
  Deny-by-default fires; the derived set genuinely GROWS-and-REDS.
- Restored, then unwired `remember`'s `with governed.write_guard("remember"):` → L2a
  (`test_every_allowlisted_local_frame_calls_write_guard`) + L2b
  (`test_every_observed_memory_mutation_is_attributed_to_a_frame`,
  `[('execute_transaction','UPSERT')]` label=None) both **RED**. L2b observes the EFFECT at the seam
  (ROUTING-IS-NOT-SHARING at runtime), independently of L2a's structural proxy.

**Derived-3 set is COMPLETE over local.py** (independent grep of ALL memory mutations in `local.py`):
exactly 3 raw sites — `REMOVE TABLE` (`local.py:970`, `_recreate_memory_table`), `UPDATE …
importance` (`local.py:1152`, `_reinforce`), `UPSERT … CONTENT` (`local.py:1368`, `_upsert_fragment`)
— matching the allowlist. Each allowlist entry carries a REAL evidencing pin (pin-existence leg).
The guarded consumers (`invalidate`, the supersede-close in `remember`) route through `guarded_write`
(governed.py), correctly not raw sites.

**BUT the class is NOT closed over the memory TABLE:** the reach is a hand-picked file. A memory
governed-column write lives in `principals.py` outside every F5 layer → §FINDING-1. Answer to "is
there an existing memory mutation of an existing row that F5 waved through?": **yes — one that F5
never SEES** (worse than waved-through-the-allowlist: it is outside the reach entirely).

---

## §CORPSE — the 7-file removed-behaviour dual (CLEAN)

Sampled the updated oracles/callers; every one preserves its ORIGINAL virtue with the owner now in
the basis (no silent weakening):
- **`test_memory_backend.py`** — `expected_memory_id` (def:267) now folds the owner pair (default =
  the shared admin `_GOV_SUBJECT` `corpse_a_admin`/`corpse_a_agent`, which `_GovernedTestBackend`
  injects into every mint). The 3-way parity `remember(...) == expected_memory_id(...) ==
  _LITERAL_ID_*` still holds (determinism + backward-compat + independent-oracle). Unicode-identical
  hashing, order-normalised refs, distinct-refs⇒distinct-id, dedup-one-row — all preserved.
- **Golden literals are a GENUINE independent cross-check (not tautological):**
  `scripts/compute_ownerfold_golden_ids_63a_iv.py` reimplements the uuid5 convention DIRECTLY over
  `uuid.uuid5` (NOT `derive_memory_id`). I ran it; its 9 outputs match the frozen `_LITERAL_ID_*` /
  inline literals in `test_memory_backend.py` **byte-for-byte** (`9f902f95…`, `263cce46…`, `68e0d114…`,
  `a7ed71cd…`, `85095576…`, `6aa88d6f…`, `f5355796…`, `16ddd5ce…`, `cffa6d96…`). A production
  derivation that diverged from the convention would red the parity pins.
- **`_memory_fakes.FakeMemoryBackend.remember` (`:308`)** folds the owner from its `subject` via the
  SAME `derive_memory_id` (`getattr(subject,"principal_id",None) or ""`) — ONE derivation policy; the
  P5 divergence (a fake minting old-scheme ids that silently tests the corpse against the real
  backend) is closed.
- **`test_mcp_server.py`** — the `governed_ctx` fixture (`:6681`) resolves the subject via the REAL
  `_resolve_subject` seam (`:6724`, the SAME one `remember` uses) and exposes `_owner_principal`/
  `_owner_agent`; the 6 parity callers fold that GROUND-TRUTH owner, so `memory_id == expected` is a
  genuine served-tool mint parity (would red if `remember` dropped/mis-folded the owner), not a guess.
- **`test_memory_ledger.py` / `test_memory_cutover.py` / `test_schema_rebuild.py` / `test_search.py`**
  — folds a fixed owner (ledger/cutover are owner-agnostic, key on the handed id); the `test_search.py`
  id is realistic and never asserted (pipeline reads `.text`/`.score`/`.refs`). Virtues (replay-in-place
  by stored id, restore keys) preserved.

Removed-behaviour adjudication (P6b): "global content-address dedup" → old-bug-not-re-pinned (design
§10.9-B); ledger replay uses the STORED `record.memory_id` (`_replay_record`), never a re-derivation —
verified, virtue intact.

---

## §GATES — re-run counts (my own, TEST store ws://127.0.0.1:18000, HEAD 9d06f6b)
- `uv run ruff check .` → **All checks passed!**
- `bash scripts/typecheck.sh` → **EXIT=0** (lorerunes/lorescribe/loresigil/loremaster[257 files]/
  skills/docs/scripts + shellcheck — every leg OK).
- all `test_*63a*.py` (15 files) + `test_mcp_server.py`, `-n auto` → **794 passed, 3 warnings** in
  154s (0 skipped — matches build).
- `test_memory_backend` + `test_memory_ledger` + `test_memory_cutover` + `test_schema_rebuild` +
  `test_search`, `-n auto` → **320 passed, 2 failed** (322 collected: 129+5+7+51+130). The 2 failures
  are the PRE-EXISTING `TestRebuildingNoticeSeam::{test_a8a_search_code_empty_in_progress_raises_rebuilding_error,
  test_a8a_search_code_rebuilding_error_survives_mcp_serialization}` (a `search_code` rebuilding-notice
  seam, `DID NOT RAISE`). Independently confirmed unrelated: 9d06f6b's PRODUCTION changes are
  `governed.py`/`backend.py`/`local.py`/`server.py`(prose-only) — none touches the search/rebuild/notice
  path; the `test_schema_rebuild.py` change is ONLY the `ledger_only_id` corpse caller in
  `TestMemoryJoinsSchemaRebuild` (a DIFFERENT class). These are the ONLY unrelated fails; 63a-iv
  introduced no new failure.
- 61-family (pdp_oracle/tool_population/visible_keeps/keep_remediation_{store,cli}/principal_delete_cascade)
  + corpse-B/C (`test_agent_capability_seams` + `test_keeps_store`) → **151 passed** (neither corpse-B/C
  references `derive_memory_id`).
- scratch 63a-iv 6 modules (provenance-asserted) → **26 passed**.

---

## §RESIDUALS — every item, an individual verdict
- **#439 owner-fold** — CLOSED (unit + 3 §REPRO constructions + control, provenance-asserted). **SAFE.**
- **F5 L1/L2a/L2b over local.py** — mutation-proven to discriminate (new site → L1 RED; unwired frame
  → L2a+L2b RED). **SAFE (within its reach).**
- **F5 reach over the memory TABLE** — **DEFECT → §FINDING-1** (verdict driver). `_migrate_memory_scope`
  in principals.py uncovered on all 3 layers; unnamed bound; design-named allowlist entry dropped.
- **Corpse dual (7 files)** — assertions preserve virtues; golden literals independent + byte-matched;
  fake folds owner; mcp_server oracle folds ground truth. **SAFE.**
- **F-2 (#444, L1 dynamic-table blind spot)** — pinned by `test_memory_enforcement_bounds_63a_iv.py`
  (with positive control), finding filed with re-open trigger. **SAFE (named bound).**
- **F-3 (#445, L2b member-verb reach)** — documented on `observe_governed_table_writes`, finding filed
  with re-open trigger. **SAFE (named bound).**
- **item-5 audit-DDL** — GREEN composition-root regression guard on the existing `generate_ddl` audit
  fold (production `build_app_context`, NO test-side ensure, discriminating valid-lands/out-of-domain-
  rejected pair). Correctly embraces #440 wontfix; does NOT re-open #438. **SAFE — do not re-open.**
- **F-B `_reinforce` pins** — non-vacuous: bump-set≡served-set has a live positive control; importance-only
  captures the RESOLVED statement (not a source regex). **SAFE.**
- **2 pre-existing failures** (`TestRebuildingNoticeSeam`) — out of packet-63 scope, confirmed unrelated
  (see §GATES); NOT a verdict driver. **NOTED / out-of-scope.**
- **Build-report over-count (minor):** `REPORT-build-63a-iv.md` §GATES claims *"344 passed, 2 failed"*
  for the 5 corpse memory suites; true count is **320 passed / 322 collected** (over-counts by 24, and
  346 > 322 collected is impossible). A build-report bookkeeping error only — the SUBSTANCE (only the
  2 known pre-existing fail) holds. Re-derive-inherited-numbers flag; **does NOT flip the verdict.**
- **Stale TEST docstring (cosmetic):** `test_memory_backend.py` `TestIdempotentIds` docstring
  (~:624-631) still says the id folds *"the note text + the sorted stamp … and NOTHING else"* — now
  folds the owner too. A test-file docstring, not a served surface (the prose-currency sweep scans
  production `_MEMORY_MODULES` only), and no ASSERTION pins the stale claim. P8d-in-test-code;
  non-blocking observation.
- **RES-ATOM (§10.9-D) / RES-A1 `scope=` bound** — correctly NOT in this wave (63b owner). **SAFE.**

---

## §METHOD — instruments (deliverables, brief-base §1)
- **Independent #439 unit probe** — pasted verbatim in §D439 (inline `uv run python -c`, disposable).
- **F5 fourth-verb injection** — the transcribed diff is in §CLASS (a new `_auditor_fourth_unguarded_write`
  method with a raw `UPDATE type::record('{MEMORY_TABLE}', $id) SET scope='seized'`); scratch is
  disposable by design.
- **Golden-literal cross-check** — `scripts/compute_ownerfold_golden_ids_63a_iv.py` is COMMITTED
  (the build's own instrument); I ran it and diffed its output against the frozen literals.
- **Reach grep** — `grep -rnE "(UPSERT|UPDATE|DELETE|REMOVE)" … | grep -iE "memory|MEMORY_TABLE"` over
  the whole `loremaster/loremaster` production tree surfaced the one out-of-reach site
  (`principals.py:1187`); re-runnable.
