# 03a — Comms: the LEDGER (`messages.py` — send/drain/ack) · split from 03
size ~0.35 wu (measured post-adversary) · wave C · depends: **packet 03** (the store)
law: read `comms-subsystem.md` FIRST + DESIGN-LAW §8/§5/§1 · design source:
~/.claude/plans/one-of-claude-codes-nifty-garden.md · **DEPLOY: NO — test-only**

## Why this packet exists
Second cut of the packet-03 split (see `03-comms-message-graph.md` §SPLIT — TWICE). The store
landed in 03 because it changes behaviour for tables already holding production data; this packet
is the new module that stands on it, and it deploys nothing. **180 of the contract's 400 pins.**

## Mission
`messages.py` — the durable store-and-forward ledger, proven at contention BEFORE any served
surface depends on it. The mint, the atomic fan-out, the recipient guard and the write-once CAS all
land where their failure is a test failure rather than a production one.

## Scope IN
- **`MessageLedger`** on the `tasks.py` blueprint (own connection, `ensure_ready()`, `_row_to_*`
  decoders, pydantic `extra="forbid"` models, typed errors):
  - **`send`** — ONE transaction: `sequence::nextval` + `CREATE` + N×`RELATE` (measured to compose
    atomically, 320/320 at 16-way, zero conflicts — fan-out does NOT contend). `to=[]` ⇒ broadcast
    **all non-retired** agents (ruling 1). All-or-nothing: validate EVERY recipient before any
    RELATE. Dedupe recipients before the loop — `UNIQUE(in,out)` makes a duplicate a LOUD ERR.
    Unregistered recipient = teaching error routed through the existing
    `_comms_enrich_unknown_agent` (ruling 2), never a second copy.
  - **`drain`** — windowed SELECT over my unstamped `to`-edges + a scoped CAS stamp of EXACTLY the
    rows served (`peek` skips stamping; elided rows stay unread — no cursor arithmetic). Counts are
    computed over the WHOLE set their label describes, never the capped window.
  - **`ack`** — write-once CAS + a disambiguating follow-up SELECT returning a TYPED outcome. ⚠ The
    bare CAS return is **FOUR-WAY AMBIGUOUS** (already-stamped / no-such-edge / not-yours /
    never-ran-due-to-conflict): kill the fourth with the shared retry driver, disambiguate the rest,
    pin the three survivors SEPARATELY. Scope every stamp by ownership (`AND out = $me`) with a
    NEGATIVE pin — the rejection is invisible in the return value.
- **`set_status` on `send`** (operator-ruled): a sender parks itself in the same call — the
  one-call operator question.
- **The DERIVED waiting state** (ruling 9): an agent is awaiting-input **iff it has a question
  thread with no answer on it**, computed at read time exactly as `orphaned` is derived from
  `heartbeat_at`. NOTHING un-parks; the derivation WRITES NOTHING (pinned structurally). Mechanism
  is `message.question: bool` (E6, lead-ruled: folding it into `grade` would conflate must-ack with
  is-a-question, which are orthogonal — the same enum-conflation this ruling just removed).
  ⚠ Its KNOWN BOUND ships with it: an answer arriving OUT-OF-BAND never lands on the thread, so the
  state stays "waiting" until relayed — pinned, with its re-open trigger.
- **The shared `AgentRefLike` module** both `briefs.py` and `messages.py` import (operator-ruled;
  DRY law — duplication is a design decision, never a quiet copy #2).
- **Concurrency pins ≥8-way with SEPARATE ledger instances** (N coroutines on ONE socket do not
  contend like N connections) and OVERLAPPING racer lifetimes. Models: `test_findings.py:477-539`,
  `test_brief_ledger.py:285-317` — **NOT** `test_txn_contention.py`, which is a scripted fake with
  zero live races. The CAS stamp MUST ride the shared retry driver: **prove by MUTATION** — move
  the shared marker and every caller's pin goes RED. Routing without classifying is a private copy
  wearing the shared name.
- **The retry-guard driving body** (`test_retry_seam.py:2510-2534`): every SDK call site this
  module adds is enumerated automatically and goes RED as "unobserved" until DRIVEN there. It fails
  CLOSED. Non-obvious and mandatory.

## Scope OUT
- Everything in packet 03 (schema, the relation flip, `ENFORCED`, dirty-store pins).
- Tool dispatch, renders, promise proofs, hostile render fixtures, deploy, smoke → **03b**.
- `blocks`/fleet columns/`_comms_footer` (04); await/story/`since=` (05).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`.**
Packet 03 DONE and cold-audited (schema live, relation flip landed on a DIRTY store, `ENFORCED`
proven on the `to` edge); the contract's ledger pin group RED for the right reason at HEAD;
spike-surreal up; task f86af162 in play.
⚠ **THE LARGEST RESIDUAL RISK, carried forward deliberately** (adversary §7.8, contract author
concurring): the **`[real]`-tier ledger leg is UNGRADED** — neither could close it without building
the real store implementation. That is precisely what this packet builds, so treat every `[real]`
failure as a live finding, not a fixture problem.
**COVERAGE-PREMISE CHECK (INDEX law):** this packet's scope excludes render hygiene because 03b
owns it. Probe that at kickoff — one receipt — before honouring the exclusion.

## Exit
Scoped gates green with passed-COUNTs + `scripts/typecheck.sh` + ruff + **cold REFUTE audit** →
one-concern commits at natural boundaries → **NO DEPLOY** (03b ships the surface) → INDEX row +
Log + ledger rows. Concurrency pins green **20 consecutive runs** — no mechanical enforcement
exists, so it is builder discipline measured in runs, and a single green run NEVER clears a
concurrency test.
