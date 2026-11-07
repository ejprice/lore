# Q4 — Opus 5.5 answer (delivered as text; Write refused for subagents)

brief-base v25 read. 5562925. lore MCP down → Read/grep/sed. Did NOT query :18500. DID measure a scratch COPY of the production memory ledger ~/.local/state/lore/lore.memory.db (+WAL/SHM, WAL last written 2026-10-31) → copy at scratchpad/ledger/.

## SUMMARY
| item | recommendation | conf |
|---|---|---|
| U1 | Stop serving importance; don't rank by it now. Delete reinforcement. Remove `importance:` from render, or render only when writer set it explicitly (16/281 overrides). Decay waits for a trigger (U3 lands, or a recall eval shows stale displacing relevant); X4 is a precondition; response must name its ordering rule. | MED-HIGH |
| U2 | kinds fact/decision/gotcha/uncertainty/ongoing. ongoing≡context. fact/gotcha/uncertainty→knowledge. decision = TWO measured populations (standing operator doctrine vs packet-scoped rulings); → identity only if decay adopted, derived at read time. | MED (map) / HIGH (mixed pop measured) |
| U3 | Not now — capture creates the volume decay exists for → reopens U1. | HIGH |
| D1 | DROP — live defect: lore_recall declares readOnlyHint+idempotentHint but writes every call; bump not in ledger → rebuild resets it. Replacement pin: recall leaves every row byte-identical, two recalls serve identical importance. | HIGH |
| D2 | DROP lens. | HIGH |
| D3 | DROP memory_category (0/291 ledger rows). DDL change → store ref first; fallback: leave dead DEFINE, drop model field + read. | HIGH |
| D4 | DROP prose, keep Protocol; supersede stale SPECTRON STATUS UPDATE memory. | HIGH |
| A1 | DON'T adopt as specified: Agent Memory's rule governs automatic reconciliation, lore's supersede is explicit; trust is caller-asserted → refusal incentivises over-claiming authoritative; #107: authoritative vendor doc was false, experiential probe right; base rate 0/26 cross-trust supersedes. INSTEAD: let it proceed, NAME the crossing in the lore_remember response ("superseded authoritative note <id> with an experiential note"), render `supersedes <id> (authoritative)` + chain readable. If operator prefers AM form, response must say "NOT superseded — both live, uncertainty <id> minted". Fixtures both trusts both sides. | MED |
| A2 | Later, gated. Blockers: memory recall has NO relevance floor (serves RRF) → would inject k notes every prompt; hook has no governed identity. ~6–12k chars/prompt at k=5 (~1.5–3k tokens, ratio a guess). Unknown whether UserPromptSubmit fires for subagents. SessionStart overlaps brief_get. Fail loud; name bound. | MED |
| X1 | ADD trust, created date, supersedes to recall render (route through render_attributed/sanitiser). | HIGH |
| X2 | ADD include="superseded"/as_of/chain read to lore_recall tool. | HIGH |
| X3 | CHANGE `score:` — it's an RRF rank-fusion score, reads as similarity; serve cosine or relabel "rank score". Prereq for A2 and study #6. | HIGH |
| X4 | Backfill ledger created_at: 0/291 rows carry it → `_replay_record` stamps now() on rebuild → every rebuild resets every note's age (Leg-2 false clear for any age feature). Whether the live store still holds true values: unmeasured. | HIGH measured / MED impact |
| X5 | 26 legacy supersede predecessors lack valid_until in the ledger; closure after rebuild depends on un-ORDERed SELECT in MemoryLedger.all() returning predecessor before successor. One-time retire of the 26 removes the dependence. | LOW-MED |
| X6 | Agree study #6 (write-time dup candidates) + #17 (chain read), after X3. | MED |

## Measured (ledger copy)
291 notes: decision 130 (45%), gotcha 78, fact 76, ongoing 2, uncertainty 0, no-kind 5. Trust: experiential 266, authoritative 15, none 10. source.kind = operator on 281/281 (hard-coded → carries no information). Importance: 265/281 = kind default; 16 explicit. Supersedes: 26, all distinct predecessors; exp→exp 25, auth→auth 1, cross-trust 0; decision→decision 11. 0/291 carry created_at / memory_category / valid_until. Note size median 1,183 chars, p90 2,421, max 18,715.

## U1 key argument
Without reinforcement, importance ≈ kind (265/281), which the same line already shows. Decay-ranking now: silent omission outside k=5 (a standing doctrine as `decision` sinks to ~0.16× after a year); unevidenced kind bias (decisions 45% would outrank gotcha landmines); age input not durable (X4); lore lacks the problem (291 hand-authored notes in ~4 months).

## D1 inventory
+0.05 bump dropped · writes during recall dropped (makes annotation true) · F5 allowlist row + `_effect_reinforce` dropped — re-run enforcement positive controls so an unlabelled raw memory write still fails · "bump set ≡ served set" becomes vacuous → stronger pin above · bare-`reinforc` docstring sweep. Pins: test_memory_reinforce_63a_iv.py (whole), TestReinforcementOnRecall + REINFORCEMENT_STEP anchor, allowlist entry/_effect_reinforce tests/importance=0.1 fixtures in test_memory_enforcement_63b_ia.py, _governed_contract.py prose, fake _reinforce. Cost S.

## Note
Study is stale on the engine version (says 3.2.4); no verdict changes.

Instrument (verbatim python over sqlite `memories` table) is in the agent's hand-back; reproduced in session transcript.
