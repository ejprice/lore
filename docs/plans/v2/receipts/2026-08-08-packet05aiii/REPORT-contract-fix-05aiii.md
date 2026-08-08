# REPORT-contract-fix-05aiii — satisfy the adversary (packet 05a-iii)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State: done.** All 7 adversary findings (2 BLOCKERs + 3 missing pins + 2 residuals)
  SATISFIED and each MUTATION-PROVEN against the exact wrong build the adversary named.
  Contract kept whole-satisfiable (per-leg reference builds green; no cross-leg
  contradiction). Only 3 TEST files touched; no production code greened.
- **F1 (BLOCKER)** — A2 fixture: inserted `claimed→in_progress` before `done`. A2 now fails
  BEHAVIOURALLY vs the stub (`'reticulate the splines' missing`), not at setup — satisfiability
  receipt restored. Safe story build → **19 passed**.
- **F2 (BLOCKER, QUANTIFIER LAW)** — new `TestStoryFencesEveryFreeTextField`: a render-level
  parametrized containment pin over EVERY free-text field (11 params) + a coverage-CHECKED
  partition pin + an end-to-end description pin. WB-A (leak_description) → **only the 2
  description pins RED**; leak_owner → **only story.owner RED** (per-field discrimination);
  safe → all green.
- **F3+F4 (missing pins)** — `test_pending_is_read_only_full_db_content_unchanged` snapshots the
  ENTIRE DB (INFO FOR DB + full row content) + `test_source_issues_no_typed_write_method` (AST
  call-scan). WB-CLI → BOTH RED (`new tables: ['cli_audit'] {(0,1)}`), while the OLD constant
  verb-scan stays GREEN (the exact F3 blindness).
- **F5 (missing pin)** — C-counts is now 3 scenarios (1/1/0, 0/0/0, 2/2/1). WB-CLI's hardcoded
  `1/1/0` → scenarios B & C RED. Correct build → all 3 green (**scenario C's skew=1 validated
  real, not a C-DEF trap**).
- **F6 (residual)** — D8 gains a timing-INDEPENDENT leg (explicit-unknown token / no `\d+[smhd]`).
  fabzero → D8 RED; demonstrated the F6 leg CATCHES the slow-render case `!= fresh` MISSES.
