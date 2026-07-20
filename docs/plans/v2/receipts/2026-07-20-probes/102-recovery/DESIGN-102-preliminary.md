# DESIGN-102 — preliminary ruling: the hot-row mint retry substrate

brief-base v2 read
design-consultant · 2026-07-12 · status: PRELIMINARY — §4's conditionality is NARROWED
by the house SurrealDB 3.1 capability reference (sequences are "New in 3.0", so the
probe settles only the function name + first-boot seeding, not existence; primary path
expected). See `DESIGN-102-addendum-2026-07-12-surrealdb-capabilities.md` for the
integration; both §4 outcomes remain analysed below.

## Verdict table (the whole ruling in six lines)

1. **Root cause of #102 is DETERMINISM, not budget size.** Three stacked determinisms
   keep racers in lockstep; enlarging budgets only lengthens the lockstep. 60 total
   attempts (12×5) already fail 4 runs in 5.
2. **Q1: retry lives in the SHARED seam ONLY.** Redesign `execute_transaction`'s policy:
   per-attempt FRESH full jitter (process PRNG), exponential-with-cap, a TIME budget
   (deadline, default 2.0 s) with a generous attempt ceiling as a runaway backstop only.
   `findings._apply_mint`'s outer loop is DELETED. Stacked budgets are ruled a bug.
3. **Q1 exhaustion mode: raise — fast, typed, hygienic.** New
   `TxnContentionExhaustedError(SurrealStoreError)`. Never block, never degrade.
4. **Q2: `finding.number` stays on the (repaired) counter row.** Right shape at its
   write rate; gaplessness was asserted in prose but is load-bearing nowhere. No
   migration, no schema churn.
5. **Q3: `message.seq` = native DEFINE SEQUENCE if the probe confirms** (I concur with
   the scout ruling already in the plan). Fallback if refuted: reserve-then-create — a
   single-statement counter bump OUTSIDE the send transaction (briefs.py's topology),
   burning a number on abort exactly as the plan already accepts. **Never mint inside
   the fan-out transaction** under either outcome.
6. **The Q1 substrate repair ships regardless of the probe** — tasks, findings, and every
   C2 CAS/edge write ride the same seam.

---

## 0. Ground truth read (receipts)

- `loremaster/store/_txn.py:333` `_MAX_TXN_CONFLICT_ATTEMPTS = 5`; `:339`
  `_TXN_CONFLICT_BACKOFF_SECONDS = 0.01`; `:549` `await asyncio.sleep(_TXN_CONFLICT_BACKOFF_SECONDS * (attempt + 1))`
  — deterministic linear backoff, zero jitter, shared by every composed transaction.
- `loremaster/findings.py:253-256` mint constants (12 attempts / 0.01 backoff / 16
  jitter slots / 0.001 s per slot); `:780` jitter slot computed ONCE per call from
  `finding_id[:4]`; `:792-794` sleep = linear backoff + that fixed offset; `:771-776`
  the docstring's own 12×5=60 worst-case admission and the (now stale) "N=16 probe
  stayed clean" claim; `:244-245` the measured 43 % txn-exhaustion at N=8.
- `loremaster/briefs.py:159-162` (4 jitter slots), `:661` fresh `uuid4()` seed per
  publish CALL (the cfb36d2 fix — correct seed, still fixed across its 20 attempts),
  `:663-668` the contended statement is ONE single-statement UPSERT via `_query`,
  outside any composed txn; `:711-713` the compensating counter decrement (reserve /
  un-burn topology).
- `git show cfb36d2` — C1 post-mortem: jitter seeded from the contended row's
  `uuid5(name, version)` was identical across racers; failed ~4 of 5 runs; fix holds
  20/20 at 8-way.
- `loremaster/tasks.py` — the 2-way claim/transition constituency: guarded-CAS UPDATE +
  `THROW` on zero rows. A CAS miss is a DOMAIN rejection (never retried by the seam);
  only genuine engine write-write conflicts hit the retry path. 5 attempts is ample there.
- `docs/reference/surrealdb-31-capabilities.md` (the house 3.1 capability reference,
  Opus scout 2026-07-11): `:38-44` DEFINE SEQUENCE is New in 3.0, NOT gapless, burns on
  abort, name needs probing, "counter-table mint stays for finding.number"; `:98-102`
  the engine has NO server auto-retry — bounded client retry on the conflict marker is
  the documented idiom (OTel `transaction.conflicts`/`.retries` counters exist);
  `:45-49` ULID/UUIDv7 ids time-sortable + range-queryable; `:64-69` CHANGEFEED is the
  ordered-replay tool. Integrated in the 2026-07-12 addendum.
- `docs/plans/v2/PKT-28-agent-comms.md:33,43-44,89-90,105` and the garden plan §Data
  model (~lines 90-93, 106, 217-219, 476): scout already ruled `message.seq` = native
  DEFINE SEQUENCE + `sequence::next()` (name vs `nextval` is a C1 probe); "not gapless";
  "an aborted send burns a number, benign"; drain/unread state rides to-edge `seen_at`
  stamps, NOT a seq cursor.

## 1. Why the current mechanism actually fails

The failure is not that 60 attempts are too few. It is that the attempts are
**correlated**, so attempt count barely buys success probability:

1. **The inner loop is fully deterministic.** All N racers that collide in a round
   sleep *identically* (`10ms × (attempt+1)`), re-arrive together, and re-collide. The
   comment at `_txn.py:336-339` says the sleep exists "so two colliding retries do not
   immediately re-race in lockstep" — its determinism GUARANTEES lockstep. (A
   prose-describes-mechanism-wrong instance of the house PKT-28 C1 class; flag §6.2.)
