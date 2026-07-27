# REPORT-contract-04a-enforced — the packet-04a `ENFORCED` sweep contract

brief-base v7 read

> ⚠ **This artifact exists at TWO repo-root addresses, byte-identical and final:**
> `REPORT-contract-04a-enforced.md` (the EXACT name my spawn brief named — where the lead looks)
> and `REPORT-contract-04a-enforced-2.md` (`REPORT-<agent-name>.md`, per brief-base §1 — what the
> `TeammateIdle` gate checks). The two rules disagreed and the brief's name does not encode the
> agent-name suffix the never-reuse-a-teammate-name law adds on respawn, so both were written rather
> than one silently dropped. They cannot diverge: no further edits are planned. **Archive ONE**
> (either) into `docs/plans/v2/receipts/2026-07-26-packet04/` and delete the other, with a one-line
> header saying which address survived — a citation to the deleted name would dangle (#152).

*Every measurement below was taken **2026-07-26** against `feat/surreal-unification` @ `28387a0`
(clean tree). Live legs ran on **spike-surreal `ws://127.0.0.1:18000` (the TEST store) only** —
`:18500` was never contacted. Present-tense claims describe THAT tree; a future reader should
re-derive before relying on any number here.*

## SUMMARY BLOCK

- **state:** done-with-deviations — contract written; **three escalations, two of which change the
  packet's implementation scope** (D1, D2). No production module touched.
- **deviations:** (1) I ran an OFFLINE derivation probe (no store) to settle group I rather than
  assume it — it found a REAL violation (D2). (2) I added §A ∀-pins and §I controls the brief did
  not name; both were forced by the quantifier law.
- **Packages considered:** the shared unknown-agent policy (§E). Evaluated: reusing the in-house
  `MessageLedger._reject_unknown_recipients` (READ: its body + docstring; it is one
  `SELECT id FROM $ids` direct-record-access query, store-shaped and SDK-typed — no library does
  this) → **`replace` with an EXTRACTED in-house function, not a new hand-roll**; the mutation
  instrument → `pytest.MonkeyPatch` (READ: `monkeypatch.setattr(..., raising=True)` semantics —
  fails closed on a missing attribute) → **`replace`**, no bespoke patcher; the DDL mutation proof →
  the repo's own `scripts/mutation_proof.py` (READ: its `--expect-red` both-ways diff) →
  **`replace`**, not a shell block.
- **File:** `loremaster/tests/test_enforced_relations.py` (new, 60 pins). Groups A–I mapped in §1.
- **RED count: `26 failed, 34 passed in 5.41s`** (contract alone, `-n auto`). With neighbours:
  **`26 failed, 481 passed in 19.01s`** over
  `test_enforced_relations.py + test_brief_ledger.py + test_comms_schema.py + test_surreal_schema.py`
  — every failure is mine, by design. Gates: `ruff` **All checks passed!**; `scripts/typecheck.sh`
  **loremaster OK / lorescribe OK / loresigil OK**.
- **decisions-needed: 7** — §4. The two that block a builder:
  **D1** — the `briefed` flip turns **≥29 collected `[real]` ids in `test_brief_ledger.py` RED**:
  that file's fixture never creates an `agent` table, so **every `briefed` edge its suite writes is
  already a dangling edge**. Fixing it is OUTSIDE my writable set; exact edit in §4.D1.
  **D2** — **P5's condition does NOT hold universally.** `{edge.src} ⊆ {node.qualified_name}` holds
  for all 56 production modules AND 8 adversarial shapes, but it is **not structural**: the two
  derivations read different inputs, and a divergence makes `build_file_graph_fragment` RELATE from
  a `code_node` it never created. Today invisible; after the flip it **fails the whole file's index
  transaction**. Fix belongs in the fragment builder — this widens 04a's implementation scope.
- **receipt pointers:** §1 group map · §2 satisfiability, per pin · §3 what wrong build survives ·
  §4 decisions/escalations · §5 removed-behaviour inventory · §6 WHAT I COULD NOT DETERMINE.

---

## 1. The contract, by group

`loremaster/tests/test_enforced_relations.py` — 60 pins. "RED"/"GREEN" below is **at `28387a0`**.

| group (brief) | class | pins | RED | GREEN |
|---|---|---|---|---|
| **A** the flip | `TestEveryRelationEdgeIsEnforced` | 14 | 4 | 10 |
| **B** dirty-store migration | `TestTheOldWorldDerivationIsNotVacuous` + `TestTheEnforcedFlipMigratesADirtyStore` | 18 | 6 | 12 |
| **C** un-enforcing door + mutation | `TestTheUnEnforcingDoor` + the `MUTATION_PROOF` block | 3 | 3 | 0 |
| **D** ghost-member reading | `TestADanglingEdgeReadsAsAFirstClassMember` | 2 | 0 | 2 |
| **E** ONE IMPLEMENTATION | `TestTheUnknownAgentPolicyHasONEHome` | 5 | 5 | 0 |
| **F/H** publish's contract | `TestPublishRefusesAnUnregisteredAgent` + `TestPublishWithARegisteredAgentStillWorks` | 6 | 4 | 2 |
| **G** shared-catch hazard | `TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent` | 2 | 1 | 1 |
| **F(3)** send | `TestSendRefusesBeforeTheWrite` | 3 | 1 | 2 |
| **I** the P5 condition | `TestTheCodeGraphFragmentNeverRelatesFromAnUncreatedEndpoint` + `TestTheDerivationsAgreeOnSourceNames` | 6 | 1 | 5 |
| — new, not briefed | `TestTheBriefSliceIsOrderDependentOnTheAgentSlice` | 1 | 1 | 0 |

Two shape decisions worth stating once, because they are what makes this a contract:

**The universal is a ∀ over the EMITTER's output, never a list of edge names.**
`test_EVERY_relation_table_the_schema_emits_is_ENFORCED` sweeps all nine DDL generators and parses
the `DEFINE TABLE … TYPE RELATION` statements out of the text. Packet 04b's `blocks` edge is
therefore pinned before it exists, and a fifth edge cannot arrive un-guarded. Repo law: *when you
catch yourself enumerating what is FORBIDDEN you have already lost.* The four per-edge pins beside
it are not the invariant — they are the DECLARED-RED target set of the group-C mutation proof.

**The old world is DERIVED from the production emitter.** `_old_world_ddl()` re-emits a slice with
the target relation's statement replaced by `_define_relation_table(rel, in_t, out_t,
enforced=False)` — the same emitter production calls, with the old argument. A hand-written old-DDL
string tests a *copy* of the code and passes while production stays broken (scout §S4). The
"is this fixture testing anything?" question gets its **own** pin
(`TestTheOldWorldDerivationIsNotVacuous`) rather than hiding inside a helper's exception, so the
BASELINE/survival/idempotence controls stay honestly GREEN and only the change-pins go RED.

---

## 2. The satisfiability argument — why each RED is RED **for the right reason**

Verified by `pytest --tb=line`; the failure *text* of every red pin was read, not just its count.
**No red comes from a `TypeError`, a collection error, or a pre-existing pin this contract
contradicts.** The four failure modes, exhaustively:

**(a) An assertion about the missing DDL clause — 4 pins.** Verbatim:
`AssertionError: every TYPE RELATION table this schema emits must carry ENFORCED … Un-guarded:
{'briefed': …, 'refers': …, 'answers_to': …}` and three per-edge equivalents. A correct build
changes the emitter and they pass.

**(b) An assertion that the old-world derivation is vacuous — 3 pins.** `re-emitting 'briefed' with
enforced=False does not change the DDL, which means today's generator ALREADY emits it
un-enforced — the flip has not happened.` This is the intended reading: today old ≡ new for these
three edges. After the flip the derivation differs and the pin passes.

**(c) `DID NOT RAISE` — 14 pins.** Every live guard/refusal pin. The store legs
(`test_the_guard_is_LIVE_…`, `TestTheUnEnforcingDoor`, `TestTheBriefSliceIsOrderDependent…`) reach a
live engine, apply real DDL through `execute_transaction`, write a real dangling RELATE, and observe
it accepted. The ledger legs (`TestPublishRefusesAnUnregisteredAgent`,
`TestTheIdempotentReAckSignal…`) drive the REAL `BriefLedger` against a database where the `agent`
table exists and the id is verified absent — and today publish/ack simply succeed. **Nothing here
errors; the code runs and does the wrong thing**, which is the only red that proves a behavioural
contract.

**(d) The intended contract-first absences — 5 pins.**
`ModuleNotFoundError: No module named 'loremaster.agent_existence'` (1) ·
`AssertionError: loremaster.{briefs,messages} must import reject_unknown_agents …` (2) ·
`AttributeError: <module 'loremaster.briefs'> has no attribute 'reject_unknown_agents'` from
`monkeypatch.setattr(raising=True)` (2). The module is imported at **CALL time** (`_shared_policy()`),
never at module scope — a module-level import would make the whole file UNCOLLECTABLE at clean HEAD,
deleting all 60 pins from the run rather than reddening 26 (finding #133; the same guard is in
`test_comms_schema.py`). The `AttributeError` is the mutation pin **failing closed**: a proof that
cannot find its mutation point must be a proof of nothing, loudly.

**Anti-vacuity, per group.** Every negative pin is paired with a positive control that is GREEN
today and must STAY green: `test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_edge` (×3),
`test_POSITIVE_CONTROL_a_REAL_endpoint_is_still_accepted_after_the_flip` (×3),
`test_POSITIVE_CONTROL_a_node_with_NO_edges_really_does_yield_an_empty_array`,
`test_POSITIVE_CONTROL_a_REGISTERED_agents_re_ack_is_still_already_acked`,
`test_POSITIVE_CONTROL_an_all_REGISTERED_recipient_list_is_delivered`,
`test_the_instrument_can_SEE_a_violation`, `test_the_ORDER_matters_not_merely_the_presence`. Three
pins additionally assert their fixture is big enough to discriminate before asserting anything
(`_relate_count(fragment) >= 4`, `len(nodes) >= 4`, `edges == {refers, answers_to}`).

**Negative fixtures use identities that genuinely do not exist, and PROVE it.** `_ghost_id()` mints
a fresh `uuid4` per call and `_record_exists()` is asserted false *before* every negative leg. An
all-registered fixture cannot discriminate a guarded table from an un-guarded one; this one cannot
accidentally become all-registered even if a sibling pin seeds a row.

**The C-DEF check (a contract must be 0-failed against a correct build).** I could not build the
reference implementation (writable set: tests only), so I did the next strongest thing — I read each
GREEN pin and asked whether the flip would break it. Two answers are load-bearing and are why §4.D1
exists: my **own** fixture applies `generate_agent_ddl()` first and registers a real agent, so the
seven GREEN ledger pins survive the flip; **`test_brief_ledger.py`'s does not**, and 29 of its
`[real]` ids do not. That asymmetry is the whole finding.

---

## 3. "What wrong build survives this contract?" — my own adversarial pass

Six plausible wrong builds. Four are killed; **two survive, and they are findings, not
embarrassments.**

1. **Flip only the three named edges, by hand, at each call site.** Passes the four per-edge pins.
   **KILLED** by the group-C mutation proof: deleting `enforced=True` from ONE
   `_define_relation_table` call must redden exactly that edge's declared pins, and running it for
   all four is what proves one emitter rather than four private copies. (Declared-RED ids are in the
   file's `MUTATION_PROOF` block, taken from `--collect-only`, written before any run.)
2. **Emit `ENFORCED` but keep `IF NOT EXISTS`** (or regress to it later). Every offline pin passes;
   every virgin-DB pin passes; production never migrates — #107 exactly.
   **KILLED** by `test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS` (offline) AND by
   `test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store` (behavioural, on a store that
   already carries the old definition).
3. **Ship `ENFORCED` and call the app-level check redundant.** The packet's Exit criterion reads as
   met — until a caller sees `statement N of M was rejected (unspecified rejection)`.
   **KILLED** by `test_an_UNREGISTERED_agent_id_is_REFUSED` (asserts the error is NOT a
   `SurrealStoreError`) + `test_the_refusal_NAMES_the_bad_agent_id` +
   `test_the_refusal_happens_BEFORE_the_version_is_minted`. The last is the discriminator between
   *refused early* and *rolled back late* — "no brief row afterwards" is true of BOTH (probe §10.2
   leg B), so a contract asserting only that would be a false gate.
4. **Clone `_reject_unknown_recipients`' body into `briefs.py`.** Every behavioural pin passes; the
   #102 shape is re-committed. **KILLED** by the two runtime mutation pins (replace the shared
   function → BOTH verbs must change) and by
   `test_BOTH_verbs_raise_the_SAME_error_type_for_an_unknown_agent`, which needs no name at all and
   so survives a rename of the pinned attribute.
5. **⚠ SURVIVOR — route through the shared function but hand-roll the DECISION underneath.**
   *Routing is not sharing.* A build that calls `reject_unknown_agents()` and then re-checks
   locally, or one whose shared function delegates back to per-caller predicates, passes the
   mutation pins (the sentinel still fires) and every behavioural pin. Only the *existence* query is
   proven shared, not the classification. I could not close this without a second, deeper mutation
   (change the shared function's SEMANTICS — e.g. make it accept everything — and demand both verbs
   accept), which needs the built function to exist. **Recommendation: the contract-adversary should
   add exactly that leg once the module lands**, or the builder should state in its report that the
   shared function is the sole decision point.
6. **⚠ SURVIVOR — satisfy §I by making `build_file_graph_fragment` emit NO `refers` edges at all
   when the inputs diverge.** `test_a_DIVERGENT_chunk_set_still_yields_a_self_consistent_fragment`
   guards against vacuity with `_relate_count(fragment) >= 1`, but a build that keeps the
   `answers_to` edges and silently drops every `refers` edge satisfies both assertions. Whether
   dropping is acceptable is a **design question I am not entitled to settle** — see §4.D2; the two
   candidate fixes (drop the edge vs mint the missing src node) have different data consequences and
   the packet is silent on which.

---

## 4. Decisions needed / escalations

### D1 — ⚠ BLOCKING. `test_brief_ledger.py` structurally contradicts the `briefed` flip

**Measured 2026-07-26.** `test_brief_ledger.py::brief_ledger_factory`'s `real` branch calls
`BriefLedger.ensure_ready()` and nothing else, and `ensure_ready` applies `generate_brief_ddl()`
alone. **The `agent` table is never created in that file.** Its constants (`AGENT_FIXER_B_ID` &c.)
name rows that do not exist, so **every `briefed` edge that suite writes today is a DANGLING edge.**

- **Derivation:** an AST pass attributing every `ack` / `_publish_as` / `_stored_via` / `_subscribe`
  / `publish(agent_id=…)` call to its enclosing test function found **36 edge-writing test
  functions**; intersecting with `pytest --collect-only -q` gives **29 collected `[real]` node ids**.
  The remaining 7 are **UNPARAMETRIZED** (they own private spy/query-count fixtures) and I did **not**
  classify their backends — so 29 is a **floor**, not a total.
- Its sibling `test_message_ledger.py` **already seeds real agent rows** (`_seed_agents`, which
  applies `generate_agent_ddl()` through the ledger's own `_query`) — precisely because `to` is
  already `ENFORCED`. `test_comms_wiring.py` registers through the real stack and is unaffected.
  `test_comms_tool.py`'s 10 `publish` sites are on `FakeBriefLedger` and are unaffected.
  **`test_brief_ledger.py` is the outlier.**
- **This is THE TEST ENVIRONMENT IS A FICTION, textbook:** a fixture that guarantees the one
  condition under which the bug is invisible. The whole brief-ledger contract runs in a world where
  agent existence cannot be violated because agents cannot exist.
- **Exact edit I would make (OUTSIDE my writable set — `test_brief_ledger.py` is packet C1's
  contract, not 04a's):** in `brief_ledger_factory`'s `real` branch, after
  `setup_connection = await connect_admin(env)` and before closing it, apply `generate_agent_ddl()`
  and `UPSERT` one `agent` row per id constant the file uses (the `_seed_agents` idiom, ~15 lines,
  one fixture — **not** 29 test edits). The `fake` branch needs nothing.
- **Ruling needed:** does the 04a wave own that edit? **My recommendation: yes, and it should be
  called out in the wave brief as a named deliverable** — a builder that discovers 29 reds mid-wave
  will be tempted to weaken the flip instead.

### D2 — ⚠ BLOCKING. P5's condition is NOT structural; the flip needs a fragment-builder fix

Probe §6.5 flagged `{edge.src} ⊆ {node.qualified_name}` and could not settle it. **I settled it, and
the answer is "conditionally".**

- **It HOLDS** for all **56** production modules under `loremaster/loremaster/` (offline derivation,
  0 violations) and for **8** deliberately adversarial source shapes (nested class, class-in-function,
  nested function, conditional class, `TYPE_CHECKING`-only class, try/except and `with`-scoped
  classes, async/lambda, property/dunder) — both with external references and with in-project ones
  forced through the keep/drop rule. The reason is real: astroid's `resolve_module` enumerates only
  top-level classes/functions, matching what the chunker chunks.
- **It is NOT structural.** `_derive_nodes` reads the **CHUNK SET the caller supplies**;
  `_derive_edges`' reference half **re-reads the FILE off disk** (`_resolve` calls
  `evict_resolved_file` to read it *deliberately fresh*). `Indexer.index_file(tier, path, source)`
  takes `source` from its caller, so **a save landing between the watcher's read and the derivation's
  read makes the two disagree.** MEASURED: with a divergent chunk set over a live source,
  `build_file_graph_fragment` emits `refers` RELATEs whose `src` `code_node` **no statement in the
  fragment ever creates** — e.g. `code_node:['custom','demo/svc.py','demo.svc.Service.boot']`.
- **Consequence of the flip:** today that is an invisible dangling edge. After it, the RELATE is
  rejected, aborting the transaction — and the graph slice rides the **same** `store.apply` as the
  chunk / `file_text` / manifest fragments (`Indexer._index_chunks`), so the file is isolated
  `failed` (last-good retained, one WARNING) and **its chunks never update**. Self-healing under a
  save-race; permanent for any deterministic divergence.
- **The contract pins the ∀, not the corpus.** `test_a_DIVERGENT_chunk_set_still_yields_a_self_
  consistent_fragment` demands *"never RELATE from an endpoint no earlier statement of the SAME
  fragment created"*, statement-ORDERED (probe §6.4 legs L5/L8: the check is at RELATE time,
  per-record, and order IS the contract). Pinning "our 56 modules are clean" would be the quantifier
  law violated — an invariant conditioned on the inputs that happened to be tested.
- **Ruling needed:** the fix belongs in `build_file_graph_fragment` — **mint the missing `src`
  `code_node`, or drop the edge**. They differ (minting preserves the reference; dropping loses it),
  and per probe §6.5 *"the fix is in the derivation or an added UPSERT for src nodes, not in
  weakening the flip."* **This widens 04a's implementation scope beyond a DDL flip.** My
  recommendation: mint the missing node (it is one statement, keeps the graph complete, and matches
  the fragment's existing "UPSERT every name first" order-independence design).

### D3 — `publish(agent_id: str | None)`: retain or retype? (I chose; both readings written down)

The ruling explicitly permits retyping. **Two readings produce different code:**
- **(1) RETAIN `agent_id: str | None`**, shared policy takes `(id, label)` pairs, error names the ID.
- **(2) RETYPE to `agent: AgentRefLike | None`** (id + name), shared policy is uniform with `send`'s,
  errors name real names. `AppContext._comms_brief_publish` already holds `agent_row`, and
  `_publish_as` exists *specifically* so the signature is stated in one place.

**I picked (1)** and the pins assert the bogus **id** appears in the message. Rationale: minimum
blast radius on `test_brief_ledger.py`, which I may not edit and which D1 already burdens; and the
id is the thing an operator must be given. **(2) is arguably the better design** — it makes the
shared policy signature-identical across both verbs with no adapter. If the operator prefers (2),
exactly one pin changes: `test_the_refusal_NAMES_the_bad_agent_id`.

### D4 — the shared policy's home and name (a DESIGN decision, escalated not assumed)

I pinned `loremaster/loremaster/agent_existence.py` exporting `reject_unknown_agents`, cloning the
**`loremaster.agent_ref` precedent verbatim**: that module exists because a ledger owning a shared
object forces its sibling to import IT, breaking `briefs.py`'s stated *"the ledger never imports its
neighbours"* law. A method on either ledger, or on `AgentRegistry` (which neither ledger holds), both
violate it. **The name is a mutation POINT** — a mutation proof needs one and a point has a name. It
fails closed and renaming costs one edit, in the contract. Flagged because per repo law duplication
*and* its resolution are design decisions, not coding ones.

### D5 — the flip makes `generate_brief_ddl` ORDER-DEPENDENT on `generate_agent_ddl`

`_message_statements`' docstring records that its slice is *"applied AFTER `generate_agent_ddl` in
every consumer"*. `generate_brief_ddl`'s does not — it never needed to. Production already orders
them correctly (`server.py`: `agent_registry` → `brief_ledger` → `message_ledger`), so this is a
property that HOLDS; `TestTheBriefSliceIsOrderDependentOnTheAgentSlice` pins it so a reordering is a
RED test rather than a silent 100% failure of `brief_publish`. **The builder should mirror the
`_message_statements` docstring note onto `generate_brief_ddl`** — served prose derived from
behaviour, per repo law.

### D6 — the un-enforcing door is a BOUND, and I pinned rather than closed it

Probe §3(a): `DEFINE TABLE OVERWRITE` omitting `ENFORCED` silently un-guards a table. It **cannot**
be closed — full-replace is the engine semantics and the very thing that makes the flip land. Per
*WHEN YOU CANNOT CLOSE A HOLE, PIN IT*, the contract does two things: the §A ∀-pin refuses an
un-enforced emission **at the source**, and `TestTheUnEnforcingDoor` demonstrates the mechanism live
(guard on → dangling refused → un-enforced re-emission raises nothing → same RELATE accepted) so
nobody rediscovers it from an outage. **Named re-open trigger:** the day the engine stops treating
the relation clause as full-replace, the live leg goes RED and says so.

### D7 — scout §S4's open gap, unchanged and now three edges wider

`test_surreal_store.py::test_the_whole_schema_migrates_an_existing_populated_store` applies four
slices and **not** `generate_message_ddl()`, so the blast-radius pin never covers the `to` slice.
After 04a it will also not cover the three newly-guarded edges' interaction with a fully populated
store. One line plus a seed row. **Operator/lead call whether 04a widens it** — I did not, because
that file is outside my writable set.

---

## 5. Removed-behaviour inventory (the ruling grants latitude, not exemption)

Each behaviour this contract's pins *change or delete*, adjudicated:

| # | behaviour at `28387a0` | adjudication |
|---|---|---|
| 1 | `publish(agent_id=<unknown>)` writes the brief AND a dangling ack edge (probe §10.2 leg A) | **dropped-deliberately** — the ruling pre-accepts it; a receipt for a non-existent agent is #105 itself |
| 2 | `ack(agent_id=<unknown>)` writes a dangling edge and reports `already_acked=False` | **dropped-deliberately** — same class; not previously stated anywhere, so it is NOTICED here rather than inherited |
| 3 | `_relate_briefed`'s `except SurrealStoreError` is the idempotent-re-ack SIGNAL | **preserved-with-pin** — `test_POSITIVE_CONTROL_a_REGISTERED_agents_re_ack_is_still_already_acked` (spec: packet §"⚠ `BriefLedger._relate_briefed` catches…" — *the pin is the ruling's own rider*) |
| 4 | first-write-wins `via` on a re-ack | **preserved-with-pin** — same test asserts `via == "publish"` survives a later `explicit` re-ack |
| 5 | `publish(agent_id=None)` is legal and writes no edge | **preserved-with-pin** — `test_agent_id_None_is_ACCEPTED_and_writes_no_edge`; ~50 call sites depend on it, and refusing it would be the quantifier law violated in the other direction |
| 6 | a rejected publish releases its minted version (`_release_version`, best-effort, swallows failures) | **preserved-but-BYPASSED on the new path** — an app check upstream never enters it. Pinned as `test_the_refusal_happens_BEFORE_the_version_is_minted`. The old path still exists for engine rejections (blank body, contention) |
| 7 | `send` raises `UnknownRecipientError` (a `MessageLedgerError` subclass) | **spec-silent → D3/D4.** The extraction changes the type both verbs raise. `test_BOTH_verbs_raise_the_SAME_error_type` pins *sameness*, not identity, so a builder may keep `UnknownRecipientError` as a subclass of the shared error. Flagged rather than decided |
| 8 | a `refers` edge from a purged/never-created `src` is written as a dangling edge | **old-bug, NOT re-pinned** — D2; under the flip it becomes an index failure, which is why the fragment must be made self-consistent |
| 9 | pre-existing dangling edges stay readable/traversable/deletable after the flip | **preserved-with-pin** — `test_the_PRE_EXISTING_dangling_edge_SURVIVES_the_flip` (probe §3 P2b). *Turning `ENFORCED` on does NOT close #236* |
| 10 | `to`'s already-shipped `ENFORCED` | **preserved-with-pin** — `test_the_edge_carries_ENFORCED_in_its_own_slice[to-…]`, a regression pin and the positive control proving that assertion can pass at all |

---

## 6. WHAT I COULD NOT DETERMINE

An empty list would itself be a claim. This one is not empty.

1. **Whether the contract is 0-failed against a correct build (the C-DEF receipt).** I could not
   build the reference implementation — writable set is tests only. I read every GREEN pin and
   reasoned about the flip's effect on it (§2), and the reasoning *produced* D1, so it is not
   vacuous — but **it is reasoning, not a run.** The contract-adversary must build the fix and grade
   exactly this.
2. **Whether wrong-build #5 (routing without sharing the DECISION) is closable.** §3.5. Needs a
   semantic mutation of a function that does not exist yet.
3. **Whether `DEFINE TABLE … IN agent … ENFORCED` even APPLIES when the `agent` table is absent.**
   Not probed (brief: do not connect a store for facts the probe settled — and this one it did not
   settle). `TestTheBriefSliceIsOrderDependentOnTheAgentSlice` asserts only the *consequence* (a
   RELATE to a non-existent agent is refused), which holds either way: if the table does not exist,
   neither does the record. **The DDL-application half is unmeasured.**
4. **The backends of the 7 unparametrized edge-writing tests in `test_brief_ledger.py`** (D1). 29 is
   a floor.
5. **Whether the save-race in D2 has ever actually fired in production.** I proved the divergence is
   *reachable and deterministic given divergent inputs*; I did not measure how often the watcher's
   read and the derivation's read disagree, and I did not sweep for `failed` manifest rows.
6. **The cost of `ENFORCED` on 3.2.1.** Probe §9 explicitly leaves it unmeasured (§4's "~2.8% at
   16-way" is a 3.1.5 number). Three more guarded edges, one of which (`refers`/`answers_to`) is on
   the hot indexing path. No pin here measures it, and I am not asserting it is free.
7. **`ENFORCED` under CONTENTION** — probe §9's own residual; every P5 leg was single-writer. The
   `briefed` edge has a documented 8-way concurrent-publisher pin in `test_brief_ledger.py`
   (`test_every_one_of_eight_concurrent_publishers_self_acks_exactly_its_own_version`) which is one
   of D1's 29. After the fixture fix it becomes the natural place to observe this — I did not add a
   contention pin of my own, because a contention pin needs 20 consecutive green runs to mean
   anything and that is a builder/audit instrument, not a contract one.
8. **Whether packet 04b's `blocks` edge is fully covered by the §A ∀-pin.** It pins `ENFORCED` from
   birth (and `test_the_relation_edge_set_is_EXACTLY_the_four_known_edges` forces a deliberate
   declaration), but the `blocks`-specific hazards — deterministic edge ids becoming a hard error on
   SurrealDB 4.0 (probe §4/#349), the `+collect` closure correction (probe §5.1) — are 04b's and
   nothing here covers them.

---

*Contract file: `loremaster/tests/test_enforced_relations.py`. Gates at `28387a0`, 2026-07-26:
`26 failed, 34 passed in 5.41s` (contract alone) · `26 failed, 481 passed in 19.01s` (with
`test_brief_ledger.py` + `test_comms_schema.py` + `test_surreal_schema.py`) · `ruff check` clean ·
`scripts/typecheck.sh` clean. No production module was modified. Live legs: spike-surreal
`ws://127.0.0.1:18000` only.*

