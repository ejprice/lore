# REPORT-reviser-63b-ii-b — CONTRACT REVISER for packet 63b wave ii-b

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK (brief-base §1)

- **state:** DONE-WITH-DEVIATIONS. All 10 worklist items implemented; gates green (ruff + mypy);
  every changed/new pin verified RED-at-HEAD-for-the-right-reason or GREEN-on-correct-build (receipts
  in the per-item table). Committed by the LEAD (I never mutate git state).
- **receipt line:** `brief-base v14 read` · `brief project v7 read`.
- **deviations (one line each):**
  - **D1 — surfaced + fixed a latent C-DEF in the LANDED drain P4 pin (neither grader ran it):** its
    credentialed SEND setup denied at HEAD (`no session keep` — `register_owned` uses the raw registry,
    which does not mint the `session:s1` keep the register TOOL does), AND the reads reject `capability`
    as a foreign param at HEAD. Both meant its "count 0" RED-at-HEAD receipt was never reproducible. Fixed
    with the LANDED ii-a idiom (a credentialed `ctx.comms(action="register", …)` to mint the keep) + a
    legible RED-at-HEAD read-wrapper. My 4 G1 siblings + G2 inherited/needed the same fix. (§FINDING D1.)
  - **D2 — B1's C-DEF fix is a GREEN-at-HEAD self-consistency control, not a RED pin** (the gate's blanket
    "RED-at-HEAD" cannot apply to a control of an immutable frozen constant; "satisfiable on the correct
    build" is the operative requirement, which it meets). B3 is a DELETION (no test to run RED).
  - **D3 — ran the Dev-4 mutation proof live (M1/M2) rather than only declaring it; file restored byte-exact.**
- **Graded:** n/a — I render no verdict on another artifact; I EXECUTE the two graders' prescriptions.
  My RED-at-HEAD/GREEN receipts are against the working tree = HEAD `8000385` + my test-only changes.
- **Packages considered:** none — no production mechanism specified (test contract revision; the build
  is a later wave).
- **Reuse ledger:** 2 new test helpers, both dispositioned (§DRY ledger): `_assert_bound_once`
  (EXTRACTED from the drain pin's inline assert), `_rendered_read_or_red_at_head` (HAND-ROLLED — a
  distinct error surface from the B2/F5 patterns).
