# Packet 58 — ruling amendment 7 (sidecar-64, 2026-09-26): the 58 ↔ 63c guarded-CAS scanner collision — ONE key (63c's derived DOMAIN + 58's hierarchy PARTITION), the exact-set membership for RS-5 / keeps / `record_measurement`, the build order, and the rollback-log tier of `TxnUniqueViolationError`

Cited by BOTH packets: 63c (amendments 32 §1.3(f) and 33 @ `f66a190`; `REPORT-contract-63c-i-a-a28b.md` §FLAGS
F-2/F-4, §10 item 7, the "RS scanner (repaired)" row) and 58 (amendment 5 §2(B), amendment 6's
`_ROLLBACK_LOG_TIERS`). Directive: lead-63c-2 Task 16. sidecar-63c-2 checks this against am-32/33.
Facts read this turn (symbols; `awk`/`sed` said so): `keeps.py::get_or_create_keyed` at HEAD catches the
BROAD class with a TUPLE passthrough (`except (SurrealConnectionError, TxnContentionExhaustedError):
raise` above `except SurrealStoreError:` → `get_by_key` re-read); RS-5 catches the typed class only
(am-32 §1.3 item 4) — renamed `TxnUniqueViolationError(TxnDomainRejectionError)` by am-33, one class over
the record-id and UNIQUE-index shapes, text-classified ONCE in `_txn._classify_engine_error`;
`floor_calibration/store.py::record_measurement` catches the broad class WITH the tuple passthrough and
re-reads through `_fence_verdict` (a same-class method carrying a `SELECT` literal — a28b's derived
re-read finds it; the old `ast.Name == "SurrealStoreError"` + `_select*` scanner could see neither the
tuple guard nor the helper, which is why it was never listed); a28b's repaired scanner resolves caught
classes BY IMPORT (Name / Attribute / Tuple elements), defines a re-read as *an awaited same-class method
whose body carries a `SELECT` literal*, and computes the guard as *exhaustion cannot reach the handler,
by `issubclass`*. The new CLAUDE.md rule (*Fix the CLASS, not the instance*, operator 2026-09-26) binds
this ruling: lift to the property and its domain's source of truth; hand-lists need a completeness
assertion.

## 0. The ruling in one screen

