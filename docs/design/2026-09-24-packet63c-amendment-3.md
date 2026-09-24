# Packet 63c — ruling amendment 3 (sidecar-63c-2, 2026-09-24): the r2 contract forks F-1..F-5

Amends `docs/design/2026-09-13-packet63c-remainder-ruling.md` (`699a6e9`) and amendment-1 E2 (`c4728b1`).
Rules the forks in `REPORT-contract-63c-i-a-r2.md` §FORKS (contract r2 `88205a4`; HEAD at ruling `0eed242`).
Directive: lore_comms #15005. Every fact below was read at HEAD this session through lore
(`lore_get_symbol` / `lore_read` / `lore_search`) or an awk sweep where lore has no textual verb — said so
where it happened. The sidecar is the authority on these forks (operator ruling 2026-09-24); sequencing
stays with the lead; the one scope-shaped item is flagged in §E.

**Classification vocabulary used below** — `r3-GATING`: a contract change that must land (and be
adversary-passed) BEFORE a builder is spawned · `r3-NON-GATING`: a contract-substrate change the builder
never touches and that changes nothing it builds — it may land in parallel with the build but MUST land
before the cold audit · `PROSE`: docstring/report text only, no pin moves · `NONE`: no change.

## F-1 — E2 control DDL order: reading (b) CONFIRMED; E2's wording and its hazard example are corrected
- **Ruling:** reading (b) — apply the CURRENT emitter (`surreal_schema.generate_agent_ddl()`) first, then
  `frozen_asserted_agent_ddl()` LAST — is the only satisfiable shape and is faithful to E2's intent.
- **Why (a) is unsatisfiable, verified:** `AgentRegistry.touch` (`agents.py`) SETs five columns —
  `status`, `heartbeat_at`, `last_note`, `declared_cadence`, `status_set_at`; the frozen capture declares
  six columns (four ASSERTed + two datetimes) + the governed overlay, so THREE of the five are undeclared
  under a frozen-only DDL, and the store reference records *"[PROBED] Undeclared top-level keys on a
  SCHEMAFULL table RAISE in 3.x."* The touch would fail with a schema error at HEAD and after the build
  alike — RED for the wrong reason, a control that cannot discriminate. The author's reason is TRUE.
- **Why (b) is build-immune:** `DEFINE FIELD OVERWRITE` is a full replacement (store-ref §1.1 — the
  LAST definition wins), so the `role` ASSERT in force is the frozen one on every build; the emitter
  contributes column declarations only. A swapped order (frozen first, emitter last) is self-revealing,
  not a false clear: post-build the emitter's ASSERT-less `role` lands last, the touch succeeds, and the
  control REDs on a correct build. No structural order pin is needed.
- **E2-bis (corrects amendment-1 E2, two places):**
  1. *"apply `frozen_asserted_agent_ddl()` (never the current emitter)"* → **"apply the current emitter
     to declare every column `touch` writes, then apply `frozen_asserted_agent_ddl()` LAST; the frozen
     capture is the ONLY source of the refusing ASSERT."**
  2. The hazard example *"a builder replaces the whole-row UPDATE with a MERGE that skips validation"*
     is STORE-IMPOSSIBLE: every write form re-validates every field ASSERT on the record (store-ref §1.4
     write-poison — the measured DD-3.c `to`-drain receipt). What the control actually kills is (i) a
     `touch` that stops WRITING the row (an in-memory/cached heartbeat, an early return on a
     legacy-shaped row), (ii) a `touch` that swallows the driver's `SurrealStoreError` into a success
     (the MP-2 narrowed-`except` class), (iii) a `touch` that writes a different row or table.
- **Classification:** `PROSE` — the pin
  `TestAgentHeartbeatOnALegacyRoleRow63cIA::test_CONTROL_the_frozen_asserted_ddl_makes_the_touch_RAISE`
  keeps its body; its docstring drops "(NEVER the current emitter)" and the MERGE example, and names
  (i)–(iii) instead. Non-gating.

