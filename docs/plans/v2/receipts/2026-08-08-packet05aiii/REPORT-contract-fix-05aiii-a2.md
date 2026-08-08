# REPORT-contract-fix-05aiii-a2 — A2 creator/sender monoculture (adversary residual)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State: done.** The SOLE surviving adversary residual (REPORT-adversary-05aiii-2.md §A2)
  is closed and MUTATION-PROVEN. One TEST file touched; no production code changed.
- **The fix (two lines, one concern):** in A2
  (`test_story_renders_subject_creator_owner_messages_and_report_path`) the task's
  `created_by="lead"` **==** the message sender `"lead"` — so the `"lead"` creator needle was
  satisfiable by rendering EITHER field. Changed `created_by="lead"` → `"planner"` (a
  NON-sender value; sender stays `"lead"`) and the `"lead"` creator needle → `"planner"`. A2
  now discriminates "renders created_by" from "renders the sender".
- **Mutation-proof (scratch, provenance-verified):** a `no_created_by` wrong build (renders
  the message SENDER, never reads `task.created_by`) → **BEFORE fix A2 PASSES** (the hole),
  **AFTER fix A2 REDS** (`'planner' missing`, whole story file 1 failed/18 passed — only A2).
  A `correct` build (renders created_by) → A2 GREEN. Control (orig fixture + correct) → GREEN
  (probe sees both directions). §Mutation-proof.
