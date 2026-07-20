# REPORT-docs-surreal-31-reconcile

brief-base v4 read

- **state:** done
- **deviations:**
  - Read the INSTALLED SDK source (`.venv/.../surrealdb/{errors.py,connections/async_ws.py}`) as a documentation source. Not a probe — no engine contacted, nothing run against a store. It is the only way to settle Q7/Q8 honestly, and it produced the report's second §6 candidate.
  - `surrealdb.com/docs/surrealdb/reference-guide/transactions` and `/docs/surrealdb/models/graph` do not exist (both resolve to marketing pages). Used `/docs/surrealql/transactions` instead.
- **decisions-needed:**
  1. **`ENFORCED` EXISTS and closes the #105 dangling-edge gap at the engine.** Our §4 sentence "an application-level existence check remains the only guard" is FALSE. Vendor-documented, present since ≥2.0.3. **UNPROBED by us** — operator's call whether packet 03 adopts it (recommend: probe first, then adopt as a backstop, keep the app check).
  2. **The vendor's Python-SDK doc is WRONG about `.query()`** — says it returns the LAST statement; SDK 2.0.0 returns the FIRST. New §6 entry, and it independently corroborates #144.
- **receipt pointers:** table §RECONCILIATION · §6 candidates §SECTION-6 CANDIDATES · design-changers §VENDOR-SAYS-MORE · §CITATION UPGRADES · §STILL GENUINELY UNDOCUMENTED · §UNASKED

Engine floor: **3.1.5**. SDK: **surrealdb 2.0.0** (`.venv/lib/python3.14/site-packages/surrealdb`, METADATA `Version: 2.0.0`). No probes run; no repo file edited.

---

## RECONCILIATION