## F-2 — the fake mirrors BOTH `is_blank` and `is_legal_identifier`, via the SHARED predicates
- **Ruling:** YES, both — `FakeAgentRegistry.register` calls `lorerunes.is_blank(role)` and
  `lorerunes.is_legal_identifier(name)` / `(session)` and raises `AgentRegistryError` before touching
  `db.agents`, exactly as the real writer does after the Q3 MOVE. Never a private re-statement of either
  rule (ROUTING IS NOT SHARING): the fake ROUTES to the one decision.
- **Why the author's residual is real, and larger than stated:**
  - The fake substitutes the REGISTRY; after i-a the registry's surface includes these refusals. A fake
    that accepts what the writer refuses is the fixture that guarantees the one condition under which a
    tool-layer bug is invisible (THE TEST ENVIRONMENT IS A FICTION).
  - "The tool layer already charset-gates" is a fact about ONE consumer at HEAD (`_comms_register` →
    `_validate_comms_charset`), not about the registry's surface: 63c-ii's brief verbs and any later
    registry caller reach `register` without that gate. Mirroring costs one call to the same predicate.
  - For `role` there is NO tool-layer gate at HEAD — the only gate was the store ASSERT the DUAL retires
    — so after i-a the fake is the ONLY place a fake-driven test could see a blank role refused, and
    today it sees nothing.
- **Fallout (measured by a bare awk sweep of `role=""` / `role=" "` over `loremaster/tests/*.py` — lore
  has no textual verb):** zero fake-driven registers with a blank role; the only hits are the raw
  seeder, its docstrings, and the governance legs (which seed under `unbounded_agent_ddl()`, never
  through a registry). No pin goes RED on a correct build from this mirror.
- **HEAD-RED shape (the one design point):** `lorerunes.is_blank` exists at HEAD
  (`lorerunes/blankness.py`, top-level export) — import it at module top. `lorerunes.is_legal_identifier`
  does NOT exist until the build; a top-level import would turn every `_comms_fakes` consumer into a
  COLLECTION error at HEAD and blind the RED receipt's missing-seam classifier. So the fake imports
  `is_legal_identifier` INSIDE `register` (PLC0415 is a house-ignored idiom), with a one-line comment
  naming this as the HEAD-RED accommodation, and the RED receipt classifier gains the
  `ImportError: cannot import name 'is_legal_identifier'` shape as missing-seam. The RED population does
  not grow: every fake-driven register is already HEAD-RED on the `session_keep_id` seam.
- **Rider — and pin it like this:**
  1. A mirror pin in `test_agent_registry.py` (it already imports `FakeAgentRegistry` and the corpus):
     ∀ `_HOSTILE_IDENTIFIERS` × {name, session} and ∀ `_MOVE_BLANK_ROLES`, `FakeAgentRegistry.register`
     raises `AgentRegistryError` and `db.agents` stays empty. Type + zero-write parity is REQUIRED;
     message parity is NOT (a fake serves no consumer, and a cloned teaching message is #102 in a fake).
  2. The two shared-decision mutation pins
     (`test_the_identifier_decision_is_the_SHARED_is_legal_identifier`,
     `test_the_blank_role_rule_is_the_SHARED_is_blank`) gain the fake as a THIRD consumer leg: with the
     predicate perturbed through `patch_shared_object_everywhere`, the fake's refusal must move too. (A
     call-time `from lorerunes import …` inside `register` reads the patched `lorerunes` attribute, so
     the deferred import does not hide the fake from the mutation.)
- **Classification:** `r3-NON-GATING` — `_comms_fakes.py` + two pins; the builder never touches the fake
  and nothing it builds changes. Lands before the cold audit; one adversary delta pass over it.

## F-3 — fold the name-keyed `_patch_everywhere` copies onto the shared instrument: YES, and it is THREE → ONE
- **Ruling:** fold, in r3, by the contract author. Two private copies exist, not one:
  - `test_secret_typing.py::TestTheBlanknessPredicateIsGENUINELYSHARED._patch_everywhere` (staticmethod,
    name-keyed on `BLANKNESS_PREDICATE`, `hasattr` + `raising=False`) — the one the author found;
  - `test_engine_rejection_seam.py::_patch_everywhere` (module-level, name-keyed, `hasattr` +
    `raising=False`), whose docstring cites *"the `test_secret_typing._patch_everywhere` idiom"* — a
    reference pattern that propagated, #102's exact shape. The author's DRY query searched by meaning near
    `is_blank` and could not see it; `lore_impact("_patch_everywhere")` names all three.
