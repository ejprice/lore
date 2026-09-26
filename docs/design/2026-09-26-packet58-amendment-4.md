# Packet 58 — ruling amendment 4 (sidecar-64, 2026-09-26): erratum against amendment 3 SD3 — `claim_task` is NOT a guarded-CAS door under decision 3; the canonical set stays unchanged; the door enumerator widens to SEE typed catches and classify them safe-by-hierarchy

Rules `REPORT-contract-58-r2.md` §FORKS FORK-1. Amends `…packet58-amendment-3.md` §6 SD3. Facts read this
turn: `test_retry_seam._discover_guarded_cas_handlers` — a door is an `except SurrealStoreError` handler
(matched by `ast.Name` id) whose body calls a `_select*` method; `has_guard` = the SAME `try` also names
`TxnContentionExhaustedError`; the canonical `_GUARDED_CAS_DOORS` is an EXACT set of five. The store
hierarchy (`store/_txn.py`): `TxnContentionExhaustedError(SurrealStoreError)` and
`TxnDomainRejectionError(SurrealStoreError)` are SIBLINGS; `TxnGovernedConflictError(TxnDomainRejection
Error)` — so decision 3's `TxnClaimLostError(TxnDomainRejectionError)` sits in a subtree that cannot
contain exhausted contention.

## Ruling — Reading A: the set is UNCHANGED; SD3 is withdrawn (erratum, mine)

- **SD3's premise was false for the ruled mechanism.** I wrote *"claim's rollback handler now re-reads
  state"* against the adversary's reference build (whose claim caught `SurrealStoreError` and re-read) —
  one sentence after decision 3 ruled that claim catches `TxnClaimLostError` BY TYPE. A typed catch of a
  `TxnDomainRejectionError` subclass is not the enumerator's door (no `except SurrealStoreError`), and
  — the property that matters — it CANNOT reinterpret exhausted contention: `TxnContentionExhausted
  Error` is a sibling subtree, so `except TxnClaimLostError` never matches it; the #102 invariant the
  door set guards holds for claim BY HIERARCHY, not by a guard clause. Reading B (add the entry and
  keep a purposeless broad handler beside the typed catch to satisfy it) would install the very door
  the invariant exists to police, for the sake of a list.
- **The behavioural pin (r2 lands it):** a claim under exhausted contention PROPAGATES
  `TxnContentionExhaustedError` (never a `ClaimResult`, never re-read) — the invariant's letter, as a
  behaviour; and under a lost race it returns `ClaimResult(claimed=False)` from the typed catch
  (decision 3's pin). Same class as the five doors' "propagates unread" legs, in the typed shape.
- **The contradiction's class (mine, third time this packet):** a clause written before the mechanism
  moved under it — am-25's erratum form: *when a later ruling changes what a state means, sweep every
  earlier pin that seeds that state.* SD3 seeded a door for a handler decision 3 had just retired.

## The reach question — YES, widen the enumerator, but to SEE typed catches and classify them, not to add doors

- **Today's reach is a hidden constant in the OTHER direction:** the enumerator sees ONLY `except
  SurrealStoreError` handlers. A re-reading handler that catches a narrower class is INVISIBLE to it —
  safe when the class is a domain-rejection subtree (claim, by construction), UNSAFE if someone one day
  writes `except (SurrealStoreError, X)` (a tuple — unrecognised, the adversary's residual), `except
  SurrealConnectionError` + re-read, or a class that a future refactor re-parents UNDER a subtree
  containing `TxnContentionExhaustedError`. An instrument whose SAFE cases are simply unseen is a
  scanner with a blind spot wearing an allowlist's name.
- **Ruling (r2's item; not a 58 blocker):** the discovery enumerates EVERY `except <Name>` and every
  `except (<Name>, …)` TUPLE handler whose body re-reads (`_select*` inline — the helper-indirected
  re-read stays the adversary's FILED residual bound), resolves each caught name to the class object
  (`getattr(_txn / the module's imports, name)`), and classifies by HIERARCHY as a checked variable:
  - the caught class (or any tuple member) has `TxnContentionExhaustedError` in its subclass closure
    (`issubclass(TxnContentionExhaustedError, caught)`) → a DOOR: must be in `_GUARDED_CAS_DOORS` and
    must carry the guard clause above it (the existing rule, now over tuples too);
  - otherwise → SAFE-BY-TYPE, and it must appear in a SECOND exact set `_TYPED_CAS_CATCHES`
    (`{"tasks.py::claim_task": "TxnClaimLostError — a lost claim, served as ClaimResult"}`) so the
    reviewer-visible list covers every re-reading handler in the ledgers, and a future re-parenting of
    that class under a contention-bearing base flips it into the door set by DERIVATION (the pin reds:
    a typed catch whose class now contains exhausted contention is a door with no entry).
  - Non-vacuity: both sets non-empty; the synthetic discriminators — a broad catch re-reading without
    the guard (found, door, RED); a typed catch (found, safe, listed); a tuple catch containing the
    broad class (found, door); the helper-indirected re-read (NOT found — the documented bound,
    asserted so).
- **Why this is allowlist-the-safe and not a third list:** the two sets are DERIVED partitions of one
  enumeration (every re-reading handler is in exactly one), and membership follows the type hierarchy
  — a constant the code owns — rather than a name the test remembers. The hand-list is only the
  human-readable message per entry, which is what an exact set is for.
- **Filed by the reviser (per amendment 3 §6):** the two pre-existing reach bounds of the enumerator
  (helper-indirected re-reads; tuple `except`) — the second is CLOSED by this ruling's widening, the
  first stays a named bound (a `_select*` call inside a helper is a different instrument's job — the
  F5-style runtime observation, if ever needed).

## Pin it like this
| pin | RED when |
|---|---|
| `_GUARDED_CAS_DOORS` unchanged (five); `claim_task` ∉ doors; `claim_task` ∈ `_TYPED_CAS_CATCHES` | the purposeless broad handler appears in claim; a typed catch unlisted |
| claim under exhausted contention propagates the typed error unread; under a lost race → `ClaimResult(False)` | a reinterpretation either way |
| hierarchy: `not issubclass(TxnContentionExhaustedError, TxnClaimLostError)` and `issubclass(TxnClaimLostError, TxnDomainRejectionError)` | a re-parenting that makes the typed catch a door |
| the widened enumerator's four discriminators; both partitions non-empty; a tuple catch of the broad class is a door | a blind typed/tuple catch |

## Discipline
- Store law §3 (classify semantically, by type — never by position or text); §5 (the driver owns
  contention; a ledger never reinterprets exhaustion).
- No code/tests/store touched; this doc only; no attribution trailer.
