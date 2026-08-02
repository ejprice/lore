# REPORT-riders-04b2-r11-1 — Ruling 11 guardrail riders (the B3 attribution leak)

## SUMMARY BLOCK

brief-base v10 read · brief project v7 read
state: **done-with-deviations**
deviation 1: Rider 1 got a REAL mutation proof (declared-RED set, `scripts/mutation_proof.py`, exit 0) ON TOP of the brief-mandated containment-detection control leg — the pin's RED direction is demonstrated, not merely argued.
deviation 2: Rider 1 carries two legs beyond the brief's literal spec — the oracle-blindness pin (6 params) and a door-B production-shape guard. Both disclosed in §1.3; neither weakens anything.
deviation 3: **RESOLVED in wave 2** — Rider 2's second half (`TestRenderInjectionRegistry`, in `test_mcp_server.py`) was flagged rather than edited under the original writable set; the lead granted D1/D2 at `0bb662a` and both are now APPLIED (§4.1, §4.2, §9).
deviation 4: `_unfenced` is a SECOND scan body (brief-directed) — ONE IMPLEMENTATION tension named and routed in §1.4.
Packages considered: fence-region-stripping predicate (`_unfenced`) — `markdown-it-py` 4.2.0, **READ** its live `MarkdownIt().parse()` token stream (correctly emits a `fence` token) → **bespoke**; reason in §5, not an unread assertion. Wave 2 (D1/D2) specified no mechanism — docstrings only.
Graded: R1/R2/R3 at cab7c128d0d67e1b433cd7242733131efb126783 · D1/D2 at 0bb662a0a4f0ca01ddfc458df7f0e7daf852cc1d · HEAD-at-report: 0bb662a0a4f0ca01ddfc458df7f0e7daf852cc1d · SAME (R1/R2/R3 landed in `0bb662a`; nothing they assert moved between the two shas)
decisions-needed: **none** — D1 and D2 were the open forks and both are granted and applied (§9).
receipt POINTERS: §1.2 pin run · §1.5 mutation proof · §2 residual sweep with per-hit verdicts · §3 suite runs · §6 gates + SCOPED-GREEN honesty · §9 D1/D2 applied

---

## 0 · Capability check (brief-base §4)

Nothing in the brief exceeded my toolset. `lore_comms register` + `drain` succeeded;
`lore_findings action=get id_or_number=321` returned the finding. No store work was
required, so `docs/reference/surrealdb-31-capabilities.md` was correctly skipped per the
brief. No lore-tool fallback to grep was needed for a code-STRUCTURE question
(`lore_get_symbol` resolved `AppContext._render_task_detail`); the greps in §2 are the
sanctioned non-symbol textual-seam case (prose in docstrings), said out loud here.

## 1 · Rider 1 — the asserted-bound pin

### 1.1 Home, and why

**`loremaster/tests/test_attribution_bound.py`** (new file, 21 tests).

