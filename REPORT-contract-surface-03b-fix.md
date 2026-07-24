brief-base v6 read

# REPORT-contract-surface-03b-fix — packet 03b SURFACE contract, FIX WAVE

**Authored 2026-07-24** against repo `feat/surreal-unification` HEAD `706924d` (clean at spawn).
Answers `REPORT-adversary-surface-03b.md` (VERDICT INSUFFICIENT — 32 of 41 wrong builds survived).
Writable set: `test_comms_tool.py`, `test_comms_promise_registry.py`, `test_message_ledger.py`,
`test_surreal_harness.py` (Part B only), this report. **No production code touched. Oracle
`_message_fakes.py` NOT edited (not required).**

## SUMMARY BLOCK

- **state: done.** All 2 BLOCKER · 9 CRITICAL · 8 MAJOR · 6 MINOR adversary findings addressed;
  every load-bearing pin mutation-proven RED on its target wrong build.
- **NO-OP FIX closed, BOTH halves:** W1 (send render never called) → B1 RED
  (`'sent #1 [directive] → fixer-b' in 'no unread messages'`); W10 (ack render never called) →
  B2 RED (`'acked 1 of 1: #1' in 'no unread messages'`).
- **Mutation proofs: 34/34 target wrong builds go RED at the intended pin, for the intended
  behavioural reason** (§4). The one driver "SURVIVOR" (W44) is a mis-map — W44 is caught by the
  *committed* cap pins (adversary I2 ✅); my m1 targets W42, which is RED.
- **Satisfiability: 1162 passed / 12 skipped / 0 failed** against the reference S4/S5 build — ROSE
  from the predecessor's 1092 by +70 (28 new named pins + 2 new injection RenderCases × the
  threat battery). C-DEF receipt holds.
- **Part B (repo was RED): FIXED, and a SECOND stale count found.** Both the importer count
  (35→**36**) AND the `connect_admin`-caller count (21→**22**) were stale — both from 03b's own
  `a774c8f` (`test_trace_telemetry.py` imports the harness AND calls `connect_admin`). Counts
  RE-DERIVED via AST, not hardcoded. `test_surreal_harness.py` → 57 passed.