⚠ **The paragraph above and §1–§6 describe the contract BEFORE the 04a/43 split. They are
preserved verbatim (they are cited from the INDEX Log and the packet file); §SPLIT below
supersedes §1's group map and the counts.**

---

# SPLIT — packets 04a / 43, 2026-07-26

*Everything in this section was measured **2026-07-26** against `feat/surreal-unification` @
`28387a0`, after the lead's ruling on D1/D2. Live legs: spike-surreal `ws://127.0.0.1:18000` only.*

## S0. What the ruling changed, and the one thing it forced me to redesign

**D1 accepted** (04a owns the `test_brief_ledger.py` agent-seeding fix). **D2 ruled to the ROOT
fix** — `_derive_edges` stops re-reading; both derivations read ONE source — which is now packet 43
(`docs/plans/v2/43-derivation-source-unification.md`, `a075e85`), a DESIGN pass before it is a build.

Splitting the file was mechanical except for **one pin that could not simply move or stay**: the ∀
law, `test_EVERY_relation_table_the_schema_emits_is_ENFORCED`. Narrowing it to the edges 04a flips
would have turned the law back into the name list repo law forbids — and **packet 04b's `blocks`
edge could then arrive un-guarded with every gate green.** Moving it wholesale to packet 43 would
have left 04a with no ∀ at all, for however long 43's design pass runs.

