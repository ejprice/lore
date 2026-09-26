# Packet 64 — ruling amendment 6 (sidecar-64, 2026-09-26): the restore driver's three seam decisions — the `UNWRAP_ALLOWLIST` entry (evidence-backed, with the shared-seam trigger named), FORK A ratified (harness credentials, never the stores' env file), the vestigial `EnvironmentFile=` leg dropped

Rules `REPORT-fix-restore-seams.md` (`441f3b0`) decisions (1)–(3). Facts read this turn: `UNWRAP_ALLOWLIST`
(`loremaster/tests/test_secret_typing.py`) holds SIX entries — two `loremaster/auth.py` guards,
`calibration/counting.py::build_auth_headers` (the Anthropic `count_tokens` header seam, R26),
`store/_txn.py::signin_credentials` (the SDK signin payload), `loresigil/voyage_http.py::build_auth_
headers` (Voyage's bearer), `loresigil/factory.py::_reject_a_blank_credential` — and its bound pin reads
`5 <= len <= 7` with the comment *"the ruled design is SIX"*; NO entry authenticates SurrealDB over
HTTP (the SDK signin is the only SurrealDB credential unwrap). `scripts/restore_prod_dump.py::build_auth_
headers(credential: SecretStr, *, user, namespace, database)` is the driver's typed seam: `httpx.BasicAuth`
(the library's encoding, never hand-rolled base64), the ONE unwrap, the FULL header map (`Accept`,
`Surreal-NS`, `Surreal-DB`, `Authorization`) so no request builds headers elsewhere. The suite harness
resolves the test store's credentials via `surreal_user()` / `surreal_password() -> SecretStr`
(`LORE_TEST_SURREAL_USER` / `LORE_TEST_SURREAL_PASS`, spike defaults). The quadlet leg asserts BOTH the
bind port per store AND `EnvironmentFile=<STORES_ENV_FILE>` — the second half names a file the driver
no longer reads.

## (1) — RULING: RATIFY the entry as an evidence-backed exemption; the shared seam is a NAMED trigger, not built now

- **ONE IMPLEMENTATION asked, answered by enumeration (the allowlist IS the enumeration):** nothing else
  in the workspace builds a SurrealDB HTTP `Authorization` header — the three existing `AUTH_HEADER`/
  `SDK_PAYLOAD` seams authenticate three OTHER services (Anthropic, Voyage, the SurrealDB SDK signin).
  The driver is the FIRST SurrealDB-HTTP consumer, so its builder IS the seam; a shared
  `loremaster/store` HTTP-auth module with ONE caller would be a home with no second resident (the
  63-rulings §1.1 principle: a substrate ships WITH its first consumer, never ahead of one).
- **The trigger for the lift, named:** *"the SECOND SurrealDB-HTTP consumer"* — the obvious candidate is
  the 65 dress rehearsal's FRESH `surreal export` of `:18500` (a `POST /export` driver against
  PRODUCTION), or any `/sql`-over-HTTP tool. At that moment `build_auth_headers` moves to
  `loremaster/store/` beside `signin_credentials` (ONE credential module for one engine, two transports),
  BOTH consumers call it, the allowlist entry MOVES with it (the count returns to six), and the move is
  proven by mutation (perturb the shared builder → both drivers' header pins move).
- **The bound:** SEVEN fills the `<= 7` ceiling exactly. That is the pin working as designed — a
  seventh unwrap is a deliberate, reviewer-visible diff — AND it means the NEXT unwrap anywhere in the
  workspace cannot be added without either the lift above (which frees a slot) or a re-ruling of the
  ceiling (the operator's — the bound is the secret-typing design's §0.9 constant). State that in the
  entry's comment so the next engineer meets the bound deliberately.
- **Who adds the line (the lead writes no code):** the fix agent that proved satisfiability in-process
  (`fix-restore-seams`, if still live — a ONE-line edit + the evidence comment naming this amendment,
  the trigger and the ceiling); if it has retired, a fresh one-shot `fix-restore-seams-2` (never the
  same name). The lead commits it as ONE concern. The entry:
  `"scripts/restore_prod_dump.py::build_auth_headers": AUTH_HEADER` with the comment above.
- **Pin (already in the invariant, stated so it is not re-invented):** the exact-set discovery reds a
  second unwrap anywhere in the driver; `TestEveryUnwrapSiteIsAllowlisted` 9/9 with the bound at 7 (the
  fix report's in-process receipt); the construction gate (`headers=` only from the seam) holds.

## (2) — RULING: FORK A = A3, RATIFIED — the test store's OWN credentials, from the harness seam; never the stores' env file

- **Why A3 and not A1:** `~/docker/mcp/lore-secrets/lore.env` carries the PRODUCTION store's secrets. A
  script whose endpoint is `:18000` BY CONSTRUCTION (amendment 3 §D-3 step 1) has no business holding
  `:18500`'s credential in memory — least privilege, and the #422-class blast radius (a leaked
  scratch/log line from a TEST tool exposing PROD credentials). The R3 allowlist (`RESOLVE_SECRET_ENV_
  FILE_ALLOWLIST` = exactly `counting.py::load_api_key`) is a standing operator ruling that a NEW env-file
  reader is an operator decision — A1 would ask the operator for a grant to a worse design. A2 (bare
  `SURREAL_*` env) makes the standard suite's live legs depend on the runner's shell — the #131 fixture
  fiction in reverse (green only where the runner remembered to export).
- **A3 is the repo's ONE answer** to "what authenticates to `:18000`" — every live test, the F5 observer,
  the S2 leg's consumer and the driver's own read-backs already use it; the driver importing it for the
  import call too is ROUTING to the shared seam, not a copy. `surreal_password()` returns a `SecretStr`,
  so the typed seam's contract (`credential: SecretStr`) holds end to end; a wrong credential is a live
  HTTP 401 → exit 2 (the fix report's control 4), never a silent success.
- **The production-export driver (65) is a DIFFERENT tool:** it targets `:18500`, so it MUST read the
  stores' env file — under an R3 grant the operator gives THAT tool, with the lift in (1). Named, not
  built.
- **Rider:** the driver's docstring states the credential source (the harness seam, the two env
  overrides, the spike defaults) and that the stores' env file is NEVER read; a bare `awk` for
  `lore-secrets` / `dotenv_values` / `STORES_ENV_FILE` over `scripts/restore_prod_dump.py` → 0 hits (after
  (3)).

## (3) — RULING: DROP the `EnvironmentFile=` half; KEEP the ports half; delete the orphaned constant

- The leg's real job is the PORTS cross-check — *the endpoint constants name the store the quadlets
  actually bind* (`:18000` = test, `:18500` = production): a live guard against the one confusion the
  store reference calls a production incident. KEEP it, renamed `leg_store_ports_match_the_quadlets`.
- The `EnvironmentFile=` half asserted *"the quadlet names the env file this script reads"* — after (2)
  the script reads no env file, so the assertion guards nothing and keeps `STORES_ENV_FILE` alive as a
  constant with no consumer (a guard nobody relies on is a hope with a filename; a constant nobody
  reads is the next stale citation). DROP the half; DELETE `STORES_ENV_FILE`; the DUAL row: *"the env-file
  cross-check — DROPPED-DELIBERATELY with the env-file read it certified (amendment 6 §2)"*.
- **Pin:** the renamed leg reds when either quadlet's `--bind` moves off its constant (unchanged
  virtue); the `awk` sweep in (2)'s rider is its replacement for the file half.

## Riders roll-up
| item | where | RED when |
|---|---|---|
| allowlist entry + evidence comment (trigger + ceiling) | `test_secret_typing.py` (fix agent's one-line edit; lead commits) | a second driver unwrap; the ceiling silently raised |
| harness credentials only; 401 → exit 2; sweep 0 hits for the env-file names | driver docstring + self-test | an env-file read returns |
| ports leg kept/renamed; env-file half + constant gone; DUAL row | `SelfTest` | a `--bind` drift; a resurrected `STORES_ENV_FILE` |

## Discipline
- Packages considered: `httpx.BasicAuth` for the header (REUSE — the library's encoding, read in the
  driver); no new mechanism.
- Store law §9 (two stores; never a test at `:18500`) — (2) is that law applied to CREDENTIALS, not only
  to the endpoint.
- No code/tests/store touched; this doc only; no attribution trailer.
