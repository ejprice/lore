brief-base v14 read
brief project v7 read

# REPORT — probe-63b-ii-b (message READ side, packet 63b wave ii-b)

## SUMMARY BLOCK
- **state:** done.
- **HEADLINE (LEG C):** `DD-3.c: ABORTS-WHOLE`. A single legacy over-cap `ack_note` `to`-edge in an
  unstamped drain window makes the drain `UPDATE ... SET seen_at` **error and abort the WHOLE
  window** (good edge NOT stamped) — standalone AND in the ruled §4.B one-txn shape. TOTAL INBOX
  DENIAL, reproduced with controls on live 3.2.4.
- **LEG A:** every ii-b composed read shape **IndexScans** — no TableScan, no #413 IN-in-OR trap.
- **LEG B:** the §4.B Reading-B one-txn drain works on a clean store (one round trip, visible served + stamped).
- **deviations:** none. (Per spawn brief I commit the probe + this report — overrides brief-base §2's "lead commits".)
- **Packages considered:** none — no NEW mechanism specified; the probe REUSES the surrealdb SDK
  (`query_raw`), the ii-a probe harness, and the REAL production DDL emitters. No hand-roll.
- **Reuse ledger:** 0 new production symbols. Probe REUSES `scripts/probe_read_filter_63.py`'s
  `explain`/`ProbeReport`/`_apply_ddl`/`_create_message`/`_read_fragment`/`_SUBJECT`/connect constants
  (cited, not forked). New helpers (`_relate`, `_create_agent`, `_per_statement`, `_reading_b_txn`,
  `_seen_state`) are probe-local INSTRUMENT, not reusable policy (ii-a has no agent/edge creation).
- **Graded:** 3f6937426808 · HEAD-at-report: 3f6937426808 · SAME.
- **decisions-needed (→ lead / Fable sidecar):**
  1. **Does a drain-UPDATE mitigation ship?** The mechanism is confirmed ABORTS-WHOLE. See §6.
  2. **Reachability (verify, don't assume — #131 class):** the dirty edge needs an over-cap
     `ack_note` to have reached the store. Only `ack` writes `ack_note`, and it is app-capped
     (`_reject_oversize_note`, same 4000, `d4e4778`) coeval with the schema — so a legacy edge may be
     UNREACHABLE. This is a claim about the deployed artifact; §5 says how to verify it against prod.
- **receipt pointers:** instrument `scripts/probe_drain_read_63b_ii_b.py` (self-checking + diagnostic,
  exit 0 this run) · schema fact `loremaster/loremaster/store/surreal_schema.py::_TO_FIELD_SPECS`
  (`ack_note` ASSERT) · drain `MessageLedger.drain` · ack `MessageLedger.ack` · store-ref §1.4/§3/§2/§4.

---

## 0. What was probed, and against what
- **Store:** spike-surreal **TEST** `ws://127.0.0.1:18000` (creds root/spikeroot), throwaway db
  **`lore_test:test_174516_5f79c6534b554acb93b834809d0c58ee`** (minted per-run, dropped on exit).
  Production `:18500` NEVER touched.
- **Schema under test:** the REAL current DDL emitters — `generate_principal_ddl` / `generate_agent_ddl` /
  `generate_message_ddl` (which bakes `message` + governed columns + the `to` relation edge). The READ
  predicate is the REAL emitter output `authorize_filter(_SUBJECT, Action.READ, message).to_surql()`
  (a member: alice/ag_a, keeps {k1,k2}), never a hand-typed WHERE.
- **Instrument:** `scripts/probe_drain_read_63b_ii_b.py`. Plan classification REUSES the ii-a walker
  (`probe_read_filter_63.py`). LEG B/C read the EXACT per-statement engine status via `connection.query_raw`
  (store-ref §3 — `execute_transaction` would launder the text; a probe must not).

---

## 1. LEG A — EXPLAIN plans for ii-b's composed read shapes (ALL IndexScan)

Every ii-b read shape is **index-served, no TableScan of the target, no #413 IN-in-OR trap**.
Instrument-integrity controls held: the walker sees an IndexScan on `to` (out,seen_at) **and** a
TableScan on unindexed columns (`to.session`, `message.body`) — so a real TableScan would be caught.

| probe | statement (WHERE) | plan |
|---|---|---|
| **A1** drain window / `await` peek | `to WHERE out = $agent AND seen_at IS NONE` | **IndexScan** (`to_out_seen_at`; operators `[SelectProject, IndexScan]`) |
| **A2** bare message read_filter | `message WHERE (<emitter fragment>)` | **IndexScan** (re-confirms ii-a P3 on this db) |
| **A3** §4.3 step-2 inbox read | `message WHERE id IN $ids AND (<fragment>)` | **IndexScan** — no per-id `type::record` fallback needed |
| **A4** story | `message WHERE task_id = $t AND (<fragment>)` | **IndexScan** — despite `task_id` being UNINDEXED (the scope UnionIndexScan drives; `task_id` rides as a residual Filter) |
| **A5** rollup message leg | `message WHERE created_at > $since AND (<fragment>)` | **IndexScan** — despite `created_at` being UNINDEXED (same: read_filter carries the plan) |

- **The `await` peek shape is IDENTICAL to A1** — `_comms_await` (server.py) delegates to
  `self.message_ledger.drain` via `InboxAwaiter` (peek just skips the UPDATE), so its `to` read IS the
  drain window SELECT. No separate probe needed.
- **A4/A5 are the notable result:** the leading predicate (`task_id`/`created_at`) is UNINDEXED, yet
  the composed `<unindexed> AND (<indexed OR-disjunction>)` still IndexScans — the planner picks the
  `message_scope` UnionIndexScan and applies the leading predicate as a residual Filter. So splicing
  the read_filter onto `messages_for_task` / `message_activity_since` does **not** introduce a
  dirty-store TableScan. (Extends store-ref §2's leading-column-disjunction fact to an AND-prefixed
  unindexed conjunct.)
- The exact fragment (member, 2 keeps): `((scope = $s AND owner_principal = principal:.. AND
  owner_agent = agent:..) OR (scope = $s AND owner_principal = principal:..) OR scope = $s OR (scope =
  $k1 OR scope = $k2))` — the keeps are EXPANDED to per-value equalities (no `IN`), dodging #413 by
  construction.

---

## 2. LEG B — the §4.B Reading-B one-txn drain works (clean store)

One `BEGIN … COMMIT` (via `query_raw`):
```
LET $edges   = (SELECT in, in.seq AS seq FROM to WHERE out=$me AND seen_at IS NONE ORDER BY seq LIMIT $n);
LET $visible = (SELECT id, scope, owner_principal, owner_agent FROM message WHERE id IN $edges.in AND (<read_filter>));
UPDATE to SET seen_at=$t WHERE out=$me AND in IN $visible.id AND seen_at IS NONE RETURN AFTER;
RETURN $visible;
```
- Over a CLEAN recipient (`rclean`: two good unseen edges) → **per-statement statuses all `OK`**, and
  a read-back shows **both edges stamped** (`seen=True`). The `$edges.in` / `$visible.id` array-pluck
  spellings work; the UPDATE's `RETURN AFTER` gives the stamped edges; the final `RETURN $visible`
  serves the visible set. One round trip, snapshot-consistent. **Positive control PASS.**

---

## 3. LEG C — THE HEADLINE: `DD-3.c: ABORTS-WHOLE`

### 3.0 The `ack_note` bound IS a live DDL ASSERT (not app-layer only)
`loremaster/loremaster/store/surreal_schema.py::_TO_FIELD_SPECS`:
`("ack_note", "option<string>", f"ASSERT string::len($value) <= {MESSAGE_BODY_MAX_CHARS}")`, and the
`to` table is `TYPE RELATION … ENFORCED SCHEMAFULL`. `MESSAGE_BODY_MAX_CHARS = 4000`. So LEG C is
**LIVE**, NOT `N/A`. (The bound is imported into the probe from production, so the probe cannot drift
from the real cap.)

### 3.1 Construction (mirrors the #131 migrate-onto-dirty-store path)
Full current schema → RELATE clean edges → **downgrade** `to.ack_note` to the pre-bound shape
(`OVERWRITE … TYPE option<string>`, no ASSERT — the `_old_to_ddl` "BEFORE ack_note was bounded" world)
→ RELATE the dirty edges (over-cap `ack_note` = 4001 chars, `seen_at`/`acked_at` NONE) → **migrate**
by re-applying the REAL `generate_message_ddl()` (re-lands the ASSERT via `DEFINE FIELD OVERWRITE`).
Per store-ref §1.4 the migration converges SCHEMA not DATA — the dirty edge persists non-conformant.

**C-control (the cap is real):** a fresh over-cap `RELATE` under the CURRENT DDL is **REJECTED**
(`Found 'xxx…' for field ack_note … must conform to: string::len($value) <= 4000`). So the dirty row
is genuinely non-conformant and the probe is valid (not a false clear).

### 3.2 The measured mechanism
| probe | window | result | after (edge seen-state) |
|---|---|---|---|
| **C1** standalone drain UPDATE | `[md_dirty(over-cap,unseen), md_good(unseen)]` | **ERR** on `ack_note` ASSERT | `md_dirty=unseen, md_good=UNSEEN` — the good edge **NOT** stamped |
| **C2** §4.B one-txn drain | same window (md_dirty **visible**) | **whole txn ABORTS** (`UPDATE`→ERR, COMMIT→`Cannot COMMIT: … aborted`) | both **UNSEEN**; `RETURN $visible` never delivered |
| **C-control** outside-window | `routside`: dirty edge ALREADY seen + a good edge | **no error**; good edge stamped | drain's `seen_at IS NONE` filter excludes the dirty edge |

- **The drain `UPDATE` sets ONLY `seen_at`** — and the SCHEMAFULL whole-record re-validation
  (store-ref §1.4) still re-fires the `ack_note` ASSERT on the untouched-but-non-conformant value.
  Exact engine text (C1): `Found 'xxxx…' for field 'ack_note', with record 'to:…', but field must
  conform to: string::len($value) <= 4000`.
- **One statement over the set aborts the whole set** — in C1 the good edge (`md_good`) in the same
  `UPDATE … in IN [dirty, good]` was NOT stamped. In C2 the failed `UPDATE` aborts the entire
  `BEGIN … COMMIT` (store-ref §3), so the whole one-txn drain returns nothing and stamps nothing:
  **TOTAL INBOX DENIAL** — the agent cannot drain ANY of its inbox.
- **The hazard is WINDOW-specific:** a dirty edge already stamped (`seen_at` set) is excluded by
  `seen_at IS NONE` and the drain is unaffected (C-control PASS).

This **empirically corroborates the packet-03b DD-3.c defect** (`cannot write-poison` is true of
`message` but FALSE of `to`, where `ack_note` lives and which drain UPDATEs) at HEAD on 3.2.4, and
**extends it to the ii-b §4.B one-txn Reading-B shape** (which was not yet built when 03b found it).

### 3.3 Two further measured facts that shape the fix
- **C3 — `ack` HEALS a dirty edge, it does NOT die on it.** `ack`'s
  `UPDATE to SET acked_at=$t, ack_note=$note WHERE acked_at IS NONE …` over the over-cap unacked edge
  **succeeds**: the SET replaces the over-cap value with the bounded `$note` and validation passes on
  the NEW value (measured: `ack_note='acked by probe', acked=True`, no error). So `ack` (which WRITES
  `ack_note`) is safe; **`drain` (which does NOT write `ack_note`) is the victim.** Corollary: a
  one-time migration `UPDATE to SET ack_note = string::slice(ack_note,0,4000) WHERE
  string::len(ack_note) > 4000` would heal every dirty edge (the SET conforms — same mechanism as C3).
- **C4 — visible-bounding the stamp is only a PARTIAL mitigation.** In the §4.B shape the `UPDATE` is
  bounded by `in IN $visible.id`. Over a recipient whose dirty edge's MESSAGE is INVISIBLE to the
  reader (excluded by the read_filter), the invisible dirty edge is NOT in `$visible` → NOT touched →
  **no abort, good edge stamped** (measured). BUT a **visible** dirty edge in the window (C2) still
  denies. So bounding the stamp by the visible set saves the drain ONLY when the dirty edge is
  invisible; it does **not** close the hazard for a visible dirty edge.

---

## 4. Store-ref sections this probe confirms / extends
- **§1.4** (whole-record re-validation on write; a narrowed ASSERT poisons later UPDATEs of old rows) —
  CONFIRMED and EXTENDED from `memory` to the `to` EDGE table and to a `SET seen_at`-only write. (C1/C2.)
- **§3** (one failed statement aborts the whole `BEGIN…COMMIT`; the COMMIT then carries a marker-less
  "aborted" notice) — CONFIRMED as the total-denial amplifier. (C2 statuses:
  `[not-executed, not-executed, ERR(ack_note), cancelled, Cannot COMMIT]`.)
- **§2** (`IN`-in-`OR` #413 TableScan trap; explicit-projection-reads-None) — the emitter EXPANDS keeps
  to per-value equalities (no `IN`), and every LEG-A composition IndexScans (A1–A5). Extends §2's
  leading-column-disjunction fact to an unindexed AND-prefix (A4/A5).
- **§4** (ENFORCED live on `to`; RELATE needs bound-RecordID endpoints) — RELATE worked only with real
  `agent`+`message` endpoints and bound RecordIDs, as §4 requires.

## 5. Reachability — a DECISION-POINT for the lead (verify, don't assume; #131 class)
The mechanism (§3) is MEASURED. Whether a dirty edge can EXIST in production is a separate,
artifact-level question I did NOT settle (and must not — I never touch `:18500`):
- **Only `ack` writes `ack_note`** (`drain` sets `seen_at`; `send` never sets `ack_note`).
- **`ack` is app-capped** by `_reject_oversize_note` (same 4000 bound), introduced in **`d4e4778`
  (packet 03b)**; the `to.ack_note` DDL ASSERT was introduced in **`1a6010f` (packet 03b)**; the
  original `message`/`to` schema (`df59f76`) shipped `ack_note` UNBOUNDED. All three are ancestors of
  HEAD. The `ack` VERB is itself the 03b comms surface — so the app cap has plausibly guarded every
  `ack_note` write since the table first went live.
- **Therefore a legacy over-cap edge may be UNREACHABLE today** — the DDL ASSERT would be
  defense-in-depth against a future raw/non-`ack` write path, never firing on real data.
- **This is a belief about the deployed artifact, not a measurement.** To settle it, the lead/sidecar
  should count over-cap `ack_note` `to`-edges on production (`SELECT count() FROM to WHERE
  string::len(ack_note) > 4000 GROUP ALL` against `:18500`) OR make the deploy smoke assert it. If the
  count is 0 and stays 0, DD-3.c is latent-not-live; if >0, the drain-denial is a live outage the day
  a recipient with such an edge drains.

## 6. Candidate mitigations (for the Fable sidecar to weigh — I recommend, it rules)
1. **DROP the `to.ack_note` DDL ASSERT (keep the app cap).** The ASSERT protects nothing the app cap
   doesn't (only `ack` writes `ack_note`, always app-capped), and it is the sole cause of the
   drain-denial re-validation. Trade: loses the store-level defense-in-depth backstop against a future
   non-`ack` write path. Simplest, closes the hazard entirely.
2. **Keep the ASSERT + a one-time heal migration at deploy.** `UPDATE to SET ack_note =
   string::slice(ack_note,0,4000) WHERE string::len(ack_note) > 4000` BEFORE any drain runs (the SET
   conforms — C3 proves it lands). Must run at/ahead of the pkt-65 deploy. Keeps the backstop.
3. **Visible-bounding the drain stamp (`in IN $visible.id`) — NOT sufficient alone** (C4): it saves
   the drain only for an INVISIBLE dirty edge; a visible one still denies. Useful as depth, not a fix.
- **Do NOT** reach for an `UPDATE to SET seen_at` on a table where any other field ASSERT can be
  violated by a legacy row, without one of the above — that is the DD-3.c shape verbatim.

## 7. How to re-run (one receipt for the lead)
```
uv run python scripts/probe_drain_read_63b_ii_b.py    # exit 0 this run; prints its own throwaway db name
```
Self-checking (exit non-zero on a surprise): LEG-A REQUIREs (A1 drain SELECT + A2 bare read_filter
must IndexScan) + walker controls (IndexScan AND TableScan both visible) + the LEG-C C-control (over-cap
RELATE under the current DDL must be REJECTED) + the LEG-B/C positive controls (clean one-txn stamps;
dirty-outside-window unaffected). The LEG-C headline (ABORTS-WHOLE / GRACEFUL / N/A) is DIAGNOSTIC —
printed, never an exit gate, per the "a probe reports the mechanism, it does not pass/fail the hazard" rule.
