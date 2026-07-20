# DESIGN-102 addendum — integrating `docs/reference/surrealdb-31-capabilities.md`

brief-base v2 read
design-consultant · 2026-07-12 · supplements `DESIGN-102-preliminary.md` (which is
edited in place only where this doc narrows its conditionality; all rulings stand).

The house SurrealDB 3.1 capability reference (Opus scout, 2026-07-11 —
`docs/reference/surrealdb-31-capabilities.md`) was read after the preliminary ruling.
It changes NO verdict. It narrows one conditionality, adds engine-documented support
under three rulings, and adds two design-law pins for C2. Item by item, with line
receipts into the reference:

## 1. §4's conditionality NARROWS — sequence existence is already documented

Reference `:38-39`: DEFINE SEQUENCE + sequence::next() is **"New in 3.0"** — 3.1.5
therefore HAS native sequences per the house reference. The open questions are only
the ones the reference itself flags (`:41-42`, `:127-129`): the real function name
(docs disagree on `next` vs `nextval`) and the first-boot seeding smoke (3.1.0-beta.3
fix). Consequence for the ruling:

- §4 PRIMARY (native sequence for `message.seq`) is now the **expected** path, not a
  coin-flip; the FALLBACK (reserve-then-create) is retained only against a probe
  *surprise* (wrong name in 3.1.5, seeding defect, capability gated at the server).
- The probe should ALSO record the `BATCH` default (`:39` — batched allocation can
  widen gaps across restarts; benign under the accepted burn semantics, but the C2
  contract prose must not promise "small" gaps) and confirm `START` syntax (the knob a
  future — optional — finding.number migration would seed with `max(number)+1`).

## 2. Q1 support — client retry on the conflict marker is the SANCTIONED idiom

Reference `:98-102`: "NO server auto-retry → bounded client retry on the conflict
marker". The engine explicitly delegates conflict retry to the client — the Q1 ruling
(retry lives in `execute_transaction`, nowhere else) is the engine's own documented
contract, not just a local preference. Two additions:

- **Observability**: the engine exposes OTel `transaction.conflicts` / `.retries`
  counters (`:101`). Wire nothing new for #102, but NAME them in the repair's docs as
  the operator's independent server-side witness: a raised
  `TxnContentionExhaustedError` can be corroborated against the server's own conflict
  counters, and they are the honest instrument for §5's post-repair N=32 latency
  measurement (measure, don't pilot).
- The retryable-conflict marker string the seam keys on (`_RETRYABLE_CONFLICT_MARKER`)
  stays the only client-visible signal — consistent with the reference; no richer
  signal exists to switch to.

## 3. Q2(d) support — ULID as order authority is engine-native

Reference `:45-49`: ULID / UUIDv7 record ids are time-sortable AND range-queryable
(timestamp-prefixed). This strengthens the ruling that TRUE message order belongs to
the ULID id, never to `seq`. The gotcha on the same lines — a RecordID's string
component cannot be indexed/prefix-matched, so any queryable component must be carried
as a value column — cuts the other way usefully: `seq` incidentally IS that queryable
value column for messages. The pair (ULID id = order + range scans; small int `seq` =
handle + indexable column) is exactly the division of labour §3(d) ruled.

## 4. New C2 design-law pin — CHANGEFEED, not seq cursors, for ordered replay

The preliminary banned `since=<seq>` incremental cursors (sequence values commit out
of allocation order). The reference names the engine-native tool for the job that ban
would otherwise leave uncovered: **CHANGEFEED + SHOW CHANGES** (`:64-69`) — durable,
versionstamped, replayable, with a retention window. Pin for the C2 contract: if
ordered cross-process replay/audit is ever required, it is a CHANGEFEED consumer;
`seq` remains a render/ack handle only. (Today nothing needs it — the unstamped-edge
backlog self-heals, as the reference itself notes at `:68-69`.)

## 5. Concurrence, with one nuance worth recording

Reference `:43-44` independently pins **"counter-table mint stays for
finding.number"** — the same mechanism my Q2 ruling keeps, so there is NO fork between
the scout reference and this ruling. The nuance: the reference's rationale is
"NOT gapless human handles", i.e. it treats gaplessness as a finding.number
requirement; my §3 analysis found gaplessness load-bearing NOWHERE (get-by-number,
order-by-number, UNIQUE backstop all survive gaps). Same mechanism either way — but
the contract author should inherit MY rationale, not the reference's, so no test pins
gaplessness as a behavioural promise (a pin on "no gaps ever" would forbid the
optional future sequence migration for no consumer's benefit).

## 6. Fallback-shape check against the UPSERT gotcha

Reference `:50-52`: `UPSERT <id> … WHERE` whose WHERE fails on an existing id cannot
create a row. The §4 fallback's reserve bump (`UPSERT message_counter:singleton SET
next += 1 RETURN AFTER` — no WHERE) is unaffected. Recorded so nobody adds a WHERE
guard to the bump later and silently converts contention into missed mints.

## Net effect on the preliminary

- §4: "conditional on whether 3.1.5 has a sequence" → "primary path expected; probe
  confirms name + seeding + BATCH default" (preliminary edited in place).
- §2.4 gains the OTel-counter witness (this addendum carries it; preliminary edit is
  a one-line pointer).
- §5 evidence list: probe scope narrowed accordingly.
- C2 contract inherits two pins: CHANGEFEED-not-seq-cursors (§4 above) and
  no-gaplessness-promise-on-finding.number (§5 above).
