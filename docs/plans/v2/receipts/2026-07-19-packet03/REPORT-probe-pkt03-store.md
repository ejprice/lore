# REPORT-probe-pkt03-store

brief-base v4 read

- **state:** done
- **deviations:**
  - Probe 1's first run had a BROKEN INSTRUMENT (endpoints bound as strings → the positive control failed). Caught by the control, fixed, re-run. The string leg was retained as a deliberate instrument control.
  - Probe 3 leg B parse-errored on `RELATE $msg.id->…` (a new §7 gotcha); re-run as probe3b with legal syntax. Probe 3 leg D was re-run hardened (probe3b) because `BATCH 1000` could mask a persisted reset behind a session cache.
  - Added 4 probes beyond the 5 briefed (3c, 4b, 4c, 5b/5c/5d) — each closed a question a briefed probe opened. Flagged individually below.
- **decisions-needed:**
  1. **Finding #124's stated mechanism is WRONG** (§Probe 5). "Commits report success, rows missing" is an artifact of the SDK's `query()`; the engine loses nothing. The finding text and reference §5 both need correcting — operator's call whether I file it or the lead does.
  2. Reference doc has 2 self-contradictions + 4 now-settled `[UNVERIFIED]`s (§REFERENCE-DOC CORRECTIONS). Report-only per brief; not edited.
- **receipt pointers:** Probe 1 §PROBE 1 · Probe 2 §PROBE 2 · Probe 3 §PROBE 3 · Probe 4 §PROBE 4 · Probe 5 §PROBE 5 · scripts in `/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/af347ebc-8215-4484-b5d3-3d94c07f7eaf/scratchpad/pkt03-probes/`

Engine: surrealdb 3.1.5 @ `ws://127.0.0.1:18000` (spike-surreal, TEST). Production `:18500` never contacted — `_probe.py:26` carries a hard `assert "18000" in URL`. Every probe minted its own `test_<pid>_<uuid4>` database and reaped it (`REMOVE DATABASE` receipt at the tail of every run).

---

## PROBE 1 — Does RELATE validate its `out` endpoint?

**Question:** #105 recorded the `in` side only. Packet 03's shape is `RELATE $message -> to -> $agent`, so the caller-supplied side is **`out`** — unrecorded behaviour.

**Script:** `probe1_relate_out.py`. Schema: `message` / `agent` / `to TYPE RELATION IN message OUT agent`. Five legs.

### The instrument control fired first (and this matters)

Run 1 — all four legs, including the positive control, returned:

```
[0] ERR: "Cannot execute RELATE statement where property 'in' is: 'message:m_real'"
```

The control failing is what exposed it: endpoints were bound as **strings**, and reference §4's "endpoints must be BOUND RecordID params" covers this. Had I only run the bogus legs I would have reported "RELATE rejects bad ids" — **the exact opposite of the truth.**

That failure is itself a result worth keeping: **a bare `str` endpoint is rejected LOUDLY.** Retained as leg 5.

### Run 2 — verbatim

```
===== LEG: CONTROL both real  (message:m_real -> to -> agent:a_real)
    [0] OK: [{'id': to:mwl4g4ktg4tfj41az0ld, 'in': message:m_real, 'out': agent:a_real, 'tag': 'e_control'}]
===== LEG: BOGUS OUT  (message:m_real -> to -> agent:a_ghost)
    [0] OK: [{'id': to:70nab2nh4f63wimzr539, 'in': message:m_real, 'out': agent:a_ghost, 'tag': 'e_bogus_out'}]
===== LEG: BOGUS IN  (message:m_ghost -> to -> agent:a_real)
    [0] OK: [{'id': to:zpb2e35nb7lt779tk0rl, 'in': message:m_ghost, 'out': agent:a_real, 'tag': 'e_bogus_in'}]
===== LEG: BOTH BOGUS  (message:m_ghost -> to -> agent:a_ghost)
    [0] OK: [{'id': to:7y7i1fucdyjupx3m24tk, 'in': message:m_ghost, 'out': agent:a_ghost, 'tag': 'e_both_bogus'}]
===== LEG: STRING endpoints (not RecordID)  ('message:m_real' -> to -> 'agent:a_real')
    [0] ERR: "Cannot execute RELATE statement where property 'in' is: 'message:m_real'"
```

**Positive control: PASSED** (both-real wrote a healthy edge, readback proves the probe can see one).

### Can a reader distinguish a dangling edge from a live one?

