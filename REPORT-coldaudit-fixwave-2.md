# REPORT-coldaudit-fixwave-2 — independent grading of the #210 / #207 / #211 fix wave

> Everything here was measured **2026-07-26** against a FROZEN copy of **`13b5659`** (branch
> `pkt11i-floor-calibration-dark`). Claims are dated and SHA-scoped where they are made, because a
> retrieved chunk arrives without its header.

## SUMMARY BLOCK

- `brief-base v6 read`
- **VERDICT: NO-GO — on ONE narrow ground, with everything else GO.**
  **#210 (GO) · #207 (GO) · #211 Half A / `SecretStr` (GO) · #211 Half B + #227, the
  logging/redaction half (NO-GO).** The blocker is **R1**: `0233999`'s path-component guard is the
  wave's only **strict regression against `d0ee2be`** — it silently stops redacting **38–63%** of
  realistic base64 credentials, reproduced end-to-end on the production JSON log line. Repo law is
  explicit that a backstop weakened to cure false positives is worse than the bug, so I will not
  wave it through as a residual. **The remediation is one function and I verified a candidate that
  closes it while preserving every false-positive class the fix exists for (§3.3).**
- **State: done.** All five gates re-run by me on a frozen copy with in-run provenance from all 64
  xdist workers · #207's sharing claim re-proven by SOURCE mutation independent of the wave's own
  helpers · Defect A re-proven live with a positive control · both #210 exemptions re-derived ·
  #219's open residual closed by an AST sweep.
- **THE TREE WAS FROZEN.** HEAD `13b5659` and `git status` clean at audit start AND at audit end.
  **No commit moved during this audit.**

### Deviations
1. **I graded a frozen copy, never the worktree** (§1), proven byte-identical over 495 tracked
   files. Per **#185** I never ran `git` with cwd inside the copy — its `.git` is a 70-byte gitdir
   POINTER at the real worktree, so a write there would mutate the tree I am grading.
2. **Two frozen copies.** Mutation work went in a second copy so it could not contaminate the gate
   run — mutating a tree while its suite runs is exactly how the predecessor produced its retracted
   Defect C.
3. **lore's index watches the MAIN checkout, not this worktree (#125)** — every structural sweep
   here is grep / Read / AST, said out loud per brief-base §4. `lore_findings` was used for the
   ledger (a store read, unaffected by index topology).
4. **I did not file ledger rows.** No task row was named as mine (brief-base §5). R1–R5 need
   findings; I recommend the lead file them.

### Gate results — FROZEN copy, provenance-clean
| gate | result | receipt |
|---|---|---|
| `uv run pytest -n auto -q` | **394 failed, 6246 passed, 17 skipped, 3 xfailed** in 201.28s | 65/65 provenance records inside the copy; **0 of 117** collected test modules outside it |
| `./scripts/typecheck.sh` | **109 errors in 3 files** (exit 1) — all packet-03b contract tests; **0 in any production or wave-touched file** | in-copy |
| `uv run ruff check .` | **All checks passed** (exit 0) | in-copy |
| `uv run pytest scripts/` | **153 passed** (⚠ not 150 — §8) | in-copy |
| `uv run mypy scripts` | **27 errors in 4 files** (exit 1) — **none is a secret-typing error**; Defect A's class is clean | in-copy |

`loremaster.__file__ = /home/ejprice/scratch-coldaudit-fixwave-2/loremaster/loremaster/__init__.py`

### Failure attribution — 1-for-1, BOTH directions, no "the rest are pre-existing"
| direction | count | ids |
|---|---|---|
| observed FAILED | 394 | — |
| enumerated baseline (`baseline-red-at-d0ee2be.txt`) | 394 | — |
| **only in NOW** (11i breakage) | **0** | *(empty)* |
| **only in BASELINE** (fixed or deleted) | **0** | *(empty)* |

**Exactly the enumerated baseline — zero drift either way.** This closes the predecessor's Defect B
and corroborates its Defect C retraction. The 109 mypy errors are the same artifact: every message
names a missing 03b symbol, and all three files are inside the 394.

