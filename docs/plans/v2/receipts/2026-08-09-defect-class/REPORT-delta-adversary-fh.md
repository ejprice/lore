brief-base v10 read
brief project v7 read

# REPORT — delta-adversary-fh (re-grade of the REVISED F/#279 + H/#290 contracts)

Session `2026-08-09-fix-344-345`. Role: contract-adversary DELTA pass — re-grade the contracts
AFTER reviser-fh closed adversary-f's WB7/WB8 and adversary-eh's two-copies BLOCKER. Two questions:
(a) does the revision TRULY close each original wrong build (independent rebuild, not the claim), and
(b) did it OPEN a NEW wrong build (the r5 lesson)? I edit NO code/tests.

## SUMMARY BLOCK

- receipt: brief-base v10 read · brief project v7 read
- state: **done**
- **VERDICT: CONTRACT SUFFICIENT** (both F/#279 and H/#290).
- **P1 headline — did any wrong build survive? NO genuine-defect build survives EITHER contract.**
  F: WB7 (4 red), WB8 the BLOCKER (2 red), and TWO NEW partials hardcoding a *different* seam (2 red / 1 red) all caught.
  H: the two-copies BLOCKER (3 red), routes-and-keeps (2 red), routes-first+dead-copy (1 red, anti-dup only) all caught.
  The ONE survivor (H TC-D) is a build that ROUTES CORRECTLY and carries dead unreachable differently-shaped code — the contract's own DECLARED bound; behaviourally equivalent to correct, not a divergence risk.
- Packages considered: none — pure introspection/AST contracts (stdlib `inspect`/`ast`/`importlib` + pytest MonkeyPatch); reference build stdlib-only. Independent survey agrees with reviser: no library introspects OUR `_txn` coroutines or AST-walks OUR source. No mechanism specified.
- Graded: `3b708e5` · HEAD-at-report: `3b708e5` · SAME. (Reviser graded `962eeb6`; its edits are committed at `3b708e5` — the tested files match the commit.)
- decisions-needed: **none.** (F5 placement, B/#337 forks belong to other cycles; TC-D residual is a declared bound, not a fork.)
- receipt pointers: satisfiability §Satisfiability · F wrong builds §P1-F · H wrong builds §P1-H · **leg-5 meta-recursion §Leg5** · quantifier table §P1b · reach table §P1c · residuals §Residuals · instruments §Probe-record.
- provenance (#140): `loremaster.__file__ = /home/ejprice/scratch-delta-fh/loremaster/loremaster/__init__.py` (asserted by `scratch_copy.sh`; main tree never mutated).

---

## VERDICT: CONTRACT SUFFICIENT (F and H)

Both revised contracts close every wrong build the two original adversaries found, close the two
NEW "different-seam" partials I built to test the ∀ genuinely covers EVERY member (not just the two
the old single-seam drops covered), and survive a leg-5 meta-recursion attack (add a member to
production → the parametrisation grows AND a stale caller reddens the coverage pin). I could not
break either contract with a genuine-defect build. The only survivor is a build that is
behaviourally correct — the contract's own honestly-declared pattern-keyed bound.

---

## P1-F — F wrong builds (independent rebuild, provenance-asserted scratch)

Reference build written independently in scratch (I did not copy the reviser's edits): a live
`loremaster.store._txn_coroutines`; `store_seams`/`seam_bindings(seams=)` routed through it;
`_degrade_every_STORE_seam` routed through it BY IDENTITY (the cleaner form the adversary
recommended — imports nothing from `scripts/`). Each wrong build patched over the reference; the
relevant contract re-run. Full probe = `delta_probe.py` (§Probe-record).

| build | what it does | F contract | correct? |
|---|---|---|---|
| REFERENCE | all three callers route through `_txn_coroutines()` | **23 passed** | ✅ satisfiability |
| **WB7** | `store_seams` routes `run_query`, HARDCODES `execute_transaction`/`execute_read_transaction` | **4 failed** | caught ✓ (was the residual survivor of the OLD contract) |
| **WB8** (was BLOCKER) | `_degrade` routes `run_query`+`bootstrap_session`, HARDCODES the other 2 doors | **2 failed** | caught ✓ (the no-backstop BLOCKER — now dies on LEG B) |
| **NEW-store_seams** | routes `run_query`+`execute_transaction`, HARDCODES `execute_read_transaction` (a DIFFERENT door) | **2 failed** | caught ✓ (proves ∀ covers every door, not just the old drop) |
| **NEW-_degrade** | routes 3 seams, HARDCODES `execute_read_transaction` ONLY (a DIFFERENT single seam) | **1 failed** | caught ✓ (single different-seam private copy reddens its own drop) |

The exact RED node ids (from the probe):
- WB7 → `test_dropping_ANY_door_..._reddens_store_seams[execute_read_transaction]`, `[execute_transaction]`, and the same two on `_reddens_seam_bindings`.
- WB8 → `test_dropping_ANY_wide_seam_..._reddens_the_degrade_derivation[execute_read_transaction]`, `[execute_transaction]`.
- NEW-store_seams → `[execute_read_transaction]` on both `store_seams` and `seam_bindings`.
- NEW-_degrade → `_reddens_the_degrade_derivation[execute_read_transaction]`.

Every partial private copy reddens on ITS OWN dropped seam, whichever seam it hardcodes — the
∀-over-every-seam quantifier does exactly what the single-`run_query` drop could not.

## P1-H — H wrong builds (independent rebuild)

Reference build: new `scripts/_harness_guards.py::refuse_vacuous_baseline`; `wrong_builds.main`'s
inline `if not baseline: raise SystemExit` (HEAD line 430) replaced by a single unconditional
`refuse_vacuous_baseline(baseline, cause_hint=tail, interpreter=repr(sys.executable))`. Full probe =
`delta_probe.py` + `delta_probe_h.py`.

| build | what it does | H contract | verdict |
|---|---|---|---|
| REFERENCE | `main` routes through the shared guard | **4 passed** (+8 `test_harness_guards`) | ✅ satisfiability |
| **TC-A** (was BLOCKER) | correct helper present, `main` keeps HEAD inline copy, does NOT route | **3 failed** (spy[0], spy[315], anti-dup) | caught ✓ — the adversary-eh two-copies BLOCKER |
| **TC-B** | `main` routes AND keeps an inline copy BEFORE the routed call | **2 failed** (spy[0], anti-dup) | caught ✓ |
| **TC-C** | `main` routes UNCONDITIONALLY first, dead `if not baseline: raise` copy AFTER | **1 failed** (anti-dup ONLY; spy GREEN) | caught ✓ — **proves anti-dup is load-bearing** (the routes-and-keeps case the spy cannot see) |
| **TC-E** | `if baseline < 1: raise` REPLACES routing (does not route) | **2 failed** (spy[0], spy[315]) | caught ✓ — a differently-shaped copy that ACTUALLY MATTERS dies on the spy |
| TC-D | `main` routes first, dead `if baseline < 1: raise` copy AFTER | **0 failed — SURVIVES** | DECLARED BOUND (see §Residuals) — behaviourally CORRECT build |

TC-C is the decisive result: it demonstrates the spy alone would pass a routes-and-keeps build
(the routed call is reached first, so `_SharedGuardWasCalled` fires on both `[0]` and `[315]`), and
ONLY the anti-dup scan reddens it. "Neither alone is the sharing proof; together they are" — verified.

## Leg5 — META-RECURSION: is the ∀ reach the LIVE surface (a checked variable), or a hidden constant?

The class this whole packet exists to kill is *a guard whose reach is a hidden constant*. So I
attacked the revised guards' OWN reach by mutating production truth. All legs EMPIRICAL (both
guards are in-tree; I built the reference in scratch).

**F door side** — added a synthetic 4th door `execute_batch(statement)` to production `_txn.py`:
- **MR-1 (reach is live):** `pytest --collect-only` now yields `..._reddens_store_seams[execute_batch]` and `..._reddens_seam_bindings[execute_batch]`. The parametrisation GREW because `_live_door_surface()` reads `vars(_txn)` live — it is NOT a fixture constant.
- **MR-2a (positive control):** with a LIVE core, `test_the_door_drop_surface_equals_the_live_core_door_filter` is GREEN.
- **MR-2b (reach is a CHECKED variable):** with a STALE core (hand-list blind to `execute_batch`), the same coverage pin REDDENS:
  `the door ∀-drop reach ['execute_batch','execute_read_transaction','execute_transaction','run_query'] has drifted from the live core's door filter ['execute_read_transaction','execute_transaction','run_query']`.

**F wide/`_degrade` side** — added `execute_batch` to `_txn` AND bound it in `loremaster.tasks`:
- **MR-W1 (reach is live):** `--collect-only` now yields `..._reddens_the_degrade_derivation[execute_batch]` — `_live_degrade_wide_surface()` reads `vars(loremaster.tasks)` live.
- **MR-W2a (positive control):** the LIVE (derived) `_degrade` keeps LEG-A `test_the_degrade_set_is_exactly_the_wide_core_bound_in_tasks` GREEN.
- **MR-W2b (LEG-A is the future-4th-seam backstop):** a STALE hardcoded `_degrade` (patches only the original 4 by name, blind to `execute_batch`) REDDENS LEG-A **without any drop** — the exact #279 divergence LEG-A was added to catch (adversary-f's missing backstop).

**H anti-dup side — DERIVED, not a hand-list:** `_inline_vacuity_guards` is an `ast.walk` classifying
every `if not <name>:` / `<name> == 0` whose body raises, keyed on AST SHAPE (not a fixed string).
Confirmed empirically:
- HEAD `wrong_builds.py` → `{'wrong_builds.py:430': "UnaryOp(op=Not(), operand=Name(id='baseline'))"}` (the offender).
- Routed reference `wrong_builds.py` → `{}` (clean).
- It correctly IGNORES the 4 legitimate guards structurally (`.git` is_dir → Call operand; `failed or errors` → BoolOp; `unknown` → truthiness; `not (passed or failed or errors)` → BoolOp operand) — none is `not <Name>` / `<Name>==0`.

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode)

Every guarded row carries a receipt (a wrong build walking the bad outcome through the pin's door,
or the door-build the pin killed). The two rows the ORIGINAL adversaries flagged (F row 4/5 guarded
by `{run_query}`/`{run_query,bootstrap_session}`; H row 4 guarded by NOTHING) are now ∀ with receipts.

| # | invariant | ∀ or guarded | receipt |
|---|---|---|---|
| F1 | `_txn_coroutines` exists, non-empty, coroutines-only, all public seams present (fail-closed) | ∀ over `vars(_txn)` live | door-only helper reddens 5 pins (adversary-f WB4; reproduced) |
| F2 | door subset == public+`statement` filter of core, SAME objects (consistency, LEG A) | ∀ over doors live | passes looks-DRY by design — sharing proven separately |
| F3 | store_seams/seam_bindings ROUTE through core (sharing) | **∀ over `_live_door_surface()`** (was guarded by `{run_query}`) | WB7 (4 red), NEW-store_seams hardcode-ERT (2 red) |
| F4 | **_degrade ROUTES through wide core (sharing)** | **∀ over `_live_degrade_wide_surface()`** (was guarded by `{run_query,bootstrap_session}` → the BLOCKER) | WB8 (2 red), NEW-_degrade hardcode-ERT-only (1 red) |
| F5 | _degrade's OWN set == wide core bound in tasks (LEG A — the missing backstop) | ∀ (live set-equality, no drop needed) | stale hardcoded `_degrade` reddens WITHOUT a drop (MR-W2b) |
| F6 | the ∀ reach EQUALS the live core (coverage as checked variable) | ∀ (meta-recursion guard) | stale core reddens door coverage pin (MR-2b); matrix grows on a new door (MR-1) |
| H1 | zero baseline REFUSED by the helper | guarded (`==0`), boundary@1 | adversary-eh WBH-a/WBH-c killed (test_harness_guards — sound) |
| H2 | nonzero baseline passes, returns None | ∀ (315, 1) | adversary-eh WBH-b/WBH-h killed |
| H3 | refusal NAMES interpreter AND cause_hint | ∀ over message content | adversary-eh WBH-d/WBH-e killed |
| H4 | **main SHARES the ONE guard (routing)** | **∀-via-delete-the-call spy `[0, 315]`** (was GUARDED BY NOTHING → the BLOCKER) | TC-A (spy[0]+[315] red), TC-E (spy red), TC-C (spy blind → anti-dup) |
| H5 | no second inline vacuity copy (anti-dup) | DERIVED AST-shape scan (∀ over If-nodes) | TC-A/B/C anti-dup red; offender@:430 on HEAD, clean on reference |

## P1c — REACH TABLE (per instrument the contracts introduce or rely on)

| instrument | reach = set of sites | DERIVED vs hand-list | coverage a CHECKED variable? | effect vs proxy | one-source proven by MUTATION | verdict | legs |
|---|---|---|---|---|---|---|---|
| F `store_seams` ∀-drop | `_live_door_surface()` (public+`statement` coroutines in `_txn`) | **DERIVED** (reads `vars(_txn)` live) | **YES** — §6 coverage pin `== live core`; matrix grows (MR-1) | EFFECT (store_seams output reflects the core drop) | **YES** (`_rebind_everywhere` by identity; WB7/NEW caught) | **SAFE** | empirical |
| F `seam_bindings` ∀-drop | same door surface | DERIVED | YES | EFFECT | YES | SAFE | empirical |
| F `_degrade` ∀-drop (LEG B) | `_live_degrade_wide_surface()` (coroutines in `tasks` defined in `_txn`) | **DERIVED** (reads `vars(loremaster.tasks)` live) | **YES** — §6 wide coverage pin; matrix grows (MR-W1) | EFFECT | **YES** (WB8/NEW caught) | **SAFE** (was BLOCKER) | empirical |
| F `_degrade` LEG A (set-consistency) | wide core bound in `loremaster.tasks` | DERIVED (`seam_bindings(seams=core)`) | YES — it IS the coverage check | EFFECT | catches divergence-without-drop (MR-W2b) | SAFE | empirical |
| H `main` routing spy | `refuse_vacuous_baseline` call in `main` | DERIVED (spy reaches BOTH import forms — module attr + from-import name — and drives `main`'s real baseline path) | via monoculture `[0,315]` + anti-dup | EFFECT (observes the guard REACHED with the measured count) | **YES** delete-the-call | **SAFE** (was BLOCKER) | empirical |
| H anti-dup scan | every `if not <name>:`/`<name>==0` raise in `wrong_builds.py` | **DERIVED** (`ast.walk`, offender-enum shape) | fail-closed on the vacuous-∀; single site, no allowlist needed | EFFECT (source AST) | n/a (structural) | SAFE — pattern-keyed bound DECLARED (TC-D) | empirical |

All legs EMPIRICAL: both guards are in-tree/constructible, so each got the wrong-build treatment in
scratch, each negative paired with a positive control (P0). No construction-inspection-only rows.

## Missing pins

**NONE.** Both contracts are SUFFICIENT. The two adversary BLOCKERS (F WB8, H two-copies) are
independently confirmed CLOSED, the two NEW different-seam partials are caught, and the leg-5
meta-recursion attack on each guard's own reach fails to break it.

## Residuals (individual verdicts — nothing dropped)

1. **H TC-D — a routes-correctly build carrying a dead `if baseline < 1: raise` copy SURVIVES both
   H pins.** VERDICT: **DECLARED BOUND, benign — NOT a defect, no missing pin.** The contract's
   `TestNoSecondInlineVacuousBaselineGuard` docstring and design §9.1 both DECLARE this exact
   pattern-keyed bound ("a differently-shaped copy `if baseline < 1:` escapes — the un-derivable
   tail INSTRUMENT 0 owns"). It is benign because the escape requires the build to ALREADY be
   correct: the unconditional routed call raises on `0` FIRST, so the `< 1` copy after it is
   unreachable DEAD CODE that can never diverge. The dangerous form — a `< 1` copy that REPLACES
   routing — is caught by the spy (TC-E, 2 red). So the surviving build cannot produce the #290
   divergence. Allowlist-the-safe holds: one real site (`:430`), no allowlist needed today; a future
   legit `not <name>: raise` must be allowlisted with a reason. Honest bound, correctly scoped.
2. **F `_degrade_reflects_core_drop` accepts EITHER an `AssertionError` OR the seam's absence as
   "reflected."** VERDICT: **SOUND.** A `_degrade` that always raised `AssertionError` would fail
   its own positive control (`_degrade_derivation_includes(seam)` calls `_degrade` in a HEALTHY
   context and does not catch `AssertionError`), so the both-way structure holds. Not exploitable.
3. **Reviser's scratch dir `/home/ejprice/scratch-reviser-fh` + my `/home/ejprice/scratch-delta-fh`
   left in place** (both `scratch_copy.sh` copies, disposable by #140; `rm -rf` was permission-denied
   to me). Flagging for cleanup — neither touched the main tree.
4. **Sibling RED contracts show mypy errors** (other cycles' unbuilt symbols — `test_auth_composition`,
   `test_ast_reach_helpers`, `test_refusal_observes_effect`, `test_mutating_set_derivation`). Not
   introduced by F/H; raised per scope law, operator owns whether it matters at this checkpoint.

## Satisfiability (C-DEF receipt — independently reproduced)

Reference build (my own, not the reviser's edits) in provenance-asserted scratch:
```
=== F contract (satisfiability) ===   23 passed in 0.55s
=== H contract (satisfiability) ===   12 passed in 0.13s   (test_wrong_builds 4 + test_harness_guards 8)
```
Both go 0-failed against a known-correct build. After ALL mutation experiments, a full restore +
re-run gives **35 passed** (23 + 4 + 8) — proving the restores are byte-clean and no experiment
leaked. RED-at-HEAD honesty (`3b708e5`, no build): F **21 failed, 2 passed** (the 2 green = the two
HEAD positive controls); H **3 failed, 1 passed** — RED for the right reason
(`AttributeError: module 'loremaster.store' has no attribute '_txn_coroutines'` /
`ModuleNotFoundError: No module named '_harness_guards'`, and the anti-dup naming `:430`).

## P4 — author-claim verification (reviser-fh)

Reproduced independently, all confirmed: F 23-passed satisfiability, F WB7 4-red / WB8 2-red, H
two-copies 3-red, the ∀-drop parametrisation `[run_query, execute_transaction,
execute_read_transaction]` (doors) and `[bootstrap_session, execute_read_transaction,
execute_transaction, run_query]` (wide). The reviser UNDER-claimed nothing material; its LEG-A /
LEG-B split and the "WB8 dies on LEG B, LEG A is the future-seam backstop" analysis reproduce
exactly (MR-W2b). One SHARPENING beyond the reviser's report: I built TWO NEW different-seam
partials (not just re-running WB7/WB8), proving the ∀ covers EVERY member, and drove the leg-5
meta-recursion on production truth (add a member → matrix grows AND stale caller reddens).

---

## Probe-record (commands + real output; instruments pasted per brief-base §1)

### Provenance (#140)
```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch-delta-fh
  loremaster  -> /home/ejprice/scratch-delta-fh/loremaster/loremaster/__init__.py
$ cd /home/ejprice/scratch-delta-fh/loremaster && uv run python -c "import loremaster; print(loremaster.__file__)"
/home/ejprice/scratch-delta-fh/loremaster/loremaster/__init__.py
```

### F + H wrong-build sweep (`uv run python delta_probe.py`)
```
== reference build (control) ==
### REFERENCE F                        EXPECT=green 23p/0f  SURVIVED (green)
### REFERENCE H                        EXPECT=green 4p/0f  SURVIVED (green)
== F wrong builds ==
### WB7 store_seams route rq/hardcode2 EXPECT=red   19p/4f  caught (4 red)
### WB-NEW store_seams hardcode ERT    EXPECT=red   21p/2f  caught (2 red)
### WB8 _degrade route rq+bs/hardcode2 EXPECT=red   21p/2f  caught (2 red)
### WB-NEW _degrade hardcode ERT only  EXPECT=red   22p/1f  caught (1 red)
== H wrong builds ==
### H TC-A helper+inline, no route     EXPECT=red   1p/3f  caught (3 red)
### H TC-B routes AND keeps inline     EXPECT=red   2p/2f  caught (2 red)
```

### H deep probe — anti-dup is load-bearing + the declared bound (`uv run python delta_probe_h.py`)
```
### TC-C routes-first + dead `not baseline` copy      3p/1f  spy_red=0 antidup_red=1  -> caught
### TC-D routes-first + dead `baseline < 1` copy      4p/0f  spy_red=0 antidup_red=0  -> SURVIVES (declared bound; behaviourally correct)
### TC-E `baseline < 1` REPLACES routing (no route)   2p/2f  spy_red=2 antidup_red=0  -> caught
```

### Leg-5 meta-recursion (add a member to production truth)
```
=== MR-1  door parametrisation GROWS (collect-only) ===
  ...test_dropping_ANY_door_..._reddens_store_seams[execute_batch]
  ...test_dropping_ANY_door_..._reddens_seam_bindings[execute_batch]
=== MR-2a LIVE core → door coverage pin GREEN (1 passed)
=== MR-2b STALE core → door coverage pin REDDENS:
  AssertionError: the door ∀-drop reach ['execute_batch','execute_read_transaction','execute_transaction','run_query']
                  has drifted from the live core's door filter ['execute_read_transaction','execute_transaction','run_query']
=== MR-W1 wide parametrisation GROWS: ...test_dropping_ANY_wide_seam_..._reddens_the_degrade_derivation[execute_batch]
=== MR-W2a LIVE _degrade → LEG-A GREEN (1 passed)
=== MR-W2b STALE hardcoded _degrade → LEG-A test_the_degrade_set_is_exactly_the_wide_core_bound_in_tasks FAILS (divergence w/o drop)
```

### Instruments (durable): reference build edits, verbatim
`delta_probe.py` / `delta_probe_h.py` live at `/home/ejprice/scratch-delta-fh/` (disposable scratch —
cite the bodies here, not the path). The reference build I graded against:
```python
# loremaster/loremaster/store/__init__.py (was EMPTY)
_SEAM_MODULE = "loremaster.store._txn"
def _txn_coroutines() -> dict[str, Callable[..., Any]]:
    from loremaster.store import _txn
    return {n: v for n, v in vars(_txn).items()
            if inspect.iscoroutinefunction(v) and getattr(v, "__module__", None) == _SEAM_MODULE}

# scripts/forgery_door_sweep.py::store_seams — route through the shared core
    from loremaster.store import _txn_coroutines
    seams = {}
    for name, value in _txn_coroutines().items():
        if name.startswith("_"): continue
        if _CALLER_STATEMENT_PARAMETER in inspect.signature(value).parameters: seams[name] = value
    return seams

# scripts/forgery_door_sweep.py::seam_bindings — gain seams= (default = door subset)
def seam_bindings(*, package=_DEFAULT_PACKAGE, seams: dict[...]|None=None):
    if seams is None: seams = store_seams()
    by_identity = {id(fn): n for n, fn in seams.items()}
    ...

# loremaster/tests/test_blocks_edge.py::_degrade_every_STORE_seam — route BY IDENTITY, import nothing from scripts/
    from loremaster.store import _txn_coroutines
    core = _txn_coroutines(); by_identity = {id(fn): name for name, fn in core.items()}
    for attribute, value in list(vars(tasks_module).items()):
        seam_name = by_identity.get(id(value))
        if seam_name is None: continue
        monkeypatch.setattr(tasks_module, attribute, replacement, raising=True); patched.append(seam_name)
    assert "run_query" in patched ...; assert "bootstrap_session" in patched ...

# scripts/_harness_guards.py (NEW)
def refuse_vacuous_baseline(measured_count: int, *, cause_hint: str, interpreter: str) -> None:
    if measured_count: return None
    raise SystemExit(f"the baseline collected NOTHING ... {cause_hint} ... {interpreter} -m pytest ...")

# scripts/wrong_builds.py::main — inline `if not baseline: raise SystemExit(...)` REPLACED by:
    refuse_vacuous_baseline(baseline, cause_hint=tail, interpreter=repr(sys.executable))
```
The surviving/killed wrong-build bodies are the `WB7`/`WB8`/`SS_NEW`/`DEG_NEW`/`TC-*` string patches
in `delta_probe.py` / `delta_probe_h.py` (each restores from a `.refbuild/` snapshot, applies one
patch, runs the contract, parses failed node ids).

## VERDICT: CONTRACT SUFFICIENT (F/#279 and H/#290)

The revision TRULY closes each original wrong build (WB7, WB8-BLOCKER, H two-copies-BLOCKER —
independently rebuilt and reddened), closes TWO NEW different-seam partials I built to test the ∀
covers every member, and OPENED no new genuine-defect wrong build (the r5 lesson): the sole survivor
routes correctly and carries dead code — the contract's own declared, benign bound. Both guards'
reach is DERIVED and a CHECKED variable, proven by mutating production truth (leg-5). No missing pin.
