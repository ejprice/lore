# D&D graph scope — the edge catalog and the 2026-08-01/02 operator rulings

**Status: RULED.** This doc records the operator rulings from the 2026-08-01/02 slot-in
session and the consolidated edge catalog they were made from. It is the design input for
packet 50 (dnd design spec) and amends `2026-08-01-dnd-rules-rag-proposal.md` §9.
**Provenance:** three read-only graph-scope scouts, archived with every derivation command at
`docs/plans/v2/receipts/2026-08-01-dnd-graph-scope/REPORT-{class,monster,crosscut}-scout-1.md`
(they extend, not supersede, the `2026-08-01-dnd-rag-scoping/` reports). Counts inherit
their derivations from those reports — anything without a derivation there is unchecked.

## 1. The rulings

1. **Fork 1 = OPTION C** (extension framework wired; D&D its first extension; second
   instance `lore-dnd`; allowlist gates the surface).
2. **Comms completes first** (wave C: 04b-2 → 05a → 05b → 06); wave D starts after.
3. **Hosted on this box, exposed off-LAN** via hades' Caddy to claude.ai users (odoo-code
   pattern) ⇒ packet 39 build + principals/keys precede go-live; #236/#138 consult at
   first exposure.
4. **Fork 6 OVERRIDDEN — full-power graph**: monsters (type, CR), classes → subclasses →
   features are all in scope. Reference query: *"What creatures can my level 4 Moon Druid
   wild shape into?"*
5. **THE PICKS — seven families ship in v1** (§2 below): spells+classes · class
   architecture · monsters core · monster—casts→spell · conditions + damage types ·
   items · feats/backgrounds/species. **Deferred with a named trigger** (first
   campaign-lore query that needs it): lore glossary / deities / planes / gazetteer.
6. **COMPOSITION IS CLIENT-SIDE, ALWAYS.** Wild shape is one of MANY prose-mechanic
   rules. The served pattern: the consumer LLM searches the rule → reads the returned
   rules text → derives the constraint (Beast, CR = level/3) → runs a graph FILTER query
   (Beasts at CR ≤ 1). Packet 50 therefore designs **rules retrieval + general
   parameterized graph-filter tools** — no per-mechanic composed tools, no server-side
   rules interpretation. The three inferences the corpus never states (Circle Forms
   overrides only Max CR; silence-means-unchanged for the level-8 fly gate; swarm
   legality) stay in the client's reading of served rules text.
7. **EDITION POLICY: 2024 supersedes 2014 on conflict, implemented as RANKING** —
   downrank `edition: '5.0'` content; no collision ⇒ 2014 content still outranks
   non-answers; collision ⇒ 5.5 wins via the downranking. **Rider (operator, verbatim
   intent): packet 50 must READ the 2024 rules in the corpus for how they say to evaluate
   older material and derive the final policy from that text.** The 2014 base-rules gap
   (no 2014 PHB/MM in the corpus) is a NAMED BOUND renders state on 2014-mechanic
   queries; no scraper work ruled in.
8. ~~**Extraction lives in the lore extension under a real DESIGN SPEC** (packet 50);
   vector search is never neutered — chunks embed prose exactly as today; entity rows +
   edges are ADDITIVE beside chunks (the twelfth-seam shape). Producer changes remain a
   lever only where they do not reduce prose.~~ **SUPERSEDED 2026-08-03 (operator — the
   TRANSMUTE ruling):** extraction moves to the SCRAPER as an LLM transcriber stage
   (`dndlorescraper:SPEC-transmute.md`) — HTML-first, word-for-word fidelity under
   deterministic gates, Claude Agent SDK on the Max subscription; the corpus splits into
   a prose tier (unchanged — the never-neuter clause SURVIVES) and a machine-readable
   `output-graph/**/*.jsonl` tier that the lore extension consumes near-mechanically.
   Wave-D architecture: `2026-08-03-wave-d-architecture.md` (also carries the
   auth-to-the-end resequence: local soak at 54, go-live at 56).
9. **No memory for dnd; the full tool enumeration is ruled** (§4).
10. **Fork 2: the extension package is an in-repo workspace member** (5th member;
    registration derived by `scripts/registration_sites.py`; Containerfile COPY +
    `EXPECTED_MEMBERS`).

Still open, ruled at packet 50/51 kickoff: proposal §9 forks 3 (MCDM dedupe — rec stands),
5 (class-node edition scoping), 7 (edge-only membership), 8 (ENFORCED from birth — rec
stands); D3 (degraded 2014 stat blocks) moves into 50's design scope.

## 2. The picked families — what each ships

