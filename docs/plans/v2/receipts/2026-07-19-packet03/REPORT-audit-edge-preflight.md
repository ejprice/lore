# REPORT-audit-edge-preflight

brief-base v4 read

- **state:** done
- **deviations:**
  - Audited **BOTH** production databases, not one. `INFO FOR NS` showed the namespace `lore` holds
    `lore` **and** `demand_intelligence` — both are served by the same schema code, so the flip hits
    both. Auditing only the one I was pointed at would have covered ~half the rows. §PROD-IDENTITY.
  - My first `TYPE ANY`-edge detector **false-positived on `name`** (18 476 rows). It keyed on
    key-presence in a SCHEMALESS `SELECT`, which returns `None` for an ABSENT key — reference §2's
    silent-`None` trap, in my own instrument. Re-derived by COUNT. §INSTRUMENT-DEFECT.
- **decisions-needed:**
  1. **The flip is SAFE — zero poisoning, zero ghosts, across both databases and all 101 448 edge
     rows.** All three edge tables are perfectly homogeneous. §VERDICTS.
  2. `message` / `to` do **NOT** exist in either production database — packet 03 is genuinely
     greenfield. §Q5.
  3. ⚠ **`name` is `TYPE ANY` by OMISSION, not design** (`_define_schemaless_table` emits no `TYPE`
     clause). It is an open door for a stray `RELATE` to silently auto-create an edge on a node
     table. Currently clean. Recommend `TYPE NORMAL`. §UNASKED-1.
  4. ⚠ The `OVERWRITE`-is-cheap evidence was measured on an **8-row** table; production carries
     **101 448** edge rows. Not a blocker — an honest bound. §UNASKED-3.
- **receipt pointers:** identity §PROD-IDENTITY · per-table data §PER-TABLE · verdicts §VERDICTS ·
  risk §RISK-STATEMENT · every statement §STATEMENTS · controls §CONTROLS · extras §UNASKED ·
  raw output `/tmp/claude-1000/edge-preflight/{out-lore.txt,out-di.txt}`

---

## PROD-IDENTITY — what I actually read

| | |
|---|---|
| URL | `ws://127.0.0.1:18500/rpc` — **`lore-surreal`, PRODUCTION** (reference §9) |
| Namespace | `lore` (from `lore.yaml:38` `surreal.namespace`) |
| Databases audited | **`lore`** and **`demand_intelligence`** |
| Credentials | `SURREAL_USER` / `SURREAL_PASS` from `~/docker/mcp/lore-secrets/lore.env` (per `lore.yaml:39-40` `user_env`/`password_env`) |

`lore.yaml` sets no `surreal.database`, so `LoreConfig.effective_surreal_database`
(`config.py:620-628`) falls through to the project slug — `project: {slug: lore}` (`lore.yaml:5`) →
database **`lore`**. `INFO FOR NS` then revealed a **second** database, `demand_intelligence` — the
pp-odoo project's lore instance, sharing this store (memory `lore-two-container-topology`). Both are
built by the *same* `surreal_schema.py`, so the flip ships to both. I audited both.

**READ-ONLY compliance.** The audit script gates every statement before it reaches the wire with an
**allowlist** (`^\s*(SELECT|INFO FOR)\b`) plus an independent deny-scan for write verbs
(`prod_audit.py:26-42`). Allowlist-the-safe rather than enumerate-the-forbidden, per CLAUDE.md's
six-defeats table. **28 statements ran against `lore`, 28 against `demand_intelligence`; all are
`SELECT` or `INFO FOR`** — the full verbatim list is §STATEMENTS. No `use()`/`signin()` side effects:
I did **not** call the repo's `connect_admin` helper, which issues `DEFINE NAMESPACE IF NOT EXISTS` +
`DEFINE DATABASE IF NOT EXISTS` (`_surreal_harness.py:242-244`) — that would have been a write.

---

## THE EDGE TABLES — derived from the store, not from the brief

`INFO FOR DB` on **both** databases returns an identical 20-table set. Tables whose definition
carries `TYPE RELATION`:

