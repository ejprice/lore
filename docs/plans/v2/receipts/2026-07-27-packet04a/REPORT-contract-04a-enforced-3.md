# REPORT-contract-04a-enforced-3 — closing the contract-adversary's findings on packet 04a

brief-base v7 read

*Every measurement below was taken **2026-07-27** against `feat/surreal-unification` @ **`369db57`**
(the tree at start, and at end, carries ONLY the five test-side files listed under §0). Live legs ran
on **spike-surreal `ws://127.0.0.1:18000` (the TEST store) ONLY** — `:18500` was never contacted.
Present-tense claims describe THAT commit; re-derive before relying on any number here.*

**Scratch provenance (#140) — every wrong build and every mutation proof below ran in a
`scripts/scratch_copy.sh` tree, and its own guard printed:**
`loremaster -> /tmp/mp04a/ref/loremaster/loremaster/__init__.py`.
Reference-build files were `cp -a` content-backed-up and restored byte-exact after every wrong build
(md5s in §5). ⚠ `git status` was run with `git -C <tree>` after the adversary's R14 — the repo's own
status is in §0, the scratch's is not it.

---

## SUMMARY BLOCK

- **state:** done-with-deviations. All seven missing pins built; both lead rulings implemented; four
  residuals fixed. **No production module touched** (repo diff = 5 test files, §0).
- **MP-1** `TestTheLEDGERsOwnMigrationPathLandsTheGuard` — RED on **W-A** (2 failed vs 0) · GREEN on correct.
  **MP-2a/b** `TestTheSharedPolicyIsTheSOLEDecisionPoint` — RED on **W-E** (both legs) and on **W-A** · GREEN on correct.
  **MP-3** counter-row pin — RED on **W-D** · GREEN. **MP-4** RELATE-sentinel pin — RED on **W-D** · GREEN.
  **MP-5** second identity — RED on **W-B** (3 legs) · GREEN. **MP-6** `brief_publish` tool seam — RED at HEAD · GREEN.
  **MP-7** `FakeBriefLedger` parity — RED at HEAD on `[real]`+`[fake]` · GREEN. **All four surviving
  wrong builds are now KILLED** (§5, each re-built and re-measured).
- **RED count with the passed-COUNT tail:** contract alone `26 failed, 24 passed in 5.53s` (**50 pins**,
  was 38/17); 13-suite set `29 failed, 2431 passed, 33 skipped in 34.50s` — every failure mine by design.
  Gates: `ruff` **All checks passed!** · `scripts/typecheck.sh` **loremaster/lorescribe/loresigil OK**.
- **C-DEF (the receipt the contract never had): a reference build takes it to `50 passed, 0 failed`,
  and `2189 passed, 0 failed, 14 skipped` across nine suites** — so **C-DEF-2 and C-DEF-3 are CLOSED**, §4.
- **RULING 2's proof:** after widening `_AckConnection`, the retry-seam pins still go RED under their
  own mutation — `EXIT=0`, 3/3 declared, **twice**: at HEAD and on the reference build where the new
  branch is actually exercised (§3).
- **Mutation proof, both ways, EXECUTED for the first time (§6): `EXIT=0`, 8/8 declared fired EXACTLY**
  — including the two pins I ADDED to the declared set — no unexpected reds, no declared-green.
- **decisions-needed: 3** — (D-a) the shared error class's NAME collides with the existing
  `loremaster.agents.UnknownAgentError`; (D-b) the SENDER door (adversary R8) is still unguarded and
  still unruled; (D-c) the fake's declared bound (unmodelled agent table) — close it in 04a or defer
  with the trigger already pinned. §7.
- **Receipt pointers:** §0 diff · §1 the seven pins · §2 RED reasons · §3 retry-seam widening ·
  §4 C-DEF · §5 wrong builds · §6 mutation proof · §7 escalations · §8 residuals · §9 what I could not determine.

**Packages considered:** shared unknown-agent policy → in-house `MessageLedger._reject_unknown_recipients`
(READ: its body — one direct-record-access `SELECT id FROM $ids`) → **replace by extraction** (unchanged
from my predecessor; no library does a store-shaped existence read) · sharing mutation → `pytest.MonkeyPatch`
(READ: `setattr(..., raising=True)` fails closed on a missing attribute — which is what makes the E-section
pins RED-not-silent at HEAD) → **replace** · mutation proof → repo's `scripts/mutation_proof.py`
(READ: its `--expect-red` both-ways diff + the `--anchor-file` note; I hit its documented
anchor-must-match-EXACTLY-once guard on my first attempt, §3) → **replace** · scratch isolation →
repo's `scripts/scratch_copy.sh` (READ: its three poison modes) → **replace** · the fake's agent-table
model → `_message_fakes.FakeMessageLedger.register_agent` (READ: its `db.agents` + refusal body) →
**replace by cloning the SHAPE, not the code** — the two doubles are independent implementations by
design (that module's own "Fidelity" note), so the affordance is named and shaped identically and the
POLICY each enforces is the one thing they must not disagree about.

---

## §0 — what changed (repo diff, tests only)

```
$ git -C /home/ejprice/PycharmProjects/lore status --short
 M loremaster/tests/_comms_fakes.py
 M loremaster/tests/test_brief_ledger.py
 M loremaster/tests/test_comms_tool.py
 M loremaster/tests/test_enforced_relations.py
 M loremaster/tests/test_retry_seam.py
```
(plus the appended §S8 correction note in `REPORT-contract-04a-enforced.md`, per the brief.)

**DEVIATIONS, each disclosed rather than chosen silently:**

1. **I implemented the FAKE's unknown-agent policy** (`_comms_fakes.FakeBriefLedger._reject_unknown_agent`
   + `register_agent` + `FakeBriefDatabase.agents`) rather than pinning it and leaving it to the builder.
   Rationale: `_comms_fakes.py` is named in my writable set for MP-7, a test double is contract-side
   work in this repo (`_message_fakes` is), and the alternative left MP-6/MP-7 reddening with a bare
   `AttributeError` on a missing affordance instead of the intended contract-first absence. The builder's
   job stays production code.
2. **Three existing pins are now parametrised and one is RENAMED**, so their node ids changed:
   `test_an_UNREGISTERED_agent_id_is_REFUSED`, `test_the_refusal_NAMES_the_bad_agent_id`,
   `test_an_ack_by_an_UNREGISTERED_agent_is_REFUSED_and_never_already_acked` gain
   `[unregistered_agent_…]` / `[registered_agent_0…]`; `test_BOTH_verbs_raise_the_SAME_error_type_for_an_unknown_agent`
   → `test_BOTH_verbs_raise_an_error_a_caller_can_catch_with_ONE_except`. **The rename is not cosmetic:**
   a name that promises IDENTITY over an assertion that checks a COMMON BASE is the same false-gate
   class as a failure message that promises a check the assertion does not perform. None of the four is
   in the mutation proof's declared set, so no declared id was invalidated.
3. **The module docstring's ⚠ D1 warning was STALE** (it still said `test_brief_ledger.py` "needs the
   same treatment" — the seeding landed in `dfb5cd0`). Rewritten to record both structural
   contradictions and how each was closed. Stale served prose is the defect class this repo names most.
4. **`test_brief_ledger.py::brief_ledger_factory`'s `[fake]` branch now seeds the fake's agent table**
   (it previously seeded nothing, by design), which is what makes MP-7's parity legs meaningful.
   Measured blast radius: **zero pre-existing tests changed status** (§8).

---

## §1 — the seven pins, as built

| pin | class / test (`test_enforced_relations.py` unless noted) | kills | RED-on-wrong / GREEN-on-correct |
|---|---|---|---|
| **MP-1** | `TestTheLEDGERsOwnMigrationPathLandsTheGuard::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE` + `test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints` | **W-A** | W-A: `2 failed, 48 passed` (was `0 failed`) · correct: green |
| **MP-2a/b** | `TestTheSharedPolicyIsTheSOLEDecisionPoint::test_MUTATION_neutralising_the_shared_policy_lets_{publish,send}_reach_the_ENGINE` + `test_POSITIVE_CONTROL_the_neutralised_policy_still_lets_a_REGISTERED_publish_through` | **W-E**, **W-A** | W-E: `2 failed, 48 passed` (exactly these two) · correct: green |
| **MP-3** | `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row` + `test_POSITIVE_CONTROL_an_ACCEPTED_publish_DOES_create_the_counter_row` | **W-D** (publish) | W-D: RED · correct: green |
| **MP-4** | `…::test_a_refused_ack_never_ATTEMPTS_the_RELATE` + `test_POSITIVE_CONTROL_a_REGISTERED_agents_ack_DOES_reach_the_RELATE` | **W-D** (ack) | W-D: RED · correct: green |
| **MP-5** | `UNREGISTERED_AGENT_ID_WEARING_THE_REGISTERED_SHAPE` + the three parametrised negative legs | **W-B** | W-B: `3 failed, 47 passed`, all three the new param · correct: green |
| **MP-6** | `test_comms_tool.py::TestBriefPublishTeachesWhenTheAUTHORNamesNoAgentRow` (2 legs) | a seam that swallows/re-wraps the teaching error | HEAD: RED · correct: green |
| **MP-7** | `test_brief_ledger.py::TestTheFakeLedgerSharesTheUnknownAgentPolicy` (4 tests × `[real]`/`[fake]` + 1 fake-only bound pin = 7 node ids) | real/fake divergence on the headline property | HEAD: RED both backends · correct: green |

**Every one ships with its named POSITIVE CONTROL, and each control is load-bearing rather than
decoration** — MP-2's control also proves the accept-everything stub is INERT for legal input (so its
two reds are caused by the id, not by the patch); MP-4's control also proves the monkeypatch actually
attached (a run where it silently did not would otherwise pass MP-4 for a reason unrelated to the
property); MP-3's control proves the counter-row read can SEE a row at all.

