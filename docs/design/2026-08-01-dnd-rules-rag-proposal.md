# Proposal — a D&D rules RAG: extend lore, reuse its components, or both

**Status:** ~~PROPOSAL, not ruled~~ → **RULED 2026-08-02: option C** (fork 1), slotted into
the plan of record as wave D (INDEX packets 45–54). Forks 2/4/9 also ruled, fork 6
OVERRIDDEN (monsters + class architecture IN), fork 10 done earlier at `b3ba703`; forks
3/5/7/8 + D3 route to packet 50's kickoff. The rulings, the graph-scope edge catalog, and
the closed tool enumeration live in `2026-08-02-dnd-graph-scope-rulings.md` (which amends
§9 of this doc); deep-scout receipts at
`docs/plans/v2/receipts/2026-08-01-dnd-graph-scope/`.
**Author:** design lead (Fable), 2026-08-01, at `a049118` on `feat/surreal-unification`.
**Provenance:** three parallel read-only scouts, every claim `file:symbol`-cited in their
reports, archived at `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/`:
- `REPORT-corpus-scout-1.md` — the corpus, entity taxonomy, graph-readiness, hazards H1–H10
- `REPORT-lorearch-scout-1.md` — component-by-component reuse verdicts, the tool-set split
- `REPORT-graph-scout-1.md` — SurrealDB modelling, 6 live probes on the test store,
  instruments pasted verbatim in its §7

Companion doc: `docs/design/2026-08-01-multi-user-lore-proposal.md` (the allowlist is its
Part 2; principals/keys/scoped memory are its Parts 1 and 3).

**Standing operator decisions this proposal builds on, not re-litigates:** a tool allowlist
in `lore.yaml` (enable/disable per deploy, applied on restart); the D&D MCP is multi-user;
SurrealDB-native graph for spell→class→level questions; the chunker is out of scope.

---

## 1. Context — what the corpus scout established

The corpus (`/home/ejprice/code/python/dndlorescraper/output`): 141 markdown files (~3.1M),
2024 core books (PHB/DMG/MM), five 2014-era expansions, one MCDM book. All measured
2026-08-01 against the 2026-07-31 scrape.

- **All three target queries are supported and were empirically verified** — 21 Druid
  level-4 spells and 14 Druid ritual spells, each derived from **two independent corpus
  sources that agree exactly** (per-spell descriptor lines vs the class spell-list tables:
  987/987 class edges, zero disagreement across all 8 classes). `Fireball` resolves to
  exactly one heading corpus-wide. (Archived report §6, instrument in §6.4.)
- **Frontmatter is uniform and load-bearing**: 12 identical YAML keys × 141 files, including
  `edition` (the 2014-vs-2024 disambiguator), `source_book`, `tier`, `content_sha256` —
  validated against the crawler manifest, 141/141 hash match.
- Entity mass: 528 spell entries / 496 distinct names (4 descriptor dialects; PHB-2024's
  parses 391/391 with one regex) · 667 stat blocks / 596 distinct (599 clean 2024-dialect,
  68 degraded 2014-dialect) · 372 magic items (the cleanest entity; attunement restrictions
  are a free item→class edge set) · 134 feats · classes/subclasses/backgrounds/species.
- **The two silent-failure traps** (archived report H1/H7b): ritual status lives in the
  *Casting Time value*, not the spell descriptor (a descriptor-reading extractor reports
  zero PHB rituals, plausibly); and entity names contain other entity names (`Fireball` ⊂
  `Delayed Blast Fireball`; 77 stat-block cases), so bare-name reference matching must be
  longest-match-first — `\b` anchoring does not fix it.
- **Zero markdown links or anchors exist in the corpus.** Every cross-reference is a bare
  capitalised name in prose; the entity-name index is the load-bearing artifact.
- Three product decisions belong to the operator, not the extractor: **D1** the
  byte-identical `MCDM/tir` file pair; **D2** the 19 cross-edition same-name spell pairs
  (same name/level/school, *different rules text*, sometimes different class lists); **D3**
  whether the degraded 2014-dialect stat blocks are in scope at all. (§9 below.)

## 2. What the architecture scout established

Verdicts, from the archived reuse map (§11 there carries the full table):

