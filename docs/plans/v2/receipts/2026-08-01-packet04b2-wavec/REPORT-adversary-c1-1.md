# REPORT-adversary-c1-1 — the CONTRACT ADVERSARY's grading of slice **C1** (04b-2 wave C)

brief-base v9 read
brief project v7 read

*Every measurement below was taken 2026-08-01 against `feat/surreal-unification` @ `025c2a9`
(the commit that landed C1), in a provenance-asserted scratch copy. "RED/GREEN today" means
at that commit. ⚠ A sibling agent advanced HEAD to `c5ca6f2` while I ran; I re-checked, and
`git diff --stat 025c2a9 c5ca6f2 --` over the three C1 files is **EMPTY**, so every verdict
below applies unchanged at `c5ca6f2`.*

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline — SEVEN wrong builds take contract C1 to `48 passed / 0 failed`.** Three are
  BLOCKER class: (1) **ESC-5's own false clear survives on a served path** — a dispatcher
  routing only `blocked is None` through the new seam serves `action=query blocked=false
  limit=5` with no disclosure; (2) **the chain render's truncated and complete worlds are
  byte-identical** (the contract's two-world leg is satisfied by the id COUNT differing, and
  its depth assertion by a hex digit); (3) **the whole new surface is UNREACHABLE through the
  registered MCP tool** — my reference build passes C1 48/48 *and* `test_mcp_server.py`
  641/641 while `lore_tasks` exposes no `max_depth` and its served description never names
  `blockers`.
- **state: done.** Independent reference build from the contract's own build spec →
  **48 passed / 0 failed** (the satisfiability receipt reproduced, §2.1). RED at HEAD
  reproduced exactly: **35 failed / 13 passed**, every failure for the right reason (§6).
  #268's tightened instrument **verified: 6/6 deterministic RED** under its named mutation (§7).
- **deviations:** none. No repo file was edited; no git command was run.
- **Packages considered:** *has-more pagination over the store read* → **bespoke** (READ:
  live `AsyncWsSurrealConnection` — **33** public methods, zero page/cursor/limit/offset/next;
  author reported 32) · *two-world line diff* → **bespoke, minimal** (READ: `difflib` exports)
  · *id normaliser* → **replace, stdlib `re`** · *cycle enumeration* → **not this slice** ·
  ⚠ **DIFF: serve-cap validation → `replace_with_adapter`, `pydantic` 2.13.4** — measured live,
  `TypeAdapter(Annotated[PositiveInt, Strict()])` rejects `0`, `-1` **and** `True` and names
  `input_value`; the author's table carries this row as *"reuse, not a package question"* with
  an in-repo read and **no package read column** (§9).
- **MISSING PINS: 8 families, all WRITTEN and measured in BOTH directions** — 64/64 green
  together with the contract on a fully-wired correct build, and each one RED on exactly its
  own wrong build and nothing else (§3, §4). The file is pasted verbatim in §10.
- **decisions-needed:** whether MP-1 (the served-tool reach) is C1's to close or a wave-exit
  item — it is the largest and the only one that touches a file outside C1's three (§3.1).
- **receipt pointers:** §1 the seven survivors · §2 provenance + controls · §3 the missing
  pins, one per finding · §4 the both-legs matrix · §5 the quantifier table · §6 RED honesty
  · §7 #268 verified · §8 corpse + removed-behaviour sweeps, item by item · §9 package diff ·
  §10 the instruments, verbatim · §11 residuals, each with its own verdict.

---

# §1 · P1 — THE WRONG BUILDS, AND WHAT THE CONTRACT WAVED THROUGH

Every variant is the SAME reference build with exactly ONE thing changed, so a surviving pin
set names precisely one missing pin. All seven were built by `adv_build.py` (§10.1) in
`/home/ejprice/scratch-adv-c1`, whose provenance is asserted in §2.1.

| # | wrong build | C1 result | the defect, MEASURED |
|---|---|---|---|
| **WB-1** | `tasks(action='query')` routes only the `blocked is None` branch through `_task_listing`; the blocked branch keeps `query_tasks` + `_render_task_rows` | **48 passed** | `blocked=false limit=5` over 40 unblocked tasks renders **no disclosure line**; the same question without the filter renders one |
| **WB-2** | the chain render carries ids only — no `truncated`, no `max_depth_used` | **48 passed** | a walk that STOPPED AT ITS BOUND and one that completed render **byte-identically** (normalised) |
| **WB-3** | *(the reference build itself)* — the MCP-registered `lore_tasks` tool is never wired | **48 passed** + `test_mcp_server.py` **641 passed** | `max_depth` absent from the tool's `inputSchema`; served `action` description names six actions, not `blockers` |
| **WB-4** | `_task_listing` drops the caller's `owner` filter | **48 passed** | `owner='alice'` served **6** rows where the ledger says **1** matches — with a bound disclosure about a population the caller never asked about |
| **WB-5** | the disclosure line hard-codes the cap the render pins use | **48 passed** | `limit=2` serves 2 rows and discloses *"showing **5** of more"* — a fabricated served number |
| **WB-6** | `ClaimResult.superseded_blockers` is never populated; the DISPATCHER does its own second read | **48 passed** | `ledger.claim_task()` returns `superseded_blockers={}` on a loss whose blocker WAS superseded |
| **WB-7** | the `max_depth` refusal names only `action='create'` | **48 passed** | `action='query' max_depth=3` **accepted and silently ignored** |
| **WB-8** | the supersede render drops the successor id | **48 passed** | `superseded task X (status open)` — the id the caller's next move needs is gone |
| — | `wb-private-limit` (the seam hand-rolls a second copy of the cap validator) | **48 passed** | see §3.7: proven by MUTATION, not by survival |
| ✅ | `wb-drop-blocked` (`_task_listing` drops the `blocked` filter) | **1 failed / 47 passed** | **CAUGHT** by `TestTheDisclosureIsUNIFORMAcrossBOTHFilterPaths` — the contract does discriminate here |

Raw tails, in order (`uv run pytest tests/test_task_read_surface.py -n auto -q`):

```
############ VARIANT: wb-blocked-seam     48 passed in 6.07s
############ VARIANT: wb-drop-owner       48 passed in 6.11s
############ VARIANT: wb-confident-chain  48 passed in 6.40s
############ VARIANT: wb-maxdepth-create  48 passed in 11.41s
############ VARIANT: wb-dead-typed-field 48 passed in 8.48s
############ VARIANT: wb-supersede-drops-successor 48 passed in 8.03s
############ VARIANT: wb-hardcoded-cap    48 passed in 7.15s
############ VARIANT: wb-private-limit    48 passed in 8.04s
############ VARIANT: wb-drop-blocked      1 failed, 47 passed in 7.02s   <-- CAUGHT
```

---

# §2 · P0 — MY OWN CONTROLS, BECAUSE AN AUDITOR'S INSTRUMENT LIES THE SAME WAY

## 2.1 Provenance (#140), and the satisfiability receipt REPRODUCED

```
./scripts/scratch_copy.sh /home/ejprice/scratch-adv-c1
scratch copy READY: /home/ejprice/scratch-adv-c1
  loremaster  -> /home/ejprice/scratch-adv-c1/loremaster/loremaster/__init__.py
```
Every probe below re-printed `loremaster.__file__` and it resolved inside the scratch tree.

I did **not** reuse the contract author's reference tree — I built my own implementation from
the contract's own build spec (the module docstring's *"THE PRODUCTION SURFACE THIS CONTRACT
DEFINES"*), which is precisely what a builder will do. That build is the control:

```
$ uv run pytest tests/test_task_read_surface.py -n auto -q
48 passed in 6.18s
```

**So the author's satisfiability receipt reproduces on an independently-authored build**, and
my harness demonstrably reaches the store, the seams and the pins.

## 2.2 Two probes of mine that failed for the WRONG reason, caught before they were believed

1. `wb-private-limit` first reported **4 failed** — I read it as *"the contract catches the
   private copy"*. It did not: my variant raised `TaskLedgerError` in `server.py` where the
   name was never imported, so the pins died on `NameError`. Fixed (import added) → **48
   passed**, i.e. the contract does **not** catch it. A survivor I would have mis-scored as a
   catch.