**Both lead rulings, as implemented:**
- **RULING 1.** `type(a) is type(b)` → *"the two raised values share a base class whose `__module__` is
  `SHARED_POLICY_MODULE`"*. It admits the ruled shape (shared base + distinct subclasses) and the alias
  shape; it REFUSES a base owned by either ledger, which is §4.D4's layering (the W-G reading the ruling
  rejected). It needs no new name-keyed handle — the base is derived from the raised VALUES.
- **RULING 2.** §3.

---

## §2 — every RED at `369db57`, by reason (no red is a `TypeError` or a collection error)

```
14  Failed: DID NOT RAISE <class 'Exception'>              the live refusal/guard pins — the code runs and does the wrong thing
 3  AttributeError: loremaster.briefs has no attribute 'reject_unknown_agents'      monkeypatch(raising=True) failing CLOSED
 2  AttributeError: loremaster.messages has no attribute 'reject_unknown_agents'    ditto
 1  ModuleNotFoundError: No module named 'loremaster.agent_existence'               the contract-first absence, at CALL time (#133)
 6  AssertionError (the ∀ law · the per-edge slice · the old-world anti-vacuity ·
    the two import preconditions · MP-4's "the ack path ATTEMPTED the RELATE")
26  total
```
Outside the contract file: `test_brief_ledger.py` 2 (MP-7 `[real]` DID-NOT-RAISE, `[fake]` the shared
error base not yet importable) · `test_comms_tool.py` 1 (MP-6, same absence, surfaced through the
served-message assertion).

