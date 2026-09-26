# Packet 63c — ruling amendment 33 (sidecar-63c-2, 2026-09-26): FK-a28b-1 — the conflict class covers BOTH identity shapes (record id + UNIQUE index); the class is RENAMED

Rules directive #17083 (lead, read from its native wake — the lore client is still `ECONNREFUSED`, so #17083
was neither drained nor acked on thread `63c`) over `REPORT-contract-63c-i-a-a28b.md` §F FK-a28b-1 / §A.1b
(measured on `surrealdb-3.2.4+20260803.93ab219`, seven legs). Amends amendment-32 §1.1 item 3 and §1.2.

## Ruling: Reading 1

The class is *"the write's IDENTITY is already taken — re-read; the winner is there."* A schema declares two
kinds of identity: the record id (primary) and a UNIQUE index (secondary). Both are CAS doors; both re-read the
winner by the identity the caller chose; both must decide from ONE class or R-6 stays two predicates. Reading 2
withdraws am-32 §1.2's own stated intent to save one marker. Reading 1 costs one live-verified marker pair.

**Erratum (mine, am-32 §1.2 + §1.1 item 3):** I ruled keeps' door onto a class whose engine shape I had derived on
the AGENT create (a caller-chosen record id, `already exists`) and stated over both doors, without reading how
keeps mints its id (`keep_id = str(ULID())` — fresh per call; the race is on the UNIQUE `keep.key` index,
`already contains`, and `InternalError` on the SDK path). The quantifier law, again: derived on one member,
stated over the set. The author's live probe is what caught it; the am-32 "bound" about the table text is
CLOSED by the same measurement (the 3.2.x table text differs and is excluded by construction below).

## (a) The untyped `InternalError` — text classification is forced for the U shape, and it is confined

- **Forced, yes:** U-sdk serves `InternalError(kind='Internal', details=None)` — nothing typed to key on. The
  U shape is text-classified on BOTH paths; the R shape is typed on `run_query` and text on the transactional
  path (am-32 unchanged).
- **Confined, yes — and that is what separates it from W14.** W14 was text read AT THE CALLER (routing is not
  sharing). Here the text is read ONCE, in `_txn._classify_engine_error` — the hygiene boundary that already
  reads engine text for ASSERT / coercion / recursion-depth — and every caller (RS-5, keeps) reads only the
  class the ONE mapping helper builds. The rule "never by message text" binds callers; the driver IS the one
  place text becomes a class.
- **Markers, specific by construction:** two noun-bearing pairs, case-insensitive membership like the existing
  markers, never a captured value: `("database record", "already exists")` and `("database index", "already
  contains")`. The pair form is what excludes `The table 't' already exists` (T-sdk/T-txn) — a lone
  `already exists` would not.
- **Pin (c), GENERATED over shape × path:** `{R, U} × {sdk, txn}` → the class, live on `:18000`; controls
  `{T-sdk, T-txn, ASSERT-txn}` → NOT the class (T-sdk classifies as `unspecified rejection` even though it IS an
  `AlreadyExistsError` — the typed branch keys on `record_id is not None`). Mutation, each marker
  independently: reword the record pair → R-txn RED, R-sdk GREEN (typed); reword the index pair → U-sdk AND
  U-txn RED (no typed leg exists for U). The second mutation's double RED is the receipt that U has no typed
  leg.
- **Pin the miss (the U-sdk bound):** a pin asserting U-sdk is `InternalError` with `details is None` on the
  pinned SDK version, docstring: *"KNOWN BOUND — the SDK does not type a unique-index collision; the day it does
  (`KIND_TO_CLASS` gains an index kind, or `InternalError` carries details), add the typed branch ahead of the
  marker and delete this pin."* A bound the next engineer meets deliberately, not by an outage.

## (b) The name no longer fits — rename now, while the author is mid-fold

`TxnRecordExistsError` teaches "a record with this id exists", which is false for the U shape (no record with
the loser's id exists at all). A class name is served prose; the consumer law applies. Rename to
**`TxnUniqueViolationError(TxnDomainRejectionError)`** — SQL vocabulary every LLM reader already holds (a
unique violation is exactly "record id or unique-index value already taken"), and it does not collide with the
driver's "conflict" vocabulary (`RetryableConflictSignal`, `TxnContentionExhaustedError` are write-write
conflicts, retried; this is a domain rejection, never retried). Label:
`_ERROR_CLASS_UNIQUE_VIOLATION = "unique violation — the record id or a unique index value is already taken;
re-read the row"`. am-32's `_ERROR_CLASS_RECORD_EXISTS` / `_RECORD_EXISTS_MARKER` / `TxnRecordExistsError` are
replaced wherever they appear (K9's `_CONFLICT_CLASS`, keeps' narrowed catch, the scanner's canonical set);
nothing else in am-32 changes. The rename is one substitution in a contract not yet built; later it is a
retired-name sweep.

## §W
| # | item | lands |
|---|---|---|
| 1 | `TxnUniqueViolationError` + label + two marker pairs in the ONE classifier; typed R branch unchanged | a28b fold (in progress) |
| 2 | pin (c) generated over `{R,U}×{sdk,txn}` + three controls; per-marker mutation | same |
| 3 | pin-the-miss on U-sdk's untyped `InternalError`, with the re-open trigger | same |
| 4 | keeps' door narrowed to the class (am-32 §1.2 stands, on the correct shape); R-6 → one predicate | same |

## §E
Nothing new for the operator beyond am-32 §E item 1 (the driver seam changes; now two marker pairs instead of
one). Confidence HIGH on the ruling (every engine fact is the author's live measurement, seven legs with
controls); the rename is a design call, cheapest at this moment.
