# REPORT-apply-152-tests-d

brief-base v5 read

- **state:** done-with-deviations — 26 hits re-derived, 24 rewritten, 2 left (§2.3, §3)
- **deviations:**
  - **A RED GATE IS ALREADY IN THE TREE AT HEAD** — `test_retired_symbols` fails at clean `b3e7687`, broken 13 commits back by `1666856`. §5.1
  - **Closing commits are NOT the blame line:** `test_indexer…:248` blames `df5431e`, closed by **`0a90687`**. 13 distinct closing commits, each derived. §2.2
  - **`test_surreal_store`'s 2 sites close at `8f24e11`, NOT the later `9d29111`** — my predecessor predicted otherwise; derived by `git log -S`. §2.2
  - **The CWD trap fired (nine now)** — a repo-relative `git grep` from `…/lore/loremaster` returned **0** where 26 was true; an asserted count caught it. §4.5
  - **Verb tense changed inside claim sentences** where present tense would keep the claim FALSE; 3 clauses deliberately left present because still true. §2.3
- **decisions-needed:**
  - **§5.1** — apply the three SUPERSEDED banners (`docs/` is DO-NOT-TOUCH for me), or accept a red pin? Exact text ready.
  - **§5.2** — `test_config.py:507` states the WRONG slug contract (hyphen allowed) 18 lines above the constant that rejects it. Exact edit ready.
  - **§5.3** — 2 stale-tense banners in `test_graph_surreal.py` (`:1004`, `:3046`) the three briefed patterns structurally CANNOT see. Exact edits ready.
  - **§5.5** — the instrument: key the pin on `today` (193 lines / 44 files), not on `RED` — §5.3 is the RED name-list already being defeated.
- **receipts:** green-before-rewrite §1 · ledger §2.3 · derivations §2.2 · untouched §3 · AST inertness + 2 controls §4.1 · gates §4.2–4.4 · flags §5

---

## 0. What binds this report

**Prose only.** No assertion, fixture, constant, signature, return, raise or control-flow
change — proven mechanically in §4.1 against HEAD, with a positive AND a negative control,
not asserted.

**Tool honesty (brief-base §4 / dogfood protocol).** `lore_findings` for #152 and #151
(ledger reads). Every *sweep* and every *provenance derivation* used **grep / `git log -S`
/ `git blame`**, deliberately: these are (b) non-symbol textual seams — tense markers inside
comments and docstrings — and (c) a cross-cutting history question. A symbol graph cannot
see the word "today" inside a docstring, and it has no notion of *which commit made a pin
go green*. That is the sanctioned fallback, said out loud; no friction filed, because this
is the protocol working rather than a lore gap.

**Backup before mutation (repo law).** All 12 candidate files were **committed and clean**
at start (`git status --porcelain` over exactly those paths: empty). A `cp -a` content
backup was still taken first — belt and braces, and it is the §4.1 comparator's second
baseline:

```
/tmp/apply152d-backup/   12 files, md5s in §4.6
```

---

## 1. Green-before-rewrite — the non-negotiable guard

**Nothing was rewritten before its pin was RUN.** Every suite below was run at a clean HEAD
`b3e7687`, BEFORE any edit. Counts are pasted, never summarised.

| suite | result at HEAD, pre-edit | verdict for its claims |
|---|---|---|
| `test_caplog_isolation.py` | `2 passed, 2 skipped in 0.91s` | GREEN (the 2 skips resolved below) |
| ↳ nested probe `::TestTheLeak` | `2 passed in 0.12s` | GREEN — the skipped pair really passes |
| `test_config.py` | `86 passed in 0.29s` | GREEN |
| `test_eager_startup.py` | `16 passed in 14.66s` | GREEN |
| `test_extension.py` | `47 passed in 7.29s` | GREEN |
| `test_graph_surreal.py` | `108 passed in 10.08s` | GREEN |
| `test_indexer_chunker_fault_isolation.py` | `6 passed in 0.72s` | GREEN |
| `test_mcp_server.py` | `640 passed in 86.58s` | GREEN |
| `test_resilient_db.py` | `13 passed in 1.83s` | GREEN |
| `test_retired_symbols.py` | **`1 failed, 15 passed in 5.02s`** | **GENUINELY RED — NOT TOUCHED** (§3.1, §5.1) |
| `test_surreal_harness.py` + `test_retry_seam.py` | `531 passed, 1 warning in 18.40s` | GREEN (the briefed gate baseline) |
| `test_surreal_store.py` | `178 passed in 12.55s` | GREEN |
| `test_task_ledger.py` | `234 passed in 82.30s` | GREEN |

**The two skips are resolved, not waved past.** `test_caplog_isolation.py`'s `TestTheLeak`
pair is `skipif`-ed in any outer run (`_NESTED_RUN_ENV = LORE_CAPLOG_LEAK_PROBE`) by design.
A skip is not a green. I ran the pair the way its own driver does:

```
$ cd /home/ejprice/PycharmProjects/lore && LORE_CAPLOG_LEAK_PROBE=1 uv run --project loremaster \
    python -m pytest "loremaster/tests/test_caplog_isolation.py::TestTheLeak" -p no:randomly -q --no-header
..                                                                       [100%]
2 passed in 0.12s
```

**No packet-03 blockage anywhere in my 12 files.** Zero collection errors, zero
`ModuleNotFoundError: loremaster.messages` in any of the runs above. So the third verdict
the brief provided for (`packet-03-blocked`) **applies to no site in this population** — I
looked for it rather than assuming its absence.

---

## 2. RULING — the 26 claims

### 2.1 The population, re-derived from the tree (not inherited)

```
$ cd /home/ejprice/PycharmProjects/lore && \
  git grep -nE "RED today|expected RED|RED by construction" -- 'loremaster/tests/' | wc -l
26
```
26 hits, 12 files — matching the lead's derivation exactly. Breakdown by pattern, derived:
**`RED today` ×25 · `RED by construction` ×1 · `expected RED` ×0.** (The brief names three
patterns; only two of them have any hits in the tree today. Worth knowing before someone
"fixes" a pattern that never matched.)

### 2.2 Closing commits — DERIVED per site, never assumed

The brief warned that a hand-list assumed one closing commit where there were two. **This
population has NINE.** Method per site: `git blame` the claim line for the *introducing*
commit, then `git log -S <production symbol>` on the **production** file to find where the
behaviour the claim describes actually changed — the two are NOT the same question, and for
one site they gave different answers.