2. My first *"the DISPATCHABLE pin is vacuous"* probe added a spare key to `_COMMS_ACTIONS`,
   so the **equality** pin fired — not the dispatchability one. Re-run without the extra key
   (§3.6): the pin passes over a table whose `ack` dispatches to `None`.

## 2.3 The negative control for the whole probe set

`wb-drop-blocked` (last row of §1) is a wrong build the contract **does** catch, and
`ref + neutralised shared predicate` (§3.7) reddens 4 pins. So *"48 passed"* on the seven
survivors is a fact about those builds, not about a suite that cannot fail.

---

# §3 · THE MISSING PINS — each one *the test that should exist* + *the defect it catches*

All eight are written, in `test_adv_missing_pins.py` (§10.3), which is **scratch, never for
the repo** — the author owns where they land. Both legs measured in §4.

## 3.1 MP-1 (⚠ BLOCKER) — the new surface is UNREACHABLE through the REGISTERED tool

**The test that should exist:** `test_MISSING_the_served_tool_exposes_max_depth` and
`test_MISSING_every_declared_action_is_NAMED_in_the_served_text` — build the MCP server, list
tools, assert `lore_tasks`' `inputSchema.properties` carries `max_depth`, and that every name
in `_TASK_ACTIONS` appears in the tool's served text.

**The defect it catches:** every SECTION B pin drives `AppContext.tasks` through `_tool_seam`.
That is an **internal method**. The thing an agent calls is the module-level, FastMCP-registered
`tasks(context, action, …)` function, which has its own explicit parameter list, its own
forwarding call, and its own served `action` description. Measured on my reference build —
the one that passes C1 48/48:

```
MCP tool exposes 'max_depth' parameter: False
MCP tool forwards 'max_depth':          False
SERVED action description names 'blockers': False
internal _TASK_ACTIONS: ('create','query','transition','supersede','rollup','create_many','blockers')
AppContext.tasks accepts max_depth: True
```

and that same build takes the served-surface suite to **`641 passed in 102.34s`**. The
existing exact-set registration pin covers tool NAMES; the dead-name hygiene scan
(`test_every_lore_prefixed_token_in_served_text_is_a_live_tool_name`) covers the ABSENCE of
retired names. **Neither covers a live action that is never advertised.** Under THE CONSUMER
LAW the served description *is* the contract the agent learns, and a closed enumeration that
excludes `blockers` actively teaches that the action does not exist.

⚠ **This is finding #302's own quantifier failure.** #302 was *"the action vocabularies are
pinned by NOTHING"*; C1 closes it by pinning the **internal tuple** by equality — the door the
author walked through — and leaves the **served** half open, in the same slice that mints a
new action.

**Decision needed:** MP-1's fix touches the MCP tool function (in `server.py`, i.e. the
builder's file, but the *pin* would most naturally live in `test_mcp_server.py`, outside C1's
three files). Confirm whether C1 carries it or the wave exit does. It is satisfiable: §4 shows
64/64 green once the tool is wired.

## 3.2 MP-2 (⚠ BLOCKER) — ESC-5 at the TOOL, on the BLOCKED filter path

**The test that should exist:** `test_MISSING_a_blocked_filtered_TOOL_call_discloses_its_bound`
— `tasks(action='query', blocked=False, limit=cap)` and `tasks(action='query', limit=cap)` over
the same all-unblocked population must render the same non-row lines.

**The defect it catches:** `TestTheDisclosureIsUNIFORMAcrossBOTHFilterPaths` calls
`context._task_listing(...)` **directly**. A helper cannot be non-uniform with itself, so the
class proves the helper's arithmetic and nothing about the dispatcher's routing. **Nothing in
the whole tree drives `tasks(action='query')` with `status`, `owner` or `blocked`** — derived:

```
$ grep -rn 'tasks(action="query"' loremaster/tests/*.py | grep -E "owner|status|blocked"
(no hits)
```

WB-1 exploits exactly that. Its measured output, beside the correct build's:

```
--- WRONG BUILD: action=query limit=5 (no blocked filter) ---
- [open] claimable backlog item (id <id>, owner None, blocked_by [])   × 5
(showing 5 of more matching tasks — re-run with a larger limit to see the rest)
--- WRONG BUILD: action=query blocked=false limit=5 (SAME 40 rows, all unblocked) ---
- [open] claimable backlog item (id <id>, owner None, blocked_by [])   × 5
VERDICT: no-filter lines the blocked path lacks=['(showing 5 of more matching tasks — …)']
```

That is ESC-5's own false clear — the packet's DEPLOY ENTRY CONDITION — alive on a served
call, at 48/48.

## 3.3 MP-3 (⚠ BLOCKER) — the chain render's bound, over two worlds of the SAME SIZE

**The tests that should exist:**
`test_MISSING_two_walks_of_EQUAL_reach_still_disclose_their_bound` (a leaf over a 4-deep chain
walked at `max_depth=2` vs a leaf over a 2-deep chain walked at `max_depth=2` — both serve
exactly 2 ids; normalised bytes must differ) and
`test_MISSING_the_truncated_render_names_the_DEPTH_not_a_digit_in_an_id`.

**The defect it catches — two independent vacuities in one class:**

1. `assert deep != shallow` compares the SAME leaf at `max_depth=8` and `max_depth=2`. Those
   walks return **4 ids and 2 ids**, so the renders differ by the id list alone. The class
   docstring says WB-B1 (*"render `ids` and nothing else"*) is *"killed by the two-world leg"*
   — **it is not.** Measured on WB-2:
   ```
   --- TRUNCATED world: 4-deep chain walked at max_depth=2 ---   blockers of task <id>:  - <id>  - <id>
   --- COMPLETE  world: 2-deep chain walked at max_depth=2 ---   blockers of task <id>:  - <id>  - <id>
   GROUND TRUTH: truncated-world truncated=True · complete-world truncated=False
   VERDICT: normalised bytes IDENTICAL = True
   ```
   *"Identical bytes = a false clear = STOP"*, in the surface this wave mints, on a build the
   contract passes.
2. `assert "2" in shallow` — the render carries **96 opaque hex characters**. Measured on WB-2:
   ```
   "2" in shallow           = True    <-- what the pin asserts
   "2" in shallow-minus-ids = False   <-- whether the DEPTH is named
   P(no "2" among the 96 hex chars) = 0.00204
   ```
   So the assertion passes with probability ≈0.998 on a build that names **no depth at all**,
   while its own message reads *"the truncated render names no depth"*. That is the false-gate
   class, and it is also this repo's own instrument lesson (*a gate keyed on a literal,
   defeated by a substring*) — and on the other 0.2% it is a flake.

## 3.4 MP-4 — the render's disclosure names the CALLER's cap, not a literal

**The test that should exist:** `test_MISSING_the_disclosure_names_the_number_actually_served`,
parametrised over `[_LISTING_CAP, _ALT_CAP]`.

**The defect it catches:** `_ALT_CAP = 2` exists *because* of the monoculture law and reaches
the BIT and the STATEMENT — and **never reaches the RENDER**. Every render pin uses cap 5, and
`test_a_CAPPED_listing_renders_a_line_a_COMPLETE_one_does_NOT` asserts `str(_LISTING_CAP) in
disclosure[0]`. Measured on WB-5 (48/48 green):

```
ref  limit=5 -> '(showing 5 of more …)'   limit=2 -> '(showing 2 of more …)'
WB-5 limit=5 -> '(showing 5 of more …)'   limit=2 -> '(showing 5 of more …)'   <-- fabricated
```

A fabricated number on the one surface whose entire purpose is a trustworthy bound.

## 3.5 MP-5 — `max_depth` refused for EVERY other action

**The test that should exist:** the existing refusal pin, parametrised over all six
non-`blockers` actions.

**The defect it catches:** the contract tests `action='create'` only. WB-7 hard-codes that one
action; `action='query' max_depth=3` is then **accepted and silently ignored**:

```
ref   REFUSED: {'action':'query','max_depth':3} -> 'max_depth' applies only to action='blockers' …
WB-7  ACCEPTED (no refusal): {'action':'query','max_depth':3} -> [a normal task row]
```

`_TASK_ACTIONS_ACCEPTING_LIMIT` exists as a SET precisely so *"a caller passing `limit` to
`transition` is making a mistake and deserves to be told"*; the new parameter inherits the
discipline in prose only.

