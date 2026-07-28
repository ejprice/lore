# REPORT-reader-04a-inherit — what packet 04b inherits from packet 04a

brief-base v7 read

*Read-only run, **2026-07-27**, on `feat/surreal-unification` @ `c4da1c3`. I read REPORTS, not code:
every claim below is attributed to an archived report + section. **I ran no test, no probe, no store
connection, and read no production source** — where a report's claim is unverified or contradicted by
a sibling report, I say so rather than resolving it by reading the tree. The one derivation I made
myself is a `diff` between two archived report FILES (§Q6-O1), method disclosed there.*

**Source set** (all under `docs/plans/v2/receipts/2026-07-27-packet04a/`, cited below as
`receipts/…`): `REPORT-builder-04a.md` · `REPORT-adversary-04a.md` ·
`REPORT-contract-04a-enforced.md` · `REPORT-contract-04a-enforced-2.md` ·
`REPORT-contract-04a-enforced-3.md` · `REPORT-fixwave-04a.md` · `REPORT-scout-pkt04-seams.md`.
**Deliberately NOT re-reported** (lead has them): `REPORT-coldaudit-04a.md` summary + RESIDUALS,
`REPORT-probe-pkt04-store.md` §5/§8/§9. `REPORT-investigate-hardkill-reaper.md` was outside my brief
and is UNREAD by me — if 04b touches the reaper, nobody has triaged it for 04b.

---

## SUMMARY BLOCK

- **state:** done. Six answers below, each cited. **Packages considered:** none — no mechanism
  specified or built; this is a read-and-extract task.
- **Q1** — `loremaster/loremaster/agent_existence.py` exports `UnknownAgentRowError` (shared base) +
  `async reject_unknown_agents(query, agents, *, error=…)` + `format_unknown_agent_refusal(mapping)->str`.
  5 callers (3 prod, 2 fakes). A new caller passes an `AgentRef`-shaped identity + its OWN
  `error=` subclass and **decides nothing underneath**; it must add an MP-2 leg. §Q1.
- **Q2 — ⚠ THE BRIEF'S PREMISE IS WRONG:** there is **no** mutation proof pinning all four edges.
  04a deliberately re-scoped it to the ONE edge it flips (`FLIPPED_BY_04A`, single entry); executed
  once, `8 failed, 42 passed`, EXIT=0. §Q2.
- **Q2b — the name enumeration exists and it fails CLOSED**: `test_the_relation_edge_set_is_EXACTLY_the_four_known_edges`
  + `KNOWN_RELATION_EDGES`. A fifth edge reddens it → deliberate declaration. The ∀ pin is
  emitter-text-parsed, not a name list. The real escape hatch is `DEFERRED_TO_PACKET_43`, guarded
  **only in `test_derivation_source_unification.py`** — 04b's wave gate MUST run that file. §Q2.
- **Q3** — W-A (migration never lands) · W-B (policy keyed on one fixture literal) · W-D (check after
  the write, greener than correct) · W-E (routing≠sharing). **All four recur in 04b**; W-D maps onto
  `create_task`'s non-atomic `_query` seam, W-E onto the `_comms_footer`, W-B onto both served
  counts. §Q3.
- **Q4** — five fixture axes recorded: id SHAPE (R-2, KNOWN) · single-literal identity · `_BRIEF_NAME`
  value monoculture · `via=` closed-set monoculture · small-N `len()`≡`sum()`. Plus S2's
  `len(pending) <= limit` window/whole-set trap, which is aimed straight at 04b's fleet columns. §Q4.
- **Q5** — `publish`'s SIGNATURE did not change (bare `str` kept, deliberately); its BEHAVIOUR did
  (refuse before mint). The transferable method for 04b's dispatcher collapse is fixwave's four-part
  "runtime behaviour unchanged" receipt + the adversary's P6b **independent** enumeration. §Q5.
- **Q6** — 17 open obligations listed individually. Highest-value NEW one: the store reference's own
  §8 `#105` bullet still teaches the claim 04a proved false, and it is the file every store/DDL brief
  reads FIRST — i.e. 04b's `blocks` brief. §Q6-F1.

---

## Q1 — THE SHARED POLICY 04b MUST REUSE

### Q1.1 Public symbols, as reported

Module: `loremaster/loremaster/agent_existence.py` (new in 04a; builder §1 file table).

| symbol | what the reports state | citation |
|---|---|---|
| `UnknownAgentRowError` | the SHARED BASE exception. Named `…RowError`, **never** `UnknownAgentError` — that name is already taken by `loremaster.agents.UnknownAgentError` meaning *"this display NAME resolves to no agent at the REGISTRY"*; the new one means *"this row ID names no `agent` row at the LEDGER"* | builder §3.5; the collision was escalated as D-a in `receipts/…/REPORT-contract-04a-enforced-3.md` §7 |
| `async reject_unknown_agents(query, agents, *, error=…)` | ONE direct-record-access read (`SELECT id FROM $agent_ids`), names every missing `name (id)`. Imports neither ledger | builder §1 table, §3.4 |
| `format_unknown_agent_refusal(unknown_name_by_id: Mapping[str, str]) -> str` | added by the fix wave. Owns BOTH halves of the served surface — the `name (id)` identity rendering AND the sentence — *"because handing the fakes only the joined string would have left them cloning the rendering"* | fixwave §F3 |

**⚠ What no report states, and 04b must not guess:** the *annotated* signature of
`reject_unknown_agents` (parameter types, return type, and the `error=` default) is **not quoted
verbatim anywhere in the seven reports**. The nearest is `receipts/…/REPORT-contract-04a-enforced-3.md`
§4, which gives `async reject_unknown_agents(query, agents, *, error=UnknownAgentError)` — **but that
is the ADVERSARY-GRADING REFERENCE BUILD in a scratch tree, not the shipped module** (that build
predates the D-a rename ruling, so its default names a class the shipped tree does not use for this
purpose). Treat the shipped default as UNKNOWN-from-reports; read the module.

**Raises:** the class passed as `error=`. Both ledgers subclass the shared base so a caller can catch
either vocabulary with one `except` (builder §3.5):

- `UnknownBriefAgentError(BriefLedgerError, UnknownAgentRowError)`
- `UnknownRecipientError(MessageLedgerError, UnknownAgentRowError)`

This shape is a **LEAD RULING**, not a builder choice: the adversary measured all three readings of
the error-type fork and every one cost something (`receipts/…/REPORT-adversary-04a.md` §C-DEF-3);
RULING 1 picked *shared base + distinct subclasses*, and the pin was re-shaped and **renamed** from
`test_BOTH_verbs_raise_the_SAME_error_type_for_an_unknown_agent` to
`test_BOTH_verbs_raise_an_error_a_caller_can_catch_with_ONE_except`, asserting the two raised values
share a base whose `__module__` is the shared policy module — *"it needs no new name-keyed handle —
the base is derived from the raised VALUES"* (`…-enforced-3.md` §1).

### Q1.2 Every current caller

**Production (3):**
1. `BriefLedger.publish` — calls the policy **before `_mint_version`** (builder §1, §3.4).
2. `BriefLedger.ack` — calls it **before the versions read** (builder §1).
3. `MessageLedger._reject_unknown_recipients` — its body is now **one delegating call**; it survives
   only to own the ledger's *vocabulary* (`error=UnknownRecipientError`), *"the choice of which
   exception a caller catches, never which ids are unknown"* (builder §3.4). Its own caller is
   `MessageLedger.send`.

