## Routing table (written before any packet read)
| step | tier | who | why |
|---|---|---|---|
| read 5 packet files (~420 lines) + INDEX rows | 3 | self | the answer IS subsystem-boundary judgment for slotting findings; a mis-scoped draft seals itself (lead slots findings on it); reading is ~420 lines, smaller than a brief+sample |
| #NNN extraction | 1 | self, one `python -I` command | one deterministic command; spawning costs more than running |

---
brief-base v26 read
STATE: done · read-only; read 2026-11-09 at HEAD e1593d7 (feat/surreal-unification)
Deviations: the routing table sits above this block because §3 says to write it first.
Packages considered: none (no mechanism specified) · Odoo-20 portability: n/a (no Odoo seam touched) · Reuse ledger: none
Graded: n/a (scope summary, not a verdict)
Decisions needed: (1) #563/#557 (covering-tests cap 15, classes/modules counted as tests) have NO home in any of the 5 files OR in INDEX.md. Nearest home is 28 (#155/#252/#459), but 28's Scope OUT bars impact SEMANTIC changes. (2) Stale text found, listed in §Flags.
Landmine recall: k=50 returned 6 notes, so the list is not cut off.
Finding lists were extracted with `python3 -I` regex `#(\d+)` over each file. They are raw: they include context and receipt numbers, not only owned findings. I mark owned vs mentioned below.

