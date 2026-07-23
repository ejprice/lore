brief-base v6 read

# REPORT — builder-03a1 · FOLLOW-UP (operator decision pool #24: message id → ULID)

> The main 03a-1 build report is committed/archived at
> `docs/plans/v2/receipts/2026-07-23-packet03a1/REPORT-builder-03a1.md` (commit `d2ba0d7`),
> and 03a-1 itself is committed (`e6b9b81` messages.py · `0cff06d` seam registration ·
> `42eeedc` C-DEF fix / finding #173 · `a05a3e9` INDEX DONE). THIS file is only the
> pool-#24 ULID follow-up on top of that committed work.

## SUMMARY BLOCK
- state: **done** (ULID applied; all gates green; not committed — lead cold-audits + commits).
- change (messages.py only): `message.id` mint `uuid4().hex` → **real ULID** `str(ULID())` (`python-ulid==4.0.1`), CLIENT-side, bare, 26-char Crockford, time-sortable.
- deviation (flag): the dependency was relocated from the **workspace root** `pyproject.toml` (where `uv add` from the repo root put it) to **`loremaster/pyproject.toml`** — the repo convention (every loremaster third-party dep lives there; `messages.py` is a loremaster module). Root restored to zero-diff. No deployment gap either placement (image = `uv sync --locked` over the workspace, #141). Revertable if you wanted root.
- decisions-needed: none (unless you specifically want the dep at the workspace root).
- receipts: bareness pin 2 passed (both legs) · full contract 140 passed / 31 red (03a-2 stubs) / 9 skipped (no regression) · ruff clean · messages.py mypy 0 (total unchanged, 36) · diffs below.

## 1. The change (messages.py)
- **API verified by reading the installed package** (packages-over-hand-rolling — confirm it does the job, nothing hand-rolled): `from ulid import ULID`; `str(ULID())` → **bare** (`':' not in str`), **26-char** Crockford, **lexicographically time-sortable** (`str(ULID()) < str(ULID())` for a later mint — [PROBED 2026-07-23]). Matches the contract's stated intent (`id: str # bare ulid`) and pkt-05's future `since=` cursor.
- `message_id = uuid4().hex` → `message_id = str(ULID())`; removed `from uuid import uuid4`, added `from ulid import ULID`; kept CLIENT-side (before the RELATE fan-out — binds directly as the `in` endpoint; the `execute_transaction` is UNCHANGED, no server-side `ulid()`). One docstring word (`bare hex id`→`bare ULID`). `_message_fakes.py` untouched (its own id mint; no pin checks ULID format — the fake leg is unaffected).

## 2. Dependency placement (DEVIATION from the literal instruction — flagged)
`uv add python-ulid` run from the repo root added it to the **virtual workspace-root** `pyproject.toml`. That is off-convention: `loremaster`'s other third-party deps (surrealdb, pydantic, pyyaml, httpx, mcp, watchdog) are all declared in `loremaster/pyproject.toml`, and `messages.py` is a `loremaster` module. I `uv remove`d it from root (restored the root to a clean virtual root — **zero diff**) and `uv add --package loremaster`ed it into `loremaster/pyproject.toml`. **No deployment gap either way** — the Containerfile installs via `uv sync --locked` over the whole workspace (finding #141), which installs both root and member deps — but per-package declaration is the correct hygiene and matches the repo (and survives a hypothetical standalone `loremaster` install). If you specifically wanted the workspace-root placement, one command moves it back.

## 3. Receipts
- `test_the_message_id_is_BARE_with_no_table_prefix` (`-n0`, :18000): **2 passed** (both `[real]` and `[fake]`).
- Full `test_message_ledger.py` (`-n auto`, :18000): **`31 failed, 140 passed, 9 skipped`** — identical to the pre-ULID post-C-DEF-fix state; the 31 red are the same 03a-2 `NotImplementedError` stubs (13 ack + 18 awaiting_answer). No regression, no new red.
- `ruff check .`: **All checks passed!**
- `scripts/typecheck.sh`: `messages.py` **0 errors**; total **36** (unchanged — `python-ulid` ships `py.typed`; no ULID-related error).
- Diffs (`git diff`): root `pyproject.toml` = **no diff**; `loremaster/pyproject.toml` = `+ "python-ulid>=4.0.1",`; `uv.lock` = +python-ulid (11 lines); `messages.py` = uuid4→ULID (import + mint + 1 docstring word), 3 files / +20 −3.

## 4. Not committed
Working tree (yours to cold-audit + commit): `M loremaster/loremaster/messages.py`, `M loremaster/pyproject.toml`, `M uv.lock`. Suggested one-concern commit: `feat(comms): message.id is a real ULID (pool #24) + declare python-ulid on the loremaster package`. No deploy, :18000 only.
