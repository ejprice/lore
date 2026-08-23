# REPORT-probe-61b — store-law facts for the packet-61b PDP read-filter emitter

```
brief-base v14 read
brief project v7 read
```

## SUMMARY BLOCK

- **State:** done. Committed self-checking probe `scripts/probe_read_filter_61b.py` (exit 0,
  every leg with a positive control) + this facts report. All four load-bearing facts
  settled BY CONSTRUCTION (EXPLAIN pasted below), not asserted.
- **Deviations:** none. (Two writable-set files touched: the probe, and one adjudication
  entry in `test_secret_typing.py`'s credential-ORIGIN allowlist — the packet-48/61a-w1
  precedent, expected by the brief.)
- **Packages considered:** none — the deliverable is a measurement instrument, not a
  mechanism; EXPLAIN-plan classification is trivial stdlib dict-walking (mirrors the shipped
  `test_keeps_schema.TestTheKeeperIndexFires` walker). DDL/reads route through the production
  `loremaster.store._txn` seams (`execute_transaction`/`bootstrap_session`/`signin_credentials`).
- **Reuse ledger:** 0 new *reusable* symbols. 3 script-local helpers mirror test-tree code not
  importable from `scripts/` — see DRY LEDGER at the end.
- **Graded:** `7aab121` · HEAD-at-report: `7aab121` · SAME. (Facts are engine behaviour probed
  on the live 3.2.4 TEST store at this HEAD; the probe/report add no production code.)
- **Decisions-needed:** none for me. Two items handed UP (both non-blocking): (1) the emitter
  contract 61b-w1 chooses between the two proven index-served emitter shapes (recommendation
  below — expand the `IN`); (2) a recommended `docs/reference/surrealdb-31-capabilities.md` §2
  addition (outside my writable set — flagged, not made).
- **Receipt POINTERS:** probe = `scripts/probe_read_filter_61b.py`; durable engine fact =
  finding **#413** (`lore_findings get 413`) + memory `0dd841df` (`lore_recall("surrealdb planner IN OR")`);
  precedent walker = `loremaster/tests/test_keeps_schema.py::TestTheKeeperIndexFires`.

---

## The one-message headline

`STATE: done · REPORT: REPORT-probe-61b.md · IN→UnionIndexScan; composite=leading-col-only;`
`flat OR w/ IN = TableScan (#107 trap) but IN-EXPANDED-to-equalities = IndexScan; member_of in= IndexScan.`
`Emitter may stay a FLAT OR iff it expands scope IN $keeps to per-keep equalities.`

---

## What was probed, and how it is trustworthy

The packet-61 PDP's `authorize_filter` will emit a SurrealQL `WHERE` fragment for the governed-row
READ predicate (design Fork C):

```
(scope='agent-private' AND owner_principal=$p AND owner_agent=$a)
  OR (scope='principal-private' AND owner_principal=$p)
  OR scope='server'
  OR scope IN $my_keep_scopes
```

Fork E rules `owner` as two indexed record-link fields (`owner_principal record<principal>` +
`owner_agent record<agent>`), and names three things as **BELIEVED, not known** (the trust-law
hazard) until probed on the live 3.2.4 engine: does `IN` IndexScan, what index set the disjunction
needs, and — the load-bearing one — whether an **OR of indexed predicates** index-serves or forces
a whole-table scan (the #107 shape: green on a small/virgin test DB, a TableScan on a large dirty
store). Fork F rules the visible-Keeps resolver as a plain-table `member_of WHERE in=$p` read on the
existing `UNIQUE(in,out)` leading column.

**Method (store-ref §2 EXPLAIN discriminator + §4 "a probe needs a positive control").** Each scan
claim is a live `EXPLAIN` plan on the real 3.2.4 store `ws://127.0.0.1:18000` (TEST store; never
:18500), classified by the **same plan-walker the shipped packet-60 pin uses**
(`test_keeps_schema.py::TestTheKeeperIndexFires` — `operator == "IndexScan"` / `"TableScan"` with
`attributes.table`). E1/E2/E3 use a **synthetic** `gov` table matching the Fork-E owner shape (two
indexed record-link fields + an indexed `scope` + a deliberately **unindexed** `note` column) since
the governed tables aren't retrofitted until 63/64; Probe F uses the **real** `member_of` edge
(`generate_principal_ddl()` + `generate_keep_ddl()`).