```
--- SELECT tag, in, out, in.body AS in_body, out.name AS out_name FROM to ORDER BY tag;
  {'tag': 'e_bogus_in',   'in': message:m_ghost, 'in_body': None,    'out': agent:a_real,  'out_name': 'scout'}
  {'tag': 'e_bogus_out',  'in': message:m_real,  'in_body': 'hello', 'out': agent:a_ghost, 'out_name': None}
  {'tag': 'e_both_bogus', 'in': message:m_ghost, 'in_body': None,    'out': agent:a_ghost, 'out_name': None}
  {'tag': 'e_control',    'in': message:m_real,  'in_body': 'hello', 'out': agent:a_real,  'out_name': 'scout'}

--- SELECT tag, in, out FROM to ORDER BY tag FETCH in, out;
  {'tag': 'e_bogus_in',   'in': None, 'out': {...a_real...}}
  {'tag': 'e_bogus_out',  'in': {...m_real...}, 'out': None}
  {'tag': 'e_both_bogus', 'in': None, 'out': None}
  {'tag': 'e_control',    'in': {...m_real...}, 'out': {...a_real...}}
```

Distinguishable **only if you project a field or FETCH, and then check for `None`** — which is reference §2's "a missing SELECT projection reads `None`, not a `KeyError`" silent-degradation trap, one level deeper.

**The traversal cannot distinguish at all:**

```
--- SELECT ->to->agent AS recipients FROM message:m_real;
  [{'recipients': [agent:a_ghost, agent:a_real]}]
```

`agent:a_ghost` appears in the recipient list as a first-class member. Meanwhile `SELECT count() FROM agent` = **1**, and `SELECT * FROM agent` returns only `a_real` — **no phantom node is materialised.** So the recipient list contains an id that exists nowhere in the node table, and the natural graph query reports it as a recipient.

**VERDICT: `out` is NOT validated. A non-existent `out` silently writes a dangling edge — identical to #105's `in` behaviour, and now on the CALLER-SUPPLIED side.**

**The conclusion the brief asked for, stated explicitly:** an application-level "is this recipient registered?" check is **the only thing** standing between a typo'd recipient name and a permanent, silent delivery receipt for an agent who does not exist. It is therefore a **REQUIRED, PINNED INVARIANT of the new module, not a nicety.** `#105` must be widened from "latent — we never hard-delete" to **"LIVE the moment `send` accepts a recipient name from a caller"**, because packet 03's fan-out does exactly that.

---

## PROBE 2 — UNIQUE(in,out) on an edge, across an endpoint hard-delete

**Question:** reference §4 flags the #7061 cascade interaction `[UNVERIFIED]`: RELATE → hard-delete endpoint → re-RELATE.

**Script:** `probe2_unique_cascade.py`, with `DEFINE INDEX to_unique ON to FIELDS in, out UNIQUE`.

### B. POSITIVE CONTROL — is UNIQUE actually enforcing? (run FIRST, deliberately)

```
--- first RELATE m1->a1
    [0] OK: [{'id': to:j20nusxwfuqa2ipf56fn, 'in': message:m1, 'out': agent:a1, 'tag': 'first'}]
--- DUPLICATE RELATE m1->a1 (MUST fail if UNIQUE enforces)
    [0] ERR: 'Database index `to_unique` already contains [message:m1, agent:a1], with record `to:j20nusxwfuqa2ipf56fn`'
--- NEGATIVE control — a DIFFERENT pair m1->a2 must SUCCEED
    [0] OK: [{'id': to:32xndsp6mv53o0e8k1dd, ... 'tag': 'different-pair'}]
```

Both directions shown: the duplicate is rejected, a different pair is accepted. **The index is genuinely enforcing**, so a later passing re-RELATE is meaningful.

### A. Does deleting an endpoint remove the edge?

```
--- DELETE agent:a1                          [0] OK: []
--- edges after out-endpoint delete          [0] OK: [ {tag:'different-pair', in:message:m1, out:agent:a2} ]
--- count of to rows                         [0] OK: [{'count': 1}]
```

The `first` edge is gone. Same for the **in** side:

```
--- DELETE message:m1                        [0] OK: []
--- edges after in-endpoint delete           [0] OK: []
```

**§2's claim that RELATION edges self-delete when an endpoint is deleted is CONFIRMED, in BOTH directions.**

### C. Ghost index entry?

```
--- recreate agent:a1                        [0] OK: [{'id': agent:a1, 'name': 'alpha2'}]
--- re-RELATE m1->a1                         [0] OK: [{'id': to:kinrtyy2sd3yddcph4tp, ... 'tag': 're-relate'}]
--- DELETE agent:a2                          [0] OK: []
--- re-RELATE m1->a2 with a2 ABSENT          [0] OK: [{'id': to:smqg25i9nv4gghfgpdk4, ... }]
--- (after DELETE message:m1) re-RELATE m1->a1  [0] OK: [{'id': to:yp811zlid5f63hfdiasu, ...}]
--- INFO FOR TABLE to
    {'indexes': {'to_unique': 'DEFINE INDEX to_unique ON to FIELDS in, out UNIQUE'}, ...}
```

