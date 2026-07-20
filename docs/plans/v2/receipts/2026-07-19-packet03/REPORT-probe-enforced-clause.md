# REPORT-probe-enforced-clause

brief-base v4 read

- **state:** done
- **deviations:**
  - Probe 2's guard probes reused ONE `(in, out)` pair across checkpoints, so the UNIQUE index — not `ENFORCED` — decided 2 of 4 controls. Caught, re-run clean as probe2b. Both runs reported verbatim; only probe2b is evidence.
  - Probe 3's UPDATE-door leg was VACUOUS (matched zero rows — the edge had cascaded away one section earlier). Re-run as probe3b with live edges **and** a non-ENFORCED control arm.
  - Added 3 probes beyond the 8 briefed (3b doors, 6 OVERWRITE-safety, 7 untyped-upgrade). Each closed a question a briefed probe opened; flagged individually.
- **decisions-needed:**
  1. **Adopt `ENFORCED` — recommend YES, as a BACKSTOP, keeping the app-level check.** §RECOMMENDATION.
  2. **The reference doc's §4 false absolute is CONFIRMED false** — `ENFORCED` works exactly as the vendor documents. §CONFIRMS/CONTRADICTS.
  3. **⚠ Reference §3's "`_txn.py` raises on `failed_statements[0]` — the first ERR is the root cause by execution order" is FALSE against the current code and against the engine.** The code is right; the doc is stale. §Q7 + §UNASKED-3.
  4. `_define_relation_table` emits `TYPE RELATION` with **no IN/OUT at all** — every shipped relation table is untyped. §UNASKED-5.
- **receipt pointers:** Q1 §Q1 · Q2 §Q2 · Q3 §Q3 · Q4 §Q4 · Q5 §Q5 · Q6 §Q6 · Q7 §Q7 · Q8 §Q8 · extras §UNASKED · scripts in `/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/af347ebc-8215-4484-b5d3-3d94c07f7eaf/scratchpad/enforced-probes/`

Engine: surrealdb 3.1.5 @ `ws://127.0.0.1:18000` (spike-surreal, **TEST**). Production `:18500` never contacted — `_probe.py:26` carries a hard `assert "18000" in URL`. Every probe minted its own `test_<pid>_<uuid4>` database and reaped it (`[reaped …]` receipt at the tail of every run).

---

## SUMMARY OF VERDICTS

| # | Question | Verdict |
|---|---|---|
| 1 | Does `ENFORCED` work on 3.1.5? | **YES — CONFIRMED.** Validates **BOTH** endpoints. `The record 'agent:a_ghost' does not exist` |
| 2 | Migration via `IF NOT EXISTS` | **⚠ SILENT NO-OP — #107's exact shape.** `OVERWRITE` lands, preserves fields/indexes/rows |
| 3 | Pre-existing dangling edges | **Fully intact** — readable, traversable, updatable, deletable. **NOT** write-poisoned |
| 4 | Endpoint-deletion cascade | **Unaffected** — still cascades cleanly, both endpoints, UNIQUE entry cleaned |
| 5 | Composes with `UNIQUE(in,out)` + `SCHEMAFULL` | **YES**, all three enforce independently |
| 6 | Cost | **~2.8% over 3 rounds — inside round-to-round noise.** Negligible |
| 7 | Error ergonomics | Whole txn aborts (all-or-nothing); error **names the bad recipient**; but only ONE per attempt |
| 8 | GitHub #5039 | **Does NOT reproduce on 3.1.5** — the chained edge cascades correctly |

---

## Q1 — Does `ENFORCED` work at all on 3.1.5?

**Script:** `probe1_enforced_basic.py`. Two tables, identical but for the clause, in one DB:

```surql
DEFINE TABLE deliver TYPE RELATION IN message OUT agent ENFORCED;
DEFINE TABLE loose   TYPE RELATION IN message OUT agent;          -- CONTROL table
CREATE message:m_real SET body = 'hello';
CREATE agent:a_real SET name = 'scout';
```

**First: does the clause survive into the STORED definition?** (A parser that accepts and drops a clause looks identical from outside.) `INFO FOR DB`:

```
    deliver: DEFINE TABLE deliver TYPE RELATION IN message OUT agent ENFORCED SCHEMALESS PERMISSIONS NONE
    loose:   DEFINE TABLE loose TYPE RELATION IN message OUT agent SCHEMALESS PERMISSIONS NONE
```

**Four legs, verbatim (endpoints bound as `RecordID`, per §4/§7):**

```
===== TABLE deliver (ENFORCED)
--- LEG: CONTROL both real  (message:m_real -> deliver -> agent:a_real)
    [0] OK: [{'id': RecordID(table_name=deliver, record_id='j60jkyc4fjh2et58afmr'), 'in': RecordID(table_name=message, record_id='m_real'), 'out': RecordID(table_name=agent, record_id='a_real'), 'tag': 'deliver_CONTROL both real'}]
--- LEG: BOGUS OUT  (message:m_real -> deliver -> agent:a_ghost)
    [0] ERR: "The record 'agent:a_ghost' does not exist"
--- LEG: BOGUS IN  (message:m_ghost -> deliver -> agent:a_real)
    [0] ERR: "The record 'message:m_ghost' does not exist"
--- LEG: BOTH BOGUS  (message:m_ghost -> deliver -> agent:a_ghost)
    [0] ERR: "The record 'message:m_ghost' does not exist"
```

**POSITIVE CONTROL: PASSED** — both-real wrote a healthy edge and read back.

**NEGATIVE CONTROL (the `loose` table, same four legs) — all four OK**, three dangling edges written, exactly as §4 records:

```
===== TABLE loose (no clause — CONTROL table)
--- LEG: CONTROL both real  : [0] OK
--- LEG: BOGUS OUT          : [0] OK: [{... 'out': RecordID(table_name=agent, record_id='a_ghost') ...}]
--- LEG: BOGUS IN           : [0] OK: [{... 'in': RecordID(table_name=message, record_id='m_ghost') ...}]
--- LEG: BOTH BOGUS         : [0] OK: [{... 'in': message:m_ghost, 'out': agent:a_ghost ...}]
```

Final row counts: `deliver` = 1 row (the control only). `loose` = 4 rows (3 dangling). **The probe demonstrably sees both outcomes**, so the `deliver` rejections are the clause, not the harness.

**Error shape.** `"The record '<table>:<id>' does not exist"` — a plain string, no structured code, but it **names the offending record id verbatim**. Note the both-bogus leg reports **only `in`**: the engine short-circuits on the first bad endpoint, so a caller learns about ONE bad id per attempt, never the full set.

> **VERDICT Q1: CONFIRMED. `ENFORCED` is real on 3.1.5, is persisted into the stored definition, and validates BOTH `in` and `out`. The vendor is correct — and it closes the caller-supplied `out` half of #105 at the engine.**

---

## Q2 — MIGRATION. ⚠ The one that could bite silently.

**Script:** `probe2b_migration_clean.py` (see §INSTRUMENT DEFECT for why probe2 is superseded).

Setup — the OLD definition, deliberately with its own field and a UNIQUE index, so we can also see what `OVERWRITE` preserves:

```surql
DEFINE TABLE deliver TYPE RELATION IN message OUT agent SCHEMAFULL;   -- no ENFORCED
DEFINE FIELD tag ON deliver TYPE option<string>;
DEFINE INDEX deliver_unique ON deliver FIELDS in, out UNIQUE;
```

A pre-existing dangling edge is then written under that definition, and **every checkpoint uses a FRESH, never-before-used `(in, out)` pair**, so no UNIQUE index entry can ever pre-exist and decide a result.

### Baseline — proving the instrument can see both outcomes

```
--- GUARD PROBE [baseline_no_enforced]  (fresh message pair m1a / m1b)
    positive control (both real, unused pair) : [('OK', [{... 'out': agent:a_real, 'tag': 'good_baseline_no_enforced'}])]
    negative control (ghost out, unused pair) : [('OK', [{... 'out': agent:ghost_1, 'tag': 'bad_baseline_no_enforced'}])]
```

Both OK — no guard is active yet. Correct.

```
--- RELATE m_dangler -> deliver -> agent:permanent_ghost
    [0] OK: [{'id': deliver:9xszeer0s5zo3u0uaddl, 'in': message:m_dangler, 'out': agent:permanent_ghost, 'tag': 'preexisting_ghost'}]

stored def BEFORE migration: DEFINE TABLE deliver TYPE RELATION IN message OUT agent SCHEMAFULL PERMISSIONS NONE
```

### MIGRATION 1 — `DEFINE TABLE IF NOT EXISTS … ENFORCED`

```
--- DEFINE TABLE IF NOT EXISTS deliver ... ENFORCED
    [0] OK: None
stored def AFTER IF NOT EXISTS: DEFINE TABLE deliver TYPE RELATION IN message OUT agent SCHEMAFULL PERMISSIONS NONE
                                                                              ^^^^ NO ENFORCED

--- GUARD PROBE [after_IF_NOT_EXISTS]  (fresh message pair m2a / m2b)
    positive control (both real, unused pair) : [('OK', ...)]
    negative control (ghost out, unused pair) : [('OK', [{... 'out': agent:ghost_2, 'tag': 'bad_after_IF_NOT_EXISTS'}])]
```

**The DDL returns `OK`. The stored definition is UNCHANGED. A ghost RELATE still succeeds and writes a dangling edge.** Two independent instruments agree (the stored definition text and a live negative control), so this is not an introspection artifact.

**This is #107 verbatim, and the brief's fear is exactly right — it is WORSE than #107 in one specific way:** on a **fresh** database the table does not exist, so `IF NOT EXISTS` creates it **with** `ENFORCED` and every test passes. §1.6's blind spot, unmodified: *every test mints a virgin DB*, so a green suite would prove the guard works while **no long-lived store ever gained it**.

### MIGRATION 2 — `DEFINE TABLE OVERWRITE … ENFORCED`

Applied while the table still holds the dangling edge:

```
--- DEFINE TABLE OVERWRITE deliver ... ENFORCED
    [0] OK: None
stored def AFTER OVERWRITE: DEFINE TABLE deliver TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL PERMISSIONS NONE

--- GUARD PROBE [after_OVERWRITE]  (fresh message pair m3a / m3b)
    positive control (both real, unused pair) : [('OK', [{... 'tag': 'good_after_OVERWRITE'}])]
    negative control (ghost out, unused pair) : [('ERR', "The record 'agent:ghost_3' does not exist")]
```

**`OVERWRITE` lands. The guard goes live.** Positive control still passes on the same checkpoint, so the arm is not simply rejecting everything.

**Does it reject or re-validate the EXISTING dangling edges?** **NEITHER — the DDL applies cleanly and every dangling row survives untouched:**

```
--- SELECT FROM deliver
    [{'in': message:m2b,       'out': agent:ghost_2,        'tag': 'bad_after_IF_NOT_EXISTS'},
     {'in': message:m1b,       'out': agent:ghost_1,        'tag': 'bad_baseline_no_enforced'},
     {'in': message:m2a,       'out': agent:a_real,         'tag': 'good_after_IF_NOT_EXISTS'},
     {'in': message:m3a,       'out': agent:a_real,         'tag': 'good_after_OVERWRITE'},
     {'in': message:m1a,       'out': agent:a_real,         'tag': 'good_baseline_no_enforced'},
     {'in': message:m_dangler, 'out': agent:permanent_ghost,'tag': 'preexisting_ghost'}]
```

