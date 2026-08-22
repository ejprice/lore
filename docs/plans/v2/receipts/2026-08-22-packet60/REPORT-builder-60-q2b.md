# REPORT-builder-60-q2b — packet 60 FR-2 Q2b BUILD (KeepStore engine-rejection wrap)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK

- **state:** done — all four `KeepStore` write paths WRAP raw `SurrealStoreError` as
  `KeepStoreError`, with the transport/contention pass-through re-raise FIRST at every site;
  the 8 Q2b REDs are green, the 8 pass-through cases stayed green, all gates pass.
- **capability check:** brief fully satisfiable with my toolset (Edit on keeps.py, the live
  spike-surreal test store at `ws://127.0.0.1:18000`, `uv`/`pytest`/`mypy`/`ruff`). No gaps.
- **deviations:**
  - Internal READS inside a write verb are inside the wrap (per the brief's "any read-back
    that could raise"): `create_keep`'s `get_keep` readback, `add_household_member`'s two
    `_read_membership` calls, `remove_household_member`'s `get_keep` (its DELETE cannot
    reject — this read is its only injection-coverage seam, per the contract), `set_rank`'s
    `_read_membership`. This is stricter consumer-law than wrapping only the write, and it is
    what the coverage pin's injection (patching `keeps.run_query`) exercises. Not a scope
    change — still keeps.py-only, still the four write paths.
  - Updated the `Raises:` docstrings of all four methods (they said "raises
    `SurrealStoreError`" / were silent on the wrap — now stale after the wrap; #398 /
    stale-prose class). No behavioural change.
  - Observed-not-touched: the top-of-file class docstring's `Exceptions:` list
    (`keeps.py:62-63`) omits `KeeperLockoutError` (added wave-1) — pre-existing, unrelated to
    my change; flagged, not edited (§Flags).
- **Packages considered:** none — no new production mechanism. The wrap MIRRORS the shipped
  `PrincipalStore.create` idiom (stdlib try/except); no library involved.
