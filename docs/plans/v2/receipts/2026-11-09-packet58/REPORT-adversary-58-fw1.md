brief-base v27 read · brief project v7 read

# REPORT-adversary-58-fw1 — packet 58 fix-wave contract, the ONE grade (am-17 §12.6)

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** · state: done · deviations: test runs inline, not via haiku-runner (routing table); logs live in my scratchpad (non-durable), every instrument is pasted in §INSTRUMENTS.
- **P1 headline:** 34 wrong builds. 31 die exactly as declared. **2 survive the whole contract** (W45 single-pass loop: 7/7 fix-wave green; W26 per-chunk check: 307/307 heal-set green). The **spec-faithful reference** also passes the contract and **violates P** (#631).
- **#631 (filed, correctness, security-relevant):** the shared cycle predicate's step-over drops ONE edge of a legacy loop; when that edge is shared with the minted row's cycle, the cycle is missed. Store repro at pristine 25cfd16: a **live `supersede_task` writes S→L1→L2→R→S** (the control without the shared edge is refused). am-17 §12.3 orders the heal to keep this step-over, so P fails by spec. A sound SCC predicate (networkx, already a dependency) passes every probe and the 25-file set, except the R6 pin that requires `find_blocked_by_cycle` to be the detector (1 red): **design fork**.
- **Runs used: 46**, all targeted, never the full suite. 2 runs over the 25-file set (reference SAT; REF2 pricing), 2 over the 20-file heal set (survivor confirmation), 42 scoped to classes or files. Per-run list in §RUNS.
- **Reference (round 1):** my reference of am-17 §12.2/§12.3/§12.7/§12.8-1 + #625a/b + #130(a) scored **1585 passed / 1 skipped / 0 failed** (EXIT=0) over 25 files. The 9 declared reds go green. 30 parked 64b-i ids deselected.
- **RED reproduced (P7):** 9/9 declared reds at 25cfd16 code, 0 unexpected, each failing on its property's own message (§P7).
- **QUANTIFIER (P1b):** P is GUARDED: one cycle, one chunk, no shared edge with a legacy loop. Three doors walk a heal-written cycle past it: W45, W26, REF/#631. Every other invariant is ∀ with killed receipts (§P1b).
- **ENFORCEMENT (P1c):** the predicate is shared, proven by mutation (predicate→None reddens create, supersede, batch AND heal A/B/C in one run). It is not exact (#631). The chokepoint for R1 can be moved into the chunk loop with no pin going red (W26).
- **P-PKG:** the author's survey has no row for the predicate, the mechanism P rests on; mine says `replace` with networkx SCC. **P-PRIOR:** the predicate is an extraction (reuse right); the new event name is justified; test helpers are test-side. **P-PORT:** n/a (lore is not Odoo).
- `Packages considered:` networkx `strongly_connected_components`/`shortest_path` (read: installed lib, live REF2 run) → replace for the predicate · graphlib (find_blocked_by_cycle body) → keep for "any cycle" · networkx.simple_cycles, more_itertools.constrained_batches → keep. `Odoo-20 portability: n/a — no Odoo seam touched`. `Reuse ledger: none` (I built no production symbol; scratch reference only).
- **MISSING PINS:** MP-1 predicate exactness (NEW PROPERTY + SECURITY DOOR at supersede) · MP-2 ≥2 independent would-be cycles (PINNED PROPERTY, NEW CASE) · MP-3 joint cycle across a chunk boundary (PINNED PROPERTY, NEW CASE). Details in §MISSING PINS.
- `Graded: 25cfd16 · HEAD-at-report: 7a8b9d7 · DIFFERENT (3 ahead: e0df22b CLAUDE.md, 8fc46f0 parked plugin, 70665b9 fix-wave part 1 = THROW markers/docstrings/_still_claimable). None of them touches the predicate, the heal skip, the backfill early return or the four served texts.` Every run's code = 25cfd16.
- **Decisions needed:** D1 #631 design (SCC predicate vs R6's one-detector pin; am-17 §12.3 "keep the step-over") · D2 the order-dependent §12.2 fate (W21) · D3 whether MP-2/MP-3 go to the builder as requirements (my recommendation) or to the contract.
- **Pointers:** §P1 table · §MISSING PINS · §P1b · §P1c · §P-PKG · §P6 · §Surfaced · §RESIDUALS · §RUNS · §INSTRUMENTS. **Loop cost:** 1 author run + this grade + (if D1 re-opens) 1 design ruling.

## CAPABILITY CHECK
- Brief demands I can meet: lore (loaded, registered), scratch_copy.sh, the TEST store :18000, systemd-run caps. Met.
- `mutation_proof.py` needs `--file/--anchor` and mutates in place. My builds are pre-applied deltas, so I used its parser (`parse_red_node_ids`) in `wb_run.py`. It diffs the declared reds both ways, with reds declared before each run from `--collect-only` ids. Same check, different driver.
- `#620` guard: `run.sh` refuses an empty selection and a non-file selection (rc=64, proven on three inputs before the first run).
- lore_impact returned 0 covering tests for `_refuse_a_cycle` / `_reanchor_stragglers` (#563/#557 known), so the targeted set was derived by grep over event names / symbols (textual seams). I say so here.

## ROUTING TABLE (written before the first sweep / probe)

| step | tier | who | reason |
|---|---|---|---|
| read am-17 §12, coldaudit-58, findings #623/#625/#626/#628 | 3 | me | spec judgment; feeds reference build |
| read production tasks.py heal/cycle/backfill + server.py texts | 3 | me | reference build needs it |
| build reference (am-17 §12.2/12.3/12.7/12.8-1, #625 a/b) in scratch | 3 | me | design of the reference is the P0 control |
| own wrong-build enumeration (before reading author §FIXWAVE) | 3 | me | adversarial judgment |
| build wrong builds (one scratch copy each, via scratch_copy.sh) | 3 | me | each is a judgment on "plausible wrong" |
| test runs: SAT on reference, each wrong build | 1 | me inline (Bash) | each run is a mutation-proof verdict wrapped by mutation_proof.py-style both-ways diff; runner output is short and I judge every line; a haiku-runner would add a hop per build with no context saving because I read the full red set anyway. What a runner would NOT miss: nothing — so this is a cost choice; logged as a deviation from §3 default |
| P6 corpse sweep (retired served phrases, literal grep over tree) | 1 | me, one parallel batch | ≤6 literal patterns, small output, read in full; coverage line attached |
| P-PORT | n/a | — | lore is not Odoo: no Odoo seam |


## MY OWN WRONG-BUILD ENUMERATION (written 2026-11-10 from am-17 §12 + tasks.py/server.py at 25cfd16, BEFORE reading the contract's tests or REPORT-contract-58-r53.md §FIXWAVE)

Heal (P, legs A–C): W1 no check (HEAD) · W2 check, WARN, write anyway · W3 raise (boot denial) · W4 silent skip ·
W5 partial re-anchor (move X2, keep X) · W6 row-by-row check · W7 am-3 §4 `minted` copy (minted = heads) ·
W13 skipped row still counted in `count` · W14 skip stamps `updated_at`/provenance · W15 skip still runs the edge DELETE ·
W16 over-skip (any cycle ⇒ skip every pending row) · W17 predicate over the pending map only (no stored graph read) ·
W18 graph seeded from the OLD blockers instead of the new heads · W21 skipped row's graph entry not restored to its stored
column (over-skip of a row only on a cycle THROUGH the skipped row's rewrite) · W25 skip recorded under the existing
`_HEAL_CYCLE_EVENT` name · W26 check per CHUNK (joint cycle across a chunk boundary) · W30 WARNING de-duplicated by a
process-level memo (not every boot) · W11 one WARNING per cycle, not per row · W12 WARNING missing `cycle`/`members`/`blocker_ids`.
Leg D: W9 early-return kept · W19 legacy record moved into the heal (fires only when stragglers exist) · W20 recorded
first boot only (memo).
OB3 (#626): W8 DELETE only edges to read dependents · W8b DELETE filtered by the dependent's column naming the old id.
Served text: W31 F5 old text · W32 F5 fixed in text but "can never win" survives elsewhere served · W33 #130(a) only one site ·
W34 #625a hardcoded "10000" · W35 #625b keeps "file it with lore_findings" / omits #628 / hardcodes 50000.
Sharing (P1c): predicate mutated to return None ⇒ create pin, supersede pin, leg A must all redden (run on my reference).

## INTERIM (2026-11-10, measured at 25cfd16 code): the shared cycle predicate's step-over is UNSOUND
- In-memory (`stepover_probe.py`, pasted in §INSTRUMENTS): heal shape, 45/360 id orderings MISS a cycle through the
  pending row when a legacy loop shares an EDGE with it; supersede shape, 1994/2000 random successor ids MISS.
- Store, pristine 25cfd16 code (`wb/HEAD`): `TestE3…[with_legacy_loop]` — the LIVE `supersede_task` re-anchors R
  onto a cycle S -> L1 -> L2 -> R -> S (ground-truth reachability asserted) instead of raising TaskCycleError;
  control `[control_no_legacy_loop]` is refused (PASSED). Log: scratchpad logs/extra_head3.log.
- Store, my reference (spec-faithful extraction): `TestE1…[legacy_ids_sort_first]` FAILS — the heal writes D onto
  D -> H -> L1 -> L2 -> D; `[control_dependent_sorts_first]` PASSES. Property P is violated BY THE SPEC'S OWN
  algorithm (§12.3 "keeping the existing step-over"). Log: logs/extra_ref2.log.

## P-PKG — my table first (built before opening the author's survey), then the diff

| mechanism the contract/spec specifies | library evaluated | what I READ | verdict |
|---|---|---|---|
| detect a `blocked_by` cycle (any) | stdlib `graphlib.TopologicalSorter` via `find_blocked_by_cycle` | the function body at 25cfd16 (`CycleError.args[1]`) | keep (R6, sound for "is there ANY cycle") |
| **"does a MINTED/pending row lie on a cycle" (the §12.3 predicate, used by the heal AND the live supersede)** | `networkx.strongly_connected_components` + `networkx.shortest_path` (networkx is ALREADY a prod dependency: `_record_legacy_cycles` imports it) | installed networkx, exercised live: `REF2_SCC` build (wrong_delta.py) and `stepover_probe*.py` | **replace** — the spec's hand-roll (find any cycle, drop ONE edge of a non-minted one, repeat) is UNSOUND when the dropped edge is shared with the minted row's cycle (#631; 45/360 heal orderings, 1994/2000 supersede ids miss). Membership in a non-trivial SCC is the exact answer. Hand-roll ONE LEVEL DOWN: the correction ("extract the predicate") still carries the hand-rolled step-over. |
| enumerate legacy loops for the record | `networkx.simple_cycles` | `_record_legacy_cycles` body | keep (already the package) |
| chunk packing | `more_itertools.constrained_batches` | `_pack_heal_chunks` body | keep (already the package) |
| whole-number token match in served text (test side) | stdlib `re` | the helper | keep |

**Diff vs the author's survey (REPORT-contract-58-r53.md §FIXWAVE "Package survey"):** the author surveyed only the
TEST-side detector (`find_blocked_by_cycle`, REUSED), `re` and `argparse`. The mechanism the contract's central property
P rests on — the minted-row cycle predicate — has NO row. That missing row is exactly where the defect lives (#631).

## P-PRIOR — new symbols the contract demands
| new symbol | where I looked | owner found | verdict |
|---|---|---|---|
| the extracted predicate (`first_cycle_through_minted` in my ref; author's `cycle_through_minted`) | `_refuse_a_cycle` body; lore_search "strongly connected components cycle membership" (1 hit: 04b3 adversary report §7, build R "from-minted DFS" graded as a SHARING violation of R6); grep `strongly_connected\|shares an edge` over tasks.py (0) | `_refuse_a_cycle`'s loop (extraction = reuse, correct) | REUSE is right; but the owner itself is unsound (#631) |
| `task.backfill.straggler_would_close_cycle` event | grep of `_HEAL_*_EVENT` / `_BACKFILL_*_EVENT` constants | `_HEAL_CYCLE_EVENT` (chain-of-supersession cycle) and `_BACKFILL_CYCLE_EVENT` (legacy loop) are different causes | new name justified (§12.2 rules it) |
| `assert_hub_refusal_serves_its_facts`, `HUB_TIMEOUT_BAND_FINDING`, `HUB_REFUSAL_RETIRED_PHRASES` (test support) | lore_search for a "whole-token number in served text" helper — the tool errored once (`SurrealDB query rejected against :18500`, transient; retry worked); grep `(?<![0-9])` over tests | none found | test-side, acceptable |

## Surfaced (spec-level, from `restore_probe.py`, in-memory over the reference's predicate, 2026-11-10)
- **§12.2's fate is ORDER-DEPENDENT.** World: D1 [X1→H1], H1 [D1, D2]; D2 [X2→H2], H2 [D1]. D1 alone closes D1→H1→D1;
  D2 closes a cycle only THROUGH D1's rewrite. "every pending row ON that cycle is skipped" skips BOTH rows for 12 of
  24 id orderings (the detector reports the long cycle first) and D1 ONLY for the other 12 (D2 heals). Both satisfy P;
  they differ in what the store holds and what WARNINGs fire. The spec does not say which is intended.
- Consequence for grading: a "no-restore" build (W21: a skipped row keeps its REWRITTEN column in the predicate's view)
  differs from the reference in 9/24 orderings (it over-skips D2), and NO contract pin can be written against it until
  the spec picks a fate. Fork for the lead, not a missing pin (see DECISIONS).

## P6 — corpse sweep of the retired served phrases (git grep over all 1838 tracked files at 25cfd16 code, docs/design + receipts counted separately; textual seam ⇒ grep is the right tool)
| hit | verdict |
|---|---|
| `server.py` claim render "so this claim can never win" | the F5 target; builder (pinned by F5 leg) |
| `server.py` comment "this claim can NEVER win" | builder rider (§12.7: "the code comment … is corrected with it"); NOT pinned (comment) — cold-audit check |
| `tests/test_task_read_surface.py` F5's OLD render pin, failure MESSAGE "this claim can NEVER win" | prose corpse: its assertion (blocker + successor named) passes on both texts, but its failure message teaches the retired over-claim. NO ROUND residual; cheap fix for the contract author |
| `tests/test_task_ledger.py:908` "claim that can never win" | TRUE there (a never-minted/phantom blocker refuses forever). keep |
| `tests/test_blocks_edge.py:7352` "attempts a claim that can never win" | confident-empty traversal message; different defect. keep |
| `tests/test_query_tasks_bounded.py:616` "claim that can never win" | message about an OPEN direct blocker: over-claims (the mid can finish), unrelated to F5. NO ROUND residual, outside F5 |
| `tasks.py` `StragglerHealPackerError` "transaction cap — the heal" | #625 a target; builder (pinned) |
| `tasks.py` `HubSupersedeRefusedError` "pinned KNOWN BOUND (58 F-1); file it with lore_findings" | #625 b target; builder (pinned) |
| `tests/_reanchor_58_support.py` `HUB_REFUSAL_RETIRED_PHRASES` | the pin itself. keep |
| `server.py` "exact-status filter" at the `lore_tasks` `status` Field | #130(a) target; pinned |
| `server.py` "status: The exact-status filter" (internal `_query_tasks` docstring) | §12.7 names "two sites"; this one is NOT served → unpinned builder rider, cold-audit check |
| `server.py` `lore_findings` status Field "exact-status filter (open / acknowledged / …)" | a different tool; not #130. keep |
| `tasks.py` `query_tasks` docstring (§12.7 names it) | not served; unpinned builder rider, cold-audit check |
| other "pinned KNOWN BOUND" hits (11a doc, test_agent_governance_63c, test_agent_registry, test_comms_promise_registry, test_message_migrate_dirty_store_63b, test_pytest_workers_503) | unrelated packets; the 2026-11-09 pin-the-miss conversion set, not this contract. keep (Phase 4 owns them) |

## P1 — wrong builds (each its own scratch copy via `scripts/scratch_copy.sh`, code pinned to 25cfd16, REF + ONE delta; reds declared from `--collect-only` ids BEFORE the run in `declared/<build>` (written 2026-11-10T06:31:50Z / 06:34Z / 06:37Z); verdict = `wb_run.py` both-ways diff through `mutation_proof.parse_red_node_ids`)

Every row: `loremaster.__file__` asserted inside its own copy by `mk.sh` and printed at the top of its log.
"killed" = observed RED set == declared set, and the failure text read per test was the property's own message.

| build | what it does | selection | declared → observed | verdict |
|---|---|---|---|---|
| NOCHECK (= 25cfd16 heal) | no predicate in the heal | fixwave file | A,B,C → A,B,C | killed |
| W2 check-then-write | records, writes anyway | fixwave | A,B,C → same | killed |
| W3 raise | boot denial (TaskCycleError) | fixwave | A,B,C → same | killed |
| W4 silent skip | no WARNING | fixwave | A,B,C → same | killed |
| W5 partial re-anchor | moves the blockers whose head is off the cycle | fixwave | A,C → same | killed |
| W6 row-by-row | predicate per row against stored graph | fixwave | B → B | killed |
| W7 am-3 §4 minted copy | minted = the new heads | fixwave | C → C | killed |
| W13 counted | skipped rows counted in `count` | fixwave | A,B,C → same | killed |
| W14 stamp | skipped row's `updated_at` touched | fixwave | A,B,C → same | killed |
| W15 edge delete | skipped row's edge DELETE still runs | fixwave | A,B,C → same | killed |
| W16 over-skip | any cycle ⇒ skip all pending | fixwave | A → A (S not healed) | killed |
| W17 no stored graph | predicate over pending only | fixwave | A,B,C → same | killed |
| W18 old seeds | closure seeded from the superseded ids | fixwave | A,B,C → same | killed |
| W25 old event name | records as `straggler_chain_cycle` | fixwave | A,B,C → same | killed |
| W30 memo | WARNING de-duplicated per process | fixwave | A → A (boot 2) | killed |
| W11 one per cycle | WARNING for the first row only | fixwave | B → B | killed |
| W12 no `cycle` extra | | fixwave | A,B,C → same | killed |
| W12b blocker_ids = whole column | | fixwave | C → C | killed |
| EARLY_RETURN (leg D at HEAD) | | fixwave | D → D | killed |
| W20 legacy memo | legacy loop recorded once per process | fixwave | D → D | killed |
| W46 double record | legacy loop recorded twice on a missing-edge boot | fixwave + legacy classes of test_blocks_edge | 4 → 3 (`TestTheEnumerationEQUALSNetworkxAfterTheSwap` ×3 red; my 4th prediction, the DISJOINT pin, stayed green: it checks membership, not count) | killed |
| W8 OB3 (#626) | DELETE only edges to read dependents | fixwave | OB3 → OB3 | killed |
| W8b both directions | | fixwave | OB3 → OB3 | killed |
| W31 F5 old text | | fixwave | F5 → F5 | killed |
| W33 #130(a) old text | | fixwave | 130a → 130a | killed |
| W34 #625a hardcoded 10000 | | conv class + hub class | conv → conv | killed |
| W34b #625a serves the HARD cap | | same | conv → conv | killed |
| W35 #625b keeps "file it with lore_findings" | | same | hub[0],[2] → same | killed |
| W35b #625b drops #628 | | same | hub[0],[2] → same | killed |
| **W45 single pass** | asks the predicate ONCE, skips that cycle's rows, writes the rest | fixwave + my E4 | E4 → E4 (**7/7 contract tests GREEN**) | **SURVIVES the contract** |
| **W26 per chunk** | ONE graph read, predicate per CHUNK | the whole heal set (20 files) + my E2 | E2 → E2 (**307 contract tests GREEN**) | **SURVIVES the contract** |
| W21 no restore | skipped row keeps its rewritten column in the view | heal set (20 files) | ∅ → ∅ (307 passed) | survives; NOT gradable until D2 is ruled (the spec's fate is order-dependent, see Surfaced) |
| **REF (spec-faithful)** | my reference | my probes | E1[legacy_first], E3[with_legacy] → same | **violates P** on E1; live supersede hole on E3 — #631 |
| REF2_SCC (sound predicate, NOT a wrong build) | SCC membership + shortest path through the minted row | 25-file set; my probes | R6 sharing pin → that pin (1 failed / 1584 passed); probes ∅ → ∅ (6/6) | the fix is satisfiable against everything except R6's one-detector pin |
| PRED_NONE (sharing mutation) | predicate returns None | heal legs + supersede rewire class + 04b3 file + 3 blocks_edge classes | 9 → 11 (+self-block, +batch-key tool seam) | sharing PROVEN |

## P1b — QUANTIFIER TABLE (every invariant the contract pins; receipts are runs in §P1)

| invariant | as pinned | ∀ or GUARDED | receipt |
|---|---|---|---|
| P: no row the heal wrote lies on a cycle | legs A/B/C + `find_blocked_by_cycle(all_columns) is None` | **GUARDED** — by the three named shapes, each with ONE cycle among the pending rows, in ONE chunk, and with NO legacy loop sharing an edge with the would-be cycle | three doors walk the same bad outcome (a heal-written cycle) past every pin: **W45** (two independent cycles; single-pass loop) — 7/7 green, dies only on my E4; **W26** (cycle across a chunk boundary) — 307/307 heal-set green, dies only on my E2; **the spec-faithful REF itself** (legacy loop sharing an edge) — green on the contract, violates P on my E1 (#631) |
| a skipped row is untouched (column, edges, updated_at) and uncounted | `_row_state` equality + `count`/`sum(healed)` | ∀ skipped rows in A/B/C | W13, W14, W15, W5 killed |
| a healthy straggler still heals beside a skipped one | A's S + control 2 | GUARDED to "unrelated" healthy rows (not a row whose only cycle runs through a skipped row's rewrite) | W16 killed; W21 survives (but the spec's own fate is order-dependent there — Surfaced, not gradable) |
| the skip is recorded every boot, per row, with the ruled extras | `_assert_one_skip_record`, boots 1 and 2 | ∀ skipped rows × 2 boots | W4, W11, W12, W12b, W25, W30 killed |
| the boot completes (no denial) | A's boot runs | ∀ legs | W3 killed |
| a legacy loop is recorded on every boot, once | leg D, two boots, no missing edge | GUARDED to a 2-cycle on a nothing-missing boot; the missing-edge boot is covered by the existing count pins | EARLY_RETURN, W20 killed by leg D; W46 (double record on a missing-edge boot) killed by the existing `TestTheEnumerationEQUALSNetworkxAfterTheSwap` count pins (3/3) |
| supersede deletes every out-edge of the old task | OB3, a drift edge | ∀ out-edges in a non-mirror world | W8, W8b killed |
| served texts say what is true | F5, #130(a), #625 a (shrunk world), #625 b (facts) | per text | W31, W33, W34, W34b, W35, W35b killed |

## P1c — ENFORCEMENT TABLE
Legs: removal and move-after were run (EMPIRICAL); sharing was run by mutation (EMPIRICAL); spelling verdict by inspection.

| rule | the ONE chokepoint | effect vs proxy (removed / moved after) | sharing by mutation | spelling-test verdict |
|---|---|---|---|---|
| R1 heal writes no cycle (P) | the heal's pre-pack skip over the whole pending set (§12.2) | EFFECT: removed (NOCHECK) → A,B,C red; moved after the write (W2) → A,B,C red; moved INTO the chunk loop (W26) → **green** (no multi-chunk fixture) — MISSING PIN | — | behaviour pins only |
| R2 the cycle predicate is ONE shared policy (create, create_many, supersede, heal) | the extracted predicate | EFFECT | **PROVEN, one run**: predicate → `None` (PRED_NONE) reddens the live create pin, the persisted-coexisting-legacy pin, the supersede rewire pin, the batch-id pin, the formatter-mutation pin, the cycle-vs-existence pin, self-block, batch-key tool seam, AND heal legs A/B/C (11/27 red, 9 declared + 2 more, 0 declared-but-green). No private copy. | the existing `test_blocks_edge.py` supersede pin that asserts `"_refuse_a_cycle" in called_attrs` is a SPELLING check (pre-existing, not introduced here) — operator decision, not graded |
| R2′ the predicate is EXACT (a minted row on any cycle is found) | same predicate | **MISSING PIN — the predicate is unsound** (#631): its step-over drops an edge shared with the minted row's cycle. Store reproduction at pristine 25cfd16: live supersede writes S→L1→L2→R→S (E3[with_legacy_loop]); control without the shared edge is refused | — | — |
| R3 skipped rows recorded every boot | the same loop | EFFECT (W4, W30) | — | none |
| R4 legacy loop recorded every boot | `_backfill_blocks_edges` before its early return | EFFECT (EARLY_RETURN, W20, W46) | — | none |
| R5 supersede removes every out-edge | `_supersede_transaction`'s graph-anchored DELETE | EFFECT (W8, W8b) | — | none |
| R6 served texts | `server.py` claim render; the `lore_tasks` `status` Field; `StragglerHealPackerError`; `HubSupersedeRefusedError` | EFFECT, read through the dispatcher / served schema / raised error (W31, W33, W34, W34b, W35, W35b) | the #625a pin reads the LIVE bound under a shrink, so a copied-at-import or hardcoded value reds (W34, W34b) | #130(a) is a substring check on served schema text — behaviour of served output, acceptable |

## MISSING PINS (each as a CLASS; triage bucket per the tdd ROUND CAP)

### MP-1: the cycle predicate is not exact. NEW PROPERTY (heal; goes to the lead) + SECURITY DOOR (live supersede)
- **The test that should exist:** at the predicate's two persisted-graph doors, one behaviour leg each, in a world where a legacy loop L1↔L2 SHARES an edge with the would-be cycle and its ids sort first:
  - heal (my E1): X→H, H `[L1]`, L1 `[L2]`, L2 `[L1, D]`, D `[X]` ⇒ after boot D is unchanged and recorded, and D is not on a cycle (checked by ground-truth reachability, not by `find_blocked_by_cycle`, whose first answer is the legacy loop);
  - supersede (my E3): R `[X]`, L1 `[L2]`, L2 `[L1, R]`; `supersede(X, blocked_by=[L1])` ⇒ `TaskCycleError`.
  - Each leg has its control: E1 with the dependent's id sorting first, E3 without the back edge L2→L1. Both are green on REF.
- **Defect it catches:** a supersede or heal that writes a `blocked_by` cycle (every member unclaimable forever) while the guard reports acyclic. Reproduced at 25cfd16 for the live supersede, and for the spec-faithful heal.
- **CLASS:** a cycle guard must answer "does any minted/pending row lie on a cycle?" exactly, over every graph. Today it answers that only when no non-minted loop shares an edge with the minted cycle.
- **CHOKEPOINT:** the extracted predicate (`_refuse_a_cycle`'s loop today), the ONE place create, create_many, supersede and the heal all route through (PRED_NONE proves the routing).
- **SIBLINGS TRIED:** heal (E1, REF red), live supersede (E3, HEAD and REF red), in-memory both shapes (45/360 and 1994/2000 misses), and a sound replacement (REF2_SCC green on all probes).
- **SIBLINGS NOT TRIED:** `create_task` and `create_many`, by argument only. A fresh uuid4 id cannot be named by any persisted row, so their minted cycle cannot run through persisted rows that a legacy loop shares. It only became reachable when packet 58 put rewired dependents into `pending` (am-3 §4).
- **Why NEW PROPERTY, not a builder requirement:** §12.3 tells the builder to keep "the existing step-over" and to keep `find_blocked_by_cycle` / `_drop_one_cycle_edge` as "the only detector and the only step-over". The R6 pin `TestTheCyclePolicyHasONEImplementation::test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through` reds on a sound SCC predicate (REF2 run). A builder following the spec ships the hole, and one fixing it reds a pinned ruling. This is a design problem and must not reach a builder (repo CLAUDE.md).
- **Why SECURITY DOOR at supersede:** the cycle refusal is a validation guard a caller reaches through `lore_tasks supersede`. It needs pre-existing legacy loop data, which the backfill exists to record, so it is real data, not planted.

### MP-2: two or more independent would-be cycles. PINNED PROPERTY, NEW CASE (→ builder requirement + cold-audit probe)
- **Test:** two stragglers, each closing its OWN 2-cycle (D1 [X1→H1], H1 [D1]; D2 [X2→H2], H2 [D2]). After boot there is no cycle over all columns and both rows are unchanged and recorded (my E4).
- **Defect:** a loop that asks the predicate once (W45), skips that cycle's rows and writes the rest, writes D2 onto D2→H2→D2. It passes 7/7 of the fix-wave file.
- **CLASS:** P ∀ pending sets, including ones holding several disjoint would-be cycles. The §12.2 "ask again" step is unpinned: every leg has exactly one cycle.
- **CHOKEPOINT:** the §12.2 skip loop (re-ask after each skip).
- **SIBLINGS TRIED:** two disjoint 2-cycles. **NOT TRIED:** three or more, and a cycle surfacing only after the step-over drops edges.
- **Builder requirement:** loop until the predicate returns None. Cold-audit probe: E4 (pasted).

### MP-3: a joint cycle across a chunk boundary. PINNED PROPERTY, NEW CASE (→ builder requirement + cold-audit probe)
- **Test:** leg B's world with the heal packing one row per chunk (E2 patches `_pack_heal_chunks`; a contract version should shrink `TXN_ROW_WARN_THRESHOLD` below two rows' cost instead, the house `shrunk_row_caps` idiom). After boot there is no cycle over all columns.
- **Defect:** a build that reads the graph once but runs the predicate per chunk (W26) writes D1→H1→D2→H2→D1 once the stragglers span two chunks. Every heal test passes (307/307).
- **CLASS:** P over the WHOLE pending set (§12.2 "not row by row") holds whatever the chunk packing.
- **CHOKEPOINT:** the skip runs BEFORE `_pack_heal_chunks`.
- **SIBLINGS TRIED:** a 2-row joint cycle, one row per chunk. **NOT TRIED:** a cycle spanning three chunks.
- **Exposure:** needs more than 10,000 composed rows (am-17 §5's `chunks >= 2` re-open trigger). It is reachable on a large store, which is why it gets a probe rather than a residual.

## P2 — fixture discrimination (perturbations, each with its correct-build control)
| contract fixture | perturbation | wrong build on perturbed | correct build on perturbed | verdict |
|---|---|---|---|---|
| leg B (one chunk) | one row per chunk (E2) | W26 RED (cycle written) | REF GREEN | leg B only discriminates at "everything in one chunk" |
| leg A (one cycle) | add a second, independent cycle (E4) | W45 RED | REF GREEN | leg A/B/C never exercise the loop's second pass |
| leg C (legacy loop through the row itself) | legacy loop elsewhere, sharing an EDGE with the would-be cycle, ids sorting first (E1) | — | REF RED (spec defect), REF2_SCC GREEN; ordering control (dependent sorts first) GREEN on REF | leg C never exercises the step-over: its cycle contains D directly |
| leg A control 1 (live supersede refused) | add a legacy loop sharing an edge (E3) | HEAD/REF RED (supersede succeeds, successor on a cycle) | REF2_SCC GREEN; no-shared-edge control GREEN on HEAD | the live refusal pin only discriminates in edge-disjoint worlds |
| leg D (2-cycle, nothing missing) | — (W46 tried instead: double record on a missing-edge boot) | killed by existing count pins | — | discriminates |
| #625a shrunk 5000/800 world | — | W34 (10000), W34b (hard cap 5000) RED | REF GREEN | discriminates the live bound |
| #625b shrunk world, [0] and [2] | — | W35/W35b RED | REF GREEN | discriminates |

## P7 — RED honesty (reproduced)
`wb/HEAD` = 25cfd16 code, the 9 registry ids declared from `scripts/pending_contracts.yaml` (`packet-58-fixwave`), selection = fix-wave file + the convergence class + the hub class. Result: **9 failed / 10 passed, declared 9, observed 9, 0 unexpected, 0 declared-but-green**. Every failure is the property's own message:
- A: `S must heal and be the ONLY row counted: [(2, 1)]`
- B: `the heal wrote a cycle`
- C: `D was re-anchored onto its legacy loop`
- D: `must be recorded exactly once per boot; saw []`
- F5: `the ruled form … is not served`
- #130a: the old description
- #625a: `still says transaction cap`
- #625b [0] and [2]: `does not name #628`

The author's leg-C wrong-reason RED (setup ENFORCED) is fixed at 25cfd16. I confirmed C now reds for the cycle reason.

## P6b — the dual (code being replaced)
The brief named no Phase 0 removed-behaviour inventory, so there was nothing to diff against. My own enumeration:
- **`_refuse_a_cycle`'s loop:**
  1. empty pending → no read;
  2. seeds are the union of the pending blockers;
  3. one bounded closure read;
  4. pending overlays the graph;
  5. `minted` defaults to `set(pending)`;
  6. a cycle through a minted row raises `TaskCycleError` with the persisted-ids sentence; a non-minted cycle is stepped over one edge at a time; when no edge can be dropped, it accepts.

  All six are preserved by the extraction in my REF, and PRED_NONE shows every caller still behaves through the extracted predicate. Behaviour 6's step-over is the defect (#631).
- **`_backfill_blocks_edges`'s early return:** a nothing-missing boot makes no existence probe and records nothing. Leg D rules the record moved before the return. The existence probe and the round-trip count are unchanged (two on a nothing-missing boot): the record is in memory.
- Nothing else is deleted.

## DECISIONS NEEDED (lead; the operator may overrule)
- **D1 (#631, MP-1):** replace the step-over with an exact predicate. My recommendation: networkx SCC membership, plus a shortest path through the minted row for the served/recorded cycle string, pasted as `REF2_SCC` in wrong_delta.py. This means re-ruling R6's "find_blocked_by_cycle is the only detector" for the minted-row question: keep it for "any cycle" and for the batch-key check. **Alternative:** keep R6 and make the step-over sound, i.e. never drop an edge that lies on a path between two minted rows' SCC members. That is more hand-roll, the hand-roll ONE LEVEL DOWN again. **Scope note:** the live supersede hole is pre-existing in 25cfd16 production code (packet 58, never deployed per §12.8-3). Fixing it in this wave widens §12.6's "exhaustive" contract scope, which is your call.
- **D2 (W21, Surfaced):** §12.2's fate depends on detector order (12/24 orderings skip a row that would not close a cycle on its own). Pick one:
  - canonical-over-skip: skip every pending row in a non-trivial SCC of the overlay. SCC gives this directly, and it is deterministic;
  - minimal: skip only rows still on a cycle after the others are restored.

  Then one pin.
- **D3 (MP-2/MP-3):** the brief's triage sends a new case of a pinned property to the builder plus a cold-audit check. I recommend that: E4 and E2 are pasted and ready for the audit.

## RESIDUALS (each with its own verdict; none reopens a round)
1. `test_task_read_surface.py` F5's old render pin: its failure MESSAGE still teaches "this claim can NEVER win" (its assertion passes on both texts). NO ROUND; cheap for the author.
2. `test_query_tasks_bounded.py:616` message over-claims "can never win" for an OPEN direct blocker. Unrelated to F5. NO ROUND.
3. Unpinned builder riders (cold-audit checks):
   - the `server.py` comment above the F5 text;
   - `server.py` `_query_tasks` docstring "The exact-status filter";
   - `tasks.py` `query_tasks` docstring (#130(a) names it);
   - `_refuse_a_cycle`'s "already RECORDED" sentence (§12.3 rider; after leg D it is true every boot, except for #631's missed cycles).

   NO ROUND.
4. The #130(a) pin is a two-substring check ("superseded" and "exclud"). A sentence that misstates the exclusion but carries both words passes. Low plausibility. NO ROUND.
5. The `lore_tasks` `blocked` Field does not name the exclusion. §12.7 names only `status`. Spec-silent → lead.
6. `_assert_one_skip_record` checks that `cycle` contains the task id and " -> ", not that it is the actual cycle (a "D -> D" string passes). It is a log record only. NO ROUND.
7. Leg D is GUARDED to a 2-cycle (the author says so; simple_cycles' arity is pinned elsewhere). Accepted.
8. Pre-existing spelling pins relied on, not introduced here, for an operator decision:
   - `test_blocks_edge.py` asserts `"_refuse_a_cycle" in called_attrs`;
   - `test_networkx_is_imported_by_the_PRODUCTION_tasks_module`;
   - R6's detector-mutation pin, which now blocks a sound predicate (D1).
9. lore_impact returned 0 covering tests for the heal/cycle symbols (#563/#557, known). The targeted set was derived by grep.
10. A transient `lore_search` store rejection was filed as **#632**.
11. The live HEAD moved 3 commits during the grade, including the builder's fix-wave part 1 (70665b9), so a builder is already working. The §12 heal/predicate is not in that commit.

## §RUNS (46; every one capped: systemd-run MemoryMax=16G MemorySwapMax=0, -n ≤ 8, --timeout=300, TEST store :18000; logs under the scratchpad's logs/, non-durable)
| # | build → tests → result (count line from the log) |
|---|---|
| 1 | REF → 25-file targeted set (full contract tag set, the ONE over-fire check) → 1585 passed, 1 skipped, 35 warnings in 417.22s (0:06:57) |
| 2 | probe development extra_ref → probes file/classes → 1 failed, 2 passed in 2.53s |
| 3 | probe development extra_head → probes file/classes → 1 failed in 2.44s |
| 4 | probe development extra_ref2 → probes file/classes → 3 failed, 2 passed in 3.05s |
| 5 | probe development extra_head2 → probes file/classes → 2 failed in 2.39s |
| 6 | probe development extra_head3 → probes file/classes → 1 failed, 1 passed in 2.30s |
| 7 | NOCHECK: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.58s |
| 8 | W2_WARN_WRITE: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.45s |
| 9 | W3_RAISE: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 5.09s |
| 10 | W4_SILENT: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.69s |
| 11 | W5_PARTIAL: declared=2 observed=2 unexpected=0 declared-but-green=0 | 2 failed, 5 passed in 4.58s |
| 12 | W6_ROW_BY_ROW: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.62s |
| 13 | W7_MINTED_HEADS: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.72s |
| 14 | W13_COUNTED: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 5.30s |
| 15 | W14_STAMP: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.77s |
| 16 | W15_EDGE_DELETE: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.53s |
| 17 | W16_OVERSKIP: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.50s |
| 18 | W17_NO_STORED_GRAPH: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 5.02s |
| 19 | W18_OLD_SEEDS: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.71s |
| 20 | W21_NO_RESTORE: declared=0 observed=0 unexpected=0 declared-but-green=0 | 7 passed in 4.66s |
| 21 | W25_OLD_EVENT: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.57s |
| 22 | W26_PER_CHUNK: declared=0 observed=0 unexpected=0 declared-but-green=0 | 7 passed in 4.57s |
| 23 | W30_MEMO: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.54s |
| 24 | W11_ONE_PER_CYCLE: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.50s |
| 25 | W12_NO_CYCLE_EXTRA: declared=3 observed=3 unexpected=0 declared-but-green=0 | 3 failed, 4 passed in 4.64s |
| 26 | W12b_BLOCKERS_ALL: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.64s |
| 27 | EARLY_RETURN: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.44s |
| 28 | W20_LEGACY_MEMO: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.47s |
| 29 | W8_OB3: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.56s |
| 30 | W8b_BOTH_DIRECTIONS: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.36s |
| 31 | W31_F5_OLD: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.44s |
| 32 | W33_130a_OLD: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 6 passed in 4.67s |
| 33 | W34_625a_HARDCODE: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 11 passed in 10.36s |
| 34 | W34b_625a_HARDCAP: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 11 passed in 10.76s |
| 35 | W35_625b_KEEP_FILE: declared=2 observed=2 unexpected=0 declared-but-green=0 | 2 failed, 10 passed in 8.42s |
| 36 | W35b_625b_NO_FINDING: declared=2 observed=2 unexpected=0 declared-but-green=0 | 2 failed, 10 passed in 8.53s |
| 37 | W45_SINGLE_PASS: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 7 passed in 4.49s |
| 38 | W26_PER_CHUNK: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 307 passed, 32 warnings in 77.73s (0:01:17) |
| 39 | W21_NO_RESTORE: declared=0 observed=0 unexpected=0 declared-but-green=0 | 307 passed, 32 warnings in 78.21s (0:01:18) |
| 40 | W46_DOUBLE_RECORD: declared=4 observed=3 unexpected=0 declared-but-green=1 | 3 failed, 22 passed in 4.82s |
| 41 | PRED_NONE: declared=9 observed=11 unexpected=2 declared-but-green=0 | 11 failed, 16 passed in 5.07s |
| 42 | REF2_SCC: declared=1 observed=1 unexpected=0 declared-but-green=0 | 1 failed, 1584 passed, 1 skipped, 35 warnings in 363.16s (0:06:03) |
| 43 | ref: declared=2 observed=2 unexpected=0 declared-but-green=0 | 2 failed, 4 passed in 2.36s |
| 44 | REF2_SCC: declared=0 observed=0 unexpected=0 declared-but-green=0 | 6 passed in 2.33s |
| 45 | HEAD: declared=2 observed=1 unexpected=0 declared-but-green=1 | 1 failed, 1 passed in 2.07s |
| 46 | HEAD (25cfd16 code) RED reproduction → fixwave + conv class + hub class → 9 failed, 10 passed in 10.82s |

Full-set justification: run 1 is the contract's over-fire check; the REF2_SCC 25-file run prices the D1 fix's blast radius across the targeted set (it is the only way to see which existing pins a sound predicate reddens). The W26/W21 20-file runs confirm survival across every heal test, not just the fix-wave file.

## Gate receipts (my runs; this role edits no repo file except this report)
| gate | command | log (scratch, non-durable) | EXIT | count | TREE |
|---|---|---|---|---|---|
| SAT on reference | `run.sh ref sat_ref.log 8 $(cat sat_set.txt)` | logs/sat_ref.log | 0 | 1585 passed, 1 skipped | 570b446f…a7a |
| RED reproduction | `wb_run.py wb/HEAD head_red.log 4 declared/HEAD_RED <fixwave> <conv class> <hub class>` | logs/head_red.log | 1 | 9 failed, 10 passed (9/9 declared) | bb7fbda9…e4d |
| REF2 pricing | `wb_run.py wb/REF2_SCC wb_REF2_SAT.log 8 declared/REF2_SCC $(cat sat_set.txt)` | logs/wb_REF2_SAT.log | 1 | 1 failed (declared R6 pin), 1584 passed | fb4762b4…233 |
| #631 store repro at 25cfd16 | `wb_run.py wb/HEAD probes_head_final.log 4 … ::TestE3…` | logs/probes_head_final.log | 1 | 1 failed (with_legacy_loop), 1 passed (control) | bb7fbda9…e4d |

TREE= is of each scratch copy (25cfd16 code + the build's delta + my probe file), not of 25cfd16 itself. The copies' git HEAD reads e0df22b/7a8b9d7, because the live repo moved while I was copying. Content was pinned with `git checkout 25cfd16 -- .`, and `git diff 25cfd16 --stat` in a copy shows only the delta and the probe file (checked on wb/W45_SINGLE_PASS).

`sat_set.txt` (25 files): test_blocks_edge, test_cycle_write_path_04b3, test_mcp_server, test_query_tasks_bounded, test_reanchor_58_{fixwave, r2_am2, r2_probes, r2_rulings, r2_scale, r3_am6, r3_cas_seam, r3_convergence, r3_probes, r3_relate, r3_tiers, r4_lease_fates, r4_state, r53_bound_and_plans, r5_rows}, test_supersede_reanchor_58, test_task_claimable_partition_58, test_task_guarded_shell_58, test_task_ledger, test_task_read_surface, scripts/test_forgery_door_sweep. Derivation: grep over the textual seams (event names `straggler`/`legacy_cycle_minted`, `_refuse_a_cycle`, `TaskCycleError`, `find_blocked_by_cycle`, the two error classes, `max_reanchor_dependents`) plus the served `lore_tasks` schema suite. I fell back to grep because lore_impact showed 0 covering tests (#563).

## §INSTRUMENTS — pasted verbatim (scratch tools; not committed — the writable set is this report only)

### `tools/ref_patch.py`
```python
#!/usr/bin/env python3
"""Reference build of am-17 §12.2/§12.3/§12.7/§12.8-1 + #625 a/b + #130(a), applied to a scratch copy at 25cfd16.

Usage: ref_patch.py <copy-root> [VARIANT]
VARIANT selects a wrong build (default: REF, the reference). Every edit asserts its anchor matched exactly once.
"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
variant = sys.argv[2] if len(sys.argv) > 2 else "REF"
tasks = root / "loremaster/loremaster/tasks.py"
server = root / "loremaster/loremaster/server.py"


def sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{path.name}: anchor matched {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


# ---- §12.3 the extracted predicate (module level, beside the detector) ----------------------------------
PRED = '''

def first_cycle_through_minted(
    graph: Mapping[str, Iterable[str]],
    pending: Mapping[str, Sequence[str]],
    minted: set[str],
) -> list[str] | None:
    """The ONE cycle PREDICATE (am-17 §12.3): the first ``blocked_by`` cycle a ``minted`` row lies on.

    ``graph`` is the stored closure, ``pending`` overlays the columns about to be written. A loop that
    touches no minted row is stepped over one edge at a time (``_drop_one_cycle_edge``), so a different
    loop through the same rows still surfaces. Returns ``None`` when no minted row is on a cycle.
    """
    work: dict[str, set[str]] = {node: set(refs) for node, refs in graph.items()}
    for task_id, blockers in pending.items():
        work[task_id] = set(blockers)
    while True:
        cycle = find_blocked_by_cycle(work)
        if cycle is None:
            return None
        if minted.intersection(cycle):
            return cycle
        if not _drop_one_cycle_edge(work, cycle):
            return None
'''
if variant == "PRED_NONE":  # sharing mutation: the predicate never finds a cycle
    PRED = PRED.replace("    work: dict[str, set[str]] =", "    return None\n    work: dict[str, set[str]] =")

sub(tasks, "\n\ndef _superseded_blocker_clause(", PRED + "\n\ndef _superseded_blocker_clause(")

# _refuse_a_cycle routes through it
sub(
    tasks,
    '''        graph: dict[str, set[str]] = {
            node: set(refs)
            for node, refs in (await self._bounded_dependency_graph(seeds)).items()
        }
        for task_id, blockers in pending.items():
            graph[task_id] = set(blockers)
        minted = set(pending) if minted is None else minted
        while True:
            cycle = find_blocked_by_cycle(graph)
            if cycle is None:
                return
            if minted.intersection(cycle):
                raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)
            if not _drop_one_cycle_edge(graph, cycle):
                return
''',
    '''        graph = await self._bounded_dependency_graph(seeds)
        cycle = first_cycle_through_minted(
            graph, pending, set(pending) if minted is None else minted
        )
        if cycle is not None:
            raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)
''',
)

# ---- §12.2 the heal: event constant ---------------------------------------------------------------------
sub(
    tasks,
    '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n',
    '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n'
    '_HEAL_WOULD_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n',
)

# _plan_heal_rows carries (final column, olds) on each built entry
sub(
    tasks,
    "            built.append((dependent, fragments, relates, cost))\n",
    "            built.append((dependent, fragments, relates, cost, final, olds, columns))  # type: ignore[arg-type]\n",
)

# heal: skip rows whose re-anchor would close a cycle, over the WHOLE pending set
SKIP_CALL = "        built = await self._skip_cycle_closing_rows(built)\n"
if variant == "NOCHECK":
    SKIP_CALL = ""
sub(
    tasks,
    "        built = self._plan_heal_rows(stragglers, successor, heads, existing, at)\n",
    "        built = self._plan_heal_rows(stragglers, successor, heads, existing, at)\n" + SKIP_CALL,
)

SKIP_METHOD = '''
    async def _skip_cycle_closing_rows(self, built: list[Any]) -> list[Any]:
        """am-17 §12.2: drop (and record, every boot) every planned row whose re-anchor would close a cycle.

        The check is over the WHOLE pending set at once (two rows can close a cycle jointly), through the
        ONE predicate ``first_cycle_through_minted``, over ONE graph read. A skipped row's graph entry returns
        to its stored column and the predicate is asked again; ``pending`` shrinks, so the loop ends.
        """
        if not built:
            return built
        pending = {entry[0]: list(entry[4]) for entry in built}
        stored_column = {entry[0]: list(entry[6]) for entry in built}
        olds_of = {entry[0]: list(entry[5]) for entry in built}
        seeds = {blocker for blockers in pending.values() for blocker in blockers}
        graph: dict[str, list[str]] = dict(await self._bounded_dependency_graph(seeds))
        skipped: set[str] = set()
        while pending:
            view = {**graph, **{row: stored_column[row] for row in skipped}}
            cycle = first_cycle_through_minted(view, pending, set(pending))
            if cycle is None:
                break
            on_cycle = [row for row in pending if row in cycle]
            for row in on_cycle:
                logger.warning(
                    _HEAL_WOULD_CYCLE_EVENT,
                    extra={
                        "database": self._database,
                        "task_id": row,
                        "blocker_ids": olds_of[row],
                        "cycle": " -> ".join(cycle),
                        "members": sorted(set(cycle)),
                    },
                )
                skipped.add(row)
                del pending[row]
        return [entry for entry in built if entry[0] not in skipped]

    def _plan_heal_rows(
'''
sub(tasks, "\n    def _plan_heal_rows(\n", "\n" + SKIP_METHOD)

# ---- §12.8 item 1, leg D: record legacy loops on every boot ---------------------------------------------
if variant != "EARLY_RETURN":
    sub(
        tasks,
        '''        missing = sorted(wanted - existing)
        if not missing:
            return
''',
        '''        missing = sorted(wanted - existing)
        if not missing:
            self._record_legacy_cycles(columns)
            return
''',
    )

# ---- #625 a / b ---------------------------------------------------------------------------------------
sub(
    tasks,
    '''f"straggler {render_attributed(row_id)} alone composes {weight} rows, over the {row_cap}-row "
            f"transaction cap — the heal cannot pack it"''',
    '''f"straggler {render_attributed(row_id)} alone composes {weight} rows, over the {row_cap}-row "
            f"heal chunk bound — the heal cannot pack it"''',
)
sub(
    tasks,
    '''f"at most {cap_dependents} dependents) — refused, nothing changed. This is a pinned KNOWN "
            f"BOUND (58 F-1); file it with lore_findings."''',
    '''f"at most {cap_dependents} dependents) — refused, nothing changed. A hub somewhat below that "
            f"bound may instead time out and commit nothing (finding #628)."''',
)

# ---- §12.7 F5 + #130(a) -------------------------------------------------------------------------------
sub(
    server,
    '''f"blocker can never resolve, so this claim can never win: block on the "
                f"successor instead"''',
    '''f"blocker can never resolve: block on the "
                f"successor instead"''',
)
sub(server, "so the CAS counts it forever and this claim can NEVER win.", "so the CAS counts it until the next boot heal re-anchors it.")
sub(
    server,
    '''"of 'done' additionally requires 'summary'). For 'query', an "
                    "optional exact-status filter. Omit otherwise."''',
    '''"of 'done' additionally requires 'summary'). For 'query', an "
                    "optional exact-status filter; superseded rows are excluded from every "
                    "status and blocked filter. Omit otherwise."''',
)
print(f"patched {variant}")
```

### `tools/wrong_delta.py`
```python
#!/usr/bin/env python3
"""Wrong builds as ONE delta each on top of the REFERENCE (ref_patch.py REF already applied).

Usage: wrong_delta.py <copy-root> <BUILD>. Every edit asserts its anchor matched exactly once.
"""
import sys
from pathlib import Path

root = Path(sys.argv[1]); build = sys.argv[2]
tasks = root / "loremaster/loremaster/tasks.py"
server = root / "loremaster/loremaster/server.py"


def sub(path, old, new):
    text = path.read_text(); n = text.count(old)
    assert n == 1, f"{build}: {path.name}: anchor matched {n}x: {old[:90]!r}"
    path.write_text(text.replace(old, new))


RET = "        return [entry for entry in built if entry[0] not in skipped]\n"
LOOP_FIND = "            cycle = first_cycle_through_minted(view, pending, set(pending))\n"
WARN_START = "                logger.warning(\n                    _HEAL_WOULD_CYCLE_EVENT,\n"

if build == "W2_WARN_WRITE":          # check, record, write anyway
    sub(tasks, RET, "        return built\n")
elif build == "W3_RAISE":             # boot denial
    sub(tasks, "            on_cycle = [row for row in pending if row in cycle]\n",
        "            raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)\n"
        "            on_cycle = [row for row in pending if row in cycle]\n")
elif build == "W4_SILENT":            # skip, no record
    sub(tasks, WARN_START, "                (lambda *a, **k: None)(\n                    _HEAL_WOULD_CYCLE_EVENT,\n")
elif build == "W5_PARTIAL":           # move every superseded blocker whose head is NOT on the cycle
    sub(tasks, "        built = await self._skip_cycle_closing_rows(built)\n",
        "        self._w5 = (successor, heads, existing, at)\n"
        "        built = await self._skip_cycle_closing_rows(built)\n")
    sub(tasks, RET,
        "        kept = [entry for entry in built if entry[0] not in skipped]\n"
        "        succ, heads, existing, at = self._w5\n"
        "        for entry in built:\n"
        "            if entry[0] in skipped:\n"
        "                last = self._w5_cycle[entry[0]]\n"
        "                sub_succ = {o: s for o, s in succ.items() if heads[o][0] not in last}\n"
        "                if any(b in sub_succ for b in entry[6]):\n"
        "                    pad = [{'id': f'w5pad{i}', 'blocked_by': []} for i in range(500)]\n"
        "                    kept.append(self._plan_heal_rows(pad + [{'id': entry[0], 'blocked_by': entry[6]}],"
        " sub_succ, heads, existing, at)[-1])\n"
        "        return kept\n")
    sub(tasks, "                skipped.add(row)\n",
        "                skipped.add(row)\n"
        "                self.__dict__.setdefault('_w5_cycle', {})[row] = set(cycle)\n")
elif build == "W6_ROW_BY_ROW":
    sub(tasks, LOOP_FIND,
        "            cycle = None\n"
        "            for one in list(pending):\n"
        "                cycle = first_cycle_through_minted(view, {one: pending[one]}, {one})\n"
        "                if cycle is not None:\n"
        "                    break\n")
elif build == "W7_MINTED_HEADS":      # am-3 §4's choice copied: only the successors count as minted
    sub(tasks, LOOP_FIND,
        "            cycle = first_cycle_through_minted(view, pending,"
        " {b for r in pending for b in pending[r] if b not in stored_column[r]})\n")
elif build == "W13_COUNTED":
    sub(tasks, RET, "        self._w13 = len(skipped)\n" + RET)
    sub(tasks, "        if healed:\n            logger.info(\n                _HEAL_EVENT,",
        "        healed += getattr(self, '_w13', 0)\n        if healed:\n            logger.info(\n                _HEAL_EVENT,")
elif build == "W14_STAMP":            # skipped row gets updated_at touched
    sub(tasks, RET,
        "        for row in skipped:\n"
        "            await self._query(f\"UPDATE type::record('{TASK_TABLE}', $w14) SET {_COL_UPDATED_AT} = time::now()\","
        " {'w14': row})\n" + RET)
elif build == "W15_EDGE_DELETE":      # skipped row still runs its edge DELETE fragment
    sub(tasks, RET,
        "        for entry in built:\n"
        "            if entry[0] in skipped:\n"
        "                await self._apply([entry[1][0]])\n" + RET)
elif build == "W16_OVERSKIP":         # any cycle => skip every pending row
    sub(tasks, "            on_cycle = [row for row in pending if row in cycle]\n",
        "            on_cycle = list(pending)\n")
elif build == "W17_NO_STORED_GRAPH":
    sub(tasks, "        graph: dict[str, list[str]] = dict(await self._bounded_dependency_graph(seeds))\n",
        "        graph: dict[str, list[str]] = {}\n")
elif build == "W18_OLD_SEEDS":
    sub(tasks, "        seeds = {blocker for blockers in pending.values() for blocker in blockers}\n        graph: dict[str, list[str]] = dict(",
        "        seeds = {b for olds in olds_of.values() for b in olds}\n        graph: dict[str, list[str]] = dict(")
elif build == "W21_NO_RESTORE":       # a skipped row keeps its REWRITTEN column in the graph view
    sub(tasks, "            view = {**graph, **{row: stored_column[row] for row in skipped}}\n",
        "            view = {**graph, **{row: self._w21[row] for row in skipped}}\n")
    sub(tasks, "                skipped.add(row)\n",
        "                self.__dict__.setdefault('_w21', {})[row] = pending[row]\n                skipped.add(row)\n")
elif build == "W25_OLD_EVENT":
    sub(tasks, WARN_START, "                logger.warning(\n                    _HEAL_CYCLE_EVENT,\n")
elif build == "W26_PER_CHUNK":        # ONE graph read, but the predicate runs per chunk (other rows at stored column)
    sub(tasks, "        built = await self._skip_cycle_closing_rows(built)\n", "")
    sub(tasks, "        chunks = self._pack_heal_chunks(built)\n",
        "        chunks = self._pack_heal_chunks(built)\n"
        "        self._w26_graph = dict(await self._bounded_dependency_graph({b for e in built for b in e[4]})) if built else {}\n")
    sub(tasks, "            fragments = [f for entry in chunk for f in entry[1]]\n",
        "            chunk = await self._skip_cycle_closing_rows(list(chunk))\n"
        "            if not chunk:\n                continue\n"
        "            fragments = [f for entry in chunk for f in entry[1]]\n")
    sub(tasks, "        graph: dict[str, list[str]] = dict(await self._bounded_dependency_graph(seeds))\n",
        "        graph: dict[str, list[str]] = dict(self._w26_graph)\n")
elif build == "W30_MEMO":             # WARNING de-duplicated per process
    sub(tasks, WARN_START,
        "                if (self._database, row) in _W30_SEEN:\n                    skipped.add(row); del pending[row]; continue\n"
        "                _W30_SEEN.add((self._database, row))\n" + WARN_START)
    sub(tasks, '_HEAL_WOULD_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n',
        '_HEAL_WOULD_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n_W30_SEEN: set = set()\n')
elif build == "W11_ONE_PER_CYCLE":
    sub(tasks, "            for row in on_cycle:\n                logger.warning(\n",
        "            for row in on_cycle:\n                if row != on_cycle[0]:\n"
        "                    skipped.add(row); del pending[row]; continue\n                logger.warning(\n")
elif build == "W12_NO_CYCLE_EXTRA":
    sub(tasks, '                        "cycle": " -> ".join(cycle),\n', "")
elif build == "W12b_BLOCKERS_ALL":    # blocker_ids = the row's whole stored column, not the superseded ones
    sub(tasks, '                        "blocker_ids": olds_of[row],\n', '                        "blocker_ids": stored_column[row],\n')
elif build == "W20_LEGACY_MEMO":      # legacy loops recorded once per process
    sub(tasks, "        if not missing:\n            self._record_legacy_cycles(columns)\n            return\n",
        "        if not missing:\n            if self._database not in _W20_SEEN:\n"
        "                _W20_SEEN.add(self._database)\n                self._record_legacy_cycles(columns)\n            return\n")
    sub(tasks, '_HEAL_WOULD_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n',
        '_HEAL_WOULD_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n_W20_SEEN: set = set()\n')
elif build == "W8_OB3":
    sub(tasks, 'statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],\n                params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id},',
        'statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec AND out INSIDE $ssx_deps"],\n'
        '                params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id,'
        ' "ssx_deps": [RecordID(TASK_TABLE, d) for d in dependents]},')
elif build == "W8b_BOTH_DIRECTIONS":
    sub(tasks, 'statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],',
        'statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec OR out = $ssx_old_rec"],')
elif build == "W31_F5_OLD":
    sub(server, 'f"blocker can never resolve: block on the "', 'f"blocker can never resolve, so this claim can never win: block on the "')
elif build == "W34_625a_HARDCODE":
    sub(tasks, 'over the {row_cap}-row "\n            f"heal chunk bound', 'over the 10000-row "\n            f"heal chunk bound')
elif build == "W34b_625a_HARDCAP":
    sub(tasks, 'over the {row_cap}-row "\n            f"heal chunk bound', 'over the {_txn_module.TXN_ROW_HARD_CAP}-row "\n            f"heal chunk bound')
elif build == "W35_625b_KEEP_FILE":
    sub(tasks, '(finding #628)."', '(finding #628); file it with lore_findings."')
elif build == "W35b_625b_NO_FINDING":
    sub(tasks, ' A hub somewhat below that "\n            f"bound may instead time out and commit nothing (finding #628)."', '"\n            f""')
elif build == "W33_130a_OLD":
    sub(server, '"optional exact-status filter; superseded rows are excluded from every "\n                    "status and blocked filter. Omit otherwise."',
        '"optional exact-status filter. Omit otherwise."')
elif build == "REF2_SCC":             # NOT a wrong build: a SOUND predicate (SCC membership), to price the fix
    sub(tasks, """    work: dict[str, set[str]] = {node: set(refs) for node, refs in graph.items()}
    for task_id, blockers in pending.items():
        work[task_id] = set(blockers)
    while True:
        cycle = find_blocked_by_cycle(work)
        if cycle is None:
            return None
        if minted.intersection(cycle):
            return cycle
        if not _drop_one_cycle_edge(work, cycle):
            return None
""", """    work: dict[str, set[str]] = {node: set(refs) for node, refs in graph.items()}
    for task_id, blockers in pending.items():
        work[task_id] = set(blockers)
    digraph = networkx.DiGraph()
    for node, refs in work.items():
        digraph.add_node(node)
        for ref in refs:
            digraph.add_edge(node, ref)
    for component in sorted(networkx.strongly_connected_components(digraph), key=sorted):
        hits = sorted(minted & component)
        if not hits:
            continue
        for start in hits:
            if len(component) == 1 and not digraph.has_edge(start, start):
                continue
            inner = digraph.subgraph(component)
            best: list[str] | None = None
            for blocker in sorted(inner.successors(start)):
                path = [start, *networkx.shortest_path(inner, blocker, start)]
                if best is None or len(path) < len(best):
                    best = path
            if best is not None:
                return best
    return None
""")
elif build == "W45_SINGLE_PASS":      # ask the predicate ONCE: skip that cycle's rows, write the rest
    sub(tasks, "                skipped.add(row)\n                del pending[row]\n",
        "                skipped.add(row)\n                del pending[row]\n            break\n")
elif build == "W46_DOUBLE_RECORD":    # record legacy loops at the top AND in the missing-edge branch
    sub(tasks, "        missing = sorted(wanted - existing)\n        if not missing:\n            self._record_legacy_cycles(columns)\n            return\n",
        "        missing = sorted(wanted - existing)\n        self._record_legacy_cycles(columns)\n        if not missing:\n            return\n")
else:
    raise SystemExit(f"unknown build {build}")
print(f"delta {build} applied")
```

### `tools/mk.sh`
```bash
#!/usr/bin/env bash
# mk.sh <name> <BUILD> — scratch copy at 25cfd16 + reference + one wrong-build delta (or a ref_patch variant).
set -euo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2bfd474a-f66f-4068-a4bd-60e2a1cd530b/scratchpad
name="$1"; build="$2"; dest="$S/wb/$name"
mkdir -p "$S/wb"
cd /home/ejprice/PycharmProjects/lore
./scripts/scratch_copy.sh --force "$dest" > "$S/logs/mk_$name.log" 2>&1 || ./scripts/scratch_copy.sh "$dest" > "$S/logs/mk_$name.log" 2>&1
git -C "$dest" checkout 25cfd16 -- .
rm -f "$dest"/REPORT-adversary-58-r5.md "$dest"/REPORT-adversary-58-r53.md "$dest"/REPORT-builder-58-1.md "$dest"/REPORT-contract-58-r53.md
case "$build" in
  NOCHECK|EARLY_RETURN|PRED_NONE) python3 "$S/tools/ref_patch.py" "$dest" "$build" ;;
  HEAD) : ;;
  REF) python3 "$S/tools/ref_patch.py" "$dest" REF ;;
  *) python3 "$S/tools/ref_patch.py" "$dest" REF && python3 "$S/tools/wrong_delta.py" "$dest" "$build" ;;
esac
cd "$dest" && uv run python -c "import loremaster.tasks, loremaster.server, loremaster; assert loremaster.__file__.startswith('$dest'), loremaster.__file__; print('OK', '$name', loremaster.__file__)"
```

### `tools/run.sh`
```bash
#!/usr/bin/env bash
# run.sh <copy> <log> <N-workers> <selection...> — capped, timed pytest in a scratch copy, receipt-headed log.
# GUARD (#620): refuses an empty selection (pytest would widen to the whole suite) and any selection
# element that is not an existing file or a file::node id under the copy.
set -uo pipefail
copy="$1"; log="$2"; workers="$3"; shift 3
if [ "$#" -eq 0 ]; then echo "run.sh: REFUSED — empty selection (#620)" >&2; exit 64; fi
for sel in "$@"; do
  f="${sel%%::*}"
  if [ -z "$sel" ] || [ ! -f "$copy/$f" ]; then echo "run.sh: REFUSED — selection '$sel' is not a file in $copy (#620)" >&2; exit 64; fi
done
{
  ~/.claude/orchestration/tree_id.sh "$copy"
  cd "$copy" && uv run python -c 'import loremaster; print("loremaster.__file__=" + loremaster.__file__)'
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    uv run pytest -q -p no:cacheprovider -n "$workers" --timeout=300 -rf "$@"
  echo "EXIT=$?"
} > "$log" 2>&1
tail -3 "$log"
```

### `tools/wb_run.py`
```python
#!/usr/bin/env python3
"""wb_run.py <copy> <log> <workers> <declared-red-ids-file> <selection...>

Runs the (guarded, capped) selection via run.sh against a pre-built wrong build, parses the RED set with
mutation_proof.parse_red_node_ids (pytest's short summary only), and diffs it BOTH WAYS against the set
declared in <declared-red-ids-file> BEFORE the run. Exit 0 iff observed == declared. Prints the verdict line.
"""
import subprocess, sys
from pathlib import Path
sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/scripts")
from mutation_proof import parse_red_node_ids  # noqa: E402

copy, log, workers, declared_file, *selection = sys.argv[1:]
declared = {l.strip() for l in Path(declared_file).read_text().splitlines() if l.strip()}
tools = Path(__file__).parent
rc = subprocess.run([str(tools / "run.sh"), copy, log, workers, *selection]).returncode
text = Path(log).read_text()
if rc == 64 or "EXIT=" not in text:
    print(f"RUN REFUSED/INCOMPLETE rc={rc}"); sys.exit(2)
observed = parse_red_node_ids(text)
count = [l for l in text.splitlines() if (" passed" in l or " failed" in l) and " in " in l]
unexpected, still_green = sorted(observed - declared), sorted(declared - observed)
name = Path(copy).name
print(f"{name}: declared={len(declared)} observed={len(observed)} unexpected={len(unexpected)} "
      f"declared-but-green={len(still_green)} | {count[-1].strip() if count else 'NO COUNT LINE'}")
for u in unexpected: print(f"  UNEXPECTED RED {u}")
for g in still_green: print(f"  DECLARED BUT GREEN {g}")
sys.exit(0 if not unexpected and not still_green else 1)
```

### `tools/stepover_probe.py`
```python
"""Is the step-over (find_blocked_by_cycle + _drop_one_cycle_edge) SOUND when a legacy loop shares an EDGE with
the minted row's cycle? Pure in-memory probe against the reference's first_cycle_through_minted."""
import itertools
from loremaster.tasks import first_cycle_through_minted, find_blocked_by_cycle

def on_cycle(graph, node):
    # ground truth: node lies on a cycle iff it reaches itself
    seen, stack = set(), list(graph.get(node, ()))
    while stack:
        n = stack.pop()
        if n == node: return True
        if n in seen: continue
        seen.add(n); stack.extend(graph.get(n, ()))
    return False

misses = []
names = ["a", "b", "h", "d", "z", "y"]
# legacy loop L1 <-> L2; heal row D rewritten to [H]; H blocked_by [L1]; L2 blocked_by [D] (and [L1])
for l1, l2, h, d in itertools.permutations(names, 4):
    stored = {l1: [l2], l2: [l1, d], h: [l1], d: ["x"]}
    pending = {d: [h]}
    view = {**stored, **pending}
    truth = on_cycle(view, d)
    got = first_cycle_through_minted(stored, pending, {d})
    if truth and got is None:
        misses.append((l1, l2, h, d, find_blocked_by_cycle(view)))
print(f"cases={len(list(itertools.permutations(names, 4)))} misses={len(misses)}")
for m in misses[:5]: print("MISS", m)
# positive control: no legacy loop -> found
print("control", first_cycle_through_minted({"h": ["a"], "a": ["d"], "d": ["x"]}, {"d": ["h"]}, {"d"}))
```

### `tools/stepover_probe2.py`
```python
"""Supersede shape: legacy loop L1<->L2, successor S blocked_by [L1], rewired dependent R -> S, L2 blocked_by [L1, R].
minted={S} (am-3 §4). For which S ids does the shared predicate miss the cycle S -> L1 -> L2 -> R -> S?"""
import uuid
from loremaster.tasks import first_cycle_through_minted
L1, L2, R = "00fwl1".ljust(32, "0"), "00fwl2".ljust(32, "0"), "00fwr".ljust(32, "0")
stored = {L1: [L2], L2: [L1, R], R: ["x"]}
miss = 0; n = 2000
for _ in range(n):
    s = uuid.uuid4().hex
    pending = {s: [L1], R: [s]}
    if first_cycle_through_minted(stored, pending, {s}) is None:
        miss += 1
print(f"supersede shape: {miss}/{n} random successor ids MISS the cycle")
```

### `tools/restore_probe.py`
```python
"""Does restoring a skipped row's STORED column (am-17 §12.2) change any fate, and is the spec's fate order-independent?
World: D1 [X1->H1], H1 blocked_by [D1, D2]; D2 [X2->H2], H2 blocked_by [D1]."""
import itertools
from loremaster.tasks import first_cycle_through_minted

def heal(graph, pending0, stored, restore):
    pending, skipped, view_extra = dict(pending0), [], {}
    while pending:
        view = {**graph, **view_extra}
        cyc = first_cycle_through_minted(view, pending, set(pending))
        if cyc is None: break
        for r in [r for r in pending if r in cyc]:
            view_extra[r] = stored[r] if restore else pending[r]
            skipped.append(r); del pending[r]
    return sorted(skipped)

fates_ref, fates_w21, diff = {}, {}, 0
for d1, h1, d2, h2 in itertools.permutations("abcd"):
    graph = {h1: [d1, d2], h2: [d1], d1: ["x1"], d2: ["x2"]}
    pending = {d1: [h1], d2: [h2]}; stored = {d1: ["x1"], d2: ["x2"]}
    r, w = heal(graph, pending, stored, True), heal(graph, pending, stored, False)
    key = "both" if len(r) == 2 else "D1-only"
    fates_ref[key] = fates_ref.get(key, 0) + 1
    if r != w: diff += 1
print("reference fate by id order:", fates_ref, "| orders where no-restore differs:", diff, "of 24")
```

### `extra/test_adv_fw1_probes.py`
```python
"""adversary-58-fw1 probes (scratch only, never in the repo). Each names the wrong build / hole it targets."""
from __future__ import annotations

import logging

import pytest
from _reanchor_58_support import (
    HEAL_EVENT, all_columns, boot, column, create, edge_pairs, ledger58, raw_relate, raw_seed_row, supersede,
    updated_at_of,
)
from _surreal_harness import SurrealEnv
from loremaster.tasks import TaskCycleError, TaskLedger, find_blocked_by_cycle

__all__ = ["ledger58"]
WOULD = "task.backfill.straggler_would_close_cycle"


def _id(tag: str) -> str:
    return tag.ljust(32, "0")[:32]


async def _seed(ledger, task_id, blocked_by, **kw):
    await raw_seed_row(ledger, task_id, blocked_by=blocked_by, **kw)
    return task_id


class TestE1HealCycleSharingAnEdgeWithALegacyLoop:
    @pytest.mark.parametrize("order", ["legacy_ids_sort_first", "control_dependent_sorts_first"])
    async def test_E1_heal_never_writes_a_cycle_that_shares_an_edge_with_a_legacy_loop(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, order: str
    ) -> None:
        """Legacy loop L1 <-> L2 (ids sort FIRST). X superseded by H (raw); H blocked_by [L1]; L2 blocked_by
        [L1, D]; D blocked_by [X]. Re-anchoring D writes D -> H -> L1 -> L2 -> D, which shares the edge
        L1 -> L2 with the legacy loop. P (am-17 §12.2): no row the heal wrote lies on a cycle."""
        ledger, env = ledger58
        if order == "legacy_ids_sort_first":
            l1, l2, h, x, d = _id("00e1a1"), _id("00e1b2"), _id("00e1h"), _id("00e1x"), _id("00e1d")
        else:
            l1, l2, h, x, d = _id("00e1l1"), _id("00e1l2"), _id("00e1h"), _id("00e1x"), _id("00e1d")
        await _seed(ledger, h, [])
        await _seed(ledger, x, [], superseded_by=h)
        await _seed(ledger, d, [x])
        await _seed(ledger, l1, [])
        await _seed(ledger, l2, [])
        from _reanchor_58_support import raw_force
        await raw_force(ledger, l1, blocked_by=[l2])
        await raw_force(ledger, l2, blocked_by=[l1, d])
        await raw_force(ledger, h, blocked_by=[l1])
        for blocker, blocked in ((x, d), (l2, l1), (l1, l2), (d, l2), (l1, h)):
            await raw_relate(ledger, blocker, blocked)
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await boot(env)
        cols = await all_columns(ledger)
        d_col = cols[d]
        # ground truth: is D on a cycle after the heal?
        seen, stack, on = set(), list(cols.get(d, ())), False
        while stack:
            n = stack.pop()
            if n == d:
                on = True; break
            if n in seen:
                continue
            seen.add(n); stack.extend(cols.get(n, ()))
        assert not on, f"the heal wrote D onto a cycle: D={d_col}, columns={cols}"
        assert d_col == [x] and any(r.getMessage() == WOULD for r in caplog.records), (d_col,)


class TestE2JointCycleAcrossAChunkBoundary:
    async def test_E2_leg_B_with_one_row_per_chunk(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Contract leg B's world, but the heal packs each row in its OWN chunk (the shape a store past the
        10 000-row chunk bound produces). P over the WHOLE pending set must still hold."""
        ledger, env = ledger58
        monkeypatch.setattr(
            TaskLedger, "_pack_heal_chunks", staticmethod(lambda built: [[entry] for entry in built])
        )
        from _reanchor_58_support import raw_force
        h1 = await create(ledger, "e2 H1"); h2 = await create(ledger, "e2 H2")
        x1, x2 = _id("e2x1"), _id("e2x2")
        await _seed(ledger, x1, [], superseded_by=h1)
        await _seed(ledger, x2, [], superseded_by=h2)
        d1 = await _seed(ledger, _id("e2d1"), [x1]); await raw_relate(ledger, x1, d1)
        d2 = await _seed(ledger, _id("e2d2"), [x2]); await raw_relate(ledger, x2, d2)
        await raw_force(ledger, h1, blocked_by=[d2]); await raw_relate(ledger, d2, h1)
        await raw_force(ledger, h2, blocked_by=[d1]); await raw_relate(ledger, d1, h2)
        await boot(env)
        assert find_blocked_by_cycle(await all_columns(ledger)) is None, (
            f"a joint cycle was written across a chunk boundary: {find_blocked_by_cycle(await all_columns(ledger))}"
        )


class TestE3LiveSupersedeCycleSharingAnEdgeWithALegacyLoop:
    @pytest.mark.parametrize("legacy_loop", [True, False], ids=["with_legacy_loop", "control_no_legacy_loop"])
    async def test_E3_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop(
        self, ledger58: tuple[TaskLedger, SurrealEnv], legacy_loop: bool
    ) -> None:
        """Legacy loop L1 <-> L2 (raw, ids sort first). X is a live task; R blocked_by [X]; L2 blocked_by [L1, R].
        supersede X with blocked_by=[L1]: R is re-anchored to S, closing S -> L1 -> L2 -> R -> S, which shares
        L1 -> L2 with the legacy loop. The live write path must refuse it (TaskCycleError)."""
        ledger, env = ledger58
        from _reanchor_58_support import raw_force
        x = await create(ledger, "e3 X")
        l1, l2, r = _id("00e3l1"), _id("00e3l2"), _id("00e3r")
        await _seed(ledger, r, [x]); await raw_relate(ledger, x, r)
        await _seed(ledger, l1, []); await _seed(ledger, l2, [])
        await raw_force(ledger, l1, blocked_by=[l2]); await raw_force(ledger, l2, blocked_by=[l1, r] if legacy_loop else [r])
        for blocker, blocked in ((l2, l1), (r, l2)) + (((l1, l2),) if legacy_loop else ()):
            await raw_relate(ledger, blocker, blocked)
        await boot(env)  # backfill + heal settle first (nothing to heal: X is not superseded)
        try:
            await supersede(ledger, x, blocked_by=[l1])
        except TaskCycleError:
            return
        cols = await all_columns(ledger)
        successor = (await ledger.get_task(x)).superseded_by
        seen, stack, on = set(), list(cols.get(successor, ())), False
        while stack:
            n = stack.pop()
            if n == successor:
                on = True; break
            if n in seen:
                continue
            seen.add(n); stack.extend(cols.get(n, ()))
        assert on, f"supersede succeeded and the successor is NOT on a cycle (probe world wrong): {cols}"
        cycle = find_blocked_by_cycle(cols)
        pytest.fail(f"the live supersede wrote a blocked_by cycle through its successor: store cycle {cycle}; "
                    f"R={await column(ledger, r)}")


class TestE4TwoIndependentCycles:
    async def test_E4_two_stragglers_each_closing_their_OWN_cycle_are_both_skipped(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        """D1 [X1->H1], H1 [D1]; D2 [X2->H2], H2 [D2]: two INDEPENDENT would-be cycles. The §12.2 loop must ask
        the predicate again after skipping the first (kills a single-pass loop)."""
        ledger, env = ledger58
        from _reanchor_58_support import raw_force
        h1 = await create(ledger, "e4 H1"); h2 = await create(ledger, "e4 H2")
        x1, x2 = _id("e4x1"), _id("e4x2")
        await _seed(ledger, x1, [], superseded_by=h1); await _seed(ledger, x2, [], superseded_by=h2)
        d1 = await _seed(ledger, _id("e4d1"), [x1]); await raw_relate(ledger, x1, d1)
        d2 = await _seed(ledger, _id("e4d2"), [x2]); await raw_relate(ledger, x2, d2)
        await raw_force(ledger, h1, blocked_by=[d1]); await raw_relate(ledger, d1, h1)
        await raw_force(ledger, h2, blocked_by=[d2]); await raw_relate(ledger, d2, h2)
        await boot(env)
        assert find_blocked_by_cycle(await all_columns(ledger)) is None, find_blocked_by_cycle(await all_columns(ledger))
        assert await column(ledger, d1) == [x1] and await column(ledger, d2) == [x2]
```

## lead_context_guard tmux probe (operator-requested via team-lead, 2026-11-10T10:13:19Z; not part of the grade)
Step 1 output, verbatim:
```
2026-11-10T10:13:19Z
CLAUDECODE=1
CLAUDE_CODE_ATTRIBUTION_PROJECT=
CLAUDE_CODE_BRIDGE_SESSION_ID=session_01Fn6LEvjCWxsx2ZpyNKJqNb
CLAUDE_CODE_CHILD_SESSION=1
CLAUDE_CODE_ENTRYPOINT=cli
CLAUDE_CODE_EXECPATH=/home/ejprice/.local/share/claude/versions/2.1.321
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
CLAUDE_CODE_MESSAGING_SOCKET=/run/user/1000/cc-socks/1845908.sock
CLAUDE_CODE_SESSION_ATTENDED=0
CLAUDE_CODE_SESSION_ID=2bfd474a-f66f-4068-a4bd-60e2a1cd530b
CLAUDE_CODE_TASK_LIST_ID=session-3df65e4b
CLAUDE_CODE_USER_DELEGATED_SESSION_ALLOWED_CHECK_MODELS=
CLAUDE_CODE_USER_DELEGATED_SESSION_DIRECT_API=
CLAUDE_EFFORT=high
CLAUDE_PID=1845908
```
Step 2: wrote /var/tmp/claude-1000/lead_guard_probe/adversary-58-fw1.py. Package-first message seen: YES. It came as PreToolUse additionalContext on the Write; first 80 chars: `package-first check (new implementation file). Before writing this: WHAT PACKAG`
Step 3: Packages considered: none needed — lead_context_guard tmux probe.
Guard note: the TeammateIdle guard refused the multi-line final answer the probe brief asked for (refusal 1 of 2), so the detail lives here.
