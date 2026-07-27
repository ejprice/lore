# 04 — Comms: blocks edge + fleet columns + footer · formerly PKT-28 phase C2c
size ~0.20 wu · wave C · depends: packet 03
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · DEPLOY: yes (both)

## Mission
Close the C2 surface: the task-DAG `blocks` edge, the fleet view's message columns, the
pending-traffic nudge footer, and the dangling-edge hardening.

## Scope IN
- `blocks` task DAG edge (`task->blocks->task`), mirrored from `task.blocked_by` inside
  the existing write txns; invariant tests pin edge≡blocked_by + acyclicity.
  ⚠ **THE TRANSITIVE-READ IDIOM BELOW WAS WRONG AND IS CORRECTED (P4, PROBED 3.2.1
  2026-07-26).** This packet formerly prescribed `@.{1..n}->blocks->task, always TIMEOUT`.
  **Both halves are false and a builder implementing them cannot succeed:**
  - `@.{1..n}->blocks->task` returns **terminal-depth nodes only**, NOT the closure. The
    closure operator is **`+collect`** (deduplicated, ordered by proximity — v3.2.0 spec
    `language/graph/path_collect.surql`): `@.{1..n+collect}`, plus `+inclusive` only where
    the root itself is wanted.
  - **`TIMEOUT` is a `SELECT` clause — a PARSE ERROR on a bare idiom** (`Unexpected token
    `TIMEOUT``). "Always TIMEOUT" is satisfiable ONLY through the
    `SELECT id, @.{1..n+collect}(->blocks->task).id AS downstream FROM task:x TIMEOUT 5s`
    form. Reference §4 says "add a `TIMEOUT`" without noting the bare form cannot carry one.
  - ⚠ **Depth cap TRUNCATES SILENTLY**: `{..256+collect}` on a 299-deep chain returns 256
    nodes with **no error and no signal**. A served "downstream" set can be short and look
    complete. Decide deliberately what the packet serves and pin the boundary.
  - **FIXTURE FLOOR: ≥3 deep AND branching.** A 2-node chain cannot discriminate the correct
    closure from the terminal-depth read the old text prescribed — the small-N trap.