```
### TYPE RELATION tables: ['answers_to', 'briefed', 'refers']
### TYPE ANY tables (candidate silently-auto-created edges): ['name']
```

The brief's list (`briefed`, `refers`, `answers_to`) is **confirmed complete** — the store agrees.
`name` is the only `TYPE ANY` table and is **NOT** an edge (§UNASKED-1).

---

## PER-TABLE

### Verbatim stored definitions — identical in both databases

```
answers_to: DEFINE TABLE answers_to TYPE RELATION SCHEMAFULL PERMISSIONS NONE
briefed:    DEFINE TABLE briefed    TYPE RELATION SCHEMAFULL PERMISSIONS NONE
refers:     DEFINE TABLE refers     TYPE RELATION SCHEMAFULL PERMISSIONS NONE
name:       DEFINE TABLE name       TYPE ANY      SCHEMALESS PERMISSIONS NONE
```

**Q4 answered: all three ARE `TYPE RELATION`; NONE carries `IN`, `OUT`, or `ENFORCED`.** This is
`REPORT-probe-enforced-clause.md` §UNASKED-5 confirmed on the live production store — the untyped
shape `_define_relation_table` emits (`surreal_schema.py:615-624`, which takes only a `name` and has
no `IN`/`OUT` parameters at all) is exactly what is stored.

The engine auto-defines the endpoint columns as bare `record` — **untyped** — on all three:

```
in:  DEFINE FIELD in  ON <edge> TYPE record PERMISSIONS FULL
out: DEFINE FIELD out ON <edge> TYPE record PERMISSIONS FULL
```

### The data

| database | edge | rows | endpoint combinations (count per combo) | ghosts | dangling `in` | dangling `out` |
|---|---|---:|---|---:|---:|---:|
| `lore` | `answers_to` | 17 276 | `code_node → name` : **17 276 (100%)** | **0** | 0 | 0 |
| `lore` | `briefed` | 31 | `agent → brief` : **31 (100%)** | **0** | 0 | 0 |
| `lore` | `refers` | 30 200 | `code_node → name` : **30 200 (100%)** | **0** | 0 | 0 |
| `demand_intelligence` | `answers_to` | 17 912 | `code_node → name` : **17 912 (100%)** | **0** | 0 | 0 |
| `demand_intelligence` | `briefed` | **0** | *(empty)* | 0 | 0 | 0 |
| `demand_intelligence` | `refers` | 36 060 | `code_node → name` : **36 060 (100%)** | **0** | 0 | 0 |
| — | **TOTAL** | **101 479** | **exactly 3 distinct combinations across the whole store** | **0** | 0 | 0 |

**Every edge table is perfectly homogeneous.** Not one row in either database has an endpoint on a
table other than the single intended one. There is no second combination anywhere.

Those combinations match the schema source's stated intent exactly — `agent->briefed->brief`
(`surreal_schema.py:81-82`), `code_node -> refers/answers_to -> name` (`:100-109`).

### Method (Q2) — two independent instruments, and they agree

**`meta::tb()` DOES exist on 3.1.5** — verified against the TEST store before use, not assumed
(`_shape.py` §A/§B). I used **both** available methods and cross-checked them:

1. **Engine-side:** `SELECT meta::tb(in) AS in_tb, meta::tb(out) AS out_tb, count() AS n FROM <edge> GROUP BY in_tb, out_tb`
2. **Client-side:** `SELECT id, in, out FROM <edge>`, then aggregating `RecordID.table_name` in Python.

The script asserts the two agree per table. Receipt, every table:
`--- instruments agree: True`.

### Ghost detection (Q3)

The brief suggested field projection. I used **`record::exists()`** instead, which the shape probe
proved exists on 3.1.5 and which is **strictly better**: field projection returning `None` cannot
distinguish *"the record is missing"* from *"the record exists but lacks that field"* — a
SCHEMALESS target like `name` makes that a live confusion, and it is exactly the trap that bit my own
`TYPE ANY` detector (§INSTRUMENT-DEFECT). The shape probe ran both side by side on a dirty fixture and
they agreed (`_shape.py` §D vs §E), so this is a substitution with a receipt, not a preference.

