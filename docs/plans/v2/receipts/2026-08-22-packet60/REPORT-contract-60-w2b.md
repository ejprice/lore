# REPORT-contract-60-w2b — packet 60 wave 2b CONTRACT REVISION (FR-2)

brief-base v14 read
brief project v7 read

- **state:** done — the three FR-2 changes (Q2b + Q1 + D1) are written, gated, and
  satisfiability-proven against a reference build.
- **deviations:**
  - D1: I catch `KeepStoreError` (which SUBSUMES `KeeperLockoutError`/`KeepNotFoundError`) —
    NOT the literal list `{KeepStoreError, KeeperLockoutError, …}` in the brief. Cleaner and
    symmetric with `_dispatch` catching `PrincipalStoreError` alone (which subsumes
    `PrincipalNotFoundError`). Confirmed the coverage is right (§D1).
  - `remove_household_member` has NO natural engine rejection (its DELETE cannot reject via
    the public API), so its behavioural wrap pin is the fault-injection one, not a real-reject
    one. Stated, not hidden (§Q2b).
  - Scratch reference-build copy `/tmp/pkt60w2b-ref` could NOT be removed — `rm -rf` denied by
    the permission policy (3 attempts). It is a disposable `scripts/scratch_copy.sh` rsync copy
    in `/tmp` (NOT a git worktree); `scratch_copy.sh --force /tmp/pkt60w2b-ref` reclaims it or
    the operator can delete it. Flagged so it is not silently abandoned.
- **Packages considered:** none — no NEW production mechanism specified. The wrap is a
  builder-side policy that MIRRORS the shipped `PrincipalStore.create` idiom (no package); my
  deliverable is RED pins.
- **Reuse ledger:** none — no new PRODUCTION reusable symbol. New symbols are TEST-LOCAL only
  (`_derive_keepstore_write_paths`, `_method_has_mutating_statement`, `_WRITE_PATHS`,
  `_WRITE_PATH_INVOCATIONS`, `_MUTATING_STATEMENT_KEYWORDS`, `_KEEPSTORE_READ_METHODS`,
  `_WRAP_PROBE_GHOST_KEEP` in `test_keeps_store.py`).
- **Graded:** `ea03ea6` (HEAD) + the 3 uncommitted files · HEAD-at-report `ea03ea6` · SAME.
  The satisfiability verdict is graded against a scratch reference build I constructed on top of
  this tree (§Satisfiability).
- **decisions-needed:** (F-DRY) the sidecar's ONE-IMPLEMENTATION follow-up — extract
  `wrap_engine_rejection` into `lorerunes` — is a ledgered recommendation for the LEAD to file
  (`lore_findings` DRY task), not part of this unblock fix. Surfaced, §Flags.
- **receipts:** RED/GREEN → §RED/GREEN; satisfiability (83/0) + provenance → §Satisfiability;
  mutation proofs → §Mutation proofs; fixtures self-audit → §Fixtures; store-law cites → inline.

---

## Store-law grounding (cited, not re-transcribed)

- **Error hierarchy is the load-bearing fact** — `[CODE] loremaster/store/_txn.py:116-183`:
  `SurrealStoreError(RuntimeError)` is the base; **`SurrealConnectionError(SurrealStoreError)`**
  (`:120`) and **`TxnContentionExhaustedError(SurrealStoreError)`** (`:156`) are SUBCLASSES.
  `TxnContentionExhaustedError.__init__(message, *, attempts, elapsed_seconds)` (`:180`). Because
  the transport/contention errors subclass `SurrealStoreError`, a naive `except SurrealStoreError:
  raise KeepStoreError` would SWALLOW them — the wrap MUST re-raise them FIRST.
- **Why they pass through** — store ref §3 (Transactions): client-side conflict retry is
  mandatory and lives in the retry/lifecycle layer (`retry_on_conflict` / `_ensure_connection`);
  `TxnContentionExhaustedError`'s own docstring (`_txn.py:165-170`) says a caller that must not
  treat exhausted contention as a domain outcome "opts in by catching THIS type FIRST, above its
  own `SurrealStoreError` handler" — exactly `PrincipalStore.create`'s shape (`principals.py:432-437`).
- **The reference idiom to mirror** — `PrincipalStore.create`/`set_subject` (`principals.py:432-437`,
  `:560-568`): `except (SurrealConnectionError, TxnContentionExhaustedError): raise` THEN
  `except SurrealStoreError as error: raise PrincipalStoreError(...) from error`.
