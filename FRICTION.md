# Lore friction log

Live dogfood record of every point where an agent (or the team-lead) hit a lore
limitation and worked around it. **Doctrine: if a lore call forces a workaround,
log it here FIRST, then work around.** Entry shape deliberately mirrors the
planned P8 `kind=friction` finding (plan §3 "Friction reporting"), so this file
seeds the findings table when that lands and retires afterward.

Harvest protocol (team-lead): subagent reports carry a `FRICTION:` line when a
lore call disappointed; the team-lead appends entries at each cycle close and
consumes open entries when specifying the NEXT cycle — friction found while
building phase N feeds the design of phase N+1, not a backlog.

Entry fields: date · reporter · tool · intent · what happened
(zero_hits | error | wrong_result | too_stale | distrust_unverified |
capability_gap | affordance_gap) · workaround taken · disposition (open /
consumed-by-<phase or commit> / superseded).

---

## Open

- **2026-07-03 · team-lead · (whole surface) · distrust_unverified** — avoided
  lore for an entire heavy build session on an unmeasured staleness prior;
  later measured FALSE (90-minute-old `CommandSubscriber` resolved perfectly,
  0 in-flight). Workaround: grep/subagent sweeps all session. Root cause:
  freshness is pull-only (agent must remember to ask `index_status`); trust
  decays on priors when nothing pushes freshness into results. **Feeds:** P6
  read-path — per-result staleness flags + `wait_for_fresh` are the fix;
  keep them visible in EVERY result, not opt-in.

- **2026-07-03 · team-lead · lore_search_code · capability_gap** — P5's
  discovery questions were structural seam-sweeps ("every call site of the
  sync manifest," "which tests pin this behavior," "what breaks if X changes")
  that flat semantic hits cannot answer in one shot; v0.3's graph tools cover
  single edges (what_imports/tests_for) but not budgeted multi-file maps.
  Workaround: Explore/scout subagents + grep (thousands of tokens per sweep,
  every session). **Feeds:** P6/P8 — this is the live justification for
  lore_map / lore_impact rollups; measure them against exactly these three
  question shapes.

- **2026-07-03 · team-lead · (tool loading) · affordance_gap** — the lore MCP
  tools are deferred behind a ToolSearch load; any brief that doesn't pre-solve
  that one-line load loses to grep by default (grep is always loaded). Subagent
  briefs never mentioned lore → subagents never used it. Workaround: none
  (tools simply unused). **Feeds:** process (the lore-first TOOLS block in
  every brief — in force as of today) + P8 doctrine: the instructions block
  must assume deferred loading and say so.

- **2026-07-03 · team-lead · graph tools · affordance_gap (self-inflicted doc gap)** —
  the team-lead mis-scoped v0.3's own graph surface, attributing "structural
  seam-sweeps" wholesale to grep/Explore when `references`/`what_imports`/
  `blast_radius`/`tests_for` chains answer most symbol-level sweep questions at
  function granularity. The tool's own steward underestimated it → typical
  agents will too. Workaround: none (capability unused). Root cause: no single
  affordance says "chain these four for a seam map." **Feeds:** P8 tool
  descriptions + instructions block (teach the CHAIN, not just the tools);
  P6 lore_map/lore_impact are the one-call ergonomic. Residual truth: astroid-
  inference bounds mean exhaustiveness checks (renames/await migrations) still
  need mypy/grep verification — document that boundary in the tool text.

## Consumed

*(none yet — entries move here when a phase/commit addresses them, with the
commit/phase reference appended)*
