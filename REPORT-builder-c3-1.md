# REPORT-builder-c3-1 — C3 BUILD: **PARTIAL**, four slices landed, the dispatcher wiring is not

**brief-base v9 read**
**brief project v7 read**

> ⚠ **THIS REPORT COVERS TWO PHASES.** §0–§5 are the BLOCKED phase (2026-08-02 08:38–08:50),
> left intact because its measurements are what got the spec committed. **§6 onward is the
> BUILD phase against `0d24c12`.** Where they disagree, §6 wins and says so — in particular
> §4e/§4f.1's *"C3 cannot even collect"* is **retracted in §4f.0**.

## SUMMARY BLOCK — supersedes the blocked-phase block below

```
state: done-with-deviations (PARTIAL BUILD — the dispatcher wiring is NOT built)
⛔ WHAT LANDED, each independently verified (§6.1, §6.4, §6.5):
  · SECTION D's shared counting seam — PendingTraffic + MessageLedger.pending_traffic +
    the fake's INDEPENDENT double. LIVE-STORE verified: 5 passed / 212 deselected.
  · COMMS_FOOTER_PREFIX + AppContext._comms_footer, through the render seam. SECTION A green.
  · #219 — ALL FOUR prose sites + Ruling 10 link 4's FENCED refusal (repr() killed): 10 passed,
    including the tree-wide sweep and the derived query-TEXT invariant.
  · R-5 — MessageLedgerError added to AppContext.comms' Raises:.
⛔ WHAT IS NOT BUILT (§6.3, named honestly, NOT deferred quietly): the three dispatchers'
  resolution + trigger + teaching wiring, Ruling 10 link 1b's call sites, the _INSTRUCTIONS
  paragraph, the agent=/session= tool parameters, MP-6's ambiguity classification.
⛔ ESCALATION, BLOCKING AND NOT MINE TO FIX (§6.2): a CROSS-SLICE COLLISION. C1's `0ff05ed`
  added `blockers`+`get` to _TASK_ACTIONS BEFORE the contract's `0d24c12`, which does not
  adjudicate them. The partition pin is RED and correct; the fix is a CONTRACT edit I am
  forbidden to make. Recommendation in §6.2; I did not make it.
receipt: C3 alone 55 passed / 162 failed (scope + why in §6.4). Neighbours: test_comms_tool +
  test_message_ledger + test_render_seam_pins = 1116 passed / 14 skipped / 2 failed, and the
  2 are the lead's own known C3 orphans, corroborated by count (§6.5). ruff clean on my files.
  ⚠ NOT a gates-green claim — typecheck is RED AT HEAD from packet 39 (#306/#307), not mine.
deviation: I edited `loremaster/tests/_message_fakes.py`, which my brief never granted. The
  CONTRACT mandates it and it is not on my do-not-touch list; I asked twice and got no answer,
  so I acted and am disclosing rather than treating silence as consent (§4f.1, §6.1).
deviation: I stopped building rather than half-wire three dispatchers in a dying context —
  a structured handoff, not a can-kick. Reasoning and the exact next step in §7.
Packages considered: §6.6 — one mechanism specified (the two-count query): stdlib/house seam
  vs a store-side aggregate => bespoke-in-house, reusing MessageLedger._query/_as_rows and
  drain's own whole-set arithmetic; READ drain's implementation + store reference §2. No new
  dependency is implicated by any remaining item.
decisions-needed: 2 — §6.2 the partition collision (BLOCKING, contract edit) · §4f.1 the
  _message_fakes.py grant (acted on, needs ratification).
receipt pointers: the build §6.1 · the collision §6.2 · not-built §6.3 · the numbers + scope
  §6.4-§6.5 · packages §6.6 · the handoff §7 · blocked-phase measurements §1 · corrections §4f.0.
```

---

## BLOCKED-PHASE SUMMARY BLOCK (superseded — kept for its measurements)

```
state: blocked
⛔ THE BLOCKER, measured 2026-08-02 08:38–08:42 EDT: `contract-04b2-c3fix-1` — the C3
  contract's AUTHOR — is STILL ALIVE (pid 752783, ~12.6h elapsed) and is ACTIVELY REWRITING
  `loremaster/tests/test_comms_footer.py` IN THE REAL TREE. My brief says my spec is "All
  committed. Make them pass." It is not: at 08:38 the file was a **SyntaxError** (a literal
  `@@DELTA3_BLOCK@@` placeholder at what is line 1551 of the HEAD file), and by 08:42 it had
  become **+328/-150 vs HEAD** — a THIRD C3 fix wave, in flight, uncommitted.
⛔ TWO CONSEQUENCES, and the second is why I stopped rather than pressed on:
  (1) SPEC IDENTITY is ambiguous — HEAD's 3916-line contract vs an in-flight replacement.
  (2) I CANNOT VERIFY. pytest collects the working-tree file, which is the thing flapping.
      Any "N passed" I produced right now would grade a moving target — a FALSE CLEAR, which
      this repo's trust doctrine calls the one fatal, irreversible outcome. I will not mint one.
⛔ I ALSO DID NOT WRITE TO `server.py`, deliberately: wrong-build mutation drivers restore
  whole files from backups taken before my edits, so a restore firing after I write silently
  DESTROYS my work with no signal (#140's shape, one level up). `builder-c1-1` is live in that
  same file. Nothing of mine is at risk yet because I have written nothing — that was the point.
deviation: I have produced NO production code. This is a deliberate stop under brief-base §4
  ("if it blocks the mission, STOP and report NOW rather than at the end"), not slow progress.
Packages considered: none — no mechanism built yet; the build never started. The mechanism
  survey belongs in the build report once the spec is frozen (§4 names what I had already
  settled by READING, so the next pass does not redo it).
decisions-needed: 2 — §3 BLOCKING (which artifact is my spec, and when does the tree settle);
  §4e NON-BLOCKING (my writable set is one file short: the contract's harness calls
  `FakeMessageLedger.pending_traffic`, which does not exist, so `loremaster/tests/_message_fakes.py`
  must be writable or C3 cannot collect. Not named in my brief either way).
receipt pointers: the measurement §1 · why I did not proceed §2 · the ruling I need §3 · the
  build design I had already derived, ready to execute §4 · the symbol inventory §4e ·
  capability check §0.
```

