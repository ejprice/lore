# REPORT-builder-c3-2 — C3 BUILD: the dispatcher wiring, GREEN except one CONTRACT DEFECT

**brief-base v10 read**
**brief project v7 read**

## SUMMARY BLOCK

```
state: done-with-deviations
⛔ C3 IS BUILT. 225 collected -> 217 passed / 8 failed, and the 8 are ONE CONTRACT DEFECT
  I may not fix (§3): TASK_READ_ACTIONS gained `get` and `blockers` on 2026-08-02, but the
  contract's own `_task_action_kwargs` seeds NO `task_id` for them, so `_require_arg` raises
  before any footer decision is reached. PRE-EXISTING (the guard is at HEAD, untouched by me
  — proof in §3.2). Exact one-line fix named in §3.3; I did NOT make it.
⛔ DEVIATION 1 (prominent): I edited `loremaster/tests/test_query_tasks_bounded.py`, outside my
  writable set, under brief-base §2's regression exception. It holds a SECOND copy of
  `_tool_seam` that the C3 contract's ruled R-4 co-edit never reached, so three
  test_task_read_surface pins died on AttributeError the moment the footer landed. #102 in a
  fixture. Mirrored the ruled co-edit VERBATIM. §5.1.
⛔ DEVIATION 2 (prominent): I edited `loremaster/tests/test_comms_promise_registry.py`, same
  exception. Three NEW served render literals must be classified there or they cannot ship —
  that is the file's designed workflow, not a workaround. §5.2.
⛔ SCOPED-GREEN HONESTY: this is NOT a gates-green claim. `scripts/typecheck.sh` is
  RED AT HEAD from packet 39's unbuilt contract (#306/#307) — 191 residuals, RED_ADJUDICATED,
  not mine, not touched. §6.3.
receipt: C3 alone 217 passed / 8 failed / 225 collected (§6.1). Neighbours + the #314 schema
  invariant: test_comms_tool + test_message_ledger + test_render_seam_pins + test_mcp_server
  = 1759 passed / 14 skipped, 0 failed (§6.2). Currency gate: ~202 C3 orphans -> 8, and ZERO
  non-C3 orphans repo-wide; ruff GREEN (§6.3). Mutation proofs: MP-A 6/6 exact both ways;
  MP-B 21/21 declared fired + 3 UNEXPECTED reds I did not predict, reported as a miss (§7).
Packages considered: §8 — three mechanisms specified, all bespoke-in-house with the reads
  named. No new dependency; none is implicated.
decisions-needed: 3 — §3 the C-DEF (BLOCKING for a 225/225 claim; contract edit) ·
  §5.1 + §5.2 ratification of the two out-of-writable-set regression fixes.
receipt pointers: capability §0 · the build §2 · the C-DEF §3 · design decisions §4 ·
  deviations §5 · numbers §6 · mutation proofs §7 · packages §8 · residuals §9.
```

---

# §0 · CAPABILITY CHECK (brief-base §4 — first thing in the report)

Every tool my brief demanded was reachable and every path it named exists. `lore_comms
register` succeeded (session `packet04b2-wavec-resume`, role `builder`, spawned_by
`lead-04b2-wavec-r2`; brief `project` v7 auto-acked); `drain` returned `no unread messages`.
`ToolSearch "+lore"` returned the 15-tool lore surface. `uv`, `git` (read-only), `pytest`,
`ruff` and the live store at `ws://127.0.0.1:18000` all worked. **No capability gap.**

