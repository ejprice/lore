claims_checked=80 supported=73 overstated=4 unsupported=1 wrong_source=2

Scope: every added line of `git diff docs/reference/surrealdb-31-capabilities.md` (286 + lines). Claims grouped; SUPPORTED rows are summarised by group, non-SUPPORTED rows are individual. Findings #588 #590 #593 #597 #601 #603 checked via lore_findings (all open, bodies match the doc).

| claim | cited source | verdict | evidence |
|---|---|---|---|
| "Its source is pasted verbatim in `REPORT-storeref-66.md`, which is archived under `docs/plans/v2/receipts/2026-11-08-sdk3/`" | that dir | UNSUPPORTED | `ls` of the dir has no REPORT-storeref-66.md (git status: not tracked either). It exists only in the scratchpad (closeout66/REPORT-storeref-66.md). Archive it before commit or reword. |
| "The pin is EXACT because 3.0.1 changes `str(RecordID)` (R7)" | R7 | OVERSTATED | R7: "SDK pinned `surrealdb==3.0.0` (3.0.1 unpublished on PyPI as of 2026-11-07)". It records the str change (3.0.0 brackets / 3.0.1 backticks) separately; R7 gives no "because" linking them. |
| "request timeout 30.0, which is SDK 3.0's own default, kept until measured (R19 Q2)" | R19 Q2 | WRONG-SOURCE | 30.0 default verified in SDK `__init__.py:360` and `_txn.py:684`. "keep SDK 3.0's 30 s until measured" is R5 F4b; R19 Q2 is only the conformance-run grep for TransportTimeoutError/OutcomeUnknown. |
| "No `websockets.*` class reached lore in 120 legs (C-row #9)" | REPORT-builder-66 C-row | WRONG-SOURCE | C-row #9 row says 20 x {ABORT, CLOSE_FRAME} (40 per outcome). "120 legs" is in the FINAL drop-list fate table row 9 (builder report line ~265: "probe_c_proxy.py 120 legs, 0 websockets classes"). |
| "The cold audit is GO at `88b06be` (§DELTA-2)" | REPORT-coldaudit-66 §DELTA-2 | OVERSTATED | Verdict line is GO, but it states two readings of #598: (a) strict R17 gives NO-GO again, (b) gives GO; GO rests on (b) with #598 (LOW) open. Doc omits the conditionality. |
| "the in-image conformance run PASSED" | REPORT-conform-66 | OVERSTATED | Report: "Verdict: PASS for the SDK-3 artifact, with named holes" (state done-with-deviations; lore_diff out of scope because snapshot_entry not restored; #604 found; 9 CHANGED tool rows). |
| "Served catch sites … are pinned for every served catch site (D1) and for the 14 `SurrealStoreError` sites (F18)" | R9 D1, R12 F18 | OVERSTATED (ruling claim, pin existence not re-measured) | R12 F18 says "(14 sites)" as a ruled scope; builder report line 202 shows the F18 family table was being re-adjudicated. I did not verify 14 pins exist. Treat as ruling, not measurement. |

SUPPORTED groups (evidence, one line each):

| claim group | verdict | evidence |
|---|---|---|
| Header: pin `surrealdb==3.0.0`, previously `>=2.0`; commit `9863c11` touches pyproject+uv.lock; uv.lock resolves 3.0.0; Containerfile `uv sync --locked --all-packages` | SUPPORTED | `git show 9863c11` (-`surrealdb>=2.0` +`==3.0.0`); uv.lock:2246-2247; Containerfile:97 |
| "storeref-66 = 28 checked legs plus informational; one throwaway DB on :18000, removed" | SUPPORTED | log: 28 `^PASS`, 10 `^INFO`, `PASS cleanup: throwaway DB removed`, FAILS=[] EXIT=0 |
| S1 `[1,2]`/`[1]`; seam refuses 2-entry; S2 raise `ThrownError boom`, rows 1,2 both exist w/o BEGIN; S2b `QueryError kind=Query details NotExecuted` "failed transaction", nothing commits | SUPPORTED | log lines S1, S2 (+INFO rows `[[1, 2]]`), S2b |
| `_statement_values` raises first ERR else returns all results | SUPPORTED | SDK builders.py:912-917 |
| `QueryDetailKind.TRANSACTION_CONFLICT`, `is_transaction_conflict`; `_RETRYABLE_CONFLICT_KIND` deleted `df84764` (drop #2) | SUPPORTED | errors.py:106,291; `git show df84764` removes the symbol; builder report line 72/258 |
| `surrealdb.__version__` absent; version via metadata (3.0.0 in-image, /app/.venv path) | SUPPORTED | grep of SDK __init__ has no `__version__`; conform §Step 2 |
| Constants: SURREAL_RECONNECT(-1,0.5,2.0), REQUEST_TIMEOUT 30.0, STREAMING True, ENSURE_READY/INDEX_TXN 300, TEARDOWN_KILL 2.0, OUTCOME_UNKNOWN_ADVICE text, SurrealOutcomeUnknownError subclass of SurrealConnectionError, TXN_ROW_HARD_CAP 50_000, warn 10_000, `one_statement_result`, `record_key`, `record_text`, `served_instant_text`, `parse_served_instant` zone check | SUPPORTED | `_txn.py` lines 151,176,180,481,492,679-696,769,843-880,892,924 |
| `TXN_STATEMENT_HARD_CAP` (5,000) deleted; R3 5,113 statements for test_comms_tool | SUPPORTED | no definition in `_txn.py`; removed in df84764 (`git log -S`); R3 line 72. Note (not a claim defect): dormant packet-58 tests still reference the name (RED_ADJUDICATED per audit). |
| `_await_reconnect` bounded by request timeout -> TransportTimeoutError; in-flight drop ConnectionUnavailableError not re-sent | SUPPORTED | async_ws.py:758-771; R5 grounds |
| Why-unknown: streaming cancel commits nothing; disconnect nothing; streaming=False + timeout commits; client txns never stream; SurrealKV/RocksDB unprobed; measured on memory engines 3.3.5 and 4.0 | SUPPORTED | R7 "R5 amended" + "throwaway v4.0.0 + v3.3.5 memory containers" |
| First connect to down store -> ConnectionUnavailableError (C-row #21) | SUPPORTED | builder C-row table row #21 |
| kill() parks 30 s, TransportTimeoutError 40/40, SDK 2.0 failed at once; fix 5e464bc; re-measure 2.00 s vs 30.00 s; worst case 2xN; not stdlib asyncio.timeout | SUPPORTED | builder lines 58,127-129,222; R41; RULING-13. ("SDK 2.0 failed at once" is the builder's statement, no probe log cited.) |
| close() idempotent (docstring), 40/40, S6 second close raises nothing; 18 `_safe_close` retired `6b43b65` (18 files); pin `5fb57fc` 17 owners x 2 modes + scout | SUPPORTED | async_ws.py:2616; probe S6; `git show --stat`; R41 FORK S |
| PreciseDatetime tz-aware UTC, ns kept (C-row #8/#34); `parse_instant` 1-9 digits, 9-digit round-trip; `==`/`<` ignore ns (#593); stamp_key `(instant, nanosecond)` | SUPPORTED | builder C-row; log O2/O3; stamp_paging.py:60-66; finding #593 |
| Py 3.14 `fromisoformat` truncates 9->6 digits silently (#590), 3.14.7, six-digit control | SUPPORTED | log O1; finding #590 |
| `db.batch()` cancellation notice vs THROW (#588; drop #14 KEEP; one error) | SUPPORTED | builder C-row #14, R-9 row #14; finding #588 (filing awaits operator) |
| Record-id table (5 rows) and rules (a)-(d); RecordID hashable; ead3356 graph de-dupe on RecordID; d41aa47 all-digit correction | SUPPORTED | log S3/O4/O5; R7; `_txn.py` comments; ead3356 diff |
| `> $datetime` ADMITS array/object/uuid/record/later datetime; EXCLUDES string,number,float,bool,NULL,duration,NONE,earlier; R45 S6; DELTA-2 4b; storeref S4; KNOWN BOUND #597; de6e116, d2df34c; door = admin DDL retype | SUPPORTED | log S4 (admitted set, controls); coldaudit 4b lists exact excluded set; R45/R46; RULING-17; finding #597 |
| `option<datetime>` rejects literal NULL, Python None stores NONE, controls | SUPPORTED | log S5; coldaudit DELTA-2 item 7 |
| #25: bound record-id range -> RecordIdScan 20/20; two prefixes Union 40/40; starts_with(record::id) and id range TableScan; audit 303+21 traps; fate RETIRE owed; INDEX_SCAN_OPERATORS lacks RecordIdScan; U+10FFFF; surrogates | SUPPORTED | builder R-9 "#25 cand. 1/2"; coldaudit §DELTA item 5 |
| INSERT ... ON DUPLICATE KEY UPDATE parity (X13, 66a9979), plain INSERT -> AlreadyExistsError | SUPPORTED | builder lines 43,356 |
| `POST /import` 4 GiB (vendor); HTTP 413 "length limit exceeded"; snapshot_entry 6.25 GB; packet 65 (#603) | SUPPORTED | via-http.mdx:43 (scout copy of corpus); conform §Step 4b (6,249,803,480 B); finding #603 |
| Q4 drop #29/#30; ping_interval 30 / ping_timeout 10 (~40 s); version_check True, MIN 2.0.0 / MAX 5.0.0; whole-stream-hold starves pong | SUPPORTED | SDK __init__.py:358-359,361; features.py:19-20; packet doc rows 29/30 and lines 829-833 |
| Harness `run()` answers first statement, fails closed on empty/non-list, #486 reaper reads INFO FOR NS; pin class name | SUPPORTED | `_surreal_harness.py:249-262`; `test_surreal_harness.py:2308` |
| Served production container NOT on 3.0.0: image 43122071…, built 2026-08-18, venv surrealdb 2.0.0; latest id unchanged | SUPPORTED | I re-measured now: `podman inspect lore-lore` image 4312207128bb…, Created 2026-08-18; `podman run --entrypoint python` -> surrealdb 2.0.0; conform §Step 7 id before=after. Dated [MEASURED 2026-11-08]. |
| Recovery tag v3.3.5 in lore-surreal.container; v3.2 now 3.2.6 | SUPPORTED | quadlet line 7; doc §0a lines 16,274 |
| #601 incident: `--help` printed SURREAL_PASS; container env via EnvironmentFile lore.env; export recipe; open | SUPPORTED | conform §INCIDENT; finding #601; quadlet line 15 |
| History-edit rows in §3/§6.x/§7 (2.0.0 qualifiers, "second item an upgrade invalidated", candidate list item 15 incl. #588/#593/#597) | SUPPORTED | consistent with the above receipts; item 15 explicitly says un-swept |

Present-tense undated sentences (not defects, flagged per brief): "The store containers carry SURREAL_USER/SURREAL_PASS in their env" (true today via EnvironmentFile; no date); "#601 … Open: rotation and transcript purge are operator decisions" (finding open at 2026-11-08 close-out; no date).