- **Gates:** ruff `All checks passed`; mypy `./scripts/typecheck.sh` → zero lines mention the
  touched file (191 pre-existing = 89+102, the auth-WIP #333 branch baseline, untouched);
  pytest `test_comms_story.py` against the stub → **3 failed / 16 passed** (A2/A3/A5 the still-
  RED behavioural pins; A2 fails BEHAVIOURALLY on the stub header, not at setup) — zero new
  failures, other pins unchanged. §Gates.
- **Files touched:** ONLY `loremaster/tests/test_comms_story.py` (7 insertions / 2 deletions).
  `git status` confirms no other tracked change. §Diff.
- **Packages considered:** none — test-fixture change, no NEW mechanism specified.
- **Graded:** authored + verified against `dc54bbd` · committed as `4dc2949` ·
  HEAD-at-report `4dc2949` (this fix's own commit; the only move from the graded base).
  Store spike-surreal `:18000` ONLY; `:18500` never touched. Scratch
  `loremaster.__file__` = `/home/ejprice/scratch/cf05aiii-a2/loremaster/loremaster/__init__.py`.
- **Deviations:** none. (Added a 5-line explanatory comment beside the needle documenting the
  discrimination + the adversary residual it closes — in-scope documentation of the fix.)
- **Decisions-needed:** none. This was the last contract touch before the builder.
- **Receipt pointers:** exact diff §Diff · mutation-proof legs §Mutation-proof · gate output
  §Gates · patcher (verbatim) §Instrument.

---

## Diff (the exact change — `git diff loremaster/tests/test_comms_story.py`)

```diff
@@ A2 fixture: task.created_by @@
-            "reticulate the splines", "the long description", created_by="lead"
+            "reticulate the splines", "the long description", created_by="planner"
@@ A2 creator needle @@
-            "lead",  # creator
+            # created_by is "planner" — a NON-sender value. The message sender is
+            # "lead", so this needle discriminates "renders created_by" from
+            # "renders the sender": a build that emits sender-in-place-of-creator
+            # (never reading task.created_by) reddens here. Adversary residual
+            # (REPORT-adversary-05aiii-2.md §A2) — the creator/sender monoculture.
+            "planner",  # creator (distinct from the "lead" message sender)
```

The message sender remains `sender=lead` (a registered agent). `created_by` is a plain
provenance string with NO registration validation (`TaskLedger.create_task` records it
straight into `provenance` — verified via `lore_get_symbol`), so `created_by="planner"`
cannot reintroduce a setup-crash C-DEF trap (the exact class F1 fixed). `"planner"` appears
in NO other rendered field (subject / owner / report_path / done_summary / sender / body),
so a build that never renders `created_by` cannot satisfy the needle by coincidence.

---

## Mutation-proof (the residual is real; the fix closes it)

Scratch copy built via `scripts/scratch_copy.sh /home/ejprice/scratch/cf05aiii-a2`,
provenance-asserted (`loremaster.__file__ =
/home/ejprice/scratch/cf05aiii-a2/loremaster/loremaster/__init__.py`, printed on the run).
Store spike-surreal `:18000`. The wrong build `no_created_by` renders each message line's
SENDER via `render_attributed` and omits `task.created_by` entirely — the exact door the
monoculture let through. `correct` renders `created_by`. The A2 fixture is toggled between
the committed pre-fix HEAD version (`created_by="lead"`, needle `"lead"`) and my fixed
version (`created_by="planner"`, needle `"planner"`).

| leg | A2 fixture | story render build | A2 result | reads as |
|---|---|---|---|---|
| 1 | orig (`created_by="lead"`) | `no_created_by` | **1 passed** | THE HOLE — sender `lead` satisfies the old `"lead"` needle |
| 2 | fixed (`created_by="planner"`) | `no_created_by` | **1 failed** (`'planner' missing`) | HOLE CLOSED — sender ≠ creator |
| 2b | fixed | `no_created_by` (whole file) | **1 failed / 18 passed** | fix reddens EXACTLY A2, not wholesale |
| 3 | fixed | `correct` | **1 passed** | satisfiable — a build that renders created_by greens A2 |
| 4 (control) | orig | `correct` | **1 passed** | probe sees both directions |

Leg-2 RED evidence (the render emitted the sender, never the creator):
```
E  AssertionError: story must reconstruct the task arc; 'planner' missing from:
   'story: arc of task ```…```\nsubject: ```reticulate the splines```\n
    owner: ```worker```\nreport: ```…/REPORT-worker.md```\nsummary: ```splines reticulated```\n
    - msg #0 from ```lead```:\n```\nstarting on it now\n```'
```
The render contains `msg #0 from ```lead``` ` (sender) and every other arc field, but **no
created_by line** — so `"planner"` is absent. BEFORE the fix (leg 1) that identical build
passed, because the render's sender `"lead"` matched the old `"lead"` needle. This is the
QUANTIFIER-LAW monoculture (the invariant asserted on the one fixture value where
creator == sender), now ∀-discriminating.

Positive controls: leg 4 shows a `correct` build greens A2 even on the ORIGINAL fixture
(the probe is not stuck-red); leg 2b shows only A2 reds under the wrong build (the fix does
not fail wholesale). BEFORE-vs-AFTER on the SAME wrong build (leg 1 PASS → leg 2 RED) is the
discrimination the fix installs.

---

## Gates (real tree, my final edit, against the stub)

- **ruff** `uv run ruff check loremaster/tests/test_comms_story.py` → **All checks passed!**
  (exit 0).
- **mypy** `./scripts/typecheck.sh` → **no line mentions `test_comms_story`** (zero new
  errors on the touched file). Pre-existing branch baseline `Found 89 … / Found 102 …` = 191
  (auth-WIP #333), unchanged by a string-literal + comment edit.
- **pytest** `uv run pytest loremaster/tests/test_comms_story.py -q -n auto` against the
  current stub → **3 failed, 16 passed**. The 3 RED are the still-unbuilt behavioural pins:
  A2 (`…subject_creator_owner_messages_and_report_path`), A3
  (`…question_message_is_marked…`), A5 (`…hostile_message_body_is_fenced_verbatim`). A2 fails
  BEHAVIOURALLY — `AssertionError: … 'reticulate the splines' … (stub — lineage not yet
  reconstructed)` (the stub renders only a header, so the first needle already fails) — NOT
  at setup. Matches the story leg's baseline (3 red / 16 pass = 19); zero new failures, all
  other story pins unchanged. Satisfiability receipt (every RED pin fails behaviourally)
  holds.

---

## Scope / hygiene

- Touched ONLY `loremaster/tests/test_comms_story.py`. `git status --porcelain` shows a single
  ` M` on that file; the `??` REPORT-*.md at root are pre-existing untracked sibling reports,
  not mine, not staged.
- No production code changed; no sibling test file changed; no other A2 pin re-opened; no
  scope added (the brief's "minimal, last touch before builder" honoured).
- Scratch trees `/home/ejprice/scratch/cf05aiii-a2` (scratch_copy) and
  `/home/ejprice/scratch/cf05aiii-a2-probes` (patcher) remain on disk — disposable
  scratch_copy dirs, NOT git worktrees. Operator's call whether to reap them.

## Instrument (verbatim — brief-base §1; the mutation-proof's patcher)

`patch_story.py` splices ONE story render into the scratch `server.py` (between the
`_comms_story` and `_comms_send` anchors), restoring from a pristine `.orig` first. Reference
build assembled from the shipped `render_attributed` / `render_fenced` / `render_line` seams
(independent of any author patcher). Reproduce any row above with
`python patch_story.py {correct|no_created_by}` then the pytest node.

```python
import sys
from pathlib import Path

MODE = sys.argv[1]
SERVER = Path("/home/ejprice/scratch/cf05aiii-a2/loremaster/loremaster/server.py")
ORIG = SERVER.with_suffix(".py.orig")
if not ORIG.exists():
    ORIG.write_text(SERVER.read_text())

# The created_by render line — present in `correct`, absent in `no_created_by`.
CREATED_BY = (
    '        if story.created_by:\n'
    '            lines.append(str(render_line("created_by: {v}", '
    'v=render_attributed(story.created_by))))\n'
    if MODE == "correct"
    else ""  # WRONG build: created_by never rendered
)

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
            lines.append(str(render_line("subject: {{v}}", v=render_attributed(story.subject))))
{CREATED_BY}        if story.owner:
            lines.append(str(render_line("owner: {{v}}", v=render_attributed(story.owner))))
        if story.report_path:
            lines.append(str(render_line("report: {{v}}", v=render_attributed(story.report_path))))
        if story.done_summary:
            lines.append(str(render_line("summary: {{v}}", v=render_attributed(story.done_summary))))
        for m in story.messages:
            marker = " [question]" if m.question else ""
            lines.append(str(render_line("- msg #{{n}} from {{s}}{{mk}}:", n=safe_str(str(m.seq)),
                s=render_attributed(m.sender_name), mk=safe_str(marker))))
            lines.append(str(render_fenced(m.body)))
            for ref in m.refs:
                lines.append(str(render_line("  ref: {{r}}", r=render_attributed(ref))))
        return "\\n".join(lines)  # type: ignore[return-value]
'''

text = ORIG.read_text()
start = text.index("    async def _comms_story(")
end = text.index("    async def _comms_send(")
SERVER.write_text(text[:start] + HANDLER + "\n" + text[end:])
print(f"patched story render: MODE={MODE}")
```

Test-file toggle: `test_orig.py` = `git show HEAD:loremaster/tests/test_comms_story.py`
(pre-fix), `test_fixed.py` = the working-tree file (my fix); `cp` one over the scratch test
file per leg. The whole-file leg used `pytest … -n auto`; single-node legs used the A2 id.
