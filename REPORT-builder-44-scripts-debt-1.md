# REPORT-builder-44-scripts-debt-1

brief-base v9 read
brief project v7 read
brief pkt44 v1 read

- **state:** done-with-deviations
- **deviations:**
  1. HEAD MOVED UNDER ME mid-run — the lead committed `cc0105d` believing I had died to an API 500, sweeping up 4 of my finished working-tree files. No damage; its message is accurate. My remaining commits build on it. §F1
  2. I CAUSED ONE REAL TEST FAILURE and self-reverted it: `SecretStr("unused")` broke the S6 credential-origin pin. Fixed by NOT weakening the pin; the arg-type error now carries a narrow, documented `# type: ignore[arg-type]`. §D1 — **read this one**
  3. Commit split is 4, not the suggested 3 (a regression-fix commit inserted). Three files carried both type and prose edits; split via a temporary revert, byte-exactness proved by md5. §F2
- **Packages considered:** none — no mechanism specified. This wave adds no mechanism: every change is an annotation, an `__all__` entry, a comment, one mypy config override, and one `MEMBERS`/`MYPYPATH` entry reusing the runner's EXISTING per-root mechanism (`docs/eval`, #261) rather than inventing a second one — which was itself the packages-over-hand-rolling rule applied in-repo.
- **decisions-needed:**
  1. ~~loresigil widening~~ — **GRANTED (R7) and DONE**; cast deleted, comment corrected. §D2
  2. **Does `scripts/comms_consumer_eval.py` join the S6 mint-origin allowlist?** Expands a SECURITY allowlist ⇒ operator ruling. **Still open.** §D1
  3. **`scripts/test_forgery_door_sweep.py::TestThisInstrumentIsTYPECHECKED` is now REDUNDANT** and asserts a false claim. Peer-owned, untouched. LEDGER item. §C4
  4. **3 known-false prose sites** outside my writable set, verbatim edits ready. §C2
- **receipts:** measurement §A · fixes §B · prose sweep w/ per-hit verdicts §C · forks §D · gates + mutation proof §E · git §F · **loresigil R7 §H**

---

## A. THE MEASUREMENT — RE-DERIVED, NOT INHERITED

Re-derived at `f033a87` over `git ls-files 'scripts/*.py'`. **Reproduces the lead's brief exactly; no drift, nothing to STOP for.**

```
uv run mypy <tracked scripts/*.py>              ->  45 errors in 7 files
MYPYPATH=scripts uv run mypy <the same files>   ->  24 errors in 7 files
```

Distribution of the 24 — identical to the brief, file for file:

| n | file |
|---|---|
| 8 | `scripts/survey_txn_contention_102.py` |
| 6 | `scripts/test_search_score_survey.py` |
| 5 | `scripts/comms_consumer_eval.py` |
| 2 | `scripts/search_score_survey.py` |
| 1 | `scripts/test_snapshot_gc.py` |
| 1 | `scripts/test_scratch_copy.py` |
| 1 | `scripts/test_calibration_baseline.py` |

**The 21-error gap is import-resolution artifact, not debt.** `scripts/` is not a package; its modules import each other as top-level names behind the house `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` idiom — **11 sites**, derived by `git grep -n 'sys.path.insert' -- 'scripts/*.py'`. That resolves at runtime and is invisible to mypy from the repo root under `explicit_package_bases`.

### A.1 — THE INHERITED "41" WAS A THIRD NUMBER, TRUE UNDER NEITHER SHAPE

Finding #188's own acknowledgement note (2026-07-26) recorded `uv run mypy scripts/` → *"41 errors in 6 files (**14 source files checked**)"*. Today's tracked set is **19 files**. So 41 / 45 / 24 differ on **two axes at once — invocation shape AND file set**. Any of the three quoted without both is a rumour. This is precisely why #188 made a re-measure its named decision point, and it is the second time in this packet that an inherited count has failed to reproduce.

The scope call that note made from the wrong number was nonetheless **correct**: not a drive-by, and "do the config half first — it likely collapses a large fraction" predicted the 21 exactly.

---

## B. THE 24 FIXES — NO BEHAVIOUR CHANGED

That constraint is load-bearing: `comms_consumer_eval.py` was packet 03b's ACCEPTANCE AUTHORITY, and `survey_txn_contention_102.py` / `search_score_survey.py` are measurement instruments whose numbers this repo's law cites. **A type fix that moves a measured number is a defect, not a fix.** Every change below is an annotation, an `__all__` entry, a comment, or a parameter rename that only widens compatibility. **No expression, no control flow, and no constant was altered.**

### B.1 `survey_txn_contention_102.py` — 8 errors, one root cause *(landed in `cc0105d`)*
`AsyncSurreal` was used as a **type**. It is a **factory function**, not a class — `def AsyncSurreal(url: str) -> Union[AsyncEmbedded… | AsyncHttp… | AsyncWs…]` (read in the installed SDK, `surrealdb/__init__.py`). Hence `valid-type`, and every attribute read off the result then reported missing.

