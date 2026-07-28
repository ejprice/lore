# REPORT-adversary-pkt42-1-rerun4 — CONTRACT ADVERSARY, packet 42, FIFTH PASS

brief-base v7 read

Grades revision 6 at **`77d70f7`**. Prior passes cited, none superseded:
`REPORT-adversary-pkt42-1.md` · `-rerun.md` · `-rerun2.md` · `-rerun3.md`.

## SUMMARY BLOCK

- **VERDICT: CONTRACT SUFFICIENT.** No wrong build survives. Every attack from rounds 1–4 is caught, including round 4's blocker. Three corrections are required but **none of them lets a wrong build through**, so they do not block.
- **P1 headline — I could not break it.** Round 4's `W-PARAMNAME-BARE` (credential parameter named `bearer_token`, bare `str`) is now caught by **both** legs of the v3 union, verified deterministically against the real gate. The full battery stays dead: `W-SYNCWIRE` 3 RED · `W-R10a` 2 RED · `W-SHAPEA` 2 RED · `W-LASTWRITER` 2 RED · `W-ENGINE`/new-module siblings now swept.
- **Frontier 1 — the union is a genuine OR, not an AND.** `_node_verdicts` appends from both legs independently; measured on one node emitting *both* verdicts (`builds 'x-api-key' outside the seam` **and** `headers= not sourced from build_auth_headers()`). No shape is exonerated by one leg passing.
- **Frontier 5 — the attack corpus DOES run.** `loremaster/tests` is in `testpaths`; a bare `pytest --collect-only` collects **13** nodes from `TestTheSeamGateWasAttackedByItsOwnAuthor`, all passing. Not a hope with a filename.
- **⚠ CORRECTION 1 (the one that matters) — the corpus tests a COPY of the gate.** `_gate_flags()` re-implements `_node_verdicts()` instead of calling it. I deleted v1's name leg from the **real** gate: `_node_verdicts` returned no verdict on S1, `_gate_flags` still returned `True`, the corpus passed **13/13**, and the whole file added **zero** failures. The instrument built to measure the gate's reach every run measures a duplicate's reach. It also **falsifies one ledger row**: S6 is ledgered `True`, the copy says `True`, the real construction gate says **False** — S6 is in fact caught by the *mint* gate (`embedding.py:97`), a different function. Outcome safe, attribution wrong, drift undetectable.
- **⚠ CORRECTION 2 — S8's dissolution is over-claimed.** Measured: `?api_key=` and `?token=` are covered by the surviving labelled pattern; **`?key=` and `?access_token=` LEAK**. The claim needs the qualifier.
- **⚠ CORRECTION 3 — a countable claim is wrong.** *"6 production sites today, and 2 of them retire"*: measured **6 sites, 4 retire** (`counting.py:77,84` + `token_survey.py:731,738`). "2" counts *functions*. Two populations, the packet's own recurring defect.
- **Everything else verified closed:** R26 typed seam (round-4 blocker caught) · R27.1 module list **genuinely derived** (a brand-new module IS swept) · R27.2 floor **replaced by a totality check** (`assert not skipped`, naming the unbuilt holder) · mint gate has **no production false positives** and excludes tests by construction · triggers on S2/S7/S9 present.
- **Packages considered:** none — no mechanism specified or built by me beyond scratch probes.
- **Receipts:** §P1 · §P1b · §Frontiers · §Corrections. Baseline at `77d70f7`: **113 failed / 249 passed** (362 tests), real worktree. **Repo never edited** — `git diff` over production trees empty.

Measurements **2026-07-27**, worktree `lore-pkt42` at **`77d70f7`**, `scratch_copy.sh` tree,
`loremaster.__file__` inside scratch verified.

---

## P0 — CONTROLS

Scratch survives; `logging_setup.BASE.py` md5 `831ca42e782e9ee9b4533dc750166ccc` still matches.
Every mutation asserts its landing; every wrong build carries a behavioural sanity line.

**One methodological correction I made mid-pass, and it changed a conclusion.** My first attempt to
test round-4's blocker used a `comm` diff of failure sets — which came back **blank** and would have
read as "not caught". It was blank because `test_no_auth_header_is_built_outside_a_seam` is
*already* RED at base (no seam is built yet), so it appears on both sides and cancels. **A pin that
is red for an unrelated reason cannot discriminate anything**, and a diff over it is not evidence.
I replaced it with a deterministic call into the gate's own helper
(`_auth_construction_offenders()`), which answers the question without needing a green tree — and
the honest answer was the opposite: **caught, by both legs.** The same substitution fixed the
`CalibrationEngine` and new-module checks. Any "blank diff" in this report is therefore backed by a
deterministic check, never by the diff alone.

---

## P1 — WRONG BUILDS: none survive

### Round 4's blocker is dead, verified against the REAL gate

`StreamingCountClient(bearer_token: str)` holding `{"x-api-key": bearer_token}`, appended to
`loremaster/calibration/counting.py`:

```
  seam gate verdicts on the new class's lines:
    loremaster/calibration/counting.py:211 headers= not sourced from build_auth_headers()
    loremaster/calibration/counting.py:211 builds 'x-api-key' outside the seam
  -> round-4 blocker is CAUGHT by the v3 seam gate
```

Both legs fire on the same node — which is also the empirical proof for frontier 1 that the union
**ORs** rather than ANDs. R26's design answers MP14 at the level it was raised: the credential-NAME
set is unbounded, and the gate no longer keys on it.

### The standing battery (re-run at `77d70f7`)

| build | verdict |
|---|---|
| `W-SYNCWIRE` (sync twin sends no auth header) | **3 failed** |
| `W-R10a` (owned arm unauthenticated) | **2 failed** |
| `W-SHAPEA` (client-level headers) | **2 failed** |
| `W-LASTWRITER` (shared client, per-construction writes) | **2 failed** |
| `W-ENGINE` (early unwrap in `CalibrationEngine`) | now **constructed and interrogated** (R27.2) |
| new-module sibling (`batch_counter.py`) | now **swept** (R27.1: `['loremaster.calibration.batch_counter.BatchClaudeTokenCounter']`) |
| `W-PARAMNAME-BARE` (round-4 blocker) | **caught, both legs** |

**I did not find a wrong build that satisfies this contract while leaking, mis-authenticating, or
failing to fix the thing.**

---

## P1b — QUANTIFIER TABLE (mandatory)

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| I1 | An outgoing auth header is built only through a typed seam | **∀ over the workspace AST**, two independent predicates OR'd — a NAME leg and a construction-SURFACE leg. **Not name-keyed alone**, which is what closed MP14 | ✅ round-4 blocker caught by both legs; S5 (`httpx.BasicAuth`, no header name in source) caught by the surface leg |
| I2 | A `SecretStr` is minted only where a credential originates (S6) | ∀ over `SecretStr(...)` calls in production; tests excluded by `_python_sources()` | ✅ 6 sites, 4 retire with the consolidation, 2 allowlisted. Re-wrap bypass in `embedding.py` → flagged |
| I3 | The seam rejects a bare `str` at RUNTIME (not just mypy) | ∀ over both packages | ✅ R18-compliant by construction |
| I4 | The seam still emits the real bytes | ∀ over both packages | ✅ the "satisfiable by breaking auth" trap is closed |
| I5 | Every auth-holder sibling is swept | **∀ over pkgutil-walked packages + `scripts/` by filename** | ✅ R27.1 — a brand-new module IS seen |
| I6 | Every rostered holder is CONSTRUCTED, not counted | ∀, totality (`assert not skipped`) | ✅ R27.2 — replaces the `>= 4` floor that hid `CalibrationEngine` |
| I7 | Every wire arm authenticates (async + sync, owned + injected, N-model) | ∀ 2 classes × 2 arms + 2-model leg | ✅ whole battery RED on the wrong builds |
| I8 | No credential is baked into either client (shape B) | ∀ both classes, mandate + function pinned separately | ✅ |
| I9 | No production object retains an unwrapped credential | ∀ both counters + production log path ×2 | ✅ |
| I10 | `x-api-key` line covered / structured bounded | ∀, clean partition, bound verified not-live | ✅ |
| I11 | `_scrub_value` recurses; R8 schemes; byte-exactness; entropy gone | ∀ | ✅ all closed since earlier rounds |
| I12 | Every unwrap site is allowlisted | ∀ whole workspace, both ways | ✅ backstops the sweep |
| I13 | **The gate's own REACH is measured every run** | **GUARDED — measured against a re-implementation, not the gate** | ⚠ **CORRECTION 1**: real gate regressed → corpus **13/13 green**, zero added failures; S6 ledger row falsified against the real gate |

---

## FRONTIER ANSWERS

**1 — Is v3 genuinely the union?** **Yes, an OR.** `_node_verdicts` appends from both legs
independently and returns the accumulated list; no branch exonerates. Measured: one node produced
both verdicts simultaneously. Nothing is ANDed, so v3 is strictly stronger than either half.

**2 — Does the mint gate redden honest code?** **No production false positive found.** All 6 mint
sites are credential origins; `_python_sources()` excludes test files by construction, so fixtures
and round-trips are safe. The allowlist (`config.py`, `survey_txn_contention_102.py`) is correct
post-consolidation. This gate does not insult honest code, which is the condition for it staying on.

**3 — Does S8 dissolve?** **Partly — the claim is over-broad.** Measured on the labelled patterns:

```
  LEAK=False https://api.x/v1/count?api_key=***REDACTED***
  LEAK=False https://api.x/v1?token=***REDACTED***
  LEAK=True  https://api.x/v1?key=sk-ant-api03-…
  LEAK=True  https://api.x/v1?access_token=sk-ant-api03-…
```

