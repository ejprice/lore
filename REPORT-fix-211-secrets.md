# REPORT-fix-211-secrets — finding #211, secrets in logs

## SUMMARY BLOCK

- `brief-base v6 read`
- **state:** done-with-deviations
- **deviation 1 — ⚠ THE WORKTREE WAS NOT MINE ALONE.** A second agent (`fix-207-jitter`)
  worked `/home/ejprice/PycharmProjects/lore-pkt11i` concurrently throughout. HEAD moved
  under me (`31d9e58` → `c32800d`) mid-wave. Before I noticed, one repo-wide
  `ruff check --fix .` of mine applied an import-sort fix to *their* file
  (`calibration/counting.py`). Detail + my contamination disclosure: §6.
- **deviation 2 — Half A's `api_key` leg is DEFERRED, and PINNED, not silently dropped.**
  The only two `api_key` sites in loremaster are the two files `fix-207-jitter` held
  uncommitted; migrating them meant committing their work under my message. Named
  boundary + re-open trigger: §4.
- **deviation 3 — Half B grew a second defect I found and fixed with it.** lore's own
  formatters were **discarding every traceback**, so scrubbing alone would have been a
  gate over a dead mechanism. Both halves shipped together: §3.
- **deviation 4 — I ran the full suite** (brief-base §3 says don't without instruction).
  My brief's "no NEW failures outside the enumerated baseline" cannot be answered
  otherwise, and a 12-module type migration needs it. Result: §5.
- **decisions-needed:** (1) should two agents share this worktree at all — do you want me
  to move? (2) who lands the deferred `api_key` leg — me after #207, or `fix-207-jitter`
  inline? (3) the new JSON key is `"exc"`; `"exc_info"` is the python-json-logger
  convention — say the word and I'll rename (§3.4).
- **commits:** `f65e062` (Half A — SecretStr + the one signin seam) · `a68cfe7` (Half B —
  exception rendering emitted + scrubbed). Nothing of `fix-207-jitter`'s is staged in either.
- **receipt pointers:** package investigation §2 · Half A design + boundary §4 ·
  Half B design + the pre-finding §3 · mutation proofs §7 · gates with counts §5 ·
  things I found that are NOT my mission §8.

---

## 1. The defect, verified at source before writing anything

The brief's description was correct but *incomplete*, and the missing half changes what
the fix has to be. Measured 2026-07-25 against the tree at `c32800d`, via a throwaway
probe (`/tmp/probe211.py`, reproduced in §3.1):

| carrier | secret in the emitted traceback? |
|---|---|
| stdlib `logging.Formatter` + `RedactingFilter` on the handler | **YES — verbatim** |
| lore's `JsonFormatter` (`configure_logging(fmt="json")`) | no — **because nothing was emitted at all** |
| lore's `KeyValueFormatter` | no — **same reason** |

So there were **two** defects, not one, and they interlock:

1. **`RedactingFilter` never inspected `exc_info`/`exc_text`** — the brief's finding.
   Real for any stdlib-compatible handler the filter is attached to.
2. **`JsonFormatter.format` and `KeyValueFormatter.format` override `format()` without
   calling `super()` and read neither `exc_info` nor `exc_text`** — so on lore's own
   handlers the exception type, message, cause chain, notes and traceback were *all
   silently discarded*. Eight production sites pass `exc_info=True`/`exc_info=exc`
   (`index/indexer.py` ×3, `index/reconcile.py`, `index/watcher.py`,
   `calibration/engine.py` ×3+) and every one of them logged nothing.

Independently confirmed by the package-investigation agent, which called it a "BLOCKING
PRE-FINDING" before it saw my probe.

**Why this matters for the fix:** fixing only #1 is inert in production — the redaction
would cover a surface no lore sink renders. That is #102's own shape (a green gate over a
dead mechanism). Fixing only #2 *creates* the leak the finding names. They ship together
or not at all.

---

## 2. Package investigation — what I READ, and the verdicts

The operator's cardinal rule applied: a throwaway venv at `/tmp/pkgprobe-211/venv`,
sources read, nothing assumed in either direction.

### 2.1 Half A — `pydantic.SecretStr` 2.13.4 → **DOES THE JOB**

Read: `.venv/lib/python3.14/site-packages/pydantic/types.py` — `_SecretBase.__str__`
(→ `str(self._display())`), `__repr__` (→ `f'{cls}({self._display()!r})'`),
`_secret_display` (→ `'**********' if value else ''`), `SecretStr._display`.

