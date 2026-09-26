# Packet 64 — ruling amendment 3 (sidecar-64, 2026-09-26): 64b split — D-1b (which wave flips the read verbs) and D-3 (the F1 S2 restore instrument)

Rules `REPORT-contract-64b.md` (`6a09954`) §2 D-1b and §4 D-3; the lead has ruled the kickoff §12 split
TRIGGERED (≈0.33–0.40): **64b-i = substrate + writes + migrate · 64b-ii = reads**. Amends the kickoff
§8 (F7 flips) and §2/§12/§13 (the S2 leg). Facts this turn (said so where `awk`): `_COMMS_ACTIONS` at
HEAD carries `"capability"` in the `params` of the enforcing verbs only (drain/ack/story/await/…) —
ii-a's interim shape was "the parameter is FOREIGN on a non-enforcing verb", never accepted-and-ignored;
`ls scripts/` holds no restore driver; `/backups/lore/` holds two full `surreal export` dumps
(`lore-prod-20260728T194511Z.surql` 2.7 GB, `lore-prod-20260803T141930Z.surql` 3.6 GB — pre-63, i.e.
the exact legacy shape), each opening `OPTION IMPORT;` with grouped `-- TABLE: <name>` sections (task,
finding, finding_counter, memory, message, to, … — awk over the first 4000 lines); no `surreal` binary
on the host, but the store image ships `/surreal` (3.2.4) and the vendor documents `POST /import`
(`Surreal-NS`/`Surreal-DB` headers, `--data-binary @file` — `surrealdb-docs` tier, the surreal-deal
tutorial); the 63a migration module's docstring already ruled S2 *"a COMMITTED build-time integration
script, NOT pinned as a unit test; a builder/adversary deliverable"* — and nobody wrote it.

## D-1b — Reading A: 64b-i flips the 7 write verbs + `set_scope`; 64b-ii flips `query`/`get`/`chain_head` WITH their filter

- **Ruling: A**, the ii-a §4 letter: a `True` whose handler does not enforce is the typed-applicability
  lie (PKT-28 C1). Under B, `query` would deny without a capability and then serve an UNFILTERED set
  with one — the F3 isolation pins of 64b-ii would be RED for the wrong reason (a served set, not a
  denied call), and the bound line would describe a filter that does not exist. The #420 legs go GREEN
  7 + 1 in 64b-i (`report`, `acknowledge`, `resolve`, `wontfix`, `annotate`, `resolve_many`,
  `acknowledge_many`, `set_scope`) and 3 in 64b-ii; `lore_findings` leaves
  `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` at 64b-ii close (R-a.5: a tool leaves when ALL its verbs route).
- **The 64b-i interim for the three read verbs (the ii-a shape, reused — never invented):** the
  `capability=` PARAMETER lands on the tool in 64b-i (one signature); each read verb's spec stays
  `requires_capability=False`, and `capability` is a FOREIGN param for it — a supplied value is REFUSED
  with the strict-param teaching (`"'capability' applies only to actions report/acknowledge/… — omit it
  for query until its read filter lands (64b-ii)"` — the `_comms_foreign_param_error` idiom by CALL,
  extended to the finding dispatcher, never a second spelling). Never accepted-and-ignored (the silent
  lie), never resolved-and-unused (a Subject nobody consults is a resolved credential for nothing).
  64b-ii flips the three, adds `capability` to their param sets, and the interim refusal disappears
  (a DUAL row: its pin is DELETE-WITH-REPLACEMENT by the R6 deny-without-capability row).
- **The F5 retirement in 64b-i is WHOLLY write-side:** the reads never carried `created_by`/`actor`
  (`query` takes `status/kind/area/limit`; `get`/`chain_head` take `id_or_number`). 64b-i removes
  `created_by` (report) and `actor` (the six status edges) from the tool signature, lands the shared
  teaching sentence in the `lore_findings` description, the exact-set schema pin, the F4 retired-name
  legs, and `_resolve_identity` (writes use it). The read handlers do NOTHING for F5 in 64b-i; in 64b-ii
  they gain the Subject, `read_filter`, `render_subject_bound` FIRST, and the filtered counts.