Predicate: `SELECT id, in, out FROM <edge> WHERE !record::exists(in) OR !record::exists(out)`.
**Result: zero rows, every table, both databases.** No ids to list.

---

## CONTROLS — proving a zero is a real zero

Six zeros in a row is exactly what a **blind probe** also returns. Both instruments were therefore
controlled on the TEST store (`ws://127.0.0.1:18000`, throwaway DB, reaped) against a table built to
mirror production's `briefed` verbatim (`TYPE RELATION SCHEMAFULL`, no `IN`/`OUT`) and deliberately
dirtied with a clean row, a ghost `out`, a ghost `in`, and a wrong-**table** row.

| control | statement | expected | got |
|---|---|---|---|
| **1 — combination query DISCRIMINATES** | the exact production `meta::tb` + `GROUP BY` | 2 combos | `agent→brief: 3`, `agent→intruder: 1` ✅ |
| **2 — ghost predicate FIRES** | the exact production `WHERE !record::exists(...)` | 2 rows | 2 rows, both named ✅ |
| **2b — per-side split** | `WHERE !record::exists(in)` / `(out)` | 1 each | 1 each ✅ |
| **3 — arithmetic** | live + ghosts == total, on a store WITH ghosts | True | `2 + 2 == 4` ✅ |
| **4 — NEGATIVE control** | same predicate on a known-clean table | `[]` | `[]` ✅ |

Control 4 matters as much as control 2: it shows the predicate does not fire on *everything*.
Controls 1 and 2 show it fires on cases we know are broken. **The instruments demonstrably see both
outcomes**, so production's zeros are measurements, not blindness.

The arithmetic control also ran **in production** on every non-empty table as a third check —
`live + ghosts == total` returned `True` for all six. ⚠ But note what control 3 exposed: the
**wrong-TABLE row counts as LIVE** (`intruder:x` exists), so *the arithmetic control alone cannot see
a poisoning candidate*. Only the combination query (control 1) can. That is why both instruments were
required, and why the homogeneous combination table above — not the ghost zero — is the load-bearing
evidence for `SAFE TO TYPE`.

---

## VERDICTS PER EDGE TABLE

| edge table | verdict |
|---|---|
| `briefed` (`lore`, 31 rows) | ✅ **SAFE TO TYPE.** All 31 rows are `agent → brief`. `TYPE RELATION IN agent OUT brief ENFORCED` poisons **0** rows. 0 ghosts. |
| `briefed` (`demand_intelligence`, 0 rows) | ✅ **SAFE TO TYPE** — empty; nothing to poison. |
| `refers` (`lore`, 30 200 · `demand_intelligence`, 36 060) | ✅ **SAFE TO TYPE.** All 66 260 rows are `code_node → name`. `IN code_node OUT name` poisons **0**. 0 ghosts. |
| `answers_to` (`lore`, 17 276 · `demand_intelligence`, 17 912) | ✅ **SAFE TO TYPE.** All 35 188 rows are `code_node → name`. `IN code_node OUT name` poisons **0**. 0 ghosts. |
| `name` | **NOT AN EDGE** — `TYPE ANY` but 0 of its 18 476 / 18 713 rows carry `in`/`out`. It is the *target* node table of `refers`/`answers_to`. No verdict needed; see §UNASKED-1 for the door it leaves open. |

No table earned `WOULD POISON N ROWS`, `HAS N GHOSTS`, or `CANNOT DETERMINE`.

---

## Q5 — do `message` / `to` already exist in production?

**No — and this is the good answer.** Checked against `INFO FOR DB` in both databases:

```
### PACKET-03 TABLES — do 'message' / 'to' already exist?
    message: absent
    to: absent
```

Packet 03 is genuinely greenfield on both. Per `REPORT-probe-enforced-clause.md` §RECOMMENDATION,
that means `IF NOT EXISTS` **would** in fact land today — and per the same section it must **not** be
relied on: ship `DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL`,
because the clause becomes a silent trap the first time anyone edits it, and every test mints a virgin
DB so no suite could ever see the no-op.

---

## RISK-STATEMENT

