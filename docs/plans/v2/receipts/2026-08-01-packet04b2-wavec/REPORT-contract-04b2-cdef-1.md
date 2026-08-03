# REPORT-contract-04b2-cdef-1 — the C3 contract's C-DEF fixture gap, closed and proven non-vacuous

brief-base v10 read
brief project v7 read

- **state**: done-with-deviations
- **deviation 1 (PROMINENT)**: the brief's CONTINGENT clause FIRED and I took it —
  `loremaster/tests/_task_fakes.py` gained `FakeTaskLedger.transitive_blockers` (+ a private
  `_upstream_reach`). Both preconditions were MEASURED, not assumed (§3). Details + bounds: §4.
- **deviation 2**: one line of the fixture helper that I did **not** add was removed —
  `_task_action_kwargs`' explicit `if action == "rollup": return {}`, folded into the identical
  bare fall-through, because my seventh return tripped `ruff PLR0911`. Behaviour-identical; the
  decision it recorded is preserved as a comment. §5.
- **Packages considered**: `FakeTaskLedger._upstream_reach` (bounded upstream graph walk) —
  evaluated `networkx` 3.6.1 (a DECLARED direct dep of `loremaster`, operator-authorised at
  `54d0585`) and stdlib `graphlib`; READ `nx.bfs_tree` / `nx.descendants_at_distance` signatures
  and RAN a 3-cycle probe (§6, verbatim); verdict **bespoke** — measured, not asserted.
- **Graded**: `cbe19824074094dc544efe8c82763e007b3b0aea` · HEAD-at-report:
  `cbe19824074094dc544efe8c82763e007b3b0aea` · **SAME**. `loremaster/loremaster/server.py` is
  byte-identical to that commit at report time (`git status` names only the two test files).
- **decisions-needed**: ONE — this is the **second** instance of one defect class in this contract
  (C-DEF 2 repaired `_finding_action_kwargs`; C-DEF 3 is `_task_action_kwargs`). I did **not** build
  the invariant, because it is beyond *"strictly needed to drive get/blockers"* and a new pin in a
  contract mid-wave has not met the adversary. Proposed shape in §8 — **lead's call**.
- **receipt pointers**: §2 red-before · §3 the two-stage measurement · §5 `225 passed / 0 failed` ·
  §5.2 ripple `1297 passed` · §7 **PROOF HELD**, declared set fired EXACTLY · §9 gate currency.

---

## 1. Capability check (brief-base §4)

Everything the brief demanded was reachable: `Read`/`Edit`/`Bash`, the lore MCP surface (loaded with
the keyword form `ToolSearch "+lore"`, 15 tools), `scripts/mutation_proof.py`, and the live TEST
store `spike-surreal` (`systemctl --user is-active spike-surreal.service` → `active`). **No demand
was unmeetable, and nothing was skipped for a tooling reason.** No fallback to grep for a
code-structure question was needed either — every lookup here was a named symbol in two files I was
told to open, so `Read`/`grep` on a known path was the honest instrument, not a route-around.

Store reference `docs/reference/surrealdb-31-capabilities.md` read in full before touching anything
(§1.6 *"every test mints a virgin database"* and §9's two-store table are the two facts that bore on
this work; **cited, not transcribed**). It turned out to be **advisory rather than load-bearing
here** — see §3: these eight pins never reach an engine.

## 2. The defect, reproduced before any edit (RED-before)

At `cbe1982`, unmutated, scoped to the four `TASK_READ_ACTIONS`-parametrised tests:

```
8 failed, 8 passed, 209 deselected in 1.98s
E   ValueError: the 'task_id' argument is required for this task action
loremaster/loremaster/server.py:1376: ValueError   (_require_arg, via AppContext.tasks)
```

Exactly the eight the brief named. `_task_action_kwargs` seeded `create` / `create_many` /
`transition` / `supersede` and fell through to `return {}` for `get` and `blockers`, so every one of
those eight died inside `server._require_arg` **before any footer decision was reached**. A red pin
wearing the costume of a build defect — the same shape C-DEF 2 repaired in `_finding_action_kwargs`
one wave earlier, and its in-file comment says so.

## 3. Which backend drives these pins — the question the builder flagged, SETTLED