| # | question | ruling |
|---|---|---|
| **1a — the key** | 63c's (class-by-import + any re-read) vs 58's (hierarchy partition, re-read retired) | **BOTH, as one instrument — they answer different halves.** DOMAIN = 63c's: every `except` handler in the WHOLE production tree whose caught expression resolves by import to a subclass of `SurrealStoreError` (Name / Attribute / Tuple elements) AND that re-reads (a28b's derived definition). PARTITION = 58's: a handler is a **DOOR** iff some caught class's subclass closure contains `TxnContentionExhaustedError` (a door must carry the passthrough above it — tuple guards count); otherwise **SAFE-BY-TYPE** (`_TYPED_CAS_CATCHES`). Re-read presence is the DOMAIN filter (58 am-5 was wrong to retire it there — erratum §1); the caught class is the DOOR test (63c am-32 was wrong to list typed catches as doors — a28b already computes their guard "by type"). 58 am-5's *"derived shell callers"* scope is WITHDRAWN — it lost `record_measurement`; the F5 lesson applies (the file set is an OUTPUT of the tree walk, never an input). |
| **1b — membership** | RS-5 · keeps · `record_measurement` | RS-5 (`agents.py`, `except TxnUniqueViolationError` + `_select_row`) → **`_TYPED_CAS_CATCHES`**. keeps `get_or_create_keyed` → at HEAD a DOOR (broad class, tuple guard — listed in `_GUARDED_CAS_DOORS` the moment the derived scanner lands); after am-33 narrows it to `except TxnUniqueViolationError` → **`_TYPED_CAS_CATCHES`** (the move is forced by the partition's own completeness pin, one line). `record_measurement` → **`_GUARDED_CAS_DOORS`** (broad class; ALREADY guarded by its tuple passthrough — no code fix; message *"FenceLostError — the lease fence moved (a confirming re-read via `_fence_verdict`)"*). The five existing doors stay; `tasks.py::claim_task` → typed (58 am-4). Both sets EXACT, diffed both ways; the union is the derived domain. |
| **2 — build order** | 63c-i-a builds first (pool 30) | **63c-i-a lands the DOMAIN half (a28b's scanner: import-resolved classes, tuples, derived re-read, whole tree, `has_guard` by `issubclass`) with ONE set** — RS-5, keeps and `record_measurement` listed as doors whose guard is "by type" or "tuple passthrough". **58's §HELD re-key is REBASED as a DELTA** on that scanner: the PARTITION (`_TYPED_CAS_CATCHES` split out by the `issubclass` predicate a28b already computes), the two moves (RS-5, keeps), the completeness pins (§3), never a second scanner and never a replacement (a28b's DRY row *"58 am-5's re-key will REPLACE them"* is corrected to EXTEND). contract-58-r2's import of `_TYPED_CAS_CATCHES` is RED until 58's delta lands — adjudicated under the a28 bound (F-3) / 58's pending registry, the lead's bookkeeping. |
| **3 — the tier** | `TxnUniqueViolationError` under am-6's `_ROLLBACK_LOG_TIERS` | **WARNING**, keyed by CLASS. am-6's table is RE-KEYED from THROW-marker PREFIX to the CLASSIFIED EXCEPTION CLASS (the same information one step later — the classifier already maps every marker to a class — and the only key that also covers ENGINE-typed classes with no app marker). `{TxnClaimLostError: DEBUG, TxnGovernedConflictError: WARNING, TxnCasLostError: WARNING, TxnReanchorStragglerError: WARNING, TxnHealChunkError: WARNING, TxnUniqueViolationError: WARNING}`; any OTHER `TxnDomainRejectionError` (the engine refusing DATA: assert/coercion/parse/recursion) and exhaustion → ERROR; unknown → ERROR. No marker is needed for the engine-typed class — that is exactly why the key is the class. §4 |

## 1. The key — lifted to its PROPERTY (the CLAUDE.md rule, applied)

- **Property:** *no handler that DECIDES on a store rejection may reinterpret exhausted contention*
  (#102 — the driver gave up; a re-read or a translation of that state is a lie about a different
  world). **Domain, source of truth:** every `except` handler in the production tree whose caught
  expression resolves to a class in `SurrealStoreError`'s tree — derived by walking the tree and
  IMPORTING the names (a28b), never a name list, never a file list.
- **Three sub-populations, each with its own instrument, and a completeness assertion over the union:**
  1. **re-readers** (this scanner): DOOR if the class closure contains exhaustion → must carry the
     passthrough; SAFE-BY-TYPE otherwise → listed;
  2. **translators** (`except <store class>: raise <Domain> from …`, no re-read): the #400 seam
     `wrap_store_rejection` owns them and carries its own passthrough; the `test_engine_rejection_seam`
     shape guard enumerates them; a direct translate outside the seam is THAT instrument's red (#406);
  3. **pure passthroughs** (`except (…): raise`): the guard clauses themselves.
  **Completeness pin (NEW, 58's delta):** every handler in the derived domain is in exactly one of
  {door, typed-safe, translate-seam, passthrough}; a handler in none — a swallow (`except
  SurrealStoreError: pass`), a log-and-continue, a re-raise of a DIFFERENT class without re-read —
  REDS by `file::function`. This is the assertion that makes the two exact sets honest hand-lists
  (CLAUDE.md rule 2) and closes 58 am-5's over-reach in one direction (re-read retired) and am-32's
  under-partition in the other (typed catches as doors).
- **Erratum, mine (58 am-5 §2(B)):** *"re-read presence is NOT consulted"* — as the DOOR test, right;
  as the DOMAIN filter, wrong: without it every translate handler joins the door set and the #400 seam
  is double-policed. The class test and the domain filter are two different questions; I answered one
  with the other. **Erratum, 63c am-32 §1.3(f) (for sidecar-63c-2 to confirm):** listing RS-5 as a
  `_GUARDED_CAS_DOORS` entry names a door that cannot be one — a28b's own `has_guard`-by-`issubclass`
  says so; the partition makes that a listed TYPED catch instead of a door with a vacuous guard.
- **Bounds kept, named:** a re-read through a helper OUTSIDE the class, or a `SELECT` built without a
  literal, is invisible to the static domain (a28b's bound) — the runtime leg (58 am-5 (C)) is the
  instrument that does not care how the re-read is spelled, and the union cross-check (§3) makes each
  layer measure the other's reach.

## 2. Membership, stated as the exact sets after BOTH landings

```
_GUARDED_CAS_DOORS = {
  "briefs.py::_relate_briefed":                    "already_acked=True with a racer's `via`",
  "findings.py::_transition":                      "IllegalTransitionError — a lost transition race",
  "findings.py::annotate":                         "FindingNotFoundError — a row that vanished (defensive)",
  "tasks.py::transition":                          "IllegalTransitionError — a lost transition race",
  "tasks.py::supersede_task":                      "IllegalTransitionError — 'already superseded by someone else'",
  "floor_calibration/store.py::record_measurement": "FenceLostError — the lease fence moved (confirming re-read via _fence_verdict)",
}
_TYPED_CAS_CATCHES = {
  "tasks.py::claim_task":               "TxnClaimLostError — a lost claim, served as ClaimResult",
  "agents.py::<RS-5 create branch>":    "TxnUniqueViolationError — the identity is taken; the winner is re-read",
  "keeps.py::get_or_create_keyed":      "TxnUniqueViolationError — the UNIQUE key is taken; the winner is re-read",
}
```
(Function names for the two 63c entries are the a28b fold's; the message is the reviewer-visible
"what it reports". Between 63c-i-a's landing and 58's delta, RS-5 and keeps sit in the ONE set with
`has_guard` = by-type / by-tuple — correct and green under a28b's scanner; 58's delta moves them.)

## 3. Order and the cross-checks — riders, and pin it like this

1. **63c-i-a (first):** a28b's scanner as written; ONE set with the three new entries; the F-4 hand-list
   of four transactional doors (`ast.Name == TxnContentionExhaustedError`) is RE-KEYED to the derived
   domain in the same fold (it is the same blind spot — a tuple guard is invisible to it; keeps' and
   `record_measurement`'s guards are tuples).
2. **58 (serial, after):** the partition + `_TYPED_CAS_CATCHES` + the two moves + the union completeness
   pin (§1) + the runtime↔static cross-check (58 am-5 §3): every door AND every typed catch has a runtime
   injection somewhere in the suite (a listed handler no injection drives → RED — if
   `floor_calibration`'s fence tests do not inject exhausted contention at `record_measurement`, that is
   a NEW red the lead routes to that module's owner, not 58's file); every driven function's handlers
   are classified.
3. **Mutations agree across the layers:** make keeps catch the broad class again → static: door without
   an entry → RED; runtime: unchanged (the tuple guard still passes exhaustion) — the static layer
   catches a classification drift the runtime one cannot see, by design. Make `record_measurement` drop
   its tuple guard → static RED (door without guard) AND runtime RED (re-read after exhaustion).
4. **No second scanner, ever:** an AST pin that exactly ONE function in the test tree resolves caught
   classes by import over the production tree (allowlist the one symbol).

## 4. The tier — `_ROLLBACK_LOG_TIERS` keyed by CLASS (am-6 corrected), `TxnUniqueViolationError` → WARNING

- **Why the key moves from marker prefix to class:** am-6 keyed the table on the app-THROW prefix; the
  driver already maps each prefix to a typed class (`claim_lost:` → `TxnClaimLostError`, …) and — per
  am-33 — maps ENGINE text to typed classes too (`TxnUniqueViolationError` from two marker pairs). The
  CLASS is the one key both paths reach; keying on it removes the marker question entirely for the
  engine-typed class and keeps ONE mapping (text → class) in ONE place (`_classify_engine_error`),
  which is am-33's own rule (*"the driver IS the one place text becomes a class"*). `_log_rollback`
  receives the classified exception (or its class) and looks up the tier; the raw root-cause text is
  logged as `extra`, never keyed on.
- **Why WARNING and not DEBUG:** the unique-violation class is PLANNED FOR by both doors (the winner is
  re-read and served) but it is not the fleet's per-call hot path (a keep mint or a register race is
  rare) and the SAME class also carries a possible code defect (a duplicate id a bug minted — the
  re-read then finds no winner and propagates). WARNING keeps it visible without alarming; DEBUG is
  claim's tier because a claim loss is the normal outcome of the most common contention in the fleet.
  Re-open trigger to DEBUG: *"measured WARNING noise from register/keep races at the 65 cutover"* — one
  table entry.
- **Pins (re-keyed from am-6):** the table's keys == the set of typed classes the classifier can PRODUCE
  (derived from `_classify_engine_error`'s return domain + the marker map — a completeness assertion,
  both directions: a producible class with no tier → falls to ERROR and a pin names it as "unclassed";
  a tier for a class the classifier never produces → RED); per-class `caplog` legs including a UNIQUE
  violation on each of keeps and RS-5 → exactly one WARNING; the ASSERT / coercion / parse legs → ERROR;
  exhaustion → ERROR; the synthetic unprefixed THROW → ERROR (deny-by-default control); mutation: drop
  the `TxnUniqueViolationError` entry → its leg logs ERROR → RED, others unchanged.

## Discipline
- Store law §3 (classify semantically, once, in the driver); §5 (contention belongs to the driver; a
  handler never reinterprets exhaustion).
- CLAUDE.md *Fix the CLASS, not the instance*: the property (§1), its domain's source of truth (the
  import-resolved tree walk), the completeness assertion over the union, the generated per-class tier
  legs — and the litmus: a seventh re-reading handler tomorrow lands in exactly one partition by
  derivation or reds by name.
- No code/tests/store touched; this doc only; no attribution trailer.
