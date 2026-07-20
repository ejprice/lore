# REPORT-audit-150-final — cold REFUTE audit of the #150 fix waves 2 & 3

brief-base v5 read

## SUMMARY BLOCK

- **VERDICT: GO** — with 5 residuals, none blocking. Every load-bearing new pin is
  mutation-proven by me and discriminates; zero production drift; all gates reproduced.
- **state:** done
- **blockers:** none
- **residual count:** 5 (2 MEDIUM, 2 LOW-MED, 1 LOW) — §7 is the substantive section
- **deviations:** none. Report-only honoured; every mutation reverted and proven byte-exact (§8).
- **decisions-needed:** R1 (the test-tree gate misses 7 of 9 natural receiver names — fix now
  or ledger as a pinned bound?) and R3 (a false claim in a committed doc stamp).
- receipts: gates §1 · drift §2 · mutations §3 · gate attack §4 · counts §5 · sweep §6 · residuals §7

---

## 1. Gates, re-run independently (passed-COUNTs in every tail)

| gate | command | result |
|---|---|---|
| harness + seam | `uv run pytest loremaster/tests/test_surreal_harness.py loremaster/tests/test_retry_seam.py -q -n auto` | **453 passed, 1 warning in 7.90s** |
| live store (11 files, spike-surreal :18000) | `uv run pytest test_surreal_store test_txn_contention test_store_read test_task_ledger test_findings test_agent_registry test_brief_ledger test_snapshots test_surreal_manifest test_surreal_apply test_graph_surreal -q -n auto` | **1181 passed in 34.60s** |
| mypy | `./scripts/typecheck.sh` **from repo root** | **Found 55 errors in 5 files (checked 146 source files)** |
| ruff | `uv run ruff check .` from repo root | **All checks passed!** |

- The 55 mypy errors are entirely `test_comms_tool.py` / `test_comms_promise_registry.py` /
  `test_message_ledger.py` (packet-03 comms contract). **Zero errors in the three changed
  files** — grep for `_surreal_harness|test_surreal_harness|test_retry_seam` over the mypy
  output returns nothing. Floor did not grow.
- I ran the live suite broader than the lead's 200-test set (1181 passed). Fully green.
- ⚠ I confirm the lead's `typecheck.sh` warning independently: piping the run swallows the
  exit code (`MYPY_EXIT=0` despite `typecheck: one or more members failed`). The **count
  line** is the only honest signal; a bare exit-code check behind a pipe reads as a pass.

## 2. Production drift — verified by CONTENT, not by `git status`

```
git diff --name-status 8c96451..HEAD -- loremaster/loremaster/   -> (empty)
git ls-tree -r 8c96451 -- loremaster/loremaster/ | md5sum        -> 262803a90c6532e9a13a9fd3cffdb336
git ls-tree -r HEAD     -- loremaster/loremaster/ | md5sum       -> 262803a90c6532e9a13a9fd3cffdb336
```
File set identical; **blob-hash tree identical**. Zero production drift, established by content.

## 3. Mutation proofs — I broke each guard myself and watched it redden

All four applied to the **real tree** (committed + clean, per repo law #140 — no `cp -a`
scratch copy, so no `.pth`/`__pycache__` provenance poisoning), with a `cp -a` content
backup at `/tmp/audit150_backup/` and md5 restore proof after each.

