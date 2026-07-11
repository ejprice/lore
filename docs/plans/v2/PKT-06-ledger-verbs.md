# PKT-06 — Orchestration ledger verbs (approved row f38f3b96)
size ~0.30 wu · wave C · depends: none (operator-sequenced after detection)
law: DESIGN-LAW §8 (pull-only; L5 rejected), §5 (hot-row minting) · DEPLOY: yes

## Mission
The operator-approved fleet-coordination verbs — **zero new tools**, actions on the
existing lore_tasks/lore_findings surface. Design source:
docs/orchestration/2026-07-06-orchestration-context-retro.md:60-86 (L-series).

## Approved scope (build all four)
- **L1** `lore_tasks action=rollup` — ONE cursor-based call: "since <cursor>: N tasks
  transitioned (ids→states), M findings filed (numbers+subjects), K reports registered
  (paths + summary lines)". Compact render, never dumps (DESIGN-LAW §8).
- **L2a** `lore_tasks action=create_many` — batch create with deps wired.
- **L2b** `lore_findings action=resolve_many / acknowledge_many` — with per-item notes.
- **L3-lite** `report_path` + `summary` fields on the done-transition (the durable
  analogue of completion messages; the rollup carries them).
  **Lead proposal (2026-07-11 gap-2/#9 discussion, rule at build): `summary` is
  MANDATORY on done** — a done-transition without one is rejected like claimed→done.
  Rationale: operator ruling that author discipline is not a capture mechanism; the
  done-summary is the fleet's episodic memory and optional fields get skipped.

## Candidates — RULED (operator, 2026-07-11)
- **L4** `lore_tasks action=await` (bounded wait on a ledger condition; thin wrapper on
  the LIVE SELECT machinery). From the retro; NOT in the approved C0 row.
  **RULED BUILT (operator, 2026-07-11):** await is approved. It satisfies this packet's
  "L4 requires operator ruling" clause, but it is built in the agent-comms subsystem as
  `lore_comms action=await` (PKT-28 **C3**, the L4/LIVE leg — Opus 4.8 builder), NOT in
  C0. PKT-06/C0 ships without await.
- **ack/acked_at** for must-not-lose signal acknowledgment (comms-research
  recommendation, docs/orchestration/2026-07-04-agent-comms-failures-research.md:56).
  **RULED BUILT (operator, 2026-07-11):** acknowledgment is approved — realized as
  write-once `acked_at` CAS stamps on the `to` delivery edge + `lore_comms action=ack`
  (PKT-28 **C2**), not a column on the task row. `grade=directive` messages require ack.

## Do not re-propose
A push message-bus (L5) — REJECTED with rationale on record (DESIGN-LAW §8).

## Entry check
`lore_tasks` row f38f3b96 carries the full approved description — read it; claim it.
State machine law: claimed → in_progress → done.

## Exit
Full gates + cold audit; deploy BOTH; smoke: create_many with deps → claim → done with
report_path/summary → rollup returns the whole arc in one call; instructions/tool
descriptions teach the new actions (structural pins in test_mcp_server.py updated in
step); INDEX row + Log.
