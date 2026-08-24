# REPORT-contract-62w2 — packet 62 Wave 2 CONTRACT (the per-agent CAPABILITY / anti-spoofing mechanism A)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — **§1.1** (FIELD `OVERWRITE`;
  INDEX `IF NOT EXISTS` never `OVERWRITE` — a flip is a boot-time crash), **§1.4** (a NEW field on a
  POPULATED table MUST be `option<>`; a DEFAULT does not rescue a legacy row), **§1.6** (the
  dirty-store blind spot — every ordinary fixture mints a VIRGIN db), **§1.8** (a UNIQUE index over
  `option<string>` PERMITS multiple NONE + rejects duplicate non-NONE — EXACTLY the `capability_hash`
  shape), **§2** (`SELECT *` OMITS a NONE `option<>` column; explicit projection reads `None`).
  Cited by §, never re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: spike-surreal test store `ws://127.0.0.1:18000` was
`active` (systemd); lore tools loaded via `ToolSearch "+lore"`; pytest/ruff/`scripts/typecheck.sh`
ran; two `opus48-worker` scouts mapped the reach/PDP + harness/seam surfaces. No impossibilities.
One deviation: the two scouts' `REPORT-*.md` files were harness-blocked (subagents must return text),
so their findings arrived as final messages — I relayed the load-bearing facts into this report's
receipts. No effect on the contract.

---

## SUMMARY BLOCK
- **State:** done. 63 pins collect cleanly; **52 RED against HEAD `6d6c63c` for their own reason**,
  11 GREEN guards/positive-controls (classified below). All gates green on the contract files
  (ruff `All checks passed!`; `scripts/typecheck.sh` clean for all three files).
- **Deviation 1:** the reach pin (item 5b / R4.1) realises Fork 4's "per-tool RED_ADJUDICATED" as a
  SINGLE coverage-as-a-checked-variable pin over a production adjudication map
  `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` (self-destructs entry-by-entry as 63/64 route each tool),
  not N literal xfail legs. Reach-law INVARIANT identical; flagged for the lead (§Escalations).
- **Deviation 2:** the retired-prose sweep (item 6) found NO literal "unlinked"/"forbids wiring"
  prose and NO test asserting the principal↔agent non-link (grep clean, receipt below) — so item 6
  is surgical: a `principals.py` module-docstring acknowledgement of the owns edge (pinned), not a
  deletion. The design's "forbids wiring" phrases were paraphrases, not code strings.
- **Packages considered:** none new — the contract PINS reuse of existing in-house seams, never a
  hand-roll (`loremaster.index.records.sha512_hex`, stdlib `secrets.token_urlsafe(32)`, the
  `surreal_schema._define_field`/`_unique_index` emitters, the `AgentRegistry._query` retry seam,
  and the `PrincipalKeyStore.verify` admission template). Verdict: `keep_with_trigger` (trigger: the
  builder must ROUTE through each, proven by the mutation pins — a hand-rolled clone reds them).
- **Reuse ledger:** none — contract tests introduce no PRODUCTION reusable symbol. The production
  reuse the contract DEMANDS (`parse_credential` extraction shared by both verifies; `sha512_hex`;
  `AgentRegistry._query`) is dispositioned in §DRY.
- **Graded:** n/a — contract author, renders no verdict on another agent's artifact. Authored +
  verified RED at HEAD `6d6c63c` (working tree carries only the 3 new test files, untracked).
- **Decisions-needed:** **ESC-1** (stamp_owner home/signature — spec internally inconsistent;
  recommendation given, pinned reading (A)); **ESC-2** (explicit `capability_hash`-clear revoke verb
  — W2.3(b) is a "recommend"; I pinned only retire-based revocation; recommend deferring the verb);
  **ESC-3** (the `capability_expires_at` enforced-when-set pin — SF-2 frames enforcement as optional
  defense-in-depth; I pinned enforced-when-set to avoid a decorative-field lie — the lead/adversary
  may delete it deliberately). Details in §Escalations.
- **Receipt pointers:** expected-RED set §"Declared expected-RED"; guards §"Guards"; satisfiability
  §"Satisfiability argument"; DRY-mutation §"DRY"; store-ref reliance §"Store-ref"; escalations
  §"Escalations".

---

## What the contract covers (files + concern → spec clause)