## 16 — surreal-ops-hardening
1. Status (INDEX row `| 16 |`): open; depends on 07a ✅ (2026-08-17), which "UNBLOCKED" #249's prod leg; L ∥; 0.15, with split guidance.
2. Scope IN: explicit RocksDB cache/memory bounds in both quadlets (#110); the credential story plus killing the boot warning (#116); reaping spike-surreal orphan test DBs plus an age-based reaper (#113); a durable `transaction.conflicts` scrape (#109); slow-query logging and txn timeouts, probe-then-apply-or-document (#114); `?sync=never` on the TEST store only (#117); land #175 (the UPDATE-on-edge zero-match) and #239 (4.0 RELATE deterministic-id break) in the store reference; a #249 RSS restart policy sized with #110.
3. Finding numbers in the file: 102 107 109 110 113 114 116 117 124 164 175 239 249 250 349. Owned: #109 #110 #113 #114 #116 #117 #175 #239 #249. The rest are context; #349 is an upstream release-note item.
   Added by the INDEX row only (routed 2026-09-24): #379 #380 #409 #422 #463 #468 + #433, the `:18500` WS-drop class, plus #341, pinning the floating tag.
4. Sub-splits: if the packet is over size at kickoff, 16 keeps the ops six + #249, and the #175/#239 probe→reference work goes to **16b**. 16a is a separate packet (loresigil #205/#223/#209), not a split of 16.
5. Fits: findings about the store DEPLOYMENT and engine behaviour, i.e. the quadlet units, store config/tuning, the test-store hygiene reaper, and the `docs/reference/surrealdb-31-capabilities.md` entries. Lore code, schema/DDL and engine upgrades are explicitly OUT.
**Answers (HIGH, read):**
- WS-drop class: owned per the INDEX row only. The packet file never names it.
- #249: owned, as a "restart policy in the quadlets, sized WITH #110's cache bounds". The word `MemoryMax` does not appear in the file. #110 says "cache/memory bounds".
- Reconnect: the header says "lore containers reconnect". The Exit requires "lore/DI containers reconnect and serve (live smoke)". #249's text still says "BLOCKED … lore-lore does not survive a store restart; 07a is the enabler", which is stale: 07a's row says the wedge did NOT reproduce, A1 was ruled, and the **named re-open trigger = packet 16**. So reconnect-after-restart re-enters through 16's restart work.

## 11c — index boot/reconcile honesty
1. Status (INDEX row `| 11c |`): open, MINTED 2026-09-24. RULED a HARD dependency of 65 (runs before the cutover; its own recreate is the measurement). L ∥ · ~0.20.
2. Scope IN: (1) a #355 structured decision log at the heal (tier, counts, leg, action), added before anything else; (2) a #355 per-file heal instead of a whole-tier purge (F-1), possibly mid-life detection (F-2); (3) #338/#383, so a file over 5000 statements per txn indexes (chunked compose / budget, F-3), plus stopping the re-embed of an unchanged failed file; (4) #474 + task `f4e3b63f…`, renaming `embed.permanent_failure` on batch exhaustion and logging the fallback outcome; (5) **#434**, making `lore_index(reconcile=True)` progress-emitting or async, or teaching the bound (F-4); (6) #366, one shared `_periodic_reconcile` with a mutation proof; (7) re-measuring the eager-boot budget and correcting CLAUDE.md §Deploy.
3. Finding numbers in the file: 1 165 166 171 336 338 339 341 355 366 383 434 466 472 474. Owned: #355 #338 #383 #434 #474 #366. OUT: #171 #339 #165 #166 #336/#341 (→16). Context: #472 #466 #1.
4. Sub-splits: none minted. The size note says "→split at kickoff if #355's root-cause hunt prices it over". F-5 decides whether 11b subsumes #355, leaving 11c with items 1 and 3–7.
5. Fits: findings about index boot/sweep/reconcile behaviour and indexing-failure honesty: `server.reconcile_store_divergence`, `store/_txn.compose`, `Indexer._index_chunks`, `loresigil.resilient` logging, the two `_periodic_reconcile` daemons, and the `lore_index` reconcile surface.
**Answer (HIGH):** 11c owns BOTH the boot purge (#355) AND the `reconcile=True` timeout (#434, Scope item 5, F-4). "Progress" is one of F-4's named options.

## 09 — surface residues (09a / 09b)
1. Status (INDEX row `| 09 |`): open; SPLIT RULED 2026-07-29; two sessions, ~0.20 + ~0.20 ("09b grew").
2. Scope IN (file): #84/#85 get_symbol miss-arm teach parity; #86 at-cap off-by-one; #88 wrong-method miss lists the class's methods; #64 lore_read nested-path teach; #80 map tail edge; #82 suffix-bound tripwire; #34 promoting the sanitiser seam to a public module (with hostile fixtures); #197 `capture_git_identity` silent `(None,None)`; #208 XML element-relative spans served as `file:line`; #230 six unfailable isinstance-on-raises assertions; #231 the #210 gate allowlist keyed per (pattern, site); #244 23 `unique_database()` clones collapsed with a mutation proof; a README/docs truth pass.
3. Finding numbers in the file: 12 15 34 64 80 82 84 85 86 88 90 92 131 197 208 210 229 230 231 244 246. Owned: #15 #34 #64 #80 #82 #84 #85 #86 #88 #92 #197 #208 #230 #231 #244 (+#12 if still open). Context: #90 #131 #210 #229 #246.
4. Sub-splits:
   - **09a**, served surface + docs truth: #15 #64 #80 #82 #84–86 #88 #92 #197 #208 + the docs pass; the INDEX row adds #391 and task `73516abe` (a re-run of the 35-pair bar on the 15-tool surface).
   - **09b**, testing hygiene: #230 #231 #244. **The INDEX row (not the file) adds #293 #364 #390 #401 #405 #410 #421 #426 #450 #461 #466**, which it labels "the harness port/RAM isolation + 'full suite ALONE `-n 12`' law". **So yes, 09b is the test-harness / gate-tooling half.**
   - #34 is listed in neither split (only the file's Scope IN has it). The header says #92 supersedes #34/#90. MEDIUM: likely consumed by #92, unverified.
5. Fits: 09a takes served-render/teach-text truth fixes in the existing tools plus docs prose, with no map/impact semantics (DESIGN-LAW §2). 09b takes test-harness and gate-instrument defects (`_surreal_harness`, AST/pattern gates, test assertions, worker/RAM isolation).

## 28 — graph/search v1.1
1. Status (INDEX row `| 28 |`): open; wave F; 0.35 →split; depends on v1.0.
2. Scope IN: materialized PageRank, one-query graph-enriched search, and materialized RELATE eval, each adopted only if measured better; docstring as a weighted BM25 field; a markdown link extractor → refers edges; #70 depth>1 honesty; #155 the `tests_for` friction; #3 attribute-access edges (OPERATOR GRANT required); a #233 count-line degradation render; #254 path-scoped search budget/detail defaults; #252 indirect `tests_for` coverage; relative-score fusion; personalized-PageRank lane (disclosed, no covert re-rank); detail_level reshape only if the operator places it here.
3. Finding numbers in the file: 3 70 155 233 252 254. INDEX row adds #361 (test doubles outrank the prod definition) and #459 (`lore_impact` cannot resolve a test module), plus #20/#37/#40/#41 as candidates.
4. Sub-splits: "→split" is flagged, but no halves are minted. 28a (report/thread serving, #163/#160) is a separate packet.
5. Fits: graph-derived ranking/coverage and search relevance/budget behaviour: graph edges, `tests_for`, impact rollup renders, fusion/ranking. Scope OUT: impact/map SEMANTIC changes (these need a fresh consult) and reranker adoption.
**Answers:**
- Covering-tests view (HIGH): 28 owns its friction class: #155 (live `tests_for` friction), #252 (empty for indirect-only coverage, the "misses indirect coverage" half of #563) and #459. **The cap of 15, counting classes/modules as tests (#557), and completeness labelling are named NOWHERE**: not in these 5 files, and `#557`/`#563` do not appear in INDEX.md at all. 28 is the natural home, but counting semantics may trip its Scope OUT (DESIGN-LAW §2). That is an operator fork.
- Search recall (MEDIUM): only #254 is related, a path-scoped constant lookup served a stub and the agent routed to grep. It is framed as budget/detail defaults, not as an embedding/chunking recall miss. Recall misses on module-level constants or literal config keys as a chunker/recall defect are owned by none of the five.

## 43 — derivation-source unification
1. Status (INDEX row `| 43 |`): open, minted 2026-07-26; L; 0.20; independent; DESIGN problem → an Opus author who attacks its own design.
2. Scope IN: (1) a design pass on why `_derive_edges` re-reads from disk (`evict_resolved_file`/astroid cache), which source to unify on, with a doc and the operator ruling; (2) build the unification; (3) the `refers`/`answers_to` `ENFORCED` flip (`_refers_statements`, `_answers_to_statements`); (4) the statement-ordered ∀ pin "never RELATE from an endpoint no earlier statement of the same fragment created"; (5) #248, folding 7 `_bare_id` copies into one with a per-site mutation proof (separable).
3. Finding numbers in the file: 219 248. Owned: #248. #219 is Scope OUT (→04a/04b). The core divergence defect has no finding number; it cites `REPORT-contract-04a-enforced.md` §4.D2 @ `48537c3`.
4. Sub-splits: #248 may split out with its own row at kickoff.
5. Fits: findings in the indexer's graph-fragment WRITE derivation: `graph.py` `_derive_nodes`/`_derive_edges`/`build_file_graph_fragment`, RELATE enforcement, `_bare_id` parsing. Widening what is indexed is OUT.
**Answer (MEDIUM, from scope text):** 43 owns WHICH SOURCE the node and edge derivations read, and the dangling-edge consequence. It does NOT own the reference-resolution coverage that `lore_impact`/`lore_dead_code` read. A false-dead verdict caused by node/edge source divergence or a dangling `src` belongs in 43. A false-dead caused by a MISSING edge kind (attribute access, dynamic dispatch, an un-indexed consumer) belongs in 28 (#3, grant-gated). A dead_code caveat/corroborator belongs in INDEX pool item 18 → packet 35. Route by mechanism.

## Flags (stale or conflicting text, surfaced; operator/lead decides)
- 43 Exit says `pytest -n auto`, which contradicts CLAUDE.md "never `-n auto`" and the full-suite `-n 12` rule.
- 11c Hazards say "do NOT `lore-deploy start` lore-lore (hand-rolled mount)". The landmine says it is SAFE since the #165 fix (2026-11-01).
- 16: the #249 "BLOCKED by #250/#164" is stale per 07a ✅. #114 says "probe what 3.1.5 offers" and #175 says "3.2.1", but the stores are on 3.3.5 since 2026-11-07. The Entry check says "all seven" while the file owns nine.
- 09: #34 appears in Scope IN but in neither split list.
