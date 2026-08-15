# REPORT-adversary-47a (r2 / DELTA) — CONTRACT ADVERSARY, packet 47a (twelfth-seam ingest entity-fragment)

brief-base v14 read
brief project v7 read

_This overwrites the r1 report (r1 verdict: INSUFFICIENT — C-DEFs P6/P13/P20 + missing quantifier pin + P8 reach gap). The r1 findings and their probes are preserved in the archived wave receipts and cited by name below where they anchor a fix._

## SUMMARY BLOCK (read first)

- **VERDICT: CONTRACT SUFFICIENT.**
- **P1 headline — does the CONTRACT hold, and does every fix/new pin CATCH a wrong build?** YES. A known-correct r2 reference build goes **40/40 GREEN** (the 3 r1 C-DEFs are genuinely fixed), and I broke each fix and each new pin with a deliberately-wrong build — **all 6 wrong builds RED**, so the pins are real, not letter-patched.
- **Graded: 0bdc6116 · HEAD-at-report: 0bdc6116 · SAME.** (r2 contract + stubs live in the working tree at this HEAD, uncommitted.)
- **Satisfiability receipt: 40 passed / 0 failed** against a reference build I wrote across 8 production files, spike-surreal `:18000`. Provenance: `loremaster.__file__ = /tmp/adv47a-r2/loremaster/loremaster/__init__.py` (in-scratch, #140-clean).
- **The 3 r1 C-DEF fixes are REAL (fresh frame — I attacked the rewrites, not confirmed them):**
  - **P6 / CF1** (drop `pytest.raises`, `capped==[]` sole discriminator) — private-writer build → **RED** (Probe-F). Correct build → green.
  - **P13 / DG1** (`IngestBackend.entity_tables()` + `SurrealStore(entity_tables=)` + `delete_by_tier` co-purge) — chunk-only build → **RED** (Probe-D).
  - **P20 / DG2** (`ResolvedScope(scope, fragment)` + `IndexSummary.scopes_failed`) — position-based build → **RED** (Probe-E).
- **The new pins DISCRIMINATE (wrong build built for each):** CF2 framework-atomicity (separate-apply → RED, Probe-A); CF5b share-mutation (private per-entry resolver → RED, Probe-B); CF8 3-site mutation (per-site exclusivity clone → RED, Probe-C); CF5c no-op-tick gate (always-resolve → RED, Probe-G).
- **REACH re-check (CF3):** P8 now spans `scripts/` AND `loremaster/scripts/` — the r1 blind spot is closed (both offenders → RED). Reach IS a checked variable within its widened roots.
- **NEW wrong-build survivors introduced by the rewrites?** None found. Two LOW-severity residuals (not blockers, scope-law surfaced): (R1) P8's reach is still a **3-root hand-list** — a `tools/` offender is exempt (Probe-H); (R2) P13 can't distinguish a channel-reading `delete_by_tier` from one hardcoding `fake_node`.
- **decisions-needed:** none. The two residuals are pinned-bound observations with a recommended derived form; per CLAUDE.md's reach STOP-rule I do NOT demand another revision round (the reach is receding one level per round — accept the bound + recommend the whole-repo-derived form).
- **receipt pointers:** satisfiability §Probe-0; fix-verify §Probe-D/E/F; new-pin discrimination §Probe-A/B/C/G; reach §Probe-CF3/H; quantifier table §P1b; reach table §P1c.

---

## THE QUESTION, re-answered on r2 with a FRESH FRAME

> *"If a builder satisfied this contract PERFECTLY but fixed NOTHING — or fixed it WRONG — would these tests still pass?"*

A passing correct build proves only satisfiability; it does NOT prove the pins bite. So I built the r2 reference implementation (8 production files) to get 40/40, then **built a wrong implementation for every fix and every new pin** and ran the real contract against each. The table below is the whole verdict in one place: correct build green, wrong build red, for each.

| pin (r2) | correct build | wrong build I constructed | wrong build result |
|---|---|---|---|
| **P6 / CF1** ONE-IMPL | GREEN | private-writer (raw `_query`, bypasses compose) | **RED** (Probe-F) |
| **P13 / DG1** sink purge | GREEN | `delete_by_tier` chunk-only (ignores `entity_tables`) | **RED** (Probe-D) |
| **P20 / DG2** partial-failure loud | GREEN | report fragment POSITION not `resolved.scope` | **RED** (Probe-E) |
| **CF2** framework-atomicity (∀-dir) | GREEN | non-atomic separate-apply (entity in own apply, before main) | **RED** (Probe-A) |
| **CF5b** share-mutation | GREEN | index_all inlines a private resolver | **RED** (Probe-B) |
| **CF8** 3-site mutation | GREEN | watcher `_purge` hand-rolls its own claim check | **RED** (Probe-C) |
| **CF5c** no-op-tick gate | GREEN | resolver with the gate removed (resolve every tick) | **RED** (Probe-G) |
| **P8 / CF3** reach | GREEN | `Indexer(...)` sans `extensions=` in `scripts/` | **RED** (Probe-CF3) |

Every fix and every new pin discriminates. That is the SUFFICIENT verdict, earned empirically.

---

## P1b — THE QUANTIFIER TABLE (r2)

| # | invariant | ∀ or GUARDED | receipt |
|---|---|---|---|
| 1 | **Per-file atomicity of a claimed file — BOTH sides** | **∀ over both transaction sides (r1 gap CLOSED)** | P5 pins entity-fail⇒nothing-indexed; **CF2 pins framework-fail⇒no-orphan-entities**. r1's surviving separate-apply build is now caught (Probe-A RED). P5 catches the entity-after ordering, CF2 the entity-before ordering — the two orderings are jointly closed. |
| 2 | Entity write rides the SHARED compose | ∀ | P6/CF1 `capped==[]` discriminates (correct green / private-writer RED, Probe-F). The r1 `pytest.raises` false-gate is gone. |
| 3 | Entity nodes present after a claimed index | ∀ | P3 (both slugs+kinds), P4 (`node_rows>0`), P5b positive control (`len==2`). |
| 4 | Chunk-skip (`n_chunks=0` ∧ 0 chunk rows) | ∀ | P4 conjunction; `.fake→markdown` makes the skip leg discriminate. CF6: P15 now REQUIRES `n_chunks==0` (claimed) so it can't pass via the markdown path. |
| 5 | Resolve-or-drop | ∀ over both fates | P19 (one resolvable + one unresolvable) + positive control (two resolvable). |
| 6 | Full-sweep re-resolution / newer-wins | ∀ over re-crawl | P22 genuine cross-book; re-points to newer book Bp. |
| 7 | Phase-2 per-scope isolation + LOUD surface | ∀ (isolation) + **∀ (loud, r1 C-DEF CLOSED)** | P20 asserts A committed, C attempted, B absent, AND `"B" in scopes_failed` — satisfiable now because DG2 `ResolvedScope` carries the label (Probe-E: a position-based build RED). |
| 8 | Corruption-direction convergence | ∀ over both directions | P21 (a→b then a→c ⇒ only a→c). |
| 9 | Dedupe before RELATE | ∀ | P24 (repeated intent ⇒ one edge). |
| 10 | Dirty-store ENFORCED migration | ∀ over the #107 hazard | P25 (legacy row under OLD DDL, OVERWRITE flip, fresh dangler rejected ∧ old row survives; `execute_transaction`). |
| 11 | Claim-exclusivity as ONE shared rule | ∀ over 3 sites | P9 (helper raises naming both) + **CF8 (mutate the shared helper ⇒ all 3 sites propagate; per-site clone RED, Probe-C)**. |
| 12 | Param namespacing `xt_<name>_` | ∀ over ≥2 names | P7 (`fake`/`fake2`). |
| 13 | Lifecycle ready-order + unwind | ∀ over the failure paths | P11 + P12a/b/c (all green on the reference build). |
| 14 | Tier entity purge at the sink (DG1) | ∀ over the sink's callers | P13 (chunk-only build RED, Probe-D). See residual R2. |
| 15 | Phase-2 fires from ALL 3 orchestrator entries via ONE resolver | ∀ over the 3 entries + gated | **CF5a** (rebuild_all resolves), **CF5b** (share-mutation; private resolver RED, Probe-B), **CF5c** (no-op tick gate; always-resolve RED, Probe-G). |

**Every GUARDED-in-r1 row is now ∀, each with a wrong-build receipt.** No row is conditioned on the failure mode that prompted it.

---

## P1c — THE REACH TABLE (r2)

| instrument | reach = SET of sites | DERIVED or hand-list? | coverage a CHECKED variable? | effect vs proxy | one-source proven by mutation? | verdict |
|---|---|---|---|---|---|---|
| **P8 `_find_indexer_construction_sites(_production_python_roots())`** | every `Indexer(...)` call under `{package, repo/scripts, loremaster/scripts}` | coverage DERIVED (AST); **REACH is a HAND-LIST of 3 roots** (r1's single-root hidden constant WIDENED, not eliminated) | reddens when a site is added in ANY of the 3 roots (Probe-CF3: `scripts/` + `loremaster/scripts/` offenders RED); anti-vacuity `assert sites` kept | effect (real AST, `has_extensions` per site) | n/a | **PASS for all realistic sites** — the r1-named gap (`scripts/comms_consumer_eval`) is closed. **RESIDUAL R1:** a `tools/` offender is exempt (Probe-H GREEN). The reach receded one level; per the STOP-rule, pinned-bound + recommend whole-repo derivation, not another round. |
| **CF8 shared `claiming_extension` (mutation)** | the 3 claim sites (indexer/watcher/reconcile) | the sites reference it via the LIVE module (`extension_module.claiming_extension`) | reddens when a site DOESN'T route through it (Probe-C: per-site clone RED) | effect (mutate the real module attr, watch all 3 raise) | **YES — mutation of the ONE helper reddens all 3 sites** | **SAFE.** Genuine ONE-IMPLEMENTATION proof by mutation. |
| **CF5 shared `_resolve_all_extension_edges` (mutation)** | the 3 orchestrator entries (index_all/rebuild_all/reconcile) | spy wraps the class method | reddens when an entry inlines a private resolver (Probe-B RED) | effect (spy counts real method calls); the GATE tested separately by CF5c | **YES — a private per-entry resolver fails to increment** | **SAFE.** Routing≠sharing proven. |
| **P13 `delete_by_tier` co-purge (DG1)** | the tier's entity rows across all 5 callers | co-located in the sink; tables supplied via the `entity_tables` channel | reddens when the co-purge is absent (Probe-D chunk-only RED) | effect (real rows seeded + read back; `fake_node` carries a `tier` field so the DELETE is no #107 no-op) | n/a | **SAFE** (with residual R2: doesn't prove the channel is READ vs hardcoded). |
| **P25 / P26 / P23 / CF5c** guards | (as r1) | derived from the real DDL / spy / gate | reddens on the wrong build (CF5c: Probe-G) | effect | n/a | **SAFE.** |

**Legs run:** all EMPIRICAL (Probe-CF3/H for P8; Probe-C for CF8; Probe-B for CF5b; Probe-D for P13; Probe-G for CF5c). A SUFFICIENT verdict requires this table — provided, with a wrong-build receipt on every row and the one residual named.

---

## THE SATISFIABILITY RECEIPT (mandatory)

- **Provenance:** `loremaster.__file__ = /tmp/adv47a-r2/loremaster/loremaster/__init__.py` (scratch_copy.sh --force, provenance-asserted). Not the original tree.
- **Result: `40 passed in 35.20s`** (`-p no:cacheprovider`, spike-surreal `:18000`). ALL 40 GREEN — the 3 r1 C-DEFs (P6, P13, P20) are gone.
- **8 production files the reference build touched** (so the author knows the shape r2 forces): `extension.py` (`claiming_extension` helper + eleven→twelve), `index/indexer.py` (`_claiming` via live module + `_entity_fragment` + compose branch + chunk-skip + `_resolve_all_extension_edges` with the gate, wired into index_all AND rebuild_all), `index/reconcile.py` (`_purge_file` entity purge via own `extensions` + shared helper; `reconcile` routes phase-2 through the shared resolver), `index/watcher.py` (`_purge` entity purge via own `extensions` + shared helper), `store/surreal.py` (`delete_by_tier` co-purge from `self._entity_tables`), `server.py` (ingest rail block-1 + block-2 teardown + aclose + `extensions=server.extensions` to Indexer/Reconcile/Watcher + `ingest_backends` on AppContext), `index/cli.py` + `scout.py` (`extensions=` threaded).
- **Harder leg:** the 40 pass on a build with the reference additions; the failures I induced (Probes A–H) are structural, not lint artefacts.

---

## RESIDUALS (scope-law — surfaced, NOT blockers)

**R1 — P8's reach is still a HAND-LIST (LOW).** *Probe-H:* an `Indexer(...)` omitting `extensions=` in `_REPO_ROOT/tools/` (a plausible future production tree) → P8 **GREEN** (missed). The r2 `_production_python_roots()` is `[package, repo/scripts, loremaster/scripts]` filtered by `is_dir()` — a wider hand-list than r1, covering all THREE current construction sites and the design's named `scripts/` concern, but not derived. *Why not a blocker:* no current wrong build survives (all 3 sites are covered), the residual is hypothetical, and per CLAUDE.md's reach STOP-rule the reach is *receding one level per round* — the correct move is a pinned bound + a recommended derived form, not another revision. *Recommended derived form (ends the recession):* rglob `*.py` under `_REPO_ROOT` excluding `**/tests/**`, `**/.venv/**`, `**/.git/**` — every production tree, present or future, is then in reach. *Re-open trigger:* the day an `Indexer(...)` is constructed in any tree outside the 3 roots.

**R2 — P13 doesn't prove the channel is READ (LOW).** A `delete_by_tier` that HARDCODED `DELETE fake_node WHERE tier` (ignoring `self._entity_tables`) would also pass P13. Implausible (a production method hardcoding a fixture table name) and review-catchable, but the pin verifies the OUTCOME (fake_node purged), not that the DG1 channel is the mechanism. *Optional tightening:* a second extension contributing a differently-named entity table, asserting BOTH are purged — then a single-table hardcode fails.

**Adjudicated author-flags (from r1, resolved in r2):** P14 access-path → CF7 (watcher/reconcile own `extensions=` param) — verified satisfiable (P14a/P14b green). P20 identifier reading → DG2 — satisfiable + discriminating (Probe-E).

---

## §P-PKG — package survey diff (unchanged from r1)

My independent survey AGREES with the author's `Packages considered: none`. DG1/DG2 add typed seam SURFACE (`entity_tables`, `ResolvedScope`) and wire the EXISTING `_txn` compose/apply layer; no new mechanism, no library gap. `keep_with_trigger` on `_txn` (the mutation-proven driver). No `bespoke` verdict has an empty read-column.

---

## FULL PROBE RECORD (commands + real output)

All in `/tmp/adv47a-r2` (r2 reference build); each wrong build was applied, the target test run, then reverted from `/tmp/r2bak`.

- **Probe-0 (satisfiability):** `uv run pytest loremaster/tests/test_ingest_entity_seam.py -q` → `40 passed in 35.20s`. `loremaster.__file__` in-scratch.
- **Probe-D (P13/DG1 real):** `delete_by_tier` reverted to chunk-only → `TestSinkPurge` **FAILED** (fake_node rows survive).
- **Probe-E (P20/DG2 real):** `scopes_failed.append(str(_idx))` (position) → `TestPhaseTwoPartialFailure` **FAILED** (`'B' not in {'1'}`).
- **Probe-F (P6/CF1 real):** entity via raw `_query` (bypass compose) → `TestOneImplementation` **FAILED** (`capped != []`).
- **Probe-A (CF2 discriminates):** entity in a SEPARATE `store.apply` before the main apply → `test_framework_failure_leaves_no_orphan_entity_rows` **FAILED** (orphan entity rows survive the poisoned framework apply).
- **Probe-B (CF5b discriminates):** index_all inlines a private resolver → `test_all_three_entries_share_one_resolver` **FAILED** (`index_all must route through the shared resolver`, line 1222).
- **Probe-C (CF8 discriminates):** watcher `_purge` hand-rolls its own claim check → `test_all_three_sites_route_through_the_shared_helper` **FAILED** (the mutated helper's `RuntimeError("MUTATED")` not raised at the watcher leg, line 692).
- **Probe-G (CF5c discriminates):** gate removed (resolve every tick) → `test_noop_reconcile_tick_does_not_reresolve` **FAILED** (a no-op reconcile re-resolved).
- **Probe-CF3 (reach closed):** offender in `scripts/` → **FAILED (caught)**; offender in `loremaster/scripts/` → **FAILED (caught)**; no offender → passed.
- **Probe-H (reach residual):** offender in `_REPO_ROOT/tools/` → **passed (MISSED)** — R1.

---

## VERDICT: **CONTRACT SUFFICIENT**

The r2 contract is satisfiable by a correct build (40/40, provenance-clean), every r1 C-DEF is genuinely fixed (P6/CF1, P13/DG1, P20/DG2 — each verified by a reddening wrong build), the missing quantifier pin is added and discriminates (CF2), the new ONE-IMPLEMENTATION mutation pins bite (CF5b, CF8), the no-op-tick gate is real (CF5c), and the r1 reach gap the verdict raised is closed for every realistic construction site (CF3). The two residuals are low-severity, non-blocking observations with recommended tightenings and named re-open triggers; per the reach STOP-rule I decline to force another round on a reach that is receding one level at a time. The scratch worktree `/tmp/adv47a-r2` holds the reference build and probes; the operator decides its disposition. No revision skips the adversary — but this one has nothing left that must be fixed before a builder starts.
