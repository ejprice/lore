# REPORT-contract-04b1 — the test contract for packet 04b-1

brief-base v7 read

*Every claim in this file is scoped to **branch `feat/surreal-unification` at `c5a2552`,
2026-07-28**, with this contract's own edits applied. "RED today" means RED at that state.
No production file was written, stubbed or edited. The production store `:18500` was never
touched; every live pin ran against spike-surreal `ws://127.0.0.1:18000`.*

---

## SUMMARY BLOCK

- **state:** done-with-deviations (3, below) · **80 new pins** in one new contract file, plus
  6 pins added / 1 renamed / 1 fixture hardened in `test_enforced_relations.py`.
- **deviations:** (1) `_enforced_relations_scaffold.py` edited beyond `KNOWN_RELATION_EDGES`
  — `seed_endpoint` gained a `task` row and `edge_set_clause` a `blocks` entry, because the
  fifth edge's vocabulary *is* part of declaring it and a local copy would be #102's shape;
  (2) the fifth edge's name is a scaffold **literal** (`BLOCKS_RELATION_NAME`), not an
  import — importing a not-yet-existing `BLOCKS_RELATION` would make THREE files
  UNCOLLECTABLE rather than RED (#133), and a pin holds the two equal; (3) PROOF 3 was run
  **piped to `tail`**, so its shell `$?` was tail's — the `PROOF HELD` line is printed only
  on the tool's success path and is the receipt; PROOF 4 was run unpiped with `EXIT=0`.
- **`Packages considered:`** *transitive/critical-path traversal* → SurrealDB's own
  `@.{1..n+collect}` recursive-path operator; read: `REPORT-probe-pkt04-store.md` §5.1 +
  the engine's v3.2.0 spec `language/graph/path_collect.surql` it cites → **replace** (never
  a client-side BFS). *Cycle detection over persisted ids* → `networkx` evaluated and
  rejected — the graph lives in the store, so a client-side DFS would need the whole edge
  set client-side (the `_is_blocked` unbounded-read shape this repo already ledgers);
  read: probe §5.4's measured self-reach detector → **replace with the engine operator**;
  the batch-local half already exists in-house as `AppContext._find_key_cycle`.
  *Row-existence policy* → `loremaster.agent_existence` (in-house, packet 04a); read: the
  module source, signatures quoted in §L3 below → **reuse via generalisation**, never a
  second implementation.
- **decisions-needed: 5 escalations**, each with both readings written down and a pinned
  recommendation — E-1 edge direction · E-2 identity rendering with no label · E-3 the
  transitive read's direction + bound behaviour · E-4 #247's check order · **E-5 (NEW, not
  in the brief): the "widen the mutation proof to five edges" instruction is not uniformly
  satisfiable** — see §C.
- **gates:** `./scripts/typecheck.sh` → **OK, all five members, 0 errors** (170 loremaster
  source files) · `uv run ruff check .` → **All checks passed!** · `pytest -n auto`:
  `test_blocks_edge.py` **72 failed, 8 passed** (80 collected) · `test_enforced_relations.py`
  + `test_derivation_source_unification.py` **3 failed, 70 passed, 19 skipped** ·
  regression sweep `test_surreal_schema/test_brief_ledger/test_message_ledger/
  test_retry_seam/test_task_ledger` → **1220 passed, 14 skipped**.
- **mutation proofs EXECUTED (2 of 5):** PROOF 3 (`briefed`) **PROOF HELD 12/12**; PROOF 4
  (`to`) **PROOF HELD 6/6, EXIT=0**; both restored the tree byte-exact (md5
  `dc5dc6f18eb6dc87dbb8cd8d26df417d`). PROOF 4 found a coupling 04a's block never recorded.
- **`loremaster.__file__` receipt:** not applicable — **no scratch copy was made.** Both
  mutation proofs ran `./scripts/mutation_proof.py` against the REAL tree, which takes a
  CONTENT backup and verifies byte-exact restoration (the always-sound alternative named in
  brief-base §6).
- **receipt POINTERS:** §A–§K below (one per brief requirement) · §ESCALATIONS · §RESIDUALS ·
  the contract's own `MUTATION_PROOF` block at the foot of `test_blocks_edge.py`.

---

## Files written

| file | what |
|---|---|
| `loremaster/tests/test_blocks_edge.py` | **NEW** — the 04b-1 contract, 80 pins |
| `loremaster/tests/test_enforced_relations.py` | R-1 (`ack` leg + its control), R-2 (id shapes, both halves), the fifth-edge declaration's consequences, the `MUTATION_PROOF` block widened |
| `loremaster/tests/_enforced_relations_scaffold.py` | the fifth edge declared: `KNOWN_RELATION_EDGES`, `BLOCKS_RELATION_NAME`, `seed_endpoint`'s `task` row, `edge_set_clause`'s `blocks` entry |
| `REPORT-contract-04b1.md` | this file |

