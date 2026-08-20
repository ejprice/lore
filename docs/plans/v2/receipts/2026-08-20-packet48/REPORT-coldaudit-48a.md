# REPORT-coldaudit-48a — Cold audit (REFUTE), packet 48 Wave 48-A (`build_store` extraction)

`brief-base v14 read` · `brief project v7 read`

## SUMMARY BLOCK
- **VERDICT: GO.** The 48-A `build_store(config)` extraction is a faithful, byte-equivalent
  execution of design §1. Every gate re-run independently is GREEN (or GREEN-DELTA); the
  mutation/sharing proof HELD in a provenance-verified scratch; the REFUTE diff pass found no
  behavior change the pins miss.
- **State:** done. Independent ground truth re-established — builder's green claim NOT taken on trust.
- **Deviations:** none.
- **Packages considered:** none — no mechanism specified. 48-A is an internal extraction of an
  existing store-construction recipe (`build_store` routes through the existing
  `config.resolve_config_value` / `config.resolve_secret` / `SurrealStore.__init__` seams; mints no
  new policy). I concur with the builder's/adversary's `none`.
- **Reuse ledger:** none — I authored no reusable symbol (auditor; findings only).
- **Graded:** `5bd1b36` (+ the uncommitted 48-A build: 4 working-tree files) · HEAD-at-report:
  `84bca93c` · **DIFFERENT (1 ahead).** The single commit that moved during this audit
  (`84bca93 test(48): allowlist probe_unique_nullable_48 in the S6 mint-site invariant (#389)`)
  is **exclusively** the lead's #389 fix in `loremaster/tests/test_secret_typing.py`. It touches
  **none** of the 48-A surfaces (the 4 build files + `test_build_store.py` are unchanged and still
  uncommitted), so the verdict is unaffected; it merely resolves the one unrelated red the builder
  flagged. See §"#389 — resolved, not flaky".