So the ∀ is kept **TOTAL over the emitter's output** and takes exactly one deny-by-default
exemption: `_enforced_relations_scaffold.DEFERRED_TO_PACKET_43`, a small, enumerated, **asserted**
safe-set (*allowlist the safe*). Anything not in that set must be `ENFORCED`, today and forever.
Packet 43's contract pins its exact contents, refuses its growth, and empties it as its entry
condition. Three pins hold that shape together:

| pin | file | state | what it forbids |
|---|---|---|---|
| `test_EVERY_relation_table_the_schema_emits_is_ENFORCED` | 04a | **RED** | an un-guarded edge that is not exempt — incl. 04b's `blocks` |
| `test_the_deferred_set_names_EXACTLY_the_two_code_graph_edges` | 43 | GREEN | the exemption set QUIETLY GROWING (the "fix" a builder reaches for when the ∀ reddens) |
| `test_the_deferred_set_is_EMPTY` | 43 | *skipped* | packet 43 shipping without closing the hole |

## S1. The 04a group map (supersedes §1)

`loremaster/tests/test_enforced_relations.py` — **38 pins**. RED/GREEN at `28387a0`.

| group | class | pins | RED | GREEN |
|---|---|---|---|---|
| **A** the flip (`briefed` + the `to` regression + the ∀) | `TestEveryRelationEdgeIsEnforced` | 12 | 2 | 10 |
| **B** dirty-store migration | `TestTheOldWorldDerivationIsNotVacuous` + `TestTheEnforcedFlipMigratesADirtyStore` | 6 | 2 | 4 |
| **C** un-enforcing door | `TestTheUnEnforcingDoor` | 1 | 1 | 0 |
| **D** ghost-member reading | `TestADanglingEdgeReadsAsAFirstClassMember` | 2 | 0 | 2 |
| **E** ONE IMPLEMENTATION | `TestTheUnknownAgentPolicyHasONEHome` | 5 | 5 | 0 |
| **F/H** publish's contract | `TestPublishRefusesAnUnregisteredAgent` + `TestPublishWithARegisteredAgentStillWorks` | 6 | 4 | 2 |
| **G** shared-catch hazard | `TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent` | 2 | 1 | 1 |
| **F(3)** send | `TestSendRefusesBeforeTheWrite` | 3 | 1 | 2 |
| — DDL slice ordering (not briefed) | `TestTheBriefSliceIsOrderDependentOnTheAgentSlice` | 1 | 1 | 0 |

