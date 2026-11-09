brief-base v25 read

# REPORT — delta-r17-66 (R17 read of the fix-wave production diff 7cc5837..672b6d6) — PERSISTED BY audit-sdk3-66
Provenance (audit-sdk3-66, 2026-11-08): the reader's harness refused its Write. It returned the report inline;
this is the auditor's condensed transcription with every verdict kept. Probe kept on disk:
`audit66/delta_r17_probes/probe_h3_two_truncated.py` (sha256 252cdf46…, pasted in REPORT-audit-66.md §DELTA).

## Summary
- Graded: 672b6d6 · HEAD-at-report: 672b6d6 · SAME. Packages considered: none. Odoo-20: n/a. Reuse ledger: none.
- Headline: the production diff mostly holds under R17. **One served-text false clause (S1): the h3 truncated-leg
  header is false for a leg that is not the MIN leg, and beside a held leg** (reproduced at the render seam;
  the #593 pin's page 1 builds the same live state). h3 is pinned twice (S2). R-12's snapshot_gc item
  was resolved as "no edit" without a ruling (S3).

## Check 1 — production diff (commit partition PASS: production paths only in fda1411 5b4c138 f2327ef b411cab d41aa47 b2214d7 273bb69)
| item | verdict | basis |
|---|---|---|
| 1a cursor codec (`_txn.served_instant_text` / `parse_served_instant`; `AppContext._parse_rollup_since`, `_render_rollup`) | PASS | SDK `isoformat_with_nanoseconds` / `parse_instant`; plain → 000 ns; naive → UTC; offset → UTC with Z; CBOR binds `.nanosecond`; lowercase z / date-only / 10-digit fraction refused loudly |
| 1b R-6 `record_key` routes (4 server.py sites, `TaskLedger._traversal_ids`) | PASS | identical for word keys; now consistent with `keeps.keeper_id` for non-word keys |
| 1c R34 clause (f2327ef → 273bb69) | PASS, one over-claim (S4) | "this call reads that row and could not be completed" true for listing + single read + stamp-paging overflow row; "the store's other rows are intact" over-claims under schema drift; message leg projection has no id → "(id unknown)" |
| 1d prose (b411cab, d41aa47) | PASS | measured live: ULID bare; uuid backticked; 32-digit all-digit string backticked; `abc123def` / `0199c4f1abc` bare; `(10/16)^32 ≈ 2.9e-7` true; `string::starts_with` on `name.value` = IndexScan `name_value` |
| 1e stamp paging (`cut_stamp_page`, `read_stamp_page`, `_rollup_next_cursor`, `_rollup_leg_header`) | PASS on the cut/cursor; **FAIL on h3 prose (S1)** | a page never ends inside a group except the named held case; `resume_at` ≤ last served stamp; stamp_key orders by ns; held N = whole-group count; h2-held correct on the message leg |
| 1f R-12 | PARTIAL | scout stop() and briefs already_acked bounds are now docstrings with triggers; `scripts/snapshot_gc._to_aware_utc` NOT edited (builder: not an SDK user, naive branch unreachable) — deviates from RULING-14's literal "fix-now if Q5 port, else header it", unruled (D2) |

### S1 probe output (672b6d6)
```
tasks transitioned (showing 1 of 2 — the next cursor resumes at the elision point, and the other legs re-serve their rows above it; re-call rollup with it, or raise limit):
findings filed (showing 1 of 2 — the next cursor resumes at the elision point, and the other legs re-serve their rows above it; ...):
next cursor: 2031-05-06T07:08:09.186697100Z   <- the FINDING leg's tail (LOW), not the task leg's elision point (HIGH)
```
Second shape: a held leg beside a truncated leg → the truncated leg's h3 says "resumes at the elision point", but the cursor = since. Harm: unnamed duplicate serves (at-least-once), never loss. h2 "not covered by the next cursor" is false-CONSERVATIVE when the cursor holds/echoes since (S5).

## Check 2 — #593 PreciseDatetime comparison sweep (grep fallback; `audit66/sweep593-raw.txt` 48 hits, `sweep593-precise.txt` 15)
`_rollup_next_cursor` fixed (stamp_key; b8ae2cd pins at literal sub-µs stamps); `cut_stamp_page` correct; `agents` heartbeat max/sort = Python-µs minted (no sub-µs); server trace `max(latest_values).isoformat()` = display, not hand-back (LOW); 5 `expires_at <= now` sites harmless (≤ 1 µs, conservative); others N/A or engine-side. Bound: name-keyed sweep.

## Check 3 — R-9 saved logs (`build66/logs/r9_*.log`; headers HEAD b411cab, DIRTY 0, TREE 17796957…, probe sha, loremaster in checkout, SDK 3.0.0, EXIT=0; codec unchanged b411cab → 672b6d6)
#14 yes · #15 yes · #19 yes · #25 yes (RecordIdScan / Union 20/20, 40/40 + mirror IndexScan control) · #26 yes (L2 line not separately sighted, LOW) · **#34 yes, well-controlled** (ns=372; L1/L2 excluded; L3 isoformat/fromisoformat RE-SERVED = #590 reproduced as control; L4 codec excluded; L5 µs cursor re-served once = stated bound) · #35 yes · X13 yes · R-7 record_text yes.

## Check 4 — test side
4a P4 asserts h2-held (not h1): PASS · each header pinned once: **FAIL for h3 (S2)** (`H3_OTHER_LEGS_RESERVE` in test_sdk3_rollup_ties_r15 + a literal in `test_mcp_server::…test_truncated_leg_header_shows_n_of_total_and_teaches_resume`) · 4b R34 two shapes: PASS (task get_task + query_tasks, finding get; ledger-raised text, MCP seam not traced) · 4c `_stamp_page_fakes` tautology: PASS (builds INPUT windows only; P1–P6 / #593 assert literals or live walks) · 4d F3 safe-door rows: PASS (three callers verified; trigger named) · 4e window fields: PASS (builders changed only in test commits) · 4f #592: h2 PASS, h3 FAIL (S1/S2).

## Suspected defects (ranked)
1. S1 h3 false for a non-MIN truncated leg / beside a held leg — HIGH (reproduced).
2. S2 h3 pinned twice — HIGH (grep).
3. S3 R-12 snapshot_gc "no edit" unruled — LOW.
4. S4 R34 "other rows are intact" over-claims under drift — MEDIUM (wording).
5. S5 h2 false-conservative when the cursor holds — LOW.
6. S6 refused message row names "(id unknown)" — LOW.