---

# §0 · CAPABILITY CHECK (brief-base §4 — first thing in the report)

Everything my brief demanded was reachable. `lore_comms register` succeeded (session
`packet-04b2-wavec`, role `builder`; brief `project` v7 auto-acked; `drain` returned
`no unread messages`). `ToolSearch "+lore"` returned the 15-tool lore surface;
`lore_get_symbol` resolved `AppContext._validate_comms_charset` authoritatively. `git`
(read-only), `uv`, `ps` and `stat` all ran. **No capability gap.** The blocker below is a
tree-state and coordination fact, not a tooling one.

Per my brief I ran **no git write commands** and did **not** read `/home/ejprice/scratch-c3-ref`
(the reference build — withheld deliberately to keep builder ≠ grader independence intact).

**Brief step 4 discharged:** `docs/reference/surrealdb-31-capabilities.md` read before any
store-adjacent work (§2 DML IDIOMS in full — the bound-parameter / `CONTENT $content` idioms
that #219's repair asserts). Cited, not re-transcribed, per standing law.

**Tooling honesty:** the lore MCP answered every structure question I asked it
(`lore_get_symbol` for the validator). I fell back to `grep` for exactly one class of question —
**the symbol-EXISTENCE inventory in §4e** ("does `pending_traffic` exist anywhere yet?"). That is
a sanctioned fallback under the dogfood protocol's case (a) — absence-of-a-symbol across a tree is
an exhaustiveness question, and a graph index cannot prove a negative about symbols nobody has
written. Saying so out loud as the protocol requires; no friction filed, because this is the tool
working as documented rather than a gap.

---

# §1 · THE MEASUREMENT — what the tree actually did while I watched it

All times 2026-08-02, EDT, on `feat/surreal-unification`, brief-named HEAD `58f2786`.

**1a. The contract was a syntax error.** At 08:38:29 the working-tree contract was 3745
lines against HEAD's 3916, `git diff --stat` read `1 insertion, 172 deletions`, and the
deletion had been replaced by a bare marker:

```
@@DELTA3_BLOCK@@
```

sitting where HEAD has the DELTA-3 class block. `ast.parse` on it:

```
    @@DELTA3_BLOCK@@
     ^
SyntaxError: invalid syntax
```

**1b. It was still moving.** Sampling `stat -c '%Y %s'` every 5s:

```
1785674275 196620
1785674275 196620
1785674275 196620
1785674368 215537      <- +18,917 bytes mid-watch
```

**1c. It landed as a different contract, not as a restore.** At 08:42 the file parsed
again — but `git diff --stat` against HEAD read:

```
 loremaster/tests/test_comms_footer.py | 478 +++++++++++++++++++++++-----------
 1 file changed, 328 insertions(+), 150 deletions(-)
```

That is **not** a mutation-proof apply/restore cycle returning to baseline. It is a new
revision of the contract being authored in place.

**1d. Who is doing it.** The process table names the author, still running:

```
752783  45398s  --agent-name contract-04b2-c3fix-1 --agent-type tdd-contract
                --permission-mode auto --effort xhigh --model opus
```

~12.6 hours elapsed. Also live on this tree: `adversary-c3-delta-2` — consistent with a
third adversary pass having returned blockers that the author is now closing.

**1e. Uncommitted production work is stacked in the tree**, from `builder-c1-1` and
whoever else: `server.py` `+379`, `tasks.py` `+195`. Neither carries any footer symbol yet —
`grep` for `_comms_footer|pending_traffic|_validate_comms_identities` in `server.py` returns
exactly two hits, both pre-existing (`_validate_comms_identities`'s single call site inside
`AppContext.comms`, and its definition). **C3's production surface is untouched; my slice has
not been started by anyone.**

---

# §2 · WHY I STOPPED INSTEAD OF BUILDING TO HEAD

Two independent reasons. The first is a judgement call I would have escalated but could have
worked around; **the second is not.**

**2a. Spec identity (escalatable, workaroundable).** My brief says the contract is committed
and names a third change as needing a ruling: *"C3 has already survived two adversary passes
and two fix waves; a third change needs a ruling."* A third change is being written right
now. Either my brief's freeze is stale, or this wave is unruled — I cannot tell from here,
and it is not mine to decide.

**2b. I cannot verify, and a green claim would be a false clear (NOT workaroundable).**
`pytest` collects the working-tree file. That file was unparseable three minutes ago and is
being rewritten. Any passed-count I reported would describe a contract that no longer exists
by the time anyone read it. My brief requires "a green claim needs a **passed-COUNT** in the
tail" and forbids unqualified gate claims; the repo's trust doctrine is blunter — **one false
clear is fatal and irreversible within the session**, and trust is won at build time or not
at all. Producing a number here would be exactly the "verified it" claim-about-a-scope this
repo has receipts against. I will not mint one.

**2c. And writing production code now risks silent destruction.** Wrong-build drivers in this
project mutate production files and restore them from a pre-mutation copy. If I write
`_comms_footer` into `server.py` and any driver's restore fires afterward, my work is
overwritten **with no error and no signal** — the #140 lesson one level up ("nothing tells
you"), compounded by `builder-c1-1` being live in the same file and by the working tree being
the only copy of everyone's uncommitted work (the COMMIT AT NATURAL BOUNDARIES law).
Starting the build into a contested, actively-restored tree is how this wave loses two
agents' work at once, so I wrote nothing.

---

# §3 · ⛔ THE DECISION I NEED (blocking) — with both readings and my pick

**Reading A — HEAD is frozen; the in-flight wave is a later builder's problem.** I build to
`git show 58f2786:loremaster/tests/test_comms_footer.py`, and the author's third wave lands
behind me as its own delta packet.
*Cost:* I may ship a build that fails the landed contract. Its adversary found real blockers
(the last two waves each did), so this is likely, not hypothetical.

**Reading B — the third wave IS the spec; I wait for it to land and be COMMITTED, then build.**
*Cost:* wall-clock on the critical path.

**MY PICK: B, with a hard precondition** — I do not need the wave to be *perfect*, I need it
to be **frozen and committed**, because a committed spec is the only kind I can verify against
and cite. Concretely, unblock me with either:

1. **`contract-04b2-c3fix-1` lands + the lead commits** `test_comms_footer.py`, and I get one
   line naming the commit SHA; **or**
2. **the lead rules HEAD frozen** AND confirms the contract author has stopped writing to the
   tree — in which case I build to `58f2786` and the third wave becomes a follow-on.

Either way I also need: **confirmation that no mutation driver will restore `server.py` or
`tasks.py` while I hold edits there.** That is the one that can silently eat the wave.

**I recommend the lead ALSO consider committing the stacked `server.py`/`tasks.py` work now**
(+379/+195 uncommitted, two live builders): the working tree is currently the only copy, which
is the precise state this repo's law says finished work must never sit in.

---

# §4 · WHAT I HAD ALREADY DERIVED — so the next pass does not re-read the world

Read-only work completed before I stopped. All of it is spec-stable (it comes from the
RULINGS, not from the flapping fixtures) and should survive whichever reading wins.

**4a. The shared validator, verified via `lore_get_symbol` (not grepped):**
`AppContext._validate_comms_charset(value: str, label: str) -> None`, at
`loremaster/loremaster/server.py`, a `@staticmethod` on `AppContext`. It does
`AGENT_NAME_PATTERN.fullmatch(value)` and raises `ValueError`. Its sibling
`AppContext._validate_comms_identities(agent, *, session, name, to)` delegates per value and
is called at **exactly one site** — inside `AppContext.comms`. **This confirms §11.4's
central derivation independently**: the three ledger dispatchers do not charset-gate anything
today.

**4b. #219's four prose sites are both confirmed present, verbatim.** The docstring claims
the identities *"are inlined into C3's live WHERE clauses"*, and the served `ValueError`
claims *"names are inlined into store queries and must stay in the safe charset"*. Both are
the FALSE rationale #219 names — the WHEREs use bound parameters. The repair is the RATIONALE
only: the guard stays, and the literal `safe charset` must survive (7 pre-existing pins assert
it, per my brief).

**4c. The build shape I would execute, unchanged by either reading:**
- `_comms_footer` built through the **sanitised render seam** (`render_line` → `Rendered`),
  never a bare f-string (§B5/L1) — and the FALLBACK render too, which is the path W22 proved
  was the unpinned one and carries the riskier free-text value.
- Counts **CALLED from `MessageLedger.pending_traffic`**, never re-derived (#102; a
  re-deriving build passed 48/48 before it was pinned).
- **Extend the call set of the existing validator to the three dispatchers** for `agent=` AND
  `session=` — *never clone it* (Ruling 10 link 1b). Sharing to be proven by **mutation**:
  perturb the predicate, every dispatcher's refusal must move together.
- Ruling 10 link 4: the charset-REFUSAL teaching renders the **CONSTRAINT**, never the bare
  value on a bare line; **`repr()` is not a neutraliser** (named wrong build — a
  footer-shaped instruction inside a repr survives same-line and readable).
- MP-6: an `agent=` registered in two sessions is **ambiguous, not unregistered** — it must
  not be told "is not registered", and the teaching must name `session=` as the remedy.
- R-5: add `MessageLedgerError` to `AppContext.comms`'s `Raises:` (the residual's
  `_comms_dispatch` name is stale — that symbol does not exist; confirmed, it is `.comms`).