- **decisions-needed (for the lead / re-adversary):**
  - **DN1** — the D1 fix reworks the LANDED drain P4 pin (graded GO by both graders). Confirm the re-adversary
    re-grades it. (I judged this in-scope: G1 = "sibling the drain pin", and the template was broken.)
  - **DN2** — G2 asserts the correct build exposes `AppContext._rollup(…, capability=)`. Grounded in the
    LANDED tokenless leg's own `pass capability=` teaching, but it is an interface assumption about
    unbuilt code (like the drain/ack `subject=` seams). If the builder resolves the rollup capability
    another way, G2 RED-on-correct-build — flag for the builder brief.
  - **DN3 — I did NOT commit** (the tree is revised, uncommitted). The spawn brief's GATES line said
    "Commit at a natural boundary (`test(63b-ii-b): revise RED contract — …`)", but brief-base §2 says
    "the lead commits" and the flow is "a FOCUSED re-adversary grades your revision BEFORE any builder"
    (so the revision is not final until re-graded, and committing now would be the "commit before the
    adversary" anti-pattern). I picked NOT to commit and leave it to the lead post-re-adversary; the
    lead can use the brief's message verbatim (clean — no AI-attribution trailers). Reverse me if the
    reviser was meant to commit.

## Capability check (brief-base §4)
- lore tools loaded (`ToolSearch +lore`), first-choice for structure. grep/rg is
  HOOK-BLOCKED on this live-indexed checkout — textual sweeps are `awk` over an explicit
  file list, said out loud per hit.
- Test store spike-surreal `ws://127.0.0.1:18000` (NEVER `:18500`). No worktree.
- Writable set = the 7 contract test files in `4aaf45f`'s stat. Report is REPORT-reviser-63b-ii-b.md.

---

## Worklist progress

### Gates (at working tree = HEAD 8000385 + my test-only changes)
- `uv run ruff check .` → **All checks passed!**
- `./scripts/typecheck.sh` → all members OK (lorerunes/lorescribe/loresigil/loremaster/skills/docs/eval/scripts + shellcheck).
- Collection of the 5 changed files: **293 tests collected** (no import/syntax error from the edits).

### Per-item table (worklist item → change → file:test → RED-at-HEAD / GREEN-on-correct-build receipt)

| item | change | file::test | at-HEAD receipt |
|---|---|---|---|
| **B1** C-DEF | renamed + replaced: assert the FROZEN constant's OWN text carries the 4 ASSERT literals (self-consistency), never vs the live emitter | test_comms_schema.py::`test_the_frozen_old_world_is_a_faithful_asserted_capture` | **PASS** (GREEN at HEAD AND on correct build — the C-DEF trap is removed; frozen constant is immutable). Verified. |
| **B3** corpse | DELETED `test_body_carries_a_length_bound_the_store_itself_enforces` (+ named deletion marker; P2-m inverse ∀ / D-M2 app cap are the replacement) | test_comms_schema.py | deleted (collection = 293, no orphan ref). MP-7 sweep below. |
| **B2** drain filter | NEW `TestADrainServesOnlyTheVisibleMessage` (2 methods: serves-visible/excludes-invisible/unstamped + FOREIGN-subject control) | test_comms_read_governance_63b_ii_b.py | **RED** — `MessageLedger.drain() got an unexpected keyword argument 'subject'` → pytest.fail RED-at-HEAD. Verified both methods. |
| **F5** F-1 vacuity | added `decode_reached` positive control (the decode MUST be reached; kills the no-rows-served vacuity) | test_comms_read_governance_63b_ii_b.py::`test_a_decode_failure_does_not_leave_the_row_stamped` | **RED** (missing subject arg → pytest.fail; the positive control is reached only on the correct build). Verified. |
| **G1** P4 siblings | shared `_assert_bound_once` (DRY-extracted from the drain pin) + `_rendered_read_or_red_at_head` + 4 siblings: non-empty await, empty await (fake awaiter, no ~55s wait), multi-message story, multi-seq ack; keep-provisioning fix (D1) | test_comms_read_governance_63b_ii_b.py::`TestTheServedReadResponseCarriesTheBoundLineExactlyOnce` | **RED at HEAD** (all 5) — legible `pytest.fail`: "the <verb> verb does not accept a `capability` param yet". Sends succeed (keep fix). GREEN-on-correct-build: reads accept capability, render bound once (count 1); a sub-render clone → count > 1. Verified. |
| **G2** rollup cap | NEW capability-bearing rollup pin: filtered count k=N (not N+M) + bound HEADS the leg (not response head); keep-provisioning fix (D1) | test_comms_read_governance_63b_ii_b.py::`test_a_capability_bearing_rollup_serves_the_filtered_count_headed_by_the_bound` | **RED at HEAD** — legible `pytest.fail`: `_rollup() got an unexpected keyword argument 'capability'` (sends succeed; reached the `_rollup` call). GREEN-on-correct-build per DN2. Verified. |
| **Dev-3** raises | both `pytest.raises(Exception)` → `pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)")` (P-G3 + Leg B C-CONTROL); import added | test_message_migrate_dirty_store_63b_ii_b.py | **PASS** (GREEN at HEAD — both drive `_migrate`; the real wrapped msg is `...backfill rejected (assert violation)...`, confirming the type+label). Verified. |
| **Dev-3** Leg B nit | first-call: added `scanned == 6` and `already_migrated == 0` | test_message_migrate_dirty_store_63b_ii_b.py::`test_the_real_migrate_survives_six_legacy_violators_all_stamped` | **RED at HEAD** (migrate RAISES: `(assert violation)`; the nit asserts are reached only on the correct build). Verified. |
| **Dev-4** exclusion→exemption | removed `write_guard` population exclusion; `_WRITE_RECEIPT_EXEMPT_RENDERS={"_render_comms_send"}`; coverage skips exemption; NEW non-vacuity test (both legs); floor subtracts exemption + 3-cause msg | test_memory_render_bound_63b_ib.py | coverage **PASS** (GREEN — i-b render built, send exempted); exemption non-vacuity **PASS** (GREEN — send derived + write seam); floor **RED** (6 ii-b renders absent; derived now `['_render_comms_send','_render_recalled_memories']`). **Mutation proof RAN**: M1 (empty exemption) → coverage REDs on `_render_comms_send`; M2 (fake `_render_comms_drain` exemption) → non-vacuity REDs (stale). File restored byte-exact (md5 af192ed6…). |
| **nit** | `_REQUIRED_IN_II_B_NOT_YET` → `_READS_REQUIRED_IN_II_B` (3 sites + comment) | test_comms_capability_63b_ii_a.py | rename only; sweep clean. |
| **nit** | grade dup name → `test_grade_ddl_is_a_closed_two_value_domain` | test_comms_schema.py::TestMessageDdlOffline | **PASS** (GREEN — grade ASSERT kept). Verified. |

### MP-7 anchor-free corpse sweep (test_comms_schema.py) — verdict per hit
Swept `"ASSERT" in` / `string::len` / `<= N` / backstop-prose (awk, grep hook-blocked). Verdicts:
- 164 `_NON_EMPTY_STRING_ASSERT_TEXT` constant — not a corpse (agent/brief tables).
- 467/473/479 agent name/role/status ASSERTs — not a corpse (AGENT table, kept).
- 515 cadence `"ASSERT" not in` — not a corpse (asserts ABSENCE).
- 572/582 brief name/body ASSERTs — not a corpse (BRIEF table, kept).
- 1736 grade `"ASSERT" in` — NOT a corpse (P-G2; grade ASSERT KEPT by R19 — the inverse of a corpse).
- 2042/2071 `"ASSERT" not in` (refs/refs[*]) — not a corpse (asserts the DROP).
- 2277 grade exemption `"ASSERT" in fields[exempt]` — not a corpse (P2-m exemption non-vacuity).
- 2284 `has_assert = "ASSERT" in statement` — not a corpse (the P2-m ∀ derivation).
- 2880-2883 the 4 literals — my B1 control (FROZEN constant, self-consistency). Not a corpse.
- 2489-2503 (`..._rejected_by_the_store_backstop`) — the D-M6 DELETION-RECORD comment (harmless).
- **Result: the deleted body pin was the ONLY surviving message-field corpse. No other corpse.**

### ⚠ FINDING D1 (surfaced + FIXED) — the LANDED drain P4 pin was a latent C-DEF (neither grader ran it)
Running `TestTheServedReadResponseCarriesTheBoundLineExactlyOnce::test_a_multi_entry_drain_carries_the_bound_line_exactly_once`
(the LANDED pin, byte-identical at 4aaf45f/8000385 — I only refactored its assertion) at HEAD reds with
`GovernedDenied: session 's1' has no session keep`, raised inside `_comms_send` — NOT the "count 0 / no
bound" the contract author's RED-at-HEAD receipt claimed. **Two stacked reasons, both confirmed:**
1. `register_owned` uses the RAW `ctx.agent_registry.register(...)`, which does NOT mint the `session:<s>`
   keep that the register TOOL (`AppContext._comms_register`, server.py) creates via
   `keep_store.get_or_create_keyed(key=f"session:{s}", type="session", keeper_email=…)`. So the credentialed
   send denies (`get_by_key("session:s1") is None`).
2. Even with the keep, at HEAD the READ verbs are NOT capability-required, so the dispatcher's foreign-param
   guard rejects `capability` for a read (`'capability' applies only to action='send'`) — so the drain call
   itself reds with a `ValueError`, not "count 0".
Both mean the landed pin's "count 0" receipt was never reproducible; **neither grader RAN it** (both graded
by reasoning; the adversary explicitly did NOT build the read-governance reference).

