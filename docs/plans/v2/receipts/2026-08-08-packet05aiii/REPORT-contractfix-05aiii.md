# REPORT-contractfix-05aiii — 5 test-side companion pins for packet 05a-iii

brief-base v10 read

## SUMMARY BLOCK
- **State:** done-with-deviations — all 5 companion pins (ESC-2/3/4/5/6) applied, green, committed (shas below). Whole suite: my entire area GREEN; the only residual is the pre-existing packet-39 auth-WIP baseline (316 pytest + 191 mypy), proven isolated from my change.
- **Deviation 1 (ESC-6, the substantive one):** the builder's "one root cause" ESC-6 diagnosis was INCOMPLETE. Fixing `FakeMessageLedger.message_activity_since` unmasked a SECOND parity gap: `_seed_inbox` (in `test_comms_footer.py`, OUTSIDE my writable set) seeds `db.messages` with grade-only `SimpleNamespace(id, grade)` stubs; my faithful whole-table reads hit `.created_at` on them. Fixed IN-scope (`_message_fakes.py`) by making the fake's read filters NONE-tolerant, mirroring the store's `WHERE created_at > $since` (NONE falsy ⇒ excluded) — MORE faithful, not a leniency. Alternative (seed full `Message`s in `test_comms_footer.py`) is out of my writable set — flagged, not taken.
- **Deviation 2 (ESC-2, strengthening):** beyond registering the 10 story literals promise-free, I added `_render_comms_story` to the coverage `expected` set (a new comms render helper belongs in the coverage checker). Tightens, never loosens.
- **Two adjudications (stated in §ESC-2 / §ESC-3):** ESC-2 = all 10 `_render_comms_story` literals are `label: {value}` status reports / a section header, NONE names a call or issues an imperative ⇒ genuinely promise-free (READ the render). ESC-3 = `comms_cli.py:181` mints `SecretStr(args.password)` from `--password` argv — a genuine composition-root credential ORIGIN (READ the CLI); added ONE origin, not a wildcard.
- **Packages considered:** none — no new mechanism specified (all edits are test-side registry/allowlist/count/fake-mirror; the fake mirror reuses stdlib + the shipped `StoredMessage`/`MessageActivityWindow`).
- **Graded:** `c0949b1` · HEAD-at-report: `4fc8b70` · DIFFERENT (3 ahead — my 3 test-only companion-pin commits). The adjudications grade the build at `c0949b1`; my commits touch only the 5 test files, so no production surface my verdict rests on moved.
- **Decisions-needed:** (1) FLAG — `_render_story_message` sits OUTSIDE the promise-scanner's `_render_comms`/`_comms_` prefix, so a future promise added there serves invisibly (no promise today). Clean fix is production (rename `_render_comms_story_message`, or broaden the scanner prefix). (2) FLAG — the ESC-6 alternative: seed full `Message`s in `test_comms_footer.py::_seed_inbox` (out of my writable set).
- **Receipt pointers:** RED baseline §RED baseline · adjudications §ESC-2 / §ESC-3 · mechanical §ESC-4 / §ESC-5 · fake mirror + 2nd gap §ESC-6 · gates §Gates · process gap §Process gap · files §Files touched.

---

## Capability check (tool honesty)
- Store `:18000` (spike-surreal) reachable for the live-store suites; `:18500` NEVER touched.
- **lore MCP tools did NOT load** — `ToolSearch "+lore"` returned `No matching deferred tools found` on every attempt (the `lore_lore` server never came online this session; same as the builder observed). Per the dogfood protocol I SAY SO: every structure lookup this session fell back to `grep`/`Read` over the real tree (symbol locations, importer/mint/field derivations). I could NOT file a `lore_findings` friction row — the tool was unreachable; flagging the lore outage here instead.
- Gates runnable: `uv run pytest -n auto`, `uv run ruff check .`, `./scripts/typecheck.sh`, `scripts/pending_contract_gate.py --currency`.

