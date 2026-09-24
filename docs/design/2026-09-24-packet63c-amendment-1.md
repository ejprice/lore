# Packet 63c — ruling amendment 1 (sidecar-63c-2, 2026-09-24)

Amends `docs/design/2026-09-13-packet63c-remainder-ruling.md` (`699a6e9`). Found by the 63c-i-a contract
fidelity read (`REPORT-sidecar-63c-2.md` at `0b8ce37`, HEAD `d0c9946`). The ruling is NOT rewritten; each
erratum below states the sentence it corrects and the corrected sentence. Precedence: this doc over the
cited sentence; everything else in the ruling stands.

## E1 — §4.4 Leg A: "four non-aligned shapes on `agent`" → THREE
- **Was:** *"the four non-aligned shapes on `agent` and all three on `brief` are ACCEPTED via a RAW seeder"*.
- **Is:** the THREE non-aligned shapes on `agent` (`name` charset, `session` charset, `role` non-empty) and all
  three on `brief`. `agent` has FOUR birth ASSERTs; the fourth, `status`, is KEPT (§4.2) and is the
  status-STAYS leg, not a drop-lands leg. The contract's `_AGENT_DROP_VIOLATORS` (three) + status-STAYS is
  the correct reading.

## E2 — §4.4 heartbeat leg: the positive control's shape (junk status) cannot work; two pins, not one
- **Was:** *"Positive control: a row seeded with a junk `status` under a downgraded-`status` DDL → `touch` is
  refused by the engine (the KEEP's mechanism, proving the leg can see a denial) — and that row is P-A3."*
- **Why wrong (verified against `AgentRegistry.touch` at HEAD):** `touch` decodes the row through
  `_row_to_agent` (pydantic `Agent.status: AgentStatus`) BEFORE its UPDATE, so a junk-status row is refused at
  decode and never reaches the store ASSERT — F6 working as ruled. P-A3 (the BACKFILL refuses a junk-status
  row) is a separate pin and stays as written.
- **Is:** the heartbeat leg's positive control is build-immune and store-side: seed `role=""` under
  `unbounded_agent_ddl()`, apply **`frozen_asserted_agent_ddl()`** (never the current emitter), then the REAL
  `touch` → the driver's typed store rejection (`SurrealStoreError`), zero rows changed — the Leg B C-control's
  twin through the `touch` seam. RED if `touch` ever stops re-validating the row (e.g. a builder replaces the
  whole-row UPDATE with a MERGE that skips validation).

## E3 — §6 row-level precondition: a KNOWN BOUND with a named re-open trigger
- **Was:** *"a NONE-scope row that already carries an owner is either a multi-principal store (§2.1:
  adjudicate by hand) or a half-applied prior run (impossible after this ruling …)"*.
- **The third population:** a credentialed `register` on any image from pkt 62 (`66b5fa4`, 2026-08-24) through
  63b stamps `owner_principal` on an `agent` table with no `scope` column → owner = the operator, scope = NONE
  — neither multi-principal nor half-applied, and the precondition as written REFUSES the cutover on it.
- **Measured 2026-09-24:** the running `lore-lore` image was built 2026-08-17 20:13 -0400 (`podman inspect`),
  BEFORE pkt 62; production `:18500` has no `owner_principal` column, so the population is EMPTY today. The
  plan of record is COMMIT-ONLY until pkt-65, which ships 62+63 in one image; under 63c code every register
  stamps all three columns, so the population cannot arise between boot and `migrate-governed`.
- **Is:** the precondition stands as ruled — a **KNOWN BOUND**, pinned in R-Q5-1's docstring with this
  re-open trigger: *"a pkt-62-through-63b image deployed before the 63c cutover."* If it fires, the
  precondition narrows to `scope IS NONE AND owner_principal IS NOT NONE AND owner_principal != <the resolved
  operator>`, and operator-owned NONE-scope rows are stamped `scope` + `owner_agent` only (owner untouched).
  Not widened now: measure-then-tune — a branch for an empty set is a mechanism nobody can test on the store
  it guards.

## N1 — §2.2 F5 write-attribution rows: wave ownership (lead call D1 — recommendation)
The register CREATE `write_guard("register")` + CREATE-OWNS-IT allowlist evidence, the re-register entry, and the
dispatcher touch's per-verb label were assigned to no sub-wave by the 63c-i-a/i-b split. Recommendation:
**63c-i-b**, named in its brief as the `agent` write-verb (F4) family observed via
`observe_governed_table_writes("agent")`. Recorded here so the gap is not rediscovered at the cold audit.

## N2 — §6 `LegacyMapping("agent", "OWNED-BY-THE-OPERATOR")`: a docstring row, not a table row
`LegacyMapping` has 0 references at HEAD (`lore_impact`, heuristic) — it is the docstring-shape dataclass
whose docstring enumerates the dispositions. "Joins the mapping table" means: the i-a builder adds the agent
disposition to that docstring beside memory/brief/message. Nothing pinnable; nothing for the contract.

## N3 — heads-up for 63c-ii: the wiring "schema actually applied" proof goes empty
After i-a's DUAL, `test_comms_wiring.py::TestSchemaIsActuallyAppliedNotJustConstructed` rests solely on the
`brief.name` charset ASSERT, which 63c-ii DROPs. The 63c-ii contract replaces the proof with a store fact no
ledger app-validates (`INFO FOR TABLE agent` through the registry's own connection, or a raw duplicate
`capability_hash` rejected by the UNIQUE index) — or deletes the class WITH a removed-behaviour line saying
why. Owner: the 63c-ii contract author; the ii brief names it.
