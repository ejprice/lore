# REPORT-stub-pkt42-1-pass2 — STUB phase pass 2, packet 42: mint `lorerunes`

brief-base v7 read

- **state:** done-with-deviations
- **deviation 1:** I created `lorerunes/tests/test_smoke.py` (2 lines, mirroring
  `lorescribe/tests/test_smoke.py` byte-for-byte in shape). Registering `lorerunes/tests` in
  `testpaths` while the directory does not exist makes **every** pytest invocation in the repo
  error. This is a NEW test for a NEW package, not an edit to the frozen contract — but it is
  still me writing a test, so it is called out rather than buried.
- **deviation 2:** I rewrote five stale member-count prose spans in `scripts/typecheck.sh` and
  `Containerfile` ("the three workspace members", "all three tests/ dirs", "three total"). A
  regression my own change directly caused (brief-base §2). Written **count-free** rather than
  updated to "four", so member five does not re-stale them.
- **deviation 3:** `uv.lock` changed (+6 lines). Not optional — the Containerfile runs
  `uv sync --locked`, which **fails the build** on a stale lock.
- **Packages considered:** none — no mechanism specified. This pass mints a package skeleton and
  registers it; the one function it declares (`is_blank`) raises `NotImplementedError` by design.
  ⚠ For the GREEN implementer: the predicate's semantics are `not value or not value.strip()`,
  which is stdlib `str.strip`/`str.isspace` — there is no package to evaluate here, and R29 already
  ruled out the library alternative (`pydantic.Field(min_length=1)`) by measurement.
