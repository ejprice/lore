# REPORT-fixwave-04b1-close — the two in-wave items the 04b-1 cold audit left

brief-base v8 read
brief project v7 read
comms: registered `fixwave-04b1-close` (session `pkt04b-20260728`, role builder, model
claude-opus-5, task `e48347a9020945efb5725e16ae1e73c3`) — the register call re-acked brief
`project` v7.

**CAPABILITY CHECK (brief-base v8 §4) — NO GAP.** Everything the brief demands was reachable:
`lore_comms` / `lore_findings` / `lore_get_symbol` / `lore_impact` loaded via ToolSearch and
answered; `scripts/typecheck.sh`, `uv run ruff`, `uv run pytest -n auto` all ran; the test store
(spike-surreal `ws://127.0.0.1:18000`) accepted the live probe. One thing the brief assumed that
was NOT true, reported rather than worked around silently: it named my task id, and brief-base §5
says to drive my own row — but `lore_claim_task` returned *"already held by `lead-pkt04b`
(status in_progress)"*, so the row is the LEAD's, not mine, and per §5 I touched the board no
further. If the lead intended me to own it, the row must be released first.

**`trust hard-definition read`** — `CLAUDE.md` § THE CONSUMER LAW → *TRUST — THE HARD DEFINITION*.
Both askable questions, verbatim:
- Leg 1 — ***"what question did I actually answer, and is it the one the consumer thinks they
  asked?"***
- Leg 2 — ***"what broken state of this tool would serve exactly these bytes?"***

---

## SUMMARY BLOCK