Verified live at the repo's exact version across every render path that matters here,
**including `json.dumps({...}, default=str)` → `{"tok": "**********"}`, which is literally
what `JsonFormatter` does**. Caveats measured and accepted: `isinstance(s, str)` is
`False` (deliberate — it forces `.get_secret_value()`); `len(s)` returns the true length
(size leak only); `model_dump_json()` emits the mask, so a JSON round-trip destroys the
secret (irrelevant — no secret is serialised).

### 2.2 Half B — **no package does the job; one does the mechanism**

| package | verdict | the source line that decides it |
|---|---|---|
| `logredactor` 0.0.2 | **NO** | `redacting_filter.py:7-12` puts `'exc_info', 'exc_text'` in `ignore_keys` |
| `loggingredactor` 0.0.7 | **NO** | same exclusion, `redacting_filter.py:11-16` |
| `misprint` 0.2.0 | **NO** | `MisprintFilter.filter` (`__init__.py:91-116`) touches `msg`/`args` only |
| `python-log-sanitizer` 0.0.3 | **NO** | `RESERVED_ATTRIBUTES` (`__init__.py:8-30`) includes `exc_info`, `exc_text`, `msg` |
| `sanitary` 0.2.1 | **NO** | zero hits for `exc_info|exc_text|LogRecord|formatException|logging.Filter` |
| `logger-kit` 0.0.3 | **NO** | zero `exc_info|exc_text|formatException` hits; wrapper API needing call-site rewrites |
| `structlog` 26.1.0 | **NO (redaction)** / partial (rendering) | exhaustive grep for `redact\|scrub\|mask\|sanitiz\|secret` over the installed package returns **two** hits, both a docstring in `tracebacks.py::to_repr`. `processors.__all__` is formatting + exception rendering only. It supplies a pipeline; the scrubber would still be ours. |
| `python-json-logger` | **NO** | zero redaction hits. And `core.py:252-255` **inverts the stdlib precedence** — `exc_info` wins, `exc_text` is a fallback — so the "pre-set `exc_text`" mechanism is silently ignored under it |
| `detect-secrets` 1.5.0 | **NO** (as a per-record scrubber) | `core/scan.py:109 scan_line` exists but *detects*, never redacts; measured **4.80 ms** per 7-line traceback and flagged `Traceback`, `File`, `line`, `most`, `recent`, `ValueError`… as "Base64 High Entropy String". Redacting its hits destroys the traceback. Fine as a CI scanner. |
| `scrubadub` 2.0.1 | **NO** | wrong threat model (PII). Measured: `Authorization: Bearer sk-…` → the token **survived**, only the email was masked |
| `maskerlogger` 1.1.1 | **PARTIAL — the only one that touches exception rendering** | `masker_formatter.py:110` does exactly the `exc_info → format_exception → exc_text` route. But it masks `record.msg` and **never `record.args`**, so `super().format()` re-expands `msg % args` and re-emits the raw secret (measured: `lg.info("token is %s", SECRET)` **leaked in full**); and `RegexMatcher.match_regex_to_line` calls `line.lower()` unguarded, so a non-`str` `msg` raises `AttributeError` inside `format()` and **drops the record**. Adopting it would REGRESS against the filter we already have, which does cover `args`. |
| `maskingengine`, `presidio` | **unverified** — surfaced in search, neither installed nor read. Both PII/NER-oriented. |

**Conclusion — a clean packages-over-hand-rolling "side 2":** the package does not do the
job, so hand-roll, minimally. The gap is *one seam* (render the exception, scrub it with
the `_scrub_text` we already have, hand it to the formatter), not a second redaction
engine. `maskerlogger` is worth reading precisely because it proves the mechanism works
and shows two ways to get it wrong.

**Open, cheaper question for you (not decided here):** whether to vendor maskerlogger's
maintained 218-rule gitleaks corpus as a *data* dependency behind our own scrubber. Its
Aho-Corasick prefilter measured **7 µs** on the no-hit path, so cost is not the objection.

### 2.3 The three stdlib mechanics, with receipts

Read `/usr/lib/python3.14/logging/__init__.py`, `logging/handlers.py`:

- **(a) When a HANDLER filter runs, `exc_text` is not yet populated by that handler.**
  `Handler.handle` (`:1011`) calls `self.filter(record)` at `:1022` and `self.emit` at
  `:1027`. Measured: the filter observed `exc_text is None`, set a sentinel, and the
  sentinel is exactly what got emitted. **The pre-scrub trick works.**
- **(b) A pre-set `exc_text` suppresses re-rendering.** `Formatter.format` `:716-724`:
  `if record.exc_info: / if not record.exc_text: / record.exc_text = self.formatException(...)`.
  The `if not record.exc_text` guard is the whole mechanism.
- **(c) `exc_text` leaks across handlers — both directions, confirmed.**
  `Logger.callHandlers:1737` passes the **same record object** to every handler. Measured:
  plain-handler-first **emitted the real secret** and cached the RAW traceback for
  everyone downstream. The stdlib knows this class of bug and its own mitigation is *too
  late*: `QueueHandler.prepare` (`handlers.py:1498-1500`) formats and *then*
  `copy.copy(record)`.

(b) and (c) directly shaped the design in §3.2.

---

## 3. Half B — exception rendering is now EMITTED and SCRUBBED

### 3.1 RED, for the right reason, before any code changed

The demonstration the finding asked for did not exist. It does now:
`test_logging_setup.py::TestExceptionRenderingIsEmittedAndScrubbed`, 16 tests (13 written
up front; 3 added because the mutation proof proved two legs untested — §7.1). First run,
against the unfixed tree — **10 failed, 2 passed**, and the failures show the secret
*present*:

```
E   AssertionError: assert 'sk-deadbeef...456789abcdef' not in 'Traceback (...456789abcdef'
      'sk-deadbeefcafef00...def0123456789abcdef' is contained here:
        r password=sk-deadbeefcafef00d1234567890abcdef0123456789abcdef
E   KeyError: 'exc'
E   assert '***REDACTED***' in '{"ts": "…", "level": "ERROR", "logger": "loremaster.exc", "msg": "store.connect.failed"}'
```

The last line is defect #2 rendered as a test failure: the whole emitted record, with no
traceback in it.

⚠ **Honesty about the two that passed:** `test_a_record_with_no_exception_is_untouched`
passed correctly. `test_stack_info_is_scrubbed` passed **vacuously** — nothing was
emitted, so "the secret is absent" and "everything is absent" were the same string. I
caught that and added a positive control (`assert "Stack (most recent call last)" in …`)
so it now proves the stack is *present* before believing it is clean.

### 3.2 The mechanism, and why both carriers

Both carriers were built, routing through the same `_scrub_text` — one redaction policy,
two delivery points:

1. **`RedactingFilter`** renders the exception itself, scrubs it, and caches the result in
   `record.exc_text` — the attribute §2.3(b) proves the stdlib formatter honours *before*
   re-rendering. Any stdlib-compatible handler downstream therefore emits scrubbed text
   without knowing this filter exists. It also **scrubs an `exc_text` it finds already
   set**, which is the §2.3(c) repair case.
2. **`JsonFormatter` / `KeyValueFormatter`** call the shared `scrubbed_exception_text()`
   rather than depending on `exc_text` precedence — so lore's own sinks are safe even
   under a formatter-precedence surprise like python-json-logger's.

