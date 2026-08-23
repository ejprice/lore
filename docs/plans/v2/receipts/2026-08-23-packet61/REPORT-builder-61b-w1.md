# REPORT-builder-61b-w1 — the PDP CORE (packet 61b wave 1)

brief-base v14 read
brief project v7 read
store-ref cited: §2 (IN-inside-OR TableScan trap #413; IndexScan-vs-TableScan-via-EXPLAIN), §1.1 (DDL clause rule — not touched; no DDL changed), §4 (record<> owner links, RELATE no endpoint enforcement — read-only context)

## SUMMARY BLOCK  (updated for ROUND 2 — the #416 security fix + SEC hardening)
- **state:** done
- **deviations:** none behavioural. Contract deviation B2 (Resource carries `table`) was PRE-RULED by the contract (lead-61 confirmed).
- **Packages considered:** none for the PDP itself — `bespoke` forced by the lorerunes stdlib-only charter (deps==[]); value objects are stdlib `@dataclass(frozen=True, slots=True)` (F3, not pydantic). No mechanism (retry/backoff/classifier) specified.
- **Reuse ledger:** unchanged from R1 + 2 re-homed table names (SEC-R4); all dispositioned below.
- **Graded:** n/a — build report. Built at HEAD `599354a`.
- **decisions-needed:** none.
- **receipt pointers (ROUND 2):**
  - both contract files `-n auto` → **123 passed** — §Gates R2
  - typecheck **0** (all 7 roots; loremaster 232 files — R4 re-exports validated across ~30 consumers) + ruff clean — §Gates R2
  - full suite: **8765 passed / 50 skipped / 3 xfailed / 0 failed** (`-n auto`) — §Gates R2
  - mutation battery: **M7** (unparenthesised ScopeInKeeps → composition pin RED *while oracle GREEN*) + legs 1–5 + new **R4**/**F3**, all RED→restored byte-identical — §Mutation proof R2
  - the D2+R4 re-home (own concern, flagged for a separate commit) — §D2/R4 re-home

## ROUND 2 — the #416 security fix + SEC hardening (applied 2026-08-23, revised 123-pin contract)

Adversary SUFFICIENT on the revised contract; the security-auditor's #416 MEDIUM + 4 LOW applied
to production. My R1 core was correct as-invoked; these harden the PUBLIC IR + value objects:

- **#416 (MEDIUM — latent cross-principal LEAK in the public IR):** `ScopeInKeeps.to_surql` now
  emits a SELF-CONTAINED (parenthesised) fragment `(scope=$k0 OR scope=$k1)`. Previously it
  returned unparenthesised disjuncts (to splice flat into the top-level READ `Or`); that leaks
  under `And`-composition — `(owner=$p AND scope=$k0) OR scope=$k1` lets the 2nd disjunct escape
  the owner constraint and return foreign rows. Not reachable via 61b's own entry points, but
  `And`/`Or`/`ScopeInKeeps` are re-exported and 63/64 compose them. The parenthesised form STILL
  IndexScans as a top-level READ disjunct (SurrealDB flattens `A OR (B OR C)` — the oracle
  IndexScan pin confirms, no #413 regression).
- **SEC-F3 (empty-identity):** `Subject.__post_init__` rejects an empty `principal_id`/`agent_id`;
  `Resource.__post_init__` rejects an empty-string owner (a confused-deputy forgery vector).
- **SEC-F2 (absent owner):** `Resource.owner_principal`/`owner_agent` are now `str | None` — `None`
  (an `option<>` NONE column, an unowned/legacy row) is legal and matches NO owner predicate
  (`None != any id`) while scope predicates still apply. `matches` already handled `None` correctly
  (`None == id` is `False`); the oracle's new NONE-owner rows (r13 server, r14 agent-private) prove
  to_surql (store NULL) and matches (Python None) AGREE.
- **SEC-F4 (reach law):** `_AUDITED_ACTIONS = frozenset(Action) - {Action.READ}` — DERIVED, so a new
  mutating action auto-audits (was a hand-list; the values are identical, the derivation is the point).
- **SEC-R4 (DRY):** `PRINCIPAL_TABLE` + `AGENT_TABLE` re-homed to `lorerunes` (the D2 pattern);
  `surreal_schema` IMPORTS them (redundant-alias re-exports for its ~30 consumers), the emitter uses
  the lorerunes constants. No private second copy.

### Gates R2 (receipts)

```
# both revised contract files, -n auto
$ uv run python -m pytest lorerunes/tests/test_pdp_core.py loremaster/tests/test_pdp_oracle_61b.py -n auto -q
123 passed in 4.89s

$ ./scripts/typecheck.sh
typecheck: lorerunes OK / lorescribe OK / loresigil OK / loremaster OK (232 files) /
           skills OK / docs/eval OK / scripts OK / shellcheck OK (7 tracked .sh)   # 0 errors

$ uv run ruff check .
All checks passed!
```
The `loremaster` mypy leg over 232 files is the receipt that the SEC-R4 re-home's re-exports
(`PRINCIPAL_TABLE`/`AGENT_TABLE`/`AUDIT_TABLE` imported from `surreal_schema` by ~30 modules)
stay clean under `strict = true` (`no_implicit_reexport`).

```
$ uv run python -m pytest loremaster/tests lorerunes/tests -n auto -q
8765 passed, 50 skipped, 3 xfailed, 6 warnings in 288.29s
```
**0 failed.** #405 flakes cause false-RED only, never false-GREEN — so a clean `-n auto` run is
an honest 0-failed (no solo re-run needed; had anything failed I would have re-run it solo to
separate a real failure from a #405 flake). The 6 warnings are pre-existing deprecation/resource
warnings in unrelated suites, not from this wave.

### Mutation proof R2 (real-tree mutation, `cp -a` green backup, byte-exact restore)

Backup `/tmp/pdp61b_green/` (md5 recorded); every leg restored + `md5sum -c` → both files OK.

| # | mutation | pin that RED | verdict |
|---|---|---|---|
| **M7** | `ScopeInKeeps.to_surql` UNPARENTHESISED (the #416 leak) | oracle `TestCompositionSafetyNoLeakUnderAnd::...returns_only_the_owners_rows` **and** core `test_no_node_emits_an_unparenthesised_top_level_or` | RED (leaked bob's r12) **while the single-brain oracle `test_authorize_equals...` stayed GREEN** — the #416 pin catches what the oracle alone cannot |
| 1 | `ScopeEq.matches` → `return True` | oracle `test_authorize_equals_the_emitted_filter_over_the_store` | RED |
| 2 | `ScopeInKeeps.to_surql` → literal `scope IN` | core `...never_a_literal_IN` (#413) | RED |
| 3 | `requires_audit` uses a grantability-dropping member check | core `test_admin_set_scope_into_a_non_grantable_keep_is_audited` | RED |
| 4 | private `AUDIT_TABLE = "audit"` in surreal_schema | oracle `test_audit_table_is_imported_from_lorerunes_not_assigned_locally` | RED |
| 5 | `import pydantic` in `lorerunes/pdp.py` | core charter pin | RED |
| **R4** | private `PRINCIPAL_TABLE = "principal"` in surreal_schema | oracle `test_governed_table_names_are_imported_from_lorerunes` (`[PRINCIPAL_TABLE]` RED, `[AGENT_TABLE]` still GREEN) | RED |
| **F3** | drop the `Subject` empty-identity check | core `test_subject_rejects_empty_identity` (both params) | RED |

## WHAT I BUILT

### The PDP core — `lorerunes/lorerunes/pdp.py` (NEW, stdlib-only)
The single-brain authorization engine (design `2026-08-22-packet61-pdp-audit-rulings.md`
Forks A/B/C/D/E/G/H + addenda D1/D2/D4/F3). Symbols, all re-exported from
`lorerunes/__init__.py` (`__all__`):

- **Vocabulary (row-VISIBILITY scopes — distinct from `scopes.py`'s capability scopes):**
  `SCOPE_AGENT_PRIVATE` / `SCOPE_PRINCIPAL_PRIVATE` / `SCOPE_SERVER`, `KEEP_SCOPE_PREFIX`,
  `keep_scope()`, `PRINCIPAL_ROLE_MEMBER` / `PRINCIPAL_ROLE_ADMIN` / `PRINCIPAL_ROLES`,
  `AUDIT_TABLE`.
- **Action** — closed enum of exactly `{READ, WRITE, DELETE, SET_SCOPE, SET_OWNER}` (Fork C).
- **Value objects (F3 stdlib frozen dataclasses, `frozen=True, slots=True`, no field
  defaults, `__post_init__` validation):** `Subject(principal_id, agent_id, role,
  visible_keep_ids)`, `Resource(table, owner_principal, owner_agent, scope)` (D1 4-field,
  reading B2), `Decision(allowed, requires_audit)`.
- **The closed predicate IR (Fork A):** `Predicate` (ABC; BOTH `to_surql` and `matches`
  abstract, so a node missing one cannot instantiate — coverage is structural), and the
  exactly-eight concrete nodes `ScopeEq, OwnerPrincipalEq, OwnerAgentEq, ScopeInKeeps, And,
  Or, AllRows, NoRows`. Two TOTAL interpreters over ONE tree:
  - `to_surql() -> (fragment, bound_params)` — every value a BOUND param via a
    content-addressed `_param_name()` (never interpolated; a hostile principal id survives as
    a bound value, store-ref §2). `ScopeInKeeps` EXPANDS to per-keep `scope = $k_i`
    equalities (never a literal `scope IN $set` — #413 / store-ref §2), joined unparenthesised
    so a parent `Or` splices them FLAT (the probe's index-served form); empty keep set → `false`.
  - `matches(resource) -> bool` — the Python evaluator.
- **Entry points:** `authorize_filter(subject, action, table, *, target_scope=None) ->
  Predicate` and `authorize(subject, action, resource, *, target_scope=None) -> Decision`,
  where `authorize` IS `authorize_filter(...).matches(resource)` — single brain by
  construction. `requires_audit` reuses the SAME `_member_filter` (no clone; ROUTING-IS-NOT-
  SHARING), firing iff an allowed admin mutating action could NOT have been done by a member
  of the same identity (the load-bearing bypass, Fork G / §9).

Per-action policy (Fork C + addenda), all in `_member_filter` (role-independent):
READ = own agent-private ∨ own-principal principal-private (any sibling agent) ∨ server ∨
scope∈keeps[expanded]; WRITE = EXACT (p,a) private/server ∨ scope∈keeps; DELETE = owner (p,a)
any scope (D4(a)); SET_SCOPE = owner (p,a) ∧ grantable(target) [D4(b): private/server always,
a keep only if the subject is in it; `None`/non-grantable → `NoRows`]; SET_OWNER = `NoRows`.
Admin ⇒ `AllRows` EXCEPT the audit carve-out (`NoRows` for the 4 mutating actions when
`table == AUDIT_TABLE`, Fork G).

### `lorerunes/__init__.py` — re-exports the full PDP surface (`__all__`).

### D2 re-home — `loremaster/loremaster/store/surreal_schema.py` (own concern; SEPARATE COMMIT)
See §D2 re-home below. Flagged for the lead to commit as its own one-concern commit.

## Gates (receipts)

```
# pure core — no store
$ uv run python -m pytest lorerunes/tests/test_pdp_core.py -q -p no:xdist
91 passed in 0.08s

# live-store oracle — ws://127.0.0.1:18000 (TEST store; NEVER :18500)
$ uv run python -m pytest loremaster/tests/test_pdp_oracle_61b.py -q -p no:xdist
15 passed in 2.68s

# both contract files, -n auto (brief-required)
$ uv run python -m pytest lorerunes/tests/test_pdp_core.py loremaster/tests/test_pdp_oracle_61b.py -n auto -q
106 passed in 4.56s

# D2-re-home-affected suites + all lorerunes tests
$ uv run python -m pytest loremaster/tests/test_principals_schema.py \
    loremaster/tests/test_principals_store.py loremaster/tests/test_audit_schema.py \
    loremaster/tests/test_audit_store.py loremaster/tests/test_principal_keys_schema.py \
    lorerunes/tests/ -n auto -q
328 passed in 6.91s

# canonical static gate — per-member mypy + shellcheck
$ ./scripts/typecheck.sh
typecheck: lorerunes OK / lorescribe OK / loresigil OK / loremaster OK (232 files) /
           skills OK / docs/eval OK / scripts OK / shellcheck OK (7 tracked .sh)   # 0 errors

$ uv run ruff check .
All checks passed!
```

```
# full suite (-n auto, run to catch any other consumer of the re-homed constants)
$ uv run python -m pytest loremaster/tests -n auto -q
8589 passed, 50 skipped, 3 xfailed, 6 warnings in 274.43s
```
0 failed. (The 6 warnings are pre-existing deprecation/resource warnings in unrelated
suites — `websockets.legacy`, an un-awaited coroutine in `test_retry_seam` — not from this
wave.)

The `loremaster` mypy leg passing over 232 source files is the receipt that the D2 re-home's
re-exports (`audit.py` imports `AUDIT_TABLE`, `principals.py` imports `_PRINCIPAL_ROLES`) stay
clean under `strict = true` (`no_implicit_reexport`).

## Mutation proof (all 5 legs — real-tree mutation, `cp -a` content backup, byte-exact restore)

Backup at `/tmp/pdp61b_backup/` (md5 recorded pre-mutation); every leg restored and verified
byte-identical against `orig.md5` (`md5sum -c` → both OK).

| # | mutation (production code) | pin that RED | verdict |
|---|---|---|---|
| 1 | `ScopeEq.matches` → `return True` (split to_surql from matches) | `test_pdp_oracle_61b::...::test_authorize_equals_the_emitted_filter_over_the_store` | RED (only-python rows appear; single-brain oracle caught it) |
| 2 | `ScopeInKeeps.to_surql` → literal `scope IN $set` | `test_pdp_core::TestScopeInKeepsExpansion::...never_a_literal_IN` **and** `test_pdp_oracle_61b::...::test_member_read_emitter_with_TWO_keeps_indexscans_no_tablescan` | RED (both; `' IN '` present + live plan) |
| 3 | `requires_audit` uses `_member_filter(..., SCOPE_SERVER)` (cloned check that DROPS grantability) | `test_pdp_core::TestRequiresAudit::test_admin_set_scope_into_a_non_grantable_keep_is_audited` | RED (`requires_audit=False`, expected True) |
| 4 | private `AUDIT_TABLE = "audit"` assignment in `surreal_schema` | `test_pdp_oracle_61b::...::test_audit_table_is_imported_from_lorerunes_not_assigned_locally` | RED (`assigned=True`) |
| 5 | `import pydantic` in `lorerunes/pdp.py` | `test_pdp_core::TestLorerunesStdlibOnlyCharter::test_every_lorerunes_module_imports_only_stdlib_or_itself` | RED (`{'pdp.py': {'pydantic'}}`) |

Each leg was applied, run, confirmed RED, then restored; final `md5sum -c orig.md5` → both files OK.

## D2 re-home (flagged — its own one-concern commit)

Moved the shared authorization vocabulary to stdlib-only `lorerunes` (it cannot import
`loremaster`, so the shared home MUST be `lorerunes`; one-column-one-vocabulary). Pre-authorized
(the brief); touches committed 48/60/w4 code.

- `PRINCIPAL_ROLE_MEMBER` / `PRINCIPAL_ROLE_ADMIN` / `PRINCIPAL_ROLES` and `AUDIT_TABLE` now
  live in `lorerunes/pdp.py`.
- `surreal_schema.py`:
  - top import: `from lorerunes import AUDIT_TABLE as AUDIT_TABLE  # noqa: PLC0414` (deliberate
    explicit re-export — `audit.py` imports `AUDIT_TABLE` from `surreal_schema`, and mypy
    `no_implicit_reexport` requires the redundant-alias marker; ruff PLC0414 noqa'd for that
    idiom) + `from lorerunes import PRINCIPAL_ROLE_MEMBER, PRINCIPAL_ROLES`.
  - `_PRINCIPAL_ROLE_MEMBER = PRINCIPAL_ROLE_MEMBER` and `_PRINCIPAL_ROLES = PRINCIPAL_ROLES`
    (same object as `lorerunes.PRINCIPAL_ROLES` — sharing-by-identity, what the oracle pin
    asserts; kept as an ASSIGNMENT so `principals.py`'s existing `from surreal_schema import
    _PRINCIPAL_ROLES` stays re-export-clean).
  - removed the local `_PRINCIPAL_ROLE_ADMIN` (dead after the re-home; grep confirms zero
    other references) and the local `AUDIT_TABLE = "audit"` assignment.
- **Sharing proved by mutation** (legs 3–4 above): a cloned member predicate reds the audit
  sharing pin; a private `AUDIT_TABLE` copy reds the D2 AST pin. `_AUDITED_ACTIONS` was
  deliberately NOT re-homed (the audit ASSERT domain stays in `surreal_schema`; the PDP's
  four mutating actions must-AGREE `==` it — pinned in the oracle).

## registration_sites.py

`uv run python scripts/registration_sites.py` → 55 co-occurrence sites, 22 incomplete. **None
reference packet-61b code** — they are pre-existing member-name co-occurrences (prose/subsets)
in files I did not touch. Packet 61b adds NO new workspace member (lorerunes is already fully
registered in every site: pyproject members/mypy_path, typecheck.sh MEMBERS, AST `_SCANNED_MEMBERS`,
testpaths, Containerfile, scratch_provenance), only new PUBLIC symbols WITHIN it — so no
registration site is owed. (The 22 incomplete are the tool's standing worklist, unchanged by
this wave.)

## DRY ledger (§6 — required output)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `SCOPE_AGENT_PRIVATE`/`SCOPE_PRINCIPAL_PRIVATE`/`SCOPE_SERVER`, `KEEP_SCOPE_PREFIX`, `keep_scope` | `lore_search "row visibility scope constants agent-private principal-private server keep scope"` | only my own new `pdp.py`; `scopes.py` has `LORE_READ`/`LORE_WRITE` (CAPABILITY scopes — a different concept) | HAND-ROLLED — no existing row-visibility scope vocabulary; capability scopes don't fit |
| `Action`, `Subject`, `Resource`, `Decision`, `Predicate` + 8 IR nodes, `authorize`, `authorize_filter` | `lore_search "authorize filter policy decision point SurrealQL where fragment emitter bound params"` | only my own new `pdp.py` + the contract tests; no pre-existing PDP | HAND-ROLLED — the PDP is new (design confirms no prior authorization engine) |
| `_param_name`, `_grantable`, `_member_filter`, `_is_valid_scope`, `_emit_children` | (same searches) | nothing pre-existing | HAND-ROLLED — private helpers internal to the new PDP |
| `PRINCIPAL_ROLE_MEMBER`/`ADMIN`/`PRINCIPAL_ROLES`, `AUDIT_TABLE` | grep for consumers (`principals.py`, `audit.py`, tests) | existed in `surreal_schema`; re-homed | RE-HOME (SHARED, not cloned) — moved to `lorerunes`, `surreal_schema` now imports; proved shared by mutation legs 3–4 |

## FILES TOUCHED
- `lorerunes/lorerunes/pdp.py` — NEW (the PDP core).
- `lorerunes/lorerunes/__init__.py` — re-export the PDP surface.
- `loremaster/loremaster/store/surreal_schema.py` — D2 re-home (SEPARATE COMMIT).
- `REPORT-builder-61b-w1.md` — this report.

Do-not-touch respected: no edits to contract tests, packet 62/63/64 code, or anything outside
the writable set. Did NOT stage/commit (the lead commits after a cold audit + the dedicated
security-auditor).