Fixed with the **house alias `loremaster.store._txn::_SurrealConnection`** — the factory's exact return union, whose own comment says *"this alias is exactly its return union so a cached connection type-checks under strict"*. **The file already imported it and already used it one line away** (`_acquire() -> _SurrealConnection`). Annotations only.

### B.2 `search_score_survey.py` + `test_search_score_survey.py` — 8 errors, one root cause
`__all__ = ["query_tokens"]` omitted the module's **two sibling re-exports**. Under `no_implicit_reexport` (part of `strict`) an aliased import (`_x as y`) is **not** an export, so all six `sss.<name>` reads in the contract were `attr-defined`.

The narrowness was an accident of a different tool: the list had been written for **ruff's unused-import rule**, which the other two names did not trip because the module uses them internally. The module's own comment already claimed all three were re-exported, and `TestPredicateParityWithProduction` already pinned all three by identity — **the declaration was the only thing lagging.** `__all__` affects `import *` alone; nothing imports `*` from it.

Also: `_make_embedder` annotated `-> Embedder` (was a blanket `# type: ignore[no-untyped-def]`).

### B.3 `comms_consumer_eval.py` — 5 errors
- **2× `no-any-return`** (`_render_helper`, `_grader`): annotated the `getattr` local (`Callable[..., Any] | None`, `Grader | None`); the pre-existing `is None` guard then narrows. No cast.
- **`_query` stand-in parameter names** aligned to `AgentRegistry._query(self, statement, params)`. mypy reported the mismatch as `[assignment]` — **an error code the existing `# type: ignore[method-assign]` never covered**, which mypy said out loud in a `note` that had simply never been read. All 5 production call sites pass positionally (verified), so this only widens compatibility.
- **`password="unused"`** → see **§D1**. This is the one that bit.
- **`import anthropic`** → see **§B.4**.

### B.4 THE ONE MYPY OVERRIDE ADDED — SAID LOUDLY, AS INSTRUCTED

```toml
[[tool.mypy.overrides]]
module = ["anthropic", "anthropic.*"]
ignore_missing_imports = true
```

House shape (matches `kubernetes` / `networkx`, which are also *absent*-module cases; `astroid` uses `follow_untyped_imports` because it is present-but-untyped). Committed with ~15 lines of reason and a named re-open trigger.

**VERIFIED, NOT ASSUMED (2026-07-29):**
- `git grep -nI 'anthropic' -- '*.toml'` → **zero hits.** It is in no dependency group.
- `ls .venv/lib/python3.14/site-packages/anthropic` → **absent.**
- The overlay decision is ruled and archived: `docs/plans/v2/receipts/2026-07-25-packet03b/REPORT-eval-author-03b-1.md` §D — chosen so the one surface that talks to a paid API stays out of every developer's and every container's dependency closure.
- The import is **already guarded**: `AnthropicConsumerClient.__init__` catches `ImportError` and re-raises naming the exact `uv run --with` line.

**Blast radius:** one class, one script. Nothing served is typed by it.
**Re-open trigger:** if `anthropic` ever becomes a real dependency, **DELETE the block** rather than keep both.

### B.5 Three redundant `# type: ignore[import-not-found]` *(landed in `cc0105d`)*
`test_snapshot_gc.py`, `test_calibration_baseline.py`, `test_scratch_copy.py` — compensating for the missing MYPYPATH. Deleted. **Consequence for hand-runners:** a bare `uv run mypy scripts/…` on these now errors. Documented in `typecheck.sh` in the same shape as the existing `docs/eval` hand-runner note.

---

## C. THE PROSE SWEEP — PER-HIT VERDICTS

Bare, anchor-free. **No "all remaining hits are X" claim is made anywhere in this report.**

### ⚠ C.0 — THE BRIEF'S SUGGESTED PATTERN MISSED A REAL SITE

`git grep -nI -e '#188' -e 'ungated' -e 'outside .*typecheck'` did **not** match:

> `loremaster/tests/test_secret_typing.py`: *"``scripts/`` is scanned even though it is NOT one of ``scripts/typecheck.sh``'s ``MEMBERS``, so mypy never sees it"*

Found only by reading context around a **neighbouring** hit, then re-sweeping on `-e 'typecheck' -e 'MEMBERS' -e 'mypy'`. **Anchor-free is not pattern-free.** The phrasings for one concept are open-ended — this is the enumerate-the-forbidden trap wearing sweep clothing, and the counter is the same: sweep the broad term and read, don't enumerate the phrasings.

### C.1 FIXED (in my writable set)