Three dangling edges, all still there. **`ENFORCED` is a write-path guard only — there is no retro-validation**, exactly as §1.4 records for narrowed ASSERTs.

**Fields, indexes and rows all preserved by `OVERWRITE`:**

```
--- INFO FOR TABLE deliver
    {'fields': {'in':  'DEFINE FIELD in ON deliver TYPE record<message> PERMISSIONS FULL',
                'out': 'DEFINE FIELD out ON deliver TYPE record<agent> PERMISSIONS FULL',
                'tag': 'DEFINE FIELD tag ON deliver TYPE none | string PERMISSIONS FULL'},
     'indexes': {'deliver_unique': 'DEFINE INDEX deliver_unique ON deliver FIELDS in, out UNIQUE'}, ...}

--- duplicate RELATE m3a -> a_real
    [0] ERR: 'Database index `deliver_unique` already contains [message:m3a, agent:a_real], with record `deliver:9t6iar5w2no2exex7kkw`'
```

The duplicate rejection is the control proving the index is still **enforcing**, not merely still **defined**.

> **VERDICT Q2: `IF NOT EXISTS` is a SILENT NO-OP for `ENFORCED` — confirmed, #107's exact shape, invisible to every existing test by construction. `OVERWRITE` is the only clause that lands it; it preserves fields, indexes and rows, and it neither rejects nor re-validates existing dangling edges.**

**What a correct migration must be:**

```surql
DEFINE TABLE OVERWRITE <edge> TYPE RELATION IN <a> OUT <b> ENFORCED SCHEMAFULL;
```

…plus a **separate data migration** for the ghosts already stored — the DDL will not find them and no error will ever mention them. And per §1.6's pinned invariant (`TestSchemaMigrationAgainstAnExistingStore`), the migration needs a test of the shape *apply OLD DDL → write a dangling edge → apply NEW DDL → assert the guard is live AND the old row survived*. A fresh-DB test cannot see this defect.

---

## Q3 — Pre-existing dangling edges under a live `ENFORCED`

Same run, after `OVERWRITE` made the guard live. The `preexisting_ghost` edge points at `agent:permanent_ghost`, which has never existed.

```
--- READ (projection through the ghost)
    [0] OK: [{'in': message:m_dangler, 'out': agent:permanent_ghost, 'out_name': None, 'tag': 'preexisting_ghost'}]

--- TRAVERSE ->deliver->agent from its message
    [0] OK: [{'recipients': [RecordID(table_name=agent, record_id='permanent_ghost')]}]

--- UPDATE an UNRELATED column on the ghost edge (write-poisoning?)
    [0] OK: [{'id': deliver:9xszeer0s5zo3u0uaddl, 'in': message:m_dangler, 'out': agent:permanent_ghost, 'tag': 'touched'}]

--- DELETE the ghost edge
    [0] OK: [{'id': deliver:9xszeer0s5zo3u0uaddl, ... 'tag': 'touched'}]
```

- **Still readable** — and the ghost is still only detectable by projecting a field and getting `None` (§2's silent-`None` trap, §4's ghost-in-traversal receipt). `ENFORCED` changes nothing about detection.
- **Still traversable** — `->deliver->agent` lists `agent:permanent_ghost` as a first-class recipient.
- **NOT write-poisoned.** An `UPDATE` of an unrelated column succeeds. This differs from §1.4's narrowed-ASSERT/TYPE-change behaviour, and the difference is worth stating: `ENFORCED` is enforced **at RELATE**, not at record validation, so it does not participate in the whole-record re-validation that poisons rows on a narrowed ASSERT.
- **Still deletable** — a cleanup migration is unobstructed.

> **VERDICT Q3: pre-existing ghosts are entirely unaffected — readable, traversable, updatable, deletable. `ENFORCED` neither hides them, breaks them, nor helps you find them. Cleanup is a separate data migration, and it is not blocked by the guard.**

⚠ **The practical consequence:** turning `ENFORCED` on gives a **false sense of completion**. New ghosts become impossible; every old ghost keeps serving as a delivery receipt for an agent that does not exist, silently, forever.

**Contrast — the wrong-TABLE case IS poisoned** (probe7, §UNASKED-5): a row whose `out` is of the wrong table fails on its next UPDATE with `Couldn't coerce value for field 'out' … Expected 'record<agent>' but found 'intruder:x'`, while a well-typed row in the same statement updates fine. So `IN/OUT` typing poisons; `ENFORCED` does not.

---

## Q4 — Does `ENFORCED` interact with the endpoint-deletion cascade?

**Script:** `probe3_cascade_and_doors.py`, on `deliver TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL` + `UNIQUE(in, out)`.

```
--- edges before
    [0] OK: [{'in': message:m1, 'out': agent:a1, 'tag': 'first'}]
--- DELETE agent:a1 (the OUT endpoint of a live edge)
    [0] OK: []
--- edges after the OUT delete
    [0] OK: []
--- agents after
    [0] OK: [{'id': RecordID(table_name=agent, record_id='a2')}]
```

The DELETE **succeeds** and the edge cascades away. `ENFORCED` does not make the delete fail.

UNIQUE index entry cleaned — re-RELATE the same pair after recreating the endpoint:

```
--- re-RELATE the SAME pair after recreating a1 (UNIQUE entry cleaned?)
    [0] OK: [{'id': agent:a1, 'name': 'scout again'}]
--- RELATE m1->deliver->a1 (post-cascade)
    [0] OK: [{'id': deliver:1op1tf5gs9vxjs6hb7iu, 'in': message:m1, 'out': agent:a1, 'tag': 'reborn'}]
```