**Two bounds met deliberately and documented in the code** (per "when you cannot close a
hole, pin it"):

- `record.exc_info` is **not** cleared. It is shared state across handlers and other
  handlers may legitimately want the live exception. A formatter that ignores `exc_text`
  and re-renders from `exc_info` still sees raw text. lore's own formatters do not.
- Handler filters run in handler order. A handler *without* this filter formatting first
  emits raw and caches raw; this filter repairs `exc_text` for everyone after it but
  cannot un-emit. `configure_logging` attaches exactly one handler per namespace with
  `propagate=False`, so that ordering does not arise in lore's configuration today.

### 3.3 Shapes covered (a single-shape fixture is how this class stays green)

`logger.exception` · `logger.error(exc_info=True)` · `exc_info=<exception object>` ·
secret in the exception's own `str()` · **`raise X from Y`** (the "direct cause" leg) ·
**implicit context chain** (the "During handling" leg — a *different* traceback section) ·
**`__notes__`** via `add_note` · **the quoted SOURCE LINE** of a frame (a hardcoded
credential reaches the log even when the message is clean — a shape no message-only
scrubber covers) · `stack_info=True` · a foreign handler's already-cached raw `exc_text` ·
both formatters — **plus the filter under a plain `logging.Formatter`, which is the
finding's own scenario and the configuration that emitted the secret in full**.

Plus two guards that fail a *wrong* fix: a clean traceback must come out **unredacted and
intact** (a scrubber that nukes tracebacks is not better than one that drops them), and a
record with no exception must gain no field.

### 3.4 One behaviour change worth your eye

`exc_info=True` **outside** an `except` block gives the record the truthy-but-empty
`(None, None, None)` triple. The stdlib renders that as the useless line `NoneType: None`;
lore now emits no field at all. mypy found this edge, not I. Pinned by
`test_exc_info_true_with_no_live_exception_emits_nothing`.

The JSON key is **`"exc"`**, exported as `logging_setup.EXC_FIELD` (tests import it rather
than re-hardcoding). The alternative reading is `"exc_info"`, which is
`python-json-logger`'s convention and might matter for a Mezmo parser someone else writes.
I picked `"exc"`; say the word and it is a one-line change.

---

## 4. Half A — `SecretStr`, with an honest boundary

### 4.1 What it covers, completely

**Every secret that enters loremaster through `loremaster.config.resolve_secret` is now a
`pydantic.SecretStr` from resolution to point-of-use.**

- `resolve_secret() -> SecretStr` — the one entry seam.
- **12 connection owners** now declare `password: SecretStr` and hold it as such:
  `store/surreal.py`, `index/surreal_manifest.py`, `graph_surreal.py`,
  `index/snapshots.py`, `memory/local.py`, `agents.py`, `briefs.py`, `findings.py`,
  `tasks.py`, `messages.py`, `diff.py`, and `scout.py::_open_command_connection`.
- **`auth.py`** — `ApiKeyVerifier` holds `dict[str, SecretStr]` for the live bearer-key
  set and unwraps only inside `verify`'s constant-time comparison.
- **The unwrap has ONE implementation**: `store/_txn.py::signin_credentials`. Before this
  wave, twelve modules each hand-rolled `{_SIGNIN_USER_KEY: self._user, _SIGNIN_PASS_KEY:
  self._password}` with **twelve private copies of the `"username"`/`"password"` constant
  pair**. Adding `.get_secret_value()` to each would have been twelve copies of the unwrap
  *policy* — the #102 sin. It is now one function that all twelve call, in the module they
  already import `bootstrap_session` from (zero new import edges). The test harness's two
  copies route through it too.

**The username is deliberately NOT a secret.** It is a public default named by
`SURREAL_DEFAULT_USER_ENV`, it is interpolated into no log or error message in the package
(verified: `self._user` appears only in assignment and in the signin payload), and typing
it as a secret would dilute the signal until nothing reads as one. It is unwrapped
explicitly at its four resolution sites, each with the reason inline. *The alternative
reading — "`resolve_secret` returns secrets, so both halves are secrets" — is coherent and
would have been simpler; I rejected it for the signal-dilution reason and because it
doubles the migration. Reversible in an afternoon if you disagree.*

### 4.2 The pins (and what wrong build each one kills)

New `loremaster/tests/test_secret_typing.py`, 16 tests:

| pin | the wrong build it kills |
|---|---|
| `resolve_secret` returns `SecretStr`; `repr`/`str`/f-string/container-`repr` all hide the value | the status quo |
| byte-exactness survives the wrapper | a "fix" that strips or mangles the credential |
| **∀ AST scan**: every `password`/`api_key` parameter in the whole package is annotated `SecretStr` | a *new* credential-carrying constructor written next year — caught by the pin, not by an auditor's memory |
| **runtime leak scan** over the *derived* set of connection-owner classes: no `repr`/`str`/`vars()` shows the value | a build that accepts `SecretStr` and stores `.get_secret_value()` — this passes the AST pin and fails here |
| `ApiKeyVerifier` renders nothing **and still authenticates** | a "fix" that hides the key by breaking auth |
| `signin_credentials` is the only site constructing the SDK payload (AST scan for the literal key set, one file exempt) | routing-is-not-sharing: a caller that calls the shared helper *and* keeps its own literal |

**Three positive controls, because a probe needs one:** the AST scan asserts it found ≥10
parameters (a silently-matching-nothing scan would pass vacuously); the class scan asserts
it actually *constructed* ≥8 owners (my first version skipped every constructor needing an
extra argument and passed on an empty set — caught and fixed); and a deliberately-leaky
throwaway class proves the rendering oracle can *see* a leak.

**One bound stated as a test:** the AST pin is keyed on parameter *names*, and the set of
names a future secret could wear is unbounded (`value`, `credential`, `bearer`…). It is
the cheap mechanical half; the runtime leak scan is the ∀ instrument that does not depend
on names. `test_the_pin_is_keyed_on_names_and_says_so` records this so the pin cannot be
mistaken for total coverage.

### 4.3 THE NAMED BOUNDARY — what Half A does NOT cover

**The Anthropic API key is still a bare `str`** at exactly two sites:
`calibration/counting.py::AsyncClaudeTokenCounter.__init__` and
`calibration/engine.py::CalibrationEngine.__init__`. These are the only two `api_key`
parameters in loremaster.

**Why deferred, not dropped:** both files were held modified-and-uncommitted by
`fix-207-jitter` for the whole of my wave. Migrating them meant committing another agent's
in-flight work under my commit message. The alternative — leaving my committed AST pin RED
— pollutes a baseline the whole packet diffs against.

**So they are PINNED, not allowlisted.** An allowlist entry asserts "this is safe", which
would be a lie. `DEFERRED_BARE_STR_SECRETS` + `TestDeferredApiKeyBound` assert the two
sites **are still bare `str`** and go **RED the day someone fixes them**, carrying:

> *if you closed them DELIBERATELY, that is exactly right: delete them from
> `DEFERRED_BARE_STR_SECRETS`, delete this test if the set is now empty, and say so in
> your report.*

A second pin asserts the deferred set names sites that still exist, so a stale entry cannot
make the first pin unfalsifiable.

**The remaining change, in full** (≈20 minutes): annotate both parameters `SecretStr`,
store them as such, unwrap at `counting.py`'s `"x-api-key"` header dict, and delete the
one deferred unwrap I left at `server.py`'s `CalibrationEngine(...)` construction (marked
in-code, pointing at the pin). **Re-open trigger:** the moment #207 lands, or any wave
touches either file.

