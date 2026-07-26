# REPORT-pkgscout-loremaster-2

Package-vs-hand-roll sweep of the `loremaster/` surface that `REPORT-pkgscout-loremaster.md`
could not reach — the 984 LOC it never opened, `server.py`'s ~6,700 unread lines, and the
ledger modules' domain state machines.

**Everything below was measured on 2026-07-25 against worktree
`/home/ejprice/PycharmProjects/lore-pkt11i` at commit `67279be` (branch
`pkt11i-floor-calibration-dark`).** Every present-tense claim means "at that sha" —
re-derive before acting.

---

## SUMMARY BLOCK

```
brief-base v6 read
state: done-with-deviations
```

**Deviations** — (1) I delegated *line-by-line reading* to twelve read-only subagents and did
**every** library verification myself; five subagent claims were overstated or wrong and I
corrected each in place (§N1 chaining, §N6 cycle-detection, §N16 cycle-detection, §S8, §S18).
Claims I did not re-derive are labelled `[subagent-sourced]`. (2) Ephemeral overlays only
(`uv run --with`, one `podman run --rm`); no file, lockfile, image or git state mutated. This
report is my only written artefact. (3) This block exceeds 40 lines; the verdict table is most
of the overrun.

**COVERAGE — the composed statement.** Total production LOC **41,334**, derived by script over
`loremaster/loremaster/**.py` excluding `tests/`.
⚠ **My predecessor's "NOT covered (~700 LOC)" figure was itself incomplete.** Re-derived
mechanically, **984 LOC** were named by NEITHER its covered *nor* its uncovered list — it omitted
**`extension.py` (372)**, `calibration/__init__.py` (48), `index/__main__.py` (14). I assigned
all 984. **Together the two reports now account for all 41,334 LOC**, with residuals named
explicitly in §COVERAGE — no silent gap.

**Ranked verdicts** — by what a wrong choice COSTS. All are *silent*-failure hand-rolls unless
marked. `[lib-verified]` = I introspected that version myself.

| # | Symbol / cluster | Library | Verdict |
|---|---|---|---|
| **N1** | `logging_setup.RedactingFilter` — key-blind, dict-repr-blind, 24-char floor; **tracebacks discarded entirely**; third-party loggers bypass it | `detect-secrets` / `structlog` / `python-json-logger` | **REPLACE** — silent credential leak; the self-declared "last line of defence" |
| **N2** | Secrets are bare `str` end-to-end; `SecretStr` appears in **zero** files | `pydantic.SecretStr` *(installed)* | **REPLACE** — makes N1's backstop mostly unnecessary |
| **N3** | Teardown hand-rolled **5×**, 3 error policies; ~135 LOC of `build_app_context` unguarded | `contextlib.AsyncExitStack` *(stdlib)* | **REPLACE** — leaks ~10 sockets **×5 retries** on one unset env var |
| **N4** | `_validate_comms_charset` uses `re.match` on a `$`-anchored pattern | `re.fullmatch` *(stdlib)* | **REPLACE** — **proven**: `"scout\n"` passes and mints a *distinct* identity |
| **N5** | `AppContext._path_similarity` / `._nearest_indexed_paths` | `difflib` *(stdlib)* / `rapidfuzz` | **REPLACE-WITH-ADAPTER** — **measured 0/4 vs 4/4.** REVERSES predecessor's T3.2 KEEP |
| **N6** | `calibration.baseline.validate_baseline` has **zero production callers**; the generation anchor is never enforced | `pydantic` *(installed)* | **REPLACE** — the drift detector's anchor is prose, not a mechanism |
| **N7** | `source.local_directory.acquire` — `copytree(dirs_exist_ok=True)` is a **merge, not a mirror**; symlinks make re-acquire raise | `shutil.rmtree`+copy / `rsync` | **REPLACE-WITH-ADAPTER** — deleted files live forever in the snapshot |
| **N8** | `schema_rebuild_status` blob: 5 hand-rolled sites, 3 constants **+ a bare literal**, malformed → silently "not rebuilding" | `pydantic` *(installed)* | **REPLACE** — silently disables the rebuild notice |
| **N9** | Extension dispatch: typo'd seam = permanent silent no-op; duplicate `.name` clobbers config | `pluggy` 1.6.0 *(in the image)* | **REPLACE-WITH-ADAPTER** — LIFO-order caveat |
| **N10** | `scout.CommandSubscriber._rows` — any non-list SDK result → `[]` | `pydantic.TypeAdapter` | **REPLACE** — command channel dies silently, looks healthy |
| **N11** | `memory/backend.derive_refs_stamp` — unescaped `@`/`,`/`:` feed `uuid5` | `json.dumps(sort_keys=)` *(stdlib)* | **REPLACE** — id collision silently overwrites a memory |
| **N12** | 4 unjittered backoffs — **now with a measured kill**: `2**attempt` → `OverflowError` at ~10.7 d, status still `cached_retrying` | `tenacity` 9.1.4 *(in the image)* | **REPLACE-WITH-ADAPTER** — extends predecessor's P5 with a receipt |
| **N13** | `_apply_config_chunker_overrides` — dotless `chunkers:` key silently never fires | `pydantic` *(installed)* | **REPLACE** — live operator-facing bug, proven |
| **N14** | `_child_context` re-lists fields + republishes a copied dict | `pydantic.model_copy` *(installed)* | **REPLACE** — one line |
| **N15** | Batch validation cloned 2×; `configure_logging` silently downgrades a bad level to INFO | `TypeAdapter` · `pydantic-settings` *(declared, **unused**)* | **REPLACE** — also answers predecessor's open P10.1 |
| **N16** | `tasks`/`agents` state machines: agent CAS **unguarded**; `blocked_by` ids never validated | in-house shared CAS + `graphlib` | **FORK → operator** — two undecided policy questions |
| **N17** | The served tool surface: `lore_impact` teaches a knob **that exists nowhere**; the Origin guard's configurable branch is unreachable | *(prose derived from behaviour)* | **REPLACE** — both **proven by grep**; the #104 class, live |
| **K1** | `snapshot.SnapshotLayout._safe_path` · `agent_ref.py` · `findings` state machine · fence emission · `_no_tokenizer` · `main`'s argparse | — | **GENUINELY BESPOKE / KEEP** — I tried to break them and could not |

**Decisions needed (operator)** — (1) **N16a**: is a task claim a *lock* or a *hint*? `transition`
and `supersede_task` never compare `actor` to `owner`, so any agent can close any other's claimed
task. (2) **N16b**: does supersession transfer `blocked_by`? Today it silently drops them **and**
permanently deadlocks dependents. (3) **§S2**: should `lore_read` honour the tier `exclude`
policy? It applies containment only, so any file inside a live root — `.env`, `.git/config` — is
readable by any agent that names it. (4) **§S12**: `messages.py` is committed but **not wired
into `server.py`**, while `test_comms_tool.py` calls `action="send"` — is this a red 03b contract,
or is this tree behind master?