`loremaster/tests/test_derivation_source_unification.py` — **26 pins** (22 moved + 4 new).

| group | pins | skipped | running |
|---|---|---|---|
| entry condition (`DEFERRED_TO_PACKET_43`) — **all 4 new** | 4 | 2 | 2 |
| `refers`/`answers_to` DDL pins | 3 | 3 | 0 |
| `refers`/`answers_to` dirty-store + old-world + un-enforcing | 13 | 13 | 0 |
| the ∀-over-the-fragment pin and its controls (old §I) | 6 | 1 | 5 |

**Arithmetic, so no count here is un-derived:** 60 pins before → 38 stay + 22 move; 22 + 4 new = 26.
38 + 26 = **64 collected** (`pytest --collect-only -q`, both files). Of the 22 moved, **9 were RED
and 13 GREEN** before the split.

## S2. Counts, with the passed-COUNT tails

```
loremaster/tests/test_enforced_relations.py              -n auto -q  ->  17 failed, 21 passed in 5.05s
loremaster/tests/test_derivation_source_unification.py   -n auto -q  ->   7 passed, 19 skipped in 4.69s
both + test_brief_ledger + test_comms_schema
     + test_surreal_schema + test_graph + test_graph_surreal          -> 17 failed, 611 passed, 19 skipped in 23.59s
uv run ruff check .                                                   -> All checks passed!
./scripts/typecheck.sh                          -> loremaster OK / lorescribe OK / loresigil OK (155 files)
```