**4e. THE SYMBOL INVENTORY — measured, not assumed, and it settles "has anyone started C3?"**
Grepping `loremaster/loremaster/**` and the two fakes for every symbol the contract's harness
imports (`_footer_for`, `_pending_traffic_over`, `_footer_line`, `_traffic`):

| symbol the contract calls | production | test fakes |
|---|---|---|
| `loremaster.messages.PendingTraffic` | **absent** | absent |
| `MessageLedger.pending_traffic` | **absent** | absent |
| `loremaster.server.COMMS_FOOTER_PREFIX` | **absent** | n/a |
| `AppContext._comms_footer` | **absent** | n/a |
| `FakeAgentRegistry._agent_id(session, name)` | n/a | **present** (`_comms_fakes.py`) |
| `FakeDeliveryEdge` / `FakeMessageDatabase` | n/a | **present** (`_message_fakes.py`) |

**Every C3 symbol is unbuilt; nobody has started this slice.** The two the harness leans on
already exist, so the fixture side is sound.

⚠ **AND THE GAP THAT NEEDS A RULING (non-blocking):** `FakeMessageLedger` has `send` / `drain`
/ `ack` / `awaiting_answer` / `_pending` but **no `pending_traffic`** — yet
`_pending_traffic_for` calls exactly that, and SECTION D's `PENDING_TRAFFIC_BACKENDS` drives a
`"fake"` leg through it. So **`loremaster/tests/_message_fakes.py` must be writable or C3
cannot even collect.** My brief's writable set does not name it, and its DO-NOT-TOUCH list does
not exclude it. I am treating it as a FLAG rather than an assumption (brief-base §2).
Note the fake's `pending_traffic` must count **INDEPENDENTLY**, not delegate — SECTION D's
class docstring is explicit that a delegating double "cannot launder a wrong production
statement," and the fake leg exists precisely to be a second opinion.

