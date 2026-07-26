# REPORT-coldaudit-fixwave — independent grading of the #210 / #207 / #211 fix wave

## SUMMARY BLOCK

- `brief-base v6 read`
- **VERDICT: NO-GO.** Three independent reasons, any one sufficient: (1) **the tree was never
  frozen** — HEAD moved SIX times during this audit and the branch tip is not the commit I was
  asked to grade; (2) a **confirmed, gate-invisible 100% breakage** shipped into
  `scripts/search_score_survey.py` and is **still live at the newest tip**; (3) the branch tip is
  **RED on a test this wave itself broke**, under a commit message claiming baseline parity.
- **State: done.** Every gate re-run independently on FROZEN `git archive` snapshots; four
  mutation proofs re-done from scratch with declared-before-run sets diffed both ways; both #210
  allowlist exemptions re-derived; #211's traceback claim verified at the original base; all three
  findings re-graded against source.
- **Deviation 1 — MY BRIEF'S PREMISE WAS FALSE BY THE TIME I READ IT.** Brief: *"HEAD `2bc28cf`,
  the wave is 14 commits."* Measured: `git status` was CLEAN at 22:42 and had **10 modified files
  by 22:52**; HEAD then moved `2bc28cf → 20ea39a → 0b851a3 → b4d1f1a → f0b6c99 → 98692d8 →
  883ab7f`. The wave is **20 commits**, not 14. See §0 — read it before anything else.
- **Deviation 2 — I therefore measured FROZEN SNAPSHOTS, not the worktree** (`git archive <sha> |
  tar -x` into a `scratch_copy.sh` copy). Every number below names its commit. I never ran `git`
  with cwd inside the copy (a worktree `.git` is a FILE naming the ORIGINAL gitdir — #134 — so a
  write there mutates the real tree).
- **Deviation 3 — lore's index watches the MAIN checkout, not this worktree (#125).** Every
  structural sweep here is **grep/Read**, said out loud per §4. `lore_findings` was used for the
  findings ledger (a store read, unaffected by index topology).

