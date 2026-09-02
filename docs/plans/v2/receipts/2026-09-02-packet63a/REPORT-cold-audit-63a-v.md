# REPORT-cold-audit-63a-v — COLD AUDIT (fresh-context REFUTE), the CLOSING gate for the whole 63a wave

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: GO.** 63a-v is sound → **the WHOLE 63a wave CLOSES.** I hunted a defect green at every
  builder gate and found none. All gates re-run GREEN; three real-tree mutation constructions confirm
  the pins discriminate; an independent from-truth grep corroborates F5's derived reach; the R4 bounds
  are OPEN and honestly pinned (not silently closed, not silently widened), matching operator OPTION A.
- state: **done**
- deviations: none.
- **Packages considered:** none — 63a-v specifies no new production mechanism I audited beyond the
  stdlib `contextvars`/`contextlib` mirror of `write_guard` (which is the correct, DRY choice — a
  third-party ctx lib would break the ONE-IMPLEMENTATION mirror). Verdict: **keep (stdlib)**.
- **Reuse ledger:** none (auditors write no production symbols; scratch disposable, probes pasted §METHOD).
- **Graded:** `c794b21` · HEAD-at-report: `c794b21` · **SAME**.
- decisions-needed: **none.** The R4 design fork was already operator-ruled OPTION A (finding #449);
  63b root-fix is task `571ef1addd764912b9deb0f1a9d52239` (open, verified).
- receipt POINTERS: gate re-runs → §GATES; governed_exempt leak/auto-reset construction → §C1;
  R3 real-frame + whole-tree reach constructions → §C2/§C4; R4-bounds-honestly-pinned → §R4;
  from-truth grep (4 sites) → §REACH-GREP; pre-existing fails → §PREEXISTING; residuals → §RESIDUALS;
  instruments → §METHOD.

---

## §SCOPE + PROVENANCE
- Graded HEAD `c794b213688d0afd45bd3b045ee7690718eca963`, branch `feat/surreal-unification`.
- lore index confirmed watching this exact ref (`lore_index().workspace.roots[0].git_ref = c794b21`),
  synced 278 s before I started; no session edits between (I edit nothing).
- **63a-v production surface (the ENTIRE change since the 63a-iv GO-point `9d06f6b`):** exactly two
  production files — `governed.py` (+44, the `governed_exempt`/`active_exempt`/`_ACTIVE_EXEMPT` mirror
  of `write_guard`) and `principals.py` (`_migrate_memory_scope` wraps its backfill `run_query` in
  `governed_exempt("migrate-governed")`). Both purely ADDITIVE. Plus test infra
  (`_governed_contract.py` +453, `test_memory_enforcement_63a_v.py` +915) and docs. Verified:
  `git diff 9d06f6b c794b21 --name-only` touches NO search_code / notice / serialization / server
  surface. The earlier 63a waves are not re-litigated; I CONFIRM no 63a-v change regressed them (§GATES).
- Scratch: `./scripts/scratch_copy.sh /tmp/cav63av_close_120796` — provenance ASSERTED, all four
  members resolve INSIDE the copy (`loremaster.__file__ = /tmp/cav63av_close_120796/loremaster/
  loremaster/__init__.py`; #140-safe). Every construction ran in-scratch and restored.

## §GATES — every gate re-run (a green claim carries a passed-COUNT; TEST store ws://127.0.0.1:18000)
| gate | command | result |
|---|---|---|
| 16 × `test_*_63a*.py` + `test_mcp_server.py` + 60/61/62 regression (6 files) | `uv run pytest -q -n auto <24 files>` | **886 passed, 0 failed, 0 skipped**, 3 benign ResourceWarnings (142.03s) |
| ruff | `uv run ruff check .` | **All checks passed!** (exit 0) |
| typecheck | `bash scripts/typecheck.sh` | **exit 0** — lorerunes/lorescribe/loresigil/loremaster/skills/docs·eval/scripts/shellcheck all OK |
| pre-existing-fail file | `uv run pytest -q test_schema_rebuild.py` | **2 failed, 49 passed** (the 2 known `TestRebuildingNoticeSeam` — §PREEXISTING) |

- The 886 = 818 (16 63a suites + `test_mcp_server.py`) + 68 (60/61/62 regression), matching the build
  report's split exactly. `test_mcp_server.py` ran with **0 skipped** (the combined summary reports no
  skips/deselects/xfails at all). `test_memory_enforcement_63a_v.py` (24 pins incl. the R4 pin-the-miss
  pins + base-3) is inside the 886, all GREEN.

## §C1 — REFUTE FOCUS 1: `governed_exempt` soundness (leak / auto-reset construction)
`governed_exempt` is a **verbatim mirror** of `write_guard`: `token = _ACTIVE_EXEMPT.set(name)` /
`try: yield / finally: _ACTIVE_EXEMPT.reset(token)` over a task-local `contextvars.ContextVar`. I built
a probe (`/tmp/probe_exempt_leak.py`, pasted §METHOD) run against the scratch `governed.py`. All legs PASS:
- baseline `active_exempt()` is `None`; inside the block == `"migrate-governed"`; **survives an
  `await asyncio.sleep(0)` inside the block** (task-local, async-safe across the await that runs the store
  mutation); **reset to `None` on normal exit**; **reset to `None` after a RAISE** (the `finally` fires,
  the exception propagates).
- **The ONLY leak shape is a child TASK spawned inside the block** — it inherits a *copy* of the context
  (documented `contextvars` semantics, reproduced). This is **harmless for two independent reasons**:
  (a) the real `_migrate_memory_scope` spawns no task — it directly `await`s the one `run_query`; and
  (b) the classifier requires the write's stack ORIGIN `(file, symbol)` to equal the allowlist entry's
  registered site, so a leaked token in a *foreign* origin fails the match — the borrowed-token defense,
  independently pinned GREEN by `test_a_borrowed_exempt_token_is_unclassified` (origin
  `(_PRINCIPALS, "_some_other_function")` → UNCLASSIFIED). **Verified: a leaked token cannot launder a
  foreign write.**

## §C2 — REFUTE FOCUS 2: the exemption classifies ONLY the migrate write (R3 on the REAL frame)
Spliced a SECOND co-located same-verb UPDATE seizure (`… WHERE scope = $victim`) into the **real**
`principals.py::_migrate_memory_scope` in scratch, ran the R3 single-shape pin:
- CONTROL (unmodified real frame): `test_the_exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation`
  **GREEN** (the real frame holds exactly its one `WHERE scope IS NONE` UPDATE — `_scope_count` SELECTs
  and `get_or_create_keyed` (keep table) live in DIFFERENT functions/tables, so are not counted).
- MUTATED (2nd seizure in the real frame): R3 pin **RED** (`assert 2 == 1` at test line 612) — the
  extractor returns a genuine LIST of 2 (not collapsed, not first-match).
- CROSS-CHECK: with the 2nd same-verb UPDATE present, the whole-tree derived-SET pin stays **GREEN**
  (L1 keys by (file, function, verb) → two UPDATEs in one function collapse to ONE site). This is the
  exact L1 blind spot R3 exists to cover, and R3 covers it. **The layered defense works as designed.**

## §C4 — REFUTE FOCUS 4: the whole-tree F5 reach is an OUTPUT, not a relocated hand-list
Added a NEW governed memory UPDATE (`UPDATE type::record('{MEMORY_TABLE}', $id) SET scope = 'seized'`)
in a **different member** — a synthetic `loresigil/loresigil/_synthetic_mem_write.py` — in scratch:
- `test_the_whole_tree_derived_set_is_the_known_four_sites` **RED** (test line 148 — the derived set grew
  past the 4 allowlisted sites), AND `test_every_whole_tree_site_is_in_the_allowlist` **RED** (line 171 —
  orphan detected). A memory write in ANY member grows the derived set and reds until classified.
- Corroborated by construction: the scan roots are DERIVED from `[tool.uv.workspace] members` in
  `pyproject.toml` (`derive_member_source_roots`), so a new member joins the reach by the same
  derivation that registers it everywhere else. **Not a relocated constant — a genuine output.**

## §REACH-GREP — independent from-truth cross-check (grep is honest for exhaustiveness; I say so)
A bare, anchor-free grep for every mutation verb (UPSERT/UPDATE/DELETE/REMOVE + INSERT/CREATE/RELATE)
adjacent to `memory`/`{MEMORY_TABLE}`/`type::record('memory'` across all four member PRODUCTION trees
(test trees excluded) finds **exactly four** raw memory-table mutation sites — the exact allowlist:
- `principals.py` `_migrate_memory_scope` — `UPDATE {MEMORY_TABLE} … WHERE scope IS NONE` (migrate).
- `memory/local.py` `_recreate_memory_table` — `REMOVE TABLE IF EXISTS {MEMORY_TABLE}`.
- `memory/local.py` `_reinforce` — `UPDATE type::record('{MEMORY_TABLE}', $id) SET importance …`.
- `memory/local.py` `_upsert_fragment` — `UPSERT type::record('{MEMORY_TABLE}', $id) CONTENT …`.
- **No fifth orphan.** `surreal_schema.py::_remove_field(MEMORY_TABLE, name)` is correctly NOT derived —
  it returns `f"REMOVE FIELD IF EXISTS {name} ON {table}"`, whose immediate REMOVE-operand is the field
  name and whose `{table}` is a generic param (renders `{table}`, not `{MEMORY_TABLE}`); it is a schema
  DDL field-drop, not an F5 row/table mutation.
- **No INSERT/CREATE/RELATE memory write exists in production** → R4-c is a genuine PINNED bound, not a
  live hole hiding a seizure.

## §R4 — REFUTE FOCUS 3: the R4 bounds are HONESTLY PINNED — not closed, not widened
- **The bounds are STILL OPEN** (the pin-the-miss pins are GREEN because the limitation EXISTS, not
  because anyone closed it), verified in code at HEAD:
  - **R4-a (WHERE-substring):** the R3 shape leg (`test…:622`), the base-3 pin (`…:311`), and
    `exempt_frame_raw_memory_mutations`' callers all match `re.search(r"WHERE\s+scope\s+IS\s+NONE")` —
    a SUBSTRING, so `… WHERE scope IS NONE OR scope = $victim` still passes. Bound present.
  - **R4-c (verb-set):** `_MUTATION_VERBS = ("UPSERT","UPDATE","DELETE","REMOVE")`;
    `_raw_mutation_of_table` matches `UPSERT|UPDATE|DELETE` + `REMOVE TABLE|FIELD|INDEX`, and
    `_mutation_verb_for_table` the same set — INSERT/CREATE/RELATE return `None`. Bound present.
- **Not silently WIDENED:** the migrate statement is exactly `WHERE scope IS NONE` (not OR-extended);
  no new laundering surface was introduced.
- **Disposition MATCHES the operator ruling.** Finding **#449** (durable ledger record) carries the
  full lead-63-relayed operator **OPTION A**: accept R4-a + R4-c as the **#138 HOSTILE-AUTHOR class**
  F5 explicitly does not defend (F5 is a static HONEST-DEVELOPER net); root-fix DEFERRED to 63b task
  `571ef1addd764912b9deb0f1a9d52239` (**verified open**); named re-open trigger (63b F5 parametrization
  OR migrate/any exempt frame becoming member-reachable/served). A builder did **not** silently close
  R4 (no un-ledgered scope creep) NOR silently widen the laundering surface. This is a valid, structured
  deferral (owner + trigger + pin-the-miss), per CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, PIN IT".
- **The #449 named-bound docstrings + the base-3 fix are ACCURATE (no new false gate):**
  - base-3 `test_migrate_memory_scope_updates_only_none_scope_rows` — docstring now states it reads the
    FIRST `UPDATE … SET scope` (first-match) and asserts the `WHERE scope IS NONE` SUBSTRING, and names
    both accepted bounds; the assertion is UNCHANGED and MATCHES the prose. A dropped/relocated WHERE
    still reds it. **Accurate.**
  - `_raw_mutation_of_table` / `_mutation_verb_for_table` — each names the R4-c verb-set bound + the 63b
    re-open + the pin. `exempt_frame_raw_memory_mutations` — names the R4-a substring bound. Each states
    what its assertion actually checks. **Accurate.**
  - `classify_tree_observed_write` (R2) — names the hand-set-label #138 bound; the `if observed.label is
    not None: return True` first leg genuinely does bless any labelled write. **Accurate**; pinned GREEN
    by `test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound` (tokens
    guarded_write/honest/138 present). The pin-the-miss pins carry PROBE-HONESTY POSITIVE CONTROLS
    (no-substring seizure reds the matcher; an in-set UPDATE is seen by both verb-set functions), so the
    GREEN witnesses are genuine laundering paths, not blind matchers.

## §PREEXISTING — REFUTE FOCUS 5: the 2 pre-existing fails are the ONLY unrelated fails; 63a-v added none
- `test_schema_rebuild.py::TestRebuildingNoticeSeam::test_a8a_search_code_empty_in_progress_raises_rebuilding_error`
  and `…_rebuilding_error_survives_mcp_serialization` — **2 failed, 49 passed**. Root: a `search_code`
  rebuilding-notice does not survive MCP serialization (`convert_result` drops a `_NoticeList` attribute
  → a bare `[]` reaches the agent) — a notice-serialization seam.
- **Structurally unrelated to 63a-v:** the wave touched NO search_code/notice/`convert_result`/server
  surface (`git diff 9d06f6b c794b21 --name-only` confirms), and `test_schema_rebuild.py` was last
  modified at `9d06f6b` (the 63a-iv commit, BEFORE the 63a-v wave). So these fails PRE-DATE 63a-v; the
  63a-iv cold audit already logged them out-of-scope. **63a-v introduced no new failure.**
- I do NOT hold the verdict on them (per brief). Flagged per the operator's standing count rule below.

## §RESIDUALS — every item, an individual verdict
- **F5 whole-tree reach (#446 close)** — mutation-proven a genuine OUTPUT (§C4) + grep-corroborated to
  exactly 4 sites (§REACH-GREP). **SAFE — the 63a-iv NO-GO driver is CLOSED.**
- **`governed_exempt` mechanism** — task-local/async-safe/auto-reset-on-raise; only "leak" (child-task
  context copy) caught by origin-match. **SAFE (§C1).**
- **R3 single-shape / R1 self-containment** — R3 reds a 2nd write on the REAL frame (§C2); both carry
  discrimination mutation-proofs with positive controls in the suite. **SAFE.**
- **R4-a / R4-c** — OPEN accepted bounds, honestly pinned, matching operator OPTION A; root-fix owned by
  63b task `571ef1a…` with a named re-open trigger. **SAFE (named bound, not a live prod hole — no
  exotic-verb/OR-extended memory write exists in prod today).**
- **Label-channel whole-frame trust (adversary-63a-v3 §R4-OTHER d)** — the `if observed.label is not
  None: return True` leg trusts a labelled frame's whole raw-mutation set (R3's ∀ covers only EXEMPT
  frames). Today the one member label-frame (`_reinforce`) is backstopped by its own importance-only
  column pin (`test_the_reinforce_update_sets_only_the_importance_column`, in the 886), which reds a
  co-located `SET scope` seizure — the adversary verified this. Same #138 class as R4; closed generically
  by the 63b statement-scope root-fix. **SAFE today (backstopped) — surfaced, re-open trigger = 63b.**
- **Member-layout assumption in `derive_member_source_roots` (latent, INHERITED — NOT a 63a-v defect)** —
  the scan derives each member's package as `<repo>/<m>/<m>` filtered by `is_dir()`. A FUTURE member
  with a non-standard layout (e.g. `src/`) would resolve to no root and be silently outside F5's reach,
  and the from-truth-roots pin (which uses the same `<m>/<m>` derivation) would not catch it. All four
  current members follow `<m>/<m>` (design-verified); this is the documented uv-workspace/registration-
  sites convention, identical to the bound governing every other registration site. **Observation only —
  not a verdict driver, not introduced by 63a-v; re-open = a member joining with a non-standard layout.**
- **Stale TEST docstring `test_memory_backend.py::TestIdempotentIds` (~624-631)** — carried from the
  63a-iv residuals; cosmetic, un-pinned, not a served surface, untouched by 63a-v. **NOTED (non-blocking).**
- **2 pre-existing `TestRebuildingNoticeSeam` fails** — confirmed pre-63a-v + unrelated. **NOTED /
  out-of-scope; not a verdict driver (§PREEXISTING).**

## §METHOD — instruments (deliverables; scratch is disposable by design, #140-safe)
Scratch `/tmp/cav63av_close_120796` (provenance ASSERTED). Two instruments, pasted verbatim so every
construction is re-runnable:

**(1) `governed_exempt` leak/auto-reset probe** (`/tmp/probe_exempt_leak.py`):
```python
import asyncio
import loremaster.governed as g
results = []
def check(name, cond): results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
async def main():
    check("baseline None", g.active_exempt() is None)
    with g.governed_exempt("migrate-governed"):
        check("inside == migrate-governed", g.active_exempt() == "migrate-governed")
        await asyncio.sleep(0)
        check("survives await inside", g.active_exempt() == "migrate-governed")
    check("reset after normal exit", g.active_exempt() is None)
    raised = False
    try:
        with g.governed_exempt("migrate-governed"):
            check("set before raise", g.active_exempt() == "migrate-governed"); raise ValueError("boom")
    except ValueError: raised = True
    check("exception propagated", raised); check("reset after RAISE", g.active_exempt() is None)
    seen = {}
    async def child(): seen["token"] = g.active_exempt()
    with g.governed_exempt("migrate-governed"):
        t = asyncio.create_task(child()); await t
    check("child inherited a COPY (contextvars)", seen.get("token") == "migrate-governed")
    check("parent reset after child", g.active_exempt() is None)
asyncio.run(main())
raise SystemExit(0 if all(c for _, c in results) else 1)
# → ALL PASS (run in scratch loremaster/; the child-copy is caught by the classifier origin-match).
```

**(2) Real-frame + whole-tree constructions** (`/tmp/construct_63av.py`): backs up the scratch
`principals.py`, splices a 2nd co-located same-verb `UPDATE {MEMORY_TABLE} SET scope=$scope WHERE
scope=$victim` into the real `_migrate_memory_scope`, runs the R3 pin (→ **RED, assert 2==1**) and the
whole-tree set pin (→ GREEN, L1 collapse), restores; then writes a governed memory UPDATE into
`loresigil/loresigil/_synthetic_mem_write.py`, runs the whole-tree set + containment pins (→ **both
RED**), removes it. Full applier text is in the scratch file; the pin node-ids are
`test_memory_enforcement_63a_v.py::TestTheExemptFrameHoldsOnlyItsGuardedMutation::…` and
`::TestTheWholeTreeReachIsAnOutput::{test_the_whole_tree_derived_set_is_the_known_four_sites,
test_every_whole_tree_site_is_in_the_allowlist}`.

**From-truth reach grep:**
`grep -rniE "(UPSERT|UPDATE|DELETE|REMOVE|INSERT|CREATE|RELATE)[^\"']*(memory|\{MEMORY_TABLE\}|type::record\(['\"]?memory)" lorerunes/lorerunes lorescribe/lorescribe loresigil/loresigil loremaster/loremaster --include="*.py"`
→ after excluding prose/comments, exactly the 4 allowlisted mutation literals.

## VERDICT: **GO** — 63a-v is sound; the WHOLE 63a wave CLOSES.
63a-v closes the 63a-iv NO-GO driver (#446 F5-reach hidden constant) with a whole-tree derived reach
(mutation-proven an output, grep-corroborated to 4 sites), adds `migrate-governed` as an
evidence-backed exempt triple attributed by a sound `governed_exempt` mirror (leak/auto-reset proven),
and pins the two accepted R4 bounds honestly per operator OPTION A (open, not closed, not widened; 63b
task verified). All gates GREEN (886/0/0 scoped, ruff + typecheck exit 0), the only fails are the 2
pre-existing `TestRebuildingNoticeSeam` search_code-serialization fails, confirmed pre-63a-v and
unrelated. 63a has been through the full gauntlet (contract → adversary → build → cold audit, across
63a → 63a-iv → 63a-v); this is the closing confirmation.

Standing count line (operator preference): **There are 2 failing tests unrelated to our present scope
(the pre-existing `TestRebuildingNoticeSeam` search_code notice-serialization fails). Do you want to
examine them more closely?**
