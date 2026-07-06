# lore — project process law

Standing rules for every session in this repo. Distilled from operator rulings and
audited failure patterns (P7–P8d); the phase resume docs in `~/.claude/plans/` carry
*phase state only* — process law lives here.

## Quality gates (operator-ruled, every commit)
- `scripts/typecheck.sh` — zero mypy errors including test trees. This runner is
  canonical; a single combined `mypy` invocation false-errors on `tests.conftest`.
- `uv run ruff check .` — clean. The PL family is live under the 2026-07-05 curation
  (PLC0415/PLR0913 ignored as house idioms; PLR2004 prod-only). Real pylint is
  upstream-blocked (astroid<4.1 pin) — do not install it.
- pydantic at every validated boundary; models stay `extra="forbid"` on the wire with
  resilient *construction seams* (`from_engine_status` pattern) — never loosen the model.
- Full suite (~11 min) is lead-run at checkpoints only; agents run scoped tests.
  ⚠ A piped pytest with a bad filename exits "no tests ran" silently — a green claim
  requires a passed-COUNT in the tail.
- Skill tests have their own idiom: `cd skills/lore-deploy/scripts && uv run python -m
  pytest -q . ../tests`.

## Using lore's own tools (the dogfood protocol)
lore-first is the default for code-structure questions — but trust requires currency,
so the protocol is: **check, then trust**.
1. Freshness first: `lore_index()` renders last_sync/last_sweep ages. If your session
   has edited files since those stamps, run `lore_index(reconcile=True)` (cheap,
   idempotent) before trusting graph-derived answers (impact, dead_code liveness,
   covering tests). Never use a possibly-stale impact result as a deletion gate —
   reconcile first (finding #46 was a near-miss).
2. Then lore-first: lore_search / lore_get_symbol / lore_impact / lore_read for
   definitions, semantic where-is, consumer sets, covering tests, spans.
3. Grep remains honest for exactly three cases — and the agent SAYS SO in its report
   when it falls back: (a) rename/await-migration exhaustiveness where one missed
   site compiles-but-breaks, (b) non-symbol textual seams (config keys, log event
   names, prose in string literals), (c) cross-cutting multi-question maps.
4. Friction files through `lore_findings action=report` (REQUIRES category, area,
   created_by). Routing around a lore weakness without filing it is the one
   unacceptable move.

## Rename/reshape sweeps (audited failure pattern, P8d — 3 of 4 confirmed defects)
Confirmed green-at-gate defects cluster in *natural-language surfaces whose consistency
with code no gate checks* (error prose, tool descriptions, instructions claims,
rendered free text). Therefore:
- Sweep greps for retired names use BARE, anchor-free patterns (no `lore_` prefix
  anchor, no call-paren anchor) — prose mentions don't carry structural anchors.
- "All remaining hits are X" is banned output. Every residual hit gets a file:line +
  one-word verdict, individually.
- Tests written before a semantic change certify the OLD world: on any rename, grep the
  test tree for assertions pinning retired names/strings — a green suite may be green
  because it still asserts the corpse.
- Any NEW render of stored free text (finding bodies, memory notes, task subjects)
  routes through the shared sanitiser seam (`loremaster.search._sanitise_line` until
  finding #34 promotes it) — multi-line stored text renders inside a backtick fence.
  Its tests MUST include a hostile fixture (newlines + a row-shaped forgery line +
  backtick runs). Single-line-only fixtures are the documented way these defects
  stayed green.
- Structural pins guard the served surface: the exact-set registration pin, the
  dead-name hygiene scan, the instructions-names-every-tool pin (all in
  test_mcp_server.py). Every audit-caught defect CLASS gets converted into a pin like
  these — a fix without an invariant is half a fix.

## Orchestration (multi-agent phases)
- The lead writes no code — tests included. Ladder: ground-truth verify → TaskStop →
  respawn fresh (never reuse a teammate name).
- Directives travel ONLY in fully-front-loaded spawn briefs; the inbox is advisory
  both directions; proof of receipt is the recipient's artifact (or its process on
  the process table). An idle agent with a live gate-pytest + self-watcher is the
  benign waiting-on-own-wake mode — do not double-drive it.
- Briefs use the versioned base protocol: the agent's FIRST action is
  `Read ~/.claude/orchestration/brief-base.md`, and its report opens with the
  `brief-base v<N> read` receipt (missing receipt ⇒ treat as unbriefed). The brief
  itself carries only: identity/mission, writable-set + do-not-touch, task-specific
  steps/receipts, the lore ToolSearch load line, and any override of the base. This
  repo's specifics (gates, dogfood protocol, store idioms below) ride THIS file —
  never re-transcribed into briefs. Store idioms: CONTENT for protected-key writes
  (`session` is protected); str(RecordID); statement[0]-only validation; CONTENT
  datetimes are Python datetimes; missing SELECT-projection reads None; time:: family
  for datetime aggregates under GROUP BY.
- Reports: REPORT-<agent-name>.md at repo root, EXACT name; delete all before any
  image build. One concern per commit; cold REFUTE audit before every wave commit
  (builder ≠ grader; P8d receipts: 3 of 4 waves shipped a defect green at every
  builder gate and only the cold audit caught it).
- Lead context checklist (P8d retro + fresh-Fable review, 2026-07-06): consume report
  SUMMARY BLOCKS first — Read(limit≈40) — and the body only for rulings/audits; point
  briefs at spec/scout files, never transcribe them; agents drive their OWN ledger
  rows (brief names the id); a stale notification for a stopped agent gets zero tool
  calls; keep design/spec authorship in dedicated design agents, consumption by
  pointer. Resume docs carry PHASE STATE ONLY — process law lives here.
- Verification law (operator-amended 2026-07-06, F3): for AUDITED work, the cold audit
  is the ground-truth instrument (it re-runs gates/probes); the lead keeps judgment
  reads + one random receipt re-run per batch. For anything committed WITHOUT a cold
  audit, the lead verifies in full: re-run the tests, read the diff, confirm the
  number. The global Working Discipline carries the canonical wording.
- lore_tasks state machine: claimed → in_progress → done (claimed→done is illegal).

## Deploy
- Rebuild + recreate, never restart, after loremaster changes (the container bakes the
  code; the mount is read-only reference). Capture `podman inspect <name> --format
  '{{.Config.CreateCommand}}'` BEFORE rm. lore-lore boots ~150s (eager), DI ~5s.
- smoke_p8b full mode files a dogfood finding row each run — resolve it as a smoke
  artifact (duplicate of #1), not a live defect.
- spike-surreal ws://127.0.0.1:18000 is the test store; :18500 is production
  lore-surreal — never point tests at it. Post-reboot: `podman start spike-surreal`.