Nothing else was touched. No production file, no doc, no other test file.

---

## THE EXPECTED-RED SET

Declared, not transcribed. The contract is committed RED in every pin that describes the
CHANGE and GREEN in every control — which is which is stated in each class docstring.

**`test_blocks_edge.py`: 72 RED, 8 GREEN.** The 8 green are exactly the controls and
declarations that must hold today:

```
TestTheBlocksEdgeIsDeclared::test_blocks_is_in_the_DECLARED_edge_set
TestTheBlocksEdgeIsDeclared::test_blocks_is_NOT_in_the_DEFERRED_exemption_set
TestTheBlocksEdgeIsGuardedFromBirth::test_the_blocks_edge_carries_NO_required_edge_field
TestTheLedgersOwnMigrationPathLandsTheGuard::test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_blocks_edge
TestTheLedgersOwnMigrationPathLandsTheGuard::test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints
TestTheLedgersOwnMigrationPathLandsTheGuard::test_the_PRE_EXISTING_dangling_edge_and_the_task_ROWS_SURVIVE
TestSendRefusesAGhostSENDER::test_POSITIVE_CONTROL_a_REGISTERED_sender_is_DELIVERED
TestSendRefusesAGhostSENDER::test_a_GOOD_sender_with_a_BAD_recipient_still_raises_UnknownRecipientError
```

The last one is the 04a **regression** pin (the recipient guard and its vocabulary must
survive the sender guard landing beside it); the first BASELINE is what proves the old world
is genuinely un-guarded, so §B's rejections are caused by the migration and not the fixture.

**`test_enforced_relations.py`: 3 NEW RED, and all three are the DELIBERATE DECLARATION**
(04a contract §6.8 predicted them by name):

```
TestEveryRelationEdgeIsEnforced::test_the_relation_edge_set_is_EXACTLY_the_five_known_edges
TestEveryRelationEdgeIsEnforced::test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS[blocks]
TestEveryRelationEdgeIsEnforced::test_the_edge_declares_its_IN_and_OUT_endpoint_tables[blocks-endpoints1]
```

⚠ **Neither "fix" is legal**: removing `blocks` from `KNOWN_RELATION_EDGES`, or adding it to
`DEFERRED_TO_PACKET_43` (measured wrong build **W-C**). Both are pinned against from the
04b-1 side too (`TestTheBlocksEdgeIsDeclared`), so a builder who is not running
`test_derivation_source_unification.py` still meets the wall. **The wave gate must still
include that file** — it is the only guard on the exemption's exact contents, and it was
verified RUNNING and GREEN here (`7 passed, 19 skipped`).

⚠ **`[blocks-endpoints1]` — the parametrised suffix RENUMBERED.** Adding `blocks` to
`KNOWN_RELATION_EDGES` shifts every `endpointsN` index in
`test_the_edge_declares_its_IN_and_OUT_endpoint_tables`. Any declared-RED list carrying an
old suffix is now stale; take them from `--collect-only`, never from a report.

---

## A. The `blocks` relation table

**Pins** (`TestTheBlocksEdgeIsEmittedByBOTHGenerationPaths`,
`TestTheBlocksEdgeIsGuardedFromBirth`, `TestTheBlocksEdgeIsDeclared` — 12 pins):
both generation paths emit it · the two paths emit the **byte-identical** statement (derived
equality) · the `blocks` DEFINE TABLE is positioned **after** the `task` DEFINE TABLE in both
· `ENFORCED` in each slice · `OVERWRITE` not `IF NOT EXISTS` · `IN task OUT task` · no
required edge field · the schema exports `BLOCKS_RELATION` · declared, and NOT exempt · the ∀
sweep covers it.

**Wrong builds killed**

