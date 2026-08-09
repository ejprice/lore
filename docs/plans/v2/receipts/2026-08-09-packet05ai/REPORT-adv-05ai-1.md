# REPORT-adv-05ai-1 — contract-adversary, packet 05a-i (comms CONSUME PATH)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 result — the contract does NOT pass its own satisfiability receipt.** A *known-correct*
  reference build (implementing the designed semantics verbatim) is **5 failed / 1265 passed /
  17 skipped** across the four contract files. The failures are not my build's bugs (each was
  chased to ground and the non-defect ones fixed); they are two BLOCKER contract defects.
- **Packages considered:** none — the contract pins tests over already-shipped store idioms
  (`sequence::nextval`, `count()…GROUP ALL`, `UPDATE…RETURN AFTER`); no new library mechanism is
  specified, so there was nothing to survey.
- **Graded:** `d9b151b` + the UNCOMMITTED contract (working tree: `test_message_ledger.py`,
  `_message_fakes.py`, `test_comms_promise_registry.py` modified; `test_comms_waiting_line.py`
  untracked) · HEAD-at-report `d9b151b` · SAME. Reference build in scratch:
  `loremaster.__file__ = /tmp/adv-05ai-scratch/loremaster/loremaster/__init__.py`. Store 3.2.4,
  spike-surreal `:18000`.

### MISSING PINS (each = the test that should exist + the defect it catches)

- **F1 (BLOCKER, LEG B):** the `since=0` recovery fixtures are RED on `[real]` for the
  designed-correct **uniformly-strict** build, because production `message.seq` is **0-based**
  (`sequence::nextval` `START 0` — verified `real_first_seq=0`) while the fixtures hardcode
  `since=0` as a "before-the-first" sentinel that only holds in the fake's **1-based** world.
  *Missing pin/fix:* (a) fix the fake to mint 0-based (F2); (b) the fixtures must derive the
  "recover-all" cursor as `seqs[0]-1`, not `0`; (c) add a pin that a caller who genuinely
  processed seq 0 and passes `since=0` is **not** re-served seq 0 — the pin that catches the
  muddy `since==0 ⇒ >=` special-case that is the ONLY way to pass the fixtures as written.
- **F2 (BLOCKER root cause, oracle #190-gap):** the fake mints `seq` starting at **1**
  (`next_seq += 1` before assign) while production starts at **0**. No parity pin catches this
  seq-origin divergence — it is what hid F1 from the fake leg. *Missing pin:* a real-vs-fake
  parity assertion that a fresh ledger's first send has the **same** seq on both backends (or fix
  the fake to be 0-based).
- **F3 (BLOCKER, LEG C render):** the per-row `question` marker has **no classification home** in
  the promise registry, so no build satisfies BOTH `TestTheDrainRowVisiblyMarksAQuestion` AND the
  promise/​safe_str classification suites without editing a contract test. *Missing pin/fix:*
  register the marker literal in `_PROMISE_FREE`/`_SAFE_STR_PROMISE_FREE` (exactly as LEG D's
  waiting line was registered) — which means the glyph **cannot** be "builder latitude": the
  contract must pin a specific marker and classify it.
