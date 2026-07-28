# REPORT-refactor-pkt42-1 — packet 42 REFACTOR phase

> ⚠ **SUPERSEDED SYMBOLS (dated record):** mentions `_BRIEF_PUBLISH_`, a retired prefix (the
> private mint-retry constants deleted by finding #108 — `_txn.retry_on_conflict` owns that
> policy now). It appears here only inside REPRODUCED TEST OUTPUT: this record quotes the
> packet-11i/03b doc-banner failure that packet 42 inherited and verified as unrelated to its
> own work. Preserved as-written per the archive law; read it as history, not instruction.

brief-base v7 read

- **state:** done
- **deviations:** one, disclosed — I briefly added an assertion to `lorerunes/tests/test_smoke.py`, judged it a CONTRACT act, and reverted it to a byte-identical body before any gate was run against it (§2.8, §4.E).
- `Packages considered:` **none — no mechanism specified.** This phase built no mechanism; it moved no policy and added no dependency. The one dependency question in range (`python-dotenv` vs `python-decouple`) was already settled by ruling R2 with a read-and-measured rationale, and I re-read it rather than re-opening it.
- **decisions-needed (5, none blocking):** ① 🔴 `scripts/scratch_provenance.py::WORKSPACE_MEMBERS` still missing `lorerunes` — now **mandated by CLAUDE.md at `d252802` as registration site #7**, code not yet compliant (§4.A) · ② two `token_survey` constants went production-dead in this packet and are now held alive only by a parity assertion (§4.C) · ③ the `forbidden_prose` blocklist covers `logging_setup.py` but not the test tree that carried the same corpse prose (§4.D) · ④ `lorerunes/tests/test_smoke.py` cannot discriminate a namespace-package shell (§4.E) · ⑤ `LORE_NAMESPACES` still excludes `lorerunes` — previously ruled not-needed; re-confirmed still correct (§4.B).
- **receipt pointers:** gates §1 · changes §2 · mutation proof §3 (89/89 both directions) · not-acted-on findings §4 · declined refactors §5.
- **base:** work done against `f582ee0`. HEAD moved to `d252802` mid-run (docs-only, `CLAUDE.md`); no code moved, so every gate above stands. That commit independently corroborates finding §4.A and promotes it to standing law — **the code half is still outstanding.**

---

## 0. Scope and what "green" means here

This is **pure-logic, fixed-spec code** — secret resolution, header construction, a blankness
predicate, a regex redactor, and workspace registration. Its outputs are fixed by the packet
spec and rulings R1–R32, not derived from a data distribution. **The data-driven-validation
clause of my role therefore does not apply, and I say so explicitly:** green tests plus the
typecheck and lint gates are a sufficient completion criterion for this refactor. No backtest,
holdout, or scored oracle is owed.

Every change below is behaviour-preserving. I weakened, retargeted, loosened, re-scaled and
deleted **zero** assertions; the collected test-node set is byte-identical before and after
(§1, §3).

