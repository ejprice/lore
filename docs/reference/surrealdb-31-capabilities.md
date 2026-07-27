# SurrealDB — the canonical reference for this project

**Engine: `surrealdb-3.2.1`** (`docker.io/surrealdb/surrealdb:v3.2.1`) — live-read from the
running stores, 2026-07-22, **migrated from 3.1.5 that day** (both stores; prod data byte-identical,
full suite regression-free, #107 fact re-probed on 3.2.1 — receipts in [§0](#0-the-321-migration-receipts)).
Python SDK `surrealdb>=2.0` (installed: 2.0.0; officially supports servers 2.0.0–3.2.0). Server floor
≥3.1.0 (CVE-2026-49997).

> **Version-provenance honesty:** most facts below were `[PROBED]` on **3.1.5** and are dated as such.
> The migration to 3.2.1 was validated to introduce **no behavioural regression** the suite can see
> (§0), and the load-bearing #107 fact was **re-probed directly on 3.2.1**. But an un-re-probed
> `[PROBED … 3.1.5]` fact keeps its 3.1.5 provenance — it was **not** silently relabelled to 3.2.1. If
> you depend on one on 3.2.1, re-probe it (the store IS 3.2.1 now — that is the store to probe).

> ## ⚠ READ THIS BEFORE YOU TOUCH THE STORE
>
> Six facts. Each one has already cost us something.
>
> 1. **`DEFINE … IF NOT EXISTS` is a SILENT NO-OP on an object that already exists.** It does
>    not error. Your changed definition simply never lands on a live store. **This caused a
>    100% production outage** ([#107](#107)) — and it was written in *this file* at the time.
>    **Re-probed on 3.2.1 (2026-07-22): still true** ([§0](#0-the-321-migration-receipts)).
> 2. **Fields therefore use `DEFINE FIELD OVERWRITE`. Indexes, analyzers and tables stay
>    `IF NOT EXISTS`.** Not a style choice — flipping indexes turns a silent no-op into a
>    **boot-time crash**. [§1](#1-ddl--migration)
> 3. **`ALTER` is not the migration verb.** It **cannot create** a field, and
>    `ALTER … IF EXISTS` on a missing one silently no-ops — adopting it re-commits #107 from
>    the other side. [§1.3](#13-why-not-alter)
> 4. **A multi-statement `.query()` validates statement[0] ONLY.** A later statement can fail
>    and roll the whole thing back while `query()` raises *nothing*. Always
>    `execute_transaction`. [§3](#3-transactions)
> 5. **Every test mints a virgin database.** No fixture can see a migration defect — that is
>    *structurally* why 1040 tests, a cold audit and a contract-adversary all passed #107.
>    A clean-slate fixture can never test what only happens on a dirty store. [§1.6](#16-the-blind-spot-that-hid-107)
> 6. **The vendor's docs contain a load-bearing FALSE claim** about exactly this. Read
>    [§6](#6--where-the-vendor-docs-are-wrong) before you trust a SurrealDB doc page.
>
> **And the meta-rule that produced this file:** read the docs *first*, then verify them.
> Probing is for **confirming** what the vendor wrote and finding what it **omits** — never for
> deriving from scratch what is already written down. A doc is a source, not an oracle.

**Provenance legend — every claim below carries one. A claim with neither a citation nor a
probe is worthless; that is exactly how we got here.**

| Tag | Meaning |
|---|---|
| **[VENDOR]** | Official SurrealDB docs, with URL + quoted passage. |
| **[PROBED]** | Run live against spike-surreal by us, with the date **and engine version**. Historical probes are **3.1.5**; **3.2.1** re-probes are marked as such (§0). |
| **[MEASURED]** | Observed in our own test/production runs (receipts named). |
| **[#n]** | A finding in the ledger (`lore_findings get n`). |
| **[CODE]** | Read out of our source, file:line. |
| **[INFERRED]** | Reasoned, not observed. Treat as a hypothesis. |
| **[UNVERIFIED]** | We do **not** know. Probe before depending on it. |

---

## 0. The 3.2.1 migration receipts

We moved off 3.1.5 on **2026-07-22** — the engine had drifted two minors ahead (3.1.5 → 3.2.0 → 3.2.1)
while we ran the old floor. Latest stable is `v3.2.1` (released 2026-07-10); note there is **no
`v3.2.1` git tag** — SurrealDB does **not** tag patch releases, so version questions go to
`surrealdb.com/releases` + Docker Hub, never `git ls-remote --tags`. Both stores now run
`surrealdb-3.2.1`. Validation, all first-hand this session:

- **[MEASURED] Data integrity — prod migrated byte-for-byte.** The 1.2 GB production RocksDB store
  (`lore-surreal :18500`, **174,161 rows across 20 tables**) opened on 3.2.1 in **2 s** with **every
  table count byte-identical** to the pre-migration 3.1.5 baseline (per-table diff: no difference). A
  cold backup of the 3.1.5 store sits at `/backups/lore/surreal-pre-3.2.1-20260721` (verified
  byte-exact) — the RocksDB format change is **forward-only**, so that backup is the sole path back to
  3.1.5.
- **[MEASURED] No behavioural regression the suite can see.** The full test suite (`-n auto`) run
  against a 3.1.5 store vs a 3.2.1 store returned an **IDENTICAL failure set** — 309 failed / 5598 vs
  5597 passed; the diff of the two sorted 309-line failure lists is empty. The single passed-count
  delta was one setup-time harness connection race ([#150](#150)/[#164](#164)), **not** an engine
  behaviour change. (The 309 failures are the packet-03 RED contract, unrelated to the engine.)
- **[PROBED 2026-07-22, spike-surreal 3.2.1] The #107 fact still holds on 3.2.1.** Re-run directly on
  the new engine: `DEFINE FIELD IF NOT EXISTS a ON u TYPE int` against an existing `a TYPE string`
  **raised nothing** and left the field `TYPE string` — a **silent no-op**, exactly as on 3.1.5.
  `DEFINE FIELD OVERWRITE a ON u TYPE int` then migrated it to `TYPE int`. So the §1.1 decision rule is
  unchanged on 3.2.1: **`OVERWRITE` for fields; `IF NOT EXISTS` never migrates.**
- **[MEASURED] SDK unchanged.** `surrealdb==2.0.0` (our pin) talks to the 3.2.1 engine with no code
  change — it is what produced the identical suite result above. The `surrealdb` 3.0.0 alphas
  (a1–a4, 2026-07-13→16) are **not** adopted.

**What 3.2.1 brought that we have NOT independently verified** (from the vendor release notes,
`surrealdb.com/releases/3.2` — `[VENDOR]`, not probed here): an index-backed `COUNT` fix for
multiple-`WHERE`-conjunct queries (a *silently wrong served number* — worth a probe if we lean on
indexed counts), `FLEXIBLE` field-propagation fixes, ~8 security advisories we did not have, and two
**breaking changes** (view tables are now read-only; permissions-predicate restrictions). A `duplicate
edge record ID` fix (#349) and a cold-start `Session not found` router-race fix (#308) touch our edge +
bootstrap seams. **These are release-note claims, not our probes — verify before relying on them.**

Corpus note: this repo now indexes the SurrealDB **3.2 docs** and the engine's **CI-verified SurrealQL
language tests** as lore tiers (`surrealdb-docs`, `surrealql-tests`, pinned at the `v3.2.0` tag). A
claim like the §6.1 falsehood below can now be checked against the vendor's own **executable spec** via
`lore_search(tier="surrealql-tests", …)` instead of a hand-run probe — that corpus is *why* this
reference can cite the engine's own tests rather than only our probes.

---

## 1. DDL & MIGRATION

The single most expensive area in this file. Read all of it before changing any DDL.

### 1.1 The decision rule

| Object | Clause | Why |
|---|---|---|
| **FIELD** | **`OVERWRITE`** | The only clause that makes a changed definition actually land. [#107] |
| **INDEX** | **`IF NOT EXISTS`** | `OVERWRITE` **rebuilds** the index over every row → boot-time crash on a dim change. |
| **ANALYZER** | **`IF NOT EXISTS`** | `OVERWRITE` lands the definition but does **not** re-tokenise built indexes → silent recall bug. |
| **TABLE (plain)** | **`IF NOT EXISTS`** | `OVERWRITE` is *safe* (probed, see below) but plain table clauses never change. Nothing to migrate. |
| **TABLE (RELATION)** | **`OVERWRITE`** | ⚠ **The only clause that lands a changed `IN`/`OUT`/`ENFORCED`.** `IF NOT EXISTS` is a **silent no-op** on an existing edge table [PROBED 2026-07-19] — #107's shape, and invisible to every virgin-DB fixture. Safe: preserves fields, indexes and rows, and does **not** rebuild. |
| **SEQUENCE** | **`IF NOT EXISTS`** | A **bare** `DEFINE SEQUENCE` **RAISES** *"The sequence 'x' already exists"* — and `ensure_ready()` re-applies the DDL every boot, so a bare DEFINE is a **boot-time crash**, exactly the INDEX failure mode. ⚠ Residual: like ANALYZER/INDEX, a changed `BATCH`/`START` then **never migrates** onto an existing store ([#146](#146)). Verified: **no** variant (`IF NOT EXISTS` *or* `OVERWRITE`) resets the counter — the catastrophic case (re-issuing numbers from zero at every boot) is ruled out. [PROBED 2026-07-19] |

[CODE] `loremaster/store/surreal_schema.py` — `_define_field` (:637–671, `OVERWRITE`),
`_define_index`/`_hnsw_index`/`_analyzer_statement`/`_define_table` (all `IF NOT EXISTS`).

### 1.2 `OVERWRITE` vs `IF NOT EXISTS` — the mechanism

**[VENDOR]** [DEFINE FIELD](https://surrealdb.com/docs/surrealql/statements/define/field),
§*Using `IF NOT EXISTS` clause* — this sentence *is* `ensure_ready`'s contract, written by the
vendor:

> "you should not use the `IF NOT EXISTS` clause when you want to ensure that the field
> definition is updated regardless of whether it already exists. In such cases, you might prefer
> using the `OVERWRITE` clause … **ensuring that the latest version of the definition is always
> in use**"

**[VENDOR]** [Release 3.1](https://surrealdb.com/releases/3.1) — the cleanest statement of the
`OVERWRITE`/`ALTER` split:

> "Individual properties on a definition can be modified **without re-specifying the whole
> definition** via `DEFINE … OVERWRITE`."

**`OVERWRITE` = FULL REPLACE. `ALTER` = PATCH.** [PROBED 2026-07-12] `OVERWRITE` omitting an
`ASSERT` **drops** it; `ALTER` omitting one **keeps** it — a retired constraint would live in
the store forever, invisible in the code. Our generators are **declarative** (the `_*_FIELD_SPECS`
emit complete definitions, re-applied in full every boot), so full-replace is exactly what makes
the store converge on the code.

Re-applying an *unchanged* definition with `OVERWRITE` is still a safe no-op. You spend nothing;
you gain the ability to change things.

### 1.3 Why NOT `ALTER`

`ALTER` looks like the "proper" migration verb. It is a trap, and it fails in **#107's own
direction**.

| | `ALTER FIELD` | `DEFINE FIELD OVERWRITE` |
|---|---|---|
| Field doesn't exist yet (a fresh DB — *every test DB, every new project*) | **RAISES** `The field 'x' does not exist`; with `IF EXISTS`, **SILENTLY NO-OPS** | **creates it** ✅ |
| Semantics | **PATCH** — omitted clauses survive | **FULL REPLACE** — omitted clauses dropped ✅ |

[PROBED 2026-07-12] Both rows. `ensure_ready` must also bring a brand-new empty database to the
full schema — **`ALTER` cannot do that at all**, and the `IF EXISTS` variant would re-commit the
exact silent-no-op sin on the fresh-DB path.

**[VENDOR]** [ALTER overview](https://surrealdb.com/docs/surrealql/statements/alter) routes you
away from itself: *"For other such modifications, use the `OVERWRITE` clause in other `DEFINE`
statements."*

**[VENDOR]** [ALTER INDEX](https://surrealdb.com/docs/reference/query-language/statements/alter/indexes)
**cannot change an index definition at all** — the full syntax is `COMMENT | PREPARE REMOVE |
DROP COMMENT`. No FIELDS, no DIMENSION, no ANALYZER. (A prior version of *this file* claimed
ALTER was "in-place schema migration instead of drop+recreate". That was wrong and is corrected.)

### 1.4 What happens to EXISTING ROWS — schema converges, DATA does not

**[VENDOR: entirely SILENT.]** Neither the DEFINE FIELD nor the ALTER pages say one word about
existing rows. Everything below is **[MEASURED]** (REPORT-c1f-contract-migration §4, live 3.1.5).
The vendor documents no retro-validation **because there is none**.

| Change applied to a table WITH ROWS | The DDL | Existing rows | New writes | UPDATE of an old row |
|---|---|---|---|---|
| **Widen** an ASSERT | applies | intact, still writable | new value accepted; junk still rejected | fine |
| **Narrow** an ASSERT (a row violates it) | **applies cleanly** | **intact, NOT rewritten, still readable** | now-illegal value rejected | **RAISES**, naming field + value |
| **TYPE** change `string`→`int` | **applies cleanly** | **intact, UNCOERCED** (`'7'` stays `'7'`) | held to the new type | **RAISES** `Couldn't coerce value …` — *even for `'7'`* |
| Add a `DEFAULT` | applies | untouched | default fills an omitted field | — |

> **A TYPE or NARROWING change converges the SCHEMA but never the DATA.** Old rows are left
> **write-poisoned** — readable, but any future UPDATE (*even of an unrelated column*, because the
> whole record is re-validated on write) is **rejected loudly**. Never silently corrupted, never
> dropped. Migrate rows separately.

**⚠ A NEW field on a POPULATED table must be `option<>`.** [PROBED] A required (non-`option`)
field poisons every existing row (`Expected string but found NONE`) — and **a `DEFAULT` does NOT
rescue it** (DEFAULT applies at CREATE, not to an existing row's missing value). Only `option<>`
un-poisons it.

### 1.5 Indexes & analyzers — why they must NOT get `OVERWRITE`

**[VENDOR]** [DEFINE INDEX](https://surrealdb.com/docs/reference/query-language/statements/define/indexes):
*"During this stage, SurrealDB **indexes all existing records**."* / *"Without `CONCURRENTLY`,
`DEFINE INDEX` **blocks until the index is fully built** (or the build fails)."*

A define **builds**. Therefore [PROBED 2026-07-12]:

```
re-DEFINE INDEX dim 4 -> 8 (IF NOT EXISTS): OK      (silent no-op — today's behaviour)
re-DEFINE INDEX dim 4 -> 8 (OVERWRITE):     RAISED  InternalError:
    Incorrect vector dimension (4). Expected a vector of 8 dimension.
```

`DEFINE INDEX OVERWRITE` at boot would re-index the whole `chunk` table on **every start** and
**hard-fail `ensure_ready()`** on an embedding-dim change. The dim change already has its own
mechanism (the schema-fingerprint rebuild). **Do not flip it.**

> **⚠ DO NOT GENERALISE THAT WARNING TO `DEFINE TABLE OVERWRITE` — it is a different verb and it is
> SAFE.** [PROBED 2026-07-19] On a populated table carrying **both** an HNSW vector index and a
> UNIQUE index: `DEFINE TABLE OVERWRITE … SCHEMAFULL` completed in **1.7 ms**, rows intact (8/8),
> the HNSW definition preserved verbatim, KNN results identical, and the UNIQUE index still
> rejecting duplicates. **It does not rebuild.**
> **Positive control, on the same table:** `DEFINE INDEX OVERWRITE` with a changed dimension raised
> `Incorrect vector dimension (8). Expected a vector of 16 dimension.` — §1.5's crash reproduces on
> demand, which proves the clean TABLE result is a real negative and not a blind instrument.
> This is what makes the relation-table flip to `OVERWRITE` (§1.1) affordable.

**An ANALYZER change needs `OVERWRITE` *plus* `REBUILD INDEX`.** [PROBED 2026-07-12] —
`DEFINE ANALYZER OVERWRITE` updates the definition but leaves every already-built FULLTEXT index
tokenised the **old** way:

```
under 'blank' analyzer, search 'ensure_ready' : []       (miss, as expected)
DEFINE ANALYZER OVERWRITE (now splits punct)  : OK
same search, index NOT rebuilt                : []       <-- STILL STALE
REBUILD INDEX t6_ft ON t6 -> OK; same search  : [t6:a]   <-- only now correct
```

An analyzer OVERWRITE **alone is a silent recall-quality bug**. A correct analyzer migration is
`OVERWRITE` + [`REBUILD INDEX`](https://surrealdb.com/docs/reference/query-language/statements/rebuild)
on every FULLTEXT index, and it belongs in the fingerprint-rebuild path, not in `ensure_ready`'s
boot DDL.

**Documented index-migration toolkit we do NOT currently use** [VENDOR]:
`REBUILD INDEX … [CONCURRENTLY]` (non-blocking; progress via `INFO FOR INDEX`) and
`ALTER INDEX … PREPARE REMOVE` (decommission → verify with `EXPLAIN` → `REMOVE INDEX`).
See [§8](#8-open-hazards--unverified-claims).

### 1.6 The blind spot that hid #107

**Every test mints a virgin database** — `_surreal_harness.unique_database()` → `test_<pid>_<uuid4>`.
Excellent isolation (it is what makes the suite parallel-safe), and it means **no test in this repo
had ever applied a schema change to an EXISTING store**. On a virgin DB, `IF NOT EXISTS` cheerfully
creates the *new* definition — so 1040 tests, a full cold code audit, and a contract-adversary
specifically hunting wrong builds **all passed**. The only instrument that could see it was the
deploy smoke against the real store.

> **A fixture that guarantees a clean slate can never test the thing that only happens on a dirty
> one. Every long-lived deployment is, by definition, a dirty one.**

The invariant that closes it (now pinned, `TestSchemaMigrationAgainstAnExistingStore` in
`test_surreal_store.py`): **apply the OLD DDL → insert a row → apply the NEW DDL → assert the new
constraint took effect AND the existing row survived.**

### 1.7 Other DDL hazards

- **[MEASURED, P8c]** `REMOVE TABLE` + `DEFINE TABLE/INDEX` in **one transaction** can hit a
  retryable conflict with an async HNSW index build — recreate in **two** steps.
  **The two-step window is a TRAP:** any raw write landing between the REMOVE and the DDL
  auto-creates the table **SCHEMALESS**, making `DEFINE TABLE IF NOT EXISTS … SCHEMAFULL` a no-op,
  so a later `DEFINE FIELD … FLEXIBLE` is rejected (*"FLEXIBLE can only be used in SCHEMAFUL
  tables"*) and the whole DDL rolls back. Fix in `memory/local.py`: one `asyncio.Lock` held across
  the entire drop→DDL→restore span. Any future table-recreate path must take the same lock or be
  single-writer.
- **[PROBED]** `array<object> FLEXIBLE` still enforces **declared** `[*].key` paths; declared *and*
  undeclared nested keys survive CREATE+UPDATE. A non-FLEXIBLE object raises, as documented.
- **[PROBED]** Undeclared **top-level** keys on a SCHEMAFULL table RAISE in 3.x.
- **[PROBED]** `DEFINE FIELD OVERWRITE` is legal inside the `BEGIN … COMMIT` that `ensure_ready`
  uses, and works on relation-edge fields and nested `chunk_hashes[*].…` fields.

---

## 2. DML IDIOMS

The house rules for reading and writing rows. Each one was found the hard way.

- **`session` is a PROTECTED variable name.** [PROBED, P8a] `SET session = $session` is rejected
  (*"'session' is a protected variable and cannot be set"*). Writing a row with a `session` column
  requires **`CREATE <table> CONTENT $content`** with `session` as a KEY *inside* the bound object.
  `SurrealStore.record_trace` is shaped this way on purpose. **This is the general rule: use
  `CONTENT` for any write whose columns may collide with a protected name.**
  - **⚠ `CONTENT` composes with NEITHER `SET` NOR `MERGE` — both are PARSE ERRORS.**
    [PROBED 2026-07-24, 3.2.1] So the moment you need "bind an object **AND** compute a column
    store-side" (the usual case: a `sequence::nextval()` mint alongside a bound payload), the obvious
    spellings are dead ends:

    | shape | result |
    |---|---|
    | `CREATE t CONTENT $c SET seq = sequence::nextval("s")` | **PARSE ERROR** — `Unexpected token 'SET'` |
    | `CREATE t CONTENT $c MERGE { seq: … }` | **PARSE ERROR** — `Unexpected token 'MERGE'` |
    | `CREATE t CONTENT object::extend($c, { seq: sequence::nextval("s") })` | ✅ **the working shape** |
    | `CREATE t CONTENT { tool: $c.tool, …, seq: … }` | works, but re-enumerates every column by hand |

    **`object::extend($bound, {computed})` is the idiom** — it is the only one that keeps the bound
    payload opaque (no hand-listing, so adding a column later cannot silently drop it) while letting
    the engine mint. Also measured: **`sequence::nextval` starts at 0** under the default `START 0`,
    so a sequence-backed column is 0-based — do not write a pin that assumes 1.
- **A missing SELECT projection reads `None`, not a `KeyError`.** Projecting a column that does not
  exist yields `None` — so a typo'd projection degrades **silently** into a null, it does not blow
  up. Validate the shape you got.
  - **⚠ BUT `SELECT *` BEHAVES THE OPPOSITE WAY: it OMITS a `NONE`-valued column ENTIRELY, so
    `row["col"]` raises `KeyError`.** [PROBED 2026-07-24, 3.2.1] The sentence above is true of an
    explicit **projection** and says nothing about `SELECT *` — and the two differ exactly where it
    hurts. A column that is `option<>` and unset does not come back as `None` under `SELECT *`; **the
    key is not there at all.** So the defensive shape depends on how you read: `row.get("col")` after
    a `SELECT *`, `row["col"]` (may be `None`) after an explicit projection. Cost of learning this the
    hard way: two pins in the 03b telemetry contract. **Corollary for any `option<>` column** — and
    every enrichment column on `trace` is one — **a reader must not assume presence.**
- **`str(RecordID)` round-trips.** The SDK's `RecordID` stringifies to `table:id` and parses back.
- **CONTENT datetimes are Python datetimes.** tz-aware stdlib datetimes bind fine (cbor2 tag 0) —
  do not stringify them.
- **⚠ Use the `time::` family for datetime aggregates under `GROUP BY`.** [PROBED, P8d W3]
  `time::max()` is the **only** correct max-aggregate for a datetime column — **`math::max` and
  `array::max` both accept datetimes and silently return GARBAGE instead of erroring.** First
  consumer: `SurrealStore.trace_aggregates()`.
- **You cannot index or prefix-match a RecordID's string component** — carry a queryable value
  column (the `name`-table idiom).
- **[PROBED]** `string::starts_with` = TableScan (*"unsupported predicate"*, the index is ignored).
  A range predicate `value >= $p AND value < $p_hi` = IndexScan, identical results. Use the range.
- **`UPSERT`** is insert-first ("INSERT, otherwise UPDATE"). Gotcha: `UPSERT <id> … WHERE` on an
  existing id whose WHERE fails **cannot create** a row.
- **`record<t>` links do NOT auto-clean on target delete** — but graph RELATION edges **do**
  self-delete when an endpoint node is deleted. Snapshot GC must delete `snapshot_entry` rows
  explicitly. **[VENDOR]** [RELATE](https://surrealdb.com/docs/surrealql/statements/relate):
  *"a graph edge will also automatically be deleted if it is no longer connected to a record at
  both `in` and `out`."*
- **⚠ `UPDATE` of a relation edge's `in`/`out` is a SILENT NO-OP.** [PROBED 2026-07-19] Setting
  either endpoint to a **real, existing** record returns `OK` **with a returned record**, and the
  endpoint is **unchanged**. Not a rejection — a silent no-op, the §2 degradation shape rather than
  a loud failure. **Any future "rewire this delivery to a different agent" written as an `UPDATE`
  will report success and do nothing.** The upside: endpoints are effectively immutable after
  `RELATE`, so `ENFORCED` (§4) cannot be walked around via `UPDATE`. To re-point an edge, DELETE
  and re-`RELATE`.

---

## 3. TRANSACTIONS

- **⚠ The SDK's `.query()` validates ONLY statement[0].** [CODE, SDK 2.0.0:
  `_check_query_result(response["result"][0])`] Any multi-statement string whose **later** statement
  fails returns a per-statement `ERR` **with no top-level error** → a **silent partial apply**. This
  bit us as silent-partial-SCHEMA in all three `ensure_ready` DDL paths.
  > **NEVER send multi-statement SurrealQL through `query()`. Use `execute_transaction`, which
  > checks every statement.** (`DEFINE`-in-transaction is allowed on 3.1.5.)
- **⚠ Classify SEMANTICALLY — POSITION IS WRONG AT BOTH ENDS.** [#93, RESOLVED @ 93a9aab] In a
  `BEGIN; …; COMMIT;` body, once *any* statement fails, **the COMMIT also errors** — with
  *"Cannot COMMIT: the transaction was aborted due to a prior error"*, which carries none of the
  real error's markers. So `failed_statements[-1]` **discards the real cause**.
  **⚠ BUT `[0]` IS ALSO WRONG, AND A PRIOR VERSION OF THIS SECTION TAUGHT IT.** [PROBED 2026-07-19]
  The engine stamps CASCADE notices on statements *before* the offender, so `[0]` is typically
  *"The query was not executed due to a failed transaction"* — a notice, not the cause.
  **The CODE was already right and this prose was stale**: `_txn.py:416` defines
  `_CASCADE_NOT_EXECUTED_MARKER = "was not executed due to"` and `_domain_root_cause` (:714) picks
  the first **non-cascade** entry, its docstring stating outright that *"selecting by POSITION is
  refused at both ends … only a SEMANTIC (marker-seeking) selector is correct."* Fixed here
  2026-07-19; the code never had the bug. *(This is the §8 stale-prose class: a doc teaching a
  retired mechanism, which no gate will ever catch.)*
  *The original #93 defect is why the C1 mint bug could hide: the collision's own rejection text
  was masked by the COMMIT's.*
- **[VENDOR] The supported all-statements call is `query_raw()`** —
  [executing-queries](https://surrealdb.com/docs/sdk/python/concepts/executing-queries):
  *"If you need the results from every statement, use `.query_raw()` instead"* (per-statement
  `status`/`time`/`result`). It is what `execute_transaction` already rides. ⚠ The same page lies
  about `.query()` itself — see §6.5.
- **Client-side conflict retry is MANDATORY.** [PROBED] The engine does **not** auto-retry user
  transactions. The only signal is the literal marker string **`"can be retried"`**
  ([CODE] `_txn.py:326`). 3.1 exposes OTel counters `surrealdb.transaction.retries` / `.conflicts`.
  - **#111 ANSWERED — keep the substring, the trigger is NOT met.** [CODE, 2026-07-19] SDK 2.0.0
    *does* ship a typed `kind`/`details` error hierarchy (`surrealdb/errors.py`), which is what #111
    was waiting for — but **`ErrorKind` has no retryable member** (`Validation, Configuration,
    Thrown, Query, Serialization, NotAllowed, NotFound, AlreadyExists, Connection, Internal`), and a
    conflict arrives as a plain `QueryError`. A typed check is therefore not yet possible. Re-open
    when `ErrorKind` gains a retryable/conflict member — not merely when the SDK version bumps.
- **[PROBED]** A socket drop with queries **in flight** surfaces a raw `builtins.KeyError(uuid)`
  from SDK 2.0.0's response routing (6/6 futures) — *not* `CancelledError`. The next call heals via
  `ConnectionClosedError`. Classify `KeyError` tightly, at the SDK-await boundary only.
- **[PROBED]** One WS connection multiplexes concurrent `query()` safely (uuid-keyed futures).

---

## 4. GRAPH / RELATE

- **⚠ RELATE endpoints must be BOUND RecordID params.** [PROBED 2026-07-12]
  `RELATE type::record(..)->edge->type::record(..)` is a **PARSE ERROR**. The working shape is:
  ```surql
  RELATE $from->edge->$to SET ...     -- $from / $to bound as RecordIDs
  ```
  (Matches the `graph_surreal.py` precedent.) The **edge name itself cannot be bound** — inline it.
- **⚠⚠ `RELATE` does NOT validate that its ENDPOINTS exist — NEITHER `in` NOR `out`.** [#105]
  A `RELATE` with a bogus record id on **either or both** ends **silently writes a DANGLING edge**
  to a phantom record — no error. In a brief/ack or delivery graph this is a **receipt for an agent
  who does not exist**: provenance you cannot trust is worse than no provenance.
  - **[VENDOR — and the vendor endorses our guard]** [RELATE](https://surrealdb.com/docs/surrealql/statements/relate):
    *"`RELATE` will create a relation regardless of whether the records to relate to exist or not"*,
    and it is *"advisable to … ensure that they exist."* So the application-level existence check is
    **vendor-recommended**, not merely prudent.
  - **[PROBED 2026-07-19]** all four legs, verbatim: bogus `out` → **OK**; bogus `in` → **OK**;
    both bogus → **OK**; both real (positive control) → OK. ⚠ The instrument's own first run said the
    opposite — endpoints bound as **strings** made every leg fail, and *only the positive control
    exposed it.* A run without that control would have reported "RELATE rejects bad ids".
  - **The traversal cannot distinguish a ghost at all**: `SELECT ->to->agent AS recipients` lists
    `agent:a_ghost` as a first-class recipient while `SELECT count() FROM agent` = 1 and no phantom
    node is materialised. A reader sees it **only** by projecting a field or `FETCH`ing and checking
    for `None` — §2's silent-`None`-projection trap, one level deeper.
  - **`in` was the recorded half; `out` is the DANGEROUS half.** In a `message->to->agent` fan-out
    `in` is a row we just created, and **`out` is the CALLER-SUPPLIED recipient**.
  - *Formerly filed as latent* because agents are **retired, never hard-deleted**, and callers passed
    store-resolved ids. **The second clause dies the moment any verb accepts a recipient NAME from a
    caller** (comms `send`), and the first dies the day anything hard-deletes a node. Note
    `BriefLedger.publish(agent_id=...)` already takes a **bare string**.
  - A typed relation table `DEFINE TABLE to TYPE RELATION IN message OUT agent` rejects a
    wrong-**table** endpoint with a field-coercion error [PROBED 2026-07-19], but does **not**
    reject a non-existent record of the RIGHT table.
  - ⚠ **THE ENGINE SHIPS A DECLARATIVE GUARD FOR EXACTLY THIS — `ENFORCED`.** [VENDOR]
    [DEFINE TABLE](https://surrealdb.com/docs/surrealql/statements/define/table): *"the `ENFORCED`
    clause can be used on a table of `TYPE RELATION` to disallow a `RELATE` statement from working
    unless it points to existing data."* BNF:
    `TYPE RELATION [IN|FROM] @table [OUT|TO] @table [ENFORCED]`. Present since ≥2.0.3 (issue #5039
    is filed against it there), so it is **on our floor, not a 3.2+ feature**.
    **An earlier version of this bullet said an application-level check was "the only guard". That
    was FALSE — see §6.3.**
  - **[PROBED 2026-07-19, 8 legs — `REPORT-probe-enforced-clause.md`] Everything you need to adopt it:**
    | question | answer |
    |---|---|
    | Does it work on 3.1.5? | **YES**, and it validates **BOTH** endpoints. Error: `The record 'agent:a_ghost' does not exist`. Vendor CONFIRMED verbatim. |
    | ⚠ **Migration onto an EXISTING table** | **`IF NOT EXISTS` is a SILENT NO-OP** — #107's shape, invisible to every virgin-DB test. **`OVERWRITE` is the only clause that lands it**, and it preserves fields, indexes and rows. |
    | Pre-existing dangling edges | **Entirely unaffected** — readable, traversable, updatable, deletable. `ENFORCED` neither hides them, breaks them, nor helps you find them. **Turning it on and calling the ghost problem closed is a false all-clear**; cleanup is a separate data migration. |
    | Endpoint-delete cascade | **Unchanged** — still cascades, still cleans the UNIQUE entry, re-`RELATE` succeeds. |
    | Composition | Fine with `UNIQUE(in,out)` **and** `SCHEMAFULL` fields; the three failures are distinguishable by error text. |
    | Cost | **None measurable** — ~2.8% at 16-way × 20, inside run-to-run noise. |
    | Error ergonomics | ⚠ **ONE bad endpoint per attempt, as untyped PROSE, only AFTER the write is attempted, aborting the whole txn.** So it does **NOT** replace an app-level check that names EVERY bad recipient BEFORE the write — and parsing `"The record 'x:y' does not exist"` to recover the id would be a literal-keyed instrument of the kind this repo forbids. |
    | Issue #5039 (chained relations) | Does **not** reproduce on 3.1.5; the closure is genuine. |
    | `INSERT RELATION` | **The door only `ENFORCED` shuts** — `TYPE RELATION` alone rejects `CREATE`/`INSERT`/`UPSERT`, but `INSERT RELATION INTO` writes a dangling edge on a non-ENFORCED table. An app check on one verb cannot reach it; **`ENFORCED` guards the TABLE, including write paths nobody has written yet.** |
    **Shape to ship:** `DEFINE TABLE OVERWRITE <edge> TYPE RELATION IN <a> OUT <b> ENFORCED SCHEMAFULL`,
    with the app-level check kept as the ergonomic layer. Neither is redundant.
  - A **bare `str`** endpoint (rather than a bound `RecordID`) is rejected LOUDLY:
    `"Cannot execute RELATE statement where property 'in' is: 'message:m_real'"`. That is a helpful
    failure — do not "fix" it by pre-formatting ids into strings.
  - Note the original audit **could not make the RELATE fail with a bad id at all**. That inability
    *is* the finding.
- **UNIQUE index on a RELATION edge is LEGAL on our floor.** [CODE + PRODUCTION] `briefed` declares
  `UNIQUE(in, out)` (`surreal_schema.py:1071`) and runs in production. The old ban (#7061
  ghost-entry cascade bug) is **retired** — fixed in ≥3.1.0.
  - **SETTLED — the #7061 cascade hazard is ABSENT on 3.1.5, and the VENDOR SAYS SO TOO.**
    [VENDOR] [Release 3.1](https://surrealdb.com/releases/3.1) §Indexes names **both** of our probe's
    legs as fixed in 3.1 — *"ghost UNIQUE-index entries on relation tables"* and *"phantom
    UNIQUE-index entries when `IN`/`OUT` records were deleted before the relation."* The fix landed
    **on our floor**. [PROBED 2026-07-19] `RELATE` →
    **hard-delete an endpoint** → re-`RELATE`: deleting either endpoint **cascades the edge away**
    (confirmed, not assumed) **and cleans its UNIQUE index entry**, so the re-`RELATE` SUCCEEDS —
    for a recreated endpoint, an absent endpoint, and an `in`-side delete alike. Positive control:
    a genuine duplicate while both endpoints live IS rejected, proving the index was enforcing.
    `UNIQUE(in, out)` is safe to ship on relation edges. Still interacts with UPDATE-inside-EVENT
    (#7310 — moot while those edges carry no events).
  - ⚠ Because `UNIQUE(in, out)` makes a duplicate a **loud ERR**, a fan-out that may repeat a
    recipient must **dedupe before the RELATE loop** (or catch it) — the index is a correctness
    backstop, not a de-duplicator you can lean on silently.
- **Recursive graph paths** — `@.{n}` fixed, `@.{1..n}` bounded, `@.{..}` open (cap 256); nested
  shapes `@.{1..n}.{ id, kids: ->edge->t.@ }`. **Add a `TIMEOUT`** and assert DAG acyclicity (3.1.5
  fixed min-depth>1 node drops on cycles).
- **Record references** (`REFERENCE … ON DELETE CASCADE|REJECT|UNSET|THEN`, incoming via `<~`) give
  referential integrity on **plain link fields** — the thing plain `record<t>` links lack.

---

## 5. CONCURRENCY / HOT ROWS

The counter-row mint (a single row every writer funnels through) is this project's standard
gapless-number mechanism — and its standard footgun.

**The three rules, each bought with a defect:**

1. **Retry policy lives in ONE driver — never hand-roll it.** [#102/#108/#120, FIXED 2026-07-14,
   commit 9d29111] `_txn.retry_on_conflict` owns: per-attempt **fresh full jitter drawn from the
   process PRNG on EVERY attempt** (never cached, never derived from the contended row's identity
   or any call parameter), a guaranteed attempt **floor**, a wall-clock **deadline** that may cut
   retries only once the floor is met, a generous attempt **ceiling** as runaway backstop, and the
   typed exhaustion error. `bootstrap_session` (the ONE session bootstrap, composed single budget)
   and `run_query` (the ONE single-statement attempt body, classify-and-signal) ride it; so does
   every `_query` seam, scout, and `execute_transaction`. A caller that routes through the driver
   but classifies the conflict locally is a private copy wearing the shared name — **prove sharing
   by mutation** (move the marker: every seam's pin must go red).
   > *A concurrency guarantee is only as good as the contention you have actually tested it at.*
   > Pin hot-row mints at **≥8-way**, never 2-way — and structure fixtures so racer LIFETIMES
   > overlap (repeated operations per racer); a start-line barrier synchronises Python, not the
   > wire. Historical receipt for why: the pre-fix deterministic shared backoff measured **43%
   > txn-exhaustion at N=8** on the findings mint.
2. **A mint failing under contention is a STOP, not "flaky".** The C1 brief mint failed ~4 of 5
   runs, was called flaky, and shipped. **A single green run NEVER clears a concurrency test —
   require 20 consecutive.**

**A TOCTOU read-max-then-CREATE is not a mint.** The proven shape is the **counter-row UPSERT**
riding the shared driver. Note the `UNIQUE` index stays the **backstop**, never the mechanism.

**[MEASURED 2026-07-12, probe-sequence-1] Native sequences are REAL and the correct spelling is
`sequence::nextval("<name>")`** — `sequence::next()` and bare `sequence::nextval()` are wrong.
Syntax: `DEFINE SEQUENCE <name> [BATCH <n>] [START <n>] [TIMEOUT <duration>];` then
`RETURN sequence::nextval("<name>");` (defaults `BATCH 1000 START 0`, confirmed via `INFO FOR
DB`). Contention-free measured to **32-way** (3200 calls: 100% distinct, zero gaps, zero errors)
and **zero retryable conflicts** with `nextval` inside `BEGIN/COMMIT` alongside a `CREATE`
(16-way × 30 × 5 runs). **NOT gapless — and this is a DOCUMENTED GUARANTEE, not an accident we
observed.** [VENDOR] [DEFINE SEQUENCE](https://surrealdb.com/docs/surrealql/statements/define/sequence):
*"Sequences are never rolled back, even in a failed transaction"* (with a `0 → 2` cancelled-txn
example). The vendor also documents `sequence::nextval('mySeq2')` and a BNF carrying **both**
`OVERWRITE | IF NOT EXISTS` — so the clause CHOICE in §1.1 is ours (driven by the bare-DEFINE boot
crash), not a syntax limit. An aborted txn burns the number. Fine for monotonic ids
where gaps are OK (PKT-28 C2's `message.seq` — task f86af162); **not** for gapless human handles
(that is why the counter-row mint stays for `finding.number` / `brief.version`).

**[PROBED 2026-07-19, re-confirmed in the real write shape]** `sequence::nextval` + `CREATE` +
N×`RELATE` **composes in ONE `execute_transaction`**: 16-way × 20 = **320/320 OK, zero conflicts,
zero duplicates, zero gaps**. So a fan-out send does **not** contend — contention lives on the
per-recipient CAS stamp, not on the mint. `sequence::next` is a **PARSE ERROR** on 3.1.5 (the engine
itself suggests `nextval`), settling the contradiction §8 used to carry. Declare the sequence
`IF NOT EXISTS` — see the §1.1 row for why, and for the BATCH/START residual ([#146](#146)).
**Gaps are REAL**: an aborted txn burns a number, so `seq` is a monotonic ORDERING key — never a
count, never a "how many messages" display, never a gapless handle. Pin that consumers tolerate gaps.

**⚠ [MEASURED, finding #124 — MECHANISM CORRECTED 2026-07-19, see [#144](#144)] Auto-schema table
creation STORMS WITH RETRYABLE CONFLICTS under concurrent first-write, and `query()` makes them
LOOK like silent data loss.** Many concurrent transactions issuing the first-ever `CREATE` against a
table with no `DEFINE TABLE` appeared to commit while an independent read found rows missing
(466–474 of 480; always each worker's first txn; zero errors surfaced).

> **The engine was NOT losing committed rows.** [PROBED 2026-07-19] Those "successes" were
> **retryable conflicts**, invisible because they were issued through the SDK's `.query()`, which
> validates **statement[0] only** (§3) — with `BEGIN` at index 0, every later `ERR` is discarded and
> the call reads as success. Under full per-statement checking: **10 OK / 10 readable, ZERO loss**;
> with the retry driver, **160/160 land**. #124 is an **INSTANCE OF THE §3 `query()` GAP**, not a
> separate engine defect. **Do not cite it as evidence that SurrealDB loses committed data.**

**The conclusion is UNCHANGED and now rests on two independently measured reasons: every table
production code writes to must be declared before first write.** (1) Undeclared tables storm with
retryable conflicts under concurrent first-write. (2) An undeclared **edge** table is auto-created
`TYPE ANY`, silently discarding the `IN`/`OUT` type constraint — which §4 records as the *only*
endpoint validation the engine offers. Reason (2) was previously unrecorded: a missing DDL entry for
an edge does not fail loudly, it **silently downgrades the guard**.

⚠ **OPEN RECONCILIATION ([#144](#144)):** the 2026-07-19 probe did **not** re-read the original
`scratchpad/102-recovery/` harness before contradicting its result, and says so — its own verdict on
that point is INCONCLUSIVE. Two harnesses can each be right about their own run. Read the original
FIRST and reconcile before rewriting finding #124 itself.

---

## 6. ⚠ WHERE THE VENDOR DOCS ARE WRONG

**This section can exist nowhere else. It is the most valuable thing in this file.**

### 6.1 The `IF NOT EXISTS` lie

Both the **DEFINE FIELD** and **DEFINE INDEX** pages state, verbatim:

> "If the field already exists, the `DEFINE FIELD` statement **will return an error**."
> "If the index already exists, the `DEFINE INDEX` statement **will return an error**."

**FALSE on 3.1.5 — and still FALSE on 3.2.1.** [PROBED 2026-07-12 on 3.1.5; RE-PROBED 2026-07-22 on
3.2.1 — §0] Re-defining an existing field with `IF NOT EXISTS` and a
*different* body returns **OK** and **silently keeps the old definition**. It does not error.

```
before          : DEFINE FIELD via ON q1 TYPE string ASSERT $value INSIDE ['register','explicit']
re-DEFINE (INE) : OK                       <-- NOT an error. The docs are WRONG.
after           : DEFINE FIELD via ON q1 TYPE string ASSERT $value INSIDE ['register','explicit']
CREATE via='publish' : RAISED -> Found 'publish' for field `via` … must conform to: …
                                            <-- THE OUTAGE, reproduced
re-DEFINE (OVERWRITE): OK
after                : … ASSERT $value INSIDE ['register','explicit','publish']
CREATE via='publish' : OK                  <-- CONTROL: the probe can see a success
```

**Why this matters more than a typo:** it is **load-bearing misinformation**. An engineer who read
that sentence would reasonably conclude that a stale field definition **cannot happen** — because a
mismatched re-definition would have *thrown*. **That is plausibly how `IF NOT EXISTS` was chosen in
the first place.** The trustworthy sentence is in the *next paragraph* (§1.2) — the one that names
our bug.

Upstream source of record (unfiled, not our call):
`docs.surrealdb.com` → `src/content/reference/query-language/statements/define/field.mdx:678`
and `.../define/indexes.mdx:541`.

### 6.2 The docs' silences (not lies — gaps we filled by measurement)

Every one of these is **probe-only**. Do not mistake them for vendor guarantees.

| Question | Our probed answer | Vendor |
|---|---|---|
| What happens to **existing rows** on a field-definition change? | No retro-validation; violations surface on the **next write**, loudly | **silent** |
| Can `ALTER FIELD` create a missing field? | **No** — raises; the `IF EXISTS` variant silently no-ops | silent |
| Does `OVERWRITE` **drop** clauses you omit? | **Yes** — full replace | implied, never stated |
| Is `DEFINE TABLE OVERWRITE` safe on a populated table? | **Yes** — fields, indexes and rows all preserved | silent |
| Does changing an ANALYZER re-tokenise an existing FULLTEXT index? | **NO** — stale until `REBUILD INDEX` | silent |
| Must a NEW field on a populated table be `option<>`? | **Yes** — a required one poisons every existing row; a `DEFAULT` does **not** rescue it | silent |

### 6.3 A doc *we* wrote was also wrong

A prior version of **this file** sold `ALTER` as *"in-place schema migration instead of
drop+recreate"* with *"full ALTER coverage"*. That generalised "3.1 added ALTER for 9 more resource
types" into "ALTER is how you migrate," and **nobody checked**. It is corrected in §1.3.
**Our own reference docs are a source, not an oracle, either.**

**And again, 2026-07-19, in the worse direction.** A version of §4 written EARLIER THE SAME DAY stated
that a typed relation table was *"the **only** endpoint validation the engine offers"*, and that
*"an application-level existence check remains the only guard"*. **FALSE** — the engine ships
`ENFORCED` (§4), documented, on our floor since 2.0.3. The ALTER error made us avoid a trap; **this
one would have made us hand-roll a guard the vendor already ships** — the packages-over-hand-rolling
failure, committed inside the file that exists to prevent exactly this.
**How it happened, because the mechanism is the lesson:** the claim was derived from five live
probes and never checked against the vendor's `DEFINE TABLE` page. **Probing can only find what you
already thought to test, and nobody thought to test a keyword they did not know existed.** One doc
page, read first, would have cost nothing and found it. That is the docs-first law's actual argument,
and this is its cleanest receipt.

### 6.4 The "dangling edges read as an empty array" claim

**[VENDOR]** [RELATE](https://surrealdb.com/docs/surrealql/statements/relate):

> "If the records to relate to don't exist, a query on the relation will still work but will return
> an empty array."

**FALSE as a reader would apply it.** [PROBED 2026-07-19] The *identity* traversal — the natural
fan-out query — returns the ghost as a **first-class member**:

```
SELECT ->to->agent AS recipients FROM message:m_real;
  [{'recipients': [agent:a_ghost, agent:a_real]}]      <-- ghost listed as a real recipient
SELECT count() FROM agent;  ->  1                      <-- no such node exists
```

The sentence is true only of the **dereferencing** forms (`FETCH`, or projecting a field) — and those
yield `None`, not `[]`, either. **Why it matters:** an engineer reading it concludes a dangling edge
is *self-announcing* (an empty result is visible; a wrong result is not). It is not — it is silently
indistinguishable in exactly the query a delivery-graph reader writes. Load-bearing misinformation
about a hazard we already carry as #105.

### 6.5 The Python SDK doc names the WRONG statement

**[VENDOR]** [executing-queries](https://surrealdb.com/docs/sdk/python/concepts/executing-queries):

> "When a query string contains multiple semicolon-separated statements, `.query()` returns only the
> result of the **last** statement."

**FALSE on SDK 2.0.0 — it returns the FIRST.** [CODE] `surrealdb/connections/async_ws.py:206-219`
checks and returns `response["result"][0]`; identical at ~20 `blocking_http.py`/`async_http.py`
sites.

**Why this one is worth more than the others:** the docs' version is the *reassuring* one. In
`BEGIN; …; COMMIT;` the LAST statement is the **COMMIT**, so an engineer trusting the doc believes a
failed transaction surfaces — because the COMMIT errors. The SDK reads index 0, which is the
**`BEGIN`**, and is always `OK`. **The doc describes precisely the behaviour that would have
prevented [#144](#144); the SDK does the opposite.** Independent, source-level corroboration of §3
and of #144's mechanism correction — arrived at with no probe at all.
**[VENDOR] The supported all-statements call is `query_raw()`** (per-statement `status`/`time`/
`result`) — which is what `execute_transaction` already rides.

### 6.6 Where the vendor is SILENT — claims for which WE ARE THE ONLY SOURCE

A documentation sweep (2026-07-19) checked every load-bearing claim in this file against the
official docs. Most upgraded to `[VENDOR]+[PROBED]`. **These did not** — no vendor page addresses
them, so they rest entirely on our own probes. **Treat them as the most fragile knowledge here:
they are the ones an engine upgrade could silently invalidate, with nothing upstream to warn us.**

1. `RELATE` onto an **undeclared** table auto-creates it `TYPE ANY`, silently discarding the
   `IN`/`OUT` guard (§4). Vendor silent on undefined targets entirely.
2. Concurrent first-write to an undeclared table **storms with retryable conflicts** (§5, #144).
3. The retryable marker is the literal string **`"can be retried"`** — it appears in no vendor doc,
   and there is still **no typed alternative** (§3, #111).
4. **Re-`DEFINE SEQUENCE` semantics** — bare `DEFINE` raises; no variant resets the counter;
   `BATCH`/`START` never migrate (#146).
5. `TYPE RELATION IN/OUT` rejects a **wrong-table** endpoint by field coercion — mechanism and
   error text are ours.
6. `RELATE $expr.field->…` is a **parse error** (§7); a bare `str` endpoint is rejected loudly (§4).
7. The **four-way-ambiguous** CAS return (§5) — the vendor confirms only the two-way ambiguity.
8. `UPDATE` of a relation edge's `in`/`out` is a **silent no-op** (§2).
9. Everything in §6.2's silences table — existing-row behaviour on a definition change, `ALTER FIELD`
   creation, `OVERWRITE` clause-dropping, `DEFINE TABLE OVERWRITE` on a populated table, analyzer
   re-tokenisation, the `option<>` requirement.
10. The SDK's **later-statement error swallowing** — undocumented, and the docs actively describe the
    opposite (§6.5).
11. **`CONTENT` composes with neither `SET` nor `MERGE`** (both parse errors), leaving
    `object::extend($bound, {computed})` as the only shape that mixes a bound payload with a
    store-side mint (§2). [PROBED 2026-07-24, 3.2.1]
12. **`SELECT *` OMITS a `NONE`-valued column entirely** → `KeyError`, which is the OPPOSITE of the
    documented missing-**projection**-reads-`None` behaviour (§2). The vendor addresses neither, and
    our own §2 sentence was silent about `SELECT *` for months. [PROBED 2026-07-24, 3.2.1]
    ⚠ Load-bearing for every `option<>` column: **a reader must not assume presence.**

---

## 7. SYNTAX GOTCHAS

Small, sharp, and each one cost somebody an hour. All [PROBED 2026-07-12] unless noted.

| Want | ✅ Correct | ❌ Parse error / wrong |
|---|---|---|
| Charset ASSERT on a field | `string::matches($value, '<re>')` — the **FUNCTION** form | `$value =~ '<re>'` — **PARSE ERROR** on 3.1.5 |
| A flexible optional object column | `option<object> FLEXIBLE` — **FLEXIBLE is TRAILING** | `option<object FLEXIBLE>` |
| RELATE endpoints | `RELATE $from->edge->$to` (bound RecordIDs) | `RELATE type::record(..)->edge->type::record(..)` — **PARSE ERROR** |
| A record from parts | `type::record(..)` | `type::thing(..)` — **not a 3.1.5 function** |
| FULLTEXT index clause | `FULLTEXT ANALYZER <name> BM25` | `SEARCH ANALYZER …` (the older form) |
| Max of a datetime column under GROUP BY | `time::max()` | `math::max` / `array::max` — accept it, **return garbage silently** |
| RELATE an endpoint you just created | `LET $m = (CREATE ONLY t …).id;` then `RELATE $m->e->$x` | `RELATE $m.id->e->$x` — **PARSE ERROR** (*"Unexpected token `.`, expected a relation arrow"*). Bind the id INTO the `LET`; you cannot reach through a field at the arrow. |
| RELATE endpoint values | bound **`RecordID`** objects | a bare **`str`** — `"Cannot execute RELATE statement where property 'in' is: 'message:m_real'"` |
| `ORDER BY` a column under an **EXPLICIT projection** [PROBED 2026-07-25, 3.2.1] | project the ordered column too: `SELECT a, b, ts FROM t ORDER BY ts` | `SELECT a, b FROM t ORDER BY ts` — **PARSE ERROR**: *"Missing order idiom `ts` in statement selection"*, with a second span pointing at the projection (*"Idiom missing here"*). `SELECT *` never hits it — so the rule that `option<>` columns want an explicit projection is exactly what walks you into this. |
| Bind a value against a **`session`** column [PROBED 2026-07-25, 3.2.1] | name the bind anything else: `WHERE session = $comms_session` | `WHERE session = $session` — ***"'session' is a protected variable and cannot be set"*, on a BARE SELECT.** §2 documents the write-side (`SET session = $session`); **the protection is wider than that — the BIND NAME ITSELF is refused**, whatever the statement. The column name is fine; only the `$session` parameter is reserved. |
| A **per-entry ASSERT** on an array column [PROBED 2026-07-25, 3.2.1] | TWO field rows — the array and its element path: `DEFINE FIELD refs … TYPE array<string> DEFAULT [] ASSERT array::len($value) <= 20` **plus** `DEFINE FIELD OVERWRITE refs[*] … TYPE string ASSERT string::len($value) <= 256`. The composed `DEFAULT [] ASSERT` clause works; count and per-entry asserts fire independently, and the element error names **`refs.*`** and the offending VALUE. | ⚠ **The element row without `OVERWRITE` → `"The field 'refs.*' already exists"`.** `DEFINE FIELD … TYPE array<T>` **IMPLICITLY DEFINES `<field>.*`**, so the element definition is always a RE-definition — §1.1's `OVERWRITE`-for-fields rule applies to it with no exception. A whole-array `$value.all(\|$x\| …)` closure also works and is a known-good fallback, but loses per-element error ergonomics (it dumps the whole array). |
| An ASSERT on an **`option<>`** field, when the value is absent [PROBED 2026-07-25, 3.2.1] | write the assert BARE: `TYPE option<string> ASSERT string::len($value) <= 256`. **The ASSERT is NOT evaluated when the field is NONE** — an omitted field is accepted, and the assert still fires on a supplied over-length value. | `ASSERT $value = NONE OR …` — harmless but **pure cruft**, and it teaches the next author that the guard is required. Do not copy the guard onto new `option<>` fields. |
| Compare `INFO FOR TABLE` output against the DDL you emitted [PROBED 2026-07-25, 3.2.1] | pin the **EMITTED** statement (house idiom) | the stored echo is **NORMALISED and will not match**: a closure `\|$r\|` comes back `\|$r: any\|`, and `option<array<string>>` comes back `none \| array<string>`. Any pin diffing the echo against emitted DDL mismatches on closure- or `option<>`-bearing definitions. |
| Put a `RecordID` in a `set` or use it as a dict key [PROBED 2026-07-27, SDK 2.0.0] | decode first — `str(record.id)` (the SDK's own rendering) and key on the `str` | **`RecordID` is UNHASHABLE** — `__hash__ is None` on SDK 2.0.0, so a `set()` / dict key raises `TypeError` at runtime. **Two independent agents hit this within one packet** (a probe script raised mid-body; a builder measured it deliberately), which is why it is here. ⚠ And decode with **`str(record.id)`, never `str(row["id"]).split(":", 1)[-1]`** — the split is right for `agent:abc` and **WRONG for a uuid-shaped id**, which the SDK renders `agent:⟨0199c4f1-7d2a-…⟩`. That exact guess cost **130 red pins** across two suites (finding #248: seven hand-rolled copies of this parse exist package-wide). |

---

## 8. OPEN HAZARDS & UNVERIFIED CLAIMS

Live defects and things we genuinely do not know. **Nothing here is settled — do not assume.**

- **[#107's TWIN, LIVE AND UNFIXED] `DEFINE ANALYZER IF NOT EXISTS` silently ignores a changed
  tokenizer/filter set.** Edit `_ANALYZER_TOKENIZERS` / `_ANALYZER_FILTERS` today and **the change
  never lands on any existing database.** It has never bitten only because `code_ident` has never
  changed. It is a loaded gun. And the fix is **not** simply flipping to `OVERWRITE` (§1.5) — a
  correct analyzer migration is `OVERWRITE` **+ `REBUILD INDEX`** on every FULLTEXT index.
- **[SAME CLASS] `DEFINE INDEX IF NOT EXISTS`** carries the identical silent-no-op hazard for any
  index change that is *not* the embedding dim (fields, analyzer, UNIQUE-ness). The dim case is
  covered by the fingerprint rebuild; **the others are covered by nothing.**
- **[#102, OPEN] The shared `_txn` conflict-retry budget is 2-way-tuned and completely un-jittered**
  (§5). Blocks `-n auto` as the full-suite checkpoint gate.
- **[#105, OPEN — and NO LONGER LATENT] Dangling `RELATE` edges, on BOTH endpoints** (§4). Goes live
  the moment any verb accepts a recipient/endpoint identity from a caller rather than resolving it
  from the store. An application-level existence check is the only guard; a typed
  `TYPE RELATION IN a OUT b` catches only wrong-*table* endpoints.
- **[UNVERIFIED] Does an edge-table LIVE SELECT fire on `RELATE`?** Never probed. The
  contentless-wake design makes an empty payload harmless (so #5014 cannot bite), but the *firing*
  itself is an assumption.
- ~~[UNVERIFIED] The #7061 cascade-delete interaction with UNIQUE-on-edge~~ — **SETTLED ABSENT**
  [PROBED 2026-07-19], see §4. Endpoint deletion cascades the edge and cleans the UNIQUE entry;
  re-`RELATE` succeeds. Kept struck rather than deleted so a reader who remembers the old ban sees
  it was retired deliberately.
- **[STALE PROSE, found 2026-07-13]** `surreal_schema.py:873` still explains behaviour in terms of
  *"`DEFINE FIELD IF NOT EXISTS` does NOT retro-validate existing rows"* — the **mechanism was
  retired** by #107's fix (fields are `OVERWRITE` now). The *behaviour* claim happens to remain true
  (measured: no retro-validation at DDL time either way), so **no gate will ever catch it** — it
  simply teaches a dead mechanism to the next reader. Same for `test_diff.py:982`'s comment.
  Flagged, not fixed (docs-only writable set).

---

## 9. OPS

- **Two stores, and confusing them is a production incident:**
  | Store | Port | Role |
  |---|---|---|
  | `spike-surreal` | **`ws://127.0.0.1:18000`** | **TEST.** Point tests here. |
  | `lore-surreal` | **`:18500`** | **PRODUCTION.** ⚠ **Never point a test at it.** |
- Both are **systemd/quadlet-managed** (`~/.config/containers/systemd/{lore-surreal,spike-surreal}.container`,
  `WantedBy=default.target` + linger) → they **auto-start on boot**. No manual `podman start`.
  Manage with `systemctl --user {start,stop,restart} {lore-surreal,spike-surreal}.service`
  (after editing a `.container`: `systemctl --user daemon-reload`).
- **Recovery** (image + both stores gone): image `docker.io/surrealdb/surrealdb:v3.2.1`,
  `--network=host`, `--userns=keep-id --user 1000:1000` (the `nonroot` image user + a 0700 data dir
  owned by 1000 → `PermissionDenied` without this), `--env-file ~/docker/mcp/lore-secrets/lore.env`,
  `start --bind 127.0.0.1:<port> rocksdb:/data/store.db`. Then rebuild the lore image and
  `lore-deploy start`. Full recipe: memory `surreal-stores-systemd-managed`.
- **Auth split:** DB-level users sign in with namespace + database + user + pass (a *different shape*
  from root signin). A VIEWER cannot `DEFINE` tables and nobody below root creates namespaces → **NS/DB
  creation + schema DDL must be a separate root/owner bootstrap step**; role connections skip it.
  (searcher = VIEWER; scout/indexer = EDITOR.)
- **HNSW is in-memory** (default 256 MiB, `SURREAL_HNSW_CACHE_SIZE`). 3.1 added **DiskANN**
  (persisted, larger-than-memory) — evaluate at Odoo scale.
- A live MCP session connects to lore only at session **start**: if the server was down then, the
  `mcp__lore_lore__*` tools stay unreachable until `claude --continue`.

---

## 10. CAPABILITY NOTES (the rest of the surface)

Kept brief — reach for these rarely; the sections above are where the defects live.

- **LIVE SELECT** — real-time notifications; DIFF mode; FETCH inside LIVE (≥2.2). **Single-node
  only** (#5070 open). **Hard limits, all honoured by `scout.py`:** WS-only; **params are IGNORED in
  a LIVE `WHERE`** (inline a charset-ASSERTed literal); the SDK's `.live(table)` is whole-table, so
  a filtered LIVE means `query("LIVE SELECT … WHERE …")` + `subscribe_live(uuid)`; best-effort,
  possibly out-of-order, **NO replay on reconnect**; the SDK silently orphans `live_queues` on a
  socket drop. **A poll fallback is MANDATORY.** Use it for a **contentless wake ONLY** — never as a
  source of truth.
- **CHANGEFEED + SHOW CHANGES** — durable, versionstamped, replayable change log
  (`DEFINE TABLE t CHANGEFEED 3d`). Retention-windowed; `SINCE` must post-date creation. Reach for
  cross-process ordered replay / audit / DR.
- **DEFINE EVENT** — server trigger on CREATE/UPDATE/DELETE (`$event`/`$before`/`$after`/`$value`).
  **Sync events run IN the triggering txn and can THROW to abort**; `ASYNC [RETRY] [MAXDEPTH]` runs
  out-of-txn. Weigh against a tested app-layer mirror; note the #7310 UNIQUE×EVENT interaction.
- **Record IDs** — `ulid()` / `uuid()` v7 are time-sortable (timestamp-prefixed, range-queryable);
  composite `[a,b,c]` ids supported (CBOR tag-8). Remember you **cannot prefix-match the id's string
  component** (§2).
- **DEFINE FUNCTION `fn::name()`** — reusable server-side SurrealQL. Reach for atomic ops shared by
  **non-Python** consumers; never for render-shaped logic.
- **DEFINE ACCESS TYPE RECORD / JWT** — per-record identity (`$auth`), signup/signin, row/field
  `PERMISSIONS … WHERE`. `DEFINE TOKEN` was **REMOVED** in 3.0. 3.1.5 fixed field-permission
  bypasses via graph traversal — **re-verify permissions on edge-heavy graphs**.
- **DEFINE BUCKET / DEFINE API** — **EXPERIMENTAL** (bucket gated behind
  `--allow-experimental files`). Artifacts stay files-on-disk referenced by refs.
- **`VERSION` / temporal reads** — `SELECT … VERSION d'…'`, propagated through graph/ref/FETCH in
  3.1. Needs history retention.
- **INFO / SHOW / EXPLAIN** — schema/index introspection; `EXPLAIN` reports pushed KNN filters.
  Gotcha: `INFO FOR INDEX` returns `{}` for non-concurrent builds.
- **Notable 3.1 deltas** — `value::expect`; `encoding::json::encode/decode`; **`time::min`/`time::max`
  return `NONE` for empty groups**; predicate prefilter always-on; W3C trace propagation; a built-in
  `surreal mcp` server.

---

## Sources

**Vendor** — [DEFINE FIELD](https://surrealdb.com/docs/surrealql/statements/define/field) ·
[DEFINE INDEX](https://surrealdb.com/docs/reference/query-language/statements/define/indexes) ·
[ALTER overview](https://surrealdb.com/docs/surrealql/statements/alter) ·
[ALTER FIELD](https://surrealdb.com/docs/surrealql/statements/alter/field) ·
[ALTER INDEX](https://surrealdb.com/docs/reference/query-language/statements/alter/indexes) ·
[REBUILD](https://surrealdb.com/docs/reference/query-language/statements/rebuild) ·
[Release 3.1](https://surrealdb.com/releases/3.1) · statements: define/sequence, define/table,
define/event, define/access/record, relate, upsert, show; datamodel: ids, references ·
issues #7061 #7310 #5014 #5070 · CVE-2026-49997.

**Ours** — findings **#93** (txn root-cause selection, resolved @ 93a9aab) · **#102** (hot-row mint
retry budget, open) · **#105** (dangling RELATE edges, open) · **#107** (the schema could not evolve
— the outage) · `REPORT-c1f-docs-surreal.md` (vendor citations + the ALTER probes) ·
`REPORT-c1f-contract-migration.md` §4 (the measured OVERWRITE matrix) · memories
`surreal-31-docs-audit-adjustments`, `read-the-docs-then-verify-them`,
`surreal-error-classifier-latent-edges`, `surreal-stores-systemd-managed` · live probes on
spike-surreal 3.1.5 (throwaway DBs; production `:18500` never touched).

<a id="107"></a>*#107 — `lore_findings get 107`. Read it once. It is the whole reason this file has
a "read this first" block.*

<a id="144"></a>*#144 — the #124 mechanism correction (the engine does **not** silently lose committed
rows; `query()`'s statement[0]-only validation hid retryable conflicts). Carries an OPEN
reconciliation against the original `scratchpad/102-recovery/` harness.*

<a id="146"></a>*#146 — `DEFINE SEQUENCE IF NOT EXISTS` inherits the silent-no-op migration hazard for
`BATCH`/`START`. Named re-open trigger: the day anyone changes either.*

**Correction pass 2026-07-19/20** (packet 03 kickoff — five live probes, then a documentation-first
reconciliation against the official docs, operator-ruled). Two of the three biggest results
CONTRADICTED careful prior reasoning, including reasoning in this file.

*From the probes:* §1.1 gained SEQUENCE and split TABLE into plain vs RELATION · §4's RELATE entry
corrected from "`in`" to **both endpoints**, with the caller-supplied `out` half and the
ghost-in-traversal receipt · the #7061 cascade question **settled ABSENT** · §5's #124 paragraph
**rewritten** (mechanism was wrong, conclusion stands, now on two measured reasons — see #144) ·
§5 gained the one-transaction fan-out measurement · §7 gained two RELATE gotchas · §8's
`sequence::next` `[UNVERIFIED]` line **deleted** as a self-contradiction of §5.

*From the docs-first pass (the one that found what probing could not):* **`ENFORCED` exists** and
this file had asserted the opposite — see §6.3, and §4 for its eight probed legs · §6.4 and §6.5
added (two more vendor falsehoods, the second an independent source-level corroboration of #144) ·
§3's root-cause rule was **FALSE and is fixed** — the code was always right, the prose taught a
retired mechanism · §2 gained the `UPDATE`-endpoint silent no-op · §1.5 gained the
`DEFINE TABLE OVERWRITE` safety proof with its positive control · citations upgraded from
`[PROBED]` to `[VENDOR]+[PROBED]` throughout §3/§4/§5 · **§6.6 added: the claims for which we are
the ONLY source.** · #111 answered (keep the substring; the trigger is not met).

**The method lesson, since it cost the most:** five live probes and a cold audit did not find
`ENFORCED`, because probing can only find what you already thought to test — and nobody thinks to
test a keyword they do not know exists. One doc page found it in minutes. **Read the docs first;
probe to confirm them and to find what they omit.**

Receipts: `REPORT-probe-pkt03-store.md` · `REPORT-docs-surreal-31-reconcile.md` ·
`REPORT-probe-enforced-clause.md` · `REPORT-audit-edge-preflight.md` (all preserved under
`docs/plans/v2/receipts/2026-07-19-packet03/`).
