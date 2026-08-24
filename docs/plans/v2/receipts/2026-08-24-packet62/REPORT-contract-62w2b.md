# REPORT-contract-62w2b — packet 62 Wave 2 CONTRACT REVISION (ESC-1: relocate `stamp_owner` home)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: not re-consulted — this revision touches NO store/schema/DDL surface
  (it moves ONE symbol's *home* pin from `lorerunes` to `loremaster` in a test file; the DDL,
  migration, and store idioms the wave-2 contract pins are UNCHANGED and stay as `contract-62w2`
  cited them by §).

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: the three wave-2 test files, the ruling doc, and the
prior report were readable; lore tools loaded via `ToolSearch "+lore"` and I registered on
`lore_comms` (session `packet62`, role `contract-author`); spike-surreal test store
`ws://127.0.0.1:18000` was `active` (systemd) so the live-store pins ran; ruff / `scripts/typecheck.sh`
/ `pytest -n auto` all ran. No impossibilities, no partial capability.

---

## SUMMARY BLOCK
- **State:** done. Single targeted revision applied to `test_agent_capability_seams.py` ONLY:
  `stamp_owner`'s HOME pin relocated `lorerunes` → `loremaster` per ESC-1's operator ruling (doc
  v5). All other pins (parse_credential, and every behavioral/security/reach/mechanism pin) STAND
  exactly as `contract-62w2` wrote them.
- **RED count coherent:** `52 failed, 11 passed` at HEAD `e34cf47` (spike-surreal `:18000`) —
  **identical total** to the prior contract's 52/11. The seams file contributes 17 RED
  (8 parse + 4 DRY + 5 stamp_owner). The relocated pin REDs **behaviorally**
  (`AssertionError: loremaster.stamp_owner is unbuilt` — `assert None is not None`), not a
  collection error.
- **Node-id delta (exactly ONE):**
  `…::TestStampOwnerSeam::test_stamp_owner_exists_in_lorerunes` →
  `…::TestStampOwnerSeam::test_stamp_owner_exists_in_loremaster_not_lorerunes`. The declared
  expected-RED set must adopt this one-line change (see §"Declared expected-RED delta"). Every
  other node id in `contract-62w2`'s declared set is unchanged.
- **Isolation confirmed (the brief's STOP condition did NOT fire):** the relocation touched NO
  behavioral/security pin's assertion. The signature is UNCHANGED (`registry=` injected, isolated
  in `_call_stamp_owner`), so `returns_the_verified_owner_pair`, both `fail_closes_*`, and
  `routes_through_verify_capability` are byte-for-byte behaviorally identical — only the symbol
  they resolve moved package. The revision is fully isolated to the home/purity pins.
- **Packages considered:** none — no mechanism specified (this is a test-only home relocation; it
  hand-rolls nothing and pins reuse exactly as the prior contract did).