**Test doubles (2) — these call the FORMATTER, not the policy** (fixwave §F3):
4. `_message_fakes.FakeMessageLedger.send` — imports `format_unknown_agent_refusal` at MODULE scope
   (safe there: that file already imports `loremaster.messages`, which imports `agent_existence`).
5. `_comms_fakes.FakeBriefLedger._reject_unknown_agent` — via `_shared_unknown_agent_message()`,
   which **keeps that file's call-time-import idiom (finding #133)** and **fails closed** via
   `getattr` with no default, exactly like its sibling `_shared_unknown_agent_error()`.

⚠ **The fake fleet is not symmetric with production and 04b must not assume it is.** `FakeBriefLedger`
enforces the policy only when its agent table is MODELLED (non-empty); an empty table accepts
everything. That is a **DECLARED BOUND with a pinned re-open trigger** — `…-enforced-3.md` §7 D-c —
because closing it would cost a `register_agent` call at ~55 tool-seam sites in `test_comms_tool.py`
**plus 3 in `test_comms_render_architecture.py`, which was outside 04a's writable set.**

### Q1.3 What a NEW caller must do to REUSE rather than clone

Derived from the reports' own receipts; each line has the receipt that makes it non-optional.

1. **Pass identities, not bare ids.** 04a added `AgentRef` to `loremaster/loremaster/agent_ref.py` —
   a frozen 2-field concrete `AgentRefLike` — explicitly *"so the brief ledger reaches the shared
   policy through the SAME door `send` does instead of the policy growing a second, id-only entry
   point"* (builder §1). A `blocks` endpoint check or a sender check adds **no third door**.
2. **Pass your own `error=` subclass of `UnknownAgentRowError`.** The ledger owns vocabulary; the
   policy owns the decision (builder §3.4).
3. **Decide NOTHING underneath.** W-E is the measured wrong build that calls the shared function and
   re-checks locally: it survived 38/38 **and every neighbour suite** (`…-adversary-04a.md` §P1 W-E).
4. **Do not hand-roll the id derivation.** The policy matches the engine's echo against its own
   `str(RecordID(AGENT_TABLE, id))` renderings, *"symmetric by construction"*; a hand-rolled
   `str(row["id"]).split(":", 1)[-1]` is right for `agent:abc` and **wrong** for a uuid-shaped id
   (`agent:⟨0199c4f1-…⟩`) and cost the reference-build author **130 red pins** across
   `test_message_ledger.py` + `test_brief_ledger.py` (builder §3.2; `…-enforced-3.md` §7 D-d.1).
   ⚠ Also measured: **`RecordID` is UNHASHABLE on SDK 2.0.0** (`__hash__ is None`) — never put one in
   a set or use it as a dict key (builder §3.2, §7 E-4).
5. **Any refusal it serves must carry BOTH the NAME and the ID** — one pin demands the id, another
   the name, and `f"{name} ({id})"` is the single string that satisfies both (`…-enforced-3.md` §7
   D-d.2; builder §3.3).
6. **If the new caller's path runs against a deny-by-default fake connection, that fake must be
   widened SHAPE-keyed, never text-keyed.** 04a hit exactly this: adding the check to `ack` broke 5
   pins in `test_retry_seam.py` because `_AckConnection` is a closed-set fake (`…-adversary-04a.md`
   §C-DEF-2, originally BLOCKING). The widening that closed it keys on *"a `SELECT` whose PARAMS bind
   `agent`-table `RecordID`s"*, and **branch ORDER is load-bearing and commented** —
   `_select_briefed_edge`'s SELECT also binds an agent RecordID, so its branch must be tried first
   (`…-enforced-3.md` §3).
7. **Note the dead branch.** The policy's empty-input early-return is **unreachable through both
   current entry points** (`publish` passes exactly one; `send` raises `EmptyRecipientSetError`
   first) — *"A builder will write it; no pin reaches it"* (`…-adversary-04a.md` §P3). A 04b caller
   that CAN pass an empty set either reaches it (→ needs a pin) or must not.

### Q1.4 The mutation proof that pins it as the SOLE decision point — 04b must EXTEND it

**The load-bearing pair (this is the one to extend):**
`test_enforced_relations.py::TestTheSharedPolicyIsTheSOLEDecisionPoint::test_MUTATION_neutralising_the_shared_policy_lets_publish_reach_the_ENGINE`
and `…_lets_send_reach_the_ENGINE`, plus
`test_POSITIVE_CONTROL_the_neutralised_policy_still_lets_a_REGISTERED_publish_through`
(`…-enforced-3.md` §1, table row MP-2a/b).

- **Instrument:** replace the shared policy with an **ACCEPT-EVERYTHING stub — NOT a raising
  sentinel** — and assert the unregistered id is then refused by the **ENGINE**
  (`pytest.raises(SurrealStoreError)`). The adversary's whole point: the two pre-existing sentinel
  mutations *"prove only that the function is CALLED, never that it DECIDES"*
  (`…-adversary-04a.md` §MISSING-PINS MP-2a/b, §P1b row I11).
- **MEASURED, both directions:** on W-E → `2 failed, 48 passed`, *"exactly these two"*; green on the
  correct build (`…-enforced-3.md` §1, §5). The same pin also kills W-A.
- **The neutralising mutation, verbatim and reproducible** — insert `return None` at the top of
  `reject_unknown_agents`' body, anchored on `    name_by_id: dict[str, str] = {}`; full
  `scripts/mutation_proof.py` invocation with `--expect-red` ids is pasted in **fixwave §F1**
  ("Reproduce"). Fixwave notes `--show-capture=no` is required on the child pytest or a captured log
  line mimics a summary line.
- **The SERVED-TEXT sharing proofs, also extendable:** fixwave §F3 mutates the formatter's sentence
  and requires **all three** legs of `TestTheSERVEDRefusalTextHasONEImplementation` to redden across
  four suites (`3 failed, 1270 passed`, EXIT=0, both directions clean) — **and the converse**: two
  further mutations each turn ONE double into a private copy and must redden **only its own** leg
  (`1 failed, 1060 passed` / `1 failed, 1143 passed`).
- **Builder's two independent format-string mutations** (builder §4.2/§4.3), each with its declared
  RED node ids, prove brief-side and message-side ride ONE string. ⚠ Builder discloses that its first
  two runs were **piped to `tail`, so `$?` was tail's** — re-run unpiped (builder §4.4). 04b: do not
  pipe.

**So the obligation on 04b is explicit:** a fifth caller (a `blocks` endpoint check, a sender check
for #247) adds a `test_MUTATION_neutralising_the_shared_policy_lets_<verb>_reach_the_ENGINE` leg **and
its positive control**, and if it serves the refusal text, a fourth leg on
`TestTheSERVEDRefusalTextHasONEImplementation` **plus** the converse private-copy mutation. Without
the new leg the neutralising stub proves nothing about the new verb.

---

## Q2 — THE `_define_relation_table` GENERATOR

### Q2.1 Exact signature (quoted by the scout from the tree at `e4cfc6e`, before the flip)

`receipts/…/REPORT-scout-pkt04-seams.md` §S6:

```python
def _define_relation_table(name: str, in_table: str, out_table: str, *, enforced: bool = False) -> str:
    enforced_clause = " ENFORCED" if enforced else ""
    return (f"DEFINE TABLE OVERWRITE {name} TYPE RELATION "
            f"IN {in_table} OUT {out_table}{enforced_clause} SCHEMAFULL")
```

**`enforced` semantics:** keyword-only `bool`, default `False`; `True` appends the literal
` ENFORCED`. The verb is **always `OVERWRITE`** — never `IF NOT EXISTS` — and that is the half that
makes a flip LAND on a long-lived store: *"`IF NOT EXISTS` on an existing edge table is a MEASURED
silent no-op — #107's shape. I changed the `enforced` argument and nothing about the clause"*
(builder §3.1, citing store reference §1.1). Scout §S6 adds that the docstring already records a
3.2.1 re-probe: *"the flip lands `ENFORCED`+`IN`/`OUT` on an existing untyped edge table."*

**Its four callers at 04a's start** (scout §S6): `_briefed_statements` (`briefed`, `agent`→`brief`,
`False` → flipped to `True` by 04a) · `_message_statements` (`to`, `message`→`agent`, already `True`)
· `_refers_statements` (`refers`, `False`) · `_answers_to_statements` (`answers_to`, `False`). The
last two are deferred to packet 43. `blocks` is the fifth call.