And the `in` side:

```
--- DELETE message:m1 (the IN endpoint)
    [0] OK: []
--- edges after the IN delete
    [0] OK: []
```

> **VERDICT Q4: unchanged. The cascade works exactly as the prior probe settled — both endpoints, edge removed, UNIQUE entry cleaned, re-RELATE succeeds. `ENFORCED` does not block or complicate endpoint deletion.**

Note the asymmetry this creates, which is inherent and not a defect: **`ENFORCED` forbids CREATING an edge to a non-existent record, but the engine will happily DESTROY the edge for you when the record goes away.** The invariant is maintained by cascade, not by refusal.

---

## Q5 — Composition with `UNIQUE(in,out)` and a `SCHEMAFULL` relation

Same table, all three constraints live. Five legs (`probe3_cascade_and_doors.py`):

```
--- RELATE m1->deliver->a1 SET tag='first'  (positive control)
    [0] OK: [{'id': deliver:mwn4ly5mneh3d3o1k0qo, 'in': message:m1, 'out': agent:a1, 'tag': 'first'}]
--- RELATE m1->deliver->a1 again  (UNIQUE must reject)
    [0] ERR: 'Database index `deliver_unique` already contains [message:m1, agent:a1], with record `deliver:mwn4ly5mneh3d3o1k0qo`'
--- RELATE m1->deliver->a_ghost  (ENFORCED must reject)
    [0] ERR: "The record 'agent:a_ghost' does not exist"
--- RELATE m1->deliver->a1 SET tag = 42  (SCHEMAFULL type must reject)
    [0] ERR: "Couldn't coerce value for field `tag` of `deliver:ur5f8e708bj8k9uha37j`: Expected `none | string` but found `42`"
--- RELATE m1->deliver->a1 SET nope = 'x'  (SCHEMAFULL undeclared field)
    [0] ERR: "Found field 'nope', but no such field exists for table 'deliver'"
```

Four distinct rejections with four distinct messages, plus a passing positive control. Each constraint fires **for its own reason** — no masking, no interference.

> **VERDICT Q5: YES. `ENFORCED` + `UNIQUE(in,out)` + `SCHEMAFULL` fields compose cleanly and are individually distinguishable by error text.**

⚠ Keep §4's existing caution: because `UNIQUE(in,out)` makes a repeated recipient a **loud ERR**, a fan-out must still dedupe before the RELATE loop. `ENFORCED` does not change that.

---

## Q6 — Cost

**Script:** `probe5_cost.py`. Shape mirrors the real send: **16 workers × 20 transactions**, each transaction `CREATE message` + N `RELATE` (N cycles 5–10) inside ONE `BEGIN/COMMIT`. Both arms are identical tables in the SAME database. **Arm order alternates per round** so cold-start cost cannot be attributed to the clause.

```
shape: 16 workers x 20 txns, [5, 6, 7, 8, 9, 10] recipients cycling, one BEGIN/COMMIT per txn

--- round 1 (order: enforced_edge first)
    enforced_edge     0.266s   2336 edges     113.7 us/edge
    loose_edge        0.282s   2336 edges     120.6 us/edge
--- round 2 (order: loose_edge first)
    loose_edge        0.253s   2336 edges     108.3 us/edge
    enforced_edge     0.296s   2336 edges     126.7 us/edge
--- round 3 (order: enforced_edge first)
    enforced_edge     0.273s   2336 edges     117.0 us/edge
    loose_edge        0.277s   2336 edges     118.6 us/edge

--- totals over 3 rounds
    enforced_edge     0.835s
    loose_edge        0.812s
    ENFORCED / loose = 1.028x

--- CONTROL: row counts must match (a fast arm that wrote nothing is not fast)
    enforced_edge: [('OK', [{'count': 7008}])]
    loose_edge:    [('OK', [{'count': 7008}])]
```

Every transaction's full per-statement envelope was checked (`AssertionError` on any non-OK), so a silently-failing fast arm was impossible; the equal final counts are the second, independent control.

**In round 1 the ENFORCED arm was FASTER than the control.** The 2.8% total is smaller than the between-round spread of either arm.

> **VERDICT Q6: no measurable cost. ~2.8% aggregate, inside run-to-run noise, at 16-way × 20 with 5–10 recipients. Cost is not an argument against adoption.**

---

## Q7 — Error ergonomics (the one that decides whether the app check survives)

**Script:** `probe4_ergonomics.py`. Fan-out of 5 recipients, one bogus.

### Control — 4 good recipients, one transaction

```
--- BEGIN; 4x RELATE; COMMIT;
    [0] OK: None
    [1] OK: [{... 'out': agent:a1, 'slot': 0}]
    [2] OK: [{... 'out': agent:a2, 'slot': 1}]
    [3] OK: [{... 'out': agent:a3, 'slot': 2}]
    [4] OK: [{... 'out': agent:a4, 'slot': 3}]
    [5] OK: None
```

### Shape A — 5 recipients, bogus at position 3 (`['a1','a2','typo_agent','a3','a4']`), one transaction

```
--- per-statement envelope (query_raw, nothing filtered):
    [0] OK: None
    [1] ERR: 'The query was not executed due to a failed transaction'
    [2] ERR: 'The query was not executed due to a failed transaction'
    [3] ERR: "The record 'agent:typo_agent' does not exist"
    [4] ERR: 'The query was not executed due to a cancelled transaction'
    [5] ERR: 'The query was not executed due to a cancelled transaction'
    [6] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'
--- rows AFTER the failed fan-out (all-or-nothing?)
    [0] OK: []
```

