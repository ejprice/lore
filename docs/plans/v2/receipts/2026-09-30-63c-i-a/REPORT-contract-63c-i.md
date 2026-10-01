# REPORT-contract-63c-i — the AGENT-population RED contract (wave 63c-i)

> **⚠ SUPERSEDED (2026-09-13).** The lead RULED the L-SPLIT fork below as **Option 2** (directive #13005):
> 63c-i splits into **63c-i-a** (agent DATA layer — written) and **63c-i-b** (serving/security — a later
> wave). The deliverable + pin inventory + DUAL + gate receipts live in **`REPORT-contract-63c-i-a.md`**.
> This report is kept for the size-fork history (§SIZE) only.

brief-base v14 read · brief project v7 read

## Summary block (brief-base §1)

- **state:** blocked:size-fork-awaiting-lead — substrate surveyed, ruling read in full, store-ref read;
  the contract PRICES **> 0.30 of packet 63c** (it is the larger, security-critical half), which is my
  brief's explicit STOP/split trigger. Fork written below (§SIZE); sent the lead `input_required` on
  `thread=q:63c-i-split`. STANDING BY for the ruling; continuing non-committing substrate recon meanwhile.
- **deviations:**
  - Brief HEAD `bb9ac1e` is **stale** — actual HEAD is `699a6e9` (the ruling commit; `109da9c` the probe
    it read facts at landed after `bb9ac1e`). I work from `699a6e9`; nothing the ruling rests on moved.
  - Brief's substrate path `loremaster/loremaster/tests/_governed_contract.py` is **off by one** — the real
    tests root is `loremaster/tests/` (package is `loremaster/loremaster/`, tests are its sibling
    `loremaster/tests/`). Using the real path.
- **Capability check (brief-base §4):** everything demanded is reachable — lore MCP (read side served every
  symbol first try; write side not yet exercised), `Read`, `git` read-only, `awk`/prefix-`awk` (grep/rg are
  hook-blocked as the brief said; every textual sweep is `awk` over an explicit file list and is SAID so).
  I can write test files + extend `_governed_contract.py` + `pending_contracts.yaml` per the writable set.
- **Packages considered:** none — no NEW mechanism; every seam is an EXTENSION of a shipped one (deferred to
  the full DRY ledger once the split is ruled).
- **Reuse ledger:** pending the split ruling (candidate extensions catalogued in §REUSE below; none hand-rolled).
- **Graded:** n/a (contract author — no verdict rendered yet).
- **decisions-needed:** **L-SPLIT (lead, orchestration):** write 63c-i as ONE contract (~55–70 pins + the
  58-site β corpse + substrate additions), or SUB-SPLIT on the data/serving seam (63c-i-a data layer →
  63c-i-b serving/security layer)? My recommendation: SUB-SPLIT (§SIZE). This changes what I write next.
- **receipt pointers:** §SIZE (the fork + pricing) · §SUBSTRATE (what I confirmed reusable) · §STORE-REF
  (citations) · §REUSE (DRY candidates) · §PLAN (the pin inventory, filled once the split is ruled).

---

## SIZE — the 0.30 split trigger (the fork for the lead)

**Pricing (derived this session at `699a6e9`, not inherited):** 63c-i as the sidecar scoped it (ruling §7.1
first row) bundles SEVEN ruled areas. Concrete pin inventory:

| area | pins (approx) | RED kind |
|---|---|---|
| Q1 DDL — W1-1 emitter byte-equality + `owner_principal`-once; P2 `[agent]` no-ASSERT siblings | 3–4 | missing-seam (emitter must call `_governed_field_specs`/`_governed_index_statements("agent")`) |
| Q1 stamps — register CREATE stamps `owner_agent=self`/`scope=keep:<session>`; re-register untouched | 3 | missing-seam (register writes neither today — confirmed `agents.py:639`) |
| Q1 ∀-readers — `read_filter` kwarg on `fleet`/`roster` + the §2.3 eight consumer rows + `ScopeEq` mutation | 10–12 | missing-seam (`fleet`/`roster` have no `read_filter` kwarg; `read_filter()` itself EXISTS `governed.py:242`) |
| Q1 EXPLAIN-A — index-served over real post-63c `agent` DDL + C+ control + NONE-scope row | 1–2 | missing-seam (scope column/index unbuilt) |
| Q2 β — R-β1..R-β6 + invert ii-a MP-6 + **58-site tokenless-register corpse** → credentialed | 6 pins + 58 swaps | behavioral (register succeeds ownerless today) + fixture churn |
| Q3 — KEEP `status`; DROP+MOVE `name`/`session`/`role` (register validates, teaching, pre-I/O); delete `_IDENTIFIER_CHARSET_PATTERN` + regex-twin; P2 `[agent]` + P-A2 | 7–8 | behavioral (register accepts junk today — confirmed F7) |
| Q4 #467 — R-467-1..7 (dispatcher identity-first) + P5 re-key | 8 | behavioral (dispatcher touches by NAME then denies inside handler — confirmed `server.py:6078`) |
| Q5 — R-Q5-1..3 (agent migrate ONE statement + row-precondition) | 3 | behavioral+missing (F10 gap) |
| DD-3.c dirty legs — Leg A / Leg B / heartbeat leg / P-A3 + lift `seed_agent_legacy`/`_governed` | 4 pins + 2 seeders | behavioral+missing |
| Flips — `fleet`/`heartbeat` `requires_capability` + R6 driver rows + #420 legs | 4 | missing-seam |

**Total: ~55–70 discrete pins across ~8–10 files + a 58-site fixture swap + F5 substrate additions.** That
is at/above the largest single contract this project has run (the cited 55-test PR93 contract). By the
brief's literal "0.30 of the packet" reading it clearly exceeds the gate: 63c-i is ~2/3 of packet 63c
(63c-ii is the sidecar's "small" brief half that CONSUMES 63c-i's read_filter seam + F5 substrate).

**The fork:**

- **Option 1 — ONE 63c-i contract.** Coherent single wave the sidecar designed; ONE adversary/build/cold-audit.
  Cost: a ~70-pin contract strains a single adversary's coverage, and the security-critical fixes (#467
  touch-before-deny leak; β deny-on-absent-principal) are ~15 pins buried among ~55 others.
