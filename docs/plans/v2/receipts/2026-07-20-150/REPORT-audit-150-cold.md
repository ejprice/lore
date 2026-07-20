# REPORT — audit-150-cold (finding #150, COLD REFUTE audit)

brief-base v5 read

## SUMMARY BLOCK

- **verdict: GO** — every load-bearing claim in `REPORT-harness-retry-builder.md` reproduced
  independently. Production drift is byte-zero. The contract genuinely fails on the unfixed build.
- **state:** done
- **blockers: NONE.**
- **residual count: 8** (1 medium = a missing pin; 7 low/info). Full table §7 — read it, do not
  read only this block.
- **The one finding worth the lead's attention (R1):** a wrong build I constructed —
  `connect_admin` inlining THREE INDEPENDENT `retry_on_conflict` budgets instead of the composed
  `bootstrap_session` — **passes the entire contract 17/17.** Shipped code is correct; the pin is
  missing. Brief item 6, bullet 4.
- **One confirmed prose defect (R2):** *"21 test files import this harness"* is **FALSE — it is 35**
  (AST-derived), written at 4 committed sites, and it is the stated justification for RULING 1.
  The substantive claim it supports I re-verified independently and it holds anyway.
- **deviations:** none. Report-only honoured; no fix, no edit, no commit.
- **receipt pointers:** gates §2 · RED proof §3 · seam mutations §4 · wrong-build probes §5 ·
  independent removed-behaviour enumeration + diff vs builder §6 · residuals §7 · bare-grep sweep §8.
- **tree state:** `git status --short` = 3 untracked reports/scratchpad only; `_txn.py` md5
  `e67978f0dc474af17079ed9ee0c5cb1a`, harness md5 `0d60e5158653a7bacb19548c373015fe` — both
  byte-identical to pre-audit backups (§9).

---

## 1. Production drift — INDEPENDENTLY VERIFIED ZERO

```
$ git diff 8c96451..HEAD -- loremaster/loremaster/
[prod diff bytes: 0]

$ git diff --stat 8c96451..HEAD
 loremaster/tests/_surreal_harness.py     | 159 +++++----
 loremaster/tests/test_retry_seam.py      |  86 ++---
 loremaster/tests/test_surreal_harness.py | 540 ++++++++++++++++++++++++++++---
 3 files changed, 618 insertions(+), 167 deletions(-)
```

Byte-exactness of `_txn.py` after the builder's own mutation proof is confirmed not by `git status`
but by content diff against a `cp -a` backup I took before touching anything, re-proven after every
one of my seven mutations (§9). **Claim verified.**

⚠ Tooling note for the lead: my first `git diff … -- test_retry_seam.py` returned EMPTY output while
`--numstat` reported `21/65`. Re-running to a file gave 6177 bytes. A parallel-tool-call artifact,
not a repo condition — but it is exactly the "green claim with no count" failure mode in reverse, so
I re-derived every diff through `--numstat` before trusting it.

## 2. Gates — re-run by me, with passed-COUNTs

| gate | my result | builder claimed | verdict |
|---|---|---|---|
| `pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q` | **420 passed, 1 warning in 11.46s** | 420 passed | ✅ exact |
| live store, real engine: `pytest tests/test_txn_contention.py tests/test_surreal_store.py -q -n auto` | **200 passed in 12.14s** | 353 passed (3-file set) | ✅ (different set; both counted) |
| `./scripts/typecheck.sh` | **Found 55 errors in 5 files (checked 146 source files)** | 55 in 5 | ✅ exact |
| mypy errors in the 3 changed files | **none** (grep returned nothing) | zero | ✅ |
| `uv run ruff check .` | **All checks passed!** | clean | ✅ |

**Store targeting proven, not assumed:** `systemctl --user is-active spike-surreal.service` → `active`;
`LORE_TEST_SURREAL_URL` = **unset** → `DEFAULT_URL = ws://127.0.0.1:18000/rpc`. Production **:18500 was
never contacted.** The live suites drive `surreal_env`/`admin_db`, i.e. `connect_admin` → `bootstrap_session`
against the real engine, hundreds of times under `-n auto`.

