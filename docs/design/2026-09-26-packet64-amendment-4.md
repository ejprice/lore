# Packet 64 — ruling amendment 4 (sidecar-64, 2026-09-26): probe-64's D1 (the pending-table hand-list) and D2 (required vs absent dump sections) — ratified with pins; my amendment-3 step 4 corrected

Rules `REPORT-probe-64.md` §1 D1/D2 (script `scripts/restore_prod_dump.py` committed `80409f4`; D3 —
stripping the export's log lines and requiring `OPTION IMPORT;` as the first STATEMENT — is the probe's
own measured correction of my "opens with" wording and is RATIFIED in passing). Amends
`…packet64-amendment-3.md` §D-3 step 4. Facts (probe-64, measured): `surreal_schema.governed_node_tables`
does NOT exist (my amendment 3 named a function the kickoff §9 only PROMISED for 64d — an un-derived
citation, mine); the repo's ONE derivation is `_governed_contract.governed_populations()` over
`_enforced_relations_scaffold.emitted_schema_ddl()`; at HEAD it yields `{agent, briefed, memory,
message, to}`; both dumps LACK `blocks, keep, member_of, principal, principal_key, audit` (they predate
packets 48/60/61 and the 04b-3 edge) — so "a section for every table, else refuse" refuses every dump
that exists, including the one the receipt run was ordered against; the real population: task 116,
finding 324.

## D1 — RULING: RATIFY the hand-list, made a CHECKED VARIABLE in both directions; the production promotion is 64d's, and the driver switches import then