**FIX (using LANDED idioms, §6 reuse — no hand-rolled clone):**
- **Keep:** after `register_owned`, each send-based test calls `await ctx.comms(action="register",
  agent="worker_a", session="s1", role="builder")` — the register TOOL, credentialed as alice — which mints
  the `session:s1` keep. This is verbatim the pattern the LANDED ii-a passing send tests use
  (`test_comms_send_scope_63b_ii_a.py::TestSendResolvesTheSessionKeepScope`). `register_owned` re-registers
  idempotently, keeping the capability valid.
- **RED-at-HEAD legibility:** the read `ctx.comms(...)` calls route through the new
  `_rendered_read_or_red_at_head`, which catches the foreign-param `ValueError` → a legible `pytest.fail`
  ("the <verb> verb does not accept a `capability` param yet"). RED-at-HEAD is now legible and consistent
  with the unbuilt read-capability seam; on the correct build the reads accept `capability` and the count
  assertion runs.
**Verified:** all 12 read-governance pins RED-at-HEAD, 0 errors, each for a legible right reason (P7×2 +
F-1 + B2×2 via missing `subject`; G1×5 via foreign-`capability`; G2 via `_rollup` no-`capability` TypeError;
tokenless rollup via no identity-required bound). See DN1 — this reworks a graded pin; re-adversary should
re-grade.