- **F7 (residual)** — chose a MUTATION pin (not a ledger): monkeypatch `LoreConfig.
  effective_surreal_database` to a sentinel. Correct → green; cloned yaml resolver → RED while
  C-default/C-anthropic stay green (the adversary's F7 door).
- **Packages considered:** none — test contract, no NEW mechanism. Every seam pinned is shipped
  in-house (`render_attributed`/`render_fenced`, `MessageLedger.pending_traffic`,
  `LoreConfig`/`SurrealConfig`, `AsyncSurreal`); F7 pins the ONE-IMPLEMENTATION `SurrealConfig`
  reuse it flagged (`keep_with_trigger` → now mutation-pinned).
- **Deviations:** (1) test_comms_cli.py gained `import json`, `from typing import Any`,
  `BriefLedger`, `LoreConfig` imports (needed by the new pins); (2) the single C-counts method
  became 3 scenario methods (rename); (3) minor A2 observation surfaced below, NOT fixed
  (outside F1 scope).
- **Graded:** authored + verified against `657a117` · HEAD-at-report `657a117` · SAME.
  Store: spike-surreal `:18000` ONLY; `:18500` never touched.
- **Decisions-needed:** (a) A2's "creator" needle is satisfied by the coincident message SENDER,
  not `created_by` rendering — a pre-existing fixture-reason gap (out of F1 scope) — fix or leave?
- **Receipt pointers:** gate counts §Gates · per-finding pins+proofs §F1–§F7 · satisfiability
  §Satisfiability · instruments (verbatim) §Instruments · scratch provenance §Scratch.

---

## Scratch provenance (#140)

All wrong/reference builds ran in a `scripts/scratch_copy.sh` copy at
`/home/ejprice/scratch/cf05aiii`, provenance-VERIFIED at build time
(`loremaster -> /home/ejprice/scratch/cf05aiii/loremaster/loremaster/__init__.py`) and
re-printed on the story + CLI + fleet runs. Store spike-surreal `:18000`. The scratch tree +
patcher scripts (`cf05aiii-patch_{story,cli,fleet,resolver}.py`) are DISPOSABLE; the load-bearing
patchers are pasted verbatim in §Instruments so every claim re-runs. **Scratch tree still on disk
— operator's call whether to reap it** (it is a scratch_copy, not a git worktree).

## Gates (real tree, my final edits, against the STUB)

- **ruff** `uv run ruff check` on all 3 files → **All checks passed**.
- **mypy** `./scripts/typecheck.sh` → grep over the 3 touched files returns **nothing** (zero new
  errors). Branch baseline (~191 auth-WIP #333) untouched.
- **pytest** the 3 files (`-n auto`, `:18000`) → **13 failed / 27 passed**. Every one of the 13 is a
  BEHAVIOURAL contract RED (list below); the 27 are the GREEN(inv)/structural/decline pins.
  The 13 RED, classified — all fail on a behavioural `AssertionError` (handler/write-side/render/
  resolver unbuilt), NONE at setup/import:
  - Story: A2 `..._subject_creator_owner_messages_and_report_path` (now behavioural, F1),
    A3 `..._question_message_is_marked...`, A5 `..._hostile_message_body_is_fenced_verbatim`.
  - Age: D5 `..._status_change_stamps...`, D6 `..._same_status_does_not_restamp`,
    D7 `..._declaration_age_beside_the_liveness_age`, D8 `..._renders_unknown_not_a_fabricated_zero`.
  - CLI: C-counts A/B/C (`..._one_unread_directive` / `..._zero_when_no_traffic` /
    `..._multiple_unread_and_brief_skew`), C-default `..._resolves_the_config_surreal_coordinate`,
    C-anthropic `..._does_not_require_an_anthropic_key`, F7 `..._routes_through_the_shared_surrealconfig`.
- **Existing non-auth surface** (5 sibling comms files, satisfiability): **1298 passed / 1 skipped /
  0 failed** — ZERO new failures (matches the branch baseline). No production or sibling-test file
  was touched.

---

## F1 — A2 unsatisfiable fixture (BLOCKER, C-DEF)

- **Pin:** `test_story_renders_subject_creator_owner_messages_and_report_path` — inserted
  `await sctx.task_ledger.transition(task_id, "in_progress", actor="worker")` between `claim_task`
  and the `done` transition (`LEGAL_TRANSITIONS`: `claimed→done` is illegal; `claimed→in_progress→
  done` is legal — `tasks.py`).
- **Discrimination / RED-for-right-reason:** against the untouched stub A2 now fails on the
  behavioural assertion `AssertionError: story must reconstruct the task arc; 'reticulate the
  splines' missing from: 'story: arc of task ```…``` (stub — lineage not yet reconstructed)'` —
  NOT `IllegalTransitionError` at setup. The satisfiability receipt ("every RED pin fails
  behaviourally") is restored.
- **Mutation-proof:** safe reference story build (§Instruments `patch_story.py safe`) →
  `19 passed` (A2 flips RED→GREEN; the whole story leg satisfiable).

## F2 — story containment ∀ free-text field (BLOCKER, QUANTIFIER LAW)

- **Pins (new `TestStoryFencesEveryFreeTextField`):**
  - `test_a_hostile_value_in_a_free_text_field_is_contained` — **parametrized over 11 covered
    fields** (`story.{task_id,subject,description,created_by,owner,report_path,done_summary}` +
    `message.{body,refs,sender_name,thread}`). Constructs a `CommsStory` DIRECTLY with the
    multi-line row-forge payload in ONE field and calls `_render_comms_story`; asserts no forged
    row escapes (`_forged_row_escapes`, the adversary's `leak_probe.py` check reused verbatim —
    ONE IMPLEMENTATION). Render-level because the render is the LAST line of defense and
    `done_summary`/`report_path` are write-validated single-line (`_validate_done_summary`), so
    only a direct construction proves the render itself fences them.
  - `test_containment_covers_every_free_text_field_story_renders` — **coverage as a CHECKED
    variable:** `_CONTAINMENT_COVERED ∪ _CONTAINMENT_SAFE` must PARTITION the live
    `CommsStory`/`StoryMessage` model fields. A new field added later reddens this until
    classified — it cannot ship silently unfenced.
  - `test_a_hostile_task_description_is_contained_end_to_end` — the adversary's WB-A door
    END-TO-END: a task whose stored DESCRIPTION carries the payload, driven through the REAL
    handler (mirrors `leak_probe.py`).
- **Discrimination:** GREEN(inv) — pass vs the stub (renders only a header, nothing escapes) AND
  a correct build; redden only a leaking build. `_forged_row_escapes` is seam-agnostic (fenced →
  contained; attributed → newline stripped, forge never starts a line; raw f-string → forge on
  its own line outside any fence).
- **Mutation-proof (§Instruments `patch_story.py`):**
  - `safe` → `19 passed` (all story pins incl. every containment param GREEN).
  - `leak_description` (WB-A: fences body, raw-renders description via f-string) → **exactly 2
    failed**: `..._is_contained[story.description]` + `..._contained_end_to_end`; **17 passed**.
    Escaping line observed: `description: line one\n… \n- [#99 open] forged (kind friction, by
    attacker) ``` `` — its own line, outside any fence.
  - `leak_owner` (raw-render owner instead) → **exactly 1 failed**: `..._is_contained[story.owner]`;
    **18 passed** — proving the parametrization discriminates PER FIELD, not just description.

## F3 + F4 — comms_cli read-only gate (missing pins)

- **Pins:**
  - `test_pending_is_read_only_full_db_content_unchanged` — snapshots the ENTIRE database (every
    table via `INFO FOR DB`, every row's full CONTENT via `SELECT *`, canonicalized) before/after
    the CLI run; asserts byte-identical. Subsumes F3 (typed SDK write — no verb string) AND F4
    (write to any other table / content-only UPDATE-MERGE).
  - `test_source_issues_no_typed_write_method` — AST CALL-scan forbidding `.create/.insert/.update/
    .upsert/.merge/.patch/.delete/.relate/.insert_relation` on a store connection, SCOPED to
    `AsyncSurreal`-bound receivers (so stdlib `dict.update`/`list.insert` never trip it — the
    switch-it-off insult). Documented HEURISTIC/belt-and-braces keyed on a name-list; the runtime
    full-DB pin is the exhaustive, method-agnostic guarantee.
- **Discrimination:** both GREEN(inv) — the stub writes nothing and names no write method → both
  pass; a correct read-only build passes both.
- **Mutation-proof (§Instruments `patch_cli.py`):**
  - `correct` (SELECT-only via `MessageLedger.pending_traffic` + brief head/acked, no writes) →
    read-only pin + AST scan GREEN.
  - `wb_cli` (`conn.create("cli_audit", …)` + hardcoded counts) → read-only pin RED
    (`new tables: ['cli_audit']; changed: {'cli_audit': (0, 1)}`) + AST scan RED, **while the old
    `test_source_issues_no_write_verb` (constant scan) stays GREEN** — the exact F3 blindness the
    adversary named.

## F5 — C-counts monoculture (missing pin)

- **Pins:** `TestPendingReportsCounts` now has 3 scenarios via `_seed_scenario(directives, publish_
  brief)` + a shared `_assert_pending_counts` (ONE IMPLEMENTATION): A `1/1/0`, B `0/0/0`,
  C `2/2/1` (x registered before the brief was published → behind head by one version → skew=1).
- **Discrimination:** three DIFFERENT value-triples on all three axes; a build hardcoding one
  counts line reddens on a differing scenario.
- **Mutation-proof:** `correct` build → **all 3 scenarios GREEN** (satisfiability; **scenario C's
  skew=1 is REAL**, verified live — not a C-DEF trap). `wb_cli` (hardcoded `unread=1 unacked=1
  skew=0`) → scenarios B and C RED (A green — the hardcode happens to match 1/1/0).

## F6 — D8 timing-fragility (residual)

- **Pin:** `test_none_status_set_at_renders_unknown_not_a_fabricated_zero` keeps the `!= fresh`
  leg AND adds a timing-INDEPENDENT leg: the legacy (NONE) status bracket must name `"unknown"`
  OR carry NO age token (`_AGE_TOKEN = \d+[smhd]`).
- **Discrimination:** the existing `!= fresh` leg is timing-fragile (a slow render makes `fresh`
  "1s" ≠ fabricated "0s", false-clearing); the new leg reddens fabricate-zero regardless of timing.
- **Mutation-proof (§Instruments `patch_fleet.py`):**
  - `ref` (NONE → `declared: unknown`) → D7/D8/D9/D10 GREEN (D5/D6 stay RED — write-side not built
    in this render-only proof).
  - `fabzero` (NONE → `declared 0s` via `status_set_at or now`) → D8 RED.
  - **Timing-independence demonstrated** (§Instruments, using the test's real `_AGE_TOKEN`): on a
    SLOW render `!= fresh` PASSES (`[…0s]` != `[…1s]`, a false-clear) while the F6 leg is False
    (RED — catches it); a correct `declared: unknown` build → F6 leg True (green).

## F7 — ONE-IMPLEMENTATION resolver reuse (residual)

- **Choice: a MUTATION pin, not a ledger** — the adversary explicitly accepted either; a mutation
  pin is strictly stronger and the coupling was feasible without over-coupling.
- **Pin:** `test_default_resolution_routes_through_the_shared_surrealconfig` — monkeypatches
  `LoreConfig.effective_surreal_database` (a `@property`, the `surreal.database or slug` resolver
  the ruling names) to a sentinel, asserts `resolved.database == sentinel`. A resolver that ROUTES
  through it follows; a cloned yaml reader ignores the monkeypatch and stays stale.
- **Discrimination:** C-default/C-anthropic are value-only (a clone passes both, per the adversary);
  this pin turns on the SHARING itself.
- **Mutation-proof (§Instruments `patch_resolver.py`):** `correct` (routes through
  `LoreConfig.model_validate(...).effective_surreal_database`, env-free) → all 3 resolution pins
  GREEN. `clone` (hand-rolled `yaml.safe_load` + `surreal["database"]`) → **only F7 RED**
  (`ignored_if_shared` != sentinel); C-default + C-anthropic GREEN — exactly the adversary's F7
  door, now caught. (Fixture fix folded: the sentinel-database fixture value must be a valid
  `SlugStr`, so `ignored_if_shared` with underscores, not hyphens — `model_validate` validates
  `surreal.database` even when the property is patched away.)

---

## Satisfiability (whole contract, per-leg reference builds)

The legs touch independent production surfaces (`server._comms_story`/`_render_comms_story`;
`server._render_comms_fleet_row` + `agents.touch` + schema; `comms_cli.py`), so per-leg
satisfiability + no cross-leg contradiction ⇒ whole-contract satisfiable:

- **Story leg:** `patch_story.py safe` → 19/19 GREEN (F1's A2 + all F2 containment).
- **CLI counts/read-only/source leg:** `patch_cli.py correct` → 10 GREEN (all C-counts scenarios,
  read-only full-DB, AST call-scan, constant scan, coordinate-safety, C-cmd); the 3 REDs there are
  the resolver pins, greened by the resolver leg.
- **Resolver leg:** `patch_resolver.py correct` → C-default + C-anthropic + F7 all GREEN.
- **Fleet render leg:** `patch_fleet.py ref` → D4/D7/D8/D9/D10 GREEN (D5/D6 = write-side, a
  separate builder concern, adversary-confirmed solid).

No two pins contradict; the D9 pair, D6/D8 write-side, A4b, B4, #302 adjudication and the
property-keying domain trigger were NOT weakened (D8 was STRENGTHENED, not weakened). **Post-lint
leg:** the touched test files are ruff- and mypy-clean; no pin traps the builder between lint and an
un-editable file (the F7 pin's `effective_surreal_database` requirement is the RULED intent, not a
trap).

## Observation surfaced (scope law — NOT fixed)

A2's `"lead"` (creator) needle is satisfied by the coincident message SENDER (the A2 fixture's
message is sent by `lead`), so a build that renders `sender_name` but never `created_by` still
greens A2. Pre-existing, outside F1's scope (F1 was only the illegal-transition fix), and A2 is an
adversary-CONFIRMED-SOLID pin — flagged for the lead, not touched. Fix would be a distinct `created_
by`-only needle (e.g. a task created_by a NON-sender).

---

## Instruments (verbatim — brief-base §1; a measurement's instrument is a deliverable)

### `patch_story.py` — reference / WB-A / owner-leak story builds

```python
import sys
from pathlib import Path
MODE = sys.argv[1]
SERVER = Path("/home/ejprice/scratch/cf05aiii/loremaster/loremaster/server.py")

def field(name, template_key, leak_target):
    if MODE == f"leak_{leak_target}" and name == leak_target:
        return f'            lines.append(f"{template_key}: {{story.{name}}}")'
    return (f'            lines.append(str(render_line("{template_key}: {{v}}", '
            f"v=render_attributed(story.{name}))))")

HANDLER = f'''    async def _comms_story(self, *, task_id: str | None = None, thread: str | None = None, **_ignored: Any) -> Rendered:
        if task_id is None and thread is None:
            raise ValueError("story needs a task_id (or thread) to anchor on")
        anchor = str(task_id if task_id is not None else thread)
        task = await self.task_ledger.get_task(anchor)
        raw = await self.message_ledger._query(
            "SELECT seq, grade, body, refs, question, thread, sender.name AS sender_name "
            "FROM message WHERE task_id = $tid ORDER BY seq", {{"tid": anchor}})
        rows = self.message_ledger._as_rows(raw)
        messages = [StoryMessage(seq=int(r["seq"]), sender_name=str(r.get("sender_name") or "?"),
            grade=str(r.get("grade") or "signal"), body=str(r.get("body") or ""),
            refs=[str(x) for x in (r.get("refs") or [])], question=bool(r.get("question")),
            thread=str(r.get("thread") or "")) for r in rows]
        story = CommsStory(task_id=anchor, subject=task.subject, description=task.description,
            created_by=str(task.provenance.get("created_by") or ""), owner=task.owner or None,
            status=task.status, report_path=task.report_path, done_summary=task.summary, messages=messages)
        return AppContext._render_comms_story(story)

    @staticmethod
    def _render_comms_story(story: CommsStory) -> Rendered:
        lines: list[str] = [str(render_line("story: arc of task {{tid}}", tid=render_attributed(story.task_id)))]
        if story.subject:
{field("subject", "subject", "subject")}
        if story.description:
{field("description", "description", "description")}
        if story.created_by:
{field("created_by", "created_by", "created_by")}
        if story.owner:
{field("owner", "owner", "owner")}
        if story.report_path:
{field("report_path", "report", "report_path")}
        if story.done_summary:
{field("done_summary", "summary", "done_summary")}
        for m in story.messages:
            marker = " [question]" if m.question else ""
            lines.append(str(render_line("- msg #{{n}} from {{s}}{{mk}}:", n=safe_str(str(m.seq)),
                s=render_attributed(m.sender_name), mk=safe_str(marker))))
            lines.append(str(render_fenced(m.body)))
            for ref in m.refs:
                lines.append(str(render_line("  ref: {{r}}", r=render_attributed(ref))))
        return "\\n".join(lines)  # type: ignore[return-value]
'''
text = SERVER.read_text()
start = text.index("    async def _comms_story(")
end = text.index("    async def _comms_send(")
SERVER.write_text(text[:start] + HANDLER + "\n" + text[end:])
print(f"patched story: MODE={MODE}")
```

### `patch_cli.py` — correct read-only vs WB-CLI

```python
import sys
from pathlib import Path
MODE = sys.argv[1]
CLI = Path("/home/ejprice/scratch/cf05aiii/loremaster/loremaster/comms_cli.py")

CORRECT = '''def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "pending":
        import asyncio
        unread, unacked, skew = asyncio.run(_run_pending(args))
        print(f"unread={unread} unacked={unacked} skew={skew}")
        return 0
    return 2


async def _run_pending(args: argparse.Namespace) -> tuple[int, int, int]:
    from pydantic import SecretStr
    from loremaster.agents import AgentRegistry
    from loremaster.briefs import STANDING_BRIEF, BriefLedger
    from loremaster.messages import MessageLedger
    coord = dict(url=args.url, namespace=args.namespace, database=args.database,
                 user=args.user, password=SecretStr(args.password))
    registry = AgentRegistry(**coord); messages = MessageLedger(**coord); briefs = BriefLedger(**coord)
    try:
        agent = await registry.get_agent(args.agent)
        traffic = await messages.pending_traffic(agent_id=agent.id)
        try:
            head = await briefs.get_head(STANDING_BRIEF)
            acked = await briefs.acked_version(agent_id=agent.id, name=STANDING_BRIEF)
            skew = head.version - (acked or 0)
        except Exception:
            skew = 0
        return traffic.unread, traffic.unacked_directives, skew
    finally:
        await registry.close(); await messages.close(); await briefs.close()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
'''

WB_CLI = '''def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "pending":
        import asyncio
        asyncio.run(_run_pending(args)); print("unread=1 unacked=1 skew=0"); return 0
    return 2


async def _run_pending(args: argparse.Namespace) -> None:
    from pydantic import SecretStr
    from surrealdb import AsyncSurreal
    from loremaster.store._txn import bootstrap_session, signin_credentials
    conn = AsyncSurreal(args.url)
    await conn.signin(signin_credentials(user=args.user, password=SecretStr(args.password)))
    await bootstrap_session(conn, args.namespace, args.database, url=args.url)
    await conn.create("cli_audit", {"agent": args.agent, "checked": True})
    await conn.close()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
'''
text = CLI.read_text()
start = text.index("def main(argv: Sequence[str] | None = None) -> int:")
CLI.write_text(text[:start] + (CORRECT if MODE == "correct" else WB_CLI))
print(f"patched comms_cli: MODE={MODE}")
```

### `patch_fleet.py` — ref vs fabricate-zero declaration age

```python
import sys
from pathlib import Path
MODE = sys.argv[1]
SERVER = Path("/home/ejprice/scratch/cf05aiii/loremaster/loremaster/server.py")
if MODE == "fabzero":
    DECL = ('        decl = ""\n'
            '        if row.status == "input_required":\n'
            '            now = datetime.now(UTC)\n'
            '            secs = int((now - (row.status_set_at or now)).total_seconds())\n'
            '            decl = " declared " + str(AppContext._render_age(secs))\n')
else:
    DECL = ('        decl = ""\n'
            '        if row.status == "input_required":\n'
            '            if row.status_set_at is None:\n'
            '                decl = " declared: unknown"\n'
            '            else:\n'
            '                now = datetime.now(UTC)\n'
            '                secs = int((now - row.status_set_at).total_seconds())\n'
            '                decl = " declared " + str(AppContext._render_age(secs))\n')
METHOD = f'''    def _render_comms_fleet_row(
        row: Agent, *, project_head_version: int | None, acked_version: int | None,
        stale_after_s: int, heartbeat_age_s: int,
    ) -> Rendered:
        cells: list[SafeLine] = [render_join(" ", [safe_str("role"), render_attributed(row.role)])]
        if row.model is not None:
            cells.append(render_join(" ", [safe_str("model"), render_attributed(row.model)]))
        if row.task_id is not None:
            cells.append(render_join(" ", [safe_str("task"), safe_str(row.task_id[:8] + "…")]))
        brief_cell = AppContext._render_comms_fleet_brief_cell(project_head_version, acked_version)
        if brief_cell is not None:
            cells.append(brief_cell)
        if row.last_note is not None:
            cells.append(render_join(" ", [safe_str("note:"), render_attributed(row.last_note)]))
{DECL}        if heartbeat_age_s > stale_after_s:
            return render_line("- {{name}} [{{status}}{{decl}} ⚠ STALE] hb {{age}} · {{cells}}",
                name=sanitise_line(row.name), status=sanitise_line(row.status), decl=safe_str(decl),
                age=AppContext._render_age(heartbeat_age_s), cells=render_join(" · ", cells))
        return render_line("- {{name}} [{{status}}{{decl}}] hb {{age}} · {{cells}}",
            name=sanitise_line(row.name), status=sanitise_line(row.status), decl=safe_str(decl),
            age=AppContext._render_age(heartbeat_age_s), cells=render_join(" · ", cells))

'''
text = SERVER.read_text()
start = text.index("    def _render_comms_fleet_row(")
end = text.index("    @staticmethod\n    def _render_comms_fleet(")
SERVER.write_text(text[:start] + METHOD + text[end:])
print(f"patched fleet: MODE={MODE}")
```

### `patch_resolver.py` — shared SurrealConfig vs cloned yaml reader

```python
import sys
from pathlib import Path
MODE = sys.argv[1]
CLI = Path("/home/ejprice/scratch/cf05aiii/loremaster/loremaster/comms_cli.py")
CORRECT = '''def _resolve_coordinate(args: argparse.Namespace, *, config_path: Path | None = None) -> _ResolvedCoordinate:
    if args.url is not None:
        return _ResolvedCoordinate(url=args.url, namespace=args.namespace, database=args.database)
    import yaml
    from loremaster.config import LoreConfig
    config = LoreConfig.model_validate(yaml.safe_load(Path(config_path).read_text()))
    return _ResolvedCoordinate(url=config.surreal.url, namespace=config.surreal.namespace,
                               database=config.effective_surreal_database)


'''
CLONE = '''def _resolve_coordinate(args: argparse.Namespace, *, config_path: Path | None = None) -> _ResolvedCoordinate:
    if args.url is not None:
        return _ResolvedCoordinate(url=args.url, namespace=args.namespace, database=args.database)
    import yaml
    payload = yaml.safe_load(Path(config_path).read_text())
    surreal = payload["surreal"]
    return _ResolvedCoordinate(url=surreal["url"], namespace=surreal["namespace"],
                               database=surreal.get("database"))


'''
text = CLI.read_text()
start = text.index("def _resolve_coordinate(")
end = text.index("def main(")
CLI.write_text(text[:start] + (CORRECT if MODE == "correct" else CLONE) + text[end:])
print(f"patched resolver: MODE={MODE}")
```

### F6 timing-independence demonstration (verbatim, uses the test's real `_AGE_TOKEN`)

```python
import sys
sys.path.insert(0, "loremaster/tests")
from test_comms_status_age import _AGE_TOKEN
def f6_leg(cell):                      # the F6 assertion
    return ("unknown" in cell.lower()) or (not _AGE_TOKEN.search(cell))
def neq_fresh(legacy, fresh):          # the pre-existing D8 leg
    return legacy != fresh
# SLOW (>1s) render + fabricate-zero — the case F6 exists for:
print(neq_fresh("[input_required declared 0s]", "[input_required declared 1s]"))  # True  = != fresh MISSES
print(f6_leg("[input_required declared 0s]"))        # False = F6 CATCHES
print(f6_leg("[input_required declared: unknown]"))  # True  = correct build greens
```
Observed: `!= fresh` PASSES (True, false-clear) while the F6 leg CATCHES (False = RED); a correct
`unknown` build greens the F6 leg.

## Writable set touched
`loremaster/tests/test_comms_story.py`, `loremaster/tests/test_comms_status_age.py`,
`loremaster/tests/test_comms_cli.py`. No production code edited (the builder greens it after
re-grade). No sibling test file edited.