Every one of the 17 failures is in `test_enforced_relations.py`, by design. **`test_graph.py` and
`test_graph_surreal.py` were added to the neighbour set for this run specifically because packet
43's file now imports the derivation seam** — they are green.

## S3. Is every remaining 04a pin RED today for the RIGHT reason? — yes, and here is the check

Failure reasons, tallied from `--tb=line` over the 17 (not one is a collection error, a `TypeError`,
or a pre-existing pin this contract contradicts):

| n | reason | verdict |
|---|---|---|
| 9 | `Failed: DID NOT RAISE <class 'Exception'>` | the live guard/refusal pins — **the code runs and does the wrong thing**, the only red that proves a behavioural contract |
| 2 | `AttributeError: <module 'loremaster.{briefs,messages}'> has no attribute 'reject_unknown_agents'` | the mutation pins **failing closed** — a proof that cannot find its mutation point must fail loudly |
| 2 | `AssertionError: loremaster.{briefs,messages} must import reject_unknown_agents …` | the fail-closed precondition, stated as its own assertion |
| 1 | `ModuleNotFoundError: No module named 'loremaster.agent_existence'` | the intended contract-first absence, at CALL time so the file reddens rather than going uncollectable (#133) |
| 1 | `AssertionError: … Un-guarded and NOT exempt: {'briefed': …}. The ONLY legal exemption is DEFERRED_TO_PACKET_43 (['answers_to', 'refers']) …` | **the ∀ law, correctly re-scoped** |
| 1 | `AssertionError: briefed must be declared ENFORCED: …` | the per-edge slice pin |
| 1 | `AssertionError: re-emitting 'briefed' with enforced=False does not change the DDL …` | the anti-vacuity guard on the old-world derivation |

### The question you actually asked: **did any pin go GREEN for a SCOPING reason?**

**No. Zero pins flipped RED → GREEN across the split.** Derived, not asserted: 26 RED before; 9 RED
moved out; 17 RED remain — `26 − 9 = 17`, exactly the observed count. If any surviving pin had gone
green for a scoping reason the arithmetic would not close, and it does.

**One pin was one edit away from being exactly that failure, and it is worth naming.** Had I
narrowed the ∀ to `{briefed}`, it would still be RED *today* — indistinguishable, at this commit,
from the version I shipped. It would have gone GREEN the moment 04a landed, while `refers`,
`answers_to` **and any future edge** sat un-guarded, and packet 04b's `blocks` could have shipped
without the clause with every gate green. *A pin that is red today for the right reason can still be
the wrong pin*; the deferred-set design is what keeps the ∀ honest through the split, and
packet 43's `test_the_deferred_set_names_EXACTLY_the_two_code_graph_edges` (running, not skipped) is
what stops the exemption becoming the escape hatch.

## S4. The mutation proof, re-scoped — and labelled as a PREDICTION

**(a) It now declares exactly the edges 04a flips: one.** `FLIPPED_BY_04A` is a single-entry tuple
and the `--expect-red` list names six pins, all `briefed`-keyed. A proof still declaring four edges
would produce **declared reds that stay GREEN** — the direction the both-ways diff exists to catch
and the direction that reads as success. `refers`/`answers_to` get their own proof in packet 43's
file.

**(b) The ids came from `pytest --collect-only -q`, never from a watched run.** Node ids were read
off the collection listing and the parametrised suffixes (`[briefed-generate_brief_ddl]`,
`[briefed]`) copied from it, not typed from source.

**⚠ And the bound, stated because an instrument that hides its own bound is how "unproven" becomes
"proven":** this set **cannot be executed yet**. The mutation is *deleting* `enforced=True`, which is
a no-op on a tree that never added it — `mutation_proof.py`'s exactly-once anchor match would fail
outright. So the set is a **prediction**, derived from which pins depend on the clause. It is written
into the file *before* any run, which is the process working; the both-ways diff is what will grade
it when the flip lands. **Do not reconcile a mismatch by editing the list to match the output** —
that is the tautology this whole mechanism exists to prevent.

One prediction is load-bearing and deliberate: **the app-check pins (E/F/G/H) are NOT in the set.**
They depend on the app-level layer, not the engine clause. A build that reddened them under this
mutation would have coupled two layers the contract requires to stay independent — so if the proof
reports them as unexpected reds, that is a finding, not a bad prediction.

## S5. Deviations from the split brief — two, both disclosed rather than chosen silently

**(1) A third file: `loremaster/tests/_enforced_relations_scaffold.py`.** The brief's writable set
was "same as before, plus the new test file". Splitting the pins meant both files needed the same
migration idiom — DDL application, the old-world derivation, the live-store helpers, the edge
vocabulary. Copying it would have been **copy #2 of a POLICY** (what counts as a genuinely-absent
endpoint, how DDL is applied, how an old world is derived), which repo law #102 forbids and which
makes two migration pins silently diverge. Repo law also says the *non*-duplicating choice needs no
escalation while duplication does — so I wrote the shared module and am flagging it here. Precedent:
`_surreal_harness` (which exports the `admin_db` fixture the same way), `_comms_fakes`,
`_task_fakes`, `render_injection_scaffold`. It asserts nothing; every pin lives in a contract file.

