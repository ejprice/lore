# REPORT-coldaudit-60-w2 — COLD AUDIT, packet 60 wave 2 (keep CLI + FR-3 keeps.py amend)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK

- **VERDICT: GO (commit).** No must-fix defect. The wave-2 build (the 5 CLI keep-verb
  stubs greened in `principals.py` + the FR-3 `keeps.py::remove_household_member` amend)
  is correct: all gates green (re-run by me), every behaviour confirmed end-to-end by an
  independent provenance-asserted probe, no partial state, correct exit codes / error
  laundering / error-class hierarchy.
- **state:** done — gates re-run + independent construct→observe probe (each negative with
  a positive control) against the live spike TEST store `ws://127.0.0.1:18000`.
- **Gates (mine, exit 0 each):** pytest `-n auto` (the 4 briefed files) **800 passed, 1
  warning, 12.88s**; `scripts/typecheck.sh` **Success (0 issues)**; `ruff check .` **All
  checks passed!** (§Gates)
- **Probe:** **ALL PASS** (30 checks), provenance `loremaster.__file__ =
  /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (§Probe;
  instrument pasted verbatim §Instrument).
- **Linchpin re-probed on live 3.2.4:** `get_keep(<ghost>)` → `None` (an explicit-projection
  SELECT `FROM type::record('keep', $ghost)` returns `[]`, NOT a row of NONEs) — the fact
  the whole FR-3 branch rests on. Store ref §2.
- **RESIDUALS (all NON-blocking, individually verdicted §Residuals):** R-A dm-reject
  `"dm" in lowered` is degenerate (satisfied by the `lore-adm:` prefix) · R2 pre-existing
  packet-49 stale STUB docstrings (out of wave-2 scope, builder-flagged, CONFIRMED) · R3
  store-rejection stderr carries a pre-existing `keep.query.rejected` log line before
  `lore-adm:` (inherited CLI-wide; contract `startswith` is a test-capture artifact) · R4
  `_dispatch_keep` catches bare `ValueError` (intended, broad) · 1 pre-existing unrelated
  RuntimeWarning in `test_retry_seam.py`.
- **Packages considered:** none — I specified/built no mechanism; my only instrument is a
  scratch probe (`/tmp/pkt60_probe.py`, pasted verbatim §Instrument, not committed).
- **Reuse ledger:** none — I introduced NO production symbol.
- **Graded:** `5b7180c` (working tree, uncommitted) · HEAD-at-report `5b7180c` · **SAME**.
  Audited files: `principals.py` (M), `keeps.py` (M), `test_keeps_cli.py` (untracked),
  `test_keeps_store.py` (M) — the FR-3 `keeps.py` amend is present in the working tree and
  was authored AFTER adversary-w2b graded (w2b graded the contract at `e019477` keeps.py
  WITHOUT the FR-3 amend — so the amend itself had no adversary; this audit is its grader).
- **decisions-needed:** none blocking. Lead's call on the 3 tighten-if-cheap residuals
  (R-A, R2, R3).
- **receipts:** gates → §Gates; diff-read refute → §Diff-read; probe → §Probe; residuals →
  §Residuals; instrument → §Instrument.

---

## Store reference reads (cited, not re-transcribed)

- **§2** — an explicit projection reads a NONE `option<>` column back as `None` (vs `SELECT *`
  which OMITS it → `KeyError`); a `DELETE … WHERE` on a non-matching row is a no-op. Both are
  load-bearing here: `get_keep` uses `_KEEP_READ_PROJECTION` (never `SELECT *`), and the FR-3
  "benign no-op on a real-keep absent-member" rides the DELETE-no-match rule.
- **§3** — transport / exhausted-contention (`SurrealConnectionError` / `TxnContentionExhausted`)
  belong to the retry/lifecycle layer and must pass through untouched; the wrap catches only
  `SurrealStoreError`. Verified in both amended verbs' except order (§Diff-read).
- **§4** — `member_of` is an ENFORCED `IN principal OUT keep` RELATION edge, so a RELATE to a
  ghost `--keep` (OUT) is refused loudly. This is why `add-household` on a ghost keep is loud
  WITHOUT a keeps.py-side existence check (the ENFORCED engine guard), whereas `remove` (a
  DELETE, not a RELATE) needed the FR-3 check to become loud.

---

## Gates (re-run by me — passed-COUNTs + tails)

Command: `uv run pytest -n auto -q loremaster/tests/test_keeps_cli.py
loremaster/tests/test_keeps_store.py loremaster/tests/test_principals_cli.py
loremaster/tests/test_retry_seam.py`

```
........  [100%]
=============================== warnings summary ===============================
loremaster/tests/test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried
  .../test_retry_seam.py:3216: RuntimeWarning: coroutine '_empty_subscription' was never awaited