## 3.6 MP-6 — the fact must be TYPED STATE, and *"every declared action is DISPATCHABLE"*

**(a) The test that should exist:** `test_MISSING_a_LOSS_carries_the_superseded_blockers_on_the_RESULT`
— assert `result.superseded_blockers == {blocker: successor}` on a LOSS.

**The defect it catches:** the contract asserts the field EXISTS, that it DEFAULTS, and that a
WON claim leaves it empty. `test_a_WON_claim_carries_NO_superseded_blockers`' docstring claims
*"both directions are asserted — here, and in the loss leg above"* — but the loss leg asserts
about the **RENDER**, not the field. So an **always-empty** field satisfies every leg. WB-6
does exactly that, with the dispatcher performing its own second store read:

```
ref   claimed=False superseded_blockers={'5eb4fd32…': '7a7a2a57…'}
WB-6  claimed=False superseded_blockers={}      GROUND TRUTH: blocker … superseded by …
```

Every non-MCP consumer of `TaskLedger.claim_task` gets nothing, and the blocker policy has a
second implementation in the dispatcher — the exact thing
`test_the_claim_result_carries_the_superseded_blockers_as_TYPED_state`'s docstring forbids.

**(b) `test_every_declared_action_is_actually_DISPATCHABLE` is a FALSE GATE.** Its docstring
says *"Three equal tuples prove agreement between two constants, not that any action reaches a
handler"* — and then its assertions are `len(set(_TASK_ACTIONS)) == len(_TASK_ACTIONS)` and
`set(_COMMS_ACTIONS) == set(_EXPECTED_COMMS_ACTIONS)`, i.e. **agreement between two constants**.
Measured, running the pin's own assertions verbatim against a table whose `ack` dispatches
nowhere:

```
ack dispatches to: None
PIN VERDICT: PASSES — 'every declared action is actually DISPATCHABLE' is GREEN
equality pin still green: True
```

