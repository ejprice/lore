# REPORT-probe-63b-ii — §4.F message-table DDL index de-risking (63b wave ii-a)

brief-base v14 read
brief project v7 read

## SUMMARY
- **State:** done — §4.F message DDL index choices de-risked GREEN; the WRITE-side risk the ii-a
  contract needed cleared is cleared.
- **Headline:** the member READ filter over `message` IndexScans (`UnionIndexScan` on `message_scope`,
  5 branches, **no `message` TableScan**); `owner_agent` alone TableScans (the named re-open trigger,
  real); the `id IN $ids AND (fragment)` inbox read IndexScans and its **leak gate returns exactly
  `['message:x_ap']`** (outer parens hold, no cross-principal leak). All on the live 3.2.4 TEST store.
- **Deviations:** (1) the existing `scripts/probe_read_filter_63.py` ALREADY probes the message table
  via the REAL shipped emitter — the message de-risking was largely already built; my extension adds
  the one genuinely-missing leg. (2) brief item 4(c) (ORDER-BY-on-alias) is a READ-side (drain/ii-b)
  query-shape concern, not a write-side DDL concern, and fails LOUD — surfaced for ii-b, not folded in.
- **Packages considered:** none — no mechanism specified (probe extension; reuses the engine + SDK).
- **Reuse ledger:** none — no new reusable symbol (the added control reuses `explain`/`_require`/
  `_governed_field_specs`/`PRINCIPAL_TABLE`, all already in the probe).
- **Graded:** `454375f` · HEAD-at-report: `454375f` · SAME.
- **Decisions-needed:** none blocking. One FLAG for the ii-a contract author (F-2 below): the read
  filter does NOT exercise `message_owner_principal` — pin the wiring, not just the plan.
- **Receipt pointers:** probe `scripts/probe_read_filter_63.py` (extended; the lead commits) · emitted
  DDL + EXPLAINs §"Receipts" below · emitter source `surreal_schema._governed_field_specs` /
  `_governed_index_statements` / `_message_statements` (read at HEAD via lore) · store-ref §2 (IN-in-OR),
  §7 L845 (ORDER BY).

---

## What was proven (mission: de-risk §4.F message DDL BEFORE the ii-a contract freezes)

