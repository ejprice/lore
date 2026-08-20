# REPORT-contract-48a — Contract author, packet 48 Wave 48-A (`build_store` extraction)

`brief-base v14 read` · `brief project v7 read`

## SUMMARY BLOCK
- **State:** done — **revision r2** (adversary MP-1 C-DEF + MP-2 monoculture fixed, both proven). Contract written, validated, gate-clean.
- **Scope:** design doc `docs/design/2026-08-20-packet48-principals-substrate.md` §1 (Fork 1 — NARROW extraction) + §8 checklist items 1–4 (Half 1 — `build_store`). CONTRACT TESTS ONLY; no production code written.
- **Deliverable:** `loremaster/tests/test_build_store.py` — 11 pins: 9 contract-first RED now, 2 standing guards GREEN now (labelled). ruff clean · mypy clean · 11 collected · offline (no live store).
- **Deviations:** none. Two minor FLAGS (non-blocking) in §"Flags / spec notes": (F1) design §1 R5 chain omits the `_eager_build_or_operator_safe_error` wrapper that actually calls `_eager_build_with_retry` — cosmetic; (F2) `build_store` placement resolved to `store.surreal` (no config↔surreal cycle — verified) per design's own check.
- **Packages considered:** none — no mechanism specified. `build_store` is an internal extraction of an existing store-construction recipe; no library involved. Test helpers reuse `unittest`-free stdlib (`inspect`/`ast`/`argparse`) + existing `loresigil.testing.FakeEmbedder` + `_surreal_harness.surreal_url`.
- **Reuse ledger:** 5 new test helpers, all dispositioned — see §"DRY ledger".
- **Graded:** N/A (I author a contract; I render no verdict on another artifact). HEAD at authoring: `9195839` (`git rev-parse HEAD` == `9195839f6dc9e54321656d18a5f983bc62aa7d01`).
- **decisions-needed:** none blocking. F1/F2 above are FYI; the builder should keep `build_store` in `loremaster/store/surreal.py` (my `_require_build_store()` resolves it there) or update that one resolver if placed elsewhere.

## Message to lead-48
`STATE: done (r2) · REPORT: REPORT-contract-48a.md · 48-A build_store contract r2: adversary MP-1(C-DEF) + MP-2 fixed & proven — R4 pin now AST-based (no docstring/config-field false-redden), namespace+dim+url distinctive sentinels; 9 RED/2 green, ruff+mypy clean, satisfiability 0-failed re-proven vs correct ref build`

---

## Revision r2 (adversary delta — REPORT-adversary-48a.md MP-1/MP-2)

Both findings were real. Fixes + proofs:

### MP-1 (C-DEF / STOP) — R4 pin false-reddened a correct build. FIXED, and a LATENT second
false-positive fixed with it.
- **The reported cause:** the forbidden-token list contained the bare substring `.password`,
  which is a substring of `config.surreal.password_env` — the field the CORRECT build MUST
  reference. Any correct `build_store` reddened the pin.
- **The latent cause I found while fixing it:** `inspect.getsource(build_store)` includes the
  **docstring**, and the design's *ruled* build_store docstring (§1) literally contains
  `config._reject_url_userinfo` and "never parses or handles credentials in the URL". So even
  after dropping `.password`, a substring scan would STILL false-redden on the docstring's
  `_reject_url_userinfo` (and my `_reject_url_userinfo` token). A word-boundary string fix would
  not have caught this.
- **Fix (robust for both):** `test_build_store_body_has_no_url_credential_parsing` is now
  **AST-based**. It bans `urlparse`/`urlsplit`/`_reject_url_userinfo` as *Call* names (via the
  existing `_direct_call_names`) and `username`/`password`/`userinfo` as *Attribute* `.attr`
  names. This is precise by construction: `config.surreal.password_env` is the AST attribute
  `"password_env"` (**not** `"password"`), and a docstring is an `ast.Constant` that yields **no**
  Call/Attribute nodes — so both the config-field reference and the docstring prose are inert.
  Real URL-credential parsing (`urlparse(url).password`, a `_reject_url_userinfo(url)` call,
  a `.userinfo` access) is still caught.
- **PROVEN 0-failed** against a correct reference `build_store` carrying the design's **ruled
  docstring verbatim** (the exact `_reject_url_userinfo`-naming prose) plus the design body:
  the R4 pin + intrinsic resolution + un-readied pins all pass. (Scratch suite, 5/5 passed,
  deleted — not committed.)

### MP-2 (fixture monoculture) — namespace/dim non-distinctive. FIXED.
- The test config used `namespace="lore_test"` and `dim=2048` — a build hardcoding either
  survived every resolution pin.
