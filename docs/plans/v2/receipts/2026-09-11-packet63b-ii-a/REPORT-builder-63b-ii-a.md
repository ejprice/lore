# REPORT — builder-63b-ii-a (packet 63b wave ii-a, message WRITE side)

`brief-base v14 read` · `brief project v7 read` · store-ref read
(`docs/reference/surrealdb-31-capabilities.md`): §1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS —
ALTER is a trap), §1.4 (option<> on a POPULATED table, no ASSERT/DEFAULT), §2 (CONTENT / bound
RecordID owner links / protected `session` / explicit projection reads NONE as None / SELECT *
omits NONE) — cited, not re-transcribed.

## Capability check (brief-base §4)
- Demanded: build the ruled production (adversary reference diff) to make the 5 ii-a contract files
  + 2 cross-file pins GREEN; reconcile the corpse to a GREEN full suite; register the α promise line.
  HAVE: full tool access, lore MCP loaded, live TEST store `ws://127.0.0.1:18000` up,
  `scripts/typecheck.sh`, `uv run ruff/pytest`. All satisfiable.
- **`grep`/`rg` are HOOK-BLOCKED** in this live-indexed checkout (confirmed repeatedly — a bare
  `grep` and even `grep` inside an `awk` pipe are rejected). Used lore
  (`lore_get_symbol`/`lore_search`/`lore_read`) + `Read` + `awk`/`sed` for every structure query.
  SAID per the dogfood protocol. No lore-tool friction — every query served cleanly, nothing filed.
- Attribution: the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by
  the operator's standing `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY — the lead commits).

## SUMMARY BLOCK (brief-base §1)
- receipt: `brief-base v14 read` · `brief project v7 read` · store-ref read · idle-gate contract
  written (`/tmp/claude-idle-gate-lore/387b7f9e-…-builder-63b-ii-a.contract`).
- **state: done** — the ruled production is built; the 5 ii-a contract files + 2 cross-file pins are
  GREEN; the ENTIRE corpse is reconciled; **the FULL suite is GREEN (11223 passed / 0 failed / 0
  errors, run ALONE)**; mypy + ruff clean. Currency gate: see §Gates-currency.
- deviations:
  1. **R-WIRE closed early (in the good direction, forced by an existing pin).** The adversary
     residual R-WIRE deferred threading `capability=` through the FastMCP `lore_comms` wrapper to
     63b-iii. But `test_comms_tool.py::test_param_honesty__every_spec_param_is_in_the_tool_signature`
     asserts every `_COMMS_ACTIONS` spec param is an MCP-visible wrapper param — so adding `capability`
     to send's `spec.params` REQUIRED adding the `capability` Annotated param to the wrapper. Done;
     this CLOSES R-WIRE rather than deferring it. In-scope (server.py is writable).
  2. Ruff auto-fixed 2 import-sort (I001) issues in server.py (my lazy imports) via
     `ruff check loremaster/loremaster/server.py --fix` — the same 2 the adversary reference hit.
- **Packages considered:** none — no NEW package mechanism. The three lifts
  (`governed.resolve_principal`, `governed.resolve_write_scope`, `principals.resolve_operator_principal`)
  are EXTRACTIONS of code already in the tree; identity/keep resolution is against this repo's own
  `PrincipalStore`/`KeepStore`. Verified by reading each seam's installed source before lifting.
- **Reuse ledger:** see §DRY ledger — 3 EXTENDED (lifts), 1 HAND-ROLLED (`_owner_count`, twin of the
  existing `_scope_count`; no owner-count helper existed), plus test-only helpers.
- **Graded:** N/A — this is a BUILD report, not a verdict over someone else's artifact. HEAD at spawn
  `2ad831c`; all work is uncommitted in the MAIN tree (the lead commits).
- decisions-needed: none blocking. One FYI: R-WIRE was closed early (deviation 1) — flag if the lead
  wanted it strictly deferred to iii (I judged the param-honesty pin makes deferral impossible).
- receipt POINTERS: §Production diff · §Gates · §Corpse reconciliation · §α promise-registry ·
  §Removed-behaviour adjudication · §DRY ledger · §Tree provenance.

---

## Production diff (by file · symbol · what) — the ruled design (§7 item 5 / adversary reference)

