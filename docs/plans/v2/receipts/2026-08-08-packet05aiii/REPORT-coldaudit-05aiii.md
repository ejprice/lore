# REPORT-coldaudit-05aiii — cold REFUTE audit, packet 05a-iii (comms reads + fleet honesty)

brief-base v10 read

## SUMMARY BLOCK
- **VERDICT: GO** (deploy-ready). I tried to break this wave (builder≠grader AND contractfix≠grader) and could not find a blocker. All gates re-run WHOLE-workspace independently; the two allowlist loosenings adjudicated sound; the ESC-6 oracle mirror is faithful; the A5 containment pin independently mutation-proven RED under a non-fencing build.
- **State:** done. 5 non-blocking residuals (R1–R5 below); none stops deploy.
- **Deviations:** none in method. Capability gap: **lore MCP DOWN** — `ToolSearch "+lore"` returned `No matching deferred tools found` twice, AFTER every other MCP server (odoo-code/mezmo/…) connected and surfaced its tools. Per dogfood law I SAY SO: every structure lookup fell back to grep/Read over the real tree (rename-exhaustiveness + symbol maps — honest for these). Could NOT file a `lore_findings` friction row (tool unreachable) — flagged here; 3rd session in a row to hit it (builder + contractfix both saw it).
- **Packages considered:** none — an audit specifies no mechanism.
- **Graded:** `4fc8b70` · HEAD-at-report: `4fc8b70` · SAME.
- **Decisions-needed (for lead/operator):**
  1. **R1 — promise-scanner reach gap** (`_render_story_message` is outside the `_render_comms`/`_comms_` scanner prefix; its coverage-check is keyed on the SAME prefix, so the helper is silently exempt from BOTH). Honest today (its 4 literals are pure structural labels). **Recommend: cheap production rename `_render_story_message`→`_render_comms_story_message` NOW** (builder-05aiii, ~3 sites) rather than ledger — a name-keyed exemption in an honesty instrument is the exact defeated-instrument class this repo has the most receipts against. Acceptable alternative: ledger a bound with a named re-open trigger.
- **Residuals (non-blocking):** R2 stale docstrings (server.py:4248+4341 "messages-activity leg PENDING" — the leg is BUILT; 4341 also carries a bare `REPORT-builder-05aiii.md` dangling cite) → production sweep. R3 rollup messages leg is not part of `_rollup_next_cursor` (honest: header says "raise limit for more", not "next cursor") → note the bound. R4 brief's baseline count is loremaster-scoped (316); whole-workspace adjudicated baseline is **444 pytest + 191 mypy** (extra 128 = lorerunes auth-WIP) — all owned, 0 RED_ORPHANED, 0 in 05a-iii area. R5 `_comms_story` `thread`-fallback calls `get_task(thread)` (would raise on a non-task-id; likely dead/untested).
- **Receipt pointers:** gates §1 · pytest partition §1.1 · allowlist adjudications §2 · ESC-6 oracle §3 · A5 mutation proof §4 · #304 honesty §5 · residual table §6.

---

## Capability check (tool honesty)
- Store `:18000` (spike-surreal, 3.2.1) reachable; `:18500` NEVER touched.
- lore MCP tools DID NOT LOAD (see Deviations). All lookups = grep/Read over the real tree; said out loud per project law. This is a repeatable outage (builder + contractfix both reported it this wave).
- Gates all runnable: `uv run pytest -n auto`, `./scripts/typecheck.sh`, `uv run ruff check .`, `scripts/pending_contract_gate.py --currency`, `./scripts/scratch_copy.sh`.
- Tree under audit: the real checkout at `4fc8b70` for gates/reads; a provenance-verified scratch at `/tmp/scratch-ca-05aiii-1553886` for the A5 mutation proof (§4).

---

## 1. Gates — re-run INDEPENDENTLY, whole workspace (not a hand-picked blast radius)