**Brief step 2 discharged:** `docs/reference/surrealdb-31-capabilities.md` read BEFORE any
store-adjacent work — §2 DML IDIOMS in full, per repo law (#107). It is CITED, never
re-transcribed. Its bearing on this slice, stated once so the next reader can check I
actually used it: my build adds **no new query and no DDL**. The footer's counts come from
`MessageLedger.pending_traffic`, already built and live-verified by `builder-c3-1`, and the
dispatchers' WHERE clauses are untouched. The §2 idioms that DO bind here are the ones
finding #219's repair rests on — comms identities travel as **bound parameters**, never
inlined text — and I preserved that: nothing I wrote interpolates an identity into query
text. The tree-wide derived invariant `TestNoCommsIdentityReachesQueryTEXT` passes (§6.1).

Per my brief I ran **no git write commands**, and I did **NOT** read
`/home/ejprice/scratch-c3-ref` (the reference build). This build is independent of it.

**Tooling honesty (brief-base §4).** I used `lore_comms` for coordination. For the
code-structure work I fell back to `grep`/`ast` rather than the lore graph in three places,
and say so: (a) enumerating the **unbound-rewrite call set** (§4.2) — I wrote a throwaway AST
script rather than asking the graph, because the question was "which of THESE functions call
`self.<method>`" over a set I was mid-edit on, i.e. a same-session-edited tree where the
index is stale by construction; (b) finding every hand-built `AppContext` seam in the test
tree (§5.1) — an exhaustiveness question over a *textual* pattern (`AppContext.__new__`),
the sanctioned case (a); (c) locating source-scanning pins (`inspect.getsource(...AppContext.
tasks)`) — a non-symbol textual seam, sanctioned case (b). No friction filed: all three are
the documented fallbacks working as intended, not gaps in the tool.

---

# §1 · WHAT I INHERITED, AND THE BASELINE I MEASURED

Base commit `379c2c5` on `feat/surreal-unification`, measured 2026-08-02. Already committed
and NOT rebuilt: `messages.py`'s `PendingTraffic`/`pending_traffic`/`pends` (SECTION D),
`server.py`'s `COMMS_FOOTER_PREFIX` + `AppContext._comms_footer` + `_validate_comms_identities`
(one call site) + #219's four prose sites + link 4's fenced refusal + R-5, and the contract's
`TASK_READ_ACTIONS` partition fix.

**The RED baseline, measured before I wrote a line** (this is the number the build moves):

```
$ uv run pytest tests/test_comms_footer.py -q -p no:randomly -n auto
169 failed, 56 passed in 7.32s        # 225 collected
```

---

# §2 · THE BUILD — each of the brief's seven items, with where it landed

All in `loremaster/loremaster/server.py` unless said otherwise. Cited by SYMBOL, never line
number (brief-base §1).

## 2.1 · The identity parameters (brief item 1)

`agent: str | None = None` + `session: str | None = None` on `AppContext.tasks`,
`AppContext.findings`, `AppContext.claim_task` **and** on all three `@mcp.tool` registration
wrappers, which forward them.

The `Field(description=)` text is **ONE shared constant per parameter** —
`_COMMS_IDENTITY_AGENT_DESCRIPTION` and `_COMMS_IDENTITY_SESSION_DESCRIPTION` — not three
blurbs (SECTION H's #102 leg). They are long deliberately: R8's rider MEASURED that a terse
description means neither Sonnet 5 nor Opus 5 passes `agent=` at all. The agent text states
the PAYOFF and discloses R8(2)'s coupling (the exact-match attribution fallback, and that it
is *matched, never authenticated*, which is why that line is third-person); the session text
says WHEN a caller needs it (a name is unique only within a session).

## 2.2 · Link 1b — the validation call set EXTENDED, never cloned (brief item 2)

`AppContext._validate_comms_identities` is now called as the **FIRST statement** of all three
dispatchers, plus its pre-existing site in `AppContext.comms`. The seam itself was WIDENED,
not forked: its `agent` parameter became `str | None` so an OMITTED identity validates
vacuously (R1 rules an omitted identity honest silence, not an error), and `name`/`to` gained
defaults so a dispatcher need not pass placeholders. **Every SUPPLIED value still meets
exactly the same predicate at every member** — the property the in-suite mutation test
`test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal` checks, and which MP-A
(§7.1) proves can actually FAIL.

⚠ **I also found and closed a second copy of the charset DECISION, which the brief did not
name.** The attribution gate (Ruling 5.2's cheap gate in front of the registry read) needed a
BOOLEAN answer to *"could this be a name?"*, while `_validate_comms_charset` RAISES. Writing
`AGENT_NAME_PATTERN.fullmatch(...)` a second time at that site would have been a private copy
of the predicate wearing the shared constant (#102: routing is not sharing). So the predicate
is extracted as `AppContext._is_comms_charset_legal` and **both policies call it**: one
refuses, one skips. They are genuinely different policies over the same question — refusing a
free-text `owner="the release train"` would break every honest caller, which is Ruling 10's
own falsifier. MP-B (§7.2) proves both move with ONE edit.

## 2.3 · The footer at a SINGLE exit (brief item 3)

`AppContext._with_comms_footer` is the ONE place any of the three dispatchers appends the
line. Beneath it: `_comms_traffic_line` (the trigger, the budget, the two identity paths) and
`_resolved_comms_traffic_line` (R8(1)'s path). Each dispatcher branch now ASSIGNS
`(rendered, writes)` and the single trailing `return` appends.

* **Resolution rides the registry, and only the registry** — `agent_registry.get_agent`,
  Ruling 5.3's ONE resolution seam. There is no second name-resolution path anywhere in this
  build.
* **The counts are CALLED, never re-derived** — `MessageLedger.pending_traffic(agent_id=row.id)`,
  on the same row that resolved. A re-deriving build passed 48/48 before it was pinned.
* **The disjunction has ONE spelling** — `PendingTraffic.pends`, inside `_comms_footer`. No
  call site re-spells `unread or unacked`.
* **Outcome-keying, not verb-keying.** `writes` is a COUNT: `claim_task` carries
  `int(result.claimed)` so a LOSING claim (which mutates nothing) is a read by outcome;
  `_resolve_or_acknowledge_many` now returns `(rendered, success_count)` so L2's best-effort
  batches footer iff **≥1** item actually wrote (the 1-of-5 fate is what kills
  `write_count == len(items)`); `create_many` carries `len(items)` because it is
  all-or-nothing (one atomic `execute_transaction`), stated in a comment beside it.
* **`writes < 1` short-circuits FIRST**, before any registry touch — which is what makes a
  READ cost zero registry reads whatever identity it carries (DW3's defect).
* **R8(1) resolved-render teaches `action=drain`; R8(2)'s fallback is third-person with no
  imperative.** Both already lived in `_comms_footer`; my wiring supplies the `authenticated`
  flag from the fact that decides it.

## 2.4 · Link 4 (brief item 4) — verified, not rebuilt

`_validate_comms_charset` already routed the offending value through `render_fenced`
(`repr()` explicitly rejected as a non-neutraliser). What was missing was REACH: it fired at
one member. With link 1b extended, the hostile fixture now drives all four link-0 members ×
both identity parameters, each with its `owner=`-style control, and all 16 refusal legs plus
all 8 per-parameter controls pass (§6.1). MP-B (§7.2) shows every one of them moves with the
predicate.

## 2.5 · MP-6 — the AMBIGUOUS agent is told the TRUTH (brief item 5)

**Mechanism chosen: serve the REGISTRY'S OWN classification, never a second one here.** The
registry already distinguishes *unknown* from *registered in two sessions* and both of its
messages already name the offending value and the remedy. `_comms_identity_teaching` renders
whatever `AgentRegistryError` was raised, inside a non-footer-shaped frame. There is ONE
`except` clause on purpose: branching per subclass would re-introduce the second classifier —
free to disagree with `lore_comms action=fleet`'s answer to the identical question, which IS
the defect MP-6 names.

Served bytes, measured (this is the case the adversary caught serving a falsehood):

```
created task 225ca23dc0f740cbb75c83bc6c117d2f (status open)
(no pending-traffic line: agent name 'builder-04b2-wavec-3' is registered in sessions
 packet-04b2-wavec, packet-04b3-waved — pass session= to disambiguate)
```

Not *"is not registered"*; names the value; names `session=`; serves no footer. Production
`AgentRegistry` and `FakeAgentRegistry` carry that sentence byte-identically (checked in
`loremaster/agents.py` and `loremaster/tests/_comms_fakes.py`), so the fake leg is not
laundering a production message that differs.

## 2.6 · `_INSTRUCTIONS` (brief item 6)

The `PENDING TRAFFIC:` paragraph landed in `server.py`'s `_INSTRUCTIONS`, between the ruled
comms block and `TOOL LOADING`, byte-exact against
`test_comms_tool._FOOTER_INSTRUCTIONS_PARAGRAPH` — imported by the contract, never re-typed
by me. Both `test_comms_tool` orphans are green. It uses NONE of the seven duty words (CL1's
rider); the comment beside it says so and says why growing `_COMMS_DUTY_VOCABULARY` instead
would be the wrong fix.

## 2.7 · The four non-blocking decisions (brief item 7)

Read (`REPORT-contract-04b2-c3fix-1.md` §7). Their bearing on the build: §7.1's FORK — I
built Reading A (the RESOLVED footer keeps the drain imperative), which is what the pinned
`TestTheRESOLVEDFooterIsACTIONABLE` requires; a lead ruling B deletes that class and my
`authenticated=True` branch loses its imperative. §7.2's R4-overlap reading is already
satisfied by the committed `pending_traffic` and I changed nothing there. §7.3 (the
`SimpleNamespace` harness) is the reason for §4.2 below. §7.7's `_registry_reads` bound holds:
my build resolves through `get_agent` and nothing else, so the spy sees every read.

---

# §3 · ⛔ THE ESCALATION — a CONTRACT DEFECT, 8 pins, and I did not touch it

## 3.1 · What fails

All 8 remaining failures are ONE cause, derived rather than asserted:

```
$ uv run pytest tests/test_comms_footer.py -q -p no:randomly -n auto 2>&1 | grep -E "^E  " | sort | uniq -c
      8 E           ValueError: the 'task_id' argument is required for this task action
```

The 8 are 4 test functions × the 2 actions `get` and `blockers`:
`TestTheFooterRidesTheOUTCOMENotTheVERB::test_a_READ_action_NEVER_footers_even_with_traffic_pending`,
and `TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS::{test_a_READ_carrying_a_RESOLVABLE_agent_spends_NO_registry_read,
test_a_READ_carrying_an_AMBIGUOUS_agent_teaches_NOTHING, test_the_teaching_NEVER_appears_on_a_READ}`.

Each drives `_tasks_call(action=<read>, ...)`, which builds its kwargs from
`_task_action_kwargs`. That helper handles `create`, `create_many`, `transition`, `supersede`
and `rollup`, and returns `{}` for everything else — so `get` and `blockers` are driven with
**no `task_id`**, and `_require_arg(task_id, "task_id")` raises before the dispatcher reaches
any footer decision.

## 3.2 · It is PRE-EXISTING, and here is the control

The requirement is at HEAD, in code I only moved:

```
$ git show HEAD:loremaster/loremaster/server.py   # around _TASK_ACTION_GET / _TASK_ACTION_BLOCKERS
    return self._render_task_detail(
        await self.task_ledger.get_task(_require_arg(task_id, "task_id"))
    )
    target = _require_arg(task_id, "task_id")
```

It was invisible at HEAD because those 8 tests were already RED for a **different** reason
(`tasks() got an unexpected keyword argument 'agent'`), so the C-DEF was masked by the very
absence this build fills. That is `TASK_READ_ACTIONS`' own documented history one step
further on: the partition pin correctly forced `get`/`blockers` to be adjudicated into a
fate, and the **fixture** that must DRIVE that fate was not extended with them.

## 3.3 · The exact edit — which I did NOT make

In `loremaster/tests/test_comms_footer.py::_task_action_kwargs`, before its final
`return {}`:

```python
    if action in ("get", "blockers"):
        # A READ needs something to read (the same repair C-DEF 2 made for
        # `_FINDING_ACTIONS_NEEDING_A_REF`): the task is created HERE, through the
        # ledger, so the id is real rather than invented.
        return {
            "task_id": await harness.task_ledger.create_task(
                "a real subject", "a real description", created_by=_UNREGISTERED_ATTRIBUTION
            )
        }
```

I am confident but not certain this is sufficient — `blockers` additionally walks
`transitive_blockers`, which the fake ledger must support; I did not run it, because doing so
means editing the contract. **A pin that looks wrong is an escalation, never an edit** (my
brief), and this is a fixture gap in a file on my do-not-touch list.

**Consequence if it is not fixed:** the four properties those pins assert
(*a read never footers · a read spends no registry read · a read never teaches*) are
currently proven over `query`/`rollup` only, and are UNPROVEN over `get`/`blockers` — the
exact silent-exemption shape the partition pin exists to stop. My build treats all four
identically (the trigger is a `writes < 1` short-circuit that cannot see the action name at
all), so I expect them green once the fixture drives them; **that expectation is not a
measurement and I am not offering it as one.**

---

# §4 · DESIGN DECISIONS I MADE, WITH THE ALTERNATIVE WRITTEN DOWN

Brief-base §2: a sentence admitting two readings that produce different code is the trigger,
regardless of confidence.

## 4.1 · The branch chain STAYS in the public dispatcher — a constraint, not a style choice

My first shape extracted the dispatch into `_tasks_dispatch`/`_findings_dispatch`. That
**silently blinded** `test_task_read_surface.py::TestTheServedActionVocabulariesArePinnedBy
EQUALITY`, which AST-scans `inspect.getsource(AppContext.tasks)` for `action == <NAME>`: it
reported **all 8 declared actions as reaching NO dispatch branch** while every action still
worked perfectly. A footer must not be able to turn a live dispatcher into an unreadable one.

Final shape: each branch ASSIGNS `(rendered, writes)`; one trailing `return` appends the
footer. Single exit preserved, structural scan preserved. Both `tasks` and `findings` use it
— `findings` is not scanned today, but two shapes for one policy is how the next person puts
the chain back in a helper. Recorded in both docstrings so the constraint meets its next
reader deliberately.

## 4.2 · The unbound-dispatcher rewrite is DERIVED, not hand-listed

Ruling 5.3 routed *"the 23-call-site unbound-dispatcher rewrite"* to this brief: the C3
harness is a `SimpleNamespace`, so `AppContext.tasks(harness, ...)` runs UNBOUND and every
`self._method(...)` must become `AppContext._method(self, ...)`. I did not work from the
number. I walked the AST from the three public dispatchers to a fixed point over `self.<name>`
calls, classified each callee as instance/class/static (a `classmethod` rewritten as
`AppContext._x(self, ...)` would pass `self` as the first real argument — a silent
wrong-answer bug), and rewrote by node position:

```
rewrote 11 instance-method call sites and 15 class/static call sites across 25 reachable functions
```

26, not 23. The routed number was a rumour; the derivation is re-runnable. The classifier
mattered: 15 of the 26 were `@classmethod`/`@staticmethod`, and a blanket
`AppContext._x(self, …)` would have corrupted all 15.

## 4.3 · The attribution ORDER, and the deliberate consequence

`tasks` → `(owner, actor, created_by)`; `findings` → `(actor, created_by)`; `claim_task` →
`(owner,)`. Only the FIRST supplied one is consulted, ever. **Alternative considered and
rejected:** try each until one resolves — which is R1's rejected guess wearing a budget, and
is what the discriminating fixtures (`test_a_SECOND_attribution_is_NEVER_consulted_after_the_first`,
`test_findings_never_consults_a_SECOND_attribution`) exist to kill. The consequence — a
REGISTERED `created_by` sitting behind an UNREGISTERED `owner` gets no footer — looks like a
bug and is not; it is documented in `_comms_traffic_line`'s docstring.

## 4.4 · A registry row whose name ≠ the request serves SILENCE, not a teaching

Link 2's in-code guard. **Two readings:** (A) silence, which I built — a lenient/normalising/
caching registry answering about somebody else is a defect in the REGISTRY, and teaching the
caller anything here would be a claim about their arguments that is not true; (B) serve a
teaching naming the mismatch. The contract pins only *no footer*, so both pass. I picked A
and wrote the reason into `_resolved_comms_traffic_line`. **A lead who prefers B should say
so** — B is arguably better for operability (today the anomaly is invisible), and the cost of
A is that a misbehaving registry is silent.

## 4.5 · The teaching frame is a plain literal, not an interpolated constant

I first built it as `render_line("{prefix}{reason})", prefix=…)` with the lead-in as a named
constant. That made the served sentence UNREADABLE to
`test_comms_promise_registry`'s render-literal scan — it would have classified the string
`'{prefix}{reason})'`, which tells a reviewer nothing. Changed to
`render_line("(no pending-traffic line: {reason})", …)` so the scan classifies the sentence a
consumer actually meets. An instrument that can only see a placeholder is not an instrument.

---

# §5 · ⛔ DEVIATIONS — two files outside my writable set, both regression fixes

Both are permitted by brief-base §2's single exception (*a regression your own in-scope change
directly causes may be fixed minimally and MUST be disclosed as a deviation, prominently*).
Both are disclosed here and in the summary block. **Neither is on my do-not-touch list**; both
need ratification.

## 5.1 · `loremaster/tests/test_query_tasks_bounded.py::_tool_seam` — the copy the ruling missed

Adding the footer made the three ledger dispatchers touch two more services. Ruling 5.3 routed
that as a co-edit — *"`test_blocks_edge::_tool_seam` wiring co-edit (§4.2 — empty fakes, NOT a
missing-service guard; a silently-skipped footer is confident silence)"* — and the C3 contract
landed it. **There are TWO copies of that seam.** Derived, not guessed:

```
$ grep -rn "AppContext.__new__" loremaster/tests/*.py
loremaster/tests/test_query_tasks_bounded.py:1056:    context = AppContext.__new__(AppContext)
loremaster/tests/test_blocks_edge.py:633:    context = AppContext.__new__(AppContext)
```

`test_task_read_surface.py` imports `_tool_seam` from **`test_query_tasks_bounded`**, not from
the co-edited `test_blocks_edge`, so three of its pins died on
`AttributeError: 'AppContext' object has no attribute 'agent_registry'`. That copy's own
docstring says it is *"deliberately the SAME construction … and NOT an import of it"* — which
is #102's shape in a fixture: two copies of one seam, and the ruled fix reached one.

I mirrored the ruled co-edit VERBATIM (empty `FakeAgentRegistry` + `FakeMessageLedger`, same
`type: ignore[assignment]`, a comment pointing at the sibling's rationale rather than
re-deciding it). I did **not** take the option the ruling explicitly rejected (a
missing-service guard in production that swallows `AttributeError` into "no footer" — that is
confident silence, which this slice exists to remove).

⚠ **The durable lesson is the lead's, not the fixture's:** a routed co-edit rider named ONE
address, and the seam had two. A rider that names a FILE rather than a PROPERTY reaches
whichever copy its author happened to know about.

## 5.2 · `loremaster/tests/test_comms_promise_registry.py` — classifying three new served lines

That file's contract is deny-by-default: every comms render template literal must be
registered WITH ITS PREDICATE (`_PROMISE_REGISTRY`) or declared promise-free
(`_PROMISE_FREE`), and every registered promise needs an executable emit/no-emit proof
(`_PROMISE_PROOFS`, with `set(...) == set(...)` a checked invariant). My build adds three
served literals, so classifying them is **the designed workflow**, not a way around a red pin.

* RESOLVED footer (names `lore_comms action=drain agent={identity}`) → `_PROMISE_REGISTRY`,
  with §9.7's litmus answered: emitted IFF the caller supplied `agent=`, the registry
  RESOLVED it, and the returned row's name EQUALS the request — so the identity it
  interpolates is a registered name by construction and the drain it names is the caller's
  OWN inbox, read from that same row in that same call.
* FALLBACK footer (third-person) → `_PROMISE_FREE`: it names no call and issues no
  imperative, which is the whole of R8(2); the counts are a real measurement and the
  parenthetical discloses the basis of the match.
* The teaching frame → `_PROMISE_FREE`, with an explicit ⚠: any remedy the reader acts on
  rides in a render VALUE (the registry's own message), which is that module's separately
  pinned bound. Stated rather than implied.

I also added the required `PromiseProof`. Its NO-EMIT leg is the **FALLBACK render, not a
quiet inbox** — a quiet inbox proves only that a footer can be withheld entirely, while R8's
actual split is between two footers that both appear and differ by exactly this imperative. A
build reusing the resolved text for the fallback path (the most natural, most DRY-looking
implementation, and wrong build W21's mirror) fails NO-EMIT. `test_comms_promise_registry`:
**118 passed**.

---

# §6 · THE NUMBERS — every one derived and re-runnable, with its scope stated

All measured 2026-08-02 against `379c2c5` plus my working tree.

## 6.1 · C3 alone

```
$ uv run pytest tests/test_comms_footer.py --collect-only -q | tail -1
225 tests collected in 0.07s

$ uv run pytest tests/test_comms_footer.py -q -p no:randomly -n auto | tail -1
8 failed, 217 passed in 7.09s
```

**169 failed / 56 passed → 8 failed / 217 passed.** The 8 are §3's single contract defect,
NAMED with its cause. SECTION D's live-store legs run against spike-surreal
`ws://127.0.0.1:18000` (the TEST store — never `:18500`).

## 6.2 · The neighbouring seams + the #314 tool-schema invariant

```
$ uv run pytest tests/test_comms_tool.py tests/test_message_ledger.py \
      tests/test_render_seam_pins.py tests/test_mcp_server.py -q -p no:randomly -n auto | tail -1
1759 passed, 14 skipped in 111.26s (0:01:51)
```

`test_mcp_server.py` is included because I added two parameters to three registered tools, and
Ruling 8 rider 4's generic invariant lives there (*every dispatcher parameter appears in the
registered tool's inputSchema*). Both `test_comms_tool` `_INSTRUCTIONS` orphans are green.

## 6.3 · The currency gate — RUN, not asserted

```
$ uv run python scripts/pending_contract_gate.py --currency
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 191 residual(s), owned by: packet-39-pending-build …
  ruff         GREEN
  pytest       RED_ORPHANED — 8 residual(s) with NO owner
      … all 8 are test_comms_footer.py [asyncio-get] / [asyncio-blockers]
CURRENCY   : FAIL — RED with nobody's name on it: pytest
```

**The ~202 C3 orphans (200 `comms_footer` + 2 `comms_tool`) are now 8, all one adjudicated
cause, and there are ZERO non-C3 orphans repo-wide.** That last clause is the load-bearing
one: the gate runs the whole suite, so it is an independent, derived receipt that the six
regressions §5 describes are closed and that nothing else in the repo broke.

⚠ **SCOPED-GREEN HONESTY, stated because an unqualified claim here would be FALSE:**
`scripts/typecheck.sh` is **RED AT HEAD** from packet 39's unbuilt contract (#306/#307) —
191 residuals, RED_ADJUDICATED with a named owner and trigger. **Not mine, not touched, and
I did not run it as if it were my receipt.** `ruff check` is GREEN on my three files and
repo-wide.

An intermediate run of this same gate is what surfaced the six non-C3 regressions (three
`test_task_read_surface` AttributeErrors, two `test_task_read_surface` dispatch-scan pins,
one `test_comms_promise_registry` classification). None of them was visible from
`test_comms_footer.py`.

---

# §7 · MUTATION PROOFS — declared BEFORE the run, diffed BOTH ways (#194/#196)

Instrument: `scripts/mutation_proof.py` (committed; I built no new one). Declared node ids
were taken from `pytest --collect-only -q`, never transcribed from source or from output.
The 8 §3 C-DEF failures are `--deselect`ed so a pre-existing red cannot be read as a proof.
Both runs restored the tree byte-exact (md5 verified by the tool).

## 7.1 · MP-A — link 1b's call removed from ONE member. **HELD, 6/6 exactly.**

Mutation: delete `AppContext._validate_comms_identities(agent, session=session)` from
`AppContext.claim_task`. Declared RED (6), all six fired and nothing else did:

```
PROOF HELD — the declared RED set fired EXACTLY:
  test_a_charset_illegal_identity_is_REFUSED_before_any_use[asyncio-lore_claim_task-agent]
  test_a_charset_illegal_identity_is_REFUSED_before_any_use[asyncio-lore_claim_task-session]
  test_the_refusal_renders_NO_RAW_VALUE_on_a_BARE_LINE[asyncio-lore_claim_task-agent]
  test_the_refusal_renders_NO_RAW_VALUE_on_a_BARE_LINE[asyncio-lore_claim_task-session]
  test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal[asyncio]
  test_every_identity_accepting_ENTRY_POINT_routes_through_the_ONE_seam
6 failed, 211 passed
```

The in-suite mutation test named the survivor by name — `['lore_claim_task'] kept accepting
'builder-04b2-wavec-3'` — and the AST door scan named it by address —
`server.py:3562: claim_task`. **This is the direction that matters:** the forwarder exemption
that swallowed DELTA-3 once did NOT swallow it here, because `claim_task` forwards its
identity into an underscore-prefixed helper and the repaired predicate calls that a DOOR.

## 7.2 · MP-B — the SHARED predicate itself. **PROPERTY HELD; MY PREDICTION MISSED 3.**

Mutation: `AppContext._is_comms_charset_legal` → `return True` (one line, one function).
Declared RED (21): 4 link-0 members × 2 identity parameters × 2 refusal legs (16), the
in-suite shared-predicate test (1), and the four attribution-gate/budget legs whose
expectation is *0 registry reads for a charset-illegal value* (4).

**Result: 24 failed, 193 passed. All 21 declared fired — ZERO declared-but-green — plus 3 I
did not predict:**

```
TestTheCharsetGuardDoesNotTeachAFalseRationale::test_POSITIVE_CONTROL_the_guard_STILL_REFUSES_a_bad_charset
TestTheCharsetGuardDoesNotTeachAFalseRationale::test_the_served_ValueError_does_not_claim_the_value_is_INLINED
TestTheCharsetGuardDoesNotTeachAFalseRationale::test_the_refusal_STILL_NAMES_the_value_and_the_pattern
```

`mutation_proof.py` exited **4 (MISMATCH)** and I am reporting that rather than dressing it
up. Cause of the miss: I enumerated the pins that drive the guard THROUGH a dispatcher and
forgot SECTION F's three pins that drive `_validate_comms_charset` DIRECTLY. They redden for
the same reason as the other 21 — the predicate always says yes, so no refusal is raised.

⚠ **I deliberately did NOT re-run with a corrected declaration.** Repo law is explicit that a
"declared" set read off the failures you just watched is the tautology in a new costume, and
a green exit bought that way would be worth less than this honest 4.

**What the run does and does not establish.** It DOES establish the property the brief asked
for: one edit to one predicate moved **all four link-0 members' refusals and both attribution
gates together** — no member is running a private copy. The zero declared-but-green count is
the direction that catches a mutation landing in dead code, and it is clean. It does NOT
establish that my prediction was complete; it was not, by three. **Stated scope:** the command
ran `test_comms_footer.py` only, so reds in other suites (`test_comms_tool` certainly has
some) are outside what this run observed.

---

# §8 · PACKAGES CONSIDERED

| mechanism I built | library evaluated | what I **READ** | verdict |
|---|---|---|---|
| the footer-append seam (`_with_comms_footer`) — trigger, read budget, single exit | none applicable; the in-house alternative was a decorator over the three dispatchers | `loremaster.render`'s `render_line`/`render_compose` signatures (`render_line(template: LiteralString, /, **values: SafeLine \| int) -> Rendered`) and the three dispatchers' existing return shapes | **bespoke, in-house** — this is application policy over our own ledgers; no library models "append a pending-traffic annotation at a dispatcher's single exit". A decorator was rejected because the write-COUNT is only knowable inside each branch. |
| the identity teaching (`_comms_identity_teaching`) | none — the alternative was re-classifying the registry's exceptions here | `loremaster.agents`' `UnknownAgentError`/`AmbiguousAgentError` message text and `FakeAgentRegistry._resolve`'s mirror of it | **reuse, not bespoke** — the classification already exists in `AgentRegistry`; I render what it said. Writing a second classifier is #102 and is the defect MP-6 names. |
| the charset predicate (`_is_comms_charset_legal`) | `re` (stdlib), already in use via `AGENT_NAME_PATTERN` | `loremaster.agents.AGENT_NAME_PATTERN` (`^[a-z0-9][a-z0-9_-]{0,63}$`) and finding #210's `fullmatch`-vs-`match` note | **stdlib, extracted not duplicated** — one `re` call, one home, two policies calling it. |

**No new dependency is implicated, and none was needed.** Had one been, my brief says to
escalate for install rather than code around the gap; that did not arise (§6.6 of
`REPORT-builder-c3-1.md` predicted the same and was right).

---

# §9 · RESIDUALS AND FLAGS — everything I noticed, individually

1. **⛔ The C-DEF (§3)** — 8 pins, exact fix named, not made. Needs a contract edit.
2. **⛔ Ratify §5.1** — `test_query_tasks_bounded.py` edited (regression fix, ruled co-edit
   mirrored). ⚠ And the general lesson: **the ruled co-edit rider named a FILE and the seam
   had TWO copies.** If a future ruling routes a fixture co-edit, route it by PROPERTY
   (`every hand-built AppContext seam`) with the derivation attached
   (`grep -rn "AppContext.__new__"`), not by filename.
3. **⛔ Ratify §5.2** — `test_comms_promise_registry.py` edited (three new served literals
   classified + one proof added, which is that file's designed workflow).
4. **§4.4 needs a lead's eye** — the link-2 name-mismatch branch serves SILENCE. Both
   readings are written down; the cost of mine is that a misbehaving registry is invisible.
5. **§4.1 is a NEW constraint on this dispatcher** and it is undefended by anything but a
   docstring: `test_task_read_surface` scans `inspect.getsource(AppContext.tasks)`, so ANY
   future extraction of that branch chain reports all 8 actions dead. `AppContext.findings`
   has NO such scan — an asymmetry a future reader can trip on. **Suggested (not made,
   outside my writable set): add the same structural scan for `findings`, or better, derive
   the scanned method from a list so the pin covers every dispatch-on-action verb.**
6. **`create_many`'s write count is `len(items)`, on the strength of a docstring** that calls
   it all-or-nothing (one atomic `execute_transaction`). I READ that docstring; I did not
   prove atomicity empirically. If it can ever partially write, the count is wrong — flagged
   rather than assumed.
7. **`_registry_reads`' stated bound now has a second reader.** The contract's spy wraps
   `get_agent` specifically. My build resolves ONLY through `get_agent`, so the bound is
   satisfied today — but it is satisfied by my discipline, not by a mechanism. Ruling 5.3
   makes any second resolution path a #102 escalation, which is the mechanism.
8. **`_validate_comms_identities` now has default arguments for `name`/`to`.** That is a
   surface widening: a future caller can omit them silently. It was the alternative to making
   three dispatchers pass `name=None, to=None` boilerplate. Disclosed because a defaulted
   parameter the code branches on is a fixture-factory hazard one level up.
9. **Nothing I wrote touches the store, the schema or any DDL** (§0). If a reviewer expected
   a store change here, that expectation is wrong and this line is where to check it.

---

**`loremaster.__file__` receipt (#140):** I made **NO scratch copy.** Every measurement above
ran against the real tree at
`/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`. Both mutation proofs
mutated the REAL file through `scripts/mutation_proof.py`, which takes an md5-verified content
copy and restored byte-exact both times (`md5 fce25de2493b3a935dbf8046b1c0d914`, printed by
the tool in each run). There is therefore no isolated tree whose provenance could be poisoned.
Stated explicitly because its absence would read as an omission.

**My tree writes, in full:** `loremaster/loremaster/server.py`,
`loremaster/tests/test_comms_promise_registry.py`,
`loremaster/tests/test_query_tasks_bounded.py`, and this report. **I never touched
`test_comms_footer.py` (THE CONTRACT), `_message_fakes.py`, `_comms_fakes.py`,
`test_comms_tool.py`, `scripts/**` or `docs/**`**, and I ran no git write command —
`git status --porcelain` shows exactly the three modified files above.

*Written 2026-08-02 by `builder-c3-2` (Opus) against `feat/surreal-unification`, base commit
`379c2c5`. Every number here is mine and re-runnable from the pasted invocations. I did NOT
read `/home/ejprice/scratch-c3-ref` (the reference build), so this build is independent of it.*
