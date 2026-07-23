brief-base v6 read

# REPORT — auditor-03a1 · COLD REFUTE audit of packet 03a-1 (comms ledger SEND path + drain + foundations)

## SUMMARY BLOCK
- receipt: `brief-base v6 read`; store reference read in full (§1.1 SEQUENCE, §2 CONTENT/protected-`session`, §3 execute_transaction, §4 RELATE/ENFORCED/dangling, §5 mint/nextval).
- **VERDICT: GO.** The SEND path + `drain` + `AgentRefLike` home + module foundations are correctly built; every load-bearing pin genuinely DISCRIMINATES a wrong build (4 mutation proofs, each with a positive control, all restored byte-exact). The `[real]` leg — the §7.8 residual this audit exists to close — is GRADED and PASSING.
- gates (independently reproduced, :18000 ONLY): full `test_message_ledger.py -n auto` = **31 failed / 140 passed / 9 skipped**; the 31 red are EXACTLY the 03a-2 stubs (13 ack + 18 awaiting_answer, all `[real]`, all `NotImplementedError` — the ONLY error type in the whole run). `ruff` clean; `test_retry_seam.py` 503; `test_brief_ledger.py` 120.
- **typecheck.sh EXITS 1 (36 errors) — but ZERO in the builder's writable prod files**; all 36 are 03b-forward-ref / frozen-contract surfaces, expected under the operator's 2026-07-23 global-mypy-deferral. (The background-task "exit 0" was the bash wrapper; real `typecheck.sh` exit is 1 — reported honestly.)
- C-DEF fix (the sole contract edit, `_seed_agents:243` CREATE→UPSERT) is NON-WEAKENING: proven by Mutation A + control.
- residuals (7, latent — read §RESIDUALS): message-id is `uuid4().hex` not `ulid()` (needs an operator ruling); typecheck globally red by design; `drain` scope-migrated into 03a-1 (lead-confirmed); `_MIN_KNOWN_SEAMS` left at 10; validate-then-write TOCTOU (ENFORCED-backstopped); drain loads-all-then-caps; seq read-back is a 2nd round-trip.
- receipt pointers: gate counts §1; `[real]`-leg grading §2; mutation table §3; C-DEF §4; AgentRefLike §5; residuals §6. All mutations restored to md5 `9ca1ba3d5ee7cf71f587150af06443d2`.

---