**Also outside this wave, and outside loremaster** (flagged, not touched — §8):
`loresigil` has its own hand-rolled secret resolver and its embedder API keys are bare
`str` end to end.

---

## 5. Gates

All measured 2026-07-25 in `/home/ejprice/PycharmProjects/lore-pkt11i`, against my two
commits `f65e062` (Half A) and `a68cfe7` (Half B).

### 5.1 `./scripts/typecheck.sh` — ZERO delta

The gate does not pass, and could not: it was already failing on the inherited packet-03b
RED. So the honest measurement is a **delta**, taken against a pristine export of HEAD
(`git archive HEAD` into `/tmp/base211`, so the comparison is a real tree and not a memory):

| tree | result |
|---|---|
| pristine `HEAD` (`c32800d`) | `Success` (lorescribe) · `Success` (loresigil) · **`Found 109 errors in 3 files (checked 150 source files)`** |
| my tree | `Success` · `Success` · **`Found 109 errors in 3 files (checked 151 source files)`** |

Same 109, same 3 files (`test_comms_tool.py`, `test_comms_promise_registry.py`,
`test_comms_wiring.py` — all packet-03b contract RED, e.g. `"AppContext" has no attribute
"message_ledger"`, which does not exist yet). 151 vs 150 files is my new test module.
Cross-check: `grep -icE "SecretStr|password|api_key|signin_credentials|resolve_secret"`
over the residual errors returns **0**.

⚠ **mypy did NOT catch everything, and that is worth carrying forward.** It is blind
through `dict[str, Any]`: `test_retry_seam.py::_CTOR_VALUES` feeds constructors from an
untyped mapping, so the type gate was at zero delta while **119 tests in that file were
broken at runtime**. Only the full suite found it. See §8.4.

### 5.2 `uv run ruff check .` — clean

`All checks passed!`

### 5.3 pytest — with counts

| scope | result |
|---|---|
| `test_logging_setup.py` (Half B, whole module) | **34 passed** (16 of them the new class) |
| `test_secret_typing.py` (Half A) | **16 passed** |
| the 18 suites my change touches, `-n auto` | **2146 passed, 14 skipped** |
| **full suite**, `-n auto -q --tb=no` | **394 failed, 6222 passed, 17 skipped, 3 xfailed** in 162.82s |

**The baseline diff, which is the claim that matters.** Against the enumerated inherited
list (`docs/plans/v2/receipts/2026-07-24-packet11i/baseline-red-at-d0ee2be.txt`, 394 ids):