**4d. Coordination with `builder-c1-1`:** none needed yet — I have made no edit. When I do,
the collision surface is `server.py`'s dispatcher exits. Its owned regions per my brief (the
`lore_tasks` dispatcher, `action=get`, `max_depth` forwarding, the chain render) are
**distinct from** the single-exit footer append, but they are in the same functions, so this
needs a live hand-off rather than an assumption.

---

# §4f · THE LEAD'S RULING (2026-08-02, thread `q:c3-spec-identity`) — and my verification of it

**Option (A) confirmed: I hold for a commit SHA, then build to that commit.**

**Context the lead supplied, which exonerates the contract author:** `contract-04b2-c3fix-1` is
not freelancing — the lead sent it **sidecar Ruling 10** *after* it reported done (the re-ruled
forgery chain: derived link 0, new link 4, `repr()` named as not a neutraliser), which required a
third pass. The rewrite is AUTHORISED work. The lead names the sequencing — spawning me against
the same file — as its own error rather than either agent's discipline failure. **Recording that
here because the durable lesson is a lead-side one:** an in-place contract rewrite and a builder
spawned against that contract cannot overlap, and nothing in the tree makes the overlap visible.

**VERIFIED, NOT TRUSTED** (the lead explicitly asked for re-verification rather than acceptance):

* `0ff05ed` **exists** and is `feat(04b-2): C1 build — the packet's FIRST production code`,
  committing exactly `server.py` +379 and `tasks.py` +195 — `534 insertions(+), 40 deletions(-)`,
  two files. **Matches the lead's summary exactly.** My §1e flag is discharged: the packet's first
  production code is no longer sitting only in a working tree with three agents live in it.
* `contract-04b2-c3fix-1` (pid 752783) is **still alive** at 08:46:30 and the contract is **still
  growing** (215,537 → 222,626 bytes). `test_comms_tool.py` has now also gone modified — the R-4
  co-edits landing. **The tree has NOT settled; I remain correctly blocked.**

**Confirmed by the lead, as I asked:** no driver will restore `server.py`/`tasks.py` while I hold
edits; C1's build is committed so a restore now costs nothing; and c3fix has been told to stop
mutating in-tree entirely, moving its probes to `scripts/scratch_copy.sh` copies.

**New spec fact from C1's builder, recorded so my build inherits it:** the currency gate reports
**202 orphans, all C3's** — 200 `comms_footer` + 2 `comms_tool`. That is the expected state while
C3 is unbuilt, and **my build is what discharges it.** It is therefore a receipt I owe in my build
report: the orphan count must go to zero (or to an adjudicated remainder I name), and I will run
`scripts/pending_contract_gate.py --currency` rather than assert it.

## 4f.0 · ⚠ TWO CORRECTIONS TO MY OWN CLAIMS — made before anyone had to catch them

**(1) "C3 cannot even collect" (§4e, §4f.1) was WRONG.** Measured at `0d24c12`:
`pytest --collect-only -q` returns **`217 tests collected in 0.07s`**. Collection only IMPORTS the
test module; `FakeMessageLedger.pending_traffic` is called inside an async test BODY
(`_pending_traffic_for`), so the missing method fails at **RUN** time, not collection. The gap is
real and still blocks SECTION D's `"fake"` leg — but I overstated its blast radius, and an
overstated blocker is the same species of un-derived claim as an understated one. Re-derived, not
inherited from my own earlier sentence.

