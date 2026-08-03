# REPORT-refbuild-c3-1 — C3's satisfiability receipt: **PRODUCED (0 failed)**, after seven defects found by executing

**Three phases, one report.** PHASE 1 (§§0–7) REFUSED the receipt and diagnosed five C-DEFs
against the contract as committed at `533d917`. PHASE 2 (§8) repaired C-DEFs 1–4 under the
lead's scope grant. PHASE 3 (§9) applied design-sidecar **Ruling 5**, which settled C-DEF 5
and corrected #305 — and whose mutation proofs exposed **two further defects a green suite
could not see**. C3 now goes **0-failed**.

## SUMMARY BLOCK

```
brief-base v9 read
brief project v7 read
state: done — ⛔ THE SATISFIABILITY RECEIPT IS PRODUCED (§9.4).
  C3 alone: 48 passed, 0 failed. The 11 seam suites: 2607 passed, 14 skipped, 3 xfailed,
  ZERO FAILURES. Zero mypy errors in the C3 file set; ruff clean. C3 is builder-ready.
  ⚠ NOT a wave-level gates-green claim — scoped in §9.5; typecheck.sh is RED at HEAD from
  packet 39 (finding #306), which is not mine and which I did not touch.
  SEVEN defects total, every one found by EXECUTING rather than reading: five C-DEFs (§3),
  plus two that survived the repairs and only a MUTATION could see (§9.2).
deviation: PHASE 1 ran with test_comms_footer.py NOT writable and produced the refusal via
  an out-of-tree plugin (§6). Phases 2-3 landed everything in the file itself under grant;
  the plugin is REDUNDANT and no receipt run uses it.
deviation: the build's co-edit to test_blocks_edge.py::_tool_seam lives in SCRATCH ONLY —
  the grant named one repo file and I did not widen it myself. Exact diff in §8.2.
deviation: I synced the repo's contract file into the scratch tree — the prepared copy was
  STALE (it predated §4.5.3c's TestAHostileIdentity… rewrite). §1.
deviation: Ruling 5.2's world (i) is UNREACHABLE at these dispatchers (every write action
  requires an attribution). Derived, pinned in its constructible form, and SAID rather
  than silently dropped. §9.1.
Packages considered: none — no new mechanism. Every seam this build needed already exists
  in-tree and was CALLED, not re-implemented: loremaster.render.render_line (read its
  source + the four-instrument docstring; the footer is assembled through it, prefix passed
  as a VALUE so the constant has ONE home) · loremaster.sanitise.sanitise_line (read the
  signature: str -> SafeLine) · MessageLedger._as_rows/_query (read drain's body for the
  TO_RELATION statement idiom) · pydantic BaseModel + ConfigDict(extra="forbid") (the house
  value-object idiom, copied from MessageDrainResult). Verdict on all: replace (use in-tree).
decisions-needed: none — C-DEF 5 and #305 were ruled (sidecar §5) and are applied. Nothing
  held, no fork open, no RED handed back.
receipt pointers: ⛔ THE RECEIPT §9.4 · Ruling 5 applied §9.1 · the two mutation-found
  defects §9.2 · mutation table §9.3 · gate scope §9.5 · still-open §9.6 · the original
  five C-DEFs §3 · cross-file co-edits §4 · the diagnostic plugin, verbatim §6.1.
```

---

# §0 · CAPABILITY CHECK (brief-base §4, first thing in the report)

Everything the brief demanded was reachable. `lore_comms register` succeeded (fleet
`packet-04b2-wavec`, role builder). The lore tool surface loaded on the keyword form
(`ToolSearch "+lore"`, 15 tools). The scratch tree, `scripts/scratch_copy.sh`,
`scripts/scratch_provenance.py`, `scripts/typecheck.sh`, `uv`, `ruff`, `mypy` and `pytest
-n auto` all ran. No brief clause was unmeetable.

One honest tool note (brief-base §4, last bullet): **the structural questions in this run
were answered by direct `Read`/`grep`/AST scanning, not by lore.** They were not
code-structure lookups — they were *"what does this exact fixture pass on line N"* and
*"does this fake expose method X"*, where the graph has nothing to add over the file. I used
`lore_comms` for coordination only. No friction to file: lore was not routed around, it was
not the right instrument.

---

# §1 · PROVENANCE — which tree I graded (#140)

⚠ **The prepared tree was STALE and I re-synced it.** `/home/ejprice/scratch-c3-ref` sat at
`a88e7c5` carrying a contract file that predated §4.5.3c's rewrite of
`TestAHostileIdentityCannotReachTheFooterAtAll` (191 diff lines: the neutralisation pins
replaced by the cannot-reach + registered-name-never-raw-string pins). I copied the repo's
committed-tree file over it and verified byte-identity before building anything. **Everything
below grades the repo's file, not the predecessor's draft.** The commit delta `a88e7c5..f67a219`
is one docs file (`REPORT-lead-04b2-wavec.md`), so the production code in the scratch tree is
current with `f67a219`.

⚠ **Re-verified at the END of the run, after the lead committed the contract as `533d917`:**
`git show 533d917:loremaster/tests/test_comms_footer.py` is **byte-identical** to the file in
my scratch tree. So every number in this report grades the file as committed — not a
working-tree snapshot that has since moved.

Provenance, re-verified by me with the blessed tool (`scripts/scratch_provenance.py`, exit 0)
and independently by direct import:

```
loremaster:  /home/ejprice/scratch-c3-ref/loremaster/loremaster/__init__.py
lorerunes:   /home/ejprice/scratch-c3-ref/lorerunes/lorerunes/__init__.py
loresigil:   /home/ejprice/scratch-c3-ref/loresigil/loresigil/__init__.py
lorescribe:  /home/ejprice/scratch-c3-ref/lorescribe/lorescribe/__init__.py
```

All four resolve INSIDE the scratch root; none resolves home. The three #140 poison modes are
closed.

---

# §2 · THE REFERENCE BUILD — what I implemented

Scratch only. Five files, `558 insertions(+), 32 deletions(-)`:

| file | what landed |
|---|---|
| `loremaster/messages.py` | `PendingTraffic{unread, unacked_directives}` · `MessageLedger.pending_traffic(*, agent_id)` |
| `loremaster/server.py` | `COMMS_FOOTER_PREFIX` · `AppContext._comms_footer` · `_comms_footer_line` · `_resolve_footer_identity` · `_with_comms_footer` · `agent`/`session` on all three dispatchers + all three tool seams · one shared `Field(description=)` constant · the `_INSTRUCTIONS` paragraph · #219's three production prose sites · R-5's `Raises:` line |
| `loremaster/tests/_message_fakes.py` | `FakeMessageLedger.pending_traffic` — an INDEPENDENT count over `self.db`, never a delegation |
| `loremaster/tests/test_comms_tool.py` | CL3's sanctioned co-edit (`_DECLARED_NON_COMMS_PARAGRAPHS`) + #219's fourth site |
| `loremaster/tests/test_blocks_edge.py` | the `_tool_seam` co-edit its own docstring predicted (§4.2) |