| wrong build | the pin |
|---|---|
| a new `_blocks_statements()` wired into `generate_task_ddl` only — the edge then auto-creates `TYPE ANY` on a store built by `generate_ddl`, silently discarding the IN/OUT guard (store ref §5) | `test_the_path_emits_the_blocks_relation_table[generate_ddl]` |
| declared twice, differently (ENFORCED in one path, not the other) | `test_BOTH_paths_emit_the_IDENTICAL_blocks_statement` — derived, never two hand-written expectations |
| the relation table emitted BEFORE the `task` table it names as both endpoints | `test_the_blocks_table_is_declared_AFTER_the_task_table_in_BOTH_paths` — the SELF-order-dependence reader §Q2.4 item 6 flagged as *"a different and unexamined shape"* |
| `IF NOT EXISTS` (harmless on day 1, #107 on the day anyone changes IN/OUT/ENFORCED) | `test_the_blocks_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS` |
| a required edge field, making the edge carry state `blocked_by` cannot — the mirror invariant then cannot be *stated* | `test_the_blocks_edge_carries_NO_required_edge_field` (measured over emitted `DEFINE FIELD` statements, not a text scan) |

**Fixture axes varied:** generation path (2, parametrised so a miss NAMES the path);
statement POSITION (derived from the emitted list, not asserted as a literal).

---

## B. Migration + the un-enforcing door

**Pins** (`TestTheOldWorldIsGenuinelyOlder`, `TestTheLedgersOwnMigrationPathLandsTheGuard`,
`TestTheUnEnforcingDoor` — 7 pins). The old world is DERIVED from the production emitter (a
removal of the `blocks` statement), with its own anti-vacuity pin. The migration is driven by
**`TaskLedger.ensure_ready()` and nothing else**.

⚠ **Reader §Q2.4 item 4 asked whether `TaskLedger` even HAS an `ensure_ready`. It does** —
`tasks.py::TaskLedger.ensure_ready` applies `generate_task_ddl()` inside ONE `BEGIN … COMMIT`
via `execute_transaction`. Verified 2026-07-28. So `TaskLedger` is the right owner to drive,
and the W-A pin has a real subject.

**Wrong builds killed**

| wrong build | the pin |
|---|---|
| **W-A** — emitter perfect, `ensure_ready` never lands it (04a measured this build at **38/38 and 6 failed/2073 passed over seven suites, the SAME six the correct build has**) | `test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE`, which applies NO DDL itself |
| a guard that rejects everything (a botched DDL / wrong endpoint type) | `test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints` |
| a migration that raises on the second boot (the `DEFINE SEQUENCE` failure mode) | `test_the_migration_is_IDEMPOTENT_on_an_ALREADY_migrated_store` |
| a migration that destroys pre-existing rows or "cleans" ghosts (#236 is ruled OUT) | `test_the_PRE_EXISTING_dangling_edge_and_the_task_ROWS_SURVIVE` |
| **the un-enforcing door** — `OVERWRITE` without `ENFORCED` silently un-guards, invisibly on a virgin DB | `test_re_emitting_blocks_WITHOUT_ENFORCED_silently_un_guards_it`, which first asserts the guard WAS live |
| a vacuous migration (old world ≡ new world, so every pin migrates a schema to itself) | `test_the_old_world_DIFFERS_from_todays_task_ddl` |

**Fixture axes varied:** the dirty store is dirty in the way production is — task ROWS
present, plus a **pre-existing dangling edge** written while the table was undeclared (store
ref §5's `TYPE ANY` auto-create is what makes that possible, and it is the realistic
pre-04b-1 state, not a hypothetical).

---

## C. The mutation proof, WIDENED — **and an escalation (E-5)**

⚠ **The brief's premise, corrected before use.** 04a's proof covers ONE edge and its
single-entry scope is DELIBERATE (`REPORT-contract-04a-enforced.md` §S4(a): *"a proof still
declaring four edges would produce declared reds that stay GREEN"*). Confirmed by reading
`FLIPPED_BY_04A` at HEAD: one tuple.

**E-5 — THE WIDENING IS NOT UNIFORMLY SATISFIABLE, and I will not paper over it.**
`briefed`, `to` and `blocks` carry `enforced=True`, so their per-edge mutation is deleting
it. **`refers` and `answers_to` carry no `enforced=True` to delete** — they are deliberately
un-enforced pending packet 43. A five-edge proof using ONE mutation would declare reds that
stay green for two of the five, which is exactly the direction the both-ways diff exists to
catch. **Reading I pinned:** five PER-EDGE proofs, each mutating what that edge's pins
actually read — `enforced=True` for the three guarded edges, an IN/OUT swap for the two
deferred ones (proving THEIR pins are live rather than that their guard is). **Alternative
reading:** one mutation of the shared `_define_relation_table` emitter's `enforced_clause`,
which reddens every guarded edge at once but discriminates none of them per-edge. Lead's
call; the block is written for the first reading and says so.

**EXECUTED, 2 of 5 (both against the real tree, restored byte-exact):**

- **PROOF 3 — `briefed`.** `PROOF HELD — 12/12`, no unexpected reds, no declared-green.
  Declared = 04a's 8 + this contract's 3 already-RED declaration pins + **the new `ack`
  leg**, which reddened exactly as predicted. 04a's block was updated in place with that
  entry and a note saying why.
- **PROOF 4 — `to`.** `PROOF HELD — 6/6`, `EXIT=0` (unpiped).
  ⚠ **AND IT FOUND SOMETHING 04a's BLOCK NEVER RECORDED:**
  `TestTheSharedPolicyIsTheSOLEDecisionPoint::test_MUTATION_neutralising_the_shared_policy_lets_send_reach_the_ENGINE`
  is COUPLED to `to`'s clause — it neutralises the app policy precisely so the ENGINE's
  rejection is what it measures, so un-enforcing `to` makes it DID-NOT-RAISE. A three-entry
  declaration would have reported an unexpected red and read as a wrong prediction. This is
  the both-ways diff earning its keep on its first use here.
- **PROOFS 1, 2 and 5 — NOT EXECUTED**, and why is stated in the block: 1 and 2 mutate code
  that does not exist yet (a no-op anchor, `EXIT=3`); 5 was not run for time. Their declared
  sets are labelled PREDICTIONS.

**Discipline followed:** every declared node id came from `pytest --collect-only -q`
(collecting names tests without running them, so the set is fixed before any result exists);
never transcribed from output. `--show-capture=no` on the child (04a fixwave §F1: a captured
log line otherwise mimics a summary line).

---

## D. The edge-set declaration

Done, and **said out loud**: `blocks → (task, task)` added to `KNOWN_RELATION_EDGES`;
`test_the_relation_edge_set_is_EXACTLY_the_four_known_edges` **renamed** to `…_five_…` with
its docstring rewritten to record that its own previous version predicted this reddening and
that it IS the declaration. `test_derivation_source_unification.py` — the ONLY guard on the
`DEFERRED_TO_PACKET_43` exemption — **runs and passes: `7 passed, 19 skipped`** (the 19 are
packet 43's own skipped pins).

---

## E. `create_task` becomes atomic

**Pins** (`TestCreateTaskIsAtomic` — 4). The instrument: neutralise the app-level check so
the ENGINE's `ENFORCED` rejection is what the RELATE meets, then ask whether a task row
exists. One transaction ⇒ the CREATE rolls back ⇒ no row. A separately-failable RELATE ⇒ the
row is there ⇒ RED.

**Wrong builds killed:** **W-D** — *write first, compensate afterwards* — which 04a measured
as **GREENER than correct** (`2 failed, 2077 passed` vs the correct build's `6 failed, 2073
passed`); *the incentive gradient points at the wrong build*. Also a build that refuses
everything (killed by the positive control), and a run where the monkeypatch silently did not
take (killed by `test_POSITIVE_CONTROL_the_neutralised_policy_still_lets_a_LEGAL_create_through`).

**Fixture axes varied:** `create_task` and `create_many` are pinned **separately**, on the
scout's explicit warning (*"a contract that only pins `create_many` will miss it"*) — their
transaction shapes differ and a fix may reach one. The positive control uses **TWO** blockers,
not one: with a single blocker `len(edges) == 1` is satisfied by a build that writes exactly
one edge regardless of dependency count (the small-N trap where `len()` and the real count are
indistinguishable).

---

## F. The mirror invariant, under THE QUANTIFIER LAW

**Pins** (`TestTheMirrorHoldsAtEveryWritePath` — 8, plus one exact-set coverage pin). ONE
`_assert_mirror(ledger, task_id, where=...)` helper every write-path pin calls — never a
pattern each pin clones. The property is *the edge set equals `blocked_by`, for EVERY task,
after EVERY verb*, and each verb's fate is FORCED by its own fixture:

| verb | fate, forced |
|---|---|
| `create_task` | mirrors — blocker counts **0 / 1 / 3**, plus a DUPLICATE-blocker leg |
| `create_many` | mirrors — including a **FORWARD reference** (item 0 blocked by item 1's pre-minted id) |
| `supersede_task` | successor born UNBLOCKED with **no** `blocks` in-edges; predecessor keeps its own — **old-behaviour-preserved DELIBERATELY** (scout §A2-FLAG 2; spec-silent, consistent with today's row) |
| `transition` / `claim_task` | must NEVER touch it — ∀ over a full lifecycle (claim → in_progress → done, twice) |
| every other public verb | adjudicated in `NON_WRITING_VERBS` |

**The coverage pin** `test_EVERY_public_TaskLedger_verb_is_ADJUDICATED` derives the public
async verb set from the class by **AST** and holds it equal to
`MIRRORING_VERBS ∪ MIRROR_IMMUTABLE_VERBS ∪ NON_WRITING_VERBS` — deny-by-default, so a SIXTH
write verb next packet cannot silently escape the invariant. (Reader §Q4 A6: 04a's
*"one fixture, no test edits"* spec turned out to have SIX call sites, and the sweep built to
catch that MATCHED ITSELF. Coverage is a CHECKED VARIABLE here, not a derivation done once.)

**Wrong builds killed:** a mirror that RELATEs the RAW `blocked_by` list (two edges for one
dependency — the duplicate leg) · a build that emits `CREATE_0, RELATE_0, CREATE_1, RELATE_1`
(the forward-reference leg: under `ENFORCED` item 0's RELATE rejects an endpoint the very
next statement would have created) · a build that "keeps the edge in sync" on transition,
silently making `blocked_by` mutable and breaking the claim path's stated assumption · a
build that garbage-collects the predecessor's edges on supersede.

**Fixture axes varied:** blocker COUNT (0/1/3), duplicate ids, batch ORDER (forward
reference), lifecycle depth (two blockers each driven through three transitions).

⚠ **UNMEASURED STORE BEHAVIOUR, stated rather than assumed.** The forward-reference leg
mints **both** endpoints inside one transaction. Reader §Q2.5: 04a measured that `ENFORCED`
resolves an **out** endpoint created earlier in the same uncommitted transaction and left the
**in** side unmeasured. If the engine cannot do it, that is a STOP and an escalation — **not**
a licence to move the edges out of the transaction, which is W-D.

---

## G. Acyclicity over PERSISTED ids

**Pins** (`TestACycleIsDetectedOverPERSISTEDIds` 4, `TestCreateRefusesToFormACycle` 4).

**The discriminating fixture is the whole point.** Probe §5.4: the bare idiom "detected" a
4-cycle **by arithmetic accident** (depth 8, 8 mod 4 = 0) — *a positive result for the wrong
reason*. With a **3-cycle** the same query returns a different node and reports ACYCLIC. So
the cycle fixtures are **3, 4 and 5** — no small explicit bound is a multiple of all three —
plus an ACYCLIC control that stops the lot passing on a build that answers "cycle" to
everything, and which doubles as the `+inclusive` pin (an inclusive traversal makes every
task look cyclic).

Cycles are **raw-seeded** into the store, bypassing the ledger, and the file says why: once
04b-1 lands the ledger refuses to create one, and *a detector that can only be tested through
the guard that prevents the condition is a detector nobody has tested*.

**The two reachable holes today**, both invisible to `AppContext._find_key_cycle` because it
filters its edge set to `ref in key_index`: a batch whose items name each other's **pre-minted
IDS**, and a **SELF-loop** (`ids=[X]`, `blocked_by=[X]`) — which `ENFORCED` structurally
cannot catch, because by RELATE time X genuinely exists. A cyclic task can never be claimed,
so this is the same silent black hole R3 describes for phantom blockers.

**Wrong builds killed:** a bare-idiom detector (the 3- and 5-cycle legs) · a batch-local-only
DFS (the persisted-reach leg) · a build that refuses every batch carrying any intra-batch
dependency (the 4-deep legal-chain positive control) · a cycle error indistinguishable from
an existence error (`test_the_CYCLE_error_is_NOT_an_existence_error`, derived from the raised
values, W-F's shape).

---

## H. The transitive read

**Pins** (`TestTheTransitiveBlockerRead` 5, `TestTheReadIsHONESTAtItsBound` 4).

**Fixture floor met and exceeded:** the `branching_dag` fixture is **4 deep, branching AND a
diamond**, plus two controls (a leaf, an isolated node). `leaf`'s transitive blockers are four
nodes; its TERMINAL-DEPTH blockers are `{root}` alone — that is the discrimination, and the
diamond additionally proves the closure DEDUPLICATES. A 2-node chain, which is all this repo
has ever had, cannot tell the two apart.

**The bound: DECIDED, not deferred — and it is escalation E-3.** Silent truncation is a
trust-doctrine defect (probe §5.3 measured `{..256+collect}` returning 256 of 299 with no
error and no signal). **Pinned:** the helper returns a typed result carrying `truncated`, and
the instrument is a **DISCRIMINATING PAIR** — a 5-chain read at `max_depth=2` must report
`truncated=True` with exactly the in-bound nodes, and a 3-chain read *at the same depth* must
report `False`. One fixture proves neither; a build hard-coding either value dies on one leg.
The rejected alternative (RAISE at the bound) is recorded in the file: it makes a legitimately
deep DAG unreadable rather than honestly partial.

**Wrong builds killed:** the bare `@.{1..n}` idiom the packet itself used to prescribe · a
build returning `[]` for an absent task (`TaskNotFoundError` is pinned — `[]` for absent and
`[]` for unblocked are the same answer to two different questions) · a build reading the edge
TABLE rather than traversing FROM the task (the isolated-node control catches it where the
leaf control does not) · a default bound at or past the engine's 256 ceiling.

⚠ **One TEXT pin, with its bound stated in its own docstring:**
`test_the_traversal_statement_carries_collect_AND_a_SELECT_level_TIMEOUT` captures the
statement through the `_query` seam and asserts `+collect` and `TIMEOUT` are present. **It
does not check that the timeout ever fires, and does not pretend to.** It exists because
`TIMEOUT` is a `SELECT` clause and a PARSE ERROR on a bare idiom (probe §5.2), so its absence
usually means the bare form is in use — and because which brake fires, depth or wall-clock, is
a property of the DATA and not the query (probe §5.5), so the design needs both plus the
explicit bound.

---

## I. The blocker-existence pre-check — ONE IMPLEMENTATION (L3)

**Pins** (`TestAPhantomBlockerIsRefusedAndNamed` 15 incl. parametrisation,
`TestTheRowExistencePolicyHasONEImplementation` 6).

**The shared policy as it actually ships** (read from the module, since reader §Q1.1 warns no
report quotes it):

```python
class UnknownAgentRowError(RuntimeError): ...
def format_unknown_agent_refusal(unknown_name_by_id: Mapping[str, str]) -> str: ...
async def reject_unknown_agents(
    query: AgentQuery, agents: Sequence[AgentRefLike], *,
    error: type[UnknownAgentRowError] = UnknownAgentRowError,
) -> None: ...
# AgentQuery = Callable[[str, dict[str, Any]], Awaitable[Any]]
```

Its served sentence is pinned BY VALUE in 04a's `_served_refusal`, so the generalisation must
keep the agent text **byte-identical**. The contract therefore pins a shared **skeleton**
`unknown {noun}(s): {identities} — {requirement}` with the agent vocabulary unchanged and a
task sibling sentence pinned by value in `_served_task_refusal`.

**Sharing is proven by MUTATION, three ways, all in-suite and runnable:**

1. neutralise the generalised policy inside `loremaster.tasks` → the phantom must reach the
   ENGINE (a private copy underneath still refuses ⇒ RED);
2. neutralise it inside the **SHARED MODULE** → the AGENT verb must ALSO stop deciding —
   **this is the pin that proves the generalisation LANDED**, because a *"generalise it and
   also keep the old body"* build (copy #2 wearing a compatibility shim) keeps refusing;
3. replace the shared **FORMATTER** with a sentinel → **both** families' served text must
   change, in ONE run, from TWO call sites. That is L3's demanded proof (*"change the shared
   refusal text and BOTH the agent pins and the new task pins must go RED"*) as a runnable
   pin; its shell counterpart (PROOF 2) adds what a monkeypatch cannot — that the two ride
   ONE LITERAL, not merely one function.

Plus `test_the_two_families_errors_share_a_base_from_the_SHARED_module`, **derived from the
raised values** (not a name-keyed handle), asserting the shared base's `__module__` is the
policy module AND that the task error is still a `TaskLedgerError`.

**Wrong builds killed:** **W-B** — the policy keyed on the one fixture literal, which passed
04a's whole contract 38/38 — killed by parametrising every negative leg over **four**
differently-constructed phantom ids · a build naming only the FIRST phantom (the
`ENFORCED`-leaning build) — killed by the 3-phantoms-plus-one-real leg · a build that refuses
the whole list unexamined — killed by asserting the REAL blocker is *not* named · a build
that stopped sorting or changed the join — killed by the served-text pin with two phantoms in
non-sorted order · **W-E** routing≠sharing, both directions, above.

**Fixture axes varied:** id SHAPE ×4 (native 32-hex, **dashed uuid** → the bracketed
`task:⟨…⟩` rendering, all-numeric, dash-bearing temp-key shape) · phantom COUNT (1 and **3**)
· mixed real+phantom · empty dependency list in **both** spellings (`None` and `[]` — they
travel different lines of `_new_task_content`, and `None` is what reaches the shared policy's
empty-input early return, which 04a's adversary §P3 measured as UNREACHABLE through both
existing entry points).

---

## J. #247 — the sender door

**Pins** (`TestSendRefusesAGhostSENDER` — 9 incl. parametrisation). Refused BEFORE the write,
NAMING the sender; **no message row AND no `to` edge** after (the pin that distinguishes
*refused early* from *rolled back late*, and a rollback that reclaimed the row but left an
edge is a third outcome the two counts separate); positive control with a real sender.

**E-4 pinned:** the sender is validated in its own call, BEFORE the recipients, with its own
error vocabulary. `test_a_BAD_sender_and_a_BAD_recipient_refuse_on_the_SENDER_FIRST` asserts
the raised error is **not** `UnknownRecipientError` and that the recipient's id is **not**
named — today it fails with exactly the defect in the message
(`UnknownRecipientError('unknown agent(s): phantom-fixer (…)')`).

**Wrong builds killed:** a hand-rolled sender check (killed by
`test_the_sender_refusal_routes_through_the_SHARED_policy`, whose observable is deliberately
that the send **SUCCEEDS** under a neutralised policy — because `sender` is a FIELD and not an
endpoint, so no `ENFORCED` backstop exists; that IS the door, reproduced) · folding the sender
into the recipient call (E-4 pin) · dropping 04a's recipient guard while adding the sender one
(the GREEN regression pin).

**Fixture axes varied:** two sender shapes, the second wearing the **registered** prefix so a
refusal keyed on a prefix/literal/length accepts it.

⚠ **Removed-behaviour note for the builder:** closing this makes
`MessageLedger._reject_unknown_recipients`' name and docstring inaccurate (they say
*"recipients"*), and `send`'s `Raises:` gains an entry. That is the #219 class, one packet
later, inside the fix for #247 — adjudicate it, do not leave the prose teaching a contract the
code no longer has.

---

## K. 04a residuals

**R-1 — CLOSED.** `TestTheSharedPolicyIsTheSOLEDecisionPoint` gained
`test_MUTATION_neutralising_the_shared_policy_lets_ack_reach_the_ENGINE` **and its positive
control**. The observable is non-obvious and the docstring states it: with the app check
neutralised, `_relate_briefed` DOES catch the engine's rejection in the `except
SurrealStoreError` that is its idempotent-re-ack signal, then `_select_briefed_edge` finds no
edge to attribute it to and **re-raises** — so the correct build surfaces `SurrealStoreError`
and NEVER `already_acked=True`. **Measured RED under the `briefed` mutation in PROOF 3**, and
added to 04a's declared set (which would otherwise have reported an unexpected red).

**R-2 — CLOSED, both halves.** Negative: `UNREGISTERED_AGENT_IDS` grew from 2 to 5 with a
dashed-uuid, an all-numeric and a dash-bearing shape. **Positive** — the half that matters
more: the fixture's `registered_id` was `f"registered_agent_{uuid4().hex}"`, a BARE id, so no
leg of the file, positive or negative, ever exercised the bracketed rendering. It is now a
dashed uuid, with an anti-vacuity assertion that `str(RecordID(AGENT_TABLE, id))` really does
contain `⟨` — so a future SDK change reverts loudly rather than silently restoring the blind
spot. **Receipt: the change is GREEN**, which independently confirms that 04a's shipped policy
handles the bracketed rendering correctly (it matches the engine's echo against its own
`str(RecordID)` renderings, symmetric by construction).

---

## ESCALATIONS

Each is ONE edit to overturn, and each is written into the contract file's module docstring
so a builder meets it there too.

| # | fork | pinned | alternative | why I picked it |
|---|---|---|---|---|
| **E-1** | edge DIRECTION | `RELATE $blocker->blocks->$task` (`in` = blocker) | `task->blocks->blocker` | reads as English AND puts the newly-created row on the `out` side — the side 04a MEASURED resolves inside an uncommitted txn (§Q2.5); the alternative rides the unmeasured `in` side |
| **E-2** | identity rendering with no display label | `name (id)` where a label exists (agent, byte-identical to 04a), **bare id** where none does (task) | force a label ⇒ `abc (abc)` | a task has no name at the call site; `abc (abc)` teaches a reader that it does — a trust-doctrine wart |
| **E-3** | the transitive read's direction + bound | transitive **blockers** (upstream); typed result with `truncated` | downstream; or RAISE at the bound | upstream is what 04b-2's *"renders its critical path"* needs; RAISE makes a deep DAG unreadable rather than honestly partial |
| **E-4** | #247 check order | sender validated FIRST, own vocabulary | one call, one error class | a refusal that mis-names the role is one an agent acts on wrongly. **Cost, stated: one extra round trip on the send path** |
| **E-5** | "widen the mutation proof to five edges" | five PER-EDGE proofs, two mutation shapes | one mutation of the shared emitter's `enforced_clause` | `refers`/`answers_to` have no `enforced=True` to delete; one mutation for all five declares reds that stay green |

---

## RESIDUALS — every item on its own line, with its own verdict

| # | item | verdict |
|---|---|---|
| R-a | **Concurrency is unpinned.** Two racers can form a cycle neither sees (a genuine TOCTOU; reader §Q6-O16). | **DELIBERATELY NOT PINNED — flagged, not dropped.** A contract pin is the wrong instrument (≥8-way, 20 consecutive green runs). Needs a measurement task, not a test. **Operator's call.** |
| R-b | **The forward-reference batch mints BOTH `blocks` endpoints in one transaction; nothing has measured whether `ENFORCED` resolves an `in` endpoint created in the same uncommitted txn.** 04a measured only the `out` side. | **UNMEASURED, pinned anyway.** If the engine cannot do it, that is a STOP and an escalation — not a licence to move the edges out of the txn (W-D). |
| R-c | The `blocks` DDL adds a statement to the task slice; 04a residual **R-11** notes `old_world_ddl` uses `str.replace` with no `count=1`. | **Not triggered here** — this contract's old world is a REMOVAL (`_task_ddl_without_blocks`), not a replacement, and it has its own anti-vacuity pin. R-11 stays open for its own path. |
| R-d | 04a residual **R-10**: the scaffold's `statements()` splits DDL on a bare `;`. | **Not triggered** — the `blocks` DDL adds no ASSERT and therefore no teaching prose containing a semicolon. Would trigger the day it does. |
| R-e | 04a residual **O14 / D7**: `test_surreal_store.py::test_the_whole_schema_migrates_an_existing_populated_store` applies four slices and not the guarded-edge ones. A fifth edge widens that gap again. | **OPEN, not fixed** — that file is outside my writable set. *"One line plus a seed row."* Recommend the builder or 04b-2 close it. |
| R-f | 04a residual **O21**: SEVEN hand-rolled `_bare_id` copies package-wide, `tasks.py` among them. This packet edits `tasks.py`. | **OPEN, and now higher-risk.** An EIGHTH copy is one careless line away, and the uuid-shaped parse is the one that cost 130 red pins. The contract's helpers decode with `record::id(...)` server-side and never a client-side `split(":")`, and say so. |
| R-g | 04a residual **O7 (A3)**: `_BRIEF_NAME = "project"` monoculture, recommended and never done. | **STILL OPEN.** Untouched here — it is inside 04a's pins and outside my (a)/(b) writable grant. |
| R-h | 04a residual **O8 (A4)**: the `via=` closed-set monoculture (`register` never exercised). | **STILL OPEN**, untouched. Low risk, named. |
| R-i | 04a residual **O13**: `brief_ack` has no tool-seam teaching pin. | **OPEN** — routed to 04b-2 by §04b SPLIT (its R-12). Not mine. |
| R-j | PROOFS 1, 2 and 5 are unexecuted. | **BY CONSTRUCTION for 1 and 2** (their anchors do not exist yet; running them would exit 3). **For 5 it is a time choice, stated.** The builder runs all five. |
| R-k | PROOF 3 was piped to `tail`, so the shell `$?` was tail's. | **DISCLOSED.** The `PROOF HELD` line is printed only on the tool's success path, and I read it. PROOF 4 was unpiped with `EXIT=0`. Do not pipe where a shell decides. |
| R-l | The contract names five production symbols that do not exist (`BLOCKS_RELATION`, `reject_unknown_rows`, `format_unknown_row_refusal`, `transitive_blockers`, `TASK_BLOCKER_MAX_DEPTH`). | **DELIBERATE, and each fails CLOSED.** They are MUTATION POINTS, which unavoidably have names. Renaming any is legal and costs ONE edit, in the constants block at the head of the file, which says so. A red pin naming one is a NAMING mismatch, not a behavioural one. |
| R-m | The scaffold now carries the edge name as a LITERAL (`BLOCKS_RELATION_NAME = "blocks"`) rather than an import. | **DELIBERATE, pinned.** An import of a not-yet-existing constant makes THREE files uncollectable rather than RED (#133); `test_the_schema_exports_BLOCKS_RELATION_under_this_exact_name` holds the two equal, and the literal may be replaced by the import in one edit once the constant lands. |
| R-n | `TaskLedger._is_blocked` computes "blocked" client-side over an UNBOUNDED `SELECT * FROM task` (scout's *"surfaced, not taken"*). | **NOT PINNED, NOT IN SCOPE, RESTATED HERE so it is not lost.** The transitive helper this contract pins is a server-side traversal and does not fix it. Unfiled as of 2026-07-28. |
| R-o | `test_surreal_schema.py`'s `_REQUIRED_GUARDS` already rules `TABLE (RELATION) → OVERWRITE` tree-wide. | **NO ACTION** — verified compatible: the whole regression sweep (1220 passed) includes that file, and the `blocks` clause satisfies it by construction. |
| R-p | The 04a mutation-proof block's own prose still describes itself as covering 04a's single edge. | **CORRECTED IN PLACE** — a pointer to `test_blocks_edge.py`'s block was added, stating why the widening is not uniform, rather than leaving a reader to infer a four-edge proof that never existed. |

---

## FLAGS — things I noticed that nobody asked me about

1. **`test_the_edge_declares_its_IN_and_OUT_endpoint_tables`'s parametrised suffixes
   RENUMBERED** when `blocks` entered `KNOWN_RELATION_EDGES` (`endpointsN` is a positional
   index over a sorted dict). Any inherited declared-RED list carrying an old suffix is now
   stale. This is the line-number-citation hazard wearing pytest clothes.
2. **04a's `MUTATION_PROOF` block did not know that its own `send` leg is coupled to `to`'s
   clause.** Found by running PROOF 4 (§C). Nothing was wrong with 04a — it never had reason
   to declare a `to` mutation — but any future `to` proof needs the entry, and it is now
   written into `test_blocks_edge.py`'s block.
3. **The generalisation forces a decision 04a never had to make: what a refusal renders when
   there is no display label** (E-2). It is a served-surface decision under the trust
   doctrine, not a formatting detail, which is why it is an escalation rather than a note.
4. **`TaskSpec` has `extra="forbid"` and no `key` field** — the temp key lives on the
   DISPATCHER's item type, not the ledger's spec. Worth knowing before writing `create_many`
   fixtures; it cost me one mypy round.