- **Why this is the instrument lesson, not tidiness:** a NAME-keyed patcher rebinds ANY same-named
  attribute — including a caller's PRIVATE same-named copy (`is_blank = …` defined locally, or a wrapper
  assigned the shared name). The mutation then moves the private copy too, and the sharing proof PASSES
  for a build that shares nothing: a false clear inside the very instrument built to catch
  routing-not-sharing. Identity-keyed (`is original`) patches only holders of THE object; a private
  same-named copy is not patched, does not move, and REDs. The engine-rejection discriminator control
  (`test_the_technique_moves_a_router_and_not_a_private_clone`) proves a private clone that FREEZES the
  object is not moved — it never controls for a private clone that WEARS THE NAME, so the name-keyed
  instrument's blind spot was never exercised.
- **Fold mechanics + rider:** each call site becomes
  `patch_shared_object_everywhere(monkeypatch, <name>, <THE object read from its home>, replacement)` —
  `lorerunes.is_blank`; the object `_load_reclassify()` returns / `loremaster.store._txn.wrap_store_rejection`
  — keeping the non-vacuous receipt (`assert patched`, a non-empty list). Identity-keying can patch FEWER
  modules than name-keying, so: both suites GREEN at HEAD before and after the fold, AND their declared
  mutation RED sets re-run through `scripts/mutation_proof.py` both ways. **STOP-rule:** if any folded pin
  changes verdict, that is either a private same-named copy (a real finding — file it) or a sanctioned
  wrapper (then the PIN needs a ruling) — never widen the shared instrument back to names.
- **Home:** `patch_shared_object_everywhere` stays in `_governed_contract.py` for r3 (minimal diff). A
  non-governed suite importing from the governed substrate is a naming smell; re-open trigger: a THIRD
  non-governed consumer → lift it to a neutral test-substrate module.
- **Classification:** `r3-NON-GATING`; the r3 writable set extends to the two suites named. Not a builder
  item (tests). Lands before the cold audit.

## F-4 — sanity check: (a) CONFIRMED with its reason; (b) NOT confirmed — the column-wise 2-of-3 build IS constructible
- **(a) "MERGE that skips validation" unbuildable:** TRUE, for the reason in E2-bis(2) — every write form
  re-validates the record. Not a gap; the control's real kill set is (i)–(iii) above.
