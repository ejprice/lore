brief-base v11 read
brief project v7 read

# REPORT-builder-verbs-05b — BUILDER for #174 (supersede blocked_by) + #262 (register liveness notice)

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- role: BUILDER (Opus-4.8, `opus48-worker` frontmatter-pinned — **attest**). I edited PRODUCTION code + minimal test-support regressions; I did NOT touch the frozen contract tests.
- state: **done-with-deviations** — the FROZEN 26-test contract is GREEN (26 passed); all builder-obligation + directly-caused regressions fixed; gates green modulo the pre-existing #333 baseline.
- deviations (each a directly-caused regression fixed minimally per brief-base §2 scope-law exception, OUTSIDE the named writable set — disclosed here prominently):
  - **D1** `tests/_task_fakes.py::FakeTaskLedger.supersede_task` — added the `blocked_by` sentinel (INHERIT/CLEAR/REPLACE, deduped) lockstep with production. A double lacking its twin's param TypeErrors in every test that drives the fake (this was builder-obligation #1; auto-enforced by `test_mcp_server.py` + `test_comms_footer.py`).
  - **D2** `tests/test_link5_render_containment.py` — (a) updated the `_render_supersede_result` probe to the new 4-arg signature + added a forgery-carrying `successor_blocked_by` branch shape (builder-obligation #2); (b) added a driver + probe for the NEW render `_render_holder_liveness_notice` (the "reach is a checked variable" invariant `TestEveryRenderCandidateIsDrivenOrOut` reddens on any un-classified new render — NOT foreseen by the contract report, discovered + resolved here).
  - **D3** `tests/_surreal_harness.py` docstring counts 52→53 importers / 34→35 `connect_admin` callers. The NEW contract file `test_comms_register_notice.py` is both a harness importer and a `connect_admin` caller, so the AST-derived-count pin `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` went RED. This regression is caused by the **contract file** (not my production code); I fixed it because it blocks the wave's currency gate and the pin's own message sanctions "update this pin's patterns in the same diff". FLAG: strictly this is the contract's regression, surfaced late.
- Packages considered: **none** — both features reuse in-repo policy seams (no third-party mechanism). #174: `reject_unknown_rows`→stdlib `graphlib` (already `replace`d), `_refuse_a_cycle`/`_relate_fragment`/`_new_task_content` (in-repo). #262: `get_task`, `_select_rows_by_name`, `max(key=…)` (stdlib), the extracted STALE predicate. All INTERNAL/DRY — see DRY LEDGER.
- Graded: n/a (a build, not a verdict). All work @HEAD `c0071cd` on `feat/surreal-unification` (lore_index confirms watched root + ref).
- decisions-needed:
  - **Q1 (D3 ownership):** the harness-docstring count regression is the contract file's, not my production code's. I fixed it (2 numbers) to green the currency gate. Confirm this was the right call vs a contract-side fix.
- receipt pointers: DRY LEDGER §DRY; 26/26 §CONTRACT GREEN; mutation pins §ONE-IMPL PROOFS; gates §GATES; diff §DIFF SCOPE.
- delivery: durable notice = `lore_comms` #4127 → lead-05b (the record). Native `SendMessage lead-05b` was UNREACHABLE (no native teammate by that name — lead is a peer session); per comms discipline the ledger row + this report ARE the proof of delivery, not a native send.

---

## DRY LEDGER (one row per new symbol; searched BEFORE writing)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `AgentRegistry.resolve_holder` (agents.py) | `lore_search("resolve an agent by name retired-inclusive, pick most-recent-heartbeat, return None on miss (not raise on ambiguity)")` | `_resolve_row` (agents.py:539) — RAISES on ambiguity, EXCLUDES retired | **HAND-ROLLED** — `_resolve_row`/`get_agent` cannot fit (fork F1: raise-on-ambiguity + retired-exclusion conflates retired-holder with unknown). REUSES the raw fetch `_select_rows_by_name` + `_row_to_agent` beneath a distinct DISCLOSE policy; most-recent = stdlib `max(key=…)`. `get_agent` stays the seam ruling 5.3 governs. |
| `AppContext._heartbeat_is_stale` (server.py) | `lore_search("heartbeat staleness predicate: is an agent's heartbeat age past the stale threshold")` | only the inline `heartbeat_age_s > stale_after_s` in `_render_comms_fleet_row`; no shared fn | **EXTRACTED (ONE-IMPL)** — pulled the existing inline predicate into the ONE shared fn; fleet row + notice both call it via the CLASS. Proven shared by MUTATION (contract `test_both_surfaces_share_the_EXTRACTED_predicate`). Not a clone — the de-duplication itself. |
| `AppContext._holder_liveness_notice` (server.py) | `lore_search("compose an advisory note disclosing a task holder's liveness on the register surface")` | no existing helper (low-sim design-doc hit only) | **HAND-ROLLED** — the I/O orchestrator; REUSES `get_task` + `resolve_holder` + delegates rendering. No existing register-notice composer. |
| `AppContext._render_holder_liveness_notice` (server.py) | (same query as above) | no existing render formats holder-liveness for the register surface | **HAND-ROLLED** — pure render, SPLIT from the orchestrator to follow this file's `_comms_X`(I/O)→`_render_X`(pure) pattern + to make the containment invariant drive a pure render. The fleet render is a DIFFERENT format (`[status ⚠ STALE]` bracket vs the notice sentence); no reuse target. |

Params added (not new symbols): `blocked_by` on `TaskLedger.supersede_task` + `FakeTaskLedger.supersede_task`; `successor_blocked_by` on `_render_supersede_result`.

---

## CONTRACT GREEN (the frozen 26)

```
uv run pytest -n auto -q \
  loremaster/tests/test_comms_register_notice.py \
  "loremaster/tests/test_blocks_edge.py::TestSupersedeCarriesBlockedBy174" \
  "loremaster/tests/test_blocks_edge.py::TestTheMirrorHoldsAtEveryWritePath::test_the_SUPERSEDED_successor_INHERITS_predecessor_blocked_by"
-> 26 passed in 6.74s
```

---

## ONE-IMPL PROOFS (mutation, not inspection)

- **STALE predicate SHARED** (fleet + notice): `test_both_surfaces_flip_at_one_threshold` + `test_both_surfaces_share_the_EXTRACTED_predicate` → **2 passed**. The second monkeypatches `AppContext._heartbeat_is_stale` (always-False then always-True) and asserts BOTH the register notice AND the fleet row flip together — a private `age > threshold` clone in either surface would ignore the patch. Both surfaces call it via the CLASS (`AppContext._heartbeat_is_stale`), which is why the monkeypatch is seen.
- **Supersede routes through the SHARED blocker check**: `test_supersede_ROUTES_THROUGH_the_SHARED_blocker_check` (in the 26) neutralises `loremaster.tasks.reject_unknown_rows` and the inherited-superseded refusal DISAPPEARS — a private clone would keep refusing. Supersede calls `_reject_unusable_blockers` (→ `reject_unknown_rows`), not a hand-rolled check.

---

## #256 DOOR CLASS — PREEMPTED (no new guarded-CAS door)

My changes add NO new `except SurrealStoreError`-that-re-reads-state door. `_holder_liveness_notice` catches only `TaskNotFoundError` (a not-found→render, no store-error re-read); `resolve_holder` returns `None` on miss (no guard); `supersede_task`'s existing CAS door is unchanged (I only added `_relate_fragment` inside its existing `_apply`). `test_retry_seam.py` → **564 passed** (no `_GUARDED_CAS_DOORS` widening needed).

---

## GATES

- `uv run ruff check .` (FULL tree, incl. test files) → **All checks passed** (after fixing a PLW0108 the currency gate caught on my probe lambda — I had initially only ruff'd the 3 production files; lesson logged).
- `scripts/typecheck.sh` → RED, but **RED_ADJUDICATED** (owned by packet-39-pending-build per finding #333). **ZERO of my edited files appear in the mypy output** (grep-verified): every error is in the 11 auth/posture/roster contract files #333 enumerates. **ZERO-NEW vs #333 CONFIRMED.**
- `scripts/pending_contract_gate.py --currency` → **PASS — every claimed gate is GREEN or OWNED** (exit 0). ruff GREEN; typecheck RED_ADJUDICATED (191, owned packet-39/#333); pytest RED_ADJUDICATED (444, owned packet-39/#333). **No RED_ORPHANED** — my two transient orphans (a PLW0108 probe lambda + the harness-docstring count) are both fixed; the remaining RED is entirely the auth/posture baseline #333 enumerates.
- `test_retry_seam.py` → 564 passed.

## ZERO-NEW no-regression (affected suites, real + fake)
- `test_comms_footer.py` + `test_link5_render_containment.py` + `test_render_seam_pins.py` → **435 passed**.
- `test_mcp_server.py` + `test_task_read_surface.py` + `test_task_ledger.py` + `test_txn_contention.py` + `test_agent_registry.py` → **1170 passed, 1 skipped**.

---

## DIFF SCOPE

Production (writable set):
- `loremaster/loremaster/server.py` (R1 / finding #359, folded in post-cold-audit at lead's direction): the `lore_tasks` `blocked_by` tool-param DESCRIPTION now names `supersede` and teaches its OMITTED/[]/[ids] sentinel (was `create`-only) — served-English discoverability, no test (no teaches-pin exists; the cold audit caught it, not a gate).
- `loremaster/loremaster/tasks.py` — `supersede_task`: `blocked_by` sentinel (INHERIT/CLEAR/REPLACE), self-ref guard (`TaskCycleError`, names id + "supersede", covers explicit + inherited), shared `_reject_unusable_blockers` + `_refuse_a_cycle` over resolved deps, `_new_task_content(…dependencies…)`, `_relate_fragment` appended to the existing supersede `_apply` (RELATE after CREATE; CAS envelope preserved). Docstring Args/Raises updated.
- `loremaster/loremaster/server.py` — supersede dispatch threads `blocked_by` + reads back `successor.blocked_by`; `_render_supersede_result` gains `successor_blocked_by` (surfaced when non-empty, each id `render_attributed`); `_heartbeat_is_stale` extracted; `_render_comms_fleet_row` routes through it (via the CLASS); `_holder_liveness_notice` (I/O) + `_render_holder_liveness_notice` (pure render); `_comms_register` composes the notice (additive; task_id-None/self/unheld byte-unchanged); `TaskNotFoundError` imported.
- `loremaster/loremaster/agents.py` — `AgentRegistry.resolve_holder`.

Test-support (deviations D1/D2/D3, outside writable set — directly-caused regressions):
- `tests/_task_fakes.py`, `tests/test_link5_render_containment.py`, `tests/_surreal_harness.py`.

NOT touched: the frozen contract tests (`test_blocks_edge.py`, `test_comms_register_notice.py`, `test_mcp_server.py`). `test_retry_seam.py::_GUARDED_CAS_DOORS` NOT widened (no new door).
