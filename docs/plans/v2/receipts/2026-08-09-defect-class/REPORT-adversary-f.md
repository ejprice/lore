brief-base v10 read
brief project v7 read

# REPORT-adversary-f — contract adversary for the ONE store-seam derivation (#279 / INSTRUMENT F / F5)

Target contract: `loremaster/tests/test_store_seam_one_derivation.py` (contract-f, HEAD `e1dfa14`).
Shared-helper under test: `loremaster.store._txn_coroutines` (unbuilt) routed by
`forgery_door_sweep.store_seams`/`seam_bindings` and `test_blocks_edge._degrade_every_STORE_seam`.

## SUMMARY

- **VERDICT: CONTRACT INSUFFICIENT** — one concrete missing pin (below). The contract is *strong*
  on gross routing-not-sharing; it has an ∀-quantifier hole on partial private copies.
- **P1 headline — a wrong build SURVIVES the contract:** two *partial-route* builds pass all 14
  pins (`WB7` store_seams, `WB8` _degrade) — they route the seams the mutation happens to drop
  (`run_query` / `run_query`+`bootstrap_session`) and keep **private hardcoded copies of the other
  doors**. `_degrade` (WB8) has NO consistency backstop, so this is a silent hole.
- **Contract CATCHES** (empirically): full private-copy `store_seams` (WB1), routing-not-sharing
  `store_seams` (WB2), **routing-not-sharing `_degrade` (WB3)**, DOOR-not-WIDE helper (WB4), no-op
  "helper present, all callers private" (WB5), and a naive partial route that KeyErrors (WB6).
- **MISSING PIN:** the sharing mutation-proof must be ∀ over the seam set. Parametrise the drop
  over ALL `_DOOR_SEAMS` (store_seams/seam_bindings) and ALL of `_degrade`'s wide set
  (`run_query, execute_transaction, execute_read_transaction, bootstrap_session`); **and/or** add a
  `_degrade` set-consistency pin (`set(_degrade) == core seams bound in loremaster.tasks`, live) —
  `_degrade` is the only caller with no such backstop. Defect it catches: WB7/WB8.
- **C-DEF satisfiability RE-VERIFIED independently:** reference build → **14 passed** (contract-f's
  claim reproduces). RED baseline RE-VERIFIED: **12 failed, 2 passed**, red for the right reasons.
- **Fixture constants verified** at HEAD (door/wide/tasks-binding sets all accurate).
- Packages considered: none — pure introspection contract (stdlib `inspect`/`contextlib`, pytest
  MonkeyPatch). Reference/wrong builds use stdlib `inspect` only. No mechanism specified.