2. **The outer jitter is per-racer but still a fixed phase.** `findings.py` seeds
   correctly (unique `finding_id` — the C1 lesson is honoured) but: (a) only 16
   discrete slots — at N=8 the probability that at least two racers share a slot is
   1 − (16·15·…·9)/16⁸ ≈ **87.9 %**, expected ≈1.75 colliding pairs per run; (b) the
   slot is computed ONCE, so a colliding pair stays in lockstep for the entire
   12-attempt ladder; (c) 1 ms slot granularity is smaller than the transaction's own
   window, so even distinct adjacent slots overlap the conflict window.
3. **The two budgets multiply latency, not success.** Each outer attempt burns the
   whole deterministic inner ladder (5 lockstep attempts + up to 100 ms of lockstep
   sleeps) before the outer fixed offset even applies.

**Why briefs.py "holds 20/20" with a strictly WORSE slot count (4 slots — pigeonhole
guarantees a shared slot at 8-way):** its contended statement is one tiny UPSERT
(`briefs.py:663-668`), so the conflict window is microseconds and natural RTT/scheduling
variance is enough accidental desynchronisation. findings' window is the whole composed
`BEGIN … COMMIT` (LET-UPSERT + CREATE + per-statement verification) — a window long
enough that schedule variance cannot save it. briefs survives by accident, not design
(flag §6.1).

## 2. Q1 — the substrate ruling

### 2.1 A TIME budget, not an attempt count derived from racer count

**Deriving the budget from the racer count is the wrong frame.** The racer count is
unknowable at call time, non-stationary (agents join mid-retry), and — decisively —
unnecessary: randomized exponential backoff is *self-adapting to any N with zero
coordination*; that is the entire point of the technique. What the caller CAN state is
its latency invariant, so the budget is a **deadline**:

- `execute_transaction(..., conflict_deadline_seconds: float = 2.0)` — retry retryable
  conflicts until the deadline; raise typed on exhaustion.
- A generous attempt ceiling (e.g. 64) as a **runaway backstop only** — early full-jitter
  sleeps can be near zero and a pathological loop must not spin thousands of times
  inside the deadline. The ceiling is not the budget; the deadline is. Both are logged
  on exhaustion.

Latency envelope sanity: under OCC one racer commits per overlap window, so the last of
N racers completes in ≈ N × (RTT + E[sleep]). At N=16 on the local store
(~2 ms RTT, mean sleep ≈ 20 ms) that is ≈ 350 ms — comfortably inside 2.0 s. N=32
bursts ≈ 700 ms. The default needs no per-caller tuning today; the kwarg exists for C2
if measurement ever says otherwise.