**The test that should exist:** resolve each declared action to its handler (`_COMMS_ACTIONS`
values are `CommsActionSpec`s — assert each is one, and for `_TASK_ACTIONS` assert each name
survives the dispatcher's unknown-action refusal), or rename the pin to what it checks.

## 3.7 MP-7 — ONE IMPLEMENTATION of the cap predicate, PROVEN BY MUTATION

**The rider that should exist:** the contract must demand a **mutation receipt** — neutralise
the shared `validated_task_limit` and require *every* caller's pins to redden.

**The defect it catches:** the author's report §8 states that
`TestTheCALLERSOwnLimitIsWhatGetsVALIDATED` *"is what makes a private second copy impossible to
ship green"*. **Measured — that claim is false:**

```
######## ref + neutralised shared predicate           -> 4 failed in 4.51s
######## wb-private-limit + neutralised shared predicate -> 4 passed in 4.39s
```

The pins are behavioural; a seam-side clone with the same rules satisfies them, and the
mutation that should have reddened every caller reaches none of them. Two aggravating facts:
(i) the contract's build spec — the *"PRODUCTION SURFACE THIS CONTRACT DEFINES"* list — **never
names `validated_task_limit` at all**, so a builder is not told to create it; (ii) at HEAD there
are exactly two `_validated_limit` sites, both in `tasks.py`, so the seam is a genuinely new
second call site. Duplication is a DESIGN decision (repo law), and nothing here forces it into
the open.

## 3.8 MP-8 — the supersede render still NAMES the successor

**The test that should exist:** `test_MISSING_the_render_names_the_successor_it_minted`.

**The defect it catches:** the contract's test is *named*
`test_superseding_a_task_with_dependents_NAMES_them_and_the_SUCCESSOR` and asserts only the
dependents; the local it calls `successor` is in fact `get_task(dependents[0])`. The successor
id is a **pre-existing served fact** of the branch this wave rewrites. WB-8 drops it, 48/48
green:

```
ref  'superseded task <id>; successor <id> (status open)'   render NAMES the successor = True
WB-8 'superseded task <id> (status open)'                   render NAMES the successor = False
```

---

# §4 · THE BOTH-LEGS MATRIX — every proposed pin, green on right and red on wrong

**Control leg (a correct build, tool wired):** the proposed pins and the contract, together:

```
$ uv run pytest tests/test_adv_missing_pins.py tests/test_task_read_surface.py -q
64 passed in 9.07s
```

So the pins are satisfiable, they do not contradict C1, and they demand nothing impossible.

**Negative legs** — each wrong build with the MCP tool wired, so only the variant's own defect
can fire (`pytest tests/test_adv_missing_pins.py -q --tb=no -rf`):

| wrong build | proposed pins that fired | others |
|---|---|---|
| `wb-blocked-seam` | `…::test_MISSING_a_blocked_filtered_TOOL_call_discloses_its_bound` | 15 passed |
| `wb-drop-owner` | `…::test_MISSING_the_tool_passes_the_OWNER_filter_through` | 15 passed |
| `wb-confident-chain` | `…::test_MISSING_two_walks_of_EQUAL_reach_still_disclose_their_bound` · `…::test_MISSING_the_truncated_render_names_the_DEPTH_not_a_digit_in_an_id` | 14 passed |
| `wb-maxdepth-create` | `…::test_MISSING_max_depth_is_refused_for_every_non_blockers_action[query,transition,supersede,rollup,create_many]` | 11 passed |
| `wb-dead-typed-field` | `…::test_MISSING_a_LOSS_carries_the_superseded_blockers_on_the_RESULT` | 15 passed |
| `wb-supersede-drops-successor` | `…::test_MISSING_the_render_names_the_successor_it_minted` | 15 passed |
| `wb-hardcoded-cap` | `…::test_MISSING_the_disclosure_names_the_number_actually_served[cap-2]` | 15 passed |
| reference build, tool NOT wired | `…::test_MISSING_the_served_tool_exposes_max_depth` · `…::test_MISSING_every_declared_action_is_NAMED_in_the_served_text` | 14 passed |

No pin fired on a build it was not written for. That is the discrimination property the
contract's own fixtures are missing in eight places.

---

# §5 · P1b — THE QUANTIFIER TABLE (every invariant classified, every "guarded" row with a receipt)

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| A1 | `TaskListing`'s field set is exactly `(rows, more)`, extras refused | **∀** over the model | attempted door: a third field — killed by equality + a live `ValidationError`. No survivor. |
| A2 | `more` is TRUE **iff** a further matching row exists | **GUARDED** — ∀ over population × 2 caps, but only through `_task_listing` called DIRECTLY | **BLOCKER: WB-1 survives** (§3.2) |
| A3 | the disclosure is UNIFORM across both filter paths | **GUARDED to the helper**, not to the dispatcher | same receipt as A2 |
| A4 | a capped listing serves at most `cap` rows | **∀** over 2 caps × {cap, cap+1} | door-build: serve the over-fetched row → killed by `len(listing.rows) == cap` |
| A5 | the emitted statement is bounded at `cap+1`, in ONE round trip | **∀** — 2 caps + an order-of-magnitude growth pair | door-builds WB-A6 (`count()`) and WB-A7 (unbounded probe) both die on `seam.calls`/`seam.rows`. No survivor. |
| A6 | `limit=None` emits NO `LIMIT` clause | **∀**, with a positive control | door-build: always emit + bind `None` → killed. No survivor. |
| A7 | an illegal `limit` is refused NAMING the caller's value | **∀** over `{-1, 0, True}` | behaviour has no hole; **the ONE-IMPLEMENTATION rider does** — `wb-private-limit` + neutralised shared predicate stays **4 passed** (§3.7) |
| A8 | the RENDER discloses the bound, both directions | **GUARDED to one cap value (5)** | **WB-5 survives**; `limit=2` discloses "5" (§3.4) |
| A9 | the render takes the bit as TYPED applicability and never recomputes | **∀** over the typed bit, both directions, rows held constant | door-build: derive from `len(rows)` → killed. The strongest pin in the file. |
| A10 | an empty listing renders exactly `_render_task_rows([])` | **∀** | no survivor |
| B1 | the chain render NAMES its own bound | **GUARDED — and vacuous**: `deep != shallow` rides the id COUNT, `"2" in shallow` rides a hex digit | **BLOCKER: WB-2 survives**; the two worlds are byte-identical (§3.3) |
| B2 | served ids RESOLVE and keep proximity order | **∀** over the chain, on a fixture whose proximity order reverses creation order | door-build: `str(record).split(':')` → killed. No survivor. |
| B3 | an id naming nothing ≠ an id with no blockers | **∀** (both cases forced) | no survivor |
| B4 | the phantom residue is NAMED, and only when it exists | **∀** over three worlds (phantom / honest / free), residue DERIVED not matched | no survivor — the best construction in the file |
| C1 | `supersede` warns **iff** dependents exist | **∀** both directions, byte-compared | door-build WB-C1 (unconditional) → killed |
| C1b | the supersede render names the SUCCESSOR | **UNPINNED** (the test name promises it; no assertion performs it) | **WB-8 survives** (§3.8) |
| C2 | the claim render names a superseded blocker AND its successor | **∀** both directions (superseded + ordinary-with-decoy) | door-builds WB-C3/WB-C4 → killed |
| C3 | that fact travels as TYPED state | **GUARDED — existence + default + empty-on-WIN only** | **WB-6 survives**; the field is always `{}` (§3.6a) |
| D1 | the three action vocabularies are EXACTLY the declared sets | **∀** over the three INTERNAL tuples | internally sound; **the SERVED text is unguarded → BLOCKER MP-1** (§3.1) |
| D2 | every declared action is DISPATCHABLE | **VACUOUS** — the assertions compare two constants | pin stays GREEN over `_COMMS_ACTIONS['ack'] = None` (§3.6b) |
| D3 | `max_depth` is refused for every other action | **GUARDED to `action='create'`** | **WB-7 survives** (§3.5) |
| D4 | `limit` is STILL refused for `blockers` | **∀** (one action, and it is the one that matters) | no survivor |
| X1 | the task surfaces agree with each other and with the CAS | **∀** within the fixture's stated terminal-blocker restriction (a ruled difference, correctly excluded) | no survivor |
| #268 | a cap never shrinks the candidate scan | **∀**, comparative and self-normalising, with an independent positive control | **verified 6/6 deterministic RED** under the named mutation (§7) |

---

# §6 · P7 — RED HONESTY AT HEAD, REPRODUCED AND CLASSIFIED

```
$ cd loremaster && uv run pytest tests/test_task_read_surface.py -n auto -q
35 failed, 13 passed in 6.27s          # at 025c2a9, working tree
```

Matches the author's claim exactly (35/13, and 35+13 = 48). The failure reasons, counted:

```
14  AttributeError: 'AppContext' object has no attribute '_task_listing'
 5  ImportError: cannot import name 'TaskListing' from 'loremaster.tasks'
 5  ValueError: unknown task action 'blockers'; valid actions are [...]
 3  TypeError: AppContext.tasks() got an unexpected keyword argument 'max_depth'
 8  AssertionError — each naming a behaviour that does not exist yet
    (supersede warns / claim names the superseded blocker / ClaimResult carries the field /
     _TASK_ACTIONS lacks 'blockers' / the chain render is absent)
```

**No import typo, no fixture error, no bad path.** Every RED is RED for the right reason, and
the 13 GREEN are the removed-behaviour guards the author enumerated. `test_query_tasks_bounded.py`
is **41 passed** at HEAD (author's figure; I re-ran its `#268` class: **4 passed**).

⚠ **Scope, stated:** the canonical typecheck is RED at HEAD for packet-39 reasons (#306) —
not this contract's. I make **no unqualified gates-green claim**; every green above is scoped
to the file set named beside it.

---

# §7 · P4 — THE AUTHOR'S CLAIMS, RE-DERIVED RATHER THAN RELAYED

| claim | verdict | receipt |
|---|---|---|
| the contract is satisfiable — 48/0 on a correct build | **CONFIRMED** on an independently-authored build | §2.1 |
| RED at HEAD = 35 failed / 13 passed | **CONFIRMED, exactly** | §6 |
| #268's named mutation now fires deterministically (author: 8/8) | **CONFIRMED — 6/6** | below |
| `tasks.py` md5 after mutation-restore = `532ca75…` | **CONFIRMED** (my restore produced the identical hash) | below |
| `transitive_blockers` has 0 prod / 0 test consumers | **CONFIRMED** by grep over `loremaster/` and the test tree | §8 |
| *"`TestTheCALLERSOwnLimitIsWhatGetsVALIDATED` makes a private second copy impossible to ship green"* (report §8) | **FALSE** | §3.7 |
| SDK has no pagination helper — "32 methods" | **verdict CONFIRMED, count differs**: I read **33** public methods; zero pagination-ish names either way | §9 |

#268, control then mutation (`limit=None if blocked is not None else cap` → `limit=cap`):

```
CONTROL (unmutated):  4 passed in 0.97s
run 1: 2 failed, 2 passed   run 2: 2 failed, 2 passed   run 3: 2 failed, 2 passed
run 4: 2 failed, 2 passed   run 5: 2 failed, 2 passed   run 6: 2 failed, 2 passed
FAILED …::test_a_capped_BLOCKED_query_serves_the_FULL_cap_when_the_answer_is_bigger
FAILED …::test_a_SHORT_answer_means_the_scan_was_EXHAUSTED_never_silently_truncated
tree restored: md5 532ca7564374b8671111daf45ed48a0d  loremaster/loremaster/tasks.py
```

The author's *split* also reproduces: across three runs of the single leg, the **traffic**
assertion fired twice (*"the blocked-partition scan read 61 rows under a cap of 60 and 67 rows
with no cap"*) and the **outcome** assertion once (*"a capped query served 5 tasks and the SAME
query with no cap served 6"*). So the traffic leg is genuinely carrying the ≈45% of runs where
the outcome comparison is blind. **The #268 instrument discriminates; I could not break it.**
Its positive control is a genuinely independent direction (the `blocked is None` path, where
R5 puts the `LIMIT` in the statement), so the negative result is not from a blind instrument.

---

# §8 · P6 / P6b — THE SWEEPS, EVERY HIT WITH ITS OWN VERDICT

## 8.1 Corpse sweep — assertions still pinning the retired world

`grep -rn "TestACappedListingDISCLOSESNothingAboutItsOwnBOUND\|_PARTIAL_WORLD_POPULATION\|_normalise_task_render"` over `loremaster/tests/`:

| hit | verdict |
|---|---|
| `test_query_tasks_bounded.py` HOLE-8 comment block (2 mentions) | **CLEAN** — prose, explicitly headed as the preserved record of a deleted class |
| `test_task_read_surface.py::TestTheRenderedListingDISCLOSESItsOwnBOUND` docstring | **CLEAN** — the successor citing its predecessor |
| `test_blocks_edge.py` Leg-1 table, *"`TestACappedListingDISCLOSESNothingAboutItsOwnBOUND` **constructs** both worlds and **reddens** the day the disclosure lands"* | ⚠ **RESIDUAL** — present tense, naming a class C1 DELETES, in a file this slice does not own and which #279 is editing concurrently. Not a green-test corpse (it is a comment), but it is the natural-language-surface class this repo has receipts against. **Exact edit:** change to *"…constructed both worlds; CLOSED by 04b-2 wave C, successor `test_task_read_surface.py::TestTheRenderedListingDISCLOSESItsOwnBOUND`."* |
| `_normalise_task_render` | **CLEAN** — exactly ONE definition survives (in `test_task_read_surface.py`); `test_query_tasks_bounded.py`'s only remaining mention is inside the HOLE-8 comment. The move is complete, no orphan. |
| `test_the_TOOL_SEAM_passes_the_limit_through_to_the_ledger` (counts `"- "` lines) | **CLEAN** — the disclosure line cannot break it; the contract's `_rendered_rows` docstring cites this pin by name and is correct. |
| any assertion on the unknown-action teaching list | **NONE EXIST** — `grep -rn "valid actions are" loremaster/tests/` returns nothing. So widening `_TASK_ACTIONS` changes a served teaching string that no pin observes. Related to MP-1; folded there. |

## 8.2 P6b — removed-behaviour inventory, enumerated from the SOURCE first, then diffed

I enumerated the replaced code's observable behaviours from `server.py` **before** reading the
contract's own adjudications (the contract's *"TWO EDITS THE BUILDER MUST MAKE"* block is the
nearest thing to a Phase 0 inventory this slice has; my brief names no separate inventory file).

| # | behaviour of the code being REPLACED | adjudicated by the contract? | pinned? |
|---|---|---|---|
| 1 | the `query` branch forwards `status` to `query_tasks` | **no** | **no** — MP-4's owner leg covers the class; `status` specifically remains unpinned |
| 2 | the `query` branch forwards `owner` | **no** | **no → WB-4** (§3.1/§3.2) |
| 3 | the `query` branch forwards `blocked` | implicitly, via the uniformity class | at the HELPER only (`wb-drop-blocked` caught; WB-1's routing not) |
| 4 | the `query` branch forwards `limit` | yes | yes (pre-existing tool-seam pin + C1) |
| 5 | the `query` branch renders through `_render_task_rows` | yes, explicitly | yes — `test_an_EMPTY_listing_…` asserts equality with `_render_task_rows([])` |
| 6 | the `supersede` branch names the PREDECESSOR | no | weakly — the quiet leg asserts one line, not its content |
| 7 | the `supersede` branch names the SUCCESSOR + `(status open)` | **no** | **no → WB-8** (§3.8) |
| 8 | `_render_claim_result`'s `blocked_by [...] unresolved` shape | yes (re-authored) | yes |
| 9 | `_render_claim_result`'s `superseded by X` (the task's OWN supersession, finding #7) | named in a docstring; used only as a fixture guard | **no** — `grep -rn "unowned but not claimable" loremaster/tests/` returns **zero hits**, so the whole loss-render family had no text pin before C1 and still has none for this shape. **RESIDUAL** |
| 10 | `_render_claim_result`'s `status X` fallback shape | no | **no** — same grep, same verdict. **RESIDUAL** |
| 11 | `TaskLedger._validated_limit` is the ONLY cap policy | asserted in the report, not in the contract | **no → §3.7** |
| 12 | the DELETED known-bound class's virtue (a two-world byte comparison) | yes, explicitly, with the wave-report sentence | **yes** — preserved and inverted by the successor. Correctly done. |

---

# §9 · P-PKG — MY TABLE, BUILT AND THEN DIFFED AGAINST THE AUTHOR'S

⚠ **Honesty about my own frame:** the brief required me to read the author's report, which
carries its §8 table, so my enumeration is **not blind**. What I can and did do independently
is attack the *what I READ* column — which is where brief-base says the failures actually live.

| mechanism | libraries evaluated | what **I** READ (live, this session) | my verdict | vs author |
|---|---|---|---|---|
| has-more / pagination over a SurrealDB read | `surrealdb` SDK | `dir(AsyncWsSurrealConnection)` → **33** public methods; filtered for page/cursor/limit/offset/more/next/paginat → **0 hits**; top-level `dir(surrealdb)` → 0 hits | **bespoke** | **AGREE** on verdict; their count is 32, mine 33 — a re-derived number that differs, immaterial to the verdict but recorded |
| two-world line diff (a TEST helper) | `difflib` (stdlib) | `dir(difflib)`; `unified_diff` / `Differ` emit two-letter-prefixed deltas a test must re-parse | **bespoke, 2 lines** | **AGREE** |
| id normalisation in a render comparison | `re` (stdlib) | the inherited helper | **replace** | **AGREE** |
| all-cycle enumeration | `networkx` / `graphlib` | routed to 04b-3 by ruling | **not this slice** | **AGREE** |
| **serve-cap validation (`validated_task_limit`)** | **`pydantic` 2.13.4** (already a hard dependency) | measured live: `TypeAdapter(Annotated[PositiveInt, Strict()])` → `5`→`5`; `0`→REJECTED `greater_than`; `-1`→REJECTED `greater_than`; **`True`→REJECTED `int_type`** (lax mode coerces `True`→`1`, so `Strict()` is load-bearing). Errors carry `input_value=…`. | **`replace_with_adapter`** — pydantic supplies all three T2 refusals and names the value; the adapter is the `TaskLedgerError` wrapper and the project's own sentence | ⚠ **DIFF** — the author's row reads *"reuse, not a package question"*, read-column `TaskLedger._validated_limit, read this session`. That is an **in-repo** read where the house rule is *"pydantic at every validated boundary"*, and it is the empty-package-read-column shape brief-base names |
| depth-bounded upstream walk | engine-side `+collect` | existing `transitive_blockers` | **keep** — not new this slice | not in author's table (correctly — it predates the slice) |
| reverse dependency lookup (`direct_dependents`) | `surrealdb` SDK | same read as row 1 — no helper above raw SurrealQL | **bespoke** (a `WHERE $id IN blocked_by`) | not in author's table |

**Diff result: one row.** No mechanism the contract specifies as `bespoke` turns out to be
covered by a library — except the cap validator, which the survey did not treat as a package
question at all. Not a blocker; worth a row and a sentence in the contract.

---

# §10 · THE INSTRUMENTS (brief-base §1 — pasted, because scratch is a plan to lose them)

Three files, all authored in `/home/ejprice/scratch-adv-c1` (disposable by design; **not the
record**). They are reproducible from the text below plus `./scripts/scratch_copy.sh`.

## 10.1 `adv_build.py` — the reference build and the wrong variants

Applies the C1 build spec to a scratch copy, with one deliberate defect per variant. Full
source is long; the load-bearing parts are reproduced here and the whole file can be rebuilt
from the contract's own build spec plus these deltas.

```python
# the reference build (all variants start here, then change exactly one thing)
#   tasks.py:  + validated_task_limit(limit)          (module-level, shared)
#              + class TaskListing(rows: list[Task], more: bool, extra="forbid")
#              + ClaimResult.superseded_blockers: dict[str,str] = Field(default_factory=dict)
#              + TaskLedger.direct_dependents / TaskLedger._superseded_among
#              ~ TaskLedger._validated_limit -> `return validated_task_limit(limit)`
#              ~ claim_task -> `superseded = {} if won else await self._superseded_among(blocked_by)`
#   server.py: + _TASK_ACTION_BLOCKERS / _TASK_ACTIONS_ACCEPTING_MAX_DEPTH
#              + AppContext._task_listing / _render_task_listing / _render_transitive_blockers
#              ~ tasks(): max_depth param + guard, query branch -> _task_listing,
#                blockers branch, supersede branch + dependents warning
#   test_blocks_edge.py: NON_WRITING_VERBS / VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH += "direct_dependents"

    async def _task_listing(self, *, status, owner, blocked, limit) -> TaskListing:
        cap = validated_task_limit(limit)                       # BEFORE the +1 — #310
        if cap is None:
            rows = await self.task_ledger.query_tasks(
                status=status, owner=owner, blocked=blocked, limit=None)
            return TaskListing(rows=rows, more=False)
        fetched = await self.task_ledger.query_tasks(
            status=status, owner=owner, blocked=blocked, limit=cap + 1)
        return TaskListing(rows=fetched[:cap], more=len(fetched) > cap)

    @classmethod
    def _render_task_listing(cls, listing: TaskListing) -> str:
        rendered = cls._render_task_rows(listing.rows)
        if not listing.more:
            return rendered
        return (f"{rendered}\n(showing {len(listing.rows)} of more matching tasks — "
                f"re-run with a larger limit to see the rest)")

    @staticmethod
    def _render_transitive_blockers(task: Task, blockers: TransitiveBlockers) -> str:
        lines = [f"blockers of task {task.id} (walked to depth {blockers.max_depth_used}):"]
        lines.extend(f"- {blocker}" for blocker in blockers.ids)
        residue = [e for e in task.blocked_by if e not in set(blockers.ids)]
        if residue:
            lines.append(f"! {len(residue)} blocked_by entry/entries carry NO edge and can "
                         f"never resolve — the claim CAS counts them forever: {residue}")
        if blockers.truncated:
            lines.append(f"! the walk stopped at its bound of {blockers.max_depth_used} and "
                         f"more upstream remains — re-run with a larger max_depth")
        if not blockers.ids and not residue:
            lines.append("(nothing is blocking this task)")
        return "\n".join(lines)

# THE WRONG BUILDS — each is the above with ONE change:
# wb-blocked-seam   query branch: `if blocked is None: <_task_listing path>` else old path
# wb-drop-owner     _task_listing passes `owner=None` on the capped read
# wb-drop-blocked   _task_listing passes `blocked=None` on the capped read   (CAUGHT)
# wb-hardcoded-cap  the disclosure interpolates a literal 5, not len(listing.rows)
# wb-confident-chain _render_transitive_blockers drops the header depth AND the truncated line
# wb-maxdepth-create the guard is `if action == _TASK_ACTION_CREATE and max_depth is not None`
# wb-dead-typed-field claim_task never sets the field; the DISPATCHER re-reads and stamps a
#                     private attribute the render reads instead
# wb-supersede-drops-successor  the head line omits `; successor {successor_id}`
# wb-private-limit  _task_listing calls AppContext._private_validated_limit (a byte-copy)
```

`adv_neutralise.py` — the sharing mutation (§3.7):
```python
from pathlib import Path
p = Path("loremaster/loremaster/tasks.py"); t = p.read_text()
old = ('    if limit is None:\n        return None\n'
       '    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:\n'
       '        raise TaskLedgerError(\n'
       '            f"limit={limit!r} is out of range — it must be a positive integer "\n'
       '            f"naming how many tasks to serve, or be omitted for every match"\n'
       '        )\n    return limit')
assert t.count(old) == 1
p.write_text(t.replace(old, "    return None if limit is None else 1"))
```

`adv_wire_tool.py` — the MP-1 control leg: adds `max_depth: Annotated[int | None, Field(...)]`
to the **registered** `tasks` tool, forwards it to `_app_context(context).tasks(...)`, and
extends the served `action` description with `'blockers'`.

## 10.2 `adv_demo.py` / `adv_demo2.py` / `adv_demo3.py` — the defect demonstrations

Standalone async probes that build a `TaskLedger` on a throwaway database
(`_surreal_harness.unique_database()`), wire an `AppContext.__new__` seam, and print the
observed behaviour so a wrong build's survival can be scored as a DEFECT rather than as an
equivalent implementation. Probes: `blocked-seam`, `drop-owner`, `confident-chain`,
`maxdepth`, `dead-typed-field`, `supersede-successor`, plus the fabricated-number probe and
the `"2" in shallow` id-digit probe (whose output appears in §3.3). Each prints
`loremaster.__file__` first.

⚠ **One probe of mine that could not see what it claimed, removed rather than reported:** my
first sharing probe monkey-patched `loremaster.tasks.validated_task_limit` at runtime — which
cannot reach `server.py`'s `from … import` binding, so it would have printed *"the seam did not
notice"* for the CORRECT build too. Replaced by the source-level mutation in §3.7, which has
both legs.

## 10.3 `test_adv_missing_pins.py` — the eight missing pins, written

Structure (full assertions in §3; the file is 16 tests in 7 classes):

```
TestTheNewSurfaceIsREACHABLEThroughTheREGISTEREDTool
    test_MISSING_the_served_tool_exposes_max_depth
    test_MISSING_every_declared_action_is_NAMED_in_the_served_text
TestTheRenderedDisclosureNamesTheCALLERSCapNotALiteral
    test_MISSING_the_disclosure_names_the_number_actually_served[cap-5, cap-2]
TestATruncatedWalkAndACompleteWalkOfTheSameSizeDIFFER
    test_MISSING_two_walks_of_EQUAL_reach_still_disclose_their_bound
    test_MISSING_the_truncated_render_names_the_DEPTH_not_a_digit_in_an_id
TestTheDisclosureSurvivesTheFILTERSAtTheServedSeam
    test_MISSING_a_blocked_filtered_TOOL_call_discloses_its_bound
    test_MISSING_the_tool_passes_the_OWNER_filter_through
TestTheNewParameterIsRefusedForEVERYOtherAction
    test_MISSING_max_depth_is_refused_for_every_non_blockers_action[6 actions]
TestTheSupersededBlockerFactIsTYPEDStateNotARenderSideRead
    test_MISSING_a_LOSS_carries_the_superseded_blockers_on_the_RESULT
TestTheSupersedeRenderStillNamesTheSUCCESSOR
    test_MISSING_the_render_names_the_successor_it_minted
```

It imports the contract's own vocabulary (`_ALT_CAP`, `_LISTING_CAP`, `_SURPLUS_POPULATION`,
`_extra_lines`, `_rendered_rows`, `_normalise_task_render`, `_seed_identical_tasks`) plus
`_fresh_ledger` / `_tool_seam`, so the pins land in the file's own idiom with no new fixture
vocabulary. The two MP-1 pins use `test_mcp_server`'s `_config` / `_slug` + `build_mcp_server`
+ `mcp.list_tools()` — the repo's existing served-surface idiom.

---

# §11 · RESIDUALS — everything I noticed, each with its OWN verdict

1. **P5 — the test DOUBLE cannot fail.** `FakeTaskLedger.direct_dependents` was added by this
   contract ahead of the production verb. Measured: neutralised to `return []`,
   `test_mcp_server.py -k TasksTool` stays **5 passed** and C1 stays **48 passed**. Its entire
   function is to prevent an `AttributeError`; **no pin anywhere asserts its answer**, and
   there is no agreement pin between the double and its production twin (it was adjudicated
   into `NON_WRITING_VERBS`, so it owes no mirror pin either). `_task_fakes.py` restored
   byte-exact — md5 `6e19f17cb5723b1607c1373bdd48ee37`, identical to the repo copy.
   **VERDICT: real gap, low blast radius today, guaranteed to matter the first time a
   `[fake]`-parametrised pin drives the supersede warning.**
2. **`test_blocks_edge.py`'s present-tense citation of the deleted class** — §8.1, with the
   exact edit. **VERDICT: fix during the wave; the file is live under #279, so it needs the
   lead's sequencing, not mine.**
3. **The claim render's other two loss shapes are pinned by NOTHING, before or after this
   wave** (`grep -rn "unowned but not claimable" loremaster/tests/` → zero hits). §8.2 rows
   9–10. **VERDICT: pre-existing, widened by this wave's rewrite of the branch; worth one pin
   in C1 since the branch is already being edited.**
4. **R9's default display cap is still unbuilt and unpinned** — the author's decision-needed
   #3 and finding #309. I re-derived it: `_render_task_rows` renders every row and no display
   cap exists on the task read path. **VERDICT: CONFIRMED, and it interacts with ESC-5** — an
   uncapped `action=query` over a large ledger renders every row with no line at all, which
   is *correct* under this contract and *contradicts* R9. Operator ruling territory.
5. **`_ALT_CAP` reaches the bit and the statement, never the render** — MP-4. Also worth
   noting the general form: **this contract's second-cap discipline stops at the seam
   boundary**, and the same is true of `max_depth` (one value, `2`, at the render).
   **VERDICT: MP-4 closes the measured instance; the general form is a review question for
   the author.**
6. **`measure_store_traffic` reach is a checked variable in `TestTheEMITTEDStatementIsBounded…`
   (`require_full_reach`) but NOT in the new #268 leg**, which asserts only `rows > 0`.
   **VERDICT: mitigated by the positive control and by the mutation reproducing 6/6, so not a
   defect — but the idiom is inconsistent between two legs of the same file and one line would
   settle it.**
7. **The count discrepancy in the package survey** (32 vs 33 SDK methods) — §9.
   **VERDICT: immaterial to the verdict; recorded because inherited numbers get re-derived.**
8. **Scratch tree:** `/home/ejprice/scratch-adv-c1` (provenance-asserted, branch-less, holds
   my reference build, the nine variants and the missing-pins file). **It is NOT the record** —
   §10 carries the instruments. Tell me to keep it (a builder could start from the reference
   build), or discard it.
9. **No production or test file in the repo was modified, and no git command of any kind was
   run.** `scripts/**`, `test_comms_footer.py` and every packet-39 file were untouched. The
   only file I wrote at the repo root is this report.

---

# VERDICT: **CONTRACT INSUFFICIENT**

Eight missing-pin families, seven wrong builds surviving at `48 passed / 0 failed`, three of
them BLOCKER class — and the sharpest of the three is that **the contract's reach stops at an
internal method**, so a build that satisfies it perfectly ships a served surface no agent can
call and a served description that teaches the new action does not exist.

What is genuinely strong, and should not be churned: SECTION A's `more` arithmetic (the
`population == cap` case really does kill mechanism (b)), the `cap+1` traffic instrument, the
`limit=None` no-clause guard with its control, `TestTheRenderNEVERRecomputesTheDisclosure`
(the best pin in the file — a mutation, not a style assertion), the phantom-residue three-world
construction, and **#268's tightened comparative form, which I attacked and could not break**
(6/6 deterministic, both legs live, positive control independent). The failures above are
uniformly of one shape: **an invariant proven at the layer where it was implemented, and not
at the layer where it is served.**

---

*Written 2026-08-01 by `adversary-c1-1` (Opus) against `feat/surreal-unification` @ `025c2a9`.
Every number here was produced by a command shown beside it, in a provenance-asserted scratch
copy whose `loremaster.__file__` resolved to `/home/ejprice/scratch-adv-c1/loremaster/loremaster/__init__.py`.
Nothing is inherited, including from the contract author's report — the seven claims I checked
are tabulated in §7, and one of them is false.*

---

# §12 · APPENDIX — `test_adv_missing_pins.py`, VERBATIM

Scratch, never for the repo as-is: the author owns where these land and in what idiom. Measured
64/64 green with the contract on a fully-wired correct build (§4), and each test RED on exactly
its own wrong build.

```python
"""THE MISSING PINS — written by ``adversary-c1-1`` as SCRATCH, never for the repo.

Each test here is a pin contract C1 does NOT contain.  Every one of them is GREEN on a
correct build (the control leg) and RED on a wrong build that C1 waves through at
48 passed / 0 failed.  They are handed to the contract author as *the test that should
exist*, already written and already measured in both directions.

Run:  uv run pytest tests/test_adv_missing_pins.py -q      (from the scratch loremaster/)
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from _surreal_harness import SurrealEnv, drop_database
from loremaster.tasks import STATUS_OPEN, TaskLedger, TaskSpec

from test_blocks_edge import CREATOR, DESCRIPTION, task_ledger  # noqa: F401,I001
from test_query_tasks_bounded import _fresh_ledger, _tool_seam
from test_task_read_surface import (
    _ALT_CAP,
    _IDENTICAL_SUBJECT,
    _LISTING_CAP,
    _SURPLUS_POPULATION,
    _extra_lines,
    _normalise_task_render,
    _rendered_rows,
    _seed_identical_tasks,
)


# =========================================================================== #
# MP-1 — the SERVED tool surface.  Every C1 pin drives ``AppContext.tasks``; the
# MCP-registered tool is a DIFFERENT function with its own parameter list and its own
# served ``action`` description, and nothing compares the two.
# =========================================================================== #


class TestTheNewSurfaceIsREACHABLEThroughTheREGISTEREDTool:
    async def test_MISSING_the_served_tool_exposes_max_depth(self, tmp_path: Path) -> None:
        from test_mcp_server import _config, _slug  # noqa: PLC0415

        from loremaster.server import LoreServer, build_mcp_server  # noqa: PLC0415

        mcp = build_mcp_server(LoreServer(_config(_slug(), tmp_path / "live")))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        properties = (tools["lore_tasks"].inputSchema or {}).get("properties", {})
        assert "max_depth" in properties, (
            f"the REGISTERED lore_tasks tool exposes {sorted(properties)} — no 'max_depth'. "
            f"Every pin in SECTION B drives AppContext.tasks directly, which is an INTERNAL "
            f"method; an agent reaches the MCP tool, and on this build it cannot bound the "
            f"walk at all. A contract whose reach stops at the internal seam certifies a "
            f"surface no consumer can call"
        )

    async def test_MISSING_every_declared_action_is_NAMED_in_the_served_text(
        self, tmp_path: Path
    ) -> None:
        from test_mcp_server import _config, _slug  # noqa: PLC0415

        from loremaster.server import _TASK_ACTIONS, LoreServer, build_mcp_server  # noqa: PLC0415

        mcp = build_mcp_server(LoreServer(_config(_slug(), tmp_path / "live")))
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        served = (tools["lore_tasks"].description or "") + "".join(
            (schema.get("description") or "")
            for schema in ((tools["lore_tasks"].inputSchema or {}).get("properties", {})).values()
        )
        unadvertised = [action for action in _TASK_ACTIONS if f"'{action}'" not in served]
        assert not unadvertised, (
            f"lore_tasks dispatches {list(_TASK_ACTIONS)} but its SERVED text never names "
            f"{unadvertised}. THE CONSUMER LAW: the reader is an agent that learns this "
            f"tool's contract FROM what is served — an action absent from the description "
            f"is an action no caller will ever use, and a description enumerating a CLOSED "
            f"list that excludes it actively teaches that it does not exist. #302 pinned the "
            f"internal tuple; this is the served half of the same hole"
        )


# =========================================================================== #
# MP-2 — the disclosure at a SECOND cap (parameter-value MONOCULTURE, axis 2).
# ``_ALT_CAP`` reaches the BIT and the STATEMENT and never reaches the RENDER.
# =========================================================================== #


class TestTheRenderedDisclosureNamesTheCALLERSCapNotALiteral:
    @pytest.mark.parametrize("cap", [_LISTING_CAP, _ALT_CAP], ids=["cap-5", "cap-2"])
    async def test_MISSING_the_disclosure_names_the_number_actually_served(
        self, cap: int
    ) -> None:
        ledger, env = await _fresh_ledger()
        try:
            await _seed_identical_tasks(ledger, _SURPLUS_POPULATION)
            partial = str(await _tool_seam(ledger).tasks(action="query", limit=cap))
        finally:
            await ledger.close()
            await drop_database(env)
        rows = _rendered_rows(partial)
        disclosure = [line for line in partial.splitlines() if not line.startswith("- ")]
        assert len(rows) == cap and len(disclosure) == 1, (
            f"the construction did not produce a capped world: {len(rows)} rows, "
            f"{len(disclosure)} non-row line(s)"
        )
        assert str(cap) in disclosure[0], (
            f"a listing capped at {cap} discloses {disclosure[0]!r}, which does not name "
            f"{cap}. Every RENDER pin in the contract uses one cap, so a build that "
            f"hard-codes that literal serves a FABRICATED count on every other call — the "
            f"trust-doctrine defect inside the fix for a trust-doctrine defect. If the code "
            f"can branch on a value, at least one pin must supply a DIFFERENT one"
        )


# =========================================================================== #
# MP-3 — the chain render's BOUND, over two worlds of the SAME SIZE.
# ``deep != shallow`` in the contract is satisfied by the id COUNT differing; and
# ``"2" in shallow`` is satisfied by a hex id containing the digit 2.
# =========================================================================== #


class TestATruncatedWalkAndACompleteWalkOfTheSameSizeDIFFER:
    @staticmethod
    async def _chain(ledger: TaskLedger, depth: int) -> list[str]:
        chain: list[str] = []
        previous: list[str] = []
        for index in range(depth):
            task_id = await ledger.create_task(
                f"chain link {index}", DESCRIPTION, blocked_by=previous, created_by=CREATOR
            )
            chain.append(task_id)
            previous = [task_id]
        return chain

    async def test_MISSING_two_walks_of_EQUAL_reach_still_disclose_their_bound(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811
    ) -> None:
        ledger, _env, _seed = task_ledger
        deep_chain = await self._chain(ledger, 4)
        truncated_leaf = await ledger.create_task(
            "leaf of a FOUR-deep chain", DESCRIPTION,
            blocked_by=[deep_chain[-1]], created_by=CREATOR,
        )
        short_chain = await self._chain(ledger, 2)
        complete_leaf = await ledger.create_task(
            "leaf of a TWO-deep chain", DESCRIPTION,
            blocked_by=[short_chain[-1]], created_by=CREATOR,
        )
        context = _tool_seam(ledger)
        truncated = str(await context.tasks(action="blockers", task_id=truncated_leaf, max_depth=2))
        complete = str(await context.tasks(action="blockers", task_id=complete_leaf, max_depth=2))

        truncated_walk = await ledger.transitive_blockers(truncated_leaf, max_depth=2)
        complete_walk = await ledger.transitive_blockers(complete_leaf, max_depth=2)
        assert truncated_walk.truncated and not complete_walk.truncated, (
            f"the fixture did not build the two worlds: truncated={truncated_walk!r} "
            f"complete={complete_walk!r}"
        )
        assert len(truncated_walk.ids) == len(complete_walk.ids) == 2, (
            f"the two worlds serve different id COUNTS ({len(truncated_walk.ids)} vs "
            f"{len(complete_walk.ids)}), so a render that carries no bound would still "
            f"differ and this construction would measure nothing"
        )
        assert _normalise_task_render(truncated) != _normalise_task_render(complete), (
            f"a walk that STOPPED AT ITS BOUND with more upstream reachable renders "
            f"byte-identically to one that walked its graph to completion. Identical bytes "
            f"= a false clear = STOP. ⚠ The contract's own two-world leg compares a 4-deep "
            f"walk at depth 2 against the SAME leaf at depth 8, so its renders differ by "
            f"the ID COUNT alone and a build carrying neither `truncated` nor "
            f"`max_depth_used` passes it.\ntruncated={truncated!r}\ncomplete={complete!r}"
        )

    async def test_MISSING_the_truncated_render_names_the_DEPTH_not_a_digit_in_an_id(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811
    ) -> None:
        """``assert "2" in shallow`` is satisfied by any hex id containing a '2'."""
        import re  # noqa: PLC0415

        ledger, _env, _seed = task_ledger
        chain = await self._chain(ledger, 4)
        leaf = await ledger.create_task(
            "the leaf of a four-deep chain", DESCRIPTION,
            blocked_by=[chain[-1]], created_by=CREATOR,
        )
        shallow = str(await _tool_seam(ledger).tasks(action="blockers", task_id=leaf, max_depth=2))
        without_ids = re.sub(r"[0-9a-f]{32}", "", shallow)
        assert "2" in without_ids, (
            f"with the opaque ids removed the truncated render names no depth at all: "
            f"{without_ids!r}. The contract asserts `\"2\" in shallow` against a render that "
            f"carries 96 hex characters, so it passes with probability ≈0.998 on a build "
            f"that names no depth whatsoever — a failure message promising a check the "
            f"assertion does not perform. Full render: {shallow!r}"
        )


# =========================================================================== #
# MP-4 — ESC-5 at the TOOL, on the BLOCKED filter path.  The contract's uniformity class
# drives ``_task_listing`` DIRECTLY; nothing drives ``tasks(action='query', blocked=…)``.
# =========================================================================== #


class TestTheDisclosureSurvivesTheFILTERSAtTheServedSeam:
    async def test_MISSING_a_blocked_filtered_TOOL_call_discloses_its_bound(self) -> None:
        ledger, env = await _fresh_ledger()
        try:
            await _seed_identical_tasks(ledger, _SURPLUS_POPULATION)
            context = _tool_seam(ledger)
            plain = str(await context.tasks(action="query", limit=_LISTING_CAP))
            filtered = str(
                await context.tasks(action="query", blocked=False, limit=_LISTING_CAP)
            )
        finally:
            await ledger.close()
            await drop_database(env)
        assert len(_rendered_rows(plain)) == len(_rendered_rows(filtered)) == _LISTING_CAP, (
            f"the two tool calls served {len(_rendered_rows(plain))} and "
            f"{len(_rendered_rows(filtered))} rows over the same all-unblocked population"
        )
        assert _extra_lines(plain, filtered) == [] and _extra_lines(filtered, plain) == [], (
            f"the SAME question asked two ways renders differently at the TOOL: "
            f"blocked=False lacks {_extra_lines(plain, filtered)} and carries "
            f"{_extra_lines(filtered, plain)}. The contract's uniformity class calls "
            f"_task_listing DIRECTLY, so it cannot see a dispatcher that routes only ONE "
            f"branch through it — and the branch left behind serves ESC-5's false clear on "
            f"a live tool call"
        )

    async def test_MISSING_the_tool_passes_the_OWNER_filter_through(self) -> None:
        ledger, env = await _fresh_ledger()
        try:
            await _seed_identical_tasks(ledger, 6)
            rows = await ledger.query_tasks(limit=None)
            claim = await ledger.claim_task(rows[0].id, "alice")
            assert claim.claimed, "the fixture could not claim a task"
            served = str(
                await _tool_seam(ledger).tasks(action="query", owner="alice", limit=_LISTING_CAP)
            )
            truth = await ledger.query_tasks(owner="alice")
        finally:
            await ledger.close()
            await drop_database(env)
        assert len(_rendered_rows(served)) == len(truth) == 1, (
            f"lore_tasks action=query owner='alice' served {len(_rendered_rows(served))} "
            f"rows where the ledger says {len(truth)} match. The dispatcher's query branch "
            f"is REPLACED by this wave, and 'it forwards status/owner/blocked' is a "
            f"removed-behaviour item that no pin in the tree covers: NOTHING anywhere "
            f"drives action='query' with a filter. A build dropping `owner` also serves a "
            f"bound disclosure about a population the caller never asked about"
        )


# =========================================================================== #
# MP-5 — the max_depth refusal, ∀ over the actions it is illegal for.
# =========================================================================== #


class TestTheNewParameterIsRefusedForEVERYOtherAction:
    @pytest.mark.parametrize(
        "action", ["create", "query", "transition", "supersede", "rollup", "create_many"]
    )
    async def test_MISSING_max_depth_is_refused_for_every_non_blockers_action(
        self, action: str
    ) -> None:
        ledger, env = await _fresh_ledger()
        try:
            with pytest.raises(ValueError) as caught:  # noqa: PT011
                await _tool_seam(ledger).tasks(action=action, max_depth=3)
            message = str(caught.value)
            assert "max_depth" in message and action in message, (
                f"'max_depth' on action={action!r} was refused with {message!r}. The "
                f"contract tests ONE non-blockers action, so a guard hard-coded to that "
                f"action accepts and silently IGNORES the parameter everywhere else — the "
                f"teaching surface `_TASK_ACTIONS_ACCEPTING_LIMIT` exists to provide"
            )
        finally:
            await ledger.close()
            await drop_database(env)


# =========================================================================== #
# MP-6 — the TYPED state the render is supposed to take its applicability from.
# =========================================================================== #


class TestTheSupersededBlockerFactIsTYPEDStateNotARenderSideRead:
    async def test_MISSING_a_LOSS_carries_the_superseded_blockers_on_the_RESULT(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811
    ) -> None:
        ledger, _env, _seed = task_ledger
        blocker = await ledger.create_task("the blocker that moved", DESCRIPTION, created_by=CREATOR)
        dependent = await ledger.create_task(
            "work waiting on it", DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
        )
        successor = await ledger.supersede_task(
            blocker, subject="where it went", description=DESCRIPTION, created_by=CREATOR
        )
        result = await ledger.claim_task(dependent, "alice")
        assert not result.claimed, "the fixture's claim unexpectedly WON"
        assert result.superseded_blockers == {blocker: successor}, (
            f"a LOST claim reports superseded_blockers={result.superseded_blockers!r}; the "
            f"blocker {blocker!r} was superseded by {successor!r}. The contract asserts the "
            f"field EXISTS and DEFAULTS, and asserts a WON claim leaves it empty — so an "
            f"always-empty field satisfies every leg while the dispatcher does its own "
            f"second store read to write the sentence. That is a second implementation of "
            f"the blocker policy, and every NON-MCP consumer of the ledger gets nothing"
        )


# =========================================================================== #
# MP-7 — the supersede render's own removed behaviour.
# =========================================================================== #


class TestTheSupersedeRenderStillNamesTheSUCCESSOR:
    async def test_MISSING_the_render_names_the_successor_it_minted(
        self, task_ledger: tuple[TaskLedger, SurrealEnv, str],  # noqa: F811
    ) -> None:
        ledger, _env, _seed = task_ledger
        lonely = await ledger.create_task("nothing waits on this", DESCRIPTION, created_by=CREATOR)
        rendered = str(
            await _tool_seam(ledger).tasks(
                action="supersede", task_id=lonely, subject="s1",
                description=DESCRIPTION, created_by=CREATOR,
            )
        )
        moved = await ledger.get_task(lonely)
        assert moved.superseded_by is not None and str(moved.superseded_by) in rendered, (
            f"the supersede render {rendered!r} does not name the successor "
            f"{moved.superseded_by!r} it just minted. The contract's own test is NAMED "
            f"`..._NAMES_them_and_the_SUCCESSOR` and asserts only the DEPENDENTS — the "
            f"successor id is a pre-existing served fact this wave's rewrite of the branch "
            f"can silently drop, and the caller's whole next move needs it"
        )
```
