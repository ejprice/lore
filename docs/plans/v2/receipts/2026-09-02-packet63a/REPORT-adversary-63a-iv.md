# REPORT-adversary-63a-iv — CONTRACT ADVERSARY, packet 63 wave 63a-iv (Opus 4.8)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT SUFFICIENT** — no wrong build I constructed survives the 5-module contract.
  Two required follow-ups (below); neither is "a wrong build passes the contract."
- state: **done**
- **Graded:** 0ea337b (code+tests I ran) · HEAD-at-report: 7c9dc6a · DIFFERENT (1 ahead) —
  the ONLY delta 0ea337b→7c9dc6a is `docs/design/…retrofit-rulings.md` (§10.8 supersession +
  §10.9 wave-line, docs-only). NO production/test file moved, so the code+tests I graded are
  byte-identical at HEAD; my RED/GREEN + reference grades stand.
- **P1 headline — did any wrong build survive?** NO. Five wrong builds (owner-fold: no-op /
  single-axis / nonce over-fix; F5: new-unguarded-write / runtime-escape; F-B: pre-filter
  reinforce; audit-DDL: fold-removal) EACH reddened the pin that must catch it. See §P1.
- **Satisfiability receipt (C-DEF):** reference correct build in provenance-asserted scratch
  (`loremaster.__file__ = /tmp/adv63aiv_ref1/loremaster/loremaster/__init__.py`) → **24/24 GREEN**,
  ruff clean on all 4 touched prod files. §SAT.
- Packages considered: none new — the only mechanisms are stdlib (`uuid5`, `contextvars`,
  `contextlib`, `ast`); `contextvars.ContextVar`+`@contextmanager` is the exact write-guard
  primitive. No library would do it better; author's `bespoke`/stdlib choice is correct.
- Reuse ledger: none (adversary writes no production symbols; scratch reference discarded).
- **P1b QUANTIFIER TABLE:** §P1b — owner fold pinned ∀ BOTH owner axes (≥2 principals × ≥2 agents);
  single-axis fold + no-op + over-fix all caught.
- **P1c REACH TABLE:** §P1c — L1 (AST, DERIVED, grows-and-reds proven with a REAL new site),
  L2a (structural, derived-from-allowlist), L2b (RUNTIME, observes the EFFECT not a proxy —
  proven). Two NAMED BOUNDS recommended (F-2, F-3).
- **FINDINGS (none flips the verdict; F-1 is a required pre-build action):**
  - **F-1 (MEDIUM — §SAT under-enumeration):** the owner-fold signature change breaks
    `derive_memory_id` callers/oracles in **6 test files** beyond the ONE (`test_memory_backend`)
    the §SAT NOTE named — the P8d "every residual hit gets a file:line" law. Full worklist in §F-1.
  - **F-2 (LOW — pin the miss):** L1 AST scan misses a raw memory write whose table name is a
    runtime VARIABLE (not the `MEMORY_TABLE` constant / literal `'memory'`) — proven evasion.
    Defensible under the honest-idiom threat model, but NAME the bound + re-open trigger. §P1c.
  - **F-3 (LOW — note the bound):** L2b runtime coverage reaches only the 3 member-reachable seam
    paths; `_replay_record`/`_recreate_memory_table` have L2a-structural coverage ONLY. §P1c.
- decisions-needed: none for the verdict. F-1 worklist should be recorded for the builder before
  the GREEN wave (recommendation, not a blocker).
- receipt POINTERS: wrong builds → §P1; quantifier → §P1b; reach → §P1c; satisfiability → §SAT;
  corpse sweep → §F-1/§P6; RED honesty → §P7; author-claim verification → §P4.

---

## §P1 — WRONG BUILDS (highest-value probe). None survived.

All built in the provenance-asserted scratch `/tmp/adv63aiv_ref1` (`scratch_copy.sh`, #140-safe;
`loremaster.__file__` INSIDE the copy — printed each run). Edit → run → revert; reference restored
to 24/24 GREEN after every probe (final confirmation run at §SAT).

