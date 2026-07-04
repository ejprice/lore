# P8a Eval Baseline — LIVE pre-flip MCP surface

**Date**: 2026-07-04
**Ledger task**: P8a-9 (`cf6f84a0e05a496da66b0b649147f9c6`), owner `eval-baseline`
**Purpose**: re-measured (not reused) accuracy/tool-call/token receipts against the
live, pre-P8a lore-lore MCP server, to gate P8d's later A/B comparison.

## Headline numbers (run 3 — the valid baseline; see "Run audit trail" below)

| Metric | Value |
|---|---|
| **Accuracy** | **11/11 (100.0%)** |
| **Average tool calls per task** | **5.45** |
| **Average response (output) tokens per task** | **1447.1** |
| Average input tokens per task (supporting detail, not a headline ask) | 112,756.6 |
| Average task duration | 74.91s |
| Total tool calls | 60 |
| Total response (output) tokens | 15,918 |

## Serving endpoint & image provenance

- **Endpoint**: `http://127.0.0.1:9202/mcp` (container `lore-lore`, image `localhost/lore:latest`)
- **Image id**: `620588e53b2b474cea3eaa421ca1c52ca5021cbf07c7bd59b1d841c185827c03`
- **Image created**: 2026-07-04 15:12:09 UTC (2026-07-04 11:12:34 -0400)
- **Container created**: 2026-07-04 11:12:34 -0400 (`podman inspect lore-lore`)
- **Commit correlation**: image build/container-create timestamp lands 34s after
  commit `c5a71b6` ("feat(map): re-denominate the default budget 1500 → 2500",
  authored 2026-07-04 11:12:00 -0400) and 20 minutes before `2339025` ("docs(design):
  P8 decomposition rationale", 11:32:09 -0400, a docs-only commit that would not
  have triggered a rebuild anyway). This confirms the served image is the
  **c5a71b6-era, pre-P8a surface** — exactly the "before" baseline P8d needs.
- Live tool count confirmed via smoke test: **16 tools** (`lore_search_code`,
  `lore_read_file`, `lore_get_symbol`, `lore_save_memory`, `lore_recall_memory`,
  `lore_claim_task`, `lore_tasks`, `lore_reindex`, `lore_index_status`,
  `lore_what_imports`, `lore_blast_radius`, `lore_tests_for`, `lore_references`,
  `lore_dead_code`, `lore_impact`, `lore_map`).

## Harness provenance + exact command

- **Source**: `~/.claude/skills/mcp-builder/scripts/evaluation.py` (mcp-builder
  skill, Phase-4 evaluation harness) + its sibling `connections.py`. Neither
  file in the skill directory was modified.
