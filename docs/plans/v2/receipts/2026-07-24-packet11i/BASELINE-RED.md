# Packet 11-i — inherited RED baseline at the worktree base

**Purpose.** Packet 11-i branches from a tree whose test suite is deliberately RED: packet 03b's
contract phase is certified and landed, but its builder has not run, so 03b's contract tests fail
BY DESIGN. Every agent on 11-i (contract author, contract-adversary, builder, cold auditor) needs
the inherited failure set as an exact list so it can diff its OWN breakage against it. A summary
count is not enough — "394 failed" looks identical whether or not 11-i broke something and fixed
something else.

## Provenance

| field | value |
|---|---|
| base commit | `d0ee2be` (`feat/surreal-unification`; packet 10 + 10-d merged) |
| worktree | `/home/ejprice/PycharmProjects/lore-pkt11i`, branch `pkt11i-floor-calibration-dark` |
| command | `uv run pytest -n auto -q --tb=no` |
| measured by | `lead-11i`, 2026-07-24 |
| runs | 2 independent runs, **identical counts** (394 / 6138 / 17 / 3) |

## Counts

```
394 failed, 6138 passed, 17 skipped, 3 xfailed, 1 warning
```

Wall clock 160s and 234s across the two runs (`-n auto`, 64 cores).

## The failure set

Full sorted list: `baseline-red-at-d0ee2be.txt` (394 node ids, one per line).

Distribution by file:

| count | file |
|---|---|
| 284 | `loremaster/tests/test_comms_tool.py` |
| 89 | `loremaster/tests/test_trace_telemetry.py` |
| 15 | `loremaster/tests/test_comms_promise_registry.py` |
| 3 | `loremaster/tests/test_comms_schema.py` |
| 1 | `loremaster/tests/test_surreal_schema.py` |
| 1 | `loremaster/tests/test_surreal_fakes.py` |
| 1 | `loremaster/tests/test_comms_wiring.py` |

**All 394 are packet 03b's deliberate contract RED.** The three singletons were checked
individually rather than waved past with the rest, because they sit outside the obvious 03b
contract files and a lazy read would classify them by file name alone (repo law bans
"all remaining hits are X" as an output):

- `test_comms_wiring.py::TestAppContextAcloseClosesCommsLedgers::test_aclose_closes_the_message_ledger_connection`
  — 03b comms surface wave.
- `test_surreal_fakes.py::TestRecordTraceFake::test_record_trace_signature_matches_real_store`
  — 03b telemetry wave (the fake must track the real store's widened `record_trace` signature).
- `test_surreal_schema.py::TestTraceTableFieldDefinitions::test_trace_core_scalar_fields_are_defined`
  — 03b telemetry wave (the widened `trace` table's field definitions).

**No inherited defect outside packet 03b's contract was found in this baseline.**

## How to use this

A green claim from any 11-i agent means: the suite's failure set is a SUBSET of this file, and
every 11-i test the agent added passes. It does **not** mean "394 failures, same as before" —
that count is reachable by breaking one test and fixing another. Diff the sets:

```bash
uv run pytest -n auto -q --tb=no 2>&1 | grep '^FAILED ' | sed 's/^FAILED //' | sort \
  > /tmp/now.txt
diff docs/plans/v2/receipts/2026-07-24-packet11i/baseline-red-at-d0ee2be.txt /tmp/now.txt
```

Lines only in `now.txt` are 11-i's breakage. Lines only in the baseline are 11-i having fixed
(or deleted — check which) an 03b contract test, which is **out of scope for this packet** and
must be escalated, not celebrated.

⚠ A piped pytest with a bad path exits "no tests ran in 0.00s" behind the pipe and looks green.
A green claim requires the passed-COUNT in the tail (repo law).