### Gate results — FROZEN tip `0b851a3`, measured 2026-07-26 (all counts mine)
| gate | result |
|---|---|
| `./scripts/typecheck.sh` | **109 errors in 3 files** — `test_comms_tool.py` (102), `test_comms_promise_registry.py` (6), `test_comms_wiring.py` (1). **All packet-03b contract RED. Zero in any wave-touched production file.** |
| `uv run ruff check .` | **All checks passed** |
| `uv run pytest -n auto -q` | **395 failed, 6223 passed, 17 skipped, 3 xfailed** in 199.77s |
| `uv run pytest scripts/` | **150 passed** (this is what the merge target's `testpaths` will start gating) |
| at `2bc28cf` (brief's HEAD) | **395 failed, 6223 passed, 17 skipped, 3 xfailed** in 276.25s |

### Failure attribution — every deviation, 1-for-1 (no "the rest are pre-existing")
| node id | `2bc28cf` | `0b851a3` | root cause |
|---|---|---|---|
| the 394 enumerated baseline ids | RED | RED | inherited packet-03b contract RED. Set **identical both ways**: zero drift, zero newly-fixed. |
| `test_logging_setup.py::TestExceptionRenderingIsEmittedAndScrubbed::test_the_wire_field_name_is_exactly_exc_info` | **RED** | GREEN | **DEFECT C** — `2bc28cf` shipped a pin asserting `EXC_FIELD == "exc_info"` while production said `"exc"`. Fixed by `20ea39a`. |
| `test_calibration_counting.py::TestRequestShapeParity::test_wire_shape_is_byte_identical_to_survey_counter` | GREEN | **RED** | **DEFECT B** — `0b851a3` widened `token_survey.ClaudeTokenCounter.__init__` to `SecretStr` and left an in-`testpaths` consumer passing `str`. |

### Confirmed defects
- **A — `scripts/search_score_survey.py::_make_store` is 100% broken. LIVE AT THE NEWEST TIP.** §2
- **B — regression at the tip + a FALSE green claim in `0b851a3`'s own commit message.** §3
- **C — the commit I was asked to grade for merge (`2bc28cf`) was not green.** §4

### Findings grading
- **#211 — amended version CORRECT**, independently re-verified at `d0ee2be`. §7.1
- **#199 — the 150-vs-50 correction is CORRECT; its standing question is STALE.** The merge target
  already added `scripts` to `testpaths` (`c9431ae`). §7.2
- **#210 — STILL WRONG, and still `open`.** Its load-bearing "inlined into live WHERE clauses"
  claim is FALSE — every identity comparison is a bound `$param`. The same falsehood is in a
  **SERVED error message**. §7.3

### Mutation-proof receipts — `loremaster.__file__ = /home/ejprice/scratch-coldaudit-base/loremaster/loremaster/__init__.py`
M1 · M1b · M2 · M3 in §5. All restores verified byte-exact by `md5sum -c`.

### Decisions needed
1. **Freeze the branch before any merge decision.** A GO cannot be issued against a moving tip.
2. **Defect A** — fix `search_score_survey.py`, or rule it accepted-and-pinned. §2.4 has the edit.
3. **Defect B** — fix `test_calibration_counting.py`'s fixture; the tip is RED without it.
4. **#210 must be corrected and closed**, and the three false in-code claims (one SERVED) fixed. §7.3
5. **#199 should be resolved/superseded** — the operator call it is waiting on was already made on main.
6. **`scripts/` belongs in `typecheck.sh`'s MEMBERS.** Both Defect A and Defect B live in the hole
   that absence creates. `fix-211-secrets` flagged the same thing and did not act (correctly — it
   is the canonical gate runner).
7. `search_score_survey.py` hard-codes `ws://127.0.0.1:18500/rpc` = **PRODUCTION lore-surreal**.
   Pre-existing, outside this wave, raised under scope law. §8.1

---

## §0. THE TREE WAS NEVER FROZEN — read this before any number below

My brief said: *"branch `pkt11i-floor-calibration-dark`, HEAD `2bc28cf`. The wave is commits
`c32800d..2bc28cf` (14 commits)."*

Measured, in this audit's own tool output:

| time (2026-07-25) | observation |
|---|---|
| 22:42 | `git status --short` → **empty**. HEAD `2bc28cf`. Audit begins; full `pytest -n auto` launched. |
| 22:52 | `git status --short` → **10 modified files**. mtimes 22:46:41 … 22:51:23 — i.e. **during my suite run**. |
| 22:53 | HEAD is **`0b851a3`** — two new commits (`20ea39a`, `0b851a3`). |
| 23:02 | HEAD is **`883ab7f`** — three more (`b4d1f1a`, `f0b6c99`, `98692d8`, `883ab7f`). |

A sibling (`fix-211-secrets`) was still building. That is not a criticism of the builder — it is a
statement about what an audit of this tree can mean. **My first full-suite run straddled a source
edit**, which is exactly how I found Defect C: the run captured `EXC_FIELD == "exc"` while the file
on disk had already become `"exc_info"`, so the test passed in isolation minutes later and failed
in the run. A green-at-a-glance re-run would have called that flaky and moved on.

**Everything measured after 22:53 in this report was measured on a frozen `git archive` snapshot**,
never on the worktree. The two authoritative trees are `2bc28cf` (my brief's target) and `0b851a3`
(the last tip carrying a code change; `b4d1f1a..883ab7f` are docs-only, verified by
`git diff --name-only 0b851a3..883ab7f` → `REPORT-fix-211-secrets.md` alone).

**A GO from me would have named a commit that is no longer the branch tip.** That alone is the
NO-GO; the two code defects below are why it matters rather than being a formality.

---

## §1. What I actually verified (coverage, so a clean claim is legible)

Re-run independently, never read from a report: `./scripts/typecheck.sh`, `uv run ruff check .`,
`uv run pytest -n auto` at two commits, `uv run pytest scripts/`. Re-derived from source: every
`resolve_secret` caller (13), every `.signin(` call site (13), every `get_secret_value()` unwrap
(11), every `jittered_backoff_delay` caller (5), every `WHERE` clause in the three comms store
modules (27). Re-done from scratch: four mutation proofs. Re-probed empirically against the live
**TEST** store `ws://127.0.0.1:18000` (never `:18500`): SurrealDB signin with a `SecretStr`
username, with a `str` control. Re-derived: both #210 allowlist exemptions, the base-`d0ee2be`
formatter behaviour, the scrubber's real coverage under hostile input, and all three findings.

---

## §2. DEFECT A — `scripts/search_score_survey.py::_make_store` is 100% broken (LIVE at `883ab7f`)

### 2.1 The defect
The wave changed `config.resolve_secret` to return `SecretStr`. Four call sites were updated to
unwrap the **username** (`index/cli.py`, `scout.py`, `server.py`, `scripts/snapshot_gc.py`, each
gaining `.get_secret_value()` plus an identical explanatory comment). One was not:

```python
# scripts/search_score_survey.py::_make_store
        user=resolve_secret(DEFAULT_SURREAL_USER_ENV),      # <- now a SecretStr
        password=resolve_secret(DEFAULT_SURREAL_PASSWORD_ENV),
```

`SurrealStore.__init__` is typed `user: str, password: SecretStr`. The `SecretStr` username flows
into `store._user`, then into `_txn.signin_credentials(user=…)`, which does **not** unwrap the
username by design — so the SDK receives a `SecretStr` object where the wire needs a string.

### 2.2 Measured, with a positive control (TEST store `ws://127.0.0.1:18000`)
```
store._user  type = SecretStr  repr = SecretStr('**********')
signin payload = {'username': ('SecretStr', "SecretStr('**********')"), 'password': ('str', "'spikeroot'")}

control  (user=str 'root')        -> SIGNIN OK
defect   (user=SecretStr('root')) -> BufferError: ('no encoder for type ', <class 'pydantic.types.SecretStr'>)
```
The control is the point: the probe demonstrably distinguishes a working signin from a broken one,
and the only variable is the username's type.

### 2.3 Why NOTHING caught it — this is the interesting half
Three independent gates are each individually blind, and their union is still blind:

1. **mypy never sees the file.** `scripts/typecheck.sh` runs `MEMBERS=(lorescribe loresigil
   loremaster)`. `scripts/` is not a member. A `SecretStr` passed to a `user: str` parameter is a
   textbook mypy error that no one runs mypy to find.
2. **pytest never sees the file on this branch.** `pyproject.toml` `testpaths` here is
   `lorescribe/tests, loresigil/tests, loremaster/tests`.
3. **Even the merge target's new `scripts/` gate cannot see it.** I ran it:
   `uv run pytest scripts/` at `0b851a3` → **150 passed**. Because
   `scripts/test_search_score_survey.py` line 550 does
   `monkeypatch.setattr(sss, "_make_store", lambda: store)` — **the one test near the broken
   function replaces the broken function.** *The fixture guarantees the one condition under which
   the bug is invisible* (`CLAUDE.md`, THE TEST ENVIRONMENT IS A FICTION), reproduced exactly.
4. **The wave's own new ∀ instrument is blind by construction.** `loremaster/tests/
   test_secret_typing.py` (14 passed at `0b851a3`, with `scripts/` in its reach as of `0b851a3`)
   pins *"no bare `str` where a secret belongs"*. Defect A is the **inverse** direction — a
   `SecretStr` where a raw `str` is required. A type migration has two failure directions and the
   ∀ pin quantifies over one. **That is the missing pin**, and it is worth more than the one-line
   fix: `mypy` over `scripts/` would give it for free (see decision 6).

`0b851a3`'s commit message says *"Half A now covers every secret in `loremaster/` AND `scripts/`:
zero bare-`str` credentials, ∀-pinned across both."* The first clause is true. The sentence reads
as *"`scripts/` is now correct"*, and `scripts/` is not.

### 2.4 The edit I would make (not made — outside my writable set)
```python
        user=resolve_secret(DEFAULT_SURREAL_USER_ENV).get_secret_value(),
```
matching the four siblings verbatim. **But the fix that matters is decision 6**, because this site
was found by reading, not by any instrument, and reading does not scale to the next one.

---

## §3. DEFECT B — a regression at the tip, and a green claim that is false

`loremaster/tests/test_calibration_counting.py::TestRequestShapeParity::test_wire_shape_is_byte_identical_to_survey_counter`
is **RED at `0b851a3`** and was **GREEN at `2bc28cf`**. Reproduced in the frozen copy
(`loremaster.__file__` asserted inside it):

```
survey_counter = ts.ClaudeTokenCounter(api_key, model=model, client=sync_client)
  api_key = 'sk-parity-fixture'
      "x-api-key": api_key.get_secret_value(),
E     AttributeError: 'str' object has no attribute 'get_secret_value'
scripts/token_survey.py:764: AttributeError
```

`0b851a3` widened `scripts/token_survey.py::ClaudeTokenCounter.__init__` to `api_key: SecretStr`;
this consumer lives in `loremaster/tests/` — **inside `testpaths`** — and still passes a bare `str`.
It is the exact failure mode `0b851a3`'s own message describes for the sites it fixed
(*"would have died at `signin_credentials` with `'str' object has no attribute
'get_secret_value'`"*), reproduced in the opposite direction by the fix itself.

**The false claim.** `0b851a3`'s message states: *"Full suite with tracebacks: 394 failed / 6223
passed, failure set identical to the enumerated baseline."* My independent frozen run of that exact
commit: **395 failed / 6223 passed**. The passed-count matches to the unit and the failure set
differs by exactly this one id — consistent with the suite having been run and then one more file
edited, which is precisely the §0 hazard. Under this repo's law a green claim is grounded by a
re-run, and this one was not.

---

## §4. DEFECT C — `2bc28cf`, the commit I was asked to grade, shipped a RED test

At `2bc28cf`: `test_logging_setup.py::TestExceptionRenderingIsEmittedAndScrubbed::
test_the_wire_field_name_is_exactly_exc_info` asserts `EXC_FIELD == "exc_info"`; production carried
`EXC_FIELD = "exc"`. `AssertionError: assert 'exc' == 'exc_info'`. 395 failed vs the 394 baseline.

Fixed by `20ea39a` eleven minutes later, and `20ea39a` is a genuinely good commit — its own message
records the real lesson (all 34 existing assertions index `parsed[EXC_FIELD]`, so they follow the
constant wherever it points and the **served name had no pin at all**). I report it because my
brief presented `2bc28cf` as the merge candidate, and it was not green.

---

## §5. My own mutation proofs — declared before the run, diffed BOTH ways

All four in a `./scripts/scratch_copy.sh` copy with asserted provenance. Receipt, printed in every
run: `loremaster.__file__ = /home/ejprice/scratch-coldaudit-base/loremaster/loremaster/__init__.py`.
Node ids taken from `pytest --collect-only` **before** any result existed. Backups by `cp -a`
content; every restore verified `md5sum -c → OK`.

### M2 — POSITIVE CONTROL for #207's sharing pin (does it fire at all?)
Mutation: `scout.CommandSubscriber._backoff` keeps a private multiplicative copy.
Declared RED (written before the run): `test_command_subscriber_shares_the_policy`,
`test_EVERY_declared_site_draws_from_the_mutated_policy`.
Observed: **exactly those two.** 0 unexpected reds, 0 declared-reds-that-stayed-green.
→ The sharing pin genuinely discriminates.

### M3 — #210's fix and class instrument
Mutation: `AGENT_NAME_PATTERN.fullmatch` → `.match` (one occurrence, anchor count asserted = 1).
Declared RED: the 2 class-instrument pins + the 3 behavioural trailing-newline pins.
Observed: **exactly those five** — `test_every_anchored_match_use_is_allowlisted`,
`test_the_fixed_call_site_is_not_reported`, and `test_a_trailing_newline_{agent_name,session,
brief_name}_is_rejected[scout\n]`. 0 unexpected, 0 declared-green.
→ The #210 fix and its instrument are load-bearing. **Confirmed.**

### M1 / M1b — MY ATTACK ON #207's CENTRAL CLAIM, and its honest outcome
`test_backoff_seam.py::_DECLARED_SITES` names
`loremaster.calibration.engine.CalibrationEngine._probe_loop`. Its driver
(`_drive_calibration_engine`) calls `engine._backoff_delay(attempt)` — a **different method**. So I
attacked the seam one level up: leave `_backoff_delay` intact and make `_probe_loop` stop calling it.

- **M1** — `_probe_loop` hand-rolls a deterministic ladder, written **multiplicatively** so the
  perimeter's own KNOWN BOUND keeps it invisible and the sharing question is isolated.
  Declared: sharing pins GREEN (the gap), `test_backoff_doubles_and_caps` RED. **Observed exactly
  that.**
- **M1b** — the sharper build: a **statistically equivalent** private full-jitter copy
  (`random.uniform(0, min(window, cap))`), i.e. #102's shape verbatim. I predicted the behavioural
  pin might also go green. **It did not** — `test_backoff_doubles_and_caps` reddened again.

**Both times `test_backoff_seam.py` was entirely GREEN — including
`test_EVERY_declared_site_draws_from_the_mutated_policy`, the pin whose whole docstring is that
coverage is a CHECKED VARIABLE.** So `_DECLARED_SITES`'s `…_probe_loop` entry names a site that pin
does not reach.

**But the claim survives, and I will not manufacture a finding out of it.** The real coverage
exists elsewhere and is stronger:
`test_calibration_engine.py::TestEndpointLifecycle::test_backoff_doubles_and_caps` drives the REAL
`_probe_loop` end-to-end through a recording wrapper on the shared policy and asserts the exact
per-attempt `(attempt, base_s, cap_s)` sequence — which is why it caught both mutations, including
the statistically-equivalent one. `_drive_calibration_engine`'s docstring already points at that
test by name. **Residual R1 (§8.2): the `_DECLARED_SITES` label overstates one pin's reach.** The
#207 sharing invariant itself: **CONFIRMED**.

---

## §6. Attacking the #210 gate: what could an honest developer write tomorrow?

Probed against the shipped `_anchored_match_uses`, with the verbatim #210 shape as a control
(CAUGHT). Each shape below was then checked to confirm it really carries the hole
(`.match("scout\n")` → True, `.fullmatch` → False):

| shape | scan | hole present | covered by a stated KNOWN BOUND? |
|---|---|---|---|
| `re.compile(r"^[a-z]+$")` + `.match` (control) | **CAUGHT** | yes | — |
| `re.compile(r"^([a-z0-9_-]+$)")` + `.match` | **MISSED** | **yes** | **NO** |
| `re.compile(r"^(?:[a-z0-9_-]+$)")` + `.match` | **MISSED** | **yes** | **NO** |
| `agents.AGENT_NAME_PATTERN.match(v)` (module attr) | **MISSED** | yes | partially |
| `NAME_TEXT = r"…$"` ; `re.compile(NAME_TEXT).match(v)` | **MISSED** | yes | partially |

**The two unstated ones are the finding.** `_ends_with_end_anchor` is a *suffix* test
(`pattern.endswith("$")`), so a `$` inside a trailing group is invisible — and wrapping a validator
pattern in a capturing group is an ordinary thing an honest author does. The instrument's own law
(`CLAUDE.md`: *when you cannot close a hole, PIN it*) says these should either be seen or pinned
with a re-open trigger; today they are neither.

The module-attribute miss is only *partially* covered: the stated bound says *"a compiled pattern
stored somewhere other than a module-level NAME (a dict value, a list element, an instance
attribute)"* — a **module** attribute is none of those, and `from loremaster import agents;
agents.AGENT_NAME_PATTERN.match(v)` is this repo's own mandated idiom (`loresigil/backoff.py`'s
docstring makes module-attribute access *load-bearing*).

**Both exemptions re-derived, and both hold:**
- **`_TASK_ID_SHAPE_PATTERN` — SOUND, evidence-backed.** Verified at source: `server.py`'s
  `create_many` does `if item.key is not None and _TASK_ID_SHAPE_PATTERN.match(item.key): raise
  ValueError(...)` — genuinely inverted, so `$`'s leniency errs toward rejecting more. Re-probed:
  `TaskSpecItem.model_fields["key"]` is `str | None` with metadata `[]` (unconstrained);
  `.match(<32hex>+NL)` → True (shipped code rejects it), `.fullmatch(<32hex>+NL)` → False (would
  accept it as a key); **control**: a bare `<32hex>` is rejected by both, so the probe
  discriminates and the difference is scoped to exactly the trailing-newline value. Nit: the
  exemption's prose says *"TaskSpecItem(key=<32hex>+NL) constructs"* — it also needs `subject` and
  `description`, so the literal sentence is imprecise; the substance holds.
- **`_HEADING_LINE` — SOUND.** Verified at source: `lorescribe/markdown.py::_parse_sections`
  iterates `source.splitlines()` and calls `_HEADING_LINE.match(line)`. `splitlines()` output
  cannot contain a line terminator, so `$` ≡ end-of-string and `.match` ≡ `.fullmatch` there. The
  65,786-line corpus measurement is corroboration, not the load-bearing argument, and the argument
  itself is correct.

---

## §7. Findings, graded

### 7.1 #211 — the amended framing is CORRECT
The lead's correction (that the scout was right and the lead's own reframe was wrong — tracebacks
were **discarded**, not merely un-scrubbed) is independently confirmed. At `d0ee2be`,
`JsonFormatter.format` builds `{ts, level, logger, msg}` + flattened extras and returns; it never
calls `super().format()` and never reads `exc_info`/`exc_text`. Measured emission at base:

```
BASE json output: {"ts": "...", "level": "ERROR", "logger": "base.probe", "msg": "store.connect.failed"}
BASE contains Traceback: False
```

And at the tip, a traceback **is** emitted and **is** scrubbed — verified with a positive control
(a plain exception, to prove the path is exercised at all) alongside the secret-bearing cases, so
this is not the *"stopped finding the secret because it stopped exercising the path"* failure the
brief warned about. Both halves shipped together, correctly. **#211's fix and its framing: sound.**

### 7.2 #199 — the correction is CORRECT; the finding is STALE
The 50→150 re-derivation is right (`uv run pytest scripts/` collects and runs **150** — my own run).
But the amendment closes with *"the operator's call on whether `scripts/` joins testpaths … still
stands."* **It does not.** The merge target `feat/surreal-unification` already added `"scripts"` to
`testpaths` at `c9431ae` (*"the guards were ungated"*) — a commit that is **not** an ancestor of this
branch (`git merge-base --is-ancestor c9431ae HEAD` → NO; merge-base is `d0ee2be`). So at merge,
`scripts/` becomes gate-blocking. I measured what happens: **150 passed** at the wave tip — the gate
will not block. Which is exactly why Defect A ships silently. **#199 should be resolved/superseded,
with that cost re-priced.**

### 7.3 #210 — STILL WRONG, and still `open`
Two problems, and the second is the serious one.

**(a) Status.** #210 is `open` in the ledger although the fix landed at `c32800d` and the class
instrument at `8b1343e`. `#199` and `#211` were both moved to `acknowledged`; #210 was not.

**(b) Its load-bearing claim is FALSE, and was never amended.** The body asserts the guard's purpose
is injection defence because identities are *"inlined into C3's live WHERE clauses"*, and lists as
consequence **(b)**: *"The charset guard's injection posture is defeated for the one character it
most needs to exclude in an inlined-query context."*

I enumerated **every** `WHERE` in `agents.py`, `briefs.py` and `messages.py` (27 occurrences) and
searched for any f-string interpolating an identity **value** into a query. Result: **every
identity comparison is a bound `$param`** — `$_NAME_LOOKUP_PARAM`, `$_SESSION_FILTER_PARAM`,
`$agent`, `$names`, … — and **nothing is inlined**. Consequence (b) is not merely overstated; it
does not exist. #210 is an **identity/impersonation** bug, which consequence (a) states correctly.

`fix-210-charset` found this independently and raised it as its Flag F1 / decision-needed 2. It was
right, it correctly did not edit outside its writable set, and nothing was done with it. The same
falsehood sits in three places in code, **one of them a SERVED surface an agent consumer reads**:

| location | text |
|---|---|
| `server.py::_validate_comms_charset` — **the raised `ValueError`** | *"names are inlined into store queries and must stay in the safe charset"* |
| the same method's docstring | *"all three are inlined into C3's live WHERE clauses"* |
| `agents.py` module comment (above `_COL_SESSION`) | *"`agent.session` is inlined as a literal into C3's live WHERE clauses"* |

This is `CLAUDE.md`'s named class verbatim — *natural-language surfaces whose consistency with code
no gate checks* — and a **TRUST DOCTRINE** violation: served teaching prose that does not match
measured behaviour. An agent that reads that error learns a false mechanism and will reason from it.
**A finding that is still wrong after being corrected is worse than one nobody touched**, and this
one was never touched at all.

---

## §8. Residuals and everything else I noticed (scope law — the operator decides)

### 8.1 `search_score_survey.py` points at PRODUCTION
`DEFAULT_SURREAL_URL: str = "ws://127.0.0.1:18500/rpc"`. `:18500` is **production `lore-surreal`**;
`:18000` is the test store. Pre-existing, outside this wave, and the file has no gate — but a survey
script that defaults to prod is worth a ruling.

### 8.2 R1 — `_DECLARED_SITES` overstates one pin's reach (§5, M1/M1b)
The entry `loremaster.calibration.engine.CalibrationEngine._probe_loop` is certified by a driver
that reaches `_backoff_delay`. Real coverage exists (`test_backoff_doubles_and_caps`, mutation-proven
by me twice). Suggested minimal fix: rename the declared entry to
`…CalibrationEngine._backoff_delay` and add a one-line pointer to the test that covers `_probe_loop`
— so the coverage claim matches the coverage.

### 8.3 The scrubber's real coverage, measured (pre-existing regexes, newly load-bearing)
The wave changed no scrubber pattern (`git diff d0ee2be..0b851a3 -- logging_setup.py` shows zero
changes to `_BEARER_RE` / `_ASSIGNMENT_RE` / `_TOKEN_RE` / `_ENTROPY_BITS_THRESHOLD`) — but it newly
routes **tracebacks** through them, so their gaps now guard a much larger surface. Measured through
the real `RedactingFilter` + `JsonFormatter`:

| input in a traceback | outcome |
|---|---|
| `api_key=<long anthropic key>` | REDACTED ✓ |
| bare `<long anthropic key>`, no label | REDACTED ✓ (entropy backstop) |
| `{'x-api-key': '<long key>'}` dict repr | REDACTED ✓ (entropy backstop; the *labelled* rule misses it — `'` sits between the label and the `:`) |
| `password=spikeroot` | REDACTED ✓ |
| **`Authorization: Basic cm9vdDpzcGlrZXJvb3Q=`** | **LEAKS** — emits `Authorization: ***REDACTED*** cm9vdDpzcGlrZXJvb3Q=` |
| **`ws://root:spikeroot@127.0.0.1:18000/rpc`** | **LEAKS** |
| bare `spikeroot`, unlabelled | **LEAKS** (inherent to entropy scrubbing) |

The `Basic` case is a genuine bug worth naming: `_ASSIGNMENT_RE` redacts only the **first** `\S+`
after the label, i.e. the **scheme**, leaving the credential in the clear. Any `<label>: <scheme>
<secret>` shape leaks. `_scrub_text`'s own docstring advertises `Authorization: Bearer
***REDACTED***` — which works only because `_BEARER_RE` runs first and is Bearer-specific, so the
docstring's example is the one auth scheme that happens to be covered. **`SecretStr` is the real
defence and it is sound; this is the backstop, and the backstop has a named hole.**

### 8.4 `counting.py` stores an unwrapped secret in a long-lived attribute
`AsyncClaudeTokenCounter.__init__` unwraps into `self._headers` — an instance attribute that lives
as long as the counter, unlike `signin_credentials`'s transient dict. httpx does **not** obscure
`x-api-key` in `Headers.__repr__` (only `authorization`/`proxy-authorization`/`cookie`). The
builder's comment shows this was considered and it is arguably the narrowest possible unwrap for a
header — recording it because "where can `get_secret_value()`'s result be stored?" was an explicit
question in my brief and this is the one place the answer is "in a long-lived object".

### 8.5 Cosmetic — a mechanical-rewrite artifact in `scout.py`
The new `# The USERNAME is deliberately not carried as a secret (#211)` comment block has blank
lines interleaved between its comment lines (the sibling copies in `index/cli.py` / `server.py` /
`snapshot_gc.py` do not). Ruff-clean, harmless, ugly.

### 8.6 Things I looked at and found nothing wrong with
`loresigil/backoff.py`'s adapter (tenacity's `wait_random_exponential` is genuinely Full Jitter and
genuinely called — the AST pin reads the call inside the function, not the file's text, which its
own comment records as a lesson learned from a mutation that fooled the substring version); the
`_POW_ALLOWLIST` exemption for `_txn.py` (evidence-backed, with a positive control asserting the
exempted construct is still present *and* still jittered); the perimeter's negative controls; the
`_txn.signin_credentials` seam (one unwrap, transient dict, straight to `signin`); `auth.py`'s two
unwraps (constant-time compare, emptiness check); `RedactingFilter`'s two documented bounds (it does
not clear `exc_info`, and handler ordering) — both correctly stated rather than discovered later.
All new test files are inside `testpaths` (`loremaster/tests/`, `loresigil/tests/`), verified.

---

## §9. What a GO would require

1. Freeze the branch. Name the tip. Re-run the three gates on it.
2. Fix Defect A (§2.4) — or rule it accepted with a pin that goes RED the day it is closed.
3. Fix Defect B; the tip is RED without it, and re-derive `0b851a3`'s failure-set claim.
4. Correct and close #210; fix the three false in-code claims, the served `ValueError` first.
5. Resolve/supersede #199 with the merge-target reality recorded.
6. Decide on `scripts/` in `typecheck.sh` — the hole that produced A **and** B.

I did not find a defect in the #207 consolidation, the #210 fix, the #210 class instrument, or the
#211 traceback work: I attacked all four and they held, and §5/§6/§7.1 say exactly how. The wave's
engineering is strong. **It is the process around it — three builders on one index, an unfrozen tip,
and a whole directory outside both standing gates — that put two live defects into the tree.**

---
*Measured 2026-07-25/26 against `pkt11i-floor-calibration-dark` at commits `2bc28cf` and `0b851a3`,
in worktree `/home/ejprice/PycharmProjects/lore-pkt11i` and frozen `git archive` snapshots at
`/home/ejprice/scratch-coldaudit-base`. Every present-tense claim above is a claim about those
commits, not about a later tip.*
