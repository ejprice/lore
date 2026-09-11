# Packet 63b — ii-b drain-UPDATE (DD-3.c) ruling (sidecar-63b-ii-b, 2026-09-11)

brief-base v14 read
brief project v7 read

## Summary block (brief-base §1)

- **state:** done (ruling doc; standing by for the contract fidelity read).
- **deviations:** none. Writable set honoured (this file only); no git mutation — the lead commits.
  HEAD at ruling: `6b351c9` (the brief named `3f69374`; the probe commits `0f36420`/`6b351c9` landed
  after — nothing this ruling rests on moved between them; verified by reading at `6b351c9`).
- **Capability check (brief-base §4):** everything demanded was reachable — lore tools loaded
  (`ToolSearch +lore`), `Read`/`awk`/`sed` for spans, `git` read-only. Text-search binaries are
  hook-blocked in this checkout as the brief said; every textual sweep below is `awk` over an explicit
  file list and is SAID so where used.
- **Packages considered:** none — no mechanism specified. The ruling REMOVES a mechanism (a store
  ASSERT) and specifies no new one; the migration rides the existing emitter (`_define_field`,
  `OVERWRITE`) and the existing boot re-apply (`ensure_ready`).
- **Reuse ledger:** none — 0 new production symbols introduced by this ruling. (The two renders the
  fidelity section names — `_render_rollup`'s message leg and the awaiter's drain binding — are shape
  rulings on EXISTING symbols, not new ones; the lead's contract author owns any new name and its row.)
- **Graded:** `6b351c9` · HEAD-at-report: `6b351c9` · SAME.
- **decisions-needed:**
  1. §3 RULING — **DROP the `to.ack_note` DDL ASSERT; keep the app cap** — is BINDING per the
     operator's 63b delegation; no operator ruling needed. Listed here so the lead sees it is settled.
  2. §7 RESIDUAL (raised, NOT ruled — outside my fork): the same class exists on `message` (5 ASSERTs,
     and ii-a's §4.C migrate UPDATEs message rows). Not live today by the same construction argument
     (§4.2); needs an operator decision on whether the §3.4 invariant extends to `message`.
  3. §9.3 — the i-b coverage pin's reach is keyed on the `self.` receiver; the comms handlers use
     `AppContext.` — the pin will NOT see ii-b's renders as written. RULED (extend the derivation);
     filed as a finding. The lead grants `test_memory_render_bound_63b_ib.py` to the contract's set.
  4. §9.5 — the fate of an ack over an addressed-but-INVISIBLE seq is UNSTATED by §4.B and falls to
     a false `already_acked(acked_at=None)` at HEAD's `_ack_entries`. RULED (α: `unknown_message`),
     reading β written down. Lead: confirm the contract pins it.
- **receipt pointers:** the probe (`scripts/probe_drain_read_63b_ii_b.py`, committed `0f36420`;
  report `REPORT-probe-63b-ii-b.md` at `6b351c9`, to be archived under
  `docs/plans/v2/receipts/2026-09-11-packet63b-ii-b/`) · store-ref §1.1 / §1.2 / §1.4 / §3 · the
  existing dirty-`to` pin class `test_comms_schema.py::TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge`
  · the offline ASSERT pin `test_comms_schema.py::TestThePointerBoundsHaveTheirSTOREBackstop::
  test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap` · the app cap
  `messages.py::MessageLedger._reject_oversize_note` + its pins (§5.1) · the 03b origin
  `docs/plans/v2/receipts/2026-07-25-packet03b/REPORT-coldaudit-03b-2.md` §3.0.

---

## 0. The ruling in one screen

| # | item | ruling |
|---|---|---|
| R1 | the fork | **DROP the `to.ack_note` store ASSERT (option 1). Keep `_reject_oversize_note` as the ONE implementation of the note bound.** Option 2 (keep + heal) REJECTED; option 3 (visible-bounding) REJECTED as a fix, KEPT as the §4.B shape it already is. §3 |
| R2 | the invariant this generalises to | **`to` is the UPDATE-hot table (drain stamps it on EVERY call, one statement over the window) → `to` carries NO constraint a legacy row can violate: no ASSERT on any field, no non-`option<>` field added after birth, no TYPE change.** Pinned as a KNOWN BOUND with a re-open trigger (§3.4, pin P2). The quantifier law: stated ∀ fields of `to`, not the one I derived it on. |
| R3 | the DDL mechanism | No new mechanism. `_TO_FIELD_SPECS`'s `ack_note` row gets an EMPTY constraint; `_define_field` emits `DEFINE FIELD OVERWRITE ack_note ON to TYPE option<string>` — a FULL REPLACE that DROPS the ASSERT on an existing store (store-ref §1.2, PROBED 2026-07-12; and the ii-b probe's `_downgrade_ack_note` is byte-for-byte this statement, MEASURED on 3.2.4 to drop the bound). `ensure_ready` re-applies it at boot, BEFORE any drain is served — so the migration has no deploy ordering to remember. §3.3 |
| R4 | the dirty-store pin (the load-bearing rider) | **INVERT the existing `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge`** — same fixture, assertion flipped (the whole-window stamp SUCCEEDS and stamps BOTH edges), driven through the REAL `MessageLedger.drain` in the §4.B one-txn shape, with the dirty edge VISIBLE to the reader (else it is C4's false clear). RED the day the hazard reopens (mutation proof: re-add the ASSERT → RED). §6, pin P1 |
| R5 | the DUAL | Removed behaviour = the store-level over-cap rejection on `to.ack_note`. Adjudicated item-by-item in §5: dropped-deliberately (reason) · the length virtue preserved-with-pin at the app layer · two existing pins that certify the OLD world named and re-adjudicated (one deleted-with-replacement, one inverted). |
| R6 | reachability | **MOOT for the ruling** (no ASSERT ⇒ nothing to re-validate). NOT moot for the RUNNING image until pkt-65 ships: one read-only count on `:18500`, owner = lead, decision point = ii-b close-out; expected 0 BY CONSTRUCTION (§4.2). §4 |
| R7 | `render_subject_bound` on comms reads | ONE line per served response, FIRST line of the TOP-LEVEL render the handler calls directly; never on sub-renders. Carried by `_render_comms_drain`, `_render_comms_await` AND `_render_comms_await_empty`, `_render_comms_story`, `_render_comms_ack`, and `_render_rollup`'s MESSAGE LEG (leg-scoped, not response-scoped). §9 |
| R8 | rollup `capability=` | §4.E's shape HOLDS, sharpened in §9.4: the leg is rendered INSIDE `_render_rollup` (so the i-b coverage derivation reaches it), the bound line heads the LEG, and the tokenless line is `messages: identity required — pass capability=` with NO count. |
| R9 | two things raised, not buried | §9.3 the i-b derivation's `self.`-receiver reach bound (RULED: extend to `AppContext.`/`cls.`; finding filed) · §9.5 the invisible-seq ack fate (RULED α). |

---

## 1. The facts this ruling rests on (read at `6b351c9`; cited, not re-transcribed)

- **The hazard is MEASURED, not believed.** `REPORT-probe-63b-ii-b.md` §3 (lead re-ran, exit 0):
  C1/C2 `DD-3.c: ABORTS-WHOLE` — a legacy over-cap `ack_note` edge with `seen_at IS NONE` in the
  window makes drain's `seen_at`-only UPDATE error; in the §4.B one-txn shape the whole
  `BEGIN…COMMIT` aborts (store-ref §3) and NOTHING is served or stamped. C3: `ack` heals (it writes
  `ack_note`). C4: visible-bounding masks only an INVISIBLE dirty edge. This is the packet-03b C3 defect
  (`REPORT-coldaudit-03b-2.md` §3.0) re-confirmed at HEAD on 3.2.4 and extended to the one-txn shape.
- **`to` carries exactly ONE constraint.** `surreal_schema.py::_TO_FIELD_SPECS` at `6b351c9`:
  `session string · created_at datetime · seen_at option<datetime> · acked_at option<datetime> ·
  ack_note option<string> ASSERT string::len($value) <= MESSAGE_BODY_MAX_CHARS` (=4000). No other
  ASSERT, no DEFAULT (a DEFAULT on `seen_at` would make edges look stamped — the spec's own comment).
  History (git `-S ack_note` + `git show` of the tuple at each sha): `df59f76` shipped the row
  UNBOUNDED; `1a6010f` (03b, 2026-07-25) added the ASSERT; no TYPE on `to` has changed since birth (the
  tuples differ ONLY in that constraint).
- **The mechanism is SCHEMAFULL whole-record re-validation** — store-ref §1.4 (MEASURED, with the
  fixture trap named: the legacy row must be written UNDER the old DDL). Dropping the ASSERT removes
  the only clause `to` has that a row can violate.
- **`_define_field` is `OVERWRITE` = FULL REPLACE** — store-ref §1.1/§1.2: an OVERWRITE omitting an
  ASSERT DROPS it (PROBED 2026-07-12); `IF NOT EXISTS` is the #107 no-op; `ALTER` is the §1.3 trap
  (a PATCH keeps the omitted ASSERT forever, and cannot create the field on a virgin DB).
- **Exactly ONE production writer of `ack_note`** — `messages.py::MessageLedger.ack`'s
  `UPDATE to SET acked_at = $acked_at, ack_note = $ack_note …`, app-capped by
  `_reject_oversize_note` (introduced `d4e4778`, 03b, same day as the ASSERT). Bare-pattern `awk`
  sweep of every `*.py` under `loremaster/ lorerunes/ loresigil/ lorescribe/ scripts/` (text-search
  binaries are hook-blocked — said so): production mentions are the `ack` UPDATE, the drain projection
  (`_ENTRY_PROJECTION`), `InboxEntry.ack_note`, and one server.py COMMENT. **No render consumes
  `InboxEntry.ack_note` at HEAD** (03b's design: "`ack_note` is NOT rendered in drain … notes are read
  via packet 05's history surface", and 05a-iii's story renders message BODIES, not ack notes).
- **F5 (63b-i-a) observes every `to` mutation as a state diff**, deny-by-default on an unattributed
  write that LANDED (design §1.2, incl. the "relation table like `to` diffs identically" row); ii-a's
  `test_message_enforcement_63b_ii_a.py` pins ack's effect predicate `changed_columns ⊆ {acked_at,
  ack_note}` and drain's `{seen_at}`. Its reach is the battery's executed frames (§1.5c coverage leg) —
  a bound, stated as such below.
- **The app cap is already pinned, ∀ error classes:** `test_message_ledger.py` — `MessageBodyError` at
  cap+1 with the cap named in the message, a POSITIVE CONTROL at exactly the cap, and the parity
  scenario `ack_note_overcap` in `_PARITY_SCENARIOS`, whose coverage pin asserts the scenario set covers
  EVERY concrete `MessageLedgerError` subclass (coverage as a checked variable).
- **Two existing tests certify the OLD world** (the rename-sweep law: tests written before a semantic
  change certify the corpse): `test_comms_schema.py::TestThePointerBoundsHaveTheirSTOREBackstop::
  test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap` (offline DDL-text pin: the emitted `to`
  statement CONTAINS the ASSERT) and `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge::
  test_a_WHOLE_WINDOW_stamp_is_DENIED_by_ONE_legacy_edge` (the mechanism, pinned as a known miss:
  *"so that the next narrowing of a `to` field meets the mechanism DELIBERATELY"*). Both go RED under
  this ruling. Both are adjudicated in §5 — neither may be quietly deleted.

---

## 2. THE THREAT MODEL — written down, so the verdicts follow mechanically (CLAUDE.md: a gate needs one)

**Who is the `to.ack_note` ASSERT for?** DD-3.c named it at 03b (the class docstring of
`TestThePointerBoundsHaveTheirSTOREBackstop`): *"a LEDGER-ONLY build … any future writer that does not
go through `MessageLedger.send` lands an unbounded row silently."* Transposed to the edge: **the honest
developer who adds a SECOND production writer of `ack_note` and forgets the app cap.** It is NOT a
security boundary against a hostile author (anyone who can commit can remove the ASSERT too — #138's
model), and it is not for the consumer agent (a note is never served back to it at HEAD).

**Who is hurt by the ASSERT?** The honest developer who does either of:
- (T1) **narrows the cap** — lowers `MESSAGE_BODY_MAX_CHARS` (it is one constant, shared with
  `message.body`; a "4000 is generous, make it 2000" edit is the most ordinary change imaginable); or
- (T2) **adds any constraint to `to`** — an ASSERT on a new field, a non-`option<>` field, a TYPE change.

Under either, EVERY gate is green (virgin DBs — store-ref §1.6), and on the long-lived store every
agent holding a now-illegal edge UNSEEN in its window **cannot drain ANY of its inbox** the day the
image ships. That is the #107/#131 shape verbatim, and the outage is the WORST comms failure shape
available (total, per-agent, silent until an agent reports it).

**The two failure costs, side by side:**

| failure | who causes it | what a gate sees | production consequence |
|---|---|---|---|
| ASSERT ABSENT, second writer lands an over-cap note | honest dev adding a writer without the cap | F5 reds an unattributed `to` write it EXECUTES (§1.5c); the §3.4 single-writer floor reds the new SET site | one long row; nothing served (no render reads the note); nothing denied |
| ASSERT PRESENT, cap narrowed / constraint added | honest dev editing one constant | NOTHING (green on virgin) | **total inbox denial** for every agent holding a legacy edge unseen — the measured C1/C2 |

**The verdict follows:** the ASSERT guards a small, duplicated property (a storage length, already
capped by the ONE writer and observed by F5) and does so by arming the worst outage shape against the
most ordinary honest edit. *"A gate that refuses honest code is a gate that gets SWITCHED OFF"* — here
it is worse: the gate does not refuse honest code at commit time at all; it detonates in production.
A backstop whose only observed effect in this repo's history is to deny drains (03b C3 in July, the
probe in September) is not a backstop. **Drop it.**

---

## 3. RULING R1 — DROP the `to.ack_note` ASSERT; the app cap is the ONE implementation

### 3.1 The ruling, precisely
- `surreal_schema.py::_TO_FIELD_SPECS`: the `ack_note` row becomes `("ack_note", "option<string>", "")`.
  Its comment is REWRITTEN to state the §3.4 invariant and cite this doc (the current comment — *"Bare
  assert: NONE is not evaluated"* — becomes a stale-prose defect the moment the assert is gone; the
  rename-sweep law: served/source prose consistent with code).
- `MessageLedger.ack`'s `_reject_oversize_note` stands UNCHANGED as the ONE implementation of the note
  bound (ONE IMPLEMENTATION: the policy lived at two layers by DD-3.c's deliberate choice; after this
  ruling it lives at one, which is the rule's preferred state, not a loss).
- `MESSAGE_BODY_MAX_CHARS` is untouched (it still bounds `message.body`'s ASSERT — see §7 for the
  `message` residual, which this ruling does NOT touch).

### 3.2 Why not option 2 (keep + heal migration)
1. **It heals nothing today and re-arms the hazard forever.** At the CURRENT cap the heal is a no-op by
   construction (§4.2: zero over-cap rows can exist), so the migrate leg is paid to heal an empty set —
   and the NEXT narrowing (T1) needs the heal re-run, in the right order, ahead of the first drain: a
   "remember-to" with production denial as the forfeit. A heal is the right tool for a one-time
   accident; this is a standing property of an UPDATE-hot table.
2. **Deploy ordering is exactly the kind of rider that gets dropped** (CLAUDE.md, THE RIDER IS PART OF
   THE RULING — six instances in 03b alone). The DROP has NO ordering: `ensure_ready` lands the
   ASSERT-free definition at boot, before serving.
3. **It keeps two implementations of one policy** — the exact seam where a fix reaches one copy and not
   the other (#102).

### 3.3 Why not option 3 (visible-bounding) as the fix
C4 measured it: it saves the drain only when the dirty edge's message is INVISIBLE to the reader; a
visible dirty edge in the window still denies. It is not a mitigation of the hazard; it is the §4.B
one-txn shape's own stamp predicate (`in IN $visible.id`) and stays for THAT reason (the §4.3
"invisible is neither served nor stamped" guarantee), not this one.

### 3.4 RULING R2 — the invariant, stated ∀ (the quantifier law) and pinned as a KNOWN BOUND

> **`to` is UPDATE-hot** — `drain` writes it on every call in ONE statement over the whole window
> (`MessageLedger.drain`, and the §4.B one-txn shape keeps that property). **Therefore `to` carries no
> constraint a legacy row can violate:** every field has an EMPTY constraint (no ASSERT), every field
> added after birth is `option<>` with no DEFAULT, no field's TYPE changes. A constraint on `to` is a
> loaded gun pointed at every agent's inbox, and the trigger is any narrowing edit.

**The askable form** (THE LEVER — a question, not a property): *"Does this table get UPDATEd by a
statement that does not also SET the field I am constraining? If yes, a legacy row that violates my
constraint denies that statement for everyone in its window — who heals it, and when?"*

**Pin it like this — P2 (offline, DDL-text, `test_comms_schema.py`, beside the pointer-bound class):**
- Derive the `to` statements from `generate_message_ddl()` (the house idiom — *"assert what we send"*,
  never `INFO FOR TABLE`'s normalised echo), select every `DEFINE FIELD OVERWRITE <f> ON to …`, and
  assert for EACH: no `ASSERT`, no `DEFAULT`, and (for every field not in the birth set
  `{session, created_at, seen_at, acked_at, ack_note}`) the type starts with `option<`. The birth set is
  a CONSTANT in the pin with a comment naming why it is exempt (written at birth, always populated).
- **Non-vacuity control:** the pin also asserts the derived field set is non-empty AND contains
  `ack_note` (a derivation that finds nothing must red, not pass).
- **Its failure message carries the bound:** *"`to` is UPDATE-hot (drain stamps it in one statement
  over the window): a constraint here is DD-3.c — total inbox denial on the first legacy row that
  violates it (63b-ii-b ruling §3.4). If you are adding one DELIBERATELY you owe (a) a heal migration
  that runs BEFORE the first drain and (b) the §6 dirty-store denial pin inverted back — then delete
  this pin and say so."*
- **Re-open trigger** (named, per the deferral law): the day drain stops being a whole-window UPDATE
  (e.g. per-edge stamps, or a `to` rewrite that moves `seen_at` off the edge) — at which point a
  constraint on `to` is a per-row rejection again and this bound may be retired.
- **Mutation proof (the rider):** re-add the ASSERT to `_TO_FIELD_SPECS` → P2 RED; add a spec row
  `("x", "string", "")` → P2 RED (non-option post-birth); restore → GREEN. Declare the expected-RED ids
  from `--collect-only` before the run (`scripts/mutation_proof.py`).

**P3 (the single-writer floor — static, cheap; F5 is the runtime instrument):** a bare-pattern scan of
the PRODUCTION modules (`_SCANNED_MEMBERS`-derived, never a hand list of files) for `ack_note` inside a
`SET`/`CONTENT` clause, asserting the allowlisted safe set is EXACTLY `{MessageLedger.ack}`. Threat
model stated IN the pin: the honest developer adding a writer without the cap; NOT a hostile author
(`"ack_" + "note"` gets through — #138's shape, ledgered, not paid for). Non-vacuity: the scan must find
the `ack` site. This is the static FLOOR; the ∀ instrument is F5's effect predicate, whose reach is the
battery's executed frames (design §1.5c) — the pin's docstring says so.

---

## 4. Reachability — RULING R6

### 4.1 For the RULING: MOOT
With no ASSERT there is nothing for the drain UPDATE to re-validate: a pre-existing over-cap row (if
any) is inert — readable, stampable, ackable (ack overwrites it with a capped value, C3). The pkt-65
deploy needs no count, no heal, no ordering.

### 4.2 For the RUNNING image (until pkt-65 ships): expected ZERO BY CONSTRUCTION — and one receipt
- The `to` table first reached `:18500` with packet 03b's deploy (INDEX row 03b: *"DONE + DEPLOYED
  2026-07-26 … DEPLOYS BOTH"*; the 03b cold audit §3.0 and the existing pin class's docstring both state
  `message`/`to` had NEVER been deployed before). The ASSERT (`1a6010f`) and the app cap (`d4e4778`)
  are both 03b commits dated 2026-07-25, the day BEFORE that deploy.
- **Bound on that claim, stated honestly:** the INDEX's deploy identifier `b46bc1d5` is an IMAGE hash,
  not a git sha (`git cat-file -t` → not an object), so "the deployed image contained `1a6010f`" is a
  strongly-grounded BELIEF (dates + the packet's own close-out), not a git-proven fact. It becomes a
  fact with ONE read-only statement on `:18500`, which is the lead's to run (never a test — CLAUDE.md):
  `SELECT count() FROM to WHERE string::len(ack_note) > 4000 GROUP ALL` — expected `[]`/0 — and, for
  the schema half, `INFO FOR TABLE to` showing the ASSERT on the stored `ack_note` definition.
- **Decision point (named):** owner = **lead-63b-iib**, when = **ii-b close-out** (before the INDEX Log
  line), input = the two reads above. Outcome table: count 0 → record the receipt in the close-out and
  move on (nothing gates on it). Count > 0 → that agent's drains are DENIED TODAY on the running image
  (the 3-call drain at HEAD has the same whole-window UPDATE): file a `lore_findings` row (kind=bug),
  and heal as an ops action with the C3 statement (`UPDATE to SET ack_note = string::slice(ack_note, 0,
  4000) WHERE string::len(ack_note) > 4000` — the SET conforms; the probe measured the mechanism) —
  pre-production charges are authorized (CLAUDE.md), so no operator gate. Either way the ruling stands.

---

## 5. THE DUAL — removed-behaviour inventory, adjudicated item by item

The removed behaviour: **the store rejects a `to.ack_note` value longer than `MESSAGE_BODY_MAX_CHARS`
on any write path.** Every virtue and every pin that depended on it:

| # | item | adjudication | receipt / pin |
|---|---|---|---|
| D1 | store-level over-cap rejection of `ack_note` (DD-3.f "at BOTH layers, mirroring `body`") | **DROPPED DELIBERATELY** — reason §2/§3: guards a duplicated storage bound at the price of total inbox denial on an honest narrowing. | this doc §2–§3 |
| D2 | the NOTE LENGTH bound itself (DD-3.f: *"a note is message-grade PROSE, so it takes the BODY constant"*) | **PRESERVED-WITH-PIN at the app layer** — spec clause DD-3.f is satisfied by `_reject_oversize_note` (cap+1 → `MessageBodyError` naming the cap; positive control AT the cap; parity scenario `ack_note_overcap` under the ∀-error-class coverage pin). Cited to the SPEC, not to "the old code did it". | `test_message_ledger.py` (the three pins in §1) |
| D3 | `test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap` (offline: the emitted `to` statement carries the ASSERT) | **DELETED-WITH-REPLACEMENT** — it certifies the corpse. Replaced by **P2** (§3.4), which asserts the INVERSE property ∀ fields of `to`. The class docstring of `TestThePointerBoundsHaveTheirSTOREBackstop` gains one paragraph: `message` keeps both layers (never UPDATEd after create at 03b; see §7 for the ii-a caveat); `to` is the exception, and why. | contract worklist item W3 |
| D4 | `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge::test_a_WHOLE_WINDOW_stamp_is_DENIED_by_ONE_legacy_edge` (the mechanism pinned as a known miss) | **INVERTED** — same fixture (`_old_to_ddl` + `_dirty_edges` + `generate_message_ddl()` migrate), assertion flipped: the whole-window stamp SUCCEEDS and stamps BOTH edges. This IS the required dirty-store pin — §6 specifies it. The BASELINE and CONTROL tests in that class STAND (they discriminate the fixture). The class docstring's *"Production exposure at this deploy is ZERO (`message`/`to` have never been deployed)"* is STALE since 2026-07-26 — rewrite, dated. | §6 / P1 |
| D5 | the `_TO_FIELD_SPECS` comment (*"Bare assert: NONE is not evaluated"*) | **REWRITTEN** to the §3.4 invariant — stale prose otherwise. | W1 |
| D6 | `ack` docstring: *"Bounded HERE rather than one packet later"* | **STANDS** (still true — the app layer is now the only layer; the sentence's reason is stronger, not weaker). | — |
| D7 | store-ref §1.4's example of the hazard on `to` | outside my writable set — **FLAG**: the lead may add one dated line under §1.4 citing this ruling as the `to` receipt (a reference that names the hazard should name its resolution). | lead |
| D8 | a render/served-length virtue | **NONE EXISTS at HEAD** — no render consumes `InboxEntry.ack_note` (§1 sweep). When one lands (a future history surface), it routes through `render_fenced`/`render_attributed` like every stored free text (the rename-sweep law's hostile-fixture rule applies THEN). | — |

Spec-silent items requiring an operator ruling: **none** on `to`. (The `message` extension is §7.)

---

## 6. THE DIRTY-STORE PIN — P1, "pin it like this" (the contract author carries this verbatim)

**Threat model of the pin:** the honest developer who re-adds a constraint to `to` (or narrows a cap)
with every virgin-DB gate green. It goes RED the day the hazard reopens.

**Fixture — the #131 migrate-onto-dirty-store path, exactly the probe's construction and the existing
class's `_dirty_edges`, with two REQUIRED changes:**
1. **OLD world:** apply `generate_agent_ddl()`; a SCHEMALESS `message` stand-in is NOT acceptable here
   (the ii-b drain reads `message` through the read_filter, so the message rows must be REAL: apply
   `generate_message_ddl()` FIRST, then DOWNGRADE `to.ack_note` with the probe's `_downgrade_ack_note`
   statement `DEFINE FIELD OVERWRITE ack_note ON to TYPE option<string>` — the "before it was bounded"
   world). ⚠ The legacy row MUST be written under the OLD definition (store-ref §1.4's fixture trap:
   a row written after the migration measures nothing).
2. **Dirty edges:** one recipient agent; TWO messages in the recipient's OWN scope (both VISIBLE to the
   draining Subject — a governed member Subject built through the shared credentialed harness, ii-a
   §11.3, with the messages stamped `scope`/owner such that the read_filter KEEPS them); RELATE both
   edges `seen_at = NONE`, one with `ack_note = "n" * (MESSAGE_BODY_MAX_CHARS + 1)`, one clean.
   **Visibility is load-bearing:** an INVISIBLE dirty edge is excluded by `in IN $visible.id` and the
   pin would pass for C4's reason (a false clear). The assertion in step 5 FORCES visibility.
3. **Migrate:** re-apply `generate_message_ddl()` (the CURRENT emitter — under this ruling it lands
   an ASSERT-free `ack_note`; under a wrong build that keeps/re-adds the ASSERT it lands the bound and
   the drain below denies).
4. **Act through the PRODUCTION seam, never a hand-typed statement:** call the real
   `MessageLedger.drain(agent_id=…, limit=10, peek=False, <the ii-b subject/read_filter arg>)` on a
   ledger over a real `SurrealConnection` (a hand-typed copy of drain's UPDATE is a private copy that
   can drift from drain — ROUTING IS NOT SHARING; the existing class's verbatim-UPDATE leg may REMAIN as
   the mechanism control, labelled as such).
5. **Assert:** (a) the call returns (no `SurrealStoreError`, no aborted txn); (b) `stamped_seqs` ==
   BOTH seqs (this forces both edges visible AND stamped — a dirty edge masked by C4 would be missing);
   (c) `entries` serves both; (d) a read-back `SELECT seen_at FROM to WHERE out = $agent` shows both
   `seen_at IS NOT NONE`; (e) the over-cap `ack_note` value SURVIVES unchanged on its edge (store-ref
   §1.4: a migration converges schema, never data — and this ruling adds no heal).
6. **Controls in the same class (keep the existing two):** BASELINE (the old world accepts the over-cap
   note — else "success after migrating" could be success because the row was never dirty); and a
   second leg where the dirty edge is `seen_at` already set (the C-control: outside the window, never
   touched) — proving the pin's window predicate is drain's real one.
7. **Mutation proof (declared before the run):** restore the ASSERT on `_TO_FIELD_SPECS` → P1 RED with
   the engine's `ack_note … must conform to` text in the failure; P2 RED; restore → both GREEN. That is
   the "RED the day the hazard reopens" property demonstrated, not asserted.

**Where:** `test_comms_schema.py`, in place of the current `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge`
(renamed to say what it now certifies — e.g. `TestALegacyOverCapNoteCannotDenyADrain`), carrying the
DD-3.c reference and this doc's path in its docstring. If the contract author needs the credentialed
harness there, the lead grants `_governed_contract.py` per ii-a §11.3 (F-DUP: one shared harness).

**Also in the contract (the ii-b one-txn leg):** the same fixture driven through the §4.B Reading-B
transaction path (`execute_read_transaction`, probe `_reading_b_txn` shape) — because C2 measured that
the one-txn shape converts a statement error into a whole-txn abort with NOTHING served; the pin must
prove the served set arrives. If drain's implementation IS the one-txn path (§4.B RULED), step 4
already exercises it and this is one leg, not two — the contract author states which.

---

## 7. RESIDUAL — raised, not ruled (scope belongs to the operator)

**The same class on `message`.** `_MESSAGE_FIELD_SPECS` carries FIVE constraints (`thread`, `grade`,
`body`, `refs`/`refs[*]`, `task_id`). 03b's argument that `message` cannot be write-poisoned rested on
*"message rows are never UPDATEd"* — **ii-a's §4.C migrate leg UPDATEs message rows** (owner/scope
stamps; `eafb8fd`), and any future `message` UPDATE inherits the hazard. Not live today by the §4.2
construction (all five constraints shipped in or before the 03b deploy, and `MESSAGE_BODY_MAX_CHARS`
has never been lowered). But T1 — lowering that ONE constant — now poisons `message.body` for the §4.C
migrate exactly as it would have poisoned `to`. **Fork for the operator:** (a) extend the §3.4
invariant to `message` (drop its length/closure ASSERTs, keep the app caps — same reasoning, but a
bigger removed-behaviour inventory and `message` is not UPDATE-hot, only UPDATE-able); (b) keep them
and pin the miss (a dirty-store pin on the §4.C migrate over a legacy over-cap `body` row, RED-on-fix,
with the heal statement named); (c) defer with a named trigger ("the first lowering of any message cap
or the first new `message` UPDATE path"). My recommendation: **(b) now, in ii-b or 65, at ~one test**;
(a) only if a second `message` UPDATE path lands. Not ruled here — outside the ii-b fork.

---

## 8. Riders roll-up — the "and pin it like this" index for the contract author / adversary

| pin | what | where | RED when |
|---|---|---|---|
| P1 | dirty-`to` drain SERVES + STAMPS both edges through the real drain (§6) | `test_comms_schema.py` (inverted class) | any constraint returns to `to` / cap narrowed |
| P2 | `to` carries no constraint a legacy row can violate, ∀ fields (§3.4) | `test_comms_schema.py`, offline DDL text | an ASSERT/DEFAULT/non-option post-birth field on `to` |
| P3 | single production writer of `ack_note` = `{MessageLedger.ack}` (static floor; F5 is the ∀ instrument) | AST/text scan over derived members | a second SET site lands |
| D2 | app cap stands (already pinned, ∀ error classes) | `test_message_ledger.py` | — (existing) |
| P4 | bound line EXACTLY ONCE per served comms READ response (§9.1) | render pins per verb | a sub-render double-renders it, or a top-level render omits it |
| P5 | the i-b coverage derivation sees `AppContext.`/`cls.` receivers + non-vacuity floor naming the ii-b renders (§9.3) | `test_memory_render_bound_63b_ib.py` | the derivation regresses to `self.` only |
| P6 | rollup tokenless: the message leg is the ONE bound line, no count, no rows; WITH capability: bound line heads the leg (§9.4) | rollup render pins | an unfiltered leg / a withheld count / a response-scoped line |
| P7 | invisible-seq ack → `unknown_message`, stamps nothing, never `already_acked(acked_at=None)` (§9.5) | ledger + render pins | the read-back leaks an unfiltered edge |
| M | mutation proofs for P1/P2 declared from `--collect-only` before the run | `scripts/mutation_proof.py` | — |

---

## 9. FIDELITY CONFIRMATIONS on the ruled read side (design §3.3 / §4.B / §4.E)

### 9.1 `render_subject_bound` — placement RULED (it was ambiguous at the sub-render level)
- **ONE line per served response, the FIRST line, on the TOP-LEVEL render the handler calls
  directly** — the recall precedent (`_render_recalled_memories(recalled, *, subject)` prepends it and
  then the content, INCLUDING the empty case). Sub-renders shared with ungoverned verbs or called from
  helpers (`_render_comms_drain_row`, `_render_story_message`, `_render_comms_waiting_line` — the last
  is composed by `heartbeat` too) NEVER carry it. Pin P4: the rendered response contains the bound line
  EXACTLY once (a count, so a sub-render clone reds).
- **Carriers and the exact seam** (each gains a keyword-only `subject`, no default — the fixture-default
  law at the signature layer, as `session` already is on drain's render):
  - `drain` → `_render_comms_drain(result, *, agent_name, limit, session, subject)`: bound line, then
    the existing header count line (`inbox: N unread …`). The counts stay whole-set edge counts labelled
    "pending deliveries"/"unread" — §4.B's Leg-1 wording — and the bound line is what makes a served
    window smaller than the count honest (the diff is NAMED: scope).
  - `await` → BOTH `_render_comms_await(result, *, session, subject)` (bound, then `surfaced k of N …`)
    AND `_render_comms_await_empty(waiting_lines, *, subject)` (bound, then the timeout fact) — the
    empty case is where Leg 1 matters most (§3.3). The awaiter's `drain` seam must carry the subject/
    read_filter into `MessageLedger.drain` (an `InboxAwaiter(drain=…)` binding — lead mechanics; the
    awaiter itself stays subject-blind, R-1).
  - `story` → `_render_comms_story(story, *, subject)`: bound, then `story: arc of task …`.
  - `ack` → `_render_comms_ack(result, *, agent_name, note, subject)`: bound first. `ack` IS a governed
    read render under the derivation (its handler resolves a Subject and its fates are read back through
    the visibility filter, §4.B), so the derivation DEMANDS it — the ruling is derived, not chosen.
  - rollup → §9.4.

### 9.2 The derivation makes the coverage law self-enforcing — IF it can see the calls (→ 9.3)
`_governed_read_render_methods` (i-b) collects, per `AppContext` function that calls
`self._resolve_subject`, the `_render_*` names it calls; the pin demands `subject` in the signature and
`render_subject_bound` in the source of each. So the moment ii-b's handlers resolve a Subject, their
top-level renders join the set with no edit — the §3.3 pin-ii growth property.

### 9.3 ⚠ RAISED + RULED — the derivation's reach is a hidden receiver constant (INSTRUMENT 0)
The derivation admits only `node.func.value.id == "self"` for BOTH the signal (`self._resolve_subject`)
and the renders (`self._render_*`). **Every comms handler calls its renders as `AppContext._render_*`
(`_comms_drain`, `_comms_await`, `_comms_story`, `_comms_ack`, `_rollup`) and its helpers as
`AppContext._helper(self, …)`** — the duck-typed-harness idiom the handlers document. As written, the
pin's "a new governed read render reds with no edit" claim is FALSE for ii-b: the comms renders are
invisible to it. This is the instrument lesson's *receiver-name* row (a gate keyed on 2 receiver names,
defeated by the other doors) — a false clear waiting in the pin built to prevent false clears.
**RULING:** the derivation admits the receivers `self`, `cls`, and `AppContext` (a NAME node equal to
the class's own `__name__`, derived, not spelled) for both the signal and the render calls; and ii-b
adds a NON-VACUITY FLOOR asserting the derived set ⊇ `{_render_comms_drain, _render_comms_await,
_render_comms_await_empty, _render_comms_story, _render_comms_ack, _render_rollup}` (a floor, like the
existing `_render_recalled_memories` assert — never the exact set). Filed as lore finding **#464**
(area `test_memory_render_bound_63b_ib`, kind bug, by this sidecar). Lead: grant that test file to the contract.

### 9.4 The rollup message leg's `capability=` bound — §4.E HOLDS, sharpened
- **Tokenless (`capability` absent):** `_rollup` does NOT resolve a Subject (the composition root
  would deny — that is §4.E's letter: optional in 63b, required in 64); the task/finding legs render
  exactly as today; the message leg is replaced by ONE line, verbatim
  `messages: identity required — pass capability=` — **no count, no rows** (a count is an existence
  leak, 63-rulings §4.3). A PRESENT-but-unverifiable capability is the composition root's teaching
  `GovernedDenied`, never a silent fallback to the tokenless line.
- **With a verified capability:** `message_activity_since(since, *, limit, <read_filter>)` splices
  `AND (<read_filter>)` (probe A5: still IndexScans); `total` is the FILTERED count (the count describes
  the set its label claims — Leg 1); the leg is rendered with the bound line as its FIRST line, i.e.
  `scope: principal … · visible via N keep(s)` immediately above `messages activity (k):` — **leg-scoped,
  not response-scoped**: the task/finding legs are UNGOVERNED until 64 and a response-head scope line
  would over-claim about them.
- **Seam ruling (so the 9.3 derivation reaches it):** the message leg is rendered INSIDE
  `_render_rollup(…, subject: Subject | None)` (or by a `_render_rollup_messages(window, *, subject)`
  that `_rollup` calls DIRECTLY — either satisfies the derivation once 9.3 lands; the contract author
  picks one and the pin P6 asserts the placement, not the function name). `_rollup_extra_sections` keeps
  the fleet-health and brief-skew sections, which carry no scope line.

### 9.5 ⚠ RAISED + RULED — the fate of an ack over an addressed-but-INVISIBLE seq
§4.B: *"ack takes the same shape: resolve seqs → filter visible → CAS on visible → read back."* It does
not say what the RENDER reports for a seq whose message is real, whose edge is addressed to me, and
which the read_filter EXCLUDES. At HEAD `_ack_entries`' ladder gives it: not in `won_stamps` (CAS
skipped it) → `message_id in stored_stamps` (the read-back SELECT of MY edges finds the edge, `acked_at`
None) → **`already_acked` with `acked_at=None`** — a false fate ("acked earlier" about a message never
served and never acked), rendered as such. Two readings:
- **α (RULED): `unknown_message`.** Resolve seqs THROUGH the read_filter (the seq→message resolution is
  itself a `message` read and takes the splice like every other) so an invisible message is, to this
  Subject, indistinguishable from a nonexistent one; the CAS and the read-back then never see it;
  nothing is stamped. Consistent with §4.3's "an invisible message is neither served nor stamped" — the
  agent never received seq N through drain, so "unknown" is the truthful fate from ITS side, and it leaks
  no existence. The ack render's `unknown_message` teaching stands unchanged.
- **β (written down, rejected): `not_addressed`.** Truthful-sounding ("no delivery to you") but FALSE —
  the edge exists — and it requires the read-back to see the edge, which re-opens the `acked_at=None`
  hole for the `already_acked` branch.
**Pin P7:** an ack of an invisible seq → `unknown_message`; `acked_count == 0`; no `to` row changed (F5's
effect predicate sees zero delta); a CONTROL ack of a visible seq on the same ledger → `acked`. And the
QUANTIFIER leg: every requested seq still gets exactly one fate (the existing ∀-request walk).

---

## 10. Contract-revision worklist (what the lead hands the contract author — by file)

- **W1** `surreal_schema.py::_TO_FIELD_SPECS` — `ack_note` constraint → `""`; comment rewritten to §3.4 +
  this doc's path. (Builder wave; listed so the DDL-text pins are written against the target.)
- **W2** `test_comms_schema.py` — P1 (§6, the inverted class, renamed, docstring re-dated), P2 (§3.4),
  and the class-docstring paragraph for D3.
- **W3** `test_comms_schema.py` — DELETE `test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap`
  (D3; replaced by P2 — say so in the commit message, the rename-sweep law).
- **W4** P3 single-writer floor (a small AST scan beside the existing `_SCANNED_MEMBERS` scans).
- **W5** `test_memory_render_bound_63b_ib.py` — P5 (§9.3): receivers `self`/`cls`/`AppContext`, plus
  the ii-b non-vacuity floor. (Lead grants the file.)
- **W6** render pins per verb — P4 (once-per-response), the drain/await/await-empty/story/ack bound
  placement (§9.1), P6 rollup (§9.4).
- **W7** P7 invisible-seq ack (§9.5) — ledger + render.
- **W8** the ii-a §11.5 R6 obligation (per-verb no-cap-deny driver table keyed on the True set with a
  coverage assertion) — ALREADY RULED, not re-ruled here; listed for completeness of the ii-b set.
- **Close-out receipt (lead):** the §4.2 read-only count + `INFO FOR TABLE to` on `:18500`, recorded in
  the INDEX Log line.

## 11. Discipline receipts
- Every number above is derived this session (git dates, `awk` sweeps, symbol reads at `6b351c9`) or
  cited to the probe report the lead ground-truthed. The one belief is labelled as one (§4.2) with the
  instrument that converts it.
- Fallbacks to textual search, said out loud: the `ack_note` writer sweep and the `ASSERT` inventory
  are `awk` over explicit file lists (non-symbol textual seams — dogfood protocol case (b)); lore served
  the symbol-level reads (`generate_message_ddl`, `MessageLedger.drain`/`ack`, `render_subject_bound`,
  `_governed_read_render_methods` via `lore_search` → `Read`).
- No worktree used. No files outside the writable set touched. Idle-gate contract written for this path.