- **(b) "Leg B's 2-of-3 stamp is unrepresentable under the ruled ONE statement":** conflates two things.
  ROW-wise partial stamping (some violators stamped, some not) is unrepresentable — one UPDATE applies
  its SET to every matching row or aborts atomically. COLUMN-wise 2-of-3 is ONE statement and one line:
  `UPDATE agent SET owner_principal = $op, scope = $scope WHERE scope IS NONE` (drops `owner_agent`).
  That is the wrong build my F7 named (the r1 Leg B pin read back two of three columns). r2 items 12
  (per-violator `owner_agent == own id` read-back) and 13 (the exempt token's statement sets all three)
  SHOULD red it — but "not separately mutated" means the load-bearing pin has no mutation receipt, and
  a pin that has not been shown failing is not a pin.
- **Ruling:** r3 runs WB-2of3 (column-wise) through `mutation_proof.py` with the RED set declared from
  `--collect-only` BEFORE the run — {item 12 read-back, item 13 token pin, and every Leg B pin that
  reads `owner_agent`} — diffed both ways. If the running re-adversary delta pass already built it, its
  receipt suffices; do not double-run. Do this FIRST in r3 (minutes).
- **Classification:** `r3-GATING iff` the observed RED set differs from the declared one either way —
  that is a missing pin, and it lands before a builder is spawned. Otherwise a receipt, nothing moves.

## F-5 — the regex-twin identity bound: ACCEPTED as a pinned KNOWN BOUND, stated precisely
- **The bound:** CPython's `re.compile` returns the cached object for an identical (pattern text, flags)
  pair (`re._compile`'s bounded cache; HIGH confidence, CPython-specific — the docstring says "CPython").
  So a SOURCE-TEXT twin `AGENT_NAME_PATTERN = re.compile(<same text>)` in `agents.py` is object-identical
  to the `lorerunes` one at birth: the re-export assert and the mutation both pass. A runtime instrument
  cannot see source text; this is closable only by a static scan.
- **Direction — MISS-only, never a false alarm:** the moment the twin's text drifts it is a distinct
  object, `agents_module.AGENT_NAME_PATTERN is lorerunes.AGENT_NAME_PATTERN` REDs, and that is the correct
  verdict (WB-A4b held). Cache eviction between the two compiles would make even a same-text twin
  distinct → RED on a twin = also correct; a correct build holds ONE object by re-export, not by cache,
  so the pin cannot flake on it.
- **Instruments that DO see the twin at birth:** the builder's DRY row (A4 says agents.py RE-EXPORTS; a
  `re.compile` in agents.py is a second spelling by construction) and the cold audit's contract-blind
  diff read. Named as the coverage, not hoped.
- **Re-open trigger:** the pin REDs and the fix turns out to be a source-text twin → close the bound with
  an AST scan over `_SCANNED_MEMBERS` (`re.compile` calls whose first argument is a string constant equal
  to `AGENT_NAME_PATTERN.pattern` → exactly one site, in `lorerunes`); the `_schema_string_constants`
  machinery already exists. Not built now: rigor-to-importance — the drift is caught the moment it matters.
- **Classification:** `PROSE` — the pin's docstring carries the bound, the direction, and the trigger.
- **WB4 two-sessions determinism (ULID-ordered keep ids):** sound; its trigger is named. `NONE`.

## §A — the r3 delta, in order, with gating
| # | item | class | gate |
|---|---|---|---|
| 1 | F-4(b): run WB-2of3 (column-wise) through `mutation_proof.py`, declared RED set both ways | receipt | GATING iff a pin is missing |
| 2 | F-2: fake mirrors `is_blank` + `is_legal_identifier` (deferred import) + mirror pin + third consumer leg on the two shared-decision pins | `r3-NON-GATING` | before cold audit; adversary delta |
| 3 | F-3: fold BOTH `_patch_everywhere` copies onto `patch_shared_object_everywhere`; GREEN-before/after + mutation RED sets re-run; STOP-rule | `r3-NON-GATING` | before cold audit; adversary delta |
| 4 | F-1/E2-bis: the control pin's docstring (drop "NEVER the current emitter" and the MERGE example; name (i)–(iii)) | `PROSE` | none |
| 5 | F-5: the regex-twin pin's docstring carries the bound as stated above | `PROSE` | none |

The builder may be spawned once item 1 has answered; items 2–5 run in parallel with the build (disjoint
files: the builder's set is production, r3's is tests) and one adversary delta pass covers 2–3. Lead
sequences; this is the recommendation.

## §B — my own errata, corrected here
- Amendment-1 E2 said *"(never the current emitter)"* — over-stated; E2-bis(1) is the ruling.
- Amendment-1 E2's hazard example (MERGE skipping validation) was store-impossible — E2-bis(2). The
  askable form I failed to ask: *"can the store actually produce the wrong build my control claims to
  kill?"* — the same class as DD-3.c's safety claim derived off the wrong table.

## §C — operator-visible (flagged, not judged MAJOR)
- F-3 touches two suites OUTSIDE packet 63c (`test_secret_typing.py`, `test_engine_rejection_seam.py`) —
  test-instrument hygiene, ~two call sites; ruled in as "fix it in the session that found it". Say no and
  it becomes a ledgered task with the STOP-rule attached.
- Smell, note only: the "ONE corpus" `_HOSTILE_IDENTIFIERS` is defined in `test_comms_schema.py` (a test
  module), not in the shared substrate; consumers import a test module. Not moved in r3.