| file | symbol | change |
|---|---|---|
| `governed.py` | `resolve_principal` (NEW, async) | lifted from `resolve_subject` step (2): token→admitted `Principal\|None`. `getattr(token,"subject",None)`; `if not email: return None` (short-circuit — no store lookup, adversary3 §D-NULLTOKEN); presented-but-unadmitted → `GovernedDenied` (moved text, not cloned). |
| `governed.py` | `resolve_write_scope` (NEW, sync) | lifted grant seam from `LocalMemoryBackend._resolve_write_scope`: `None→default`, else `pdp._grantable` else `GovernedDenied`. PURE (caller resolves default). |
| `governed.py` | `resolve_subject` | step (2) → `principal = await resolve_principal(...)`; `email = principal.email` (R4 ONE derivation). |
| `memory/local.py` | `_resolve_write_scope` | now a CALLER of `governed.resolve_write_scope`; default resolved LAZILY (`await self._default_project_scope() if scope is None else scope`). |
| `store/surreal_schema.py` | `_message_statements` | §4.F: `+= _governed_field_specs()` (3 `option<>` OVERWRITE fields, no ASSERT/DEFAULT) after the message field specs, `+= _governed_index_statements(MESSAGE_TABLE)` (message_scope + message_owner_principal, plain IF NOT EXISTS) after the hot-path indexes. Mirrors `_memory_statements`. Grows `governed_populations()` → {memory, message, to}. |
| `messages.py` | `send` / `_send_fragment` | optional `owner_principal`/`owner_agent`/`scope` threaded into the CREATE CONTENT: owners bound as `RecordID(PRINCIPAL_TABLE/AGENT_TABLE, …)` links (store-ref §2), scope a string; each bound NONE when its arg is absent (legacy sends stay unstamped). Columns always NAMED in CONTENT (stable raw-write shape for F5 site-derivation); all reads use explicit projections, so the added columns never reach a `SELECT *` decode. |
| `principals.py` | `resolve_operator_principal` (NEW, async) | THE operator (single principal / single admin), `None` on ambiguity. ONE IMPL — memory + agent + message legs all call it (proven by the value-mutation route pin). |
| `principals.py` | `_owner_count` (NEW) | owner-column count (twin of `_scope_count`) for the agent backfill + the §2.6 agent-first precondition. |
| `principals.py` | `_migrate_agent_owner` (NEW) | backfill NONE-owner agents → operator via `type::record`; `governed_exempt("migrate-governed")`; ∀ NONE-owner, never re-stamp; idempotent. |
| `principals.py` | `_migrate_message_owner` (NEW) | §2.6 agent-first refuse (count>0), operator-ambiguity refuse, golden `UPDATE message SET owner_agent = sender, owner_principal = sender.owner_principal, scope = $scope WHERE owner_principal IS NONE` (byte-matches the enforcement contract's `_MIGRATE_MESSAGE_GOLDEN`); `governed_exempt`. |
| `principals.py` | `_migrate_memory_scope` | now a CALLER of `resolve_operator_principal` (refuse reason byte-preserved for the 63a memory test). |
| `principals.py` | `migrate_governed` | dispatch wires `agent` → `_migrate_agent_owner`, `message` → `_migrate_message_owner`; fallback reason updated (memory/agent/message supported at 63b). |
| `server.py` | `CommsActionSpec.requires_capability` (NEW field, default False) | typed applicability (PKT-28 law). |
| `server.py` | `_COMMS_ACTIONS[send]` | `requires_capability=True` + `"capability"` in params. |
| `server.py` | `comms` + FastMCP `lore_comms` wrapper | `capability: str\|None=None` param + values-dict entry + threaded to the handler dispatch AND the wrapper (deviation 1 — closes R-WIRE). |
| `server.py` | `_comms_send` | §2.3 enforcement: UNCONDITIONAL `self._resolve_subject(capability)`; `agent_row.id == subject.agent_id` agent≡subject check (MP-5); session keep by key + "register first" deny; `governed.resolve_write_scope(subject, session_scope, default=session_scope)` (explicit — R5); `write_guard("send")` around `message_ledger.send(..., owner_principal=subject.principal_id, owner_agent=subject.agent_id, scope=message_scope)`. |
| `server.py` | `_comms_register` | resolve principal (§3.1); α ownerless branch (no keep, `owner_principal_id=None`); `get_or_create_keyed("session:<s>", type="session", keeper_email=principal.email)` + SF-63-1 foreign gate via `resolve_visible_keeps` BEFORE register (#97 — a denied register writes no row); `owner_principal_id=_bare(principal)`; render args. |
| `server.py` | `_render_comms_register` | + SF-63-1 keep line (minted/joined, keyed on `keep.keeper_id == principal_bare`); + reading-α OWNERLESS bound line (deny-verbs DERIVED from `_COMMS_ACTIONS` — INSTRUMENT 0); + R7 one-time `<name>:<secret>` capability line (first register only). |

---

## Gates
- `./scripts/typecheck.sh` → **Success, all members** (lorerunes/lorescribe/loresigil/loremaster/
  skills/docs-eval/scripts + shellcheck). Zero mypy errors incl. test trees. (`resolve_write_scope`
  typed `-> str`; `resolve_principal -> Any` — no annotation narrows needed.)
- `uv run ruff check .` → **All checks passed!** (after the 2 I001 auto-fixes in server.py — deviation 2).
- `uv run python scripts/pending_contract_gate.py --currency` → *(recorded in §Gates-currency below)*.
- **Contract files (the FROZEN contract — untouched):** built GREEN, run ALONE:
  - `test_message_governed_ddl_63b_ii_a.py` → 25 passed.
  - `test_message_migrate_63b_ii_a.py` + `test_message_enforcement_63b_ii_a.py` → 30 passed.
  - `test_comms_capability_63b_ii_a.py` + `test_comms_send_scope_63b_ii_a.py` → 34 passed.
  - cross-file: `test_governed_migration_63a.py` + `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput` → 12 passed.
- **Corpse (comms family), all GREEN:** `test_comms_tool.py` 924 · `test_mcp_server.py` 667 (128s, `-n auto`)
  · `test_comms_render_architecture.py` 26 · `test_comms_waiting_line.py`+`test_comms_await.py` 49 ·
  `test_comms_wiring.py` 29 · `test_surreal_fakes.py` 72 · `test_comms_promise_registry.py` 122.
- **Full suite (`-n auto`):** *(recorded below once the background run completes.)*

### Gates-currency
`uv run python scripts/pending_contract_gate.py --currency` → **CURRENCY: PASS** —
`typecheck GREEN · ruff GREEN · pytest GREEN` (manifest `(typecheck, ruff, pytest)`); 0 RED_ORPHANED.

### Full-suite result
**`uv run pytest -n auto` (run ALONE) → 11223 passed, 51 skipped, 3 xfailed, 0 failed, 0 errors**
(335s). Receipt: `scratchpad/fullsuite3.txt`.
- ⚠ The FIRST full run (concurrent with a straggler currency-gate process) reported 69 failed / 475
  ERRORS — the documented store-contention spurious-E pattern (brief: "run the full suite ALONE").
  Re-run ALONE it fell to **18 failed / 0 errors**, then to **0 / 0** after fixing the 18 (below).
- **There are 0 failing tests, related or unrelated.** The full suite is entirely green.

### In-scope regressions found by the full suite (18, all FIXED — brief-base §2 disclosure)
The clean full run surfaced 18 failures in 3 files my in-scope changes directly broke (all outside the
comms-family files the brief pre-named — disclosed here prominently and fixed minimally):
- **`test_comms_register_notice.py` (14)** — its `_RegisterCtx` duck-typed AppContext lacked
  `_principal_store`/`_keep_store` that the SF-63-1 `_comms_register` now reads. Added them
  (present-but-`None`: these tests drive a TOKENLESS register → the α path never dereferences them).
  → 15 passed.
- **`test_link5_render_containment.py` (2)** — the render-branch-reach instrument. (a) `_comms_register`
  became a render candidate (its foreign-gate/keep-missing `GovernedDenied` now interpolates `session`)
  → classified `store_backed` in `_RENDER_OUT` (same class as `_comms_send`; error text, not a served
  row). (b) `_render_comms_register`'s three new branches (keep/α/credential) were un-driven → added
  three probe shapes so branch reach stays a CHECKED variable. → 160 passed.
- **`test_principal_keys_schema.py` (1)** — the "PIN THE MISS" `record<principal>` link-set gate fired
  (as designed) on the new `message.owner_principal` link. Classified it LIVE-DEPENDENCY with the
  delete-disposition DEFERRED (mirroring `memory.owner_principal`, §4.F) + a re-open trigger. → 33 passed.
These files were NOT in the brief's pre-named corpse set; they are legitimate in-scope regressions of
the §4.F DDL + the SF-63-1 register (brief-base §2 "a regression your own in-scope change directly
causes may be fixed minimally and MUST be disclosed"). No CONTRACT pin was touched.

---

## Corpse reconciliation (the D1 all-in-ii-a shared fix + per-site adjudication)

The adversary measured the corpse at ~100 sites larger than the reviser's estimate; the root was the
comms test doubles lacking the governed identity substrate the enforced `send` + SF-63-1 `register`
now read. Reconciled by a SHARED fake seam (unblocked the bulk) + per-site credentialed drives.

**Shared fake seam (`_comms_fakes.py`, `_message_fakes.py`):**
- `FakeAgentDatabase` gains `owners` + `capabilities` maps.
- `FakeAgentRegistry`: `register(owner_principal_id=…)` kwarg (mint-once, stores owner + a minted
  `<name>:<secret>` capability); `_verify_capability_owner(presented, token)` mirroring the real
  four admission conditions (known cap · agent not retired · owner non-NONE · owner-email==token.subject),
  resolving the owner email through a wired `principal_store` ref (the JOIN's fake analog);
  `_mint_capability`.
- NEW `FakePrincipalStore` (`create`/`get_by_email`/`list`/`email_for_id`) + `FakeKeepStore`
  (`get_by_key`/`get_or_create_keyed`/`list_keeps_for_member`/`add`/`remove_household_member`,
  keeper-auto-household on mint).
- `FakeMessageLedger.send` accepts (and ignores) `owner_principal`/`owner_agent`/`scope` — the
  `Message` READ model carries no owner columns (like production's projection); the live owner-stamp +
  F5 classification are pinned against the REAL store in the ii-a contract files, never the fake.

**Test-side credentialing (`test_comms_tool.py` — shared, imported by waiting_line/await):**
- `_governed_ambient_token` autouse fixture (patches `server.get_access_token` to a switchable
  holder, tokenless by default → register α path unchanged for non-credentialed tests).
- `_credential_agent` (register owned + household), `_send` (credentialed send seam), `_credentialed_harness`.
- Setup helpers (`_harness`, `_03b_fleet`, `_ready`, `_fleet`, `_populate`, `_broadcast_recipients`)
  wire the governed stores + credential their agents; ~34 inline sends routed through `_send`
  (2 omitted-session tests credentialed INLINE so the omitted-session resolution path stays tested).
- `test_send_params_and_required` updated: send spec params include `capability`; `requires_capability is True`.
- `test_comms_render_architecture.py`: its `_harness` gains the governed stores (α path — register/
  heartbeat/fleet/publish render pins are additive-safe; 26 GREEN).
- `test_comms_await.py` / `test_comms_waiting_line.py`: import `_governed_ambient_token` (autouse) +
  `_send`; `_ask_via_dispatcher` drives credentialed.

### Removed-behaviour adjudication (CLAUDE.md rename-law / the DUAL)
- **Every reconciled send-family test PRESERVES its assertions** (recipient sets, receipts, drain/ack
  semantics, question teach, skew, session scoping) — only the DRIVE changed from tokenless to
  credentialed. No test was gutted to pass.
- Two coverage-preservation fixes (not mere pass-fixes): `test_a_DOMAIN_reject_DOES_touch_the_callers_row`
  and `TestUnregisteredRecipientIsTheEXISTINGTeachingError::test_nothing_is_delivered_…` were passing
  tokenless but for the WRONG reason (identity deny fires after the touch / broad `raises(Exception)`
  swallowed a GovernedDenied) — credentialed so they reject for the RIGHT reason (body / unknown
  recipient), restoring the intended coverage.
- `FakeMessageLedger.send` ignoring the owner stamps is adjudicated PRESERVED-WITH-PIN: the owner-stamp
  behaviour lives on the real Message row (no read model column), pinned live in
  `test_comms_send_scope_63b_ii_a.py::test_a_credentialed_send_stamps_exactly_the_subjects_pair` (R1) +
  the enforcement classifier — the fake never owned it.

---

## α promise-registry (task 3)
Three NEW served register lines were registered in `test_comms_promise_registry.py` (the standing
instrument auto-reds an unregistered served line):
- `_PROMISE_REGISTRY` + `_PROMISE_PROOFS` (with a `_render_register_governed` driver): the reading-α
  OWNERLESS bound line (§3.2 — emitted IFF ownerless; deny-verbs DERIVED) and the R7 one-time
  capability line (§3.4 — emitted IFF first register).
- `_PROMISE_FREE`: the two SF-63-1 session-keep lines (minted / joined — status reports).
- Two STRUCTURAL `_MARKER_CO_EMISSION_EXEMPTIONS` (no-brief-line × α, no-brief-line × credential): the
  register render ALWAYS emits a brief-section line, so a new register-render proof necessarily
  co-emits the bootstrap no-brief line — a structural co-emission (each new line still independently
  gated by its own NO-EMIT leg). `test_comms_promise_registry.py` → 122 passed.

---

## DRY ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `governed.resolve_principal` | `lore_get_symbol(governed.resolve_subject)` | step (2)'s token→principal block is the existing impl | **EXTENDED** `resolve_subject` (lifted; `resolve_subject` becomes a caller — R4 ONE derivation) |
| `governed.resolve_write_scope` | `lore_get_symbol(LocalMemoryBackend._resolve_write_scope)` | the grant predicate is a private method on the memory backend | **EXTENDED** `_resolve_write_scope` (lifted; memory becomes a caller — §4.A/§6) |
| `principals.resolve_operator_principal` | `lore_get_symbol(principals._migrate_memory_scope)` | the operator-resolution block is inline there | **EXTENDED** `_migrate_memory_scope` (lifted; all 3 legs call it — §4.C/§6) |
| `principals._owner_count` | `lore_get_symbol(principals._scope_count)` | `_scope_count` counts `scope IS NONE`, not owner | **HAND-ROLLED** — the owner twin; no owner-count helper existed (minimal, mirrors the scope twin exactly) |
| test helpers `_credential_agent`/`_send`/`_credentialed_harness` (test_comms_tool) | n/a (test infra) | the pre-enforcement `_deliver`/`_03b_fleet` idioms were tokenless | HAND-ROLLED test infra (the ONE shared credentialed-send seam every comms test now routes through) |

Sharing proven: the reference production diff was built + proven 88/0 TWICE by the adversaries; my
build makes the same 5 contract files + 2 cross-file pins GREEN. The R4 value-mutation pin
(`TestThePrincipalResolutionIsSharedByMutation`) + the structural route pins pass — perturbing
`governed.resolve_principal` moves BOTH `resolve_subject`'s subject AND `_comms_register`'s keeper.

## Tree provenance
Built in the MAIN tree (COMMIT-ONLY wave; the lead commits). `loremaster.__file__` +
`server.__file__` resolve under `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/` (the
main checkout — no scratch copy, per brief). Content backups `cp -a`'d to the session scratchpad
before this report (near-miss law): `scratchpad/builder-backup-green-120845` (+ earlier snapshots).

## Files touched (git status the lead will see)
- **Production (all in the brief's writable set):** `governed.py`, `memory/local.py`,
  `store/surreal_schema.py`, `messages.py`, `principals.py`, `server.py`.
- **Corpse test files (brief-named):** `_comms_fakes.py`, `test_comms_tool.py`,
  `test_comms_render_architecture.py`, `test_comms_waiting_line.py`, `test_comms_await.py`,
  `test_comms_promise_registry.py`, + `_message_fakes.py` (the sibling message-ledger fake the
  enforced send call reaches — same class as `_comms_fakes.py`).
- **Additional in-scope regression fixes (disclosed per brief-base §2, NOT contract files):**
  `test_comms_register_notice.py` (a comms register test — the enforcement broke it),
  `test_link5_render_containment.py` (render-branch reach instrument), `test_principal_keys_schema.py`
  (the `record<principal>` link-set gate). See §In-scope regressions.
- **NOT touched:** the 5 ii-a contract files + the 2 cross-file pins are byte-untouched;
  `_governed_contract.py` left as-is (§11.3 F-DUP follow-up, per brief).

## Flags / decisions-needed
- **R-WIRE closed early** (deviation 1) — forced by `test_param_honesty__every_spec_param_is_in_the_
  tool_signature`. If the lead wanted it strictly deferred to 63b-iii, say so; I judged it unavoidable
  (the pin makes deferral impossible). It is strictly forward progress (the wire now delivers `capability`).
- No other flags. No contract pin was edited.
