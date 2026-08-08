# REPORT-adversary-05aiii — CONTRACT ADVERSARY, packet 05a-iii (comms READS + FLEET honesty)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: CONTRACT INSUFFICIENT.** Two BLOCKERs + three missing pins, each with a surviving wrong build (receipts below).
- **P1 headline — did a wrong build survive the contract? YES, twice.**
  - **F1 (C-DEF / unsatisfiable):** the story A2 pin cannot go green against ANY correct build — its fixture does `transition(claimed → done)`, an ILLEGAL task edge, and fails at *setup* with `IllegalTransitionError`, not a behavioural assertion. This **falsifies the contract's satisfiability receipt** ("all 12 RED pins fail on a behavioural AssertionError"). Reproduced against the untouched stub at `657a117`.
  - **F2 (QUANTIFIER LAW / BLOCKER):** `story` renders MANY stored free-text fields (subject, **description**, done_summary, refs); the ONLY containment pin (A5) exercises `body` alone. A build that fences the body correctly but raw-renders the **description** passes ALL 6 story pins **and leaks a forged output row** from a hostile description. Both leak-build and safe-build green the contract — it cannot tell them apart.
- **Missing pins (comms_cli read-only gate; its own threat model is the honest-developer footgun):**
  - **F3:** C-readonly-source AST scan reads only string CONSTANTS → typed SDK writes (`conn.create/update/merge/delete/insert/upsert`) carry no verb string and evade it.
  - **F4:** C-readonly-runtime checks row COUNTS of only `{agent,message,to}` → a write to any other table, or an UPDATE/MERGE (no count change), evades it.
  - **F5:** C-counts is a single-fixture monoculture (1 directive → `1/1/0`) → a hardcoded `print("unread=1 unacked=1 skew=0")` passes.
  - Combined receipt: a CLI doing `conn.create("cli_audit", …)` + a hardcoded counts line passes C-readonly-source **and** C-readonly-runtime **and** C-coordinate-safety **and** C-counts, while writing 1 real row per run.
- **Residuals (P2, soft):** **F6** D8's `legacy != fresh` discrimination is timing-fragile (a slow render makes `fresh` "1s", waving a fabricate-zero build through). **F7** C-default pins the coordinate VALUE, not that `SurrealConfig` was REUSED — a cloned resolver passes (ONE-IMPLEMENTATION unenforced).
- **Frontier pins that DO fire (confirmed solid, wrong-build receipts below):** #1 D9 vocabulary pair (conflation reddens D9a AND D9b); #7 D6/D8 write/render (blindstamp→D6, fabzero→D8); #8 A4b scope + B4 cursor; #9 #302 story adjudication (register+dispatch+describe all redden); #2 property-keying re-open trigger is mechanical (a 5th status reddens the domain pin).
- **Packages considered:** none — no NEW mechanism specified (a test contract reusing shipped seams). One ONE-IMPLEMENTATION residual (F7): `SurrealConfig` reuse is `keep_with_trigger` but the reuse is unpinned. Full survey §P-PKG.
- **Graded:** `657a117` · HEAD-at-report `657a117` · **SAME**. All wrong builds run in a provenance-verified scratch copy (`scripts/scratch_copy.sh`); `loremaster.__file__` = `/home/ejprice/scratch/adv05aiii/loremaster/loremaster/__init__.py` on every run. Store: spike-surreal `:18000` only; `:18500` never touched.
- **Receipt pointers:** blocker builds §F1/§F2 · missing pins §F3-F5 · residuals §F6/§F7 · quantifier table §P1b · confirmed-solid §CONFIRMED · full probe record + verbatim instruments §PROBES.

---

## The missing pins, as pins the author can write

