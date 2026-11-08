brief-base v16 read · brief project v7 read

# REPORT-builder-63c-i-a-fix — the 63c-i-a fix-wave BUILD (amendments 19–26 onto `84af63f`)

## SUMMARY BLOCK
- **state:** done-with-deviations (2026-09-26 11:5x; HEAD at report `5d549a1`+, production = `84af63f` + this build, uncommitted). Full suite ALONE `-n 12` on the build: **`11625 passed, 62 skipped, 3 xfailed` · EXIT=0 · 0 failed**; RED@HEAD baseline `108 failed, 11517 passed` → all 108 GREEN, 0 previously-green red (§5). ruff + typecheck GREEN; currency legs typecheck/ruff GREEN (§6). #486 did not appear.
- **deviations:** DV-1 gates ran on a provenance-asserted HEAD scratch copy + EXACTLY my 6 files (peer sessions 58/64b/#466 were dirtying the shared checkout, incl. tracked test files) · DV-2 #4b compensation inlined in `_comms_register` (the link-5 render gate reddened on a separate AppContext helper; classifying it is a test edit) · DV-3 `_owner_count` deleted (F-5) · DV-4 `-n 12` per brief despite MEMORY.md's new `-n auto` note. The lane blocked me 10:40→11:41 (reported to the lead at 11:11; cleared, run landed).
- **Packages considered:** dangling-link detection — SurrealQL, vendor doc `record::exists` READ + both forms PROBED: `sender.id IS NONE` (total), `record::exists(NONE)` RAISES → rejected (§1, §P.1) · created-vs-found — EXTENDED the existing `KeepStore.get_or_create_keyed` CAS (pydantic `__eq__` read from the installed source + measured) · no new dependency.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 14 new symbols, all dispositioned (§8) — incl. `_operator_unresolved` EXTRACTED from 3 inline copies (mutation-proven, 7/7 HELD, §6); no eighth `_bare_id` (#248).
- **Graded:** n/a — I built; I graded no one's artifact.
- **decisions-needed:** FORK-1 agent `backfilled` still the pre-count (D2 ruled on the message leg only; recommend the 1-line `_rows_stamped` for i-b) · FORK-2 ORDER-guard + dangling still two round trips (am-26 scope) · am-26 has NO pin (behaviour probe §P.2 ALL PASS; i-b pins) · DV-2's alternative (a `_RENDER_OUT` entry) is the lead's call.
- **receipt pointers:** §2 per-amendment table · §3 §10 constraints checklist · §4 builder-only items (F-8/F-5/F-7/R-4) · §5 RED→GREEN (108 ids verbatim) · §6 gates + currency + mutation proof · §7 DUAL (21 rows) · §8 DRY · §9 deviations/forks/residuals · §P.1 dangling probe · §P.2 am-26 probe · §B backup (patch md5 `b23f3e43416b9d0931dff1635ad53f85`).

## §0 Capability check (2026-09-26)
- Idle-gate contract written, not denied: `/tmp/claude-idle-gate-lore/297217bd-cb03-409c-ac95-0eb7ca9bf74b-builder-63c-i-a-fix.contract` = `{"artifact": "REPORT-builder-63c-i-a-fix.md"}` (session id = the lead's, as every 63c sibling contract carries; my env exposes none).
- lore reachable; `lore_comms register` OK (builder-63c-i-a-fix / 63c-20260924, role builder, cadence ≤20m). `lore_index()` at start: root `/workspace` @ `f4511ef` (= HEAD then), last sweep ~12 min.
- Store reference `docs/reference/surrealdb-31-capabilities.md` read FIRST, in full. Cited: §1.4 (legacy rows are seeded, not written), §2 (`SELECT *` omits NONE; decode ids with the SDK's `str()`), §6.4 (a dangling link's dereference yields NONE), §7 (`record::id()` on NONE raises — the same class decided the dangling predicate, §P).
- **grep/rg are hook-blocked (#473):** every textual sweep here used `awk` over `git ls-files` (said so per use): `_owner_count` consumers, not-supported prose pins, "inlin"/"injection" prose sweep, `delete-keep` verb, `LIVE SELECT` sites.
- **lore friction filed: #490** — `lore_search` exceeded 120 s twice (harness-backgrounded) and a DRY query for a bare-record-id helper missed the seven known `_bare_id` copies (#248). Fallback: awk + reading #248.
- **Process table (the one real obstacle):** another project (`mobile-pricepaper-smoke`) ran 4–8 concurrent pytest processes continuously from ~09:40 (sampled every 2 s for 60 s at 10:12: `4 4 6 6 6 6 6 6 6 8 8 6 … 4`). Per the brief I did not start a pytest while any was live, and killed nothing but my own gated runner (PID 2043401, by PID). To keep the main tree free for building while waiting, the RED@HEAD baseline was moved to a provenance-asserted HEAD scratch copy (`./scripts/scratch_copy.sh`, all four members resolve inside the copy).
- **MEMORY.md changed mid-run** (operator, 2026-09-26: full suite may run `-n auto`). My brief binds `-n 12`; brief > memory, so `-n 12` is used. Noted, not acted on.
- HEAD moved during the run by docs-only commits (`f4511ef` → `a761b71` → `081782e`; `git diff --stat f4511ef HEAD -- loremaster lorerunes loresigil lorescribe scripts` empty). A peer session left an untracked `scripts/probe_reanchor_58.py` in the tree (see §6).

## §1 Packages considered
- **Dangling-link detection** (the one mechanism I chose): SurrealQL, not a library. Vendor docs READ (`surrealdb-docs` tier, `functions/database-functions/record.mdx` — `record::exists(record) -> bool`, with executable test annotations) and store reference §6.4 read; both candidates PROBED on the test store (§P). Verdict: `sender.id IS NONE` (total over a NONE link); `record::exists` rejected because `record::exists(NONE)` RAISES (probed) — the §7 `record::id()` failure class.
- **Created-vs-found signal**: the existing `KeepStore.get_or_create_keyed` CAS — EXTENDED in place (it already knows which branch won); no package does this. The pydantic behaviour it relies on was READ from the installed source (`BaseModel.__eq__`, pydantic 2.13.4) and measured (§4 keeps row).
- No new dependency. Nothing hand-rolled that a package covers.

## §2 Per-amendment table (what · where (symbols) · receipt)
| am. | what the ruling requires | where (production symbol) | receipt (pins; §5 row) |
|---|---|---|---|
| 19 D-1 | §2.1 owned-but-unscoped refusal is a STORE fact, checked ONCE at the verb, ∀ `--table`, SAME teaching, byte-inert; ONE shared function also read by the message ORDER guard, re-keyed owner→scope | `principals.migrate_governed` → `_agent_migration_preconditions` + `_verb_level_refusal`; `_migrate_message_owner` decides the ORDER guard from `preconditions.unscoped_count`; agent leg's private row precondition DELETED | a19 `TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19`, `TestTheMessageOrderGuardIsScopeKeyed63cIAa19`, `TestThePreconditionIsSHAREDByMutation63cIAa19` |
| 19 F-3 | agent UPDATE self-guarding `… AND owner_principal IS NONE` | `principals._migrate_agent_owner` backfill statement | `test_agent_governance_63c_i_a.py::…::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement` |
| 19 D-2 | blank role refused BEFORE the keep mint, via `is_blank` | subsumed by am-22 §1: `AgentRegistry.preflight` (→ `_refuse_an_invalid_identity` → `lorerunes.is_blank`) called by `AppContext._comms_register` before `get_or_create_keyed` | a19 `TestABlankRoleRegisterHasNoSideEffect63cIAa19`; `test_agent_registry.py::…::test_the_blank_role_rule_is_the_SHARED_is_blank[handler]` |
| 19 D-3 F-1 | derived diagnosis: operator-owned (E3 wording) / named other principals (bounded) | `principals._owned_unscoped_part` | R-Q5-1 ×6 populations |
| 19 CA-1 | stored ids through THE `sanitise_line` | `principals._id_sample` (+ the dangling render, the principal names) | a19 `TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19` |
| 19 D-3 F-9 | gloss dropped; `must match <pattern>` byte-identical in registry + server | `AgentRegistry._refuse_an_invalid_identity`; `AppContext._validate_comms_charset` ("does not match" → "must match") | a19 `TestTheIdentityRuleHasOneSpelling63cIAa19`; a19a skeleton goldens |
| 19 F-8/F-5/F-7 | builder-only prose | §4 below | — (cold audit) |
| 20 §8.1 | operator-only owned-but-unscoped store still refused; diagnosis names operator + E3 | `_owned_unscoped_part` | R-Q5-1 `[operator-owned]` |
| 20 §8.2 R1 | principals named == `min(_REFUSAL_ID_SAMPLE_SIZE, distinct)`, same constant | `_owned_unscoped_part` (`others[:_REFUSAL_ID_SAMPLE_SIZE]`) | R-Q5-1 `[above-cap]`/`[perturbed-bound]` |
| 20 §8.3 | exact name `_agent_migration_preconditions`, takes the `StoreHandle` | `principals._agent_migration_preconditions(store, *, table=None)` | the redirect pins (a19/a19a/a19b) |
| 20 §8.4 R2 | unresolvable operator + owned-but-unscoped: ONE refusal, operator remedy FIRST, owners UNCLASSIFIED | `_verb_level_refusal` + `_operator_unresolved(…, purpose="to classify the rows below")` + `_owned_unscoped_part(…, None)` | a19a `TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed63cIAa19a` |
| 21 CD-1 | message WHERE `scope IS NONE AND owner_principal IS NONE`; scope-keyed counts; ∀-legs WHERE rider | `_migrate_message_owner` (statement + `_scope_count`); `_owner_count` DELETED | a19a `TestTheMessageBackfillIsScopeKeyed63cIAa19a`; a19b D2 pin |
| 21 CD-2 / 22 F-1 / 23 FK-3 | validity FIRST, zero I/O; valid = {agent, memory, message, brief} | `migrate_governed` first line; `_MIGRATE_VALID_TABLES`; `_not_supported(table, store_was_read=False)` | a19a `TestTableValidityIsCheckedFirst63cIAa19a` |
| 22 §1 (#485) | `preflight` ONE write-free method; `register` calls it first; handler calls it before the mint; created-only compensation | `AgentRegistry.preflight`; `AgentRegistry.register`; `AppContext._comms_register`; `keeps.minted_by_this_call`; its inline compensation | a19a runtime pin + `TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a`; a19b KP1/KP4/KP5/KP6/KP13/KP14 |
| 22 F-2 | both agent half-pairs refused at the verb, "half-applied" | `_agent_migration_preconditions` (one OR query, both halves) + `_verb_level_refusal` | a19a `TestHalfPairsAreRefusedAtTheVerb63cIAa19a`, PD2 |
| 22 §4 / 24 FK-a | `None` receipts on EVERY refusal | `principals._refused` (every refusal routes through it); `governed.MigrateGovernedResult` fields `int | None` | a19a `_assert_no_unmeasured_count` legs; a19b KP7a/b/c |
| 23 FK-2 | dangling sender refuses the MESSAGE leg only; count + bounded ids; byte-inert | `_agent_migration_preconditions` (message leg, `sender.id IS NONE`) + `_message_leg_refusal` | a19a `TestADanglingSenderRefusesTheMessageLeg63cIAa19a`, invariant pin; a19b KP2 |
| 24 §1 MP-A | runtime property ∀ driven registers | (behaviour — preflight before mint) | a19a `test_EVERY_driven_register_meets_the_runtime_property` |
| 24 door #1 | both agent half-pairs: ONE refusal naming BOTH | `_verb_level_refusal` | a19b KP8 |
| 24 door #2 + 25 | message half-pairs, BOTH halves, one refusal, per-half count + bound; `backfilled` = rows stamped | `_agent_migration_preconditions` (message half-pair read) + `_message_leg_refusal`; `_rows_stamped` | a19b `TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b`, `TestBackfilledIsTheRowsStamped63cIAa19b` |
| 24 door #4b | failed compensation: teaching verbatim + ONE appended line (bare keep id + `lore-adm delete-keep`) | the `except _AgentRegistryError` branch inline in `AppContext._comms_register` (DV-2) | a19b `TestAFailedCompensationIsNamedToTheCaller63cIAa19b` |
| 24 FK-b | "created" from the mint's own return | `KeepStore.get_or_create_keyed` sets the flag only on its own winning CREATE; `keeps.minted_by_this_call` | a19b KP1 |
| **26** | dangling + half-pair in one store: ONE refusal naming BOTH, dangling FIRST, each counted + bounded, byte-inert | `_message_leg_refusal` (parts in the shared function's check order, one remedy sentence); order stated ONCE in `_agent_migration_preconditions`' docstring | **no pin (ruled for 63c-i-b)** — behaviour probe §P.2 |

## §3 `REPORT-contract-63c-i-a-a19b.md` §10 BUILDER CONSTRAINTS — item by item
| # | constraint | how the build meets it (symbol) |
|---|---|---|
| carried | `AgentRegistry.preflight(name, *, session, role, spawned_by, owner_principal_id, session_keep_id?)`; `register` calls it first | `AgentRegistry.preflight` (signature exact; `session_keep_id` defaults to the `_KEEP_NOT_YET_MINTED` marker so an explicit `None` still checks the pair — a19a mirror case `mixed-pair-once-minted`); `register`'s first statement is `await self.preflight(…, session_keep_id=session_keep_id)`; its private retired/role/spawned_by copies are DELETED |
| carried | handler calls `preflight` BY NAME on the wired registry BEFORE `get_or_create_keyed`, keywords `session`, `role`, `spawned_by`, `owner_principal_id`, NO `session_keep_id` | `AppContext._comms_register`: `await self.agent_registry.preflight(agent, session=…, role=…, spawned_by=…, owner_principal_id=principal_bare)` — before the `if principal is not None:` mint block, so the tokenless path preflights too |
| carried | mint through `self._keep_store.get_or_create_keyed`, BY NAME | unchanged call (`keep_store = self._keep_store`; `keep_store.get_or_create_keyed(key=…, type=…, keeper_email=…, name=…)` — same kwargs as `84af63f`, so `FakeKeepStore`'s signature is untouched, item 9) |
| carried | `principals._agent_migration_preconditions` is THE shared function (redirect pins rebind it by name and swap its `StoreHandle`) | defined with that name, first positional arg the `StoreHandle`; `migrate_governed` looks it up at CALL time through the module global (so a monkeypatched binding is what runs); the message leg receives its RESULT (no second call, no private query) |
| carried | `principals._REFUSAL_ID_SAMPLE_SIZE` is THE one bound | read at call time by `_id_sample`, the principal-name slice in `_owned_unscoped_part`, and the dangling slice in `_message_leg_refusal` — no other literal bound |
| 1 | `AppContext.comms` instance-patchable; handler reaches the keep store via `self._keep_store` | unchanged dispatch; `keep_store = self._keep_store` |
| 2 | every refusal a driven register can meet precedes the mint, except the race (keep + `member_of` byte-identical after created-only compensation) | `preflight` before the mint; `except _AgentRegistryError` → an inline `keep_store.delete_keep(keep_id=session_keep_bare)` iff `minted_session_keep` |
| 3 | "created" from the mint's OWN return | `minted_by_this_call(session_keep)` — the flag is set only inside `get_or_create_keyed` after ITS OWN CREATE; a found keep (key read, or CAS re-read of a concurrent winner) never carries it; no pre-read |
| 4 | race path serves the registry refusal unaltered; a failed mint propagates `KeepStoreError` and writes no agent row | successful compensation → bare `raise` (same object, untouched); the mint is outside the `try`, so its `KeepStoreError` propagates before `register` runs |
| 5 | door #2 IN `_agent_migration_preconditions`' message leg, beside the dangling read; both halves; per-half count + `_REFUSAL_ID_SAMPLE_SIZE` sample; ONE refusal naming every present half; `half-applied`, never `multi-principal`/`dangling` (half-pairs alone); `sanitise_line`; message table only; byte-inert; `scanned=None`/`already_migrated=None`/`backfilled=0`; decides from the SHARED result | message-leg reads in `_agent_migration_preconditions` (`messages_owned_unscoped`, `messages_scoped_ownerless`); `_message_leg_refusal` renders each present half with `_id_sample`; `_refused(...)`; the message leg reads only `preconditions` |
| 6 | message WHERE stays `scope IS NONE AND owner_principal IS NONE`; `backfilled` = rows stamped; counts SCOPE-keyed | the function-local `backfill_statement`; `_rows_stamped(stamped)`; `_scope_count(store, MESSAGE_TABLE, none=…)` |
| 7 | door #4b: same CLASS; `str()` STARTS WITH the teaching; exactly ONE `"\n"` line with the BARE keep id + `lore-adm delete-keep`; caller's `session` out of it; the delete error never replaces the teaching | on a failed inline `delete_keep` (DV-2) `_comms_register` mutates the SAME exception's `args` to `(f"{refusal}\nALSO: … session keep {keep_bare} … remedy: \`lore-adm delete-keep --keep {keep_bare}\`",)` and the caller's bare `raise` re-raises it — same object, same class, same traceback; `keep_bare` is the store-minted id (`--keep` accepts a bare id: `principals.build_parser`'s `delete-keep` → `KeepStore.delete_keep`, verified) |
| 8 | FK-a everywhere | EVERY refusal is built by `principals._refused` (`scanned=None`, `already_migrated=None`, `backfilled=0`): verb, ORDER, dangling/half-pair, the three legs' operator refusals, not-supported |
| 9 | fakes' `FakeKeepStore.get_or_create_keyed` signature | no new kwarg — "created" rides the return value |

## §4 Builder-only items (amendment 19 §W item 6; a19 report §9) — no pin, graded by the cold audit
| item | what I did | where |
|---|---|---|
| **F-8** — the refuted "inlined as a literal into live WHERE clauses" threat model | Replaced with #219's corrected rationale (bound parameters; the trailing-newline twin, #210; render-safety by construction; the cheap gate before the registry read). **Verified before writing (#219's own residual — "whether any OTHER path inlines an identity was not swept"):** awk over production for `LIVE SELECT` → the only identity-derived inlined literal is `inbox_awaiter.live_select_statement`'s `WHERE out = agent:\`<id>\``, and `<id>` is the uuid5 HASH of name/session (no caller text); names/sessions themselves are never inlined. The prose says exactly that. | `lorerunes/identifiers.py` module docstring + the `AGENT_NAME_PATTERN` comment; `loremaster/agents.py` identity-charset block comment |
| **F-5** — `_owner_count`'s stale docstring | **Deleted the function** instead: after CD-1 (scope-keyed message counts) and D-1 (the ORDER guard reads THE shared function) it had no caller. Stronger than a docstring fix; DUAL row D3. Consumer check: `lore_impact` (1 prod ref — the message leg, now rewritten) + awk over `loremaster/tests`, `scripts`: no reference (the only `owner_count` hit is an unrelated test name, `test_retry_seam.py::…test_the_two_independent_owner_counts_AGREE`). | `principals.py` |
| **F-7** — DUAL line | "dropped-deliberately: `is_blank` is the ONE blankness rule (#222)" — §7 row A3. (The narrowing itself shipped at `84af63f`; this wave only records it.) | §7 |
| **Cold audit R-4** — "a `refused=True` writes nothing" | Stated where it is true and scoped: the `_refused` docstring says a `refused=True` result writes NOTHING, and that a leg whose backfill UPDATE RAISES after its idempotent project-keep mint is not a refusal (CA-2). Also §7 row D14. | `principals._refused` docstring; §7 |
| a19 §9 note — the a19 reference reached a registry-private static from the handler | Superseded: the handler calls the PUBLIC `AgentRegistry.preflight`. | `server.py` |

## §7 DUAL — removed-behaviour inventory (every deleted or replaced production branch)
Adjudication vocabulary per CLAUDE.md: preserved-with-pin · dropped-deliberately (reason) · old-bug (not re-pinned) · spec-silent (→ ruling).
| # | old behaviour at `84af63f` (symbol) | new | adjudication |
|---|---|---|---|
| D1 | `migrate_governed`: any table outside memory/agent/message → refused, `scanned=0`/`already_migrated=0`, no I/O, reason echoing `{table!r}` raw, "at packet 63b … (brief lands 63c …)" | invalid name → `_not_supported(store_was_read=False)`: still ZERO I/O, `None` receipts, the table echo through `sanitise_line`, names the governed set; `brief` is VALID (preconditions read, then `_not_supported(store_was_read=True)` saying "does not yet migrate `brief` — lands 63c-ii … preconditions were read and passed, nothing was written") | zero-I/O: preserved-with-pin (a19a validity pin; am-21 CD-2). `0`→`None`: dropped-deliberately (am-22 §4). brief-valid: changed per am-22 F-1/FK-3. "at packet 63b"/"brief lands 63c": old-bug (stale prose), not re-pinned. The two texts differ on purpose: the brief answer READ the store, the invalid answer did not (CONSUMER LAW) |
| D2 | memory leg operator-unresolved refusal, `0` receipts | same text byte-identical (now built by the shared `_operator_unresolved(purpose="to keep the project keep")`), `None` receipts | text preserved; `None`: am-24 FK-a (KP7c[memory]) |
| D3 | `_owner_count` (owner-keyed counts: the ORDER guard on `agent`; the message leg's unmigrated/already) + its log event `governed.owner_count.rejected` | DELETED | dropped-deliberately: CD-1 (counts scope-keyed) + D-1 (the ORDER guard reads THE shared function). Residual R-f: the log event name is retired |
| D4 | agent leg §2.1 ROW precondition (after operator resolution and the counts): `SELECT VALUE id … scope IS NONE AND owner_principal IS NOT NONE`; refused with MEASURED `scanned`/`already`; fixed text "a multi-principal or half-applied store"; ids `str()`-raw; an unresolvable operator answered ALONE (the owned rows unnamed); ownerless-SCOPED agents never refused | moved to the VERB (`_agent_migration_preconditions` + `_verb_level_refusal`): ∀ tables, same text, `None` receipts, derived diagnosis, ids sanitised, operator remedy FIRST + owners unclassified when unresolvable, ownerless-scoped agents refused "half-applied" | the refusal: preserved-with-pin (R-Q5-1, a19 ∀[agent]); measured→`None`: am-22 §4; fixed phrase: old-bug (F-1); raw ids: old-bug (CA-1 #484); operator-alone: changed per am-20 §8.4; half-applied: added per am-22 F-2 |
| D5 | agent leg operator refusal, `0` receipts | text byte-identical via `_operator_unresolved(purpose="to own the fleet's agents")`, `None` | as D2 |
| D6 | agent backfill `… WHERE scope IS NONE` (would stamp a row that became owned-but-unscoped after the precondition read) | `… WHERE scope IS NONE AND owner_principal IS NONE` | dropped-deliberately (am-19 F-3 TOCTOU); golden pinned. `backfilled` still the scope-keyed pre-count — FORK-1 (§9) |
| D7 | message ORDER guard: `_owner_count(agent, none=True) > 0`, noun "NONE-owner agent(s)", `0` receipts | `preconditions.unscoped_count > 0` (THE shared read), noun "un-migrated (NONE-scope) agent(s)", `None` | refusal on a legacy store naming `agent`: preserved-with-pin (a19 PRESERVED pin, ii-a pins); re-key: am-19 D-1; noun follows the predicate (MP-4); an ownerless-SCOPED agent no longer trips it — it is refused at the verb instead (am-22 F-2) |
| D8 | message operator refusal, `0` receipts, reached right after the ORDER guard | text byte-identical via `_operator_unresolved`, `None`, reached after the row-fact refusal | text preserved; order: the row facts are table-local and measured without the operator |
| D9 | message counts owner-keyed | `_scope_count` (scope-keyed) | am-21 CD-1; pinned by the a19b D2 redirect leg |
| D10 | message WHERE `owner_principal IS NONE` (re-stamped a scoped-but-ownerless row's scope/owner) | `scope IS NONE AND owner_principal IS NONE` | dropped-deliberately (am-21 CD-1; am-25: that population is now refused and never stamped) |
| D11 | message `backfilled = unmigrated` (pre-count) | `_rows_stamped(<UPDATE result>)` | old-bug (D2 / am-24 §2) |
| D12 | message leg over a ghost sender: stamped the message `owner_principal` NONE + the project scope | refused, byte-inert, "dangling sender" (the sound rows NOT stamped either) | old-bug (am-23 FK-2); invariant pinned (a19a) |
| D13 | message leg over a message half-pair: proceeded; half (i) never converged, half (ii) was re-stamped | refused "half-applied", both halves in ONE refusal | old-bug (am-24 door #2, am-25) |
| D14 | (R8 wording, cold audit R-4) "a refusal writes nothing" | scoped: "a `refused=True` writes nothing"; a backfill that RAISES after the idempotent project-keep mint may leave that keep (CA-2) — unchanged behaviour, now stated truthfully | prose correction only |
| A1 | `AgentRegistry.register`: pair → identity → `_select_row` → retired → role → spawned_by, inline | `register` → `preflight` (same order, same texts, same ONE row read; the pair still unconditional in `register`, which always passes `session_keep_id`) | preserved-with-pin (`test_an_inconsistent_provenance_pair_is_refused_before_any_store_io`; a19a mirror; KP5) |
| A2 | identity refusal: "must match <pattern> (lowercase letters, … starting with a letter or digit)" | "must match <pattern>; nothing was written …" | dropped-deliberately (am-19 F-9: the gloss omitted the 64-char cap and was a second spelling of the rule) |
| A3 | **F-7:** a role of only U+001C–U+001F was ACCEPTED by the dropped store `ASSERT string::len(string::trim($value)) > 0`, REFUSED by `is_blank` (since `84af63f`) | unchanged | **dropped-deliberately: `is_blank` is the ONE blankness rule (#222)** (63c-ii aligns `brief.body`'s trim-based ASSERT, am-19 D-3) |
| S1 | handler: mint → SF-63-1 gate → `register` (a refusal after the mint left the keep, caller its keeper — #485) | `preflight` → mint → gate → `register` → created-only compensation (+ #4b line on a failed delete) | old-bug (#485); tokenless-mints-no-keep preserved (P3; a19 CONTROLS). Cost: one extra agent-row read per register (the preflight read; `register` re-reads — see R-j) |
| S2 | charset refusal "{label} does not match {pattern}" | "{label} must match {pattern}" | am-19 F-9 (one rule, one spelling) |
| K1 | `get_or_create_keyed` returned the keep, created-vs-found invisible | the SAME keep, plus the non-field flag on its own winning CREATE | additive; equality/dumps unaffected (measured) |
| G1 | `MigrateGovernedResult.scanned/already_migrated: int` | `int | None` | am-22 §4. The only renderer (`principals._dispatch_migrate_governed`) prints counts only on `refused=False`, where they are always ints — `None` is never rendered as a count |

## §8 DRY ledger (every new symbol)
| new symbol | lore query / read | what it returned | disposition |
|---|---|---|---|
| `AgentRegistry.preflight` | ruled name (am-22 §1); read `AgentRegistry.register` | register's own inline refusals | **EXTENDED `AgentRegistry.register`** — its write-free refusals factored out; register now CALLS it (no copy left) |
| `agents._KEEP_NOT_YET_MINTED` | read `_comms_fakes._KEEP_NOT_YET_MINTED` (the contract's mirror) | the fake's own marker (test tree) | HAND-ROLLED: production cannot import a test fake; the two are mirrored by the a19a mirror pin |
| `keeps.minted_by_this_call` + `_MINTED_BY_THIS_CALL` | read `KeepStore.get_or_create_keyed` | the CAS already distinguishes create-won vs found | **EXTENDED `KeepStore.get_or_create_keyed`** (reports its own branch); ONE reader function |
| (compensation — no new symbol after DV-2) | NO lore query run for this one (said plainly); awk over production for `delete_keep(` callers (note ¹) | only the `lore-adm delete-keep` verb | inlined in `AppContext._comms_register`; REUSES `KeepStore.delete_keep`. (First draft was a helper `AppContext._release_the_minted_session_keep` — removed, DV-2) |
| `principals._agent_migration_preconditions` + `AgentMigrationPreconditions` | ruled name (am-20 §8.3); `lore_impact(_owner_count)`, `lore_get_symbol(run_query)` | the agent leg's private query, `_owner_count` | **REPLACES** three private decisions (agent-leg row precondition, `_owner_count` ORDER guard, none-yet for dangling/half-pairs) with ONE read; REUSES `run_query`, `_scope_count` |
| `principals._governed_select` | `lore_get_symbol(run_query)` | `run_query` (the ONE attempt body) | thin wrapper that REUSES `run_query` (three parameterless SELECTs, one tolerance rule) |
| `principals._id_sample` | `lore_search` "render a bounded sample of record ids with sanitise_line …" ² | — | HAND-ROLLED as the ONE bounded-id render for this verb's refusals; REUSES `loremaster.sanitise.sanitise_line` + `_REFUSAL_ID_SAMPLE_SIZE`; replaced the agent leg's inline raw render |
| `principals._operator_unresolved` | read the three legs | THREE inline copies of the same sentence + counts | **EXTRACTED to ONE home** (text byte-identical per call site via `purpose`) — the fourth caller (the verb's R2 refusal) would otherwise have been copy #4 |
| `principals._refused`, `_not_supported`, `_MIGRATE_VALID_TABLES` | read `migrate_governed` | the inline `MigrateGovernedResult(... refused=True ...)` constructions (6 sites) | ONE refusal constructor — FK-a (`None` receipts) cannot be forgotten at a site |
| `principals._owned_unscoped_part`, `_verb_level_refusal`, `_message_leg_refusal` | ruled renders (am-19 F-1, am-20 §8.4, am-24/25/26) | the a19b reference's shape | HAND-ROLLED to the rulings; no id parse — owners compare/render by the SDK's `str(RecordID)` (finding #248's seven `_bare_id` copies NOT extended with an eighth) |
| `principals._by_id`, `_rows_stamped` | — | — | single-purpose (sort key; D2 count) |

¹ ² `lore_search` over-ran 120 s on this box today (finding #490); results, when they arrive, are recorded in §9 R-k. The awk fallback over `loremaster/loremaster` + `lorerunes/lorerunes` (run 2026-09-26, pattern `delete_keep\(|ids shown|of .* shown`): the only other `delete_keep` caller is the `lore-adm delete-keep` verb (`principals._cmd_delete_keep` — an admin verb, not a compensation seam); the only bounded-id render is this build's `_id_sample` (the `84af63f` agent-leg inline render it replaced is deleted); `search.py:849` is unrelated prose.

## §P Probe instruments (verbatim — scratch is disposable)

### §P.1 `probe_dangling_sender.py` — md5 `25767255958074ccaf50457a2285aa1f`
Run 2026-09-26 ~10:05 EDT on the TEST store (spike-surreal `:18000`, throwaway DB), repo HEAD `a761b71` production. Output, verbatim:
```
agents: [RecordID(table_name=agent, record_id='real_sender')] | connectivity: ''
sender.id IS NONE                  -> ['message:m_ghost']
record::exists(sender) = false     -> ['message:m_ghost']
record::exists(NONE) RAISES: InternalError Incorrect arguments for function record::exists(). Argument 1 was the wrong type. Expected `record` but found `NONE`
ALL PREDICATES CORRECT
EXIT=0
```
```python
"""builder-63c-i-a-fix — probe: which SurrealQL predicate detects a legacy message whose `sender` link
names NO agent row (amendment 23 FK-2 asks the builder to confirm the detection shape against the store
reference / a TEST-store probe). Neither candidate is in docs/reference/surrealdb-31-capabilities.md.

Throwaway database on the TEST store (spike-surreal ws://127.0.0.1:18000 — NEVER :18500), the REAL
emitted agent + message DDL + the governed overlay, rows seeded through the repo's ONE seeders.
Self-checking: exits non-zero if either predicate misclassifies. Controls: a SOUND legacy message (real
sender) must NOT match; the GHOST must match; a scoped (migrated) ghost must not match the scope-gated
form. Run: cd <repo> && uv run python <this file>
"""

import asyncio
import sys

sys.path.insert(0, "loremaster/tests")

from _governed_contract import (  # noqa: E402
    apply_ddl,
    governed_overlay_ddl,
    seed_agent_legacy,
    seed_message_legacy,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database  # noqa: E402
from lorerunes.pdp import keep_scope  # noqa: E402
from loremaster.store import surreal_schema  # noqa: E402

PREDICATES = {
    "sender.id IS NONE": "SELECT VALUE id FROM message WHERE scope IS NONE AND sender.id IS NONE",
    "record::exists(sender) = false": (
        "SELECT VALUE id FROM message WHERE scope IS NONE AND record::exists(sender) = false"
    ),
}


async def main() -> int:
    env = make_env(database=unique_database(), dim=8)
    connection = await connect_admin(env)
    failures = []
    try:
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl("message"), url=env.url)
        version = await run(connection, "RETURN string::concat('', '')")  # connectivity check
        await seed_agent_legacy(connection, row_id="real_sender", name="real-sender", session="p")
        await seed_message_legacy(connection, sender_id="real_sender", session="p", seq=1, row_id="m_sound")
        await seed_message_legacy(connection, sender_id="ghost_sender", session="p", seq=2, row_id="m_ghost")
        await seed_message_legacy(
            connection,
            sender_id="ghost_sender_2",
            session="p",
            seq=3,
            row_id="m_ghost_scoped",
            scope=keep_scope("somekeep"),
        )
        agents = await run(connection, "SELECT VALUE id FROM agent")
        print("agents:", agents, "| connectivity:", repr(version))
        for label, statement in PREDICATES.items():
            found = sorted(str(value) for value in (await run(connection, statement) or []))
            print(f"{label:34s} -> {found}")
            if found != ["message:m_ghost"]:
                failures.append(f"{label}: expected ['message:m_ghost'], got {found}")
        # TOTALITY over a NONE link (a legacy row written under an older DDL): the dereference form is total,
        # record::exists RAISES (the store-ref §7 record::id() class) — so the builder uses the dereference form.
        assert await run(connection, "RETURN (NONE).id IS NONE") is True
        try:
            await run(connection, "RETURN record::exists(NONE)")
        except Exception as error:  # noqa: BLE001 - the probe records the engine's refusal
            print("record::exists(NONE) RAISES:", type(error).__name__, str(error)[:120])
        else:
            failures.append("record::exists(NONE) did not raise — re-evaluate the choice")
    finally:
        await connection.close()
        await drop_database(env)
    for failure in failures:
        print("FAIL", failure)
    print("ALL PREDICATES CORRECT" if not failures else "PROBE FAILED")
    return 1 if failures else 0


sys.exit(asyncio.run(main()))
```

## §9 Deviations, forks and residuals (each with an individual verdict)
### Deviations
- **DV-1 · The gates ran on an ISOLATED tree, not the shared checkout.** From ~10:30 peer sessions (packets 58, 64b, #466) began writing UNCOMMITTED contract tests into the shared checkout — new RED-by-design files (`test_supersede_reanchor_58.py`, `test_task_guarded_shell_58.py`, `test_task_claimable_partition_58.py`, six `test_findings_*_64b.py`, `test_loopback_serving.py`, `test_no_raw_listener_in_test_trees.py`, …) AND edits to TRACKED test files (`test_task_ledger.py`, `test_blocks_edge.py`, `test_task_read_surface.py`), plus `scripts/*` and `skills/…` files. On the shared tree `./scripts/typecheck.sh` went RED in those files (11 errors in 5 loremaster test files + 2 in `skills/`) and `ruff check .` RED on `scripts/probe_reanchor_58.py` — none of it mine. So every gate below ran on the `scratch_copy.sh` tree of HEAD (`a761b71`; HEAD since moved `.md`-only, `git diff --stat a761b71 HEAD -- . ':!*.md'` empty) with EXACTLY my six production files applied (`git apply` of `build_prod.patch`, then `cmp` of each against the main tree: identical) — the same committed test bytes the RED@HEAD baseline ran. Provenance re-verified (`scratch_copy.sh --verify-only`: all four members resolve inside the copy).
- **DV-2 · The #4b compensation is INLINE in `AppContext._comms_register`, not a separate helper.** My first build put it in a new `AppContext._release_the_minted_session_keep`; the link-5 completeness gate (`test_link5_render_containment.py::TestEveryRenderCandidateIsDrivenOrOut::test_every_candidate_is_driven_or_out`) correctly reddened: a new AppContext method interpolating non-constants into a served string must be DRIVEN or in `_RENDER_OUT`, and classifying it is a test-file edit outside my writable set. Its output IS an error surface of `_comms_register`, which `_RENDER_OUT` already classifies `store_backed` (the SF-63-1 deny text) — so it lives there now. I did NOT move it to module level (the a19b reference's placement), because that is outside the scan's universe and would pass by being invisible, not by being classified. **Alternative, written down (brief-base §2):** keep a named helper and have the i-b contract author add `"_release_the_minted_session_keep": ("store_backed", …)` to `_RENDER_OUT`. To stay under PLR0915 after inlining, `principal_bare`'s declaration + conditional assignment became one expression (behaviour identical).
- **DV-3 · `_owner_count` DELETED rather than re-documented (F-5).** §4 / §7 D3.
- **DV-4 · `-n 12`, not `-n auto`**, despite MEMORY.md's 2026-09-26 operator note — the brief binds `-n 12`.

### Forks (non-blocking; my pick taken, the alternative stated)
- **FORK-1 · agent (and memory) `backfilled` is still the pre-count.** Amendment 24 §2's D2 ("`backfilled` is the rows the UPDATE STAMPED — a measured count, never the pre-count") is ruled on the MESSAGE leg. F-3 made the AGENT WHERE self-guarding, so its pre-count (`scope IS NONE`) and its WHERE now disagree by construction exactly as the message leg's did — on the F-3 race only (an owned-but-unscoped row appearing between the verb read and the UPDATE; unreachable by any test). Reading A (mine): the ruling covers the message leg; changing the agent receipt is a served-surface change beyond the rulings (a brief STOP trigger), so NOT built. Reading B: the D2 principle is general; `backfilled=_rows_stamped(...)` on the agent leg is a one-line change using the helper that already exists. Memory's WHERE equals its count predicate, so it has no gap. **Recommend Reading B for i-b** (quantifier law: the safety claim was derived on one leg of a set this wave changed).
- **FORK-2 · amendment 26 scope.** Built exactly as ruled (dangling + half-pairs → one refusal, dangling first). The ORDER guard is still a SEPARATE earlier refusal: a store with un-migrated agents AND a dangling sender answers the ORDER refusal first and the dangling one only on the next run (two round trips — the shape am-26 forbids for its own pair). Not ruled; not built; surfaced.

### Residuals
| # | residual | verdict |
|---|---|---|
| R-a | A non-registry failure AFTER the keep mint (e.g. a store error on `register`'s CREATE) leaves the minted session keep — compensation is scoped to `AgentRegistryError` per am-22 §1.2 | surfaced (unruled); same #485 harm class, unreachable by the drivers |
| R-b | `_dispatch_migrate_governed` prints `result.table` raw to stderr on a refusal; for an invalid name that is the operator's own argv (the reason now sanitises it) | LOW |
| R-c | `inbox_awaiter.live_select_statement`'s docstring calls the id "a uuid5 hash of charset-ASSERTed name/session" — the store ASSERT was dropped at 63c-i-a Q3 (the writer enforces the charset now) | stale prose outside F-8's named sites; flagged, not edited |
| R-d | `server.py::_validate_comms_charset` docstring still QUOTES the design doc's "same injection posture" — immediately corrected in the same docstring (#219) | quote + correction; OK |
| R-e | the log event `governed.owner_count.rejected` is retired with `_owner_count`; any external (Mezmo) query keyed on it goes silent | none found in-repo (awk over tests + scripts); surfaced |
| R-f | the new precondition reads are not index-served (an OR of compound predicates; a `sender.id` dereference) | one-shot cutover verb; not probed; surfaced |
| R-g | owner classification compares `str(owner)` to `Principal.id` — both the SDK's rendering (`_row_to_principal` sets `id=str(row["id"])`); a future change to how `Principal.id` is built would silently re-class the operator's rows as "other" | pinned indirectly: R-Q5-1 `[operator-owned]`/`[mixed-owners]` redden on a mismatch |
| R-h | a credentialed register now reads the agent row TWICE (the handler's `preflight`, then `register`'s own `preflight`) | inherent in the ruling (register calls preflight first; the handler calls it pre-mint); +1 SELECT |
| R-i | amendment 26 has no pin | ruled for 63c-i-b; behaviour probe §P.2 |
| R-j | the a19b a19b-§12 R-2 (the runtime spy treats any exception as refused) and adversary R-2/R-3 carry unchanged; R-3 (`_owner_count` orphaned) is CLOSED by DV-3 | carried / closed |
| R-k | `lore_search` (finding #490): the DRY query for a bounded-id render returned only this build's own `_id_sample` (the watcher had indexed the working tree) | no pre-existing equivalent surfaced |

## §5 RED@HEAD → GREEN (full suite ALONE, `-n 12`, 15 GB PID watchdog never fired, `spike-surreal` active, 0 other pytest at start)
| run | tree | tail |
|---|---|---|
| RED@HEAD baseline, 2026-09-26 10:14:24→10:23:24 | `scratch_copy.sh` copy of HEAD `a761b71` (PROVENANCE `…/scratchpad/headcopy/loremaster/loremaster/__init__.py`) | `108 failed, 11517 passed, 62 skipped, 3 xfailed, 7 warnings in 528.53s (0:08:48)` · EXIT=1 |
| BUILD, 2026-09-26 11:41:23→11:49:43 | the same copy + EXACTLY my six production files (`build_prod.patch`, md5 `b23f3e43416b9d0931dff1635ad53f85`; each file `cmp`-identical to the main tree) | `11625 passed, 62 skipped, 3 xfailed, 7 warnings in 494.60s (0:08:14)` · EXIT=0 |

- **All 108 RED@HEAD tests are GREEN on the build, and 0 previously-green tests are red:** the build run has ZERO failures over the identical test bytes, and the totals reconcile (108 + 11517 = 11625 = the build's passed count; 62 skipped / 3 xfailed identical). The count also equals the a19b SAT's `11625 passed` on its reference.
- **#486 did not appear** in either run (its node is absent from the red list; the build run has no failures at all).
- The 108, by file: `test_fixwave_a19a_63c_i_a.py` 53 · `test_fixwave_a19b_63c_i_a.py` 27 · `test_fixwave_a19_63c_i_a.py` 20 · `test_agent_governance_63c_i_a.py` 7 · `test_agent_registry.py` 1 (the a19b report §5 counts 80 = 53 + 27; the other 28 are the a19 round's pins, still red at `84af63f`-equivalent production). Every id, verbatim:
```
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[above-cap]
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[at-cap]
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[below-cap]
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[mixed-owners]
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[operator-owned]
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[perturbed-bound]
loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement
loremaster/tests/test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_blank_role_rule_is_the_SHARED_is_blank[handler]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestABlankRoleRegisterHasNoSideEffect63cIAa19::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestABlankRoleRegisterHasNoSideEffect63cIAa19::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestABlankRoleRegisterHasNoSideEffect63cIAa19::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[\t\n]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheIdentityRuleHasOneSpelling63cIAa19::test_both_refusals_serve_the_SAME_rule_and_it_is_the_pattern
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheIdentityRuleHasOneSpelling63cIAa19::test_the_served_rule_MOVES_with_the_shared_pattern
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheMessageOrderGuardIsScopeKeyed63cIAa19::test_CA_A_the_message_leg_refuses_the_store_the_agent_leg_refuses
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_all_four_tables_serve_the_SAME_teaching
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[brief]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[memory]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[message]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_ORDER_GUARD_reads_the_shared_function
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_VERB_LEVEL_check_reads_the_shared_function[agent]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_VERB_LEVEL_check_reads_the_shared_function[brief]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_VERB_LEVEL_check_reads_the_shared_function[memory]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_VERB_LEVEL_check_reads_the_shared_function[message]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[agent]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[brief]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[memory]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[message]
loremaster/tests/test_fixwave_a19_63c_i_a.py::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_the_id_render_ROUTES_through_the_shared_sanitise_line
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestADanglingSenderRefusesTheMessageLeg63cIAa19a::test_a_dangling_sender_refuses_the_message_leg_byte_inert[above-cap]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestADanglingSenderRefusesTheMessageLeg63cIAa19a::test_a_dangling_sender_refuses_the_message_leg_byte_inert[one-ghost]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestADanglingSenderRefusesTheMessageLeg63cIAa19a::test_a_dangling_sender_refuses_the_message_leg_byte_inert[two-ghosts]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestADanglingSenderRefusesTheMessageLeg63cIAa19a::test_a_hostile_dangling_id_cannot_forge_a_line
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestADanglingSenderRefusesTheMessageLeg63cIAa19a::test_the_dangling_decision_is_THE_shared_functions_in_BOTH_directions[shared-says-dangling]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestADanglingSenderRefusesTheMessageLeg63cIAa19a::test_the_dangling_decision_is_THE_shared_functions_in_BOTH_directions[shared-says-sound]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed63cIAa19a::test_the_refusal_names_both_operator_first_owners_unclassified[agent]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed63cIAa19a::test_the_refusal_names_both_operator_first_owners_unclassified[brief]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed63cIAa19a::test_the_refusal_names_both_operator_first_owners_unclassified[memory]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed63cIAa19a::test_the_refusal_names_both_operator_first_owners_unclassified[message]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-role-conflict]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[AgentIdentityConflictError-spawned-by-conflict]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-empty]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-ideographic]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[InvalidAgentIdentityError-blank-spaces]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[RetiredAgentError-retired]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_register_itself_decides_with_preflight_in_BOTH_directions
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_handler_decides_with_preflight_BEFORE_the_mint
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_the_RACE_compensation_deletes_only_a_keep_this_call_created[created-by-this-call]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestHalfPairsAreRefusedAtTheVerb63cIAa19a::test_an_ownerless_SCOPED_agent_refuses_every_table_as_half_applied[agent]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestHalfPairsAreRefusedAtTheVerb63cIAa19a::test_an_ownerless_SCOPED_agent_refuses_every_table_as_half_applied[brief]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestHalfPairsAreRefusedAtTheVerb63cIAa19a::test_an_ownerless_SCOPED_agent_refuses_every_table_as_half_applied[memory]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestHalfPairsAreRefusedAtTheVerb63cIAa19a::test_an_ownerless_SCOPED_agent_refuses_every_table_as_half_applied[message]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestHalfPairsAreRefusedAtTheVerb63cIAa19a::test_BOTH_half_pairs_together_are_refused_byte_inert[memory]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestNoServedCountStandsUnderAForeignNoun63cIAa19a::test_PD2_the_served_count_describes_the_set_its_noun_names
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestNoStampedMessageCarriesANoneOwner63cIAa19a::test_after_agent_then_message_no_stamped_message_has_a_NONE_owner[dangling-sender]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestNoStampedMessageCarriesANoneOwner63cIAa19a::test_after_agent_then_message_no_stamped_message_has_a_NONE_owner[half-pair-owned-unscoped]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestRefusalReceiptsServeOnlyWhatWasMeasured63cIAa19a::test_the_multi_principal_refusal_serves_no_unmeasured_count[agent]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestRefusalReceiptsServeOnlyWhatWasMeasured63cIAa19a::test_the_multi_principal_refusal_serves_no_unmeasured_count[brief]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestRefusalReceiptsServeOnlyWhatWasMeasured63cIAa19a::test_the_multi_principal_refusal_serves_no_unmeasured_count[memory]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestRefusalReceiptsServeOnlyWhatWasMeasured63cIAa19a::test_the_multi_principal_refusal_serves_no_unmeasured_count[message]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestSharingMovesInBothDirections63cIAa19a::test_K1_the_verb_does_not_refuse_when_the_shared_function_says_clean[agent]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestSharingMovesInBothDirections63cIAa19a::test_K1_the_verb_does_not_refuse_when_the_shared_function_says_clean[brief]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestSharingMovesInBothDirections63cIAa19a::test_K1_the_verb_does_not_refuse_when_the_shared_function_says_clean[memory]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestSharingMovesInBothDirections63cIAa19a::test_K1_the_verb_does_not_refuse_when_the_shared_function_says_clean[message]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestSharingMovesInBothDirections63cIAa19a::test_K2_the_order_guard_refuses_when_the_shared_function_says_unmigrated
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTableValidityIsCheckedFirst63cIAa19a::test_an_invalid_table_is_answered_not_supported_with_zero_store_io
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[blank-role]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[fresh-legal]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[illegal-name]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[matching-existing]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[mixed-pair-once-minted]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[owner-before-the-mint]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[retired]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[role-conflict]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree[spawned-by-conflict]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheIdentityRefusalsHaveAGoldenSkeleton63cIAa19a::test_the_registry_refusal_skeleton_is_the_golden[name]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheIdentityRefusalsHaveAGoldenSkeleton63cIAa19a::test_the_registry_refusal_skeleton_is_the_golden[session]
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheIdentityRefusalsHaveAGoldenSkeleton63cIAa19a::test_the_server_refusal_skeleton_is_the_golden
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_a_scoped_but_ownerless_message_is_never_restamped
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_EVERY_governed_legs_backfill_WHERE_is_scope_keyed
loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_the_message_backfill_EXECUTES_the_golden
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAFailedCompensationIsNamedToTheCaller63cIAa19b::test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[both-halves]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[owned-unscoped]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[scoped-ownerless]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_each_halfs_sample_is_bounded_by_THE_constant
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_the_message_half_pair_decision_is_THE_shared_functions
loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestBackfilledIsTheRowsStamped63cIAa19b::test_backfilled_is_the_rows_the_UPDATE_stamped_never_the_pre_count
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP2_the_dangling_sender_sample_reads_THE_constant
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP3_the_half_applied_id_sample_is_bounded_by_THE_constant
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[AgentIdentityConflictError-role-conflict]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[AgentIdentityConflictError-spawned-by-conflict]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[InvalidAgentIdentityError-blank-empty]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[InvalidAgentIdentityError-blank-ideographic]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[InvalidAgentIdentityError-blank-spaces]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[RetiredAgentError-retired]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[AgentIdentityConflictError-role-conflict]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[AgentIdentityConflictError-spawned-by-conflict]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[InvalidAgentIdentityError-blank-empty]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[InvalidAgentIdentityError-blank-ideographic]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[InvalidAgentIdentityError-blank-spaces]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[RetiredAgentError-retired]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP7a_the_order_refusal_serves_no_unmeasured_count
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP7b_the_dangling_refusal_serves_no_unmeasured_count
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count[agent]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count[memory]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count[message]
loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP8_both_half_pairs_are_both_named
```
- Interim (main tree, 10:35, before DV-2): the 11 contract/adjacent files → `1 failed, 1715 passed` — the one red was the link-5 render-candidate gate (DV-2), fixed; the build run above is after the fix.

## §6 Gate receipts (the isolated tree — DV-1)
```
$ uv run ruff check .            → All checks passed!
$ ./scripts/typecheck.sh         → typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK · skills OK · docs/eval OK · scripts OK · shellcheck OK (7 tracked .sh)
$ uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff
  typecheck    GREEN
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN …
CURRENCY   : FAIL — claimed but never run: pytest
```
- **Currency, read honestly:** both legs the brief names are GREEN; the tool's overall line reads FAIL solely because `--legs` excludes `pytest` (the brief forbids a bare `--currency`, #466). The pytest gate ran separately — §5, 0 failed. `scripts/pending_contracts.yaml` has NO 63c-i-a entry (`bounds: []`), so there was nothing to self-destruct; the file is untouched.
- **Main tree** (shared checkout, 11:0x, with peers' untracked/uncommitted files present): `ruff` RED only on `scripts/probe_reanchor_58.py` (E501, a packet-58 file); `typecheck` RED only in peers' files (`test_supersede_reanchor_58.py`, `test_task_guarded_shell_58.py`, `test_loopback_serving.py`, `test_no_raw_listener_in_test_trees.py`, `test_task_ledger.py`, `skills/lore-deploy/tests/test_loopback_home.py`). My six files: `ruff check loremaster/loremaster lorerunes/lorerunes` → All checks passed; `mypy` on principals/server/agents → no issues.
- **Mutation proof of the new shared `principals._operator_unresolved`** (brief-base §6: a shared thing is proven by mutation) — `scripts/mutation_proof.py` in the scratch tree; declared set from `--collect-only` BEFORE the run (KP7c ×3 = the memory/agent/message legs' operator refusals; R2 ×4 = the verb-level refusal); mutation = the shared sentence emptied:
```
7 failed, 89 passed in 45.98s
tree restored byte-exact (loremaster/loremaster/principals.py: md5 c5a998032ea8cab1f5d4c3d85420cf5c)
PROOF HELD — the declared RED set fired EXACTLY: [R2[agent|brief|memory|message], KP7c[agent|memory|message]]
```
  Every call site moved with the one function (a private copy at any site would have kept its test green).

### §P.2 `probe_am26_combined_refusal.py` (amendment 26 — no pin yet; the cold audit grades, i-b pins) — md5 `4529a084a7f96ec87eea9f663064049a`
Run 2026-09-26 ~11:52 on the scratch tree (PROVENANCE `…/scratchpad/headcopy/loremaster/loremaster/principals.py`), test store. Output, verbatim:
```
REASON: 1 legacy message(s) name a dangling sender — their `sender` link resolves to no agent row, so no owner can be derived from it. First 1 of 1 shown: message:m_ghost_000 (sender agent:ghost_sender_000). 1 message row(s) carry an owner but no scope — a half-applied store (one column of the governed pair was stamped without the other). First 1 of 1 ids shown: message:m_owned_unscoped. 1 message row(s) carry a scope but no owner — a half-applied store (one column of the governed pair was stamped without the other). First 1 of 1 ids shown: message:m_scoped_ownerless. Adjudicate these messages by hand before migrating `message`; no row was stamped
PASS combined: refused
PASS combined: byte-inert on every byte-inert table (sound row NOT stamped)
PASS combined: None receipts, backfilled 0
PASS combined: BOTH diagnoses named in ONE refusal
PASS combined: dangling FIRST (amendment 26 check order)
PASS combined: dangling count stated (1)
PASS combined: half (i) count stated (1)
PASS combined: half (ii) count stated (1)
PASS combined: ONE remedy sentence (one refusal, not two glued)
PASS CONTROL (a) clean store proceeds: MigrateGovernedResult(table='message', scanned=1, backfilled=1, already_migrated=0, refused=False, reason=None)
PASS CONTROL (b) ghost-only names only dangling
PASS CONTROL (b) half-pair-only names only half-applied
ALL PASS
PROBE_EXIT=0
```
```python
"""builder-63c-i-a-fix — amendment 26 behaviour probe (NO pin exists yet; the cold audit grades it, 63c-i-b pins
it). Fixture = the ruling's shape: ONE ghost-sender legacy message + ONE owned-but-unscoped message + ONE
scoped-but-ownerless message + ONE sound legacy message. Asserts: refused=True; ONE refusal naming BOTH
diagnoses; the dangling diagnosis FIRST (check order); each count stated; the sound row NOT stamped;
``SELECT *`` on every byte-inert table identical; None receipts. CONTROLS: (a) the same store WITHOUT the
three bad rows proceeds and stamps the sound row (so the refusal is caused by them); (b) ghost-only and
half-pair-only stores each name ONLY their own diagnosis (so "both" is not a constant string).
Test store only (spike-surreal ws://127.0.0.1:18000; NEVER :18500), throwaway DBs.
Run: cd <repo>/loremaster/tests && uv run python <this file>
"""

import asyncio
import sys

sys.path.insert(0, ".")

import test_fixwave_a19_63c_i_a as a19  # noqa: E402
import test_fixwave_a19a_63c_i_a as a19a  # noqa: E402
from _governed_contract import seed_message_legacy  # noqa: E402
from lorerunes.pdp import keep_scope  # noqa: E402
from surrealdb import RecordID  # noqa: E402

from loremaster import principals  # noqa: E402

FAILURES: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("PASS " if condition else "FAIL ") + label)
    if not condition:
        FAILURES.append(label)


async def seed(world, *, ghost: bool, owned_unscoped: bool, scoped_ownerless: bool) -> None:
    await a19a._seed_ghost_store(world, ghosts=1 if ghost else 0)  # migrated senders + m_sound (+ ghost)
    if owned_unscoped:
        await seed_message_legacy(
            world.connection, sender_id="sender_operator", session="gs", seq=50, row_id="m_owned_unscoped",
            owner_principal=RecordID("principal", world.operator_bare),
        )
    if scoped_ownerless:
        await seed_message_legacy(
            world.connection, sender_id="sender_operator", session="gs", seq=51, row_id="m_scoped_ownerless",
            scope=keep_scope("sessionkeepother"),
        )


async def main() -> int:
    async with a19._governed_world() as world:
        await seed(world, ghost=True, owned_unscoped=True, scoped_ownerless=True)
        before = await a19._snapshot(world.connection)
        result = await world.migrate("message")
        after = await a19._snapshot(world.connection)
        reason = str(result.reason or "")
        print("REASON:", reason)
        check(result.refused is True, "combined: refused")
        check(before == after, "combined: byte-inert on every byte-inert table (sound row NOT stamped)")
        check(result.scanned is None and result.already_migrated is None and result.backfilled == 0,
              "combined: None receipts, backfilled 0")
        dangling_at = reason.lower().find("dangling sender")
        half_at = reason.lower().find("half-applied")
        check(dangling_at >= 0 and half_at >= 0, "combined: BOTH diagnoses named in ONE refusal")
        check(0 <= dangling_at < half_at, "combined: dangling FIRST (amendment 26 check order)")
        check("1 legacy message(s) name a dangling sender" in reason, "combined: dangling count stated (1)")
        check("1 message row(s) carry an owner but no scope" in reason, "combined: half (i) count stated (1)")
        check("1 message row(s) carry a scope but no owner" in reason, "combined: half (ii) count stated (1)")
        check(reason.count("by hand") == 1, "combined: ONE remedy sentence (one refusal, not two glued)")
    async with a19._governed_world() as control:
        await seed(control, ghost=False, owned_unscoped=False, scoped_ownerless=False)
        result = await control.migrate("message")
        check(result.refused is False and result.backfilled == 1, f"CONTROL (a) clean store proceeds: {result}")
    async with a19._governed_world() as ghost_only:
        await seed(ghost_only, ghost=True, owned_unscoped=False, scoped_ownerless=False)
        reason = str((await ghost_only.migrate("message")).reason or "").lower()
        check("dangling sender" in reason and "half-applied" not in reason, "CONTROL (b) ghost-only names only dangling")
    async with a19._governed_world() as half_only:
        await seed(half_only, ghost=False, owned_unscoped=True, scoped_ownerless=True)
        reason = str((await half_only.migrate("message")).reason or "").lower()
        check("half-applied" in reason and "dangling" not in reason, "CONTROL (b) half-pair-only names only half-applied")
    print("PROVENANCE", principals.__file__)
    print("ALL PASS" if not FAILURES else f"{len(FAILURES)} FAILED")
    return 1 if FAILURES else 0


sys.exit(asyncio.run(main()))
```

### §P.3 runners (verbatim)
`run_suite.sh` — md5 `60b9df25744f73276cb870f3638689f4`
```bash
#!/usr/bin/env bash
# builder-63c-i-a-fix — wait (<=30 min) for a clear process table (2 consecutive clear checks 15 s apart; python/pytest/uv
# processes whose cmdline mentions pytest), then full suite ALONE on the main tree, -n 12 (>=23G) or -n 8 (>=20G),
# PID watchdog kills the pytest below 15 GB avail (polls 10 s). usage: run_suite.sh <logfile> [tree]
LOG=$1; L=${2:-/home/ejprice/PycharmProjects/lore}
others() { ps -eo comm,args | awk '($1 ~ /^(python|python3|pytest|uv)/) && /[p]ytest/' | wc -l; }
deadline=$(( $(date +%s) + 1800 )); clear=0
while [ $clear -lt 2 ]; do
  if [ "$(date +%s)" -gt $deadline ]; then echo "BLOCKED: other pytest live for 30 min $(date -Is)" > "$LOG"; exit 3; fi
  if [ "$(others)" -eq 0 ]; then clear=$((clear+1)); else clear=0; fi
  sleep 15
done
cd $L || exit 2
AV=$(free -g | awk 'NR==2{print $7}')
if [ "$AV" -ge 23 ]; then N=12; elif [ "$AV" -ge 20 ]; then N=8; else echo "BLOCKED: avail ${AV}G" > "$LOG"; exit 4; fi
{ echo "START $(date -Is) avail=${AV}G -n $N HEAD=$(git rev-parse --short HEAD)"; uv run python -c "import loremaster; print('PROVENANCE', loremaster.__file__)"; echo "spike-surreal: $(systemctl --user is-active spike-surreal.service)"; echo "other pytest at start: $(others)"; } > "$LOG" 2>&1
uv run pytest -n $N -q -p no:cacheprovider --tb=line -rf >> "$LOG" 2>&1 &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ]; then echo "WATCHDOG: killing $PID (avail < 15G) $(date -Is)" >> "$LOG"; kill $PID; fi
  sleep 10
done
wait $PID; echo "EXIT=$?" >> "$LOG"; echo "END $(date -Is)" >> "$LOG"
```

## §B Backup (brief COMMIT DISCIPLINE — nothing committed)
- Patch: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f11f841f-5a48-4be4-9ef4-db7b181287ba/scratchpad/builder-63c-i-a-fix.patch` — md5 `b23f3e43416b9d0931dff1635ad53f85` (= `git diff --binary` of the whole tree at 11:5x, byte-identical to the mine-only patch — the peers' tracked edits had left the diff by then; also = `build_prod.patch`, the bytes every gate ran). `git diff --stat`: 6 files changed, 619 insertions(+), 206 deletions(-).
- Files: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f11f841f-5a48-4be4-9ef4-db7b181287ba/scratchpad/builder-63c-i-a-fix-files/` — `cp -a` of every path in `git status --porcelain` (22 files: my 6 + this report + peers' untracked files, copied as the brief says, not claimed).

### Late note — HEAD moved under the report (2026-09-26 ~11:55)
- HEAD is now `5a43aeb` "test(58): contract — supersede re-anchor + task guarded-append extraction + #130": packet 58's RED-by-design contract (tests, `scripts/probe_reanchor_58.py`, `scripts/test_forgery_door_sweep.py`, and 58's own `scripts/pending_contracts.yaml` entries). `git diff --stat 5d549a1 HEAD -- loremaster/loremaster lorerunes/lorerunes loresigil lorescribe` is EMPTY — no production change and no overlap with my six files.
- **Bound, stated:** every gate in §5/§6 ran against `a761b71`'s TEST bytes (= `84af63f`'s contract + a19/a19a/a19b). A full suite at `5a43aeb` will additionally carry packet 58's owned RED contract, and I have NOT measured my build against 58's changed `scripts/test_forgery_door_sweep.py` / `test_task_*` edits. The cold audit re-running at the new HEAD should expect 58's reds (adjudicated in 58's `pending_contracts.yaml` rows) and nothing else.
- The isolated tree the gates ran on is kept for the auditor: `…/scratchpad/headcopy` (HEAD `a761b71` + `build_prod.patch`; provenance-verified). No git worktree was created.
