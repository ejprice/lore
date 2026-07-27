# REPORT-probe-pkt04-store — the packet-04 3.2.1 store probes

brief-base v7 read

## SUMMARY BLOCK

- **P5 verdict first, because the lead asked for it at the top: `refers` + `answers_to` are
  SAFE TO FLIP — under ONE named condition** (every RELATE's endpoints must be created by an EARLIER
  statement in the same txn; production already does this, but the condition is an invariant of the
  DERIVATION, not of the store — §6.5). Not a packet-changing NO.
- **`briefed` is a DIFFERENT verdict — SAFE ONLY UNDER (§10.4).** Its IN endpoint is the
  caller-supplied `agent_id`, NOT minted in-txn, and after the flip a bogus one **rolls the BRIEF
  back — the publish is LOST, not merely un-acked** (§10.2). The brief's app-level check moves from
  ergonomics to requirement.
- **Packet 03 is NOT latently broken — `to`'s shipped shape is measured sound (§10.3)**, which is the
  receipt the lead asked for either way. Its leg-D property is new and deployed: **one bad recipient
  loses the WHOLE fan-out**, message row included.
- **Report defect I fixed:** five citations named `build_file_fragment`; the real symbol is
  `build_file_graph_fragment` (the lead's message exposed it). Corrected throughout.
- **state:** done — 5 probes owed, 5 answered, plus 3 self-added legs that closed gaps the five opened.
- **deviations:** (1) added **P2b/P2c/P4b** — P2 and P4 each exposed a load-bearing gap the briefed leg
  did not cover; closing them cost ~15 min and would otherwise have landed in a builder's lap.
  (2) two of my own declared expectations went RED in P4 — **both were my expectations, not the engine**;
  that is the finding, and it is written up rather than quietly corrected.
  (3) **P5's first run was INVALID and I re-ran it** — my second instrument re-executed the same
  transaction, so on the two load-bearing positive legs the `CREATE` failed with *"record already
  exists"*, an artifact of the probe. It still printed PASS. Fixed by giving each instrument a
  disjoint record set; both then agreed on all nine legs (§6.6).
- **Packages considered:** none — no mechanism specified. (Probe scaffolding reused the repo harness
  `_surreal_harness.unique_database` / `make_env` + the pinned `surrealdb==2.0.0` SDK rather than
  hand-rolling a client; no new dependency evaluated or needed.)
- **P1: §6.4 CONFIRMED on 3.2.1** · rung 4 (probe; rungs 1–3 could not answer) · **§4/§6.4 unchanged —
  a dangling edge is still a FIRST-CLASS member of the identity traversal.** The 3.2 vendor claim is
  still FALSE, and I found *why* their example prints `[]`.
- **P2: §4 CONFIRMED, and INCOMPLETE in 3 ways** · rung 2 gave the shape, rung 4 settled it ·
  `IF NOT EXISTS` = silent no-op; `OVERWRITE` lands it and preserves rows/fields/index/enforcement.
- **P3: §4 CONFIRMED on 3.2.1** · rung 2 (two v3.2.0 executable specs) + rung 4 · #7061 stays fixed under
  BOTH compositions; the 3.2 release-note item (#349) is now VERIFIED and carries a 4.0 break.
- **P4: §4 INCOMPLETE — and the PACKET TEXT IS WRONG** · rung 2 + rung 4 · `@.{1..n}->blocks->task` is
  **not** a transitive read; `TIMEOUT` is not legal where the packet implies. **Blocks a correct build.**
- **P5: SAFE TO FLIP** · rung 4 (rungs 1–3 SILENT — no reference line, no spec, no vendor page covers
  `ENFORCED` against an uncommitted same-txn endpoint) · **`ENFORCED` DOES see endpoints created
  earlier in the same transaction** — `CREATE`-then-`RELATE`, `UPSERT`-then-`RELATE`, both sides, and
  the full `build_file_graph_fragment` sequence all commit; the guard is per-record and statement-ordered.
- **decisions-needed:** 6, listed in §8 — the first (packet 04's transitive-read idiom) must be settled
  before a builder writes the `blocks` read; the rest are pins, reference edits and ledger rows.
- **receipt pointers:** §1 method+provenance · §2 P1 · §3 P2/P2b/P2c · §4 P3 · §5 P4/P4b · §6 P5 ·
  §7 facts §4 does not carry · §8 decisions · §9 residuals · **§10 P5b (`briefed` + `to` verdicts)**.
  ⚠ P5 is **§6**, not the `## 9` the lead's re-send asked for — §9 was already Residuals by then, and
  renumbering twice would have falsified every pointer above (§10.0).

---

## 1. Method, provenance, and which rung answered what

**Engine, live-read 2026-07-26:** `spike-surreal` reports `surrealdb-3.2.1`; image
`docker.io/surrealdb/surrealdb:v3.2.1`. Every probe below ran against
**`ws://127.0.0.1:18000` (spike-surreal, the TEST store)**. `:18500` (production `lore-surreal`) was
never contacted. Each probe minted its own throwaway database via the repo harness
(`_surreal_harness.unique_database()` → `test_<pid>_<uuid4>` under namespace `lore_test`) and reaped it
with `REMOVE DATABASE` in a `finally`.

**One statement per `query()` call, on purpose.** Reference §3/§6.5: the SDK validates `statement[0]`
only, so a multi-statement string would swallow later failures — the exact shape a probe must never
have. Every statement's result *or its raised error text* is recorded verbatim below.

**Every probe carries checked expectations, not just output.** Each leg declares what it expects
*before* the run and prints PASS/FAIL; a probe exits non-zero if any expectation failed. This is why
the P4 correction surfaced at all — the raw output looked plausible.

**Which rung answered each question** (the operator-directed ladder):

| question | rung 1 (`docs/reference/…`) | rung 2 (`surrealql-tests` @`v3.2.0`) | rung 3 (`surrealdb-docs` 3.2) | rung 4 (live 3.2.1) |
|---|---|---|---|---|
| P1 dangling traversal | §6.4 answers it **for 3.1.5** | **SILENT** — no spec RELATEs to a phantom on a non-ENFORCED table and then traverses | **asserts the OPPOSITE**, 3 pages | **ANSWERED** |
| P2 changed relation clause | §4 answers it **for 3.1.5** | **partial** — `redefinition.surql` / `relation_redefinition*.surql` only migrate by `REMOVE TABLE` (destructive); `remove/table.surql` pins bare-DEFINE→error | silent on migrating an existing relation clause | **ANSWERED** |
| P3 UNIQUE cascade | §4 answers it for 3.1.5 | **ANSWERED** — `7061_…`, `7132_…`, `7280_…`, `duplicate_edge_record_id.surql` | — | **CONFIRMED live** |
| P4 recursion/TIMEOUT/cycles | §4 one line, incomplete | **ANSWERED** — `depth_range`, `cycles_bounded`, `cycles_collect`, `path_collect`, `collect_min_depth_cycles`, `timeout`, `recursion_limits` | prose only | **CONFIRMED + extended** |
| P5 `ENFORCED` vs same-txn endpoints | **SILENT** — §3/§4 never address the interaction | **SILENT** — `relate/enforced.surql` commits its `CREATE` before the `RELATE` as separate statements; no spec puts them in one `BEGIN…COMMIT` | **SILENT** — the `ENFORCED` docs say nothing about transactions | **ANSWERED — the only rung that could** |

**Tool honesty.** `lore_search(tier=…)` was the entry point for all five questions and located the
right corpora (for P5 it correctly returned nothing — the corpora genuinely do not cover it). I then **fell back to `grep` over the two static corpus directories**
(`/home/ejprice/docker/mcp/lore-corpora/{surrealql-tests,surrealdb-docs}`) for the *exhaustiveness*
half — "is there ANY spec covering a changed relation clause / a dangling traversal?", where a
semantic top-k cannot prove absence. That is sanctioned fallback case (c) (cross-cutting map) and (a)
(exhaustiveness), and I am saying so out loud per the dogfood protocol. **This is not a lore weakness
and I filed no friction row**: the corpora are static tiers and lore returned the correct neighbourhood
every time; only the *"prove nothing else exists"* step needed grep. Index currency: I edited no
indexed file this session, so no `reconcile` was required.

**Provenance of the probe scripts.** They lived in the session scratchpad under `/tmp`, which
brief-base forbids citing as a durable address — so **every statement and every observed value is
inlined below**, and the report is the record. Re-running any leg needs only the SurrealQL shown.

---

## 2. P1 — does a dangling edge read as a first-class member, or as `[]`?

**VERDICT: reference §6.4 is CONFIRMED on 3.2.1. A dangling edge is a FIRST-CLASS MEMBER of the
identity traversal.** The 3.2 vendor claim remains FALSE as a reader would apply it.
*(PROBED 2026-07-26, spike-surreal `surrealdb-3.2.1`.)*

Fixture — `to` declared `TYPE RELATION IN message OUT agent SCHEMAFULL`, **not** `ENFORCED`
(a dangling edge must be writable at all); one real agent, two phantoms, endpoints bound as
`RecordID` params per §4:

```surql
RELATE $src->to->$dst   -- (message:m_real, agent:a_real)   both real   -> OK
RELATE $src->to->$dst   -- (message:m_real, agent:a_ghost)  DANGLING    -> OK, edge written
RELATE $src->to->$dst   -- (message:m_ghostonly, agent:a_ghost2)        -> OK, edge written
```

Ground truth first — the phantoms genuinely do not exist:

```
SELECT count() FROM agent GROUP ALL   ->  [{'count': 1}]
SELECT * FROM $id  (agent:a_ghost)    ->  []
```

### The identity traversal

| query | observed on 3.2.1 |
|---|---|
| `SELECT ->to->agent AS recipients FROM message:m_real` (1 real + 1 ghost) | `[{'recipients': [agent:a_real, agent:a_ghost]}]` |
| **the discriminator** — `… FROM message:m_ghostonly` (ONLY a ghost) | `[{'recipients': [agent:a_ghost2]}]` |
| **positive control** — `… FROM message:m_lonely` (no edges at all) | `[{'recipients': []}]` |

**The control is what makes this a finding rather than a rumour.** `[]` *is* producible by this exact
query shape — the no-edge message returns it. So the ghost-only message returning `[agent:a_ghost2]`
is a real negative for the vendor's claim, not a blind instrument. (§4 records that this probe's
ancestor reported the *opposite of the truth* on its first run, and only the control caught it.)

### The dereferencing forms (§6.4 says the vendor sentence is true only here)

| form | observed |
|---|---|
| `SELECT ->to->agent.name AS names FROM message:m_real` | `[{'names': ['real', None]}]` |
| same, ghost-only message | `[{'names': [None]}]` |
| `SELECT ->to->agent.* AS recipients FROM message:m_real` | `[{'recipients': [{id: agent:a_real, name: 'real'}, None]}]` |
| `SELECT id, in, out FROM to FETCH out` | the ghost rows carry `'out': None` |
| **`SELECT array::len(->to->agent) AS n FROM message:m_real`** | **`[{'n': 2}]`** |

§6.4 CONFIRMED to the letter: the dereferencing forms yield **`None`, not `[]`** — and the `None`
sits *inside* the array as a positional member, so a consumer zipping names against ids gets a
correctly-lengthed list with a hole in it, not a short list.

**NEW, and directly load-bearing for packet 04's counting law:** `array::len` over the traversal
**counts the ghost** (`n == 2` where one recipient exists). Any served per-agent or per-message
recipient count computed from a graph traversal over a non-`ENFORCED` edge **over-reports**, silently.
That is a TRUST-DOCTRINE surface, and it is an argument for `ENFORCED` on `briefed`/`refers`/
`answers_to` independent of the provenance argument.

### Why the vendor's own example prints `[]` — the mechanism, not just the refutation

`learn/schema-management/tables-and-fields/tables.mdx` (and the identical passage at
`reference/query-language/statements/define/table.mdx`) demonstrates the claim with:

```surql
RELATE city:one->road_to->city:two SET distance = 12.4;
SELECT ->road_to->city FROM city;     -- doc shows: []
CREATE city:one, city:two;
SELECT ->road_to->city FROM city;     -- doc shows: rows
```

**The `[]` comes from the `FROM` clause selecting zero rows** — no `city` record exists yet, so the
statement has nothing to project *from*. It is not the traversal filtering ghosts. Reproduced on
3.2.1: `SELECT ->to->agent AS recipients FROM agent` (one row, no out-edges) → `[{'recipients': []}]`,
i.e. an empty *traversal*, while a table with no rows at all yields a bare `[]`. **The vendor's
example cannot distinguish "the ghost was filtered" from "there was nothing to select" — which is
exactly how the false sentence has survived two minor releases.** `reference/query-language/statements/relate.mdx`
carries the stronger wording verbatim on 3.2: *"If the records to relate to don't exist, a query on
the relation will still work but will return an empty array."*

**Consequence for packet 04's negative fixture:** the assertion must be
`recipients == [<the ghost>]` (or "the ghost is present"), **never** `recipients == []`. A pin written
to the vendor's sentence would be green on a build that never wrote the edge at all.

---

## 3. P2 — `IF NOT EXISTS` vs `OVERWRITE` for a CHANGED relation clause

**VERDICT: reference §4 is CONFIRMED on 3.2.1** (`IF NOT EXISTS` is a silent no-op; `OVERWRITE` is the
only clause that lands a changed relation clause, and it preserves fields, indexes and rows)
**— and INCOMPLETE in three respects**, each measured below.
*(PROBED 2026-07-26, `surrealdb-3.2.1`.)*

Fixture: an **existing** edge table with a field, a UNIQUE index and a ROW —
`DEFINE TABLE IF NOT EXISTS edge1 TYPE RELATION IN alpha OUT beta SCHEMAFULL` +
`DEFINE FIELD note … DEFAULT 'd'` + `DEFINE INDEX edge1_unique ON edge1 FIELDS in, out UNIQUE` +
one `RELATE alpha:a1->edge1->beta:b1 SET note = 'row1'`.

Baseline stored DDL: `DEFINE TABLE edge1 TYPE RELATION IN alpha OUT beta SCHEMAFULL PERMISSIONS NONE`.

### LEG A — `IF NOT EXISTS` with `ENFORCED` added

```surql
DEFINE TABLE IF NOT EXISTS edge1 TYPE RELATION IN alpha OUT beta ENFORCED SCHEMAFULL;
```
- raised **nothing** (returned `None`).
- stored DDL afterwards: **byte-identical to the baseline** — no `ENFORCED`.
- **behavioural** confirmation (a stored-DDL diff alone could be a rendering artifact):
  `RELATE alpha:a2->edge1->beta:ghost` → **accepted**, edge written.

**#107's shape exactly.** A migration written this way ships, boots clean, and guards nothing.

### LEG B — `OVERWRITE`, same clause (and the positive control for Leg A's negative)

```surql
DEFINE TABLE OVERWRITE edge1 TYPE RELATION IN alpha OUT beta ENFORCED SCHEMAFULL;
```
- stored DDL: `DEFINE TABLE edge1 TYPE RELATION IN alpha OUT beta ENFORCED SCHEMAFULL PERMISSIONS NONE`
- **behavioural:** `RELATE alpha:a3->edge1->beta:ghost` →
  `NotFoundError: The record 'beta:ghost' does not exist` — the verbatim error the lead pre-settled.

Leg B is Leg A's positive control: the same instrument, on the same table, **can** see a clause land.

### LEG B preservation — every item checked explicitly, not assumed

| preserved thing | check | result |
|---|---|---|
| ROWS | `SELECT id, in, out, note FROM edge1` before vs after | **identical, including the generated edge id** |
| FIELD definitions | `INFO FOR TABLE edge1` `.fields` | `['in','note','out']`; `note` string-identical (`DEFINE FIELD note ON edge1 TYPE string DEFAULT 'd' PERMISSIONS FULL`) |
| INDEX definition | `.indexes` | `{'edge1_unique': 'DEFINE INDEX edge1_unique ON edge1 FIELDS in, out UNIQUE'}` — unchanged |
| index **still enforcing** (defined ≠ live) | duplicate `RELATE alpha:a1->edge1->beta:b1` | `InternalError: Database index 'edge1_unique' already contains [alpha:a1, beta:b1], with record 'edge1:…'` |

The last row matters: §1.5's warning is that a *define* can **build**. `DEFINE TABLE OVERWRITE` did not
rebuild — it completed instantly, and the pre-existing UNIQUE entry was still present and still
rejecting. Checking the definition string alone would not have shown that.

### The three INCOMPLETE items — new facts §4 does not carry

**(a) `OVERWRITE` is FULL REPLACE for `ENFORCED` too — omitting it SILENTLY UN-ENFORCES the table.**

```surql
DEFINE TABLE OVERWRITE edge1 TYPE RELATION IN alpha OUT beta SCHEMAFULL;   -- ENFORCED omitted
```
→ stored DDL loses `ENFORCED`; `RELATE alpha:a4->edge1->beta:ghost` is **accepted again**.

§1.2 states the full-replace property for `ASSERT`; §4 does not state it for `ENFORCED`. **This is a
live regression door for packet 04:** the guard on `to`/`briefed`/`refers`/`answers_to` survives only
as long as *every* path that re-emits those table definitions carries the keyword. A DDL generator
change, a copy-paste, or a new table-recreate path drops the guard with **zero** error and zero test
signal on a virgin DB (a fresh DB re-creates the table *with* whatever the generator says, so only a
long-lived store shows the difference — and only for edges written after the drop). Recommended pin
in §7.

**(b) A changed `IN`/`OUT` under `OVERWRITE` DOES re-emit the `in`/`out` FIELD definitions.**

```surql
DEFINE TABLE OVERWRITE edge1 TYPE RELATION IN alpha OUT gamma ENFORCED SCHEMAFULL;
```
→ `INFO FOR TABLE edge1`.fields: `out` becomes `DEFINE FIELD out ON edge1 TYPE record<gamma> …`,
`in` stays `record<alpha>`. A `RELATE alpha:a5->edge1->gamma:g1` is accepted; a `RELATE` to the
retired table is rejected: `Couldn't coerce value for field 'out' … Expected 'record<gamma>' but found
'beta:b1'`.

This is worth recording because the engine's own spec (`relation_redefinition_info.surql` @`v3.2.0`)
shows that the table-level clause string and the `in`/`out` field definitions **can diverge** — a
`REMOVE FIELD out` + `DEFINE FIELD out` leaves the table DDL still advertising the old `OUT`, while
coercion follows the field. `DEFINE TABLE OVERWRITE` keeps the two in step. Packet 04 does not change
`IN`/`OUT`, so this is a preserved fact, not a blocker.

**(c) A surviving row whose OUT table was retired is WRITE-POISONED (§1.4's prediction, now measured).**

Control first: the row `UPDATE`s cleanly *before* the migration. After
`DEFINE TABLE OVERWRITE edge1 … OUT gamma`:

```
SELECT id, out, note FROM edge1        ->  still readable, out = beta:b1
UPDATE edge1 SET note = 'touched-after'->  InternalError: Couldn't coerce value for field `out` of
                                           `edge1:…`: Expected `record<gamma>` but found `beta:b1`
DELETE edge1 RETURN BEFORE             ->  succeeds (a cleanup path exists)
```

§1.4 generalises to relation endpoints exactly as written: schema converges, data does not.

### P2b — the flip onto a table that ALREADY holds dangling edges (packet 04's real migration)

**This is the case the three live tables are actually in**, and §4's claim ("pre-existing dangling
edges entirely unaffected") was probed on 3.1.5. Re-settled on 3.2.1:

- The `OVERWRITE … ENFORCED` flip **succeeds with a dangling row present** — there is **no validation
  sweep** over existing rows.
- Positive control: a NEW dangling `RELATE` is rejected immediately afterwards ⇒ the guard is live.
- The pre-existing ghost remains **readable**, **traversable** (still a first-class member — P1's
  behaviour is not suppressed by `ENFORCED`), **updatable**, and **deletable**.
- **`UPDATE to SET ack_note = 'bulk'` over the WHOLE table — the one-statement `drain` shape — did NOT
  fail** despite spanning a ghost row. `ENFORCED` is a `RELATE`-time (write-path) guard; it does not
  re-validate endpoints on `UPDATE`. So the flip introduces **no** new total-denial risk of the
  DD-3.c kind from *this* direction. (Stated narrowly on purpose: this measures `ENFORCED` only, on
  the tables and statement shapes probed — it says nothing about a *field* ASSERT in the same drain.)

**Verdict: §4's "entirely unaffected" is CONFIRMED on 3.2.1**, and #236's deferred cleanup remains
mechanically possible (the ghosts are `DELETE`able after the flip).

---

## 4. P3 — `UNIQUE(in,out)` cascade + the unverified 3.2 release-note item

**VERDICT: reference §4 is CONFIRMED on 3.2.1.** #7061 stays fixed, under **both** compositions
packet 04 ships. **The `duplicate edge record ID` item (#349) that §0 lists as UNVERIFIED is now
verified — and it carries a 4.0 breaking change worth ledgering.**

**Rung 2 answered most of this before any probe ran** — three v3.2.0 executable specs, whose
expected results cannot lie about v3.2.0: `reproductions/7061_cascade_delete_unique_index_ghost.surql`
(cascade cleans the UNIQUE entry; re-RELATE succeeds), `reproductions/7132_phantom_unique_index_relation.surql`
(deleting IN/OUT *before* the relation leaves no phantom entry), and
`reproductions/7280_relation_unique_index_none_phase_scan.surql` (3-field UNIQUE incl. an
`option` field, on an `ENFORCED` relation). Rung 4 then confirmed on the 3.2.1 patch we actually run.

Fixture: `pc TYPE RELATION IN p OUT c`, `DEFINE INDEX pc_unique ON pc FIELDS in, out UNIQUE`;
run twice — once **UNIQUE only**, once **ENFORCED + UNIQUE**. Identical results both times:

| leg | observed |
|---|---|
| **positive control** — duplicate `(in,out)` while both endpoints live | `InternalError: Database index 'pc_unique' already contains [p:one, c:one]` ⇒ the index IS enforcing |
| OUT-side hard delete | edge **cascades away** (`SELECT * FROM pc` → `[]`) |
| re-create the OUT endpoint, re-`RELATE` the SAME pair | **succeeds** ⇒ no ghost UNIQUE entry |
| IN-side hard delete | edge **cascades away** |
| re-`RELATE` after the IN-side delete | **succeeds** |
| absent endpoint (deleted, never recreated), **UNIQUE only** | dangling edge written (expected, non-ENFORCED) |
| absent endpoint, **ENFORCED + UNIQUE** | `NotFoundError: The record 'c:two' does not exist` |

The control is load-bearing: without it, "the re-RELATE succeeded" is consistent with an index that
was never enforcing anything.

### #349 — repeated explicit edge record ids

Probed (3.2.1) and corroborated by the v3.2.0 spec `language/graph/duplicate_edge_record_id.surql`:

```surql
RELATE $src->dup_edge:fixed->$dst SET note = 'first';    -- OK
RELATE $src->dup_edge:fixed->$dst SET note = 'second';   -- OK — no error
SELECT id, note FROM dup_edge;  ->  [{'id': dup_edge:fixed, 'note': 'second'}]
```

**A repeated explicit edge id silently UPDATES the existing edge — one row, last write wins, no error
raised through the SDK.** The engine's spec documents the full matrix and its future:

- `RELATE` on a duplicate explicit id → **updates**, with a server-side warning suggesting `OR RELATE`;
  the spec's own `reason` says *"RELATE should return a hard error beginning in 4.0"*.
- `INSERT RELATION` with a duplicate id → **errors** (`Database record … already exists`) unless
  `ON DUPLICATE KEY UPDATE` is given.
- `RELATE OR UPDATE …` is the explicit opt-in spelling.

**Relevance to packet 04:** if the `blocks` edge ever mints a *deterministic* edge id (e.g. keyed on
`[in, out]` — an attractive way to make the mirror idempotent), a repeat is a **silent overwrite**
today and a **hard error on 4.0**. Either behaviour should be chosen deliberately, not inherited.
Random edge ids + `UNIQUE(in,out)` gives a loud duplicate instead — but then §4's dedupe-before-the-
RELATE-loop rule applies.

---

## 5. P4 — recursive graph paths, TIMEOUT, and cycles

**VERDICT: reference §4's one-line treatment is INCOMPLETE on 3.2.1, and packet 04's Scope-IN
sentence is WRONG.** Nothing here contradicts an existing §4 claim; §4 simply does not say the things
that decide the build. **Two of my own declared expectations went RED — both were mine, not the
engine's.** That is why they are the first two subsections.

### 5.1 ⚠ THE BARE RECURSIVE IDIOM IS NOT A TRANSITIVE READ

Packet 04, Scope IN: *"transitive reads use the recursive idiom (`@.{1..n}->blocks->task`, always
TIMEOUT)"*. Measured on an **acyclic** chain `t1 -> t2 -> t3 -> t4`:

```
task:t1.{1..3}->blocks->task            ->  [task:t4]                       <-- terminal node ONLY
task:t1.{1..3+collect}->blocks->task    ->  [task:t2, task:t3, task:t4]     <-- the transitive closure
task:t1.{1..3+collect+inclusive}->…     ->  [task:t1, task:t2, task:t3, task:t4]
```

**The bare form returns the nodes reached at the TERMINAL depth of each path, not the union of nodes
along the way.** `+collect` is the closure operator — deduplicated, ordered by proximity. This is not
a 3.2.1 quirk: it is the documented semantics in the engine's own v3.2.0 specs
(`language/graph/path_collect.surql`: *"All unique people in alice's reporting chain (deduplicated,
ordered by proximity)"* uses `+collect`; `language/graph/depth_range.surql` returns a single
`person:ceo` for `person:alice.{1..4}->reports_to->person`).

**A `blocks` critical-path read written to the packet's stated idiom would silently return only the
deepest blocker, on a green suite** — and a small-N fixture (a 2-node chain, where terminal ≡ closure)
cannot tell the two apart. FIXTURES MUST DISCRIMINATE: any pin for this needs a chain of **≥3** and a
**branching** shape.

Controls: a leaf (`task:t4.{1..3+collect}`) and an isolated node both return `[]`, so the instrument
can say "nothing"; the served shape works end to end —
`SELECT id, @.{1..8+collect}(->blocks->task).id AS downstream FROM task:t1 TIMEOUT 5s` →
`[{'downstream': [task:t2, task:t3, task:t4], 'id': task:t1}]`.

### 5.2 ⚠ `TIMEOUT` IS A `SELECT` CLAUSE — it is a PARSE ERROR on a bare idiom

```
task:t1.{1..3}->blocks->task TIMEOUT 5s
  ->  Parse error: Unexpected token `TIMEOUT`, expected Eof
       --> [1:30]
SELECT id, @.{1..8}(->blocks->task).id AS chain FROM task:t1 TIMEOUT 5s   ->  OK
```

Packet 04 says *"always TIMEOUT"*, and §4 says *"Add a `TIMEOUT`"*, neither noting that the bare
idiom form **cannot carry one**. So "always TIMEOUT" is only satisfiable via the `SELECT … @ …`
form — which is a constraint on the query shape, not a stylistic preference.

### 5.3 Depth bounds and the 256 limit — a hard error, and a SILENT truncation

| query | observed on 3.2.1 |
|---|---|
| `task:t1.{0..}->blocks->task` | `InternalError: Found 0 for bound but expected at least 1.` |
| `task:t1.{..257}->blocks->task` | `InternalError: Found 257 for bound but expected 256 at most.` |
| `task:t1.{..256}->blocks->task` | OK |
| 299-hop acyclic chain, `@.{..}` (open) | `InternalError: Exceeded the idiom recursion limit of 256.` |
| 299-hop acyclic chain, `@.{..256+collect}` | **256 nodes returned, NO error** — the chain has 299 |

§4's *"`@.{..}` open (cap 256)"* is CONFIRMED as to the number, but the phrasing understates it two
ways: **(1)** the open bound past 256 is a **LOUD error**, not a stop; **(2)** an *explicit* bound
silently **truncates** — `{..256+collect}` on a 299-deep chain returns a short answer with no signal.
A served "critical path" over a >256-deep DAG would be **wrong and confident**. (Realistically far
out of reach for a task DAG; recorded because a truncating read is a trust-doctrine surface and the
bound is fixed, not configurable.)

### 5.4 Cycles

```
-- with t4 -> t1 added (a 4-cycle):
task:t1.{..8}->blocks->task           ->  [task:t1]                  <-- terminal at depth 8; 8 mod 4 = 0
task:t1.{..8+collect}->blocks->task   ->  [task:t2, task:t3, task:t4, task:t1]   <-- deduped, terminates
SELECT id, @.{..+collect}(->blocks->task).id AS reach FROM task:t1 TIMEOUT 5s
                                      ->  [{'id': task:t1, 'reach': [t2, t3, t4, t1]}]   <-- open bound, still terminates
task:t1.{2..3+collect}->blocks->task  ->  [task:t3, task:t4]         <-- min-depth>1 over a cycle: no node drops
```

- **`+collect` deduplicates and terminates over a cycle**, even with an *open* upper bound — dedup
  bounds the frontier. The bare form does not dedupe (the v3.2.0 spec `cycles_bounded.surql` shows a
  21-element result with repeats for `person:alice.{..6}->knows->person`).
- **min-depth > 1 over a cycle drops nothing** on 3.2.1 — §4's note that 3.1.5 fixed this holds, and
  it is independently pinned by the v3.2.0 spec `language/graph/collect_min_depth_cycles.surql`.
- **A working acyclicity detector:**
  `SELECT id, @.{..256+collect}(->blocks->task).id AS reach FROM $task TIMEOUT 5s` → **the task
  appears in its own `reach`** iff it is on a cycle. Confirmed live.
  ⚠ **The BARE form is NOT a detector** — my P4 leg using `@.{..8}` "detected" the cycle *by
  arithmetic accident* (depth 8 landed on `t1` because the cycle length divides 8). With a 3-cycle
  and depth 8 it would have returned a different node and reported "acyclic". **A positive result for
  the wrong reason**; recorded because a pin built on it would be decoration.

### 5.5 My RED expectation about TIMEOUT vs the 256 limit — and the qualifier that resolves it

I declared that an unbounded recursion over a cycle *"does NOT return — TIMEOUT is the only brake"*,
because the v3.2.0 spec `language/graph/timeout.surql` expects exactly that
(`@.{..}` over a cyclic `knows` graph → `The query was not executed because it exceeded the timeout: 1s`).
On **our** 4-cycle it instead raised `Exceeded the idiom recursion limit of 256.` in well under 1s.

**Both are true, and the difference is the branching factor.** With out-degree 1 the frontier stays at
size 1, so depth 256 arrives almost instantly and the *depth* brake fires first; on the spec's dense
social graph the frontier explodes and the *wall-clock* brake fires first. **Which brake fires is a
property of the DATA, not of the query** — so a design that relies on either one specifically is
conditioning an invariant on the one graph shape it was tested against. The safe shape is neither
brake: **an explicit small upper bound, plus `+collect`, plus a `SELECT`-level `TIMEOUT` as the
backstop.**

---

## 6. P5 — does `ENFORCED` see UNCOMMITTED endpoints created in the SAME transaction?

**VERDICT for `refers` + `answers_to`: SAFE TO FLIP — under one named condition (§6.5).**
`ENFORCED` **does** see endpoints created by an earlier statement in the same transaction. The guard
is **per-record and statement-ordered**, not deferred to `COMMIT` and not blanket-relaxed inside a
transaction. *(PROBED 2026-07-26, `surrealdb-3.2.1`.)*

**This probe had no rung above 4.** Reference §3 and §4 never address the interaction; the engine's
own `relate/enforced.surql` puts its `CREATE` and `RELATE` in *separate top-level statements* with no
`BEGIN`; and **no spec in the v3.2.0 corpus contains both `ENFORCED` and a `BEGIN` block** (verified by
grep over the corpus, an exhaustiveness question a semantic search cannot settle). The vendor's
`ENFORCED` documentation says nothing about transactions. A live probe was the only instrument.

### 6.1 Why the question is load-bearing — the production shape, read first

`graph_surreal.py::build_file_graph_fragment` emits ONE `TxnFragment` executed by a single
`execute_transaction`, in this order (read from the source, not assumed):

1. `DELETE code_node WHERE tier = $t AND file_path = $f;` + the same for `refers` and `answers_to`
   (`_purge_statements`)
2. `UPSERT $name_i SET value = $v;` — **every OUT endpoint**, for every name the file touches
3. per node: `CREATE $code_node_id CONTENT {…};` then
   `RELATE $code_node_id->answers_to->$fqn_name;` and `->$bare_name;` (`_node_statements`)
4. per reference: `RELATE $src->refers->$dst;` (`_edge_statement`)

**Every endpoint of every code-graph edge is created inside the same transaction, statements before
the RELATE that points at it.** If `ENFORCED` could not see them, the flip would break indexing 100%
in production while every virgin-DB test stayed green — #107's exact shape. The docstring at
`build_file_graph_fragment` even states the intent: *"the name records are UPSERTed next … so an edge to a
not-yet-defined name never dangles (order-independence)"*.

### 6.2 Instruments — and a probe failure I have to report

Two readings per leg: **`execute_transaction`** (the production seam — its verdict is what production
gets) and **`query_raw`** (per-statement `status`/`result`, so a failure names the offending statement
and its verbatim engine text). A bare multi-statement `query()` was never used — §3/§6.5: it validates
`statement[0]` only, so a rejected `RELATE` returns `None` with no exception. **This probe is exactly
the shape that trap eats**, and the lead's warning was correct.

**⚠ My first run was invalid and I re-ran it.** Both instruments initially shared one params dict, so
`query_raw` re-executed a transaction `execute_transaction` had already committed — and on L1 and L3
the `CREATE` then failed with `Database record 'code_node:txn_node' already exists`. **The leg still
printed PASS**, because the seam verdict (correctly COMMITTED) was what the expectation read; the
corroborating instrument had silently stopped corroborating and was reporting a failure about
something else entirely. *"If step N silently no-opped, would step N+1 still print something that
reads as success?"* — here step N+1 printed a **failure** that read as noise, which is the same defect
wearing the other hat. Fixed by giving each instrument a **disjoint record set** so both observe the
same virgin precondition; the re-run has both instruments agreeing on all nine legs, and the runner
now FAILS the leg if they ever disagree.

### 6.3 The legs

| # | shape (inside one `BEGIN … COMMIT`) | `execute_transaction` | `query_raw` |
|---|---|---|---|
| **L0** | **POSITIVE CONTROL** — `RELATE`, both endpoints committed BEFORE the `BEGIN` | **COMMITTED** | all OK |
| **L7** | **NEGATIVE CONTROL** — `RELATE` to a name created nowhere | **RAISED**, rolled back | `stmt[1] ERR: The record 'name:never_created' does not exist` |
| **L1** | `CREATE $node;` → `RELATE $node->answers_to->$name` (the IN-side `answers_to` shape) | **COMMITTED** | all OK |
| **L2** | `UPSERT $name;` → `RELATE $src->refers->$name` (the OUT-side `name` shape, name is NEW) | **COMMITTED** | all OK |
| **L3** | `UPSERT $name;` `CREATE $node;` → both RELATEs (**both** endpoints uncommitted) | **COMMITTED** | all OK |
| **L6** | `UPSERT` an ALREADY-COMMITTED name → `RELATE` (steady-state re-index) | **COMMITTED** | all OK |
| **L4** | **the FULL `build_file_graph_fragment` sequence** — 3 purge DELETEs + 2 UPSERTs + CREATE + 2×`answers_to` + 1×`refers` | **COMMITTED** | all OK |
| **L5** | **REVERSE ORDER** — `RELATE` BEFORE its endpoint's `CREATE` | **RAISED**, rolled back | `stmt[1] ERR: The record 'code_node:later_node_raw' does not exist` |
| **L8** | **NEGATIVE CONTROL** — `CREATE` node A, then `RELATE` from a DIFFERENT absent node B | **RAISED**, rolled back | `stmt[2] ERR: The record 'code_node:never_created' does not exist` |
| **L9** | `DELETE $node;` → `RELATE $node->…` (endpoint removed earlier in the same txn) | **RAISED**, rolled back | `stmt[2] ERR: The record 'code_node:committed_node' does not exist` |

**Both controls are load-bearing and both fired.** L7 proves `ENFORCED` is **not inert inside a
transaction** — without it, every COMMITTED row above would be worthless. L8 proves the guard is
**per-record, not per-transaction**: creating *some* node does not blanket-bless a *different* absent
endpoint. L0 proves a `RELATE` in a txn with committed endpoints succeeds, so every rejection above is
attributable to the endpoint, not to the transaction boundary or my fixture.

L4 wrote what it claimed: `SELECT count() FROM answers_to GROUP ALL` → `[{'count': 4}]` (2 per
instrument × 2 instruments), i.e. the fan-out actually landed rather than the txn silently no-opping.

### 6.4 What this establishes about the mechanism

- **Visibility is read-your-own-writes within the transaction.** A statement sees the effects of every
  earlier statement in the same txn, including for `ENFORCED`'s existence check.
- **The check is at RELATE time, not at COMMIT time.** L5 proves it: the endpoint exists by the end of
  the transaction, and the `RELATE` is still rejected because it ran first. So `ENFORCED` cannot be
  satisfied by "it'll exist by COMMIT" — statement order is the contract.
- **The rejection aborts the whole transaction** (`Cannot COMMIT: the transaction was aborted due to a
  prior error`), consistent with §4's error-ergonomics row: one bad endpoint, as untyped prose, after
  the write is attempted, killing the txn. For the code graph that means **one bad endpoint fails the
  whole file's index write** — not a partial graph. That is the safe failure direction, but it is
  loud, so the ergonomic app-level check §4 recommends keeps its value here too.

### 6.5 ⚠ THE CONDITION THE VERDICT RESTS ON — and it is NOT a store question

**SAFE TO FLIP requires: every `RELATE`'s endpoints are created by an EARLIER statement in the same
transaction.** For the `name` (OUT) side that is structurally guaranteed — `build_file_graph_fragment`
UPSERTs the union of *all* names (node FQNs, bare names, **and every edge dst**) before any RELATE.

**For the `code_node` (IN) side it is an invariant of the DERIVATION, and I could not confirm it
holds.** `_edge_statement` binds `src = _code_node_id(tier, file_path, edge.src)`, where `edge.src`
comes from `CodeGraph._derive_edges` — while the CREATEd nodes come from `_derive_nodes`. Nothing I
can see enforces `{edge.src} ⊆ {node.qualified_name}`. Two shapes I could not rule out by reading:
`_defines(class_qualified, method_qualified)` fires for a METHOD chunk and uses the CLASS as src
(is a class node always emitted for a file that has method chunks?), and `_reference_edge(caller, …)`
takes a caller FQN that may name something finer-grained than any emitted node.

**Today this is invisible**, because a `refers` edge from a src that was purged and never re-created
just becomes a dangling edge. **Under `ENFORCED` it becomes a hard failure of the whole file's index
transaction** — and the purge DELETE at the top of the fragment means the src is *actively removed*
first (L9's shape). So: **the flip converts a silent dangling edge into a loud indexing failure**,
which is the point of the flip, but only if that set relation actually holds.

**Required before the flip ships** (my recommendation, §8 item 6): a pin asserting
`{edge.src for edge in edges} ⊆ {node.qualified_name for node in nodes}` over a REAL multi-chunk file —
classes with methods, nested functions, module-level calls, an unresolved reference. If it does not
hold, the fix is in the derivation or an added UPSERT for src nodes, **not** in weakening the flip.
This is a contract question, not a store question, which is why I am flagging it rather than deciding
it.

### 6.6 Reference verdict

**§3 and §4 are INCOMPLETE, not wrong, on 3.2.1** — neither says anything about `ENFORCED` inside a
transaction, and it is the fact that decides whether packet 04's flip is shippable. Proposed as a new
§4 line in §7 item 9.

---

## 7. Facts established here that reference §4/§6.4 does not currently carry

Listed for the lead — **I did not edit the reference**, per the brief.

1. §4/§6.4 re-probed and **CONFIRMED on 3.2.1** (P1, P2, P2b, P3): the version-provenance caveat in
   the reference's header can be discharged for these specific claims, with today's date.
2. **`DEFINE TABLE OVERWRITE` omitting `ENFORCED` silently drops it** — full-replace applies to the
   relation clause. (§1.2 says this for `ASSERT`; §4 does not say it for `ENFORCED`.)
3. **`array::len()` / any count over a graph traversal counts dangling edges** — a served-number
   hazard, and a second, independent argument for `ENFORCED`.
4. **The vendor's `[]` example is an empty-`FROM` artifact** — the mechanism behind §6.4's refutation,
   which makes the refutation checkable rather than assertive.
5. **`ENFORCED` is a write-path (`RELATE`-time) guard only** — it does not re-validate endpoints on
   `UPDATE`, so a bulk `UPDATE` spanning a pre-existing ghost row succeeds.
6. **A retired `IN`/`OUT` table write-poisons surviving rows** (§1.4 generalised to endpoints), and
   `OVERWRITE` keeps the table clause and the `in`/`out` field definitions in step (the engine's own
   spec shows they can diverge under `REMOVE FIELD`/`DEFINE FIELD`).
7. **The recursion section needs three corrections**: bare ≠ `+collect` (the big one), `TIMEOUT` is a
   `SELECT` clause only, and the 256 bound is a loud error when open / a **silent truncation** when
   explicit.
8. **#349 verified**: `RELATE` on a duplicate explicit edge id **updates silently** (hard error
   promised for 4.0); `INSERT RELATION` errors; `RELATE OR UPDATE` / `ON DUPLICATE KEY UPDATE` are the
   opt-ins. §0's UNVERIFIED marker on this item can be discharged.
9. **`ENFORCED` is satisfied by an endpoint created earlier in the SAME transaction** — read-your-own-
   writes, checked at `RELATE` time (not deferred to `COMMIT`), per-record (not per-transaction).
   Nothing above rung 4 documents this, and it is the fact that makes the `refers`/`answers_to` flip
   shippable. Belongs in §4 beside the `ENFORCED` adoption table, cross-referenced from §3.

---

## 8. Decisions needed (lead / operator — I decided none of these)

1. **BLOCKING for the `blocks` build — packet 04's transitive-read idiom is wrong.** Scope IN names
   `@.{1..n}->blocks->task`; that returns terminal-depth nodes only. Recommend amending the packet to
   `@.{1..n+collect}` (with `+inclusive` only where the root is wanted), served through the
   `SELECT … @ … TIMEOUT` form since the bare idiom cannot carry a `TIMEOUT`. **Ruling needed before a
   builder writes the read**, and the contract needs a ≥3-deep, branching fixture — a 2-node chain
   cannot discriminate.
2. **A regression pin for the un-enforcing door (§3(a)).** `OVERWRITE` without `ENFORCED` silently
   un-guards a table, invisibly on a virgin DB. Recommend a dirty-store pin per edge — flip on, then
   assert a dangling `RELATE` is rejected — plus a mutation proof (delete `enforced=True` from the
   generator call → every one of the four pins must go RED). Prove sharing by mutation, not by
   inspection: four tables routed through `_define_relation_table` *looks* identical to four with
   private copies.
3. **Reference §4/§6.4 edits** — the nine items in §7. Mine to report, yours to land.
4. **#236 / #105 wording.** P2b confirms pre-existing ghosts stay fully workable after the flip and
   remain `DELETE`able, so the deferred cleanup is mechanically open. Note for whoever widens #105's
   text: `ENFORCED` does **not** make ghosts self-announcing — P1 shows they still read as
   first-class members *after* the flip.
5. **Ledger the 4.0 break (§4, #349).** If `blocks` uses deterministic edge ids, today's silent
   overwrite becomes a hard error on SurrealDB 4.0. Cheap to file now, expensive to discover later.
6. **The one condition P5's SAFE verdict rests on — needs a pin before the `refers` flip ships.**
   `ENFORCED` is satisfied by same-txn endpoints, so the store is not the risk; the risk is whether
   `{edge.src} ⊆ {node.qualified_name}` actually holds in `CodeGraph._derive_edges` vs `_derive_nodes`
   (§6.5). Today a violation is an invisible dangling edge; after the flip it fails the whole file's
   index transaction. Recommend a contract pin over a REAL multi-chunk file (class+methods, nested
   functions, module-level calls, an unresolved reference) **before** the flip lands. If it does not
   hold, fix the derivation or UPSERT the src nodes — do not weaken the flip. This is a derivation
   question, not a store one, so it is yours to route, not mine to settle.

---

## 9. Residuals — everything else I noticed (scope law: reported, not judged)

- **`ORDER BY` under an explicit projection** reproduced verbatim on 3.2.1 while probing:
  `SELECT ->to->agent FROM message ORDER BY id` → `Parse error: Missing order idiom 'id' in statement
  selection`. Already in §7 (entry dated 2026-07-25); this is independent corroboration, no action.
- **Error types are usefully distinguishable** through the SDK: `NotFoundError` (ENFORCED endpoint),
  `InternalError` (UNIQUE violation, coercion, recursion limit), `AlreadyExistsError` (bare
  `DEFINE TABLE`), `ValidationError` (parse). Not a substitute for typed errors — §4 is right that
  parsing `"The record 'x:y' does not exist"` to recover an id is a literal-keyed instrument this repo
  forbids — but the *class* is switchable-on without string matching. Possibly useful to the ergonomic
  app-level layer; flagging, not recommending.
- **`DEFINE TABLE OVERWRITE` on a populated relation table did not rebuild** (instant; UNIQUE entries
  intact) — consistent with §1.5's carve-out for the TABLE verb, now also true for relation tables
  carrying an index, on 3.2.1.
- **A bare `DEFINE TABLE` on an existing table raises** `The table 'edge1' already exists` — matching
  the v3.2.0 spec `language/statements/remove/table.surql`. So the `SEQUENCE`-style boot-crash failure
  mode (§1.1) applies to tables too: `ensure_ready` can never use a bare `DEFINE TABLE`.
- **No probe touched production.** All five scripts asserted `env.url == ws://127.0.0.1:18000/rpc`
  before opening a connection and reaped their database in a `finally`; one script raised mid-body (a
  bug of mine — `RecordID` is unhashable) and its teardown still ran. Verified after the fact:
  **zero of my probe databases remain** in `lore_test`.
- **⚠ Unrelated, and surfaced rather than judged: the `lore_test` namespace on spike-surreal holds
  555 databases** (counted 2026-07-26 via `INFO FOR NS`). These are orphaned `test_<pid>_<uuid4>`
  databases from earlier runs whose teardown did not complete (a killed pytest, a crashed harness).
  Nothing here depends on it and it did not affect any probe, but 555 abandoned RocksDB databases on
  the test store is a housekeeping question — and, less obviously, a *fixture* question: the harness's
  guarantee is a virgin DB per test, and nothing reaps the ones a hard kill leaves behind. Do you want
  this looked at?
- **⚠ `briefed`'s flip lands on a DIFFERENT call shape than `refers`/`answers_to` — flagged, not
  settled.** P5 measured the code-graph shape (multi-statement `execute_transaction`).
  `BriefLedger._relate_briefed` is **not** that shape: it is a SINGLE-statement `_query`, and it
  **catches `SurrealStoreError` as the idempotent-re-ack SIGNAL** — the `UNIQUE(in,out)` rejection is
  load-bearing control flow there, disambiguated by reading back the existing edge. *(READ from the
  source, not probed.)* After the flip, an `ENFORCED` rejection (*"The record 'agent:x' does not
  exist"*) arrives through **that same `except SurrealStoreError`**; `_select_briefed_edge` then finds
  no edge and the original rejection re-raises, so the behaviour looks correct — but two distinct
  failure modes now share one catch and are separated only by a follow-up read. Worth a builder's
  attention and a pin (a publish to a NON-EXISTENT agent must raise, and must NOT be reported as
  `already_acked`), because `publish(agent_id: str | None)` still takes a bare string.
- **⚠ `ENFORCED` alone does not satisfy packet 04's own Exit criterion.** *(MEASURED in P5.)* The
  Exit line requires *"a bogus-recipient publish/send TEACHES instead of dangling"*. What
  `execute_transaction` actually raises is
  `SurrealDB transaction failed and was rolled back: statement 2 of 3 was rejected (unspecified
  rejection); see the server log for the full engine detail` — the engine's `The record 'name:x' does
  not exist` is deliberately kept out of the raised message by the seam's error-message hygiene
  (ledger #31) and logged server-side instead. So the **app-level check is not optional garnish for
  the Exit criterion — it is the only layer that can teach**, which is exactly what §4 says and worth
  restating because "we flipped ENFORCED" reads like the job is done.
- **What I did NOT measure**, so nobody inherits it as settled: the cost of `ENFORCED` on 3.2.1 (§4's
  "~2.8% at 16-way" is a 3.1.5 number); `ENFORCED` interaction with `INSERT RELATION` on 3.2.1 (§4's
  claim is 3.1.5 + the v3.2.0 spec, not re-probed here); how many dangling edges exist in the
  production store (#236 — explicitly out of scope, and §4 is right that any number quoted before a
  sweep is a rumour); **P5 under CONTENTION** (every P5 leg was single-writer — I did not test an
  `ENFORCED` RELATE racing a concurrent DELETE of its endpoint, which is the shape where a
  read-your-own-writes guard could interact with the retry seam); and **whether
  `{edge.src} ⊆ {node.qualified_name}` holds** (§6.5 — the condition P5's verdict rests on, a
  derivation question I flagged rather than settled).

*All measurements in this report: **PROBED 2026-07-26**, `spike-surreal`, engine `surrealdb-3.2.1`,
SDK `surrealdb==2.0.0`. Corpus citations: `surrealql-tests` pinned at the engine's `v3.2.0` tag;
`surrealdb-docs` at version "3.2".*

---

## 10. P5b — the ASYMMETRIC fragments (`briefed`, `to`), and the per-edge verdicts

> **Orientation / numbering note.** The lead asked for P5 as `## 9`, believing it had never landed
> (the mid-run message was dropped by the busy-agent inbox bug, but a later re-send did land and P5
> ran). **P5 is §6**, not §9 — §9 was already Residuals when the request arrived, and renumbering a
> second time would falsify every pointer in the summary block. This section is the ADDITION P5b:
> the `briefed` verdict the lead asked for separately, which §6 did **not** cover.
> *(PROBED 2026-07-26, spike-surreal `surrealdb-3.2.1`.)*

### 10.1 The premise that needed splitting

The lead's brief stated that on both flipped edges *"every endpoint is minted by an EARLIER STATEMENT
OF THE SAME FRAGMENT … with no caller-supplied input anywhere."* **That is true of `refers` and
`answers_to`. It is NOT true of `briefed`** — and it is the difference that produces two different
verdicts. Read from source:

| fragment | endpoint minted in-txn | endpoint CALLER-SUPPLIED |
|---|---|---|
| `graph_surreal.py::build_file_graph_fragment` | **both** — `UPSERT $name` (OUT) and `CREATE $code_node` (IN) | none |
| `briefs.py::_publish_fragment` | `brief` (**OUT**) — `CREATE type::record('brief', $pub_id)` | **`agent` (IN)** — `RecordID(AGENT_TABLE, agent_id)`, a bare string resolved from nothing |
| `messages.py::_send_fragment` | `message` (**IN**) — `CREATE type::record('message', $msg_id)` | **`agent` (OUT)** — `RecordID(AGENT_TABLE, ref.id)` per recipient |

So `briefed` and `to` are mirror images of each other, and neither is the code-graph shape. §6 answered
"does `ENFORCED` see the in-txn endpoint" (yes). The question these two raise is different: **what
happens to the OTHER statement's row when the caller-supplied endpoint is bogus.**

### 10.2 `briefed` — the flip changes what a bogus `agent_id` COSTS

Fragment shape probed verbatim in structure: `CREATE type::record('brief', $pub_id) CONTENT {…}` then
`RELATE $ack_from->briefed->$ack_to SET via = $ack_via, at = $ack_at`.

| leg | `briefed` state | result |
|---|---|---|
| **A** — bogus `agent_id` | **NOT enforced (today)** | **COMMITTED** — brief `b_today` published, **and a dangling ack edge written** (`in: agent:a_bogus`, `out: brief:b_today`) |
| **B control** — real agent | **ENFORCED** | **COMMITTED** — the in-txn OUT endpoint (`brief`) satisfies `ENFORCED` |
| **B** — bogus `agent_id` | **ENFORCED** | **REJECTED**, `statement 3 of 4 … rolled back` |
| **B, the receipt that matters** | **ENFORCED** | `SELECT id FROM brief WHERE id = brief:b_lost` → **`[]`** |

**⚠ THE BRIEF IS ROLLED BACK. The publish is LOST — not merely un-acked.** Today a publish with an
unknown `agent_id` still publishes the brief (and leaves a ghost ack). After the flip, the same call
publishes **nothing**. That is the correct atomicity — the `_publish_fragment` docstring already says
*"a rejected CREATE rolls the edge back with it"*, and this is simply its converse — but it is a
**behaviour change on a live verb**, not a silent tightening, and `publish(agent_id: str | None)`
still takes a bare string.

Control: the good publish (`brief:b_ok`) survived the neighbouring rollback, so the rollback is
per-transaction and not a global abort — the instrument can distinguish the two.

### 10.3 `to` — packet 03's shipped behaviour, now MEASURED rather than inferred

The lead flagged the `to` precedent as *"a hint from a shipped neighbour, not a measurement."* Here is
the measurement, on `to` declared exactly as packet 03 ships it (`ENFORCED`):

| leg | result |
|---|---|
| **C control** — send to a REAL recipient, `message` minted in-txn | **COMMITTED** — the shipped shape works; the in-txn IN endpoint satisfies `ENFORCED` |
| **C** — send to a BOGUS recipient | **REJECTED**, and `SELECT id FROM message WHERE id = message:m_lost` → **`[]`** — the message is rolled back too |
| **D** — fan-out to **[REAL, BOGUS]** | **REJECTED**; message not created; **zero** delivery edges — `SELECT id, out FROM to WHERE in = message:m_partial` → `[]` |

**So packet 03 is NOT latently broken — the shipped precedent is sound, and §6's result explains why.**
But leg **D** is a live property worth stating plainly: **one bad recipient in a fan-out loses the
WHOLE send**, with no partial delivery and no message row. Atomic, and defensible — but it means the
blast radius of a single bad recipient id is every recipient in that send. This is deployed today; it
is not something packet 04 introduces.

### 10.4 VERDICTS, per edge

- **`refers` + `answers_to` — SAFE TO FLIP, under the §6.5 condition.** Both endpoints are minted
  in-txn with no caller-supplied input, and §6 proves `ENFORCED` resolves them. The condition is
  unchanged and unrelated to this section: `{edge.src} ⊆ {node.qualified_name}` must actually hold
  between `_derive_edges` and `_derive_nodes` (§8 decision 6).
- **`briefed` — SAFE ONLY UNDER: the caller-supplied `agent_id` is validated (or resolved from the
  store) BEFORE the fragment is composed, or the operator accepts that a publish with an unknown
  `agent_id` now loses the ENTIRE publish rather than just dangling its ack.** The store side is fine
  — the in-txn `brief` OUT endpoint satisfies `ENFORCED` (leg B control). The risk is not the
  transaction; it is that `briefed`'s IN endpoint is the one caller-supplied identity among the three
  edges being flipped, and its failure now takes the brief with it. **This is exactly the case packet
  04's own text names** (*"`BriefLedger.publish(agent_id: str | None)` — confirmed still a bare
  string"*) and exactly what the packet's ergonomic app-level layer is for: it names every bad id
  BEFORE the write, so the publish is refused with a teaching message instead of being rolled back
  behind an *"unspecified rejection"*.
- **`to` — already flipped, shipped, and now measured sound.** No action. Its leg-D property (one bad
  recipient kills the whole fan-out) is surfaced for the record, not as a defect claim.

### 10.5 What this adds to the decisions in §8

Decision 1 (the app-level check "stays as the ergonomic layer") is **upgraded from ergonomics to a
correctness-adjacent requirement for `briefed` and `send`**: without it, the failure mode a caller
sees is a rolled-back write plus `statement N of M was rejected (unspecified rejection); see the
server log` — which cannot satisfy packet 04's Exit criterion (*"a bogus-recipient publish/send
TEACHES instead of dangling"*). Suggested pins for the builder:

1. `publish` with an unregistered `agent_id` → refused by the app-level check, with the bad id named,
   and the brief **not** written. (Negative fixture must use an id that is absent — a fixture where
   every agent is registered cannot discriminate.)
2. `publish` with a registered `agent_id` → brief written **and** ack edge written (the positive
   control, so pin 1 cannot pass by refusing everything).
3. `send` to `[real, bogus]` → refused before the write; assert **no** message row exists afterwards,
   so the pin distinguishes "refused early" from "rolled back late".

### 10.6 Reference verdict for this section

**§4 is INCOMPLETE, not wrong.** It records that `ENFORCED` reports one bad endpoint as untyped prose
*"only AFTER the write is attempted, aborting the whole txn"* — correct, and this section supplies the
consequence it does not draw: **in a fragment that also CREATEs a row, aborting the txn discards that
row too.** Proposed as a clause on §7 item 9's new §4 line.