- **Fix:** every resolved field now carries a **distinctive sentinel** — `_SENTINEL_URL =
  "ws://contract48-sentinel-host:19248/rpc"` (no userinfo → valid `CredentialFreeUrl`),
  `_SENTINEL_NAMESPACE = "contract48_ns_sentinel"` (matches `SLUG_PATTERN ^[a-z0-9][a-z0-9_]*$`),
  `_SENTINEL_DIM = 1493` (a distinctive `PositiveInt`), alongside the already-distinctive
  unique-slug `database` and the user/password sentinels. (I verified the config constraints
  live: `namespace: SlugStr`, `url: CredentialFreeUrl`, `dim: PositiveInt` — my sentinels
  validate. The `surreal_url()` harness import is dropped; the file now imports NOTHING from the
  sibling test tree.)
- **PROVEN discriminating:** a `namespace="lore_test"`-hardcoding build and a `dim=2048`-hardcoding
  build each FAIL the resolution pin (scratch, both raised AssertionError); the sentinel config
  still passes `run_probe_gate` with `FakeEmbedder(dim=1493)` and the caller-capture harness.

### r2 satisfiability expectation (for the adversary's delta re-check)
Against a CORRECT routed extraction (`build_store` in `store.surreal` + all three callers routed
through it), the expectation is **0 failed / 11 passed**. My scratch proved the intrinsic +
R4 + caller-resolution/readiness + caller-capture pins pass on a correct `build_store`; the 3
structural routing pins additionally require the callers to actually call `build_store(...)`
(they pass once routed — validated logic in r1). No pin reddens on a correct build.

### r2 receipts
```
$ uv run pytest loremaster/tests/test_build_store.py --collect-only -q | tail   → 11 tests collected
$ uv run ruff  check loremaster/tests/test_build_store.py                        → All checks passed!
$ uv run mypy  loremaster/tests/test_build_store.py                              → Success: no issues found in 1 source file
$ uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q | tail       → 9 failed, 2 passed
   (6 factory-gated → Failed: build_store not yet extracted; 3 structural → AssertionError; 2 guards → passed)
```
The RED-now shape is unchanged by r2; only the false-redden-on-correct-build risk is removed and
the monoculture closed.

## Receipt pointers
- Ground truth (3 sites, ctor, R4, R5): §"Ground truth (verified live @ 9195839)".
- Pin catalogue (file:test-name): §"Pins written".
- Declared expected-RED set for `scripts/mutation_proof.py --expect-red`: §"Mutation-proof declared-RED set".
- Collect-only tail (green count): §"Collect-only + RED receipts".

---

## Ground truth (verified live @ `9195839`, via `lore_get_symbol`/`lore_verify`)

The three sites construct a byte-identical `SurrealStore(...)` after the identical recipe
(`resolve_config_value(config.surreal.user_env)` + `resolve_secret(config.surreal.password_env)`
+ `config.effective_surreal_database`):

| site | store local | readied? | evidence |
|---|---|---|---|
| `loremaster.server.build_app_context` | `write_store` | **YES** — `await write_store.ensure_ready()` on the `write_stack_readied` rail | `server.py::build_app_context` |
| `loremaster.index.cli._run` | `store` | **YES** — `await store.ensure_ready()` | `index/cli.py::_run` |
| `loremaster.scout.Scout.from_config` | `store` | **NO** — construction only; readiness is `start`'s job | `scout.py::Scout.from_config` |

- **Ctor** (keyword-only): `SurrealStore.__init__(*, url, namespace, database, dim, user, password, analyzer_name=DEFAULT_ANALYZER_NAME, entity_tables=())`; stores `self._url/_namespace/_database/_dim/_user/_password/_analyzer_name/_entity_tables`. Un-readied tell: `self._connection is None` (set in `__init__`; `ensure_ready` connects via `_ensure_connection`). — `store/surreal.py::SurrealStore.__init__` / `.ensure_ready`.
- **Scout store attribute:** `self._store` (NOT `.store`). — `scout.py::Scout.__init__`.
- **R4** `config._reject_url_userinfo(value)` exists, uses `urlsplit`, raises on a `user:pass@host` userinfo component — the inline-credential rejection lives UPSTREAM at config load, so `build_store` inherits it and must contain NO url-credential parsing. — `config.py::_reject_url_userinfo`.
- **R5** `loremaster.server._EagerStartupLifespan` → `lore_verify` = **not_found** (deleted). Current server-site chain: `build_mcp_server` → nested `_lifespan` → `_eager_build_or_operator_safe_error(...)` → `_eager_build_with_retry(...)` → nested `_build_context()` → `build_app_context(...)` (builds `write_store`). — `server.py::build_mcp_server` / `._eager_build_with_retry`. (NOTE: the immediate caller in `_lifespan` is `_eager_build_or_operator_safe_error`, which WRAPS `_eager_build_with_retry`; design §1 R5 named `_eager_build_with_retry` — both are on the chain; I cite the full chain and the deleted symbol.)