**(2) A piped exit code lied to me, in the session where I am the one warning about it.** I first
checked the fake with `grep … | head; echo exit=$?` — which reads **`head`'s** status, always `0`,
so a *missing* symbol reported "exit=0" and read as present. Caught it on sight and re-ran with
the grep's status read directly (`if grep -q …`). This is finding #194's shape (*"if step N
silently no-opped, would step N+1 still print something that reads as success?"*) and the answer
was yes. **Recording it because the law says the instrument is the deliverable:** the honest form
is `if grep -q PATTERN FILE; then … else … fi`, never a pipeline whose last stage is `head`.

## 4f.1 · ⚠ STILL OPEN — the writable-set gap the ruling did not cover

§4e's question is **unanswered** and it is a hard blocker at collection time, not a nicety:
`FakeMessageLedger` still has no `pending_traffic` (re-checked at 08:46 — `_message_fakes.py` is
NOT among the modified files, so c3fix has not added it either). SECTION D's `"fake"` leg calls it
directly. So one of two things must be true before I can go green, and only the lead can say which:

* **(i)** `loremaster/tests/_message_fakes.py` joins my writable set and I implement the fake's
  own INDEPENDENT count (SECTION D requires independence — a delegating double "cannot launder a
  wrong production statement"); or
* **(ii)** `contract-04b2-c3fix-1` ships it as part of the contract, and I must not touch it.

Asked as a single-item ping rather than stacked with anything else. Defaulting silently to (i)
would be me writing test-tree code my brief never granted; defaulting to (ii) and being wrong
means C3 cannot collect at all.

---

# §6 · THE BUILD (against `0d24c12`) — what landed, with receipts

## 6.1 · SECTION D — the shared counting seam. **COMPLETE and LIVE-VERIFIED.**

**`loremaster/loremaster/messages.py`:**
* **`PendingTraffic`** — a `BaseModel`, `extra="forbid"` per house law, carrying R4's two
  counts plus a `pends` property. The property exists so the footer's trigger — a
  **disjunction** — has ONE home: a caller re-spelling `unread or unacked` is how the `(0, 3)`
  world (nothing new to read, three acks owed) came to serve nothing (W23).
* **`MessageLedger.pending_traffic(*, agent_id)`** — keyword-only, matching every sibling verb
  (`send`/`drain`/`ack`/`awaiting_answer`), which the contract pins explicitly. ONE round trip:
  a minimal projection over `TO_RELATION` tallied in Python, mirroring `drain`'s own whole-set
  arithmetic. **Counts the WHOLE inbox, never a capped window** — a footer riding `drain`'s cap
  would under-report the moment an inbox exceeded it.
  * Predicates are R4 **as written**: `unread` = `seen_at IS NONE` (any grade);
    `unacked_directives` = `acked_at IS NONE AND grade = 'directive'`, **no `seen_at` clause** —
    so an unseen directive counts in BOTH and a seen, unacked signal in NEITHER.
  * **Bound parameters throughout** (`$agent`, a `RecordID`) — store reference §2's idiom.

**`loremaster/tests/_message_fakes.py`: `FakeMessageLedger.pending_traffic`** — deliberately
**does NOT delegate** to production. That independence is the entire value of the fake leg: a
delegating double agrees with whatever predicate production used *by construction*, so the two
backends would stop being two opinions. Re-derived from edge state directly.

**RECEIPT — the live-store leg, which is the only instrument that can see production's own
predicate** (a build dropping R4's conjunct or riding `drain`'s cap is invisible to every fake):

```
$ uv run pytest test_comms_footer.py -k "PendingTrafficCountIsONEImplementation and real" -q
5 passed, 212 deselected in 9.25s
```

And with both backends plus the existence/conformance pins:

```
$ uv run pytest test_comms_footer.py -k "PendingTrafficCountIsONEImplementation or ProductionSeamEXISTS" -q
7 failed, 12 passed, 198 deselected in 3.47s
```

**The 12 passed are SECTION D's own property. All 7 failures are `ImportError:
COMMS_FOOTER_PREFIX`** — the footer itself, not yet built. Scope stated rather than implied.

## 6.2 · ⛔⛔ ESCALATION — a CROSS-SLICE COLLISION between C1's build and C3's contract

**`TestTheFooterRidesTheOUTCOMENotTheVERB::test_the_declared_action_PARTITION_covers_the_
dispatchers_OWN_action_set` is RED, and I cannot fix it without editing the contract.**

Measured:

```
_TASK_ACTIONS = ('create','query','transition','supersede','rollup','create_many','blockers','get')
contract declares: WRITE=(create,create_many,transition,supersede)  READ=(query,rollup)
undeclared in tasks: ['blockers', 'get']
_FINDING_ACTIONS: partition matches production -> True   (only `tasks` collides)
```

**Provenance, derived with `git log -S`:** both `blockers` and `get` were added by
**C1's build at `0ff05ed`** — which landed **BEFORE** the contract's `0d24c12`. So the contract
was committed against a production action set it does not cover.

**The pin is CORRECT and is doing exactly its job.** Its own docstring: *"A future action added
to `_TASK_ACTIONS`/`_FINDING_ACTIONS` and NOT adjudicated here reddens this pin — it cannot be
silently exempt from the footer property, which is exactly how six of nine write actions became
exempt."* This is that mechanism firing on a real, new, unadjudicated pair.

**Why it is an ESCALATION and not an edit:** the adjudication has to land in the CONTRACT's
`TASK_READ_ACTIONS`, and my brief forbids me touching it (*"a pin that looks wrong is an
ESCALATION, never an edit"*). It is also **not cosmetic** — `TASK_READ_ACTIONS` is the sweep for
*"a READ action NEVER footers"*, so until `get`/`blockers` are adjudicated in, **neither is
covered by that property at all**, which is the exact silent-exemption the pin exists to stop.

**My recommendation, for the author or the lead to ratify:** both are **READS**.
`get` is a plain read verb (Ruling 8 mints it mirroring `lore_findings action=get`) and
`blockers` is a dependency walk. So `TASK_READ_ACTIONS = ("query", "rollup", "get", "blockers")`,
which makes the partition equal production and extends the never-footers sweep over both. I have
**not** made that edit.

## 6.3 · NOT YET BUILT (the remaining work, named honestly)

`COMMS_FOOTER_PREFIX` · `AppContext._comms_footer` · the trigger/resolution wiring at the three
dispatchers' single exits · Ruling 10 link 1b (extending `_validate_comms_identities`'s call set)
· link 4 (the fenced refusal; `repr()` killed) · #219's four prose sites · R-5's `Raises:` ·
MP-6's ambiguity classification. §4c carries the design for each; none of it is started.

## 6.4 · THE FOOTER + #219 + R-5 — what landed and its receipts

**`COMMS_FOOTER_PREFIX`** (`"— pending traffic"`) is exported from `server.py` rather than
transcribed by each reader: a literal copied into a test would let the footer's shape drift
while every placement pin silently stopped discriminating.

**`AppContext._comms_footer(*, identity, traffic, authenticated)` → `Rendered | None`.**
* Built through **`render_line`**, never a bare f-string (§B5/L1) — which also makes the line
  structurally single-line, so it cannot forge a row boundary in the render it is appended to.
* The **trigger lives in the helper**, as `PendingTraffic.pends` — one spelling of the
  disjunction. A caller re-deriving `unread > 0` is exactly W23/DW1.
* **`authenticated` is the whole R8(2) split**: the RESOLVED render names `action=drain`; the
  FALLBACK render is third-person with no imperative, because an exact match against a
  free-text column is a *match*, not an authentication — and a drained message is marked seen
  for its real owner, who then never sees it.
* Returns `None` on a quiet inbox: a signal that fires on the healthy state is noise.

**#219 — all four prose sites repaired, guard KEPT.** The docstring rationale is replaced with
what the charset *actually* buys (`fullmatch` vs `match` per #210; render-safety by
construction; the cheap gate in front of the registry read), and the served `ValueError` no
longer claims inlining. **Ruling 10 link 4 is implemented in the same edit**: the refusal
states the CONSTRAINT in prose and carries the offending value through **`render_fenced`** —
`repr()` explicitly rejected, because it escapes newlines and leaves a same-line forged
instruction intact and readable.

```
$ uv run pytest test_comms_footer.py -k "CharsetGuardDoesNotTeachAFalseRationale or
    FalseRationaleSurvivesNowhere or NoCommsIdentityReachesQueryTEXT" -q
10 passed, 207 deselected in 1.68s
$ uv run pytest test_comms_footer.py -k "FooterIsBuiltThroughTheRenderSeam or
    FALLBACKFooterIsAlsoBuilt" -q
2 passed, 215 deselected in 0.69s
```

**R-5** — `MessageLedgerError` added to `AppContext.comms`' `Raises:`, naming its subclasses,
without displacing the two families already documented.

## 6.5 · ⛔ THE NUMBERS, AND THEIR SCOPE STATED

**C3 alone, at `0d24c12` + my working tree:**

```
$ uv run pytest loremaster/tests/test_comms_footer.py -q -p no:randomly
162 failed, 55 passed in 14.77s
```

**55 passed is a PARTIAL build and I am not dressing it up.** The 162 failures are dominated by
the unbuilt dispatcher wiring (§6.3) — every trigger, placement, identity and teaching pin
routes through `_write_call`/`_tasks_call`, which need `agent=`/`session=` on the dispatchers.

**Neighbouring suites — the regression check that actually mattered**, because I reshaped the
shared `ValueError` that pre-existing pins assert on:

```
$ uv run pytest test_comms_tool.py test_message_ledger.py test_render_seam_pins.py -q
2 failed, 1116 passed, 14 skipped in 41.66s
```

**The 9 `test_comms_tool` pins that assert the value appears in the refusal PASS** — the fenced
message satisfies them, so link 4 did not cost the teaching. **The 2 failures are the
`_INSTRUCTIONS` pins**, and they are the lead's own **known C3 orphans**: the currency gate
reported `202 orphans, all C3's (200 comms_footer + 2 comms_tool)`, and exactly 2 comms_tool
pins fail. **The count corroborates independently.** I also confirmed `git diff` shows my edits
touch `_INSTRUCTIONS` **zero** times.
⚠ **Stated bound:** I did NOT re-run those 2 at `0d24c12` with my changes reverted — the
corroboration is the orphan count plus the zero-diff, which is strong but is inference, not a
controlled before/after. Saying so rather than claiming a control I did not run.

**⚠ NOT a gates-green claim.** `ruff check` is clean on my three files. `scripts/typecheck.sh`
is **RED AT HEAD** from packet 39's unbuilt contract (#306/#307) — not mine, not touched by me.
I did not run the full suite (brief-base §3: run the scoped set, not the repo).

## 6.6 · PACKAGES CONSIDERED

One mechanism was specified this session: **the two-count inbox query**.

| mechanism | alternative evaluated | what I READ | verdict |
|---|---|---|---|
| `MessageLedger.pending_traffic`'s counting | a store-side aggregate (`count()` / `GROUP BY`) vs materialise-and-tally | `MessageLedger.drain`'s implementation (it tallies `total_pending`/`directive_pending` in Python over the whole set) + store reference §2 DML IDIOMS | **bespoke, in-house seam** — reuses `_query`/`_as_rows`/`RecordID` and drain's own arithmetic. No library is implicated: this is one bound-parameter SELECT against our own schema. A second aggregate grammar for a number drain already computes would be #102's shape. |

No new dependency is implicated by any remaining item in §6.3 either — the footer rides
`loremaster.render`, which already exists and is already the one render seam.

---

# §7 · THE HANDOFF — why I stopped here, and the exact next step

**This is a structured handoff under the third legitimate deferral shape (capacity), not a
can-kick.** My context is largely spent on the blocked-phase investigation and a 3,900-line
contract. The remaining work is the *highest-blast-radius* part of the slice: wiring three
dispatchers that `builder-c1-1` has just committed production code into. Half-wiring them in a
dying context risks breaking `0ff05ed` — committed, green work — which is a worse outcome than
an honest partial. **Delegation is unavailable to me (my brief forbids spawning subagents), so
this is the handoff the law prescribes when delegation cannot cover it.**

**The next step, in order, for whoever continues:**
1. **Resolve §6.2 first** — the partition collision is a contract edit and it gates SECTION B's
   read sweep. Nothing downstream is trustworthy while it is red.
2. Add `agent: str | None = None` + `session: str | None = None` to `AppContext.tasks`,
   `.findings`, `.claim_task` **and** their `@mcp.tool` registrations (SECTION H pins the
   `Field(description=)` payoff text — R8's rider, and it is load-bearing: MEASURED, terse
   descriptions mean neither Sonnet 5 nor Opus 5 passes `agent=`).
3. **Link 1b**: first line of each of the three dispatchers calls
   `AppContext._validate_comms_identities(...)` — **extend the call set, do not clone.** The
   AST scan in `TestTheIdentityParameterSurfaceIsDERIVEDNotEnumerated` is unforgiving about
   this and its forwarder exemption has already been proven to swallow DELTA-3 once.
4. The single-exit footer append: resolve identity → `pending_traffic` → `_comms_footer` →
   append. **The helper already exists and is green**; the remaining work is the trigger's
   outcome-keying (write-count for batches, the losing-claim branch) and R8(1)'s teaching.
5. `_INSTRUCTIONS` paragraph (SECTION E + the 2 comms_tool orphans).

**`loremaster.__file__` receipt (#140):** I made **no scratch copy** — every measurement in §6
was run against the real tree at
`/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`, with no mutation probe,
so there is no isolated tree whose provenance could be poisoned. Stated explicitly because its
absence would otherwise read as an omission.

**Coordination with `builder-c1-1`:** no collision occurred. My edits are `messages.py` (new
symbols only), `_message_fakes.py` (new method only), and `server.py` — where I added a new
constant block and a new `_comms_footer` method, and edited two docstrings plus one `Raises:`
block. **I touched none of C1's owned regions** (the `lore_tasks` dispatcher body, `action=get`,
`max_depth` forwarding, the chain render). Step 2 above is where a real hand-off is needed,
because that edits `AppContext.tasks`' signature.

# §5 · STATE (blocked-phase — superseded by the summary block at the top)

*This section recorded the blocked state before `0d24c12` landed. Superseded by §6/§7.*

---

# §9 · ⛔⛔ THE C-DEF VERDICT'S **B1 DOES NOT REPRODUCE** AT `0d24c12` — measured, with a control

**Relayed to me as decisive: *"no Ruling-10-compliant build can satisfy this contract"*, because
leg 1 has three asserts, `render_fenced` fails its `"\n" not in message"` leg and
constraint-only fails its `"mallory" in message` leg. I built the `render_fenced` shape, so I
could TEST that rather than relay it. It does not reproduce.**

**Receipt 1 — leg 1's actual asserts at `0d24c12`, read from the commit, not the working tree:**

```
$ git show 0d24c12:…/test_comms_footer.py | sed -n '/def test_a_charset_illegal_identity_is_REFUSED_before_any_use/,…/p' | grep -E "assert|pytest.raises"
        with pytest.raises(ValueError) as caught:
        message = str(caught.value)
        assert _agent_name_pattern_text() in message, (
```

**ONE assert.** And a grep of that whole test body for `\n`, `mallory`, or `HOSTILE_OWNER in`
returns **0**. There is no newline assert and no value-naming assert in leg 1.

**Receipt 2 — my `render_fenced` build PASSES leg 1 on the member that reaches the validator:**

```
$ uv run pytest -k "test_a_charset_illegal_identity_is_REFUSED_before_any_use" -q
6 failed, 2 passed, 217 deselected in 1.13s
```

**The 2 that PASS are `lore_comms` × {agent, session}** — the ONE link-0 member wired to
`_validate_comms_charset` today, i.e. the only one that actually exercises my fenced refusal.
**The 6 failures are the three ledger dispatchers, and they fail because I never wired link 1b
— they raise no `ValueError` at all**, so `pytest.raises` fails. That is my unbuilt work, not a
contract defect. **The claimed trap is not reachable at `0d24c12`.**

**My diagnosis of where B1 came from, offered as a lead not a verdict:** those three asserts are
verbatim the **SECOND-wave** class `TestAHostileAgentValueIsREFUSEDBeforeItReachesAnyRender`,
described in `REPORT-contract-04b2-c3fix-1.md` §11.3 as *"raises ValueError; the message carries
no raw newline; the raw multi-line value is not embedded verbatim; and it still names the
offending value."* `0d24c12` **replaced** that class with
`TestAHostileIdentityIsREFUSEDAtEveryLink0Member`, whose leg 1 keeps only the constraint assert
and moves containment to leg 2's `_unfenced` helper — which `render_fenced` satisfies **by
construction**, since `_unfenced` exists precisely to strip fenced regions. **B1 appears to have
been graded against the superseded contract.**

⚠ **STATED BOUNDS, so this refutation does not over-claim:**
* I refute **B1's leg-1 trap only.** I do **not** refute the other two findings, and one of them
  I can partly **corroborate**: link 1b is genuinely unwired on the three ledger dispatchers —
  that is exactly my §6.3 unbuilt work — so `lore_claim_task` really does lack the gate today.
* I could not exercise my fenced refusal through the three ledger dispatchers, because wiring
  them is the unbuilt step. My evidence is the `lore_comms` leg, which is the same validator on
  the same value; extending it to the others is an inference from ONE implementation, not a
  measurement of three.
* If leg 1 is re-authored later to add the two asserts B1 describes, the trap becomes real. My
  claim is scoped to the contract **as committed at `0d24c12`**.

**Consequence if this holds:** the C-DEF is not a C-DEF, and the contract does not need the
rewrite. The two remaining findings are real build/contract work, not an unsatisfiability.

# §8 · ⚠ PROVENANCE CORRECTION AT CLOSE-OUT — where my work actually lives

**Re-derived at close-out rather than asserted from memory, and it CHANGED the answer.** My
first draft of the closing line claimed the contract was untouched and named four tree writes.
`git status` then showed `test_comms_footer.py` **modified** and `messages.py` /
`_message_fakes.py` **clean** — the opposite of what I believed on both counts. Checking
instead of shipping the sentence:

* **The lead committed my SECTION D work as `d3b8d88`** (*"wip(04b-2): C3 build PARTIAL —
  halted on the C-DEF, committed to preserve it"*): `messages.py` +85, `server.py` +80,
  `_message_fakes.py` +35. That is why those two files read clean — **not** because my edits
  vanished. My escalation about uncommitted work sitting only in a working tree was acted on,
  applied to my own output.
* **HEAD is now `01e7e3c`**, and `58f4f38` records *"C3 delta round 3 — C-DEF, and TWO blockers
  live on the CORRECT build"*. The partition collision I escalated in §6.2 is adjudicated as a
  **C-DEF**, and the lead's `01e7e3c` covers *"the partition collision and the fakes
  authorship"* — so §4f.1's open grant is settled in the record rather than by my assumption.
* **⚠ MY #219 + LINK 4 + R-5 WORK IS STILL UNCOMMITTED** — `server.py`, 60 insertions /
  17 deletions, and **the working tree is its only copy.** Verified as entirely mine: all five
  hunks fall in exactly two regions (`AppContext.comms`' `Raises:` block, and
  `_validate_comms_charset` / `_validate_comms_identities`). Nobody else's work is entangled
  in that file. **This needs a commit.**
* **`test_comms_footer.py` is modified (+19/−1) and it is NOT mine** —
  `contract-04b2-c3fix-1` is still live. I did not touch the contract at any point.

**The retraction:** my closing line originally said *"the contract was not touched: `git status`
shows `test_comms_footer.py` clean against `0d24c12`"*. **The first clause is true and the
second is now false.** I did not touch it; it is nonetheless dirty, because its author is still
working. Both halves stated separately, because conflating them is how a true claim smuggles a
false one.

*Written 2026-08-02 by `builder-c3-1` (Opus) against `feat/surreal-unification`, blocked phase
at HEAD `58f2786`, build phase at `0d24c12`. Every measurement is mine and re-runnable: §1 with
`git diff --stat` / `stat -c '%Y %s'` / `ps -eo pid,etimes,args`, §6 with the pasted pytest and
ruff invocations. I did NOT read `/home/ejprice/scratch-c3-ref` (the reference build), so this
build is independent of it. No git write command was run; my tree writes are this report,
`loremaster/loremaster/messages.py`, `loremaster/loremaster/server.py`, and — disclosed as a
deviation — `loremaster/tests/_message_fakes.py`. **I never touched the contract.** See §8 for
where each of those writes lives at close-out, and for the one that is still uncommitted.*