Not `test_render_seam_pins.py`. That module's own docstring declares it holds *"two
independent, **zero-semantics** invariants"* — an AST mint-pin and an AST template-literal
pin. This bound is a **runtime render-behaviour** pin over four render families plus the
teaching-error surface; dropping it in would have falsified that module's docstring and
forced a co-edit, i.e. exactly the widening the brief told me to escalate rather than do.
The repo's own precedent for an asserted bound is a **dedicated section in the file about
that perimeter** (`test_shellout_seam_perimeter.py` §2, finding #138) — and here the bound
crosses what any single existing module owns (`test_task_read_surface.py` owns `action=get`
only). A dedicated file also makes the bound findable by name the day 04b-3 reddens it: the
failing FILE name is itself the message.

`loremaster/tests` is already in `testpaths` (`pyproject.toml`), so this is not a guard
nobody runs.

### 1.2 It PASSES today — the leak exists

```
$ uv run pytest -q loremaster/tests/test_attribution_bound.py
.....................                                                    [100%]
21 passed in 0.92s
```

The §11.1 measurement was **re-derived at `cab7c12`, not relayed** — I ran the sidecar's
verbatim probe before writing anything, and all six doors reproduce (`ctrl clean` True,
`newlines eq` True, `LEAKS` True on every row), with
`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`
(the real tree, not a copy).

### 1.3 What the pin asserts (and the two legs beyond the brief's literal spec)

Six doors from Ruling 11 §11.1's `DOORS` map, driven with the forgery **and** a benign
control:

| leg | params | what it asserts |
|---|---|---|
| `test_the_benign_control_does_not_carry_the_forgery` | 6 | CONTROL — the probe can tell hostile from benign. Without it the bound leg proves nothing. |
| `test_a_free_text_caller_value_leaks_unattributed` | 6 | **THE BOUND** — the caller's bytes survive `_unfenced`. Carries the verbatim KNOWN BOUND message + the named re-open trigger. |
| `test_the_existing_injection_oracle_is_blind_to_this_class` | 6 | ⚠ **BEYOND THE BRIEF, disclosed** — `assert_render_injection_safe` PASSES on every leaking door. This is §11.1 fact 1, and it is what makes Rider 2's prose correction **checkable** rather than prose nobody can verify ("ship the instrument with the law"). Goes RED the day the oracle is widened. |
| `test_door_b_still_mirrors_the_production_teaching_shape` | 1 | ⚠ **BEYOND THE BRIEF, disclosed** — door B builds `TaskNotFoundError`'s message in the TEST (the real raise needs a live ledger, which a rider does not buy). This asserts `tasks.py` still raises `f"no task with id {task_id!r}"` (7 identical sites at `cab7c12`), so a stale mirror fails loudly instead of testing a fiction. |
| `TestThePredicateCanSeeContainment` | 2 | The control the brief required: a value inside a PRODUCTION `render_fenced` fence is stripped by `_unfenced` (two-sided — the fence must also PRESERVE the bytes), and a *differently*-broken containment (`repr`) still leaks, so the predicate is not clearing on any-transformation-whatsoever. |

The KNOWN BOUND message is carried verbatim in the failure text (`_DELETE_THIS_PIN`) **and**
in the module docstring, with the re-open trigger named in both: **04b-3's link-5 slice**.

`_DOORS` is labelled a **HAND LIST** in the module docstring, with the derivation (Ruling 11
§11.5) named as 04b-3's first deliverable — shipping an unlabelled hand list inside a pin
about deriving surfaces is the failure this repo has the most receipts against.

### 1.4 ⚠ `_unfenced` is a SECOND scan body — named, not hidden

The brief directed a fresh minimal helper and forbade cloning `test_comms_footer.py::_unfenced`.
That is in tension with ONE IMPLEMENTATION, so here is the honest accounting:

- **The POLICY is shared and mutation-provable**: both bodies import `FENCE_CHAR` /
  `MIN_FENCE_WIDTH` from `loremaster.sanitise`. Change the production fence shape and both
  redden. What is duplicated is the trivial scan mechanics, not the rule.
- **What I did NOT do, and why**: importing a `test_*` module's private symbol from another
  test module couples a bound pin to a landed contract file; promoting `_unfenced` into
  `render_injection_scaffold.py` would mint a shared surface, which the brief explicitly
  forbade ("these MINT NOTHING") and would still leave the footer's copy in place today.
- **Routed**: Ruling 11 §11.5 already says the 04b-3 slice EXTENDS the c3fix `_unfenced`
  with the inline-delimiter case. That slice is where the promotion to one implementation
  belongs, and it deletes this pin anyway. Recorded in the helper's own docstring.

### 1.5 Mutation proof — the pin's RED direction, DEMONSTRATED

The brief said a bound pin cannot show its RED direction without a containment build, so a
containment-detection control leg was the substitute. I built the containment instead, as a
mutation, so the receipt is about the PIN and not only about the predicate.

**Declared BEFORE the run** (node ids taken from `pytest --collect-only -q`, never
transcribed from output; the declaration file was written before the mutation ran):

- RED: `test_a_free_text_caller_value_leaks_unattributed[task_rows.owner]`
- RED: `test_a_free_text_caller_value_leaks_unattributed[task_detail.owner]`
- GREEN, with reasons: `claim_result.*` (interpolates `owner` in its OWN f-string, never via
  `_render_task_rows`) · `task_detail.provenance.created_by` (`owner` is BENIGN there) ·
  `TaskNotFoundError(task_id!r)` (message built in the test) · **every
  `test_the_existing_injection_oracle_is_blind_to_this_class[*]`** (the fence is added to
  BOTH the benign baseline and the hostile render, so newline counts stay equal and the
  oracle still passes — i.e. the oracle cannot see containment either) · the controls.

```
$ uv run python scripts/mutation_proof.py \
    --file loremaster/loremaster/server.py \
    --anchor 'f"(id {task.id}, owner {safe_str(task.owner)}, "' \
    --replacement 'f"(id {task.id}, owner\n{render_fenced(str(task.owner))}\n, "' \
    --expect-red '...::test_a_free_text_caller_value_leaks_unattributed[task_rows.owner]' \
    --expect-red '...::test_a_free_text_caller_value_leaks_unattributed[task_detail.owner]' \
    -- uv run pytest -q loremaster/tests/test_attribution_bound.py

mutation LANDED (anchor matched exactly once) in loremaster/loremaster/server.py
2 failed, 19 passed in 0.69s
tree restored byte-exact (loremaster/loremaster/server.py: md5 fce25de2493b3a935dbf8046b1c0d914)
PROOF HELD — the declared RED set fired EXACTLY
MUTATION_PROOF_EXIT=0
```

An independent `cp -a` content backup was taken first and `diff -q` confirmed
`server.py RESTORED BYTE-EXACT` after the run (belt and braces over the tool's own md5).

⚠ **Stated bound on this proof:** the declared RED set is scoped to
`test_attribution_bound.py` only. A real link-5 containment build would redden a great deal
more elsewhere (`test_task_read_surface.py`, `test_query_tasks_bounded.py`, the registered
`RenderCase`s). This proves *this pin* fires; it makes no claim about the rest of the suite.

⚠ **A second, unplanned finding from the same proof, worth 04b-3's attention:** under a
real containment mutation, `assert_render_injection_safe` stayed GREEN on the newly-contained
door. The existing oracle cannot see containment ARRIVING any more than it can see the leak —
so it will neither confirm nor deny the link-5 slice, and 04b-3 must not read a green
injection-registry run as evidence its fix landed.

## 2 · Riders 2 & 3 — the retired prose, with a per-hit residual table

**Pre-edit grep for the retired phrases** (BARE, anchor-free — repo law) was run BEFORE any
edit. **No test asserts either retired string**: `grep -rn` for `three-assertion` /
`acceptance oracle` / `archetype` / `single-line trailers` / `BODY is FENCED` across the
whole `*.py` tree returned no assertion, no parametrised literal, no AST-scan constant —
only prose. **So no pin co-edits.** (`test_text_hygiene.py` scans production string
literals, but only for retired `lore_`-shaped tool tokens and three retired bare verbs; my
new prose introduces none, and it is GREEN — §3.)

**Post-edit residual table** — every remaining hit, `file:line`, individual verdict (no
wholesale classification):

| file:line | text | verdict |
|---|---|---|
| `render_injection_scaffold.py:84` | *"**NOT** a general acceptance oracle for a served render, and it must not be read as one"* | **CORRECT** — the negation is the fix. |
| `render_injection_scaffold.py:94` | quotes the retired sentence to record what was retired, with a date + sha | **CORRECT** — dated provenance, explicitly labelled FALSE. |
| `test_mcp_server.py:7712` | comment: *"extracted … the three-assertion acceptance oracle into the shared, reusable module"* | **RESIDUAL, not edited** — outside the brief's writable set. The COUNT stays true (still three assertions) and it narrates an extraction rather than claiming coverage, so it is not a dangling name. See D1 (§4.1). |
| `server.py:3421` | `_render_finding_detail`: *"the identical archetype"* (finding #34, `diff.py`'s sanitiser adoption) | **UNRELATED** — about a cross-module sanitiser pattern, not the fence/trailer completeness claim. |
| `server.py:3974` | my own new text quoting *"the archetype, verbatim"* as the retired framing | **CORRECT** — the retirement record. |
| `test_task_read_surface.py:2888` | *"The other half of the archetype: the body is FENCED, the trailers are SANITISED"* | **RESIDUAL, not edited** — outside writable set, and it describes what that test pins rather than claiming closure. See D2 (§4.2). |
| `diff.py:90`, `test_workspace_status.py:{29,991}`, `test_mcp_server.py:1095`, `skills/lore-deploy/tests/test_workspace_probe.py:689` | "render archetype" / "#94 archetype" / "defect archetype" | **UNRELATED** — different subjects entirely. |

### 2.1 Rider 2 — `loremaster/tests/render_injection_scaffold.py`

- `assert_render_injection_safe`'s docstring: the opening line *"The three-assertion
  acceptance oracle a served render must pass"* is replaced by *"Three assertions about
  CONTROL CHARACTERS AND ROW SHAPE. **NOT a general acceptance oracle for a served render,
  and it must not be read as one.**"*, plus a ⚠⚠ block that (a) explains all three
  assertions are about LINE STRUCTURE and none looks at what the surviving text SAYS,
  (b) names the blind class (same-line instruction forgery) and the six measured doors
  including the two already-registered `RenderCase` families, (c) cites **finding #321 /
  Ruling 11 §11.1, measured 2026-08-02 at `cab7c12`**, (d) points at
  `test_attribution_bound.py`, and (e) warns against widening these assertions to cover the
  class without reading that file (it is a provenance problem, not a charset problem).
- Module docstring: a ⚠⚠ pointer at the function's own scope statement, saying plainly that
  **a registry name is not a coverage claim**; and the two bare uses of the over-claiming
  label ("the SAME acceptance oracle", "the three-assertion acceptance oracle") reworded to
  name the mechanism (`control-character/row-shape check`) and the symbol
  (`:func:`assert_render_injection_safe``).
- **No assertion was weakened, reordered, or removed.** The three `assert`s are byte-identical.

### 2.2 Rider 3 — `loremaster/loremaster/server.py::AppContext._render_task_detail`

The archetype is **kept** — the body/line distinction is right — and its *"⚠ **The
archetype, verbatim**"* framing is removed, because that sentence is an instruction to clone
a shape with a measured hole (#102: a reference pattern in a doc is a defect to clone). The
docstring now:

- opens *"The shape, and what each half of it actually buys"* instead of "the archetype, verbatim";
- adds ⚠⚠ **"THIS SHAPE IS NOT A COMPLETE CONTAINMENT, SO DO NOT CLONE IT AS ONE"**, naming
  finding **#321** and dating the measurement, and stating explicitly that the completeness
  claim was false while the body/line distinction stands;
- states **what SANITISED does not buy**: it is a CONTROL-CHARACTER policy, not a PROVENANCE
  one — `sanitise_line` stops line-structure breakage, not attribution; a same-line
  instruction in `owner`/`created_by` carries no control character and no row shape, survives
  intact, and reaches the consuming agent as this server's own prose. Both this render's
  `owner` trailer and its `provenance` blob are named as measured doors;
- names the bound as DELIBERATE and PINNED until **04b-3's link-5 slice**, forbids adding a
  per-site containment here (Ruling 11 §11.4), and points at `test_attribution_bound.py`.

## 3 · Suite runs (passed-COUNTs, not adjectives)

**The affected set** — `test_render_seam_pins.py`, every module importing
`render_injection_scaffold` (derived by `grep -rln`, 11 modules), the `_render_task_detail`
behaviour suite, and the production-prose scanner:

```
$ uv run pytest -q -n auto \
    loremaster/tests/test_attribution_bound.py loremaster/tests/test_render_seam_pins.py \
    loremaster/tests/test_render.py loremaster/tests/test_text_hygiene.py \
    loremaster/tests/test_task_read_surface.py loremaster/tests/test_mcp_server.py \
    loremaster/tests/test_comms_tool.py loremaster/tests/test_comms_wiring.py \
    loremaster/tests/test_comms_fleet_grouping.py loremaster/tests/test_comms_schema.py \
    loremaster/tests/test_brief_ledger.py loremaster/tests/test_agent_registry.py \
    loremaster/tests/test_message_ledger.py loremaster/tests/test_enforced_relations.py

2658 passed, 14 skipped, 3 xfailed in 199.57s (0:03:19)
EXIT=0
```

Re-run after the final scaffold-docstring wording change (the run above predates it):

```
$ uv run pytest -q -n auto loremaster/tests/test_attribution_bound.py \
    loremaster/tests/test_render_seam_pins.py loremaster/tests/test_text_hygiene.py \
    loremaster/tests/test_task_read_surface.py
143 passed in 9.45s
```

`_enforced_relations_scaffold.py` is a scaffold, not a suite — covered via
`test_enforced_relations.py`, included above.

## 4 · Flags — files outside the writable set that the ruling touches

### 4.1 D1 — `test_mcp_server.py::TestRenderInjectionRegistry` (Ruling 11 §11.6 item 2, second half)

> ✅ **APPLIED in wave 2** (lead grant at `0bb662a`), verbatim as the replacement below. The
> analysis in this section is retained as the reason it was flagged rather than edited in
> wave 1. Receipts: §9.

Ruling 11 asks for BOTH the oracle docstring **and** `TestRenderInjectionRegistry`, which
*"reads as completeness"*. That class lives in **`test_mcp_server.py`**, not in the scaffold
the brief named. Brief-base §2 makes the writable set absolute, so I did not edit it. Two
readings of the brief, written out rather than picked silently: *(a)* "the scaffold file" is
the writable set, the class is a flag — **what I did**; *(b)* "already-open files" extends to
the class the ruling names. I chose (a) because `test_mcp_server.py` is named nowhere in the
brief, and because the correction now lives at the ONE place the oracle is defined — the
class CALLS `assert_render_injection_safe`, whose docstring states its scope — leaving only
the class's own one-line docstring as residual.

**Exact edit, if granted** — replace

```python
    """PKT-06 §D3: the render-injection meta-test + its completeness pin."""
```

with

```python
    """PKT-06 §D3: the render-injection meta-test + its completeness pin.

    ⚠ "Completeness" here means REGISTRY completeness (a registered family's cases are
    still present), NEVER threat completeness. The oracle this drives checks CONTROL
    CHARACTERS AND ROW SHAPE only and is measurably blind to same-line instruction
    forgery — a registered case can be GREEN while leaking (finding #321, Ruling 11;
    asserted in ``test_attribution_bound.py``). Read
    ``assert_render_injection_safe``'s docstring before treating a green run here as
    closure.
    """
```

### 4.2 D2 — `test_task_read_surface.py::test_the_SINGLE_LINE_trailers_are_SANITISED_not_fenced`

> ✅ **APPLIED in wave 2** (lead grant at `0bb662a`), verbatim as the appended line below.
> Receipts: §9.

Its docstring repeats the archetype's second half — *"the body is FENCED, the trailers are
SANITISED"* — one level down from the docstring Rider 3 corrected. Milder than the server.py
case (it describes what that test pins, not a safety guarantee) and outside the writable set,
so **not edited**. If granted, one appended line suffices: *"⚠ SANITISED is a control-character
policy, not a provenance one — a same-line instruction in a trailer survives it (finding #321,
Ruling 11; asserted in `test_attribution_bound.py`)."*

### 4.3 Not a flag, recorded for 04b-3

The `!r` teaching-error family is 7 identical `TaskNotFoundError(f"no task with id {task_id!r}")`
sites in `tasks.py` at `cab7c12` (I re-derived this: the sidecar's §11.1 says 8, and the
difference is the class DEFINITION line at `tasks.py:493` plus the docstring mention at
`tasks.py:57` — `grep -n 'TaskNotFoundError('` returns 9 lines, of which **7 are `raise`
sites**). Nothing in this wave depends on the number; 04b-3 should derive it rather than
inherit either figure.

## 5 · Packages considered (brief-base §1)

| mechanism | library evaluated | what I READ | verdict |
|---|---|---|---|
| fence-region-stripping predicate (`_unfenced`) | `markdown-it-py` 4.2.0 (present in the venv, transitively via `rich`) | ran `MarkdownIt().parse()` live on a lore-shaped render and inspected the token stream — it **does** emit a `fence` token with the body isolated, so it is technically capable | **bespoke** |

Reason for `bespoke`, so this is not an unread assertion: (1) markdown-it implements
**CommonMark's** fence rules, which are not lore's — production sizes its fence
`max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)` and the whole load-bearing property of
this helper is that it is DERIVED from `FENCE_CHAR`/`MIN_FENCE_WIDTH`, so a change to the
production fence shape reddens the pin. Routing through a third-party CommonMark parser
installs a **second, independent notion of "what a fence is"** — precisely the divergence
ONE IMPLEMENTATION exists to prevent, and it would silently keep passing the day lore's
fence changes. (2) It is a transitive dependency, not a declared one; adopting it in a
gate would need a declaration and an install authorization, which a rider does not buy.
Noted for 04b-3 in case its containment sweep wants render-fidelity checking, where the
trade may go the other way.

## 6 · Gates — SCOPED-GREEN honesty

- **`ruff check` on my three files: CLEAN.**
  ```
  $ uv run ruff check loremaster/tests/test_attribution_bound.py \
      loremaster/tests/render_injection_scaffold.py loremaster/loremaster/server.py
  All checks passed!
  ```
  (Two initial findings — `I001` import order, `UP017` `datetime.UTC` — fixed before this run.)
- **`scripts/typecheck.sh`: RED at `cab7c12`, and it is NOT MINE.** It is the packet-39
  RED_ADJUDICATED state (#306/#307). Measured: `Found 102 errors in 8 files (checked 182
  source files)` on the `loremaster` leg; every error file is an auth/posture file
  (`_auth_fixtures.py`, `test_allowlist_roster.py`, `test_auth_composition.py`,
  `test_auth_identity_seam.py`, `test_auth.py`, `test_google_token_verifier.py`,
  `test_hosted_readonly_posture.py`, `test_permission_resolver_seam.py`) plus three
  `lorerunes/tests/*`. **Zero errors name any of my three files.** The `skills`,
  `docs/eval`, `scripts` and `shellcheck` legs are OK. **I do not claim gates-green.**
- **Suites: green with counts, §3.**
- **`scripts/pending_contract_gate.py --currency` (the manifest-derived gate-set read
  CLAUDE.md requires at wave close-out): PASS — no `RED_ORPHANED`.** Run to completion at
  `cab7c12` with these three files in the tree:
  ```
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 191 residual(s), owned by: packet-39-pending-build
  ruff         GREEN
  pytest       RED_ADJUDICATED — 444 residual(s), owned by: packet-39-pending-build
  CURRENCY   : PASS — every claimed gate is GREEN or OWNED
    (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
  ```
  The `191` matches my own `grep -c "error:"` over `typecheck.sh`'s output independently, so
  the two derivations agree. Both RED gates carry packet 39's adjudication, not mine — and
  the tool says plainly this is not a deploy receipt.

## 7 · Everything else I noticed (scope belongs to the operator)

1. **The oracle cannot see containment arriving** (§1.5). 04b-3 must not read a green
   `TestRenderInjectionRegistry` run as evidence the link-5 fix landed.
2. **`_render_claim_result`'s own docstring already records a residual gap** — its
   BLOCKED/UNOWNED branch interpolates `blocked_by`/`status` unwrapped, *"flagged as a
   residual gap for the PKT-03 tree-wide sweep"*. That is a different (charset) class from
   #321, still open, and worth folding into 04b-3's derived surface rather than leaving it
   pointing at a sweep that has not run.
3. **The `!r` count discrepancy** in §4.3 — 7 raise sites vs the sidecar's 8. Immaterial
   here, flagged so it is not inherited.

## 8 · Files changed

| file | change |
|---|---|
| `loremaster/tests/test_attribution_bound.py` | **NEW** — Rider 1, the asserted bound (21 tests) |
| `loremaster/tests/render_injection_scaffold.py` | Rider 2 — docstrings only; **no assertion touched** |
| `loremaster/loremaster/server.py` | Rider 3 — `_render_task_detail` docstring only; **no code touched** (byte-exactly restored after the §1.5 mutation, verified two ways) |

**Docstring-only, PROVEN rather than asserted.** Both edited files were AST-parsed at `HEAD`
and in the working tree, every module/class/function docstring stripped, and the resulting
`ast.dump`s compared:

```
loremaster/loremaster/server.py: code identical modulo docstrings = True
loremaster/tests/render_injection_scaffold.py: code identical modulo docstrings = True
```

So "no assertion was weakened" and "no code touched" are measurements, not claims — a
one-character change to any statement in either file would have flipped both lines to False.

No git state was mutated: nothing staged, committed, or reverted. The lead commits.

---

## 9 · Wave 2 — D1 and D2 APPLIED (lead grant, base `0bb662a`)

R1/R2/R3 landed in `0bb662a`. The lead then granted the two flagged edits, writable set
expanded to exactly two files, **docstring only**.

| file | change |
|---|---|
| `loremaster/tests/test_mcp_server.py` | D1 — `TestRenderInjectionRegistry`'s docstring, replaced verbatim with the §4.1 text: "completeness" here means REGISTRY completeness, never THREAT completeness; the oracle checks control characters and row shape only; a registered case can be GREEN while leaking (finding #321, Ruling 11; asserted in `test_attribution_bound.py`); read `assert_render_injection_safe`'s docstring before treating a green run as closure. |
| `loremaster/tests/test_task_read_surface.py` | D2 — `test_the_SINGLE_LINE_trailers_are_SANITISED_not_fenced`'s docstring, the §4.2 line appended verbatim: SANITISED is a control-character policy, not a provenance one — a same-line instruction in a trailer survives it (finding #321, Ruling 11; asserted in `test_attribution_bound.py`). |

**Docstring-only, PROVEN not asserted** — same instrument as §8, both files parsed at
`0bb662a` and in the working tree, docstrings stripped, `ast.dump`s compared:

```
loremaster/tests/test_mcp_server.py: code identical modulo docstrings = True
loremaster/tests/test_task_read_surface.py: code identical modulo docstrings = True
```

**Suites** (the two touched files only, per the lead's instruction not to re-run the
14-module sweep):

```
$ uv run pytest -q -n auto loremaster/tests/test_mcp_server.py loremaster/tests/test_task_read_surface.py
731 passed in 109.03s (0:01:49)
```

**ruff:**

```
$ uv run ruff check loremaster/tests/test_mcp_server.py loremaster/tests/test_task_read_surface.py
All checks passed!
```

**Nothing else touched.** `git status --short` after the edits shows exactly the two
modified files plus this untracked report; no assertion, no logic, no git state.

**Coverage of Ruling 11's riders is now complete:** item 1 (the asserted-bound pin) ·
item 2 BOTH halves (the oracle docstring + the registry class) · item 3 (the archetype
docstring, now with its test-tree echo corrected too) · item 4 (finding #321) was already
filed by the lead. The two residual-table rows in §2 that read "RESIDUAL, not edited"
are, as of this section, **edited** — the table is retained as the wave-1 record.
