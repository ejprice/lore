# REPORT-builder-c1-1 — the BUILD for contract **C1**, the task read surface (04b-2 wave C)

brief-base v9 read
brief project v7 read

## SUMMARY BLOCK

- **state: done-with-deviations.** Contract C1 goes **90 passed / 0 failed** (RED→GREEN
  from a measured **63 failed / 27 passed** baseline at `54a29dd`, first implementation
  attempt, zero contract edits). Production code written in exactly two files:
  `loremaster/loremaster/tasks.py` and `loremaster/loremaster/server.py`.
- **capability check (brief-base §4): no gap.** Every tool, path, binary and service the
  brief names was reachable — lore MCP, the spike-surreal test store, `scripts/typecheck.sh`,
  `scripts/pending_contract_gate.py`, `scripts/mutation_proof.py`. Nothing was skipped for
  want of a tool. I spawned no subagents (prompt-level instruction).
- **deviations (3, each in §5):** (1) I corrected a **served-prose falsehood** in the
  registered `lore_tasks` `limit` parameter description — it claimed *"For 'rollup' ONLY
  (rejected for every other action)"* while `query` has accepted `limit` since ruling R9,
  and it sits in the parameter block this slice edits; pinned by nothing. (2)
  `TaskLedger.direct_dependents` narrows **store-side** rather than reusing
  `_read_dependency_graph`'s whole-graph read — reuse considered, argued, probed. (3)
  `claim_task` now buys **one extra read on a BLOCKED loss only**.