**All-or-nothing: zero rows written.** No partial fan-out. For packet 03 that is arguably the desired semantics — a message is delivered to all its recipients or to none — but it must be a *chosen* semantic, not an inherited one.

**⚠ Note the envelope shape.** The real cause is at index **3**. Indices 1–2 — statements that would have run BEFORE the offender — are stamped `'was not executed due to a failed transaction'`. **`failed_statements[0]` is a cascade notice, not the root cause.** See §UNASKED-3: the repo's `_txn.py` already handles this correctly; the reference doc does not.

### Shape B — bogus FIRST

```
    [0] OK: None
    [1] ERR: "The record 'agent:typo_agent' does not exist"
    [2..5] ERR: 'The query was not executed due to a cancelled transaction'
    [6] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'
```

Position of the substantive error moves with the offender — confirming a positional classifier is wrong in general, and that a **semantic** (marker-seeking) selector is required.

### Shape C — NO transaction, five RELATEs in one send

```
    [0] OK: [{... 'out': agent:a1, 'slot': 0}]
    [1] OK: [{... 'out': agent:a2, 'slot': 1}]
    [2] ERR: "The record 'agent:typo_agent' does not exist"
    [3] OK: [{... 'out': agent:a3, 'slot': 3}]
    [4] OK: [{... 'out': agent:a4, 'slot': 4}]
--- rows after C
    [{'out': agent:a1, 'slot': 0}, {'out': agent:a2, 'slot': 1}, {'out': agent:a3, 'slot': 3}, {'out': agent:a4, 'slot': 4}]
```

**A PARTIAL fan-out — 4 of 5 delivered, one silently missing.** Without `BEGIN/COMMIT` the message is delivered to a subset with no aggregate signal.

### Shape C′/C″ — what the SDK's plain `.query()` says about all this

```
########## C' — what the SDK's plain .query() reports for shape C
    query() RETURNED (no exception): [{'id': deliver:agimd7hy6e0wm2zui848, ... 'slot': 0}]

########## C'' — and what .query() reports for shape A (BEGIN at index 0)
    query() RETURNED (no exception): None
```

**A totally-failed 5-recipient fan-out returns `None` from `query()` and raises nothing.** §3's rule, reproduced live in exactly the shape packet 03 will write. `execute_transaction` is mandatory here, not stylistic.

### What the application can actually tell the caller