- Graded: `e1dfa14` · HEAD-at-report: `e1dfa14` · SAME.
- Provenance (#140): `loremaster.__file__ = /home/ejprice/scratch-adversary-f/loremaster/loremaster/__init__.py` (isolated, asserted).
- Receipt pointers: probe harness §"Probe record" (pasted verbatim); reach table §P1c; quantifier
  table §P1b; builder flags §Flags.

---

## P1 — did any wrong build survive the contract? (the headline)

**Method (empirical, all in an isolated provenance-asserted scratch copy):** built the reference
implementation contract-f's handoff describes, ran the contract (14 passed), then patched in a
series of wrong builds and re-ran. The harness (`adversary_probe.py`) restores from a saved
reference before each variant and parses pytest's summary + failed node ids. Full output is pasted
in §"Probe record".

| build | what it does | contract verdict | correct? |
|---|---|---|---|
| REFERENCE | all three callers route through `_txn_coroutines()` | **14 passed** | ✅ this IS a correct build (satisfiability) |
| WB1 | `store_seams` privately walks `vars(_txn)` (looks-DRY) | 2 failed | caught ✓ |
| WB2 | `store_seams` calls the core then IGNORES it, re-walks `_txn` | 2 failed | caught ✓ |
| WB3 | `_degrade` privately walks `vars(loremaster.tasks)` (HEAD shape) | 2 failed | caught ✓ (the routing-not-sharing case the brief flags) |
| WB4 | helper returns the DOOR subset, not the WIDE superset | 5 failed | caught ✓ |
| WB5 | helper present, ALL callers private (no-op fix / decoration) | 4 failed | caught ✓ |
| WB6 | `store_seams` reads `core["run_query"]` then hardcodes 2 doors | 2 failed | caught ✓ (KeyErrors on the drop) |
| **WB7** | `store_seams` routes `run_query` DEFENSIVELY, **hardcodes 2 doors** | **14 passed** | ❌ **SURVIVES** |
| **WB8** | `_degrade` routes `run_query`+`bootstrap_session`, **hardcodes 2 doors** | **14 passed** | ❌ **SURVIVES** |

**The surviving builds are partial "routing is not sharing" (CLAUDE.md #102/#120).** They read the
shared core for exactly the seam(s) the mutation drops, and keep private copies of the rest. The
mutation never drops those others, so nothing tests whether they route.

- **WB7 (store_seams)** — the `test_store_seams_is_exactly_the_public_statement_filter_of_the_core`
  consistency pin recomputes the expected door set from the LIVE core each run and checks
  `set(doors)==filter(core)` + `doors[name] is core[name]`. So store_seams's OUTPUT is forced to
  track the core: WB7 cannot ship a *wrong* door set undetected (any divergence reddens that pin).
  WB7 therefore demonstrates the mutation-proof's **stated claim is over-broad** (its docstring
  §"WHY THE MUTATION PROOF IS THE LOAD-BEARING TEST" says it "tells DRY from looks-DRY" — WB7 is
  looks-DRY for 2 of 3 doors and passes) but is *backstopped* against a silent defect. Residual, not
  the blocker.
- **WB8 (_degrade)** — `_degrade` has **NO consistency pin**. Its only pins are the two per-seam
  mutation pins (drop `run_query`, drop `bootstrap_session`) + their positive controls. So WB8's
  hardcoded `execute_transaction`/`execute_read_transaction` are exempt from the sharing proof
  *silently and permanently*. Consequences, both real:
  1. **#279 re-opens on the `_degrade` side.** A future 4th public statement-bearing coroutine bound
     in `loremaster.tasks` is picked up by a routed `store_seams`/`_degrade` automatically, but WB8's
     hardcoded `_degrade` structurally ignores anything beyond its 4 named seams — the two
     derivations disagree about the new seam, which is the exact defect #279 exists to prevent, and
     no `_degrade` pin catches it.
  2. **The byte-diff forgery pins break silently.** `_degrade_every_STORE_seam` is consumed by
     `test_a_FAILED_traversal_NEVER_renders_as_a_COMPLETE_answer` et al. (test_blocks_edge.py
     `_seed_then_degrade`), whose whole premise is *"break EVERY store seam"*. A `_degrade` that
     misses a seam the ledger read rides can leave a live door, serving healthy bytes over a broken
     world — a false clear — and the contract's `_degrade` pins would not see it because they only
     drop `run_query`/`bootstrap_session`.

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode)