## RED baseline (at HEAD `c0949b1`, before any edit)
`uv run pytest -n auto` over the 5 companion files → **9 failed / 633 passed**. The 9 RED:
- ESC-2 `test_comms_promise_registry.py::TestEveryCommsRenderLiteralIsClassified::test_every_comms_render_literal_is_classified` (10 unclassified `_render_comms_story` literals).
- ESC-3 `test_secret_typing.py::…::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`.
- ESC-4 `test_agent_registry.py::TestNoForwardCompatFieldsOnAgent::test_agent_field_set_is_exactly_the_c1_slice` (RED@HEAD, build-independent).
- ESC-5 `test_surreal_harness.py::…::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` (48 stated vs 52 actual; RED@HEAD, build-independent).
- ESC-6 `test_comms_footer.py::…[asyncio-rollup]` ×5 (`FakeMessageLedger` lacks `message_activity_since` → AttributeError).

---

## ESC-2 — promise-registry (ADJUDICATED)
**What I READ:** `server.py::_render_comms_story` (+ `_render_story_message`). The scan flags exactly 10 template literals, all in `_render_comms_story`:
`story: arc of task {task_id}` · `subject: {subject}` · `created_by: {created_by}` · `owner: {owner}` · `status: {status}` · `blocked_by: {ids}` · `description: {description}` · `report: {report}` · `summary: {summary}` · `messages ({count}):`.

**Adjudication (promise-FREE, all 10):** every one is a `label: {value}` STATUS REPORT or a section header. NONE names a `lore_comms action=…` call, issues an imperative ("re-run", "catch up", "ack"), or promises any runtime mechanism — so §9.7's litmus (*"if the reader acted on this line, would the promised thing happen?"*) has nothing to gate: there is nothing to act on. `report: {report}` names the report PATH but promises no fetch. Registered in `_PROMISE_FREE` with per-entry reasons. The message-arc BODY is a `render_fenced` block (not a `render_line` template), so it is not a promise literal.

**Strengthening (deviation 2):** added `_render_comms_story` to `test_the_scan_reached_every_comms_render_helper_that_emits`'s `expected` set — it is a new comms render helper and the coverage checker should know it (matches how all 8 existing helpers are pinned). Verified `_render_comms_story` IS observed by the scan, so this stays green.

**FLAG (decision-needed 1):** `_render_story_message` (the per-message header/thread/refs render) is named `_render_story_*`, NOT `_render_comms_*`/`_comms_*`, so the scanner's prefix filter (`_scan_render_literals_over_tree`) does not reach it. Its 4 literals today are pure labels/structural templates (`- #{seq} from {sender} [question]` etc.) — no promise — so the surface is honest and the pin is satisfiable. But a future promise added there would serve INVISIBLY. Clean fix is PRODUCTION (rename to `_render_comms_story_message`, or broaden the scanner's prefix set), so it is a flag, not an edit.

**Receipt:** `uv run pytest -n auto tests/test_comms_promise_registry.py` → **118 passed** (incl. the self-attack + coverage + no-dead-entry legs).

## ESC-3 — SecretStr mint origin (ADJUDICATED)
**What I READ:** `comms_cli.py::_resolve_credentials`. The ONLY `SecretStr(...)` construction in the module is `SecretStr(args.password)` (line 181), taken from the `--password` argparse value; the sibling branch calls `resolve_secret(...)` which wraps INSIDE `config.py` (an already-allowed origin).

**Adjudication (genuine composition root):** `main(argv) → _run_pending(args) → _resolve_credentials(args)` reads `args.password` — the raw credential arriving from the OS argv. That is the point where the bare value FIRST enters the process; there is no earlier site where it could already be a `SecretStr`. A CLI `main()` reading a credential from argv IS a composition root (packet-42 law), exactly like `config.py::resolve_secret` reading an env var. So the mint is AT a credential ORIGIN and closes attack shape S6 (`build_auth_headers(SecretStr(raw))`) trivially — it does not re-wrap a value that was bare through a call chain. Added ONLY `"loremaster/comms_cli.py"` to the pin's `allowed` tuple (ONE origin, never a wildcard), with a reason comment.

**Receipt:** `test_secretstr_is_minted_only_where_a_credential_ORIGINATES` → passes (see §Gates 4-pin run).