---

## §3 — RULING 2: the `_AckConnection` widening, and the proof it is still honest

**What was widened.** `_AckConnection.query` now serves ONE more shape: a `SELECT` whose **PARAMS bind
`agent`-table `RecordID`s**, answered from a modelled agent table (`registered_agent_ids`, default
`{_ACK_AGENT_ID}`), returning only the ids that EXIST — the engine's own direct-record-access
behaviour. Deny-by-default is preserved for everything else; the branch is **shape-keyed, never keyed
on one policy's SQL TEXT** (a literal-keyed instrument is the lesson this repo has lost six times).
Branch ORDER is load-bearing and commented: `_select_briefed_edge`'s SELECT also binds an agent
RecordID, so its own branch must be tried first — and a reordering is caught by
`test_a_UNIQUE_violation_still_reports_the_honest_idempotent_re_ack`.

**Proof it can still FAIL for its own reasons** — the mutation the five pins exist to catch is
removing `_relate_briefed`'s `except TxnContentionExhaustedError` guard (spelled as
`except TypeError:`, which never fires there). **Declared-RED set written to `/tmp/mp04a/declared.txt`
BEFORE the run, ids taken from `pytest --collect-only -q`, never transcribed from output:**

```
…::TestTheAckEdgeNeverReportsAnExhaustedRelateAsAReAck::test_exhausted_contention_on_the_ack_RELATE_raises_the_TYPED_error[A-RACERS-EDGE-IS-PRESENT-the-defect]
…::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_every_door_guards_the_typed_error_ABOVE_its_rollback_handler[briefs.py::_relate_briefed]
…::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::test_the_brief_ack_door
```

