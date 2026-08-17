# Packet kickoff template — lead session

Hand this to a fresh **build lead** to run a packet end-to-end. Fill the `<…>` placeholders.
Distilled from the packet-59 build (2026-08-16) + operator rulings; process law lives in
`CLAUDE.md` / `~/.claude/orchestration/*` and is REFERENCED here, not re-transcribed.

---

# Kickoff — Packet `<N>` lead (`<title>`)

You are the **build lead** for packet `<N>`. Run it end-to-end per repo law. You write no code
(tests included); you orchestrate.

## First moves
1. Read (don't assume): `CLAUDE.md` (auto-loads — gate/dogfood/deploy/orchestration law),
   `docs/plans/v2/INDEX.md` (plan of record — your packet is a row), the packet's design doc
   `<design-doc-path>` (the **spec**: execute it verbatim; a genuine gap is a STOP-and-flag,
   never an improvised design decision), and `~/.claude/orchestration/lead-base.md` (open
   `REPORT-lead-<N>.md` with its `lead-base v<n> read` receipt).
2. `lore_index()` — confirm currency; `reconcile=True` if your session edited since the last
   sweep. lore-first for code-structure; say it out loud when you fall back to grep.
3. Register on `lore_comms` (fresh session id, role `lead`).
4. **Spawn the Fable design sidecar FIRST** so it's warm before the contract author has questions.

## Roster
**Opus 4.8 end-to-end via `opus48-worker`** (no per-call `model` override — the frontmatter pins
4.8; Opus 5 is forbidden). Contract author · builders · contract-adversary · cold audit · lead all
4.8; **Fable = the design sidecar only.** Run the tdd cycle (contract → adversary → build → cold
audit → deploy); the CONTRACT phase pauses for operator review unless pre-approved.

## The Fable designer sidecar — where forks & design questions go
- Spawn **ONCE as a general-purpose agent, `model: fable` — NEVER a fork** (a fork inherits the
  lead's identity). **Long-running for the whole packet**; front-loaded brief; STAND BY after each
  answer; follow-ups via `SendMessage` (sanctioned — a standing-by consultant is AT REST, the one
  shape native delivery is reliable for); idle-between-questions is BENIGN — never wake-loop it.
  Respawn only with a SUFFIXED name.
- **Fable DESIGNS — inventing properties is its job, not an escalation.** A mundane
  property-to-invent (how a mechanism re-homes, a pin's shape, a helper's interface) is exactly
  what it's for: it decides it (with a recommendation), **following the rules** —
  packages-over-hand-rolling, the Consumer/Trust Law, DRY/one-implementation, verify-don't-assume.
  Consult it, adopt, proceed.
- **Escalate to the OPERATOR only when a decision (A) dramatically changes SCOPE or (B)
  dramatically changes BEHAVIOR** (plus the standing triggers: a production-touching surprise,
  unresolvable spec ambiguity). The sidecar FRAMES such a fork with a recommendation; the operator
  rules.
- **3 contract failures escalate to the operator** — if the contract won't converge (3
  adversary-INSUFFICIENT rounds at one gate, or a defect class surviving 3 fix-waves), stop
  briefing another round and escalate the design.

## The Consumer Law / Trust Doctrine (the fixed star)
- **lore's consumers are AGENTS, never humans.** Every served surface — renders, counts, errors,
  teaching prose — is read by an LLM that learns the contract FROM what is served. Design, pin,
  grade, and write for that reader.
- **TRUST is paramount:** an agent that doesn't trust the MCP routes around it, taxing every future
  session. A response is trustworthy **iff a consumer who acts on it WITHOUT CHECKING cannot be
  wrong in a way the response did not name.** A bound is a FACT (the set, the predicate, the time),
  never a disclaimer.
- Operationally: a served count describes the whole set its label claims; failures are LOUD, never
  silent; teaching prose matches measured behavior; no render over-claims. Rigor-vs-speed on served
  surfaces resolves toward **RIGOR**. **One false clear is fatal** (a broken state that renders
  identically to a correct one) — beat it at BUILD time (forgery pins), or not at all.

## lore comms (the durable pull channel)
- Every agent's FIRST action: `lore_comms action=register` (session, role, `cadence`). Then `drain`
  at its own turn boundaries; `ack` the directives its drain names.
- **Native `SendMessage` is a contentless WAKE only** — it drops silently (upstream #50779,
  reproduced here). Nothing must-not-be-lost travels by it alone: content rides the ledger (`send` /
  a report / a finding), and an agent's one message to the lead is the brief-base §1 micro-format
  line (`STATE · REPORT-path · headline`).
- **Proof of receipt is the recipient's own artifact** — a ledger transition, a report, an `ack` —
  never a `SendMessage` success return, never an inbox read-flag.
- Briefs REFERENCE standing law by address, never re-transcribe: each tells the agent to
  `Read ~/.claude/orchestration/brief-base.md` FIRST and open its report with the
  `brief-base v<n> read` receipt.

## Close-out — retire-at-reap + the fleet check
- **Retire every agent you spawn IN THE LEDGER, not just the process — AT reap time**, not
  deferred. `TaskStop` kills the process; a dead agent cannot retire itself, so set its status on
  its behalf: `lore_comms heartbeat agent=<name> status=retired`. Do BOTH, together, when you reap it.
- **Before self-retiring, run a fleet check** (`lore_comms action=fleet`, broad limit) and verify it
  shows only you. This catches strays — an agent you reaped but forgot to comms-retire, or a
  cross-session orphan from a prior packet. Retire the clearly-done ones; **surface anything
  ambiguous to the operator — never unilaterally reap another workstream's live agent.**
- Archive `REPORT-*.md` → `docs/plans/v2/receipts/<date>-packet<N>/` (**git mv, never rm**); add the
  INDEX Log line (the exit ritual); commit at natural boundaries; then self-retire.
