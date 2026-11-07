# Q4 — Fable 5.1 answer (delivered as text; Write refused for subagents)

brief-base v25 read. Graded 5562925. lore MCP down → grep/Read. Its one prod-store read (re-measure "15 of 16 at 1.00") was DENIED by the auto-mode classifier → that number is inherited from the study, unmeasured. Hooks doc fetched 2026-11-07 (code.claude.com/docs/en/hooks, first 100k chars, per-event sections partly truncated → MEDIUM).

## SUMMARY
| item | recommendation | conf |
|---|---|---|
| U1 importance | STOP serving it (render + `lore_remember` param), stop reinforcing; serve created_at / expires_at / trust instead. Do NOT build decay-ranking now. If kind-aware ordering wanted later: a NAMED tiebreak after RRF, never a multiplier. | HIGH (stop) / MED (no decay) |
| U2 kind→category | Don't import identity/knowledge/context names; `kind` already IS the retention axis (ongoing = context; nothing else decays). If forced: decision → identity (×1) — but the name "identity" means "who the user is" in Agent Memory and would mislead. gotcha/uncertainty also must not fade (#107 = an unread gotcha). | HIGH / MED |
| U3 Stop-hook capture | No. Instead build the trigger's INSTRUMENT: a Stop/SessionEnd hook counting the session's lore_remember calls, nudging when zero (S). | HIGH / MED (mechanics) |
| D1 _reinforce + STEP | Drop; 10-site inventory. F5 ghost pin reds if `_REINFORCE_ENTRY` is left behind — good. | HIGH |
| D2 lens | Drop; tool never exposed it; job already done by governed.read_filter + keeps. Reopen → `scope=` via the same read_filter. | HIGH |
| D3 memory_category | Drop column (REMOVE FIELD migration per store ref), model field, read, fake, link5 containment-manifest door. | HIGH |
| D4 Spectron intent | Drop intent prose (bare `spectron` sweep, each hit dispositioned; incl. store/surreal.py + test_surreal_store.py "Spectron's runtime floor" version-floor rationale — misleading for next engine upgrade); KEEP MemoryBackend Protocol (fake is a real 2nd implementer). Supersede stale "SPECTRON STATUS UPDATE" memory. | HIGH |
| A1 cross-trust supersession | YES as a LOUD REFUSAL with named remedy (variant R), not the study's mint-uncertainty (M). Bundle: render trust + supersedes; `source_ref` param; chokepoint rule trust=authoritative REQUIRES source_ref (trust from how a note entered, not the writer's adjective). | HIGH (do it) / MED (R over M) |
| A2 auto-recall | SessionStart first; fail loud via exit-0 stdout (only channel Claude sees); never exit 2 on UserPromptSubmit (blocks all work when lore down). Cost M: hook has no MCP Subject (recall denies identity-less) + needs a "recent notes by kind" list read lore lacks. UserPromptSubmit keep_with_trigger: precision ≥ floor and tokens ≤ budget on ≥50 real prompts. Env opt-out. | MED |
| Extras | E1 include/as_of in backend but not on lore_recall → expose or delete; E2 source.ref unsettable; E3 render shows no trust/age/supersession (fix first); E4 write-time supersession candidates Phase B (changes lore_remember return → name contract change); E5 NOT: derived_from, traces-as-memory, HyDE, /profile, purge, LLM extraction, confidence floats; E6 law: reads have no side effects on served data. | HIGH (E1–E3 code facts) |

Decisions needed: U1 (a) vs (b) · A1 R vs M · A2 scope · E1/E2 surface exposure · whether the kind vocabulary moves off IMPORTANCE_DEFAULTS_BY_KIND in the same packet.

## Notable code facts it adds
- `_VALID_MEMORY_KINDS = frozenset(IMPORTANCE_DEFAULTS_BY_KIND)` → removing the importance table without re-homing the kind vocabulary breaks kind validation.
- Ledger never carries reinforced importance; `_replay_record` restores write-time value → rebuild_embeddings silently resets.
- `_row_score` = rrf_score only; importance affects no ranking.
- TestSupersession fixtures: kind="fact", default trust both sides → parameter monoculture, no cross-trust pin.
- At tool surface source = MemorySource(kind="operator", trust=caller's word); source.ref not settable.

## U1 Leg 1 / Leg 2
Leg 1: `importance: 1.00` = decision recalled twice OR fact recalled 10×; 0.50 = fresh fact OR once-hot note after rebuild → false clear every call. Leg 2: "importance was reset" vs "never bumped" serve identical bytes.
Option (a) problems: Agent Memory docs don't say how importance enters their ranker (copying an unknown); multiplier makes `score` unexplainable; no memory-ranking eval instrument exists (LOW, grep); under U2 nearly every kind is ×1 anyway.
Plan: Phase 1 (S) remove render fragment + remember param, D1, add created_at/trust to render. Phase 2 (S + migration) drop importance column (REMOVE FIELD), delete IMPORTANCE_DEFAULTS_BY_KIND, re-home kinds as Literal/frozenset, delete TestImportance* pins; replay must tolerate+ignore old ledger `importance` metadata (pin it).

## D1 inventory (10)
1 bump dropped deliberately · 2 constant + docstrings (backend module, MemoryBackend.recall Returns, local module/recall "PRE-bump", rebuild-lock comment) · 3 delete test_memory_reinforce_63a_iv.py · 4 TestReinforcementOnRecall + REQUIRED_REINFORCEMENT_STEP · 5 fake `_reinforce` · 6 `_REINFORCE_ENTRY`/`_effect_reinforce` + tests in test_memory_enforcement_63b_ia.py · 7 _governed_contract.py prose (reword) · 8 write_guard("_reinforce") frame · 9 63-rulings §10.9-C "ACCEPTS _reinforce as-is" → superseding ruling line · 10 test_comms_schema.py comment. Shrinks the deny-by-default raw-UPDATE allowlist by one.

## A1 variants
M (study): new row live, old stays live, mint system `uncertainty` with derived_from — costs a system-minted row, a new field, and a response reporting success for a write that didn't do what was asked. R (Fable): refuse with teaching error naming the old note's trust/ref and two remedies (pass authoritative + source_ref, or save as kind=uncertainty naming old). Fixtures: both trusts both sides; R fires only on authoritative←experiential. "authoritative requires ref" touches existing callers → stop-and-ask, operator rules. Threat model: honest agent, not hostile writer.

## A2 hooks mechanics (from doc, MED)
Both events: exit-0 stdout → Claude's context (also additionalContext). UserPromptSubmit exit 2 blocks prompt; timeout 30s. SessionStart exit 2 doesn't block; stderr to user only; timeout 600s. Claude never sees stderr on exit 0. Injected block must carry scope-bound line + k, fence note text (#195), name the query answered.
