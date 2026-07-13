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
- **Run pytest with `-n auto` (pytest-xdist).** Measured 2026-07-12 on this box (64 cores):
  mcp_server+render_seam_pins went **846s → 88s (9.6×)** with an IDENTICAL pass count (666);
  live-store suites are stable across repeated parallel runs (178/178 × 3). Parallel is safe
  BY CONSTRUCTION, not by luck — the harness was already built for it:
  `_surreal_harness.unique_database()` mints `test_<pid>_<uuid4>` per test precisely so
  "a concurrent pytest process on the SAME server never collides on, or reaps, this
  database". Only the runner was missing.
- Full suite is lead-run **at phase checkpoints only** — before the deploy that ships the
  work, NOT after every fix wave. Between waves: the changed suites + the structural/AST
  pins. The cold audit already re-runs the gates as its own independent instrument; the lead
  re-running the same suite behind it is duplicated wall-clock, not verification.
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

## A DIAGNOSIS IS NOT AN INSTRUMENT (PKT-28 C1, ten instances, 2026-07-13)
This file ALREADY said defects cluster in "natural-language surfaces whose consistency with
code no gate checks". We knew. **We then shipped TEN more instances of exactly that class in
one phase** — wrong counts, wrong labels, a fabricated version, and three lines promising
mechanisms that never run. Knowing the failure mode changed nothing.

**Every other invariant here has a mechanical guard** — mypy for values/returns, AST pins for
template slots and mints, schema ASSERTs for the store, query-count pins for N+1s. **Served
English had none.** It was guarded only by whatever assertion a test author happened to write,
with whatever fixture value they happened to pick — and they picked the one value for which the
prose was true.

Therefore, standing law:
- **When a defect CLASS is identified, ship the INSTRUMENT in the same breath as the law.**
  A rule people must remember is not a guard; it is a hope. "Every audit-caught defect class
  becomes a repo-local invariant test" is already written above — this section exists because
  we wrote the law and skipped the instrument.