- Fleet unread/directive columns (per-agent unread + unacked-directive counts — computed
  over the WHOLE set their label claims, per the spec's counting law).
- `_comms_footer`: lore_tasks/lore_claim_task/lore_findings mutations append one line
  when traffic pends. ⚠ **DESIGN FORK — OPERATOR-RULED 2026-07-26.** There is **no shared
  render seam**: the three tools are independent `-> str` dispatchers with ~17 return points,
  so appending at the render sites would be sixteen-plus clones of one policy (the #102 shape
  repo law forbids).
  - **RULED SHAPE: ONE `_comms_footer(...)` helper called from the SINGLE exit of each of the
    three `AppContext` dispatchers.** DRY-legal, mypy-visible, `str`-typed, and
    **mutation-provable — change the footer text and ALL THREE pins must go RED** (a caller
    that stays green is a private copy wearing the shared name). Costs a small refactor
    collapsing `tasks` and `findings` to one return each; `claim_task` is already 1-return.
    *Rejected: `TracingFastMCP.call_tool` — it returns content blocks not `str`, would need a
    tool-NAME allowlist its own docstring exists to avoid, and its failure posture
    deliberately swallows errors, which is wrong for served output.*
  - **RULED TRIGGER: per-ACTION-OUTCOME — only calls that actually WROTE.** `claim_task`'s
    LOSING branch writes nothing → no footer. `lore_tasks action=query|rollup` and
    `lore_findings action=query|get|chain_head` are reads → no footer. (Spec ambiguity
    escalated by the scout rather than chosen — both readings produce different code.)
  - ⚠ **TYPE DISCIPLINE (D2):** the comms surface renders through `Rendered`/`SafeLine`/
    `render_line`; these three return plain f-string `str`. A footer built as `Rendered` and
    appended to a `str` crosses the render-safety boundary the wrong way; one built as a bare
    f-string is a NEW un-sanitised served surface. **Choose deliberately and say which.**
  - ⚠ **`_INSTRUCTIONS` IS PINNED BY EQUALITY.** `test_comms_tool.py::test_the_served_
    INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs` (CL3, RULED) — and its sibling's
    docstring **names packet 04 by name** as the likely violator. Any teaching prose the
    footer adds lands through the declared-paragraph allowlist, never around it.
- **#105 — THE `ENFORCED` SWEEP.** ⚠ **RE-SCOPED BY OPERATOR RULING 2026-07-26 (kickoff).**
  **The text this replaces was STALE and understated what packet 03 shipped** — it said 03
  landed only "a typed `TYPE RELATION IN message OUT agent` (which catches only wrong-**table**
  endpoints)". Ground truth at kickoff: `surreal_schema.py` `_define_relation_table(TO_RELATION,
  MESSAGE_TABLE, AGENT_TABLE, **enforced=True**)` → `DEFINE TABLE OVERWRITE to TYPE RELATION IN
  message OUT agent ENFORCED SCHEMAFULL`. Per store reference §4, `ENFORCED` validates **BOTH**
  endpoints and guards the **TABLE** — including `INSERT RELATION`, the door an app-level check
  on one verb can never reach. **So `send`'s structural half is DONE, and done more strongly
  than a per-verb guard.** Building to the old text would have re-solved a solved problem while
  leaving the real gaps open.
  **THE REAL GAP, measured at kickoff — exactly ONE of four relation tables is `ENFORCED`:**
  | edge | endpoints | `ENFORCED`? | note |
  |---|---|---|---|
  | `to` | message→agent | ✅ packet 03 | closed |
  | `briefed` | agent→brief | ❌ | `BriefLedger.publish(agent_id: str \| None)` — confirmed still a **bare string** |
  | `refers` | code_node→name | ❌ | **the old text never mentioned these two** |
  | `answers_to` | code_node→name | ❌ | ditto |
  **RULED SCOPE:** `ENFORCED` onto `briefed`, `refers`, `answers_to`, and onto the new `blocks`
  edge **from birth**. The app-level check stays as the **ergonomic layer** — it names EVERY bad
  id BEFORE the write; `ENFORCED` reports ONE, as untyped prose, only AFTER the write is
  attempted, aborting the txn (§4). Neither is redundant; do not delete one for the other.
  ⚠ **MIGRATION — THIS IS THE #107 SHAPE.** The flip lands on THREE EXISTING tables.
  `IF NOT EXISTS` is a **SILENT NO-OP** on an existing table; **`OVERWRITE` is the only clause
  that lands it**, and it preserves fields, indexes and rows (§4). A virgin-DB test cannot see
  this failure — dirty-store pins are mandatory, per THE TEST ENVIRONMENT IS A FICTION.
  **Negative fixtures REQUIRED**: an identity that does not exist must be REJECTED. A fixture
  where every endpoint is registered cannot discriminate (FIXTURES MUST DISCRIMINATE).
  Widen #105's own text from "latent — we never hard-delete" when resolving it.
- **⚠ REQUIRED 3.2.1 KICKOFF PROBES — the reference's §4 evidence is all 3.1.5.** Both stores
  moved 3.1.5 → 3.2.1 on 2026-07-22 (reference §0). Operator-directed at kickoff: confirm the
  capabilities reference against the lore corpora (`surrealql-tests` → `surrealdb-docs`) and the
  live 3.2.1 engine before building. **Already settled by the lead — do NOT re-derive:**
  `ENFORCED` rejects non-existent endpoints on 3.2 with the verbatim error `The record 'x:y'
  does not exist`, confirmed by the engine's own executable spec
  (`tests/language/statements/relate/enforced.surql` @`v3.2.0`, which ships its own positive
  control), the 3.2 vendor docs, and reference §4 — all three agree.
  **✅ ALL FIVE PROBES ANSWERED 2026-07-26** — receipts:
  `docs/plans/v2/receipts/2026-07-26-packet04/REPORT-probe-pkt04-store.md` (committed `03241f4`;
  archived at close-out). **Do NOT re-probe these; DO re-derive any number you rely on.**
  - **P1 — ✅ §6.4 CONFIRMED on 3.2.1.** A dangling edge is **STILL a first-class member** of the
    identity traversal; the 3.2 vendor `[]` claim is **still FALSE** (the probe also found *why*
    their example prints `[]`). **The negative fixture asserts the GHOST-MEMBER reading.**
  - **P2 — ✅ CONFIRMED.** `IF NOT EXISTS` = silent no-op; **`OVERWRITE` lands the flip and
    preserves rows, fields, index AND enforcement.** Migration shape settled.
  - **P3 — ✅ CONFIRMED.** #7061 stays fixed under both compositions. ⚠ #349 is now VERIFIED and
    **carries a SurrealDB 4.0 BREAK**: if `blocks` uses deterministic edge ids, today's silent
    overwrite becomes a hard error on 4.0. Ledgered — see the finding.
  - **P4 — ⚠ THE PACKET TEXT WAS WRONG.** Corrected in the `blocks` bullet above.
  - **P5/P5b — the flip is SAFE, but NOT uniformly, and it CHANGES A LIVE VERB.**
    `ENFORCED` **does** resolve endpoints created in the SAME uncommitted transaction (both
    controls held: committed-endpoint positive leg passed; a genuinely absent endpoint was still
    rejected, so the guard is **not inert** in transactions). Per-edge:
    - **`refers` + `answers_to` — SAFE TO FLIP.** No caller-supplied endpoint exists on either;
      every endpoint is minted by an earlier statement of the same fragment. ⚠ **Conditional on
      `{edge.src} ⊆ {node.qualified_name}` actually holding** between `_derive_edges` and
      `_derive_nodes` — FLAGGED, NOT SETTLED. The contract must establish it.
    - **`briefed` — SAFE ONLY IF `agent_id` IS VALIDATED BEFORE THE FRAGMENT IS COMPOSED.**
      ⚠ **BEHAVIOUR CHANGE ON A LIVE VERB, MEASURED:** today a publish with an unknown
      `agent_id` still writes the brief and leaves a dangling ack. **After the flip the txn rolls
      back and the publish is LOST** (`SELECT id FROM brief WHERE id = brief:b_lost` → `[]`).
      Correct atomicity — but it is a change, not a silent tightening.
    - **`to` — already shipped; NOW MEASURED SOUND, not merely inferred. Packet 03 is NOT
      latently broken.** Live property for the record (deployed today, not introduced here):
      **one bad recipient in a fan-out loses the WHOLE send** — no partial delivery, no message
      row.
  - ⚠⚠ **`ENFORCED` ALONE CANNOT SATISFY THIS PACKET'S OWN EXIT CRITERION.** What a caller
    actually receives is `statement N of M was rejected (unspecified rejection); see the server
    log` — the engine's `The record 'agent:x' does not exist` is deliberately withheld by the
    seam's error-message hygiene (ledger #31). **So "a bogus-recipient publish/send TEACHES
    instead of dangling" is UNREACHABLE via the engine guard: the app-level check is the ONLY
    layer that can teach.** It is therefore REQUIRED, not ergonomic garnish.
  - ⚠ **`BriefLedger._relate_briefed` catches `SurrealStoreError` AS ITS IDEMPOTENT-RE-ACK
    SIGNAL.** After the flip an `ENFORCED` rejection arrives through that SAME `except`, leaving
    two distinct failure modes sharing one catch, separated only by a follow-up read. **PIN IT:**
    a publish to a non-existent agent MUST raise and MUST NOT be reported as `already_acked`.
  - **Required pins (from P5b), each with its control:** (1) `publish` with an UNREGISTERED
    `agent_id` → refused by the app check, the bad id NAMED, brief NOT written; (2) `publish`
    with a registered `agent_id` → brief written AND ack edge written — **the positive control,
    so pin 1 cannot pass by refusing everything**; (3) `send` to `[real, bogus]` → refused
    BEFORE the write, asserting no message row exists after, so the pin distinguishes "refused
    early" from "rolled back late".
  - **Un-enforcing regression pin (P2 §3(a)):** `OVERWRITE` WITHOUT `ENFORCED` silently
    un-guards a table, invisibly on a virgin DB. One dirty-store pin per edge, **plus a mutation
    proof: delete `enforced=True` from the generator call and ALL FOUR pins must go RED** —
    prove sharing by mutation, never by inspection.

- **#219 (slotted 2026-07-26)** — `_validate_comms_charset`'s docstring AND its SERVED error
  message are FALSE: they claim identities are inlined into WHERE clauses, while every WHERE
  uses bound parameters. Fix the prose toward the measured truth (served prose is DERIVED
  from behaviour, never re-stated beside it — repo law); it deploys with this packet.

## ⚠ OPERATOR RULING 2026-07-26 — NO CONSUMERS, NO BACK-COMPAT OBLIGATION
**Verbatim: *"None of the comms package is in use. Change whatever."*** The comms surface has **no
live consumers**, so nothing in this packet owes a migration path, a deprecation shim, a preserved
signature, or a preserved failure mode. Consequences, stated so no agent re-litigates them:
- The **`briefed` behaviour change is ACCEPTED** — a publish with an unknown `agent_id` rolling the
  whole transaction back (rather than writing the brief and dangling its ack) needs no transition
  plan. It is simply the new behaviour.
- **`BriefLedger.publish(agent_id: str | None)` may be RETYPED OR RESHAPED OUTRIGHT** — required
  instead of optional, a validated type instead of a bare `str`, a different call shape. Pick the
  RIGHT design; do not preserve the current one out of caution.
- The same latitude covers every comms verb this packet touches.
⚠ **This grants latitude, NOT licence to skip law.** The removed-behaviour inventory still applies
to any delete/replace (repo CLAUDE.md: each removed branch/guard/side-effect adjudicated —
preserved-with-pin / dropped-deliberately / old-bug-not-re-pinned / spec-silent→escalate). "No
consumers" means you need not PRESERVE a behaviour; it does not mean you need not NOTICE dropping
one. And it says nothing about the code-graph edges (`refers`/`answers_to`), which ARE in use by
every index run.

## Scope OUT
- await/story/rollup/hooks (packet 05); protocol + drill (06).
- **Pre-existing dangling-edge CLEANUP — operator-ruled OUT 2026-07-26, filed as #236.**
  `ENFORCED` guards FUTURE writes only; existing ghosts are "entirely unaffected …
  turning it on and calling the ghost problem closed is a FALSE ALL-CLEAR" (§4). The
  operator's rationale: *"We're on a localhost. I'm not concerned about exposure at the
  moment."* **Named re-open trigger: the first non-local deployment** (hosted, multi-user,
  or off-LAN) — packet 39 MUST consult #236, as it must #138. ⚠ Nobody has measured how
  many ghosts exist; any number quoted before that sweep runs is a rumour.

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
⚠ **Its §4 evidence is 3.1.5; both stores now run 3.2.1 (§0).** Operator-directed
2026-07-26: DB claims are confirmed against the lore corpora — `lore_search(tier=
"surrealql-tests")` (the engine's own executable specs, pinned `v3.2.0` — an expected
result CANNOT lie) then `tier="surrealdb-docs"` (vendor prose, which CAN — treat a hit
as a lead to VERIFY) — before any live probe.
Packet 03 deployed **and it shipped `ENFORCED` on `to`** (verified at kickoff — the old
#105 text denied this); `lore_findings` → #105 open; the edge≡blocked_by invariant's
fixture set includes a CYCLE attempt (3.1.5 fixed cyclic node-drops — **re-pin on 3.2.1,
probe P4**).

## Exit
Full gates + cold audit + deploy BOTH + smoke: a blocked task chain renders its
critical path; a bogus-recipient publish/send teaches instead of dangling; #105
resolved; INDEX row + Log.