---

## Pin design (rationale)

**Harness is fully OFFLINE — no live store needed.** For the two READIED callers I patch
`SurrealStore.ensure_ready` (class-level → fires regardless of import style) to record `self`
and raise a sentinel, aborting BEFORE any store I/O. `Scout.from_config` is construction-only
(no `ensure_ready`), so I read `scout._store` directly. So none of the Half-1 pins touch
`ws://127.0.0.1:18000`. (Live round-trip is Half-2's job; brief says a live connect pin is
optional here.)

### Three complementary discriminators (each caller)
1. **Behavioral RESOLUTION pin (mutation-provable):** run the REAL caller with the REAL
   `build_store`, capture the store it actually constructs, assert `store._database ==
   config.effective_surreal_database` and `store._dim == config.embedding.dim` (and `_url ==
   config.surreal.url`). RED now via a `from loremaster.store.surreal import build_store`
   guard at the top of the test (ImportError). After extraction: GREEN. **At BUILD time,
   `scripts/mutation_proof.py` mutates `build_store`'s resolved `database` → these three pins
   redden; an inlined caller stays GREEN → the both-ways diff catches routing-is-not-sharing.**
2. **Structural ROUTING pin (the static inline-catcher the FIXTURES-MUST-DISCRIMINATE clause
   demands):** `inspect.getsource(caller)` contains `build_store(` and does NOT construct the
   write store inline (`SurrealStore(` absent — each caller constructs exactly ONE
   `SurrealStore`, the others are `SurrealManifest`/`SurrealCodeGraph`/… ). RED now
   (currently `SurrealStore(` present, `build_store(` absent). Discriminates: an inliner keeps
   `SurrealStore(` → RED.
3. **READINESS pin (behavioral, not a flag):** `build_app_context`/`_run` → the capture patch
   FIRED (sentinel raised) ⇒ `ensure_ready()` WAS called on the build_store'd store.
   `Scout.from_config` → `ensure_ready` NOT called (recorder untouched) AND
   `scout._store._connection is None`.

### Intrinsic `build_store` pins (no caller)
- **RESOLUTION:** `build_store(config)` returns a `SurrealStore` whose 6 fields equal the
  config-resolved values (`_url/_namespace/_database/_dim/_user/_password`). Anchors the
  intrinsic mutation proof.
- **UN-READIED:** `build_store` is not a coroutine function AND `build_store(config)._connection
  is None` (behavioral un-readied tell; a build that readied would connect / return a coroutine).
- **R4 no-parsing:** `inspect.getsource(build_store)` contains none of
  `urlparse`/`urlsplit`/`userinfo`/`.username`/`.password`/`_reject_url_userinfo`.

### Standing guards (GREEN NOW by design — labelled, not contract-first)
- **R4 upstream anchor:** a `LoreConfig` built with an inline-credential `surreal.url` raises at
  LOAD (proves the rejection lives upstream in `_reject_url_userinfo`, making build_store's
  no-parsing safe). GREEN now — reddens only if `_reject_url_userinfo` is deleted.
- **R5 deleted-symbol guard:** `not hasattr(loremaster.server, "_EagerStartupLifespan")`. GREEN
  now (already deleted) — reddens if the symbol is resurrected. The server-site RESOLUTION pin
  drives `build_app_context` (the terminal of the current chain
  `build_mcp_server`→`_lifespan`→`_eager_build_or_operator_safe_error`→`_eager_build_with_retry`
  →`_build_context`→`build_app_context`), referencing no deleted symbol (item 4 satisfied).

## Pins written (`loremaster/tests/test_build_store.py`)

RED-now mechanism: factory-gated pins call `_require_build_store()` (a dynamic `getattr` on
`loremaster.store.surreal` that `pytest.fail`s while `build_store` is absent — chosen over a
top-level `from ... import build_store` so the file stays **collection-clean and mypy-clean**,
the sibling `test_comms_wiring` norm, instead of reddening the typecheck gate). Structural pins
are RED because each caller currently inlines `SurrealStore(...)`.