- **`KeeperLockoutError`/`KeepNotFoundError` subclass `KeepStoreError`** — `keeps.py:155/159`.
- Ghost-endpoint refusal (ENFORCED) and closed-domain ASSERT rejections are store ref §4 / §1.1.

---

## Q2b — wave-1 KeepStore error-wrapping pins (`loremaster/tests/test_keeps_store.py`)

The sidecar (FR-2 Q2 = ruling (b)) requires KeepStore to WRAP raw `SurrealStoreError` →
`KeepStoreError` at EVERY write boundary (consumer-law parity with `PrincipalStore`), while
`SurrealConnectionError`/`TxnContentionExhaustedError` pass through. Wave-1 `keeps.py` (committed
`efccdc8`) does NOT wrap — it leaks raw at all four write paths. My pins force the wrap and are RED
against that unwrapped tree. New test class `TestKeepStoreWrapsEngineRejections`.

### The pins

1. **Per-write-path BEHAVIOURAL pins (real engine rejections)** — 3 of 4 paths have a natural
   engine reject:
   - `create_keep` bad `--type` → the type ASSERT rejects → **`test_a_REJECTED_create_keep_leaves_NO_keep_row`
     TIGHTENED** from `pytest.raises(Exception)` to `pytest.raises(KeepStoreError)` (corpse fix, below).
   - `create_keep` ghost-keeper edge → ENFORCED rejects → **`test_create_keep_is_ATOMIC_…`
     TIGHTENED** likewise.
   - `add_household_member` to a ghost keep → ENFORCED rejects the ghost OUT endpoint →
     **`test_add_household_member_wraps_a_ghost_keep_engine_rejection`** (new).
   - `set_rank` to an unruled rank (member is a real household member first, so the UPDATE matches
     and the ASSERT fires) → **`test_set_rank_wraps_an_unruled_rank_engine_rejection`** (new).
   - ⚠ `remove_household_member`'s DELETE **cannot naturally reject** via the public API (a DELETE
     of a non-matching row is a no-op; the only pre-write raise is the domain `KeeperLockoutError`).
     Its wrap coverage therefore comes from the fault-injection pin, NOT a real-reject pin — stated
     openly, not papered over.

