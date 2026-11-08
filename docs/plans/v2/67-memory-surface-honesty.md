# Packet 67 — memory-surface honesty (the Q4 Agent-Memory review, adopted)

**Minted 2026-11-07 by operator ruling:** *"look up the agents recommendations regarding question 4 including the
Fable addon and slot them in after the next incomplete packet group lands."* then *"Move the Q4 resolution before
65-cut."* **67a → 67b → 67c land after 64 and 65-pre and BEFORE 65-cut** (so the cutover ships them); 67d after 65-cut. Lead: Opus. Size: ≥0.30 in total, so it is
**PRE-SPLIT** into 67a–67d (sizing law); each sub-packet has its own entry and exit.

**Source (cited, never re-transcribed):** `receipts/2026-11-07-q4-memory-review/` — three independent answers
(Sonnet, Opus 5.5, Fable 5.1, each run under the Consumer Law without seeing the others) plus `COMPILED.md`, the
per-item comparison table and the lead synthesis. The question was what lore's memory should take from, or drop in
favour of, Anthropic's Agent Memory design.

**FIRST READS:** repo CLAUDE.md (Consumer Law + Trust Doctrine) · `docs/reference/surrealdb-31-capabilities.md`
(67a drops a column; 67b backfills the ledger) · `COMPILED.md` above · the 63 governed-contract substrate
(`loremaster/tests/_governed_contract.py`), because D1 shrinks the governed raw-write allowlist.

**ENTRY CHECK (all sub-packets):** 64 and 65-pre are closed in the Status table and the SDK-3 packet (66) has landed. Every
code fact below was grep-derived by the reviewers while lore MCP was down, so re-derive each with `lore_impact`
(after `lore_index(reconcile=True)`) before deleting anything. The Opus ledger counts came from a scratch COPY of
the production memory ledger taken 2026-11-07; **re-measure them at kickoff** — they are inherited numbers.

## 67a — deletions + read-side honesty (UNANIMOUS across all three reviewers) · ~0.15
IN:
- **D1** — delete `_reinforce` and `REINFORCEMENT_STEP`. **This is also a live defect:** `lore_recall` is registered
  `readOnlyHint`/`idempotentHint` but writes on every call, and the bump is not in the ledger, so a rebuild
  silently resets it. The removed-behaviour inventory is Fable's 10 sites + Sonnet's list (receipts). The
  replacement pin: **recall issues no mutating statement — rows are byte-identical after N recalls, and two
  recalls serve identical bytes** (`remember` is the positive control). Re-run the governed-write enforcement
  positive controls so an unlabelled raw memory write still fails once `_REINFORCE_ENTRY` is gone.
- **U1 (stop serving importance)** — remove `importance:` from the recall render. Today it serves `1.00` for both
  "decision recalled twice" and "fact recalled 10×", a Leg-2 false clear on every call.
- **D2** — delete `lens` from the protocol, the implementation, the fake and the pin. The tool never exposed it.
- **D3** — drop `memory_category`. Opus measured it on 0 of 291 ledger rows. The DDL change goes per the store
  reference (REMOVE FIELD); the dirty-store verify is the rider.
- **D4** — drop the Spectron-intent prose and keep the `MemoryBackend` Protocol, whose fake is a real second
  implementer. Sweep bare `spectron` and give each hit a verdict, including `store/surreal.py` and
  `test_surreal_store.py`'s "Spectron's runtime floor" rationale. Supersede the stale "SPECTRON STATUS UPDATE"
  lore memory.
- **Fable's add-on (the U3 trigger instrument)** — a Stop/SessionEnd hook that counts the session's
  `lore_remember` calls and nudges when the count is zero. It is the instrument that would justify reopening U3
  (automatic capture), which all three reviewers rejected for now. Hook mechanics are in Fable's answer. Pipe-test
  every branch before registering.
- Re-home the kind vocabulary: `_VALID_MEMORY_KINDS = frozenset(IMPORTANCE_DEFAULTS_BY_KIND)` breaks kind
  validation if the importance table goes.
OUT / ruled at 67a kickoff: **the U1 sub-fork** — keep writer-set importance (16 of 281 notes override the kind
default) as a stored, unrendered field, or drop the `lore_remember` parameter and the column too (Fable Phase 2).

## 67b — render honesty (UNANIMOUS) · ~0.20
IN:
- Render **trust, created date, supersedes / superseded_by** in the recall output. `RecalledMemory` already
  carries them. Route them through the shared sanitiser seam, with a hostile fixture.
