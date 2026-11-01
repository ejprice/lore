brief-base v24 read
brief project v7 read

## Summary
- **State:** done.
- **Deviations:** none. (The only uncertainty is the dropped wording in the removed-behavior inventory below: the "podman exit N:" prefix and the "inspect podman logs" hint.)
- **Packages considered:** `shlex.quote` (stdlib; its documented contract is to return a shell-safe single token and to leave a safe string unchanged, confirmed by the A8 pins going green with plain paths) — `replace` for hand-quoting. No other mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new reusable symbols. One new local variable (`cold_index_command`) inside the existing message builder. Rows below.
- **Graded:** bb61542 (+ my uncommitted edit to `lore_deploy.py`) · HEAD-at-report: bb61542 · SAME.
- **GREEN:** `RAN:` matches the brief's command. **208 passed in 11.73s, EXIT=0**, 0 failed, no ImportError or collection error (log `/var/tmp/claude-1000/impl165a1-green.log`). The lead's RED at bb61542 was 11 failed / 141 passed over `. ../tests`. My run adds the 3 loremaster files, hence the larger count.
- **Gates:** ruff `All checks passed!`, RUFF_EXIT=0. typecheck: 83 `error:` lines (baseline 83, RED_ADJUDICATED: 82 in loremaster/tests + 1 in `scripts/test_forgery_door_sweep.py`), **0 in lore_deploy.py**, TC_EXIT=1 as at baseline (log `/var/tmp/claude-1000/impl165a1-gates.log`).
- **Decisions needed:** (1) the fresh (not-running) start path still lets a `_launch_container` raise escape raw (§Anything noticed 1); (2) a doc still teaches bare `python -m loremaster.index` (§Anything noticed 2). Neither is in my writable set or in A1's "recreate path".
- **Pointers:** §Routing; §Diff; §DRY ledger; §Removed-behavior inventory; §Anything noticed.

## Routing table (written before any read beyond the brief and brief-base v24)

| step | tier | who | reason |
|---|---|---|---|
| A. Lookups: the recreate handler (`verb_start`), `_require_launchable_snapshot`, `_loremaster_python`, `_launch_container` (raise set), the A1/A8/R3 tests | 1-sized, run as ONE parallel batch | self | brief-routed "one parallel batch". Batch size: 5 lore calls (`lore_index` currency + 4 `lore_get_symbol`), then 3 test-span `lore_search`es. Coverage: 4/4 symbols resolved, `candidate_count` 1 each. On the critical path, and I read all of it |
| B. Implementation | 3 | self | brief: inline |
| C. Test run | 1 | `haiku-runner` | brief-routed |
| D. Gates (ruff + typecheck) | 1 | `haiku-runner` | brief-routed, parallel with C |

Fan-out: haiku 2 (2 runners) · sonnet 0 · peak 2.
Tool note: `grep` was denied by the PreToolUse hook on the lore checkout, even over `/var/tmp` logs when the command also named the repo. Lookups went through lore MCP; log tails were checked with `tail`/`awk`. This is the hook working as configured, not a lore weakness; nothing filed.
Index currency: `lore_index()` at start showed root `/workspace` at bb61542, last_sync 1.5 s; `lore_deploy.py` was unmodified in the tree before my edit.

## Diff (`skills/lore-deploy/scripts/lore_deploy.py`, +22 / −10)
- `import shlex` added to the module imports.
- `_require_launchable_snapshot` (the ONE refusal builder): the remedy is now `` `{shlex.quote(_loremaster_python())} -m {_COLD_INDEX_MODULE} --config {shlex.quote(str(config_path))}` ``, replacing bare `python`. Covers **A8**; quoting per lead ruling (2).
- `verb_start` recreate branch: the ONE existing handler is widened from `except subprocess.CalledProcessError` to `except (RuntimeError, subprocess.CalledProcessError)`. It prints `start: relaunch of <c> failed (<error>); the stale container was already removed — fix that cause and retry \`start\`.` and returns `_EXIT_ERROR`. Covers **A1**. `OSError` is excluded per lead ruling (1). Comments updated to say why the RuntimeError is reachable after the pre-teardown gate (config or snapshot can change before the launch's own re-check).
- No second handler and no retyped interpreter path.

## DRY ledger
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| (none: no new function, helper or constant) | n/a | n/a | n/a |
| interpreter in the remedy | brief-named `_loremaster_python`; `lore_impact(_loremaster_python)` → 5 prod consumers, incl. `_read_config_field`, which execs it as a single argv token | the resolver | **REUSED `lore_deploy._loremaster_python`** |
| module in the remedy | the existing `_COLD_INDEX_MODULE` constant | the constant | **REUSED `_COLD_INDEX_MODULE`** |
| refusal message | brief-named `_require_launchable_snapshot` | the one builder | **EXTENDED in place** (remedy line only) |
| post-teardown failure handling | brief-named recreate handler (R3) | the one handler | **EXTENDED in place** (exception tuple + message) |

## Removed-behavior inventory (the handler's message was rewritten)
1. **"podman exit {returncode}:" prefix: dropped deliberately.** `str(CalledProcessError)` already reads `Command '[…]' returned non-zero exit status N.`, so the exit code and the failed command (R3) still reach stderr. The R3 test `test_called_process_error_exit_code_and_command_reach_stderr` is green in the run above. The prefix would be false for a RuntimeError, and the handler is now shared.
2. **"inspect podman logs" hint: dropped deliberately.** For a refusal, no container was launched, so there are no logs, and the refusal's own text carries the remedy. For a podman run failure, the error text names the command. Replaced by "fix that cause and retry `start`". If the lead wants a podman-specific hint kept for CalledProcessError, that needs a type branch inside the one handler; this is a wording call left for the lead.
3. "stale container was already removed" and `_EXIT_ERROR`: **preserved**, pinned by the A1 ∀-test and R3.

## Anything noticed
1. **The fresh (not-running) path still calls `_launch_container` with no handler.** A RuntimeError or CalledProcessError there propagates raw to the dispatcher. No serving container is lost on that path (it at most `podman rm -f`'d an already-exited one), so A1's outage rationale does not apply. But the "loud `_EXIT_ERROR`, never a raw raise" shape is inconsistent between the two paths. A1 names only the recreate path, so I did not touch it. Do you want the fresh path brought into line?
2. **`skills/lore-deploy/references/server-interface.md` (§ the "`setup` cold-indexes via" paragraph, ~line 89) still reads `python -m loremaster.index --config <lore.yaml>`.** That is the same bare-`python` spelling A8 retired from the served refusal. It is outside my writable set (docs). The edit I would make is `<loremaster python> -m loremaster.index …`, noting that lore-deploy resolves it via `LORE_PYTHON` / the workspace `.venv`. Found by `lore_search` (a non-symbol textual seam). A bare-pattern grep sweep was not possible under the hook, so other prose hits may exist. NOT TRIED: an exhaustive sweep.
3. Quoting consistency: `_loremaster_python()` can return a `LORE_PYTHON` override verbatim. `shlex.quote` makes an override like `uv run python` paste as one token. That matches how lore_deploy itself runs it (`_read_config_field`: `[_loremaster_python(), "-c", …]`, a single argv element), so the remedy runs exactly what lore_deploy runs.