| site | verdict |
|---|---|
| `pyproject.toml` `testpaths` `"scripts"` comment | **FALSE, both halves — fixed.** Said *"still outside `scripts/typecheck.sh` (#188 measured 41 mypy errors there)"*. The second half was **already false when written** (§A.1). Replaced with the re-measured pair + an explicit *re-derive, do not inherit*. |
| `scripts/search_score_survey.py::_make_embedder` | **FALSE — fixed.** *"the one no type gate can see, because `scripts/` is not a typecheck member"* → past-tensed. The **⚠ COMPOSITION ROOT** half is untouched and still true. |
| `scripts/test_search_score_survey.py::TestTheRealStoreFactoryBuildsSdkEncodableCredentials` | **FALSE — fixed, and DELIBERATELY NOT DELETED.** Its docstring lists 3 blindnesses that let cold-audit Defect A ship; 2 are now closed. Past-tensed **plus an explicit note that the pin does not become redundant**: blindness 3 is untouched (the covering test still monkeypatches `_make_store` away) and the asserted property is a RUNTIME one the SDK imposes (CBOR-encodability), which no type checker states. |

### C.2 FALSE, OUTSIDE WRITABLE SET — VERBATIM EDITS FOR THE LEAD

**(a) `loremaster/tests/test_secret_typing.py`**, above `_SCANNED_MEMBERS`' trailing comment. Currently:
> `# ``scripts/`` is scanned even though it is NOT one of ``scripts/typecheck.sh``'s`
> `# ``MEMBERS``, so mypy never sees it — and its files construct the very stores`

Proposed:
> `# ``scripts/`` is scanned AND is now its own ``scripts/typecheck.sh`` MEMBERS root`
> `# (#188, 2026-07-29) — but this scan is not redundant: mypy proves types, and this`
> `# proves a POLICY (one blankness predicate, one mint origin) that no type states.`
> `# Its files construct the very stores`

*(The paragraph continuing "That gap shipped a real defect during #211's own migration…" is **past tense and stays true** — no edit needed.)*

**(b) `loremaster/tests/test_secret_leak_vectors.py::test_the_sync_survey_counter_does_not_retain_the_raw_key`.** Currently:
> `# The twin in ``scripts/``, which mypy never sees (``scripts/`` is not a`
> `# typecheck member) and which the loremaster package scan below cannot reach.`

Proposed:
> `# The twin in ``scripts/``. It was invisible to mypy until #188 made ``scripts`` a`
> `# typecheck root (2026-07-29); it is still outside the loremaster package scan`
> `# below, which is why it is forced explicitly here.`

**(c) `docs/design/2026-07-25-floor-calibration-addendum-F.md`** — *"`scripts/` **remains outside** `scripts/typecheck.sh` MEMBERS"*. **FALSE.** A dated design doc; per archiving law the correct treatment is a one-line "superseded 2026-07-29 by #188's discharge" header rather than a silent rewrite. Lead's call.

### C.3 UNAFFECTED — INDIVIDUAL VERDICTS (no wholesale claim)

| site | verdict |
|---|---|
| `Containerfile` `# lore-ungated-binary: curl` | Different sense of "ungated" — image binaries. Unaffected. |
| `loremaster/tests/test_shellout_allowlist.py` (10 hits: `_declared_ungated`, `ungated = installed - derived`, …) | Same binary-allowlist sense. Unaffected. |
| `loremaster/tests/_surreal_fakes.py` (2 hits: *"module-prefix reach is ungated by kind"*) | Graph-edge sense. Unaffected. |
| `loremaster/tests/test_mcp_server.py::test_no_auth_block_leaves_app_ungated` | Auth-middleware sense. Unaffected. |
| `CLAUDE.md` *"the guards for #192 and #196, ungated"* | About `testpaths`, already past-tense. Unaffected. |
| `loremaster/tests/test_secret_resolution_seam.py` (2 hits) | Both about **`skills/`**, both already correctly dated/past-tensed by a prior wave. Unaffected. |
| `scripts/registration_sites.py` *"its ungatedness is a stated bound"* | About **its own** exit code deliberately not being a gate. Unaffected — and correct. |
| `docs/eval/test_smoke_p8b.py` *"Packet 44 added the type gate too"* | About `docs/eval`. Unaffected, and now has a sibling. |
| `docs/plans/v2/44-ungated-ground.md`, `docs/plans/v2/INDEX.md` (3 hits) | Packet/plan docs; **do-not-touch** per brief. The packet doc's *"scripts/ untyped #188"* is now historical — lead's close-out. |
| `REPORT-builder-forgery-sites.md` (3 hits, incl. two more *"41 mypy errors"*) | Another agent's un-archived root report. Historical record of a correct decision **at the time**; per archiving law it gets a superseded header on archive, not a rewrite. Not mine. |

### C.4 ⚠ LEDGER ITEM — `scripts/test_forgery_door_sweep.py` (NOT TOUCHED, as ruled)

