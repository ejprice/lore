# Packet 58 — ruling amendment 6 (sidecar-64, 2026-09-26): FORK-3 — the rollback log tier is keyed on WHO decided the rollback (a prefix-marker table, deny-by-default ERROR); FORK-4 — `array::distinct` over the WHOLE column, the legacy duplicate collapses, inventoried

Rules `REPORT-contract-58-r2.md` (`c42eeaf`) §FORKS FORK-3 and FORK-4. Amends `…packet58-amendment-3.md`
§3 (makes its three tiers MECHANICAL) and the kickoff §1/§6 (E11). Facts: `store/_txn.py::_log_rollback`
logs EVERY rolled-back transaction at ERROR (shared by the domain-rejection raise and the contention-
exhausted raise); the classifier already keys ONE app-authored THROW by a prefix marker
(`_GOVERNED_CONFLICT_MARKER = "governed_conflict:"` → `TxnGovernedConflictError`) and the engine's own
refusals by their markers (`_ERROR_CLASS_ASSERT_VIOLATION = "assert violation"`, coercion, parse,
recursion-depth); the ledgers never MATCH their THROW text (they re-read), so a THROW message may gain a
prefix without a consumer moving. Lead-ruled sequencing noted: 58's §HELD `test_retry_seam` re-key lands
FIRST; 64b re-derives its G2 door population on top at integration.

## FORK-3 — RULING: tier by WHO decided; recognised app markers get DEBUG/WARNING, everything else is ERROR

- **The principle (so the tiers are derived, not remembered):** a rollback the APPLICATION authored (a
  `THROW` the ledger wrote for an outcome it planned for) is a domain decision — the operator does not
  need to act; a rollback the ENGINE decided (an `ASSERT` violation, a type coercion refusal, a parse
  error, the recursion ceiling) means the application tried to write something the schema refused —
  every writer validates first, so this is UNPLANNED: on a live store it is the DD-3.c / #107 class (a
  legacy row poisoning a write) and the operator MUST see it. Contention exhaustion is the driver giving
  up — also unplanned. So:
  | root cause of the rollback | tier | why |
  |---|---|---|
  | `claim_lost:` (58's claim THROW) | **DEBUG** | the fleet's most common contention outcome; served as `ClaimResult` |
  | `governed_conflict:` (63's guarded write — a concurrent scope/owner change) | **WARNING** | app-authored, planned for, LOUD to the caller as `GovernedConflict`; server-side a rare race worth seeing, not a fault. **YES, amendment 3's WARNING tier reaches it** — the author's reading and §HELD part 3 stand. |
  | `cas_lost:` — the ledgers' lost-race THROWs (transition/supersede-stamp/annotate/relate), `reanchor_straggler:` (R1), `heal_chunk:` (a chunk's row THROW) | **WARNING** | app-authored, planned for |
  | `assert violation`, coercion, parse, recursion-depth (the engine's classified refusals) | **ERROR** | the engine refused a write the app did not expect to fail — the #107 alarm |
  | contention exhausted | **ERROR** | the driver gave up (unchanged) |
  | ANY unrecognised root cause | **ERROR** | deny-by-default: an unclassified rollback is a fault until someone classifies it |
- **Mechanism (ONE table, the existing marker mechanism generalised — never a second classifier):**
  `_txn` gains `_ROLLBACK_LOG_TIERS: dict[str, int]` = `{"claim_lost:": DEBUG, "governed_conflict:":
  WARNING, "cas_lost:": WARNING, "reanchor_straggler:": WARNING, "heal_chunk:": WARNING}`;
  `_log_rollback` tiers by the FIRST recognised prefix in the root cause's THROW text, else ERROR. The
  ledgers' existing THROW constants (`_TRANSITION_ALREADY_MESSAGE`, `_SUPERSEDE_ALREADY_MESSAGE`, the
  findings/briefs shells') gain the `cas_lost:` prefix — allowed because no consumer parses them (a
  pin: no production module outside `_txn` compares a THROW text; the R4-style AST allowlist over the
  marker strings). The table is the app-THROW VOCABULARY, reviewer-visible; a ledger inventing a new
  THROW without a table entry logs at ERROR until classified — the instrument working, not a bug.
- **Why not a `level=` parameter on the apply seam:** it would let every caller pick its own loudness
  per call (N private policies); the table keeps the policy in the driver, keyed on what the store
  actually reported.
- **Pin it like this:** (i) the table's keys == the set of app-THROW prefixes found by an AST sweep of
  the ledgers' THROW constants (both directions: a prefix in code with no tier → RED; a tier with no
  producer → RED); (ii) per tier a `caplog` leg: a claim loss → 0 records ≥ WARNING; a transition lost
  race → exactly one WARNING; a governed conflict (63's existing fixture) → exactly one WARNING (the
  63 pin that may assert ERROR here is a DUAL row for §HELD part 3 — re-keyed, reason cited); an ASSERT
  violation (the ii-b dirty-store legs' shape) → exactly one ERROR; contention exhausted → ERROR; a
  synthetic unprefixed THROW → ERROR (deny-by-default control); (iii) mutation: drop one table entry →
  that tier's leg RED (WARNING became ERROR), the others unchanged.

## FORK-4 — RULING: `array::distinct` over the WHOLE column; `[A, A, X]` → `[A, X']`; E11 inventoried as CHANGED-DELIBERATELY

- **Ruling:** the re-anchor rewrite is `array::distinct(array::map(blocked_by, …))` over the whole
  column (the kickoff §1 spelling, probed on 3.2.4 by contract-58's instrument — `[old, old]` → `[new]`,
  order kept). A legacy duplicate of ANOTHER blocker (`A, A`) collapses too. The kickoff §6 fixture
  text *"only the X entry rewritten"* meant the VALUE mapping (only X's value changes); it did not rule
  the dedupe scope — this does.
- **Why whole-column, not X-only:** (i) a duplicate entry is the CAS hazard T5 exists to tolerate
  (`array::len(array::distinct(blocked_by))` on the claim side) and the birth-time dedupe exists to
  prevent; the re-anchor is the ONE post-birth write path that touches a legacy `blocked_by`, and
  leaving `[A, A]` in place on a row we are already rewriting preserves a known hazard for no virtue;
  (ii) `edge ≡ blocked_by` — the edge set is a SET (no duplicate `A→Y` edge is ever minted), so the
  deduped column is the shape that actually mirrors the edges; (iii) one expression, no per-entry
  branch (an X-only dedupe needs a positional rewrite — a second, more fragile spelling).
- **Inventory (E11 — the adversary's row, adjudicated):** CHANGED-DELIBERATELY: *a re-anchored legacy
  row loses duplicate entries of its OTHER blockers; the claim CAS (T5) already treated them as one;
  the served `blocked_by` shortens by the duplicates.* Not a silent change — the note event on Y
  records the rewrite, and the render shows the deduped list.
- **Pin it like this:** seed Y raw with `blocked_by = [A, A, X]` → after supersede(X→X'): `[A, X']`,
  exactly one `A→Y` edge (untouched), exactly one `X'→Y` edge, no `X→Y`; the claim CAS on Y with A and
  X' done → WINS (the count-compare agrees with the deduped column); control: `[A, X]` → `[A, X']`
  (no unrelated change); the note event present. The same fixture runs through the boot heal (§am-1)
  — same result.

## Discipline
- Store law §3 (classify SEMANTICALLY — the tier table is a semantic key on the root cause the
  classifier already selects; never position, never a slice of raw text beyond the recognised prefix).
- No code/tests/store touched; this doc only; no attribution trailer.
