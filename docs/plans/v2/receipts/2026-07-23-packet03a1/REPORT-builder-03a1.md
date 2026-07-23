brief-base v6 read

# REPORT — builder-03a1 · packet 03a-1 (comms ledger SEND path + foundations)

## SUMMARY BLOCK
> **UPDATE (post-lead-ruling):** the C-DEF fix was AUTHORIZED and applied (the sole contract edit — `_seed_agents:243` `CREATE`→`UPSERT`). All 10 required-green classes are now GREEN. Contract now differs from `efef2b3` by that one authorized helper line. Post-fix: **140 passed, 31 red (ALL 03a-2 stubs), 9 skipped**; the 2 formerly-blocked pins PASS; the unblocked concurrency pin is **20/20**. See §"C-DEF" (RESOLVED) and §5.

- state: **done** (SEND path + foundations GREEN; the only red is the 31 expected 03a-2 `NotImplementedError` stubs).
- All 10 required-green classes GREEN after the authorized C-DEF fix; the drain-scope and seam-registration deviations are lead-CONFIRMED.
- deviation 1: **`drain` is IMPLEMENTED, not stubbed** — 11 required-green SEND pins call `drain(peek=True)`; stubbing it makes the assigned green target unsatisfiable. Moves `drain` from 03a-2's scope into 03a-1. DECISION NEEDED. §"Scope forks".
- deviation 2: **`test_retry_seam.py` edited** (2 lines) — registered the required-discoverable 11th seam `MessageLedger` in `_SEAM_REJECTION_EVENTS`/`_SEAM_REJECTION_NOUNS` (the pin's own message sanctions the deliberate diff). §"Seam registration".
- deviation 3: **`server.py:1828`** Sphinx xref repointed `~loremaster.briefs.AgentRefLike` → `~loremaster.agent_ref.AgentRefLike` (rename sweep). deviation 4: **I did NOT commit** (see §"Commit fork").
- decisions-needed: (a) C-DEF fix for `_seed_agents` (`CREATE`→`UPSERT`) to unblock the 2 pins; (b) confirm `drain` belongs in 03a-1; (c) message id is `uuid4().hex` not a true `ulid()` (no ulid lib) — accept or install `python-ulid`. §"Decisions needed".
- receipts: 03a-1 classes 87 passed / 2 C-DEF-blocked / 7 skipped · full file 138 passed / 33 red (31 stubs + 2 C-DEF) · 20/20 concurrency · ruff clean · mypy: my files 0-error · test_retry_seam 503 passed · test_brief_ledger 120 passed · `import _message_fakes` OK. Pointers below.

---

## 1. What was built (file:symbol)

- **CREATE `loremaster/loremaster/agent_ref.py`** — the ONE shared `AgentRefLike` Protocol (read-only `id`/`name` properties, docstring rationale moved verbatim from briefs). `__module__ == "loremaster.agent_ref"` (neither ledger).
- **CREATE `loremaster/loremaster/messages.py`** — `MessageLedger` cloning the `briefs.py` blueprint: own lazily-opened connection (`_ensure_connection`/`ensure_ready`/`close`/`_drop_connection`/`_safe_close`), the `async def _query` seam (spelled EXACTLY, → `run_query`), `_apply` (→ `compose`+`execute_transaction`). Full public type surface: `Message`, `MessageSendResult`, `InboxEntry`, `MessageDrainResult`, `MessageAckEntry`, `MessageAckResult`, `WaitingOnAnswer` (all pydantic `extra="forbid"`); `MessageGrade`/`AckOutcome` Literals; constants `MESSAGE_GRADE_SIGNAL`/`MESSAGE_GRADE_DIRECTIVE`/`MESSAGE_GRADES` (runtime source = schema's own grade constants, DRY) + `MESSAGE_BODY_MAX_CHARS` (imported from `surreal_schema`, never redefined — landmine #4); errors `MessageLedgerError`(RuntimeError) + 4 subclasses. `send` + `set_status`, `drain` implemented; `ack`/`awaiting_answer` = `NotImplementedError` stubs (03a-2).
- **MODIFY `loremaster/loremaster/briefs.py`** — removed the local `class AgentRefLike` (was `:224`); `from loremaster.agent_ref import AgentRefLike as AgentRefLike  # noqa: PLC0414 (re-export)`; removed now-unused `Protocol` from the `typing` import. `_BareAgentRef`, `coverage()`/`_acked_versions_for_roster` annotations resolve against the imported Protocol (mypy-clean). `briefs.AgentRefLike is messages.AgentRefLike is agent_ref.AgentRefLike` — one object.
- **MODIFY `loremaster/loremaster/server.py`** — rename sweep: `_HeartbeatAgentLike` docstring xref `~loremaster.briefs.AgentRefLike` → `~loremaster.agent_ref.AgentRefLike`.
- **MODIFY `loremaster/tests/test_retry_seam.py`** — 2 lines: added `"MessageLedger": "message.query.rejected"` to `_SEAM_REJECTION_EVENTS` and `"MessageLedger": "message query"` to `_SEAM_REJECTION_NOUNS` (see §"Seam registration").

### `send` mechanism (store reference §5/§4/§7)
Validate → mint+write → read-back. Order (matches the fake oracle): grade domain → body strip/blank/over-cap/at-cap → empty-recipients → **recipient existence** (a raw `SELECT id FROM $ids` over `agent`, direct-record-access, returns only existing ids — [PROBED 2026-07-23, spike-surreal 3.2.1: a non-existent RecordID is silently dropped, so ghosts are exactly `requested − returned`]) → **dedupe by row IDENTITY** → ONE `execute_transaction` composing `LET $minted_seq = sequence::nextval("message_seq")` + `CREATE message CONTENT {…}` + N×`RELATE $msg_rec->to->$recipient SET session=…, created_at=…` (bound `RecordID`s) → read `seq` back by the Python-minted id (`execute_transaction` returns nothing; the read is by the row's own id, race-free). `created_at` is Python-stamped (agent/task idiom); message id is `uuid4().hex` (bare). Everything rides the shared `_txn` driver via `_query`/`execute_transaction` — no hand-rolled retry/classify.

### `drain`
Windowed inbox read: `SELECT in.<fields>, acked_at, ack_note FROM to WHERE out=$agent AND seen_at IS NONE`, sorted by `seq` in Python (the fake decorrelates id-order adversarially; the real store guarantees no incidental order), `total_pending`/`directive_pending` over the WHOLE set, window = oldest `limit`, non-peek stamps EXACTLY the window (`UPDATE … WHERE out=$agent AND in IN $window AND seen_at IS NONE`).

---

## 2. Scope forks / deviations (DECISIONS NEEDED)

### DEVIATION 1 — `drain` implemented, not stubbed (the brief said stub it)
The brief and packet doc say `drain`/`ack`/`awaiting_answer` land as `NotImplementedError` stubs (03a-2). **But 11 required-green SEND pins call `drain(peek=True)` to verify delivery** — e.g. `test_the_message_id_is_BARE…`, `test_fan_out_reaches_every_recipient…`, `test_a_sender_never_receives_its_own_message`, `test_EVERY_recipient_actually_RECEIVES…`, `test_a_mixed_batch_is_all_or_nothing`, `test_an_oversize_body_is_REJECTED…`, `test_a_hostile_body_is_stored_RAW`, `test_a_question_still_delivers_normally`, `test_a_gap_breaks_nothing`, `test_every_concurrent_send_is_readable…`. A `NotImplementedError` `drain` makes the assigned SEND green target **unsatisfiable**. The contract (frozen at `efef2b3`, monolithic 400-pin file) was NOT split when the packet was; the send-verification/drain coupling was inherited.
- **My reading (chosen):** implement `drain` fully (it is well-specified by the fake oracle; correct implementation makes the drain-dedicated pins go green too — a bonus, not a defect). `ack`/`awaiting_answer` stay stubbed (no SEND pin needs them; the genuinely hard 03a-2 work — the four-way CAS disambiguation + 16-way ack concurrency + the derived-waiting read — is untouched).
- **Alternative:** keep `drain` stubbed and REMOVE the ~11 drain-dependent pins from 03a-1's green target (then they + the drain-dedicated pins all become 03a-2's).
- **Consequence for 03a-2:** its remaining scope is `ack` + `awaiting_answer` (+ their concurrency). Please confirm this is acceptable or tell me to revert.

### DEVIATION 2 / C-DEF — RESOLVED (lead-authorized fix applied)
**Lead ruling (verified): AUTHORIZED.** Applied the sole contract edit — `_seed_agents` (`test_message_ledger.py:243`) `CREATE type::record('agent', $id) CONTENT $content` → **`UPSERT …`**. Post-fix: the 2 formerly-blocked pins PASS (`2 passed`), full contract `140 passed, 31 red (all stubs), 9 skipped` — no regression, no new red. The contract now differs from `efef2b3` by exactly this one line. Original diagnosis (kept for the record):
`_seed_agents` (contract, immutable, `test_message_ledger.py:225`) registers agents with a raw `CREATE type::record('agent', $id) …`. Two required-green tests call it with an **already-existing agent id**:
- `TestSendWritesTheNodeAndOneEdgePerRecipient::test_a_send_in_a_DIFFERENT_session_records_that_session` — the `message_ledger` fixture pre-seeds `lead`/`fixer-b` in wave7; the test re-seeds the SAME ids in wave9.
- `TestConcurrentSendsMintDistinctSeqs::test_concurrent_seqs_all_exceed_the_pre_race_maximum` — the test seeds, then `_race` re-seeds the same ids on the same DB.

`CREATE` on a duplicate row id RAISES (`AlreadyExistsError: Database record 'agent:'lead-id-0000'' already exists`, [PROBED 2026-07-23]). The `[fake]` leg passes because `register_agent` is idempotent — so the fake and real seed paths are **not equivalent**, which is the defect. The adversary never graded `[real]` (packet doc §Entry: "the `[real]`-tier ledger leg is UNGRADED").
- **This is not my code** and `_query` cannot make a `CREATE` idempotent without breaking the retry-seam contract (which requires `_query` to raise on domain rejections).
- **PROOF (mutation, byte-exact restore):** patched `_seed_agents`'s `CREATE`→`UPSERT` in-tree (content-backup first), the 2 pins went **2 passed**, restored (md5 identical). So my send code is correct; the helper is the sole blocker.
- **Recommended fix (yours to make — contract is immutable to me):** `_seed_agents` `CREATE` → `UPSERT type::record('agent', $id) CONTENT $content` (idempotent, last-write-wins — matches the fake). One line.

### DEVIATION 3 — `test_retry_seam.py` registration (see §"Seam registration")
### DEVIATION 4 — message id is `uuid4().hex`, not a true `ulid()`
The design/schema note the id as `ulid()` (time-sortable). **No ULID lib is installed** (`import ulid` fails). No contract pin requires sortability (`drain`/`awaiting_answer` order by `seq`, never id; the only id pin is `test_the_message_id_is_BARE…`). Per the packages-over-hand-rolling rule I did NOT hand-roll a ULID: I used `uuid4().hex` (bare, unique, stdlib) and flag it. If time-sortable ids are wanted, escalate to install `python-ulid`.
### DEVIATION 5 — `seq` read-back
`send` mints `seq` INSIDE the one `execute_transaction` (per landmine #5) but `execute_transaction` returns nothing, so `seq` is read back by the row's own id in a following `SELECT` (mirrors `briefs.publish`'s `_select_row` read-back). Two round-trips; the read is race-free (id is unique to the send).

### COMMIT FORK — I did NOT commit
The brief says "commit at natural boundaries" AND "your 'green' is a CLAIM I verify with a cold REFUTE audit (builder ≠ grader) … end your turn; I will read the report", and the repo law is "cold REFUTE audit before every wave commit". Committing unaudited work would violate that. **Reading chosen:** leave the work in the working tree and commits to you (post-audit). Suggested one-concern commits: (1) `feat(comms): AgentRefLike shared home + briefs re-export + server xref`; (2) `feat(comms): messages.py MessageLedger — send + drain + foundations (03a-1)`; (3) `test(retry-seam): register MessageLedger as the 11th query seam`. If you meant me to commit, say so.

---

## 3. The AgentRefLike rename sweep (BARE anchor-free grep, every hit + verdict)
Command: `grep -rnI "AgentRefLike" --include=*.py --include=*.md` (whole repo, ex-`.venv`). P8d: prose surfaces get individual verdicts; "all remaining hits are X" is banned.

| file:line | kind | verdict |
|---|---|---|
| `agent_ref.py` (new) | DEFINITION | **the new home** |
| `briefs.py:224` | class def | **REMOVED** (moved to agent_ref) |
| `briefs.py` import line | import | **REPOINTED** to agent_ref, re-exported (`as … # noqa: PLC0414`) |
| `briefs.py:58` | module-docstring API listing | KEEP — briefs still EXPOSES it (re-export); not a wrong import |
| `briefs.py:85` | module-docstring prose ("accepts an AgentRefLike roster") | KEEP — still true |
| `briefs.py:247` | `_BareAgentRef` docstring `:class:` xref | KEEP — resolves via briefs' re-exported name; `_BareAgentRef` still satisfies it |
| `briefs.py:997` | `coverage()` annotation | KEEP — resolves to imported Protocol (mypy-clean) |
| `briefs.py:1190` | `_acked_versions_for_roster` annotation | KEEP — same |
| `server.py:1828` | Sphinx xref `~loremaster.briefs.AgentRefLike` | **UPDATED** → `~loremaster.agent_ref.AgentRefLike` (points at the definition) |
| `messages.py` (new) | import + annotations | imports from agent_ref; re-exports the same object |
| `_comms_fakes.py:96` | `from loremaster.briefs import AgentRefLike` | KEEP — re-export keeps it working (test_brief_ledger 120✓) |
| `_comms_fakes.py:623` | annotation | KEEP — same |
| `_message_fakes.py:43` | `from loremaster.briefs import AgentRefLike` | KEEP (DO-NOT-TOUCH) — works via re-export |
| `_message_fakes.py:173,177,214` | annotations | KEEP — same |
| `test_brief_ledger.py:51,81,177` | docstring prose | KEEP — still accurate; briefs exposes it; suite green |
| `test_message_ledger.py:75,201,2026,2036,2038,2044,2045,2049` | the CONTRACT (immutable) | KEEP — these are the pins driving the requirement; `TestAgentRefLikeHasONEHome` passes |
| `docs/plans/v2/{03,03a,03a-1,INDEX}.md` | planning-doc prose | KEEP — describe the work ("move AgentRefLike to a shared home") — accurate, not a code consumer |
| `docs/plans/v2/receipts/2026-07-19-packet03/*.md` | archived reports | KEEP — archived historical records |

Removed-behaviour inventory for `briefs.py`: the ONLY removed behaviour is briefs DEFINING the Protocol; it still EXPOSES the identical object (re-export) with identical `id`/`name` members, and `coverage()`/`_acked_versions_for_roster` still typecheck against it (mypy 0 errors in briefs). `test_brief_ledger.py` stays green (120 passed).

---

## 4. Seam registration (`test_retry_seam.py`, DEVIATION 2)
`TestTheLedgerIsDiscoverableByTheSeamEnumerator` REQUIRES `MessageLedger` to be discovered by `_discover_query_seams()` (name-keyed on `async def _query`). Discovery makes it the **11th** seam, which `test_every_seam_still_logs_its_OWN_canonical_rejection_event` compares (driven from the discovered set) against the hardcoded `_SEAM_REJECTION_EVENTS`/`_SEAM_REJECTION_NOUNS` (10 entries). An unregistered 11th turns that exact-set pin RED. **This is a regression my in-scope (required) change directly causes**, and the pin's own failure message instructs: "Add or remove the entry DELIBERATELY, in a diff a reviewer can see." I added the two entries (`message.query.rejected` / `message query` — the `<domain> query` convention the other 5 ledger seams use), and `messages.py::_query` emits exactly those. `_MIN_KNOWN_SEAMS = 10` left unchanged (it is a floor; `11 >= 10`; optionally bump to 11 for a tighter floor — your call). Result: **test_retry_seam.py 503 passed** (incl. the coverage pin `test_every_production_sdk_call_site_was_OBSERVED_by_the_guard` — `messages.py`'s only connection-receiver SDK calls are `signin` in `_ensure_connection` and `close` in `_safe_close`, both driven by that pin; send/drain route through `_query`/`execute_transaction`, whose sites live in `_txn.py`).

---

## 5. Gate receipts
> **POST-C-DEF-FIX (authoritative):** Full `test_message_ledger.py` (`-n auto`, :18000): **`31 failed, 140 passed, 9 skipped`**. The 31 red are EXACTLY the 03a-2 stubs — 13 `ack` + 18 `awaiting_answer` `NotImplementedError`, all `[real]` leg (their `[fake]` legs pass); a filtered re-run confirms **zero non-stub red**. The 2 formerly-blocked pins (`test_a_send_in_a_DIFFERENT_session_records_that_session[real]`, `test_concurrent_seqs_all_exceed_the_pre_race_maximum[real]`) now **pass**. Newly-unblocked concurrency pin `test_concurrent_seqs_all_exceed_the_pre_race_maximum[real]`: **20/20 consecutive green**.

Pre-fix receipts (kept for the record):
- **03a-1 required-green classes** (`-n auto`, :18000): `2 failed, 87 passed, 7 skipped` — the 2 failed were exactly the C-DEF pins (now fixed); the 7 skipped are `[fake]`-leg raw-store observations.
- **Full `test_message_ledger.py`** (pre-fix): `33 failed, 138 passed, 9 skipped`. The 33 red decomposed EXACTLY as: 13 `ack` `NotImplementedError` + 18 `awaiting_answer` `NotImplementedError` (= the 31 03a-2 stub residuals) + **2 C-DEF** (`AlreadyExistsError` inside `_seed_agents`, now resolved). No other red.
- **Enumerated residual RED `[real]` legs (03a-2 stubs — MUST be `NotImplementedError`, confirmed):** `TestAckIsWriteOnce` (3) · `TestAckDisambiguatesTheFourWayEmptyReturn` (9) · `TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner` (1) · `TestTheWaitingStateIsDerived` (16) · `TestTheDerivedWaitingStateKnownBound` (2). All fail at `messages.py` `raise NotImplementedError` (ack :807 / awaiting_answer :819), NOT import errors.
- **Concurrency 20-run:** 3 send-concurrency `[real]` pins (`test_eight_concurrent_sends_all_land_on_distinct_seqs`, `test_at_scale[16]`, `test_every_concurrent_send_is_readable_by_its_recipient`) run 20× consecutively → **20/20** green (`test_concurrent_seqs_all_exceed…` excluded — C-DEF-blocked, not a concurrency failure).
- **`import _message_fakes`** (landmine #3, after all edits): **OK**.
- **`ruff check .`**: **All checks passed!**
- **`scripts/typecheck.sh`**: my writable files (`messages.py`, `agent_ref.py`, `briefs.py`, `server.py`, `test_retry_seam.py`) = **0 errors**. 36 residual errors are all in 03b test files I did not touch (`test_comms_tool.py` 31, `test_comms_promise_registry.py` 3 — 03b render/tool symbols) + 2 pre-existing contract `no-any-return` (`test_message_ledger.py:1716/1736`); **none reference my new module or symbols**. These are the expected RED-contract 03b forward-refs (global mypy-zero deferred to 03b end, operator 2026-07-23). NB: could not diff against a pristine HEAD baseline without mutating git state; evidence (0 in my files, 0 referencing my symbols, `loremaster.messages` now resolves for `_message_fakes`) indicates my change REDUCED, not increased, the count.
- **`test_retry_seam.py`**: **503 passed**. **`test_brief_ledger.py`**: **120 passed** (AgentRefLike move safe).

## 6. Store-law probes run (receipts, spike-surreal 3.2.1 :18000, throwaway DBs)
1. `SELECT id FROM $recs` (direct record access) returns ONLY existing records — the recipient-existence check's correctness (ghost silently dropped, not echoed). 2. `session` is a protected PARAM name (`{"session": …}` → "protected variable"); the COLUMN and `SET session = $msg_session` are fine — fixed by binding `$msg_session`. 3. Duplicate `CREATE type::record('agent', id)` RAISES `AlreadyExistsError` (the C-DEF root cause).

## 7. Do-not-declare-victory
Per the brief, this "green" is a CLAIM. The `[real]` leg needs your cold REFUTE audit (builder ≠ grader). Load-bearing items to grade independently: the atomic all-or-nothing send (no partial edges on a rejected fan-out), the ghost-recipient guard, the mint under contention, and the C-DEF diagnosis (re-run the mutation proof if you want the receipt). I did not commit; the working tree holds 2 new files + 3 modified.
