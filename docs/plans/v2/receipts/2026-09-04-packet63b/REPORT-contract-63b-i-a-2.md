# REPORT-contract-63b-i-a-2

brief-base v14 read
brief project v7 read

Opus contract author revising the RED contract for packet 63b wave i-a (the F5 runtime root-fix),
per the design §1.9 ADDENDUM (committed 103c661) + REPORT-adversary-63b-i-a.md (INSUFFICIENT).
Base HEAD 103c661, branch feat/surreal-unification. CONTRACT TESTS ONLY (+ a disposable scratch
reference for the C-DEF satisfiability receipt). No git state mutated — the lead commits.

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done**
- deviations: (1) the observer-stub BODY is kept as the RED-until-built verb-observer with an updated
  ★CONTRACT SHAPE★ docstring specifying the §1.9 mechanism (kept `extra_modules` in the HEAD signature
  so the HEAD body compiles; the builder drops it) — so every effect pin REDs for the *right* reason
  (effect None), never a collection/TypeError. (2) `ExemptToken` is a test-side twin in
  `_governed_contract` (constructible at HEAD); production's `governed.ExemptToken` is structurally
  identical and the classifier reads BOTH by attribute (`.name/.statement/.origin`).
- Packages considered: none NEW — the contract is bespoke test substrate; the reference reuses stdlib
  `ast`/`re`/`asyncio`/`pathlib` + `pyyaml` (already a dep) over the live store. The design §6 already
  dispositioned every production mechanism (`bespoke`/`keep_with_trigger`); I add no production mechanism.
- Reuse ledger: 3 new test-substrate symbols, all dispositioned (§"DRY LEDGER" below).
- Graded: 519c0bb (the 1st contract the adversary graded) → revised against §1.9 · HEAD-at-report:
  103c661 · SAME (my edits are uncommitted working-tree changes on 103c661).
- decisions-needed: none. Two C-DEFs I FOUND during the satisfiability build are FIXED in the contract
  (below); no open forks.
- pointers: the 6 changes §"THE SIX §1.9 REVISIONS"; RED-at-HEAD §"RECEIPT A"; satisfiability
  §"RECEIPT B"; the 2 C-DEF fixes §"C-DEF FIXES FOUND"; the reference instrument §"REFERENCE BUILD".

---

## THE SIX §1.9 REVISIONS (each closes a named adversary finding)

1. **MISSING PIN #1 — classifier RUNS a label frame's effect predicate ∀ label frame** (adversary
   P1b/MISSING PIN #1). New class `TestTheClassifierRunsALabelFramesEffectPredicate`: the concrete
   `_reinforce`+{importance,scope} seizure → `classify … is False` (positive control {importance}-only
   → True), plus a GENERALISED ∀-label-frame method with a per-entry self-checking rejected effect.
   Catches `if observed.label is not None: return True` (the `WB-label-ignores-effect` door, 30/30 green).
2. **MISSING PIN #2 — governed_populations() reach is a CHECKED VARIABLE** (adversary P1c/MISSING PIN #2).
   `governed_populations(schema_source=…)` gains a synthetic-source param; new pin
   `test_the_population_derivation_reach_is_a_checked_variable` feeds a synthetic `surreal_schema` where a
   new `_widget_statements` CALLS `_governed_field_specs` + a governed-endpoint `_define_relation_table` →
   the set GROWS. Also pins the §1.9-item-2/F-TRAP-1 correction (an emitter with a DIRECT
   `owner_principal` but no `_governed_field_specs` call is NOT included). Catches `frozenset({memory})`.
3. **F-TRAP-3 C-DEF — the ensure_ready oracle is CONSTRUCTED** (§1.9 item 4). DELETED
   `_memory_ddl_object_names()` (the DDL-text regex); added `SchemaSnapshot` + `schema_snapshot_from_info`
   + `ObservedEffect.schema_after`; the oracle is the engine's rendering of `generate_memory_ddl(dim)` on
   a VIRGIN harness DB (session-cached `ensure_ready_oracle` fixture keyed by dim); `_effect_ensure_ready`
   = `schema_after == oracle` (dict equality, NO regex) AND no rows moved; non-vacuity pin (one extra
   field → snapshot ≠ oracle → RED).
