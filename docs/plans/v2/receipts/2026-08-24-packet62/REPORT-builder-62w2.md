# REPORT-builder-62w2 — packet 62 wave 2: the per-agent capability / anti-spoofing mechanism

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — all 53 declared-RED pins GREEN, all 11 controls GREEN; the 3 wave-2 files
  go **64 passed / 0 failed** (the exact adversary reference-build target).
- deviations (each detailed in §Deviations):
  1. `PrincipalKeyStore.verify` keeps a leading shared-`is_blank` check ALONGSIDE the new shared
     `parse_credential` — a removed-behavior PRESERVATION so pre-existing packet-49 pin 17a stays
     green; matches the adversary reference build's `from lorerunes import is_blank, parse_credential`.
  2. `owner_principal` is stamped at CREATE only (not re-stamped on re-register — mint-once aligned;
     contract does not require re-stamp). Flagged, not silently decided.
  3. Added two small in-scope symbols the contract's seam needs but did not name: `AgentRegistry.
     owner_principal_of` (the owner read `stamp_owner` uses) and `loremaster.OwnerStampError`.
- Packages considered: **none new** — every mechanism reuses an in-tree shared helper or the stdlib
  (`secrets.token_urlsafe` + `hashlib` via `sha512_hex`, `str.partition`); no external dependency
  added, none evaluated because no new external-facing mechanism exists (crypto is the stdlib the
  repo already standardises on via `sha512_hex`).
- Reuse ledger: 6 new symbols, all dispositioned (§DRY ledger) — `parse_credential` (extracted per
  W2.6), `stamp_owner` (mandated ONE seam), `verify_capability`/`owner_principal_of`/`_deny_capability`
  (mirror the pkt-49 precedent), `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` (adjudication record).
- Graded: N/A (builder — own build). Gates run at working tree over base `8408e1b`.
- decisions-needed: 2 flags for the lead (§Flags) — the W2.6 fleet-briefing obligation (NOT a 62
  build task, by design) and confirmation that create-only owner-stamp is the intended scope.
- receipt pointers: gates §Gates; security mutation proofs §Security mutation proofs (recipes verbatim);
  DRY/parse-sharing §DRY ledger; prose sweep §Prose sweep.

## Capability check (tool honesty)
Brief demanded: edit production + prose docstrings, live store at ws://127.0.0.1:18000, lore tools,
`scripts/scratch_copy.sh`, gates (`pytest -n auto`, `scripts/typecheck.sh`, `ruff`). All available and
used. No blocked demand. The lore MCP tools loaded via `ToolSearch "+lore"` and were used for
registration/heartbeat; code-structure investigation here was direct file reads + one empirical
derivation (the governed-set derivation, §reach) — said out loud, no grep fallback on a structure
question that lore would have owned.

## What was built (file:symbol)
1. **`lorerunes/lorerunes/credentials.py`** (NEW) — `parse_credential(presented) -> tuple[str,str] | None`:
   the shared `<name>:<secret>` wire parse (`is_blank` reject → `partition(":")` FIRST-colon → blank-half
   reject), byte-exact with the sequence formerly inline at `principal_keys.py:519-525`. Stdlib-only
   (depends only on `lorerunes.blankness.is_blank`) — a pure predicate, W2.6. Re-exported in
   `lorerunes/__init__.py` `__all__`.
2. **`loremaster/loremaster/principal_keys.py`** — `verify` re-routed: `if is_blank(presented)` (pin 17a
   shared-blank guard, §F5) then `if parse_credential(presented) is None` (the shared parse). Both are
   module attributes (`from lorerunes import is_blank, parse_credential`) so the mutation pins reach them.
3. **`loremaster/loremaster/store/surreal_schema.py`** — `_AGENT_FIELD_SPECS` gains
   `("capability_hash", "option<string>", "")` and `("capability_expires_at", "option<datetime>", "")`
   (both `DEFINE FIELD OVERWRITE` via `_define_field`, store-ref §1.1/§1.4); `_agent_statements` appends
   a UNIQUE `IF NOT EXISTS` index on `capability_hash` (§1.1/§1.8 — UNIQUE over `option<string>` permits
   many NONE, rejects a duplicate real hash).
4. **`loremaster/loremaster/agents.py`**:
   - `AgentRegisterResult.capability: str | None = None` — the raw one-time credential (create only).
   - `register(..., owner_principal_id=None)`: the create branch MINTS `secrets.token_urlsafe(
     _SECRET_ENTROPY_BYTES)`, forms `f"{name}:{secret}"`, stores `sha512_hex(credential)` as
     `capability_hash` (raw secret NEVER persisted), stamps `owner_principal` as a bound `RecordID`
     (ownerless when `None`), `capability_expires_at=None`, and returns the raw credential ONCE.
     Re-register does not mint/rotate (mint-once-on-create).
   - `verify_capability(presented, access_token) -> str | None`: NO cache, one `now`, uniform-`None`
     no-oracle deny (laundered DEBUG) — the pkt-49 `PrincipalKeyStore.verify` discipline. Parses via the
     shared `parse_credential`, looks up by `sha512_hex($h)` over the UNIQUE index, then the four
     admission conditions in ONE indexed SELECT (owner-link dereference): (1) hash match, (2) agent not
     retired, (3) THE BINDING `owner_principal.email == access_token.subject` (NONE owner → deny;
     fail-closed), (4) owning principal active+unexpired PLUS the optional `capability_expires_at`
     enforced-when-set (ESC-3).
   - `owner_principal_of(agent_id) -> str | None`, `_deny_capability(reason)` (static, laundered).
5. **`loremaster/loremaster/owner_stamp.py`** (NEW) + `loremaster/__init__.py` re-export — `stamp_owner(
   access_token, agent_capability, *, registry) -> (owner_principal, owner_agent)` + `OwnerStampError`.
   Routes owner_agent through `verify_capability` (ROUTING-IS-NOT-SHARING mutation-proven), owner_principal
   from the verified agent's `owner_principal_of`; FAIL-CLOSED raise on any non-verify (R2.1). ESC-1: lives
   in `loremaster` (store-reading orchestration), NOT `lorerunes`; imports no sibling at runtime
   (`AccessToken`/`AgentRegistry` under `TYPE_CHECKING` — no import cycle).
6. **`loremaster/loremaster/token_verifier.py`** — `agent_of` docstring updated per W2.4/SF-3 (stays
   `None` under the capability model; the real resolver is `verify_capability`; do NOT stuff an agent into
   the token). Behaviour unchanged.
7. **`loremaster/loremaster/server.py`** — `_GOVERNED_TOOLS_PENDING_OWNER_STAMP: dict[str,str]` — the
   reach adjudication (Fork 4 R4.1–R4.3), keys = the DERIVED governed set (see §reach), each a non-empty
   trigger. Self-destructs entry-by-entry as 63/64 route each tool.
8. **`loremaster/loremaster/principals.py`** — module docstring gains the "⚠ RELATED, NOT CONFLATED
   (packet 62, I1/I2)" block: acknowledges the `owner_principal` owns edge (I1) while preserving the
   distinct-vocabulary / never-wire law (I2).

## reach — the governed set is DERIVED, not assumed
Empirically derived the live governed set from `partition_tools_by_population` over the real registry
(store-free `build_mcp_server` + `list_tools`): **6 tools** = `{lore_comms, lore_recall, lore_remember,
lore_tasks, lore_claim_task, lore_findings}` (== `_REVIEWED_GOVERNED_TOOLS ∩ live`; no unreviewed live
tool, so the 61b growth pin stays green). `_GOVERNED_TOOLS_PENDING_OWNER_STAMP`'s keys equal exactly this
set — the coverage-as-a-checked-variable equality (`test_every_governed_tool_is_pending_owner_stamp_and
_adjudicated`) passes, and the synthetic-new-governed-tool discriminator (`test_a_synthetic_new_governed
_tool_would_red_the_coverage`) confirms a grown governed set would red it.

## Gates (passed-COUNTs, real tree, base 8408e1b)
- **3 wave-2 contract files** (`test_agent_capability{,_seams,_reach}.py`): `-n auto` → **64 passed / 0
  failed in 7.98s**. Matches the adversary reference build's 64/0 target exactly.
- **Blast radius** (`-n auto`, one run): `test_agent_registry`, `test_agent_owns_principal_schema`,
  `test_principal_keys_store`, `test_principal_keys_schema`, `test_principals_store`, `test_principals
  _schema`, `test_token_verifier`, `test_oauth_identity_seam`, `test_retry_seam`, `test_tool_population
  _61b`, `test_pdp_oracle_61b`, `test_principal_delete_cascade_61`, `test_surreal_schema`, `test_schema
  _fold_coverage`, `test_schema_rebuild`, `test_surreal_store` → **1452 passed / 0 failed in 42.63s**.
  (The `test_retry_seam` `_empty_subscription` coroutine RuntimeWarning is pre-existing test-side noise,
  not from this change — present on the pre-fix run too.)
  ⚠ **PrincipalKeyStore regression check: 0 regressions** — the `parse_credential` extraction touches
  `PrincipalKeyStore.verify`; its full suite (`test_principal_keys_store.py`) is inside the 1452 and all
  green, INCLUDING pin 17a (`test_verify_routes_blank_check_through_the_shared_is_blank`), preserved by
  the leading `is_blank` guard.
- **lorerunes** (`-n auto`): **170 passed / 0 failed** (new `credentials.py` module + `__all__` change).
- **`bash scripts/typecheck.sh`**: `Success` on all 7 legs (lorerunes/lorescribe/loresigil/loremaster/
  skills/docs-eval/scripts) + shellcheck OK. **0 mypy errors.**
- **`uv run ruff check .`**: **All checks passed!** (repo-wide).

## Security mutation proofs (the load-bearing pins have teeth)
Run in a provenance-verified scratch copy — `scripts/scratch_copy.sh /tmp/scratch-62w2-mut`.
**Tree receipt (printed at run time): `loremaster.__file__ = /tmp/scratch-62w2-mut/loremaster/loremaster
/__init__.py`** — every mutation graded the ISOLATED copy (#140), never the real tree. Each mutation
carried a LANDING ASSERTION (the edit's target string must be present, else abort — #194), the pin went
**PASS→FAIL** on the break, and **restored→GREEN** after. The real tree was never mutated (all edits under
`/tmp/scratch-62w2-mut`). Recipes below are verbatim so a later reader can re-run without the scratch.

| # | break (in scratch) | pin | result |
|---|---|---|---|
| a-i | `verify_capability` cond-3 binding deny → `if False:` | `test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token` | **RED** → restored GREEN |
| a-ii | cond-3 **and** cond-4 made None-permissive (NONE owner treated as wildcard) | `test_an_ownerless_agents_capability_is_denied` | **RED** → restored GREEN |
| b | SHARED `lorerunes/credentials.py::parse_credential` → `return None` | BOTH `PrincipalKeyStore.verify` happy-path (`test_verify_returns_the_owning_principal_and_key_name`) AND `verify_capability` happy-path (`test_a_valid_capability_under_its_owners_token_resolves_the_agent`) | **BOTH RED** → restored GREEN |
| c | `verify_capability` memoises `presented→agent_id` (a cache) | `test_a_retired_agents_capability_is_denied_next_call_no_cache` | **RED** → restored GREEN |
| d | re-register mints a fresh secret + rotates the stored `capability_hash` | `test_re_register_does_not_rotate_a_live_secret` | **RED** → restored GREEN |
| e-i | add `capability_hash` field to the `Agent` model | `test_the_agent_model_has_no_capability_or_hash_or_secret_field` | **RED** → restored GREEN |
| e-ii | leak the raw credential into `last_note` (a rendered column) | `test_a_secret_shaped_value_never_appears_in_a_rendered_agent` | **RED** → restored GREEN |

Notes on (a): the brief bundled "binding + ownerless" under one break, but they guard DISTINCT wrong
builds — the binding pin catches a *present-but-wrong* owner (removing cond-3's mismatch deny), the
ownerless pin catches a *NONE-owner-as-wildcard* build (None-permissive cond-3 AND cond-4). This is
defense-in-depth: an ownerless agent is denied by BOTH cond-3 (owner_email NONE) and cond-4 (owner_status
NONE ≠ active), so a single-condition skip does NOT open the ownerless door — which is why (a-ii) needs
both conditions None-permissive to red the ownerless pin. Reported as measured, not as hoped.

Verbatim mutation targets (all `str.replace`, single-shot, landing-asserted):
- a-i: `if not owner_email or not token_principal or str(owner_email) != str(token_principal):` → `if False:`
- a-ii: same cond-3 → `if owner_email is not None and token_principal is not None and str(...)...:`; and
  `if row.get(_OWNER_STATUS_ALIAS) != _PRINCIPAL_STATUS_ACTIVE:` → `if row.get(_OWNER_STATUS_ALIAS) is not None and row.get(_OWNER_STATUS_ALIAS) != _PRINCIPAL_STATUS_ACTIVE:`
- b: `credentials.py` body `if is_blank(presented): return None` → `return None`
- c: insert cache check after the malformed guard + memoise before the final `return self._bare_id(...)`
- d: replace the re-register `return AgentRegisterResult(...)` with a mint + `UPDATE ... SET capability_hash=$rh` + return the new capability
- e-i: append `capability_hash: str | None = None` to the `Agent` model fields
- e-ii: `_COL_LAST_NOTE: None,` → `_COL_LAST_NOTE: capability,` in the create CONTENT

## parse_credential — ONE IMPLEMENTATION proven (both verifies share it)
- **Identity**: `principal_keys.parse_credential is lorerunes.parse_credential` AND `agents.parse_credential
  is lorerunes.parse_credential` — pinned green by `test_{principal_keys,agents}_references_the_lorerunes
  _parse`.
- **Mutation (routing, per-consumer)**: `test_breaking_the_shared_parse_denies_{PrincipalKeyStore_verify,
  verify_capability}` — patch each module's `parse_credential` → its verify denies — both green.
- **Mutation (sharing, source)**: proof (b) above — breaking the ONE `lorerunes` source reds BOTH
  consumers' happy-paths. This is sharing-by-MUTATION, not routing.

## Prose sweep (item 6 — BARE-pattern, anchor-free; every hit + verdict)
Swept `loremaster/loremaster` + `lorerunes/lorerunes` for retired "forbids wiring" / "deliberately
unlinked" / "unrelated" / "not linked" / "not wired" class prose (the P8d rendered-prose class). Result:
**CLEAN of retired non-link prose.** The only principal↔agent-relationship hits:
- `principals.py:31` "never wire `principal.role`/`status` to the `agent` tuples" — **KEEP** (this is the
  I2 distinct-vocabulary law, still TRUE — vocabularies stay distinct; explicitly preserved).
- `principals.py:34` "the two identity NODES are no longer *unrelated*" — **NEW (the I1 fix I added)**.
- `token_verifier.py:172` "the agent is NEVER carried in the transport token" — **NEW (my W2.4 docstring
  update)**, about the token-borne agent, not the owns edge — correct.
- Every other `unlink`/`unrelated` hit (`sqlite_resilient.py` file unlink, `impact.py`/`graph.py`/`symbols.py`
  symbol-profile "unrelated", `server.py:10129` etc.) — **UNRELATED to the principal↔agent edge; no action.**
The brief's named phrases `forbids wiring` / `deliberately unlinked` returned **zero hits** anywhere in
production. This corroborates the contract author's LEG-5 note that the retired-non-link sweep came back
clean; the only stale-prose site was `principals.py:13-31`, now updated (I1) with I2 preserved (both pinned).

## DRY ledger
| new symbol | lore/search run | returned | disposition |
|---|---|---|---|
| `lorerunes.parse_credential` | read `principal_keys.py:519-525` (the inline parse) + `blankness.py` | the inline `is_blank→partition→blank-half` sequence, unshared | **EXTRACTED** per W2.6 contract mandate — promoted to `lorerunes`; both verifies reference the ONE object (identity + mutation pinned) |
| `loremaster.stamp_owner` | grepped `Subject(`/`owner_principal=`/owner-derivation | none exists (this is the first) | **HAND-ROLLED** — the ONE server-derived owner seam (R1.1); mandated new, mutation-proven it routes through `verify_capability` |
| `AgentRegistry.verify_capability` | read `PrincipalKeyStore.verify` | the pkt-49 4-condition/one-`now`/uniform-`None`/no-cache/no-oracle template | **MIRRORS** the precedent (discipline pinned in both, not a shared skeleton — admission conditions differ, W2.2) |
| `AgentRegistry.owner_principal_of` | — | no existing "who owns agent Y" read | **HAND-ROLLED** (minimal read the seam needs; `stamp_owner` reads owner from the verified row since only `registry` is injected) |
| `AgentRegistry._deny_capability` | read `PrincipalKeyStore._deny` | the laundered-DEBUG deny helper | **MIRRORS** the precedent (per-store — the label differs) |
| `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` | read `_REVIEWED_GOVERNED_TOOLS` / `partition_tools_by_population` | the derived-set idiom | **HAND-ROLLED** adjudication record (Fork 4; keys DERIVED-equal the governed set) |

REUSED (no clone, stated per the brief): `sha512_hex` (`loremaster.index.records`) · `secrets.token_urlsafe`
entropy `principals._SECRET_ENTROPY_BYTES` · the `_query` retry seam (`AgentRegistry._query`, no new store)
· `_PRINCIPAL_STATUS_ACTIVE` (`surreal_schema`) · `is_blank` (`lorerunes`) · `_to_aware_utc`/`_bare_id`
(existing `AgentRegistry`) · `_define_field`/`_unique_index` (schema emitters). No new store, no new
`_query` seam to enroll, no new dependency.

## Deviations (detailed)
1. **Two-guard `PrincipalKeyStore.verify` (`is_blank` THEN `parse_credential`).** The DRY extraction moves
   the blank check inside `parse_credential`, which would obsolete pre-existing pkt-49 pin 17a
   (`test_verify_routes_blank_check_through_the_shared_is_blank`, which patches `principal_keys.is_blank`
   and expects verify to deny). Rather than let an in-scope change red an out-of-scope pin (a test I may not
   edit), I preserved the removed behavior: `verify` keeps a leading shared-`is_blank` guard (routing pin
   17a — a §F5 clone guard) BEFORE the shared `parse_credential` (routing the seam pin). The two overlap on
   blankness by design but pin DISTINCT properties, both through ONE `lorerunes` predicate each. This is
   EXACTLY the adversary reference build's shape (`REPORT-adversary-62w2.md:323` — `from lorerunes import
   is_blank, parse_credential`), i.e. the intended build, not an improvisation. Removed-behavior verdict:
   **preserved-with-pin** (pin 17a; spec §F5).
2. **`owner_principal` stamped at CREATE only.** Re-register does not re-stamp the owner (mint-once-on-create
   aligned — the owner is set at birth; a running agent's owner is not rewritten mid-session). The contract
   tests owner stamping only on create (`test_register_stamps_owner_principal_from_the_server_derived_id`
   uses a fresh register) and has no re-register-owner pin, so this is contract-sufficient. Flagged for the
   lead (§Flags) since it is a scope choice, not a forced one.
3. **`owner_principal_of` + `OwnerStampError` added.** The seam contract injects only `registry` into
   `stamp_owner` (no PrincipalStore), and the token's `subject` is the email (not the record id the PDP
   stamps), so `owner_principal` must be read from the VERIFIED agent row — which the binding has already
   proved is the token's principal. `owner_principal_of` is that minimal read; `OwnerStampError` is the
   fail-closed signal. Both in-scope (production, writable set).

## Flags for the lead
- **W2.6 fleet-briefing obligation (NOT a 62 build task).** The capability model requires each subagent to
  CAPTURE `register`'s one-time `capability` and PRESENT it on every governed call — a spawn-BRIEF change
  (like "register first"), owned by orchestration/packet-65, per the addendum's explicit "FLAG, not a
  62-build task". Pre-cutover nothing breaks (62 governed tools are still RED_ADJUDICATED — 63/64 wire
  them). Surfaced so it is not lost.
- **Confirm create-only owner-stamp is intended** (deviation 2). If the operator wants re-register to
  re-stamp `owner_principal` from a later credential (e.g. an ownerless pre-cutover agent gaining an owner
  post-cutover), that is a small follow-up — say so and I/63 can add it. My recommendation: keep create-only
  for wave 2 (mint-once aligned, contract-sufficient); revisit at the 63/64 cutover.

## Artifacts
- Changed production files `cp -a` to the scratchpad (insurance against concurrent tree ops on this shared
  branch): `.../scratchpad/builder-62w2-changed/` (10 files).
- Scratch copy `/tmp/scratch-62w2-mut` (disposable, `scratch_copy.sh`-provenance-verified) still present for
  the cold audit / security auditor to re-run the mutation recipes; reproducible from the verbatim recipes
  above if reaped.
- **DID NOT COMMIT** (per brief) — the lead commits after the cold-audit + security-auditor GO.