Three new files under `loremaster/tests/` (writable set); no production touched.

- **`test_agent_capability.py`** (the mechanism, live store): capability_hash DDL (option<string>
  OVERWRITE + UNIQUE `IF NOT EXISTS`, §1.1/§1.4/§1.8/W2-R7) · optional `capability_expires_at`
  seam (SF-2) · dirty-store migration (§1.6) · mint-in-register + returned-once + stored-hash
  invariant + mint-once-on-create (W2.3/W2-R6) · no-credential-leak (§F3a/W2-R6, hostile fixture) ·
  verify_capability admission: hash-match/forge, THE BINDING (W2-R2), retired no-cache (W2-R3),
  owning-principal active+unexpired (W2.2 cond 4), uniform-deny/injection (bound param) · lifecycle
  lifetime not clock-TTL (SF-2/W2-R4) · verify rides the EXISTING `AgentRegistry._query` (W2.2, #353
  settled) · register-time owner stamp from the server-derived credential, ownerless-when-absent,
  no display-owner arg (R3.3/§3.2.2).
- **`test_agent_capability_seams.py`** (shared seams, live store): `parse_credential` behaviour +
  ONE-implementation (identity + mutation across BOTH `PrincipalKeyStore.verify` AND
  `verify_capability`, W2.6) · `stamp_owner` existence/verified-pair/fail-closed/routes-through-verify
  (R1.1/R2.1) — pinned per ESC-1 reading (A).
- **`test_agent_capability_reach.py`** (structural, store-free): the DERIVED reach pin over
  `partition_tools_by_population` (R4.1–R4.3) with a synthetic-new-governed-tool discriminator ·
  lore_comms exposes no owner/capability caller input (§3.2.2/W2.1) · `agent_of` stays None
  (W2.4/SF-3) · the PDP single brain (authorize/authorize_filter signatures + Subject shape) is
  UNCHANGED (§5) · the 48 non-wiring guard docstring acknowledges the owns edge while preserving the
  distinct-vocabulary law (I1/I2).

---

## Declared expected-RED node ids (from `--collect-only`, fixed before any run)

For `scripts/mutation_proof.py` and the adversary's reference build: these **52** nodes are RED at
HEAD `6d6c63c` and go GREEN on a correct build. The other **11** collected nodes are GREEN-at-HEAD
guards/positive-controls (see §Guards) — they must STAY green, never appear in the expected-RED set.

