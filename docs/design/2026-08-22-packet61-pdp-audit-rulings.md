# Packet 61 — Authorization PDP + audit store: design-fork rulings

**Author:** design-sidecar-61 (Fable), 2026-08-22, working tree on branch
`feat/surreal-unification`.
**Nature:** design-authority rulings for packet 61 (the in-process PDP + the append-only audit
store), delegated by `lead-61` (operator-granted: all packet-61 forks route here; only a MAJOR
scope/design pivot escalates to the offline operator). The lead implements; this doc decides the
model.
**Receipt lines:** `brief-base v14 read` · `brief project v7 read`.
**Inputs read (this session, not skimmed):** `docs/design/2026-08-21-lore-authorization-model.md`
(§1, §2, §3, §4, §5, §6, §7, §8, §9, §10, §11); `docs/reference/surrealdb-31-capabilities.md`
(§1.1, §1.4, §1.8, §2, §3, §4, §6, §10); `docs/design/2026-08-22-packet60-keep-substrate-rulings.md`
(Forks A–F + FR-1/2/3 — the format model + the substrate this PDP consumes); the shipped 48/49/60
build — `loremaster/loremaster/keeps.py` (the full `KeepStore`), `principals.py` (the
`PrincipalStore` idiom + `principal.role ∈ {member,admin}` domain), `store/surreal_schema.py`
(`_principal_statements`/`_keep_statements`/`_member_of_statements`/`generate_ddl` fold +
`generate_keep_ddl` slice), `readonly_guard.py` (the #295 coverage-as-checked-variable +
PDP-composition precedent), `token_verifier.py`/`config.py` (the packet-39 `get_access_token`/
`AccessToken` seam), `lorerunes/lorerunes/` (`__init__`, `scopes.py` — the stdlib-only shared home);
`docs/plans/v2/INDEX.md` rows 39, 60–65; findings **#398 · #399 · #400 · #401**; ledgered task
`06b195e306a34b6391174477bc7744e7`.

**Scope reminder (from INDEX row 61 + design §5/§6/§9):** packet 61 builds (a) the in-process
`authorize`/`authorize_filter` PDP — one policy brain PER ACTION, the 3-way write rule, the admin
short-circuit, the visible-Keeps resolver; and (b) a NEW, greenfield, append-only, ADMIN-EXEMPT
`audit` store. It is COMMIT-ONLY (deploys with 39 at packet 65's joint cutover). **Boundaries that
are NOT packet 61:** the credential→`Subject` binding + the two anti-injection invariants are
**packet 62** (§3) — 61 owns the `Subject` SHAPE, 62 populates it. The governed-row `owner`+`scope`
RETROFIT of comms/memory/tasks/findings (+ their dirty-store migration + the per-verb PDP routing)
is **packets 63/64** (§4/§7) — 61 builds + pins the PDP against FIXTURE Subjects/Resources. This doc
rules only the 61 substrate and marks every boundary a contract could over-reach.

**Greenfield fact that governs the audit-store rulings:** there is NO existing `audit` table
(grepped `surreal_schema.py`). So `audit` is a BRAND-NEW EMPTY table — store-law §1.4's *"a new
field on a POPULATED table must be `option<>`"* does **NOT** apply at birth (exactly as packet 60's
`keep`/`member_of`). Required (non-`option`) fields are legal on `audit`. This is different from the
63/64 retrofit, which adds `owner`/`scope` to POPULATED governed tables and there §1.4 bites hard.

---

## Ruling summary (one line per fork)

- **A — the single-brain mechanism:** a CLOSED predicate **IR** (a small typed algebra) with TWO
  TOTAL interpreters — `to_surql()` (emitter) + `matches()` (Python evaluator) — sharing one tree.
  Equivalence is established by a **LIVE-STORE ORACLE differential test** (not a Python mock of the
  engine), IR-node coverage is a checked variable, and the admin branch is a node OF the same
  `authorize_filter`. ⚠ Realizes design §5 faithfully — RULED within authority, countermand stated.
- **B — PDP home split:** the pure PDP CORE (IR + `to_surql` + `matches` + `Action` enum +
  `Subject`/`Resource` types + per-action predicates + `authorize`/`authorize_filter`) →
  **`lorerunes`** (stdlib-only, PREDICATES not entry points). The visible-Keeps RESOLVER (store
  traversal) + store-execution wiring → **`loremaster`**. Pin `lorerunes` imports no sibling.
- **C — action taxonomy:** closed `Action = {READ, WRITE, DELETE, SET_SCOPE, SET_OWNER}`; one
  predicate per action (the 3-way rule realized per-action). Member-reachable: READ/WRITE/DELETE
  (owned)/SET_SCOPE (owned). Admin-only cross-owner authority: SET_OWNER. ⚠ Owner-of-a-
  `principal-private` write is a two-reading ambiguity — RULED exact-`(principal,agent)`, countermand.
- **D — Subject + Resource:** `Subject = (principal_id, agent_id, role, visible_keep_ids)` (frozen
  value object); `Resource = (owner_principal, owner_agent, scope)`. 61 owns the SHAPES + PDP; 62
  populates Subject from a credential; 63/64 produce Resources. Pinned against FIXTURES only.
- **E — owner representation:** TWO indexed fields `owner_principal: record<principal>` +
  `owner_agent: record<agent>` — **NOT** a single composite ref (a sub-field hop is un-indexable,
  store-law §4). Read predicate is a flat OR of indexed clauses + `scope IN $my_keep_scopes`. Names
  THREE live 3.2.4 probes (IN-index · composite-index shape · OR-planner) — the trust-law hazard.
- **F — visible-Keeps resolver:** a NEW `KeepStore.list_keeps_for_member` (plain-table
  `member_of WHERE in=$principal`, IndexScan on the EXISTING UNIQUE(in,out) LEADING column — no new
  index) + a `loremaster` shell mapping keep ids → `keep:<id>` into the Subject. Bounded by
  membership degree, one round trip.
- **G — audit store:** a greenfield `audit` table (actor `(principal,agent)`, action, target
  table+row, old→new, `created_at`), `ulid()` id, folded after `member_of`; append-only enforced
  **IN-PROCESS** (AuditStore exposes ONLY `append`; the PDP admin short-circuit CARVES OUT `audit`).
  Threat model stated IN the instrument. Audit fires when the admin bypass was load-bearing.
- **H — coverage at 61:** two reach-checked variables buildable NOW — (a) every registered tool is
  classified `{shared_read, governed}`, derived from the live registry (§1); (b) IR-node interpreter
  exhaustiveness (Fork A). The per-governed-verb routing pin DEFERS to 63/64 (named trigger).
- **I — #400 DRY:** the 3rd wrapper (Principal + Keep + Audit) — the named trigger IS met. **EXTRACT
  NOW** a `lorerunes.wrap_engine_rejection` shared by all three; prove-by-mutation. Touches committed
  48/49/60 code — surfaced, the operator-pre-blessed resolution.
- **J — #398/#399 recurrence invariant:** BUILD IT **FIRST** (green on the cleaned tree, guards the
  new `audit` slice), fully contracted. Property = STRUCTURAL fold-coverage (primary) + an
  allowlist-the-safe prose backstop (NAMED BOUND). Coverage-as-checked-variable, mutation-proven.
- **K — #401 stderr:** packet 61 ships no lore-adm verb touching the `run_query` rejection seam →
  **DEFER** with #401's intact named trigger; a STANDING RIDER binds any 61 CLI/test work to
  `"lore-adm:" in stderr`, never `startswith`. Confirm at contract time 61 ships no CLI verb.
- **L — decomposition + sizing:** packet 61 prices **ABOVE 0.30 → SPLIT** (sizing law). Recommend
  **61a Foundations+Audit** (invariant → #402 keeper-cascade → DRY extraction → audit store) THEN
  **61b PDP+resolver+coverage** (the load-bearing engine), each its own
  contract→adversary→build→cold-audit; a dedicated **SECURITY-AUDITOR** pass on 61b (the PDP) + the
  audit carve-out.
- **FR-4 — #402 keeper-on-principal-delete cascade** (a packet-60 escapee; RED_ORPHANED gate at
  HEAD): RULE **REFUSE-WHILE-KEEPING** — a hard principal-delete is REFUSED (loud) while the
  principal keeps ≥1 keep (cascade-DELETE would vanish other principals' shared collaboration
  spaces + their 63/64 keep-scoped rows). `member_of` edges auto-cascade on endpoint delete
  (store-law §4 — PROBE it, the finding disputes it). Update the exact-set pin (+`keep.keeper`) + add
  a behavioral no-dangle pin; land the admin `set-keeper`/`delete-keep` remediation verbs. Lands in
  **61a**, adjacent to #400. Resolves the gate + #402. One countermand (cascade-delete). See §FR-4
  (+ its 2026-08-23 addendum ruling the contract decisions D1/D2/D3).

---

## Fork A — the single-brain mechanism: a closed predicate IR with two total interpreters

**RULING:** Realize design §5's *"the single-row gate IS the list-filter predicate applied to that
one row"* as a **closed predicate IR** — a small, typed algebra of predicate nodes (a frozen
AST) — with **TWO TOTAL interpreters that walk the SAME tree**:

```
authorize_filter(subject, action) -> Predicate           # returns the IR for this (subject, action)
    Predicate.to_surql(params)     -> (where_fragment, bound_params)   # the SurrealQL emitter
    Predicate.matches(resource)    -> bool                              # the Python evaluator
authorize(subject, action, resource) -> Decision         # == authorize_filter(s,a).matches(resource)
```

`authorize` is DEFINED as `authorize_filter(subject, action).matches(resource)` — it is not a
second decision path, it is the filter applied to a singleton. That makes the §5 invariant
`authorize(s,a,row).allowed ≡ authorize_filter(s,a).matches(row)` **true by construction of
`authorize`**, and the remaining risk moves entirely to the fidelity between `to_surql` and
`matches` (below).

The IR node set is a CLOSED algebra — the governed predicates need only: `ScopeEq(scope)`,
`OwnerPrincipalEq`, `OwnerAgentEq`, `ScopeInKeeps` (the pre-resolved `$my_keep_scopes` set),
`And`, `Or`, `AllRows` (the TRUE predicate — the admin short-circuit), `NoRows` (the FALSE
predicate — a fully-denied action). No fulltext, no KNN, no arrow-traversal (design §6) — every
node is trivially faithful in BOTH SurrealQL and Python, which is what makes the equivalence
achievable rather than aspirational.

**Rationale:**
1. **One tree = one source of structural truth.** The predicate an action produces is a single IR
   value; both interpreters read it. Change the IR an action emits and BOTH `to_surql` and `matches`
   move — the mutation proof §5 demands (*"change the predicate, and BOTH the read-filter and the
   write-gate must move"*). Two hand-synced code paths (the shape §2.4/§5 reject as split-brain)
   cannot give this; a declarative-clause-spec-rendered-two-ways is just an IR by another name.
2. **`authorize = authorize_filter(...).matches(...)` collapses the two forms to ONE.** There is no
   separate single-row gate to keep in sync with the filter — the gate literally calls the filter's
   evaluator. This is the strongest possible realization of §5's *"there is structurally one brain
   per action."*
3. **The admin short-circuit lives INSIDE `authorize_filter` (§5/§10-K), as a node.** For a
   `role==admin` subject, `authorize_filter` returns `AllRows` (with the audit carve-out of Fork G);
   for a member it returns the scoped predicate. Same function, same evaluator — so the §5
   equivalence holds trivially for admin (all-vs-all) and *"a bug that grants admin cannot also
   silently drop the equivalence"* (§5). Admin is the `role==admin` BRANCH of the one expression,
   never a code path beside it.

**⚠ THE LOAD-BEARING RIDER (and pin it like this) — the split-brain reappears one level down if
you skip it:** an IR with two hand-written interpreters gives structural agreement on the predicate
*shape*, but **NOT** automatic agreement on what each node MEANS. `matches` uses Python `in`/`==`
semantics; `to_surql` emits `scope IN $set` / `owner_principal = $p` and the ENGINE decides what
those mean (NONE handling, type coercion, the `option<>`/`SELECT *` traps of store-law §2, the
array-`IN` behaviour). If `matches` models the engine WRONG, both interpreters walk one tree and
still disagree — ROUTING-IS-NOT-SHARING, the #102 defect wearing an IR. **Therefore the equivalence
is PROVEN, never asserted:**
- **The equivalence pin is a LIVE-STORE ORACLE differential test, run against the REAL 3.2.4
  engine (`ws://127.0.0.1:18000`), NEVER a Python mock of SurrealQL.** For a HOSTILE fixture
  row-set (≥2 principals × ≥2 agents each; every scope value; `option<>` owner columns present AND
  absent; a `keep`-scoped row in and out of `$my_keeps`; a `server` row; the empty `$my_keep_scopes`
  case), assert `{r.id : authorize(s,a,r).allowed for r in fixture} == set(store.query(BUILD a
  SELECT id ... WHERE <authorize_filter(s,a).to_surql>))` — **byte-identical id-sets**, for every
  `(s, a)` in the cross-product. A Python-mock oracle is exactly the false-clear this pin exists to
  prevent (a mock cannot exhibit the store's real `IN`/`option<>`/`SELECT *` semantics), so the
  ORACLE IS THE ENGINE. This is the single most important pin in packet 61.
- **IR-node coverage is a checked variable (reach law #344/#345):** the node set is DERIVED (every
  concrete `Predicate` subclass), and a pin asserts BOTH interpreters handle EVERY node
  exhaustively (no `else: return True` fall-through in either). A new node type one interpreter
  silently mishandles reds the pin. Mutation-prove: add a node handled only by `matches` → the
  coverage pin reds.
- **Mutation-prove the sharing:** change one action's emitted predicate (e.g. drop `ScopeEq('server')`
  from the READ predicate) → BOTH the read-filter pin AND the write/single-row pin for that action
  redden. A caller that stays green is a private copy.

**⚠ FLAG — divergence risk from design §5's literal "one expression" (surfaced, not silently
resolved):** §5 writes the two forms as *"THE SAME expression."* This ruling realizes "the same
expression" as an IR value with two interpreters — semantically the design's intent (one brain per
action, mutation-provable, the equivalence pinned), and §5's own text (*"two forms that are THE
SAME expression"* + *"change the predicate, BOTH must move"*) contemplates exactly this shape. I
judge this WITHIN my delegated authority — it is the mechanism realizing the operator's ruled §5
property, not a design pivot, and it is the fork the lead assigned me. But because it is the packet's
load-bearing choice: **if the operator intended a single literal SurrealQL string interpreted by
one engine for BOTH the row-gate and the list-filter (e.g. always round-tripping even a single-row
check through the store), countermand this ruling** — that alternative is sound too (the store is
then the only interpreter, no `matches` to keep faithful) but costs a store round-trip on every
single-row authorize, which the in-process PDP exists to avoid, and it cannot authorize a row not
yet written (a pre-write scope-on-create check). I found the IR-with-oracle the better fit for §5's
"in-process PDP" framing; the countermand is clean because every other fork is independent of this
choice.

