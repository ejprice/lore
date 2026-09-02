# REPORT-probe-63 — packet 63a read-filter store-law probe

- `brief-base v14 read`
- `brief project v7 read`
- store reference read FIRST (this is store/DDL/probe work):
  `docs/reference/surrealdb-31-capabilities.md` — cited by § below (§1.1 OVERWRITE-for-
  fields / IF-NOT-EXISTS-for-indexes; §1.4 option<> on a populated table; §1.5 a DEFINE
  INDEX builds; §1.8 UNIQUE over option<> = multiple NONE coexist; §2 the #413 IN-inside-OR
  TableScan trap + composite-leading-column corollary + `session`/`scope` protected param
  names; §3 statement[0]-only validation → execute_transaction; §4 traversal never
  index-served). Never re-transcribed.

## SUMMARY BLOCK

- Receipt: `brief-base v14 read` · `brief project v7 read`
- State: **done** — `scripts/probe_read_filter_63.py` committed, self-checking, **exit 0**;
  every §4.4 probe verdict established BY CONSTRUCTION on the live 3.2.4 TEST store.
- Capability check (brief-base §4): full tool access; every path/service the brief named was
  reachable (lore MCP loaded; spike-surreal TEST store on `ws://127.0.0.1:18000` live). No gap.
- Headline: **the §4.1 index ruling HOLDS.** P1 (THE discovery) IndexScans; P2/P3 UnionIndexScan;
  P4 index-served AND leak-free; P6 IndexScan + NONE-key coexistence; C+ controls prove the
  walker sees both scan classes. **P1 did NOT come back anything other than IndexScan — no §4.1
  re-open.**
- Deviations (3, all disclosed below §D): (1) referenced principal/agent rows NOT created
  (plain record<> links; the EXPLAIN plan is structural — store-ref §2/§4); (2) two bound-param
  renames (`$scope`→`$sc`, `$session`→`$sess`) forced by the protected-param rule (store-ref §2);
  (3) run with `uv run --all-packages` (a bare `uv run` installs no workspace members).
- Packages considered: none — no new mechanism specified. The probe reuses the project's
  `surrealdb` SDK, the REAL `generate_*_ddl` generators, and the REAL PDP emitter
  (`authorize_filter`); the EXPLAIN plan-walker is MIRRORED from `scripts/probe_read_filter_61b.py`
  (cited, not forked — instrument parsing, not production policy).
- Reuse ledger: 0 new REUSABLE production symbols (a throwaway `scripts/` probe). Reuse decisions
  in §E.
- Graded: `b02487c` · HEAD-at-report: `b02487c` · SAME (branch `feat/surreal-unification`;
  `lore_index` watched root `/workspace` @ `b02487c`).
- Decisions-needed: **ONE, non-blocking** — the design §2.3/§4.4 states `WHERE scope IS NONE`
  (the boot count) is a **TableScan**; on 3.2.4 it is an **IndexScan** (`access: "= NONE"` on the
  option<> scope index). Better than feared; §2.3/§4.4 should be corrected. Does NOT re-open §4.1.
  Routed to lead-63 / the design sidecar as a doc-currency fix (§C below).
- Receipt POINTERS: the probe → `scripts/probe_read_filter_63.py` (run: `uv run --all-packages
  python scripts/probe_read_filter_63.py`, exit 0); the §4.4 verdict table → §A; the P1 discovery
  → §B; the P5 correction → §C; the P4 leak gate → §A/P4.

---

## §A — The §4.4 probe table (P1–P6 + C+), with pasted EXPLAINs

Every plan classified by the SAME walker the shipped packet-60 pin uses
(`test_keeps_schema.py::TestTheKeeperIndexFires` — `operator == 'IndexScan'` / `'TableScan'` with
`attributes.table`), mirrored into the probe. Full JSON plans are printed by the committed script;
the decisive nodes are pasted here.