| Component | Verdict for a rules corpus |
|---|---|
| `lorerunes` / `lorescribe` / `loresigil` | **GENERIC, zero work.** The markdown ingest path is code-free and proven at scale by the three vendor-doc tiers in this repo's own `lore.yaml`. The shared TEI embedder needs nothing. |
| tier system (`RootConfig`, `local_directory`, watcher, reconcile) | **GENERIC — a D&D tier is declarable TODAY, config-only.** |
| `store/_txn.py` (driver: `execute_transaction`, `retry_on_conflict`, `compose`) | **GENERIC — the single most valuable reusable asset.** |
| `surreal_schema.py` per-domain DDL slices | **GENERIC-WITH-WORK** — a `_SPELL_FIELD_SPECS` slice follows the `floor_*`/`lease` recipe (`7acbef4`). |
| the code graph (`code_node`/`refers`, `graph.py`) | **CODE-SPECIFIC, unusable for D&D** — but its *patterns* transfer (composite ids, edge scope columns, purge-by-scope re-ingest). |
| memory / findings / tasks / comms / diff | **GENERIC** (tasks/comms are purpose-irrelevant for D&D — allowlist them off). |
| deploy (one image, N `lore-<slug>` containers, shared store + embedder) | **GENERIC — a `dnd` instance costs essentially zero new machinery.** Slug must be hyphen-free. |
| **the extension framework** (`loremaster/extension.py`) | **COMPLETE and UNWIRED.** Eleven seams — declarative ToolSpecs, `payload_indexes`, config model, source providers, chunkers — written *for exactly this use case* (its docstring: "the contract by which a domain-specific MCP … plugs into loremaster as a thin extension"). `_register_extension_tools` is live in `build_mcp_server`; **but zero production call sites of `register_extension` exist and no config→extension discovery path exists.** 340 tests, no production mileage. |
| ingest-time entity extraction | **THE GAP.** No seam lets a tier contribute typed records + edges to the per-file index transaction — the extension ABC's eleven seams do not include a write-fragment. This is the one genuinely new design item in every option. |

**Tool-surface split** (archived report §10): 10 of the 15 tools are corpus-agnostic; 5 are
Python-only (`lore_get_symbol`, `lore_verify`, `lore_impact`, `lore_map`, `lore_dead_code`).
⚠ The five do not merely under-serve a rules corpus — **they return honest-looking EMPTY**
(`lore_map` renders an empty module list; `lore_impact` says `dead (heuristic)` about
anything asked). Under the Trust Doctrine that is a false clear wearing an honest render.
**The allowlist is therefore trust-critical for a D&D instance, not ergonomic** — this
belongs in the allowlist's rationale when it ships.

Minimal viable D&D generic set (6+1): `lore_search`, `lore_read`, `lore_index`,
`lore_remember`, `lore_recall`, `lore_diff`, optionally `lore_findings` — plus the domain
tools that do not exist yet.

## 3. What the graph scout established

Six live probes on the test store (`ws://127.0.0.1:18000`, throwaway namespaces, verbatim
instruments in the archived report §7). Engine 3.2.1. Highlights that shape the design:

1. **A graph traversal NEVER uses a secondary index** — every traversal plan is a
   `GraphEdgeScan` from the start record (probed: a defined `level` index provably absent
   from the traversal's plan). You cannot index your way out of a traversal. Meanwhile **an
   edge table read as a plain table is fully indexable** — which is also how lore's own code
   graph does every read (`SELECT VALUE in FROM refers WHERE out IN $names`; not one arrow
   traversal in `graph_surreal.py`; arrows are used for writes and for the single genuinely
   recursive query in the repo).
2. **The array-index trap**: `DEFINE INDEX … FIELDS classes` on an `array<string>` is
   useless for containment (all containment spellings TableScan) — and the one spelling it
   accelerates, `WHERE classes = 'druid'`, IndexScans and returns `[]` silently. The correct
   spelling is the element path `FIELDS classes.*`.
3. **Composite indexes are leading-column only**; one `UNIQUE(name, source_book)` index
   serves both cross-book uniqueness and the exact-name lookup.
4. **Two engine behaviours nobody has documented anywhere** (we are the only source, probed
   with controls): a `WHERE` over a subquery-`FROM` is evaluated once over the whole result
   array — all-or-nothing, including a **false-INCLUDE** (a "level 4" filter returning a
   level-1 spell, no error); and an SDK-minted `RecordID("t", "4")` (string id) vs the
   SurrealQL literal `t:4` (int id) are **different records**, the mismatch reading as `[]`.
   Rule: never put a traversal-producing subquery in a `FROM`; never mint numeric-looking
   ids.
5. **Re-ingest corrupts the graph in both directions unless edges are handled explicitly**
   (probed): DELETE+CREATE silently loses edges (a re-created spell is absent from its own
   class list, no error); UPDATE silently keeps stale edges. Mitigation is lore's own
   pattern: a `source_book` scope column on the edge and purge-then-rebuild per book in one
   transaction.

**The modelling recommendation (hybrid), with the dividing line stated once:** *a thing
connecting two entities that both have identity, attributes, and inbound questions is an
EDGE; one scalar belonging to one entity is a FIELD.* So: `spell` and `class` node tables;
`learnable_by` relation (`ENFORCED` + `UNIQUE(in,out)` from birth, `source_book` + `via`
on the edge); `level`/`ritual`/`school` as indexed fields. **`Spells->Druid->Level 4` is an
edge hop for Druid and a field filter for level:**

```surql
SELECT VALUE in.* FROM learnable_by
WHERE out = class:druid AND in.level = 4;      -- IndexScan on lb_out + cheap filter

SELECT *, ->learnable_by->class.name AS classes
FROM spell WHERE name = $name;                  -- IndexScan on UNIQUE(name, source_book)
```

Edges genuinely pay where the questions are relational: subclass inheritance
(`subclass->specialises->class`, the one recursive case), "monsters that cast Fireball",
"items granting X", per-edge provenance ("from Circle of the Land"). Each is a new edge
table and zero changes to `spell`. Full DDL sketch, under the repo's migration law, in the
archived report §5.

---

## 4. The options

### Option A — extend lore in place (domain code in loremaster proper)

Add the D&D tier to a lore instance, add `spell`/`class` tables to `surreal_schema.py`,
add `dnd_*` tools as more hardcoded decorators in `_register_tools`, add an extraction
step to `Indexer`.

- **For:** every path is well-trodden; no framework wiring; smallest step count to a demo.
- **Against:** D&D-specific code rides in the image every project's RAG runs; the exact-set
  pin, `_INSTRUCTIONS`, and the dead-name scan grow domain entries that every OTHER
  instance's config must then disable; the extension framework — built for exactly this —
  stays unwired and unproven, while its reason to exist is consumed piecemeal. It is the
  quiet start of a second registration idiom beside the one the framework already defines.

### Option B — a separate D&D MCP reusing lore's components as libraries

New repo/package importing `lorerunes` + `lorescribe` + `loresigil` (all supported library
shapes today), with its own server.

- **For:** total isolation; a tool surface designed from scratch for the domain; none of
  lore's process weight on a hobby corpus.
- **Against — and this is where the measurement is decisive:** everything above the three
  lower members must be rebuilt — config, indexer, watcher, snapshot/materialisation, store
  schema management, hybrid search, MCP server, deploy, conformance guard. That is most of
  `loremaster`. **And the operator's multi-user requirement doubles the bill**: principals,
  key mint/validation, scoped memory are designed (multi-user proposal Parts 1/3) to land
  in lore — a separate MCP either duplicates them (the ONE IMPLEMENTATION violation this
  repo has the most receipts against) or waits on extracting loremaster's core into a
  shared member, a refactor larger than the D&D project itself.

### Option C — lore as platform: wire the extension framework, D&D is its first real extension, deployed as a second instance ★ RECOMMENDED

1. The **allowlist** ships as designed (multi-user proposal Part 2 — needed for #296
   regardless of D&D; the D&D instance is its second-best argument).
2. The **extension discovery gap is closed**: `extensions:` in `lore.yaml` actually
   instantiates registered `Extension`s (an entry-point/registry lookup in `from_config` —
   small, well-scoped).
3. The **twelfth seam is designed** (the one real design packet): an extension-contributed
   ingest fragment — per-tier entity extraction producing typed records + `RELATE` edges
   composed into the same per-file `store.apply(fragments)` transaction as chunks, so
   entities and chunks commit or roll back together, and purge-by-scope rides the existing
   `replace_file`/`delete_by_tier` semantics.
4. The **`dnd` extension package** is built against those seams: the extractor
   (dialect-A first), the schema slice, a `SpellStore` (ledger-pattern: own connection,
   `_txn` driver — `SurrealStore` deliberately has no arbitrary-query verb), and the domain
   `ToolSpec`s.
5. **Deploy `lore-dnd`**: one more container on the existing image, slug `dnd`, database
   `dnd` in the shared store, same TEI embedder, its `lore.yaml` enabling the 6–7 generic
   tools + the `dnd_*` tools. lore-the-repo's own instance never sees a spell.
6. **Multi-user lands once, in lore** (proposal Parts 1A→1C→3), and the D&D instance
   inherits it by being a lore deploy. Nothing is duplicated.

- **For:** everything measured as GENERIC is consumed as-is; the D&D corpus becomes the
  forcing function that pays lore's own outstanding debts (allowlist, extension wiring —
  both already wanted); domain code stays out of other instances' surfaces; multi-user is
  built once.
