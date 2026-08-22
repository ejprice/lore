# REPORT-builder-60-w2 — packet 60 wave 2 BUILDER (keep CLI + FR-3 keeps.py amend)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done — the SUFFICIENT wave-2 contract is GREEN. Production-only edits to
  `principals.py` (CLI keep verbs) + `keeps.py` (FR-3 amend). No test files touched.
- **deviations:** none material.
- **Packages considered:** none — no new external mechanism. The `--name` policy is a
  house-local CLI rule (stdlib membership test); the FR-3 guard is a store read the method
  already performs. Bespoke is correct (nothing to install for "is `--name` valid for this
  `--type`"), so no package survey applies.
- **Reuse ledger:** 2 new production symbols, both dispositioned (§Reuse ledger). No shared
  cross-caller policy introduced.
- **Graded:** builder work, not a verdict on another artifact — `Graded:` N/A. Built at
  HEAD `5b7180c` + the wave-2 uncommitted contract scaffold (`principals.py` M,
  `test_keeps_store.py` M, `test_keeps_cli.py` untracked).
- **decisions-needed:** ONE, out of my packet-60 scope — two packet-49 `PrincipalStore`
  methods carry stale `STUB (contract-49-1)` docstrings over fully-greened code (§Flags).
  Recommend the lead fold them into the packet-49 stale-prose cleanup (precedent: `3077d23`).
- **receipts:** gates → §Gates (per-file passed counts + tails); what changed → §1/§2;
  scope confirmation → §Scope; #398 stub-comment audit → §3.

---

## 1. (A) CLI verbs — `loremaster/loremaster/principals.py`

Greened the 5 stubs the contract scaffold left (`build_keep_store` + the 4 `_cmd_*` keep
handlers), mirroring the `build_principal_store` / `build_principal_key_store` /
`_cmd_mint_key` precedents. Everything else in the `principals.py` diff (the parser entries,
`_dispatch_keep`, `_KEEP_VERB_HANDLERS`, the `_KeepVerbHandler` TYPE_CHECKING alias, the
`_dispatch` keep-routing + FR-2 D1 catch) was PRE-EXISTING uncommitted contract scaffold —
NOT authored by me; it shows in `git diff` only because it was never committed.

- **`build_keep_store(config) -> KeepStore`** (`principals.py`, sibling of
  `build_principal_store`): lazy `from loremaster.keeps import KeepStore` (keeps→principals
  is a runtime cycle), then `KeepStore(url=…, namespace=…,
  database=config.effective_surreal_database, user=resolve_config_value(config.surreal.user_env),
  password=resolve_secret(config.surreal.password_env))` — no `dim` (a collaboration store is
  never embedded). Removed the `STUB (contract-60-w2)` prose (#398).
- **`_cmd_create_keep`** — the per-`type` `--name` rule enforced at DISPATCH level, BEFORE any
  store write (no partial state): `project`/`team` with no `--name` → `raise ValueError("--name
  is required for --type <type>")`; `dm` WITH `--name` → `raise ValueError("--name is not valid
  for --type dm (a dm keep has no name concept)")` (FR-2 Q1 — teaching message names `--name`
  AND `dm`). Both `ValueError`s are laundered by `_dispatch_keep` → `lore-adm:` stderr + exit 1.
  Then `create_keep(keeper_email=args.keeper, type=args.type, name=args.name)` + `print(keep.id)`
  (the `_cmd_mint_key` print-the-id precedent) + `return 0`.
- **`_cmd_add_household` / `_cmd_remove_household` / `_cmd_set_rank`** — one-line delegations to
  the matching `KeepStore` method (`add_household_member` / `remove_household_member` /
  `set_rank`), `return 0`. Silent on success.
- **`_KEEP_NAME_REQUIRED_TYPES = frozenset({"project", "team"})`** and
  **`_KEEP_NAME_FORBIDDEN_TYPES = frozenset({"dm"})`** — the CLI-owned `--name` policy the
  ruling places in the CLI (not the store; `keep.name` stays `option<string>`). Coverage of the
  `_KEEP_TYPES` domain is a CHECKED VARIABLE in the contract
  (`test_keeps_cli.py::test_every_keep_type_has_a_declared_name_policy`), which reds until a new
  keep type's `--name` policy is decided (reach law #344/#345) — so the production hardcode is
  the CLI decision and the test is its reach guard.
- `_KEEP_VERB_HANDLERS` (scaffold) already wires all 4 verbs — verified, unchanged.

## 2. (B) FR-3 amend — `loremaster/loremaster/keeps.py`

`remove_household_member`: a GHOST keep is now LOUD. Folded the existence check into the ONE
`get_keep(keep_id)` read the keeper-lockout guard already performs (a DIRECT keep-row SELECT —
store ref §2, not a keeper-is-None proxy): `if keep is None: raise KeepNotFoundError(f"no keep
{keep_id!r} exists — cannot remove a household member from it")`, raised BEFORE the DELETE so
store state is unchanged. The keeper check is unchanged (now guarded by `if keep.keeper_id ==
member_id:` after the ghost check).

- **Benign asymmetry PRESERVED:** a REAL principal who is NOT a member of a REAL keep → keep is
  not None → not the keeper → the `DELETE … WHERE in=$member AND out=$keep` no-matches (store
  ref §2: a DELETE no-match is a no-op) → returns None, no raise.
- `KeepNotFoundError` subclasses `KeepStoreError` (→ `RuntimeError`), NOT `SurrealStoreError`,
  so the method's `except SurrealStoreError` wrap never re-wraps it — it propagates like the
  existing `KeeperLockoutError` (`keeps.py` error hierarchy `:156`/`:160`), and `_dispatch_keep`
  catches it via the `KeepStoreError` clause → CLI exit 1.
- Docstring updated to describe both pre-DELETE guards + the asymmetry (no stale prose left).

Q2b engine-rejection wrap is ALREADY committed (`e019477`) — my `keeps.py` diff is the FR-3
amend ALONE.

## 3. #398 stub-comment audit (my greened code)
`grep -nE "STUB|contract-60-w2|NotImplementedError"` over the two prod files after my edits:
- `keeps.py:3/:6` — MODULE docstring HISTORY ("Introduced as the STUB half … and GREENED by
  the wave-1 builder … Every CRUD verb below is now fully implemented"). Accurate, not stale —
  left as-is.
- `principals.py:575/:617` — `STUB (contract-49-1)` on packet-49 `set_expires`/`delete` —
  PRE-EXISTING, out of packet-60 scope (see §Flags).
- No `STUB (contract-60-w2)` / `NotImplementedError` survives in my greened symbols.

## Gates (measured this session; spike TEST store ws://127.0.0.1:18000 confirmed reachable)
`cd loremaster && uv run pytest -n auto tests/test_keeps_cli.py tests/test_keeps_store.py
tests/test_principals_cli.py tests/test_retry_seam.py`:
```
64 workers [800 items]
======================= 800 passed, 1 warning in 12.06s ========================
```
Per-file (collected == passed; sum 47+45+45+663 = 800):
- **test_keeps_cli.py — 47 passed** (wave-2 CLI + R1/R2/blocker + FR-3 ∀-verb, all green).
- **test_keeps_store.py — 45 passed** (FR-3 ghost/asymmetry + Q2b wrap pins green).
- **test_principals_cli.py — 45 passed** (no regression to the 9 existing principal/key verbs).
- **test_retry_seam.py — 663 passed** (no seam disturbance; `_query` sharing pins intact).

The 1 warning is a PRE-EXISTING `RuntimeWarning: coroutine '_empty_subscription' was never
awaited` at `test_retry_seam.py:3216` (a test file I did not touch; inside its own
`contextlib.suppress`) — a warning, not a failure; the 663 all pass.

`./scripts/typecheck.sh` (canonical):
```
Success: no issues found in 222 source files
typecheck: loremaster OK
... lorerunes/lorescribe/loresigil/skills/docs·eval/scripts OK; shellcheck OK (7 tracked .sh)
```
`uv run ruff check .`:
```
All checks passed!
```

## Scope
- Edited ONLY `loremaster/loremaster/principals.py` + `loremaster/loremaster/keeps.py`
  (`git status --short loremaster/loremaster/` → exactly those two `M`). No test file touched.
  Did NOT stage/commit (the lead splits `fix(60) R3` + `feat(60) CLI`).

## Reuse ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_KEEP_NAME_REQUIRED_TYPES` (prod) | `lore_search("per-type name required policy for keep create CLI validation project team dm nameless")` | only the TEST-local `_NAME_POLICY_BY_TYPE` (0 prod) — production must not import a test map | **HAND-ROLLED** — no production name-policy exists; the ruling places this policy in the CLI, and its reach is the contract's checked-variable pin, not a shared helper. |
| `_KEEP_NAME_FORBIDDEN_TYPES` (prod) | same query | same (nothing production-side) | **HAND-ROLLED** — the dm-nameless half of the same CLI-owned policy; single call site (`_cmd_create_keep`). |

Both are named constants (not inline literals) matching the file's `_COL_*` / `_PRINCIPAL_ROLES`
constant idiom + the global "no hardcoded values" rule. No shared cross-caller POLICY (a single
call site), so `lorerunes` extraction does not apply.

## Flags / decisions-needed (surfaced, NOT resolved — out of packet-60 scope)
- **Stale `STUB (contract-49-1)` docstrings over LIVE packet-49 code** — `principals.py:575`
  (`PrincipalStore.set_expires`) and `:617` (`PrincipalStore.delete`) both open
  `"""STUB (contract-49-1): …` yet their bodies are fully implemented (real UPDATE / cascade
  DELETE, not `raise NotImplementedError`). This is a #398-class stale-prose defect, but it is
  PACKET 49, outside my packet-60 CLI mandate, and mixing a packet-49 doc fix into a packet-60
  commit violates one-concern-per-commit. There is active precedent for this cleanup
  (`3077d23 docs(49): retire stale RED-STUB comments on the greened principal_key slice`), which
  covered the `principal_key` slice but MISSED these two `principals.py` methods.
  **Exact edit (both):** delete the `STUB (contract-49-1): ` prefix from the docstring's first
  line (the rest of each docstring already describes the live behaviour accurately).
  **Recommendation:** fold into the packet-49 stale-prose cleanup, or authorize me to fix it in
  a separate `docs(49)` commit. Your call.

## Task / comms
- Task `53f78fd1dfcf43468d6207593463a260` claimed + in_progress (→ done on close).
- Registered on `lore_comms` as `builder-60-w2` (session pkt60, role builder). No lore weakness
  hit; lore tools used first-choice for symbol/precedent lookup. One grep used for the #398
  stub-comment sweep (a non-symbol textual seam — bare-pattern sweep per the rename-sweep law,
  said out loud) and one for the git scope check; no structure-question grep fallback.
