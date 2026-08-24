# REPORT-contract-62w2c — packet 62 Wave 2 CONTRACT REVISER (the 2 adversary-found fixes)

- `brief-base v14 read`
- `brief project v7 read`
- store reference: no store/schema/DDL change made (tests-only revision); the two fixes touch a
  regex helper and add a live-store admission pin. `docs/reference/surrealdb-31-capabilities.md`
  cited, not re-transcribed, only where the pins already reference it (§1.1/§1.8 for the index).

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: the contract file
`loremaster/tests/test_agent_capability.py` was writable; the live spike-surreal test store
`ws://127.0.0.1:18000` (never :18500) was up and every live-store pin ran; `ruff` /
`scripts/typecheck.sh` / `pytest -n auto` all ran; lore tools loaded via `ToolSearch "+lore"`;
registered on `lore_comms` (session `packet62`, role `contract-author`). No impossibilities.

---

## SUMMARY BLOCK
- **State: done.** The exactly-2 adversary-found fixes are in; nothing else touched.
- **Graded:** n/a — I authored, I did not grade. (Base sha for the edit: HEAD `6b180f0`, the same
  commit the adversary graded; `git merge-base --is-ancestor 6b180f0 HEAD` → SAME.)
- **FIX 1 (C-DEF):** `_index_statement_over`'s field regex `\s*$` → `\b` — a one-token change +
  expanded docstring. Empirically verified: the correct `… FIELDS capability_hash UNIQUE`
  emission now matches, the plain-index positive control still matches, and
  `capability_hash_extra` does NOT match (exact-field semantics preserved). The 3
  `TestTheCapabilityHashUniqueIndex` pins are now SATISFIABLE on a correct build and STILL RED at
  HEAD (field absent).
- **FIX 2 (ownerless deny):** added `test_an_ownerless_agents_capability_is_denied` to
  `TestVerifyCapabilityAdmission` — ownerless mint → cap presented under alice's AND bob's foreign
  tokens → DENY; positive control: an OWNED agent's cap under its OWN token RESOLVES. RED at HEAD
  (behavioral, `verify_capability` absent — not a collection break).
- **RED count:** all 3 contract files at HEAD `6b180f0` = **53 failed / 11 passed** (was 52/11 →
  **prior 52 + 1** = my new ownerless pin). Per-file RED: `test_agent_capability.py` 33 ·
  `_reach.py` 3 · `_seams.py` 17. Full node-id set in §"Declared expected-RED set" below.
- **Gates:** `ruff check` clean · `scripts/typecheck.sh` clean (all 7 members + shellcheck) ·
  collection whole (36 tests in the file, +1 vs prior 35).
- **Isolation:** neither fix touched a behavioral pin, implementation, the design doc,
  `_reach.py`/`_seams.py`, or any other file. Diff = 44 insertions / 2 deletions, one file.
- **Reuse ledger:** none — no new reusable symbol (the new pin reuses `_verify_capability`,
  `_register_owned`, `_token`, `getattr`).
- **Packages considered:** none — no mechanism specified (tests-only revision).
- **Decisions-needed:** none. Both fixes were contract-author fixes, not operator forks, exactly
  as the adversary graded.
- Receipt pointers: diff → §"The exact diff"; regex proof → §"FIX 1"; RED proof → §"Verification";
  full RED set → §"Declared expected-RED set".

---

## FIX 1 — C-DEF: `_index_statement_over` `\s*$` → `\b` (the unsatisfiable UNIQUE-index pins)

**Root cause (adversary MISSING PIN 1):** the helper the three `TestTheCapabilityHashUniqueIndex`
pins depend on anchored the field at `\s*$`:

```python
and re.search(rf"FIELDS\s+{field}\s*$", statement, re.IGNORECASE)   # required statement to END at the field
```

A correct build emits the UNIQUE index through the shared `_unique_index` emitter as
`… FIELDS capability_hash UNIQUE` — ` UNIQUE` follows the field, so `\s*$` never matches, so
`_index_statement_over` returns `None` and all three pins stay RED on a correct build (C-DEF: a
declared-RED pin that cannot go green on the intended build).