```
$ comm -23 <my failures> <baseline>     # NEW failures
                                         (empty)
$ comm -13 <my failures> <baseline>     # baseline entries that changed
0
```

**The failure set is identical to the inherited baseline — zero new, zero disturbed.**
Passing count rose 6138 → 6222.

⚠ **An earlier run of mine was NOT clean and I am recording it rather than only the green
one.** The first full run showed **515 failed** — 119 new in `test_retry_seam.py` (the
`_CTOR_VALUES` breakage above), 1 in `test_surreal_harness.py` (I had violated operator
RULING 1 by adding a module-level `store._txn` import to the harness; its own pin caught
me — §8.6), and 1 in `test_calibration_engine.py` which was `fix-207-jitter`'s, not mine.
The first two are fixed; the third resolved itself when they committed.

---

## 6. The worktree collision (deviation 1, in full)

`/home/ejprice/PycharmProjects/lore-pkt11i` was **not quiescent**. `fix-207-jitter`
(finding #207, the shared jittered-backoff policy) worked it concurrently for my whole
session. Observed: HEAD moved `31d9e58` → `c32800d` mid-wave; their `server.py`,
`test_agent_registry.py` and `test_comms_tool.py` edits appeared and then vanished into
that commit; `REPORT-fix-207-jitter.md` appeared at the repo root.

**Their files, which I did not stage and did not intentionally edit:**
`loremaster/loremaster/calibration/{counting,engine}.py`,
`loremaster/tests/{test_calibration_engine,test_backoff_seam}.py`,
`loresigil/loresigil/{backoff,resilient}.py`, `loresigil/tests/*`, `loresigil/pyproject.toml`,
`scripts/token_survey.py`, `uv.lock`.

**My contamination, disclosed:** before I noticed, I ran `uv run ruff check --fix .`
repo-wide. It applied one `I001` import-sort fix to **their** `calibration/counting.py`.
Content-neutral, but it is an edit to a file another agent held open. No other file of
theirs was touched by me. After noticing, every subsequent `ruff --fix` was scoped to
explicit paths, and both commits stage explicit path lists.

**Two of their failures appear in my full-suite run and are NOT mine:**
`test_calibration_engine.py::TestEndpointLifecycle::test_backoff_doubles_and_caps` (their
jitter change vs an old "doubles and caps" assertion) and the `test_backoff_seam.py` /
`test_anchored_pattern_seam.py` additions.

**Your call:** should we be sharing this worktree at all?

---

## 7. Mutation proofs

`scripts/mutation_proof.py` was unavailable (§8.5), so I followed its discipline by hand
and mechanised it as a throwaway harness: **declare the expected-RED node ids BEFORE the
run** (never transcribed from the output), **assert the mutation LANDED** (md5 before/after
— a no-op patch that "passes" is the failure mode), **diff BOTH ways**, and **restore from
a `cp -a` content backup, proving byte-exactness by md5**.

| # | mutation | declared RED | result |
|---|---|---|---|
| **M1** | `scrubbed_exception_text` stops calling `_scrub_text` | 8 tests | ⚠ **ALL 8 STAYED GREEN** — see below |
| **M1b** | same, after the fix | 2 new tests | exactly those 2 RED, nothing else |
| **M2** | `RedactingFilter`'s whole exception leg deleted (pre-#211 behaviour) | 2 tests | exactly those 2 RED, nothing else |
| **M3** | `JsonFormatter` stops emitting the exception (defect 2 restored) | 7 tests | all 7 RED **+ 4 undeclared** (the `REDACTED in output` assertions — nothing emitted, so nothing redacted). My declaration was incomplete; the both-ways diff caught it. |
| **M4** | `resolve_secret` returns a bare `str` again | 4 tests | exactly those 4 RED, nothing else |
| **M5** | **the sharing proof** — `_SIGNIN_USER_KEY` in `store/_txn.py` changed to `"usernameMUTATED"` | every connection owner | **766 errors + 11 failures across all 12 owner suites** |

Every mutation restored byte-exact (md5 verified); `git status` on all three mutated files
is clean, and the gates were re-run afterwards at the same numbers.

### 7.1 M1 is the one that earned its keep

**Every single declared-RED test stayed GREEN.** The mutation had landed in code no test
reached: all my tests go through `configure_logging`, where the FILTER scrubs `exc_text`
before any formatter runs — so the formatters' own scrub was pure belt-and-braces, and
**entirely untested**. Deleting it changed nothing observable. M2 then showed the mirror
image: the filter's render leg was equally invisible.

That is the "a runtime gate is an invariant only over code it actually RUNS" failure, found
in my own fix. Three pins now cover both legs directly — the two formatters exercised
WITHOUT the filter, and the filter exercised under a plain `logging.Formatter` (the
finding's own scenario, and the configuration that emitted the secret in full before this
work). They are in the amended Half B commit.

**Had I only reported "mutation proof: RED, restored", I would have shipped two dead legs
and a receipt saying they were proven.**

### 7.2 M5 — sharing proven by mutation, not by inspection

Changing ONE constant in `store/_txn.py` broke **all twelve** connection-owner suites:

```
115 test_task_ledger      105 test_surreal_store    101 test_message_ledger
 99 test_graph_surreal     71 test_findings          64 test_agent_registry
 60 test_surreal_manifest  55 test_memory_backend    53 test_brief_ledger
 24 test_diff              12 test_snapshots          7 test_scout
```

No owner kept a private copy wearing the shared name — which was exactly the state of the
tree before this wave (twelve hand-rolled `_SIGNIN_USER_KEY`/`_SIGNIN_PASS_KEY` pairs).
This is the test that distinguishes DRY from looks-DRY.

---

## 8. Raised, not folded in (scope law)

Everything below is outside my mission. I fixed none of it.

1. **`loresigil` has a SECOND, hand-rolled secret resolver.**
   `loresigil/loresigil/factory.py::_resolve_api_key` duplicates
   `loremaster.config.resolve_secret`'s job (read env var, fail loud when unset/empty) and
   cannot call it — loremaster imports loresigil, so the dependency cannot reverse.
   Its embedder API keys are bare `str` end to end
   (`voyage_cloud.py::__init__`, `voyage_context.py::__init__`,
   `voyage_http.py::build_bearer_client` → `headers={"Authorization": f"Bearer {api_key}"}`).
   `pydantic>=2.13` is already a loresigil dependency, so `SecretStr` is available there
   with no new dep. **Recommend:** a follow-up wave that migrates loresigil's key path and
   decides whether the two resolvers become one (in a shared lower package) or stay two
   with the duplication documented.

2. **A THIRD hand-rolled resolver, reading a `.env` file.**
   `loremaster/loremaster/calibration/counting.py::load_api_key` and
   `scripts/token_survey.py::load_api_key` are two copies of *each other*, and neither is
   `resolve_secret`. Both return bare `str`. `counting.py`'s docstring says "Mirrors
   `token_survey.load_api_key`" — which is the "reference pattern in a doc" antipattern
   #102 exists to kill.

3. **The AST pin's blind spot, stated so it cannot be inherited silently.**
   `ApiKeyVerifier.add_key`'s secret parameter is named `value`, so a name-keyed scan
   cannot see it. I typed it `SecretStr` anyway and pinned it *behaviourally*, but the
   general problem stands: a future secret parameter named `credential`/`bearer`/`token`
   would pass the AST pin. Recorded in-test rather than fixed, because enumerating
   forbidden names is exactly the losing move.

4. **mypy is blind through `dict[str, Any]`, and that cost me a real breakage.**
   `test_retry_seam.py::_CTOR_VALUES` is an untyped ctor-value mapping; my migration
   passed `./scripts/typecheck.sh` at zero delta while **119 tests** in that file were
   broken at runtime. Only the full suite caught it. Worth knowing generally: a type
   migration's gate is *not* mypy alone wherever an `Any`-typed mapping feeds a
   constructor.

5. **I could not use `scripts/mutation_proof.py`.** It exists only in the MAIN checkout,
   untracked, from another session. I deliberately did **not** write a second one (that is
   copy #2 of a policy), and instead followed its discipline by hand — declared expected-RED
   node ids from `--collect-only` before each run, diffed both ways. **Recommend:** land
   that helper so the next agent is not in this position.

6. **A pre-existing operator RULING I tripped and restored.** RULING 1 (2026-07-20) forbids
   a module-level `loremaster.store._txn` import in `_surreal_harness.py`. My first patch
   added one; `test_surreal_harness.py`'s own pin caught it and I moved the import
   in-function. Noting it because the pin worked exactly as designed and is worth keeping.
