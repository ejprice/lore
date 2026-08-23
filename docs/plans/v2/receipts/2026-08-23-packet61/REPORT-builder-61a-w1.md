# REPORT-builder-61a-w1

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations**
- deviations:
  - Edited TWO test files outside my nominal writable set (`test_keeps_store.py`,
    `test_keeps_cli.py`) — coverage-map entries forced by pre-existing FR-2 Q2b / FR-3
    **reach pins** (coverage-as-checked-variable) that DERIVE write-paths/`--keep`-verbs
    from production and red when a new one is unregistered. My in-scope production change
    (new write methods + new `--keep` CLI verbs) directly caused these reds → brief-base
    §2 exception (regression my change directly causes, fixed minimally, disclosed). NOT
    the 4 contract spec files.
  - Corrected my own first-pass `set_keeper`/`delete_keep` structure: moved the check-first
    `get_keep` INSIDE the wrapping `try` (the `remove_household_member` idiom) so an engine
    `SurrealStoreError` from the internal read is wrapped as `KeepStoreError` — required by
    the FR-2 Q2b consumer-law invariant. Also fixed the `set_keeper` post-update fallback to
    raise `KeepStoreError` (a confirmed-existing keep read-back-None is a store anomaly, not
    "not found"), matching the `create_keep` idiom.
- Packages considered: none — no mechanism specified (all substrate reuse; see Reuse ledger).
- Reuse ledger: 3 new reusable symbols, all dispositioned (below). Store methods/CLI verbs
  route through existing shared seams.
- Graded: n/a (builder, not a verdict-rendering pass).
- decisions-needed: none (D1/D2/D3 already ruled; the 2 test-file edits are disclosed above).
- receipt pointers:
  - gate receipts: §Gates below
  - mutation-proof table: §Mutation proofs
  - files touched: §Files touched

## What was built (§FR-4 + D1/D2/D3)

Production only (`loremaster/loremaster/`):

