brief-base v10 read
brief project v7 read

# REPORT-contract-f — RED contract for the ONE store-seam derivation (#279 / INSTRUMENT F / F5)

## SUMMARY

- state: **done** — RED contract written, confirmed RED, mypy+ruff clean, satisfiability-proven.
- file (new, only writable): `loremaster/tests/test_store_seam_one_derivation.py` (14 tests).
- RED confirmed (real tree, HEAD `e1dfa14`): **12 failed, 2 passed** — the 2 green are the two
  designed positive controls (door-set oracle + probe self-control), 12 red for the right
  reasons (`_txn_coroutines` absent → AttributeError; `seams=` absent → TypeError).
- shared-helper target PINNED (operator ruling F5, placement (b)): `loremaster.store._txn_coroutines`
  — a WIDE superset of every coroutine defined in `loremaster.store._txn`; the DOOR subset is its
  public + `statement`-param filter (`forgery_door_sweep.store_seams`).
- **Satisfiability receipt (C-DEF): 14 passed** against a minimal reference build in an isolated,
  provenance-asserted scratch copy. The scratch build CAUGHT one C-DEF defect in my own contract
  (a bindings pin that was empty on a correct build); fixed and re-proven. Reference patch pasted
  verbatim below (§Reference build) — the instrument is otherwise disposable scratch.
- Packages considered: none — pure test contract (pytest MonkeyPatch + stdlib `inspect`/`contextlib`);
  reference build uses stdlib `inspect` only. No new mechanism specified.
- Graded: e1dfa14 · HEAD-at-report: e1dfa14 · SAME.
- deviations: (1) unbuilt symbol read via `getattr`, not `from … import`, so the RED contract keeps
  the typecheck gate GREEN (rationale in §Decisions). (2) scratch copy left at
  `/tmp/lore-scratch-contract-f` — `rm -rf` sandbox-denied; disposable `/tmp`, not a git worktree.
- decisions-needed: none for this cycle. One downstream note for the BUILDER (§Builder handoff):
  the reference `_degrade` reaches `seam_bindings` (which stays in `scripts/`) via a tests→scripts
  `sys.path` insert; only the DERIVATION moved to production, exactly as F5 ruled.
- receipt pointers: contract file above · reference build §"Reference build" below · per-pin
  wrong-build table §"Fixtures must discriminate".

---

## 1. What the contract pins (14 tests, 5 classes)

Investigation was **lore-first** (`lore_get_symbol`, `lore_read`, `lore_findings`) plus three
grep/direct-read fallbacks, each SAID OUT LOUD: (a) `forgery_door_sweep.store_seams`/`seam_bindings`
are in `scripts/` and not symbol-indexed under that module name — read the file directly; (b)
enumerating `_txn.py`'s coroutine set and `statement` params (rename/shape exhaustiveness — one
missed seam breaks the door filter); (c) `loremaster.tasks`'s `_txn` import block (a config/import
seam). All three are the sanctioned grep cases; no lore friction filed (the tools answered every
symbol-level question; the fallbacks are the documented non-symbol cases).

Verified at HEAD `e1dfa14`, empirically:
- public coroutines in `_txn`: `{run_query, execute_transaction, execute_read_transaction,
  retry_on_conflict, bootstrap_session}`; door subset (public + `statement`): the first three;
  WIDE\DOOR: `{retry_on_conflict, bootstrap_session}`.
- `loremaster.tasks` binds `{bootstrap_session, execute_read_transaction, execute_transaction,
  run_query}` from `_txn` (NOT `retry_on_conflict`) → `_degrade`'s wide set is the 3 doors +
  `bootstrap_session`; the one element the door filter removes is `bootstrap_session`.