---

## Fork B — PDP home split: pure core in `lorerunes`, store-touching shell in `loremaster`

**RULING:** The line falls between the PURE PREDICATE LOGIC and the STORE EXECUTION:

- **`lorerunes` (stdlib-only) — the PDP CORE:** the predicate IR (all node classes), `to_surql`,
  `matches`, the `Action` enum, the `Subject` and `Resource` typed value objects (Fork D), the
  per-action predicate builders, `authorize`, and `authorize_filter`. All pure — `to_surql` is
  string+dict assembly, `matches` evaluates a Python dict, and both consume a `Subject` whose
  `visible_keep_ids` is already resolved (passed IN). This is `lorerunes`'s chartered content:
  *"policy … validation predicates, error classification … anything whose rules must agree
  everywhere"* — and the `lorerunes` law's own caveat, *"it holds PREDICATES, not ENTRY POINTS."*
  The PDP core is the paradigm predicate.
- **`loremaster` — the STORE-TOUCHING SHELL:** the visible-Keeps RESOLVER (Fork F — it executes a
  `member_of` read via `KeepStore`), the wiring that feeds `authorize_filter(s,a).to_surql()` into a
  live store query (63/64 consume this), and the tool-population classification registry (Fork H,
  which reads the live tool registry). These need a sibling (`KeepStore`) or the store, so they
  cannot live in `lorerunes`.

**Rationale:**
1. **It keeps `lorerunes` importable by everyone and the PDP core trivially testable.** A pure
   `authorize(subject, action, resource)` over typed values is a pure function — the equivalence
   oracle (Fork A) and every predicate pin run without a store for the `matches` side and against
   the store only for the `to_surql` side. The store-touching resolver is the thin shell.