- state: **done** — both items fixed; no scope growth; git state untouched (lead commits).
- **Item 1 (#275) — FIXED, and the audit's own suggested wording was REJECTED as measurably false.**
- **Corrected predicate, verbatim as it now stands in the file:** *"the tasks reachable UPSTREAM
  over **EVERY `blocks` EDGE THIS LEDGER HOLDS**, from this task, to a depth of at most
  `max_depth_used`, **at this ledger**, as of this read."* — followed by the provenance as a FACT:
  three mint sites (the `ensure_ready` backfill; `create_task`/`create_many`, in the same
  transaction as the row), zero production delete sites.
- **What would falsify it:** (i) a fourth `blocks` mint site, or ANY production delete of a
  `blocks` edge or `task` row; (ii) a create SUCCESS path writing `blocked_by` with no edge;
  (iii) an out-of-band writer — which falsifies the PROVENANCE clause, not the predicate. (i) and
  (ii) checked and absent at `af3551c` (§1.3); (iii) is a stated bound, not a hole.
- deviations: **none to the writable set.** ⚠ `REPORT-contractfix-04b1-r6.md` was already dirty in
  the working tree when I started (it is in the session-start `git status`) — NOT my edit.
- Item 2 (#272) — FIXED: `[[tool.mypy.overrides]]` for `networkx`/`networkx.*` in the root
  `pyproject.toml`, inline `# type: ignore[import-untyped]` deleted, comment kept and re-pointed.
  MUTATION-PROVEN load-bearing (§2.2).
- `Packages considered:` **networkx** — READ: `loremaster/pyproject.toml` `[dependency-groups] dev`
  (it is a DEV dep since `f0f4561`) + the three `[[tool.mypy.overrides]]` precedents in the root
  `pyproject.toml` (astroid, kubernetes, lorescribe.astroid_parse) → verdict **keep_with_trigger**
  (trigger: if `types-networkx` is ever added to the dev group, DELETE the override — never keep
  both; written into the override's own comment). No mechanism was built or specified.
- **Gates, unpiped, exits captured: `scripts/typecheck.sh` exit 0 ("no issues found", all five
  members) · `uv run ruff check .` exit 0 ("All checks passed!") · `uv run pytest -q -n auto`
  over the three named files exit 0 — `487 passed in 11.69s`, 0 failed.**
- findings: **#275 resolved · #272 resolved · #277 FILED** (new: the audit's suggested fix for #275
  was itself false — measured; supersedes-links #275).
- decisions-needed: none blocking. One judgement call for the lead in §4 R-1 (two archived reports
  carry the false suggested wording in prose).
- receipts: §1.2 (the six-step live measurement) · §1.3 (the derivation + the lore_impact
  cross-check) · §2.2 (the mypy mutation proof + byte-exact restore) · §3 (gate tails).

---

## 1. Item 1 — finding #275, LEG-1 row 1's predicate

### 1.1 What was wrong, and what the third version had to survive

At `af3551c` the row's predicate named the edges *"this ledger's last completed `ensure_ready`
**mirrored**"*. On a virgin store that set is EMPTY and the read still answers non-empty, so the
row named a strict SUBSET of what the response is true of — and, as the cold audit put it, thereby
asserted the INVERSE of the edge ≡ column invariant SECTION K pins. That was version **2**;
version **1** said the difference was *"CLOSED"*. Both were written by an agent that had just
measured its predecessor false.

**So before writing version 3 I stated what would falsify it and checked those cases — and the
first casualty was the wording #275 and the r6 adversary both recommended:**

> *"...over the `blocks` edges this ledger holds — every `blocked_by` column the **LAST** completed
> `ensure_ready` mirrored, plus every dependency written **SINCE** — at this ledger, as of this
> read"*

**That is false one reboot later**, and I measured it rather than argued it (§1.2 step [4]):
`_backfill_blocks_edges` is idempotent against the STORE's edge set (it mints `wanted - existing`),
so a second boot over an unchanged store mirrors **0** columns, nothing is written **since** it, and
`transitive_blockers` still serves the edge minted before it. Both legs of the suggested form name
the empty set while the response is non-empty — the same defect it was correcting, one boot out.
**Root class: ANY predicate for this row indexed on *the last* `ensure_ready` is false again on the
next boot**, because the edge set is CUMULATIVE and the backfill is idempotent. Filed as **#277**.

### 1.2 The live measurement — six steps, one virgin database (CONSTRUCTED, not reasoned)

Run 2026-07-29 against the TEST store `ws://127.0.0.1:18000` on `test_<pid>_<uuid4>`, through the
suite's own harness constants (loaded from `loremaster/tests/_surreal_harness.py` by path, never
re-typed). Provenance receipt printed by the probe:
`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`
(the real tree — no scratch copy was made; the repo was not mutated by the probe).

```
database = test_673157_2ebb383e2f3048e08dd8e3b66465a7eb (VIRGIN)
[1] edges after the FIRST ensure_ready (the backfill): 0
[2] edges after ONE post-boot create_task dependency: 1
[3] transitive_blockers(dependent) -> ids=['fef8f46001504b46bd7c81a0128d89cf'] truncated=False max_depth_used=32
[3b] the id it served IS the post-boot blocker: True
[4] edges after a SECOND ensure_ready: 1
[4b] transitive_blockers still serves it: ids=['fef8f46001504b46bd7c81a0128d89cf']
[5] with every blocks edge DELETED: ids=[] truncated=False
[6] after ensure_ready re-mirrors the column: ids=['fef8f46001504b46bd7c81a0128d89cf']
```

- **[1]+[3] re-derive #275's measurement independently** (0 mirrored, non-empty answer) — I did not
  inherit the audit's number.
- **[4] kills the suggested form** (§1.1).
- **[5] is the positive control** the earlier passes did not print: with the columns intact and the
  edges gone, the read serves `ids=[] truncated=False`. That proves the predicate's operative clause
  is *over the EDGES* — and it is sidecar **S3**'s confident lie, constructed.
- **[6]** shows the backfill re-mirroring from the column, which is what makes difference (a) a
  difference-that-closes rather than a permanent divergence.

### 1.3 The derivation behind the new provenance clause (two independent instruments)

The new row states the mint/delete doors as a fact, so the doors were ENUMERATED, at `af3551c`:

- **grep** (a sanctioned fallback, SAID OUT LOUD per the dogfood protocol — case (a),
  rename/exhaustiveness where one missed site falsifies the prose): `_relate_fragment` is called at
  `_backfill_blocks_edges`, `create_task`, `create_many` and nowhere else; `BLOCKS_RELATION` appears
  in production only in the mirror-state read, the `RELATE`, and the traversal; no `DELETE` anywhere
  under `loremaster/loremaster/` names `blocks` or `task`; no `.delete(`/`.remove(` touches either;
  `TASK_TABLE` appears outside `tasks.py` only in the schema DDL.
- **lore_impact** (`loremaster.tasks.TaskLedger._relate_fragment`) — used FIRST for the structure
  question and it agrees exactly: `verdict: live`, `3 prod / 0 test references`, consumers
  `_backfill_blocks_edges`, `create_many`, `create_task`. Its own astroid-bounds caveat is why the
  grep leg exists beside it rather than instead of it.

`lore_get_symbol` served the authoritative `transitive_blockers` body (`loremaster/loremaster/
tasks.py`), which confirms the read rides `<-blocks<-task` and that the helper's OWN docstring
already scoped itself correctly — the defect was only ever in the contract's Leg-1 table.

### 1.4 The edit

`loremaster/tests/test_blocks_edge.py`, module docstring, LEG 1:

1. **Row 1's predicate** replaced (verbatim text in the SUMMARY BLOCK), plus a provenance sentence
   naming the three mint sites, the zero production delete sites, and — explicitly — that this
   contract's OWN fixtures do delete edges, to construct the edge-less world. The derivation is
   dated and SHA'd in place (`DERIVED 2026-07-29 at af3551c`), per brief-base §1: a retrieved chunk
   arrives without its header.
2. **The row's second defect** (its commentary misquoting its own predicate as *"a COMPLETED
   migration"*) rewritten: the predicate now *names the BACKFILL as the door the LEGACY edges come
   through*, and the ⚠ clause keeps difference (a)'s partial/swallowed-migration warning, now
   carrying step [5]/[6]'s measurement instead of an appeal to a phrase that was not there.
3. **A new ⚠⚠ paragraph above the table** records that version 2 was false (#275), that the fix is
   version 3, and WHY it is shaped as it is — *any predicate indexed on the last `ensure_ready` is
   false on the next boot* — so version 4 is not written by someone re-deriving from the same
   report prose. Differences (b), (c), (d) and every other row are untouched.

Nothing about the production code changed, and nothing about what the suite ASSERTS changed. **Two
claims, kept apart because only one of them is mine to make:** (i) 487 passed / 0 failed AFTER the
edits — measured, §3; I did NOT run the gate before editing, so "before" is the lead's green at
`af3551c`, inherited, not re-derived by me. (ii) No pin reads this MODULE docstring — checked, not
assumed: every `__doc__` assertion in the file targets a helper or a `TaskLedger` method
(`transitive_blockers`, `create_task`, the verb sweep), never `__doc__` of the module.

---

## 2. Item 2 — finding #272, the networkx house idiom

### 2.1 The edit

- Root `pyproject.toml`, beside the astroid / kubernetes / `lorescribe.astroid_parse` precedents:
  `[[tool.mypy.overrides]] module = ["networkx", "networkx.*"] / ignore_missing_imports = true`,
  with a comment scoping it honestly — networkx is a **DEV** dependency of the `loremaster` member
  (`f0f4561`, after the stage-2 adversary caught the runtime placement) and a **TEST-SIDE ORACLE**
  only; production imports it nowhere, so nothing served is typed by the relaxation. The comment
  also carries the re-open trigger: if `types-networkx` is ever added, DELETE this block rather than
  keep both.
- `loremaster/tests/test_blocks_edge.py::TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST.
  _independent_cycles` — the inline `# type: ignore[import-untyped]` is gone; the explanatory
  comment is KEPT (per brief) and now points at the override, naming why an inline ignore may not
  co-exist with it (unused-ignore reporting is on under `strict`).

### 2.2 Mutation proof — the override is load-bearing, not decoration

Content-backed up first (standing law for mutating an uncommitted tree), mutated, restored, and the
restore proven byte-exact:

```
md5 before/after: 1a07405de9e14968fd84e57cde8fb259 (pyproject.toml == the content backup)

MUTATION APPLIED: networkx override removed
MUTATED_TYPECHECK_EXIT=1
loremaster/tests/test_blocks_edge.py:7900: error: Library stubs not installed for "networkx"  [import-untyped]
loremaster/tests/test_blocks_edge.py:7900: note: Hint: "python3 -m pip install types-networkx"
Found 1 error in 1 file (checked 171 source files)
```

With the block present: exit 0. **Expected-RED set declared before the run** (exactly the networkx
import site, exactly one error) and the observed set matched — the direction that also catches a
mutation landing in dead code. This is what distinguishes "I added an override" from "the override
does the thing the finding said it would".

---

## 3. Gates — unpiped, exits captured, counts in the tail

```
$ ./scripts/typecheck.sh                      -> TYPECHECK_EXIT=0
Success: no issues found in 3 source files     / typecheck: lorerunes OK
Success: no issues found in 27 source files    / typecheck: lorescribe OK
Success: no issues found in 35 source files    / typecheck: loresigil OK
Success: no issues found in 171 source files   / typecheck: loremaster OK
Success: no issues found in 12 source files    / typecheck: skills OK

$ uv run ruff check .                          -> RUFF_EXIT=0
All checks passed!

$ uv run pytest -q -n auto loremaster/tests/test_blocks_edge.py \
      loremaster/tests/test_query_tasks_bounded.py loremaster/tests/test_task_ledger.py
487 passed in 11.69s                           -> PYTEST_EXIT=0
```

The expected state was 0 failed and it is 0 failed. **There are 0 failing tests in the scope I was
given; I did not run the full suite (brief-base §3 forbids it unless briefed), so I make no claim
about the rest of the tree.**

`git status` at the end: `M loremaster/tests/test_blocks_edge.py`, `M pyproject.toml`, and the
pre-existing `M REPORT-contractfix-04b1-r6.md` that was dirty before I started. No git state was
mutated.

---

## 4. RESIDUALS — one line each, my own verdict

- **R-1 (for the lead, one judgement call).** `REPORT-adversary-04b1-r6.md` §LEG1 and
  `REPORT-coldaudit-04b1.md` §4 both print the SUGGESTED true form that #277 measures FALSE; when
  they are `git mv`'d into `receipts/`, a one-line header saying so costs nothing and stops a future
  retrieval adopting version 2.5. I did not edit either report — they are other agents' records.
- **R-2 (bound, not a hole).** The new row's provenance clause is a claim about THIS codebase at
  `af3551c` (three mint sites, no production delete); an out-of-band writer touching the store
  directly would falsify the clause but NOT the predicate, which is over the edges the ledger HOLDS.
  Stated here rather than hedged in the row.
- **R-3 (Leg 1's own stated bound, unchanged).** Everything in §1 is a claim about what the code
  SAYS plus one CONSTRUCTED run of what it DID; time, environment and predicate-as-EXECUTED remain
  BELIEVED, not known (#24 · #107 · #131 · #139). I did not run the packet's contract inside the
  deployed image.
- **R-4 (untouched by design).** #273 (the hand-rolled all-cycle enumeration vs `networkx.
  simple_cycles`) and #274/#276 (the accepted bound + the derived door instrument) were named
  NOT-MINE in the brief; I read neither into scope and changed nothing near them. Note the coupling
  the lead already flagged on #272: if networkx ever becomes a PRODUCTION import, the override's
  module scope AND its dependency group both change — the comment I wrote says the dev/test-oracle
  framing out loud precisely so that move cannot happen silently.
- **R-5 (task board).** `e48347a9020945efb5725e16ae1e73c3` is held by `lead-pkt04b` at
  `in_progress`; I could not claim it and did not transition it. The lead closes it.
- **R-6 (tool honesty).** lore was first choice and answered (`lore_get_symbol`, `lore_impact`,
  `lore_findings`, `lore_comms`); the grep leg in §1.3 is a SANCTIONED fallback (exhaustiveness
  where a single missed site falsifies served prose), run as a cross-check of `lore_impact` rather
  than instead of it — both instruments returned the same three consumers. No friction filed,
  because none was met.