### Q2.2 ⚠ THE BRIEF'S PREMISE IS WRONG — no proof pins all four edges

There is **no** mutation proof over four edges, and its absence is DELIBERATE. `REPORT-contract-04a-enforced.md`
§S4(a): *"It now declares exactly the edges 04a flips: **one**. `FLIPPED_BY_04A` is a single-entry
tuple… A proof still declaring four edges would produce **declared reds that stay GREEN** — the
direction the both-ways diff exists to catch and the direction that reads as success.
`refers`/`answers_to` get their own proof in packet 43's file."*

**The proof as EXECUTED** (first executed by the adversary on its reference build, §P4; re-run by the
contract fixer, `…-enforced-3.md` §6; re-run by the builder on the real tree, builder §4.1):

- **Anchor:** the single call `_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)`;
  mutation = delete `enforced=True`.
- **Declared-RED set:** grown **6 → 8 before any run** because two new pins depend on the engine
  clause (MP-1 is a migration pin; MP-2a's publish leg deliberately observes BOTH layers) — and the
  file's prose sentence *"the app-check pins are deliberately NOT in the set"* was CORRECTED in the
  same edit, *"leaving it would have made the proof report two unexpected reds and invited a builder
  to 'fix' the list"* (`…-enforced-3.md` §6).
- **Result:** `8 failed, 42 passed in 5.15s`, `EXIT=0`, `PROOF HELD — the declared RED set fired
  EXACTLY`, tree restored byte-exact (`surreal_schema.py` md5 `86ba10f8…` / `ddc2d58a…` in the
  builder's run). **No unexpected reds; no declared red stayed GREEN** (builder §4.1).
- ⚠ **The node-id set itself is not transcribed in any report** — the reports name it as living in
  the contract file's own `MUTATION_PROOF` block, taken from `pytest --collect-only -q` **before** any
  run. 04b must read that block, not a report.

**What pins the OTHER three edges instead:** the ∀ pin plus the parametrised per-edge pins
(`test_the_edge_carries_ENFORCED_in_its_own_slice[to-generate_message_ddl]`,
`test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS`, the IN/OUT typing pin) — the adversary
proved those assertions are LIVE by building the wrong build *"Regress `to`'s `ENFORCED` while
flipping `briefed`"* and watching them kill it (`…-adversary-04a.md` §P1 killed-builds; §P1b rows
I3/I4/I14).

### Q2.3 Does any pin enumerate the edges BY NAME? — YES, one, and it fails CLOSED

**Stated plainly, as the brief asks.** There are two name-bearing artifacts and one text-derived ∀:

| artifact | shape | does a 5th edge silently escape? |
|---|---|---|
| `test_EVERY_relation_table_the_schema_emits_is_ENFORCED` | **∀ over the EMITTER's OUTPUT** — sweeps all **nine** DDL generators and text-parses the `DEFINE TABLE … TYPE RELATION` statements. *"Packet 04b's `blocks` edge is therefore pinned before it exists, and a fifth edge cannot arrive un-guarded"* (contract §1) | **NO** — it is not a name list at all |
| `test_the_relation_edge_set_is_EXACTLY_the_four_known_edges` + `KNOWN_RELATION_EDGES` (the per-edge pins are parametrised over it) | **an exact-set NAME enumeration** | **NO — it fails CLOSED.** Contract §6.8: it *"forces a deliberate declaration"*. A `blocks` edge reddens it until 04b adds it. This is deny-by-default, i.e. the safe direction the repo's instrument lesson prescribes — not the name-list failure mode |
| `_enforced_relations_scaffold.DEFERRED_TO_PACKET_43` | **an allowlist-the-safe EXEMPTION** — *"a small, enumerated, asserted safe-set… Anything not in that set must be `ENFORCED`, today and forever"* (contract §S0) | **This is the real escape hatch, and it is guarded in ANOTHER FILE — see below** |

⚠ **THE ONE THING 04B CAN GET WRONG HERE.** The adversary built W-C — *escape the ∀ by widening
`DEFERRED_TO_PACKET_43`* — and it was KILLED, but the forward-looking half is guarded only by
`test_derivation_source_unification.py::test_the_deferred_set_names_EXACTLY_the_two_code_graph_edges`
(RUNNING, not skipped; verified firing with `Extra items in the left set: 'briefed'`).
**`…-adversary-04a.md` §RESIDUALS R3: *"The 04a wave's gate must include that file, or a future
author who widens the exemption goes green on the file they are editing."*** A 04b builder who meets
a red ∀ pin and "fixes" it by adding `blocks` to the deferred set reddens **only a file it is not
running**. → **04b's wave gate MUST include `test_derivation_source_unification.py`.** It was green
in 04a's runs (`7 passed, 19 skipped`, `…-enforced-3.md` §8).

### Q2.4 What a NEW edge must add so the existing pins cover it

Assembled from contract §1/§S0/§6.8, scout §S4, `…-adversary-04a.md` §MISSING-PINS, builder §6 RB-11.
Items 1–2 are what the *existing* pins demand; 3–7 are what 04a learned the existing pins do **not**
give you.

1. `enforced=True` on its `_define_relation_table(...)` call — else the ∀ pin reddens.
2. Its name in `KNOWN_RELATION_EDGES` / the exact-set pin — else that pin reddens. Declaring it there
   also buys the per-edge `ENFORCED`-in-its-own-slice pin, the `OVERWRITE`-never-`IF NOT EXISTS` pin,
   and the IN/OUT typing pin, all parametrised over that set.
3. **A dirty-store migration leg whose OLD world is DERIVED from the production emitter** —
   `_define_relation_table(rel, in, out, enforced=False)` — **plus its own anti-vacuity pin**
   (`TestTheOldWorldDerivationIsNotVacuous` shape). A hand-written old-DDL string *"tests a copy of
   the code and passes while production stays broken"* (scout §S4; contract §1).
4. **A LEDGER-migration-path pin (the MP-1 shape) — the one the emitter-∀ cannot give you.** Drive
   the owning ledger's **own `ensure_ready()`** against a dirtied old-world store and nothing else.
   This is what kills W-A; without it, *"the contract proves the RECIPE migrates; nothing proves the
   CAKE does"* (`…-adversary-04a.md` §P1 W-A / MP-1).
5. **Its own entry in the group-C mutation proof's declared-RED set**, taken from `--collect-only`
   BEFORE the run, diffed both ways.
6. **An ORDER-DEPENDENCE pin + docstring note if its slice depends on another slice.** 04a's
   `briefed` slice became order-dependent on the agent slice; pinned by
   `TestTheBriefSliceIsOrderDependentOnTheAgentSlice` and recorded in `_briefed_statements`' docstring
   (contract §4.D5; builder §6 RB-11). **A `task->blocks->task` edge makes the task slice
   order-dependent on ITSELF, which is a different and unexamined shape — no report covers it.**
7. **If the RELATE takes a caller-supplied endpoint, an app-level existence check through the SHARED
   policy.** Scout §S6 established that `briefed` was the ONLY #105 exposure precisely because it
   takes a bare `str` from a caller, while `refers`/`answers_to` mint both endpoints inside the same
   fragment. **`blocks` takes `blocked_by` ids from a caller** (scout §S1) → same class as `briefed`,
   so it needs the app check *and* its teaching prose, not just the clause.

### Q2.5 The same-transaction question — scout's highest-risk unknown is now (partly) ANSWERED

Scout §S6 / §WHAT-I-COULD-NOT-DETERMINE #1 called this *"the single highest-risk unknown in the
packet"*: does `ENFORCED` resolve an endpoint **created earlier in the SAME uncommitted transaction**
on 3.2.1? **That claim is now stale for `briefed`,** and I name both sides rather than resolving it
by reading code: builder §5 drove the REAL registry + REAL ledger end-to-end on spike-surreal with
the flip LIVE and got `publish v1 by a REGISTERED agent -> OK`, and
`test_a_REGISTERED_agent_id_writes_the_brief_AND_the_ack_edge` asserts `_briefed_edge_count() == 1` —
and `briefed`'s `out` endpoint (the `brief` row) is CREATEd one statement earlier in the same
fragment (scout §S6 site 1). **So same-transaction resolution works for the OUT side, measured.**
Unmeasured still: the IN side minted in the same transaction, and `refers`/`answers_to` (packet 43).
**04b's `blocks` in `create_many` would mint BOTH endpoints in one fragment — that exact case is
UNMEASURED by any 04a report.**

---

## Q3 — WHAT THE ADVERSARY KILLED, AND WHAT TRANSFERS

Source: `receipts/…/REPORT-adversary-04a.md` §P1 (the four survivors, each with a run),
§MISSING-PINS (the seven pins prototyped to kill them), and `…-enforced-3.md` §1/§5 (the pins as
built, and the four re-measured kills).

### Q3.1 The four, each with wrong build → missing pin → pin added → measured kill

**W-A — the flip never LANDS through the production entry point.**
- *The wrong build:* the emitter is perfect; `BriefLedger.ensure_ready` does
  `generate_brief_ddl().replace(" ENFORCED SCHEMAFULL", " SCHEMAFULL")`. **MEASURED: 38/38, and
  `6 failed, 2073 passed` over seven suites — the SAME 6 the correct build has. ZERO new failures
  repo-wide.**
- *The pin that should have killed it and didn't:* `test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store`,
  whose own docstring claims to be *"the leg that catches"* a perfect-emitter/never-lands build — it
  is not, because **it applies the DDL itself**. Every migration pin in section B did.
- *Pin added:* **MP-1** `TestTheLEDGERsOwnMigrationPathLandsTheGuard::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE`
  + `test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints`. **Kill measured:
  `2 failed, 48 passed`** (`…-enforced-3.md` §5).

**W-B — the shared policy never queries the store (single-identity monoculture).**
- *The wrong build:* `del query`; refuse iff `agent_id == "unregistered_agent_0000000000000000"` —
  the ONE literal every negative leg in the contract used. **MEASURED: 38/38 survives.
  `test_brief_ledger.py` catches nothing;** only `test_message_ledger.py`'s independent ghost killed
  it — *"an accident of a neighbouring suite, not a property of this contract."*
- *Pin added:* **MP-5** — a SECOND, differently-shaped unregistered identity,
  `UNREGISTERED_AGENT_ID_WEARING_THE_REGISTERED_SHAPE` (`"registered_agent_000…0"`), parametrised
  across three negative legs. **Kill measured: `3 failed, 47 passed`, all three the new param.**

**W-D — the checks run AFTER the write, through the shared `except` — and it is GREENER than correct.**
- *The wrong build:* `publish` mints first, then checks, then hands the version back via best-effort
  `_release_version`; `ack` has no upstream check at all — the engine's `ENFORCED` rejection lands in
  `_relate_briefed`'s `except SurrealStoreError` (which is the idempotent-re-ack signal) and the app
  error is manufactured from inside that handler. **MEASURED: 38/38, and `2 failed, 2077 passed`
  versus the CORRECT build's `6 failed, 2073 passed` — four MORE pre-existing pins pass.**
  *"The incentive gradient points at the wrong build."*
- *The pins that should have killed it:* `test_the_refusal_happens_BEFORE_the_version_is_minted`
  (*"its own docstring admits the hole and then does not close it"*) and
  `TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent`, whose class docstring states
  *"two distinct failure modes must not share one except clause"* **while no assertion in the class
  checks it** — the repo's own FALSE-GATE class.
- *Pins added:* **MP-3** `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row`
  (row EXISTENCE is the discriminator the version NUMBER is not — a mint-then-release build leaves the
  `brief_counter` row behind at 0) + **MP-4** `…::test_a_refused_ack_never_ATTEMPTS_the_RELATE`
  (monkeypatch `_relate_briefed` to raise a sentinel; the app error must win). Each ships a named
  positive control. **Kill measured: `3 failed, 47 passed`.**
- ⚠ **And MP-3's own pin was still weak until the fix wave.** The cold audit's F1 found
  `test_the_refusal_happens_BEFORE_the_version_is_minted` PASSED under the neutralising mutation while
  claiming in its docstring to be *"THE discriminator"*; fixwave §F1 strengthened it to assert
  `await _version_counter_rows(ledger) == []`, made the overlap with MP-3 deliberate and documented,
  and reproduced the original defect independently (`EXIT=4`, "DECLARED RED but STAYED GREEN").

**W-E — ROUTING IS NOT SHARING.**
- *The wrong build:* the shared function exists, both ledgers import and CALL it, and it decides
  nothing (`return None`); each ledger keeps a private copy underneath. **MEASURED: 38/38 + every
  neighbour suite. "Nothing anywhere catches it."** The contract author had PREDICTED this (its §3
  survivor #5) and could not close it without a semantic mutation of a function that did not exist
  yet; the adversary upgraded it from note to BLOCKER.
- *Pin added:* **MP-2a/b** (see §Q1.4). **Kill measured: `2 failed, 48 passed` — "and ONLY those two,
  which is the design."**

*(Also killed, for completeness — each with its own run in §P1: W-C widen-the-exemption · W-F
subclass-instead-of-identity · drop-the-self-ack-RELATE · `ENFORCED`-but-keep-`IF NOT EXISTS` ·
flip-by-hand-at-the-call-site · regress-`to`-while-flipping-`briefed`.)*

### Q3.2 TRANSFER — which shapes recur in 04b's three deliverables

**All four recur. None is retired by 04a's fixes**, because every fix was a pin on 04a's own surface.

| shape | recurs in 04b as | what the 04b contract must carry |
|---|---|---|
| **W-A** (emitter right, migration never lands) | The `blocks` DDL emits `ENFORCED` but the **task** ledger's own boot path never applies the changed slice to a long-lived store | An MP-1-shaped pin driving **`TaskLedger`'s own `ensure_ready()`** (or whatever applies the task slice) on a DIRTIED store, and nothing else. ⚠ No report states whether `TaskLedger` even HAS an `ensure_ready` — scout §S1 does not mention one. Establish that first; if the task slice is applied by a different owner, the pin must drive **that** owner |
| **W-B** (policy keyed on the one fixture literal) | (a) a `blocks` endpoint/cycle check keyed on a fixture-shaped task id; (b) a fleet unread/unacked count that returns a constant; (c) a footer that decides "traffic pends" from a hard-coded value | ≥2 differently-SHAPED task ids in every negative leg (task ids are pre-minted `uuid4().hex` in `AppContext._create_many`, scout §S1 — so vary against dashed/bracketed/short shapes; see §Q4 axis A1) and ≥2 distinct counts per served number |
| **W-D** (write first, compensate in a shared `except`; GREENER than correct) | **The single most likely 04b defect.** Scout §S1: `create_task` does **not** go through `_apply` — it issues one bare `CREATE` via `_query`. A `blocks` mirror there *"lands in a second, separately-failable write"*. A builder that meets red atomicity pins and moves the edge downstream arrives exactly at W-D | The MP-3 shape (*a refused/failed X never TOUCHES <row>*) and the MP-4 shape (monkeypatch the write helper to raise a sentinel; the app error must win). Explicitly pin `create_task` and `create_many` **separately** — scout §S1: *"a contract that only pins `create_many` will miss it"* |
| **W-E** (routing≠sharing) | **`_comms_footer` is this shape's natural habitat**: three dispatchers each calling one helper while hand-rolling the *"is this a mutation / does traffic pend"* decision underneath | A neutralising (accept-everything / return-nothing) stub on the shared footer helper, with a leg per dispatcher asserting the served output changes for **all three** — and the converse private-copy mutation per call site (fixwave §F3's two-direction pattern) |
| **W-F** (subclass where identity was pinned) | Any new 04b error type (a cycle error, a blocked-task error) | If the pin's NAME promises identity, the assertion must check identity — 04a had to RENAME the pin when the ruling changed the shape (`…-enforced-3.md` §0 deviation 2) |
| **W-C** (widen the exemption) | A builder adds `blocks` to `DEFERRED_TO_PACKET_43` to silence the ∀ pin | Wave gate includes `test_derivation_source_unification.py` (§Q2.3) |

**One more transfer the adversary states directly and 04b should copy:** *"A PROBE NEEDS A CONTROL."*
Every one of the seven added pins ships a **named positive control**, and `…-enforced-3.md` §1 argues
each control is load-bearing rather than decoration (MP-2's control proves the accept-everything stub
is INERT for legal input, so its two reds are caused by the id and not by the patch; MP-4's control
proves the monkeypatch actually attached).

---

## Q4 — FIXTURE / MONOCULTURE LESSONS

Per-axis, with the axis named and the 04b instruction. Primary source:
`receipts/…/REPORT-adversary-04a.md` §P2 (the perturbation PAIR + a per-fixture verdict table),
plus `…-enforced.md` §S7 and `…-enforced-3.md` §8.

**A1 — id SHAPE (the R-2 axis). KNOWN to the lead.** The cold audit's residual R-2 records that every
id in `test_enforced_relations.py` is unbracketed, so a `split(":")`-style wrong build is invisible to
the file that owns the policy; caught only by three neighbouring suites (135 reds). Independently
corroborated from the other side by builder §3.2 and `…-enforced-3.md` §7 D-d.1, where the uuid-shaped
`agent:⟨0199c4f1-…⟩` rendering cost **130 red pins**. **04b instruction:** any test that constructs or
parses a record id must use ≥2 shapes — at minimum one bare (`task:abc`) and one bracketed/uuid-shaped.
Task ids are `uuid4().hex` (scout §S1), i.e. **unbracketed by default**, so 04b inherits the same blind
spot for free unless it deliberately breaks it.

**A2 — single-literal identity monoculture.** `UNREGISTERED_AGENT_ID` was the ONE literal behind every
negative leg. Verdict in the adversary's table: **"CANNOT DISCRIMINATE"**, proven by the perturbation
PAIR — leg 1 (perturbed contract on the CORRECT build) `38 passed` = the perturbation is not botched;
leg 2a (original contract on W-B) `38 passed` = blind; leg 2b (perturbed on W-B) `4 failed, 34 passed`
= discriminates. *"The fixture VALUE is what blinds the contract."* Fixed by MP-5's second identity.
**04b instruction:** every "does not exist" / "is invalid" input class needs ≥2 literals of different
construction, and the contract should run the perturbation pair as its own receipt.

**A3 — parameter-VALUE monoculture: `_BRIEF_NAME = "project"`.** Adversary verdict: **MONOCULTURE** —
*"the exact value repo law names as having manufactured a blind spot. No branch keys on it today;
perturbation to `"wave-7-charter"` is green on the correct build, so the change is free. Recommend
it."* **⚠ I found no report saying this was DONE** — the fix wave closed F1/F2/F3 and
`…-enforced-3.md` §8 lists the residuals it fixed; A3 is not among them. Treat as **still open**
(and see §Q6-O7). **04b instruction:** the fleet view keys on `STANDING_BRIEF`/`name` and the footer
may key on tool/action names — any fixture that uses one such value everywhere is this axis again.

**A4 — closed-set monoculture: `via="explicit"`.** Adversary: monoculture over a 3-value closed set
(`register`/`explicit`/`publish`); `publish` is exercised by the self-ack, **`register` never**.
Verdict *"Low risk, named"* — not fixed. **04b instruction:** the footer's action classification is
exactly a closed vocabulary; enumerate it and assert each member is exercised.

**A5 — small-N `len()` ≡ `sum()`.** Adversary judged 04a's own instances SAFE for a stated reason
(*"the code under test counts nothing; `len()`≡`sum()` is not reachable here"* for
`_briefed_edge_count() == 1`). **04b cannot inherit that exemption** — 04b's fleet columns and footer
DO count. Scout §S2 states the live trap: *"a fixture where `len(pending) <= limit` cannot discriminate
a whole-set count from a window count."* **04b instruction:** every count fixture must exceed the
display cap, and hold ≥2 items per group.

**A6 — the SWEEP-COVERAGE axis (`_seed_agent_rows`, the D1 fix).** This is the richest one and it is
three lessons in one (`…-enforced.md` §S7):
- The §4.D1 spec said *"~15 lines, one fixture, no test edits"*. **WRONG** — an AST derivation found
  **six** functions in `test_brief_ledger.py` that construct a real `BriefLedger`, only one of which is
  the factory. *"A seeded factory plus five unseeded helpers is precisely the 'a fix reached one copy
  and not the other' shape."* Solved as **ONE function with SIX call sites**.
- **Coverage was made a CHECKED VARIABLE**, not a derivation performed once: an AST sweep pin asserting
  every real-ledger builder also calls the seeder, plus a pin that every module-level `AGENT_*_ID`
  constant is in the seeded set.
- ⚠ **The first version of that sweep MATCHED ITSELF** — a substring sweep whose own assertion message
  mentioned `BriefLedger(` and `make_env(`, so the gate counted itself as a covered site and a future
  author could satisfy it by *mentioning* the seeder in a comment. Rewritten to AST `Call`-node
  detection with the gate's own class excluded by name. *"Caught by printing what the sweep saw
  instead of trusting that it saw the right things."*
- And the FLOOR: `len(builders) >= 5` under a message saying SIX — adversary R4: *"One builder site can
  be deleted with the gate green."* Fixed to `_REAL_LEDGER_BUILDER_FLOOR = 6`, with the message READING
  the constant so number and prose come from one place (`…-enforced-3.md` §8).
- **Named re-open trigger, still live (adversary R5):** the sweep's reach is keyed on
  `{"BriefLedger", "make_env"} <= called`, so *"a helper that takes `env` as a PARAMETER and constructs
  a `BriefLedger` is invisible"*. Exactly one such function exists today and is safe. **Trigger: the
  first `env`-taking real-ledger helper.**
- **04b instruction:** if the `blocks` work needs any per-site seeding/mirroring (it will — every real
  `TaskLedger` builder that writes a blocked task), build the AST coverage sweep with a floor read from
  a constant, exclude the gate's own class, print what it saw, and mutation-prove it by deleting one
  call site.

**A7 — a fixture factory must not DEFAULT a parameter the served text branches on.** Fixwave §F3 made
`FakeBriefLedger._reject_unknown_agent`'s `agent_name` a **required keyword-only** parameter: *"a
default would let the fake serve a different sentence for a fixture reason"*. **04b instruction:** the
footer's inputs (pending counts, agent id, action) must be required at every double.

**A8 — the fake fleet's own monoculture.** `_message_fakes.FakeMessageLedger`'s unknown set was
collected as a set of **NAMES**, so *"two agents may share a display name, and a name-keyed set silently
merged two bad recipients into one refusal line"*; changed to first-wins per ID (fixwave §F3; builder
§6 RB-1/RB-6). **04b instruction:** any grouping key in the fleet columns must be the ID, never the
display name.