### The five findings I am raising
| id | severity | what |
|---|---|---|
| **R1** | **BLOCKER** | #227's guard stops redacting `/`-bearing base64 credentials — **38–63%** measured, strict regression vs `d0ee2be`, live on the production log line. §3 |
| **R2** | **HIGH** | The same false-positive class #227 fixed for paths is **unfixed for FUNCTION NAMES**: **201 of 1,616 production functions (12.4%)** are erased from every traceback frame — on the surface #211 Half B exists to deliver. §4 |
| **R3** | **HIGH** | The two pins that would have caught R2 are **vacuous**: the credential never reaches the traceback, and their `REDACTED` assertion is satisfied by R2 itself, at a **0.023-bit** entropy margin. §5 |
| **R4** | MEDIUM | Reverting the shared policy to the **exact pre-#207 build** reddens **only 4 tests, all in the policy's own file** — five site-level pins admit the un-jittered world. §6 |
| **R5** | LOW | `assert not isinstance(exc_info.value, AgentRegistryError)` inside `pytest.raises(ValueError)` **cannot fail**; its comment calls it "the load-bearing half of this pin". §7 |

### What I confirmed FIXED / SOUND
Defect A (live re-proof + control, and my own 5/5 enumeration) · Defect B (failure set exact) ·
Defect C (retraction correct) · #210's `fullmatch` fix and **both** allowlist exemptions
(independently re-derived, with controls) · **#207 sharing: 8/8 sites proven by source mutation** ·
#211 Half A end-to-end against a live store · traceback rendering restored (it emitted nothing at
`d0ee2be`, which I verified) · #219 correct, and I closed its open residual.

### Decisions needed
1. **R1 — fix before merge (recommended), or accept-and-restate the bound.** Verified candidate in §3.3.
2. **R2 — a design call**, not a one-liner: exempting identifier-shaped runs collides with #227's
   two accepted KNOWN BOUNDS. Needs an owner.
3. **R3/R4/R5 — test-quality debt**, fixable after merge, but R3 must not be closed by deleting the
   pins: they name real properties that are currently untested.
4. **Ledger hygiene**: #204, #207, #210, #227 are all still `open` though this wave fixed them;
   #227's body still says the fix is "awaiting GO"; #199's amended count (150) is stale at **153**.
5. **`scripts/search_score_survey.py` still hard-codes `ws://127.0.0.1:18500/rpc` = PRODUCTION.**
   Pre-existing, raised by the predecessor, still unactioned. Re-raised under scope law.
6. **The pre-merge baseline from main** (`FIXWAVE-CLOSEOUT.md` §2.4) is still owed — my "exactly the
   baseline" result is a true statement about a fiction and certifies nothing about the merged world.

---

## §1. Provenance — what I actually graded

```
scratch copy READY: /home/ejprice/scratch-coldaudit-fixwave-2
  loremaster  -> /home/ejprice/scratch-coldaudit-fixwave-2/loremaster/loremaster/__init__.py
  loresigil   -> /home/ejprice/scratch-coldaudit-fixwave-2/loresigil/loresigil/__init__.py
  lorescribe  -> /home/ejprice/scratch-coldaudit-fixwave-2/lorescribe/lorescribe/__init__.py
```
`git archive 13b5659 | tar -x` extracted OVER the copy (git run from the worktree). I md5'd all
**495** tracked files before and after: **identical** — the copy was already exactly `13b5659`.

The gate run recorded provenance from INSIDE the run, per worker, via a `-p` plugin: **65 records
(64 workers + master), all inside the copy; 117 collected test modules, all inside the copy; zero
outside.** This is the receipt the predecessor lacked when it mislabelled a live-worktree run with a
frozen SHA.

## §2. Three of MY OWN instruments were wrong first — disclosed

1. **My first ruff run reported 1 error: my own provenance plugin.** Removed it; ruff is clean. Had
   I not read the filename I would have reported a lint failure against the wave.
2. **My first gate invocations printed `EXIT=$?` after a pipe to `tail`** — which reports *tail's*
   status. Re-run unpiped; `typecheck.sh`'s real exit is **1**. The repo documents this trap and I
   walked into it.
