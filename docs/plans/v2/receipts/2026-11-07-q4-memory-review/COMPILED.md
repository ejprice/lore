## QUESTION 4 — THREE-MODEL REVIEW, COMPILED (2026-11-07; for operator review when we tackle Q4)
Full answers: q4-{sonnet,opus,fable}.md (this directory) (harness refused subagent report-file writes; lead persisted them).
All three: lore MCP down → grep/Read; vendor docs unread except Fable's hooks-doc fetch. Opus MEASURED a scratch copy of the
production memory ledger (~/.local/state/lore/lore.memory.db → scratchpad/ledger/); Fable's prod-store read was denied by the classifier.

| item | Sonnet | Opus | Fable | verdict |
|---|---|---|---|---|
| U1 importance | stop rendering; drop reinforce; serve age; no decay (MED) | stop serving (or render only the 16 writer-set overrides); no decay until trigger (MED-HIGH) | stop serving + drop `lore_remember` param; Phase 2 drop column (HIGH stop / MED no-decay) | **UNANIMOUS: stop serving, no decay now, serve age/trust instead.** Sub-fork: keep writer-set importance vs drop param+column |
| U2 kind→category | no stored category; decision=identity if ever | decision is 2 measured populations (doctrine vs packet rulings); identity only if decay; derive at read | don't import the names; `kind` already is the retention axis; decision→identity if forced | **UNANIMOUS: nothing to build; decision=identity only if decay ever adopted** |
| U3 Stop-hook capture | not now (HIGH) | not now (HIGH) | not now; build the trigger's instrument instead (Stop hook counting lore_remember calls, S) | **UNANIMOUS no**; Fable's instrument idea is the one addition |
| D1 _reinforce | DROP (HIGH) | DROP (HIGH) | DROP (HIGH) | **UNANIMOUS. Also a LIVE DEFECT: lore_recall declares readOnlyHint/idempotentHint but writes every call; bump not in ledger → rebuild resets it.** Replacement pin: recall issues no mutating statement / rows byte-identical |
| D2 lens | DROP | DROP | DROP | **UNANIMOUS** (tool never exposed it) |
| D3 memory_category | DROP (+migration, dirty-store verify) | DROP (0/291 rows); fallback leave dead DEFINE | DROP (REMOVE FIELD) | **UNANIMOUS**; DDL via store ref |
| D4 Spectron intent | drop prose, keep Protocol | same | same + store/surreal.py "Spectron runtime floor" rationale is misleading | **UNANIMOUS**; + supersede stale "SPECTRON STATUS UPDATE" lore memory |
| A1 cross-trust supersede | ADOPT, MINT uncertainty (AM form) | DON'T adopt; allow + NAME the crossing in response + render provenance (0/26 real supersedes crossed trust; #107 shows experiential can be right; refusal incentivises over-claiming) | ADOPT as LOUD REFUSAL + teaching remedy; trust=authoritative requires source_ref | **SPLIT 3 WAYS — operator fork.** All agree: today's silent cross-trust supersede must become NAMED in the response, and fixtures need both trusts on both sides |
| A2 auto-recall hooks | adapt; SessionStart standing set first; M + identity ruling | later/gated; blockers: no relevance floor in memory recall, no hook identity; SessionStart overlaps brief_get | SessionStart first; exit-0 stdout is the only loud channel; never exit 2 on UserPromptSubmit; M | **UNANIMOUS: not S, needs identity design; fail loud.** Opus adds the no-floor blocker |
| Render provenance (trust/age/supersedes) | E1 HIGH | X1 HIGH | E3 HIGH | **UNANIMOUS ADD — prerequisite for A1/U1** |
| Expose include/as_of on lore_recall | E2 | X2 | E1 | **UNANIMOUS** (backend has it, tool doesn't) |
| `score:` is RRF, reads as similarity | — | X3 HIGH | — | Opus only; prereq for A2 + write-time dup flag |
| Ledger lacks created_at (0/291) → rebuild resets age | — | X4 measured | — | Opus only; precondition for any age render/decay |
| 26 legacy predecessors' closure depends on un-ORDERed MemoryLedger.all() | — | X5 LOW-MED | — | Opus only; one-time retire fixes |
| kind vocabulary derived from IMPORTANCE_DEFAULTS_BY_KIND | — | — | noted | dropping the table must re-home `_VALID_MEMORY_KINDS` |
| Write-time dup/supersession candidates (study #6) | later | after X3 | Phase B | agree, later |

Lead synthesis (for discussion, not a ruling):
- Packet A (deletions, unanimous): D1+D2+D3+D4, importance stops being served (U1), replacement pin "recall is side-effect-free".
  D1 also fixes a live false annotation on lore_recall.
- Packet B (render honesty): provenance/age/supersedes in the recall render + include/as_of on the tool + `score:` relabel/cosine,
  with X4 (ledger created_at backfill) as its precondition and X5 one-time retire.
- Then A1 under the operator's chosen form; A2 after an identity design + relevance floor.
- Operator decisions: (1) U1 sub-fork — keep writer-set importance or drop param+column; (2) A1 — mint (Sonnet) / refuse (Fable) / allow-and-name (Opus);
  (3) A2 — whether/when; (4) Fable's lore_remember-count Stop hook as U3's trigger instrument — yes/no.
- Housekeeping: Opus left a COPY of the production memory ledger in scratchpad/ledger/ — delete with scratch cleanup.