**The fix (verbatim to the brief):** `\s*$` → `\b`. A word boundary matches BOTH a plain index
that ends at the field AND a UNIQUE index where ` UNIQUE` follows, while still requiring the WHOLE
field token.

**Empirical verification (isolated regex control — the receipt, re-runnable):**

```python
import re
correct_unique = "DEFINE INDEX IF NOT EXISTS agent_capability_hash ON agent FIELDS capability_hash UNIQUE"
plain_index    = "DEFINE INDEX IF NOT EXISTS agent_owner_principal ON agent FIELDS owner_principal"
compound       = "DEFINE INDEX IF NOT EXISTS x ON agent FIELDS capability_hash_extra"

# CURRENT (broken $-anchor): rf"FIELDS\s+capability_hash\s*$"
#   correct UNIQUE index matches?          -> False   ← the C-DEF (unsatisfiable)
#   plain index (owner_principal) matches? -> True
#   capability_hash_extra matches?         -> False
# FIXED (\b word-boundary): rf"FIELDS\s+capability_hash\b"
#   correct UNIQUE index matches?          -> True    ← now satisfiable
#   plain index (owner_principal) matches? -> True    ← positive control preserved
#   capability_hash_extra matches?         -> False   ← exact-field token still required
```

Both checks the brief demanded pass: the correct UNIQUE index matches AND the plain-index positive
control still matches; the `_extra` negative control confirms `\b` did not weaken exact-field
matching. What the three pins ASSERT (emitted / UNIQUE / IF-NOT-EXISTS-never-OVERWRITE) is
UNCHANGED — only the helper's field-boundary regex moved.

**Satisfiability, cross-checked:** the adversary's reference build (a known-correct build authored
off `6b180f0`) took these three pins to 3-pass with exactly this `\s*$`→`\b` change
(`REPORT-adversary-62w2.md` §"MISSING PIN 1", "Fix proof"). At HEAD they remain RED because
`capability_hash` is absent from the DDL (verified below), so the C-DEF is closed without
introducing a false-green.

## FIX 2 — the ownerless-agent capability deny (adversary MISSING PIN 2)

