# Packet 63c — ruling amendment 20 (sidecar-63c-2, 2026-09-25): the a19 contract author's readings, §8.1–8.4

Rules `REPORT-contract-63c-i-a-a19.md` §8 (`77d9146`). Directive: `REPORT-lead-63c.md@1634e35` (durable copy;
this session's lore client is still down — `Read`/`awk`, said so). The narrow adversary grades `77d9146` as
committed in parallel; the two riders below are assertions on graded pins, not new instruments, and land
with the builder-fix wave's contract addendum (amendment-8's precedent), graded by the cold-audit re-run —
or by the adversary's own receipt if it reports the same door first.

## §8.1 — CONFIRMED: an operator-only owned-but-unscoped store is still REFUSED at i-a; the diagnosis names the operator and E3
The refusal is unconditional at i-a (E3's narrowing is measure-then-tune, deferred as ruled); only the served
DIAGNOSIS changes: *owned by the operator — registered by a pkt-62–63b image; see amendment-1 E3* — never
"multi-principal", never "half-applied". The pinned-bound note is right: the day E3's trigger fires and the
precondition is narrowed deliberately, `[operator-owned]`'s refusal assertion is the one that flips, and it
says so in its own docstring.

## §8.2 — CONFIRMED, with ONE rider: the principal-naming bound is `_REFUSAL_ID_SAMPLE_SIZE`, and it must be READ
A second constant would be a second magic number for one policy ("how much of a bounded list do we serve").
Rider (X2's class — a bound that is read but never perturbed hides a restated twin): the principal count
served is asserted EXACTLY as `min(_REFUSAL_ID_SAMPLE_SIZE, distinct_owner_count)` under the SAME
perturbation leg that already patches the constant for the id sample — patch it to 3, seed more than 3
distinct foreign owners, and the served principal list is exactly 3. The author's *"a smaller bound still
passes"* is the door: a private smaller literal is a second source, invisible until perturbed. One constant,
one perturbation, both lists move together.

## §8.3 — CONFIRMED: `_agent_migration_preconditions(store)`, name + `StoreHandle` pinned, return shape the builder's
The sharing pin redirecting the real function at another store is mutation-by-redirection and is
type-agnostic by construction — the right shape. "Or the like" in amendment 19 meant "the builder may not
rename it out of the pin's sight"; pinning the exact name closes that reading.

## §8.4 — RULED (was a stated bound): when an owned-but-unscoped store ALSO has an unresolvable operator, the refusal names BOTH
Two facts, one refusal: the operator cannot be resolved (its remedy first — nothing else can be diagnosed
until it is), AND N owned-but-unscoped rows exist (count + bounded ids). The reference's *"other" when the
operator is unresolved* is a FALSE diagnosis — those owners may be the operator — so an unresolved operator
means the owners are NOT classified, and the text says so. CONSUMER LAW: a refusal that names one of two
problems buys the operator two round trips. Pin: one fixture carrying both conditions; the served reason
contains both teachings; byte-inert store. Rides the same addendum.

## §W
| # | item | lands |
|---|---|---|
| R1 | §8.2 rider: principal count == `min(bound, distinct owners)` under the constant's perturbation | fix-wave contract addendum (assertion on a graded pin) |
| R2 | §8.4: both-conditions fixture; both teachings; owners unclassified when the operator is unresolved | same |
| — | builder brief: the diagnosis derivation (operator / other / unclassified) and the remedy order | lead |

## Addendum (2026-09-25, Task 20 addendum): CD-1 and CD-2

### CD-1 — the message backfill's WHERE: i-a, by amendment 19's own rule
- **The fact (read at HEAD):** the message leg's UPDATE is `… WHERE owner_principal IS NONE` — owner-keyed,
  and without a `scope` conjunct: F-3's mirror image (a scoped-but-ownerless row would be overwritten), on a
  leg whose "unmigrated" predicate now disagrees with the agent leg, the memory leg (`WHERE scope IS NONE`),
  and `report_unmigrated_governed_rows` (scope-keyed ∀ tables) — the O3 disagreement the reader marked
  "fixed" for agent, still open for message. The agent leg's docstring claims *"`scope IS NONE` is THE
  unmigrated predicate ∀ governed tables"*; the message leg falsifies the claim one function down.
- **Ruling: i-a.** Same class, same wave, same rule — the wave that changed the predicate's meaning sweeps its
  consumers, and the message leg's own WHERE is a consumer. ONE line: `WHERE scope IS NONE AND
  owner_principal IS NONE` (scope-keyed AND self-guarding), the message leg's unmigrated/already counts read
  through the shared preconditions function parametrised by table (never `_owner_count`), the golden updated.
  Rider — the ∀-tables claim gets its pin: over every governed leg's golden statement, the backfill WHERE
  contains `scope IS NONE` (memory, agent, message today; brief joins at ii by inheriting the rule). A claim
  written "∀ governed tables" and checked on one table is this packet's signature defect; the pin is what
  makes the sentence true rather than hopeful.
- **Where it lands:** a19 addendum (`a19a`), one pin + goldens, BEFORE the builder. If `adversary-63c-i-a-a19`
  is still live when it lands, its delta extends to a19a in the same session (cheapest); if retired, the
  cold-audit re-run is the instrument — the pin is a golden-text leg plus a byte-identity leg on a seeded
  scoped-but-ownerless message row, construction-simple. Not ii's: ii would inherit a false ∀ claim and a
  TOCTOU write into the brief leg's template.

### CD-2 — table validity is checked FIRST; the §2.1 teaching never answers a typo
- A refusal that answers `--table agnet` with "your store is multi-principal" is a false diagnosis of the
  operator's actual error (CONSUMER LAW: the served text must describe the question asked), and it costs a
  store read for an invalid request (#97: an invalid request does no store I/O). Argument validation
  precedes the verb-level precondition; "not supported" names the supported set.
- **Pin (same addendum):** an unsupported table on a multi-principal store → the "not supported" teaching,
  ZERO store reads (the precondition query never runs — observed through the store spy the migrate pins
  already use), byte-inert; control: a supported table on the same store → the §2.1 refusal.