### 2.1 Design decisions worth the real builder's attention

- **SINGLE EXIT, enforced structurally.** `tasks`/`findings` are now thin wrappers over
  `_tasks_dispatch`/`_findings_dispatch`, which return `tuple[str, bool]` — the render
  BESIDE whether the call actually MUTATED. The footer is appended in one place, so it
  cannot be forgotten on one of seven return paths. `_resolve_or_acknowledge_many` returns
  `tuple[str, int]` (L2's write-count, DERIVED from the loop that already computes the
  header's `success_count`, never a flag set beside it).
- **⚠ EVERY DISPATCHER-INTERNAL CALL HAD TO BECOME `AppContext.X(self, …)`.** C3 drives the
  UNBOUND dispatchers against a `SimpleNamespace` double, so `self._render_task_rows(...)`
  raises `AttributeError`. This is already the house idiom in `comms`
  (`AppContext._validate_comms_identities(...)`) but `tasks`/`findings`/`claim_task` were
  never written that way. **23 call sites rewritten** — mechanical, but the builder will hit
  it in minute one and the contract does not warn.
- **The footer is built through `render_line`, and the PREFIX is passed as a VALUE**
  (`prefix=sanitise_line(COMMS_FOOTER_PREFIX)`) rather than interpolated into the template.
  The AST template-literal pin requires a literal template, and a second copy of the marker
  is exactly the drift `_footer_line`'s import-from-production comment exists to prevent.
- **The rendered identity is `row.name` from the registry row, never the caller's string.**
  §4.5.3c's load-bearing pin passes for that reason and would fail a raw-echo build.
- **`pending_traffic` carries NO `LIMIT`.** Deliberately not `drain(peek=True)`: that clamps
  at the drain cap and would serve `50` for every busier inbox.

### 2.2 ⚠ WHERE §4.5.3's BUILD SPEC IS UNDER-DETERMINED (escalation, not a silent pick)

The spec names the symbols but **never names the identity-RESOLUTION seam**, and the two
candidate readings produce different code and different test outcomes:

- **Reading A (what I built): resolve through `agent_registry.get_agent`.** This is R1
  verbatim (*"resolved through the registry"*) and R8's own cost line (*"one charset-gated
  **registry read** per identity-less write"*). It is the only reading compatible with ONE
  IMPLEMENTATION — name→row resolution already has exactly one home.
- **Reading B: resolve through the message ledger's view of the `agent` table.** Nothing in
  any ruling suggests it — **but it is the ONLY reading the contract's harness is consistent
  with** (§3.1b), and it is the only one under which C-DEF 5 disappears.

I built A and say so. Reading B would require a SECOND implementation of agent-name
resolution living on `MessageLedger`, which is the `#102` shape and, per repo law, a design
decision to escalate rather than write. **That is decision-needed #2.**

---

# §3 · THE FIVE C-DEFs — every pin RED against a correct build

Measured 2026-08-01 in `/home/ejprice/scratch-c3-ref` against the repo's `f67a219` contract
file. Baseline before the build: `34 failed, 8 passed`. After the build: `12 failed, 30
passed`. **All twelve are contract defects, not build defects** — proven by construction in
§3.6, where repairing three of them takes the file to `41 passed, 1 failed`.

## 3.1 · C-DEF 1 — `_footer_harness` never registers anyone in `FakeAgentRegistry` (7 pins)

`_footer_harness` builds `FakeAgentRegistry(db=FakeAgentDatabase())` and never puts an agent
in it. The only "registration" is `message_ledger.db.agents[f"agent:{name}"] = name` — the
MESSAGE ledger's id→name map, which is its stand-in for the `agent` table's *existence*
check, not a registry. So **no identity can ever resolve**, and every leg asserting a footer
IS served is RED on a correct build:

| pin | served |
|---|---|
| `TestAHostileIdentity…::test_POSITIVE_CONTROL_a_benign_registered_identity_DOES_reach_the_footer` | `'created task … (status open)'` |
| `TestNoTrafficMeansNoFooter::test_POSITIVE_CONTROL_the_same_write_WITH_traffic_DOES_footer` | `…\n(no pending-traffic line: agent=builder-04b2-wavec-3 is not registered …)` |
| `TestTheFallback…::test_the_FALLBACK_footer_carries_no_second_person_imperative` | no footer at all |
| `TestTheFallback…::test_POSITIVE_CONTROL_the_RESOLVED_caller_footer_MAY_be_directive` | both paths `None` |
| `TestABatchThatWroteNOTHING…::…[1-True]`, `[4-True]`, `[5-True]` | no footer |

⚠ **AND THE SECOND HALF, WHICH REGISTERING ALONE DOES NOT FIX.** The contract seeds the
inbox under `f"agent:{name}"`, while `FakeAgentRegistry._agent_id(session, name)` mints
`uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex`. A build that resolves an
identity and then counts `pending_traffic(agent_id=row.id)` would count an **EMPTY** inbox —
green-looking resolution, zero traffic, no footer, same reds. **The two fakes must agree on
the agent id**, and the registry's is the real one (in production the `to` edge points at the
`agent` row). The repair is in §6's `_registered_row`.

Three pins in the same area currently pass **VACUOUSLY** for the same root cause and will
change meaning once C-DEF 1 lands — the author should re-read them then:
`test_a_hostile_identity_can_NEVER_REACH_the_footer`,
`test_the_fallback_matches_EXACTLY_never_heuristically`,
`test_the_FALLBACK_footer_names_no_drain_CALL` (this last one reads
`_footer_line(served) or ""`, so "no footer" satisfies it).

### 3.1b · What the harness's id convention IMPLIES about the intended design

`f"agent:{name}"` is not any id this system mints. It is, however, **exactly** what a reverse
lookup over `FakeMessageLedger.db.agents` returns — and the harness seeds BOTH the `agent=`
identity and the R8(2) `owner` identity into that map and nowhere else. Read as a whole, the
harness is a complete, self-consistent fixture for a build that resolves names through the
MESSAGE LEDGER, and an impossible fixture for one that resolves through the registry. That
is why §2.2 is an escalation rather than a preference: **the harness, not the ruling, is
currently deciding the architecture.**

## 3.2 · C-DEF 2 — `_findings_call` drives `get`/`chain_head` with NO `id_or_number` (2 pins)

```
E   ValueError: the 'id_or_number' argument is required and must be a non-empty finding
    number or id for this findings action
    (loremaster/loremaster/server.py, _require_finding_ref)
```