| # | family | core content | oracles (build-time pins) |
|---|---|---|---|
| F1 | **spells + classes** | spell nodes; `learnable_by` edges; level/ritual/school as indexed fields | the 987/987 two-source class-edge diff |
| F2 | **class architecture** | subclass—specialises→class (134 entries / 115 names, 7 heading dialects); feature—belongs_to→class/subclass; feature—granted_at→level (an EDGE with a level property — ASI recurs 39×, a scalar field is wrong); subclass—grants_spell (56 + 28 tables); sub-option families (invocations/metamagic/maneuvers) | PHB features 174/174 (headings vs progression tables); XGtE subclass manifest 31/31 |
| F3 | **monsters core** | monster nodes; type/CR/size/speed-modes/senses as fields; habitat edges (Appendix B is the ONLY habitat source for the Beast core); group membership; the 59-row 2014→2024 rename alias | Appendix B: CR 500/0 mismatch; Beast sets 85=85; habitat 337/341 |
| F4 | **monster—casts→spell** | 630 frequency-list edge tokens (630/630 resolve to PHB spells) + inline-action grammar (~94% recall measured) + the 2014-dialect grammar; frequency bucket + upcast rider as edge properties | resolution rate itself (630/630) is the pin |
| F5 | **conditions + damage types** | 15 condition nodes + 13 damage-type nodes; mechanical immunity edges; the GRAMMAR-grade inflicts-condition edge is defer-able within the family | conditions 15=15 across two sources |
| F6 | **items** | item—attunable_by→class (89 pairs — the cleanest edge set in the corpus) / species / feat-gated; item—grants_spell (139 pairs; charge-cost as edge property) | attunement DMG-descriptor vs artificer-table diff (located, undiffed — diff at build) |
| F7 | **feats / backgrounds / species** | feat prerequisite edges (level/ability/feature/feat/species/setting; **13 NEGATIVE prerequisites are anti-edges, never "must have"**); feat—grants_spell (~200–280 pairs; PARAMETRIC grants — school+level — are constraints, not name edges); background—grants_feat (33, with class parameter); species—has_trait (47) | feat category descriptor-vs-table diff; dragonmark EFotA-vs-ERftLW diff (both located, undiffed — diff at build) |

**Explicitly not built:** monster—references→monster (measured mostly-false: `Spider`
21/21 hits are the Spider Climb trait) · spell—references→spell as a name edge (≥58% of
raw surface false) · the deferred lore-glossary family.

## 3. The hazard registers and the resolver — packet 50's checklist

The three archived reports carry numbered hazard registers that are the design spec's
acceptance checklist, cited here by id, never re-transcribed: **H1–H10** (scoping report,
2026-08-01 — ritual-in-Casting-Time, name nesting, dialects), **M1–M10** (monster report —
comma-inside-parens ×3, three ability-table header shapes, embedded Initiative, 4-way case
divergence, merged 2014 immunity fields, Beast dedup 134/91/85, Yuan-ti 1-name→3-blocks,
sub-dialects), **C1–C10** (class report — depth-meaningless headings, 16 subclass name
collisions (11 cross-edition), in-file name drift, SCAG lore-vs-subclass, advice wearing
subclass shape, merged-span table headers), plus the crosscut report's §6.

**The reference resolver** (crosscut report §6, every rule measured): bare-name matching
has a HARD FLOOR — `{Darkness, Darkvision, Resistance, Telepathy}` are simultaneously
glossary terms and spell names; longest-match-first is necessary, not sufficient. The
resolver ships: the 8-rule normalization stack (unicode fold incl. U+2212; unconditional
case-fold — never branch on `edition`, MCDM is the counterexample; hyphen/space
equivalence; plural `e`-restore; trailing-punct strip in see-also quotes; unified index;
context cues; own-heading masking), the cue table (`cast X` → spell · `X condition` ·
`X damage` · attunement parenthetical), and the ~15-name hand-curated ambiguous
deny-list. A generic `**X:**` field extractor is banned: 165 play-example dialogue lines
wear the exact field-line shape.

## 4. The `lore-dnd` tool surface (ruled, closes proposal fork 9)

Mechanism: the allowlist never registers a disabled tool (multi-user proposal §2 / #296-2A
— absent from `tools/list` AND uncallable by SDK dispatch).

**ENABLED (5 generic + domain):** `lore_search` (the rules leg) · `lore_read` (spans w/
book+edition provenance) · `lore_index` (honesty surface) · `lore_diff` (re-scrape change
detector) · `lore_findings` (**ruled ENABLED** — in-band defect channel for players'
agents; rides packet 39's per-principal write gating, which precedes deploy on this plan)
· the `dnd_*` tools (packet 53).

**DISABLED (10), with the rationale packet 54 writes into the instance `lore.yaml`:**
`lore_map` / `lore_get_symbol` / `lore_verify` / `lore_impact` / `lore_dead_code` —
code-only; on a rules corpus each renders an honest-looking EMPTY (`lore_impact` says
`dead (heuristic)` about anything asked) — false clears under the Trust Doctrine ·
`lore_remember` / `lore_recall` — ruled: no memory for dnd · `lore_tasks` /
`lore_claim_task` / `lore_comms` — build-fleet orchestration machinery, purpose-irrelevant
to players.

## 5. The domain tool surface (packet 53's frame, per ruling 6)

Rules retrieval + general filters — illustrative, packet 50 finalizes: `dnd_get_spell(name,
book?)` (one row per book that ships the name — the render names the book, never "the"
Fireball) · `dnd_spells(class?, level?, ritual?, school?, book?)` · `dnd_monsters(type?,
cr_max?, cr_min?, fly?, swim?, habitat?, book?)` · `dnd_get_entity(name, kind?)` for
features/subclasses/items/conditions. Every render names edition and, where touched, the
2014 base-rules bound. Every served surface passes both trust legs (scope diff + forgery
pins from store-deps × {stale, empty, wrong-instance, partial}).

## 6. The worked example, as the acceptance query

Level-4 Moon Druid: search "Moon Druid wild shape" must surface `Level 2: Wild Shape` +
`Level 3: Circle Forms` (2024 PHB); the client derives max CR = 4÷3 → 1, no fly until 8;
`dnd_monsters(type="Beast", cr_max=1, fly=false)` returns the 56-form set (2 swarms
included — swarm legality is corpus-unstated; the render does not adjudicate it). The
XGtE wild-shape text is a fluent POINTER at unscraped 2014 rules — the class report's
sharpest retrieval hazard; the edition downranking plus the named 2014 bound is the
mitigation, and packet 50's design must show this query does not surface XGtE:904 above
the PHB text.
