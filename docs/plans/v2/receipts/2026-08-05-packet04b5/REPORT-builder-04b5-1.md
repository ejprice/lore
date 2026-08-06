# REPORT-builder-04b5-1 — packet 04b5 Link-5 render-site injection containment (the build)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`,
no #334 flake); registered `builder-04b5-1` (session pkt04b5) + drained (empty inbox). Full
tool access — Edit/Bash/pytest/mypy/ruff all present; delegated the test_mcp_server.py ripple
to an `opus48-worker` (different file, no worktree needed). No lore weakness forced a
route-around; nothing filed. Grep used for the bare-anchor-free `!r` sweeps and fence-site
exhaustiveness (CLAUDE.md dogfood case (a)/(b) — non-symbol textual seams + rename
exhaustiveness); said so per use.

## SUMMARY BLOCK
- **state: done-with-deviations** — the FULL 04b5 contract is GREEN (the #133 discharge);
  render/error ripple closed. Deviations below.
- deviation 1: I widened **`render_join`** (not only `render_line`) to accept `Rendered`
  values — the comms fleet-row cells route door values through `render_attributed` inside
  `render_join([...])`, so its `parts` type needed the same widening as `render_line` (brief
  named only `render_line`). Type-only widening; return stays `SafeLine`.
- deviation 2: I made **`render_attributed(value: object)`** (not `str`) — it stringifies via
  the existing `safe_str` seam. 60+ caller values are `str | None` / `int | str` (e.g.
  `id_or_number`, `spawned_by`); accepting `object` lets the ONE seam own the stringify (the
  `safe_str` precedent) instead of coercing at every call site. Contract only ever drives str;
  behaviour on str is identical.
- deviation 3: I updated **`tests/_task_fakes.py`** (4 done-summary error strings) alongside the
  R3 test-pin update — my `tasks.py` routing made the `[real]` ledger diverge from the `[fake]`
  one; restoring [real]/[fake] parity forced the fake's 4 tested error strings through
  `render_attributed` too. Minimal (4 sites; the fake's other errors keep their own text —
  the fake is behavioural, not byte-identical, and no other test asserts them).
- deviation 4: `_render_recalled_memories` — `memory.text` is now a **fenced block on its own
  line** (`"- memory:"` header + `render_fenced`), because `render_fenced` MUST be
  newline-framed (WB-8: `f"- {render_fenced(x)}"` breaks the fence). The lead ruled render_fenced
  for `memory.text`; the framing is the only way to satisfy it.
- **Packages considered:** none new — `render_attributed`/`fence_width` are the in-house
  composition the ruled design specifies (ONE-IMPLEMENTATION extraction of the existing
  `sanitise` primitives, not a hand-roll of anything a package provides). READ: `render.py` /
  `sanitise.py` installed source (the seam I extended). Verdict: `bespoke-by-in-house-composition`
  (per design-sidecar-04b3-1 §B Packages line).
- **Graded:** n/a — I authored code, I did not render a verdict on another artifact. (The
  contract is the grader; I made it green.)
- decisions-needed / STOP-and-flags: **none blocked the build.** One noticed residual raised for
  the operator (§RESIDUALS): `tasks.py`'s bare-`ValueError` `{target!r}` at the non-done
  summary/report_path guard — a caller `target` reprd into a served error the contract's ERROR
  scan deliberately bounds OUT (bare ValueError, not a domain error). Left un-routed to keep the
  contract's partition coherent; flagged, not silently dropped.
- receipt pointers: milestones + SHAs §MILESTONES · gate receipts §GATES · the two routing rules
  §ROUTING-RULES · ripple §RIPPLE · residual §RESIDUALS.

---

## §MILESTONES (commit SHAs, explicit pathspec per #191)

| M | what | commit |
|---|---|---|
| M1 | `sanitise.fence_width(text)->int` extracted (the ONE width policy, #102); `render_fenced` consumes it | `a68d3e0` |
| M2 | `render.render_attributed(value)->Rendered` inline seam; `render_line`/`render_join` widened to accept `Rendered` | `a68d3e0` |
| M3 | 63 served domain-error doors routed through the seam (7 modules); R3 ripple pins (`TestDoneSummaryReportPath` + `_task_fakes` parity) | `a68d3e0` |
| M5 | search.py fence construction routed fully through `render_fenced`; private `_fence_width` retired; byte-preserving | `a68d3e0` |
| M4 | render half — every `_render_*`/serving-helper door routed; full contract GREEN; comms/wiring ripple | `55865a1` |
| M6 | `test_attribution_bound.py` retirement confirmed (already deleted `969fa1c`); stale `_render_task_detail` docstring prose updated | `55865a1` |
| — | test_mcp_server.py ripple (delegated) + close-out | _(pending final commit)_ |

## §ROUTING-RULES (measured against the contract's `_leaks` oracle — receipts, not assertion)
1. **`render_attributed(x)` embedded in an f-string is byte-safe** regardless of surrounding
   text — its inline backtick delimiter is self-closing (sized to the content's runs), and the
   `_leaks` predicate's symmetric backreference strips it. So inline door fields route as
   `f"...{render_attributed(x)}..."`. (The brief's demotion warning is about the `Rendered`
   TYPE being lost, not the bytes; for the RUNTIME byte-diff proof the bytes are contained.)
2. **`render_fenced(body)` MUST be newline-framed** — `f"- {render_fenced(x)}"` (prefix on the
   fence line) and `f"x {render_fenced(x)} y"` (inline) both LEAK (WB-8), because the fence's
   opening/closing lines stop being pure-backtick lines. So bodies route as `...\n{render_fenced(body)}\n...`.

## §GATES (receipts)
- **FULL 04b5 contract GREEN — the #133 satisfiability discharge:**
  `pytest tests/test_link5_render_containment.py tests/test_task_read_surface.py -n auto` →
  **251 passed, 1 skipped, 0 failed** (at `55865a1`). The render-containment half alone: 153 passed.
- **mypy:** `scripts/typecheck.sh` → 102 errors, **ALL in auth-WIP files (#333), ZERO in any
  file I touched** (production `mypy loremaster` clean but for the pre-existing unrelated
  `calibration.baseline` double-module error). Added zero new.
- **ruff:** clean on every file I touched (`ruff check` → All checks passed).
- **Changed non-04b5 suites green (zero new failures beyond the intended greening + P8d pin
  updates):** task_ledger/findings/agent_registry/message_ledger/memory_*/impact/symbols/
  store_read (995+629 passed across sweeps); all comms suites (footer/fleet_grouping/tool/
  render_architecture/promise_registry/wiring/schema — ripple fixed, green); server/extension/
  query_tasks_bounded/blocks_edge/sanitise/workspace_status/brief_ledger/cycle_write_path/render
  (629 passed); diff/map/scout/read_file (142 passed).

## §RIPPLE (P8d — served bytes changed → OLD-WORLD pins updated to NEW contained output)
Every updated pin DERIVES its expected via `render_attributed(value)` (never a hardcoded
delimiter width — that would go stale) and PRESERVES its safety assertion.
- **R3 (error half):** `test_task_ledger::TestDoneSummaryReportPath` (4 exact-text pins) +
  `_task_fakes.py` parity (4).
- **render half:** `test_comms_tool` (question-teach thread, brief publisher), `test_comms_
  render_architecture` (publish author), `test_comms_promise_registry` (thread-teach marker),
  `test_comms_wiring` (register role, brief author, fleet-row role, publish author).
- **test_mcp_server.py** (rollup/resolve-many/create-many/filter-miss/tier-miss renders):
  delegated to `opus48-worker` — _result pending._

## §RESIDUALS (surfaced, not dropped — operator owns scope)
- **`tasks.py` non-done-summary guard `{target!r}`** (a bare `ValueError`, not a domain error):
  a caller `target` reprd into a served error. The contract's ERROR-half scan
  (`TestNoServedDomainErrorLeavesACallerParamUncontained`) deliberately bounds bare `ValueError`s
  OUT (its named bound (3)); I left it un-routed so the ERROR partition stays coherent. It is a
  real (low-stakes, per-caller self-echo) door. **Fix-now-vs-defer is the operator's call** —
  routing it is one edit + updating any exact-text pin; it changes the served bytes of that one
  refusal.

---
_Authored by `builder-04b5-1` (Opus 4.8) against `55865a1`. The test_mcp_server.py ripple line
and the final close-out commit are appended after the delegated worker's result is
ground-truthed (operator law: a subagent's "done" is a claim; I re-run its file myself)._