**Instrument integrity is proven, not assumed.** The probe fails LOUD (exit ≠ 0) unless the walker
can SEE both an IndexScan (control: `WHERE scope='x'` on the indexed column) **and** a TableScan
(control: `WHERE note='x'` unindexed; and an unindexed `note OR note`) — the store-ref §4 discipline
("the instrument's first run said the opposite … only the positive control exposed it"). Every
probed plan must be classifiable; an unreadable plan is a surprise, never a guessed IndexScan.
Discoveries (does `IN` IndexScan? does the OR?) are OBSERVED and reported, whatever they are.

`uv run python scripts/probe_read_filter_61b.py` → **exit 0**: all controls held, Fork-F
assumptions held, every plan classifiable.

---

## THE FOUR SETTLED FACTS

### (1) `scope IN $set` — IndexScan, via `UnionIndexScan`

`WHERE scope IN $set` on an indexed `scope` column **IndexScans** — the engine expands it into a
`UnionIndexScan` of per-value equality `IndexScan` nodes:

```
SELECT id FROM gov WHERE scope IN ['keep:k1','keep:k2'] EXPLAIN
  operator "Filter" (predicate "scope INSIDE ['keep:k1','keep:k2']")
    operator "UnionIndexScan" (branches 2, table gov)
      operator "IndexScan" (access "= 'keep:k1'", index gov_scope)
      operator "IndexScan" (access "= 'keep:k2'", index gov_scope)
```

**Empty set:** `scope IN []` → `EmptyScan` — the engine proves zero rows and reads nothing (NOT a
TableScan). So the empty `$my_keep_scopes` case is safe by construction.

### (2) Composite index is LEADING-COLUMN only → minimal set = separate `scope` + `owner_principal`

Store-ref §2's leading-column-only rule **holds on 3.2.4**. On a single composite
`(scope, owner_principal, owner_agent)`:

| predicate | plan |
|---|---|
| `scope = $s` (leading) | **IndexScan** |
| `owner_principal = $p` alone (2nd col) | **TableScan** |
| `owner_agent = $a` alone (3rd col) | **TableScan** |
| `scope = $s AND owner_principal = $p` (leading+2nd) | **IndexScan** |
| `owner_principal = $p` on `gov` (its OWN separate index) | **IndexScan** |

