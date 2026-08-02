# REPORT-contract-04b2-c3fix-1 — C3's FIX WAVE: the 26 wrong builds, closed and mutation-proven

**brief-base v9 read**
**brief project v7 read**

## SUMMARY BLOCK

```
state: done-with-deviations
⛔ THE HEADLINE, COUNTED CAREFULLY: the adversary's table has 26 ROWS, of which 25 were
  GREEN (row W1 is its own control and was already RED — its §2.3). **24 of those 25 are
  now CAUGHT**, each by a named pin, each demonstrated by a landed mutation with the RED
  set diffed BOTH WAYS (§3). The 25th (W25, COMMS_FOOTER_PREFIX="zzz") is DELIBERATELY
  LEFT OPEN with its reason and its bound stated (§5.1). One further wrong build of my own
  construction (W1b) is closed too, so the driver carries 25 receipts. C3 goes 48 pins ->
  75 test functions / 128 parametrised tests.
⛔ THE RECEIPT (§4): C3 alone 128 passed / 0 failed. The 11 seam suites: 2686 passed,
  14 skipped, 3 xfailed, ZERO failures (the adversary measured 2606 on the same 11 with the
  old contract; +80 is exactly this wave's new tests). ruff + mypy clean on my three files.
  ⚠ NOT a wave-level gates-green claim — scoped in §4.3; scripts/typecheck.sh is RED at HEAD
  from packet 39's unbuilt contract (#306/#307), which is not mine and which I did not touch.
deviation: the receipt required ONE repair to the scratch REFERENCE BUILD — MP-6's ambiguity
  classification (§5.2). That is a BUILD requirement the contract now imposes, not a contract
  defect; the mechanism is the builder's choice and my scratch version is evidence of
  satisfiability, not a prescription.
deviation: SECTION D is now driven against a LIVE SurrealDB as well as the fake, so
  test_comms_footer.py gains a store dependency and ~24s of serial wall-clock (§2.2, §7.4).
deviation: my first prediction for two mutations was WRONG and is reported as wrong, with the
  reason, rather than re-declared after the fact (§3.3).
deviation: R-4's co-edits land production PROSE in test_comms_tool.py, so CL3's terminating
  pin is RED at HEAD until the builder ships (§6.1) — visible to every agent in this tree.
Packages considered: §8 — unittest.mock.AsyncMock(wraps=) vs the hand-rolled read counter =>
  REPLACE (adopted); _surreal_harness + test_message_ledger._seed_agents vs a second live
  harness => REPLACE (reused by import); re vs a parser for the count extractor => keep,
  stdlib; ruff S608 => keep_with_trigger, the adversary's trigger unchanged.
decisions-needed: 4, none blocking — §7.1 the R8(2)/T3 reading I pinned and its alternative ·
  §7.2 R4's overlap world, now pinned from R4's verbatim text · §7.3 the SimpleNamespace
  harness (R-3), left alone because Ruling 5.3 already routed the rider · §7.5 two docs
  corpses outside my writable set.
receipt pointers: the 26-row table §2.1 · the new pins §2.2 · mutation proofs §3 · THE
  RECEIPT §4 · left-open + build requirements §5 · the R-4 co-edits §6 · residuals §7 ·
  packages §8 · the instrument, verbatim §9.
```

---

# §0 · CAPABILITY CHECK (brief-base §4 — first thing in the report)

Everything the brief demanded was reachable. `lore_comms register` succeeded (session
`packet-04b2-wavec`, role `contract`; brief `project` v7 auto-acked, drained clean).
`ToolSearch "+lore"` returned the 15-tool lore surface. `scripts/scratch_copy.sh
--verify-only`, `uv`, `pytest`, `ruff`, `mypy` and `scripts/typecheck.sh` all ran, and the
spike test store (`ws://127.0.0.1:18000`, `spike-surreal.service` active) accepted live
connections. **No brief clause was unmeetable.**

One honest tool note (brief-base §4, last bullet): the structural questions in this run —
*"which fixture value reaches which branch"*, *"what arguments does this dispatcher accept
for action X"*, *"how many occurrences of this anchor exist"* — were answered by `Read`,
`grep` and AST/regex scanning I wrote, not by lore. That is not a route-around: the graph
has nothing to add over the file for *"what does this exact line pass"*. `lore_comms` was
used for coordination only. No friction filed, because lore was not the right instrument
rather than a failing one.