**If the flip shipped tomorrow, nothing in production would break.** All 101 479 edge rows across both
production databases are endpoint-homogeneous — `briefed` is 100% `agent → brief`, `refers` and
`answers_to` are 100% `code_node → name` — so adding `TYPE RELATION IN <a> OUT <b>` write-poisons
**zero** rows: there is no row whose endpoint points at a table the new typing would forbid, and the
`Couldn't coerce value for field 'out'` failure mode measured in `REPORT-probe-enforced-clause.md`
§UNASKED-5 has no candidate to fire on. There are likewise **zero ghosts** — every one of the 101 479
edges resolves to a record that actually exists — so `ENFORCED` can be adopted with no cleanup
migration and, unusually, with no false sense of completion (§Q3's warning about old ghosts serving
forever as receipts for agents who don't exist simply does not apply: there are none). The two real
risks are elsewhere and both are already documented: **(1)** the migration must use `OVERWRITE`, not
`IF NOT EXISTS` — `_define_relation_table` currently emits `IF NOT EXISTS`, which is a **silent
no-op** on these three already-existing tables, so a flip that ships unchanged would return `OK`,
pass every virgin-DB test, and leave production **exactly as untyped as it is today** (#107's shape,
and the far likelier failure than data damage); and **(2)** the `OVERWRITE`-is-free evidence was
measured on an 8-row table while production carries 101 479 edge rows — the probe showed
`DEFINE TABLE OVERWRITE` does not rebuild indexes, so this should be a metadata-only operation, but
it is an extrapolation across four orders of magnitude and deserves one timed run against a restored
copy rather than a shrug. **The data is clean; the mechanism is the thing to get right.**

---

## UNASKED — things I found that you did not ask about

### UNASKED-1 ⚠ `name` is `TYPE ANY` by OMISSION — an open door for a silent edge

`name` is the only non-`RELATION` table in either database that is not `TYPE NORMAL`:

```
name: DEFINE TABLE name TYPE ANY SCHEMALESS PERMISSIONS NONE
```

The cause is not a design choice — `_define_schemaless_table` (`surreal_schema.py:623-631`) emits
`DEFINE TABLE IF NOT EXISTS {name} SCHEMALESS` with **no `TYPE` clause at all**, and the engine
defaults an untyped table to `TYPE ANY`. Every other node table routes through `_define_table`, which
is also untyped-in-source yet stores as `TYPE NORMAL` — so the engine is inferring `NORMAL` for those
from their non-edge usage and `ANY` for `name`, which is *pointed at* by edges.

**Why it matters:** the enforced-clause probe established that a `RELATE` onto an undeclared table
auto-creates it `TYPE ANY`, silently. The inverse is the live exposure here — `name` is **already**
`TYPE ANY`, so a stray `RELATE $x->name->$y` (a typo'd edge name, a future verb) would be accepted and
would begin storing edges inside a node table, with no error and no schema change to notice. It is
clean today (I verified: **0 of 18 476 / 18 713 rows carry `in` or `out`**), which is the moment to
close it.

**Suggested fix, in the same flip:** give `_define_schemaless_table` an explicit
`TYPE NORMAL SCHEMALESS`, shipped `OVERWRITE` like the relation tables. Zero rows are affected
(`TYPE NORMAL` is what the data already is). Report-only — I edited nothing.

### UNASKED-2 The two production databases are schema-identical — the flip is one migration, not two

Both databases carry byte-identical definitions for all 20 tables, all three edge tables, and every
field and index on them. Whatever DDL fixes `lore` fixes `demand_intelligence`. Worth stating because
`demand_intelligence` is a **different project's** lore instance that no packet-03 brief mentions, and
its `refers` table is the **largest single edge population in the store** (36 060 rows — 19% more than
`lore`'s). If the flip is validated only against `lore`, it is validated against the smaller half.

### UNASKED-3 ⚠ The `OVERWRITE`-is-cheap measurement does not cover production scale

`REPORT-probe-enforced-clause.md` §UNASKED-4 measured `DEFINE TABLE OVERWRITE` on a populated table at
**1.7 ms** — an excellent result, and its HNSW/UNIQUE positive controls were sound. But that table
held **8 rows**. Production's three edge tables hold **101 479**. The probe's finding (that
`DEFINE TABLE OVERWRITE` preserves indexes rather than rebuilding them, unlike
`DEFINE INDEX OVERWRITE`) is a *mechanism* claim, so it should hold at any scale — but the *timing* is
an extrapolation across four orders of magnitude, and the schema DDL runs at **container boot**
(`lore-lore` already boots ~150 s eager). Cheap mitigation: one timed `OVERWRITE` against a restored
copy of the production RocksDB before the deploy, or simply time the first boot after the flip and
compare. Flagging, not blocking.

### UNASKED-4 `briefed` is the only edge with a UNIQUE index — and it is the only one that needs the dedupe rule

```
briefed_in_out:       DEFINE INDEX briefed_in_out       ON briefed    FIELDS in, out UNIQUE
refers_src_file_path: DEFINE INDEX refers_src_file_path ON refers     FIELDS src_file_path
answers_to_tier_file: DEFINE INDEX answers_to_tier_file ON answers_to FIELDS tier, file_path
```

Reference §4's caution — *"because `UNIQUE(in, out)` makes a repeated recipient a loud ERR, a fan-out
must dedupe before the RELATE loop"* — applies to `briefed` only. `refers`/`answers_to` carry plain
non-UNIQUE indexes and can hold duplicate `(in, out)` pairs. Relevant to packet 03 because the new
`to` edge is a **fan-out** and will presumably copy `briefed`'s UNIQUE shape; if so, the dedupe is
mandatory, not optional. (Consistent with reference §4's `surreal_schema.py:1071` citation —
`briefed`'s UNIQUE index is at `:519` in the current file, a stale line number in the reference, but
the claim itself is correct and confirmed live in production.)

### UNASKED-5 `briefed.via` carries a live closed-set ASSERT — do not disturb it with the flip

```
via: DEFINE FIELD via ON briefed TYPE string ASSERT $value INSIDE ['register', 'explicit', 'publish'] PERMISSIONS FULL
```

The enforced-clause probe verified `DEFINE TABLE OVERWRITE` preserves fields on an 8-row table with
one `option<string>` field. `briefed` carries a field with a **three-value closed-set ASSERT** and a
`DEFAULT time::now()` datetime. Both should survive (`OVERWRITE` on the TABLE does not touch FIELD
definitions), but the flip's migration test should assert `INFO FOR TABLE briefed` still shows the
ASSERT and the DEFAULT afterwards — a silently-dropped ASSERT is exactly the invisible-until-production
class §1.4 documents, and it is `briefed`'s only data-integrity guard.

---

## INSTRUMENT-DEFECT (disclosed)

My first `TYPE ANY`-edge detector was **wrong and would have reported a false finding**:

```python
rows = await q(connection, f"SELECT id, in, out FROM {name} LIMIT 1")
if rows and ("in" in rows[0] or "out" in rows[0]):   # WRONG
```

A SCHEMALESS `SELECT` of an **absent** key returns the key with value `None` rather than omitting it,
so `"in" in rows[0]` is `True` for every row of every table. It duly announced
`!! TYPE ANY table 'name' carries in/out — treating as an edge` and then crashed on
`None.table_name` — **the crash is the only reason I caught it.** Had `name` held even one row with a
real endpoint, the crash would not have happened and I would have reported a phantom fourth edge table
with a fabricated combination set.

This is reference §2's silent-`None`-projection trap, reproduced inside the very audit that was
written to hunt for it — and it is the same shape as the ghost-detection trap §4 warns about, which is
precisely why I switched the ghost predicate to `record::exists()` rather than field projection.

Corrected instrument — count rows whose endpoints are actually **set**, not keys that are present:

```
SELECT count() AS n FROM {tname} WHERE in != NONE OR out != NONE GROUP ALL
    name: 18476 rows, 0 of them carry in/out     (lore)
    name: 18713 rows, 0 of them carry in/out     (demand_intelligence)
```

---

## STATEMENTS — every statement run against production, verbatim

The audit script records each statement as it passes the read-only gate and prints the list at the
end. **28 statements against `lore`**, printed below from `out-lore.txt`. The
`demand_intelligence` run issued the **identical 28** (the script is parameterised only by database),
except that `briefed` is empty there so its combination/ghost/control statements (`[14]`–`[19]`) are
skipped, giving 22.

```
  [  0] INFO FOR NS
  [  1] INFO FOR DB
  [  2] SELECT count() AS n FROM name GROUP ALL
  [  3] SELECT count() AS n FROM name WHERE in != NONE OR out != NONE GROUP ALL
  [  4] INFO FOR TABLE answers_to
  [  5] SELECT count() AS n FROM answers_to GROUP ALL
  [  6] SELECT meta::tb(in) AS in_tb, meta::tb(out) AS out_tb, count() AS n FROM answers_to GROUP BY in_tb, out_tb
  [  7] SELECT id, in, out FROM answers_to
  [  8] SELECT id, in, out FROM answers_to WHERE !record::exists(in) OR !record::exists(out)
  [  9] SELECT count() AS n FROM answers_to WHERE !record::exists(in) GROUP ALL
  [ 10] SELECT count() AS n FROM answers_to WHERE !record::exists(out) GROUP ALL
  [ 11] SELECT count() AS n FROM answers_to WHERE record::exists(in) AND record::exists(out) GROUP ALL
  [ 12] INFO FOR TABLE briefed
  [ 13] SELECT count() AS n FROM briefed GROUP ALL
  [ 14] SELECT meta::tb(in) AS in_tb, meta::tb(out) AS out_tb, count() AS n FROM briefed GROUP BY in_tb, out_tb
  [ 15] SELECT id, in, out FROM briefed
  [ 16] SELECT id, in, out FROM briefed WHERE !record::exists(in) OR !record::exists(out)
  [ 17] SELECT count() AS n FROM briefed WHERE !record::exists(in) GROUP ALL
  [ 18] SELECT count() AS n FROM briefed WHERE !record::exists(out) GROUP ALL
  [ 19] SELECT count() AS n FROM briefed WHERE record::exists(in) AND record::exists(out) GROUP ALL
  [ 20] INFO FOR TABLE refers
  [ 21] SELECT count() AS n FROM refers GROUP ALL
  [ 22] SELECT meta::tb(in) AS in_tb, meta::tb(out) AS out_tb, count() AS n FROM refers GROUP BY in_tb, out_tb
  [ 23] SELECT id, in, out FROM refers
  [ 24] SELECT id, in, out FROM refers WHERE !record::exists(in) OR !record::exists(out)
  [ 25] SELECT count() AS n FROM refers WHERE !record::exists(in) GROUP ALL
  [ 26] SELECT count() AS n FROM refers WHERE !record::exists(out) GROUP ALL
  [ 27] SELECT count() AS n FROM refers WHERE record::exists(in) AND record::exists(out) GROUP ALL
```

**Every one is a `SELECT` or an `INFO FOR`.** No `DEFINE`, `REMOVE`, `ALTER`, `CREATE`, `UPDATE`,
`UPSERT`, `DELETE`, `RELATE`, `INSERT`, `REBUILD`, `BEGIN` or `COMMIT` was sent to `:18500` — enforced
by the gate at `prod_audit.py:26-42`, which raises **before** the wire rather than relying on my
discipline. No database, namespace or table was created. Nothing was written.

### Files (all outside the repo — no repo file was edited, no git state mutated)

`/tmp/claude-1000/edge-preflight/`:

| file | store | role |
|---|---|---|
| `_shape.py` | **TEST** `:18000` | shape verification: does `meta::tb` exist? does `record::exists` exist? do projection and `record::exists` agree on a dirty fixture? |
| `_control.py` | **TEST** `:18000` | the 4 positive/negative controls in §CONTROLS |
| `prod_audit.py` | **PROD** `:18500` | the read-only audit + its allowlist gate |
| `out-lore.txt`, `out-di.txt` | — | full verbatim output of both production runs |

Both test-store scripts minted their own `test_<pid>_<uuid4>` database and reaped it
(`[reaped …]` at the tail of each run).