- **Prose that describes behaviour must be DERIVED from the behaviour, not re-stated beside
  it.** Renders take typed applicability (`auto_ack_at_register: bool`), never a name they
  compare. A role ("the standing brief") gets ONE accessor, not seven hardcoded lookups. Then
  changing the mechanism is a TYPE ERROR at every site that describes it, instead of a prose
  bug nobody can see. (The full root-cause analysis + the C2 step-0 plan: finding #104.)
- **Fixture factories must not default a parameter the code branches on.** `_brief()`
  defaulting to `name="project"` MANUFACTURED this blind spot: every render fixture silently
  tested the one value where the lies were true. No default ⇒ every call site must choose.

## Every artifact gets an adversary — not just the code (PKT-28 C1, 2026-07-12)
C1 shipped FIVE defects that no builder gate caught. Their provenance, measured: THREE
were tests that were never written (fleet grouping, the `brief_counter` declaration,
every count above the display cap — no contract fixture exceeded small-N); ONE was a
SPEC that prescribed the bug (§5.1 specified a retry jitter derived from the CONTENDED
ROW's id — identical across racers — and justified a 4-retry budget with "contention is
≤2-way" while the contract pinned 8-way); ONE was a real gate that FIRED and a builder
talked itself past. Only the code had an adversary. The spec, the contract, and the
brief each had exactly one author and zero graders — and every defect was born in one of
them. Therefore:

- **Cold-audit the CONTRACT, before the builder starts** — invoke the reusable
  `contract-adversary` agent (`~/.claude/agents/contract-adversary.md`, Opus; the role's
  full spec lives there — do NOT re-transcribe it into briefs, just point at it and add the
  project-specific landmines). A fresh Opus adversary reads
  the contract + the spec and reports what the contract does NOT test: boundary and
  SCALE cases (0, 1, cap−1, cap, cap+1 — the N>cap fixture nobody wrote), every-branch
  reachability (a branch no test reaches is dead code waiting to be discovered by an
  auditor), concurrency DEGREE (≥8-way, never 2-way), hostile input, and whether each
  fake can actually FAIL. It grades the tests, not the code. This is cheap: the missing
  fixtures cost one function each to write — they were expensive only to THINK OF.
- **A failing test is a STOP. "Flaky" is not a builder's verdict to render.** A builder
  may never downgrade a red test to flakiness and proceed; it escalates. The C1 mint
  defect failed ~4 of 5 runs, was called flaky, and shipped. Corollary: a single green
  run NEVER clears a concurrency test — require 20 consecutive (a lone green run gave
  the LEAD a false all-clear on that same defect).
- **Spec ambiguity is a defect, not a judgment call.** If a contract author finds itself
  CHOOSING between two readings of a spec sentence, that is an escalation — not a
  contract decision. Two C1 contract authors read one sentence opposite ways, both chose
  silently, and their suites contradicted each other.
- **Every load-bearing pin is mutation-proven**: break the production code, watch the
  test go RED, restore. A pin that cannot be demonstrated failing is not a pin. Every
  time this was demanded ad hoc in C1 it immediately exposed something.
- **FIXTURES MUST DISCRIMINATE — interrogate every one with "what WRONG build would this
  still pass?"** This single class has now produced a blocker THREE times, on two axes:
  1. **Small-N**: a collapsed tail holding ONE agent at ONE version makes `len()` ≡
     `sum()`, so a build counting VERSIONS instead of AGENTS passed 489/489 + ruff + mypy
     + the AST pins. No contract fixture had ever exceeded small-N — the same reason three
     of C1's five defects (all of which only appear past the display cap) were never tested.
  2. **Parameter-value MONOCULTURE**: all 37 `brief_publish` calls at the tool seam used
     `name="project"`, so a build that self-acks ONLY when `name == 'project'` passed the
     ENTIRE contract (832 passed, 0 failed, zero mypy delta) with the finding fully intact
     for every other name. **If the code can branch on a value, at least one pin must use a
     DIFFERENT value.**
  The generalisation: a fixture that cannot distinguish the correct build from a plausible
  wrong one is decoration. Ask what wrong build survives it — the answer is the pin you are
  missing.
- **The lead's brief sets the adversarial frontier — so the lead must not be the only
  imagination.** C1's contract writers found precisely what the briefs told them to look
  for, and nothing else. Delegate frontier-generation to the contract adversary rather
  than relying on the lead to enumerate it.
- **CONTRACT AUTHORS ARE OPUS (operator, 2026-07-12).** Roster: **Opus contract authors**
  · Sonnet builders · Opus contract-adversary · Opus cold code-audits · Fable lead + design
  consultant. Rationale, measured: the contract is where the thinking is and where the
  defects are born, and Sonnet contracts kept shipping the same *class* of gap — small-N
  fixtures that cannot discriminate. Twice: (1) the #94 contract went green (561 passed,
  exit 0) with the defect fully intact — every pin tested a new method *nothing required
  the code to CALL*; (2) both cap-boundary fixtures in the #96 contract held ONE agent at
  ONE version, so `len()` and `sum()` were indistinguishable and a wrong build passed
  489/489 + ruff + mypy + the AST pins. Building to a good contract is comparatively
  mechanical — that is where Sonnet stays. **The adversary is NOT retired by this change:**
  an Opus author is still its own only grader, and that is the structural fault this
  section exists to fix.

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
  lore-surreal — never point tests at it. Both stores are systemd/quadlet-managed
  (`~/.config/containers/systemd/{lore-surreal,spike-surreal}.container`,
  `WantedBy=default.target` + linger) and auto-start on boot — no manual
  `podman start` post-reboot. Manage via `systemctl --user {start,stop,restart}
  {lore-surreal,spike-surreal}.service`. Full teardown recovery (image + both
  stores gone): see memory `surreal-stores-systemd-managed`.
