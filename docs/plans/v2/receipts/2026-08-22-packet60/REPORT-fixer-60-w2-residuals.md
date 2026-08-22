# REPORT-fixer-60-w2-residuals

brief-base v14 read
brief project v7 read

## SUMMARY
- state: **done**
- deviations: none
- Packages considered: none — no mechanism specified (test-only assertion tightens)
- Reuse ledger: none — no new reusable symbols (two edits add function-local vars `prog_prefix` / `body` only)
- scope: edited ONLY `loremaster/tests/test_keeps_cli.py` (2 residual tightens, R-A + R3). No production code, no other tests.
- gates: `uv run ruff check loremaster/tests/test_keeps_cli.py` → clean; `uv run pytest -n auto loremaster/tests/test_keeps_cli.py` → **47 passed in 5.99s**.
- HEAD at report: `5b7180c` (uncommitted — the lead commits with the wave-2 `feat(60)`; `test_keeps_cli.py` is still untracked `??`).
- receipt pointers: R-A tighten → `test_create_keep_dm_with_a_name_is_rejected` (the `body`-strip check); R3 → the 3 `f"{p_module._CLI_PROG}:" in err` sites (`TestAdversarySetRankErrorPath`, `test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero`, `TestANonexistentKeepIsLoudForEveryKeepConsumingVerb::test_a_nonexistent_keep_is_a_loud_exit_1`); discrimination/honesty proof below (§Proofs).
- decisions-needed: none.

## R-A — the degenerate `dm`-substring check (FIXTURES-MUST-DISCRIMINATE)

**Where:** `TestCreateKeepPerTypeNameRule::test_create_keep_dm_with_a_name_is_rejected`.

**Defect:** the content check was `assert "name" in err.lower() and "dm" in err.lower()`. The
launder prefix is `lore-adm:` and `"dm"` is a substring of it (`…a-`**`dm`**`…`), so `"dm" in
err.lower()` is TRUE for **any** message — the pin never verified the body names the type. (The
`"name"` half is also partly prefix-satisfiable via `--name` elsewhere, but `dm` is the load-bearing
degeneracy.)

**Real production message** (verified by reading `loremaster.principals._cmd_create_keep`):
`--name is not valid for --type dm (a dm keep has no name concept)`, laundered by `_dispatch_keep`
to `f"{_CLI_PROG}: {error}"` → `lore-adm: --name is not valid for --type dm (a dm keep has no name concept)`.

**Fix (before → after):**
- before: `lowered = err.lower(); assert "name" in lowered and "dm" in lowered`
- after: strip the launder prefix first, then check the BODY —
  `prog_prefix = f"{p_module._CLI_PROG}: "`; `assert err.startswith(prog_prefix)` (kept — this is a
  clean dispatch-level `ValueError`, single line, no store rejection); `body = err[len(prog_prefix):].lower()`;
  `assert "name" in body and "dm" in body`. A comment records WHY (so a future reader does not
  "tighten" it back into the degenerate whole-line form).

The `"name"`/`project`/`team` reject pins were **not** weakened: `"project"`/`"team"` are not substrings
of `lore-adm:`, so `test_create_keep_without_name_is_rejected_for_name_requiring_types` is already
honest and is left as-is.

**Passes on the real message; reddens on the degenerate case** — see §Proofs (old check false-passes a
body that never names dm; new check reddens).

## R3 — `startswith` is a test-env fiction on STORE-rejection paths (finding #401)

**Mechanism (verified against `loremaster/loremaster/keeps.py`):** on a genuine engine rejection the
shared `run_query` seam (`keeps.py::KeepStore._query`, `label="keep.query.rejected"`) logs a structured
line to stderr via `logging.lastResort` BEFORE `_dispatch_keep` prints the `lore-adm:` teaching line —
so real prod stderr does **not** `startswith("lore-adm:")`. pytest strips that log line, so `startswith`
is green in-suite but pins a property FALSE in prod. Fix: `err.startswith(f"{...}:")` →
`f"{...}:" in err` (honest on both the clean suite line and the dirty prod line), on the store-rejection
pins only. Each carries a comment citing #401.