| # | probe | over | classification | verdict |
|---|---|---|---|---|
| **P1** | `WHERE scope = $s` | REAL `memory` DDL (HNSW + FULLTEXT co-resident) + `scope option<string>` + NONE-scope row present | **IndexScan** (`memory_scope`) | **PASS** — the discovery holds |
| **P2** | FULL `authorize_filter(member, READ).to_surql()` (member, 2 keeps) | `memory` | **IndexScan** (`UnionIndexScan` of 5 `IndexScan`) | **PASS** — no memory TableScan |
| **P3** | P2's shape | REAL `message` DDL, legacy(NONE)+migrated rows | **IndexScan** (`UnionIndexScan` on `message_scope`) | **PASS** |
| **P4** | `WHERE id IN $ids AND (<fragment>)` (§4.3 step-2) | `message` | **IndexScan** + **leak-free** | **PASS (report+gate)** — no per-id fallback needed |
| **P5m/P5x** | `WHERE scope IS NONE` (§2.3 boot count) | `memory` / `message` | **IndexScan** (`access: "= NONE"`) | **REPORT — design said TableScan; see §C** |
| **P6** | `WHERE key = $k` after SF-63-4 UNIQUE index, ≥2 NONE-key keeps | `keep` | **IndexScan** (`keep_key`) + 2 NONE keys coexist | **PASS** |
| **C+m/C+x** | `WHERE owner_agent = $a` alone | `memory` / `message` | **TableScan** | **PASS** — documents the un-indexed `owner_agent` bound (§4.1) |

**Script exit status: `0`** (`All controls held; P1–P3 + P6 IndexScanned; NONE keys coexisted;
every required plan was classifiable`).

### Pasted EXPLAINs (decisive nodes)

**Instrument-integrity + C+ controls** (proving the walker can see BOTH scan classes on BOTH real tables):
```
[IndexScan ] CTRL memory owner_principal= (indexed)      operators=['SelectProject', 'IndexScan']
[IndexScan ] CTRL message scope=          (indexed)      operators=['SelectProject', 'IndexScan']
[TableScan ] CTRL memory kind=            (unindexed)    operators=['SelectProject', 'TableScan']
[TableScan ] CTRL message body=           (unindexed)    operators=['SelectProject', 'TableScan']
[TableScan ] C+ memory owner_agent= alone (un-indexed@63)operators=['SelectProject', 'TableScan']
[TableScan ] C+ message owner_agent= alone(un-indexed@63)operators=['SelectProject', 'TableScan']
```

**P1 — the discovery** (`SELECT id FROM memory WHERE scope = $s`):
```
operators=['SelectProject', 'IndexScan']
  IndexScan  attributes={ access: "= 'server'", direction: "Forward", index: "memory_scope" }
```

**P2 — memory FULL emitter READ fragment** (real `authorize_filter` output; keeps EXPANDED, never `IN`):
```
operators=['SelectProject', 'Filter', 'UnionIndexScan',
           'IndexScan', 'IndexScan', 'IndexScan', 'IndexScan', 'IndexScan']
UnionIndexScan branches=5 table="memory":
  IndexScan access "= 'agent-private'"   index "memory_scope"
  IndexScan access "= 'principal-private'" index "memory_scope"
  IndexScan access "= 'server'"          index "memory_scope"
  IndexScan access "= 'keep:k1'"         index "memory_scope"
  IndexScan access "= 'keep:k2'"         index "memory_scope"
(residual Filter re-checks owner_principal/owner_agent; NO TableScan of memory)
```
The emitted fragment (verbatim, from the REAL emitter):
```
((scope = $s_… AND owner_principal = type::record('principal', $p_…) AND owner_agent = type::record('agent', $a_…))
 OR (scope = $s_… AND owner_principal = type::record('principal', $p_…))
 OR scope = $s_…
 OR (scope = $k_… OR scope = $k_…))
```

**P3 — message FULL emitter READ fragment** (identical shape, `message_scope`):
```
operators=['SelectProject', 'Filter', 'UnionIndexScan', 'IndexScan'×5]
UnionIndexScan branches=5 table="message"  (all children index "message_scope"); NO TableScan of message
```

