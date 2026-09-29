brief-base v18 read
brief project v7 read

# REPORT — blindreader-63c-i-a-3 (contract-blind diff read, 63c-i-a final fix build)

## SUMMARY
- **State:** done. **Graded:** patch `956e4136b403d061cf60603c53def3ef` (builder-63c-i-a-a28c) over base `bbf6a0c` · HEAD-at-report: `1dcb668` · DIFFERENT (HEAD moved `e4f52a7`→`1dcb668` during the read: docs-only commits `ac60acd`, `1dcb668`; `git diff --stat bbf6a0c 1dcb668 -- loremaster/loremaster` is EMPTY, so every production "before" I read is byte-identical at both SHAs).
- **Deviations:** (1) My first awk sweep for retired `_txn` names (step 1) printed single matching lines from test files before I wrote the inventory; I read no test body until §6. (2) I saw the commit SUBJECT of `ac60acd` (it mentions a "cascade kinds = {NotExecuted, Cancelled}" requirement) in `git log --oneline` AFTER I had written F-6 below. I did not open the amendment. (3) I ran three live probes against the TEST store `:18000` (throwaway namespace `blindreader_probe`, removed afterwards and verified absent). The instruments are pasted verbatim in §7.
- **Packages considered:** none. No mechanism was specified; I checked the SDK's own typed errors (`surrealdb/errors.py` 2.0.0, read in full) as the basis of the change I graded.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. I introduced no symbols.
- **Verdict:** 0 BLOCKER · 2 MAJOR · 7 MINOR · 7 NOTE. The core `_txn` typed-classification change holds up against a live 3.2.4 engine in every input class I could construct (§7). It also FIXES two real echo-misclassifications the old code had (F-A, F-B).
- **The two MAJORs are both served English that contradicts the code:**
  - **M-1:** the REQUIRED-FIRST-READ store reference still teaches "the only signal is the literal `can be retried`" and "no typed alternative". Both are measured false today.
  - **M-2:** `MigrateGovernedResult.table_defined` defaults to `True`, so every refusal and not-supported result CLAIMS the target table is defined without having checked.
- **Decisions needed:** M-1. `docs/reference/surrealdb-31-capabilities.md` is outside every writable set I know of. Who updates §3 / §6 item 3 / #111 in the same wave?
- **Pointers:** inventory §2 · input-fate §3 · findings §4 · uncovered §6 · probe instruments + raw output §7.

## 1. Capability check
- **Demanded vs available:** the brief demands nothing I cannot do. grep/rg are hook-blocked, so every textual sweep used `awk` over `git ls-files`, as the brief instructs.
- **lore:** I used it only for comms. My structure questions were bounded by the 6-file diff plus the installed SDK source, so I read the files directly. No graph question arose that lore would answer better. This was not a routing-around, so I filed no friction.
- **No pytest was run**, per the brief.

## 2. REMOVED-BEHAVIOUR INVENTORY (written before any test was read)
Each item is marked P = preserved, C = changed, or D = dropped.