```
tests/test_agent_capability.py::TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_is_emitted
tests/test_agent_capability.py::TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_is_option_string
tests/test_agent_capability.py::TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_is_OVERWRITE
tests/test_agent_capability.py::TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_routes_through_the_shared_emitter
tests/test_agent_capability.py::TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_emitted
tests/test_agent_capability.py::TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_UNIQUE
tests/test_agent_capability.py::TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE
tests/test_agent_capability.py::TestTheOptionalCapabilityExpiresSeam::test_the_capability_expires_field_is_emitted_as_option_datetime
tests/test_agent_capability.py::TestMintInRegister::test_first_register_returns_a_raw_capability_once
tests/test_agent_capability.py::TestMintInRegister::test_the_stored_hash_is_sha512_of_the_whole_returned_credential
tests/test_agent_capability.py::TestMintInRegister::test_the_raw_secret_is_never_persisted_as_a_readable_column
tests/test_agent_capability.py::TestMintInRegister::test_re_register_does_not_rotate_a_live_secret
tests/test_agent_capability.py::TestTheCapabilityNeverLeaksOntoTheAgentValueObject::test_a_secret_shaped_value_never_appears_in_a_rendered_agent
tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_a_valid_capability_under_its_owners_token_resolves_the_agent
tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_a_forged_capability_without_the_secret_is_denied
tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token
tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_a_retired_agents_capability_is_denied_next_call_no_cache
tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_a_suspended_owning_principal_denies_the_capability
tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_an_expired_owning_principal_denies_the_capability
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank]
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[whitespace]
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[no-colon]
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank-secret]
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank-name]
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank-halves]
tests/test_agent_capability.py::TestVerifyCapabilityUniformDenyNoOracle::test_an_injection_laden_credential_is_a_bound_param_not_interpolated
tests/test_agent_capability.py::TestCapabilityLifetimeIsLifecycleScopedNotAClockTtl::test_a_capability_with_no_expiry_is_not_time_gated
tests/test_agent_capability.py::TestCapabilityLifetimeIsLifecycleScopedNotAClockTtl::test_a_capability_whose_optional_expiry_is_in_the_past_is_denied
tests/test_agent_capability.py::TestVerifyCapabilityRidesTheSharedQuerySeam::test_verify_capability_routes_through_agent_registry_query
tests/test_agent_capability.py::TestRegisterStampsOwnerPrincipalFromTheCredential::test_register_stamps_owner_principal_from_the_server_derived_id
tests/test_agent_capability.py::TestRegisterStampsOwnerPrincipalFromTheCredential::test_register_without_a_credential_is_ownerless_not_fabricated
tests/test_agent_capability.py::TestRegisterStampsOwnerPrincipalFromTheCredential::test_register_exposes_no_display_owner_argument
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_parse_credential_exists_in_lorerunes
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_well_formed_credential_splits_on_the_first_colon
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank]
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_malformed_credential_is_none[whitespace]
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_malformed_credential_is_none[no-colon]
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank-secret]
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank-name]
tests/test_agent_capability_seams.py::TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank-halves]
tests/test_agent_capability_seams.py::TestParseCredentialIsTheONEImplementation::test_principal_keys_references_the_lorerunes_parse
tests/test_agent_capability_seams.py::TestParseCredentialIsTheONEImplementation::test_agents_references_the_lorerunes_parse
tests/test_agent_capability_seams.py::TestParseCredentialIsTheONEImplementation::test_breaking_the_shared_parse_denies_PrincipalKeyStore_verify
tests/test_agent_capability_seams.py::TestParseCredentialIsTheONEImplementation::test_breaking_the_shared_parse_denies_verify_capability
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_exists_in_lorerunes
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_returns_the_verified_owner_pair
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_fail_closes_on_a_binding_mismatch
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_fail_closes_on_an_absent_or_garbage_credential
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_routes_through_verify_capability
tests/test_agent_capability_reach.py::TestTheGovernedSurfaceReachPin::test_every_governed_tool_is_pending_owner_stamp_and_adjudicated
tests/test_agent_capability_reach.py::TestTheGovernedSurfaceReachPin::test_a_synthetic_new_governed_tool_would_red_the_coverage
tests/test_agent_capability_reach.py::TestTheNonWiringGuardDocstringIsUpdated::test_the_module_docstring_acknowledges_the_owns_edge
```

RED→verify receipt (HEAD `6d6c63c`, spike-surreal `ws://127.0.0.1:18000`): `52 failed, 11 passed in
~11s`. Spot-checked failure REASONS (not fixture bugs): binding → `verify_capability unbuilt`; mint
→ `register(...).capability ... unbuilt`; owner-stamp → `TypeError: register() got an unexpected
keyword argument 'owner_principal_id'`; stamp_owner → `lorerunes.stamp_owner is unbuilt (R1.1)`.

## Guards / positive-controls (GREEN at HEAD — NOT expected-RED)

These discriminate a WRONG build while passing at HEAD and on a correct build; they must never be
listed as RED. `test_a_legacy_agent_survives_the_field_add_and_reads_capability_none` ·
`test_the_field_add_does_not_write_poison_the_legacy_row` (§1.4 option<> discriminators — GREEN at
HEAD because OLD==NEW slice, RED on a required-not-option build) · `test_the_agent_model_has_no_
capability_or_hash_or_secret_field` (reds a leaky model) · reach `test_the_governed_set_is_non_empty`
(anti-vacuity) · `test_lore_comms_input_schema_has_no_owner_or_hash_input` · `agent_of` ×2 ·
authorize/authorize_filter/Subject signature ×3 · `test_the_distinct_vocabulary_law_is_preserved`.

## Satisfiability argument (what a correct build does to green each RED pin)

The contract is satisfiable in one coherent build (the adversary's reference build discharges the
formal receipt; this is the argument):
1. **DDL** — append `("capability_hash", "option<string>", "")` and `("capability_expires_at",
   "option<datetime>", "")` to `_AGENT_FIELD_SPECS` (route through `_define_field` ⇒ `OVERWRITE`),
   and a `_unique_index(AGENT_TABLE, f"{AGENT_TABLE}_capability_hash", ("capability_hash",))` in
   `_agent_statements()` ⇒ the offline + live DDL + migration pins green (§1.8 gives multiple-NONE +
   unique-non-NONE for free). The Wave-1 exact-set delete pin does NOT move (capability_hash is not
   a `record<principal>` link — confirmed by scout).