**Tool honesty (brief-base §4).** I did not use lore's MCP for any structural question. The
brief states the index points at the primary checkout rather than this worktree (#134/#125),
so every sweep here was direct `grep`/`git grep`/AST over the worktree, plus `ast.parse` for
the call-site enumerations in §3. Stating the fallback per the dogfood protocol; the grep
grounds are the sanctioned ones (rename-exhaustiveness, non-symbol textual seams, and a
cross-cutting map).

---

## 1. Gates — final tree

Scoped contract run (the brief's command, verbatim):

```
383 passed in 6.33s
```

Typecheck, all five members, each its own iteration:

```
typecheck: lorerunes OK
typecheck: lorescribe OK
typecheck: loresigil OK
typecheck: loremaster OK
typecheck: skills OK
```

Ruff:

```
All checks passed!
```

R25's required co-run (`test_calibration_counting.py`, the only file exercising the R19 shape
change) — run because §2.2 edits `counting.py`:

```
16 passed in 0.20s
```

**Coverage preservation, proven rather than asserted.** `test_logging_setup.py` is the file
this refactor changed most. Its collected node ids were captured before and after and diffed:

```
=== NOW ===    44 tests collected
=== BEFORE === 44 tests collected
=== NODE-ID DIFF (empty = identical test set) ===
IDENTICAL
```

The full-suite receipt is in §6.

---

## 2. What changed — 8 files, all behaviour-preserving

### 2.1 `logging_setup.py` — string concatenation → f-string, proven byte-identical

`_AUTH_HEADER_RE` was built with `+` concatenation around a `"|".join(...)`. The house rule is
f-strings; the brief names string concatenation explicitly. Because a regex is not a place to
take a cosmetic risk, the two forms were evaluated side by side **before** the edit:

```
current : (?i)(\bauthorization\b\s*[=:]\s*)(?:(Bearer|Basic|Digest|Token|ApiKey)(\s+))?(\S+)([^\n]*)
proposed: (?i)(\bauthorization\b\s*[=:]\s*)(?:(Bearer|Basic|Digest|Token|ApiKey)(\s+))?(\S+)([^\n]*)
BYTE-IDENTICAL: True
```

and re-asserted against the compiled object after the edit (`_AUTH_HEADER_RE.pattern` equals
the pre-edit literal). Behaviour cannot have moved.

### 2.2 Prose that no longer matched the code — six sites, each derived not guessed

This is the repo's most expensive defect class, and packet 42 deleted a great deal. I swept
with **bare, anchor-free** patterns per CLAUDE.md, and adjudicated every residual hit
individually (§5 carries the ones I did **not** change, with reasons — no wholesale
classification).

| # | site | what was false | how I derived the truth |
|---|---|---|---|
| 1 | `logging_setup.py` module docstring | named **two** of the three surviving patterns — the bare `Bearer …` pass that fires with no `Authorization` label was undocumented | probed `_scrub_text` on five shapes; `curl -H 'Bearer sk-…'` is redacted with no `Authorization` present, so the pass is real and separately observable |
| 2 | `counting.py` module docstring | *"it replicates the shape and the constants"* — packet 42 **reversed the direction**: `token_survey.py` now imports `build_auth_headers` and `load_api_key` FROM here | read both modules; named exactly what is shared (2 functions) vs still replicated (4 constants + the counter class), and which parity test pins each |
| 3 | `test_secret_typing.py` | quoted `MEMBERS=(lorescribe loresigil loremaster)` — packet 42 changed that list | `grep '^MEMBERS=' scripts/typecheck.sh` → `(lorerunes lorescribe loresigil loremaster skills)` |
| 4 | `test_secret_typing.py` | *"`skills/` … sits outside `testpaths` AND outside `scripts/typecheck.sh`"* — **ruling R9 closed the second half in this very packet** | ground truth: `skills` IS in `MEMBERS`, and `typecheck: skills OK` runs |
| 5 | `test_secret_resolution_seam.py` ×2 | same R9 claim, in a docstring and in a pin comment | same |
| 6 | `Containerfile` | enumerated 2 of the 3 workspace-source declarations | `grep 'workspace = true'` across the member pyprojects |

**Sites 3–5 are the sharpest finding of this phase.** R9's *substance* was implemented — the
gate genuinely extends over `skills/` and runs there — but the prose describing the gap it
closed was never updated. A reader is taught that `skills/` is mypy-ungated, which would
justify either re-doing R9 or treating `probe_embed.py` as type-unchecked. This is the
rider-dropped shape from CLAUDE.md's own §"THE RIDER IS PART OF THE RULING", one level up: the
ruling landed, the *description* of the world it changed did not.

I preserved each site's original point (`scripts/` really is unseen by mypy; `skills/` really
is outside `testpaths`) and stated the enumerations as **shapes** rather than lists, so the
next member added does not re-stale them.