The `principal-private` read (a user's personal memory — a hot path) filters `owner_principal`, and
under a single composite that predicate has no leading `scope=` in isolation for the whole-table
case → it would **TableScan**. **Minimal READ index set = SEPARATE indexes on `scope` AND
`owner_principal`** (as Fork E rules — two flat indexed fields, not one composite). `owner_agent`
warrants its own index for the Fork-E record-link shape / other actions, but the READ predicate
never filters `owner_agent` in isolation (always with `scope` + `owner_principal`), so it is not
required by the READ path.

### (3) ⚠ THE OR-PLANNER — a flat OR *with `IN`* TableScans; the defeating ingredient is `IN`-inside-OR

The full flat 4-way READ predicate is a **whole-table `TableScan`** — the entire predicate becomes a
`pre_decode_filter` and no index access path appears — **even though every disjunct ALONE IndexScans**:

```
SELECT id FROM gov WHERE (scope='agent-private' AND owner_principal=$p AND owner_agent=$a)
  OR (scope='principal-private' AND owner_principal=$p) OR scope='server' OR scope IN $keeps EXPLAIN
  operator "TableScan" (table gov, pre_decode_filter "yes", predicate "<the whole OR>")
```

But the cause is **NOT the OR itself, and NOT the compound `AND` disjuncts.** The boundary probes
isolate it — the ONLY ingredient that collapses an OR to a TableScan is an **`IN` appearing as an OR
branch**:

| OR shape | plan |
|---|---|
| same-column OR `scope='a' OR scope='b'` | **IndexScan** (UnionIndexScan) |
| cross-column OR `scope='s' OR owner_principal=$p` | **IndexScan** |
| bound-A: `(scope=x AND owner=$p) OR (scope=y AND owner=$p)` (two AND-compounds) | **IndexScan** |
| bound-D: `(scope=x AND owner=$p) OR scope='s'` (compound OR eq) | **IndexScan** |
| bound-B: `scope='s' OR scope IN $keeps` (eq **OR IN**, same column) | **TableScan** |
| bound-C: `scope=a OR scope=b OR scope=c OR scope IN $keeps` (**with IN**) | **TableScan** |
| bound-E: bound-C with the **`IN` EXPANDED** to `scope='k1' OR scope='k2'` | **IndexScan** |
| **FULL READ predicate (uses `IN`)** | **TableScan** |
| **FULL READ predicate, `IN` EXPANDED to per-keep equalities** | **IndexScan** |

bound-C vs bound-E is the decisive pair: identical row semantics, differing only in `IN` vs expanded
equalities, and they classify oppositely. The FULL-OR-expanded plan is a clean index union:

```
SELECT id FROM gov WHERE (scope='agent-private' AND owner_principal=$p AND owner_agent=$a)
  OR (scope='principal-private' AND owner_principal=$p) OR scope='server'
  OR scope=$k1 OR scope=$k2 EXPLAIN
  operators = [SelectProject, Filter, UnionIndexScan, IndexScan, IndexScan, IndexScan, IndexScan, IndexScan]
```

**Positive controls proving the probe distinguishes the two:** an index-served OR (the `IN`'s
`UnionIndexScan`, and the same-column OR) is classified IndexScan; a known-TableScanned OR (unindexed
`note OR note`) is classified TableScan. So the "flat OR with `IN` TableScans" verdict is trustworthy.

### (4) `member_of WHERE in=$p` — leading-column IndexScan (Fork F resolver confirmed)

On the **real** `member_of` edge (`UNIQUE(in,out)`, index `member_of_in_out`):

```
SELECT out FROM member_of WHERE in = $p EXPLAIN
  operator "IndexScan" (access "[principal:alice]", index member_of_in_out)   -- LEADING column
SELECT in FROM member_of WHERE out = $k EXPLAIN
  operator "TableScan" (table member_of)                                       -- TRAILING column
```

The resolver's `SELECT out FROM member_of WHERE in=$principal` (Fork F) is a leading-column
**IndexScan** on the existing UNIQUE index — **no new index needed**, bounded by membership degree,
one round trip. The trailing-column `WHERE out=$k` TableScans (positive control proving
leading-vs-trailing discrimination on THIS edge).

---

## EMITTER-SHAPE VERDICT (for the 61b-w1 emitter contract)

**The PDP read-filter emitter (`Predicate.to_surql`) may stay a FLAT OR — provided it EXPANDS
`scope IN $my_keep_scopes` into N explicit per-keep `scope = $k_i` equality disjuncts** (bound
params, N = membership degree; **omit the keep clause entirely when the keep set is empty** — an
empty `IN` OR'd in would re-introduce the trap, and with no keeps the predicate is
`d1 OR d2 OR d3`, which index-serves). Every disjunct is then an index-served equality and the whole
predicate is a `UnionIndexScan` — **no UNION-of-queries, no bounded-TableScan acceptance needed.**

Two proven-safe shapes exist; both index-serve, the first is simpler:

1. **Flat OR with the `IN` expanded to equalities** (recommended — proven: FULL-OR-expanded =
   IndexScan). Cost: the emitted string length grows with membership degree (bounded, small).
2. A UNION of per-clause queries. Also valid; more machinery. Not needed given (1).

**What would be WRONG (the #107 ship):** emitting the flat OR with `scope IN $my_keep_scopes` left as
an `IN`. It is green on a virgin/small test DB and a full TableScan on a large dirty store — exactly
#131/#107's "the test environment is a fiction" shape. A pin over the emitter's output must EXPLAIN
the emitted fragment against a real store and assert **no `TableScan`** (positive control: an
unindexed predicate that does), not merely that the SQL string parses.

**Cross-reference for Fork A's oracle:** the `matches()` Python evaluator uses `scope in
my_keep_scopes` set-membership; the emitter expanding `IN` to equalities is semantically identical
(`scope == k1 OR scope == k2 …`), so the two interpreters stay equivalent. The Fork-A live-store
oracle differential test will catch any divergence — the expansion is an emitter-side index
optimisation, not a semantic change.

---

## Fork F latent seam (surfaced, per Fork F rider — not fixed, scope-adjacent)

`KeepStore.list_household` filters `WHERE out=$keep` — the **trailing** column of `UNIQUE(in,out)` →
a **TableScan** (fact 4 control). Bounded by the `member_of` row count (small today), so not a 61
blocker, and the 61 read path does NOT share it (the resolver uses the leading column). If a
household or the global `member_of` table grows, `list_household` wants its own index on `out` (a
free `IF NOT EXISTS` add). Flagged for the lead; not in 61's writable intent unless the operator
rules it in.

---

## FLAGS handed up (non-blocking)

1. **Emitter design choice** → 61b-w1 emitter contract. Recommendation above (expand the `IN`);
   both shapes proven index-served, so this is a simplicity call, not a correctness fork.
2. **Store-reference §2 doc gap** (outside my writable set — recommended, not made): §2 proves `=`
   and range IndexScan but has **not** probed `IN` or the OR-planner. Fold facts (1)–(3) into
   `docs/reference/surrealdb-31-capabilities.md` §2 — the `IN`-inside-OR → TableScan behaviour and
   the expand-to-equalities fix are a #107-class trap that belongs in the canonical reference.
   Captured durably meanwhile as finding **#413** + memory `0dd841df`.
3. **`list_household` trailing-column TableScan** (fact 4 / Fork F rider) — latent perf seam, above.

---

## Discipline receipts

- TEST store `ws://127.0.0.1:18000` only; production `:18500` never touched. DB minted
  `test_<pid>_<uuid4>`, dropped on exit.
- Bound params throughout (`RecordID`, lists); no interpolation of caller values.
- DDL applied via production `execute_transaction` (every statement checked — store-ref §3), never
  the lax `.query()` that validates only `statement[0]`.
- Gates run: `ruff check scripts/probe_read_filter_61b.py` → clean;
  `pytest loremaster/tests/test_secret_typing.py -n auto` → **69 passed** (after the allowlist add).
- `IN`-in-OR fact is STRUCTURAL (the plan carries no index access path at all, not a cost/selectivity
  choice), so it is a version-pinned 3.2.4 engine fact. **Bound:** measured on 3.2.4, small fixture;
  re-probe if the engine version moves (the quadlets pin the floating `v3.2` tag — store-ref §0).

---

## DRY LEDGER (brief-base §6)

The probe is a self-contained `scripts/` script (house convention — `probe_unique_nullable_48.py`
hand-rolls its own helpers rather than importing test scaffolds). No NEW reusable/shared symbol is
introduced; the three helpers below mirror **test-tree** code that a `scripts/` script cannot cleanly
import, and are cited, not forked into shared production code:

| new script-local symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_operators` / `_scans_table` (EXPLAIN walker) | `lore_search "EXPLAIN IndexScan TableScan positive control"` + read `test_keeps_schema.py` | the shipped walker lives as static methods on `TestTheKeeperIndexFires` (a test class, not importable API) | HAND-ROLLED, byte-mirroring `test_keeps_schema.TestTheKeeperIndexFires._operators/_scans_table` (cited) — instrument parsing, not production policy; a probe is self-contained by house convention |
| `_apply_ddl` (BEGIN/COMMIT via `execute_transaction`) | read `_enforced_relations_scaffold.apply_ddl` | exists as a test scaffold in `loremaster/tests/`, not importable from `scripts/` | HAND-ROLLED, mirroring `_enforced_relations_scaffold.apply_ddl` (cited); routes through the production `execute_transaction` seam (no cloned retry/classify policy) |
| `unique_database` | read `_surreal_harness.unique_database` + `probe_unique_nullable_48.py` | the harness helper is a test-module function; `probe_48` redefines it locally | HAND-ROLLED, following the `probe_48` precedent (test module not imported by `scripts/` probes) |

No retry / backoff / error-classifier / validator / sanitiser was written — the probe rides the
production `_txn` seams for all engine access.
