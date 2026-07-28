# REPORT-adversary-04b1 — grading the 04b-1 test contract

brief-base v7 read

*Every claim in this file is scoped to **branch `feat/surreal-unification`**, measured
**2026-07-28**. The graded artifacts are named by SHA in §0 because **the target moved
during this audit** (see D-0). No repo file was edited: my only write is this report. All
live probes ran against spike-surreal `ws://127.0.0.1:18000` (TEST); `:18500` was never
touched.*

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — 3 wrong builds survive the whole contract, each
  reproduced with a correct-build control.
- **P1 headline — THREE wrong builds passed 80/80 (sections A–H):** `truncated_explicit`
  (truncation computed only when `max_depth` is passed explicitly) · `split_decode` (the
  #248 hand-rolled `split(":")` id parse, an 8th copy, in the file this packet edits) ·
  and the QUANTIFIER door `superseded blocker` (R3's "unclaimable forever" reached through
  an unguarded third cause). Nine other wrong builds were correctly KILLED (§P1 table).
- **MISSING PINS, ranked:** MP-1 a discriminating truncation pair at the **DEFAULT** bound ·
  MP-2 a **REAL, ACCEPTED** bracket-rendered task id through the mirror + traversal ·
  MP-3 a `max_depth` **argument-bound** pin (`256` → raw `(unspecified rejection)`; `0` →
  `ids=[] truncated=True`) · MP-4 adjudicate `server.py::_find_key_cycle` (becomes policy
  copy #2, its own sentence + `ValueError`) · MP-5 the superseded-blocker door.
- **X1 reverse arrow: MEASURED, NO BLOCKING DIFFERENCE — 15 of 15 properties identical**
  (§X1 table). Two of my own probe legs lied first and were caught by their controls.
- **X2 discharged:** PROOF 5 both legs **HELD, EXIT=0**, tree byte-exact · PROOF 3 re-run
  **UNPIPED, 12/12, EXIT=0**, md5 `dc5dc6f18eb6dc87dbb8cd8d26df417d` · **R-e CONFIRMED REAL
  and WIDER than stated** (`generate_message_ddl` absent ⇒ `to` never migrated).
- **X3 satisfiability: 80 passed / 0 failed** on a known-correct reference build, AND
  still 80/80 + mypy-clean **after `ruff --fix`** reorganised imports (harder leg).
- **D-0 PROCESS FLAG (read first):** the contract grew 2666 → 3241 lines and gained an
  untracked 21-pin sibling *while I was grading it*. Two parallel authors. §0.
- **Residual R-b MEASURED (was "unmeasured, pinned anyway"):** `ENFORCED` DOES resolve an
  endpoint created earlier in the same uncommitted txn — no STOP. §X-Rb.
- **`Packages considered:`** graph closure → SurrealDB `@.{..+collect}` (read: my own X1
  live measurement + probe §5.1) → **replace** · cycle detection → engine self-reach
  operator (read: probe §5.4 + my §MP-4a measurement) → **CONFLICT, escalated** · row
  existence → `loremaster.agent_existence` (read: module source) → **reuse via
  generalisation** · retry/backoff → `loremaster.store._txn` → **keep**.
- **`loremaster.__file__` = `/home/ejprice/scratch/adv04b1-ref/loremaster/loremaster/__init__.py`**
  (`scratch_copy.sh --verify-only` → VERIFIED, all four members).
- **Receipt pointers:** §0 (drift) · §X1 · §P1 · §P1b table · §P2 · §MP-1…5 · §X2 · §X3 ·
  §P6b · §P-PKG · §RESIDUALS.

---

## §0 — WHAT I GRADED, AND THE FACT THAT IT MOVED (D-0, escalation)

My brief named **HEAD `f2bebfc`**, contract **`688621b`**, "80 pins". Measured at spawn:
`test_blocks_edge.py` = **2666 lines**. Measured 40 minutes later, mid-audit: **3241 lines**,
plus a new untracked **`test_query_tasks_bounded.py` (43 KB, 21 pins)** and an untracked
`REPORT-contract-04b1-253.md`.

```
$ git log --oneline -3
98d5084 test(04b-1): #253 Section I — the late-landing requirement, 14 pins (3 RED, 11 regression)
f2bebfc docs(04b-1): rule the contract's five escalations, plus one rider the author could not have raised
688621b test(04b-1): the blocks-edge contract — 80 pins, 72 RED, five escalations
```

The addendum's own docstring states the cause: *"A second author was commissioned in
parallel on the belief that [the #253 ping] had not [reached its author]."* So **two authors
independently produced #253 coverage**, and one of the two artifacts is uncommitted.

**What I did about it.** I pinned my scratch tree's test files to **exactly `98d5084`** (md5
`f7666cb04feee6561a0180cd9a92b101`, byte-identical to the repo's working copy) and graded:

| artifact | SHA / state | pins | my depth |
|---|---|---|---|
| `test_blocks_edge.py` **sections A–H** (the brief's target) | `688621b`, unchanged at `98d5084` | **80** | **FULL** — all probes |
| `test_blocks_edge.py` **Section I** (#253) | `98d5084` | 14 | RED-honesty only, declared |
| `test_query_tasks_bounded.py` | **UNTRACKED** | 21 | RED-honesty only, declared |

**Escalation for the lead, not settled by me:** an uncommitted 21-pin contract addendum has
no durable address and cannot be cited (CLAUDE.md's archiving law). It is also an untracked
file a scratch/deploy step will silently drop. And it *imports from a sibling test module*
(`from test_blocks_edge import …`), which its author correctly escalates. **Decide whether it
lands, merges into Section I, or is discarded — and re-run an adversary pass on whichever
survives.** My verdict below does **not** cover it.

---

## §X1 — THE REVERSE ARROW, MEASURED (the lead's rider)

Ruling E-1 is `RELATE $blocker->blocks->$task`, so the transitive blocker read traverses
**`<-blocks<-`**. Probe P4 measured only `->blocks->`. I measured the reverse on
spike-surreal 3.2.1, **every leg paired with a same-run forward control**.

| # | property | FORWARD (P4, 2026-07-26) | REVERSE (X1, 2026-07-28) | same? |
|---|---|---|---|---|
| 1 | bare idiom returns TERMINAL-DEPTH only | yes | yes — `c4.{1..3}<-blocks<-` → `[task:c1]` | ✅ |
| 2 | `+collect` is the CLOSURE | yes | yes — `[c3, c2, c1]` | ✅ |
| 3 | `+collect` DEDUPLICATES a diamond | yes | yes — `[middle, right, left, root]`, root once | ✅ |
| 4 | bare form does NOT dedupe | `[leaf, leaf]` | `[root, root]` | ✅ |
| 5 | ordered by PROXIMITY (nearest first) | yes | yes — deep chain `first=d297 last=d42` | ✅ |
| 6 | `+inclusive` adds the root | yes | yes — n=4 incl. `c4` | ✅ |
| 7 | leaf / isolated node → `[]` | yes | yes, both | ✅ |
| 8 | `TIMEOUT` is a PARSE ERROR on the BARE idiom | yes | yes — **identical message and column** | ✅ |
| 9 | `SELECT id, @.{…}(…) … TIMEOUT` form works | yes | yes | ✅ |
| 10 | cycle TERMINATES under `+collect` | 4-cycle | **3, 4 AND 5** | ✅ (widened) |
| 11 | node appears in its OWN `+collect` reach iff cyclic | yes | yes for 3/4/5; acyclic control → absent | ✅ |
| 12 | BARE form is NOT a detector (arithmetic accident) | 8 mod 4 = 0 → false hit | **identical**: 3→miss, 4→hit, 5→miss | ✅ |
| 13 | min-depth > 1 over a cycle drops nothing | yes | yes — `{2..3+collect}` → 2 nodes | ✅ |
| 14 | `{0..}` / `{..257}` / open `{..}` past 256 → LOUD errors | yes | yes — same three messages | ✅ |
| 15 | explicit bound TRUNCATES **SILENTLY** | 256 of 299 | **256 of 299, no error, no signal** | ✅ |

Extra, unmeasured on either arrow before: **`ENFORCED`'s refusal is identical whether the
ghost is on the `in` or the `out` side** (`NotFoundError: The record 'task:ghost_in' does not
exist`), and **a traversal from a NON-EXISTENT start id returns `[]` silently on BOTH arrows**
— which is why `test_an_UNKNOWN_task_id_raises_TaskNotFoundError` is load-bearing.

**VERDICT: the inference held. No blocking finding. The contract's transitive-read pins rest
on measured ground now, not on an inference.**

### ⚠ My own two probe failures, both self-caught (P0)

1. **Run 1's self-in-reach check printed `False` for all three cycles** — it compared
   `f"task:{start}"` against `str(list_of_RecordID)`, whose element repr is
   `RecordID(table_name=task, record_id='k3_0')`. The **rendered list printed beside it**
   plainly contained the node. Had I trusted the boolean, I would have filed a blocking
   false difference. Fixed: compare `{str(v) for v in result}`.
2. **Run 2's `TIMEOUT`-on-a-bare-idiom leg wrapped the idiom in `SELECT VALUE id FROM …`**, so
   `TIMEOUT` bound to the outer SELECT and **both directions returned OK**. The **forward
   control** exposed it (§5.2 says forward is a parse error). Fixed: idiom = whole statement.
3. **Run 2's L6 printed `REV n=0` vs `FWD n=256`** — which read as a blocking difference. It
   was a FIXTURE artifact: SurrealQL's `FOR $i IN 0..N` is end-EXCLUSIVE, so the tail node the
   reverse read starts from never existed, and a reverse read from a non-existent start
   returns `[]`. Re-run with explicit node/edge-count assertions: **REV 256, FWD 256**.

---

## §P1 — WRONG BUILDS vs THE REAL CONTRACT (the headline)

Method: `./scripts/scratch_copy.sh` → provenance VERIFIED → a **known-correct reference
build** of the whole packet (schema + generalised `agent_existence` + `tasks` + `messages`),
then ONE surgical mutation per variant, then the REAL contract (sections A–H, 80 pins).

| # | wrong build | result | verdict |
|---|---|---|---|
| W1 | **`truncated_explicit`** — truncation computed only when `max_depth` is supplied; the DEFAULT path hard-codes `False` | **80 passed** | 🔴 **BLOCKER B-1** |
| W2 | **`split_decode`** — traversal decode hand-rolled `str(x).split(":",1)[-1]` instead of `_bare_id` | **80 passed** | 🔴 **BLOCKER B-2** |
| W3 | **superseded blocker** (not a code mutation — the *correct* build reaches R3's harm) | n/a — contract has no pin | 🔴 **BLOCKER B-3** |
| W4 | `truncated_false` — hard-code `False` | 1 failed | ✅ killed |
| W5 | `truncated_true` — hard-code `True` | 3 failed | ✅ killed |
| W6 | `private_copy` — call the shared policy, re-decide underneath (routing ≠ sharing) | 3 failed | ✅ killed |
| W7 | `relate_after` — CREATE then RELATE in a SECOND txn (W-D) | 1 failed | ✅ killed |
| W8 | `no_dedupe` — mirror RELATEs the RAW `blocked_by` | 1 failed | ✅ killed |
| W9 | `edge_cycle` — cycle check walks the EDGE not the COLUMN | 1 failed | ✅ killed |
| W10 | `no_cycle_guard_on_persisted` — guard never leaves the batch | 1 failed | ✅ killed |
| W11 | `reversed_edge` — E-1 silently overturned | **15 failed** | ✅ killed |
| W12 | `private_sender` — hand-rolled sender check under the shared call | 1 failed | ✅ killed |
| W13 | `sender_after_recipients` — E-4 order violated | 1 failed | ✅ killed |
| W14 | `sender_as_recipient_error` — E-4 vocabulary violated | 1 failed | ✅ killed |

**Nine of twelve code mutations died, several of them hard.** This is a strong contract. The
three that lived are all the same shape: *an invariant conditioned on the one input value the
author happened to exercise.*

### B-1 — `truncated` is only honest on the path no pin uses

The contract's own claim (`TestTheReadIsHONESTAtItsBound` docstring): *"a build hard-coding
`truncated = False` dies on the second; a build hard-coding `True` dies on the first."* **Both
halves are TRUE** (W4, W5). But `max_depth` appears in the whole 3241-line file exactly twice,
**both times as the literal `2`**:

```
$ grep -n "max_depth" loremaster/tests/test_blocks_edge.py
  1763:        result = await _transitive_blockers(ledger, chain[-1], max_depth=2)
  1787:        result = await _transitive_blockers(ledger, chain[-1], max_depth=2)
```

A 100% parameter-value monoculture on a parameter the code branches on. Control pair, same
fixture (`TASK_BLOCKER_MAX_DEPTH + 3` deep chain), same script, only the build changed:

```
########## A. REFERENCE (correct) build:
TASK_BLOCKER_MAX_DEPTH = 32; chain depth = 35
DEEP  chain, DEFAULT bound : n=32  truncated=True    (true upstream = 34)
SHALLOW node, DEFAULT bound: n=3   truncated=False   (true upstream = 3)
DEEP  chain, max_depth=2   : n=2   truncated=True

########## B. WRONG build (truncated_explicit):
DEEP  chain, DEFAULT bound : n=32  truncated=False   (true upstream = 34)   <-- 32 of 34, served as WHOLE
SHALLOW node, DEFAULT bound: n=3   truncated=False
DEEP  chain, max_depth=2   : n=2   truncated=True                            <-- both contract legs satisfied
```

**The default path is the one 04b-2's *"renders its critical path"* will call.** This is
precisely the trust-doctrine defect E-3 exists to prevent, shipped green.

### B-2 — every ACCEPTED task id in the contract is bare; only REFUSED ids are bracket-shaped

`PHANTOM_TASK_IDS` varies id shape ×4 — but **only on legs where the id is refused**, so no
shape ever travels the edge, the mirror or the traversal. Every ACCEPTED id in the file is
`uuid4().hex` or `<word>_<hex>`. Measured renderings:

```
'abc'                                  -> 'task:abc'
'real_ab12'                            -> 'task:real_ab12'          <-- every contract fixture
'00000000000000000000000000000000'     -> 'task:⟨…⟩'
'0199c4f1-7d2a-4e51-9a63-000000000000' -> 'task:⟨…⟩'
'20260728'                             -> 'task:⟨…⟩'
'wave-7-charter'                       -> 'task:⟨…⟩'
```

Control pair (`prove_uuid_id.py`, both builds, same fixture):

```
########## A. REFERENCE:      UUID-shaped waiter -> ['0199c4f1-7d2a-4e51-9a63-0000000000aa']  correct? True
########## B. split_decode:   UUID-shaped waiter -> ['⟨0199c4f1-7d2a-4e51-9a63-0000000000aa⟩'] correct? False
                              BARE-hex waiter    -> correct? True        <-- invisible everywhere the contract looks
                              get_task(served id) -> TaskNotFoundError: no task with id '⟨0199c4f1-…⟩'
```

The contract's OWN fixture comment names this hazard — *"finding #248 records SEVEN hand-rolled
copies of that parse, and `tasks.py` is on the list, so an EIGHTH is one careless line away in
exactly the file this packet edits"* — and then does not pin it on the accepted side. This is
04a residual **R-2's positive half**, which the author closed in `test_enforced_relations.py`
and re-opened in its own new file.
**Honest bound:** production's only id minter is `uuid4().hex` (not bracket-rendered), so the
defect is **latent, not live, today**. `TaskLedger.create_many(ids=…)` is public API and
`blocked_by` is an unconstrained `array<string>`, so the trigger is any caller-supplied id.

### B-3 — the QUANTIFIER DOOR: R3's harm through an unguarded third cause

R3's justification for changing a live verb is *"a loud refusal replaces a silent black hole"*
— the black hole being *"a task created and then **unclaimable forever, silently**"*. The
contract guards **two causes**: a phantom blocker, and a cycle. There is a third, and nothing
touches it. Measured on the **correct reference build**:

```
blocker d8370610… superseded by bc537b5e…
  its status is 'open';  TERMINAL_STATUSES = ['done', 'wontfix']   -> is it terminal? False
create_task(blocked_by=[<superseded>]) -> ACCEPTED
claim_task(waiter) -> claimed=False
  freed via transition->done?     NO — IllegalTransitionError: task … is superseded
  freed via transition->wontfix?  NO — IllegalTransitionError: task … is superseded
  freed via supersede?            NO — IllegalTransitionError: task … is already superseded
re-claim after every escape attempt -> claimed=False
POSITIVE CONTROL: waiter on a NORMAL blocker driven to done -> claimed=True
```

Existence passes (the row exists). No cycle. Nothing refuses. The waiter is unclaimable
forever, silently — **the exact outcome, through a door with a different cause.** This is
THE QUANTIFIER LAW verbatim: the invariant was written over the failure modes already
debugged instead of over the outcome. Pre-existing, not introduced by 04b-1 — but 04b-1 is
the packet chartered to close this class, and it will close two thirds of it and declare the
black hole shut.

---

## §P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| # | invariant | ∀-over-inputs or GUARDED | receipt |
|---|---|---|---|
| I1 | `blocks` emitted by BOTH paths, identically, ENFORCED/OVERWRITE/IN-OUT/no edge field | **∀** over generators — parametrised + a DERIVED equality pin | W11 → 15 RED; PROOF 3/5 redden the clause pins |
| I2 | the guard LANDS through `TaskLedger.ensure_ready` on a DIRTY store | **∀** over the production entry point (applies no DDL itself) | PROOF 3: `…LandsTheGuard::test_ensure_ready_on_a_DIRTY_store…` RED on clause deletion |
| I3 | re-emitting without `ENFORCED` silently un-guards | **∀** over clause states (both directions asserted in one test) | PROOF 3 declared-RED, fired |
| I4 | `create_task` **and** `create_many` are atomic | **∀** over both write verbs, pinned separately | W7 `relate_after` → 1 RED |
| I5 | edge set ≡ `blocked_by`, ∀ verbs | **∀** — AST exact-set over public async verbs + a forced fixture per verb | W8 `no_dedupe` → RED; verb set derived, not hand-listed |
| I5b | …∀ blocker id SHAPES | 🔴 **GUARDED** — only bare ids are ever ACCEPTED | **B-2**: W2 survives 80/80; perturbed pin RED-on-wrong / GREEN-on-correct |
| I6 | a create that closes a cycle is REFUSED | **∀** over the three reachable shapes + an acyclic control | W9, W10 each → 1 RED |
| I6b | the detector is right at every modulus | **∀** over cycle lengths 3/4/5 | X1 #12: the arithmetic accident reproduces on the reverse arrow (3 miss, 4 hit, 5 miss) |
| I7 | the read is the CLOSURE, dedupes, empty for leaf/isolated, RAISES for unknown | **∀** over graph shapes (diamond, leaf, isolated, absent) | W11 `reversed_edge` → 15 RED |
| I8 | the read is HONEST at its bound | 🔴 **GUARDED by an explicitly-supplied `max_depth=2`** (2 of 2 call sites) | **B-1**: W1 survives 80/80; perturbed pair RED-on-wrong / GREEN-on-correct |
| I8b | the bound ARGUMENT is itself bounded | 🔴 **NOT PINNED AT ALL** | measured: `max_depth=256` → raw `(unspecified rejection)`; `0` → `ids=[] truncated=True`; `-1` → raw store error |
| I9 | a phantom blocker is refused, naming EVERY one, in the exact sentence | **∀** over 4 phantom shapes × both verbs + multi-phantom + a real id | W6 → 3 RED |
| I10 | ONE row-existence implementation | **∀** over both directions of the generalisation (3 semantic mutations) | W6 → 3 RED; W12 `private_sender` → 1 RED |
| I11 | a cycle error is NOT an existence error | **∀** — derived from the raised values, not a name | holds on reference; W-F shape closed |
| I12 | `send` refuses a ghost SENDER, FIRST, in its own vocabulary | **∀** over 2 sender shapes (one wearing the registered prefix) | W13, W14 each → 1 RED |
| I13 | **"created, then unclaimable forever, silently" never happens** | 🔴 **GUARDED by two named causes** (phantom, cycle) | **B-3**: reached through a SUPERSEDED blocker, with a positive control |
| I14 | the cycle POLICY has one implementation | 🔴 **NOT PINNED** — `server.py::_find_key_cycle` keeps its own sentence + `ValueError` | §MP-4, §P6b |

---

## MISSING PINS (each is *the test that should exist* + *the defect it catches*)

### MP-1 — `test_a_chain_DEEPER_than_the_DEFAULT_bound_reports_TRUNCATED` (+ its within-bound twin)
*Catches:* B-1 — a build honest about truncation only when `max_depth` is supplied, serving a
silently short critical path on the DEFAULT path 04b-2 uses. **Written and proven (§P2).**

### MP-2 — `test_a_REAL_blocker_of_this_SHAPE_round_trips_through_the_transitive_read`
Parametrised over `dashed-uuid` / `all-numeric` / `dash-bearing`, ACCEPTED via
`create_many(ids=…)`, asserting `result.ids == [blocker_id]` **and** that `get_task(served_id)`
resolves. *Catches:* B-2 — an 8th hand-rolled `split(":")` decode. **Written and proven (§P2).**

### MP-3 — `test_an_OUT_OF_RANGE_max_depth_is_REFUSED_with_a_TEACHING_error`
Legs: `0`, `-1`, `>= ENGINE_RECURSION_CEILING`. *Catches:* a served surface that answers
`ids=[] truncated=True` for `max_depth=0` (nonsense) and leaks
`SurrealStoreError … (unspecified rejection); see the server log` for `max_depth=256` — the
engine's real *"Found 257 for bound but expected 256 at most"* withheld by the seam's error
hygiene. **Also removes a real under-specification:** my reference's usable ceiling is 255
because it probes at `max_depth+1`; a single-query build's is 256. Two "correct" builds
disagree about where the public API breaks, and no pin decides it.

### MP-4 — `test_a_key_CYCLE_refused_at_the_TOOL_seam_serves_the_LEDGER_vocabulary`
*Catches:* the ledger's new cycle guard becoming **copy #2 of a POLICY**. `server.py::AppContext`
already owns `_find_key_cycle` + its own sentence — `"create_many items contain a blocked_by
cycle among batch keys: a -> b -> a — a cyclic batch can never be claimed; break the cycle"`,
raised as a bare **`ValueError`**. After 04b-1 there are two cycle policies, two sentences and
two error classes, and the dispatcher's fires first, so a `lore_tasks` caller **never sees the
ledger's vocabulary**. Every cycle pin in the contract calls the ledger directly, so nothing
observes what an agent is actually served. L3 ruled exactly this for the *existence* policy and
the contract is silent for the *cycle* policy.

### MP-5 — `test_a_create_blocked_on_a_SUPERSEDED_task_is_REFUSED_or_the_blocker_is_ESCAPABLE`
*Catches:* B-3. ⚠ **This is a DESIGN fork, not a builder task — escalating, not settling it.**
Three readings: (a) refuse at create; (b) treat `superseded_by IS NOT NONE` as terminal in the
claim CAS; (c) declare it out of scope with a named re-open trigger. (b) is the smallest and
matches `supersede_task`'s own *"terminal-like"* docstring, but it changes a live claim gate.
**Operator's call.**

---

## §P2 — FIXTURE DISCRIMINATION (perturbed, with the correct-build control leg)

Perturbations live in a scratch COPY inside the scratch tree
(`loremaster/tests/test_p2_perturbations.py`), never in the repo. Each changes exactly ONE
fixture value.

| leg | perturbation | on CORRECT build | on WRONG build |
|---|---|---|---|
| P2a | `max_depth=2` **omitted**; chain `MAX+3` deep vs 3 deep | **2 passed** | `truncated_explicit`: **DEEPER leg FAILS**, within-bound leg passes |
| P2b | real blocker id shape → dashed-uuid / numeric / dash-bearing | **3 passed** | `split_decode`: **all 3 FAIL** |

```
##### A. REFERENCE (correct) build — the CONTROL leg:            5 passed in 1.31s
##### B. WRONG build truncated_explicit — P2a legs:              1 failed, 1 passed, 3 deselected
##### C. WRONG build split_decode — P2b legs:                    3 failed, 2 deselected
```

**⚠ My own P0 failure, self-caught, and it is the exact shape the role spec names.** My first
run of these perturbations put the file OUTSIDE the repo, so `asyncio_mode = auto` never
applied and every leg failed with *"async def functions are not natively supported"* — on the
correct build AND both wrong builds. Read as "5 failed / 3 failed / 2 failed", it looked like a
clean discrimination result. **It was a plugin error, not an assertion.** Only the
correct-build control leg exposed it. A probe that passes for the wrong reason green-lights a
broken finding just as surely as a broken pin green-lights a broken build.

### Fixture verdicts, individually

| fixture | verdict |
|---|---|
| `PHANTOM_TASK_IDS` (4 shapes) | **DISCRIMINATES on the negative side** — W-B (literal-keyed policy) genuinely dies. **BLIND on the positive side** → MP-2. |
| `branching_dag` (4 deep, branching, diamond) | **DISCRIMINATES.** Closure `{middle,left,right,root}` vs terminal `{root}`; W11 killed by it. Meets the packet's ≥3-deep-AND-branching floor. |
| cycle fixtures 3 / 4 / 5 | **DISCRIMINATES, and X1 independently confirms why**: on the REVERSE arrow the bare form hits at 4 and misses at 3 and 5. A 4-only fixture would pass a bare-idiom build. |
| `TestTheReadIsHONESTAtItsBound` pair (5-chain vs 3-chain, both `max_depth=2`) | **DISCRIMINATES on the hard-coded-constant axis; BLIND on the supplied-vs-defaulted axis** → MP-1. |
| `dirty_task_store` (task rows + a pre-existing dangling edge) | **DISCRIMINATES.** Realistic pre-04b-1 state; the BASELINE leg proves the old world is genuinely un-guarded. |
| `task_ledger` (asserts all four phantoms ABSENT) | **DISCRIMINATES** for the negative legs. Its one real `blocker_id` is ledger-minted bare hex — the monoculture behind MP-2. |
| `agent_and_task_ledgers` (both families, ONE database) | **DISCRIMINATES.** W6 and W12 both die on it; one database is what lets "the shared thing changed" be told from "two things changed". |
| `UNREGISTERED_SENDER_IDS` (2 shapes, one wearing the registered prefix) | **DISCRIMINATES** against prefix/length/literal-keyed refusals. |
| `_seed_chain` / `_seed_cycle` (RAW-seeded) | **DISCRIMINATES**, and correctly raw — a detector testable only through the guard that prevents the condition is untested. |
| `test_the_refusal_NAMES_EVERY_phantom` (3 phantoms + 1 REAL, unsorted) | **DISCRIMINATES** against first-miss-only, against ENFORCED-leaning builds, and against refuse-the-list-unexamined. |
| `_served_task_refusal` (by VALUE, not derived) | **DISCRIMINATES.** Correctly not derived from production's formatter — that would be a tautology. |

---

## §X2 — THE THREE OWED OBLIGATIONS, DISCHARGED

### 1. PROOF 5 — EXECUTED, both legs, EXIT=0

```
############ PROOF 5a — refers IN/OUT swap ############
mutation LANDED (anchor matched exactly once) in loremaster/loremaster/store/surreal_schema.py
4 failed, 62 passed in 3.90s
tree restored byte-exact (…surreal_schema.py: md5 dc5dc6f18eb6dc87dbb8cd8d26df417d)
PROOF HELD — the declared RED set fired EXACTLY
PROOF5a EXIT=0

############ PROOF 5b — answers_to IN/OUT swap ############
… PROOF HELD … PROOF5b EXIT=0
```

**⚠ FINDING IN THE PROOF 5 BLOCK ITSELF.** My first attempt declared only the block's stated
node id and came back `PROOF FAILED / EXIT=4` with three unexpected reds — the contract's own
three already-RED `blocks` declaration pins. **PROOF 3's and PROOF 4's blocks both say
"+ this contract's three already-RED `blocks` declaration pins". PROOF 5's does not.** A
builder running PROOF 5 verbatim gets a FAILED verdict and is one step from "fixing" it by
editing the declared list — the exact anti-pattern `mutation_proof.py` exists to prevent.
**One-line fix: add the same clause to the PROOF 5 block.**

### 2. PROOF 3 — RE-RUN UNPIPED, exit captured separately

```
mutation LANDED (anchor matched exactly once) in loremaster/loremaster/store/surreal_schema.py
12 failed, 54 passed in 3.54s
tree restored byte-exact (…surreal_schema.py: md5 dc5dc6f18eb6dc87dbb8cd8d26df417d)
PROOF HELD — the declared RED set fired EXACTLY: [ …12 ids… ]
==========================================
PROOF 3 SHELL EXIT (UNPIPED, captured separately) = 0
```

The author's claim reproduces independently, **including the new `ack` leg**
(`…SOLEDecisionPoint::test_MUTATION_neutralising_the_shared_policy_lets_ack_reach_the_ENGINE`),
which the author added to close 04a residual R-1. The md5 matches the author's reported value
exactly, so the tree the author proved against and the tree I proved against are the same tree.

### 3. R-e — CONFIRMED REAL, and WIDER than the residual states

`test_surreal_store.py::test_the_whole_schema_migrates_an_existing_populated_store` applies:

```python
ddl_slices = (generate_ddl(dim=_MIGRATION_DIM), generate_graph_ddl(),
              generate_agent_ddl(), generate_brief_ddl())
```

Derived from the production emitter, the four relation-edge emitters today are
`BRIEFED_RELATION`, `TO_RELATION`, `REFERS_RELATION`, `ANSWERS_TO_RELATION`. Cross-referencing:

| edge | guarded? | emitted by | in the pin's slices? | edge ROW seeded? |
|---|---|---|---|---|
| `briefed` | ENFORCED | `generate_brief_ddl` | ✅ | ✅ (`via` asserted to survive) |
| `to` | ENFORCED | **`generate_message_ddl`** | ❌ **ABSENT** | ❌ |
| `refers` | deferred | `generate_graph_ddl` | ✅ | ❌ |
| `answers_to` | deferred | `generate_graph_ddl` | ✅ | ❌ |
| **`blocks`** (04b-1) | ENFORCED | `_task_statements` → rides `generate_ddl` | ✅ **applied** | ❌ |

So the residual is real in **two distinct ways**: (i) `generate_message_ddl` is missing, so
`to` — a guarded edge — is never migrated by the repo's only whole-schema migration pin; (ii)
`blocks` WILL be applied but no `blocks` edge row is seeded, so the row-survival property the
04b-1 contract pins for `blocks` in isolation is untested in the whole-schema path.
**Fix, still "one line plus a seed row":** add `generate_message_ddl()` to `ddl_slices`; seed a
`message` row + a `to` edge and a second `task` row + a `blocks` edge; assert both survive.

---

## §X3 — THE SATISFIABILITY RECEIPT

A full known-correct reference build: `BLOCKS_RELATION` + `_define_relation_table(…,
enforced=True)` inside `_task_statements`; `agent_existence` generalised to
`UnknownRowError` / `format_unknown_row_refusal` / `reject_unknown_rows` with
`reject_unknown_agents` and `format_unknown_agent_refusal` as thin DELEGATING adapters (the
04a sentence byte-identical); `tasks.py` gaining `TASK_BLOCKER_MAX_DEPTH`,
`TransitiveBlockers`, `UnknownBlockerError`, `TaskCycleError`, an atomic `create_task`, a
mirroring `create_many`, the column-walking cycle guard and `transitive_blockers`;
`messages.py` gaining `UnknownSenderError` + a sender check that routes through the shared
policy, ordered FIRST.

```
$ uv run pytest -q -n 8 loremaster/tests/test_blocks_edge.py -k "<sections A-H>"
80 passed in 4.31s
```

**The harder leg — still satisfiable after the cleanups the lint demands:**

```
$ uv run ruff check --fix .        # reorganised the imports my patch added
$ uv run pytest -q -n 8 …          80 passed in 3.98s
$ ./scripts/typecheck.sh           lorerunes OK · lorescribe OK · loresigil OK · loremaster OK (171 files) · skills OK
```

**No pin is RED on a correct build.** The one remaining `ruff` complaint is `E501` on a long
string literal my *patch generator* emitted, not a contract constraint.

### ⚠ The contract killed my first reference build — as designed

My first `create_many` emitted `CREATE_0, RELATE_0, CREATE_1` and
`test_the_mirror_holds_after_create_many_including_a_FORWARD_reference` failed with
`statement 3 of 5 was rejected` — the RELATE's `in` endpoint not yet created. That is the
exact wrong build the pin's docstring names. **Strong pin; it caught a real builder mistake
on its first live use.**

### §X-Rb — residual R-b MEASURED (it was "UNMEASURED, pinned anyway")

Restructuring to all-CREATEs-then-all-RELATEs made the pin pass. So on 3.2.1:
**`ENFORCED` DOES resolve an `in` endpoint created EARLIER in the same uncommitted
transaction.** R-b's STOP condition does not fire; the pin is satisfiable; the builder needs
no escalation. The constraint it imposes is real and should be written down: **all CREATEs
must precede all RELATEs in the composed transaction.**

---

## §P6b — INDEPENDENT REMOVED-BEHAVIOUR ENUMERATION, THEN THE DIFF

Enumerated from `tasks.py` / `server.py` source **before** opening the packet's inventory.

| # | behaviour 04b-1 removes or changes | in the packet's inventory? | verdict |
|---|---|---|---|
| 1 | `create_task` is a bare `_query`, not a transaction | ✅ yes | agreed |
| 2 | `blocked_by` is FAIL-OPEN at write | ✅ yes | agreed, pinned |
| 3 | `supersede_task` drops the predecessor's dependencies | ✅ yes | agreed, pinned as old-behaviour-preserved |
| 4 | **`server.py::_find_key_cycle` becomes copy #2 of a POLICY** (own sentence, own `ValueError`, fires FIRST at the tool seam) | ❌ **MISSING** | 🔴 **finding → MP-4** |
| 5 | **`create_task`'s docstring has NO `Raises:` section**; it gains two error classes. `create_many`'s says `ValueError` only | ❌ **MISSING** | 🔴 the #219 class, a **second and third site** inside the same packet — the contract names only `_reject_unknown_recipients` |
| 6 | **`create_task` goes from ONE round trip to ≥2 (+N for the cycle walk)** | ❌ **MISSING** | 🔴 E-4 states the send-path extra trip as an ACCEPTED COST; the same cost on the **create** path is stated nowhere. Rider asymmetry. |
| 7 | `create_task`'s rejection error TEXT changes (`run_query`'s *"task query rejected"* → `execute_transaction`'s *"statement N of M was rejected"*) and its retry seam changes with it | ❌ **MISSING** | 🟡 a served-surface change; low harm, but unadjudicated |
| 8 | `_reject_unknown_recipients`' name/docstring become inaccurate | ✅ yes, named in the contract | agreed |

**Diff verdict: 3 of my 8 items are in the inventory; 4 are missing (one of them, #4, is a
`ONE IMPLEMENTATION` violation); 1 is named.**

---

## §P-PKG — MY TABLE, BUILT FIRST, THEN DIFFED

| mechanism | libraries I evaluated | what I **READ** | my verdict | author's | diff |
|---|---|---|---|---|---|
| transitive closure over a DAG | SurrealDB `@.{n..m+collect}`; `networkx.descendants` | **my own X1 live measurement** of `<-blocks<-` on 3.2.1 (15 properties) + probe §5.1 + spec `path_collect.surql` | **replace** (engine) | replace (engine) | ✅ agree |
| cycle detection over persisted ids | engine self-reach (`node ∈ its own +collect reach`); `networkx.simple_cycles`; in-house `_find_key_cycle` | probe §5.4; the contract's `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED` fixture; `server.py::_find_key_cycle` source | 🔴 **CONFLICT — escalated** | "replace with the engine operator" | ❌ **DISAGREE** |
| row-existence policy | in-house `loremaster.agent_existence` | the module source; `reject_unknown_agents` / `format_unknown_agent_refusal` signatures | **reuse via generalisation** | reuse via generalisation | ✅ agree |
| retry / backoff / error classification | `tenacity`; in-house `loremaster.store._txn` | `_txn.run_query` / `execute_transaction` / `retry_on_conflict` | **keep_with_trigger** (trigger: a second retry policy appearing outside `_txn`) | not surveyed | ➕ mine |
| edge DDL emission | in-house `_define_relation_table` | its source (OVERWRITE rationale, `enforced_clause`) | **keep** — one emitter, five callers | not surveyed | ➕ mine |

### MP-4a — the cycle-detection conflict, stated precisely (escalation)

The author's package verdict says *"replace with the engine operator"*, citing probe §5.4's
self-reach detector. **The contract's own fixture makes that operator structurally unable to
detect the case it pins.** In
`test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED` the closing
dependency is written **column-only**:

```python
await run(setup, f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $blocked_by",
          {"id": chain[0], "blocked_by": [new_id]})
```

No `blocks` edge exists for that link — **and none can**, because `new_id` does not exist yet
and `ENFORCED` would reject the RELATE. So the fixture is *forced* into a column-only write by
the very guard this packet adds, and any engine-traversal detector returns "acyclic".
Measured: W9 `edge_cycle` fails exactly this one pin.

**Consequence the contract does not state:** the write-time cycle guard MUST walk the
`blocked_by` COLUMN, client-side — which is the right answer (the column is what the claim CAS
reads, so a column cycle is what makes a task unclaimable) but is the OPPOSITE of the
"engine over hand-rolling" verdict in the author's own package table, and the opposite of what
`TestACycleIsDetectedOverPERSISTEDIds`' docstring teaches (*"the working acyclicity detector is
the +collect self-reach"* — true of the READ, false of the write-time GUARD).
**A builder will build the engine detector, fail one pin, and have no sentence explaining why.**
Fix: state it in the class docstring and correct the package-table verdict to
`bespoke (engine cannot see a column-only dependency; minimal surface: a DFS over the column,
the closure read stays on the engine)`.

---

## §P7 — RED HONESTY (reproduced, with counts)

Pristine production (`surreal_schema.py` md5 `dc5dc6f18eb6dc87dbb8cd8d26df417d`), tests at `98d5084`:

| run | measured | author's claim | verdict |
|---|---|---|---|
| `test_blocks_edge.py` sections A–H | **72 failed, 8 passed** | 72 failed, 8 passed | ✅ exact |
| `test_blocks_edge.py` Section I (#253) | **3 failed, 11 passed** | "14 pins (3 RED, 11 regression)" | ✅ exact |
| `test_blocks_edge.py` whole file at HEAD | **75 failed, 19 passed** | — | ✅ consistent (72+3, 8+11) |
| `test_enforced_relations.py` + `test_derivation_source_unification.py` | **3 failed, 70 passed, 19 skipped** | 3 failed, 70 passed, 19 skipped | ✅ exact |
| `test_query_tasks_bounded.py` (UNTRACKED) | **2 failed, 19 passed** | — | see §0 |

**RED for the RIGHT reason, proven the strongest available way:** the reference build turns
those same 72 GREEN with zero failures. Not an import typo, not a fixture error, not a path.

**⚠ Note on the untracked addendum:** 2 RED of 21 pins. A file whose stated purpose is *"the
pins SECTION I does not have"* is **90% already-green**. Not a defect on its face (regression
pins are legitimate), but a low RED ratio for an artifact claiming to close four holes, and
worth the lead's eye when deciding its fate.

---

## §P5 — CAN THE TEST DOUBLES FAIL?

Sections A–H drive **real ledgers against a real store** end to end; the only substitutions
are `monkeypatch` mutation points. `_accept_everything` is correctly an **accept-everything
stub, never a raising sentinel** — 04a measured that a raising sentinel proves only that a
function is CALLED, never that it DECIDES. **Proven able to fail:** W6 `private_copy` reddens
exactly the three neutralising legs, and W12 `private_sender` reddens the sender leg. The
`_Ref` double is a 12-line id/name pair with no behaviour to bless. **No fake blesses its
implementation here.**

---

## §P3 — BRANCH REACHABILITY (each branch, the pin that would fail if deleted)

| branch the build will have | pin that dies if deleted | verdict |
|---|---|---|
| `blocked_by` empty (`None` **and** `[]`) → no RELATE, no txn | `test_an_EMPTY_dependency_list_is_ACCEPTED_and_writes_NO_edge[None/[]]` | ✅ reached, both spellings |
| ≥1 blocker → RELATE per deduped id | `test_the_mirror_holds_after_create_task[1/3]` | ✅ |
| duplicate blocker → collapse | `test_the_mirror_holds_after_create_task_with_a_DUPLICATE_blocker` | ✅ |
| batch-sibling id treated as existing | `test_the_mirror_holds_after_create_many_including_a_FORWARD_reference` | ✅ |
| existence miss → refuse naming ALL | `test_the_refusal_NAMES_EVERY_phantom_not_just_the_FIRST` | ✅ |
| cycle → refuse (intra-batch / self / persisted) | the three `TestCreateRefusesToFormACycle` legs | ✅ |
| traversal truncated at the bound | `test_a_chain_DEEPER_than_max_depth_reports_TRUNCATED` | 🔴 **only via an explicit `max_depth`** → MP-1 |
| traversal complete | `test_a_chain_WITHIN_max_depth_reports_truncated_FALSE` | 🔴 same → MP-1 |
| `max_depth` out of range | — | 🔴 **NO PIN** → MP-3 |
| unknown task id → raise | `test_an_UNKNOWN_task_id_raises_TaskNotFoundError` | ✅ |
| sender miss → refuse first, own class | `test_a_BAD_sender_and_a_BAD_recipient_refuse_on_the_SENDER_FIRST` | ✅ |
| id-decode branch (`RecordID` vs `str`) in `_bare_id` | — | 🔴 **str branch never exercised with a bracket-rendered id** → MP-2 |
| **UNREACHABLE THROUGH THE REAL ENTRY POINT, honestly:** the ledger's cycle vocabulary for an intra-batch KEY cycle — `server.py::_find_key_cycle` fires first | — | 🔴 → MP-4 |

---

## RESIDUALS — every item, its own line, its own verdict

| # | item | verdict |
|---|---|---|
| R-1 | **The target moved mid-audit** (2666 → 3241 lines + an untracked 21-pin sibling; two parallel authors) | 🔴 **ESCALATED, §0.** My verdict covers sections A–H fully; Section I and the addendum got RED-honesty only. Re-run an adversary pass on whichever #253 artifact survives. |
| R-2 | **PROOF 5's block omits the "+ three already-RED `blocks` pins" clause** that PROOF 3's and PROOF 4's carry | 🔴 **REAL, one-line fix.** Verbatim execution yields `PROOF FAILED / EXIT=4`; reproduced. |
| R-3 | Author's R-b ("unmeasured, pinned anyway") | ✅ **MEASURED AND CLOSED** (§X-Rb). `ENFORCED` resolves an `in` endpoint created earlier in the same txn. Constraint to write down: all CREATEs before all RELATEs. |
| R-4 | Author's R-e (`test_surreal_store.py` migration gap) | 🔴 **CONFIRMED AND WIDER** (§X2.3): `generate_message_ddl` absent ⇒ `to` never migrated; no edge row seeded for `blocks`. |
| R-5 | Author's R-a (concurrency unpinned; two racers form a cycle neither sees) | 🟡 **AGREE it is not a contract pin.** Note it is the SAME TOCTOU my B-3 door widens: my reference's cycle walk is N client-side reads outside the txn. Needs a measurement task. **Operator's call.** |
| R-6 | Author's R-f (#248, seven `_bare_id` copies, `tasks.py` among them) | 🔴 **UPGRADED TO A MEASURED BLOCKER** — B-2 / MP-2. The author named the risk and did not pin it. |
| R-7 | Author's R-l (five named non-existent production symbols as mutation points) | ✅ **CORRECT AND WELL-HANDLED.** Every one failed CLOSED in my builds; renaming costs one edit in the documented constants block. |
| R-8 | Author's R-m (`BLOCKS_RELATION_NAME` a scaffold literal, not an import) | ✅ **CORRECT** (#133: an import of a non-existent name makes three files uncollectable rather than RED), and held equal by a pin. |
| R-9 | Author's R-n / #253 (`query_tasks` unbounded read) | 🟡 **NOW IN SCOPE** via Section I + the addendum; **not graded by me** beyond RED honesty. §0. |
| R-10 | Author's R-c / R-d / R-o (`str.replace` count, bare-`;` split, `_REQUIRED_GUARDS`) | ✅ **CONCUR, not triggered.** I re-derived R-o: my reference's `blocks` clause satisfies `TABLE (RELATION) → OVERWRITE` by construction, and the tree-wide guard stayed green. |
| R-11 | Author's R-g / R-h (`_BRIEF_NAME="project"` and `via=` monocultures, 04a) | 🟡 **STILL OPEN, untouched, correctly outside this contract's writable set.** Named so they are not lost. |
| R-12 | Author's R-i (`brief_ack` tool-seam teaching pin) | ✅ **CORRECTLY ROUTED to 04b-2** (its R-12). Not 04b-1's. |
| R-13 | Author's R-j / R-k (proofs unexecuted; PROOF 3 piped) | ✅ **DISCHARGED BY ME** — §X2. PROOF 1 and 2 remain un-runnable until the build lands, correctly. |
| R-14 | `create_task` / `create_many` docstring `Raises:` sections | 🔴 **#219 class, sites 2 and 3 in this packet, unadjudicated** — §P6b #5. |
| R-15 | `create_task`'s round-trip count 1 → ≥2 (+N) | 🔴 **UNSTATED COST.** E-4 states the equivalent for `send`; the create path has no such sentence. §P6b #6. |
| R-16 | `create_task`'s rejection error TEXT and retry seam change with the txn conversion | 🟡 **UNADJUDICATED**, low harm. §P6b #7. |
| R-17 | `PHANTOM_TASK_ID_NATIVE_SHAPE = "0"*32` is described as *"the shape TaskLedger itself mints"* | 🟡 **MINOR PROSE INACCURACY.** All-zeros is all-DIGITS, so it renders `task:⟨…⟩`; a real `uuid4().hex` almost never does. The comment teaches the wrong lesson about which shape is bracketed. |
| R-18 | The scratch tree `/home/ejprice/scratch/adv04b1-ref` holds my reference build | 🟡 **DISPOSITION NEEDED.** It is a working 04b-1 reference implementation the builder could diff against. Keep or delete — **your call**; I have not deleted it. |
| R-19 | X1's three self-caught probe failures | ✅ **DISCLOSED IN FULL** (§X1). Two would have produced a false BLOCKING finding about the reverse arrow. |
| R-20 | `TestTheReadIsBOUNDEDByTheCallersFilter` etc. (Section I) fixtures | 🟡 **NOT GRADED.** Declared, not assessed. §0. |

---

## WHAT I COULD NOT BREAK (so the strength is on the record)

I attempted and **failed** to defeat: the both-paths derived-equality pin · the
statement-ORDER pin · the `OVERWRITE` pin · the un-enforcing-door pin · the
`ensure_ready`-only migration pins (W-A) · the atomicity pins (W-D) · the dedupe pin · the
forward-reference pin (which killed my own first reference build) · the exact-set AST verb
adjudication · the three cycle-refusal legs and their 4-deep positive control · the
closure/dedup/isolated/unknown read pins · all three sharing mutations (W-E, both directions)
· the served-refusal-by-VALUE pin · the derived error-hierarchy pins · all four #247 legs.
**Eleven of fourteen code mutations died, `reversed_edge` under fifteen simultaneous reds.**
The three survivors are one shape — *an invariant conditioned on the one input value its
author exercised* — and every one is closed by a fixture, not by a redesign.

---

# VERDICT: **CONTRACT INSUFFICIENT**

Three wrong builds pass the contract, each reproduced against a known-correct control:
**B-1** (`truncated` honest only on the explicitly-bounded path — 80/80), **B-2** (an 8th
hand-rolled id parse — 80/80), **B-3** (R3's own harm through a superseded blocker — no pin
exists). Five missing pins are named above with the defect each catches; **MP-1 and MP-2 are
written and proven RED-on-wrong / GREEN-on-correct** and can be lifted verbatim. **MP-5 is a
DESIGN fork and an operator escalation, not a builder task.** Add MP-1 through MP-4, rule on
MP-5, fix PROOF 5's declared-set clause and R-e, and this becomes one of the stronger
contracts this repo has produced.