---

## Q5 — REMOVED-BEHAVIOUR + LIVE-VERB CHANGES

### Q5.1 What actually changed on `BriefLedger.publish`

**The SIGNATURE did not change.** Builder §3.6, explicitly and deliberately: the operator's
no-consumers ruling *permitted* retyping `agent_id`, and the builder **kept it a bare `str`** because
*"Retyping it to `AgentRefLike` would redden ~90 pins I may not edit — the latitude is real but the
contract is the binding constraint, so the 'hardening' here is the existence check and its placement,
not a signature change."* The contract had written both readings down as D3 (`…-enforced.md` §4.D3)
and picked (1); it notes reading (2) *"is arguably the better design"* and costs exactly one pin to
switch. **So `publish(name, body, *, created_by, note=None, agent_id: str | None = None)` is
unchanged** (signature quoted by scout §S5 from the pre-flip tree).

**The BEHAVIOUR changed, in one direction:** *"a publish with an unknown `agent_id` now refuses before
the mint rather than writing the brief and dangling its ack. `agent_id=None` is untouched — the third
input class, legal and edge-free, forced by its own pin"* (builder §6, closing paragraph). `ack` gained
the same check before its versions read.

**The pins that now hold it** (builder §6 verdict column, `…-enforced-3.md` §1, fixwave §F1):
- `test_the_refusal_happens_BEFORE_the_version_is_minted` — **strengthened by fixwave F1** to assert
  the `brief_counter` hot row is ABSENT immediately after the refused publish; the "next version is
  v1" leg demoted to *consequence, not proof*.