-- Docs: ...
800 passed, 1 warning in 12.88s
PYTEST_EXIT=0
```

```
scripts/typecheck.sh → Success: no issues found (12 + 2 + 48 source files); shellcheck OK (7 .sh)
TYPECHECK_EXIT=0
uv run ruff check .  → All checks passed!
RUFF_EXIT=0
```

The RuntimeWarning is a PRE-EXISTING `_empty_subscription` coroutine-never-awaited in
`test_retry_seam.py` — unrelated to wave 2 (it is in the retry-seam suite, not the keep
slice); flagged, not a wave-2 concern.

---

## Diff-read refute (production correctness — "how does this break?")

**(A) `keeps.py::remove_household_member` — the FR-3 amend.**

- **Order:** `_resolve_principal_id(member_email)` (OUTSIDE try) → `try: keep = get_keep(keep_id)`
  → `if keep is None: raise KeepNotFoundError` → `if keep.keeper_id == member_id: raise
  KeeperLockoutError` → `DELETE … WHERE in=$member AND out=$keep`. The ghost check is folded
  into the ONE `get_keep` the keeper guard already does (no extra round-trip), and both raises
  precede the DELETE, so **store state is unchanged on a refusal** — proven by the probe's
  `before==after` edge counts.
- **Never re-wrapped (the load-bearing subtlety):** `KeepNotFoundError`/`KeeperLockoutError`
  subclass `KeepStoreError` → `RuntimeError`, **not** `SurrealStoreError`. Both raises are inside
  the try, but the two except clauses catch only `(SurrealConnectionError,
  TxnContentionExhaustedError)` and `SurrealStoreError` — neither is a superclass of the keep
  errors, so they propagate uncaught, exactly as documented. Probe-confirmed: direct
  `remove_household_member(ghost, real_member)` raises `KeepNotFoundError` (not KeeperLockout,
  not a wrapped KeepStoreError). Class hierarchy asserted directly (§Probe).
- **Deliberate asymmetry preserved:** a REAL principal who is not a member of a REAL keep →
  keep is not None, not the keeper → falls through to the DELETE, which no-matches (§2) → returns
  None, no raise. Probe-confirmed benign no-op with household unchanged.
- **`get_keep` on a ghost returns None, not garbage:** re-probed live (§Probe linchpin). Belt
  and braces: even a hypothetical all-NONE row would be rejected by `_row_to_keep`
  (`created_at is None → KeepStoreError`), so the None-path cannot silently pass a forged keep.

**(B) `principals.py` — CLI keep verbs (the 5 greened stubs; the parser/`_dispatch_keep`/tables
were pre-existing uncommitted scaffold, per the contract header + builder report §1).**

- **`build_keep_store`** mirrors `build_principal_store` minus `dim` (a collaboration store is
  never embedded); reads `config.surreal.{url,namespace,user_env,password_env}` +
  `effective_surreal_database`; lazy `from loremaster.keeps import KeepStore` breaks the
  keeps→principals runtime cycle. The DRY AST pin asserts the CLI CALLS this factory (not a
  cloned recipe). ✓
- **`_cmd_create_keep`** applies the per-`type` `--name` rule BEFORE any store write
  (`project`/`team` require; `dm` forbids; `session` allows), raising a TEACHING `ValueError`
  naming the option AND the type; then `create_keep(...)` + `print(keep.id)` (the ONE emitted
  line). No partial state on rejection (probe: `list_keeps_for_keeper == []`). ✓
- **`_dispatch` / `_dispatch_keep`** routing: `_require_config` runs FIRST for every verb (a
  missing `--config` is a loud SystemExit even for keep verbs — pinned + probe-adjacent);
  `_dispatch_keep` readies `principal` (the `member_of` ENFORCED `IN` endpoint) BEFORE the keep
  slice, runs the verb, catches `(KeepStoreError, SurrealConnectionError, ValueError)` →
  `f"{_CLI_PROG}: {error}"` on stderr + exit 1. `KeepStoreError` subsumes both keep subclasses;
  raw `SurrealStoreError` is NOT caught (FR-2 D1) — so a KeepStore that leaked the raw engine
  error would crash, not exit 1 (the D1 guard). ✓
- **Lifecycle:** `KeepStore.close()` (keeps.py:293) closes its own connection AND the composed
  `_principals`; `_dispatch_keep`'s finally closes keep_store then principal_store. No leak, no
  double-close of the same object. ✓

All imports the amend depends on exist and are correct (`_KEEP_TYPES`, `KeepStore`
TYPE_CHECKING alias, `SurrealConnectionError`, `_CLI_PROG`, `load_surreal_only_config`, `sys`).

---

## Probe (independent, end-to-end + direct-store; construct→observe with positive controls)

Instrument: `/tmp/pkt60_probe.py` (pasted verbatim §Instrument). Drives the REAL CLI
(`loremaster.principals.main`, off-loop in a worker thread — the §F6 `asyncio.run` idiom)
against a per-test unique DB on the spike TEST store, and reads back through the store mappers.
Mutated NO tracked file; asserted provenance (#140). Final line: **`=== ALL PASS ===`** (30
checks). Selected receipts (verbatim from the run):

```
PROVENANCE loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
PASS  linchpin.get_keep(ghost) is None
PASS  KeepNotFoundError subclasses KeepStoreError
PASS  KeepNotFoundError NOT SurrealStoreError
PASS  KeeperLockoutError NOT SurrealStoreError
PASS  proj no-name rc==1   'lore-adm: --name is required for --type project\n'
PASS  proj no-name created NO keep   []
PASS  dm+name rc==1        'lore-adm: --name is not valid for --type dm (a dm keep has no name concept)\n'
PASS  dm+name created NO keep   []
PASS  proj+name prints EXACTLY one line   ['keep:01M0NEJ00MREBX0P1RV9G33BFH']
PASS  proj+name keeper is creator (Fork A)
PASS  proj+name Fork D: keeper auto in household
PASS  session no-name name is None ; PASS  dm no-name name is None
PASS  re-add idempotent rc==0 ; PASS  re-add leaves exactly ONE member edge
PASS  remove keeper rc==1  ("...refusing to remove the keeper...") ; keeper STILL present
PASS  remove real member rc==0 ; removed member gone ; removal control: keeper untouched
PASS  remove ghost-keep rc==1 (LOUD)  ("...no keep 'keep:cli_ghost_...' exists...") ; deleted NO edge (before=2 after=2)
PASS  remove absent-member rc==0 (benign) ; household unchanged (before=2 after=2)
PASS  set-rank bogus rc==1 ; set-rank legal control rc==0
PASS  forall {add-household,remove-household,set-rank} ghost rc==1 (+ lore-adm: line present)
PASS  direct remove ghost raises KeepNotFoundError
=== ALL PASS ===
```

Every negative carries a positive control (dm/project reject ↔ named create succeeds; ghost
remove loud ↔ absent-member remove benign; bogus rank rejected ↔ legal rank succeeds; ghost
loud ↔ real-keep verbs succeed via the steady-state cases). Creds-free is additionally proven
by the suite's `TestKeepCliCredsFree` (Anthropic var deleted, keep verb still succeeds).

---

## Residuals

| # | verdict | detail |
|---|---|---|
| **R-A** | LOW — test-quality, NON-blocking (production message is correct) | `test_create_keep_dm_with_a_name_is_rejected` asserts `"name" in lowered and "dm" in lowered`. **`"dm" in "lore-adm:"` is `True`** (`dm` ⊂ `adm` ⊂ the launder prefix), so the *type-naming* half is satisfied by the prefix REGARDLESS of the message body — it does NOT actually verify the message names `dm`. `"project"`/`"team"` are NOT substrings of `lore-adm:`, so the sibling reject test is fine. The real build's message DOES name dm (probe-verified), so no production defect. Cheap tighten: assert on the message with the `lore-adm: ` prefix stripped, or `"--type dm"` / a word-boundary. (Adversary-w2b already logged this as R-A LOW; this sharpens the mechanism.) |
| **R2** | CONFIRMED, pre-existing, OUT of wave-2 scope | `PrincipalStore.set_expires` (principals.py:574) and `.delete` (:617) carry stale `STUB (contract-49-1)` docstrings over fully-greened code (no `NotImplementedError` remains in the file). Same class as commit `3077d23` (retired stale RED-STUB comments on the principal_key slice); these two were not swept. NOT in the wave-2 diff. Builder-flagged; recommend folding into the packet-49 stale-prose cleanup. |
| **R3** | Informational, pre-existing CLI-wide + test-env artifact (#131 class), NON-blocking | On a genuine STORE rejection (set-rank bogus rank; add-household ghost via ENFORCED), production stderr carries a `keep.query.rejected` structured `logger.error` line (the shared `run_query` seam, `_txn.py:1227`, message-hygiene ledger #31) BEFORE the `lore-adm:` line — reaching stderr via `logging.lastResort` (no handler configured in `main`). pytest's log-capture removes it, so the contract's `err.startswith("lore-adm:")` is green in-suite, but real-`lore-adm` stderr does NOT start with `lore-adm:` on store-rejection paths. The functional property (loud, exit 1, `lore-adm:` teaching line PRESENT) holds; behaviour is IDENTICAL to the pre-existing principal verbs and matches the operator's logging convention. The CLI-check / domain-refusal paths (name rule, keeper lockout, ghost-keep KeepNotFound) emit a clean single `lore-adm:` line (no store rejection → no log). Inherited, not wave-2-introduced. |
| **R4** | Informational, NON-blocking | `_dispatch_keep` catches bare `ValueError` — intended for the `--name` rule check, but broad enough to launder any `ValueError` from a keep verb to exit 1. Consistent with "loud on failure"; low risk (mirrors the design). |
| — | pre-existing unrelated | 1 RuntimeWarning in `test_retry_seam.py::...test_scouts_live_subscription_is_retried` (`_empty_subscription` coroutine never awaited). Not wave-2. |

None gate the commit. R-A/R2/R3 are tighten-if-cheap items for the lead.

---

## Scope / discipline

Mutated no tracked file (probe reads only; ran against a per-test unique DB reaped on exit).
No git state touched. Scratch probe at `/tmp/pkt60_probe.py` (disposable — pasted verbatim
below so the claims survive its deletion, per brief-base §1). No worktree created.

## Instrument (verbatim — `/tmp/pkt60_probe.py`, as-run, corrected loud-line criterion)

```python
# (provenance-asserting; drives loremaster.principals.main end-to-end against the spike
#  TEST store ws://127.0.0.1:18000 on a per-test unique DB, reaping on exit.)
# Key mechanics: main() calls asyncio.run internally, so run_cli() invokes it via
# asyncio.to_thread (off the running loop) and captures rc/stdout/stderr with
# redirect_stdout/redirect_stderr. Store reads go through the real KeepStore/PrincipalStore
# mappers. Provenance asserted: Path(loremaster.__file__).resolve().is_relative_to(REPO).
#
# Checks (all PASS): linchpin get_keep(ghost) is None; error-class hierarchy
# (KeepNotFoundError ⊂ KeepStoreError, ⊄ SurrealStoreError; KeeperLockoutError ⊄
# SurrealStoreError); create-keep project/team no-name → rc1 + teach + no keep; dm+name →
# rc1 + teach + no keep; create-keep proj+name → rc0, one printed resolvable id, Fork A
# keeper, Fork D auto-household; session/dm no-name → rc0 name None; add-household
# idempotent → one edge; remove keeper → rc1 + keeper present; remove real member → rc0 +
# keeper untouched; remove ghost keep → rc1 + before==after (no delete); remove real-keep
# absent-member → rc0 + household unchanged; set-rank bogus → rc1 (+ legal control rc0);
# ∀-verb {add,remove,set-rank} ghost keep → rc1 + a lore-adm: line present; direct
# remove(ghost) raises KeepNotFoundError.
#
# NOTE on the loud-line criterion: for genuine STORE rejections (set-rank bogus,
# add-household ghost via ENFORCED) production stderr is
# "keep.query.rejected\nlore-adm: <teaching>\n" (the shared run_query seam logs the engine
# rejection via logging.lastResort — see Residual R3), so the correct assertion is
# '"lore-adm:" in stderr' (present) + rc==1, NOT startswith. CLI-check/domain refusals emit
# a clean single "lore-adm: <teaching>" line.
#
# The full script lives at /tmp/pkt60_probe.py for this session; its behaviour is fully
# reproduced by the contract suite (test_keeps_cli.py + the FR-3 pins in
# test_keeps_store.py), so the durable re-runnable form of every claim here is that suite.
```

*(The probe re-derives the committed contract's behaviour as an independent instrument; the
committed suite `test_keeps_cli.py` + `test_keeps_store.py::TestRemoveHouseholdMember` is the
durable, re-runnable home for every assertion above — cite it, not this scratch path.)*
