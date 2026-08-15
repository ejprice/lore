# Kickoff — Packet 59: migrate MCP server → standalone `fastmcp` 3.x

**Purpose.** This is the launch brief for the packet-59 BUILD. The investigation, design, and
rulings are DONE and committed (`aad58e8`); the build has not started. Hand this to a fresh lead
session to run the build with the correct orchestration. It is a pointer document — it names
where truth lives; it does not re-transcribe it (re-transcription goes stale — that is itself the
comms doctrine below).

---

## 0. Status & mission

- **Mission:** swap lore's MCP server façade off the official SDK's `mcp.server.fastmcp` onto the
  standalone **`fastmcp>=3.4,<4`** (full umbrella, NOT `fastmcp-slim`). KEEP `mcp` for `mcp.types`.
  This delivers the `on_call_tool`/`on_list_tools` middleware substrate that packet 39's hosted
  read-only enforcement is authored on.
- **Priority:** operator-ruled **IMMEDIATE NEXT BUILD** (D2), ahead of the wave-D queue.
- **Hard constraint:** **MUST precede packet 39** (39's `Depends on` now names 59).
- **Deploy:** operator-ruled **STANDALONE** (D1) — rebuild+recreate + the in-image gate, proving the
  substrate swap in isolation, not co-mingled with 39. Pre-production status pre-authorizes it.

## 1. Read-first (ground truth — do not re-derive)

1. `CLAUDE.md` (auto-loads) — process/gate/dogfood/comms/deploy law. Governs everything.
2. **The design doc = the spec to build:** `docs/design/2026-08-15-fastmcp-3x-migration.md`
   (coupling→migration map §3, the two re-architectures + DUAL removed-behaviour inventory §5,
   acceptance gates §6, the spike-validation gates §6.6, packet-39 sequencing §7, escalation
   rulings §11).
3. `lore_recall("fastmcp migration")` — the DECISION memory + the spike MEASURED-facts memory.
4. **Receipts** (`docs/plans/v2/receipts/2026-08-15-fastmcp-migration/`): `REPORT-fastmcp-blastradius.md`
   (coupling inventory + §7 packet-39 forward-compat), `REPORT-handroll-inventory.md` (14 dispositioned
   hand-rolls), `REPORT-fastmcp-spike.md` (the VERIFIED GO spike), `REPORT-fastmcp4-changes.md`
   (4.0-later context), `REPORT-migration-author.md`.
5. Finding **#184** (`lore_findings get 184`) — the 03b refusal this migration RESOLVES (re-open
   trigger (b): packet 39 is the 2nd non-telemetry `call_tool` consumer; #102 shared-substrate law).

## 2. The build path (repo TDD law — do NOT freehand it)

Run the `tdd` skill's cycle: **DISCOVERY → CONTRACT → ADVERSARY → STUB → RED → GREEN → REFACTOR →
AUDIT**, then the **standalone deploy**. The CONTRACT phase PAUSES for operator review before any
implementation. Roster is **Opus end-to-end** (Opus contract author · Opus builders · Opus
contract-adversary · Opus cold audit · Opus lead); **Fable = the design sidecar** (§4 below).

**Spike FIRST (§6.6).** Three payoffs in the design are `[inferred]`, not proven, and are gated on a
migration spike BEFORE they are trusted — each with a NO-GO fallback:
1. the ~150-LOC lifespan DELETE (`_ProcessLifespanGuard`+`_EagerStartupLifespan`) — prove fastmcp
   enters `lifespan=` exactly once per process in the served (stateful) mode; **NO-GO ⇒ KEEP the guard**;
2. the Origin-ordering property — does `host_origin_protection` run BEFORE the `TokenVerifier`
   (packet 39's "zero outbound Google call" property)? NO-GO ⇒ outermost Origin layer stays bespoke;
3. `host_origin_protection` closes the today-open Host/DNS-rebinding gap (`transport_security` is unset).

**Acceptance gates that are NOT negotiable** (the source is a fiction — only the artifact proves it):
- the **in-image conformance run** (packet 01a instrument, #131/#139) — run the suite IN the deployed
  image, assert `loremaster.__file__` is site-packages;
- a **real uvicorn wire smoke** (the spike's transport shape) — incl. `serverInfo.version` ==
  `_resolve_version()`;
- the **two unmeasured bounds PINNED** (PIN-THE-MISS): the real Google-OAuth verification path
  (tokeninfo POST — the spike used a static verifier stand-in), and long-lived token-refresh;
- **D4 caveats:** the transitive `mcp` pin is BARE (no `[cli]` extra) — confirm nothing needs
  `mcp[cli]`'s deps; run the FULL collection once, gate = **zero-new-delta vs #333** (the 11
  packet-39 pending-contract files must still COLLECT).

## 3. THE COMMS DOCTRINE (how the fleet coordinates)

The authoritative text is `CLAUDE.md` (Orchestration) + `~/.claude/orchestration/brief-base.md`
(the versioned base protocol) + `lead-base.md`. The operative rules, so the lead runs them from
the first spawn:

- **The durable ledger is the content channel; native is a thin WAKE only.** Every agent's FIRST
  action is `lore_comms action=register` (session, role, `cadence`). Status, coordination, forks,
  and blockers route through `lore_comms` (bodies ≤4000 chars — put content in a report, ADDRESSES
  in `refs`). Native `SendMessage` carries only a wake to an **at-rest** agent, never content.
- **Proof of receipt is the recipient's own artifact** — a ledger transition, a report, an `ack` —
  NEVER a `SendMessage` success return, never an inbox read-flag (silent-loss bug #50779).
- **Never steer a BUSY builder** (push to a busy agent drops silently). Corrections are ONE
  single-item ping to an at-rest agent; if it doesn't land, `TaskStop` + respawn with a consolidated
  brief. **Never reuse a teammate name on respawn** (suffix it).
- **Front-load spawn briefs completely** — the brief is the only guaranteed-read channel. It
  instructs the agent to `Read ~/.claude/orchestration/brief-base.md` FIRST and open its report with
  the `brief-base v<N> read` receipt line. The brief carries ONLY: identity/mission, writable-set +
  do-not-touch, task-specific steps/receipts, the lore ToolSearch load line (`ToolSearch "+lore",
  max_results 20`), and any rule that OVERRIDES the base. It REFERENCES standing law; it never
  re-transcribes it.
- **The lead is the HUB.** Agents route questions they can't answer UP to the lead (`lore_comms send
  to=["<lead>"] grade=directive`); the lead relays to the right consultant (the Fable sidecar, or a
  scout) and returns the answer. An agent MAY try a direct ledger send to another registered agent,
  but must not BLOCK on it (idle agents don't self-drain) — the lead-relay is the reliable path.
- **Idle notifications are AMBIGUOUS** (done / waiting-on-own-wake / stalled / permission-blocked):
  ground-truth the filesystem (the expected artifact) before acting; a complete artifact is proof of
  done even without a signal; do not double-drive a waiting agent.
- **Reports:** `REPORT-<name>.md` at repo root during the wave → `git mv` into
  `docs/plans/v2/receipts/<date>-packet59/` at close-out (ARCHIVE, never delete; cite section-exact
  paths, never a bare `REPORT-*.md` or a scratchpad path).
- **The store reference is a required first read** for ANY store/schema/DDL touch —
  `docs/reference/surrealdb-31-capabilities.md`. (Packet 59 touches only `server.py` + deps; store
  touch is expected NONE — but if that changes, this rule binds.)

## 4. THE FABLE DESIGNER SIDECAR (forks & design questions)

Spawn a **Fable** design consultant to answer design/fork questions for the whole packet.

- **Spawn ONCE, as a general-purpose agent — NEVER a fork** (a fork inherits the orchestrator's
  identity; see memory `orchestration-fork-and-path-hazards`). Keep it **LONG-RUNNING for the whole
  packet** so follow-ups answer from already-loaded context.
- **Front-load its spawn brief:** the design-question surface for THIS packet (the middleware
  re-architecture §5a, the lifespan-DELETE spike design §6.6, the removed-behaviour adjudication, the
  Origin-ordering property, the "property-to-invent vs spec-to-implement" routing), the exact file
  pointers (the design doc, the receipts, relevant `DESIGN-LAW.md` sections, findings #184/#131/#139/
  #102), and the standing instruction to **STAND BY for follow-ups** after each answer.
- **Follow-ups travel via `SendMessage`** — sanctioned here because a standing-by consultant is AT
  REST between questions (the one shape native delivery is reliable for); its reply is its receipt.
  Its idle-between-questions state is BENIGN — never wake-loop it; exempt it from the idle-gate until
  its design doc is owed.
- **Its output is a DOC + a recommendation. The OPERATOR rules; the consultant decides nothing.** If
  a question is a genuine fork (a property to INVENT, not a spec to implement), it escalates to the
  operator — the Fable sidecar frames the fork, it does not settle it.
- If it must be respawned, **suffix the name** (never reuse).
- **Escalation valve:** the Fable sidecar is also the named escalation target for the INDEX triggers
  — two failed fix-waves at one gate · a production-touching surprise · unresolvable spec ambiguity ·
  a NO-GO with cross-packet residuals.

## 5. Constraints, sequencing, and deferred items

- **Dependency:** independent packet — touches only `loremaster/loremaster/server.py` + `pyproject.toml`.
  ∥-safe with 45–53/48/49. **Must land before 39 builds** (D3: 39's `Depends on` = `45, 48, 49, 59`).
- **Packaging (D4 ruled):** REPLACE `"mcp[cli]>=1.27"` with `"fastmcp>=3.4,<4"`; `mcp` rides
  transitively (bare, no `[cli]`). `mcp.types` becomes an undeclared-but-accepted direct import.
- **4.0 is a SEPARATE future packet** (§8) — do NOT chase the beta; its re-open trigger is the first
  off-fleet/hosted consumer.
- **DEFERRED, not dropped (surface at build kickoff):** the operator-approved **full 7-file
  frameworks→packages→hand-rolling sweep** of `~/.claude/CLAUDE.md` §Packages + `brief-base.md` +
  package-scout.md/tdd-contract.md/contract-adversary.md/lead-base.md/odoo-reuse-scout.md. It is
  independent of the build; do it whenever, but do not lose it.

## 6. First moves for the build lead

1. Read §1. `lore_index()` — confirm currency; reconcile if your session has edited since.
2. Register on `lore_comms` (new session id, role `lead`). Spawn the **Fable sidecar** (§4) FIRST so
   it's warm before the contract author has questions.
3. Launch the `tdd` cycle at DISCOVERY (the design doc IS most of Discovery). Run the **spike (§6.6)**
   as/before the contract so the `[inferred]` items are proven-or-fallen-back before pins depend on them.
4. Contract → PAUSE for operator review → adversary → build → cold audit → **standalone deploy** with
   the in-image gate.