- `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row`
  (MP-3) — deliberately overlapping the above, *"so deleting either leaves the discrimination
  standing"*, with a **NOT REDUNDANT WITH** paragraph naming its twin.
- `…::test_a_refused_ack_never_ATTEMPTS_the_RELATE` (MP-4), with its positive control.
- `test_agent_id_None_is_ACCEPTED_and_writes_no_edge` — the third input class.
- `test_a_REGISTERED_agent_id_writes_the_brief_AND_the_ack_edge` (`_briefed_edge_count() == 1`).
- `test_POSITIVE_CONTROL_a_REGISTERED_agents_re_ack_is_still_already_acked` — the idempotent-re-ack
  signal and first-write-wins `via` survive.
- `TestTheSERVEDRefusalTextHasONEImplementation` ×3 legs — the exact served sentence, production and
  both doubles (fixwave §F3).

### Q5.2 The removed-behaviour METHOD 04b should copy for the dispatcher collapse

04a ran this instrument **three times, by three different authors**, and the third pass found things
the first two missed. That is the transferable part.

1. **The author's inventory.** Contract §5 = 10 items; builder §6 = **11 items, each adjudicated**
   preserved-with-pin / dropped-deliberately / old-bug-not-re-pinned. Builder's framing is the one to
   quote to a 04b builder: *"The no-consumers ruling grants latitude not to PRESERVE a behaviour; it
   does not excuse not NOTICING one."*