| # | invariant the contract pins | ∀ or guarded | receipt |
|---|---|---|---|
| 1 | `_txn_coroutines` exists, non-empty, coroutines-only, all public seams present (fail-closed on empty) | **∀** over `vars(_txn)` (recomputed live) | door-only helper `WB4` reddens 5 pins (built + run) |
| 2 | door subset == public+`statement` filter of the core, **same objects** | **∀** over doors (set-eq + identity, recomputed live) — but this is *consistency*, not *sharing* | passes for looks-DRY `WB1` (consistency can't tell DRY from looks-DRY — by design) |
| 3 | `seam_bindings(seams=…)` builds from either set; wide includes `bootstrap` in tasks, door does not | guarded by named seams (`bootstrap_session`, `run_query`) | `WB4` reddens `test_wide_bindings_…` |
| 4 | **store_seams / seam_bindings ROUTE through the shared core (sharing≠routing)** | **GUARDED by `{run_query}`** | ✅ door-build: `WB1/WB2/WB5` reddened by the run_query drop. ❌ **surviving wrong build `WB7`** routes run_query, hardcodes the other doors → passes (backstopped by pin #2, so residual) |
| 5 | **_degrade ROUTES through the shared WIDE core (sharing≠routing)** | **GUARDED by `{run_query, bootstrap_session}`** | ✅ door-build: `WB3/WB5` reddened. ❌ **surviving wrong build `WB8`** routes those two, hardcodes `execute_transaction`/`execute_read_transaction` → passes, **no consistency backstop** → BLOCKER |

Rows 4 & 5 are the guarded invariants; row 5's surviving wrong build (`WB8`) is the missing pin.
Proof the fix closes it (`fix_demo.py`, §"Probe record"): dropping `execute_transaction` (a seam the
shipped mutation never drops) from the core is REFLECTED by the reference build (correct-build
control) and NOT reflected by WB7 — so a ∀-parametrised drop fails WB7/WB8; the shipped
`run_query`-only drop does not.

## P1c — REACH TABLE (per instrument: reach DERIVED? coverage a checked variable? effect vs proxy? one source proven by mutation?)

| instrument | reach = set of sites | DERIVED or hand-list | coverage checked? | effect vs proxy | one-source proven by MUTATION | verdict | leg |
|---|---|---|---|---|---|---|---|
| `_txn_coroutines()` (the derivation) | coroutines defined in `_txn` | DERIVED (`iscoroutinefunction`+`__module__`) | yes — non-empty + all-public + coroutines-only pins | EFFECT (the mapping itself) | it IS the one source | **SAFE** | empirical (`WB4`) |
| `store_seams` door filter | public+`statement` filter of core | DERIVED | yes — consistency pin (set-eq+identity, live) | EFFECT | proven **for `run_query` only** | ∀-gap (residual: pin #2 backstops output) | empirical (`WB7`) |
| `seam_bindings` scan | imported `loremaster.*` attrs holding a core seam, **by identity** | DERIVED (by identity) | partial — wide-vs-door pin; the file states its own reach bound | EFFECT | proven **for `run_query` only** | ∀-gap | empirical |
| **`_degrade` derivation** | core seams bound in `loremaster.tasks` | DERIVED in reference (via `seam_bindings`) | **NO set-consistency pin — only 2 per-seam drops** | EFFECT | proven **for `{run_query, bootstrap_session}` only** | **MISSING PIN (`WB8`)** | empirical (`WB8`) |
| mutation machinery `_rebind_everywhere` / `_core_dropping` | every `sys.modules` attr that IS the fn (by identity) | DERIVED (by identity) | yes — landing assert (#194) + `TestTheMutationProofDiscriminates` positive control | EFFECT (re-reads canonical attr, byte of result) | n/a — it is the prober | **SAFE** (the prober itself is sound) | construction + ran the contract's own control |

The one instrument whose reach over *seams* is a **hand-list, not a checked variable**, is the
sharing mutation proof: it drops `run_query` (and `bootstrap_session` for `_degrade`), so seams
outside that list are exempt from the sharing proof silently — the exact shape of INSTRUMENT 0's
reach attack (`a guard certifies only the sites it EXECUTES over; its reach is a hidden constant`).

## MISSING PIN (the test that should exist + the defect it catches)

**Test that should exist** — make the sharing proof ∀ over the seam set:

```python
# store_seams / seam_bindings side — parametrise over EVERY door, not just run_query
@pytest.mark.parametrize("door", sorted(_DOOR_SEAMS))
def test_dropping_ANY_door_from_the_core_reddens_store_seams(self, door):
    assert door in fds.store_seams()                       # positive control
    with _core_dropping(door):
        assert door not in fds.store_seams()               # every door must route

# _degrade side — either parametrise over its FULL wide set …
_DEGRADE_WIDE_SET = _DOOR_SEAMS | {"bootstrap_session"}    # the 4 seams tasks binds
@pytest.mark.parametrize("seam", sorted(_DEGRADE_WIDE_SET))
def test_dropping_ANY_wide_seam_reddens_the_degrade_derivation(self, seam):
    assert _degrade_derivation_includes(seam)              # positive control
    assert _degrade_reflects_core_drop(seam)

# … OR (stronger — closes the missing-backstop) a _degrade set-consistency pin, recomputed live:
def test_degrade_set_is_exactly_the_wide_core_bound_in_tasks(self):
    core = _load_core()()
    expected = {b.seam_name for b in fds.seam_bindings(package="loremaster", seams=core)
                if b.module_name == "loremaster.tasks"}
    with pytest.MonkeyPatch.context() as mp:
        assert set(_load_degrade()(mp, _inert_seam_replacement)) == expected
```

**Defect it catches:** a `store_seams`/`_degrade` that routes the currently-tested seam(s) through
the shared core but keeps **private hardcoded copies of the other doors** (WB7/WB8). For `_degrade`
— which has no consistency backstop — such a build passes the whole contract today, would silently
**miss a future 4th store seam** (re-opening #279 on exactly the axis the instrument exists to
close), and would leave a **live store door** the byte-diff forgery pins assume is degraded.

## Fixtures must discriminate (P2) — perturbation + correct-build control

- **Perturbation of the mutation's load-bearing seam** (`run_query` → `execute_transaction`), a seam
  the shipped mutation never drops: on the REFERENCE build store_seams reflects the drop
  (`reflected=True` — correct-build control); on WB7 it does NOT (`reflected=False` — the private
  copy). **Pair proven** (`fix_demo.py`, §"Probe record"): the perturbed pin passes a correct build
  and fails the wrong build → the ∀-parametrised pin is real, not botched.
- **Fixture constants are accurate**, verified by live introspection at HEAD `e1dfa14`:
  public coroutines = `{run_query, execute_transaction, execute_read_transaction, retry_on_conflict,
  bootstrap_session}` (= `_ALL_PUBLIC_SEAMS`); door subset = first three (= `_DOOR_SEAMS`);
  `loremaster.tasks` binds `{run_query, execute_transaction, execute_read_transaction,
  bootstrap_session}` (NOT `retry_on_conflict`) → wide-only-in-tasks seam = `bootstrap_session`
  (= `_DEGRADE_WIDE_ONLY_SEAM`). `compose`/`signin_credentials`/`is_connection_error` are
  non-coroutines (the `test_the_core_holds_coroutines_only…` oracle is grounded).
- **Small-N / monoculture:** the mutation always operates on a real 5-element core with distinct
  door vs wide-only members, so `len()`≡`sum()` collapse and value-monoculture do not apply. The one
  genuine monoculture is the **seam the mutation drops** (`run_query`) — that IS the ∀-gap above.

## RED honesty (P7) + author-claim verification (P4)

- **RED baseline reproduced on the real tree** (scratch, HEAD `e1dfa14`, no helper): **12 failed, 2
  passed** — matches contract-f exactly. Red for the right reasons: `AttributeError: module
  'loremaster.store' has no attribute '_txn_coroutines'` (the helper) and `TypeError` (`seams=`
  absent). The 2 green are the two designed positive controls (`test_the_door_subset_is_the_known_
  three_doors` oracle, `test_the_mutation_technique_moves_a_router_and_not_a_private_clone` probe
  control).
- **Satisfiability reproduced independently:** reference build (helper + routed callers) → **14
  passed**. contract-f's C-DEF claim holds; I did not need contract-f's report to reach it.
- **Mutation machinery is sound** (P5 — can the fake fail?): `TestTheMutationProofDiscriminates`
  (run, green) proves `_rebind_everywhere` moves a router and not a private clone; `_core_dropping`
  carries a #194 landing assert. The prober is not decoration.

## P6b — deleted/replaced-code virtues (independent enumeration, then diff)

The `_degrade_every_STORE_seam` rewrite REPLACES the HEAD private walk of `vars(loremaster.tasks)`.
Enumerated the HEAD behaviours from source *before* reading contract-f's handoff:
1. degrades EVERY coroutine bound in `loremaster.tasks` defined in `_txn` (`run_query,
   execute_transaction, execute_read_transaction, bootstrap_session`);
2. fail-closed `assert "run_query" in patched` (vacuity guard);
3. precondition "caller must hold a live connection" (bootstrap_session is in the set);
4. returns `tuple(patched)`.

Diff vs the routed reference: (1) preserved — `seam_bindings(seams=_txn_coroutines())` filtered to
`loremaster.tasks` yields the same 4 seams; (2) preserved AND strengthened (adds `assert
"bootstrap_session" in patched`); (3) preserved (bootstrap still degraded); (4) preserved. **No
virtue dropped** *by the reference build*. ⚠ But virtue (1) — degrade EVERY seam — is exactly the
completeness the byte-diff forgery pins depend on, and it is the ∀-property the missing pin fails to
guard: WB8 preserves (2)/(3)/(4) and quietly breaks (1) for a future seam. This is why the missing
pin matters beyond #279 hygiene.

## Flags to lead / builder (scope law — surfaced, not silently dropped)

- **Builder fragility (not a contract defect):** `loremaster/tests/conftest.py` puts the *tests*
  dir on `sys.path`, not `scripts/`. A routed `_degrade` that does `import forgery_door_sweep`
  (as contract-f's handoff reference does) only resolves when `test_store_seam_one_derivation.py`
  (which inserts `scripts/`) is collected in the same session; a full/isolated `test_blocks_edge`
  run would `ImportError`. The cleaner build routes `_degrade` through `_txn_coroutines()` directly
  (iterate the core, patch each name bound in `tasks` by identity) and imports NOTHING from
  `scripts/`. Recommend the builder take that form; otherwise add a `scripts/` `sys.path` insert to
  `conftest.py` and pin it.
- **Mutation-proof docstring over-claims** (TRUST/honesty): the file's §"WHY THE MUTATION PROOF…"
  says the mutation "tells DRY from looks-DRY". True only for the dropped seam(s). WB7/WB8 are
  looks-DRY for the undropped doors and pass. If the missing pin is adopted the claim becomes true;
  otherwise the docstring should scope it ("for run_query/bootstrap_session").
- **The design doc anticipated this and chose wrong** (design §INSTRUMENT F "Mutation proof"):
  it prescribes mutating the shared CORE so *both sides redden together* (e.g. `core → {}`), a
  ∀-reddening mutation; contract-f implemented a per-seam DROP instead and reasoned an ADD gives "no
  extra discrimination" (contract-f §2). That reasoning is falsified by WB7/WB8: an ADD (or a
  ∀-parametrised DROP) is precisely what catches the partial private copy the single-seam DROP
  misses.

---

## Probe record (commands + real output; the instruments are `adversary_probe.py` / `fix_demo.py`, pasted below)

### Provenance (#140) — scratch copy runs its OWN code
```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch-adversary-f      # (uv sync --all-packages, asserts provenance)
scratch copy READY: /home/ejprice/scratch-adversary-f
  loremaster  -> /home/ejprice/scratch-adversary-f/loremaster/loremaster/__init__.py
$ cd /home/ejprice/scratch-adversary-f/loremaster && uv run python -c "import loremaster; print(loremaster.__file__)"
/home/ejprice/scratch-adversary-f/loremaster/loremaster/__init__.py
```

### RED baseline (unmodified scratch, HEAD e1dfa14)
```
$ cd /home/ejprice/scratch-adversary-f/loremaster && uv run python -m pytest tests/test_store_seam_one_derivation.py -q
E  AttributeError: module 'loremaster.store' has no attribute '_txn_coroutines'   # (12 pins)
12 failed, 2 passed in 1.21s
```

### Fixture-constant introspection (real tree)
```
PUBLIC COROUTINES in _txn: ['bootstrap_session','execute_read_transaction','execute_transaction','retry_on_conflict','run_query']
DOOR subset (public+statement): ['execute_read_transaction','execute_transaction','run_query']
WIDE-only public: ['bootstrap_session','retry_on_conflict']
loremaster.tasks binds from _txn: ['bootstrap_session','execute_read_transaction','execute_transaction','run_query']
compose/signin_credentials/is_connection_error: iscoro=False (all three)
```

### Wrong-build sweep (`uv run python adversary_probe.py`)
```
### REFERENCE (correct build)        EXPECT=green OBSERVED=GREEN | 14 passed
### WB1 store_seams private-walk      EXPECT=red   OBSERVED=RED   | 2 failed  (reddens_store_seams, reddens_seam_bindings)
### WB2 store_seams call-then-ignore  EXPECT=red   OBSERVED=RED   | 2 failed  (reddens_store_seams, reddens_seam_bindings)
### WB3 _degrade private-walk (HEAD)  EXPECT=red   OBSERVED=RED   | 2 failed  (reddens_the_degrade_derivation, reddens_the_degrade wide-only)
### WB4 helper = DOOR subset          EXPECT=red   OBSERVED=RED   | 5 failed  (wide-set, non-empty, wide-vs-door bindings, both degrade drops)
### WB5 no-op: all callers private    EXPECT=red   OBSERVED=RED   | 4 failed  (all 4 mutation pins)
### WB6 partial route (core[..])      EXPECT=?     OBSERVED=RED   | 2 failed  (KeyError on the run_query drop)
### WB7 partial-route DEFENSIVE       EXPECT=?     OBSERVED=GREEN | 14 passed   <-- SURVIVES (store_seams; backstopped by consistency pin)
### WB8 partial-route _degrade        EXPECT=?     OBSERVED=GREEN | 14 passed   <-- SURVIVES (no _degrade consistency pin = BLOCKER)
```

### Fix proof — parametrised drop over `execute_transaction` (`uv run python ../fix_demo.py`)
```
REFERENCE build: 'execute_transaction' in store_seams() = True
  after dropping 'execute_transaction' from the shared core: reflects = True    # correct-build control passes
WB7 build:       'execute_transaction' in store_seams() = True
  after dropping 'execute_transaction' from the shared core: reflects = False   # private copy — the ∀ pin CATCHES it
```

### Instruments (durable — pasted per brief-base §1; live at `/home/ejprice/scratch-adversary-f/{adversary_probe.py,fix_demo.py}`)

`adversary_probe.py` restores 3 files from `.refsave/` before each variant, applies the variant's
string patches, runs the contract, parses `N passed/failed` + failed node ids. Variants WB1–WB8 are
the `*_BODY` string patches shown in §P1's table (full source in the scratch file). `fix_demo.py`
imports the contract's own `_core_dropping` and drops `execute_transaction` (a seam the shipped
mutation never drops), printing whether `store_seams()` reflects it — the paired correct-build /
wrong-build discrimination for the proposed ∀ pin. Reference build (my satisfiability instrument),
verbatim:

```python
# loremaster/loremaster/store/__init__.py  (was empty)
_SEAM_MODULE = "loremaster.store._txn"
def _txn_coroutines() -> dict[str, Callable[..., Any]]:
    from loremaster.store import _txn
    return {n: v for n, v in vars(_txn).items()
            if inspect.iscoroutinefunction(v) and getattr(v, "__module__", None) == _SEAM_MODULE}

# scripts/forgery_door_sweep.py::store_seams — walk the shared core instead of vars(_txn)
    from loremaster.store import _txn_coroutines
    seams = {}
    for name, value in _txn_coroutines().items():
        if name.startswith("_"): continue
        if _CALLER_STATEMENT_PARAMETER in inspect.signature(value).parameters: seams[name] = value
    return seams

# scripts/forgery_door_sweep.py::seam_bindings — gain seams= (default = door subset)
def seam_bindings(*, package=_DEFAULT_PACKAGE, seams=None):
    if seams is None: seams = store_seams()
    by_identity = {id(fn): n for n, fn in seams.items()}
    ...

# loremaster/tests/test_blocks_edge.py::_degrade_every_STORE_seam — route through the shared helper
    from loremaster.store import _txn_coroutines
    import forgery_door_sweep as _fds
    for binding in _fds.seam_bindings(package="loremaster", seams=_txn_coroutines()):
        if binding.module_name != "loremaster.tasks": continue
        monkeypatch.setattr(tasks_module, binding.attribute, replacement, raising=True)
        patched.append(binding.seam_name)
    assert "run_query" in patched ...
    assert "bootstrap_session" in patched ...
```

### Appendix — the two SURVIVING wrong builds, verbatim (the load-bearing instruments)

WB7 replaces `store_seams`'s body; WB8 replaces `_degrade`'s routing loop. Both leave the two
`assert … in patched` lines intact (WB8) / the door filter intact (WB7). Each patched into a fresh
copy of the reference build; each ran the contract → **14 passed**.

```python
# WB7 — store_seams: routes run_query DEFENSIVELY, PRIVATE hardcoded copies of the other 2 doors
    from loremaster.store import _txn_coroutines
    from loremaster.store import _txn
    core = _txn_coroutines()
    seams: dict[str, Callable[..., Any]] = {}
    if "run_query" in core:                       # run_query IS routed (reflects the drop)
        seams["run_query"] = core["run_query"]
    seams["execute_transaction"] = _txn.execute_transaction             # PRIVATE COPY
    seams["execute_read_transaction"] = _txn.execute_read_transaction   # PRIVATE COPY
    return seams

# WB8 — _degrade: routes run_query+bootstrap_session, PRIVATE hardcoded copies of the other 2 doors
    from loremaster.store import _txn_coroutines
    tasks_module = importlib.import_module("loremaster.tasks")
    core = _txn_coroutines()
    patched: list[str] = []
    for name in ("run_query", "bootstrap_session"):        # routed through the shared core
        if name in core and inspect.iscoroutinefunction(getattr(tasks_module, name, None)):
            monkeypatch.setattr(tasks_module, name, replacement, raising=True)
            patched.append(name)
    for name in ("execute_transaction", "execute_read_transaction"):   # PRIVATE hardcoded copies
        monkeypatch.setattr(tasks_module, name, replacement, raising=True)
        patched.append(name)
    # (then the unchanged asserts: "run_query" in patched, "bootstrap_session" in patched — both pass)
```

Both survive because the mutation only ever drops `run_query` (and `bootstrap_session` for
`_degrade`); the hardcoded `execute_transaction`/`execute_read_transaction` are never dropped, so
nothing tests whether they route. Full harness (disposable scratch, cite the bodies above, not the
path): `/home/ejprice/scratch-adversary-f/adversary_probe.py` + `fix_demo.py`.

## VERDICT: CONTRACT INSUFFICIENT

The contract robustly catches gross routing-not-sharing (WB1/WB2/WB3), the wrong-superset helper
(WB4), and the no-op decoration build (WB5) — a genuinely strong sharing proof for the seams it
exercises. It is INSUFFICIENT on ONE axis: the sharing/routing mutation proof is **guarded by
`{run_query}` (store_seams/seam_bindings) and `{run_query, bootstrap_session}` (_degrade), not ∀
over the seam set.** A partial private copy of the undropped doors survives (WB7 store_seams —
backstopped by the consistency pin, a residual; **WB8 _degrade — no backstop, a blocker**). The
missing pin is named above (∀-parametrise the drop, and/or add a `_degrade` set-consistency pin),
the defect it catches is WB8, and the fix is proven to discriminate (correct-build control +
wrong-build catch in `fix_demo.py`).