2. **Mint** — `register`'s create branch: `secret = secrets.token_urlsafe(32)`;
   `capability = f"{name}:{secret}"`; write `capability_hash = sha512_hex(capability)` into the same
   `CONTENT`; also stamp `owner_principal` from a new server-derived `owner_principal_id` kw;
   `AgentRegisterResult` gains `capability: str | None` (the raw string on create, `None` on
   re-register). The else/re-register branch mints nothing (mint-once) ⇒ the mint + owner + no-leak
   pins green. `Agent` and `_row_to_agent` are untouched, so the hash never reaches the value object.
3. **Verify** — `AgentRegistry.verify_capability(presented, access_token)` mirrors
   `PrincipalKeyStore.verify`: one `now`; `parse_credential(presented)` reject; `sha512_hex(presented)`
   UNIQUE-hash SELECT dereferencing `owner_principal.{email,status,expires_at}` + `status` +
   `capability_expires_at`; four independent early denies (hash-miss / retired / binding
   owner_email≠token.subject / owning-principal inactive-or-expired) + the optional expiry; uniform
   `None`. Rides `self._query` ⇒ every admission + no-cache + injection + rides-seam pin green.
4. **Seams** — extract `lorerunes.parse_credential`; have BOTH verifies import it as a module
   attribute; add `lorerunes.stamp_owner(access_token, agent_capability, *, registry)` composing
   `registry.verify_capability` (fail-closed) ⇒ the parse + stamp_owner pins green.
5. **Reach + prose** — add `loremaster.server._GOVERNED_TOOLS_PENDING_OWNER_STAMP` (a dict of the 6
   governed tools → their "packet 63/64 retrofits <tool>" trigger); update the `principals.py`
   module docstring to name the owns edge ⇒ the reach + docstring pins green.

## DRY — the ONE-implementation mutation proof (how changing `parse_credential` reds BOTH sides)

Three composed pins (`test_agent_capability_seams.py::TestParseCredentialIsTheONEImplementation`):
- **IDENTITY (single source):** `principal_keys.parse_credential is lorerunes.parse_credential` AND
  `agents.parse_credential is lorerunes.parse_credential` (both consumers reference the ONE object as
  a module attribute — a private inline/clone in either fails this even if it behaves identically:
  ROUTING-IS-NOT-SHARING).
- **MUTATION (PrincipalKeyStore side):** monkeypatch `principal_keys.parse_credential` to reject
  everything ⇒ `PrincipalKeyStore.verify("k:s")` DENIES (it routed through the shared parse).
- **MUTATION (AgentRegistry side):** monkeypatch `agents.parse_credential` to reject everything ⇒
  `verify_capability(valid_cap, token)` DENIES (with a positive control that the real capability
  resolves BEFORE the mutation). Together: changing the shared parse reds BOTH verifies — the
  brief's "change the parse → BOTH stores' verify pins red", plus the identity guarantee that it is
  literally ONE object. The `AgentRegistry._query` retry seam is reused (not cloned) and
  mutation-pinned (`test_verify_capability_routes_through_agent_registry_query`).

## Store-ref sections relied on
§1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS) · §1.4 (option<> on a POPULATED table + no-DEFAULT
rescue — the write-poison discriminator) · §1.6 (dirty-store idiom: OLD slice → legacy row → NEW
slice) · §1.8 (UNIQUE over option<string> = multiple-NONE + unique-non-NONE — the `capability_hash`
shape) · §2 (explicit projection reads NONE back; `SELECT *` omits it).

## Retired-prose sweep receipt (item 6 close-out)
`grep -rniE "deliberately[ -]unlinked|forbids wiring|no edge between|unlinked|never linked|not
linked"` over `loremaster/loremaster loremaster/tests docs/design/authorization-model*` → **0 hits**
(excluding owner_principal lines). No test asserts the principal↔agent non-link (grep for
`principal.*agent.*(not|never).*(link|wire|conflat|relat)` over `loremaster/tests` → 0). So the OLD
world was never pinned as a test; item 6 reduces to the module-docstring acknowledgement pinned in
`test_the_module_docstring_acknowledges_the_owns_edge` (RED) + the I2-preserved guard. The design's
"forbids wiring"/"deliberately unlinked" were paraphrases, not code strings.