| # | mutation | target pin | observed |
|---|---|---|---|
| **M1** | `connect_admin` rebuilt as the auditor's wrong build — three **independent** `_run_under_store_retry_seam` calls instead of `bootstrap_session` | `test_connect_admins_three_statements_share_one_budget` | **RED.** `assert 64 == 5` — "attempted 64 times … A caller that COMPOSES leaves it the attempt floor (5); 64 means it was handed a FRESH budget". **This is the exact build that previously passed the contract 17/17.** Now caught. |
| **M2a** | module-level `try: from loremaster.store._txn import … except ImportError:` added to the harness | `test_the_module_level_imports_stay_confined_to_the_sdk_and_records` | **RED.** `assert not ['loremaster.store._txn']`. This shape passed **GREEN** before the `tree.body`→`ast.walk` repair. |
| **M2b** | `_TEARDOWN_MAX_ATTEMPTS = 7` — a **differently-named** private budget | `test_the_harnesss_module_level_names_are_exactly_the_allowed_set` | **RED.** And the three retired-name deny-list legs stayed **GREEN** — a clean demonstration that the deny-list could not see it and the allowlist can. Item 5 repaired as claimed. |
| **M3** | `_txn.bootstrap_session` given a `label=` (i.e. the #151 hole CLOSED) | `test_the_bootstrap_paths_exhaustion_is_UNATTRIBUTED_a_known_bound` | **RED.** It is a real tripwire, not decoration — it fires on the exact re-open trigger its docstring names. |
| **M4** | harness issues a new engine op (`INFO FOR DB`) with no probe | `test_every_operation_under_the_seam_has_a_constant_tied_probe` | **RED.** Reach is genuinely a checked variable. |

**Reach pin (item 7) verified in both directions:** `_OPERATION_PROBES` holds all 5 retried
operations (`connect_admin:{DEFINE NAMESPACE,use,DEFINE DATABASE}`, `drop_database:{use,REMOVE
DATABASE}`); each is parametrised through both the attempt-ceiling and wall-clock-deadline
mutation legs, each carrying its own positive-control leg at the unmutated value. M4 proves the
set is enforced, not decorative.

**Positive controls throughout:** every mutation above was paired with the unmutated run
(453 passed) so each probe is shown able to be green; M1/M2/M4 each additionally left the
sibling pins green, so the reds are attributable rather than blanket.

## 4. Attacking the wave-3 bootstrap gate (item 4)

**What it gets right** — genuinely strong, and I could not break these:

- **Site-count allowance FIRES.** I added a second `connection.use()` to the allowlisted
  `_surreal_harness.py`: `test_every_allowance_still_holds_exactly_the_sites_it_was_granted`
  went **RED** — `assert 2 == 1`, with the reason text and both "if you ADDED / if you REMOVED"
  branches. It is not a blanket file exemption. This closes the failure mode the section names.
- **No false positives.** Execution-keyed scan over all 92 test modules yields **exactly 1
  site**. Fakes that merely `async def use(...)` are untouched (`FunctionDef` ≠ `Call`), and
  22+ `DEFINE NAMESPACE` fixture strings are correctly read as data. The negative-control
  and DATA-fixture pins exist and pass.
- **Reach control** (`≥60` of 92 modules, `_surreal_harness.py` and `test_retry_seam.py`
  explicitly asserted present) is real and would catch a broken walk.

**What I broke — R1, below.** The gate is keyed on receiver NAME. Same honest-engineer
bootstrap, only the variable name varied:

```
receiver name    sites   verdict
connection       3       CAUGHT
conn             3       CAUGHT
self._connection 3       CAUGHT
db               0       *** MISSED ***
client           0       *** MISSED ***
surreal          0       *** MISSED ***
session          0       *** MISSED ***
handle           0       *** MISSED ***
store            0       *** MISSED ***
_connection      0       *** MISSED ***   <-- see R1b
```

**Demonstrated end-to-end, with a positive control.** I wrote a real test file
(`test_zz_honest_helper.py`) containing a textbook #131/#150-shaped helper — opens a socket,
signs in, hand-rolls `DEFINE NAMESPACE` / `use()` / `DEFINE DATABASE`, never heard of
`bootstrap_session` — and ran the gate twice, changing **only the variable name**:

```
--- receiver named 'db' ---          1 passed, 409 deselected   <-- the gate does not see it
--- receiver named 'connection' ---  1 failed, 409 deselected   <-- the gate sees it
```

(temp file removed; `ls` confirms absent.)

**Judged by the pin's own stated standard** (which I take as binding, and which is a genuine
strength of the section — it made this verdict mechanical rather than a matter of taste):

> * "a determined author could evade this" → NOT a defect. Out of model.
> * "an honest engineer's hand-rolled bootstrap in a test helper goes unnoticed" → A DEFECT.

An engineer who names a SurrealDB handle `db` is not evading anything. **This is the second
bullet, so by the instrument's own spec it is a defect** — see R1. I want to be explicit that
the threat-model block is what let me reach that verdict cleanly, and that the bound *is*
disclosed in `_is_connection_receiver`'s docstring; the problem is that the block asserts a
standard the predicate does not meet, and the two are ~40 lines apart.

## 5. Independent count derivation (item 9)

Derived with my own AST script, not the suite's helpers and not anyone's number:

```
total test modules          : 92
files IMPORTING the harness : 35
files CALLING connect_admin : 22  (21 excluding _surreal_harness.py itself)
callers not importers       : ['_surreal_harness.py']
```