| class | tests | what it pins | red now? |
|---|---|---|---|
| `TestTheOneDerivationExistsAndIsWide` | 4 | `loremaster.store._txn_coroutines` exists, returns a non-empty mapping of `_txn` coroutines, is the WIDE set (bootstrap/retry present, not doors), coroutines-only (no `compose`/`signin_credentials`) | RED |
| `TestTheDoorSubsetIsDerivedFromTheCore` | 3 | `store_seams()` == the public+`statement` filter of the core; DOOR ⊆ WIDE; door set == the known three (oracle) | 2 RED, 1 GREEN (oracle) |
| `TestSeamBindingsCanBuildFromEitherSet` | 2 | `seam_bindings(seams=…)` accepts an explicit set; the WIDE set yields a `bootstrap_session` binding in `loremaster.tasks`, the default DOOR set does not | RED (TypeError) |
| `TestSharingProvenByMutation` | 4 | **the load-bearing discriminator** — drop a seam from the shared core → `store_seams`, `seam_bindings` (default), and `_degrade` (door seam AND wide-only seam) all reflect it | RED |
| `TestTheMutationProofDiscriminates` | 1 | positive control ON THE PROBE — the mutation technique moves a router and NOT a private clone | GREEN |

**Why the mutation proof is the only sharing test** (CLAUDE.md "PROVE SHARING BY MUTATION;
ROUTING IS NOT SHARING"): the consistency pins (door == filter of core; DOOR ⊆ WIDE) pass EQUALLY
for one shared helper and for two private copies that merely agree today. Only
`TestSharingProvenByMutation` tells DRY from looks-DRY: it rebinds the shared function *everywhere
it is referenced* — by identity across `sys.modules`, the same technique `seam_bindings` itself
uses — so it reaches a caller whether it imports the helper at module level (a rebindable global)
or re-imports it per call (which re-reads the patched canonical `loremaster.store` attribute). A
caller that references the helper nowhere is unreached, stays green under the mutation, and is
FAILED. Its own positive control (`TestTheMutationProofDiscriminates`) proves that discrimination
is real, so a green mutation pin is not a green light with a filename.

## 2. Fixtures must discriminate — per-pin "what wrong build still passes?"

| wrong build | killed by |
|---|---|
| two derivations that AGREE today (routing-is-not-sharing / looks-DRY) | ONLY the 4 `TestSharingProvenByMutation` pins (consistency pins wave it through) |
| a caller that imports the helper but re-derives locally (routes, doesn't share) | the mutation pins (its output won't reflect the drop) |
| door subset re-walks `_txn` independently of the core | `test_dropping_a_door_from_the_core_reddens_store_seams` |
| helper returns only the DOOR subset (not the WIDE superset) | `test_the_core_is_the_wide_set_not_the_door_subset` + `test_dropping_the_wide_only_seam…` |
| helper walks every NAME in `_txn` (no `iscoroutinefunction`) | `test_the_core_holds_coroutines_only_not_every_txn_name` (`compose`/`signin_credentials` absent) |
| `_degrade` keeps a private copy of the walk | the two `_degrade` mutation pins (door seam + wide-only seam) |
| `seam_bindings` can't build from the wide set | `test_seam_bindings_accepts_a_seams_argument` + the wide-vs-door binding pin |
| the mutation-proof logic itself can't fail a private copy | `test_the_mutation_technique_moves_a_router_and_not_a_private_clone` |

The mutation chose **drop** (not add) deliberately: dropping `run_query`/`bootstrap_session` from
the core reddens BOTH callers cleanly (store_seams loses the door; `_degrade`'s own fail-closed
`assert "<seam>" in patched` fires, or the seam is simply absent — the predicate accepts either).
An ADD would need the synthetic seam bound in `loremaster.tasks` for `_degrade` to see it — a
messier fixture with no extra discrimination.

## 3. Decisions & rationale

- **`getattr`, not `from loremaster.store import _txn_coroutines`** (deviation 1): a RED contract
  that names an unbuilt symbol statically turns the whole `scripts/typecheck.sh` gate RED, and I
  cannot adjudicate it (`pending_contracts.yaml` is out of my writable set; the lead owns it).
  `getattr(loremaster.store, "_txn_coroutines")` is the exact existence check `from … import`
  performs, so the builder exposing the attribute at the package satisfies both — but mypy stays
  GREEN and the RUNTIME test carries the "symbol must exist" requirement. Confirmed: mypy clean,
  and the test reddens NOW with `AttributeError: … has no attribute '_txn_coroutines'`.
- **Cross-tree import** `import forgery_door_sweep as fds  # type: ignore[import-not-found]` mirrors
  the established loremaster/tests idiom (`test_stats.py`, `test_backoff_seam.py`,
  `test_calibration_counting.py` import `scripts/` modules the same way).
- **No implementation written.** Only the new test file. `store_seams`/`seam_bindings`/`_degrade`/
  `loremaster/store` untouched in the real tree.

## 4. Satisfiability receipt (the reference build — INSTRUMENT, pasted verbatim per brief-base §1)

Built in an isolated scratch copy via `./scripts/scratch_copy.sh /tmp/lore-scratch-contract-f`
(provenance asserted: `loremaster.store -> /tmp/lore-scratch-contract-f/…`, so it ran its OWN code,
#140). My contract went **14 passed** against it. The scratch build **caught a real C-DEF defect**
in my first draft — `test_seam_bindings_accepts_a_seams_argument` asserted non-empty bindings but
did not import a binding-holding module, so a correct build returned `()`; fixed by importing
`loremaster.tasks` first, re-proven 14 passed. This is exactly the C-DEF class the satisfiability
receipt exists to catch, caught before any builder saw the contract.

### Reference build

`loremaster/loremaster/store/__init__.py` (was empty):
```python
"""The ``loremaster.store`` package — home of the ONE store-seam derivation (#279)."""
from __future__ import annotations
import inspect
from collections.abc import Callable
from typing import Any

_SEAM_MODULE = "loremaster.store._txn"

def _txn_coroutines() -> dict[str, Callable[..., Any]]:
    """The ONE store-seam derivation: the WIDE superset (every coroutine defined in _txn)."""
    from loremaster.store import _txn
    return {
        name: value
        for name, value in vars(_txn).items()
        if inspect.iscoroutinefunction(value)
        and getattr(value, "__module__", None) == _SEAM_MODULE
    }
```

`scripts/forgery_door_sweep.py::store_seams` — walk the shared core instead of `vars(_txn)`:
```python
    from loremaster.store import _txn_coroutines
    seams: dict[str, Callable[..., Any]] = {}
    for name, value in _txn_coroutines().items():
        if name.startswith("_"):
            continue
        if _CALLER_STATEMENT_PARAMETER in inspect.signature(value).parameters:
            seams[name] = value
    return seams
```

`scripts/forgery_door_sweep.py::seam_bindings` — gain a `seams=` arg (default = door subset):
```python
def seam_bindings(
    *, package: str = _DEFAULT_PACKAGE, seams: dict[str, Callable[..., Any]] | None = None,
) -> tuple[SeamBinding, ...]:
    ...
    if seams is None:
        seams = store_seams()
    by_identity = {id(function): name for name, function in seams.items()}
    ...
```

`loremaster/tests/test_blocks_edge.py::_degrade_every_STORE_seam` — derive via the shared route
(`seam_bindings(seams=_txn_coroutines())` filtered to `loremaster.tasks`), KEEP `assert "run_query"
in patched`, ADD `assert "bootstrap_session" in patched`; `seam_bindings` stays in `scripts/`, so
`_degrade` reaches it with the file's existing tests→scripts `sys.path` idiom.

## 5. Builder handoff (for the F5 build cycle — NOT done here)

- Create `loremaster.store._txn_coroutines` (package-level attribute per operator ruling F5(b)).
- Route `store_seams`, `seam_bindings`, and `_degrade_every_STORE_seam` through it; **reference it
  patchably** (module attribute / call-time re-import), because the mutation pins rebind
  `loremaster.store._txn_coroutines` and every module-level binding of it — a caller that freezes
  the value into a local will fail the sharing proof (correctly: that is a private copy).
- The reference build is MINIMAL (only what makes THIS contract green). The cold audit must re-run
  the FULL `test_blocks_edge` suite (packet 04b-1 closed 8256/0) + `test_forgery_door_sweep.py` +
  the sharing mutation-proof, per INSTRUMENT F / F5 — I did not run those (live-store + closed-file
  scope beyond a contract author's remit; flagged, not silently skipped).

## 6. Flags to operator / lead

- Scratch copy left at `/tmp/lore-scratch-contract-f` (`rm -rf` sandbox-denied). Disposable `/tmp`,
  not a git worktree — safe to `rm -rf` when convenient.
- The design's INSTRUMENT-F escalations (F3/#337 ledger-only; INSTRUMENT-B `_RENDER_DRIVERS`
  retirement) are other cycles' concerns, untouched here.