- **Pins:** the R6 driver table in 64b-i asserts EXACTLY the 8 `True` verbs (docstring naming 64b-ii's
  growth to 11 — ii-a's `test_the_capability_set_is_EXACTLY_the_message_family_surfaced_not_narrowed`
  precedent); the ∀-leg *"a `True` verb denies without a capability"* holds over the derived set; the
  interim foreign-param refusal on `query`/`get`/`chain_head` WITH a capability is pinned in 64b-i and
  inverted in 64b-ii; the REVERSE #420 pin (kickoff §8 rider ii) keeps the 3 read legs honest —
  pending with a live trigger, not observed, not flagged `True`.

## D-3 — the F1 S2 restore instrument: a COMMITTED `scripts/` driver, written by a one-shot `probe-64` agent NOW; the S2 leg is marker-gated on the driver's receipt, with its bound named

- **Ruling: build the instrument; do not bless a skip with no driver behind it.** The author was right to
  flag rather than bless — an env-gated test with no committed way to produce the env is a hope with a
  marker (#278's class). 63a's docstring promised the script and no wave wrote it; 64 is the third
  packet to need it, so it is written now, in parallel, by a dedicated one-shot **`probe-64`** agent
  (`scripts/` is not a 63c-shared file; a probe agent is the 63a/63c precedent) — BEFORE 64b-i's build,
  so the builder and the cold audit can run S2 as a receipt.
- **`scripts/restore_prod_dump.py` (self-checking, exit 0 with positive controls; PEP 723 + uv shebang
  per the house idiom):**
  1. Endpoint by CONSTRUCTION `http://127.0.0.1:18000` — the port is a constant, not an argument;
     a `--endpoint` flag does not exist (the "NEVER :18500" law is unrepresentable, not remembered).
     Credentials from the same env file the stores use (`~/docker/mcp/lore-secrets/lore.env`).
  2. Target DB minted `test_dump_<utc-stamp>_<uuid4>` under the test namespace — never an existing
     name (asserted absent before import; `--db` is not accepted); printed as the ONE line a test
     consumes (`LORE_PROD_DUMP_DB=<name>`); `--reap <name>` removes it (refusing any name outside the
     `test_dump_` pattern).
  3. `--dump <path>` (default: the newest `/backups/lore/lore-prod-*.surql`), verified to open with
     `OPTION IMPORT;` and to carry a `-- TABLE: <t>` section for every requested table, else REFUSE
     naming the missing ones.
  4. **Governed-slice import by DEFAULT:** a text pass extracts the `OPTION` header + the DDL/data
     sections of the governed set + their dependencies — `memory, message, to, agent, briefed, brief,
     task, blocks, finding, finding_counter, keep, member_of, principal, principal_key, audit` (the set
     is DERIVED at run time from `surreal_schema.governed_node_tables(generate_ddl())` ∪ the relations
     whose endpoints are in it ∪ `{finding_counter, keep, member_of, principal, principal_key, audit}`
     named as the slice's known dependencies — a constant WITH the reason for each) — into a temp
     `.surql`, then `POST /import` streams it (`Surreal-NS`/`Surreal-DB` headers, the vendor's
     documented endpoint). `--full` imports everything (the `chunk`/HNSW tables included — minutes to
     hours; the driver prints the elapsed time either way). ⚠ The section-header format is a
     PROPERTY OF THE EXPORT FILE, not of this repo: the driver asserts it (step 3) and its own test
     fixture is a 40-line synthetic export with two tables (precision + recall controls: a requested
     table found, an un-requested one omitted, a missing one refused).
  5. Receipts printed: per-table row counts read back (`SELECT count() … GROUP ALL`) for every imported
     table, the `scope IS NONE` count per governed table (`report_unmigrated_governed_rows` — expected
     == the row count on a pre-63 dump), the elapsed time, the DB name. Exit non-zero on any mismatch
     between the dump's declared sections and the read-back (an empty table for a section that carried
     rows = a silent partial import = STOP).
  6. Positive controls in the driver's self-test: an import into the minted DB is VISIBLE via a
     second connection; the reap removes it; a second import of the same slice into a fresh DB yields
     identical counts (determinism).
- **The S2 test leg (`test_findings_migrate_64b.py`, the last row of kickoff §12's table):** marker-gated
  on `LORE_PROD_DUMP_DB` (skip-with-reason naming the driver + this amendment when unset — the ONLY skip
  marker in the 64 contract, and its reason text is a promise-registry entry). It connects to that DB,
  applies the CURRENT emitter (`ensure_ready` — the new DDL over the dirty rows, store-ref §1.6's idiom),
  asserts BEFORE: a member `query`/`get` serves 0 of the legacy findings and admin serves N; drives the
  REAL `migrate_governed(table="finding")` through `store_handle`; asserts AFTER: `backfilled == N`, the
  keeper's household serves the SAME id set admin served before (63-rulings §2.2's byte-diff pin),
  `created_by` bytes intact on every row, second run 0, `report_unmigrated_governed_rows` 0. The same
  leg for `task` lands in 64a.
- **The bound, named:** S2 is NOT in the standard gate (a 3.6 GB backup is an environment dependency
  and a multi-minute import); it RUNS at 64b-i's close-out (builder receipt + the cold audit's re-run,
  each pasting the driver's receipt lines), at 64a's, and in 65's dress rehearsal against a FRESH
  `surreal export` of `:18500` (the driver takes any dump path). A close-out without the S2 receipt is
  `done-with-deviations`, never `done`. Re-open trigger: *"the day the export format changes"* (the
  driver's step-3 refusal is the alarm).
- **Who writes what:** `probe-64` (one-shot, Opus): the driver + its self-test + a receipt run against
  the 2026-08-03 dump (counts pasted in its report — the first measurement of the fleet's real
  task/finding legacy population). The 64b-i CONTRACT author: the marker-gated S2 leg (consuming the
  env var). The 64b-i BUILDER + cold audit: the receipt runs. The adversary grades the leg on the S1
  synthetic fixture (the S2 leg's discrimination is the same assertions over real rows).

## Riders roll-up

| pin | where | RED when |
|---|---|---|
| R6 table = exactly the 8 `True` verbs in 64b-i; 11 in 64b-ii | `test_findings_identity_64b.py` (i) / the reads file (ii) | a read verb `True` without its filter; a write verb left `False` |
| interim: `capability=` on `query`/`get`/`chain_head` → foreign-param teaching, no Subject resolved (the F5 observer + a spy on `_resolve_subject`: 0 calls) | 64b-i; inverted in 64b-ii | accepted-and-ignored; resolved-and-unused |
| reverse #420: the 3 read legs stay pending with a live trigger, unmarked, `False` | 64b-i | a marker or a `True` on a pending leg |
| driver self-test: synthetic export precision/recall/missing-section refusal; endpoint constant; DB-name pattern; reap refuses foreign names; read-back == sections | `scripts/restore_prod_dump.py --self-test` (a committed instrument) | a partial import that reads as success |
| S2 leg: BEFORE/AFTER over the real dump, byte-diff of the served id set, second run 0; skip reason registered | `test_findings_migrate_64b.py` (marker-gated) | a leg that runs on S1 only |
| close-out law: S2 receipt pasted or `done-with-deviations` | 64b-i / 64a / 65 reports | — |

## Discipline
- Store law: §1.6 (dirty-store idiom), §3 (never `query()` for multi-statement — the import is the
  vendor's endpoint, not the SDK), §9 (the two stores; `:18500` never a target — made unrepresentable).
- Packages considered: the import mechanism — `surreal import` (needs a container/binary) vs the
  documented `POST /import` (host-side, streams a file) → **REUSE the vendor endpoint**; a hand-rolled
  statement-by-statement replay through the SDK is REJECTED (the §3 statement[0] trap at 3.6 GB).
- No code, no tests, no store touched; this doc only; no attribution trailer on the commit.
