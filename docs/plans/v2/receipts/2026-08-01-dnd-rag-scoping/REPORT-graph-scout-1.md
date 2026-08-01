# REPORT-graph-scout-1 — modelling a D&D rules graph in SurrealDB

brief-base v9 read

- **state:** done
- **deviations:** (1) The five probe scripts that establish this report's load-bearing claims are
  pasted VERBATIM in §7 rather than committed — I am read-only outside this file. A lead may lift
  them into `scripts/` unchanged; they take no arguments and drop their own namespace.
  (2) Three grep fallbacks, disclosed at §1.
- **Packages considered:** `surrealdb` (Python SDK 2.0.0, installed) — read `AsyncSurreal.query` /
  `RecordID` at `.venv/.../surrealdb/connections/async_ws.py` before using them; verdict **replace**
  (it is already the repo's driver, no hand-rolling proposed). No new mechanism is specified by this
  report — it recommends a SCHEMA, and the store access it assumes is `loremaster.store._txn`'s
  existing `execute_transaction` / `run_query` seams, not new code.
- **decisions-needed:**
  1. **Is class membership single-source-of-truth on the EDGE, or is a `classes` array kept too?**
     I recommend edge-only (§4.2); if the array is kept for render convenience it becomes a second
     source of truth AND its index must be spelled `FIELDS classes.*` (§3.1) — the obvious spelling
     is measurably useless.
  2. **Do `learnable_by`-style edges get `ENFORCED` from birth?** I recommend yes; note `refers` /
     `answers_to` still do NOT have it (§2.3), so "match the existing graph" and "match repo law"
     point opposite ways here.
- **receipt pointers:** §3.1 (the array-index trap, probe 1 Leg A) · §3.3 (the winning plan, probe 2
  G4a / probe 5 J1a) · §3.5 + §6.2 (two SILENT wrong-answer hazards, probes 3–4) · §4.3 (SurrealQL
  for the three target queries) · §5 (DDL) · §7 (instruments verbatim)

---

## 1. Capability check (brief-base §4)

Everything the brief demanded was reachable. Recorded honestly:

| demanded | actual |
|---|---|
| `Read ~/.claude/orchestration/brief-base.md` | done, first action; v9 |
| `docs/reference/surrealdb-31-capabilities.md` as required first read | read in FULL (909 lines), incl. §6 and the RELATE hazards. Cited throughout, never re-transcribed |
| lore tools via one ToolSearch | loaded; `lore_index` / `lore_search` / `lore_read` used. **Index currency checked first:** `last_sync` 552 s, watched root `/workspace` on branch `feat/surreal-unification` @ `a049118` = my HEAD, so graph-derived answers are current for this session |
| live probe on `ws://127.0.0.1:18000` only | 6 probes, each in its OWN throwaway namespace (`probe_dnd*_<uuid8>`), each `REMOVE NAMESPACE`d at the end. **`:18500` never opened** — the string does not appear in any probe. ⚠ Probe 1's first run CRASHED before its teardown and leaked `probe_dnd_9a8da673`; found by an `INFO FOR ROOT` sweep at exit and removed. Verified clean: no `probe_dnd*` namespace remains (survivors `lore_test` / `main` / `probe` / `probe_ns` are pre-existing, not mine). **A probe that can die before its teardown needs the sweep, not the intention** — worth copying by anyone probing this shared store |

**Grep fallbacks, said out loud** (dogfood protocol case (b), non-symbol textual seams — all three
are SurrealQL text inside string literals, which the symbol graph cannot key on):

1. `TYPE RELATION` across the source tree — to enumerate edge tables exhaustively.
2. `->`/`<-` **inside `SELECT`** strings — to establish the arrow-traversal count (§2.2). This one is
   the reason the report's central observation about lore exists; no symbol query could have asked it.
3. `UPSERT` in `graph_surreal.py` — to confirm name-row creation.

`lore_search` unscoped was noticeably dominated by the two vendor tiers (`surrealdb-docs`,
`surrealql-tests`) even for questions clearly about our own code; `tier="lore"` fixed it. Not filed as
friction — it is correct behaviour for a corpus-weighted ranker and the tier filter is the documented
remedy — but a brief that says "use lore first" should say "and scope the tier".

---

## 2. What lore already does with SurrealDB graph features

### 2.1 The tables: which are edges, which are plain

Derived from `surreal_schema.py` (`generate_graph_ddl`, `_define_relation_table`) and corroborated
against a live `INFO FOR DB` receipt at
`docs/plans/v2/receipts/2026-07-19-packet03/REPORT-audit-edge-preflight.md`.

| table | kind | endpoints | ENFORCED | UNIQUE(in,out) | own indexes |
|---|---|---|---|---|---|
| `code_node` | plain, SCHEMAFULL, **composite id** `[tier, file_path, qualified_name]` | — | — | — | `bare_name`, `qualified_name`, `(tier, file_path)` |
| `name` | plain, **SCHEMALESS**, id `name:<string>` | — | — | — | `value` (the prefix-reach index) |
| `refers` | `TYPE RELATION` | `IN code_node OUT name` | **no** | no | `src_file_path` |
| `answers_to` | `TYPE RELATION` | `IN code_node OUT name` | **no** | no | `(tier, file_path)` |
| `briefed` | `TYPE RELATION` | `IN agent OUT brief` | yes (`6f0e03a`) | **yes** | — |
| `to` | `TYPE RELATION` | `IN message OUT agent` | yes (`df59f76`) | yes | — |
| `blocks` | `TYPE RELATION` | `IN task OUT task` | yes, from birth | — | — |

So the code graph is **two node tables and two edge tables**, and the fleet/ledger graph adds three
more edges. Everything else in the store (`chunk`, `memory`, `trace`, `finding`, …) is plain records.

### 2.2 How the code graph is actually traversed — and this is the headline

**`lore_impact` / `lore_map` issue no SurrealQL of their own.** `impact.py` and `map.py` call only
`SurrealCodeGraph` methods (`references`, `tests_for`, `blast_radius`, `what_imports`,
`all_nodes`, `module_names_by_file`); the entire query surface lives in
`graph_surreal.py`. And in that surface:

> **Every read of the code graph is a plain `SELECT` against the edge table with a `WHERE` on
> `in` / `out`. There is not one arrow traversal in it.**

Representative, `SurrealCodeGraph._bare_name_answerers`:

```surql
SELECT VALUE in FROM answers_to WHERE out IN $names
```

and `what_imports` / `_reverse_neighbours` / `tests_for` / `references` are all the same shape over
`refers` (`SELECT VALUE in FROM refers WHERE out IN $names`, `SELECT src_tier, src_file_path FROM
refers WHERE …`). Multi-hop `blast_radius` is a **Python-side BFS**: `_reverse_neighbours` is called
once per depth level with the frontier bound as a parameter.

Arrows appear in exactly two places, both deliberate:

- **Writes** — 32 `RELATE` sites, e.g. `RELATE $src->refers->$dst SET kind = …` in
  `SurrealCodeGraph._edge_statement`.
- **One read**, `TaskLedger.transitive_blockers` in `tasks.py`, which is a genuine recursive path:
  `SELECT @.{1..$depth+collect}(<-blocks<-task).id …  TIMEOUT 5s`. This is the only native traversal
  in the repo, and it exists because the question (transitive upstream reach over a DAG) is one a
  fixed-shape `WHERE` cannot express.

That split is the most useful thing lore's own experience has to say about the D&D question, and §4
leans on it directly: **arrows earned their place for unbounded recursion and nothing else.**

### 2.3 Is the substrate reusable for an arbitrary domain?

**The patterns are; the code is not.** There is no generic domain-graph API — `code_node`, `name`,
`refers`, `answers_to` are module-level constants, the columns are hardcoded in both the SurrealQL
and the decoder (`_COL_*` / `_EDGE_*` in `graph_surreal.py`, deliberately shared "so a rename can
never silently desynchronise the query from the reader"), and `SurrealCodeGraph` is welded to astroid
derivation via `_AstroidDerivation`. A D&D graph would be a **sibling schema slice**, not an instance
of this one.

What transfers, and should:

1. **Deterministic composite record ids** so a re-ingest targets the SAME row
   (`code_node:[tier, file_path, qname]` → e.g. `spell:[source_book, slug]`). Idempotent by
   construction, and collision-correct across tiers/books.
2. **Denormalised SCOPE columns on the edge** (`refers.src_tier` / `src_file_path`) purely so a
   re-ingest can delete a slice of edges by scope **without traversing**. Directly reusable for
   per-book re-scrapes (§6.1).
3. **A `name` side-table carrying its own id-string as an indexed `value` column**, because
   *"you cannot index or prefix-match a RecordID's string component"* (capabilities §2). Any
   prefix/fuzzy reach over spell names needs this same trick.
4. **The declare-before-first-write rule** — capabilities §5: an undeclared edge table is
   auto-created `TYPE ANY`, silently discarding the `IN`/`OUT` guard.
5. **Edge-table-as-plain-table reads** — which §3.3 shows is also the *fastest* shape for the target
   queries, so this is not merely a habit to copy.

⚠ **One thing NOT to copy:** `refers` and `answers_to` carry neither `ENFORCED` nor `UNIQUE(in,out)`.
Capabilities §8 records them as *"unguarded pending packet 43"* — i.e. a known open hazard, not a
model. A new domain graph should be born with both (§5).

---

## 3. Verified engine capabilities for this workload

Engine **surrealdb-3.2.1** (`spike-surreal`), all probes **2026-08-01**. Provenance tags follow the
capabilities doc's legend. Where an answer is mine alone, it says so.

**Bound, stated up front: these are QUERY PLANS, not timings.** Every probe ran on 4–7 spell rows.
`EXPLAIN` tells you which access path the planner *chooses*, which is what a schema decision needs;
it tells you nothing about behaviour at 5,000 spells. No latency claim appears in this report, and
any that a reader infers is theirs, not mine.

### 3.1 Indexing an `array<string>` — the trap that decides design (ii)

Neither the capabilities doc nor the vendor's index pages address a **flat** array field. The CI spec
`tests/language/statements/create/create_with_std_index_with_flattened_field_new_executor.surql`
(tier `surrealql-tests`, v3.2.0) covers only a NESTED path (`marks.*.mark`), where it establishes
`40 INSIDE marks.*.mark` → `IndexScan` but `marks.*.mark = 40` → `TableScan (unsupported predicate)`.
Generalising that to a flat array would be a quantifier error, so I measured it (probe 1, Leg A):

| index definition | predicate | plan | rows |
|---|---|---|---|
| *(none)* | `'druid' INSIDE classes` | TableScan | 6 ✅ |
| **`FIELDS classes`** | `'druid' INSIDE classes` | **TableScan** | 6 ✅ |
| **`FIELDS classes`** | `classes CONTAINS 'druid'` | **TableScan** | 6 ✅ |
| **`FIELDS classes`** | `classes CONTAINSANY ['druid']` | **TableScan** | 6 ✅ |
| **`FIELDS classes`** | `classes = 'druid'` | **IndexScan** | **`[]`** ⚠ |
| **`FIELDS classes.*`** | `'druid' INSIDE classes` | **IndexScan** | 6 ✅ |
| **`FIELDS classes.*`** | `classes CONTAINS 'druid'` | **IndexScan** | 6 ✅ |
| **`FIELDS classes.*`** | `'druid' INSIDE classes.*` | **IndexScan** | 6 ✅ |

**[PROBED 2026-08-01, 3.2.1 — WE ARE THE ONLY SOURCE.]** Two facts worth their own lines:

- **`DEFINE INDEX … FIELDS classes` on an `array<string>` is USELESS for containment.** It indexes
  the array as ONE key. Every containment spelling full-scans. The obvious definition is the wrong one.
- **The one spelling it *does* accelerate returns the wrong answer.** `WHERE classes = 'druid'`
  IndexScans and yields `[]` — no error, no warning. A developer who writes the natural-looking
  index and the natural-looking equality gets a fast, empty, silently wrong result. The `[]` is not
  "index missing": the plan proves the index fired.
- The fix is one character-pair: **`FIELDS classes.*`** — the element path — after which all three
  containment spellings IndexScan and return correct rows.

Positive control for the whole leg: the no-index baseline TableScans, so the IndexScans in rows 6–8
are a real change of access path, not a constant.

### 3.2 Composite indexes: leading-column only

**[PROBED 2026-08-01, 3.2.1]** Measured twice, on an element-path composite (probe 2 G2) and again on
a plain scalar composite (probe 6 K4–K6), because generalising from the first alone would repeat the
quantifier error:

| index | predicate | plan |
|---|---|---|
| `FIELDS classes.*, level` | `'druid' INSIDE classes AND level = 4` | IndexScan `access: ['druid']` **+ Filter `level = 4`** |
| `FIELDS classes.*, level` | `'druid' INSIDE classes` (leading only) | IndexScan |
| `FIELDS classes.*, level` | `level = 4` (trailing only) | **TableScan** |
| `FIELDS name, source_book UNIQUE` | `name = 'Fireball'` (leading only) | IndexScan `access: ['Fireball']` |
| `FIELDS name, source_book UNIQUE` | both columns | IndexScan |
| `FIELDS name, source_book UNIQUE` | `source_book = 'PHB'` (trailing only) | **TableScan** |

Consequence used in §5: **one** `UNIQUE(name, source_book)` index serves BOTH the cross-book
uniqueness constraint AND the exact-name lookup. Control: the duplicate `('Fireball','PHB')` insert
is rejected naming the index and the existing record, while `('Fireball','XGE')` is admitted.

Also **[PROBED]**: a composite over an array element path is **legal** (`FIELDS classes.*, level`
defines without error), and the planner uses only its leading column for access.

### 3.3 Graph traversal — syntax, and what it costs

Syntax is settled by the engine's own CI-verified specs (tier `surrealql-tests`, v3.2.0), so no probe
was needed to establish the FORMS — only to confirm them on 3.2.1:

- `tests/reproductions/7155_parent_in_graph_traversal_filter.surql` establishes all three filter
  shapes: node-side `id->visible->(tag WHERE name IN $parent.visibility.tags)`, edge-side bracket
  `->visible[WHERE out.name IN $parent.visibility.tags]`, and a chained
  `->…->(tag WHERE …)<-…<-(contact WHERE active)`. `$parent` resolves inside a traversal WHERE.
- `tests/language/idiom/graph_filter_flattened.surql` establishes the `[?predicate]` post-filter form
  and result flattening.
- `<->edge<->table` traverses both directions ([VENDOR], `learn/data-models/graph/graph-traversal.mdx`).
- Recursive paths `@.{n}` / `@.{1..n}` / `@.{..}`, cap 256, are capabilities §4.

**[PROBED 2026-08-01, 3.2.1]** All confirmed working on 3.2.1 (probe 1 D3–D6, probe 3 H1–H6,
probe 5 J3). And the load-bearing plan fact:

> **A traversal NEVER uses a secondary index.** Every traversal plan is `GraphEdgeScan` from the
> start record, with any filter applied as a `predicate` on the scanned rows. Probe 5 J4 asserts it
> explicitly: with `spell_level` defined, the string `spell_level` does **not** appear in the plan for
> `SELECT VALUE <-learnable_by<-(spell WHERE level = 4).name FROM class:druid`.

That is not a defect — a traversal is already bounded by the start node's degree, which is usually
what you want. But it means **you cannot index your way out of a traversal**, and it is why §4 keeps
the scalar filters on an indexable path.

Against that, the **edge table read as a plain table** is fully indexable
(**[PROBED]**, probe 2 G4a / probe 5 J0–J2):

| query | index present | plan |
|---|---|---|
| `… FROM learnable_by WHERE out = class:druid AND in.level = 4` | none | **TableScan** over the whole edge table |
| same | `FIELDS out` | **IndexScan** `access: = class:druid` + Filter `in.level = 4` |
| `… WHERE out = class:druid AND level = 4` *(level denormalised onto the edge)* | `FIELDS out, level` | **IndexScan** `access: [class:druid, 4]`, no Filter |

The first two rows are each other's control: the index is what changes the access path.

### 3.4 UNIQUE and ENFORCED on edges — confirmed on 3.2.1, with controls

Capabilities §4 settles both for our floor. Re-confirmed here because this design leans on them
(probe 1 D0b/D2/D2b, probe 2):

- `DEFINE INDEX … ON learnable_by FIELDS in, out UNIQUE` — legal. Control: a duplicate `RELATE`
  raises `Database index 'learnable_by_in_out' already contains [spell:fireball, class:wizard]`.
- `DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL` —
  legal, and a bogus endpoint raises `The record 'class:artificer_ghost' does not exist`.
- Indexes on **edge fields** are legal, including composites mixing `out` with a data column
  (`FIELDS out, level`, `FIELDS out, ritual`).
- **Endpoint delete cascades the edges.** Probe 1 Leg E: 15 edges → `DELETE spell:blight` → 13, and
  `SELECT … FROM learnable_by WHERE in = spell:blight` → `[]`. Matches [VENDOR] + capabilities §2.

### 3.5 Full-text, and one thing that is NOT full-text's job

**[PROBED 2026-08-01, 3.2.1]** `DEFINE ANALYZER … TOKENIZERS class FILTERS lowercase,ascii` +
`DEFINE INDEX … FIELDS body FULLTEXT ANALYZER rules_txt BM25` works, and `WHERE body @@ 'thing'`
matches. **A FULLTEXT index is single-column** — `FIELDS name, body FULLTEXT …` is a parse error
(*"Expected one column, found 2"*), which the CI spec
`tests/parsing/errors/define_index_fulltext_multiple_fields.surql` also pins.

For TARGET-3 (`"Fireball"` → the record), full-text is the **wrong instrument**: exact-name lookup
wants the B-tree (§3.2 K4, `IndexScan access: ['Fireball']`). Full-text belongs on rules *prose*
(`body`), beside the existing HNSW/BM25 chunk substrate — a different query than "give me this spell".

⚠ **And a live analyzer hazard inherited from the store, not created here:** capabilities §8 records
`DEFINE ANALYZER IF NOT EXISTS` silently ignoring a changed tokenizer/filter set, with the correct
migration being `OVERWRITE` **+ `REBUILD INDEX`**. A rules corpus is exactly the kind of thing whose
analyzer gets tuned twice in the first month. Whoever tunes it must read §1.5 first.

---

## 4. Modelling recommendation

### 4.1 The three candidates, judged

| | (i) pure graph — level/ritual as EDGE HOPS or nodes | (ii) plain records + indexes, no edges | (iii) **hybrid: edge for membership, fields for attributes** |
|---|---|---|---|
| TARGET-1 plan | GraphEdgeScan(s), never indexed (§3.3); level-as-node needs a nested traversal predicate | IndexScan on `level` **+ Filter** on containment, or IndexScan on `classes.*` + Filter on level (§3.2) | **IndexScan on the edge's `out`, bounded to druid, + a cheap per-edge Filter** (§3.3) |
| "what classes cast X" | native, one hop | re-read the array | native, one hop |
| class hierarchy / subclass, "monsters that cast X", "items granting X" | native and the only sane option | needs a join table per relationship, hand-rolled | native |
| re-ingest bookkeeping | edges must be purged/rebuilt per book | none — one row replace | edges purged by scope (§6.1) |
| ways to be silently wrong | most (§3.5, §6.2, §6.3) | one, and it is severe (§3.1) | fewest |

**Recommend (iii).** The dividing line is not "graph vs relational" — it is
**RELATIONSHIP vs ATTRIBUTE**:

> **A thing that connects two entities that both have their own identity, their own attributes, and
> their own inbound questions, is an EDGE. A thing that is one scalar value belonging to one entity
> is a FIELD.**

`class` passes every clause: it has a name, it will grow attributes (spell list progression, ritual
casting rules, subclasses), and other entities will point at it. `level` passes none — "level 4" has
no attributes, nothing else ever points at it, and no query ever walks *from* a level to anything but
the spells that have it.

### 4.2 The brief's direct question: is `Spells->Druid->Level-4` an edge hop?

**No. `level` is a FIELD with an index, and `ritual` likewise.** Reasons, in the order that they
matter:

1. **The hop cannot be indexed and the field can.** §3.3: every traversal is a `GraphEdgeScan` and
   provably ignores a defined index (probe 5 J4). Making level a hop converts an indexable predicate
   into an un-indexable one — the opposite of the intent.
2. **It buys no query.** A level node has no attributes and no other inbound relationships. The only
   question it answers is the one a `WHERE level = 4` already answers.
3. **It costs an ingest write per spell, plus cascade bookkeeping**, plus a second table.
4. **Measured: it is the shape people get wrong.** My *own* first attempt at level-as-a-node returned
   `[]` — silently — because `RecordID("slevel", "4")` (SDK, string id) and the SurrealQL literal
   `slevel:4` (integer id) are **different records** (§6.3). A control leg caught it. The
   *equivalent field filter has no such failure mode*, and a modelling choice that makes a whole class
   of silent bug reachable is worse than one that does not, even at equal expressiveness.

For the record, once the id types are made consistent, level-as-a-node **does** work — probe 3
H1–H4 return the correct three spells via `spell WHERE ->has_level->slevel CONTAINS slevel:4`. So
this is a cost/benefit ruling, not a feasibility one, and it should not be re-litigated as though the
engine were the obstacle.

**Where edges genuinely pay** — and these are the reasons to build the edge table now rather than
retrofit it:

- **Multi-hop:** "spells my subclass grants at level 3" = `character->has_class->class->grants->spell`.
- **Inheritance:** `subclass->specialises->class`, then a druid-circle's spells are the union over a
  one-hop walk — the recursive `@.{1..n}` form, the *one* thing lore already uses arrows for (§2.2).
- **Reverse questions over a large fan-in:** "monsters that cast Fireball", "items that grant it",
  "which classes get it" — each is a new edge table and zero changes to `spell`. In model (ii) each is
  a new array column, a new `.*` index, and a new chance to write `FIELDS classes` by mistake.
- **Provenance on the relationship itself:** "the druid gets this at level 3 *from Circle of the
  Land*" is a property of the *edge*, and has nowhere to live in model (ii).

### 4.3 The three target queries, under the recommendation

All three measured (probe 5, plans in §3.3 / §3.2).

**TARGET-1 — all Druid spells of level 4.** Read the edge table as a plain table:

```surql
SELECT VALUE in.* FROM learnable_by
WHERE out = class:druid AND in.level = 4;
```
Needs: `learnable_by` edge table + `DEFINE INDEX lb_out ON learnable_by FIELDS out`.
Plan: `IndexScan [index: lb_out, access: = class:druid] → Filter [in.level = 4]`. Returns a **flat**
list. Without `lb_out` the same query TableScans the whole edge table — that pairing is the control.

The traversal spelling returns the same rows and is fine to serve when you want the nesting:

```surql
SELECT VALUE <-learnable_by<-(spell WHERE level = 4) FROM class:druid;
```
Plan: `GraphEdgeScan … predicate: level = 4`. ⚠ It returns **`[[…]]`** — one array per start record —
where the edge-table form returns a flat list. For an LLM-facing render, prefer the flat one; a
nested-array-of-one is exactly the shape that gets mis-decoded.

**TARGET-2 — all Druid ritual spells.** Identical shape; only the predicate changes:

```surql
SELECT VALUE in.* FROM learnable_by
WHERE out = class:druid AND in.ritual = true;
```
Needs: the same `lb_out` index. Plan: `IndexScan [lb_out] → Filter [in.ritual = true]`. Measured rows:
`['Water Breathing', 'Detect Magic']`.

**TARGET-3 — exact name → full record, with its classes:**

```surql
SELECT *, ->learnable_by->class.name AS classes
FROM spell
WHERE name = $name;
```
Needs: `DEFINE INDEX spell_name_book ON spell FIELDS name, source_book UNIQUE` — the leading column
serves this lookup (§3.2). Plan:
`IndexScan [spell_name_book, access: ['Fireball']] → Compute [classes = ->learnable_by->class.name]`.
⚠ **This returns one row PER BOOK** that ships a spell of that name (§6.4) — which is correct, and is
a thing the render must not flatten into "the" Fireball.

**Do I need a denormalised `level` on the edge?** Measured both (§3.3): denormalising gets a single
`IndexScan access: [class:druid, 4]` with no Filter, against `IndexScan access: = class:druid` +
Filter. **Recommend NOT denormalising**: the second copy of every spell's level is a divergence
hazard forever, the `out`-index already bounds the scan to one class's edges, and at 5–7 rows I have
**no evidence** the Filter costs anything. If a measurement later shows the Filter hurts, add
`FIELDS out, level` **and** an invariant test that the edge's copy equals the spell's — never the
index alone. That is a measure-then-tune deferral with a named decision point: *the first p50 on
TARGET-1 over the real corpus.*

---

## 5. Schema DDL sketch

Under the repo's migration law: **FIELD → `OVERWRITE`; plain TABLE / INDEX / ANALYZER →
`IF NOT EXISTS`; RELATION TABLE → `OVERWRITE`** (capabilities §1.1 — note the RELATION row INVERTS
the table rule, because `IF NOT EXISTS` is a measured silent no-op for a changed `IN`/`OUT`/`ENFORCED`).
`ALTER` appears nowhere (§1.3). Emit via `execute_transaction`, never a multi-statement `query()` (§3).

```surql
-- ---------- nodes ----------
DEFINE TABLE IF NOT EXISTS class SCHEMAFULL;
DEFINE FIELD OVERWRITE name ON class TYPE string;

DEFINE TABLE IF NOT EXISTS spell SCHEMAFULL;
DEFINE FIELD OVERWRITE name        ON spell TYPE string;
DEFINE FIELD OVERWRITE slug        ON spell TYPE string;
DEFINE FIELD OVERWRITE source_book ON spell TYPE string;
DEFINE FIELD OVERWRITE level       ON spell TYPE int  ASSERT $value >= 0 AND $value <= 9;
DEFINE FIELD OVERWRITE school      ON spell TYPE string;
DEFINE FIELD OVERWRITE ritual      ON spell TYPE bool;
DEFINE FIELD OVERWRITE body        ON spell TYPE string;

-- ONE composite serves BOTH cross-book uniqueness AND the exact-name lookup
-- (leading-column access — measured, §3.2). Order matters: name FIRST.
DEFINE INDEX IF NOT EXISTS spell_name_book ON spell FIELDS name, source_book UNIQUE;
DEFINE INDEX IF NOT EXISTS spell_level     ON spell FIELDS level;
DEFINE INDEX IF NOT EXISTS spell_ritual    ON spell FIELDS ritual;

-- ---------- the edge ----------
-- OVERWRITE, not IF NOT EXISTS: capabilities §1.1's RELATION row.
-- ENFORCED from birth: it is the only guard that closes the INSERT RELATION door
-- (§4), and it guards BOTH endpoints.
DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL;
DEFINE FIELD OVERWRITE source_book ON learnable_by TYPE string;   -- the re-ingest PURGE key
DEFINE FIELD OVERWRITE via         ON learnable_by TYPE option<string>;  -- "Circle of the Land"

DEFINE INDEX IF NOT EXISTS lb_in_out      ON learnable_by FIELDS in, out UNIQUE;
DEFINE INDEX IF NOT EXISTS lb_out         ON learnable_by FIELDS out;          -- TARGET-1/2
DEFINE INDEX IF NOT EXISTS lb_source_book ON learnable_by FIELDS source_book;  -- §6.1

-- ---------- rules prose ----------
DEFINE ANALYZER IF NOT EXISTS rules_txt TOKENIZERS class FILTERS lowercase, ascii;
DEFINE INDEX IF NOT EXISTS spell_body_ft ON spell FIELDS body FULLTEXT ANALYZER rules_txt BM25;
```

Notes on choices a reviewer should be able to challenge:

- **`spell` record id should be the composite `spell:[source_book, slug]`**, mirroring
  `code_node:[tier, file_path, qname]` (§2.3): re-ingest of a book targets the same rows, and two
  books' Fireball are two rows by construction rather than by an index rejection. Composite `[a,b]`
  ids are supported (capabilities §10).
- **`option<>` on `via` is deliberate.** A NEW non-`option` field on a POPULATED table poisons every
  existing row and a `DEFAULT` does **not** rescue it (capabilities §1.4/§6.2). Every field added
  after first ingest must be `option<>`.
- **`ritual` is indexed even though it is a 2-value column.** Justified only by TARGET-2 being a named
  target query; on a low-cardinality bool the index earns little and a reviewer may reasonably cut it.
  Measured: with it, TARGET-2's field-only form IndexScans; the edge-table form in §4.3 does not use
  it at all. **If TARGET-2 is only ever asked per-class, drop `spell_ritual`.**
- **No `classes` array.** If the operator rules otherwise (decision 1), it needs
  `DEFINE FIELD OVERWRITE classes[*] ON spell TYPE string` **and**
  `DEFINE INDEX … ON spell FIELDS classes.*` — the `.*`, per §3.1 — plus something that keeps it
  equal to the edges.

---

## 6. Hazards

### 6.1 Re-ingest — the two failure modes, both measured (probe 1 Leg E)

A corpus re-scrape either replaces rows or updates them, and **both directions corrupt the graph if
edges are not handled explicitly**:

- **DELETE+CREATE loses the edges silently.** `DELETE spell:blight` cascaded its 2 edges away
  (15 → 13, confirmed by [VENDOR] + capabilities §2). Re-`CREATE`ing the row does **not** bring them
  back: measured, TARGET-1 then returned `['Confusion','Grasping Vine']` — Blight, a level-4 druid
  spell that exists in the store, was **absent from its own answer, with no error anywhere**. Any
  re-ingest that replaces rows MUST re-`RELATE` in the same transaction.
- **UPDATE keeps STALE edges.** `UPDATE spell:confusion SET classes = ['druid','bard']` (dropping
  warlock) left all three edges in place: `[bard, druid, wizard]`. An UPSERT-style re-ingest silently
  accumulates memberships that the source no longer claims.

**Mitigation, and it is lore's own:** carry the scope on the edge (`learnable_by.source_book`, exactly
`refers.src_file_path`) and make re-ingest of a book **purge-then-rebuild in ONE transaction**:

```surql
DELETE learnable_by WHERE source_book = $book;   -- then re-RELATE every membership
```
Verified purge-by-scope works and the answer follows it: probe 5 J6 deleted one spell's edges and
TARGET-1 correctly dropped from 3 rows to 2.

### 6.2 ⚠ NEW, and the sharpest thing in this report: a WHERE over a subquery-FROM is evaluated at the WRONG GRANULARITY

**[PROBED 2026-08-01, 3.2.1 — WE ARE THE ONLY SOURCE. Not in the capabilities doc, not in the vendor
docs, not in the CI specs I searched.]** Probe 4, with controls in both directions:

```surql
-- 4 druid spells exist: Blight(4), Confusion(4), Grasping Vine(4), Cure Wounds(1)
SELECT VALUE name FROM (SELECT VALUE <-learnable_by<-spell FROM ONLY class:druid)
  WHERE ->has_level->slevel CONTAINS slevel:4;
--> ['Grasping Vine','Confusion','Cure Wounds','Blight']   ⚠ Cure Wounds is LEVEL 1
```

| leg | result | what it proves |
|---|---|---|
| subquery FROM, no WHERE | 4 names | baseline |
| `WHERE level = 4` (plain field) | **`[]`** | a field predicate excludes EVERYTHING |
| `WHERE ->has_level->slevel CONTAINS slevel:4` | **all 4, incl. level 1** | a traversal predicate includes everything |
| `WHERE level = 999` (impossible field) | `[]` | consistent with row 2 |
| `WHERE …CONTAINS slevel:1234` (impossible traversal) | `[]` | consistent with row 3 |
| same traversal predicate, **no** subquery FROM | correct 3 | the predicate itself is fine |
| non-`ONLY` subquery | same wrong 4 | not an `ONLY` artefact |

The mechanism is in the plan: the subquery yields an **array of RecordIDs**, `UnwrapExactlyOne` makes
the outer `FROM` a **single value**, and the predicate is evaluated **once over the whole array**
instead of per record. So the filter is all-or-nothing: a field predicate finds no `level` on an
array and drops everything; a traversal predicate flattens across every member and keeps everything.

**Both directions are silently wrong and neither raises.** A false-empty is survivable; the
false-INCLUDE is a trust-doctrine defect — a "level 4 druid spells" answer containing a level-1 spell,
served with no bound and no error.

**Rule to carry into the build:** *never put a traversal-producing subquery in a `FROM`.* Use the
node-side parenthesised filter (`<-edge<-(spell WHERE …)`) or the edge-table `SELECT` in §4.3 — both
measured correct. This deserves a repo-local pin the day any code goes near the shape.

### 6.3 ⚠ NEW: an SDK-minted string id and a SurrealQL integer id literal are DIFFERENT records, and the mismatch reads as empty

**[PROBED 2026-08-01, 3.2.1 — ours alone.]** `RecordID("slevel", "4")` stores id `'4'` (a string).
The SurrealQL literal `slevel:4` names id `4` (an integer). Measured: with the row present,
`SELECT * FROM slevel:4` → **`[]`**; and `slevel:'4'` is a **parse error**
(*"Unexpected token `a strand`, expected an identifier"*), so the naive escape hatch is closed too.

This cost me a wrong conclusion mid-probe: I nearly reported "nested traversal filters return empty
on 3.2.1" as an engine bound. It was my ids. **Only the positive control caught it** — capabilities
§4 records the identical rescue on the RELATE probe, and §7's `str(record.id)` row is this hazard's
sibling (uuid-shaped ids), but the **int-vs-string id literal** face of it is not written down
anywhere I can find. Any ingest that mints numeric-looking ids (levels, CRs, page numbers, editions)
walks straight into it. Prefer non-numeric slugs, or bind the `RecordID` as a parameter and never
write the literal.

### 6.4 Name collisions across books and editions

**[PROBED]** `UNIQUE(name)` alone **rejects the second book's Fireball**:
`Database index 'bk_name' already contains 'Fireball', with record 'spellbk:a'` — i.e. the naive
uniqueness constraint makes a legitimate multi-source corpus *unloadable*, loudly, at ingest.
`UNIQUE(name, source_book)` admits both (§3.2) and still rejects a true duplicate.

Consequences the design must own rather than discover:
- **TARGET-3 is not single-valued.** `WHERE name = 'Fireball'` legitimately returns N rows. A render
  that says "the spell" over an N-row result is over-claiming; it must name the book, or name the
  fact that it picked one. Same class as the trust-doctrine label/set rule in this repo's CLAUDE.md.
- **`class:druid` is edition-scoped too.** A 2014 druid and a 2024 druid are arguably different
  entities. Unresolved here, and it is a design question, not a scout's: **surfaced for the operator.**

### 6.5 Dangling edges and the traversal that cannot see them

Capabilities §4 + §6.4: `RELATE` does **not** validate either endpoint, a ghost appears in the
identity traversal as a **first-class member**, and the vendor's "returns an empty array" sentence is
FALSE as a reader would apply it. For this design the dangerous half is caller-supplied: an ingest
that maps a scraped class string to `class:<slug>` will happily `RELATE` to `class:atrificer`.
**Mitigation: `ENFORCED` from birth** (§5) — measured rejecting `class:artificer_ghost` — *plus* an
app-level check, because `ENFORCED` reports ONE bad endpoint as untyped prose only after the write is
attempted, aborting the transaction (capabilities §4's error-ergonomics row). Neither is redundant.

⚠ And `ENFORCED` does **not** clean up pre-existing dangling edges — capabilities §4 calls turning it
on and declaring the ghost problem closed *"a false all-clear"*. Adopting it on a populated table is
`OVERWRITE` (never `IF NOT EXISTS`) plus a separate data migration.

### 6.6 Multi-hop truncates SILENTLY at 256

If subclass inheritance or "granted by" chains ever become recursive walks: the engine truncates at
its recursion ceiling **with no error and no signal** — measured 256 of 299 nodes, receipt
`docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-probe-pkt04-store.md` §5.3. The in-repo answer is
worth copying wholesale: `TaskLedger.transitive_blockers` runs the SAME statement at `depth` **and**
`depth + 1` and compares the two reaches, so truncation is **measured, never inferred** — plus a
`TIMEOUT` and a client-side depth guard (`ENGINE_RECURSION_CEILING = 256`,
`TASK_BLOCKER_MAX_DEPTH = 32` in `tasks.py`). A rules graph that walks inheritance without that pair
will serve a truncated answer as a complete one.

### 6.7 Smaller, still real

- **Declare every table before first write** (capabilities §5): an undeclared edge table is
  auto-created `TYPE ANY`, **silently discarding the `IN`/`OUT` guard**, and undeclared tables storm
  with retryable conflicts on concurrent first-write.
- **A dedupe before the RELATE loop** — `UNIQUE(in, out)` makes a repeated membership a loud ERR
  (measured §3.4), and a scraped class list can repeat. The index is a backstop, not a de-duplicator.
- **`SELECT *` omits a `NONE`-valued column entirely** → `KeyError`, the opposite of the
  missing-projection-reads-`None` rule (capabilities §2/§6.6 #12). Every `option<>` field here
  (`via`) means readers must not assume presence.
- **`UPDATE` of an edge's `in`/`out` is a silent no-op** (capabilities §2) — to re-point a membership,
  DELETE and re-`RELATE`.
- **`REMOVE TABLE` + re-`DEFINE` in one transaction** can conflict with an async index build; do it in
  two steps under a lock (capabilities §1.7). Relevant to any "reload the whole corpus" verb.

---

## 7. Instruments (verbatim — brief-base §1)

Five probe scripts. Each opens its own throwaway namespace on the **test** store and `REMOVE
NAMESPACE`s it at the end; none writes to the repo; none references `:18500`. Run with
`uv run python <file>` from the repo root. **Recommend a lead commit these to `scripts/` unchanged** —
I could not, being read-only. Probe 6 is the composite-index leg (§3.2 K-rows).

Note probe 1 was patched mid-run after `AlreadyExistsError: The database 'rules' already exists`:
`db.use(NS, DB)` **auto-creates** the database, so the explicit `DEFINE DATABASE` raises. The version
below is the corrected one.

<details><summary>probe 1 — array-index trap, name lookup, ENFORCED/UNIQUE controls, cascade, full-text</summary>

```python
"""Probe: how should a D&D rules graph be modelled in SurrealDB 3.2.1?

Read-only w.r.t. the repo. Runs against the TEST store (spike-surreal
ws://127.0.0.1:18000/rpc) in a THROWAWAY namespace+database, dropped at the end.
NEVER :18500 (production lore-surreal).

Every leg pairs its result with a POSITIVE CONTROL (a case we know is broken /
known-good) so a negative result cannot come from a blind instrument.
One statement per query() call — store reference §3 (query() validates
statement[0] only, so a multi-statement string hides later failures).
"""
import asyncio, uuid
from surrealdb import AsyncSurreal, RecordID

URL = "ws://127.0.0.1:18000/rpc"
USER, PASS = "root", "spikeroot"
NS = f"probe_dnd_{uuid.uuid4().hex[:8]}"
DB = "rules"

async def q(db, stmt, params=None):
    try:
        return await db.query(stmt, params or {})
    except Exception as exc:  # noqa: BLE001 - the probe reports failures verbatim
        return f"!! {type(exc).__name__}: {exc}"

def plan(result):
    """Squeeze an EXPLAIN result down to the scan kind + index name."""
    text = str(result)
    for token in ("IndexScan", "TableScan", "CountScan", "Iterate"):
        if token in text:
            return token, text
    return "?", text

async def main():
    db = AsyncSurreal(URL)
    await db.signin({"username": USER, "password": PASS})
    await db.query(f"DEFINE NAMESPACE {NS}")
    await db.use(NS, DB)          # NOTE: use() AUTO-CREATES the database.
    out = []
    P = out.append

    # ---------- schema: plain-record model (design ii) ----------
    P(("DDL spell table", await q(db, "DEFINE TABLE IF NOT EXISTS spell SCHEMAFULL")))
    for name, typ in (
        ("name", "string"), ("level", "int"), ("school", "string"),
        ("ritual", "bool"), ("classes", "array<string>"), ("body", "string"),
    ):
        await q(db, f"DEFINE FIELD OVERWRITE {name} ON spell TYPE {typ}")
    await q(db, "DEFINE FIELD OVERWRITE classes[*] ON spell TYPE string")

    # ---------- data ----------
    rows = [
        ("fireball",     "Fireball",      3, "evocation",    False, ["wizard", "sorcerer"]),
        ("blight",       "Blight",        4, "necromancy",   False, ["druid", "warlock"]),
        ("confusion",    "Confusion",     4, "enchantment",  False, ["druid", "bard", "wizard"]),
        ("grasping_vine","Grasping Vine", 4, "conjuration",  False, ["druid"]),
        ("detect_magic", "Detect Magic",  1, "divination",   True,  ["druid", "cleric", "wizard"]),
        ("water_breath", "Water Breathing", 3, "transmutation", True, ["druid", "ranger"]),
        ("cure_wounds",  "Cure Wounds",   1, "evocation",    False, ["druid", "cleric"]),
    ]
    for rid, nm, lvl, sch, rit, cls in rows:
        await q(db,
            "CREATE $id CONTENT { name: $name, level: $level, school: $school, "
            "ritual: $ritual, classes: $classes, body: $body }",
            {"id": RecordID("spell", rid), "name": nm, "level": lvl, "school": sch,
             "ritual": rit, "classes": cls, "body": f"{nm} does a thing."})

    # ================= LEG A: flat array<string> index =================
    P(("A0 no-index baseline: 'druid' INSIDE classes",
       plan(await q(db, "EXPLAIN SELECT name FROM spell WHERE 'druid' INSIDE classes"))[0]))
    P(("A1 DEFINE INDEX FIELDS classes", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell_classes ON spell FIELDS classes")))
    for label, stmt in (
        ("A1a 'druid' INSIDE classes", "SELECT name FROM spell WHERE 'druid' INSIDE classes"),
        ("A1b classes CONTAINS 'druid'", "SELECT name FROM spell WHERE classes CONTAINS 'druid'"),
        ("A1c classes = 'druid'", "SELECT name FROM spell WHERE classes = 'druid'"),
        ("A1d classes CONTAINSANY ['druid']", "SELECT name FROM spell WHERE classes CONTAINSANY ['druid']"),
    ):
        P((f"{label} PLAN", plan(await q(db, f"EXPLAIN {stmt}"))[0]))
        P((f"{label} ROWS", await q(db, stmt)))

    # the .* variant, on a second table so the two indexes can't be confused
    await q(db, "DEFINE TABLE IF NOT EXISTS spell2 SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE name ON spell2 TYPE string")
    await q(db, "DEFINE FIELD OVERWRITE classes ON spell2 TYPE array<string>")
    await q(db, "DEFINE FIELD OVERWRITE classes[*] ON spell2 TYPE string")
    for rid, nm, lvl, sch, rit, cls in rows:
        await q(db, "CREATE $id CONTENT { name: $name, classes: $classes }",
                {"id": RecordID("spell2", rid), "name": nm, "classes": cls})
    P(("A2 DEFINE INDEX FIELDS classes.*", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell2_classes_star ON spell2 FIELDS classes.*")))
    for label, stmt in (
        ("A2a .* idx: 'druid' INSIDE classes", "SELECT name FROM spell2 WHERE 'druid' INSIDE classes"),
        ("A2b .* idx: classes CONTAINS 'druid'", "SELECT name FROM spell2 WHERE classes CONTAINS 'druid'"),
        ("A2c .* idx: 'druid' INSIDE classes.*", "SELECT name FROM spell2 WHERE 'druid' INSIDE classes.*"),
    ):
        P((f"{label} PLAN", plan(await q(db, f"EXPLAIN {stmt}"))[0]))
        P((f"{label} ROWS", await q(db, stmt)))

    # ================= LEG B: scalar index + conjunction =================
    P(("B1 DEFINE INDEX level", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell_level ON spell FIELDS level")))
    P(("B1 DEFINE INDEX ritual", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell_ritual ON spell FIELDS ritual")))
    for label, stmt in (
        ("B1a level = 4", "SELECT name FROM spell WHERE level = 4"),
        ("B2 TARGET-1 druid AND level=4",
         "SELECT name FROM spell WHERE 'druid' INSIDE classes AND level = 4"),
        ("B3 TARGET-2 druid AND ritual",
         "SELECT name FROM spell WHERE 'druid' INSIDE classes AND ritual = true"),
    ):
        P((f"{label} PLAN", plan(await q(db, f"EXPLAIN {stmt}"))[0]))
        P((f"{label} PLANTEXT", plan(await q(db, f"EXPLAIN {stmt}"))[1][:400]))
        P((f"{label} ROWS", await q(db, stmt)))
    P(("B4 composite (classes, level) legal?", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell_classes_level ON spell FIELDS classes, level")))
    P(("B4a composite PLAN", plan(await q(db,
       "EXPLAIN SELECT name FROM spell WHERE 'druid' INSIDE classes AND level = 4"))[1][:400]))

    # ================= LEG C: exact-name lookup (TARGET-3) =================
    P(("C1 DEFINE INDEX name UNIQUE", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell_name ON spell FIELDS name UNIQUE")))
    P(("C1a name='Fireball' PLAN", plan(await q(db,
       "EXPLAIN SELECT * FROM spell WHERE name = 'Fireball'"))[0]))
    P(("C1b name='Fireball' ROWS", await q(db, "SELECT name, level, school FROM spell WHERE name = 'Fireball'")))
    P(("C1c UNIQUE control: duplicate name rejected?", await q(db,
       "CREATE spell:dupe CONTENT { name: 'Fireball', level: 3, school: 'x', ritual: false, classes: [], body: 'y' }")))

    # ================= LEG D: pure-graph model =================
    await q(db, "DEFINE TABLE IF NOT EXISTS class SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE name ON class TYPE string")
    for slug in ("druid", "wizard", "cleric", "bard", "sorcerer", "warlock", "ranger"):
        await q(db, "CREATE $id CONTENT { name: $name }",
                {"id": RecordID("class", slug), "name": slug})
    P(("D0 edge table ENFORCED", await q(db,
       "DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL")))
    P(("D0b edge UNIQUE(in,out)", await q(db,
       "DEFINE INDEX IF NOT EXISTS learnable_by_in_out ON learnable_by FIELDS in, out UNIQUE")))
    P(("D0c edge field level (denormalised)", await q(db,
       "DEFINE FIELD OVERWRITE level ON learnable_by TYPE int")))
    for rid, nm, lvl, sch, rit, cls in rows:
        for c in cls:
            P((f"D1 RELATE {rid}->{c}", await q(db,
               "RELATE $s->learnable_by->$c SET level = $level",
               {"s": RecordID("spell", rid), "c": RecordID("class", c), "level": lvl})))
    P(("D2 ENFORCED control: dangling endpoint rejected?", await q(db,
       "RELATE $s->learnable_by->$c SET level = 1",
       {"s": RecordID("spell", "fireball"), "c": RecordID("class", "artificer_ghost")})))
    P(("D2b UNIQUE control: duplicate edge rejected?", await q(db,
       "RELATE $s->learnable_by->$c SET level = 3",
       {"s": RecordID("spell", "fireball"), "c": RecordID("class", "wizard")})))

    # TARGET-1 via traversal, node-side WHERE (the 7155 spec form)
    for label, stmt in (
        ("D3 TARGET-1 node-side WHERE",
         "SELECT VALUE <-learnable_by<-(spell WHERE level = 4).name FROM class:druid"),
        ("D4 TARGET-1 edge-side bracket WHERE (denormalised level)",
         "SELECT VALUE <-learnable_by[WHERE level = 4]<-spell.name FROM class:druid"),
        ("D5 TARGET-2 ritual via traversal",
         "SELECT VALUE <-learnable_by<-(spell WHERE ritual = true).name FROM class:druid"),
        ("D6 forward traversal spell->classes",
         "SELECT name, ->learnable_by->class.name AS classes FROM spell:confusion"),
    ):
        P((f"{label} ROWS", await q(db, stmt)))
        P((f"{label} PLAN", plan(await q(db, f"EXPLAIN {stmt}"))[1][:300]))

    # ================= LEG E: re-ingest / dangling =================
    P(("E1 edge count before", await q(db, "SELECT count() FROM learnable_by GROUP ALL")))
    P(("E2 DELETE spell:blight (endpoint)", await q(db, "DELETE spell:blight")))
    P(("E3 edge count after endpoint delete (cascade?)",
       await q(db, "SELECT count() FROM learnable_by GROUP ALL")))
    P(("E3b any edge still naming spell:blight?",
       await q(db, "SELECT id, in, out FROM learnable_by WHERE in = spell:blight")))
    P(("E4 re-CREATE spell:blight then re-RELATE", await q(db,
       "CREATE spell:blight CONTENT { name: 'Blight', level: 4, school: 'necromancy', "
       "ritual: false, classes: ['druid','warlock'], body: 'b' }")))
    P(("E4b traversal sees it before re-RELATE?", await q(db,
       "SELECT VALUE <-learnable_by<-(spell WHERE level = 4).name FROM class:druid")))
    P(("E5 UPSERT (no delete) leaves stale edges: drop 'warlock' from classes", await q(db,
       "UPDATE spell:confusion SET classes = ['druid','bard']")))
    P(("E5b edges for confusion after UPDATE", await q(db,
       "SELECT VALUE out FROM learnable_by WHERE in = spell:confusion")))

    # ================= LEG F: FULLTEXT on body + name =================
    P(("F1 analyzer", await q(db,
       "DEFINE ANALYZER IF NOT EXISTS rules_txt TOKENIZERS class FILTERS lowercase,ascii")))
    P(("F2 fulltext index on body", await q(db,
       "DEFINE INDEX IF NOT EXISTS spell_body_ft ON spell FIELDS body FULLTEXT ANALYZER rules_txt BM25")))
    P(("F3 @@ match on body", await q(db,
       "SELECT name FROM spell WHERE body @@ 'thing'")))
    P(("F4 fulltext + FIELDS name,body rejected?", await q(db,
       "DEFINE INDEX IF NOT EXISTS bad_ft ON spell FIELDS name, body FULLTEXT ANALYZER rules_txt BM25")))

    for label, value in out:
        print(f"{label}\n    {value}\n")
    await db.query(f"REMOVE NAMESPACE {NS}")
    await db.close()

asyncio.run(main())
```
</details>

<details><summary>probe 2 — composite/element-path indexes, the edge-table route, level-as-a-node</summary>

```python
"""Probe 2: index shapes for the three target queries + level-as-edge-hop cost.

Same discipline as probe 1: TEST store only, throwaway namespace, one statement
per query(), every negative paired with a control.

⚠ THIS PROBE'S LEG G5 IS WRONG — see probe 3. Its `spell_level` rows were minted
via RecordID(table, "4") (a STRING id) while the queries name `spell_level:4` (an
INTEGER id), so G5's [] is an id-type mismatch, not an engine bound. Kept verbatim
because the correction is the lesson.
"""
import asyncio, uuid
from surrealdb import AsyncSurreal, RecordID

URL, USER, PASS = "ws://127.0.0.1:18000/rpc", "root", "spikeroot"
NS, DB = f"probe_dnd2_{uuid.uuid4().hex[:8]}", "rules"

async def q(db, stmt, params=None):
    try:
        return await db.query(stmt, params or {})
    except Exception as exc:  # noqa: BLE001
        return f"!! {type(exc).__name__}: {exc}"

def scan(text):
    t = str(text)
    return "IndexScan" if "IndexScan" in t else ("TableScan" if "TableScan" in t else "?")

ROWS = [
    ("fireball", "Fireball", 3, False, ["wizard", "sorcerer"]),
    ("blight", "Blight", 4, False, ["druid", "warlock"]),
    ("confusion", "Confusion", 4, False, ["druid", "bard", "wizard"]),
    ("grasping_vine", "Grasping Vine", 4, False, ["druid"]),
    ("detect_magic", "Detect Magic", 1, True, ["druid", "cleric", "wizard"]),
    ("water_breath", "Water Breathing", 3, True, ["druid", "ranger"]),
    ("cure_wounds", "Cure Wounds", 1, False, ["druid", "cleric"]),
]

async def main():
    db = AsyncSurreal(URL)
    await db.signin({"username": USER, "password": PASS})
    await db.query(f"DEFINE NAMESPACE {NS}")
    await db.use(NS, DB)
    out = []
    P = out.append

    for t in ("spell", "spellc"):
        await q(db, f"DEFINE TABLE IF NOT EXISTS {t} SCHEMAFULL")
        for n, ty in (("name", "string"), ("level", "int"), ("ritual", "bool"),
                      ("classes", "array<string>")):
            await q(db, f"DEFINE FIELD OVERWRITE {n} ON {t} TYPE {ty}")
        await q(db, f"DEFINE FIELD OVERWRITE classes[*] ON {t} TYPE string")
        for rid, nm, lvl, rit, cls in ROWS:
            await q(db, "CREATE $id CONTENT { name: $n, level: $l, ritual: $r, classes: $c }",
                    {"id": RecordID(t, rid), "n": nm, "l": lvl, "r": rit, "c": cls})

    # G1: element-path index + scalar indexes, separate
    await q(db, "DEFINE INDEX IF NOT EXISTS spell_classes_star ON spell FIELDS classes.*")
    await q(db, "DEFINE INDEX IF NOT EXISTS spell_level ON spell FIELDS level")
    await q(db, "DEFINE INDEX IF NOT EXISTS spell_ritual ON spell FIELDS ritual")
    await q(db, "DEFINE INDEX IF NOT EXISTS spell_name ON spell FIELDS name UNIQUE")
    for label, stmt in (
        ("G1a TARGET-1 druid+level4", "SELECT name FROM spell WHERE 'druid' INSIDE classes AND level = 4"),
        ("G1b TARGET-2 druid+ritual", "SELECT name FROM spell WHERE 'druid' INSIDE classes AND ritual = true"),
        ("G1c TARGET-3 exact name", "SELECT * FROM spell WHERE name = 'Fireball'"),
    ):
        P((f"{label} PLAN", str(await q(db, f"EXPLAIN {stmt}"))[:400]))
        P((f"{label} ROWS", await q(db, stmt)))

    # G2: composite over the element path
    P(("G2 composite FIELDS classes.*, level legal?", await q(db,
        "DEFINE INDEX IF NOT EXISTS spellc_cls_lvl ON spellc FIELDS classes.*, level")))
    P(("G2a composite PLAN", str(await q(db,
        "EXPLAIN SELECT name FROM spellc WHERE 'druid' INSIDE classes AND level = 4"))[:400]))
    P(("G2b composite ROWS", await q(db,
        "SELECT name FROM spellc WHERE 'druid' INSIDE classes AND level = 4")))
    P(("G2c composite, containment only PLAN", scan(await q(db,
        "EXPLAIN SELECT name FROM spellc WHERE 'druid' INSIDE classes"))))
    P(("G2d composite, level only PLAN", scan(await q(db,
        "EXPLAIN SELECT name FROM spellc WHERE level = 4"))))

    # G3: the edge table queried AS A PLAIN TABLE (lore's own idiom)
    await q(db, "DEFINE TABLE IF NOT EXISTS class SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE name ON class TYPE string")
    for slug in ("druid", "wizard", "cleric", "bard", "sorcerer", "warlock", "ranger"):
        await q(db, "CREATE $id CONTENT { name: $n }", {"id": RecordID("class", slug), "n": slug})
    await q(db, "DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL")
    for n, ty in (("level", "int"), ("ritual", "bool")):
        await q(db, f"DEFINE FIELD OVERWRITE {n} ON learnable_by TYPE {ty}")
    await q(db, "DEFINE INDEX IF NOT EXISTS lb_in_out ON learnable_by FIELDS in, out UNIQUE")
    P(("G3 index (out, level) on the EDGE legal?", await q(db,
        "DEFINE INDEX IF NOT EXISTS lb_out_level ON learnable_by FIELDS out, level")))
    P(("G3b index (out, ritual) on the EDGE legal?", await q(db,
        "DEFINE INDEX IF NOT EXISTS lb_out_ritual ON learnable_by FIELDS out, ritual")))
    for rid, nm, lvl, rit, cls in ROWS:
        for c in cls:
            await q(db, "RELATE $s->learnable_by->$c SET level = $l, ritual = $r",
                    {"s": RecordID("spell", rid), "c": RecordID("class", c), "l": lvl, "r": rit})
    for label, stmt in (
        ("G4a TARGET-1 via edge-table SELECT",
         "SELECT VALUE in.name FROM learnable_by WHERE out = class:druid AND level = 4"),
        ("G4b TARGET-2 via edge-table SELECT",
         "SELECT VALUE in.name FROM learnable_by WHERE out = class:druid AND ritual = true"),
    ):
        P((f"{label} PLAN", str(await q(db, f"EXPLAIN {stmt}"))[:400]))
        P((f"{label} ROWS", await q(db, stmt)))
    P(("G4c control: does the edge index fire on out alone?", str(await q(db,
        "EXPLAIN SELECT VALUE in FROM learnable_by WHERE out = class:druid"))[:300]))

    # G5: LEVEL AS A NODE (the brief's explicit question) — cost of the extra hop
    await q(db, "DEFINE TABLE IF NOT EXISTS spell_level SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE n ON spell_level TYPE int")
    for lvl in range(0, 10):
        await q(db, "CREATE $id CONTENT { n: $n }", {"id": RecordID("spell_level", str(lvl)), "n": lvl})
    await q(db, "DEFINE TABLE OVERWRITE has_level TYPE RELATION IN spell OUT spell_level ENFORCED SCHEMAFULL")
    for rid, nm, lvl, rit, cls in ROWS:
        await q(db, "RELATE $s->has_level->$l", {"s": RecordID("spell", rid),
                                                "l": RecordID("spell_level", str(lvl))})
    P(("G5a level-as-node: intersect two traversals", await q(db,
        "SELECT VALUE <-learnable_by<-(spell WHERE ->has_level->spell_level CONTAINS spell_level:4).name "
        "FROM class:druid")))
    P(("G5a PLAN", str(await q(db,
        "EXPLAIN SELECT VALUE <-learnable_by<-(spell WHERE ->has_level->spell_level "
        "CONTAINS spell_level:4).name FROM class:druid"))[:500]))
    P(("G5b level-as-node, other direction (from the level node)", await q(db,
        "SELECT VALUE <-has_level<-(spell WHERE ->learnable_by->class CONTAINS class:druid).name "
        "FROM spell_level:4")))
    P(("G5c array::intersect of the two reaches", await q(db,
        "RETURN array::intersect("
        "(SELECT VALUE <-learnable_by<-spell FROM ONLY class:druid), "
        "(SELECT VALUE <-has_level<-spell FROM ONLY spell_level:4))")))

    # G6: name collision across books — a UNIQUE(name) is WRONG the moment two books ship it
    await q(db, "DEFINE TABLE IF NOT EXISTS spellbk SCHEMAFULL")
    for n, ty in (("name", "string"), ("book", "string")):
        await q(db, f"DEFINE FIELD OVERWRITE {n} ON spellbk TYPE {ty}")
    P(("G6a UNIQUE(name) then same name from another book", await q(db,
        "DEFINE INDEX IF NOT EXISTS bk_name ON spellbk FIELDS name UNIQUE")))
    await q(db, "CREATE spellbk:a CONTENT { name: 'Fireball', book: 'PHB' }")
    P(("G6b second book's Fireball REJECTED?", await q(db,
        "CREATE spellbk:b CONTENT { name: 'Fireball', book: 'XGE' }")))
    P(("G6c composite UNIQUE(book, name) admits both?", await q(db,
        "DEFINE INDEX IF NOT EXISTS bk_book_name ON spellbk FIELDS book, name UNIQUE")))

    for label, value in out:
        print(f"{label}\n    {value}\n")
    await db.query(f"REMOVE NAMESPACE {NS}")
    await db.close()

asyncio.run(main())
```
</details>

<details><summary>probe 3 — the CONTROL leg that caught probe 2's instrument lying</summary>

```python
"""Probe 3 — CONTROL leg for probe 2's G5 empty result.

G5 (level-as-a-graph-node) returned [] / [[]]. Before reporting that as an engine
bound, prove the instrument can see a NON-empty answer on the same data: if the
`has_level` edges or the record ids are wrong, the [] is MY bug, not the engine's.
"""
import asyncio, uuid
from surrealdb import AsyncSurreal, RecordID

URL, USER, PASS = "ws://127.0.0.1:18000/rpc", "root", "spikeroot"
NS, DB = f"probe_dnd3_{uuid.uuid4().hex[:8]}", "rules"

async def q(db, stmt, params=None):
    try:
        return await db.query(stmt, params or {})
    except Exception as exc:  # noqa: BLE001
        return f"!! {type(exc).__name__}: {exc}"

ROWS = [
    ("blight", "Blight", 4, ["druid", "warlock"]),
    ("confusion", "Confusion", 4, ["druid", "bard"]),
    ("grasping_vine", "Grasping Vine", 4, ["druid"]),
    ("fireball", "Fireball", 3, ["wizard"]),
    ("cure_wounds", "Cure Wounds", 1, ["druid", "cleric"]),
]

async def main():
    db = AsyncSurreal(URL)
    await db.signin({"username": USER, "password": PASS})
    await db.query(f"DEFINE NAMESPACE {NS}")
    await db.use(NS, DB)
    out = []
    P = out.append

    await q(db, "DEFINE TABLE IF NOT EXISTS spell SCHEMAFULL")
    for n, ty in (("name", "string"), ("level", "int"), ("classes", "array<string>")):
        await q(db, f"DEFINE FIELD OVERWRITE {n} ON spell TYPE {ty}")
    await q(db, "DEFINE FIELD OVERWRITE classes[*] ON spell TYPE string")
    await q(db, "DEFINE TABLE IF NOT EXISTS class SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE name ON class TYPE string")
    await q(db, "DEFINE TABLE IF NOT EXISTS slevel SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE n ON slevel TYPE int")

    for rid, nm, lvl, cls in ROWS:
        await q(db, "CREATE $id CONTENT { name: $n, level: $l, classes: $c }",
                {"id": RecordID("spell", rid), "n": nm, "l": lvl, "c": cls})
    for slug in ("druid", "warlock", "bard", "wizard", "cleric"):
        await q(db, "CREATE $id CONTENT { name: $n }", {"id": RecordID("class", slug), "n": slug})

    # CONTROL 1: how does the SDK's RecordID("slevel", "4") actually LAND?
    await q(db, "CREATE $id CONTENT { n: 4 }", {"id": RecordID("slevel", "4")})
    await q(db, "CREATE slevel:9 CONTENT { n: 9 }")                       # literal int id
    P(("CTL1 ids as stored", await q(db, "SELECT id, n FROM slevel")))
    P(("CTL1a does slevel:4 (int id) resolve?", await q(db, "SELECT * FROM slevel:4")))
    P(("CTL1b does slevel:'4' (string id) resolve?", await q(db, "SELECT * FROM slevel:'4'")))

    # Build the edges using literal INT ids so the id-type question cannot confound
    await q(db, "DEFINE TABLE OVERWRITE has_level TYPE RELATION IN spell OUT slevel ENFORCED SCHEMAFULL")
    await q(db, "DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL")
    for lvl in (1, 3, 4):
        await q(db, f"CREATE slevel:{lvl} CONTENT {{ n: {lvl} }}")
    for rid, nm, lvl, cls in ROWS:
        P((f"CTL2 RELATE {rid}->has_level->slevel:{lvl}",
           await q(db, f"RELATE $s->has_level->slevel:{lvl}", {"s": RecordID("spell", rid)})))
        for c in cls:
            await q(db, "RELATE $s->learnable_by->$c",
                    {"s": RecordID("spell", rid), "c": RecordID("class", c)})

    # CONTROL 3: can the instrument see a NON-empty reverse traversal at all?
    P(("CTL3 reverse from the level node (must be non-empty)", await q(db,
        "SELECT VALUE <-has_level<-spell.name FROM slevel:4")))
    P(("CTL3b forward from a spell (must be non-empty)", await q(db,
        "SELECT VALUE ->has_level->slevel FROM spell:blight")))
    P(("CTL3c reverse from the class node (must be non-empty)", await q(db,
        "SELECT VALUE <-learnable_by<-spell.name FROM class:druid")))

    # NOW the real question: a traversal predicate INSIDE a traversal filter
    for label, stmt in (
        ("H1 nested traversal in WHERE, CONTAINS",
         "SELECT VALUE <-learnable_by<-(spell WHERE ->has_level->slevel CONTAINS slevel:4).name FROM class:druid"),
        ("H2 nested traversal in WHERE, IN",
         "SELECT VALUE <-learnable_by<-(spell WHERE slevel:4 IN ->has_level->slevel).name FROM class:druid"),
        ("H3 flat: traversal predicate on a plain SELECT (no outer traversal)",
         "SELECT name FROM spell WHERE ->has_level->slevel CONTAINS slevel:4"),
        ("H4 flat: the other direction",
         "SELECT name FROM spell WHERE slevel:4 IN ->has_level->slevel"),
        ("H5 two-hop intersect via subquery",
         "SELECT VALUE name FROM (SELECT VALUE <-learnable_by<-spell FROM ONLY class:druid) "
         "WHERE ->has_level->slevel CONTAINS slevel:4"),
        ("H6 level kept as a FIELD, class as an EDGE (the HYBRID)",
         "SELECT VALUE <-learnable_by<-(spell WHERE level = 4).name FROM class:druid"),
    ):
        P((label, await q(db, stmt)))

    for label, value in out:
        print(f"{label}\n    {value}\n")
    await db.query(f"REMOVE NAMESPACE {NS}")
    await db.close()

asyncio.run(main())
```
</details>

<details><summary>probe 4 — the subquery-FROM granularity hazard (§6.2)</summary>

```python
"""Probe 4 — is probe 3's H5 a SILENTLY DROPPED filter?

H5 (`SELECT ... FROM (subquery) WHERE <traversal predicate>`) returned rows the
predicate should have excluded. Before calling that a silent wrong answer, run the
discriminating controls: same shape with a PLAIN FIELD predicate, and the same
traversal predicate applied WITHOUT the subquery FROM.
"""
import asyncio, uuid
from surrealdb import AsyncSurreal, RecordID

URL, USER, PASS = "ws://127.0.0.1:18000/rpc", "root", "spikeroot"
NS, DB = f"probe_dnd4_{uuid.uuid4().hex[:8]}", "rules"

async def q(db, stmt, params=None):
    try:
        return await db.query(stmt, params or {})
    except Exception as exc:  # noqa: BLE001
        return f"!! {type(exc).__name__}: {exc}"

async def main():
    db = AsyncSurreal(URL)
    await db.signin({"username": USER, "password": PASS})
    await db.query(f"DEFINE NAMESPACE {NS}")
    await db.use(NS, DB)
    out = []
    P = out.append

    await q(db, "DEFINE TABLE IF NOT EXISTS spell SCHEMAFULL")
    for n, ty in (("name", "string"), ("level", "int")):
        await q(db, f"DEFINE FIELD OVERWRITE {n} ON spell TYPE {ty}")
    await q(db, "DEFINE TABLE IF NOT EXISTS class SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE name ON class TYPE string")
    await q(db, "DEFINE TABLE IF NOT EXISTS slevel SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE n ON slevel TYPE int")
    for lvl in (1, 3, 4):
        await q(db, f"CREATE slevel:{lvl} CONTENT {{ n: {lvl} }}")
    await q(db, "CREATE class:druid CONTENT { name: 'druid' }")
    await q(db, "DEFINE TABLE OVERWRITE has_level TYPE RELATION IN spell OUT slevel ENFORCED SCHEMAFULL")
    await q(db, "DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL")
    for rid, nm, lvl in (("blight", "Blight", 4), ("confusion", "Confusion", 4),
                         ("grasping_vine", "Grasping Vine", 4), ("cure_wounds", "Cure Wounds", 1)):
        await q(db, "CREATE $id CONTENT { name: $n, level: $l }",
                {"id": RecordID("spell", rid), "n": nm, "l": lvl})
        await q(db, f"RELATE $s->has_level->slevel:{lvl}", {"s": RecordID("spell", rid)})
        await q(db, "RELATE $s->learnable_by->class:druid", {"s": RecordID("spell", rid)})

    SUB = "(SELECT VALUE <-learnable_by<-spell FROM ONLY class:druid)"
    legs = (
        ("I0 subquery FROM, NO where (baseline = 4 druid spells)",
         f"SELECT VALUE name FROM {SUB}"),
        ("I1 subquery FROM + PLAIN FIELD where level = 4 (CONTROL: does any WHERE apply?)",
         f"SELECT VALUE name FROM {SUB} WHERE level = 4"),
        ("I2 subquery FROM + TRAVERSAL where (the suspect)",
         f"SELECT VALUE name FROM {SUB} WHERE ->has_level->slevel CONTAINS slevel:4"),
        ("I3 traversal where WITHOUT the subquery FROM (CONTROL: predicate works alone)",
         "SELECT VALUE name FROM spell WHERE ->has_level->slevel CONTAINS slevel:4"),
        ("I4 subquery FROM + traversal where, IN form",
         f"SELECT VALUE name FROM {SUB} WHERE slevel:4 IN ->has_level->slevel"),
        ("I5 subquery FROM + impossible field predicate (does WHERE ever exclude here?)",
         f"SELECT VALUE name FROM {SUB} WHERE level = 999"),
        ("I6 subquery FROM + impossible traversal predicate",
         f"SELECT VALUE name FROM {SUB} WHERE ->has_level->slevel CONTAINS slevel:1234"),
        ("I7 non-ONLY subquery FROM + traversal where",
         "SELECT VALUE name FROM (SELECT VALUE <-learnable_by<-spell FROM class:druid) "
         "WHERE ->has_level->slevel CONTAINS slevel:4"),
        ("I8 what the subquery actually RETURNS",
         f"RETURN {SUB}"),
        ("I9 nested-filter form that DID work (probe 3 H1), for comparison",
         "SELECT VALUE <-learnable_by<-(spell WHERE ->has_level->slevel CONTAINS slevel:4).name "
         "FROM class:druid"),
        ("I10 EXPLAIN of the suspect",
         f"EXPLAIN SELECT VALUE name FROM {SUB} WHERE ->has_level->slevel CONTAINS slevel:4"),
        ("I11 EXPLAIN of the field-predicate control",
         f"EXPLAIN SELECT VALUE name FROM {SUB} WHERE level = 4"),
    )
    for label, stmt in legs:
        P((label, await q(db, stmt)))

    for label, value in out:
        print(f"{label}\n    {str(value)[:600]}\n")
    await db.query(f"REMOVE NAMESPACE {NS}")
    await db.close()

asyncio.run(main())
```
</details>

<details><summary>probe 5 — is denormalising level onto the edge necessary? (the §4.3 ruling)</summary>

```python
"""Probe 5 — is DENORMALISING level onto the edge necessary?

Probe 2 G4a got ONE IndexScan from a composite (out, level) index on the edge —
but that copies the spell's level onto every edge (a second source of truth that
can diverge). This leg measures the alternative: an `out`-only index plus a
dereference predicate `in.level = 4`, which keeps ONE source of truth.
Controls: the same query with no index at all, and the node-side traversal form.
"""
import asyncio, uuid
from surrealdb import AsyncSurreal, RecordID

URL, USER, PASS = "ws://127.0.0.1:18000/rpc", "root", "spikeroot"
NS, DB = f"probe_dnd5_{uuid.uuid4().hex[:8]}", "rules"

async def q(db, stmt, params=None):
    try:
        return await db.query(stmt, params or {})
    except Exception as exc:  # noqa: BLE001
        return f"!! {type(exc).__name__}: {exc}"

SPELLS = [
    ("blight", "Blight", 4, False), ("confusion", "Confusion", 4, False),
    ("grasping_vine", "Grasping Vine", 4, False), ("fireball", "Fireball", 3, False),
    ("detect_magic", "Detect Magic", 1, True), ("water_breath", "Water Breathing", 3, True),
    ("cure_wounds", "Cure Wounds", 1, False),
]
CLASSES = {"blight": ["druid", "warlock"], "confusion": ["druid", "bard"],
           "grasping_vine": ["druid"], "fireball": ["wizard"],
           "detect_magic": ["druid", "cleric"], "water_breath": ["druid", "ranger"],
           "cure_wounds": ["druid", "cleric"]}

async def main():
    db = AsyncSurreal(URL)
    await db.signin({"username": USER, "password": PASS})
    await db.query(f"DEFINE NAMESPACE {NS}")
    await db.use(NS, DB)
    out = []
    P = out.append

    await q(db, "DEFINE TABLE IF NOT EXISTS spell SCHEMAFULL")
    for n, ty in (("name", "string"), ("level", "int"), ("ritual", "bool")):
        await q(db, f"DEFINE FIELD OVERWRITE {n} ON spell TYPE {ty}")
    await q(db, "DEFINE INDEX IF NOT EXISTS spell_level ON spell FIELDS level")
    await q(db, "DEFINE INDEX IF NOT EXISTS spell_name ON spell FIELDS name UNIQUE")
    await q(db, "DEFINE TABLE IF NOT EXISTS class SCHEMAFULL")
    await q(db, "DEFINE FIELD OVERWRITE name ON class TYPE string")
    for slug in ("druid", "warlock", "bard", "wizard", "cleric", "ranger"):
        await q(db, "CREATE $id CONTENT { name: $n }", {"id": RecordID("class", slug), "n": slug})
    for rid, nm, lvl, rit in SPELLS:
        await q(db, "CREATE $id CONTENT { name: $n, level: $l, ritual: $r }",
                {"id": RecordID("spell", rid), "n": nm, "l": lvl, "r": rit})
    await q(db, "DEFINE TABLE OVERWRITE learnable_by TYPE RELATION IN spell OUT class ENFORCED SCHEMAFULL")
    await q(db, "DEFINE INDEX IF NOT EXISTS lb_in_out ON learnable_by FIELDS in, out UNIQUE")
    for rid, cls in CLASSES.items():
        for c in cls:
            await q(db, "RELATE $s->learnable_by->$c",
                    {"s": RecordID("spell", rid), "c": RecordID("class", c)})

    J1 = "SELECT VALUE in.name FROM learnable_by WHERE out = class:druid AND in.level = 4"
    P(("J0 NO edge index yet — dereference predicate PLAN", str(await q(db, f"EXPLAIN {J1}"))[:400]))
    P(("J0b ROWS", await q(db, J1)))
    P(("J1 add out-only index", await q(db,
        "DEFINE INDEX IF NOT EXISTS lb_out ON learnable_by FIELDS out")))
    P(("J1a dereference predicate PLAN (out index present)", str(await q(db, f"EXPLAIN {J1}"))[:400]))
    P(("J1b ROWS", await q(db, J1)))
    J2 = "SELECT VALUE in.name FROM learnable_by WHERE out = class:druid AND in.ritual = true"
    P(("J2 TARGET-2 dereference PLAN", str(await q(db, f"EXPLAIN {J2}"))[:400]))
    P(("J2b ROWS", await q(db, J2)))
    J3 = "SELECT VALUE <-learnable_by<-(spell WHERE level = 4).name FROM class:druid"
    P(("J3 node-side traversal PLAN", str(await q(db, f"EXPLAIN {J3}"))[:400]))
    P(("J3b ROWS", await q(db, J3)))
    # does the spell-side index EVER get used from inside a traversal?
    P(("J4 does traversal use spell_level index? (search plan text for it)",
       "spell_level" in str(await q(db, f"EXPLAIN {J3}"))))
    # full record for TARGET-3 with its classes, one statement
    P(("J5 TARGET-3 full record + classes", await q(db,
        "SELECT *, ->learnable_by->class.name AS classes FROM spell WHERE name = 'Fireball'")))
    P(("J5b TARGET-3 PLAN", str(await q(db,
        "EXPLAIN SELECT *, ->learnable_by->class.name AS classes FROM spell WHERE name = 'Fireball'"))[:400]))
    # re-ingest: purge a spell's edges by scope without touching the node
    P(("J6 purge one spell's edges", await q(db,
        "DELETE learnable_by WHERE in = $s", {"s": RecordID("spell", "confusion")})))
    P(("J6b edges left for confusion", await q(db,
        "SELECT VALUE out FROM learnable_by WHERE in = $s", {"s": RecordID("spell", "confusion")})))
    P(("J6c TARGET-1 after purge (confusion must be gone)", await q(db, J1)))

    for label, value in out:
        print(f"{label}\n    {str(value)[:600]}\n")
    await db.query(f"REMOVE NAMESPACE {NS}")
    await db.close()

asyncio.run(main())
```
</details>

<details><summary>probe 6 — composite leading-column rule on plain scalars (§3.2)</summary>

```python
"""Probe 6 — does ONE composite UNIQUE(name, source_book) serve BOTH
the cross-book uniqueness constraint AND the exact-name lookup (TARGET-3)?

Probe 2's G2c/G2d showed leading-column access works and trailing-column-only
falls back to TableScan — but that was measured on an ELEMENT-PATH composite
(classes.*, level). Generalising from it to a plain scalar composite would be
exactly the quantifier error this repo forbids, so it is measured directly here.
"""
import asyncio, uuid
from surrealdb import AsyncSurreal

URL, USER, PASS = "ws://127.0.0.1:18000/rpc", "root", "spikeroot"
NS, DB = f"probe_dnd6_{uuid.uuid4().hex[:8]}", "rules"

async def q(db, stmt, params=None):
    try:
        return await db.query(stmt, params or {})
    except Exception as exc:  # noqa: BLE001
        return f"!! {type(exc).__name__}: {exc}"

def scan(t):
    t = str(t)
    return "IndexScan" if "IndexScan" in t else ("TableScan" if "TableScan" in t else "?")

async def main():
    db = AsyncSurreal(URL)
    await db.signin({"username": USER, "password": PASS})
    await db.query(f"DEFINE NAMESPACE {NS}")
    await db.use(NS, DB)
    out = []
    P = out.append
    await q(db, "DEFINE TABLE IF NOT EXISTS spell SCHEMAFULL")
    for n, ty in (("name", "string"), ("source_book", "string"), ("level", "int")):
        await q(db, f"DEFINE FIELD OVERWRITE {n} ON spell TYPE {ty}")
    P(("K1 composite UNIQUE(name, source_book)", await q(db,
        "DEFINE INDEX IF NOT EXISTS spell_name_book ON spell FIELDS name, source_book UNIQUE")))
    for i, (nm, bk, lv) in enumerate((("Fireball", "PHB", 3), ("Fireball", "XGE", 3),
                                      ("Blight", "PHB", 4), ("Confusion", "PHB", 4))):
        P((f"K2 create {nm}/{bk}", await q(db,
            f"CREATE spell:s{i} CONTENT {{ name: $n, source_book: $b, level: $l }}",
            {"n": nm, "b": bk, "l": lv})))
    P(("K3 duplicate (name, book) REJECTED? (control)", await q(db,
        "CREATE spell:dupe CONTENT { name: 'Fireball', source_book: 'PHB', level: 3 }")))
    P(("K4 LEADING column only: WHERE name = 'Fireball'", scan(await q(db,
        "EXPLAIN SELECT * FROM spell WHERE name = 'Fireball'"))))
    P(("K4plan", str(await q(db, "EXPLAIN SELECT * FROM spell WHERE name = 'Fireball'"))[:300]))
    P(("K4rows", await q(db, "SELECT name, source_book FROM spell WHERE name = 'Fireball'")))
    P(("K5 BOTH columns", scan(await q(db,
        "EXPLAIN SELECT * FROM spell WHERE name = 'Fireball' AND source_book = 'PHB'"))))
    P(("K6 TRAILING column only: WHERE source_book = 'PHB'", scan(await q(db,
        "EXPLAIN SELECT * FROM spell WHERE source_book = 'PHB'"))))
    for label, value in out:
        print(f"{label}\n    {str(value)[:400]}\n")
    await db.query(f"REMOVE NAMESPACE {NS}")
    await db.close()

asyncio.run(main())
```
</details>

---

## 8. Candidates for the capabilities doc

Three facts measured here are absent from `docs/reference/surrealdb-31-capabilities.md`, and two of
them are silent-wrong-answer classes. Offered as a flag, not an edit (docs are outside my writable
set):

1. **§3.1 → a new §2 or §7 row.** `DEFINE INDEX … FIELDS <array_field>` is useless for containment;
   the element path `FIELDS <array_field>.*` is required; and `WHERE <array_field> = 'x'` IndexScans
   and returns `[]`. Sits naturally beside the existing *"`string::starts_with` = TableScan, use the
   range"* row — same shape of trap.
2. **§6.2 → §6.6 (the "we are the only source" list) and/or §7.** A `WHERE` over a subquery-`FROM`
   is evaluated once over the whole array, so it is all-or-nothing: false-empty for a field
   predicate, **false-include** for a traversal predicate.
3. **§6.3 → §7.** `RecordID(table, "4")` (string id) and the literal `table:4` (int id) are different
   records; the mismatch reads as `[]`, and `table:'4'` is a parse error. Sibling of the existing
   `str(record.id)` / uuid-shaped-id row.

Also worth a §4 line: **a graph traversal never uses a secondary index** (probe 5 J4). It is the fact
that decides field-vs-edge-hop modelling questions, and nothing currently states it.

---

## 9. Everything I noticed that is outside this brief

Surfaced, not acted on (scope law — the operator decides):

- **`refers` / `answers_to` carry neither `ENFORCED` nor `UNIQUE(in, out)`** (§2.1). Capabilities §8
  ledgers this as open pending packet 43. Not my scope, but a new domain graph copying the existing
  code graph would copy the gap — hence decision 2.
- **No `learnable_by`-style corpus exists yet.** This report models a table set that is not in the
  repo; nothing here is a change to shipped code, and no gate was run (nothing to run one against).
- **Task #14 on the shared board** ("D&D rules RAG — extend-vs-reuse proposals doc") looks like this
  work's parent. My brief named no ledger row as mine, so per brief-base §5 I touched the board not at
  all — flagging in case the lead wants that row driven.
- **The traversal-vs-edge-table return SHAPE differs** (`[[…]]` vs a flat list, §4.3). If both spellings
  end up behind one served tool, that is a render-consistency trap for an LLM consumer.
