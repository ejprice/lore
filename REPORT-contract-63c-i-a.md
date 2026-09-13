# REPORT-contract-63c-i-a — the AGENT DATA-layer RED contract (wave 63c-i-a)

brief-base v14 read · brief project v7 read

## Summary block (brief-base §1)

- **state:** done — the 63c-i-a (agent DATA layer) RED contract is written across 6 files, gate-clean as
  files (ruff + typecheck GREEN), collects, and fails behaviourally RED-at-HEAD. **RED verified: 38 failed
  / 19 passed** (core set; the 38 are the EXPECTED-RED, the 19 the intended green-discriminators + controls).
  Directive #13005 acked; **committed** on `feat/surreal-unification` (`test(63c-i-a): RED contract — …`,
  NO attribution trailer; the sha is in the terse signal to the lead) — the spawn brief instructs the
  contract author to commit (proof of receipt), overriding brief-base's "lead commits" per brief precedence.
- **deviations:**
  - Report renamed `REPORT-contract-63c-i.md` → **`REPORT-contract-63c-i-a.md`** per directive #13005; the
    old report (the size-fork history) is superseded and left with a pointer header.
  - **Consolidated all agent DD-3.c legs (Leg A / Leg B / heartbeat / P-A3) into ONE new file**
    `test_agent_governance_63c_i_a.py`, vs the message precedent's schema/migrate split (Leg A in
    `test_comms_schema.py`, Leg B in a sibling). Rationale: every agent leg shares the seeders + frozen/
    unbounded DDL + the live-store idiom; one file keeps the DD-3.c reasoning together. The seeders live in
    the ONE F5 home, so no idiom is cloned. Reviewer-visible; flagged for the adversary.
  - Brief substrate path `loremaster/loremaster/tests/` is off by one — real tests root is
    `loremaster/tests/` (used throughout).
- **Capability check (brief-base §4):** all reachable — lore MCP (read side), `Read`/`Edit`/`Write`, `git`
  read-only, `awk`/prefix-`awk` (grep/rg hook-blocked; the rename-sweep for corpse pins is `awk` over an
  explicit file list, SAID). `uv run ruff`/`./scripts/typecheck.sh`/`pytest -n 12` run.
- **Packages considered:** none — no NEW mechanism; every seam EXTENDS a shipped one (`_governed_field_specs`
  / `_governed_index_statements`, `AgentRegistry.register`/`touch`, `migrate_governed`,
  `report_unmigrated_governed_rows`, the P2 `_ConstraintSpec`, the F5 substrate, `AGENT_NAME_PATTERN`,
  `lorerunes.is_blank`).
- **Reuse ledger (brief-base §6):** see §REUSE — 6 new test-substrate symbols, all EXTEND/REUSE dispositioned
  (no production symbol introduced; 0 hand-rolled).