| run | result |
|---|---|
| at `369db57` (repo), suite before mutation | `503 passed` |
| at `369db57`, `mutation_proof.py` | **`EXIT=0` · `3 failed, 500 passed` · PROOF HELD, declared set fired EXACTLY · tree restored byte-exact (md5 `fdf34422c205b5e8a8d5081b33fcc6b9`)** |
| on the REFERENCE build (ack really does check), suite | `503 passed` |
| on the REFERENCE build, same proof | **`EXIT=0` · PROOF HELD, 3/3 · restored byte-exact (md5 `427eb43bf58b8a4072662b89f1f363e9`)** |

**REACH IS A CHECKED VARIABLE, not an assumption.** The HEAD run alone would prove only that the
widening broke nothing — at HEAD the new branch is never entered. The reference-build run enters it,
and I have direct evidence it does: before I fixed a bug in my own reference policy (§7.4), all five
pins failed with `UnknownBriefAgentError: unknown agent(s): contract-fix-1 (0199c4f1-…)`, an error
that can only be produced from data **this branch served**.

⚠ **My first attempt at this proof was a live #194** and the tool caught it, exactly as documented:
`anchor matched 0 times … NOTHING WAS MUTATED and no proof was run` (my anchor file carried a trailing
newline mid-line). Had I run the suite by hand in the next line of the same block, it would have
printed `503 passed` and read as a proof.

---

## §4 — C-DEF: the satisfiability receipt (and C-DEF-2 / C-DEF-3 CLOSED)

I built a reference implementation in the scratch tree (the only way to grade a contract), following
the adversary's §C-DEF recipe plus RULING 1's shape:

| file | change |
|---|---|
| `store/surreal_schema.py` | `_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)` |
| `agent_existence.py` (new) | `UnknownAgentError(RuntimeError)` + `async reject_unknown_agents(query, agents, *, error=UnknownAgentError)` — ONE direct-record-access read, names every missing `name (id)` |
| `briefs.py` | imports the shared symbol; `publish` calls it BEFORE `_mint_version`, `ack` BEFORE the versions read; `UnknownBriefAgentError(BriefLedgerError, UnknownAgentError)` |
| `messages.py` | imports it; `_reject_unknown_recipients`' body → one delegating call; `UnknownRecipientError(MessageLedgerError, UnknownAgentError)` |

```
$ cd /tmp/mp04a/ref && uv run pytest -q loremaster/tests/test_enforced_relations.py -p no:randomly -n auto
50 passed in 5.29s
$ uv run ruff check --fix .   -> Found 2 errors (2 fixed, 0 remaining);  ruff check . -> All checks passed!
$ ./scripts/typecheck.sh      -> lorescribe OK / loresigil OK / loremaster OK (156 files)
$ uv run pytest -q  test_enforced_relations test_brief_ledger test_comms_tool test_retry_seam \
      test_message_ledger test_comms_schema test_comms_render_architecture \
      test_comms_promise_registry test_comms_wiring  -p no:randomly -n auto
2189 passed, 14 skipped, 1 warning in 26.62s
$ uv run pytest -q test_agent_registry test_comms_fleet_grouping -n auto     ->  181 passed
```