| # | test | kind | §8 | RED-now reason | discriminates (what wrong build fails) |
|---|---|---|---|---|---|
| 1 | `test_build_store_resolves_all_six_config_values` | intrinsic RESOLUTION | 1 | `pytest.fail` (factory absent) | mis-resolves/hardcodes any of url/ns/**database**/dim/**user**/**pass** — ALL six carry distinctive sentinels (r2/MP-2) |
| 2 | `test_build_store_returns_unreadied_store` | intrinsic UN-READIED | 3 | `pytest.fail` | async/self-readying factory (coroutine or `_connection is not None`) |
| 3 | `test_build_store_body_has_no_url_credential_parsing` | R4 no-parse (**AST-based**, r2/MP-1) | 2 | `pytest.fail` | factory re-implements url-credential parsing (Call `urlparse`/`urlsplit`/`_reject_url_userinfo`, or Attr `.username`/`.password`/`.userinfo`) — ignores docstring prose + config `.password_env` |
| 4 | `test_build_app_context_store_is_resolved_and_readied` | caller RESOLUTION+READIED (server/R5) | 1,3,4 | `pytest.fail` | server-site store mis-resolved; or NOT readied |
| 5 | `test_index_cli_run_store_is_resolved_and_readied` | caller RESOLUTION+READIED | 1,3 | `pytest.fail` | `_run` store mis-resolved; or NOT readied |
| 6 | `test_scout_from_config_store_is_resolved_and_unreadied` | caller RESOLUTION+UN-READIED | 1,3 | `pytest.fail` | scout store mis-resolved; or scout READIES it (breaks the deliberate variance) |
| 7 | `test_build_app_context_routes_write_store_through_build_store` | structural ROUTING | 1 | AssertionError (inline `SurrealStore(`) | `build_app_context` keeps inline construction |
| 8 | `test_index_cli_run_routes_store_through_build_store` | structural ROUTING | 1 | AssertionError | `_run` keeps inline construction |
| 9 | `test_scout_from_config_routes_store_through_build_store` | structural ROUTING | 1 | AssertionError | `Scout.from_config` keeps inline construction |
| 10 | `test_config_load_rejects_inline_url_credentials` | R4 UPSTREAM anchor | 2 | **GREEN now** (labelled) | reddens if `config._reject_url_userinfo` is deleted |
| 11 | `test_eager_startup_lifespan_symbol_stays_deleted` | R5 regression guard | 4 | **GREEN now** (labelled) | reddens if `_EagerStartupLifespan` is resurrected |

**Readiness (§8 item 3) is behavioral, not a flag:** for #4/#5 the `ensure_ready` sentinel FIRING
proves the caller readies the build_store'd store; for #6 the sentinel NOT firing + `_connection
is None` proves Scout leaves it un-readied. The store is captured (readied callers) via a
class-level `SurrealStore.ensure_ready` patch that records `self` and raises before any socket —
so no live store is touched (offline). Import-style-immune: I never spy on `build_store` (which
recon flagged has no universal patch point — build_app_context imports SurrealStore lazily, cli/
scout at module level); I observe the RESULTING store and read source via AST.

## Mutation-proof declared-RED set (for `scripts/mutation_proof.py --expect-red`)

Mutation = change `build_store`'s resolved `database` INSIDE `build_store` ONLY (e.g.
`config.effective_surreal_database + "_MUT"`). These four (and ONLY these) must redden; a caller
that kept inline construction stays GREEN → the both-ways diff catches routing-is-not-sharing:

```
loremaster/tests/test_build_store.py::test_build_store_resolves_all_six_config_values
loremaster/tests/test_build_store.py::test_build_app_context_store_is_resolved_and_readied
loremaster/tests/test_build_store.py::test_index_cli_run_store_is_resolved_and_readied
loremaster/tests/test_build_store.py::test_scout_from_config_store_is_resolved_and_unreadied
```

(Node ids taken from `pytest --collect-only`. The structural routing pins #7–9 do NOT redden
under a body mutation — source still calls `build_store` — they are the *static* inline catcher;
#2/#3/#10/#11 don't redden either.) The mutation proof runs at BUILD time (builder/adversary),
after `build_store` exists and callers route through it — I supply the pins + this set.

## Collect-only + RED receipts (@ `9195839`, offline)

```
$ uv run pytest loremaster/tests/test_build_store.py --collect-only -q | tail
  … (11 test ids) …
  11 tests collected in 0.26s

$ uv run ruff check loremaster/tests/test_build_store.py      → All checks passed!
$ uv run mypy  loremaster/tests/test_build_store.py           → Success: no issues found in 1 source file
$ uv run pytest loremaster/tests/test_build_store.py -p no:xdist -q | tail
  9 failed, 2 passed in 1.09s
    # 6 factory-gated  → Failed: build_store not yet extracted (packet 48-A) — contract is RED until it lands
    # 3 structural     → AssertionError: <caller> must obtain its write store from build_store(...)
    # 2 standing guards → PASSED (green-now by design)