**P4 — the §4.3 step-2 inbox read** (`WHERE id IN $ids AND (<fragment>)`):
```
operators=['SelectProject', 'Filter', 'UnionIndexScan', 'IndexScan'×5]   (index_served, NO message TableScan)
LEAK GATE — id IN [x_ap(admitted), x_other(excluded)] AND (fragment) returned: ['message:x_ap']
```
⚠ The EXPLAIN pretty-prints the predicate with the fragment's outer parens FLATTENED
(`id INSIDE [...] AND A OR B OR C …`) — which, if EVALUATED that way (AND binds tighter than OR),
would apply the id filter to only the FIRST disjunct and leak principal-private/server/keep rows
outside the id set (the #416 hazard, one level out). **The leak gate reads the ACTUAL rows and
proves the sent parens HOLD**: with `$ids = [x_ap (fragment admits), x_other (fragment excludes)]`,
the query returned **exactly `['message:x_ap']`** — no leak. The flattened render is a lossy
display artifact, not the evaluated semantics. **The §4.3 two-step shape is index-served AND
correctly scoped; no per-id `type::record` fallback is needed.**

**P5 — `WHERE scope IS NONE`** (`SELECT count()`):
```
operators=['SelectProject', 'Compute', 'IndexScan']
  IndexScan  attributes={ access: "= NONE", direction: "Forward", index: "memory_scope" }   (memory)
  IndexScan  attributes={ access: "= NONE", direction: "Forward", index: "message_scope" }  (message)
```

**P6 — keep `key = $k`** after SF-63-4's UNIQUE index (`keep_key`), with 2 NONE-key keeps present:
```
NONE-key keeps present (must be >= 2, §1.8 coexistence): 2       ← both manual keeps persisted
operators=['SelectProject', 'IndexScan']
  IndexScan  attributes={ access: "= 'project:lore'", direction: "Forward", index: "keep_key" }
```

---

## §B — P1 DISCOVERY VERDICT (the one genuinely unprobed delta, §4.4)

**✅ IndexScan — the §4.1 index ruling HOLDS. No re-open, no sidecar route.**

61b probed a **non-option `scope string` on a BARE `gov` fixture table**. 63's genuinely unprobed
delta is a **PLAIN index on an `option<string>` `scope` column, with NONE-scope rows present,
CO-RESIDENT with the real `memory` HNSW vector index and BM25 FULLTEXT index**. This probe applied
the REAL `generate_memory_ddl(dim=8)` (analyzer + `memory` + HNSW + FULLTEXT + valid_until), then
the §4.1 governed overlay (`owner_principal`/`owner_agent`/`scope` via OVERWRITE + plain
`IF NOT EXISTS` indexes on `scope` and `owner_principal`), seeded a spread of scoped rows plus a
NONE-scope legacy row, and confirmed:

- `WHERE scope = $s` → **IndexScan on `memory_scope`** (P1), and the same on `message_scope` (a
  message-side control).
- The full emitted READ predicate → **UnionIndexScan of 5 `IndexScan` children, no TableScan**
  (P2/P3), identical to 61b's finding — re-confirmed on the REAL tables with the REAL option<>
  columns and legacy NONE rows present.

**61b's result generalises to the real option<> columns on the real tables.** The HNSW/FULLTEXT
co-residence does not perturb the `scope` equality plan; the `option<string>` type does not defeat
the plain index (consistent with store-ref §1.8: an option<> index stores its NONE entries — which
is exactly what P5 and P6's coexistence also show).

---

## §C — P5 finding: a design-doc correction (NON-BLOCKING, does NOT re-open §4.1)

**Design §2.3 and §4.4 both state the `WHERE scope IS NONE` boot count is a TableScan.** On 3.2.4
it is an **IndexScan** — the plain index on the option<> `scope` column serves the NONE predicate
(`access: "= NONE"`, index `memory_scope` / `message_scope`). Empirically the §2.3/§4.4 "TableScan"
claim is FALSE on 3.2.4.

- **Impact: purely favourable.** The boot-time `SELECT count() … WHERE scope IS NONE GROUP ALL`
  (§2.3's forgotten-backfill alarm) is *index-served*, not a table scan bounded by row count. The
  mechanism §2.3 relies on still works (a non-zero count still fires the WARNING); it is merely
  cheaper than the design assumed.
- **It does NOT re-open the §4.1 index ruling** — the READ filter's plans (P1/P2/P3) are unaffected;
  this is only about the boot-count query's cost class.
- **Recommended doc fix** (for the design sidecar / the 63a contract author): §2.3 — change
  *"The count query is a TableScan on a NONE predicate"* to *"index-served on 3.2.4 (`access: "= NONE"`
  on the `scope` index) — even cheaper than a bounded TableScan"*; §4.4 P5 — change the expected
  verdict from "TableScan" to "IndexScan (`= NONE`)" and drop the "so nobody mistakes it for
  index-served" rationale (it IS index-served). This is the P8d prose-currency class (a doc claim no
  gate checks); surfaced here per scope law rather than silently absorbed.

Per brief-base §2, this is escalated as a fork with a recommendation, not silently resolved. It is
**non-blocking** for 63a's contract (the store-law plan the contract pins — P1/P2/P3 — is exactly as
designed).

---

## §D — Deviations (all disclosed)