§4.F (design `docs/design/2026-09-03-packet63b-design.md`) rules that 63b-ii adds
`_governed_field_specs()` + `_governed_index_statements(MESSAGE_TABLE)` to
`surreal_schema._message_statements`: `option<>` governed columns via `_define_field OVERWRITE`, plain
`IF NOT EXISTS` indexes on `scope` and `owner_principal` ONLY (`owner_agent` deliberately NOT indexed).
The de-risking question: **do those two indexes make the spliced `governed.read_filter` an IndexScan,
not a TableScan** (#107 shape — green on a virgin DB, TableScan on a dirty store)?

**Answer: YES, by construction, on the live 3.2.4 store.** The probe applies the REAL shipped emitter
(not a transcription) to `MESSAGE_TABLE` on top of `generate_message_ddl()`, seeds legacy(NONE) +
migrated rows, and classifies every read via live `EXPLAIN` with the same plan-walker the shipped
packet-60 pin uses. Ran clean twice at HEAD `454375f` on `ws://127.0.0.1:18000` (throwaway
`test_<pid>_<uuid4>` db, dropped on exit), **EXIT=0**.

### The exact §4.F DDL emitted (verbatim from the REAL emitter, applied to `message`)
```
DEFINE FIELD OVERWRITE owner_principal ON message TYPE option<record<principal>>;
DEFINE FIELD OVERWRITE owner_agent    ON message TYPE option<record<agent>>;
DEFINE FIELD OVERWRITE scope          ON message TYPE option<string>;
DEFINE INDEX IF NOT EXISTS message_scope            ON message FIELDS scope;
DEFINE INDEX IF NOT EXISTS message_owner_principal  ON message FIELDS owner_principal;
```
This is exactly what §4.F rules `_message_statements` will bake in. Source read at HEAD confirms the
emitter produces it: `_governed_field_specs()` → the three `option<>` specs with NO ASSERT/DEFAULT
(correct for a populated table, store-ref §1.4); `_governed_index_statements(t)` → `<t>_scope` +
`<t>_owner_principal`, both `_plain_index` (`IF NOT EXISTS`), `owner_agent` absent.

### Receipts — message-table EXPLAIN classifications (live 3.2.4, run at `454375f`)
| probe | query shape | plan | verdict |
|---|---|---|---|
| CTRL message `scope=` | `WHERE scope = $s` | `IndexScan` (`message_scope`) | index live |
| **CTRL message `owner_principal=`** (added) | `WHERE owner_principal = principal:alice` | `IndexScan` (`message_owner_principal`) | **2nd index live** |
| CTRL message `body=` | unindexed col | `TableScan` | walker sees TableScan |
| **C+ message `owner_agent=` alone** | `WHERE owner_agent = agent:ag_a` | `TableScan` | **re-open trigger real** |
| **P3 message FULL READ fragment** | member emitter, 2 keeps | `UnionIndexScan` on `message_scope`, 5 branches, **NO message TableScan** | **read filter index-served** |
| **P4 message `id IN $ids AND (fragment)`** | §4.3 step-2 inbox read | `IndexScan` (UnionIndexScan); LEAK GATE returned `['message:x_ap']` (excluded `x_other` NOT leaked) | **index-served + correctly scoped** |
| P5 message `scope IS NONE` | §2.3 boot count | `IndexScan` (`= NONE` on `message_scope`) | index-served |

The member emitter fragment (printed by the probe) is a flat OR of `scope`-keyed equalities with the
keeps **EXPANDED to per-value equalities** (`… OR scope = $k1 OR scope = $k2`) — NOT `scope IN $set` —
so the store-ref §2 `IN`-inside-`OR` TableScan trap is **structurally absent** (see F-3).

---

## Findings for the ii-a contract

**F-1 (informational, high value): the message DDL de-risking was already 90% built and is GREEN.**
`scripts/probe_read_filter_63.py` (committed, `f6db0ba`) already applies the REAL `_governed_field_specs`
+ `_governed_index_statements` emitter to `MESSAGE_TABLE` and probes P3/P4/P5 + `owner_agent` control on
the message table. The contract can CITE this committed probe as the DDL-index receipt rather than
re-deriving it. My extension adds the single missing leg (F-2).

**F-2 (FLAG — pin the wiring, not just the plan): the member READ filter never exercises
`message_owner_principal`.** In P3 all 5 `UnionIndexScan` branches drive off `message_scope`;
`owner_principal` rides as a residual `Filter` predicate inside the scope-keyed disjuncts (store-ref §2:
leading-column disjunction — the OR is over `scope` values). So **no probe here ever index-scanned
`message_owner_principal` until I added the dedicated `CTRL message owner_principal=` control** — a
wrong column / wrong type on that second index would have left every other message probe GREEN. The
control now proves the index is live (IndexScan on `message_owner_principal`). **Two consequences for
the contract:**
  1. Do NOT let a contract pin claim "the read filter proves `owner_principal` is indexed" — it proves
     `scope` is indexed and `owner_principal` narrows as a residual. `owner_principal`'s index exists for
     `owner_principal`-keyed reads (admin / migrate legs), not for this member filter. The dedicated
     single-column control is the receipt that it fires.
  2. The probe proves the EMITTER OUTPUT index-serves; it does NOT prove `_message_statements` actually
     CALLS the emitter (at HEAD it does NOT — §4.F). The contract needs a **wiring pin** that
     `_message_statements`'s output contains the `option<>` governed fields + both `message_*` indexes
     (mirror the memory wiring pin), else "routing is not sharing" — a green plan-probe over a seam the
     production DDL never invokes. `_message_statements` at HEAD emits only `_MESSAGE_FIELD_SPECS`
     (grade/body/sender/question) + `message_seq` + `message_sender_question` + the `to` edge; adding the
     two governed indexes is a clean ADDITIVE change (index names `message_scope`/`message_owner_principal`
     do not collide with `message_seq`/`message_sender_question`, and the governed fields use OVERWRITE so
     even a pre-existing scalar def would migrate cleanly, store-ref §1.1).

**F-3 (IN-inside-OR trap — CLEAR): the read filter carries no `IN` inside an `OR`.** The emitter expands
keep ids into per-value `scope = $kN` equality disjuncts, so the whole predicate is an index-served
`UnionIndexScan` (P3), not the store-ref §2 `col IN $set` inside an `OR` that TableScans the whole thing.
The only `IN` in the message reads is the OUTER `id IN $ids AND (fragment)` of the §4.3 step-2 inbox read
(P4), which plans as an IndexScan AND whose leak gate proves the sent parens bound the OR (excluded id
`x_other` did NOT leak). No DDL/filter-shape change needed on this axis.

**F-4 (`owner_agent` un-indexed re-open trigger — REAL): confirmed a TableScan** on both tables (C+
controls). The §4.F bound ("`owner_agent` deliberately NOT indexed; re-open trigger = the first
`owner_agent`-leading LIST read") is a genuine, measured bound — `owner_agent` never leads a READ
disjunct (it appears only ANDed under `scope='agent-private' AND owner_principal=…`), so it is not needed
by the current read filter. Pinned as a bound, not a defect.

**F-5 (brief item 4(c), ORDER-BY-on-alias — READ-side/ii-b, and it fails LOUD): surfaced, not folded in.**
The store-ref gotcha is §7 L845: under an **explicit projection**, the `ORDER BY` column must itself be
projected or it is a **PARSE ERROR** (`"Missing order idiom … in statement selection"`); `SELECT *`
never hits it. This is the drain read query shape (`SELECT id, … FROM message … ORDER BY seq`), i.e. the
**READ side (ii-b)**, and it is not a WRITE-side DDL index concern — my mission is the DDL. Because it is
a loud parse error (self-announcing in ii-b's own tests), it is NOT a silent de-risk hazard. Design §4.B
already notes it is "the L1 gotcha already in drain". **Recommendation:** the ii-b (drain/story/rollup)
contract carries a pin that every explicit-projection read ordering by a column also projects that column.
I did not build a write-side probe leg for it (out of the DDL scope, and the shape belongs to ii-b).

**F-6 (context for F5/ii-b, not a DDL concern): the `to` edge is an F5 DEPENDENT population, not
column-governed.** `_message_statements` defines `to` as `TYPE RELATION IN message OUT agent ENFORCED
SCHEMAFULL` with `to_in_out` UNIQUE + `to_out_seen_at` plain indexes — policy lives on `message`, per
§4.3/§4.F. Its drain-CAS index (`to_out_seen_at`) is what serves the §4.B step-1 edge window; it is
already present at HEAD and needs no governed column. Noted for the F5 population-derivation (§1.5c-iii),
not for the ii-a DDL.

---

## Method / discipline receipts
- Store law read FIRST: store-ref §1 (OVERWRITE-fields / IF-NOT-EXISTS-indexes), §2 (IndexScan-vs-
  TableScan-via-EXPLAIN, the `IN`-in-`OR` trap + composite-leading-column corollary, `IS NONE`), §7 L845
  (ORDER BY), §1.8 (UNIQUE-over-`option<>`). Cited, not re-transcribed.
- lore-first for structure: `lore_get_symbol` for `_message_statements` / `_governed_field_specs` /
  `_governed_index_statements` (read at HEAD, not recalled). `_MESSAGE_FIELD_SPECS` is a module CONSTANT
  (not a `get_symbol` chunk type); its contents are taken from the `_message_statements` docstring
  enumeration (grade/body/sender/question) + the probe's clean OVERWRITE co-application — HIGH confidence
  on no index-name collision (names read from source), MEDIUM on the exact field tuple (docstring, not
  the literal bytes; OVERWRITE makes it moot either way). No grep fallback used (grep is hook-blocked;
  said out loud per dogfood protocol).
- Positive controls per the C1 "a probe needs a control" law: the walker is shown seeing BOTH an
  IndexScan (indexed equality) AND a TableScan (unindexed equality) on the message table, so a GREEN
  verdict is not a blind instrument. The P4 leak gate reads ACTUAL rows (not the lossy EXPLAIN
  pretty-print) and includes an excluded id to prove discrimination.
- Change I made: added ONE control block (`CTRL message owner_principal=` → require IndexScan) to
  `scripts/probe_read_filter_63.py`, mirroring the existing `CTRL memory owner_principal=`. Re-ran:
  EXIT=0, all controls held. The lead commits the probe (COMMIT-ONLY).
```
=== SELF-CHECK VERDICT ===
All controls held; P1–P3 + P6 IndexScanned; NONE keys coexisted; every required
plan was classifiable. The §4.4 probe table's verdicts are established BY CONSTRUCTION.
```