3. **My first probe of the `_TASK_ID_SHAPE_PATTERN` exemption CONTRADICTED it — and the probe was
   the broken instrument**: I omitted `TaskSpecItem`'s required `subject`/`description`, so
   construction failed for the wrong reason. Re-run with controls, the exemption's evidence
   **reproduces exactly** (§9.1). *A probe needs a control.*

## §3. R1 (BLOCKER) — #227's guard leaks `/`-bearing base64 credentials

### 3.1 The claim it makes
`0233999` exempts a high-entropy run that is adjacent to `/` (a path component) or is a canonical
UUID, and states its bound twice — *"a secret inside a URL path segment … or one that is itself a
canonical UUID"* — justified by:

> *"an honest credential leak does not arrive as `/…/<secret>/…` or wearing exact UUID punctuation"*

### 3.2 That justification is false, and the bound is not the only one
`_TOKEN_RE`'s charset `[A-Za-z0-9+=_\-]` **excludes `/`**; the standard base64 alphabet **includes
it**. A base64 credential containing `/` splits into two runs — and **each run is now `/`-adjacent
and therefore exempt.** It is neither a URL, nor a path, nor a UUID.

Measured, guard ON vs guard forced OFF. The OFF leg *is* the pre-wave scrubber: I verified myself
that `_TOKEN_RE` and `_ENTROPY_BITS_THRESHOLD` are **byte-identical at `d0ee2be`**.

| secret shape | contains `/` | pre-fix redacted | **NOW LEAKS** |
|---|---|---|---|
| 24-byte → 32-char base64 | 40.0% | 76.9% | **16.9%** |
| 32-byte → 44-char base64 | 48.1% | 89.9% | **38.0%** |
| 48-byte → 64-char base64 | 64.8% | 98.2% | **63.1%** |

*(5,000 seeded trials each, in the frozen copy.)*

**End-to-end on the production surface** — `JsonFormatter` + `RedactingFilter`, exception frame
holding `kJ8vQ2mZ7xR1pL4nT6yB9wC3dF5gH0jK/aS2eD8fG1h=`:
```
SECRET LEAKS INTO THE EMITTED PRODUCTION LOG LINE?  True
emitted exc_info: RuntimeError: auth rejected token kJ8vQ2mZ7xR1pL4nT6yB9wC3dF5gH0jK/aS2eD8fG1h=
```
The same secret without a `/` is correctly redacted, so the discriminator is the `/` and the probe
can demonstrably see redaction happening.

**Why BLOCKER and not residual:** on `msg` / `args` / `extra` — a surface that existed and *was*
redacted at `d0ee2be` — this is a **strict loss of coverage**, and it is the wave's **only** strict
regression. Everything else in this wave makes things better.

### 3.3 A verified candidate narrowing (not a hand-wave)
All three false-positive classes the fix exists for are **absolute paths**. Restricting the
exemption to runs whose surrounding maximal path-like blob **starts with `/`**:

| case | shipped | candidate |
|---|---|---|
| uuid workspace path · 64-hex overlay path · nix store path · real traceback `File` line | preserved | **preserved** |
| *(bound)* secret in a URL path segment · *(bound)* secret that IS a UUID | preserved | preserved *(bounds intact)* |
| **ATTACK** base64 with `/` · basic-auth blob with `/` · token followed by `/` | **leaks** | **REDACTED** |
| CONTROL bare 64-hex | REDACTED | REDACTED |

I am not prescribing this implementation — I am establishing that the false-positive cure does
**not** require the breadth it was given, so "narrow it" is a real option and not a trade against
the tracebacks the fix protects.

## §4. R2 (HIGH) — the same class, unfixed: 12.4% of functions are erased from tracebacks

Rendering a real exception through the shipped filter:
```
Traceback (most recent call last):
  File "<stdin>", line 22, in <module>
  File "<stdin>", line 16, in ***REDACTED***
RuntimeError: connection refused
```
The **function name in the traceback header** is redacted. `_leak_from_a_literal_credential` is 31
chars over `_TOKEN_RE`'s charset with Shannon entropy **3.5231** against a **3.5** threshold.

