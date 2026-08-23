brief-base v14 read
brief project v7 read

# REPORT — contract-61a-w1 (packet 61a-w1, finding #402, §FR-4 refuse-while-keeping)

## SUMMARY BLOCK
- state: **done** — RED contract written (tests only, NO production code); D1/D2/D3 + adversary
  #403 blocker + residual applied; satisfiability re-proven (33 pins, 63/63 on ref build).
- deviations:
  - **Adversary #403 BLOCKER + residual APPLIED** (revision 3): added the `set_keeper`
    ghost-KEEP guard (I had pinned the ghost-NEW-KEEPER axis but dropped the ghost-KEEP axis) —
    a store pin (`set_keeper` on a nonexistent keep → `KeepNotFoundError`, no phantom keep) and a
    CLI pin (`lore-adm set-keeper --keep <ghost>` → exit 1, `"lore-adm:" in stderr` naming the
    keep), mirroring the `delete_keep`/FR-3 ghost-keep rider; reference build's `set_keeper` made
    CHECK-FIRST (get_keep → raise before UPDATE, so no UPDATE-upsert phantom). Residual: the
    name-them-ALL quantifier fixture bumped N=2 → **N=3** (a `[:2]` slice bug can't pass).
  - **D1/D2/D3 ruled 2026-08-23 (FR-4 addendum) and APPLIED** (revision 2): store method renamed
    `reassign_keeper`→`set_keeper`; CLI flag `--keeper`→`--new-keeper` (verb `set-keeper` stays);
    the `#131` guard rewritten to the sharper dirty-store form (ready only principal+principal_key,
    NOT the keep slice); D2 confirmed as pinned + a forward-boundary comment added.
  - The `#131`/`#107` guard establishes that the `lore-adm delete` path must ready the keep SLICE
    on the fly (D3 rule (a)); my reference build readies it in `_dispatch`. Impl placement stays
    the builder's call (ruled).
- Packages considered: none — no new mechanism; the contract PINS behaviour, the probe/tests reuse the installed `surrealdb` SDK (`query_raw`/`RecordID`) already in the tree.
- Reuse ledger: 5 new test-local helpers, all dispositioned (see §Reuse ledger) — no new production symbol (that is the builder's).
- Graded: 84d20a3 · HEAD-at-report: 84d20a3 · SAME — every "RED at HEAD" claim is at this sha.
- decisions-needed: **none** — the three I flagged were ruled (D1/D2/D3, FR-4 addendum) and applied.
  For the record: D1 (verb names) → store `set_keeper` + CLI `--new-keeper`; D2 (`delete_keep`
  ghost) → CONFIRMED loud `KeepNotFoundError`; D3 (`#131`) → delete path readies the keep SLICE,
  sharper guard added.
- receipt pointers:
  - probe: `scripts/probe_member_of_cascade.py` (committed, self-checking, exit 0) — settled fact in §Probe.
  - contract files: `loremaster/tests/test_principal_delete_cascade_61.py`, `.../test_keep_remediation_store_61.py`, `.../test_keep_remediation_cli_61.py`, edited `.../test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned`.
  - satisfiability: §Satisfiability (61 passed on reference build; `loremaster.__file__` receipt).
  - declared RED/GREEN node sets: §Declared node sets.

## CAPABILITY CHECK
Brief fully satisfiable with the tools I have (lore MCP loaded; live TEST store reachable at
`ws://127.0.0.1:18000`; `scratch_copy.sh` provenance tool available). No unmet demand.

## Store reference citations (cited, never re-transcribed)
`docs/reference/surrealdb-31-capabilities.md`: §2 (`record<t>` FIELD links do NOT auto-clean on
target delete; CONTENT / `type::record` writes; a missing projection reads NONE), §4 (graph
RELATION edges self-delete when an endpoint node is deleted; RELATE endpoints are bound RecordID
params; `record<>`/RELATE do not validate existence), §3 (the delete is ONE `execute_transaction`;
`query()` validates only `statement[0]`), §1.1 (the DDL clause decision rule).

---

## Probe — the load-bearing member_of-vs-keep.keeper cascade fact, SETTLED BY CONSTRUCTION
`scripts/probe_member_of_cascade.py` (committed; self-checking, **exit 0**; positive controls on
every leg). #402's body claims `member_of` edges DANGLE on a member delete; store-law §4 says they
auto-clean. This is a #107-class "believed vs probed" disagreement — settled live on spike-surreal
(the 3.2.x TEST store), NOT by picking a side:

- **LEG A** — hard-delete the `in` principal (a member): `member_of where in=member` went **1 → 0**;
  the keep + the keeper's own edge survived. → **`member_of` AUTO-CASCADES on an `in`-endpoint
  delete.** (#402 body **REFUTED**; store-law §4 **CONFIRMED**.)
- **LEG B** — hard-delete the keeper (raw; production REFUSES this): the keeper's `member_of` edge
  cascaded (RELATION), but `keep.keeper` still named `principal:pk_keeper` on the surviving keep
  after the keeper was gone. → **`keep.keeper` FIELD LINK DANGLES** (store-law §2 **CONFIRMED**).
- **LEG C** — hard-delete the keep NODE (the `out` endpoint; the `delete_keep` mechanism):
  `member_of where out=keep2` went **2 → 0**; both member principals survived. → **`member_of`
  AUTO-CASCADES on an `out`-endpoint (keep-node) delete too.**

**Consequence for the BUILDER'S MECHANISM (the probe decides ONLY this, not my outcome pins):**
- member-only principal delete → **no explicit `DELETE member_of` needed** (auto-cascade); pin the
  PROPERTY (zero dangling `member_of` after).
- keeper principal delete → **refuse-while-keeping** is what prevents the `keep.keeper` dangle.
- `delete_keep` → **`DELETE <keep node>` alone suffices** (member_of auto-cascades); no explicit
  edge delete needed.

Fact also recorded in lore memory (`lore_recall("member_of cascade")`, id `72d58f36…`).

---

## The contract (behavioural OUTCOME pins, mechanism-agnostic)

### A. Exact-set pin update — the ADJUDICATION half of #402 (edited in `test_principal_keys_schema.py`)
`TestTheCascadeForwardScopeIsPinned`:
- `test_the_record_principal_link_set_matches_the_cascade_adjudication` (**renamed** from
  `test_principal_key_is_the_ONLY_record_principal_link` — the name cited by #402/§FR-4; a mapping
  note in the docstring lets a grep of the old name land here — kept accurate per the P8d
  natural-language-surface-drift class). Expected set updated to
  `{("principal", PRINCIPAL_KEY_TABLE), ("keeper", KEEP_TABLE)}` — the deliberate revisit that
  adjudicates the owned `keep.keeper` link and **re-arms the tripwire for 63/64's
  `owner_principal`**. This static pin goes **GREEN** (the RED_ORPHANED → GREEN half).
- `test_the_forward_scope_regex_has_nonzero_reach` (positive control) extended: the synthetic DDL
  now carries `keep.keeper` too; the regex must find all three links (required + option-wrapped).
- Verified: the live `generate_ddl(dim=512)` record<principal> set is EXACTLY
  `{("keeper","keep"),("principal","principal_key")}` (derived, not assumed).

### B. `PrincipalStore.delete` = refuse-while-keeping (`test_principal_delete_cascade_61.py`)
- `TestPrincipalHasKeepsErrorType::…subclasses_principal_store_error` — the typed error
  `PrincipalHasKeepsError(PrincipalStoreError)` exists + subclasses so `_dispatch`'s existing
  `except PrincipalStoreError` launders it (referenced via `getattr` name, NOT imported → file
  collects on HEAD; finding #133). **RED at HEAD.**
- `TestDeleteRefusesAKeeperWhileKeeping`:
  - `test_deleting_a_keeper_raises_the_typed_error_naming_the_keep_and_remediation` — refuse a
    keeper-of-1: typed error, message NAMES the keep id + remediation. **RED.**
  - `test_deleting_a_keeper_of_MULTIPLE_keeps_names_them_ALL` — **THE QUANTIFIER LAW**: keeper of
    TWO keeps → BOTH ids named (catches off-by-one / name-only-first). **RED.**
  - `test_a_refused_delete_removes_NOTHING` — keeper + its key + its Fork-D membership + the keep
    all survive (discriminating fixture: keeper WITH a key AND a membership). **RED.**
  - `test_a_member_only_principal_STILL_deletes_cleanly` — **POSITIVE CONTROL** (a member-only
    principal deletes) so the refuse pins distinguish "refuse a keeper" from "refuse every delete"
    / "refuse a member". GREEN on HEAD + fix.
- `TestDeleteMemberDimension` (§FR-4 three-case matrix; cases 2 & 3 are controls/regression guards,
  GREEN on HEAD + fix):
  - `test_member_only_delete_proceeds_and_cleans_member_of` — member-only proceeds; zero dangling
    `member_of where in=deleted`; keep + keeper survive.
  - `test_a_loner_delete_is_clean_and_cascades_only_its_keys` — keeps-nothing-member-of-nothing:
    clean delete, returns the cascaded key count (2), keys gone.
- `TestNoDanglingLinkIsReachableViaDelete` (§FR-4 cascade-correctness guard):
  - `test_a_keeper_delete_is_refused_so_no_keep_keeper_can_dangle` — the data-integrity half of
    #402: after the refused delete, `keep.keeper` still resolves to a LIVE principal. **RED.**
  - `test_a_member_only_delete_leaves_zero_dangling_member_of` — GLOBAL absence of dangling
    `member_of` for a deleted member (member in 2 households). POSITIVE CONTROL, probe-consistent.

### C. Remediation verbs — store level (`test_keep_remediation_store_61.py`, all RED at HEAD)
Verbs referenced via a `_verb(store, name)` guard → a legible "verb is unbuilt" RED (finding #133).
- `TestSetKeeper` (D1: renamed from `TestReassignKeeper`; store method `set_keeper`): updates the
  keeper to the successor; a GHOST new-keeper email is REFUSED (`KeepStoreError`) and `keep.keeper`
  UNCHANGED (ENFORCED-flavoured — the email-resolution guard, since a `record<principal>` field does
  not validate existence, store §2); **a GHOST KEEP is REFUSED (`KeepNotFoundError`), no phantom
  keep upserted (#403 blocker — the second ghost axis the adversary caught)**; after `set_keeper`
  the former keeper's delete PROCEEDS (store-level remediation flow).
- `TestDeleteKeep`: removes the keep + cascades its `member_of` (probe-consistent; member PERSONS
  survive); a GHOST keep → `KeepNotFoundError` (D2, confirmed); after `delete_keep` the former
  keeper's delete PROCEEDS. **D2 forward-boundary note** (comment, not a pin): when 63/64 add
  keep-scoped rows, `delete_keep` must revisit that cascade — the "member_of only" scope is a 61
  boundary.

### D. Remediation verbs — CLI level (`test_keep_remediation_cli_61.py`)
- CLI verbs `set-keeper` (flag `--new-keeper`, D1) / `delete-keep` (`--keep`).
- `TestNewVerbParserSurface`: both verbs parse with required args (RED — unknown subcommand at
  HEAD); registered in `_KEEP_VERB_HANDLERS` (RED); missing-arg exits (GREEN-at-head guard).
- `TestDeleteVerbRefusesAKeeper`:
  - `lore-adm delete` of a keeper → exit 1, `lore-adm:` stderr line NAMING the keep id, principal +
    keep survive (**RED**).
  - `test_delete_readies_the_keep_slice_on_the_fly_when_the_keep_table_is_absent` — **the D3
    sharper #131/#107 test-env-fiction guard** (GREEN-at-head + fix): readies ONLY
    principal+principal_key DIRECTLY (NOT the keep slice), then `lore-adm delete` of a keeps-nothing
    principal must SUCCEED (the delete branch readies the keep slice on the fly; count=0). A build
    that counts keeps but never readies the table CRASHES here where every virgin FULL-schema
    fixture stays green. (Replaces the weaker prior guard, which `_add`'s own dispatch had already
    readied keep for.)
- `TestSetKeeperVerb` / `TestDeleteKeepVerb`: success paths + ghost refusals (exit 1, `lore-adm:`)
  — all RED at HEAD. `TestSetKeeperVerb` now includes the **ghost-KEEP** CLI pin (#403):
  `lore-adm set-keeper --keep <ghost> --new-keeper <real>` → exit 1, `"lore-adm:" in stderr`
  naming the missing keep.
- `TestTheRemediationFlow`: the end-to-end §FR-4 story via the CLI — create-keep → `delete` refused
  → `set-keeper`/`delete-keep` → `delete` proceeds; the keep survives under the new keeper (no data
  loss). **RED.**
- **Test-env-fiction (#401 rider):** every stderr assertion uses `"lore-adm:" in err`, never
  `startswith` (a `<label>.rejected` log line precedes it in prod; caplog strips it in-suite).

---

## Declared node sets (from `--collect-only`, before running)
33 node ids total (post-#403 revision: +2 ghost-keep pins; the N=2→N=3 bump adds no node). On HEAD
@ 84d20a3: **23 RED / 10 GREEN** (measured, `-rA`).

**RED at HEAD (23 — the fix drives these GREEN):** every pin in `test_keep_remediation_store_61.py`
(7 — `TestSetKeeper` ×4 incl. the ghost-KEEP pin, `TestDeleteKeep` ×3); in
`test_keep_remediation_cli_61.py` all but the 3 `missing-arg` + the `#131` guard (11 — incl. the
ghost-KEEP CLI pin); in `test_principal_delete_cascade_61.py`: `PrincipalHasKeepsErrorType`, the 3
refuse pins (incl. keeper-of-MULTIPLE), `NoDanglingLink…::keeper_delete_is_refused` (5).

**GREEN at HEAD (10 — positive controls + adjudication, guard against regression / wrong builds):**
the 2 schema pins (adjudication + reach control); the 3 member-dimension controls; the
no-dangling-`member_of` control; the 3 `missing-arg` parser pins; the D3 sharper
`#131`/`#107` slice-ready-on-the-fly guard.

---

## Satisfiability receipt (the contract goes 0-failed on a known-correct build)
Reference build in a provenance-asserting scratch (`./scripts/scratch_copy.sh /tmp/lore-sat-61a`):
- **`loremaster.__file__ = /tmp/lore-sat-61a/loremaster/loremaster/__init__.py`** (proven testing
  the scratch tree, not the original — #140).
- Reference implementation (thrown away): `PrincipalHasKeepsError`; `PrincipalStore.delete`
  refuse-while-keeping (`SELECT id FROM keep WHERE keeper=…`, names all ids); `_dispatch` readies
  the keep SLICE (`generate_keep_ddl`, D3 rule (a)); `KeepStore.set_keeper` (**CHECK-FIRST**:
  get_keep → `KeepNotFoundError` before the UPDATE, so a ghost keep is loud and no UPDATE-upsert
  phantom is possible) / `delete_keep`; the two CLI verbs (`set-keeper --new-keeper`, `delete-keep`)
  + handlers + `_KEEP_VERB_HANDLERS` registration.
- **`63 passed in 15.08s` (0 failed)** across all four contract files against the reference build
  (RE-RUN after the #403 revision — 33 pins; earlier pre-#403 runs read 61 passed / 31 pins).
- Harder leg: the reference build **passes `ruff check` and `mypy` clean** — the contract is
  satisfiable by a build that also passes lint/type gates (no orphaned-import trap).
- My four contract files: **ruff clean + mypy clean** (`loremaster` tests leg); the probe: ruff +
  mypy clean under the `MYPYPATH=scripts` leg.

The scratch copy `/tmp/lore-sat-61a` is a disposable `/tmp` scratch_copy (not a git worktree). My
`rm -rf` of it was denied by the sandbox, so it REMAINS on disk — a lead/operator can delete it
(`rm -rf /tmp/lore-sat-61a`); it holds only the throwaway reference build, nothing citable.

---

## Mutation-proof expectations (named for the adversary/builder)
- Remove the refuse-while-keeping check in `PrincipalStore.delete` → RED:
  `test_deleting_a_keeper_raises…`, `…keeper_of_MULTIPLE…`, `test_a_refused_delete_removes_NOTHING`,
  `test_a_keeper_delete_is_refused_so_no_keep_keeper_can_dangle`, and the CLI `delete`-refusal + both
  remediation-flow pins.
- Make `set_keeper` a no-op (keep old keeper) → RED: `test_set_keeper_updates_the_keeper…`.
- Drop the ghost-email guard in `set_keeper` → RED: `test_set_keeper_to_a_ghost_email_is_refused…`
  (a `record<principal>` write would silently succeed with a dangling link).
- Drop the ghost-KEEP guard in `set_keeper` (silent None on a typo'd keep) → RED:
  `test_set_keeper_on_a_ghost_keep_is_loud` (store) + `…set_keeper_of_a_ghost_keep_is_loud…` (CLI)
  — the #403 blocker.
- Slice/name only the first N-1 kept keeps in the refuse message → RED:
  `…keeper_of_MULTIPLE_keeps_names_them_ALL` (now N=3, so a `[:2]` cap is caught).
- `delete_keep` that leaves member_of edges → RED: `…removes_the_keep_and_cascades_its_member_of`.
- Forget to ready the keep slice on the delete path → RED: the D3 #131 guard
  `test_delete_readies_the_keep_slice_on_the_fly_when_the_keep_table_is_absent`.

## Reuse ledger (test-local helpers — no production symbol introduced)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_bare()` (3 files) | `lore_search "partition record id bare id KeepStore"` | `KeepStore._record_id_part`, `delete`'s `partition(':')[2]` | HAND-ROLLED (a 1-line test-local mirror of the prod idiom; a test importing a prod private helper couples them) |
| `_verb(store, name)` | (finding #133 idiom) | `test_principal_keys_schema._apply_key_ddl` legible-RED guard | HAND-ROLLED per that idiom (turns HEAD AttributeError into a clean "unbuilt" RED) |
| `_count` / `_dangling_member_of_where_in` / `_member_of_count_out` | read `test_keeps_store._count` | the absent-table-tolerant `connect_admin`+count helper | EXTENDED that idiom (test-local, per independent-collectibility) |
| CLI harness (`_config_payload`/`cli_env`/`_run_cli`/`_keep_store_for`/`_add`/`_create_keep`) | read `test_keeps_cli.py` | the established CLI-test idiom | CLONED verbatim (self-contained per-file, the repo's independent-collectibility rule; `_run_cli` additionally catches SystemExit → clean RED for unbuilt verbs) |

## lore-first / fallbacks
Used `lore_search`/`lore_get_symbol`/`lore_findings`/`lore_remember`/`lore_comms` throughout. One
grep fallback SAID OUT LOUD: enumerating the live `record<principal>` DDL set was done with a
one-shot `re` scan over `generate_ddl` output (a non-symbol textual seam — the exact-set regex the
pin itself uses), the sanctioned grep case; and `git grep` for the RED pin's name to confirm the
rename breaks no reference (rename-exhaustiveness). Both are the SAID-OUT-LOUD fallback cases.