- **Reuse ledger:** none — no new reusable production symbol introduced. The wrap is an
  inline try/except at each write boundary, cloning the `PrincipalStore.create`/`set_subject`
  shape verbatim. (The DRY follow-up to extract a shared `wrap_engine_rejection` seam into
  `lorerunes` is the reviser's ledgered F-DRY recommendation for the lead — NOT this fix.)
- **Graded:** `ea03ea6` (HEAD) + the 3 uncommitted reviser files (my base tree) ·
  HEAD-at-report `ea03ea6` · SAME. My only authored change is `loremaster/loremaster/keeps.py`.
- **decisions-needed:** none for this build. (F-DRY is the reviser's standing recommendation
  to the lead; §Flags.)
- **receipts:** the wrap sites → §The change; pass-through-FIRST confirmation → §Pass-through
  ordering; gate passed-counts → §Gates; touched-only-keeps.py → §Scope.

---

## Store-law grounding (cited, not re-transcribed)

- **Error hierarchy** `[CODE] loremaster/store/_txn.py:116/120/156`:
  `SurrealStoreError(RuntimeError)` is the base (`:116`); `SurrealConnectionError` (`:120`)
  and `TxnContentionExhaustedError` (`:156`) SUBCLASS it. Because the transport/contention
  errors subclass `SurrealStoreError`, a bare `except SurrealStoreError` would SWALLOW them —
  so the pass-through re-raise MUST come FIRST. Verified by reading `_txn.py:116-183`.
- **Why they pass through** — store reference `docs/reference/surrealdb-31-capabilities.md`
  §3 (Transactions): client-side conflict retry is MANDATORY and lives in the retry/lifecycle
  layer (`retry_on_conflict` / `_ensure_connection`); `TxnContentionExhaustedError`'s own
  docstring (`_txn.py:165-170`) says a caller that must not treat exhausted contention as a
  domain outcome opts in by catching THAT type FIRST, above its `SurrealStoreError` handler.
  That is exactly `PrincipalStore.create`'s shape.
- **Reference idiom mirrored** — `PrincipalStore.create` (`principals.py:428-442`):
  `except (SurrealConnectionError, TxnContentionExhaustedError): raise` THEN
  `except SurrealStoreError as error: raise PrincipalStoreError(...) from error`.

---

## The change (`loremaster/loremaster/keeps.py` ONLY)

Added `SurrealStoreError` to the `_txn` import (it was already exporting it; only
`SurrealConnectionError`/`TxnContentionExhaustedError` were imported before). Then wrapped the
store-touching span of each write verb with the two-clause guard, pass-through FIRST:

```python
except (SurrealConnectionError, TxnContentionExhaustedError):
    raise                                    # retry/lifecycle layer — untouched (store §3)
except SurrealStoreError as error:
    raise KeepStoreError(<clean domain message>) from error
```

| write path | span inside the `try` | message names |
|---|---|---|
| `create_keep` | `execute_transaction(...)` + `get_keep(keep_id)` readback | operation (create) + `type` + `keeper_email` |
| `add_household_member` | `_read_membership` (dedupe) + `RELATE` + `_read_membership` readback | operation (add) + `member_email` + `keep_id` |
| `remove_household_member` | `get_keep` (keeper check) + `DELETE` | operation (remove) + `member_email` + `keep_id` |
| `set_rank` | `UPDATE` + `_read_membership` readback | operation (set rank) + `rank` + `member_email` + `keep_id` |

**Domain raises kept intact and NOT re-wrapped** (they are `KeepStoreError` subclasses, so
`except SurrealStoreError` never catches them — verified structurally + by green pins):
- `remove_household_member`'s `KeeperLockoutError` fires BEFORE the delete. It is raised
  *inside* the `try`, but `KeeperLockoutError → KeepStoreError → RuntimeError` is a different
  branch from `SurrealStoreError → RuntimeError`, so it passes straight through the wrap
  unchanged (store state untouched). `test_remove_household_REFUSES_to_remove_the_KEEPER` is
  green.
- `set_rank`'s `KeepNotFoundError` (no-match readback) is raised AFTER the `try`, on the
  `membership is None` check — untouched.
- `_resolve_principal_id`'s `KeepStoreError` (unknown email) is raised BEFORE the `try` — the
  unknown-email pins stay green.

The `if <readback> is None` post-checks stay after the `try` and reference a variable assigned
inside it — the exact shape as the shipped `PrincipalStore.create` (`result` assigned in the
`try`, `self._as_rows(result)` after it), which is why mypy accepts it.

## Pass-through ordering (the load-bearing invariant)

The re-raise of `(SurrealConnectionError, TxnContentionExhaustedError)` is the FIRST `except`
clause at EACH of the four sites — structurally guaranteed by construction, AND empirically
confirmed: `test_each_write_path_propagates_transport_faults_untouched` (derived-set ×
`{connection, contention}` = 8 cases) is GREEN. Had the pass-through re-raise NOT been first,
the `except SurrealStoreError` would swallow the transport faults (both subclass it) and those
8 cases would RED. They passed → the ordering is correct, all four paths.

## Gates (passed-counts from the tail)

- `uv run pytest -n auto tests/test_keeps_store.py` (from `loremaster/`) →
  **43 passed / 0 failed** (5.38s). The 8 Q2b REDs are now green (the 2 tightened corpse
  tests, the 4-path derived-coverage injection pin, the 2 behavioural ghost/unruled-rank
  pins); the 8 pass-through cases stayed green; the reach pin
  (`test_the_derived_write_path_set_matches_the_coverage_map`) stayed green (my change adds no
  new write method, so the derived set is unchanged: `{create_keep, add_household_member,
  remove_household_member, set_rank}`, and my `KeepStoreError` messages all start with
  `could not …`, never a mutating keyword, so the AST scan does not misclassify them).
- `uv run pytest -n auto tests/test_retry_seam.py` (from `loremaster/`) →
  **663 passed** (11.17s). Transport pass-through preserved — the retry seam still sees
  `SurrealConnectionError`/`TxnContentionExhaustedError` (not a masked `KeepStoreError`), and
  `KeepStore._query` (unrenamed) is still found by the `_query` scan, so the shared
  retry/backoff/exhaustion mutation pins pass. (One pre-existing `RuntimeWarning: coroutine
  '_empty_subscription' was never awaited` at `test_retry_seam.py:3216` in a
  `contextlib.suppress` block — a scout live-subscription test-infra warning, unrelated to
  keeps.py, present before my change; a WARNING, not a failure.)
- `./scripts/typecheck.sh` (repo root) → every member OK — `loremaster OK (222 source files)`,
  lorerunes/lorescribe/loresigil/skills/docs/scripts all OK, shellcheck OK.
- `uv run ruff check .` (repo root) → `All checks passed!`

## Scope (touched ONLY keeps.py)

`git diff --stat` → `loremaster/loremaster/keeps.py | 164 ++—, 116 insertions(+), 48
deletions(-)`, one file changed. The other modified/untracked files
(`principals.py`, `test_keeps_store.py`, the design doc, `test_keeps_cli.py`,
`REPORT-contract-60-w2*.md`) were already present before I started (the contract reviser's
FR-2 work) — I did NOT edit any of them. No test file, no schema, no CLI touched by me.

## Flags

- **Top-of-file `Exceptions:` docstring** (`keeps.py:62-63`) lists only `KeepStoreError` and
  `KeepNotFoundError`, omitting `KeeperLockoutError` (added wave-1). Pre-existing, unrelated to
  the wrap. Left untouched to stay minimal; the lead may fold a one-line fix into the fix(60)
  commit if wanted.
- **F-DRY (the reviser's standing recommendation, restated, NOT resolved by me):** ruling (b)
  makes `KeepStore` the SECOND store to encode the wrap-classification policy. The sidecar's
  ONE-IMPLEMENTATION escalation recommends extracting a
  `wrap_engine_rejection(DomainError, context)` seam into `lorerunes`, called by BOTH
  `PrincipalStore` and `KeepStore`, proven by mutation — a ledgered follow-up with a named
  trigger (*the moment a THIRD store/consumer needs the same wrap*), NOT part of this unblock
  fix. My wrap is a behaviour-parity clone of the shipped idiom; when the `lorerunes`
  extraction lands it stays green and gains the prove-by-mutation. Recommend the lead file the
  `lore_findings` DRY task.

## Task / comms

- Task `53be1db0fec3424c93d00aba0d47df91` claimed + driven claimed → in_progress → done.
- Registered on `lore_comms` as `builder-60-q2b` (session pkt60, role builder).