### 2.1 The RED floor did NOT grow — measured on both trees, not reasoned

I swapped the OLD harness in (from `git show 8c96451:…`) and ran the **33 unchanged consumer files**
(the 2 changed test files excluded so the comparison set is identical on both sides):

| tree | result |
|---|---|
| HEAD (`0734d78`) | `61 failed, 2698 passed, 166 errors in 154.42s` |
| baseline (old harness) | `61 failed, 2698 passed, 166 errors in 151.44s` |

**Identical on all three counters.** Zero consumer regressions; the packet-03 RED floor is unchanged.
(My comparison set is 33 files, not the builder's 21 — see R2.)

## 3. THE RED PROOF — does the contract fail on the unfixed build?

The killer question. New pins, OLD harness swapped in:

```
13 failed, 4 passed in 0.56s
```
Failures span all four pin classes: 3 `connect_admin` bootstrap pins, 2 teardown pins, 5
`TestTheHarnessRetryPolicyIsTheSeamsPolicy` sharing pins, 3 parametrised
`test_the_private_policy_constants_are_gone`. **Exactly matches the builder's §3.2 claim (13/4),
independently reproduced.** The contract is not decorative.

## 4. Seam mutations — run by me, on the real tree, restored byte-exact

Baseline unmutated: `17 passed in 0.16s`.

| # | mutation in `_txn.py` | observed | reading |
|---|---|---|---|
| **MU1** | `:409` `_RETRYABLE_CONFLICT_MARKER` → `"MUTANT: no engine emits this"` | **11 failed, 6 passed** | detection on BOTH paths moves with the seam — no private marker copy exists |
| **MU2** | `:484` `_TXN_CONFLICT_ATTEMPT_CEILING` `64 → 9` | **17 passed** — *green* | **correct by design, see below** |
| **MU2b** | give-up predicate stops READING the constant (`attempts >= _TXN_CONFLICT_ATTEMPT_CEILING` → `>= 64`) | **2 failed** — exactly the two ceiling pins | the discriminating mutation |
| **MU2c** | `:484` ceiling → `7` (the pin's own `_MUTATED_ATTEMPT_CEILING`) | **2 failed**, `"the mutation did not take"` | the pin's own degeneracy self-check fires |
| **MU3** | `:480` `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS` `2.0 → 0.0` | **5 failed** | both paths read the seam's wall clock |

**MU2 deserves a precise statement, because a careless reader would call it a hole.** Changing the
ceiling's *value* leaves the suite green **because the pins read the constant live at assert time**
(`_seam_attempt_ceiling()`), so both sides of the equality move together. The pins therefore guard
the **relationship** — *harness observed attempt count ≡ the seam's current constant* — which is
strictly stronger than pinning a number. MU2b confirms it: sever the predicate from the constant and
exactly the 2 ceiling pins go red, and **only** those (the detection pins correctly stay green — a
mutation that reddens everything proves less than one that reddens the right things).

**Positive controls:** each leg above is paired with the unmutated baseline (`17 passed`), and MU1/MU2b/MU3
each redden a **different, non-overlapping** set — so the instrument demonstrably discriminates rather
than failing globally. MU2c is a control on the controls: it proves the pins detect their own mutation
being a no-op.

## 5. Wrong-build probes — every build the brief named, plus three of mine

Positive control throughout: the correct build = `17 passed`.

| # | wrong build (mutating the HARNESS unless noted) | observed | caught? |
|---|---|---|---|
| **WB1** | ROUTING IS NOT SHARING — calls `retry_on_conflict`, matches its OWN literal `"can be retried"` | **1 failed** (`test_detection_follows_the_seams_one_conflict_marker`) | ✅ |
| **WB2** | routes to the seam, then **also retries locally on top** (3× outer loop) | **5 failed** | ✅ |
| **WB3** | classify **too broadly** — every caught error signalled as a conflict | **2 failed** (incl. `test_propagates_on_first_attempt_without_retrying`) | ✅ |
| **WB4** | **never signals** — `retry_on_conflict` becomes a no-op wrapper, ZERO retries | **6 failed** | ✅ |
| **WB5** | `connect_admin` inlines **three INDEPENDENT budgets** instead of `bootstrap_session` | **17 passed** | ❌ **→ R1** |
| **WB6** | `bootstrap_session` statements **reordered** (`use()` before `DEFINE NAMESPACE`) | **1 failed** (exact-sequence `operations`) | ✅ |
| **WB7** | RULING 1 broken — top-level `_txn` import added to the harness | **1 failed** (the AST pin) | ✅ |

Six of seven caught, **each for a different reason and with a different failure signature** — that is
the "differently-broken build rejected for a *different* reason" control, not one blunt instrument
firing on everything. WB1 reddening exactly one pin (and *not* the bootstrap-path marker pin) is
correct and the builder said so honestly: `connect_admin` goes through `bootstrap_session`, which
uses the seam's classifier directly, so the harness helper is not on that path.

**WB7 also discharges brief item 7** (RULING 1): the AST pin can genuinely fail. I additionally
confirmed the guarantee at runtime — the harness's only module-level `loremaster` import is
`loremaster.index.records`, and all four `_txn` references are in-function
(`_surreal_harness.py:252-254`, `:288`).

## 6. Removed-behaviour enumeration — MINE FIRST, then diffed

Enumerated from `git show 8c96451:loremaster/tests/_surreal_harness.py` before comparing.
⚠ **Frame-contamination disclosure:** my brief required me to read the builder's report, which
contains its §2 table, so my enumeration is not blind. I mitigated by enumerating from the old
source into notes before diffing, but the lead should weight this as *corroboration*, not a truly
independent second enumeration.

| mine | old behaviour | in builder's table? | my verdict |
|---|---|---|---|
| A1 | 5-attempt bound | B1 | agreed — floor 5 preserves it exactly (`_MAX_TXN_CONFLICT_ATTEMPTS = 5`, verified `_txn.py:437`) |
| A2 | linear 10/20/30/40ms backoff, "one waiter" justification | B2 | agreed dropped-deliberately; the justification WAS false under `-n auto` |
| A3 | exhaustion raised engine's `QueryError` | B3 | agreed — **and I re-verified the safety claim independently** (below) |
| A4 | engine text rode on the raised exception | B4 | agreed, IS a regression; `retry_on_conflict:920` raises without `from`, `label=None` so `extra["engine_error"]` is omitted (`_txn.py:909`) |
| A5 | caught `SurrealError` ONLY | B5 | agreed widened to `_CONNECTION_ERRORS` |
| A6 | `use()` outside the retry | B6 | agreed — this was the bug |
| A7 | statement order NS → use → DB | B8 | agreed; `bootstrap_session:1021-1023` issues the identical order, pinned by exact sequence (WB6 proves the pin fires) |
| A8 | `connect_admin` wholly unretried | B7 | agreed |
| A9 | fresh budget per `drop_database` call | B9 | agreed |
| A10 | drift pin = literal equality | B10 | agreed; retirement is correct and its own failure message authorised it |
| **A11** | **NO wall-clock deadline — purely attempt-bounded** | **ABSENT** | **→ R4.** The old loop had no time bound at all. New worst case is time-bounded but ~40× longer. Not adjudicated by the builder. |
| **A12** | **non-`SurrealError` types (`OSError`/`WebSocketException`) propagated unretried even carrying the marker** | folded into B5 | agreed in substance; B5 states the direction correctly |
| **A13** | **`drop_database` never closes the connection if an operation raises** | **ABSENT** | **→ R5.** PRE-EXISTING (identical in old code), but the failure window widens. |

**A3/B3 re-verified independently, not accepted:** I AST-walked every `try` in `tests/*.py` whose body
references `connect_admin`/`drop_database` and enumerated its handlers. **Result: zero handlers — every
one is a bare `try/finally`.** A `try` with no `except` cannot observe a raised-type change. So the
type change from `QueryError` → `TxnContentionExhaustedError` is safe, **and this holds even though the
builder swept the wrong-sized file set (R2).** Corroborated by the identical 61/2698/166 counts in §2.1.

Two builder items I could not fault: B1's floor-5 non-regression argument is exactly right, and B10's
reasoning that a literal-equality assertion is something a private copy satisfies by definition is the
correct justification for retiring that pin.

## 7. RESIDUALS — complete, specific, file:line each

| # | sev | file:line | finding + concrete failure scenario |
|---|---|---|---|
| **R1** | **MED** | `loremaster/tests/test_surreal_harness.py:211` (`TestConnectAdminBootstrapsThroughTheSharedSeam` — the class that should own this) | **No pin requires `connect_admin` to use the COMPOSED budget.** Measured: a build replacing `await bootstrap_session(...)` with three `_run_under_store_retry_seam` calls over the same three statements **passes 17/17** (WB5). It still routes to the shared driver, so every sharing pin stays green — but each statement gets a FRESH `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`. **Scenario:** a future refactor inlines the three statements; under contention `connect_admin` blocks for up to 3×2.0s instead of one composed 2.0s, while holding the connect path, and the property `_txn.py:1004-1013` documents as load-bearing ("three equal deadlines would be three independent budgets wearing a parameter") is silently lost with a green suite. **The seam-side pin exists** (`test_retry_seam.py:6310`) but nothing binds the HARNESS to it. Shipped code is CORRECT — this is a missing pin, not a live defect. Cheapest fix: assert `operations` shows the three statements AND that a zeroed seam deadline yields the floor on the THIRD statement (`_DEFINE_DATABASE`), which an uncomposed build cannot satisfy. |
| **R2** | **LOW-MED** | `loremaster/tests/_surreal_harness.py:24`; `test_surreal_harness.py:572`, `:598`; `test_retry_seam.py:5031` | **"21 test files import this harness" is FALSE — the AST-derived count is 35.** This is not cosmetic: it is the *stated justification* for RULING 1 (the lazy import), so it understates the blast radius by 14 files. It also propagated into the builder's B3 consumer sweep, which claims to have "grepped every importer (21 files)". Repo's own named defect class (PKT-28 C1: wrong counts in served English, no gate). I re-verified the underlying safety claim independently (§6) and it holds — but the number is wrong in committed prose and one site (`:598`) is inside a **failure message**, so a future reader is told the wrong number at the moment the gate fires. |
| **R3** | **LOW** | `loremaster/tests/test_surreal_harness.py:556-566` | `test_the_private_policy_constants_are_gone` **enumerates three FORBIDDEN names** — the exact anti-pattern CLAUDE.md names ("when you catch yourself enumerating what is FORBIDDEN, you have already lost"). A private budget reintroduced as `_TEARDOWN_ATTEMPTS` passes it. **Mitigated, and this is why it is only LOW:** the mutation pins are the real guard — WB2 proved a reintroduced local retry loop reddens 5 pins regardless of what it is named. Defence-in-depth, not the primary instrument. |
| **R4** | **LOW** | `loremaster/tests/_surreal_harness.py:306-320`, `:337-350` | **Worst-case teardown wall-clock widens ~40×, unadjudicated (my A11).** Old bound: 5 attempts, linear 10+20+30+40ms ≈ **100ms**, no time bound. New bound: the seam's 2.0s deadline **per operation**, and `drop_database` drives TWO seam operations (`use()` + `REMOVE`) ⇒ up to **~4s**, plus `connect_admin`'s composed 2.0s. Teardown runs on EVERY `[real]` test under `-n auto`. Not a defect (a loud bounded failure beats a silent one) and the builder's B1/B2 verdicts are right — but the wall-clock consequence is nowhere stated, and it is the kind of number that surfaces later as "the suite got slower". |
| **R5** | **LOW** | `loremaster/tests/_surreal_harness.py:337-350` | **`drop_database` leaks its connection on failure** — no `try/finally` around `_select_database`/`_remove_database_with_retry`, so `await connection.close()` (`:350`) is skipped if either raises. **PRE-EXISTING** (byte-identical shape in the old code) so NOT introduced here, but the window widens materially: `use()` used to fail on attempt 1 and now retries up to the seam's budget while holding the socket. Under `-n auto` a contended teardown storm leaks one socket per failure. |
| **R6** | **LOW** | `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md:414` | Describes `_MAX_DROP_DATABASE_ATTEMPTS = 5`, `linear backoff 0.01s * attempt`, "unjittered (one waiter)" as LIVE. All four claims now false. Builder flagged this as E2 and declined to touch it (outside writable set) — **I agree with surfacing it and agree it is the lead's call**: it is a dated historical receipt, and rewriting history has its own cost. Recommend a one-line superseded-by-#150 stamp rather than an edit. |
| **R7** | **LOW** | `docs/plans/v2/INDEX.md:413` | Reads "eleven hand-rolled copies deleted" for the #102 chain. #150 deletes a **twelfth** (the harness) — the very copy `test_retry_seam.py`'s retired 7e block called "THE TWELFTH COPY". Not wrong as a dated #102 record, but the lead may want the INDEX Log line for #150 to say so explicitly, or the count reads as final when it is not. |
| **R8** | **INFO** | `_surreal_harness.py:239`, `:301` (builder E1); `scratchpad/102-recovery/probe_sequence_txn_concurrency.py:4` (builder E3) | I confirm both. `signin()` is a bare unretried `await` at both sites — correctly NOT wrapped (auth is not conflict-class; the seam's classifier would decline it, so wrapping would be routing-without-purpose), but it is a bare await in the two functions just hardened. The scratchpad probe cites the deleted constant; untracked, ungated, informational only. |

**False-gate hunt (brief item 5) — result: one gap, R3.** I compared every new assertion against its
own failure message. All five `TestTheHarnessRetryPolicyIsTheSeamsPolicy` messages promise exactly what
their assertions check (attempt-count equality against a live-read seam constant — no "non-increasing"
style weakening of the kind that shipped here in P2). The single gap is R3, where the message promises
"the harness owns NO retry policy" while the assertion checks three enumerated names.

## 8. Bare, anchor-free grep sweep — every residual hit, individually

Patterns run with no prefix/paren anchors across the whole repo (excluding `.git`, `.venv`,
`__pycache__`). **Per-hit verdicts; no wholesale classification.**

`_RETRYABLE_CONFLICT_MARKER` — 24 hits:
- `_txn.py:409` **CORRECT** — the canonical definition. · `:620`, `:626`, `:630`, `:641`, `:688`, `:1164` **CORRECT** — the seam's own docstrings/uses.
- `test_retry_seam.py:271`, `:275`, `:3549` **CORRECT** — seam-side pins, monkeypatch the seam.
- `test_surreal_store.py:83` **CORRECT — imports it from `loremaster.store._txn`, NOT the harness** (verified at source, `:76-86`). Same for `:2177`, `:2235`, `:3842`.
- `test_txn_contention.py:79` **CORRECT — imported from `loremaster.store._txn`** (verified `:78-84`); `:102` uses it.
- `test_surreal_harness.py:58` **CORRECT** — comment correctly attributing the marker to the seam; `:491`, `:524` monkeypatch the SEAM's attribute; `:558` names it as a RETIRED name (the point of the pin).
- `docs/.../REPORT-recon-pkt03.md:128` **STALE-BUT-HARMLESS** — describes the seam's classifiers accurately; the `_RETRYABLE_CONFLICT_MARKER (:409)` citation is still correct.
- `scratchpad/102-recovery/DESIGN-102-addendum-2026-07-12-…md:42`, `DESIGN-102-addendum.md:161`, `DESIGN-102-final.md:85` **INFO** — untracked scratchpad design docs, describe the seam (not the harness), still accurate.
- `scratchpad/102-recovery/probe_sequence_txn_concurrency.py:4` **STALE** → R8.
- `REPORT-harness-retry-builder.md:56,178,296` **CORRECT** — the builder's own report describing the deletion.

`_MAX_DROP_DATABASE_ATTEMPTS` — 5 hits: `test_surreal_harness.py:558` **CORRECT** (retired-name pin) ·
`docs/.../REPORT-recon-pkt03.md:414` **STALE** → R6 · `REPORT-harness-retry-builder.md:56,77,289`
**CORRECT** (builder's report). **Zero live code hits.**

`_DROP_DATABASE_BACKOFF_SECONDS` — 2 hits: `test_surreal_harness.py:558` **CORRECT** (retired-name pin) ·
`REPORT-harness-retry-builder.md:57` **CORRECT**. **Zero live code hits.**

`_remove_database_with_retry` — 5 hits. ⚠ **This name is NOT retired** — the function still exists,
rewritten to delegate: `_surreal_harness.py:306` **CORRECT** (definition), `:295` **CORRECT**
(`_RemovableDatabaseConnection` Protocol docstring, still accurate), `:349` **CORRECT** (call site) ·
`docs/.../REPORT-recon-pkt03.md:414` **STALE** → R6 · `REPORT-harness-retry-builder.md:50` **CORRECT**.

**Runtime confirmation** that the three retired constants are genuinely gone (not merely un-grepped):
`hasattr(_surreal_harness, …)` → `False, False, False`; module resolved to
`/home/ejprice/PycharmProjects/lore/loremaster/tests/_surreal_harness.py`.

**Prose claims verified against code:** "SINGLE classify-and-signal site" ✅ (exactly one, `:261-262`).
"harness owns NO retry policy" ✅ (runtime + grep). "`connect_admin` bootstraps through
`bootstrap_session`" ✅. "6.2%–34.4% of virgin first-connects lost" ✅ — matches CLAUDE.md's measured
range and correctly quotes it as a RANGE with its protocol, not a point estimate. "21 test files" ❌ → R2.

## 9. Tree provenance and restoration

Per repo law #140 I made **no `cp -a` copy of the repo** — all mutations ran in the real, committed
checkout with `cp -a` **content** backups at `/tmp/audit150-backup/`. Provenance receipt:

```
loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
```
(the real tree, which is the tree I intended to grade — the always-sound alternative the law names).

Pre-audit md5s, re-proven after **every** mutation and at the end:
```
e67978f0dc474af17079ed9ee0c5cb1a  loremaster/loremaster/store/_txn.py
0d60e5158653a7bacb19548c373015fe  loremaster/tests/_surreal_harness.py
$ diff /tmp/audit150-backup/_txn.py …            → BYTE-IDENTICAL
$ diff /tmp/audit150-backup/_surreal_harness.py … → BYTE-IDENTICAL
$ git status --short
?? REPORT-blindreader-150.md      (another agent's file — NOT touched)
?? REPORT-harness-retry-builder.md
?? scratchpad/
$ git diff --stat HEAD            → (empty)
```
Final re-green after all restoration: **420 passed, 1 warning in 11.18s.**

Nothing was fixed, edited, staged, committed or reverted. 9 mutations applied, 9 restored, each proven
by content diff rather than by `git status` alone.

---

## VERDICT: **GO**

The claim survives refutation. Production drift is byte-zero; the sharing is real and
mutation-proven on both paths by my own instruments; the contract genuinely fails 13/4 on the unfixed
build; six of seven wrong builds I constructed are caught, each for a distinct reason; zero consumer
regressions against a measured baseline; the RED floor did not grow.

**Not blocking, but the lead should rule on two things before this is considered closed:**
1. **R1** — the missing composed-budget pin. The code is right; nothing keeps it right. This is the
   one place where "what wrong build would this still pass?" returned a real answer.
2. **R2** — the 21-vs-35 count, in four committed sites, one of them a failure message. Cheap to fix,
   and it is the repo's own most-repeated defect class.

R4/R5 are pre-existing or capacity notes rather than defects in this diff, but neither was adjudicated
and R5 in particular gets worse *because* of this change.