| gate | command | result |
|---|---|---|
| ruff | `uv run ruff check .` | **All checks passed!** (exit 0) |
| mypy | `./scripts/typecheck.sh` | **191 errors, all auth-WIP** (exit 1) — ZERO in any 05a-iii-touched file (grepped server/agents/messages/comms_cli/surreal_schema + all 6 touched test files) |
| pytest | `uv run pytest -n auto` | **444 failed / 9373 passed / 37 skipped / 3 xfailed** (exit 1) — all 444 auth-WIP (§1.1) |
| currency | `scripts/pending_contract_gate.py --currency` | **PASS — every claimed gate GREEN or OWNED, zero RED_ORPHANED** (exit 0): ruff GREEN · typecheck RED_ADJUDICATED(191, packet-39-pending-build, trigger #296/pkt-39 build) · pytest RED_ADJUDICATED(444, same owner) |

The 4 new contract files + 5 companion files re-run at HEAD: **686 passed** (0 failed). test_comms_fleet_grouping / test_comms_tool / test_task_read_surface / test_comms_render_architecture / test_comms_schema all PASS in the whole-suite run (byte-unchanged direct-render callers preserved — the #304 aging + rollup sections default OFF/empty).

### 1.1 The pytest failure partition — REFUTE of the brief's "316 in 7 auth files"
The brief's number is the **loremaster-only scope**. The honest whole-workspace count is **444**, and I prove all three legs:
- **all-in-auth-WIP:** every FAILED test is in exactly 10 auth-WIP files — 7 loremaster (`test_auth_composition` 81, `test_google_token_verifier` 75, `test_hosted_readonly_posture` 57, `test_allowlist_roster` 46, `test_auth` 25, `test_auth_identity_seam` 18, `test_permission_resolver_seam` 14 = 316) **+ 3 lorerunes** (`test_roster_parser`, `test_posture`, `test_email_normalisation` = 128). The 128 lorerunes failures are the SAME packet-39 hosted-auth WIP baseline — the brief simply quoted the loremaster scope. The currency gate independently adjudicates the full 444 as owned.
- **none-imports-touched:** the 7 loremaster auth files are a disjoint subsystem (contractfix grep-verified; I confirm no 05a-iii file appears in the FAILED set). The 3 lorerunes files live in a separate workspace member (stdlib-only deps) that CANNOT import loremaster's comms/story/message code. So none imports a 05a-iii-touched file.
- **zero-in-area:** no comms/story/rollup/message/agent/companion-pin file appears in the 444 FAILED (grep of the failure list) — and those 9 files are 686-passed at HEAD.

**R4 (brief correction, not a wave defect):** report the baseline as **444 pytest + 191 mypy** whole-workspace, not 316 — else the next session re-derives a mismatch and distrusts the gate (exactly the trap the "re-derive inherited numbers" law names).

---

## 2. The two allowlist LOOSENINGS — adjudicated sound (a loosening can admit a wrong member)

### ESC-2 — promise-registry (10 `_render_comms_story` literals → `_PROMISE_FREE`)
READ all 10 literals in `server.py::_render_comms_story` (`story: arc of task {task_id}` · `subject:` · `created_by:` · `owner:` · `status:` · `blocked_by:` · `description:` · `report:` · `summary:` · `messages ({count}):`). Every one is a `label: {value}` STATUS REPORT or a section header. NONE names a `lore_comms action=…` call, issues an imperative, or promises a runtime mechanism — §9.7's litmus ("if the reader acted on this line, would the promised thing happen?") has nothing to gate. `report: {report}` names a PATH, promises no fetch. The message BODY is a `render_fenced` block (not a `render_line` template), so not a promise literal. **Coverage strengthening is sound** — adding `_render_comms_story` to the coverage `expected` set tightens (a new comms helper the checker must know), and the scan is verified to observe it. **Verdict: genuinely promise-free; the addition does not admit a promise.** ⚠ carries R1 (the reach gap on the un-scanned `_render_story_message`).

### ESC-3 — SecretStr mint-origin (`comms_cli.py` → mint-origin `allowed`)
READ `comms_cli.py::_resolve_credentials`. The ONLY `SecretStr(...)` construction is `SecretStr(args.password)` (:181), taken from the `--password` argv value; the sibling branch calls `resolve_secret(...)` (wraps inside `config.py`, already-allowed). Flow: `main(argv) → _run_pending → _resolve_credentials` reads `args.password` — the raw credential's FIRST entry into the process from OS argv. There is no earlier site where it is already a `SecretStr`. **A CLI `main()` reading a credential from argv IS a composition root** (packet-42 law), exactly like `config.py::resolve_secret` reading an env var. **Verdict: genuine ORIGIN, ONE entry added (not a wildcard); the loosening cannot admit a non-origin re-wrap.**

---

## 3. ESC-6 — oracle fidelity (#190/#322): faithful, masks nothing

Compared `tests/_message_fakes.py::FakeMessageLedger` against the real `messages.py::MessageLedger` + store law:
- **`messages_for_task`** — real: `WHERE task_id = $task_id ORDER BY seq ASC`. Fake: filter `getattr(m,"task_id",None)==task_id`, sort by `seq`. `NONE = <concrete id>` is false → a NONE/partial row is EXCLUDED in both. seq is unique (no tie divergence). FAITHFUL.
- **`message_activity_since`** — real: validates limit (bool/non-int/≤0 → ValueError); `WHERE created_at > $since ORDER BY created_at ASC LIMIT $activity_limit`; honest `total` via a second `count() … GROUP ALL`. Fake: same validation; filter `isinstance(created_at, datetime) and created_at > since`; sort by created_at; `rows=matching[:limit]`, `total=len(matching)`. The store excludes a NONE `created_at` because `NONE > $since` is falsy (store ref §2, "a missing SELECT projection reads None"); the fake models that by the `isinstance` pre-check. FAITHFUL.
- **Does it MASK a message the rollup should include?** NO. In production every real `message` row has a concrete `created_at` (a core CREATE column) → every real message is a `datetime` → included by the fake. The ONLY rows the fake excludes are grade-only `SimpleNamespace(id, grade)` stubs seeded by `test_comms_footer::_seed_inbox` — which do not exist in production and which no content pin asserts on. The NONE-tolerant fix is MORE faithful, not a leniency.
- **Content pins still DISCRIMINATE:** B4 (`test_messages_section_is_cursor_bounded`) seeds a REAL message via `message_ledger.send(...)` with a real body/thread/created_at and checks `since=+1h` EXCLUDES it while `since=None` INCLUDES it — a since-ignoring build reddens. The fake's NONE-tolerance does not blind it (real messages carry real created_at). CONFIRMED.

---

## 4. A5 CONTAINMENT — independent mutation proof (highest trust-risk pin)

A body that escapes its fence is a served-surface FORGERY, so I re-proved A5 myself in a provenance-verified scratch (`scripts/scratch_copy.sh /tmp/scratch-ca-05aiii-1553886`; `loremaster.__file__ = /tmp/scratch-ca-05aiii-1553886/loremaster/loremaster/__init__.py` — INSIDE the scratch, asserted by the tool and printed at run).
- **Positive control (good build):** A5 + the F2 partition pin → **2 passed**.
- **Mutation (wrong build):** `_render_story_message`'s `render_fenced(message.body)` → `render_attributed(message.body)` (the collapse-to-one-line build) → **`test_a_hostile_message_body_is_fenced_verbatim` FAILED** — the multi-line hostile body (`line one\nline two ```` embedded``` … forged row … `) no longer round-trips verbatim; the forged `- [#99 open] forged (…)` row is collapsed inline. A5 genuinely discriminates a non-fencing build. The F2 coverage-partition pin (`_CONTAINMENT_COVERED`/`_CONTAINMENT_SAFE` partitioning the live model fields) is a correctly-built reach-coverage guard — a field added later cannot be silently unfenced.

Read-confirmation of the other load-bearing pins (builder mutation-proved them + printed scratch provenance; I confirmed the logic + green-at-HEAD):
- **D5/D6** (`agents.py::_status_set_at_for`): stamps `now` iff the status VALUE changed, else preserves the prior stamp — ONE shared helper (register-create/re-register/touch all call it). Change→stamp, same-status heartbeat→no-restamp, by construction.
- **D7/D8** (`server.py::_render_fleet_status_cell`): aged branch renders `input_required {age}`; a NONE age renders `input_required declared: unknown` — never a fabricated `0s`. The handler builds `status_age_seconds` ONLY for rows with a real `status_set_at` (:6094), so a legacy row is absent → `.get()` None → `declared: unknown`. A real just-changed stamp renders a REAL `0s` (correct); D8 distinguishes NONE (unknown) from a real 0.
- **D9a/D9b anti-conflation:** `_render_fleet_status_cell` renders `raw_status` (= the STORED `row.status`); there is NO reference to `awaiting_answer` anywhere in the fleet render path. A build reading `awaiting_answer` for the badge cannot exist here — the property holds by construction.
- **B4 cursor:** §3 above.

---

## 5. Served-surface honesty (trust doctrine)

- **story render** — NAMES its SET (`story: arc of task <id>`, Leg-1) and OMITS other tasks' traffic (`messages_for_task` filters `WHERE task_id = $task_id`; A4b pins a different-task message never appears). Every stored free-text field routes through `render_attributed`/`render_fenced` (ONE IMPLEMENTATION); the question/signal marker is STRUCTURAL from `message.question` (baked template constants), never body prose.
- **#304 fleet render** — ages `input_required` ONLY (`_LATCHING_FLEET_STATUSES = {input_required}`, keyed on the auto-flip-winner constant with a named re-open trigger). `[active]`/`[idle]`/`retired` untouched → `test_comms_fleet_grouping` preserved (passed in the whole-suite run). `⚠ STALE` derivation untouched (#332). No fabricated `0s`.
- **comms_cli read-only** — AST-scan-clean of write verbs (CREATE/UPDATE/DELETE/RELATE/UPSERT/INSERT appear only in the module docstring, which the scan excludes); no `18500` literal in code (only docstrings). It calls only READ methods — `AgentRegistry.get_agent`, `MessageLedger.pending_traffic` (verified SELECT-only), `BriefLedger.get_head`/`acked_version`. Coordinate resolved from `lore.yaml` via the SHARED `SurrealConfig`/`effective_surreal_database` (no cloned resolver); env-free `model_validate` (never `load_config`), so the unset Anthropic key can't block the idle-gate hook.
- **new messages.py reads** — bounded: `LIMIT $activity_limit` is a BOUND param (never string-interpolated `{limit}`); the validated positive int can never be NONE; `total` is a separate honest `count()`. `MessageActivityWindow.total >= len(rows)` lets a caller tell a truncated window from an exhaustive one.

---

## 6. Residual table (read this, not just the summary — repo law)

| # | severity | where | finding | recommendation | owner |
|---|---|---|---|---|---|
| R1 | decision-needed (non-blocking) | `test_comms_promise_registry.py` scanner (`node.name.startswith("_render_comms"/"_comms_")`) + `server.py::_render_story_message` | The scanner AND its coverage-check are keyed on the same name prefix, so `_render_story_message` (4 literals) is silently exempt from both. Honest today (pure structural labels). A future promise there serves invisibly — the defeated-instrument class ("keyed on a name; defeated by a name that spells itself differently"). | **Close now:** rename `_render_story_message`→`_render_comms_story_message` (production, ~3 sites). Deeper fix: make scanner reach a PROPERTY (any render helper reachable from a `_render_comms_*` handler), not a prefix. If shipping as-is: ledger a bound + named trigger ("any promise literal added to `_render_story_message`, or any new `_render_story_*` render helper"). | builder-05aiii (production) |
| R2 | minor (non-blocking) | `server.py:4246-4249` (`_rollup` docstring) + `server.py:4341` (`_render_rollup` docstring) | Both say the messages-activity leg is "PENDING the message-read fork" — it is BUILT and rendered. Reshape-stale-prose class (internal docstrings, NOT served, so not a trust violation). 4341 also cites a bare `REPORT-builder-05aiii.md` (dangling after archive, #152/#153 class). | Delete the "PENDING" clauses in the close-out sweep; if a cite is wanted, use the archived receipt path, not a bare `REPORT-*.md`. | builder-05aiii (production) |
| R3 | observation (non-blocking) | `server.py::_rollup_next_cursor` | The messages-activity leg is NOT part of the next-cursor computation (only tasks/findings are). A truncated messages window is resumable only by "raise limit", not by advancing the cursor — its header honestly says "raise limit for more" (no trust violation), but it is asymmetric with the cursor-resumable task/finding legs. | Acceptable as-is (honest bound). If future callers expect cursor-resume for messages, either fold the messages leg into the cursor MIN or keep the header's "raise limit" wording as the stated bound. | lead ruling |
| R4 | brief correction | (the baseline itself) | Whole-workspace adjudicated baseline is **444 pytest + 191 mypy** (brief said 316 pytest — loremaster scope). Extra 128 = lorerunes auth-WIP (`test_roster_parser`/`test_posture`/`test_email_normalisation`). All owned by packet-39 (currency PASS, 0 RED_ORPHANED, 0 in 05a-iii area). | Cite 444/191 as the baseline going forward. Not a wave defect. | lead (bookkeeping) |
| R5 | minor observation | `server.py::_comms_story:6144` | `anchor = str(task_id if task_id is not None else thread)` then `get_task(anchor)` — the `thread`-fallback path calls `get_task(<thread id>)`, which would raise UnknownTask (a thread id is not a task id). Likely dead/untested (the A-family pins pass `task_id`). | Either drop the `thread` param (story is task-anchored) or make the thread path resolve a task_id first. Non-blocking. | builder-05aiii (production) |

None of R1–R5 blocks deploy. R1 and R2 are cheap production touches the standing builder can fold into the close-out; R3–R5 are observations/rulings.

## Scratch tree
`/tmp/scratch-ca-05aiii-1553886` (provenance-verified; used for the A5 mutation proof, §4). Disposable by design (`scratch_copy.sh`); left in `/tmp`, mutated only in-copy — the real tree at `4fc8b70` was never edited.