- Expose `include="superseded"` and `as_of` on the `lore_recall` tool (the backend implements both), or render a
  counted bound that says they are unreachable.
- **X3** — `score:` is an RRF rank-fusion score that reads as similarity. Relabel it, or serve the cosine.
- **X4 (precondition for any age render)** — 0 of 291 ledger rows carry `created_at`, so `_replay_record` stamps
  `now()` on every rebuild and resets every note's age. Backfill it, and pin that a rebuild preserves age (Leg 2).
- **X5** — 26 legacy supersede predecessors lack `valid_until` in the ledger. Their closure after a rebuild
  depends on an un-ORDERed `MemoryLedger.all()`. A one-time retire removes that dependence.

## 67c — cross-trust supersession (A1) · ~0.15 · after 67b
All three agree that today's silent supersede of an authoritative note by an experiential one must become
**NAMED in the `lore_remember` response**, with fixtures using both trusts on both sides. **OPERATOR FORK at
kickoff — the reviewers split three ways:**
- mint an `uncertainty` note (Sonnet: the Agent-Memory form);
- refuse loudly with a teaching remedy, plus `trust=authoritative` requires a `source_ref` (Fable);
- allow it and name the crossing in the response and the render (Opus: 0 of 26 real supersedes crossed trust;
  #107 shows experiential can be right; a refusal pushes writers to over-claim `authoritative`).

## 67d — auto-recall hooks (A2) · M · GATED, after 65-cut
Not before: (1) a hook identity — hooks have no registered Subject, and governed recall refuses identity-less
callers, so it needs 65's identity provisioning plus an identity design; (2) a relevance floor on memory recall,
which today serves RRF with none and so would inject k notes on every prompt. SessionStart comes first.
Failures must be loud via exit-0 stdout; never exit 2 on UserPromptSubmit, because that blocks all work while lore
is down. Keep-with-trigger for UserPromptSubmit: precision ≥ a floor and tokens ≤ a budget over ≥50 real prompts.

## Explicitly NOT adopted (unanimous)
- No stored category, and no identity/knowledge/context names: `kind` is already the retention axis.
- No decay-ranking now. Reopen only on a measured trigger: U3 lands, or a recall eval shows stale notes displacing
  relevant ones. **This re-scopes packet 32's decay half to that trigger.**
- No automatic Stop-hook capture (U3).
- Also not adopted: derived_from, traces-as-memory, HyDE, LLM extraction, confidence floats.
- Write-time duplicate/supersession candidates (study #6) wait until after X3; they belong to 33.

## Operator rulings, 2026-11-08 (on design-sidecar RULING-10: `receipts/2026-11-08-sdk3-sidecar/RULING-10.md`)
Measured read-only on the local ledger (294 rows): 17 importance overrides, all experiential; 26 supersedes, 0 crossing trust; `created_at` on 0/294. These counts supersede the 16/281/291 above.
- **67a U1 → (b):** drop the `lore_remember` `importance` parameter, the stored column, `IMPORTANCE_DEFAULTS_BY_KIND`/`REINFORCEMENT_STEP` and their pins, using the removed-behaviour inventory. Kinds re-home on a `MemoryKind` `Literal` in `memory/backend.py`, and the served prose is derived from it. **Pin it like this:** a legacy ledger row carrying `importance` replays and recalls byte-identically to one without; the recall render carries no `importance` token.
- **Transition: PLAIN REMOVAL, no refusing shim** (operator: *"This is a non issue. It's not in production. You're the only agent using lore right now."*).
- **67c A1, the combined form minus refusal** (operator: *"Can we combine them all (minus refusal, which will cause an agent to work around)?"*):
  - A cross-trust supersede is ALLOWED, and the `lore_remember` response NAMES it.
  - Both directions are named. Only the downgrade (authoritative ← experiential) teaches the alternative: `kind=uncertainty` naming the old note, both live.
  - The render derives the crossing at read time from the stored chain; a missing predecessor renders as a "not found" bound.
  - Fixture matrix as in RULING-10 §2.
- **Response shape APPROVED:** the first line is the id, and later lines are named guidance. The "id ALONE" pin is rewritten.
- **`source_ref` lands in 67b**, with its render: optional, rendered `authoritative (source: …)` vs `(unsourced)`, and drift-marked by the existing refs oracle.
- **Not adopted:** a system-minted uncertainty note; "authoritative requires source_ref"; any refusal of a cross-trust supersede.