This is #227's own defect class — *the redactor mangling traceback structure* — fixed for path
components and **left live for function names**, on the surface **#211 Half B exists to create**.
Half B's stated purpose is to make exception diagnosis possible; a frame whose function name is
`***REDACTED***` is a frame you cannot attribute.

**Measured across the real production tree (AST-enumerated, every `def`/`async def`, tests excluded):**

```
production functions scanned : 1616
functions whose NAME is REDACTED out of any traceback frame: 201  (12.4%)
```
Examples: `calibration/engine.py::_handle_terminal_endpoint_error` ·
`config.py::effective_surreal_database` · `embedding.py::make_embedder_from_config` ·
`graph_surreal.py::build_file_graph_fragment` · `impact.py::_production_consumer_names`.

**Note this is NOT closed by R1's candidate fix** — a function name is not `/`-adjacent. It needs
its own decision, and it is genuinely harder: the obvious cure (exempt identifier-shaped runs) is
what the wave's own mutation **M14** showed reddens both members of #227's accepted KNOWN BOUND.
A narrower shape — exempting only the `in <identifier>` tail of a `File "…", line N, in …` header —
is available but is a design call, not a patch. **Flagged, not solved.**

## §5. R3 (HIGH) — the two pins that should have caught R2 are vacuous

`test_logging_setup.py::TestExceptionRenderingIsEmittedAndScrubbed::test_secret_in_the_rendered_source_line_is_scrubbed`
and its `::test_stack_info_is_scrubbed` sibling. The fixture:
```python
def _leak_from_a_literal_credential() -> None:
    if "Zt7QnP4xW9kLm2Rb8VyH3sJd6FgA1cUe0oIT":  # the literal IS the fixture
        raise RuntimeError("connection refused")
```
```python
assert LITERAL_IN_SOURCE not in output, "the credential in the source line survived"
assert REDACTED in output
```
Measured, running the shipped fixture shape:
```
Q1: does the credential literal reach the traceback at all?  False
Q2: is REDACTED present? True
--- what _scrub_text changes in the RAW traceback ---
  before: File "<stdin>", line 16, in _leak_from_a_literal_credential
  after : File "<stdin>", line 16, in ***REDACTED***
```
**Python's traceback quotes the RAISING line, not the `if` line** — so the credential never reaches
the surface, and assertion 1 passes on every build including one that never scrubs source lines at
all. Assertion 2 is green **for an unrelated reason: R2**. The pin asserting "the secret was
redacted" is satisfied by the redactor eating the fixture's own function name, at a **0.023-bit**
margin above threshold — so renaming that helper, or nudging the threshold, reddens the pin for a
reason unrelated to secrets.

**Both properties these pins name are real and currently untested.** The fix is to put the literal
on the raising line and assert `REDACTED` at the position the literal occupied, plus a positive
control proving the literal reaches the render on an unscrubbed path. Do not close R3 by deleting
the tests.

*(Related, lower: `TestOrdinaryPathsSurviveRedaction::test_a_secret_is_still_redacted_in_that_same_traceback`
is commented "THE DISCRIMINATOR … fixing a false positive by weakening the backstop would … silently
undo the finding this module exists for". Its secret is planted as `password={TOKEN}` — a LABELLED
assignment caught by `_ASSIGNMENT_RE`, which runs before the entropy sweep — so it passes with the
entropy sweep entirely disabled. The class's real discriminator is
`test_the_exemption_is_contextual_not_a_blanket_stand_down`, which is sound.)*

## §6. R4 (MEDIUM) — five site-level backoff pins admit the pre-#207 world

I reverted the shared policy to the **exact** pre-#207 build (`min(base_s * 2**attempt, cap_s)` —
verbatim from `resilient.py::compute_backoff_delay`'s own docstring), with the expected-RED set
declared from `--collect-only` **before** the run:

```
119 node ids collected · 4 failed, 115 passed
FAILED loresigil/tests/test_backoff.py::TestJitterIsFullNotAroundAFloor::test_draws_reach_the_bottom_half_of_the_window
FAILED loresigil/tests/test_backoff.py::TestJitterIsFullNotAroundAFloor::test_draws_span_both_halves_of_the_window
FAILED loresigil/tests/test_backoff.py::TestSimultaneousClientsDecorrelate::test_simultaneous_clients_draw_distinct_delays
FAILED loresigil/tests/test_backoff.py::TestSimultaneousClientsDecorrelate::test_two_calls_with_identical_arguments_differ
```
**Undoing #207's entire fix reddens only the policy's OWN unit file.** Every site-level pin stays
green, including ones whose failure messages promise otherwise:

| pin | assertion | un-jittered build returns | verdict |
|---|---|---|---|
| `test_resilient.py::test_backoff_is_drawn_from_an_exponentially_growing_window` | `0.0 <= delay <= window` — message: *"the delay is not being drawn…"* | exactly `window` | admits it |
| `test_voyage_context.py::test_429_then_success_is_retried` | `0.0 <= d[0] <= BACKOFF_BASE_S` | exactly `BACKOFF_BASE_S` | admits it |
| `test_calibration_engine.py::test_recovers_after_transient_outage` | `0.0 <= d[0] <= BACKOFF_START_S` | exactly `BACKOFF_START_S` | admits it |
| `test_calibration_engine.py::test_429_is_retried_not_treated_as_terminal` | idem | idem | admits it |
| `test_calibration_engine.py::test_backoff_doubles_and_caps` (per-delay leg only) | idem | idem | admits it *(its window-sequence leg is sound)* |

**This is the wave's own mutation-G defect, swept once and not swept twice.** `776312b` caught
exactly this shape in the D2 pin (`7.0 <= slept[0] <= 8.0` passing on an un-jittered build),
strengthened that one to repeat-draws — and did not grep for its siblings. Repo law: *sweep from
the grep, never from a report's hand-list.*

**In fairness — coverage is not absent.** The architecture is sound: one shared policy tested
thoroughly in `test_backoff.py`, plus `test_backoff_seam.py`'s sentinel-mutation instrument proving
each site ROUTES to it. Between them, de-jittering IS caught. R4 is that the site-level pins'
**failure messages promise a check their predicates do not perform**, and that each of them
replaced a deterministic assertion (`== [30.0]`, `d[0] < d[1] < d[2]`) that DID discriminate. That
is a false gate by this repo's own definition, five times.