- **Reuse ledger:** none — no new production reusable symbol introduced.
- **Graded:** n/a — contract author; renders no verdict on another agent's artifact. `git rev-parse
  HEAD` = `e34cf47`; the wave-2 test files are untracked in the working tree (this revision edits
  only `test_agent_capability_seams.py`).
- **Decisions-needed:** **none blocking.** ONE preserved-decision NOTE (not a fork): the
  `stamp_owner` CALL SIGNATURE keeps the injected `registry=` param (the ruled doc's shorthand
  signature omits how stamp_owner obtains a registry; injection is the only form satisfiable
  against the per-test unique DB — see §"Signature note"). Surfaced, not silently resolved.
- **Receipt pointers:** the diff §"The revision (exact edits)"; RED receipt §"RED→verify receipt";
  node delta §"Declared expected-RED delta"; the signature reasoning §"Signature note".

---

## The ruling this implements
`docs/design/2026-08-24-packet62-agent-identity-rulings.md` (v5, committed):
- **Changelog note (top, lines ~11–16):** "ESC-1 (stamp_owner home) RULED **loremaster, NOT
  lorerunes** (overriding the (A) lean — lorerunes is cross-member-only + predicates-not-entry-
  points; corrected R1.1/scope-line/W2.6)."
- **R1.1 (corrected):** "it lives in `loremaster`, NOT `lorerunes`. … (1) the lorerunes
  entry-criterion is CROSS-MEMBER policy, and BOTH consumers … are `loremaster` … = a shared
  `loremaster` module; (2) it is I/O-ORCHESTRATION, not a general predicate … (#222). Only the
  GENERAL pure predicate `parse_credential` … qualifies for `lorerunes`."
- **W2.6 split:** "general pure predicates (`is_blank`, `parse_credential`) → `lorerunes`;
  store-reading orchestration (`stamp_owner`, `resolve_agent`) → `loremaster`."
- **Scope-line item 3:** "The ONE shared `stamp_owner(...)` seam in **`loremaster`** (ESC-1
  correction — it orchestrates a store read; `lorerunes` holds only the pure `parse_credential`
  predicate)."

## The revision (exact edits — `test_agent_capability_seams.py` only)
Six surgical edits, all confined to the `stamp_owner` home + the lorerunes-purity leg:

1. **Module docstring — ESC-1 block rewritten** from the prior "spec is INTERNALLY INCONSISTENT …
   I pin reading (A)" escalation to a RULED record: `stamp_owner` lives in `loremaster` (the two
   W2.6/R1.1 reasons), `parse_credential` stays in `lorerunes`, and the location pin asserts only
   the PACKAGE surface `loremaster.stamp_owner` (builder chooses the module). This removes the
   stale reading-(A) prose (P8d rendered-prose class — leaving "I pin (A) [lorerunes]" after the
   ruling would be a stale-prose defect).
2. **Imports + RED-until-built resolution:** added `import loremaster`; the module-level symbol
   `_lorerunes_stamp_owner = getattr(lorerunes, "stamp_owner", None)` became
   `_loremaster_stamp_owner = getattr(loremaster, "stamp_owner", None)` (dynamic getattr keeps the
   typecheck gate green at HEAD, same technique the prior contract used). Comment updated: only
   `parse_credential` → `lorerunes`; `stamp_owner` → `loremaster`.
3. **LEG-2 header comment:** "Signature pinned per ESC-1 reading (A)" → "Home RULED `loremaster`
   (ESC-1); call signature UNCHANGED".
4. **`_call_stamp_owner` helper:** symbol reference renamed to `_loremaster_stamp_owner`; assert
   message now names `loremaster.stamp_owner`. **The call is byte-identical** —
   `_stamp_owner(token, capability, registry=env.registry)` (registry injected, unchanged).
5. **`_assert_stamp_owner_fail_closed` guard:** the unbuilt-guard assert renamed to
   `_loremaster_stamp_owner` + message updated.
6. **The LOCATION/existence pin** `test_stamp_owner_exists_in_lorerunes` →
   `test_stamp_owner_exists_in_loremaster_not_lorerunes`, now a TWO-LEG location pin:
   - leg A: `assert _loremaster_stamp_owner is not None` (PRESENT at the loremaster package
     surface) — the leg that REDs at HEAD (unbuilt);
   - leg B: `assert getattr(lorerunes, "stamp_owner", None) is None` (ABSENT from lorerunes —
     stamp_owner is no longer a lorerunes symbol). This is the brief's "if a pin says lorerunes
     contains stamp_owner, it must now assert lorerunes does NOT" — the lorerunes-purity invariant
     is preserved and, because a symbol left it, STRENGTHENED. (A wrong build that put stamp_owner
     in `lorerunes` reds leg B; one that put it nowhere reds leg A.)

`parse_credential` LEG 1 is **untouched**: it STAYS `getattr(lorerunes, "parse_credential", None)`
and `test_parse_credential_exists_in_lorerunes` and all four ONE-implementation identity/mutation
pins stand verbatim.

## Why the location pin uses the PACKAGE surface (not a private module path)
The brief mandated "pin the loremaster IMPORT surface the way the contract pins other loremaster
seams, not a hard-coded private path; the exact module is the BUILDER's choice." The faithful
analog: the OTHER relocated seam (`parse_credential`) is pinned at its OWNING package's top level
(`getattr(lorerunes, "parse_credential", None)`), and `lorerunes/__init__.py` re-exports at package
level (`from lorerunes import is_blank`). So `stamp_owner`'s owning package is now `loremaster`, and
the source-side location pin is `getattr(loremaster, "stamp_owner", None)` — package surface, not a
private module. This keeps the defining module the builder's choice while giving the shared seam
(63/64 CALL it — Fork 4) a stable public address. Cost: the builder adds ONE re-export line to the
(currently empty) `loremaster/__init__.py`; the defining module is theirs. Satisfiable by a correct
build. (A hard-coded `loremaster.<module>.stamp_owner` pin was rejected: it removes the builder's
module choice and is the "hard-coded private path" the brief forbids.)

## Signature note (a PRESERVED decision, surfaced — NOT a new fork)
The ruled doc shows `stamp_owner(access_token, agent_capability) -> (owner_principal, owner_agent)`
(R1.1 / scope-line item 3) — a shorthand that omits HOW stamp_owner obtains the `AgentRegistry` it
must call `verify_capability` on. The prior contract (reading A) injected the registry
(`registry=env.registry`), isolated in `_call_stamp_owner`. I KEPT that injection, for a hard
satisfiability reason: the live-store behavioral pins register an agent in a **per-test
`unique_database()`** bound to `seam_env.registry`; a `stamp_owner` that constructs its own registry
from default config could not see that agent, so those pins would be unsatisfiable. Registry
injection is therefore the ONLY form a correct build can take, and the pin correctly forces it. This
is not a new ambiguity my relocation introduced — the operator ruled the HOME and did not re-open the
signature/wiring; the prior author explicitly isolated the signature in `_call_stamp_owner` so a
future signature ruling stays a one-function edit. Flagged here so the adversary/builder see the
decision rather than infer it. If the operator DOES want a registry-less `stamp_owner` signature,
`_call_stamp_owner` (this file only) is the single edit point.

## RED→verify receipt (HEAD `e34cf47`, spike-surreal `ws://127.0.0.1:18000`)
- All three wave-2 files, `pytest -n auto`: **`52 failed, 11 passed in 8.16s`** (unchanged total).
- Seams file alone: **`17 failed`** (8 `TestParseCredentialBehaviour` + 4
  `TestParseCredentialIsTheONEImplementation` + 5 `TestStampOwnerSeam`).
