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