- **F4 (MEDIUM, LEG D):** the "ONE shared helper" claim is **not mutation-proven** — a
  byte-identical private clone of `_render_comms_waiting_line` in the heartbeat path passes the
  entire LEG D suite (incl. the identical-line pin). *Missing pin:* a mutation/structural pin that
  BOTH `_comms_drain` and `_comms_heartbeat` route through the single helper (change the template →
  both verbs' output moves), not just that their outputs happen to be equal.

### FIXTURE-DISCRIMINATION VERDICTS (which fixtures cannot tell right from wrong)

- `since=0` fixtures (LEG B): **CANNOT DISCRIMINATE** on the fake (1-based makes `since=0` benign);
  they encode the oracle's divergence, not the contract. Root of F1/F2.
- LEG C `question` discriminate fixture (one question + one non-question in ONE drain):
  **DISCRIMINATES** — reddens both `question=True` and `question=False` hardcodes (WB-C).
- LEG D status-conflation pair (active+question vs input_required+no-question):
  **DISCRIMINATES** both ways (WB-D).
- `_PAGING_INBOX=12 >> _DRAIN_CAP=5` (#183): **DISCRIMINATES** — reddens a read-all-then-slice
  build (WB-B183).
- LEG D identical-line pin: **CANNOT DISCRIMINATE** a byte-identical clone (F4).

### QUANTIFIER TABLE (P1b) — see §P1b below (every invariant ∀-vs-guarded, with receipts).

### Reproduced RED / mutation / corpse verdicts

- LEG A ∀-coverage pin: **CONFIRMED discriminating** — a throwaway `MessageLedgerError` subclass
  reddens `test_the_parity_battery_covers_every_message_ledger_error` (WB-A2).
- `stamped_seqs` TOCTOU truth: **CONFIRMED deterministic** — correct build 20/20 green; the
  attempted-window build reddens (WB-B-stamp).
- Corpse sweep: no surviving old-behavior corpse found (the LEG C/D surfaces are additive; the
  `stamped_seqs`/drain reshape is guarded by the pre-existing packet-03 oldest-window pins, which
  I confirmed still red a wrong reshape).
- Two BUILDER LANDMINES the contract CORRECTLY guards (not defects — flagged so the builder is not
  trapped): **L1** `ORDER BY <linked-field>` (`in.seq`) is silently ignored on the edge — the #183
  bounded read must `ORDER BY` the **projected alias** `seq` (caught by the pre-existing over-cap
  oldest-window pins). **L2** the LEG D `awaiting_answer` read must PRECEDE the drain stamp (caught
  by `TestNoAwaitedWorkHappensAfterTheDrainStamps`, DD-4.b).

---

## The reference build (the instrument for every receipt below)

Built in `./scripts/scratch_copy.sh /tmp/adv-05ai-scratch` (provenance asserted in-scratch, printed
above). Production edits implementing the *designed* semantics:

- `messages.py`: `InboxEntry.question: bool = False`; `_row_to_inbox_entry` adds
  `question=bool(row.get("question"))`; `drain(…, since=None)` reshaped to a `since=` recovery
  branch (`in.seq > $since` STRICT, seen-or-unseen, oldest-first, bounded, non-stamping), a #183
  bounded plain window (`ORDER BY seq LIMIT $limit` + separate `count()…GROUP ALL`), and
  `stamped_seqs` read back from `UPDATE … RETURN AFTER` (DD-4 Q5 truth).
- `server.py`: `_render_comms_waiting_line(waiting, *, age_s) -> list[Rendered]`; a shared
  `_comms_waiting_lines` read helper wired into `_comms_drain` and `_comms_heartbeat` (read BEFORE
  the drain stamp, per L2).
- `_message_fakes.py`: `_inbox_entry` adds `question=message.question` (the LEG-C one-liner the
  contract's own docstring anticipates).

Result on that reference (marker absent — see F3 for why the marker cannot be added cleanly):

| file | result |
|---|---|
| `test_message_ledger.py` | 236 passed / **2 failed** (F1) / 17 skipped |
| `test_comms_tool.py` | **902 passed / 0 failed** |
| `test_comms_waiting_line.py` | 7 passed / **3 failed** (F3, LEG C render with no marker) |
| `test_comms_promise_registry.py` | all passed (marker absent ⇒ nothing unclassified) |
| **combined** | **1265 passed / 5 failed / 17 skipped** |

A satisfiability receipt REQUIRES 0-failed on a known-correct build. This build is correct (it
implements the documented semantics; the 902/0 surface pass and the 236 ledger pass, incl. LEG A
parity, LEG C ledger, #183, TOCTOU truth, all prove it) — and it is **not** 0-failed. That is the
INSUFFICIENT verdict.

---

## F1 — the `since=0` recovery C-DEF (LEG B). The headline.

**Empirical seq-origin proof** (probe, in-scratch, provenance-verified):
`ADV-PROBE real_first_seq=0 fake_first_seq=1`. Confirmed independently by the store schema
(`surreal_schema.py::_message_sequence_statement` docstring: default `BATCH 1000 START 0` "is what
`message.seq` wants") and by the TOCTOU run showing `real seqs [0, 1, 2]`.

**The reference (uniform strict `>`) fails on `[real]`:**
```
FAILED test_message_ledger.py::TestSinceServesAlreadySeenRows::test_since_re_reads_rows_a_plain_drain_already_stamped[real]
  assert [1, 2] == [0, 1, 2]     # since=0, strict > 0, production seq starts at 0 -> seq 0 lost
FAILED test_message_ledger.py::TestSinceServesAlreadySeenRows::test_since_does_not_re_stamp_and_does_not_consume_unseen[real]
  assert [1, 2] == [0, 1, 2]
```
The fake leg PASSES the identical fixtures (fake seqs `[1,2,3]`, so `since=0` is genuinely
before-the-first). The divergence is invisible to the fake.

**Why it is a defect and not my build's bug — the strict pin makes uniform-strict mandatory:**
`test_since_is_STRICTLY_greater_than_the_cursor` (`since=seqs[1]`, expects only `[seqs[2]]`) forces
`>`. Under `>`, `{seq : seq > 0}` on real `= {1,2} ≠ {0,1,2}`. The designed semantics literally
cannot serve the fixture.

**The only passing build is muddy (proven):** a `since==0 ⇒ >=` special-case (strict otherwise)
makes all four `[real]` `since=` tests pass (`4 passed`). But it ships a latent bug — a caller who
processed seq 0 and passes `since=0` to fetch newer rows is **re-served seq 0** — which no pin
catches. So the contract either (a) reds the correct build, or (b) green-lights a muddy build; it
is a defect either way.

**The fix is in the fixtures + the fake, not the code.** Make the fake 0-based (F2); derive the
recover-all cursor as `seqs[0]-1`; add the seq-0-was-processed discrimination pin.

## F2 — the oracle's seq-origin divergence (root cause of F1, #190 class)

The fake's `send` does `self.db.next_seq += 1; seq = self.db.next_seq` → first seq **1**.
Production's `LET $minted_seq = sequence::nextval("message_seq")` → first seq **0**. The LEG-A
parity battery grades ERROR PROSE only; nothing grades the seq VALUE contract, so this divergence
rides free — the exact #190 shape ("the oracle diverges from production and no parity pin sees it").
It is load-bearing precisely because every `since=` behavioural pin rides the fake.

## F3 — the LEG C `question` render marker has no classification home (BLOCKER)

The dilemma, proven from all three routes on the reference:

| marker approach | `TestTheDrainRowVisiblyMarksAQuestion` | promise/​safe_str classification |
|---|---|---|
| **none** | 3 FAILED (rows identical) | GREEN |
| **context-slot** `safe_str(f"…{ } (question)")` | `test_the_marker_is_ON` FAILED* | `test_every_comms_safe_str_literal_is_classified` FAILED (`' (task {}) (question)'` unclassified) |
| **new template** `"…→you{context} (question)"` | 3 PASSED | `test_every_comms_render_literal_is_classified` FAILED (`'#{seq} [{grade}] {sender}→you{context} (question)'` unclassified) |

\* `safe_str` **strips leading whitespace** (`safe_str(' (question)') -> '(question)'`) and the
header template glues `→you{context}`, so a context-slot marker can never be a standalone
whitespace-delimited token, which `test_the_marker_is_ON_the_question_row_not_the_non_question_row`
requires (plain-row tokens ⊆ question-row tokens).

So a *standalone-token* marker is mandatory (route 3), and every standalone-token literal is
UNCLASSIFIED with no entry the builder may add (the registry is a contract test). The author
registered LEG D's new `waiting:` literal in `_PROMISE_REGISTRY` + `_PROMISE_PROOFS` + the coverage
set, but **forgot LEG C's marker literal**. The "glyph is builder latitude" comment in the contract
is false: the promise registry requires the exact literal, so latitude is impossible.

## F4 — "ONE shared helper" is not mutation-proven (LEG D, MEDIUM)

Replacing the heartbeat path's call to the shared `_render_comms_waiting_line` with a
**byte-identical private clone** (`render_line(<same template>, …)` inline in `_comms_heartbeat`)
passes the whole LEG D suite — `7 passed` incl. `TestTheWaitingLineIsONESharedHelper` — and the
promise coverage/proofs — `32 passed`. Routing is not sharing; the identical-line pin compares
OUTPUT bytes, which two identical clones share. The repo's own DRY law ("prove sharing by mutation;
a caller that stays green is not sharing") is unmet for this line.

---

## §P1b — QUANTIFIER TABLE (per-invariant ∀-over-inputs vs guarded, with door receipts)

| leg | invariant | ∀ / guarded | receipt |
|---|---|---|---|
| A | oracle TYPE+PROSE == production | **∀ over error types** (parametrized ×10 **and** recursive `__subclasses__` coverage pin) | WB-A2: new subclass reddens coverage. PROSE compare is exact `==` (line 3285), not substring. |
| A | question parity (InboxEntry) | **∀ over both backends** (parametrized fixture) | LEG C tests run real+fake; WB-C reddens. |
| B | drain stamps EXACTLY the served window | ∀ over window (0-based reconfirmed) | pre-existing over-cap pins red a wrong reshape (WB-B183 control). |
| B | #183 entries read ≤ limit | guarded (12 vs 5) on **both** doors (plain + since=) | WB-B183: read-all-then-slice reddens (materialised 12 > 5). |
| B | `stamped_seqs` = actual stamp | guarded by ONE race shape (middle-row TOCTOU) | WB-B-stamp: attempted-window reddens, deterministic **20/20**. |
| B | `since=` STRICT `>` | guarded (one cursor `seqs[1]`) | passes on correct; **conflicts with the `since=0` fixtures ⇒ F1**. |
| B | `since=` non-stamping recovery | guarded (one scenario) | reference passes; fake leg independent. |
| C | per-row `question` marker (ledger) | **∀ over {True,False}** (both forced in ONE drain) | WB-C: both hardcodes redden; dropped-projection (⇒False) reddens. |
| C | question marker (render) | — | **UNSATISFIABLE (F3)** — no build satisfies render+classification. |
| D | waiting emitted IFF `awaiting_answer` not None | **∀ over both failure directions** | WB-D: status-conflation reddens false-neg AND false-pos. |
| D | line derived from typed `WaitingOnAnswer` | guarded (seq+thread named) | WB-D also reddens `test_the_line_is_derived` (fabricated seq 0). |
| D | ONE shared helper (drain==heartbeat) | **guarded by output-identity only — HOLE** | F4: byte-identical clone survives. |
| D | hostile thread stays one sanitised line | guarded (one hostile fixture) | reference passes; `sanitise_line(thread)`. |
| B/#195 | since= re-read reuses the drain fence | guarded (one hostile body) | reference passes. |

Every "guarded" row that is a genuine hole carries a surviving wrong build (F1 `since`-strict/​
`since=0`; F4 shared-helper). The rest carry a door-build that the pin killed.

---

## §P2 — fixture-value perturbations (with correct-build controls)

- **#183** `_PAGING_INBOX=12`, `_DRAIN_CAP=5`: perturbation = read whole mailbox then Python-slice.
  Wrong build RED (`12 <= 5` fails); correct build GREEN. The 12≫5 gap is discriminating.
- **LEG C** discriminate fixture (1 question + 1 plain in one drain): `question=True` hardcode →
  `{True}≠{True,False}` RED; `question=False` hardcode → `reports_question_True` RED; correct
  GREEN. Monoculture correctly banned.
- **`since=0`**: this is the *anti*-perturbation — the fixture value 0 is where the fake (1-based)
  and production (0-based) diverge, so the pin passes for a FIXTURE reason on the fake and fails on
  real. The perturbation that would expose it at authoring is `since=seqs[0]-1` (works on both
  origins). This is F1.

---

## Full probe record (commands + real output)

All runs in `/tmp/adv-05ai-scratch/loremaster`, `uv run pytest … -p no:cacheprovider`,
provenance `loremaster.__file__ = /tmp/adv-05ai-scratch/loremaster/loremaster/__init__.py`.

1. **Seq-origin probe** → `ADV-PROBE real_first_seq=0 fake_first_seq=1`.
2. **ORDER BY probe** (L1) → `alias_asc: [0,1,2,3,4]`; `path_asc (ORDER BY in.seq): [6,2,1,7,3]`
   (silently unordered). Fix: order by the projected alias.
3. **Reference, full `test_message_ledger.py`** → `2 failed, 236 passed, 17 skipped` (the 2 = F1).
4. **Reference, `test_comms_tool.py`** → `902 passed` (after fixing L2 wiring; the L2 violation
   reddened `TestNoAwaitedWorkHappensAfterTheDrainStamps`).
5. **Reference, combined 4 files** → `5 failed, 1265 passed, 17 skipped`.
6. **WB-A2** (throwaway subclass) → `test_the_parity_battery_covers_every_message_ledger_error`
   RED `uncovered: ['_AdvThrowawayError']`. Correct: GREEN.
7. **WB-C** hardcode `question=True` → discriminate `[real]` RED (`{True}`); hardcode `False` →
   `reports_question_True[real]` + discriminate RED. Correct: GREEN.
8. **WB-B183** unbounded window read → `TestTheDrainPendingReadIsBounded[real]` RED
   (`materialised 12 … 12 <= 5`); over-cap oldest-window still GREEN.
9. **WB-B-stamp** attempted-window `stamped_seqs` → TOCTOU pin RED
   (`stamped_seqs [0,1,2] claims seq 1 … THIS drain did NOT stamp`). Correct build: **20/20** green.
10. **WB-D** status-keyed waiting line → discriminate pair RED both ways + 3 serve pins RED.
    Correct: GREEN.
11. **F4** byte-identical heartbeat clone → LEG D suite `7 passed`, promise coverage/proofs
    `32 passed` (clone SURVIVES).
12. **F3** three routes (table above): none GREEN; the `since=0` special-case `4 passed` proving
    the only escape is muddy.

---

## VERDICT: **CONTRACT INSUFFICIENT**

A known-correct reference build is 5-failed, not 0-failed. Concrete missing pins: **F1** (the
`since=0` recovery fixtures fail a strict correct build on the 0-based real store — fix the fake to
0-based and derive the cursor as `seqs[0]-1`), **F2** (add a real-vs-fake first-seq parity pin),
**F3** (register the LEG C question-marker literal — the glyph cannot be builder latitude), **F4**
(mutation-prove the ONE shared waiting helper). F1/F2/F3 are BLOCKER; F4 is MEDIUM. Route F1/F2/F3
back to CONTRACT before a builder starts — they are the class where a builder implements the
designed semantics, watches the fake pass and the real store fail, and has no way to reconcile it
without editing a test it may not touch.

---

## Appendix — the reference build (the satisfiability instrument, pasted so it survives scratch)

Applied to a `scratch_copy.sh` tree. `_message_fakes.py` diffed vs the WORKING TREE (uncommitted contract); `messages.py`/`server.py` vs repo HEAD `d9b151b` (production was untouched by the contract). NOTE: the `in.seq > $since ORDER BY seq` and window `ORDER BY seq LIMIT` use the projected ALIAS `seq` (L1 — `ORDER BY in.seq` is silently ignored on the edge).

### _message_fakes.py (LEG C passthrough)
```diff
--- /home/ejprice/PycharmProjects/lore/loremaster/tests/_message_fakes.py	2026-08-08 23:49:06.168055761 -0400
+++ tests/_message_fakes.py	2026-08-09 00:07:02.085678617 -0400
@@ -373,6 +373,7 @@
             created_at=message.created_at,
             acked_at=edge.acked_at,
             ack_note=edge.ack_note,
+            question=message.question,
         )
 
     def _delivered_after(self, agent_id: str, since: int) -> list[Message]:
```

### messages.py (LEG C field + LEG B drain reshape: since=, #183 bound, stamped_seqs truth)
```diff
--- /home/ejprice/PycharmProjects/lore/loremaster/loremaster/messages.py	2026-08-08 05:50:45.899329953 -0400
+++ loremaster/messages.py	2026-08-09 00:26:41.521963453 -0400
@@ -253,6 +253,7 @@
     created_at: datetime
     acked_at: datetime | None = None
     ack_note: str | None = None
+    question: bool = False
 
 
 class MessageDrainResult(BaseModel):
@@ -1004,58 +1005,98 @@
 
     # -- drain --------------------------------------------------------------
 
-    async def drain(self, *, agent_id: str, limit: int, peek: bool = False) -> MessageDrainResult:
-        """Serve this agent's unread inbox window and (unless ``peek``) stamp
-        EXACTLY the rows served as seen.
-
-        Pending = every message carrying an UNSTAMPED (``seen_at IS NONE``) ``to``
-        edge to ``agent_id``. The window is the oldest ``limit`` by ``seq``;
-        ``total_pending``/``directive_pending`` are computed over the WHOLE pending
-        set, never the capped window (a display cap bounds rows rendered, never the
-        numbers beside them). A non-``peek`` drain stamps ONLY the served window,
-        so an elided remainder stays unread — no cursor arithmetic.
-
-        Args:
-            agent_id: The draining agent's opaque row id.
-            limit: The display cap on served rows.
-            peek: When ``True``, serve the same rows but stamp NOTHING.
-
-        Returns:
-            The :class:`MessageDrainResult` of this call.
+    _ENTRY_PROJECTION = (
+        f"in.{_ID_KEY} AS message_id, in.seq AS seq, in.grade AS grade, "
+        f"in.sender.name AS sender_name, in.thread AS thread, in.task_id AS task_id, "
+        f"in.body AS body, in.refs AS refs, in.question AS question, "
+        f"in.created_at AS created_at, acked_at, ack_note"
+    )
+
+    async def _count_edges(
+        self, agent_rec: RecordID, predicate: str, params: dict[str, Any]
+    ) -> int:
+        """A bounded ``count() … GROUP ALL`` of this agent's ``to`` edges under
+        ``predicate`` (#183: the counts read the whole set without materialising
+        its rows)."""
+        result = await self._query(
+            f"SELECT count() FROM {TO_RELATION} WHERE out = $agent AND {predicate} GROUP ALL",
+            {"agent": agent_rec, **params},
+        )
+        return self._extract_group_count(result)
+
+    async def drain(
+        self, *, agent_id: str, limit: int, peek: bool = False, since: int | None = None
+    ) -> MessageDrainResult:
+        """Serve this agent's inbox window and (unless ``peek``) stamp EXACTLY the
+        rows served as seen.
+
+        With ``since=<seq>`` this is the DD-4.c RECOVERY read: rows keyed by seq
+        (``seq > since`` STRICT), SEEN or unseen, oldest-first, bounded — and
+        NON-stamping. The plain (``since=None``) drain serves unseen rows only,
+        with the entries read BOUNDED (#183) and the counts read separately over
+        the whole set. ``stamped_seqs`` is read BACK from the guarded UPDATE
+        (DD-4 Q5 truth), never the attempted window.
         """
         agent_rec = RecordID(AGENT_TABLE, agent_id)
-        rows = self._as_rows(
+        if since is not None:
+            rows = self._as_rows(
+                await self._query(
+                    f"SELECT {self._ENTRY_PROJECTION} FROM {TO_RELATION} "
+                    f"WHERE out = $agent AND in.seq > $since ORDER BY seq LIMIT $limit",
+                    {"agent": agent_rec, "since": since, "limit": limit},
+                )
+            )
+            total_pending = await self._count_edges(agent_rec, "in.seq > $since", {"since": since})
+            directive_pending = await self._count_edges(
+                agent_rec,
+                "in.seq > $since AND in.grade = $grade",
+                {"since": since, "grade": MESSAGE_GRADE_DIRECTIVE},
+            )
+            return MessageDrainResult(
+                entries=[self._row_to_inbox_entry(row) for row in rows],
+                total_pending=total_pending,
+                directive_pending=directive_pending,
+                stamped_seqs=[],
+                peeked=bool(peek),
+            )
+        window_rows = self._as_rows(
             await self._query(
-                f"SELECT in.{_ID_KEY} AS message_id, in.seq AS seq, in.grade AS grade, "
-                f"in.sender.name AS sender_name, in.thread AS thread, in.task_id AS task_id, "
-                f"in.body AS body, in.refs AS refs, in.created_at AS created_at, "
-                f"acked_at, ack_note "
-                f"FROM {TO_RELATION} WHERE out = $agent AND seen_at IS NONE",
-                {"agent": agent_rec},
+                f"SELECT {self._ENTRY_PROJECTION} FROM {TO_RELATION} "
+                f"WHERE out = $agent AND seen_at IS NONE ORDER BY seq LIMIT $limit",
+                {"agent": agent_rec, "limit": limit},
             )
         )
-        # The real store guarantees no incidental ordering and the adversarial fake
-        # deliberately supplies rows seq-decorrelated, so the order is pinned here.
-        pending = sorted(rows, key=lambda row: int(row["seq"]))
-        total_pending = len(pending)
-        directive_pending = sum(1 for row in pending if row.get("grade") == MESSAGE_GRADE_DIRECTIVE)
-        window = pending[:limit]
+        window = sorted(window_rows, key=lambda row: int(row["seq"]))
+        total_pending = await self._count_edges(agent_rec, "seen_at IS NONE", {})
+        directive_pending = await self._count_edges(
+            agent_rec, "seen_at IS NONE AND in.grade = $grade", {"grade": MESSAGE_GRADE_DIRECTIVE}
+        )
         entries = [self._row_to_inbox_entry(row) for row in window]
         stamped_seqs: list[int] = []
         if not peek and window:
+            seq_by_message: dict[str, int] = {
+                self._bare_id(row["message_id"]): int(row["seq"]) for row in window
+            }
             window_records = [
-                RecordID(MESSAGE_TABLE, self._bare_id(row["message_id"])) for row in window
+                RecordID(MESSAGE_TABLE, mid) for mid in seq_by_message
             ]
-            await self._query(
-                f"UPDATE {TO_RELATION} SET seen_at = $seen_at "
-                f"WHERE out = $agent AND in IN $message_ids AND seen_at IS NONE",
-                {
-                    "seen_at": datetime.now(UTC),
-                    "agent": agent_rec,
-                    "message_ids": window_records,
-                },
+            stamped_edges = self._as_rows(
+                await self._query(
+                    f"UPDATE {TO_RELATION} SET seen_at = $seen_at "
+                    f"WHERE out = $agent AND in IN $message_ids AND seen_at IS NONE "
+                    f"RETURN AFTER",
+                    {
+                        "seen_at": datetime.now(UTC),
+                        "agent": agent_rec,
+                        "message_ids": window_records,
+                    },
+                )
+            )
+            stamped_seqs = sorted(
+                seq_by_message[self._bare_id(edge.get("in"))]
+                for edge in stamped_edges
+                if self._bare_id(edge.get("in")) in seq_by_message
             )
-            stamped_seqs = [int(row["seq"]) for row in window]
         return MessageDrainResult(
             entries=entries,
             total_pending=total_pending,
@@ -1123,6 +1164,7 @@
             created_at=self._require_aware_utc(row.get("created_at")),
             acked_at=self._to_aware_utc(row.get("acked_at")),
             ack_note=row.get("ack_note"),
+            question=bool(row.get("question")),
         )
 
     # -- ack / awaiting_answer (packet 03a-2 — the CONSUME path) ------------
```

### server.py (LEG D waiting-line helper + drain/heartbeat wiring, read BEFORE the stamp per L2)
```diff
--- /home/ejprice/PycharmProjects/lore/loremaster/loremaster/server.py	2026-08-08 17:41:29.387299692 -0400
+++ loremaster/server.py	2026-08-09 00:28:07.895181325 -0400
@@ -181,6 +181,7 @@
     MessageLedger,
     MessageSendResult,
     PendingTraffic,
+    WaitingOnAnswer,
 )
 from loremaster.render import (
     render_attributed,
@@ -5989,12 +5990,14 @@
         subscribed_skew = await self.brief_ledger.subscribed_name_skew(
             agent_id=agent_row.id, exclude=STANDING_BRIEF
         )
-        return AppContext._render_comms_heartbeat(
+        heartbeat = AppContext._render_comms_heartbeat(
             agent_row,
             project_head_version=head_version,
             project_acked_version=acked_version,
             subscribed_skew=subscribed_skew,
         )
+        waiting_lines = await AppContext._comms_waiting_lines(self, agent_row=agent_row)
+        return render_compose(heartbeat, *waiting_lines)
 
     async def _comms_brief_get(
         self, *, agent_row: Agent, session: str | None, name: str | None, **_ignored: Any
@@ -6446,6 +6449,7 @@
         STAMPED window whose render never reached the caller.
         """
         skew_lines = await AppContext._comms_brief_skew_lines(self, agent_row=agent_row)
+        waiting_lines = await AppContext._comms_waiting_lines(self, agent_row=agent_row)
         display_limit = min(
             limit if limit is not None else self.config.comms.drain_limit, _MAX_DRAIN_LIMIT
         )
@@ -6458,7 +6462,19 @@
             limit=display_limit,
             session=agent_row.session,
         )
-        return render_compose(inbox, *skew_lines)
+        return render_compose(inbox, *waiting_lines, *skew_lines)
+
+    async def _comms_waiting_lines(self, *, agent_row: Agent) -> list[Rendered]:
+        """Read the DERIVED question-debt and render it — the ONE read+compose both
+        drain and heartbeat ride (DD-2.a). Keyed on ``awaiting_answer`` (the derived
+        debt), NEVER the stored ``input_required`` status."""
+        waiting = await self.message_ledger.awaiting_answer(agent_id=agent_row.id)
+        age_s = (
+            int((datetime.now(UTC) - waiting.asked_at).total_seconds())
+            if waiting is not None
+            else 0
+        )
+        return AppContext._render_comms_waiting_line(waiting, age_s=age_s)
 
     async def _comms_ack(
         self, *, agent_row: Agent, seqs: list[int], note: str | None, **_ignored: Any
@@ -7472,6 +7488,22 @@
         return render_compose(*lines)
 
     @staticmethod
+    def _render_comms_waiting_line(waiting: WaitingOnAnswer | None, *, age_s: int) -> list[Rendered]:
+        """The DD-2.a derived question-debt line, as a list of ``Rendered`` (empty
+        when the agent owes no question) — the ONE helper both drain and heartbeat
+        compose, so a template change moves BOTH verbs (the skew-lines precedent)."""
+        if waiting is None:
+            return []
+        return [
+            render_line(
+                "waiting: your question #{seq} on thread {thread} has no reply — asked {age} ago",
+                seq=waiting.question_seq,
+                thread=sanitise_line(waiting.thread),
+                age=AppContext._render_age(age_s),
+            )
+        ]
+
+    @staticmethod
     def _render_comms_drain_row(entry: InboxEntry, *, session: str) -> Rendered:
         """ONE drain row's HEADER line — the body is fenced beneath it by the caller.
 
```

---

# §DELTA — re-grade of the F1–F4 fix wave (adv-05ai-1, second pass)

**Graded:** the FIXED contract in the working tree (`_message_fakes.py`,
`test_comms_promise_registry.py`, `test_message_ledger.py` modified;
`test_comms_waiting_line.py` untracked) at HEAD `d9b151b` · reference build in a FRESH scratch
`loremaster.__file__ = /tmp/adv05ai-delta/loremaster/loremaster/__init__.py` · store 3.2.4, `:18000`.
Directive #4007 (thread 05ai-delta) drained + acked.

## DELTA VERDICT: **CONTRACT INSUFFICIENT** — F1–F4 CLOSED, but the F3 fix opened **ONE new door (F5)**.

**Satisfiability RE-DERIVED on my OWN reference build (not the author's claim):**
`1274 passed / 0 failed / 17 skipped` across all four files — AND ruff + mypy clean on the changed
production files (`messages.py`, `server.py`, `_message_fakes.py`), so there is no
green-only-before-the-lint C-DEF trap. The author's 1274/0 reproduces.

### F1–F4 — CLOSED (each new pin empirically catches its wrong build; correct build passes)

| fix | wrong build I constructed | result |
|---|---|---|
| **F1** muddy `since==0 ⇒ >=` special-case | applied it | `test_since_0_does_NOT_re_serve_a_processed_seq_0[real]` RED (`[0,1,2]==[1,2]`, re-served processed seq 0); the recover-all fixtures (cursor `seqs[0]-1=-1`) STAY green. **Killed.** |
| **F2** 1-based fake | reverted the mint to increment-then-assign | `test_a_fresh_ledgers_first_send_has_the_SAME_seq_on_both_backends` RED (`0 == 1`). ⚠ NOTE: the `since=` fixtures derive the cursor from `seqs[0]`, so they STILL pass on a 1-based fake — the parity pin is the **only** instrument that catches the origin gap, i.e. load-bearing, not redundant. **Caught.** |
| **F3** exact `(question)` token | context-slot marker (safe_str glue) | `test_the_marker_is_ON` RED — the exact-token assertion `q_tokens - plain_tokens == {"(question)"}` rejects the glued `lead→you(question)` token. Also: **mark-ALL-rows** → all 3 render pins RED; **only-the-no-refs-variant** → `test_no_dead_registry_entries` RED (the refs-question template registered-but-unemitted). **Robust on the no-refs path.** |
| **F4** byte-identical heartbeat clone | inlined a byte-identical clone in `_comms_heartbeat` | `test_both_verbs_route_through_the_ONE_helper_PROVEN_BY_MUTATION` RED (no sentinel in heartbeat), while the OLD output-identity pin STAYS green (confirming the clone is byte-identical — the exact hole now closed). Monkeypatch reaches BOTH verbs. **Closed.** |

### F5 (NEW, MEDIUM) — the F3 fix opened a door: the refs+question render is UNEXERCISED at runtime

**Wrong build that SURVIVES the entire fixed contract (1274/0):** mis-wire the refs branch of
`_render_comms_drain_row` — mark refs+**non**-question rows with `(question)` and leave
refs+**question** rows UNMARKED (both registered templates stay in the source, so the static
`test_no_dead_registry_entries` scan is satisfied). This build inverts the marker for **every
message carrying refs** — a refs+question message shows no marker; a refs+plain message is falsely
marked — and passes `test_message_ledger.py + test_comms_tool.py + test_comms_waiting_line.py +
test_comms_promise_registry.py` **identically to the correct build (1274 passed)**.

*Why:* the LEG C render fixtures (`test_comms_waiting_line.py::_q_entry`) hardcode `refs=[]`, so
only the NO-refs branch is exercised at runtime. The refs-question template variant the fix wave
added is guarded ONLY by the static "the literal exists in server.py source" scan
(`test_no_dead_registry_entries`), never by a runtime discrimination. Messages routinely carry refs
(the whole "messages carry POINTERS" design), so this is not a corner.

**MISSING PIN:** a render discriminate pin with a refs-carrying entry — mirror
`TestTheDrainRowVisiblyMarksAQuestion` with `refs=["docs/x.md"]`: a refs+question row must contain
`(question)`, a refs+non-question row must NOT. Add it and the mis-wired build above goes RED.

### Residual verdicts

- Aligning the fake to 0-based broke **no** other fake-dependent test (full 1274/0). The `burn_seq`
  helper was aligned too; no seq-value-pinned test regressed.
- The `seqs[0]-1` recover-all cursor is correct ∀ (derived from the actual first seq, not hardcoded),
  so it holds on any origin — verified by the fixtures passing on both 0-based backends.
- No other new door found: the context-slot glue and a safe_str `(question)` injection are both
  caught (the former by the exact-token assertion, the latter would be an unclassified safe_str
  literal).

**One-line:** F1–F4 CLOSED and satisfiability 0-failed re-derived, but the F3 fix left the
refs+question render path unexercised — a mis-wired refs branch that inverts the marker on every
refs-carrying message survives the whole contract (1274/0). One missing pin (F5): a
`refs=[...]`-carrying question/non-question render discriminate pair.

---

# §DELTA-2 — re-grade of the F5 fix (adv-05ai-1, third pass; the last sweep)

**Graded:** the F5-fixed contract in the working tree at HEAD `d9b151b` · reference build in a FRESH
scratch `loremaster.__file__ = /tmp/adv05ai-delta2/loremaster/loremaster/__init__.py` · store 3.2.4,
`:18000`. Directive #4011 (thread 05ai-delta2) drained + acked.

## DELTA-2 VERDICT: **CONTRACT SUFFICIENT** — F1–F5 CLOSED, satisfiability 0-failed re-derived, no plausible new door. One LOW-severity residual noted (non-blocking).

**Satisfiability RE-DERIVED on my OWN reference build** (not the author's claim):
`1275 passed / 0 failed / 17 skipped` across all four files, ruff + mypy clean on the changed
production. The author's 1275/0 reproduces (+1 vs delta-1 = the new refs-variant pin).

### F5 — CLOSED

- **The new `test_the_REFS_variant_ALSO_discriminates_question_from_non_question` catches the F5
  mis-wire.** Constructed the exact door: swap the refs-branch condition to `if not entry.question`
  (refs+question rows UNMARKED, refs+non-question falsely marked; both templates stay in source so
  `test_no_dead_registry_entries` is satisfied). RESULT: the new pin RED
  (`assert set() == {'(question)'}` — the refs+question row carried no marker), while the three
  NO-refs render pins STAY green — so the new pin is the load-bearing instrument for the refs
  branch, exactly where the coverage gap was. Positive control: the correct build passes (1275/0).
- **`_q_entry.refs` made REQUIRED weakened nothing.** The call sites split correctly: `refs=[]` at
  the no-refs-branch pins (they test that branch on purpose) and `refs=[ref]` at the new
  refs-branch pin. Making it required enforces the AC-11 explicit-branch-choice discipline (no
  defaulted branch param); no fixture now passes for a wrong reason.

### F1–F4 — remain CLOSED

The fix wave touched only the LEG C render fixtures + the two refs `(question)` templates' guard;
F1/F2 (seq origin + parity pin + `seqs[0]-1` cursor + muddy-build killer), F3 (exact `(question)`
token, both variants), and F4 (monkeypatch mutation pin) are unchanged and re-derive green in the
1275/0 run. No regression from the F5 fix.

### RESIDUAL (LOW, non-blocking) — the question marker × non-empty context path is unexercised

Every LEG C render fixture uses `task_id=None` and `thread == session`, so the `{context}` cell is
always empty in the question-marker tests. A build that DROPS the task/thread context label on
question rows only (override `context = safe_str("")` when `entry.question`, keeping the registered
template literal) SURVIVES the whole contract (1275/0) — a question+task message would render
without its task label, unpinned.

**Why this is LOW and NOT a blocker:** unlike the F5 mis-wire (a plausible honest slip — inverting
one of two duplicated `if entry.question` branches), this is a CONTRIVED construction. The natural
implementation computes `context` ONCE before the render branches and shares it across all four, so
context is correct for question rows by construction; there is no honest path that drops it. The
LEG C marker property itself (the token, both variants, discrimination, orthogonality to grade) is
fully pinned. **Optional cheap pin if the lead wants belt-and-braces:** one `_q_entry` fixture with
`question=True` + a `task_id` (or non-session thread), asserting the context label survives beside
`(question)`. I surface it per scope law; I do not block on it.

**One-line:** F1–F5 CLOSED; satisfiability 0-failed re-derived on my own reference (1275/0, ruff+mypy
clean); the new refs-variant pin catches the F5 mis-wire; required-refs weakened nothing. One
LOW/contrived residual (question×context coverage) noted, non-blocking. **SUFFICIENT — clear to fire
the builder.**
