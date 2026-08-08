# REPORT-builder-05aiii — GREEN build for packet 05a-iii (comms READS + FLEET honesty)

brief-base v10 read

## Summary block
- **State:** DONE (production). ESC-1 ruled **Option A** (lead, 2026-08-08) — `messages.py` granted ADD-ONLY; the two reads + `StoredMessage` are built and story A2/A3/A5 + rollup B1/B4 are now GREEN. The ONLY remaining whole-suite RED are the 4 companion-pin adjudications (ESC 2/3/4/5) the lead routed to a fresh contract-fix agent — I left those 4 test files UNTOUCHED (builder≠author). All 6 load-bearing pins mutation-proven (D5/D6/D7/D8 + A5/B4).
- **Deviations:** (1) `_render_comms_fleet`/`_render_comms_fleet_row` gained a `status_age_seconds`/`age_declaration` opt-in (#304 render; default OFF ⇒ pre-#304 callers byte-unchanged). (2) `messages.py` add-only (ruled scope grant — `StoredMessage`, `messages_for_task`, `message_activity_since`, `MessageActivityWindow`, `_row_to_stored_message`, `_extract_group_count`); HARD FENCE respected — no touch to `drain`/`InboxEntry`/drain SELECT/`pending_traffic`/`awaiting_answer` (verified: `test_message_ledger.py` green). (3) `comms_cli.py` secret fixes (unwrap→`resolve_config_value`, env-read→`--config`) kept per ruling.
- **Packages considered:** none — no new mechanism. comms_cli reuses stdlib `argparse` (already the stub's idiom) + the shared `LoreConfig.model_validate`/`SurrealConfig` resolver + the existing ledgers (`AgentRegistry`/`MessageLedger.pending_traffic`/`BriefLedger`); story/rollup/#304 reuse the shipped render seam (`render_fenced`/`render_attributed`/`render_line`/`render_compose`), `_render_age`, and the agent-DDL `_define_field`. ONE IMPLEMENTATION throughout — no second copy of any of these.
- **Graded:** built against `4dc2949` (HEAD-at-report `4dc2949`, SAME). Store live-read: spike-surreal `:18000` (3.2.1); `:18500` never touched.
- **Decisions RULED by the lead (2026-08-08):** ESC-1 = **Option A** (DONE — messages.py add-only, story/rollup green). ESC-2/3/4/5 = routed to a fresh contract-fix agent (4 companion-pin adjudications); I leave those 4 test files UNTOUCHED. My 2 comms_cli secret fixes KEPT.
- **⚠ ESC-6 (NEW — surfaced by building ESC-1; needs a boundary call).** The granted `MessageLedger.message_activity_since` method the rollup dispatcher now calls is NOT mirrored on the test DOUBLE `FakeMessageLedger` (`loremaster/tests/_message_fakes.py`) → **5 `test_comms_footer.py::[asyncio-rollup]` tests CRASH** with `AttributeError`. The test's OWN failure message names this as finding **#322 (DOUBLE-face parity)** and instructs "add the method to the fake — a CORRECT build turns into an AttributeError." This is a MECHANICAL oracle-mirror (the fake's own docstring: *"every method's public surface matches the real ledger exactly"*), NOT a trust/security adjudication — but it IS a test-file edit, so it is the lead's boundary call: mine (scope-law regression exception) or contract-fix's (same test-file class as ESC-2/3/4/5). I FIXED the related query-text-scan flag (`test_no_UNDECLARED_value_...`) in my writable set — `message_activity_since` now binds `LIMIT $activity_limit` (never interpolates `{limit}`).
  - Remaining whole-suite RED after my fixes: the **4 companion pins** (ESC-2 `test_comms_promise_registry` · ESC-3 `test_secret_typing` mint-origin · ESC-4 `test_agent_registry` field-set RED@HEAD · ESC-5 `_surreal_harness.py` docstring RED@HEAD) **+ the 5 ESC-6 fake-parity crashes** (one root cause).
- **Receipt pointers:** RED baseline §RED baseline · escalation §Escalation · #304 §D · comms_cli §C · rollup §B · story §A · gates §Gates · mutation-proofs §Mutation proofs · scratch tree receipt §Mutation proofs.

---

## Capability check (tool honesty)
- Store `:18000` (spike-surreal) live and reachable; `:18500` present but never touched. Gates (`pytest -n auto`, `scripts/typecheck.sh`, `ruff`, `pending_contract_gate.py --currency`) all runnable.
- **lore MCP tools did NOT load** — `ToolSearch "+lore"` returned `No matching deferred tools found` twice (the `lore_lore` server was "still connecting" both times). Per the dogfood protocol I SAY SO: all structure lookups this session fell back to `grep`/`Read` over the real tree (rename-exhaustiveness + symbol maps). I will retry the lore load and file a `lore_findings` friction row if it stays down at close-out.

## RED baseline (at `4dc2949`, before any production edit)
`uv run pytest -n auto` the 4 new files → **17 failed / 27 passed, 0 errors** (no setup/import/collection failures — every RED is a behavioural `AssertionError`). The 17 RED, grouped:
- **story** (3): A2 `test_story_renders_subject_creator_owner_messages_and_report_path`, A3 `test_a_question_message_is_marked_and_a_signal_is_not`, A5 `test_a_hostile_message_body_is_fenced_verbatim`.
- **rollup** (4): B1 messages-activity, B4 cursor-bounded, B2 fleet-health, B3 skew.
- **comms_cli** (6): C-counts ×3 (1/1/0, 0/0/0, 2/2/1), C-default-resolution ×3 (no-override, anthropic-independence, routes-through-shared).
- **#304** (4): D5 write-on-change, D6 no-restamp, D7 age render, D8 NONE render.
The GREEN-against-stub invariants (D4 schema, D9a/D9b vocabulary pair, D10 no-poison, F2 containment ∀-field + coverage partition, C-cmd, C-readonly-source/runtime, C-coordinate-safety, A4a/A4b, obedience decline) pass at baseline as designed.

---

## Escalation — the message-read gap (Decisions-needed #1)

**What the contract requires:** `story` must render a task's message ARC (A2 needs a message body `"starting on it now"`; A3 needs the STRUCTURAL question marker from `message.question`; A5 needs a message body fenced verbatim). Rollup's messages section (B1/B4) must list messages filtered by the `since` cursor.

**What exists:** `MessageLedger`'s only public reads are `drain(agent_id, …)`, `pending_traffic(agent_id)`, `awaiting_answer(agent_id)` — all per-RECIPIENT. There is NO task-scoped or since-scoped message read anywhere in the codebase (grep-verified over `loremaster/loremaster/*.py`). `AppContext` reads messages ONLY through those per-agent methods.

**What my writable set contains:** `server.py`, `agents.py`, `store/surreal_schema.py`, `comms_cli.py`. NOT `messages.py`.

**Two readings (the fork):**
- **(A) — RECOMMENDED — the omission is real; add public `MessageLedger` reads.** The ledger owns the `message` table; every other table read in this repo goes through its ledger (server.py never raw-queries a ledger's table — grep-verified). Exact edits (I will apply them the instant the writable set is granted):
  ```python
  # messages.py — value object + window (mirrors TaskActivityWindow)
  class StoredMessage(BaseModel):
      model_config = ConfigDict(extra="forbid")
      seq: int; sender_name: str; grade: str; body: str
      refs: list[str] = Field(default_factory=list)
      question: bool = False; thread: str = ""; task_id: str | None = None
      created_at: datetime

  async def messages_for_task(self, *, task_id: str) -> list[StoredMessage]:
      """Every message anchored to task_id, oldest-first by seq — story's arc read."""
      rows = self._as_rows(await self._query(
          f"SELECT seq, grade, body, refs, thread, question, task_id, "
          f"sender.name AS sender_name, created_at FROM {MESSAGE_TABLE} "
          f"WHERE task_id = $task_id ORDER BY seq", {"task_id": task_id}))
      return [self._row_to_stored_message(row) for row in rows]

  async def messages_since(self, since: datetime, *, limit: int) -> MessageActivityWindow:
      """Messages created at/after `since`, oldest-first — rollup's messages leg
      (mirrors TaskLedger.updated_since / FindingLedger.filed_since: total + capped rows)."""
      # SELECT … WHERE created_at >= $since ORDER BY created_at LIMIT $limit + a count()
  ```
  Cost: two small read methods + one value object + one window model in `messages.py`. Because it adds a store read surface, the strict reading is that it wants its own contract line — but these are pure read compositions over existing columns (no schema/DDL change), the lowest-risk possible addition. **My ask: grant `messages.py` (I add + mutation-proof them here), OR you add them.**
- **(B) — server.py reaches `self.message_ledger._query(...)`.** Stays inside the writable set, reuses the retry seam — but hand-writes SurrealQL against the `message` table INSIDE server.py (duplicates the table name + column set + the `sender.name` link + ordering into a second module) and reaches TWO private methods (`_query`, `_as_rows`). This is the "server never raw-queries a ledger's table" norm broken, and message-table schema knowledge cloned — the exact ONE-IMPLEMENTATION smell the repo pins against. I do NOT recommend it, but it is the tight-scope option if you want to avoid a `messages.py` contract.

**Why this reached you and not the contract:** the contract placed stubs only in the 4 writable files, so its "Writable set touched" (which the brief inherited) never named `messages.py`. The satisfiability receipt holds only if the adversary's reference build read messages somehow — which is exactly the choice above. This is a spec ambiguity (PKT-28 C1: "spec ambiguity is a defect, not a judgment call"), surfaced not silently resolved.

**Everything else is built and green regardless of this ruling** (below). On your ruling I finish A2/A3/A5 + B1/B4 in this session.

### The whole-suite currency check surfaced 4 MORE blockers — all un-editable test-file adjudications the contract left undone
`scripts/pending_contract_gate.py --currency` runs the WHOLE suite (not the contract's 5-file declared blast radius). It reports 9 RED (5 above + these 4). Each needs a test-file edit I am forbidden to make; each is a contract omission, not a code defect. Exact edits below so you (or the contract-author) can apply them in one pass, or grant me the narrow scope.

- **ESC-2 — PROMISE-REGISTRY (`test_comms_promise_registry.py`, un-editable).** The 4 new contract files pin the render method NAME `_render_comms_story` (`test_comms_story.py` calls `AppContext._render_comms_story` directly), and the promise pin scans EVERY `render_line` literal in a `_render_comms_*` function. So the 10 story labels MUST be classified — an inherent conflict the stub hid (it had one literal). They are status-report LABELS (promise-FREE per §9.7). **Edit:** add to `_PROMISE_FREE` in `test_comms_promise_registry.py`: `'story: arc of task {task_id}'`, `'subject: {subject}'`, `'created_by: {created_by}'`, `'owner: {owner}'`, `'status: {status}'`, `'blocked_by: {ids}'`, `'description: {description}'`, `'report: {report}'`, `'summary: {summary}'`, `'messages ({count}):'`. (I can re-word/re-shape any label if you prefer a different render — say so.)
- **ESC-3 — SECRET-MINT ORIGIN (`test_secret_typing.py`, un-editable).** The C-counts pins run the CLI with a RAW `--password` value; the ledger takes `SecretStr`; so comms_cli MUST mint `SecretStr(args.password)` — a credential ORIGIN (the CLI arg is where the secret enters the process, exactly like an env var). The mint-origin allowlist permits only `("loremaster/config.py", "scripts/survey_txn_contention_102.py")`. **Edit:** add `"loremaster/comms_cli.py"` to that `allowed` tuple (a CLI credential-arg origin). **Alternative (no test edit):** a `config.py` seam that mints a `SecretStr` from an explicit CLI value — but `config.py` is not in my writable set either. RECOMMEND the allowlist entry; the mint is genuinely at an origin.
- **ESC-4 — AGENT FIELD-SET PIN (`test_agent_registry.py`, un-editable; RED at HEAD `4dc2949`).** The contract stub added `status_set_at` to `Agent`, but `test_agent_field_set_is_exactly_the_c1_slice` still asserts the pre-`status_set_at` field set. This is RED at HEAD independent of my build (I changed no Agent field). **Edit:** add `'status_set_at'` to that test's `expected` set (it is now part of the agent surface, by contract).
- **ESC-5 — HARNESS DOCSTRING COUNT (`_surreal_harness.py`, un-editable; RED at HEAD `4dc2949`).** The contract's 4 new test files import `_surreal_harness`, pushing importers 48→52, but the harness docstring still says "48 test files import this harness" (`test_surreal_harness.py` re-derives and reddens). RED at HEAD independent of my build. **Edit:** update the two docstring counts in `_surreal_harness.py` to the live values (52 importers; re-derive the `connect_admin`-caller count too).

**My recommendation:** ESC-2/4/5 are mechanical, obviously-correct adjudications the contract omitted; ESC-3 is a small design call (allowlist a real credential origin). Grant me these four test edits (I apply + re-run) OR route to the contract-author. ESC-1 (message read) is the only one with a genuine design fork.

### ESC-6 — FakeMessageLedger parity (surfaced by building ESC-1; #322 DOUBLE-face)
The rollup dispatcher now calls `MessageLedger.message_activity_since`, which the test double `FakeMessageLedger` (`loremaster/tests/_message_fakes.py`) does not have → 5 `test_comms_footer.py::[asyncio-rollup]` tests raise `AttributeError`. The failing guard's OWN message: *"FakeMessageLedger lacks a method its production twin has … a CORRECT build turns into an AttributeError … Add the method to the fake (#322, DOUBLE face)."* The fake's docstring already mandates *"every method's public surface matches the real ledger exactly."* Mechanical oracle-mirror, not an adjudication. **Exact edit** (add to `FakeMessageLedger`, import `StoredMessage`/`MessageActivityWindow`):
```python
async def messages_for_task(self, *, task_id: str) -> list[StoredMessage]:
    await asyncio.sleep(0)
    matching = sorted((m for m in self.db.messages.values() if m.task_id == task_id), key=lambda m: m.seq)
    return [self._to_stored_message(m) for m in matching]

async def message_activity_since(self, since: datetime, *, limit: int) -> MessageActivityWindow:
    await asyncio.sleep(0)
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError(f"limit must be a positive integer, got {limit!r}")
    matching = sorted((m for m in self.db.messages.values() if m.created_at > since), key=lambda m: m.created_at)
    return MessageActivityWindow(rows=[self._to_stored_message(m) for m in matching[:limit]], total=len(matching))

@staticmethod
def _to_stored_message(message: Message) -> StoredMessage:
    return StoredMessage(seq=message.seq, sender_name=message.sender_name, grade=message.grade,
        body=message.body, refs=list(message.refs), question=message.question, thread=message.thread,
        task_id=message.task_id, created_at=message.created_at)
```
An HONEST mirror (filters/sorts/caps, honest total) — it does NOT make the footer assertions trivially pass; they still test rollup's real footer/registry behaviour.

**Query-text-scan flag (`test_no_UNDECLARED_value_is_interpolated_into_query_text`): I FIXED it in my writable set** — `message_activity_since` now binds `LIMIT $activity_limit` (never string-interpolates `{limit}`), so no caller-adjacent value reaches query TEXT. Not an escalation.

---

## D — #304 age-the-declaration  (BUILT — green)
- **Write-side (`agents.py`):** one shared policy helper `AgentRegistry._status_set_at_for(new, prior, prior_stamp, now)` — returns `now` iff the status VALUE changed, else the preserved prior stamp (ONE IMPLEMENTATION: register-create stamps birth, register-re-register + touch both CALL it, never a cloned `now if … else …`). D5 (change stamps), D6 (same-status heartbeat does NOT restamp) green; D10 (option<> no-poison) green.
- **Schema (`surreal_schema.py`):** `status_set_at option<datetime>` was already in `_AGENT_FIELD_SPECS` (stub); `generate_agent_ddl` emits it via `_define_field` (`DEFINE FIELD OVERWRITE`, store §1.1). D4 green. No further edit needed — confirmed.
- **Render (`server.py`):** `_LATCHING_FLEET_STATUSES = frozenset({input_required})` keyed on the auto-flip-winner PROPERTY (comment + named re-open trigger citing `test_agent_registry.py::{TestAgentStatusesConstant,TestIdleAutoFlip}`, Fable FORK 1 rider). Aging is OPT-IN (`age_declaration`, default OFF ⇒ pre-#304 direct-render callers byte-unchanged; the handler opts in via a `status_age_seconds` map off the SAME `now` as the heartbeat age). `_render_fleet_status_cell` renders `input_required 47m` (D7) / `input_required declared: unknown` for a NONE legacy row (D8, never a fabricated 0s). D9a/D9b vocabulary pair green (fleet renders STORED status, never derived `awaiting_answer`). All 12 `test_comms_status_age.py` pins green.
- ⚠ link5 note: the status-cell helper renders via `render_line` (raw sanitisation stays in the already-classified `_render_comms_fleet_row`), so it is not a new render candidate.

## C — comms_cli.py  (BUILT — green, 13/13)
- New read-only CLI. `pending --agent <name>` prints `unread=<n> unacked=<n> skew=<n>`. REUSES `AgentRegistry.get_agent` + `MessageLedger.pending_traffic` (unread/unacked — NOT re-derived) + `BriefLedger.get_head`/`acked_version` for skew (`max(0, head - acked)`, 0 when no standing brief). No raw SELECTs, no `AsyncSurreal` — the C-readonly AST scans pass by construction, and the runtime full-DB snapshot is byte-identical.
- Default coordinate resolution (Fable FORK 2): `_resolve_coordinate` reads the project `lore.yaml` via the SHARED `LoreConfig.model_validate` (env-free — NOT `load_config`, so the unset Anthropic key never blocks boot: C-anthropic-independence) and derives the database THROUGH `LoreConfig.effective_surreal_database` (F7 mutation pin green — a cloned `yaml.safe_load` resolver reddens). `$LORE_CONFIG` is the discovery convention (mirrors the server's own `--config` default). No `18500` literal anywhere (C-coordinate-safety).
- Packages: stdlib `argparse` (the stub's idiom) + `yaml` (already a dep) + the shared config/ledgers. No new mechanism, no hand-roll.

## B — rollup extension  (BUILT — all green: B1/B2/B3/B4)
- **B2 fleet-health / B3 brief-ack-skew:** handler `_rollup` gathers `roster` (true per-status counts) + `_rollup_brief_skew` (reuses `get_head` + `acked_versions_for_ids` — the ONE grouped read the fleet action already uses, never a per-agent loop). `_rollup_extra_sections` renders via `render_line` (not bare f-strings ⇒ not a link5 render candidate). Each section OMITTED when empty (no messages / no agents / no brief), so a 0-activity rollup is byte-identical to before — the existing exact-output pins (empty rollup == 2 lines; the line-count pins in `test_mcp_server.py`) all hold. `_render_rollup` extends `extra_sections` UNCONDITIONALLY (default `()`), so it gains no branch the link5 driver cannot reach.
- **B1 messages-activity / B4 cursor:** built (ESC-1 Option A). `MessageLedger.message_activity_since(since, limit)` — a WHOLE-`message`-table read bounded by `created_at > $since` (EXCLUSIVE, mirrors `updated_since`; NOT drain's per-agent `seen_at` cursor), with an honest `total`. The messages section is omitted when the cursor excludes everything ⇒ B4's pre-cursor exclusion holds AND the empty-collapse pin holds.

## A — story  (BUILT — all green: A2–A5 + F2)
- **Render (`_render_comms_story` / `_render_story_message`):** NAMES its SET (`story: arc of task <id>`), renders subject/created_by/owner/status/blocked_by/description/report/summary + the message arc. Message BODY → `render_fenced` (verbatim, A5); every single-line attribution/id → `render_attributed`. The STRUCTURAL question/signal marker is baked into two templates (from `message.question`, never prose; keeps the method off the link5 candidate universe). F2 containment ∀-field (11 parametrized) + coverage partition + description-end-to-end + A4a/A4b green.
- **Handler (`_comms_story` / `_story_messages`):** `get_task` → CommsStory (created_by from `task.provenance["created_by"]` — `Task` exposes it only there); `_story_messages` REUSES `MessageLedger.messages_for_task` (ONE IMPLEMENTATION — no raw message-table query cloned into server.py) and projects `StoredMessage` → `StoryMessage`. Called via `AppContext._method(self, …)` so the duck-typed harness resolves.

## Gates
- **ruff** `uv run ruff check` on all 5 touched files — **All checks passed**.
- **mypy** `./scripts/typecheck.sh` — **0 errors** across all 5 touched files (grep-scoped). The ~191-error branch baseline (#333 auth-WIP, RED_ADJUDICATED under packet-39) is untouched — none added.
- **pytest** — story `test_comms_story.py` + rollup `test_rollup_extension.py` = **23 passed**; message-ledger regression + full blast radius (9 files) = **1689 passed / 15 skipped** (hard fence held — `test_message_ledger.py` green, drain/pending/awaiting_answer untouched).

## Mutation proofs
Done in a provenance-verified scratch copy — tree receipt `loremaster.__file__ = /tmp/scratch-05aiii-mp/loremaster/loremaster/__init__.py` (asserted inside the scratch, NOT the original). Each: break prod → the named pin goes RED → restore → GREEN.
- **D5** — `_status_set_at_for` never stamps on change (`return prior_stamp`) ⇒ `test_a_status_change_stamps_status_set_at` RED.
- **D6** — `_status_set_at_for` stamps every heartbeat (`return now`) ⇒ `test_the_same_status_does_not_restamp` RED.
- **D7** — `_render_fleet_status_cell` aged branch returns bare status ⇒ `test_input_required_shows_the_declaration_age_beside_the_liveness_age` RED.
- **D8** — the NONE-age branch fabricates `_render_age(0)` ⇒ `test_none_status_set_at_renders_unknown_not_a_fabricated_zero` RED.
- Restored ⇒ `TestStatusSetAtWriteSide` + `TestFleetAgesTheDeclaration` GREEN (2+2 passed).
- **A5** (story fence) — `_render_story_message` renders the body raw (`Rendered(message.body)`, unfenced) ⇒ `test_a_hostile_message_body_is_fenced_verbatim` RED. Scratch tree `/tmp/scratch-05aiii-mp2/…` (provenance asserted; `messages_for_task` present).
- **B4** (rollup messages cursor) — `message_activity_since` drops the `created_at > $since` filter (`WHERE true`) ⇒ `test_messages_section_is_cursor_bounded` RED (the pre-cursor sentinel appears).
- Restored ⇒ `TestStoryContainsStoredFreeTextInAFence` + `TestRollupMessagesSection` GREEN (3 passed).
- **F7** (comms_cli routes through the shared `SurrealConfig`) is a mutation pin BY CONSTRUCTION (`test_default_resolution_routes_through_the_shared_surrealconfig` monkeypatches `LoreConfig.effective_surreal_database` to a sentinel) — green in the comms_cli 13/13.

## Files touched (production)
- `loremaster/loremaster/agents.py` — `_status_set_at_for` helper + register(create/re-register) + touch write-side stamp (#304).
- `loremaster/loremaster/store/surreal_schema.py` — confirmed the stubbed `status_set_at option<datetime>` spec (no edit needed).
- `loremaster/loremaster/server.py` — story render + handler + `_story_messages`, `_render_story_message`, `_render_fleet_status_cell` + `_LATCHING_FLEET_STATUSES` (#304), rollup `_rollup_extra_sections`/`_rollup_brief_skew` + `_render_rollup` extra_sections + the messages leg, `_RollupBriefSkew`, `_STORY_TASK_CREATED_BY_KEY`.
- `loremaster/loremaster/comms_cli.py` — the read-only CLI (rewritten from stub).
- `loremaster/loremaster/messages.py` — **ADD-ONLY** (ESC-1 Option A grant): `StoredMessage`, `MessageActivityWindow`, `messages_for_task`, `message_activity_since`, `_extract_group_count`, `_row_to_stored_message`. Hard fence honoured — `drain`/`InboxEntry`/drain SELECT/`pending_traffic`/`awaiting_answer` untouched.

## Pre-existing / out-of-scope note
`./scripts/typecheck.sh` full run shows the ~191-error mypy baseline (all pre-existing auth-WIP #333, operator-accepted, adjudicated RED_ADJUDICATED under packet-39) — untouched, none added by me. The `pending_contract_gate --currency` verdict is FAIL only on the 9 orphaned pytest RED enumerated in §Escalation, every one requiring a decision above; ruff is GREEN.