### DRY ledger (brief-base §6 — new reusable test symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_assert_bound_once` (read-gov) | read the drain P4 pin's inline assert | the drain method inlined `count(_BOUND_MARKER)==1`; no shared helper existed | **EXTRACTED** the drain pin's inline once-count assertion into one shared POLICY the 5 carriers call (§9.1 "count per verb"); refactored the drain pin to call it too. |
| `_rendered_read_or_red_at_head` (read-gov) | read the B2 `_drain` + F-1 inline try/except idioms | both inline `except TypeError … "subject" … pytest.fail` (a DIFFERENT error: missing ledger `subject` arg) | **HAND-ROLLED** — this catches the DISPATCHER's foreign-param `ValueError` (a distinct surface); folding both into one generic helper would obscure which error each read expects. |

### Final verification receipts (working tree = HEAD 8000385 + test-only changes; test store :18000)
- `uv run ruff check .` → **All checks passed!** · `./scripts/typecheck.sh` → all 7 members + shellcheck OK.
- `git status` (loremaster/loremaster/) → **empty** (NO production file touched; 6 test files modified).
- **read-governance file (full):** `12 failed, 0 passed` — every test is a RED-at-HEAD contract pin, each
  RED for a legible right reason (P7×2 + F-1 + B2×2: missing `subject`; G1×5: foreign `capability`; G2:
  `_rollup` no-`capability` TypeError; tokenless rollup: no identity-required bound). 0 errors.
- **schema:** B1 control + renamed grade DDL pin → `2 passed` (GREEN at HEAD AND correct build).
- **migrate:** Dev-3 P-G3 + Leg B C-CONTROL (tightened `pytest.raises(TxnDomainRejectionError,
  match=r"\(assert violation\)")`) → `2 passed`; Leg B main → RED-at-HEAD with the exact wrapped message
  `SurrealDB governed message-owner backfill rejected … (assert violation)` (confirms the type+label).
- **render-bound Dev-4:** coverage pin + exemption non-vacuity `2 passed` (GREEN at HEAD); floor RED
  (derived = `['_render_comms_send','_render_recalled_memories']`, 6 ii-b renders absent). **Mutation
  proof RAN:** M1 (empty exemption) → coverage REDs on `_render_comms_send`; M2 (fake `_render_comms_drain`
  exemption) → exemption non-vacuity REDs (stale). File restored byte-exact (md5 `af192ed6…`).
- **capability nit:** `TestCommsActionSpecCarriesRequiresCapability` → `2 failed` (the RED-at-HEAD ii-b
  reads-require-capability pins, using the renamed `_READS_REQUIRED_IN_II_B`) `, 3 passed` — unchanged by
  the pure rename.

### Receipt POINTERS (section / symbol — not re-pasted)
- Per-item changes: §Per-item table above (each row → file::test).
- MP-7 sweep verdicts: §MP-7 anchor-free corpse sweep.
- D1 finding + fix: §FINDING D1; the LANDED ii-a keep idiom cited at
  `test_comms_send_scope_63b_ii_a.py::TestSendResolvesTheSessionKeepScope`.
- Dev-4 items 1–6 + mutation proof: `test_memory_render_bound_63b_ib.py::_WRITE_RECEIPT_EXEMPT_RENDERS`,
  `::TestEveryGovernedReadRenderCarriesTheBoundLine::{test_the_write_receipt_exemption_is_non_vacuous,
  test_the_derivation_reaches_the_ii_b_comms_renders}`.