### 2.3 Corpse prose inside the test file — three sites

Adjudicated individually against the code at `f582ee0`:

- **`TestRedactingFilter` docstring: *"bearer / api_key / high-entropy tokens are scrubbed"*** —
  **FALSE.** High-entropy tokens are the thing packet 42 deleted and pins as an accepted bound.
  Rewritten, with a note recording that the module has a prose blocklist for exactly this and
  the test tree has none — which is *how this sentence survived the deletion it describes*.
- **`test_does_not_redact_realistic_paths_and_identifiers` comment: *"must survive the entropy
  backstop verbatim … the fix splits on those separators"*** — **STALE**; presumes a backstop
  and a tuning that no longer exist. The test's property is unchanged and now holds for a
  stronger reason (nothing inspects an unlabelled run at all).
- **`_leak_from_a_literal_credential` pin comment: *"`_ASSIGNMENT_RE` fires before the entropy
  sweep"*** — **STALE**; there is no sweep to fire before. The real reason for the open-ended
  assertion is `(\S+)` over-consumption, which is residual R12, ruled pre-existing and out of
  packet scope — now named as such.

**Not one assertion was touched.** Node-id diff in §1 is the receipt.

### 2.4 `scout.py` — a comment block with a blank line between every line

The block packet 42 re-authored carried four interleaved blank lines (verified pre-existing at
`6a21fb6`, so not introduced here — but inside text this packet rewrote). Removed. Confirmed
isolated: an AST-free scan found exactly these four in the whole file and none elsewhere.

### 2.5 The test de-bloat — `_logging_fixtures.py` had ONE consumer while claiming two

`_logging_fixtures.py` is new in packet 42 and opens:

> *"`test_logging_setup.py` … and `test_secret_leak_vectors.py` … **both** need to build a real
> `LogRecord`, snapshot/restore the global lore namespace logger state, and drive an emission
> through the REAL `configure_logging` handler."*

**Only `test_secret_leak_vectors.py` imported it.** `test_logging_setup.py` still carried its
own private copies of all four things:

| shared thing | private copy in `test_logging_setup.py` |
|---|---|
| `SILENCED_THIRD_PARTY` | identical tuple |
| `make_record` | identical body |
| `restored_lore_logger_state` | identical snapshot/restore, inlined in the autouse fixture |
| `emit_through_configured_logger` | `TestExceptionRenderingIsEmittedAndScrubbed._emit`, identical but hardcoding `"loremaster"` where the shared one derives it from `LORE_NAMESPACES[0]` |

This is the brief's sanctioned de-bloat (*"consolidating duplicate fixtures and setup into a
shared fixture/helper"*), it removes a genuine second copy of a policy the packet itself
declared shared, and it makes the module's own docstring **true**. Four definitions deleted, 12
`_make_record(` and 13 `self._emit(` call sites repointed, `Callable` import dropped as newly
unused. Coverage identical (§1); sharing proven by mutation (§3).

Behavioural equivalence of the `_emit` → `emit_through_configured_logger` swap, checked before
the edit rather than after: same namespace (`LORE_NAMESPACES[0]` **is** `"loremaster"`), same
child (`"exc"` default), same level (`"DEBUG"` default); the shared version adds only a failure
*message* on its `isinstance` assert. The one assertion that reads a filename
(`assert "test_logging_setup.py" in parsed[EXC_FIELD]`) is fed by the traceback of the `action`
closure, which still lives in `test_logging_setup.py` — verified before moving.

### 2.6 `lorerunes/tests/test_smoke.py` — the missing docstring