- **mypy RE-DERIVED: 96 at HEAD (not the design doc's 36, not the adversary's 58 — my new pins add
  38 S4/S5 forward-refs). Of the 96: 90 are STRUCTURAL (vanish when S4/S5 is built — proven: scratch
  = 6), 6 are NON-STRUCTURAL** (all `test_trace_telemetry.py::record_trace(caller=)` — the S6/S7
  TELEMETRY wave's, NOT paid by S4/S5). ruff clean on all writable files.
- **provenance:** `loremaster.__file__ = /home/ejprice/scratch/surface03bfix/loremaster/loremaster/__init__.py`
  (scratch, asserted by `scratch_copy.sh`; scratch test files byte-identical to repo — §5).
- **escalations (§6):** (1) design doc Residual 8's "mypy 36→0 structural" is FALSE — global
  mypy-zero needs the telemetry build too; (2) R5/m4: `_render_comms_drain`'s `agent_name`+`limit`
  are DEAD params in the ruled signature — spec question for the design sidecar; (3) Part B counts
  depend on the sibling telemetry wave — re-derive before the final gate; (4) m5/m6 cosmetic/latent,
  left with rationale.
- **decisions-needed:** none blocking. I did NOT commit (lead commits per standing law) — natural
  commit boundaries named in §7.

---

## Part B — the RED repo, repaired (do-this-first)

`test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`
failed at HEAD. The pin re-derives two populations by AST and checks the harness docstring against
them. **Both stated numbers were stale**, and the second was hidden behind the first assert:

| docstring claim | stated | DERIVED (AST, 2026-07-24) | cause |
|---|---|---|---|
| "N test files import this harness" | 35 | **36** | `a774c8f` added `test_trace_telemetry.py`, which imports the harness |
| "N test files — calls `connect_admin`" | 21 | **22** | the SAME file calls `connect_admin` 3× |

The brief named only the importer count; the caller count is a second 03b-caused regression the
first assert masks. Both fixed in `_surreal_harness.py`'s module docstring (35→36, 21→22).
`_derive` receipt (regeneratable): the AST walker in the pin itself, or the one-liner in §8.

- **The pin is CORRECT and untouched** — it caught a real drift; only the docstring was stale.
- **The historical narrative in the PIN's own docstring** (`"…was FALSE: 35 files import it; 21 call
  connect_admin"`) is dated context about finding #150 and is left as-is: rewriting its numbers to
  36/22 would falsify the record of what the #150 defect was. Judgment call, flagged.
- **Out-of-writable-set stale hit (FLAG, not edited):** `test_retry_seam.py` contains a comment
  `"(35 test files import it — …)"` — now also stale (36), same `a774c8f` cause. It is a comment, not
  a gate, and the file is outside my writable set. Exact edit for the owner: `35 → 36`.

Receipt: `test_surreal_harness.py` → **57 passed** (real repo, 2026-07-24). Counts re-derived NOW:
`importers=36  connect_admin_callers=22`.

---

## Part A — the pins, by severity (all in `test_comms_tool.py`)

Every adversary finding is a surface render/dispatcher pin, so all pins landed in
`test_comms_tool.py`; `test_comms_promise_registry.py` and `test_message_ledger.py` needed no change
(the promise-registry statics and the frozen ledger contract are not where these 32 survivors live).
Each row names the pin, its home class, and the wrong build(s) it turns RED (all proven §4).

### BLOCKER — the no-op fix, twice (the #94 shape)

| pin | class | catches |
|---|---|---|
| `test_the_SEND_dispatcher_serves_the_SEND_RENDER` | `TestDrainAndAckAtTheDispatcher` | **W1** — drives the REAL `comms(action="send", grade="directive", set_status="input_required", thread="q:cap")` and asserts the receipt, the ack-trailer AND the question line all reach the output. A handler returning hardcoded text fails all three. |
| `test_the_ACK_dispatcher_serves_the_ACK_RENDER` | `TestDrainAndAckAtTheDispatcher` | **W10** (wiring) + **W11** (counts) + **W12** (already-acked distinct) + **W15b** (not-addressed names the CALLER, not the session) — all through the real `action=ack` dispatch. |

### CRITICAL

| pin | class | catches |
|---|---|---|
| `test_the_header_names_the_TRUE_pending_total` | `TestRenderCommsDrainShape` | **W4, W5** — header `drained/peeked 2 of 7 pending`, exact. |
| `test_an_unacked_SIGNAL_is_not_demanded` | `TestRenderCommsDrainShape` | **W41** — the grade axis of the ACK-REQUIRED monoculture R3 left open (unacked signal + unacked directive; only the directive is demanded). |
| `test_the_ACK_REQUIRED_command_is_RUNNABLE` | `TestRenderCommsDrainShape` | **W6** — extracts `action=ack seqs=[…]` and asserts it names every demanded seq (the proof marker stopped one char short). |
| `test_a_broadcast_receipt_names_the_true_fan_out_and_the_session` | `TestBroadcastFanOut` | **W2b, W2c, W3** — dispatcher broadcast (explicit non-session thread) catches all three: wrong count, thread-in-session-slot, and the handler never rendering the broadcast variant. |
| `test_the_question_teach_survives_a_BROADCAST` | `TestBroadcastFanOut` | **W33** — broadcast question keeps its clearing-rule teach. |
| `test_send_forwards_set_status_task_id_and_refs` | `TestDrainAndAckAtTheDispatcher` | **W28, W29** — question line present (set_status forwarded) AND the next drain row shows `(task T-9)` + refs. |
| `test_the_body_cap_is_DERIVED_from_the_constant` | `TestTheServedInstructions…` | **W16** — extracts the served integer, compares to `MESSAGE_BODY_MAX_CHARS` (#104: derive, don't restate). |
| `test_the_grade_and_peek_and_broadcast_semantics_taught_are_the_ones_IMPLEMENTED` | `TestTheServedInstructions…` | **W17, W18, W19** — peek/grade/broadcast semantics not invertible. |
| `test_a_broadcast_with_session_OMITTED_stays_in_the_callers_session` | `TestBroadcastFanOut` | **W32** — roster scoped by `agent_row.session`, not the nullable param; a wave9 outsider gets nothing. |

### MAJOR

| pin | class | catches |
|---|---|---|
| `test_to_EMPTY_LIST_is_a_broadcast` | `TestDrainAndAckAtTheDispatcher` | **W31** — `to=[]` broadcasts (not `EmptyRecipientSetError`). |
| `test_the_drain_serves_its_rows_in_LEDGER_order` | `TestRenderCommsDrainShape` | **W25** — `#61` before `#62` by index. |
| `test_every_served_row_renders_ABOVE_the_first_trailer` | `TestRenderCommsDrainShape` | **W8** — composition order (rows above trailers/elision). |
| `test_a_row_with_REFS_renders_them` | `TestRenderCommsDrainShape` | **W7** — the refs row variant actually renders. |
| `test_the_row_names_the_GRADE_and_the_SENDER_in_the_right_slots` | `TestRenderCommsDrainShape` | **W24, W24b** — grade/sender slots not swapped or thread-fed. |
| `test_drain_honours_an_EXPLICIT_limit_at_the_dispatcher` | `TestDrainAndAckAtTheDispatcher` | **W9** — `limit=1` serves one, leaves two unread. |
| `test_the_send_receipt_names_the_MESSAGES_seq_and_grade` | `TestRenderCommsSendShape` | **W22, W23** — receipt seq/grade + the trailer seq. |
| `test_ack_forwards_the_NOTE` | `TestDrainAndAckAtTheDispatcher` | **W27** — the note lands on the winning edge. |

### The ack render, pinned end to end (was UNPINNED — new class `TestRenderCommsAckShape`)

| pin | catches |
|---|---|
| `test_the_four_groups_render_in_FIXED_order` | **W13** — acked · already-acked · not-addressed · unknown. |
| `test_seqs_within_a_group_stay_in_REQUEST_order` | **W14** — `#9, #3` not re-sorted. |
| `test_the_receipt_counts_are_the_TRUE_counts` | **W11** — `acked 1 of 2`. |
| `test_already_acked_is_a_DISTINCT_group_from_acked` | **W12** — not folded. |
| `test_not_addressed_names_the_CALLER` | **W15** — names `agent_name`. |

### MINOR

| pin / action | catches / disposition |
|---|---|
| `test_the_capped_recipient_list_shows_the_FIRST_names` (`TestRenderCommsSendShape`) | **m1 → W42** (tail slice); exact comma-split membership (also pre-empts m6's substring hazard). |
| `drain.task_id` + `drain.refs` RenderCases + `TestDrainTaskIdAndRefsInjectionCasesAreNotVACUOUS` | **m2** — the two caller-controlled row fields the battery lacked, with non-vacuity guards. |
| `test_description_names_every_action_as_a_WHOLE_WORD` (`TestCommsToolRegistration`) | **m3** — word-boundary (`\back\b` matches `'ack'` not the `_ack` in `brief_ack`); discrimination proven (§4, hand mutation: old substring pin passes vacuously, new pin RED). |
| **m4** | ESCALATION (see §6). |
| **m5** | cosmetic — `_drain_line_containing` is reused by send/ack pins; left un-renamed (broad churn for zero behaviour). Flagged. |
| **m6** | the committed `test_the_recipient_list_shares_ONE_display_cap` counts by substring membership — LATENT only (no substring-collision at `_COVERAGE_NAMES_CAP=5`); my m1 uses exact split. Flagged, committed pin left un-touched (would alter a committed assertion). |

---

## Satisfiability + provenance (receipt 1, 2, 5)

Fresh `scripts/scratch_copy.sh /home/ejprice/scratch/surface03bfix` (provenance asserted, printed
above), reference S4/S5 build applied via the adversary's `refbuild/apply_reference.py`, three
surface files run against the scratch's OWN venv:

```
loremaster.__file__ = /home/ejprice/scratch/surface03bfix/loremaster/loremaster/__init__.py
1162 passed, 12 skipped in 10.07s     # test_comms_tool.py + test_comms_promise_registry.py + test_message_ledger.py
```

Predecessor baseline 1092 → **1162** (+70). Scratch test files md5-identical to the repo (all 4).
ruff: `All checks passed!` on all four writable files (real repo).

---

## §4 — Mutation-proof table (receipt 3)

Driver `refbuild/prove.sh` (in the scratch): for each wrong build, apply → run ONLY the target
pin's node id → assert RED → restore. Running the target pin alone means each RED is the
BEHAVIOURAL assertion firing, never a static literal classifier (the adversary's own "caught for the
wrong reason" trap).

```
RED ✅ W1  W10  W4  W5  W41  W6  W2b  W2c  W3  W33  W28  W29  W16  W17  W18  W19  W32
RED ✅ W31 W25  W8  W7  W24  W24b W9  W22  W23  W27  W42  W13  W14  W11  W12  W15
       →  33 of 34 target-mapped mutations RED at the intended pin.
W44 "SURVIVOR" = driver mis-map: W44 (under-cap → first name only) is caught by the COMMITTED
     cap pins (adversary I2 ✅); verified 2 failed. My m1 targets W42 (RED above).
W15b (ack identity) vs B2: RED — "no delivery to wave7" instead of "to idle-c".
m3 discrimination (hand mutation removing standalone 'ack'): OLD substring pin PASS (vacuous),
     NEW word-boundary pin FAIL — exactly the vacuity the finding named.
```

Sample intended-reason receipts (assertion lines, not collection noise):
- W1 → `assert 'sent #1 [directive] → fixer-b' in 'no unread messages'`
- W10 → `assert 'acked 1 of 1: #1' in 'no unread messages'`
- W2c → `assert 'broadcast: 3 agents in session wave7' in 'sent #1 [signal] → broadcast: 3 agents in session q:cap'`
- W29 → `assert "awaiting an answer on thread 'q:cap'" in 'sent #1 [signal] → fixer-b'`
- W18 → `assert 'to=[] broadcasts to all non-retired' in "…(to=[] sends to nobody; name every recipient)…"`

---

## §5 — mypy re-derivation (receipt 2 — the hard leg)

`uv run mypy loremaster`, file breakdown, 2026-07-24:

| where | total | test_comms_tool.py | test_comms_promise_registry.py | test_trace_telemetry.py |
|---|---|---|---|---|
| **HEAD `706924d`** (S4/S5 NOT built, my pins present) | **96** | 87 | 3 | 6 |
| **scratch** (S4/S5 reference build applied) | **6** | 0 | 0 | 6 |

- **90 of 96 are STRUCTURAL** — forward-refs to `_render_comms_*` / `comms(...)` kwargs /
  `CommsConfig.drain_limit` / `AppContext.message_ledger` that the S4/S5 build resolves. Proof: they
  are ZERO in the scratch. My new pins raised the HEAD total from the adversary's 58 to 96 (+38),
  and every one of the +38 is structural.
- **6 are NON-STRUCTURAL** — `test_trace_telemetry.py::record_trace(caller=…)` (S6/S7 telemetry,
  the SIBLING wave's file, which I did not touch). They are UNCHANGED from the adversary's residual
  of 6, and the S4/S5 build does NOT pay them.
- **Verdict, confirming adversary R2:** design doc Residual 8's *"Global mypy-zero (36→0) is
  structural: building S4's surface pays [it]"* is **FALSE** on two counts — the number is wrong,
  and 6 errors are not S4/S5's to pay. **03b owns global mypy-zero, but the SURFACE builder alone
  cannot reach it; the surface build + the telemetry build must both land.** (Escalation §6.)

---

## §6 — Escalations & flags (scope is the operator's)

1. **Global mypy-zero crosses wave boundaries.** After a full S4/S5 build, 6 mypy errors remain,
   all `test_trace_telemetry.py::record_trace(caller=)` — the telemetry contract's RED forward-ref.
   The surface builder cannot clear them; the S4/S5 and S6/S7 builds must land together (or the
   telemetry build lands the `record_trace(caller=…)` signature first). Named so 03b's global
   mypy-zero is not attributed to the surface builder in isolation.
2. **R5 / m4 — `_render_comms_drain` has DEAD ruled params.** The ruled signature
   `_render_comms_drain(result, *, agent_name, limit, session)` forces the builder to accept
   `agent_name` (immediately `del`'d — "the drain block never names its own reader") and `limit`
   (never read; only the elision TEMPLATE says `limit={next_limit}`, fed by `next_limit=more`).
   This is a SPEC question — is a line missing from S4.2 that consumes them, or is the signature
   wider than the ruling? — **for the design sidecar, not a builder or a pin.** Pinning "unused"
   pins dead code; pinning "used" contradicts the reference. Left un-pinned, escalated.
3. **Part B counts depend on the sibling telemetry wave.** `36`/`22` are DERIVED from a tree that
   includes `test_trace_telemetry.py` (owned by `contract-telemetry-03b-fix`, editing concurrently).
   If that wave adds/removes a harness-importing or `connect_admin`-calling test file before the
   final gate, the docstring goes stale — the pin is self-checking and will go RED; **re-derive,
   don't hardcode.** Re-derived stable at 36/22 as of this report.
4. **m5 (cosmetic):** `_drain_line_containing` is reused by send/ack pins; its name and failure
   message say "drain". A rename touches ~25 call sites for zero behaviour change — left as-is.
5. **m6 (latent):** the committed `test_the_recipient_list_shares_ONE_display_cap` counts recipients
   by substring membership; safe at `_COVERAGE_NAMES_CAP=5` (no name is a substring of another), a
   future `agent-1`/`agent-11` rename would double-count. My m1 uses exact comma-split. Left the
   committed pin untouched (editing it alters a committed assertion — outside the mechanical grant).
6. **`test_retry_seam.py`** carries a now-stale `"35 test files import it"` comment (same `a774c8f`
   cause), outside my writable set — exact edit `35→36` for the owner.
7. **Oracle `_message_fakes.py` NOT edited** — no finding required it (the `set_status→question`,
   ack-outcome, and edge-note mechanisms all already exist and the mutation proofs exercise them).
8. **I did not commit.** Per standing law the lead commits; brief receipt #6 ("commit at natural
   boundaries") is read as the granularity to use. Natural boundaries: (a) Part B docstring repair;
   (b) the BLOCKER+CRITICAL surface pins; (c) the MAJOR+MINOR pins + ack-shape class; or a single
   "close adversary surface findings" commit if the lead prefers.

---

## §7 — Before → after per file

| file | before | after | change |
|---|---|---|---|
| `test_comms_tool.py` | 214 test methods | 242 | +28 named pins (+ 2 injection RenderCases × threat battery); +773 lines |
| `test_comms_promise_registry.py` | 75 | 75 | none (no finding required it) |
| `test_message_ledger.py` | 94 | 94 | none (no finding required it) |
| `_surreal_harness.py` | docstring 35/21 | 36/22 | Part B (2 lines) |

Satisfiability count against the reference build: 1092 → **1162** (+70).

---

## §8 — Reproduction recipe

```bash
# Part B count derivation (regeneratable — the AST walker is the pin itself):
python3 - <<'PY'
import ast, pathlib
h=pathlib.Path('loremaster/tests/_surreal_harness.py'); d=h.parent
imp=cal=0
for p in sorted(x for x in d.rglob('*.py') if x!=h):
    t=ast.parse(p.read_text())
    imp += any((isinstance(n,ast.Import) and any(a.name=='_surreal_harness' or a.name.startswith('_surreal_harness.') for a in n.names)) or (isinstance(n,ast.ImportFrom) and n.module=='_surreal_harness') for n in ast.walk(t))
    cal += any(isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id=='connect_admin') or (isinstance(n.func,ast.Attribute) and n.func.attr=='connect_admin')) for n in ast.walk(t))
print('importers',imp,'callers',cal)   # -> 36 22
PY

# Satisfiability + mutation proofs (scratch, reference S4/S5 build):
./scripts/scratch_copy.sh /home/ejprice/scratch/surface03bfix          # asserts provenance
python3 /home/ejprice/scratch/adv03b/refbuild/apply_reference.py /home/ejprice/scratch/surface03bfix
cp loremaster/tests/{test_comms_tool,test_comms_promise_registry,test_message_ledger,_surreal_harness}.py \
   /home/ejprice/scratch/surface03bfix/loremaster/tests/
cd /home/ejprice/scratch/surface03bfix
LORE_TEST_SURREAL_URL=ws://127.0.0.1:18000/rpc uv run pytest -n auto -q \
  loremaster/tests/test_comms_tool.py loremaster/tests/test_comms_promise_registry.py \
  loremaster/tests/test_message_ledger.py                              # -> 1162 passed, 12 skipped
bash refbuild/prove.sh                                                  # -> all target mutations RED
```

**Scratch tree** `/home/ejprice/scratch/surface03bfix` is a disposable `scratch_copy.sh` copy (NOT a
git worktree). It carries the reference build + `refbuild/{mutate,prove}.py|sh`. Operator: discard
at will, or keep for the adversary's re-grade.

---

## §9 — AMENDMENT R5-OUTCOME-2 (design-sidecar ruling, 2026-07-24; landed after `44c42b7`)

The R5/m4 escalation (§6.2) was ruled **OUTCOME 2: drop both dead params.**
`_render_comms_drain(result, *, agent_name, limit, session)` → **`_render_comms_drain(result, *, session)`.**
`_render_comms_ack` KEEPS `agent_name` (load-bearing in `…no delivery to {name}`) — untouched.

**Why both are dead (design-ruled):** `limit` was orphaned when the elision was ruled fully
result-derived (`more = total_pending − len(entries)`; `next_limit == more`; emit predicate
`total_pending > shown`) — the render never read it. `agent_name` never had a consumer — no drain
template carries `{name}`; the row is `{sender}→you` with a literal second person, now a recorded
deliberate choice (NOT to be re-added as a header/label).

**What changed (tests only — the production signature is the builder's, but the reference build and
every DRIVER now match the ruling):**
- `test_comms_tool.py`: the `TestRenderCommsDrainShape._render` helper (dropped its own dead `limit`
  param too, + 7 callers de-`limit`'d), the 5 injection drivers (`_render_drain_body/sender/thread/
  task_id/refs`), and the class docstring's ruled-signature prose.
- `test_comms_promise_registry.py`: the `_render_drain` driver (dropped `limit` param + 2 callers)
  and its ruled-signature prose.
- `refbuild/server.py.reference` (scratch only): the render signature AND the `_comms_drain` handler
  call — a CORRECT build of the ruled signature.

**The dropped signature IS the pin (no new discriminating pin — lead-ruled).** Every driver now calls
`_render_comms_drain(result, session=…)`; a build whose render still REQUIRES either param is a
`TypeError` at the call sites. Mutation-proven both ways (2026-07-24, scratch):

```
re-require agent_name -> TypeError: _render_comms_drain() missing 1 required keyword-only argument: 'agent_name'   (RED at render pin AND dispatcher drain pin)
re-require limit      -> TypeError: _render_comms_drain() missing 1 required keyword-only argument: 'limit'         (RED, same call sites)
restore               -> 2 passed
```

**Receipts (2026-07-24):**
- Satisfiability HELD: **1162 passed / 12 skipped / 0 failed** (reference build, R5 applied) — count
  unchanged (params dropped mechanically, no pins removed).
- Full 34-mutation suite **re-run post-R5: all still RED** at the intended pin (only the known W44
  driver mis-map "survives", caught by the committed cap pins).
- ruff clean; mypy HEAD **96** (87 `test_comms_tool.py` + 3 `test_comms_promise_registry.py` +
  6 telemetry), scratch **6** — the structural/non-structural split is UNCHANGED by R5.
- provenance: `loremaster.__file__ = /home/ejprice/scratch/surface03bfix/loremaster/loremaster/__init__.py`.
- Committed with explicit paths (test files + this report only; the 4 concurrently-modified
  `test_surreal_*`/`test_trace_telemetry.py` files are the sibling telemetry wave's and were NOT staged).
