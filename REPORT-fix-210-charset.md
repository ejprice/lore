# REPORT-fix-210-charset

## SUMMARY BLOCK

- `brief-base v6 read`
- **State: done-with-deviations.** #210 fixed, behaviourally pinned, mutation-proven; the
  class instrument shipped and mutation-proven; the repo-wide sweep is complete with an
  individual verdict per hit.
- **Commits (branch `pkt11i-floor-calibration-dark`):** `c32800d` (fix + pins),
  `8b1343e` (class instrument), `5e99409` (allowlist exemption upgraded from ARGUED to
  PROBED — §Decision 3). All **path-scoped** — see deviation 1 and §Commit hygiene.
- **DEVIATION 1 — ⚠ TWO SIBLING BUILDERS SHARE THIS WORKTREE.** Detected independently
  mid-run (the tree was CLEAN at `31d9e58` when I started; by 22:10 **21 tracked files I
  never touched were modified and 3 untracked files appeared**), then confirmed and named
  by the lead: `fix-207-jitter` (#207) and `fix-211-secrets` (#211). I committed **only my
  4 files by explicit path**, before the lead's warning arrived and by the same rule it
  states. **Both commits verified clean afterwards — see §Commit hygiene for the receipt.**
- **DEVIATION 2 — the repo-wide gates CANNOT be certified green by me**, because that tree
  is mid-migration: 244 mypy errors, 2 ruff `F821`, 65 test breakages, all in files I never
  touched. My files are individually clean; receipts in §Gates.
- **DEVIATION 3 —** I changed one pre-existing assertion,
  `test_agent_registry.py::TestAgentNamePatternConstant::test_pattern_accepts_legal_names`,
  from `.match` to `.fullmatch`. It was asserting a function production did not call.
- **Mutation-proof receipt (BOTH WAYS):** §Mutation proof — 5 expected-RED node ids declared
  from `--collect-only` **before** the run; mutation-landed evidence (md5 delta + the changed
  line); control leg green; result **`0` declared-reds-that-stayed-green, `0` unexpected reds,
  `0` declared-greens-that-reddened`**. Run in a `scratch_copy.sh` copy with asserted
  provenance so my siblings never saw a mutated `server.py`; restored byte-exact (`md5sum -c`
  → OK).
- **Class-sweep table:** §The class sweep — 5 candidate sites, 5 individual verdicts, 1 defect.
- **Residual answers:** §Residuals — (1) NO, the row cannot land: the store's Rust-regex
  ASSERT rejects it, so defense-in-depth held; (2) a newline in a SurrealQL literal is an
  ordinary character, no parse break. **This is an IDENTITY bug, not something sharper** —
  but with a real trust cost (§Residuals R1).
- **DECISIONS NEEDED:**
  1. **The concurrent agent in this worktree** — collision risk is live; who owns the tree?
  2. **`_validate_comms_charset`'s docstring + served error message are FALSE** (verified at
     `31d9e58`): they claim identities are "inlined into store queries"/"C3's live WHERE
     clauses". Every WHERE in `agents.py` and `briefs.py` uses **bound parameters**. I did
     not touch it — it is a served consumer surface and a separate concern. §Flag F1.
  3. Whether to file the AST gate's two allowlist entries as a finding, or leave them as
     the in-test record they now are.

---

## What changed

| file | change |
|---|---|
| `loremaster/loremaster/server.py` | `AppContext._validate_comms_charset`: `AGENT_NAME_PATTERN.match` → `.fullmatch`, + a docstring paragraph stating why the CALL carries the intent. |
| `loremaster/tests/test_comms_tool.py` | `TestCommsDispatchCharsetValidation`: 3 new parametrized pins (agent / session / brief name) × 2 values. |
| `loremaster/tests/test_agent_registry.py` | `TestAgentNamePatternConstant`: `"scout\n"`/`"scout\r\n"` added to the reject list; new `test_the_end_anchor_is_lenient_about_a_trailing_newline` (a KNOWN-BOUND pin); `test_pattern_accepts_legal_names` switched to `.fullmatch` (deviation 3). |
| `loremaster/tests/test_anchored_pattern_seam.py` | **NEW** — the class instrument (432 lines). |

### Why `.fullmatch` and not `\Z`

Both are correct. `.fullmatch` was chosen because it puts the requirement **in the call**,
where the reader of the guard sees it, and it survives any future edit of the pattern's
anchors. `\Z` puts it in the pattern, one file away in `agents.py`, where a later author
widening the charset can drop it without ever reading the call site. `AGENT_NAME_PATTERN`
is also referenced in the served tool description (`server.py`'s `comms` `agent` Field), so
its literal text is a consumer surface — leaving `$` there and hardening the call is the
lower-blast-radius choice.

---

## TDD receipts

### RED first, and RED for the RIGHT reason

The three pins were written before the fix and run against the unmodified build. All three
`\n` cases failed; both `\r\n` cases passed (they were never accepted — see §Negative control).
Crucially, each failure **demonstrates the store was reached**, which is the invariant this
test class is named for ("the store is never reached for a malformed identity"):

```
E   loremaster.agents.UnknownAgentError: agent 'scout\n' is not registered   <- agent name: guard passed it, ledger touched
E   Failed: DID NOT RAISE <class 'ValueError'>                                <- session: a newline-bearing session REGISTERED SUCCESSFULLY
E   loremaster.agents.UnknownAgentError: agent 'fixer-b' is not registered    <- brief name: guard passed it, ledger touched
3 failed, 7 passed in 0.61s
```

Not an import error, not a fixture error, not a collection error.

### GREEN after the minimal fix

```
.........................  (TestCommsDispatchCharsetValidation)
10 passed in 0.62s
```

### Mutation proof — BOTH WAYS, against a declared expectation

Re-run 2026-07-26 at lead request, under the packet-03b #194 discipline (`CLAUDE.md`,
*"FILING A RULE DOES NOT INSTALL IT"*), which landed after my first pass. My original proof
was **one-way** — it showed reds appeared, never that *every* declared red appeared. The
missing direction is the one that catches a mutation landing in **dead code**, i.e. a proof
that is vacuous rather than passing. `scripts/mutation_proof.py` does not exist on this
branch (it is on main at `bdb61c7`), so the discipline was applied by hand.

**Mutation under test:** `_validate_comms_charset`'s `AGENT_NAME_PATTERN.fullmatch` →
`.match` — i.e. reintroduce #210 exactly.

**1. Expectation declared BEFORE the run, from `pytest --collect-only`** (never transcribed
from failures — collecting names tests without running them, so the set is fixed before any
result exists). 49 ids collected → **5 declared RED, 44 declared GREEN**.

Declared RED:
```
test_comms_tool.py::TestCommsDispatchCharsetValidation::test_a_trailing_newline_agent_name_is_rejected[scout\n]
test_comms_tool.py::TestCommsDispatchCharsetValidation::test_a_trailing_newline_session_is_rejected[scout\n]
test_comms_tool.py::TestCommsDispatchCharsetValidation::test_a_trailing_newline_brief_name_is_rejected[scout\n]
test_anchored_pattern_seam.py::TestNoAnchoredPatternValidatedWithMatch::test_every_anchored_match_use_is_allowlisted
test_anchored_pattern_seam.py::TestScanCoverage::test_the_fixed_call_site_is_not_reported
```

The declared-GREEN 44 are load-bearing, not filler. Three members carry real claims:
* the three **`[scout\r\n]`** variants — if any reddened, my "negative control" was actually a
  second demonstration and this report's boundary claim would be wrong;
* all seven **`TestAgentNamePatternConstant`** ids — they exercise the PATTERN, not the guard,
  so a call-site mutation must not move them. Their staying green is the **empirical proof of
  flag F3**: those pre-existing pins are not load-bearing for #210 and could never have caught it;
* **`test_the_allowlist_carries_no_dead_entries`** — both exemptions must remain live.

**2. Isolation + provenance.** Run in a scratch copy via the blessed
`./scripts/scratch_copy.sh` — deliberately, because **two siblings share this worktree** and
mutating `server.py` in place would have handed them spurious failures. Provenance asserted
by the tool:

```
loremaster  -> /tmp/mp210_scratch_a/loremaster/loremaster/__init__.py
```

**3. Control leg** (an unmutated scratch must be green, or the diff means nothing):
`49 passed in 3.39s`.

**4. Evidence the mutation LANDED** — the #194 requirement itself. The edit asserted exactly
one target site, then: `md5sum -c` → `WARNING: 1 computed checksum did NOT match`, and
`server.py:4519` reads `if not AGENT_NAME_PATTERN.match(value):`.

**5. The both-ways diff:**

```
DECLARED RED 5 | ACTUAL RED 5

[A] DECLARED RED THAT STAYED GREEN (vacuous-proof direction): 0
[B] UNEXPECTED REDS (not declared):                           0
[C] DECLARED-GREEN THAT REDDENED:                             0

VERDICT: BOTH-WAYS CLEAN — every declared red reddened, nothing else did
```

**6. Restored and verified byte-exact:** `md5sum -c` → `server.py: OK`; `49 passed in 1.86s`.
The real worktree was **never mutated** — its `server.py` still reads `.fullmatch` at 4519 and
its only uncommitted diff remains `fix-211-secrets`' two hunks (`8 insertions, 2 deletions`,
unchanged across the whole proof).

**Conclusion: no declared pin stayed green. The pins are as strong as they read** — the
behavioural pins and the class gate both observe the mutation, and the class gate names the
offender (`loremaster/loremaster/server.py — AGENT_NAME_PATTERN`), so **it would have caught
#210**.

*(Scratch dir `/tmp/mp210_scratch_a` left in place, not deleted — flagging rather than
silently removing it. Disposable; `rm -rf` at will.)*

### Provenance (which tree was tested)

`loremaster.__file__ = /home/ejprice/PycharmProjects/lore-pkt11i/loremaster/loremaster/__init__.py`

No scratch copy was made — both mutation proofs mutated the real tree with a `cp -a` content
backup and restored from content (the always-sound alternative in brief-base §6).

---

## The class sweep

**Method (SAID OUT LOUD per brief-base §4): grep + AST, not lore.** lore's index watches the
MAIN checkout, not this worktree (#125), so a lore answer here would describe a different
tree. Greps were **bare and anchor-free** per the repo's sweep law: `re\.compile`,
`\.match(`, `fullmatch`, `\.search(`, and `\$["']` across `loremaster/`, `lorescribe/`,
`loresigil/`, `scripts/`, `skills/`.

Every `$`-anchored pattern in production, with an individual verdict:

| # | site (symbol) | pattern | call | verdict |
|---|---|---|---|---|
| 1 | `server.py::AppContext._validate_comms_charset` → `agents.py::AGENT_NAME_PATTERN` | `^[a-z0-9][a-z0-9_-]{0,63}$` | `.match` | **DEFECT — #210. FIXED** → `.fullmatch`. An ALLOW guard: `$`-leniency admits a second identity. |
| 2 | `server.py::AppContext.<create_many dispatch>` → `_TASK_ID_SHAPE_PATTERN` | `^[0-9a-f]{32}$` | `.match` | **BENIGN — and `.fullmatch` would be a REGRESSION.** An **INVERTED** guard: matching means *reject this batch key as id-shaped*, so `$`-leniency errs toward rejecting MORE. `TaskSpecItem.key` is an unconstrained `str`, so `'<32hex>\n'` can arrive; `fullmatch` would ACCEPT it as a batch-local key, re-creating exactly the id/key ambiguity the guard exists to prevent (a `blocked_by` of `'<32hex>'` passes through as a pre-existing task id, `'<32hex>\n'` resolves to a sibling's minted id — invisibly). **Allowlisted with this reason.** |
| 3 | `lorescribe/markdown.py::_Section`-builder (`_parse_sections`) → `_HEADING_LINE` | `^(#{1,6})\s+(.*\S)\s*$` | `.match` | **BENIGN — measured, not asserted.** Not a validator: an EXTRACTOR whose input is `source.splitlines()` output, which cannot contain a line terminator by construction, and nothing downstream treats the matched INPUT as an identity (only `group(1)`/`group(2)` are read). Measured 2026-07-25 over this repo's markdown corpus — **215 files, 65,786 lines, 0 disagreements** between `.match` and `.fullmatch` on match/no-match AND on extracted groups. **Left as `.match` deliberately + allowlisted**: churning a working parser in another package to satisfy a new gate is the false-positive tax that gets gates switched off. |
| 4 | `loremaster/config.py::SlugStr` → `SLUG_PATTERN` | `^[a-z0-9][a-z0-9_]*$` | pydantic `StringConstraints` | **BENIGN — probed, not assumed.** pydantic 2.13.4's default engine is `rust-regex`, whose `$` is end-of-haystack only. Probed live: `ProjectConfig(slug="proj\n")` and `slug="proj\r\n"` **both raise `ValidationError`**; `slug="proj"` accepted (positive control). Not in class. |
| 5 | `store/surreal_schema.py::_IDENTIFIER_CHARSET_ASSERT` → `_IDENTIFIER_CHARSET_PATTERN` | `^[a-z0-9][a-z0-9_-]{0,63}$` | SurrealQL `string::matches` | **BENIGN — probed live on the TEST store.** Rust regex; rejects `"scout\n"`. This is what saved us — see §Residuals R1. Not in class. |

**Not in the class (checked and excluded, individually):** `javascript.py::_RE_FUNCTION`,
`_RE_CLASS`, `_RE_EXPORT_NAMED`, `_RE_EXPORT_DEFAULT_ANON` and `markdown.py::_FENCE_LINE`
are `^`-anchored **prefix** matchers with no `$` — `.match` is the correct idiom.
`logging_setup.py::_BEARER_RE`/`_ASSIGNMENT_RE`/`_TOKEN_RE`, `search.py::_QUERY_TOKEN_PATTERN`/
`_DOTTED_IDENTIFIER_CHAIN_PATTERN`, `sanitise.py::CONTROL_CHAR_PATTERN`/`BACKTICK_RUN_PATTERN`,
`_txn.py::_BEGIN_COMMIT_KEYWORD_PATTERN`, `tei.py::_GIVEN_N_RE` carry no `$` and are used
with `.search`/`.sub`/`.findall`. There were **zero** `re.match(...)` module-level calls and
**zero** pre-existing `fullmatch` call sites in production.

### The AST invariant — built, and why it is worth it

`loremaster/tests/test_anchored_pattern_seam.py`. The brief allowed "not worth it" as an
answer; I judged it worth it because the class is mechanical, greppable, and *already had two
more instances*. Design decisions, all driven by repo law:

- **Deny by default, allowlist the safe.** Every `$`-pattern + `.match` pair fails unless it
  is in `_ALLOWED_ANCHORED_MATCH` **with a written, evidence-backed reason**. The safe set is
  2 entries; the forbidden set is unbounded. This is the shape CLAUDE.md's six-defeats table
  prescribes.
- **Repo-wide and cross-module.** The name→pattern map is built across ALL scanned trees
  before any call site is checked, because **#210's own shape is cross-module** (compiled in
  `agents.py`, called in `server.py`). A per-file scan could not have found it. Pinned by
  `test_a_cross_module_constant_is_caught`.
- **Coverage is a CHECKED variable, not an assumption** — a scanner that silently parsed
  nothing would pass vacuously forever. `TestScanCoverage` asserts all four packages were
  reached and that both shipped anchored constants still resolve **by name and by pattern
  text**.
- **5 positive controls** (`TestScannerFiresOnAKnownViolation`) prove it fires — including
  `test_an_annotated_assignment_is_caught`, because `AGENT_NAME_PATTERN` is an `AnnAssign`
  and a scan walking only `Assign` would have missed #210 entirely.
- **5 negative controls** (`TestScannerDoesNotRefuseHonestCode`) prove it does not refuse
  honest code — `fullmatch`, prefix-only patterns, `.search`, an **escaped** `\$` (a currency
  sign, not an anchor), and an unrelated `.match` receiver.
- **A stale-exemption test** (`test_the_allowlist_carries_no_dead_entries`) so the safe set
  cannot rot into a licence inherited by code rewritten later.
- **The threat model is written IN the instrument**, per CLAUDE.md: it catches the **honest
  developer** who reaches for the more familiar `.match`; it is **not** a boundary against an
  author who builds patterns at runtime. So *"a clever author evades it"* is not a defect
  here; *"an honest engineer's charset validator accepts a trailing newline"* is.
- **KNOWN BOUNDS stated, not implied** (module docstring): runtime-built pattern literals,
  patterns not bound to a module-level `Name`, name-keyed collisions across modules, and
  `.search` being deliberately out of scope.

---

## Residuals

### R1 — Does a `"scout\n"` registration land as a SEPARATE ledger row, end-to-end? **NO.**

Probed live against the **TEST store `ws://127.0.0.1:18000`** (never `:18500`; a throwaway
namespace/database, removed after). Three measurements:

```
string::matches('scout')       -> True
string::matches('scout\n')     -> False        <- Rust regex: `$` is end-of-haystack ONLY
ASSERT: CREATE name='scout'    -> ACCEPTED (row landed)     <- positive control
ASSERT: CREATE name='scout\n'  -> REJECTED (must conform to string::matches(...))
rows in store: ['scout']
```

So the chain was: the Python guard **passed** it → `_agent_row_id`'s
`uuid5("lore://agent/{session}/{name}")` minted a **genuinely different row id** → and the
**store's charset ASSERT stopped it**. Defense-in-depth held; **no duplicate identity could
land**, and this is not a data-corruption incident.

**But the severity is not zero, and it is not only cosmetic.** Two things were really broken:

1. **A stated invariant was false.** `TestCommsDispatchCharsetValidation`'s own docstring is
   *"the store is never reached for a malformed identity"*. For this shape the store **was**
   reached — proven by the RED tracebacks above (`UnknownAgentError` from the ledger).
2. **The served surface degraded, which is the consumer law's concern.** Instead of the
   guard's teaching `ValueError` — which names the pattern and says *"names are inlined into
   store queries and must stay in the safe charset"* — the calling agent got a raw store
   ASSERT violation from the wrong layer, teaching it nothing about the charset. The clients
   here are LLMs that learn the contract from what is served.
3. Note the asymmetry: `register` hits the ASSERT, but **lookup-only actions never do**.
   `heartbeat`/`brief_get` with `"scout\n"` sail past the guard into a bound-parameter SELECT
   that simply finds nothing, and the agent is told *"'scout\n' is not registered"* — for a
   name that is visually identical to one that IS. Safe, but maximally confusing.

### R2 — What does a newline do inside a live SurrealQL WHERE clause? **Nothing hostile.**

Two answers, because the premise turned out to be stale:

**(a) Production does not inline identities at all.** Every WHERE in `agents.py` and
`briefs.py` uses **bound parameters** (`$name_lookup`, `$session_filter`, `$row_id`,
`$edge_in`, …). Verified at `31d9e58`. See flag F1 — this contradicts the guard's own
docstring.

**(b) Probed anyway, with a hand-inlined literal** on the test store:

```
SELECT name FROM probe WHERE name = 'scout'     -> [{'name': 'scout'}]
SELECT name FROM probe WHERE name = 'scout\n'   -> []
```

A literal newline inside single quotes is an **ordinary character**: it did not terminate the
string, did not cause a parse error, and did not alter the statement's shape. It is **not an
injection primitive** — that would need a quote, which the charset already blocks.

**Verdict on the finding's own fork: this is an IDENTITY bug, not something sharper.**

---

## Gates

⚠ **Read deviation 2 first.** The repo-wide gates are RED for reasons that are not mine, and
I will not launder that. Receipts both ways:

| gate | repo-wide | my 4 files |
|---|---|---|
| `uv run ruff check .` | **2 errors** — `F821 Undefined name 'backoff'` ×2 in `scripts/token_survey.py`, from the other agent's in-flight `loresigil/backoff.py` extraction. | `All checks passed!` |
| `./scripts/typecheck.sh` | **244 errors in 30 files** — 134 `SecretStr` arg-type (the in-flight migration), the rest packet-03b contract RED (`_render_comms_send/drain/ack`, `limit_cap`, `to`/`grade` kwargs). | I found **1 error that WAS mine** (`_is_re_call` taking `expr \| None` from a bare `AnnAssign`) and **fixed it**. `uv run mypy loremaster/tests/test_anchored_pattern_seam.py` → `Success: no issues found in 1 source file`. Zero errors attributable to my edits in the other three. |
| `pytest -n auto` (my 3 suites) | `285 failed, 679 passed, 64 errors` | see the diff below |

**The failure diff against the enumerated baseline** (`docs/plans/v2/receipts/2026-07-24-packet11i/baseline-red-at-d0ee2be.txt`),
per the brief's instruction to use the LIST and never the count:

```
baseline failures in my 3 suites: 284
my failures:                      285
NEW (mine, not in baseline):      test_agent_registry.py::TestAgentRegistryConnectionLifecycle::
                                  test_recovers_on_the_next_call_after_a_dropped_connection
FIXED (baseline, now passing):    (none)
```

That single new failure is **not mine** — traced, not assumed:

```
loremaster/loremaster/store/_txn.py:982: in signin_credentials
    return {..., _SIGNIN_PASS_KEY: password.get_secret_value()}
E   AttributeError: 'str' object has no attribute 'get_secret_value'
```

`store/_txn.py` is one of the other agent's modified files. Classifying **every** deviation
by root cause: exactly **65** carry the `'str' object has no attribute 'get_secret_value'`
signature (1 failure + 64 errors) — matching the deviation count exactly. Every remaining
failure carries a packet-03b contract-RED signature (`_render_comms_send`/`_drain`/`_ack`,
`to`/`grade`/`seqs`/`peek` kwargs, `limit_cap`, `_MAX_DRAIN_LIMIT`).

**My new-failure exposure is ZERO.**

Green counts for the pins I own outright — final run, made **after** both commits and
**with the other agent's newest edits present in the tree** (they modified
`test_agent_registry.py` on top of my commit while I was writing this report; my additions
survived intact, verified by grep and by this run):

```
loremaster/tests/test_anchored_pattern_seam.py
  + test_comms_tool.py::TestCommsDispatchCharsetValidation
  + test_agent_registry.py::TestAgentNamePatternConstant
49 passed in 1.84s
```

---

## Decision 3, answered — the allowlist stays in-test, and one entry needed upgrading

Lead ruling: keep the two exemptions as the in-test record rather than a separate finding,
**provided each carries an evidence-backed reason inline** — *"if an entry's justification is
anything weaker than evidence, tell me and it becomes a finding instead."*

Auditing my own entries against that bar, **one passed and one did not**, and I am reporting
the failure rather than grading myself green:

| entry | justification as first written | verdict |
|---|---|---|
| `_HEADING_LINE` | **MEASURED** — 215 files / 65,786 lines, 0 `.match`/`.fullmatch` disagreements | already evidence ✓ |
| `_TASK_ID_SHAPE_PATTERN` | **ARGUED** — a correct-sounding chain about an inverted guard, but no measurement | **below the bar** → probed (`5e99409`) |

That second entry is exactly the *"it writes no row"* shape `CLAUDE.md` names as a banned
exemption rationale: plausible reasoning standing in for a measurement. Its load-bearing
assumption — that `'<32hex>\n'` can actually ARRIVE — was never tested. Now probed, with a
positive control:

```
TaskSpecItem.model_fields['key'] -> annotation `str | None`, metadata []      <- genuinely unconstrained
TaskSpecItem(key=<32hex>+NL) constructs -> '860049...b5de\n'                  <- the value CAN arrive
shipped .match : real id -> REJECTED as id-shaped | hostile -> REJECTED as id-shaped
if .fullmatch : real id -> REJECTED as id-shaped | hostile -> ACCEPTED AS KEY   <- the regression
```

The control is the half that makes it a probe rather than a hope: **a bare `uuid4().hex` is
REJECTED by BOTH legs**, so the instrument demonstrably discriminates and the divergence is
scoped to the trailing-newline value alone — it is not a check that simply says "no" to
everything. The reason string in `_ALLOWED_ANCHORED_MATCH` now carries this receipt inline.

**Neither entry becomes a finding.** Both are now evidence-backed at their one durable
address, per the ruling.

## Commit hygiene — the receipt (re-verified after the lead's shared-worktree warning)

**No commit of mine contains a sibling's work. This is measured, not asserted.** Both commits
were made with `git add <explicit path>` only; `git add -A`/`.`/`-u` and `git commit -a` were
never used. Full file sets:

```
c32800d fix(comms): #210 — the charset guard's `$` let a trailing newline through
 loremaster/loremaster/server.py         |  9 +++++-
 loremaster/tests/test_agent_registry.py | 31 +++++++++++++++++--
 loremaster/tests/test_comms_tool.py     | 55 +++++++++++++++++++++++++++++++++

8b1343e test(seam): the #210 CLASS instrument — `$`-anchored patterns are never `.match`ed
 loremaster/tests/test_anchored_pattern_seam.py | 432 +++++++++++++++++++++++++
```

**`server.py` — the file the lead flagged — carries exactly ONE hunk in `c32800d`:** the
docstring paragraph plus `AGENT_NAME_PATTERN.match` → `.fullmatch` at
`AppContext._validate_comms_charset`. `9 +++++-` = my 8 insertions and 1 deletion, nothing
else. **The commit is NOT mixed** and needs no disclosure of the kind the lead's rule
anticipates. `fix-211-secrets`' `server.py` edits (§F2a) landed in the working tree and remain
uncommitted there.

Sequencing note for the audit: I committed **before** the lead's warning arrived, having
detected the shared tree myself. The rule was already satisfied — the re-verification above
was run afterwards specifically to prove it rather than claim it.

## Flags (scope law — raised, not folded in, not buried)

**F1 — `_validate_comms_charset`'s docstring AND its served error message are FALSE.**
(Verified at `31d9e58`; I did **not** change them.)

The docstring says all three identities *"are inlined into C3's live WHERE clauses"*; the
error message the guard serves to agents says *"names are inlined into store queries and must
stay in the safe charset"*. **Neither is true of the current code.** Every WHERE in
`agents.py` and `briefs.py` binds parameters. The charset is still worth enforcing — the row
id is a `uuid5` over the name, and the store ASSERT independently demands it — but the stated
*reason* names a mechanism that does not run.

This is precisely the class CLAUDE.md calls this repo's most expensive: served English that
promises a mechanism it does not perform, read by an LLM that learns the contract from it.
I left it alone because (a) it is a **served consumer surface** — changing what agents are
taught is a separate, ruled concern, not a drive-by edit inside a `.match`→`.fullmatch`
commit, and (b) `test_comms_tool.py` asserts `"safe charset"` appears in the message, so a
reword touches the contract. **Recommend: a one-concern follow-up that re-derives the
justification from the actual mechanism** (uuid5 identity + the store ASSERT), rather than
leaving prose that a future author will trust when deciding whether the guard still matters.

**F2 — the shared worktree (deviation 1), restated because it is the operational risk.**
Timeline: tree clean at start; `git status` empty. By 22:10:52, 21 tracked files modified and
3 untracked added, and the set kept growing during my run (`_surreal_harness.py`,
`scripts/token_survey.py`, `calibration/engine.py` appeared between two consecutive checks).
Lead-confirmed owners: **`fix-207-jitter`** (#207 shared jittered backoff — `loresigil/backoff.py`,
`calibration/*`, `scout.py`, `loresigil/resilient.py`, `scripts/token_survey.py`, `uv.lock`)
and **`fix-211-secrets`** (#211 `SecretStr` + traceback redaction). The half-applied `SecretStr`
migration is why the tree fails to type-check and 65 tests error. **Nobody should run
`git checkout --`, `git stash`, or `git commit -a` in this worktree** — their work exists only
in the working tree.

**⚠ F2a — one correction to the lead's warning, so the cold audit looks in the right place.**
The lead predicted the `server.py` overlap would be with **`fix-207-jitter`**. Measured at
`8b1343e`+, the uncommitted `server.py` hunks are **`fix-211-secrets`'** work, not #207's:
they are `resolve_secret(...).get_secret_value()` unwraps for `surreal_user` and
`CalibrationEngine.api_key`, whose comments cite `#211` and `test_secret_typing.py`. Neither
hunk is anywhere near `_validate_comms_charset`. So the predicted collision did not
materialise from the predicted source, and **did not materialise at all** for my change.

**F2b — I applied no repo-wide auto-fixes.** The lead flagged that `fix-211-secrets` ran
`ruff check --fix .` before noticing the collision. For the record: every ruff invocation I
made was **read-only** — `uv run ruff check .` (to see the tree's state, reported in §Gates)
and `uv run ruff check <my 4 paths>`. I never passed `--fix`, so nothing in this tree was
reformatted by me.

**F3 — the pre-existing pattern pin tested a function production did not call.**
`test_pattern_accepts_legal_names` asserted `AGENT_NAME_PATTERN.match(value) is not None`
while the guard called `.match`, and `test_pattern_rejects_illegal_names` asserted
`.fullmatch(value) is None` — i.e. the *reject* pin was already using the strict function,
so **it could never have caught #210**: every one of its five fixtures is rejected by both
functions. A pin that exercises a stricter function than production is a pin that certifies a
build nobody ships. Fixed (deviation 3) and pinned going forward by
`test_the_end_anchor_is_lenient_about_a_trailing_newline`, which asserts the *gap between the
two functions* explicitly and goes RED if the pattern's anchor is ever changed to `\Z`.

---

## Negative control (stated, so it is not mistaken for a second demonstration)

`"scout\r\n"` was carried through every pin, but it **was already rejected before the fix**:
Python's `$` is lenient about `\n` only, so `.match("scout\r\n")` was always `None`. It
demonstrates nothing about #210. It is kept as a **boundary pin** — a later "tidy-up" that
reaches for `re.MULTILINE` (under which `$` matches before *every* newline) goes RED there.
Measured 2026-07-25:

```
'scout'      match=True   fullmatch=True
'scout\n'    match=True   fullmatch=False    <- the defect
'scout\r\n'  match=False  fullmatch=False    <- negative control
'scout\nx'   match=False  fullmatch=False
'scout\r'    match=False  fullmatch=False
```
