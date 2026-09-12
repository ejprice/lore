# REPORT — adversary2-63b-ii-a (MANDATORY re-run contract-adversary, packet 63b wave ii-a, message WRITE side)

`brief-base v14 read`
`contract-adversary role read`
`brief project v7 read`
store-ref read (`docs/reference/surrealdb-31-capabilities.md`): §1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS) · §1.4 (option<> on populated tables) · §2 (CONTENT / protected `session` param / bound RecordID owner links / `SELECT *` omits NONE) · §4.F/ENFORCED. Cited, not re-transcribed.

## SUMMARY BLOCK (brief-base §1)

- **VERDICT: CONTRACT SUFFICIENT.** The revised RED contract at `4b5a9de` is satisfiable by a correct build with **NO contract-line correction** and every rider I wrong-built discriminates its named build. The predecessor's two BLOCKERs (MP-1 C-DEF, MP-2 unflagged corpse) are **CLOSED**; MP-3/MP-4 are **addressed** by the ruling + revision.
- **P1 headline — did any wrong build survive?** NO. Every constructed wrong build for the revision's risk surface (WB-2/R1, WB-guarded/R2+R6, WB-routing/R4, WB-MP3 agent-leg) went RED for the right reason. No wrong build passed.
- **Satisfiability receipt:** whole-feature reference (all §4.A/C/D/F + SF-63-1 + R1–R8 + the lifts) in provenance-asserted scratch (`loremaster.__file__ = /tmp/.../scratchpad/ref/loremaster/loremaster/__init__.py`, verified twice) → **88 passed / 0 failed** (85 ii-a + 3 cross-file MP-2/F-A). NO MP-1-style C-DEF this pass. Harder leg: ruff clean (zero fixes); mypy needed 2 trivial annotation fixes in `governed.py` (a PRODUCTION file, never a contract file) → the 5 contract files stay **85/0** after the cleanup.
- **QUANTIFIER TABLE (P1b):** full table below — every invariant classified; the two previously-guarded rows (message-leg ambiguity, tokenless-send owner) are now ∀/pinned.
- **REACH TABLE (P1c):** full table below — the capability-routing coverage is now DERIVED + coverage-checked + EFFECT-keyed (R6 closes the F-D proxy leg); resolve_principal / resolve_operator_principal are now MUTATION-proven (R4/MP-3), not structural-only.
- **F-MP3-SCOPE — RESOLVED empirically:** the message leg MUST consult `resolve_operator_principal` (a get_by_key-only leg fails the BACKFILL test — the fixtures don't pre-mint the project keep, so the leg must be able to mint it). The ambiguity pin is NOT over-constraining.
- **MISSING PINS:** none that make a wrong build pass. Residuals (non-blocking) below: R-WIRE (wrapper threading, disclosed → 63b-iii), R-ALPHA (tokenless-register render unpinned in the 5 files → test_comms_promise_registry).
- **FINDING for the lead (D1 effort):** the reviser's corpse inventory **UNDERSTATES the register corpse.** `test_comms_tool.py` → **139 failed / 785 passed** on the reference; register sites break on `self._principal_store` (the fake AppContext is a `SimpleNamespace`), NOT "mostly GREEN." ANY correct build breaks register-on-fakes (the ruled `resolve_principal` path reads `self._principal_store`). D1 is bigger than estimated. Decision-needed.
- **Packages considered:** none — no NEW mechanism specified; the reference implements the ruled design (lifts are extractions of existing code; identity resolution is against the repo's own stores).
- **Reuse ledger:** none — an adversary reference ships no reusable production symbol; it reuses the landed i-a F5 substrate (`_governed_contract`) UNTOUCHED and the design's ruled lifts.
- **Graded:** `4b5a9de` · HEAD-at-report: `4b5a9de` · SAME (`git rev-parse HEAD`; `a4eb097` is an ancestor and the only production delta a4eb097→4b5a9de is a 1-line PLR0915 silence in a probe SCRIPT — no `loremaster/` production changed, so the RED-at-HEAD base equals the predecessor's).
- **decisions-needed:** **D1-CORPSE** (register corpse understated — re-estimate the ii-a D1 fake-seam effort: credential-the-fake for REGISTER, not just send) · **R-ALPHA** (confirm the tokenless-register α render line is pinned somewhere before ii-a closes — it is NOT in the 5 ii-a files).
- **receipt POINTERS:** §Satisfiability · §Predecessor-finding closure · §Per-rider door-builds · §REACH · §QUANTIFIER · §F-MP3-SCOPE · §Corpse spot-check · §Residuals.

## Capability check (brief-base §4)
- Demanded: re-grade the revised RED contract; BUILD the whole-feature satisfiability reference; run wrong builds for R1–R8 + MP-1..4 + F-MP3-SCOPE; REACH/QUANTIFIER tables; corpse spot-check. HAVE: full tool access, lore MCP loaded, live TEST store `:18000` up, `scripts/scratch_copy.sh` (provenance-asserting). All satisfiable.
- **`grep`/`rg` are HOOK-BLOCKED in this checkout** ("lore main checkout is live-indexed" — it rejects any `grep`, even inside a pipe, even in the scratch copy). Used lore (`lore_get_symbol`/`lore_search`/`lore_read`) + `Read` + `awk`/`sed` for every structure query and log filter — SAID here per the dogfood protocol. No lore-tool friction (lore served every query cleanly), so nothing filed to `lore_findings`.
- Attribution: the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by the operator's standing `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY — the lead commits).

---

## Satisfiability reference (I own it — the reviser deferred it again, the sanctioned deviation)

Built a CORRECT whole-feature reference for the ruled design in a provenance-asserted scratch
(`./scripts/scratch_copy.sh`; `--verify-only` re-run clean). The build recipe is three re-runnable
patch scripts (`apply_reference{,2,3b}.py` in the session scratchpad — disposable by design, so the
per-file diff below IS the durable record; each script asserts every anchor matched exactly once).

**Reference production diff (by file · symbol · what) — the ruled design, §5/§7:**

| file | symbol | change |
|---|---|---|
| `governed.py` | `resolve_principal` (NEW) | lifted from `resolve_subject` step (2): token→admitted `Principal | None` (None iff no subject; DENY iff presented-but-unadmitted). §3.1 |
| `governed.py` | `resolve_write_scope` (NEW) | lifted grant seam: `None→default`, else `pdp._grantable` else `GovernedDenied`. Pure (caller resolves default). §4.A |
| `governed.py` | `resolve_subject` | step (2) → `principal = await resolve_principal(...)`; `if principal is None or not email: DENY`. R4 structural. |
| `memory/local.py` | `_resolve_write_scope` | now a CALLER of `governed.resolve_write_scope` (default resolved LAZILY when scope is None). §4.A/§6 ONE IMPL. |
| `store/surreal_schema.py` | `_message_statements` | §4.F: `+= _governed_field_specs()` + `_governed_index_statements(MESSAGE_TABLE)`. Grows populations to {memory,message,to}. |
| `messages.py` | `send` / `_send_fragment` | thread optional `owner_principal`/`owner_agent`/`scope` into the CREATE CONTENT (owner links bound `RecordID`, store-ref §2). |
| `principals.py` | `resolve_operator_principal` (NEW) | THE operator (single principal / single admin), `None` on ambiguity. ONE IMPL, all 3 legs call it. §4.C/§2.1 |
| `principals.py` | `_owner_count` (NEW), `_migrate_agent_owner` (NEW), `_migrate_message_owner` (NEW) | §4.C legs (governed_exempt frames); `_migrate_memory_scope` → CALLER of the lift; `migrate_governed` dispatch wires agent+message. |
| `server.py` | `CommsActionSpec.requires_capability` (NEW field) | typed applicability; send spec `requires_capability=True` + `capability` in `params`. §4.D/RULING §4 |
| `server.py` | `comms` / `_comms_register` / `_comms_send` / `_render_comms_register` | `capability=` seam; register resolves principal + mints session keep + foreign gate + owner stamp + R7 credential line; send enforces identity (unconditional `_resolve_subject`, agent≡subject, keep-by-key, explicit-scope lift, `write_guard("send")` + 3 stamps). §2.3/§3.1/§4.A |

**Receipts:**
- `85 passed / 0 failed` on the 5 ii-a files (`-n auto`, live `:18000`), **with NO contract-line patched** (contrast the predecessor: the shipped contract was RED on a correct build at MP-1 until one line was corrected — that C-DEF is fixed).
- `3 passed / 0 failed` on the 2 cross-file pins (`test_governed_migration_63a.py::TestTheAgentFirstOrderIsChecked` MP-2 + `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput` F-A).
- Combined re-run on the restored clean reference: **88 passed / 0 failed**.
- **Harder leg:** `uv run ruff check` on the 6 changed production files AND the 5 contract files → *All checks passed* (zero `--fix`). `mypy` on the reference reported exactly 2 errors, both in `governed.py` (`no-any-return` on `resolve_write_scope`; `arg-type` on `resolve_visible_keeps(member_email=...)`) — trivial annotation narrows in a PRODUCTION file; after the fix, `governed.py` is mypy-clean and the 5 contract files re-run `85 passed`. No cleanup a correct build demands touches a contract file.

---

## Predecessor-finding closure (each verified, without regressing the strong instruments)

- **MP-1 (BLOCKER / C-DEF) — CLOSED.** The pin now reads the sender AGENT's stored `owner_principal` from the store (not the non-existent `Agent.owner_principal` attribute). Satisfiable on a correct build (green in the 85). It discriminates a NONE/unstamped owner and a re-stamp of an already-owned message (the `_effect_migrate_message` unit + the store-read compare). ⚠ *Note (not a defect):* in the single-operator `message_world`, `sender.owner_principal == operator`, so MP-1 cannot distinguish "stamp sender.owner" from "stamp operator" — but under the §2.1 single-operator precondition every agent is owned by the one operator, so the two are EQUIVALENT in every migratable state; there is no observable wrong build between them.
- **MP-2 (BLOCKER / unflagged corpse) — CLOSED.** The 63a fixture now registers a genuine NONE-owner agent (`ag_legacy_none_owner`), so the §2.6 agent-first precondition is NON-vacuous on a correct §4.C build. `TestTheAgentFirstOrderIsChecked` → GREEN on the reference (the reference's `_migrate_message_owner` REFUSES agent-first with a real NONE-owner agent present, rather than proceeding into a `TxnDomainRejectionError` on an absent table).
- **MP-3 (message-leg ambiguity + routing) — ADDRESSED and discriminating.** The agent-leg value-mutation (`test_the_operator_resolution_is_shared_by_mutation`) + the message-leg ambiguity refuse (`test_message_migrate_refuses_on_multi_principal_ambiguity`) + the structural route pin all pass on the reference AND all RED the routing-not-sharing wrong build (below).
- **MP-4 (tokenless-send owner under-specified) — CLOSED by the ruling.** Q1 fixes the owner to the subject's pair and a tokenless send DENIES (writes nothing). R1 pins owner EXACTNESS, so the live-classify's non-None owner is no longer a false clear — WB-2 (stamp the keeper) now REDS R1 (the exact wrong build the predecessor's reference demonstrated as *passing*).
- **Strong instruments NOT regressed:** the DDL route-emitter file (`test_message_governed_ddl_63b_ii_a.py`) is byte-unchanged since the predecessor and passes on the reference; the population-growth derivation yields exactly {memory, message, to} (F-A pin green); the site-derivation deny-by-default pins pass.

---

## Per-rider discrimination (P1 door-builds — every wrong build ran in the provenance-asserted scratch)

| rider | pin | wrong build (door) | result |
|---|---|---|---|
| **R1** owner exactness | `test_a_credentialed_send_stamps_exactly_the_subjects_pair` | **WB-2**: `owner_principal = session_keep.keeper_id` (Reading A) | **RED** — got `principal:p4im…` (keeper alice) ≠ `principal:2h01…` (sender bob). Positive control: A's own send stamps A (green on reference). |
| **R2** tokenless send denies + 0 rows | `test_a_tokenless_send_denies_and_creates_no_message_row` | **WB-guarded** (F-D door): `if capability is not None:` around the enforcement; send stamps None when absent | **RED** — DID NOT RAISE + a row was written. Anti-vacuity inverted (zero observed creates) confirmed non-vacuous. |
| **R4** ONE derivation | `TestThePrincipalResolutionIsSharedByMutation` + structural twin | **WB-routing**: `_comms_register` reads `self._principal_store.get_by_email(subject)` directly (private copy) | **RED** on BOTH — value-mutation (patch `resolve_principal`→P*; the minted keep keeper does NOT move) + structural (`function_calls_named(_comms_register, resolve_principal)` fails). |
| **R6** ∀ True-verb no-cap deny | `test_send_without_a_capability_denies` | **WB-guarded** (same F-D door) | **RED** — DID NOT RAISE (anti-vacuity leg confirms the True-set ⊇ {send} first). |
| **MP-3** operator resolution shared | `test_the_operator_resolution_is_shared_by_mutation` + route pin | **WB-MP3**: `_migrate_agent_owner` hand-rolls the operator resolution | **RED** on BOTH — value-mutation (patched operator P* ignored) + structural route pin. |
| **R3** keeper exactness | `test_register_mints_the_session_keep_kept_by_the_registrants_principal` (+ foreign-deny + positive control) | (not separately wrong-built) | **GREEN on reference** (keeper == alice, `!= carol`). The `!= carol` leg structurally REDS Reading A (keeper=admin); the same keeper-vs-registrant machinery is wrong-built at R1/WB-2. |
| **R5** send-half grant flip | `test_a_sender_removed…denied_at_send` + `test_perturbing_the_lifted_seam_changes_send` | (mutation test IS the discriminator) | **GREEN on reference** — the perturb-seam test itself proves routing (permissive seam → removed-member send SUCCEEDS only if routed; positive control DENIES). |
| **R7** credential served once | `test_a_first_register_serves_the_capability_once…` + no-leak | (HEAD is the never-serve build) | **GREEN on reference** — first serves the exact `<name>:<secret>` (verifies under the owner token), re-register does not, fleet/heartbeat never do. RED-at-HEAD is the never-serve door. |
| **R8** owner_agent==sender | `_effect_send_message` unit (`wrong_owner` case) + live-classify | (reject-case built INTO the pin) | **GREEN on reference** — the unit's `wrong_owner` delta (owner_agent ≠ sender) is REJECTED; the live-classify classifies a real credentialed send whose owner_agent IS the sender. |

Legs run: WB-2, WB-guarded, WB-routing, WB-MP3 are EMPIRICAL door-builds (RED reproduced with real output). R3/R5/R7/R8 pass on the reference with their own reject-cases/mutation-legs built into the pins (discrimination is by construction; I did not additionally hand-build a separate wrong build for each — SAID).

---

## REACH TABLE (P1c) — every guard/scan classified

| instrument (introduced ‡ / relied-on) | reach DERIVED? | coverage a checked variable? | effect vs proxy? | one-source-by-mutation? | leg | verdict |
|---|---|---|---|---|---|---|
| DDL route-through-emitter ‡ | yes (patches shared `_governed_field_specs`) | n/a (single seam) | EFFECT | YES (predecessor WB-1) | construction (file unchanged) | SAFE |
| population growth (`governed_populations`) | yes (AST over `surreal_schema` for `_governed_field_specs` CALLERS + relation endpoints) | YES (`test_the_population_set_is_an_OUTPUT_not_a_hand_list` grows on synthetic source) | EFFECT | n/a | EMPIRICAL (green; F-A pin green) | SAFE |
| deny-by-default site coverage | yes (whole-tree AST from workspace members) | YES (`test_the_send_sites_are_derived_and_covered` anti-vacuity) | EFFECT | n/a | construction | SAFE |
| live send-classify (`observe_governed_table_writes`) ‡ | reach = the query_raw door | anti-vacuity present (`assert creates`) | EFFECT (WB-3 label-only reds; owner effect now pinned by R1/R8, no longer non-None-only) | n/a | EMPIRICAL (green on reference) | **SAFE — MP-4 closed** |
| capability routing coverage ‡ (`test_every_capability_verb_handler_resolves_the_subject`) | yes (verb set from `_COMMS_ACTIONS`, keyed on `requires_capability`) | YES (True-set derived; R6 anti-vacuity) | AST-presence FLOOR **+ R6 EFFECT leg** (behavioural no-cap deny) | n/a | EMPIRICAL (WB-guarded reds R6) | **SAFE (F-D proxy door CLOSED by R6)** |
| `resolve_principal` lift ‡ (R4) | n/a | n/a | EFFECT (send owner + keep keeper both move under mutation) | **YES** — WB-routing reds value-mutation + structural | EMPIRICAL | **SAFE (MUTATION-proven, no longer structural-only)** |
| `resolve_operator_principal` lift (MP-3) | n/a | n/a | EFFECT (agent-leg stamp moves under mutation) | **YES** — WB-MP3 reds value-mutation + structural | EMPIRICAL | **SAFE (MUTATION-proven; predecessor's structural-only gap closed)** |
| `resolve_write_scope` lift (R5) | n/a | n/a | remember EFFECT + send EFFECT (both halves flip) | YES (both mutation proofs pass; a private copy stays put) | EMPIRICAL | **SAFE (send-half now exercised — predecessor's R3 residual closed)** |

## QUANTIFIER TABLE (P1b) — every invariant classified

| invariant | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| every governed field option<>/OVERWRITE/no-ASSERT | ∀ over the 3 columns | green on reference (§4.F wiring) |
| governed reads IndexScan | ∀ over read predicates + C+ controls | green (DDL file unchanged) |
| population set == {memory, message, to} | ∀ via derivation (grows on synthetic input) | green; F-A i-a pin green (coupling correct) |
| every derived message/to site ∈ allowlist | ∀ whole-tree derived (deny-by-default) | green; anti-vacuity present |
| classifier runs the effect predicate ∀ label frame | ∀ (label leg RUNS effect) | green; WB-3 (label-only) reds |
| **send message owner == subject's pair** | **∀ (R1 owner exactness)** | **WB-2 reds** (predecessor's guarded/non-None-only row is now ∀) |
| send message owner_agent == sender | ∀ (R8 structural leg) | unit `wrong_owner` rejected |
| tokenless send DENIES, writes nothing | ∀ over identity-absence (R2) | WB-guarded reds |
| every requires_capability verb denies without one | ∀ over the True-set (R6, derived) | WB-guarded reds |
| migrate agent backfills ∀ NONE-owner, never re-stamp | ∀ (MIX fixture) | green on reference |
| migrate agent/message REFUSE on multi-principal ambiguity | ∀ over both legs (agent + **message**) | **message-leg pinned now** (predecessor's MP-3 gap closed); WB-MP3 reds routing |
| migrate message REFUSES before agents migrated | ∀ count>0 (1-agent AND 2-agent fixtures) | green (predecessor's count==1 softness hardened) |
| ONE derivation (Q1 owner + Q2 keeper same seam) | ∀ (R4 mutation) | WB-routing reds |

---

## F-MP3-SCOPE — the reviser's flag, answered EMPIRICALLY

The reviser asked: *does a correct `_migrate_message_owner` actually consult `resolve_operator_principal` for the project keep? If not, the ambiguity pin over-constrains.*

**Answer: it MUST, and the pin does NOT over-constrain.** I built the alternative — a message leg that reads the project keep by `keep_store.get_by_key(PROJECT_KEEP_KEY)` and refuses if absent (no operator resolution). It **REDS the BACKFILL test** (`test_message_migrate_backfills_owner_from_sender_and_scope_to_project_keep`): `message_world` does NOT pre-mint the project keep (it migrates neither memory nor agent), so a read-by-key leg finds nothing and refuses → cannot backfill. Because migrate legs are independent CLI invocations with no memory-before-message order (§2.6 orders only agent-before-message), a correct message leg must be able to MINT the project keep on its own → must resolve the keeper → must call `resolve_operator_principal`. Its ambiguity is therefore a legitimate refuse, and the ambiguity pin (which reds the read-by-key leg's project-keep-absent reason) is correct, not over-constraining. My reference's message leg consults it and passes all pins.

---

## Corpse-inventory spot-check (brief-mandated) — a MATERIAL understatement

Ran `test_comms_tool.py` (the reviser's claimed 39 send + 20 register fake-harness sites) against the reference: **139 failed / 785 passed**. The cause on a register site (`TestRegisterAction::test_reregister_says_re_registered_not_registered`): `AttributeError: 'types.SimpleNamespace' object has no attribute '_principal_store'` at `_comms_register`'s `governed.resolve_principal(get_access_token(), principal_store=self._principal_store)`.

- **Claimed-breaking SEND sites — CONFIRMED break** (as the reviser predicted): the fake harness has no `_principal_store`/`_keep_store`, so an enforced send cannot run — credential-the-fake is required.
- **Claimed-GREEN REGISTER sites — the inventory is WRONG.** The reviser's table B said `test_comms_tool.py` register sites are "mostly setup registers → GREEN; only a byte-exact render pin → render update." Empirically they are broadly **RED**: the ruled `_comms_register` reads `self._principal_store` BEFORE the reading-α decision, so EVERY register-then-do test on the `SimpleNamespace` fake AttributeErrors. This is not a property of my reference — ANY correct build must call `resolve_principal(get_access_token(), principal_store=self._principal_store)` (the structural route pin requires it). So the register corpse is as broad as the send corpse, and the 139-failure blast radius (register-setup cascading into drain/ack/fleet/brief tests) is the real D1 cost.
- **Consequence (decision-needed D1-CORPSE):** the ii-a D1 fake-seam reconciliation must credential-the-fake for REGISTER (add `_principal_store` + `_keep_store` + a `get_access_token` setup to `_comms_fakes.py`), not just for `send`. The reviser's D1 estimate ("~40 send sites + a subset of register render pins") is understated by ~100 sites. This does NOT change the contract's SUFFICIENCY (the 5 ii-a files use the real store and pass) — it is a builder-effort / wave-placement input the lead needs before granting D1.

---

## Residuals (individual verdicts — nothing waved)

- **R-WIRE (residual, disclosed):** the FastMCP `lore_comms` wrapper (`server.py`, the `return await _app_context(context).comms(...)` site) does NOT thread `capability=` to `AppContext.comms` in my reference (only the handler dispatch does). The contract author DISCLOSED this (`test_comms_capability` docstring: "the FastMCP wrapper threads it… pinning the dispatch signature is the seam-level contract"). A builder could pass all 5 ii-a files with a wire that never delivers a capability. Known bound → 63b-iii's wire battery. Not an ii-a blocker; the ii-a contract pins `AppContext.comms`'s signature only, deliberately.
- **R-ALPHA (residual, decision-needed):** the tokenless-register α render line (ruling §3.2) is NOT pinned in any of the 5 ii-a files — the ruling routes it to `test_comms_promise_registry.py`, outside my run set. A build could ship a broken/absent α line and pass the 5 files. Confirm it is pinned before ii-a closes.
- **MP-1 single-operator equivalence (note, not a defect):** covered above — sender.owner ≡ operator under §2.1, so no observable wrong build between "stamp sender.owner" and "stamp operator."
- **Already-decided, not re-litigated (no contradiction found):** F-DUP (per-file harness duplication — lead-accepted for ii-a); the 41-site corpse reconciliation as the builder's GREEN-phase job (operator D1); the RED-contract pytest orphan window. I found no contradiction with these — the only correction is the D1 register-corpse SIZE (above).

---

## Method / discipline receipts
- Store law read FIRST (brief step 3): store-ref §1.1/§1.4/§2/§4.F cited, not re-transcribed. The `RecordID` owner-link binding follows `AgentRegistry.register`'s existing practice.
- lore-first for structure: `lore_get_symbol`/`lore_search`/`lore_read`/`lore_verify` for every production symbol (`resolve_subject`, `stamp_owner`, `_verify_capability_owner`, `AgentRegistry.register`, `AppContext.{comms,_comms_register,_comms_send,_resolve_subject,_render_comms_register}`, `CommsActionSpec`/`_COMMS_ACTIONS`, `LocalMemoryBackend._resolve_write_scope`, `KeepStore.{get_or_create_keyed,add_household_member}`, `resolve_visible_keeps`, `pdp.{keep_scope,_grantable}`, `MessageLedger.{send,_send_fragment}`, `_migrate_memory_scope`, `migrate_governed`, `governed_populations`, `_message_statements`/`_governed_field_specs`/`_governed_index_statements`, `write_guard`). grep hook-blocked → `awk`/`sed`, SAID. No lore friction filed (lore served every query cleanly).
- Provenance asserted (#140): `scratch_copy.sh` + `loremaster.__file__` inside the copy, re-verified with `--verify-only`. Every wrong build ran in the same provenance-asserted scratch, restored from a `cp -a` content backup between builds.
- Controls per "a probe needs a control": every wrong-build RED paired with the correct-build GREEN (the reference) + the pin's own positive control (WB-2's A-stamps-A; R2's credentialed control writes one row; R4/MP-3's unpatched positive controls).
- COMMIT-ONLY honoured: no production/contract edits in the MAIN tree; the only MAIN-tree write is this report. All builds in SCRATCH. Git untouched — the lead commits.

**VERDICT: CONTRACT SUFFICIENT.** The revised contract is satisfiable by a correct build with no contract-line correction; every rider discriminates its named wrong build; the predecessor's blockers (MP-1, MP-2) are closed and its softer findings (MP-3 message-leg ambiguity + routing, MP-4 owner exactness, R3/R5/R7 residuals) are addressed and mutation/behaviour-proven. The one material item for the lead is a BUILDER-EFFORT correction, not a contract defect: the D1 register corpse is ~100 sites larger than the reviser's inventory states.