---

## Escalations (§2 — surfaced, not silently resolved)

### ESC-1 (design fork — spec internally inconsistent) — `stamp_owner` home vs signature
- Scope-line item 3 + R1.1 place `stamp_owner` in **`lorerunes`** (stdlib-only, imports NO sibling —
  `lorerunes/__init__.py`; CLAUDE.md "predicates, not entry points").
- W2.4 has it **call `resolve_agent(cap, token, registry)`** — needing the `AgentRegistry`
  (`loremaster`). A function importing `loremaster` cannot live in stdlib-only `lorerunes`.
- **Two readings, different code.** (A) [I pinned this] `stamp_owner` in `lorerunes` takes the
  registry as an OPAQUE duck-typed resolver, staying import-pure:
  `stamp_owner(access_token, agent_capability, *, registry) -> (owner_principal, owner_agent)`.
  (B) `stamp_owner` relocates to `loremaster` (it is fundamentally an entry point), with only the
  fail-closed predicate — if anything — in `lorerunes`.
- **Recommendation: (A).** It honours the scope line's "in lorerunes" AND lorerunes's purity (the
  existing purity pin would catch a `loremaster` import), and makes fail-closed the shared policy.
  The load-bearing property (fail-closed + owner-from-verified-capability, never an argument) is
  signature-robust; the signature is isolated in ONE helper (`_call_stamp_owner`) so a lead ruling
  is a one-function edit. **If the lead/operator rules (B) or a different signature, only
  `test_agent_capability_seams.py`'s stamp_owner pins move.**

### ESC-2 (scope question) — the explicit `capability_hash`-clear revoke verb (W2.3(b))
W2.3 rules retire-based revocation (condition 2, RULED) AND "recommends" a thin explicit-clear verb
mirroring `PrincipalKeyStore.revoke`. I pinned **only** the RULED retire-based revocation
(`test_a_retired_agents_capability_is_denied_next_call_no_cache`) — it fully satisfies W2-R3.
**Recommendation: defer the explicit verb** (a "recommend", not a ruling; adds surface without a
current consumer). If the lead wants it in wave 2, I add its pin.

### ESC-3 (rigor call) — `capability_expires_at` enforced-when-set
SF-2 rules the seam PRESENT and defaulting to never (NO clock TTL). It frames ENFORCEMENT as
optional defense-in-depth. I pinned **enforced-when-set** (`test_a_capability_whose_optional_expiry_
is_in_the_past_is_denied`) because a field that exists but is never checked is a decorative lie the
trust doctrine forbids (a surface that looks like it limits and does not). **If the operator wants
the field present-but-unenforced in wave 2, this ONE pin is deleted deliberately** (per the
pin-the-miss law — a bound met deliberately, with its rationale attached).

---

## Notes for the adversary + security-auditor (make their job findable)
- The **binding** (`test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token`,
  W2-R2) is the load-bearing anti-spoof pin: A's valid capability under B's token → DENY, with the
  A-under-A positive control. It is what reduces the residual to the ACCEPTED own-capability leak
  (Fork 1). Attack it hardest.
- Every deny pin carries a POSITIVE CONTROL (the good input accepted) so nothing passes for the
  WRONG reason (the C1 parse-error-instead-of-assert trap).
- FIXTURES DISCRIMINATE: TWO principals (A≠B) for the binding; a hostile secret-shaped value for the
  leak pin; a `'`/`;`/`DELETE`-laden string for injection (bound-param proof + a table-survives
  positive control); a distinct expiry FUTURE control for the expiry seam.
- The reach pin's coverage is a CHECKED variable (`test_a_synthetic_new_governed_tool_would_red_the_
  coverage` proves a growing governed set reds it) — not a hand-list trusted blind.
- The 61 live PDP oracle (`loremaster/tests/test_pdp_oracle_61b.py`) is the load-bearing §5
  instrument and must stay GREEN; the reach file's signature guards red a 62 build that touches the
  PDP before the oracle would.
