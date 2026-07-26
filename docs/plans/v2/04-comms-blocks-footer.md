# 04 — Comms: blocks edge + fleet columns + footer · formerly PKT-28 phase C2c
size ~0.20 wu · wave C · depends: packet 03
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · DEPLOY: yes (both)

## Mission
Close the C2 surface: the task-DAG `blocks` edge, the fleet view's message columns, the
pending-traffic nudge footer, and the dangling-edge hardening.

## Scope IN
- `blocks` task DAG edge (`task->blocks->task`), mirrored from `task.blocked_by` inside
  the existing write txns; invariant tests pin edge≡blocked_by + acyclicity; transitive
  reads use the recursive idiom (`@.{1..n}->blocks->task`, always TIMEOUT).
- Fleet unread/directive columns (per-agent unread + unacked-directive counts — computed
  over the WHOLE set their label claims, per the spec's counting law).
- `_comms_footer`: lore_tasks/lore_claim_task/lore_findings mutations append one line
  when traffic pends.
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
  control), the 3.2 vendor docs, and reference §4 — all three agree. **Still OWED, each
  load-bearing:**
  - **P1 — decides the negative fixture's assertion.** Does a dangling edge still read as a
    **first-class member** (our §6.4, measured on **3.1.5**) or as `[]` (**what the 3.2 vendor
    docs STILL assert**, `learn/schema-management/tables-and-fields/tables.mdx`)? §6.4 calls the
    vendor claim FALSE — but that refutation predates the upgrade. Get this wrong and the pin is
    hollow. **Positive control mandatory** (§4: the original instrument's first run reported the
    OPPOSITE of the truth, and only the control exposed it).
  - **P2 — gates the migration for all three tables.** `IF NOT EXISTS` vs `OVERWRITE` for a
    CHANGED **RELATION CLAUSE** (`IN`/`OUT`/`ENFORCED`) on an EXISTING table, on 3.2.1. The
    executable spec covers `SCHEMAFULL`, **not** the relation clause.
  - **P3** — `UNIQUE(in,out)` cascade on 3.2.1. #7061 was fixed in 3.1.0, but the 3.2 release
    notes carry an **unverified** "duplicate edge record ID" fix (#349) touching this seam (§0).
  - **P4** — recursive `@.{1..n}` + `TIMEOUT` + cycle handling on 3.2.1.

- **#219 (slotted 2026-07-26)** — `_validate_comms_charset`'s docstring AND its SERVED error
  message are FALSE: they claim identities are inlined into WHERE clauses, while every WHERE
  uses bound parameters. Fix the prose toward the measured truth (served prose is DERIVED
  from behaviour, never re-stated beside it — repo law); it deploys with this packet.

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
