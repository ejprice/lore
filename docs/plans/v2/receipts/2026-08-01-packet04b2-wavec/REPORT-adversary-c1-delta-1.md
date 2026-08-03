# REPORT-adversary-c1-delta-1 — the DELTA ADVERSARY PASS over contract C1's fix wave (04b-2 wave C)

brief-base v9 read
brief project v7 read

*Every measurement below was taken **2026-08-01** against `feat/surreal-unification` @ `f4a9f52`
(the commit that landed the 81-pin C1), in a provenance-asserted scratch copy at
`/home/ejprice/scratch-adv-c1d`. "RED/GREEN today" means at that commit. Where the working
tree differs from `f4a9f52` (slice C3's uncommitted `test_comms_footer.py`) I say so and
attribute it.*

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline — FIVE new wrong builds take the 81-pin contract to `81 passed / 0 failed`, and
  the REFERENCE BUILD ITSELF carries TWO more defects at 81/81.** Two are BLOCKER class:
  (1) **`max_depth` is exposed in the served schema and never FORWARDED** — an agent asking for
  `max_depth=2` gets a walk to **depth 32**, and the render *tells it* "walked to depth 32"
  (§1.1); (2) **ESC-5's own false clear is still alive on a served path, through the `status`
  filter door** — the adopted pin covers only `blocked`, the door the last adversary happened to
  show (§1.2).
- **⚠ THE THIRD BLOCKER IS A CONTRACT DEFECT THE BUILDER CANNOT FIX:** SECTION F specifies
  minting `loremaster.sanitise.fenced_block`/`fence_width` when **`loremaster.render.render_fenced`
  already implements that exact policy**, is already imported by `server.py`, has **3 live call
  sites** there and its own contract suite. Proven by mutation: move the "shared" rule and
  `render_fenced` does **not** move (§1.6). The contract's own falsifier grep was keyed on
  `_fence_width` and is structurally blind to it; its *"exists TWICE"* count is wrong.
- **state: done.** Independent reference build from the contract's build spec → **81 passed /
  0 failed**; satisfiability set **1571 passed / 1 failed** (the 1 attributable to C3, proven both
  legs, §5.2). RED at HEAD reproduced **exactly: 62 failed / 19 passed** (§5.1).
- **All NINE of `adversary-c1-1`'s wrong builds: CONFIRMED-DEAD**, each killed by exactly its own
  pin and nothing else (§2). #268 re-verified **6/6 deterministic RED**, right reason (§5.3).
- **deviations:** none. No repo file was edited; no git *write* command was run.
- **Packages considered:** *backtick-fence policy* → ⚠ **DIFF: `replace` with the IN-REPO
  `loremaster.render.render_fenced`** (READ: `render.py::render_fenced` source, `server.py:182`
  import + 3 call sites, `test_render.py::TestRenderFencedContract`); `markdown-it-py` 4.2.0 →
  **bespoke** (READ: `dir(markdown_it)`, `RendererHTML.fence` — it emits **HTML**, and
  `rules_block.fence` only PARSES; no markdown fence emitter) · *cap validator* →
  `replace_with_adapter`, pydantic 2.13.4 (predecessor's measured row, **still unadopted**) ·
  *over-fetch pagination* → `bespoke` (re-derived: `AsyncWsSurrealConnection`, **33** public
  methods, zero page/cursor/offset) · *id normalisation* → `replace`, stdlib `re`.
  **⚠ The author's §8 survey has NO ROW for the fence mechanism at all** — it predates Ruling 8.
- **MISSING PINS: 7**, each with a wrong build that survives it (§3), each measured with a
  POSITIVE CONTROL (§4).
- **decisions-needed:** (a) whether Δ-6 (the `render_fenced` duplication) is a contract REVISION
  or an operator design ruling — it changes what the builder is told to create; (b) a gate is
  **RED at HEAD** from C3's `39db35c`, not C1's — filed as **finding #317** (§6.1).
- **receipt pointers:** §1 the seven survivors · §2 the nine confirmed-dead · §3 the missing pins
  · §4 my own controls · §5 re-derived author claims · §6 residuals, each with its own verdict ·
  §7 the quantifier table · §8 the package diff · §9 the sweeps · §10 the instruments, verbatim.

---

# §0 · CAPABILITY CHECK (brief-base §4)

Everything the brief demanded was reachable. `lore_comms register` succeeded (the tool-grant gap
that crippled earlier `contract-adversary` runs is fixed for this definition); `scratch_copy.sh`
ran; the store at `ws://127.0.0.1:18000` was reachable. One brief step deviated from
*mechanically*: the brief names `docs/reference/surrealdb-31-capabilities.md` as a required read
before reasoning about store behaviour — **no probe in this pass reasons about engine semantics**
(every store interaction goes through the existing ledger verbs and the existing harness), so I
did not need its content and did not derive any store claim. Saying so rather than claiming a
read I did not use.

**PROVENANCE (#140), printed by every probe:**

```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch-adv-c1d
scratch copy READY: /home/ejprice/scratch-adv-c1d
  loremaster  -> /home/ejprice/scratch-adv-c1d/loremaster/loremaster/__init__.py
  loresigil   -> /home/ejprice/scratch-adv-c1d/loresigil/loresigil/__init__.py
  lorescribe  -> /home/ejprice/scratch-adv-c1d/lorescribe/lorescribe/__init__.py
  lorerunes   -> /home/ejprice/scratch-adv-c1d/lorerunes/lorerunes/__init__.py

PROVENANCE loremaster.__file__ = /home/ejprice/scratch-adv-c1d/loremaster/loremaster/__init__.py
```

I did **not** reuse the fix wave author's reference tree. I built my own implementation from the
contract's own build spec — the module docstring's *"THE PRODUCTION SURFACE THIS CONTRACT
DEFINES"* — which is precisely what a builder will do:

```
$ cd loremaster && uv run pytest tests/test_task_read_surface.py -n auto -q
81 passed in 6.69s
```

**So the author's 81/0 satisfiability receipt reproduces on an independently-authored build**, and
my harness demonstrably reaches the store, the seams, the registered MCP tool and every pin.

---

# §1 · P1 — THE WRONG BUILDS THE FIXED CONTRACT STILL WAVES THROUGH

Every variant is the SAME reference build with exactly ONE thing changed (diffs in §10.2), so a
surviving pin set names precisely one missing pin.

| # | wrong build | C1 result | the defect, MEASURED |
|---|---|---|---|
| **Δ-1** ⛔⛔ | `wb-schema-only` — the registered tool DECLARES `max_depth` but never forwards it | **81 passed** | `lore_tasks action=blockers max_depth=2` walks to **depth 32** and the render says so |
| **Δ-2** ⛔⛔ | `wb-status-seam` — only `status is None` routes through `_task_listing` | **81 passed** | `action=query status='open' limit=5` over 40 matching tasks: **no disclosure line** |
| **Δ-3** | `wb-drop-status` — `_task_listing` drops the caller's `status` filter | **81 passed** | `action=query status='claimed' limit=5` serves **5** rows where the ledger says **1** |
| **Δ-4** | `wb-unknown-reworded` — the unknown-action refusal reworded; `rollup` reaches no branch | **81 passed** | the DISPATCHABLE pin's own verdict is `dead == []` over a **genuinely dead action** |
| **Δ-5** | `wb-search-private` — `SearchPipeline._fence_width` keeps its private copy | **81 passed** | the shared rule moves; `SearchPipeline`'s does not (12 vs 5) |
| **Δ-6** ⛔⛔ | *(the REFERENCE build itself)* — `render.render_fenced` is a second implementation of the specified policy | **81 passed** | shared rule moved → `render_fenced` **unmoved** (12 vs 5), **3 live call sites** in `server.py` |
| **Δ-7** | *(the REFERENCE build itself)* — the served TOP-LEVEL description keeps its CLOSED six-action list | **81 passed** | `missing from the top-level description = ['blockers', 'get']` |
| ✅ | `wb-private-fence` (the task render hand-rolls its fence) | **1 failed / 80 passed** | **CAUGHT** — my negative control, §4.1 |

Raw tails (`uv run pytest tests/test_task_read_surface.py -n auto -q`):

```
######## VARIANT: wb-schema-only        81 passed in 6.86s
######## VARIANT: wb-status-seam        81 passed in 6.85s
######## VARIANT: wb-drop-status        81 passed in 6.77s
######## VARIANT: wb-unknown-reworded   81 passed in 6.76s
######## VARIANT: wb-search-private     81 passed in 6.80s
######## VARIANT: ref                   81 passed in 6.69s   (carries Δ-6 and Δ-7)
######## VARIANT: wb-private-fence       1 failed, 80 passed in 6.79s   <-- CAUGHT
```

## 1.1 Δ-1 (⛔⛔ BLOCKER) — MP-1's SECOND measured fact was never pinned

`adversary-c1-1` §3.1 measured **two** facts and the adopted class pins **one**:

```
MCP tool exposes 'max_depth' parameter: False      <- pinned by test_the_served_tool_exposes_max_depth
MCP tool forwards 'max_depth':          False      <- pinned by NOTHING
```

The wrong build is a one-line deletion from the reference build's forwarding call. The instrument
is the **real registered callable**, pulled off FastMCP's own tool manager
(`mcp._tool_manager.get_tool("lore_tasks").fn`) and invoked with a stub `Context` whose
`lifespan_context` is a live `AppContext` — the exact call an agent makes, not a reconstruction:

```
REGISTERED tool exposes 'max_depth': True    <- what the pin checks
REGISTERED tool FORWARDS 'max_depth': False  <- what NO pin checks

--- AppContext.tasks (the INTERNAL seam EVERY pin drives), max_depth=2 ---
blockers of task 1fdda271…:  (walked to depth 2)
- 0a87b78d…
- 15d7760b…
! the walk stopped at its bound of 2 and more upstream remains — re-run with a larger max_depth

--- the REGISTERED lore_tasks tool (what an AGENT calls), max_depth=2 ---
blockers of task 1fdda271… (walked to depth 32):
- 0a87b78d…
- 15d7760b…
- 6940c9db…
- 0d455343…

VERDICT: the served answer honoured max_depth=2: False
```

**Positive control, same probe on `ref`:** `FORWARDS 'max_depth': True` · both renders `walked to
depth 2` · `VERDICT: True`.

This is worse than a silently-ignored parameter. The render is *honest about the depth it
actually used* — so the served answer **contradicts the caller's own request in writing**, and a
consumer that trusted the bound gets a different scope with no disclosure that its bound was
discarded. That is a Leg-1 scope diff the contract's own module docstring claims to have closed.

⚠ **This is the letter-of-the-finding failure in its purest form.** #314 is *"the new surface is
unreachable through the registered tool"*. The fix pinned the half of the finding whose evidence
line was quoted, and left the other half — measured in the same code block, three lines below —
with no pin at all.

## 1.2 Δ-2 (⛔⛔ BLOCKER) — ESC-5's false clear, through the OTHER filter door

`TestTheDisclosureSurvivesTheFILTERSAtTheSERVEDSeam` drives `blocked=False` (the door WB-1 walked
through) and `owner=` (row COUNT only — it asserts nothing about the disclosure). **`status` is
driven by nothing at the tool.** So the adopted pin kills WB-1 and not WB-1's *class*:

```
--- action=query limit=5 (no status filter): 5 rows ---
['(showing 5 of more matching tasks — re-run with a larger limit to see the rest)']
--- action=query status='open' limit=5 (SAME 40 rows): 5 rows ---
[]

VERDICT: lines the STATUS path lacks = ['(showing 5 of more matching tasks — re-run with a larger limit to see the rest)']
```

**Positive control, same probe on `ref`:** `VERDICT: lines the STATUS path lacks = []`.

The packet's **DEPLOY ENTRY CONDITION**, defeated on a live served call, at 81/81 — for the second
consecutive adversary pass, through a different one of the three filters the same branch accepts.

## 1.3 Δ-3 — the removed-behaviour leg covers `owner` and not `status`

`test_the_tool_passes_the_OWNER_filter_THROUGH` exists because *"this wave REPLACES the query
dispatch branch, so 'it forwards status/owner/blocked' is a removed-behaviour item"*. The pin's
own message names **three** filters; the pin drives **one**.

```
                          ref                          wb-drop-status
status='claimed' limit=5  TOOL served 1 row(s)         TOOL served 5 row(s)
                          LEDGER says 1 match          LEDGER says 1 match
```

And — in that pin's own words — a build dropping the filter *"also serves a bound disclosure about
a population the caller never asked about, which is a false claim wearing an honest mechanism."*
Exactly so; there is just no pin that says it about `status`.

⚠ `blocked` **is** pinned, at the helper (`adversary-c1-1`'s `wb-drop-blocked` was caught), so this
is genuinely a one-filter hole, not a three-filter one. But helper-level coverage only reaches the
tool if routing is TOTAL — which is precisely what Δ-2 breaks.

## 1.4 Δ-4 — the RE-AUTHORED dispatchable pin is keyed on a LITERAL, with no positive control

`test_every_declared_action_is_actually_DISPATCHABLE` was re-authored after `adversary-c1-1` §3.6(b)
proved its first version a false gate. The new version is materially stronger — and it is keyed on
the string `"unknown task action"`:

```python
if "unknown task action" in str(refusal):
    dead.append(action)
```

Reword the dispatcher's own refusal and delete the `rollup` branch:

```
                     ref                                    wb-unknown-reworded
the PIN's verdict    dead == []   (PASSES)                  dead == []   (PASSES)

GROUND TRUTH, rollup:
  ref                AttributeError: 'AppContext' object has no attribute 'finding_ledger'
  wb-unknown-reworded ValueError: unsupported task action 'rollup'; valid actions are [...]
```

`rollup` reaches **no dispatch branch at all**, the dispatcher says so in its own words, and the
pin that exists to detect exactly this is GREEN. This is **the instrument lesson from this repo's
own CLAUDE.md table, verbatim** — *"retry gate · keyed on a label's literal · defeated by a
substring of it"* — reproduced inside the fix for a false gate.

⚠ A second, milder vacuity in the same loop: `except Exception` admits **any** refusal that is not
the literal. On the correct build `rollup` fails with `AttributeError: no attribute
'finding_ledger'` (the seam fixture has no findings ledger) — so on `ref` that action passes the
pin **for a reason unrelated to dispatchability**. The pin is green on `ref` by accident for 1 of
its 8 actions.

## 1.5 Δ-5 — the rider claimed a delegation nothing pins

Ruling 8's rider 2 is discharged in the report by *"`SearchPipeline._fence_width` delegating"*.
`grep -rn "_fence_width" loremaster/tests/*.py` returns **two hits, both PROSE inside the contract's
own comments** — there is no assertion anywhere in the tree. Measured by moving the shared rule
(`sanitise.fence_width` → `+7`):

```
                                           ref        wb-search-private
shared sanitise.fence_width(body)          12 (MOVED)  12 (MOVED)
SearchPipeline._fence_width(body)          12          5      <-- private copy, 81/81 green
```

*Routing is not sharing; prove sharing by MUTATION* — the contract does this for two of the three
call sites the rider names and not for the third.

## 1.6 Δ-6 (⛔⛔ BLOCKER) — THE CONTRACT SPECIFIES A MECHANISM THE REPO ALREADY PROVIDES

**`loremaster.render.render_fenced` already is the shared fenced-block helper.** At `f4a9f52`:

```python
# loremaster/loremaster/render.py
def render_fenced(body: str) -> Rendered:
    """Wrap ``body`` VERBATIM inside a backtick fence (the pre-existing
    ``_render_finding_detail`` idiom, server.py …)."""
    fence = FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)
    return Rendered(f"{fence}\n{body}\n{fence}")
```

That is **byte-for-byte the policy** SECTION F asks the builder to mint in `loremaster.sanitise`.
And it is not obscure:

```
$ grep -n "render_fenced" loremaster/loremaster/server.py
182:  from loremaster.render import render_compose, render_fenced, render_join, render_line
5298:         render_fenced(brief.body),
5498:         render_fenced(brief.body),
6060:         lines.append(render_fenced(entry.body))
```

`server.py` — the very file the new render lives in — **already imports it and calls it three
times**. It has its own contract class (`test_render.py::TestRenderFencedContract`) with a
verbatim-round-trip test, a widen-past-the-longest-run test, and a hostile-body fence-escape test.
Its docstring records that it was extracted **from `_render_finding_detail`'s inline idiom** — the
same inline copy SECTION F now proposes to extract a second time, into a different module.

**The mutation receipt (the correct build; nothing is wrong with the build):**

```
shared sanitise.fence_width(body)         -> 12  (MOVED)
SearchPipeline._fence_width(body)         -> 12
render.render_fenced(body) fence width    -> 5     <-- DID NOT MOVE

render_fenced CALL SITES in server.py: 3
    render_fenced(brief.body),
    render_fenced(brief.body),
    lines.append(render_fenced(entry.body))
```

So a build that satisfies this contract *perfectly* ends with the fence policy in **two**
independent implementations, and the "shared" one reaches **2 of the 5** fence call sites in
`server.py`. `test_the_shared_fenced_block_helper_EXISTS` makes this **unavoidable** — a builder
who did the right thing (call `render_fenced`) goes RED on a pin it may not edit. **This is a
defect the builder cannot fix; it will be built exactly as specified.**

**How it got past the author, and it is this repo's own instrument lesson again.** Ruling 8's
falsifier check (contract SECTION F header, and the report's §13.1) is:

```
grep -rn '_fence_width' loremaster/loremaster
  search.py: the definition + ONE real call site;  server.py: PROSE references only
```

A grep keyed on the **name** `_fence_width` is structurally incapable of seeing `render_fenced`,
which spells the same policy differently — *"seam enumerator · keyed on `async def _query` ·
defeated by `scout.py`, which spells it differently."* The consequence is a stated count that is
false: the contract asserts *"The fence rule already exists TWICE at `025c2a9`"*. Derived here, it
exists **at least THREE times** (`SearchPipeline._fence_width`, `_render_finding_detail`'s inline
copy, `render.render_fenced`) — and `render_fenced` is the one with the type discipline, the tests
and the live callers.

⚠ **`sanitise` may still be the right HOME** (`render.py` imports `FENCE_CHAR`/`MIN_FENCE_WIDTH`/
`max_backtick_run` *from* `sanitise`, so `sanitise` sits below `render` and a helper there is
importable by both). That is a design question — **and it is exactly the design question the
ONE IMPLEMENTATION law says to escalate rather than resolve by writing copy #2.** What is not
defensible is minting the helper and leaving `render_fenced` standing beside it unmentioned.

## 1.7 Δ-7 — the served TOP-LEVEL description still teaches a CLOSED six-action list

`test_every_declared_action_is_NAMED_in_the_served_text` concatenates the tool description **and
every parameter description** before searching. So naming the new actions in the `action`
parameter alone satisfies it. Measured on the **reference build** (81/81):

```
--- what the CONTRACT's pin concatenates ---
    unadvertised = []
--- the TOP-LEVEL tool description ALONE (the summary an agent reads first) ---
    missing from it = ['blockers', 'get']

    "Manage the project's shared, durable fleet task ledger: dispatch on 'action' to CREATE a
     task, CREATE_MANY (…), QUERY the ledger (…), TRANSITION a task (…), SUPERSEDE (reframe) a
     task, or ROLLUP — …"
```

That sentence is a **closed enumeration** ("… or ROLLUP") and it is now false. The pre-existing
`test_mcp_server.py::test_tasks_description_teaches_the_actions` cannot see it either — it checks
four hardcoded literals, all still present. In the adopted pin's own words: *"a description
enumerating a CLOSED list that excludes it teaches that it does not exist."* Correct — and the pin
does not enforce it where the sentence actually lives.

---

# §2 · P4 — ALL NINE OF `adversary-c1-1`'s WRONG BUILDS: **CONFIRMED-DEAD**

Rebuilt from scratch against the 81-pin contract. **A closed finding is a claim**, so each was
re-run, and each is killed by exactly its own pin and nothing else:

| original wrong build | verdict | the pin that killed it | result |
|---|---|---|---|
| WB-1 `wb-blocked-seam` | **CONFIRMED-DEAD** | `TestTheDisclosureSurvivesTheFILTERSAtTheSERVEDSeam::test_a_BLOCKED_filtered_TOOL_call_discloses_its_bound` | 1 failed, 80 passed |
| WB-3 `wb-tool-unwired` | **CONFIRMED-DEAD** | `TestTheNewSurfaceIsREACHABLEThroughTheREGISTEREDTool::test_the_served_tool_exposes_max_depth` | 1 failed, 80 passed |
| WB-4 `wb-drop-owner` | **CONFIRMED-DEAD** | `…::test_the_tool_passes_the_OWNER_filter_THROUGH` | 1 failed, 80 passed |
| WB-2 `wb-confident-chain` | **CONFIRMED-DEAD** | `TestATruncatedWalkAndACompleteWalkOfTheSAMESizeDIFFER` — **both** legs | 2 failed, 79 passed |
| WB-7 `wb-maxdepth-create` | **CONFIRMED-DEAD** | `TestTheNewParameterIsRefusedForEVERYOtherAction` ×5 + the SECTION F matrix row | 6 failed, 75 passed |
| WB-6 `wb-dead-typed-field` | **CONFIRMED-DEAD** | `…::test_a_LOSS_carries_the_superseded_blockers_ON_THE_RESULT` | 1 failed, 80 passed |
| WB-8 `wb-supersede-drops-successor` | **CONFIRMED-DEAD** | `TestTheSupersedeRenderStillNamesTheSUCCESSOR::test_the_render_names_the_successor_it_MINTED` | 1 failed, 80 passed |
| WB-5 `wb-hardcoded-cap` | **CONFIRMED-DEAD** | `…::test_the_disclosure_names_the_number_ACTUALLY_SERVED[cap-2]` | 1 failed, 80 passed |
| `wb-private-limit` | **CONFIRMED-DEAD** | `TestTheCapPredicateHasONEImplementationPROVENByMutation::test_the_SEAM_routes_through_it_TOO_and_not_merely_ITS_CALLEE` | 1 failed, 80 passed |

**No collateral in any of the nine** — no pin fired on a build it was not written for. The eight
adopted classes are genuinely discriminating instruments; the failure is one of QUANTIFIER
(§1.1–1.3) and of the enumeration antipattern (§1.4), not of construction.

⚠ The author's §12.3 record is also **CONFIRMED**: the call-RECORDER form of the ONE-IMPLEMENTATION
pin is what discriminates, and it does — `wb-private-limit` reddens exactly one test.

---

# §3 · THE MISSING PINS — *the test that should exist* + *the defect it catches*

**MP-Δ1 (⛔⛔ BLOCKER)** — `test_MISSING_the_registered_tool_FORWARDS_max_depth`. Pull the
registered callable off the tool manager, invoke it with a stub `Context`, and require the served
render for `max_depth=2` to be byte-identical to `AppContext.tasks(..., max_depth=2)`.
*Catches:* a tool that declares the parameter and drops it — an agent's bound silently discarded
while the render tells it a different depth was used (§1.1).
**Generalise it, or the same hole reopens on the next parameter:** for every parameter in the
registered tool's `inputSchema`, assert the forwarding call passes it through. That property is
∀-over-parameters and cannot be defeated by the next addition.

**MP-Δ2 (⛔⛔ BLOCKER)** — `test_a_FILTERED_TOOL_call_discloses_its_bound`, **parametrized over
`[("blocked", False), ("owner", …), ("status", "open")]`**. Same construction as the existing pin;
one `@pytest.mark.parametrize` instead of a hand-picked filter.
*Catches:* a dispatcher routing only ONE filter branch through `_task_listing` — the DEPLOY ENTRY
CONDITION, defeated for the second adversary pass running (§1.2).

**MP-Δ3** — `test_the_tool_passes_the_FILTER_through`, **parametrized over the same three**, each
with a population where the filter and the cap both bite (§1.3's `status='claimed' limit=5`,
5-vs-1, is the construction).
*Catches:* `_task_listing` dropping any one filter on the capped path — 5 rows served where 1
matches, under a bound disclosure about a population never asked about.

**MP-Δ4** — a POSITIVE CONTROL for `test_every_declared_action_is_actually_DISPATCHABLE`:
`tasks(action="definitely_not_an_action")` **must** raise carrying the literal the loop matches on;
and the `except Exception` should be narrowed so an unrelated error cannot pass an action.
*Catches:* a reworded refusal turning the whole pin vacuous over a genuinely dead action (§1.4).
*Stronger form, if the author prefers the property to the literal:* resolve each `_TASK_ACTIONS`
name to its branch structurally (an AST scan for `action == _TASK_ACTION_<X>` in the dispatcher),
so no served prose is load-bearing at all.

**MP-Δ5** — extend `TestTheFencedBodyRenderHasONEImplementation` with
`test_the_SEARCH_pipeline_routes_through_it_TOO` (the same recorder, over
`SearchPipeline._fence_width`).
*Catches:* the third call site the rider claims to have converted and nothing verifies (§1.5).

**MP-Δ6 (⛔⛔ BLOCKER — contract revision, not just a pin)** — before any pin demands
`loremaster.sanitise.fenced_block`, the contract must adjudicate `loremaster.render.render_fenced`:
either (a) require the new render to CALL it (and delete the `fenced_block` mint), or (b) rule the
move to `sanitise` deliberately and require `render_fenced` to **delegate**, with the recorder
proving it — `test_the_BRIEF_render_routes_through_the_shared_helper` over one of its three live
call sites.
*Catches:* the policy shipping in two implementations, with the "shared" one reaching 2 of the 5
fence call sites in `server.py` — the #102 shape, minted by the contract written to prevent it
(§1.6). **A builder cannot fix this: the pin as written forbids the correct build.**

**MP-Δ7** — split `test_every_declared_action_is_NAMED_in_the_served_text` so the **tool
description alone** must name every action (or state deliberately that the `action` parameter's
description is the canonical enumeration and fix the top-level sentence's closed list).
*Catches:* a served summary that enumerates six actions when eight exist (§1.7) — measured on the
correct build.

---

# §4 · P0 — MY OWN CONTROLS, BECAUSE AN AUDITOR'S INSTRUMENT LIES THE SAME WAY

## 4.1 The negative control for the whole probe set

`wb-private-fence` — the task detail render carries its own fence arithmetic, everything else
identical — is a wrong build the contract **does** catch:

```
FAILED …TestTheFencedBodyRenderHasONEImplementation::test_the_TASK_detail_render_routes_through_the_shared_helper
E  AssertionError: the task detail render fenced its body WITHOUT the shared helper (it recorded 0 call(s)).
1 failed, 80 passed in 6.79s
```

So *"81 passed"* on the five survivors is a fact about **those builds**, not about a suite that
cannot fail. The recorder instrument works, fires on exactly the build it is for, and produces no
collateral.

## 4.2 Two probes of mine that failed for the WRONG reason, caught before they were believed

1. My first `wb-private-fence` build interpolated `FENCE_CHAR`/`MIN_FENCE_WIDTH`/`max_backtick_run`,
   which `server.py` imports under **aliased** names (`_FENCE_CHAR`, …). It reported **5 failed** and
   I would have scored the contract as catching far more than it does. Fixed (aliases) →
   **1 failed**, which is the true discrimination. A survivor set inflated by a `NameError`.
2. My first `#268` mutation run printed `no tests ran in 0.15s` six times behind a `tail` — I had
   guessed the class name. **A green-looking six-run receipt over zero tests.** Node ids re-taken
   from `--collect-only` (which names tests without running them), then re-run — §5.3.
3. My first `wb-drop-status` measurement showed the wrong build serving the CORRECT row count,
   because my probe used an uncapped read and the variant only drops the filter on the *capped*
   path. Re-probed with `limit=5` → 5-vs-1. A survivor I would have mis-scored as caught.

## 4.3 Every negative result in this report is paired

| claim | negative leg | POSITIVE control |
|---|---|---|
| the tool does not forward `max_depth` | `wb-schema-only`: `FORWARDS: False`, depth 32 | `ref`: `FORWARDS: True`, depth 2, renders identical |
| the status path serves no disclosure | `wb-status-seam`: lines lacked = [the disclosure] | `ref`: lines lacked = `[]` |
| the status filter is dropped | `wb-drop-status`: 5 served / 1 matching | `ref`: 1 served / 1 matching |
| a dead action passes the DISPATCHABLE pin | `wb-unknown-reworded`: `dead == []` with `rollup` dead | `ref`: `dead == []` with every action live, per-action ground truth printed |
| `render_fenced` does not share the rule | shared rule +7 → `render_fenced` = 5 | same run: `SearchPipeline._fence_width` = 12 (the instrument CAN see a move) |
| the #302 pin is EXACT equality | spare action → **RED** | a `<=` subset assertion over the same table → **GREEN** |
| the contract can fail at all | — | `wb-private-fence` → 1 failed / 80 passed |

---

# §5 · P7 / P4 — THE AUTHOR'S CLAIMS, RE-DERIVED RATHER THAN RELAYED

## 5.1 RED at HEAD — **reproduced exactly**

```
$ cd loremaster && uv run pytest tests/test_task_read_surface.py -n auto -q
62 failed, 19 passed in 6.72s          # matches §13.4's claim exactly; 62 + 19 = 81
$ uv run pytest tests/test_query_tasks_bounded.py -n auto -q
41 passed in 5.36s
```

Every RED is RED for the right reason — **no import typo, no fixture error, no bad path**:

```
14  AttributeError: 'AppContext' object has no attribute '_task_listing'
12  TypeError: AppContext.tasks() got an unexpected keyword argument 'max_depth'
 7  ValueError: unknown task action 'blockers'
 5  ValueError: unknown task action 'get'
 5  ImportError: cannot import name 'TaskListing' from 'loremaster.tasks'
 2  AttributeError: module 'loremaster.tasks' has no attribute 'validated_task_limit'
 2  AttributeError: module 'loremaster.sanitise' has no attribute 'fenced_block'
 2  AttributeError: 'ClaimResult' object has no attribute 'superseded_blockers'
13  AssertionError — each naming a behaviour that does not exist yet
```

## 5.2 The satisfiability set — **1571 passed / 1 failed**, and the 1 is NOT C1's

The author's §13.4 claims `1572 passed`. I measure **1571 passed, 1 failed**:

```
$ uv run pytest tests/test_task_read_surface.py tests/test_query_tasks_bounded.py \
    tests/test_blocks_edge.py tests/test_task_ledger.py tests/test_mcp_server.py \
    tests/test_txn_contention.py tests/test_surreal_harness.py tests/test_sanitise.py \
    tests/test_search.py tests/test_findings.py -n auto -q
FAILED tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
E  AssertionError: the harness docstring says 46 test files import it; 47 actually do.
1 failed, 1571 passed in 116.27s
```

**Attributed by construction, both legs, in my scratch copy:**

```
$ git show HEAD:loremaster/tests/test_comms_footer.py | grep -c _surreal_harness   -> 0
$ grep -c _surreal_harness loremaster/tests/test_comms_footer.py                   -> 2   (working tree)

@@@ CONTROL: C3's uncommitted edit REVERTED in scratch      1 passed in 1.81s
@@@ C3's edit RESTORED                                      1 failed in 1.86s
```

So the count moved 46 → 47 because **slice C3's `test_comms_footer.py` adds a new
`_surreal_harness` import**. Not C1's, and the author's 1572 was honest at the time it was taken.

⚠ **UPDATE, same session: C3 COMMITTED WHILE I RAN (`39db35c`), so this is no longer a prediction.**
Re-derived at `6948364`:

```
$ git show HEAD:loremaster/tests/test_comms_footer.py | grep -c "_surreal_harness"   -> 2
$ grep -n "test files import this harness" loremaster/tests/_surreal_harness.py
  24:46 test files import this harness, so a module-level import of code still being …
```

The new import is at HEAD and the docstring still says **46**. Combined with the two-legged control
above, **`test_surreal_harness.py::…::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` is
RED at HEAD right now, for every session** — see §6.1.

⚠ **And my own verdicts are unaffected, checked rather than assumed:** the two C1 contract files are
**byte-identical** between repo HEAD `6948364` and my scratch tree
(`diff loremaster/tests/test_task_read_surface.py …` and `…test_query_tasks_bounded.py` → SAME), so
every measurement in this report applies unchanged at the new HEAD. C3's commit touched
`test_blocks_edge.py` (+21 lines) — which C1 imports fixtures from — so I refreshed my scratch to
that file and **re-ran everything against it** rather than leaving it as a stated bound:

```
@@@ ref, against HEAD 6948364's test_blocks_edge     81 passed in 6.69s
wb-schema-only           81 passed in 6.82s
wb-status-seam           81 passed in 6.78s
wb-drop-status           81 passed in 6.78s
wb-unknown-reworded      81 passed in 6.68s
wb-search-private        81 passed in 6.67s
```

**Every verdict in this report holds at `6948364`.**

## 5.3 #268's comparative instrument — **6/6 deterministic RED, for the right reason**

Mutation (declared BEFORE the run, node ids taken from `--collect-only`):
`limit=None if blocked is not None else cap` → `limit=cap` in `TaskLedger._candidate_statement`.

```
@@@ MUTATED, 6 runs:   1 failed / 1 failed / 1 failed / 1 failed / 1 failed / 1 failed
@@@ the POSITIVE-CONTROL leg, mutated:   1 passed
```

The firing assertion is the traffic comparison, not an outcome accident, and the served statements
name the cause:

```
E  AssertionError: the blocked-partition scan read 61 rows under a cap of 60 and 67 rows with no
   cap, for the IDENTICAL answer. The cap SHRANK THE SCAN …
   capped=  ("… SELECT * FROM task WHERE status = $qt_status LIMIT $qt_limit …",)
   unlimited=("… SELECT * FROM task WHERE status = $qt_status …",)
```

Tree restored byte-exact: `md5 532ca7564374b8671111daf45ed48a0d` (identical to the predecessor's
own post-restore hash), `test_query_tasks_bounded.py` back to **41 passed**.

## 5.4 Rider-by-rider, verified

| rider | claim | verdict |
|---|---|---|
| **1** | the #302 pin reddens and updates in the same diff; EXACT equality not a subset | **CONFIRMED by construction** (§4.3): a spare action makes the pin RED where a `<=` assertion stays GREEN |
| **2** | the fence rule is extracted so two call sites share ONE implementation, proven by mutation | **PARTIAL — the two named renders share it (recorder verified, §4.1); `SearchPipeline` is unpinned (Δ-5); and `render_fenced` is an unadjudicated third implementation (Δ-6)** |
| **3** | `get` needed NO new guard code — it sits outside all three accepting-sets | **CONFIRMED by construction**: `limit`/`since`/`max_depth` **and** `items` all refuse `get`, each naming the parameter and the action. ⚠ Bound: 8 further parameters are silently swallowed (§6.2) |
| **4** | #314's generic invariant covers `get` | **PARTIAL** — `get` is inside the served-text pin's coverage, but that pin's reach is the concatenated text (Δ-7), and #314's forwarding half is unpinned (Δ-1) |
| **5** | the chain render's follow-up teaches `action=get`, and the property pin is permanent | **CONFIRMED**: the taught-action pin is written to the property; my reference render teaches `lore_tasks action=get task_id=<served id>` and both legs pass |
| — | the author's own two self-caught false gates (§12.3 sentinel, §13.3 post-lint trap) | **CONFIRMED** — the recorder form discriminates (§4.1); `PLR0912` does fire on `AppContext.tasks` once two actions land (my ref build needed the same `noqa`) |

⚠ **The brief predicted a third self-inflicted false gate. There is one, and it is Δ-4** — the
re-authored DISPATCHABLE pin, keyed on a literal, with no positive control. It is a genuine
improvement on what it replaced and still defeatable by a reword.

---

# §6 · RESIDUALS — every one with its OWN verdict

## 6.1 ⚠ ESCALATED, NOT C1's — a gate that goes RED the moment C3 commits

`test_surreal_harness.py::…::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` **IS RED at
HEAD right now, for every session.** C3's fix wave landed at `39db35c` **during this pass**, its
`test_comms_footer.py` now imports `_surreal_harness` at HEAD, and the harness docstring still says
`46 test files import this harness` where **47** do (§5.2, with a two-legged control).

The fix is a one-character docstring bump in `loremaster/tests/_surreal_harness.py` (`46` → `47`) —
which is **#308's shape recurring, one commit after #308 was fixed**. Nobody has seen it: C3's own
suite does not include the harness file, so its `exit 0` receipt could not have caught this.
**Filed as finding #317.** **Owner: C3 / the lead. Decision point: NOW — it is red at HEAD, not pending.** I did not touch it
(outside my writable set, and `test_comms_footer.py` is explicitly do-not-touch).

⚠ **The generalisable half:** a DERIVED-count pin in a shared file goes red on the commit of *any*
slice that adds an importer, and no slice's own scoped gate can see it. That is exactly the class
`scripts/pending_contract_gate.py --currency` exists for — this one is currently **RED_ORPHANED**.

## 6.2 `action=get` silently swallows 8 of 12 caller-supplied parameters

Measured on the reference build, each producing **byte-identical** output to a bare `get`:

```
parameter     outcome on action=get   same bytes as a bare get?
limit         REFUSED                 ValueError: 'limit' applies only to action='rollup' and 'query' …
since         REFUSED                 ValueError: 'since' applies only to action='rollup' — omit it for 'get'
max_depth     REFUSED                 ValueError: 'max_depth' applies only to action='blockers' — omit it for 'get'
items         REFUSED                 ValueError: 'items' applies only to action='create_many' — omit it for 'get'
summary       ACCEPTED, ignored       True
report_path   ACCEPTED, ignored       True
blocked_by    ACCEPTED, ignored       True
status        ACCEPTED, ignored       True
owner         ACCEPTED, ignored       True
blocked       ACCEPTED, ignored       True
actor         ACCEPTED, ignored       True
subject       ACCEPTED, ignored       True
```

**Verdict: pre-existing class, NOT this wave's regression** — the same holds for `create`, `query`
and every other action, because the dispatcher only guards `since`/`limit`/`items`. But the
refusal matrix is the teaching surface the contract cites as *"the strict-parameter matrix exists
so a caller passing one is TOLD rather than silently ignored"*, and it covers 4 of 12. Escalated,
not buried; not a C1 blocker.

## 6.3 `test_mcp_server.py::test_tasks_description_teaches_the_actions` is now a second grammar

It asserts four hardcoded literals (`create`/`transition`/`rollup`/`create_many`) for a property
the new SECTION E pin states ∀. **Verdict: benign today** (green on every build I made), **but it is
the enumeration antipattern beside its own replacement** — the #102 shape at the pin level. Worth
deleting or converting when Δ-7 is addressed.

## 6.4 `_render_finding_detail`'s fenced OUTPUT has no direct pin

`grep -rn "_render_finding_detail" loremaster/tests/*.py` outside the new contract returns **three
hits, all unrelated string fixtures in `test_comms_promise_registry.py`**. The reroute through
`fenced_block` is covered by the recorder (routing) and, indirectly, by `test_findings` /
`test_mcp_server` output assertions — my ref build's 1571 pass is the evidence the behaviour
survived. **Verdict: adequately covered indirectly; no missing pin claimed.**

## 6.5 #313 — the hostile fixtures ARE armed (checked, not assumed)

The brief warned that an upstream guard can shadow a fixture meant to arm a downstream pin. Both
of SECTION F's hostile fixtures survive the WRITE path byte-exact:

```
#313 — does the hostile SUBJECT survive the WRITE path to arm the render pin?
  newline still in STORED subject: True
  stored subject repr: 'ordinary\n- [open] forged by the subject (id x, owner root, blocked_by [])'
#313 — does the hostile BODY survive the WRITE path?
  newlines still in STORED description: 4
  backtick runs still present: True
```

**Verdict: no shadowing. The forgery pins are genuinely armed.**

## 6.6 The `_fence_bounds` helper derives its marker from PRODUCTION

`_fence_bounds` computes `FENCE_CHAR * fence_width(body)` from the production function. This is
declared deliberate in its own docstring, and it is the right trade (a test re-deriving the rule
would agree with a build that got it wrong). **Verdict: sound** — and `test_the_fence_is_WIDER_than
_the_longest_backtick_run_in_the_body` supplies the independent check by comparing against
`max_backtick_run` rather than against `fence_width`.

## 6.7 Not re-verified by me — stated so it is not read as cleared

I did **not** re-derive: the author's ruff/mypy figures; the `_ANSWER_CAP`/`_BLOCKED_NOISE_EACH_SIDE`
sandwich constants beyond what #268's own fixture guards assert; the SECTION B phantom-residue
constructions beyond running them. Each was verified by `adversary-c1-1` or is guarded by its own
in-file drift assertion. **No verdict claimed on any of them.**

---

# §7 · P1b — THE QUANTIFIER TABLE (the DELTA: SECTION E + SECTION F, plus what I re-opened)

Every invariant the fix wave ADDED, classified ∀-over-inputs vs guarded-by-known-failure-mode.
Every **GUARDED** row carries a receipt: a surviving wrong build, or the door-build that died.

| # | invariant (SECTION E/F) | ∀ / GUARDED | receipt |
|---|---|---|---|
| E1a | the registered tool EXPOSES `max_depth` | **∀** over the served schema | door-build `wb-tool-unwired` → killed |
| E1b | the registered tool **FORWARDS** what it exposes | **UNPINNED** | **BLOCKER: `wb-schema-only` survives** — served depth 32 vs requested 2 (§1.1) |
| E1c | every declared action is NAMED in the served text | **GUARDED to the CONCATENATION** (description + every param description) | **`ref` itself survives**: the top-level description names 6 of 8 (§1.7) |
| E2a | a filtered TOOL call discloses its bound | **GUARDED to `blocked`** | **BLOCKER: `wb-status-seam` survives** (§1.2) |
| E2b | the tool passes the caller's filter THROUGH | **GUARDED to `owner`** (and to row COUNT, not to the disclosure) | **`wb-drop-status` survives**: 5 served / 1 matching (§1.3) |
| E3 | the disclosure names the number ACTUALLY SERVED | **∀** over 2 caps (5 and 2) | door-build `wb-hardcoded-cap` → killed at `[cap-2]` |
| E4 | a truncated walk and a complete walk of EQUAL size differ | **∀** over the two-world construction, id lists equal BY CONSTRUCTION | door-build `wb-confident-chain` → killed, **both** legs |
| E5 | `max_depth` is refused for every non-`blockers` action | **∀** over all six | door-build `wb-maxdepth-create` → killed on 5 of 6 + the matrix row |
| E6 | the superseded-blocker fact is TYPED state on the RESULT | **∀** both directions (LOSS populated, WIN empty) | door-build `wb-dead-typed-field` → killed |
| E7 | the supersede render names the SUCCESSOR | **∀** on the no-dependents branch (deliberately, so nothing else can carry the id) | door-build `wb-supersede-drops-successor` → killed |
| E8 | the cap predicate has ONE implementation | **∀ over the two call sites**, by call RECORDER with a control leg | door-build `wb-private-limit` → killed. The strongest pin in the file. |
| D2′ | every declared action is DISPATCHABLE | **GUARDED by a served LITERAL** (`"unknown task action"`), and `except Exception` admits any other error | **`wb-unknown-reworded` survives** with `rollup` genuinely dead (§1.4) |
| F1 | `get` serves the DESCRIPTION `query` omits | **∀**, discriminated against `query` rather than against a literal | no survivor |
| F2 | an unknown id TEACHES; a missing `task_id` names the argument | **∀** (both forced) | no survivor |
| F3 | the refusal matrix covers `get` | **GUARDED to 3 parameters** of 12 | receipt §6.2 — **pre-existing class**, all 4 guarded params refuse correctly; not a C1 regression |
| F4 | a row-shaped forgery in the body stays INSIDE the fence | **∀** over the hostile fixture, **armed** (#313 checked, §6.5) | door-build `wb-private-fence` → killed |
| F5 | the fence is WIDER than the longest run (two runs of different widths) | **∀**, independent of `fence_width` (compares to `max_backtick_run`) | door-build `wb-private-fence` → killed |
| F6 | single-line trailers are SANITISED, body is FENCED | **GUARDED to `subject`** | armed and discriminating for `subject` (#313 checked). The other caller-supplied single-line fields a detail render might carry are unspecified by the contract, so no door-build exists to try. **No survivor built** — bound STATED, not a claimed hole |
| F7a | the TASK detail render routes through the shared helper | **∀ by call RECORDER** | door-build `wb-private-fence` → killed |
| F7b | the FINDING detail render routes through it TOO | **∀ by call RECORDER** | no survivor |
| F7c | the fence rule has **ONE** implementation *in the repo* | **FALSE AS SPECIFIED** | **BLOCKER: `ref` itself survives** — `render.render_fenced` unmoved under mutation, 3 live call sites (§1.6); `wb-search-private` adds a third (§1.5) |

---

# §8 · P-PKG — MY TABLE, BUILT FIRST, THEN DIFFED AGAINST THE AUTHOR'S

| mechanism | libraries evaluated | what I **READ** | my verdict |
|---|---|---|---|
| **backtick-fence policy (width + wrap)** — the mechanism SECTION F mints | **in-repo `loremaster.render.render_fenced`**; `markdown-it-py` 4.2.0 | `render.py::render_fenced` full source; `server.py:182` import and its 3 call sites (grepped); `test_render.py::TestRenderFencedContract` (3 tests incl. a hostile-body fence-escape case). For the package: `dir(markdown_it)` (12 exports, all parser-side), `dir(RendererHTML)` — its `fence` method emits **HTML**, and `markdown_it.rules_block.fence` is a **tokeniser**; no markdown-emitting fence helper exists in it | ⚠ **`replace` — with the IN-REPO helper.** No package needed; the repo already owns it, tested, imported and called. `markdown-it-py` → **bespoke** (wrong direction: it parses fences, it does not emit them) |
| Over-fetch-by-one bound disclosure over a store read | `surrealdb` (installed SDK) | re-derived live this session: **33** public methods on `AsyncWsSurrealConnection`, filtered for `page`/`limit`/`cursor`/`offset`/`next`/`more` → **zero**. (Predecessor reported 33; the author reported 32) | **bespoke** — confirmed, nothing sits between us and the engine |
| The cap validator (`limit` range refusal) | `pydantic` 2.13.4 | the predecessor's measured row: `TypeAdapter(Annotated[PositiveInt, Strict()])` rejects `0`, `-1` **and** `True`, and names `input_value` | ⚠ **`replace_with_adapter` — and it is STILL UNADOPTED.** The fix wave promoted the predicate to a shared module-level function (correct for ONE IMPLEMENTATION) but kept the hand-rolled `isinstance(limit, bool) or not isinstance(limit, int) or limit < 1` triple. `keep_with_trigger` is defensible here (the message text is a pinned served surface) — but the trigger must be NAMED, and it is not |
| Locating the disclosure line by two-world diff | `difflib` (stdlib) | the author's read, not re-derived | **bespoke, minimal** — agreed, no diff |
| Normalising opaque ids | `re` (stdlib) | in-use | **replace** — agreed, no diff |

**THE DIFF, and it is the largest one:** the author's §8 table has **five rows and none of them is
the fence.** SECTION F was authored under Ruling 8, *after* §8 was written, and §8 was never
re-opened. So the newest mechanism this contract specifies — a shared policy helper plus the
rerouting of two renders through it — **was surveyed neither for a package nor for in-repo reuse**,
and the in-repo answer was already imported at the top of the very file the new render lives in.
That is Δ-6, and it is why P-PKG is a required OUTPUT rather than a rule: *nobody refused the rule;
nothing asked for the answer* about the one mechanism added last.

---

# §9 · P6 / P6b — THE SWEEPS, EVERY HIT WITH ITS OWN VERDICT

## 9.1 Corpse sweep — assertions still pinning the retired world

| hit | verdict |
|---|---|
| `test_query_tasks_bounded.py:2074` *"HOLE 8 — CLOSED BY 04b-2 WAVE C. THE KNOWN BOUND THAT LIVED HERE IS DELETED."* | **NOT a corpse** — the class is genuinely gone; the marker is its tombstone, as its own instruction required |
| `test_query_tasks_bounded.py:158` (docstring reference to the deletion) | **NOT a corpse** — prose recording the deletion |
| `test_task_read_surface.py:1224` `unknown task action 'get'` (prose) | **NOT a corpse** — it is the fabricated-affordance rationale, and it is now counterfactual prose about a verb that exists. ⚠ Mildly stale: `get` now DOES exist, so the example no longer illustrates a live hazard. Cosmetic |
| `test_task_read_surface.py:1777` / `:1805` `"unknown task action"` | **NOT a corpse — it is Δ-4**, the literal the DISPATCHABLE pin is keyed on (§1.4) |
| `test_mcp_server.py::test_tasks_description_teaches_the_actions` (4 literals) | **NOT a corpse** — green on every build; but see §6.3 |
| `server.py:6376` *"Exactly six actions in C1"* · `server.py:7943` *"its six actions"* | **NOT corpses** — both describe `_COMMS_ACTIONS` (`lore_comms`), untouched by this wave. Verified by reading both sites |
| `test_comms_footer.py` / `test_comms_tool.py` "six actions" hits | **NOT corpses** — `lore_comms`, and those files are C3's |
| any test transcribing the `lore_tasks` tool description verbatim | **NONE EXIST** (`grep -rln "or 'rollup' (one-call fleet catch-up" tests/*.py` → no hits) — which is exactly why Δ-7 is invisible |

## 9.2 P6b — removed-behaviour, enumerated from the SOURCE first, then diffed

Enumerated from `server.py` at `f4a9f52` before opening the contract's inventory (the contract's
docstring adjudicates 2 explicit removed-behaviour items; I enumerated **8** behaviours across
**5** replaced sites).

| replaced/deleted code | observable behaviour | pinned? |
|---|---|---|
| the `QUERY` dispatch branch | forwards `owner` to the ledger | ✅ SECTION E (count only) |
| " | forwards `blocked` | ✅ at the HELPER — and only reaches the tool if routing is total, which Δ-2 breaks |
| " | forwards **`status`** | ❌ **MISSING — Δ-3** |
| " | forwards `limit`; renders via `_render_task_rows`; empty case | ✅ SECTION A |
| the `SUPERSEDE` return line | names the successor id | ✅ SECTION E (this was the author's own adjudicated item) |
| `_render_finding_detail`'s inline fence | the finding detail's fenced output | ⚠ indirectly (§6.4) |
| `SearchPipeline._fence_width`'s body | the search pipeline's fence width | ❌ **MISSING — Δ-5** |
| `TaskLedger._validated_limit`'s body | the ledger's cap refusal + message | ✅ SECTION E recorder + SECTION A behavioural pins |

**Diff against the contract's own inventory:** it adjudicates 2 items (`NON_WRITING_VERBS` and
`VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH` for `direct_dependents` — both verified correct, both
green on my ref build) and names the query branch's filter-forwarding as a removed-behaviour item
in `TestTheDisclosureSurvivesTheFILTERSAtTheSERVEDSeam`'s docstring — **naming all three filters and
pinning one.** No inventory item is ungrounded. Two behaviours the inventory misses: `status`
forwarding (Δ-3) and `SearchPipeline._fence_width` (Δ-5).

---

# §10 · THE INSTRUMENTS (brief-base §1 — pasted, because scratch is a plan to lose them)

## 10.1 What they are, and how to re-run them

Three scripts, in `/home/ejprice/scratch-adv-c1d` (**disposable by design — this section is the
record**). `advd_build.py` extends `adversary-c1-1`'s `adv_build.py` (pasted verbatim in that
agent's report, archived with this wave) with the SECTION E/F surface; its variant-defining hunks
are the diffs in §10.2, which is the compact and precise form. `advd_demo.py` / `advd_demo2.py`
are pasted whole in §10.3–10.4.

```bash
./scripts/scratch_copy.sh /abs/scratch                 # provenance-asserted copy
python advd_build.py <variant>                         # ref | wb-*  (--restore to revert)
cd loremaster && uv run pytest tests/test_task_read_surface.py -n auto -q
cd loremaster && uv run python ../advd_demo.py  {maxdepth|status|dispatch|fence}
cd loremaster && uv run python ../advd_demo2.py {desc|ignored|equality}
```

Reference-build recipe, in full, so §0's 81/0 is reproducible without the script:
`tasks.py` += `validated_task_limit` / `TaskListing` / `ClaimResult.superseded_blockers` /
`direct_dependents` / `_superseded_among`, `_validated_limit` delegating, `claim_task` populating ·
`sanitise.py` += `fence_width` / `fenced_block` · `search.py` `_fence_width` delegating ·
`server.py` += `_TASK_ACTION_BLOCKERS` / `_TASK_ACTION_GET` / `_TASK_ACTIONS_ACCEPTING_MAX_DEPTH` /
`_task_listing` / `_render_task_listing` / `_render_transitive_blockers` / `_render_task_detail`,
the `max_depth` guard, the `blockers` + `get` branches, the supersede warning, the claim reason,
`_render_finding_detail` → `fenced_block`, the registered tool's `max_depth` param **and its
forwarding**, the `action` description naming `'blockers'`/`'get'`, and `noqa: PLR0911,PLR0912` ·
`test_blocks_edge.py` += `direct_dependents` in both ∀-verb frozensets.

## 10.2 The five surviving wrong builds, as diffs against the REFERENCE build

```diff
===== Δ-1  wb-schema-only  (server.py — the registered tool's forwarding call) =====
             since=since,
             limit=limit,
-            max_depth=max_depth,
             items=items,

===== Δ-2  wb-status-seam  (server.py — AppContext.tasks, the QUERY branch) =====
         if action == _TASK_ACTION_QUERY:
-            return self._render_task_listing(
-                await self._task_listing(
-                    status=status, owner=owner, blocked=blocked, limit=limit
+            if status is None:
+                return self._render_task_listing(
+                    await self._task_listing(
+                        status=status, owner=owner, blocked=blocked, limit=limit
+                    )
                 )
+            rows = await self.task_ledger.query_tasks(
+                status=status, owner=owner, blocked=blocked, limit=limit
             )
+            return self._render_task_rows(rows)

===== Δ-3  wb-drop-status  (server.py — AppContext._task_listing, the capped path) =====
         fetched = await self.task_ledger.query_tasks(
-            status=status, owner=owner, blocked=blocked, limit=cap + 1
+            status=None, owner=owner, blocked=blocked, limit=cap + 1
         )

===== Δ-4  wb-unknown-reworded  (server.py — AppContext.tasks) =====
-        if action == _TASK_ACTION_ROLLUP:
-            return await self._rollup(since=since, limit=limit)
         if action == _TASK_ACTION_CREATE_MANY:
...
         raise ValueError(
-            f"unknown task action {action!r}; valid actions are {list(_TASK_ACTIONS)}"
+            f"unsupported task action {action!r}; valid actions are {list(_TASK_ACTIONS)}"
         )

===== Δ-5  wb-search-private  (search.py — SearchPipeline._fence_width) =====
-        from loremaster.sanitise import fence_width  # noqa: PLC0415
-
-        return fence_width(source_text)
+        return max(_MIN_FENCE_WIDTH, _max_backtick_run(source_text) + 1)
```

Δ-6 and Δ-7 need **no diff at all** — they are properties of the *correct* build (§1.6, §1.7).

## 10.3 `advd_demo.py` — the four defect measurements

```python
#!/usr/bin/env python
"""DELTA-ADVERSARY INSTRUMENT — MEASURE the defect each surviving wrong build carries.

A wrong build that passes the contract is only a finding once its DEFECT is measured on a
served path.  Run against whichever variant advd_build.py has installed.
"""
from __future__ import annotations
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "loremaster" / "tests"))
import loremaster
print(f"PROVENANCE loremaster.__file__ = {loremaster.__file__}")
from _surreal_harness import drop_database
from test_blocks_edge import CREATOR, DESCRIPTION
from test_query_tasks_bounded import _fresh_ledger, _tool_seam


async def probe_maxdepth() -> None:
    """MP-1's SECOND measured fact: does the REGISTERED tool FORWARD max_depth?

    The instrument is the REAL registered callable, pulled off FastMCP's own tool manager
    and invoked with a stub Context whose lifespan_context is a live AppContext — the exact
    call an agent makes, not a reconstruction of it.
    """
    import inspect, tempfile, types
    from loremaster.server import LoreServer, build_mcp_server
    from test_mcp_server import _config, _slug

    with tempfile.TemporaryDirectory() as tmp:
        mcp = build_mcp_server(LoreServer(_config(_slug(), Path(tmp) / "live")))
        tool = {t.name: t for t in await mcp.list_tools()}["lore_tasks"]
        registered = mcp._tool_manager.get_tool("lore_tasks").fn
    props = (tool.inputSchema or {}).get("properties", {})
    print(f"REGISTERED tool exposes 'max_depth': {'max_depth' in props}   <- what the pin checks")
    source = inspect.getsource(registered)
    forward = source[source.index("_app_context(context).tasks(") :]
    print(f"REGISTERED tool FORWARDS 'max_depth': "
          f"{'max_depth=max_depth' in forward}   <- what NO pin checks")

    ledger, env = await _fresh_ledger()
    try:
        previous, chain = [], []
        for index in range(4):
            task_id = await ledger.create_task(
                f"chain link {index}", DESCRIPTION, blocked_by=previous, created_by=CREATOR)
            chain.append(task_id); previous = [task_id]
        leaf = await ledger.create_task("leaf", DESCRIPTION, blocked_by=[chain[-1]],
                                        created_by=CREATOR)
        app = _tool_seam(ledger)
        stub = types.SimpleNamespace(
            request_context=types.SimpleNamespace(lifespan_context=app))
        internal = str(await app.tasks(action="blockers", task_id=leaf, max_depth=2))
        served = str(await registered(stub, action="blockers", task_id=leaf, max_depth=2))
        print("\n--- AppContext.tasks (the INTERNAL seam EVERY pin drives), max_depth=2 ---")
        print(internal)
        print("\n--- the REGISTERED lore_tasks tool (what an AGENT calls), max_depth=2 ---")
        print(served)
        print(f"\nVERDICT: the served answer honoured max_depth=2: {served == internal}")
    finally:
        await ledger.close(); await drop_database(env)


async def probe_status() -> None:
    """ESC-5 at the TOOL, through the STATUS filter door."""
    ledger, env = await _fresh_ledger()
    try:
        from loremaster.tasks import TaskSpec
        await ledger.create_many(
            [TaskSpec(subject="claimable backlog item", description=DESCRIPTION, blocked_by=[])
             for _ in range(40)], created_by=CREATOR)
        context = _tool_seam(ledger)
        plain = str(await context.tasks(action="query", limit=5))
        filtered = str(await context.tasks(action="query", status="open", limit=5))
        rows = lambda text: [l for l in text.splitlines() if l.startswith("- ")]
        extra = lambda text: [l for l in text.splitlines() if not l.startswith("- ")]
        print(f"--- action=query limit=5 (no status filter): {len(rows(plain))} rows ---")
        print(extra(plain))
        print(f"--- action=query status='open' limit=5 (SAME 40 rows): "
              f"{len(rows(filtered))} rows ---")
        print(extra(filtered))
        print(f"\nVERDICT: lines the STATUS path lacks = "
              f"{[l for l in extra(plain) if l not in extra(filtered)]}")
        # the REMOVED-BEHAVIOUR half: is the status filter forwarded AT ALL?
        # A claim moves ONE task to 'claimed' (no transition machine needed).
        first = (await ledger.query_tasks(limit=1))[0]
        await ledger.claim_task(first.id, CREATOR)
        served_claimed = str(await context.tasks(action="query", status="claimed", limit=5))
        truth_claimed = await ledger.query_tasks(status="claimed")
        print(f"\nstatus='claimed' limit=5: the TOOL served {len(rows(served_claimed))} row(s); "
              f"the LEDGER says {len(truth_claimed)} match")
    finally:
        await ledger.close(); await drop_database(env)


async def probe_dispatch() -> None:
    """Run the DISPATCHABLE pin's own assertions against a build with a DEAD action."""
    from loremaster.server import _TASK_ACTIONS
    ledger, env = await _fresh_ledger()
    try:
        context = _tool_seam(ledger)
        dead, real_failures = [], {}
        for action in _TASK_ACTIONS:
            try:
                await context.tasks(action=action)
            except Exception as refusal:
                real_failures[action] = f"{type(refusal).__name__}: {str(refusal)[:90]}"
                if "unknown task action" in str(refusal):
                    dead.append(action)
        print(f"the PIN's verdict — dead == {dead}   (pin PASSES iff this is [])")
        print("\nGROUND TRUTH, per action:")
        for action, message in real_failures.items():
            print(f"  {action:<12} {message}")
    finally:
        await ledger.close(); await drop_database(env)


def probe_fence() -> None:
    """Move the SHARED fence rule; report which implementations moved with it."""
    import loremaster.render as render_module
    import loremaster.sanitise as sanitise_module
    from loremaster.search import SearchPipeline

    body = "x\n```\n````\ny"
    real = sanitise_module.fence_width

    def widened(text: str) -> int:
        return real(text) + 7                       # the shared rule, MOVED

    sanitise_module.fence_width = widened
    real_block = sanitise_module.fenced_block
    sanitise_module.fenced_block = lambda text: (
        sanitise_module.FENCE_CHAR * widened(text) + "\n" + text + "\n"
        + sanitise_module.FENCE_CHAR * widened(text))
    try:
        print(f"shared sanitise.fence_width(body)         -> "
              f"{sanitise_module.fence_width(body)}  (MOVED)")
        print(f"SearchPipeline._fence_width(body)         -> "
              f"{SearchPipeline._fence_width(body)}")
        rendered = str(render_module.render_fenced(body))
        print(f"render.render_fenced(body) fence width    -> "
              f"{len(rendered.splitlines()[0])}")
        server_src = (Path(__file__).resolve().parent / "loremaster" / "loremaster"
                      / "server.py").read_text()
        calls = [line.strip() for line in server_src.splitlines()
                 if "render_fenced(" in line and "import" not in line and "func:" not in line]
        print(f"\nrender_fenced CALL SITES in server.py: {len(calls)}")
        for line in calls:
            print(f"    {line}")
    finally:
        sanitise_module.fence_width = real
        sanitise_module.fenced_block = real_block


if __name__ == "__main__":
    probe = sys.argv[1]
    if probe == "fence":
        probe_fence()
    else:
        asyncio.run({"maxdepth": probe_maxdepth, "status": probe_status,
                     "dispatch": probe_dispatch}[probe]())
```

## 10.4 `advd_demo2.py` — the three residual probes

```python
#!/usr/bin/env python
"""DELTA-ADVERSARY INSTRUMENT — three residual probes against the REFERENCE build.

  desc     the served TOP-LEVEL tool description vs the live action set
  ignored  which caller-supplied lore_tasks parameters action='get' silently swallows
  equality whether the #302 pin is EXACT equality (constructive, not by reading)
"""
from __future__ import annotations
import asyncio, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "loremaster" / "tests"))
import loremaster
print(f"PROVENANCE loremaster.__file__ = {loremaster.__file__}")
from _surreal_harness import drop_database
from test_blocks_edge import CREATOR, DESCRIPTION
from test_query_tasks_bounded import _fresh_ledger, _tool_seam


async def probe_desc() -> None:
    from loremaster.server import _TASK_ACTIONS, LoreServer, build_mcp_server
    from test_mcp_server import _config, _slug
    with tempfile.TemporaryDirectory() as tmp:
        mcp = build_mcp_server(LoreServer(_config(_slug(), Path(tmp) / "live")))
        tool = {t.name: t for t in await mcp.list_tools()}["lore_tasks"]
    top = tool.description or ""
    props = (tool.inputSchema or {}).get("properties", {})
    joined = top + "".join((s.get("description") or "") for s in props.values())
    print("--- what the CONTRACT's pin concatenates (description + every param description) ---")
    print(f"    unadvertised = {[a for a in _TASK_ACTIONS if f\"'{a}'\" not in joined]}")
    print("--- the TOP-LEVEL tool description ALONE (the summary an agent reads first) ---")
    print(f"    missing from it = {[a for a in _TASK_ACTIONS if a not in top.lower()]}")
    print(f"\n    the served top-level description, verbatim:\n    {top!r}")
    print("\n--- the OLDER test_mcp_server pin's four literals ---")
    for literal in ("create", "transition", "rollup", "create_many"):
        print(f"    {literal!r} in description: {literal in top.lower()}")


async def probe_ignored() -> None:
    """Which caller-supplied parameters does action='get' SILENTLY swallow?"""
    ledger, env = await _fresh_ledger()
    try:
        target = await ledger.create_task("a task", DESCRIPTION, created_by=CREATOR)
        context = _tool_seam(ledger)
        baseline = str(await context.tasks(action="get", task_id=target))
        candidates = {
            "limit": 5, "since": "2026-07-01T00:00:00Z", "max_depth": 3,
            "items": [{"subject": "x", "description": "y"}],
            "summary": "a completion digest that means nothing here",
            "report_path": "/tmp/nope.md", "blocked_by": ["deadbeef"], "status": "done",
            "owner": "someone-else", "blocked": True, "actor": "someone",
            "subject": "a different subject",
        }
        print(f"{'parameter':<14}{'outcome on action=get':<24}same bytes as a bare get?")
        for name, value in candidates.items():
            try:
                served = str(await context.tasks(action="get", task_id=target, **{name: value}))
            except Exception as refusal:
                print(f"{name:<14}{'REFUSED':<24}{type(refusal).__name__}: {str(refusal)[:60]}")
            else:
                print(f"{name:<14}{'ACCEPTED, ignored':<24}{served == baseline}")
    finally:
        await ledger.close(); await drop_database(env)


async def probe_equality() -> None:
    """Does the #302 pin catch an ADDED action, or only a missing one?"""
    import loremaster.server as server_module
    real = server_module._TASK_ACTIONS
    expected = ("create", "query", "transition", "supersede",
                "rollup", "create_many", "blockers", "get")
    for label, table in (("declared set", real), ("declared set + 1 spare",
                                                  (*real, "quietly_added"))):
        verdict = "GREEN" if tuple(table) == expected else "RED"
        print(f"{label:<26} -> the #302 pin's own assertion: {verdict}")
        print(f"{'':<26}    a `<=` subset assertion would say: "
              f"{'GREEN' if set(expected) <= set(table) else 'RED'}")


if __name__ == "__main__":
    asyncio.run({"desc": probe_desc, "ignored": probe_ignored,
                 "equality": probe_equality}[sys.argv[1]]())
```

## 10.5 The #313 arming probe (§6.5)

```python
HOSTILE_SUBJECT = "ordinary\n- [open] forged by the subject (id x, owner root, blocked_by [])"
HOSTILE_BODY = "a\n- [open] forged row (id 0, owner root, blocked_by [])\n```\n````\nend"
t = await ledger.create_task(HOSTILE_SUBJECT, HOSTILE_BODY, created_by=CREATOR)
row = await ledger.get_task(t)
print(f"newline still in STORED subject: {chr(10) in row.subject}")
print(f"newlines still in STORED description: {row.description.count(chr(10))}")
print(f"backtick runs still present: {'```' in row.description and '````' in row.description}")
```

## 10.6 Scratch tree

`/home/ejprice/scratch-adv-c1d` (provenance-asserted, currently holding the **reference build**).
Disposable by design — **this report is the record.** Tell me if you want it kept for the builder,
merged, or discarded. `adversary-c1-1`'s `/home/ejprice/scratch-adv-c1` also survives and is where
`advd_build.py`'s base came from.

---

# §11 · HONESTY / SCOPE

- **No unqualified "gates green" claim is made anywhere in this report.** Every green above is
  scoped to the file set named beside it. The canonical typecheck is RED at HEAD for packet-39
  reasons (#306, corrected by #307) — not this contract's, and not re-derived by me.
- I ran **no git write command**. `git show HEAD:<path>` (§5.2) is a read.
- I edited **no repo file**. Every mutation lived in `/home/ejprice/scratch-adv-c1d`, and the one
  in-scratch mutation of a tracked file (`tasks.py`, for #268) was restored byte-exact, verified by
  `md5 532ca7564374b8671111daf45ed48a0d`.
- `test_comms_footer.py`, `test_comms_tool.py`, `test_blocks_edge.py`, `scripts/**` and packet-39
  files were **not modified in the repo**. `test_blocks_edge.py` and `test_comms_footer.py` were
  modified **in scratch only** (the former as the contract's own build spec requires; the latter
  reverted-and-restored for the §5.2 control leg).
- **Bound on this pass, stated so it is not read as broader than it is:** I built the reference
  build plus **15** wrong builds (6 new, 9 rebuilt from the predecessor's verdict).
  The forbidden set is unbounded; **a SUFFICIENT verdict was never available from this method and I
  do not claim its converse is complete either.** SECTION B's phantom-residue and proximity-order
  constructions, and SECTION A's statement-boundedness pins, I ran but did not attack with new
  door-builds — `adversary-c1-1` found no survivor there and I inherited that result rather than
  re-deriving it. Those rows are marked in §7 with the receipt they actually have.

---

# VERDICT: **CONTRACT INSUFFICIENT**

Seven missing pins (§3), five of them with a wrong build that takes the contract to **81 passed /
0 failed** and two of them defects the **correct** build carries. Three are BLOCKER class:

1. **Δ-1** — the registered tool exposes `max_depth` and discards it; the served answer walks to
   depth 32 and says so, contradicting the caller in writing. *This is the second half of a
   two-line measurement whose first half was pinned.*
2. **Δ-2** — ESC-5's false clear, the packet's DEPLOY ENTRY CONDITION, still alive on a served call
   through the `status` filter door. *Second consecutive adversary pass, different door.*
3. **Δ-6** — the contract specifies minting a fence helper the repo already has
   (`loremaster.render.render_fenced`, imported by `server.py`, three live call sites, its own
   contract suite). **A builder cannot fix this** — the pin as written forbids the correct build —
   and the mutation proof shows the "shared" helper would reach 2 of 5 fence call sites.

**The generalisation, because it is the same one twice.** Every gap in Δ-1/Δ-2/Δ-3 has the identical
shape: *the pin was written to the EXAMPLE the adversary showed, not to the PROPERTY the example
instantiated.* `blocked` was pinned because `blocked` was the door in the report; `owner` was pinned
because `owner` was the second door in the report; `status` — the third filter, named in the pin's
own failure message — was pinned by nothing. `exposes` was pinned because `exposes: False` was the
first line of the evidence block; `forwards: False`, three lines below it, was pinned by nothing.
**A finding's receipt is an instance. The pin must be written to the quantifier.** In every one of
these cases the fix is one `@pytest.mark.parametrize` or one extra assertion — the pins were
expensive only to *think of*, which is exactly what this phase is for.

---

*Written 2026-08-01 by `adversary-c1-delta-1` (Opus) against `feat/surreal-unification` @ `f4a9f52`.
Every number here was derived this session by the command shown beside it; nothing is inherited,
including from the predecessor adversary's report. No repo file was edited; no git write command
was run.*