`TestThisInstrumentIsTYPECHECKED` — docstring *"⛔ `scripts/` is OUTSIDE `scripts/typecheck.sh` (#188 measured 41 mypy errors…)"* and assertion message *"…the canonical gate cannot see it (scripts/ is outside scripts/typecheck.sh MEMBERS)"*. **Both now FALSE, and both re-cite the wrong 41.**

Its whole mechanism — shelling out to `mypy` from inside a test because the canonical gate could not see the file — **is now redundant with the `scripts` leg.** `REPORT-builder-forgery-sites.md` §D3 already named the correct follow-up in advance: *"delete `TestThisInstrumentIsTYPECHECKED` in the same commit rather than keeping both."* Operator-ruled untouched this packet; **flagged, not acted on.**

---

## D. FORKS — SURFACED, NOT SETTLED

### D.1 ⚠ MY OWN REGRESSION, AND THE RULING IT NEEDS

**What happened.** I fixed `password="unused"`'s `arg-type` error with `SecretStr("unused")`. The full suite went **1 failed / 8392 passed** — and the one failure was mine:

```
FAILED loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam
       ::test_secretstr_is_minted_only_where_a_credential_ORIGINATES
E  AssertionError: a SecretStr is minted outside a credential ORIGIN. Re-wrapping a bare
   str at a call site defeats the typed seam (attack shape S6):
E      scripts/comms_consumer_eval.py:957
```

**The pin is right; my fix was wrong.** It allows a `SecretStr(...)` mint only in `loremaster/config.py` and `scripts/survey_txn_contention_102.py`, because minting at a call site **is** attack shape S6: the type then proves the value is wrapped *at the call*, never that it was not bare the whole way. My edit was that exact shape. **A green type gate bought by reddening a security invariant is not a fix.**

**What I did:** took the safe side. `password="unused"` restored, with **one narrow `# type: ignore[arg-type]` on one argument** and ~20 lines naming which two invariants collide, why the security one wins, and what retires it. The registry never connects (`ws://127.0.0.1:1`; `_query` replaced on the next line), so the value is inert either way — the disagreement is purely about which gate absorbs it.

**THE FORK FOR YOU:** the consistent alternative is adding `scripts/comms_consumer_eval.py` to that pin's `allowed` origins — **exactly as `scripts/survey_txn_contention_102.py` already is**, which is precedent that a script's inert test credential can be an origin. That **expands a security allowlist** and edits a test outside my writable set ⇒ operator ruling, not a builder's call.
**My recommendation: keep the ignore.** The allowlist should stay as small as the threat model allows, and one documented ignore on an inert literal is cheaper than a permanent widening. But it is your call, and if you rule the other way the edit is: add the path to `allowed`, delete the ignore, write the `SecretStr`.

**Worth recording:** the full suite caught what mypy, ruff and every scoped run waved through. The instrument was an **AST invariant over a defect CLASS** — the thing CLAUDE.md says every audit-caught class must become — and it fired on a builder who had read neither it nor the class, one file away from the code it guards. *A fix without an invariant is half a fix*, demonstrating itself.

### D.2 UPSTREAM: `loresigil` widens its own discriminators — **GRANTED (R7) AND DONE, see §H**

`loresigil/loresigil/factory.py`:
```python
BACKEND_TEI: str = "tei"            # explicit str -> WIDENS
BACKEND_VOYAGE_CLOUD: str = "voyage-cloud"
BACKEND_VOYAGE_CONTEXT: str = "voyage-context"
```
…against `EmbeddingConfig.backend: Literal["tei", "voyage-cloud", "voyage-context"]`. Their own comment says they are *"kept as constants so dispatch and the schema agree"* — **at type level they demonstrably do not.**

**Exact edit (3 lines):** `BACKEND_TEI: Literal["tei"] = "tei"`, and likewise for the two siblings.
**Safety, checked:** `Literal` is a subtype of `str`; the only other consumers are `if config.backend == BACKEND_TEI` comparisons (`factory.py`, and loresigil's own test) and a `list[tuple[str, str]]` in `test_factory_secret_resolution.py`. All still typecheck.
**Why I didn't:** `loresigil/` is outside my writable set (brief-base §2 ⇒ flag, don't edit).
**In-scope stand-in:** a commented `cast(Literal["tei"], BACKEND_TEI)` at the call site that names the upstream fix and says **DELETE THIS CAST** the day it lands. The *value* still comes from the constant, so a renamed backend is still a one-place change.
**Recommendation: grant it** — it is strictly safe and removes the cast entirely.

### D.3 Escalation not needed but noted
`scripts/typecheck.sh`'s `MEMBERS` is a **hand-list**, and CLAUDE.md's own law says the enumeration is the artifact with the most receipts against it (*"wrong four times"*). `registration_sites.py` derives registration sites from a property; `MEMBERS` could plausibly be derived too (*every tracked `.py` lives under some typecheck root*). **Out of scope, not attempted, raised because I noticed it** — and because `scripts/registration_sites.py` already contains the germ: *"The thing that IS enforceable — 'every committed `.py` rides some gate' — is a different instrument."*

