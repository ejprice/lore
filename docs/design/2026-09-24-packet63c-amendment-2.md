# Packet 63c — ruling amendment 2: the adversary's forks (MP-10 · MP-12 · R5), the predicate home (MP-9), and ONE reviser worklist (sidecar-63c-2, 2026-09-24)

Amends `docs/design/2026-09-13-packet63c-remainder-ruling.md` (`699a6e9`) after amendment 1 (`c4728b1`).
Inputs: `REPORT-adversary-63c-i-a.md` (`b46d3f2`, INSUFFICIENT + UNSATISFIABLE on `0b8ce37`),
`REPORT-sidecar-63c-2.md` (`043f960`), the lead's adoption of D1–D3 (`f89a1ae`). Operator ruling
2026-09-24: the sidecar is the authority on design forks; only MAJOR scope/architecture goes to the
operator — **§E names the one item I judge major enough to surface** (the predicate's move into
`lorerunes`, a fourth workspace member gaining a symbol). Everything else here is a HOW inside the
confirmed scope. Facts cited were read at HEAD `f3c25df` (no production symbol has moved since `0b8ce37`).

## A. Rulings

### A1 — MP-10: `briefed` IS a governed population from 63c-i-a; the resolver is fixed in i-a; its F5 case lands in 63c-ii
- **The derivation's rule is right and its resolver is wrong.** `governed_populations()` (`_governed_contract.py`)
  = `{t : _<t>_statements calls _governed_field_specs}` ∪ `{relations whose IN or OUT ∈ that set}`.
  `_schema_string_constants` resolves a `Name` endpoint only through module-level `NAME = "literal"`
  assigns; `AGENT_TABLE` and `PRINCIPAL_TABLE` are `from lorerunes import X as X` re-exports
  (`surreal_schema.py:40/43`, defined `lorerunes/pdp.py:72-73`) → they resolve to `None`. Every relation call
  in the module, read: `blocks(task,task)` · `briefed(AGENT_TABLE, brief)` · `to(message, AGENT_TABLE)` ·
  `refers/answers_to(code_node, name)` · `member_of(PRINCIPAL_TABLE, keep)`. So `to` joined at ii-a by the
  luck of its IN being a resolvable constant, and on a correct i-a build `briefed` — whose IN is the
  governed `agent` — does NOT join. A reach that resolves one endpoint spelling and not another is the
  instrument-lesson's seventh-defeat shape (a hidden constant in the reach), so it is fixed **in i-a**, the
  wave that makes it observable — never left "until ii, when `brief` makes it join anyway".