2. **⚠ THE INDEPENDENT ENUMERATION, DIFFED — this is the half that paid.** `…-adversary-04a.md` §P6b
   enumerated the replaced code's observable behaviours **from SOURCE** and found **three the author's
   inventory did not itemise**: (a) the ONE-query-regardless-of-count property (*"the extraction must
   not become one-query-per-recipient"* — and `test_message_ledger`'s query-count pins do not cover
   it); (b) *"names the recipient's NAME, never its ID"* — **load-bearing**, because 04a pins the ID
   while a neighbour pins the NAME, so *"a builder emitting only one loses a pin in one file or the
   other"*; (c) dedupe + sort of the unknown set, a served-ORDER property. It also found the author's
   item 7 adjudication measurably FALSE. **The adversary disclosed its own contamination**: it read
   the source before the report but had read the report's §5 before writing the enumeration down —
   *"Partially contaminated; stated rather than hidden."* 04b should run P6b **before** reading the
   inventory.
3. **The "runtime behaviour is unchanged" receipt — four instruments, weakest named as weakest.**
   Fixwave §RUNTIME-BEHAVIOUR-UNCHANGED, verbatim in structure:
   (i) the served string proven **byte-identical against the RETIRED expression transcribed out of
   `git show <sha>:<file>`** — not against memory — over **15 cases** including 0/1/2/3+/25 identities,
   two agents sharing a display name, a dashed uuid, an em-dash-and-parens name, and **all 6
   permutations of a 3-identity input** so insertion order cannot leak through a new dict:
   `cases=15 mismatches=0`;
   (ii) a diff-scope argument (one file docstring-only, one expression changed; no call graph, no
   query, no control flow, no exception type, no DDL);
   (iii) **the neutralising mutation still produces the SAME behaviour it produced at the base commit**
   — *"If the refactor had moved a decision, that run's shape would have changed"*;
   (iv) the consumer suites of both doubles green at an unchanged count.
   *"The full-suite count is necessary and **not** sufficient, so it is the weakest of these four."*
   Delta accounting was exact: `7134 → 7137 = +3 and only +3`, the three new pins, collectable by node id.
4. **Adjudicate a prose deletion as a behaviour.** Builder RB-9 deleted `ack`'s docstring claim
   *"this ledger never queries the `agent` table itself"* because *"it became FALSE the moment the check
   landed"* — the #219 class. RB-5 (dropping the word "recipient" from the shared refusal) was
   **escalated for a lead ruling rather than decided** (builder §7 E-1).

### Q5.3 What this means for the footer collapse specifically

The reports do not cover the footer's removed behaviour (no 04a report mentions `_comms_footer` at all
outside `REPORT-scout-pkt04-seams.md`; grep confirmed). What the scout DOES supply, and 04b must treat
as inventory input for a delete/replace of `tasks`/`findings`' return points:

- **~17 distinct `return` statements** across the three dispatchers: `claim_task` 1 · `tasks` 6 + 1
  raise · `findings` 9 + 1 raise (scout §S3 table). *"Appending a `_comms_footer` at the render sites
  would be sixteen-plus clones of one policy — precisely the `#102` shape repo law forbids."*
- Collapsing to one return per dispatcher **deletes branch-local return expressions** — each one is an
  inventory item with a fate, per the removed-behaviour law.
