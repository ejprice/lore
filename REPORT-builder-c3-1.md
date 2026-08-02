# REPORT-builder-c3-1 — C3 BUILD: **BLOCKED AT START**, my spec is being rewritten under me

**brief-base v9 read**
**brief project v7 read**

## SUMMARY BLOCK

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

# §5 · STATE

**Blocked, cleanly, with nothing written and nothing at risk.** I am standing by. Unblock me
with a committed spec (a SHA) or a freeze ruling, plus the assurance that no driver will
restore `server.py`/`tasks.py` under me, and §4c is ready to execute immediately.

*Written 2026-08-02 by `builder-c3-1` (Opus) against `feat/surreal-unification`. Measurements
in §1 are mine, timestamped, and re-runnable with `git diff --stat`, `stat -c '%Y %s'` and
`ps -eo pid,etimes,args`. No git write command was run; this file is my only tree write.*