- **The fix (test substrate, the reviser's):** `_schema_string_constants` gains an `ImportFrom` leg — for each
  module-level `from <m> import <name> [as <alias>]`, `constants[alias or name] = getattr(import_module(m),
  name)` when that attribute is a `str`; non-`str` attributes are skipped. Importing the REAL `lorerunes` for a
  synthetic source is honest: `lorerunes` is the stdlib-only constants home and its value IS production
  truth. **Pin (extend the existing reach pin, one pin):** a synthetic source carrying
  `from lorerunes import AGENT_TABLE as AGENT_TABLE`, an `_agent_statements` that calls
  `_governed_field_specs`, and `_define_relation_table('edge', AGENT_TABLE, 'x')` → `'edge'` joins; negative
  control: a re-export of a non-`str` attribute does not resolve and its relation does not join.
- **What "governed" means for a relation (the `to` precedent, ii-a):** no governed columns on the edge
  (`_TO_CONSTRAINT_SPEC`'s floor is `{ack_note}`); its READS ride the endpoint's filter; its WRITES are
  attributed (`write_guard` labels + allowlist evidence) and F5-observed as a population. For `briefed`:
  reads = `coverage`/`behind` over the VISIBLE roster (ruling §2.3 row 4) and the head brief (ii); writes =
  `brief_ack`'s RELATE and register's auto-ack RELATE (§3.5). **Every `briefed` writer is a 63c-ii verb**, so
  its F5 case (seeders, write verbs, labels, evidence) lands in **63c-ii** beside them — exactly as `to`'s
  landed with `drain`/`ack`.
- **The i-a known set is therefore `{agent, briefed, memory, message, to}`** (`member_of` stays out: neither
  `principal` nor `keep` is governed). There is NO "every population has a case" pin — the exact-set pins ARE
  the adjudication point (their docstring: *"REDDENS a SURPRISE governed population with no F5 case"*), so the
  i-a edit adjudicates `briefed` in its docstring: *joined at i-a by derivation; F5 case owed by 63c-ii.*
  **Two exact-set pins assert one fact** (`test_memory_enforcement_63b_ia.py` and
  `test_message_enforcement_63b_ii_a.py`) — the reviser edits both to the five-set now and folds them to ONE
  (delete the ia copy with a DUAL comment pointing at the ii-a pin, which owns the growth story) — a
  second copy of a known-set is where the next wave's edit reaches one and not the other.

### A2 — MP-12: the registry stamp input is `session_keep_id`; the forbidden-name pin is re-keyed to the SAFE set; fakes mirror the writer; no conditional splat
- **The seam.** `AgentRegistry.register(..., owner_principal_id: str | None = None, session_keep_id: str | None
  = None)`. The caller (`_comms_register`) passes the bare id of THE session keep it just minted/joined
  (`session_keep.id` — the same keep the SF-63-1 foreign gate checked one line earlier); the REGISTRY forms
  `scope = keep_scope(session_keep_id)` through the ONE formatter (`lorerunes.pdp.keep_scope`) and stamps
  `owner_agent = RecordID(AGENT_TABLE, agent_id)` — both inside the SAME `CREATE … CONTENT` as the capability
  hash (atomic, mint-once). This is `owner_principal_id`'s exact twin: a bare server-derived id in, a typed
  link/scope formed inside the writer. A `scope: str` kwarg (the adversary's first ref) would let any caller
  hand the registry an arbitrary scope string — `server`, a foreign keep — which is the display-owner class
  the pkt-62 pin exists for; `session_scope` (its second ref) is that same kwarg renamed to walk past a
  name list. Neither is the seam. **Mutation pin:** perturb `keep_scope`'s prefix → the stamped scope moves
  (a private `f"keep:{…}"` in the registry stays green = RED).
- **The forbidden-name pin (`test_agent_capability.py::test_register_exposes_no_display_owner_argument`) is
  re-keyed, not deleted.** It enumerates the forbidden (`{"owner","as_agent","created_by","scope"}`) — the
  antipattern six defeats taught — and its real property is *"the registry's provenance inputs are
  server-derived only and unreachable from the wire."* Allowlist the safe: (i) the registry's
  provenance-bearing kwargs are EXACTLY `{owner_principal_id, session_keep_id}` (an exact-set pin — a third
  is a deliberate edit that reds it); (ii) the wire surface is DERIVED, not listed: `_COMMS_ACTIONS["register"].params`
  ∩ `{owner_principal_id, session_keep_id}` = ∅, and the existing F4 foreign-param fuzz keeps refusing
  `owner=`/`as_agent=`/`created_by=`/`scope=` at the MCP layer (ruling §2.2: *no `scope=` argument on any
  63c verb*). Docstring re-dated; the pkt-62 virtue is carried by (i)+(ii).
- **Fakes mirror the writer.** `_comms_fakes.FakeAgentRegistry.register` gains `session_keep_id` and stamps
  `scope`/`owner_agent` on its fake row the way the real writer does (the §9 item 6 `_comms_fakes` clause:
  *the fake mirrors the writer's check, not the schema's*). `_comms_register` passes `session_keep_id=`
  **unconditionally** — `None` when no keep was minted (the α interim in i-a; β makes it always non-None in
  i-b). The adversary's `**({...} if session_keep else {})` splat is REJECTED: a conditional kwarg whose only
  purpose is to keep an un-updated fake from raising `TypeError` is a fixture guaranteeing the condition
  under which the seam mismatch is invisible.
- **Pins (MP-8 accepted, and named here as the stamp's ∀ legs):** two sessions → each agent's scope is ITS
  session keep (kills `sorted(visible)[0]`); a householded JOINER's agent (second principal, admitted via
  `add-household`) is stamped with the SHARED session keep (kills the `kept_by_me` gate); the keeper's own
  later agents likewise.

### A3 — R5: YES — `register` refuses an inconsistent provenance pair, before any store I/O
- §6's *"a half-applied state is impossible after this ruling"* was a claim about production PATHS; the
  registry API could still express `owner_principal_id=X, session_keep_id=None` (the adversary's
  `TestMigrateAgentOwner` corpse writes exactly that shape). THE QUANTIFIER LAW's askable form — *does this
  safety claim hold on every branch the ruling touches, or only the one I derived it on?* — says make it a
  writer invariant, not a belief: `(owner_principal_id is None) != (session_keep_id is None)` → a teaching
  `AgentRegistryError` (an INTERNAL invariant, worded for the engineer: *"register called with an owner but no
  session keep (or the reverse) — a server-side caller bug; nothing was written"*), raised BEFORE
  `_select_row`. Cost: three lines. Value: R-Q5-1's trap population becomes unreachable through ANY writer
  (only a raw seed or the E3 image can produce it), so the precondition guards what it claims to.
- Both consistent pairs stay legal at the REGISTRY: `(None, None)` — the α interim, and legal for tests /
  future admin seeding after β (β is the TOOL layer's rule and denies before the registry; it does not retire
  the registry shape) — and `(set, set)`. **Pins:** the two mixed pairs refuse with zero rows; the two
  consistent pairs succeed; mutation: invert the XOR → RED.

### A4 — MP-9 (consequence ruling): the identifier DECISION moves to `lorerunes`; the pattern object is not the implementation
- **The measured defect (WB11):** sharing `AGENT_NAME_PATTERN` and calling `.match` on it passes the
  regex-twin pin and accepts `"fixer-b\n"` (finding #210's class) — ROUTING IS NOT SHARING, measured for the
  N-th time in this repo: the pattern OBJECT was shared, the DECISION (`fullmatch`) was private.
- **The ONE decision already exists:** `AppContext._validate_comms_charset` (`server.py`) — `fullmatch`, the
  offending value through `render_fenced` (Ruling 10 link 4), and a docstring that says *"every
  identity-accepting parameter routes through this seam by EXTENDING its call set, never by cloning the
  check"*. `AgentRegistry.register` cannot call it: `server.py` imports `agents.py` (a circular import), and
  `briefs.py`'s docstring forbids importing `agents` (F-briefs-import). That is the CLAUDE.md `lorerunes`
  case verbatim: *"when the only shared home was a package the other side could not import, 'share it' had no
  address, and the honest engineer wrote the second copy."*
- **Ruling:** `lorerunes` gains `is_legal_identifier(value: str) -> bool` (the `fullmatch` decision) beside
  `is_blank`, and `AGENT_NAME_PATTERN` MOVES there (`agents.py` re-exports it so existing import sites keep
  working). Consumers, each calling the predicate and never the pattern: `_validate_comms_charset` (keeps its
  rendering half — `ValueError` + `render_fenced`), `AgentRegistry.register` (i-a: the teaching
  `AgentRegistryError` subclass — field · rule stated in prose · remedy · the value fenced through the SAME
  helper `_validate_comms_charset` uses, never `repr`), `BriefLedger.publish` (ii: `brief.name`). **This
  pre-answers F-briefs-import:** `briefs.py` imports `lorerunes.is_legal_identifier`, never `agents`; ruling
  §4.2's *"`briefs.py` already imports from `agents`"* is withdrawn. `_IDENTIFIER_CHARSET_PATTERN`
  (`surreal_schema.py`) dies in ii as ruled (F-regex-twin) — its last consumer is then gone.
- **Pins:** the MOVE pins parametrise over the SHARED `_HOSTILE_IDENTIFIERS` corpus (`test_comms_schema.py`),
  which gains `"fixer-b\n"` — ONE corpus, no narrower local copy; mutation of `lorerunes.is_legal_identifier`
  (make it reject a normally-legal value) reds the tool-layer pin AND the register pin (AND `publish`'s in ii);
  mutation of `lorerunes.is_blank` reds the blank-role pin (MP-9c). ⚠ For the reviser: the regex-twin pin's
  monkeypatch target moves to the `lorerunes` home — patching `agents.AGENT_NAME_PATTERN` (a re-export) no
  longer moves anything, and a pin that still patches the re-export is green for a fixture reason.
- **DRY ledger row owed by the builder:** `is_legal_identifier` — query `lore_search("identifier charset
  predicate fullmatch")` → `_validate_comms_charset` (server-bound, unimportable from `agents`/`briefs`),
  `AGENT_NAME_PATTERN` (a pattern, not a decision) → **EXTENDED**: the decision lifted out of
  `_validate_comms_charset` into the shared home; the server seam becomes a caller.

## B. The diff — adversary §9/§10 × sidecar §1 + amendment-1, with every conflict resolved

| adversary | sidecar | verdict | resolution for the reviser |
|---|---|---|---|
| MP-1 delete `TestAgentRoleNonEmptyAssert` ×4 (missed corpse) | — | **ADVERSARY-ONLY — my miss** (I graded the three deletions the author named; I did not sweep for siblings) | DELETE-WITH-REPLACEMENT + DUAL comment; virtue → Leg A`[role]` + the blank-role MOVE pins |
| MP-2 heartbeat seed id ≠ `uuid5` → `UnknownAgentError` on every build; narrow the `except`; add a junk-status touch control | E2 | **CONFLICT → RESOLVED: E2's control shape wins; MP-2's seed-id fix + narrowed except ACCEPTED** | seed `row_id=AgentRegistry._agent_id("wave7","legacy-agent")`; `except` narrowed to the driver's typed store rejection; the positive control = `role=""` under `unbounded_agent_ddl()` + `frozen_asserted_agent_ddl()` + real `touch` → `SurrealStoreError`, zero rows changed. The adversary's junk-status shape is decode-rejected by `_row_to_agent` BEFORE the UPDATE (verified against `AgentRegistry.touch`); it cannot show a store denial. (My own F2 missed the seed-id defect — I trusted the docstring's RED reason; the adversary ran it.) |
| MP-3 update both exact-set pins; decide `briefed` | F19 (owned/not orphaned — WRONG on this point) | **ACCEPT + A1** | five-set `{agent, briefed, memory, message, to}`; resolver `ImportFrom` leg + reach-pin growth leg; fold the two exact-set pins to one |
| MP-4 re-key `TestMigrateAgentOwner`; C4 (∀ scoped rows untouched) orphaned | §9 item 9 | **ACCEPT — my miss**: I adjudicated the missing precondition (F10) and did not list C4 as a distinct virtue | re-key the pre-owned fixture to owner AND scope; C4 → MP-6 |
| MP-5 W1-1 twin survives the append-only probe (WB1) | F12 FAITHFUL | **ADVERSARY SUPERSEDES MINE** (my grade was construction-inspection; WB1 is empirical) | kill-pin: REWRITE every shared spec's type + RENAME every shared index under mutation; the agent DDL carries only the mutated forms. ⚠ No conflict with ruling §2.1's *"`agent_owner_principal` name is preserved"*: that holds on the UNMUTATED build; the rename leg is a mutation context |
| MP-6 mixed store (governed + legacy) migrates only legacy; owner-only precondition (WB3) | E3 | **ACCEPT; consistent with E3** (the predicate stays `scope IS NONE AND owner_principal IS NOT NONE`) | the mixed fixture: 2 governed (member owner + session scope) + 3 legacy → not refused, `backfilled == 3`, governed rows byte-identical |
| MP-7 byte-inert refusal, counts two (WB9/WB10) | F8 | **ACCEPT; strengthens F8** (full `SELECT *` before == after replaces the `scope` proxy) | ⚠ WB10 pairs stamp-first with the predicate `owner_principal != operator`. That predicate is E3's RE-OPEN shape and is legitimate on its own; what is wrong in WB10 is the stamp BEFORE the check. Pin byte-inertness and the exact refusal set — do NOT pin against the `!= operator` predicate (that pin would red E3's trigger path) |
| MP-8 scope = THE session keep ∀ sessions; joiner stamped (WB4/WB12) | — | **ADVERSARY-ONLY — my miss** (the stamp's fixture monoculture: one principal, one session) | as A2's pins |
| MP-9a shared `_HOSTILE_IDENTIFIERS` + trailing newline | F13 ("transfers via the pattern identity" — WRONG) | **ADVERSARY SUPERSEDES MINE → A4** | one corpus + `"fixer-b\n"`; the decision lives in `lorerunes.is_legal_identifier` |
| MP-9b refusal teaches field · rule · remedy (WB5) | F5 | **AGREE (independently found)** | A4's teaching pin; value fenced via the helper `_validate_comms_charset` uses — I wrote `render_attributed` in F5; the adversary read the seam: it is the fence helper. Cite the symbol, not my word |
| MP-9c `is_blank` mutation (WB13) | — | **ADVERSARY-ONLY** | accept |
| MP-9d fence the echoed value | F5 | agree | as above |
| MP-10 resolver / `briefed` | — | **RULED A1** | i-a |
| MP-11 refusal names the row id (WB8) | F8 | **AGREE** | assert the seeded id (`already_owned`) in the reason + the remedy |
| MP-12 register seam / forbidden-name pin / fakes | F3 (write-attribution orphan — adjacent, distinct) | **RULED A2** | i-a |
| R1 frozen DDL = 6 of 16 columns | — | agree: pinned bound, trigger = a type change on an existing agent column | docstring line |
| R2 Leg B 2-of-3 + no re-run | F7 | agree | add `owner_agent` read-back + second run `backfilled == 0` |
| R3 `LegacyMapping` row unpinnable | F18 / N2 | agree | builder docstring |
| R4 `make_ddl` default | F10 | agree | no default |
| R5 owner ⇒ scope | — | **RULED A3: YES** | i-a |
| R6 α interim in i-a | §3.1 | agree; cutover is pkt-65, after i-b's β | none |
| R7 two spellings during the gap | F-regex-twin (lead) | agree; A4 makes the ii deletion a one-liner | none |
| R8 C1/C2/C3/C5–C8 unpinned | — | C1: reviser verifies the 63b-ii-a ambiguity pins still cover the re-shaped leg by `--collect-only` name, not belief. **C5 is NOT low-consequence:** `governed_exempt("migrate-governed", statement=…)` is STATEMENT-SCOPED (`governed.py` §F5 EXEMPT ATTRIBUTION) — the 3-column backfill CHANGES the golden statement, so the allowlist entry's evidence must move with it or leg 4 reds on the first observed run | **i-a owns it** (the wave that changes the golden statement owns its allowlist row): run the agent migrate under `observe_governed_table_writes("agent")` and assert the exempt token's statement equals the executed one. This is the one F5 row that is NOT D1's (i-b) — D1 covers the per-caller `write_guard` labels; the exempt token belongs with the statement |
| R9 "before any store I/O" observed as a row count | F5 (accepted) | agree | none |
| — | F1 P2 `[agent]` serves message-only prose | **SIDECAR-ONLY** (consumer law; the adversary graded discrimination, not prose) | `hazard` slot on `_ConstraintSpec`, no default; content leg for `[agent]` |
| — | F4 `_create_agent` docstring not re-dated | **SIDECAR-ONLY** | rewrite; D3 folds the helper onto `seed_agent_legacy` |
| — | F6 regex-twin blind to a private `session` copy | **SUPERSEDED by A4** (both fields call the shared predicate; still parametrise the mutation per field) | per-field legs |
| — | F14 wiring schema-applied proof goes empty at ii | **DOWNGRADED to a class-hygiene note**: the adversary's WB6 shows the virtue is carried by ~30 other pins; at ii the empty class is deleted with a DUAL line | ii brief line stands (N3), severity: note |

**Conflicts, stated once:** (1) E2 vs MP-2's control — E2 wins on mechanism. (2) E3 vs WB10 — no conflict;
the `!= operator` predicate must not be pinned against. (3) F12 vs MP-5, F13 vs MP-9a — the adversary's
empirical grades supersede my construction-inspection ones. Nothing else conflicts.

## C. My misses, named (so the next fidelity read asks the questions I did not)
MP-1 (a sibling corpse the author did not name — *sweep from the grep, never from a report's hand-list*),
MP-2's seed id (*a RED reason in a docstring is a claim; only running it is a receipt*), C4 (*a removed
behaviour has as many virtues as the old code had branches — inventory them, do not adjudicate the headline
one*), MP-5 and MP-9a (*a routing/identity grade that was not attacked with a wrong build is a
construction-inspection grade — say so, or run one*), MP-8 (*one principal, one session: the fixture
monoculture, on the stamp I ruled*).

## D. ONE reviser worklist for 63c-i-a (each item: what · pin · owner)
1. DELETE `TestAgentRoleNonEmptyAssert` with a DUAL comment (MP-1).
2. Heartbeat leg: correct seed id; narrow the `except`; add E2's frozen-DDL touch control (MP-2/E2).
3. Population set: resolver `ImportFrom` leg + reach-pin growth/negative legs; both exact-set pins → the
   five-set, then fold to one; `briefed` adjudicated in the docstring as *F5 case owed by 63c-ii* (MP-3/A1).
4. `TestMigrateAgentOwner` re-keyed to owner-AND-scope; the mixed-store pin (MP-4/MP-6).
5. W1-1 kill-pin: rewrite-and-rename mutation of the shared emitter (MP-5).
6. R-Q5-1: byte-inert (`SELECT *` before == after), two trap rows, the reason names count + ids + remedy;
   KNOWN BOUND docstring + E3 trigger; never a pin against `!= operator` (MP-7/MP-11/F8/F9/E3).
7. Register stamp ∀ legs: two sessions; a householded joiner; `keep_scope` mutation (MP-8/A2).
8. Registry seam `session_keep_id`; forbidden-name pin re-keyed to the exact provenance set + wire
   disjointness (derived from `_COMMS_ACTIONS`); `FakeAgentRegistry.register` mirrors; unconditional pass (A2).
9. `register` refuses an inconsistent provenance pair; four-shape pins + XOR mutation (A3).
10. MOVE pins over the shared `_HOSTILE_IDENTIFIERS` (+ `"fixer-b\n"`); teaching content (field · rule ·
    remedy · fenced value); `is_legal_identifier` + `is_blank` mutations; regex-twin retargeted to the
    `lorerunes` home (MP-9/A4/F5/F6).
11. P2 `[agent]`: `hazard` slot, no default; `make_ddl` no default; `[agent]` content leg (F1/F10/R4).
12. Leg B: `owner_agent` read-back on violators + second run (R2/F7). R1 bound line in the frozen-DDL docstring.
13. Migrate exempt token: the golden statement follows the 3-column UPDATE; observed run asserts it (R8-C5).
14. `_create_agent` docstring re-dated (F4); D3 fold noted for the build's refactor step.
15. Docstring rows for the builder: `LegacyMapping` agent disposition (R3/N2).
- **Owned elsewhere, named so nothing is orphaned:** F5 per-caller write labels + CREATE-OWNS-IT evidence
  → i-b (D1); `briefed`'s F5 case + `brief.name` MOVE via `is_legal_identifier` + `_IDENTIFIER_CHARSET_PATTERN`
  deletion + the wiring class's DUAL deletion → ii (A1/A4/N3); β → i-b (R6).

## E. Surfaced to the operator (the one item I judge MAJOR enough)
**A4 moves a symbol into `lorerunes`** (`is_legal_identifier` + the pattern), a fourth-member change that
touches `server.py`, `agents.py` and (in ii) `briefs.py`. It is the CLAUDE.md-designated home for exactly
this and I recommend it without reservation — but it widens i-a's production footprint by one shared module,
so it is named here rather than assumed. The alternative that avoids `lorerunes` is a private `fullmatch` in
`agents.py` — the second copy A4 exists to refuse.