| # | Question | Our claim (`docs/reference/surrealdb-31-capabilities.md`) | Verdict | Vendor |
|---|---|---|---|---|
| 1 | RELATE validates endpoints? | `:275` "`RELATE` does NOT validate that its ENDPOINTS exist — NEITHER `in` NOR `out`" | **VENDOR-CONFIRMS** | [relate](https://surrealdb.com/docs/surrealql/statements/relate): *"`RELATE` will create a relation **regardless of whether the records to relate to exist or not**. As such, it is advisable to create the records you want to relate to before using `RELATE`, or to at least ensure that they exist before making a query on the relation."* |
| 1b | Ghost visible in traversal | `:284–286` ghost lists as a first-class recipient | **VENDOR-CONTRADICTS** → §6 | Same page: *"If the records to relate to don't exist, a query on the relation will still work but will return an empty array."* Our probe: `[agent:a_ghost, agent:a_real]`. |
| 1c | Dangling edges / guard advice | (not recorded) | **VENDOR-SAYS-MORE** | Same page: *"Edge tables are deleted once there are no existing relationships left."* · *"a graph edge will also automatically be deleted if it is **no longer connected to a record at both `in` and `out`**."* |
| 2 | `TYPE RELATION IN/OUT` enforcement | `:293–296` "The **only** endpoint validation the engine offers … does **not** reject a non-existent record … an application-level existence check remains the only guard" | **VENDOR-CONTRADICTS** → §6 (our doc is the wrong one) | [define/table](https://surrealdb.com/docs/surrealql/statements/define/table) BNF: `TYPE [ ANY \| NORMAL \| RELATION [ IN \| FROM ] @table [ OUT \| TO ] @table [ ENFORCED ]]` — *"the `ENFORCED` clause can be used on a table of `TYPE RELATION` to disallow a `RELATE` statement from working unless it points to existing data."* Error shown: `The record 'city:one' does not exist` |
| 2b | Wrong-TABLE endpoint rejected | `:294–295` field-coercion rejection [PROBED] | **VENDOR-SILENT** on the mechanism | Docs promise only that the table *"can only store relational type content"*; the coercion-error shape is ours. Stays [PROBED]. |
| 3 | RELATE auto-creates an undeclared table `TYPE ANY` | `:386–389` | **VENDOR-SILENT** | Neither define/table nor relate addresses an undefined target table. Stays [PROBED]-only. |
| 4 | Endpoint delete cascades the edge | `:237` + `:305–309` | **VENDOR-CONFIRMS** | relate: *"a graph edge will also automatically be deleted if it is no longer connected to a record at both `in` and `out`."* |
| 4b | UNIQUE index entry cleaned; #7061 retired | `:302–309` "fixed in ≥3.1.0" [PROBED] | **VENDOR-CONFIRMS — and names our exact probe legs** | [Release 3.1](https://surrealdb.com/releases/3.1), §Indexes: *"Fixed cascade-delete index bugs that caused COUNT-index drift, ghost UNIQUE-index entries on relation tables, and phantom UNIQUE-index entries when `IN` / `OUT` records were deleted before the relation."* · Issue #7061 **CLOSED**, labels `3.x`, `topic:indexing`, title *"CASCADE DELETE on RELATION tables does not clean UNIQUE index entries, causing ghost index violations"* |
| 4c | #7310 UNIQUE × EVENT | `:314` "moot while those edges carry no events" | **VENDOR-SILENT on a fix** | Issue #7310 **CLOSED**, `topic:indexing`, *"UNIQUE index alters execution outcome of UPDATE within an EVENT on a relation"*; reported against **3.0.2 / 3.0.3 / 3.0.5**. No fix version stated. Caution stands. |
| 5 | `sequence::nextval("<name>")` spelling | `:352–353` [MEASURED] | **VENDOR-CONFIRMS** | [define/sequence](https://surrealdb.com/docs/surrealql/statements/define/sequence): `sequence::nextval('mySeq2')` |
| 5b | Sequence syntax + clauses | `:355–356` `[BATCH][START][TIMEOUT]` | **VENDOR-CONFIRMS**, and **SAYS MORE** | `DEFINE SEQUENCE [ OVERWRITE \| IF NOT EXISTS ] @name [ BATCH @batch ] [ START @start ] [ TIMEOUT @duration ]` — **both** clauses are documented as legal (our §1.1 row mentions only `IF NOT EXISTS`). *"Batch allocation: Nodes request ranges of sequence values at once, reducing network chatter."* |
| 5c | Gaps are real / aborted txn burns a number | `:359`, `:368–369` [MEASURED] | **VENDOR-CONFIRMS, explicitly** | *"Sequences are never rolled back, even in a failed transaction."* Worked example: `BEGIN … nextval → 0 … CANCEL` then `sequence::nextval("seq"); -- 2` |
| 5d | Re-DEFINE / changing `BATCH`/`START` (#146) | `:60` residual | **VENDOR-SILENT** | Page says nothing about redefining an existing sequence or migrating BATCH/START. #146 stays [PROBED]-only. |
| 6 | `UPDATE … WHERE` empty return is ambiguous | Probe 4c, four-way | **VENDOR-CONFIRMS the ambiguity; offers no cleaner primitive** | [update](https://surrealdb.com/docs/surrealql/statements/update): *"If the record does not exist, the statement will succeed but no records will be updated."* · *"UPDATE does not create records that do not exist. To update a record and create it if it does not exist, use the UPSERT statement."* `RETURN NONE\|BEFORE\|AFTER\|DIFF` exist but none discriminate a zero-match. |
| 7 | `.query()` validates statement[0] only | `:243–248` `[CODE, SDK 2.0.0]` | **VENDOR-CONTRADICTS** → §6 | [executing-queries](https://surrealdb.com/docs/sdk/python/concepts/executing-queries): *"When a query string contains multiple semicolon-separated statements, `.query()` returns only the result of the **last** statement."* SDK 2.0.0 source returns the **first**. |
| 7b | The error-swallowing itself | `:245–246` silent partial apply | **VENDOR-SILENT** | No page warns that a later statement's `ERR` does not raise. Undocumented trap — stays ours. |
| 7c | A supported all-statements call | (not recorded) | **VENDOR-SAYS-MORE** | *"If you need the results from every statement, use `.query_raw()` instead."* Returns per-statement `status` / `time` / `result`. |
| 8 | Concurrent first-write to an undeclared table | `:371–389` | **VENDOR-SILENT** | No page addresses auto-schema creation under concurrency. Stays [PROBED]. |
| 8b | Engine does NOT auto-retry; client retry mandatory | `:257–259` [PROBED] | **VENDOR-CONFIRMS by omission + an OPEN feature request** | Issue #5229 *"Feature: Transaction retries to recover from resource busy/key contention errors"* — **OPEN**, `topic:transactions`, no milestone. Server-side retry does not exist. Release 3.1: *"New `surrealdb.transaction.retries` / `surrealdb.transaction.conflicts` counters fire from the commit path when the storage engine returns a retryable error."* |
| 8c | Typed retryable error instead of the substring (#111) | `:258` "the only signal is the literal marker string" | **VENDOR-SAYS-MORE — but the answer is still NO** | SDK 2.0.0 ships a full `kind`/`details` hierarchy (`errors.py`). **`ErrorKind` has no retryable member** (`Validation, Configuration, Thrown, Query, Serialization, NotAllowed, NotFound, AlreadyExists, Connection, Internal`). Conflicts arrive as `QueryError`. **#111's trigger is NOT met — keep the substring.** |
| 9 | 3.1 notes bearing on the above | — | see §UNASKED | Four items our reference does not carry. |

---

## SECTION-6 CANDIDATES (`WHERE THE VENDOR DOCS ARE WRONG`)

### 6.4 The "dangling edges read as an empty array" claim

**[relate](https://surrealdb.com/docs/surrealql/statements/relate) states:**

> "If the records to relate to don't exist, a query on the relation will still work but will return an empty array."

**FALSE as a reader would apply it.** [PROBED 2026-07-19] A graph traversal returns the ghost as a **first-class member**, not an empty array:

```
SELECT ->to->agent AS recipients FROM message:m_real;
  [{'recipients': [agent:a_ghost, agent:a_real]}]      <-- ghost listed as a real recipient
SELECT count() FROM agent;  ->  1                      <-- no such node exists
```

The vendor's sentence is true only of the **dereferencing** forms (`FETCH`, or projecting a field), which yield `None` — not `[]` either. It is false of the *identity* form, which is the natural fan-out query.

**Why it matters more than a wording quibble — it is the same class as §6.1:** an engineer who read that sentence would conclude a dangling edge is **self-announcing** (an empty result is visible; a wrong result is not). It is not. It is silently indistinguishable in exactly the query a delivery-graph reader writes. That is load-bearing misinformation about a hazard we already carry as finding #105.

### 6.5 The Python SDK doc names the WRONG statement

**[executing-queries](https://surrealdb.com/docs/sdk/python/concepts/executing-queries) states:**

> "When a query string contains multiple semicolon-separated statements, `.query()` returns only the result of the **last** statement."

**FALSE on the SDK we run (2.0.0).** It returns the **FIRST**. Source, WS path — the transport this project uses:

```python
# .venv/lib/python3.14/site-packages/surrealdb/connections/async_ws.py:206-219
async def query(self, query, vars=None, session_id=None, txn_id=None) -> Value:
    response = await self.query_raw(query, vars, session_id=session_id, txn_id=txn_id)
    self.check_response_for_error(response, "query")
    self.check_response_for_result(response, "query")
    self._check_query_result(response["result"][0])      # <-- index 0
    return response["result"][0]["result"]               # <-- index 0
```

```python
# .venv/lib/python3.14/site-packages/surrealdb/connections/utils_mixin.py:21-24
def _check_query_result(stmt: dict[str, Any]) -> None:
    """Raise if a query statement result has ``status: "ERR"``."""
    if stmt.get("status") == "ERR":
        raise parse_query_error(stmt)
```

Identical at every `blocking_http.py` / `async_http.py` call site (`response["result"][0]`, ~20 occurrences).

**Why it matters:** the docs' version is the *reassuring* one. In `BEGIN; …; COMMIT;`, the LAST statement is the **COMMIT** — so an engineer trusting the doc would believe a failed transaction surfaces, because the COMMIT errors. The SDK reads index 0, which is the **`BEGIN`** — always `OK`. **The doc describes precisely the behaviour that would have prevented #144, and the SDK does the opposite.** This is an independent, source-level corroboration of §3 and of #144's mechanism correction, arrived at without a probe.

---

## VENDOR-SAYS-MORE

### ⭐ `ENFORCED` — **THIS WOULD CHANGE THE DESIGN.** The engine ships the guard we concluded it does not have.

Our `:293–296` says, in bold, that a typed relation table is *"the only endpoint validation the engine offers"* and that *"an application-level existence check remains the only guard against a ghost."* **The vendor documents a switch that does exactly this.**

[define/table](https://surrealdb.com/docs/surrealql/statements/define/table) — in the BNF, `ENFORCED` is a trailing clause of `TYPE RELATION`:

```
[ TYPE [ ANY | NORMAL | RELATION [ IN | FROM ] @table [ OUT | TO ] @table [ ENFORCED ]]]
```

> "If this behaviour is not desirable, the `ENFORCED` clause can be used on a table of `TYPE RELATION` to disallow a `RELATE` statement from working unless it points to existing data."

```surql
DEFINE TABLE road_to TYPE RELATION IN city OUT city ENFORCED;
RELATE city:one->road_to->city:three SET distance = 5.5, slope = 30.0;
-- The record 'city:one' does not exist
```

And [relate](https://surrealdb.com/docs/surrealql/statements/relate) routes you to it by name:

> "To override this behaviour and return an error if no records exist to relate, you can use a `DEFINE TABLE` statement that includes the **`ENFORCED` keyword**."

**Version availability — it is on our floor.** The docs carry no "available since" note, but GitHub issue **#5039** (*"Bug: `ENFORCED` relation not working when connected to another relation"*, **CLOSED**, `topic:links`) is reported against **2.0.3**, so `ENFORCED` predates our 3.1.5 floor by a full major version. **It is not a 3.2+ or experimental feature.**

**What I am NOT claiming.** We have **never probed `ENFORCED`**, and this repo's §6.1 is a standing proof that this vendor ships load-bearing false sentences about exactly this kind of DDL clause. Specifically unknown, and each one is a real fork in packet 03's design:

1. Does it validate **both** endpoints, or only `in`? (The doc's example fails on `in`; nothing says `out` is checked.)
2. Does it interact with `RELATE … OR UPDATE`?
3. What is the failure shape inside a multi-`RELATE` transaction — does one bad recipient abort the whole fan-out? (For packet 03 that is arguably the *desired* semantics, but it must be measured, not assumed.)
4. Is #5039's chained-relation defect fully fixed on 3.1.5?
5. Does adding `ENFORCED` to an existing relation table migrate at all? It is a `DEFINE TABLE` clause, and our §1.1 puts TABLE on `IF NOT EXISTS` — **which means it would be a silent no-op on any existing store.** This is #107's shape, waiting.

**Recommendation:** probe `ENFORCED` before packet 03 fixes its design, and adopt it as a **backstop, not a replacement**. The application-level recipient check still earns its place: it produces a typed, actionable error naming the bad recipient at the seam, where `ENFORCED` produces a transaction abort. But shipping a hand-rolled guard while the engine offers a declarative one — without having even measured the engine's — is precisely the packages-over-hand-rolling call the operator has ruled on. **Point 5 above is the one that could bite silently.**

### `query_raw()` — **would change the design only if we were not already correct.**
The vendor documents the supported all-statements call: *"If you need the results from every statement, use `.query_raw()` instead."* Per-statement `status`/`time`/`result`. Our `execute_transaction` already does per-statement checking, so this is a **citation**, not a change — but §3's "NEVER send multi-statement SurrealQL through `query()`" can now name the vendor's own sanctioned alternative instead of sounding like a house rule.

### `QueryError.is_not_executed` — **worth a probe; may simplify §3's root-cause selection.**
SDK 2.0.0 exposes `QueryDetailKind.NOT_EXECUTED` and a typed `QueryError.is_not_executed`. Our probe's cascade notices read *"The query was not executed due to a failed transaction"* — the literal of that kind. If those statements carry `details.kind == "NotExecuted"`, then §3's *"classify `failed_statements[0]`"* positional heuristic has a **typed** equivalent: filter out every `is_not_executed` statement and what remains is the real cause, regardless of position. Same answer, no reliance on execution order. **Unprobed — flagged, not recommended.**

### `RETURN BEFORE` / `RETURN DIFF` on UPDATE — **would NOT change the design.**
Documented, but none of `NONE|BEFORE|AFTER|DIFF|<projection>` distinguishes "WHERE matched nothing" from "no such record" — both are the empty set. **The vendor offers no cleaner primitive for Q6.** Probe 4c's four-way ambiguity must be resolved in application code exactly as planned; that decision is now vendor-backed rather than assumed.

---

## CITATION UPGRADES ([PROBED] → [VENDOR]+[PROBED])

| Line | Claim | Citation to add |
|---|---|---|
| `:275` | RELATE does not validate endpoints | relate: *"`RELATE` will create a relation regardless of whether the records to relate to exist or not."* — plus the vendor's own guard advice (*"advisable to … ensure that they exist"*), which makes our app-level check vendor-endorsed, not merely prudent |
| `:237`, `:305–309` | Endpoint delete cascades the edge | relate: *"a graph edge will also automatically be deleted if it is no longer connected to a record at both `in` and `out`."* |
| `:302–309` | #7061 retired, UNIQUE entry cleaned | Release 3.1 §Indexes, verbatim — it names *"ghost UNIQUE-index entries on relation tables"* **and** *"phantom UNIQUE-index entries when `IN`/`OUT` records were deleted before the relation"*, i.e. both of probe 2's legs (recreated endpoint **and** absent endpoint). Strongest upgrade in this report: the vendor confirms the fix landed **in 3.1**, our floor. |
| `:352–356` | `sequence::nextval` + syntax | define/sequence: `sequence::nextval('mySeq2')`; full BNF incl. `OVERWRITE \| IF NOT EXISTS` |
| `:359`, `:368–369` | Sequences are not gapless | define/sequence: *"Sequences are never rolled back, even in a failed transaction."* + the `0 → 2` cancelled-transaction example. **Upgrade this from [MEASURED] to [VENDOR]+[MEASURED]** — it is a deliberate documented guarantee, not an accident we happened to observe. |
| `:257–259` | Client-side retry is mandatory | Issue #5229 (**OPEN**) proves engine-side retry does not exist; Release 3.1's OTel-counter bullet confirms the commit path classifies retryable errors |
| `:243–248` | `query()` statement[0] | Add `query_raw()` as the vendor-named alternative, and the §6.5 contradiction |
| `:60` | SEQUENCE row | Vendor confirms `OVERWRITE` is legal syntax (our row mentions only `IF NOT EXISTS`); the *choice* between them stays ours |

---

## STILL GENUINELY UNDOCUMENTED — [PROBED]-only, we are the sole source

The vendor gives us nothing here. Every one must keep its probe tag.

1. **RELATE onto an undeclared table auto-creates it `TYPE ANY`** (`:386–389`) — and thereby silently discards the `IN`/`OUT` guard. Vendor silent on undefined target tables entirely.
2. **Concurrent first-write to an undeclared table storms with retryable conflicts** (`:371–389`, 22/192) — no page addresses auto-schema creation under concurrency.
3. **The retryable marker is the literal `"can be retried"`** — the string appears in no vendor doc. `_txn.py:409` and `_surreal_harness.py:99`. There is still **no typed alternative** (see 8c).
4. **Re-DEFINE SEQUENCE semantics** — bare `DEFINE` raises; no variant resets the counter; `BATCH`/`START` never migrate (#146). Vendor entirely silent.
5. **`TYPE RELATION IN/OUT` rejects a wrong-TABLE endpoint by field coercion** — the mechanism and its error text are ours.
6. **`RELATE $expr.field->…` is a parse error** (`:467`) — no syntax page mentions it.
7. **A bare `str` endpoint is rejected loudly** (`:468`) — undocumented.
8. **The four-way-ambiguous CAS return** (probe 4c) — vendor confirms the two-way ambiguity (Q6) but never enumerates conflict-never-ran or wrong-owner as additional collapses.
9. **Everything in §6.2's silences table** — unchanged; I found no vendor page addressing existing-row behaviour on a definition change, `ALTER FIELD` creation, `OVERWRITE` clause-dropping, `DEFINE TABLE OVERWRITE` on a populated table, analyzer re-tokenisation, or the `option<>` requirement.
10. **The SDK's later-statement error swallowing** — documented nowhere; the docs actively describe the opposite (§6.5).

---

## UNASKED — things I found anyway

1. **⚠ Our own §4 carries a false absolute, and it is load-bearing.** `:293` — *"The **only** endpoint validation the engine offers is a typed relation table"* — is contradicted by the vendor's `ENFORCED`. This is a **§6.3-class defect** ("a doc *we* wrote was also wrong"), and it is worse than the ALTER one it would join: that error made us avoid a trap, this one makes us **hand-roll a guard the engine ships**, in a file whose entire purpose is to stop that. Recommend it be recorded in §6.3 with the same candour, not quietly patched.
2. **`ENFORCED` on an existing table is plausibly a silent no-op (#107's shape).** §1.1 puts TABLE on `IF NOT EXISTS`; `ENFORCED` is a `DEFINE TABLE` clause. Adding it to a live relation table would therefore land on every fresh DB and **on no existing store** — invisible, exactly like #107, and worse because the *fresh* path would pass every test (§1.6's blind spot verbatim). If `ENFORCED` is adopted, its migration is a first-class question, not an afterthought.
3. **The SDK ships a structured error hierarchy our reference never mentions at all.** `ErrorKind` + per-kind subclasses with typed detail accessors (`NotFoundError.record_id`, `NotAllowedError.is_token_expired`, `ValidationError.is_parse_error`, `QueryError.is_timed_out`, …), a `cause` chain with `has_kind()` / `find_cause()`, and `SurrealDBMethodError = ServerError` as a deprecated alias. §3 discusses error classification purely in substring terms. Worth a short §3 subsection — several of our hand-rolled classifications may have typed equivalents. (Retryability specifically does **not** — see 8c.)
4. **Release 3.1 items bearing on our graph work, none in our reference:**
   - *"RELATE overwrites existing edge records without UPDATE permission"* (fixed) — relevant to `UNIQUE(in,out)` + `RELATE … OR UPDATE` semantics.
   - *"Edge PERMISSIONS FOR delete bypassed when a connected node is deleted"* (fixed) and *"Vertex-delete cascades now run edge deletes with the caller's permissions"* — **cascade deletes now run under the caller's permissions.** Our `:526` auth split has searcher=VIEWER; a cascade that previously succeeded implicitly may now be permission-checked. Untested by us.
   - *"Single-scan `->edge->vertex` graph traversals. Vertex-side adjacency keys now embed the target (table, id) after RELATE"* — plausibly *why* a ghost id surfaces in traversal (§6.4): the adjacency key carries the target id, so traversal never touches the node table. Speculative; flagged as a hypothesis, not a finding.
5. **#7310 is CLOSED but no fix version is stated**, and it was reported against 3.0.2/3.0.3/3.0.5 — i.e. entirely below our floor, so 3.1.5 *probably* carries the fix. `:314`'s "moot while those edges carry no events" is still the right posture; I could not upgrade it to settled.
6. **Vendor advice we should quote, not just cite.** relate tells you to *"at least ensure that they exist before making a query on the relation"* — the vendor **recommends the application-level check** our probe concluded was necessary. Worth landing in §4 verbatim: it turns our guard from a house invention into the documented practice, which matters for the next engineer tempted to remove it as ceremony.
7. **Method note.** The single highest-value item here (`ENFORCED`) took one doc page and cost nothing, and **five live probes plus a cold audit did not surface it** — because probing can only find what you think to test, and nobody thought to test a keyword they did not know existed. That is the docs-first law's actual argument, and this run is a clean receipt for it.
8. **No lore tools used** (§4 tool honesty): this was vendor-documentation research plus two reads of the installed SDK at known paths. No code-structure question arose, so no grep fallback and no friction to file. The one repo-code grep (`can be retried`) was a citation lookup for a literal string — a non-symbol textual seam, which is case (b) of the sanctioned grep exceptions.