`_findings_call` only sets `id_or_number`-bearing kwargs for `batch_writes` and `report`;
`get` and `chain_head` get `{"action": …, "agent": …, "session": …}` and nothing else. That
refusal is PRE-EXISTING, load-bearing behaviour (`_require_finding_ref`'s docstring:
*"never a lookup on an empty id"*), so **no build can make these two pins pass.**

Pins: `TestTheFooterRidesTheOUTCOMENotTheVERB::test_a_findings_READ_action_NEVER_footers[get]`
and `[chain_head]`. `[query]` is fine.

**Repair:** seed a finding in the harness's `finding_ledger` and pass its id (§6).

## 3.3 · C-DEF 3 — `_claim_call` calls a method that does not exist (2 pins)

```
E   AttributeError: 'FakeTaskLedger' object has no attribute 'create'
    (test_comms_footer.py, _claim_call)
```

The method is `create_task(subject, description, *, blocked_by=None, created_by)` — and it
returns the **id string**, not a `Task`, so the very next line (`task.id`) is a second,
latent error behind the first. Pins:
`test_the_LOSING_claim_branch_writes_NOTHING_and_so_NEVER_footers` and
`test_POSITIVE_CONTROL_the_WINNING_claim_DOES_footer` — i.e. **the entire
outcome-vs-verb distinction**, the class the contract itself calls *"the leg that
distinguishes outcome-keyed from verb-keyed"*, never executes.

## 3.4 · C-DEF 4 — `test_comms_footer.py` cannot meet the repo's mypy gate, ever (2 errors)

`scripts/typecheck.sh` in the scratch tree, WITH the reference build landed:

```
loremaster/tests/test_comms_footer.py:1352: error: Module "test_comms_tool" does not
    explicitly export attribute "FakeAgentDatabase"  [attr-defined]
loremaster/tests/test_comms_footer.py:1352: error: Module "test_comms_tool" does not
    explicitly export attribute "FakeAgentRegistry"  [attr-defined]
```

**These are NOT the five §4.5.3b named**, and they are not of that class. §4.5.3b's five
(`COMMS_FOOTER_PREFIX`, `PendingTraffic`, `_comms_footer` ×2,
`FakeMessageLedger.pending_traffic`) all resolved the moment the build landed, exactly as
predicted. These two are re-export errors: `test_comms_tool` imports both names from
`_comms_fakes` without re-exporting them, and mypy's `--no-implicit-reexport` refuses the
hop. **No build can clear them** — the fix is one line in the contract:
`from _comms_fakes import FakeAgentDatabase, FakeAgentRegistry` (the module that actually
defines them, which the contract already imports from for `FakeMessageLedger`).

Every other file in that mypy run is a packet-39/auth file (finding #306, RED at HEAD,
operator-held). **The reference build's own files — `server.py`, `messages.py`,
`_message_fakes.py`, `test_comms_tool.py` — contribute ZERO errors** (§5).

## 3.5 · C-DEF 5 — the ONE irreducible red: a pin that contradicts R8's own cost line

```
E   AssertionError: an omitted agent= still cost 1 registry read(s). There is no identity
    to resolve, so there is nothing to look up
    assert 1 == 0
```

`TestAnOmittedIdentity…::test_an_OMITTED_agent_serves_no_footer_and_reads_NO_registry` asserts
`registry_reads == 0` for a call with `agent=None` and `created_by="contract-04b2-wavec-1"`.
But R8(2)'s fallback matches `owner`/`actor`/`created_by` **exactly against a registered
agent name** — and there is no way to know whether a free-text value names a registered agent
without reading the registry. **The pin and the ruling are jointly unsatisfiable.**

⚠ **And the ruling says so itself.** `docs/plans/v2/04-comms-blocks-footer.md` §RULINGS ROUND
3, R8, verbatim:

> Cost: **one charset-gated registry read per identity-less write** · ~7 pins · ~a day of 04b-2.

The operator PRICED this pin's forbidden read as R8's accepted cost. The pin is the half that
is wrong.

**PROVEN BY CONSTRUCTION, both directions** (same build, same repaired harness, one branch
toggled):

| build | `…reads_NO_registry` | R8(2)'s three fallback legs | total |
|---|---|---|---|
| fallback PRESENT | **RED** (1 read) | GREEN | `1 failed, 41 passed` |
| fallback DELETED | GREEN | **RED** ×3 | `3 failed, 39 passed` |

No build satisfies both. The three "dodges" are all worse: resolving via a registry method
other than `get_agent` games a counter rather than answering the question; resolving via the
message ledger is Reading B (a second copy of name resolution, §2.2); deleting the fallback
deletes R8(2).

**Recommendation (I did not choose):** keep the *silence* half of the pin — an omitted
`agent=` must not serve a footer, and that leg is right and passes — and replace the
`registry_reads == 0` leg with what R1 actually protects: **at most ONE registry read per
call, and ZERO when no attribution value is supplied either.** That is R8's priced cost stated
as a pin, and it still kills the build R1 rejects (a per-attribution scan, or a heuristic
sweep). Operator/lead ruling required.

## 3.6 · The construction that proves these are CONTRACT defects, not build defects

