# 03a-1 — Comms ledger: the SEND path + AgentRefLike home + foundations · sub-packet 1/2 of 03a

> **DONE 2026-07-23. TEST-ONLY, nothing deployed.** Commits `2d1f75d`→`42eeedc`, plus the pool-#24
> ULID follow-up `13da377`. Cold-audit **GO**, `[real]` leg graded; send concurrency 20/20 ×3;
> #173 C-DEF fix proven non-weakening. Receipts:
> `docs/plans/v2/receipts/2026-07-23-packet03a1/`.
>
> ⚠ **STALE BELOW, deliberately preserved as the packet AS EXECUTED:** this doc describes `ack` and
> `awaiting_answer` as `raise NotImplementedError` stubs. That was true at 03a-1's close and is
> FALSE today — **03a-2 built both** (`f04729c` is the last of its commits), so the file now stands
> at 180 passed / 0 failed. Read `03a-2-comms-ledger-consume.md` for the consume path.
size ~0.20 wu · wave C · depends: **packet 03** (the store, DONE) · **DEPLOY: NO — test-only**
law: read `03a-comms-message-ledger.md` (the shared 03a reference — Scope IN/OUT, rulings) +
`comms-subsystem.md` + DESIGN-LAW §8/§5/§1 · **FIRST READ (repo store law):
`docs/reference/surrealdb-31-capabilities.md`** · task `6804b707d8994bf7adc87e7cc2692e8e`

## Why this sub-packet exists
03a (0.35) split at kickoff (sizing law ≥0.30; operator-confirmed 2026-07-23). This is the WRITE
path + the module foundations both sub-packets stand on; **03a-2** builds the CONSUME path
(drain/ack/derived-waiting) onto the `messages.py` this commits.

## Mission
Build the foundations + `send` of `loremaster/loremaster/messages.py`, plus the shared
`AgentRefLike` home, proven at ≥8-way send contention — against the committed RED contract
`loremaster/tests/test_message_ledger.py` (`efef2b3`, 180 pins). `_message_fakes.py` (the
ADVERSARIAL in-memory fake) and `render_injection_scaffold.py` ALREADY EXIST — the builder writes
the REAL module only; the fake is the reference oracle.

## Scope IN (03a-1's slice of 03a's Scope IN)
- **AgentRefLike extraction** — move the `Protocol` out of `briefs.py:224` into a NEW shared module
  (neither ledger module; the contract pins `AgentRefLike.__module__ not in {briefs, messages}`).
  `briefs.py` imports + re-exports it so `from loremaster.briefs import AgentRefLike` resolves to the
  **SAME object** (contract test at 2035). A bare-pattern rename sweep over every `AgentRefLike`
  mention (prod + tests + **docstrings/prose** — `server.py:1828`, `briefs.py:58/85`), each hit given
  an individual verdict (P8d natural-language-surface hazard — "all remaining hits are X" is banned).
- **Module foundations** — the FULL public type surface (`Message`, `MessageSendResult`,
  `InboxEntry`, `MessageDrainResult`, `MessageAckEntry`, `MessageAckResult`, `WaitingOnAnswer`,
  the `MessageGrade`/`AckOutcome` vocab, every error, every constant), so `_message_fakes.py`'s
  wholesale import resolves; `MESSAGE_BODY_MAX_CHARS` **imported from `surreal_schema`** (DRY —
  never redefined); `ensure_ready()` applying `generate_message_ddl()`; `close()`; the
  `async def _query` seam **spelled EXACTLY that** (the name-keyed enumerator silently drops ~19
  pins otherwise — the `scout.py` instrument-defeat, recommitted).
- **`send`** (+ `set_status` question-marking) — `sequence::nextval("message_seq")` + `CREATE` +
  N×`RELATE` in ONE `execute_transaction`; recipient-existence validation (a raw SELECT over the
  `agent` table — NOT an import of `loremaster.agents`) BEFORE any RELATE, all-or-nothing;
  dedupe-by-identity before the RELATE loop; body validation (blank / oversize-rejected-not-truncated
  / at-cap / hostile-stored-RAW / out-of-domain-grade); an empty recipient set is
  `EmptyRecipientSetError` — **the ledger never resolves a roster; broadcast (`to=[]`) is 03b's
  dispatcher** (contract §"DELIBERATE DECOUPLING").
- **send-side concurrency ≥8-way, 20 CONSECUTIVE green runs** — SEPARATE ledger instances on
  SEPARATE connections, overlapping lifetimes (models `test_findings.py` / `test_brief_ledger.py`,
  **not** the scripted `test_txn_contention` fake). `send` rides the shared `_txn.retry_on_conflict`
  driver — a private retry/classify is a copy wearing the shared name.
- **Structural pins** — seam-enumerator discoverability + DDL-slice-applied.

## Scope OUT (→ 03a-2)
`drain`/`peek`, `ack` (+ four-way disambiguation), `awaiting_answer` (the derived waiting state),
ack-side concurrency — these land as `raise NotImplementedError` stubs so the module imports; their
pins stay RED (03a-2's target). Also OUT (→ 03b): all renders / dispatch / promise proofs / deploy.

## Pin classes (03a-1's green target within the 180, both `[real]` and `[fake]` legs)
`TestVocabularies` · `TestSendWritesTheNodeAndOneEdgePerRecipient` ·
`TestSendValidatesEveryRecipientBeforeWritingAnyEdge` · `TestSendValidatesTheBody` ·
`TestSetStatusMarksTheQuestionItDoesNotStoreAState` · `TestSeqIsAnOrderingKeyNotACount` ·
`TestConcurrentSendsMintDistinctSeqs` · `TestTheLedgerIsDiscoverableByTheSeamEnumerator` ·
`TestTheDdlSliceIsAppliedByEnsureReady` · `TestAgentRefLikeHasONEHome`.

## Entry check
FIRST READ the store reference. Packet 03 DONE (schema slice + `generate_message_ddl` live); the
180 pins RED with `ModuleNotFoundError: No module named 'loremaster.messages'` (call-time imports
keep the file collectible — RED, not uncollectable); spike-surreal :18000 healthy; task `6804b707`
in play; `_message_fakes.py` + `render_injection_scaffold.py` present. **Coverage-premise
(render hygiene → 03b) CONFIRMED at kickoff:** the contract itself pins `body: RAW, never sanitised
in storage` + `test_a_hostile_body_is_stored_RAW`.

## Exit
03a-1 pin classes 100% green (real+fake) with a passed-COUNT in the tail; the module imports
cleanly; the ONLY residual failures are 03a-2's `[real]`-leg drain/ack/waiting pins failing with
`NotImplementedError` (enumerate them). `scripts/typecheck.sh` per-file clean (global mypy-zero
deferred to the 03b end — operator 2026-07-23, since the RED contract forward-refs 03b symbols) +
ruff clean + `test_retry_seam.py` green (send's seams driven). Cold REFUTE audit before commit
(builder ≠ grader) that **GRADES THE `[real]` LEG** (adversary §7.8). One-concern commits at natural
boundaries. **NO deploy.** INDEX row + Log + ledger row done (summary). Concurrency 20 consecutive
runs — builder discipline; a single green run NEVER clears it.