---

## E. GATES

### E.1 mypy — `scripts` is ZERO over every tracked file

```
MYPYPATH=scripts uv run mypy $(git ls-files 'scripts/*.py')
Success: no issues found in 19 source files
EXIT=0
```
**24 → 0.**

### E.2 `./scripts/typecheck.sh` — EXIT=1, and NOT because of anything I own

```
typecheck: lorerunes OK      typecheck: loremaster OK    typecheck: scripts FAILED
typecheck: lorescribe OK     typecheck: skills OK        typecheck: shellcheck OK (7 tracked .sh)
typecheck: loresigil OK      typecheck: docs/eval OK
TYPECHECK_EXIT=1
```

**All 6 residual errors are in the peer session's two UNTRACKED files** (`git ls-files` returns neither):
```
scripts/gated_ground.py:303,311,316,333: error: Returning Any from function declared to return "list[str]"  [no-any-return]
scripts/test_gated_ground.py:1239: error: "list[UngatedFile]" has no attribute "findings"  [attr-defined]
scripts/test_gated_ground.py:1241: error: "list[UngatedFile]" has no attribute "render"   [attr-defined]
```
**Zero errors in any tracked file.** This is exactly the case the brief anticipated. Not mine, not touched, not "fixed". It was 19 errors when I started and is 6 now — that build is converging, and the leg goes green when it lands. **I am not claiming this gate green; I am claiming my half of it is.**

