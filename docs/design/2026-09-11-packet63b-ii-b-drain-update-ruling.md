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
| R3 | the DDL mechanism | No new mechanism. `_TO_FIELD_SPECS`'s `ack_note` row gets an EMPTY constraint; `_define_field` emits `DEFINE FIELD OVERWRITE ack_note ON to TYPE option<string>` — a FULL REPLACE that DROPS the ASSERT on an existing store (store-ref §1.2, PROBED 2026-07-12; and the ii-b probe's `_downgrade_ack_note` (since 2026-11-07: the shared `unbounded_to_ack_note_ddl()` in `loremaster/tests/_governed_contract.py`) is byte-for-byte this statement, MEASURED on 3.2.4 to drop the bound). `ensure_ready` re-applies it at boot, BEFORE any drain is served — so the migration has no deploy ordering to remember. §3.3 |
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
   `generate_message_ddl()` FIRST, then DOWNGRADE `to.ack_note` with the probe's `_downgrade_ack_note` (since 2026-11-07: the shared `unbounded_to_ack_note_ddl()` in `loremaster/tests/_governed_contract.py`)
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

---

# §12 — ADDENDUM 2026-09-11 · §7-RESOLUTION: the `message` DD-3.c class (sidecar-63b-ii-b-2)

brief-base v14 read
brief project v7 read

## 12.S Summary block (brief-base §1)

- **state:** done (ruling addendum; standing by for the contract fidelity read).
- **deviations:** none. Writable set honoured (this file only, APPENDED — §0–§11 untouched); no git
  mutation — the lead commits. HEAD at addendum: `0566587` (the brief's "0566587" — same).
- **Capability check (brief-base §4):** everything demanded was reachable — lore tools loaded
  (`ToolSearch +lore`; `lore_get_symbol`/`lore_impact`/`lore_search` served the symbol reads),
  `sed`/`awk` for spans, `git` read-only (`-S` history). Text-search binaries are hook-blocked as the
  brief said; every textual sweep below is `awk` over an explicit `find` list and is SAID so where used.
- **Packages considered:** none — no mechanism specified. This addendum REMOVES five store mechanisms
  (ASSERT clauses) and adds tests; the migration rides the existing emitter (`_define_field`,
  `OVERWRITE`) and the existing boot re-apply (`ensure_ready`), exactly as §3.3.
- **Reuse ledger:** none — 0 new production symbols. ONE test-helper lift is RECOMMENDED for the
  contract author's own ledger (§12.6 step 0: a raw legacy-`message` seeder shared by two test files —
  `_governed_contract.py::seed_message_legacy`, beside the existing `seed_memory_legacy`); the contract
  author owns the name and its DRY row.