`REPORT-builder-c3-2.md` §3.1–§3.3 flagged uncertainty about whether `blockers` could be driven at
all. It settles in two moves, and the second is a MEASUREMENT rather than a reading:

1. **These pins never touch a store.** `_footer_harness` (in `test_comms_footer.py`) hands the
   dispatcher `task_ledger=FakeTaskLedger(db=FakeTaskDatabase())` — the in-memory double from
   `loremaster/tests/_task_fakes.py`. Not `spike-surreal`, not anything. So the store reference's
   DDL/DML law does not bind this fixture, and the brief's *"SECTION D drives the live TEST store"*
   note applies to a different part of the file, not to these eight.
2. **`FakeTaskLedger` lacked `transitive_blockers`, and I proved it rather than inferring it.** I
   applied the `task_id` seeding FIRST and re-ran. Result:

```
4 failed, 12 passed, 209 deselected in 1.29s
E   AttributeError: 'FakeTaskLedger' object has no attribute 'transitive_blockers'
loremaster/loremaster/server.py:3817  (AppContext.tasks, the _TASK_ACTION_BLOCKERS branch)
```

The four `get` pins went GREEN on the fixture fix alone; the four `blockers` pins moved from a
`ValueError` to an `AttributeError`. **Both of the brief's contingent preconditions are therefore
measured facts, not expectations**, and the contingency fired on evidence.

## 4. Deviation 1 — `FakeTaskLedger.transitive_blockers` (the contingent edit)

Added to `loremaster/tests/_task_fakes.py`: `FakeTaskLedger.transitive_blockers` plus a private
`FakeTaskLedger._upstream_reach`, and four names added to the existing `from loremaster.tasks import`
block (`ENGINE_RECURSION_CEILING`, `TASK_BLOCKER_MAX_DEPTH`, `TaskLedgerError`, `TransitiveBlockers`).