| # | The test that should exist | The defect it catches | Sev |
|---|---|---|---|
| **F1** | Fix A2's fixture: `transition(task_id, "in_progress", actor="worker")` BEFORE the `done` transition. | A2 is currently RED-for-the-wrong-reason (setup `IllegalTransitionError`); no correct build greens it, and the satisfiability receipt is false. | BLOCKER |
| **F2** | `test_a_hostile_task_DESCRIPTION_is_contained` (and done_summary / a ref): seed a task whose **description** is the hostile multi-line/row-forge/backtick body; assert no forged row escapes containment. | A story build that fences `body` but raw-renders `description` (the "never re-embed a Rendered in an f-string" footgun the model docstring itself warns of) leaks a forged output row, contract fully green. | BLOCKER |
| **F3** | Extend C-readonly-source to also forbid typed-write METHOD calls (`.create/.update/.merge/.delete/.insert/.upsert/.patch` on a store connection) — an AST call-scan, not just a string-constant scan. Better: a runtime SDK-connection wrapper that refuses any non-SELECT (the repo's own "enforce at RUNTIME / allowlist the safe" instrument-lesson). | A write via a typed SDK method carries no SurrealQL verb string and is invisible to the current constant-only scan. | missing pin |
| **F4** | Make C-readonly-runtime table-complete AND content-sensitive: count EVERY table (`INFO FOR DB`) or snapshot full row content, not row-counts of `{agent,message,to}`. | A write to any other table, or an UPDATE/MERGE that changes no count, mutates the store while the pin stays green. | missing pin |
| **F5** | Add a SECOND C-counts scenario with DIFFERENT values (e.g. 0 unread; ≥2 unread + a published brief → `skew>0`). | A build that hardcodes `print("unread=1 unacked=1 skew=0")` passes the single-fixture pin. | missing pin |
| **F6** | Assert the legacy (NONE) cell renders an explicit unknown TOKEN (e.g. contains "unknown" / carries no `\d+[smhd]` age), not merely `!= fresh`. | On a >1s render, `fresh` becomes "1s" and a fabricate-zero build (legacy→"0s") differs from fresh → D8 false-clears the exact build it targets. | residual |
| **F7** | A mutation/structural pin that `_resolve_coordinate`'s default path routes THROUGH `SurrealConfig` (not a value-only assertion). Or LEDGER the bound with a named trigger. | A cloned hand-rolled resolver passes C-default/C-anthropic; a future `SurrealConfig` change reaches the server and not the CLI. | residual |

---

## P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| Invariant (pin) | ∀-over-inputs vs GUARDED | Receipt |
|---|---|---|
| story containment (A5) | **GUARDED** — conditioned on the ONE field `body` the fixture exercises | **BLOCKER F2**: WB-A fences body, raw-renders description → forged row escapes, all 6 story pins green. Door-build survives. |
| story scope (A4b) | ∀-over-tasks (global `WHERE task_id`) | Door-build (scope-blind, WHERE dropped) → A4b RED. |
| story question marker (A3) | ∀ over {question, signal} — both fates forced, non-monoculture | Body avoids the marker word (structural from `message.question`); passes leak+safe, RED on stub for the right reason. |
| story arc reconstruction (A2) | ∀ (subject/creator/owner/body/report_path) | **BLOCKER F1**: fixture unsatisfiable (illegal `claimed→done`); RED-for-wrong-reason. |
| #304 stored-status render (D9a/D9b) | ∀ over {active+question, input_required+no-question} — both fates forced | Conflation door-build reddens **BOTH** D9a AND D9b. SOLID. |
| #304 stamp-on-change (D5/D6) | ∀ over {change, no-change} — both fates forced | blindstamp door-build → D6 RED (needs the 2nd heartbeat, which the fixture has). SOLID. |
| #304 NONE honesty (D8) | GUARDED — `legacy != fresh`, `fresh` is timing-dependent | fabzero door-build → D8 RED (sub-second). **F6**: a slow render defeats it. |
| #304 no-poison (D10) | ∀ (any field-less row) — schema-guarded by D4 (`option<datetime>`) | D4 parses the OVERWRITE/`option<datetime>` statement; D10 greens on ref, structurally reddens a required-field build. |
| comms_cli read-only source (C-readonly-source) | **GUARDED** — conditioned on STRING CONSTANTS | **F3**: typed SDK write methods carry no verb string → door-build green. |
| comms_cli read-only runtime (C-readonly-runtime) | **GUARDED** — conditioned on COUNTS of `{agent,message,to}` | **F4**: `conn.create("cli_audit",…)` writes 1 real row, pin green. |
| comms_cli counts (C-counts) | **GUARDED** — conditioned on ONE fixture (`1/1/0`) | **F5**: hardcoded `print` door-build green. |
| comms_cli coordinate resolution (C-default/C-anthropic) | ∀ over {key-set, key-unset} — two fixtures | hardcode → both RED; loadconfig → C-anthropic RED (C-default green: correct isolation). **F7**: cloned resolver green (reuse unpinned). |
| rollup cursor (B4) | ∀ over {pre-cursor, post-cursor} — both fates forced | nocursor door-build → B4 RED. SOLID. |
| rollup sections present (B1/B2/B3) | presence (∀ weak — substring `message`/`fleet`/`skew`) | ref greens all three; stub reds. Loose keying, adequate for presence. |

---

## P-PKG — package survey (independently built, then diffed vs the contract's "none")

This is a TEST CONTRACT; it specifies no NEW mechanism, so both the contract's `Packages considered: none` and my own independent survey agree that no library is hand-rolled-around. The mechanisms the contract PINS are all shipped in-house seams it REUSES:

| Mechanism the contract touches | in-house seam reused | verdict | note |
|---|---|---|---|
| multi-line free-text containment | `render_fenced` / `render_attributed` (render.py) | `keep_with_trigger` | trigger = a NEW stored free-text field a render reaches; **F2 is exactly that trigger firing unpinned** |
| question-debt derivation | `MessageLedger.awaiting_answer` | `keep_with_trigger` | D9 pair guards the conflation; SOLID |
| agent field DDL | `_define_field` / `DEFINE FIELD OVERWRITE` (store §1.1) | `keep_with_trigger` | D4 parses the statement (house idiom) |
| CLI store-coordinate resolution | `SurrealConfig` + `effective_surreal_database` | `keep_with_trigger` | **F7**: reuse is the ruling's intent but the pin checks VALUE, not reuse — a clone passes |

Diff vs the author's line: no disagreement on "no new mechanism." The finding is one level down — the contract does not PIN the ONE-IMPLEMENTATION reuse for the CLI resolver (F7), and the containment reuse is pinned over only one field (F2).

---

## CONFIRMED-SOLID (frontier pins that fire correctly — the parts that ARE sufficient)

Every one below was proven by building the exact wrong build and watching the pin redden (commands in §PROBES):

- **#1 / D9 vocabulary (the packet's central wrong build):** a fleet render that derives the badge from `awaiting_answer` reddens **BOTH** D9a (`active`+question → wrongly badges) AND D9b (`input_required`+no-question → false-not-waiting). Two fixtures, different values, real live `awaiting_answer` state. The DD-2 conflation cannot survive.
- **#7 / D6 + D8:** blindstamp (stamp-every-heartbeat) → D6 RED; fabzero (NONE→"0s") → D8 RED. D6 is not monoculture (uses the 2nd heartbeat); D8 has the NONE-vs-0s pair (but see F6).
- **#8 / A4b + B4:** scope-blind story → A4b RED; cursor-ignoring rollup → B4 RED.
- **#9 / #302 adjudication:** removing `story` from `_COMMS_ACTIONS` reddens the exact-set pin (`test_the_COMMS_actions_are_EXACTLY_the_declared_set`), the per-action coverage pin (`test_every_action_has_at_least_one_registered_case`) and `test_exact_action_set`; removing `story` from the served description reddens `test_description_names_every_action`. Register + dispatch + describe all pinned. `story` does not slip in unadjudicated.
- **#2 / property-keying re-open trigger:** adding a 5th status ("blocked") reddens `TestAgentStatusesConstant.test_agent_statuses_is_the_closed_four_value_domain`. The trigger is MECHANICAL (a new latching status cannot be added silently), and `touch`'s else-branch (`new_status = agent.status`) means ANY new non-idle status auto-latches → trips the domain pin. The render-side property-key guard is deliberately NOT built (undiscriminable at a single-member latch set); that limitation is operator-ratified (Fable FORK 1) and the docstring points the forced human review at the age-scope decision. **Not a missing pin** — a ratified docstring-linked trigger with a confirmed tripwire.

---

## F1 — BLOCKER: story A2 is UNSATISFIABLE (RED for the wrong reason)

`test_story_renders_subject_creator_owner_messages_and_report_path` (test_comms_story.py:142) sets up its fixture with:
```python
await sctx.task_ledger.claim_task(task_id, "worker")      # -> status 'claimed'
...
await sctx.task_ledger.transition(task_id, "done", ...)    # claimed -> done : ILLEGAL EDGE
```
`LEGAL_TRANSITIONS` (tasks.py) contains `(claimed, in_progress)` and `(in_progress, done)` but **NOT `(claimed, done)`** — tasks.py's own docstring says "rejected like `claimed -> done`". So the fixture raises `IllegalTransitionError` BEFORE `_comms_story` is ever called.

Receipt (untouched stub at `657a117`, scratch copy):
```
E  loremaster.tasks.IllegalTransitionError: illegal transition from 'claimed' to ```done```
loremaster/tasks.py:1868: IllegalTransitionError
1 failed in 1.37s
```
This is the **C-DEF class** the lead's frontier #10 names: a pin RED for a setup error, not a behavioural assertion. The contract's satisfiability receipt (§Satisfiability, REPORT-contract-05aiii: "every one of the 12 RED pins … fails on a *behavioural `AssertionError`*") is **false for A2**. A3 and A5 DO fail behaviourally (verified — they do no `done` transition), so F1 is scoped precisely to A2.

**Fix:** insert `await sctx.task_ledger.transition(task_id, "in_progress", actor="worker")` before the `done` transition. With that one line, WB-A (leak) and WB-REF (safe) both green all 6 story pins (verified) — proving the rest of the story leg is satisfiable and the bug is only A2's fixture.

## F2 — BLOCKER: story containment is pinned over `body` only (QUANTIFIER LAW)

`CommsStory` (server.py:7357) carries `subject`, `description`, `done_summary`, `report_path`, `owner`, and `messages[].{body, refs}` — all stored free text. The stub docstring itself says the builder "routes EVERY stored free-text field (bodies, refs, ack_notes, descriptions) through render_attributed/render_fenced". But the ONLY containment pin, A5 (`test_a_hostile_message_body_is_fenced_verbatim`), exercises **`body`**.

Wrong build **WB-A** (verbatim in §PROBES): reconstructs the arc, marks questions, scopes to the task, fences every message `body` correctly — and raw-renders `description` via `f"description: {story.description}"` (the "never re-embed a Rendered in an f-string" footgun). Result against the FIXED story contract (A2 fixture patched so the leg is runnable at all):
```
WB-A (leak):  6 passed          <- ALL story pins green
WB-REF (safe, description attributed): 6 passed
```
Both green. Then a hostile-description probe (`leak_probe.py`, §PROBES) drives the real handler with a task whose DESCRIPTION is the same multi-line/row-forge/backtick payload A5 puts in a body:
```
WB-REF (safe):  forged row escapes fence/containment: False
WB-A  (leak):   forged row escapes fence/containment: True
   >>> '- [#99 open] forged (kind friction, by attacker) ``` `'
```
A forged output row is emitted as lore's own output. The contract cannot distinguish the leaking build from the safe one — the containment invariant is conditioned on the single member of the set it governs. This is the QUANTIFIER LAW failure the repo has now shipped repeatedly (PR93 / PKT-28), reproduced on story.

## F3 / F4 / F5 — comms_cli read-only gate: three doors (all in the gate's own threat model)

The C-readonly gate's stated threat model (comms_cli docstring) is the FOOTGUN — "a hook that could mutate the fleet ledger while merely *checking* it". All three doors below are honest-developer footguns, not clever attacks.

Wrong build **WB-CLI** (`wb_cli.py`, verbatim §PROBES): a `pending` that connects and issues `await conn.create("cli_audit", {"agent": …, "checked": True})` — a typed SDK write (an "audit trail" footgun) to an uncounted table — then `print("unread=1 unacked=1 skew=0")`. Result:
```
test_source_issues_no_write_verb ............... PASSED   (F3: typed method, no verb string)
test_pending_is_read_only_row_counts_unchanged . PASSED   (F4: cli_audit uncounted; agent/message/to unchanged)
test_source_never_hardcodes_the_production_coordinate PASSED
test_pending_reports_unread_unacked_and_skew ... PASSED   (F5: hardcoded 1/1/0)
```
Proof the "read-only" build genuinely WRITES (subprocess, as the test runs it):
```
CLI exit=0 stdout='unread=1 unacked=1 skew=0'
cli_audit rows written by this 'read-only' run: 1   <-- a WRITE the contract waved through
```
`AsyncSurreal` exposes `create, update, merge, delete, insert, insert_relation, upsert, patch` — every one a write with no SurrealQL verb string (F3). `_comms_row_counts` counts only `("agent","message","to")` and only COUNTS (not content), so a write elsewhere or an UPDATE/MERGE is invisible (F4). C-counts has one scenario, so a constant print passes (F5).

## F6 — residual: D8 timing-fragility

D8 asserts `legacy_cell != fresh_cell`. `fresh` is `set_status_set_at(fresh, datetime.now(UTC))` then rendered; the render computes `int((render_now - fresh.status_set_at))`. On this box that rounds to "0s" and a fabricate-zero build (legacy→"0s") reddens correctly. But if the render takes >1s (loaded host, several store round-trips), `fresh` renders "1s" and fabzero's legacy "0s" DIFFERS from "1s" → D8 GREEN over the exact build it targets. Low-probability, but timing-dependent discrimination is the fixture class FIXTURES-MUST-DISCRIMINATE warns about. Fix in the table (assert an explicit unknown token).

## F7 — residual: ONE-IMPLEMENTATION reuse is unpinned for the CLI resolver

C-default-resolution asserts `resolved.{url,namespace,database} == fixture values`. A build that reads the same `lore.yaml` via a hand-rolled `yaml.safe_load` + manual dict access (NOT `SurrealConfig`) returns identical values and passes — verified (`2 passed`). Ruling FORK 2's ONE IMPLEMENTATION intent ("reused, NOT cloned") is therefore not enforced; a future `SurrealConfig` change (a new default, a slug-derivation tweak) reaches the server and not a cloned CLI. Genuinely hard to pin without coupling — a LEDGERED bound with a named trigger ("the day SurrealConfig's resolution changes, re-verify the CLI follows") is an acceptable alternative to a mutation pin.

---

## PROBES — full record (commands, real output, verbatim instruments)

All runs: scratch copy `/home/ejprice/scratch/adv05aiii` (provenance-verified via `scripts/scratch_copy.sh`; `loremaster.__file__` printed and confirmed inside the copy on every run). Store spike-surreal `:18000`. Graded sha `657a117`.

### Instruments (deliverables per brief-base §1 — pasted verbatim so the claims re-run)

**`patch_story.py`** — installs WB-A (leak) or WB-REF (safe) story builds:
```python
import sys
from pathlib import Path
MODE = sys.argv[1]  # leak | safe
SERVER = Path("/home/ejprice/scratch/adv05aiii/loremaster/loremaster/server.py")
HANDLER = '''    async def _comms_story(self, *, task_id: str | None = None, thread: str | None = None, **_ignored: Any) -> Rendered:
        if task_id is None and thread is None:
            raise ValueError("story needs a task_id (or thread) to anchor on — it reconstructs ONE task's arc")
        anchor = str(task_id if task_id is not None else thread)
        task = await self.task_ledger.get_task(anchor)
        raw = await self.message_ledger._query(
            "SELECT seq, grade, body, refs, question, thread, sender.name AS sender_name "
            "FROM message WHERE task_id = $tid ORDER BY seq", {"tid": anchor})
        rows = self.message_ledger._as_rows(raw)
        messages = [StoryMessage(seq=int(r["seq"]), sender_name=str(r.get("sender_name") or "?"),
            grade=str(r.get("grade") or "signal"), body=str(r.get("body") or ""),
            refs=[str(x) for x in (r.get("refs") or [])], question=bool(r.get("question")),
            thread=str(r.get("thread") or "")) for r in rows]
        story = CommsStory(task_id=anchor, subject=task.subject, description=task.description,
            created_by=str(task.provenance.get("created_by") or ""), owner=task.owner, status=task.status,
            report_path=task.report_path, done_summary=task.summary, messages=messages)
        return AppContext._render_comms_story(story)

    @staticmethod
    def _render_comms_story(story: CommsStory) -> Rendered:
        lines: list[str] = [str(render_line("story: arc of task {tid}", tid=render_attributed(story.task_id)))]
        if story.subject:
            lines.append(str(render_line("subject: {s}", s=render_attributed(story.subject))))
%DESC%
        if story.owner:
            lines.append(str(render_line("owner: {o}", o=render_attributed(story.owner))))
        if story.report_path:
            lines.append(str(render_line("report: {r}", r=render_attributed(story.report_path))))
        if story.done_summary:
            lines.append(str(render_line("summary: {v}", v=render_attributed(story.done_summary))))
        for m in story.messages:
            marker = " [question]" if m.question else ""
            lines.append(str(render_line("- msg #{n} from {s}{mk}:", n=safe_str(str(m.seq)),
                s=render_attributed(m.sender_name), mk=safe_str(marker))))
            lines.append(str(render_fenced(m.body)))
        return "\\n".join(lines)  # type: ignore[return-value]
'''
DESC_LEAK = '''        if story.description:
            lines.append(f"description: {story.description}")'''   # RAW f-string interpolation = leak
DESC_SAFE = '''        if story.description:
            lines.append(str(render_line("description: {d}", d=render_attributed(story.description))))'''
block = HANDLER.replace("%DESC%", DESC_LEAK if MODE == "leak" else DESC_SAFE)
t = SERVER.read_text()
start = t.index("    async def _comms_story("); end = t.index("    async def _comms_send(")
SERVER.write_text(t[:start] + block + "\n" + t[end:])
```

**`leak_probe.py`** — drives the real `_comms_story` with a hostile task DESCRIPTION, reports whether a forged row escapes the fence:
```python
import asyncio, sys
sys.path.insert(0, "/home/ejprice/scratch/adv05aiii/loremaster/tests")
from types import SimpleNamespace
from typing import Any, cast
from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, unique_database
from loremaster.agents import AgentRegistry; from loremaster.briefs import BriefLedger
from loremaster.messages import MessageLedger; from loremaster.server import AppContext
from loremaster.tasks import TaskLedger; from render_injection_scaffold import _ROW_FORGE_PAYLOAD
HOSTILE = f"line one\nline two\n{_ROW_FORGE_PAYLOAD}"; FORGE_PREFIX = "- [#99 open] forged"
async def main():
    db = unique_database(); env = make_env(database=db, dim=PRODUCTION_DIM)
    coord: dict[str, Any] = {"url": env.url, "namespace": env.namespace, "database": env.database,
                             "user": env.user, "password": env.password}
    s = await connect_admin(env); await s.close()
    ar = AgentRegistry(**coord); ml = MessageLedger(**coord); tl = TaskLedger(**coord); bl = BriefLedger(**coord)
    for l in (ar, ml, tl, bl): await l.ensure_ready()
    ctx = SimpleNamespace(agent_registry=ar, message_ledger=ml, task_ledger=tl, brief_ledger=bl,
                          config=SimpleNamespace(comms=SimpleNamespace(stale_heartbeat_s=600, fleet_limit=20)))
    await ar.register("lead", session="probe", role="lead")
    tid = await tl.create_task("benign subject", HOSTILE, created_by="lead")
    rendered = str(await AppContext._comms_story(cast(AppContext, ctx), task_id=tid, thread=None))
    lines = rendered.splitlines()
    fence = [i for i, ln in enumerate(lines) if ln and set(ln) == {"`"}]
    in_fence = set()
    for a, b in zip(fence[0::2], fence[1::2]): in_fence.update(range(a, b + 1))
    escapes = any(ln.strip().startswith(FORGE_PREFIX) and i not in in_fence for i, ln in enumerate(lines))
    print(f"HOSTILE description rendered. forged row escapes fence/containment: {escapes}")
    for l in (ar, ml, tl, bl): await l.close()
    await drop_database(env)
asyncio.run(main())
```

**`wb_cli.py`** (the writing "read-only" CLI) — the load-bearing lines:
```python
async def _run(args):
    from surrealdb import AsyncSurreal
    from pydantic import SecretStr
    from loremaster.store._txn import bootstrap_session, signin_credentials
    conn = AsyncSurreal(args.url)
    await conn.signin(signin_credentials(user=args.user, password=SecretStr(args.password)))
    await bootstrap_session(conn, args.namespace, args.database, url=args.url)
    await conn.create("cli_audit", {"agent": args.agent, "checked": True})  # typed write, no verb string
    await conn.close()
def main(argv=None):
    args = _build_parser().parse_args(argv)
    if args.command == "pending":
        asyncio.run(_run(args)); print("unread=1 unacked=1 skew=0"); return 0   # hardcoded counts
    return 2
```
(patch_fleet.py / patch_rollup.py / patch_cli_resolve.py follow the same shape — each swaps one seam per the mode; the full set lives at `/home/ejprice/scratch/*.py`.)

### Run log (key results)

```
# F1 — A2 unsatisfiable, against the UNTOUCHED stub at 657a117
$ pytest tests/test_comms_story.py::…::test_story_renders_subject_creator_owner_messages_and_report_path
E  loremaster.tasks.IllegalTransitionError: illegal transition from 'claimed' to ```done```
1 failed in 1.37s
# A3/A5 against the same stub fail BEHAVIOURALLY (right reason):
E  AssertionError: a question message must be marked structurally (from message.question)
E  AssertionError: a stored body must round-trip byte-verbatim inside its fence

# F2 — WB-A (leak) vs the FIXED story contract, + the leak probe
patch_story.py leak  -> pytest tests/test_comms_story.py -> 6 passed
patch_story.py safe  -> 6 passed
leak_probe (WB-REF safe): forged row escapes: False
leak_probe (WB-A leak):   forged row escapes: True  >>> '- [#99 open] forged (kind friction, by attacker) ``` `'

# #304 — reference greens all 8 age pins; each wrong variant reddens its target
patch_fleet.py ref        -> tests/test_comms_status_age.py: 8 passed
patch_fleet.py blindstamp -> FAILED TestStatusSetAtWriteSide::test_the_same_status_does_not_restamp        (D6)
patch_fleet.py fabzero    -> FAILED TestFleetAgesTheDeclaration::test_none_status_set_at_renders_unknown_… (D8)
patch_fleet.py conflate   -> FAILED …test_active_with_an_outstanding_question_still_shows_active           (D9a)
                             FAILED …test_input_required_with_no_question_still_shows_input_required        (D9b)

# comms_cli resolution — wrong builds redden the ruled pins
patch_cli_resolve.py hardcode   -> C-default RED + C-anthropic RED
patch_cli_resolve.py loadconfig -> C-anthropic RED (C-default green: correct isolation)
cloned yaml resolver (F7)       -> TestDefaultCoordinateResolution: 2 passed  (reuse unpinned)

# comms_cli read-only — WB-CLI writes yet passes the safety+counts pins
wb_cli.py -> test_source_issues_no_write_verb PASSED; test_pending_is_read_only_row_counts_unchanged PASSED;
             test_pending_reports_unread_unacked_and_skew PASSED; cli_audit rows written per run: 1

# rollup — ref satisfiable, nocursor reddens B4
patch_rollup.py ref      -> tests/test_rollup_extension.py: 4 passed
patch_rollup.py nocursor -> FAILED TestRollupMessagesSection::test_messages_section_is_cursor_bounded (B4)

# scope + #302 + property-keying
story scope-blind (drop WHERE task_id) -> FAILED …test_story_omits_other_tasks_traffic (A4b)
remove story from _COMMS_ACTIONS       -> FAILED exact-set + coverage pins (3)
remove story from tool description     -> FAILED test_description_names_every_action
add 5th status "blocked"               -> FAILED test_agent_statuses_is_the_closed_four_value_domain
```

### Positive controls (P0 — my instruments can SEE both directions)
- Story leak/safe: WB-REF (safe) is the accept-control (does NOT leak, contract green); WB-A (leak) is the reject-case (leaks, contract STILL green). The probe fires on the known-broken input and stays silent on the known-good one.
- #304: the `ref` build is the accept-control (all 8 green); each wrong variant reddens ONLY its target pin (blindstamp→D6 alone, fabzero→D8 alone), so the pins discriminate rather than failing wholesale.
- comms_cli: `hardcode` reddens BOTH resolution pins, `loadconfig` reddens ONLY C-anthropic (C-default stays green) — proving C-default turns on coordinate-reading and C-anthropic turns on the key, not both on one thing.

## Scope law — nothing dropped
- The A2 illegal-transition bug (F1) is a defect in a TEST FILE I may not edit; surfaced here with the exact one-line fix, not edited.
- I did NOT build a fully-correct `pending` for C-counts (only a hardcoded-print build showing satisfiable-and-monoculture) — a disclosed bound of the satisfiability check; the counts leg's correctness against a REAL reads-impl is unverified by me.
- Instruments live at `/home/ejprice/scratch/*.py` (disposable) — the load-bearing ones are pasted verbatim above so every claim re-runs.

**VERDICT: CONTRACT INSUFFICIENT** — F1 (unsatisfiable A2, falsifies the satisfiability receipt) and F2 (story containment pinned over `body` only; a leaking build survives) are BLOCKERs; F3/F4/F5 are missing pins on the comms_cli read-only gate, each with a surviving wrong build.