- **Pinned copy for reuse**: [`docs/eval/evaluation_harness_p8a.py`](evaluation_harness_p8a.py)
  + [`docs/eval/connections_p8a.py`](connections_p8a.py) (the latter is a
  byte-identical, unmodified copy — confirmed via `diff` against the skill's
  original — vendored only because it's a load-bearing sibling import).
  **P8d's A/B gate MUST reuse these exact two files and the exact pinned
  model below**, not a fresh copy from the skill dir, so the comparison is
  apples-to-apples against this baseline.
- **Environment**: dedicated `uv`-built venv in scratch space (not the
  project's `.venv`), deps installed from
  `~/.claude/skills/mcp-builder/scripts/requirements.txt` (`anthropic>=0.39.0`,
  `mcp>=1.1.0`; resolved to `anthropic==0.116.0`, `mcp==1.28.1`).
- **Exact command (run 3, the valid baseline)**:
  ```sh
  cd /home/ejprice/PycharmProjects/lore
  export ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=' /home/ejprice/docker/mcp/.env | cut -d= -f2-)
  <evalvenv>/bin/python docs/eval/evaluation_harness_p8a.py \
    -t http -u http://127.0.0.1:9202/mcp \
    -m claude-sonnet-4-5-20250929 \
    -o <out>/p8a_baseline_report_v2.md \
    loremaster/evaluation.xml
  ```
  (During the actual run the script executed from the scratch copy path
  before being promoted into `docs/eval/`; command shown above is the
  reuse-ready equivalent pointing at the now-committed path.)

## Model used

**`claude-sonnet-4-5-20250929`** — NOT the script's original hardcoded default.

The stock script defaults to `claude-3-7-sonnet-20250219`, which is **retired**:
a live `GET https://api.anthropic.com/v1/models` call against this account
confirms it is absent from the model list entirely, and run 1 (below) failed
immediately with `anthropic.NotFoundError: 404 - model: claude-3-7-sonnet-20250219`.
Of the account's currently available models, `claude-sonnet-4-5-20250929` was
selected as the replacement: the newest **dated/pinned** Sonnet snapshot (as
opposed to undated rolling aliases like `claude-sonnet-5` / `claude-sonnet-4-6`,
which could silently point at a different model between this baseline and
P8d's later A/B run — pinning matters more here than chasing the newest
alias). Same tier (Sonnet) as the original default, preserving cost/capability
parity with the harness's original design intent.

**P8d must use this same model id.**

## QA-pair count — GROUND-TRUTH FLAG

`loremaster/evaluation.xml` contains **11** `<qa_pair>` elements
(`grep -c "<qa_pair" loremaster/evaluation.xml` → `11`), added in commit
`f9aa09a` and never amended since. The project plan / resume docs refer to
"the 23-pair harness." **That figure is stale/wrong** — there is no 23-pair
version of this file in the repo's history at HEAD. This baseline runs
against the actual 11-pair file; the discrepancy is flagged here for the
operator to reconcile (planning doc vs. reality), not resolved unilaterally.

## Per-task table (run 3)

| # | Question topic | Correct | Tool calls | Tool breakdown | Input tokens | Output tokens | Duration |
|---|---|---|---|---|---|---|---|
| 1 | Startup-gate exception class name | ✅ | 4 | search_code×3, read_file×1 | 66,677 | 1,072 | 64.86s |
| 2 | Once-per-process lifespan lease class | ✅ | 2 | search_code×1, get_symbol×1 | 33,740 | 787 | 25.44s |
| 3 | Embedding-bisect combine helper — # of None-return conditions | ✅ | 11 | search_code×6, read_file×3, tests_for×1, references×1 | 289,154 | 2,408 | 261.42s |
| 4 | Indexer's chunk-model import module path | ✅ | 6 | search_code×2, read_file×3, get_symbol×1 | 97,333 | 1,571 | 89.32s |
| 5 | Vector-point key-version constant value | ✅ | 11 | search_code×5, read_file×5, get_symbol×1 | 210,495 | 1,836 | 91.78s |
| 6 | Per-request max input-text count (HTTP 413 cap) | ✅ | 7 | search_code×5, read_file×2 | 195,680 | 1,710 | 52.78s |
| 7 | Max backoff-delay cap (seconds) | ✅ | 3 | search_code×2, read_file×1 | 56,947 | 1,100 | 29.01s |
| 8 | Memory collection name for slug "myrepo" | ✅ | 8 | search_code×4, read_file×4 | 131,699 | 1,899 | 68.86s |
| 9 | Sole non-test importer of the backend-selecting factory | ✅ | 3 | search_code×1, what_imports×1, read_file×1 | 43,990 | 1,295 | 46.35s |
| 10 | Test file covering the startup dimension/reachability gate | ✅ | 2 | search_code×1, tests_for×1 | 66,780 | 1,257 | 46.85s |
| 11 | Committed pinned tokenizer filename | ✅ | 3 | search_code×2, read_file×1 | 47,828 | 983 | 47.33s |
| **Σ/avg** | | **11/11** | **60 / 5.45 avg** | | **1,240,323 / 112,756.6 avg** | **15,918 / 1,447.1 avg** | 74.91s avg |

(Ground-truth answers and the model's exact `<response>` text for each task
are reproduced verbatim in
[`docs/eval/2026-07-04-p8a-baseline-raw.md`](2026-07-04-p8a-baseline-raw.md),
including full per-task `<summary>`/`<feedback>` transcripts.)

## Run audit trail — 3 runs, only run 3 is the baseline

| Run | Model | Outcome | Root cause |
|---|---|---|---|
| 1 | `claude-3-7-sonnet-20250219` (stock default) | Crashed on task 1/11, 0 tasks completed | Model retired: `anthropic.NotFoundError: 404 - model: claude-3-7-sonnet-20250219`. Confirmed independently via `GET /v1/models` (absent from account's model list). No API tokens wasted beyond one failed call. |
| 2 | `claude-sonnet-4-5-20250929` | Completed all 11 tasks, **0/11 (0.0%) accuracy** | **Harness bug, not a lore-server defect.** `MCPConnection.call_tool()` (in the stock `connections.py`) returns `result.content`, which for every real MCP server is `list[mcp.types.TextContent]` — pydantic objects, not JSON-serializable. The stock script's `json.dumps(tool_result) if isinstance(tool_result, (dict, list)) else str(tool_result)` therefore threw `TypeError: Object of type TextContent is not JSON serializable` on **every single tool call** (verified live via a direct `call_tool` + `json.dumps` repro, independent of the harness). The surrounding `try/except` swallowed this into a fabricated `"Error executing tool ..."` message fed back to the model on every turn, so the model — seeing identical fake errors from all 16 tools across all 11 tasks — reasonably answered `NOT_FOUND` every time. This is a defect in the **stock, unmodified mcp-builder `evaluation.py`/`connections.py`** that would break against *any* real MCP server returning standard `TextContent`, not something specific to lore. Full per-task transcripts of this run are not committed (superseded by run 3) but are reproducible from the log if needed. |
| 3 | `claude-sonnet-4-5-20250929` | Completed all 11 tasks, **11/11 (100.0%) accuracy** | **This is the baseline.** Ran with the bug from run 2 fixed in a scratch copy (`_serialize_tool_result()`, extracting `.text` off each content block instead of `json.dumps`-ing pydantic objects), extended with per-task token capture. See `docs/eval/evaluation_harness_p8a.py` module docstring for the full diff rationale against the stock script. |

**Note on scope of the fix**: per the packages-over-hand-rolling / "extend a
copy, never modify the source" discipline, the actual skill file at
`~/.claude/skills/mcp-builder/scripts/evaluation.py` was **never touched** —
only the scratch copy (now promoted to `docs/eval/evaluation_harness_p8a.py`)
was patched. Whether to report the upstream bug against the mcp-builder skill
itself is an operator/team-lead call, raised separately, not resolved here.

## Concurrency note (per brief)

Other agents were editing repo source files concurrently with this run. The
live container serves a **baked image** (confirmed via `podman inspect` —
image built ~34s after `c5a71b6`), so tool *behavior* was stable throughout.
The server's live watcher does reindex edited workspace files in the
background, but scanning all 11 per-task `<summary>`/`<feedback>` transcripts
in the raw report, **no task showed a "rebuilding"/stale-index notice
influencing an answer**. (One transcript, task 2, mentions a class that
itself "tracks currently live sessions and rebuilds when needed" — that is
the model describing `_ProcessLifespanGuard`'s own runtime behavior, the
subject of the question, not a tool-emitted staleness warning about the
index.)

## Token-capture method

The stock `evaluation.py` captures **zero** token usage. The pinned copy adds
`_accumulate_usage()`, which sums
`usage.{input_tokens,output_tokens,cache_creation_input_tokens,cache_read_input_tokens}`
across **every** Claude API call made while servicing one `qa_pair` — the
initial `messages.create` plus every subsequent tool-result round trip in the
same agent loop — since a task's real cost has no coarser natural boundary
than the sum of all API calls it triggers. "Average response tokens per
task" in this report is the accumulated `output_tokens` per task, averaged
across all 11 tasks. This was directly obtainable (not a proxy) — no token
metric gap to report.

## Notes / gaps

- **No persistent per-task failures** in run 3 — all 11 tasks answered, all
  correct, zero tool-call errors.
- **No stale-index notices** observed influencing any answer (see
  Concurrency note above).
- **Token-capture** was directly measurable; no proxy needed.
- **Harness bug** (run 2, 0/11) is the most consequential finding of this
  task and is surfaced above, in `REPORT-eval-baseline.md`, and directly to
  the team-lead — not buried.
- This run is **read-only** against the live server; no container was
  stopped, restarted, or reconfigured.