- **decisions-needed #1 (BLOCKING R29's own rider):** `lorerunes` **cannot** be added to the
  deploy skill's `conformance_provenance.py::WORKSPACE_MEMBERS` — a frozen test asserts that
  tuple exactly. **Proven by mutation: 7 tests redden.** R29 names that in-image conformance run
  (#139) as the instrument that proves the member reached the artifact, so as it stands **the
  ruling's guard does not cover the member the ruling mints.** Routes to `tdd-contract`. §5.
- **decisions-needed #2:** two further member registries exist that the six-site list omits —
  `scripts/scratch_provenance.py::WORKSPACE_MEMBERS` and
  `loremaster.logging_setup::LORE_NAMESPACES`. Neither is in my brief; neither is blocked. §5.
- **decisions-needed #3:** the contract revision (+225 lines across two test files) is
  **uncommitted** in the working tree. §6.
- **receipts:** §1 gate · §2 counts + node delta · §3 what was created · §4 the six sites ·
  §5 the sites beyond six + the mutation proof · §6 other gates.

All measurements taken **2026-07-27** in `/home/ejprice/PycharmProjects/lore-pkt42`, branch
`pkt42-prevent-the-leak`, at HEAD `ab6c965` plus the uncommitted contract revision. They are not
current claims about any later tree. My pass-1 work is committed at `2439005`; this report
supplements, and does not supersede, `REPORT-stub-pkt42-1.md` (still untracked at repo root —
see §6).

**Tree-provenance receipt:**

```
lorerunes: /home/ejprice/PycharmProjects/lore-pkt42/lorerunes/lorerunes/__init__.py
```

Resolves inside the packet-42 worktree. `/home/ejprice/PycharmProjects/lore` untouched.
**Nothing staged, nothing committed** (`git diff --cached --stat` empty). The frozen contract
test files were not edited by me — the `M` on two of them predates this pass (§6).

---

## 1. THE GATE

```
BEFORE:  124 failed, 255 passed in 5.80s
AFTER:   121 failed, 258 passed in 5.88s
FINAL (re-run, reproducible):  121 failed, 258 passed in 5.82s
```

Failure-type histogram, the brief's exact grep:

| type | before | after |
|---|---|---|
| AssertionError | 70 | 67 |
| TypeError | 21 | 21 |
| RuntimeError | 2 | 2 |
| **ModuleNotFoundError** | **1** | **0** ✅ |
| **NotImplementedError** | 0 | **1** ← the stub being HIT |

Structural sentinels, word-boundary scan (the brief's `[A-Za-z]*` cannot cross `.` or `_`, so it
silently drops dotted exception names — I do not rely on it alone):

```
ModuleNotFoundError    0
ImportError            0
AttributeError         0
NameError              0
SyntaxError            0
```

Full per-failure classification via `--tb=line` (one line per failure), reconciling to 121/121:

| type | count | verdict |
|---|---|---|
| `AssertionError` (67 + 5 bare-`assert` renderings) | 72 | BEHAVIORAL |
| `pydantic_core._pydantic_core.ValidationError` | 25 | BEHAVIORAL |
| `TypeError` (all one cause: `resolve_secret()` has not yet grown `env_file`) | 21 | BEHAVIORAL |
| `Failed: DID NOT RAISE` | 2 | BEHAVIORAL |
| `NotImplementedError` | 1 | BEHAVIORAL — **the stub** |
| **total** | **121** | |

The single `NotImplementedError` is located, as intended, at
`lorerunes/lorerunes/blankness.py::is_blank` — i.e. the contract now reaches the seam and stops
there, which is precisely the state GREEN is supposed to start from.

## 2. Node-id delta — 3 fixed, 0 newly failing

| fixed (red → green) | why |
|---|---|
| `TestEverySecretParameterIsTyped::test_the_scan_reaches_every_workspace_member` | the AST scan's `_SCANNED_MEMBERS` entry now resolves to a real directory |
| `TestTheBlanknessPredicateIsGENUINELYSHARED::test_the_shared_package_depends_on_nothing_but_the_stdlib` | the package imports only its own submodule |
| `TestTheBlanknessPredicateIsGENUINELYSHARED::test_the_shared_package_does_NOT_resolve_secrets` | no `environ`/`getenv` anywhere in it |

**Newly failing: none.** The fourth test in that class,
`test_the_shared_package_exists_and_owns_the_predicate`, correctly remains RED: `callable(...)`
passes, then `predicate("")` hits the stub. That is the intended shape — the package exists, the
name is bound, the behaviour is absent.

## 3. What was created

```
lorerunes/pyproject.toml              19 lines   dependencies = []  (stdlib only, and that is the constraint)
lorerunes/lorerunes/__init__.py       22 lines   re-exports is_blank; __all__
lorerunes/lorerunes/blankness.py      42 lines   is_blank(value: str) -> bool  -> NotImplementedError
lorerunes/tests/test_smoke.py          2 lines   import smoke (deviation 1)
```

`__pycache__` is covered by `.gitignore:2`; a dry-run `git add` of the tree stages exactly the
four files above.

**Why a `blankness.py` submodule rather than putting `is_blank` in `__init__.py`:** CLAUDE.md's
`lorerunes` section says the package is the home for *"validation predicates, error
classification, retry/backoff budgets, sanitisation, normalisation, formatting rules"* — it is
built to grow. Putting the first primitive in `__init__.py` sets the precedent that everything
lands there. The package-level re-export is what the contract binds to
(`from lorerunes import is_blank`), so callers are unaffected either way.

**The name is `lorerunes`, PLURAL, everywhere** — package dir, import name, workspace member,
`mypy_path`, `MEMBERS`, `testpaths`, Containerfile, docstrings. I grepped my own diff for a stray
singular: zero occurrences of `lorerune` not followed by `s`.

## 4. THE SIX SITES — which existed, which I added

| # | site | state before | action |
|---|---|---|---|
| 1 | `pyproject.toml` `[tool.uv.workspace] members` | absent | **ADDED** |
| 2 | `pyproject.toml` `mypy_path` | absent | **ADDED** |
| 3 | `scripts/typecheck.sh` `MEMBERS` | absent | **ADDED** |
| 4 | `_SCANNED_MEMBERS` (`test_secret_typing.py`) | **ALREADY PRESENT** — contract author's | **verified, not duplicated** |
| 5 | `pyproject.toml` `testpaths` | absent | **ADDED** (+ created the dir it names) |
| 6 | `Containerfile` | absent | **ADDED** |

Site 4 verified as `(SHARED_PREDICATE_PACKAGE, f"{SHARED_PREDICATE_PACKAGE}/{SHARED_PREDICATE_PACKAGE}")`
— derived from the constant, not a hardcoded literal, so it cannot drift from the ruled name. No
edit made.

**Site 3 is its own iteration, not a merged invocation** — the loop body is
`uv run mypy "${member}"`, so adding the name adds an iteration. Receipt, four separate verdicts:

```
typecheck: lorerunes OK        <- Success: no issues found in 3 source files
typecheck: lorescribe OK
typecheck: loresigil FAILED
typecheck: loremaster FAILED
```

**Site 6 — the Containerfile does NOT install the workspace wholesale.** Asked not to guess, so
the actual lines, before my edit:

```dockerfile
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock        /app/uv.lock
COPY lorescribe/ /app/lorescribe/
COPY loresigil/  /app/loresigil/
COPY loremaster/ /app/loremaster/
RUN uv sync --locked --all-packages
```

`uv sync --all-packages` *does* install every member — but only from source already COPYed into
the build context. There is one explicit `COPY` per member, so I added
`COPY lorerunes/  /app/lorerunes/`. Without it the build fails loudly at `--locked`
(a workspace member with no source), which is the good direction; the dangerous direction is the
one R29 names, and it is closed.

## 5. ⚠ SITES BEYOND THE SIX — the enumeration is still incomplete

Per the brief, I swept by grepping `lorescribe` bare rather than trusting the list. Three further
member registries exist. **I changed none of them.**

### 5a. `skills/lore-deploy/scripts/conformance_provenance.py::WORKSPACE_MEMBERS` — BLOCKED

```python
WORKSPACE_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")
```

pinned by a frozen test:

```python
EXPECTED_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")
...
assert tuple(conformance_provenance.WORKSPACE_MEMBERS) == EXPECTED_MEMBERS
```

**Mutation proof, with both control legs** (CLAUDE.md: a probe needs a control):

| leg | result |
|---|---|
| control — before mutation | `117 passed` |
| **mutated** (`WORKSPACE_MEMBERS` gains `"lorerunes"`) | **`7 failed, 110 passed`** |
| restored, byte-exact (`md5 b204ad5d…` identical, `git status skills/` clean) | `117 passed` |

The 7: `TestModuleSurface::test_workspace_members_are_the_three_uv_workspace_members`,
`TestAudit::test_audit_default_members_cover_all_three_workspace_members`,
`TestAudit::test_audit_evaluates_every_member_and_accounts_for_each_one`, and four `TestCli` cases.

**Why this matters more than a registration chore.** R29's consequence 5 says the member must be
in the image, and names **packet 01a's in-image conformance run (#139) as the instrument** that
proves it. That instrument enumerates the members it checks. `lorerunes` is not in that
enumeration and cannot be added without a contract change — so **the rider R29 attaches to its own
ruling does not currently cover the member the ruling mints.** The image will *contain*
`lorerunes` (§4, site 6); nothing will *prove* it does. This is CLAUDE.md's "THE RIDER IS PART OF
THE RULING" — the half of the ruling that is the gate. Routes to `tdd-contract`.

⚠ Note the shape of the blockage: **two of the seven test NAMES hardcode "three"**
(`..._are_the_three_uv_workspace_members`). A member count baked into a test's *name* is the same
stale-natural-language class as the prose I fixed in §deviation 2, one layer harder to see.

### 5b. `scripts/scratch_provenance.py::WORKSPACE_MEMBERS` — not blocked, not mine

```python
WORKSPACE_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")
```

This is the provenance guard behind `scripts/scratch_copy.sh` (CLAUDE.md #140 — "prove which tree
you are testing"). I checked: `scripts/test_scratch_copy.py` builds `MemberProvenance` objects
individually and does **not** pin the tuple, so adding `lorerunes` here appears safe. It is
outside my brief's six, so I flagged rather than did it. **Consequence if left:** a scratch copy
made for a future mutation proof will not verify `lorerunes`' provenance — the copy could be
importing the original checkout's `lorerunes` and the guard would not say so.

### 5c. `loremaster/loremaster/logging_setup.py::LORE_NAMESPACES` — not needed today

```python
LORE_NAMESPACES: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")
```

`lorerunes` emits no logs (it has no logger and, being stdlib-only, no logging config), so adding
it now would be speculative. **Named re-open trigger:** the day `lorerunes` acquires a
`logging.getLogger(__name__)`, its records will propagate to the root logger un-namespaced and
escape the redaction handler config — which, in a packet about secret leaks, is the wrong place to
discover a gap. Recorded so it is met deliberately.

### 5d. Not registered, and I believe correctly so
`loremaster/pyproject.toml` and `loresigil/pyproject.toml` do not declare
`lorerunes = { workspace = true }`. R29 says both *will* depend on it, but neither imports it yet.
`uv sync --all-packages` installs it regardless (proven below), and `mypy_path` resolves it, so the
stub needs no edge. **GREEN must add both edges when it wires the callers** — otherwise the image
carries `lorerunes` only incidentally via `--all-packages` rather than by declared dependency.

## 6. Other gates

**`uv sync --all-packages` — required receipt:**

```
Building lorerunes @ file:///home/ejprice/PycharmProjects/lore-pkt42/lorerunes
   Built lorerunes @ file:///home/ejprice/PycharmProjects/lore-pkt42/lorerunes
Installed 1 package in 72ms
 + lorerunes==0.1.0 (from file:///home/ejprice/PycharmProjects/lore-pkt42/lorerunes)
SYNC EXIT=0
```

```
import lorerunes: OK
  __file__ : /home/ejprice/PycharmProjects/lore-pkt42/lorerunes/lorerunes/__init__.py
  callable : True
from lorerunes import is_blank: OK
  calling it raises NotImplementedError: Not yet implemented
```

**ruff:** 2 errors, **both pre-existing** from pass 1 and already committed at `2439005` (the
`F401`s on the deliberately-unused `resolve_secret` imports, which GREEN consumes). **`lorerunes`
contributes zero.**

**mypy:** `typecheck: lorerunes OK` — "Success: no issues found in 3 source files". Repo total is
33 errors, distributed as 13 `test_secret_resolution_seam.py` · 6 `test_factory_secret_resolution.py`
· 4 `test_tei_prompt_name.py` · 3 `test_secret_typing.py` · 2 each `test_voyage_batch.py` /
`test_factory_voyage_context.py` / `test_factory.py` · 1 `embedding.py`. **Zero are attributable to
any file I created or touched this pass** — the 30→33 move since pass 1 comes from the contract
revision, not from `lorerunes`.

**Global collection:** `7390 tests collected`, no errors — the new `testpaths` entry resolves.
`lorerunes/tests` alone: `1 passed`.

**Deploy-skill suite:** `117 passed`, restored byte-exact after the §5a mutation proof.

**⚠ Housekeeping the lead owns, surfaced not fixed:**
- The contract revision (`test_secret_typing.py` +198, `test_factory_secret_resolution.py` +32)
  is **uncommitted**. CLAUDE.md: *"the working tree is never the ONLY copy of finished work"* —
  an adversary-graded contract living only in the working tree is one `git checkout --` from gone.
- Seven `REPORT-*.md` files sit untracked at the repo root, including my pass-1 report, which this
  report cites. Per CLAUDE.md they are archived with `git mv` into
  `docs/plans/v2/receipts/<date>-<packet>/`, never deleted — and a citation naming an untracked
  report is not yet a durable address.

## 7. What changed

My pass-2 edits (excluding the two pre-existing contract-revision test files):

```
 Containerfile        | 10 ++++++----
 pyproject.toml       |  5 +++--
 scripts/typecheck.sh | 12 ++++++------
 uv.lock              |  6 ++++++
 4 files changed, 21 insertions(+), 12 deletions(-)
```

plus 4 new files under `lorerunes/` (85 lines total, §3).

**Not done, per the brief:** no test file edited (the smoke test is a new file for a new package,
deviation 1) · `is_blank` not implemented · `resolve_secret` not wired to it · `loresigil`'s
validator not wired to it · `api_key_env` still present · `_resolve_api_key` / `MissingApiKeyError`
still present · `logging_setup.py` untouched · `scripts/search_score_survey.py` not migrated ·
nothing staged, nothing committed.
