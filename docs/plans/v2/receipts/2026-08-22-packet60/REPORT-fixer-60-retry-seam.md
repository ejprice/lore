# REPORT — fixer-60-retry-seam

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: done
- deviations: none
- Packages considered: none — no mechanism specified (two literal dict rows added; no new mechanism)
- Reuse ledger: none — no new symbols (two data rows in existing hand-written maps)
- Graded: n/a — this is a fix, not a verdict on someone else's artifact
- decisions-needed: none
- receipt pointers:
  - production values: `loremaster/loremaster/keeps.py::KeepStore._query` (`noun="keep query"`, `label="keep.query.rejected"`)
  - edits: `loremaster/tests/test_retry_seam.py` `_SEAM_REJECTION_EVENTS` + `_SEAM_REJECTION_NOUNS`
  - gate tails: §VERIFY below

## TASK
Finding #397 (contract-gap recurrence of #353): packet-60 wave-1 added `KeepStore`
(`loremaster/loremaster/keeps.py`) whose `async def _query` is AST-auto-discovered by
`test_retry_seam.py::_discover_query_seams()`, but the file's two HAND-WRITTEN canonical
maps had no `KeepStore` row, so the map-completeness / attribution pins compared
discovered-vs-canonical and KeyError'd/failed. The sanctioned packet-48/49 resolution is to
register the new seam in both maps (never a bespoke seam that dodges the AST enumeration,
finding #120). This is the fix. NOT builder work (builder ≠ grader).

## GREP CONFIRMING KeepStore._query's ACTUAL label/noun (non-arbitrary)
`loremaster/loremaster/keeps.py::KeepStore._query` (lines 332–341) delegates to the shared
`run_query` seam with:
```
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="keep query",
            label="keep.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )
```
So the registered map values MUST be `noun="keep query"` and `label="keep.query.rejected"`
— which equal the brief's suggested values. No production code touched.

## THE TWO EDITS (in `loremaster/tests/test_retry_seam.py` ONLY)
Both maps are alphabetically ordered; `KeepStore` (K) inserted between
`FloorCalibrationStore` (F) and `LocalMemoryBackend` (L) in each.

### 1. `_SEAM_REJECTION_EVENTS` (was ~line 6041 area)
Added after the `FloorCalibrationStore` entry:
```python
    # Packet 60 wave-1's new seam (finding #397 — the contract-gap recurrence of #353).
    # HAND-WRITTEN entry for the auto-DISCOVERED ``KeepStore._query`` (loremaster.keeps):
    # registering its canonical event is the sanctioned 48/49 resolution — never a bespoke
    # seam that dodges the AST enumeration (finding #120), never "pre-existing, ship". Its
    # ``_query`` MUST raise with ``label="keep.query.rejected"`` to match this entry.
    "KeepStore": "keep.query.rejected",
```

### 2. `_SEAM_REJECTION_NOUNS` (was ~line 6080 area)
Added after the `FloorCalibrationStore` entry:
```python
    # Packet 60 wave-1's new seam (finding #397): ``KeepStore._query`` MUST raise with
    # ``noun="keep query"`` to match this entry (a domain-naming noun, so it also keeps
    # the two-population monoculture guard non-trivial).
    "KeepStore": "keep query",
```
Note: `keep query` is a DOMAIN-naming noun (≠ the plain `"query"` population), so it keeps
the two-population monoculture guard (`test_the_canonical_noun_map_is_not_a_MONOCULTURE`)
non-trivial rather than tipping it.

## VERIFY
- `uv run ruff check loremaster/tests/test_retry_seam.py` → **All checks passed!**
- `git status --short` → my change adds ONLY `loremaster/tests/test_retry_seam.py` to the
  modified set. The other three modified files (`store/surreal_schema.py`,
  `tests/_enforced_relations_scaffold.py`, `tests/test_enforced_relations.py`) were already
  modified in the working tree BEFORE this task (present in the spawn-time snapshot).
- `uv run pytest loremaster/tests/test_retry_seam.py -n auto -q` → **663 passed, 1 warning in 11.29s** (exit 0). 0 failed.

The retry-seam pins RE-EXECUTE `KeepStore._query` under a forced rejection and assert it
emits the registered event/noun — so a fully-green run PROVES the registered value matches
the production code (NOT a tautology: the map is compared against what the built code
actually emits).

### Retry-seam full-green tail
```
........................................................................ [ 97%]
...............                                                          [100%]
=============================== warnings summary ===============================
loremaster/tests/test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried
  .../test_retry_seam.py:3216: RuntimeWarning: coroutine '_empty_subscription' was never awaited
663 passed, 1 warning in 11.29s

[exited with code 0]
```
The single warning is PRE-EXISTING and UNRELATED to this change: it fires in
`TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried` (a scout
subscription test, not a KeepStore path) and is a `RuntimeWarning`, not a failure. My edit
added two data rows to two dicts and touches nothing that could create it.