Every re-RELATE succeeded, in all three variants (recreated endpoint / absent endpoint / in-side delete). No ghost entry.

**VERDICT: the #7061 cascade hazard is ABSENT on 3.1.5.** Endpoint deletion cascades the edge away *and* cleans its UNIQUE index entry; re-RELATE succeeds. `UNIQUE(in,out)` on `to` is safe to ship. §4 and §8's `[UNVERIFIED]` flags are now settled.

---

## PROBE 3 — `sequence::nextval` under the real write shape

**Scripts:** `probe3_sequence.py`, `probe3b_sequence.py` (hardened D + legal B), `probe3c_seq_concurrent.py`.

### A. Spelling — settling the §5-vs-§8 contradiction

```
--- RETURN sequence::nextval("message_seq")   [0] OK: 0
--- RETURN sequence::next("message_seq")
    Parse error: Invalid function/constant path, did you maybe mean `sequence::nextval`
--- RETURN sequence::nextval()
    [0] ERR: 'Incorrect arguments for function sequence::nextval()(). Expect a sequence name'
```

**SETTLED: `sequence::nextval("<name>")` is the only correct spelling.** `sequence::next` does not exist (parse error, with the engine itself suggesting `nextval`). §5 was right; **§8's `[UNVERIFIED]` line is stale and must be deleted** — the file contradicting itself is a real defect in our own reference (listed below).

### B. The real shape — nextval + CREATE + 3× RELATE in ONE transaction

First attempt was a **parse error** — a new gotcha:

```
RELATE $msg.id->to->$a1 SET seen_at = NONE;
Parse error: Unexpected token `.`, expected a relation arrow
 --> [5:24]
```

**A field access is not a legal RELATE endpoint.** The working form binds the id into the LET: `LET $msg = (CREATE ONLY message CONTENT {...}).id;` then `RELATE $msg->to->$a1`.

With legal syntax (`probe3b`), 3 rounds:

```
--- txn round 0 : [0..2] OK  [3] to:69oiidjj… in:message:wa2jy8b6… out:agent:a1
                             [4] …out:agent:a2  [5] …out:agent:a3  [6] OK: 0  [7] OK: None
--- txn round 1 : … [6] OK: 1
--- txn round 2 : … [6] OK: 2
--- messages : [{'body':'round-0','seq':0}, {'body':'round-1','seq':1}, {'body':'round-2','seq':2}]
--- edge count (must be 9) : [{'count': 9}]
```

Distinct + monotonic; the whole mint+create+fan-out composes in one transaction.

**Concurrency (`probe3c`, 16-way × 20 rounds = 320 txns, the full shape):**

```
attempts      : 320   statuses={'OK': 320}
message rows  : 320  (expect 320)
distinct seq  : 320  (expect 320)
monotonic     : True
min/max seq   : 0/319
gaps          : 0
edge rows     : [{'count': 960}]  (expect 960)
DUPLICATES    : []
```

**320/320 committed, zero conflicts, zero duplicates, zero gaps.** Note the contrast with Probe 4: the fan-out shape has no hot row, so it does not contend.

### C. An aborted transaction burns the number

```
--- txn that mints then violates (THROW)
    [0] OK: None
    [1] ERR: 'The query was not executed due to a failed transaction'
    [2] ERR: 'The query was not executed due to a failed transaction'
    [3] ERR: 'An error occurred: deliberate abort'
    [4] ERR: 'Cannot COMMIT: the transaction was aborted due to a prior error'
--- rows after abort ('doomed' must be ABSENT)   [0] OK: []
--- next value after the abort                   [0] OK: 2
```