- **Graded:** `0566587` · HEAD-at-report: `0566587` · SAME.
- **decisions-needed:**
  1. §12.3 RULING — **DROP all FIVE `message` store ASSERTs (thread-len · grade closed-set · body-len ·
     refs count + refs[*] len · task_id len); 0 MOVE, 0 KEEP.** Every one is app-capped BY CONSTRUCTION in
     the ONE writer (§12.1). Binding per the operator's 63b delegation + the verbatim "fix it now"; listed
     so the lead sees it is settled and can see the per-ASSERT receipts.
  2. §12.5 D-M8 — a NAMED BOUND for the operator to ACCEPT or overrule: after the drop, a writer that
     BYPASSES the ledger could land an out-of-domain `grade`; the reader's decode (`InboxEntry.grade:
     MessageGrade`, a `Literal` — read, not executed) then fails LOUD for that recipient's drain. Covered
     by the single-writer floor (P3, extended §12.7) + F5; NOT covered against a hostile author (#138's
     model, already outside §2). Recommendation: ACCEPT as a pinned bound; do not harden the decode.
  3. §12.6 step 0 — the Leg-B seeder lift into `_governed_contract.py` is a REUSE design decision
     (brief-base §6: two files need one raw legacy-row writer). Recommendation: lift. Lead grants
     `_governed_contract.py` to the contract's writable set if accepted.
  4. §12.4 — P2 (`to`) and P2-m (`message`) are ONE parametrized pin over a `table → birth set` map, not
     two pins (ONE IMPLEMENTATION). Recommendation stated; the contract author picks the name.
- **receipt pointers:** the writer inventory §12.1 (`awk` sweep, said so) · the five app caps
  `messages.py::MessageLedger.send` (grade + body inline) and `MessageLedger._reject_oversize_pointers`
  (thread/task_id/refs/refs[*]) · the migrate seam `principals.py::_migrate_message_owner` (one
  `UPDATE message SET owner_agent, owner_principal, scope WHERE owner_principal IS NONE`) · git history
  `df59f76` (birth: grade + body ASSERTs) / `1a6010f` (03b: thread, refs, refs[*], task_id ASSERTs) /
  `eafb8fd` (ii-a: the governed columns + the migrate) · store-ref §1.1 / §1.2 / §1.4 · the existing
  pin classes `test_comms_schema.py::TestThePointerBoundsHaveTheirSTOREBackstop` /
  `::TestMessageSchemaLive` / `::TestThePointerBoundsMigrateADIRTYStore` · the ii-a migrate fixtures
  `test_message_migrate_63b_ii_a.py::message_world` + `::_migrate` · the app-cap pins
  `test_message_ledger.py` (§12.5 D-M2).

---

## 12.0 The ruling in one screen

| # | item | ruling |
|---|---|---|
| R10 | the five `message` ASSERTs | **DROP ALL FIVE.** Each duplicates an app cap in the ONE writer (§12.3 table, symbol-cited, verified by construction). `_MESSAGE_FIELD_SPECS` rows STAY with EMPTY constraints (`refs` keeps `DEFAULT []`, `question` keeps `DEFAULT false`); **no row is deleted** — a spec row that disappears leaves the STORED asserted definition in place forever (store-ref §1.2: only an OVERWRITE that re-lands the field drops its clause). §12.3 |
| R11 | `thread` | ONLY its LENGTH ASSERT drops. Type `string`, REQUIRED/non-`option` — UNTOUCHED (DD-2.b, `TestThreadIsREQUIREDAndNonOptional` stands). §12.3 |
| R12 | `grade` | The closed set is app-validated (`send`: `grade not in MESSAGE_GRADES` → `IllegalMessageGradeError`, ONE vocabulary source — `MESSAGE_GRADES` is built from the schema slice's own `_MESSAGE_GRADE_*` constants) → DROP the store ASSERT; delete `_MESSAGE_GRADE_ALLOWED` (2 hits at HEAD: its definition + the spec row — dead after the drop). The reader-decode bound is D-M8. §12.3 / §12.5 |
| R13 | R2-for-`message` | **`message` is UPDATE-ABLE, not UPDATE-HOT.** Exactly ONE UPDATE path at HEAD — the §4.C cutover backfill, one statement over every NONE-owner row, operator-run ONCE (never at boot). A constraint on `message` is a loaded gun for (a) that cutover (a LOUD, whole-table, retryable refusal of the 65 migrate — not a per-agent silent denial) and (b) any FUTURE `message` UPDATE path. The ∀ invariant is stated and pinned anyway (P2-m), because ONE IMPLEMENTATION forbids the duplicate regardless of the hazard's severity; severity decided only URGENCY ("fix it now"). §12.4 |
| R14 | the dirty-store pin | **TWO legs, both required** (the rider): **Leg A** — the DROP LANDS on a store that carries the ASSERTed definitions (production's shape at `:18500` today): apply the frozen 0566587 DDL → apply `generate_message_ddl()` → each formerly-refused shape is ACCEPTED (RED if the OVERWRITE no-ops: the #107 direction). **Leg B** — the REAL `_migrate_message_owner` survives legacy violators: unbounded old DDL → six violator rows + one clean → apply `generate_message_ddl()` → drive `principals.migrate_governed(table="message")` → not refused, every row stamped, every violator value byte-intact (RED the day any ASSERT is re-added: the DD-3.c direction). §12.6 |
| R15 | the DUAL | Removed behaviour = store-level rejection of six shapes. Adjudicated item-by-item in §12.5: six dropped-deliberately · six virtues preserved-with-pin at the app layer (all six pins EXIST at HEAD, cited) · nine existing tests certify the OLD world — each named with its fate (deleted-with-replacement / split / inverted / kept). One spec-silent bound (D-M8) → operator. |
| R16 | single-writer floor | P3 (§3.4) becomes a PER-TABLE allowlist: `to.ack_note` SET → `{MessageLedger.ack}`; `message` CREATE → `{MessageLedger._send_fragment}`; `message` UPDATE → `{_migrate_message_owner}`. Non-vacuity: all three sites FOUND. §12.7 |
| R17 | deploy ordering | NONE to remember — `ensure_ready` lands the ASSERT-free definitions at the pkt-65 image BOOT (`OVERWRITE`, store-ref §1.1), and the §4.C cutover migrate is a CLI verb run AFTER boot (design §2.3: never at boot). The drop therefore precedes the first `message` UPDATE by construction. §12.8 |
| R18 | supersession inside this doc | §5 D3's clause *"`message` keeps both layers (never UPDATEd after create at 03b; see §7 …)"* is SUPERSEDED: neither table keeps both layers; the app cap is the ONE implementation for both. §7 is RESOLVED by this addendum. Nothing else in §0–§11 changes. §12.9 |

---

## 12.1 The facts this addendum rests on (read at `0566587`; cited, not re-transcribed)

- **The five constraints, verbatim at HEAD** (`surreal_schema.py::_MESSAGE_FIELD_SPECS`, read by `awk`):
  `thread string ASSERT string::len($value) <= MESSAGE_POINTER_MAX_CHARS` (=256) ·
  `grade string ASSERT $value IN [_MESSAGE_GRADE_ALLOWED]` (= `'signal', 'directive'`) ·
  `body string ASSERT string::len($value) <= MESSAGE_BODY_MAX_CHARS` (=4000) ·
  `refs array<string> DEFAULT [] ASSERT array::len($value) <= MESSAGE_REFS_MAX_COUNT` (=20) ·
  `refs[*] string ASSERT string::len($value) <= MESSAGE_POINTER_MAX_CHARS` ·
  `task_id option<string> ASSERT string::len($value) <= MESSAGE_POINTER_MAX_CHARS`.
  Plus, NOT constraints: `question bool DEFAULT false`; the three governed columns
  (`_governed_field_specs`: `owner_principal`/`owner_agent`/`scope`, all `option<>`, empty constraint —
  emitted INSIDE `_message_statements` since ii-a `eafb8fd`).
- **History, derived (`git log -S` on the spec file):** `df59f76` (2026-07-23, packet 03) shipped the
  birth set `{seq, session, thread, sender, grade, body, refs, task_id, question, created_at}` with
  exactly TWO ASSERTs (grade, body); `1a6010f` (2026-07-25, 03b) added the four pointer ASSERTs
  (thread, refs count, the `refs[*]` element row, task_id) and minted `MESSAGE_POINTER_MAX_CHARS` /
  `MESSAGE_REFS_MAX_COUNT`; **no cap constant has EVER been changed since it was minted**
  (`MESSAGE_BODY_MAX_CHARS = 4000` appears in one commit only, `df59f76`). All five ASSERTs therefore
  shipped in or before the 03b deploy of 2026-07-26 (§4.2's dating) — so production exposure TODAY is
  ZERO BY CONSTRUCTION, with §4.2's stated bound (an image hash, not a sha) applying identically.
- **The production writers of `message` rows — a bare-pattern `awk` sweep of every `*.py` under
  `loremaster/loremaster/ lorerunes/ lorescribe/ loresigil/ scripts/` (text-search binaries hook-blocked;
  said so), patterns `CREATE|UPDATE|UPSERT|INSERT` against `MESSAGE_TABLE`/`message`, plus `.send(`:**
  - CREATE: **exactly one** — `messages.py::MessageLedger._send_fragment` (the `CREATE type::record('message', $msg_id) CONTENT {…}` inside `send`'s one transaction).
  - UPDATE: **exactly one** — `principals.py::_migrate_message_owner` (`UPDATE message SET owner_agent = sender, owner_principal = sender.owner_principal, scope = $scope WHERE owner_principal IS NONE`, inside `governed_exempt("migrate-governed")`, driver-routed via `run_query`). It SETs only the three governed columns — never a constrained field — so under SCHEMAFULL whole-record re-validation (store-ref §1.4) it re-validates every legacy row's `thread/grade/body/refs/refs[*]/task_id` against whatever ASSERT the store holds at cutover time.
  - Callers of `send`: `server.py::AppContext._comms_send` (the tool handler — resolves Subject, scope, recipients, then `self.message_ledger.send(...)` inside `write_guard("send")`; it validates NOTHING the ledger does not, and needs to validate nothing — the caps are the ledger's) and `scripts/comms_consumer_eval.py` (a consumer-eval harness driving the real ledger; not a second writer).
  - Residual raw CREATE hits, each with a verdict: `scripts/probe_read_filter_63.py` (a committed PROBE's fixture writer — not production; it writes under a probe DB) — verdict: not a writer of the served store. Tests' `_create_message` helpers — test fixtures, by design raw.
- **Every one of the five bounds is enforced at the app layer, in the ONE writer, BEFORE the write
  (verified by READING the code path, not by assuming — the #107 lesson):** `MessageLedger.send`'s
  synchronous prologue runs, in order: `grade not in MESSAGE_GRADES → IllegalMessageGradeError`;
  `body.strip()` blank → `MessageBodyError`; `len(trimmed) > MESSAGE_BODY_MAX_CHARS → MessageBodyError`;
  then `self._reject_oversize_pointers(thread=, task_id=, refs=)` which checks `len(refs) >
  MESSAGE_REFS_MAX_COUNT`, then each `len(ref) > MESSAGE_POINTER_MAX_CHARS`, then each of
  `("thread", thread), ("task_id", task_id)` for `len(value) > MESSAGE_POINTER_MAX_CHARS` (None skipped).
  The `thread` default (`thread if thread is not None else session`) is applied AFTER the check on the
  raw argument — `session` is itself bounded upstream by the identity charset/length of the agent row
  (`_validate_comms_charset`), so the defaulted value is ≤ cap; a row's `thread` is never unbounded via
  the default path. `lore_impact(_reject_oversize_pointers)` → 1 prod consumer (`send`), covering tests
  21 across `_message_fakes` (the fake oracle CALLS it — "so the two enforcements cannot drift").
- **The store-side backstop's only remaining job was the SECOND-WRITER threat**
  (`TestThePointerBoundsHaveTheirSTOREBackstop`'s docstring: *"a LEDGER-ONLY build … any future writer
  that does not go through `MessageLedger.send` lands an unbounded row silently"*). At HEAD that threat is
  ALSO covered by F5 (ii-a: every `message` write is observed as a state diff; an unattributed write that
  LANDS is denied — reach = executed frames, §1.5c) and can be given a static floor (§12.7).
- **`grade` has ONE vocabulary source:** `messages.py` builds `MESSAGE_GRADES` from the schema slice's
  `_MESSAGE_GRADE_SIGNAL/_MESSAGE_GRADE_DIRECTIVE` (its own comment: "the ledger's app-level check and
  the store's ASSERT can never spell the vocabulary differently"). After the drop the schema module's
  `_MESSAGE_GRADE_ALLOWED` (the `', '`-joined literal) has NO consumer — `awk` over prod+tests found
  exactly two hits: its definition and the spec row.

---

## 12.2 THE THREAT MODEL for `message` — the §2 table, re-derived for this table

**Who are the five ASSERTs for?** The honest developer who adds a SECOND production writer of `message`
without the ledger's caps (DD-3.c's own words). NOT a hostile author (#138), NOT the consumer agent (the
render side already bounds what it serves).

**Who is hurt by them?** The honest developer who does any of:
- (T1) **lowers a cap** — `MESSAGE_BODY_MAX_CHARS`, `MESSAGE_POINTER_MAX_CHARS` or `MESSAGE_REFS_MAX_COUNT`
  (one constant each; the most ordinary edit imaginable, and §2 already named the first);
- (T2) **narrows the grade vocabulary** — retires `directive` or renames a grade (the closed-set ASSERT
  makes every legacy row of the retired grade a violator);
- (T3) **adds any constraint to `message`** — an ASSERT on a new field, a non-`option<>` field, a TYPE change.

Under any of these, every gate is green (virgin DBs, store-ref §1.6) and **the pkt-65 cutover's
`migrate-governed --table message` is REFUSED WHOLESALE** on the long-lived store: one legacy row that
violates the new definition aborts the ONE backfill statement, zero rows are stamped, and the message
table stays un-governed. Loud (the CLI verb errors, naming field + value), whole-table, retryable — but
with no heal path except a hand-typed UPDATE, on the day of the cutover, discovered at the cutover.

| failure | who causes it | what a gate sees | production consequence |
|---|---|---|---|
| ASSERTs ABSENT, a second writer lands a junk row | honest dev adding a writer without the caps | F5 reds an unattributed `message` write it EXECUTES; the P3 floor (§12.7) reds the new CREATE/UPDATE site | one junk row; render-side bounds still hold; a junk `grade` row is D-M8 |
| ASSERTs PRESENT, a cap lowered / a grade retired / a constraint added | honest dev editing one constant | NOTHING (green on virgin) | **the 65 cutover migrate refuses for the whole table** (and any later `message` UPDATE path inherits the denial) |

**The verdict follows, and it is §2's verdict with a smaller blast radius:** five duplicated bounds,
each already enforced by the ONE writer and observable by F5, guarded at the price of arming the cutover
against the most ordinary honest edits. The severity is LOWER than `to`'s (a one-shot operator verb, not
every agent's inbox), which is why §7 could honestly say "not live today"; the DUPLICATION is the same,
which is why ONE IMPLEMENTATION rules the same way. **Drop them.**

---

## 12.3 RULING R10–R12 — the per-ASSERT verdict table (verified by construction, per constraint)

| constraint (store, at `0566587`) | app cap found? — SYMBOL (read, not assumed) | app-cap PIN at HEAD | verdict |
|---|---|---|---|
| `thread` `ASSERT string::len($value) <= 256` | YES — `MessageLedger._reject_oversize_pointers`, the `("thread", thread)` leg → `MessagePointerError` naming the field | `test_message_ledger.py::…::test_an_over_length_pointer_LABEL_is_REJECTED[thread]` + parity scenario `thread_len` | **DROP** the length ASSERT. Type/requiredness UNTOUCHED (R11). |
| `grade` `ASSERT $value IN ['signal', 'directive']` | YES — `MessageLedger.send`, first statement: `grade not in MESSAGE_GRADES → IllegalMessageGradeError`; `MESSAGE_GRADES` is derived from the schema's `_MESSAGE_GRADE_*` (one source) | `test_an_out_of_domain_grade_is_rejected` + `test_grade_is_a_closed_two_value_domain` (Literal ≡ constants) + parity `illegal_grade` | **DROP.** Delete the now-dead `_MESSAGE_GRADE_ALLOWED`. Reader-decode bound → D-M8 (operator). |
| `body` `ASSERT string::len($value) <= 4000` | YES — `MessageLedger.send`: `len(trimmed) > MESSAGE_BODY_MAX_CHARS → MessageBodyError` (teaching reject naming `refs`) | `test_an_oversize_body_is_REJECTED_not_truncated` (frontier #19: raises AND nothing lands) + parity `overcap_body` | **DROP.** |
| `refs` `DEFAULT [] ASSERT array::len($value) <= 20` | YES — `_reject_oversize_pointers`: `len(refs) > MESSAGE_REFS_MAX_COUNT → MessagePointerError` | `test_an_over_COUNT_refs_list_is_REJECTED` + positive control `test_POSITIVE_CONTROL_refs_exactly_at_both_caps_are_accepted` + parity `refs_count` | **DROP the ASSERT; KEEP `DEFAULT []`** (a DEFAULT is not a violation source; a ref-less send must still omit the field — existing pin half survives). |
| `refs[*]` `ASSERT string::len($value) <= 256` | YES — `_reject_oversize_pointers`: per-entry `len(ref) > MESSAGE_POINTER_MAX_CHARS → MessagePointerError` naming `refs[index]` | `test_an_over_length_ref_is_REJECTED_naming_its_index` + the same positive control + parity `refs_entry_len` | **DROP the ASSERT; KEEP THE ROW, as `("refs[*]", "string", "")`, still `OVERWRITE`.** ⚠ The row must stay for TWO reasons: (i) `TYPE array<T>` implicitly defines `refs.*`, so a bare re-definition raises (the existing comment) — and, NEW: (ii) **the stored `refs[*]` definition on `:18500` CARRIES THE ASSERT; only an emitted `OVERWRITE refs[*] … TYPE string` with no clause drops it.** Deleting the row would leave that ASSERT in the store forever (store-ref §1.2) — the #107 shape from the other side. Leg A pins this (§12.6). |
| `task_id` `option<string> ASSERT string::len($value) <= 256` | YES — `_reject_oversize_pointers`, the `("task_id", task_id)` leg (None skipped, mirroring the bare option<> ASSERT's non-evaluation on NONE) | `test_an_over_length_pointer_LABEL_is_REJECTED[task_id]`; ⚠ NO parity scenario `task_id_len` at HEAD (the parity set covers error CLASSES, so the fake oracle is unpinned for this one field — W15 adds it) | **DROP.** |

**Tally: 5 DROP · 0 MOVE · 0 KEEP.** No `_reject_oversize_*` sibling needs to be ADDED — the brief's
"NOT app-capped" branch is EMPTY at `0566587`, and that is a finding derived from reading the writer, not
an assumption: each row above cites the exact predicate.

**What "DROP" means mechanically (R3 applies verbatim):** each `_MESSAGE_FIELD_SPECS` row keeps its name
and type and gets an EMPTY constraint (`refs` → `"DEFAULT []"`); `_define_field` then emits `DEFINE FIELD
OVERWRITE <f> ON message TYPE <t>` — a FULL REPLACE that DROPS the stored ASSERT on an existing store
(store-ref §1.2, PROBED 2026-07-12; and §3.3's `to` probe measured the identical statement shape dropping
`ack_note`'s bound on 3.2.4). `ensure_ready` re-applies it at boot. `IF NOT EXISTS` would be the #107
no-op; `ALTER` would be the §1.3 trap (a PATCH keeps the omitted ASSERT forever). Leg A (§12.6) is the
instrument that proves the drop LANDED on an asserted store, because an offline DDL-text pin cannot.

---

## 12.4 RULING R13 — R2 for `message`: UPDATE-ABLE, not UPDATE-HOT — the invariant, ∀, and pin P2-m

> **`message` has exactly ONE UPDATE path at `0566587`** — `_migrate_message_owner`'s §4.C backfill:
> one statement over every NONE-owner row, run ONCE by the operator at the 65 cutover, never at boot,
> idempotent (a second run matches zero rows and re-validates nothing). **It is not UPDATE-hot**: no
> per-call path touches a `message` row after CREATE (drain/ack/await write `to`, never `message`).
> **Therefore a constraint on `message` is a loaded gun with a NARROWER field of fire than `to`'s:** it
> fires (a) at the cutover — a LOUD, whole-table, retryable refusal of an operator-run verb, discovered
> at the cutover, healable only by hand; and (b) on any FUTURE `message` UPDATE path (a redaction, an
> edit, a 64+ re-scope), which inherits `to`'s full hazard the day it lands. It does NOT fire per agent,
> per call, or silently. **The invariant is nonetheless stated ∀ fields of `message` and pinned**,
> because the rule that forbids the duplicate is ONE IMPLEMENTATION (§"ONE IMPLEMENTATION", #102), and
> that rule does not scale with severity — severity decided only WHEN ("fix it now"), not WHETHER.

**The askable form** (THE LEVER; §3.4's question, re-aimed): *"Does ANY statement — today's cutover
migrate, or a path I am adding — UPDATE this table without SETting the field I am constraining? If yes,
which legacy rows would my constraint refuse, who heals them, and does the heal run BEFORE that
statement?"* For `message` at HEAD the answer names one statement; the day it names two, this is `to`.

**Pin it like this — P2-m (offline, DDL-text, `test_comms_schema.py`, beside P2 — and RECOMMENDED as ONE
parametrized pin over `{to, message}` with a per-table birth-set map, never two clones):**
- Derive the statements from `generate_message_ddl()` (the house idiom — assert what we SEND, never
  `INFO FOR TABLE`'s normalised echo), select every `DEFINE FIELD OVERWRITE <f> ON message …`, and assert
  for EACH: no `ASSERT`; `DEFAULT` only on the birth-DEFAULT set `{refs, question}` (a post-birth DEFAULT
  falsely promises to rescue legacy rows — store-ref §1.4: it does not); and, for every field not in the
  BIRTH set `{seq, session, thread, sender, grade, body, refs, refs[*], task_id, question, created_at}`
  (df59f76 + the 1a6010f element row — a CONSTANT in the pin with a comment naming why: written at birth,
  populated on every legacy row), the type starts with `option<`. At HEAD the post-birth set is exactly
  the three governed columns, all `option<>` (§12.1) — the pin is GREEN on a correct build.
- **Non-vacuity control:** the derived field set is non-empty AND ⊇ `{body, refs[*], owner_principal}`
  (a derivation that misses the element row or the governed overlay must red, not pass).
- **Its failure message carries the bound:** *"`message` is UPDATE-able (the §4.C cutover migrate
  re-validates every legacy row in ONE statement; a future UPDATE path would too): a constraint here is
  DD-3.c — a legacy row that violates it refuses the whole statement (63b-ii-b ruling §12.4). The app cap
  in `MessageLedger.send` is the ONE implementation. If you are adding a constraint DELIBERATELY you owe
  (a) a heal that runs BEFORE the first `message` UPDATE and (b) §12.6 Leg B inverted for that field —
  then delete this pin and say so."*
- **Re-open triggers (named, per the deferral law):** (i) the day `message` gains a per-call UPDATE path
  → this bound is `to`'s R2 in full force (nothing to change in the pin; its message gets `to`'s wording);
  (ii) the day the §4.C migrate is RETIRED (post-65, every row stamped) AND no UPDATE path remains → a
  constraint on `message` is a per-row CREATE rejection again, and the HAZARD half of this bound may be
  retired — the ONE IMPLEMENTATION half may not: the app cap stays the sole enforcement regardless.
- **Mutation proof (the rider):** re-add ANY one of the five ASSERTs to `_MESSAGE_FIELD_SPECS` → P2-m RED;
  add a row `("x", "string", "")` → P2-m RED (non-option post-birth); add `("y", "option<string>",
  "DEFAULT 'z'")` → RED (post-birth DEFAULT); restore → GREEN. Declare the expected-RED ids from
  `--collect-only` before the run (`scripts/mutation_proof.py`).

---

## 12.5 THE DUAL — removed-behaviour inventory for `message`, adjudicated item by item

The removed behaviour: **the store rejects, on any write path, a `message` row whose `thread` or
`task_id` exceeds 256 chars, whose `grade` is outside `{signal, directive}`, whose `body` exceeds 4000
chars, whose `refs` holds more than 20 entries, or any `refs` entry exceeding 256 chars.** Every virtue
and every pin that depended on it (derived from the `awk` inventory of `ASSERT`/`backstop`/`both
layers`/`never UPDATEd` over `test_comms_schema.py`, `test_message_ledger.py`, `messages.py`,
`surreal_schema.py` — said so):

| # | item | adjudication | receipt / pin |
|---|---|---|---|
| D-M1 | store-level rejection of the six shapes (DD-3.c "at BOTH layers, mirroring `body`") | **DROPPED DELIBERATELY** — reason §12.2/§12.3: six duplicated bounds, each enforced by the ONE writer and observed by F5, arming the 65 cutover against T1/T2/T3. | this addendum |
| D-M2 | the six BOUNDS themselves (DD-3.c/DD-3.f: pointers are ADDRESSES; a body is capped so the drain render is bounded) | **PRESERVED-WITH-PIN at the app layer — all six pins EXIST at HEAD** (§12.3, column 3), each a teaching reject at cap+1 with a positive control AT the cap, and six of the seven under the `_PARITY_SCENARIOS` ∀-error-class coverage pin. Cited to the SPEC clauses, not to "the old code did it". The seventh (`task_id`) has its direct pin but no parity scenario → **W15** adds `task_id_len` so the fake oracle is pinned per field, not per class. | `test_message_ledger.py` (§12.3 col 3) |
| D-M3 | `TestThePointerBoundsHaveTheirSTOREBackstop::test_refs_carries_its_COUNT_assert` (offline: ASSERT + DEFAULT) | **SPLIT** — the ASSERT half is DELETED-WITH-REPLACEMENT (P2-m asserts the inverse ∀); the `DEFAULT []` half is KEPT as its own pin (a ref-less send must still omit the field). | W11 |
| D-M4 | `…::test_the_ELEMENT_row_carries_the_per_entry_assert_AND_overwrite` | **SPLIT** — the ASSERT half DELETED-WITH-REPLACEMENT (P2-m); the `startswith("DEFINE FIELD OVERWRITE refs[*] ")` half KEPT and its docstring gains the SECOND reason (§12.3 refs[*] row: the OVERWRITE is what drops the stored ASSERT on `:18500`; Leg A is its live twin). | W11 / W12 |
| D-M5 | `…::test_the_pointer_LABELS_carry_bare_length_asserts[thread,task_id]` (ASSERT present + no NONE-guard) | **DELETED-WITH-REPLACEMENT** — both halves are moot with no ASSERT; P2-m covers the inverse. The NONE-guard lesson (an option<> ASSERT is not evaluated on NONE) survives in `_reject_oversize_pointers`'s `value is not None` leg, which is pinned by the app-cap positive control. | W11 |
| D-M6 | `TestMessageSchemaLive::test_an_out_of_domain_grade_is_rejected_by_the_store`, `::test_an_oversize_body_is_rejected_by_the_store_backstop`, `::test_an_oversize_REF_ENTRY_…`, `::test_an_over_COUNT_refs_list_…`, `::test_an_oversize_pointer_LABEL_…[thread,task_id]` (LIVE rejections) | **DELETED-WITH-REPLACEMENT** — they certify the corpse (the rename-sweep law). Replacement = D-M2's app pins + Leg A (which asserts the INVERSE live property on a dirty store). `::test_both_legal_grades_are_accepted` and `::test_POSITIVE_CONTROL_a_legal_pointer_row_IS_accepted` are KEPT (they still certify that legal rows land — fixture-liveness controls for Leg A's class). | W11 |
| D-M7 | `TestThePointerBoundsMigrateADIRTYStore` (BASELINE · bound-is-LIVE-after-migrating · row-SURVIVES · idempotent) | **INVERTED into Leg A** (§12.6): same `_old_message_ddl` construction, but the "old world" is now the ASSERTED 0566587 world and the assertion flips — after `generate_message_ddl()` the formerly-refused shapes are ACCEPTED. `row-SURVIVES` folds into Leg B (values byte-intact after the migrate). `idempotent` is KEPT verbatim (the element-row OVERWRITE double-apply). The class docstring's *"harmless here because message rows are never UPDATEd after create"* is STALE since `eafb8fd` regardless of this ruling — rewrite, dated. | W12 |
| D-M8 | the virtue *"a junk `grade` cannot exist in the store, so every reader's `Literal` decode is total"* — `Message.grade`/`InboxEntry.grade: MessageGrade` (a `Literal`; by the annotation, READ not executed, pydantic rejects a junk value → that recipient's drain raises on decode; `StoryMessage.grade: str` renders it) | **SPEC-SILENT → OPERATOR** (decisions-needed 2). Recommendation: ACCEPT as a NAMED BOUND — it is reachable only through a writer that bypasses the ledger (the honest-developer case is covered by the P3 floor §12.7 + F5; the hostile author is outside §2's model, #138). Do NOT harden the decode (a lenient decode would silently mis-grade a directive — worse than loud). If accepted: the bound is stated IN the P3 floor's docstring, not in a separate pin. | §12.7 |
| D-M9 | `_MESSAGE_FIELD_SPECS` comments: the element-row paragraph (*"the element path is what buys the per-entry ERROR"*) and the *"BARE asserts on the two pointer labels"* paragraph; `_message_statements` docstring (*"the closed `grade` domain, the length-bound `body` backstop"*) | **REWRITTEN** — stale prose otherwise (a comment teaching an ASSERT that is gone is a served-surface defect of exactly the P8d class). The element-row comment KEEPS reason (i) and GAINS reason (ii) (§12.3). | W9 |
| D-M10 | `messages.py::_reject_oversize_pointers` docstring: *"the store ASSERTs are the backstop underneath it — a writer that bypasses this method fails LOUDLY at the engine rather than landing an unbounded row"*; and the `# --- closed vocabularies` comment: *"so the ledger's app-level check and the store's ASSERT can never spell the vocabulary differently"* | **REWRITTEN** — both now name F5 + the P3 floor as the second-writer instrument and this addendum as the reason; the vocabulary comment keeps its ONE-source point (still true and still the reason the constants are imported from the schema slice). No behaviour change. | W10 |
| D-M11 | `TestThePointerBoundsHaveTheirSTOREBackstop` class docstring (DD-3.c both layers); `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge`'s *"The sibling class above covers `message`, where the original reasoning happened to hold"* | **REWRITTEN** (the first is renamed — it no longer certifies a store backstop; e.g. `TestTheMessageStoreCarriesNoAssertALegacyRowCanViolate`); §5 D3's planned paragraph *"`message` keeps both layers"* is SUPERSEDED (R18) — the paragraph now says: neither table carries a store ASSERT; the app cap is the ONE implementation for both; cite §3.4 and §12.4. | W11 |
| D-M12 | `server.py` comms tool description prose (*"capped at N characters … over-cap is REJECTED, never truncated"*, the refs/thread/task_id bounds) | **STANDS** — describes the app layer, which is unchanged. Verified each hit (`awk`, §12.1): none mentions the store. | — |
| D-M13 | store-ref §1.4 / §1.6 examples | outside my writable set — **FLAG** (as §5 D7): the lead may add one dated line under §1.4 citing §3 and §12 as the `to`/`message` receipts. | lead |

Spec-silent items requiring an operator ruling: **D-M8 only.**

---

## 12.6 THE MIGRATE DIRTY-STORE PIN — P1-m, "pin it like this" (the contract author carries this verbatim)

**Threat model of the pin:** the honest developer who re-adds a constraint to `message` (or lowers a
cap, or retires a grade) with every virgin-DB gate green — AND the honest developer whose emitter change
emits perfectly and never LANDS on the asserted store (#107). Two directions, two legs; each RED the day
its hazard reopens.

**Step 0 — the raw legacy-row seeder (ONE IMPLEMENTATION):** both legs, and Leg B in a second file, need
a RAW `CREATE message` that bypasses the ledger's caps (that is the hypothesis under test: a row the app
cap would refuse). `test_comms_schema.py::_create_message` already exists; the ii-a migrate file has none
(it seeds through the real `send`). RECOMMENDED: lift ONE seeder into `_governed_contract.py` as
`seed_message_legacy(connection, *, sender_id, session, seq, **overrides)` beside `seed_memory_legacy`,
writing every required column (`seq, session, thread, sender, grade, body, refs, question, created_at`)
with legal defaults, `owner_principal/owner_agent/scope` bound NONE (a legacy row), and any override
verbatim — then both files call it. A second copy is the #102 seam; the contract author's DRY ledger
carries the row.

**Leg A — THE DROP LANDS on an ASSERTED store (the #107 direction). `test_comms_schema.py`, in place of
`TestThePointerBoundsMigrateADIRTYStore` (renamed to what it now certifies, e.g.
`TestTheMessageAssertsAreDroppedFromADIRTYStore`):**
1. **OLD world = production's shape:** apply `generate_agent_ddl()`; then a FROZEN constant
   `_ASSERTED_MESSAGE_DDL_AT_0566587` — the eleven `DEFINE FIELD OVERWRITE … ON message` statements
   exactly as `generate_message_ddl()` emitted them at `0566587` (the five ASSERT-bearing rows verbatim,
   plus the governed overlay), hand-captured and labelled with the sha in a comment. A frozen capture is
   the honest fixture here: the old world is a FACT (what `:18500` holds today), not a derivation.
   ⚠ Store-ref §1.4's trap applies in reverse: the CLEAN control row must be written UNDER the asserted
   DDL (proving the table is live), and the violator writes in step 2 must ALSO be attempted under it.
2. **BASELINE (positive control, the same class):** under the asserted DDL, each of the SIX violator
   shapes — `body` at cap+1 · `thread` at cap+1 · `grade='urgent'` · `refs` of cap+1 entries · one ref at
   cap+1 · `task_id` at cap+1 — is REJECTED by the engine (`pytest.raises`, the ASSERT-violation surface).
   Without this leg, "accepted after migrating" could be true because the shape was never refused.
3. **Migrate:** apply `generate_message_ddl()` (the CURRENT emitter — under this ruling it re-lands every
   row with no clause; under a wrong build that keeps an ASSERT, or an emitter that regressed to
   `IF NOT EXISTS`, the stored clause survives).
4. **Assert, parametrized over the six shapes:** the same raw CREATE is now ACCEPTED, and a read-back of
   the row returns the over-cap value byte-intact (`len(body) == MESSAGE_BODY_MAX_CHARS + 1`, etc.).
   `grade='urgent'` lands as `'urgent'`.
5. **Keep** the existing `idempotent` leg (double-apply of `generate_message_ddl()` then a legal CREATE).
6. **Mutation proof (declared before the run):** re-add ONE ASSERT (say `body`) → exactly the `body`
   parametrization of step 4 RED with the engine's *"must conform to"* text, the other five GREEN, and
   P2-m RED; restore → GREEN. Per-shape discrimination is what the six-way parametrization buys — a build
   that drops four of five is caught on the fifth, BY NAME.

**Leg B — THE REAL MIGRATE SURVIVES LEGACY VIOLATORS (the DD-3.c direction). Lives with the migrate's own
contract — `test_message_migrate_63b_ii_a.py` (or a sibling `test_message_migrate_dirty_store_63b_ii_b.py`
importing its fixtures); the contract author states which:**
1. **OLD world = the UNBOUNDED construction** (a world that never shipped — it exists to ACCEPT the
   violators; say so in its docstring): `generate_agent_ddl()`; then the existing `_old_message_ddl`
   shape (every birth field, NO ASSERT) PLUS `governed_overlay_ddl(MESSAGE_TABLE)` (the three option<>
   columns + two indexes; `_governed_contract.py`, already decoupled from the emitter for exactly this
   use); then the `message_world` preconditions the migrate REQUIRES — one operator principal, and
   agents registered with `owner_principal_id` set (the §2.6 agent-first precondition, else the migrate
   REFUSES before it UPDATEs and the pin measures nothing — a fixture that trips the refusal reads as
   RED-for-the-wrong-reason; assert `result.refused is False` FIRST, with the reason in the message).
2. **Dirty rows, written UNDER the old DDL by the step-0 seeder:** SIX legacy rows (`owner_principal`
   NONE, `sender` = the migrated agent), one per violator shape of Leg A step 2, PLUS one CLEAN legacy
   row sent through the REAL `ledger.send` (as `message_world` does — an un-stamped legacy send). Seven
   NONE-owner rows total; record their ids.
3. **Migrate the SCHEMA:** apply `generate_message_ddl()` (the current emitter — the step where a wrong
   build lands an ASSERT onto the dirty store).
4. **Act through the PRODUCTION seam, never a hand-typed statement:** `await _migrate(connection, env,
   table=MESSAGE_TABLE, keep_store=…, principal_store=…)` — i.e. `principals.migrate_governed(table=
   "message", store=<StoreHandle>, …)` dispatching to the real `_migrate_message_owner` (ROUTING IS NOT
   SHARING: a copied `UPDATE message SET …` is a private copy that drifts from the migrate).
5. **Assert:** (a) `result.refused is False` (reason rendered on failure); (b) `result.backfilled == 7`
   and `result.already_migrated == 0`, `scanned == 7`; (c) a read-back `SELECT id, owner_principal,
   owner_agent, scope, thread, grade, body, refs, task_id FROM message` (explicit projection — the house
   rule) shows EVERY one of the seven with `owner_agent == sender`, `owner_principal == sender's`, `scope
   == keep:<project>`; (d) every violator VALUE is byte-intact (store-ref §1.4: a migration converges
   schema, never data — and this ruling adds no heal): `len(body) == cap+1`, `grade == 'urgent'`,
   `len(refs) == 21`, etc.; (e) **idempotence on the dirty store**: a SECOND `_migrate` call returns
   `backfilled == 0, already_migrated == 7`, not refused.
6. **Controls in the same class:** BASELINE — the unbounded world accepted all seven (count == 7 before
   step 3; else "migrate succeeded" could be success over an empty set); and the C-CONTROL that proves the
   instrument can SEE the hazard: a leg that applies `_ASSERTED_MESSAGE_DDL_AT_0566587` at step 3 instead
   of the current emitter and asserts the migrate RAISES (`SurrealStoreError`, the engine text naming the
   field) with ZERO rows stamped (read-back: all seven still NONE-owner). This is the measured DD-3.c
   mechanism reproduced on `message`, so the pin is self-validating rather than trusting a mutation run.
7. **Mutation proof (declared before the run, `--collect-only` ids):** re-add ONE ASSERT to
   `_MESSAGE_FIELD_SPECS` → Leg B's main leg RED with the engine's text naming that field; Leg A's
   matching parametrization RED; P2-m RED; the C-CONTROL stays GREEN (it uses the frozen DDL); restore →
   all GREEN. Both directions are diffed (`scripts/mutation_proof.py`): an unexpected green is the
   mutation landing in dead code.

**Why two legs and not one:** Leg B's fixture cannot start from the ASSERTED world (the violators cannot
be written under it), so it cannot see an emitter that fails to LAND the drop; Leg A's fixture never runs
the migrate, so it cannot see a re-added constraint denying it. Each is blind exactly where the other is
strong — the TRUST doctrine's two-leg shape at test scale.

**Reach, stated (INSTRUMENT 0):** these pins cover the six shapes ENUMERATED from `_MESSAGE_FIELD_SPECS`
at `0566587`. A SEVENTH constraint added later is caught by P2-m (∀ over the emitted DDL, a derived set),
which is why P2-m is not optional beside them — the legs pin the mechanism, P2-m pins the reach.

---

## 12.7 RULING R16 — the single-writer floor, per table (P3 extended; the ∀ instrument stays F5)

W4's P3 (a bare-pattern scan over the `_SCANNED_MEMBERS`-derived production modules for `ack_note` in a
`SET`/`CONTENT` clause, allowlist `{MessageLedger.ack}`) becomes ONE scan over a `table → {sites}` map:

| write | allowlisted safe set (EXACT) | non-vacuity |
|---|---|---|
| `to.ack_note` in SET/CONTENT | `{MessageLedger.ack}` | must find `ack` |
| `message` CREATE (`CREATE … 'message'`/`MESSAGE_TABLE` in a statement literal) | `{MessageLedger._send_fragment}` | must find `_send_fragment` |
| `message` UPDATE/UPSERT/INSERT | `{principals._migrate_message_owner}` | must find `_migrate_message_owner` |

Threat model IN the pin's docstring (a gate needs one): the honest developer adding a writer without the
ledger's caps — a new CREATE site outside `_send_fragment`, or a new UPDATE path that inherits DD-3.c
(the day this table grows a second entry, §12.4's re-open trigger (i) has fired and the author owes the
heal + the inverted Leg B). NOT a hostile author (`"mess" + "age"`, a table-name variable — #138's shape,
ledgered, not paid for in false positives). D-M8's bound is stated here if the operator accepts it. This
is the static FLOOR; the ∀ instrument is F5's effect predicate, whose reach is the battery's executed
frames (ii-a §1.5c) — the docstring says so. `_governed_contract.py::governed_table_raw_mutation_sites`
already derives raw mutation sites per table for the F5 registration pins — REUSE its derivation for the
site set rather than a second regex (brief-base §6; the contract author's DRY row names it).

---

## 12.8 Deploy & close-out — R17, and the R6-shaped receipt for `message`

- **Ordering: none to remember.** pkt-65's image boots → `ensure_ready` applies `generate_message_ddl()`
  → every `message` field is re-landed clause-free (`OVERWRITE`) BEFORE the store serves; the cutover's
  `lore-adm migrate-governed --table message` is run by the operator AFTER boot (design §2.3: never at
  boot). So on the day the first `message` UPDATE ever runs against `:18500`, the ASSERTs are already
  gone. Under this ruling the migrate cannot meet a legacy violator even if one existed.
- **For the RUNNING image (until 65): expected ZERO violators BY CONSTRUCTION** (§12.1: every ASSERT
  predates the 03b deploy; no cap ever lowered; no grade ever retired). The receipt is the lead's, at
  ii-b close-out, one read-only statement on `:18500` (never a test):
  `SELECT count() FROM message WHERE string::len(body) > 4000 OR string::len(thread) > 256 OR
  array::len(refs) > 20 OR (task_id != NONE AND string::len(task_id) > 256) OR grade NOTINSIDE ['signal',
  'directive'] GROUP ALL` — expected `[]`/0 (⚠ the per-entry `refs[*]` predicate needs a closure or
  `array::any` form — verify the spelling against store-ref §2/§7 or `lore_search(tier="surrealql-tests",
  "array::any closure")` before running; a parse error is not a zero). And `INFO FOR TABLE message`
  showing the five ASSERTs on the STORED definitions — the "before" receipt that proves Leg A's frozen
  old world IS production's shape (a fact this addendum BELIEVES from dates, exactly as §4.2 does).
- **Decision point (named):** owner = **lead-63b-iib**, when = **ii-b close-out**, input = the two reads.
  Count 0 → record in the INDEX Log line. Count > 0 → a `lore_findings` row (kind=bug) and NO action
  needed for correctness (the ruling removes the clause the row would violate; the row is inert) — but
  the row's origin is a second writer or a corrupted store and must be explained before 65.

---

## 12.9 What this addendum changes inside §0–§11 (supersession, stated so the doc does not contradict itself)

- **§5 D3**, the clause *"The class docstring of `TestThePointerBoundsHaveTheirSTOREBackstop` gains one
  paragraph: `message` keeps both layers (never UPDATEd after create at 03b; see §7 for the ii-a caveat);
  `to` is the exception, and why"* → **SUPERSEDED by D-M11**: neither table keeps both layers; the class
  is renamed; the paragraph states the ONE-implementation rule for both tables and cites §3.4 + §12.4.
- **§7** → **RESOLVED**: option (a) as ruled by the operator, with the pin from (b) — both legs — carried
  as the rider, not instead of the fix.
- **§8 riders roll-up** gains the rows below (the contract author / adversary index):

| pin | what | where | RED when |
|---|---|---|---|
| P1-m-A | the DROP lands on an ASSERTED `message` store: six shapes ACCEPTED after `generate_message_ddl()`; BASELINE refuses them under the frozen 0566587 DDL (§12.6 Leg A) | `test_comms_schema.py` (inverted `…MigrateADIRTYStore`) | an ASSERT survives on the store / the emitter no-ops |
| P1-m-B | the REAL `migrate_governed(table="message")` survives seven legacy rows (six violators + one clean): not refused, 7 backfilled, values byte-intact, idempotent; C-CONTROL: the frozen asserted DDL makes it RAISE with zero stamped (§12.6 Leg B) | the migrate contract file | any ASSERT re-added / cap lowered / grade retired |
| P2-m | `message` carries no ASSERT ∀ emitted fields; DEFAULT only on `{refs, question}`; post-birth ⇒ `option<`; non-vacuity ⊇ `{body, refs[*], owner_principal}` (§12.4) — RECOMMENDED as one parametrized pin with P2 | `test_comms_schema.py`, offline DDL text | a constraint / non-option post-birth field / post-birth DEFAULT lands |
| P3 (ext.) | per-table single-writer floor: `to.ack_note` SET · `message` CREATE · `message` UPDATE, exact allowlists, non-vacuity on all three (§12.7) | the W4 scan | a second site lands |
| D-M2 | the six app caps stand (existing pins) + W15's `task_id_len` parity scenario | `test_message_ledger.py` | — |
| M | mutation proofs for P1-m-A / P1-m-B / P2-m declared from `--collect-only`, diffed both ways | `scripts/mutation_proof.py` | — |

- **§10 worklist** gains W9–W17 (§12.10). W1–W8 are unchanged.

---

## 12.10 Contract-revision worklist — the `message` items (continuing §10's numbering)

- **W9** `surreal_schema.py::_MESSAGE_FIELD_SPECS` — constraints of `thread`/`grade`/`body`/`refs[*]`/
  `task_id` → `""`; `refs` → `"DEFAULT []"`; **every row STAYS** (R10 — a deleted row leaves the stored
  ASSERT in place forever); delete `_MESSAGE_GRADE_ALLOWED` (dead: 2 hits at HEAD, both retired here);
  rewrite the two spec comments and the `_message_statements` docstring (D-M9) citing §12.4 and this
  doc's path. (Builder wave; listed so the DDL-text pins are written against the target.)
- **W10** `messages.py` — D-M10's two prose rewrites (`_reject_oversize_pointers` docstring; the
  closed-vocabularies comment). No behaviour change; a bare-pattern sweep (`backstop`, `both layers`,
  `store ASSERT`, `never UPDATEd`) over `loremaster/` + `loremaster/tests/` + `docs/design/` with a
  file:line + verdict per residual hit (the rename-sweep law — "all remaining hits are X" is banned).