## 0. What I audited & how (provenance)
- Tree under audit: the UNCOMMITTED working tree at `feat/surreal-unification` — NEW `messages.py` + `agent_ref.py`; MODIFIED `briefs.py` / `server.py` / `test_message_ledger.py` (the one authorized edit) / `test_retry_seam.py` (2-line seam registration).
- Tree identity receipt: `loremaster.messages.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/messages.py` (the REAL in-place tree — no scratch copy, #140; no worktree, #134). Every mutation was IN-TREE with a `cp -a` content backup at `/tmp/messages.py.ORIG` and restored byte-exact (md5 verified each time).
- Store: spike-surreal `ws://127.0.0.1:18000` ONLY (`LORE_TEST_SURREAL_URL` unset → harness default; env confirmed clean of any `:18500` override). Production `:18500` never touched.
- I trusted NOTHING in `REPORT-builder-03a1.md` (it is pre-C-DEF-fix stale). Every number below is my own live re-run.

---

## 1. Independent gate counts (all at :18000)

| gate | result | exit |
|---|---|---|
| `test_message_ledger.py -n auto` | **31 failed / 140 passed / 9 skipped** | 1 (expected — stubs) |
| `test_message_ledger.py -k real` (verbose) | **31 failed / 55 passed / 0 skipped** | 1 |
| `scripts/typecheck.sh` | **36 errors / 3 files** — none in writable prod files | **1** |
| `ruff check .` | All checks passed | 0 |
| `test_retry_seam.py -n auto` | **503 passed** | 0 |
| `test_brief_ledger.py -n auto` | **120 passed** | 0 |

**The 31 red are all genuine 03a-2 stubs, NOT defects wearing a stub's error.** Grouped: `TestTheWaitingStateIsDerived` 16 · `TestAckDisambiguatesTheFourWayEmptyReturn` 9 · `TestAckIsWriteOnce` 3 · `TestTheDerivedWaitingStateKnownBound` 2 · `TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner` 1 = **13 ack + 18 awaiting_answer**, ALL `[real]`, 0 `[fake]`. Error-type histogram across the ENTIRE run: `NotImplementedError` only — **zero `AssertionError`, zero `AlreadyExistsError`, zero `SurrealStoreError`.** Since these tests run 03a-1 `send`/`drain` setup FIRST and only then hit `ack`/`awaiting_answer`, the absence of any non-stub error proves the send/drain paths inside them executed cleanly and the failure is purely the stub (`ack` :807, `awaiting_answer` :819). Confirmed a real defect could not hide behind them.

**Full reconciliation (no gap):** 55 real-pass + 85 fake-pass = 140 ✓ · 31 real-stub-fail + 0 fake-fail = 31 ✓ · 9 fake-leg raw-store `pytest.skip` (`if not _is_real`) = 9 ✓.

**typecheck.sh — the 36 errors, attributed:** `test_comms_tool.py` (31: 03b `comms(to=/grade=/peek=/seqs=)` kwargs not yet on `AppContext.comms`) + `test_comms_promise_registry.py` (3, 03b) + `test_message_ledger.py:1716/1736` (2 pre-existing `no-any-return` in the FROZEN contract helpers `_message_row_count`/`_edge_row_count`). `git diff HEAD --stat` on the contract file = **1 insertion / 1 deletion** (line 243 only); 1716/1736 are untouched → those 2 errors pre-date the builder. NONE of the 36 touch `messages.py`/`agent_ref.py`/`briefs.py`/`server.py`/`test_retry_seam.py` (grep-confirmed). Consistent with the operator's 2026-07-23 ruling that global mypy-zero is deferred to the 03b end; the packet's "per-file clean for writable files" exit criterion IS met.

---

## 2. `[real]`-LEG GRADING (adversary §7.8 — the reason this audit exists) — PASS

The largest carried-forward risk was that the `[real]` tier was UNGRADED. It is now graded: **the real leg genuinely exercises spike-surreal, with ZERO silent skips.** The `-k real` verbose run shows **0 SKIPPED** — every real-leg pin RAN — and every raw-store-only observation pin (impossible to satisfy on the in-memory fake) PASSED on real:

- `test_the_receipt_COUNT_equals_the_edges_actually_written[real-1..4]` — raw `count() FROM to` — PASS
- `test_a_rejected_send_leaves_no_message_row_at_all[real]` — raw message-row count — PASS
- `test_no_dangling_edge_survives_a_send[real]` — `SELECT out.name` ghost scan (#105) — PASS
- `test_eight_concurrent_sends_all_land_on_distinct_seqs[real]`, `test_at_scale[real-16]`, `test_concurrent_seqs_all_exceed_the_pre_race_maximum[real]`, `test_every_concurrent_send_is_readable_by_its_recipient[real]` — live races — PASS
- `test_ensure_ready_creates_the_message_and_to_tables[real]` (INFO FOR DB), `test_ensure_ready_is_idempotent[real]` (no-rewind re-apply) — PASS

The 9 fake-leg skips are exactly these real-only observations on the fake tier — consistent, not a coverage hole.

---

## 3. Refutation attempts (each with a POSITIVE CONTROL) — every load-bearing pin discriminates

All mutations IN-TREE, `cp -a` backup, restored to md5 `9ca1ba3d5ee7cf71f587150af06443d2` (verified after each).

| # | what I mutated | target pin(s) | RESULT | positive control |
|---|---|---|---|---|
| **A** | `send`: hardcode `session = "wave7"`, ignore the call arg | `test_a_send_in_a_DIFFERENT_session_records_that_session[real]` | **RED** — `assert 'wave7' == 'wave9'` | unmutated pin PASSES |
| **B** | replace `sequence::nextval` with `array::len((SELECT VALUE seq FROM message))` (TOCTOU read-count) | `test_eight_concurrent_sends…`, `test_at_scale[16]` | **RED** — `duplicate seq minted at 16-way: [0,0,0,0,0,2,3,3,…]` | unmutated: **8 green runs, 0 flakes** (§below) |
| **C** | delete the `_reject_unknown_recipients` app-check | `…is_rejected_by_name[real]`, `…all_or_nothing[real]`, `…leaves_no_message_row[real]` | **RED** — send raises `SurrealStoreError` ("statement 5 of 6 rejected, rolled back") not `UnknownRecipientError` | `test_no_dangling_edge_survives_a_send` (valid recipients) stays GREEN |
| **D** | `_query`: bypass `run_query`, call `connection.query` directly | 22 pins incl. `test_every_seams_query_GOES_THROUGH_the_shared_attempt_body[MessageLedger]`, both `…SHARED_marker…[MessageLedger]`, `test_no_seam_escapes_the_driver_against_the_real_engine` | **RED** (22 failed) | restore → **503 passed** |

Key readings:
- **B proves the mint is a genuine native sequence, not TOCTOU** — the read-count wrong build collides at 8- and 16-way; the real `sequence::nextval` in one `execute_transaction` does not.
- **C proves two independent guards, both real:** (a) the app-level `SELECT id FROM $recipient_ids` owns the TYPED `UnknownRecipientError` that names every ghost *before* any write; (b) `ENFORCED` + the single atomic `BEGIN…COMMIT` (`compose`/`execute_transaction`) is a live store-integrity backstop — with the app-check gone, the engine rejected the ghost RELATE and **rolled the whole transaction back** (no message row, no dangling edge). Defense-in-depth, both verified live. This also settles the **atomic all-or-nothing** concern: a rejected fan-out leaves ZERO message row AND ZERO edges by transaction atomicity, observed directly.
- **D proves routing-is-sharing** for the retry seam: the two `SHARED_marker[MessageLedger]` pins reddening means `messages._query` uses the SHARED classifier (`_txn`'s `"can be retried"` marker), not a private `"Resource busy"` copy — the #102 "private copy wearing the shared name" failure mode is absent. The runtime SDK-escape guard (`test_no_seam_escapes_the_driver_against_the_real_engine`) also fired, confirming the seam's SDK calls are observed by the guard.

**Concurrency stability (repo law: a single green run never clears a concurrency test):** ran `TestConcurrentSendsMintDistinctSeqs -k real` **6 consecutive times → 6× "4 passed"**, plus the full run and the `-k real` run = **8 clean runs, 0 flakes**. Mutation B confirms these pins are not vacuously green. (The lead already established `test_concurrent_seqs_all_exceed` at 20/20; I did not re-run 20× — discrimination + reproduction is this audit's job.)

---

## 4. C-DEF fix — NON-WEAKENING (verified with control)

The ONLY edit to the contract is `_seed_agents` (`test_message_ledger.py:243`) `CREATE type::record('agent',$id) CONTENT` → `UPSERT …`. `git diff HEAD --stat` = 1 file, 1 insertion / 1 deletion; the change sits at line 243 and touches nothing else (helper lines 1716/1736 untouched). The UPSERT makes the real seed path idempotent (last-write-wins), matching the fake's already-idempotent `register_agent` — the CREATE-on-a-duplicate-id `AlreadyExistsError` that blocked two `[real]` pins is gone (0 `AlreadyExistsError` in my run).

**It does NOT neuter the anti-monoculture pin.** Mutation A reddened `test_a_send_in_a_DIFFERENT_session_records_that_session[real]` (`'wave7' != 'wave9'`) and the unmutated build passes — the pin still catches a session-hardcoding build. The UPSERT changed only *how agents are seeded*, orthogonal to whether `send` records the call's session; the pin's discrimination is intact.

---

## 5. AgentRefLike shared home — clean

- Live identity: `agent_ref.AgentRefLike is briefs.AgentRefLike is messages.AgentRefLike` → **all True**; `__module__ == "loremaster.agent_ref"` (neither ledger — `test_the_shared_home_is_neither_ledger_module` satisfied).
- Independent BARE-pattern sweep (`grep -rnI AgentRefLike --include=*.py`): every code reference accounted for. `messages.py` imports from `agent_ref`; `briefs.py:105` re-exports (`as AgentRefLike # noqa: PLC0414`); annotations in both ledgers resolve to the one Protocol (briefs mypy-clean). The fakes' `from loremaster.briefs import AgentRefLike` is **NOT a stale consumer** — it is the exact re-export path the contract PINS (`test_briefs_and_messages_expose_the_SAME_object` imports it that way). `server.py:1828` xref correctly repointed `~loremaster.briefs.` → `~loremaster.agent_ref.`.
- P8d natural-language check: no code/docstring teaches `briefs` as the DEFINITION home. The only qualified `briefs.AgentRefLike` mentions are the identity-invariant docstring (`agent_ref.py:8`, correct), the contract's own assertion text, the builder report, and an archived receipt. Clean.

---

## 6. RESIDUALS (latent — even on GO; surfaced per scope law, operator decides)

1. **Message id is `uuid4().hex`, not `ulid()` — needs an operator ruling.** The contract docstring says "bare ulid (no table prefix)" but the only id pin (`test_the_message_id_is_BARE_with_no_table_prefix`) checks bare-ness + round-trip, NOT time-sortability, so `uuid4().hex` satisfies it. No current consumer relies on sortable ids (`drain`/`awaiting_answer` order by `seq`). NOT hand-rolling a ULID is correct (packages-over-hand-rolling). **Fork for the operator:** accept `uuid4`, or authorize installing `python-ulid` if a downstream (03b renders, `since=` in pkt 05) will want time-sortable ids. The builder flagged this as deviation 4.
2. **`scripts/typecheck.sh` is globally RED (exit 1).** Expected under the 2026-07-23 deferral, and no writable prod file errors — but the *gate itself is not green*, and when 03b lands it must reach zero. Naming it so it is met deliberately, not silently inherited.
3. **`drain`/`peek` migrated from 03a-2 into 03a-1** (builder deviation 1, lead-CONFIRMED): 11 SEND pins call `drain(peek=True)`, so a stub makes them unsatisfiable. `drain` is correctly implemented (stamps exactly the served window `in IN $message_ids AND out=$agent AND seen_at IS NONE`; peek stamps nothing; counts over the whole set). Consequence: **03a-2's remaining scope is `ack` + `awaiting_answer` (+ 16-way ack concurrency + the derived-waiting read)** — the 31 stubs. The `03a-2-comms-ledger-consume.md` packet doc should be updated to record that `drain` already landed, so 03a-2's builder does not re-implement it.
4. **`_MIN_KNOWN_SEAMS = 10` left at 10** though there are now 11 seams. Low risk — the exact-set pin `test_every_seam_still_logs_its_OWN_canonical_rejection_event` already pins the 11-member set incl. `MessageLedger` — but the FLOOR is now slack. Optional: bump to 11 for a tighter floor.
5. **Recipient-existence check is a SEPARATE query from the atomic send** (validate-then-write TOCTOU window). Benign: agents are retired-never-deleted (store ref §4), and `ENFORCED` + the atomic txn is the backstop — a recipient vanishing between check and RELATE rolls the whole send back (proven live in Mutation C), so no dangling edge is possible. Noted, not a defect.
6. **`drain` loads ALL pending rows then caps in Python** (`window = pending[:limit]`). Required, because `total_pending`/`directive_pending` are (correctly) over the whole set — but for a very large unread inbox this is O(all-pending) per drain. Bounded in practice (2000-char pointer messages + drain cadence + the `(out, seen_at)` index). Scalability note only.
7. **`seq` is read back in a SECOND round-trip** after the atomic send (builder deviation 5). Race-free (read by the send's own `uuid` id; mirrors `briefs.publish`). Minor perf (2 round-trips/send), no correctness impact — `test_every_concurrent_send_is_readable_by_its_recipient` passes at 8-way.

**Commit:** the builder correctly did NOT commit (cold audit precedes the wave commit, repo law). The lead commits post-audit; the builder's suggested three one-concern commits are sound. `messages.py` remains at md5 `9ca1ba3d5ee7cf71f587150af06443d2`; the working tree is byte-identical to the builder's state (no probe residue; my backup lives only in `/tmp`).

---

## 7. Bottom line
**GO.** The 03a-1 SEND path, `drain`, the `AgentRefLike` home, and the module foundations are correctly built; the mint is a real native sequence proven under 8/16-way live contention, the fan-out is atomic all-or-nothing with a real `ENFORCED` backstop AND a typed app-level ghost guard, the seam genuinely rides the shared `_txn` retry driver (shared marker, not a private copy), and the `[real]` leg is graded and passing. The only red is the 31 expected 03a-2 `NotImplementedError` stubs. The seven residuals are latent, not blockers — but #1 (ulid vs uuid) wants an operator ruling and #3 (drain scope-migration) wants a one-line packet-doc update before 03a-2 starts.