- **D2, the type mismatch:** `tasks`/`claim_task`/`findings` return **bare `str` built by f-string**,
  while the comms surface renders through `Rendered`/`SafeLine`/`render_line`/`render_join`/
  `render_compose`/`sanitise_line`. *"A `_comms_footer` built as `Rendered` and appended to a plain
  `str` crosses the render-safety boundary in the wrong direction, and a footer built as a plain
  f-string is a NEW un-sanitised served surface. Decide which, deliberately."*
- `AppContext._render_claim_result`'s own docstring already declares its `blocked_by`/`status` branch an
  unsanitised **"residual gap"** — and **04b will be touching that render** (scout §S1, §S3).
- **`TracingFastMCP.call_tool` was evaluated and REJECTED as the seam**, with three named costs: its
  return type is `Sequence[ContentBlock] | dict[str, Any]` not `str`; restricting it to three tools
  means a tool-NAME allowlist, which is *"exactly the staleness that seam was designed to avoid"*
  (it fails closed, which is the acceptable direction, *"but say it out loud"*); and its failure posture
  is ruled *"the tool call's outcome ALWAYS wins"* — **do not append the footer inside the shielded
  `finally`.** Scout's recommendation is candidate 2, the shared helper at each dispatcher's single exit
  — which is the brief's plan.
- ⚠ **`_INSTRUCTIONS` is pinned BY EQUALITY** — `test_comms_tool.py::test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`
  (CL3, RULED, an allowlist over the whole served document) plus
  `test_the_comms_block_is_the_ONLY_paragraph_claiming_a_comms_DUTY`, **whose docstring names packet 04
  by name**: *"packets 04 (`_comms_footer`) and 05 (await/story) both add to this block, and a general
  'fleet etiquette' paragraph is exactly what a later author writes."* Footer teaching prose must land
  **through** the declared-paragraph allowlist, not around it.