`?api_key=` and `?token=` are covered because those literals are in the label alternation.
`?key=` (Google's convention) and `?access_token=` (OAuth) are not. **CORRECTION 2**: qualify the
ledger row — *"covered for the labelled spellings only"* — or re-ledger S8 as a bound with a
trigger. It is not a leak lore produces today; it is a claim that is broader than its evidence.

**4 — Are the S2/S7/S9 triggers real?** They are **written and specific** (e.g. *"the day a caller
binds the seam's result to anything"*), and `test_every_uncaught_shape_has_a_reason_and_a_trigger`
enforces that every `False` row carries one. **Nothing automatically watches for the conditions** —
but that is inherent to a ledgered bound, and the repo's own law asks for a named trigger, not a
daemon. I record this as adequate, not as a defect.

**5 — Does the attack corpus run?** **Yes** — 13 nodes collected under bare `testpaths`, all
passing. This was the highest-value check and it passes cleanly. **But see Correction 1: it runs,
and it measures the wrong object.**

**6 — R27's two fixes?** Both real. The module list walks `pkgutil` over both packages plus
`scripts/` by filename — a brand-new module is swept, which the previous hand-list could not do.
`constructed >= 4` is replaced by `assert not skipped`, which names any rostered-but-unbuilt holder;
`CalibrationEngine` is now supplied its three extra kwargs and actually interrogated.

---

## THE THREE CORRECTIONS (required; none blocking)

**C1 — make the corpus call the gate.** `_gate_flags()` should build the enclosing map and call
`_node_verdicts()` (plus the mint check, explicitly, so S6's attribution is honest) instead of
re-deriving the predicates. Receipt for why:

```
W-GATEDRIFT: v1 name leg deleted from the REAL gate; _gate_flags untouched
  REAL gate (_node_verdicts) on S1: NO VERDICT  <- regressed
  CORPUS helper (_gate_flags) on S1: True       <- still True: it tests a COPY
  TestTheSeamGateWasAttackedByItsOwnAuthor: 13 passed
  failures ADDED across the whole file: (none)
```

And the standing divergence today: **S6 ledger `True` / copy `True` / real construction gate
`False`** — safe only because the mint gate catches it at `embedding.py:97`. This is the repo's
ONE-IMPLEMENTATION law (*"prove sharing by MUTATION — change the shared thing and every caller must
break"*) unmet inside the instrument built to honour it. **I would insist on this before the corpus
is relied on in a later wave**; it does not block today because a builder may not edit contract
tests, so `_node_verdicts` cannot drift during this packet.

**C2 — qualify S8** (`?key=`, `?access_token=` are not covered).

**C3 — fix the count**: 6 mint sites, **4** retire, not 2.

---

## RESIDUALS — individual verdicts

| # | item | verdict |
|---|---|---|
| S1 | `counting.py:110` comment still names `self._headers`, which shape B deletes | **STILL OPEN** (raised rounds 3–4). One line, and it is the very comment R10/R19 quote as "prose that names a hazard is not a guard". |
| S2 | The sweep imports `token_survey` via `sys.path` mutation; a same-named module elsewhere on the path would be scanned instead | **FLAG**, low risk, unchanged. |
| S3 | Round-1 residual R12 (`Bearer <k>'}` eats the closing quote) | **STILL OPEN, out of scope** — operator declined four times. Recorded so it dies by decision, not attrition. |
| S4 | `skills/` remains outside `scripts/typecheck.sh` (R9 extends it; verify at build time) | **NOTED** — author's own residual, unchanged. |
| S5 | Baseline moved 341 → 362 tests | **CONSISTENT** with the new seam/corpus classes; not derived line-by-line. |
| S6 | I ran `pytest` in the graded worktree (read-only) | **DISCLOSED.** `git diff` over production trees empty. |

---

## VERDICT

# CONTRACT SUFFICIENT

I tried hard to break it and failed. Round 4's blocker is dead at the level it was raised — R26
answered *"the credential-name set is unbounded"* with a type rather than a longer list, and the v3
union is a real OR of two independent predicates, so `httpx.BasicAuth` (no header name in source)
and `{"x-api-key": token}` (no seam call) are each caught by the leg the other misses. R27 closed
both of my round-4 instrument findings properly: the module list is genuinely derived, and the
vacuity floor is replaced by a totality check that names what it could not build. The whole
five-round battery of wrong builds is caught, and the attack corpus is inside `testpaths` and
collected — the check I expected to fail.

**The most valuable thing I found this round is not a hole; it is that the corpus grades a copy of
the gate.** I regressed the real gate by half and the corpus stayed 13/13 green, and one ledger row
(S6) is already false about the real construction gate. That is a genuine instrument defect of the
class this repo has the most receipts on — but it does not admit a wrong build today, because the
contract's tests are not the builder's to edit and the gate itself demonstrably works when called.
So it is a required correction, not a blocker, and I have said which one I would refuse to inherit.

Findings across five passes: 4 → 4 → 4 → 2 → 3-non-blocking, with every prior finding staying
closed and each round's survivor a genuinely new class. **This one clears.**
