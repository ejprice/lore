# SurrealDB 3.1 capability reference for lore agents

*(Opus scout deliverable, 2026-07-11. At kickoff: commit verbatim as
`docs/reference/surrealdb-31-capabilities.md` + lore_remember pointer row.
Format: Capability — desc · 3.1 status · SDK reach (Python surrealdb>=2.0
AsyncSurreal) · house idiom / gotcha · when to reach for it. "SDK: .query()"
= issue the SurrealQL through connection.query(). Server floor ≥3.1.0
(CVE-2026-49997).)*

**Data definition & schema**
- **DEFINE TABLE SCHEMAFULL / TYPE RELATION** — typed tables; RELATION =
  first-class edge with auto in/out. · Stable · SDK: .query(). · House:
  `_define_table`/`_define_relation_table` in surreal_schema.py; edges
  self-delete when an endpoint node is deleted (plain links do not). · Reach
  for: every table; edges for delivery/ack/dependency.
- **DEFINE FIELD … ASSERT / DEFAULT / FLEXIBLE** — typed fields, domain
  constraints, DEFAULT time::now(), FLEXIBLE nested bags. · Stable · SDK:
  .query(). · Gotcha: `DEFINE … IF NOT EXISTS` never updates an existing
  definition — see **Schema migration** below (this cost us a production
  outage, finding #107); `object FLEXIBLE` still enforces declared `[*].key`
  paths. · Reach for: all field DDL.
- **ALTER (every DEFINE)** — 3.1 added ALTER for EVENT/PARAM/BUCKET/ANALYZER/
  FUNCTION/USER/ACCESS/CONFIG/API. · SDK: .query(). · **DO NOT reach for it as
  the migration tool** — ALTER is a property-by-property PATCH that **cannot
  create** a missing definition, and **ALTER INDEX cannot change an index
  definition at all** (only COMMENT / PREPARE REMOVE / DROP COMMENT). See
  **Schema migration** below for the actual decision rule.

**Schema migration — the authoritative rule (docs-verified + live-probed 3.1.5, 2026-07-12)**

*Written after finding #107: a widened field ASSERT shipped green (1040 tests, cold
audit GO) and broke `brief_publish` 100% in production, because `DEFINE FIELD IF NOT
EXISTS` is a NO-OP on an existing field. The answer was in the vendor docs the whole
time. Full workings + citations: `REPORT-c1f-docs-surreal.md`.*