- **Unsettled spec question, both readings written down** (scout §WHAT-I-COULD-NOT-DETERMINE #4): which
  ACTIONS count as "a mutation"? (a) per-TOOL — simple, stale-proof; (b) per-ACTION-OUTCOME — only calls
  that actually wrote. Scout picks (b) *"because a footer on a read is noise on the highest-frequency
  path and the packet's own word is 'mutations'"*, and notes `claim_task`'s LOSING branch writes
  nothing, so *"mutation" is a per-outcome question, not a per-tool one*. **This is an unruled spec
  ambiguity — repo law makes it an escalation, not a contract decision.**

---

## Q6 — OPEN OBLIGATIONS

Every item on its own line with its receipt and a verdict. **KNOWN** = the lead's brief already names it.

### Escalations awaiting a ruling
- **O1 — KNOWN. The message SENDER door (#247).** `receipts/…/REPORT-adversary-04a.md` §RESIDUALS R8 /
  §P1b row I13, with a **door-build receipt**: on the CORRECT reference build,
  `send(sender=_Ref(UNREGISTERED_AGENT_ID,…), recipients=[registered])` **SUCCEEDS** (`1 passed`).
  Re-stated unclosed by builder §7 E-2 and `…-enforced-3.md` §7 D-b. *"The fix itself is small: pass the
  sender into the same shared call"* (builder E-2). ⚠ `…-enforced-3.md` §9.3 discloses it **inherited**
  the adversary's door-build result rather than re-deriving it.
- **O2 — KNOWN. #105's own text-widening.** Adversary R12: a named packet deliverable *"with no test and
  no mention in the contract"*; fixwave §WHAT-I-COULD-NOT-DETERMINE #5 confirms this wave touched it.
- **O3 — E-1: the shared refusal no longer says "recipient".** Builder §6 RB-5 / §7 E-1 — a deliberate
  drop, escalated for a lead ruling, *"If the lead wants 'recipient' back for `send`, the fix is one
  parameter and one format string, in one file."* **No report records a ruling.**
- **O4 — the footer's "which actions are mutations" fork.** Scout §WHAT-I-COULD-NOT-DETERMINE #4. Both
  readings written down; **unruled**. Lands directly in 04b.

### Prose defects still live outside 04a's writable sets
- **O5 — ⚠ HIGHEST VALUE, and it aims straight at 04b.** `docs/reference/surrealdb-31-capabilities.md`
  §8's open-hazards list, the `#105` bullet, still asserts *"An application-level existence check is the
  only guard"* — **the same sentence §6.3 of that very file records as FALSE**, and which §4 replaces
  with the `ENFORCED` adoption table. Found by fixwave's own anchor-free sweep, **not by the audit**
  (fixwave §FLAGS-1), with a proposed one-bullet replacement quoted in full. *"The store reference is
  the file every store/schema/DDL brief is told to read FIRST, and it currently teaches, in its own
  summary of open hazards, the exact claim that produced the §6.3 entry."* **04b's `blocks` brief IS a
  store/schema/DDL brief.**
- **O6 — `docs/design/2026-07-12-pkt28-c1-semantics.md` still asserts** *"the brief ledger never queries
  the agent table itself (one roster definition, one owner)"* **as current** — false since 04a. Fixwave
  §FLAGS-2 (= cold-audit §5 row 7). *"Operator's call whether a landed design doc gets a correction
  header; I made none."*

### Contract-side residuals recorded and NOT fixed
- **O7 — A3, the `_BRIEF_NAME = "project"` monoculture.** Adversary §P2 verdict **MONOCULTURE**, with
  *"perturbation to `"wave-7-charter"` is green on the correct build, so the change is free. Recommend
  it."* No report records it being done.
- **O8 — A4, the `via=` closed-set monoculture** (`register` never exercised). Adversary §P2, verdict
  *"Low risk, named"*.
- **O9 — R5, the D1 coverage sweep's reach** is keyed on `{"BriefLedger","make_env"} <= called`.
  Adversary R5, restated open in `…-enforced-3.md` §8. **Named re-open trigger: the first `env`-taking
  real-ledger helper.**
- **O10 — R9: the scaffold's `statements()` splits DDL on a bare `;`.** Measured safe today across all
  four relevant generators; *"A future ASSERT with a semicolon in its teaching prose mis-splits — but it
  fails CLOSED."* Verdict low risk, named. ⚠ **04b's `blocks` DDL may add teaching prose to an ASSERT.**
- **O11 — R10: `old_world_ddl` uses `str.replace(target, …)` with no `count=1`.** Safe today (one
  statement per edge). Cosmetic, named. ⚠ **A fifth edge is another statement in the same slice.**
- **O12 — R11: four store legs use bare `pytest.raises(Exception)`.** The adversary measured the real
  surface (`surrealdb.errors.NotFoundError: The record 'brief:<id>' does not exist`, which NAMES the
  ghost) and judged this a *"strengthening suggestion, not a missing pin"*.
- **O13 — `brief_ack` has NO tool-seam teaching pin.** MP-6 covers `brief_publish` only. Stated three
  times: builder §8.6, `…-enforced-3.md` §5.4, fixwave §WHAT-I-COULD-NOT-DETERMINE #1 (which adds that
  MP-6's production-side assertion is only an `id in str(exc)` substring check, not exact text, because
  `test_comms_tool.py` was outside the fix wave's writable set).
- **O14 — D7 / scout §S4 gap: the blast-radius pin does not cover every slice.**
  `test_surreal_store.py::test_the_whole_schema_migrates_an_existing_populated_store` applies four
  slices and **not** `generate_message_ddl()`. Contract §4.D7 adds that after 04a it also does not cover
  the newly-guarded edges. *"One line plus a seed row."* ⚠ **A `blocks` edge makes this gap wider again.**
- **O15 — D-c, the fake's declared bound**, pinned with its re-open trigger: *"the day the brief
  tool-seam harness seeds the fake's agent table wholesale"* (`…-enforced-3.md` §7 D-c).

### Measurement debts (nobody has a number)
- **O16 — CONCURRENCY / TOCTOU is unmeasured, stated by all three authors.** Builder §8.1: `publish`'s
  check-then-mint window is *"a genuine TOCTOU against agent retirement/deletion"*; the engine guard is
  the backstop *"that makes the window safe rather than merely narrow"*. Adversary §6 and
  `…-enforced-3.md` §9.4 agree, and both note a contract pin is the WRONG instrument (≥8-way, 20
  consecutive green runs). **04b's `blocks` acyclicity invariant is a concurrency property by nature** —
  two concurrent creates can form a cycle neither sees.
- **O17 — the cost of `ENFORCED` on 3.2.1 is unmeasured.** Stated by contract §6.6, builder §8.3
  (*"the store reference's 'none measurable' is a 3.1.5 figure and I did not re-derive it"*), and
  `…-enforced-3.md` §9.6.
- **O18 — the cost of the added existence read is unmeasured.** Builder §8.2: `publish`/`ack` each gain
  ONE query when `agent_id` is present. *"I did NOT measure latency and I am not asserting it is free."*
- **O19 — pre-existing dangling `briefed` edges in production: count UNKNOWN.** Ruled OUT as #236.
  Builder §8.4: *"nobody has measured it, so any number is a rumour — including zero."* And builder §6
  RB-10: **turning `ENFORCED` on is a FALSE ALL-CLEAR on pre-existing dangling edges** (store ref §4).
- **O20 — the deployed artifact is unproven.** Builder §8.5 ran nothing against `:18500` and built no
  image; fixwave §3 restates THE TEST ENVIRONMENT IS A FICTION and that only packet 01a's in-image
  conformance run proves the cake.
- **O21 — SEVEN hand-rolled `_bare_id` copies package-wide**, each beside its own private
  `_TABLE_SEPARATOR = ":"`: `agents.py`, `briefs.py`, `findings.py`, `messages.py`, `tasks.py`,
  `memory/local.py`, `store/surreal.py`. Builder §7 E-3, **derived by grep, not recalled** — and the
  builder discloses its own first draft said FIVE, *"an un-derived count inside the escalation about
  un-derived counts."* Pre-existing; builder added none. **Recommendation: a finding with a named home
  (a neutral `bare_record_id`), not a fix inside this packet.** ⚠ **`tasks.py` is on that list and 04b
  edits `tasks.py`** — an eighth copy is one careless line away, and D-d proves the parse is easy to get
  wrong.

### Report-hygiene hazards 04b will trip over
- **O22 — ⚠ THE TWO CONTRACT REPORTS HAVE DIVERGED, and the stale one carries a KNOWN-FALSE claim.**
  *Method disclosed: I ran `diff <(sed -n '1,700p' REPORT-contract-04a-enforced.md) REPORT-contract-04a-enforced-2.md`
  — empty output.* `REPORT-contract-04a-enforced-2.md` is byte-identical to the **first 700 lines** of
  `REPORT-contract-04a-enforced.md` and **lacks its §S8 CORRECTION NOTE** (lines 701–739). The report's
  own header instructs: *"**Archive ONE** (either) into … and delete the other, with a one-line header
  saying which address survived."* **Both were archived and neither carries that header.** Consequence:
  a 04b agent that lands on `-2` reads §5 item 7's *"pins sameness, not identity, so a builder may keep
  `UnknownRecipientError` as a subclass"* — measured FALSE by the adversary (§P4 / W-F: `1 failed, 249
  passed`) and corrected only in the copy it is not reading. **Recommended: add a one-line superseded
  header to `-2`, or delete it. This is exactly #152/#153's class.**
- **O23 — the surviving contract report's SUMMARY BLOCK is stale by design of the correction protocol.**
  It still reads *"60 pins"* / *"26 failed, 34 passed"*; §S1/§S2 carry 38/17 and §S8 C1 carries the
  re-derived 50 pins / `26 failed, 24 passed`. Adversary R7 flagged it because *"the block the lead reads
  FIRST was not updated"*; the fix was an APPENDED note, never a rewrite (§S8's own stated reason: §1–§7
  are cited from the INDEX Log and commits). **04b: read §S8 before trusting any count above it.**
- **O24 — three counts in these reports were wrong once and corrected in place; re-derive before citing.**
  `_seed_agent_rows` *"three call sites"* → **six**, plus a SECOND instance in the same file's section
  banner (*"FIVE call sites … the sixth site"*) that the adversary's R6 did not name
  (`…-enforced-3.md` §8) · `~50 publish sites` → **74**, independently re-derived by AST, *"and one fact
  the audit did not state: all 74 are TEST sites"* (fixwave §DEVIATIONS D-1, which deliberately did NOT
  add a pin: *"the honest instrument for a soft number is a dated derivation"*) · the D1 *"≥29 collected
  `[real]` ids"* floor, retired by `…-enforced.md` §S7.5.
- **O25 — `REPORT-investigate-hardkill-reaper.md` (605 lines) is in the 04a archive and NOBODY has
  triaged it for 04b.** It was outside my brief and I did not read it. If 04b touches process lifecycle
  or the reaper, that is an unread inheritance.

### Stale-versus-sibling conflicts I found (both sides named, neither resolved by me)
- **O26 — scout §S6/§D3 vs builder §5.** Scout calls same-transaction endpoint resolution under
  `ENFORCED` *"the single highest-risk unknown in the packet"*, UNVERIFIED. Builder §5's end-to-end run
  on a live store with the flip LIVE shows `publish v1 -> OK` with `_briefed_edge_count() == 1`, whose
  `out` endpoint is created one statement earlier. **Scout's D3 is stale for `briefed`'s OUT side;
  still unmeasured for an IN side minted in the same txn and for `refers`/`answers_to`.** See §Q2.5.
- **O27 — adversary §C-DEF-2 and §C-DEF-3 were BLOCKING and are now CLOSED**, measured
  (`…-enforced-3.md` §4: `50 passed, 0 failed` on the contract; `2189 passed, 0 failed, 14 skipped`
  across nine suites). Anyone reading the adversary report alone will believe no repo-wide 0-failed
  build exists. It does.
- **O28 — adversary residuals R1 and R2 were RED at HEAD and are fixed**, per the archival banner the
  adversary report now carries (fixed at `369db57`; the four wrong builds killed at `bbada6a`).

---

## What I could not determine

1. **Whether O3 (the "recipient" wording), O4 (the mutation-action fork) or O7 (the `_BRIEF_NAME`
   perturbation) were ever ruled or done.** No report in my source set records a ruling or a fix; the
   cold audit and the probe (which I was told not to re-read) may.
2. **The shipped, annotated signature of `reject_unknown_agents`** — see §Q1.1. No report quotes it.
3. **The declared-RED node-id set of the group-C mutation proof** — the reports name its home (the
   contract file's `MUTATION_PROOF` block) but do not transcribe it.
4. **Whether `TaskLedger` has an `ensure_ready`-equivalent** that a `blocks` MP-1 pin would drive. Scout
   §S1 maps the write path and never mentions one.
5. **Anything about the `blocks`-specific hazards named but not covered:** deterministic edge ids
   becoming a hard error on SurrealDB 4.0 (probe §4 / #349) and the `+collect` closure correction
   (probe §5.1). Contract §6.8 and §S6 both say these *"are 04b's and are covered by nothing here"* —
   they live in the probe report, which is the lead's read.
6. **Any claim in the cold audit or the probe** — deliberately not re-read per the brief, so where those
   two contradict what I report above, they win.