- **WHICH recipient was bad: YES** — `"The record 'agent:typo_agent' does not exist"` names the id verbatim.
- **How many were bad: NO** — the engine short-circuits at the first offender (Q1's both-bogus leg is the same behaviour). A send with three typos surfaces one, and the caller fixes-and-retries three times.
- **A typed error: NO** — a bare string. Naming the recipient means substring-parsing the engine's prose, which is precisely the kind of literal-keyed instrument the repo's "six defeats, one shape" table warns about. **The engine's message is a diagnostic, not an API.**

> **VERDICT Q7: `ENFORCED` gives a clean all-or-nothing abort that NAMES the bad recipient, but only ONE per attempt, only as untyped prose, and only after the write has been attempted. It does NOT make the application-level check redundant.**

---

## Q8 — GitHub issue #5039

**Determined, not guessed.** Fetched the issue: tables `user -> messaged* -> attached* -> image`, where **both `messaged` and `attached` are relation tables** (so `attached`'s `IN` endpoint is an EDGE record). Reported against **2.0.3 / macOS x86_64**. Reporter's complaint: *"deleting a `messaged` record doesn't delete the connected `attached` record"*; expected: *"deleting a `messaged` record should trigger deletion of the linked `attached` record since the `in` field on that record is now `NONE`"*. **Status: closed.**

Reproduced on 3.1.5 (`probe3_cascade_and_doors.py`, final section), with `ENFORCED` on **both** relation tables:

```
--- DDL DEFINE TABLE messaged TYPE RELATION IN user OUT user ENFORCED SCHEMALESS;
    [0] OK: None
--- DDL DEFINE TABLE attached TYPE RELATION IN messaged OUT image ENFORCED SCHEMALESS;
    [0] OK: None

--- RELATE alice->messaged->bob (capture the edge id)
    [1] OK: RecordID(table_name=messaged, record_id='s5beo0iz6rfg862ygtqz')

--- RELATE $messaged_edge->attached->image:pic  (an EDGE as the IN endpoint)
    [0] OK: [{'id': attached:inhncg71kwegg4x6s8r8, 'in': messaged:s5beo0iz6rfg862ygtqz, 'note': 'chained', 'out': image:pic}]
--- attached rows
    [0] OK: [{'id': attached:inhncg71kwegg4x6s8r8, 'in': messaged:s5beo0iz6rfg862ygtqz, 'note': 'chained', 'out': image:pic}]

--- DELETE the messaged edge record
    [0] OK: []
--- messaged rows after delete
    [0] OK: []
--- attached rows after delete — #5039 says this row SURVIVES with a dangling in
    [0] OK: []
```

Positive control embedded: the `attached` row is shown **present** immediately before the delete, so the empty result afterwards is a cascade, not a row that never existed.

> **VERDICT Q8: #5039 does NOT reproduce on 3.1.5. Deleting the intermediate edge record cascades the dependent edge away correctly. An `ENFORCED` relation whose `IN` endpoint is itself a relation table works. The closure is genuine.**

Two honest bounds: (a) I reproduced the shape the issue *describes*; the issue body carries no runnable script, so an exact-fidelity claim is not available; (b) the reporter's phrasing conflates the cascade with `ENFORCED`, and my run shows the cascade is correct **with** `ENFORCED` on — I did not additionally test the chained shape *without* it.

---

## UNASKED — things I found that you did not ask for

### UNASKED-1 ⭐ `INSERT RELATION` is a dangling-edge door that §4 does not record — and `ENFORCED` closes it

`probe3b_doors_rerun.py` runs every write verb against an ENFORCED table and an otherwise-identical non-ENFORCED control, so we can tell **which clause** closes each door.

| Verb, ghost `out` | on `enforced_edge` | on `loose_edge` (CONTROL) | closed by |
|---|---|---|---|
| `CREATE … CONTENT {in,out}` | ERR *"not a relation"* | ERR *"not a relation"* | **TYPE RELATION** |
| `INSERT INTO …` | ERR *"not a relation"* | ERR *"not a relation"* | **TYPE RELATION** |
| `UPSERT <id> SET in,out` | ERR *"not a relation"* | ERR *"not a relation"* | **TYPE RELATION** |
| **`INSERT RELATION INTO …`** | **ERR "The record … does not exist"** | **OK — dangling edge WRITTEN** | **⭐ ENFORCED** |

```
--- INSERT RELATION INTO   (enforced_edge)
    [0] ERR: "The record 'agent:ghost_insert_rel' does not exist"
--- INSERT RELATION INTO   (loose_edge)
    [0] OK: [{'id': loose_edge:tym8m1o2g8kp2zt3swln, 'in': message:m2, 'out': agent:ghost_insert_rel, 'tag': 'door_insert_rel'}]
```

Controls with both endpoints REAL prove the verb is legal on both tables (`INSERT RELATION … OK` on each), so the ENFORCED rejection is the clause and not the verb.

**§4 currently frames dangling edges as a `RELATE` hazard. `INSERT RELATION` is a second door with the same consequence**, and it is the one `ENFORCED` — and *only* `ENFORCED` — shuts. Worth adding to §4 whether or not `ENFORCED` is adopted.

### UNASKED-2 ⚠ `UPDATE` of a relation edge's `in`/`out` is a SILENT NO-OP

On **both** arms, and even when the new endpoint is a **real, existing** record:

```
--- UPDATE deliver SET out = agent:a2  (a REAL, existing agent)
    [0] OK: [{'id': deliver:ejtbybudwcagdefbzc70, 'in': message:m1, 'out': agent:a1, 'slot': 0}]
--- rows after
    [0] OK: [{'in': message:m1, 'out': agent:a1, 'slot': 0}]
```

`OK` status, a returned record, **and `out` is unchanged**. Not a rejection — a silent no-op. Any future "rewire this delivery to a different agent" operation written as an `UPDATE` will report success and do **nothing**. This is a §2-class DML gotcha (silent degradation, not a loud failure) and belongs in the reference regardless of the `ENFORCED` decision. It is also good news for the guard: the endpoints are effectively immutable post-RELATE, so `ENFORCED` cannot be walked around via `UPDATE`.

### UNASKED-3 ⚠⚠ Reference §3's root-cause rule is FALSE — the doc, not the code

§3 states: *"`_txn.py` now raises on `failed_statements[0]` — the first ERR is the root cause by execution order."*

**Both halves are wrong.** Q7 shape A shows the engine stamps cascade notices on statements BEFORE the offender, so `[0]` is `'The query was not executed due to a failed transaction'`, not the cause.

**The code is already right and knows it** — `loremaster/store/_txn.py:416` defines `_CASCADE_NOT_EXECUTED_MARKER = "was not executed due to"`, and `_domain_root_cause` (:714) selects the first **non-cascade** entry, with a docstring that says explicitly:

> *"Selecting by POSITION is refused outright, at both ends … neither `[0]` nor `[-1]` is correct for any shape here; only a SEMANTIC (marker-seeking) selector is."*

So this is **stale doc prose teaching a retired mechanism** — precisely the class §8's last bullet already flags for `surreal_schema.py:873`, and precisely the class the CLAUDE.md rename-sweep law says no gate will ever catch. My probe independently reproduced the engine behaviour the code was fixed for, which is a live re-confirmation of the fix; only the doc lies. **Report-only — I did not edit the reference (docs are outside my write-set).**

### UNASKED-4 `DEFINE TABLE OVERWRITE` does NOT rebuild indexes — the flip is safe

Adopting `ENFORCED` on an existing table means `OVERWRITE`, which brushes against §1.5's warning that `DEFINE INDEX OVERWRITE` **rebuilds** over every row (a boot-time crash on a dim change). If `DEFINE TABLE OVERWRITE` did the same, flipping `_define_table` would re-index `chunk`'s HNSW on every boot.

`probe6_overwrite_safety.py` — a populated table carrying **both** an HNSW vector index and a UNIQUE index:

```
--- KNN BEFORE (positive control)
    [0] OK: [{'slug': 'doc-0'}, {'slug': 'doc-6'}, {'slug': 'doc-2'}]
--- duplicate slug BEFORE (UNIQUE control — must ERR)
    [0] ERR: "Database index `doc_slug` already contains 'doc-0', with record `doc:c1tlwgi9ewo05ze561p0`"

########## DEFINE TABLE OVERWRITE on the populated, indexed table
--- DEFINE TABLE OVERWRITE doc SCHEMAFULL
    [0] OK: None
    elapsed: 0.0017s

--- row count AFTER          : [{'count': 8}]
--- KNN AFTER                : [{'slug': 'doc-0'}, {'slug': 'doc-6'}, {'slug': 'doc-2'}]
--- duplicate slug AFTER     : ERR "Database index `doc_slug` already contains 'doc-0' …"
```

HNSW definition preserved verbatim (`… HNSW DIMENSION 8 DIST EUCLIDEAN TYPE F32 EFC 150 M 12 M0 24 …`), KNN identical, UNIQUE still enforcing, **1.7 ms**.

**Positive control that the probe can detect a rebuild** — the same table, `DEFINE INDEX OVERWRITE` with a changed dim:

```
########## CONTRAST: DEFINE INDEX OVERWRITE with a CHANGED dim (§1.5's crash)
    [('ERR', 'Incorrect vector dimension (8). Expected a vector of 16 dimension.')]
```

§1.5's failure mode reproduces on demand, which proves the clean `DEFINE TABLE OVERWRITE` result is a real negative and not a blind instrument.

**This corroborates §6.2's row** (*"Is `DEFINE TABLE OVERWRITE` safe on a populated table? Yes — fields, indexes and rows all preserved"*) and extends it: **safe even with an HNSW index present, and it does not rebuild.**

### UNASKED-5 ⚠ Every shipped relation table is UNTYPED

`loremaster/store/surreal_schema.py:615` — `_define_relation_table`:

```python
return f"DEFINE TABLE IF NOT EXISTS {name} TYPE RELATION SCHEMAFULL"
```

**No `IN`, no `OUT`.** So `briefed`, `refers` et al. currently get neither endpoint typing nor any prospect of `ENFORCED`. Adopting `ENFORCED` on an *existing* edge is therefore a **two-constraint** migration, which probe7 measures:

```
stored def (repo's current shape): DEFINE TABLE deliver TYPE RELATION SCHEMALESS PERMISSIONS NONE

--- RELATE m1->deliver->intruder:x (WRONG out table — untyped permits it)
    [0] OK: [{... 'out': intruder:x, 'tag': 'wrongtable'}]

--- DEFINE TABLE OVERWRITE deliver TYPE RELATION IN message OUT agent ENFORCED
    [0] OK: None
stored def AFTER: DEFINE TABLE deliver TYPE RELATION IN message OUT agent ENFORCED SCHEMALESS PERMISSIONS NONE
--- rows survived? : both rows still present, including the wrong-table one

--- positive control: RELATE m2->deliver->a1        : [0] OK
--- negative control: RELATE m2->deliver->agent:ghost: [0] ERR "The record 'agent:ghost' does not exist"

--- B: is the WRONG-TABLE row now write-poisoned (§1.4)?
--- UPDATE deliver SET tag='touched' WHERE tag='wrongtable'
    [0] ERR: "Couldn't coerce value for field `out` of `deliver:diz2jpr6qy5zse07v1c4`: Expected `record<agent>` but found `intruder:x`"
--- and the well-typed row, for contrast
    [0] OK: [{... 'tag': 'touched_ok'}]
```

**The migration succeeds and preserves rows, but any pre-existing WRONG-TABLE row becomes write-poisoned** — §1.4's exact pattern, with the well-typed row updating fine in the same run as the discriminating control. For packet 03's brand-new table this is moot; for retrofitting `briefed`/`refers` it is a required pre-flight audit.

---

## INSTRUMENT DEFECT (disclosed — probe2 is superseded by probe2b)

`probe2_migration.py` reused ONE `(in, out)` pair across every checkpoint. Two of four controls therefore fired on the **UNIQUE index**, not on `ENFORCED`:

```
--- GUARD PROBE [after_INE]
    negative control (ghost out) : [('ERR', 'Database index `deliver_unique` already contains [message:m_real, agent:a_ghost], with record `deliver:j34bhzz6g19hzqox97ug`')]
--- GUARD PROBE [after_OVERWRITE]
    positive control (both real) : [('ERR', 'Database index `deliver_unique` already contains [message:m_real, agent:a_real], with record `deliver:xalk361ryk5g7luddv8y`')]
```

The verdict survives — the `after_INE` rejection is an **index** error, not an existence error, so it never claimed ENFORCED was live — but a probe whose controls fire for the wrong reason is not evidence, and **a failing positive control is a stop**. probe2b re-ran every checkpoint on a fresh never-used pair. All Q2/Q3 claims above cite probe2b only.

Likewise `probe3`'s UPDATE-door leg returned `OK` against **zero matching rows** (the edge had cascaded away in the section above) — a vacuous pass reported as a door being open. probe3b re-ran it with a verified-live edge and a control arm. Two instrument defects in one session, both caught by controls; the brief's insistence on them is carrying its weight.

---

## RECOMMENDATION

**ADOPT `ENFORCED` — as a BACKSTOP, not a replacement. Keep the application-level recipient check.**

**Why adopt:**
1. It **works**, on our floor, validating **both** endpoints (Q1) — the guard we told ourselves the engine did not have.
2. It costs **nothing measurable** (Q6, 2.8% inside noise).
3. It composes with everything we already ship — `UNIQUE(in,out)`, `SCHEMAFULL`, the cascade (Q4, Q5).
4. It closes a door the app check **cannot**: `INSERT RELATION` (UNASKED-1). An app check guards the code path it sits on; `ENFORCED` guards the **table**, including every future write path nobody has written yet.
5. Packages-over-hand-rolling, straightforwardly: the engine ships a declarative constraint, so we do not carry a hand-rolled one *alone*.

**Why it does NOT replace the application check** — three independent reasons, each measured:
1. **Ergonomics (Q7):** an untyped prose string, one bad recipient per attempt, surfaced only after the write is attempted and the transaction aborted. The seam needs a typed error naming *every* bad recipient *before* the write. Parsing `"The record 'x:y' does not exist"` to recover the id would be a literal-keyed instrument of exactly the kind the repo's six-defeats table exists to forbid.
2. **It is a WRITE-path guard only (Q3):** it does not find, fix, or flag the ghosts already stored. Turning it on and calling #105 closed would be a false all-clear.
3. **Defence in depth against the migration hazard itself (Q2):** if the DDL ever silently fails to land — which is exactly what `IF NOT EXISTS` does — the app check is the only thing still standing, and nothing would tell you.

**So the shape is:** app check produces the typed, actionable, all-recipients-at-once error at the seam; `ENFORCED` is the engine-level invariant that no dangling edge can be written by *any* path. Neither is redundant.

### The migration adopting it requires on an existing production store

For **packet 03's new `to` edge** — greenfield, so `IF NOT EXISTS` would in fact land today (the table exists nowhere). **Do not rely on that.** The clause becomes a silent trap the first time anyone edits it, and the fresh-DB path will pass every test while no live store migrates. Ship it as:

```surql
DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL;
```

For **relation tables generally**, three steps:

1. **Flip relation tables to `OVERWRITE`** in `surreal_schema._define_relation_table`, and give it real `IN`/`OUT` parameters (today it emits neither — UNASKED-5). Safe: `DEFINE TABLE OVERWRITE` preserves fields, indexes and rows and does **not** rebuild indexes, verified with an HNSW positive control (UNASKED-4). This does **not** contradict §1.5 — that warning is about `DEFINE INDEX OVERWRITE`, which I reproduced crashing on demand as the control.
2. **Pre-flight audit before retrofitting any POPULATED edge** (`briefed`, `refers`): existing rows with a wrong-**table** endpoint become **write-poisoned** by the `IN`/`OUT` typing (UNASKED-5, §1.4's pattern). Existing **ghost** rows do not poison — but they also do not go away (Q3), so they need their own cleanup pass. Neither is reported by the DDL.
3. **Pin the migration against a DIRTY store**, per §1.6's `TestSchemaMigrationAgainstAnExistingStore`: apply OLD DDL → write a dangling edge → apply NEW DDL → assert the guard is LIVE **and** the old row survived. Without this the suite proves nothing: a virgin-DB fixture guarantees the one condition under which the no-op is invisible.

**Suggested §1.1 row:** **RELATION TABLE → `OVERWRITE`** — *"the only clause that lands a changed `IN`/`OUT`/`ENFORCED`; `IF NOT EXISTS` is a silent no-op on an existing edge table (probed). Safe: preserves fields, indexes, rows; does not rebuild."*

---

## CONFIRMS / CONTRADICTS THE VENDOR

| Q | Vendor claim | Verdict |
|---|---|---|
| 1 | *"the `ENFORCED` clause … disallow a `RELATE` statement from working unless it points to existing data"* | **CONFIRMED, verbatim.** Including the error text shape (`The record 'city:one' does not exist` ≙ our `The record 'agent:a_ghost' does not exist`) |
| 1 | BNF `TYPE … RELATION [IN] @table [OUT] @table [ENFORCED]` | **CONFIRMED** — parses, persists into the stored definition, survives `INFO FOR DB` |
| 1 | Docs are silent on **which** endpoint is checked (their example fails on `in`) | **EXTENDED — BOTH are checked.** A vendor SILENCE we filled, not a lie. The engine short-circuits on the first bad endpoint, which is plausibly why the docs only ever show `in` |
| 2 | Docs are **silent** on adding `ENFORCED` to an existing table | **GAP FILLED, and it is the dangerous one.** `IF NOT EXISTS` = silent no-op; `OVERWRITE` required. Consistent with §6.1's established `IF NOT EXISTS` behaviour — a second instance of the same lie's *shape*, on a different clause |
| 3 | Silent on existing rows | **GAP FILLED** — no retro-validation, no poisoning, ghosts fully intact |
| 4 | Silent on cascade × ENFORCED | **GAP FILLED** — no interaction; cascade unaffected |
| 8 | Issue #5039 CLOSED against 2.0.3 | **CONFIRMED FIXED on 3.1.5** — chained relation cascades correctly |
| — | §4's *"an application-level existence check remains the only guard against a ghost"* (**ours**) | **CONTRADICTED — our doc is the wrong one.** §6.3-class defect, exactly as the reconcile report predicted |
| — | §3's *"`_txn.py` raises on `failed_statements[0]` — the first ERR is the root cause by execution order"* (**ours**) | **CONTRADICTED by the engine AND by our own code.** The code is right; the prose is stale (UNASKED-3) |

**No vendor sentence about `ENFORCED` was found to be false.** Given §6.1, that is a result worth stating plainly rather than assuming: this time the docs held, and the thing that nearly bit us was the vendor's **silence** on migration — filled here before it cost anything, rather than after (#107).

---

## FILES

Probe scripts (write-set), all under
`/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/af347ebc-8215-4484-b5d3-3d94c07f7eaf/scratchpad/enforced-probes/`:

| Script | Question |
|---|---|
| `_probe.py` | shared scaffolding (copied from the pkt03 probes; hard test-store assert at :26) |
| `probe1_enforced_basic.py` | Q1 — does it work, both endpoints, + non-ENFORCED control table |
| `probe2_migration.py` | Q2/Q3 — **SUPERSEDED**, instrument defect disclosed above |
| `probe2b_migration_clean.py` | Q2/Q3 — clean re-run, fresh pair per checkpoint |
| `probe3_cascade_and_doors.py` | Q4, Q5, Q8, first doors pass |
| `probe3b_doors_rerun.py` | doors re-run: live edges + non-ENFORCED control arm |
| `probe4_ergonomics.py` | Q7 — fan-out shapes A/B/C/C′/C″ + the UPDATE no-op |
| `probe5_cost.py` | Q6 — 16×20, alternating arm order, 3 rounds |
| `probe6_overwrite_safety.py` | UNASKED-4 — does TABLE OVERWRITE rebuild indexes? |
| `probe7_untyped_upgrade.py` | UNASKED-5 — untyped→typed+ENFORCED on a populated edge |

No repo source or test file was touched. No git state was mutated.