**Root cause (adversary MISSING PIN 2):** the binding pin
(`test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token`) and the
owner-active pins only ever register OWNED agents (`owner_bare=alice_bare`) — a parameter-value
monoculture on owner-PRESENCE. The contract itself sanctions ownerless agents
(`test_register_without_a_credential_is_ownerless_not_fabricated`: `register(owner_principal_id=None)`,
the Fork-2 pre-cutover loopback fleet), and such an agent still mints a capability on create
(W2.3). A build treating a NONE owner as permissive in cond 3 AND cond 4 (two idiomatic
`if owner_x is not None and owner_x != …: deny` guards) resolves that ownerless capability under
ANY foreign principal's token — the confused-deputy hole §3.2 exists to close. The adversary
reproduced this LIVE (`30b3735f…` returned under bob's token) and it passed the whole contract.

**The pin (added to `TestVerifyCapabilityAdmission`):**
- register an OWNERLESS agent (`owner_bare=None`) that mints a capability;
- present that capability under alice's token → assert `None`; and under bob's token → assert
  `None` (∀ principals: a NONE owner is never a wildcard, fail-closed binding W2.2 cond 3);
- **POSITIVE CONTROL leg:** an OWNED agent's capability under its OWN token resolves to its agent
  id — so the pin discriminates deny-for-ownerless from accept-for-owned, not "denies everything".

**Discrimination is grounded, not asserted:** the adversary's live two-idiom None-permissive build
resolved the ownerless cap under bob's token (`REPORT-adversary-62w2.md` §"MISSING PIN 2") — that
is exactly the build my first `is None` assert reddens, while a correct build (cond 3
`owner_principal is None → deny`) passes it and resolves the owned positive control. The delta
adversary re-grades the full deny/accept discrimination after me (per my brief).

**RED at HEAD is behavioral, not collection:** the pin's first line is
`verify = _verify_capability(cap_env)` → `getattr(env.registry, "verify_capability", None)` → `None`
at HEAD, so `assert verify is not None` reds BEFORE `_register_owned` is reached (no TypeError
masking). Confirmed in the run below.

## The exact diff

```
loremaster/tests/test_agent_capability.py | 46 ++++++++++++++++++++++++++-- (44 insertions, 2 deletions)
```

- `_index_statement_over`: `re.search(rf"FIELDS\s+{field}\s*$", …)` → `re.search(rf"FIELDS\s+{field}\b", …)`
  + docstring expanded to state why `\b` (matches plain-end AND UNIQUE-follows, still whole-token).
- `TestVerifyCapabilityAdmission`: new `test_an_ownerless_agents_capability_is_denied` inserted
  after `test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token` (its
  ownerless-binding twin), reusing `_register_owned` / `_verify_capability` / `_token`.

## Verification (receipts)

**Ruff:** `uv run ruff check loremaster/tests/test_agent_capability.py` → `All checks passed!`

**Typecheck:** `bash scripts/typecheck.sh` → all members OK
(`lorerunes`/`lorescribe`/`loresigil`/`loremaster`/`skills`/`docs/eval`/`scripts` + shellcheck).

**Collection whole:** `pytest --collect-only -q` → `36 tests collected` (prior 35 + the new pin);
`test_an_ownerless_agents_capability_is_denied` collects cleanly (no import collapse).

**C-DEF pins RED-at-HEAD (satisfiable-by-fix, still red because field absent):**
```
uv run pytest -n auto …::TestTheCapabilityHashUniqueIndex -q
  E  assert None is not None      (test_agent_capability.py:300)
  3 failed in 5.98s   (emitted / UNIQUE / IF-NOT-EXISTS_never_OVERWRITE — all RED)
```

**All 3 contract files at HEAD `6b180f0`:**
```
uv run pytest -n auto test_agent_capability.py test_agent_capability_reach.py test_agent_capability_seams.py -q
  53 failed, 11 passed in 8.05s
```
Prior (62w2 adversary): 52 failed / 11 passed. Delta = **+1 RED** = the new ownerless pin (verified
present in the RED set). Per-file RED: 33 / 3 / 17.

**The new pin is in the RED set (grep of the FAILED lines):**
`…::TestVerifyCapabilityAdmission::test_an_ownerless_agents_capability_is_denied` — present, count 1.

## Declared expected-RED set (full, for the adversary / mutation_proof / pending_contracts.yaml)

53 node ids, derived mechanically from the FAILED lines of the 3-file run at HEAD `6b180f0` (not
transcribed by eye). The set is the prior 62w2 declared-RED set **plus exactly** the one new node
`loremaster/tests/test_agent_capability.py::TestVerifyCapabilityAdmission::test_an_ownerless_agents_capability_is_denied`.

`test_agent_capability.py` (33):
```
TestCapabilityLifetimeIsLifecycleScopedNotAClockTtl::test_a_capability_whose_optional_expiry_is_in_the_past_is_denied
TestCapabilityLifetimeIsLifecycleScopedNotAClockTtl::test_a_capability_with_no_expiry_is_not_time_gated
TestMintInRegister::test_first_register_returns_a_raw_capability_once
TestMintInRegister::test_re_register_does_not_rotate_a_live_secret
TestMintInRegister::test_the_raw_secret_is_never_persisted_as_a_readable_column
TestMintInRegister::test_the_stored_hash_is_sha512_of_the_whole_returned_credential
TestRegisterStampsOwnerPrincipalFromTheCredential::test_register_exposes_no_display_owner_argument
TestRegisterStampsOwnerPrincipalFromTheCredential::test_register_stamps_owner_principal_from_the_server_derived_id
TestRegisterStampsOwnerPrincipalFromTheCredential::test_register_without_a_credential_is_ownerless_not_fabricated
TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_is_emitted
TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_is_option_string
TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_is_OVERWRITE
TestTheCapabilityHashFieldDdl::test_the_capability_hash_field_routes_through_the_shared_emitter
TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_emitted
TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_IF_NOT_EXISTS_never_OVERWRITE
TestTheCapabilityHashUniqueIndex::test_the_capability_hash_index_is_UNIQUE
TestTheCapabilityNeverLeaksOntoTheAgentValueObject::test_a_secret_shaped_value_never_appears_in_a_rendered_agent
TestTheOptionalCapabilityExpiresSeam::test_the_capability_expires_field_is_emitted_as_option_datetime
TestVerifyCapabilityAdmission::test_a_forged_capability_without_the_secret_is_denied
TestVerifyCapabilityAdmission::test_an_expired_owning_principal_denies_the_capability
TestVerifyCapabilityAdmission::test_an_ownerless_agents_capability_is_denied          ← NEW (FIX 2)
TestVerifyCapabilityAdmission::test_a_retired_agents_capability_is_denied_next_call_no_cache
TestVerifyCapabilityAdmission::test_a_suspended_owning_principal_denies_the_capability
TestVerifyCapabilityAdmission::test_a_valid_capability_under_its_owners_token_resolves_the_agent
TestVerifyCapabilityAdmission::test_the_binding_denies_a_valid_capability_under_a_DIFFERENT_principals_token
TestVerifyCapabilityRidesTheSharedQuerySeam::test_verify_capability_routes_through_agent_registry_query
TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank]
TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank-halves]
TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank-name]
TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[blank-secret]
TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[no-colon]
TestVerifyCapabilityUniformDenyNoOracle::test_a_malformed_credential_denies_uniformly[whitespace]
TestVerifyCapabilityUniformDenyNoOracle::test_an_injection_laden_credential_is_a_bound_param_not_interpolated
```
`test_agent_capability_reach.py` (3):
```
TestTheGovernedSurfaceReachPin::test_a_synthetic_new_governed_tool_would_red_the_coverage
TestTheGovernedSurfaceReachPin::test_every_governed_tool_is_pending_owner_stamp_and_adjudicated
TestTheNonWiringGuardDocstringIsUpdated::test_the_module_docstring_acknowledges_the_owns_edge
```
`test_agent_capability_seams.py` (17):
```
TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank]
TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank-halves]
TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank-name]
TestParseCredentialBehaviour::test_a_malformed_credential_is_none[blank-secret]
TestParseCredentialBehaviour::test_a_malformed_credential_is_none[no-colon]
TestParseCredentialBehaviour::test_a_malformed_credential_is_none[whitespace]
TestParseCredentialBehaviour::test_a_well_formed_credential_splits_on_the_first_colon
TestParseCredentialBehaviour::test_parse_credential_exists_in_lorerunes
TestParseCredentialIsTheONEImplementation::test_agents_references_the_lorerunes_parse
TestParseCredentialIsTheONEImplementation::test_breaking_the_shared_parse_denies_PrincipalKeyStore_verify
TestParseCredentialIsTheONEImplementation::test_breaking_the_shared_parse_denies_verify_capability
TestParseCredentialIsTheONEImplementation::test_principal_keys_references_the_lorerunes_parse
TestStampOwnerSeam::test_stamp_owner_exists_in_loremaster_not_lorerunes
TestStampOwnerSeam::test_stamp_owner_fail_closes_on_a_binding_mismatch
TestStampOwnerSeam::test_stamp_owner_fail_closes_on_an_absent_or_garbage_credential
TestStampOwnerSeam::test_stamp_owner_returns_the_verified_owner_pair
TestStampOwnerSeam::test_stamp_owner_routes_through_verify_capability
```

## Scope / isolation
- Both fixes are ISOLATED — neither forced touching a behavioral pin, so no STOP/escalate was
  needed. FIX 1 changed only the offline helper's regex + docstring; FIX 2 added a new pin reusing
  existing helpers. Every other pin (binding-for-owned, mint-once, no-leak, DRY-mutation, forgery,
  no-cache, ESC-3 enforced-when-set, the reach pin, stamp_owner-in-loremaster, resolve_agent
  fail-closed) is byte-unchanged.
- Nothing outside the writable set (`loremaster/tests/test_agent_capability.py` +
  `REPORT-contract-62w2c.md`) was touched. `_reach.py` / `_seams.py` / implementation / design doc
  untouched. No git state mutated (the lead commits).

## VERDICT
The exactly-2 adversary-found fixes are in and verified: the C-DEF index pins are now satisfiable
on a correct build (still RED at HEAD), and the ownerless cross-principal door is pinned with a
discriminating positive control. RED count 52 → 53 (the one new pin), gates green, isolation
clean. Ready for the focused adversary delta re-grade.