2. **It mirrors the settled `lorerunes` precedent EXACTLY (packet 42, #222).** The blankness
   PREDICATE moved to `lorerunes` while secret RESOLUTION stayed in `loremaster` *"because only a
   composition root may read the environment."* Here: the authorization PREDICATE → `lorerunes`;
   the store READ (the visible-Keeps resolver) → `loremaster`. Same principle, same split point.
3. **`Subject.visible_keep_ids` carried IN the Subject is what makes the core pure.** The RESOLVER
   (loremaster) reads `member_of` and builds `visible_keep_ids`; the pure PDP then emits
   `ScopeInKeeps` over that frozenset. No traversal ever enters the pure core (design §6).

**RIDER (and pin it like this):**
- **Pin `lorerunes` imports NO sibling.** A test asserts no `loremaster`/`loresigil`/`lorescribe`
  import appears anywhere under `lorerunes/` (the moment it does, `lorerunes` stops being importable
  by them — the whole constraint). This is a guard, not a habit (`lorerunes` law). If a
  `registration_sites.py`-style AST scan already covers this, extend it; else add the pin.
- **Prove sharing by MUTATION across the split:** change a per-action predicate in `lorerunes` → a
  `loremaster` read-filter pin AND a `loremaster` write-gate pin BOTH redden. Routing a call
  through the shared core while re-deciding underneath it is a private copy (ROUTING-IS-NOT-SHARING).
- **Register the new `lorerunes` surface** per the `lorerunes` law's registration-sites rule — RUN
  `./scripts/registration_sites.py`, do not read a list (the count has been wrong four times). The
  PDP core is new public `lorerunes` API; its `__init__` re-exports + `mypy_path`/typecheck
  MEMBERS/AST `_SCANNED_MEMBERS`/testpaths/Containerfile conformance entries all follow from that
  derivation, not a hand-list.

---

## Fork C — the action taxonomy

**RULING — a closed `Action` enum, one predicate per action:**

| Action | who (member) | who (admin) | READ/WRITE predicate (member; admin ⇒ `AllRows`) |
|---|---|---|---|
| `READ` | visible-set (scope-filtered) | AllRows | `(scope='agent-private' AND owner_principal=$p AND owner_agent=$a) OR (scope='principal-private' AND owner_principal=$p) OR scope='server' OR scope IN $my_keep_scopes` |
| `WRITE` (edit / transition / supersede / claim / correct) | owner-of-private · any household member of a `keep` row · owner of a `server` row | AllRows (audited) | `(scope IN {agent-private,principal-private} AND owner=me) OR (scope IN $my_keep_scopes) OR (scope='server' AND owner=me)` |
| `DELETE` (hard) | the row's owner | AllRows (audited) | `owner=me` |
| `SET_SCOPE` (change a row's scope) | the row's owner (any tier, up/down) | AllRows (audited) | `owner=me` |
| `SET_OWNER` (reassign a row's owner) | **NONE** | AllRows (audited) | `NoRows` |

`Action` is a closed domain (the house closed-domain idiom — mirror `_PRINCIPAL_ROLES`/`_KEEP_TYPES`).
`WRITE` is the single "mutate the row's content/state" action (claim/transition/supersede/correct all
route to it — §4: *"a household member claims another's task, corrects another's memory, supersedes
another's finding"*). `DELETE` is the separate "vanish the row" action (§4: hard-delete of a shared
row = owner+admin, never any household member). `SET_SCOPE`/`SET_OWNER` are the two
metadata-authority actions (§4.3).

**Rationale:** this is the minimal-complete realization of §4/§4.3/§5's *"ONE policy expression PER
ACTION"* — five actions, five predicates, each independently keeping the §5 equivalence. It maps 1:1
onto the design's stated verbs and no more. `SET_OWNER = NoRows` for members is §4.3's *"the only
cross-owner authority"* (admin-only) expressed as a predicate, not a special case.

**⚠ FLAG — a genuine two-readings-different-code ambiguity in `principal-private` WRITE/DELETE
(surfaced per brief-base §2, ruled per my delegated authority, countermand stated):** design §4's
3-way table lumps *"agent-/principal-private → the owner only"* for WRITE, and the owner stamp is
`(principal, agent)`. Two readings produce different code:
- **(reading 1, RULED)** "owner" = the EXACT `(principal, agent)` stamp for BOTH private scopes. A
  sibling agent of the same principal may READ a `principal-private` row (§4 read column: *"the
  owning principal + its agents"*) but may NOT write/delete it.
- **(reading 2)** "owner" of a `principal-private` row = the PRINCIPAL (any sibling agent may write
  it), from §3.1's *"a user and their agents is ONE trust unit."*

**I RULE reading 1** (exact `(principal, agent)`), because: (a) it is the literal reading of "owner"
(= the stamp); (b) TRUST/isolation is the paramount property — resolve toward rigor; (c) §4 frames
private scopes as explicitly NON-collaborative (*"Private scopes stay owner-only … the owner opts
INTO collaboration by choosing a Keep scope"*), so within-principal write-collaboration on a private
row would contradict the design's own line — a sibling wanting to co-edit scopes the row to a Keep.
The read-vs-write asymmetry (siblings see, only the author edits) is coherent and isolation-safe
(cross-principal isolation, the §9 in-scope property, is untouched either way — this is a
WITHIN-principal question). **Countermand:** if the operator intends within-principal collaboration
on `principal-private` rows without a Keep, flip reading 2 (WRITE/DELETE `owner` for
`principal-private` becomes `owner_principal=$p`, dropping the `owner_agent` conjunct). Every other
fork is independent of this choice.

**RIDER (and pin it like this):**
- **The contract-adversary MUST pin the chosen reading with a ≥2-agents-per-principal fixture** — a
  sibling agent attempting to WRITE and DELETE another sibling's `principal-private` row is REFUSED
  (reading 1) — the exact fixture that discriminates reading 1 from reading 2 (fixtures-must-
  discriminate: a single-agent-per-principal fixture cannot tell them apart, the PKT-28 C1
  parameter-monoculture trap).
- **Pin each action's member-vs-admin fixture on the role axis** (member filtered, admin `AllRows`),
  and `SET_OWNER` REFUSED for a member on their OWN row (it is admin-only regardless of ownership —
  a member cannot even give away their own row; §4.3).

---

## Fork D — Subject + Resource types (the 61↔62 and 61↔63/64 boundaries)

**RULING — two frozen pydantic value objects (`extra="forbid"`, the house `Keep`/`Membership`/
`Principal` idiom), both in `lorerunes`:**

```
Subject:                                  # the authenticated actor, a TYPED value
    principal_id: str                     # the principal's bare record id
    agent_id: str                         # the fleet agent's identity (the (principal,agent) unit)
    role: str                             # {member, admin} — the principal.role domain
    visible_keep_ids: frozenset[str]      # $my_keeps, RESOLVED (Fork F) — the keep:<id> scope set

Resource:                                 # a governed row's authorization columns, a TYPED value
    owner_principal: str                  # the owning principal's bare id
    owner_agent: str                      # the owning agent's id (the (principal,agent) stamp)
    scope: str                            # {agent-private, principal-private, keep:<id>, server}
```

**The 61↔62 boundary (crisp):** packet 61 DEFINES the `Subject` type and CONSUMES it; **packet 62
POPULATES it from a server-bound credential** (§3). At 61 the PDP is built + pinned against
hand-constructed FIXTURE `Subject`s. Packet 61 does **NOT**: touch `get_access_token`/`AccessToken`,
mint or bind credentials, or retire the free-form `created_by`/`actor`/`agent=` arguments (that
retirement is 62's anti-injection invariant #2, applied by 63/64 at the tool seams). `Subject`
carries `agent_id` NOW (the `agent-private` read predicate needs it), but its BINDING to a real
credential is 62 — 61 owns the SHAPE, 62 owns the FILL. **Flag any contract pin that reaches into
`get_access_token` or asserts credential-derived identity as OVER-REACH into 62.**

**The 61↔63/64 boundary (crisp):** packet 61 DEFINES the `Resource` shape (`owner_principal` +
`owner_agent` + `scope`) and the PDP that consumes it; **packets 63/64 RETROFIT the actual governed
tables** (comms/memory/tasks/findings) with these columns + the dirty-store migration (§7) + the
per-verb PDP routing. At 61 the PDP is pinned against FIXTURE `Resource`s. Packet 61 does **NOT** add
`owner`/`scope` columns to any populated table. (61 DOES create the greenfield `audit` table — Fork
G — but that is a NEW empty table, not a retrofit.) **Flag any contract pin that migrates or writes
to comms/memory/task/finding rows as OVER-REACH into 63/64.**

**Rationale:** carrying `visible_keep_ids` IN the `Subject` (rather than resolving inside the PDP) is
what keeps the `lorerunes` core pure (Fork B) and makes the whole PDP a pure function of typed
inputs — the strongest testability and the cleanest 62 seam (62 fills three fields + the resolver
fills the fourth). The value-object idiom (frozen, `extra="forbid"`) matches every sibling substrate
type and gives free construction-time validation.

**RIDER (and pin it like this):** pin that `role` is validated against the `{member, admin}` domain
at `Subject` construction (reuse the `principal.role` vocabulary — never a re-spelling; the
one-column-one-vocabulary law from `principals.py`). Pin that a `Resource.scope` is one of the four
scope values (or `keep:<...>`). Do NOT default any field the PDP branches on (the `_brief()`-factory
trap, PKT-28 C1 — no fixture default for `role`, `scope`, or `agent_id`; every fixture call chooses,
so a build that branches on one value cannot hide behind a fixture monoculture).

---

## Fork E — owner representation: two indexed fields, not a composite ref (needs the live probe)

**RULING:** Store `owner` as **TWO separate indexed fields** on every governed table (63/64) and in
the `Resource` shape (61): `owner_principal: record<principal>` + `owner_agent: record<agent>`.
**NOT** a single composite `owner` ref (an array `[principal, agent]` or an object
`{principal, agent}`). The READ predicate (Fork C) is then a flat OR of indexable clauses plus the
pre-resolved `scope IN $my_keep_scopes` (design §6) — **no sub-field hop, no arrow-traversal inside
the per-row WHERE.**

**Rationale (all store-law §4/§2):**
1. **A single composite forces an un-indexable sub-field hop on the hot read path.** The
   `principal-private` read (a user's personal memory — the common case) needs `owner.principal =
   $p`; store-law §4 verbatim: *"a scalar attribute … filtered through a hop is un-indexable by
   construction — keep scalars as indexed fields."* Two flat fields make `owner_principal = $p` a
   direct equality on an indexed column — an IndexScan.
2. **It mirrors packet-60 Fork A EXACTLY.** Keepership is a `keep.keeper: record<principal>` INDEXED
   FIELD LINK (not an edge/hop) precisely so `WHERE keeper = $p` is an IndexScan — mutation-proven
   with EXPLAIN (Fork A rider). `owner_principal`/`owner_agent` are the identical shape, one level
   out: indexed record-link fields, equality-matched, IndexScan.
3. **A composite/array `owner` walks into store-law §2's silent-`[]` array-index trap** (a plain
   `FIELDS <array_col>` index + `WHERE col = 'x'` IndexScans and returns `[]`, no error). Two scalar
   fields sidestep it entirely.

**⚠ NAMED store-law probes (per the trust law — these are BELIEVED, not known, until probed on the
live 3.2.4 store `ws://127.0.0.1:18000`, with EXPLAIN + a positive control per the store-reference's
own IndexScan-vs-TableScan discipline):**
1. **`scope IN $set` index usage** — does a defined index on `scope` serve `WHERE scope IN $set` as
   an **IndexScan**, or a TableScan? The store reference proves `=` (equality → IndexScan) and range
   (`>= AND <` → IndexScan) but **has NOT probed `IN`** (§2). The keep-read path (`scope IN
   $my_keep_scopes`) rests on this. If `IN` TableScans, the fallback is an OR-of-equalities or a
   UNION of per-scope IndexScans.
2. **The composite-index shape** — store-law §2: *"composite indexes are LEADING-COLUMN only."* A
   single `(scope, owner_principal, owner_agent)` index will NOT serve every disjunct of the READ
   predicate. Probe which index set the disjunction needs (likely a separate index on
   `owner_principal` AND one on `scope`).
3. **⚠ THE OR-PLANNER (the #107-class trap here)** — does SurrealDB use indexes for an **OR of
   indexed predicates**, or does an OR force a whole-table scan? Many planners TableScan on OR. If
   this OR TableScans, the read-filter must be a **UNION of per-clause IndexScans**, or accept a
   bounded TableScan (a user's memory table can grow — this is NOT a "bounded by row count is fine"
   table). **Assuming the OR is index-served, shipping it, and having it TableScan in production on
   a large dirty store is exactly the #107 shape** (green on a virgin/small test DB, wrong on a
   long-lived one). This probe MUST run before the read-filter emitter (Fork A `to_surql`) is
   contracted — the emitter's SHAPE depends on the answer.

**RIDER (and pin it like this):** the read-filter's IndexScan claim is a PINNED EXPLAIN with a
positive control (a deliberately-un-indexed predicate that TableScans, proving the probe can SEE a
TableScan — the store reference's own §4 "the instrument's first run said the opposite … only the
positive control exposed it" discipline). The probe is a COMMITTED `scripts/probe_*.py`
(self-checking, exit 0 with positive controls), per brief-base §1 (an instrument that establishes a
load-bearing claim is a deliverable, committed to `scripts/`, not scratch). `owner_*` field
NULLABILITY on the RETROFIT tables (`option<>` per §1.4 on populated tables) is a 63/64 decision, not
61's — 61 rules the SHAPE and pins the indexability.

---

## Fork F — the visible-Keeps resolver

**RULING:** Add a NEW read method **`KeepStore.list_keeps_for_member(*, member_email: str) ->
list[str]`** (the mirror of the shipped `list_keeps_for_keeper`), reading the `member_of` edge **AS
A PLAIN TABLE** — `SELECT out FROM member_of WHERE in = $principal` (endpoint bound as a `RecordID`)
— **never an arrow traversal** (store-law §4; the existing `_read_membership`/`list_household`
precedent already reads `member_of` as a plain table). It returns the caller's keep ids. A thin
**`loremaster` resolver shell** (`resolve_visible_keeps`) maps those ids → `keep:<id>` scope strings
→ the `Subject.visible_keep_ids` frozenset (Fork B/D).

**Rationale:**
1. **The direction is "keeps whose household I'm in" — `member_of` FROM the principal.**
   `list_household(keep_id)` is the REVERSE (members of a keep); this is the symmetric `WHERE in =
   $principal`. It belongs on `KeepStore` (it owns the `member_of` edge), as the mirror of
   `list_keeps_for_keeper` (which reads `keep WHERE keeper = $p`).
2. **No new index is needed — the EXISTING `UNIQUE(in, out)` serves it.** Store-law §2: *"composite
   indexes are LEADING-COLUMN only … ONE UNIQUE(name, source_book) serves both … and the
   leading-column exact-name lookup."* `member_of` carries `UNIQUE(in, out)` (packet 60 Fork F), so
   `WHERE in = $principal` (the LEADING column) is an **IndexScan on the existing index**. (The
   design §6 traversal-first-then-flat-`IN` plan is realized: this ONE bounded read resolves the
   set; the PDP then emits `scope IN $my_keep_scopes`, no traversal in the per-row WHERE.)
3. **Bounded by membership degree, one round trip.** Store-law §4: a plain-table read is
   IndexScan-bounded, not a per-keep loop.

**RIDER (and pin it like this):**
- **Pin the LEADING-column IndexScan with a positive control:** an EXPLAIN that `WHERE in = $p`
  IndexScans, AND that the TRAILING-column `WHERE out = $keep` (what `list_household` does)
  TableScans — the control proves the probe discriminates leading from trailing (the store-law §2
  composite-leading-column fact, on THIS edge). Mutation/negative control: without the index the
  leading read would TableScan too.
- **⚠ Pre-existing observation, surfaced not fixed (scope-adjacent):** `KeepStore.list_household`
  filters `WHERE out = $keep` — the TRAILING column of `UNIQUE(in, out)` → a **TableScan** (store-law
  §2). It is bounded by the `member_of` row count (small today), so it is not a 61 blocker, but it is
  a latent perf seam the 61 read path does NOT share (the resolver uses the leading column). If a
  keep's household or the global `member_of` table grows, `list_household` wants its own index on
  `out` (a free `IF NOT EXISTS` add). Flagged for the lead; not in 61's writable intent unless the
  operator rules it in.
- **The resolver is `loremaster` (it calls `KeepStore`); the mapping keep-id → `keep:<id>` is pure
  string work.** Pin the mapping (a keep id `k` → the scope string `f"keep:{k}"`) as a `lorerunes`
  helper if 63/64 also mint `keep:<id>` scopes on write (ONE spelling — prove-by-mutation), else a
  local shell helper. Run `registration_sites.py` if it becomes `lorerunes` API.

---

## Fork G — the audit store (§9)

**RULING — a greenfield `audit` table + an append-only `AuditStore`, enforced IN-PROCESS.**

**Field set (48/49/60 house `(name, type_expr, constraint)` format):**

| field | type_expr | constraint | notes |
|---|---|---|---|
| `actor_principal` | `record<{PRINCIPAL_TABLE}>` | `""` | the admin who acted (the `(principal,agent)` stamp). Required at birth (greenfield, §1.4 N/A). |
| `actor_agent` | `record<{AGENT_TABLE}>` | `""` | the agent that carried the action. Required. |
| `action` | `_CHUNK_STRING_TYPE` | `f"ASSERT $value IN [{audited_actions}]"` | call-time-derived from a `_AUDITED_ACTIONS` tuple = the MUTATING actions `{WRITE, DELETE, SET_SCOPE, SET_OWNER}` (READ is never audited). Mutation-provable (the `_principal_statements` idiom). |
| `target_table` | `_CHUNK_STRING_TYPE` | `_NON_EMPTY_STRING_ASSERT` | which governed table. Non-empty string (a closed domain would be a hand-list of governed tables that don't exist until 63/64 — the reach-law trap; defer). |
| `target_row` | `_CHUNK_STRING_TYPE` | `_NON_EMPTY_STRING_ASSERT` | the `str(RecordID)` of the affected row (store-law §2: `str(RecordID)` round-trips; a queryable value column, since the id's string component can't be indexed/prefix-matched). |
| `old_value` | `option<object> FLEXIBLE` | `""` | the before-state. `option<>` — a CREATE/SET_OWNER-from-nothing has no old. FLEXIBLE (arbitrary row shape). |
| `new_value` | `option<object> FLEXIBLE` | `""` | the after-state. `option<>` — a DELETE has no new. |
| `created_at` | `datetime` | `DEFAULT time::now()` | engine-stamped; store OMITS on write (the `finding`/`keep.created_at` idiom). |

Record id = **`ulid()`** at CREATE (creation-ordered, sortable — the `message`/`keep` precedent; an
audit log is append-ordered and `str(RecordID)` round-trips to a clean id). **NOT** a counter-row or
sequence mint — an audit write must not contend on a hot counter row (the whole point is a
cheap, non-blocking append), and no gapless human handle is needed. Emitted via `_audit_statements()`
+ `generate_audit_ddl()` (slice, mirroring `generate_keep_ddl`), **folded into `generate_ddl` AFTER
`_member_of_statements()`** (`actor_principal`/`actor_agent` reference `principal`/`agent`, which are
defined earlier). **Indexes DEFERRED** — 61 ships no audit-query verb (that is an admin tool, 63/64+),
so ship only table + fields; add `actor_principal` + `created_at` indexes when a listing verb lands
(a free `IF NOT EXISTS` add). Table = plain SCHEMAFULL (`IF NOT EXISTS`); fields = `OVERWRITE`
(§1.1).

**Append-only enforcement — IN-PROCESS, two layers (native PERMISSIONS is INERT under root, §2.3 —
the #107 trap):**
1. **`AuditStore` exposes ONLY an `append` method** — no `update`, no `delete`, no `set_*` exists on
   the class. You cannot call what is not there (the narrowest surface).
2. **The PDP admin short-circuit CARVES OUT the `audit` table (Fork A):** for a `Resource` whose
   `target_table`/type is `audit`, `authorize(admin, {WRITE,DELETE,SET_SCOPE,SET_OWNER}, audit_row)
   = DENY` — the admin `AllRows` node is `AllRows EXCEPT audit-mutations`. So even an admin acting
   through the governed tools (63/64) cannot erase or rewrite its own trail. The §5 equivalence still
   holds (the carve-out is IN the one expression, a node, not a bypass beside it).

**⚠ THREAT MODEL — stated IN the instrument (a gate needs a threat model, CLAUDE.md):** the audit
store's append-only guard is a boundary against a **COMPROMISED or INJECTED ADMIN CREDENTIAL acting
THROUGH lore's own governed MCP tools** — such an admin cannot delete or rewrite an audit row. It is
**NOT** a boundary against direct-store / root access: lore connects as root (Version A, §2.3), and
anyone holding the root SurrealDB connection (the process itself; an operator with store creds) can
rewrite any table, `audit` included. That is an ACCEPTED bound by construction, not a defect — write
it as a docstring on `AuditStore` + a comment on the carve-out pin, so a future auditor does not call
*"a root user can delete audit rows"* a hole. **Re-open trigger:** Version B (per-principal record
auth, §2.3) would let native `PERMISSIONS` enforce append-only IN-ENGINE — the day lore moves to
Version B, this in-process guard is revisited.

**WHAT triggers an audit write, and the 61 boundary:** the design §9 audits admin writes THROUGH
governed tools that do not exist until 63/64. So at packet 61:
- 61 BUILDS the `audit` table + the `AuditStore.append` primitive + the **PDP audit-OBLIGATION
  seam** — `authorize(...)` returns a `Decision` carrying **`requires_audit: bool`**, computed
  inside the ONE expression as **`requires_audit = (subject.role == admin) AND NOT
  member_predicate(action).matches(resource)`** — i.e. audit fires IFF the admin superuser bypass was
  LOAD-BEARING (the same action would have been DENIED for a non-admin subject). An admin editing its
  OWN row (where the member predicate already allows) exercises no bypass → `requires_audit=False`.
  This is the precise realization of §9's *"every admin action is AUDITED"* (every USE of admin
  POWER) reconciled with §9's pin *"an admin mutation of ANOTHER principal's row writes the audit
  record"* — cross-owner is the paradigm case of a load-bearing bypass. It is DERIVED from the same
  member predicate, so it is single-brain (no second decision).
- 61 does **NOT** wire the governed tools (they don't exist). The audit-on-admin-write is a SEAM the
  63/64 governed tools consume — pinned at 61 against FIXTURE admin mutations.

**Pins (§9, and pin it like this):**
- **`requires_audit` fixtures (fixtures-must-discriminate):** admin cross-owner WRITE →
  `requires_audit=True`; admin WRITE of its OWN row → `False`; MEMBER WRITE of anything → `False`
  (no admin power). A single admin-cross-owner fixture cannot tell "audits the bypass" from "audits
  every admin action" — include the own-row-admin fixture that discriminates them.
- **`AuditStore.append` writes the record** (who=`(actor_principal, actor_agent)`, action,
  target_table, target_row, old→new, when) — a fixture admin mutation → the exact row.
- **The append-only carve-out:** `authorize(admin, DELETE, audit_resource) = DENY` AND
  `authorize(admin, WRITE, audit_resource) = DENY`; and `AuditStore` has no delete/update method
  (assert the class surface). Mutation-prove: remove the carve-out node → the admin-can't-delete-audit
  pin reds.
- **old→new capture:** a WRITE fixture records `old_value` + `new_value`; a DELETE records
  `old_value` + `new_value=None`; a SET_OWNER records the owner change.

**⚠ FORWARD-COMPAT SEAM (get it right at 61):** 63/64 must land the audit append + the governed
mutation ATOMICALLY (one `execute_transaction` — store-law §3; a partial apply is a mutation with no
trail or a trail with no mutation). So design `AuditStore.append` to be **composable into a caller's
transaction** — return/accept a `TxnFragment` (the `KeepStore.create_keep` `compose`/
`execute_transaction` precedent) so 63/64 lands `[mutation, audit-append]` in ONE `BEGIN…COMMIT`.
Pin at 61 that `append` is a single-statement CREATE that composes (not a standalone `.query()`).

**Uses `wrap_engine_rejection` (Fork I):** `AuditStore` wraps raw `SurrealStoreError` → `AuditStoreError`
via the extracted shared seam from birth (it is the 3rd consumer — the whole reason the extraction
lands in 61).

---

## Fork H — coverage-as-checked-variable at packet 61 (the reach law #344/#345)

**RULING:** At 61 no governed tool routes through the PDP yet (that is 63/64), so the per-verb
routing pin cannot fire on real tools. Build the two reach-checked variables that CAN, and DEFER the
third with a named trigger:

1. **(a) Tool-population classification — buildable NOW, against the EXISTING tool surface.** §1: a
   tool is classified `{shared_read (corpus), governed (owner+scope)}` at registration, and *"which
   population is a checked variable (no tool is silently neither)."* Build a classification registry
   whose set is **DERIVED from the live tool registry** (the `readonly_guard`
   `partition_tools_by_posture`-over-the-live-list precedent — NOT a hand-list), classifying every
   registered tool into exactly one population. A registered tool that is NEITHER reds the pin;
   a NEW tool grows the derived set and reds the pin until classified. This is the §1 instrument, and
   it is the seed 63/64's routing pins build on (corpus tools → shared-read exempt; comms/memory/
   tasks/findings → governed).
2. **(b) IR-node interpreter exhaustiveness (Fork A)** — both `to_surql` and `matches` handle EVERY
   IR node; a new node one interpreter misses reds a pin. The IR is built at 61, so this is
   reach-checked at 61.
3. **(c) DEFERRED to 63/64, NAMED:** the per-governed-VERB *"every write routes through `authorize`,
   every list-read through `authorize_filter`"* coverage pin — it can only fire once the verbs route
   through the PDP (63/64). **Named owner/trigger (deferral law):** *"the first governed-tool
   retrofit (packet 63) MUST add the verb-routing coverage pin, DERIVED from the tool-classification
   registry seeded at 61 — a governed verb that bypasses the PDP reds it."* This is a structured
   deferral (named owner + named trigger), NOT an open punt.

**Rationale + self-check (INSTRUMENT-0 askable form):** *"does a test go RED when the derived set
GROWS but the observed set does not?"* — (a): a new unclassified tool reds the pin; (b): a new IR
node handled by one interpreter reds the pin. Both are growth-detecting and mutation-provable.
Building (c) NOW would be a guard over an empty set (no governed verb routes yet) — *"a guard nobody
runs is a hope with a filename"* — so it is honestly deferred with a trigger rather than shipped
green-over-nothing.

**RIDER (and pin it like this):** mutation-prove (a) — add a tool with no classification → the pin
reds. Mutation-prove (b) — add an IR node handled only by `matches` → the coverage pin reds. The
classification derivation is DERIVED (from the registry) with an EXPLICIT allowlist of shared-read
corpus tools (allowlist-the-safe, §1's clean line), never a blocklist of governed ones.

---

## Fork I — #400 DRY: extract `lorerunes.wrap_engine_rejection` NOW (the 3rd consumer)

**RULING → EXTRACT NOW, in packet 61, as its own contracted one-concern sub-wave.** The `AuditStore`
(Fork G) is the THIRD store to wrap engine rejections (PrincipalStore + KeepStore + AuditStore) —
**#400's named re-open trigger is exactly met** (*"the 3rd store/consumer that needs engine-rejection
wrapping (e.g. packet 61 PDP, or a governed-store retrofit)"*). Build
`lorerunes.wrap_engine_rejection(DomainError, context)` (a contextmanager/decorator — a PREDICATE/
policy helper, the `lorerunes` chartered content, NOT an entry point), called by all three stores.

**Rationale:**
1. **ONE-IMPLEMENTATION — error classification is POLICY, now cloned 2× and about to be 3×.** The
   packet-60 FR-2 Q2 ruling already made KeepStore a *"SECOND store to encode the same
   wrap-classification policy"* and surfaced the extraction as #400 rather than blessing a silent
   copy #3. Building AuditStore's wrap by hand would be copy #3 — *"you may not quietly write copy
   #2 … duplication is a DESIGN decision, ESCALATE it"* — and the escalation's answer is `lorerunes`
   (the designated home), decided already (#400 body: *"SIDECAR-RULED RESOLUTION … extract a
   `wrap_engine_rejection` helper into `lorerunes`"*).
2. **Don't-kick-the-can + do it at the cheapest moment.** Extracting NOW (2 existing stores + 1 new)
   means AuditStore uses the shared seam FROM BIRTH — never a clone to un-clone later. Deferring past
   61 means a 4th consumer (63/64 governed stores) refactors 3+ stores instead of 2.

**Behaviour (mirror PrincipalStore/KeepStore EXACTLY — FR-2 Q2):** catch `SurrealStoreError`
SPECIFICALLY (not bare `Exception`), re-raise as the store's `DomainError` `from error`
(chain preserved); **re-raise `SurrealConnectionError`/`TxnContentionExhaustedError` FIRST** (they
subclass `SurrealStoreError`, so the connection/contention re-raise must precede the wrap — the exact
KeepStore ordering). The `DomainError` message carries WHAT was rejected (the context).

**RIDER (and pin it like this):**
- **Coverage-as-checked-variable (reach law) — DERIVE the wrap set by property, do NOT hand-list it.**
  The wrapping set is exactly *"every store write-path that today catches `SurrealStoreError` and
  re-raises a domain error"* — DERIVE it, then pin EACH derived member routes through the shared
  helper. ⚠ **My earlier illustrative enumeration in this rider was itself a stale HAND-LIST** (it
  named `PrincipalStore.set_status`, which does NOT wrap at HEAD — FR-2 Q2 wraps `create`/`set_subject`
  only) — the exact reach-law defect this rider warns against, in the rider. The 61a-w2 contract
  DERIVED the real set = **8 paths**: `PrincipalStore.{create, set_subject}` +
  `KeepStore.{create_keep, add_household_member, remove_household_member, set_rank, set_keeper,
  delete_keep}` (+ `AuditStore.append` becomes the 9th, born wrapped). Pin the derived set; a store
  wrapping locally is a private copy (ROUTING-IS-NOT-SHARING) — the FR-2 Q2 *"a wrap on create but not
  add-household is a partial fix"* rule, now ∀-over-the-derived-set. See the D1 addendum below for the
  DRY-not-expansion boundary.
- **Prove sharing by MUTATION:** change the classification inside `wrap_engine_rejection` once (e.g.
  make it also swallow a new error class) → PrincipalStore + KeepStore + AuditStore pins ALL move. A
  store that stays green is not routed through it.
- **Fix the tests that certify the OLD world:** any PrincipalStore/KeepStore pin catching bare
  `Exception` (the green-because-it-asserts-the-corpse hazard) tightens to the specific domain error;
  mutation-prove (remove the wrap → red).
- **Register the new `lorerunes` symbol** — RUN `./scripts/registration_sites.py` (not a list);
  `__init__` re-export + the derived registration sites follow.
- **Its own one-concern commit(s),** landed in sub-packet 61a BEFORE the audit store (so AuditStore
  is born using it).

**⚠ Scope-authority note:** this touches COMMITTED 48/49 (`PrincipalStore`) + 60 (`KeepStore`) code
— a cross-cutting refactor. It is NOT new scope: it is the operator-pre-blessed #400 resolution with
its named trigger firing exactly as designed. I rule it lands at 61 (the trigger fired) under my
delegated authority, surfaced durably (this section + #400) — the FR-2 DRY-flag handling. Not a MAJOR
pivot. **Resolve #400 on the extraction commit.**

---

## Fork J — #398/#399 recurrence invariant: build it FIRST, fully contracted, structural-primary

**RULING → BUILD IT, as its own PROPERLY-CONTRACTED instrument, placed FIRST in packet 61 (sub-wave
61a-w1), as a GATE before the new `audit` schema slice lands.** This executes the packet-60 FR-1
Part 3 ruling (mandatory per standing law; ledgered task `06b195e306a34b6391174477bc7744e7`) and
closes BOTH provenances of one class: **#398** (lead-60: packets 49 + 60) and **#399** (coldaudit-60-w1:
5 sites). The trigger — *"before the next schema-slice TDD wave writes new RED-STUB comments"* — is
literally packet 61: the `audit` table adds `_audit_statements`/`generate_audit_ddl`, whose TDD
contract WILL write RED-STUB comments a builder greens. Build the guard first; it is GREEN on the
current cleaned tree (the stale comments were retired in `efccdc8`/`3077d23` per #398/#399), then it
GUARDS the audit slice.

**Property (refined per the FR-1 reach-attack rider — STRUCTURAL primary, allowlist-the-safe
backstop):**
- **PRIMARY — the STRUCTURAL fold-coverage check (undefeatable by rewording):** the set of
  schema-slice functions is DERIVED by AST-walking `surreal_schema.py` for `def _*_statements`
  returning a non-empty statement list. EVERY such function must be either (a) FOLDED into
  `generate_ddl` (its name appears as a call in `generate_ddl`'s body — also AST-derived) OR (b) a
  member of an EXPLICIT allowlist of intentionally-standalone slices (`generate_manifest_ddl`/
  `generate_memory_ddl`/`generate_task_ddl`/… the slices consumed by a dedicated store's
  `ensure_ready`). A slice fn that is NEITHER folded NOR allowlisted reds the pin — this catches the
  *"NOT folded into generate_ddl"* lie STRUCTURALLY, with no forbidden literal. Coverage-as-checked-
  variable: a NEW slice fn grows the derived set and reds the pin until folded-or-allowlisted.
- **BACKSTOP — the prose-lie leg (allowlist-the-safe, with a NAMED BOUND):** a folded slice fn whose
  docstring/leading-comment asserts EMPTINESS while its body emits ≥1 statement is a defect. Detecting
  "asserts emptiness" needs SOME literal, which is the enumerate-the-forbidden limit — so this leg is
  a BEST-EFFORT backstop over a small closed set of KNOWN emptiness phrasings, **pinned as a KNOWN
  BOUND (§"WHEN YOU CANNOT CLOSE A HOLE, PIN IT")**: a novel phrasing evades it. The PRIMARY defense
  is the structural fold-coverage above; the prose leg only adds cover for an "emit []" comment on a
  *folded* slice. **Re-open trigger:** a new prose-evasion found in the wild → widen the known set OR
  strengthen the structural check.

**RIDER (and pin it like this):**
- **Route through the FULL pipeline** — contract → `contract-adversary` (its P1c REACH ATTACK forces
  the coverage-as-checked-variable + the derived-not-hand-list property) → build → cold-audit. NOT a
  rushed inline text-scan (FR-1 Part 3 verbatim).
- **Mutation-prove BOTH legs:** (structural) remove a slice fn's `generate_ddl` call → the
  fold-coverage pin reds; restore → green. (prose) reintroduce an "emits nothing" comment above a
  folded slice → the prose pin reds; restore → green.
- **Coverage of the guard itself is a checked variable:** the derived slice-fn set is asserted
  non-empty and is re-derived each run (not cached), so a rename of the `_*_statements` convention
  reds the guard rather than silently exempting the renamed fns (the reach law on the instrument
  itself — INSTRUMENT-0).
- **Resolve #398 AND #399 on the invariant's commit** (both are the same class; the fix without the
  invariant was half a fix).

**Scope-authority note:** FR-1 Part 3 already ruled this mandatory + contracted; I rule PLACEMENT
(first, as a gate) + REFINE the property to structural-primary. It is a cross-cutting hygiene
instrument (scope-adjacent, standing-law-mandated), surfaced durably (this section + #398/#399 + the
task). Not a MAJOR pivot.

---

## Fork K — #401 stderr (test-env-fiction): DEFER with an intact trigger + a standing rider

**RULING → DEFER (with #401's existing named owner/trigger), UNLESS the contract phase finds packet
61 ships a `lore-adm` verb that touches the `run_query` rejection seam.** Packet 61 is an in-process
PDP engine + a greenfield append-only `audit` store (written by 63/64 governed tools, no CLI at 61).
On current design it ships **NO new `lore-adm` verb** touching the `run_query` `<label>.rejected`
stderr seam, so it does not reach #401's surface. #401 stays open with its own re-open trigger (*"a
lore-adm consumer relying on the exact stderr first-line, or the principal-CLI test sweep"*).

**STANDING RIDER (binds any 61 CLI/test work that DOES touch the seam):** any NEW CLI error-path
assertion in packet 61 uses **`"lore-adm:" in stderr`, NEVER `startswith("lore-adm:")`** — the #401
honest form (pytest strips the structured `<label>.rejected` line, so a `startswith` pin is green
in-suite and FALSE in production — the test-env-fiction / #131 class). **Confirm at contract time**
whether 61 ships any `lore-adm` verb (e.g. an admin audit-inspect verb). If it does: that verb's
error-path pins inherit the rider, AND #401's broader 48/49-CLI-test sweep becomes scope-adjacent —
surface it to the lead rather than silently absorbing.

**Rationale:** a deferral with an intact named trigger is the legitimate "out-of-authority / not-yet-
triggered" shape (deferral law) — #401 is CLI-wide and pre-existing, not 61-introduced, and 61 does
not add to the seam. The standing rider prevents 61 from CREATING a new instance of the fiction while
the broader sweep waits for its trigger. Not a MAJOR pivot.

---

## Fork L — wave decomposition + sizing

**SIZING VERDICT → packet 61 prices ABOVE 0.30 → SPLIT (sizing law: split ≥0.30 at kickoff).**
As scoped, packet 61 contains: a NOVEL single-brain PDP engine (the highest-design-risk piece in the
whole authz track — per PKT-28 C1, defects are born in the contract/design, and this is genuinely new
design), a new append-only audit store with a security carve-out, a cross-cutting DRY extraction
touching two committed stores, a mandatory recurrence invariant, live-store probes, AND a dedicated
security-auditor pass. That is materially more than one 0.30 packet; the PDP core alone is ~0.25–0.30.

**RECOMMENDED SPLIT — two sub-packets, dependency-ordered:**

### 61a — Foundations + Audit (substrate-flavoured, lower design-risk; ~0.20–0.30)
Mirrors packet 60's shape (a new table + store + shared-seam work). Four one-concern sub-waves, each
its own contract → adversary → build → cold-audit:
- **61a-w1 — the #398/#399 recurrence invariant (Fork J).** FIRST — green on the cleaned tree, guards
  the audit slice. Fully contracted (P1c reach attack). Resolves #398 + #399.
- **61a-w2 — the #402 keeper-on-principal-delete cascade (FR-4).** RESOLVES the RED_ORPHANED gate
  before anything else builds on the substrate: refuse-while-keeping in `PrincipalStore.delete` +
  `member_of` cleanup (probed) + the exact-set pin update + a behavioral no-dangle pin + the admin
  `set-keeper`/`delete-keep` remediation verbs. Resolves #402. Adjacent to 61a-w3 (both touch
  `PrincipalStore`).
- **61a-w3 — `lorerunes.wrap_engine_rejection` extraction (Fork I).** Touches PrincipalStore +
  KeepStore; mutation-proven across both. Resolves #400. Lands BEFORE the audit store so it is born
  using the shared seam.
- **61a-w4 — the `audit` store (Fork G).** `_audit_statements`/`generate_audit_ddl` folded after
  `member_of`; `AuditStore.append` (append-only surface, composable `TxnFragment`); wraps via
  61a-w3's seam. NO audit-query verb, NO governed-tool wiring (63/64).

### 61b — the PDP engine + resolver + coverage (the load-bearing core; ~0.25–0.30)
- **61b-probe — the store-law probes (Fork E: IN-index · composite-index · OR-planner; Fork F:
  leading-column IndexScan).** A GATE at the head — the read-filter emitter's SHAPE depends on the
  results (committed `scripts/probe_*.py`, positive controls). Feeds the 61b-w1 contract.
- **61b-w1 — the PDP core (Forks A/C/D/G-seam), in `lorerunes`.** The IR + `to_surql` + `matches` +
  `Action` enum + `Subject`/`Resource` types + per-action predicates + `authorize`/`authorize_filter`
  + the admin short-circuit + the audit-obligation flag; **the LIVE-STORE ORACLE equivalence test**
  (the load-bearing pin). Its own contract → adversary → build → cold-audit.
- **61b-w2 — the visible-Keeps resolver + coverage (Forks B/F/H).** `KeepStore.list_keeps_for_member`
  + the `loremaster` resolver shell + the tool-classification registry (Fork H-a) + the IR-node
  coverage pin (Fork H-b). Its own pipeline.
- **61b-security-audit — a DEDICATED SECURITY-AUDITOR pass** (design §9/§11 names it the arbiter of
  the enforcement). Scope: the single-brain equivalence (no row writable-but-invisible / visible-but-
  unwritable-by-a-different-rule), cross-principal isolation (≥2 principals × ≥2 agents), the admin
  short-circuit + the audit carve-out (admin can't erase its trail), and injection-containment **AS
  FAR AS 61 OWNS IT**. ⚠ **The 61-vs-62 security-auditor boundary (name it in the brief):** 61's
  auditor grades the PDP's DECISION correctness over a TYPED `Subject`; the CREDENTIAL-MINTING /
  anti-spoofing surface (server-bound `(principal,agent)`, identity-never-from-a-tool-arg) is
  **packet 62's** dedicated auditor (§10-O) — the 61 auditor must NOT chase the credential surface,
  which does not exist at 61.

**Dependency:** 61a → 61b (61b's PDP flags `requires_audit`; 61a's `AuditStore` is what 63/64 append
to; 61b's resolver may wrap via 61a-w3's seam). Within 61a: w1 → w2 → w3 → w4 (w2 resolves the
RED_ORPHANED gate; w3's extraction then covers all three stores incl. w4's AuditStore). Within 61b:
probe → w1 → w2 → security-audit.

**Sizing is a RECOMMENDATION** to the lead/operator; the split BOUNDARY (foundations vs engine) is my
ruling within authority — the sizing law prescribes splitting ≥0.30 at kickoff, so the split is not a
scope expansion (same deliverables, two tracks). If the operator prefers single-packet execution,
that is their call (surfaced); the load-bearing-PDP risk + the sizing law argue for the split, so the
adversary can focus wholly on the novel engine (61b) without the audit/DRY work diluting it.

---

## Store-law compliance checklist (for the contract-adversary + cold audit)

- **`audit` table (Fork G):** plain SCHEMAFULL `IF NOT EXISTS`; fields `OVERWRITE` (§1.1); greenfield
  → required non-`option` fields legal (`actor_principal`/`actor_agent`/`action`/`target_table`/
  `target_row`); `old_value`/`new_value` `option<object> FLEXIBLE` (a CREATE/DELETE lacks one side);
  `created_at datetime DEFAULT time::now()`, store OMITS on write (§2). ULID id (colon-free,
  round-trips via `str(RecordID)`, §2/§10). Folded AFTER `member_of` (link-target-first, §generate_ddl
  order).
- **Call-time-derived domain** (`action` from `_AUDITED_ACTIONS`): mutation-provable (the
  `_principal_statements`/`_keep_statements` idiom — NOT a frozen import join).
- **`AuditStore.append` composability (§3):** a single-statement CREATE composable into a caller's
  `execute_transaction` (never a standalone multi-statement `.query()` — §3 validates statement[0]
  only). 63/64 land audit + mutation in ONE `BEGIN…COMMIT`.
- **The read-filter (Fork A/E) — the load-bearing store-law surface:** emitted with BOUND params,
  never string-interpolated (§2, injection-safe); the `owner_*` equality clauses are IndexScans
  (two indexed record-link fields, the `keep.keeper` precedent); `scope IN $my_keep_scopes` is a flat
  set predicate (design §6 — NO arrow-traversal in the per-row WHERE); the OR-of-clauses planner
  behaviour + `IN` index usage + composite-index-leading-column are PROBED live on 3.2.4 with EXPLAIN
  + positive controls (Fork E) BEFORE the emitter is contracted.
- **The visible-Keeps resolver (Fork F):** plain-table `member_of WHERE in=$principal` (never an
  arrow traversal — §4), IndexScan on the EXISTING `UNIQUE(in,out)` LEADING column (§2 leading-column
  corollary), positive control that the trailing-column read TableScans.
- **The single-brain equivalence (Fork A):** oracle differential test against the LIVE 3.2.4 store —
  NOT a Python mock of SurrealQL (the mock is the false-clear this pin exists to prevent; it cannot
  exhibit the store's `IN`/`option<>`/`SELECT *` semantics).
- **Virgin-DB blind spot (§1.6):** the equivalence/read-filter pins run against a real store; the
  63/64 dirty-store migration (§7) is NOT a 61 concern (61 builds no retrofit) — but the audit store's
  greenfield-vs-retrofit distinction is exactly the store-law §1.4 line and is stated (Fork G).
- **`lorerunes` stdlib-only (Fork B):** the PDP core imports no sibling; pin it (guard, not habit).

---

## Escalation status

**Nothing escalated to the operator.** All twelve forks (A–L) are ruled within delegated authority,
including the sizing SPLIT (the sizing law prescribes it — not a scope expansion). Three items are
surfaced LOUDLY with a clean countermand condition (the packet-60 Fork-A precedent), because each is
a two-reading or load-bearing choice a returning operator may want to flip in ONE ruling without
disturbing the rest:

1. **Fork A — the single-brain MECHANISM** (an IR-with-two-interpreters + a live-store oracle,
   realizing §5's *"the same expression"*). Judged a realization, not a pivot. Countermand: if the
   operator intends a single literal SurrealQL string interpreted only by the engine for BOTH forms,
   flip it (sound, but costs a store round-trip per single-row authorize + cannot check a pre-write
   scope-on-create).
2. **Fork C — `principal-private` WRITE/DELETE owner** (RULED exact-`(principal, agent)`; countermand
   to `owner_principal` if the operator intends within-principal collaboration on private rows
   without a Keep).
3. **Fork G — the audit TRIGGER** (RULED: audit fires when the admin bypass is load-bearing;
   reconciles §9's "every admin action" with its "another principal's row" pin). Countermand to "every
   admin mutation incl. own-row" if the operator wants a maximal trail.

Two cross-scope items are surfaced durably (not escalated — the operator-pre-blessed / law-mandated
handling, Fork-A precedent): **#400 extraction** (touches committed 48/49/60 — the pre-blessed DRY
resolution, trigger met) and the **#398/#399 invariant** (a cross-cutting hygiene instrument,
standing-law-mandated). Both are ledgered; neither is a MAJOR scope/design pivot.

One pre-existing observation is flagged, not fixed: **`KeepStore.list_household`'s trailing-column
`WHERE out=$keep` TableScan** (Fork F rider) — not a 61 blocker (bounded, and the 61 read path uses
the leading column), surfaced for the lead.

---

*Every recommendation is a recommendation; the operator rules the design forks, and the
security-auditor + contract-adversary are the named arbiters of the §9 enforcement (§11). This doc
realizes design `2026-08-21-lore-authorization-model.md` §5/§6/§9 faithfully — the single brain per
action as an IR with a live-store oracle, the append-only admin-exempt audit store as an in-process
guard with a stated threat model, and the reach law applied to what packet 61 can actually check
today.*

---

## Follow-up ruling FR-4 (2026-08-23) — #402 keeper-on-principal-delete cascade (a packet-60 escapee)

Ruling on `lead-61`'s entry-check fork (`lore_comms #5170` · thread `q:keeper-delete-cascade` ·
finding **#402** · the RED_ORPHANED gate
`test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned::test_principal_key_is_the_ONLY_record_principal_link`).
Ground-truthed this session: `PrincipalStore.delete` (`principals.py`, the `delete` verb) cascades
`principal_key` ONLY, inside one `execute_transaction`, and its docstring EXPLICITLY names the
trigger — *"When ANY new `record<principal>` link is added … this cascade MUST be revisited."*
Packet-60 Fork A added exactly such a link (`keep.keeper: record<principal>`) and revisited neither
the cascade nor the pin. The static pin scans `generate_ddl` for every `record<principal>` field and
asserts the set is exactly `{("principal", "principal_key")}`; `keep.keeper` makes the found set
`{("principal","principal_key"), ("keeper","keep")}` — so the pin reddened **exactly as designed**
(PIN THE MISS working). Packet 60 closed on a SCOPED "800 pytest green" run that excluded this file,
so the red shipped ORPHANED — the process-escape half of #402 (*"I verified it" was a claim about a
SCOPE* — the standing verification law).

**Two record-link populations, with DIFFERENT auto-clean behaviour (store-law §4 — the load-bearing
distinction):**
- **`keep.keeper: record<principal>` is a FIELD LINK → does NOT auto-clean on target delete.** A
  hard principal-delete leaves every keep they keep pointing at a phantom keeper — a #105-class
  dangling link (a keep whose `keeper` names a deleted principal; `get_keep` would deref a ghost).
  This MUST be handled.
- **`member_of` (principal `--member_of-->` keep) is a RELATION EDGE → auto-cascades on endpoint
  delete** (store-law §4 verbatim: *"graph RELATION edges DO self-delete when an endpoint node is
  deleted"*; the #7061 fix, SETTLED ABSENT and vendor-confirmed — *"deleting either endpoint
  cascades the edge away and cleans its UNIQUE index entry"*). So the `member_of` edges where the
  deleted principal is `in` SHOULD self-clean. **⚠ #402's body claims they dangle; store-law §4 says
  they auto-clean. This is a load-bearing disagreement — PROBE it live, do not assume either way.**

### RULING → keeper-on-principal-delete = REFUSE-WHILE-KEEPING (NOT cascade-delete, NOT silent-reassign).

A hard `PrincipalStore.delete` is **REFUSED (loud)** when the principal keeps ≥1 keep, naming the
kept keep ids and the remediation. A member-only principal (keeps no keep) deletes cleanly, its
`member_of` memberships cleaned (auto-cascade, probed). The admin remediates a keeper-principal by
**reassigning the keeper** (admin `set_owner` on the keep — §4.3) or **hard-deleting the keep**
(admin `delete` — §4.3), both landed as 61a remediation verbs, THEN deleting the principal.

**Rationale:**
1. **Cascade-DELETE (the lead's option a) is DATA-LOSS for OTHER principals and violates the
   collaboration model.** A keep is a shared collaboration space; cascade-deleting every keep a
   departing principal keeps would VANISH multi-member team/project keeps — and, in 63/64, every
   keep-scoped row every OTHER household member created in them. The design's core principle is
   *"members correct and supersede, they do not vanish each other's work"* (§4); annihilating a
   shared space (and everyone's rows in it) because its keeper's account was deleted is that
   principle inverted, at the container level. An admin deleting one user must never silently
   destroy a team's shared work.
2. **Silent-reassign-to-admin/sentinel (option c) is a SILENT SURPRISE.** The admin deletes a
   principal and, unasked, inherits keepership of N stranger keeps (and their households see their
   keeper silently change). It is less catastrophic than (a) but it is a silent ownership transfer,
   against the whole authz track's *loud-on-failure / no-silent-surprise* discipline (FR-2 Q1 dm
   `--name` reject; FR-3 ghost-keep loud).
3. **REFUSE-WHILE-KEEPING is loud, safe, and forces the explicit decision.** The admin sees *"cannot
   delete principal X: they keep N keeps [ids] — reassign or delete those keeps first."* No data
   loss, no dangle, no silent transfer; the ownership decision (reassign to whom? or delete?) is
   made deliberately. It reuses the authz model's own §4.3 admin authority (`set_owner` /`delete`)
   as the remediation, rather than inventing cascade or sentinel machinery.
4. **It resolves BOTH halves of #402.** The data-integrity bug: no dangling `keep.keeper` can occur
   (you cannot delete a principal while they keep a keep). The gate: the exact-set pin is updated to
   include `keep.keeper` (a deliberate revisit, re-arming the tripwire for the next new link — 63/64's
   `owner_principal`), plus a behavioral pin proves the refuse + the no-dangle.

**Riders (and pin it like this):**
- **The refuse is a LOUD typed error** (a `PrincipalHasKeepsError(PrincipalStoreError)` or reuse the
  domain-error idiom), `exit 1` at the CLI, naming the kept keep ids AND the remediation. Read the
  kept-keep count with `SELECT count() FROM keep WHERE keeper = type::record('principal', $pid)` —
  an **IndexScan on the existing `keep_keeper` index** (packet-60 Fork A), mirroring `delete`'s
  existing `principal_key` count query (no `KeepStore` dependency; the delete issues it on its own
  connection). Pin: a principal-delete with a kept keep → refused, no rows deleted (state unchanged),
  the keep ids in the message.
- **`member_of` cleanup on MEMBER delete — PROBE, then pin.** Run a live 3.2.4 probe (with a
  positive control) confirming that hard-deleting a principal cascades away every `member_of` edge
  where it is `in` (store-law §4 says yes; #402 says no — settle it by construction, committed
  `scripts/probe_*.py`). **If it auto-cascades:** no explicit DELETE needed — pin the property (a
  member-only principal delete leaves zero dangling `member_of` edges) so a future engine change
  reds it. **If it does NOT:** add an explicit `DELETE member_of WHERE in = type::record('principal',
  $pid)` to the delete transaction (children-first, before the principal row — the existing
  `principal_key`-first ordering). This is the #107 *"believed, not probed"* trap — the finding and
  the store reference disagree, so neither is assumed.
- **The exact-set pin update (do BOTH halves):** (1) update the expected set to
  `{("principal", PRINCIPAL_KEY_TABLE), ("keeper", KEEP_TABLE)}` — the deliberate revisit that
  re-arms the tripwire (it will red AGAIN when 63/64 add `owner_principal: record<principal>` to the
  governed tables, forcing THAT cascade revisit — correct). (2) the static pin is only a *"someone
  added a link"* tripwire; add a **behavioral live-store pin** that a keeper-principal delete is
  REFUSED (no dangling `keep.keeper`) and a member-only principal delete cleans its `member_of` — the
  actual cascade-correctness guard. The forward-scope regex positive-control test already exercises a
  synthetic `memory.owner`; extend/confirm it also matches `keep.keeper` (it does — `keep.keeper` is
  why the pin is red).
- **Mutation-prove:** remove the refuse-while-keeping check → the keeper-delete pin reds (a dangling
  `keep.keeper` becomes reachable, or the delete succeeds where it must refuse); restore → green.
  Keep a positive control that a member-only principal delete DOES succeed (rc 0) so the refuse pin
  can see the benign path is preserved (fixtures-must-discriminate: a fixture that only tests the
  keeper case cannot tell *"refuse a keeper"* from *"refuse every delete"*).
- **The remediation verbs (admin §4.3 authority — land in 61a; names RULED in the D1 addendum
  below):** `KeepStore.set_keeper` (admin `set_owner` on a keep — UPDATE `keep.keeper` to a new
  principal; the departing keeper's `member_of` edge stays or is separately managed) and
  `KeepStore.delete_keep` (admin `delete` — cascade the keep + its `member_of` edges; a
  `dm`/sole-member keep's natural remediation). Both are lore-adm admin verbs (admin-by-construction
  — the CLI is CREDS-FREE admin substrate, like packet-60's keep verbs; they need NOT route through
  the 63/64-facing PDP at 61, mirroring the packet-60 keep verbs). Pin each; the `set_keeper` UPDATE
  must keep the keeper a valid principal (ENFORCED-flavoured — a ghost new-keeper is refused). **If
  the lead wants the #402 fix minimal, the remediation verbs are
  a NAMED follow-up** (a keeper-principal stays un-deletable until they land — SAFE, no data loss,
  just inconvenient) — but they are cheap (mirror set-rank / the delete cascade) and complete the
  story, so I RECOMMEND landing them in 61a-w2. Flag to the lead as the one sizing sub-choice.

**The MEMBER dimension, ruled decisively (so no new unpinned ambiguity):**
- **Deleted principal is a KEEPER of ≥1 keep** → **REFUSE** (loud, name the keeps + remediation).
- **Deleted principal is only a MEMBER (keeps nothing)** → **delete PROCEEDS**; their `member_of`
  memberships clean (auto-cascade per store-law §4, probed). A member leaving is normal; the keep +
  keeper + other members survive.
- **Deleted principal keeps nothing and is a member of nothing** → clean delete (the `principal_key`
  cascade only, as today).

**The RED_ORPHANED gate:** resolved by BOTH the pin's expected-set update (ADJUDICATED — the new
`keep.keeper` link is a deliberate, owned addition, cascade-handled by refuse-while-keeping) AND the
behavioral fix (the cascade is actually correct). Per the currency-gate law it moves from
RED_ORPHANED to GREEN (fixed) — NOT merely re-baselined. This MUST land before packet 61's own
close-out currency gate (`scripts/pending_contract_gate.py --currency`), which is exactly why it is
61a-w2 (early), not deferred.

**Scope/authority:** #402 is a packet-60 escapee (the Fork-A `keep.keeper` link's un-revisited
cascade + the orphaned pin), but it is squarely the authorization model's OWNERSHIP-INTEGRITY
concern (§4.3 set_owner/delete authority; the record-link cascade discipline) — so it is IN packet-61
scope, ruled here under my delegated authority, adjacent to the #400 extraction (both touch
`PrincipalStore`). It is a data-integrity correctness fix + a gate resolution, not a MAJOR
scope/design pivot → not escalated. **ONE countermand (the Fork-A precedent):** if the operator
prefers **cascade-DELETE semantics** (accepting that deleting a keeper annihilates their keeps + all
household members' keep-scoped rows — the aggressive reading), countermand this ruling; I rule
refuse-while-keeping because silent multi-principal data-loss on an account delete is the more
dangerous default and contradicts the design's collaboration principle. Resolve #402 on the fix
commit(s).

### FR-4 addendum (2026-08-23) — the three frozen 61a-w1 contract decisions (D1 · D2 · D3)

Ruling on `lead-61`'s `lore_comms #5174` (thread `q:61a-w1-contract-decisions` · `REPORT-contract-61a-w1.md`).
**The contract's probe SETTLED the FR-4 open question:** `member_of` auto-cascades BOTH endpoints on
delete, `keep.keeper` dangles — so #402's body claim (dangling member_of) is REFUTED, refuse-while-keeping
is confirmed, and **no explicit `member_of` DELETE is needed** (the store-law §4 auto-cascade the FR-4
rider required a probe for is now proven live). FR-4 stands as ruled.

**D1 — remediation verb names → RULED (b) `set-keeper` / `set_keeper` / `--new-keeper` (kwarg
`new_keeper_email`), COUNTERMANDING the lead's lean (a) `reassign-keeper`.** The delete verb keeps
`delete-keep` / `delete_keep` (both options agreed). ⚠ This is a countermand — it forces the one
contract edit (verb root + kwarg), which is why the lead froze the adversary on it.
- **Rationale (design-vocabulary, three converging reasons):** (1) **the design spec's own method
  name is `set_owner`** (§4.3: *"reassign ANY owner (set_scope/**set_owner**/delete across all
  rows)"*) — a keep's owner IS its `keeper` field, so the spec-faithful keep-flavoured spelling of
  `set_owner` is `set_keeper` (the prose word "reassign" describes what it does; the METHOD name in
  the spec is `set_*`). (2) **Keep-verb-family consistency (CLAUDE.md naming law).** The family is
  `create-keep`/`delete-keep` (`<verb>-keep`), `add-household`/`remove-household` (`<verb>-household`),
  `set-rank` (`set-<field>`). `set-keeper` slots into the `set-<field>` pattern (`set-rank` sets the
  edge's rank field; `set-keeper` sets the keep's keeper/owner field) — THREE patterns. `reassign-keeper`
  would open a FOURTH (`reassign-<field>`) pattern for one verb. (3) `keep.keeper` is a FIELD;
  `set-keeper` reads as "set the keeper field," least-surprise for an admin reading `--help` beside
  `set-rank`.
- **The lead's (a) gravity argument acknowledged and outweighed:** yes, an ownership transfer is
  weightier than a rank tweak — but the spec already chose the `set_*` vocabulary for exactly this
  (`set_owner`), and one-consistent-root (CLAUDE.md) beats gravity-signalling. The store-method name
  I used casually in the FR-4 body (`reassign_keeper`) is SUPERSEDED by this ruling — the FR-4 body
  references above are updated to `set_keeper`.
- **Rider:** `set-keeper --keep <id> --new-keeper <email>` → `KeepStore.set_keeper(*, keep_id,
  new_keeper_email)` → UPDATE `keep.keeper` to the resolved new-keeper principal; a ghost keep is
  LOUD (`KeepNotFoundError`, D2 parity), a ghost new-keeper principal is LOUD (`KeepStoreError` "no
  principal with email", the `_resolve_principal_id` idiom). Mutation-prove the UPDATE actually moves
  `keep.keeper` (a set-keeper that no-matched must not read as success — the FR-3 silent-no-op class).

**D2 — `delete-keep` / `delete_keep` on a GHOST keep → CONFIRMED LOUD (`KeepNotFoundError`).** Exactly
FR-3's ruling class: a DESTRUCTIVE access-control verb on a nonexistent target is LOUD, never a silent
no-op (a typo'd `--keep` must not read as *"deleted"* when nothing was deleted — the false-success
class FR-3 named the most dangerous in an authz substrate). FR-4 was silent on delete-keep's ghost
behaviour; this fills it, consistent with `remove-household`'s ghost-keep loudness (FR-3 reading (a))
and the ∀-keep-consuming-verb *"a nonexistent `--keep` is LOUD"* invariant FR-3 pinned. There is NO
member-dimension idempotency wrinkle here (delete-keep has no `--member`): a keep either exists (delete
it) or does not (loud). **Rider:** pin the ghost-keep-loud + no-partial-state; `delete-keep` on a REAL
keep DELETEs the keep row (its `member_of` edges auto-cascade — the settled probe; no explicit member_of
DELETE). ⚠ **63/64 forward-boundary:** at 61 a keep holds no governed keep-scoped rows, so delete-keep
cascades only keep + member_of; when 63/64 add `scope='keep:<id>'` governed rows, delete-keep MUST
revisit whether it cascades or orphans them — a NAMED trigger for 63/64 (record-link cascade discipline,
the same #402 class one layer out), not a 61 concern.

**D3 — #131 keep-table readiness on the delete path → RULED (a), KEEP SLICE (not full `generate_ddl`).**
Ground-truthed the readiness pattern this session (`principals.py` `_dispatch` / `_dispatch_keep`): the
established idiom is **each dispatch branch readies EXACTLY the schema slices its verbs touch** —
`_dispatch` readies `principal` + `principal_key`; `_dispatch_keep` readies `principal` + the keep slice
(principal FIRST, for `member_of`'s ENFORCED `IN principal`). The `delete` verb now READS the `keep`
table (the refuse-while-keeping count), so its branch must ready the keep slice too — option (a).
- **Slice, NOT full `generate_ddl`:** the lore-adm CLI is CREDS-FREE and resolves ONLY the surreal
  block (the packet-49 ruling) — it has **no embedder `dim`**, and `generate_ddl(dim=…)` both requires
  one and would build the `chunk`/`memory` HNSW indexes + analyzers an admin CLI has no business
  touching. The established pattern is slices; ready `generate_keep_ddl` (keep + member_of), principal
  FIRST (the `_dispatch_keep` ordering). Option (b) (tolerate an absent keep table as 0 keeps) is
  REJECTED: it makes the admin CLI operate against an un-migrated schema and leans on the unprobed
  "SELECT from an undeclared table returns [] not raises" behaviour — fragile, and it swallows the
  "this store predates packet 60" signal. **The admin CLI should run against a migrated schema.**
- **⚠ THE #131 RIDER (the load-bearing part — a virgin-DB fixture CANNOT see this):** every test mints
  a virgin DB with the FULL schema (`generate_ddl`), so a *"delete reads an unreadied keep table"*
  failure is INVISIBLE to the ordinary suite — this is #131/#107 test-env-fiction verbatim. Pin it with
  a **DIRTY-STORE fixture: ready ONLY the pre-60 slices (`principal` + `principal_key`), then run
  `delete`** — and assert (i) a keeper-principal is refused (not an undeclared-table crash), (ii) a
  member-only principal deletes clean. This is the ONLY fixture shape that reproduces the hazard; a
  full-schema fixture proves nothing about it. (Optional, cheap, settles the ambiguity: probe whether a
  SELECT from an undeclared table raises or returns [] — but (a) is correct regardless, so it is not a
  gate.)
- **Placement/coupling (implementation detail, lead's call):** ready the keep slice at the `_dispatch`
  principal branch (consistent with the branch-readies pattern — mild: every principal verb builds a
  KeepStore + one idempotent `ensure_ready`) OR only on the `delete` path (precise, but a handler doing
  its own readiness breaks the dispatch-readies/handler-runs separation). I recommend the branch-level
  readiness (consistency); either satisfies the ruling. The DESIGN ruling is: option (a), keep slice,
  principal-first, #131 dirty-store pin.

**Escalation/authority:** all three are design-vocabulary / readiness rulings within my delegated
authority (the lead explicitly routed them here). D1 is the one countermand (verb name); D2/D3 confirm
the lead's leans. None is a MAJOR scope/design pivot. The operator's clean countermand on D1 (if they
prefer `reassign-keeper`'s gravity over `set-keeper`'s consistency) is a single verb-root flip.

### Fork I addendum (2026-08-23) — the two 61a-w2 wrap-extraction design points (D1 · D2)

Ruling on `lead-61`'s `lore_comms #6002` (thread `q:61a-w2-seam` · `REPORT-contract-61a-w2.md`). Both
guide the builder; neither blocks the (binding-agnostic) adversary already running.

**D1 — SCOPE of the wrap set → CONFIRMED: #400 is DRY-NOT-EXPANSION (behaviour-preserving), over the
DERIVED 8-path set; the currently-unwrapped paths are a SEPARATE ledgered consumer-law question.**
- The contract author DERIVED the actual wrapping set by property (not a hand-list) =
  `PrincipalStore.{create, set_subject}` + `KeepStore.{create_keep, add_household_member,
  remove_household_member, set_rank, set_keeper, delete_keep}` = **8 paths** (+ `AuditStore.append`,
  born wrapped = the 9th). That derivation is correct and is the method Fork I's own rider MANDATED —
  and it caught that my illustrative prose (`set_status`) was a stale hand-list (set_status does NOT
  wrap at HEAD; FR-2 Q2 = create/set_subject only). **The catch is the reach law working exactly as
  written, on this very doc — I've corrected the rider above.** Good catch; derive-by-property wins,
  every time, over a hand-list (including mine).
- **#400 = DRY the EXISTING wraps, byte-behaviour-preserving.** Extracting the shared seam must NOT
  add wraps to the currently-unwrapped paths (`set_status`, `set_expires`, `delete`) — that is a
  BEHAVIOUR CHANGE (coverage expansion), a DIFFERENT concern, and it would muddy the mutation proof
  (the "all callers move" proof needs a FIXED caller set; adding callers mid-refactor breaks the clean
  before/after). One-concern-per-commit: DRY now, coverage later.
- **The unwrapped paths are a SEPARATE potential FR-2-Q2 consumer-law gap → LEDGER with a trigger, NOT
  in w2.** I do NOT rule them wrap-or-stay now, because it needs a REACHABILITY analysis, not a
  reflex: a path is a real gap only if it has a REACHABLE engine rejection with a domain meaning that
  leaks RAW to the caller (e.g. `set_status` with an out-of-domain status would hit the closed-domain
  ASSERT and leak `SurrealStoreError` — UNLESS the lore-adm CLI's argparse `choices=` makes a bogus
  status unreachable, in which case there is no raw-leak path and it is unwrapped BY DESIGN). That
  per-path reachability check is the separate item's job. **Recommend the lead file it** (`lore_findings`,
  FR-2-Q2 consumer-law completeness sweep of the currently-unwrapped principal-store write paths),
  **trigger:** *the moment any unwrapped path is shown to leak a raw `SurrealStoreError` to a consumer,
  OR a governed-tool (63/64) consumes one of these verbs and needs the clean domain error.* Behaviour-
  preserving DRY (w2) does not wait on it.

**D2 — the SEAM SHAPE under lorerunes stdlib-purity → RULED (a): a TWO-LAYER seam. Confirm the lead's
lean; reject (b).**
- **Layer 1 (lorerunes, stdlib-only) — the generic control-flow POLICY.** A helper (contextmanager)
  parameterised over exception CLASSES it receives as arguments — it never imports a surreal type, it
  just applies the classify-and-reclassify control flow over `BaseException` subclasses passed in.
  Shape:
  ```
  @contextmanager
  def reclassify(*, passthrough: tuple[type[BaseException], ...],
                 catch: tuple[type[BaseException], ...],
                 make_error: Callable[[], BaseException]):
      try: yield
      except passthrough: raise                      # ⚠ FIRST — passthrough SUBCLASSES catch
      except catch as error: raise make_error() from error
  ```
  This is chartered `lorerunes` content (its `__init__` names *"error classification"* explicitly) and
  is a POLICY helper, not an entry point. The `passthrough`-FIRST ordering is the load-bearing
  correctness FR-2 Q2 established (`SurrealConnectionError`/`TxnContentionExhaustedError` SUBCLASS
  `SurrealStoreError`, so they must be re-raised before the catch translates).
- **Layer 2 (loremaster) — the ONE surreal taxonomy binding.** `loremaster.store._txn.wrap_store_rejection(domain_error, context)`
  (the address the ref build already used) binds the surreal taxonomy ONCE —
  `passthrough=(SurrealConnectionError, TxnContentionExhaustedError)`, `catch=(SurrealStoreError,)`,
  `make_error=lambda: domain_error(context)` — and delegates the control flow to `lorerunes.reclassify`.
  All 9 store write-paths call `wrap_store_rejection`. The taxonomy lives in exactly one place;
  `_txn` already owns these three exception types, so it is their natural home.
- **RULE the target address so the builder + the mutation pin have ONE:** stores call
  `loremaster.store._txn.wrap_store_rejection(<DomainError>, <context>)`; it delegates to
  `lorerunes.reclassify`. (Contextmanager over a decorator: the wrapped body is an `await
  execute_transaction(...)` / `await self._query(...)`, so a `with` block reads cleaner than
  decorating each method; either is acceptable — the builder rules the ergonomic form, the ADDRESSES
  are ruled.)
- **REJECT (b) (stores call `lorerunes` directly, each passing the taxonomy):** it reintroduces the
  #400 defect ONE LEVEL DOWN. Each store would hand-write `passthrough=(SurrealConnectionError,
  TxnContentionExhaustedError), catch=(SurrealStoreError,)` at its call site — the taxonomy tuple
  becomes a per-store CLONE, and a taxonomy change (a new pass-through class) reaches one store and not
  the others. That is ROUTING-IS-NOT-SHARING verbatim: all stores call the shared control-flow while
  hand-rolling the classification DECISION. The whole point of #400 is that the classification is ONE
  thing; (b) keeps the control-flow DRY but re-clones the classification.
- **TWO-LAYER mutation proof (the prove-sharing rider, now spanning both layers):** mutating EITHER
  layer must move all 9 callers' pins — (i) change `lorerunes.reclassify`'s control flow (e.g. drop
  the `from error` chain) → every caller's chain-preservation pin reddens; (ii) change the
  `_txn.wrap_store_rejection` taxonomy binding (e.g. remove `TxnContentionExhaustedError` from
  `passthrough`) → every caller's contention-passes-through pin reddens. A caller that stays green
  under EITHER mutation is a private copy. This is the ROUTING-IS-NOT-SHARING two-address test: one
  address for control-flow (lorerunes), one for taxonomy (loremaster `_txn`), both shared.

**Escalation/authority:** both are Fork-I design-fill / DRY-placement rulings within my delegated
authority (the lead routed them here). D1 confirms + fixes my own stale hand-list; D2 confirms the
lead's (a) with the two-layer addresses named. Neither is a MAJOR scope/design pivot. Register the new
`lorerunes.reclassify` + `_txn.wrap_store_rejection` symbols per `./scripts/registration_sites.py`
(not a hand-list — the lesson D1 just re-taught).

### Fork I addendum-2 (2026-08-23) — the 61a-w2 reach-scope fork (the guard property + the clone scope)

Ruling on `lead-61`'s `lore_comms #6005` (thread `q:61a-w2-reach-scope` · `REPORT-adversary-61a-w2.md`).
The adversary's CORE finding is CORRECT and valuable: within the ruled Principal+Keep scope the contract
is decisively sufficient (8 wrong builds caught incl. ROUTING-IS-NOT-SHARING), and the SOLE gap is that
the coverage guard's cross-store reach is a **2-store HAND-LIST** (`_CASES={keep,principal}`) — the
reach-law defeat. That is a real, non-negotiable fix.

**⚠ BUT I VERIFIED THE NAMED CLONE SITES (read each this session) AND THE ADVERSARY LUMPED THREE
DISTINCT IDIOMS under "the identical #400 wrap idiom." This changes both items.** `except
SurrealStoreError` is a SURFACE shared by at least three DIFFERENT policies:
- **(i) the #400 WRAP idiom — a PURE TRANSLATE:** the handler's SOLE body is `raise
  <DomainError>(...) from error` (no follow-up read, no branch). Sites: the in-scope
  `PrincipalStore.{create,set_subject}` + `KeepStore.{6}`, AND **`principal_keys.py:~418` →
  `PrincipalKeyStoreError`** (verbatim, comment copy-pasted — a GENUINE out-of-scope clone).
- **(ii) the CAS-RE-VALIDATION idiom — NOT a wrap:** `tasks.py:~1678/~2006` and `findings.py:~1088`
  (and the belt-and-braces `findings.py:~1033`) catch the rolled-back txn, then **do a follow-up read
  (`_select_row`/`_select_row_by_id`) + `_validate_transition`** to raise a STATE-SPECIFIC error naming
  the now-current status and the refused target (the audit-#1 lost-race false-success guard). **Routing
  these through `wrap_store_rejection` would DELETE the re-read + re-validation — a REGRESSION** (the
  removed-behavior-inventory law; the lost-race state-naming vanishes).
- **(iii) the FENCE-VERDICT idiom — NOT a wrap:** `floor_calibration/store.py:~417` catches, then
  `if fence is None: raise` else `verdict = await self._fence_verdict(error, fence)` — a BRANCH +
  follow-up, not a translate. Routing it through the wrap seam would delete the fence-verdict path.
- (For completeness, also on this surface but never in question: `briefs.py` idempotent-re-ack /
  version-not-released SIGNAL detection; `index/indexer.py` degradation-LOG-and-continue.)

**So the adversary's "6 wrap clones" is really: 1 true out-of-scope wrap clone (`principal_keys`) + a
DIFFERENT idiom (CAS re-validation) cloned in tasks/findings + a fence idiom in floor_calibration.**
The clone CLASS #400 governs is smaller than reported; two of the "clones" must NOT be extracted.

### Item 1 — the coverage guard property → RULED (non-negotiable), keyed on the PURE-TRANSLATE SHAPE.

The guard must be PROPERTY-DERIVED (allowlist-the-safe), AST-walking EVERY loremaster module — but keyed
on the **wrap idiom's STRUCTURE, not the `except SurrealStoreError` surface**, or it would demand
breaking the CAS/fence idioms (item (ii)/(iii)). The property:
> **An `except SurrealStoreError as <e>:` clause whose body is EXACTLY a single `raise
> <DomainError-subclass>(...) from <e>` (a pure translate) MUST NOT appear in any loremaster module
> outside `loremaster.store._txn.wrap_store_rejection`.** Every such site routes through the shared
> seam; the escape hatch is an EVIDENCE-BACKED allowlist (empty today — post-extraction the pure-
> translate `except` shape is replaced by `with wrap_store_rejection(...)` everywhere, so it should
> occur NOWHERE).
- **This discriminates correctly by construction:** the pure-translate shape matches the wrap clones
  (Principal/Key/Keep) and a future new-store clone; it does NOT match the CAS idiom (its body has a
  read + `_validate_transition`), the fence idiom (a branch), the signal idiom, or the log idiom — so
  the guard never falsely demands breaking them, and no hand-list of "which stores are exempt" is
  needed (the SHAPE exempts them).
- **Threat model (state it IN the guard — a gate needs a threat model):** this catches the HONEST
  engineer who COPY-PASTES the wrap idiom verbatim (exactly how `principal_keys` cloned it — "comment
  copy-pasted"). It is NOT a boundary against a deliberate evader who adds a no-op statement to dodge
  the shape match — that is out of scope by construction, ledgered not paid for.
- Reds at HEAD (the un-extracted pure-translate clones exist), green post-extraction (all replaced by
  `with`), reds a future pure-translate clone. Mutation-prove: reintroduce a bare pure-translate
  `except SurrealStoreError → raise DomainError from e` in any store → the guard reds.

### Item 2 — the scope fork → RULED Option B′ (a corrected B): route the ONE true clone now, ledger the CAS idiom separately. NOT escalated.

Neither of the lead's framed options survives the idiom correction: Option A ("extract all 6") would
route the CAS/fence idioms through the wrap seam (deleting behaviour — a regression); Option B ("keep
scope + allowlist the 4 deferred clones") mislabels 3 non-clones as deferred wrap clones (a stale/wrong
ledger entry) and defers `principal_keys` — a TRUE clone one `with`-block away from the seam being built
(a can-kick). **RULE B′:**
- **Route the ONE true out-of-scope wrap clone — `principal_keys` — through `_txn.wrap_store_rejection`
  in w2, alongside Principal+Keep.** It is the IDENTICAL idiom, verbatim, in the SIBLING 48/49
  substrate store (principal/principal_key are one family); extracting it is one `with` block and it
  COMPLETES the wrap-clone class for the substrate stores (Principal+PrincipalKey+Keep now, Audit
  born-wrapped in w4 = the whole `record`-substrate family). This is **NOT a MAJOR scope expansion**
  (one site, same idiom, sibling store — it does NOT reach the 63/64 ledger write paths or any
  different idiom), so it is ruled within my authority, not escalated. Don't-kick-the-can: a trivial
  true clone the seam is being built for anyway.
- **Do NOT touch tasks / findings / floor_calibration** — they are DIFFERENT idioms (CAS
  re-validation, fence verdict), not wrap clones; the shape-keyed guard correctly does not flag them,
  so no allowlist entry is needed for them (they were never in the guarded class).
- **Ledger the CAS-RE-VALIDATION idiom's OWN duplication as a SEPARATE DRY finding** (it is genuinely
  cloned across `tasks.py`×2 + `findings.py`×1–2 — a "lost-CAS → re-read fresh → `_validate_transition`
  → raise a state-named lost-race error" POLICY). It is a real second DRY candidate but a DIFFERENT
  policy from #400, and **63/64 rework the tasks/findings write paths anyway** (the lead's own note) —
  so the NAMED TRIGGER is *the 63/64 governed-ledger retrofit* (consider extracting a shared
  `revalidate_lost_cas` seam THEN, when those paths are already open), or sooner if a 3rd CAS clone
  appears. Recommend the lead file it (`lore_findings`, category `design`/DRY, area
  `loremaster.tasks + loremaster.findings CAS re-validation`). This is the standing-law "pin the bound
  with a named trigger" form — applied to the RIGHT class.

**Net:** w2 routes Principal + PrincipalKey + Keep through the two-layer seam (Audit born-wrapped, w4);
the guard is property-derived on the pure-translate shape (kills the wrap-clone class + reds any future
clone); the CAS/fence idioms are correctly untouched and the CAS-duplication is ledgered to its proper
63/64 home. No scope expansion into 63/64 territory, the wrap-clone class is DEAD, and no non-clone is
mislabelled. **Escalation:** none — B′ preserves scope (the one added site is same-idiom sibling
substrate, not major); the operator's clean countermand, if any, is "route the CAS idiom now too"
(Option A-flavoured), which I advise AGAINST (regression risk + 63/64 will rework those paths).

**Contract revision needed (builder held):** (1) replace the 2-store `_CASES` hand-list with the
shape-derived guard (item 1); (2) add `principal_keys` to the routed set (item 2); (3) the
mutation-sharing pin now spans Principal+PrincipalKey+Keep (all move when either seam layer mutates);
(4) NOTHING for tasks/findings/floor beyond the ledgered follow-up. Then re-grade.

### Fork I addendum-3 (2026-08-23) — the 10th clone: route `transitive_blockers` (RULE B)

> ⚠ **SUPERSEDED by addendum-4 (2026-08-23).** This section's conclusion — *route
> `transitive_blockers`, 10 total* — is REVERSED. Ground truth: `transitive_blockers` has NO
> passthrough-first clause, so it deliberately wraps TRANSPORT faults (a documented behaviour); routing
> it would CHANGE that contract — my "zero-regression" here was an unverified assumption. The routed set
> is **9**, `transitive_blockers` is PRESERVED, and the shape-guard is tightened to the FULL #400 idiom.
> Read addendum-4 for the current ruling. This section is kept for the reasoning trail (why the loose
> shape-guard first flagged it) — its conclusion does not bind.

Ruling on `lore_comms #6008` (thread `q:61a-w2-reach-scope`). The property-derived SHAPE guard (item 1
of addendum-2) found a **10th pure-translate clone that BOTH the adversary's hand-list AND my own
named-site read in addendum-2 MISSED**: `tasks.py::transitive_blockers` — a READ-path traversal-rejection
wrap whose `except SurrealStoreError as error:` handler's SOLE body is `raise TaskLedgerError(...) from
error` (verified this session). It is a genuine #400 wrap clone; it is correctly DISTINCT from the CAS
re-validation sites (`tasks.py:1678/2006`) the shape guard already excludes (those do a follow-up read).

**⚠ This FALSIFIES my addendum-2 premise "tasks has NO pure-translate wrap (only CAS/fence)."** It was
true of the three sites I READ (1678/2006/1088) and FALSE of the one I did not (transitive_blockers). And
the correction was made by MY OWN RULED INSTRUMENT: the shape guard is the property-derived detector, my
addendum-2 site-classification was the fallible hand-list — this is the SECOND time in this fork the
property beat the hand-read (D1 caught my stale `set_status`; this caught the missed `transitive_blockers`).
The lesson is exactly the one this fork keeps teaching: **derive by property, do not trust a read.** The
scope boundary is the SHAPE (a pure-translate wrap), never the store FAMILY — my "record-substrate family"
framing in addendum-2 was a proxy that under-counted; the shape is the property.

**RULING → B: ROUTE `transitive_blockers` now, through `_txn.wrap_store_rejection`.** (Confirms the lead's
lean; the contract author's A is rejected.)
- **A (allowlist it as deferred) reintroduces the reach-law defeat this fork exists to kill.** The whole
  virtue of the item-1 shape guard is being ALLOWLIST-FREE — the shape classifies correctly, so no
  hand-list is needed. A 1-entry allowlist is a hand-list creeping back in, and it would NOT be
  evidence-backed (the deny-by-default rule requires a live-proven reason to exempt): transitive_blockers
  is a pure-translate wrap identical in policy to the other 9, with NO 63/64 reason to stay separate.
  Deferring it "same as the CAS idiom (#407)" re-commits the addendum-2 LUMPING error in reverse — it is
  NOT the CAS idiom (that does a re-read; this is a pure translate), so it does not belong on #407's
  63/64 trigger.
- **B is zero-regression + completes the class.** It is pure-translate, so `with
  wrap_store_rejection(TaskLedgerError, "the upstream blocker walk for task … was REJECTED …")` preserves
  the exact translate byte-for-byte. One method, one `with` block. The routed set becomes the full
  **10 pure-translate wraps** — `PrincipalStore{create,set_subject}` (2) + `PrincipalKeyStore.mint` (1) +
  `KeepStore{create_keep,add_household_member,remove_household_member,set_rank,set_keeper,delete_keep}` (6)
  + `TaskLedger.transitive_blockers` (1) — with `AuditStore.append` born-wrapped (w4). The guard's
  allowlist stays EMPTY; the pure-translate `except` shape occurs NOWHERE outside the seam.
- **No 63/64 conflict.** transitive_blockers' engine-rejection WRAP is orthogonal to 63/64's owner/scope
  read-filter work (63/64 adds scoped visibility to governed-ROW reads; this is a blocker-graph traversal
  whose store-rejection translate 63/64 would build ON, not rework). So routing now creates no pre-touch.

**Unchanged:** the CAS re-validation idiom (tasks 1678/2006 + findings 1088/1033) remains a SEPARATE DRY
finding (#407) with the 63/64 trigger — transitive_blockers is NOT part of it. **Escalation:** none —
routing one orthogonal read-method's wrap is not a MAJOR expansion (same non-escalation logic as
principal_keys), and it is REQUIRED to honour item-1's allowlist-free property. **Contract revision:** add
`transitive_blockers` to the routed set (10 total); the mutation-sharing pin spans all 10; the guard stays
allowlist-free (empty). Then re-grade.

### Fork I addendum-4 (2026-08-23) — CORRECTION: preserve `transitive_blockers`, tighten the guard to the FULL #400 idiom (routed set = 9)

Ruling on `lore_comms #6011` (thread `q:61a-w2-reach-scope`), which GROUND-TRUTHED and FALSIFIED
addendum-3's "route it, zero-regression." I verified it independently this session (`tasks.py:2495-2513`
+ the contrast with `keeps.create_keep`): **`transitive_blockers` has ONLY `except SurrealStoreError as
error: raise TaskLedgerError(...) from error` — NO passthrough-first `except (SurrealConnectionError,
TxnContentionExhaustedError): raise` clause.** The nine true #400 clones ALL have the passthrough-first.
So transitive_blockers DELIBERATELY wraps transport/contention faults (both subclass `SurrealStoreError`)
into a uniform "retry" `TaskLedgerError` — DOCUMENTED in its `Raises:` + the handler comment. **Routing it
through `wrap_store_rejection` (which re-raises transport/contention FIRST) would make transport
PROPAGATE instead of wrapping — a CHANGE to a documented contract + the served blockers-error surface.**
It shares only the TRANSLATE LINE with #400, not the #400 POLICY (transport-propagate-THEN-translate).

**RULING → PRESERVE + REFINE (confirm the lead's recommendation; reject route-and-fix):**
- **PRESERVE `transitive_blockers`'s documented wrap-everything behaviour — do NOT route it.** Routed
  set returns to **9** (`PrincipalStore{create,set_subject}` + `PrincipalKeyStore.mint` +
  `KeepStore{6}`; `AuditStore.append` born-wrapped in w4).
- **REFINE the item-1 shape-guard to key on the FULL #400 idiom, not the translate line:** a
  `try` whose handlers include a passthrough-first re-raise of BOTH `SurrealConnectionError` AND
  `TxnContentionExhaustedError` PRECEDING a sole-body `except SurrealStoreError as e: raise <Domain>(...)
  from e`. Still property-derived (a structural handler-GROUP pattern over all loremaster modules, no
  hand-list); allowlist STILL EMPTY. This correctly EXCLUDES `transitive_blockers` BY SHAPE (it has no
  passthrough-first) and reds a future FULL-#400 clone. Post-extraction the full-idiom structure occurs
  nowhere outside the seam.
- **LEDGER `transitive_blockers`'s transport-wrap-everything as a SEPARATE transport-consistency
  question** (finding, area `loremaster.tasks.transitive_blockers`): is wrapping `SurrealConnectionError`
  into a domain `TaskLedgerError` a latent bug (a transport fault the shared driver already exhausted,
  surfaced as "retry" rather than propagated like every other path) OR a documented deliberate choice
  for a read that cannot serve a partial answer? NOT #400's call, NOT this wave's — trigger: a
  transport-fault-handling consistency pass, or the 63/64 tasks rework. Recommend the lead file it.

**Route-and-fix (the ALTERNATIVE) is REJECTED and would need the operator.** Making transitive_blockers
propagate transport for consistency CHANGES a documented contract + a served surface — a behaviour
change, not a DRY refactor, so per my escalation trigger it would go to the operator. I do NOT pick it:
preserve+refine is behaviour-safe and makes the guard correctly keyed on the actual #400 policy. **So
nothing is escalated.**

**⚠ THE META-LESSON, OWNED — this is the THIRD instrument-correction in this one fork, and it landed on
MY OWN guard:** (1) D1 caught my stale `set_status` prose hand-list; (2) addendum-3 caught the
`transitive_blockers` site my named-site read missed; (3) NOW the lead's ground-truth caught my
SHAPE-GUARD being keyed on the TRANSLATE LINE — a SUBSTRING of the full #400 idiom — and defeated by a
site carrying that substring under a DIFFERENT policy (wrap-everything). **This is CLAUDE.md's instrument-
lesson table exactly** (*"keyed on X, defeated by a substring of X"*), now on the guard I myself ruled as
the fix. Two compounding errors of mine: I keyed the guard on a fragment of the idiom rather than the
whole policy, AND I asserted "zero-regression / byte-identical" for routing it WITHOUT verifying the
transport-fault path (the passthrough-first absence) — an assume-don't-verify claim the lead correctly
refused to take on faith and ground-truthed. **The fix is the same each time: key the property on the
FULL policy (the complete passthrough-first+translate structure = the safe/complete set), never a
recognizable fragment of it; and verify a "no-behaviour-change" claim against the ACTUAL handler, never
assert it from the happy-path line.** The lead's discipline — *a subagent's "zero-regression" is a
claim, not a sign-off; ground-truth it* — is why this did not ship.

**Contract revision (builder still held):** routed set = 9 (drop `transitive_blockers`); the shape-guard
keys on the FULL passthrough-first+translate idiom (still allowlist-free, empty); the mutation-sharing
pin spans the 9; `transitive_blockers` untouched + its transport-wrap ledgered separately. Then re-grade.

### Fork G addendum (2026-08-23) — audit.actor cascade disposition (the #402 tripwire's 3rd link)

Ruling on `lore_comms #6032` (thread `q:61a-w4-audit-cascade`). The w4 audit build fired the #402/FR-4
re-armed tripwire: `audit.actor_principal` is the THIRD `record<principal>` link (after
`principal_key.principal` + `keep.keeper`), so the exact-set pin demands a delete-cascade ruling.
Verified the built field set (`_AUDIT_FIELD_SPECS`): actor is `actor_principal: record<principal>` +
`actor_agent: record<agent>`, with NO denormalized human-identity value.

**RULING → DANGLE-TOLERATED for `audit.actor_principal` AND `audit.actor_agent` — and it is COHERENT
with #402, not a second arbitrary call, via one unifying principle:**

> **A record-link's cascade disposition follows the target's ROLE in the referencing row:**
> - **A LIVE DEPENDENCY** — the row NEEDS the target to resolve to FUNCTION (`keep.keeper`: a keep
>   must have a resolvable keeper to be managed/used) → **REFUSE / reassign** on target delete. A
>   dangling live-dependency corrupts a live, in-use object (#105).
> - **A HISTORICAL REFERENCE** — the row RECORDS that the target was involved at a PAST time, an
>   immutable fact (`audit.actor`: "principal P, agent A, did action X at time T") → **DANGLE-
>   TOLERATED**. The fact stays true after the actor is gone; cascade-delete would let an admin ERASE
>   THEIR OWN TRAIL by deleting a principal (re-opening the §9 append-only-admin-exempt hole), and
>   refuse-while-having-audit-rows would make essentially every principal permanently un-deletable
>   (everyone accrues audit rows). Both alternatives are wrong for a historical reference.

So `principal_key.principal` (cascade-delete: a key is owned data that dies with its owner),
`keep.keeper` (refuse: a live dependency), and `audit.actor` (dangle: a historical reference) are ONE
rule applied to three link-ROLES — the coherent generalization the #402 story needed. **The next new
`record<principal>` link — 63/64's `owner_principal` on the governed tables — is a LIVE dependency-class
link (a governed row's current owner), so it will be cascade-or-refuse, NOT dangle; 63/64 disposition it
by this principle, not ad hoc.**

**Pin expected-set edit (confirm the builder's + the lead's proposal):** add `("actor_principal",
AUDIT_TABLE)` to the `record<principal>` exact-set, **annotated inline as a KNOWN DANGLE-TOLERATED link
with the §9 rationale** (an audit record outlives its actors; `PrincipalStore.delete` deliberately does
NOT cascade or refuse for it — the record id survives per store-law §4, a FETCH just returns None). The
tripwire stays armed for the next link. **Prefer** the disposition as a CHECKED variable — a small
classified structure `{cascade-delete: {principal_key.principal}, refuse-guarded: {keep.keeper},
dangle-tolerated: {audit.actor_principal}}` so a new link must be CLASSIFIED (not silently absorbed into
a flat set) — but the flat-set + inline-rationale form the builder proposed satisfies the tripwire's
core job (it reds on a new link, forcing the decision); the classified form is the more-robust option,
right-sized to the lead's taste (3 links today).

**`audit.actor_agent` coverage (the lead's astute catch — "same policy, not pin-caught") → NOTE +
NAMED TRIGGER, do NOT extend the pin to all `record<agent>` links.**
- `actor_agent` follows the SAME dangle-tolerated policy (immutable history). It is MOOT today: agents
  are RETIRED, never hard-deleted (store-law §4 / the agent model), so a `record<agent>` link never
  dangles in practice.
- **Do NOT extend the exact-set tripwire to enumerate all `record<agent>` links.** Unlike
  `record<principal>` (rare — 3 links), `record<agent>` is COMMON (the comms subsystem: `message.sender`,
  the `to`/`briefed` edge endpoints, …). An exact-set `record<agent>` pin would red on ALL of them,
  forcing a cascade-disposition pass over the comms subsystem — scope-expansion far beyond w4/61a.
- **Instead, guard the LOAD-BEARING ASSUMPTION, not the enumeration:** the moot-ness rests entirely on
  *"agents are never hard-deleted."* Document `actor_agent = dangle-tolerated (moot: agents
  retired-not-deleted)` inline beside `actor_principal`, and carry a **NAMED RE-OPEN TRIGGER: the day an
  agent HARD-DELETE path is introduced, EVERY `record<agent>` link (audit.actor_agent + the comms links)
  needs a cascade-disposition pass.** Optionally a cheap assumption-guard pin (reds if a hard-DELETE on
  the `agent` table / a hard-delete agent-store method appears) — recommended if cheap, else the
  documented trigger suffices (right-sized: agent-hard-delete is on no roadmap). This closes the blind
  spot at the RIGHT granularity (the assumption) without dragging the comms subsystem into w4. ⚠ The
  #402 lesson (*"moot-today shipped a bug"* — keep.keeper was "handled" until it wasn't) is why leaving
  it wholly unguarded is wrong; a documented disposition + a named trigger is the proportionate guard.

**⚠ RIDER (surfaced per scope law; RECOMMENDED, non-blocking — a gap in the built row AND in my own
Fork G field set): DENORMALIZE the human actor identity.** The built `_AUDIT_FIELD_SPECS` carries actor
as record LINKS only. Dangle-tolerated means the row RETAINS the actor RecordID (`principal:xyz`) after
deletion (store-law §4 — the link value persists; deref → None), so *"who, by id"* survives (the
builder's/lead's stated rationale — correct as far as it goes). **BUT the HUMAN identity (email / agent
name) is LOST when the principal/agent row is deleted — exactly the case §9 audit matters MOST: a
deleted / offboarded / compromised admin.** *"`principal:01J…xyz` did this"* is far weaker in an
incident report than *"alice@corp did this,"* and the human→id mapping is gone with the row. The
textbook audit-log pattern captures identity-AT-WRITE as a VALUE precisely because actors get
deleted/renamed. **RECOMMEND adding `actor_email` (+ `actor_agent_name`) as denormalized value columns
stamped at the audit write** — the PDP already resolves the actor to stamp the row, so capturing the
email is one more field, and it makes the audit trail a self-contained immutable snapshot (the whole
point of §9). This does NOT block the cascade ruling (dangle-tolerated is sound either way — the id
survives); it is a design enhancement the lead/operator sizes. **My lean: DO it** — cheap, and §9's
forensic purpose wants the human identity, not a pseudonymous id. (This corrects my own Fork G field
set, which specified links without a denormalized identity — the cascade question surfaced the gap.)

**Escalation:** none — a cascade-disposition ruling within the audit/authz model, coherent with #402;
the denormalization is a surfaced recommendation, not a MAJOR pivot. **Builder unblock:** the pin's
expected-set gains `audit.actor_principal` (dangle-tolerated, annotated); `actor_agent` noted +
triggered; the two authorized test edits (this pin + the retry-seam roster) proceed. The denormalization
is a separate small field-set decision for the lead to rule in/near w4.

---

### FYI acknowledgements (2026-08-23) — no objection to two lead ratifications

- **`#6020` (Fork J standalone-slice property):** NO objection — the contract author's DERIVED property
  (*a slice is legitimately standalone iff CALLED BY some `generate_*_ddl` entry point*) is CORRECT and
  implements my Fork-J rider + INSTRUMENT-0 over my prose's letter. My Fork-J §(b) literal hand-list
  (*"generate_manifest_ddl/generate_memory_ddl/…"*) WAS the reach-law antipattern my own rider forbade —
  this is the FOURTH hand-list of mine this packet corrected to a derivation (set_status prose;
  transitive_blockers site; the translate-line guard; now the standalone-slice list). The pattern is
  clear and worth stating plainly: **my prose reaches for illustrative hand-lists; the property-derived
  instrument beats them every time — derive, never enumerate, including in a ruling doc.** The adversary
  P1c grading the derivation's faithfulness is the right check.
- **`#6027` (Fork G agent-not-folded correction):** NO objection — correct. `agent` is defined by the
  comms subsystem's own `ensure_ready`, not `generate_ddl`; my *"references defined earlier"*
  justification held for `principal` but not `agent`. The fold-after-`member_of` conclusion still stands
  because a `record<agent>` FIELD needs no pre-existing target table at definition time (store-ref §2 —
  `record<>` links don't validate existence), which the build proved live. No design change; only my
  justification was imprecise, now corrected.
