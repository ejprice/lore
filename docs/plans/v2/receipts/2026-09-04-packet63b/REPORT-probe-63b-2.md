# REPORT-probe-63b-2

`brief-base v14 read`
`brief project v7 read`

Extend the committed read-filter probe (`scripts/probe_read_filter_63.py`) to prove the
governed **message-family** reads are index-served on the live SurrealDB 3.2.4 engine, over the
REAL production governed-column emitter, BEFORE the 63b-1 contract freezes.

## SUMMARY BLOCK
- receipt: `brief-base v14 read` · `brief project v7 read`
- state: **done-with-deviations** — mission proven (probe exit 0); the brief's premise was inaccurate (see D1) so the work was an UPGRADE, not a new build.
- D1 (premise correction): the committed probe (commit `4c9a54a`, 2026-08-28) ALREADY contained the message P3/P4 + message C+ probes. They ran over a HAND-TRANSCRIBED overlay (§4.1 verbatim, written when the emitter did not yet exist). The genuine remaining work — and the brief's own stated method — was to switch that overlay to the REAL shipped emitter (`_governed_field_specs`/`_governed_index_statements`). Done.
- D2 (RESOLVED — lead ruled apply, `lore_comms #9004`): the probe's P5 verdict PROSE was stale (it printed "the design §2.3/§4.4 states `scope IS NONE` is a TableScan" though the doc was already corrected to IndexScan on 2026-08-28). **FIXED** in `_verdict()`'s P5 branch (now reads "exactly as design §2.3/§4.4 records … nothing left to correct here"); re-ran → exit 0. See §7 / §9.
- Packages considered: none — no mechanism specified; the extension REUSES in-tree production emitters (no new dependency).
- Reuse ledger: 0 new symbols. REUSED 3 existing production emitters (`loremaster.store.surreal_schema._governed_field_specs` / `_governed_index_statements` / `_define_field`) in place of a hand-transcription — DRY table in §6.
- Graded: `cedb20d` · HEAD-at-report: `cedb20d` · SAME (probe RAN against the working tree = `cedb20d` + my uncommitted edits to `scripts/probe_read_filter_63.py`; the pre-edit file was committed at ancestor `4c9a54a`). Store: spike-surreal TEST `ws://127.0.0.1:18000`, engine 3.2.4.
- decisions-needed: none — lead ruled both (`lore_comms #9004`): D2 P5-prose fix APPLIED (done); emitter-upgrade CONFIRMED for commit (lead commits, not me).
- receipt POINTERS: message index-service proof → §2 (P3), §3 (P4 + leak gate); C+ controls → §4; emitted read fragment + overlay DDL → §1; full self-checking instrument → `scripts/probe_read_filter_63.py` (exit 0); design grounding → `docs/design/2026-08-28-packet63-retrofit-rulings.md` §4.1/§4.3/§4.4.

---

## 0. What changed, and why (the honest framing)

The mission was "extend the probe to the message table." On reading the committed instrument
(`scripts/probe_read_filter_63.py` @ `4c9a54a`, `git diff HEAD` = 0 lines → working tree matched
HEAD exactly) I found it **already** carries:
- **P3** — the message FULL emitter READ fragment (member, 2 keeps) over legacy(NONE)+migrated rows;
- **P4** — the §4.3 step-(2) `id IN $ids AND (fragment)` shape, WITH a #416 leak gate;
- the **message C+ controls** (message `scope=`→IndexScan, `body=`→TableScan, `owner_agent=` alone→TableScan).

So the brief's premise ("it already probes MEMORY + KEEP … BUILD two new message probes") was
inaccurate — the message rows existed. BUT they ran over a **hand-transcribed** `_governed_overlay`,
written in 63a with the explicit note *"the emitter that will produce this … is NOT yet built."*
63a is now CLOSED (git log `cedb20d`), so the emitter EXISTS
(`loremaster.store.surreal_schema._governed_field_specs` / `_governed_index_statements`, verified
via `lore_get_symbol`). The brief's own stated method is to apply *"the shared 63a governed
specs … applied to MESSAGE_TABLE."* That is the real remaining work, and what I did:

**One surgical change** to `scripts/probe_read_filter_63.py` — `_governed_overlay(table)` now
builds its DDL from the REAL production emitter (`_governed_field_specs()` via `_define_field`
+ `_governed_index_statements(table)`) instead of a verbatim §4.1 transcription, and prints the
message overlay DDL as a receipt. This makes the message index-service proof rest on production
code, not a copy of it (DRY / no reference-pattern-to-clone) and INDEPENDENT of the not-yet-built
63b `_message_statements` governed wiring. Stale module/function docstrings corrected in the same
edit. `ruff check` clean; probe **exit 0**.

The change is behaviorally a **no-op** — I verified `_define_field` + `_plain_index` produce DDL
byte-identical to the old transcription (`PRINCIPAL_TABLE='principal'`, `AGENT_TABLE='agent'`,
confirmed by the printed overlay in §1) — but it converts a transcription that could silently
drift from production into a direct use of the shipped emitter.

---

## 1. The REAL production seams under test (emitted, never hand-typed)

**READ predicate** — `authorize_filter(subject, Action.READ, MESSAGE_TABLE).to_surql()` (for a
member this IS `lorerunes.pdp._member_filter`), the real emitter. For the member Subject
`principal=alice, agent=ag_a, keeps={keep:k1, keep:k2}`, the emitted **message** fragment was:

```
((scope = $s_… AND owner_principal = type::record('principal', $p_…) AND owner_agent = type::record('agent', $a_…))
 OR (scope = $s_… AND owner_principal = type::record('principal', $p_…))
 OR scope = $s_…                                   -- server
 OR (scope = $k_… OR scope = $k_…))                -- keep:k1, keep:k2 EXPANDED (never IN — #413)
```
params: `agent-private, alice, ag_a, principal-private, server, keep:k1, keep:k2` (content-addressed
`_param_name`s, collision-free). Flat OR of equalities on indexed columns, keep set EXPANDED, every
node parenthesised (#413 fact-3 + #416) — exactly design §4.2.

**Governed columns/indexes** — the REAL emitter (`_governed_field_specs`/`_governed_index_statements`)
applied to `message` printed exactly (byte-for-byte, the receipt that proves the upgrade is a no-op):
```
DEFINE FIELD OVERWRITE owner_principal ON message TYPE option<record<principal>>;
DEFINE FIELD OVERWRITE owner_agent     ON message TYPE option<record<agent>>;
DEFINE FIELD OVERWRITE scope           ON message TYPE option<string>;
DEFINE INDEX IF NOT EXISTS message_scope           ON message FIELDS scope;
DEFINE INDEX IF NOT EXISTS message_owner_principal ON message FIELDS owner_principal;
```
(`owner_agent` deliberately NOT indexed at 63 — §4.1 named-trigger bound; its C+ control in §4
documents it.) These are applied ON TOP of `generate_message_ddl()` in the throwaway DB, so the
probe proves the exact columns/indexes 63b's `_message_statements` will bake in, before that wiring
lands.

---

## 2. P3 — message FULL member READ fragment → **IndexScan, NO message TableScan** ✅

`SELECT id FROM message WHERE (<the fragment in §1>) EXPLAIN`, over a message table holding BOTH
migrated rows (owner_principal + owner_agent + scope set, spanning every READ disjunct) AND a
legacy row `x_legacy` (real `sender` link, NONE owner_principal/owner_agent/scope). Verdict:
**IndexScan** — `operators=['SelectProject', 'Filter', 'UnionIndexScan', 'IndexScan'×5]`, no
`TableScan` of `message`. Pasted plan (the load-bearing shape):

```
SelectProject(id)
└─ Filter  predicate: scope='agent-private' AND owner_principal=principal:alice AND owner_agent=agent:ag_a
                      OR scope='principal-private' AND owner_principal=principal:alice
                      OR scope='server' OR scope='keep:k1' OR scope='keep:k2'
   └─ UnionIndexScan  branches: 5, table: message
      ├─ IndexScan  access: = 'agent-private'     index: message_scope
      ├─ IndexScan  access: = 'principal-private'  index: message_scope
      ├─ IndexScan  access: = 'server'             index: message_scope
      ├─ IndexScan  access: = 'keep:k1'            index: message_scope
      └─ IndexScan  access: = 'keep:k2'            index: message_scope
```
**Verdict:** the governed message-family list-read is served by a `UnionIndexScan` of five
`message_scope` `IndexScan` children — no whole-table scan of `message`, on the REAL DDL, with
legacy NONE rows present. This is the §4.4 P3 proof. The residual `Filter` re-checks the ANDed
`owner_principal`/`owner_agent` legs (correct: those are the narrowing conjuncts under
`agent-private`/`principal-private`; `owner_agent` is intentionally un-indexed — §4.1).

---

## 3. P4 — §4.3 step-(2) inbox read `id IN $ids AND (fragment)` → **IndexScan + no leak** ✅

`SELECT id FROM message WHERE id IN $ids AND (<fragment>) EXPLAIN` with
`$ids = [message:x_ap (ADMITTED: agent-private/alice/ag_a), message:x_other (EXCLUDED: scope=keep:k9,
not in the subject's keeps)]`. Verdict: **IndexScan** (UnionIndexScan on `message_scope`), no
message TableScan:

```
SelectProject(id)
└─ Filter  predicate: id INSIDE [message:x_ap, message:x_other]
                      AND scope='agent-private' AND owner_principal=principal:alice AND owner_agent=agent:ag_a
                      OR scope='principal-private' AND owner_principal=principal:alice
                      OR scope='server' OR scope='keep:k1' OR scope='keep:k2'
   └─ UnionIndexScan  branches: 5, table: message   (message_scope children, as P3)
```

**LEAK GATE (reads the ACTUAL rows, not the lossy EXPLAIN pretty-print):**
`id IN [x_ap, x_other] AND (fragment)` returned **exactly `['message:x_ap']`**. The excluded
`x_other` (scope `keep:k9`, outside the subject's keeps) was correctly filtered — the outer parens
the emitter SENDS hold, so the id filter bounds the WHOLE OR. The EXPLAIN pretty-print flattens the
parens (`id INSIDE […] AND A OR B OR …`), which — IF the engine evaluated that flattened form — would
leak principal-private/server/keep rows outside the id set (#416, one level out); the leak gate proves
it does NOT.

**Verdict:** the §4.3 two-step drain is BOTH index-served AND correctly scoped on 3.2.4. **No per-id
`type::record` fallback is needed** (the design named it as the fallback for a TableScan degradation;
that degradation did not occur).

---

## 4. C+ controls (message) — the walker is not blind

A green IndexScan verdict with no firing control is a probe passing for the wrong reason
(CLAUDE.md: A PROBE NEEDS A CONTROL). In the SAME run, on the SAME `message` table:

| control | statement | classification |
|---|---|---|
| walker sees an IndexScan | `WHERE scope = $s` (indexed) | **IndexScan** (`SelectProject, IndexScan`) |
| walker sees a TableScan | `WHERE body = $b` (un-indexed) | **TableScan** (`SelectProject, TableScan`) |
| C+ un-indexed governed bound | `WHERE owner_agent = type::record('agent', $a)` ALONE | **TableScan** (`SelectProject, TableScan`) |

All three fired as required. The walker demonstrably CAN see a TableScan on `message`, so the P3/P4
IndexScan verdicts are trustworthy; and `owner_agent`'s TableScan documents the deliberate §4.1
"owner_agent NOT indexed at 63" bound (re-open trigger: the first `owner_agent`-leading LIST read).

---

## 5. Full-run receipts (all nine §4.4 rows, exit 0)

The probe self-checks and exits non-zero on any surprise; it **exited 0**. Verdict table as printed:

```
P1   IndexScan   PASS     memory scope= (option<> + NONE rows, HNSW/FULLTEXT co-resident)
P2   IndexScan   PASS     memory FULL emitter READ fragment
P3   IndexScan   PASS     message FULL emitter READ fragment (legacy+migrated)     ← MISSION
P4   IndexScan   REPORT   message id IN $ids AND (fragment) [REPORT+leak gate]      ← MISSION
P5m  IndexScan   REPORT   memory scope IS NONE
P5x  IndexScan   REPORT   message scope IS NONE
P6   IndexScan   PASS     keep key= after SF-63-4 UNIQUE
C+m  TableScan   PASS     memory owner_agent= alone
C+x  TableScan   PASS     message owner_agent= alone
SELF-CHECK: All controls held; P1–P3 + P6 IndexScanned; NONE keys coexisted; every required plan classifiable.
```
(P1/P2/P6 are memory/keep — outside my mission but re-verified green by the same run; P5 both
tables IndexScan — the design §4.4 already records this "IndexScan, corrected from TableScan"
finding; see D2/§7.) Database minted+dropped: `lore_test:test_3185002_4393e2fa9c…` on
`ws://127.0.0.1:18000` (TEST store; never :18500). Full pasted EXPLAINs are in the probe's own
stdout; the instrument is the committed deliverable (`scripts/probe_read_filter_63.py`).

---

## 6. DRY / reuse ledger

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| (none) | `lore_get_symbol _governed_field_specs` / `_governed_index_statements` / `_define_field` | the three shipped emitters (surreal_schema.py:1143/1158/1060), `_governed_index_statements(table)` is table-parametrised | **REUSED** all three in `_governed_overlay`, replacing the hand-transcription — this IS the extension |

No new reusable symbols were introduced. The change is a REPLACEMENT of a transcription with a call
to the existing production emitter — the ONE-IMPLEMENTATION direction (the same emitter
`_memory_statements` wires in; design §1.2 item 4).

---

## 7. Flags / deviations for the lead (scope law — surfaced, not silently resolved)

- **D1 — premise correction (headline).** The message probes existed at `4c9a54a`; the deliverable
  was an emitter-upgrade, not a new build. No new P3/P4 code was written (that would have been a
  duplicate). If you expected a NET-NEW probe file or net-new probe functions, this is the reason
  there is neither.
- **D2 — P5 verdict PROSE is stale (report-only, pre-existing, NOT edited).** `_verdict()` prints
  "the design §2.3/§4.4 states `scope IS NONE` is a TableScan" and flags a "DESIGN-DOC CORRECTION."
  But the design doc was ALREADY corrected on 2026-08-28 (design §4.4 row P5: *"REPORTED, not
  required — measured IndexScan (= NONE on the scope index) on 3.2.4"*; §2.3 line: *"INDEX-SERVED on
  3.2.4"*), citing this very probe. So the probe now tells the reader to fix a doc that is already
  fixed. **Exact minimal fix** (in `scripts/probe_read_filter_63.py`, `_verdict()`'s P5 branch):
  change the `p5m == 'TableScan' and p5x == 'TableScan'` expectation prose so the IndexScan branch
  reads *"as the design §2.3/§4.4 (already corrected 2026-08-28) records"* rather than *"DESIGN-DOC
  CORRECTION … §2.3/§4.4's stated 'TableScan' expectation is empirically FALSE."* I left it untouched
  to keep the diff surgical to the message mission — **your call** whether to fold it in.
- **No mypy run.** Brief scoped me to the probe; I ran `ruff check` (clean) and the probe itself
  (exit 0 → imports resolve, executes end-to-end). The gate law runs the full typecheck at your
  checkpoint before commit; the change is a trivially-typed list-comprehension over typed emitters.
- **Nothing in `loremaster/` or the schema wiring was touched** (writable set honored:
  `scripts/probe_read_filter_63.py` + this report only). No git state mutated — the lead commits.

## 9. Post-directive (lead `lore_comms #9004`, 2026-09-03)
**P5 prose fixed, exit 0.** Applied the §7 D2 P5 prose-currency fix (`_verdict()`'s P5 branch now
branches on `IndexScan` and states the design was already corrected 2026-08-28, rather than
prescribing a correction). `ruff check` clean; probe re-run → **exit 0** (all controls held; P1–P3
+ P6 IndexScanned; P5 both IndexScan; NONE keys coexisted). Emitter-upgrade confirmed by lead for
commit. I did NOT commit (lead commits the script).

## 8. Bottom line
The governed **message**-family READ (`send`/`drain`/`ack`/`await`/`story`/rollup's message leg,
design §4.3) is **index-served on 3.2.4 by construction**: P3 is a `UnionIndexScan` of
`message_scope` children with no `message` TableScan; P4's two-step inbox read is index-served AND
leak-proof (returned exactly the one admitted id). Proven over the REAL production emitter DDL, with
the walker's TableScan-sight controlled. The §4.1 index set is sound for `message`; the 63b-1
contract can freeze on this. Probe exit 0.