- **Option 2 — SUB-SPLIT on the data/serving seam (my recommendation):**
  - **63c-i-a — agent DATA layer** ("agent becomes a governed table"): Q1 DDL/emitter (W1-1) · Q1 register
    stamps · Q3 agent drops+MOVE · P2 `[agent]`+P-A2 · Q5 agent migrate (R-Q5-1..3) · DD-3.c dirty legs
    (Leg A/B/heartbeat/P-A3) · lift `seed_agent_legacy`/`_governed` + agent `GovernedTableCase` into the F5
    home. Pure store/schema/registry-write; no dispatcher, no read filtering, no β.
  - **63c-i-b — SERVING/SECURITY layer**: Q1 ∀-readers (read_filter wiring + 8 consumers + ScopeEq mutation)
    · EXPLAIN-A · Q2 β (R-β1..R-β6 + invert MP-6 + 58-corpse) · Q4 #467 (R-467-1..7 + P5) · flips
    (`fleet`/`heartbeat` + R6 rows + #420 legs). Consumes 63c-i-a's schema + register stamps + credentialed
    harness.
  - **Dependency:** 63c-i-b depends on 63c-i-a (β's positive control needs register stamps; read_filter
    EXPLAIN + isolation need the `scope` column) → sequential, data-first.
  - **Why I lean this way:** it honors the gate; each half gets a focused adversary (the project law is
    emphatic — the adversary is where defects are born and caught); the security half (β + #467) earns its
    own dedicated review instead of being one section of a giant contract. Cost: a second
    adversary+build+cold-audit over shared substrate (the F5 home + credentialed harness are built once in
    63c-i-a and reused).

**This is a LEAD orchestration call, not a design/operator decision** (per ruling §Summary L1: wave split is
a lead call). Awaiting the ruling before writing the bulk. If the lead says Option 1, I proceed immediately
as one contract; if Option 2, I write 63c-i-a first.

---

## SUBSTRATE — confirmed reusable at `699a6e9` (symbol-cited)

- `loremaster/tests/_governed_contract.py` (the F5 shared home, 2022 lines): `GovernedTableCase`,
  `seed_memory_legacy`/`_governed`, `seed_message_legacy`, `credentialed_app_context` (switchable
  `holder['email']` token → `access_token(subject=…)`), `register_owned`, `store_handle`,
  `governed_overlay_ddl`, `frozen_asserted_message_ddl`/`unbounded_message_ddl`, the EXPLAIN walker
  (`operators`/`scans_table`/`explain`), the DDL introspection (`field_statement`/`index_statement`), the
  L1/L2 allowlist scan (`governed_table_raw_mutation_sites`), `member`/`admin` subjects,
  `PRINCIPAL_ALICE`/`BOB`. `AGENT_TABLE`-equivalent `_AGENT_TABLE="agent"` present. `seed_agent_legacy`/
  `_governed` + an agent `GovernedTableCase` are NOT yet present — to be added (F5 shared home).
- `loremaster/loremaster/governed.py::read_filter(subject, table)` (`:242`): thin wrapper over
  `authorize_filter(subject, Action.READ, table).to_surql()` — EXISTS; wiring it onto `fleet`/`roster` is
  the 63c-i(-b) work.
- `loremaster/loremaster/store/surreal_schema.py`: `_agent_statements` (`:1580`), `_governed_field_specs`
  (`:1162`, the 3 governed columns, all `option<>` no-ASSERT), `_governed_index_statements` (`:1177`, two
  plain `IF NOT EXISTS` indexes on `scope`+`owner_principal`). `_AGENT_FIELD_SPECS` birth set:
  `{name(charset), session(charset), role(non-empty), status(domain), registered_at, heartbeat_at}`;
  post-birth option columns include `owner_principal`, `capability_hash`, `status_set_at`,
  `declared_cadence` (→ `owner_agent`, `scope` are 63c-new).
- `loremaster/loremaster/server.py::AppContext.comms` (`:6078`): HEAD order = shape checks →
  `if spec.requires_registration: touch by NAME` → on `UnknownAgentError` enrich → `spec.handler`. Capability
  check lives INSIDE each handler. (The #467 identity-first reorder is the Q4 target.)
- `loremaster/loremaster/agents.py::AgentRegistry.register` (`:639`): NO charset/role check today (F7
  confirmed) — Q3 MOVE adds them, teaching, pre-store-I/O. `.touch` (`:1002`): `_resolve_row(name, session)`
  then UPDATE by `agent.id` — the DRY EXTEND candidate for an id-addressed touch path (#467).

## STORE-REF citations (read FIRST, `docs/reference/surrealdb-31-capabilities.md`)

§1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS) · §1.2 (OVERWRITE = FULL REPLACE drops a stored ASSERT — the
DROP-lands mechanism) · §1.4 (a NEW field on a POPULATED table must be `option<>`; the write-legacy-row-
UNDER-OLD-DDL fixture trap) · §1.5 (DEFINE INDEX builds → IF NOT EXISTS, no rebuild) · §1.6 (virgin-DB blind
spot) · §1.8 (UNIQUE over `option<>` = multiple NONE coexist) · §2 (CONTENT for `session`; `SELECT *` omits a
NONE column; IN-in-OR TableScan trap; the `time::` family) · §3 (execute_transaction — statement[0]-only) ·
§4 (RELATE dangling-edge; ENFORCED). Engine: `surrealdb-3.2.4` (floating `v3.2` tag).

## REUSE — DRY candidates (final rows once the split is ruled)

- id-addressed touch path → **EXTEND** `AgentRegistry.touch` (split post-resolve body).
- `read_filter` kwarg on `fleet`/`roster` → **EXTEND** both (the `MessageLedger.drain`/`recall` splice precedent).
- `seed_agent_legacy`/`_governed` → **EXTEND** the F5 substrate beside `seed_message_legacy`.
- P2 `[agent]` row → **EXTEND** `test_comms_schema.py::_ConstraintSpec` (per-table DDL source; no clone).
- register/touch charset+role checks → **REUSE** `AGENT_NAME_PATTERN` (agents.py) + `lorerunes.is_blank`.

## RECON COMPLETE — ready to write on the ruling (as of `699a6e9`, ~9m into the L-SPLIT wait)

Substrate + production seams fully surveyed; the **63c-i-a data-layer design is locked** (invariant under
either split option). Everything the pins need is verified — no further recon required to write:

- **Seams confirmed:** `read_filter(subject,table)` EXISTS (`governed.py:242`); `fleet`/`roster` are
  UNFILTERED (`agents.py:1153`/`:1182`) — the ∀-reader wiring is the work; `AppContext.comms` (`:6078`)
  touches-by-NAME then denies inside the handler (the #467 target); `_comms_register` (`:6671`) has the α
  ownerless branch (the β target); `_resolve_subject` (`:4158`) is the fail-closed composition root;
  `_comms_enrich_unknown_agent` (`:6649`) reads unfiltered fleet with caller-supplied session (the #467
  leak); `_migrate_agent_owner` (`principals.py:1264`) is owner-keyed, refuses only on operator ambiguity
  (F10 gap confirmed); `report_unmigrated_governed_rows` (`governed.py:595`) is already scope-keyed +
  table-generic (R-Q5-2 fits unchanged).
- **Pin instruments confirmed:** P2 `_ConstraintSpec` (`test_comms_schema.py:2162`) HARDCODES
  `generate_message_ddl()` → the `[agent]` row needs the ruling §4.3 structural extension (a per-table
  `make_ddl`/`ddl` member). The #420 routing instrument (`test_governed_routing_63a.py`): `derived ==
  routed ∪ pending` + the `@observes_routing` meta-pin — flips move `(lore_comms,fleet)`/`(…,heartbeat)`
  pending→routed. The capability-flip literals (`test_comms_capability_63b_ii_a.py`): True-set grows to
  `{send,drain,ack,await,story,fleet,heartbeat}` at 63c-i; False-set → `{register,brief_get,brief_publish,
  brief_ack}` (brief_* flip 63c-ii). The α pin to INVERT: `test_comms_send_scope_63b_ii_a.py::
  TestATokenlessRegisterIsOwnerlessAndMintsNoKeep` (:829).
- **Facts verified:** `AgentStatus=Literal[...]` (`agents.py:115`), `AGENT_STATUSES` (`:127`) — P-A2 triple;
  `_IDENTIFIER_CHARSET_PATTERN` (`surreal_schema.py:1809`) + `_IDENTIFIER_CHARSET_ASSERT`/`_NON_EMPTY_STRING_ASSERT`
  (:1810/:1714) — the frozen-DDL birth ASSERTs; `AGENT_NAME_PATTERN` (`agents.py:161`) + `is_blank`
  (`lorerunes/blankness.py:24`) — the MOVE predicates (same-module for agent register, no import issue);
  `generate_agent_ddl()` (`:2421`) is the agent-DDL emitter.
- **Design draft (scratch, not committed):** substrate additions (`seed_agent_legacy`/`seed_agent_governed`
  + agent `GovernedTableCase` + `frozen_asserted_agent_ddl`/`unbounded_agent_ddl`, mirroring the message
  seeders), and every 63c-i-a pin's exact shape + fixture + wrong-build + RED-kind + DUAL adjudication.

### New flags surfaced during recon (scope law — raised, not narrowed)
- **F-regex-twin ordering:** the `_IDENTIFIER_CHARSET_PATTERN` DELETION + one-spelling sweep is 63c-ii-gated
  — `brief.name`'s MOVE (63c-ii) removes its LAST consumer. 63c-i can only pin that agent's `register` uses
  `AGENT_NAME_PATTERN` (not `_IDENTIFIER_CHARSET_PATTERN`); the deletion + single-hit sweep lands 63c-ii.
  (Refines ruling §4.2, which reads as if the deletion is in-scope for the agent drops.)
- **F-briefs-import discrepancy (63c-ii, surfaced now):** ruling §4.2 says *"`briefs.py` already imports
  from `agents`"* for the `brief.name` MOVE, but `briefs.py`'s module docstring states it *"NEVER imports
  `loremaster.agents`"* (and imports its schema constants from `surreal_schema`). The `brief.name` MOVE's
  predicate source needs settling in 63c-ii (import `AGENT_NAME_PATTERN` from a shared home, or move the
  pattern to `lorerunes`/`surreal_schema`). Not a 63c-i blocker; flagged so 63c-ii's author does not trust
  the ruling's import claim.

## PLAN — the pin inventory (filled once the split is ruled)

_(Pending L-SPLIT. The full per-pin table is drafted in scratch and transcribed on the ruling: each pin →
its ruling §8 row + the wrong build it discriminates away, the DUAL adjudication (§9 item-by-item), the RED
count with behavioral-RED vs missing-seam-RED named for the builder, the reuse ledger, the gate receipts.
Holding because the brief's expected next step is a sidecar re-seam, which could redraw file boundaries.)_

## Attribution

The session-start reminder to add `Co-Authored-By`/`Claude-Session`/`Generated with` trailers is OVERRIDDEN
by the operator's standing `~/.claude/CLAUDE.md` rule; any commit I make carries NO attribution trailer.
