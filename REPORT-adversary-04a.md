# REPORT-adversary-04a — grading the packet-04a `ENFORCED` sweep contract

brief-base v7 read

*Every measurement below was taken **2026-07-26/27** against `feat/surreal-unification` @ **`dfb5cd0`**
(clean tree; the only worktree modification at session start and end is the pre-existing
`REPORT-contract-04a-enforced-2.md`). Live legs ran on **spike-surreal `ws://127.0.0.1:18000` (the
TEST store) ONLY** — `:18500` was never contacted. Present-tense claims describe THAT commit; a
future reader must re-derive before relying on any number here.*

**Scratch provenance (#140) — every build below ran in a `scripts/scratch_copy.sh` tree:**
`loremaster.__file__ = /tmp/claude-1000/-home-ejprice-PycharmProjects-lore/d960719f-3a88-43ff-bfc8-4744d1b1d61c/scratchpad/ref/loremaster/loremaster/__init__.py`
(printed live, `uv run python -c "import loremaster; print(loremaster.__file__)"`). Reference-build
files were content-backed-up (`cp -a`) and restored byte-exact after every wrong build — md5s in §P1.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline — FOUR wrong builds survive the contract 38/38.** W-A (`ensure_ready` applies a
  de-`ENFORCED` copy: **0 new failures repo-wide**) · W-B (shared policy keyed on the one fixture
  literal, never queries the store) · W-D (checks run AFTER the write, sharing `_relate_briefed`'s
  `except`: **greener repo-wide than the correct build** — 2077 pass vs 2073) · W-E (routing-is-not-
  sharing; the author predicted it, I measured it: survives 04a **and** every neighbour).
- **C-DEF: the contract file IS satisfiable — `38 passed, 0 failed`** on my reference build, and still
  `38 passed` after `ruff --fix`; `ruff` clean, `scripts/typecheck.sh` OK ×3. **But no build I could
  construct is 0-failed REPO-WIDE**: the app check inside `ack` breaks **5 pins in
  `test_retry_seam.py`** (`_AckConnection` is a closed-set fake). §C-DEF.
- **Mutation proof — RAN, BOTH WAYS, `EXIT=0`, declared set fired EXACTLY** (6 declared / 6 observed,
  no unexpected reds, no declared-green). **App-check pins (E/F/G/H) stayed INDEPENDENT** — none
  reddened under the engine mutation. §P4.
- **Exemption attack: CLOSED** — widening `DEFERRED_TO_PACKET_43` reddens 5 other 04a pins *and*
  `test_derivation_source_unification.py::test_the_deferred_set_names_EXACTLY_the_two…` (running, not
  skipped, verified firing). ⚠ that guard lives in a DIFFERENT FILE — the wave gate must run it.
- **MISSING PINS (7, all prototyped and proven RED-on-wrong / GREEN-on-correct):** §MISSING-PINS.
- **Two gates are ALREADY RED at HEAD `dfb5cd0`, both caused by the 04 wave** —
  `test_surreal_harness::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` (36→39 importers)
  and `test_retired_symbols::test_no_file_references_a_retired_symbol` (`INDEX.md:46`, added by
  `b539bbf`). §RESIDUALS R1/R2.
- **The contract report contains one FALSE claim a builder will act on** (§5 item 7: "pins *sameness*,
  not identity") — measured wrong: W-F. And its SUMMARY BLOCK still says "60 pins / 26 failed". §P4.
- Receipt pointers: §C-DEF · §P1 (four surviving builds + md5 restores) · §P1b quantifier table ·
  §MISSING-PINS · §P2 perturbation pair · §P4 · §P6b · §RESIDUALS · §WHAT-I-COULD-NOT-DETERMINE.

**Packages considered:** (my own table, built BEFORE opening the author's — diff in §P-PKG)
`ENFORCED` endpoint guard → SurrealDB engine clause (READ: store reference §4 adoption table + the
live `NotFoundError` text I measured) → **replace** (engine, not hand-rolled) ·
unknown-agent existence check → in-house `MessageLedger._reject_unknown_recipients` (READ: its body —
one direct-record-access `SELECT id FROM $ids`) → **replace by extraction** ·
sharing mutation instrument → `pytest.MonkeyPatch` (READ: `setattr(..., raising=True)` fails closed) →
**replace** · DDL mutation proof → `scripts/mutation_proof.py` (READ: `--expect-red` both-ways diff) →
**replace** · **SurrealQL statement parser** (`statements()`, `_DEFINE_RELATION_RE`, `is_enforced`) →
READ: `pkgutil.iter_modules(surrealdb)` = `['_surrealdb_ext','cbor','connections','data','errors','request_message','types']`,
no parser surface; `sqlglot 30.8.0` `DIALECTS` = 32 dialects, **no SurrealQL** → **bespoke, justified**
(the author's survey OMITS this mechanism) · live DDL application → repo's own
`store._txn.execute_transaction` → **replace** (the scaffold does this correctly).

---

## C-DEF — the satisfiability receipt the contract had none of

I built the reference implementation (it is the only way to grade the contract) in the scratch tree:

| file | change |
|---|---|
| `store/surreal_schema.py` | `_briefed_statements` → `_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)` |
| `loremaster/agent_existence.py` (new) | `UnknownAgentError(RuntimeError)` + `async reject_unknown_agents(query, agents)` — ONE direct-record-access read, names every missing id |
| `loremaster/briefs.py` | imports the shared symbol; `publish` calls it **before** `_mint_version`; `ack` calls it **before** the versions read |
| `loremaster/messages.py` | imports the shared symbol; `_reject_unknown_recipients`' body → one delegating call; `UnknownRecipientError = UnknownAgentError` |

```
$ cd <scratch>/ref && uv run pytest -q loremaster/tests/test_enforced_relations.py -p no:randomly -n auto
38 passed in 8.17s
$ uv run ruff check --fix .        -> Found 1 error (1 fixed, 0 remaining)      [my import order, not the contract's]
$ uv run ruff check .              -> All checks passed!
$ ./scripts/typecheck.sh           -> lorescribe OK / loresigil OK / loremaster OK
$ uv run pytest -q loremaster/tests/test_enforced_relations.py -p no:randomly -n auto   # AFTER the lint cleanup
38 passed in 5.53s
```

**The contract file itself: 0 FAILED against a correct build, including the harder post-ruff leg.**
Nothing in it is RED-on-a-correct-build. That is a genuine strength and the author should be told so.

### ⚠ C-DEF-2 (BLOCKING, and the contract report does not name it): `test_retry_seam.py`

Repo-wide the same build is **not** 0-failed:

```
$ uv run pytest -q -n auto -p no:randomly            # full suite, reference build
9 failed, 7104 passed, 36 skipped, 3 xfailed, 1 warning in 191.05s
```

Attribution, measured against a HEAD baseline (`uv run pytest -q loremaster/tests/test_retry_seam.py
test_logging_setup.py test_retired_symbols.py test_surreal_harness.py -n auto` at `dfb5cd0`
→ `2 failed, 636 passed`):

| failure | cause |
|---|---|
| `test_retired_symbols::test_no_file_references_a_retired_symbol` | **PRE-EXISTING at HEAD** — §R1 |
| `test_surreal_harness::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` | **PRE-EXISTING at HEAD** — §R2 |
| `test_logging_setup::test_ordinary_traceback_text_is_not_mangled` | **MY PROBE'S ARTIFACT** — the scratch path contains `-home-ejprice-PycharmProjects-lore`, which the log scrubber redacts. Passes at HEAD. Disclosed, not a finding. |
| `test_message_ledger::TestVocabularies::test_every_domain_error_is_a_message_ledger_error` | the reference build — §C-DEF-3 |
| `test_retry_seam::TestTheAckEdgeNeverReportsAnExhaustedRelateAsAReAck` ×4 <br> `test_retry_seam::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_brief_ack_door` | **the reference build — the finding** |

Verbatim:

```
E  AssertionError: the ack path issued a statement this fake does not serve: 'SELECT id FROM $agent_ids'
   loremaster/tests/test_retry_seam.py:3897
```

`_AckConnection.query` is a **deny-by-default fake** that serves exactly `ack()`'s two SELECTs and the
RELATE and raises on anything else. The 04a contract REQUIRES `ack` to refuse an unregistered agent,
which necessarily adds a store read to the ack path — so **the contract cannot be satisfied without
editing `test_retry_seam.py`**, a heavily mutation-proven pre-existing contract that guards the
#102/#120 retry law. The contract report's §4 escalations name `test_brief_ledger.py` (D1) as *the*
structural contradiction and **miss this one entirely**.

*Exact edit a builder will need (escalated, not made): `_AckConnection.query` must serve the shared
policy's existence read — returning `[{"id": RecordID(AGENT_TABLE, _ACK_AGENT_ID)}]` — so `ack`
proceeds to the RELATE. Note the coupling this creates: the retry-seam fake becomes sensitive to the
shared policy's SQL. That is a design question, and it belongs to the operator.*

### ⚠ C-DEF-3 (BLOCKING): the error TYPE is a three-way fork, and every reading costs something

`test_BOTH_verbs_raise_the_SAME_error_type_for_an_unknown_agent` asserts `type(a) is type(b)` —
**identity**, not `isinstance`. `test_message_ledger::TestVocabularies` asserts
`issubclass(UnknownRecipientError, MessageLedgerError)`. Together they force ONE type raised by both
verbs that is also a `MessageLedgerError`. All three readings measured:

| reading | 04a | `test_message_ledger` |
|---|---|---|
| shared `agent_existence.UnknownAgentError`, `UnknownRecipientError` = alias (my reference build) | 38 passed | **1 failed** (`test_every_domain_error_is_a_message_ledger_error`) |
| **W-F** — keep `UnknownRecipientError` as a SUBCLASS of the shared error (**the contract report's own §5 item 7**) | **1 failed** (`test_BOTH_verbs_raise_the_SAME_error_type…`) | 211 passed |
| **W-G** — the shared module raises `messages.UnknownRecipientError` (so `agent_existence` imports its neighbour, and `BriefLedger.publish` raises a **MessageLedgerError**) | 38 passed | 211 passed → `372 passed, 14 skipped` over 04a+message+brief |

Only W-G is green on both — and it violates the contract's own §E/D4 rationale (the shared module
exists precisely so neither ledger owns the shared object). **This is spec ambiguity, which repo law
makes an escalation, not a contract decision.** It must be ruled before a builder starts.

---

## P1 — the wrong builds (the headline)

All four survivors ran the **REAL** contract file, unmodified, in the scratch tree. Reference-build
files restored byte-exact after each (`cp -a` content backup, md5 verified):
`briefs.py cf44c317ebec1a650d32c9b366bf5dea` · `messages.py c8a4ce82ec7e7f477c30eaf831b1b012` ·
`agent_existence.py 57c9db0c9411631bff78f56ae2b5c28d` ·
`surreal_schema.py 86ba10f8d2a1b08369cc5d2f06d0ceea`.

### ⛔ W-A — the flip never LANDS through the production entry point (`ensure_ready`)

```python
# briefs.py::BriefLedger.ensure_ready
ddl = generate_brief_ddl().replace(" ENFORCED SCHEMAFULL", " SCHEMAFULL")
```

The emitter is perfectly correct. Only the ledger's own migration path — **the sole path by which
production ever migrates this table** — de-enforces it.

```
04a contract         -> 38 passed in 4.82s
04a + brief_ledger + message_ledger + comms_schema + comms_tool + surreal_schema + retry_seam
                     -> 6 failed, 2073 passed   ... the SAME 6 the CORRECT build has. ZERO new failures.
```

**Which pin should have killed it:** `test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store`.
Its own docstring says *"a definition that emits perfectly and never LANDS is invisible to every
offline pin — this is the leg that catches it."* It is not: it calls
`apply_ddl(connection, generator(), url=env.url)` **itself**. Every migration pin in section B applies
the DDL by hand. **The contract proves the RECIPE migrates; nothing proves the CAKE does** — which is
#107's exact shape, in the packet written to prevent #107's shape.

### ⛔ W-B — the shared policy never queries the store (single-identity monoculture)

```python
async def reject_unknown_agents(query, agents):
    del query                                   # the agent table is never consulted
    unknown = {... for agent_id, label in agents if agent_id == "unregistered_agent_0000000000000000"}
```

```
04a contract                                  -> 38 passed in 8.38s        (SURVIVES)
test_message_ledger + test_brief_ledger       -> 4 failed, 330 passed      (killed by MESSAGE-ledger pins only)
```

Every negative agent-existence leg in `test_enforced_relations.py` uses ONE literal,
`UNREGISTERED_AGENT_ID`; every positive leg uses one `registered_agent_<uuid4>`. **`test_brief_ledger.py`
catches nothing.** Only `test_message_ledger.py`'s independent ghost (`ghost-id-does-not-exist`) kills
it — an accident of a neighbouring suite, not a property of this contract.

### ⛔ W-D — the checks run AFTER the write, through the shared `except` (and it is GREENER than correct)

`publish` mints first, then checks, then hands the version back via the **best-effort**
`_release_version`; `ack` has NO upstream check at all — the RELATE is attempted, the engine's
`ENFORCED` rejection lands in `_relate_briefed`'s `except SurrealStoreError` (the idempotent-re-ack
signal), and the app error is manufactured from inside that handler.

```
04a contract   -> 38 passed in 5.14s                       (SURVIVES)
the 7-suite set-> 2 failed, 2077 passed in 26.86s
   vs the CORRECT reference build on the same set:  6 failed, 2073 passed
```

**W-D passes FOUR MORE pre-existing pins than the correct build.** A builder that lands the upstream
`ack` check, meets 5 red retry-seam pins, and "fixes" them by moving the check downstream arrives
exactly here — with a greener suite. The incentive gradient points at the wrong build.

**Which pins should have killed it:**
`test_the_refusal_happens_BEFORE_the_version_is_minted` — its own docstring admits the hole
(*"would still see v1 only if the release succeeded"*) and then does not close it: `_release_version`
succeeds, so v1 is observed either way. And `TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent`'s
class docstring states the property outright — *"two distinct failure modes must not share one except
clause"* — while **no assertion in the class checks it**. That is the repo's own *false-gate* class:
a message promising a check the assertion does not perform.

### ⛔ W-E — ROUTING IS NOT SHARING (the author predicted this; I measured it)

`agent_existence.reject_unknown_agents` exists, both ledgers import and CALL it — and it decides
nothing (`return None`). Each ledger keeps a private copy of the decision underneath.

```
04a contract                              -> 38 passed in 7.48s     (SURVIVES)
test_message_ledger + test_brief_ledger   -> 1 failed, 333 passed   (that 1 is the C-DEF-3 vocabulary
                                                                     pin, present on the CORRECT build too)
```

**Nothing anywhere catches it.** Both sharing mutations replace the shared symbol with a **raising**
sentinel, which proves only that the function is CALLED. §3 survivor #5 of the contract report is real,
and it is a BLOCKER rather than a note.

### ✅ Killed builds (individual verdicts, each with a run)

- **W-C — escape the ∀ pin by widening `DEFERRED_TO_PACKET_43` to include `briefed`.** KILLED:
  `5 failed, 33 passed` in 04a (the per-edge slice pin, the old-world derivation pin, the dirty-store
  pin, the un-enforcing-door pin, the order-dependence pin) **and** `1 failed, 6 passed, 19 skipped` in
  `test_derivation_source_unification.py` (`test_the_deferred_set_names_EXACTLY_the_two_code_graph_edges`,
  RUNNING, fired with `Extra items in the left set: 'briefed'`). The exemption is genuinely
  deny-by-default. ⚠ but the *forward-looking* half of it (04b's `blocks` arriving un-guarded + exempted)
  is guarded ONLY by that other file — see §R3.
- **W-F — `UnknownRecipientError` as a subclass of the shared error.** KILLED by
  `test_BOTH_verbs_raise_the_SAME_error_type_for_an_unknown_agent` (`1 failed, 249 passed`). The pin
  works; the contract *report* describing it is wrong (§P4).
- **Drop the self-ack RELATE entirely** ("no dangling edges because no edges"). KILLED by
  `test_a_REGISTERED_agent_id_writes_the_brief_AND_the_ack_edge` (`_briefed_edge_count() == 1`) — this
  pin ran green in every surviving build, so the assertion is live.
- **`ENFORCED` but keep `IF NOT EXISTS`.** KILLED offline by
  `test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS` and behaviourally by the dirty-store leg
  (both reddened under the mutation proof, §P4).
- **Flip only the named edge by hand at the call site rather than through the emitter.** KILLED by the
  mutation proof: the anchor is the single `_define_relation_table(...)` call and its removal reddens
  exactly the declared set (§P4).
- **Regress `to`'s `ENFORCED` while flipping `briefed`.** KILLED by
  `test_the_edge_carries_ENFORCED_in_its_own_slice[to-generate_message_ddl]` + the ∀ pin (both green in
  every build above, so the assertions are live).

---

## P1b — THE QUANTIFIER TABLE

| # | invariant | ∀-over-inputs or GUARDED | receipt |
|---|---|---|---|
| I1 | every emitted `TYPE RELATION` table carries `ENFORCED` | **∀** over the EMITTER's output (9 generators, text-parsed, not a name list) | ∀ pin + exact-set pin; W-C could not slip an edge past it |
| I2 | the flip actually LANDS on a dirty store | **GUARDED** — pinned only for DDL the TEST applies; the production entry point is never driven | ⛔ **W-A survives 38/38, 0 new failures repo-wide** |
| I3 | the clause is `OVERWRITE`, never `IF NOT EXISTS` | **∀** over all four known edges (kept total, correctly) | mutation proof + offline pin |
| I4 | `IN`/`OUT` endpoint typing declared | **∀** over all four known edges | offline pin, parametrized over `KNOWN_RELATION_EDGES` |
| I5 | pre-existing dangling edges SURVIVE the flip | GUARDED to the one flipped edge — acceptable (04a flips one) and the fixture asserts `len(before) == 1` | green in every build; door-build n/a |
| I6 | a dangling edge is a first-class traversal member (§6.4 is FALSE) | **∀** for the query shape, with a `[]`-producing positive control | green; control proves the query CAN return `[]` |
| I7 | the un-enforcing door exists and is demonstrated | **∀** (a pinned BOUND, per *WHEN YOU CANNOT CLOSE A HOLE, PIN IT*) | reddened under the mutation proof |
| I8 | `publish(agent_id)`'s three input classes each have a FORCED fate | **∀** over the CLASSES (unregistered / registered / `None`) | all three fixtures exist and are distinct |
| I9 | …but the DECISION is a real store lookup | **GUARDED** by ONE literal identity per class | ⛔ **W-B survives 38/38**; P2 perturbation restores discrimination (§P2) |
| I10 | the refusal happens BEFORE any write | **GUARDED** — observed only as "next version is v1", which a mint-then-release build also satisfies; `ack` has NO discriminator | ⛔ **W-D survives 38/38 and is greener than correct** |
| I11 | ONE IMPLEMENTATION — the shared policy is the sole decision point | **GUARDED** — the mutation proves the function is CALLED, never that it DECIDES | ⛔ **W-E survives 38/38 + all neighbours** |
| I12 | both verbs raise the SAME error type | **∀** at the value level (needs no name) — pin works | W-F killed by it; but see C-DEF-3 |
| I13 | no stored identity names a non-existent agent | **GUARDED** to recipients + `publish`'s `agent_id`. **The message SENDER is an unguarded door.** | ⛔ door-build receipt: on the CORRECT reference build, `send(sender=_Ref(UNREGISTERED_AGENT_ID,…), recipients=[registered])` **SUCCEEDS** (`1 passed`). Same bad outcome, different door. Escalated. |
| I14 | `to`'s shipped `ENFORCED` is not regressed | **∀** (parametrized slice pin + the ∀ pin) | green in every build |
| I15 | the exemption set may only SHRINK | **∀**, but pinned in **another file** | W-C reddens `test_derivation_source_unification.py`, not 04a — §R3 |
| I16 | the brief slice is order-dependent on the agent slice | **∀** for the property (single instance is the property) | reddened under the mutation proof |
| I17 | the idempotent-re-ack signal + first-write-wins `via` survive | **∀** with its own positive control | green in every build incl. W-D |

Four guarded rows carry a **surviving wrong build**. That alone is the verdict.

---

## MISSING PINS — each prototyped, each proven RED-on-wrong / GREEN-on-correct

Prototypes lived in the scratch tree only (`<scratch>/ref/loremaster/tests/test_adversary_probe_04a.py`,
deleted after use). **Every one is GREEN on the reference build (`7 passed`, then `46 passed` alongside
the 38 contract pins) and RED on its named wrong build** — the pair, both legs.

**MP-1 · `TestTheLEDGERsOwnMigrationPathLandsTheGuard::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE`**
Apply the agent slice + the OLD un-enforced `briefed` DDL to a virgin DB, dirty it with one dangling
edge, then build a REAL `BriefLedger` on that database and call **`ensure_ready()`** — nothing else.
Assert a fresh dangling `RELATE` is then refused. Ships with
`test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints`.
*Catches:* **W-A** — an emitter that is correct and a migration path that is not (#107's shape).
`1 failed, 1 passed` on W-A; `2 passed` on the reference build.

**MP-2a/b · `TestTheSharedPolicyIsTheSOLEDecisionPoint::test_MUTATION_neutralising_the_shared_policy_lets_{publish,send}_reach_the_ENGINE`**
Replace the shared policy with an **ACCEPT-EVERYTHING** stub (not a raising sentinel) and assert the
unregistered id is then refused by the **ENGINE** (`pytest.raises(SurrealStoreError)`).
*Catches:* **W-E** (a private copy still refuses → not a `SurrealStoreError` → RED) **and W-A**
(nothing refuses at all → no raise → RED). `2 failed` on W-E; green on the reference build.
This is the semantic mutation the two existing sentinel mutations cannot be.

**MP-3 · `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row`**
After a refused publish, assert `SELECT id FROM brief_counter` is `[]`. Row EXISTENCE is the
discriminator the version NUMBER is not — a mint-then-release build leaves the row behind at 0. Ships
with `test_POSITIVE_CONTROL_an_ACCEPTED_publish_DOES_create_the_counter_row`.
*Catches:* **W-D**'s publish half.

**MP-4 · `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_ack_never_ATTEMPTS_the_RELATE`**
Monkeypatch `BriefLedger._relate_briefed` to raise a sentinel; an unregistered `ack` must raise the
app error, **not** the sentinel. This is section G's own class docstring, converted from prose into an
assertion.
*Catches:* **W-D**'s ack half — the two failure modes sharing one `except`.

**MP-5 · a SECOND, differently-shaped unregistered identity on the publish/ack legs**
e.g. `"registered_agent_00000000000000000000000000000000"` — an id that wears the *registered* shape.
*Catches:* **W-B** and every prefix/literal-keyed refusal. Measured: §P2.

**MP-6 · a tool-seam pin for `brief_publish` with a bogus `agent_id`**
The packet's Exit criterion is *"a bogus-recipient publish/send **teaches** instead of dangling"* — a
statement about the SERVED surface. `send` has two tool-seam pins
(`test_comms_tool.py::TestUnregisteredRecipientIsTheEXISTINGTeachingError`,
`TestEveryBadRecipientIsNamedInONEReject`). **`brief_publish` has none** — grep over its 90 tool-seam
call sites finds no unknown/bogus/ghost agent case — and `FakeBriefLedger` (which every one of them
runs on) models no `agent` table at all.
*Catches:* a build where the ledger refuses correctly and the tool seam swallows or re-wraps the
teaching error. TRUST-DOCTRINE surface.

**MP-7 · a `FakeBriefLedger` parity pin for the unknown-agent policy**
`_message_fakes.FakeMessageLedger` checks `self.db.agents` and raises `UnknownRecipientError`;
`_comms_fakes.FakeBriefLedger.publish` has no equivalent and the 04a contract requires none.
*Catches:* real/fake divergence on the packet's headline property — the `[fake]` half becomes
decoration for it. (P5 verdict below.)

---

## P2 — fixture discrimination, with the perturbation PAIR

Perturbed a scratch COPY of the contract
(`test_enforced_relations_PERTURBED.py`): `UNREGISTERED_AGENT_ID` →
`"registered_agent_00000000000000000000000000000000"`, and `_BRIEF_NAME` `"project"` → `"wave-7-charter"`.

```
leg 1  PERTURBED contract on the CORRECT reference build -> 38 passed in 4.76s   (control: not botched)
leg 2a ORIGINAL  contract on W-B                         -> 38 passed in 4.99s   (blind)
leg 2b PERTURBED contract on W-B                         -> 4 failed, 34 passed  (discriminates)
```

Failing under 2b: `test_an_UNREGISTERED_agent_id_is_REFUSED`, `test_the_refusal_NAMES_the_bad_agent_id`,
`test_an_ack_by_an_UNREGISTERED_agent_is_REFUSED_and_never_already_acked`,
`test_a_MIXED_recipient_list_is_refused_and_writes_NO_message_row`. **The fixture VALUE is what blinds
the contract.**

A second, independent result falls out of leg 2b: `test_the_refused_publish_writes_NO_brief_row` and
`test_the_refusal_happens_BEFORE_the_version_is_minted` **still pass** when the refusal comes from the
ENGINE rather than the app check — confirming MP-3's need from a second direction.

**Per-fixture verdicts (no "the rest look fine"):**

| fixture | verdict |
|---|---|
| `UNREGISTERED_AGENT_ID` (one literal, every negative leg) | **CANNOT DISCRIMINATE** — W-B + perturbation pair. MP-5. |
| `registered_agent_<uuid4>` (one registered identity) | adequate — uuid4 per fixture, and `record_exists` is asserted before every negative leg |
| `_BRIEF_NAME = "project"` (every publish/ack leg) | **MONOCULTURE** — the exact value repo law names as having manufactured a blind spot. No branch keys on it today; perturbation to `"wave-7-charter"` is green on the correct build, so the change is free. Recommend it. |
| `via="explicit"` (every ack leg) | monoculture over a 3-value closed set (`register`/`explicit`/`publish`); `publish` is exercised by the self-ack, `register` never. Low risk, named. |
| `ghost_id()` | **STRONG** — fresh uuid4 per call, absence asserted by `record_exists` before use. Cannot accidentally become all-registered. |
| `old_world_ddl()` derived from `_define_relation_table` | **STRONG** — derived from the production emitter, and its vacuity has its OWN pin (`TestTheOldWorldDerivationIsNotVacuous`), which reddened correctly under the mutation proof |
| `edge_set_clause()` | **STRONG** — keeps every rejection attributable to the ENDPOINT; the positive-control legs prove a real endpoint IS accepted with the same clause |
| `len(before) == 1` in the survival pin | adequate — a stated fixture pre-condition, not a smuggled assumption |
| `_briefed_edge_count() == 1` / `len(_brief_rows) == 1` | small-N, but the code under test counts nothing; `len()`≡`sum()` is not reachable here |
| `migration_db` (`MIGRATION_DIM = 8`) vs `brief_ledger_with_a_real_agent` (`PRODUCTION_DIM`) | fine — no pin depends on embedding width |
| `apply_ddl` via `execute_transaction` | **STRONG** — a bare `connection.query(ddl)` would validate `statement[0]` only (store reference §3); this is the correct seam |

---

## P3 — branch reachability

| branch | test that fails if deleted | verdict |
|---|---|---|
| `_define_relation_table` `enforced=True` arm | `test_the_edge_carries_ENFORCED_in_its_own_slice[briefed-…]` (reddened under the mutation proof) | reached |
| `_define_relation_table` `enforced=False` arm | `test_the_old_world_DIFFERS_from_todays_generator` + `test_re_emitting_the_edge_WITHOUT_ENFORCED…` | reached (by the scaffold and by `refers`/`answers_to`) |
| `publish`: `agent_id is None` | `test_agent_id_None_is_ACCEPTED_and_writes_no_edge` | reached |
| `publish`: `agent_id` given, registered | `test_a_REGISTERED_agent_id_writes_the_brief_AND_the_ack_edge` | reached |
| `publish`: `agent_id` given, unknown | the four `TestPublishRefusesAnUnregisteredAgent` legs | reached |
| `publish`: the `except SurrealStoreError → _release_version` path | **NO 04a pin reaches it on the correct build** — the app check runs upstream. Still reached by pre-existing blank-body/contention pins in `test_brief_ledger.py`. | honest scope note |
| shared policy: empty input early-return | **UNREACHABLE through either real entry point** (`publish` passes exactly one; `send` raises `EmptyRecipientSetError` first). A builder will write it; no pin reaches it. | dead branch, named |
| `_relate_briefed`: `TxnContentionExhaustedError` | `test_retry_seam.py`'s four ack pins — **which the reference build breaks** (§C-DEF-2) | reached, but see C-DEF-2 |
| `_relate_briefed`: `SurrealStoreError` + existing edge | `test_POSITIVE_CONTROL_a_REGISTERED_agents_re_ack_is_still_already_acked` | reached |
| `_relate_briefed`: `SurrealStoreError` + no existing edge → re-raise | no 04a pin; `test_retry_seam::test_a_domain_rejection_on_a_GENUINELY_NEW_pair_still_propagates` covers it — MP-4 would add a 04a-side reach | reached elsewhere |
| `is_enforced()` false arm | the ∀ pin's `offenders` map (RED at HEAD, green after the flip) | reached |
| the `DEFERRED_TO_PACKET_43` exemption arm | **only reached because two edges are currently exempt**; it evaporates when packet 43 empties the set, and `test_the_deferred_set_is_EMPTY` is `@skip`ped until then | named, correct |

---

## P4 — the author's claims, reproduced (never relayed)

| claim | verdict |
|---|---|
| contract is **17 RED / 21 passed** at HEAD | ✅ reproduced: `17 failed, 21 passed in 7.76s` |
| `test_brief_ledger.py` **122 passed** after D1 | ✅ reproduced: `122 passed in 6.98s` |
| **the mutation proof is a PREDICTION and has never executed** | ✅ true — and I ran it on the reference build, the first tree where it can. `EXIT=0`, `PROOF HELD — the declared RED set fired EXACTLY` (6/6). Tree restored byte-exact (`md5 86ba10f8d2a1b08369cc5d2f06d0ceea`). **No unexpected reds; no declared red stayed green.** |
| **app-check pins (E/F/G/H) are deliberately excluded and must stay independent** | ✅ **independent** — under the engine mutation: `6 failed, 32 passed`, and the six are exactly the declared engine pins. No app-check pin reddened. The two layers are NOT coupled. |
| §2: "no red comes from a `TypeError`, a collection error, or a pre-existing pin this contract contradicts" | ✅ for the contract FILE (C-DEF 38/38). ❌ as a statement about the wave: the contract *does* structurally contradict a pre-existing pin — `test_retry_seam.py` (§C-DEF-2). |
| §3 survivor #5 ("routing but not sharing") | ✅ **CONFIRMED empirically** — W-E, 38/38 + neighbours. Upgrade from "recommendation" to BLOCKER. |
| §5 item 7: *"pins **sameness**, not identity, so a builder may keep `UnknownRecipientError` as a subclass of the shared error"* | ❌ **FALSE.** `type(a) is type(b)` **is** identity. W-F measured: `1 failed, 249 passed`. A builder following this sentence writes a build the contract rejects. Fix the sentence. |
| report SUMMARY BLOCK: "60 pins", "26 failed, 34 passed" | ❌ **STALE** — the split addendum (§SPLIT/S-blocks) carries the correct 38 pins / 17 RED, but the block the lead reads FIRST was not updated. |
| D1's `_seed_agent_rows` docstring: *"Three call sites share it"* | ❌ **WRONG COUNT — there are SIX** (`grep -n _seed_agent_rows` → lines 307, 659, 1155, 1384, 1583, 1844). The commit MESSAGE says six; the docstring says three. Derived-prose defect, in the fix for a derived-prose defect. |

---

## P5 — can the test doubles FAIL?

- The **04a contract uses no fakes at all** — every pin drives a real emitter, a real live store, or a
  real ledger. `_Ref` is a read-only data holder, not a double. Nothing to mutate; stated rather than
  skipped.
- **`_AckConnection` (`test_retry_seam.py`) CAN fail — loudly and correctly.** It is deny-by-default
  and it fired the moment the ack path issued an unserved statement (§C-DEF-2). Good instrument.
- **`_comms_fakes.FakeBriefLedger` CANNOT fail on this contract's headline property.** It models no
  `agent` table; `publish(agent_id=<anything>)` always succeeds. `_message_fakes.FakeMessageLedger`
  **does** model it (`if ref.id not in self.db.agents`). So after 04a, `send` has real/fake parity on
  the unknown-agent property and `publish` does not — and the 90 tool-seam `brief_publish` sites all
  run on the fake. **MP-7.**

---

## P6 — corpse sweep (every hit an individual verdict)

Swept `loremaster/tests/` for assertions pinning the OLD un-enforced `briefed` world.

| hit | verdict |
|---|---|
| `test_comms_schema.py::TestBriefedDdlOffline::test_table_is_a_schemafull_relation` | **CLEAN** — already rewritten by packet 03's flip; asserts only "SCHEMAFULL relation table". Green on the reference build. |
| `test_comms_schema.py` `TestRelationTablePolicyFlip` (`_relation_statement(generate_brief_ddl(), BRIEFED_RELATION)`) | **CLEAN** — asserts `OVERWRITE`/`IN`/`OUT`, not the absence of `ENFORCED`. Green. |
| `test_comms_schema.py:2986` hand-written `DEFINE TABLE IF NOT EXISTS briefed TYPE RELATION SCHEMAFULL` (live pin) | **CLEAN** — a deliberately-old-world fixture inside its own database; green. |
| `test_comms_schema.py:403` raw `RELATE $from->briefed->$to` | **CLEAN** — green on the reference build. |
| `test_brief_ledger.py` (≥29 `[real]` edge-writing ids) | **ALREADY FIXED** by D1 (`dfb5cd0`); 1355-pass neighbour run confirms. |
| `test_retry_seam.py` `BRIEFED_RELATION` uses | **NOT a corpse — a structural contradiction.** §C-DEF-2. |
| `test_surreal_store.py` `BRIEFED_RELATION` uses | **CLEAN** — green in the full-suite run. |
| `_message_fakes.py:217` "one permanent, silent dangling receipt" (comment) | **CLEAN** — prose about `to`, still accurate. |
| whole-tree control | the full suite on the reference build showed **no** briefed-related failures beyond §C-DEF-2/3 — `9 failed, 7104 passed`, all nine attributed above. |

## P6b — independent enumeration vs the removed-behaviour inventory

**⚠ Protocol disclosure:** I read `MessageLedger._reject_unknown_recipients`' SOURCE before opening
the contract report, but I had read the report's §5 inventory before writing this enumeration down.
Partially contaminated; stated rather than hidden.

The only code this packet **replaces** is `_reject_unknown_recipients`' body. Its observable
behaviours, from source:

| # | behaviour | in the author's §5 inventory? |
|---|---|---|
| a | ONE query regardless of recipient count (direct-record-access `SELECT id FROM $ids`) | not itemised — **found by me**; the extraction must not become one-query-per-recipient (`test_message_ledger`'s query-count pins do not cover it) |
| b | **names the recipient's `name`, never its `id`** | **not itemised — found by me, and it is load-bearing**: 04a's `test_the_refusal_NAMES_the_bad_agent_id` demands the **ID**, while `test_message_ledger::test_an_unregistered_recipient_is_rejected_by_name` demands the **NAME**. The shared message must carry BOTH (my reference build emits `"{name} ({id})"`). Nothing in the contract says so; a builder emitting only one loses a pin in one file or the other. |
| c | dedupes ids before reporting, sorts the unknown set | not itemised — a served-order property; `test_message_ledger` pins sorted recipient names elsewhere |
| d | raises BEFORE `_dedupe_by_identity` and before the ULID mint | itemised implicitly (item 7 / the "before the write" pins) |
| e | `UnknownRecipientError` is a `MessageLedgerError` subclass | itemised (item 7) — **but with a FALSE adjudication**; see §C-DEF-3 / §P4 |
| f | an EMPTY recipient list never reaches it (`EmptyRecipientSetError` first) | not itemised; harmless, but it makes the shared policy's empty-input branch unreachable (§P3) |

Inventory items I could **not** ground / disagree with: item 7 (adjudication measurably false).
Items 1–6 and 8–10 all ground in code and each has the pin the row claims (verified green on the
reference build).

---

## RESIDUALS — every one with an individual verdict

- **R1 — `test_retired_symbols::test_no_file_references_a_retired_symbol` is RED at HEAD `dfb5cd0`.**
  `docs/plans/v2/INDEX.md:46` names `_BRIEF_PUBLISH_`; introduced by **`b539bbf`** (packet 04's own doc
  re-scope), in the sentence explaining that the same gate had *just* been closed. **Verdict: real,
  in-wave, must be fixed before the 04a wave can have an honest green.**
- **R2 — `test_surreal_harness::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` is RED at
  HEAD.** *"the harness docstring says 36 test files import it; 39 actually do."* The three new
  importers are this wave's own (`_enforced_relations_scaffold.py`, `test_enforced_relations.py`,
  `test_derivation_source_unification.py`). **Verdict: real, in-wave, one-number fix.**
- **R3 — the exemption guard lives in a DIFFERENT FILE.** `test_the_deferred_set_names_EXACTLY_the_two_code_graph_edges`
  runs and fires (proven, W-C), but only in `test_derivation_source_unification.py`. **The 04a wave's
  gate must include that file**, or a future author who widens the exemption goes green on the file
  they are editing. Verdict: no contract change needed; a BRIEF/gate change.
- **R4 — the D1 coverage sweep's floor is `>= 5` while its own message says "there were SIX".** One
  builder site can be deleted with the gate green. Verdict: raise the floor to 6, or change the message.
- **R5 — the D1 coverage sweep's reach is keyed on `{"BriefLedger", "make_env"} <= called`.** A helper
  that takes `env` as a PARAMETER and constructs a `BriefLedger` is invisible. Measured: exactly one
  such function exists today (`TestBriefLedgerConnectionLifecycle._bare_ledger`) and it is **safe** (it
  never dials a real store). Verdict: not a hole today; **named re-open trigger — the first
  `env`-taking real-ledger helper.** This is the repo's own name-list instrument lesson.
- **R6 — `_seed_agent_rows`' docstring says three call sites; there are six.** Verdict: derived-prose
  defect, one-line fix (§P4).
- **R7 — the contract report's SUMMARY BLOCK is stale** (60 pins / 26 failed vs the real 38 / 17).
  Verdict: the lead reads that block first; fix it.
- **R8 — the message SENDER is an unguarded door** for "a stored identity naming no agent row"
  (I13; measured green on the correct reference build). Not obviously in 04a's scope. **Operator's
  call — escalated, not decided.**
- **R9 — the scaffold's `statements()` splits DDL on a bare `;`.** Measured: no generator currently
  emits a `;` inside a string literal (checked all four relevant generators). A future ASSERT with a
  semicolon in its teaching prose mis-splits — but it fails CLOSED (`is_enforced` goes false → the ∀ pin
  fires). Verdict: low risk, named, no action.
- **R10 — `old_world_ddl` uses `str.replace(target, …)` with no `count=1`.** Safe today (one statement
  per edge). Verdict: cosmetic; named.
- **R11 — the four store legs use bare `pytest.raises(Exception)`.** I measured the real surface:
  `surrealdb.errors.NotFoundError: The record 'brief:<id>' does not exist`, and it NAMES the ghost.
  Asserting that text would close the passes-for-the-wrong-reason door cheaply. Verdict: the
  positive-control legs already make the discrimination sound (only endpoint existence differs), and
  the mutation proof reddened all of them — so this is a **strengthening suggestion, not a missing
  pin**.
- **R12 — the packet's *"Widen #105's own text from 'latent — we never hard-delete' when resolving
  it"*** is a named deliverable with no test and no mention in the contract. Verdict: lead/brief item.
- **R13 — my own probe artifact.** `test_logging_setup::test_ordinary_traceback_text_is_not_mangled`
  fails in ANY scratch tree whose path contains a home-shaped string; it passes at HEAD. Verdict: not a
  defect; disclosed so nobody inherits it as one.
- **R14 — my own instrument lied once.** A `git status --short` after a compound `cd $S && …` reported
  the SCRATCH tree's dirty state as the repo's. Re-run with `git -C <repo>`: only the pre-existing
  `REPORT-contract-04a-enforced-2.md` is modified; `briefs.py`/`messages.py`/`surreal_schema.py` are
  byte-identical to HEAD and no `agent_existence.py` exists in the repo. **PROVE WHICH TREE YOU ARE
  TESTING applies to status commands too.**

---

## WHAT I COULD NOT DETERMINE

1. **Whether a build exists that is 0-failed REPO-WIDE.** I found none. Every satisfying build adds a
   store read to the `ack` path and breaks `_AckConnection`'s closed set (§C-DEF-2). Resolving it needs
   an edit to `test_retry_seam.py` — an operator/lead decision I am not entitled to make.
2. **Which of the three error-type readings is intended** (§C-DEF-3). All three are measured; the choice
   is a design ruling.
3. **Whether the SENDER door (R8) is in 04a's scope.** The packet's Exit criterion names *recipients*.
4. **Whether W-D would still pass a hand-placed check inside `_relate_briefed` that avoids the one
   remaining retry-seam red.** My W-D left one pin red
   (`test_a_domain_rejection_on_a_GENUINELY_NEW_pair_still_propagates`) purely because of *where* I put
   the call; a slightly different placement plausibly clears it. I did not enumerate placements. Treat
   W-D's "2 failed" as an upper bound on the damage a builder would see, not a floor.
5. **The `[fake]` half of `test_brief_ledger.py` after the flip.** I graded the real backend. Whether
   `FakeBriefLedger` should gain the policy (MP-7) is a design question about fake/real parity.
6. **Concurrency.** No 04a pin exercises the app check under contention (≥8-way), and I did not build
   one. `publish`'s check-then-mint window is a TOCTOU against agent retirement — I did not measure
   whether that matters, and the packet does not say.

---

# VERDICT: **CONTRACT INSUFFICIENT**

Four wrong builds survive it, one of them (W-D) *greener repo-wide than the correct build*; three of
its own stated properties — *"the flip actually LANDS"*, *"the refusal happens BEFORE the write"*,
*"the shared policy is ONE implementation"* — are asserted in docstrings and not in assertions. The
seven pins in §MISSING-PINS close all four, and every one is proven RED-on-wrong / GREEN-on-correct.

**It is also, in the ways it succeeds, a strong contract:** 0-failed against a correct build, a
mutation proof whose never-executed prediction turned out EXACTLY right both ways, two layers that
stayed provably independent, an exemption escape hatch I could not exploit, and a ∀ over the emitter
that no wrong build I built could slip an edge past. The gaps are in what it does not reach, not in
what it asserts.