- **C-DEF-2 (BLOCKING) is CLOSED.** The five `test_retry_seam.py` pins that the app-check-inside-`ack`
  broke now pass on a build that has that check — `503 passed` — because the fake models the agent
  table. This was the adversary's *"whether a build exists that is 0-failed REPO-WIDE"*, and the answer
  is now **yes, measured**, over nine suites and 2189 pins.
- **C-DEF-3 (BLOCKING) is CLOSED** by RULING 1: the ruled shape (shared base, distinct subclasses)
  satisfies 04a's re-shaped pin AND `test_message_ledger::TestVocabularies` simultaneously — the
  three-way fork had no such reading before the ruling, and this build demonstrates one.
- **The harder leg holds:** still `50 passed` after `ruff --fix`'s import-order cleanup.

---

## §5 — "what wrong build survives NOW?" — the four survivors, rebuilt and re-measured

Each was rebuilt ON the reference build in scratch, run against the REAL contract file unmodified, and
restored from a `cp -a` content backup with md5 verification (`briefs.py 427eb43b…` ·
`messages.py aff3d5c9…` · `agent_existence.py ea1b2dc3…` · `surreal_schema.py 86ba10f8…`).

| build | before (adversary, at `dfb5cd0`) | NOW | killed by |
|---|---|---|---|
| **W-A** `ensure_ready` applies a de-`ENFORCED` copy | **38/38 SURVIVES**, 0 new failures repo-wide | **`2 failed, 48 passed`** | MP-1 · MP-2a |
| **W-B** policy keyed on the one fixture literal, never queries the store | **38/38 SURVIVES** | **`3 failed, 47 passed`** | MP-5 ×3 (all three `[registered_agent_0…]` legs) |
| **W-D** checks AFTER the write, through the shared `except` | **38/38 SURVIVES**, greener repo-wide than correct | **`3 failed, 47 passed`** | MP-3 · MP-4 · (+ the pre-existing sharing mutation pin) |
| **W-E** routing-is-not-sharing (shared fn decides nothing; private copies underneath) | **38/38 SURVIVES + every neighbour** | **`2 failed, 48 passed`** | MP-2a · MP-2b — and ONLY those two, which is the design |

**What still survives, honestly:**
1. **A build that leaves the message SENDER unguarded** (adversary I13/R8). Unchanged, unruled, and I
   did not close it — see §7 (D-b). A `send` whose SENDER names no agent row still writes a
   message row with a ghost sender id.
2. **A build with a TOCTOU between the check and the write** (agent retired between the existence read
   and the RELATE). No pin here exercises the app check under contention; the adversary named this too
   and neither of us built it. Not closable by a contract pin alone — it needs a ≥8-way concurrency
   instrument and 20 consecutive green runs to mean anything.
3. **A build whose `FakeBriefLedger` is correct only where the agent table is modelled** — the declared
   bound, pinned with its re-open trigger (§7 D-c).
4. **A build that names the bad agent by NAME only, in the tool seam, for `brief_ack`.** MP-6 covers
   `brief_publish`; `brief_ack`'s tool seam has no equivalent teaching pin. I judged one enough for the
   packet's stated Exit criterion (which names publish/send) — flagging rather than deciding.

---

## §6 — the group-C mutation proof: EXECUTED, both ways, on the first tree where it can run

The declared set was **grown from six to eight before any run** (the file's `MUTATION_PROOF` block
records why), because two of my new pins depend on the engine clause: MP-1 is a MIGRATION pin, and
MP-2a's publish leg deliberately observes BOTH layers. The sentence *"the app-check pins are
deliberately NOT in the set"* was therefore CORRECTED in the same edit — leaving it would have made
the proof report two unexpected reds and invited a builder to "fix" the list.

```
$ ./scripts/mutation_proof.py --file loremaster/loremaster/store/surreal_schema.py \
    --anchor '…, enforced=True)' --replacement '…)' --expect-red ×8 -- uv run pytest -q $F -n auto
8 failed, 42 passed in 5.52s
tree restored byte-exact (surreal_schema.py: md5 86ba10f8d2a1b08369cc5d2f06d0ceea)
PROOF HELD — the declared RED set fired EXACTLY  ·  EXIT=0
```