- **Changing an existing FIELD definition → `DEFINE FIELD OVERWRITE`.** The vendor's own
  rule ([define/field](https://surrealdb.com/docs/surrealql/statements/define/field)):
  *"you should not use the `IF NOT EXISTS` clause when you want to ensure that the field
  definition is updated regardless of whether it already exists … use the `OVERWRITE`
  clause … ensuring that the latest version of the definition is always in use."* That is
  exactly `SurrealStore.ensure_ready`'s contract — it re-applies the full DDL every boot.
- **`OVERWRITE` = FULL REPLACE; `ALTER` = PATCH.** ([releases/3.1](https://surrealdb.com/releases/3.1):
  *"Individual properties … can be modified without re-specifying the whole definition via
  `DEFINE … OVERWRITE`."*) Our generators are DECLARATIVE — the `_*_FIELD_SPECS` emit
  complete definitions — so full-replace is what makes the store converge on the specs.
  Probed: `OVERWRITE` omitting an ASSERT **drops** it; `ALTER` omitting one **keeps** it
  (a retired constraint would live in the store forever, invisible in the code).
- **⚠ `ALTER` CANNOT CREATE.** `ALTER FIELD x` on a missing field RAISES; `ALTER FIELD IF
  EXISTS x` **silently no-ops**. `ensure_ready` must also serve a FRESH database, so ALTER
  can never be the boot-time apply — and the `IF EXISTS` form would re-commit #107's exact
  silent-no-op sin on the fresh-DB path.
- **INDEXES and ANALYZERS stay `IF NOT EXISTS` at boot.** A `DEFINE INDEX` **builds** the
  index over every existing row (*"SurrealDB indexes all existing records"*, blocking
  without `CONCURRENTLY` —
  [define/indexes](https://surrealdb.com/docs/reference/query-language/statements/define/indexes)),
  so `OVERWRITE` at boot would re-index `chunk` on every start and hard-fail on an
  embedding-dim change. Probed: `DEFINE INDEX OVERWRITE` on a populated HNSW index at a new
  dim RAISES `Incorrect vector dimension`.
- **An ANALYZER change needs OVERWRITE *plus* `REBUILD INDEX`.** Probed: `DEFINE ANALYZER
  OVERWRITE` updates the definition but leaves every already-built FULLTEXT index tokenised
  the OLD way (the search keeps missing until
  [`REBUILD INDEX`](https://surrealdb.com/docs/reference/query-language/statements/rebuild)).
  An analyzer OVERWRITE alone is a silent recall-quality bug. Corollary: `DEFINE ANALYZER IF
  NOT EXISTS` silently ignores a changed tokenizer/filter set — #107's live, unfixed twin.
- **`DEFINE TABLE OVERWRITE` is SAFE but unnecessary** — probed: it preserves fields,
  indexes AND rows. Our table clauses never change, so leave them `IF NOT EXISTS`.
- **Index migration toolkit (documented, currently unused by lore):** `REBUILD INDEX …
  [CONCURRENTLY]` (non-blocking; progress via `INFO FOR INDEX`) and `ALTER INDEX … PREPARE
  REMOVE` (decommission → verify with `EXPLAIN` → `REMOVE INDEX`).
- **⚠ THE DOCS THEMSELVES ARE WRONG ON ONE POINT.** Both define/field and define/indexes
  claim `IF NOT EXISTS` on an existing object *"will return an error."* **FALSE on 3.1.5** —
  it returns OK and silently keeps the old definition (probed). Do not trust that sentence:
  believing it means believing a stale definition is impossible.
- **Existing rows are NEVER retro-validated** (docs are entirely silent; measured): a TYPE
  or narrowing change converges the SCHEMA, never the DATA. Old rows survive readable but
  become **write-poisoned** — any later UPDATE fails loudly (`Couldn't coerce value for
  field …`). Migrate rows separately. **A new field on a populated table must be `option<>`**
  — a required one poisons every existing row, and a `DEFAULT` does NOT rescue it.
- **DEFINE INDEX (plain / UNIQUE / composite)** — exact-match + uniqueness
  backstops. · Stable · SDK: .query(). · Gotcha (UPDATED RULE): UNIQUE on a
  RELATION edge was unsafe under cascade-delete (ghost entries, #7061) —
  FIXED in 3.1.0; still interacts with UPDATE-inside-EVENT (#7310). Concurrent
  rebuild over populated data needs CONCURRENTLY + poll INFO FOR INDEX. ·
  Reach for: idempotency keys, status filters.
- **DEFINE ANALYZER + FULLTEXT BM25 / HNSW / DiskANN** — code-ident tokenizer;
  BM25 FULLTEXT; HNSW in-memory (SURREAL_HNSW_CACHE_SIZE) + DiskANN
  (persisted, larger-than-memory, NEW in 3.1). · SDK: .query(). · Gotcha:
  `FULLTEXT ANALYZER <n> BM25` (not SEARCH ANALYZER); 3.1.5 requires
  file_allowlist for file-backed mapper analyzers. · Reach for: hybrid
  retrieval (chunk/memory tables only).

**Sequences, counters, IDs**
- **DEFINE SEQUENCE + sequence::next()** — native monotonic counter,
  clustered-safe, lock-free, BATCH/START/TIMEOUT. · New in 3.0 · SDK:
  .query(). · Gotcha: NOT gapless — values never roll back, an aborted txn
  burns the number. Docs disagree on next vs nextval — PROBE the real name;
  smoke first-boot seeding (3.1.0-beta.3 fix). · Reach for: monotonic ids
  where gaps are OK; NOT for gapless human handles (counter-table mint stays
  for finding.number).
- **Record IDs: default / ulid() / uuid() v7 / composite** — ULID + UUIDv7 are
  time-sortable (timestamp-prefixed, range-queryable); composite [a,b,c] ids.
  · Stable · SDK: str(RecordID) round-trip. · Gotcha: cannot index/prefix-match
  a RecordID's string component — carry a queryable value column (the `name`
  table idiom). · Reach for: ulid()/uuid7 when time-clustering helps.
- **UPSERT** — insert-first ("INSERT, otherwise UPDATE") since 2.0.5. · SDK:
  .query(). · Gotcha: `UPSERT <id> … WHERE` on an existing id whose WHERE
  fails cannot create a row. · Reach for: idempotent register/meta writes.

**Change streaming & events**
- **LIVE SELECT** — real-time create/update/delete notifications; DIFF mode;
  FETCH inside LIVE (≥2.2). · Stable, SINGLE-NODE only (#5070 open) · SDK:
  uuid = await conn.query("LIVE SELECT…") then conn.subscribe_live(uuid);
  conn.kill(uuid) to stop. · Gotchas (all honored by scout.py): params IGNORED
  in LIVE WHERE → inline charset-ASSERTed literals; .live(table) is
  whole-table → use query(); best-effort, possibly out-of-order, NO replay on
  reconnect → poll fallback mandatory; relation-traversal-filtered LIVE may
  fire empty-content (#5014) — fine iff payload is discarded and you re-drain.
  · Reach for: contentless wake ONLY; never the source of truth.
- **CHANGEFEED + SHOW CHANGES** — durable versionstamped replayable change log
  (`DEFINE TABLE t CHANGEFEED 3d`; `SHOW CHANGES FOR TABLE t SINCE … LIMIT n`).
  · Stable · SDK: .query(). · Gotcha: retention window; SINCE must post-date
  creation; 3.1 grouped-view writes emit deltas. · Reach for: cross-process
  ordered replay / audit / DR — not when a durable unstamped-edge backlog
  already self-heals.
- **DEFINE EVENT** — server trigger on CREATE/UPDATE/DELETE;
  $event/$before/$after/$value/$input; sync events run IN the triggering txn
  and can THROW to abort; ASYNC [RETRY] [MAXDEPTH] out-of-txn. · Stable
  (ASYNC new 3.0) · SDK: .query() to define. · Gotcha: recent edge/event
  cascade bug history (3.1.0 fix; #7310 UNIQUE×EVENT). · Reach for:
  server-enforced invariants — weigh against a tested app-layer mirror.

**Graph & relations**
- **RELATE + arrow traversal** — RELATE a->edge->b; ->edge->node / <-edge<- /
  <->; single-scan fast path in 3.1. · SDK: .query() (edge-name binding
  unsupported — inline it). · House: RELATE-in-TxnFragment writes; in/out
  edge-table selects. · Reach for: delivery/ack/dependency edges.
- **Recursive graph paths** — @.{n} fixed, @.{1..n} bounded, @.{..} open
  (cap 256); nested shapes @.{1..n}.{ id, kids: ->edge->t.@ }. · Stable ≥2.1 ·
  SDK: .query(). · Gotcha: add TIMEOUT; 3.1.5 fixed min-depth>1 node drops on
  cycles — assert DAG acyclicity. · Reach for: transitive blocks queries in
  one call.
- **Record references (REFERENCE … ON DELETE CASCADE|REJECT|UNSET|THEN)** —
  referential integrity on plain link fields; incoming refs via <~. · Stable
  ≥2.2 · SDK: .query(). · Gotcha: plain record<t> links do NOT auto-clean on
  target delete. · Reach for: link integrity when targets can be deleted
  (comms never deletes agents → skip).

**Server-side logic & config**
- **DEFINE FUNCTION fn::name()** — reusable server-side SurrealQL w/
  permissions. · SDK: .query("… fn::name(args)"). · Reach for: atomic ops
  shared by non-Python consumers (hook CLI, UI); not render-shaped logic.
- **DEFINE PARAM $name** — global db constant, shadowable. · SDK: .query().
- **Transactions** — ACID multi-statement; THROW aborts. · SDK: plain
  .query() validates ONLY statement[0] → always execute_transaction (checks
  every statement); NO server auto-retry → bounded client retry on the
  conflict marker (OTel transaction.conflicts/.retries counters exist). ·
  Reach for: every multi-write op.

**Auth, files, temporal, introspection**
- **DEFINE ACCESS TYPE RECORD / TYPE JWT (+ WITH JWT)** — per-record identity
  ($auth), signup/signin, external JWTs; row/field PERMISSIONS … WHERE. ·
  Stable; DEFINE TOKEN REMOVED in 3.0 · SDK: .signin()/.query(). · Gotcha:
  3.1.5 fixed field-permission bypasses via graph traversal — re-verify perms
  on edge-heavy graphs. · Reach for: PKT-21 per-agent auth.
- **DEFINE BUCKET / DEFINE API** — file storage + custom endpoints. ·
  EXPERIMENTAL (bucket gated behind --allow-experimental files). · Reach for:
  rarely — artifacts stay files-on-disk referenced by refs.
- **VERSION / temporal reads** — SELECT … VERSION d'…'; propagated through
  graph/ref/FETCH in 3.1. · Needs history retention. · Reach for:
  point-in-time forensics beyond what stamps carry.
- **INFO / SHOW / EXPLAIN** — schema/index introspection; EXPLAIN reports
  pushed KNN filters (3.1). · Gotcha: INFO FOR INDEX returns {} for
  non-concurrent builds.
- **Notable 3.1 deltas** — value::expect (inline assertion);
  encoding::json::encode/decode; **time::min/max return NONE for empty groups**
  (fleet aggregates over empty sets now clean); predicate prefilter always-on;
  W3C trace propagation; built-in `surreal mcp` server.

*Sources: surrealdb.com/docs (statements: define/sequence, define/table,
define/event, define/access/record, relate, upsert, show; datamodel: ids,
references; learn: graph-traversal; releases/3.1) · issues #7061 #7310 #5014
#5070 · CVE-2026-49997. Three load-bearing claims want live probes before
first dependence: #7061 cascade fix, edge-table LIVE fires on RELATE,
sequence::next vs nextval.*