The only undocumented function packet 42 added. Now carries a module docstring explaining why a
near-empty test module is correct here (it is the member's `testpaths` anchor — consequence 4 of
CLAUDE.md's six registration sites; an entry that collects nothing is a hope with a filename)
and where the real `is_blank` pins live. **The test body and its node id are byte-identical to
`HEAD`** (verified with `cat -A`).

### 2.7 Docstrings / type hints / magic values on packet-42-added code

Checked and already clean — nothing to do. Every function the packet added
(`counting.build_auth_headers`, `counting.load_api_key`, `config.resolve_secret`,
`config.resolve_config_value`, `logging_setup._redact_auth_header`, `logging_setup._scrub_text`,
`lorerunes.is_blank`, `voyage_http.build_auth_headers`,
`factory.EmbeddingConfig._reject_a_blank_credential`, `probe_embed._resolve_key`) has a
docstring with Args/Returns/Raises and complete annotations. A grep of **only the lines packet 42
added** found no `%s`, no `.format()`, and exactly one string concatenation — the one fixed in
§2.1. No `NotImplementedError`, no `TODO`, no `FIXME` anywhere in the diff.

### 2.8 The deviation, stated plainly

While adding the `test_smoke.py` docstring I also strengthened its assertion from a bare import
to a predicate check. I then judged that **adding** an assertion is a CONTRACT decision, not a
refactor one, and reverted the body to byte-identical before running any gate against it. The
finding that motivated it is filed as §4.E for the lead to rule on, and recorded in the file's
docstring as a known weakness rather than silently fixed.

---

## 3. Prove sharing by MUTATION — 89 declared reds, both directions

Repo law: *routing is not sharing; change the shared thing and every caller must break.* The
de-bloat in §2.5 is a DRY claim, so it gets the DRY proof, using the repo's own instrument
(`scripts/mutation_proof.py`, which diffs the observed RED set against a declared one **both
ways** — catching a mutation that lands in dead code as well as one that over-reaches).

**The declared set was derived from SOURCE before any run**, by `ast.parse`-walking both test
modules for tests that reach `emit_through_configured_logger`, then resolving those names to
node ids via `pytest --collect-only -q` (per the instrument's own bound: never transcribe a
declared set from output, and never hand-write parametrised ids). 21 test functions → **89 node
ids**.

Mutation: the shared helper's `isinstance` assert replaced with an immediate `raise
AssertionError`.

```
89 failed, 136 passed in 3.71s

tree restored byte-exact (loremaster/tests/_logging_fixtures.py: md5 e2d70dea94ca09a841732bfa2d9567d1)

PROOF HELD — the declared RED set fired EXACTLY
```

The 89 span **both** files — 13 nodes in `test_logging_setup.py` and 76 in
`test_secret_leak_vectors.py`. That is the "ONE implementation, TWO contracts" claim in
`_logging_fixtures.py`'s docstring, now demonstrated instead of asserted. `git diff --stat` on
the fixture file after the run is empty, confirming the restore.

Note the direction that matters: before this refactor the same mutation would have reddened
**only** `test_secret_leak_vectors.py`, because `test_logging_setup.py` held a private copy
wearing the shared name — the exact #102 shape.

---

## 4. Found, NOT acted on — all five need a decision above my phase

### A. `scripts/scratch_provenance.py` is a 7th registration site, still missing `lorerunes` 🔴

> **UPDATE — corroborated by the lead, independently, while this phase was running.** HEAD moved
> from `f582ee0` to **`d252802`** ("docs: the registration list is SEVEN sites — and has been wrong
> twice while being written"), a **docs-only** commit that adds exactly this file to CLAUDE.md's
> registration list as **site #7**. So the LAW has landed. **The CODE has not:** re-derived at
> `d252802`, `scratch_provenance.py::WORKSPACE_MEMBERS` is still the 3-tuple, while its sibling
> guard `conformance_provenance.py::WORKSPACE_MEMBERS` already carries the 4-tuple. That is
> "filing a rule does not install it", same-day. I did not make the edit: the lead is demonstrably
> mid-flight on this exact item, and a second hand in the same file is how a fix gets applied
> twice or reverted. Raising it to the top of the decisions-needed list instead. Everything below
> was written before that commit and reads unchanged.


```python
# The workspace members whose code a scratch copy must actually be running.  Mirrors
# ``[tool.uv.workspace] members`` in pyproject.toml.
WORKSPACE_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")
```

The comment's claim — *"Mirrors `[tool.uv.workspace] members`"* — is **false** as of `f582ee0`;
that list is now four. This is the `#140` provenance guard behind `scripts/scratch_copy.sh`,
i.e. the tool CLAUDE.md mandates for every scratch mutation proof.

**Consequence:** a scratch copy made for a future mutation proof never verifies `lorerunes`'
provenance, so a copy importing the *original* checkout's `lorerunes` passes the guard silently
— which is the precise failure the guard exists to make impossible.

CLAUDE.md's `lorerunes` section enumerates **six** registration sites and warns, in its own
text, *"this list was written with five entries and `mypy_path` was the one missed — grep for the
existing members by name before trusting any list of registration sites, including this one."*
I did that grep; this is the site the list does not name. The stub agent flagged it
independently (its §5b) and it was never actioned.

Exact edit, if the lead wants it: add `"lorerunes"` to the tuple. `scripts/test_scratch_copy.py`
does **not** pin the tuple (verified), so no test breaks. I did not make it because adding a
member to a guard's coverage is a behaviour change and therefore a CONTRACT call.

### B. `logging_setup.LORE_NAMESPACES` still excludes `lorerunes` — re-confirmed correct 🟢

`("loremaster", "loresigil", "lorescribe")`. `lorerunes` emits no logs and has no logger, so
adding it would be speculative. The stub ruled this not-needed-today **with a named re-open
trigger** (*the day `lorerunes` acquires a `getLogger(__name__)`, its records propagate to root
un-namespaced and escape the redaction handler config*). I re-derived it and agree — recorded
so the lead knows it was checked, not missed.

### C. Two `token_survey` constants went production-dead in this packet 🟠

Measured mention counts in `scripts/token_survey.py` (definition included):

```
ANTHROPIC_COUNT_TOKENS_URL: 2   <- still live (used at the post call)
ANTHROPIC_VERSION:          1   <- DEFINITION ONLY
ANTHROPIC_API_KEY_ENV:      1   <- DEFINITION ONLY
DEFAULT_ENV_FILE:           2   <- still live (argparse default)
```

Packet 42 killed the last two: the version header now comes from
`counting.build_auth_headers`, and the env-var name from `counting.load_api_key`. Their only
remaining consumer anywhere is `TestConstantsParity`, which asserts `counting.X == ts.X`.

So that assertion now compares a live constant against a replica **nothing reads**. It still
discriminates (editing the dead replica reddens it), but it guards a value that can no longer
affect the wire. Two options, both CONTRACT calls: delete the two constants *and* their parity
legs, or keep them and say in the test why they exist. I changed nothing — deleting them would
break an assertion, which I may not do.

### D. The `forbidden_prose` blocklist covers the module but not the test tree 🟠

`test_secret_leak_vectors.py::test_the_module_prose_no_longer_teaches_a_mechanism_it_does_not_run`
reads `logging_setup.__file__` and rejects `["Shannon entropy", "high-entropy token", "entropy
threshold", "catch-all backstop"]`. It is a good instrument and the adversary reported it firing
twice for real value.

**Its reach stops at the production module** — which is exactly why the three corpse-prose sites
I fixed in §2.3 survived, one of them a class docstring stating outright that high-entropy tokens
are scrubbed. Per CLAUDE.md (*"every audit-caught defect class becomes a repo-local invariant
test"*), the natural close is to extend the ∀ over the packet's own test modules. That widens a
pin's scope, so it routes to `tdd-contract`, not to me. I recorded the gap in the docstring I
rewrote so the next reader meets it deliberately.

### E. `lorerunes/tests/test_smoke.py` cannot discriminate a namespace-package shell 🟠

Asking the repo's own question — *what WRONG build would this still pass?* — `def test_import():
import lorerunes` passes against a `lorerunes` installed as an **empty namespace package**
(`__file__ = None`, no production code loaded). That is poison mode 3 of finding #140, and it is
what a plain `uv sync` without `--all-packages` produces. Asserting on `is_blank` instead of the
bare import closes it in one line. **This is the deviation I reverted (§2.8)** — filed here as a
recommendation and documented in the file.

### F. Two `.get_secret_value()`-adjacent observations, both pre-existing, neither packet 42's

- **`logging_setup.FORMAT_JSON` is unused** — and was already unused at base `6a21fb6` (verified
  against the base blob), so not this packet's. It is a public-looking, documented selector
  constant; deleting it is a small API change, not a refactor.
- **`_redact_auth_header` binds `first_token` and never uses it.** Deliberate
  documentation-by-naming of capture group 4 (the credential, which is replaced). Invisible to
  ruff by design. Left alone — the unpacking is what makes the five-group regex readable.

---

## 5. Refactors I considered and DECLINED, with reasons

Per the brief: several things here look like duplication and are ruled. I verified each against
the inventory before deciding, and acted on none.

| candidate | verdict |
|---|---|
| **Two typed auth seams** (`counting.build_auth_headers`, `voyage_http.build_auth_headers`) | **RULED — R26 constraint 1.** `loresigil` cannot import `loremaster` (#222); the enforcement is the TYPE SIGNATURE, not a shared body. They are also genuinely different policies (3 headers with `x-api-key` vs 1 with `Authorization: Bearer`). Collapsing would re-open a settled design. |
| **`probe_embed.py::_resolve_key` duplicating `resolve_secret`** | **RULED — R14**, deliberately stdlib-only, with a documented re-open trigger and a structural pin. Untouched. |
| **Per-package validators calling shared `lorerunes.is_blank`** | Already ONE implementation, proven by an existing cross-caller mutation pin. Nothing to do. |
| **`resolve_secret` / `resolve_config_value` share a blank-check + raise** | **Declined.** R17 makes them two policies with different return types and deliberately different messages; the *predicate* is already shared via `lorerunes.is_blank`, so what is left is six lines of glue. Extracting a helper with a `kind` parameter would make the two operator-facing messages less greppable — a real cost in a repo whose law is that served English must be derivable. Reporting rather than acting, since it is a design call. |
| **The two counters (`AsyncClaudeTokenCounter` / `ClaudeTokenCounter`)** | **Declined.** Near-duplicates by design (sync vs async), pre-existing, and held in lock-step by `TestConstantsParity` + `TestRequestShapeParity`. Packet 42 already shared the two pieces that are *policy*. Collapsing further is a design decision. |
| **`token_survey.ClaudeTokenCounter.count`'s raw `200`/`429`/`500`/`200`/`60.0`** | **Declined — flagged instead.** `counting.py` has named constants for all five (`_HTTP_OK`, `_HTTP_TOO_MANY_REQUESTS`, `_HTTP_SERVER_ERROR_FLOOR`, `_ERROR_BODY_SNIPPET`, `_HTTP_CLIENT_TIMEOUT_S`); its sync twin does not. Pre-existing and **outside packet 42's diff** — the packet touched only that method's `post(...)` call. Mixing it in would muddy the lead's review of the packet. Worth a follow-up. |
| **`make_embedder`'s `api_key = config.api_key`** | Vestigial alias left by the deleted `_resolve_api_key(config.api_key_env)`. Harmless, used three times, arguably still a readability aid. Left. |
| **Deleting `lorerunes/tests/test_smoke.py` as subsumed** | **Declined**, and the de-bloat bar is why: its behaviour *is* strictly subsumed by `test_the_shared_package_exists_and_owns_the_predicate`, which imports the package — but deleting it would leave `lorerunes/tests` collecting zero tests, making a `testpaths` entry that CLAUDE.md requires into a hope with a filename. Kept, and the reasoning written into the file. |
| **`scout.py` / `server.py` / `index/cli.py` / `snapshot_gc.py` / `search_score_survey.py` repeating the same 5-line username comment** | Left. It is *explanatory* text at five sites that each need it, not policy; the policy itself is already one function (`resolve_config_value`). Consolidating comments across modules is not a thing. |

---

## 6. Full-suite receipt

Baseline supplied by the lead and independently re-derived here: **2 failed / 7368 passed**, both
failures reproduced at `76f1d9f` and not caused by packet 42.

⚠ **This receipt is from a run started AFTER the final edit.** An earlier full run was killed
mid-flight precisely because it had started against an intermediate tree, and a result
describing a tree that no longer exists is not a receipt for anything.

```
FAILED loremaster/tests/test_retired_symbols.py::TestNoFileReferencesARetiredSymbol::test_no_file_references_a_retired_symbol
FAILED loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
2 failed, 7368 passed, 17 skipped, 3 xfailed, 1 warning in 217.23s (0:03:37)
```

**Same count, same two node ids as the baseline.** Two independent checks that neither is mine,
because a "36 vs 37" off-by-one is exactly the shape a newly-added import would produce and I did
add one import:

1. **Neither failure names anything I touched.** The retired-symbol offenders are three archived
   receipts under `docs/plans/v2/receipts/2026-07-24-packet11i/` and `…-2026-07-25-packet03b/`
   mentioning `_BRIEF_PUBLISH_`. None of my eight files imports `_surreal_harness`
   (checked mechanically over the changed-file list), so the 36-vs-37 importer count cannot have
   moved because of me — my one added import is of `_logging_fixtures`.
2. **Both reproduce on the clean tree.** With my changes stashed at `f582ee0`:

```
FAILED loremaster/tests/test_retired_symbols.py::TestNoFileReferencesARetiredSymbol::test_no_file_references_a_retired_symbol
FAILED loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
2 failed in 1.73s
```

Changes restored afterwards and the scoped gate re-run to confirm the round-trip was clean:
**383 passed**, typecheck 0 errors across five members, ruff clean.

⚠ Both failures are themselves instances of this repo's #1 defect class — a docstring count that
drifted from the derived count, and archived records naming a retired symbol without a
`SUPERSEDED` banner. They are outside packet 42, but they are real and currently red.

---

## 7. Naming consistency (`lorerunes` is PLURAL by operator ruling)

Bare, anchor-free sweep for a stray singular across `*.py`, `*.md`, `*.toml`, `*.sh`, `*.lock`
and the `Containerfile`, excluding `.venv` and the untracked wave reports:

```
### stray SINGULAR 'lorerune' (not followed by s):
docs/plans/v2/receipts/2026-07-26-packet42/REMOVED-BEHAVIOR-INVENTORY.md:593
```

**One hit, and it is correct** — R29 recording that the lead proposed the singular and the
operator chose the plural. Zero code, config, or prose sites use the singular. Capitalisation
variants (`Lorerune`, `LORERUNE`): none.

---

## 8. Files changed

```
 Containerfile                                   |  11 +-
 loremaster/loremaster/calibration/counting.py   |  10 +-
 loremaster/loremaster/logging_setup.py          |  20 ++--
 loremaster/loremaster/scout.py                  |   5 -
 loremaster/tests/test_logging_setup.py          | 144 ++++++++++--------------
 loremaster/tests/test_secret_resolution_seam.py |  12 ++-
 loremaster/tests/test_secret_typing.py          |  31 ++---
 lorerunes/tests/test_smoke.py                   |  25 ++++
```

Production **behaviour** changed in zero files: `counting.py` and `scout.py` are docstring/comment
only, `logging_setup.py` is a docstring plus a proven byte-identical regex literal, and
`Containerfile` is a comment. The three test files lose duplicated plumbing and stale prose; no
assertion moved. **Not committed** — the lead reviews the diff.