**Tool honesty.** lore's index watches the MAIN checkout, **not this worktree (#125)** — so every
structural fact came from grep/Read and I called no `lore_*` structure tool. The documented #125
fallback, said out loud. No friction row: #125 is already ledgered.

**Receipts** — §N1/N2 (hole enumeration) · §N3 (measured `AsyncExitStack` semantics **+ a
correction**) · §N4 (regex probe with a discriminating control + provenance) · §N5 (0/4 vs 4/4 on
the real 56-path corpus, both-ways control) · §N8 (the 3-constants-plus-bare-literal grep) · §N9
(pluggy `check_pending`) · §N12 (`OverflowError`) · §N13 (live registry probe, loud/silent
control) · §N17 (the one-hit grep + the sole-call-site grep) · §COVERAGE (regenerating command).

**If only three things are done:** §N2 (`SecretStr` — removes the reliance on a leaky redactor
rather than patching it) · §N6 (`load_baseline` returns a validated model — the drift anchor is
currently prose) · §N3 (`AsyncExitStack` — the ~50-socket leak on one unset env var).

---

## COVERAGE — the composed long form

```bash
find loremaster/loremaster -name '*.py' -not -path '*/tests/*' | xargs wc -l | tail -1
```

**Read line-by-line in this sweep** (by me, or by a subagent whose claims I spot-verified wherever
one changed a verdict):

* **`server.py` 1–8,633** — eight readers, contiguous, **no gaps**. This closes the predecessor's
  largest partial (it read ~1,900 line-by-line and grep-swept the rest by category). The final
  span (6,700–8,633: `_register_tools`' ~1,300 lines of served tool descriptions,
  `_register_extension_tools`, `build_asgi_app`, `main`) is where §N17's served-surface defects
  came from — the region a category sweep is *least* able to see, because its defects are English.
* **`tasks.py` (1,546)** and **`agents.py` (975)** in full — the state machines the predecessor
  deliberately skipped.
* **`findings.py` (1,273)**, **`briefs.py` (1,273)**, **`messages.py` (1,155)** in full — same.
* The never-covered 984: `source/local_directory.py`, `source/snapshot.py`, `source/__init__.py`,
  `agent_ref.py`, `calibration/baseline.py` (+ `baseline.json`), `calibration/__init__.py`,
  `index/__main__.py`, **`extension.py`**.
* **`logging_setup.py`** in full (predecessor read only its head); **`memory/backend.py`** in full
  (predecessor *inferred* 200–422 from a symbol listing); **`scout.py`** in full minus the settled
  retry seam.
* By me directly: `index/paths.py` (full), `index/watcher.py`'s overflow-task retention, the
  sanitiser-seam import map, the whole sleep/backoff population, the declared-vs-imported
  dependency inventory, and every library probe below.

**Cleared — recorded so nobody re-spends the tokens.** `index/paths.py` is *not* a hand-roll
(stdlib `PurePosixPath.full_match` + `os.walk` with an in-place prune; `pathspec` would only apply
under gitignore semantics, and the config uses explicit globs). `LiveWatcher._launch_overflow_reconcile`
retains its task in `_overflow_tasks` with a `discard` done-callback — the textbook pattern, **not**
the fire-and-forget hazard its call site resembles. `findings.chain_head` cannot hang (`visited` +
`_MAX_CHAIN_HOPS`). `findings.report`'s number mint really is gapless (counter bump and CREATE in one
transaction). There is **no tar/zip extraction anywhere in `source/`**, so the classic archive-escape
class does not exist here.

**Residual gaps neither report has closed:** `shellout.py` (566) — the predecessor read its *threat
model*; nobody has audited its AST gate **as code**, and it is the instrument guarding #131 ·
`store/surreal_schema.py` + `store/surreal.py` were ruled GENUINELY BESPOKE, but the predecessor's own
note that `compose`/`_assert_envelope_integrity` "deserve their own adversarial review" (a
statement-smuggling guard resting on regex-scanning for `;`/`BEGIN`/`COMMIT`) still stands ·
`lorescribe/`, `loresigil/`, `scripts/` are #201's.

---

## N1–N2 — the logging layer leaks credentials and discards every traceback

**Symbols:** `logging_setup.RedactingFilter`, `._scrub_text`, `._scrub_value`, `_TOKEN_RE`,
`_shannon_entropy_bits`, `JsonFormatter.format`, `KeyValueFormatter.format`, `_LOGRECORD_RESERVED`.

This module's own docstring calls it the *"CRITICAL secret backstop"* and *"last line of defence."*
`[subagent-sourced, source-verified by its reader; I did not re-run the regexes]` It is a two-regex
blocklist plus a Shannon-entropy heuristic, with at least five holes that each fail **completely
silently** — the line emits, looks redacted-by-policy, and carries the secret:

1. **Key-blindness.** `_scrub_value` inspects only *values*, never keys. `extra={"password":
   "hunter2"}` → `JsonFormatter` emits `"password": "hunter2"` verbatim. Every mature redactor
   (Django `SENSITIVE_VARIABLES`, structlog processors) is key-aware *first*.
2. **Dict/JSON reprs escape the assignment regex** — it requires the separator to follow the label
   immediately, so `{'password': 'hunter2'}` does not match. That is precisely the shape of
   `scout._open_command_connection`'s credentials dict in an SDK error.
3. **A 24-char floor** misses a typical 16–20-char `SURREAL_PASS` with no adjacent label.
4. **The charset excludes `/`**, which standard base64 includes — a real secret fragments into
   sub-24 pieces and *partially* leaks.
5. **`exc_info`/`exc_text`/`stack_info` are in `_LOGRECORD_RESERVED`**, so the filter skips them.

**And the tracebacks are gone entirely.** Both formatters override `format()` and never touch
`exc_info`. Every `logger.exception(...)` and 15+ `exc_info=True` sites across `scout.py`,
`index/watcher.py`, `index/indexer.py`, `calibration/engine.py`, `server.py` emit an **event name
with no cause**. No test pins this (the only `exc_info` reference passes `None`).

**Worse, the filter is only attached to `loremaster`/`loresigil`/`lorescribe` handlers.** Every
third-party logger bypasses it — including `websockets`/`surrealdb`, whose DEBUG frame dumps carry
the **plaintext SurrealDB signin frame**. Anyone running a debug root level leaks it, and the "last
line of defence" is not on that path.

