# KICKOFF — finding #102: the hot-row mint retry substrate

Paste everything below the line into a fresh Claude Code session (Opus 4.8 lead).

---

Execute finding #102 — the hot-row mint retry substrate. This is a PREREQUISITE for PKT-28 C2
(the message graph), and it is a LIVE defect today.

**FIRST TECHNICAL ACTION, before any design or contract work: settle the native-sequence probe
(mission item 1). It determines whether this is a "fix the retry substrate" job or a "delete the
hand-rolled counter" job. Do not design around an unverified mechanism.**

## WORKTREE — do this first, so you cannot collide with the session finishing PKT-28 C1
```
git -C /home/ejprice/PycharmProjects/lore worktree add \
    /home/ejprice/PycharmProjects/lore-102 feat/surreal-unification
cd /home/ejprice/PycharmProjects/lore-102
```
Base on current HEAD of `feat/surreal-unification` (it MUST include `93a9aab`, the `_txn`
root-cause fix, and `f36120b`, the C1 comms work). Work only in the worktree. When done, ask the
operator what to do with it — **never abandon a worktree.**

## READ FIRST
- `lore_findings get 102` (supersedes #33) — the defect, with receipts.
- `lore_findings get 104` — the render-architecture root cause (C2's OTHER step-0; not yours, but
  read it so you don't duplicate).
- `/home/ejprice/PycharmProjects/lore/CLAUDE.md` — process law. Read ALL of it, especially the new
  sections **"A DIAGNOSIS IS NOT AN INSTRUMENT"** and **"Every artifact gets an adversary"**.
- `docs/plans/v2/PKT-28-agent-comms.md` (the C2 row) and
  `~/.claude/plans/one-of-claude-codes-nifty-garden.md` §Data model (the `message` node's `seq`
  field) — your work decides how C2 mints it.

## ⚠ ROOT CAUSE ALREADY FOUND (2026-07-13, finding #122 — read it FIRST)
**`_txn.py:549` — the shared conflict-retry backoff has ZERO JITTER.** It is deterministic and
**identical across every racer**, so N colliding writers all sleep the same duration and
**re-collide in lockstep** until the budget drains — **while its own comment claims it prevents
exactly that.** This is the un-named substrate under #102, and it is the SAME defect we fixed one
layer up in `BriefLedger.publish` (commit `cfb36d2`): jitter that de-synchronises nothing.

So this is a **known-cause fix, not an investigation**: (1) add PER-RACER jitter (full or
decorrelated — never a shared constant, never derived from the contended row's identity);
(2) derive the retry BUDGET from the racer count, not a 2-way-tuned constant; (3) correct the
false comment; (4) pin at >=8-way. `lore_findings get 122`.

## THE DEFECT (reproduced — and the codebase already knew)
`findings.py:244` says, in a source comment: *"`finding_counter` row, so N-way contention
(**measured 43% txn-exhaustion at N=8**"*. Someone measured it, wrote it down, and shipped.

- `test_findings.py::TestConcurrentNumbering::test_concurrent_reports_get_distinct_consecutive_numbers[real]`
  fails **~4 of 5 SOLO runs** when the machine is under load; it also failed a full serial suite run.
- Root cause per #33/#102: `_txn`'s conflict-retry budget was tuned for **2-way** task-claim races
  and **DRAINS under N-way contention** on a hot counter row.
- Every agent filing a finding during a busy multi-agent session is rolling dice at ~43%
  exhaustion. **This is not theoretical.**

## WHY IT BLOCKS C2
`message.seq` is the **same shape** as `finding.number` — a single global counter row — but with far
higher traffic (every message from every agent, vs every finding). C2's whole purpose is *many
agents messaging concurrently*, so the hot-row mint sits directly on its load-bearing path. If C2
builds `send` on this substrate, **`send` fails under exactly the fleet concurrency the subsystem
exists to support.**

## YOUR MISSION, IN ORDER
1. **SETTLE THE NATIVE-SEQUENCE PROBE FIRST.** The plan says mint `message.seq` via SurrealDB's
   native `sequence::next()` / `sequence::nextval()` — but a scout found that mechanism appears
   **NOWHERE** in this codebase and the real function name is unverified. Probe it live against
   surrealdb 3.1.5 (spike-surreal). **If a native sequence works, the hot-row problem may be
   DELETABLE rather than fixable** — that is the packages-over-hand-rolling answer, and it changes
   what the fix even is. Settle it before designing anything.
2. **FIX THE SUBSTRATE** (if the native path is unavailable — or regardless, since the existing
   counter-row mints must survive: `finding.number` AND `brief.version` both use it):
   - Derive the retry budget from the **ACTUAL racer count**, never a 2-way-tuned constant.
   - **Jitter must be unique PER RACER — never derived from the contended row's identity.**
     (The exact C1 lesson: `BriefLedger.publish` seeded its jitter from `uuid5(name, version)` —
     identical across racers — so every loser slept the same duration and re-collided in lockstep
     forever. It failed 4 of 5 runs. See commit `cfb36d2` and the 2026-07-12 INDEX log entry.)
   - **Pin it at >=8-way contention. A 2-way test proves nothing.**
3. **RECOMMEND THE MECHANISM FOR C2's `message.seq`** — native sequence, fixed counter-row,
   per-session counter, or a ULID-derived handle. (`message.id` is **already a ULID**: time-ordered
   and contention-free; and the plan already accepts gaps — *"an aborted send burns a number,
   benign"* — so a strictly-monotonic global counter may never have been required.) Say which, and
   why.

## PROCESS — repo CLAUDE.md governs. The parts that will bite you:
- **The lead writes NO code (tests included).** Fresh-named briefed agents per seam; the contract
  author is NEVER the implementer.
- **CONTRACT AUTHORS ARE OPUS** (operator ruling 2026-07-12 — Sonnet contracts twice shipped
  fixtures that could not discriminate a correct build from a wrong one).
- **A cold CONTRACT ADVERSARY grades the tests BEFORE the builder starts.** Invoke the reusable
  agent: `subagent_type: contract-adversary` (`~/.claude/agents/contract-adversary.md`). Its killer
  question: *"if a builder satisfied this contract perfectly but fixed NOTHING, would it still
  pass?"* It has caught a blocker on **all four** of its runs, including against an Opus-authored
  contract. **For a concurrency fix this is not optional** — it is exactly where green-but-broken
  ships.
- **A failing test is a STOP. "Flaky" is NOT a verdict you may render.** The worst defect of the
  last phase shipped because a builder called a 4-of-5 failure flaky. If a test fails, you
  escalate. **Corollary: a single green run NEVER clears a concurrency fix — require 20
  consecutive.** (A lone green run gave the C1 LEAD a false all-clear on this exact class.)
- **Every load-bearing pin is MUTATION-PROVEN**: break the code, watch it go RED, restore.
- **Fixtures must DISCRIMINATE** — ask of each: *"what WRONG build would this still pass?"* Small-N
  and single-value fixtures are how this class keeps shipping.
- **Spec ambiguity is an ESCALATION**, never a silent choice.
- **Cold Opus REFUTE audit before the commit** (builder != grader).

## ROSTER
Opus 4.8 lead (you) · Opus contract authors · `contract-adversary` (Opus) between contract and
builder · Sonnet 5 builders · Opus cold audits · **ONE persistent Fable design consultant** spawned
at kickoff and kept alive all session for design forks (SendMessage it only when it is AT REST;
proof of receipt is its **written artifact**, never the send's success return; it must write rulings
to disk EARLY, before long synthesis).

## WRITABLE SET
`loremaster/loremaster/store/_txn.py`, `loremaster/loremaster/findings.py`, and their tests
(`test_surreal_store.py`, `test_findings.py`). Plus a design doc under `docs/design/` if the
consultant rules.

**DO NOT TOUCH:** `server.py`, `briefs.py`, `agents.py`, `surreal_schema.py` (the C1 comms surface —
another session owns it), `CLAUDE.md`, `docs/plans/v2/INDEX.md`.

## TESTING
- **`pytest-xdist` is installed — use `-n auto` on every run** (measured 846s -> 88s, identical pass
  counts). A green claim **STILL requires a passed-COUNT in the tail**; a piped pytest with a bad
  path exits "no tests ran" and looks green.
- Live store = **ws://127.0.0.1:18000 (spike-surreal), throwaway DBs. NEVER :18500 — PRODUCTION.**
- ⚠ **YOU SHARE spike-surreal WITH OTHER SESSIONS.** That contention is *how this bug reproduces*
  (good for you) but it means an unrelated flake can appear in your runs (bad for your gates). When
  you take a final gate number, **check the machine is quiet first.**
- Gates: `scripts/typecheck.sh` zero mypy errors **including tests** · `uv run ruff check .` clean ·
  scoped suites with passed-COUNTs · the **full suite at the checkpoint only** (NOT per wave).
- **Known-open, NOT yours:** three log-capture tests (#101) fail under parallel scheduling — a
  latent isolation leak xdist exposed. Do not chase them; do not let them block you.

## EXIT
Gates green + cold audit GO -> one-concern commits -> file a finding/task recording the C2
`message.seq` recommendation -> resolve #102 with receipts -> report to the operator, and **ASK what
to do with the worktree** (keep / merge / discard). No resume docs.