- **Packages considered:** *"has-more" pagination over the store read* → **bespoke**
  (READ, this venv, 2026-08-02: `dir(AsyncWsSurrealConnection)` = 39 members, **zero**
  matching `page|cursor|limit|offset|paginat|skip|start` — the SDK exposes raw SurrealQL
  only, so `LIMIT cap+1` in our own statement builder IS the whole mechanism;
  re-derived rather than inherited from the contract author's identical finding) ·
  *backtick-fence wrap for a new stored-free-text render* → **replace, in-repo**
  (READ: `loremaster.render.render_fenced` source — it already carries the `Rendered`
  type discipline, the width rule, and its own contract class; nothing minted) ·
  *cap validation shared between two seams* → **replace, in-repo** (`validated_task_limit`,
  promoted out of `TaskLedger._validated_limit` per the build spec) · *array-containment
  predicate* → **replace, engine-native** (SurrealQL `CONTAINS`; READ store reference §2
  *"Indexing an ARRAY column"*, then **PROBED** — instrument pasted verbatim in §4.1).
- **decisions-needed (2):** §5.1's served-prose correction (confirm or revert — it is a
  one-line behaviour-free edit outside the contract's ask), and §6.2's **provenance flag**:
  the two `test_blocks_edge.py` adjudication edits the contract assigned to me were swept
  into a **C3 commit** (`b40e84d`/`58f2786`) rather than landing with this build.
- **receipt pointers:** §1 what I built and why each choice · §2 gate results with scopes
  and passed-COUNTs · §3 the 634 full-suite failures DECOMPOSED (444 + 190, zero mine) ·
  §4 probes and mutation proofs, declared-before-run · §5 deviations · §6 flagged, not
  buried · §7 what the surfaces actually serve.

---

# §1 · WHAT I BUILT, AND WHY EACH CHOICE

*All claims measured 2026-08-02 against `feat/surreal-unification`; the baseline was
`54a29dd`, and HEAD moved to `58f2786` mid-run (§6.1).*

## 1.1 `loremaster/loremaster/tasks.py`

| symbol | what it is, and the decision inside it |
|---|---|
| `TaskListing` | pydantic, `extra="forbid"`, exactly `rows` + `more`. Field set CLOSED deny-by-default; the docstring carries the derivation the contract requires (*a count field acquires the failed-count construction first; a number-free wrapper acquires none of it, because the existence bit rides the SAME read as the rows*). |
| `validated_task_limit` | the cap predicate promoted to module level (#310). `TaskLedger._validated_limit` now **delegates** and carries no rule of its own. The delegation is by **module-global name**, so a monkeypatch of `tasks.validated_task_limit` is observed at BOTH call sites — which is what makes the contract's call-recorder able to tell one implementation from two that agree. |
| `ClaimResult.superseded_blockers` | `dict[str, str]`, **defaulted** — a required field would be a `TypeError` at every existing construction site on an otherwise-correct build (the C-DEF class). |
| `TaskLedger.direct_dependents` | the one-hop read R10(iii)'s supersede warning rides. One hop deliberately: the CAS that strands them is itself one-hop, so a transitive answer would name rows the supersession did not strand. |
| `TaskLedger._superseded_among` | maps the superseded members of a `blocked_by` list to their successors. **Short-circuits on empty input** — an unblocked loss must not buy a round trip to learn nothing. |
| `TaskLedger.claim_task` | populates `superseded_blockers` **only on a loss that has blockers**. |

## 1.2 `loremaster/loremaster/server.py`

**ESC-5, the deploy entry condition.** `AppContext._task_listing` is the ONE
implementation of the over-fetch: with a cap it asks the ledger for `limit + 1`, serves at
most `limit`, and sets `more` from whether the extra row came back; with no cap it asks
for none and `more` is always `False`. Three orderings inside it are load-bearing and each
is stated in the docstring rather than left to be rediscovered:

1. **The CALLER's cap is validated FIRST.** Adding one before validating destroys all
   three of the ledger's refusals silently — `-1` reaches it as `0` and is refused naming a
   number the caller never passed; `0` becomes a legal `LIMIT 1`, turning a refusal into
   one served row; `True` becomes `LIMIT 2`, bypassing the guard that exists precisely to
   stop `bool` meaning a cap.
2. **Both seams call the SHARED predicate**, so *"what counts as a legal cap?"* has one
   answer rather than two that agree today. Proven by mutation, not by inspection (§4.2).
3. **No cap ⇒ no clause**, because `LIMIT $k` with `$k = NONE` returns ZERO rows and NO
   error on 3.2.1.

**The dispatcher routes EVERY filter combination through that one helper.** This is the
half two consecutive adversary passes defeated (through `blocked`, then through `status`),
and it is why the query branch is a single call rather than a per-branch decision: a
dispatcher that sent only some spellings through the helper would serve an honest bound on
one phrasing of a question and the false clear on another.

**`_render_task_listing`** takes `listing.more` as typed applicability and never re-derives
it; the disclosure is strictly ADDITIVE (a render that swapped one sentence for another
would make the two worlds differ without either being a bound), and the NUMBER it names is
derived from the rows actually served — so it is a fact about *this* answer rather than a
literal that is right only for whichever cap the author happened to test.

**`_render_transitive_blockers`** — ID-only, proximity-ordered, and honest at **both** its
bounds: the measured `truncated` flag with its concrete depth, and the RESIDUE (`blocked_by`
entries carrying no `blocks` edge, which `ENFORCED` guarantees the backfill can never mint
and which the claim CAS counts forever). Every line rides a TRUE verdict — the follow-up
affordance is emitted only when there is an id to resolve, the residue notice only when the
column and the walk actually disagree — and the follow-up names `action=get`, a verb that
now exists, so it is not a fabricated affordance.

**`_render_task_detail`** (`action=get`) — the archetype verbatim: the BODY is FENCED
through `render.render_fenced`, the single-line trailers are SANITISED.

**`_render_supersede_result`** — NAMES the stranded dependents (the caller's next move
cannot be made from a number), WARNS rather than rewrites (transfer is R10(iv), deferred),
and fires only when something was actually stranded.

**`_render_claim_result`** gains the superseded-blocker branch, ordered AFTER the task's own
`superseded_by` check so finding #7's pre-existing branch is untouched.

**`_render_finding_detail`'s inline fence MIGRATED onto `render_fenced`** (Ruling 9 item 3),
and the now-orphaned `_max_backtick_run` import was deleted with it — leaving it would have
been the `F401` the contract author predicted.

**The trap the contract warned me about, met exactly as described:** `AppContext.tasks`
crosses ruff's branch cap at 13 > 12 once it gains two actions. Resolved the way that
function already resolves the identical complaint about its return count — the existing
`# noqa: PLR0911` became `# noqa: PLR0911,PLR0912`, same rationale, same line.

**The registered MCP tool** (a DIFFERENT function from `AppContext.tasks`) gains `max_depth`
in its explicit parameter list, **forwards it**, and its served text now names `blockers`
and `get` in the top-level summary AND in the `action` parameter's quoted enumeration.

---

# §2 · GATES — EACH SCOPED, NO UNQUALIFIED GREEN CLAIM

| gate | scope | result |
|---|---|---|
| `pytest` | `test_task_read_surface.py` (the contract) | **90 passed / 0 failed** in 6.99s |
| `pytest -n auto` | contract + `query_tasks_bounded` + `blocks_edge` + `task_ledger` + `mcp_server` + `txn_contention` + `findings` + `render` + `render_seam_pins` + `sanitise` + `search` | **1595 passed, 3 xfailed** in 120.89s |
| `pytest -n auto` | contract + `query_tasks_bounded` + `blocks_edge` + `mcp_server` + `findings`, re-run AFTER both mutation proofs restored the tree | **1130 passed / 0 failed** in 123.92s |
| `uv run ruff check .` | whole repo | **All checks passed!** — zero errors, mine or otherwise |
| `./scripts/typecheck.sh` | whole repo | 114 errors in 9 files — **not one of them in a file I touched** (per-file counts in §3.2) |
| `scripts/pending_contract_gate.py --currency` | manifest `(typecheck, ruff, pytest)` | `ruff` **GREEN**; `typecheck` **RED_ORPHANED** (12 residuals) and `pytest` **RED_ORPHANED** (190) — **202 orphans, of which 200 are C3's `test_comms_footer.py` and 2 are `test_comms_tool.py`**, a live agent's contract-first files. Zero orphans mine. |
| `pytest -n auto` | **FULL SUITE** | **8888 passed, 634 failed, 36 skipped, 3 xfailed** in 327.52s — decomposed in §3.1 |

⚠ **The currency gate FAILS, and it is not mine to clear.** Its own output says so:
*"RED with nobody's name on it: typecheck, pytest"* — the unowned residuals are C3's
designed-RED pins, which have no `scripts/pending_contracts.yaml` adjudication yet. That is
a wave-close-out item for the lead, and it is the instrument doing its job.

---

# §3 · THE 634 FULL-SUITE FAILURES, DECOMPOSED RATHER THAN WAVED AT

## 3.1 Derived by file, not asserted

```
188 loremaster/tests/test_comms_footer.py        ┐
  2 loremaster/tests/test_comms_tool.py          ┘ = 190  C3, live agent, my brief's do-not-touch list

 81 loremaster/tests/test_auth_composition.py    ┐
 75 loremaster/tests/test_google_token_verifier.py
 70 lorerunes/tests/test_posture.py              │
 57 loremaster/tests/test_hosted_readonly_posture.py
 46 loremaster/tests/test_allowlist_roster.py    ├ = 444  packet 39's deliberately-unbuilt
 37 lorerunes/tests/test_roster_parser.py        │        contract (#296 operator-held, #306/#307)
 25 loremaster/tests/test_auth.py                │
 21 lorerunes/tests/test_email_normalisation.py  │
 18 loremaster/tests/test_auth_identity_seam.py  │
 14 loremaster/tests/test_permission_resolver_seam.py ┘
```

**444 + 190 = 634**, exactly. The 444 independently reproduces the INDEX row the design
sidecar quotes for packet 39 (*"480 pins / 444 RED / 36 GREEN"*) — I did not take that
number on faith; it fell out of a `uniq -c` over my own run. **Zero failures anywhere in
the tree are attributable to this slice.**

⚠ Scope of that claim, stated: the 190 is a **snapshot**. C3's agent was editing
`test_comms_footer.py` while I measured (it shows ` M` in `git status`), so its count is a
moving target — the load-bearing half is the FILE SET, which contains nothing of mine.

## 3.2 Typecheck, per file — the same discipline

```
40 test_auth_composition · 36 test_roster_parser · 35 test_posture · 20 test_permission_resolver_seam
18 test_email_normalisation · 13 test_hosted_readonly_posture · 12 test_comms_footer
10 test_allowlist_roster · 7 test_google_token_verifier · 7 test_auth · 3 _auth_fixtures
2 test_auth_identity_seam
```

`server.py`, `tasks.py`, `test_blocks_edge.py` and all three contract files: **absent from
that list entirely**, i.e. zero errors each.

---

# §4 · WHAT I MEASURED, AND THE INSTRUMENTS THAT MEASURED IT

## 4.1 The store predicate — READ THE DOCS, THEN VERIFY THEM

`direct_dependents` needed *"which rows' `blocked_by` array names this id"*. Store reference
§2 (*"Indexing an ARRAY column"*) names the containment spellings **and** names the trap:
`WHERE <array> = 'x'` **IndexScans and returns `[]`** — fast, silent, wrong. So I read it,
then probed it with a positive control rather than trusting either the doc or my instinct.
**The instrument is a deliverable, so here it is verbatim** (it is not committed — it is a
one-shot settling one predicate choice, and per brief-base §4 that makes it a paste, not a
`scripts/` entry):

```python
"""PROBE: does `array<string> CONTAINS $bound` select rows on 3.2.1, under the
project's real `task` schema, and does it agree with a client-side filter?
Run against spike-surreal (ws://127.0.0.1:18000 — the TEST store)."""
import asyncio, sys, uuid
sys.path.insert(0, "loremaster"); sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, unique_database, drop_database, PRODUCTION_DIM
from loremaster.tasks import TaskLedger

async def main() -> None:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database,
                        user=env.user, password=env.password)
    await ledger.ensure_ready()
    try:
        target = await ledger.create_task("target", "d", created_by="probe")
        other = await ledger.create_task("other", "d", created_by="probe")
        dep_a = await ledger.create_task("dep a", "d", blocked_by=[target], created_by="probe")
        dep_b = await ledger.create_task("dep b", "d", blocked_by=[target, other], created_by="probe")
        await ledger.create_task("unrelated", "d", blocked_by=[other], created_by="probe")
        await ledger.create_task("free", "d", created_by="probe")
        expected = sorted([dep_a, dep_b])
        for label, clause in (
            ("CONTAINS", "blocked_by CONTAINS $dep_task_id"),
            ("IN", "$dep_task_id IN blocked_by"),
        ):
            try:
                rows = ledger._as_rows(await ledger._query(
                    f"SELECT record::id(id) AS id FROM task WHERE {clause}",
                    {"dep_task_id": target},
                ))
                got = sorted(str(r.get("id")) for r in rows)
                print(f"{label:10} -> {len(got)} rows, correct={got == expected}")
            except Exception as error:  # noqa: BLE001
                print(f"{label:10} -> RAISED {type(error).__name__}: {error}")
        # CONTROL: a value nothing names must select NOTHING (not everything).
        rows = ledger._as_rows(await ledger._query(
            "SELECT record::id(id) AS id FROM task WHERE blocked_by CONTAINS $dep_task_id",
            {"dep_task_id": uuid.uuid4().hex},
        ))
        print(f"{'CONTROL':10} -> {len(rows)} rows for an id nothing names (want 0)")
    finally:
        await ledger.close(); await drop_database(env)

asyncio.run(main())
```

```
CONTAINS   -> 2 rows, correct=True
IN         -> 2 rows, correct=True
CONTROL    -> 0 rows for an id nothing names (want 0)
```

The control is the half that matters: 2-of-6 with the right two, and **0** for an id nothing
names, so the predicate is not quietly matching everything. `CONTAINS` chosen (the
vendor-documented spelling our own reference names); the rationale and the silently-wrong
alternative are recorded at `_DEPENDENTS_ID_PARAM` so the next author meets them deliberately.

## 4.2 Mutation proofs — declared BEFORE each run, diffed BOTH ways

Run through `scripts/mutation_proof.py` (which fails on unexpected reds **and** on declared
reds that stayed green), against the REAL tree with a `cp -a` content backup — the sanctioned
alternative to a scratch copy — and the declared node ids taken from `pytest --collect-only`,
never transcribed from output.

| # | mutation (a plausible WRONG build my own code could have been) | declared | observed |
|---|---|---|---|
| **M1** | `_task_listing` validates with a **private copy** of the cap rule instead of the shared predicate — same rules, so every behavioural pin stays green | 1 | `1 failed, 89 passed` — **PROOF HELD**, fired exactly |
| **M2** | `_render_task_detail` **hand-rolls its fence** as a bare backtick literal instead of calling `render_fenced` | 3 | `3 failed, 87 passed` — **PROOF HELD**, fired exactly |

M2 is the load-bearing one: the derived fence-site scan named a door it was never told
about — `server.py:3771 — a bare backtick-run literal` — which is the property a name-keyed
falsifier could not have had. Both runs restored the tree byte-exact
(`md5 8e180fe0c4afb5408ef0d2f86d61d4d8` before and after each, and a final `diff -q` against
the pre-mutation `cp -a` backup).

## 4.3 Provenance (#140)

```
loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
```

No scratch copy was used: I built in the real tree, and the only mutations were the two
above, each content-backed-up and restored byte-exact. Stated rather than implied, because
*"I tested it"* is a verdict about a TREE.

---

# §5 · DEVIATIONS

## 5.1 ⚠ A SERVED-PROSE FALSEHOOD, CORRECTED — the one edit outside what the contract asked for

At `54a29dd` the registered `lore_tasks` tool's `limit` parameter description read:

> *"For 'rollup' ONLY (rejected for every other action): the per-leg row cap …"*

**That has been false since operator ruling R9** (packet 04b-1), which put `query` into
`_TASK_ACTIONS_ACCEPTING_LIMIT`. It is exactly this repo's most-documented defect class —
served English whose consistency with code no gate checks — and it was pinned by nothing
(`grep` over the test tree: no assertion touches that string). It is also directly about the
surface this slice ships: an agent reading it concludes `action=query limit=N` is rejected,
which is the whole affordance ESC-5 exists to make honest.

I rewrote it to name both actions and to state what the cap does on each. **This is a
deviation** — a behaviour-free served-text correction the contract did not ask for, in a
parameter block I was already editing. It is trivially revertible; the alternative was to
ship a new disclosure surface underneath a sentence telling agents not to use it.

**Not fixed, flagged instead (§6.3):** whether the same class exists in the other tool
descriptions. I did not sweep, because that is scope I do not own.

## 5.2 `direct_dependents` narrows STORE-SIDE rather than reusing `_read_dependency_graph`

brief-base §6 says search for the existing thing first, so: `_read_dependency_graph` **can**
answer this question — it reads every dependency-bearing row and I could filter client-side.
I did not reuse it, and the reason is that the two are not the same policy wearing two names:
it answers *"the whole `blocked_by` graph"* (for cycle detection, where the whole graph is
genuinely needed), and this answers *"who names this id"*. Routing the second through the
first would ship every dependency-bearing row over the wire on every supersede, so the
payload scales with the BACKLOG rather than with the ANSWER — #253's own property, on the
write path. **This is duplication of a QUESTION, not of a POLICY**: there is no shared rule
that could drift between them. Disclosed because "I chose not to reuse" is a design decision
and the operator owns those.

## 5.3 `claim_task` buys ONE extra read on a BLOCKED loss

The superseded-blocker fact is TYPED STATE on `ClaimResult` (the contract requires it: the
render is a pure staticmethod, and a render-side store read would be a second implementation
of the blocker policy that every non-MCP consumer would miss). So the ledger reads it — but
only when the claim LOST **and** the row has blockers. A win costs nothing extra; an
already-owned or wrong-status loss costs nothing extra. No round-trip pin covers `claim_task`
(I checked: the `measure_store_traffic` pins cover `create_task`, `transitive_blockers`,
`ensure_ready` and the query paths), so this is a new cost nothing was measuring — which is
precisely why it is written down here rather than left to be discovered.

---

# §6 · FLAGGED — NOTICED, NOT MINE TO DECIDE, NOT BURIED

## 6.1 HEAD moved under me, mid-build

I started at `54a29dd` and finished at `58f2786` — two C3 commits (`b40e84d`,
`58f2786`) landed while I was building. Nothing broke, and my final scoped re-run
(1130 passed) is post-move. Recorded because every number in this report is dated to the
tree it was measured on, and that tree changed once.

## 6.2 ⚠ My `test_blocks_edge.py` adjudication edits were swept into a C3 commit

The contract assigned me two one-line edits (`NON_WRITING_VERBS` and
`VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH` each gain `"direct_dependents"`, with the
adjudication recorded as a comment beside each so an omission and a decision cannot look
alike). I made them. They are now **at HEAD, inside a C3 commit** — `git status` no longer
shows the file as modified, and `git show HEAD:…test_blocks_edge.py | grep -c direct_dependents`
returns **4**.

I ran no git write command (my brief forbids it). So a `-a`/`add -A` commit for C3 collected
C1's uncommitted edits as a side effect. **Consequence for the lead:** the C1 build commit
will not contain the two edits that make it green, and the C3 commit contains a change whose
message says nothing about it — one-concern-per-commit, breached invisibly. Nothing needs
re-doing; the lead may want to note it in the wave close-out so the provenance is not lost.

## 6.3 The residual-gap class `_render_claim_result`'s own docstring already names

That docstring records that the BLOCKED/UNOWNED branch interpolates `blocked_by`/`status`
without a wrap, flagged as *"a residual gap for the PKT-03 tree-wide sweep"*. **My new
superseded-blocker branch is in that same branch and inherits the same residual** — it
interpolates opaque store-minted ids (a `blocked_by` entry and a `superseded_by` stamp),
which are not agent free text, but they are unwrapped for the same reason the neighbouring
line is. I did not widen the sweep's scope unilaterally. If PKT-03 lands, this branch is one
more site for it.

## 6.4 The currency gate's orphans are C3's, and they need an adjudication row

`scripts/pending_contract_gate.py --currency` exits 1 with 12 typecheck and 190 pytest
orphans — 202 in total, 200 in `test_comms_footer.py` and 2 in `test_comms_tool.py`, derived
by `uniq -c` over its own output rather than eyeballed. Under Ruling 7 the invariant is
ADJUDICATION, not greenness — so these want a `scripts/pending_contracts.yaml` entry naming
C3 as owner with its build as the trigger, exactly as packet 39's red already has. Not mine
to write (I do not own those files or that registry row), but it will block any close-out
that requires currency to pass.

---

# §7 · WHAT THE SURFACES ACTUALLY SERVE

The consumer of every one of these is an agent, so the acceptance question is what it reads.
Rendered live against the test store, 2026-08-02 (ids are real, from a throwaway database):

```
=== action=query limit=3 (CAPPED) ===
- [open] backlog item 4 (id 15e76b566bbd49b898081431dabca90b, owner None, blocked_by [])
- [open] backlog item 8 (id 2e0eb1a244254bc58e42ef7efd75b8f9, owner None, blocked_by [])
- [open] backlog item 6 (id 3be9e44144094d1aa1f80c158ec627f8, owner None, blocked_by [])
showing 3 matching task(s) — MORE MATCH than were served: re-run with a larger limit, or narrow with status/owner/blocked

=== action=blockers max_depth=2 (TRUNCATED) ===
critical path for task b6a2c5e7681a4f61ad5ef6afb8617dd4:
  1. e364a0fe984148949d80799f5bd3b125
  2. ab481f87dc7e4274aa1886d478608fb7
  ⚠ the walk STOPPED at max_depth=2 and more upstream is still reachable — this is a FLOOR; re-run with a larger max_depth
  ↳ read any of these with: lore_tasks action=get task_id=e364a0fe984148949d80799f5bd3b125

=== action=supersede (STRANDS a dependent) ===
superseded task 0ac0ae7cbf7e4a16ae17dc2c1e662b70; successor 5395e22d4e78485ca5723ec5f8f6bf44 (status open)
⚠ 1 task(s) blocked on 0ac0ae7cbf7e4a16ae17dc2c1e662b70 are now STRANDED — it can never resolve, so they can never become claimable: re-point them at 5395e22d4e78485ca5723ec5f8f6bf44: ['d90808faa5d64010b4a3bed6f66bed7b']

=== lore_claim_task on the stranded dependent ===
not claimed: task d90808faa5d64010b4a3bed6f66bed7b is unowned but not claimable (blocked_by ['0ac0ae7cbf7e4a16ae17dc2c1e662b70'] unresolved, and 0ac0ae7cbf7e4a16ae17dc2c1e662b70 → 5395e22d4e78485ca5723ec5f8f6bf44 — a SUPERSEDED blocker can never resolve, so this claim can never win: block on the successor instead)
```

The chain closes: a supersede names what it stranded → the claim refusal on a stranded task
names the successor instead of inviting a forever-poll → and every opaque id any of them
hands out is now resolvable with `action=get`, which is the verb finding #89's author did not
have when they read a task description with a raw SELECT against production.

---

# §8 · WHAT I DID NOT DO

- **No contract file was edited.** `test_task_read_surface.py`, `test_query_tasks_bounded.py`
  and `_task_fakes.py` are byte-unchanged; the only test-tree edit is the two lines
  `test_blocks_edge.py` the contract explicitly assigned me (§6.2).
- **`search.py` and `sanitise.py` were never opened for editing** (Ruling 9 item 3 fences
  them to 04b-3). The dated exemption `_FENCE_SITE_EXEMPTION = "search.py"` is still USED, so
  its self-destructing pin still has its premise — verified green, and it is what will go RED
  the day 04b-3 unifies the width rule.
- **No packet-39 file was touched** (operator-held behind #296), and no `scripts/**` file.
- **No git write command was run.** The lead commits.
- **No subagents were spawned** (prompt-level instruction).
- I did not sweep the other tool descriptions for §5.1's defect class, and did not file a
  `lore_findings` row for it — both are scope calls I am raising rather than taking.

---

*Written 2026-08-02 by `builder-c1-1` (Opus) against `feat/surreal-unification`. Baseline
`54a29dd`, finished at `58f2786`. Every number was derived this session by the command shown
beside it; nothing is inherited, including the SDK-pagination survey and packet 39's 444,
both of which I re-derived rather than quote. Files modified: `loremaster/loremaster/tasks.py`,
`loremaster/loremaster/server.py`, and `loremaster/tests/test_blocks_edge.py` (the two assigned
adjudication lines).*
