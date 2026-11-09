# SurrealDB — the canonical reference for this project

**Engine: `surrealdb-3.3.5`** (both stores, since **2026-11-07**; quadlets pin the EXACT tag
`docker.io/surrealdb/surrealdb:v3.3.5`, image id `d4330a269f11`). History: 3.1.5 → **3.2.1** on
2026-07-22 ([§0](#0-the-321-migration-receipts)); the floating `v3.2` tag then carried both stores to
**3.2.4** (finding #336); **3.2.4 → 3.3.5** on 2026-11-07, in place, forward-only (receipts in
[§0a](#0a-the-335-migration-receipts)). Python SDK **`surrealdb==3.0.0`** (exact pin, since packet 66,
2026-11-08 — receipts in [§0b](#0b-sdk-300-receipts-packet-66-2026-11-08); before that `surrealdb>=2.0`, installed
2.0.0, which no vendor statement covers against 3.3; §0a measured it working, with the full suite showing
no SDK regression). **Sections below that were measured on SDK 2.0.0 say so
where they stand; a `(SDK 3.0.0, packet 66: …)` note marks each one 3.0.0 changed.** Server floor ≥3.1.0
(CVE-2026-49997).

> **FLOATING TAG (finding #336) — CLOSED for the stores by the 3.3.5 migration:** both quadlets now pin
> `v3.3.5`, so a recreate or `podman pull` can no longer move the engine without a quadlet edit. (While
> they pinned `v3.2`, that tag had silently re-pointed to the one-way **3.2.6** by 2026-11-07.) Still
> re-read the version host-side (`curl :<port>/version`) before depending on a version-sensitive fact.
>
> **Version-provenance honesty:** most facts below were `[PROBED]` on **3.1.5** and are dated as such; a
> set was re-probed on **3.2.1** (§0) and a further set on **3.2.4** (the await build-probe, 2026-08-05 —
> §3, §8). Each `[PROBED … <version>]` label is KEPT at the version it was run on — a fact is **never**
> silently relabelled to a newer engine. *(Since 2026-11-07 the live stores run 3.3.5, and §0a re-probed a
> set on it; the 3.2.4 advice that follows predates that.)* If you depend on an un-re-probed fact on the live 3.2.4 store,
> re-probe it (3.2.4 is forward within the 3.2 minor, so a 3.2.1 re-probe is a strong but not guaranteed
> prior).

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
> 4. **Multi-statement work never goes through a bare `.query()`. Always `execute_transaction`.**
>    On SDK 2.0.0 `.query()` validated statement[0] ONLY: a later statement could fail and roll the
>    whole thing back while `query()` raised *nothing*. *(SDK 3.0.0, packet 66: `query()` now raises
>    the FIRST failing statement — but without `BEGIN` the statements after it still APPLY, and inside
>    `BEGIN … COMMIT` the error it raises is a cascade notice, not the cause — [§0b](#0b-sdk-300-receipts-packet-66-2026-11-08).
>    The rule is unchanged.)* [§3](#3-transactions)
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

## 0b. SDK 3.0.0 receipts (packet 66, 2026-11-08)

lore's Python SDK moved **`surrealdb` 2.0.0 → 3.0.0** on the 3.3.5 stores in packet 66. **The authority is
the operator rulings, `docs/plans/v2/sdk3-rulings.md` R1–R46** (cite them; do not re-derive them here).
- The cold audit's verdict at `88b06be` is GO (`docs/plans/v2/receipts/2026-11-08-sdk3/REPORT-coldaudit-66.md`
  §DELTA-2). That GO rests on reading (b) of finding #598, which is LOW and still open; strict reading (a)
  would be NO-GO.
- The in-image conformance run is *"PASS for the SDK-3 artifact, with named holes"*
  (`…/2026-11-08-sdk3/REPORT-conform-66.md`). `lore_diff` was not exercised, and #604–#606 were filed. Every `[PROBED]` fact in this
section ran on **SDK 3.0.0 + engine 3.3.5 + Python 3.14.7**. "storeref-66" below means the probe
`probe_storeref66.py` (28 checked legs plus informational ones, with controls; one throwaway DB on `:18000`, removed afterwards). Its
source is pasted verbatim in `docs/plans/v2/receipts/2026-11-08-sdk3/REPORT-storeref-66.md`, and the script
itself is archived at `docs/plans/v2/receipts/2026-11-08-sdk3/probes/storeref/probe_storeref66.py`.

- **⚠ [MEASURED 2026-11-08] The served production container is NOT on SDK 3.0.0 yet.** `lore-lore` runs
  image `43122071…` (`localhost/lore:latest`, built 2026-08-18), whose venv holds `surrealdb 2.0.0`.
  Packet 66 shipped no production deploy. By R19 Q1 the conformance image was tagged
  `sdk3-conform-<sha>`, never `latest`, and `latest`'s id was identical before and after
  (`REPORT-conform-66.md` §Teardown). So until the next rebuild, the 2.0.0-era facts this file marks as
  history still describe the RUNNING server, and the 3.0.0 facts describe the REPO and its tests. Re-check
  before you lean on either one: `podman inspect lore-lore --format '{{.Image}}'` against the image you built.
- **The pin.** [CODE] `loremaster/pyproject.toml` declares `surrealdb==3.0.0`, and `uv.lock` resolves
  `surrealdb 3.0.0` (commit `9863c11`). The Containerfile's `RUN uv sync --locked --all-packages`
  installs exactly the lock. [MEASURED] In-image, `importlib.metadata.version("surrealdb")` is `3.0.0`,
  from `/app/.venv/lib/python3.14/site-packages` (`REPORT-conform-66.md` §Step 2). ⚠ **`surrealdb.__version__`
  does not exist in 3.0.0** (an `AttributeError`). Read the version from the distribution metadata.
  R7 pins it exactly (3.0.1 was unpublished on PyPI as of 2026-11-07). R7 also records that 3.0.1 changes
  `str(RecordID)`, so re-probe this section on any SDK bump.
- **Result shapes: one entry per statement, and the FIRST `ERR` raises.** [CODE] SDK 3.0.0
  `connections/builders.py::_QueryState._statement_values` raises the first statement whose `status` is
  `ERR`; otherwise it returns every statement's `result`. [PROBED storeref-66 S1/S2/S2b]
  - `RETURN 1; RETURN 2` → `[1, 2]`, and `RETURN 1` → `[1]`.
  - **A raise does not mean nothing applied.** With no `BEGIN`, `CREATE a:1; THROW 'boom'; CREATE a:2`
    raises `ThrownError("boom")`, and BOTH rows exist afterwards: each statement is its own transaction.
  - **Inside `BEGIN … COMMIT` the raised error is a CASCADE NOTICE, not the cause.**
    `BEGIN; CREATE c:1; THROW 'boom'; COMMIT;` raises `QueryError` with `kind=Query`,
    `details.kind=NotExecuted` and the text *"The query was not executed due to a failed transaction"*.
    The THROW's own text is not in it, and nothing commits. R7 W6 records the same for a conflict. So
    root-cause selection still needs the per-statement entries: `execute_transaction` still rides
    `query_raw` and the semantic selector in §3, unchanged. *(SDK 2.0.0 instead returned a later
    statement's `ERR` silently: §3, §6.5.)*
  - **The seam rule** (R2; R8 F13): `_txn.one_statement_result` returns exactly ONE entry or raises
    `SurrealStoreError` (storeref-66 S1: a two-entry answer is refused). `run_query`, scout's command
    channel and the inbox awaiter all call it. The SDK-3 failure behind R2 was measured: a lost CAS read
    as the truthy `[[]]`, and 8/8 racers "won".
  - **The test harness's rule differs, deliberately** (R19 C10; contract surface).
    `tests/_surreal_harness.run()` answers the FIRST statement's result, because it is also the setup
    helper for multi-statement generated DDL. It FAILS CLOSED on an empty or non-list answer, because the
    #486 reaper reads `INFO FOR NS` through it. Pinned by `test_surreal_harness::TestRunAnswersItsFirstStatement`.
  - The conflict signal is the SDK's own predicate, `QueryError.is_transaction_conflict`. [CODE] SDK
    3.0.0 also ships `QueryDetailKind.TRANSACTION_CONFLICT`. `_txn._RETRYABLE_CONFLICT_KIND` is deleted
    (drop list #2, `df84764`).
- **Outcome UNKNOWN is not failure** (R5 rider 2, R7, R9 D1, R12 F18, R19 Q6).
  - Every SDK `TransportError` on a request becomes `_txn.SurrealOutcomeUnknownError`, a
    `SurrealConnectionError` subclass. That covers a timeout, a socket dropped mid-flight, and a request
    parked on a reconnect that never completed. A server-ANSWERED error is a definite failure and never
    this class (R12 F-b).
  - The served advice is ONE constant, `_txn.OUTCOME_UNKNOWN_ADVICE`: *"a write may have landed: verify
    before retrying; a read is safe to re-run"*. A renderer that knows its request's shape serves only its
    own half (Q6).
  - A served catch site must catch this class before it renders a definite failure. R9 D1 rules this for
    every served `SurrealConnectionError` catch site; R12 F18 extends it to the `SurrealStoreError` family
    (14 sites, the ruling's count). This reference has NOT counted the pins.
  - **Why "unknown" is real** ([MEASURED] by scout-40-sdk3 on memory engines 3.3.5 and 4.0; the durable
    record is **R7** in the rulings, because that scout's own report was not archived):
    - with streaming (the SDK default, which lore sets EXPLICITLY: `_txn.SURREAL_STREAMING = True`), a
      timed-out request is cancelled and commits nothing;
    - a disconnect mid-flight commits nothing;
    - **with `streaming=False` and a timeout, the ENGINE KEEPS RUNNING AND COMMITS**;
    - client transactions never stream.

    Bound (R7): SurrealKV and RocksDB are unprobed, and a commit racing the cancel was never constructed.
- **Connection policy: ONE factory** (R5; `_txn.open_surreal_connection`).
  - It uses `ReconnectOptions(attempts=-1, retry_delay=0.5, retry_delay_max=2.0)` and a request timeout of
    `SURREAL_REQUEST_TIMEOUT_SECONDS = 30.0`. That is SDK 3.0's own default, kept until measured (R5 F4b);
    R19 Q2's conformance grep is the re-open signal.
  - Named overrides go through `long_operation` (`ENSURE_READY_TIMEOUT_SECONDS`,
    `INDEX_TRANSACTION_TIMEOUT_SECONDS`, 300 s each). They are applied as `with connection.timeout(N)` at
    the seam.
  - [CODE] SDK `async_ws.py::_await_reconnect`: a request made during a reconnect waits, bounded ONLY by
    the request timeout, then raises `TransportTimeoutError`. A request in flight at a drop fails with
    `ConnectionUnavailableError` and is NOT re-sent (R5 grounds).
  - [MEASURED] A first connect to a store that is down raises `ConnectionUnavailableError`: the SDK does
    not reconnect a connection that never connected. That is why scout keeps its boot ladder (builder C-row
    #21, `REPORT-builder-66.md` §C-row measurement table).
  - No `websockets.*` class reached lore in 120 legs (`REPORT-builder-66.md` §FINAL drop-list fate table,
    row 9; C-row #9 has the 20 × {abort, close-frame} legs). The `WebSocketException` arm and SDK
    2.0's in-flight `KeyError` arm are both retired (drop list #1, #9).
- **`kill()` is bounded by the SDK's own timeout** (R41 FORK T, `5e464bc`;
  `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-13.md`).
  - [MEASURED] `kill()` on a dropped socket PARKS in `_await_reconnect` until the request timeout. It
    raised `TransportTimeoutError` after 30 s, 40/40. SDK 2.0 failed at once.
  - Teardown therefore runs `with connection.timeout(_txn.TEARDOWN_KILL_TIMEOUT_SECONDS): await
    connection.kill(id)`, with the constant at 2.0 s. Re-measured: 2.00 s, against 30.00 s uncapped.
  - The worst case is **2 × N**: the reconnect wait and the request each get the budget.
  - Not stdlib `asyncio.timeout`: it injects a `CancelledError` the SDK was not built to receive (RULING-13).
- **`close()` is idempotent** (R41 FORK S, `6b43b65`).
  - [CODE] SDK 3.0.0 `AsyncWsSurrealConnection.close` documents itself as *"Idempotent."*
  - [MEASURED] `close()` over a severed socket never raised, 40/40 (C-row #16).
  - [PROBED storeref-66 S6] A second `close()` raises nothing.
  - So the 18 `_safe_close` wrappers are retired. The live close pin is `5fb57fc`: 17 owners × 2 sever
    modes, plus scout's drop path.
- **`PreciseDatetime` and THE cursor codec** (R6 S2/F3, R34, R43 B1 `fda1411`, R44).
  - SDK 3.0.0 decodes every `datetime` column as a tz-aware UTC `PreciseDatetime` (a `datetime`
    subclass), keeping the engine's nanoseconds (C-row #8/#34).
  - A stamp an agent may HAND BACK is rendered with `isoformat_with_nanoseconds` and parsed with the SDK's
    `parse_instant`. Those are `_txn.served_instant_text` and `_txn.parse_served_instant`; the parser adds
    a zone-presence check, because `parse_instant` reads a zone-less text as UTC.
    [PROBED storeref-66 O2] `parse_instant` accepts 1–9 fraction digits, and a nine-digit text round-trips
    exactly. **The pair is THE cursor codec. A second codec is copy #2** (RULING-14).
  - ⚠ **`PreciseDatetime` `==` and `<` IGNORE nanoseconds** (#593). [PROBED storeref-66 O3] Two stamps
    differing only in ns compare `eq=True, lt=False`; the control, a different microsecond, compares.
    **Never compare, sort or take min/max of store stamps in Python.** Use the engine's `ORDER BY`, or
    `store.stamp_paging.stamp_key` (`(instant, nanosecond)`; R44).
  - A store-row stamp is CHECKED, never converted: `_txn.required_datetime` / `stored_datetime` (R34).
- **⚠ Python 3.14's `datetime.fromisoformat` silently truncates nine fraction digits to six.** This was the
  root of #590. [PROBED RULING-14 on 3.14.7; re-probed storeref-66 O1, control: a six-digit text
  round-trips exactly] `fromisoformat("…45.186697518+00:00")` returns `…45.186697+00:00` with no error.
  With `isoformat()` (µs) on the render side, the rollup cursor re-served the row it was read from (#590).
  Serving more digits alone would not have fixed it, because the parser threw them away.
- **`db.batch()` reports the cancellation notice instead of a THROW's own error** (#588; drop list #14 = KEEP).
  - [MEASURED, `REPORT-builder-66.md` §R-9 row #14] For `[CREATE, THROW, CREATE]` through
    `db.batch().execute()`, where the THROW's text quotes the cascade notice, `db.batch()` raises
    `QueryError kind=Query "…not executed due to a cancelled transaction"`: the wrong root cause. The
    control, a plain THROW, raises `ThrownError kind=Thrown`. Nothing commits either way.
  - `db.batch()` raises ONE error, so no per-statement entries exist for the rollback log.
  - So lore keeps `compose` + per-statement root-cause selection (§3). The trigger to retire it is an SDK
    release whose batch result selects by typed kind, not text. Filing upstream waits on the operator (#588).
- **Record-id TEXT: never `str(RecordID)`** (R7, `d41aa47`; `_txn.record_key` / `record_text`).
  [PROBED storeref-66 S3/O4/O5; audit `probe_record_text` in `REPORT-coldaudit-66.md` §Instruments]

  | key | engine `<string> id` | SDK 3.0.0 `str(RecordID)` | `RecordID.parse(str(rid)) == rid` |
  |---|---|---|---|
  | `'abc'` | `kt:abc` | `kt:abc` | yes |
  | `'01JABC…'` (ULID, digit-led) | `kt:01JABC…` | `kt:⟨01JABC…⟩` | **no** |
  | `'42'` (all-digit STRING) | ``kt:`42` `` | `kt:⟨42⟩` | — |
  | `'a-b'` (non-word) | ``kt:`a-b` `` | `kt:⟨a-b⟩` | **no** |
  | `42` (int) | `kt:42` | `kt:42` | **no** |

  - The engine renders a word key that holds a letter BARE, and backticks a non-word key or an ALL-DIGIT
    string key (`d41aa47` corrected the all-digit case).
  - SDK 3.0.0 brackets; 3.0.1 backticks (R7).
  - The rules (R7 (a)–(d)):
    - take the key from the PARTS (`record_key`);
    - build display text from the parts (`record_text`, which equals the engine form only for
      letter-holding word keys and composites);
    - text that is persisted, compared, or expected back from an agent comes from the engine
      (`<string> id` in the query).
  - Persisted bare strings needed no migration (R7).
  - [PROBED storeref-66 O5] `RecordID` is **hashable** on 3.0.0. The 2.0.0 row in §7 is history.
- **⚠ On 3.3.5, `field > $datetime` ADMITS non-datetime values.** [PROBED] `v > $since`, with `$since` a
  datetime:
  - ADMITS array, object, uuid and record values, and later datetimes;
  - EXCLUDES string, number, float, bool, `NULL`, duration, `NONE` and earlier datetimes.

  Receipts: R45 S6 (servicer); `REPORT-coldaudit-66.md` §DELTA-2 item 4b, with datetime controls on both
  sides; storeref-66 S4, on a SCHEMALESS table. Consequence: a non-datetime stamp is outside every
  stamp-paged leg. That is **KNOWN BOUND #597**, pinned (R46: pin-the-miss `de6e116`; the predicate is
  stated once in `stamp_paging.read_stamp_page`'s docstring, `d2df34c`). Its only door is an admin DDL
  retype (RULING-17). Why the engine orders these types this way is NOT established here.
- **`option<datetime>` on a SCHEMAFULL table rejects a literal `NULL`; Python `None` stores `NONE`.**
  [PROBED `REPORT-coldaudit-66.md` §DELTA-2 item 7; re-probed storeref-66 S5]
  - `SET t = NULL` → rejected (`InternalError`).
  - `CONTENT {…, "t": None}` through the SDK → accepted, and `t = NONE` reads true while `t = NULL` reads false.
  - Controls: a string is rejected and a datetime is accepted.
- **A BOUND record-id range is index-served and exact. The `name.value` mirror's KEEP basis has fallen**
  (drop-list row #25 of the packet doc, not finding #25; R43 §ADDENDUM).
  - [MEASURED, `REPORT-builder-66.md` §R-9 row "#25 cand. 2"] `FROM $r`, with
    `$r = RecordID('name', Range(BoundIncluded(lo), BoundExcluded(hi)))`, plans as **`RecordIdScan`** and
    returns 20/20, exact. Two prefixes (`FROM $r1, $r2`) plan as a `Union` of two RecordIdScans, 40/40.
  - By contrast, `string::starts_with(record::id(id), $p)` and `WHERE id >= $lo AND id < $hi` both
    TableScan.
  - **Audit CONFIRMED** (`REPORT-coldaudit-66.md` §DELTA item 5): 303 production-shaped values + 21 traps,
    set equality both ways, EXPLAIN over a deny-by-default operator allowlist with firing controls.
  - The fate is RETIRE, owed to a follow-up packet; no schema was touched.
  - That packet's notes: `INDEX_SCAN_OPERATORS` lacks `RecordIdScan`; a prefix ending in U+10FFFF has no
    next bound; skip surrogates.
- **`INSERT … ON DUPLICATE KEY UPDATE` has overwrite parity with per-row `UPSERT … CONTENT`** (R4, R27-2a, `66a9979`).
  - [PROBED by the builder, `REPORT-builder-66.md` §Progress log + §R-9 row X13] A batched
    `INSERT INTO chunk $rows ON DUPLICATE KEY UPDATE <every CHUNK_COLUMNS column> = $input.<column>`
    equals per-row `UPSERT … CONTENT` byte-for-byte:
    - an overwrite drops an absent optional column;
    - a duplicate id within one batch → the last row wins;
    - `$input.<absent>` reads NONE;
    - control: a plain `INSERT` over an existing id → `AlreadyExistsError`.
  - This is what retired the statement cap. A file's index write is still ONE transaction, but its rows
    ride one batched `INSERT` per table. The bound is now `_txn.TXN_ROW_HARD_CAP = 50_000` rows (warn at
    10,000; R4, R8 F12). `TXN_STATEMENT_HARD_CAP` (5,000) is deleted; R3 measured `test_comms_tool.py`
    composing to 5,113 statements and being refused.
- **HTTP `POST /import` caps one request at 4 GiB** (#603). [MEASURED, `REPORT-conform-66.md` §Step 4b]
  A full prod dump through the single-POST restore driver got *"HTTP 413: 'length limit exceeded'"*.
  [VENDOR] `manage/instances/connect/via-http.mdx` (request-size table) gives `/import` 4 GiB. At
  2026-11-08, `snapshot_entry` alone is 6.25 GB of the dump, so no single POST can restore it. The fix
  shape (chunk the import, or `surreal import`) belongs to packet 65 (#603). See also §6.7.
- **Q4: drop rows #29 / #30 accepted. lore takes the SDK defaults and sets neither** (R19 Q4).
  - **Keepalive** [CODE `surrealdb/__init__.py`]: `ping_interval=30.0`, `ping_timeout=10.0`, so a
    half-open peer is noticed in about 40 s. A reader that holds the stream without reading starves the
    pong (packet doc `sdk3-python-sdk-3-migration.md`, the whole-stream-hold instrument note).
  - **Version gate** [CODE `surrealdb/features.py`]: `version_check=True`, with servers from
    `MINIMUM_VERSION = "2.0.0"` (inclusive) to `MAXIMUM_VERSION = "5.0.0"` (exclusive).

## 0a. The 3.3.5 migration receipts

Both stores moved **3.2.4 → 3.3.5 on 2026-11-07, in place** (no export/import; the vendor guide
`build/migrating/from-old-surrealdb-versions/32-to-33.mdx`, now in the `surrealdb-docs` tier, says a 3.2
datastore opens on 3.3 directly). **FORWARD-ONLY:** per the same guide a 3.2 binary started on a migrated
store *"reads it wrongly"* rather than refusing it. The ONLY way back is a cold copy:
`/backups/lore/surreal-pre-3.3.5-cutover-20261107T135252Z` (prod, taken at the cutover) and
`/backups/lore/surreal-pre-3.3.5-20261107T122016Z/` (both stores, earlier that morning) — each verified
byte-identical with `diff -rq`. Restore = stop the unit, swap the dir, set the quadlet image to
`v3.2.4` (never `v3.2`, which now means the one-way 3.2.6). **Do not plan a rollback via a 3.2.x
`import` of a dump:** 3.2.x's ENFORCED-relation import drops edges whose endpoint table sorts later
(`member_of`), fixed only in 3.3.0 (engine language test `reproductions/828_enforced_relation_import_order.surql`).

- **[MEASURED] Data integrity.** On boot 3.3.5 applied three startup data migrations (copy sequence
  definitions out of the table band; re-key module definitions; rebuild forward doc-ID mappings) and
  recorded `version=3.3.5`; `/ready` answered 200 in ~4 s. Prod inventory before vs after (every ns/db,
  per-table `count()` + HNSW index DDL): **45 tables, 2,700,624 rows, zero differences.** Positive
  control: the same diff over two inventories taken 90 minutes apart reported the 4 tables that grew.
- **[MEASURED] kNN duplicate-vector exposure: none.** The 3.2.x HNSW bug drops the 10th+ record sharing
  one identical vector. Counting `GROUP BY crypto::md5(<string> embedding)` groups with n > 9 over all
  four HNSW indexes (`chunk`/`memory` × `lore`/`demand_intelligence`) gave **0** (control: a 10-copy
  fixture → 1 at n > 9, 0 at n > 10). No `REBUILD INDEX` was needed for correctness; 3.3 serves
  3.2-built indexes on their old layout (a rebuild would only add 3.3's bitmap / pre-filtered kNN).
- **[MEASURED] Full suite, attributed.** On the 3.3.5 test store: 534 failed / 13759 passed. Rerunning
  every file containing a failure against a throwaway 3.2.4 RocksDB store (via `LORE_TEST_SURREAL_URL`;
  provenance: the control store gained the `lore_test` namespace) gave 530 failed / 1475 passed —
  **530 failures are identical on both engines** (pre-existing RED contracts). Of the 4 that failed only
  on 3.3.5, one (`test_harness_database_lifecycle_486` reap bound) passed 3/3 in isolation on 3.3.5
  (load-sensitive under `-n 12`, not engine). **Three fail deterministically (3/3) on 3.3.5 and pass
  3/3 on 3.2.4**, and are the same instrument defect — see the next bullet.
- **[MEASURED] EXPLAIN operator names changed for multi-`OR` index plans (bitmap fusion, 3.3.0).** The
  member READ filter (`scope = … OR scope = … OR …`, #413's expanded form) now plans as
  `Filter → BitmapResolve → BitmapOr → BitmapIndexScan ×N` — still fully index-served, **no
  TableScan** — where 3.2.4's operator list contained an `IndexScan` element. Pins that assert the
  literal `"IndexScan" in operators(plan)` go red on a correct, index-served plan. The property is
  "index-served, no TableScan"; assert it through an allowlist of index-scan operators, not one name.
  Single-index plans still render `IndexScan`: no other `IndexScan` pin joined the 3.3.5-only failure
  set (pins inside the 530 pre-existing reds were not separately checked).
- **[PROBED 2026-11-07, 3.3.5 vs a 3.2.4 control, identical script]** unchanged on 3.3.5:
  - #107: `DEFINE FIELD IF NOT EXISTS` over an existing field is still a **silent no-op**; `OVERWRITE`
    still migrates it (§1.1 / §6.1 hold).
  - §5 CAS shape: matching `WHERE` updates; stale `WHERE` → `[]`; missing id → `[]`. A data clause
    that would fail coercion on a `WHERE`-excluded row returns `[]` with no error on **both** engines.
  - §6.6 #14 still holds, and has a second face: with a plain `DEFINE INDEX … FIELDS tags`,
    `WHERE tags = 'x'` → `[]` **and whole-array `WHERE tags = ['x','y']` → `[]` too**, while the same
    queries on an UNINDEXED table return the row for the whole-array form — **adding the index changes
    the answer**, on 3.2.4 and 3.3.5 alike. `CONTAINS` is correct either way.
- **[PROBED 2026-11-07, 3.3.5] Field ASSERTs still fire under 3.3's second-pass ASSERT ordering.**
  The deployed production definitions, verbatim: `role ON agent TYPE string ASSERT
  string::len(string::trim($value)) > 0` rejects `''` and `'   '` on CREATE and accepts `'member'`;
  `ack_note ON to TYPE none | string ASSERT string::len($value) <= 4000` rejects 4001 chars on RELATE
  **and** on UPDATE and accepts 4000. (The `probe_governed_63c` / `probe_drain_read_63b_ii_b` C-controls
  that fail on these fields test HEAD's generated DDL, where 63b-ii-b / 63c-i-a deliberately DROPPED
  those store ASSERTs into the writers — a stale probe premise, not an engine change.)
- **[PROBED 2026-11-07] CHANGED on 3.3.5: `DEFINE SEQUENCE OVERWRITE` resets the counter** (§1.1
  SEQUENCE row). Production declares sequences `IF NOT EXISTS`, so no live path is affected.
- **Correction to §0 below:** SurrealDB **does** now tag patch releases (`v3.2.1`–`v3.2.4` were tagged
  retroactively on 2026-08-17; `v3.2.5`, `v3.2.6`, `v3.3.0`–`v3.3.5` exist).
- **[VENDOR, not probed here] Other 3.3 changes that touch this file** (32-to-33 guide): `UPDATE`/`UPSERT`
  evaluate `WHERE` before the data clause from one pre-write image; field clauses run in dependency
  order with `ASSERT` as a second pass (error ORDER may change — §6.6 #3); `POST /import` answers
  **422** for a partial import (§6.7 rows 2–4 describe 3.2.4); `/health` is 200 during startup — **use
  `/ready`**; sequence export/import fixes (3.2.5/3.3.0).

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

Corpus note: this repo now indexes the SurrealDB docs and the engine's **CI-verified SurrealQL
language tests** as lore tiers (`surrealdb-docs`, `surrealql-tests`). *(Originally pinned at the `v3.2.0`
tag; since 2026-11-07, [MEASURED] from each corpus dir's `PROVENANCE.yaml`: `surrealql-tests` at engine
tag `v3.3.5`, and `surrealdb-docs` at surrealdb/docs commit `9b533d1f` (2026-10-28, the last before the 4.0
docs; it documents 3.3.4 and has no 3.3.5-specific page).)* A
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
| **SEQUENCE** | **`IF NOT EXISTS`** | A **bare** `DEFINE SEQUENCE` **RAISES** *"The sequence 'x' already exists"* — and `ensure_ready()` re-applies the DDL every boot, so a bare DEFINE is a **boot-time crash**, exactly the INDEX failure mode. ⚠ Residual: like ANALYZER/INDEX, a changed `BATCH`/`START` then **never migrates** onto an existing store ([#146](#146)). Verified on 3.1.5–3.2.4: **no** variant (`IF NOT EXISTS` *or* `OVERWRITE`) resets the counter [PROBED 2026-07-19]. ⚠ **CHANGED ON 3.3.5: `DEFINE SEQUENCE OVERWRITE` now RESETS the counter to its `START`** (`START 10` → nextval 10; `OVERWRITE … START 100` → nextval **100**, where 3.2.4 returned 11) [PROBED 2026-11-07, 3.3.5 vs a 3.2.4 control, [§0a](#0a-the-335-migration-receipts)]. So `OVERWRITE` on a sequence that `ensure_ready()` re-applies every boot **would re-issue numbers at every boot** — the catastrophic case is ruled out only because the clause here is `IF NOT EXISTS` (which still neither resets nor migrates `START`: nextval 101 after `IF NOT EXISTS … START 500`). Never switch this row to `OVERWRITE`. |

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

> **[RE-MEASURED 2026-07-26 on 3.2.1 — §1.4 CONFIRMED, with a second address, because the first one
> does not resolve.]** `REPORT-c1f-contract-migration.md` is cited here and in §8 and is **tracked
> nowhere in this repo** (`git ls-files` → empty) — #152/#153's dangling-address class, sitting under
> the load-bearing claim that answers #107. The claim is NOT in doubt; its receipt was unreachable.
> **Resolvable receipt:**
> `docs/plans/v2/receipts/2026-07-26-packet11i-build/REPORT-fixwave-11ia-1.md` **§2.2** — a three-leg
> isolated probe (`int DEFAULT 0` · bare `string` · `string DEFAULT 'x'`, each added alone to a table
> already holding a row) in which **all three REJECT** an unrelated `UPDATE` with
> `Expected <type> but found NONE`. **A `DEFAULT` does not rescue an existing row**, exactly as this
> section says.
> ⚠ **And the trap that probe fell into first, which is the reusable part:** its initial fixture
> created the "legacy" row *after* the full DDL was applied, so `DEFAULT 0` filled it at CREATE and
> the UPDATE passed trivially — appearing to REFUTE this section. **A fixture that writes its legacy
> row after the migration cannot see this hazard at all.** Write the row under the OLD DDL, then
> migrate, or you will measure nothing and believe §1.4 is wrong.

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

### 1.8 UNIQUE over an `option<>` (nullable) field — multiple NONE COEXIST

**[PROBED 2026-08-20, 3.2.4 — `scripts/probe_unique_nullable_48.py` (committed, self-checking,
exit 0 with positive controls); receipts
`docs/plans/v2/receipts/2026-08-20-packet48/REPORT-probe-unique-null-48.md`.]** Packet 48's
`principal.subject` (an `option<string>` UNIQUE column, NONE until an OAuth login fills it)
forced this, and the **vendor docs are SILENT** on it — so it was settled by construction.

- **A plain `DEFINE INDEX … FIELDS <col> UNIQUE` over `<col> option<string>` (= `none | string`)
  PERMITS MULTIPLE rows with the column = NONE.** Fail-open coexistence (4 unset rows coexisted).
  This is exactly the pre-create-a-row-by-another-key-then-fill-later pattern: many rows carry
  NONE at once and the UNIQUE index does not treat them as duplicates.
  ⚠ **Do NOT assume the SQL-ish "one NULL only" behaviour.** A careful engineer expecting
  `option<> UNIQUE` to reject the 2nd NONE would design the fill-later pattern wrong — the 2nd
  `CREATE` would appear to fail. It does NOT fail. This is a **#107-class trap: an unwritten
  engine fact, believed rather than probed** (which is why it is written here).
- **The backstop still holds: the SAME NON-NONE value IS rejected** — on CREATE **and** on the
  `UPDATE` that fills a previously-NONE row to a value another row already holds (the fill path).
  So a real (non-NONE) key maps to ≤1 row; only NONE is exempt.
- **A FILTERED / PARTIAL unique index is NOT SUPPORTED.** Every spelling — `… UNIQUE WHERE col !=
  NONE`, `… WHERE col IS NOT NONE`, `… FIELDS col WHERE … UNIQUE` — is a **parse error**
  (`Unexpected token 'WHERE'`); `WHERE` on `DEFINE INDEX` is COUNT-only, not a row predicate. And
  it is not needed: plain `UNIQUE` over `option<>` already gives multiple-NONE + unique-non-NONE.

Provenance (stored shape): `DEFINE INDEX <n> ON <t> FIELDS <col> UNIQUE` over
`DEFINE FIELD <col> ON <t> TYPE none | string`. [Finding #388.]

---

### 1.9 A schema-BEHIND store (a dump restored with no server boot) — the governed-migration facts

Both facts below were **[PROBED 2026-09-30 on the TEST store `ws://127.0.0.1:18000`, the quadlet's floating
`v3.2` tag — 3.2.4 per MEMORY.md, not re-measured]** in a minted `unique_database()` (reaped), with controls;
instrument + verbatim output in the packet-63c-i-a fix6 builder report (§STORE-FACT PROBE, archived with the
63c receipts). They are why the migrate verb's pre-boot schema gate
(`principals._schema_predates_refusal`, packet 63c amendment 37 §13 D) is shaped as it is.

- **`INFO FOR TABLE <undefined table>` returns EMPTY maps, NOT an error** — measured
  `{'events': {}, 'fields': {}, 'indexes': {}, 'lives': {}, 'tables': {}}`. So a table gate must read
  `INFO FOR DB`'s `tables` (as `principals._agent_migration_preconditions` and `PrincipalStore._table_exists`
  do), **never infer definedness from `INFO FOR TABLE`**: an undefined table and a defined table with no
  fields answer identically.
- **An `UPDATE` assigning a REMOVED field on a SCHEMAFULL table is SILENT over 0 rows and RAISES over ≥ 1
  row** — after `REMOVE FIELD scope ON TABLE memory` (answers `None`; `INFO FOR TABLE memory` then omits
  `scope`), `UPDATE memory SET scope = … WHERE scope IS NONE` answered `[]` over zero rows and raised
  `InternalError: Found field 'scope', but no such field exists for table 'memory'` over one row (control:
  the same UPDATE over one row on the healthy table stamped it). So **a schema precondition must be derived
  from the SCHEMA (`INFO FOR TABLE`'s `fields`), never from the write's outcome**: on a pre-boot store with
  zero legacy rows the write "succeeds" silently and the next legacy row fails later, out of context.
  (Note the kind: `Internal` with no typed `details` — the untyped set in §3/§6.)

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
- ~~**`str(RecordID)` round-trips.**~~ **FALSE on SDK 3.0.0** *(packet 66; the 2.0.0-era claim was "the
  SDK's `RecordID` stringifies to `table:id` and parses back")*. 3.0.0 brackets a digit-led, non-word or
  all-digit-string key (`kt:⟨01J…⟩`), and `RecordID.parse(str(rid)) != rid` for those and for an int
  key ([PROBED] storeref-66 O5; R7). Never build or parse id text from `str(RecordID)`: use `_txn.record_key`
  / `record_text`, or the engine's `<string> id` ([§0b](#0b-sdk-300-receipts-packet-66-2026-11-08)).
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
- **⚠ `IN` INSIDE AN `OR` IS A TABLESCAN TRAP — expand it to per-value equalities** [PROBED
  2026-08-23, 3.2.4, `scripts/probe_read_filter_61b.py`, #413; the packet-61b read-filter emitter].
  On its own, `WHERE col IN $set` on an indexed `col` **IndexScans** (a `UnionIndexScan`; `IN []` →
  `EmptyScan`, safe). **BUT the same `IN` as one disjunct of an `OR` makes the WHOLE `OR` TableScan** —
  even though every *other* disjunct (and the `IN` alone) IndexScans. The defeating ingredient is `IN`
  inside the `OR`, not the `OR` itself and not compound `AND` disjuncts. **Fix: EXPAND the `IN` into
  N per-value equality disjuncts** (`col = $v1 OR col = $v2 OR …`, bound params, omit when the set is
  empty) — then the whole predicate is an index-served union, no `UNION`-of-queries needed. This is a
  #107 shape: a flat `OR … col IN $set` is green on a small/virgin DB and a full TableScan on a large
  dirty store. **Composite corollary (same probe):** a single `(scope, owner_principal, owner_agent)`
  composite is leading-column only — a disjunctive read filtering both `scope` AND `owner_principal`
  needs **separate** indexes on each.
- **⚠ Indexing an ARRAY column: the element path `<field>.*` is the ONLY spelling that serves
  containment — and the plain spelling builds an index that answers a DIFFERENT question, silently.**
  [VENDOR] the DEFINE INDEX page documents array-element composite indexes since 3.1.0
  (`DEFINE INDEX tag_age ON article FIELDS tags.*, age`, accelerating `CONTAINS` / `CONTAINSANY` /
  `ANYINSIDE` — `define/indexes.mdx` §*Array-element composite indexes*). [PROBED 2026-08-01, 3.2.1 —
  receipts + verbatim instrument:
  `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md` §3.1]:
  - `DEFINE INDEX … FIELDS classes` (no `.*`) on an `array<string>`: **every containment spelling**
    (`'x' INSIDE classes`, `classes CONTAINS 'x'`, `CONTAINSANY`) **TableScans** — useless.
  - ⚠ The one predicate that plain index DOES accelerate is `WHERE classes = 'x'` — which
    **IndexScans and returns `[]`**. No error; the plan proves the index fired; the answer is wrong.
    The natural-looking index plus the natural-looking equality = a fast, silent, empty result.
  - `FIELDS classes.*` (probed as a SINGLE-field element path, beyond the vendor's composite
    example): all three containment spellings IndexScan and return correct rows.
  - Composite indexes are **leading-column only** — probed on both an element-path composite
    (`FIELDS classes.*, level`) and a scalar one (`FIELDS name, source_book UNIQUE`): a
    trailing-column-only predicate TableScans. Useful corollary: ONE `UNIQUE(name, source_book)`
    serves both cross-book uniqueness and the leading-column exact-name lookup.
  - **[PROBED 2026-08-24, 3.2.4 — re-confirmed forward off 3.2.1, plus the OR/empty facts;
    `scripts/probe_dnd_multitag_schema.py`, self-checking, exit 0]** over a `FIELDS <f>.*`
    element-path index: `<f> CONTAINSANY [a, b]` **and** a same-field OR
    (`'a' INSIDE <f> OR 'b' INSIDE <f>`) are **BOTH `UnionIndexScan`** (each disjunct an
    `IndexScan` child) — so the `IN`-in-`OR` TableScan trap above does **NOT** extend to two
    array-containment disjuncts; `CONTAINSANY` is the cleaner plan (no residual `Filter`
    wrapper the OR carries). ⚠ **But `<f> CONTAINSANY []` (empty set) TableScans** — an emitter
    MUST omit the clause when the set is empty, exactly the omit-when-empty rule the `IN`-in-`OR`
    note carries. The bare-index silent-`[]` equality trap and **member-exact** array membership
    (`'Forest' INSIDE <f>` does NOT match an element `'Foresthome'`; `IN` on a joined STRING is
    substring — the false-match a joined column would ship) both reproduce **unchanged on 3.2.4**.
    Corroborates §4's plain-table-read pattern: a two-level containment taxonomy expands via
    indexed edge reads (`WHERE in = $x` leading, `WHERE out = $y` with its own index) then feeds
    an indexed `CONTAINSANY $expanded` — never a traversal-in-`FROM` (§6.6 item 13).
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

- **⚠ (HISTORY, SDK 2.0.0) The SDK's `.query()` validated ONLY statement[0].** [CODE, SDK 2.0.0:
  `_check_query_result(response["result"][0])`] Any multi-statement string whose **later** statement
  failed returned a per-statement `ERR` **with no top-level error**: a **silent partial apply**. This
  bit us as silent-partial-SCHEMA in all three `ensure_ready` DDL paths.
  *(SDK 3.0.0, packet 66: `query()` answers one entry per statement and RAISES the FIRST `ERR`
  ([§0b](#0b-sdk-300-receipts-packet-66-2026-11-08)). It is still not a multi-statement tool. Without
  `BEGIN`, the statements after the failing one still apply. Inside `BEGIN … COMMIT`, what it raises is
  the first CASCADE notice (`NotExecuted`), not the root cause. Single-statement callers go through
  `_txn.one_statement_result` (R2).)*
  > **NEVER send multi-statement SurrealQL through `query()`. Use `execute_transaction`, which
  > checks every statement.** (`DEFINE`-in-transaction is allowed on 3.1.5.)
- **⚠ Classify SEMANTICALLY — POSITION IS WRONG AT BOTH ENDS.** [#93, RESOLVED @ 93a9aab] In a
  `BEGIN; …; COMMIT;` body, once *any* statement fails, **the COMMIT also errors** — with
  *"Cannot COMMIT: the transaction was aborted due to a prior error"*, which carries none of the
  real error's markers. So `failed_statements[-1]` **discards the real cause**.
  **⚠ BUT `[0]` IS ALSO WRONG, AND A PRIOR VERSION OF THIS SECTION TAUGHT IT.** [PROBED 2026-07-19]
  The engine stamps CASCADE notices on statements *before* the offender, so `[0]` is typically
  *"The query was not executed due to a failed transaction"* — a notice, not the cause.
  **The CODE was already right and this prose was stale** (fixed here 2026-07-19; the code never had
  the bug): `_txn._domain_root_cause` picks the first **non-cascade** entry — *"selecting by POSITION
  is refused at both ends … only a SEMANTIC selector is correct."* *(This is the §8 stale-prose class:
  a doc teaching a retired mechanism, which no gate will ever catch.)*
  **⚠ SUPERSEDED 2026-09-29 (packet 63c-i-a, amendment 37 §5–§7) — the selector is KIND-seeking, not
  marker-seeking.** The 2026-07-19 text above named a text marker (`"was not executed due to"`); that
  constant is gone. On 3.2.4 every cascade entry is TYPED: a rollback's root cause is the first entry
  that `_txn._is_domain_cascade_notice` does not call cascade, and that predicate is the SDK's OWN
  `QueryError.is_not_executed or QueryError.is_cancelled` over the one parse of the entry — no kind
  string of ours, no text. Measured on 3.2.4 (builder-63c-i-a-a28c §REQ-3): statements BEFORE the
  offender and the refused COMMIT carry `details.kind: NotExecuted`; statements AFTER it carry
  `details.kind: Cancelled`. `TimedOut` is SUBSTANTIVE (a statement that ran and timed out is the
  cause). The degenerate all-cascade list degrades to the LAST entry. The adjudication lives in ONE
  place, `_is_domain_cascade_notice`'s docstring; the engine text is logged server-side as evidence.
  *The original #93 defect is why the C1 mint bug could hide: the collision's own rejection text
  was masked by the COMMIT's.*
- **[VENDOR] The supported all-statements call is `query_raw()`** —
  [executing-queries](https://surrealdb.com/docs/sdk/python/concepts/executing-queries):
  *"If you need the results from every statement, use `.query_raw()` instead"* (per-statement
  `status`/`time`/`result`). It is what `execute_transaction` already rides, and still rides on SDK
  3.0.0 ([CODE] `_txn._txn_query_raw`). ⚠ The same page lies about `.query()` itself: see §6.5.
- **Client-side conflict retry is MANDATORY.** [PROBED] The engine does **not** auto-retry user
  transactions. **The retry signal is TYPED** [PROBED 3.2.4, both paths — contract-63c-i-a-a28c §A.2,
  builder-63c-i-a-a28c §REQ-3, blindreader-63c-i-a-3 §7 P2]: `details.kind == "TransactionConflict"`
  (under `kind: Query`) on the per-statement COMMIT entry (transactional path) and on the raised
  `QueryError` (single-statement path). The code decided by the symbol `_txn._RETRYABLE_CONFLICT_KIND`.
  *(SDK 3.0.0, packet 66: that symbol is DELETED. The decision is the SDK's own
  `QueryError.is_transaction_conflict` (drop list #2, `df84764`), and retries run on native tenacity
  `AsyncRetrying` (R11/R18). [§0b](#0b-sdk-300-receipts-packet-66-2026-11-08).)*
  The text *"can be retried"* (live: *"…Transaction conflict: Resource busy. This transaction can be
  retried"*) is EVIDENCE, logged server-side, **never consulted for a decision** — a finding body
  quoting that phrase must not buy engine retries. *(Superseded 2026-09-29: until then this bullet
  called the literal marker the only signal; that was measured against SDK 2.0.0 / engine 3.1.5 and is
  no longer true — the store is forward-only at 3.2.4.)* 3.1 exposes OTel counters
  `surrealdb.transaction.retries` / `.conflicts`.
  - **#111 ANSWERED — trigger MET (2026-09-27).** The typed alternative lives in `details.kind`, ONE
    LEVEL BELOW `ErrorKind` — which still has no retryable member (`Validation, Configuration, Thrown,
    Query, Serialization, NotAllowed, NotFound, AlreadyExists, Connection, Internal`), exactly as the
    2026-07-19 read found; that read looked one level too high. The SDK ships
    `QueryDetailKind.{NOT_EXECUTED, TIMED_OUT, CANCELLED}` (and the matching `QueryError.is_*`
    predicates) but **NO constant or predicate for `TransactionConflict`** — a bare literal in `_txn`,
    pinned by the live-shape cells. *(That was SDK 2.0.0. SDK 3.0.0 ships BOTH:
    `QueryDetailKind.TRANSACTION_CONFLICT` and `QueryError.is_transaction_conflict` ([CODE]
    `surrealdb/errors.py`), and the bare literal is retired. [§0b](#0b-sdk-300-receipts-packet-66-2026-11-08).)*
- *(HISTORY, SDK 2.0.0. SDK 3.0.0, packet 66: an in-flight request at a drop fails with the SDK's typed
  `ConnectionUnavailableError` and is not re-sent; no `KeyError` and no `websockets.*` class reaches
  lore. The `KeyError` arm is retired (drop list #1), and the connection reconnects itself through the
  shared factory's `ReconnectOptions` ([§0b](#0b-sdk-300-receipts-packet-66-2026-11-08)). The bullet
  below still describes a server running a 2.0.0 image.)*
  **[PROBED]** A socket drop with queries **in flight** surfaces a raw `builtins.KeyError(uuid)`
  from SDK 2.0.0's response routing (6/6 futures) — *not* `CancelledError`. The next call heals via
  `ConnectionClosedError`. Classify `KeyError` tightly, at the SDK-await boundary only.
  ⚠ **"heals via `ConnectionClosedError`" names the ERROR SHAPE normalizing, not the connection
  auto-recovering** — the raw `KeyError` on the in-flight call becomes a clean `ConnectionClosedError`
  on the *next* call, which `is_connection_error` then classifies as transport → `drop` →
  reconnect-on-the-call-after-that, via the owner's `_ensure_connection`. It is not automatic and it
  is not instantaneous. (#250 misread this as "the connection recovers," reported a contradiction
  against a full-server-restart bounce, and it wasn't one — packet 07a settled it live.)
  **[RE-PROBED 2026-08-05 on 3.2.4 — shape UNCHANGED]** 6/6 in-flight awaits raise
  `KeyError(request-uuid)`; the next call raises `ConnectionClosedError`. The mechanism is
  SDK-2.0.0-side (`_recv_task` clears `self.qry` racing `_send`'s `del`), so it is
  **engine-version-independent** and holds until the SDK version changes (receipt: lore memory
  `bef131a1`; finding #336).
- **[PROBED]** One WS connection multiplexes concurrent `query()` safely (uuid-keyed futures).
- **⚠ A `RETURN` inside `BEGIN … COMMIT` ENDS THE TRANSACTION EARLY AND COMMITS WHAT RAN BEFORE IT — and every
  statement after it reports `status: OK`, so `execute_transaction`'s per-statement verification CANNOT
  see the truncation.** **[VENDOR]** `return.mdx` §*Return breaks execution*: *"`RETURN` breaks execution
  of statements, functions and transactions"*, with the exact example `BEGIN; RETURN 1; CREATE a; --
  Is not executed; COMMIT;` — DOCUMENTED, and unread by this repo until finding [#497](#497) (the
  docs-first law's own receipt, again). **[PROBED 2026-09-26, 3.2.4 — contract-58-r2
  (`c42eeaf:REPORT-contract-58-r2.md` §INSTRUMENTS `return_in_txn.py`, through the production
  `TaskLedger._apply`), re-probed the same day by sidecar-64 over `POST /sql` with two controls
  (instrument pasted verbatim in `REPORT-sidecar-64.md` Task 15 — archived under
  `docs/plans/v2/receipts/` at 64 close):** `BEGIN; CREATE a; RETURN NONE; CREATE b; COMMIT;` → only
  `a` exists and **all four statements report `OK`** (the skipped `CREATE b` comes back `result: null,
  status: OK`); the `LET $pad = NONE` control leaves `a` and `b`; **a `THROW` placed AFTER a `RETURN`
  never fires** (`BEGIN; CREATE a; RETURN NONE; THROW 'x'; COMMIT;` → `a` committed, no error) while the
  same `THROW` without the `RETURN` aborts (the table never exists). What the vendor does NOT say
  (§6.2): that the earlier statements COMMIT, and that the skipped ones report success. **House rule:**
  a composed fragment never contains a top-level `RETURN` — a THROW-guard after one is DEAD and a
  truncated apply reads as green; `compose`'s envelope-integrity check should refuse it (finding
  [#501](#501)). This is how packet 58's padding mutation (`RETURN NONE` appended to a shell output)
  silently stranded stragglers instead of moving the cap: a measurement that reads as success.

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
- **⚠ A graph TRAVERSAL NEVER uses a secondary index.** [PROBED 2026-08-01, 3.2.1 — receipt
  `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md` §3.3, probe 5 J4]
  Every traversal plan is a `GraphEdgeScan` from the start record, with filters applied as per-row
  predicates — a defined index on the filtered field provably never appears in the plan for
  `SELECT VALUE <-edge<-(node WHERE field = $v) FROM start:id`. Bounded by the start node's degree,
  which is usually what you want — but **you cannot index your way out of a traversal.** For an
  indexable read, query the edge table AS A PLAIN TABLE (`SELECT VALUE in.* FROM edge WHERE
  out = $node AND in.field = $v`, with an index on `out`) — which is how `graph_surreal.py` already
  reads the code graph (plain SELECTs on `refers`; not one arrow traversal in its read surface).
  **This fact decides FIELD-vs-EDGE-HOP modelling questions:** a scalar attribute (a level, a rank)
  filtered through a hop is un-indexable by construction — keep scalars as indexed fields and spend
  edges on real relationships. ⚠ Return-shape corollary, same probes: the traversal spelling
  returns `[[…]]` (one array per start record) where the edge-table spelling returns a flat list —
  a render-consistency trap if both feed one served tool.
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
> validated **statement[0] only** on SDK 2.0.0 (§3) — with `BEGIN` at index 0, every later `ERR` was
> discarded and the call read as success. *(SDK 3.0.0 raises the first `ERR` instead, §0b; the
> mechanism below is the 2.0.0 history of #124.)* Under full per-statement checking: **10 OK / 10 readable, ZERO loss**;
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
| Does a `RETURN` inside `BEGIN … COMMIT` COMMIT the statements before it, and how do the skipped ones report? | **Commits them**; every skipped statement reports `status: OK` (invisible to per-statement verification); a later `THROW` never fires | the BREAK is documented (`return.mdx`); the commit + the OK-status of the skipped statements are **silent** |

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

*(SDK 3.0.0, packet 66: the quoted sentence is false on 3.0.0 TOO, in a third way. `query()` returns
EVERY statement's result, one entry per statement, and raises the first `ERR`. [CODE]
`connections/builders.py::_QueryState._statement_values`; [PROBED] `RETURN 1; RETURN 2` → `[1, 2]`
([§0b](#0b-sdk-300-receipts-packet-66-2026-11-08)). The line numbers above are 2.0.0's. Whether the current
vendor page still carries the "last statement" sentence was NOT re-checked in packet 66. The analysis
below is SDK 2.0.0 history, still true of any server running a 2.0.0 image.)*

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
3. The retry marker **`"can be retried"`** appears in no vendor doc — and neither do the per-statement
   `details.kind` values `TransactionConflict` / `NotExecuted` / `Cancelled`, all three measured live
   on 3.2.4; the SDK's `errors.py` names two of them (`QueryDetailKind.NOT_EXECUTED` / `.CANCELLED`).
   **The typed alternative EXISTS (§3); the vendor prose is silent, not the engine.** *(Corrected
   2026-09-29 — this item previously said there was "no typed alternative".)* And the UNTYPED set, a
   fact of its own: the UNIQUE-index prefix, `ASSERT` and coercion rejections arrive as
   `kind: Internal` with `details: None`; the recursion-depth rejection (#66) as `kind: Validation`
   with `details: None` — for these, text may pick a teaching LABEL, never the class or the retry
   (packet 63c-i-a amendment 37 §1).
4. **Re-`DEFINE SEQUENCE` semantics** — bare `DEFINE` raises; `BATCH`/`START` never migrate under
   `IF NOT EXISTS` (#146). Through 3.2.4 no variant reset the counter; **on 3.3.5 `OVERWRITE` resets
   it to `START`** (§1.1 SEQUENCE row, [§0a](#0a-the-335-migration-receipts)) — the first fact on this
   list an engine upgrade has actually invalidated.
5. `TYPE RELATION IN/OUT` rejects a **wrong-table** endpoint by field coercion — mechanism and
   error text are ours.
6. `RELATE $expr.field->…` is a **parse error** (§7); a bare `str` endpoint is rejected loudly (§4).
7. The **four-way-ambiguous** CAS return (§5) — the vendor confirms only the two-way ambiguity.
8. `UPDATE` of a relation edge's `in`/`out` is a **silent no-op** (§2).
9. Everything in §6.2's silences table — existing-row behaviour on a definition change, `ALTER FIELD`
   creation, `OVERWRITE` clause-dropping, `DEFINE TABLE OVERWRITE` on a populated table, analyzer
   re-tokenisation, the `option<>` requirement.
10. The SDK's **later-statement error swallowing** — undocumented, and the docs actively describe the
    opposite (§6.5). *(SDK 2.0.0 only. On SDK 3.0.0 `query()` raises the first `ERR`, so nothing is
    swallowed. What remains ours alone: without `BEGIN` the later statements still APPLY after the raise,
    and inside `BEGIN … COMMIT` the raised error is the cascade notice, not the cause (§0b, storeref-66
    S2/S2b). This is the second item on this list an upgrade has invalidated: #4 fell to an engine
    upgrade, this one to an SDK upgrade.)*
15. **CANDIDATES, not yet checked against the vendor docs:** SDK 3.0.0 facts that rest only on our own
    measurement (packet 66, [§0b](#0b-sdk-300-receipts-packet-66-2026-11-08)). Packet 66 ran no
    documentation sweep. Until one does, treat these as un-swept, not as vendor-silent:
    - `PreciseDatetime` `==` / `<` ignore nanoseconds (#593);
    - `db.batch()` reports the cascade notice instead of a THROW's own error (#588);
    - `kill()` parks in `_await_reconnect` until the request timeout;
    - on 3.3.5, `> $datetime` admits array/object/uuid/record values (#597);
    - Python 3.14's `fromisoformat` truncates nine fraction digits silently. That one is a stdlib fact,
      not a vendor one, and the Python docs were not checked for it.
11. **`CONTENT` composes with neither `SET` nor `MERGE`** (both parse errors), leaving
    `object::extend($bound, {computed})` as the only shape that mixes a bound payload with a
    store-side mint (§2). [PROBED 2026-07-24, 3.2.1]
12. **`SELECT *` OMITS a `NONE`-valued column entirely** → `KeyError`, which is the OPPOSITE of the
    documented missing-**projection**-reads-`None` behaviour (§2). The vendor addresses neither, and
    our own §2 sentence was silent about `SELECT *` for months. [PROBED 2026-07-24, 3.2.1]
    ⚠ Load-bearing for every `option<>` column: **a reader must not assume presence.**
13. **A `WHERE` over a subquery-`FROM` that yields an ARRAY is evaluated ONCE over the whole
    array, not per element** — all-or-nothing, in BOTH directions: a field predicate finds no such
    field on the array and returns `[]` (false-empty); a traversal predicate flattens over every
    member and keeps them ALL (**false-INCLUDE** — a "level 4" filter serving a level-1 row, no
    error anywhere). [PROBED 2026-08-01, 3.2.1, seven controlled legs —
    `docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md` §6.2] The vendor
    documents per-row `WHERE` over a **plain** subquery (`from.mdx`:
    `SELECT * FROM (SELECT age >= 18 AS adult FROM user) WHERE adult = true`) and is silent on the
    single-value/array shape (`SELECT VALUE <-edge<-node FROM ONLY x` — `UnwrapExactlyOne` makes
    the outer `FROM` one array). **Rule: never put a traversal-producing subquery in a `FROM`** —
    use the node-side parenthesised filter (`<-edge<-(node WHERE …)`) or read the edge table as a
    plain table; both measured correct.
14. **The plain-array-index silent-`[]` equality trap** (§2): `DEFINE INDEX … FIELDS <array_col>`
    (no `.*`) + `WHERE <array_col> = 'x'` IndexScans and returns `[]` with no error. The vendor
    documents the correct `.*` element-path form (since 3.1.0) but nowhere says the plain spelling
    is useless for containment, nor that the one predicate it accelerates answers a different
    question. [PROBED 2026-08-01, 3.2.1]

### 6.7 `POST /import` and `surreal export` files — NOT atomic, errors ride an HTTP 200, and the reference example is broken

**[PROBED 2026-09-26, surrealdb-3.2.4 — probe-64, eleven curl legs into throwaway `test_dump_probe_*`
DBs on `:18000`, each with a control; instrument pasted VERBATIM in `80409f4:REPORT-probe-64.md`
Appendix A (§3 is the claim table — a SHA-qualified path, so it resolves after the report is archived
under `docs/plans/v2/receipts/`); the driver-side consequences are PINNED by
`scripts/test_restore_prod_dump.py` over the committed `scripts/restore_prod_dump.py`.]** Packet 64's
S2 leg is the first thing in this repo to restore a production dump; nothing below was written down
before it, and three of the facts are the vendor saying the opposite.

| # | the vendor says | 3.2.4 does |
|---|---|---|
| **1** | **[VENDOR]** `reference/rest-api/http-protocol.mdx` §`POST /import` shows `curl … -d file.surql` as THE example | **BROKEN.** `-d file.surql` sends the literal string → **HTTP 400**; `-d @file` strips newlines, so the export's leading `-- …` comment swallows the whole file → **HTTP 400**. Only `--data-binary @file` (the shape the surreal-deal tutorial happens to use) imports. |
| **2** | **silent** on the response | Success statements return NOTHING under `OPTION IMPORT`; the body is `[]` **iff every statement succeeded**; each failure is one `{"status":"ERR",…}` entry. **A consumer must check the body, never the status code.** |
| **3** | **silent** on atomicity | **NOT ATOMIC.** A runtime error mid-file (a duplicate `CREATE` → `AlreadyExists`) is an `ERR` entry inside an **HTTP 200** and the import **CONTINUES** — the statements after it land. |
| **4** | **silent** | A **parse error** mid-file is also **HTTP 200** + one `ERR` (`Parse error …`); statements BEFORE it are applied and everything AFTER it is **silently NOT** — a partial restore that reads as success to anything keyed on the status code. |
| **5** | **silent** on whether the target DB must exist | An **absent** DB is HTTP 200 + ONE `ERR` (`database … does not exist`) — **yet later statements ran**: the table came back `TYPE ANY SCHEMALESS` (its `SCHEMAFULL` define failed) while fields, events and rows landed. A silent SCHEMA DOWNGRADE with one error line — the §1.7 schemaless-auto-create hazard through the import door. **Always `DEFINE DATABASE` first.** |
| **6** | ✅ `OPTION IMPORT;` must be the first statement (≥ 3.0.4) | **HTTP 400** *Import requires `OPTION IMPORT;` as the first statement* — the one loud refusal in the set. |
| **7** | ✅ "field processing" is disabled | `ASSERT` bypassed (`$value < 10` stored 99), `VALUE` bypassed, `EVENT` not fired. Restored rows are **byte-faithful and never re-validated** — so a restored legacy row may violate the CURRENT DDL's asserts, which is exactly the §1.4 dirty-store condition a migration leg exists to reach (and exactly what makes the S2 restore a real fixture rather than a fresh-DB fiction). |
| **8** | ✅ `Accept` "required" | Not enforced (omitted → 200 `[]`). |
| **9** | `Authorization` optional | A wrong password is **HTTP 401** `The password did not verify` (the auth IS checked). |
| **10** | — | **The raw `surreal export` file is REFUSED as written.** Both `/backups/lore/lore-prod-*.surql` open with a tracing line (`…Z  INFO surrealdb::method::export: Exporting bytes`) and close with one — the export was captured with its log stream — and line 1 yields **HTTP 400** `Invalid statement: Parse error …`. Strip exactly the log lines (the driver counts them: 2 per dump) and require `OPTION IMPORT;` as the first STATEMENT after them. |

**And the probe's own lesson, kept (a probe needs a control):** `THIS IS NOT SURREALQL;` is NOT a parse
error — it parses as the expression `THIS != SURREALQL`. The first parse-error probe was invalid for
that reason; row 4 was re-run with `SELECT FROM WHERE };`.

**House rules that follow, each pinned in the driver:** accept an import only on HTTP 200 **and** a
body of exactly `[]`; `DEFINE DATABASE` before every import; strip the export log lines; treat any
`ERR` entry as a partial restore (STOP, never "mostly worked"). Restored rows are legacy rows in the
§1.4 sense — migrate them, do not trust them to satisfy today's asserts.

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
| Put a `RecordID` in a `set` or use it as a dict key [PROBED 2026-07-27, SDK 2.0.0] *(SDK 3.0.0, packet 66: `RecordID` IS hashable, so key on the `RecordID` itself, as graph de-dupe does since `ead3356` ([PROBED] storeref-66 O5; §0b). The row below is 2.0.0 history. Its `str(row["id"]).split` warning still holds; build text with `_txn.record_key`.)* | decode first — `str(record.id)` (the SDK's own rendering) and key on the `str` | **`RecordID` is UNHASHABLE** — `__hash__ is None` on SDK 2.0.0, so a `set()` / dict key raises `TypeError` at runtime. **Two independent agents hit this within one packet** (a probe script raised mid-body; a builder measured it deliberately), which is why it is here. ⚠ And decode with **`str(record.id)`, never `str(row["id"]).split(":", 1)[-1]`** — the split is right for `agent:abc` and **WRONG for a uuid-shaped id**, which the SDK renders `agent:⟨0199c4f1-7d2a-…⟩`. That exact guess cost **130 red pins** across two suites (finding #248: seven hand-rolled copies of this parse exist package-wide). |
| Decode a record id **SERVER-SIDE** in a `SELECT` whose **FROM is an ARRAY of bound RecordIDs** that may contain a ghost [PROBED 2026-07-28, 3.2.1] | project the **BARE `id`** and decode CLIENT-SIDE (`str(record.id)`): a RecordID naming no row is then **silently dropped** from the result, which is the fail-CLOSED behaviour a bounded read wants — `SELECT id, status FROM array::map([…], \|$v\| type::record('task',$v))` | **`record::id(id)` is an ENGINE ERROR**: *"Incorrect arguments for function `record::id()`. Argument 1 was the wrong type. Expected `record` but found `NONE`"*. The FROM-clause dereference yields `NONE` for the ghost and the function refuses it — **and inside a `BEGIN…COMMIT` this rolls the WHOLE transaction back**, turning the exact phantom-endpoint case the read exists to serve into a failure. ⚠ **Scope, measured:** `record::id()` on a FIELD VALUE (e.g. `record::id(in)` over an edge table holding a dangling endpoint) is **UNAFFECTED** — the value is a RecordID whether or not the row exists; only the FROM-clause dereference produces `NONE`. (#267, cost a rolled-back migration in packet 04b-1.) |
| Address a row whose id the SDK minted as `RecordID("t", "4")` — a numeric-LOOKING **string** id [PROBED 2026-08-01, 3.2.1] | bind the `RecordID` as a parameter (always sound) — or the documented backtick literal `` t:`4` `` ([VENDOR] `record-ids.mdx`: a number-as-string id is stored backticked **precisely because `article:10` and `` article:`10` `` are DIFFERENT records** — the int-vs-string distinctness is vendor-documented, not ours) | `SELECT * FROM t:4` — that literal names the **INT-id** record, a different row entirely; with only the string-id row present it reads as **`[]`**, no error. And `t:'4'` is a **PARSE ERROR** (*"Unexpected token `a strand`"*) — the single-quote escape does not exist. Corollary: **never mint numeric-looking ids** (levels, CRs, page numbers, editions) — prefer non-numeric slugs or always-bound RecordIDs. This nearly shipped as a false "nested traversal filters return empty" engine bound; only a positive control caught it. |

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
- **[#102, ~~OPEN~~ → FIXED 2026-07-14 at `9d29111`; corrected here 2026-07-26]** ~~The shared
  `_txn` conflict-retry budget is 2-way-tuned and completely un-jittered (§5). Blocks `-n auto` as
  the full-suite checkpoint gate.~~ **BOTH HALVES ARE NOW FALSE.** §5 of *this file* records the
  fix: `retry_on_conflict` draws **fresh full jitter per attempt**, and `-n auto` is this repo's
  **standard** gate (`CLAUDE.md`: measured 846s → 88s, identical pass count). Left visible rather
  than deleted because the correction is the lesson: **§5 and §8 of one document contradicted each
  other for twelve days**, and a retrieval chunk arrives without its neighbours (#160) — so a reader
  landing here alone was taught a mechanism that no longer exists, in the file this repo makes a
  REQUIRED FIRST READ. Found by `builder-11ia-1` during packet 11-i-a, which is to say: found by
  someone obeying the instruction to read this file first, which is the only reason it was found at
  all.
- **[#105, GUARDED on `to` + `briefed`; OPEN elsewhere] Dangling `RELATE` edges, on BOTH endpoints**
  (§4). Goes live the moment any verb accepts a recipient/endpoint identity from a caller rather than
  resolving it from the store. **The engine's `ENFORCED` clause guards BOTH endpoints (§4) and is now
  live on `to` (`df59f76`) and `briefed` (`6f0e03a`); `refers`/`answers_to` remain unguarded pending
  packet 43.** `ENFORCED` is a **BACKSTOP, not a replacement**: it reports ONE bad endpoint, as
  untyped prose, only AFTER the write is attempted, aborting the txn — and the seam's error hygiene
  withholds even that from the caller — **so an application-level check remains the only layer that
  can TEACH.** A typed `TYPE RELATION IN a OUT b` alone catches only wrong-*table* endpoints.
  ⚠ **This bullet read *"an application-level existence check is the only guard"* until 2026-07-27** —
  the very sentence **§6.3 of this file records as FALSE** (*"this one would have made us hand-roll a
  guard the vendor already ships"*), surviving in the open-hazards summary twelve sections below its
  own correction. Caught by packet 04a's fix wave, not by any gate. **If you are adding a hazard
  bullet here, check whether §4 or §6 already settles it** — a summary that contradicts its own
  authority is worse than no summary, because this is the file every store brief is told to read
  FIRST.
- **[PROBED 2026-08-05, surrealdb-3.2.4] An edge-table LIVE SELECT FIRES on `RELATE`.** Both
  whole-table `.live(<edge>)` and filtered `LIVE SELECT * FROM <edge> WHERE out = <literal>` deliver a
  normal `CREATE` notification carrying the full edge record `{id,in,out,fields}`; an edge UPDATE
  re-fires `action=UPDATE` on the whole-table form (the re-dispatch storm `CommandSubscriber` avoids by
  filtering). Filtered `WHERE out=<literal>` discriminates correctly (spurious + negative controls held).
  The contentless-wake assumption holds (the payload is non-empty but scout ignores it). **A poll
  fallback is STILL MANDATORY** — LIVE is best-effort, single-node only (#5070), no replay on reconnect,
  the SDK silently orphans `live_queues` on a socket drop (receipt: lore memory `bef131a1`; finding #336).
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
- **[PROBED 2026-08-17, spike-surreal 3.2.4] The QUERY-TOO-COMPLEX parse recursion-depth branch
  is LIVE on 3.2.4 — but ONLY for the fulltext `@@`/RRF query SHAPE, and this shape-specificity
  is NEW.** The classifier's `_ERROR_CLASS_QUERY_TOO_COMPLEX` branch (`_txn.py`, keyed on the
  marker `"recursion depth"` — finding #66's 3.1.5 boundary of ~40 fulltext tokens / ~120 `@@`
  clauses) still fires on 3.2.4, but the limit is a **whole-query parse-depth** property, **not
  operator-agnostic**. Simple-operator chains no longer trip it at any realistic size (probed
  to **40000 OR-clauses, 64000 nested parens, 32000 nested fn calls — all execute FINE**); even
  a bare `@@`-only predicate chain at **400 clauses** executes fine in **isolation**. It is
  tripped ONLY by the full `hybrid_search` / `recall` **RRF-fusion query** — the `@@` chain
  EMBEDDED in `search::score` / `search::rrf` / the dual-arm UNION, a much deeper parse tree —
  at #66's ~120-clause boundary. **An isolated construct is a FALSE NEGATIVE** ("a probe needs
  a control": `scripts/probe_query_complexity_07.py` first read the branch as DEAD on 3.2.4
  until the EXISTING live tests corrected it — the probe's committed as a negative-space
  receipt). The authoritative, **standard-gate** instrument is
  `test_bypassing_both_clamps_still_raises_a_classified_store_error`
  (`test_surreal_store.py::TestResidualRejectionStillLaunders` +
  `test_memory_backend.py::TestRecursionDepthClassificationAtRecallSeam`): it runs the REAL RRF
  path with the clamps bypassed and asserts the laundered `"query too complex"` label, GREEN on
  3.2.4 ONLY if the engine still emits `"recursion depth"`. That doubles as the drift alarm — it
  goes RED the day the engine rewords the marker OR lifts the limit (the #336 floating-tag class).

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
- **Recovery** (image + both stores gone): image `docker.io/surrealdb/surrealdb:v3.3.5`. That is the EXACT
  tag both quadlets pin since 2026-11-07 (header; §0a). [MEASURED 2026-11-08] `lore-surreal.container`
  reads `Image=docker.io/surrealdb/surrealdb:v3.3.5`. *(Until 2026-11-07 this line named the floating
  `v3.2` tag, then 3.2.4 / `6e2f7f0134c7`. `v3.2` now resolves to the one-way 3.2.6, so never recover
  with it; §0a.)*
  `--network=host`, `--userns=keep-id --user 1000:1000` (the `nonroot` image user + a 0700 data dir
  owned by 1000 → `PermissionDenied` without this), `--env-file ~/docker/mcp/lore-secrets/lore.env`,
  `start --bind 127.0.0.1:<port> rocksdb:/data/store.db`. Then rebuild the lore image and
  `lore-deploy start`. Full recipe: memory `surreal-stores-systemd-managed`.
- **⚠ NEVER run `surreal <subcommand> --help` (or any usage/help output) inside a store container.**
  ([#601](#601), 2026-11-08.) [MEASURED 2026-11-08] Both store quadlets load
  `EnvironmentFile=…/lore-secrets/lore.env`, which defines `SURREAL_USER` / `SURREAL_PASS`. The CLI's help renders every env-backed option with its CURRENT value
  (`[env: NAME=<value>]`). `podman exec lore-surreal /surreal export --help` printed the **production root
  password** in clear into an agent's transcript (`REPORT-conform-66.md` §INCIDENT). The class is any
  help/usage/debug output of the `surreal` CLI in an environment that carries `SURREAL_PASS` or
  `SURREAL_TOKEN`. *Ask: "does this help/usage/debug command echo its environment?"*
  - **Read flags from the docs, not from `--help`:** `lore_search(tier="surrealdb-docs", …)`, e.g.
    `cli/surrealdb-cli/commands/export.mdx`. Or run `--help` in a container started WITHOUT the secrets env.
  - **The safe export recipe** (#601; the one conformance used). Run the subcommand itself, and let the
    CLI's env fallback supply the credentials, so none appear on any command line, in `ps`, or in a log:
    ```bash
    podman exec lore-surreal /surreal export --endpoint http://127.0.0.1:18500 \
      --namespace lore --database lore - > <dump-file>
    ```
    (`-` writes the dump to stdout; redirect it to a file OUTSIDE the repo.) Never pass `--user`/`--pass`
    on the command line, and never `echo`/`env`/`printenv` inside the container.
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
`REPORT-c1f-contract-migration.md` §4 (the measured OVERWRITE matrix — ⚠ **this address does NOT
resolve**; it is tracked nowhere in this repo. The §1.4 claim it backs is re-measured on 3.2.1 at
`docs/plans/v2/receipts/2026-07-26-packet11i-build/REPORT-fixwave-11ia-1.md` §2.2, which IS tracked;
see the boxed note in §1.4) · memories
`surreal-31-docs-audit-adjustments`, `read-the-docs-then-verify-them`,
`surreal-error-classifier-latent-edges`, `surreal-stores-systemd-managed` · live probes on
spike-surreal 3.1.5 (throwaway DBs; production `:18500` never touched).

<a id="107"></a>*#107 — `lore_findings get 107`. Read it once. It is the whole reason this file has
a "read this first" block.*

<a id="144"></a>*#144 — the #124 mechanism correction (the engine does **not** silently lose committed
rows; `query()`'s statement[0]-only validation hid retryable conflicts). Carries an OPEN
reconciliation against the original `scratchpad/102-recovery/` harness.*

<a id="497"></a>*#497 — a `RETURN` inside `BEGIN … COMMIT` ends the transaction early and commits the
statements before it; the skipped ones report OK (§3, §6.2). Docs gap closed 2026-09-26.*

<a id="501"></a>*#501 — `compose` should refuse a top-level `RETURN` fragment statement (the envelope-integrity
guard's missing case; the #497 hazard's in-repo door). Open.*

<a id="146"></a>*#146 — `DEFINE SEQUENCE IF NOT EXISTS` inherits the silent-no-op migration hazard for
`BATCH`/`START`. Named re-open trigger: the day anyone changes either.*

<a id="601"></a>*#601 — `surreal <subcommand> --help` inside a store container prints `SURREAL_PASS` in clear;
an agent leaked the production root password into its transcript this way on 2026-11-08 (§9 OPS). Open:
rotation and transcript purge are operator decisions.*

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
the ONLY source.** · #111 answered (keep the substring; the trigger is not met) — *superseded
2026-09-29: trigger MET (the typed `details.kind`, §3); the substring is evidence only.*

**The method lesson, since it cost the most:** five live probes and a cold audit did not find
`ENFORCED`, because probing can only find what you already thought to test — and nobody thinks to
test a keyword they do not know exists. One doc page found it in minutes. **Read the docs first;
probe to confirm them and to find what they omit.**

Receipts: `REPORT-probe-pkt03-store.md` · `REPORT-docs-surreal-31-reconcile.md` ·
`REPORT-probe-enforced-clause.md` · `REPORT-audit-edge-preflight.md` (all preserved under
`docs/plans/v2/receipts/2026-07-19-packet03/`).

**Addition pass 2026-08-01** (D&D-graph scoping — six probes on spike-surreal 3.2.1, throwaway
namespaces, verbatim instruments preserved in
`docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md` §7; each claim checked
against `surrealdb-docs` / `surrealql-tests` tiers before landing here). §2 gained the
array-index element-path rule (vendor-corroborated) with its silent-`[]` equality trap · §4 gained
**"a traversal never uses a secondary index"** plus the `[[…]]`-vs-flat return-shape note · §6.6
gained items 13–14 · §7 gained the SDK string-id vs SurrealQL int-id literal row. **And the
docs-first check caught the scout over-claiming novelty:** its report calls the int-vs-string id
face *"not written down anywhere I can find"* — FALSE; `record-ids.mdx` documents it explicitly
(the backtick storage rule exists *because* `article:10` ≠ `` article:`10` ``). Only the SDK-mint
face and the `t:'4'` parse error are ours. The archived report carries a correction header. Same
lesson as 2026-07-19, running in both directions: probe to find what the docs omit, and read the
docs to find what your probe wrongly claims to have discovered.

**Addition pass 2026-09-26** (packet 64's S2 restore instrument, probe-64 — eleven `POST /import` legs on
spike-surreal 3.2.4, throwaway DBs reaped): §6.7 added — the import is NOT atomic, errors ride an HTTP
200, the reference example is broken, `surreal export` files are refused until their log lines are
stripped, and an absent target DB silently downgrades the schema. Docs-first check: the vendor's
`http-protocol.mdx` names the endpoint and headers correctly and its example is wrong; the
tutorial's `--data-binary` form is the working one.

**Addition pass 2026-09-26 (b)** (finding #497, contract-58-r2 → sidecar-64): §3 gained the `RETURN`-
inside-a-transaction bullet and §6.2 its silence row. Docs-first check: the vendor DOCUMENTS the break
(`return.mdx`) — this repo had never read that section; the probe added what the page omits (the
earlier statements commit; the skipped ones report OK; a later THROW is dead).