**No unexpected reds and no declared-red stayed GREEN** — so the two ADDED predictions were right, and
every other app-check pin (the refusal, the naming, the counter row, the RELATE sentinel, the second
identity, the common-base pin, MP-2b, all three positive controls) stayed independent of the engine
clause, which is the property §S4 demanded.

---

## §7 — escalations and hand-offs (scope belongs to the operator)

**D-a — ⚠ NAME COLLISION: `UnknownAgentError` already exists in this package.**
`loremaster.agents.UnknownAgentError` means *"this display NAME resolves to no agent at the REGISTRY"*
and is imported by `_comms_fakes.py` and `test_comms_tool.py` today. The shared policy's base means
*"this row ID names no `agent` row at the LEDGER"* — a different error with the same obvious name. The
contract does NOT pin the class's name (deliberately: the base is derived from raised values), so this
is a builder-facing fork: **pick a distinguishing name (`UnknownAgentRowError`, `AgentNotRegisteredError`)
or accept the collision and alias at every import site.** My recommendation: distinguish it — two
same-named exceptions in one package is precisely the confusion a teaching error is supposed to remove.

**D-b — the SENDER door (adversary R8/I13) is still open and still unruled.** 04a's Exit criterion
names recipients; a `send` whose SENDER is a ghost id is the same #105 outcome through a different
door. I did NOT pin it: closing it would widen the ruled scope, and *"the operator decides"*. **Fix
now vs defer — lead/operator call**; if deferred it needs a finding number and a named trigger, or it
is a can-kick.

**D-c — the fake's DECLARED BOUND.** `FakeBriefLedger` refuses an unknown id only when its agent table
is MODELLED (non-empty); an empty table accepts everything. The alternative — unconditional strictness —
costs a `register_agent` call at each of the ~55 `brief_publish`/`brief_ack` tool-seam sites in `test_comms_tool.py` **and 3 in
`test_comms_render_architecture.py`, which is OUTSIDE 04a's writable set** (the exact edit: give its
`_harness()` a `brief_ledger.register_agent(agent_id=…, name=…)` after each registry registration).
Shipping that would have created a second D1-shaped structural contradiction, so I pinned the bound
instead — `TestTheFakeLedgerSharesTheUnknownAgentPolicy::test_the_UNMODELLED_agent_table_is_a_DECLARED_BOUND`
goes RED the day someone closes it, carrying the "if you closed it deliberately, delete this pin" message.
**Named re-open trigger:** the day the brief tool-seam harness seeds the fake's agent table wholesale.

**D-d — two findings the BUILDER needs, from building the reference implementation (not opinions —
both cost me a red suite):**
1. **The shared policy must derive bare ids the way the ledgers already do** (`MessageLedger._bare_id`:
   `str(record.id)` for a `RecordID`). My first version used `str(row["id"]).split(":", 1)[-1]`, which
   is correct for `agent:abc` and WRONG for a uuid-shaped id, because the SDK renders it
   `agent:⟨0199c4f1-7d2a-…⟩`. Effect: every id looked unknown → **130 red pins across
   `test_message_ledger.py` + `test_brief_ledger.py`**, none of them in 04a's own file. A builder who
   hand-rolls that parse will meet the same wall.
2. **The shared refusal message must carry BOTH the NAME and the ID** (adversary P6b item b): 04a pins
   the ID, `test_message_ledger::test_an_unregistered_recipient_is_rejected_by_name` pins the NAME.
   `f"{name} ({id})"` satisfies both — measured, `2189 passed`.

---

## §8 — residuals fixed, each with its receipt