**Verdict N1: REPLACE.** `detect-secrets` (maintained named-shape plugins *plus* a maintained
entropy detector) or `structlog` processors; `python-json-logger` renders `exc_info` by default and
owns `RESERVED_ATTRS` (which is currently a hand-transcribed copy that already had to absorb
CPython 3.12's `taskName`). The key-aware denylist is the piece this hand-roll structurally cannot
grow into.

**Verdict N2: REPLACE — and do this one first.** `config.resolve_secret() -> str` returns a bare
string that `Scout.from_config` threads through **five** constructors plus a captured closure.
`SecretStr` appears in **zero** `.py` files repo-wide. Adopting it turns "a password can never
appear in a repr" from a hope that N1 must catch into a property of the type — which is strictly
better than improving the redactor, because it removes the reliance instead of patching it.
**The control:** a test asserting `repr()` and `json.dumps(default=str)` of a populated config
contain no secret material, plus a positive control that the value is still readable via
`.get_secret_value()`.

**Adjacent, same module `[source-verified by me]`:** `configure_logging` resolves
`getLevelNamesMapping().get(level.upper(), logging.INFO)` — `LORE_LOG_LEVEL=DEBGU`, a trailing
space, or an empty value **silently becomes INFO**, biting exactly when an operator is cranking
verbosity to chase a production issue. `LoggingConfig.level` is a bare `str` while its two
siblings are `Literal`s, and `destination`'s own docstring says *"modelled as a `Literal` so a typo
fails loud."* **This is also the answer to the predecessor's open P10.1**: `pydantic-settings` is
declared, installed, shipped, and imported **nowhere** — a `BaseSettings` field typed
`Literal[...]` with `env="LORE_LOG_LEVEL"` fixes both paths from one declaration and gives the
dependency a reason to exist. `KeyValueFormatter` additionally does `f"{key}={value}"` with no
escaping, so a value containing a newline **forges a complete extra log line** — the row-forgery
class this repo already has law about, in the one formatter where JSON's escaping does not save it.

---

## N3 — teardown is hand-rolled five times with three error policies, and 135 lines are unguarded

**Symbols:** `build_app_context`'s `write_stack_readied` unwind · its second `except BaseException`
· `AppContext.aclose` · `LoreServer.run_startup_hooks`/`.run_shutdown_hooks` · a fifth copy in
`scout.Scout.start` (per its own comment).

| site | ordering | per-close error policy |
|---|---|---|
| `write_stack_readied` | tracked list, `reversed()` | `contextlib.suppress(Exception)` |
| the second `except BaseException` | hand-typed literal order | **none** — first raiser aborts the other nine |
| `AppContext.aclose` | hand-typed order (**different again**) | **none** |

**The cost.** `build_app_context`'s first `try` closes ~135 lines before the second opens.
Everything built in that window runs with **all ten SurrealDB backends live and nothing to close
them** — and two verified raisers sit inside it (`resolve_secret(...ANTHROPIC...)` raises `KeyError`
on an unset var; `CalibrationEngine.__init__` does packaged-file I/O). Because
`_acquire_eager_lease_with_retry` retries the whole build **5 times**, a deployment that simply
never set `ANTHROPIC_API_KEY` leaks five full write stacks (~50 WebSockets) before failing.

**Measured** `[library-verified, CPython 3.14.6]`:
```
callbacks that RAN (reverse order): [3, 2, 1]   <-- 1 still ran despite 2 raising
CONTROL, the current hand-rolled unwind, errors visible: []      <-- zero diagnostics
CONTROL 2, CancelledError swallowed by 'except BaseException': True
```
**A correction I owe you.** My subagent claimed — and I first repeated — that `AsyncExitStack`
*chains* failures into `__context__`. **It does not.** With two failing callbacks I measured
`__context__ is None` and `__cause__ is None`: it runs every callback but surfaces only the
last-raised. So the honest claim is **"runs all ten closes"** (vs. aborting after the first) and
**"surfaces one failure"** (vs. `suppress(Exception)` surfacing zero). If preserving *all* teardown
failures matters, the adapter must build an `ExceptionGroup` itself.

**The second silent hole.** `run_startup_hooks`'s unwind is `except BaseException: pass`, and I
measured that this **swallows `asyncio.CancelledError`** — so a shutdown arriving mid-boot
degenerates the whole unwind into a no-op, leaving every started extension half-started with no
exception, no log, and no failing test.

**Verdict: REPLACE.** One `AsyncExitStack` spanning `build_app_context`, `pop_all()` on success,
handed to `AppContext` so `aclose()` is `await self._stack.aclose()`.
**The control:** inject a failure at `CalibrationEngine.__init__` and assert **zero** open SurrealDB
connections afterward — run against the current tree first, where it must FAIL.

---

## N4 — the injection charset guard admits a trailing newline. Proven.

**Symbol:** `AppContext._validate_comms_charset` (guarding agent names, sessions **and** brief names).

Its docstring: *"names are inlined into store queries and must stay in the safe charset."* The
implementation is `AGENT_NAME_PATTERN.match(value)` against `^[a-z0-9][a-z0-9_-]{0,63}$`. Python's
`$` **also matches immediately before a trailing newline**. Measured
`[library-verified, CPython 3.14.6; provenance receipt: `loremaster.__file__` =
`…/lore-pkt11i/loremaster/loremaster/__init__.py`]`:

```
'scout'          match=PASS    fullmatch=PASS
'scout\n'        match=PASS    fullmatch=reject     <-- the bypass
'scout\nrogue'   match=reject  fullmatch=reject     <-- CONTROL: probe discriminates
'Scout'          match=reject  fullmatch=reject     <-- CONTROL

id('scout')   = 025da630-911a-55e8-91a2-13b9a7888ad0
id('scout\n') = 18711948-3809-599d-96ae-0aebc815076b     distinct identities: True
```

The control matters: `$` matches only before a *trailing* newline, so an embedded newline is
correctly rejected — the guard is not simply broken, it has exactly one hole, and that hole is the
one that produces a **second, distinct agent identity** for a visually identical name.

**Why the existing pin cannot see it:** `test_agent_registry.py::TestAgentNamePatternConstant`
asserts with **`fullmatch`**, while production uses **`match`**. The test and the code disagree
about which function is under test — a fixture that structurally cannot fail on this defect.

**Verdict: REPLACE** — `.fullmatch()` (or `\Z`). One character of real change.
**The control:** re-point the existing pin at the *production* call path, not at the constant.
⚠ **Related, unverified and worth your eye:** the store's independent ASSERT uses SurrealDB's Rust
`regex` engine, whose `$` I believe has *no* trailing-newline exemption — meaning the two
"defense-in-depth" layers currently disagree about the charset. **I did not measure the Rust half;
it needs a probe before anyone relies on either.**

---

## N5 — `_path_similarity` scores 0/4 where stdlib `difflib` scores 4/4. This REVERSES a prior KEEP.

The predecessor ruled this **KEEP** (T3.2) and named the gap precisely: *"I did not empirically
compare outputs on a real path corpus — that comparison is the experiment that would overturn
this."* **I ran it**, against the real 56-path corpus of this package
`[library-verified, rapidfuzz 3.14.5 / difflib stdlib CPython 3.14.6]`:

```
typo: loremaster/loremaster/servr.py       MEANT: .../server.py
  lore      : ['__init__.py', 'agent_ref.py', 'agents.py']   *** MISS ***
  difflib   : ['server.py', 'search.py', 'render.py']        HIT
SCORE over 4 one-char typos -> lore 0/4 | difflib 4/4 | rapidfuzz 4/4
```

**Why, structurally.** The metric is `max(common leading segments, common trailing segments)` —
segment-granular, **zero character sensitivity**. `servr.py` and `server.py` share two leading
directories → score 2; so does every sibling. The tie-break is **alphabetical**, so the agent gets
`agent_ref.py, agents.py, auth.py`. **The file it meant can never be preferred.** The predecessor
was right about the metric and wrong about the use case: this exists to answer *"did you mean X?"*,
and a typo is the dominant reason a path misses.

**The control — why ADAPTER, not a clean REPLACE:**
```
query: totally/different/tree/server.py
  lore: ['loremaster/loremaster/server.py']    difflib: []    rapidfuzz: [server.py, ...]
```
`difflib` returns **nothing** on the right-basename-wrong-tree case. The metrics are complementary,
not ordered; a naive swap trades one blind spot for another.

**Verdict: REPLACE-WITH-ADAPTER** — score by `max(segment_score, fuzzy_score)`; keep the segment
metric, add `difflib.SequenceMatcher` (or `rapidfuzz`, ~20× faster, installed-free). Also swap the
full `sorted()` over every manifest row for `heapq.nlargest`.
**Failure mode today: SILENT** — three authoritative-looking wrong files. A `[FILTER MISS]` naming
three wrong paths is worse than one naming none.
**The control:** the table above, pinned — four typo rows **plus** the wrong-directory row, so it
discriminates in both directions.

---

## N6 — the calibration drift anchor is prose: `validate_baseline` has ZERO production callers

**Symbols:** `calibration.baseline.validate_baseline`, `.load_baseline`, `CalibrationEngine.__init__`.

`[source-verified by its reader, grep-confirmed repo-wide]` `CalibrationEngine.__init__` calls
**`load_baseline()`**, which checks exactly one thing: `isinstance(data, dict)`.
**`validate_baseline` — ~60 lines of hand-rolled schema checking — is called only by the generator
script and by tests.** Consequences, all silent:

* A baseline with `schema_version: 2` is consumed by a v1 engine with no complaint.
* A `claude_total` that disagrees with its own files is consumed as gospel — and the drift detector
  computes `live/baseline` against it, **silently rescaling the served token budget**.
* **The "generation anchor" is never enforced at runtime.** `CalibrationEngine._model` comes from
  the operator-settable `config.anthropic.yardstick_model` and **is never compared to
  `baseline["model"]`**. Boot with a different yardstick and any tokenizer-generation difference is
  reported as *drift* and adopted, with a note naming the **symptom** and never the cause. The
  whole generation-anchored premise has **no mechanical guard** — it is a docstring.
* `sha256` is validated as "a str of length 64" only (`"z"*64` passes); `generated_at` is never
  parsed and is served verbatim into `index_status`.

**The mitigation and its limit.** `test_calibration_baseline.py` *does* pin the committed artifact,
and the reader independently re-derived both totals and all nine sha256s — **they match**
(`claude_total = 26187`, `voyage_total = 16681`). So code and data agree *today*. But per this
repo's own "TEST ENVIRONMENT IS A FICTION" law that proves the **recipe**: it asserts nothing about
whether `resources.files(...)` resolved to the checkout or to site-packages, and cannot see a
baseline swapped at deploy time or a `yardstick_model` override in a live `lore.yaml`.

**Verdict: REPLACE.** Make `load_baseline()` **return a validated pydantic model** — then the
validator cannot be left un-called, because the typed object is the only way to get the data. Add
one assertion at engine construction: `baseline.model == self._model`. `_is_plain_int` is literally
`pydantic.StrictInt`; the cross-sum is a `@model_validator(mode="after")`.
**This is the highest-leverage single fix in the sweep** — it also collapses §S9's four-way
duplication of `"claude-sonnet-5"`.

---

## N7 — the snapshot provider MERGES where it claims to MIRROR

**Symbol:** `source.local_directory.LocalDirectorySourceProvider.acquire`.

Eleven lines: an existence check, then
`shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)`.

**`dirs_exist_ok=True` never deletes.** A file removed from or renamed in the source tier stays in
the snapshot **forever**, and because the indexer purges the tier's store rows and re-walks, the
stale file is **re-indexed as live content on every rebuild**. The docstring says re-acquiring
overwrites the subtree *"with the current source contents."* False. No error, no log, no test.
**Why no test catches it:** `test_acquire_is_idempotent` re-acquires a source where a file was
*modified* and one was *added* — it never deletes one. A fixture that cannot discriminate.

**Second, worse, and loud:** verified against CPython's `shutil._copytree`, with `symlinks=True` the
copy does `os.symlink(...)` with **no unlink of an existing destination** — so **the second
`acquire()` of any tier containing a symlink raises `FileExistsError`**. `symlinks=True` (correct,
CWE-59) and `dirs_exist_ok=True` (idempotency) are **mutually incompatible**, and the two tests
cover the corners either side of the intersection: one acquires *once* with symlinks, the other
acquires *twice* without them. The production case — a vendored `site-packages` or `node_modules`
static tier — is exactly the uncovered corner.

**Verdict: REPLACE-WITH-ADAPTER.** `shutil.copytree` genuinely **cannot** mirror — so this is rule
side 2, a correct hand-roll of the missing piece: `rmtree`-then-copy (two stdlib lines), or `rsync
-a --delete` if permissions/specials matter. `copytree` also aborts a whole tier on a FIFO/socket
(`SpecialFileError`) or an unreadable file, and its `ignore=`/`ignore_dangling_symlinks` params are
unused.
**The control:** the two missing fixtures — acquire, **delete a source file**, re-acquire, assert
it is gone from the snapshot; and acquire **twice** over a source containing a symlink.

**Cleared, and worth recording as the rule working correctly:** `SnapshotLayout._safe_path` is
**GENUINELY BESPOKE and correct**. Its three-stage guard deliberately normalises the base without
resolving it (a real requirement — the live root is itself a directory symlink) and no library
exposes that knob: `werkzeug.utils.safe_join` and `os.path.commonpath` do the lexical half only and
would miss the escaping-intermediate-symlink case stage 3 exists for. The reader tried to break it
and could not. **KEEP.** (Two notes, neither an escape: the `except OSError` arm is effectively
dead on 3.14 because `resolve(strict=False)` does not raise on a symlink loop — a wrong comment,
not a hole; and `rel_path=""` resolves to the base *directory*, latent only because the sole caller
guards with `is_file()`.)

---

## N8–N16 — the rest, compressed

**N8 — the `schema_rebuild_status` blob.** Five hand-rolled producer/consumer sites, no pydantic
model, on a boundary that round-trips through the database. `[source-verified by me]` The literal
`"in_progress"` exists as **three private constants** (`index/schema.py`, `index/indexer.py`,
`server.py`), each commented as "one literal across the producer and the consumers" — **plus a bare
literal**: `_maybe_spawn_schema_rebuild` writes `"state": "in_progress"` inline while the sibling
key *in the same dict* correctly uses `_REBUILD_REASON_FINGERPRINT_MISMATCH`, and the constant it
should have used sits ~880 lines above **in the same file**. (I am deliberate here: the two
`task`-status copies in `tasks.py`/`surreal_schema.py` are a **different population** and are *not*
part of this count.) `rebuilding_notice` catches `(ValueError, TypeError)` → `return None` = "no
rebuild in progress", **with no log** — so any drift silently stops the notice firing and every read
tool serves a **silently empty result** mid-rebuild. And since `SchemaRebuildStatus` is
`extra="forbid"`, **the day any writer adds a seventh key, `lore_index` silently reports `idle`
during a live rebuild.** The resilience seam for exactly this (`CalibrationStatus.from_engine_status`)
exists in the same file and was applied to the *in-process* seam but not the *persisted* one.
**REPLACE** with one model + a loud `logger.warning`.

**N9 — the extension seam.** `Extension` is an ABC where every seam ships an inert default, so
`def format_results(...)` (plural) registers **cleanly** and is never called — no error, no log, no
import failure. `register_extension` has **no duplicate-`.name` guard** (the second extension's
config silently clobbers the first's; they share one "private" state namespace), and a typo'd key in
the `extensions:` config block is never reported. Measured `[library-verified, pluggy 1.6.0]`:
```
firstresult (first non-None)       : B-WINS
duplicate NAME refused             : ValueError Plugin name already registered
typo'd seam CAUGHT by check_pending: PluginValidationError unknown hook 'format_results'
```
pluggy is **already in the image**. `check_pending()` is the prize — it converts the typo'd-seam
class from a permanent silent no-op into a startup error. **Genuine gap → ADAPTER:** I measured
pluggy's multi-hook order as **LIFO** (`['B','A']`) where lore concatenates in **registration**
order, so `tool_specs`/`payload_indexes`/`source_providers` reverse unless `trylast` is applied.
(The ABC-not-entry-points choice is deliberate per D2 and pluggy does not disturb it.)

**N10 — `scout.CommandSubscriber._rows`.** `if isinstance(result, list): return [row for row in
result if isinstance(row, dict)]; return []`. If the `surrealdb` SDK ever returns an envelope or a
typed object, `_drain_pending` iterates nothing: **the command channel processes zero commands
forever, with no error and no log line**, while the subscriber looks perfectly healthy. Non-dict
elements are silently dropped. **REPLACE** with `pydantic.TypeAdapter[list[CommandRow]]` — a wire
boundary, where a `ValidationError` is exactly the loud outcome you want.

**N11 — `memory/backend.derive_refs_stamp` / `derive_memory_id`.** Three delimiters (`@`, `,`, `:`)
concatenated with **no escaping or length-prefixing**, fed to `uuid5` to mint a memory's primary
key. `[MemoryRef("a",1), MemoryRef("b",2)]` and `[MemoryRef("a@1,b",2)]` produce the same stamp →
same id → **the second memory silently overwrites the first**. Same class one level up: `text="a"`
+ stamp `"b:c"` collides with `text="a:b"` + stamp `"c"`, and `text` is free-form operator prose
that routinely contains `:`. Also: the docstring says "the same **set** of refs … dedups to one id",
but the input is a `list` and `sorted()` does not dedup. **REPLACE** the encoding with
`json.dumps(sorted(...), sort_keys=True)` — unambiguous by construction. The deterministic-id
*policy* is genuine domain design; the *encoding* underneath is the re-derivation, and it is the
part that is wrong.

**N12 — the four unjittered backoffs.** I re-derived the whole `asyncio.sleep|time.sleep`
population independently: the predecessor's P5 table is **correct and complete** (no additions;
`tenacity` 9.1.4 is in the image and used **nowhere**). What I add is the missing cost receipt —
`CalibrationEngine._probe_loop` computes `min(start * (2**attempt), cap)` with `attempt`
incrementing forever, and `[library-verified, CPython 3.14.6]` `30.0 * 2**1024` → `OverflowError`.
That is caught by the loop's blanket handler, logged once, and **returns** — after ~1024 × 15 min ≈
**10.7 days** of outage — while the served state remains **`cached_retrying`**, a status that now
actively lies. **REPLACE-WITH-ADAPTER** exactly as the predecessor framed it: *one* lore-owned
policy module, not four sites each building their own `wait_exponential_jitter` from their own
literals. **Do NOT fold in `_txn.retry_on_conflict`.**

**N13 — the dotless `chunkers:` key.** `_normalise_extension` only `.lower()`s — it never prepends a
dot — while dispatch looks up `PurePosixPath(path).suffix`, which always carries one. Proven live
against the real registry `[source-verified + probed]`:
```
chunkers: {'.py': {chunker: text}}  -> ['CHUNKED-BY-text']
chunkers: {'py':  {chunker: text}}  -> ['CHUNKED-BY-python']  <-- SILENTLY IGNORED
CONTROL (bad TARGET name) -> LOUD KeyError     CONTROL (bad KEY shape) -> silent   <-- the asymmetry
```
An operator writing the dotless form — how most tools accept it — gets a config that validates,
applies, and **never fires for a single file**. **REPLACE** with a pattern-constrained pydantic key.
Related, same method: the declared-overlap error advises *"use a config override to re-route"*, but
overrides are applied **once in `__init__` before any extension registers**, so an extension
chunker's key can **never** be a valid override target — teaching prose contradicting behaviour, on
a served error surface.

**N14 — `_child_context`.** Measured `[library-verified, pydantic 2.13.4]`: the hand-listed
re-construction silently reverts a parent's non-default value to the default
(`OPERATOR_SET_VALUE` → `THE_DEFAULT`) and does **not** preserve dict identity;
`model_copy(update=...)` does both correctly. A control confirms only **defaulted** fields are the
silent case (a field with no default raises `ValidationError`) — i.e. the convenient case is the
dangerous one, and `extra="forbid"` cannot see an omission. Identity churn is live: this is reached
on **every tool invocation**, so state written through a captured reference lands in an orphaned
dict. **REPLACE**, one line.

**N15 — batch validation + logging config.** `_create_many` and `_resolve_or_acknowledge_many` both
hand-roll `Model(**raw)` in a loop: a non-mapping item raises `TypeError` (**not** caught, escaping
the curated error vocabulary), only the first error per item is reported, and validation stops at
the first bad *item*. `pydantic.TypeAdapter(list[Model])` fixes all three and collapses the copies.
Logging config: see N1's tail.

**N16 — the two ledger state machines. FORK → operator.** `tasks.py` transitions correctly (a
guarded CAS binding `WHERE status = $tr_expected_from`, with `THROW` on a zero-row match).
**`agents.py` has none of it**: `touch` validates in Python against a *stale read*, then issues
`UPDATE … SET status=…` **with no `WHERE` clause**, so `retired → active` — an edge deliberately
absent from the matrix — commits silently under a concurrent retire. `register` has the same shape
on the write-once `spawned_by`. `[subagent-sourced; I did not re-derive the SurrealQL fragments.]`
Three more silent holes: `blocked_by` ids are never validated to exist, so one typo yields a task
that is `open`, renders as ordinary work, and is **unclaimable forever**; `query_tasks(status=…)`
never consults `TASK_STATUSES`, so `status="in-progress"` renders *"no tasks matched"*; and
`AgentRegistry.roster` **silently drops** rows outside the four-value domain from a count its
docstring calls *"a TRUE per-status aggregate over the WHOLE scope."*
⚠ **Correction to my subagent:** it reported "there is no cycle detection." That is true of the
*ledger*, but `server.AppContext._find_key_cycle` **does** detect cycles among `create_many`'s
sibling keys — the real gap is narrower: cycles through *pre-existing* ids.
`graphlib.TopologicalSorter` (already proposed for `_find_key_cycle`) owns both halves.
**Why it is a fork:** two questions are undecided policy, not hand-rolls. **(a) Is a claim a lock or
a hint?** `claim_task` is a genuine mutual-exclusion CAS, and then `transition`/`supersede_task`
**never compare `actor` to `owner`** — any agent can drive any other's claimed task to `done`.
**(b) Does supersession transfer `blocked_by`?** Today the successor is built with
`blocked_by=None` (silently, undocumented) **and** the old row keeps its status, so it can never
reach a terminal state and **everything blocked by it is permanently unclaimable**.
**My recommendation:** extract ONE shared guarded-UPDATE helper both ledgers call, and **prove
sharing by mutation** — change the shared guard, and *both* ledgers' pins must go RED. A library
(`transitions`, `python-statemachine`) can own the edge *table* but **cannot own the CAS**, which is
the broken half — so this stays a hand-roll, correctly.

**The low-cost tail (REPLACE, individually below the churn threshold):** `_result_identity`'s bare
`[:60]` with no ellipsis → `textwrap.shorten` · `_TASK_ID_SHAPE_PATTERN` re-deriving the
`uuid4().hex` mint (and asymmetric with it) → `uuid.UUID(hex=…)` · `roster`'s manual tallying →
`collections.Counter` · `messages._dedupe_by_identity`'s 7-line hand-roll where `dict.fromkeys` is
used for the same job 15 lines above · the `_TASK_ACTION_*` / `_FINDING_ACTION_*` / `_COMMS_ACTION_*`
/ `CalibrationStatus.state` string tables → `enum.StrEnum` or `Literal` (the `state: str` ones are
load-bearing — valid values are enumerated **only in a docstring**, so a renamed engine state
round-trips and renders verbatim).

---

## N17 — the served tool surface teaches a parameter that does not exist, and a security branch nothing can reach

This is the region a category sweep is structurally blindest to: ~1,300 lines whose defects are
**English read by an LLM as the contract**. Two are proven by my own grep.

**N17a — `lore_impact` renders a remedy naming a knob that exists NOWHERE.** `[source-verified by
me]` `impact.py::_COVERING_TESTS_ELISION_TEMPLATE` is
`"+{count} more (elided by max_covering_tests={cap})"`, and:

```
$ grep -rn "max_covering_tests" --include='*.py' --include='*.md' .
loremaster/loremaster/impact.py:153:_COVERING_TESTS_ELISION_TEMPLATE = "+{count} more (elided by max_covering_tests={cap})"
```

**One hit in the entire repository — the string itself.** It is not a parameter of anything; the
cap is the bare module constant `_MAX_RENDERED_COVERING_TESTS = 15`. An agent reads *"elided by
max_covering_tests=15"*, calls `lore_impact(target=…, max_covering_tests=50)`, and gets a schema
rejection for a parameter that was never real. This is the **fabricated-value class verbatim** —
the same shape as the fabricated version number this repo's CLAUDE.md records among its ten §C1
defects.
Its sibling is subtler and arguably worse: `_ELISION_TEMPLATE` names `max_consumers`, which **is**
a real parameter of `ImpactEngine.impact` — but is **not exposed on the MCP tool** (which accepts
only `target` and `depth`). So the count is honest and the elision is **un-liftable by any MCP
caller**. A render that names a remedy the consumer cannot use is an over-claim under the trust
doctrine; a render that names one that does not exist is a lie.
**Verdict: REPLACE** — derive the notice from the typed cap that produced it, per this repo's
"prose must be DERIVED from behaviour" law, and either expose the knob or say the cap is fixed.

**N17b — the Origin guard's configurable branch is reachable only from a test.** `[source-verified
by me]` `OriginValidationMiddleware.__init__(self, app, allowed_origins=None)` sets
`self._allowed_origins = frozenset(allowed_origins or ())`. Production has exactly one call site:

```
loremaster/loremaster/server.py:8563:    app = OriginValidationMiddleware(app)          <-- no allowed_origins
loremaster/tests/test_auth.py:383:  app = OriginValidationMiddleware(inner, allowed_origins=[...])  <-- the ONLY one
```

So `_allowed_origins` is **permanently empty in every deployment**, and the middleware's documented
policy bullet — *"Configured extra Origin → ALLOWED. An explicitly trusted origin (a web UI host)
the operator adds"* — describes a branch **no `lore.yaml` key can reach**. Worse, `build_asgi_app`'s
own `Args:` docstring says *"config: … `server.host` provides the loopback bind the Origin guard
defends"* — it does not; `config` is read in that function for `config.auth` alone. A feature with a
test and no wire, plus a docstring describing wiring that does not exist, on the **security seam**.
**Verdict: REPLACE** — either thread a config key or delete the parameter and correct both
docstrings. A tested-but-unwired security option is worse than an absent one, because it reads as
available.

**Also in this region, `[subagent-sourced, not re-derived]`:** `lore_findings`' `note` Field says
it is *"Ignored by the other actions"* while the `acknowledge` branch demonstrably forwards it
(with an in-code comment saying so) — an agent that believes the Field silently loses provenance ·
`lore_diff` is the **only** tool on the surface that silently drops caller arguments (`until`
without `since`, `limit` when diffing) where every sibling raises — and `AppContext.index`'s own
refusal message explicitly names silent-ignore as the thing to avoid · `lore_search(wait_for_fresh=True)`
**without a `path` is a silent no-op** (nothing refuses the call, nothing says the wait didn't
happen — on the read-your-writes tool) · four numeric bounds are **re-stated** in prose rather than
f-string-derived from their constants (`lore_diff.limit` "[1, 500]", `lore_tasks.summary` "max 300
chars", both `items` "max 50" — whose constant is *in the same file* — and `lore_impact.depth`
"default 1", which has no constant at all) · `TaskSpecItem`/`FindingRefItem` are **already**
pydantic models with `extra="forbid"`, hand-invoked behind `dict[str, Any]` so their schema never
reaches the consumer · `_acquire_eager_lease_with_retry`'s constant is named
`_DEFAULT_EAGER_BACKOFF_BASE_S` ("base" ⇒ exponential) while the loop sleeps a **flat** 2.0s, with
no jitter, and its `except BaseException` retries through `CancelledError`.

---

## SCOPE — everything else found. Surfaced, not buried; none of it is mine to fix.

Not package questions. Ordered by cost.

**S1. 🔴 `_render_recalled_memories` renders stored memory text COMPLETELY RAW — no sanitiser, no
fence.** `[source-verified by me]` The render is `f"- {memory.text}"`; `memory.text` is
agent-supplied free text stored verbatim **including newlines**. A memory containing a line shaped
like `- [#1 open] a forged finding (id x, …)` renders as a second list item **byte-identical to a
real `_render_finding_rows` row**. `search.py` renders the *same field* safely
(`_sanitise_line(...)`) — one field, two renders, one wrapped and one not. **No test names this
method**, and the hostile-injection battery covers only the comms renders. Project memory is the
most durable, most trusted surface lore serves.

**S2. 🔴 `lore_read` does not honour the tier `exclude` policy — operator ruling needed.** Filtering
lives only in the indexer walk (`index/paths.is_included` + `walked_dirs`).
`read_file.FileReader._resolve` applies **containment only**. So **the exclude policy has two
populations and one of them does not enforce**: any file physically inside a tier root — excluded
from the index, `.gitignore`d, whatever — is readable through `lore_read` by any agent that names
its path. For a **live** tier that is the developer's whole checkout, including `.env` and
`.git/config`. Whether `lore_read` *should* honour excludes is a design question, not mine to
settle. (`acquire` applies no filter either, so those files are also copied into the `:ro`-mounted
snapshot.)

**S3. 🔴 `messages.drain` reports a fabricated `stamped_seqs`, and the contract certifies it.**
The `UPDATE … SET seen_at` return value is **discarded**; `stamped_seqs` is derived from the *read*
window. Under a concurrent second drain the loser's UPDATE matches **zero rows** and it still
reports every seq as stamped — while the field is documented as *"EXACTLY the seqs the served
window stamped seen."* **A build that deleted the UPDATE entirely would pass every existing
assertion**, because all of them compare `stamped_seqs` to the window, never to the store. Also:
the mark precedes the return, so a response lost in flight marks messages seen that nobody received
— and `drain` only serves `seen_at IS NONE`, making them **unreachable forever**. That is an
at-most-once decision made by statement ordering; the reader found no design sentence choosing it.
`[subagent-sourced]`

**S4. 🔴 `briefs.publish` compensates on an *unknown* outcome and can permanently wedge a brief
name.** The version is minted outside the CREATE, so a failure triggers a compensating decrement
guarded by `except SurrealStoreError` — whose comment enumerates *"TWO fates this ONE handler
catches"* and concludes *"either fate means nothing committed."* It catches a **third**:
`SurrealConnectionError` (a subclass), i.e. exactly the committed-but-unacknowledged case. Walk it:
v5 commits server-side, the response is lost, the counter rolls back to 4, the next publish mints 5
again, computes the same `uuid5`, and hits the existing record — **forever**, with an error naming
nothing about the counter. Its sibling `findings.report` is genuinely gapless *because the mint is
inside the transaction*; both claim gaplessness. `[subagent-sourced]`

**S5. 🔴 The `briefed` ack edge has neither `ENFORCED` nor an app-level check.** `RELATE` does not
validate endpoints (this repo's own store reference §4 says so, and names `BriefLedger.publish` by
name). `MessageLedger` does **both** guards; `BriefLedger` does **neither**. A typo'd `agent_id` at
`ack` writes a receipt for a ghost and returns **success**, while the real agent's ack is lost —
it believes it acked, `coverage()` reports it behind, and nothing errors or logs. `[subagent-sourced]`

**S6. 🔴 `_settle_schema_rebuild`'s documented mechanism does not run.** `[source-verified +
controlled]` The body is `if task is None or task.done(): return` — and a task that finished **with
an exception** is `done()`. Measured:
```
task.done() -> True   task.exception() -> RuntimeError('rebuild failed')
loremaster _settle_schema_rebuild surfaces: NOTHING
CONTROL (check .exception())              : rebuild failed
```
Because `app_context.schema_rebuild_task` holds a strong reference for the process lifetime,
asyncio's "Task exception was never retrieved" **never fires either**, and `aclose` swallows it with
a bare `pass`. **A failed background schema rebuild produces zero log lines for the entire process
lifetime**, while its docstring promises the opposite.

**S7. 🔴 `lore_findings action=query` silently serves the OLDEST 100 of a 180+ ledger.**
`[source-verified]` `_render_finding_rows` emits N rows with **no total and no "showing N of M"
trailer**, while the query caps at 100 ordered `number ASC`. Its sibling `_render_snapshot_rows`
implements exactly that trailer (finding #8's "no-silent-caps doctrine") and `_rollup_leg_header`
does too. **Every recent finding is invisible to the query tool right now.**

**S8. `_row_to_finding` and `_row_to_brief` render the literal string `"None"`.** Per the store
reference, a missing SELECT projection reads `None` — the key is *present*, so
`row.get(k, "")` never reaches its default and `str(None)` yields the four-character string
`"None"`. `messages._row_to_inbox_entry` gets this right (`row.get("body") or ""`), and
`findings` uses **both** idioms inside one method. Numeric columns diverge again into a raw
`TypeError`. `[subagent-sourced]`

**S9. A crash during a divergence heal permanently wedges the rebuilding notice.** The heal window
captures the prior blob and restores it verbatim; killed in between, the meta key is left
`in_progress`, and the next boot reads that stale value **as `prior`** and faithfully restores it.
No timestamp, pid, or lease distinguishes a live heal from a dead one — so **every read tool serves
"lore store is rebuilding its index" forever on a healthy index**, recoverable only by manual meta
surgery. (The schema-rebuild arm does not have this bug.) That blob also carries no `done`/`total`,
so the notice renders **"(0/0 files re-embedded)"**.

**S10. `_age_status_from_iso` renders a FUTURE stamp as maximally fresh.** `[measured]`
`max(age_seconds, 0.0)`, so clock skew makes `last_sync`/`last_sweep`/`newest_snapshot` report
**`0.0` seconds permanently** on the exact surface an agent reads to decide whether to trust the
index (`+2 days skew → SERVED 0.0s`). Same method: a **malformed** stamp returns a bare
`AgeStatus()` — byte-identical to "never happened" — and, unlike the naive-tz branch three lines
above, **is not even logged**.

**S11. `Indexer.index_status`'s counts do not cover the set their label claims.**
`[source-verified]` It counts only `STATE_INDEXED` and `STATE_FAILED` and hardcodes
`files_skipped=0`, but the manifest vocabulary has **four** states — rows in `dirty` and
`embedding` are in **neither bucket**, no total is served, and the gap is not derivable by the
caller. An index with 3,000 dirty of 5,000 serves `files_indexed: 2000, files_failed: 0`. It also
feeds the cosine-floor drift check.

**S12. `messages.py` is committed but NOT wired into `server.py`** (zero imports; `_COMMS_ACTIONS`
holds six actions, no `send`/`drain`/`ack`) — **while `test_comms_tool.py` calls
`AppContext.comms(action="send", to=[...], grade=...)`**, kwargs the method does not accept, and
asserts `len(_COMMS_ACTIONS) >= 9`. Meanwhile **the deployed lore MCP's own instructions advertise
`action=send`/`drain`/`ack`**. Either this tree is behind master's comms wiring, or the ledger is
dead code behind a red contract — and the shipped artifact disagrees with this branch's source,
which is the #139/#140 "which tree is real" shape. **I did not run the suite; no failure count.**

**S13. `_render_comms_fleet`'s STALE detector defaults to the most reassuring value.**
`heartbeat_age_seconds.get(row.id, 0)` — zero is below any positive `stale_after_s`, so a row
missing from the mapping renders `hb 0s` and **`⚠ STALE` never fires**. Two lines above,
`acked_versions.get(row.id)` defaults to `None` and its docstring calls that default
*"load-bearing"* — same idiom, opposite safety, no comment on the difference. The same render's
docstring claims *"there is no `len()`-derived fallback path here on purpose"* while **every read is
`.get(key, 0)`**. `[subagent-sourced]`

**S14. `Scout` lifecycle.** A crashed subscriber makes `stop()` re-raise, skipping `aclose()` and
**leaking all four write backends** · a `KeyError` from a malformed command row is classified as a
dropped socket and hot-loops forever at DEBUG, never marking the command failed · LIVE degrades
permanently to 5-second polling after one blip, with one DEBUG line as the entire signal · the
scout entrypoint **never calls `configure_logging`**, so `python -m loremaster.scout` would run with
no handler and no redaction filter at all (**latent** — the reader found no deployment reference).
`[subagent-sourced]`

**S15. Unindexed hot paths.** `messages.awaiting_answer` runs **two uncapped reads and an O(Q×D)
Python join on every heartbeat of every agent**, against a `message` table with **no index on
`sender` or `question`** — the *exact* defect this repo already caught and documented once (#103,
"6.1× leaf-elapsed at 11× rows, on EVERY heartbeat"), whose lesson was applied to
`briefs.subscribed_name_skew` and not here. Also unindexed: `message.seq` (every `ack`),
`finding.supersedes` (one full scan **per chain hop**, with `SELECT *`), and four `briefs` methods
that pull **every version including full bodies** to compute a `max` that `ORDER BY … LIMIT 1`
would serve. `[subagent-sourced]`

**S16. Budget/elision served numbers** `[subagent-sourced, not re-derived — leads]`:
`capped_visible` is measured **before** the pop loop and never recomputed, so the at-cap notice
over-claims; `visible` and `total` in that same sentence count **different sets**; `top_elided` can
be a *notice* rendered with a fabricated `score=0.000` — the exact hazard the sibling
`_worst_shown_score` guards against 30 lines away; the `[FILTER MISS]` teach is appended to the tail
and is therefore the **first** thing elided; and the `caller_model` note is appended **after**
enforcement, so its tokens are never counted.

**S17. Declared-but-inert contracts.** Seam 8 (`payload_index_specs`) is validated, collected,
exposed on a property — and **never applied**; only a comment 5,000 lines away records it.
`ToolSpec.input_schema`/`output_schema` are required fields the server **ignores** (the live
signature wins) with no warning on disagreement. `extension.SourceProvider`'s docstring claims
`runtime_checkable` gives a conformance check *"at registration"* — **no production code performs
it** (and `runtime_checkable` never checks signatures anyway). `findings.TERMINAL_STATUSES` is
declared, documented, and **never referenced**.

**S18. Duplicated policy, re-derived.** The **entire connection-lifecycle block** —
`_ensure_connection` (double-checked lock, both `except` arms), `close`, `_drop_connection`,
`_safe_close`, `_query`, `_apply` — is byte-for-byte identical across `findings.py`, `briefs.py`
and `messages.py` (~150 lines × 3), **including identical error f-strings**, and `tasks.py`/
`agents.py` carry it too. Helper census: `_as_rows` **9 copies**, `_bare_id` **7**, `_to_aware_utc`
**5**, `_require_aware_utc` **4** (one already diverged with an extra arg). `[subagent-sourced
counts — I did NOT re-derive them; do not cite as measured.]` This is the population the
predecessor flagged as "apparently separate and larger than #120's `_query` seam". Also:
`_build_source_providers` is a byte-equivalent clone of `index/cli.py::_source_providers` (which
`scout.py` *imports* — two of three roots share it, the server keeps a private copy) ·
`_DEFAULT_SNAPSHOT_ROOT` is defined in **three** modules by its own admission ·
`"claude-sonnet-5"` is a literal in **four** places with nothing pinning
`DEFAULT_YARDSTICK_MODEL == BASELINE_MODEL`.

**S19. Smaller, still real.** `reconcile_store_divergence`'s docstring names
`store.count_points(tier)`, a method that does not exist · `build_app_context`'s
`# noqa: PLR0915 - P8d rewrites this render` is a deferral with no decision point riding a lint
suppression, on a function now ~530 lines · `_MEMORY_SLUG_SUFFIX` is dead code · the
`_INSTRUCTIONS` comment claims *"14 mandatory tool-name mentions"* where the file registers **15** ·
`_ProcessLifespanGuard` tears down **outside** the lock after clearing its fields, so a concurrent
`acquire` can build a second `AppContext` (two inotify observers, two sweeps) — not reachable today
only because the eager lifespan holds a process-lifetime lease · `RootConfig.tier` is an
unvalidated path segment (`tier: ""` materialises onto the snapshot root itself) ·
`_render_comms_fleet_row` renders an unconditional ellipsis (`task_id[:8] + "…"`), claiming a
truncation that may not have happened.