- **W11** `test_comms_schema.py` — the DUAL: D-M3/D-M4 splits, D-M5 + D-M6 deletions-with-replacement
  (named in the commit message), the two KEPT controls, D-M11's rename + docstrings, P2-m (or the
  parametrized P2 ∪ P2-m).
- **W12** `test_comms_schema.py` — P1-m Leg A (§12.6), replacing `TestThePointerBoundsMigrateADIRTYStore`;
  the frozen `_ASSERTED_MESSAGE_DDL_AT_0566587` constant; `idempotent` kept.
- **W13** the migrate contract file — P1-m Leg B (§12.6) incl. the C-CONTROL; step 0's seeder lift into
  `_governed_contract.py` (lead grants the file if decisions-needed 3 is accepted).
- **W14** W4's P3 → the per-table allowlist (§12.7), reusing `governed_table_raw_mutation_sites`.
- **W15** `test_message_ledger.py` — add `_ParityScenario("task_id_len", "MessagePointerError", …)`
  (the fake oracle is unpinned for `task_id` at HEAD; per-field, not per-class).
- **W16** close-out receipt (lead): the §12.8 read-only count + `INFO FOR TABLE message` on `:18500`,
  recorded in the INDEX Log line beside §4.2's `to` receipts.
- **W17** store-ref §1.4 dated cross-reference line (D-M13 — lead, outside my set).

