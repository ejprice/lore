# REPORT-fixer-04b5-ruff

brief-base v10 read
brief project v7 read

## SUMMARY
- state: **done**
- Made the two packet-04b5 CONTRACT TEST files ruff-clean (87 pre-existing style errors → 0). No test LOGIC or behaviour changed.
- deviations: (1) A few structural `# noqa` lines on LONG `def` signatures exceed 110 chars (e.g. `_served_error_door_sites` at 137). Ruff EXEMPTS a line whose overflow is a trailing `# noqa` directive, so they do not trip E501 — confirmed by `All checks passed`. Reasons kept terse; ≤110 unattainable on an 81–83-char signature without a meaningless reason.
- Packages considered: none — no mechanism specified (pure style fix).
- Graded: 4fc9f7a · HEAD-at-report: 4fc9f7a · SAME
- decisions-needed: none for THIS task. FLAG (unrelated, pre-existing): `scripts/typecheck.sh` is RED at HEAD — 191 mypy errors, ALL in the auth/posture/roster subsystem (`test_auth_*`, `test_posture`, `test_roster_parser`, `_auth_fixtures`, …). ZERO are in my two files. Not introduced by this wave; surfaced for the lead.
- receipt POINTERS: commit 4fc9f7a · gate tails in §Gates below.

## WHAT CHANGED (file:concern)
Two files edited, nothing else (`git diff --name-only` == exactly these two):
- `loremaster/tests/test_link5_render_containment.py` — 64 E501 code-wraps + 1 over-long comment wrapped + 8 structural noqa + share of the 14 autofix.
- `loremaster/tests/test_task_read_surface.py` — 1 PLR0402 autofix (import de-alias + reorder).

### The 87 errors, by class
- **14 autofix** (`ruff check --fix`): 10 PLR0402 (`import loremaster.x as x` → `from loremaster import x`), 2 I001 (import-block sort), 1 F401 + 1 F811 (a redundant local `import inspect` in `test_the_charset_gated_half_is_the_link1b_validated_set` removed; the method now resolves `inspect` from the module-level import that F401 flagged — that import becomes USED, clearing both. Behaviour identical: module-level import binds at import time, method runs long after). Diff previewed with `--fix --diff` before applying.
- **65 E501** (line-too-long >110): manually wrapped. All 65 are pure CODE in the `_probes()` render-registry (long `_served(...)` / `model_construct(...)` calls) — NO asserted string literals, so wrapping at commas/parens is behaviour-preserving. Converted each over-long call to canonical expanded form; one over-long inline comment split across two lines. Did NOT use `ruff format` — it reflows the whole hand-authored file (1248 lines / probe table 241→851), destroying the intentional compact layout of the short probes.
- **8 structural** (`# noqa: <code> — reason`, per brief — inherent to the reach-net/AST instruments, not refactored): 4 PLW0603 (module-level lazy caches / the over-drive reach accumulator), 3 PLR0912 (AST node-shape dispatch — `_served_error_door_sites`, `_fstrings_all_error_routed`, `_raw_render_interpolations`), 1 PLR0911 (`_typed_default` return-per-type dispatch).

## GATES (all three hold)
- `uv run ruff check <both files>` → **All checks passed!**
- `uv run pytest <both files> -q -n auto` → **251 passed, 1 skipped** (baseline before edits: 251 passed, 1 skipped — IDENTICAL, so no behaviour moved).
- `scripts/typecheck.sh`: my two files contribute **0** mypy errors (`grep -c` over full output = 0). typecheck.sh's overall RED is 191 pre-existing errors in the auth/posture subsystem — unrelated to packet 04b5; see the decisions-needed FLAG.

## COMMIT
`4fc9f7a` — `style(04b5): ruff-clean the render-reach contract test files (65 E501 wraps + 8 structural noqa + 14 autofix)`, explicit pathspec naming ONLY the two files (#191).

## lore-tool honesty
Used lore MCP (registered `fixer-04b5-ruff`, drained inbox — empty). Ruff/mypy/pytest line-and-count work is non-symbol textual/gate work (grep/awk honest per CLAUDE.md dogfood case b/a), not a code-structure question — so no lore_search fallback to disclose.
