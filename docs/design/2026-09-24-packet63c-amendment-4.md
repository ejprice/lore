# Packet 63c — ruling amendment 4 (sidecar-63c-2, 2026-09-24): adversary-r2 forks NF-1 / NF-2, MP-D's fix shape, MP-G's ordering — and THE ONE r3 worklist

Amends the ruling (`699a6e9`), amendment-2 A4 (`65ca279`) and amendment-3 §A (`e6bedd1`). Rules the forks
and blockers in `REPORT-adversary-63c-i-a-r2.md` (verdict INSUFFICIENT; graded `88205a4`; committed at
`539ffae`). Directive: `REPORT-lead-63c.md@539ffae` "LEAD DIRECTIVE TO sidecar-63c-2 — TASK 4" (the lore
ledger is DOWN — host OOM — so the committed report is the durable copy and this committed doc is the
receipt; no ledger ack was possible). **Every fact below was read with `Read`/`sed`/`awk` — lore's MCP is
disconnected this pass; said so per the dogfood protocol.** HEAD at ruling: `539ffae`.

Vocabulary: **GATING** = lands in r3 and passes the adversary delta BEFORE a builder is spawned (it changes
what the builder builds, or the RED set it greens, or removes a trap in its path) · **NON-GATING** = the
builder never touches it and nothing it builds changes; may land in parallel with the build, MUST land and
be adversary-passed before the cold audit · **PROSE** = docstring/report text only.

## NF-1 — A4's consumer set includes `_is_comms_charset_legal`: YES — and A4 named the WRONG server seam
- **The fact amendment-2 A4 missed (read at HEAD, `server.py`):** `_validate_comms_charset` ALREADY routes
  through `AppContext._is_comms_charset_legal` (`if not AppContext._is_comms_charset_legal(value): raise
  ValueError(...)`), and `_comms_traffic_line`'s SKIP gate reads the same predicate. The server's ONE
  decision home is `_is_comms_charset_legal`; its own docstring says two policies read it *"which is
  exactly why the question has one home"*. A4 listed `_validate_comms_charset` — the REFUSE policy, a
  consumer of the home, not the home. The literal reading therefore licenses N1: a builder rewires
  `_validate_comms_charset` to call `is_legal_identifier` DIRECTLY and leaves the home on
  `AGENT_NAME_PATTERN.fullmatch` — two deciders, identical today, divergent on the next rule change; N1c
  (a private drifted `re.fullmatch` in the home) is divergent TODAY (`fixer.b` skips vs refuses).
- **A4-bis (replaces A4's consumer list):** i-a → **`AppContext._is_comms_charset_legal`** (the server
  home; `_validate_comms_charset` and the `_comms_traffic_line` SKIP gate both read it and are NOT
  rewired) and `AgentRegistry.register`; ii → `BriefLedger.publish`. Production shape: the home's body
  becomes `return is_legal_identifier(value)`; nothing else in the server changes. The ORPHANED rider the
  adversary names is owned by **i-a** — the wave that moves the decision.
- **Rider — pin it like this (two pins, each kills a different door):**
  1. The decision-mutation pin (`test_the_identifier_decision_is_the_SHARED_is_legal_identifier`) is
     parametrised over BOTH server policies: under the perturbation, `_validate_comms_charset(target)`
     raises AND `_is_comms_charset_legal(target) is False` (KP-N1's shape), beside `register`. This is
     the pin that kills N1c (its private literal never moves).
  2. Allowlist-the-safe AST pin over `_SCANNED_MEMBERS`: outside `lorerunes`, the ONLY attribute read on
     `AGENT_NAME_PATTERN` is `.pattern` (prose); any `.fullmatch`/`.match`/`.search`/`.finditer` on it is a
     second decision → RED naming `file:line`. This kills N1 statically and N1b without leaning on
     `test_anchored_pattern_seam.py` (R-9 stays true; the contract no longer depends on it).
- **Classification: GATING** (production shape + a RED pin the builder greens).

## NF-2 — may a legacy hostile-named agent re-register after the MOVE? NO (reading a)
- **Ruling:** the MOVE is ∀ calls. `register` refuses a hostile `name`/`session` BEFORE `_select_row` on
  every path — first register and re-register alike (the same position A3 already holds).
- **Why, three legs:**
  1. Production cost is NIL: through `lore_comms` a hostile-named agent cannot re-register TODAY —
     `_comms_register` refuses at `_validate_comms_charset` before the registry is reached. Only a direct
     registry caller could, and production has none. Reading (b) would preserve a door nothing uses.
  2. The survivor virtue DD-3.c protects is the legacy ROW — its reads, its `touch`, its `migrate`, its
     drain — never a right to RE-MINT through the writer whose entire job after the MOVE is to refuse the
     shape. The existing teaching already says it: *respawns register a fresh name*.
  3. A re-register path that accepts what the create path refuses is the quantifier-law door MP-B just
     measured on A3 (N2), one predicate over.
- **Rider — pin it like this:** seed a hostile-named legacy row under `unbounded_agent_ddl()`, apply the
  CURRENT emitter; `register(<hostile>, session=…, role=…)` → `AgentRegistryError` (teaching: field,
  rule, remedy), the row byte-identical (`SELECT *`), zero new rows; AND the same row still `touch`es
  (the survivor leg — the Leg A virtue, proven through the register seam). RED at HEAD for the right
  reason: under HEAD's asserted DDL the re-register UPDATE is refused by the STORE (`SurrealStoreError`,
  not `AgentRegistryError`).