**Prohibitions honoured:** the only repo files written are the three in my writable set
(`test_comms_footer.py`, `test_comms_tool.py`, `test_blocks_edge.py`) plus this report —
`git status` shows exactly those. **Zero git write commands.** No worktree. Nothing under
`scripts/**`, no packet-39 file, and neither `test_task_read_surface.py` nor
`test_query_tasks_bounded.py` was edited (they were copied `git show HEAD:` → scratch,
read-only, so the seam run measures HEAD's versions).

---

# §1 · PROVENANCE — which tree I graded (#140)

Reference build: `/home/ejprice/scratch-c3-ref`, the tree `refbuild-c3-1` built and
`adversary-c3-1` graded. Verified by the blessed tool and by import, this run:

```
$ ./scripts/scratch_copy.sh --verify-only /home/ejprice/scratch-c3-ref
scratch copy VERIFIED: /home/ejprice/scratch-c3-ref
  loremaster  -> /home/ejprice/scratch-c3-ref/loremaster/loremaster/__init__.py

$ uv run python -c "import loremaster; print(loremaster.__file__)"
loremaster.__file__ = /home/ejprice/scratch-c3-ref/loremaster/loremaster/__init__.py
```

The scratch tree sits at `a88e7c5` + the reference build's five modified files. Because HEAD
has moved to `3488517`, I re-synced the four test-tree files that changed in between
(`_surreal_harness.py`, `_task_fakes.py`, `test_query_tasks_bounded.py`,
`test_task_read_surface.py`) from `git show HEAD:` before the seam run, so the 11-suite
number below grades **HEAD's tests against the reference build**, not a stale snapshot.

**My three repo files are byte-identical to the scratch copies** (`diff -q`, all three
IDENTICAL) at every measurement in this report — so every number grades the file the lead
will commit, not a scratch variant of it.

**Backups are CONTENT, not hashes** (the 2026-07-14 MD5 near-miss): the wrong-build driver
`cp -a`s `server.py` and `messages.py` into `.c3fix-pristine/` before the first mutation,
restores from content after each one, and **raises if the restored bytes differ**.

---

# §2 · WHAT CHANGED, AND WHICH WRONG BUILD EACH PIN KILLS

## 2.1 · The 26-row table — one row per wrong build the adversary left green

Every "caught" row is a landed mutation with a both-ways RED diff (§3), not an argument.

| # | wrong build | the pin that now kills it | proof |
|---|---|---|---|
| **W2** | the two counts are SWAPPED | `TestTheFooterServesTheLEDGERSTwoCounts::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles` (via `_rendered_counts`, a value→ROLE extractor — a containment test cannot see a swap) | CAUGHT, 3 fns red |
| **W12** | the counts are a CONSTANT 1/1 | same class, parametrised over TWO unrelated count pairs (7/3 and 4/9) | CAUGHT, 4 fns red |
| **W3** | the footer re-derives the counts in the SERVER; `pending_traffic` never called | `TestTheProductionSeamEXISTSAndIsTheThingDriven::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam` — an `AsyncMock(wraps=)` spy asserting exactly one call, with `agent_id` = the registry row's id | CAUGHT, 1 fn red |
| **DEL** | `MessageLedger.pending_traffic` DELETED from production | the same class's existence + signature pin, the double-conformance pin, AND SECTION D now driven against the REAL ledger on a live store | CAUGHT, 7 fns red |
| **W23** | fires on `unread > 0` alone (0 unread + 3 unacked directives serves nothing) | `TestNoTrafficMeansNoFooter::test_POSITIVE_CONTROL_the_same_write_WITH_traffic_DOES_footer`, parametrised over `TRAFFIC_WORLDS_THAT_FOOTER` = {(7,3), (0,3), (7,0), (4,9)} | CAUGHT, 1 fn red |
| **W4** | `session=` accepted and IGNORED | `TestTheSESSIONScopesTheIdentityAndItsInbox` — one NAME, two sessions, two DIFFERENT inboxes, asserted both directions | CAUGHT, 2 fns red |
| **W13** | `session=` never lands on the tool schema | `TestTheAgentParameterDescriptionIsSHAREDAndStatesThePayoff::test_all_three_tools_ALSO_expose_session_with_ONE_shared_description` + `::test_the_session_description_says_WHEN_a_caller_needs_it` | CAUGHT, 2 fns red |
| **W5** | findings' four single-item write verbs never footer | `TestTheFooterRidesTheOUTCOMENotTheVERB::test_EVERY_findings_WRITE_action_footers`, ∀ over `FINDING_WRITE_ACTIONS`, each fate FORCED by a seeded fixture | CAUGHT, 2 fns red |
| **W10** | tasks' `transition`/`supersede` never footer | `::test_EVERY_tasks_WRITE_action_footers`, ∀ over `TASK_WRITE_ACTIONS` | CAUGHT, 1 fn red |
| **W24** | `acknowledge_many` footers unconditionally | `TestABatchThatWroteNOTHINGServesNoFooter::test_the_footer_follows_the_WRITE_COUNT_not_the_CALL`, now parametrised over BOTH batch verbs × four fates | CAUGHT, 1 fn red |
| — | *(a NEW action added to either dispatcher and silently exempted)* | `::test_the_declared_action_PARTITION_covers_the_dispatchers_OWN_action_set` — the declared read/write sets are asserted EQUAL to `server._TASK_ACTIONS` / `_FINDING_ACTIONS` | (not one of the 26; the guard that stops a 27th) |
| **W6** | the footer REPLACES the tool's answer | `TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_the_underlying_answer_SURVIVES_the_footer` | CAUGHT, 1 fn red |
| **W11** | the footer appended TWICE | `::test_exactly_ONE_footer_line_is_served` | CAUGHT, 1 fn red |
| **W20** | the footer PREPENDED | `::test_the_footer_is_the_LAST_line` | CAUGHT, 1 fn red |
| **W7** | `unacked_directives` clamps at 5 | `TestThePendingTrafficCountIsONEImplementation::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW`, now parametrised over BOTH roles × BOTH backends | CAUGHT, 1 fn red |
| **W8** | the footer fires only for identities containing a hyphen | `CALLERS = (CALLER_A, CALLER_B)` swept through every dispatcher-level class — the sweep the file's own header comment falsely claimed | CAUGHT, 7 fns red |
| **W9** | the teaching degenerates to the bare offending value | `TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS::test_the_teaching_names_a_REMEDY_not_just_the_offending_value` | CAUGHT, 1 fn red |
| **W17** | the teaching leaks onto READ paths | `::test_the_teaching_NEVER_appears_on_a_READ`, ∀ over `TASK_READ_ACTIONS` | CAUGHT, 1 fn red |
| **W14** | no footer paragraph in `_INSTRUCTIONS` | `TestTheFooterTeachingLandsThroughTheDeclaredAllowlist` gains FOUR positive legs (declared / served / vocabulary-clean / names `agent=` and all three tools) | CAUGHT, 1 fn red |
| **W15** | the one-read ceiling + charset gate broken on `findings` and `claim_task` | `TestTheREADBudgetHoldsOnALLTHREEDispatchers` — the budget worlds and the second-attribution ceiling, on the two dispatchers that had ZERO registry-read coverage | CAUGHT, 3 fns red |
| **W16** | the resolver falls back to `candidate.startswith(registered)` | `TestTheFallbackIsThirdPersonWithNoDrainImperative::test_the_fallback_refuses_a_charset_legal_SUPERSTRING_too` — exactness is two-sided; the prefix fixture only saw one side | CAUGHT, 1 fn red |
| **W18** | link 2's `if row.name != name` guard DELETED | `TestTheSERVERVerifiesTheRowTheRegistryHandedBack` — a deliberately LENIENT registry double, plus its own positive control | CAUGHT, 1 fn red |
| **W19** | an AMBIGUOUS `agent=` is told *"is not registered"* | `TestTheSESSIONScopesTheIdentityAndItsInbox::test_an_AMBIGUOUS_agent_is_taught_the_TRUTH_never_that_it_is_UNREGISTERED` | CAUGHT, 1 fn red |
| **W21** | the RESOLVED footer loses its drain imperative | `TestTheRESOLVEDFooterIsACTIONABLE::test_the_RESOLVED_footer_names_the_drain_CALL` (⚠ a stated READING — §7.1) | CAUGHT, 1 fn red |
| **W22** | only the FALLBACK render is a bare f-string | `TestTheFALLBACKFooterIsAlsoBuiltThroughTheRenderSeam` — using `_footer_for_owner`, the helper the contract defined and never called (adversary R-1) | CAUGHT, 1 fn red |
| **W25** | `COMMS_FOOTER_PREFIX` becomes `"zzz"` | **DELIBERATELY LEFT OPEN — §5.1**, with the reason and the residual damage bounded | open, reasoned |
| **W1** | the count placeholders removed from the template | **already RED before this wave** — the render seam's own unused-kwarg guard (adversary §2.3). Replaced by **W1b**, the case that guard structurally CANNOT see: one placeholder AND its kwarg dropped together, so the render is legal and the footer silently carries HALF the measurement. Killed by the count pins. | W1b CAUGHT, 3 fns red |

**Score, DERIVED rather than rounded: the table above has 26 rows. W1 was ALREADY RED
before this wave, so 25 rows were wrong builds that survived. Of those 25, **24 are closed
with a landed mutation receipt and 1 (W25) is deliberately open**. W1b is an addition of
mine, not one of the 26, and it is closed as well — so the driver in §9 carries 25
receipts, not 24 and not 26.**

## 2.2 · The eight structural changes underneath those pins

1. **`traffic: tuple[int, int]` replaces `pending: bool`** at every dispatcher helper. A
   boolean can express two worlds; R4 defines two independent counts, so the fixture could
   never construct `(0, 3)` — the exact state R4 exists to surface. 23 call sites converted.
2. **SECTION D is dual-driven — `("real", "fake")`.** The real leg builds a `MessageLedger`
   on a throwaway live database and seeds it through the ledger's OWN public verbs
   (`send` → `drain`), so the states counted are states production can reach. This is the
   only instrument that can grade production's *predicate*: a build dropping R4's
   `grade = 'directive'` conjunct, or riding `drain`'s cap, is invisible to every fake in
   the tree. It is what makes the DELETE probe impossible.
3. **The seam is spied, always.** `agent_registry.get_agent` and
   `message_ledger.pending_traffic` are both wrapped in `AsyncMock(wraps=…)`. The old
   hand-rolled counter recorded a COUNT and discarded `*args, **kwargs` — the instrument's
   shape was itself why W4 (session ignored) and W3 (wrong `agent_id`) were unassertable.
4. **`_task_action_kwargs` / `_finding_action_kwargs`** seed every write action so the ∀
   legs actually DRIVE each one (fate coverage — a ∀ evaluated where a branch cannot fire
   is a fixture-reason pass wearing a universal quantifier).
5. **`CALLERS` is a real parametrisation.** The file's header comment claimed a sweep that
   did not exist; `CALLER_B` reached one line. It now reaches every dispatcher class.
6. **`_rendered_counts(footer, role)`** — a value→ROLE extractor returning a SET, so a
   swap, a constant, a duplicated role and a missing number all fail differently.
7. **`_is_footer_line`** — placement claims ("exactly one", "last") need to classify EVERY
   line; a helper returning the first match cannot express either.
8. **A tree-wide #219 sweep** (`TestTheFalseRationaleSurvivesNowhereInTheTree`) over
   production AND tests, with two positive controls. Its marker is **assembled from
   fragments** (`"in" + "lined into"`) so the detector's own file is not a hit — otherwise
   five self-exemptions would be needed and every later prose edit would re-redden the pin,
   which is how a gate gets switched off.

---

# §3 · MUTATION PROOFS — declared BEFORE the run, diffed BOTH WAYS

## 3.1 · The instrument and why it is not `scripts/mutation_proof.py` directly

Several wrong builds need MORE THAN ONE anchored edit (W5 breaks four return sites; W15
forks one seam per dispatcher; W16 needs a lenient lookup *and* a lenient post-check), and
`mutation_proof.py` takes a single anchor. `scripts/**` is DO-NOT-TOUCH this wave, so I did
not extend it. The driver keeps every property that makes that tool trustworthy:

* every edit asserts its anchor matched **exactly** the declared number of times and
  **aborts** otherwise — #194's failure mode is a mutation that never LANDED printing a
  green tail that reads exactly like a proof;
* **the declared node ids are validated against `pytest --collect-only` before any run**, so
  a typo'd or renamed id is a hard error rather than a silently-empty expectation;
* the observed RED set is diffed **both ways** — unexpected reds AND declared reds that
  stayed GREEN, the direction that catches a mutation landing in dead code;
* production files are restored from a **content** backup and the restore is verified
  byte-exact after every wrong build.

**Full text is in §9** (brief-base §1: an instrument behind a load-bearing claim is a
deliverable, not scratch — and `scratch_copy.sh` trees are disposable by design).

## 3.2 · Two stated bounds on the declarations

* **Declared sets are at FUNCTION granularity** (`file::Class::func`), not per-parameter node
  id. What is predicted is WHICH PIN fires; a parametrised pin's rows multiply for reasons
  (backend, caller, traffic world) orthogonal to the defect. The both-ways diff is
  unaffected — an unexpected FUNCTION is still a failure, and a declared function that
  stayed FULLY green is still a failure.
* **Only `test_comms_footer.py` is run** by the driver. A wrong build that also reddens a
  pin in another suite is invisible to it. Stated rather than implied.

## 3.3 · ⚠ THE TWO PREDICTIONS I GOT WRONG, reported as wrong

The both-ways diff caught my own errors before it caught anything else, which is the point
of it. Neither was re-declared from the observed output (that is the tautology in a new
costume); both were corrected from a derived REASON:

* **W8** — I declared `test_the_underlying_answer_SURVIVES_the_footer` would redden. It
  stayed GREEN, and the reason is real: with `CALLER_B` the mutation suppresses the footer
  on *both* the traffic and the no-traffic call, so the two line counts still match and that
  pin cannot see this defect. Prediction corrected; W8 is still caught, by seven other pins.
* **W1** — I declared 23 functions; 17 reddened and 6 stayed green. The mutation touches
  the AUTHENTICATED template only, so every fallback-path pin was correctly unaffected — my
  declaration was over-broad. W1 was then dropped entirely (it was already RED pre-wave, so
  it proves nothing about this wave's pins) and replaced by **W1b**, which is the case the
  render guard structurally cannot see.

A third error surfaced the same way: **W7's first replacement was a mangled leftover from an
earlier draft** (`min(5, 0) + min(5, 0) + min(5,`). It landed, reddened 123 of 128 tests, and
the unexpected-red diff refused it. A one-directional check would have called `123 failed` a
successful proof.

## 3.4 · The receipt

```
collected 75 distinct test functions in loremaster/tests/test_comms_footer.py

=== W2  ... -> CAUGHT (3 function(s) red)     === W8   ... -> CAUGHT (7 function(s) red)
=== W12 ... -> CAUGHT (4 function(s) red)     === W9   ... -> CAUGHT (1 function(s) red)
=== W3  ... -> CAUGHT (1 function(s) red)     === W17  ... -> CAUGHT (1 function(s) red)
=== DEL ... -> CAUGHT (7 function(s) red)     === W13  ... -> CAUGHT (2 function(s) red)
=== W23 ... -> CAUGHT (1 function(s) red)     === W15  ... -> CAUGHT (3 function(s) red)
=== W4  ... -> CAUGHT (2 function(s) red)     === W16  ... -> CAUGHT (1 function(s) red)
=== W5  ... -> CAUGHT (2 function(s) red)     === W18  ... -> CAUGHT (1 function(s) red)
=== W10 ... -> CAUGHT (1 function(s) red)     === W19  ... -> CAUGHT (1 function(s) red)
=== W24 ... -> CAUGHT (1 function(s) red)     === W21  ... -> CAUGHT (1 function(s) red)
=== W6  ... -> CAUGHT (1 function(s) red)     === W22  ... -> CAUGHT (1 function(s) red)
=== W11 ... -> CAUGHT (1 function(s) red)     === W14  ... -> CAUGHT (1 function(s) red)
=== W20 ... -> CAUGHT (1 function(s) red)     === W1b  ... -> CAUGHT (3 function(s) red)
=== W7  ... -> CAUGHT (1 function(s) red)

ALL WRONG BUILDS CAUGHT
```

Every row printed `LANDED (every anchor matched its declared count)` before its run, and
every restore verified byte-exact. **Zero unexpected reds, zero declared reds that stayed
green, across all 25.**

---

# §4 · ⛔ THE SATISFIABILITY RECEIPT

Scratch tree, provenance re-verified (§1), reference build + the MP-6 repair (§5.2),
contract byte-identical to the repo's.

## 4.1 · C3 alone

```
$ uv run pytest loremaster/tests/test_comms_footer.py -q -p no:randomly -n 8
128 passed in 3.27s
```

48 pins → **128 passed / 0 failed** across 75 test functions.

## 4.2 · The 11 suites this seam touches (#133's leg)

`test_comms_footer` · `test_comms_tool` · `test_mcp_server` · `test_message_ledger` ·
`test_task_ledger` · `test_findings` · `test_query_tasks_bounded` · `test_blocks_edge` ·
`test_render_seam_pins` · `test_render` · `test_comms_render_architecture`:

```
$ uv run pytest -n auto -q -p no:randomly <the 11 files>
2686 passed, 14 skipped, 3 xfailed in 125.27s (0:02:05)
```

**Zero failures.** The adversary measured **2606 passed** on the same eleven with the old
contract and the same reference build; **2686 − 2606 = 80**, which is exactly this wave's new
test count (128 − 48). The delta is derived, not asserted.

## 4.3 · ⚠ GATE SCOPE — stated, because HEAD is RED

```
$ uv run ruff check loremaster/tests/{test_comms_footer,test_comms_tool,test_blocks_edge}.py
All checks passed!

$ uv run mypy loremaster/tests/{test_comms_footer,test_comms_tool,test_blocks_edge}.py
Success: no issues found in 3 source files

$ ./scripts/typecheck.sh
lorerunes/tests/test_roster_parser.py:53: error: Module "lorerunes" has no attribute "RosterParse"  [attr-defined]
... (packet 39's unbuilt contract)
typecheck: one or more legs failed
```

**This is NOT a wave-level "gates green" claim.** The canonical typecheck is RED at HEAD from
**packet 39's unbuilt contract (#306, corrected by #307)** — not mine, not touched, and every
error names `lorerunes/tests/test_roster_parser.py`. The greens above cover exactly: my three
files under `ruff` and `mypy`, and the eleven test files named in §4.2 in my scratch tree with
the reference build ported in. They say nothing about the full suite, the canonical typecheck,
or any file outside that set.

---

# §5 · WHAT IS LEFT OPEN, AND WHAT THE PINS NOW DEMAND OF THE BUILD

## 5.1 · W25 (`COMMS_FOOTER_PREFIX = "zzz"`) — DELIBERATELY LEFT OPEN

**The reason.** `_footer_line` imports the marker from production rather than transcribing
it, which is repo law (*prose that describes behaviour is DERIVED from it, never re-stated
beside it*) and is what keeps every SECTION B trigger leg discriminating when the footer's
shape changes. The price is that the marker's own bytes are invisible to the contract. The
adversary's R-5 verdict — *"CORRECT trade, state it"* — stands, and I did not re-litigate it.

**The bound, which is new and is why leaving it open is now cheap.** Before this wave a
`"zzz"` prefix cost nothing at all. It now costs everything *after* the prefix: the footer
must still carry both counts in their own roles (§2.1 W2/W12), must be the single last line
of the served response (W6/W11/W20), and must name `action=drain` on the resolved path
(W21). **The un-pinned surface is exactly the lead-in bytes and nothing else.**

**If the lead wants it closed:** one assertion on the constant's value in `test_comms_tool.py`
does it. I did not add it because no ruling specifies the marker's text — the packet's T3
shows an EXAMPLE footer, not a mandated prefix — and inventing one in a contract makes a
builder implement my invention. That is the design-vs-spec routing rule, so it is the lead's
call rather than mine.

## 5.2 · ⚠ THE ONE BUILD REQUIREMENT THIS WAVE ADDS — MP-6's ambiguity classification

`test_an_AMBIGUOUS_agent_is_taught_the_TRUTH_never_that_it_is_UNREGISTERED` was **RED against
the reference build**, which is the defect being caught, not a C-DEF. The reference build
catches every `AgentRegistryError` at the resolution seam and returns `None`, so the caller
renders one fixed teaching — and `AmbiguousAgentError` walks that door and is told
*"is not registered"*.

To produce the receipt I repaired the SCRATCH reference build (three edits: let
`AmbiguousAgentError` out of `_resolve_footer_identity`; render the registry's OWN
classification at the `agent=` teaching site; keep the free-text attribution path SILENT,
because the caller named no identity there). **That is evidence of satisfiability and NOT a
prescription** — the contract asserts only that the served text does not claim a registered
agent is unregistered, does name the offending value, does mention `session=`, and serves no
footer. Any mechanism reaching that is correct.

**⚠ A CORRECTION TO MY OWN BRIEF'S FRAMING, because the distinction matters.** The brief calls
MP-6 *"a LIVE TRUST DEFECT with served bytes"*. The bytes the adversary measured were served
by the **reference build in a scratch tree** — the footer does not exist in production yet, so
nothing is live. What is true and is the load-bearing half: **the same store and the same fact
already get two answers**, because `lore_comms action=fleet` classifies this ambiguity
correctly and teaches *"pass session= to disambiguate"*. Shipping the footer without this pin
would have made the falsehood live; it has not been. No finding filed, for that reason —
raising it here instead so the lead can rule if they disagree.

## 5.3 · Two pins whose fixture came from R4's TEXT, not from any implementation

`test_an_UNREAD_directive_is_ALSO_an_unacked_directive` is new and is derived from R4
verbatim: *"unacked directive" means `acked_at IS NONE` AND `grade = 'directive'`* — with **no
clause about `seen_at`**. Every other fixture in SECTION D seeds the two counts DISJOINTLY
(`unread` = unseen signals, `unacked` = seen directives), so a build adding a
`seen_at IS NOT NONE` conjunct — the natural mental model, *"unacked means I read it and owe a
reply"* — matched every one of them. That is the arithmetic-alignment fixture class. Both
existing implementations already satisfy it; see §7.2 for the ruling I am asking for anyway.

---

# §6 · THE R-4 CO-EDITS — exactly what I changed in the two files C3 does not name

Carried per the brief so the builder does not meet a red pin in a file it may not edit.

## 6.1 · `test_comms_tool.py` — three edits

1. **`_FOOTER_INSTRUCTIONS_PARAGRAPH`, a new module constant** holding the footer's
   `_INSTRUCTIONS` paragraph, declared ONCE and referenced by
   `_DECLARED_NON_COMMS_PARAGRAPHS`. C3 imports the constant rather than re-typing the
   prose, so the text has one home and two files assert different things about it.
2. **the constant added to `_DECLARED_NON_COMMS_PARAGRAPHS`**, immediately before
   `TOOL LOADING`. This is CL3's own documented outcome #2 (*"another packet legitimately
   edited `_INSTRUCTIONS` — then update `_DECLARED_NON_COMMS_PARAGRAPHS` and move on"*).
3. **#219's fourth prose site repaired** — the `TestEveryRecipientNameIsCharsetValidated…`
   class docstring no longer says the four identities share one charset *because they are
   inlined into live WHERE clauses*; it says because each is RENDERED into fleet-visible
   output, which is what the SECTION F invariant actually enforces. **This is now forced by a
   pin** (`TestTheFalseRationaleSurvivesNowhereInTheTree`), where the reference build repaired
   it by hand with nothing forcing it.

⚠⚠ **PROMINENT, BECAUSE IT AFFECTS EVERY AGENT IN THIS TREE: edit (2) makes CL3's terminating
pin (`test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`) RED at HEAD until the
builder ships the paragraph.** That is a contract behaving as a contract — the C3 file is
entirely red at HEAD for the same reason — but CL3 lives in a shared file, so a passing agent
will see it. Its failure message already teaches exactly this case.

⚠ **A DECISION I MADE AND AM SURFACING:** declaring the paragraph byte-exact means the
contract, not the builder, decides the served prose. I chose that deliberately — CL3 compares
byte-for-byte, so a contract saying only *"a footer paragraph exists"* would let the served
teaching say anything at all, and served prose is precisely the surface this repo has the most
receipts against. The text is the reference build's, and its CL1 vocabulary constraint is now
pinned rather than remembered. **If the lead wants the wording changed, change the constant —
one edit, and the pins follow.**

## 6.2 · `test_blocks_edge.py` — one edit

`_tool_seam` gains an empty `FakeAgentRegistry` and `FakeMessageLedger` with two
`type: ignore[assignment]`s. This is the co-edit `refbuild-c3-1` kept scratch-only (its §8.2)
and Ruling 5.3 routed to the builder's brief; landing it here removes the trap. The comment
records **why EMPTY fakes rather than absent attributes**: an absent attribute makes the
footer path raise `AttributeError`, which a dispatcher could legitimately swallow into "no
footer" — and a silently-skipped footer is confident silence, which is the failure mode this
slice exists to remove. The `type: ignore`s are load-bearing: without them the co-edit
introduces two NEW mypy errors (verified — `mypy` is clean on the file as landed).

---

# §7 · RESIDUALS, FORKS AND FLAGS — every one with an individual verdict

## 7.1 · FORK (stated reading, not silently resolved) — the RESOLVED footer's imperative

R8(2) rules the FALLBACK third-person *with no drain imperative*. It does **not** say in so
many words that the RESOLVED footer must name the drain call. Two readings:

* **Reading A (pinned):** the clause is a restriction ON THE FALLBACK, so the resolved path
  keeps the imperative T3's own worked example renders
  (*"— 9 directives await you — lore_comms action=drain …"*).
* **Reading B:** neither path names a call, and R8(2)'s clause is redundant.

Reading B makes R8's split — and the drain-theft hazard it exists to close — vacuous, so I
pinned A and wrote B into the class docstring. **A lead who rules B deletes
`TestTheRESOLVEDFooterIsACTIONABLE` and says so.**

## 7.2 · RULING REQUESTED — R4's overlap world (§5.3)

I pinned R4 as WRITTEN: an unread directive is also an unacked directive. Both the production
reference and the fake already agree, so the pin costs nothing today — but it is a reading of
a ruling, and it decides a served number. **If the operator intended `unacked` to mean "seen
but not acked", the pin is wrong and one fixture changes.** Surfacing rather than assuming.

## 7.3 · R-3 (the `SimpleNamespace` harness) — LEFT ALONE, deliberately, with the reason

The adversary is right that the harness PRESCRIBES an architecture: because it is a
`SimpleNamespace` rather than `AppContext.__new__(AppContext)` (the house idiom
`test_blocks_edge::_tool_seam` uses), every internal `self._method(…)` in the touched
dispatchers must be rewritten unbound. **I did not change it, because design-sidecar Ruling
5.3 already ROUTED that rider to the builder's brief** (*"the 23-call-site unbound-dispatcher
rewrite"*), and quietly re-deciding a routed ruling from inside a fixture is the same class of
move the adversary is complaining about. **The alternative, if the lead prefers it:** switch
`_footer_harness` to `AppContext.__new__(AppContext)` with `type: ignore[assignment]`s. That
is strictly more permissive (both bound and unbound styles then pass), removes the fixture's
vote on production style, and evaporates the production churn. It is a one-function change and
I will make it on request.

## 7.4 · The live-store dependency, priced

`test_comms_footer.py` now needs `spike-surreal` at `ws://127.0.0.1:18000`. Cost, measured:
five `real`-backend legs, of which the two 66-message over-cap legs dominate at ~11–12s each
(~24s serial, ~12s under `-n auto` since they land on different workers). The whole file is
**3.3s under `-n 8`** because the parametrised rows spread. I judged this worth it — it is the
only instrument that can see a wrong production predicate, and the DELETE probe is otherwise
unclosable — but it is a real cost and a new dependency for this file, so it is stated rather
than buried. **Alternative if the lead disagrees:** move the `real` legs into
`test_message_ledger.py`, which already owns the dual-drive fixture and the live store. That
file was outside my writable set, which is the only reason they are here.

## 7.5 · Two docs corpses, outside my writable set — ESCALATED, not dropped

The adversary's §9.1 found #219's false rationale stated in two committed docs:
`docs/design/2026-07-12-pkt28-c1-semantics.md:691` (quotes the false served string verbatim)
and `docs/plans/v2/03b-design-rulings-r2.md:150` (states it as a RULING). **My new sweep scans
`.py` only, so it does not cover them** — that is a stated bound, not an oversight I am hiding.
A future reader greps either file and re-installs the false model. One-line fix each; the lead
owns both.

## 7.6 · Reuse-by-import across test modules — named, per the DRY law

`_pending_traffic_over`'s real leg imports `_ref` and `_seed_agents` from
`test_message_ledger`. That is REUSE, not a second harness — writing my own agent-table
seeding would be copy #2 of a policy (which store, which DDL, which columns). The repo already
does this (`from test_comms_tool import _COMMS_DUTY_VOCABULARY`, `from test_mcp_server import
_config, _slug`), so it is the house idiom, but cross-module private imports are a design
choice and I am naming it rather than letting it pass as trivia.

## 7.7 · Bounds I am carrying forward unchanged

* `_registry_reads` counts `get_agent` specifically — a build resolving through some other
  registry method reads 0 and passes. Ruling 5.3 makes any second resolution path a #102
  escalation in its own right, so the bound is accepted, and it is re-stated in the helper's
  docstring rather than inherited silently.
* `MINIMUM_SITES_SCANNED = 100` vs a measured 122 (adversary R-6) — sound as a floor,
  unchanged.
* The wrong-build driver runs one suite (§3.2).
* `_rendered_counts` accepts two renderings; a build inventing a third reads as *no number in
  this role* and reddens with a message naming exactly that. A diagnosable false RED is the
  correct failure direction for an extractor, and it is documented in the helper.

---

# §8 · PACKAGES CONSIDERED — one row per mechanism this contract SPECIFIES

| mechanism | library evaluated | what I **READ** | verdict |
|---|---|---|---|
| counting registry reads / ledger calls, with their ARGUMENTS | **stdlib `unittest.mock.AsyncMock(wraps=…)`** | its `await_args_list` / `await_count` surface, and the hand-rolled `_counting` closure it replaces (which incremented an int and discarded `*args, **kwargs`) | **replace — ADOPTED.** The old shape is *why* W4 and W3 were unassertable: an instrument that cannot see arguments cannot see a build that called the right seam with the wrong identity. |
| a live SurrealDB for the REAL `pending_traffic` leg | **in-tree `_surreal_harness`** (`make_env`, `unique_database`, `connect_admin`, `drop_database`) + `test_message_ledger._ref` / `._seed_agents` | `_surreal_harness`'s exported names and `make_env`'s signature; `test_message_ledger`'s `message_ledger_factory` and `_seed_agents` bodies (the `generate_agent_ddl()` + `UPSERT … CONTENT` idiom for the real backend) | **replace — REUSED BY IMPORT.** Writing a second agent-seeding recipe would be copy #2 of a policy. Only the six-line ledger construction is local, and that is trivia. |
| seeding the live inbox to R4's states | the ledger's **own public verbs** `send` / `drain` | `MessageLedger.send`'s signature and docstring (sender/recipients/grade/session) and `drain`'s (`agent_id`, `limit`, `peek`, and that a non-peek drain stamps exactly the served window) | **replace** — public verbs, never poked edges, so the states counted are states production can reach. |
| extracting a rendered number IN a role | **stdlib `re`** | the two accepted forms and their digit-exclusion windows, checked against the reference render `"… 7 unread and 3 unacked directive(s); …"` and against the swapped variant | **keep, stdlib.** A parser would be a mechanism for a one-line property; the bound is stated in the helper. |
| the query-text interpolation scan (SECTION F, inherited) | **`ruff` S608** vs the in-tree AST scanner | the adversary's live measurement (113 hits / 15 files) and its reach diff against `QUERY_RECEIVERS`, re-read this run | **keep_with_trigger — UNCHANGED.** Its trigger (a new seam spelling defeats `QUERY_RECEIVERS`, or an identity-bearing value appears in a non-Surreal store seam) stands as the adversary wrote it. |
| the #219 prose sweep | stdlib string containment over the workspace tree | — this is a project-specific predicate (*"does our prose still teach a retired rationale"*), not a general mechanism | **bespoke, one line** — domain logic; no library models it. |

No missing dependency, so no install authorization is needed.

---

# §9 · THE INSTRUMENT (brief-base §1 — a deliverable, not scratch)

`c3fix_wrongbuilds.py` lives in `/home/ejprice/scratch-c3-ref/`, which is **disposable by
design**. Its full text is therefore reproduced here, and the lead should `git mv` it into
`scripts/` if the wave wants it re-runnable — that is #278's perversity, and I am naming it
rather than assuming someone will.

Its 26 mutation definitions are the compact, executable statement of *"what wrong build does
each pin kill"*, so it is worth keeping for the delta-adversary pass this wave expects.

**PASTED VERBATIM BELOW**, because the protocol's two sanctioned outcomes are *committed*
or *pasted in a code fence*, and I cannot commit it: `scripts/**` is DO-NOT-TOUCH this
wave and I run no git commands. Naming it in prose would be neither.

⚠ **The lead should still `git mv` it into `scripts/`** — a pasted instrument is worse
than a committed one and far better than a lost one.

```python
#!/usr/bin/env python3
"""c3fix_wrongbuilds.py — re-run the adversary's 26 wrong builds against the REPAIRED C3
contract, and diff the observed RED set against a DECLARED one BOTH WAYS.

Run from the scratch reference-build root:

    uv run python c3fix_wrongbuilds.py            # every wrong build
    uv run python c3fix_wrongbuilds.py W2 W12     # a subset

WHY THIS AND NOT scripts/mutation_proof.py DIRECTLY: several wrong builds need MORE THAN
ONE anchored edit (W5 breaks four return sites; W15 forks one seam per dispatcher), and
mutation_proof.py takes a single anchor. This driver keeps every property that makes that
tool trustworthy and adds multi-edit support:

  * every edit asserts its anchor matched EXACTLY the declared number of times, and the
    run ABORTS if it did not — a mutation that never LANDED prints a green tail that reads
    exactly like a successful proof (#194);
  * the DECLARED red set is validated against ``pytest --collect-only`` BEFORE any run, so
    a typo'd or renamed node id is a hard error rather than a silently-empty expectation;
  * the observed set is diffed BOTH WAYS — unexpected reds AND declared reds that stayed
    GREEN, the direction that catches a mutation landing in dead code;
  * production files are restored from a CONTENT backup (never a hash list) and the
    restore is verified byte-exact after every wrong build.

⚠ DECLARED SETS ARE AT FUNCTION GRANULARITY (``file::Class::func``), not per-parameter
node id. What is predicted is WHICH PIN fires; a parametrised pin's rows multiply for
reasons (backend, caller, traffic world) orthogonal to the defect. The both-ways diff is
unaffected: an unexpected FUNCTION reddening is still a failure, and a declared function
that stayed FULLY green is still a failure.

⚠ SCOPE BOUND: only ``test_comms_footer.py`` is run. A wrong build that also reddens a pin
in another suite is invisible here; that is stated rather than implied.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT = "loremaster/tests/test_comms_footer.py"
SERVER = "loremaster/loremaster/server.py"
MESSAGES = "loremaster/loremaster/messages.py"
BACKUP = ROOT / ".c3fix-pristine"
MUTABLE = (SERVER, MESSAGES)

Edit = tuple[str, str, str, int]  # (file, anchor, replacement, occurrences)

# --------------------------------------------------------------------------- #
# The wrong builds. Each is (id, prose, edits, declared-red functions).
# --------------------------------------------------------------------------- #

_AUTH_COUNTS = (
    "                unread=traffic.unread,\n"
    "                unacked=traffic.unacked_directives,\n"
)
_AUTH_COUNTS_SWAPPED = (
    "                unread=traffic.unacked_directives,\n"
    "                unacked=traffic.unread,\n"
)
_QUIET_GUARD = "        if traffic.unread == 0 and traffic.unacked_directives == 0:\n"
_SEAM_CALL = "traffic=await self.message_ledger.pending_traffic(agent_id=agent_id),"
_PRIVATE_COUNT = (
    "traffic=PendingTraffic("
    "unread=sum(1 for (m, a), e in self.message_ledger.db.edges.items() "
    "if a == agent_id and e.seen_at is None), "
    "unacked_directives=sum(1 for (m, a), e in self.message_ledger.db.edges.items() "
    "if a == agent_id and e.acked_at is None "
    'and self.message_ledger.db.messages[m].grade == "directive")),'
)
_APPEND = '        return "\\n".join([rendered, str(line)])'
_CANDIDATE = (
    "        candidate = next(\n"
    "            (\n"
    "                value\n"
    "                for value in attributions\n"
    "                if value is not None and AGENT_NAME_PATTERN.fullmatch(value)\n"
    "            ),\n"
    "            None,\n"
    "        )\n"
)
_UNGATED_SCAN_FOR_TWO = (
    "        if len(attributions) < 3:\n"
    "            for value in attributions:\n"
    "                if value is None:\n"
    "                    continue\n"
    "                probe = await AppContext._resolve_footer_identity(\n"
    "                    self, value, session=None\n"
    "                )\n"
    "                if probe is not None:\n"
    "                    pname, pid = probe\n"
    "                    return AppContext._comms_footer(\n"
    "                        identity=pname,\n"
    "                        traffic=await self.message_ledger.pending_traffic(agent_id=pid),\n"
    "                        authenticated=False,\n"
    "                    )\n"
    "            return None\n"
) + _CANDIDATE

C = "loremaster/tests/test_comms_footer.py"

WRONG_BUILDS: list[tuple[str, str, list[Edit], list[str]]] = [
    (
        "W2",
        "the two counts are SWAPPED in the authenticated render",
        [(SERVER, _AUTH_COUNTS, _AUTH_COUNTS_SWAPPED, 1)],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    (
        "W12",
        "the counts are a CONSTANT 1 and 1 whenever anything pends",
        [
            (SERVER, "unread=traffic.unread,", "unread=1,", 2),
            (SERVER, "unacked=traffic.unacked_directives,", "unacked=1,", 2),
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_FALLBACK_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    (
        "W3",
        "the footer re-derives the counts in the SERVER; pending_traffic is never called",
        [(SERVER, _SEAM_CALL, _PRIVATE_COUNT, 2)],
        [
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "DEL",
        "MessageLedger.pending_traffic DELETED from production entirely",
        [
            (MESSAGES, "    async def pending_traffic(", "    async def _deleted_traffic(", 1),
            (SERVER, _SEAM_CALL, _PRIVATE_COUNT, 2),
        ],
        [
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_the_seam_counts_unread_and_unacked_DIRECTIVES_separately",
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_a_SIGNAL_is_never_counted_as_an_unacked_directive",
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_an_UNREAD_directive_is_ALSO_an_unacked_directive",
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_PRODUCTION_ledger_exposes_pending_traffic",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_DOUBLE_conforms_to_the_production_seam",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "W23",
        "the footer fires on unread > 0 ALONE — 0 unread + 3 unacked directives gets nothing",
        [(SERVER, _QUIET_GUARD, "        if traffic.unread == 0:\n", 1)],
        [
            f"{C}::TestNoTrafficMeansNoFooter"
            "::test_POSITIVE_CONTROL_the_same_write_WITH_traffic_DOES_footer",
        ],
    ),
    (
        "W4",
        "session= is IGNORED — agent= resolves unscoped",
        [
            (
                SERVER,
                "                    self, agent, session=session\n",
                "                    self, agent, session=None\n",
                1,
            )
        ],
        [
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
    (
        "W5",
        "findings' four single-item write verbs NEVER footer",
        [
            (
                SERVER,
                'return f"reported finding #{report.number} (id {report.id}, status open)", True',
                'return f"reported finding #{report.number} (id {report.id}, status open)", False',
                1,
            ),
            (
                SERVER,
                "return AppContext._render_finding_transition(acked, actor), True",
                "return AppContext._render_finding_transition(acked, actor), False",
                1,
            ),
            (
                SERVER,
                "return AppContext._render_finding_transition(resolved, actor), True",
                "return AppContext._render_finding_transition(resolved, actor), False",
                1,
            ),
            (
                SERVER,
                "return AppContext._render_finding_transition(closed, actor), True",
                "return AppContext._render_finding_transition(closed, actor), False",
                1,
            ),
        ],
        [
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB"
            "::test_EVERY_findings_WRITE_action_footers",
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_findings_spends_ONE_registry_read_AT_MOST",
        ],
    ),
    (
        "W10",
        "tasks' transition and supersede NEVER footer",
        [
            (
                SERVER,
                "return AppContext._render_task_transition(task, actor), True",
                "return AppContext._render_task_transition(task, actor), False",
                1,
            ),
            (
                SERVER,
                'return f"superseded task {task_id}; successor {successor_id} (status open)", True',
                'return f"superseded task {task_id}; successor {successor_id} (status open)", False',
                1,
            ),
        ],
        [
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB::test_EVERY_tasks_WRITE_action_footers",
        ],
    ),
    (
        "W24",
        "acknowledge_many footers UNCONDITIONALLY, ignoring L2's write-count",
        [
            (
                SERVER,
                "            return batch_render, write_count >= _MIN_COUNT",
                "            return batch_render, (\n"
                "                True\n"
                "                if action == _FINDING_ACTION_ACKNOWLEDGE_MANY\n"
                "                else write_count >= _MIN_COUNT\n"
                "            )",
                1,
            )
        ],
        [
            f"{C}::TestABatchThatWroteNOTHINGServesNoFooter"
            "::test_the_footer_follows_the_WRITE_COUNT_not_the_CALL",
        ],
    ),
    (
        "W6",
        "the footer REPLACES the dispatcher's render — the tool's answer is destroyed",
        [(SERVER, _APPEND, "        return str(line)", 1)],
        [
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND"
            "::test_the_underlying_answer_SURVIVES_the_footer",
        ],
    ),
    (
        "W11",
        "the footer is appended TWICE",
        [(SERVER, _APPEND, '        return "\\n".join([rendered, str(line), str(line)])', 1)],
        [
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_exactly_ONE_footer_line_is_served",
        ],
    ),
    (
        "W20",
        "the footer is PREPENDED, above the answer it annotates",
        [(SERVER, _APPEND, '        return "\\n".join([str(line), rendered])', 1)],
        [
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_the_footer_is_the_LAST_line",
        ],
    ),
    (
        "W7",
        "unacked_directives CLAMPS at 5 — a cap used as a denominator",
        [
            (
                MESSAGES,
                "            unacked_directives=sum(\n",
                "            unacked_directives=min(5, sum(\n",
                1,
            ),
            (
                MESSAGES,
                '                and row.get("grade") == MESSAGE_GRADE_DIRECTIVE\n            ),',
                '                and row.get("grade") == MESSAGE_GRADE_DIRECTIVE\n            )),',
                1,
            ),
        ],
        [
            f"{C}::TestThePendingTrafficCountIsONEImplementation"
            "::test_the_count_spans_the_WHOLE_inbox_never_a_capped_WINDOW",
        ],
    ),
    (
        "W8",
        "the footer only fires for identities CONTAINING A HYPHEN",
        [
            (
                SERVER,
                _QUIET_GUARD,
                '        if "-" not in identity:\n            return None\n' + _QUIET_GUARD,
                1,
            )
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND"
            "::test_exactly_ONE_footer_line_is_served",
            f"{C}::TestTheFooterIsAPPENDEDExactlyOnceAtTheEND::test_the_footer_is_the_LAST_line",
            f"{C}::TestTheRESOLVEDFooterIsACTIONABLE::test_the_RESOLVED_footer_names_the_drain_CALL",
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB::test_EVERY_tasks_WRITE_action_footers",
            f"{C}::TestTheFooterRidesTheOUTCOMENotTheVERB"
            "::test_EVERY_findings_WRITE_action_footers",
            f"{C}::TestTheProductionSeamEXISTSAndIsTheThingDriven"
            "::test_the_FOOTERS_counts_come_THROUGH_the_ledger_seam",
        ],
    ),
    (
        "W9",
        "R8(1)'s teaching degenerates to the BARE offending value, no guidance",
        [
            (
                SERVER,
                '                    "(no pending-traffic line: agent={offending} is not '
                'registered — "\n                    "register it with lore_comms '
                'action=register, or fix the spelling)",\n',
                '                    "{offending}",\n',
                1,
            )
        ],
        [
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_the_teaching_names_a_REMEDY_not_just_the_offending_value",
        ],
    ),
    (
        "W17",
        "the teaching LEAKS onto READ paths (query/rollup)",
        [
            (
                SERVER,
                "        if not wrote:\n            return None\n",
                "        if not wrote:\n"
                "            if agent is None:\n"
                "                return None\n"
                "            try:\n"
                "                probe = await AppContext._resolve_footer_identity(\n"
                "                    self, agent, session=session\n"
                "                )\n"
                "            except _AmbiguousAgentError:\n"
                "                return None\n"
                "            if probe is None:\n"
                "                return render_line(\n"
                '                    "(no pending-traffic line: agent={offending} is not '
                'registered — "\n'
                '                    "register it with lore_comms action=register, or fix '
                'the spelling)",\n'
                "                    offending=sanitise_line(agent),\n"
                "                )\n"
                "            return None\n",
                1,
            )
        ],
        [
            f"{C}::TestTheUNRESOLVABLETeachingIsUSEFULAndStaysOffREADS"
            "::test_the_teaching_NEVER_appears_on_a_READ",
        ],
    ),
    (
        "W13",
        "session= never lands on the tool schema (R1's '+session')",
        [
            (
                SERVER,
                "            Field(description=_COMMS_IDENTITY_SESSION_DESCRIPTION),",
                "            Field(),",
                3,
            )
        ],
        [
            f"{C}::TestTheAgentParameterDescriptionIsSHAREDAndStatesThePayoff"
            "::test_all_three_tools_ALSO_expose_session_with_ONE_shared_description",
            f"{C}::TestTheAgentParameterDescriptionIsSHAREDAndStatesThePayoff"
            "::test_the_session_description_says_WHEN_a_caller_needs_it",
        ],
    ),
    (
        "W15",
        "the one-read ceiling and the charset gate hold on tasks and are BROKEN on "
        "findings + claim_task (an ungated per-attribution SCAN)",
        [(SERVER, _CANDIDATE, _UNGATED_SCAN_FOR_TWO, 1)],
        [
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_findings_spends_ONE_registry_read_AT_MOST",
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_claim_task_spends_ONE_registry_read_AT_MOST",
            f"{C}::TestTheREADBudgetHoldsOnALLTHREEDispatchers"
            "::test_findings_never_consults_a_SECOND_attribution",
        ],
    ),
    (
        "W16",
        "the resolver falls back to candidate.startswith(registered_name)",
        [
            (
                SERVER,
                "        if row.name != name:",
                "        if not name.startswith(row.name):",
                1,
            ),
            (
                SERVER,
                "            row = await self.agent_registry.get_agent(name, session=session)",
                "            try:\n"
                "                row = await self.agent_registry.get_agent(name, session=session)\n"
                "            except _UnknownAgentError:\n"
                "                rows = [\n"
                "                    r\n"
                "                    for r in self.agent_registry.db.agents.values()\n"
                "                    if name.startswith(r.name)\n"
                "                ]\n"
                "                if not rows:\n"
                "                    raise\n"
                "                row = rows[0]",
                1,
            ),
        ],
        [
            f"{C}::TestTheFallbackIsThirdPersonWithNoDrainImperative"
            "::test_the_fallback_refuses_a_charset_legal_SUPERSTRING_too",
        ],
    ),
    (
        "W18",
        "link 2's in-code guard `if row.name != name` is DELETED",
        [
            (
                SERVER,
                "        if row.name != name:",
                "        if False:",
                1,
            )
        ],
        [
            f"{C}::TestTheSERVERVerifiesTheRowTheRegistryHandedBack"
            "::test_a_row_whose_NAME_differs_from_the_request_NEVER_footers",
        ],
    ),
    (
        "W19",
        "an AMBIGUOUS agent= (registered in two sessions) is taught 'is not registered'",
        [
            (
                SERVER,
                "        except _AmbiguousAgentError:\n"
                "            # NOT \"unregistered\": the name IS registered, in more than one",
                "        except _AmbiguousAgentError:  # noqa: B025\n"
                "            return None\n"
                "        except _AmbiguousAgentError:\n"
                "            # NOT \"unregistered\": the name IS registered, in more than one",
                1,
            )
        ],
        [
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_an_AMBIGUOUS_agent_is_taught_the_TRUTH_never_that_it_is_UNREGISTERED",
        ],
    ),
    (
        "W21",
        "the RESOLVED caller's footer loses its drain imperative",
        [
            (
                SERVER,
                '                "directive(s); lore_comms action=drain agent={identity}",',
                '                "directive(s) somewhere in your fleet inbox",',
                1,
            )
        ],
        [
            f"{C}::TestTheRESOLVEDFooterIsACTIONABLE::test_the_RESOLVED_footer_names_the_drain_CALL",
        ],
    ),
    (
        "W22",
        "only the FALLBACK render is a bare f-string (the authenticated one stays Rendered)",
        [
            (
                SERVER,
                '        return render_line(\n'
                '            "{prefix} {identity} has {unread} unread and {unacked} unacked '
                'directive(s) "\n'
                '            "(matched by name on this row, not an authenticated caller)",\n'
                "            prefix=sanitise_line(COMMS_FOOTER_PREFIX),\n"
                "            identity=sanitise_line(identity),\n"
                "            unread=traffic.unread,\n"
                "            unacked=traffic.unacked_directives,\n"
                "        )",
                "        return (  # type: ignore[return-value]\n"
                '            f"{COMMS_FOOTER_PREFIX} {identity} has {traffic.unread} unread "\n'
                '            f"and {traffic.unacked_directives} unacked directive(s) "\n'
                '            f"(matched by name on this row, not an authenticated caller)"\n'
                "        )",
                1,
            )
        ],
        [
            f"{C}::TestTheFALLBACKFooterIsAlsoBuiltThroughTheRenderSeam"
            "::test_the_FALLBACK_footer_helper_returns_Rendered_not_a_bare_str",
        ],
    ),
    (
        "W14",
        "R1's closing sentence never lands — no footer paragraph in _INSTRUCTIONS",
        [
            (
                SERVER,
                '    "PENDING TRAFFIC: pass agent= (and session= when your name is not unique) to "',
                '    "PENDING TRAFFIC PLACEHOLDER "',
                1,
            )
        ],
        [
            f"{C}::TestTheFooterTeachingLandsThroughTheDeclaredAllowlist"
            "::test_the_footer_teaching_ACTUALLY_LANDS_in_the_served_INSTRUCTIONS",
        ],
    ),
    (
        "W1b",
        "ONE count placeholder AND its kwarg are dropped together — legal render, "
        "silently half a footer (the case the render seam's unused-kwarg guard CANNOT see)",
        [
            (
                SERVER,
                '                "{prefix} {identity} — you have {unread} unread and {unacked} '
                'unacked "\n                "directive(s); lore_comms action=drain '
                'agent={identity}",\n'
                "                prefix=sanitise_line(COMMS_FOOTER_PREFIX),\n"
                "                identity=sanitise_line(identity),\n"
                "                unread=traffic.unread,\n"
                "                unacked=traffic.unacked_directives,\n",
                '                "{prefix} {identity} — you have {unread} unread; "\n'
                '                "lore_comms action=drain agent={identity}",\n'
                "                prefix=sanitise_line(COMMS_FOOTER_PREFIX),\n"
                "                identity=sanitise_line(identity),\n"
                "                unread=traffic.unread,\n",
                1,
            )
        ],
        [
            f"{C}::TestTheFooterServesTheLEDGERSTwoCounts"
            "::test_the_RESOLVED_footer_carries_both_counts_in_their_own_roles",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_footer_counts_the_inbox_of_the_NAMED_SESSION",
            f"{C}::TestTheSESSIONScopesTheIdentityAndItsInbox"
            "::test_the_OTHER_sessions_counts_are_served_for_the_OTHER_session",
        ],
    ),
]


def _backup() -> None:
    BACKUP.mkdir(exist_ok=True)
    for relative in MUTABLE:
        shutil.copy2(ROOT / relative, BACKUP / Path(relative).name)


def _restore() -> None:
    for relative in MUTABLE:
        shutil.copy2(BACKUP / Path(relative).name, ROOT / relative)
    for relative in MUTABLE:
        if (ROOT / relative).read_bytes() != (BACKUP / Path(relative).name).read_bytes():
            raise SystemExit(f"RESTORE FAILED for {relative}")


def _collect() -> set[str]:
    proc = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "-p", "no:randomly", CONTRACT],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ids = set()
    for line in proc.stdout.splitlines():
        if "::" in line and line.startswith(CONTRACT):
            ids.add(re.sub(r"\[[^\]]*\]$", "", line.strip()))
    if not ids:
        raise SystemExit(f"collect-only returned nothing:\n{proc.stdout}\n{proc.stderr}")
    return ids


def _apply(edits: list[Edit]) -> None:
    for relative, anchor, replacement, occurrences in edits:
        path = ROOT / relative
        text = path.read_text()
        found = text.count(anchor)
        if found != occurrences:
            _restore()
            raise SystemExit(
                f"ANCHOR MISMATCH in {relative}: expected {occurrences} occurrence(s), "
                f"found {found}. Anchor:\n{anchor!r}"
            )
        path.write_text(text.replace(anchor, replacement))


def _run() -> set[str]:
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q", "-p", "no:randomly", "-n", "8", CONTRACT],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    reds = set()
    for line in proc.stdout.splitlines():
        if line.startswith("FAILED ") or line.startswith("ERROR "):
            node = line.split(" ", 1)[1].split(" - ")[0].strip()
            reds.add(re.sub(r"\[[^\]]*\]$", "", node))
    tail = [line for line in proc.stdout.splitlines() if " passed" in line or " failed" in line]
    print(f"      tail: {tail[-1].strip() if tail else '(no count line!)'}")
    return reds


def main(argv: list[str]) -> int:
    wanted = set(argv[1:])
    collected = _collect()
    print(f"collected {len(collected)} distinct test functions in {CONTRACT}")

    bad = []
    for wid, _prose, _edits, declared in WRONG_BUILDS:
        for node in declared:
            if node not in collected:
                bad.append(f"{wid}: declared node does not exist -> {node}")
    if bad:
        print("\n".join(bad))
        return 2

    _backup()
    failures: list[str] = []
    for wid, prose, edits, declared in WRONG_BUILDS:
        if wanted and wid not in wanted:
            continue
        print(f"\n=== {wid}: {prose}")
        _apply(edits)
        print("      LANDED (every anchor matched its declared count)")
        observed = _run()
        _restore()
        unexpected = sorted(observed - set(declared))
        stayed_green = sorted(set(declared) - observed)
        verdict = "CAUGHT" if declared and not unexpected and not stayed_green else "MISMATCH"
        if unexpected:
            print("      UNEXPECTED RED:\n        " + "\n        ".join(unexpected))
        if stayed_green:
            print("      DECLARED RED BUT STAYED GREEN:\n        " + "\n        ".join(stayed_green))
        print(f"      -> {verdict} ({len(observed)} function(s) red)")
        if verdict != "CAUGHT":
            failures.append(wid)
    print("\n" + ("ALL WRONG BUILDS CAUGHT" if not failures else f"MISMATCHES: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

---

# §10 · VERDICT

The contract's two most load-bearing surfaces — **the numbers the footer serves, and the seam
it serves them from** — are now the two it asserts hardest: a value→role extractor over two
unrelated count pairs on both render paths, and a seam that must EXIST in production, must
CONFORM to its double, must be CALLED once with the resolved identity's row id, and is graded
against a live store as well as a fake.

**24 of the adversary's 25 surviving wrong builds are closed with a landed mutation and a
both-ways RED diff; the 25th (W25) is open on purpose, with its reason and its residual
damage bounded; and one further wrong build of my own (W1b) is closed as well. The
contract goes 128 passed / 0 failed against a correct build, and the eleven seam suites go
2686 passed / 0 failed.**

Four decisions are surfaced for the lead (§7.1, §7.2, §7.3, §7.5) and none of them blocks a
builder. One build requirement is added and stated (§5.2). A fix wave is where a narrow patch
satisfying the letter of a finding is most likely, so the delta adversary should start at
§5.1 (what I left open), §3.3 (where my own predictions were wrong) and §7.4 (the cost I
chose to pay).