- **R4 — the D1 sweep floor said `>= 5` while its message said SIX.** A builder site could be DELETED
  with the gate green. Fixed: `_REAL_LEDGER_BUILDER_FLOOR = 6`, and the message now READS that constant,
  so the number and the prose come from one place. **Re-derived, not typed:** an independent AST pass
  over `test_brief_ledger.py` names exactly six real-ledger builders (`brief_ledger_factory`,
  `TestPublishSelfAckIsWrittenInTheSameTransaction._real_ledger`,
  `TestCoverageQueryCountIsBounded._coverage_query_count`,
  `TestAckedVersionsForIdsQueryCountIsBounded._query_count`,
  `TestBriefLedgerConnectionLifecycle.test_recovers_on_the_next_call_after_a_dropped_connection`,
  `TestSubscribedNameSkewQueryPlans.test_acked_by_id_fetch_is_direct_record_access_not_a_brief_tablescan`).
  Gate re-run: `2 passed`.
- **R6 — `_seed_agent_rows`' docstring said "Three call sites"; there are six.** Fixed, and the
  hand-list of names is GONE: the docstring now points at `_REAL_LEDGER_BUILDER_FLOOR` and at the
  derived coverage gate, because a hand-list beside a derived gate goes stale silently. **⚠ I found a
  SECOND instance the adversary's R6 did not name:** the section banner above that gate said *"FIVE
  call sites … the last four … the sixth site"*. Same defect, same file, three sentences long. Fixed
  and annotated.
- **R7 — the predecessor report's SUMMARY BLOCK said 60 pins / 26 failed.** Corrected by an APPENDED
  §S8 note (never a rewrite — §1–§7 are cited from the INDEX Log and commits), carrying the re-derived
  current figures.
- **§5 item 7's FALSE claim** (*"pins sameness, not identity"*) — corrected in the same §S8 note, with
  the measurement (W-F: `1 failed, 249 passed`) and the ruling that resolves it.
- **Not mine, unchanged, and re-stated so nobody inherits them wrongly:** R3 (the exemption guard lives
  in `test_derivation_source_unification.py` — **the wave gate must run that file**; it is green here,
  `7 passed, 19 skipped`, included in my 13-suite run) · R5 (the sweep's `{"BriefLedger","make_env"}`
  reach, with its named re-open trigger) · R9/R10/R11 (low-risk, named) · R12 (#105's own text — a
  lead/brief item) · R13 (the adversary's own scratch-path artifact; **I did not reproduce it** —
  `test_logging_setup` was not in my scoped set).

---

## §9 — WHAT I COULD NOT DETERMINE

1. **Whether the FULL suite is 0-failed on a reference build.** I ran ELEVEN suites (2370 pins) in the
   scratch tree, not the whole repo — repo law reserves the full run for the lead at a phase
   checkpoint, and my brief scoped me. The nine 04a-adjacent suites plus the two extra `_comms_fakes`
   importers are green; anything outside that set is UNMEASURED by me.
2. **Whether my reference build is the build 04a should ship.** It is a grading instrument, not a
   design. In particular `reject_unknown_agents(…, *, error=…)` is ONE way to keep the decision shared
   while both verbs raise their own subclass; a builder may find a better shape, and the contract
   admits any shape that satisfies the common-base pin plus MP-2a/b.
3. **The SENDER door's blast radius** (D-b). I did not re-measure the adversary's I13 door-build; I
   inherited its result and state it as inherited. My reference build does not check senders either, so
   the door is unchanged rather than re-derived.
4. **Concurrency.** No pin here exercises the app check at ≥8-way, and `publish`'s check-then-mint
   window is a genuine TOCTOU against agent retirement. Unmeasured, and a contract pin is the wrong
   instrument for it (20 consecutive green runs, per repo law).
5. **Whether MP-6's fixture shape is the one the operator wants.** It models "the registry knows this
   agent, the ledger's agent table does not" — the only world in which the SEAM's behaviour is
   observable on a fake. In production both read one `agent` table, so this world is reachable only via
   a retired/hard-deleted row or a partial write. If the lead considers that world out of scope, MP-6
   should be re-shaped rather than deleted: the property (the seam does not swallow the teaching error)
   is what the Exit criterion actually claims.
6. **The cost of `ENFORCED` on 3.2.1** — unchanged from my predecessor's §6.6: unmeasured, and I am
   not asserting it is free.