| closing commit | date | what it shipped | sites |
|---|---|---|---|
| `4c2efbf` | 2026-07-13 | `conftest._restore_lore_logger_propagation` (`git log -S` on conftest: single hit) | 3 |
| `333ba50` | 2026-06-03 | `SlugStr` + `SLUG_PATTERN` in `config.py`; `0o700`/`0o600` in `sqlite_resilient.py` | 3 |
| `001f632` | 2026-06-03 | `server.py` eager composition + `_EAGER_BUILD_FAILED_MESSAGE` constant | 3 |
| `76f04c5` | 2026-06-01 | `LoreServer.extension_tool_specs` + `_register_tools` | 1 |
| `07dd5d8` | 2026-06-01 | handler-signature-derived `inputSchema` (`list[str]`→array, default→not-required) | 2 |
| `b04d89a` | 2026-07-02 | `_names_with_value_prefix` / `string::starts_with` module-prefix arm | 1 |
| `4afdbf4` | 2026-07-06 | the same arm extended to `references` / `tests_for` (#53) | 2 |
| `297194e` | 2026-07-03 | `_bare_name_answerers` bridge for `references` / `_reverse_neighbours` | 3 |
| `9171021` | 2026-07-04 | the bare-name bridge extended to `tests_for` | 1 |
| `0a90687` | 2026-07-02 | `Indexer._handle_chunk_failure` — per-file chunker isolation | 1 |
| `c30edd6` | 2026-07-11 | `sanitise_line` wraps on finding_rows / task_rows / claim_result | 1 |
| `8f24e11` | 2026-07-13 | `random.uniform` full jitter + `_ASSERT_VIOLATION_MARKER = "must conform to"` | 2 |
| `352db0e` | 2026-07-20 | `label=`/`url=` reach `bootstrap_session`'s three `retry_on_conflict` calls | 1 |

**⚠ The one site where blame LIES.** `test_indexer_chunker_fault_isolation.py:248` blames to
`df5431e` (2026-07-03, "rewire indexer onto the composed atomic apply") — but that commit
only *moved* the line. The file was **added** by `0a90687` (2026-07-02, "isolate chunker
exceptions per-file instead of crashing the sweep"), which is also where
`_handle_chunk_failure` was introduced:

```
$ git log --oneline --diff-filter=A -- loremaster/tests/test_indexer_chunker_fault_isolation.py
0a90687 fix(indexer): isolate chunker exceptions per-file instead of crashing the sweep
$ git log --oneline -S "_handle_chunk_failure" -- loremaster/loremaster/index/indexer.py
84ad87d feat(indexer): two-pass bulk-sweep batch embedding (Voyage Batch part 2)
0a90687 fix(indexer): isolate chunker exceptions per-file instead of crashing the sweep
```
Marking this site `df5431e` would have been a **new false claim** — exactly what the brief
forbade. The contrast site is `test_graph_surreal.py:1015`, which blames to `b04d89a` and
**genuinely is** closed by `b04d89a` (`_names_with_value_prefix` lands in that same commit).
Same wave, same instrument, opposite answers: the blame line is a lead, never the verdict.

**⚠ `test_surreal_store.py`'s two sites are closed by `8f24e11`, NOT by the later
`9d29111`.** My predecessor's §5.2 predicted these "were falsified by *later* commits". They
were not — derived:

```
$ git log --oneline -S 'random.uniform' -- loremaster/loremaster/store/_txn.py
8f24e11 fix(store): the rollback verdict becomes semantic …
$ git log --oneline -S '_ASSERT_VIOLATION_MARKER = "must conform to"' -- loremaster/loremaster/store/_txn.py
8f24e11 fix(store): the rollback verdict becomes semantic …
```
Both the full jitter and the corrected marker arrived in `8f24e11` — the same commit that
introduced the pins. `9d29111` later *moved* the jitter into the shared driver; it did not
make either pin go green. Naming `9d29111` here would have been wrong.

### 2.3 Per-site ledger — 24 rewritten

Every line is `file:line` · verdict · closing commit · before → after. Line numbers are
**pre-edit** (HEAD `b3e7687`); the diff is same-line-count throughout, so they still resolve.

| # | file:line | pin verdict | closing | before → after |
|---|---|---|---|---|
| 1 | `test_caplog_isolation.py:41` | green | `4c2efbf` | `RED today; GREEN the moment a` → `RED before 4c2efbf; GREEN the moment a` |
| 2 | `test_caplog_isolation.py:94-95` | green (nested) | `4c2efbf` | `RED today: … is still in force, caplog's` / `root handler is never reached, and this sees an empty list` → `RED before 4c2efbf: … was still in force, caplog's` / `root handler was never reached, and this saw an empty list` |
| 3 | `test_caplog_isolation.py:115` | green | `4c2efbf` | `"""RED today. GREEN once …` → `"""RED before 4c2efbf. GREEN once …` |
| 4 | `test_config.py:512` | green | `333ba50` | `These tests are BEHAVIOURALLY RED today: the unconstrained ``str`` accepts every` → `These tests were BEHAVIOURALLY RED before 333ba50: the unconstrained ``str`` accepted every` |
| 5 | `test_eager_startup.py:475` | green | `001f632` | `goes RED today and only passes` → `went RED before 001f632 and only passes` |
| 6 | `test_eager_startup.py:892` | green | `001f632` | `(the RED today),` → `(the RED before 001f632),` |
| 7 | `test_eager_startup.py:941` | green | `001f632` | `the implementation may not yet emit (RED today).` → `the implementation did not yet emit (RED before 001f632).` |
| 8 | `test_extension.py:692-693` | green | `76f04c5` | `RED today: … tool is collected by` / `… so it is absent from the live` → `RED before 76f04c5: … tool was collected by` / `… so it was absent from the live` |
| 9 | `test_extension.py:802-803` | green | `07dd5d8` | `RED today: ``factor`` is` / `wrongly published as required (every arg is KEYWORD_ONLY …)` → `RED before 07dd5d8: ``factor`` was` / `wrongly published as required (every arg was KEYWORD_ONLY …)` |
| 10 | `test_extension.py:843` | green | `07dd5d8` | `RED today: both collapse to string.` → `RED before 07dd5d8: both collapsed to string.` |
| 11 | `test_graph_surreal.py:1015` | green | `b04d89a` | `RED today: Model A has no module-prefix reverse arm` → `RED before b04d89a: Model A had no module-prefix reverse arm` |
| 12 | `test_graph_surreal.py:1524` | green | `4afdbf4` | `RED today: ``tests_for`` has no module-prefix arm` → `RED before 4afdbf4: ``tests_for`` had no module-prefix arm` |
| 13 | `test_graph_surreal.py:1628` | green | `4afdbf4` | `RED today: ``references`` has no module-prefix arm` → `RED before 4afdbf4: ``references`` had no module-prefix arm` |
| 14 | `test_graph_surreal.py:3059-3060` | green | `297194e` | `RED today (live-verified …)` / `("widget")`` returns` → `RED before 297194e (live-verified …)` / `("widget")`` returned` |
| 15 | `test_graph_surreal.py:3112-3113` | green | `297194e` | `RED today (live-verified)` / `returns ``[]`` although` → `RED before 297194e (live-verified)` / `returned ``[]`` although` |
| 16 | `test_graph_surreal.py:3181-3182` | green | `9171021` | `RED today (live-reproduced)` / `never rides … so it returns an EMPTY set` → `RED before 9171021 (live-reproduced)` / `never rode … so it returned an EMPTY set` |
| 17 | `test_graph_surreal.py:3353` | green | `297194e` | `RED today: the aggregate is 0` → `RED before 297194e: the aggregate was 0` |
| 18 | `test_indexer_chunker_fault_isolation.py:248` | green | **`0a90687`** | `RED today: the ParseError propagates out of index_all` → `RED before 0a90687: the ParseError propagated out of index_all` |
| 19 | `test_mcp_server.py:7796` | green | `c30edd6` | `RED today (raw f-string interpolation, no wrap) except` → `RED before c30edd6 (raw f-string interpolation, no wrap) except` |
| 20 | `test_resilient_db.py:569` | green | `333ba50` | `These tests are BEHAVIOURALLY RED today: the default-mode mkdir yields 0755` → `These tests were BEHAVIOURALLY RED before 333ba50: the default-mode mkdir yielded 0755` |
| 21 | `test_resilient_db.py:756` | green | `333ba50` | `These mode assertions are BEHAVIOURALLY RED today:` → `These mode assertions were BEHAVIOURALLY RED before 333ba50:` |
| 22 | `test_surreal_harness.py:740` | green | `352db0e` | `"""RED today x3: the record carries ``attempts`` …` → `"""RED before 352db0e x3: the record carried ``attempts`` …` |
| 23 | `test_surreal_store.py:3423-3425` | green | `8f24e11` | `RED today: every racer sleeps …` / `All 16 wake together` / `and re-collide. That is the lockstep, … what makes` → `RED before 8f24e11: every racer slept …` / `All 16 woke together` / `and re-collided. That was the lockstep, … what made` |
| 24 | `test_surreal_store.py:4585-4586` | green | `8f24e11` | `RED today: the engine says "must conform to", the marker says "assert"` / `the caller is told` → `RED before 8f24e11: the engine says "must conform to", the marker said "assert"` / `the caller was told` |

**Three deliberate NON-changes inside edited sentences**, because the clause is still TRUE
and past-tensing it would introduce a *new* falsehood:

- #24 — **`the engine says "must conform to"` stays present tense.** The engine still emits
  that text; only the *marker* was wrong. Past-tensing both would have implied the engine
  changed, which it did not. Half the sentence moved, half did not, on purpose.
- #15 — `` `demo.consumer.run` is one real reverse hop away `` stays present tense: it still is.
- #17 — `(neither collidee's FQN dst equals the bare id)` stays present tense: it still
  doesn't, which is *why* the bridge exists.

### 2.4 Why "the introducing commit IS the closing commit" is not a reason to leave a claim

For 11 of the 13 closing commits, the pin and its production fix shipped **together** (verified
per commit via `git show --stat`, production paths listed). My predecessor's §5.2(b) offered
that as grounds to accept the claims as "contract archaeology". I applied the brief's ruling
instead, and I think the brief is right: **a docstring is read in the tree it is checked out
of, not in the tree its author was staring at.** A reader running `pytest` today sees a green
pin whose own prose says it is red, and repo law rates that above a dangling citation. The
`RED before <sha>` form loses nothing — it preserves the historical claim verbatim *and*
names the commit, so the archaeology is strictly better served than by `today`.

---

## 3. Sites left UNTOUCHED — individually, with the reason

*"All remaining hits are X" is banned output, so each of the two gets its own verdict.*

### 3.1 `test_retired_symbols.py:438` — **GENUINELY RED. Not touched.**

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest tests/test_retired_symbols.py -q -p no:randomly
FAILED tests/test_retired_symbols.py::TestNoFileReferencesARetiredSymbol::test_no_file_references_a_retired_symbol
1 failed, 15 passed in 5.02s
```
The pin's docstring says `"""RED today at every site below.` — and it **is** red today. There
is no green receipt available, so rewriting it would launder a live defect. Left exactly as
found. Its cause is a genuine, currently-open defect: see §5.1.

### 3.2 `test_task_ledger.py:1550` — **ALREADY COMPLIANT. Not touched.**

```
# RED by construction; PKT-06 (f80e95a) shipped all three and it is GREEN today.
```
Past tense, names its closing commit, states the present truth. I re-derived the commit
rather than trusting the prose — `f80e95a` ("feat(comms): PKT-06 orchestration ledger verbs
+ render sanitisation") does ship `summary` / `report_path` on the done-transition and the
new ledger verbs. Suite: `234 passed`. **This is the form the other 24 now match**, and it
gives any future AST pin (§5.5) a positive control on day one.

---

## 4. Gates and mechanical proof

### 4.1 AST inertness — proven, with BOTH controls

`/tmp/ast_inert.py` parses each changed file at HEAD and in the working tree, **strips every
docstring** (comments never reach the AST at all), and compares `ast.dump()`. Any assertion,
signature, assignment, return, raise or constant change alters the dump.

A probe needs a control (repo law), so it carries two:

```
IDENTICAL        loremaster/tests/test_caplog_isolation.py
IDENTICAL        loremaster/tests/test_config.py
IDENTICAL        loremaster/tests/test_eager_startup.py
IDENTICAL        loremaster/tests/test_extension.py
IDENTICAL        loremaster/tests/test_graph_surreal.py
IDENTICAL        loremaster/tests/test_indexer_chunker_fault_isolation.py
IDENTICAL        loremaster/tests/test_mcp_server.py
IDENTICAL        loremaster/tests/test_resilient_db.py
IDENTICAL        loremaster/tests/test_surreal_harness.py
IDENTICAL        loremaster/tests/test_surreal_store.py

POSITIVE CONTROL (flip one `assert X` -> `assert not X` in loremaster/tests/test_caplog_isolation.py): SEES IT (good)
NEGATIVE CONTROL (docstring word swap in loremaster/tests/test_caplog_isolation.py): IGNORES IT (good)

10 files compared, 0 differ: none
EXIT=0
```
The positive control matters: without it, "0 differ" is equally consistent with a comparator
that cannot see anything. The negative control matters too — it proves the comparator is not
so blunt that it would have called a prose edit a logic change and hidden a real one in the
noise.

Corroborating, the raw diff is **33 insertions / 33 deletions across 10 files, every changed
line beginning with `#` or living inside a `"""` docstring** — no `+`/`-` line touches an
`assert`, a `def`, a `=`, a `return` or a `raise`.

### 4.2 The briefed gate — unchanged at 531/0

The brief's exact command, run post-edit:

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && \
  uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
…
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
531 passed, 1 warning in 18.61s
```
**531 / 0, identical to the pre-edit baseline in §1.**

### 4.3 Every suite whose file I touched — post-edit, with counts

One serial run over all eleven briefed/touched files (`-p no:randomly`, no xdist):

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
    tests/test_surreal_harness.py tests/test_retry_seam.py tests/test_caplog_isolation.py \
    tests/test_config.py tests/test_eager_startup.py tests/test_extension.py \
    tests/test_graph_surreal.py tests/test_indexer_chunker_fault_isolation.py \
    tests/test_mcp_server.py tests/test_resilient_db.py tests/test_surreal_store.py \
    -q -p no:randomly
1627 passed, 2 skipped, 1 warning in 840.51s (0:14:00)
EXIT=0
```

And each file individually (`-n auto`), so no count hides inside an aggregate:

| suite | post-edit | pre-edit (§1) | delta |
|---|---|---|---|
| `test_caplog_isolation.py` | `2 passed, 2 skipped in 4.73s` | `2 passed, 2 skipped` | 0 |
| ↳ nested `::TestTheLeak` | `2 passed in 0.11s` | `2 passed` | 0 |
| `test_config.py` | `86 passed in 4.44s` | `86 passed` | 0 |
| `test_eager_startup.py` | `16 passed in 7.15s` | `16 passed` | 0 |
| `test_extension.py` | `47 passed in 6.92s` | `47 passed` | 0 |
| `test_graph_surreal.py` | `108 passed in 10.27s` | `108 passed` | 0 |
| `test_indexer_chunker_fault_isolation.py` | `6 passed in 5.95s` | `6 passed` | 0 |
| `test_mcp_server.py` | `640 passed in 87.89s` | `640 passed` | 0 |
| `test_resilient_db.py` | `13 passed in 5.75s` | `13 passed` | 0 |
| `test_surreal_harness.py` | `57 passed in 5.48s` | (inside the 531) | 0 |
| `test_surreal_store.py` | `178 passed in 12.49s` | `178 passed` | 0 |

**The aggregate reconciles against the parts, checked rather than trusted:**
531 + 4 + 86 + 16 + 47 + 108 + 6 + 640 + 13 + 178 = **1629** = `1627 passed + 2 skipped`. A
passed-COUNT is present in every tail above; no run exited "no tests ran" behind a pipe.

### 4.4 ruff and typecheck

```
$ cd /home/ejprice/PycharmProjects/lore && uv run ruff check .
All checks passed!
RUFF EXIT=0
```

```
$ cd /home/ejprice/PycharmProjects/lore && ./scripts/typecheck.sh
…
loremaster/tests/test_message_ledger.py:1736: error: Returning Any from function declared to return "int"  [no-any-return]
Found 55 errors in 5 files (checked 146 source files)
typecheck: loremaster FAILED
TYPECHECK EXIT=1
```
**Exactly the 55 the brief predicted** (packet-03 comms, unrelated), and **zero in any of the
10 files I touched** — derived, not eyeballed:

```
$ grep -cE "test_(caplog_isolation|config|eager_startup|extension|graph_surreal|indexer_chunker_fault_isolation|mcp_server|resilient_db|surreal_harness|surreal_store)\.py" /tmp/typecheck.log
0
```

**Line length.** ruff's config is `line-length = 110` (`pyproject.toml:33`). Every edited line
was measured after the fact; the longest is `test_surreal_harness.py:740` at **108**. Two lines
in `test_mcp_server.py` (`:4514` at 114, `:7139` at 112) exceed 110 — both are **pre-existing at
HEAD** (verified against `git show HEAD:` at the same line numbers) and ruff passes anyway, so
E501 is not enabled here. Neither is mine. **No paragraph was reflowed and no rewrap was needed.**

### 4.5 ⚠ The CWD trap fired — and an asserted count is what caught it

The brief said it had fired eight times. Make it nine. Running

```
git grep -nE "(^|[^A-Za-z_])RED([^A-Za-z_]|$)" -- 'loremaster/tests/'
```
after an earlier `cd …/lore/loremaster` returned **0 lines**. Zero is not a plausible answer
for a pattern I had already matched 26 times, so I checked instead of believing it: `git grep`
resolves its pathspec **relative to the shell's cwd**, and `loremaster/tests/` does not exist
under `…/lore/loremaster`. It exits 1 with no output and reads exactly like "clean". Re-run
from the repo root: **276 lines**.

The lesson is not "remember to cd" — the brief already said that and it happened anyway. It is
that **the count assertion is the instrument**. Had I been sweeping for something whose true
answer might plausibly have been 0, this would have shipped as "nothing found".

### 4.6 Backups — and a proof they can actually restore

All 12 candidate files were committed and clean at start, so `git` already held the content;
the `cp -a` was taken anyway (repo law) and then *proven* to be a valid restore source rather
than assumed:

```
$ for f in $(git diff --name-only); do git show "HEAD:$f" | diff -q - /tmp/apply152d-backup/$(basename $f); done
identical-to-HEAD: 10   mismatched: 0
```

| file | md5 (pre-edit) |
|---|---|
| `test_caplog_isolation.py` | `264d3d967fd2bd1db53a7b4604dfe5d5` |
| `test_config.py` | `0beab637f2cb04f75cc74dc1301299ec` |
| `test_eager_startup.py` | `4a15f6b8edf014838d3edd254d39ee32` |
| `test_extension.py` | `30dad00be04ecca4947b834b443bc250` |
| `test_graph_surreal.py` | `bcd2fdb24fbe0da40911a43d1f3b24a9` |
| `test_indexer_chunker_fault_isolation.py` | `044939240fe52d215e4554301162afce` |
| `test_mcp_server.py` | `bf40c2ca923ba5b425e9720eb53f16c7` |
| `test_resilient_db.py` | `3a93f87f56b2b5b1b668e0c3d038dc49` |
| `test_retired_symbols.py` | `2a1fd771076a2ee1c24e9d91a5cd3ac9` (untouched) |
| `test_surreal_harness.py` | `f977d4cb0296e004e247cb91099f15a8` |
| `test_surreal_store.py` | `0c26d4cbcd684e9aa6fdfdbc5a41e809` |
| `test_task_ledger.py` | `62aa275cd954448e218bb50f4faaa12b` (untouched) |

Per repo law an MD5 list is a **detector, not a backup** — the content itself is at
`/tmp/apply152d-backup/`, and the diff above proves it is the right content.

---

## 5. Flags — everything I noticed, per scope law

### 5.1 ⚠⚠ **A RED GATE IS SITTING IN THE TREE AT HEAD — from THIS wave, 13 commits ago**

This is the most important thing in this report and it is not part of my task.

`test_retired_symbols.py::test_no_file_references_a_retired_symbol` **fails at a clean HEAD
`b3e7687`** — before I touched anything (§1). Its output:

```
docs/plans/v2/receipts/2026-07-20-probes/102-recovery/DESIGN-102-addendum.md
    [DATED RECORD, no banner] mentions ['_apply_mint']
docs/plans/v2/receipts/2026-07-20-probes/102-recovery/DESIGN-102-final.md
    [DATED RECORD, no banner] mentions ['_REPORT_MINT', '_apply_mint']
docs/plans/v2/receipts/2026-07-20-probes/102-recovery/DESIGN-102-preliminary.md
    [DATED RECORD, no banner] mentions ['_REPORT_MINT', '_TXN_CONFLICT_BACKOFF_SECONDS', '_apply_mint']
```

**Provenance, derived:**

```
$ git log --oneline --diff-filter=A -- 'docs/plans/v2/receipts/2026-07-20-probes/102-recovery/DESIGN-102-*.md'
1666856 docs(receipts): #152 archive the #102 design record and the surviving probe instruments
$ git log --oneline | grep -n 1666856
13:1666856 …
```

**The archive law broke its own enforcer.** `1666856` did exactly what the new CLAUDE.md rule
demands — it archived rather than deleted — and in doing so it moved three DATED RECORDS that
name `_apply_mint` / `_REPORT_MINT` / `_TXN_CONFLICT_BACKOFF_SECONDS` into the scanner's reach.
The pin has been red for **13 commits**. This is the repo's own §"A DIAGNOSIS IS NOT AN
INSTRUMENT" pattern in miniature: an instrument existed, it fired correctly, and the wave
carried on above it.

**The fix is three prepends, and the pin's own tests define the accepted form** (`:383`,
`:412`). `docs/` is DO-NOT-TOUCH for me, so here is the exact edit, ready to apply:

```markdown
> **SUPERSEDED (finding #102, 2026-07-13):** `_apply_mint` was deleted; its
> deterministic, id-derived jitter **IS** the defect #102 fixed. Do not use it as a
> pattern. See `_txn.retry_on_conflict`.
```
prepended to `DESIGN-102-addendum.md`; the same with `` `_REPORT_MINT` `` added for
`DESIGN-102-final.md`; and with `` `_REPORT_MINT` `` **and**
`` `_TXN_CONFLICT_BACKOFF_SECONDS` `` for `DESIGN-102-preliminary.md`. The banner must NAME
every retired symbol the document mentions — the pin checks that specifically
(`test_retired_symbols.py:468`, *"the SUPERSEDED banner does not name them"*), so a generic
banner will not clear it.

**Ruling needed: apply the banners, or accept a red pin?** I did not touch them.

### 5.2 ⚠ `test_config.py:507` states the WRONG slug contract — 13 lines above the right one

Found while deriving `333ba50`. Same defect class as #151 (a prose clause that is outright
FALSE), outside my grep, so **not applied**:

```
:506  # The contract (from the requirement, NOT from any implementation): the slug must
:507  # match ``^[a-z0-9][a-z0-9_-]*$`` — lowercase alphanumerics plus ``-`` / ``_``,
…
:520  # Lowercase alnum + ``_``, must start with an alnum, non-empty. HYPHENS ARE
:521  # REJECTED (operator directive 2026-07-03) …
:525  _SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"
```
The banner permits hyphens; the constant 18 lines below rejects them, `my-proj` is in
`_INVALID_SLUGS`, and production agrees with the constant (`config.py:87`,
`SLUG_PATTERN = r"^[a-z0-9][a-z0-9_]*$"`).

**How it got there, derived:** `333ba50` (2026-06-03) shipped the pattern **with** the hyphen;
`604b113` (2026-07-03) tightened it to reject hyphens. The constant and production moved; the
banner did not.

```
$ git log --oneline -S 'r"^[a-z0-9][a-z0-9_-]*$"' -- loremaster/loremaster/config.py
604b113 feat(server): compose the Surreal write stack …      # removed it
333ba50 feat(startup): idempotent-startup follow-ups …       # introduced it
```

Exact edit I would make:

```diff
-# match ``^[a-z0-9][a-z0-9_-]*$`` — lowercase alphanumerics plus ``-`` / ``_``,
+# match ``^[a-z0-9][a-z0-9_]*$`` — lowercase alphanumerics plus ``_`` (hyphens
+# REJECTED at 604b113; see the note at the constant below),
```

**Consequence for my own edit #4, stated plainly:** I marked `test_config.py:512`
`RED before 333ba50`, because `333ba50` is where the field stopped being an unconstrained
`str` — which is precisely what that claim says. But the `my-proj` fixture entry was added
later and was only *rejected* from `604b113`. If the lead prefers the marker to cover the
whole fixture list as it stands today, the alternative reading is `RED before 604b113`. **I
would keep `333ba50`**: the claim names the *unconstrained `str`*, and that is the thing
`333ba50` killed. Both readings written down, per brief-base §2.

### 5.3 ⚠ Two stale-tense SECTION BANNERS the three briefed patterns structurally cannot see

Both in `test_graph_surreal.py`, both making a present-tense claim about production that is
now false, both invisible to `RED today|expected RED|RED by construction` because they phrase
it differently. **Not applied** — outside the briefed grep, and the brief's population is 26.

- **`:1004`** — `…so these queries return [] today (RED below).` They do not return `[]`
  today; `b04d89a` shipped the arm. The class docstring 11 lines below (my edit #11) now says
  `RED before b04d89a` and points *at this banner* — so the banner is now the last
  present-tense falsehood in that section, and the citation makes a reader go read it.
  Exact edit: `so these queries return [] today (RED below).` → `so these queries returned []
  before b04d89a (RED below).`
- **`:3046`** — `…so today ``references("widget")`` and ``blast_radius("widget", ...)``
  silently return an all-zero / empty result…` Closed by `297194e`.
  Exact edit: `so today ``references(…)`` … silently return` → `so before 297194e
  ``references(…)`` … silently returned`.

**This is the generalisable finding of my pass:** the three briefed patterns are a
*name-list*, and repo law's own most expensive lesson is that name-lists get defeated by the
next spelling. `return [] today` and `so today … silently return` are the same defect with no
`RED` token adjacent to the tense marker. §5.5 is the answer.

### 5.4 The wider population — DERIVED, and deliberately NOT bulk-classified

```
$ cd /home/ejprice/PycharmProjects/lore && git grep -nE "(^|[^A-Za-z_])RED([^A-Za-z_]|$)" -- 'loremaster/tests/' | wc -l
276
… of which the three briefed patterns match 26 → 250 outside my task
… of those 250, already in the compliant `RED before <sha7>` form: 36
```
Per-file leaders among the 250: `test_retry_seam.py` 56 · `test_surreal_store.py` 22 ·
`test_shellout_seam_perimeter.py` 11 · `test_graph_surreal.py` 11 ·
`test_comms_render_architecture.py` 11 · `test_resilient_db.py` 10 · `test_comms_tool.py` 10
· `test_surreal_apply.py` 9 · `test_shellout_allowlist.py` 9 ·
`test_comms_promise_registry.py` 9 · then a long tail across 40 more files.

**I am NOT classifying these 250.** I sampled 10 and every sampled line was legitimate
present-tense discriminator language (`goes RED until the author registers it`, `so it goes
RED the day someone closes it`) — correct prose that must NOT be past-tensed. **That is a
sample of 10, not a verdict on 250**, and "all remaining hits are X" is banned output. A real
pass over them needs the same per-site treatment I gave the 26. My estimate of the *stale*
subset is genuinely unknown; the honest number is "unmeasured".

### 5.5 The instrument this class still lacks — and why it is worth more than my 24 edits

My predecessor proposed an AST scan refusing `RED today` / `expected RED` in a
docstring/comment unless followed by a commit-shaped marker. I second it, **with one change
that §5.3 makes necessary**: keying it on those literals is a name-list, and §5.3 is the
name-list already being defeated *inside the same file I just edited*.

Key it on the **tense token, not the RED token**: any comment/docstring line in
`loremaster/tests/` containing the standalone word `today` must also carry a 7-hex-digit
commit marker, a `#NNN` finding number, or an explicit `GREEN today` present-truth statement.
`today` is short, greppable, and is the actual thing that rots — `RED` is not.

Measured, so the pin's cost is known before anyone builds it:

```
$ cd /home/ejprice/PycharmProjects/lore && git grep -niE "(^|[^A-Za-z])today([^A-Za-z]|$)" -- 'loremaster/tests/' | wc -l
193          # lines, across 44 files
```
193 lines is a real but bounded adjudication job — and unlike `RED`, the token is the thing
that actually rots. Positive control on day one: `test_task_ledger.py:1550` (`…and it is GREEN today.`) is the
compliant form; the 24 lines I just rewrote are the compliant form; `:1004`'s `return []
today` is the violation it must catch — and my grep could not.

**Repo law says a fix without an invariant is half a fix.** 24 edits without this pin means
the class regenerates at the next contract-first wave. It regenerated *between* my
predecessor's pass and mine — `test_graph_surreal.py:1004` was there the whole time and
neither of our greps could see it.

### 5.6 One residual honesty note on my own edits

For 11 of the 13 closing commits, the pin and its fix shipped in the **same** commit
(§2.4). A pedant could argue `RED before <sha>` is odd for a pin that was never red in any
*committed* tree. I think it is right — it is red against the tree *before* that commit,
which is exactly what it says — but the alternative wording `RED as authored, GREEN from
<sha>` is equally true and arguably clearer. I used the brief's prescribed form uniformly
rather than inventing a second one, because two forms for one fact is how §5.3 happens.

---

## 6. Compliance

- **Writable set respected.** Touched exactly the 10 test files in §4.1 plus this report.
  `test_retired_symbols.py` and `test_task_ledger.py` were **read only** and are clean in
  `git status`. Nothing under `loremaster/loremaster/`, `docs/`, `pyproject.toml`, `.claude/`.
- **Prose only, proven mechanically** (§4.1), not asserted — with a positive and a negative
  control, because a probe without a control can pass for the wrong reason.
- **Git state untouched.** No stage, no commit, no revert, no checkout, no stash. The lead
  commits.
- **No worktrees. No repo-wide auto-fixer.** Every one of the 24 edits was an individually
  asserted, exact-string `Edit` call.
- **Ledger board untouched** — my brief names no task row (brief-base §5).
- **Test store only.** Every live-tier suite ran against the harness's own per-test databases;
  `:18500` was never addressed.
- **Backup retained** at `/tmp/apply152d-backup/` (§4.6), proven byte-identical to HEAD.