### `store/_txn.py`
| # | Old behaviour (HEAD symbol) | Fate | New location / note |
|---|---|---|---|
| T1 | `_RETRYABLE_CONFLICT_MARKER="can be retried"` substring of `str(error)` / `str(raw_result)` decides retry on BOTH paths (`_is_retryable_conflict_text`) | **C** | `_is_retryable_conflict_kind`: `isinstance(ServerError) and details.kind == "TransactionConflict"`. An untyped (kindless or non-`ServerError`) conflict text is **no longer retried**. Verified live: 3.2.4 types every conflict on both paths (§7 P2). |
| T2 | Cascade = text contains `"was not executed due to"` or `"aborted due to a prior error"` (`_DOMAIN_CASCADE_MARKERS`) | **C** | `_is_domain_cascade_notice(failed)`: `details.kind == NotExecuted`. `Cancelled` (post-offender) is no longer cascade. It is still never selected before the offender, because it only follows the offender (§7 P1). |
| T3 | Root-cause selector skips an entry with **EMPTY text** (`if text and not …`) | **D** | An empty-`result` ERR entry that is not `NotExecuted` is now selectable as root cause. Unobserved on 3.2.4 (an empty THROW renders `"An error occurred: "`, §7 P1). |
| T4 | `_classify_engine_error`: retry marker checked first on text | **C** | Typed (`AlreadyExistsError` first, then the typed conflict). |
| T5 | Governed = `"governed_conflict:"` **anywhere** in the lowered text | **C** | Only `kind==Thrown` (or untyped) AND the text **starts with** `"an error occurred: governed_conflict:"`. This fixes the echo misclassification (F-A). |
| T6 | ASSERT (`must conform to`) / coercion (`coerce`) / recursion (`recursion depth`) for ANY error | **C** | ASSERT/coercion only for `Internal` or untyped. Recursion only for `Validation` or untyped. Verified live: ASSERT and coercion are `Internal`, recursion depth is RPC-level `Validation` (§7 P1/P2). |
| T7 | No unique-violation class: a record-id or UNIQUE-index collision was `unspecified rejection` → `TxnDomainRejectionError` | **C (new class)** | `TxnUniqueViolationError(TxnDomainRejectionError)`, label `unique violation — …`. The record case is typed (`AlreadyExistsError.record_id`). The index case is an `Internal` text prefix `database index \`` at position 0. |
| T8 | `run_query` inline ladder: transport → drop + `SurrealConnectionError("SurrealDB {noun} failed against …: {error}")`; conflict → signal `from error`; domain → `logger.error(label, extra={url,error_class,engine_error})` + `_domain_rejection_error(...)` | **P** | Moved verbatim into `_raise_attempt_failure`. I diffed message strings, extras and order by eye: identical. The seam's own logger and label are still passed through (F6 preserved). |
| T9 | `_txn_query_raw`: **EVERY** caught error (incl. RPC-level domain kinds) → `drop(connection)` + `SurrealConnectionError("SurrealDB transaction failed against …")` | **C** | Now `_raise_attempt_failure`. Only `KeyError` / `NotAllowed` / `Connection` / non-`ServerError` drop. RPC-level Validation (parse, recursion depth), Internal, Query and other kinds KEEP the connection and raise `TxnDomainRejectionError`, logged as the NEW event `store.transaction.rejected` on `_txn`'s logger. An RPC-level `TransactionConflict` now raises `RetryableConflictSignal`. |
| T10 | Old `_txn_query_raw` message embedded `{error}` (engine text) in the raised `SurrealConnectionError` for ALL RPC errors, including parse errors that echo the statement | **C** | Domain kinds no longer echo engine text in the raised message (ledger #31 now holds on this path too). Transport still embeds `{error}`, same as `run_query` always did. |
| T11 | `_FailedStatement(index, raw_result)` | **P + field** | `typed: ServerError | None = None`, parsed once via `parse_query_error` **only when the entry carries a truthy `kind`**. |
| T12 | `_log_rollback` logs `raw_result` per entry under `store.transaction.rolled_back` | **P** | Unchanged. The text is now evidence-only. |
| T13 | `_run_verified_transaction` classifies `root_cause.raw_result` (text) | **C** | Classifies `_typed_root_cause(root_cause)`: typed, else raw text. |
| T14 | `retry_on_conflict` comment: `_txn`'s `_attempt` raises the signal BARE (no cause) | **C (partly stale)** | The txn attempt can now ALSO raise a signal chained `from error` (RPC-level conflict, T9). See F-8. |

### `agents.py` — `AgentRegistry.register`
| # | Old | Fate | New |
|---|---|---|---|
| A1 | A CREATE collision (concurrent identical first register) propagated as `TxnDomainRejectionError` (`unspecified rejection`) out of `register` | **C** | Catches `TxnUniqueViolationError`. If the row now reads back, it RECURSES into `register`: `preflight` runs again, then the re-register path, with `capability=None`. If it does not read back, it re-raises the unique violation raw. |

### `keeps.py`
| # | Old | Fate | New |
|---|---|---|---|
| K1 | `get_or_create_keyed`: ANY non-transport, non-exhausted `SurrealStoreError` on the mint txn → re-read by key → return the winner if present, else re-raise (wrapped `KeepStoreError`) | **C (narrowed)** | Only `TxnUniqueViolationError` re-reads. Any other domain rejection goes straight to `KeepStoreError` with no re-read. |
| K2 | Pass-through `except (SurrealConnectionError, TxnContentionExhaustedError): raise` | **P (implicitly)** | Neither class is caught by the new `except`, so both still propagate. |
| K3 | `minted_by_this_call()` + `_MINTED_BY_THIS_CALL` flag set on the returned keep when THIS call's CREATE won | **D** | Deleted together with its only consumer (S2). No other production consumer (awk sweep over `git ls-files` production + scripts). |

### `server.py` — governed `lore_comms register`
| # | Old | Fate | New |
|---|---|---|---|
| S1 | Order: `preflight` → mint → SF-63-1 gate on the minted keep → `register` | **C** | Read-only gate on an EXISTING session keep (`get_by_key`) → `preflight` → mint → gate on the returned keep → `register`. |
| S2 | Created-only compensation: on `_AgentRegistryError` after the mint, delete the keep iff this call minted it. On delete failure: log `comms.register.compensation_failed` and append an `ALSO: … LEFT BEHIND … remedy lore-adm delete-keep` line to the refusal | **D (deliberate per new docstring)** | Gone: the log event, the served ALSO-line and the delete. The docstring states the rationale ("a keep minted before a concurrent conflicting register refuses is the session's legitimate keep"). |
| S3 | Foreign-denial sentence (`session {session!r} is kept by another principal … lore-adm add-household …`) | **P** | Byte-identical text, hoisted into `foreign_denial` and served by one local `_sf_63_1_gate`. |
| S4 | `resolve_visible_keeps` is the only visibility decision | **P** | Both gate evaluations route through it. |

### `principals.py` — `migrate_governed`
| # | Old | Fate | New |
|---|---|---|---|
| P1 | Invalid `--table` → `_not_supported(store_was_read=False)`, zero I/O | **P** | Adds `table_defined=None`. |
| P2 | `INFO FOR DB` non-dict / missing `tables` → treated as "no tables" (a memory-only store) | **C** | Raises a bare `SurrealStoreError("… nothing was migrated")`. |
| P3 | `_governed_select` non-list → `[]` (tolerant) | **C** | Raises a bare `SurrealStoreError`. `_scope_count` keeps its tolerance (non-list → 0). See F-12. |
| P4 | Agent/memory/message leg on an UNDEFINED target table ran the leg. The memory leg minted the project keep, then `_scope_count` hit `NotFound` (§7 P1: `SELECT` on an undefined table RAISES `NotFound` on 3.2.4) → uncaught `TxnDomainRejectionError`, with a keep possibly left minted | **C (improved)** | Early return `scanned=0, backfilled=0, already=0, table_defined=False` BEFORE any leg. The CLI prints "not defined … nothing to migrate" with exit 0. |
| P5 | Memory and agent `backfilled` = the pre-count `unmigrated` | **C** | `_rows_stamped(<UPDATE return>)`: measured, as message already was. `scanned` is still the pre-count sum, so `backfilled` may now differ from `scanned - already` under concurrency (honest). |
| P6 | Owner diagnosis: operator-owned row COUNT (`{operator_owned} of them are owned by the operator`) and other-owned row count (`{count-operator_owned} are owned by {len(others)} other principal(s)`) | **D (row counts per class)** | Replaced by the classification sentence. The mixed case no longer states how many ROWS each class owns. It states "{distinct_owner_principals} distinct owner(s)", which COUNTS THE OPERATOR while sitting after "other principal(s):". See F-9. |
| P7 | The verb-level refusal served only agent problems | **C** | Now also serves message problems (when `--table message`) plus a new trailer "(The store holds N agent row(s) with no scope in total.)". |
| P8 | Message leg: agent-first ORDER refusal returned ALONE (early) | **C** | ORDER sentence plus every message row problem in ONE refusal. With no row problems the ORDER sentence is served with its trailing "." stripped (byte-matches the old text). |
| P9 | Message backfill `WHERE scope IS NONE AND owner_principal IS NONE` | **C** | `+ AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE`. Rows failing the new predicate are silently left, and nothing counts or names them. See F-10. |
| P10 | `_operator_unresolved` measured and rendered in place | **C** | Inside the verb it returns an `_UnresolvedPurpose(str)` marker that the verb renders from `counts`. Outside the verb it renders through the SAME template (`_operator_unresolved_sentence`) with its own measurement. |
| P11 | `resolve_operator_principal` had no side effect | **C** | Writes `(total, admins)` into the per-call `ContextVar` record when one is installed. It is a no-op outside `migrate_governed`. |

### `governed.py`
| # | Old | Fate | New |
|---|---|---|---|
| G1 | `MigrateGovernedResult(table, scanned, backfilled, already_migrated, refused, reason)` | **C (additive)** | `+ preconditions: MigratePreconditionCounts | None = None`, `+ table_defined: bool | None = True`. See M-2. |
| G2 | — | **new** | `MigratePreconditionCounts` (pydantic, `extra="forbid"`, frozen) with an owner-triple consistency validator. |

## 3. INPUT-FATE TABLE
Each row answers the brief's three questions: connection kept or dropped (K/D), retried or not (R/–), and which class and log event is served.

Before the table, the live evidence it rests on. I ran these on the TEST store (§7) and did not infer them:
- **Record collision:** `AlreadyExists` + `details.Record.id` on both paths.
- **UNIQUE index:** `Internal`, `details:null`, text `Database index \`k\` already contains …`.
- **ASSERT and coercion:** `Internal`.
- **THROW:** `Thrown`, `An error occurred: <text>`.
- **Parse and recursion depth on the txn path:** RPC-level `Validation` (code −32000).
- **Pre-offender entries:** `Query/NotExecuted`.
- **Post-offender entries:** `Query/Cancelled`.
- **COMMIT abort:** `Query/NotExecuted`.
- **Conflict:** `Query/TransactionConflict` on both paths. On the txn path it sits on the COMMIT entry.
- **Undefined table:** `NotFound/Table`.
- **Table exists:** `AlreadyExists/Table` (record_id None).
- **Removed DB:** per-statement `NotFound/Database`.

### `_txn` — single-statement path (`run_query`)
| Input | Before | After | Silent change? |
|---|---|---|---|
| transport / `KeyError` / NotAllowed / Connection / non-`ServerError` SurrealError | D, –, `SurrealConnectionError` | same | no |
| retryable conflict (typed) | K, R | same | no |
| a VALUE echoing `can be retried` inside an ASSERT/coercion/unique text | K, **R** (~budget of retries, then `TxnContentionExhaustedError` — contention mis-served) | K, –, domain class | **fixed** (F-B) |
| parse error | K, –, `unspecified` | same | no |
| recursion depth (RPC `Validation`) | K, –, `query too complex` | same | no |
| governed THROW | K, –, `TxnGovernedConflictError` | same | no |
| coercion/ASSERT echoing `An error occurred: governed_conflict:` | K, –, **`TxnGovernedConflictError`** (substring hit) | K, –, `field coercion`/`assert violation` | **fixed** (F-A) |
| record-id collision | K, –, `unspecified` → `TxnDomainRejectionError` | K, –, `unique violation` → `TxnUniqueViolationError` | intended |
| UNIQUE-index collision | K, –, `unspecified` | K, –, `unique violation` | intended |
| table already exists (DDL) | `unspecified` | `unspecified` (typed, record_id None) | no |
| `NotFound` (undefined table / removed DB) | K, –, `unspecified` | same | no |
| kindless per-statement ERR | SDK `parse_query_error` resolves kind → `Internal` | same, but now only the Internal ladder applies (no recursion or governed label) | NOTE (F-14) |

### `_txn` — transactional path (`execute_transaction` → `_txn_query_raw` + per-statement)
| Input | Before | After | Silent change? |
|---|---|---|---|
| transport / KeyError / NotAllowed (anonymous reconnect) | D, –, `SurrealConnectionError` | same | no |
| RPC-level parse error / recursion depth (`Validation`) | **D**, –, `SurrealConnectionError` (engine text echoed in the message) | K, –, `TxnDomainRejectionError` (`unspecified` / `query too complex`), `store.transaction.rejected` | **changed**, intended per new docstring. Visible to callers: `wrap_store_rejection` now WRAPS it (e.g. `KeepStoreError`) instead of passing it through as transport. F-11. |
| RPC-level `TransactionConflict` (if the engine ever emits one) | D, –, `SurrealConnectionError` | K, **R** | changed. Exhaustion attribution gap, F-8. |
| per-statement conflict (COMMIT entry) | R (text) | R (typed) | no |
| per-statement domain, offender after NotExecuted cascade | root = offender (text) | root = offender (typed) | no |
| offender followed by `Cancelled` | Cancelled skipped by text marker | Cancelled not cascade, but never reached (the offender is first) | no, except in the degenerate case (F-6) |
| hostile value echoing `can be retried` in a UNIQUE/ASSERT text | **R** until exhaustion → `TxnContentionExhaustedError` | K, –, domain class | **fixed** (F-B; §7 P1 "txn unique echo") |
| governed THROW | `TxnGovernedConflictError` | same | no |
| error entry with EMPTY text | skipped as root cause | selectable | NOTE (T3) |
| kindless ERR entry | text ladder (retry, cascade, all labels) | `typed=None` → never a conflict, never cascade, full label ladder minus retry | NOTE (F-14): the fail direction is LOUD (a non-retried domain error), never silent success |
| per-statement `NotFound` (DB removed underneath a cached connection; §7 P3) | K, –, domain (per-statement, never reached the RPC catch) | same | no. I checked this because the T9 change could have removed a self-heal. It could not: this shape is per-statement on 3.2.4. |

### Agent register (`AgentRegistry.register` + `AppContext` register handler)
| Input | Before | After |
|---|---|---|
| concurrent identical first register (CREATE record collision) | loser: raw domain rejection, no row difference | loser: recursion → `preflight` → re-register (no capability). A differing `role`/`spawned_by` → `AgentIdentityConflictError` teaching. Intended. |
| unique violation but row does not read back | n/a | raw `TxnUniqueViolationError` escapes `register` (F-13) |
| governed principal, foreign session (keep exists) | preflight (reads agent row) → mint (returns existing) → DENIED | DENIED before any registry read (intended, "learns nothing about another principal's agents") |
| governed principal, invalid session/name | `preflight` refuses before any keep I/O | ONE keep read (`get_by_key("session:<invalid>")`, parameterised) happens first, then preflight refuses. If a keep with that key existed the foreign denial would echo `session!r` first. Only a previously-legal session can have a keep, so the exposure is nil (NOTE F-15). |
| concurrent registrants from two principals, no keep yet | the mint's CAS decides the keeper; the loser is denied by the post-mint gate | same, with the gate re-run on the RETURNED keep |
| register refused after the mint (a concurrent conflicting register — same principal, or a tokenless one) | the keep was deleted iff this call created it; failure served an ALSO-line | the keep stays (deliberate). The keeper principal is the caller, so no other principal's access is affected. A tokenless winner leaves a keep kept by a principal with no agent in the session (NOTE F-16). |
| single- vs multi-principal store | n/a to register | n/a |

### `migrate_governed` per `--table`
| Input | Before | After |
|---|---|---|
| invalid table | not-supported refusal, zero I/O | same (+ `table_defined=None`) |
| store with no agent table, `--table memory` | memory leg (operator resolve, keep mint, backfill) | same (agent counts `None`) |
| `--table agent` / `message` / `memory` whose table is undefined | leg ran → `NotFound` raised uncaught (CLI traceback). The memory leg may have minted the project keep first. | clean `table_defined=False` exit 0, no keep minted (**improved**) |
| `--table brief` undefined | not-supported refusal | same, but `table_defined=True` (default) — M-2 |
| single-principal store with owned-unscoped rows | operator = the one principal → "N of them are owned by the operator" | classification `operator` → "They are owned by the operator" (per-class row count dropped, F-9) |
| multi-principal, ≥2 admins | unresolved → "(n principals, m admins)" + unclassified | same text, counts now read from the ONE resolution record |
| mixed owners | per-class row counts | "AND by other principal(s): {distinct incl. operator} distinct owner(s)" — F-9 |
| `INFO FOR DB` shape broken | silently "no tables" | bare `SurrealStoreError`, which the CLI does not catch → traceback (F-12) |
| message rows whose sender lacks owner/scope at UPDATE time | stamped a half-pair (`owner_principal` NONE, scope set) | silently left un-migrated, not counted, not named (F-10) |
| hostile stored ids (owner / row ids with newlines) | `sanitise_line` on named owners, `_id_sample` for ids | same seams. The owner ids still pass through `sanitise_line`. |

### Keep mint (`KeepStore.get_or_create_keyed`)
| Input | Before | After |
|---|---|---|
| concurrent winner on UNIQUE `keep.key` | any domain rejection → re-read → winner | typed `TxnUniqueViolationError` (live-verified `Internal` + prefix, root = the CREATE entry) → re-read → winner. The same outcome, by a narrower door. |
| collision surfacing as a conflict first | retried; the next attempt collides → winner | same |
| unruled `type` ASSERT / ghost keeper while a winner exists | re-read → **winner returned** (the ASSERT was masked) | `KeepStoreError` (no re-read) |
| transport / exhausted | pass-through | pass-through |

## 4. FINDINGS

### MAJOR
**M-1 — `docs/reference/surrealdb-31-capabilities.md` §3 / §6 item 3 now CONTRADICT the code (served English, the required-first-read).** Three passages are affected:
- §3 says: *"The only signal is the literal marker string **`"can be retried"`**"* and *"#111 ANSWERED — keep the substring … **no typed alternative**"*.
- §6 item 3 says: *"there is still **no typed alternative** (§3, #111)"*.
- §3 also describes the cascade selector as "marker-seeking".

The patched `_txn` decides retry by `details.kind == "TransactionConflict"` and cascade by `NotExecuted`. I measured the typed kind live on 3.2.4, on BOTH paths (§7 P2), so the doc's "no typed alternative" is false today.

Per `CLAUDE.md`, this file is read FIRST by every store/DDL agent and is cited as the authority. An agent reading it will re-introduce text matching, or "correct" the typed code back. This is exactly the §8 stale-prose class that the doc itself names. The patch did not touch the file.
- *Class:* a mechanism change without an update to the authoritative prose that teaches the mechanism.
- *Siblings tried:* the `_txn` docstrings (F-4, F-5), the `TxnContentionExhaustedError` docstring, and the `retry_on_conflict` comment.
- *Siblings not tried:* `docs/design/*` (withheld) and `DESIGN-LAW.md`.
- **Decision needed:** who edits the reference in this wave?

**M-2 — `governed.MigrateGovernedResult.table_defined` defaults to `True`: a served receipt field over-claims.** The new docstring defines `True` as "when it is [defined]". But every construction site that omits the argument claims definedness:
- `_refused` (verb-level refusals, leg refusals, unresolved-operator refusals — the target's definedness was never consulted, and may be FALSE);
- `_not_supported(store_was_read=True)` for `brief`;
- the three legs' success returns (true there only because the early-return guard ran first).

A default of `True` is a claim nobody measured. `None` ("not measured") is the honest default, and `False`/`True` should be set only where `defined_tables` was consulted. Today the only consumer is the CLI, which acts only on `is False`, so there is no served lie yet. But the field is public on the typed result.
- *Class:* a receipt field whose default asserts a measurement. This is the same shape the file's own docstring forbids for `scanned` ("a `0` there would be a served count describing no set").
- *Siblings tried:* `preconditions` (defaults to `None`, honest) and `backfilled` (an int by design).

### MINOR
- **F-4 `_txn.execute_transaction` docstring (unchanged by the patch):** still says the root cause is *"the FIRST failed entry whose text is non-empty and carries no cascade marker"* and calls the COMMIT abort *"marker-less"*. After the patch it is the first non-`NotExecuted` typed entry, and empty text is no longer skipped (T3).
- **F-5 `_txn.TxnContentionExhaustedError` docstring:** still says retryable is *"the engine's own `"can be retried"` marker"*. The same class of drift also sits in the comment above `_ASSERT_VIOLATION_MARKER` ("The substrings … that `_classify_engine_error` keys off of"), which is now only the Internal/untyped leg.
- **F-6 `_txn._domain_root_cause`, degenerate branch:** `Cancelled` is no longer cascade. For a rollback with NO substantive entry (all `NotExecuted` plus `Cancelled`, or a timed-out/killed txn), the selector now returns the first `Cancelled` entry instead of degrading to the LAST entry. The label is `unspecified` either way, so the only difference is which entry `_log_rollback` names as root. (I saw afterwards that `ac60acd`'s commit subject mentions a cascade-kinds `{NotExecuted, Cancelled}` requirement. This is the same observation, derived independently.)
- **F-8 `_txn._run_verified_transaction` exhaustion attribution:** an RPC-level `TransactionConflict` (newly retried via T9) does not update `last_conflict`. On exhaustion, `_log_rollback(*last_conflict)` therefore logs a STALE earlier attempt's per-statement conflict, or nothing. `retry_on_conflict` is called with no `label`, so the chained `engine_error` is dropped too. The new `retry_on_conflict` comment says `_txn_query_raw` chains `from error` "so that raise has the same cause in scope". True, but it goes unlogged on this caller.
  - Reachability: 3.2.4 puts conflicts on the per-statement COMMIT entry (§7 P2), so this is latent.
- **F-9 `principals._owned_unscoped_part`, mixed branch:** serves *"AND by other principal(s): {counts.distinct_owner_principals} distinct owner(s) (first {len(named)} named: …)"*. `distinct_owner_principals = len(owners)` INCLUDES the operator, so an operator plus one other reads "other principal(s): 2 distinct owner(s) (first 1 named …)". Also dropped: the per-class ROW counts the old sentence served (P6). The number is derived, not restated, but its label names a different set (Leg-1 scope diff).
- **F-10 `principals._migrate_message_owner` backfill predicate:** rows excluded by the new `sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE` clause are left un-migrated with `refused=False`, and nothing names them. Once the verb-level and ORDER guards pass, the reachable population is a sender whose owner/scope changed between the precondition read and the UPDATE (e.g. a tokenless agent registering mid-migration), or a non-agent record sender. `backfilled` is honest (measured), but `scanned - already - backfilled` rows are silent leftovers. A re-run stamps 0 of them forever. The docstring still describes the UPDATE as `WHERE scope IS NONE AND owner_principal IS NONE` (stale).
- **F-12 `principals._agent_migration_preconditions` / `_governed_select` new raises:** they are bare `SurrealStoreError`, and `_dispatch_migrate_governed` catches only `(PrincipalStoreError, KeepStoreError, SurrealConnectionError, ValueError)`. The carefully-worded "nothing was migrated" message therefore surfaces as a Python traceback, not "stderr line + exit 1" as that function's docstring promises. The same is pre-existing for engine rejections in the precondition reads. Also, `_scope_count` keeps the opposite, tolerant policy for the same "non-list answer" shape (two policies for one question).
- **F-13 `agents.AgentRegistry.register`:** the unique-violation branch re-raises the raw `TxnUniqueViolationError` when the row does not read back, and the recursion has no depth bound. The first is reachable if the agent table carries any UNIQUE index besides the record id, or on a concurrent delete between the CREATE and the read. The second is bounded only by a create/delete race. The raise escapes as a store error, not an `AgentRegistryError`.

### NOTE
- **F-A (fix, confirmed):** before the patch, a coercion/ASSERT text echoing a caller value that contained `governed_conflict:` was classified `TxnGovernedConflictError` (a substring match). The anchored `Thrown`-kind prefix closes it. Live text for the echo: §7 P1 "coercion".
- **F-B (fix, confirmed):** before the patch, a UNIQUE/ASSERT text echoing `can be retried` was RETRIED to exhaustion and served as contention. It is now a domain class (§7 P1 "txn unique echo").
- **F-11 `_txn._txn_query_raw` fate change (T9):** it is visible to every `execute_transaction` caller. An RPC-level parse error or recursion depth used to be pass-through transport, so `wrap_store_rejection` re-raised it, and any `SurrealConnectionError`-driven reconnect/retry loop above reconnected and retried it. It is now a domain error that gets wrapped. I judge this correct and intended, but it is a behaviour change callers can observe. I found no production caller that string-matches the old message.
- **F-14 kindless ERR entries:** these are handled differently on the two paths. The SDK's `parse_query_error` resolves a missing kind to `Internal` on the single path; `_failed_statements` leaves `typed=None` on the txn path, which gets the full untyped label ladder. None were observed on 3.2.4.
  - Named re-open trigger: the stores' quadlets pin the FLOATING `v3.2` tag (#336). An engine that stops typing conflicts would turn every conflict into a loud, non-retried domain rejection. That is loud, not silent.
  - `"TransactionConflict"` is a bare string literal (the SDK ships no constant). A pin on the live shape is the guard; see §6.
- **F-15 register ordering:** a keep read now precedes identity validation (details in §3).
- **F-16 compensation dropped (S2):** a keep minted by a registrant whose register is then refused by a concurrent TOKENLESS winner stays kept by a principal with no agent in that session. I judge this acceptable under the stated rationale, but the lost ALSO-line and the `comms.register.compensation_failed` event had documented operator value (a re-open trigger that is now retired). Adjudication class: dropped-deliberately (new docstring).
- **F-17 `keeps.get_or_create_keyed` narrowed catch (K1):** an ASSERT or ghost-keeper rejection is no longer masked by a concurrent winner. This is an improvement, and it removes a door where a genuine rejection was answered with someone else's keep.

## 5. SERVED ENGLISH (new strings)
- `_ERROR_CLASS_UNIQUE_VIOLATION` = "unique violation — the record id or a unique index value is already taken; re-read the row". This matches both typed doors (record id via `AlreadyExistsError.record_id`, index via the prefix). A table/NS/DB `AlreadyExists` correctly falls to `unspecified`. ✓
- `_TXN_REJECTION_LABEL` = `store.transaction.rejected`. It is logged with `engine_error=str(error)` (full text, server-side only), and the raised message carries the label plus `_SERVER_LOG_HINT`. ✓ This is a new event with no existing consumers; it is distinct from `store.transaction.rolled_back`, as its comment says. ✓
- `foreign_denial`: byte-identical to HEAD's sentence. ✓
- `_operator_unresolved_sentence`: byte-identical template to HEAD's `_operator_unresolved`, and its counts are DERIVED from the resolution record. ✓ The `_UnresolvedPurpose` marker survives every leg's `_refused(TABLE, await _operator_unresolved(...))`, because no leg concatenates it. I checked the three call sites. The verb-level site calls the sentence function directly.
- The verb-level trailer "(The store holds {unscoped_agents} agent row(s) with no scope in total.)" is derived. It is not `None` whenever parts exist, because parts require the agent read. ✓
- CLI "the `{table}` table is not defined in this store — nothing to migrate" is true (the early return precedes every leg write). ✓
- `INFO FOR DB answered a {type} without a \`tables\` map — … nothing was migrated` is true: the precondition read precedes every write. But see F-12 for how it reaches the operator.
- The comments' "measured 3.2.4 on both paths" claims about `TransactionConflict`, `NotExecuted`, `Cancelled`, the THROW wrapping, the UNIQUE prefix and the record-typed `AlreadyExists` were all **reproduced** by my probe (§7). No over-claim found in the new `_txn` comments except the stale survivors F-4/F-5 and M-1 outside the file.

## 6. UNCOVERED ITEMS (test skim, done AFTER §2–§5; by-name `awk` over the working-tree `loremaster/tests/*.py`, 2026-09-29 ~21:40Z)
The skim was bounded. "Uncovered" means I found no test referencing the symbol, event or case by name. A generic test may still exercise it, so each row is a LEAD, not proof.

| Item | Evidence of coverage | Verdict |
|---|---|---|
| T9: txn-path RPC-level DOMAIN error keeps the connection, raises `TxnDomainRejectionError`, logs `store.transaction.rejected` | 0 hits for `_TXN_REJECTION_LABEL`, `transaction.rejected`, `_raise_attempt_failure`. The `_txn_query_raw` pins found (`test_surreal_store.py::TestTxnSdkKeyErrorClassification`) cover only the KeyError→drop leg. `test_fixwave_a28c` has no test whose name mentions the ladder, RPC or parse. | **UNCOVERED (likely)**. It is the largest fate change in the diff (§3), and its new log event is unpinned. |
| F-8: RPC-level conflict on the txn path, exhaustion attribution | no hits | UNCOVERED (latent path) |
| F-6: all-cascade + `Cancelled` degenerate root cause | `test_am36_1_1_KNOWN_BOUND_every_cascade_notice_is_typed_NotExecuted` pins NotExecuted only. No `Cancelled`/degenerate test in `a28c` or `retry_seam`. | UNCOVERED |
| T3: empty-text ERR entry selectable as root cause | no hits | UNCOVERED |
| M-2: `table_defined` on REFUSALS / `brief` not-supported | pinned: `False` for an undefined target (`test_am34_4_…False_after_ONE_probe`), `None` for an invalid table (`test_am36_FK4_…`), `True` when defined on a proceeding leg (`test_fixwave_a28…:2098`). Nothing pins the value on a refusal. | UNCOVERED, which is why the default-True over-claim is invisible |
| F-9: mixed-owner sentence's "{distinct incl. operator} distinct owner(s)" after "other principal(s):" | `_OWNER_SENTENCE_STEMS = ("owned by", "classif")`: stems only, no count/label agreement | UNCOVERED |
| F-10: unsound-sender messages left unnamed | `TestTheMessageBackfillGuardsTheSender63cIAa28::test_A5_…` pins that they are NOT stamped and `backfilled == 1`. It does not require the leftover to be named. | behaviour pinned. Silence is by design, so this is not a gap in the tests but a question for the operator (§4 F-10). |
| F-12: new `SurrealStoreError` raises reach the CLI as a traceback | 0 hits for "tables map" / "not a list of rows" | UNCOVERED |
| F-13: `register` unique-violation with no read-back; recursion bound | concurrent-register pins exist for the handler (`TxnUniqueViolationError` appears in `a28b`/`a28c`). I found no test for the row-absent re-raise. | UNCOVERED (row-absent leg) |
| M-1: store reference currency | no instrument checks `docs/reference` against `_txn`'s decision mechanism | UNCOVERED, and structurally so |
| F-A / F-B echo fixes | `test_KB_a_hostile_echoed_value_never_moves_the_class`, `test_am36_1_2_an_echoed_phrase_moves_nothing`, `test_am36_1_2_4_KNOWN_BOUND_an_echo_can_trade_the_assert_and_coercion_labels` | covered |
| K1 / A1 unique-violation doors | `test_am35_2_1_…execute_transaction`, `test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg`, plus `test_am35_2_5_KNOWN_BOUND_a_unique_index_collision_is_untyped_on_the_transactional_path` | covered |
| Classifier sole-text-reader property | `test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier` and its `SEES` control | covered |

**One fixture drift noticed (NOTE):** `test_fixwave_a28c_63c_i_a.py` (module constant near line 773) spells the recursion text `"Parse error: Exceeded expression recursion depth limit"`. Live 3.2.4 says `"… Exceeded query recursion depth limit"` (§7 P2). Both contain the `recursion depth` marker, so no verdict changes, but the fixture is not a capture.

## 7. PROBE INSTRUMENTS (verbatim) + RAW OUTPUT
All three probes ran against the TEST store `ws://127.0.0.1:18000` (`surrealdb-3.2.4+20260803.93ab219`, as printed by P2) on 2026-09-29 ~21:25–21:37Z, with SDK `surrealdb` 2.0.0 from the repo venv (`uv run python <file>`). Each used namespace `blindreader_probe` with a random database, removed in `finally`. After the runs I removed the namespace itself and verified it absent (`INFO FOR ROOT` → `after: []`). `:18500` was never touched.

### P1 — `probe_shapes.py`
```python
"""blindreader-63c-i-a-3 engine-shape probe (TEST store :18000 only; throwaway ns/db, removed after).

For each input class, print the per-statement entry dicts of query_raw (transactional path) and the
exception query() raises (single-statement path): kind, details, text.
"""

import asyncio
import json
import uuid

from surrealdb import AsyncSurreal

URL = "ws://127.0.0.1:18000/rpc"
NS = "blindreader_probe"
DB = f"p_{uuid.uuid4().hex[:12]}"


def show_entry(entry):
    return json.dumps({k: entry.get(k) for k in ("status", "kind", "details", "result")}, default=str)[:400]


async def both(db, label, stmt, params=None):
    print(f"\n=== {label}: {stmt[:120]!r}")
    raw = await db.query_raw(stmt, params or {})
    if raw.get("error") is not None:
        print("  RAW rpc-error:", json.dumps(raw["error"], default=str)[:400])
    for index, entry in enumerate(raw.get("result") or []):
        if isinstance(entry, dict) and entry.get("status") == "ERR":
            print(f"  RAW[{index}]:", show_entry(entry))
        else:
            print(f"  RAW[{index}]: OK {str(entry.get('result'))[:80] if isinstance(entry, dict) else entry}")


async def single(db, label, stmt, params=None):
    print(f"\n--- single {label}: {stmt[:120]!r}")
    try:
        out = await db.query(stmt, params or {})
        print("  OK:", str(out)[:200])
    except Exception as error:  # noqa: BLE001
        print(
            "  RAISED:", type(error).__name__, "kind=", getattr(error, "kind", None),
            "details=", getattr(error, "details", None), "text=", str(error)[:200],
            "record_id=", getattr(error, "record_id", "n/a"),
        )


async def main():
    db = AsyncSurreal(URL)
    await db.connect()
    await db.signin({"username": "root", "password": "spikeroot"})
    await db.query(f"DEFINE NAMESPACE IF NOT EXISTS {NS}")
    await db.use(NS, DB)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {DB}")
    await db.use(NS, DB)
    try:
        await single(db, "info-empty", "INFO FOR DB")
        await single(db, "select-undefined-table", "SELECT * FROM nosuch")
        await single(db, "select-count-undefined", "SELECT count() FROM nosuch WHERE scope IS NONE GROUP ALL")
        await db.query("DEFINE TABLE t SCHEMALESS; DEFINE FIELD key ON t TYPE option<string>; "
                       "DEFINE INDEX k ON t FIELDS key UNIQUE; "
                       "DEFINE TABLE t2 SCHEMAFULL; DEFINE FIELD n ON t2 TYPE int ASSERT $value > 0;")
        await db.query("CREATE t:x SET key = 'v'")
        await single(db, "record-collision", "CREATE t:x")
        await single(db, "record-collision-typerecord", "CREATE type::record('t', $id) CONTENT {}", {"id": "x"})
        await single(db, "unique-index", "CREATE t:y SET key = 'v'")
        await single(db, "unique-index-hostile-echo", "CREATE t:z SET key = $k; CREATE t:w SET key = $k",
                     {"k": "Transaction conflict: Resource busy. This transaction can be retried"})
        await single(db, "assert", "CREATE t2 SET n = -1")
        await single(db, "coercion", "CREATE t2 SET n = $v", {"v": "An error occurred: governed_conflict:t:x"})
        await single(db, "throw-governed", "THROW 'governed_conflict:t:x'")
        await single(db, "throw-other", "THROW 'something else'")
        await single(db, "parse", "SELEC * FROM t")
        await single(db, "table-exists", "DEFINE TABLE t")
        await single(db, "update-returns", "UPDATE t SET touched = true WHERE key = 'v'")
        await both(db, "txn record-collision mid",
                   "BEGIN; CREATE t:a1; CREATE t:x; CREATE t:a2; COMMIT;")
        await both(db, "txn unique-index", "BEGIN; CREATE t:b1; CREATE t:b2 SET key = 'v'; COMMIT;")
        await both(db, "txn unique echo", "BEGIN; CREATE t:c2 SET key = $k; CREATE t:c3 SET key = $k; COMMIT;",
                   {"k": "x can be retried"})
        await both(db, "txn assert", "BEGIN; CREATE t:d1; CREATE t2 SET n = -1; CREATE t:d2; COMMIT;")
        await both(db, "txn coercion", "BEGIN; CREATE t2 SET n = 'abc'; COMMIT;")
        await both(db, "txn throw governed", "BEGIN; CREATE t:e1; THROW 'governed_conflict:t:e1'; COMMIT;")
        await both(db, "txn parse", "BEGIN; SELEC * FROM t; COMMIT;")
        await both(db, "txn empty-text throw", "BEGIN; CREATE t:f1; THROW ''; COMMIT;")
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {DB}")
        await db.close()
        print(f"\n(removed {NS}/{DB})")


asyncio.run(main())
```

### P2 — `probe_conflict.py`
```python
"""blindreader-63c-i-a-3: provoke a REAL write-write conflict + a recursion-depth error on the TEST store
(:18000), print the engine's kind/details on both paths. Throwaway ns/db, removed after."""

import asyncio
import json
import uuid

from surrealdb import AsyncSurreal

URL = "ws://127.0.0.1:18000/rpc"
NS = "blindreader_probe"
DB = f"c_{uuid.uuid4().hex[:12]}"
N = 12


async def conn():
    db = AsyncSurreal(URL)
    await db.connect()
    await db.signin({"username": "root", "password": "spikeroot"})
    await db.use(NS, DB)
    return db


async def txn_racer(db):
    raw = await db.query_raw("BEGIN; UPDATE t:x SET n += 1; SLEEP 50ms; COMMIT;", {})
    if raw.get("error") is not None:
        return ("rpc", json.dumps(raw["error"], default=str)[:300])
    errs = [
        {k: e.get(k) for k in ("kind", "details", "result")}
        for e in raw.get("result") or []
        if isinstance(e, dict) and e.get("status") == "ERR"
    ]
    return ("stmt", json.dumps(errs, default=str)[:600]) if errs else ("ok", "")


async def single_racer(db):
    try:
        await db.query("UPDATE t:x SET n += 1", {})
        return ("ok", "")
    except Exception as error:  # noqa: BLE001
        return (type(error).__name__, f"kind={getattr(error, 'kind', None)} details={getattr(error, 'details', None)} text={str(error)[:160]}")


async def main():
    admin = AsyncSurreal(URL)
    await admin.connect()
    await admin.signin({"username": "root", "password": "spikeroot"})
    await admin.query(f"DEFINE NAMESPACE IF NOT EXISTS {NS}")
    await admin.use(NS, DB)
    await admin.query(f"DEFINE DATABASE IF NOT EXISTS {DB}")
    await admin.use(NS, DB)
    print("version:", await admin.version())
    try:
        await admin.query("CREATE t:x SET n = 0")
        racers = [await conn() for _ in range(N)]
        for round_number in range(3):
            outcomes = await asyncio.gather(*(txn_racer(db) for db in racers))
            print(f"txn round {round_number}:", sorted({o[0] for o in outcomes}))
            for outcome in {o for o in outcomes if o[0] != "ok"}:
                print("   ", outcome)
        for round_number in range(3):
            outcomes = await asyncio.gather(*(single_racer(db) for db in racers for _ in range(3)))
            print(f"single round {round_number}:", sorted({o[0] for o in outcomes}))
            for outcome in {o for o in outcomes if o[0] != "ok"}:
                print("   ", outcome)
        for db in racers:
            await db.close()
        deep = "RETURN " + "(" * 3000 + "1" + ")" * 3000
        for label, stmt in (("deep-parse", deep), ("deep-txn", "BEGIN; " + deep + "; COMMIT;")):
            raw = await admin.query_raw(stmt, {})
            print(label, "rpc-error:", json.dumps(raw.get("error"), default=str)[:300])
            for e in raw.get("result") or []:
                if isinstance(e, dict) and e.get("status") == "ERR":
                    print("   ", json.dumps({k: e.get(k) for k in ("kind", "details", "result")}, default=str)[:300])
        nested = "{" + "a:" * 0 + "}"
        _ = nested
    finally:
        await admin.query(f"REMOVE DATABASE IF EXISTS {DB}")
        await admin.close()
        print(f"(removed {NS}/{DB})")


asyncio.run(main())
```

### P3 — `probe_removed_db.py`
```python
"""blindreader-63c-i-a-3: what does the engine answer on a connection whose DB was REMOVED underneath it?
TEST store :18000 only; throwaway ns/db."""
import asyncio, json, uuid
from surrealdb import AsyncSurreal
URL, NS, DB = "ws://127.0.0.1:18000/rpc", "blindreader_probe", f"r_{uuid.uuid4().hex[:12]}"
async def conn():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"}); return db
async def main():
    admin = await conn(); await admin.query(f"DEFINE NAMESPACE IF NOT EXISTS {NS}"); await admin.use(NS, DB)
    await admin.query(f"DEFINE DATABASE IF NOT EXISTS {DB}"); await admin.query("CREATE t:x SET n = 1")
    victim = await conn(); await victim.use(NS, DB)
    await admin.query(f"REMOVE DATABASE {DB}")
    raw = await victim.query_raw("BEGIN; CREATE t:y SET n = 2; COMMIT;", {})
    print("txn rpc-error:", json.dumps(raw.get("error"), default=str)[:300])
    for e in raw.get("result") or []:
        print("  entry:", json.dumps({k: e.get(k) for k in ("status", "kind", "details", "result")}, default=str)[:300])
    try:
        print("single OK:", await victim.query("SELECT * FROM t", {}))
    except Exception as error:
        print("single RAISED:", type(error).__name__, getattr(error, "kind", None), getattr(error, "details", None), str(error)[:200])
    await admin.use(NS, "x"); await admin.query(f"REMOVE DATABASE IF EXISTS {DB}")
    print("post-state INFO FOR NS dbs:", list((await admin.query("INFO FOR NS")).get("databases", {}).keys())[:5])
    await victim.close(); await admin.close()
asyncio.run(main())
```

### Raw output (verbatim excerpts, the lines every §3 claim cites)
P1 (`probe_shapes.py`):
```
--- single info-empty: 'INFO FOR DB'
  OK: {'accesses': {}, 'analyzers': {}, 'apis': {}, 'buckets': {}, 'configs': {}, 'functions': {}, 'models': {}, 'modules': {}, 'params': {}, 'sequences': {}, 'tables': {}, 'users': {}}
--- single select-undefined-table: 'SELECT * FROM nosuch'
  RAISED: NotFoundError kind= NotFound details= {'details': {'name': 'nosuch'}, 'kind': 'Table'} text= The table 'nosuch' does not exist record_id= None
--- single select-count-undefined: 'SELECT count() FROM nosuch WHERE scope IS NONE GROUP ALL'
  RAISED: NotFoundError kind= NotFound details= {'details': {'name': 'nosuch'}, 'kind': 'Table'} text= The table 'nosuch' does not exist record_id= None
--- single record-collision: 'CREATE t:x'
  RAISED: AlreadyExistsError kind= AlreadyExists details= {'details': {'id': 't:x'}, 'kind': 'Record'} text= Database record `t:x` already exists record_id= t:x
--- single unique-index: "CREATE t:y SET key = 'v'"
  RAISED: InternalError kind= Internal details= None text= Database index `k` already contains 'v', with record `t:x` record_id= n/a
--- single unique-index-hostile-echo: 'CREATE t:z SET key = $k; CREATE t:w SET key = $k'
  OK: [{'id': RecordID(table_name=t, record_id='z'), 'key': 'Transaction conflict: Resource busy. This transaction can be retried'}]
  (NOTE: the SDK's query() checks ONLY result[0] — the 2nd statement's collision is invisible on the single path; pre-existing, execute_transaction's raison d'être)
--- single assert: 'CREATE t2 SET n = -1'
  RAISED: InternalError kind= Internal details= None text= Found -1 for field `n`, with record `t2:…`, but field must conform to: $value > 0 record_id= n/a
--- single coercion: 'CREATE t2 SET n = $v'
  RAISED: InternalError kind= Internal details= None text= Couldn't coerce value for field `n` of `t2:…`: Expected `int` but found `'An error occurred: governed_conflict:t:x'` record_id= n/a
--- single throw-governed: "THROW 'governed_conflict:t:x'"
  RAISED: ThrownError kind= Thrown details= None text= An error occurred: governed_conflict:t:x record_id= n/a
--- single parse: 'SELEC * FROM t'
  RAISED: ValidationError kind= Validation details= None text= Parse error: Unexpected token `an identifier`, expected Eof …
--- single table-exists: 'DEFINE TABLE t'
  RAISED: AlreadyExistsError kind= AlreadyExists details= {'details': {'name': 't'}, 'kind': 'Table'} text= The table 't' already exists record_id= None
--- single update-returns: "UPDATE t SET touched = true WHERE key = 'v'"
  OK: [{'id': RecordID(table_name=t, record_id='x'), 'key': 'v', 'touched': True}]
=== txn record-collision mid: 'BEGIN; CREATE t:a1; CREATE t:x; CREATE t:a2; COMMIT;'
  RAW[0]: OK None
  RAW[1]: {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "The query was not executed due to a failed transaction"}
  RAW[2]: {"status": "ERR", "kind": "AlreadyExists", "details": {"details": {"id": "t:x"}, "kind": "Record"}, "result": "Database record `t:x` already exists"}
  RAW[3]: {"status": "ERR", "kind": "Query", "details": {"kind": "Cancelled"}, "result": "The query was not executed due to a cancelled transaction"}
  RAW[4]: {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "Cannot COMMIT: the transaction was aborted due to a prior error"}
=== txn unique echo: 'BEGIN; CREATE t:c2 SET key = $k; CREATE t:c3 SET key = $k; COMMIT;'
  RAW[2]: {"status": "ERR", "kind": "Internal", "details": null, "result": "Database index `k` already contains 'x can be retried', with record `t:c2`"}
=== txn assert: 'BEGIN; CREATE t:d1; CREATE t2 SET n = -1; CREATE t:d2; COMMIT;'
  RAW[2]: {"status": "ERR", "kind": "Internal", "details": null, "result": "Found -1 for field `n`, … but field must conform to: $value > 0"}
  RAW[3]: {"status": "ERR", "kind": "Query", "details": {"kind": "Cancelled"}, …}
=== txn throw governed: "BEGIN; CREATE t:e1; THROW 'governed_conflict:t:e1'; COMMIT;"
  RAW[2]: {"status": "ERR", "kind": "Thrown", "details": null, "result": "An error occurred: governed_conflict:t:e1"}
=== txn parse: 'BEGIN; SELEC * FROM t; COMMIT;'
  RAW rpc-error: {"cause": null, "code": -32000, "kind": "Validation", "message": "Parse error: Unexpected token `an identifier`, expected Eof …"}
=== txn empty-text throw: "BEGIN; CREATE t:f1; THROW ''; COMMIT;"
  RAW[2]: {"status": "ERR", "kind": "Thrown", "details": null, "result": "An error occurred: "}
```
P2 (`probe_conflict.py`, 12 connections):
```
version: surrealdb-3.2.4+20260803.93ab219
txn round 0: ['ok', 'stmt']
    ('stmt', '[{"kind": "Query", "details": {"kind": "NotExecuted"}, "result": "The query was not executed due to a failed transaction"}, {"kind": "Query", "details": {"kind": "NotExecuted"}, …}, {"kind": "Query", "details": {"kind": "TransactionConflict"}, "result": "Cannot COMMIT: Transaction conflict: Resource busy. This transaction can be retried"}]')
(rounds 1, 2 identical)
single round 0: ['QueryError', 'ok']
    ('QueryError', "kind=Query details={'kind': 'TransactionConflict'} text=There was a problem with the key-value store: Transaction conflict: Resource busy. This transaction can be retried")
(rounds 1, 2 identical)
deep-parse rpc-error: {"cause": null, "code": -32000, "kind": "Validation", "message": "Parse error: Exceeded query recursion depth limit …"}
deep-txn rpc-error: {"cause": null, "code": -32000, "kind": "Validation", "message": "Parse error: Exceeded query recursion depth limit …"}
```
P3 (`probe_removed_db.py`):
```
txn rpc-error: null
  entry: {"status": "OK", "kind": null, "details": null, "result": null}
  entry: {"status": "ERR", "kind": "NotFound", "details": {"details": {"name": "r_…"}, "kind": "Database"}, "result": "The database 'r_…' does not exist"}
  entry: {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "Cannot COMMIT: the transaction was aborted due to a prior error"}
single RAISED: NotFoundError NotFound {'details': {'name': 'r_…'}, 'kind': 'Database'} The database 'r_…' does not exist
```
(P3's `admin.use(NS, "x")` left a stray empty database `x` in `blindreader_probe`; I removed it with the whole namespace. This is disclosed because it was my own residue on the TEST store.)