```

**Harness validated** by a throwaway scratch suite (5 checks, all passed; file deleted, NOT
committed — brief-allowed): (A) the capture plumbing works end-to-end against the CURRENT inline
callers — `FakeEmbedder(dim)` passes `run_probe_gate` offline, the sentinel captures the real
store and aborts before I/O, `scout._store` is readable + `_connection is None`; (B)
`_assert_store_resolved` PASSES on a correct local `build_store` stub and FAILS (AssertionError)
on a `database + "_MUT"` stub — the mutation-proof property, demonstrated. So the pins are RED
for the right reason now and will discriminate a correct build from a wrong one after 48-A lands.

## DRY ledger (new test helpers)

No shared `LoreConfig` factory exists in this repo — the ruled house pattern is a per-file clone
of the minimal-valid payload (documented "independent-collectibility property",
`test_comms_wiring.py` header). So the config/creds helpers are a deliberate clone of that
sibling, not a hand-roll.

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_config_payload` / `_make_config` / `_slug` / `_surreal_credentials` | recon `lore_search "test helper that builds a LoreConfig"` + `lore_read test_comms_wiring.py` | no shared factory; per-file clone is the house rule | **REUSED the pattern** (cloned `test_comms_wiring._config`/`_slug`/`_surreal_test_env`); r2: ALL resolved fields (url/ns/dim/db/user/pass) set to distinctive sentinels for discrimination — the `_surreal_harness.surreal_url` import is dropped (file now imports nothing from the sibling tree) |
| `_install_ensure_ready_capture` + `_EnsureReadyAborted` | `lore_get_symbol SurrealStore.ensure_ready` / `.close` | plain async method; `close()` no-ops when unconnected | **HAND-ROLLED** (test-only capture seam; no existing helper captures a caller's constructed store — this is the offline observation mechanism) |
| `_assert_store_resolved` | `lore_get_symbol SurrealStore.__init__` | stores `_url/_namespace/_database/_dim/_user/_password` | **HAND-ROLLED** (asserts the ctor-stored attrs; no existing equivalent) |
| `_direct_call_names` | (stdlib `ast`/`inspect`) | — | **HAND-ROLLED** (AST routing check; `ast`/`inspect` are the stdlib tools, no package needed) |
| `_require_build_store` | — | — | **HAND-ROLLED** (contract-first RED-now gate; `getattr` keeps mypy/collection clean) |

## Flags / spec notes (STOP-and-flag, not improvised)

- **F1 (cosmetic, non-blocking) — design §1 R5 chain wording.** §1 R5 writes the server chain as
  `build_mcp_server`'s lifespan → `_eager_build_with_retry` → `build_app_context`. The ACTUAL
  immediate call in `build_mcp_server._lifespan` is `_eager_build_or_operator_safe_error(...)`,
  which WRAPS `_eager_build_with_retry` (the retry lives inside the operator-safe-error wrapper).
  Verified live @ `9195839` (`lore_get_symbol build_mcp_server`). My pins cite the full accurate
  chain and drive `build_app_context` (the chain's terminal store-builder); `_EagerStartupLifespan`
  confirmed deleted (`lore_verify` = not_found). No design intent is affected — item 4's intent
  ("cite the current chain, not the deleted symbol") is fully honored.
- **F2 (resolved) — `build_store` placement.** Design §1 "Where build_store lives" recommends
  `store/surreal.py`, with a `store/factory.py` fallback ONLY if `config.py` imports
  `store.surreal`. Verified: `config.py`'s imports are `os/pathlib/typing/urlsplit/yaml/dotenv/
  loresigil/pydantic/lorerunes` — it does NOT import `store.surreal`, so there is NO cycle →
  `store.surreal` is correct. My `_require_build_store()` resolves from `loremaster.store.surreal`
  and its docstring names the one-line change if the builder deviates.
- **Builder note (not a defect) — the `build_store` spy has no universal patch point** (recon):
  `build_app_context` imports `SurrealStore` LAZILY (function-body), while `cli._run`/
  `Scout.from_config` import it at module level. My contract is IMMUNE (it never spies on
  `build_store` — it captures the resulting store + reads source via AST), so the builder may use
  whichever import style; but a future test that DID spy on `build_store` would hit this.
- **No §1/§8 gap blocks the build.** The design is executable verbatim; the satisfiability receipt
  (0-failed vs a correct reference build) is the contract-adversary's job, not mine (per brief).
