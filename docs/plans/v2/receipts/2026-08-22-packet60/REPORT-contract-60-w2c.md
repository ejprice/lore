# REPORT-contract-60-w2c — packet 60 wave 2c CONTRACT REVISION (adversary blocker + R1/R2)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK

- **state:** done — the adversary's ONE blocker + both LOW residuals are closed in
  `loremaster/tests/test_keeps_cli.py` (test-only), gated, and satisfiability-proven against a
  reference build in a provenance-asserted scratch copy.
- **BLOCKER closed:** `TestAdversarySetRankErrorPath` — a `set-rank --rank overlord` reject pin
  (rc 1 + `lore-adm:` stderr) + its positive control. Forces `_cmd_set_rank` to ROUTE to the
  store (a no-op `return 0` can't pass). Mutation-proven RED on the exact no-op WB1.
- **R1 closed:** `test_every_keep_type_has_a_declared_name_policy` — per-`type` `--name` coverage
  is now a CHECKED VARIABLE (`_NAME_POLICY_BY_TYPE` == `_KEEP_TYPES`); the 3 per-type parametrized
  cases DERIVE from the map, so a new keep type without a policy fails CLOSED (reach law #344/#345).
- **R2 closed:** the project/team-WITHOUT-`--name` reject tightened to `rc == 1` + a TEACHING
  stderr (names `--name` + the type) — symmetric with the `dm --name` reject.
- **deviations:** none material. Scratch `/tmp/pkt60w2c-ref` left behind (disposable; `rm -rf`
  guardrail typically denies — reclaim with `scratch_copy.sh` or operator `rm -rf`).
- **Packages considered:** none — no mechanism specified (test-only pins on the existing CLI).
- **Reuse ledger:** none — no production reusable symbol. New symbols are TEST-LOCAL constants in
  `test_keeps_cli.py` (`_NAME_POLICY_BY_TYPE`, `_NAME_REQUIRED/_ALLOWED/_FORBIDDEN`,
  `_NAME_REQUIRING_TYPES/_NAMELESS_OK_TYPES/_NAME_ACCEPTED_TYPES`), mirroring the file's existing
  `_KEEP_TYPES`-derived idiom.
- **Graded:** `5b7180c` (HEAD) + the 2 uncommitted contract files · HEAD-at-report `5b7180c` ·
  SAME. Satisfiability graded against a scratch reference build on top of this tree (§Satisfiability).
- **decisions-needed:** none — the blocker + R1 + R2 were the lead's directive; all satisfiable.
- **receipts:** RED@stub → §RED/GREEN; satisfiability 43/0 + provenance → §Satisfiability;
  blocker mutation proof → §Blocker mutation; gates → §Gates; fixtures self-audit → §Fixtures.

---

## What changed (all in `loremaster/tests/test_keeps_cli.py`)

### BLOCKER — set-rank error-path pin (`TestAdversarySetRankErrorPath`)
The adversary (`REPORT-adversary-60-w2.md` §Blocker/§Instruments) proved a NO-OP `_cmd_set_rank`
(`return 0`, never calling the store) passes the WHOLE contract, because the only legal rank
(`contributor`) EQUALS the default written by `add_household_member`, and `set-rank` was the sole
write verb with no error-path pin. Added the adversary's exact pin class (2 tests), adapted to this
file's idiom (`_add` / `_create_keep` / `_run_cli` / `cli_env.argv` / `p_module._CLI_PROG` /
`_KEEP_RANK_CONTRIBUTOR` — all already the file's helpers, no rename needed):

- `test_set_rank_with_an_unruled_rank_is_loud_and_nonzero` — adds `_KEEPER` + `_MEMBER`, creates a
  keep, `add-household --member _MEMBER` (so `_MEMBER` is a REAL household member — the UPDATE
  matches a row and the closed `rank` ASSERT fires), then `set-rank --rank overlord` → asserts
  `rc == 1` AND stderr starts with `lore-adm:`. The store's rank ASSERT rejects → `KeepStoreError`
  (FR-2 Q2b wrap) → laundered by `_dispatch_keep`. A no-op handler returns 0 → reds `rc == 1`.
- `test_set_rank_with_the_legal_rank_still_succeeds` (positive control) — `--rank contributor` on a
  real member → `rc == 0`.

Consistent with sidecar Fork F: proves the verb is NOT a silent no-op; does NOT gate 60 on
multi-rank behaviour (only `contributor` is legal today).

### R1 — derived per-type name-policy coverage (fold-in)
Introduced `_NAME_POLICY_BY_TYPE = {project: require, team: require, session: allow, dm: forbid}`
as the test's OWN name-policy map, plus 3 policy constants and 3 DERIVED type lists
(`_NAME_REQUIRING_TYPES`, `_NAMELESS_OK_TYPES`, `_NAME_ACCEPTED_TYPES`). The 3 existing per-type
parametrized cases now derive their `@parametrize` type lists FROM the map (was hand-lists
`["project","team"]` / `["session","dm"]` / `["project","team","session"]`), so the map is the
single source of truth. New pin `test_every_keep_type_has_a_declared_name_policy` asserts
`set(_NAME_POLICY_BY_TYPE) == set(_KEEP_TYPES)` (+ every policy value is one of require/allow/forbid).
A new keep type added to the schema's `_KEEP_TYPES` without a `--name` decision reds this pin
(coverage-as-checked-variable, fail-closed on growth — reach law #344/#345), instead of
parse-accepting via `test_create_keep_accepts_every_schema_type` while its name policy goes unpinned.
This is DEFENSIVE hardening (a new keep type is a future packet with its own contract), not a live
hole — but done as the checked-variable form the reach law prescribes, matching w2b's
`test_the_derived_write_path_set_matches_the_coverage_map` shape.

### R2 — teaching-stderr symmetry (fold-in)
`test_create_keep_without_name_is_rejected_for_name_requiring_types` tightened from `rc != 0` +
no-keep to: `rc == 1` (dispatch-level laundered `ValueError`, NOT a parser-level exit 2) + stderr
starts with `lore-adm:` + `"name" in err.lower() and keep_type in err.lower()` (names the missing
option AND the offending type) + no-keep. Now SYMMETRIC with the `dm --name` reject
(`test_create_keep_dm_with_a_name_is_rejected`), which the sidecar already required to teach.

---

## RED / GREEN (scoped, HEAD `5b7180c` + the 2 uncommitted contract files — stubs raising `NotImplementedError`)

`cd loremaster && uv run pytest -n auto tests/test_keeps_cli.py` → **22 failed / 21 passed** (5.25s,
43 items = 40 pre-existing + 3 new). The RED set is the contract's designed RED-at-stub state — every
live keep verb hits `build_keep_store`'s `NotImplementedError` (`principals.py:882`, before
`_dispatch_keep`'s try, so it is not caught → the verb errors behaviourally, never an ImportError).
My additions, verified in that run:

- `TestAdversarySetRankErrorPath::test_set_rank_with_an_unruled_rank_is_loud_and_nonzero` — **RED** ✓
- `TestAdversarySetRankErrorPath::test_set_rank_with_the_legal_rank_still_succeeds` — **RED** ✓
- `...::test_create_keep_without_name_is_rejected_for_name_requiring_types[project]` — **RED** ✓
- `...::test_create_keep_without_name_is_rejected_for_name_requiring_types[team]` — **RED** ✓
- `TestCreateKeepPerTypeNameRule::test_every_keep_type_has_a_declared_name_policy` — **GREEN** (offline
  structural pin — passes at stub like the parser-surface pins; its discrimination is proven by
  mutation, not by RED-at-stub). Confirmed alone: `1 passed in 0.19s`.

The R1 parametrize rewiring is correct: the run shows the derived cases `[project]`/`[team]`,
`[dm]`/`[session]`, `[project]`/`[session]`/`[team]` — same SETS as the old hand-lists (sorted order).

## Satisfiability (0-failed against a known-correct reference build — repo law)

Built the reference in `./scripts/scratch_copy.sh /tmp/pkt60w2c-ref` (provenance-asserting, #140).
The copy's own gate asserted imports resolve INSIDE the copy; re-printed in the run:

```
PROVENANCE: /tmp/pkt60w2c-ref/loremaster/loremaster/__init__.py
```

Reference = the 5 stubs greened (patcher asserted 5/5 replacements, no stub marker survived):
- `build_keep_store` — lazy `from loremaster.keeps import KeepStore`; `return KeepStore(url=…,
  namespace=…, database=config.effective_surreal_database, user=resolve_config_value(...),
  password=resolve_secret(...))` (mirror `build_principal_store`, minus `dim`).
- `_cmd_create_keep` — per-`type` `--name` rule (`project`/`team` → `raise ValueError("--name is
  required for --type {type}")`; `dm` with a name → `raise ValueError("--name is not valid for
  --type dm (a dm keep has no name concept)")`) then `create_keep(...)` + `print(keep.id)`.
- `_cmd_add_household` / `_cmd_remove_household` / `_cmd_set_rank` — one-line delegations to the
  matching `KeepStore` method, `return 0`.

`cd /tmp/pkt60w2c-ref/loremaster && uv run pytest -n auto tests/test_keeps_cli.py` → **43 passed /
0 failed** (5.82s). So the WHOLE contract — including my blocker reject pin + its positive control,
R1's coverage pin, and R2's tightened teaching-stderr reject — is SATISFIABLE together on a correct
build. In particular:
- **Blocker reject GREEN**: the reference `_cmd_set_rank` calls `store.set_rank`, so `--rank overlord`
  → the rank ASSERT rejects → `KeepStoreError` → `_dispatch_keep` catches → `lore-adm:` stderr + exit 1.
- **R2 GREEN**: the reference `ValueError("--name is required for --type project")` → laundered stderr
  `lore-adm: --name is required for --type project` → starts with `lore-adm:`, `.lower()` contains
  both `name` and `project`. (The require-case teaching message is a NEW requirement R2 adds; I
  verified empirically rather than reason it, since w2b's reference shape did not pin the message text.)
- **R1 GREEN**: offline (part of the 43).

## Blocker mutation (the pin bites the exact wrong build it exists to catch)

Mutated the reference `_cmd_set_rank` back to the adversary's WB1 no-op (`return 0`, never calls the
store) and ran only `TestAdversarySetRankErrorPath`:

```
tests/test_keeps_cli.py::TestAdversarySetRankErrorPath -> 1 failed, 1 passed
FAILED ...::test_set_rank_with_an_unruled_rank_is_loud_and_nonzero  (assert 0 == 1)
       ...::test_set_rank_with_the_legal_rank_still_succeeds         PASSED
```

The reject pin reds on the no-op (rc 0, never routed to the store) while the positive control stays
green (rc 0 is correct for the legal-rank path) — i.e. the pin discriminates the no-op WB1 (RED)
from the correct build (GREEN, from the 43/0 above), exactly the adversary's WB1 signature. This is
the whole point of the pin: `set-rank` can no longer be a silent no-op.

## Fixtures-discriminate self-audit ("what WRONG build passes this?")

- **Blocker reject** — the fixture adds `_MEMBER` to the household FIRST, so the store UPDATE matches
  a real edge and the closed `rank` ASSERT actually fires; a bogus rank on a NON-member would
  no-match (no reject) and the pin would pass vacuously. Discriminates: no-op handler (rc 0) reds;
  parser-level reject would red `rc == 1` too (but `--rank` is a free string, no `choices`, so no
  natural exit-2 build). Positive control proves a legal rank is NOT rejected.
- **R1 coverage pin** — a type DROPPED from the map (observed set shrinks) OR a new `_KEEP_TYPES`
  member with no map entry (production set grows) reds the `==`; a typo'd policy value reds the
  second assertion. A decorative map that DIDN'T drive the parametrize lists would be a 2nd source
  of truth — avoided by deriving the case lists from the map.
- **R2** — a build rejecting with an empty/cryptic message reds the `name`/type content check; a
  parser-level exit-2 reject reds `rc == 1`; a silent success reds `rc == 1` AND no-keep. Uses the
  parametrize type (`keep_type`) in the content assertion, so `project` and `team` each check their
  own type literal (no monoculture on one type's message).

## Gates

- **ruff** (`uv run ruff check loremaster/tests/test_keeps_cli.py`): `All checks passed!`
- **mypy** (`./scripts/typecheck.sh`): every member OK — `loremaster OK (222 source files)`,
  lorerunes/lorescribe/loresigil/skills/docs/scripts all OK, shellcheck OK.

## Scope / flags

- All edits are test-only (`loremaster/tests/test_keeps_cli.py`). No production code touched
  (principals.py / keeps.py untouched — the stubs stay for the builder). The reference build lives
  ONLY in the scratch copy.
- No unrelated failures: every RED in the scoped run is an in-scope keep-verb pin at the designed
  stub state.
- Scratch `/tmp/pkt60w2c-ref` NOT removed (disposable `scripts/scratch_copy.sh` rsync copy in `/tmp`,
  NOT a git worktree; final state carries the WB1 no-op mutation in `_cmd_set_rank`). Reclaim with
  `./scripts/scratch_copy.sh --force /tmp/pkt60w2c-ref` or an operator `rm -rf`.

## Task / comms

- Task `37b8815f8f054dfbbb5382407175750a` claimed + in_progress (→ done on close).
- Registered on `lore_comms` as `contract-60-w2c` (session pkt60, role contract).