- **The derivation home:** Reading B (the probe's) STANDS — the driver CALLS the test-tree derivation
  (the `forgery_door_sweep._harness` house idiom); a production twin in `surreal_schema` would be copy #2
  of one policy, outside the probe's writable set, and it is the kickoff §9 / amendment-1 §4 item
  64d owns (`surreal_schema.governed_node_tables(ddl)`, promoted so the substrate IMPORTS it). When 64d
  lands it, the driver's import line moves to the production home — a one-line change named in 64d-ii's
  builder constraints; until then the test-tree derivation IS production truth by construction (it
  derives from the emitted DDL).
- **`PENDING_GOVERNED_TABLES` — ratified as a 3-entry hand-list `{finding: 64b, task: 64a, brief:
  63c-ii}` BECAUSE no production truth names a not-yet-governed population** (the plan is prose; the
  #420 pending dict maps TOOLS, not tables, and a tool→table map is a second hand-list). What makes a
  hand-list honest is two directions of RED, both of which the driver's `--self-test` carries:
  1. **Decay is a PIN, not a rule:** `pending ∩ derived == ∅` — an entry whose table the derivation now
     includes is dead weight and REDS by name (the probe's decay rule, made mechanical). The builder
     constraint for each named wave: *"delete your entry from `PENDING_GOVERNED_TABLES` in the wave that
     lands your trio"* (64b-i for `finding`, 64a for `task`, 63c-ii for `brief`).
  2. **Growth is a PIN:** every governed NODE table the derivation yields is ∈ the amendment-3 named
     slice `AMENDMENT_3_NAMED_SLICE` (the floor the probe already asserts, `slice ⊇ list`) — a governed
     table that joins the derivation WITHOUT joining the slice REDS (a population S2 would silently not
     restore). And the reverse floor stands: the slice ⊇ the amendment-3 list.
  3. **Non-vacuity:** `pending` non-empty ⇒ at least one pending entry's packet is OPEN in
     `docs/plans/v2/INDEX.md` (a text read of the row's status cell — a hand-list that outlives its
     packets is exactly the hidden-constant class); when every entry has decayed the constant is
     DELETED, not left empty (a builder constraint on the last wave — 63c-ii or 64a, whichever is last).
- **Relations over pending nodes stay DERIVED** (`governed_relation_tables` → `blocks` from `task`) — the
  probe's shape; ratified.

## D2 — RULING: RATIFY the required/absent split; the ABSENT set is SERVED, never silent, and the S2 leg asserts the required populations are NON-EMPTY

- **Ruling:** node tables (`derived` ∪ `pending`) are REQUIRED — a dump lacking one is refused naming it
  (they are the populations S2 exists for); relation and dependency tables absent from a dump render
  `ABSENT (the dump predates it) (<reason>)` per table in the receipt, never silently skipped;
  `--tables` makes every named table REQUIRED; zero `-- TABLE:` sections, or a first statement other
  than `OPTION IMPORT;` after the stripped log lines, REFUSE (the format alarm). The probe's picks,
  verbatim — ratified because the alternative (refuse on any absence) refuses reality, and "reality
  predates the table" is a fact the receipt can state (Leg 1), not a defect to hide.
- **Rider — the ABSENT reason is DERIVED, not hand-written per table:** the reason names the packet
  that minted the table, taken from ONE small constant `TABLE_PROVENANCE: {table: packet}` beside the
  slice list (six entries today) — and a table in the slice with no provenance entry REDS the self-test
  (a new dependency table must arrive with its provenance). A dump that carries a table the constant
  calls "absent-capable" is imported normally (the ABSENT line is emitted only when the section is
  missing).
- **Rider — the S2 leg's own assertion (the 64b-i / 64a contract author):** for every REQUIRED node
  table, the read-back count is > 0 on the 2026-08-03 dump (`task 116`, `finding 324` — pasted as the
  expected floor in the receipt, asserted `≥` not `==`, since a fresher export at 65 grows them); a
  required table restored EMPTY is a silent partial import → the driver already exits non-zero (its
  read-back-vs-sections check); the leg asserts the same from the consumer side so a driver regression
  cannot pass unseen.
- **Rider — `--full` is the escape hatch, named:** an operator who needs `chunk`/HNSW restored runs
  `--full` and gets the elapsed time in the receipt; the S2 leg never needs it.

## What this corrects in amendment 3 (erratum, mine)
- §D-3 step 4 cited `surreal_schema.governed_node_tables(generate_ddl())` as if it existed and as if
  `generate_ddl()` emitted the comms tables. Neither is true at HEAD (the probe measured both). The
  derivation is `_governed_contract.governed_populations()` over the union of every `generate_*_ddl`;
  the production promotion is 64d's. Same class as amendment-14's lesson on the 63c side: I cited a
  symbol I had RULED into existence rather than one I had READ — the probe's `lore_verify` habit is the
  instrument that caught it.
- §D-3 step 3's *"opens with `OPTION IMPORT;`"* is corrected to *"the first STATEMENT after the
  stripped export log lines is `OPTION IMPORT;`"* (D3, ratified).

## Riders roll-up

| pin | where | RED when |
|---|---|---|
| `pending ∩ derived == ∅` (decay) · derived nodes ⊆ named slice (growth) · slice ⊇ amendment-3 list (floor) · pending non-empty ⇒ an OPEN packet named | `restore_prod_dump.py --self-test` | a decayed entry kept; a governed table outside the slice; a hand-list outliving its packets |
| required node tables refused when absent; relation/dependency tables render ABSENT with a DERIVED reason; `TABLE_PROVENANCE` covers the slice | `--self-test` (synthetic export precision/recall/missing) | a silent skip; a hand-written reason; a slice table with no provenance |
| S2 leg: required populations ≥ the pasted floor; read-back == sections | `test_findings_migrate_64b.py` / the task twin | an empty required table read as success |
| driver import line moves to the production home at 64d | 64d-ii builder constraint | two derivations |

## Discipline
- lore-first: `lore_verify` would have caught my amendment-3 citation; the probe ran it. Recorded as a
  discipline receipt against myself.
- Packages considered: none.
- No code/tests/store touched; this doc only; no attribution trailer.