| # | wrong build | what it models | pin(s) that RED | verdict |
|---|---|---|---|---|
| A | `derive_memory_id` folds `owner_principal` only, drops `owner_agent` | single-axis fold | `test_a_sibling_agent_reremember…` (construction 2) + shape pin (`owner_agent not folded`) | CAUGHT; cross-principal + revive correctly still GREEN (principal folded) |
| B | fold `owner_pair` + a `time_ns()` NONCE | over-fix that breaks legit dedup | `TestSameAgentDedupIsPreserved` (dedup control) + shape determinism leg | CAUGHT — positive control is NON-vacuous |
| C | `derive_memory_id` owner kwargs default `""`, `remember` calls the 2-arg form | the NO-OP fix (helper folds, nobody uses it) | ALL 3 seizure pins RED; shape pin GREEN | CAUGHT — the seizure pins force `remember` to USE the fold |
| D | new `_touch_note` with raw `UPDATE type::record('{MEMORY_TABLE}',…)`, unguarded/unallowlisted | HONEST new memory write (the enumerate-the-forbidden recurrence) | L1 `test_the_derived_raw_mutation_set_is…known_set` + `…is_in_the_allowlist` (orphan) | CAUGHT — deny-by-default, reach genuinely DERIVED |
| E | `remember` CALLS `write_guard` but the `_apply` write ESCAPES the `with` block | structural-green / runtime-hole (proxy vs effect) | L2b `test_every_observed_memory_mutation…` (`[('execute_transaction','UPSERT')]` label=None) — while L2a STAYS GREEN | CAUGHT by L2b (effect), MISSED by L2a (proxy) — the two layers are complementary |
| F | `_reinforce` SET grows `, scope='seized'` | F-B (ii) statement drift onto a governed column | `TestReinforceStatementTouchesOnlyImportance` (`assigns a GOVERNED column ['scope']`) | CAUGHT — captures the RESOLVED runtime statement (non-vacuous) |
| G | `recall` also reinforces a fresh UNFILTERED (pre-`read_filter`) candidate set | F-B (i) bump-set ≢ served-set | `test_a_recall_never_bumps_a_row_the_caller_cannot_read` (`0.5 -> 0.55`) — positive control stays GREEN | CAUGHT — closes the F-B(i) mutation the contract report left "not run" |
| H | remove `_audit_statements()` from `generate_ddl` | item-5 regression | both audit-DDL composition-root pins RED (audit table absent) | CAUGHT — genuine regression guards (NOT re-opening #440) |

Command receipts pasted in §PROBE-LOG.

---

## §P1b — QUANTIFIER TABLE (owner fold, design §10.9-B)

The invariant "a cross-owner content collision is UNREPRESENTABLE" is pinned ∀ over BOTH owner
components, forced with ≥2 distinct principals AND ≥2 distinct agents.

| invariant | ∀-over-inputs vs guarded | receipt |
|---|---|---|
| different `owner_principal` ⇒ distinct id | ∀ (cross-principal, forced with alice≠bob) | seizure-1 + revive RED at HEAD & no-op (C); shape pin `principal_b` leg |
| different `owner_agent` ⇒ distinct id | ∀ (intra-principal siblings, forced with ag_a1≠ag_a2 / worker_1≠worker_2) | seizure-2 RED at HEAD & wrong-build A; shape pin `agent_2` leg |
| same (principal, agent, text, refs) ⇒ SAME id (dedup preserved) | ∀ (positive control) | `TestSameAgentDedupIsPreserved` GREEN on correct build, RED on nonce over-fix (B) |
| text & refs_stamp still vary the id (old dedup basis survives) | ∀ | shape pin `text dropped` / `refs_stamp dropped` legs |
| `remember` actually FOLDS the resolved subject's pair (not just the helper) | ∀ (end-to-end) | all 3 seizure pins RED on the no-op fix (C) — the strongest leg |

The THREE promoted seizure constructions EACH go RED on a build without the owner fold: verified
at HEAD (`f77ac24`/0ea337b, no fold at all → 3 RED) AND on the no-op fix C (helper folds but
`remember` doesn't → 3 RED). No fixture monoculture/arithmetic accident: the fixture uses 2
principals (alice/bob) × 2 agents (ag_a1/ag_a2, worker_1/worker_2), and each axis is asserted
INDEPENDENTLY (principal fixed while agent varies, and vice-versa), so a one-axis fold cannot pass.

---

## §P1c — REACH TABLE (F5, design §10.9-A)

Legs run: **EMPIRICAL** for all three layers (the guard is in-tree; I built wrong versions).

| instrument | reach DERIVED vs hand-list | coverage a CHECKED variable? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|
| **L1** AST raw-mutation scan (`governed_table_raw_mutation_sites`) | DERIVED (statement-shape targeting `MEMORY_TABLE`/literal `memory`) — proven grows-and-reds with a REAL new site (wrong-build D), not just the synthetic | YES — exact-set pin `derived == _KNOWN_RAW_SITES` + anti-vacuity `assert derived`; deny-by-default (orphan ⇒ RED) | effect (source of record) | shared substrate; 64 parametrises | DERIVED, **with an unnamed bound → F-2** |
| **L2a** per-frame structural (`function_calls_write_guard`) | DERIVED from the allowlist (`{frame for entry in write_allowlist for frame in entry.frames}`) — grows with a new entry | YES — every derived frame must call `write_guard`; RED on any unwired frame (wrong-build "unwire `_recreate`" → RED) | PROXY by design (checks the frame CALLS write_guard, not that the write is inside it) — this is L2a's role; L2b covers the effect | structural | SAFE (its proxy nature is covered by L2b) |
| **L2b** runtime seam (`observe_governed_table_writes` + `active_write_guard`) | seam patch over resolved statements; coverage anti-vacuity `assert observed` + `{execute_transaction, run_query, execute_read_transaction} ⊆ seams` | YES for the 3 member-reachable seam paths; deny-by-default (label=None ⇒ RED) | **EFFECT, proven** — wrong-build E (write escapes the `with`) reds L2b while L2a stays green; observes at the real mutation point | runtime | EFFECT-observed, **coverage bound → F-3** |

**F-2 (L1 reach bound, LOW — pin the miss).** A raw memory write whose table name is a runtime
VARIABLE evades L1. Reproduced (wrong-build, both L1 pins GREEN):
```python
async def _touch_note(self, memory_id):
    tbl = self._which_table()                     # returns "memory"
    await self._query(f"UPDATE type::record('{tbl}', $id) SET valid_from = time::now()", {"id": memory_id})
def _which_table(self): return "memory"
```
`_statement_shape` renders `{tbl}` as `{tbl}`, `_targets_table` matches neither `\bmemory\b` nor the
`MEMORY_TABLE` const-hint → the site is never derived → deny-by-default never fires. Faithful to the
ruling (§10.9-A scopes L1 to "statement shape targets MEMORY_TABLE") and non-idiomatic for the honest
engineer (all 3 real sites use the `MEMORY_TABLE` constant), so I do NOT recommend widening the scan.
Per "WHEN YOU CANNOT CLOSE A HOLE, PIN IT": add a bound note in `_governed_contract`/the L1 docstring
+ re-open trigger ("any production write that constructs the memory table name dynamically").

**F-3 (L2b coverage bound, LOW — note it).** The L2b battery exercises remember / recall→`_reinforce`
/ invalidate→`guarded_write` = 3 seam paths. The other two allowlisted frames — `_replay_record` and
`_recreate_memory_table` — are NEVER exercised by the battery, so they carry L2a (structural) coverage
ONLY. Reproduced: unwiring `_recreate_memory_table` reds L2a but leaves L2b GREEN (never observed). A
runtime-escape (wrong-build-E shape) inside those two frames would pass BOTH layers. Defensible — both
are boot/admin/replay paths (not member verbs), and the ruling right-sizes ("a production-mode assert
is OPTIONAL"). The member-reachable writes all carry BOTH structural + runtime coverage. Recommend a
one-line note that L2b's runtime reach is the member-verb seam paths, L2a is the structural net for the
rest.

No hidden-constant reach that ships a blind spot the builder can't see: the reaches are DERIVED and
coverage is checked. The two bounds above are inherent to the ruling's chosen mechanism (static AST +
member-verb battery) and are recommended to be NAMED, not closed.

---

## §SAT — satisfiability receipt (C-DEF)

Reference correct build (owner-fold in `derive_memory_id` + `remember`; `write_guard`/
`active_write_guard` via stdlib `contextvars` wired into `guarded_write` + 4 local frames
[remember, `_replay_record`, `_reinforce`, `_recreate_memory_table`]; stale-prose fixes at
backend.py:14/97 + `derive_memory_id` docstring + the `lore_remember` description):

- `FINAL PROVENANCE loremaster.__file__ = /tmp/adv63aiv_ref1/loremaster/loremaster/__init__.py`
- 5 modules against the reference: **`24 passed in 11.13s`** (0 failed).
- `uv run ruff check` on the 4 touched prod files (governed.py, backend.py, local.py, server.py):
  **All checks passed!** (the C-DEF "after cleanups" leg — my stdlib mechanism reflows clean).

The harder leg confirmed the author's flag: the reference build breaks the `test_memory_backend`
parity suite (8 RED, TypeError on the widened signature) AND the wider caller/oracle set — see §F-1.

---

## §F-1 — the §SAT under-enumerates the collateral corpse set (MEDIUM)

The contract report §SAT NOTE flags "the old-signature callers (**test_memory_backend parity
suite**) must be updated by the builder." That is ONE of **SEVEN** affected test files. The
owner-fold signature change (`derive_memory_id` gains 2 required kwargs) breaks every 2-arg caller
AND every independent oracle that reconstructs the retired `memory:{text}:{refs_stamp}` scheme. On
the reference build I measured **9 failures** across five of the unflagged files (with a scoped
`-k`) plus the 8 parity failures — the true count is larger once the fake diverges. This is the P8d
"every residual hit gets a file:line — 'all remaining are X' is banned" law applied to the builder's
worklist. The builder needs the COMPLETE list or it hits surprises the §SAT did not name; the
cold-audit then can't tell an expected corpse-fix from a regression.

**Complete worklist (derived by grep at 0ea337b) — the builder must update ALL of these:**
- `test_memory_backend.py` — **FLAGGED.** Callers 1514/1520/1530/1536/1544/1547/1558/1560/1564/1578 +
  the `expected_memory_id` ORACLE (def:261) used at 617/619/622/630/1284/1320/1573/1579/1766/1802/1845.
- `test_mcp_server.py` — **UNFLAGGED.** `derive_memory_id` callers 6747/6761/6774/6782/8541/8555.
- `test_schema_rebuild.py` — **UNFLAGGED.** caller 3014.
- `test_memory_cutover.py` — **UNFLAGGED.** caller 250.
- `test_memory_ledger.py` — **UNFLAGGED.** `expected_memory_id` ORACLE (def:61) used 189/199/238 +
  docstrings 37/64 that teach `memory:{text}:{refs_stamp}`.
- `test_search.py` — **UNFLAGGED.** line 467 reconstructs the OLD scheme INLINE
  (`uuid5(NAMESPACE_URL, f"memory:{text}:{','.join(chunk_keys)}")`).
- `_memory_fakes.py` — **UNFLAGGED.** `FakeMemoryBackend.remember` line 308 calls the 2-arg form.
  ⚠ DIVERGENCE (P5): the fake must fold the owner too, or it silently mints OLD-scheme ids and any
  test using the fake for dedup tests the retired scheme against the real backend's new one.

This is NOT a contract-pin gap (the 5 modules discriminate — §P1) and does NOT flip the verdict; it
is an incomplete satisfiability receipt + removed-behaviour worklist. Recommendation: record this
worklist (this section is citable) for the builder before the GREEN wave.

---

## §P4 — author-claim verification (reproduced, not relayed)
- "12 RED / 12 GREEN at HEAD" → **reproduced: `12 failed, 12 passed in 10.82s`** (5 modules, TEST store).
- "24/24 GREEN against a provenance-asserted reference" → **reproduced independently: `24 passed`**
  (my own reference build, not the author's tree).
- "ruff clean after the cleanups it demands" → **reproduced** (All checks passed on the 4 prod files).
- "F-B (ii) captures the RESOLVED statement (a source regex is vacuous)" → **reproduced** (wrong-build F
  reds on the resolved `scope`; the source token is `{_COL_SCOPE}`, which a source regex would miss).
- "item-5 pins are GREEN regression guards, not RED-until-built" → **reproduced** (2 GREEN at HEAD;
  RED on `_audit_statements` removal). Finding #440's refutation of §10.8 is sound; I did NOT re-open it.

## §P5 — can the test doubles fail?
- The L2b seam instrument (`observe_governed_table_writes`) is not a "fake" — it observes the real
  backend; proven to FIRE and RED (wrong-builds D/E). `_capture_reinforce_statements`' fake `_query`
  proven to discriminate (wrong-build F). `FakeRegistry` (in the substrate) is not on the 63a-iv
  pins' path. The one genuine fake-divergence risk is `_memory_fakes.FakeMemoryBackend` — filed in §F-1.

## §P6 / P6b — corpse & orphaned-virtue sweep
- **Corpse sweep:** the full old-scheme corpse population is §F-1 (7 files). The contract's own
  prose-currency sweep (`_MEMORY_MODULES = backend/ledger/local`) scans PRODUCTION only; test-side
  oracles/docstrings teaching the retired scheme are the builder's worklist (correct — not served prose).
- **P6b (owner fold REPLACES the id derivation):** removed behaviour = "global content-address dedup"
  → adjudicated old-bug-not-re-pinned (design §10.9-B); the PRESERVED virtue = deterministic
  reproducible id, kept by the shape pin's determinism leg + the same-agent-dedup control. Ledger
  replay's virtue ("re-mints in place") is UNAFFECTED — verified `_replay_record` uses the STORED
  `record.memory_id`, never a re-derivation. No orphaned virtue found.

## §P7 — RED honesty
12 REDs at HEAD, ALL for the right reason (behavioural, not import/path/fixture): 3 seizure pins
(ids collide → row seized), 1 shape pin (`TypeError: unexpected keyword argument`), 4 stale-prose
(retired literal/claim present at backend.py:14/97/177), 2 L2a (`write_guard` unwired), 2 L2b
(`active_write_guard` unbuilt / label=None). Counts carry a passed-COUNT in the tail (no "no tests
ran" behind a pipe). Reproduced verbatim in §PROBE-LOG.

---

## §RESIDUALS — every item an individual verdict
- L1 exact-set pin `derived == _KNOWN_RAW_SITES`: **SAFE** — anti-vacuity `assert derived` guards
  emptiness; grows-and-reds proven with a REAL site (D), not hardcoded.
- L1 pin-existence (`_defined_test_names`): **SAFE** — AST-derived over `test_*.py`; all 3 allowlist
  pins resolve (`test_a_non_owner_reremember…`, `test_the_reinforce_update_sets_only_the_importance_column`,
  `test_recreate_memory_table_is_reachable_only_from_rebuild_embeddings`).
- L2b seam patch: patches IMPORTED names in local/governed modules — **SAFE**, observes all 3 seam
  paths live at HEAD (verified: it recorded the mutations, the RED is only the None context).
- `guarded_write` audit CREATE targets `audit` not `memory` → correctly ignored by
  `_mutation_verb_for_table` — **SAFE** (verified in source).
- audit-DDL first pin reds via `NotFoundError`/`"SCHEMAFULL" not in "None"` when the table is fully
  removed (vs the SCHEMAFULL-assertion path for a schemaless table) — **SAFE**, still a RED for the
  right class; the discriminating CREATE pin is the sharper leg.
- F-2 (L1 dynamic-table bound): **OPEN recommendation** — pin the miss + re-open trigger.
- F-3 (L2b un-exercised frames `_replay_record`/`_recreate_memory_table`): **OPEN recommendation** —
  note the bound.
- F-1 (collateral corpse worklist): **OPEN, required before build** — record the 7-file worklist.
- RES-ATOM (§10.9-D) / RES-A1 `scope=` bound: correctly NOT pinned here (63b owner, finding #441) — **out of wave, SAFE.**

---

## §PROBE-LOG — commands + real output (instruments are the deliverable)

Scratch: `./scripts/scratch_copy.sh /tmp/adv63aiv_ref1` → provenance asserted
(`loremaster -> /tmp/adv63aiv_ref1/loremaster/loremaster/__init__.py`). All wrong builds were
edit→run→revert on this copy; the reference restored to 24/24 after each (§SAT final run).

- **P7 @ HEAD (real tree, read-only pytest):** `12 failed, 12 passed in 10.82s`.
- **SAT reference:** `24 passed in 12.38s` (first) / `24 passed in 11.13s` (final, post-revert).
- **A** single-axis: `2 failed, 3 passed` — sibling-seizure + shape(agent).
- **B** nonce over-fix: `2 failed, 3 passed` — dedup control + shape determinism.
- **C** no-op: `3 failed, 2 passed` — all 3 seizure pins.
- **D** new unguarded write: `2 failed, 3 passed` — L1 exact-set + containment (orphan `_touch_note/UPDATE`).
- **D'** dynamic-table evasion: `2 passed` — L1 BLIND (F-2).
- **E** write escapes `with`: `1 failed, 3 passed` — L2b only (L2a green) — effect-vs-proxy.
- **E'** unwire `_recreate`: `1 failed, 1 passed` — L2a only (L2b green, un-exercised) — F-3.
- **F** reinforce +scope: `1 failed` — statement-shape pin (resolved `scope`).
- **G** pre-filter reinforce: `1 failed, 1 passed` — isolation pin `0.5 -> 0.55`, control green.
- **H** drop `_audit_statements`: `2 failed` — both audit-DDL composition-root pins.

Instrument note (brief-base §1): my wrong builds are transcribed as diffs above (F-2 pasted verbatim);
the reference build's exact edits are the §SAT shapes; the scratch tree is disposable by design.