## ESC-4 — Agent field-set pin (mechanical)
**What I VERIFIED:** `agents.py::Agent` (BaseModel, `extra="forbid"`) has fields `id, name, session, role, model, status, spawned_by, task_id, checkpoint, last_note, registered_at, heartbeat_at, status_set_at` — the 12 previously-pinned + `status_set_at` (line 257, the #304 aged-declaration stamp). Added `"status_set_at"` to the pin's `expected` set with a comment naming it a deliberate #304 addition (not a forward-compat unread/unacked/orphan-impact creep). No other field crept in — the exact-set equality holds, so a further field still reddens. RED@HEAD `c0949b1`, build-independent.

## ESC-5 — harness docstring counts (mechanical, both re-derived)
**What I DID:** ran the pin's OWN AST derivations — `_harness_importer_files()` = **52**, `_connect_admin_caller_files()` = **34** (all 4 new files both import the harness AND call `connect_admin`; `callers ⊂ importers` holds). BOTH docstring hand-counts were stale (importers 48→**52**, connect_admin 30→**34**). Bumped both.
**Judgment on the "de-hand-count" question (brief):** the docstring number is NOT an unchecked stale-mirror — `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` re-derives it against the AST every run, and the test's own docstring endorses this: *"Prose … must be DERIVED … or CHECKED against it. This is the check."* So the minimal correct fix is the number bump (the pin exists precisely to force it when the population changes), not removing the count.

## ESC-6 — FakeMessageLedger parity + the SECOND (masked) gap
**Mirror (the requested fix):** added to `FakeMessageLedger` (`_message_fakes.py`) — `messages_for_task(*, task_id) -> list[StoredMessage]` (oldest-first by `seq`), `message_activity_since(since, *, limit) -> MessageActivityWindow` (strictly-after `created_at`, oldest-first, capped at `limit`, HONEST uncapped `total`, `ValueError` on non-positive `limit`), and `_to_stored_message(Message) -> StoredMessage`. Signatures/ordering/cursor/total/raise mirror `messages.py::MessageLedger` EXACTLY (READ both real methods + `StoredMessage`/`MessageActivityWindow`). Independent over `self.db` (never a delegation to production), + the `await asyncio.sleep(0)` idiom.

**The second gap (unmasked by the mirror, fixed in-scope):** with `message_activity_since` present, the 5 `[asyncio-rollup]` tests advanced to a NEW crash — a generic `test_comms_footer.py` guard re-labels it "FakeTaskLedger lacks a method", but the true exception is `'types.SimpleNamespace' object has no attribute 'created_at'`. Root cause: `test_comms_footer.py::_seed_inbox` seeds `db.messages[id] = SimpleNamespace(id, grade)` — grade-only stubs (all it needs for `pending_traffic`). The `lore_tasks action=rollup` path reads the WHOLE message table via `message_activity_since`, so my read hit `.created_at` on those stubs.
**Fix (faithful, in `_message_fakes.py`):** made the fake's read filters NONE-tolerant, modelling the STORE's own semantics — `WHERE created_at > $since` excludes a NONE `created_at` (`NONE > $since` is FALSY, per the real method's docstring + `docs/reference/surrealdb-31-capabilities.md` §"a missing SELECT projection reads None"), and `WHERE task_id = $task_id` excludes a NONE `task_id` (`NONE = <concrete id>` is false). So a partial stub is EXCLUDED exactly as the store's WHERE would exclude a NONE row, rather than crashing. This is MORE faithful (the real `_row_to_stored_message` is itself NONE-tolerant via `row.get`), and it does NOT blind the content pins: `test_rollup_extension.py` B1/B4 seed REAL messages with real `created_at`, so the cursor/total discrimination is untouched — only grade-only stubs (which no content pin asserts on) are excluded.
**Alternative considered (flagged, not taken):** seed full `Message` objects in `test_comms_footer.py::_seed_inbox` — out of my writable set, more invasive (a `Message` needs 12 fields for a fixture that wants only `grade`), and it patches the fixture rather than making the oracle faithful to the store.

**Receipt:** `uv run pytest -n auto tests/test_comms_footer.py` → **245 passed** (the 5 rollup tests fixed).

---

## Process gap (observed)
The contract's satisfiability receipt AND the contract-adversary both scoped to the 4 NEW behavioural files (`test_comms_story/rollup_extension/comms_cli/comms_status_age`), so the 5 companion pins the reshape necessitated were uncaught — TWO of them (ESC-4, ESC-5) RED@HEAD `c0949b1`, build-independent, and ESC-2/3/6 unmasked only by the reshaped surface. **ESC-6 compounded it:** the builder's report named ONLY the `FakeMessageLedger` gap ("one root cause"); the second parity gap (the `_seed_inbox` `SimpleNamespace` stubs) surfaced only when the WHOLE suite ran past the first crash. Reinforces the standing rule the brief cited: run the WHOLE suite (`pending_contract_gate --currency`), never the declared blast radius — a companion-pin adjudication that scoped to the 5 files would have missed the ESC-6 second gap entirely.

## Gates (at HEAD `4fc8b70`)
- **ruff** `uv run ruff check .` → **All checks passed!**
- **pytest (5 companion files, post-fix):** promise-registry **118 passed** · footer **245 passed** · the ESC-3/4/5 pins **4 passed**.
- **pytest whole suite** `uv run pytest -n auto` → **316 failed, 7477 passed, 36 skipped, 3 xfailed in 209.56s**. ALL 316 failures are in 7 auth-WIP files — `test_auth_composition`(81) · `test_google_token_verifier`(75) · `test_hosted_readonly_posture`(57) · `test_allowlist_roster`(46) · `test_auth`(25) · `test_auth_identity_seam`(18) · `test_permission_resolver_seam`(14) — the pre-existing #333 auth-WIP baseline (packet-39-owned). **ZERO failures in my 5 companion files OR my comms/story/rollup/message/agent area** (grep-verified over the FAILED list), and **none of the 7 auth files imports any file I touched** (grep-verified) ⇒ my change is proven isolated from the residual.
- **mypy** `./scripts/typecheck.sh` → **191 errors across 11 auth-WIP files** (`test_auth_composition`, `lorerunes/tests/test_{roster_parser,posture,email_normalisation}`, `test_permission_resolver_seam`, `test_hosted_readonly_posture`, `test_allowlist_roster`, `test_google_token_verifier`, `test_auth`, `_auth_fixtures`, `test_auth_identity_seam`) — exactly the documented "~191-line auth-WIP #333 baseline" (RED_ADJUDICATED, packet-39). **NONE of my 5 files appears in the mypy error output** ⇒ zero NEW mypy errors.
- **currency** `scripts/pending_contract_gate.py --currency` → **PASS — every claimed gate is GREEN or OWNED. Zero RED_ORPHANED.** Per-gate: `ruff` GREEN · `typecheck` RED_ADJUDICATED (191 residuals, owned by packet-39-pending-build, trigger operator #296 / packet-39 build start) · `pytest` RED_ADJUDICATED (444 workspace-wide residuals, same owner). The currency gate runs pytest over the WHOLE workspace (loremaster + lorerunes), hence 444 vs my loremaster-scoped 316 — both are the same packet-39 auth-WIP baseline, adjudicated/owned, not orphaned. This is the authoritative confirmation my change adds nothing orphaned.

⚠ **UNRELATED FAILURES FLAGGED (operator rule):** the whole suite carries **316 failing tests unrelated to my scope** (all the packet-39 auth-WIP baseline). Surfaced to the lead in the close-out message, not buried.

## Files touched (all TEST-SIDE, within the writable set)
- `loremaster/tests/test_comms_promise_registry.py` — 10 story literals → `_PROMISE_FREE`; `_render_comms_story` → coverage `expected`.
- `loremaster/tests/test_secret_typing.py` — `"loremaster/comms_cli.py"` → mint-origin `allowed`.
- `loremaster/tests/test_agent_registry.py` — `"status_set_at"` → the exact-set pin.
- `loremaster/tests/_surreal_harness.py` — docstring counts 48→52, 30→34 (both re-derived).
- `loremaster/tests/_message_fakes.py` — `messages_for_task` + `message_activity_since` + `_to_stored_message` mirror (NONE-tolerant, store-faithful).

## Commits (branch `feat/surreal-unification`, no push)
- `9f1abd0` — adjudicated allowlists (ESC-2 promise-registry + ESC-3 mint origin).
- `f3e71fd` — mechanical pins (ESC-4 agent field set + ESC-5 harness counts).
- `4fc8b70` — FakeMessageLedger read-parity mirror (ESC-6, #322) + the NONE-tolerant fix for the second (masked) gap.
- Reports (this file + siblings) left UNTRACKED at repo root — the lead archives them into `docs/plans/v2/receipts/…` at close-out (standing law).