2. **The DERIVED coverage pin (reach law #344/#345 — the sidecar's explicit rider)** —
   `test_each_write_path_wraps_engine_rejection_as_KeepStoreError`, parametrized over a set that is
   **DERIVED from production truth, never a hand-list**:
   - `_derive_keepstore_write_paths()` AST-scans `keeps.py` for KeepStore public `async def`s whose
     OWN body (docstring excluded) contains a string literal whose **first whitespace-delimited
     token** is a mutating SurrealQL keyword (`CREATE/RELATE/UPDATE/DELETE/INSERT/UPSERT`). The
     whole-word check stops `"created keep … did not read back"` from false-matching `CREATE`;
     dropping the docstring stops the `"""Create a keep …"""` prose from doing the same. f-string
     literal parts are `ast.Constant` under a `JoinedStr`, so the CREATE/RELATE fragments are seen.
   - Derived set today = `{create_keep, add_household_member, remove_household_member, set_rank}`;
     read verbs (`get_keep`/`list_*`, only `SELECT`) and `ensure_ready` (GENERATED DDL — no literal
     mutating statement) are excluded.
   - **How a new write path reddens it:** `test_the_derived_write_path_set_matches_the_coverage_map`
     asserts `derived == set(_WRITE_PATH_INVOCATIONS)`. A new write verb grows the DERIVED set but
     not the coverage map → the equality reds, forcing a coverage entry (the observed set cannot
     silently lag production truth). **Positive control:** the pin also asserts the derivation
     EXCLUDES the read verbs — a derivation returning "all public methods" would fail it. (Both
     mutation-proven, §Mutation proofs.)
   - Injection point: the shared `keeps.run_query` / `keeps.execute_transaction` module seams are
     monkeypatched to raise `SurrealStoreError`; the COMPOSED `PrincipalStore`'s
     `principals`-module `run_query` is UNPATCHED, so email resolution still succeeds and the WRITE
     seam is what raises. Injecting at the shared seam proves the WHOLE verb wraps — including a read
     inside a write verb (that is how `remove_household_member`'s internal `get_keep` is covered).
   - ⚠ **Stated reach bound** (honesty per the reach law): the scan detects a mutating statement
     LITERAL in the public method's OWN body; a future write verb routing its mutation entirely
     through a PRIVATE helper (no literal in the public body) would escape it. Re-open trigger
     documented in the helper's docstring: *the first KeepStore write verb that delegates its
     mutation to a private helper.*

3. **The PASS-THROUGH discriminator** — `test_each_write_path_propagates_transport_faults_untouched`,
   parametrized over `derived-set × {connection, contention}`: inject `SurrealConnectionError` /
   `TxnContentionExhaustedError` at the seam and assert it PROPAGATES (not masked as `KeepStoreError`).
   This is the pin the coverage pin cannot see — WITHOUT it, a catch-all wrong build
   (`except SurrealStoreError: raise KeepStoreError`, no re-raise first) passes the entire wrap
   contract. GREEN today (unwrapped keeps.py propagates) AND after the correct fix; RED only against
   the catch-all wrong build (mutation-proven, §Mutation proofs).

4. **Corpse-test fix.** `test_a_REJECTED_create_keep_leaves_NO_keep_row` and
   `test_create_keep_is_ATOMIC_…` caught a bare `Exception` — GREEN whether KeepStore wraps or leaks
   (a raw `SurrealStoreError` IS an `Exception`). Tightened to `pytest.raises(KeepStoreError)`; the
   now-moot `NotImplementedError` stub-guards (the CRUD is built) were removed. **RED-today IS the
   mutation proof**: today's `keeps.py` is literally the "wrap removed" build, and both tightened
   tests flip GREEN→RED (verified below).

Pass-through preserved: the wrap is SPECIFICALLY `except SurrealStoreError` with the
connection/contention re-raise FIRST — never bare `Exception`. No wave-1 pin for the pass-through
existed; I added it (points 3).

---

## Q1 — `dm --name` REJECT pin (`loremaster/tests/test_keeps_cli.py`)

The sidecar RULED (FR-2 Q1, overriding the wave-2 author's ignore-and-store-None recommendation):
`create-keep --type dm --name X` REJECTS with exit 1, a teaching stderr line, and NO keep written.
Added `test_create_keep_dm_with_a_name_is_rejected` in `TestCreateKeepPerTypeNameRule`, mirroring the
existing project/team-without-name reject:

- `rc == 1` (a DISPATCH-level laundered `ValueError`, exit 1 — NOT a parser-level exit 2, per the
  ruling: `keep.name` stays `option<string>`, the per-type policy lives in the CLI).
- stderr starts with `lore-adm:` (loud, laundered) AND teaches — `"name" in err.lower()` and
  `"dm" in err.lower()` (proves the message names the offending option AND the type, without
  over-pinning exact prose).
- `list_keeps_for_keeper(_KEEPER) == []` — no keep created (the check precedes the store write, no
  partial state).

New required behaviour (the existing contract left `dm --name` unpinned — its F2 flag). RED at the
current stub (behaviourally — `build_keep_store` raises `NotImplementedError` before the handler runs).

Also fixed one STALE docstring in the same file (`test_add_household_to_a_nonexistent_keep_is_loud_and_nonzero`)
that taught the retired "KeepStore does not wrap it as KeepStoreError" mechanism (#398 class) — now
reflects the Q2b wrap AND documents that it doubles as a CLI-level guard that the wrap happened.

---

## D1 — CLI stub catch (`loremaster/loremaster/principals.py`, `_dispatch_keep` only)

Now that KeepStore wraps (Q2b), `_dispatch_keep` catches `KeepStoreError` — symmetric with
`_dispatch` catching `PrincipalStoreError` — NOT the raw `SurrealStoreError`. Change:

```
except (KeepStoreError, SurrealStoreError, SurrealConnectionError, ValueError)   # before (wave-2 stub)
except (KeepStoreError, SurrealConnectionError, ValueError)                      # after (FR-2 D1)
```

**Catch coverage confirmed right** (the brief asked me to): `KeeperLockoutError` and
`KeepNotFoundError` both SUBCLASS `KeepStoreError` (`keeps.py:155/159`), so `KeepStoreError`
subsumes them — listing them separately (as the brief's target set spelled it) is redundant, and
`_dispatch`'s own pattern catches `PrincipalStoreError` alone (not `PrincipalNotFoundError`
separately). `SurrealConnectionError` stays (KeepStore passes it through — a dead socket during a
verb); `ValueError` stays (the per-`type` `--name` CLI-input check). `SurrealStoreError` removed
(KeepStore no longer leaks it). Its import stays used by `PrincipalStore.create`/`set_subject`
(`:437/:563/:724`), so no orphaned import. Docstring updated (the stale "does NOT wrap" prose).

⚠ **D1↔Q2b coupling (intended, defense-in-depth):** removing `SurrealStoreError` from the catch
makes the wave-2 CLI ghost-keep test a SECONDARY guard that the Q2b wrap happened — if KeepStore
leaked a raw `SurrealStoreError`, `_dispatch_keep` would no longer catch it and the CLI would crash
instead of exiting 1. The full reference build (wrap + CLI) satisfies it; a CLI build WITHOUT the
wrap reddens it. Noted so the builder lands both.

---

## RED / GREEN (scoped to HEAD `ea03ea6` + the 3 uncommitted files — today's tree, keeps.py unwrapped at `efccdc8`)

`uv run pytest -n auto tests/test_keeps_store.py` → **8 failed / 35 passed** (5.73s). The 8 REDs
(all behavioural — raw `SurrealStoreError` / injected `SurrealStoreError` escaping
`pytest.raises(KeepStoreError)`; verified right-reason):
- `TestCreateKeep::test_a_REJECTED_create_keep_leaves_NO_keep_row` (tightened) — real engine
  `SurrealStoreError: … statement 2 of 4 … (assert violation)`.
- `TestCreateKeep::test_create_keep_is_ATOMIC_a_failed_keeper_edge_leaves_NO_keep_row` (tightened).
- `TestKeepStoreWrapsEngineRejections::test_each_write_path_wraps_engine_rejection_as_KeepStoreError`
  ×4 (`create_keep`, `add_household_member`, `remove_household_member`, `set_rank`) — injected
  `SurrealStoreError` unwrapped.
- `…::test_add_household_member_wraps_a_ghost_keep_engine_rejection` (behavioural).
- `…::test_set_rank_wraps_an_unruled_rank_engine_rejection` (behavioural).

35 GREEN include the REACH pin (`test_the_derived_write_path_set_matches_the_coverage_map`), the 8
PASS-THROUGH cases (green today — the unwrapped store propagates — they red only on the WRONG fix),
and all 26 pre-existing wave-1 tests.

`uv run pytest -n auto tests/test_keeps_cli.py` → my `test_create_keep_dm_with_a_name_is_rejected` is
RED at stub (behavioural `NotImplementedError` from `build_keep_store`), alongside the 19 other
wave-2 CLI pins that are RED at stub. The parser-surface / creds-free-structural pins stay green.

`tests/test_principals_cli.py` → **45 passed** — my `_dispatch_keep` D1 edit did NOT regress the 9
existing principal/key verbs.

## Gates

- **ruff** (`uv run ruff check .`): `All checks passed!`
- **mypy** (`./scripts/typecheck.sh`): every member OK — `loremaster OK (222 source files)`,
  lorerunes/lorescribe/loresigil/skills/docs/scripts all OK, shellcheck OK.

## Satisfiability (the 0-failed receipt against a known-correct reference build)

Per the repo's "A CONTRACT SHIPS WITH A SATISFIABILITY RECEIPT" law, I built the reference in an
isolated `scripts/scratch_copy.sh` copy (`/tmp/pkt60w2b-ref`) — **provenance ASSERTED inside the
copy** (`PROVENANCE: /tmp/pkt60w2b-ref/loremaster/loremaster/__init__.py`, and `scratch_copy.sh`'s
own provenance gate passed: all workspace members import from inside DEST). The reference build:
- `keeps.py`: wrapped all 4 write methods (`except (SurrealConnectionError,
  TxnContentionExhaustedError): raise` THEN `except SurrealStoreError: raise KeepStoreError(...) from
  error`), mirroring `PrincipalStore.create` verbatim.
- `principals.py`: implemented `build_keep_store` (mirror `build_principal_store`) + the 4 `_cmd_*`
  keep handlers + the per-`type` `--name` rule (project/team require, `dm` forbids — the Q1 reject).

`uv run pytest -n auto tests/test_keeps_store.py tests/test_keeps_cli.py` in the scratch →
**83 passed / 0 failed**. The Q2b + Q1 + D1 pins ALL go green against the correct build, and the
pre-existing wave-1 + wave-2-structural pins stay green. My pins are satisfiable, together.

## Mutation proofs (the discriminating pins actually bite)

Both run in the scratch reference build:
1. **Pass-through pin discriminates the catch-all wrong build.** Removed the
   `except (SurrealConnectionError, TxnContentionExhaustedError): raise` line from `create_keep`
   (the naive catch-all). →
   `test_each_write_path_propagates_transport_faults_untouched[create_keep-connection]` and
   `[create_keep-contention]` **RED** (KeepStoreError masked the transport fault), while the 6 other
   correctly-wrapped cases stayed GREEN. Restored → green.
2. **Reach pin reds on a new write path.** Added a dummy `async def delete_keep(self)` with a
   `DELETE type::record(...)` literal. →
   `test_the_derived_write_path_set_matches_the_coverage_map` **RED**:
   `derived=[…, 'delete_keep', …]` vs `mapped=[…]`, "Extra items in the left set: 'delete_keep'".
   The AST derivation detected the new write verb and the coverage-as-checked-variable equality
   forced a failure. Removed → green.

(The wrap pins' mutation proof in the "wrap removed" direction is the RED/GREEN table above:
today's unwrapped `keeps.py` IS that mutation, and every wrap pin is red against it.)

## Fixtures-discriminate self-audit ("what WRONG build passes this?")

- **Coverage pin (injection):** a build wrapping SOME paths but not others → the unwrapped path's
  parametrized case reds. A build that wraps nothing → all 4 red. A build catching bare `Exception`
  → passes the injection pin BUT the PASS-THROUGH pin reds (catch-all masks transport). Both needed.
- **Pass-through pin:** a naive `except SurrealStoreError: raise KeepStoreError` (no re-raise first)
  → reds (proven). A correct wrap → green. Today's no-wrap → green (guard, not a corpse — it fires
  only on the wrong fix).
- **Reach pin:** a derivation returning "all public methods" → fails the read-verb-exclusion
  positive control. A hand-list of 4 → would pass today but NOT red on a new write path; my derived
  set does red (proven). A new write verb with no coverage entry → reds.
- **Behavioural add/set:** a build that wraps only `create_keep` (the sidecar's named partial-fix
  hazard) → `add_household_member`/`set_rank` behavioural pins red. Real engine rejections (ENFORCED
  ghost, rank ASSERT), not injected — robust to "injection ≠ reality".
- **Q1 dm-reject:** a build that ignores `--name` for dm (rc 0, keep created) → reds on `rc == 1`
  AND `keeps == []`. Parser-level reject (exit 2) → reds on `rc == 1`. Silent reject → reds on the
  `lore-adm:` prefix. Non-teaching message → reds on the `name`/`dm` content check. Uses a real dm
  create (no monoculture — the sibling positive controls create project/team/session).

## Flags / decisions-needed

- **F-DRY (surfaced, NOT resolved by me):** ruling (b) makes KeepStore the SECOND store to encode
  the wrap-classification policy. The sidecar's ONE-IMPLEMENTATION escalation (FR-2 §"⚠ DRY FLAG")
  recommends extracting a `wrap_engine_rejection(DomainError, context)` seam into **`lorerunes`**,
  called by BOTH `PrincipalStore` and `KeepStore`, prove-by-mutation. That reaches into committed
  48/49 code and is a **ledgered follow-up with a named trigger** (*the moment a THIRD store/consumer
  needs the same wrap*), NOT part of this unblock fix. My pins are BEHAVIOUR-parity pins (wrap →
  KeepStoreError; transport passes through), not SHARING pins — when the `lorerunes` extraction
  lands, they stay green and the extraction adds the prove-by-mutation. **Recommend the lead file the
  `lore_findings` DRY task now** (the sidecar asked for this), so it is durable.
- **Scratch copy `/tmp/pkt60w2b-ref` left behind** — `rm -rf` denied by policy (3 attempts). Not a
  git worktree; disposable. Reclaim with `scratch_copy.sh --force /tmp/pkt60w2b-ref` or `rm -rf`.

## Task / comms

- Task `2f4336f948d44002b328e955d539a846` claimed + in_progress (→ done on close).
- Registered on `lore_comms` as `contract-60-w2b` (session pkt60, role contract).