Cross-checked a second way: my independent enumeration of `connect_admin` callers for the
live-store run returned **21 files** — matching.

- **35 importers: CORRECT** at `_surreal_harness.py:24`.
- **21 callers: CORRECT** at `_surreal_harness.py:26` — under the definition
  `_test_files()` encodes (`p != harness`, i.e. excluding the harness itself). The harness
  *does* call `connect_admin` (`:542`, `:559`), so the tests-tree-wide figure is 22. Both
  numbers are honest under a consistent, code-embodied definition. See R5 for the precision nit.
- **Stated distinctly at all four sites: YES** — `_surreal_harness.py:24/26`,
  `test_surreal_harness.py:1338-1339`, `test_retry_seam.py:5380`. All corrected; the two
  populations are named separately at each.
- The pin `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` re-derives both and
  additionally asserts `set(callers) < set(importers)` (strict subset), so it cannot pass by
  the two populations collapsing. Good discrimination.

## 6. Bare, anchor-free sweep — every residual hit, individually verdicted

No "all remaining hits are X" anywhere below. `REPORT-*.md` at repo root excluded as
untracked scratch.

**`_RETRYABLE_CONFLICT_MARKER`**
- `loremaster/loremaster/store/_txn.py:409` — **CORRECT**, the live production constant.
- `_txn.py:620,626,630,641,688,1164` — **CORRECT**, docstrings/uses of that live constant.
- `loremaster/tests/test_txn_contention.py:79,102` — **CORRECT**, imports the production
  constant from `_txn` (not a harness copy).
- `scratchpad/102-recovery/DESIGN-102-final.md:85` — **STALE, UNTRACKED.** Scratchpad, not shipped.
- `scratchpad/102-recovery/DESIGN-102-addendum.md:161` — **STALE, UNTRACKED.** Same.
- `scratchpad/102-recovery/DESIGN-102-addendum-…-capabilities.md:42` — **STALE, UNTRACKED.** Same.
- `scratchpad/102-recovery/probe_sequence_txn_concurrency.py:4` — **STALE, UNTRACKED.**
  Docstring says `_surreal_harness._RETRYABLE_CONFLICT_MARKER`, which no longer exists. Not
  executed by any gate. Flagged, not fixed (outside writable set).

**`_MAX_DROP_DATABASE_ATTEMPTS`**
- `loremaster/tests/test_surreal_harness.py:1222` — **CORRECT**, the retired-name pin's parameter.
- `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md:414` — **STALE BUT NOW
  STAMPED.** Superseded banner added directly beneath by 5bd1078. Correct handling.
- `REPORT-recon-pkt03.md:418` — **CORRECT**, inside the new superseded stamp itself.

**`_DROP_DATABASE_BACKOFF_SECONDS`**
- `test_surreal_harness.py:1223` — **CORRECT**, retired-name pin parameter.
- `REPORT-recon-pkt03.md:418` — **CORRECT**, inside the stamp.

**`_remove_database_with_retry`**
- `loremaster/tests/_surreal_harness.py:352,363,445` — **CORRECT**, the function is LIVE.
- `loremaster/tests/test_surreal_harness.py:1062` — **CORRECT**, references the live function.
- `REPORT-recon-pkt03.md:414` — **STALE, STAMPED** (line numbers in it are stale, banner covers it).
- `REPORT-recon-pkt03.md:419` — ❌ **FALSE — this is R3.** The new stamp claims this function
  "were **deleted**". It exists and is live (verified by import: `hasattr → True`).
- ⚠ Note: **`_remove_database_with_retry` is not a retired name at all** — the brief lists it
  among the retired names, but the function was kept. Flagging the brief's own premise.

**`21 test files`** (the false-count claim)
- `_surreal_harness.py:26` — **CORRECT** (now scoped to the `connect_admin` population).
- `test_surreal_harness.py:1338` — **CORRECT**, quotes the false claim as history, immediately
  corrected on :1339.
- No other tracked-file hits. The retired claim is fully swept from committed prose.

## 7. RESIDUALS — the substantive section