- Relocated pin isolated:
  `…::test_stamp_owner_exists_in_loremaster_not_lorerunes` → `1 failed`, reason
  `AssertionError: loremaster.stamp_owner is unbuilt … assert None is not None` (behavioral RED,
  correct reason).
- Gates: `uv run ruff check` (three wave-2 files) → `All checks passed!`; `bash scripts/typecheck.sh`
  → all members OK (import ordering `import loremaster` before `import lorerunes` accepted by isort).

## Declared expected-RED delta (for whoever maintains the expected-RED set / pending_contracts)
`contract-62w2`'s declared 52-node expected-RED set is unchanged EXCEPT this one line:

```
- tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_exists_in_lorerunes
+ tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_exists_in_loremaster_not_lorerunes
```

The seams-file RED set is now (17 nodes; the changed node marked ✎):
```
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
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_exists_in_loremaster_not_lorerunes    ✎ (was …_exists_in_lorerunes)
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_returns_the_verified_owner_pair
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_fail_closes_on_a_binding_mismatch
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_fail_closes_on_an_absent_or_garbage_credential
tests/test_agent_capability_seams.py::TestStampOwnerSeam::test_stamp_owner_routes_through_verify_capability
```
The 35 RED nodes in `test_agent_capability.py` + `test_agent_capability_reach.py` are unchanged
(see `REPORT-contract-62w2.md` §"Declared expected-RED"), and the 11 GREEN guards/positive-controls
are unchanged.

## Out-of-writable-set flags (raised, not edited — §2 scope law)
- **The prior report's declared expected-RED list** (`REPORT-contract-62w2.md`, and any
  `scripts/mutation_proof.py` / `scripts/pending_contracts.yaml` entry that transcribes it) carries
  the retired node id `…test_stamp_owner_exists_in_lorerunes`. It needs the one-line update above.
  Not in my writable set; flagged for the lead to apply where the set is durably kept.
- **`test_agent_capability.py:7`** (docstring) names "the shared seams (`stamp_owner` /
  `resolve_agent` / `parse_credential`) live in `test_agent_capability_seams.py`" — this is a
  pointer to which TEST FILE the pins live in, NOT a production-module (lorerunes/loremaster)
  location claim, so it is NOT stale and needs no edit. Noted so the lead need not re-check it.