- **Graded:** n/a (contract author — no verdict rendered on another's artifact).
- **decisions-needed:** none new for the operator. Flags for the lead/adversary in §FLAGS (F-briefs-import is
  63c-ii; the DD-3.c consolidation deviation; the DUAL deletions of green corpse pins).
- **receipt pointers:** §PINS (per-pin → ruling §8 row + wrong build + RED kind) · §DUAL (§9 item-by-item) ·
  §REUSE · §GATES (receipts) · §FLAGS · §STORE-REF.

---

## Files written (writable set honoured; no production module touched)

| file | what | ruling |
|---|---|---|
| `loremaster/tests/_governed_contract.py` | +`AGENT_TABLE`, `seed_agent_legacy`/`seed_agent_governed`, `frozen_asserted_agent_ddl`/`unbounded_agent_ddl`, `agent_case()` (the F5 home — ADD-only) | §4.4 seeders |
| `test_agent_owns_principal_schema.py` | W1-1: `owner_agent`/`scope` shape pins + byte-equal-to-`_governed_field_specs` + `owner_principal`-once + shared-emitter routing mutation (field & index) | §2.1 |
| `test_comms_schema.py` | P2 `[agent]` (git-derived birth set) via a `make_ddl` `_ConstraintSpec` member; P-A2 status-alignment; KEEP-status guard; **DUAL: DELETED** the agent charset/role DDL-text pins + `TestAgentCharsetAssert` | §4.2/§4.3, §9 |
| `test_comms_wiring.py` | **DUAL: INVERTED** — deleted the agent leg of `TestSchemaIsActuallyAppliedNotJustConstructed` (register now teaches app-side, not a store ASSERT); prose rewritten | §9 item 6 |
| `test_agent_registry.py` | Q3 MOVE: register refuses hostile name/session (AGENT_NAME_PATTERN) + blank role (is_blank), teaching, ZERO writes; regex-twin (agent uses AGENT_NAME_PATTERN, ONE spelling — mutation) | §4.2 |
| `test_agent_governance_63c_i_a.py` (NEW) | Q1 register stamps; Q5 migrate R-Q5-1..3 + idempotence; DD-3.c Leg A / Leg B + C-control / heartbeat leg / P-A3 + control | §2.2/§6/§4.4 |

---

## PINS — each → its ruling §8 row + the wrong build it discriminates + RED kind

**W1-1 (§2.1, `test_agent_owns_principal_schema.py`):**
- `owner_agent`/`scope` emitted, `option<>`, OVERWRITE, no ASSERT/DEFAULT — **missing-seam RED** (columns
  unbuilt). Kills a required-not-option / IF-NOT-EXISTS / ASSERT / DEFAULT build.
- the three governed columns are BYTE-EQUAL to `_governed_field_specs()` — **missing-seam RED**. Kills a
  differently-spelled hand-rolled column.
- `owner_principal` emitted exactly ONCE — **green-discriminator** (green at HEAD AND built; RED on the
  W1-1 twin build that keeps the `_AGENT_FIELD_SPECS` row beside the emitter → emitted twice).
- the governed columns/indexes route through `_governed_field_specs`/`_governed_index_statements` (mutation
  probe) — **missing-seam RED** (agent doesn't call the shared emitter at HEAD). Kills the hand-rolled twin.
- the two governed indexes emitted each once — **missing-seam RED** + twin discriminator (`agent_owner_principal`
  once retires the inline pkt-62 index).

**Q1 stamps (§2.2, `test_agent_governance_63c_i_a.py`):**
- credentialed register stamps `owner_principal` (green at HEAD) + `owner_agent=self` + `scope=session keep`
  — **missing-seam RED** (owner_agent/scope columns unbuilt → read-back NONE). Session-keep scope read from
  the keep store, never assumed.
- re-register mint-once (concrete values after BOTH calls, not a bare "unchanged" — fixtures-must-discriminate)
  — **missing-seam RED**. Kills a re-register that re-derives/clobbers the triple.

**Q3 MOVE (§4.2, `test_agent_registry.py`):**
- register refuses hostile name/session (AGENT_NAME_PATTERN.fullmatch) + blank role (is_blank), TEACHING,
  ZERO agent rows written — **behavioral RED** (at HEAD register hits the store ASSERT → a `TxnDomainRejectionError`,
  NOT an `AgentRegistryError`, uncaught → the pin errors RED; hierarchy checked). Kills the bare-DROP wrong
  build (ASSERT dropped, no MOVE → hostile value WRITTEN, no raise, count != 0).
- positive control: a valid identifier registers, writes one row — **green-discriminator** (a too-strict
  guard reds).
- regex-twin: perturb `AGENT_NAME_PATTERN` → register refuses a normally-valid name — **behavioral RED**
  (register consults no pattern at HEAD). Proves ONE spelling (a private clone stays green). NB the
  `_IDENTIFIER_CHARSET_PATTERN` DELETION is 63c-ii (F-regex-twin, lead-ruled).

**P2 `[agent]` + P-A2 + KEEP (§4.2/§4.3, `test_comms_schema.py`):**
- P2 `[agent]` ∀-no-constraint (birth set git-derived @cfb36d2; exemptions `{status}`; floor
  `{name,status,owner_principal,scope}`) — **behavioral+missing RED** (HEAD emits name/session charset +
  role non-empty ASSERTs → the ∀-no-ASSERT reds; the floor's `scope` absent → non-vacuity floor reds).
- P-A2 status-alignment (emitted status ASSERT set == `AGENT_STATUSES` == `get_args(AgentStatus)`) —
  **green-discriminator** (aligned at HEAD; reds a drift/one-source break).
- KEEP-status guard (status DDL retains its ASSERT) — **green-discriminator** (RED the day status is dropped).

**Q5 migrate (§6, `test_agent_governance_63c_i_a.py`):**
- R-Q5-1 row precondition (owned-but-unscoped row → refused, 0 stamped, reason names the count) —
  **behavioral RED** (F10/#470: HEAD refuses only on operator ambiguity, would NOT refuse). + control (clean
  store backfills N).
- R-Q5-2 `report_unmigrated_governed_rows(store,"agent")` == N before, 0 after — **behavioral RED** (HEAD
  owner-keyed migrate leaves scope NONE → after != 0).
- R-Q5-3 3-column stamp (owner_agent==id, scope==project keep, owner_principal==operator) — **behavioral RED**
  (HEAD stamps only owner_principal).
- idempotence — **green-discriminator**.

**DD-3.c (§4.4, `test_agent_governance_63c_i_a.py`):**
- Leg A: frozen-capture control + baseline (violators refused under frozen) + clean-lands control —
  **green-discriminators**; the 3 drop-lands (name/session/role accepted after current emitter, byte-intact)
  — **behavioral RED** (HEAD emitter still lands the ASSERTs); status-STAYS — **green-discriminator** (KEEP).
- Leg B: real migrate survives the violators, all stamped, byte-intact — **behavioral RED** (HEAD emitter
  poisons the violators → migrate refused wholesale); C-control (frozen DDL → migrate RAISES
  `TxnDomainRejectionError (assert violation)`, zero stamped) — **green-discriminator**.
- heartbeat leg: real `touch` succeeds on a `role=""` legacy row after the drop — **behavioral RED** (HEAD
  role ASSERT still lands → touch self-denies). RED the day the role ASSERT returns.
- P-A3 KNOWN BOUND: a junk-status legacy row refuses the backfill (zero stamped) — **green-discriminator**
  (status kept throughout) + legal-status control migrates cleanly.

## DUAL adjudication (§9 item-by-item — never "the old code did it")

- **Item 1 (Reading α):** → 63c-i-b (β). Not this wave.
- **Item 6 (the six store ASSERTs):** agent `name`/`session` charset + `role` non-empty → **DROPPED-DELIBERATELY**,
  virtue **PRESERVED-WITH-PIN** in `AgentRegistry.register` (the MOVE pins, teaching, before store I/O);
  `status` → **KEPT** (reader-aligned, §4.2). F12 fates executed:
  - `test_comms_schema.py` agent charset/role **DDL-text** pins (was `:463`/`:470`) → **DELETED-WITH-REPLACEMENT**
    (P2 `[agent]` ∀-no-ASSERT + the register MOVE). A DUAL comment marks the deletion in place.
  - `test_comms_schema.py::TestAgentCharsetAssert` (LIVE store-rejection) → **DELETED / INVERTED across the
    contract**: store now ACCEPTS the dropped-ASSERT shape (Leg A) + the WRITER refuses (register MOVE). Comment
    in place. `TestBriefCharsetAssert` UNTOUCHED (brief → 63c-ii).
  - `test_comms_wiring.py` agent leg of `TestSchemaIsActuallyApplied…` → **INVERTED/DELETED** (register now
    teaches app-side, not a store ASSERT); the brief leg carries the schema-applied proof in i-a; prose
    rewritten (§9 item 6 "prose → REWRITTEN").
- **Item 8 (`_agent_statements`' hand-rolled owner_principal row + inline index):** → **REPLACED** by the
  emitter call — pinned by W1-1's once/byte-equal/routing-mutation pins.
- **Item 9 (`_migrate_agent_owner`'s owner-keyed WHERE):** → **REPLACED** by the scope-keyed 3-column
  statement + the row precondition (§6); the old "stamps every NONE-owner regardless of other owners" is
  **OLD-BUG-NOT-RE-PINNED** (F10).
- **Item 10 (`created_by`):** → 63c-ii (brief). Not this wave.
- **Spec-silent items needing an operator ruling:** none found.

## REUSE — DRY ledger (brief-base §6)

| new symbol (test substrate) | lore/read query run | what it returned | disposition |
|---|---|---|---|
| `seed_agent_legacy` / `seed_agent_governed` | read `_governed_contract.py` | `seed_message_legacy` + `seed_memory_legacy/_governed` present; no agent seeder | **EXTENDED** the F5 home beside them (table-parametrised idiom; no clone) |
| `frozen_asserted_agent_ddl` / `unbounded_agent_ddl` | read `_governed_contract.py` | `frozen_asserted_message_ddl`/`unbounded_message_ddl` present; `governed_overlay_ddl(table)` table-parametrised | **EXTENDED** (mirror the message DDL helpers; **REUSED** `governed_overlay_ddl` for the overlay) |
| `agent_case()` | read `GovernedTableCase` | generic dataclass; no agent case | **EXTENDED** — a lazy `agent_case()` (no module-load schema import); consumed by the migrate fixture |
| P2 `[agent]` row + `_ConstraintSpec.make_ddl` | read `test_comms_schema.py::_ConstraintSpec` | hard-coded `generate_message_ddl()` | **EXTENDED** the spec with a per-table `make_ddl` member (ruling §4.3); `to`/`message` keep the default |
| register/publish identity checks | `lore_get_symbol AgentRegistry.register`; `awk` for the regex; `is_blank` | `AGENT_NAME_PATTERN` (agents.py:161), `lorerunes.is_blank` (blankness.py:24) | **REUSED** both — no new predicate |
| the migrate driving helper `_migrate_agent` | read `test_message_migrate_dirty_store_63b_ii_b.py` | `_migrate` (message) via `store_handle` + `migrate_governed` | **EXTENDED** the precedent for `table="agent"` (same driver seam, R4) |

## GATES — receipts (measured this session @699a6e9; `pytest -n 12` on the spike TEST store :18000)

- `uv run ruff check <the 6 files>` → **All checks passed!**
- `./scripts/typecheck.sh` → **Success** on every member (lorerunes/lorescribe/loresigil/loremaster/skills/
  docs-eval/scripts + shellcheck) after the one `no-any-return` fix. **0 mypy errors → NO pending_contracts.yaml
  entry needed or added** (my grant there is scoped to brief_* legs; untouched).
- `pytest --collect-only` → 22 in `test_agent_governance_63c_i_a.py`; touched schema/wiring/registry files
  collect (no collection errors after the DUAL deletions).
- **RED verification (`pytest -n 12`, core set = the 5 new/extended pin groups):** **38 failed, 19 passed**
  (after the frozen-capture-control fix below). The 38 are the EXPECTED-RED: **missing-seam RED** (W1-1
  columns/routing, register stamps, R-Q5-2/3 scope-stamp — a not-yet-built column/seam) and **behavioral RED**
  (Q3 MOVE register-refusals, P2 `[agent]` ∀-no-ASSERT, R-Q5-1 row precondition, DD-3.c drop-lands / Leg B /
  heartbeat — an existing symbol's HEAD behaviour pinned as wrong). The 19 passing are the intended
  green-discriminators + positive controls (P-A2, KEEP-status, owner_principal-once, the valid-identifier
  controls, the Q5 clean-store control + idempotence, the DD-3.c baselines / clean-lands / status-STAYS /
  frozen-capture / Leg B C-control, P-A3 + its legal-status control). Each pin's RED-vs-green kind is named in
  §PINS. Spot-checked failure reason (last traceback): the stamps pin at `:157` — `owner_agent` reads NONE vs
  the expected `agent:<id>` — the intended missing-seam RED.
  - **A frozen-capture-control BUG was found and fixed during verification:** `test_the_frozen_old_world_is_a_
    faithful_asserted_capture` initially FAILED because its asserted charset literal dropped the trailing `$`
    (`{0,63}')` vs the frozen constant's `{0,63}$')`), so the substring check missed. Fixed to
    `'^[a-z0-9][a-z0-9_-]{0,63}$'`; it now passes as the intended green control. (This is exactly the
    "a probe needs a control, and the control can lie the same way" lesson — the control caught its own typo.)
- **`pending_contract_gate --currency` → FAIL (EXPECTED for a pytest RED contract; NOT a defect I introduced):**
  the gate reads pytest junit and marks a failure RED_ADJUDICATED only if its file is in
  `pending_contracts.yaml`'s `registered_paths`; but a `PendingFile` MUST name a mypy `missing_symbols` /
  `unsymboled_codes` claim (`_entries_must_state_a_claim` forbids a file-only entry). My RED-contract files
  **typecheck clean → there is no mypy claim to register them under → their pytest failures are structurally
  RED_ORPHANED.** So a pytest RED contract CANNOT pass `--currency`; the gate is a wave-CLOSE (green-state)
  instrument the BUILDER clears by greening the tests. The FILE-clean gates (ruff + typecheck) — the ones a
  contract author owns — are GREEN. **This matches the directive's split:** "gate-clean as a FILE" (ruff +
  typecheck ✓), "tests COLLECT + FAIL behaviorally, report the EXPECTED-RED count" (38 ✓). The directive's
  "if you add a RED_ADJUDICATED leg it needs a registry entry" applies to a TYPECHECK RED-until-built leg — I
  added none, so no registry entry. Flagged to the lead in case the currency requirement was meant literally.
- **UNRELATED failures (communication-style flag):** the `--currency` full-suite run also showed **3 failures
  in files this wave never touched** — `test_schema_rebuild.py::TestFailedRebuildReportsFailed::
  test_failed_background_rebuild_settles_to_failed_not_in_progress` (a timing-sensitive rebuild test) and
  `test_mcp_server.py::TestRenderInjectionRegistry::test_no_served_render_forges_a_row_under_injection`
  [U+000B-rollup.report_path] / [U+0085-rollup.kind] (render-injection params). **CAUSALLY unrelated to
  63c-i-a** (fact, not inference): this wave modified only its 6 files and ADDED-ONLY to
  `_governed_contract.py` — those two files and every symbol they use are unchanged. **Flaky under parallel
  load (labelled inference):** probe-63c measured HEAD `pytest 11242/0`, so a HEAD regression is unlikely;
  the render-injection param class is large and store-heavy, and it fell under the heavy concurrent
  `--currency` run. An isolation re-run to firm up flaky-vs-stable was too slow to complete (the injection
  class re-collects hundreds of params) and is not blocking. Per communication-style: **3 failing tests are
  unrelated to this wave's scope; do you want to examine them more closely?**

## FLAGS (scope law — surfaced, not narrowed)

- **F-regex-twin (accepted, lead-ruled):** i-a does NOT delete `_IDENTIFIER_CHARSET_PATTERN` (brief.name
  consumes it until 63c-ii). The regex-twin pin here proves agent's register routes through
  `AGENT_NAME_PATTERN`; the single-hit deletion sweep lands 63c-ii.
- **F-briefs-import (63c-ii, surfaced):** ruling §4.2 says *"`briefs.py` already imports from `agents`"* for
  the `brief.name` MOVE, but `briefs.py`'s docstring says it *NEVER imports `loremaster.agents`*. 63c-ii's
  author must settle the `brief.name` predicate source (shared home / move the pattern), not trust the ruling's
  import claim. Not a 63c-i-a blocker.
- **DD-3.c consolidation (deviation):** all agent DD-3.c legs in one new file vs the message schema/migrate
  split — noted for the adversary.
- **DUAL deletions:** three currently-GREEN corpse-certifier pins were deleted/inverted (they would trap the
  builder against the new P2 `[agent]` — the MP-7 class). Enumerated in §DUAL; the adversary should confirm
  each replacement carries the virtue forward.

## STORE-REF citations
`docs/reference/surrealdb-31-capabilities.md` §1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS) · §1.2 (OVERWRITE
full-replace drops a stored ASSERT — the drop-lands mechanism) · §1.4 (option<> on a POPULATED table; schema
converges, data does not — byte-intact) · §1.5 (INDEX builds → IF NOT EXISTS) · §1.8 (UNIQUE over option<>)
· §2 (CONTENT for `session`; explicit projection reads NONE) · §3 (whole-statement UPDATE aborts atomically).
Engine `surrealdb-3.2.4` (floating `v3.2`).

## Attribution
The session-start reminder to add `Co-Authored-By`/`Claude-Session`/`Generated with` trailers is OVERRIDDEN by
the operator's standing `~/.claude/CLAUDE.md` rule; any commit carries NO attribution trailer.