**(2) 17 of the 22 moved pins are skipped, not 22.** The brief said *every* moved pin. The five that
RUN are the `§I` controls — `test_a_realistic_multi_chunk_file_is_self_consistent`,
`test_BOTH_edge_kinds_are_present_in_the_fixture`, `test_the_instrument_can_SEE_a_violation`,
`test_the_ORDER_matters_not_merely_the_presence`, and
`TestTheDerivationsAgreeOnSourceNames::test_every_edge_src_is_a_derived_node_for_a_matching_chunk_set`.
They are GREEN today, GREEN after packet 43, and **cannot ever be permanently RED** — so the stated
reason for skipping ("a permanently RED one is a broken gate") does not reach them. Four of the five
exercise `_unsatisfied_relate_endpoints`, the helper the headline ∀ pin depends on: skipping them
leaves that helper un-run for the whole of packet 43's design pass, and *a guard nobody runs is a
hope with a filename* — a rotted helper would produce a false green the day everything is unskipped.
**If you want the file wholly inert, it is a five-line change and I will make it.**

Everything else follows the brief: one skip reason constant, `SKIP_REASON`, naming both `packet 43`
and the finding, so `grep "packet 43"` over the test tree finds every deferred pin in one pass and
no variant spelling can hide one.

## S6. What I did NOT do