---

## 12.11 Discipline receipts

- Every number above is derived this session at `0566587`: the writer inventory and the ASSERT/prose
  inventories are `awk` over explicit `find` lists (text-search binaries hook-blocked — said so; dogfood
  protocol case (b), non-symbol textual seams); the history is `git log -S` per clause; the symbol reads
  are lore (`lore_get_symbol` for `_migrate_message_owner` / `MessageLedger.send`, `lore_impact` for
  `_reject_oversize_pointers` and the migrate seam, `lore_search` → `sed` spans for the rest).
- One belief is labelled as one (§12.8: that `:18500`'s stored `message` definitions carry the five
  ASSERTs — dated, converted by the lead's `INFO FOR TABLE` read). One annotation-only claim is labelled
  (D-M8: the `Literal` decode — read, not executed).
- Lore friction: `lore_impact(_migrate_message_owner)` reported *"tests: none detected"* while
  `test_message_migrate_63b_ii_a.py::TestMigrateMessageOwner` drives it through `migrate_governed` (the
  dispatcher) — indirect coverage is not traced, as its own caveat says. Not filed as a finding: the
  render names the bound honestly ("indirect coverage is not traced"); noted here so the lead does not
  read "no covering tests" as a gap.
- No worktree used. No file outside the writable set touched. Idle-gate contract written for this path.
  Ledger: registered `sidecar-63b-iib-2` (session `63b-iib-20260911`), heartbeats at each milestone.

---

# §13 — ADDENDUM 2026-09-11 · D-M8 RULED: KEEP the `grade` closed-set ASSERT (sidecar-63b-ii-b-2)

brief-base v14 read · brief project v7 read · **Graded:** `0566587` · HEAD-at-report: `0566587` · SAME.

**Why this addendum exists:** §12.5 D-M8 was filed *spec-silent → operator*. The operator declined to
rule it and directed, verbatim: *"The sidecar rules on forks. I am not the consumer. Agents are."* So
D-M8 is ruled HERE, as binding 63b design authority, on the AGENT-CONSUMER frame the operator named.
Scope: **ONLY the `grade` ASSERT.** The four LENGTH ASSERTs (`body`, `thread`, `refs`/`refs[*]`,
`task_id`) DROP exactly as §12 rules; nothing else in §12 is re-opened.

## 13.0 The ruling in one line

> **R19 — KEEP `grade`'s store ASSERT (`ASSERT $value IN ['signal', 'directive']`). Final tally for
> `message`: 4 DROP / 1 KEEP / 0 MOVE.** §12 R12 is SUPERSEDED. Both readings were weighed (§13.1);
> the deciding fact is a property, not a lean: **`grade`'s violation set is EXACTLY the reader's own
> rejection set**, so the ASSERT fails in the SAME direction as the reader — it is a positive control
> at the write, not a loaded gun at the UPDATE. The four length caps have the OPPOSITE property.

## 13.1 Both readings, weighed on the consumer frame

**What the two ASSERT classes actually guard, derived at `0566587` (not asserted):**

| | a LENGTH ASSERT (`body` etc.) | the `grade` ASSERT |
|---|---|---|
| a row that violates it — can the reader SERVE it? | **YES** — `InboxEntry.body: str`, `thread: str`, `refs: list[str]` decode any length; the row renders (fat, but served) | **NO** — `InboxEntry.grade: MessageGrade` is `Literal["signal", "directive"]`, pydantic-validated by the constructor in `_row_to_inbox_entry` (`InboxEntry(...)`, read at `messages.py`); a junk value RAISES |
| so a legacy violator under the §4.C migrate is… | a row the reader would have served, DENIED by a duplicated storage bound → the ASSERT is pure hazard (§12.2) | a row the reader could NEVER serve → the migrate refusal is an EARLY, LOUD, OPERATOR-VISIBLE form of a failure the consumer would otherwise meet per-agent at drain |
| policy VALUE source | one constant each (`MESSAGE_*_MAX_*`) | one tuple (`_MESSAGE_GRADES` → `MESSAGE_GRADES` frozenset, → the ASSERT literal, ≡ the `Literal` by pin `test_grade_is_a_closed_two_value_domain`) |
| what a ledger-bypassing writer can do without the ASSERT | land a fat row — served, bounded by the render side | land a junk-grade row — **that recipient's drain RAISES on decode: total inbox denial from one row**, the DD-3.c consumer outcome this wave exists to close on `to` |

**Reading (a) — DROP (§12's lean), stated fairly:** pure ONE IMPLEMENTATION; the junk-grade door is
reachable only through a writer P3 + F5 catch (honest) or #138 excludes (hostile); a lenient decode would
be worse. All true. **Where it fails the consumer frame:** P3's reach is a static floor with #138 doors
and F5's reach is *the battery's executed frames* — both are DEVELOPER-side instruments with named bounds,
and the outcome they bound is a CONSUMER-side total denial that the agent cannot diagnose, ack past, or
recover from (it never saw the row). The CONSUMER LAW's asymmetry: one false clear / total denial is fatal
within the session and resets no reputation; there is no equilibrium in which "P3 usually catches it"
earns anything back. And ONE IMPLEMENTATION is the WEAKEST objection here of the five: the vocabulary has
one source and both layers are DERIVED from it (mutation-provable — §13.3 P-G2), so this is one policy
enforced at two layers, not two policies — the #102 seam ("a fix reaches one copy and not the other")
cannot open.

**Reading (b) — KEEP (the lead's counter), stated fairly:** `grade` is categorically a DOMAIN guard on a
reader-side decode invariant, not a duplicated length cap; dropping it uniquely re-opens a total-denial
door; keeping it costs only T2 (a deliberate grade-vocabulary change arming a cutover refusal on legacy
rows), and grades are far more stable than a length constant (two values since `df59f76`, never changed —
derived §12.1). **Where it must be honest about its own cost:** T2 is real, and under the wrong protocol
it is #107's shape (a green suite, a refused cutover). But **T2 already REQUIRES a data heal regardless
of the ASSERT** — retiring `directive` narrows the `Literal`, and every legacy `directive` row becomes
unreadable at drain for every agent holding one. The store ASSERT does not ADD a heal obligation to T2;
it converts a silent per-agent denial into a loud whole-table refusal at the operator's cutover verb,
BEFORE any agent meets it. That is the direction the trust doctrine wants failures to move.

**The askable form that decides it (THE LEVER — a question, not a lean):** *"Is every row this store
constraint would refuse a row the READER would refuse anyway?"* If **yes**, the constraint is aligned
with the consumer — keep it, and pin the alignment. If **no**, it can deny what the consumer could have
read — DD-3.c applies, drop it (§3, §12). `grade`: yes. The four length caps: no. `to.ack_note`: no
(`ack_note: str | None`). This question is what §3.4's and §12.4's ∀ invariants were MISSING, and it is
now the exemption rule for both (§13.3).

**Ruling on the consumer's terms:** the consumer is served better by a store that cannot hold a row its
reader cannot decode than by a slightly purer layering diagram. A LOUD drain-decode failure on a junk
grade is NOT an acceptable consumer outcome when a nearly-free, reader-aligned store guard prevents the
row from existing. **KEEP.**

## 13.2 Two facts the ruling records, so they are not rediscovered

- **Denial, not loss — at HEAD, and only at HEAD's ordering.** `MessageLedger.drain` builds `entries`
  (`_row_to_inbox_entry` → `InboxEntry(...)`) BEFORE the `seen_at` stamp UPDATE, so a decode failure
  raises with NOTHING stamped. ⚠ **The ii-b §4.B one-txn shape moves the SELECT + stamp into one
  transaction with the Python decode AFTER commit — under that ordering a decode failure is a
  STAMPED-AND-LOST delivery** (the rows are `seen_at` forever, the entries never reach the agent). With
  R19 a junk grade cannot exist, so `grade` is moot; but the ORDERING property is general (any future
  decode-failing column). → **F-1 for the fidelity read:** the contract pins that the ii-b drain either
  decodes before it stamps, or decodes per-row with a rejected row NOT stamped and rendered as a named
  fate. Not a re-open of §12; a rider on §4.B carried here so it is not dropped.
- **The vocabulary-change protocol (T2's rider, named so a grade change meets the mechanism
  deliberately):** on a populated store, change `grade`'s domain in THREE steps — (1) WIDEN: add the new
  value to `_MESSAGE_GRADES` (ASSERT + `Literal` + frozenset move together, §13.3 P-G2), deploy; (2)
  HEAL: `UPDATE message SET grade = '<new>' WHERE grade = '<old>'` (under the widened ASSERT every row
  re-validates clean; this is the ONE heal statement, run once, operator-side — never at boot); (3)
  NARROW: remove the old value, deploy. A single-step narrow is #107's shape: green suite, refused
  cutover, unreadable legacy rows. The pinned bound in §13.3 P-G3 carries this text in its failure message.

## 13.3 Which pins change (the rider — deltas to §12, itemised; everything not named stands)

| pin / item | §12 said | §13 rules |
|---|---|---|
| **R12 / §12.3 `grade` row** | DROP; delete `_MESSAGE_GRADE_ALLOWED` | **KEEP** the ASSERT; `_MESSAGE_GRADE_ALLOWED` STAYS (live consumer: the spec row). Tally 4 DROP / 1 KEEP. |
| **P2-m** (§12.4 ∀ no-ASSERT over `message`) | ∀ emitted fields: no ASSERT | ∀ emitted fields: no ASSERT **EXCEPT an explicit exemption set `{grade}`**, the exemption a CONSTANT in the pin with the §13.1 reason in a comment (*violation set ≡ reader rejection set*). RECOMMENDED shape for the parametrized P2 ∪ P2-m: `table → (birth set, reader-aligned exemptions)`; `to`'s exemption set is `∅`. Non-vacuity gains: the exempted field's statement MUST carry an ASSERT (an exemption over a field with no ASSERT is a stale exemption → RED). |
| **P-G2 (NEW, offline, `test_comms_schema.py`)** | — | **the alignment pin**: the set inside the emitted `grade` ASSERT (parsed from `generate_message_ddl()`'s statement text) `==` `MESSAGE_GRADES` `==` `set(get_args(MessageGrade))`. Mutation proof: append a grade to `_MESSAGE_GRADES` → the DDL and frozenset move, the `Literal` does not → RED (and `test_grade_is_a_closed_two_value_domain` RED — the existing pin already holds two of the three legs; extend it or add the DDL leg beside it, ONE pin not two). This is "prove sharing by mutation" for the one-source claim §13.1 rests on. |
| **P1-m Leg A** (§12.6, drop lands) | six shapes ACCEPTED after `generate_message_ddl()` | **five** shapes ACCEPTED; the `grade='urgent'` shape is INVERTED: STILL REJECTED after the current emitter (RED if a build drops it — the wrong build for R19). BASELINE unchanged (all six refused under the frozen DDL). |
| **P1-m Leg B** (§12.6, migrate survives) | seven rows (six violators + clean), all stamped | **six** rows (five length violators + clean), all stamped; the junk-grade row moves to **P-G3**. |
| **P-G3 (NEW, live, beside Leg B — a PINNED KNOWN BOUND)** | (was the C-control's shape) | under the unbounded old DDL write ONE junk-grade legacy row + one clean; apply `generate_message_ddl()`; drive the REAL `migrate_governed(table="message")` → assert it RAISES (`SurrealStoreError`, engine text naming `grade`) and the read-back shows BOTH rows still NONE-owner (zero stamped — the whole-statement mechanism). Failure message: *"KNOWN BOUND (63b-ii-b §13): a legacy out-of-domain `grade` row refuses the message cutover — by design, because the reader could not serve that row either. Heal it FIRST with the §13.2 three-step protocol. If you closed this deliberately, delete this pin and say so."* The §12.6 C-control (frozen asserted DDL → migrate raises on a LENGTH violator) STANDS as the instrument-sees-the-hazard control; P-G3 is the grade twin, kept live. |
| **P3 floor** (§12.7) | docstring states D-M8's bound | the D-M8 bound statement is REMOVED (the reader-decode invariant is store-guarded); the floor's allowlists and non-vacuity are unchanged. |
| **D-M6** (§12.5) | `test_an_out_of_domain_grade_is_rejected_by_the_store` DELETED | **KEPT** — it now certifies R19 (docstring re-dated citing §13). `test_both_legal_grades_are_accepted` stays as its positive control. The four length rejections still DELETE-with-replacement. |
| **D-M9 / D-M10** (§12.5) | rewrite the `_message_statements` docstring's *"closed grade domain"* clause; rewrite the closed-vocabularies comment | the `_message_statements` docstring KEEPS *"the closed `grade` domain"* and loses only *"the length-bound `body` backstop"*; the `messages.py` closed-vocabularies comment (*"so the ledger's app-level check and the store's ASSERT can never spell the vocabulary differently"*) is **TRUE and STANDS** — no rewrite. `_reject_oversize_pointers`' backstop sentence still rewrites (D-M10, length-only). |
| **D-M8** | spec-silent → operator | **RULED** (this addendum). |
| **§12.8 close-out count** | six predicates | unchanged — the `grade NOTINSIDE [...]` predicate stays (expected 0; a hit is a row the reader could not serve, and must be healed before 65). |
| **W9** | five constraints → `""`; delete `_MESSAGE_GRADE_ALLOWED` | FOUR constraints → `""` (`thread`, `body`, `refs[*]`, `task_id`; `refs` → `"DEFAULT []"`); `grade` row and `_MESSAGE_GRADE_ALLOWED` untouched; the spec gains a one-line comment on the `grade` row citing §13.1's question. |
| **W11 / W12 / W13** | per §12 | per the rows above (P2-m exemption + non-vacuity; P-G2; Leg A grade inversion; Leg B six rows; P-G3). |
| **M (mutation proofs)** | Leg A / Leg B / P2-m | + P-G2 (append a grade to the tuple only) and R19's wrong build (drop the `grade` ASSERT → Leg A's grade shape RED, P-G3 RED, P2-m's exemption non-vacuity RED; the four length shapes GREEN). Declared from `--collect-only`, diffed both ways. |

**Reach, stated (INSTRUMENT 0):** the exemption set is a hand constant — `{grade}` — and that is
deliberate: an exemption is a JUDGEMENT ("reader-aligned"), so it must be written down by a person, and
the pin's non-vacuity (an exempted field must carry an ASSERT) plus P-G2 (the ASSERT must equal the
reader's set) are what keep the hand constant honest. A future field that is reader-aligned is added to
the set WITH its P-G2-shaped alignment pin, or it is not exempt.

## 13.4 Discipline receipts
- Derived this session at `0566587`: `drain`'s decode-before-stamp ordering (`lore_get_symbol`), the
  `InboxEntry(...)` constructor seam (`awk`, said so), the `Literal ≡ constants` pin
  (`test_grade_is_a_closed_two_value_domain`, read), the grade history (§12.1's `git -S`).
- Packages considered: none — no mechanism specified. Reuse ledger: none (P-G2 EXTENDS an existing pin;
  P-G3 is a test, the contract author's row). No file outside the writable set touched; §0–§12 untouched.
- Escalations: none owed to the operator (the operator delegated this fork here). One rider raised for the
  fidelity read (F-1, §13.2 — the §4.B decode/stamp ordering), not re-opening any accepted item.

---

# §14 — ADDENDUM 2026-09-11 · FIDELITY READ: ruling (§0–§13) vs the frozen RED contract `4aaf45f` (sidecar-63b-ii-b-2)

brief-base v14 read · brief project v7 read.
**Graded:** `4aaf45f` · HEAD-at-report: `8000385` · DIFFERENT (1 behind) — `8000385` touches ONLY
`scripts/probe_drain_read_63b_ii_b.py` (ruff style; `git show --stat`), nothing this read rests on.
Read: every file in `4aaf45f`'s stat (7 test files + `REPORT-contract-63b-ii-b.md`), the production
seams the pins drive (`_txn.py::run_query` raise site, `governed.py::write_guard`, the F5 classifier in
`_governed_contract.py`, the `to`-tree allowlist in `test_message_enforcement_63b_ii_a.py`), and one
`--collect-only` (2 ids, 251 deselected). No test was RUN by me — the RED/GREEN receipts are the
contract author's (report §"RED-at-HEAD run receipts"), cited not re-derived; this read grades
RULING-vs-CONTRACT (did each ruled pin land AS RULED), which is the instrument the adversary's
contract-frame cannot supply.

## 14.0 Verdict

**GO WITH THREE FIDELITY GAPS + ONE MECHANISM RULING**, none a re-open of an accepted item:
- **MP-7 (new, the DUAL missed it): a CORPSE CERTIFIER survives** — `test_comms_schema.py::
  TestMessageDdlOffline::test_body_carries_a_length_bound_the_store_itself_enforces` (collected at
  HEAD) asserts `"ASSERT" in statement` for `message.body` and pins the `<= 4000` bound. It certifies
  the OLD world and is a **C-DEF**: it CANNOT pass the correct build (W9 drops `body`'s ASSERT) — the
  builder is trapped between P2-m (demands no ASSERT) and this pin (demands one). Its docstring is the
  P8d-class stale prose verbatim (*"the schema ASSERT is the backstop that makes a bypassing writer fail
  LOUDLY"*). The DUAL ledger deleted the LIVE body rejection and the pointer/ack_note OFFLINE pins but
  not this offline body pin — the same class as ii-a's MP-5/MP-6. **Fix: DELETE-with-replacement (P2-m
  is the inverse ∀; D-M2 the app cap), named in the commit message.**
- **G1 — P4 landed for ONE of five carriers.** §9.1/§8 P4: the bound line EXACTLY ONCE per served
  READ response, *"render pins per verb"* — drain, await (non-empty AND EMPTY — *"where Leg 1 matters
  most"*), story, ack. The contract has the once-count for `drain` only
  (`test_a_multi_entry_drain_carries_the_bound_line_exactly_once`). The structural coverage pin (P5)
  forces PRESENCE of `render_subject_bound` in each derived render's source; it cannot see a
  sub-render CLONE (`_render_story_message` per message; the await-empty path) — the exact wrong build
  §9.1's count exists for. **Fix: the once-count for `await` (≥2 rows), `await`-EMPTY (timeout),
  `story` (≥2 messages — the per-message sub-render is the clone risk), `ack` (≥2 seqs).** The drain
  pin's shape is right; parametrize or sibling it.
- **G2 — P6 landed for its TOKENLESS half only.** §9.4 ruled BOTH: tokenless = the one identity line
  (LANDED, `test_the_tokenless_rollup_message_leg_names_the_identity_bound`, incl. the no-count leak
  check) AND *with a verified capability: `total` is the FILTERED count and the bound line HEADS the
  LEG (leg-scoped, not response-scoped — the task/finding legs are ungoverned until 64)*. The second
  half is unpinned: a build that puts the scope line at the RESPONSE head (over-claiming about the
  task/finding legs) or serves an UNFILTERED count passes. **Fix: one capability-bearing rollup pin —
  bound line immediately above `messages activity (k):`, NOT the first line of the response, and `k`
  equals the Subject-visible count with a foreign-principal message present (the Leg-1 diff).**
- **Dev-4 — the `write_guard` READ/WRITE exclusion is REJECTED as a mechanism (§14.2); ruled
  replacement: an explicit, non-vacuous WRITE-receipt exemption set, corroborated from truth.** A
  contract adaptation of a §9.3 gap, ruled here (the ruling was silent; the fill is mine to make) —
  NOT a ruling change for the operator.
- **Dev-3 — BLESSED with one tightening (§14.1).** Construction-isolation + the positive control
  discriminates R19's wrong build exactly as the field-name assertion would have; a bare
  `pytest.raises(Exception)` is loosened one notch too far, and the tightening is ACHIEVABLE.

Everything else ruled in §0–§13 LANDED AS RULED (§14.3 table). The two deferrals (read-verb corpse,
F-DUP convergence of `wire_world` + the 3 ii-a `cred` fixtures) are lead rulings (§11.3), not gaps.

## 14.1 Dev-3 adjudicated — P-G3 without the engine's field name

**The author's claim is TRUE, verified at the raise site:** `store/_txn.py::run_query` raises
`_domain_rejection_error(error_class, f"SurrealDB {noun} rejected against {url!r} ({error_class});
{_SERVER_LOG_HINT}")` — the engine's `"grade … must conform to"` text is LOGGED under the seam's label
and NEVER interpolated into the raised message (ledger #31, by design). §13.3's *"engine text naming
`grade`"* was written against the engine's surface, not the driver's wrapped one; the ruling's
expectation was wrong about the instrument, and the author was right to say so rather than assert a
string that cannot appear.

**Does construction-isolation still discriminate?** Yes — the wrong build for R19 is *"drops the grade
ASSERT"*; under it the junk-grade fixture MIGRATES (no raise) → `pytest.raises` fails → RED; the
sibling `test_CONTROL_a_legal_grade_fixture_migrates_cleanly` (same two rows, `directive` instead of
`urgent`, `backfilled == 2`) stays GREEN, so the pair isolates the grade as the ONLY refusing
difference. That is "a probe needs a control" done correctly, and it is not weaker than the field-name
assertion for the R19 wrong build. Zero-rows-stamped is already asserted (both rows read back
NONE-owner). `test_the_grade_assert_STAYS_after_migrating_a_dirty_store` (Leg A) and P2-m's exemption
non-vacuity red on the same wrong build — three independent instruments.

**Where it IS one notch weaker, and the achievable tightening (REQUIRED):** `pytest.raises(Exception)`
admits a raise for the WRONG reason — a transport fault (`SurrealConnectionError`), a governed
conflict (`TxnGovernedConflictError`), a fixture `TypeError`. The control halves that door (the same
fixture with a legal grade succeeds), but the class label IS in the wrapped message, so pin it:
`pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)")` — the driver's own
`_ERROR_CLASS_ASSERT_VIOLATION` label, the typed domain-rejection class (`_domain_rejection_error`
returns exactly it for a non-governed-conflict rejection). Same tightening for Leg B's C-CONTROL
(`test_C_CONTROL_the_frozen_asserted_ddl_makes_the_migrate_RAISE`), which drives the SAME seam. The
raw-connection seeds (Leg A BASELINE / grade-STAYS, `seed_message_legacy` over `run`) see the SDK's
own error, not the driver's — the house `# noqa: B017` idiom stands there; a `match="must conform"`
would be nicer but is not required.

**Mutation-proof declaration:** the report's declared RED sets stand; add the match-string to the
expected-RED reasoning (a build that raises for another reason now reds by TYPE, not by luck).

## 14.2 Dev-4 RULED — the `write_guard` exclusion re-introduces the hidden-constant class; replaced

**What the author built:** the widened derivation (`self`/`cls`/`AppContext` receivers — #464, LANDED
as ruled, with the six-render non-vacuity floor) EXCLUDES any Subject-resolving handler whose source
calls `write_guard`, on the premise *"a governed read never does — there is no `read_guard`"*.

**Why the premise is FALSE for two of the six ruled carriers, derived from truth:**
- F5's classifier (`_governed_contract.py`, the `observed.label not in entry.frames` leg) classifies a
  NON-exempt governed-table mutation iff `governed.active_write_guard()` at mutation time equals one of
  the allowlist entry's `frames`. The `to`-tree allowlist (`test_message_enforcement_63b_ii_a.py`)
  registers `_DRAIN_TO_ENTRY` with `frames=("drain",)` and `_ACK_TO_ENTRY` with `frames=("ack",)`, and
  both entries say *"ii-b drives the LIVE classification"*.
- Therefore the ii-b `drain` and `ack` — READ verbs that STAMP `to` — MUST execute their stamp inside
  `write_guard("drain")` / `write_guard("ack")` to classify at all (an unlabelled mutation is
  UNCLASSIFIED → deny-by-default). WHERE the builder enters it is the builder's choice; the ONE
  precedent in the tree (`_comms_send`: `with governed.write_guard("send"): … self.message_ledger.
  send(...)`) puts it in the HANDLER. A builder mirroring the precedent writes `with governed.
  write_guard("drain"): result = await self.message_ledger.drain(...)` in `_comms_drain` — and the
  exclusion silently removes `_comms_drain`'s (and `_comms_ack`'s) renders from the derived set.
- The premise is TRUE at HEAD only because ii-b's reads are UNBUILT (no read stamps under a label
  yet) — the fixture guarantees the one condition under which the defect is invisible (CLAUDE.md, THE
  TEST ENVIRONMENT IS A FICTION). GREEN at HEAD proves nothing about it.
- The floor (`ii_b_floor - all_renders == ∅`) WOULD red for those two — the six named renders are
  protected — but with a failure message naming two causes that are both wrong (*"handlers do not
  resolve a Subject yet … or the receiver reach fails"*), and the builder's path of least resistance
  is to move `write_guard` OUT of the handler to satisfy a test — an undocumented production constraint
  invented by a test mechanism. And a SEVENTH read-that-stamps (a future `mark-read`, a `story` that
  records a view) is outside the floor and silently excluded: the reach receded one level (the STOP
  rule's tell).

**The class:** this is the instrument lesson's row *"keyed on X, defeated by a site that spells it
differently"* — the hidden constant is the belief *reads never enter `write_guard`*, and it is a
DENY-rule over reads keyed on an idiom reads legitimately use. β (hand-exclude `_render_comms_send` by
name) was rejected as "the #464 hand-list" — but that conflates two things. #464's defect was a hidden
REACH constant (receiver names) that silently EXCLUDED sites. A visible, non-vacuous EXEMPTION is the
opposite instrument: it ALLOWLISTS THE SAFE (the write receipts permitted to omit the bound — small,
enumerable), and everything else that resolves a Subject is demanded to carry the bound
(deny-by-default on omission). §13.3 established exactly this shape for P2-m's `{grade}`: *"an
exemption is a JUDGEMENT, so it must be written down by a person, kept honest by non-vacuity."*

**RULING (binding; a contract adaptation, not a ruling change):**
1. **Remove the `write_guard` exclusion from `_governed_read_render_methods`.** The derived set is EVERY
   Subject-resolving handler's top-level `_render_*` calls (receivers `self`/`cls`/`AppContext` as
   built).
2. **Add an explicit exemption constant** — the WRITE-RECEIPT renders permitted to omit the bound — in
   the coverage pin, beside the floor: at `4aaf45f` exactly `{"_render_comms_send"}` (derived this
   read: `_comms_send` is the ONLY Subject-resolving handler in `server.py` whose renders are receipts;
   `remember` resolves a Subject but calls no `_render_*`; `recall` is a carrier). Comment: *"a governed
   WRITE renders a receipt, never a scoped result — §9.1: send is not a carrier."*
3. **Non-vacuity, both directions:** (a) every exempted render MUST be in the derived set (its handler
   DOES resolve a Subject) — else the exemption is stale → RED; (b) **from-truth corroboration on the
   SAFE side only**: the exempted render's handler source MUST contain a WRITE-family seam
   (`write_guard(` AND/OR `resolve_write_scope(`/`guarded_write(`) — a read someone "exempted" to skip
   the bound has none → RED. This uses the author's signal in the direction where it cannot hide a
   read: as a positive requirement on an exemption, never as an exclusion of the population.
4. **The coverage pin then demands `subject` + `render_subject_bound` of every derived render NOT in
   the exemption set** — so the day a builder wraps `drain`'s stamp in `write_guard("drain")` in the
   handler, `_render_comms_drain` is still demanded to carry the bound (correct), and the day a NEW
   governed write verb lands (63c `brief_publish`), its receipt render is DEMANDED to carry a bound
   until its author adds the exemption consciously — surfaced, not narrowed (R6's own property).
5. **Mutation proof (declared):** delete `_render_comms_send` from the exemption → the coverage pin
   reds on it (it carries no bound); add a fake exemption `"_render_comms_drain"` → leg (b) reds (no
   write seam in `_comms_drain`) once built, leg (a) at HEAD; restore → GREEN.
6. The floor's failure message names the THREE causes: handler resolves no Subject · receiver reach
   regressed · render wrongly exempted.

**For the adversary (report §"Spec-interface", the flagged constraint):** *"the reference build's read
handlers must NOT call `write_guard` (else excluded from coverage)"* is WITHDRAWN by this ruling — the
reference build MAY attribute drain/ack at the handler exactly as send does; F5's `frames` REQUIRE the
label somewhere on the path.

## 14.3 Per-pin fidelity table (ruled → landed)

| ruled pin | where landed | verdict |
|---|---|---|
| R1/W1 + P2 [`to`] ∀ (§3.4) | `TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate[to]` — birth set, no DEFAULT, post-birth `option<`, floor `{ack_note}`, failure text carries the heal/pin obligation | **LANDED** (the message conflates `to`/`message` wording into one — acceptable; the re-open trigger (drain stops being whole-window) is in the docstring, not the failure text — nit) |
| P2-m + `{grade}` exemption + non-vacuity (§12.4/§13.3) | same pin, `[message]`: birth set = df59f76 + `refs[*]`; `birth_defaults={refs,question}`; `exemptions={grade}` with BOTH legs (exempt field present in the emitted set AND carries an ASSERT); floor `{body, refs[*], owner_principal}` | **LANDED AS RULED** — ONE parametrized pin over a `table → (birth, defaults, exemptions, floor)` spec (§13.3's recommended shape). Confirmed: the non-vacuity leg is present. |
| P-G2 alignment (§13.3) | `TestMessageDdlOffline::test_grade_is_a_closed_two_value_domain` (test_comms_schema) — parses the emitted IN-set, asserts non-empty, `== MESSAGE_GRADES == get_args(MessageGrade)`; plus the ledger file's original two-leg pin stands | **LANDED** — but note it is a SECOND pin with the SAME NAME as `test_message_ledger.py::…::test_grade_is_a_closed_two_value_domain` (two files, one name). Not a defect (different modules), a grep hazard for the sweep law — nit: suffix one. |
| P1-m-A Leg A (§12.6 / §13.3) | `TestTheMessageAssertsAreDroppedFromADIRTYStore`: frozen 0566587 world (shared `frozen_asserted_message_ddl`) → BASELINE refuses all six → clean-row control → current emitter → five length shapes ACCEPTED byte-intact → grade STAYS refused → idempotent; plus a frozen-world-matches-emitter control | **LANDED AS RULED** (the extra control that the frozen capture cannot rot is a good addition) |
| P1-m-B Leg B (§12.6 / §13.3) | `TestTheRealMigrateSurvivesLegacyViolators`: unbounded world + governed overlay + migrated sender + operator; six rows (5 length + clean) via the shared seeder; REAL `principals.migrate_governed(table="message")` through `store_handle`; not refused, `backfilled == 6`, owner/scope stamped, values byte-intact; idempotent; C-CONTROL (frozen DDL → RAISES, zero stamped) | **LANDED AS RULED** — `scanned == 6` / `already_migrated == 0` not asserted on the first call (nit); tighten the C-CONTROL's `raises` per §14.1. |
| P-G3 (§13.3) | `TestAJunkGradeLegacyRowRefusesTheCutover` + legal-grade control | **LANDED with Dev-3** (§14.1: bless + tighten) |
| P1 dirty-`to` drain (§6) | `TestALegacyOverCapNoteCannotDenyADrain`: `generate_message_ddl()` → downgrade `ack_note` → REAL governed messages (server scope) + two edges under the unbounded note → re-apply emitter → REAL `MessageLedger.drain(subject=)`; asserts return, `stamped_seqs == [0,1]`, both served, both `seen_at` set, over-cap note byte-intact; BASELINE; C-control (pre-seen edge outside the window, dirty edge served ALONE) | **LANDED AS RULED** — the one-txn leg is one leg (drain IS the §4.B path), stated. |
| P3 per-table floor (§12.7) | `TestTheSingleWriterFloorPerTable`: reach = `derive_member_source_roots()` (derived, not a file list); CREATE/UPDATE rows REUSE `governed_table_raw_mutation_sites` (with the `table_const_hint` trap named — a measured false positive); the `ack_note` column row is an AST scan over SET/CONTENT literals; exact allowlists; D-M8 statement removed | **LANDED AS RULED** |
| P5 #464 widening + floor (§9.3) | receivers `{self, cls, AppContext.__name__}` (derived, not spelled) + `test_the_derivation_reaches_the_ii_b_comms_renders` (⊇ the six) | **LANDED** — the exclusion mechanism is §14.2's ruling |
| R6 driver table (W8 / ii-a §11.5) | `test_every_capability_required_verb_denies_without_one`: True-set DERIVED from `_COMMS_ACTIONS`; `drivers` keyed by verb; **coverage assertion `required - drivers.keys() == ∅`** + non-empty guard; every True verb driven → `GovernedDenied`; plus reads-require + exact-five FIX pins | **LANDED AS RULED** — a real coverage assertion, not a hand-list (the hand map's COVERAGE is the checked variable). Nit: `_REQUIRED_IN_II_B_NOT_YET` is now a stale NAME (they are required in ii-b). |
| P4 once-per-response (§9.1) | drain only | **PARTIAL → G1** |
| P6 rollup (§9.4) | tokenless half | **PARTIAL → G2** |
| P7 invisible-seq ack (§9.5) | `TestAnAckOfAnInvisibleSeqIsUnknownMessage`: fate `unknown_message`, `acked_count == 0`, invisible edge `acked_at` NONE, ∀-request one fate; CONTROL visible seq → `acked` + stamped | **LANDED AS RULED** |
| F-1 decode-before-stamp (§13.2) | `TestTheDrainDecodesBeforeItStamps`: monkeypatched `_row_to_inbox_entry` (instance-method signature matches) raises; edges must stay `seen_at IS NONE`; both ruled shapes admitted (decode-first, or per-row with rejected rows unstamped) | **LANDED AS RULED** (behavioural, the right pick) |
| D3/W3, D-M3, D-M4, D-M5, D-M6 (4 live length rejections deleted; grade live pin KEPT + re-dated; the two positive controls KEPT), D-M7 inversion, D-M11 rename + docstring | test_comms_schema | **LANDED** — except the offline `body` pin (**MP-7**, above) |
| W15 `task_id_len` parity | `_task_id_len_trigger` + scenario row | **LANDED** |
| F-DUP lift (§12.6 step 0) | `_governed_contract.py::{seed_message_legacy, frozen_asserted_message_ddl, unbounded_message_ddl, credentialed_app_context, register_owned}`; both dirty legs + P1 + read-governance call the ONE seeder | **LANDED** — `test_comms_schema._create_message` remains as a second raw-CREATE seeder in the same tree (used by the KEPT live pins); the report names it as predating; converge at build (a DRY row, not a gap). |
| D-M9 / D-M10 prose, W9 spec edits, §12.8 close-out reads | build wave / lead | n/a here |

## 14.4 Classification for routing

- **Ruling changes needing the operator: NONE.** §14.1 and §14.2 are fills of gaps the ruling left
  (a wrong assumption about the driver's surface; a silent spec point), both within the 63b design
  delegation.
- **Contract revisions owed before the builder (the adversary's re-grade covers them):** MP-7
  delete-with-replacement · G1 four once-counts · G2 the capability-bearing rollup pin · §14.1's
  `raises` tightening (P-G3 + C-CONTROL) · §14.2's exemption-set replacement (items 1–6).
- **Nits (build-wave hygiene, no gate):** the duplicate test name across two files; `already_migrated
  == 0` on Leg B's first call; `_REQUIRED_IN_II_B_NOT_YET` rename; the second raw seeder.

## 14.5 Discipline receipts
- Fallbacks to textual search, said: the offline-ASSERT-pin hunt (`awk '/assert "ASSERT" in/'` over
  `test_comms_schema.py` — how MP-7 was found: the DUAL ledger was a hand-list, the sweep is not), the
  `write_guard`/`governed_exempt` call-site sweep over production (`find` + `awk`), the Subject-resolving
  handler enumeration in `server.py` (an `awk` state machine over `async def` bodies). Symbol-level
  reads via `lore_get_symbol` earlier in this session (`drain`, `send`, `_migrate_message_owner`).
- Packages considered: none — no mechanism specified. Reuse ledger: none (0 new symbols; §14.2 names
  a constant the contract author owns).
- No file outside the writable set touched; §0–§13 unchanged (md5 before/after the append). Not
  committed — the lead commits.