| # | sev | file:line | finding + concrete failure scenario |
|---|---|---|---|
| **R1** | **MED** | `loremaster/tests/test_retry_seam.py:1794-1806` (`_is_connection_receiver`), consumed by the test-tree gate at `:4881-4916` | **The test-tree bootstrap gate misses an honest engineer's bootstrap whenever the connection variable is not named `connection`/`conn`/`*connection`.** Measured: 7 of 9 natural names sail through (`db`, `client`, `surreal`, `sdb`, `session`, `handle`, `store`). **Failure scenario:** an engineer adds `tests/_pkt04_harness.py` with `db = AsyncSurreal(url); await db.query(f"DEFINE NAMESPACE …"); await db.use(ns, name)` — the literal #150 construct, unretried, racing on virgin first-connects at 6.2%–34.4% — and the suite is green. This is #150 recurring in the exact file class the gate was built for. **Crucially: the PRODUCTION gate catches this same code** (its DDL-literal leg is receiver-blind: I ran it, 1 site found) — the narrowing to execution-keying dropped that safety net, so the test tree is now strictly weaker than production on the population that has actually failed. Also note repo law: packet 01 spent three waves learning that receiver-name keying loses, and the operator's settled reframe was *receiver-blind deny + allowlist the safe*; this instrument has the allowlist half (good, and it works — §4) but re-adopted receiver-name keying for the deny half. **Recommendation:** make the DDL leg receiver-blind for the test tree too (a `.query(...)`/`.execute(...)`-shaped call carrying `DEFINE NAMESPACE`/`DEFINE DATABASE` on *any* receiver) and let the one-row allowlist absorb the fallout — measured cost is likely small since the tree's DDL literals are mostly bare strings, not call arguments. **If instead this bound is accepted, it needs a pin + named re-open trigger** ("when you cannot close a hole, PIN IT"), because today it is only a docstring sentence 3000 lines from the gate. **Operator's call.** |
| **R1b** | LOW-MED | `test_retry_seam.py:1804-1806` | **The receiver predicate is internally inconsistent:** `self._connection` (an `ast.Attribute`, matched by `.endswith("connection")`) is caught, but a plain local named `_connection` (an `ast.Name`, tested against `frozenset({"connection","conn"})`) is **missed**. **Failure scenario:** `_connection = AsyncSurreal(url); await _connection.use(ns, db)` — an entirely idiomatic private-local naming — evades both scans. One-line fix: add `_connection` to `_CONNECTION_NAMES`, or test `node.id.endswith("connection")` symmetrically with the attribute leg. Independent of R1's design question and cheap either way. |
| **R2** | **MED** | `test_retry_seam.py:4831-4833` and `:4839-4840` | **A false count, committed by the commit that fixed a false count.** The comment states the production scan over the test tree "reports **23** sites, **22** of them correct code" and "Twenty-two fixture strings". I measured **31** sites at HEAD. I then measured it at `9d4b48d~1`: **23 — it was TRUE before wave 3 and falsified by wave 3's own commit**, which added ~8 new `DEFINE NAMESPACE` control fixtures to this very file. **A self-invalidating measurement: the author measured honestly, then the act of committing changed the answer.** **Failure scenario:** a future engineer sizing the false-positive trade reads "23 sites, 22 data", re-runs it, gets 31, and cannot tell whether the instrument drifted or the tree did. This is the repo's named trap (un-derived count in served English) and the direct sibling of what `fff1382` fixed 3 commits earlier — but unlike the harness docstring counts, **these numbers are in a comment with no derivation pin**, so nothing can ever catch them. **Recommendation:** either derive them (the machinery exists — `_bootstrap_sites_in` is right there, and `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` is the template) or drop the numerals and keep the qualitative claim. |
| **R3** | LOW-MED | `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md:419` (commit `5bd1078`) | **The superseded stamp asserts a function was deleted that is alive.** It lists "`_remove_database_with_retry` itself were **deleted**". The function exists at `_surreal_harness.py:363`, is called at `:445`, and imports live (`hasattr → True`). Its three siblings in that sentence *were* genuinely deleted, so the claim is 3-of-4 true. **Failure scenario:** a reader greps for the harness teardown path, hits the stamp, believes the function is gone, and is confused by finding it — precisely the mis-navigation the stamp was written to prevent. **Aggravating:** the prior cold audit had already flagged this exact name (`REPORT-audit-150-cold.md:217`: "⚠ **This name is NOT retired** — the function still exists"). The residual was read past — the repo's own named failure mode of acting on a summary and skipping the residuals table. The stamp's other claims (four constants dead, seam routing, **jitter** — I verified `_txn.py:751-776` is full-jitter `random.uniform(0, window)`) are all TRUE. One-word fix. |
| **R4** | LOW | `test_retry_seam.py:4842-4846` | **A FALSE GATE of exactly the class item 6 hunts: the prose promises a check the suite does not perform.** The comment states both scans share `_is_connection_receiver`, `_SESSION_SELECT_METHOD` **and** `_BOOTSTRAP_DDL_KEYWORDS`, then: *"Mutate one and BOTH scans change … That mutation is not an argument here; **it is executed, below.**"* Only **one of the three** is executed — I grepped every `setattr` in the block: `_SESSION_SELECT_METHOD` alone (`:5117`). `_BOOTSTRAP_DDL_KEYWORDS` and `_is_connection_receiver` are never mutated anywhere in the file. **Failure scenario:** a future edit gives the test-tree scan its own DDL keyword tuple (or its own receiver predicate); the two scans silently drift; every pin stays green, and the comment tells the reviewer that case is covered. Two more asserts in the existing test body close it. |
| **R5** | LOW | `loremaster/tests/_surreal_harness.py:363` / the known-bound pin at `test_surreal_harness.py:578-614` | **The #151 known-bound pin never names #151.** Its docstring cites "blindreader-150 F1" and "audit-150" — both **untracked scratch reports at the repo root**, which repo law requires be *deleted before any image build*. `grep -rn "#151"` over the whole repo returns **zero hits**. I confirmed via `lore_findings` that #151 exists and is open with an excellent body. **Failure scenario:** the reports are deleted (as required), the pin fires, and its stated re-open trigger cites a file that no longer exists — while the durable ledger row that *does* survive is unreachable from the code. The pin is otherwise excellent and mutation-proven (M3). One-line fix: add `#151` to the docstring. **Same pattern is worth a broader look:** committed test prose across this wave cites `audit-150 R*` / `blindreader-150 F*` repeatedly; those are all non-durable addresses. |