- **Against / honest costs:** the extension framework has zero production mileage — D&D
  becomes its shakedown cruise (its 340 tests notwithstanding); the twelfth seam is real
  design work with an adversary and a cold audit, not a build brief; and two flagged
  defects must be fixed en route (the extension name-collision guard checks the registered
  set, not the declared universe; `_INSTRUCTIONS` + tool descriptions must become functions
  of the enabled set — the allowlist's true cost).

### The comparison, on the measured axes

| Axis | A: in-place | B: separate MCP | C: extension + instance |
|---|---|---|---|
| chunking/embedding/tiers | free | free (as libraries) | free |
| index pipeline, watcher, search | free | **rebuild** | free |
| store schema + driver | slice recipe | rebuild schema mgmt (driver reusable) | slice recipe |
| MCP server + deploy | free | **rebuild both** | free |
| domain tools | hardcoded decorators + pin/prose churn in every instance | native, clean | declarative `ToolSpec`s |
| entity-extraction seam | new code on the shared hot path | new code, private | **new seam, designed once, reusable** |
| multi-user | shared, once | **duplicated or blocked** | shared, once |
| isolation of D&D from other instances | poor | total | good (config-off + separate DB) |
| new risk taken | domain creep in the platform | large rebuild surface | first production run of the extension framework |

## 5. What gets built under C — packet-shaped sketch

Sizing uses the house S/M/L idiom. Order matters; 1–2 are independent of D&D and already
wanted.

| # | Packet | Size | Notes |
|---|---|---|---|
| 1 | Allowlist (= multi-user Part 2) | M–L | already sized in the companion proposal; cost centre is served prose becoming config-derived. Fix the collision-guard universe bug here. |
| 2 | Extension discovery wiring | S–M | `extensions:` → instantiate + `register_extension`; pin: a config naming an unknown extension fails boot loudly. |
| 3 | **Twelfth seam design** (ingest entity fragment) | M design | DESIGN packet: contract → adversary → build → cold audit. The one invent-a-property item — per the routing rule it never reaches a builder as "figure out the general form". |
| 4 | `dnd` extension: extractor | M | dialect A (PHB 391) first; XGtE/TCoE/MCDM dialects follow. Hazards H1/H7b are pinned in the contract. **The A/B two-source diff ships as a permanent build-time pin, not a one-off check** — it is the only mechanical oracle the corpus offers. |
| 5 | `dnd` extension: schema slice + `SpellStore` | M | DDL per archived graph report §5; three-legged store idiom (offline DDL pin, live round-trip, dirty-store migration pin). |
| 6 | `dnd` extension: domain tools | S–M | initial surface: `dnd_get_spell(name, book?)` (N rows per book — the render names the book, never "the" Fireball), `dnd_spells(class?, level?, ritual?, school?, book?)`. Later: stat blocks, magic items (attunement edges), feats. Every served surface passes the two trust legs (scope diff + forgery pins). |
| 7 | Deploy `lore-dnd` | S | config + secrets + smoke; corpus as a `watch: static, provider: local_directory` tier, version-stamped per scrape. |
| — | Multi-user (Parts 1A/1B/1C/3) | per companion proposal | independent track; D&D inherits at deploy. |

Chunking: per the operator, out of scope — the markdown chunker serves both options today;
a stat-block-aware chunker is a later, optional `Chunker` subclass.

## 6. Where the `dnd` extension package lives — a fork with a recommendation

The extension contract was written for out-of-repo consumers, but a first extension needs a
home the image can install. Options: (a) a workspace member in this repo (registration via
`./scripts/registration_sites.py` — never a hand-list — plus Containerfile COPY + the
in-image conformance `EXPECTED_MEMBERS` guard); (b) in the `dndlorescraper` repo, installed
into a variant image; (c) a new repo. **Recommendation: (a) to start** — it keeps the
shakedown cruise inside the repo whose gates and pins can see it, and extraction to its own
repo later is mechanical once the seams are proven. The scraper repo keeps owning the
*corpus*; lore's extension owns the *reading* of it.

## 7. The trust posture of the D&D tools (Consumer Law, applied forward)

- `dnd_get_spell("Fireball")` legitimately returns one row per book that ships the name. A
  render that flattens that to "the spell" over-claims; it names the book/edition, or names
  that it picked one and why (default-to-Core is a fine policy *if stated in the render*).
- List answers state their bound: "21 spells — PHB 2024" is a whole-set claim only because
  ingest carries the two-source oracle pin; that derivation is what licenses the count.
- The five code-only generic tools are OFF in the instance config — the false-clear
  argument in §2 is written into the allowlist rationale.
- Forgery pins (trust Leg 2) for the domain tools derive their failure set from the store
  dependencies × {stale, empty, wrong-instance, partial} at build time, per standing law.

## 8. Immediate follow-ups surfaced by this scoping (independent of the A/B/C ruling)

1. **Three probed engine facts are candidates for `docs/reference/surrealdb-31-capabilities.md`**
   (its §2/§6/§7): the `FIELDS <array>.*` requirement + the silent-`[]` equality trap; the
   subquery-`FROM` wrong-granularity behaviour (false-include direction); the string-vs-int
   record-id literal mismatch. The instruments are verbatim in the archived graph report §7.
   Un-transcribed engine knowledge is the #107 failure mode — recommend folding these in at
   the next store-touching packet, or now.
2. The graph scout's probe scripts should be lifted into `scripts/` unchanged when packet 5
   builds the schema (they are its natural regression probes).
3. `refers`/`answers_to` still lack `ENFORCED`/`UNIQUE(in,out)` (ledgered, pending packet
   43) — a new domain graph must not copy that gap, hence ENFORCED-from-birth above.

## 9. Forks for the operator — recommendations only; none is ruled

| # | Fork | Recommendation |
|---|---|---|
| 1 | **A / B / C** | **C.** B is only right if lore's process weight must not touch D&D at all — and multi-user makes B the expensive path anyway. |
| 2 | Extension package home | in-repo workspace member first (§6). |
| 3 | D1 — `MCDM/tir` byte-identical pair | dedupe at ingest by `content_sha256` (free, already validated); keep `tir.md`. |
| 4 | D2 — 2014-vs-2024 same-name spells | **keep both editions**, keyed by frontmatter `edition` + `source_book` (already free); `spell:[source_book, slug]` composite ids make them distinct rows by construction. Serving default: Core/2024 unless the query names a book — stated in the render. |
| 5 | Edition-scoping of `class` nodes | one node per class name; edition/provenance lives on the spell row and the edge (`source_book`), not on the class. Revisit only if a 2014-vs-2024 class *feature* query ever materialises (named re-open trigger). |
| 6 | D3 — degraded 2014 stat blocks | defer monsters entirely to a later packet (spells are the proving ground); when monsters land, 2024-dialect first, 2014-dialect behind its own decision. |
| 7 | Edge-only class membership vs a `classes` array on `spell` | **edge-only** (single source of truth; the array's index spelling is the measured trap). |
| 8 | `ENFORCED` on `learnable_by` from birth | **yes** (probed working; the existing code graph's gap is a ledgered hazard, not a model). |
| 9 | Generic tools enabled on `lore-dnd` | the 6 + `lore_findings` (§2). |
| 10 | Capabilities-doc additions (§8.1) | fold in now — it is three rows and the receipts exist. |

## 10. Bounds of this proposal

All three scouts were read-only: no tests were run, no container started, and the
extension framework's "complete" verdict is a source read + 340 green tests, not a
production observation. The graph probes measured query *plans* on 4–7 rows, not latency at
corpus scale — every "fast" here means "correct access path", nothing more. The corpus
scout did not enumerate XGtE's 205K subclass file (the largest uncounted entity
population), the equipment/glossary entities, or 2014-dialect field completeness; its
report §9 states the full bound. Counts in this doc inherit their derivations from the
archived reports — anything without a derivation there should be treated as unchecked.