- **Scratch `loremaster.__file__` receipt (finding #140):**
  `/tmp/ca48a-scratch/loremaster/loremaster/__init__.py` (built by `scripts/scratch_copy.sh
  --force`, provenance-asserted; the mutation proof ran there).
- **decisions-needed:** none. Five residuals below, each individually verdicted — all note/deferred,
  none blocking.

## Message to lead-48
`STATE: done · REPORT: REPORT-coldaudit-48a.md · 48-A build_store cold audit: VERDICT GO — 11/11 pins, mutation-proof exit 0 (scratch, prov-verified), typecheck green-DELTA (191 auth-WIP, 0 in the 4 files), mcp 667 + no-reg 203 + entity-seam 66, byte-equivalent, entity_tables+readiness+R4 preserved. HEAD moved 5bd1b36→84bca93c = ONLY the lead's #389 fix (orthogonal). No blockers.`

---

## Gates re-run INDEPENDENTLY (every tail carries a passed-COUNT)

All runs against the real working tree (`/home/ejprice/PycharmProjects/lore`, uv editable install →
imports the actual uncommitted build) at HEAD `84bca93c`, except the mutation proof (scratch, per
brief / finding #140).

### 1. The 11 contract pins
```
$ uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q | tail
...........
11 passed in 1.01s
```
GREEN. (The pins fail via `_require_build_store()`'s `pytest.fail` if `build_store` is absent, so
11-passed independently confirms `build_store` is present and every resolution/routing/readiness/R4
pin is satisfied.)

### 2. Mutation proof — THE SHARING PROOF (routing-is-not-sharing) — exit 0
Ran inside a provenance-verified scratch copy (`scratch_copy.sh --force /tmp/ca48a-scratch`;
`loremaster.__file__ = /tmp/ca48a-scratch/loremaster/loremaster/__init__.py`; build confirmed
present: `def build_store` + `= build_store(config)` at all 3 sites). Mutated `build_store`'s
resolved `database` INSIDE `build_store` ONLY (`config.effective_surreal_database` → `+ "_MUT"`);
declared-RED set of 4 taken from `REPORT-contract-48a.md` §"Mutation-proof declared-RED set".
```
mutation LANDED (anchor matched exactly once) in loremaster/loremaster/store/surreal.py
...
4 failed, 7 passed in 2.79s
tree restored byte-exact (loremaster/loremaster/store/surreal.py: md5 70686301ae6af5990879979baf60b0d4)
PROOF HELD — the declared RED set fired EXACTLY:
  [test_build_app_context_store_is_resolved_and_readied,
   test_build_store_resolves_all_six_config_values,
   test_index_cli_run_store_is_resolved_and_readied,
   test_scout_from_config_store_is_resolved_and_unreadied]
MUTATION_PROOF_EXIT=0
```
- **Both-ways diff clean.** All 4 declared pins reddened, each on
  `assert store._database == config.effective_surreal_database` (observing `..._MUT`) — the
  intrinsic factory pin **and all three caller resolution pins**. The 3 structural routing pins
  (#7–9), the un-readied pin, R4, and the 2 standing guards stayed GREEN.
- **This is the sharing proof:** mutating the ONE factory's resolution reddens EVERY caller ⇒ all
  three route through it. An inliner would have stayed green under a body mutation → the
  routing-is-not-sharing tell is absent because there is no inliner.
- The restore md5 `70686301ae6af5990879979baf60b0d4` matches the builder's receipt — confirming the
  scratch's `surreal.py` is byte-identical to the working-tree build.

### 3. No regressions at the 3 routed sites (independent, scoped — full suite NOT run per brief)
```
$ uv run pytest -n auto -q loremaster/tests/test_mcp_server.py | tail
667 passed, 3 warnings in 107.51s          # build_app_context (R5 chain terminal)

$ uv run pytest -n auto -q \
    loremaster/tests/test_secret_resolution_seam.py \  # cred seam
    loremaster/tests/test_cli.py \                     # index.cli._run
    loremaster/tests/test_scout.py \                   # Scout.from_config
    loremaster/tests/test_comms_wiring.py              # build_app_context (sibling the contract cloned)
134 passed in 16.18s

$ uv run pytest -n auto -q loremaster/tests/test_secret_typing.py | tail
69 passed in 5.91s                                     # #389 GREEN post-84bca93c (see below)

$ uv run pytest -n auto -q [the full 5-suite builder bundle] | tail
203 passed in 15.33s                                   # reproduces builder's 203 total, now 0-failed

$ uv run pytest -n auto -q \
    loremaster/tests/test_ingest_entity_seam.py \      # register_entity_tables path (adversary R1)
    loremaster/tests/test_server_chunker_wiring.py | tail
66 passed in 12.04s
```
Every scoped seam is GREEN. (The builder's bundle was 202 passed / 1 failed because it ran at
`5bd1b36`, BEFORE the lead's #389 fix; at HEAD `84bca93c` the same 203 tests are all green.)

### 4. Gates
```
$ uv run ruff check .
All checks passed!

$ ./scripts/typecheck.sh                     → TYPECHECK_EXIT=1  (GREEN-DELTA)
  lorerunes  FAILED   89 errors, 3 test files (test_roster_parser / test_posture / test_email_normalisation)
  loremaster FAILED  102 errors, 8 test files (_auth_fixtures / test_google_token_verifier / test_auth /
                     test_allowlist_roster / test_permission_resolver_seam / test_hosted_readonly_posture /
                     test_auth_identity_seam / test_auth_composition)
  lorescribe / loresigil / skills / docs/eval / scripts / shellcheck : OK
```
**GREEN-DELTA independently confirmed.** All 191 errors (89 + 102) are `[attr-defined]` /
`[call-arg]` / `[no-any-unimported]` on **auth-WIP symbols** (`Posture` / `parse_roster` /
`normalize_email` / `SCOPE_READ` / `GoogleOAuthConfig` / `resolve_posture` / `LoreTokenVerifier` /
`PermissionFilteredToolError` / `derive_edge_policy` / `http_client` / `permission_resolver` …) —
the #333-adjudicated auth-WIP set. They live in **11 test files; the build touched exactly 4
production files** (`git diff --stat`), **none of them among the 11**. The 11 error files are
byte-identical to HEAD (only the 4 build files are modified) ⇒ their errors are the HEAD baseline ⇒
the build's mypy **delta is zero**. `build_store(config) -> SurrealStore` is type-preserving (returns
the exact type the inline `SurrealStore(...)` produced), and the `loremaster` leg type-checked all
207 source files (incl. the 4 changed) with errors only in the 8 auth test files.

---

## REFUTE — the diff, read for a behavior change the green pins do not catch

### Byte-equivalence, arg-by-arg (`build_store` vs the deleted inline construction)
`SurrealStore.__init__` (verified live, `lore_get_symbol`): `(*, url, namespace, database, dim,
user, password, analyzer_name=DEFAULT_ANALYZER_NAME, entity_tables=())`. `build_store`
(`store/surreal.py:1866+`) constructs:

| ctor arg | `build_store` | inline sites (all 3, from `git diff`) | equal? |
|---|---|---|---|
| `url` | `config.surreal.url` | `config.surreal.url` | ✓ |
| `namespace` | `config.surreal.namespace` | `config.surreal.namespace` | ✓ |
| `database` | `config.effective_surreal_database` | `database`/`surreal_database` local = `config.effective_surreal_database` | ✓ |
| `dim` | `config.embedding.dim` | `config.embedding.dim` | ✓ |
| `user` | `resolve_config_value(config.surreal.user_env)` | `surreal_user` local = same | ✓ |
| `password` | `resolve_secret(config.surreal.password_env)` | `surreal_password` local = same | ✓ |
| `analyzer_name` | **not passed** → ctor default `DEFAULT_ANALYZER_NAME` | not passed (default) | ✓ |
| `entity_tables` | **not passed** → ctor default `()` | not passed (default) | ✓ |

All three former inline sites used the identical 6-arg call and left the two ctor defaults alone
(design §1 lines 72–76, confirmed against the `git diff`). `build_store` reproduces it exactly →
**byte-equivalent construction.** Docstring is **verbatim** the design §1 ruling (word-for-word).

### `entity_tables` specifically (the brief's flagged hazard) — SAFE
`build_store` constructs with the default `entity_tables=()`. `build_app_context` **still** calls
`write_store.register_entity_tables(list(dict.fromkeys(entity_table_names)))` AFTER construction —
present at `server.py:9192`, unchanged by the routing edit (the edit replaced only the
`write_store = SurrealStore(...)` block at 9112–9119 with `write_store = build_store(config)`).
Behaviorally confirmed: `test_ingest_entity_seam.py` + `test_server_chunker_wiring.py` = **66 passed**.
A build that had dropped the `register_entity_tables` call would break extension ingest with every
48-A pin green (the pins never exercise entity tables) — it did NOT drop it.

### Readiness preserved (per-site)
| site | readiness | evidence (post-build source) |
|---|---|---|
| `build_app_context` | READIED | `await write_store.ensure_ready()` @ `server.py:9131` |
| `index.cli._run` | READIED | `await store.ensure_ready()` @ `index/cli.py:154` |
| `Scout.from_config` | UN-READIED | no `ensure_ready` in `from_config` (readiness is `start`'s job) |
No site flipped its readiness. `build_store` itself never readies (un-readied pin GREEN).

### R4 — no url-credential parsing in the factory
`build_store` reads `config.surreal.url` verbatim and passes it through; body contains no
`urlparse` / `urlsplit` / `_reject_url_userinfo` call and no `.username` / `.password` / `.userinfo`
attribute access (AST pin #3 GREEN; confirmed by reading the diff). The inline-credential rejection
lives upstream in `config._reject_url_userinfo` (standing-guard pin #10 GREEN). `config.surreal.password_env`
is the AST attr `password_env` (not `password`), so no false-redden.

### Removed-behavior inventory (delete/replace adjudication — each item)
The extraction deletes one inline `SurrealStore(...)` block at each of 3 sites and replaces it with
`build_store(config)`. Nothing else is lost:
- **The `SurrealStore` construction** → replaced by the byte-equivalent `build_store(config)`. ✓ preserved-with-pin (resolution + mutation pins).
- **The `surreal_user` / `surreal_password` / `surreal_database`(`database`) locals** → **SURVIVE** at
  all 3 sites and continue to feed the sibling backends: `SurrealManifest` (server 9143–9149 / cli /
  scout), `SurrealCodeGraph` (server 9156–9164 / scout), the snapshot stamper, and scout's command
  connection. Verified in source. This is DELIBERATE per design §1 "Why not broad" (F5 broad refactor
  deferred, ledgered with a concrete address). ✓ preserved-deliberately.
- **`register_entity_tables`** (server only) → preserved (above). ✓
- **Readiness decisions** → preserved per-site (above). ✓
No branch, guard, or side effect of the deleted blocks is dropped.

### Completeness (quantifier check) — the 3-site routed set is COMPLETE
Repo-wide grep: the ONLY remaining production `SurrealStore(` construction is `surreal.py:1877` —
INSIDE `build_store` itself. All three former inline write-store sites route through it; there is no
4th un-routed production write-store site (test-side `SurrealStore(...)` are fixtures, correctly out
of the narrow-extraction scope). No site that used the config recipe was missed.

### No import cycle; S6-clean
`config.py` imports nothing from `loremaster.*` (grep), so `build_store`'s new module-top
`from loremaster.config import ...` in `store.surreal` introduces no cycle — corroborated by clean
collection across 900+ tests. `build_store` mints **no** `SecretStr` (grep: none) — it routes through
`resolve_secret` (a credential ORIGIN), so it is S6-compliant and is not the #389 offender.

### Design §1 conformance (executed verbatim)
Ruled signature + verbatim docstring ✓ · 6-arg construction, ctor defaults untouched ✓ · returns
un-readied ✓ · R4 ✓ · R5 chain (`build_mcp_server`→`_lifespan`→`_eager_build_with_retry`→
`build_app_context`; deleted `_EagerStartupLifespan` stays deleted, guard pin #11 GREEN) ✓ · NARROW
scope keeping sibling locals (F5 deferred) ✓ · placement in `store/surreal.py` ✓ · mutation proof ✓.

---

## #389 — resolved, not flaky (why the builder saw 1 red and I saw 0)
The builder's report flagged `test_secret_typing.py::…::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`
RED (finding #389: `scripts/probe_unique_nullable_48.py:260` inline-mints `SecretStr(PASSWORD)`).
I could not reproduce it — 203 passed in the full bundle, the named test passes alone.

Root cause, established by git: **HEAD moved during my audit**, `5bd1b36` → `84bca93c`. The lead's
commit `84bca93 test(48): allowlist probe_unique_nullable_48 in the S6 mint-site invariant (#389)`
added `"scripts/probe_unique_nullable_48.py"` to the S6 test's `allowed` prefix tuple
(`test_secret_typing.py:1024`; NOT present at `5bd1b36`, present at `84bca93c`). So the builder saw
the red correctly at `5bd1b36`; the lead then fixed it; I measured post-fix. **Not a flaky red — a
resolved finding, exactly as the brief said the lead was doing.** The probe file itself
(`probe_unique_nullable_48.py:260`) is unchanged; the fix is the allowlist exemption, one of the two
options the builder proposed. `84bca93c` is orthogonal to 48-A (touches no 48-A surface).

---

## Residuals (each individually verdicted; NONE blocking — verdict is GO)

| # | residual | verdict |
|---|---|---|
| R1 | **`register_entity_tables` (server) is unpinned by the 48-A contract.** The narrow extraction correctly leaves the call in `build_app_context` (not `build_store`), but no 48-A pin asserts it survives the routing edit. | **Note.** The call IS preserved (`server.py:9192`) and is behaviorally covered by `test_ingest_entity_seam` (66 passed). A future routing edit that dropped it would be caught there, not by a 48-A pin. Same as adversary R1. |
| R2 | **`_direct_call_names` structural pin sees DIRECT calls only (shallow reach).** A build that constructed `SurrealStore` via an indirect helper the caller calls would pass the routing pin. | **Note, contrived.** The resolution + mutation pins catch the realistic mis-resolution regardless of call shape. Same as adversary R3. |
| R3 | **R4 pin cannot catch arbitrary string-op credential stripping** (`partition`/`rpartition`, no banned Call/Attr). | **Non-blocking, contrived.** The realistic R4 regression is copying `urlsplit`/`_reject_url_userinfo`, which the pin catches; a url-with-userinfo fixture can't even be built (config rejects it upstream, pin #10). Adversary concurred. |
| R4 | **The broad refactor (F5) is deferred** — `SurrealManifest`/`SurrealCodeGraph`/`AppContext._await_live_connect` still re-resolve `user`/`password`/`database` independently at the 3 sites. `build_store` is the single seam for the STORE construction only, not yet for the whole cred/db tuple (3 of ~10 resolution sites). | **Deferred by design ruling** (§1 "Why not broad", ledgered with a concrete address). Correct for a NARROW packet; the duplication is named, not hidden. Not a defect. |
| R5 | **The S6 mint-site `allowed` tuple is a growing hand-list** (6 prefixes at `test_secret_typing.py:1017–1025` after `84bca93c`). Each probe that mints `SecretStr` inline gets exempted by prefix rather than routed through `config.resolve_secret`. | **Not a 48-A concern** (surfaced only because my no-regression run crossed it). The S6 test documents a re-open trigger (lines ~1010–1012). Ownership = the #388/#389 probe owner / lead, not this wave. Raised for visibility per scope law. |

---

## Verification-law note (for a re-runner)
- Contract: `uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q` → 11 passed.
- Mutation proof (scratch): the exact command in §2, run from `/tmp/ca48a-scratch` → exit 0, tree
  restored byte-exact (md5 `70686301ae6af5990879979baf60b0d4`). Scratch provenance:
  `loremaster.__file__ = /tmp/ca48a-scratch/loremaster/loremaster/__init__.py`.
- Gates: `uv run ruff check .` (clean); `./scripts/typecheck.sh` (exit 1 = green-DELTA, all 191 reds
  in 11 untouched auth-WIP test files).
- Graded `5bd1b36` + uncommitted build; HEAD-at-report `84bca93c` (1 ahead = the #389 allowlist fix
  only). Re-derive: `git merge-base --is-ancestor 84bca93c HEAD` and `git log 5bd1b36..HEAD`.
