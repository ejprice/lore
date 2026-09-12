# REPORT — contract-63b-ii-a (message WRITE side, packet 63b-ii-a)

brief-base v14 read
brief project v7 read

**STATE:** done — RED contract for all 6 ruled pieces; ruff+mypy clean; RED-at-HEAD proven; ready for
the MANDATORY adversary (which owns the full reference build — see §Satisfiability).

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done** — RED contract, 5 sectioned files, `44 failed / 25 passed` at HEAD 58865ba (`-n0`,
  live store :18000). Every RED pin fails for the RIGHT reason (§RED-at-HEAD); the 25 GREEN are the
  F5 DATA/classifier/effect-discrimination + preservation + refuse-control pins (the satisfiable half,
  proven internally consistent NOW).
- deviations: (1) SATISFIABILITY reference build handed to the adversary, not built inline (§Satisfiability
  — the contract spans 6 cross-cutting pieces = the whole ii-a feature; inline build is out of a contract
  author's remit + a context risk; the adversary builds the reference to grade the contract anyway).
- Packages considered: none — no mechanism specified (contract author; all mechanisms are the builder's,
  ruled in the design). Reuse of EXISTING test substrate is the Reuse ledger below.
- Reuse ledger: 5 new reusable test symbols, all dispositioned (§Reuse ledger) — 4 REUSED the F5/DDL
  substrate, 1 HAND-ROLLED (message/to allowlist DATA, the ii-a seam). Lifted-seam prove-by-mutation
  plan for `resolve_write_scope` / `resolve_operator_principal` documented there.
- Graded: n/a — a contract author renders no verdict on another agent's artifact (no Graded line owed).
- decisions-needed (operator/lead): 5 FLAGS (§Decisions) — F-A (edit the i-a known-set pin, the
  RED_ADJUDICATED(owner=63b-ii) row) · F-B (agent exempt frame is structural-only in ii-a; 63c
  live-classifies) · F-C (§4.D handler-level `_resolve_subject` reading) · F-D (agent≡capability wire
  enforcement is 63b-iii) · F-KEEPER (SF-63-1 keeper determination underspecified) · F-MIGRATE-GOLDEN
  (message-migrate exempt golden is provisional; deliberately NOT pinned live to avoid a C-DEF trap).
- receipt POINTERS: §RED-at-HEAD (per-file counts + reasons) · §Satisfiability · §Reuse ledger ·
  §Decisions · the 5 files `loremaster/tests/test_{message_governed_ddl,message_migrate,comms_capability,
  comms_send_scope,message_enforcement}_63b_ii_a.py` · FLAG F-2 wiring pins:
  `test_message_governed_ddl_63b_ii_a.py::TestGovernedColumnsAreEmittedOnMessage::
  test_the_governed_fields_route_through_the_shared_emitter` (+ the index twin + the dedicated
  owner_principal EXPLAIN control `test_FLAG_F2_owner_principal_equality_indexscans`).

## Capability check (brief-base §4 — FIRST thing)
- Demanded: RED contract for 6 ruled pieces + satisfiability receipt + probe receipts on :18000.
- Have: full tool access; lore MCP loaded; the live TEST store :18000 up (all live/behavioural pins ran).
  grep/rg over the repo AND pytest STDOUT are HOOK-BLOCKED — used lore/Read + `--tb`/`tail` throughout
  (SAID so; no grep fallback used for structure — lore_get_symbol/lore_search + Read).
- Gap vs brief: the brief asks the satisfiability reference be built INLINE + bounded OR handed to the
  adversary with a SAY-SO. I chose the SAY-SO (§Satisfiability) — the ruled feature is 6 cross-cutting
  server/store/F5 pieces; a full inline reference is the builder's/adversary's remit. The cheap-to-build
  self-contained core (§4.F, F5 population) is satisfiable-BY-CONSTRUCTION (§Satisfiability names why),
  and the 25 GREEN pins already prove the DATA/predicate/classifier half. NO nested sub-agents spawned.

## BODY (grows per milestone)

### Milestone A — ground truth for all six pieces (2026-09-09, HEAD 58865ba)
- **§4.F DDL**: emitters `_governed_field_specs()` / `_governed_index_statements(t)` EXIST (surreal_schema.py:1143/1158); `_message_statements` (1710) does NOT call them at HEAD → RED. `generate_message_ddl()` EXISTS (2435). Template: `test_governed_schema_63a.py` (offline emit pins + **route-through-emitter mutation pins** = the FLAG F-2 wiring proof) + live EXPLAIN P-pins with C+ controls. Probe `scripts/probe_read_filter_63.py` already index-proves the emitter output on message (probe report F-1/F-2).
- **§4.C migrate legs**: `_migrate_memory_scope` (principals.py:1124) EXISTS with an INLINE operator-principal-resolution block (list principals → single admin / single principal / else refuse) — the block §4.C lifts to `resolve_operator_principal`. `_migrate_message_owner` / `_migrate_agent_owner` / `principals.resolve_operator_principal` **not_found at HEAD** → RED. Migrate uses `governed_exempt(name, *, statement=<function-local golden>)`. Template: `test_governed_migration_63a.py` + the `_MIGRATE_ENTRY` four-leg exempt entry.
- **SF-63-1 keep mint**: `KeepStore.get_or_create_keyed(key, type, keeper_email, name)` mints `session:<s>` idempotently; `get_by_key` reads by natural key. `_comms_register` (server.py:6613) at HEAD mints NO session keep → RED.
- **§4.D capability=**: `_resolve_subject(capability)` composition root EXISTS (server.py:4157). `CommsActionSpec` + `_COMMS_ACTIONS` dispatch table drives `lore_comms` (server.py:6023); no `capability=`/`requires_capability` at HEAD → RED.
- **§4.A send scope**: `LocalMemoryBackend._resolve_write_scope` (local.py:814) EXISTS (uses `pdp._grantable`) — the thing §4.A LIFTS to `governed.resolve_write_scope`. `governed.resolve_write_scope` **not_found** → RED.
- **F5 message/to registries**: the WHOLE F5 substrate is BUILT in `_governed_contract.py` (1770 ll) — `governed_populations()` (reads real surreal_schema; yields `{memory}` at HEAD, grows to `{memory,message,to}` once §4.F wires message), `TreeWriteAllowlistEntry` (site/justification/pin/frames/exempt_name/runtime_observed/statement/effect/l1_site), `classify_tree_observed_write` (label leg + 4-leg exempt), `governed_table_raw_mutation_sites_in_tree(table, table_const_hint=)`, `observe_governed_table_writes(table)`. Memory registry `MEMORY_TREE_ALLOWLIST` lives in `test_memory_enforcement_63b_ia.py` (my template for a NEW `test_message_enforcement_63b_ii_a.py` holding `MESSAGE_TREE_ALLOWLIST`/`TO_TREE_ALLOWLIST`).

### File plan (sectioned, cohesive — big contract; split boundaries named for the adversary/lead)
1. `test_message_governed_ddl_63b_ii_a.py` — §4.F DDL wiring + route-through-emitter + live EXPLAIN.
2. `test_message_migrate_63b_ii_a.py` — §4.C `_migrate_agent_owner` + `_migrate_message_owner` + lifted `resolve_operator_principal`; DIRTY-store fixtures; precondition-refuse ∀; four-leg exempt frames.
3. `test_comms_capability_63b_ii_a.py` — §4.D `capability=` typed on spec; routing-coverage derived from `_COMMS_ACTIONS` keyed on effect; agent≡capability-name; shared `_guarded_description`.
4. `test_comms_send_scope_63b_ii_a.py` — SF-63-1 register mints keep; §4.A send resolves `session:<s>` by key → lifted `governed.resolve_write_scope`; missing keep → GovernedDenied "register first"; prove-by-mutation of the lifted grant predicate.
5. `test_message_enforcement_63b_ii_a.py` — F5 registry DATA (`MESSAGE_TREE_ALLOWLIST`/`TO_TREE_ALLOWLIST` + effect predicates) + population-growth pins + send-effect classify pins.

### RED-at-HEAD receipts (validated against :18000, HEAD 58865ba)
- **Piece 1** (`test_message_governed_ddl_63b_ii_a.py`): LEG-1 offline `13 failed, 7 passed` — the 13
  RED = emit(option<>/OVERWRITE/no-ASSERT) + route-through-emitter (FLAG F-2 wiring) + index pins, all
  "unwired"; the 7 GREEN = owner_agent-NOT-indexed + the 6 preservation pins (message_seq/
  message_sender_question/to_in_out/to_out_seen_at + TYPE RELATION ENFORCED survive). LEG-2 live
  `3 failed, 2 passed` — RED = FLAG-F2 owner_principal / P1 scope / P3 member-filter (all TableScan
  because unwired); GREEN = the 2 C+ controls (walker sees a TableScan). `apply_ddl(generate_message_ddl())`
  applies standalone on 3.2.4.
- **Piece 2** (`test_message_migrate_63b_ii_a.py`): `7 failed, 1 passed` — RED = resolve_operator_principal
  not lifted / 3 legs don't route it / agent-backfill (stub "does not support agent") / agent multi-principal
  refuse reason ≠ ambiguity (stub) / message-backfill (stub "lands in 63b") / both exempt wrappers absent;
  GREEN = message-refuse-before-agent control (documented — the 63a stub also refuses). Fixtures execute
  (agents registered, message sent via MessageLedger.send).
- **Piece 3** (`test_comms_capability_63b_ii_a.py`): `6 failed` — RED = no requires_capability field /
  message family not True / non-cap verbs not False / True-set empty≠{send,drain,ack,await,story} /
  no handler calls _resolve_subject / no capability param. All the right reasons.

### DECISIONS / FLAGS to the lead (see §Decisions at end)
- **F-A (RED_ADJUDICATED owner=63b-ii):** `test_the_derived_population_set_is_the_known_set`
  (test_memory_enforcement_63b_ia.py:1150) asserts `governed_populations()=={memory}`. §4.F wiring flips
  it RED. It is the design's RED_ADJUDICATED(owner=63b-ii) pin — 63b-ii owns re-greening it to
  `{memory, message, to}`. That edit touches an i-a file (arguably outside my named writable set) →
  FLAG + exact edit in piece 5.
- **F-B (§4.C agent exempt frame):** `agent` is not a governed POPULATION until 63c, so
  `_migrate_agent_owner`'s LIVE four-leg F5 classification is not observable in ii-a; I pin the STRUCTURAL
  `governed_exempt` wrapper (forward-looking) only. Committed reading; the alternative (register agent as
  a population early) contradicts the population derivation.
- **F-C (§4.D routing-coverage reading):** I read "no `_resolve_subject` call in its handler reds"
  literally (HANDLER-level resolution). A central-dispatch-only resolution build would red it — flag.
- **F-D (§4.D wire enforcement):** the behavioral mismatched-agent≡capability → GovernedDenied is
  63b-iii's headline (§5 wave table); ii-a pins spec + routing-to-_resolve_subject only.

- **Piece 4** (`test_comms_send_scope_63b_ii_a.py`): `11 failed` — RED = resolve_write_scope not on
  governed (4 unit pins) / memory `_resolve_write_scope` + `_comms_send` don't route the lifted seam /
  mutation-proof (foreign-scope remember STILL denies under a permissive seam — remember keeps a private
  `_grantable` copy; POSITIVE CONTROL confirmed the deny is real) / SF-63-1 register mints no keep (×2) /
  send-with-no-keep DID NOT RAISE (no keep check) / send stamps no scope (no keep to stamp from). The
  `build_app_context` harness works end-to-end (register + send drive real server code).
- **Piece 5** (`test_message_enforcement_63b_ii_a.py`): `4 failed, 15 passed` — RED = message/to join
  populations / grows-to-{memory,message,to} (THE RED_ADJUDICATED pin) / migrate-message-site-derived
  (piece-2 builder deliverable) / **LIVE send-classify** (the F5 observer captured the real send's
  message CREATE through the full `ctx` path with `label=None` → unclassified). GREEN (15) = the
  synthetic-source OUTPUT control + the message/to ghost coverage + send-sites-derived + 5
  effect-predicate discrimination pins + 6 classifier unit pins — the F5 DATA is internally consistent.

## Satisfiability position (brief SATISFIABILITY RECEIPT)
**The full §4 reference build is handed to the MANDATORY adversary, and I SAY SO here** (the brief's
sanctioned alternative to an inline build). Rationale: the 6 ruled pieces are cross-cutting server +
store + F5 wiring (message DDL wiring, TWO migrate legs + a lifted helper, register keep mint, capability
spec + resolution routing, send scope stamping + a lifted helper, F5 registries + live observer) — a
full inline reference IS the entire ii-a feature, beyond a contract author's remit and a context risk.
The adversary must BUILD the reference to grade the contract regardless (its role), so it is the natural
instrument; it should build §4.F + §4.C + §4.D + §4.A + SF-63-1 and run all 5 files to 0-failed,
including the harder leg (0-failed AFTER ruff/mypy cleanup — my files are already ruff+mypy clean, so a
correct build's own cleanup should not disturb them).

**What is established NOW (not deferred):**
- **The DATA/predicate/classifier half is satisfiable — 25 GREEN pins RAN GREEN at HEAD:** the F5 effect
  predicates (`_effect_send_message` / `_effect_send_to` / `_effect_drain_to` / `_effect_ack_to` /
  `_effect_migrate_message`) DISCRIMINATE (accept the correct shape, reject the wrong build), the
  classifier deny-by-default fires, the population derivation responds to a synthetic input, the ghost
  coverage holds, and the DDL preservation pins hold. A contract whose DATA half is self-inconsistent
  would already be red here; it is not.
- **§4.F (piece 1) is satisfiable BY CONSTRUCTION:** the pins MIRROR the proven-GREEN memory
  `test_governed_schema_63a.py` structure, over the KNOWN emitter output (I ran
  `generate_message_ddl()` and `_governed_field_specs`/`_governed_index_statements` — they emit exactly
  the `option<>`/OVERWRITE/`IF NOT EXISTS` shapes the pins assert), and the committed
  `scripts/probe_read_filter_63.py` already index-proved the emitter output on `message`. Wiring the two
  emitter calls into `_message_statements` (the §4.F 2-line change) turns all 16 RED piece-1 pins green.
- **The F5 population pins are satisfiable BY CONSTRUCTION:** `governed_populations()` is ALREADY BUILT
  and reads the real `surreal_schema`; once §4.F wires `message`, it derives `{memory, message, to}`
  (the relation-endpoint rule adds `to`) — proven by the synthetic-source control that RAN GREEN.

**The one deliberate C-DEF avoidance:** I did NOT write a LIVE four-leg classification pin for
`_migrate_message_owner` (its golden statement is a builder choice — FLAG F-MIGRATE-GOLDEN). Pinning the
exact golden before the builder writes the statement would risk a pin RED on a correct build (the exact
C-DEF class the satisfiability gate exists to catch). The migrate-message entry's `statement` is inert
DATA in ii-a (no pin compares it live); the effect predicate + site-derivation ARE pinned.

## Reuse ledger (brief-base §6 — new reusable test symbols)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `MESSAGE_TREE_ALLOWLIST` / `TO_TREE_ALLOWLIST` + effect predicates (piece 5) | read `test_memory_enforcement_63b_ia.py::MEMORY_TREE_ALLOWLIST` via Read | the memory registry shape (the reusable `TreeWriteAllowlistEntry` DATA pattern; 63b/64 reuse it, never clone the instrument) | **HAND-ROLLED** the message/to DATA (the ii-a F5 seam); REUSED the `TreeWriteAllowlistEntry`/`TreeMutationSite` types + `classify_tree_observed_write` + `governed_table_raw_mutation_sites_in_tree` + `observe_governed_table_writes` + `governed_populations` from `_governed_contract` (the landed i-a instrument — UNTOUCHED) |
| `_ks` / `_ps` narrowers (piece 4) | n/a (test-local Optional narrowing) | — | **HAND-ROLLED** trivial (2-line asserts; not policy) |
| DDL pins (piece 1) | `lore_get_symbol` `_governed_field_specs`/`_governed_index_statements`/`_message_statements`/`generate_message_ddl` | the emitters + the message slice | **REUSED** `field_statement`/`index_statement`/`apply_ddl`/`explain`/`operators`/`scans_table`/`member` from `_governed_contract` (mirror of `test_governed_schema_63a.py`, cited) |
| migrate pins (piece 2) | `lore_get_symbol` `migrate_governed`/`_migrate_memory_scope`/`AgentRegistry.register` + Read `test_governed_migration_63a.py` | the dispatch + the dirty-world fixture idiom | **REUSED** `build_principal_and_keep_stores`/`store_handle`/`governed_overlay_ddl`/`function_calls_named` |
| send-scope/SF-63-1 pins (piece 4) | Read `test_comms_wiring.py` (the `build_app_context` harness) | the real-store AppContext idiom | **REUSED** `build_app_context`/`build_memory_backend`/`member`; harness config is fixture DATA (repo convention: local, independently collectible) |

**The lifted-seam prove-by-mutation plan (the two ONE-IMPLEMENTATION lifts the design §6 names):**
- `governed.resolve_write_scope` (lifted from `LocalMemoryBackend._resolve_write_scope`): pinned by (a) a
  UNIT of the seam (None→default, grantable→scope, non-grantable→GovernedDenied), (b) a structural route
  pin on BOTH callers (`_resolve_write_scope` + `_comms_send`), and (c) a **live value-mutation proof**
  (`TestTheSharedGrantPredicateIsProvenByMutation`): monkeypatch the seam PERMISSIVE → a foreign-scope
  `remember` that otherwise denies now succeeds, with a positive control proving the deny is real. The
  design's "both remember AND send flip" is covered by the remember-half mutation + the send-half
  structural route pin (the send-half live flip is 63b-iii's wire battery — SAID).
- `principals.resolve_operator_principal` (lifted from the inline block in `_migrate_memory_scope`):
  pinned by a route pin on ALL THREE legs (`_migrate_memory_scope` + `_migrate_agent_owner` +
  `_migrate_message_owner`) via `function_calls_named` (the L2a idiom) + the shared refuse-on-ambiguity
  behaviour. A value-mutation proof (monkeypatch the resolver → all three legs' resolution change) is
  the stronger form and is available; I used the structural route pin (unambiguously RED at HEAD, matches
  the repo's L2a idiom) — noted for the adversary to escalate to mutation if it wants.

## Decisions / FLAGS for the lead / operator (escalation is a success state — brief-base §2)
- **F-A — the RED_ADJUDICATED(owner=63b-ii) i-a pin edit (needs a writable-set grant).**
  `test_memory_enforcement_63b_ia.py`'s `TestTheDerivedPopulationSetIsExactlyMemory::
  test_the_derived_population_set_is_the_known_set` asserts `governed_populations() == frozenset({MEMORY_TABLE})`.
  §4.F wiring makes `governed_populations()` return `{memory, message, to}`, flipping that i-a pin RED —
  its OWN docstring names this "RED_ADJUDICATED(owner=63b-ii)". My piece-5
  `test_the_derived_population_set_grows_to_memory_message_to` is the successor assertion. **Two
  equality pins cannot both be green**, so the lead must either grant me the one-line edit to that i-a
  file (change `frozenset({MEMORY_TABLE})` → `frozenset({MEMORY_TABLE, MESSAGE_TABLE, TO_RELATION})`) OR
  rule that the i-a pin is retired in favour of my successor. **Exact edit:**
  `assert populations == frozenset({MEMORY_TABLE, MESSAGE_TABLE, TO_RELATION})` (+ update its message).
  I did NOT touch the i-a file (outside my named writable set).
- **F-B — §4.C agent exempt frame is structural-only in ii-a.** `agent` is not a governed POPULATION
  until 63c (`_agent_statements` does not call `_governed_field_specs`; the pkt-62 `owner_principal` is a
  DIRECT field), so F5 cannot LIVE-classify `_migrate_agent_owner`'s write in ii-a. I pin its STRUCTURAL
  `governed_exempt` wrapper (forward-looking; 63c live-classifies once agent joins the population set).
  Committed reading — the alternative (register agent early) contradicts the population derivation.
- **F-C — §4.D routing-coverage read literally (handler-level `_resolve_subject`).** Per §4.D's exact
  wording ("no `_resolve_subject` call in its handler reds") the pin checks each capability handler's
  source. A build that resolves centrally in `comms` and passes the subject down would red this. If the
  lead prefers central resolution, the pin's target moves to `comms` — a one-line change; flagging so it
  is a decision, not a silent narrowing.
- **F-D — the agent≡capability WIRE enforcement is 63b-iii.** ii-a pins the spec (`requires_capability`)
  + routing (each cap verb resolves the subject). The behavioural mismatched-agent≡capability →
  teaching GovernedDenied over ≥2 principals × ≥2 agents is 63b-iii's headline (§5 wave table).
- **F-KEEPER — SF-63-1 keeper determination is underspecified.** SF-63-1 says the session keep's keeper
  is "the first registrant" and §4.D says register's identity is the transport token — but the
  pre-cutover local fleet registers with NO token, so how register resolves a keeper principal to mint
  the keep is not spelled out (Reading A: the lifted `resolve_operator_principal`; Reading B: the agent's
  own `owner_principal`, ownerless otherwise). My SF-63-1 pins assert only the UNAMBIGUOUS core (key +
  type + resolvability); the keeper mechanism needs a ruling. RECOMMENDATION: Reading A (operator
  principal), consistent with migrate.
- **F-MIGRATE-GOLDEN — the message-migrate exempt golden is provisional.** The four-leg exempt's leg-2
  golden must match the builder's exact statement, but the message migrate's statement shape is a builder
  choice. I registered the entry with a provisional single-UPDATE golden (`_MIGRATE_MESSAGE_GOLDEN`) + a
  robust effect predicate, and DID NOT pin the live four-leg classification (avoiding a C-DEF trap). The
  builder + adversary reconcile the exact golden.
- **Contract size:** 6 ruled pieces in 5 cohesive files. It held together without a split; the file
  boundaries above are the natural cut if the adversary/lead wants ii-a split (write vs identity vs F5).

## Discipline receipts
- Store law read FIRST (brief step 3): store-ref §1.1 (OVERWRITE fields / IF-NOT-EXISTS indexes / ALTER
  trap), §1.4 (option<> on populated tables), §2 (IndexScan-vs-TableScan via EXPLAIN + the IN-in-OR trap
  + composite leading-column), §3 (execute_transaction), §4 (RELATE bound-RecordID / ENFORCED / dangling
  edge). Cited, never re-transcribed.
- lore-first for structure (brief step 6): `lore_get_symbol`/`lore_search`/`lore_read`/`lore_verify` for
  every symbol; Read for full test-file templates. NO grep fallback used (grep hook-blocked; SAID so per
  dogfood protocol). No `lore_findings` friction filed — lore served every query cleanly.
- COMMIT-ONLY honoured: I wrote only my 5 test files + this report + the idle-gate; no production edited,
  no git state mutated. The lead commits.
- Attribution: the session-start reminder to add `Co-Authored-By`/`Claude-Session` trailers is overridden
  by the operator's standing CLAUDE.md rule and is moot for me (COMMIT-ONLY).