**`principals.py`**
- `PrincipalHasKeepsError(PrincipalStoreError)` — the typed refusal (laundered by
  `_dispatch`'s existing `except PrincipalStoreError` → `lore-adm:` stderr + exit 1).
- `_COL_KEEP_KEEPER = "keeper"` — the `keep.keeper` column, named once.
- `PrincipalStore.delete` = REFUSE-WHILE-KEEPING: before any DELETE, reads the kept keep ids
  via `SELECT id FROM keep WHERE keeper = type::record('principal', $pid)` (IndexScan on the
  existing `keep_keeper` index, bound param, mirroring the `principal_key` count query, own
  connection — no KeepStore dep). ≥1 kept keep → raise `PrincipalHasKeepsError` naming ALL
  kept ids + the remediation, NO rows removed. Zero kept → today's `principal_key`-only
  cascade proceeds (`member_of` auto-cascades — no explicit DELETE, probe-settled).
- `_dispatch` (principal branch) readies the keep SLICE (`generate_keep_ddl` via
  `build_keep_store`+`ensure_ready`), principal FIRST — D3(a) / #131 dirty-store: a store
  predating packet 60 has no keep table, which would crash the delete's keep-read.
- CLI verbs `set-keeper --keep --new-keeper` / `delete-keep --keep`, handlers
  `_cmd_set_keeper`/`_cmd_delete_keep`, registered in `_KEEP_VERB_HANDLERS` (route to
  `_dispatch_keep`'s `KeepStoreError` launder — NOT the principal path).

**`keeps.py`**
- `KeepStore.set_keeper(*, keep_id, new_keeper_email) -> Keep` — admin set_owner (D1). CHECK
  -FIRST inside the wrapping try: ghost keep → `KeepNotFoundError` (before any UPDATE, no
  phantom upsert); ghost new-keeper email → `KeepStoreError` (resolve first — a
  `record<principal>` write does NOT validate existence, store §2); else UPDATE `keep.keeper`
  to the resolved successor. Transport faults re-raised first; engine rejection → `KeepStoreError`.
- `KeepStore.delete_keep(*, keep_id) -> None` — admin delete (D2). CHECK-FIRST: ghost keep →
  `KeepNotFoundError`; else DELETE the keep node (`member_of` auto-cascades on the out-endpoint
  delete — store §4, probe LEG C; no explicit `member_of` DELETE).

## Reuse ledger (brief-base §6)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `PrincipalStore.delete` refuse-count read | (in-file) mirrors `delete`'s existing `principal_key` count query | same `type::record(...)` bound-param + `_query` idiom, one method up | REUSED the in-method `principal_key`-count pattern (id-projection variant to name the keeps) |
| `KeepStore.set_keeper` / `delete_keep` | read `keeps.py` — `_resolve_principal_id`, `_record_id_part`, `_query`, `get_keep`, `remove_household_member` wrap-idiom all present | existing shared resolver / id-parser / retry-seam / read / check-first-inside-try idiom | REUSED `_resolve_principal_id`, `_record_id_part`, `_query`, `get_keep`; REUSED `remove_household_member`'s `try:(get_keep…);except transport:raise;except SurrealStoreError:wrap` idiom verbatim |
| keep-slice readiness on delete path | read `_dispatch_keep` (same file) | it already builds+readies `build_keep_store()` principal-first | REUSED `build_keep_store` + `generate_keep_ddl`-via-`ensure_ready`; NO new emitter (packet 60's `generate_keep_ddl` reused) |

New symbols introduced (non-policy): `PrincipalHasKeepsError` (a required typed error — no
existing "keeps keeps" error to reuse), `_COL_KEEP_KEEPER` (a column-name constant),
`_cmd_set_keeper`/`_cmd_delete_keep` (thin CLI handlers delegating to the store). None
duplicate an existing POLICY (retry/backoff/classification/validation) — all such policy is
routed through the shared `_query`/`_dispatch_keep` seams.

## Gates (receipts)

- **Target contract (4 files) — `-n auto`:** `63 passed in 6.28s` (the 33 packet-61 pins —
  31 new + 2 edited schema-cascade pins — plus the rest of the pre-existing packet-49 schema
  contract). RED@HEAD → GREEN as scoped by the contract.
- **`./scripts/typecheck.sh`:** `Success: no issues found` across all members incl. test trees
  (`loremaster` 225 files, `scripts` 49, shellcheck OK). **0 errors.**
- **`uv run ruff check .`:** `All checks passed!`
- **Full suite (`loremaster/tests -n auto`):** `4 failed, 8406 passed, 50 skipped, 3 xfailed`
  BEFORE the regression fixes; after fixing the 3 `TestDelete` + confirming the 4th is
  pre-existing (below): the 3 `TestDelete` are now GREEN (`5 passed`), and **1 pre-existing
  red remains** (`test_secret_typing`, not my change — see Flags §F1).
- **Touched suites re-run (contract + all 4 edited existing suites) `-n auto`:** `233 passed`.

## Mutation proofs

Real-tree mutation with a `cp -a` content backup (`/tmp/mp61/*.orig`); restored byte-exact
after each (final `diff -q` → both production files identical to backup). Every load-bearing
pin the contract author named:

| # | mutation (production defect injected) | pins that RED | controls that stayed GREEN |
|---|---|---|---|
| 1 | disable refuse-while-keeping (`if False`) | keeper-refuse-raises, refused-removes-NOTHING, names-them-ALL, no-`keep.keeper`-dangle (4) | member-only-deletes, member_of-cleans, loner, zero-dangling, error-type (5) |
| 2 | name only the FIRST kept keep (`[:1]`) | names-them-ALL (N=3) ONLY (1) | single-keep refuse pins (proves N=3 discriminates the slice bug) |
| 3 | `set_keeper` UPDATEs wrong field (no-op) | 2 store + 2 CLI update-dependent pins (4) | ghost-email / ghost-keep pins |
| 4 | drop the ghost-NEW-KEEPER guard | ghost-email store + CLI (2) | success + ghost-keep pins |
| 5a | drop `set_keeper` ghost-KEEP check-first | `set_keeper_on_a_ghost_keep_is_loud` (store) — now raises `KeepStoreError` not `KeepNotFoundError` (1) | others |
| 5b | drop BOTH ghost-KEEP checks | `delete_keep` ghost store + CLI (2) | — |
| 6 | skip keep-slice ensure on delete dispatch | `#131` dirty-store CLI pin (1) — delete crashes on absent `keep` table | full-schema fixtures |
| 7 | `set_keeper` `get_keep` OUTSIDE the wrap try | FR-2 Q2b `test_each_write_path_wraps…[set_keeper]` — injected `SurrealStoreError` escapes unwrapped (1) | — |

Mutations 3/4/5a/7 re-verified against the FINAL restructured `keeps.py` (the restructure
post-dated the first pass). All restore-to-green confirmed.

## Flags / findings (§2 — surfaced, not silently resolved)

- **F1 — PRE-EXISTING RED, not my change: `test_secret_typing.py` reds on the contract wave's
  probe.** `test_secretstr_is_minted_only_where_a_credential_ORIGINATES` scans `scripts/` for
  `SecretStr(...)` mints; `scripts/probe_member_of_cascade.py:370` mints
  `SecretStr("spikeroot")` (the spike TEST-store literal — the SAME adjudicated shape already
  allowlisted for `probe_unique_nullable_48.py` / the 07/07a probes) but was never added to the
  gate's `allowed` tuple. It reds independent of my production code (I did not author the probe
  — it is a spec file I must not touch — nor the security gate). **EXACT FIX (I did NOT apply —
  not my regression, and it is a security-gate allowlist adjudication):** add
  `"scripts/probe_member_of_cascade.py",` to the `allowed` tuple in
  `test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`
  (beside `probe_unique_nullable_48.py`), with the same "spike TEST-store literal, not a real
  credential; re-open if it ever sources a real secret" adjudication comment. Owner call: lead /
  contract-61a-w1 (probe author). Blocks the packet's full-suite currency gate until added.

- **F2 — DESIGN CONSEQUENCE (surfaced for the cold audit): `PrincipalStore.delete` now hard-
  requires the `keep` table.** Per the D3 ruling (tolerance of an absent table REJECTED), the
  refuse-while-keeping read `SELECT id FROM keep WHERE …` needs the table to exist. The SOLE
  production caller is `_cmd_delete` via `_dispatch`, which readies the keep slice first — so
  **production is safe** (verified: grep of `loremaster/loremaster/` finds exactly one caller).
  But this is a new coupling: any FUTURE non-CLI caller of `PrincipalStore.delete` must ready
  the keep slice first (the method docstring now warns of this). It broke the packet-49
  `test_principals_store.py::TestDelete` fixture (which called `delete` directly without keep) —
  fixed minimally by having that fixture apply `generate_keep_ddl` after `principal` (disclosed
  deviation). If the cold audit prefers the store method own or tolerate its keep dependency
  instead, that reverses the D3 ruling and is an operator/lead call.

## Store discipline (brief checklist)
- All reads/writes use BOUND params (`type::record('table', $id)`, `$pid`, `$kid`) — never
  string-interpolated user values (store §2 injection-safe). Table names are module constants.
- `delete` stays ONE `execute_transaction` for the cascade (validates every `statement[0..n]`);
  the refuse-read + keep-read are separate single-statement `_query` reads (store §3).
- `str(RecordID)` round-trips: the refuse message names `str(row["id"])` (`keep:<ulid>`), and
  `_bare(keep.id)` is a substring → the contract's `in`-message assertions hold.
- `member_of` auto-cascade relied on the committed probe (`probe_member_of_cascade.py` LEG A/C)
  — no explicit `DELETE member_of` added (both the member-delete and keep-delete paths).

## Files touched
- `loremaster/loremaster/principals.py` (production — `PrincipalHasKeepsError`, refuse-while-
  keeping in `delete`, keep-slice readiness in `_dispatch`, `set-keeper`/`delete-keep` CLI verbs)
- `loremaster/loremaster/keeps.py` (production — `KeepStore.set_keeper` + `delete_keep`)
- `loremaster/tests/test_keeps_store.py` (DEVIATION §2 — FR-2 Q2b reach-pin coverage entry for
  the 2 new write paths; my new methods directly grew the DERIVED write-path set)
- `loremaster/tests/test_keeps_cli.py` (DEVIATION §2 — FR-3 ghost-keep reach-pin coverage entry
  for the 2 new `--keep` verbs; my new verbs directly grew the DERIVED verb set)
- `loremaster/tests/test_principals_store.py` (DEVIATION §2 — `TestDelete` fixture now readies
  the keep slice; my `delete` keep-read directly broke it, see Flag F2)
- `REPORT-builder-61a-w1.md`

NOT touched (spec / do-not-touch, honoured): the 4 contract files, `probe_member_of_cascade.py`.
No git ops run (untracked RED contract intact).
