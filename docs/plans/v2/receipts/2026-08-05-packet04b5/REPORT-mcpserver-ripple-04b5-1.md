# REPORT-mcpserver-ripple-04b5-1 — test_mcp_server.py render ripple (04b5)

> **PROVENANCE:** authored by the `opus48-worker` delegated by `builder-04b5-1` for the
> test_mcp_server.py P8d render ripple. The worker's own `Write` was blocked by harness
> policy (subagents return findings as text), so `builder-04b5-1` transcribed the worker's
> report verbatim into this file to preserve it as a durable, citable artifact. The pass
> count below was **independently re-run by builder-04b5-1** (operator law: a subagent's
> "done" is a claim, not a sign-off) — see `REPORT-builder-04b5-1.md` §GATES for that receipt.

**brief-base v10 read**

## SUMMARY BLOCK
- **state:** done
- **Packages considered:** none — no mechanism specified (test-expectation fixup only).
- **Graded:** N/A — RED→GREEN test fixup, not a verdict. Worked at HEAD `55865a1`
  (`feat/surreal-unification`); only `loremaster/tests/test_mcp_server.py` touched (+43 / −26).
- **decisions-needed:** none
- **receipt pointers:** pass count `645 passed`, exit 0 (§Receipts); seam
  `render.render_attributed`; routing sites server.py `_render_rollup`,
  `_resolve_or_acknowledge_many`, `_format_finding_ref`, `_create_many`.

## What changed
Only `loremaster/tests/test_mcp_server.py`. Packet 04b5's containment seam
`render_attributed(value) -> Rendered` wraps caller-origin door fields in an inline backtick
delimiter (`safe_str(value)` then a `fence_width`-sized delimiter each side). The `_render_*`
methods now route their door fields through it, changing served bytes; the OLD-WORLD
exact-output pins disagreed. Each RED pin's expected string was updated to the NEW contained
bytes, **DERIVED via `render_attributed(...)`, never hardcoded** — the fence width varies (both
hostile fixtures carry a run of 4 backticks, so their delimiter is 5, not 3).

Added one module-level import `from loremaster.render import render_attributed`. Removed two
now-unused local `from loremaster.search import _sanitise_line` imports in the two rollup
hostile tests.

**13 tests updated** (exact RED set from the pre-change run):

**TestRollupDispatch (7):**
- `test_since_omitted_bootstraps_from_the_epoch` — owner `me` → `render_attributed('me')`.
- `test_one_task_transitioned_and_one_finding_filed_render_both_legs` — task subject/owner +
  finding subject/kind/created_by wrapped.
- `test_superseded_task_in_leg1_renders_the_chain_marker` — subject `s` + owner `None` →
  `render_attributed(None)` (= `` `None` ``, since `safe_str(None)=="None"`).
- `test_leg3_report_row_names_the_report_path_when_given` — owner/summary/report_path wrapped.
- `test_leg3_report_row_names_no_report_file_when_absent` — owner/summary wrapped; `no report
  file` literal unchanged.
- `test_hostile_subject_stays_single_line_and_forges_no_row` — `expected_subject` now
  `render_attributed(hostile_subject)`; owner wrapped. **Safety asserts KEPT verbatim:**
  `len(lines)==6` and forged-row `not in lines`; `lines[2]` stays `==`.
- `test_a_corrupted_multiline_summary_stays_single_line_at_render` — `expected_summary` now
  `render_attributed(corrupted_summary)`; owner wrapped. **Safety asserts KEPT:** `len(lines)==7`,
  forged-finding `not in lines`, `lines[5]` still `==`.

**TestCreateManyDispatch (1):**
- `test_forward_and_backward_key_refs_resolve_to_minted_ids` — item subject + key wrapped; each
  resolved `blocked_by` element wrapped (`blocked_by {[render_attributed(contract_id)]}`); empty
  list stays `blocked_by []`. Minted `id` stays bare.

**TestResolveManyAcknowledgeManyDispatch (5):**
- `test_all_succeed_...`, `test_acknowledge_many_uses_the_acknowledged_verb`,
  `test_an_illegal_item_fails_without_aborting_the_rest`,
  `test_duplicate_refs_in_one_batch_process_twice`,
  `test_connection_loss_aborts_remaining_as_render_not_raise` — success-row actor
  `by slate-lead` → `by {render_attributed('slate-lead')}`. **FAILED/ABORTED rows UNCHANGED**:
  their refs are int finding numbers → bare `#<n>` (only a str ref routes through the seam); the
  `_sanitise_line(str(error))` FAILED tail is also unchanged.

## Not touched (verified still GREEN — observation)
Two hostile-fixture tests were NOT in the RED set and were left as-is; they assert with
substring/count checks (`in`/`not in`/`len`), not exact door bytes, so they survive containment:
`TestCreateManyDispatch::test_hostile_subject_in_create_many_stays_single_line` and
`TestResolveManyAcknowledgeManyDispatch::test_hostile_caller_ref_is_echoed_sanitised_in_a_failed_row`.

## Receipts
Pre-change: `13 failed, 632 passed in 109.68s`. Post-change (full file, exit 0):
`645 passed`. 632 prior passers + 13 fixed = 645; none lost, none newly red. Ruff:
`All checks passed!` on the edited file. No production code edited. No git state mutated.
