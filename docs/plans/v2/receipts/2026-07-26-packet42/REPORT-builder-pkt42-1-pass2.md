# REPORT-builder-pkt42-1-pass2 — packet 42, builder pass 2 (#251 + the dead constants)

brief-base v7 read

> ⚠ **HEAD MOVED UNDER ME MID-RUN, AND EVERY NUMBER BELOW IS RE-MEASURED AT THE NEW ONE.**
> I began at `1c3260b`. While I worked, the lead committed **`3fd0fee`** (*"the EIGHTH is a class
> — four scanners each held a private root list"*), which **swept my uncommitted
> `scratch_provenance.py` edit into it verbatim** (md5 of the changed span is identical, §1.1). So
> my working tree is now clean and item ① is COMMITTED, not pending.
> **The consequence is the headline of this report:** the RED that edit causes is now a RED **in
> the committed tree**, not in a working tree someone can inspect before landing. §1.2.

Base at start: `1c3260b`. **All measurements below re-taken at `3fd0fee`**, 2026-07-27, in
`/home/ejprice/PycharmProjects/lore-pkt42`, branch `pkt42-prevent-the-leak`. My pass-1 report is
`REPORT-builder-pkt42-1.md` and is cited, not superseded.

- **state:** done-with-deviations — **① is committed and leaves a RED in `testpaths`; ② adjudicated
  but not executable by me; two ∀ scanners are still blind to `lorerunes` and `3fd0fee` did NOT
  close them.**
- **gate, re-measured at `3fd0fee` (working tree clean, so this IS the commit):** scoped run
  **0 failed / 388 passed** · `./scripts/typecheck.sh` **five iterations, all OK**, exit 0 ·
  `uv run ruff check .` **All checks passed!** · deploy-skill suite **117 passed** ·
  **full suite 3 failed / 7372 passed / 17 skipped / 3 xfailed in 190s**.
- **🔴 THE ONE THING TO READ FIRST:** `3fd0fee`'s message states *"Gates: scoped 388 passed /
  0 failed · typecheck 0 errors across all five members · ruff clean."* **Every one of those three
  is TRUE, and none of the three includes `scripts/test_scratch_copy.py`** — which is in
  `testpaths` and is **RED at HEAD**, because widening `WORKSPACE_MEMBERS` broke a hand-built
  per-member fixture. Green at the gates you ran, red at the one you did not. §1.2 carries the
  one-line fix.
- **deviations:**
  1. **I did NOT make the one-line test edit ① requires**, because your ⚠ forbids touching any test
     file. That is the whole of the delta between 2 failed and 3. Both readings of the instruction
     are written out in §1.2; I took the stricter one and say which I would pick.
  2. **I did NOT execute ②'s deletion.** Adjudicated (DELETE, §2) and measured with a mutation
     proof; its other half is two assertion lines in a test file, and landing my half alone leaves
     a RED assertion behind — the split-commit state R16 exists to forbid, one level down.
- **Packages considered: none — no mechanism specified.** Both items are registration/deletion work
  over existing constants. The §3 design question is about where a list LIVES, not about adopting a
  library.
- **decisions-needed (4):**
  1. 🔴 **The ① test edit** — one line, `scripts/test_scratch_copy.py`. **HEAD is red until it
     lands** (§1.2).
  2. 🔴 **Sites 8 and 9 are still open.** `3fd0fee` fixed four scanners *inside packet 42's own
     contract modules*; `test_backoff_seam.py` and `test_anchored_pattern_seam.py` are pre-existing
     repo instruments with their own private root lists, **both still excluding `lorerunes`**, and
     #9 pins a CLOSED SET that excludes it. Verified at `3fd0fee`, not assumed (§4).
  3. 🟠 **②'s deletion** — 2 production lines (mine) + 2 test lines (not mine), one commit (§2).
  4. 🟢 **The design call is ANSWERED, and we reached it independently** (§3): fixed constants +
     an invariant test, **not** runtime derivation, for the two provenance guards — because the
     file they would derive from lives inside the tree they grade. `3fd0fee` states the same
     reasoning in its own message. Derivation IS right for the packet's ∀ scanners, and `3fd0fee`
     built exactly that (`_logging_fixtures.workspace_roots`). The split is the answer.
- **receipt pointers:** §1 item ① + the committed RED · §2 item ② adjudication + mutation proof
  · §3 the design call, answered twice independently · §4 sites 8 and 9, still open · §5 residuals
  · §6 gates at `3fd0fee`.

---

## 1. ① `scripts/scratch_provenance.py` — `lorerunes` registered (site #7, #251)

### 1.1 The change

```python
WORKSPACE_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe", "lorerunes")
```

Plus a comment block that states, in the guard itself, what the missing member COSTS — that this is
the #140 instrument `scratch_copy.sh` runs, that a stale list lets a copy resolve that member from
the ORIGINAL checkout while the guard prints clean per-member receipts for the others, and that its
sibling guard was updated while this one was not. **The reason the comment is worth its lines:** the
line above it already claimed *"Mirrors `[tool.uv.workspace] members`"* and that claim was FALSE for
the whole of packet 42. A comment asserting a property is what failed here; a comment naming the
CONSEQUENCE is at least honest about why the reader should care.

It also records, in one sentence, why the constant is not derived at run time — see §3, so the next
engineer meets that trade deliberately instead of "fixing" it.

**It is COMMITTED, verbatim, inside `3fd0fee`** (which landed while I was still measuring). Verified
rather than assumed — the md5 of lines 35–52 of the committed file and of my working copy are the
same `564aaf9c…`, so what shipped is the text above and not a parallel edit. My working tree is
consequently clean; there is nothing of mine left to land for ①.

### 1.2 🔴 THE CLAIM THE GATE WAS SET ON IS FALSE — and it is now RED IN THE COMMITTED TREE

Both `REPORT-refactor-pkt42-1.md` §4.A and your brief state that no test breaks:

> *"`scripts/test_scratch_copy.py` does **not** pin the tuple (verified), so no test breaks."*

**The premise is right and the conclusion is wrong.** It does not pin the tuple. It hand-builds a
per-member map and calls `audit` with the DEFAULT member list, so widening that list makes `audit`
ask for a name the map does not contain. **Re-run at `3fd0fee` — i.e. this is the committed
tree, not my working copy:**

```
FAILED scripts/test_scratch_copy.py::test_audit_reports_every_dishonest_member_not_just_the_first
E   KeyError: 'lorerunes'
    scripts/scratch_provenance.py:124: in audit
        member = resolver(name)
```

**This is the THIRD appearance of one shape in this packet** — the same defect I hit in pass 1 with
`test_conformance_provenance.py`, and which you authorised the fix for then. Widening a ∀ set breaks
every hand-built per-member fixture that feeds it, and "does it pin the constant?" is the wrong
question to ask about that. The right question is *"does anything enumerate the members BY HAND?"*

**The one-line patch** (`scripts/test_scratch_copy.py`, in
`test_audit_reports_every_dishonest_member_not_just_the_first`):

```python
        "lorescribe": MemberProvenance(name="lorescribe", module_file=honest),
+       "lorerunes": MemberProvenance(name="lorerunes", module_file=honest),
```

with `assert len(failures) == 2` unchanged and `[receipt.name for receipt in receipts] ==
["lorescribe", "lorerunes"]`. (Measured: `audit` iterates in `WORKSPACE_MEMBERS` order, so
`lorerunes` appends after `lorescribe`.) Adding it as a second HONEST member is the stronger of the
two options for the same reason it was in pass 1: with one honest member, `len(receipts)` and *"the
honest member"* are indistinguishable.

**THE FORK, written down rather than picked** (brief-base §2 — *"when a sentence admits two readings
that would produce different code, that is the trigger, regardless of how confident you feel"*):

| reading | text | consequence |
|---|---|---|
| **(a) absolute** | *"Do not touch any test file."* | I cannot apply the patch. **HEAD stays 3 failed**, contradicting the gate you set — and it is now a committed red rather than a working-tree one. |
| **(b) scoped to the collision** | the same ⚠ then says *"**stay out of `loremaster/tests`, `loresigil/tests` and `lorerunes/tests` entirely** so we do not collide"*, and names the contract author's two in-flight pins — `scripts/test_scratch_copy.py` is in none of those | I apply it; tree returns to **2 failed**. |

**I took (a)** — the broader constraint, because the cost of being wrong that way is one round trip,
while the cost of being wrong the other way is a collision in a file someone else is editing. But
**(b) is the reading I would pick if it were mine**: the stated rationale is collision, `scripts/`
is outside the three named directories, and the pass-1 precedent is that you authorised exactly this
edit shape. Say the word and it is one line.

---

## 2. ② The two dead `token_survey` constants — ADJUDICATED: **DELETE**

### 2.1 Re-derived, not inherited

Bare anchor-free grep over the whole tree (receipts excluded), for all four constants
`TestConstantsParity` compares:

| constant | `scripts/token_survey.py` | verdict |
|---|---|---|
| `ANTHROPIC_COUNT_TOKENS_URL` | definition + the `post` call (`:781`) | **live in both modules** — real duplication, parity is real |
| `DEFAULT_ENV_FILE` | definition + the argparse default (`:1381`) | **live in both modules** — same |
| `ANTHROPIC_VERSION` | **definition only** (`:81`) | **DEAD** |
| `ANTHROPIC_API_KEY_ENV` | **definition only** (`:82`) | **DEAD** |

The refactor report's counts reproduce exactly. Their only consumer anywhere is
`test_calibration_counting.py::TestConstantsParity::test_endpoint_version_key_env_match_survey`.

### 2.2 The adjudication, and why it is DELETE rather than keep-with-a-comment

**They are genuinely dead, and the parity assertion over them is no longer load-bearing.** Packet 42
made `token_survey.ClaudeTokenCounter` IMPORT `build_auth_headers` and `load_api_key` from
`counting`. So the two counters' wire shape is now identical **by construction**, not because two
constants happen to agree — and that is the whole property `TestConstantsParity` existed to protect
(`counting.py`'s module docstring: *"That parity keeps every count comparable to the
generation-anchored `baseline.json` forever"*).

What remains is worse than merely useless, which is why I am not recommending the comment branch:

* The assertion compares a live constant against a **replica nothing reads**. It still
  discriminates — editing either reddens it — but it can no longer discriminate anything that
  affects the wire.
* Its RED would therefore be a **misleading diagnostic**: *"the two counters' constants diverge"*
  when the counters cannot diverge, because they share the builder.
* A duplicated policy value with no consumer is precisely the shape this packet spent a wave
  removing — the `load_api_key` twins and the two `Bearer` builders were deleted for exactly this
  reason (#102). Keeping two of the constants that motivated the consolidation, *because a test
  mentions them*, inverts the packet's own finding.

The two live rows (`URL`, `DEFAULT_ENV_FILE`) are genuine duplication and their parity legs stay.

### 2.3 The patch, MEASURED not proposed

Production half (mine, 2 lines, `scripts/token_survey.py`) — delete:

```python
ANTHROPIC_VERSION: str = "2023-06-01"
ANTHROPIC_API_KEY_ENV: str = "ANTHROPIC_API_KEY"
```

Test half (not mine, 2 lines, `test_calibration_counting.py::TestConstantsParity`) — delete the two
assertions, and rename `test_endpoint_version_key_env_match_survey`, which would otherwise name two
things it no longer checks.

**Blast radius measured with `scripts/mutation_proof.py`, declared-RED taken before the run, both
directions diffed, tree restored byte-exact:**

```
mutation LANDED (anchor matched exactly once) in scripts/token_survey.py
1 failed, 15 passed in 0.25s
FAILED …TestConstantsParity::test_endpoint_version_key_env_match_survey
E   AttributeError: module 'token_survey' has no attribute 'ANTHROPIC_VERSION'
tree restored byte-exact (md5 a4a2e02c30bcbe84c92e1addd4eae4ae)
PROOF HELD — the declared RED set fired EXACTLY
PROOF_EXIT=0
```

**Exactly one test node, and nothing else in the file's 16.** So the two halves are a single
small commit — which is also the right commit shape: a dead constant and its dead assertion are one
concern, the same argument R16 made about the deletion and its labelled-pattern fix.

**I did not apply my half alone**, because a production deletion that leaves a RED assertion behind
is the split-commit state R16 exists to forbid, one level down.

---

## 3. The design call: derive from `pyproject.toml`, or an invariant test?

**My answer: the INVARIANT TEST.** Not on style — on a specific hazard that applies to these two
guards and not to the repo's existing derivation.

> ✅ **ANSWERED TWICE, INDEPENDENTLY — and that is worth more than either answer alone.** `3fd0fee`'s
> commit message reaches the same conclusion in the same terms, before reading this: *"It stays a
> FIXED CONSTANT rather than being derived from pyproject.toml, and the reasoning refutes the lead's
> own suggestion in #251: this guard's whole job is to GRADE a tree, and an oracle derived from the
> tree under test cannot see a truncated or wrong copy of that file. What relates the mirror to the
> workspace is an INVARIANT TEST, not derivation and not a comment."* Two readers, no contact, same
> hazard, same verdict. **And the same commit built DERIVATION where derivation is right** —
> `_logging_fixtures.workspace_roots()` reads `[tool.uv.workspace] members` for the packet's ∀
> scanners, which lint the REPO rather than grade an artifact. **That split IS the answer**, and it
> is exactly the one the rest of this section argues for.

**The repo already derives, and it works — but at a site with a different relationship to its
input.** `test_shellout_allowlist.py` / the exec-seam gate derives its member set from
`[tool.uv.workspace] members` at runtime, exercises that derivation against SYNTHETIC workspaces
(`_write_workspace(root, ["alpha"])`), and its own comment says a hardcoded
`["lorescribe", "loresigil", "loremaster"]` *"must fail every synthetic fixture below"*. That is
derivation done properly, and it is the obvious precedent for doing the same here.

**It does not transfer, for one reason: those two guards GRADE A TREE, and the file they would
derive from lives INSIDE it.**

* `conformance_provenance.py` runs **inside the deployed image** and its job is to prove the image
  is honest. `pyproject.toml` **is COPYed into that image** (`Containerfile:61`). Deriving the
  expected member set from `/app/pyproject.toml` makes the oracle come from the artifact under
  test: an image that shipped a truncated `pyproject.toml` **and** a missing member would pass, and
  it would pass *silently*, which is the exact failure mode the guard exists for. Its own test
  constant already says so — *"NOT read back from the module (that would be tautological)"*; reading
  it back from the artifact is the same tautology one file over.
* `scratch_provenance.py` grades **the scratch copy**. Deriving from the copy's `pyproject.toml` has
  the identical hole. Deriving from the ORIGINAL's (via `Path(__file__)`) would be sound — but then
  the two sibling guards would use two different mechanisms, and *"two guards, same job, nothing
  relating them"* is #251's actual complaint, not its cure.

**And the invariant test generalises where derivation cannot.** The mirrors are not one shape:
`_SCANNED_MEMBERS` and `_SCANNED_ROOTS` hold per-member PATHS (`lorescribe/lorescribe`);
`mypy_path` is a colon-joined string; `testpaths` is a list of TEST dirs; the Containerfile is a
`COPY` line; and `LORE_NAMESPACES` is a deliberate SUBSET that must NOT gain `lorerunes` (re-derived
again this pass: it emits no logs; the stub's re-open trigger stands). Runtime derivation would have
to be reinvented in six shapes, and the one place it must NOT be applied would still need a written
exemption. **A single ∀ invariant test states all of that in one place, which is where the
"is this mirror current?" question actually belongs.**

**The pattern already exists and already worked.** `test_secret_typing.py::TestTheInImageGuardCoversEveryWorkspaceMember`
derives the declared members from `pyproject.toml` and asserts the conformance guard covers them —
it is the pin that caught the seventh site's sibling in pass 1. It needs siblings, not a
replacement:

```python
# sketch — the contract author's call on shape
MEMBER_MIRRORS = {
    "scratch_provenance.WORKSPACE_MEMBERS":   <set>,
    "conformance_provenance.WORKSPACE_MEMBERS": <set>,
    "test_secret_typing._SCANNED_MEMBERS":    <set>,
    "test_backoff_seam._SCANNED_ROOTS":       <set>,      # §4
    "test_anchored_pattern_seam._SCANNED_ROOTS": <set>,   # §4
}
# ∀ mirror: set == declared workspace members, EXCEPT the one documented subset
# (LORE_NAMESPACES — lorerunes emits no logs; re-open trigger recorded).
```

**⚠ The honest caveat on my own recommendation:** an invariant test only covers mirrors it
ENUMERATES, so it is a name-list, and this repo has six receipts on name-lists losing. It is not a
closed instrument — it is a cheaper and more general one than six derivations, and its list is at
least in ONE place where a reviewer can see it. If you want the stronger form, the derivable half
is *"every module-level `tuple[str, ...]` whose value is a subset of the workspace members"*, found
by AST rather than by name. That is a bigger build and it is a contract call, so I am naming it
rather than assuming it.

---

## 4. 🔴 THE LIST IS AT LEAST NINE SITES — two more ∀ scans silently exempt `lorerunes`

> ⚠ **STILL OPEN AT `3fd0fee`. VERIFIED, NOT ASSUMED.** That commit says it *"found FOUR scanners
> each carrying a PRIVATE copy"* and fixed them with one derived list — but its four are the
> scanners **inside packet 42's own contract modules** (the env gate, the M4 locals gate, the R2
> function-name corpus, the auth-holder sweep). The two below are **pre-existing repo instruments**
> and were not among them: `git show 3fd0fee --stat` names neither file, and both still hold their
> private tuples (`test_backoff_seam.py:152`, `test_anchored_pattern_seam.py:76`), with #9's closed
> set still asserting `{"loremaster", "lorescribe", "loresigil", "scripts"}` at line 305.
>
> **Their fix is now smaller than when I found them**, because `3fd0fee` built the thing they should
> call: `_logging_fixtures.workspace_roots()`. Both files live in `loremaster/tests/`, so they can
> import it. The change is *"stop holding a private list, call the derived one"* — the same move
> `3fd0fee` made four times — plus deleting #9's closed-set literal, which the derived list makes
> self-maintaining.

`d252802` instructs the reader to **derive** the sites by grepping for an existing member rather
than trust the enumeration. I did that (`grep -rn 'lorescribe/lorescribe\|"lorescribe"'`, bare and
anchor-free, over `*.py` / `*.toml` / `*.sh` / `Containerfile`), and the seven-item list is still
short by two. **Both are instances of the list's own class #4 — *"a package outside the scan is
silently exempt from every ∀ pin in the repo"* — at addresses the list does not name.**

### Site 8 — `loremaster/tests/test_backoff_seam.py::_SCANNED_ROOTS`

```python
_SCANNED_ROOTS = ("loremaster/loremaster", "loresigil/loresigil",
                  "lorescribe/lorescribe", "scripts", "skills")
```

The **deny-by-default backoff perimeter** (#207/#120): it AST-scans production source for
exponentiation by a variable and denies it everywhere but one evidence-backed file. `lorerunes` is
not scanned, so it is exempt from that perimeter — permanently and silently.

### Site 9 — `loremaster/tests/test_anchored_pattern_seam.py::_SCANNED_ROOTS`

```python
_SCANNED_ROOTS = (…/"loremaster", …/"lorescribe", …/"loresigil", …/"scripts")
```

Same shape, and this one **pins its own reach as a CLOSED SET**:

```python
assert scanned_packages == {"loremaster", "lorescribe", "loresigil", "scripts"}
```

So adding `lorerunes` to the roots reddens that pin until it is updated too — i.e. the fix is two
lines, coupled, in the same file.

**Exposure today: NIL, and I am not overstating it.** `lorerunes` holds one pure predicate — no
arithmetic, no compiled patterns, no `.match`. Neither gate would flag anything in it now. **The
defect is the SILENCE, not a live miss**: the whole reason class #4 is on the list is that a package
outside a ∀ scan is exempt without anyone being told, and `lorerunes` is explicitly built to GROW
("policy = validation predicates, error classification, retry/backoff budgets, sanitisation…"). A
retry budget landing in `lorerunes` is precisely what the backoff perimeter is for.

**I could not apply either fix** — both are `loremaster/tests`, which is the collision zone AND a
test file. The patches are one line each (plus the closed-set assertion in site 9).

**And the meta-point, which I think is the finding rather than the two lines:** the list has now been
wrong at **five** (`mypy_path` missed), at **six** (`scratch_provenance` missed), and at **seven**
(these two missed). Three corrections, three by a different reader. That is not carelessness; it is
the instrument lesson operating exactly as CLAUDE.md's six-defeat table predicts — **a list of
places to look is the artifact this repo has the most receipts against.** It is also the strongest
argument in §3's favour: the value of an invariant test is not that its list is complete, it is that
the list stops being something each new member's author has to rediscover.

---

## 5. Residuals — found, individually adjudicated, not acted on

Every hit from the bare sweep gets a verdict; no wholesale classification.

| site | verdict |
|---|---|
| `skills/lore-deploy/scripts/test_conformance_provenance.py:24` — module docstring still documents the surface as `("loremaster", "loresigil", "lorescribe")` | 🟠 **STALE.** Its own `EXPECTED_MEMBERS` two lines down is the 4-tuple. Served English contradicting the code it documents, in a test file I may not touch. One-line fix. |
| `loremaster/loremaster/logging_setup.py:64` `LORE_NAMESPACES` | 🟢 **CORRECT, re-derived again.** Not a workspace mirror — a logger-namespace list. `lorerunes` has no logger. Re-open trigger stands (the day it acquires `getLogger(__name__)`, its records propagate to root un-namespaced and escape the redaction handler). |
| `test_logging_setup.py:140`, `test_mcp_server.py:4098,4147` — three lore namespaces | 🟢 **CORRECT.** They mirror `LORE_NAMESPACES`, which is correctly three. |
| `test_static_snapshot_reacquire.py:37`, `test_schema_rebuild.py:49`, `test_memory_cutover.py:35`, `test_startup_divergence_reconcile.py:76` — `PP=<worktree>/loremaster:…/loresigil:…/lorescribe` in docstring run-recipes | 🟠 **STALE-ON-A-TRIGGER.** They are copy-paste recipes for reproducing a run; harmless while nothing in those suites imports `lorerunes`, wrong the day one does. Four docstrings, test files. |
| `scripts/test_scratch_copy.py:121–132` | 🔴 the §1.2 fixture — the one that is actually RED. |
| `loremaster/tests/test_shellout_allowlist.py:106,945` | 🟢 **CORRECT and the good precedent** — those lines are comments saying a hardcoded member list must FAIL its synthetic fixtures, because that gate derives (§3). |

---

## 6. Gates — all re-measured at HEAD `3fd0fee`, working tree clean

```
$ git log --oneline -1
3fd0fee fix(pkt42): the EIGHTH is a class — four scanners each held a private root list
$ git status --short          (only untracked REPORT-*.md; no tracked file modified)

$ uv run pytest <the six scoped paths> -q -n auto
388 passed in 5.67s

$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK · skills OK      (exit 0)

$ uv run ruff check .
All checks passed!

$ cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
117 passed in 13.90s

$ uv run pytest -q -n auto
3 failed, 7372 passed, 17 skipped, 3 xfailed, 1 warning in 190.38s (0:03:10)
```

The three, individually — no wholesale verdict:

| test | verdict |
|---|---|
| `test_retired_symbols.py::…::test_no_file_references_a_retired_symbol` | pre-existing, unrelated — reproduced at `76f1d9f` in a provenance-verified archive (pass-1 §7.8) |
| `test_surreal_harness.py::…::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` | pre-existing, packet-42-contract-caused — reproduced at `76f1d9f` (pass-1 §7.8) |
| `scripts/test_scratch_copy.py::test_audit_reports_every_dishonest_member_not_just_the_first` | 🔴 **NEW, and COMMITTED at `3fd0fee`.** Caused by item ①, which you instructed. One-line fix I did not apply — §1.2 is the fork. |

**Scoped moved 383 → 388** on the contract author's widened pins; all 388 pass.

**The gate you set was *"full suite still 2 failed / 7368 passed"*. It is 3 / 7372.** The +4 passed
are the contract author's new pins; the +1 failed is §1.2, and it is one line from being 2 again.

Nothing staged, nothing committed by me this pass — `git diff --cached --stat` is empty, and my only
production edit is already inside `3fd0fee`.