1. **Referenced `principal`/`agent` records are NOT created.** `owner_principal`/`owner_agent`
   (`option<record<…>>`) and `message.sender` (`record<agent>`) are PLAIN links — store-ref §2/§4:
   a record-link equality needs no live target, and the EXPLAIN plan is chosen STRUCTURALLY (index
   availability + operator), before any row is read. This is a store-law PLAN probe, not a
   referential-integrity probe, so the scaffolding is unnecessary; omitting it avoids the
   `agent`/`principal` required-field ASSERTs and keeps the probe faithful to the plan under test.
   The `keep` rows DO carry a (link) keeper + a valid `type` ('project') to satisfy the keep
   ASSERTs.
2. **Two bound-param renames.** The seed helpers spell the bound params `$sc` (scope) and `$sess`
   (session), NOT `$scope`/`$session` — `scope`/`session` are **protected variable names**
   (store-ref §2: `SET session = …` / a `$session` param is rejected). The COLUMN keys stay `scope`
   / `session`; only the bound-param spellings changed. (The REAL emitter is unaffected — it names
   params `s_<hash>`/`p_<hash>`/etc.)
3. **Run invocation.** `uv run --all-packages python scripts/probe_read_filter_63.py` — a bare
   `uv run` syncs a venv WITHOUT the workspace members (`loremaster`/`lorerunes`), so `import
   loremaster` fails; `--all-packages` (the `scratch_copy.sh` idiom) installs them. Noted so a
   later runner does not hit the `ModuleNotFoundError` first.

---

## §E — Reuse decisions (DRY / ROUTING-IS-NOT-SHARING)

| thing | decision | note |
|---|---|---|
| the READ predicate under test | **REUSED** `lorerunes.pdp.authorize_filter(subject, Action.READ, table)` | the REAL production emitter (`read_filter` wraps `.to_surql()`, design §1.2); for a member it delegates to `_member_filter` (`pdp.py:432`). P2/P3/P4 splice its verbatim output — never a hand-typed WHERE (§4.2). |
| the DDL under test | **REUSED** `generate_memory_ddl` / `generate_message_ddl` / `generate_keep_ddl` / `generate_agent_ddl` / `generate_principal_ddl` | the EXACT slices `LocalMemoryBackend.ensure_ready` / `MessageLedger.ensure_ready` apply, each inside one `BEGIN…COMMIT` via `execute_transaction` (verified: `memory/local.py:403`, `messages.py:599`). Applied in production order. |
| the §4.1 governed overlay | **HAND-TRANSCRIBED** from design §4.1 (verbatim) | the `_governed_field_specs`/`_governed_index_statements` emitter it describes is NOT yet built — this probe runs BEFORE 63a's contract is frozen (that is the point). The overlay is 5 lines per table + 2 for keep, copied exactly from the §4.1 code block. |
| the EXPLAIN plan-walker (`_operators`/`_scans_table`/`_classify`/`explain`/`_require`) | **MIRRORED** from `scripts/probe_read_filter_61b.py` (cited) | instrument parsing, not production policy — the same stance 61b took re-expressing `test_keeps_schema`'s walker. ROUTING-IS-NOT-SHARING does not demand two throwaway probe scripts share a walker; the shared PRODUCTION walker is `TestTheKeeperIndexFires`, which both cite. |
| the throwaway DB | **REUSED** the `test_<pid>_<uuid4>` idiom (`unique_database`) | parallel-safe per `_surreal_harness.unique_database`; dropped on exit; TEST store `:18000` only, never prod `:18500`. |

No NEW reusable production symbol is introduced — the probe is a self-contained `scripts/`
instrument. Every helper it defines (`_governed_overlay`, `_create_memory/message/keep`,
`_read_fragment`, `_row_ids`, `probe`, `_verdict`, …) is script-local.

---

## §F — Gates on the deliverable

- `uv run ruff check scripts/probe_read_filter_63.py` → **All checks passed!**
- `uv run mypy scripts/probe_read_filter_63.py` → **Success: no issues found in 1 source file**
  (`scripts/` is gated ground per #188).
- `uv run --all-packages python scripts/probe_read_filter_63.py` → **exit 0**, self-checking.

*Probe committed as one concern (`test(63): read-filter store-law probe — IndexScan proof
(P1-P6 + controls)`). Task `0161c3071ecd48d699199bd0edda20fb` → done. The one non-blocking fork
(§C, the P5 boot-count doc correction) is surfaced for lead-63 / the design sidecar; every
store-law plan the 63a contract pins (P1/P2/P3, plus P6 and the C+ owner_agent bound) is proven
BY CONSTRUCTION on the live 3.2.4 TEST store.*