**The strengthened D2 pin (`test_retry_after_header_is_honoured`) I verified SOUND** against the
build it was strengthened for: 8 draws, `len(set(draws)) >= 6`, and an un-jittered build yields 8
identical values → 1 distinct → RED. Residual: 8/6 does not exclude a *quantised* jitter table
(this repo's #102/#108 shape) — a 16-slot table passes ~70% of the time.
`test_backoff.py::test_simultaneous_callers_draw_distinct_delays` uses 64/≥60 and closes it
properly; the site pin should adopt those numbers.

## §7. R5 (LOW) — an unfalsifiable assertion described as load-bearing

`test_comms_tool.py::TestCommsDispatchCharsetValidation::test_a_trailing_newline_agent_name_is_rejected`:
```python
with pytest.raises(ValueError) as exc_info:
    ...
assert not isinstance(exc_info.value, AgentRegistryError)   # "THE class invariant, and the
                                                            #  load-bearing half of this pin"
```
Measured:
```
AgentRegistryError MRO: ['AgentRegistryError', 'RuntimeError', 'Exception', 'BaseException', 'object']
issubclass(AgentRegistryError, ValueError) = False
classes that are BOTH AgentRegistryError and ValueError: NONE
```
`pytest.raises(ValueError)` already guarantees it. The assertion **cannot fail**. Separately, the
property the comment claims — *"the store is never reached for a malformed identity"*, which is the
invariant `c32800d`'s own commit message says was violated — is **not tested by anything here**: a
build that queried the store and *then* raised the `ValueError` passes. The harness already supplies
a `FakeAgentRegistry`; asserting zero calls on it is the pin the comment describes.

## §8. #207's sharing claim — re-proven independently (GO)

I did **not** rely on the wave's own instrument. I mutated the **source** of
`loresigil/loresigil/backoff.py` to return two **distinct** sentinels and drove all eight sites
through a driver written from the production source:

| # | site | control | **mutated** |
|---|---|---|---|
| 1 | `loresigil.resilient.compute_backoff_delay` | 2.015… | **111.0** |
| 2 | `counting.AsyncClaudeTokenCounter._sleep_backoff` | 2.606… | **111.0** |
| 3 | `calibration.engine.CalibrationEngine._backoff_delay` | 2.828… | **111.0** |
| 4 | `scout.CommandSubscriber._backoff` | 0.954… | **111.0** |
| 5 | `token_survey.ClaudeTokenCounter._sleep_backoff` | 4.020… | **111.0** |
| 6 | `counting._sleep_backoff.retry_after` (D2) | 7.349… | **222.0** |
| 7 | `token_survey._sleep_backoff.retry_after` (D2) | 7.234… | **222.0** |
| 8 | `server._EagerStartupLifespan._acquire_eager_lease_with_retry` (D3) | 4.471… | **222.0** |

**8/8 shared; no private copies.** Two distinct sentinels matter: a site routed to the *wrong*
policy would still look "jittered" — sites 6–8 returning `222.0` proves they take the ADDITIVE path
and can never sleep below the server's floor. The control column also shows the additive contract
at runtime (7.0 + jitter ∈ [0,1); 3.5 + jitter) — **upward only**.

Restores verified `md5sum -c` **OK** with no marker surviving, after both mutations.

My independent grep of all four production roots finds these eight call sites and no others, each
using `from loresigil import backoff` — the module-level late binding that makes the wave's own
monkeypatch instrument sound.

## §9. #211 / Defect A — re-proven live (GO)

**Live re-proof, test store `ws://127.0.0.1:18000` (`:18500` PRODUCTION never touched):**
```
LEG 1 (CONTROL, expect OK)      user=str        -> OK — signin succeeded
LEG 2 (DEFECT,  expect FAILURE) user=SecretStr  -> BufferError: ('no encoder for type ', <class 'pydantic.types.SecretStr'>)
LEG 3 — the SHIPPED _make_store expression, verbatim:
  type(user) = str | type(password) = SecretStr | live signin -> OK
```
Leg 2 reproduces the defect on demand, so leg 3's pass is not a probe that cannot fail.

**The five-member set, enumerated by me** (bare anchor-free grep) — all five unwrap the username:
`index/cli.py` · `scout.py` · `server.py` · `scripts/snapshot_gc.py` · `scripts/search_score_survey.py`
(Defect A's site). Passwords stay `SecretStr`, unwrapped at exactly one place —
`store/_txn.py::signin_credentials(user: str, password: SecretStr)`, whose signature is the guard,
which is why it only fires where mypy runs, and why `scripts/` being outside `MEMBERS` let Defect A
ship. A sixth site, `scripts/survey_txn_contention_102.py`, builds from module constants and
correctly routes through the seam.

**Both #211 halves work end-to-end** (a non-`/` secret): `exc_info` present (159 chars — it was
absent at `d0ee2be`, which I verified: `exc_info` appears there only inside a skip-list), and
`RuntimeError: connect failed using ***REDACTED***`. Subject to R1 and R2.

## §9.1 #210 — the fix and both exemptions (GO)

**`_TASK_ID_SHAPE_PATTERN`** re-derived with controls:

| value | constructs? | `.match` | `.fullmatch` | shipped behaviour |
|---|---|---|---|---|
| `'alpha'` *(control)* | yes | False | False | accepted as batch key |
| `<32hex>` *(control)* | yes | True | True | rejected as id-shaped |
| `<32hex>+"\n"` *(hazard)* | **yes** | **True** | **False** | rejected as id-shaped |

`model_fields['key']` → `str | None`, metadata `[]` — genuinely unconstrained, so the hazard value
really can arrive; `fullmatch` here **would be a regression**, exactly as the entry claims.

**`_HEADING_LINE`** re-measured over this repo's markdown corpus: **207 files, 66,876 lines, 0
disagreements** between `.match` and `.fullmatch` on match/no-match *and* extracted groups. (My
counts differ from the entry's 215/65,786 because the corpus itself moved; the **property**
reproduces, which is what matters.)

**A checked negative worth recording:** `SLUG_PATTERN` is `$`-anchored and reaches pydantic as
`StringConstraints(pattern=...)`. It is **NOT** vulnerable — pydantic's Rust regex treats `$` as
end-of-haystack and rejects `'scout\n'`. An AST scan keyed on `.match` could never have answered
that.

**Gate reach — LATENT gaps, not live misses** (probed with controls):

| shape | gate |
|---|---|
| `NAME_RE = r"^...$"` *(uncompiled str)* + `re.match(NAME_RE, v)` | **INVISIBLE** ← not in the stated KNOWN BOUNDS |
| `re.match(pattern=..., string=...)` *(keyword form)* | **INVISIBLE** ← not in the stated KNOWN BOUNDS |
| anchored pattern on a class/instance attribute | INVISIBLE *(stated bound — fine)* |
| pattern ending `\Z` | INVISIBLE *(correct — not this defect)* |
| `re.compile(r"^...$", re.I)` + `.match` · plain #210 shape *(controls)* | **CAUGHT** |

The first is a plausible honest spelling. Two such constants exist today
(`config.py::SLUG_PATTERN`, `store/surreal_schema.py::_IDENTIFIER_CHARSET_PATTERN`) and **neither is
a live defect** — the first is cleared above, the second feeds a SurrealQL `string::matches` ASSERT
(Rust regex, no leniency). Cheapest answer: state them in KNOWN BOUNDS.

Two smaller reach notes: the #210 scan covers `{loremaster, lorescribe, loresigil, scripts}` while
the sibling `test_backoff_seam.py` perimeter in the *same wave* also covers `skills` —
`docs/eval/smoke_p8b.py` holds a live `$`-anchored `.match` the #210 gate cannot see (an
**extractor, not a validator**, so not a defect under the gate's own written threat model). And
`TestScanCoverage::test_the_scan_reaches_every_production_tree` derives its expected set from
`_SCANNED_ROOTS`, so it can notice a root going *missing* but never a root never *declared* —
coverage is a checked variable in one direction only.

## §10. #219's residual — CLOSED

#219 records that `_validate_comms_charset`'s docstring **and its SERVED error message** claim
identities are *"inlined into store queries"*. **Both are still present verbatim at `13b5659`.**
This is correctly ledgered and was correctly refused as out of scope by the #210 fixer; I am not
re-raising it.

I *can* close #219's open residual — *"whether any OTHER call path inlines an identity was not
swept."* I swept it with an AST pass over every production module, collecting every f-string
containing SurrealQL keywords and reporting each non-constant interpolation, then reading the
SurrealQL hits individually (the sweep also catches prose containing words like "created", which I
discarded by inspection, not wholesale):

- Every interpolation into a query is a **table name, field name, or `$param` NAME** — all module
  constants — or a clause assembled from constants (`' AND '.join(conditions)`).
- **No comms identity value is interpolated anywhere.** Lookups are
  `WHERE {_COL_NAME} = ${_NAME_LOOKUP_PARAM}` and `WHERE name IN $names`.
- The only value-interpolations into DDL are `_txn.py`'s `DEFINE NAMESPACE/DATABASE {namespace}` and
  `surreal_schema.py`'s `DEFINE TABLE/FIELD/INDEX {name}` — schema identifiers from config and
  module constants, not caller identities. Pre-existing, noted for completeness.

**#219 resolves in the non-inverted direction: the message is wrong, the code is right.** Its
escalation clause ("if some path DOES inline, the message is right and the code is wrong") does not
fire. The fix is a prose correction, as #219 says.

## §11. Findings grading — are the amended versions right NOW?

- **#199 — the 50→150 correction was right; the number is now STALE.** Re-derived at `13b5659`:
  `--collect-only -q scripts/` → **153**, and `pytest scripts/` → **153 passed**. The wave itself
  added script tests after the re-derivation. Small, but it is a served count in a ledger agents
  read, inside a finding whose entire history is about a count being wrong.
- **#211 — the correction-of-a-correction is CORRECT** (verified at `d0ee2be`).
- **#227 — body STALE and its bound INCOMPLETE.** It still says *"THE FIX (in the working tree,
  awaiting GO)"*; the fix landed at `0233999`. Its stated bound omits R1 and R2. A finding still
  wrong after correction is worse than one nobody touched — this one under-states a security hole.