`test_comms_footer.py` was **never edited** (byte-identical to `f67a219`'s). The three harness
C-DEFs were repaired OUT-OF-TREE by a pytest plugin (§6) that monkeypatches
`_footer_harness` / `_findings_call` / `_claim_call`:

```
# pytest loremaster/tests/test_comms_footer.py -p c3_harness_repair
..................F.......................                               [100%]
FAILED …::TestAnOmittedIdentityIsHonestSILENCEAndASuppliedOneIsNOT::
         test_an_OMITTED_agent_serves_no_footer_and_reads_NO_registry[asyncio]
1 failed, 41 passed in 1.77s
```

**41 of 42 green on the unmodified contract**, with the survivor being the ruling conflict.
That is as close to a satisfiability receipt as this contract can currently get — and it is
not one, because a receipt is `0 failed` on the contract AS COMMITTED.

---

# §4 · CROSS-FILE CO-EDITS THE BUILD SPEC DOES NOT NAME (#133's leg earning its keep)

Both were found by running the PRE-EXISTING suites the seam touches. A builder who ran only
C3 would have shipped both as regressions, green at its own gate.

## 4.1 · `test_comms_tool.py` — 7 charset pins assert the retired prose

`TestCommsDispatchCharsetValidation` (7 parametrised pins) asserts `'safe charset' in
message` against `_validate_comms_charset`'s served `ValueError`. #219's repair rewrites that
message. **This is the repo's own law firing — *"tests written before a semantic change
certify the OLD world"*.**

It is navigable rather than blocking: I re-worded the repair to KEEP the phrase *"must stay
in the safe charset"* while dropping the false *"inlined into store queries"* clause, and all
7 went green with **no test edit**. But the builder must know the constraint exists, because
the obvious rewrite trips it. **A one-line note in C3's `FALSE_RATIONALE_MARKERS` docstring
would save a fix wave.**

## 4.2 · `test_blocks_edge.py::_tool_seam` — its own stated bound, firing exactly as written

```
E   AttributeError: 'AppContext' object has no attribute 'agent_registry'
```

`_tool_seam` builds `AppContext.__new__(AppContext)` with ONLY `task_ledger`, and its
docstring says: *"⚠ Stated bound: an attribute the dispatcher gains LATER and reads on these
paths surfaces here as `AttributeError`, which is a LOUD failure naming the attribute."* R8(2)'s
fallback makes `agent_registry` a dependency of `lore_tasks` on **every identity-less write**,
and these pins pass `created_by`. 2 pins RED.

**Repair (applied in scratch, 2 lines + a comment):** wire `agent_registry` and
`message_ledger` to EMPTY fakes — nothing registered, so the fallback resolves nothing, no
footer is served, and the pins stay about the cycle refusal. ⚠ **The alternative — guarding
the footer path against a missing service — is the wrong fix**: a silently-skipped footer on
a mis-wired context is exactly the confident-silence the trust doctrine forbids. After the
repair: `test_blocks_edge.py` + `test_comms_tool.py` → **1084 passed**.

## 4.3 · CL3 / CL1 — the `_INSTRUCTIONS` paragraph is landable, with ONE non-obvious constraint

CL3's documented outcome #2 applies and I took it (declare the paragraph in
`_DECLARED_NON_COMMS_PARAGRAPHS`). ⚠ **The constraint nobody has stated: CL1 lets exactly ONE
paragraph — the ruled comms block — use the duty vocabulary (`inbox`/`ack`/`drain`/`seq`/
`thread`/`directive`/`unread`, whole-word, case-insensitive). The footer's paragraph sits
OUTSIDE that block, so it must teach the footer while using NONE of those seven words** — and
"unread" and "directive" are the two words the footer's own text is about. It IS writable
(mine is, and CL1/CL3 are green), but a builder who writes the natural sentence will redden
CL1 and be tempted to grow `_COMMS_DUTY_VOCABULARY`, which R1 and SECTION E both forbid. This
belongs in the builder's brief.

---

# §5 · GATE TAILS — scoped, because HEAD is RED