4. **ExemptToken shape** (§1.9 item 3c). `ObservedWrite.exempt: str | ExemptToken | None`; leg-4 origin
   moved INTO the token; updated EVERY pin off the old `tuple[str,str]` pair (leg2/3/4 constructions, the
   `active_exempt` token pin, the coverage name-extract, the live-migrate filter → `exempt.origin`). The
   borrowed-token leg-4 pin is RETAINED (token origin foreign). NO contextlib skip-list.
5. **Observer stub** (§1.9 item 3a/3b). Docstring rewritten to the RULED mechanism: observe at
   `query_raw` ONLY; read before/after via `type(conn).query_raw.__wrapped__`; ONE persistent dispatcher
   appended to `_CALL_HOOKS` at import + a registry `observe_…` registers into; detach pin STAYS; the
   observer docstring CITES `test_the_UNCOUNTABLE_door_set_is_DERIVED_from_the_SDK_and_DENIES_BY_DEFAULT`
   BY NAME as the reach evidence.
6. **F-TRAP-2 docstring** (§1.9 item 1). `_MIGRATE_GOLDEN`'s comment now teaches a FUNCTION-LOCAL
   statement var inside `_migrate_memory_scope` (passed to BOTH `governed_exempt(statement=)` and
   `run_query(statement=)`) — NEVER the module constant `principals.MIGRATE_MEMORY_SCOPE_STATEMENT`.

Substrate/classifier/observer/`governed_populations`/`derive_…` DOCSTRINGS were updated to spec the
§1.9 mechanism (★CONTRACT SHAPE★); their BODIES stay RED-until-built (builder deliverables).

---

## RECEIPT A — RED-at-HEAD (103c661), `test_memory_enforcement_63b_ia.py`, serial `-n0`
**20 failed / 13 passed / 33 collected.** Every RED is `AssertionError`/`Failed` — the fix unbuilt —
with ZERO TypeError/parse/store errors (verified `--tb=line`; all 20 reasons are §-cited "unbuilt" /
"CLASSIFIED" / "effect None" / "observed=[]"). New-pin reds, each for the exact adversary door:
- MISSING PIN #1 `test_a_reinforce_labeled_write_that_seizes…`: *"CLASSIFIED — the classifier blesses
  any label WITHOUT running its entry's effect predicate"*.
- MISSING PIN #1 generalised `test_every_label_frame_rejects_an_effect_its_predicate_denies`:
  *"'remember'-labeled write whose effect its OWN entry predicate REJECTS was CLASSIFIED (_upsert_fragment)"*.
- MISSING PIN #2 `test_the_population_derivation_reach_is_a_checked_variable`: *"governed_populations is
  unbuilt … cannot be exercised on a synthetic source; the reach is a hidden constant"*.
- ExemptToken pin `…_returns_the_token`: *"governed_exempt does not accept a keyword-only statement"*.
- Constructed-oracle NON-VACUITY pin `test_the_ensure_ready_effect_predicate_discriminates`: **PASSED at
  HEAD** (contract-side predicate + live oracle read) — the oracle machinery is validated live (virgin-DB
  apply → INFO FOR TABLE → SchemaSnapshot; one extra field → snapshot ≠ oracle → predicate red).
- The 13 green-at-HEAD are the pure-predicate/discrimination + L1-deny-by-default + green-vacuous pins.

Gates (main tree, both contract files): `uv run ruff check` **All checks passed!** · `uv run mypy`
**Success: no issues found in 2 source files**. The R4-deletion harder-leg: the now-orphaned `import re`
was removed from the contract module (ruff clean confirms no other orphan). Migrated modules
(`test_memory_enforcement_63a_v/_63a_iv/_bounds_63a_iv`) stay **27 passed** at HEAD — my §1.9 shape
changes did not break them.

---

## RECEIPT B — SATISFIABILITY (C-DEF), INLINE + BOUNDED (no sub-agent)
Built a CORRECT reference per §1.9's ruled mechanism in a provenance-asserted scratch and ran the
contract SERIAL + BOUNDED. **NO HANG.**

