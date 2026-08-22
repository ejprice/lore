# REPORT-contract-60-w2d — FR-3 test-only pins (remove-household ghost-keep loudness)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done.
- **Task:** FR-3 (sidecar ruling reading (a), `docs/design/2026-08-22-packet60-keep-substrate-rulings.md`): make `remove_household_member` LOUD on a GHOST keep (raise `KeepNotFoundError` → CLI exit 1), preserving the deliberate member-dimension asymmetry (real principal not in a real keep → benign rc-0 no-op). Test-only pins; I did NOT touch `keeps.py`/`principals.py`.
- **Deviations:** (1) dropped a `result is None` assertion in the store asymmetry pin — `remove_household_member` is typed `-> None`, so assigning its result trips mypy `func-returns-value`; the behavioural pin is "does NOT raise" + household-unchanged (documented in the pin). (2) A disposable scratch copy remains at `/tmp/pkt60-w2d-ref` — my `rm -rf` cleanup was permission-denied; it is an ephemeral rsync copy (not a git worktree), safe to delete.
- **Packages considered:** none — no mechanism specified (test-only pins; the `argparse`/`ast` parser introspection reuses the established in-file reach-derivation idiom).
- **Reuse ledger:** 3 new test-local symbols, all dispositioned (below) — the reach-derivation pattern EXTENDS the existing in-file idiom, no shared policy introduced.
- **Graded:** `5b7180c` · HEAD-at-report `5b7180c` · SAME. (I render a verdict on the CURRENT `keeps.py`: silent-on-ghost — RED against my ghost pin.)
- **Decisions needed:** none. FR-3 is a fully-ruled reading (a); no ambiguity beyond it arose.
- **Receipt pointers:** store pins → `loremaster/tests/test_keeps_store.py::TestRemoveHouseholdMember` (`test_remove_household_on_a_GHOST_keep_is_LOUD_KeepNotFoundError`, `test_remove_a_non_member_from_a_REAL_keep_is_a_benign_no_op`); CLI ∀-verb → `loremaster/tests/test_keeps_cli.py::TestANonexistentKeepIsLoudForEveryKeepConsumingVerb`; gate tails → §Gates below.

---

## 1. The pins written (test files ONLY)

### 1a. STORE — `loremaster/tests/test_keeps_store.py`, class `TestRemoveHouseholdMember`
Added `MEMBER_OF_RELATION` to the `surreal_schema` import, plus two methods:

- **`test_remove_household_on_a_GHOST_keep_is_LOUD_KeepNotFoundError`** — remove a member on a keep id **never created** (a real ghost, `ghost_id(...)`) → `pytest.raises(KeepNotFoundError)` **AND** the total `member_of` edge count is unchanged. A REAL keep + REAL member (bob) are seeded first (create_keep auto-adds the keeper (Fork D) → ≥2 real edges), so the no-delete leg is **non-vacuous** — a wrong build that deleted edges regardless of the ghost target (e.g. a `DELETE … WHERE in = $member` missing the `out = $keep` clause) is caught. The `--member` (bob) resolves, so the loudness is about the KEEP, not an unresolvable member (fixtures discriminate). Cites store ref §2 (a `DELETE … WHERE` no-match is a no-op — the exact current silent behaviour).
- **`test_remove_a_non_member_from_a_REAL_keep_is_a_benign_no_op`** — a REAL principal (dave, seeded, not the keeper, not a member) removed from a REAL keep → does **NOT** raise; the household is untouched (keeper still present). Pins the DELIBERATE asymmetry (ruling: *you can idempotently REMOVE a nonexistent membership but cannot SET the rank of one*). **GREEN before AND after** the amend — the positive control the ghost pin needs.

**Why BOTH (fixtures-must-discriminate):** the ghost pin requires a RAISE on a ghost keep; the asymmetry pin requires NO raise on a REAL keep with an absent member. A wrong build that "fixes" loudness by raising `KeepNotFoundError` on **every** absent membership (collapsing ghost-keep and absent-member into one behaviour) passes the ghost pin but **fails** the asymmetry pin. Neither pin alone catches that collapse.

### 1b. CLI — `loremaster/tests/test_keeps_cli.py`, class `TestANonexistentKeepIsLoudForEveryKeepConsumingVerb`
Added `import argparse` + a reach-derivation + coverage map + two pins:

- **`test_the_derived_keep_verb_set_matches_the_ghost_keep_coverage_map`** (offline reach pin, #344/#345) — `_derive_keep_verbs_taking_keep()` introspects the REAL `build_parser()` and returns every subcommand whose subparser carries a `--keep` option (a STRUCTURAL property, not a hand-list). It must equal `set(_KEEP_VERB_GHOST_KEEP_ARGV)`. Positive control: `create-keep` (which takes `--keeper`, not `--keep`) is NOT in the derived set. **A NEW keep verb taking `--keep` grows the derived set and reds this pin unless it is also added to the loud-on-ghost map** — coverage-as-checked-variable.
- **`test_a_nonexistent_keep_is_a_loud_exit_1[add-household|remove-household|set-rank]`** (∀ behavioural) — each keep-consuming verb with a ghost `--keep` (and a REAL seeded `--member`) → exit 1 + a `lore-adm:` stderr line. Pinned **∀-over-the-verbs**, not re-conditioned on the single verb (`remove`) that prompted R3.

**How the ∀-invariant reddens on a new verb (the reach requirement):** the verb set is DERIVED from `build_parser()` (production truth). Add a future keep verb that takes `--keep` → `_derive_keep_verbs_taking_keep()` grows → the coverage-pin equality fails (the observed loud-on-ghost map lags) → the author must add its ghost invocation, i.e. must decide/prove it is loud-on-ghost. The observed set cannot silently lag the parser. **Stated bound (reach-law honesty, in the derivation docstring):** it covers verbs naming the keep by the flag `--keep`; a future verb naming it `--keep-id`/positionally escapes — re-open trigger named there.

**Why all three are loud (why the invariant is satisfiable):** `_dispatch_keep` (committed, `principals.py:1209-1215`) catches `(KeepStoreError, SurrealConnectionError, ValueError)` and prints `f"{_CLI_PROG}: {error}"` + returns 1. On a ghost keep: `add-household` → ENFORCED refuses the ghost RELATE → `SurrealStoreError` WRAPPED as `KeepStoreError` (FR-2 Q2b) → exit 1; `set-rank` → UPDATE no-match → readback None → `KeepNotFoundError` → exit 1; `remove-household` → the NEW FR-3 keep-existence check → `KeepNotFoundError` → exit 1. `KeepNotFoundError`/`KeeperLockoutError` subclass `KeepStoreError`, all caught by one clause.

---

## 2. RED / GREEN receipts (measured this session, at `5b7180c`)

`pytest -n auto` against spike-surreal `ws://127.0.0.1:18000` (confirmed reachable). Store fully built; CLI at the wave-2 STUB.

**Store class, current tree (no FR-3 amend):**
```
FAILED loremaster/tests/test_keeps_store.py::TestRemoveHouseholdMember::test_remove_household_on_a_GHOST_keep_is_LOUD_KeepNotFoundError
  E   Failed: DID NOT RAISE <class 'loremaster.keeps.KeepNotFoundError'>   (line 507)
1 failed, 3 passed
```
→ ghost pin **RED** (the current silent-on-ghost no-op), asymmetry pin + 2 existing **GREEN**.

**Full store file, current tree:** `1 failed, 44 passed` — only the intended-RED ghost pin fails; no collateral breakage.

**CLI ∀-verb class, current STUB tree:**
```
FAILED ...::test_a_nonexistent_keep_is_a_loud_exit_1[set-rank]
FAILED ...::test_a_nonexistent_keep_is_a_loud_exit_1[add-household]
FAILED ...::test_a_nonexistent_keep_is_a_loud_exit_1[remove-household]
  E   NotImplementedError: build_keep_store is a stub (contract-60-w2)   (principals.py:882)
3 failed, 1 passed
```
→ 3 behavioural **RED** at stub; coverage/reach pin **GREEN** (structural guard). **No false-green risk:** the stub `NotImplementedError` is raised by `build_keep_store` OUTSIDE `_dispatch_keep`'s `try`, and is NOT in the caught tuple, so it propagates (the call errors) — it cannot be mistaken for a laundered exit 1.

---

## 3. Satisfiability + mutation-proof receipt (scratch reference build)

Per `scratch_copy.sh` (#140 provenance-asserted). The scratch ran its OWN code:
```
loremaster.__file__ = /tmp/pkt60-w2d-ref/loremaster/loremaster/__init__.py
```

**Store — FR-3 reference amend** to `remove_household_member` (fold the existence read into the read the keeper-lockout guard already does — the FR-3 rider; `get_keep` is already the DIRECT `SELECT … FROM type::record('keep',$id)` empty=absent signal, NOT the "keeper is None" proxy):
```python
            keep = await self.get_keep(keep_id)
            if keep is None:
                # FR-3: a ghost keep is LOUD (access-control verb — a typo'd --keep must not
                # read as a silent "access removed"). Raised BEFORE the DELETE, so nothing changes.
                raise KeepNotFoundError(
                    f"no keep {keep_id!r} exists — cannot remove a household member from it"
                )
            if keep.keeper_id == member_id:
                ...  # existing KeeperLockoutError guard, unchanged
```
(`KeepNotFoundError` subclasses `KeepStoreError` which subclasses `RuntimeError`, NOT `SurrealStoreError`, so it is NOT re-wrapped by the `except SurrealStoreError` clause — it propagates cleanly, exactly as the existing `KeeperLockoutError` does.)

Result on the reference: `TestRemoveHouseholdMember` → **`4 passed`**. So the ghost pin is **RED without the check / GREEN with it** — the mutation proof in both directions (current-tree = mutation removed = RED; scratch amend = restored = GREEN). The asymmetry pin is **GREEN both ways**.

**CLI — minimal reference** (build_keep_store mirroring `build_principal_key_store`; the 3 keep handlers routing to the store — `create-keep` not needed by these pins):
```python
def build_keep_store(config: LoreConfig) -> KeepStore:
    from loremaster.config import resolve_config_value, resolve_secret
    from loremaster.keeps import KeepStore
    return KeepStore(url=config.surreal.url, namespace=config.surreal.namespace,
        database=config.effective_surreal_database,
        user=resolve_config_value(config.surreal.user_env),
        password=resolve_secret(config.surreal.password_env))

async def _cmd_add_household(args, keep_store) -> int:
    await keep_store.add_household_member(keep_id=args.keep, member_email=args.member); return 0
async def _cmd_remove_household(args, keep_store) -> int:
    await keep_store.remove_household_member(keep_id=args.keep, member_email=args.member); return 0
async def _cmd_set_rank(args, keep_store) -> int:
    await keep_store.set_rank(keep_id=args.keep, member_email=args.member, rank=args.rank); return 0
```
Result on the reference: `TestANonexistentKeepIsLoudForEveryKeepConsumingVerb` → **`4 passed`** (coverage pin + all 3 behavioural ghost pins GREEN). So the CLI ∀-verb pins are satisfiable on a correct build.

(The scratch tree was removed conceptually; the actual `rm -rf` was permission-denied — see the deviation. The two reference patches are pasted verbatim above so the claim is reproducible without it — brief-base §1 "an instrument you built is a deliverable".)

---

## 4. Fixtures self-audit ("what WRONG build would still pass this?")

| pin | a wrong build it CATCHES | discrimination mechanism |
|---|---|---|
| store ghost | silent no-op on a ghost keep (today) | `pytest.raises(KeepNotFoundError)` — RED today |
| store ghost | an over-broad DELETE that ignores `out=$keep` | seeded real edges + unchanged `member_of` count |
| store asymmetry | a build that raises on EVERY absent membership | NO-raise on a REAL keep + absent member (GREEN both ways) |
| CLI coverage | a per-verb pin missing a new keep verb (R3's class) | derived-vs-map equality reds when the parser grows |
| CLI coverage | a derivation returning all keep verbs | `create-keep not in derived` positive control |
| CLI ∀ behavioural | remove silent on ghost (rc 0); any verb crashing uncaught | `rc == 1` + `lore-adm:` stderr, per verb |

- **Ghost vs unresolvable-member:** every ghost fixture uses a REAL seeded `--member`/`member_email`, so the loudness is attributable to the KEEP, not a member typo.
- **Small-N / value monoculture:** N/A here (boolean loud/quiet outcomes); the ∀ set is derived, not a hand-list, so it cannot silently narrow.

---

## 5. Reuse ledger (brief-base §6)

| new symbol (test-local) | lore query run | what it returned | disposition |
|---|---|---|---|
| `_derive_keep_verbs_taking_keep` (cli) | read the SAME file's `TestBuildKeepStoreFactory` AST-scan + store file's `_derive_keepstore_write_paths` | the established per-file reach-derivation idiom (each test file derives its own coverage set from production truth) | **EXTENDED** the in-file idiom — a per-file derivation is the PATTERN (not shared policy: the derived property differs — write-methods vs `--keep`-consuming verbs), so a shared helper would be wrong. Mirrors `_derive_keepstore_write_paths`. |
| `_KEEP_VERB_GHOST_KEEP_ARGV` / `_GHOST_KEEP` (cli) | same | mirrors `_WRITE_PATH_INVOCATIONS` (store) / `_NAME_POLICY_BY_TYPE` (cli) coverage-map idiom | **EXTENDED** the coverage-map idiom; `_GHOST_KEEP` reuses the imported `ghost_id` helper (not a new id generator). |

No shared/cross-caller policy introduced — these are test-file-local reach instruments following the established idiom in these exact files.

---

## 6. Gates (this session, at `5b7180c`)
- `uv run ruff check loremaster/tests/test_keeps_store.py loremaster/tests/test_keeps_cli.py` → **All checks passed!**
- `bash scripts/typecheck.sh` (canonical) → **all members OK** (`loremaster OK` over 222 files; lorerunes/lorescribe/loresigil/skills/docs-eval/scripts OK; shellcheck OK). No packet-39 red surfaced. (One error I introduced — `func-returns-value` at test_keeps_store.py:536 — was FIXED before this receipt.)
- Live pytest tails: §2 above.

## 7. Dogfood / friction
lore tools used first-choice for orientation (registered on `lore_comms`, claimed the task). No lore weakness hit; no grep fallback for a structure question (greps used were for line-locating within known files — not a structure query). No finding filed.