Value `1` was consumed by the aborted txn and never reappears — the sequence jumps `0 → 2`. **NOT gapless, confirmed.** (Also a live re-confirmation of §3's "classify the FIRST failed statement": the real cause `deliberate abort` sits at index [3], with cascade notices at [1]/[2] and the marker-less COMMIT error last.)

### D. Re-DEFINE SEQUENCE — does any variant RESET it? (the catastrophic case)

Hardened in `probe3b`: counter pushed to 23, then each variant, **read back on a FRESH CONNECTION** to defeat any `BATCH 1000` session cache.

```
--- value before any re-DEFINE                            [0] OK: 23
--- DEFINE SEQUENCE OVERWRITE message_seq;                [0] OK: None
---   nextval on the SAME connection                      [0] OK: 24
---   nextval on a FRESH CONNECTION                       [0] OK: 25
---   INFO FOR DB  sequences: {'message_seq': 'DEFINE SEQUENCE message_seq BATCH 1000 START 0'}
--- DEFINE SEQUENCE OVERWRITE message_seq START 0;        [0] OK: None
---   nextval same connection                             [0] OK: 26
---   nextval on ANOTHER fresh connection                 [0] OK: 27
--- DEFINE SEQUENCE IF NOT EXISTS message_seq;            [0] OK: None
---   nextval after INE re-apply                          [0] OK: 28
```

And plain `DEFINE SEQUENCE` with no clause (from `probe3`):

```
--- DEFINE SEQUENCE message_seq;   [0] ERR: "The sequence 'message_seq' already exists"
```

**NO variant resets the counter — not even `OVERWRITE … START 0`, read from a fresh connection.** The catastrophic boot-reset scenario does **not** exist on 3.1.5.

**Which clause must the schema use?** `IF NOT EXISTS`. Per §1.1's decision-rule *logic* (not its table, which has no SEQUENCE row): the rule picks `OVERWRITE` only where a changed definition must land. Here bare `DEFINE` **raises** on re-apply, which would hard-fail `ensure_ready()` on every boot after the first — the same boot-time-crash failure mode §1.1 cites for flipping INDEX to `OVERWRITE`. `IF NOT EXISTS` is a clean no-op. `OVERWRITE` is *also* safe (it does not reset) but buys nothing, and would silently discard a future changed `BATCH`/`START` — I recommend `IF NOT EXISTS` and note the residual: **a changed `BATCH`/`START` will not migrate**, the same live-and-unfixed hazard class §8 records for ANALYZER/INDEX.

**VERDICT: `sequence::nextval("<name>")` confirmed in the real shape; distinct + monotonic at 16-way; aborted txns burn numbers (gaps are real); no re-DEFINE variant resets. Schema uses `DEFINE SEQUENCE IF NOT EXISTS`.**

---

## PROBE 4 — write-once CAS stamps on an edge

**Scripts:** `probe4_cas.py`, `probe4b_cas_errors.py`, `probe4c_indistinguishable.py`.

### A/B. First stamp lands; second is a no-op

```
--- stamp #1 (guarded)
    [0] OK: [{'id': to:ei079asf…, 'in': message:m1, 'out': agent:a1, 'seen_at': '2020-01-01T00:00:00Z'}]
--- stamp #2 (guarded, DIFFERENT value 2099 — must be a NO-OP)
    [0] OK: []
--- row after stamp #2 (must STILL read 2020)
    [0] OK: [{… 'seen_at': '2020-01-01T00:00:00Z'}]
--- guarded stamp on the OTHER field (acked_at)
    [0] OK: [{'acked_at': '2021-06-06T00:00:00Z', … 'seen_at': '2020-01-01T00:00:00Z'}]
```

**The return value IS the discriminator:** a winning stamp returns the row (1-element list); a no-op returns `[]`. Neither raises. The guard is per-field — `acked_at` stamps independently while `seen_at` is already set.

### C. POSITIVE CONTROL — the guard is what does the work

```
--- UPDATE without WHERE (must overwrite to 2099)
    [0] OK: [{… 'seen_at': '2099-12-31T00:00:00Z'}]
--- row after unguarded update
    [0] OK: [{… 'seen_at': '2099-12-31T00:00:00Z'}]
```

Unguarded **does** overwrite. So the write-once behaviour is attributable to `WHERE … IS NONE`, not to some other property of edge rows.

### D. 16-way race on ONE edge, ×20 rounds

```
  OK  round  0: claimed=1 statuses={'OK': 15, 'ERR': 1} final=[{'seen_at':'2020-…','winner':'racer-0'}]
  OK  round  5: claimed=1 statuses={'ERR': 2, 'OK': 14} final=[{'seen_at':'2021-…','winner':'racer-1'}]
  OK  round  6: claimed=1 statuses={'ERR': 4, 'OK': 12} final=[{'seen_at':'2023-…','winner':'racer-3'}]
  … (all 20 rounds)
  OK  round 19: claimed=1 statuses={'OK': 16}           final=[{'seen_at':'2020-…','winner':'racer-0'}]
```

**Exactly one winner in all 20 consecutive rounds; no lost update; the winner varies across racers** (racer-0/1/3 all won rounds, so it is not an artifact of one connection always going first).

### The ERR entries — what are they? (`probe4b`, 16-way × 10)

```
total ERR entries        : 36
carrying 'can be retried' : 18

  x18   'The query was not executed due to a failed transaction'
  x18   'Cannot COMMIT: Transaction conflict: Resource busy. This transaction can be retried'
```

**These are genuine retryable optimistic-concurrency conflicts** carrying §3's canonical `"can be retried"` marker. This is load-bearing: **a racer that conflicts is NOT a legitimate loser — it never ran.** Without a retry it would report "already acked" when in fact nothing happened.

### The distinguishability trap (`probe4c`) — not briefed, found while probing B

```
########## CONTROL — the successful first stamp (must be NON-empty)
1. fresh stamp on my own edge   [0] OK: [{… 'out': agent:mine, 'seen_at': '2020-01-01T00:00:00Z'}]
########## The three no-op causes, same statement
2. ALREADY STAMPED              [0] OK: []
3. NO SUCH EDGE (fabricated id) [0] OK: []
4. NOT MY EDGE (agent:other)    [0] OK: []
```

**All three no-op causes are byte-identical `[]`.** A separate `SELECT` *does* distinguish them (nonexistent → `[]`; other's edge → a row with no `seen_at`). So the CAS return alone cannot tell "idempotent re-ack" from "forged edge id" from "authorisation failure" — and with the conflict case above, that is **four** distinct conditions collapsing onto one empty list.

**VERDICT: the CAS stamp works exactly as designed — first wins, second no-ops, exactly one winner at 16-way — but the empty return is FOUR-WAY AMBIGUOUS (already-stamped / no-such-edge / not-yours / never-ran-due-to-conflict), and the conflict case is only removed by riding the shared retry driver.**

---

## PROBE 5 — table-definition coverage

**Scripts:** `probe5_table_coverage.py`, `probe5b_124_mechanism.py`, `probe5c_control_and_retry.py`, `probe5d_type_any_edge.py`.

### A. Does RELATE auto-create an undefined edge table?

```
--- RELATE onto never-defined table 'probe_edge'
    [0] OK: [{'id': probe_edge:4nj6wuyv…, 'in': message:m1, 'out': agent:a0, 'who': 'solo'}]
--- INFO FOR DB -> tables
    'probe_edge': 'DEFINE TABLE probe_edge TYPE ANY SCHEMALESS PERMISSIONS NONE'
```

**Yes — and as `TYPE ANY`, NOT `TYPE RELATION`.** Chased in 5d below.

### B/C. Concurrent first-writes, undefined vs defined (16-way × 12 trials)

```
########## B. UNDEFINED edge table
        ok UNDEFINED trial  0: committed=1 readable=1
        ok UNDEFINED trial  4: committed=4 readable=4
        … ==> UNDEFINED: committed=22 lost=0
########## C. POSITIVE CONTROL — DEFINED edge table, same load
        ok DEFINED   trial  0: committed=16 readable=16
        … ==> DEFINED  : committed=192 lost=0
```

**Zero loss in both** — but look at `committed`: only **22 of 192** attempts committed against undefined tables, vs **192 of 192** defined. That is loud failure, not silent loss. It contradicts #124's stated mechanism, so I chased it.

### #124's mechanism, settled (`probe5b`) — NOT BRIEFED, and it inverts the finding

Same concurrent load, two instruments over identical work:

```
=== INSTRUMENT 1: the SDK's query() (statement[0] only)
  attempted           : 160
  query() reported OK : 160
  rows actually there : 10
  APPARENT SILENT LOSS: 150

=== INSTRUMENT 2: full per-statement check (execute_transaction semantics)
  attempted           : 160
  all-statements OK   : 10
  (per-trial mismatches printed above; none printed = zero loss)

=== verbatim error texts
  x150  'per-statement ERR: The query was not executed due to a failed transaction'
  x150  'per-statement ERR: Cannot COMMIT: Transaction conflict: Resource busy. This transaction can be retried'
```

**#124's "silent data loss" is MASKED RETRYABLE CONFLICTS.** In `BEGIN; CREATE …; COMMIT;` statement[0] is the `BEGIN` — always `OK` — so the SDK's `query()` returns without raising on a fully rolled-back transaction. The "missing rows" were **never committed**. The engine drops nothing.

**Both required controls (`probe5c`):**

```
=== CONTROL 1: query() instrument against a DEFINED table
  query() reported OK : 160
  rows actually there : 160
  APPARENT LOSS       : 0   <-- must be 0

=== CONTROL 2: UNDEFINED table WITH bounded client-side retry
  ok  trial  0: landed=16/16 readable=16
  … (all 10 trials 16/16)
  ==> landed=160/160 exhausted=0 total_attempts=310
```

Control 1 proves the instrument **discriminates** (it does not report loss where there is none), so the 150 in probe5b is real and specific to the undefined case. Control 2 proves the conflicts are **fully recoverable**: with a bounded retry every one of 160 lands, zero exhausted, ~1.9 attempts average.

> ⚠ **Scope honesty:** I did not re-run #124's original 480-row harness (`scratchpad/102-recovery/`). My claim is that this shape reproduces #124's exact signature under `query()` and that it vanishes under full per-statement checking. That is strong evidence for the mechanism, not a byte-for-byte re-derivation of the original run. **INCONCLUSIVE** on whether the original harness used `query()` — someone should read those scripts before the finding text is rewritten.

### D. Node table (#124's own shape)

```
        ok NODE-UNDEF trial  0: committed=1 readable=1
        … (12 trials, all committed=1 readable=1)
```

Same picture: one winner per trial, no loss among committers.

### 5d — is an auto-created `TYPE ANY` edge still an edge? (not briefed)

```
########## AUTO-CREATED (TYPE ANY, no DDL)
---   INFO: auto_edge          {'events': {}, 'fields': {}, 'indexes': {}, …}      <-- NO in/out field defs
---   DELETE agent:a1          [0] OK: []
---   edges AFTER endpoint delete   [0] OK: []                                     <-- still cascades
########## CONTROL: DEFINED TYPE RELATION
---   INFO: typed_edge  'in': 'DEFINE FIELD in ON typed_edge TYPE record<message>…'
                        'out': 'DEFINE FIELD out ON typed_edge TYPE record<agent>…'
---   edges AFTER endpoint delete   [0] OK: []                                     <-- cascades
########## Does TYPE RELATION IN/OUT reject a WRONG-TABLE endpoint?
--- typed_edge  message:m1 -> other:o1
    [0] ERR: "Couldn't coerce value for field `out` of `typed_edge:53co…`:
              Expected `record<agent>` but found `other:o1`"
--- auto_edge   message:m1 -> other:o1
    [0] OK: [{'id': auto_edge:yifrh4ne…, 'out': other:o1, 'tag': 'wrong'}]         <-- accepted!
########## And a NONEXISTENT-table endpoint on the typed edge
--- typed_edge message:m1 -> agent:ghost
    [0] OK: [{'id': typed_edge:i2uz15d9…, 'out': agent:ghost, 'tag': 'ghost'}]     <-- still dangling
```

Cascade survives on `TYPE ANY`. But `TYPE RELATION IN … OUT …` buys a **type** guard (a wrong-*table* endpoint is rejected by field coercion) that `TYPE ANY` does not. It does **not** buy an **existence** guard — re-confirming Probe 1 on a fully-typed edge.

**VERDICT: `DEFINE TABLE … TYPE RELATION` before first write is MANDATORY — but for two reasons neither of which is "silent row loss".** (1) Without it, concurrent first-writes storm with retryable conflicts (22/192 first-pass success). (2) Without it the table is `TYPE ANY`, losing the in/out type constraint that is the *only* endpoint validation the engine offers.

---

## CONSEQUENCES FOR THE BUILD

1. **A recipient-exists check is a REQUIRED, PINNED invariant of `send`.** The engine validates neither `in` nor `out`. A typo'd recipient produces a permanent, silent delivery receipt for a nonexistent agent, and `->to->agent` traversal reports it as a real recipient. The pin must use a **recipient name that does not exist** and assert `send` REJECTS it — a fixture where every recipient is registered cannot discriminate (this is the parameter-value-monoculture trap in CLAUDE.md).
2. **Resolve recipient names to `RecordID`s through a checked lookup, and pin that the check runs BEFORE any RELATE.** A partially-validated fan-out is the hazard: N−1 good edges plus one dangling receipt. Decide and pin whether `send` to a mixed batch is all-or-nothing (recommend: validate all recipients, then fan out, in one transaction — Probe 3 leg B proves mint+create+N-RELATE composes atomically).
3. **Bind endpoints as `RecordID` objects, never `str`.** A bare string raises `"Cannot execute RELATE statement where property 'in' is: …"`. This is a *helpful* loud failure — do not "fix" it by pre-formatting ids into strings.
4. **`RELATE $expr.field->…` is a PARSE ERROR.** Bind the id into the LET: `LET $msg = (CREATE ONLY message CONTENT {…}).id;`.
5. **`DEFINE TABLE to TYPE RELATION IN message OUT agent` is mandatory in `generate_ddl` before first write** (both reasons in Probe 5's verdict). Same for the `message` node table.
6. **`UNIQUE(in, out)` on `to` is SAFE to ship** — cascade hazard absent, index entry cleaned on endpoint delete, re-RELATE succeeds. It gives idempotent fan-out (a duplicate recipient in one `send` is rejected rather than double-delivered). Note it makes a duplicate a **loud ERR**, so `send` must decide: dedupe recipients client-side, or catch it. Recommend dedupe before the RELATE loop.
7. **`message.seq` uses `sequence::nextval("<name>")`; the schema declares `DEFINE SEQUENCE IF NOT EXISTS`.** No re-DEFINE variant resets, so `ensure_ready()` re-application at every boot is safe. **Gaps are REAL** (an aborted txn burns a number) — so `seq` is a monotonic ordering key, never a count, never a "how many messages" display, and never a gapless human handle. Pin that a consumer tolerates gaps.
8. **A changed `BATCH`/`START` on the sequence will NOT migrate under `IF NOT EXISTS`** — same silent-no-op class as §8's ANALYZER/INDEX hazards. Ledger it now rather than rediscovering it.
9. **The CAS stamp MUST ride `retry_on_conflict`.** 16-way contention on one edge produced genuine `"can be retried"` conflicts (18 of 160 txns). **Routing is not sharing** (CLAUDE.md #102): use the driver's classification, do not match the marker locally. Prove by mutation — move the marker, the stamp's pin must go red.
10. **`seen_at`/`acked_at` must be `option<datetime>`** so `IS NONE` is the CAS guard, and the write-once property gets a pin using a **different second value** than the first (a same-value second stamp cannot distinguish a working guard from a broken one).
11. **The four-way-ambiguous empty return must be resolved by the module, not passed to the caller.** `[]` means already-stamped OR no-such-edge OR not-your-edge OR never-ran-due-to-conflict. Fix #4 with the retry driver; disambiguate the rest with a follow-up `SELECT` (which does distinguish them) and return a typed outcome. Pin all three surviving cases separately — a test that only exercises "already stamped" passes for a build that silently accepts forged edge ids.
12. **Scope the CAS by ownership** (`AND out = $me`) so an agent cannot stamp another agent's edge — and pin it with a **negative** case, since the rejection is invisible in the return value.
13. **Never send this module's multi-statement work through `query()`.** Probe 5b measures the cost precisely: 160/160 false successes over 10 real ones. Use `execute_transaction` (reference §3).
14. **The fan-out shape itself does not contend** (320/320, zero conflicts) — contention lives on the CAS stamp, not the send. Size retry expectations accordingly; do not over-engineer `send`.

## REFERENCE-DOC CORRECTIONS

Report-only per brief — `docs/reference/surrealdb-31-capabilities.md` NOT edited.

| file:line | Status | Proposed correction |
|---|---|---|
| `:274` | **INCOMPLETE — the dangerous half is missing** | Heading says "`RELATE` does NOT validate that **`in`** exists". Probed: **neither `in` NOR `out` is validated**, in any combination. Retitle to "does NOT validate that its endpoints exist" and add: `out` is the caller-supplied side in a `message->to->agent` fan-out. |
| `:277–281` | **STALE — "latent today" is about to be false** | "*Latent today* only because agents are retired, never hard-deleted, and callers pass store-resolved ids." Packet 03's `send` takes caller-supplied recipients → **the second clause fails on arrival.** Re-mark #105 as LIVE for packet 03 and name the app-level check as the mitigation. |
| `:287–290` | **SETTLED — remove `[UNVERIFIED]`** | The #7061 cascade interaction is **ABSENT on 3.1.5** [PROBED 2026-07-19]: endpoint delete cascades the edge (both directions) and cleans the UNIQUE entry; re-RELATE succeeds (recreated endpoint / absent endpoint / in-side delete). |
| `:338–344` | **WRONG MECHANISM — the most important correction here** | §5 states auto-schema creation "LOSES DATA SILENTLY … commits report success, yet an independent read finds rows missing". Measured: those commits **did not succeed** — they were retryable conflicts masked by the SDK's `query()` (statement[0]=`BEGIN`). Under full per-statement checking: 10 OK / 10 readable, **zero loss**; with retry, 160/160 land. Rewrite as: *"concurrent first-writes against an undefined table storm with retryable conflicts; via `query()` these are INVISIBLE and read as silent loss."* **The conclusion (every table in `generate_ddl` before first write) stands — the reason changes.** ⚠ This makes it an instance of §3's `query()` gap, not a separate engine defect. Finding **#124** itself needs the same correction. |
| `:435` | **SELF-CONTRADICTION — delete the line** | §8 lists "`sequence::next` vs `sequence::nextval`" as `[UNVERIFIED]` while §5 (`:328`) records `nextval` as `[MEASURED]`. §5 is correct: `sequence::next` is a **parse error** on 3.1.5 (the engine suggests `nextval`). Delete the §8 line. |
| `:439–440` | **SELF-CONTRADICTION + settled** | Duplicates the §4 `[UNVERIFIED]` cascade flag; also says "unreachable today". Both now false — settled ABSENT (row 3 above). |
| `:52–59` (§1.1 table) | **MISSING ROW** | No **SEQUENCE** row in the decision-rule table. Add: **SEQUENCE → `IF NOT EXISTS`** — bare `DEFINE` **raises** `"The sequence 'x' already exists"` (a boot-time crash on re-apply, the same failure mode cited for INDEX); no variant resets the counter, verified from a fresh connection; residual: a changed `BATCH`/`START` will not migrate. |
| `:409–417` (§7 table) | **MISSING GOTCHA** | Add: **RELATE endpoint from a created row** — ✅ `LET $m = (CREATE ONLY t …).id; RELATE $m->e->$x` / ❌ `RELATE $m.id->e->$x` — **PARSE ERROR** (*"Unexpected token `.`, expected a relation arrow"*). |
| `:268–272` | **worth strengthening** | Add the measured failure text for a **bare string** endpoint: `"Cannot execute RELATE statement where property 'in' is: 'message:m_real'"` — relevant because `BriefLedger.publish(agent_id=...)` takes a bare string (`:281`). |
| §5 `:299–336` | **ADDITION** | Record that `sequence::nextval` + `CREATE` + N×`RELATE` composes in ONE transaction, measured 16-way × 20 = 320 txns: 320/320 OK, zero conflicts, zero duplicates, zero gaps. |
| §4 | **ADDITION** | `TYPE RELATION IN a OUT b` **does** reject a wrong-*table* endpoint (field coercion error) — the only endpoint validation the engine offers. `RELATE` onto an undefined table auto-creates it `TYPE ANY`, silently losing that guard (cascade-delete survives). |

## THINGS I FOUND THAT YOU DID NOT ASK ABOUT

1. **#124's mechanism is misdiagnosed in both the finding and the reference doc** (above). Consequential beyond packet 03: it is currently cited as evidence the *engine* silently loses committed data. It does not. Anyone reasoning about durability from that sentence is reasoning from a false premise. INCONCLUSIVE on the original harness — someone should read `scratchpad/102-recovery/` before rewriting the finding.
2. **`RELATE` auto-creates edge tables as `TYPE ANY`** — so a *missing* DDL entry does not fail loudly, it silently degrades the edge's type guard. Worth an AST/DDL-coverage pin: every table named in a `RELATE` in production code appears in `generate_ddl` as `TYPE RELATION`.
3. **The four-way-ambiguous CAS return is a defect generator**, not just a packet-03 concern. Any `UPDATE … WHERE <guard>` in this codebase has the same property. Worth checking whether existing CAS-shaped writes (brief ack paths) already conflate "no-op" with "target absent".
4. **§3's "classify the FIRST failed statement" reproduced live** in Probe 3 leg C — the real cause (`deliberate abort`) sat at index [3] behind two cascade notices at [1]/[2], with the marker-less COMMIT error last. Good news: the existing `_txn.py` logic is correct. I mention it because my probe output shows pre-offender statements stamped `ERR` too, matching the audit-102 B3 note at `_txn.py`'s docstring, and it is a useful confirmation that the fix still holds on 3.1.5.
5. **Instrument-failure receipt:** Probe 1's first run would have produced the *exact opposite* conclusion ("RELATE rejects bad ids") had I omitted the positive control. Offered as a live receipt for the repo's "a probe needs a control" law — the control is what caught it, and the cost of omitting it here would have been a shipped design premised on engine-level validation that does not exist.
6. **No lore tools used** (§4 tool honesty): this task was empirical store probing, not a code-structure question. The two file reads were direct (`brief-base.md`, the store reference) per the brief's numbered steps, and the harness idiom was read from `loremaster/tests/_surreal_harness.py` at a known path. No grep fallback for a structure question occurred, so there is no friction to file.

## CLEANUP

All 10 throwaway databases reaped (`REMOVE DATABASE IF EXISTS` receipt at the tail of every run). No repo source or test file touched; nothing staged or committed. Scripts left in the scratchpad path for re-run:

```
_probe.py  probe1_relate_out.py  probe2_unique_cascade.py  probe3_sequence.py
probe3b_sequence.py  probe3c_seq_concurrent.py  probe4_cas.py  probe4b_cas_errors.py
probe4c_indistinguishable.py  probe5_table_coverage.py  probe5b_124_mechanism.py
probe5c_control_and_retry.py  probe5d_type_any_edge.py
```