**Why THERE and not a shim inside `test_comms_footer.py`.** A private `transitive_blockers` on the
footer harness would be copy #2 of a double that already has exactly one home — the ONE
IMPLEMENTATION law, and the next test that drives `action='blockers'` through the fake (e.g. in
`test_mcp_server.py::TestTasksTool`) would meet the identical `AttributeError` with the shim sitting
one file away. The repo has already ruled this exact question: `test_task_read_surface.py` (§"TWO
EDITS THE BUILDER MUST MAKE OUTSIDE THIS FILE") states that
`_task_fakes.FakeTaskLedger.direct_dependents` *"is NOT left to the builder: it is added by this
contract, because a double lacking a method its production twin has turns a CORRECT build into an
`AttributeError` in every test that drives the fake"* — measured there as two reds in
`test_mcp_server.py::TestTasksTool`. This is that ruling's next instance, and the fake's own
`direct_dependents` docstring is the precedent I matched.

**Fidelity — the fake mirrors production BY CONSTRUCTION, and each clause has a reason:**

| property | production (`loremaster.tasks.TaskLedger.transitive_blockers`) | the fake |
|---|---|---|
| default / range | `TASK_BLOCKER_MAX_DEPTH`; `1 <= d < ENGINE_RECURSION_CEILING`, `bool` refused | **the same constants, IMPORTED** — not re-declared |
| out-of-range | `TaskLedgerError`, naming value + range | same class, same sentence |
| unknown id | `TaskNotFoundError` (an id naming nothing ≠ an id with no blockers) | `self._require(task_id)` first |
| order | proximity (`+collect` closure) | breadth-first |
| truncation | MEASURED — the same statement also collects at `depth + 1` and the reaches are compared | the same comparison, at `depth` vs `depth + 1` |
| phantom `blocked_by` entry | absent from the answer (`ENFORCED` forbids the edge) — production's own scope paragraph | skipped in the walk |
| self on a cycle | present iff genuinely on a cycle | the walk never seeds the start into `seen` |
| return type | `TransitiveBlockers` | the same class, IMPORTED |

The two depth constants are **imported from `loremaster.tasks` rather than locally copied**, unlike
this file's status vocabulary. That is deliberate and it is load-bearing: `max_depth_used` travels
back to a RENDER (`AppContext._render_transitive_blockers` teaches a concrete re-ask with it), so a
double carrying its own private default would serve a number production never would. The local-copy
rationale in the module docstring is about not importing from *the test that grades the fake*, and
about constants production had not landed yet — neither applies to a shipped production constant.

**⚠ STATED BOUND, also written into the method's own docstring so it cannot be inherited silently:
this method has NO fake-vs-real parity pin.** `test_task_ledger.py`'s `task_ledger_factory` parity
suite runs only the contract legs that exist and none drives this verb; the real walk is graded
against the live store in `test_blocks_edge.py`. So the two agree by CONSTRUCTION (table above), not
by MEASUREMENT. **Named re-open trigger:** the day any pin asserts on `ids` / `truncated` CONTENT
through this fake, it needs a parity leg first. Today's eight pins assert on the FOOTER and on the
registry-read count, never on the walk's content, so nothing currently rests on the untested half —
and §7's mutation shows the render did genuinely run over the fake's result:

```
served='critical path for task 1447e72fd63642d0a13cde914a3581ee:\n  (nothing upstream — the walk found no blockers)\n— pending traffic for …'
```

## 5. Deviation 2 + the C3 result

`_task_action_kwargs` gained a `get`/`blockers` branch that seeds a real task through the ledger
(`create_task`, `created_by=_UNREGISTERED_ATTRIBUTION`) and returns `{"task_id": task_id}` — the
builder's proposed shape in `REPORT-builder-c3-2.md` §3.3, verified against the actual harness rather
than pasted. That made the function's seventh `return`, which `ruff PLR0911` refuses (`7 > 6`; the PL
family is live under this repo's 2026-07-05 curation and PLR0911 is not one of the ignored idioms).

**Fix taken:** the explicit `if action == "rollup": return {}` and the identical bare fall-through
were folded into one return, with the decision it encoded preserved as a comment (`query` and
`rollup` are unfiltered reads taking no required argument, so an empty mapping IS their fixture).
Behaviour-identical — both arms already returned `{}`. Rejected alternatives: a `# noqa` (house style
takes the real fix, and a suppression teaches the next author that seven returns is fine), and
merging `get`/`blockers` into the `transition`/`supersede` branch (it does not reduce the count).

### 5.1 The C3 gate — the passed-COUNT, never a bare "green"

```
$ uv run pytest loremaster/tests/test_comms_footer.py -q -p no:randomly -n auto
225 passed in 7.00s
```

**225 passed / 0 failed of 225.** Target met. (Re-run AFTER the PLR0911 fix, so this is the tail of
the final tree, not of an intermediate one.)

### 5.2 Ripple — every consumer of the shared double

`_task_fakes.py` is a SHARED double, so its consumers are part of what I touched:

```
$ uv run pytest loremaster/tests/{test_task_ledger,test_mcp_server,test_query_tasks_bounded,\
      test_store_read,test_task_read_surface,test_blocks_edge}.py -q -p no:randomly -n auto
1297 passed in 117.32s (0:01:57)
```

Zero ripple. (Run before the PLR0911 fix, which touched only `test_comms_footer.py` — none of these
six files imports it.)

## 6. Packages considered — the read column, and why it lands on `bespoke`

`_upstream_reach` is a bounded upstream graph walk, so the packages rule genuinely bites here.

| candidate | what I READ / RAN | verdict |
|---|---|---|
| stdlib `graphlib` | `dir(graphlib)` → `{CycleError, GenericAlias, TopologicalSorter}`; `TopologicalSorter.__init__(self, graph=None)` | **disqualified**: it offers topological sorting and RAISES `CycleError`, while this walk must TOLERATE cycles — production's contract says the task appears in its own blockers iff it lies on one. No bounded-reach verb at all. |
| `networkx` 3.6.1 (installed, and a DECLARED direct dep of `loremaster`) | signatures of `bfs_tree(G, source, reverse, depth_limit, sort_neighbors)`, `bfs_layers`, `descendants_at_distance(G, source, distance)`, **plus the probe below** | **bespoke** — it cannot express the semantic, in both directions |

The probe, verbatim, because the claim rests on it (`a -> b -> c -> a`, edge = *"is blocked by"*):

```python
import networkx as nx
g = nx.DiGraph([('a','b'),('b','c'),('c','a')])
tree = nx.bfs_tree(g, 'a', depth_limit=5)
print(list(tree.nodes))                          # ['a', 'b', 'c']
print(nx.descendants_at_distance(g, 'a', 3))     # set()
```

`bfs_tree` includes the source **unconditionally**, as the tree root — not because it lies on a
cycle; and `descendants_at_distance` **never re-discovers** it, even at the exact distance the cycle
closes. Production must distinguish those two worlds (absent when acyclic, present when on a cycle),
and **neither networkx verb can**: one always says present, the other always says absent. Recovering
the distinction on top of either costs strictly more code than the fifteen-line walk, plus a
whole-graph `DiGraph` materialisation per call over a dict the double already holds. That is side 2
of the packages rule working as intended — *the package does not do the job, so hand-roll the missing
piece* — and the bespoke part is kept minimal (a private helper on an existing double, not a parallel
graph layer) and gated by §7's mutation plus §5.2's 1297.

## 7. NON-VACUITY — the point of the exercise

**The wrong build under test:** `AppContext.tasks` treats `get` and `blockers` as WRITES
(`writes = 1` instead of `0`) — precisely the build these eight pins exist to refuse, and a build the
committed one cannot distinguish structurally, because `_with_comms_footer`'s `writes < 1`
short-circuit cannot see the action name.

**The declared RED set was fixed BEFORE the run** (brief-base + finding #194/#196): the eight
`[asyncio-get]` / `[asyncio-blockers]` node ids of the four `TASK_READ_ACTIONS`-parametrised tests,
taken from `pytest --collect-only -q` — which names tests without running them — never transcribed
from a failure list. `scripts/mutation_proof.py` diffs the observed set against it **both ways**
(unexpected reds AND declared-but-still-green).

The anchor was CUT FROM THE FILE rather than retyped, so it could not fail to match for a whitespace
reason. That generator is an instrument a claim rests on, so it survives here verbatim rather than in
a scratch tree:

```python
"""Derive the mutation_proof anchor/replacement for the C-DEF non-vacuity proof."""
from pathlib import Path

SOURCE = Path("loremaster/loremaster/server.py")
START = "        elif action == _TASK_ACTION_GET:\n"
END = "        elif action == _TASK_ACTION_TRANSITION:\n"

text = SOURCE.read_text()
assert text.count(START) == 1, f"START matched {text.count(START)} times"
assert text.count(END) == 1, f"END matched {text.count(END)} times"
block = text[text.index(START) : text.index(END)]
assert block.count("\n                0,\n") == 2
mutated = block.replace("\n                0,\n", "\n                1,\n")
assert mutated != block and text.count(block) == 1
Path("/tmp/cdef1_anchor.txt").write_text(block)
Path("/tmp/cdef1_replacement.txt").write_text(mutated)
```

Invocation (`--anchor-file` / `--replacement-file`, then the whole contract file — NOT a `-k` subset,
so any collateral red would have surfaced as an unexpected-red FAILURE rather than going unobserved):

```
$ ./scripts/mutation_proof.py --file loremaster/loremaster/server.py \
    --anchor-file /tmp/cdef1_anchor.txt --replacement-file /tmp/cdef1_replacement.txt \
    --expect-red '…::test_a_READ_action_NEVER_footers_even_with_traffic_pending[asyncio-get]' \
    --expect-red '…[asyncio-blockers]'   (× 4 tests × 2 actions = 8 declared ids) \
    -- uv run pytest -q -p no:randomly -n auto loremaster/tests/test_comms_footer.py
MUTATION_PROOF_EXIT=0
```

```
8 failed, 217 passed in 7.00s

tree restored byte-exact (loremaster/loremaster/server.py: md5 fce25de2493b3a935dbf8046b1c0d914)

PROOF HELD — the declared RED set fired EXACTLY: [ …all eight get/blockers ids… ]
```

**The eight newly-driven pins DISCRIMINATE.** Not one of them is a vacuous pass: each goes RED on the
wrong build, and the observed set equals the declared set in both directions — no unexpected red, no
declared-but-green. Restoration verified by content md5, and independently by git: `git status` at
report time names **only the two test files**, so `server.py` is byte-identical to `cbe1982`, not
merely to my own pre-mutation copy.

Positive control that the harness could see a *different* failure at all: §2 and §3 are two DISTINCT
red modes (`ValueError` then `AttributeError`) on this same file — the instrument is demonstrably not
stuck returning one verdict.

## 8. The decision I am NOT making — one recommendation for the lead

This is the **second** instance of one defect class in this contract, and both were found by a human
reading a red, not by any gate:

> A parametrised ∀ pin over an action tuple is only as real as its fixture helper's ability to DRIVE
> each member. When a new action joins the tuple and the helper falls through to `return {}`, every
> pin over that member dies inside `_require_arg` — a RED that looks like a build defect and measures
> nothing. C-DEF 2 was `_finding_action_kwargs` (`_FINDING_ACTIONS_NEEDING_A_REF`, repaired
> 2026-08-01); C-DEF 3 is `_task_action_kwargs` (`get`/`blockers`, repaired here).

Repo law says an audit-caught defect CLASS becomes a repo-local invariant, not just a fix. **I did not
build it**, deliberately: it is past *"strictly needed to drive `get`/`blockers`"*, and adding a pin
to a contract mid-wave puts a test in front of a builder that no adversary has graded — which this
repo has ruled against. The shape I would propose, for the lead to accept, reshape or refuse:

*A pin that, ∀ action in `TASK_WRITE_ACTIONS + TASK_READ_ACTIONS + FINDING_WRITE_ACTIONS +
FINDING_READ_ACTIONS`, drives the dispatcher through the action's own `_*_action_kwargs` and asserts
the call does not raise a `ValueError` naming a missing argument.* It fails CLOSED the day an action
joins a tuple without a fixture, and it is name-free over the action set (derived from the tuples the
parametrisations already use), so it cannot go stale the way an enumerated list would. Filed as a lore
finding for durability — **lore finding #322** (`lore_findings get 322`), which also records the
class's SECOND face (a shared double missing a verb its production twin has, §3/§4). A finding row is
provenance, never an adjudication.

## 9. Gates

| gate | result |
|---|---|
| `uv run pytest loremaster/tests/test_comms_footer.py -q -p no:randomly -n auto` | **225 passed / 0 failed** |
| ripple (6 consumer suites of `_task_fakes.py`) | **1297 passed / 0 failed** |
| `uv run ruff check .` | **All checks passed!** (RED on first run — PLR0911, my own; fixed in §5) |
| `./scripts/typecheck.sh` | `102 errors in 8 files` — **all eight are the packet-39 auth family** (`test_auth_composition` 41, `test_permission_resolver_seam` 21, `test_hosted_readonly_posture` 13, `test_allowlist_roster` 10, `test_google_token_verifier` 7, `test_auth` 7, `_auth_fixtures` 4, `test_auth_identity_seam` 3). **NEITHER file I touched appears.** |
| `uv run python scripts/pending_contract_gate.py --currency` | **`CURRENCY : PASS`** — `ruff` GREEN; `typecheck` and `pytest` `RED_ADJUDICATED`, owned by `packet-39-pending-build` (trigger: operator decision #296, or packet 39's build start). No `RED_ORPHANED`. |
| `mutation_proof.py` (§7) | exit **0**, `PROOF HELD`, byte-exact restore |

## 10. Everything else I noticed (scope law — surfaced, not acted on)

1. **The C-DEF class recurrence** — §8. The one item I would call a decision for the lead.
2. **`FakeTaskLedger.transitive_blockers` has no parity leg** — §4, with a named re-open trigger, and
   the bound is written into the method's own docstring so it cannot be inherited silently.
3. **`loremaster/tests/_task_fakes.py` is a SHARED double edited by a wave that only names one test
   file writable.** It went 1297-green here, but a future wave editing it under a
   `test_comms_footer.py`-only writable set would be a scope surprise. Worth naming in the packet's
   writable set explicitly rather than as a contingency.
4. **The store reference was MANDATED and turned out not to bind** (§3: these pins never reach an
   engine). Not a complaint — the mandate is correct precisely because you cannot know that before
   reading it — but recorded so the wave's cost is honest.

**No git state was mutated.** Two files modified in the working tree
(`loremaster/tests/test_comms_footer.py`, `loremaster/tests/_task_fakes.py`); nothing staged,
committed or reverted. The lead commits.

There are 0 failing tests unrelated to this scope in the suites I ran (`test_comms_footer.py` 225/225
and the six `_task_fakes.py` consumers 1297/1297). The repo-wide `typecheck` and `pytest` gates are
RED — **adjudicated and owned by packet 39**, per the currency check above, and untouched by this
work.
