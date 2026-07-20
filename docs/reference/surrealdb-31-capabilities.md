# SurrealDB — the canonical reference for this project

**Engine: `surrealdb-3.1.5`** (`docker.io/surrealdb/surrealdb:v3.1.5`) — live-read from the
test store, 2026-07-13. Python SDK `surrealdb>=2.0` (installed: 2.0.0; officially supports
servers 2.0.0–3.2.0). Server floor ≥3.1.0 (CVE-2026-49997).

> ## ⚠ READ THIS BEFORE YOU TOUCH THE STORE
>
> Six facts. Each one has already cost us something.
>
> 1. **`DEFINE … IF NOT EXISTS` is a SILENT NO-OP on an object that already exists.** It does
>    not error. Your changed definition simply never lands on a live store. **This caused a
>    100% production outage** ([#107](#107)) — and it was written in *this file* at the time.
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
| **[PROBED]** | Run live against spike-surreal 3.1.5 by us, with the date. |
| **[MEASURED]** | Observed in our own test/production runs (receipts named). |
| **[#n]** | A finding in the ledger (`lore_findings get n`). |
| **[CODE]** | Read out of our source, file:line. |
| **[INFERRED]** | Reasoned, not observed. Treat as a hypothesis. |
| **[UNVERIFIED]** | We do **not** know. Probe before depending on it. |

---

## 1. DDL & MIGRATION

The single most expensive area in this file. Read all of it before changing any DDL.

### 1.1 The decision rule

| Object | Clause | Why |
|---|---|---|
| **FIELD** | **`OVERWRITE`** | The only clause that makes a changed definition actually land. [#107] |
| **INDEX** | **`IF NOT EXISTS`** | `OVERWRITE` **rebuilds** the index over every row → boot-time crash on a dim change. |
| **ANALYZER** | **`IF NOT EXISTS`** | `OVERWRITE` lands the definition but does **not** re-tokenise built indexes → silent recall bug. |
| **TABLE** | **`IF NOT EXISTS`** | `OVERWRITE` is *safe* (probed) but our table clauses never change. Nothing to migrate. |
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
- **A missing SELECT projection reads `None`, not a `KeyError`.** Projecting a column that does not
  exist yields `None` — so a typo'd projection degrades **silently** into a null, it does not blow
  up. Validate the shape you got.
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
  explicitly.

---

## 3. TRANSACTIONS

- **⚠ The SDK's `.query()` validates ONLY statement[0].** [CODE, SDK 2.0.0:
  `_check_query_result(response["result"][0])`] Any multi-statement string whose **later** statement
  fails returns a per-statement `ERR` **with no top-level error** → a **silent partial apply**. This
  bit us as silent-partial-SCHEMA in all three `ensure_ready` DDL paths.
  > **NEVER send multi-statement SurrealQL through `query()`. Use `execute_transaction`, which
  > checks every statement.** (`DEFINE`-in-transaction is allowed on 3.1.5.)
- **⚠ Classify the FIRST failed statement, never the last.** [#93, RESOLVED @ 93a9aab] In a
  `BEGIN; …; COMMIT;` body, once *any* statement fails, **the COMMIT also errors** — with
  *"Cannot COMMIT: the transaction was aborted due to a prior error"*, which carries none of the
  real error's markers. Classifying `failed_statements[-1]` therefore **discards the real cause**
  and reports "unspecified rejection" for every rolled-back multi-statement txn. `_txn.py` now
  raises on `failed_statements[0]` — the first ERR is the root cause by execution order — and logs
  all of them. *This defect is why the C1 mint bug could hide: the collision's own rejection text
  was masked by the COMMIT's.*
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
    was FALSE — see §6.3.** Adoption status: probed by packet 03 (`REPORT-probe-enforced-clause.md`);
    ⚠ note that `ENFORCED` is a `DEFINE TABLE` clause and §1.1 puts TABLE on `IF NOT EXISTS`, so
    **adding it to an existing relation table is a candidate silent no-op — #107's shape.** Settle
    the migration before relying on it.
  - A **bare `str`** endpoint (rather than a bound `RecordID`) is rejected LOUDLY:
    `"Cannot execute RELATE statement where property 'in' is: 'message:m_real'"`. That is a helpful
    failure — do not "fix" it by pre-formatting ids into strings.
  - Note the original audit **could not make the RELATE fail with a bad id at all**. That inability
    *is* the finding.
- **UNIQUE index on a RELATION edge is LEGAL on our floor.** [CODE + PRODUCTION] `briefed` declares
  `UNIQUE(in, out)` (`surreal_schema.py:1071`) and runs in production. The old ban (#7061
  ghost-entry cascade bug) is **retired** — fixed in ≥3.1.0.
  - **SETTLED — the #7061 cascade hazard is ABSENT on 3.1.5.** [PROBED 2026-07-19] `RELATE` →
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
(16-way × 30 × 5 runs). **NOT gapless** — an aborted txn burns the number. Fine for monotonic ids
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

**FALSE on 3.1.5.** [PROBED 2026-07-12] Re-defining an existing field with `IF NOT EXISTS` and a
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
- **Recovery** (image + both stores gone): image `docker.io/surrealdb/surrealdb:v3.1.5`,
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

**Correction pass 2026-07-19** (packet 03 kickoff probes, operator-ruled): §1.1 gained a SEQUENCE
row · §4's RELATE entry corrected from "`in`" to **both endpoints**, with the `out`/caller-supplied
half and the ghost-in-traversal receipt · the #7061 cascade question **settled ABSENT** and its two
`[UNVERIFIED]` flags retired · §5's #124 paragraph **rewritten** (mechanism was wrong, conclusion
stands, now on two measured reasons) · §5 gained the one-transaction fan-out measurement · §7 gained
two RELATE syntax gotchas · §8's `sequence::next` `[UNVERIFIED]` line **deleted** as a
self-contradiction of §5. Receipts: `REPORT-probe-pkt03-store.md`.