⚠ **No unqualified "gates green" claim is made.** `scripts/typecheck.sh` is RED at HEAD
(finding #306, packet 39, operator-held behind #296). Every claim below is scoped to a named
file set.

**mypy — the reference build's own modules, clean:**
```
$ uv run mypy loremaster/loremaster/server.py loremaster/loremaster/messages.py
Success: no issues found in 2 source files
```

**`scripts/typecheck.sh`, loremaster leg, per-file breakdown** (scratch, build landed):
every error file is a packet-39/auth file EXCEPT `test_comms_footer.py`'s 2 (C-DEF 4).
`server.py`, `messages.py`, `_message_fakes.py`, `test_comms_tool.py`, `test_blocks_edge.py`
contribute **ZERO**.

**ruff — the whole workspace, clean:**
```
$ uv run ruff check loremaster lorerunes loresigil lorescribe c3_harness_repair.py
All checks passed!
```

**pytest, C3 alone, contract as it stands** (the honest colour of the build):
```
12 failed, 30 passed in 1.80s      # baseline before the build: 34 failed, 8 passed
```

**pytest, C3 alone, with the harness repairs applied out-of-tree:**
```
1 failed, 41 passed in 1.77s
```

**pytest, the 11 pre-existing suites this seam touches (#133's leg)** — §5.1.

**Post-ruff-cleanup leg (the harder one the brief names):** `ruff check --fix` demanded one
import-block reorganisation on `server.py` (the new `AgentRegistryError` import); it was
applied and every pytest number in this report was measured AFTER it. No orphaned imports
appeared — the build adds symbols, it deletes none. So the contract is no *less* satisfiable
after the lint's demands than before: the 12→1 result in §5.1 IS the post-cleanup result.

## 5.1 · #133's leg — the pre-existing suites the seam touches

Eleven files: `test_comms_footer` · `test_comms_tool` · `test_mcp_server` ·
`test_message_ledger` · `test_task_ledger` · `test_findings` · `test_query_tasks_bounded` ·
`test_blocks_edge` · `test_render_seam_pins` · `test_render` ·
`test_comms_render_architecture`. Both runs `-n auto`, scratch tree, build landed, §4
co-edits applied.

**RUN A — the contract EXACTLY as committed at `f67a219` (no plugin):**
```
FAILED …test_comms_footer.py::TestTheFallbackIsThirdPerson…::test_the_FALLBACK_footer_carries_no_second_person_imperative
FAILED …test_comms_footer.py::TestTheFooterRidesTheOUTCOMENotTheVERB::test_the_LOSING_claim_branch_writes_NOTHING_and_so_NEVER_footers
FAILED …test_comms_footer.py::TestTheFooterRidesTheOUTCOMENotTheVERB::test_POSITIVE_CONTROL_the_WINNING_claim_DOES_footer
FAILED …test_comms_footer.py::TestTheFallbackIsThirdPerson…::test_POSITIVE_CONTROL_the_RESOLVED_caller_footer_MAY_be_directive
FAILED …test_comms_footer.py::TestAHostileIdentity…::test_POSITIVE_CONTROL_a_benign_registered_identity_DOES_reach_the_footer
FAILED …test_comms_footer.py::TestABatchThatWroteNOTHING…::test_the_footer_follows_the_WRITE_COUNT_not_the_CALL[asyncio-1-True]
FAILED …test_comms_footer.py::TestABatchThatWroteNOTHING…::test_the_footer_follows_the_WRITE_COUNT_not_the_CALL[asyncio-4-True]
FAILED …test_comms_footer.py::TestTheFooterRidesTheOUTCOMENotTheVERB::test_a_findings_READ_action_NEVER_footers[asyncio-get]
FAILED …test_comms_footer.py::TestABatchThatWroteNOTHING…::test_the_footer_follows_the_WRITE_COUNT_not_the_CALL[asyncio-5-True]
FAILED …test_comms_footer.py::TestTheFooterRidesTheOUTCOMENotTheVERB::test_a_findings_READ_action_NEVER_footers[asyncio-chain_head]
FAILED …test_comms_footer.py::TestNoTrafficMeansNoFooter::test_POSITIVE_CONTROL_the_same_write_WITH_traffic_DOES_footer
FAILED …test_comms_footer.py::TestAnOmittedIdentity…::test_an_OMITTED_agent_serves_no_footer_and_reads_NO_registry
12 failed, 2589 passed, 14 skipped, 3 xfailed in 358.32s (0:05:58)
```
**All twelve failures are inside `test_comms_footer.py`. Every pre-existing suite is GREEN
with the reference build landed** — which is #133's leg discharged: the seam does not
regress anything it touches. (It DID regress two of them before the §4 co-edits — 21 failed —
which is exactly why the leg is mandatory.)

**RUN B — same suites, harness repairs applied out-of-tree:**
```
FAILED …test_comms_footer.py::TestAnOmittedIdentityIsHonestSILENCEAndASuppliedOneIsNOT::
       test_an_OMITTED_agent_serves_no_footer_and_reads_NO_registry[asyncio]
1 failed, 2600 passed, 14 skipped, 3 xfailed in 189.50s (0:03:09)
```

**2600 passed / 1 failed across the whole seam, on an unmodified contract file, with the
survivor being C-DEF 5's ruling conflict.** That is the strongest statement available: the
reference build is correct, and everything standing between C3 and a real `0 failed` receipt
is in the contract.

---

# §6 · THE INSTRUMENT (brief-base §1 — an instrument behind a load-bearing claim is a deliverable)

`c3_harness_repair.py`, a pytest plugin, lives at `/home/ejprice/scratch-c3-ref/` — a scratch
path, therefore unrecoverable by construction, therefore **pasted verbatim below.** It is the
whole evidence for *"the reference build is correct and the contract is what is defective"*.

⚠ It is a DIAGNOSTIC, not a receipt. Each monkeypatch corresponds 1:1 to a C-DEF the contract
author must land IN the contract.

## 6.1 · `c3_harness_repair.py`, verbatim

```python
"""DIAGNOSTIC pytest plugin — the MINIMAL repairs C3's harness needs so a correct
build can be graded, applied WITHOUT editing ``test_comms_footer.py``.

Authored 2026-08-01 by ``refbuild-c3-1`` while producing C3's satisfiability
receipt. ⚠ **A run under this plugin is NOT a satisfiability receipt for the
contract as it stands** — it is the CONSTRUCTION that distinguishes "the
contract is defective" from "the reference build is wrong", by showing which
pins go green the moment the harness stops contradicting itself. Every repair
below is a C-DEF the contract author must land IN the contract.

Use: ``pytest loremaster/tests/test_comms_footer.py -p c3_harness_repair``
(run from the repo root, which is on ``sys.path`` for ``-p`` resolution).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest


def _registered_row(name: str, session: str) -> tuple[str, Any]:
    """A registry row whose ``id`` is the id the registry itself would mint.

    ⚠ **C-DEF 1, half two.** Registering the caller is not enough: the contract
    seeds the inbox under ``f"agent:{name}"``, while ``FakeAgentRegistry``
    mints ``uuid5(...)``. A build that resolves an identity and then counts
    ``pending_traffic(agent_id=row.id)`` therefore counts an EMPTY inbox. The
    two fakes must agree on the id, and the registry's is the real one (in
    production the ``to`` edge points at the ``agent`` row).
    """
    from loremaster.agents import STATUS_ACTIVE, Agent
    from test_comms_tool import FakeAgentRegistry

    agent_id = FakeAgentRegistry._agent_id(session, name)
    now = datetime.now(UTC)
    return agent_id, Agent(
        id=agent_id,
        name=name,
        session=session,
        role="builder",
        status=STATUS_ACTIVE,
        registered_at=now,
        heartbeat_at=now,
    )


@pytest.fixture(autouse=True)
def _repair_c3_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    import test_comms_footer as c3
    from _finding_fakes import FakeFindingDatabase, FakeFindingLedger
    from _message_fakes import FakeMessageDatabase, FakeMessageLedger
    from _task_fakes import FakeTaskDatabase, FakeTaskLedger
    from test_comms_tool import FakeAgentDatabase, FakeAgentRegistry

    # ---- C-DEF 1: the harness never registers anybody in the registry -------
    def _footer_harness(
        *,
        unread: int,
        unacked: int,
        registered: tuple[str, str] | None = c3.CALLER_A,
        owner_identity: str | None = None,
        count_registry_reads: bool = False,
    ) -> Any:
        message_ledger = FakeMessageLedger(db=FakeMessageDatabase())
        registry = FakeAgentRegistry(db=FakeAgentDatabase())
        reads = {"count": 0}

        def _enrol(name: str, session: str) -> None:
            agent_id, row = _registered_row(name, session)
            registry.db.agents[agent_id] = row
            message_ledger.db.agents[agent_id] = name
            c3._seed_inbox(message_ledger, agent_id, unread=unread, unacked=unacked)

        if registered is not None:
            _enrol(*registered)
        if owner_identity is not None:
            # R8(2)'s fallback matches a REGISTERED agent name, so the owner
            # value must name a registry row too — not only a message-ledger key.
            _enrol(owner_identity, c3.CALLER_A[1])

        if count_registry_reads:
            inner = registry.get_agent

            async def _counting(*args: Any, **kwargs: Any) -> Any:
                reads["count"] += 1
                return await inner(*args, **kwargs)

            registry.get_agent = _counting  # type: ignore[method-assign]

        return SimpleNamespace(
            agent_registry=registry,
            message_ledger=message_ledger,
            task_ledger=FakeTaskLedger(db=FakeTaskDatabase()),
            finding_ledger=FakeFindingLedger(db=FakeFindingDatabase()),
            config=SimpleNamespace(
                comms=SimpleNamespace(
                    stale_heartbeat_s=600,
                    fleet_limit=20,
                    drain_limit=20,
                    brief_body_warn_chars=4000,
                )
            ),
            registry_reads=reads,
        )

    # ---- C-DEF 2: get/chain_head are driven with NO id_or_number ------------
    async def _findings_call(
        *,
        action: str,
        agent: tuple[str, str] | None,
        pending: bool,
        batch_writes: int | None = None,
    ) -> str:
        from loremaster.server import AppContext

        harness = _footer_harness(
            unread=c3.UNREAD_COUNT if pending else 0,
            unacked=c3.UNACKED_DIRECTIVE_COUNT if pending else 0,
        )
        kwargs: dict[str, Any] = {"action": action}
        if agent is not None:
            kwargs["agent"], kwargs["session"] = agent
        if batch_writes is not None:
            kwargs["items"] = await c3._batch_items(harness, writes=batch_writes)
            kwargs["actor"] = "contract-04b2-wavec-1"
        elif action in ("get", "chain_head"):
            # A read needs something to read: every correct build REFUSES a
            # missing 'id_or_number' (server._require_finding_ref), so the
            # contract's own call raises before any footer decision happens.
            seeded = await harness.finding_ledger.report(
                subject="a real subject",
                body="",
                area="test_comms_footer",
                category="contract_gap",
                created_by="contract-04b2-wavec-1",
            )
            kwargs["id_or_number"] = seeded.id
        elif action == "report":
            kwargs.update(
                subject="a real subject",
                area="test_comms_footer",
                category="contract_gap",
                created_by="contract-04b2-wavec-1",
            )
        return str(await AppContext.findings(harness, **kwargs))

    # ---- C-DEF 3: FakeTaskLedger.create does not exist ----------------------
    async def _claim_call(
        *, agent: tuple[str, str] | None, pending: bool, wins: bool
    ) -> str:
        from loremaster.server import AppContext

        harness = _footer_harness(
            unread=c3.UNREAD_COUNT if pending else 0,
            unacked=c3.UNACKED_DIRECTIVE_COUNT if pending else 0,
        )
        # ``create_task``, not ``create`` — and it returns the ID, not a Task.
        task_id = await harness.task_ledger.create_task(
            "a real subject",
            "a real description",
            created_by="contract-04b2-wavec-1",
        )
        if not wins:
            await harness.task_ledger.claim_task(task_id, "someone-else")
        kwargs: dict[str, Any] = {"task_id": task_id, "owner": "contract-04b2-wavec-1"}
        if agent is not None:
            kwargs["agent"], kwargs["session"] = agent
        return str(await AppContext.claim_task(harness, **kwargs))

    monkeypatch.setattr(c3, "_footer_harness", _footer_harness)
    monkeypatch.setattr(c3, "_findings_call", _findings_call)
    monkeypatch.setattr(c3, "_claim_call", _claim_call)
```

---

---

# §8 · PHASE 2 — THE REPAIR WAVE AND THE RECEIPT

Authorised by `lead-04b2-wavec` after Phase 1: writable set widened to include
`loremaster/tests/test_comms_footer.py`; **GO** on C-DEFs 1–4; **HOLD** on C-DEF 5, which is
with the design sidecar because its answer may change the footer's shape.

## 8.0 · Provenance, re-printed for this phase (brief-base §6)

```
loremaster.__file__ = /home/ejprice/scratch-c3-ref/loremaster/loremaster/__init__.py
```

The repaired contract was authored in the REPO (`loremaster/tests/test_comms_footer.py`) and
copied to the scratch tree; `diff -q` confirmed byte-identity before every run below. So the
file measured is the file the lead will commit — not a scratch variant of it.

## 8.1 · What landed in `test_comms_footer.py` (the only repo file I wrote besides this report)

| C-DEF | repair |
|---|---|
| **1** | New module helper `_registered_agent(name, session)` mints an `Agent` keyed by `FakeAgentRegistry._agent_id(session, name)` — the id the registry ITSELF would mint. `_footer_harness` gains an `_enrol()` closure that registers the row AND seeds that agent's inbox **under the same id**, replacing the old `f"agent:{name}"` key. Both halves, because registering alone would still have counted an empty inbox. |
| **2** | `_findings_call` files a real finding through `harness.finding_ledger.report(...)` and passes its id for the actions in the new `_FINDING_ACTIONS_NEEDING_A_REF = ("get", "chain_head")` constant — named rather than inlined so the harness's list cannot drift from the dispatcher's requirement, which is what hid the defect. |
| **3** | `_claim_call` now calls `create_task("a real subject", "a real description", created_by=…)` — positional — and threads the returned **id string** through, instead of `create(subject=…)` + `task.id`. |
| **4** | `from _comms_fakes import FakeAgentDatabase, FakeAgentRegistry` — the module that DEFINES them — replacing the `test_comms_tool` hop that mypy refuses under `--no-implicit-reexport`. |

Each repair carries a ⚠ block in the file naming the C-DEF, what was wrong, and **what it
cost** — because the contract is a durable artifact and *"the harness registered nobody"* is
worth more to the next reader than a silently-correct fixture. C-DEF 3's note records the
part that matters most: the loss was not two pins but *the entire outcome-vs-verb
distinction*, which had never once executed.

**Three pins that previously passed VACUOUSLY now discriminate**, which is the repair's
second payoff and was flagged in §3.1: `test_a_hostile_identity_can_NEVER_REACH_the_footer`,
`test_the_fallback_matches_EXACTLY_never_heuristically` and
`test_the_FALLBACK_footer_names_no_drain_CALL` were all satisfied by *"no footer ever"*
before. With identities now resolvable they are answering their own questions.

## 8.2 · The one co-edit I did NOT land in the repo — exact diff, so it cannot be lost

The lead's grant named ONE repo file. `test_blocks_edge.py::_tool_seam` belongs to the
BUILD, not the contract, and the build is not in the repo — so I applied it in scratch only
and reproduce it here. **The real builder must land this with the footer**, or 2 pins go RED
with `AttributeError: 'AppContext' object has no attribute 'agent_registry'` — exactly the
bound `_tool_seam`'s own docstring predicted.

```python
    from _comms_fakes import FakeAgentDatabase, FakeAgentRegistry
    from _message_fakes import FakeMessageDatabase, FakeMessageLedger
    from loremaster.server import AppContext

    context = AppContext.__new__(AppContext)
    context.task_ledger = ledger
    # ⚠ THE STATED BOUND ABOVE, FIRING EXACTLY AS PREDICTED (packet 04b-2 slice
    # C3): the dispatcher gained the pending-traffic footer, and R8(2)'s
    # exact-match fallback reads the registry on EVERY identity-less write — so
    # this seam now touches two more services. Wired to EMPTY fakes on purpose:
    # nothing here is registered, so the fallback resolves nothing and no footer
    # is served, which keeps these pins about the CYCLE refusal and nothing else.
    # ``type: ignore`` for the same reason the rest of this tree drives handlers
    # with doubles: the fakes match the PUBLIC surface exactly but are not
    # nominal subclasses, and ``AppContext`` annotates the real classes.
    context.agent_registry = FakeAgentRegistry(db=FakeAgentDatabase())  # type: ignore[assignment]
    context.message_ledger = FakeMessageLedger(db=FakeMessageDatabase())  # type: ignore[assignment]
    return context
```

⚠ **The `type: ignore` comments are not cosmetic and I only found them by re-running the
canonical typecheck**: without them this co-edit introduces 2 NEW mypy errors
(`Incompatible types in assignment`), which would have swapped C-DEF 4's two errors for two
of my own and left the total unchanged at 104 — a fix that looks like a fix. §8.4.

The second §4 item — the `test_comms_tool` charset pins — needed **no test edit at all**.
It is a constraint on the BUILD: #219's repaired `ValueError` must keep the phrase
*"safe charset"*, which 7 pre-existing pins assert. My build does, and they are green. That
constraint belongs in the builder's brief.

## 8.3 · ⛔ THE RECEIPT

Scratch tree, reference build landed, **repaired contract, NO diagnostic plugin**, `-n auto`.

**C3 alone:**
```
1 failed, 41 passed in 1.96s
FAILED loremaster/tests/test_comms_footer.py::TestAnOmittedIdentityIsHonestSILENCEAndAS
       uppliedOneIsNOT::test_an_OMITTED_agent_serves_no_footer_and_reads_NO_registry[asyncio]
```

**The 11 suites this seam touches (#133's leg)** — `test_comms_footer` · `test_comms_tool` ·
`test_mcp_server` · `test_message_ledger` · `test_task_ledger` · `test_findings` ·
`test_query_tasks_bounded` · `test_blocks_edge` · `test_render_seam_pins` · `test_render` ·
`test_comms_render_architecture`:
```
E   AssertionError: an omitted agent= still cost 1 registry read(s). There is no identity
    to resolve, so there is nothing to look up
E   assert 1 == 0
FAILED loremaster/tests/test_comms_footer.py::TestAnOmittedIdentityIsHonestSILENCEAndAS
       uppliedOneIsNOT::test_an_OMITTED_agent_serves_no_footer_and_reads_NO_registry[asyncio]
1 failed, 2600 passed, 14 skipped, 3 xfailed in 286.57s (0:04:46)
```

**Stated plainly, as the lead asked: C-DEF 5 is the ONLY remaining RED.** It is the pin ruled
untouchable, it is failing for exactly the reason Phase 1 derived (`assert 1 == 0`, the
registry read R8's own cost line prices), and every other pin in C3 and every pre-existing
pin in the seam is green. **Handing it back.**

⚠ **This is a receipt with an asterisk and the asterisk is the point:** it is not `0 failed`,
so C3 is still not formally satisfiable. What it establishes is narrower and, I think, more
useful — *the ONLY thing standing between C3 and a real 0-failed receipt is one ruling.*

## 8.4 · Gate scope — stated, because HEAD is RED

**No wave-level "gates green" claim.** `scripts/typecheck.sh` is RED at HEAD (finding #306,
packet 39, operator-held behind #296).

Scoped claim, DERIVED rather than asserted — the distinct files carrying mypy errors in a
full canonical `typecheck.sh` run over the scratch tree with everything landed are:

```
loremaster/tests/{_auth_fixtures, test_allowlist_roster, test_auth_composition,
                  test_auth_identity_seam, test_auth, test_google_token_verifier,
                  test_hosted_readonly_posture, test_permission_resolver_seam}.py
lorerunes/tests/{test_email_normalisation, test_posture, test_roster_parser}.py
```

**Eleven files, every one of them a packet-39/auth file. NONE of the C3 file set appears** —
`test_comms_footer.py`, `test_comms_tool.py`, `test_blocks_edge.py`, `_message_fakes.py`,
`loremaster/server.py` and `loremaster/messages.py` contribute **zero** mypy errors. Direct
confirmation on that set alone:

```
$ uv run mypy loremaster/tests/test_blocks_edge.py loremaster/tests/test_comms_footer.py \
              loremaster/tests/test_comms_tool.py loremaster/tests/_message_fakes.py \
              loremaster/loremaster/server.py loremaster/loremaster/messages.py
Success: no issues found in 6 source files
```

ruff, whole workspace:
```
$ uv run ruff check loremaster lorerunes loresigil lorescribe
All checks passed!
```

## 8.5 · The diagnostic plugin is now REDUNDANT

`c3_harness_repair.py` (§6.1) did its job: it proved, before I was allowed to touch the
contract, that the reference build was correct and the contract was not. Every repair it
monkeypatched now lives IN the contract, and **no run in §8.3 uses it.** It stays pasted in
§6.1 as the record of how the diagnosis was established — an instrument behind a
load-bearing claim, per brief-base §1 — not as a live dependency.

---

---

# §9 · PHASE 3 — RULING 5 APPLIED, AND **THE RECEIPT** (0 failed)

Design-sidecar **Ruling 5** (`REPORT-design-sidecar-04b2-wavec-1.md` §5) unblocked C-DEF 5
and corrected #305. Applying it produced a real satisfiability receipt — **and two more
defects that only a mutation could see.**

## 9.1 · What Ruling 5 changed

**Q2 / C-DEF 5 — the contract yielded (§5.2).** `registry_reads == 0` is replaced by the
BUDGET pin: three parametrised worlds, each forced by its own `created_by` fixture
(charset-FAIL ⇒ 0 reads · charset-pass+UNREGISTERED ⇒ 1 read, no footer · charset-pass+
REGISTERED ⇒ 1 read, third-person footer), plus the ceiling **≤ 1 read on every path**
(`_MAX_REGISTRY_READS_PER_CALL`, a named constant so the message quotes the number the
assertion checks). The silence half is kept and correctly scoped — silence when nothing
RESOLVES, not unconditionally, because a registered `created_by` legitimately footers.

⚠ **The ruling implied a BUILD change nobody had written down:** *charset-gated* is a
behaviour, not an adjective. The build now runs `AGENT_NAME_PATTERN.fullmatch` **in front
of** the registry read, so a free-text owner like `"the release train"` costs ZERO reads —
and it resolves **one** candidate, never a loop.

⚠ **Ruling 5.2's world (i) — *"no attribution value supplied at all ⇒ 0 reads"* — is
UNREACHABLE at these dispatchers, and I did not quietly drop it.** Every write action
requires an attribution argument (`tasks` create/create_many/supersede need `created_by`,
transition needs `actor`, `claim_task` needs `owner`, `findings` report needs `created_by`,
the batch verbs need `actor`), so a write with all attribution slots empty cannot be
constructed. Derived by reading the dispatchers. The pin stands in for it with the
constructible zero-read floor (a READ short-circuits on OUTCOME before resolution) and
**says so in its own docstring** rather than implying it tested the ruled world.

**Q1 / #305 — the corrected threat model is now IN the contract (§5.1).** The docstring
claiming raw-echo-after-exact-match *"re-opens the vector completely"* is replaced: after a
true exact match that string is byte-equal to a charset-clean registered name, so it is not
a vector. The pin stays as **belt** — it keeps the safety argument local — and the real
chain is documented link by link, in `_resolve_footer_identity`'s docstring and on link 2's
pin.

**Q3 — the registry is the one resolution seam.** Already what the build did; the harness
repair removed the fixture's vote for Reading B.

## 9.2 · ⚠ TWO DEFECTS THE MUTATIONS FOUND — both invisible to a green suite

Ruling 5.1 said link 2 *"must be made REAL, not assumed."* I tried to assume it, then
mutated instead. Both times the mutation disagreed with me.

**(a) Link 2 was STILL vacuous after the C-DEF 1 repair — my own fix had shadowed it.**
Making the resolver case-fold AND strip left **all 46 pins GREEN**. Cause: the exactness
fixture was `"  LEAD-04B2-WAVEC  "`, and Ruling 5.2's new charset gate refuses that value
*before the resolver is reached*. The pin never reached the code it was named for. **Two
rulings, each right, combining to silently disarm a pin** — and nothing in either says so.

*Repair:* the exactness leg now uses `_CHARSET_LEGAL_NEAR_MISS` — a **proper prefix** of a
registered name, derived from the constraint (must satisfy `AGENT_NAME_PATTERN`, must not
equal a registered name) rather than picked for looks. The old fixture is KEPT as its own
leg, renamed for what it actually measures now: **charset-gate coverage**.

**(b) The one-read CEILING was unpinned — a per-attribution SCAN passed all 47 pins.**
The build R1 explicitly rejects, and every assertion said `<= 1` while no fixture could
ever produce 2: each row supplied exactly ONE non-`None` attribution, so *"read the first
eligible candidate"* and *"read them all"* were the same execution. **This repo's
most-repeated fixture defect, in a pin written the same hour to enforce a budget.**

*Repair:* `test_a_SECOND_attribution_is_NEVER_consulted_after_the_first` forces two
charset-legal attributions where the FIRST is unregistered and the SECOND is real. A
ceiling build reads once and serves nothing; a scan build reads twice and footers — both
observables diverge.

## 9.3 · The mutation table (declared BEFORE each run, diffed both ways)

| # | mutation | expected RED | observed |
|---|---|---|---|
| M1 | resolver does a heuristic PREFIX scan | link 2 (exactness) | ✅ `fallback_matches_EXACTLY_never_heuristically` + the REGISTERED budget row |
| M2 | charset gate removed | the charset-FAIL row + the gate leg | ✅ both |
| M3 | per-attribution SCAN (ceiling removed) | the ceiling leg | ❌ **GREEN — defect (b)**; ✅ RED after the repair |
| M4 | footer built as a bare f-string | SECTION A's type pin | ✅ `test_the_footer_helper_returns_Rendered_not_a_bare_str` |

M4 is Ruling 5.1's **re-pointed** §B5 declared-RED set, verified: with the neutralisation
pin retired, the bare-f-string build is caught by the isinstance/type pin — so §B5's seam
discipline still has a live instrument rather than a retired one.

Every mutation was made in the scratch tree against a `cp` content backup and restored
byte-exact; the baseline was re-measured green after each.

## 9.4 · ⛔ THE RECEIPT

Scratch tree, reference build + repaired contract, **no plugin, no mutation in place**,
`-n auto`.

```
loremaster.__file__ = /home/ejprice/scratch-c3-ref/loremaster/loremaster/__init__.py
```

**C3 alone:**
```
48 passed in 1.96s
```

**The 11 suites this seam touches (#133's leg)** — `test_comms_footer` · `test_comms_tool` ·
`test_mcp_server` · `test_message_ledger` · `test_task_ledger` · `test_findings` ·
`test_query_tasks_bounded` · `test_blocks_edge` · `test_render_seam_pins` · `test_render` ·
`test_comms_render_architecture`:
```
2607 passed, 14 skipped, 3 xfailed in 143.91s (0:02:23)
```

**ZERO FAILURES. C3 goes 0-failed against a known-correct build, and every pre-existing
suite its seam touches stays green. THE SATISFIABILITY RECEIPT IS PRODUCED.** C3 is
builder-ready.

The contract grew 42 → **48** pins across the three phases (four harness repairs, the
budget pin's three worlds + ceiling + zero-read floor + scoped silence, and the split of
exactness from charset-gate coverage).

## 9.5 · Gate scope — stated, because HEAD is RED

**No wave-level "gates green" claim.** `scripts/typecheck.sh` is RED at HEAD (finding #306,
packet 39, operator-held behind #296) and I did not touch those files.

```
$ uv run mypy loremaster/tests/test_comms_footer.py loremaster/tests/test_comms_tool.py \
              loremaster/tests/test_blocks_edge.py loremaster/tests/_message_fakes.py \
              loremaster/loremaster/server.py loremaster/loremaster/messages.py
Success: no issues found in 6 source files

$ uv run ruff check loremaster lorerunes loresigil lorescribe
All checks passed!
```

The eleven files carrying mypy errors in a full canonical run are enumerated in §8.4; every
one is a packet-39/auth file and none is in the C3 file set.

**Repo vs scratch: `test_comms_footer.py` is byte-identical**, so this receipt grades the
file as it will be committed.

## 9.6 · What is still open

- **The §8.2 co-edit** (`test_blocks_edge.py::_tool_seam`, +2 lines +2 `type: ignore`)
  remains SCRATCH-ONLY and must land with the real build. It is in the receipt above
  because the scratch tree carries it.
- **The build itself** is still scratch-only by design — the real builder writes it. The
  scratch tree is the diff oracle; per Ruling 5.3, keep until that build lands.
- **Nothing else.** No held pin, no unresolved fork, no RED I am handing back.

---

# §7 · WHAT I DID NOT DO

- **PHASE 1:** I did not edit `loremaster/tests/test_comms_footer.py` at all — the refusal and
  every C-DEF in §3 were established against the file exactly as committed.
- **PHASE 2:** I edited it, and ONLY it, under the lead's explicit grant — C-DEFs 1–4 (§8.1).
  **I did not touch C-DEF 5's pin**, its class, or anything the ruling could move, until
  Ruling 5 arrived and settled it.
- **PHASE 3:** I re-authored C-DEF 5's pin and corrected #305's threat model — both because
  the sidecar RULED them, not on my own judgement. §9.1 cites the clause behind each change.
- I did not modify any other repo file except this report. No git write commands were run.
- I did not touch `scripts/**` or any packet-39 file.
- I did not widen my own writable set: `test_blocks_edge.py`'s required co-edit stayed in
  scratch and is reproduced as a diff in §8.2 instead (§8.2's rationale).
- I did not run the full suite — the brief scoped me to C3 plus the seams it touches.
- I did not resolve the two decisions-needed. Both are scope/ruling calls.

**Unrelated failures:** none in any of my scoped runs, in either phase. The final receipt's
single failure is C-DEF 5, held RED by ruling. The one gate that is RED beyond my work is
`scripts/typecheck.sh`, whose errors live entirely in eleven packet-39/auth files enumerated
in §8.4 — finding #306, RED at HEAD, operator-held behind #296. I did not touch them.

**⚠ THE SCRATCH TREE IS STILL ON DISK AND IT HOLDS THE ONLY COPY OF THE REFERENCE BUILD.**
`/home/ejprice/scratch-c3-ref` (NOT a git worktree — a `scratch_copy.sh`-provenance-verified
copy at `a88e7c5` + the repo's committed contract file), carrying `558 insertions(+), 32
deletions(-)` across five files plus `c3_harness_repair.py`. It is uncommitted and
unreachable from the repo. **The lead should decide: keep it for the real builder to diff
against (it is a working, gate-clean implementation of C3's whole build spec), or discard
it.** Nothing else in this report depends on it surviving — every load-bearing claim is
either a pasted tail or the §6.1 plugin.
