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
  definition — migrations need OVERWRITE/ALTER; `object FLEXIBLE` still
  enforces declared `[*].key` paths. · Reach for: all field DDL.
- **ALTER (every DEFINE)** — full ALTER coverage new in 3.1
  (EVENT/PARAM/BUCKET/ANALYZER/FUNCTION/USER/ACCESS/CONFIG/API). · SDK:
  .query(). · Use: in-place schema migration instead of drop+recreate.
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
