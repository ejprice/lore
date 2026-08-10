# REPORT — builder-server (Opus BUILDER, packets B/#345+#348 + C/#291, session 2026-08-09-fix-344-345)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **state: done-with-deviations.** Both RED contracts GREENed by production+test code; no adversary phase (cold audit follows).
- **C (#291):** RED 13/5 → GREEN 18/0. Shipped `loremaster.server.partition_tools_by_posture(tools)->(mutating,read_only)`, deny-by-default (`readOnlyHint is not True` ⇒ mutating), single source of truth; wired `test_mcp_server.derive_tool_postures` and **retired** the drifted `_MUTATING_TOOLS`/`_READ_ONLY_TOOLS` hand-lists.
- **B (#345/#348):** RED 2/13 → GREEN 15/0. Contained the fleet-row `task_id` via `render_attributed` (Ruling 4.1); populated `_SERVED_SAFE_FIELDS` with the 9 genuinely-safe fields (evidence + re-open triggers); moved `task_id` safe→door in `_manifest` for Agent+Message (Ruling 4.2); fixed the B-3 false-safety comment (Ruling 2). Leg-2 comprehension-awareness was already shipped by reviser-asub-b — verified GREEN, no builder action.
- **deviation 1 (PROMINENT — writable-set):** edited `test_link5_render_containment.py` (NOT in the stated writable set) — the `_manifest` Agent/Message correction + fleet-row probe `task_id` hardcode removal. **Directed by the brief's own B task step** ("move `task_id` safe→door in `_manifest` for Agent+Message") **and operator Ruling 4.2.** The writable-set list omitted this file; the task step is authoritative. No sibling touches it. Full test_link5 suite re-run GREEN (158/0). See §DEV.
- **deviation 2 (PROMINENT — writable-set):** edited `test_comms_promise_registry.py` (NOT in the stated writable set) — removed ONE dead `_SAFE_STR_PROMISE_FREE` entry (`"{}…"`). This is a regression my in-scope server.py change **directly caused** (the fleet-row `safe_str`→`render_attributed` swap stopped emitting that safe_str literal); brief-base §2 permits a minimal fix + prominent disclosure. See §DEV.
- **Packages considered:** none — reused the existing `render_attributed`/`safe_str`/`render_join` seam (no hand-roll), and stdlib set-ops for the annotation partition; no library provides deny-by-default annotation partitioning. `bespoke` correct.
- **Graded:** built against HEAD `003a337` · work uncommitted (working tree) · the lead commits after the cold audit.
- **decisions-needed:** none (all forks pre-ruled: Ruling 4 = contain fleet-row `task_id`; Ruling 5 = field-name keying; Ruling 2 = `blocked_by` door). The two deviations above are DISCLOSURES, not open decisions.
- **UNRELATED pre-existing failures:** `test_hosted_readonly_posture.py` (pkt39 WIP) = 57 RED at HEAD — its production deps (`auth.mode=google_oauth` config schema, `HOSTED_REFUSAL_SECTION_HEADING` symbol) are unbuilt. NOT caused by me; brief said do-not-touch pkt39 WIP. See §PKT39.
- **Receipt pointers:** §C · §B · §348 · §DEV · §GATES · §MUTATION · §PKT39.

---

## §C — INSTRUMENT C (#291), production derivation + retire the hand-list

**Production helper** — `loremaster/loremaster/server.py`, `partition_tools_by_posture` (module-level, right after the `*_ANNOTATIONS` constants, before `_register_tools`). Pure function of the registered tools' annotations; `readOnlyHint is True` ⇒ read_only, everything else (incl. `None`/unannotated) ⇒ mutating (DENY-BY-DEFAULT). Matches the contract's own `_spec_partition` oracle exactly. Its docstring states the caller-supplies-unscoped-set bound (the packet-39 fold-in). Does NOT end in `_ANNOTATIONS`, so it does not pollute the contract's `_live_annotation_constants()` surface.

**Test wiring** — `loremaster/tests/test_mcp_server.py`:
- Imported `partition_tools_by_posture` from `loremaster.server`.
- **Deleted** `_READ_ONLY_TOOLS` (9-name literal) and `_MUTATING_TOOLS` (drifted 4-name literal). Replaced with a `derive_tool_postures(tools)` helper routing through the production helper.
- Rewrote `TestToolAnnotations.test_read_only_tools_are_marked_read_only` / `test_mutating_tools_are_not_marked_read_only` to derive the partition and assert non-empty + per-member annotation coherence.
- **Honesty note:** these two `test_mcp_server` tests are now coherence checks (no drifted hand-list). The INDEPENDENT behavioural oracle for the split — `EXPECTED_MUTATING_TOOLS`/`EXPECTED_READ_ONLY_TOOLS` (named, not derived), deny-by-default, and the ∀-liveness mutation proof over every `*_ANNOTATIONS` constant — lives in `test_mutating_set_derivation.py` (the C contract), which is where #291's real coverage now is. This is the DRY-#1 resolution the lead ruling asked for: one production source of truth, no second list beside it.
- The C contract's `test_no_drifted_hand_list_survives_beside_the_derivation` now passes because both literals are gone (its `getattr(..., None)` → no-op).

**RED→GREEN:** `test_mutating_set_derivation.py` 13 failed/5 passed → **18 passed/0**; `test_mcp_server::TestToolAnnotations` **3 passed**.

## §B — INSTRUMENT B (#345), render-slot containment

**Leg-2 offenders at HEAD (10 fields):** `agent_name, chunk_key, id, ids, name, ref, sender_name, session, superseded_by, task_id`. **Leg-1 offenders (9):** the same minus `task_id` (already observed-with-content via `InboxEntry.task_id` in the drain-row over-drive). Resolution:

- **9 genuinely-safe fields → `_SERVED_SAFE_FIELDS`** (in the B contract file, writable). Each entry carries an evidence class (charset-gated identity via `AGENT_NAME_PATTERN` / opaque system-minted id / system graph-walked id / system-minted ref) + a named re-open trigger. Verified none is a manifest DOOR name (the mis-park pin `TestNoServedSafeFieldIsAManifestDoor` passes). Fixes both Leg-1 and Leg-2 for these 9.
- **`task_id` → CONTAINED, never SAFE-listed** (it is a DOOR via `InboxEntry`; the mis-park pin forbids allowlisting it). Production fix in `_render_comms_fleet_row` (Ruling 4.1): `render_join(" ", [safe_str("task"), render_attributed(row.task_id[:8] + "…")])` — was `safe_str(row.task_id[:8] + "…")` (same-line-forgery-blind). Drop-in consistent with the role/model/note cells. Leg-2's element-wise `_value_is_contained` recognises it as CONTAINED.

**Leg-2 comprehension-awareness:** already implemented by reviser-asub-b (`_value_is_contained` in the B contract). VERIFIED working — `test_the_real_blocked_by_render_is_element_wise_contained`, `test_leg2_recognises_elementwise_comprehension_containment`, `test_leg2_recognises_str_join_containment` all GREEN; the real `_render_task_rows` `[render_attributed(blocker) for blocker in task.blocked_by]` classifies CONTAINED with no `blocked_by`-SAFE entry. No builder action was needed here.

**B-3 comment (Ruling 2):** rewrote the `_render_task_rows` docstring (server.py) — `render_attributed` is now stated as the PRIMARY, REQUIRED containment; the list-`repr()` escaping is named a FRAGILE secondary property that a join-into-prose refactor would defeat. Removed the "NOT live-forgeable" / "defense-in-depth" false-safety framing.

**RED→GREEN:** `test_render_slot_inventory.py` 2 failed/13 passed → **15 passed/0**.

## §348 — Ruling 4 fixes (the fleet-row `task_id` door + manifest honesty)

1. **Production (server.py):** `_render_comms_fleet_row` task cell now routes through `render_attributed` (above). LIVE fix — `Agent.task_id` is unconstrained caller free text (`AgentRegistry.register` stores it verbatim, length-bounded only).
2. **Manifest honesty (test_link5, deviation 1):** moved `task_id` safe→door in `_manifest`'s **Agent** and **Message** entries, replacing the false "system id / task-id ref" reason with the true "caller free text, length-bounded only — was MIS-CLASSIFIED". `Message.task_id` is latent (not served in a driven render) but a door by provenance.
3. **Probe (test_link5, deviation 1):** removed the fleet-row probe's `task_id="tid12345"` hardcode — the literal #345 artifact on a now-door field — so `_forge` drives `Agent.task_id` (drive-all-slots, §8 R3(a)). Truncation (`[:8]`) means the marker cannot survive to the served bytes, so the marker-based P-N is green either way; the discriminating regression pin is the B contract's Leg-2 AST scan (proven live in §MUTATION).

## §DEV — the two writable-set deviations (disclosed prominently)

**Both files are outside the brief's stated writable set** (`server.py, render.py, the two B/C contract files, test_mcp_server.py`). No concurrent sibling touches either (siblings: treescan on store/_logging_fixtures, scriptsgate on scripts/wave_gate/pcg, plus D/G packet files — none overlap).

1. **`test_link5_render_containment.py`** — the `_manifest` Agent/Message `task_id` safe→door correction + the fleet-row probe hardcode removal. **Directed by the brief's own B task step verbatim** ("move `task_id` safe→door in `_manifest` for Agent + Message") and by operator **Ruling 4.2**. The writable-set list omitted this file; this is a brief internal contradiction (task step vs list) resolved toward the explicit task step (spawn-brief content is authoritative per brief-base precedence). Verified safe: full `test_link5` suite re-run **158 passed/0** — `Agent.name` stays SAFE, `Agent.last_note` stays DOOR (manifest-non-vacuity pin green), branch-coverage unaffected, P-N green.
2. **`test_comms_promise_registry.py`** — removed ONE dead `_SAFE_STR_PROMISE_FREE` entry (`"{}…"`, the fleet-row truncated task-id ellipsis). A **regression my in-scope server.py change directly caused**: the `safe_str`→`render_attributed` swap stopped emitting that safe_str literal, so `test_no_dead_safe_str_free_entries` reddened. brief-base §2 permits a minimal fix + prominent disclosure. The sibling `"task"` label entry stays live (`safe_str("task")` unchanged).

If the lead prefers deviation 1 be a flag-only (not an edit), the exact edits are recorded above and can be reverted — but the brief's task step + Ruling 4.2 both direct them, and the honesty correction (a false "system id" reason on caller free text) is the exact served-English defect class this session exists to close.

## §GATES — receipts

- `test_render_slot_inventory.py` + `test_mutating_set_derivation.py`: **33 passed** (`-p no:xdist`).
- `test_mcp_server.py::TestToolAnnotations`: **3 passed**.
- Comprehensive batch (`test_render_slot_inventory` + `test_mutating_set_derivation` + `test_link5_render_containment` + `test_mcp_server` + `test_comms_promise_registry` + `test_render_seam_pins`): **982 passed** (`-n auto`).
- Blast-radius (`test_task_ledger` + `test_task_read_surface` + `test_comms_tool`): **1245 passed, 1 skipped**.
- Comms suites (`test_comms_tool`+`wiring`+`status_age`+`render_architecture`+`promise_registry`): **1083 passed** post-fix (was 1 failed pre-fix — the regression above).
- `uv run ruff check` on all 5 touched files: **All checks passed!**
- `uv run mypy loremaster/loremaster/server.py`: **Success: no issues found**. `uv run mypy` on the 4 touched test files: **Success: no issues found in 4 source files**.

## §MUTATION — the #348 regression pin is live

Reverted the fleet-row fix in server.py (`render_attributed(row.task_id[:8]+"…")` → `safe_str(...)`) in the real tree (with a `cp -a` content backup) → `test_every_uncontained_served_field_is_justified` (Leg-2) **RED**; restored from backup → **GREEN**. So a future revert of the containment reddens the B contract. Backup removed; `git diff` confirms server.py restored (fleet-row line = `render_attributed`).

## §PKT39 — pre-existing unrelated failures (flag)

`test_hosted_readonly_posture.py` (packet 39 WIP — the brief's "do NOT touch pkt39 WIP" + "packet 39 will CONSUME `partition_tools_by_posture` later") is **57 failed** and was RED at HEAD independent of my work. Two root causes, both pkt39 production dependencies not yet built (I touched neither config nor removed any symbol):
- `LoreConfig` rejects `auth.mode='google_oauth'` / `auth.google` (`extra_forbidden`) — the hosted-auth config schema is unbuilt.
- `ImportError: cannot import name 'HOSTED_REFUSAL_SECTION_HEADING' from 'loremaster.server'` — a pkt39 symbol that never existed at HEAD.

All failures die at config-validation / import, before any partition logic runs, so `partition_tools_by_posture` is not implicated. The file is byte-identical to HEAD (not in the working-tree diff).

**There are 57 failing tests unrelated to our present scope (all pkt39 WIP in `test_hosted_readonly_posture.py`, RED at HEAD). Do you want to examine them more closely?**

## §PROV — tooling

- lore tools: `lore_comms` (register/drain). Used `grep`/`ast` reads over the test tree for the offender-field census and cross-cutting consumer sweeps (non-symbol textual seams + cross-cutting maps — the honest grep cases per the dogfood protocol); lore used for the tool schema load. No lore weakness to file.
- Real-tree mutation proof used a `cp -a` content backup + restore (no worktree). No scratch tree, no worktree to abandon.