- Scratch via `scripts/scratch_copy.sh` — provenance asserted (#140 receipt):
  `loremaster.__file__ = /tmp/c63bia2-scratch-3643685/loremaster/loremaster/__init__.py`.
- Command: `cd loremaster && timeout 500 uv run python -m pytest tests/test_memory_enforcement_63b_ia.py -n0 -p no:cacheprovider -q` → **33 passed, 0 failed in 9.50s** (serial, NO HANG).
- `test_memory_enforcement_63a_v.py + _63a_iv.py + _bounds_63a_iv.py` on the reference build: **27 passed**
  — the instrument rewrite (4-leg classifier + effect observer) did not break the surviving 63a pins.
- The reference implements §1.9's ruled mechanism: `query_raw`-only observer with a `__wrapped__` read; a
  persistent dispatcher hook + registry; `governed_exempt` CLASS-CM with `sys._getframe(1)` origin →
  `ExemptToken`; function-local migrate statement; `ensure_ready` `write_guard` label; the CONSTRUCTED
  ensure_ready oracle; the derived grammar + corpus keyword derivation + AST population derivation.

### C-DEF FIXES FOUND (the receipt did its job — two contract defects a correct build tripped, now FIXED)
1. **`schema_snapshot_from_info` did not handle the `query_raw` rpc envelope.** The oracle reads via
   `.query` (bare `{fields,…}` dict); the builder's observer reads via `query_raw`
   (`{'id':.., 'result':[{'result':<map>}]}`). Without the envelope unwrap the observer's `schema_after`
   was empty → `schema_after == oracle` false → the rebuild-arc pin RED on a correct build (a genuine
   C-DEF the F-TRAP-3 ruling introduced). FIXED: `schema_snapshot_from_info` now digs through the dict
   envelope; ONE normaliser renders BOTH readers identically.
2. **The coverage-test name-extract used `isinstance(exempt, ExemptToken)`** — but production returns
   `governed.ExemptToken`, a DIFFERENT class from the substrate twin, so it failed to extract the channel
   name and blew up sorting `ExemptToken` vs `str` on a correct build. FIXED: duck-typed
   `str(getattr(write.exempt, "name", write.exempt))`.

Both fixes are in the MAIN-TREE contract (ruff + mypy re-confirmed clean; RED-at-HEAD count unchanged
20/13; the reference re-ran 33/0 with them).

---

## DRY LEDGER (brief-base §6 — new reusable test-substrate symbols)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_governed_contract.ExemptToken` | `lore_verify _governed_contract.ExemptToken` | not_found | **HAND-ROLLED** — the test-side twin of `governed.ExemptToken` (§1.9 item 3c), constructible at HEAD for the pure-unit pins; classifier reads both by attribute. |
| `_governed_contract.SchemaSnapshot` + `schema_snapshot_from_info` | `lore_search "INFO FOR TABLE snapshot maps"` | no snapshot type; `apply_ddl`/`run` read INFO ad hoc | **HAND-ROLLED** — the ONE INFO-FOR-TABLE normaliser the oracle AND the observer share (§1.9 item 4 dict-equality compare). |
| `ObservedEffect.schema_after` | (field on the existing `ObservedEffect`) | absent | **EXTENDED** `ObservedEffect` (a field, §1.9 item 4). |

---

## REFERENCE BUILD — the satisfiability instrument (brief-base §1: pasted so it survives the scratch)
Disposable scratch `/tmp/c63bia2-scratch-3643685` (excluded from git; the BUILDER re-authors this per
§1.9 as wave i-a's deliverable). The PRODUCTION-side + hook-seam deltas — the load-bearing, non-design-
obvious §1.9 mechanism — verbatim:

```diff
# loremaster/loremaster/governed.py — the exempt API (§1.9 item 3c/5)
@@ imports @@ + import sys ; + from pathlib import Path
-_ACTIVE_EXEMPT: ContextVar[str | None]
+_GOVERNED_REPO_ROOT = Path(__file__).resolve().parents[2]
+@dataclass(frozen=True)
+class ExemptToken:            # name + statement + origin (repo-relative file, co_name)
+    name: str ; statement: str ; origin: tuple[str, str]
+_ACTIVE_EXEMPT: ContextVar[ExemptToken | None]
+def active_exempt() -> ExemptToken | None: return _ACTIVE_EXEMPT.get()
+def _repo_relative(filename): 
+    try: return Path(filename).resolve().relative_to(_GOVERNED_REPO_ROOT).as_posix()
+    except ValueError: return Path(filename).resolve().as_posix()
+class governed_exempt:        # a CLASS context manager (not @contextmanager)
+    def __init__(self, name, *, statement): self._name=name; self._statement=statement; self._reset=None
+    def __enter__(self):
+        frame = sys._getframe(1)     # the frame executing the `with`, exactly one up (no contextlib frame)
+        origin = (_repo_relative(frame.f_code.co_filename), frame.f_code.co_name)
+        token = ExemptToken(self._name, self._statement, origin); self._reset = _ACTIVE_EXEMPT.set(token)
+        return token
+    def __exit__(self, *_exc): _ACTIVE_EXEMPT.reset(self._reset)

# loremaster/loremaster/principals.py — function-local migrate statement (§1.9 item 1)
+    statement = f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"
-    with governed_exempt("migrate-governed"):
+    with governed_exempt("migrate-governed", statement=statement):
         await run_query(..., statement=statement, ...)   # ONE source, passed to BOTH

# loremaster/loremaster/memory/local.py — ensure_ready label (§5.1 Q1 / §1.9 item 4)
+        with governed.write_guard("ensure_ready"):
             await execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=..., drop=..., url=...)

# loremaster/tests/_sdk_guard.py — the hook seam (§1.8 / §1.9 item 3a)
+@dataclass(frozen=True)
+class CallEvent: method:str; connection:Any; args:tuple; kwargs:dict; site:str|None; original:Any
+_CALL_HOOKS: list[Callable[[CallEvent, Any], Any]] = []
   # inside _guarded, AFTER _judge():
-            return original(self, *args, **kwargs)
+            coro = original(self, *args, **kwargs)
+            for hook in _CALL_HOOKS:
+                coro = hook(CallEvent(method_name, self, args, kwargs, site, original), coro)
+            return coro
         _guarded._sdk_guarded = True
+        _guarded.__wrapped__ = original    # §1.9 item 3a: the observer's unwrapped-door read
```

The substrate mechanism (`_governed_contract.py`, the ★BUILDER DELIVERABLE★ bodies) follows the design
verbatim; the NON-obvious satisfiability bits (measured, not design-derivable):
- **The `query_raw` result envelope is `{'id':.., 'result':[{'result':<data>}]}`** (SDK 2.0.0, dict — not
  a bare list). Both the row reader and `schema_snapshot_from_info` must dig through it; the observer's
  `schema_after` (via `query_raw`) and the oracle (via `.query`, which returns the UNWRAPPED
  `response["result"][0]["result"]`) then normalise to the SAME `SchemaSnapshot` → `after.schema ==
  oracle.schema` is a fair compare. (This was C-DEF FIX #1.)
- **Row ids are `str(RecordID) == "<table>:<id>"`** → the observer keys `RowDelta.id` on the BARE id
  (`.partition(":")[2]`), matching the gather pin's `{"g1","g2"}` (RowDelta.id's "bare row id" contract).
- **The persistent dispatcher acts on `query_raw` ONLY** (`.query` delegates to it — GOTCHA-A) and holds
  ONE `asyncio.Lock` across before→await→after; the before/after reads use `event.original` (unwrapped) →
  no re-entry, no deadlock. Confirmed: the member battery + rebuild arc + migrate + gather-of-two all
  complete serially in ~9.5s with NO HANG.

---

## PROGRESS LOG
- P0: FIRST FIVE (brief-base read, lore_comms register, idle-gate contract, report stub, heartbeat).
- P1: read adversary report + design §1.1–§1.9 + committed contract (1289 lines) + substrate shapes.
- P2: made the 6 §1.9 revisions (shapes in `_governed_contract.py`; pins + oracle in the contract module);
  ruff + mypy clean; RED-at-HEAD 20/13 all-right-reason.
- P3: built the §1.9-correct reference in a provenance-asserted scratch; ran the contract 33/0 (NO HANG);
  63a_v/iv/bounds 27/0 on the build; FOUND + FIXED 2 C-DEFs (schema envelope, coverage duck-typing) in the
  main-tree contract; re-verified gates + RED-at-HEAD + satisfiability. Report complete.
