# 04 — Comms: blocks edge + fleet columns + footer · formerly PKT-28 phase C2c
size ~0.20 wu · wave C · depends: packet 03
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · DEPLOY: yes (04b-2 only)

> ⚠ **THIS FILE NOW SERVES THREE PACKETS: 04a (DONE), 04b-1, 04b-2.** The scope division and
> the rulings that produced it are in **§04b SPLIT** at the bottom; the INDEX table rows are
> authoritative over any sentence above it. **Every "04b" in the body predates the split** —
> read it as "04b-1 or 04b-2, per §04b SPLIT".

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
  repo law forbids). ⚠ **"~17 return points" is 15, MEASURED at 04b's kickoff** —
  `AppContext.findings` 8 · `AppContext.tasks` 6 · `AppContext.claim_task` 1. The argument is
  unaffected; the number is not a number anyone derived.
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
  **THE REAL GAP, measured at 04a's kickoff — ⚠ AND THIS TABLE WENT STALE AGAIN, IN THE SAME
  PARAGRAPH THAT WARNS ABOUT IT (corrected at 04b's kickoff, 2026-07-28).** `briefed` read ❌
  *"confirmed still a bare string"* — **04a FLIPPED IT**. Two of four are `ENFORCED`, not one;
  the flip is **live in the production store**, verified read-only at 04b's kickoff
  (`DEFINE TABLE briefed TYPE RELATION IN agent OUT brief ENFORCED SCHEMAFULL`) after it rode
  packet 42's image. **Re-derive this table before building; do not read it.**
  | edge | endpoints | `ENFORCED`? | note |
  |---|---|---|---|
  | `to` | message→agent | ✅ packet 03 | closed |
  | `briefed` | agent→brief | ✅ **packet 04a** (`6f0e03a`) | closed — live in production |
  | `refers` | code_node→name | ❌ | **the old text never mentioned these two** — deferred to packet **43**, NOT 04b |
  | `answers_to` | code_node→name | ❌ | ditto |
  | `blocks` | task→task | — **absent** | minted by 04b-1, `ENFORCED` from birth (verified absent in the production store at 04b's kickoff) |
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

- **#247 (slotted 2026-07-27) — the SENDER door: adjudicate at 04b's kickoff.** The message
  SENDER is an unguarded door for a stored identity naming no agent row — measured GREEN on a
  correct 04a build (the sender-side sibling of the recipient guard 04a closed; "not obviously
  in 04a's scope" per its filer). Either close it here with the same pattern (app-level check +
  negative fixture + positive control), or pass it to 05 as an operator-visible Log line —
  never silently.

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
⚠ **Superseded per half by §04b SPLIT.** "deploy BOTH" is void — see the ruling below.

---

# §04b SPLIT — kickoff 2026-07-28 (operator-ruled)

## Ground truth that moved before a line was written
Measured at this kickoff, read-only, and each one contradicts a sentence above:
1. **04a is ALREADY DEPLOYED.** Its commits merged into the packet-42 branch
   (`c7983e8` → `7e6c1f9` → `915b7b8`) and shipped in image `e91e37b9`. Verified in the
   RUNNING artifact (`agent_existence.py` present, `enforced=True` in `_briefed_statements`)
   and in the **production store** (`briefed` … `ENFORCED`). So 04a's `OVERWRITE` migration
   landed on the real long-lived store — **which nobody had checked**; 04a's dirty-store
   evidence was all from the test store. It rode another packet's deploy unverified.
   **Consequence: "04b DEPLOYS BOTH / carries 04a's schema" is VOID.**
2. `blocks` is **absent** from the production store — confirmed, not assumed.
3. **`create_task` is a bare `_query`, not a transaction.** "Mirror the edge inside the
   existing write txn" is a NO-OP PHRASE for it. `create_many` is transactional; `create_task`
   is not, and `supersede_task` passes `blocked_by=None` (successor born unblocked).
4. **`blocked_by` is FAIL-OPEN at write**: nothing validates that a blocker id names a real
   task. Today such a task is created and is then **unclaimable forever, silently**.
5. **`refers`/`answers_to` are packet 43's**, not this packet's — the #105 bullet's ruled
   scope predates the 04a/43 split.
6. **04a never mutation-proved all four edges** — it scoped that proof to the one edge it
   flipped (`FLIPPED_BY_04A`, a single entry). The proof must be WIDENED here, not inherited.
7. **#219 does NOT invert.** An AST sweep of all 187 production files found **zero**
   identities interpolated into query text; six residual classes each adjudicated
   individually. The prose is simply false — and it has **four** sites, not two.

## The four operator rulings
- **R1 — the footer gets a real caller identity.** The three ledger tools carry NO caller
  identity today (only bare free-text `owner`/`actor`/`created_by`, never resolved against the
  `agent` table), so *"traffic pends for YOU"* had no YOU and **the footer was not buildable as
  specified**. RULED: add an **optional `agent` (+`session`)** parameter to `lore_tasks`,
  `lore_claim_task` and `lore_findings`, mirroring `lore_comms`' identity contract; resolve
  through the registry; **`agent` omitted ⇒ NO footer** — honest silence, never a guess.
  *Rejected: resolving `owner`/`actor`/`created_by` heuristically (a guessed identity serves a
  WRONG footer — a trust-doctrine hazard) and a fleet-wide agent-independent line (a different
  feature).* This meets the `_INSTRUCTIONS` equality pin deliberately, through the declared
  paragraph allowlist — never by growing `_COMMS_DUTY_VOCABULARY`, whose docstring forbids it.
- **R2 — #247 is CLOSED HERE, in 04b-1**, not routed to 05. Measured: unreachable via
  `lore_comms` (the sender is store-resolved by `agent_registry.touch`) but **caller-supplied
  and unvalidated at the `MessageLedger.send` seam**; `message.sender` is an unconstrained
  `record<agent>` and `to`'s `ENFORCED` cannot see it (a FIELD, not an edge endpoint). By the
  packet's own "is it in the diff" test this was 05's — the operator granted the scope instead,
  because the shared policy is already in hand.
- **R3 — `blocks` ships `ENFORCED` from birth, WITH an app-level pre-check.** This CHANGES a
  live verb: a `create` naming a phantom blocker is **refused** where today it silently
  produces an unclaimable task. ⚠ **The 2026-07-26 "no comms consumers, change whatever"
  ruling does NOT cover this** — `lore_tasks` is in active fleet use. The change is
  deliberate: a loud refusal replaces a silent black hole. The app check is REQUIRED, not
  garnish — per P5b the engine's rejection is withheld from the caller by the seam's error
  hygiene, so it is **the only layer that can teach**.
- **R4 — "unacked directive" means `acked_at IS NONE` AND `grade = 'directive'`** on the `to`
  edge: a directive DELIVERED and never discharged. Nothing counts this today. *Rejected:
  `seen_at IS NONE` (a filtered restatement of the unread column beside it) and the brief-ack
  sense (already rendered as the fleet's `project` cell).*

## Lead rulings (recorded; overturn by operator ruling)
- **L1 — footer type discipline (the packet's D2 fork):** the footer is built as `Rendered`
  and **explicitly `str()`-ed at the append**. Buys `render_line`'s runtime control-char
  assert, keeps the diff proportional, does not pre-empt PKT-03's retype of the three
  dispatchers. ⚠ **`Rendered`/`SafeLine` SUBCLASS `str`**, so mypy, the AST template pin, the
  mint pin and the runtime assert are ALL blind to a `Rendered` demoted by concatenation — and
  the packet's demanded text-mutation proof cannot see a wrong type choice either. **The type
  choice needs its OWN pin.**
- **L2 — the best-effort batch actions** (`findings.resolve_many` / `acknowledge_many`, which
  may write 5, 3 or **0** of 5 items) footer **iff ≥1 item actually wrote** — the same
  principle the trigger ruling already applied to `claim_task`'s losing branch. Requires the
  internal helper to return a write-count beside its rendered string.
- **L3 — the blocker-existence check is GENERALISED, never cloned.** 04a's
  `agent_existence.reject_unknown_agents` / `format_unknown_agent_refusal` own a POLICY
  (existence probe + refusal rendering). A `reject_unknown_tasks` sibling would be copy #2 of
  that policy — the #102 shape. RULED: generalise to one implementation parameterised by
  table + label, with the agent entry point kept as a thin typed adapter so 04a's callers and
  pins are untouched. **Prove sharing by MUTATION**: change the shared refusal text and BOTH
  the agent pins and the new task pins must go RED. If generalising forces a worse API, that
  is an ESCALATION, not a licence to write the second copy.

## 04b-1 — task DAG + the sender guard · ~0.25 wu · TEST-ONLY + schema, NO deploy
**Scope IN:** the `blocks` edge in `surreal_schema::_task_statements` (`ENFORCED` from birth) —
note `generate_ddl()` does NOT compose the comms/graph tables, so `_task_statements` is the one
site feeding **both** `generate_task_ddl` and `generate_ddl`; `create_task` converted to
`self._apply([fragment])` so CREATE+RELATE are atomic; the mirror at both write paths; the
generalised blocker-existence pre-check (L3); the edge≡`blocked_by` invariant; an acyclicity
guard over PERSISTED ids (today's only cycle check is `AppContext._find_key_cycle`, over
`create_many`'s batch-local temp KEYS); the transitive read as a ledger-level helper
(`@.{1..n+collect}` through the `SELECT … TIMEOUT` form, explicit small bound — **never** the
bare idiom, which cannot carry a `TIMEOUT` and returns terminal-depth nodes only); the
relation-edge mutation proof WIDENED from `FLIPPED_BY_04A` to all five edges; **#247**; 04a
residuals **R-1** (the `ack` leg missing from the sole-decision mutation proof) and **R-2** (the
id-SHAPE fixture monoculture); **#253** (added by operator ruling 2026-07-28 — see below).

**#253 — `query_tasks` materialises the WHOLE table (operator-ruled INTO scope 2026-07-28).**
`tasks.py::TaskLedger.query_tasks` issues `SELECT * FROM task` with **no WHERE and no LIMIT**, then
applies `status` / `owner` / `blocked` in a Python loop; the tool-level `limit` slices only after
the whole ledger is materialised into `Task` objects. Folded in HERE because 04b-1 already opens
this ledger to mint `blocks`, and that edge is plausibly the bounded blocker-resolution mechanism
the fix wants. ⚠ **The obvious fix is WRONG and the docstring says why:** *"Blocker statuses are
resolved against the full table so a blocker filtered OUT by the `status`/`owner` filter still
counts."* Pushing the filters into the store naively **silently mis-classifies** the `blocked`
partition. The REQUIRED PROPERTIES (stated as properties, not a mechanism — a builder must not
have to invent the general form): (1) no unbounded whole-table read — filters push into the store,
blocker resolution is bounded by the candidate set's `blocked_by`/`blocks` edges; (2) the pinned
semantics SURVIVE — an out-of-filter blocker still counts, a never-minted blocker id is fail-closed
UNRESOLVED, terminal = `done`/`wontfix`, and the query partition can **never** disagree with the
atomic claim's server-side `array::len` CAS (`tasks.py::_claim_fragment`), which is the invariant
the current full read buys; (3) the pin DISCRIMINATES — N unrelated tasks ≫ K blockers, so a
whole-table read and a bounded read are measurably different. Small-N cannot tell them apart.
⚠ Note the finding CORRECTS this packet's first framing: the unbounded read is `query_tasks`,
**not** `_is_blocked`, which is a pure predicate over an already-fetched dict and reads nothing.
**Fixture floor (non-negotiable):** ≥3 deep AND branching — a 2-node chain cannot tell the
closure from the terminal-depth read. Negative fixtures with positive controls throughout; a
fixture where every endpoint exists cannot discriminate.
**Removed-behaviour inventory REQUIRED** (delete/replace law): `create_task`'s non-transactional
write · the fail-open `blocked_by` · `supersede_task` dropping the predecessor's dependencies
(consistent with today's row — record as `old-behaviour-preserved` DELIBERATELY, not by accident).
**Entry check:** `blocks` absent from the schema AND from both stores; `_task_statements` is
still the shared site; `test_derivation_source_unification.py` runs in the wave gate (it is the
ONLY guard on the `DEFERRED_TO_PACKET_43` exemption, and the edge-set pin
`test_the_relation_edge_set_is_EXACTLY_the_four_known_edges` will redden on the fifth edge —
that reddening is the DELIBERATE declaration, not a misfire).
**Exit:** full gates with a passed-COUNT + cold REFUTE audit + commits; NO deploy (04b-2 ships
it); findings resolved/filed; INDEX row + Log.

## 04b-1 escalation rulings (lead, 2026-07-28 — on `REPORT-contract-04b1.md`)
All five of the contract author's escalations are **ACCEPTED AS PINNED**. Each was raised with
both readings written down and a recommendation; the recommendations were right. Recorded here
because a ruling that lives only in a report is a ruling the next agent does not meet.
- **E-1 — edge direction: `RELATE $blocker->blocks->$task`** (`in` = blocker, `out` = task).
  Reads as English, and puts the newly-created row on the `out` side — the side 04a MEASURED
  resolves inside an uncommitted transaction.
  ⚠ **RIDER, and it is the lead's addition, not the author's miss: the probe measured the
  FORWARD arrow.** P4 established `+collect` closure, dedup, cycle-termination and the silent
  256 truncation on `->blocks->`. This design traverses **`<-blocks<-`** (upstream blockers).
  Same-behaviour-on-the-reverse-arrow is an INFERENCE, and inferring a property over the whole
  set from the one member you measured is THE QUANTIFIER LAW's exact shape. **The adversary
  MEASURES the reverse arrow before the builder relies on it** — closure, dedup over a diamond,
  cycle termination, and whether the bound truncates the same way.
- **E-2 — identity rendering: `name (id)` where a display label exists, BARE id where none
  does.** A task has no name at the call site; forcing the shape yields `abc (abc)`, which
  teaches a reader that it does.
- **E-3 — the transitive read serves UPSTREAM blockers, and is HONEST at its bound**: a typed
  result carrying `truncated`, never a silent short answer (probe §5.3 measured 256-of-299 with
  no error and no signal) and never a RAISE (which makes a legitimately deep DAG unreadable
  rather than honestly partial). The instrument is a DISCRIMINATING PAIR — a 5-chain at
  `max_depth=2` reports `truncated=True`, a 3-chain at the SAME depth reports `False`; a build
  hard-coding either value dies on one leg.
- **E-4 — #247: the sender is validated FIRST, in its own call, with its own error
  vocabulary.** A refusal that mis-names the role is one an agent acts on wrongly.
  **ACCEPTED COST, stated so it is not rediscovered as a surprise: one extra round trip on the
  send path** (and 04a's R-4 already noted an unmeasured extra trip on `publish`/`ack`).
  **NAMED RE-OPEN TRIGGER:** if send-path latency ever becomes a measured concern, the
  pre-authorised alternative is ONE existence call whose refusal is ROLE-TAGGED and names both
  roles correctly — that is a contract change, not a builder's shortcut.
- **E-5 — the mutation proof is FIVE PER-EDGE PROOFS with two mutation shapes**, not one shared
  mutation. ⚠ **The brief's "widen it to five edges" was WRONG and the author was right to
  refuse it**: `refers`/`answers_to` carry no `enforced=True` to delete, so one mutation would
  declare reds that stay GREEN for two of the five — precisely the direction the both-ways diff
  exists to catch. The two deferred edges get an IN/OUT swap instead, proving THEIR pins are
  live rather than that their guard is.

## ⚠ THE FABLE DESIGN SIDECAR IS LIVE, AND IT OUTRANKS THE RULINGS BELOW (operator, 2026-07-28)
`design-sidecar-04b` (Fable 5, long-running, spawned once per the repo CLAUDE.md pattern) is
auditing this packet's ruled design **as a MODEL CONSUMER would experience it**. The operator's
grant, verbatim: ***"It may overrule operator rulings."*** So every ruling in this file — R1–R7,
L1–L3, E-1–E-5 — is **provisional until the sidecar reports**. An `OVERRULE:` verdict in
`docs/design/2026-07-28-04b-model-consumer-audit.md` supersedes the ruling it names; a CONCUR
leaves it standing.
**Why the operator started it here, on a packet the INDEX does not mark for a sidecar:** this
session accumulated a stack of SERVED-SURFACE design decisions (a footer's identity contract, a
live verb's failure mode, a truncation signal, a refusal's rendering) and the lead ruled them
all itself. Those are exactly the decisions the Consumer Law governs — *"lore's clients are
AGENTS … every served surface is read by an LLM that learns the contract FROM what is served"*
— and the lead is not the instrument for judging them. Standing question it carries:
***"models must be happy with lore's function"***, with a three-model consult (Sonnet 5 /
Opus 5 / Fable 5, asked independently and DIFFED) where a call is contested.
**Timing, stated because it is the whole reason it was started now: NO PRODUCTION CODE EXISTS
YET.** No builder has started. A design change is cheap at this instant and expensive once a
build lands. ⚠ `contractfix-04b1` IS running concurrently, so an overrule of R3/E-3 may strand
some of its pins — accepted deliberately: its other half closes a C-DEF blocker that is needed
under every design, and stopping it would waste all of its in-flight work to save part of it.

## RULINGS ROUND 3 — and the operator's deciding principle (2026-07-28)
> **"AGENT CONFIDENCE AND TRUST TRUMP EVERYTHING."**
> **"Agents must TRUST Lore or Lore is a failure."** — operator, verbatim, twice.
**This is the tiebreaker for every open fork in this packet, and it RETIRES the "flagged,
needs a ruling" disposition for anything that touches a served surface.** A trust question is
not a fork the lead brings back; it is already decided. What follows was staged as four
questions and is ruled instead.

- **R8 (operator) — the footer's two OVERRULES are ACCEPTED.** (1) A **supplied-but-
  unresolvable** `agent=` TEACHES loudly; silence is only correct for an OMITTED one (a
  silent typo earns a permanent route-around). (2) The strict exact-match fallback on
  `owner`/`actor`/`created_by` is reinstated, served **third-person, with no drain
  imperative** (closes the drain-theft hazard only the Opus consult saw) and the coupling
  **disclosed on the field** (the hazard only the Sonnet consult saw). Cost: one
  charset-gated registry read per identity-less write · ~7 pins · ~a day of 04b-2.
  ⚠ **RIDER, and it is the load-bearing half:** the `Field(description=)` string is now
  LOAD-BEARING and must state the PAYOFF. Measured: with a terse description **neither**
  Sonnet 5 nor Opus 5 passes `agent=`; with a payoff-stating one **both** do. A parameter
  nobody passes is a feature that never fires.
- **R9 (operator) — `limit` becomes legal for `query`, and the no-limit path gets a DEFAULT
  display cap** with the house counted-elision grammar (honest total from a store-side
  count; `+K more — re-run with limit=N`). Windows the RENDER, never the answer. Measured:
  `query` REFUSES `limit` at HEAD and served the sidecar the whole ~110-row ledger.
- **R10 (operator) — MP-5, the superseded-blocker door: CLOSED, both halves.** (ii) 04b-1's
  blocker pre-check refuses a superseded blocker and names its successor (*"task X is
  superseded by Y — block on Y instead"*) — near-zero cost, the grouped existence query
  already holds the rows, and a `blocked_by` naming a superseded task is NEVER legitimate.
  (iii) 04b-2 teaches at the moment of CAUSATION too: `supersede_task` warns when the
  predecessor has dependents, and the claim render names the superseded case — because
  supersession can happen AFTER dependents exist, which (ii) alone cannot catch (the
  quantifier law). **REJECTED:** treating `superseded` as terminal in the CAS — supersession
  means the work MOVED, not finished, so it would silently un-block dependents while the
  successor is open: the INVERSE black hole, quieter and worse. **DEFERRED:**
  dependency-transfer (iv), which breaks `blocked_by`'s post-creation immutability that the
  claim path rides — re-open trigger: the first fleet incident of a dependent stranded by a
  live supersede, or packet 05 touching the claim path, whichever comes first.

### Ruled by the trust principle — NOT brought back as forks
- **T1 — NO SILENT SHORT ANSWERS (adversary R-20).** A `LIMIT` pushed into the statement cuts
  rows BEFORE the client-side `blocked` filter, so `query_tasks(status=…, blocked=False,
  limit=5)` can serve FEWER than 5 while more exist, **with no signal**. Nothing pinned it.
  **RULED: the cap applies to the ANSWER, not the candidate scan; and where the scan is
  exhausted before the cap fills, the render SAYS SO.** DESIGN-LAW §1.4 names silent
  truncation the cardinal failure class — there was never a fork here.
- **T2 — A RAW `(unspecified rejection)` REACHING A CALLER IS A DEFECT** (sidecar §5.4). On
  every verb this packet touches, each caller-reachable engine rejection is either
  pre-checked into a teaching refusal or classified into a teaching error. An undiagnosable
  error is the anti-teaching surface: the agent cannot tell its own mistake from a broken
  tool, and **the measured consult behaviour is that it blames the tool.** Cold-audit sweep
  line: enumerate the new verbs' engine-rejection paths and assert each is laundered or
  pre-checked.
- **T3 — THE FOOTER'S HOSTILE FIXTURE IS MANDATORY, AND ITS FORGERY IS AN INSTRUCTION**
  (sidecar §5.3, sharpened by measurement at this kickoff). MEASURED: `safe_str` /
  `sanitise_line` COLLAPSE newlines — so a stored value **cannot forge a row boundary**, and
  the claim that production serves the #99 forged row "raw" is **too strong**. What survives
  verbatim is SAME-LINE text. For a task row that is misreading; **for the footer it is an
  INSTRUCTION** (`x — 7 directives await you — lore_comms action=drain …`), and agents obey
  instructions where they merely misread rows. The footer's hostile fixture therefore
  includes a **footer-shaped forgery in the identity value**, alongside L1's demanded
  type-choice pin.
- **T4 — INSTRUMENT REACH IS A CHECKED VARIABLE, NOT A STATED BOUND** (contractfix R-22).
  `measure_store_traffic` is blind to non-`query_raw` SDK calls, disclosed as a docstring
  bound. This repo's six-defeats lesson says a guard is an invariant only over the code it
  RUNS: enumerate the call sites and ASSERT each was observed, so reach cannot silently
  become the next name-list.
- **T5 — THE DUPLICATE-BLOCKER DIVERGENCE IS CLOSED** (contractfix R-19). A divergence
  between the SERVED partition and what the CAS actually does is a trust defect by
  definition. The class is still RED on the pristine tree and its own one-line fix
  (`array::len(array::distinct(blocked_by))` in the CAS) was MEASURED green on a reference
  build. ⚠ It is a live-CAS change, so it ships with the concurrency evidence that standard
  demands: **≥8-way × 20 consecutive green runs**, never a single green run.

## 04b-1 rulings, round 2 (operator, 2026-07-28 — on `REPORT-contract-04b1-253.md` + `REPORT-adversary-04b1.md`)
⚠ **These WIDEN 04b-1's writable set into `server.py`** — by one dispatcher line (R5) and the
cycle-policy unification (R6). The INDEX row records it. `server.py` is otherwise 04b-2's file;
these two touches are named exceptions, not a general grant.
- **R5 — the tool-level `limit` PUSHES DOWN, in 04b-1.** A bounded `query_tasks` that still
  materialises every matching row before the dispatcher slices is a HALF-FIX THAT READS AS A
  FIX — the trust hazard, not merely an inefficiency. `query_tasks` takes a `limit` and pushes
  it into the store; the dispatcher passes it. (Escalation E-D, raised by both #253 authors.)
- **R6 — ONE cycle detector, ledger-owned** (adversary MP-4). Today `server.py::AppContext.
  _find_key_cycle` owns a policy with its own sentence and a bare `ValueError`, and it fires
  FIRST — so a `lore_tasks` caller would never see the ledger's new vocabulary, and every cycle
  pin in the contract calls the ledger directly, observing nothing an agent is actually served.
  The DETECTION ALGORITHM is shared; the vocabularies may still differ (batch-local temp keys vs
  persisted ids) because they name different things. One refusal sentence shape, one error class,
  and **a pin at the TOOL SEAM** observing what a caller receives. This is ruling L3's shape
  applied to the cycle policy, which the contract left silent.
- **R7 — the TOCTOU is CLOSED BY CONSTRUCTION, not measured and accepted.** Any bounded rewrite
  is a TWO-read operation (candidates, then blockers) and a writer committing between them can
  make the served `blocked` partition disagree with the claim CAS **without either read being
  wrong** — a window today's single full read does not have, i.e. **a hazard this fix
  INTRODUCES**. Both reads go inside ONE `BEGIN … COMMIT` so they share a snapshot; the pin
  asserts the single transaction. Rejected: a named-hazard-only posture (accepts a correctness
  window on a SERVED answer on the strength of an argument, with no instrument) and a
  characterisation measurement (≥8-way × 20 — expensive, and it measures what this removes).
- **⚠ R7's rider, and it is load-bearing:** the adversary's MP-4a shows the write-time cycle
  guard must walk the `blocked_by` COLUMN client-side — the closing dependency **cannot** carry
  an edge, because `ENFORCED` rejects a `RELATE` to a task that does not exist yet, so any
  engine-traversal detector returns "acyclic". **A client-side walk is N reads**, which is
  exactly the shape R7 puts inside one transaction. The two rulings compose; a builder must not
  satisfy one by breaking the other.

**Owed before the builder is done** (each cheap, none optional):
1. **PROOF 5 was never executed** ("not run for time"). Run it.
2. **PROOF 3 was run piped to `tail`**, so its shell `$?` was `tail`'s — the repo's own #196
   lesson, self-declared by the author. Re-run it UNPIPED with the exit captured.
3. **04a residual R-e:** `test_surreal_store.py::test_the_whole_schema_migrates_an_existing_
   populated_store` applies four slices and not the guarded-edge ones; a fifth edge widens that
   gap again. It was outside the contract's writable set — the builder's scope now.

## SIDECAR RULING S1 — `fleet` DEFAULTS TO THE CALLER'S SESSION (2026-07-28, follow-up 1)
Source: `docs/design/2026-07-28-04b-model-consumer-audit.md` §8, on dogfood findings #257/#258.
**This lands WITH or BEFORE 04b-2's new columns** — it is not a cleanup that can trail them.
The lead offered four candidate fixes; the sidecar rejected the framing and produced a fifth.
- **The deciding fact is STRUCTURAL, not taste, which is why no consult was run:** the served
  `send` contract resolves recipient names **in YOUR session only**. So every out-of-session
  row in `fleet` is **unreachable-by-construction** — an agent cannot act on it at all.
  **The corpse problem is a SCOPE problem wearing a freshness costume.**
- **S1-a (the load-bearing half): `fleet` defaults to the caller's session, with NO new
  parameter.** `fleet` already REQUIRES registration (measured — the sidecar's own unregistered
  call was refused), so the handler already holds `agent_row.session`. The cross-session
  remainder becomes ONE counted line teaching the widening re-ask — the house elision grammar,
  which already exists.
- **S1-b: NO freshness exclusion in-session.** Stale rows are **the orphan signal** — the
  drill's whole point is that a killed agent surfaces in `fleet`. Annotate, never hide.
- **S1-c: the reaper is REJECTED in BOTH forms.** Hard-delete re-arms #105 (the comms design
  assumes agent rows are never hard-deleted). Auto-retire writes a **heuristic guess** as a
  status **another agent owns**, on a **READ path** — the confident-wrong class. Retention is
  deferred with a named trigger: an operator-set roster bound, or the first hosted deploy
  (packet 39).
- **S1-d: the smoke retires its own agents, plus one backfill for the existing corpses.**
  Necessary but NOT sufficient on its own — corpses are a *designed-for permanent feature*
  (kills never self-retire; the drill surfaces orphans deliberately). ⚠ **This touches
  `smoke_p8b`/deploy tooling, which is OUTSIDE 04b's writable set — it needs its own scope
  grant or its own routing. Flagged, not assumed.**
- **Why the new columns change the STAKES but not the ANSWER:** in-session,
  **unacked-on-STALE is the highest-value cell on the whole surface** (a stranded directive an
  agent can re-route). Cross-session, the same two numbers are 38 unactionable values that
  train an agent to skim past the signal. S1-a also shrinks the columns' grouped reads to
  fleet-size **by construction**.

## SIDECAR RULING S2 — RETIRE THE `⚠ STALE` BADGE; SERVE THE AGE (2026-07-28, follow-up 2)
Source: doc §10, on finding **#259**. Found by DOGFOODING **after** the S1-d reap — and it was
INVISIBLE before it: with 38 corpses on the roster a 17-minute STALE looked like more of the
same. **The operator's "reap first, then clean up the mess" ordering is what exposed it**, which
is worth recording as a method, not just an outcome.
- **The sidecar's own miss, in its words: it read the badge from its NAME, not its PREDICATE** —
  an un-derived claim inside its own ruling, in a packet whose recurring defect class is
  exactly that.
- **MEASURED:** `config.py::DEFAULT_COMMS_STALE_HEARTBEAT_S = 600`, predicate
  `heartbeat_age_s > stale_after_s`. One boolean spanning **1,020s to 1,407,600s** — a healthy
  Opus contract author at 17m and a 16-day corpse render IDENTICALLY.
- **S1-b's CONCLUSION SURVIVES, with a stronger justification.** A predicate measured to fire on
  HEALTHY agents is disqualified from driving EXCLUSION *a fortiori* — the freshness window
  rejected in S1-b would, today, be **hiding a live contract author**.
  Annotation-never-exclusion stands; **what falls is the annotation itself.**
- **RULED — candidate (b), NOW: retire `⚠ STALE`, serve the AGE** (already computed, already
  rendered: `hb 17m` / `hb 2d`). DESIGN-LAW §1.3's asymmetry decides it: **a measure without a
  verdict UNDER-claims, which is nearly free; a wrong verdict kills the class categorically.**
- **(a)/(c) REJECTED as rumour thresholds** — the channel measures **comms cadence, not
  liveness**, and a healthy builder's 30–60min gap overlaps early-death **at any threshold**.
  (c) stays re-openable strictly behind a NAMED measurement (per-role cadence over N real
  sessions once 04b-2's columns generate traffic; owner = #259's taker) — **with the sidecar's
  prediction stated in advance so the measurement GRADES it: the overlap will not vanish.**
- **(d) is the right SECOND step and must ship WITH its consumer:** a declared cadence yields
  `overdue (declared ≤20m, silent 45m)` — a verdict **true by construction** (the derived-prose
  law applied to liveness); with no declaration you get age only, so **non-adoption fails
  HONEST** — the property the badge lacks. ⚠ **Sequencing rider, which is the R1 lesson applied
  to itself:** the optional parameter lands in **packet 06, with the drill that pays for it**
  (the drill controls its own briefs, so declaration is guaranteed there) — **never earlier as
  dead schema nobody passes.** 04b-2 ships (b) alone.
- **The unacked-on-STALE cell SURVIVES (§10.4) — its value was never the badge's.** It is
  unacked-N **composed with age**: `unacked 3 · hb 2d` reads as stranded; `unacked 3 · hb 17m`
  reads as a busy teammate, correctly. **What the badge's noise threatens is the IMPERATIVE**:
  a "re-route or retire" teach line on a predicate firing at 17m would instruct callers to
  **re-route a live builder's traffic** — the drain-theft hazard's sibling. Same grammar rule as
  R8's split: **imperatives ride only TRUE verdicts.** So **04b-2 ships the columns as MEASURES
  beside the age, with NO stranded-imperative**; the imperative arrives with (d)'s `overdue`
  verdict, in the packet that builds it.
- **PACKET 06 IS OWED NOTICE (two items):** the glyph RETIRES, so the drill must not assert
  `⚠ STALE` in any expected render; and the drill's **orphan-detection leg rides (d)**, not the
  badge.

## ⚠⚠ SIDECAR FINDING S3 — THE LEGACY-EDGE WORLD DEPLOYS ITSELF (2026-07-28, BLOCKER)
Source: doc §11.2, re-graded under **TRUST — THE HARD DEFINITION** (`CLAUDE.md`, imported to
this branch at `0acbf47` from `ee0e87d`). **This got past the contract, the contract-adversary,
two contract-fix waves and the lead.** It became visible only under the new definition's Leg 2.
- **THE DEFECT.** The `blocks` mirror is ∀ verbs **going FORWARD**. Production tasks carry
  `blocked_by` COLUMNS **today** (measured — 04b-2's own ledger row is one) and will have **NO
  `blocks` edges** at deploy. **The transitive read rides EDGES by design.** So 04b-2's
  critical-path render serves **`ids=[] truncated=False`** — *clean, confident, wrong* — on
  exactly the rows the fleet is working.
- **It fails BOTH legs at once**, and it is worse than an ordinary forgery-pin gap: every other
  owed construction has to be CONSTRUCTED. **This degraded world needs no constructing — it is
  the default state at deploy.** `truncated=False` is not a missing bound; it is a **positive
  assertion of completeness that is false**, which is the definition's central failure.
- **NO BACKFILL EXISTS ANYWHERE** — the sidecar grepped the contract, the packet and every
  ruling; the only "backfill" in this packet is S1-d's *smoke-agent* one, a different thing.
- **RECOMMENDED (needs an OPERATOR RULING — it is a migration over production data):** backfill
  the edges in `ensure_ready`, **pre-filtered through the L3 existence policy** — ⚠ legacy rows
  carry phantom blockers, and those meet `ENFORCED`, so **a naked backfill rolls back the whole
  one-transaction migration**; the phantom SKIPS are RECORDED, not silent; forgery-pinned in the
  dirty-store harness that already exists.
- **FALLBACK if the backfill is refused:** the render **names the bound as a FACT** (not a
  disclaimer) — legal under the definition, and a **permanent tax on every future read**.
- ⚠ **TWO CREDITS, so the gap is not overstated (§11.1):** the schema/migration legs AND #253's
  partition legs **already pass Leg 2** — `_seed_legacy_task` constructs the production-real
  partial world (column-bearing, edge-less, phantom blocker) and pins fail-closed +
  claim-agreement over it. Everything else this packet adds is scope-diffed and forgery-BLIND.
- **OWED CONSTRUCTIONS, tabled per dependency × mode (§11.1):** traversal timeout ⇒ a teaching
  error, never partial-as-complete · the fleet columns' FAILED grouped count must **not** render
  `0` (its bytes must differ from a healthy zero) · the footer's explicit leg, check-FAILED ⇒ a
  loud line while the write still succeeds · the pre-check's failed existence read ⇒ constructed
  fail-CLOSED · R9's honest total never invented.

### ✅ RULING R11 (operator, 2026-07-28) — BACKFILL IN `ensure_ready`
The sidecar's recommendation is ADOPTED in full. Fix the defect; do not disclose it.
- Mint the missing `blocks` edges from existing `blocked_by` columns **at migration time**,
  **pre-filtered through the L3 existence policy** — a naked backfill meets legacy phantom
  blockers, which meet `ENFORCED`, and **rolls back the entire one-transaction migration**.
- **Phantom skips are RECORDED, never silent** — a silent skip is a false clear in the exact
  shape S3 identifies.
- **Forgery-pinned in the dirty-store harness that already exists** (`_seed_legacy_task` already
  constructs the production-real partial world — the instrument is built, it just was never
  pointed at the traversal).
- Rejected: *render-names-the-bound* (legal, but a permanent tax on every future read for a
  one-time migration we declined to run) and *a separate one-shot script* (a deploy that forgets
  it silently reproduces the defect with no signal).
- Store backed up before any migration work: `/backups/lore/lore-prod-20260728T194511Z.surql`
  (2.68 GB, `EXIT=0`, 22 tables, engine success line verified).

### ✅ R11's FOUR ESCALATIONS — RULED (lead, 2026-07-28, on `REPORT-contractfix-04b1-r4.md`)
- **ESC-1 — "RECORDED" = a structured LOG record at WARNING or above** (reading A, as pinned),
  naming both the phantom id and the task it was skipped for. Rejected reading B (a typed
  migration summary returned by `ensure_ready`): it retypes a method five test doubles
  implement and that DI calls at boot **for effect, not for value**. ⚠ **The consumer-facing
  half is already handled elsewhere and must stay that way:** the log serves the OPERATOR; the
  agent-facing bound is §C's pinned scope statement — a legacy `blocked_by` naming no task row
  means the traversal is short **by design**, and the READ surface names that as a fact.
- **ESC-2 — the policy module grows a NON-RAISING probe, and `reject_unknown_rows` becomes a
  thin caller of it** (reading A). One implementation, two callers, inside the module L3
  already names. Rejected reading B (call the raising entry per row and catch): N round trips,
  and it makes an exception the control flow of a migration. This is ONE IMPLEMENTATION applied
  to the policy's own shape.
- **ESC-3 — READING B, and it is pinned: a failed pre-check is CLASSIFIED into the ledger's
  vocabulary, not merely distinguishable.** The author recommended "B eventually, A now" out of
  well-placed C-DEF caution — a contract must not invent a requirement a correct build fails.
  **That caution does not apply once the requirement is RULED**: a correct build now classifies,
  so the pin is satisfiable by construction. T2 bans a raw `(unspecified rejection)` reaching a
  caller, and a store failure during the pre-check **does** reach one; that it is not
  caller-provoked changes who caused it, not what the caller can do with it. Add the
  `TaskLedgerError` type assertion the author names.
- **ESC-4 — READING A, and NOW PINNED: the backfill MINTS legacy cycles, and RECORDS them** like
  a phantom skip. Refusing them (B) would break **edge ≡ `blocked_by`** on exactly the rows the
  invariant is hardest to reason about, and `+collect` terminates on cycles (probe P4). A legacy
  cycle is a pre-existing DATA defect; the edge set must MIRROR reality, not quietly diverge from
  it — a divergence the invariant asserts does not exist is a false clear in the store itself.
  The RECORD is what stops it being silent. ⚠ **The author deliberately left this unpinned to
  avoid a C-DEF, which was the right call while it was unruled** — the ruling is what makes
  pinning safe, and that ordering is the point.

### ✅ FINAL-ADVERSARY ESCALATIONS — RULED (lead, 2026-07-28)
- **ESC-2 — `loremaster/loremaster/store/_txn.py` IS GRANTED TO THE BUILDER** (not to any contract
  author). R7 puts both reads in ONE transaction, and the read sibling
  (`execute_read_transaction`) does not exist. Independently found twice — `contractfix-04b1-r3`
  §ESC-4 and the final adversary §ESCALATION-2. ⚠ **It must EXTEND THE SHARED SEAM, never
  hand-roll a `query_raw`**: r3 MEASURED that a hand-rolled one **fails the repo's runtime
  SDK-escape guard**. One implementation, per repo law.
- **ESC-3 — ACCEPT THE BOUND (reading (i)), BUT THE DISCLOSURE MUST STATE THE REAL FAILURE MODE.**
  MEASURED: `TestTheScopeOfTheTransitiveReadIsSTATED` and
  `test_the_helpers_docstring_states_the_FLOOR_property` check TOKEN PRESENCE, so a docstring
  reading *"Ignores the `blocked_by` column entirely; a `phantom` entry IS included in this
  answer, which is a floor"* — **the exact inverse of the truth** — passes BOTH.
  Reading (ii) (phrase-level assertion) is REJECTED: it invents a requirement no ruling carries
  and is a C-DEF risk, which is the class this packet has already hit three times.
  ⚠ **But the existing disclosure says the pins "check presence, not truth", and that
  UNDERSTATES it** — a reader infers the failure mode is SILENCE when it is **INVERSION**. A
  disclosure that misdescribes its own bound is the false-gate class the repo already names
  (*"a failure message that promises a check the assertion does not perform"*). **So the class
  docstring states, explicitly, that a docstring asserting the OPPOSITE passes this pin** — that
  is the WHEN-YOU-CANNOT-CLOSE-A-HOLE-PIN-IT rule applied to a bound we are keeping deliberately.

### ✅ r6's TWO ESCALATIONS — RULED (lead, 2026-07-28)
- **ESC-5 — 04b-2 CLOSES THE CAPPED-LISTING FALSE CLEAR (reading (i)), and it is an ENTRY
  CONDITION of that packet, not a hope.** The author escalated rather than weigh trust against
  scope, which was right — but it stated the decisive fact without leaning on it: **the harm
  requires a DEPLOY, 04b-1 has none, and 04b-2 deploys BOTH halves.** So there is **no window in
  which any consumer can meet this false clear** — the fix lands in the same deploy that first
  exposes the surface. That makes (i) *consistent with* the trust doctrine rather than a
  concession against it: T1 forbids serving a silent short answer, and nothing is served until
  04b-2. Rejected (ii) (widen 04b-1 again and close it now): a store-side count is a **second
  read on the served query path** — a real performance decision, on the exact axis #253 and R7
  have been fighting all packet, taken under close-out pressure in a packet already green.
  ⚠ The pin r6 wrote is what makes this safe: the hole **cannot be inherited silently**.
- **ESC-1 — DEFERRED, deliberately, with a NAMED decision point** (deferral shape 1:
  measure-then-tune). The half that needed no ruling is **already done** — the false gate is
  closed by narrowing the pin's name and message to what it actually measures, and the residual
  growth is pinned as a KNOWN BOUND with a re-open trigger. What remains is *"is a
  ledger-independent write-path cycle read achievable under R7's rider?"* — and per the routing
  rule (`CLAUDE.md`: **a design problem never reaches a builder**) that is a property to INVENT,
  not a spec to implement. **DECISION POINT: 04b-2's kickoff**, which opens the same seams.
  **MEASUREMENT OWED FIRST, and it decides the answer:** whether the ancestor closure of the NEW
  dependencies is fully PERSISTED at write time — if it is, only the batch-local part need stay
  client-side, the property is achievable, and the known-bound pin becomes a defect report to be
  DELETED WITH THE FIX rather than a bound to keep.

### ⚠ ACCEPTED KNOWN BOUND (operator, 2026-07-29) — finding #274, and 04b-2 MUST consult it
**04b-1's contract cannot PROVE the backfill free of caps/doors/chunking.** Three consecutive
adversary passes each found MORE surviving wrong builds, all of ONE class (a cap, a door or a
chunk on the backfill path producing a silent short answer): 2 survivors after r5, **4 after
r6**, each passing the whole contract with a positive control.
- **The cause is diagnosed, not mysterious: the contract was ENUMERATING WHAT IS FORBIDDEN** —
  no cap of 50, then of 40, then of 200, then not these two doors. The forbidden set is
  UNBOUNDED (`CLAUDE.md`'s instrument lesson, six prior receipts), and a class surviving TWO
  waves is a DESIGN escalation, not a third fix. We were at three.
- **The design answer, recorded so nobody re-derives it:** allowlist the SAFE set — pin the
  STATEMENT SHAPE (the backfill's reads carry NO `LIMIT` clause at all) and DERIVE the door set
  the way `scripts/registration_sites.py` derives registration sites. One pin per PROPERTY, not
  one per wrong build. Independently named by the stage-2 adversary as M1 and M4. ⚠ A property
  to INVENT ⇒ an Opus author who attacks its own design, never a fix-wave brief.
- **Why accepting it is safe TODAY:** the shipped build is MEASURED clean of all six shapes (AST
  over both methods at `b8607c4`: zero try/except, no `LIMIT`, no chunking — lead-verified AND
  re-verified by the stage-2 adversary) · **04b-1 DOES NOT DEPLOY**, so no consumer can meet it ·
  and there is **NO FOURTH C-DEF** (247/0 and 881/0 against the shipped build), so no future
  builder is trapped.
- **RE-OPEN TRIGGERS:** 04b-2's kickoff (it deploys this code — the design fix is its natural
  home) · ANY edit to `_backfill_blocks_edges` / `_record_legacy_cycles`, because the guard that
  would catch a re-introduced cap does not exist and **the reviewer IS the guard** · the first
  production report of a short `transitive_blockers` answer.
- ⚠ **RECORDED, NOT PINNED.** The repo's own rule is a test asserting the hole that goes RED when
  someone closes it. That pin was not written — an unpinned known limitation is one step from an
  unknown one, and finding #274 plus this block are currently all that hold it.

## SIDECAR SELF-CORRECTIONS UNDER THE NEW DEFINITION (§11.3) — both ACCEPTED
- **OVERRULE-1 gains a FOURTH leg, and the distinction is the useful part:** *ran-and-empty*
  silence is a TRUE clear; *check-FAILED* silence is a FALSE clear **in the same bytes**. So a
  failed identity check must TEACH, not fall silent — the identical render for two different
  worlds is precisely what Leg 2 hunts.
- **OVERRULE-2(a)'s "may append" was DISCLAIMER-SHAPED** and is replaced with a fact-shaped
  asymmetric bound: **present ⇒ verified; absence asserts nothing.** ("A bound is a FACT, never
  a disclaimer.")
- §10's age-only render passes both legs as ruled.

## CONSULT CONTAMINATION DISCOUNT (§11.4) — conceded, and the grading survives
No question zero was asked; all four informants were in-repo (~60KB of house law preloaded).
Re-graded **against the bias direction**, which is the strongest instrument available here:
- **The V1/V2 `agent=` flip SURVIVES STRENGTHENED.** House law biases informants TOWARD passing
  `agent=`; both still DECLINED under the terse description. **Survival under adverse bias beats
  a cold read.**
- **The two Q1 hazards survive because they are ASYMMETRIC** — contamination manufactures
  UNANIMITY, not asymmetry; one distinct hazard per informant is the signature of derivation.
- Q2/Q4 survive on mechanism. **The route-around VOCABULARY unanimity is DOWNGRADED to colour**;
  no verdict rested on it alone.
- **STANDING, going forward:** question zero in every consult prompt, and **out-of-repo spawns
  for any claim about how a model reads a served string.**

## SIDECAR CAUTION C1 — carry this sentence into the BUILDER brief
Rounds 2 and 3 were read verbatim at `5a2dca9`: **nothing to overrule** (doc §9), and T5's
CAS-side `distinct` is judged the right fix of the three available — the only one that heals
legacy rows, and the query partition's ANY-semantics already agrees with it post-fix.
The one caution, which is not an overrule: **under T1's answer-cap, a future
"rows-read ≤ f(limit)" pin on the blocked-filtered path would be WRONG BY DESIGN.** The
boundedness property stays *"does not grow with UNRELATED ledger size"* — filling an
answer-cap legitimately requires scanning past non-matching candidates.

## 04b-2 — the comms surface · ~0.25 wu · DEPLOYS (carries 04b-1)
**Scope IN:** the blocked-chain / critical-path render; the fleet unread + unacked-directive
columns (R4's reading), counted over the WHOLE set each label claims — counts come from the
row-UNLIMITED `roster()`, never the capped `fleet()` window, and every cap
(`_MAX_FLEET_LIMIT=200`, `_MAX_DRAIN_LIMIT=50`, `config.comms.fleet_limit`) is a window, not a
denominator; `_comms_footer` per R1 + L1 + L2 (one helper, the SINGLE exit of each of the three
dispatchers, per-ACTION-OUTCOME trigger, mutation-proven shared); the optional `agent`/`session`
parameters and the `_INSTRUCTIONS` update; **#219** (all FOUR prose sites); 04a residuals **R-5**
(`_comms_dispatch`'s `Raises:` omits `MessageLedgerError`) and **R-12** (`brief_ack` has no
tool-seam teaching pin).
**Exit:** full gates + cold audit + **deploy = rebuild + recreate BOTH** + smoke; a blocked task
chain renders its critical path; the footer appears only for a resolved caller with pending
traffic; #219 + #247 resolved; INDEX rows + Log.

## Surfaced, NOT taken (operator's call, no ruling sought yet)
- ~~`TaskLedger._is_blocked` computes "blocked" client-side over an UNBOUNDED
  `SELECT * FROM task`~~ → **RULED INTO 04b-1 as #253** (operator, 2026-07-28), and the symbol
  named here was WRONG — see the #253 block in 04b-1's scope.
- **04a residual R-7 is unfixable as written.** "Widen #105's own text" cannot be done: #105 is
  already `resolved` with a full corrective note, and `lore_findings` has no verb that edits a
  subject line (that gap IS finding #129). The subject still reads *"latent today"*.