### 2.2 Jitter: shape and entropy source

**Shape: full jitter, exponential with cap, REDRAWN EVERY ATTEMPT.**

    sleep_n = uniform(0, min(CAP, BASE * 2**n))      # BASE = 0.005 s, CAP = 0.1 s

Why this shape fits OCC specifically: an optimistic-concurrency conflict is a *time
overlap* of transaction windows. Spreading retry start times uniformly over an interval
that doubles per round drives the pairwise overlap probability down geometrically, with
no coordination and no census of racers. Decorrelated jitter is an acceptable
alternative (near-identical completion time per Brooker's AWS analysis); full jitter is
simpler to reason about and to pin in tests. Deterministic linear — the status quo — is
the pessimal choice on both metrics.

**Entropy source: the process PRNG (`random.random()`), drawn fresh inside the loop.**
- Per-racer by construction: same-process asyncio racers interleave draws from one
  stream (distinct values); cross-process racers (pytest-xdist workers, separate
  containers) have independently seeded streams.
- NEVER derived from the contended row's identity (the C1 law, cfb36d2).
- NEVER precomputed once per call — findings' residual bug is exactly that: a fixed
  per-racer offset is just a per-racer *phase* of the same deterministic schedule. Two
  racers sharing a phase stay in lockstep forever. Redrawing per attempt means even a
  pair that collides once diverges on the next round with probability ≈ 1.
- No security requirement → `random`, not `secrets`; document the why-not-row-derived
  at the constant, since that is where the next author will look.

### 2.3 Where the retry lives: the SHARED seam, and only there

- The conflict is an engine artifact of optimistic concurrency. A domain caller has no
  information to add to the retry decision — it can only duplicate the loop, which is
  what happened.
- **Two stacked loops are ruled a BUG, not a feature.** They multiply budgets (12×5=60)
  and worst-case latencies opaquely; nobody can state the system's latency envelope
  from either file alone. The outer loop in `findings._apply_mint` exists solely
  because the seam's budget was neither adequate nor tunable. Once it is, DELETE the
  outer loop (keep at most a thin wrapper that maps the typed exhaustion error into the
  ledger's vocabulary, if the contract wants that).
- The seam's contract gains one **documented invariant**: a statement handed to
  `execute_transaction` must be safe to re-run WHOLE. Every current caller qualifies —
  the mint's `LET` re-reads the counter at its latest committed value on each attempt;
  the CAS transitions guard with `WHERE … THROW`, and a CAS miss is a domain rejection
  the seam never retries. State this in the module docstring so the next caller designs
  to it.
- Caller-level retry remains legitimate in exactly one situation: when the retry unit is
  LARGER than one transaction — briefs.py's reserve/compensate topology (bump, then
  CREATE, then un-burn on failure) is a genuine two-step protocol, not a second budget
  wrapped around the same transaction. That pattern stays caller-side by nature.
- **2-way constituency non-regression** (tasks.py): the no-conflict fast path is
  unchanged (zero sleeps); a single 2-way conflict now sleeps `uniform(0, 10 ms)` — in
  expectation HALF of today's fixed 10 ms; non-retryable rejections still surface
  immediately; the API change is an optional kwarg with a default. Nothing regresses.

### 2.4 The failure mode we want on genuine exhaustion

**Raise — fast, typed, hygienic.** `TxnContentionExhaustedError(SurrealStoreError)`,
carrying attempts + elapsed in its message, keeping ledger-#31 hygiene (classified
label, no raw engine text). Rationale for each rejected alternative:
- **Not block/loop forever:** with correct jitter, exhaustion of a 2 s deadline means
  genuine overload; unbounded waiting converts an overload signal into a hang and
  removes backpressure from the one place it can act (the client).
- **Not degrade:** there is no safe degraded mint — a duplicate or unordered number is
  strictly worse than a refused one (UNIQUE index would reject it anyway, later and
  more confusingly).
