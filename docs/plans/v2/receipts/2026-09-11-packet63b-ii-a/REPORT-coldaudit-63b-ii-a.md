# REPORT — coldaudit-63b-ii-a (packet 63b wave ii-a, message WRITE side — COLD AUDIT / REFUTE)

`brief-base v14 read` · `brief project v7 read` · store-ref read
(`docs/reference/surrealdb-31-capabilities.md`): §1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS —
ALTER is a trap), §1.4 (option<> on a POPULATED table, no ASSERT/DEFAULT), §1.6 (the virgin-DB blind
spot that hid #107), §2 (bound RecordID owner links; protected `session`; SELECT * omits NONE), §4
(RELATE ENFORCED / dangling-edge guard) — cited, not re-transcribed.

## Capability check (brief-base §4)
- Demanded: independently re-run all gates ALONE; REFUTE the build by mutation in a provenance-asserted
  scratch; the DUAL corpse adjudication; served-string honesty; #107 dirty-store; the 18 regressions;
  R-WIRE; a RESIDUAL table. HAVE: full tool access, lore MCP loaded, live TEST store `:18000` up,
  `scripts/{typecheck.sh,scratch_copy.sh,pending_contract_gate.py}`, `uv run ruff/pytest`. All satisfiable.
- **`grep`/`rg` are HOOK-BLOCKED** (confirmed — a bare `grep` is rejected). Used lore
  (`lore_get_symbol`/`lore_search`) + `Read` + `awk`/`git show|awk` for every structure/diff sweep. SAID.
- **lore MCP store (:18500) dropped the websocket 4× during the audit** ("no close frame received or
  sent" on lore_index/lore_search/lore_get_symbol/lore_findings). Retried; fell back to Read+awk for a
  few structure queries (SAID). Filed **lore finding #463**. Not a build defect.
- Attribution: the session-start `Co-Authored-By`/`Claude-Session` reminder is overridden by the
  operator's standing `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY — I touch no git).

## SUMMARY BLOCK (brief-base §1)
- receipt: `brief-base v14 read` · `brief project v7 read` · store-ref read · idle-gate contract written.
- **VERDICT: GO.** The build at `eafb8fd` is faithful to the owner-resolution ruling on every axis
  probed; every load-bearing pin DISCRIMINATES its wrong build by construction (7/7 mutation proofs
  RED); the corpse reconciliation PRESERVED coverage (0 assertions removed). No CONFIRMED defect.
- state: **done**
- deviations: none. COMMIT-ONLY honoured — my only main-tree write is this report; all mutation ran in
  a provenance-asserted scratch copy (`loremaster.__file__` INSIDE the copy, printed below).
- **Packages considered:** none — no mechanism specified (auditor). The two mutation instruments
  (`mut_offline.sh`, `mut_store.py`) are pasted VERBATIM in the Appendix (brief-base §1 — an instrument
  establishing a load-bearing claim is a deliverable; the scratchpad is disposable).
- **Reuse ledger:** none — auditor, no new production symbols introduced.
- **Graded:** `eafb8fd` · HEAD-at-report: `eafb8fd` · SAME (`git rev-parse HEAD` == graded sha; main
  tree clean, only untracked pre-existing reports/artifacts).
- decisions-needed: none blocking. Residuals R4 (builder count 18 vs 17) and R5 (stray repo-root
  artifacts) are lead FYIs; R1/R2/R3 are ruled/benign bounds with named triggers.
- receipt POINTERS: §Gates · §Mutation proofs · §DUAL · §Served-strings · §#107 · §Regressions ·
  §R-WIRE · §RESIDUAL TABLE · §Appendix (instruments).

---

## §Gates — independently re-run ALONE at `eafb8fd`
| gate | command | result |
|---|---|---|
| full suite | `uv run pytest -n auto` (run ALONE) | **11223 passed, 51 skipped, 3 xfailed, 0 failed, 0 errors** (349.59s) |
| mypy | `./scripts/typecheck.sh` | **Success — all members** (lorerunes/lorescribe/loresigil/loremaster/skills/docs-eval/scripts + shellcheck); zero errors incl. test trees |
| ruff | `uv run ruff check .` | **All checks passed!** |
| currency | `uv run python scripts/pending_contract_gate.py --currency` | **PASS** — manifest `(typecheck, ruff, pytest)`; typecheck GREEN · ruff GREEN · pytest GREEN; **0 RED_ORPHANED** (read the actual CURRENCY line, not a piped exit) |

The full suite passed-COUNT is in the pasted tail (`11223 passed … in 349.59s`) — not a silent "no tests
ran". The currency gate's pytest leg is itself a 2nd independent full run (junit-xml). Reproduces the
builder's 11223/0/0 and CURRENCY PASS claims. The FIRST run's spurious store-contention E-pattern the
brief warns of did NOT occur (I ran the suite alone; fleet at rest).

## §Mutation proofs — REFUTE by construction (7/7 DISCRIMINATE)
All in `scripts/scratch_copy.sh`-built scratch; **provenance asserted** —
`loremaster.__file__ = …/scratchpad/scratch-audit/loremaster/loremaster/__init__.py` (INSIDE the copy,
#140). Each: break a load-bearing seam → run the targeted node → confirm the intended pin REDS →
`git checkout` restore. Clean restore verified (no modified tracked files). Instruments in Appendix.

| # | mutation (the wrong build) | targeted pin | result |
|---|---|---|---|
| M1 | `governed.resolve_principal`: `getattr(token,"subject",None)` → `token.subject` direct | `test_comms_send_scope…::TestResolvePrincipalReturnsNoneForAnIdentitylessToken::test_a_none_token…` | **RED** (AttributeError on None) ✓ |
| M6 | `_define_field`: `OVERWRITE` → `IF NOT EXISTS` | `test_message_governed_ddl…::…::test_the_governed_field_is_OVERWRITE_not_if_not_exists` | **RED** (all 3 cols) ✓ |
| M4 | `_message_statements`: drop `_governed_field_specs()` wiring | `test_message_enforcement…::TestTheGovernedPopulationSetGrows` + DDL emitted-pin | **RED** (both) ✓ |
| M2 | `_comms_send`: neuter `agent_row.id != subject.agent_id` | `test_comms_send_scope…::TestTheAgentArgumentMustMatchTheCapability` (MP-5) | **RED** ✓ |
| M3 | `_comms_register`: Reading-A hybrid `resolve_principal(...) or resolve_operator_principal(...)` on the tokenless branch | `test_comms_send_scope…::TestATokenlessRegisterIsOwnerlessAndMintsNoKeep` (MP-6) | **RED** (fabricated owner/keep) ✓ |
| M5 | `_migrate_agent_owner`: hand-roll operator resolution (clone) | `test_message_migrate…::test_the_operator_resolution_is_shared_by_mutation` + structural route pin | **RED** (both) ✓ |
| M7 | `governed.resolve_write_scope`: `if not pdp._grantable(...)` → `if False` (permissive) | `test_comms_send_scope…::…::test_a_sender_removed_from_the_session_household_is_denied_at_send` (R5) | **RED** ✓ |

Each store test carries its OWN positive control (matching-capability send writes 1 row; unpatched
migrate stamps the real operator) and reddened as `failed`, not `error` — genuine discriminating REDs,
not store-contention. M3 is the exact wrong build ruling §11.2 MP-6 named (fabricates the fleet admin
on the tokenless branch). M5 catches ROUTING-IS-NOT-SHARING (a leg calling the seam but hand-rolling
the decision).

## §Production faithful to the ruling (read at `eafb8fd`, cited)
- `governed.resolve_principal` (`governed.py:124`) — `getattr` guard + `if not email: return None` at the
  SEAM (both None and `""`, no store lookup — §3.1 / D-NULLTOKEN); presented-but-unadmitted → DENY. ✓
- `governed.resolve_subject` (`governed.py:179`) step (2) now `= await resolve_principal(...)` — R4 ONE
  derivation. ✓  `resolve_write_scope` (`governed.py:156`) — `None→default`, else `pdp._grantable` else DENY. ✓
- `_comms_send` (`server.py:7116`) — UNCONDITIONAL `_resolve_subject(capability)` FIRST; `agent_row.id !=
  subject.agent_id` deny (MP-5); keep-by-key + "register first" deny; `resolve_write_scope(subject,
  session_keep_scope, default=session_keep_scope)` (explicit, non-None → R5 grant runs every send);
  `write_guard("send")` around `message_ledger.send(owner_principal=…, owner_agent=…, scope=…)`. ✓
- `_comms_register` (`server.py:6616`) — `resolve_principal(get_access_token(), …)`; α branch (principal
  None → no keep, `owner_principal_id=None`); `get_or_create_keyed("session:<s>", keeper_email=…)` + SF-63-1
  foreign gate via `resolve_visible_keeps` BEFORE `register` (#97 — denied register writes no row). ✓
- `messages._send_fragment` (`messages.py:941`) — owner_principal/owner_agent bound as
  `RecordID(PRINCIPAL/AGENT, …)` links, scope a string; CONTENT always NAMES the columns, each NONE when
  absent (option<>, legacy sends stay unstamped); reads use explicit projections. ✓
- `surreal_schema._message_statements` (`:1710`) — `+= _governed_field_specs()` (OVERWRITE, option<>,
  no ASSERT via `_define_field`) + `+= _governed_index_statements` (plain IF NOT EXISTS, scope +
  owner_principal; owner_agent NOT indexed); `to` edge stays OVERWRITE ENFORCED. Via the SHARED emitters
  (route-through-emitter mutation-pinned). ✓
- `principals.{resolve_operator_principal,_migrate_agent_owner,_migrate_message_owner}` — 1-admin-else-
  1-principal-else-None; agent-first refuse (count>0); golden `UPDATE … WHERE owner_principal IS NONE`
  byte-matching `_MIGRATE_MESSAGE_GOLDEN`; all three legs call the shared `resolve_operator_principal`
  (lines 1151/1282/1374); `governed_exempt("migrate-governed")`. ✓

## §DUAL — removed-behaviour adjudication (corpse ~140 sites tokenless→credentialed)
- **0 removed `assert`/`raises`/`pytest.fail`/`.assert_` lines** across ALL test files in the build diff
  (`git show eafb8fd -- 'loremaster/tests/*.py' | awk …`). Removed lines by file: test_comms_tool.py
  **126**, _comms_fakes.py 3, test_comms_waiting_line.py 4, render_architecture 1, await 1 — and **none
  contain `assert`**. Sampled: every removal is a DRIVE/SETUP (imports, harness construction, `register`,
  tokenless `AppContext.comms(action="send")`), replaced by the shared credentialed `_send`/`_credential_agent`
  seam. No recipient-set, receipt, drain/ack, teach, or skew assertion dropped. **Coverage preserved.**
- The 2 "wrong-reason→right-reason" fixes RESTORE coverage: `TestUnregisteredRecipientIsTheEXISTINGTeachingError`
  keeps a TYPED `pytest.raises((UnknownAgentError, UnknownRecipientError))` and drives credentialed, so
  the recipient check is genuinely reached (previously a broad `raises(Exception)` could swallow a prior
  identity deny). Not gutting.
- **`FakeMessageLedger.send` ignoring owner stamps is genuinely PRESERVED-WITH-PIN, not a coverage hole:**
  the `Message` READ model returned by the real `MessageLedger.send` carries NO owner columns (verified in
  `messages.py:666` — the returned `Message(...)` has no owner_* fields), so the fake modelling nothing is
  correct; the live owner stamp is pinned on the REAL store by R1
  (`test_a_credentialed_send_stamps_exactly_the_subjects_pair`, reads `owner_principal/owner_agent/sender`).

## §Served-string honesty (P8d class)
- The reading-α OWNERLESS render line (`_render_comms_register`, `server.py:7531`) DERIVES its deny-verb
  set from `_COMMS_ACTIONS` (`requires_capability=True`), NOT a hand-list — INSTRUMENT 0 (a new True verb
  joins automatically). Names ownerless ("no owning principal") + the derived verbs + both remedies
  ("credential", "migrate-governed"). Driven live GREEN by MP-6; M3 confirms the bound-naming assert
  discriminates the fabricating build.
- R7 credential line served IFF `capability is not None` (first register only; re-register mints none);
  no-leak on fleet/heartbeat pinned (`test_no_other_comms_render_carries_a_credential`).

## §#107 dirty-store
- Fields `DEFINE FIELD OVERWRITE` (M6 proves the IF-NOT-EXISTS build reds); indexes plain `IF NOT EXISTS`
  (OVERWRITE would rebuild → boot crash, §1.1); governed columns `option<>` with NO ASSERT/DEFAULT (§1.4 —
  a required field/DEFAULT poisons legacy rows). owner links `RecordID` (store-ref §2); `to` edge OVERWRITE
  `TYPE RELATION … ENFORCED` intact (`test_the_to_relation_edge_survives_as_an_enforced_relation`). The
  option<>-does-not-poison-a-legacy-row property is pinned live in `test_governed_migration_63a::
  TestTheOptionColumnsDoNotPoisonTheLegacyRow`; the migrate `message_world` seeds a real NONE-owner message
  then backfills it (a populated-table exercise). See RESIDUAL R1 for the one uncovered shape.

## §The 18 in-scope regressions (all pure ADDITIONS — 0 removed lines in the 3 files)
- `test_principal_keys_schema.py` (+9) — ADDS `("owner_principal", MESSAGE_TABLE)` to the exact-set
  `record<principal>` cascade gate, classified LIVE-DEPENDENCY with delete-disposition DEFERRED + a named
  re-open trigger, **mirroring `memory.owner_principal` exactly**. The gate still asserts `found == expected`
  → a surprise link still reds. **Sound PIN-THE-MISS, not a silenced gate.** ✓
- `test_link5_render_containment.py` (+29) — ADDS 3 probe shapes for `_render_comms_register`'s 3 new
  branches (SF-63-1 keep minted/joined, α bound, R7 credential) → branch-reach stays a CHECKED variable;
  classifies the *handler* `_comms_register` as `store_backed` (its served render is the driven
  `_render_comms_register`). Not a coverage drop. ✓
- `test_comms_register_notice.py` (+6) — adds present-but-`None` `_principal_store`/`_keep_store` the α
  path never dereferences. ✓
- Cross-file pins re-run GREEN: `test_governed_migration_63a.py` (MP-2 agent-first refuse) +
  `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput` ({memory,message,to}) —
  **220 passed** with the 3 regression files (independent focused run).
- ⚠ Count note (R4): the builder's prose says "18 in-scope regressions" but enumerates 14+2+1 = **17**.
  Harmless (all green) — flagged per the re-derive-inherited-numbers law.

## §R-WIRE (early close)
`server.py::_register_tools` threads `capability: Annotated[str|None]` → the `comms` dispatch →
`_comms_send` (`capability=capability`). Forced by `test_param_honesty__every_spec_param_is_in_the_tool_signature`
once `send`'s spec declares `capability`. **Benign forward progress:** the dispatch-level behavior is
pinned (MP-5 agent≡subject, R6 deny-without-capability, R7 credential-once); the wrapper→dispatch hop is
covered STRUCTURALLY (param-honesty). The full register→send-over-the-wire behavioral battery and the
≥2×≥2 agent≡capability matrix remain **63b-iii's** (ruling B2/B4) — R-WIRE does NOT preempt them, and
introduces no *unpinned* new behavior (only the thin wire hop, structurally pinned). No finding.

## §RESIDUAL TABLE (file:line + individual verdict — "all remaining are X" is banned)
| # | where | observation | verdict |
|---|---|---|---|
| R1 | `store/surreal_schema.py::_message_statements` (§4.F) | No test applies the PRE-63b message DDL → seeds a row → applies the §4.F DDL, to prove the governed columns ADD cleanly on a POPULATED table. Live proof is virgin-apply (LEG 2) + string OVERWRITE pin (M6) + the migrate `message_world` + the 63a option-poison pins. | **BENIGN.** For BRAND-NEW `option<>` columns the #107 changed-field-noop trap is structurally unreachable and §1.4 poison is guarded by option<>. **Re-open trigger:** the first CHANGE to a governed message column's definition (then OVERWRITE's runtime migration needs a live dirty-store pin). Low severity. |
| R2 | `server.py::_register_tools` (FastMCP `lore_comms` wrapper) | `capability=` wrapper→dispatch threading is pinned STRUCTURALLY (param-honesty), not end-to-end over the wire. | **BENIGN / RULED.** The end-to-end wire battery is 63b-iii (ruling B4); dispatch behavior is already pinned. No action. |
| R3 | `test_comms_send_scope_63b_ii_a.py::TestTheAgentArgumentMustMatchTheCapability` | ONE agent≡capability mismatch case in ii-a; the ≥2×≥2 matrix is deferred. | **SOUND DEFERRAL** (ruling §9 B2) — the equality check is BUILT + pinned in ii-a; iii widens the matrix. |
| R4 | `REPORT-builder-63b-ii-a.md` §In-scope regressions | "18 in-scope regressions" prose vs enumerated 14+2+1 = 17. | **COSMETIC** un-derived-count inconsistency; all pass. Lead FYI (re-derive-numbers law). |
| R5 | repo root | Pre-existing untracked `test_*.memory.db` (×4) + a `resume` file, present at session start (not from this build or my audit). | **HYGIENE / UNRELATED.** Per CLAUDE.md the root must be cleared of `REPORT-*.md` (git mv → `docs/plans/v2/receipts/…`) before the pkt-65 image build; the stray `.db`/`resume` clutter should be swept too. Lead FYI. |
| R6 | lore MCP store `:18500` | Dropped the websocket 4× during the audit ("no close frame received or sent"). | **DOGFOOD FRICTION**, filed **#463**. Not a build defect; monitor for idle-box recurrence (would indicate a router/store bug vs contention). |

## §Discipline receipts
- Store law: no store/schema/DDL change made by this audit; the §4.F review cites store-ref §1.1/§1.4/§4,
  not re-transcribed.
- Tree provenance: all mutation in `scripts/scratch_copy.sh`-asserted scratch (`loremaster.__file__` printed
  INSIDE the copy). Main tree left byte-clean; HEAD unchanged `eafb8fd`; COMMIT-ONLY honoured.
- lore-first: symbols via `lore_get_symbol`/`lore_search`; fell back to Read+awk on the 4 :18500 WS drops
  and for the git-diff sweeps (grep hook-blocked) — SAID, filed #463.
- Every number here was measured this session (gate tails, mutation results, `awk` diff counts, the 17-vs-18
  re-derivation); none inherited unverified.

---

## Appendix — mutation instruments (VERBATIM, brief-base §1)

### `mut_offline.sh` (no-store: M1, M6, M4)
```bash
#!/usr/bin/env bash
set -u
S=…/scratch-audit ; cd "$S"
GOV=loremaster/loremaster/governed.py ; SCH=loremaster/loremaster/store/surreal_schema.py
run_node(){ uv run pytest -p no:cacheprovider -q "$1" 2>&1 | tail -3; }
restore(){ git checkout -- "$@"; }
# M1 D-NULLTOKEN: '    email = getattr(access_token, "subject", None)' -> '    email = access_token.subject'
#    node: test_comms_send_scope_63b_ii_a.py::TestResolvePrincipalReturnsNoneForAnIdentitylessToken::test_a_none_token_resolves_to_none_without_consulting_the_store  => RED (AttributeError)
# M6 OVERWRITE->IF NOT EXISTS in _define_field's returned DEFINE FIELD string
#    node: test_message_governed_ddl_63b_ii_a.py::TestGovernedColumnsAreEmittedOnMessage::test_the_governed_field_is_OVERWRITE_not_if_not_exists  => RED (3 cols)
# M4 delete the '_governed_field_specs()' comprehension appended in _message_statements
#    nodes: test_message_enforcement_63b_ii_a.py::TestTheGovernedPopulationSetGrows::test_message_and_to_join_the_derived_population_set  => RED
#           test_message_governed_ddl_63b_ii_a.py::TestGovernedColumnsAreEmittedOnMessage::test_the_governed_field_is_emitted_as_option_wrapped  => RED
# each mutation applied via python str.replace, run_node, then restore.
```

### `mut_store.py` (store: M2, M3, M5, M7) — the load-bearing driver, verbatim
```python
# provenance-asserted; per mutation: str.replace on the SCRATCH file -> run targeted node
# against TEST store :18000 -> assert "failed" in tail -> git checkout restore.
# M2  SRV _comms_send: "if agent_row.id != subject.agent_id:" -> "if False:  # M2 neutered"
#     node test_comms_send_scope…::TestTheAgentArgumentMustMatchTheCapability::test_a_send_with_a_siblings_capability_denies_and_writes_nothing  => RED
# M3  SRV _comms_register: after `principal = await governed.resolve_principal(get_access_token(), principal_store=self._principal_store)`
#     insert `if principal is None: from loremaster.principals import resolve_operator_principal; principal = await resolve_operator_principal(self._principal_store)`
#     node test_comms_send_scope…::TestATokenlessRegisterIsOwnerlessAndMintsNoKeep::test_a_tokenless_register_succeeds_ownerless_mints_no_keep_and_names_the_bound  => RED
# M5  PRIN _migrate_agent_owner (leg-specific): "operator = await resolve_operator_principal(principal_store)"
#     -> inline `_ps_list = await principal_store.list(); _adm=[p for p in _ps_list if p.role==_ROLE_ADMIN]; operator=_adm[0] if len(_adm)==1 else (_ps_list[0] if len(_ps_list)==1 else None)`
#     nodes test_message_migrate…::TestResolveOperatorPrincipalIsLifted::test_the_operator_resolution_is_shared_by_mutation  => RED
#           …::test_all_three_migrate_legs_route_through_resolve_operator_principal  => RED
# M7  GOV resolve_write_scope: "if not pdp._grantable(subject, scope):  # noqa: SLF001 - the ruled shared grant predicate" -> "if False:  # M7 permissive"
#     node test_comms_send_scope…::TestSendResolvesTheSessionKeepScope::test_a_sender_removed_from_the_session_household_is_denied_at_send  => RED
# RESULT: all RED (discriminating); git status --short after restore == clean (no modified tracked files).
```
Full runnable copies live in the session scratchpad
(`…/scratchpad/{mut_offline.sh,mut_store.py}`); the anchors above reconstruct them exactly.