### E.3 ruff — clean
```
All checks passed!
RUFF_EXIT=0
```
*(Earlier in my run this was 1 error — an `F401` in the peer's `test_gated_ground.py`. I did not touch it; they cleared it.)*

### E.4 ⚠ THE RIDER — MUTATION PROOF THAT THE NEW LEG FIRES

Per *"THE RIDER IS PART OF THE RULING"*. Expected-RED set written down **before** the run, diffed **both ways**.

*"If step N silently no-opped, would step N+1 still print something that reads as success?"* — **Yes, and that is why leg (C) exists.** If the `MEMBERS` edit had not taken effect, leg (A) would still print `scripts FAILED` (the peer's file already reddens it) and read as success. So the proof cannot rest on the gate being red; it must show **the specific error appearing**, and **the old gate not seeing it**.

Mutation: `_MUTATION_PROOF_188: int = "not an int"` appended to `scripts/snapshot_gc.py`. Landing verified before measuring (`git diff --stat` → `3 +++`), per #194.

| leg | declared | observed | |
|---|---|---|---|
| **A** | `scripts` leg names `snapshot_gc.py` with `[assignment]`; 19/1 file → 20/2 files | `scripts/snapshot_gc.py:451: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]`; exactly 20 errors in 2 files | ✅ |
| **B** | other 6 mypy legs + shellcheck stay OK | all OK — error attributable to this leg alone | ✅ |
| **C** | **CONTROL** — pre-#188 MEMBERS (same list **minus** `scripts`) is BLIND | all 6 legs EXIT=0; `grep -l snapshot_gc` over every control log → **no match** | ✅ |

Restore byte-exact: md5 `7b64261f241831650ecf7ae294794988` before **and** after; `git diff --stat scripts/snapshot_gc.py` empty.

**Leg C is the whole proof.** A mutation red before *and* after would have demonstrated nothing.

### E.5 pytest
Run 1 (with my regression): `1 failed, 8392 passed, 36 skipped, 3 xfailed, 1 warning, 1 error in 212.72s`.
**Reconciliation as evidence this is an EXECUTED count, not a collected one:** 8392 + 1 + 36 + 3 = **8432 = the brief's stated baseline collection at `f033a87`.** The `1 error` is a collection error on the peer's `scripts/test_gated_ground.py` (`ImportError`), outside that 8432.
The single failure was **mine** (§D1) and is fixed; `test_secret_typing.py` → **69 passed**.

### E.6 pytest — FINAL, on the committed tree

```
= 5 failed, 8559 passed, 36 skipped, 3 xfailed, 1 warning in 213.39s (0:03:33) =
PYTEST_EXIT=1
```

**Reconciliation (evidence this is an EXECUTED count, not a collected one):** 8559 + 5 + 36 + 3 = **8603 collected**. The brief's baseline at `f033a87` was 8432; the delta of **+171** is the peer's `scripts/test_gated_ground.py`, which contributed **0** to run 1 (it died at collection with an `ImportError` because `gated_ground.py` did not exist yet) and now collects. No collection errors remain.

**ALL 5 FAILURES ARE IN THE PEER'S `scripts/test_gated_ground.py`. ZERO ARE MINE.** My run-1 failure is gone.

```
FAILED scripts/test_gated_ground.py::TestBlindIsNotCleanThroughTheWholeVerdict::test_a_blind_members_declaration_makes_the_whole_verdict_refuse
FAILED scripts/test_gated_ground.py::TestBlindIsNotCleanThroughTheWholeVerdict::test_a_whole_tree_testpath_makes_the_whole_verdict_refuse
FAILED scripts/test_gated_ground.py::TestBlindIsNotCleanThroughTheWholeVerdict::test_a_missing_git_binary_makes_the_whole_verdict_refuse
FAILED scripts/test_gated_ground.py::TestTheExemptionTableIsAnAllowlistOfTheSafe::test_an_exemption_is_scoped_to_its_axis
FAILED scripts/test_gated_ground.py::TestTheExemptionTableIsAnAllowlistOfTheSafe::test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE  (×2 — parametrised)
```

Not investigated, not touched: that file and `gated_ground.py` are another agent's active build, explicitly excluded from my writable set. **I did not downgrade these to "flaky" and did not fix my way past someone else's failure.**

### E.7 pytest — FINAL FINAL, after the R7 `loresigil` fix (§H). **ALL GREEN.**

```
====== 8564 passed, 36 skipped, 3 xfailed, 1 warning in 217.55s (0:03:37) ======
PYTEST_EXIT=0
```

**Reconciliation:** 8564 + 36 + 3 = **8603 collected** — identical to run 2's collection, and 0 failed / 0 errors. The 5 sibling failures from §E.6 **cleared during my run** (their build progressed); nothing I did fixed or masked them. Baseline `f033a87` was 8432; +171 is the sibling's now-collecting `test_gated_ground.py`.

**No failing tests remain, in or out of scope.**

### E.8 FINAL GATE STATE — stated honestly, not claimed green

| gate | state |
|---|---|
| `uv run pytest -n auto` | ✅ **8564 passed, 0 failed, EXIT=0** |
| `uv run ruff check .` | ✅ **All checks passed, EXIT=0** |
| `MYPYPATH=scripts mypy $(git ls-files 'scripts/*.py')` | ✅ **Success: no issues found in 19 source files, EXIT=0** — my scope, 24 → 0 |
| `./scripts/typecheck.sh` | ❌ **EXIT=1** — 7 of 8 legs OK (incl. `loresigil` and `shellcheck`); the `scripts` leg carries **22 errors, all in the sibling's UNTRACKED `scripts/test_gated_ground.py`** |

**I am NOT claiming `typecheck.sh` green, and it cannot be green today.** This is a real sequencing consequence of my own change, and it is worth recording as a fact rather than a defect: making `scripts` a typecheck root means **the leg iterates the DIRECTORY**, so any in-flight file in `scripts/` is now inside the canonical gate. It goes green when the sibling's contract and implementation land together — their landing condition, not a blocker on me, and not something I may route around, exclude, or wait on. *(Note the count moved 19 → 6 → 22 → 22 across my run as they iterated; it is a live tree, so re-derive it rather than quoting this number.)*

---

## F. GIT

### F.1 ⚠ HEAD MOVED UNDER ME
Mid-run, HEAD went `f033a87` → `cc0105d` *"fix(scripts): 11 of #188's 24 real type errors — partial, checkpointed"*, whose message says I *"died to a server-side API 500 mid-wave"*. I had not; I resumed. The commit is **accurate and correct** — it preserved exactly the 4 files I had finished (`survey_txn_contention_102.py` + the 3 unused-ignore files), byte-for-byte what I wrote, with a truthful message. **No damage, no rework.** Raised because a lead reading my commits will otherwise see work attributed twice, and because "the agent is dead" was a false inference from an idle signal — the ambiguous-idle-notification hazard, live.

### F.2 COMMITS (one concern each, explicit paths, never `-a`)

| sha | concern |
|---|---|
| `cc0105d` | *(lead's checkpoint of my first 11 fixes)* |
| `4bf4399` | the last 13 type errors + the `anthropic` override |
| `bd6fb73` | `scripts` becomes a typecheck root (+ mutation proof in the message) |
| `d3d6351` | **revert my `SecretStr` mint** — S6 pin wins |
| `a7cf955` | the #188 prose sweep |

`d3d6351` is the deviation from the suggested 3-commit split: a self-caused regression deserves its own commit rather than being folded silently into a neighbour.

Three files carried **both** type and prose edits (`pyproject.toml`, `search_score_survey.py`, `test_search_score_survey.py`). Since `git add <file>` cannot stage a hunk, I snapshotted the final versions, reverted the prose hunks with `Edit`, committed the type half, then restored from the snapshots — **byte-exactness proved by md5 match on all three** before the prose commit. Working tree clean afterwards.

### F.3 Tooling honesty
**lore's index cannot see this worktree (#125)**, so every structural question here was answered with `git grep` / `git ls-files` rather than `lore_search` / `lore_impact` — declared per the dogfood protocol. `mcp__lore_lore__lore_findings` **was** available and **#188 is resolved** with the receipts above. Not filed as new friction: #125 already records it.

**Instruments:** no bespoke prober was built. The mutation proof used the committed `./scripts/typecheck.sh` plus shell already shown verbatim in §E.4 and in `bd6fb73`'s message; the measurement is one `git ls-files`-piped `mypy` invocation, recorded in `scripts/typecheck.sh`'s own comment so it regenerates from a committed file.

---

## G. SURFACED TO LEAD — QUESTIONS

1. **Grant `loresigil/loresigil/factory.py`?** (§D2) 3-line `Literal` fix → I delete the `cast`. *Recommend: yes.*
2. **Does `scripts/comms_consumer_eval.py` join the S6 mint-origin allowlist?** (§D1) Expands a security allowlist. *Recommend: no — keep the documented ignore.*
3. **Delete `TestThisInstrumentIsTYPECHECKED`?** (§C4) Now redundant AND asserting a false claim + the wrong 41. Peer-owned. *Recommend: yes, once their build lands.*
4. **The 3 outside-writable prose sites** (§C2) — apply my verbatim edits, or route to whoever owns those files?
5. **`MEMBERS` is a hand-list** in a repo whose law says hand-lists are the most-defeated artifact (§D3). Worth a derived instrument (*every tracked `.py` rides some typecheck root*)? Not attempted.
6. **The `scripts` leg is RED on the sibling's untracked files** (§E.8). It goes green when they land. Do you want me to stand by and re-verify, or is that your close-out?
7. **`BACKEND_VOYAGE_CLOUD` has no dispatch comparison** (§H.3) — it is `make_embedder`'s fallthrough arm, so its narrowing is exercised only by test-side consumers. Not a defect; flagged because I noticed it while sweeping and the quantifier law says a property derived over two of three members is not a property of the set.

---

## I. CORRECTIONS TO THINGS I WAS TOLD (verify-don't-assume, in both directions)

Recorded because the lead asked for conflicts to be surfaced, and because this packet has already been bitten twice by inherited numbers.

1. **"Still outstanding: the rider mutation proof and `REPORT-…md`."** Both were already done and committed when that message was written — the mutation proof is in §E.4 and in `bd6fb73`'s commit message; the report existed at the worktree root. The lead's view was one commit stale (it measured at `cc0105d` + my uncommitted tree; I was four commits further on). **No action needed — flagging only so the close-out is not written from the stale picture.**
2. **"Directory invocation → 25 errors in 2 files (21 + 4)."** Did not reproduce at any point in my run: I measured **19/1**, then **6/2** (4 `gated_ground.py` + 2 `test_gated_ground.py`), then **22/1**. The sibling's tree is moving under both of us. **Nobody is wrong; the number is simply not stable enough to quote.** Re-derive at close-out.
3. **"A transient `F401` in `scripts/test_gated_ground.py`."** True when sent — I saw it and did not touch it. **Already cleared by the sibling**; ruff is `All checks passed` as of my final run.
4. **No conflict** between the `pkt44` brief v1 and anything sent by inbox. R7 as written in the brief matches the grant I received; the `Final[Literal[…]]` shape guidance is additive to R7's *"narrowed from `str` to Literal"*, not contrary to it, and §H.2 records why I took it.

---

## H. THE R7 SCOPE GRANT — `loresigil` (done)

Granted narrowly by the operator (`pkt44` brief v1, R7): **those three declarations, the cast deletion, the comment.** Nothing else in `loresigil`. Nothing needed a fourth line, so nothing was asked for.

### H.1 What was wrong
`loresigil/loresigil/factory.py` declared `BACKEND_TEI: str = "tei"` (+2 siblings) while **line 65 of the same file** declares `backend: Literal["tei","voyage-cloud","voyage-context"]`. An explicit `str` widens away from that `Literal`, so `EmbeddingConfig(backend=BACKEND_TEI)` was an `arg-type` error, pushing callers toward re-stating the literal by hand at every construction site — **duplicating exactly what the constants exist to prevent.**

**And the comment asserted the property the annotation broke:** *"kept as constants so dispatch and the schema agree."* Not stale — **FALSE**, 17 lines above the `Literal` it claimed to agree with. Tracked P8d class: a natural-language surface contradicting its own implementation, guarded by no gate. Per the operator's specific endorsement the comment was **corrected, not deleted** (the reason it existed is real), and now carries a **DO-NOT-SIMPLIFY-BACK-TO-`str`** note naming #188.

### H.2 `Final[Literal[...]]` vs bare `Literal[...]` — and why
**Chose `Final[Literal["tei"]]`.** The comment claims **two** properties; each now has an enforcer:

| the comment's claim | enforcer |
|---|---|
| *"kept as **constants**"* | `Final` — reassignment is an error, not a silent redefinition |
| *"so dispatch and the schema **agree**"* | `Literal["tei"]` — the constant **is** one member of the schema's `Literal` |

A bare `Literal` would have left **half the sentence still unenforced prose** — which is the exact failure mode being fixed. That is the difference the lead asked me to name: between the comment being *true* and the comment being *enforced*.

### H.3 Consumer sweep — RE-DERIVED BY GREP, and the fallback is declared
⚠ **Dogfood declaration:** `lore_impact` was **not** used. Two independent reasons, both cited by the lead and both verified as still applying: **(1) #125** — lore's index cannot see this worktree, so any graph answer is about a *different tree*; **(2) #233** — `lore_impact` undercounted at **this exact address** once already (an `EmbeddingConfig` same-identity collision in this same file). `git grep`, bare and anchor-free, over all three names. **Sanctioned fallback, said out loud.**

| site | verdict |
|---|---|
| `factory.py` `if config.backend == BACKEND_TEI` / `== BACKEND_VOYAGE_CONTEXT` | **Fine.** Literal-vs-Literal overlaps under `strict_equality`; the fallthrough stays reachable under `warn_unreachable`, and its comment *"the only remaining Literal value is voyage-cloud"* is now a claim mypy can actually **verify**. |
| `test_factory_secret_resolution.py` imports (×3), `_config_for(backend: str, …)` comparisons, `BACKEND_ARMS: list[tuple[str, str]]`, the 4 construction/assert sites | **Fine.** `Literal` is a subtype of `str`; tuples are covariant. |
| `test_factory_secret_resolution.py` `for kept in (…, "BACKEND_TEI")` | **Unaffected** — a **string** in a `hasattr` probe, not a symbol reference. **⚠ This site was NOT in the list handed to me** — it is the receipt for why the sweep was re-derived rather than inherited. |
| `scripts/search_score_survey.py` import + cast site | The cast is **deleted**. |

**Also noted:** `BACKEND_VOYAGE_CLOUD` has **no** comparison in `factory.py` — it is the fallthrough arm. Its narrowing is therefore untested by dispatch and rests on the test-side consumers alone.

### H.4 EVIDENCE

**Byte-identical values — CHECKED, not assumed.** Each constant compared against its own HEAD source, parsed by AST:
```
BACKEND_TEI              HEAD='tei'           NOW='tei'           bytes_identical=True
BACKEND_VOYAGE_CLOUD     HEAD='voyage-cloud'  NOW='voyage-cloud'  bytes_identical=True
BACKEND_VOYAGE_CONTEXT   HEAD='voyage-context' NOW='voyage-context' bytes_identical=True
type(BACKEND_TEI) at runtime: str   (Final/Literal are erased at runtime)
```
The instrument asserts it parsed a non-empty set from HEAD first, so an empty parse is a broken instrument rather than a false clear. **Zero runtime change.**

**THE 2×2 — which change actually clears the error** (rather than asserting it):

| upstream | cast | mypy on `search_score_survey.py` |
|---|---|---|
| `str` | present | **CLEAN** — the status quo; the workaround was *masking* the defect |
| `str` | absent | `arg-type: … incompatible type "str"; expected Literal[…]` — the original defect |
| `Literal` | present | **`redundant-cast`** — mypy itself demands the deletion |
| `Literal` | absent | **CLEAN** ← shipped |

**The third cell is the receipt.** It proves the *upstream narrowing* is what clears the call site — not the cast — and that **the gate now refuses to let both exist**, so the cast could not have become furniture even if I had left it.

**Suites:** `loresigil` → **378 passed, 1 skipped**. Direct consumer `test_factory_secret_resolution.py` → **27 passed**. `./scripts/typecheck.sh` → `typecheck: loresigil OK`. ruff → `All checks passed`.

### H.5 ⚠ FINDING-SHAPED OBSERVATION — packet 44's thesis, with a receipt on first use

**This defect was invisible for as long as `scripts/` was ungated, and surfaced the moment the tree came under a gate.** Nothing about the wrong annotation changed — only whether anything was looking.

What makes it a sharper receipt than it first appears: the defect did **not** live in the ungated tree. It sat in `loresigil`, a member that has been under `scripts/typecheck.sh` **all along**, seventeen lines from the `Literal` it contradicted. It survived there because the widening only bites where a caller **constructs the model from the constants** — and the only such caller lived in `scripts/`. **Gating tree A exposed a defect in tree B.** The argument for packet 44 is not merely "ungated ground rots"; it is that an ungated tree can hold the *only witness* to a defect in a gated one.

Its comment is the same story in the other register: this repo already knows that natural-language surfaces contradicting code are its most-shipped defect class, and this one had been asserting its own falsity in a gated member, in plain English, for as long as the annotation was wrong.