**Minor, sub-residual (noted, not tabled):** the harness docstring's "21 test files — calls
`connect_admin`" is true only under the harness-excludes-itself definition; the tests-tree-wide
figure is 22. Defensible and code-embodied, but a reader could take it either way.

## 8. Restore proof — every mutation reverted

```
git status --short        -> only the 5 untracked REPORT-*.md + scratchpad/ (pre-existing)
md5sum -c BASELINE.md5    -> _surreal_harness.py: OK
                             test_surreal_harness.py: OK
                             test_retry_seam.py: OK
md5sum -c TXN.md5         -> loremaster/loremaster/store/_txn.py: OK
git rev-parse --short HEAD -> 9d4b48d
temp file test_zz_honest_helper.py -> absent
```
`_txn.py` untouched at HEAD; finding #151 left deliberately open per operator ruling.
Content backups retained at `/tmp/audit150_backup/` (not md5 lists — actual content, per the
2026-07-14 near-miss law).

## 9. Claims I could NOT reproduce

None. Every claim in `REPORT-harness-retry-fixwave.md` and `REPORT-bootstrap-gate-reach.md`
that I tested reproduced, **except** the two counts in R2 (which reproduced at the parent
commit and not at HEAD) and the deletion claim in R3 (which is simply false). The lead's own
figures (453 / mypy 55-in-5 / ruff clean / zero prod drift) all reproduced exactly.

## 10. Verdict

**GO.** The three in-scope commits do what they claim. The composed-budget defect is really
fixed and the wrong build that beat the first contract 17/17 is now reliably RED; the AST
repair genuinely catches the `try:`-wrapped import that used to pass; the deny-list→allowlist
conversion is real and the deny-list's blindness is demonstrable; the reach pin is enforced in
both directions; the socket-leak `try/finally` is present on both paths; the #151 bound is a
true tripwire; and the counts are correct and now pinned. Zero production drift, all gates
green, 1181 live-store tests passing.

The wave-3 gate is a net improvement — it closes a real class of blindness with an allowlist
whose site-count actually fires — but **R1 means it does not yet meet the standard its own
threat-model block sets**, and R2/R4 are two instances of this repo's most-named defect class
(unpinned prose that overstates what the code checks) shipped inside the wave that was fixing
that class. None of these five make the committed work wrong; all five are cheap to close, and
R1 is the one I would not leave open, because the gate's whole purpose is to stop #150 from
recurring in the test tree and today an ordinary variable name walks past it.

**Scope note:** R1's fix is a design question (what predicate replaces receiver-name keying),
not a mechanical one — by repo routing law that escalates rather than going to a builder.
