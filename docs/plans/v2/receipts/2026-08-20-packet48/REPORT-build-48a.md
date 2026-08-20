# REPORT-build-48a — Builder, packet 48 Wave 48-A (`build_store` extraction)

`brief-base v14 read` · `brief project v7 read`

## SUMMARY BLOCK
- **State:** done. `build_store(config) -> SurrealStore` added in `loremaster/loremaster/store/surreal.py`; all 3 sites routed through it. Contract 11/11 GREEN, mutation proof exit 0 (routing-is-not-sharing), gates green-DELTA.
- **Scope:** design `docs/design/2026-08-20-packet48-principals-substrate.md` §1 (NARROW extraction) + committed contract `loremaster/tests/test_build_store.py` (adversary-cleared r2 — my GREEN target).
- **Deviations:** none. My change is byte-equivalent (`build_store` constructs the identical `SurrealStore` the inline sites did). The `surreal_user/password/database` locals at each site are KEPT — the sibling backends (manifest / code_graph / stampers / ledgers) still re-resolve the conn tuple, per §1 "Why not broad" (F5 future refactor).
- **Packages considered:** none — `build_store` is an internal extraction of an existing store-construction recipe; no library involved. It routes through the existing config resolvers (`config.resolve_config_value` / `config.resolve_secret`) + the existing `SurrealStore` ctor, and mints no new policy (no retry/classification/validation of its own).
- **Reuse ledger:** 1 new symbol (`build_store`), dispositioned — see §"DRY ledger".
- **Graded:** N/A (I build; I render no verdict on another artifact). HEAD at report: `git rev-parse HEAD` == `5bd1b36`.
- **decisions-needed:** none blocking. **One unrelated pre-existing red surfaced** (finding #389 — `probe_unique_nullable_48.py:260` trips the S6 typed-credential invariant; out of my writable set) — see §"Unrelated failure".

## Message to lead-48
`STATE: done · REPORT: REPORT-build-48a.md · 48-A build_store: 11/11 contract GREEN, mutation_proof exit 0 (exactly declared-4 reddened, structural pins green — routing-is-not-sharing), ruff clean, typecheck green-DELTA (all reds #333 auth-WIP, none in my 4 files); no-regression 202 passed (cred/cli/scout/comms-wiring) + 667 passed (test_mcp_server); 1 UNRELATED pre-existing red filed #389 (probe_unique_nullable_48 S6 mint)`

---

## What changed (file:symbol)

| file | symbol | change |
|---|---|---|
| `loremaster/loremaster/store/surreal.py` | module import + `build_store` (new) | Added `from loremaster.config import LoreConfig, resolve_config_value, resolve_secret` (module top; no cycle — config imports nothing from loremaster). Added `build_store(config) -> SurrealStore` right after the `SurrealStore` class (the "beside SurrealStore" home, mirroring `make_embedder_from_config` in `loremaster.embedding`). Carries the design §1 ruled docstring **verbatim**. Body reads `config.surreal.url` untouched + resolves the 6 core args; returns UN-READIED. |
| `loremaster/loremaster/server.py` | `build_app_context` | Lazy import `from loremaster.store.surreal import SurrealStore` → `build_store`; `write_store = SurrealStore(...)` → `write_store = build_store(config)`. The `surreal_user/password/database` locals stay (sibling backends use them). Site stays READIED on the `write_stack_readied` rail. |
| `loremaster/loremaster/index/cli.py` | `_run` | Module import `SurrealStore` → `build_store`; `store = SurrealStore(...)` → `store = build_store(config)`. Stays READIED. |
| `loremaster/loremaster/scout.py` | `Scout.from_config` | Module import `SurrealStore` → `build_store`; `store = SurrealStore(...)` → `store = build_store(config)`. Stays UN-READIED (construction only — readiness is `start`'s job). |

`git diff --stat`: exactly 4 files (`index/cli.py` 15, `scout.py` 19, `server.py` 18, `store/surreal.py` 22), 45 insertions / 29 deletions.

**R4 compliance (design §1):** `build_store` reads `config.surreal.url` verbatim — no `urlparse`/`urlsplit`/`_reject_url_userinfo` call, no `.username`/`.password`/`.userinfo` attribute access. The AST-based R4 pin (#3) is GREEN. `config.surreal.password_env`/`.user_env` are the AST attrs `password_env`/`user_env` (never `password`/`user`), so the pin does not false-redden.

**Placement / cycle check (design §1 "Where build_store lives"):** verified `loremaster/config.py` imports NOTHING from `loremaster.*` (grep) → no config↔store.surreal cycle → `store.surreal` is the correct home (not the `factory.py` fallback). All 4 modules import cleanly under execution (213 tests below import them; zero collection error).

---

## PROVE IT — receipts

### 1. All 11 contract pins GREEN
```
$ uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q | tail
...........                                                              [100%]
11 passed in 1.13s
```

### 2. Mutation proof — ROUTING-IS-NOT-SHARING (exit 0)
Mutated `build_store`'s resolved `database` INSIDE `build_store` ONLY
(`config.effective_surreal_database` → `+ "_MUT"`); declared-RED set = the 4 from
`REPORT-contract-48a.md` §"Mutation-proof declared-RED set" (ids from `--collect-only`).
Both-ways diff held; structural routing pins #7–9 stayed GREEN (an inliner would stay green
under a body mutation — the tell they exist to catch is absent because all 3 route).

```
$ ./scripts/mutation_proof.py \
    --file loremaster/loremaster/store/surreal.py \
    --anchor '        database=config.effective_surreal_database,' \
    --replacement '        database=config.effective_surreal_database + "_MUT",' \
    --expect-red '...::test_build_store_resolves_all_six_config_values' \
    --expect-red '...::test_build_app_context_store_is_resolved_and_readied' \
    --expect-red '...::test_index_cli_run_store_is_resolved_and_readied' \
    --expect-red '...::test_scout_from_config_store_is_resolved_and_unreadied' \
    -- uv run pytest -p no:xdist -q loremaster/tests/test_build_store.py

mutation LANDED (anchor matched exactly once) in loremaster/loremaster/store/surreal.py
...
4 failed, 7 passed in 1.05s
tree restored byte-exact (loremaster/loremaster/store/surreal.py: md5 70686301ae6af5990879979baf60b0d4)
PROOF HELD — the declared RED set fired EXACTLY: [test_build_app_context_store_is_resolved_and_readied,
  test_build_store_resolves_all_six_config_values, test_index_cli_run_store_is_resolved_and_readied,
  test_scout_from_config_store_is_resolved_and_unreadied]
MUTATION_PROOF_EXIT=0
```
Each reddened pin failed on `assert store._database == config.effective_surreal_database`
(observed `..._MUT`) — the intrinsic factory pin AND all three caller pins, proving every
site routes the resolution through the ONE factory. Structural pins #7–9 and the R4/un-readied/
guard pins did not redden.

### 3. No regressions at the 3 sites (covering suites via `lore_impact`, `-n auto`)
`lore_impact` on `build_app_context` / `index.cli._run` / `Scout.from_config` returned 978 / 33 /
135 covering tests (mostly transitive AppContext builders — running all = the full suite, which
is forbidden and carries the #333 auth-WIP reds). Scoped to the suites that **directly** exercise
each composition seam + the credential-resolution seam `build_store` now owns:

```
$ uv run pytest -n auto -q \
    loremaster/tests/test_secret_resolution_seam.py \  # cred seam @ build_app_context + cli._run
    loremaster/tests/test_secret_typing.py \           # typed-credential seam
    loremaster/tests/test_cli.py \                     # index.cli._run
    loremaster/tests/test_scout.py \                   # Scout.from_config
    loremaster/tests/test_comms_wiring.py              # build_app_context (the sibling the contract cloned)
1 failed, 202 passed in 15.06s
```
- **202 passed** across all 3 seams + the credential seam.
- The **1 failure is UNRELATED and pre-existing** (§"Unrelated failure" — finding #389, `probe_unique_nullable_48.py:260`, not one of my files).

Canonical server suite (`test_mcp_server.py` — the R5 chain terminal `build_mcp_server` →
`build_app_context`), `-n auto`:
```
$ uv run pytest -n auto -q loremaster/tests/test_mcp_server.py | tail
667 passed, 3 warnings in 107.42s (0:01:47)
MCP_SERVER_EXIT=0
```
**667 passed / 0 failed.** (The 3 warnings are a pre-existing unrelated
`RuntimeWarning: coroutine '_register_tools.<locals>.impact' was never awaited` in a test's own
validator setup — not my change, not a failure.) This is the strongest single build_app_context
no-regression signal: the whole server composition path builds its `write_store` through `build_store`
now and every server test is green.

### 4. Gates
```
$ uv run ruff check .
All checks passed!

$ ./scripts/typecheck.sh                                  → exit 1
  lorerunes  FAILED  (89 errors, 3 test files: test_roster_parser / test_posture / test_email_normalisation)
  loremaster FAILED  (102 errors, 8 test files: _auth_fixtures / test_google_token_verifier / test_auth /
                      test_allowlist_roster / test_permission_resolver_seam / test_hosted_readonly_posture /
                      test_auth_identity_seam / test_auth_composition)
  lorescribe / loresigil / skills / docs/eval / scripts / shellcheck : OK
```
**GREEN-DELTA proven (no NEW mypy errors):**
- All 191 errors are `[attr-defined]`/`[call-arg]`/`[no-any-unimported]` on **auth-WIP symbols**
  (`lorerunes` `Posture`/`parse_roster`/`normalize_email`/`SCOPE_READ`/`SCOPE_WRITE`/`is_admitted`;
  `loremaster.auth`/`loremaster.config` `GoogleOAuthConfig`/`resolve_posture`/`LoreTokenVerifier`/
  `PostureConfigError`/`derive_edge_policy`; `loremaster.server` `PermissionFilteredToolError`/
  `HostedToolRefusedError`/`http_client`/`permission_resolver` kwargs) — the ~446 auth-WIP reds
  the brief named as **#333-adjudicated, not mine**.
- The errors live in **11 test files. My change touched exactly 4 production files** (`git diff --stat`),
  **none of which is any of those 11**. Those 11 files are byte-identical to HEAD, so their errors
  are the HEAD baseline → my delta is **zero**.
- My change is **type-preserving**: `build_store(config)` returns `SurrealStore` — the exact type the
  inline `SurrealStore(...)` produced — so no local/downstream inferred type changed. The `loremaster`
  leg type-checked all 207 source files (incl. my `surreal.py`/`server.py`/`cli.py`/`scout.py`) and
  reported errors in only the 8 auth test files.

---

## Unrelated failure (surfaced per operator "flag unrelated failures", filed #389)
`test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`
is RED — the mint-site AST scan finds `scripts/probe_unique_nullable_48.py:260` inline-minting
`SecretStr(PASSWORD)` (`signin_credentials(user=USER, password=SecretStr(PASSWORD))`) — the S6
"re-wrap a bare str at a call site" shape the invariant forbids. Confirmed **pre-existing** and
**not mine**:
- That probe was committed at `c453c3b` (finding #388 instrument), an **ancestor of HEAD**
  (`git merge-base --is-ancestor c453c3b HEAD` → true) → red at HEAD `5bd1b36` before this wave.
- `scripts/probe_unique_nullable_48.py` is **not** in my changed set (only my 4 files are).
- `build_store` mints **no** SecretStr (`grep SecretStr( surreal.py` → none) — it calls
  `resolve_secret` (a credential ORIGIN), so it cannot be the offender.
- Out of my writable set → **flagged, not edited**. Filed as **finding #389** with the two
  one-line fix options (route the probe password through `resolve_secret`, or add the probe to
  the test's `allowed` prefix tuple). OWNER = whoever owns the packet-48 probe / #388.

---

## DRY ledger (§6 — new reusable symbols)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `build_store(config) -> SurrealStore` | `lore_search "factory function that constructs a SurrealStore from LoreConfig resolving credentials and database"` (+ design/contract confirm) | the ONLY SurrealStore-from-config factory is the one this wave creates; pre-48A the recipe was **inline copy-pasted, byte-identical, at 3 sites** (server.build_app_context / index.cli._run / scout.Scout.from_config) — no shared factory existed | **HAND-ROLLED** — this IS the packet-mandated extraction. It introduces **no new policy**: it ROUTES through the existing resolvers **REUSED `config.resolve_config_value`** + **REUSED `config.resolve_secret`** and the existing ctor **REUSED `SurrealStore.__init__`**. Sharing proven by MUTATION (§2 — mutate the factory's resolution, all 3 callers redden, an inliner would not). |

No other new reusable symbol (no helper/retry/backoff/classifier/validator/sanitiser introduced — the
factory is a thin composition of existing seams).

---

## Process note — idle-gate ↔ brief name mismatch (minor, resolved)
My spawn brief named the report `REPORT-build-48a.md`, but the `teammate-idle-gate.sh` default owed-artifact is `REPORT-<exact-agent-name>.md` = `REPORT-builder-48a.md` — so the gate fired its one-time nudge on a report that was already present under the brief's name. Resolved via the sanctioned brief-base §5 mechanism: wrote the declared-artifact contract `/tmp/claude-idle-gate-lore/<session>-builder-48a.contract` = `{"artifact": "REPORT-build-48a.md"}`; the gate then resolves at the repo root (simulated → exit 0). **For future 48-x builder briefs:** either name the report `REPORT-<exact-agent-name>.md`, or instruct the agent to write that contract file as a first action at spawn.

## Verification-law note (for the cold auditor who re-runs my gates)
- Contract: `uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q` → 11 passed.
- Mutation proof: the exact command in §2 → exit 0, tree restored byte-exact (md5 in the receipt).
- Gates: `uv run ruff check .` (clean), `./scripts/typecheck.sh` (exit 1 = green-DELTA, all reds in 11
  untouched auth-WIP files per §4).
- Placement/cycle: `grep -n "import loremaster" loremaster/loremaster/config.py` → empty (config imports
  nothing from loremaster).