- The MCP layer renders it as a teaching error ("store under heavy write contention —
  retry"), which is honest: the operation is safely rolled back and idempotently
  re-runnable. Server-side corroboration exists: the engine's OTel
  `transaction.conflicts`/`.retries` counters (capability reference `:101`) are the
  operator's independent witness for a raised exhaustion — and the honest instrument
  for the §5 post-repair latency measurement.
- A NEW typed class (not a bare `SurrealStoreError` + substring) so callers and tests
  discriminate it structurally; `findings.py` currently string-matches the classified
  label (`:790`) — that seam becomes `except TxnContentionExhaustedError` and then
  disappears with the deleted loop.

## 3. Q2 — is the counter row the right shape at all?

Tease the two surfaces' requirements apart first — they are NOT the same problem:

| surface | actually needs | does NOT need | write rate |
|---|---|---|---|
| `finding.number` | unique · ascending · compact human-citable (#102) · stable forever | gapless · strict commit-order monotonicity | tens/day, occasional 8-16-way test bursts |
| `message.seq` | unique · compact ack/render handle (`ack seqs=[14,17]`) · roughly ascending display | gapless (plan waives it VERBATIM) · commit-order monotonicity (edge stamps own delivery state) | every message from every agent — the whole fleet, bursty |

**Was a strictly-monotonic gapless global counter ever actually required? No.** For
findings, "gapless" appears in the module docstring but nothing consumes it: `get`
addresses by number, `query` orders by number, the UNIQUE index backstops uniqueness —
all survive gaps. For messages the plan waives gaps explicitly. It is a requirement
nobody challenged; strike it from the vocabulary (demote the docstring claim to
"consecutive in practice" when the file is next opened).

Ruling per option:

- **(a) Counter row, repaired — CORRECT for `finding.number`.** At tens/day the hot row
  is a non-issue once the substrate is repaired (the pinned 8/16-way tests are the
  stress case, and §2's math covers them with an order of magnitude to spare).
  Mint-inside-txn keeps numbers consecutive as a free side effect. Zero migration, zero
  schema churn, and #102's failing test goes green on the substrate repair alone.
- **(b) Native DEFINE SEQUENCE — CORRECT for `message.seq` (conditional, §4).** Zero
  contention by design; non-gapless is pre-accepted. For `finding.number` it would also
  work, but buys nothing at findings' rate and costs a live-table migration (seed the
  sequence at `max(number)+1`); not part of #102. Optional future hygiene, nothing more.
- **(c) Per-session/per-agent sharded counters — REJECTED for both.** Destroys the
  single citable number line (the handle becomes an (agent, n) pair), complicates every
  render, and solves a problem messages don't have — ordering already has a better
  owner (the ULID id). Note the codebase ALREADY uses sharding where it is right:
  `brief_counter:<name>` is per-name — which is exactly why brief contention is
  per-name only. The pattern is fine; it just doesn't fit a global human-facing number.
- **(d) ULID as the handle — REJECTED as the RENDERED handle, RETAINED as the order
  authority.** A 26-char handle in `ack seqs=[…]` is token-hostile and typo-prone;
  compact integers are the whole point of `seq`. But true message order belongs to the
  ULID/`sent_at`, never to `seq` — see the cursor caveat below.

**Caveat pinned for C2 (either mint):** sequence/counter values can commit OUT of
allocation order — message #15 can become visible before #14. A `since=<seq>`
incremental cursor would silently skip. The plan already routes unread state through
to-edge `seen_at` stamps (garden plan ~:218) — keep it that way; ban seq-cursor reads
as a design law in the C2 contract.

## 4. Q3 — the C2 recommendation for `message.seq`

**PRIMARY (probe confirms a native sequence in 3.1.5):** `DEFINE SEQUENCE IF NOT
EXISTS` at `ensure_ready`, mint via `sequence::next()`/`nextval()` (the probe settles
the name) inline in the send transaction text. Sequences are non-transactional, so an
aborted send burns a number — the plan accepts this verbatim. No counter table, no
added retry pressure, no hot row. This concurs with the scout ruling already adopted in
PKT-28 (:33, :43-44); the probe is confirmation, not a new decision.

**FALLBACK (probe refutes):** reserve-then-create — briefs.py's proven topology at C2
scale:
1. Reserve: single-statement `UPSERT message_counter:singleton SET next += 1 RETURN
   AFTER` via `_query`, riding the REPAIRED seam-classification retry (jittered,
   deadline-bounded). The conflict window is one tiny statement — the shape that
   already survives 8-way today even with bad jitter.
2. Create: the send transaction (message node + to-edge fan-out) with the reserved seq.
   A failed send burns the number — same accepted semantics as the sequence.
   (The compensating decrement briefs.py uses is OPTIONAL here and I recommend
   OMITTING it for messages: burns are pre-accepted, and the un-burn CAS only pays when
   the failed mint is the newest — complexity without a requirement behind it.)

**Under NO outcome mint inside the fan-out transaction.** That repeats the findings
mistake at 10× the traffic: it makes the entire message + N-edge write the conflict
window, and every counter conflict rolls back and re-executes the whole fan-out.

**The Q1 substrate repair is a C2 prerequisite regardless of the probe:** drain/ack
stamps are write-once CAS, `set_status` contends on agent rows, and blocks-edge writes
share rows — C2 rides `execute_transaction` everywhere even if `seq` never touches a
counter row.

## 5. Evidence that would move these rulings

- **The probe result** — narrowed by the capability reference (`:38-44`: sequences
  exist since 3.0): the probe settles the function NAME (`next` vs `nextval`),
  first-boot seeding (3.1.0-beta.3 fix), and the `BATCH` default (gap width across
  restarts). Only a probe SURPRISE flips §4 to the fallback. `IF NOT EXISTS` /
  `START` syntax get recorded for any future finding.number migration.
- Any consumer actually depending on gapless finding numbers (I found none; the claim
  lives only in prose). Would forbid ever migrating findings to a sequence — it would
  NOT change §2 or the #102 fix.
- A post-repair latency distribution at N=32 with p99 approaching the deadline — would
  justify raising the 2.0 s default or per-caller tuning. I expect ~700 ms; measure,
  don't assume.
- Clearance law: the pinned 8-way test needs **20 consecutive** green runs post-repair
  (repo law — a single green never clears a concurrency test), under `-n auto` load.

## 6. Residual flags (surfaced, not fixed — operator owns scope)

1. **briefs.py carries the same lockstep class** (`:159-162` four slots — pigeonhole
   guarantees a shared slot at 8-way; `:661` slot fixed across all 20 attempts). It
   survives only because its conflict window is one tiny statement. It should migrate
   to the repaired seam idiom (or at least redraw jitter per attempt) next time the
   file is legitimately open. DO-NOT-EDIT honoured; this is a flag.
2. **`_txn.py:336-339` prose lies about its mechanism** ("non-zero so two colliding
   retries do not immediately re-race in lockstep" — determinism guarantees exactly
   that lockstep). Must be rewritten WITH the repair, and it is a fresh instance of the
   PKT-28 C1 served-English class worth citing in the fix commit.
3. **`findings.py:776` "measured-safe (the live N=16 concurrent-mint probe stayed
   clean)"** is contradicted by the pinned test failing ~4/5 under `-n auto` parallel
   load — a safety claim derived from a retired measurement. Dies with the deleted loop.
4. **Pins the repair's contract must carry** (for the contract author + adversary, not
   me): (a) jitter is REDRAWN per attempt — a wrong build with a fixed per-call offset
   must fail a test (pin the sleep sequence's non-constancy via a patched
   `asyncio.sleep` recorder, then mutation-prove it); (b) deadline honoured (elapsed,
   not attempt-count, terminates); (c) a non-retryable rejection is NEVER retried
   (query-count pin); (d) the 2-way fast path issues exactly one engine call when
   unconflicted; (e) exhaustion raises the NEW typed class — a contract pinning only
   `SurrealStoreError` + substring would let the class silently vanish. Fixture law:
   contention degree ≥8, at least one 16- or 32-way case (monoculture fixtures are the
   house's thrice-burned blind spot).
5. **`_REPORT_MINT_*` constants and the `_apply_mint` docstring** (the 12×5=60
   narrative) must be deleted WITH the loop — orphaned constants describing a retired
   mechanism are exactly the natural-language-surface class the last audit caught ten
   of.