- **Classification: GATING** (one pin; the production behaviour is the MOVE itself).

## MP-D — the population resolver's fix shape: derive BOTH legs from the EMITTED DDL, generator set by inspection, fail CLOSED
- **The diagnosis, accepted and extended:** the relation leg resolves endpoint SPELLINGS (`Constant`,
  `Name`→`Assign`|`ImportFrom`); keyword endpoints, `Attribute`, `AnnAssign`, relative imports and failed
  imports resolve to `None` and the relation silently never joins — r1 saw one spelling, r2 two: *the
  reach is receding one level per round* (the STOP-rule's tell). The NODE leg is the same class one door
  over: a governed slice built in a helper not named `_<t>_statements` never joins. Two legs, two
  spelling hand-lists. And the adversary's proposed source of truth has a hand-list of its OWN:
  `_enforced_relations_scaffold.ALL_DDL_GENERATORS` names 10 of the 15 `generate_*_ddl` emitters in
  `surreal_schema` (measured by awk). `generate_ddl` composes principal / principal_key / keep /
  member_of / audit, so the real hole is `generate_lease_ddl` + `generate_floor_calibration_ddl` —
  outside every ∀ relation pin (they emit no relation today; the reach is still a hidden constant).
- **Ruling — ONE derivation, from the ARTIFACT (the emitted DDL text), never from source spelling:**
  1. **Generator set by inspection:** every module-level callable in `surreal_schema` named
     `generate_*_ddl` (allowlist the safe: the naming contract that already governs the scaffold), invoked
     with its required keyword arguments derived from `inspect.signature` (`dim` → `MIGRATION_DIM`,
     `analyzer_name` default). Anti-vacuity: ≥ 10 generators; a pin that this derived set ⊇
     `ALL_DDL_GENERATORS` (RED the day the scaffold's hand-list and the module disagree — today it names
     the two unswept emitters).
  2. **Node leg:** a table is governed iff its emitted DDL defines EVERY column of the governed trio —
     the trio's names DERIVED from `_governed_field_specs()` (never a hand-list of three strings) —
     matched by `DEFINE FIELD … <col> ON <table>` over `statements(ddl)`. This PRESERVES 63b §1.9 item 2's
     virtue by a different mechanism: a lone packet-62 `owner_principal` (F-TRAP-1) is one of three and
     does NOT join. Pinned both ways on synthetic DDL text: `owner_principal` alone → absent; all three →
     present.
  3. **Relation leg:** `relation_table_statements(ddl)` (the existing parser) → every `TYPE RELATION`
     statement's `IN <t> OUT <t>` endpoints (extend `_DEFINE_RELATION_RE` to capture them); the edge joins
     iff IN or OUT ∈ the node set. Spelling no longer exists at this level — `N4`, `N4ctl`, `Attribute`,
     keyword, relative import all emit the same bytes. **Fail closed:** a `TYPE RELATION` statement whose
     endpoints the regex cannot capture RAISES (never `continue`); anti-vacuity ≥ 1 relation found.
  4. **Cross-check pin (the adversary's):** `{edge ∈ KNOWN_RELATION_EDGES : IN or OUT ∈ governed nodes}
     ⊆ governed_populations()` — the relation INVENTORY and the POPULATION must agree, and N4h (inventory
     row + `enforced=True`, resolver blind) is exactly their disagreement.
  5. **Reach pins re-keyed:** `governed_populations(ddl_text=…)` takes SYNTHETIC DDL TEXT (the parameter's
     meaning changes from Python source to emitted DDL; rename it so no caller silently passes source);
     the ia growth pins seed a synthetic table with the trio / a synthetic relation over it and assert the
     output GROWS; `_schema_string_constants`, `_resolve_schema_table`, `_governed_node_tables`,
     `_governed_relation_tables` are RETIRED with a DUAL row: their virtue (an OUTPUT, never a hand list;
     keyed on something a field-presence walk cannot fake) is carried by 2–3 above.
- **Separation of concerns, stated so nobody re-adds source inspection here:** the population resolver
  answers *which tables carry governed data* — a property of the ARTIFACT. Whether a builder produced
  that DDL through the ONE emitter is W1-1's rewrite kill-pin's job (mutation over `_governed_field_specs`),
  not the resolver's. A hand-rolled trio still JOINS the population (it is governed data) and still REDs
  W1-1.
- **Classification: NON-GATING** — test substrate; the i-a five-set is unchanged (nodes {agent post-build,
  memory, message} ∪ relations {briefed, to}); RED at HEAD stays RED for the same reason (`agent` carries
  one column of three at HEAD). Lands before the cold audit; one adversary delta (its reach attack is the
  point).
- **Filed for the lead when lore returns (outside 63c):** `ALL_DDL_GENERATORS` is a hand-list missing
  `generate_lease_ddl` and `generate_floor_calibration_ddl` — the enforced-relations ∀ pins do not sweep
  them. Fix = derive the dict from the module as in 1 (one edit in the scaffold); until then item 1's ⊇
  pin names the gap on every run.

## MP-G — fix the shared patch helper BEFORE amendment-3 F-3's fold: YES, in this shape
- **Accepted:** `patch_shared_object_everywhere` keys on NAME ∧ identity, so a CORRECT build that binds the
  shared object under an alias (`from lorerunes import keep_scope as _format_keep_scope`) is RED with a
  message accusing a private copy — a false RED with a lying message, the mirror image of the name-keyed
  copies' false CLEAR that amendment-3 F-3 named. A fold onto it would move three more suites onto an
  instrument with a measured trap in the builder's path.
- **Fix shape (r3, before the fold):**
  1. Identity ALONE: `for name, value in list(vars(module).items()): if value is original: setattr(...)` —
     every module-level binding of THE object, whatever its name. The attribute parameter becomes the
     caller's EXPECTATION, not the key: each caller asserts the module(s) it expects moved (the
     `lorerunes` home at minimum).
  2. Honest failure text in every calling pin: *"behaviour did not move under the MODULE-LEVEL identity
     sweep — either a private copy, or a binding the sweep cannot reach (class attribute / container /
     call-time alias); patched: [...]"*. The bound (module-level bindings only) is stated in the helper's
     docstring; re-open trigger: a correct build holding the object in a non-module binding → the PIN gets
     a ruling, the helper is never widened by guessing.
  3. Self-tests on a synthetic module: an aliased binding → moved; a private copy (a different object,
     any name) → not moved; a private copy wearing the SHARED NAME → not moved (the name-keyed false clear,
     now unrepresentable).
- Then amendment-3 F-3's fold (three name-keyed copies → this instrument) with its STOP-rule unchanged.
- **Classification: GATING** — ten lines, and it removes a trap a correct build can fall into during
  greening (an alias is ordinary hygiene, not an exotic shape).

## MP-B · MP-F · MP-C · MP-E — rulings on the remaining §6 pins
- **MP-B (A3 on the re-register path):** ruled in — the XOR sits before `_select_row` on EVERY path (the
  reference build already does). Pin: after a consistent first register, each mixed pair on a re-register
  → `AgentRegistryError`, row byte-identical. **GATING** (pin; NF-2 and MP-B are the same law, two
  predicates).
- **MP-F (re-register never "heals" an unstamped row):** ruled in — **mint-once ∀ rows, including an
  ownerless α row and a `seed_agent_legacy` row.** Why: a re-register with a credential that heals `scope`
  + `owner_agent` and not `owner_principal` mints the REVERSE half-pair A3 forbids at create, and
  `WHERE scope IS NONE` then skips the row forever; healing all THREE would let any credential CLAIM an
  ownerless name it never minted (a takeover door). Ownerless rows are `migrate-governed`'s to stamp — to
  the operator — never the re-registering caller's. Pin: KP-N10's shape + the legacy-seed line; also
  extend `owner_principal_id`'s docstring sentence to the PAIR. **GATING.**
- **MP-C (the id bound is invisible at 2 traps):** ruled in. The bound is a NAMED constant in
  `principals.py` (`_REFUSAL_ID_SAMPLE_SIZE = 10` — no literal `[:10]`), the refusal names the FULL count
  and `min(constant, count)` ids; the pin READS the constant (derived, never restated) and its fixture
  seeds `constant + 15` traps (above the cap, so the arithmetic cannot align). **GATING** (the builder
  implements the constant).
- **MP-E (the fake's stamps are decoration) + amendment-3 F-2 rider 1:** MERGED into ONE parity matrix
  driven through BOTH the real registry and the fake — consistent / mixed pairs, hostile name (from the
  shared corpus), blank role — comparing outcome CLASS and, on success, the stamps
  (`db.scopes[id] == keep_scope(K)`, `db.owner_agents[id] == id` vs the real row). That measures F-2
  instead of asserting it, and kills N5. Amendment-3 F-2's THIRD consumer leg on the two shared-decision
  pins stands. **NON-GATING.**
- **R-6 (the exempt-token statement's text-shape constraint):** accept the adversary's recommendation —
  normalise (strip a trailing `;`, collapse `\s*=\s*`) rather than widen. **NON-GATING**, author's call
  on mechanics.
- **R-8:** amendment-3 §A item 1 (WB-2of3) is RESOLVED as a receipt — the adversary ran it through
  `mutation_proof.py`, PROOF HELD, no missing pin. Struck from the worklist.

## §W — THE ONE r3 worklist (supersedes amendment-3 §A)
| # | item | source | class | owner |
|---|---|---|---|---|
| 1 | A4-bis: `_is_comms_charset_legal` is the server consumer; decision-mutation pin over BOTH server policies + register; allowlist-the-safe AST pin on `AGENT_NAME_PATTERN` reads | NF-1 / MP-A | **GATING** | contract author |
| 2 | Hostile-named legacy row cannot re-register; still touches | NF-2 / R-10 | **GATING** | contract author |
| 3 | A3 XOR refused on the re-register path, row byte-identical | MP-B | **GATING** | contract author |
| 4 | Mint-once ∀ rows: α row + legacy-seed row re-registered with a credentialed pair → three columns byte-identical; docstring extended to the pair | MP-F | **GATING** | contract author |
| 5 | Id bound as a named constant; refusal names full count + `min(constant, count)` ids; fixture `constant + 15` traps | MP-C | **GATING** | contract author |
| 6 | `patch_shared_object_everywhere` → identity-alone sweep, caller expectations, honest message, three self-tests | MP-G | **GATING** | contract author |
| 7 | Population resolver: emitted-DDL derivation (generator set by inspection, node leg = full trio, relation leg = parsed IN/OUT, fail closed), cross-check pin vs `KNOWN_RELATION_EDGES`, reach pins re-keyed to DDL text, AST resolver retired with a DUAL row | MP-D | NON-GATING | contract author |
| 8 | Parity matrix through real + fake registries (outcome class + stamps); third consumer leg on the shared-decision pins | MP-E + F-2 | NON-GATING | contract author |
| 9 | Fold the three name-keyed `_patch_everywhere` copies onto the fixed instrument; STOP-rule | F-3 (after 6) | NON-GATING | contract author |
| 10 | Exempt-token statement shape: normalise, don't widen | R-6 | NON-GATING | contract author |
| 11 | E2-bis docstring on the heartbeat control; regex-twin pin docstring carries the F-5 bound | amendment-3 F-1/F-5 | PROSE | contract author |
| — | WB-2of3 mutation run | amendment-3 §A-1 | RESOLVED (receipt, R-8) | — |
| — | Two production prose lines the build falsifies (adversary §11) | — | builder brief | lead |
| — | `ALL_DDL_GENERATORS` hand-list misses `lease` + `floor_calibration` | measured here | finding, outside 63c | lead files when lore returns |

**Sequencing (recommendation; the lead rules):** r3a = items 1–6 → one adversary delta → builder spawned;
r3b = items 7–11 in parallel with the build (disjoint files: production vs tests) → one adversary delta →
cold audit. If the author is fast enough that r3a+r3b is one commit, one delta covers both. Items 6 → 9
is the only intra-list ordering constraint.

## §E — operator-visible
- Item 7 SUPERSEDES the MECHANISM of 63b §1.9 item 2 (AST over `surreal_schema`, keyed on
  `_governed_field_specs` callers) with emitted-DDL derivation keyed on the full trio; the INTENT (an
  output, never a hand list; a lone `owner_principal` never joins) is preserved and pinned. Flagged
  because it re-keys a prior packet's ruling; not judged MAJOR (test substrate, same output set).
- The scaffold's `ALL_DDL_GENERATORS` gap is a finding outside this packet's scope — surfaced, not fixed
  here; item 7's ⊇ pin makes it loud on every run until the scaffold derives its own set.
- My erratum: amendment-2 A4 named `_validate_comms_charset` as the server consumer; the home is
  `_is_comms_charset_legal`, which I did not read before writing A4. Corrected by A4-bis.