- **#210 / #219 — bodies accurate.**
- **Ledger hygiene: #204, #207, #210, #227 are all still `open`** though this wave fixed them.
  Not a code defect, but a ledger showing a fixed security finding as open is a served surface that
  misleads.

## §12. Coverage — what I did and did not do

**Did:** all five gates re-run in a frozen provenance-asserted copy · full failure-set diff both
ways · source-mutation sharing proof of all 8 #207 sites · a second source mutation reverting the
policy to the pre-#207 build with the expected-RED set declared from `--collect-only` first · live
signin re-proof with a positive control · independent `resolve_secret` enumeration · end-to-end
#211 render+scrub · adversarial #227 probe with a pre/post A/B and 5,000-trial quantification · a
verified candidate narrowing · an AST census of all 1,616 production functions for R2 · both #210
exemptions re-derived with controls · #210 gate reach probe with controls · AST sweep closing
#219's residual · findings graded against source and re-derived counts.

**Did not:** run the full suite more than once (the failure set was exact, and the predecessor's two
runs at two commits agree with mine) · re-verify the 394 baseline ids individually beyond set
equality plus confirming every mypy message names a missing 03b symbol · exercise the eager-lease or
`Retry-After` paths against a real remote server (both driven through the real methods with injected
sleeps) · audit the wave's receipts prose beyond the claims I tested.