**The D1 fixture edit is not in this change.** Your ruling put it in 04a's scope and your task
statement said *"ONE TASK: split"*, so I did the split. The edit is unchanged from §4.D1: in
`test_brief_ledger.py::brief_ledger_factory`'s `real` branch, apply `generate_agent_ddl()` and
`UPSERT` one `agent` row per id constant the file uses, before closing the setup connection —
~15 lines, one fixture, no test edits; the `fake` branch needs nothing. **Say the word and I will
make it**; it is harmless today (the seeded rows change nothing until the flip) and it removes the
29-red surprise from the builder's path.

Two items from §6 are *narrowed* by the split and one is *unchanged*, so nobody inherits them wrongly:

- **§6.1 (no C-DEF receipt)** — still open, but now over a smaller surface: 38 pins, one flipped
  edge. The contract-adversary must still build the reference implementation and grade it.
- **§6.8 (does the ∀ cover 04b's `blocks`?)** — **now answered for the guard itself**: yes, via the
  deferred-set design, and a `blocks` edge emitted un-guarded reddens 04a's ∀ pin. The
  `blocks`-specific hazards (deterministic edge ids → a hard error on SurrealDB 4.0, probe §4/#349;
  the `+collect` closure correction, probe §5.1) remain 04b's and are covered by nothing here.
- **§6.5 (has the D2 save-race ever fired in production?)** — unchanged and unmeasured. Packet 43's
  design pass is the natural place to settle it; a sweep for `failed` manifest rows would answer it
  cheaply.

---

# S7 — the D1 fixture edit (`test_brief_ledger.py` agent seeding)

*Measured **2026-07-26** against `feat/surreal-unification` @ `a8516b4`. Live legs: spike-surreal
`ws://127.0.0.1:18000` only. No production module touched.*

## S7.1 Counts — and the one that moved

```
BEFORE  test_brief_ledger.py -n auto -q  ->  120 passed in 5.79s
BEFORE  test_brief_ledger.py         -q  ->  120 passed in 12.53s   (second, independent reading)
AFTER   test_brief_ledger.py -n auto -q  ->  122 passed in 6.97s
```

**The count moved, +2, and it is fully accounted for.** Rather than assert that, I derived it: I
restored the pre-edit file from `git show HEAD:` into a scratch tree and diffed the two
`--collect-only -q` node-id listings.

```
before ids: 120   after ids: 122
ONLY IN AFTER (added):
  TestEveryRealLedgerSiteSeedsItsAgentRows::test_every_function_that_builds_a_real_BriefLedger_also_seeds_agent_rows
  TestEveryRealLedgerSiteSeedsItsAgentRows::test_the_seeded_id_set_covers_every_module_level_agent_id_constant
ONLY IN BEFORE (removed):   <none>
```

**Zero pre-existing node ids were added, removed, renamed or re-parametrised, and all 120 still
pass.** The delta is exactly the two pins I added (S7.3). So: *no pre-existing test changed status* —
which is the property you actually asked about — and the seeded rows are inert today, as predicted
(an un-enforced edge does not care whether its endpoint exists).

Wider gates after the edit:

```
test_enforced_relations.py             -> 17 failed, 21 passed          (unchanged by this edit)
test_derivation_source_unification.py  ->  7 passed, 19 skipped         (unchanged)
+ comms_schema, comms_tool, comms_wiring, message_ledger, surreal_schema
                                       -> 17 failed, 1595 passed, 33 skipped in 29.10s
uv run ruff check .                    -> All checks passed!
./scripts/typecheck.sh                 -> loremaster OK (155 files) / lorescribe OK / loresigil OK
```

## S7.2 ⚠ THE FINDING: the fixture alone was NOT sufficient — there are FIVE seeding sites

**This is what requirement #2 bought, and it is why "derive, don't type" was the right instruction.**
My §4.D1 spec said *"~15 lines, one fixture, no test edits"*. That was **wrong**, and an AST
derivation of every agent-id expression in the file found out why in one pass:

| expression | where | covered by the factory? |
|---|---|---|
| `AGENT_FIXER_B_ID`, `AGENT_SCOUT_C_ID`, `AGENT_AUDIT_D_ID` | module constants | yes |
| `f"agent-{index}-opaque-id"` × 8 | `test_every_one_of_eight_concurrent_publishers_self_acks…` | yes (uses the factory) |
| `_AgentRef(f"agent-{index:03d}-id", …)` × N | `TestCoverageQueryCountIsBounded._coverage_query_count` | **NO — builds its own ledger on its own env** |
| `f"agent-{index:03d}-id"` × N | `TestAckedVersionsForIdsQueryCountIsBounded._query_count` | **NO — same** |
| `AGENT_FIXER_B_ID` via `_publish_as` | `TestPublishSelfAckIsWrittenInTheSameTransaction._real_ledger` | **NO — same** |
| `AGENT_FIXER_B_ID` via `_subscribe` | `TestSubscribedNameSkewQueryPlans::test_acked_by_id_fetch_…` | **NO — same** |

**Six functions in this file construct a real `BriefLedger`; only one of them is the factory.** A
seeded factory plus five unseeded helpers is precisely the "a fix reached one copy and not the
other" shape — and it maps exactly onto the 7 unparametrized edge-writing functions §4.D1 flagged as
*"I did not classify their backends"*. They are now classified: four of them build real ledgers.

**So the seeding is ONE FUNCTION with SIX call sites, never a pattern cloned six times** (repo law
#102). `_seed_agent_rows(env, agent_ids)` applies `generate_agent_ddl()` — the **production
emitter**, per requirement #1, never a hand-written `DEFINE TABLE agent`, for the same reason the
04a migration pins derive their old-world DDL from `_define_relation_table` rather than a literal —
then `UPSERT`s one row per id with `CONTENT` (`session` is a SurrealDB PROTECTED variable name,
store reference §2) and `UPSERT` rather than `CREATE` so double-seeding is safe.

**The two N-parameterised helpers seed FROM the ids they already build** (`[ref.id for ref in
roster]`, `agent_ids`), never from a re-listed copy — so their seed set and their ack set cannot
drift.

## S7.3 Requirement #2, answered by an instrument rather than a promise

You asked me to derive the constants and not leave a mystery if one is added later. A derivation I
perform once is still a list I typed, so I made **coverage a CHECKED VARIABLE** (repo CLAUDE.md:
*enumerate every call site, assert each was observed*). Two new pins, and they are the +2 above:

1. **`test_every_function_that_builds_a_real_BriefLedger_also_seeds_agent_rows`** — AST-sweeps this
   file for every function that CALLS both `BriefLedger` and `make_env`, and asserts each also CALLS
   `_seed_agent_rows`. A seventh site written months from now reddens here, with a message naming
   the function and the exact call to add — rather than reddening mysteriously the day `briefed` is
   `ENFORCED`.
2. **`test_the_seeded_id_set_covers_every_module_level_agent_id_constant`** — reads the module's own
   namespace for `AGENT_*_ID` constants and asserts each is in `_SEEDED_AGENT_IDS`. A new constant
   that nobody seeds reddens immediately.

**⚠ The first version of pin 1 was a substring sweep, and it matched ITSELF** — its assertion message
mentions `BriefLedger(` and `make_env(`, so the gate counted itself as a covered site, and worse, a
future author could have satisfied it by *mentioning* `_seed_agent_rows` in a comment. That is the
non-discrimination it exists to hunt in others, committed by the instrument. Rewritten to AST
`Call`-node detection on both sides, with the gate's own class excluded by name. Caught by printing
what the sweep saw instead of trusting that it saw the right things.

The sweep also carries a floor (`len(builders) >= 5`): **a shrunken sweep reads exactly like full
coverage**, so a sweep that silently stopped finding sites must fail rather than pass.

## S7.4 The gate is mutation-proven, and the first attempt was a live #194

**Control:** removed one `_seed_agent_rows` call from `_real_ledger`, ran the gate, restored.

```
MUTATION LANDED (anchor matched exactly once)
E   AssertionError: these functions build a REAL BriefLedger on a fresh database but never CALL
    _seed_agent_rows: ['TestPublishSelfAckIsWrittenInTheSameTransaction._real_ledger']. …
1 failed, 121 deselected in 0.23s
RESTORED byte-exact          (cmp against a cp -a content backup)
```

**⚠ My first attempt at this control was finding #194, live, in the session that has been writing
about #194 all packet.** The anchor I chose matched **twice**, so the mutation never landed — and the
next command in the same shell block ran anyway and printed `1 passed`, which reads exactly like a
successful control. What caught it was not the rule; it was a **checked expectation**: I had asserted
`count == 1` inside the mutating step, and the assertion fired. The `1 passed` beneath it was still
printed and still meaningless.

The re-run used a unique anchor, asserted exactly-once matching *before* writing, and echoed the
mutation step's exit code. **Ask of any multi-step verification: "if step N silently no-opped, would
step N+1 still print something that reads as success?"** — here it did, in the direction of false
confidence, which is always the direction.

## S7.5 Deviations and what remains

- **Deviation: this is more than "one fixture, no test edits".** Six call sites + one shared seeder +
  two coverage pins + five imports, because the derivation you asked for proved the one-fixture spec
  insufficient. No existing test body was altered — the node-id diff in S7.1 is the receipt.
- **Not verified, and it cannot be yet:** that these seeded rows actually satisfy `ENFORCED`. The
  flip has not landed, so today they are inert. The claim "≥29 reds become 0" is a **prediction**
  until the contract-adversary's reference build exists. What *is* verified is that the rows are
  real (`generate_agent_ddl()` applied, `UPSERT`ed via the same `CONTENT` shape
  `test_message_ledger.py::_seed_agents` uses against the already-`ENFORCED` `to` edge) and that
  nothing regressed today.
- **§4.D1's "≥29" floor is now retired as a floor:** the 7 unclassified unparametrized functions are
  classified (S7.2). I did not re-derive the total that will redden without the seeding, because the
  seeding now exists and the number is no longer actionable.
- **The `fake` branch was left alone**, as specified: `FakeBriefLedger` is an independent in-memory
  implementation with no `agent` table and no endpoint validation to satisfy.