**Classification is empirical** — traced each error path in `keeps.py` to whether the engine rejects a
statement (→ `keep.query.rejected` log line in prod) or the store raises in Python (clean single line):

Changed to `f"{p_module._CLI_PROG}:" in err` (store rejection — log line precedes in prod):
| pin | path | why store-rejection |
|---|---|---|
| `TestAdversarySetRankErrorPath::test_set_rank_with_an_unruled_rank_is_loud_and_nonzero` | `KeepStore.set_rank(rank="overlord")` | `UPDATE … SET rank` hits the closed-domain rank ASSERT → engine rejects → wrapped `KeepStoreError` |
| `TestKeepVerbErrorPaths::test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero` | `KeepStore.add_household_member(keep=ghost)` | `RELATE …->ghost_keep` refused by the ENFORCED `member_of` `out` endpoint → engine rejects → wrapped |
| `TestANonexistentKeepIsLoudForEveryKeepConsumingVerb::test_a_nonexistent_keep_is_a_loud_exit_1` | ∀ add/remove/set-rank ghost | its **add-household** param is the same ENFORCED reject; shared assertion must be honest for that param |

Left as `err.startswith(f"{p_module._CLI_PROG}:")` (clean single-line domain refusal — NO seam log in prod):
| pin | path | why clean |
|---|---|---|
| `TestKeepVerbsExecuteDirectly::test_remove_household_refuses_to_remove_the_keeper` | `remove_household_member` keeper == member | `KeeperLockoutError` raised in Python BEFORE any DELETE |
| `TestCreateKeepPerTypeNameRule::test_create_keep_without_name_is_rejected_for_name_requiring_types` | `_cmd_create_keep` per-type rule | `ValueError` at dispatch, BEFORE any store call |
| `TestCreateKeepPerTypeNameRule::test_create_keep_dm_with_a_name_is_rejected` | `_cmd_create_keep` dm --name rule | `ValueError` at dispatch, BEFORE any store call (this pin's content check is the R-A fix) |
| `TestKeepVerbErrorPaths::test_create_keep_with_an_unknown_keeper_is_loud_and_nonzero` | `create_keep` unknown keeper | `_resolve_principal_id` → `get_by_email` returns None (a SELECT with no rows = SUCCESS, not a rejection) → `KeepStoreError` raised in Python BEFORE `execute_transaction`; no `keep.query.rejected` line |

The unknown-keeper pin was not in the brief's explicit change-or-keep lists; traced its path in
`keeps.py` and confirmed it is a clean Python-level raise (no engine rejection) → kept `startswith`
(the stronger, still-honest check). rc/exit-code assertions were not touched.

## Proofs (no repo file touched — logic replayed inline; see the Bash receipt in the run)

R-A discrimination — old whole-line check vs new body check:
- real msg `lore-adm: --name is not valid for --type dm (a dm keep has no name concept)`: old=True, new=True (both must pass)
- degenerate `lore-adm: --name option is not permitted here` (names name, body never names dm): old=**True (false pass — the defect)**, new=**False (reddens)**

R3 honesty — store-rejection path, `startswith` vs `in`:
- clean suite line `lore-adm: …`: startswith=True, in=True
- prod dirty line `keep.query.rejected …\nlore-adm: …` (seam log first): startswith=**False (prod-false)**, in=True

## GATES
- `uv run ruff check loremaster/tests/test_keeps_cli.py` → `All checks passed!` (one E501 fixed by shortening a comment).
- `uv run pytest -n auto loremaster/tests/test_keeps_cli.py` → `47 passed in 5.99s` (live spike store ws://127.0.0.1:18000).
- `git status --short`: `test_keeps_cli.py` (`??`) is the only file I edited; the other M/`??` entries are the pre-existing wave-2 build + sibling reports (untouched).