**On delegation:** two sweeps (test-execution reachability; a hollow-pin hunt) were run by
subagents. **Nothing from either appears above unverified** — R3, R4, R5 were re-derived by me with
my own probes and mutations, and R2 is mine, found while verifying R3. The reachability result
agrees with my own `pytest scripts/` count of 153 and the `pyproject.toml` I read directly: all 41
wave-touched test files are reachable, 3 of them (`scripts/test_calibration_baseline.py`,
`scripts/test_search_score_survey.py`, `scripts/test_snapshot_gc.py`) only by a manually-typed
`pytest scripts/`.

## §13. Everything else I noticed (scope law — the operator decides)

1. **`scripts/search_score_survey.py` hard-codes `DEFAULT_SURREAL_URL = "ws://127.0.0.1:18500/rpc"`
   — PRODUCTION `lore-surreal`**, in a repo whose CLAUDE.md says *"never point tests at it"*. And
   `scripts/test_search_score_survey.py` constructs that store in a test. Pre-existing, raised by
   the predecessor (§8.1), still unactioned. **Highest-value item in this section.**
2. **`scripts/` is outside BOTH `testpaths` and typecheck's `MEMBERS`** — the hole Defects A and B
   lived in. `mypy scripts` finds 27 errors in 4 files today (none secret-typing): mostly
   unfollowed-import degradation (`token_survey` / `search_score_survey` unresolvable as modules, so
   type information is silently lost across that boundary) plus SDK stub gaps. Adding `scripts` to
   `MEMBERS` needs those first — a cost to choose, not a free win.
3. **The `skills/lore-deploy` suite (8 files) runs only by a documented idiom no gate invokes** —
   same class as `scripts/`. Untouched by this wave.
4. **`f65e062` remains a 59-file two-wave commit.** Deliberate and disclosed at `7251c77`; I agree
   with the reasoning and flag it only so the merge does not read it as one concern.
5. **The 394 baseline is a branch-point artifact.** My "exactly the baseline" result certifies
   nothing about the merged world; the pre-merge baseline from main is still owed.

---

*Audited by `coldaudit-fixwave-2`, 2026-07-26, against frozen `13b5659`. I built none of this wave.*
