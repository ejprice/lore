# Packet 60 — Keep substrate: design-fork rulings

**Author:** design-sidecar-60 (Fable), 2026-08-22, working tree on branch
`feat/surreal-unification`.
**Nature:** design-authority rulings for packet 60 (the Keep substrate), delegated by `lead-60`
(operator-granted: all packet-60 forks route here; only a MAJOR scope/design pivot escalates to
the operator). The lead implements; this doc decides the model.
**Inputs read:** `docs/design/2026-08-21-lore-authorization-model.md` (§2.1, §4, §4.4, §5, §6, §7,
§10); `docs/reference/surrealdb-31-capabilities.md` (§1.1, §1.4, §1.8, §2, §4); the shipped 48/49
build in `loremaster/loremaster/store/surreal_schema.py` (`_PRINCIPAL_FIELD_SPECS`,
`_PRINCIPAL_KEY_FIELD_SPECS`, `_principal_statements`, `_principal_key_statements`,
`_define_relation_table`, `generate_ddl` fold at the `_principal_statements()` line, and the
`lore-adm` argparse CLI in `loremaster.principals:main`); `docs/plans/v2/INDEX.md` rows 60–65.

**Scope reminder (from the INDEX row + design §4.4):** packet 60 is SUBSTRATE ONLY — the `keep`
table, the `member_of{rank}` household edge, keeper-ownership, and the `lore-adm` verbs
(create-keep, add/remove household, set-rank). It is COMMIT-ONLY (deploys with 39 at packet 65's
joint cutover). The PDP (`authorize`/`authorize_filter`) is packet 61; agent-identity binding is
62; governed-row `owner`+`scope` retrofit is 63/64. This doc rules only the 60 substrate and marks
every boundary a contract could over-reach.

**Greenfield fact that governs several rulings:** there is NO existing `keep`/`member_of`
scaffolding in the tree (grepped). So the `keep` and `member_of` tables are BRAND-NEW EMPTY tables
— store-law §1.4's *"a new field on a POPULATED table must be `option<>`"* does **NOT** apply at
birth (exactly as `_PRINCIPAL_KEY_FIELD_SPECS` notes for `principal_key.principal`). Required
(non-`option`) fields are legal on these tables. This is different from the 63/64 retrofit, which
adds columns to POPULATED tables and there §1.4 bites hard.

---

## Ruling summary (one line per fork)

- **A — keeper storage:** an indexed `keep.keeper: record<principal>` FIELD LINK; **NO `keeps`
  edge; NOT both.** Household membership is the separate `member_of` edge. ⚠ Diverges from design
  §2.1's literal edge notation — see the flag in §A.
- **B — `keep` fields:** `keeper` (record link, indexed) · `name` (`option<string>`, non-empty
  ASSERT) · `created_at` (`datetime DEFAULT time::now()`) · `type` (closed domain
  {project,team,session,dm}, call-time-derived, NO default). Record id = `ulid()`. No separate
  `created_by`; no `name` uniqueness — both deferred with triggers.
- **C — `member_of.rank`:** `string`, `DEFAULT 'contributor'`, ASSERT closed domain derived
  call-time from `_KEEP_RANKS = ('contributor',)` (flat today). Designed to WIDEN (safe); NARROWING
  is the poison direction (forbidden without migration + re-open trigger).
- **D — keeper ↔ household:** create-keep AUTO-ADDS the keeper to the household as a `member_of`
  edge at the flat default rank (`'contributor'`). Keeper authority (manage/delete) rides the
  `keeper` FIELD, not rank, today.
- **E — DM auto-creation:** CONFIRMED **out of packet 60.** 60 supplies the substrate + verbs to
  manually create a `type=dm` keep and populate its 2 members; auto-creation-on-`send` is packet
  **63** (comms retrofit). The 60 contract must not build the auto-wire.
- **F — edge constraints:** `member_of` → ENFORCED + UNIQUE(in,out). No `keeps` edge to constrain.
  "At most one keeper per keep" is structural (single-valued field), needs no UNIQUE(out).

---

## Fork A — keeper: FIELD LINK, not a `keeps` edge, not both

**RULING:** Realize the design's `principal —keeps→ keep` ownership relationship as an **indexed
`keep.keeper: record<principal>` field link** on the `keep` table. Do **not** mint a `keeps`
RELATION edge, and do **not** carry both (A3 rejected). Keepership and household membership are
**DISTINCT** (Fork A's sub-question): keepership is the single-valued `keeper` field; household
membership is the many-to-many `member_of` edge (Fork D wires the keeper into the household too,
but as a separate fact — see §D).

**Rationale:**
1. **The house idiom is a FIELD LINK for exactly-one ownership.** Packet 49 models "a
   `principal_key` owned by exactly one principal" as `principal_key.principal:
   record<principal>` — a field, not an edge (`_PRINCIPAL_KEY_FIELD_SPECS` +
   `_principal_key_statements`, indexed via the `(principal, name)` UNIQUE composite). A keep owned
   by exactly one keeper is the identical cardinality. The INDEX row for 60 mandates "Mirrors the
   48/49 principal/principal_key build" — mirroring means the field-link idiom.
2. **Store-law §4's own FIELD-vs-EDGE-HOP decision rule, verbatim:** *"a scalar attribute … filtered
   through a hop is un-indexable by construction — keep scalars as indexed fields and spend edges on
   real relationships."* The PDP's keeper questions ("is P the keeper of keep X", "which keeps does
   P keep") are filter-by-attribute, single-valued, degree-1 — an indexed `record<principal>` field
   answers them as an IndexScan / direct read, while an edge forces a `GraphEdgeScan` that store-law
   §4 proves "NEVER uses a secondary index." Household membership, by contrast, IS a real
   many-to-many relationship that the packet-61 PDP resolves by TRAVERSAL to build `$my_keeps`
   (design §6) — that earns an edge. So: field for keepership, edge for membership.
3. **A3 (both) is a dual-write hazard.** An edge + a redundant field are two copies of one fact
   ("P keeps X") that can DIVERGE; a set-keeper action must update both in lockstep. That violates
   ONE-IMPLEMENTATION/DRY and store-law §4's "don't spend an edge on a scalar." One source of truth.
4. **"Exactly one keeper" is free with a single-valued field** (a `record<principal>` cannot hold
   two values); an edge would need a `UNIQUE(out)` index to enforce the same invariant.
5. **The graph-as-source-of-truth framing (design §2.1) is preserved.** A `record<principal>` link
   IS graph data in SurrealDB — a first-class link, `FETCH`-able and traversable — merely stored as
   a field rather than a RELATION table. The design's `resource —owned_by→ (principal|agent)`
   ownership relation is ALREADY realized as a field/link in the shipped substrate (48/49 owners,
   and the §7 migration maps free-form `created_by` strings to `owner` REFERENCES, not edges).
   Keepership is the keep's `owned_by`; same shape, same storage.

**RIDER (and pin it like this):**
- **Index:** add a **non-unique** index on `keep.keeper` (a record-link column is indexable) so
  `SELECT id FROM keep WHERE keeper = $p` ("keeps kept by P") is an IndexScan, not a TableScan —
  the shape the 61 PDP and any admin listing will run. NOT unique: a principal keeps many keeps.
- **Mutation-prove the keeper index actually fires:** pin an `EXPLAIN` (or the store-law §2
  IndexScan-vs-TableScan discriminator) that `keeper = $p` uses the index — the store-law §4
  "traversal never indexes" warning is the trap this avoids; prove the field escapes it.
- **Contract pin:** exactly one keeper per keep — a `keep` row's `keeper` is a single
  `record<principal>`, and there is no code path that appends a second. (No `keeps` edge exists to
  accidentally double.)

**⚠ FLAG — divergence from the design doc's literal wording (surfaced, not silently resolved):**
Design §2.1 and §4.4 write keepership as an EDGE (`principal —keeps→ keep`). This ruling stores it
as a FIELD LINK. The SEMANTICS are unchanged (one keeper per keep; keeper manages the household;
keeper is graph-linked to the keep). Only the storage shape differs, and it differs toward the
shipped house idiom (48/49), toward store-law §4's explicit rule, and toward a cheaper 61 PDP. I
judge this WITHIN my delegated authority — it is a substrate modeling decision, not a design pivot,
and it is precisely the fork the lead assigned me. But because it overrides the design doc's
literal notation, it is called out here loudly: **if the operator intended `keeps` as a hard
traversal-edge requirement (e.g. a planned future need to walk `keeps` as a graph edge that a field
link cannot serve), countermand this ruling.** I found no such need in §5/§6 (the PDP resolves
`$my_keeps` via `member_of`, never `keeps`).

---

## Fork B — the `keep` table field set

**RULING — the full `(name, type_expr, constraint)` triple list, in the 48/49 house format:**

| field | type_expr | constraint | notes |
|---|---|---|---|
| `keeper` | `record<{PRINCIPAL_TABLE}>` | `""` | owner link (§A). Required at birth (greenfield table, §1.4 N/A). Indexed non-unique. |
| `name` | `option<string>` | `_NON_EMPTY_STRING_ASSERT` | optional human label. `option<>` skips the ASSERT on NONE, FIRES on a present empty string — the `principal.subject` idiom exactly. |
| `created_at` | `datetime` | `DEFAULT time::now()` | engine-stamped; store OMITS it on write (the `finding`/`brief`/`principal.created_at` idiom). |

Plus `type`, emitted at **call time** (the `_principal_statements` mutation-provable idiom, NOT a
frozen import constant), derived from a `_KEEP_TYPES` tuple:

| field | type_expr | constraint |
|---|---|---|
| `type` | `_CHUNK_STRING_TYPE` | `f"ASSERT $value IN [{types_allowed}]"` — **NO `DEFAULT`** |

with `_KEEP_TYPES = ('project', 'team', 'session', 'dm')` and
`types_allowed = ", ".join(f"'{t}'" for t in _KEEP_TYPES)`.

**Sub-question rulings + rationale:**

- **Human-readable name? — YES, optional, non-empty-if-present, NOT required at the store, NOT
  unique.** A `project`/`team`/`session` keep benefits from a label; a `dm` keep is identified by
  its two members and carries no meaningful name. A per-`type` conditional requirement ("name
  required unless dm") is not cleanly expressible as a per-field SurrealQL ASSERT, so enforce it at
  the APP layer: `lore-adm create-keep` REQUIRES `--name` for `project`/`team`, allows it for
  `session`, and forbids/ignores it for `dm`. The store just guarantees `name` is optional and
  non-empty-if-set. **No uniqueness** on `name` in packet 60 — keeps are addressed by record id,
  not by name; two keepers may reuse a label. (A `UNIQUE(keeper, name)` composite is a free
  `IF NOT EXISTS` add later if collisions bite — but note `name` is `option<>`, so store-law §1.8
  applies: multiple NONE coexist, which is exactly right for `dm` keeps. **Re-open trigger:** first
  report of confusing duplicate keep names under one keeper.)

- **`type` — closed domain, NO default.** `type` is the essential discriminator; every create must
  choose it (create-keep supplies it, server-validated). Unlike `principal.status`/`role`
  (which have a sensible least-privilege default), a keep has no defensible default type — a silent
  default would mislabel keeps. Derive the ASSERT at call time from `_KEEP_TYPES` so a tuple
  mutation moves the emitted ASSERT (mutation-provable, per the `_principal_statements` note at
  `surreal_schema.py`). **Rider:** the domain widens safely (a new collaboration flavor is a new
  `type`, per design §4.4 — never a new scope tier); NARROWING it would poison existing rows
  (§1.4) — same trigger discipline as `rank` (§C).

- **Record-id form — `ulid()` at CREATE (random, creation-ordered), NOT a deterministic key, NOT a
  counter mint.** A keep has no natural key (name is optional/non-unique) and needs no human-facing
  gapless handle, so the `finding`/`brief` counter-mint is wrong here, and there is no key to derive
  a `uuid5` from (create-keep is NOT idempotent — creating "a keep" twice makes two distinct
  spaces, unlike `register`). `ulid()` mirrors the `message` table (sortable by creation, and
  `str(RecordID)` round-trips per store-law §2 so the id stringifies cleanly to the `keep:<id>`
  scope value that governed rows will carry in 63/64). Engine-assigned random is an acceptable
  fallback if the store prefers not to compute the id; `ulid()` is the recommendation for
  creation-order sortability and house consistency.

- **`created_by` provenance? — NOT in packet 60.** At creation the `keeper` IS the creator, and 60
  has no keeper-reassignment verb (admin `set_owner` is 61+), so `keeper` carries creation
  provenance with zero redundancy. **Rider / forward-compat flag:** if packet 61's admin
  `set_owner` reassigns a keeper and provenance-of-creation must survive, THAT packet adds a
  `created_by: option<record<principal>>` — and note it will then be a NEW field on a POPULATED
  table, so it MUST be `option<>` (§1.4). Do not add it in 60.

- **`type` index? — deferred.** The 61 PDP resolves visibility via `member_of`, not by `type`;
  only admin listing ("all project keeps") would want a `type` index, and that is a free
  `IF NOT EXISTS` add when a listing verb needs it. Packet 60 ships only the `keeper` index (§A).

**Table + emission:** `keep` is a plain SCHEMAFULL table (`_define_table` → `IF NOT EXISTS`
SCHEMAFULL — undeclared top-level keys RAISE, store-law §1.7). Fields via `_define_field`
(→ `DEFINE FIELD OVERWRITE`, §1.1). This mirrors `_principal_statements` line-for-line.

---

## Fork C — `member_of.rank`: closed-domain-flat-today, widen-safe

**RULING:** `rank` on the `member_of` edge is:

| field | type_expr | constraint |
|---|---|---|
| `rank` | `_CHUNK_STRING_TYPE` | `f"DEFAULT '{_KEEP_RANK_CONTRIBUTOR}' ASSERT $value IN [{ranks_allowed}]"` |

emitted at **call time** from `_KEEP_RANKS = ('contributor',)` (the `_principal_statements`
mutation-provable idiom), with `_KEEP_RANK_CONTRIBUTOR = 'contributor'` and
`ranks_allowed = ", ".join(f"'{r}'" for r in _KEEP_RANKS)`. **Closed domain, one value today
(`'contributor'`), default `'contributor'`.**

**Rationale:**
- **Closed-and-asserted beats open free-form here** — the house asserts every enum-like column
  (`principal.role`/`status`, `agent.status`, `briefed.via`) as a call-time-derived closed domain,
  precisely so a value the code branches on cannot silently be garbage. `rank` is such a column
  (the future PDP branches on it). An unasserted string would be the odd one out and would let a
  typo'd rank reach the PDP.
- **Flat = a one-value domain today.** Design §4.4: *"Today `rank` is FLAT — every member is a plain
  collaborator."* A single-value `{contributor}` ASSERT MAKES that flatness a store invariant, and
  it is mutation-provable via the tuple.
- **Why `'contributor'` and not `'member'`:** the per-Keep rank vocabulary in §4.4
  ({viewer, contributor, steward, keeper}) is deliberately DISTINCT from the GLOBAL
  `principal.role` vocabulary ({member, admin}). Reusing `'member'` for the per-keep rank would
  collide two different concepts on one word. `'contributor'` is §4.4's name for the plain
  collaborator who can write — which is exactly the 3-way rule's "any household member may write."
- **Poison direction (store-law §1.4):** the FUTURE seam GROWS the domain (add
  viewer/steward/keeper). Growth that RETAINS `'contributor'` is a pure WIDENING — store-law §1.4:
  *"Widen an ASSERT → rows intact, still writable."* SAFE. The dangerous direction is NARROWING or
  REMOVING `'contributor'`, which write-poisons every existing `member_of` row (an UPDATE of any
  column re-validates the whole record).

**RIDER (and pin it like this):**
- **Pin the widening-safe property:** a `TestSchemaMigrationAgainstAnExistingStore`-style leg —
  write a `member_of` row at `rank='contributor'` under the one-value DDL, then apply a WIDENED
  `_KEEP_RANKS` DDL (e.g. `('contributor','steward')`), and assert the existing row SURVIVES and is
  still writable, AND the new value is now accepted. This proves growth is non-poisoning on a DIRTY
  store (the #107/#131 blind-spot class — a virgin-DB fixture cannot see it).
- **Pin the mutation-provable derivation:** monkeypatch `_KEEP_RANKS` and assert the emitted ASSERT
  moves (the `_principal_statements` idiom — a frozen import constant would make this un-provable).
- **NAMED RE-OPEN TRIGGER (per the deferral law):** the day the per-Keep rank seam differentiates
  (§4.4 — viewer/contributor/steward/keeper land), whoever widens `_KEEP_RANKS` MUST keep
  `'contributor'` in the set OR ship a row migration; NARROWING is a data migration, never a bare
  tuple edit.

---

## Fork D — keeper ↔ household: auto-add the keeper, at the flat rank

**RULING:** `create-keep` mints TWO facts atomically: (1) `keep.keeper = P` (management authority),
and (2) a `member_of` edge `P → keep` at the flat default rank (`'contributor'`) — i.e. the keeper
IS auto-added to the household. Keeper authority (manage the roster, set-rank, delete the keep)
rides the `keeper` FIELD today; the keeper's household membership rides the `member_of` edge.

**Rationale:**
- **The 3-way write rule requires it.** Design §4: a `keep`-scoped row is writable by "any member of
  the Keep's household." For the keeper to WRITE rows in their OWN keep (the common case — a keeper
  is the most active member), the keeper MUST be a household member. Auto-adding closes that gap at
  create time so the keeper is never locked out of their own keep.
- **These are two DIFFERENT facts about P, not a dual-write of one fact** (so §A's dual-write
  objection does not apply). `keep.keeper` answers "who manages/deletes this keep"; the `member_of`
  edge answers "who may write keep rows / whose `$my_keeps` includes this keep." Reading one never
  substitutes for reading the other. No single value is copied twice.
- **At the FLAT rank, per §C.** Today rank is flat, so the keeper's edge is `rank='contributor'`
  like every other member; the keeper's ELEVATED power comes from the `keeper` field, not from
  rank. This is the clean today/tomorrow seam: TODAY keeper-power = the field; TOMORROW (§4.4 /
  §10-P) the seam MAY promote the keeper's edge to `rank='keeper'` and read power from rank — a 61+
  concern, explicitly out of 60.

**RIDER (and pin it like this):**
- **Atomicity pin:** create-keep writes the `keep` row + the keeper's `member_of` edge in ONE
  `execute_transaction` (store-law §3 — never a multi-statement `.query()`; a later-statement
  failure there is a silent partial apply). Pin that a create-keep leaves EITHER both (keep +
  keeper-membership) OR neither — no keep with an un-householded keeper.
- **Contract pin:** immediately after `create-keep`, the keeper appears in the keep's household
  (`member_of` traversal returns the keeper) at `rank='contributor'`, AND `keep.keeper` equals the
  creator. Both, in one test, so a build that writes the field but forgets the edge (locking the
  keeper out) goes RED.
- **`ENFORCED` ordering:** the `keep` row must exist BEFORE the `member_of` edge is RELATEd (the
  edge is ENFORCED — §F — so the keep endpoint must exist), which the single-transaction ordering
  guarantees.

---

## Fork E — DM auto-creation is NOT packet 60 (boundary confirmed)

**RULING:** CONFIRMED — auto-creation-of-a-DM-Keep-on-`send` is **out of packet 60.** Packet 60
provides (a) the substrate to hold a `type='dm'` keep, and (b) the `lore-adm` verbs to MANUALLY
create a `dm` keep and populate its 2-member household (`create-keep --type dm` +
`add-household` twice). The AUTOMATIC wire — `lore_comms send` detecting a 2-party thread and
minting a `dm` keep on the fly — lives in packet **63** (governed-tool retrofit: comms + memory),
per design §4/§10-L and the INDEX row 63 ("Governed-tool retrofit: comms + memory").

**Rationale / boundary:** the INDEX confirms 63 = comms retrofit; §10-L's "auto-created 2-member
Keep" is a COMMS behavior that presupposes both the Keep substrate (60) AND the PDP + owner/scope
retrofit (61/63). Building the auto-wire in 60 would (a) reach into `lore_comms` (out of 60's
writable surface), and (b) require the `owner`/`scope` columns that 63 adds. **The 60 contract must
NOT build any `send`-triggered keep creation, any comms coupling, or a "dm keeps are special"
auto-path.** A `dm` keep in 60 is just a keep whose `type` is `'dm'` and whose household the admin
populated with exactly two members — the "exactly two" is a COMMS-layer invariant (63), not a store
ASSERT in 60 (the store cannot cheaply count edge endpoints per keep, and a `session`/`project`
keep has no such cap). **Rider:** the 60 contract's `dm` coverage is limited to "create-keep
`--type dm` produces a keep with `type='dm'`" and "add-household works on it" — nothing about
2-member enforcement or send-time creation. Flag any contract pin that asserts a member-count cap
as OVER-REACH into 63.

---

## Fork F — edge constraints: ENFORCED + UNIQUE(in,out) on `member_of`

**RULING:**
- **`member_of`** (`principal —member_of→ keep`; IN=`principal`, OUT=`keep`): **ENFORCED +
  UNIQUE(in, out).** Emit via `_define_relation_table(MEMBER_OF_RELATION, PRINCIPAL_TABLE,
  KEEP_TABLE, enforced=True)` (→ `DEFINE TABLE OVERWRITE member_of TYPE RELATION IN principal OUT
  keep ENFORCED SCHEMAFULL`) plus `_unique_index(MEMBER_OF_RELATION, "member_of_in_out", ("in",
  "out"))`.
- **`keeps` edge:** NONE — keepership is the `keep.keeper` field (§A), so there is no `keeps` edge
  to constrain.
- **May a keep have >1 keeper? — NO, and it is STRUCTURAL.** A single-valued `keep.keeper:
  record<principal>` field cannot hold two keepers, so "exactly one keeper" needs no `UNIQUE(out)`
  edge index (there is no edge). This satisfies the design's "exactly one keeper" implication for
  free.

**Rationale (all store-law §4):**
- **ENFORCED** validates that BOTH `member_of` endpoints (the principal AND the keep) reference
  EXISTING records — closing the dangling-edge hazard (#105) AND the `INSERT RELATION` door no
  app-level check can reach. Store-law §4 "Shape to ship" is verbatim
  `DEFINE TABLE OVERWRITE <edge> TYPE RELATION IN <a> OUT <b> ENFORCED SCHEMAFULL`, which
  `_define_relation_table(enforced=True)` already emits. ENFORCED needs `OVERWRITE` (the
  `IF NOT EXISTS` flip is a silent no-op on a relation table, §1.1) — `_define_relation_table`
  emits `OVERWRITE`, correct.
- **UNIQUE(in, out)** makes a double-add of the same (principal, keep) pair a loud ERR instead of a
  second edge — the `briefed`/`to` precedent (`surreal_schema.py`), legal+safe on our floor
  (≥3.1.0; store-law §4 SETTLED with the vendor confirming both cascade-fix legs).

**RIDER (and pin it like this):**
- **Keep the app-level existence check as the ergonomic layer** (store-law §4: neither is
  redundant). ENFORCED reports ONE bad endpoint per attempt, as untyped prose, only AFTER the write
  aborts the txn — so `add-household` should app-check that the principal AND the keep exist and
  name a clear error BEFORE the RELATE (the vendor-recommended belt-and-braces). Do NOT parse the
  ENFORCED error string to recover ids (a literal-keyed instrument, forbidden).
- **`add-household` must be idempotent / dedupe-before-RELATE** — re-adding an existing member hits
  the UNIQUE(in,out) backstop as a loud ERR (store-law §4: "a fan-out that may repeat a recipient
  must dedupe before the RELATE loop, or catch it — the index is a correctness backstop, not a
  de-duplicator"). Rule: `add-household` on an already-present member is a benign no-op (check-first
  or catch-the-duplicate), NOT an error to the operator.
- **`remove-household` DELETEs the edge** (endpoints untouched — the keep and principal survive; the
  edge self-cleans on endpoint delete anyway, store-law §4). **Guard:** removing the KEEPER from the
  household is a footgun (it would lock the keeper out of writing their own keep, undoing §D) —
  `remove-household` should REFUSE to remove the current `keep.keeper` (or require an explicit
  keeper-reassign first). Pin this refusal. **Re-open trigger:** if 61 introduces keeper-reassign,
  revisit whether keeper removal is then legal.
- **`set-rank` UPDATEs the edge's `rank` field** — legal (rank is a normal edge FIELD, not an
  endpoint; store-law §4's "UPDATE of in/out is a silent no-op" applies only to ENDPOINTS, not to
  edge data fields). Today, with a one-value domain (§C), `set-rank` can only set `'contributor'` —
  so the verb is a SEAM that becomes meaningful when the domain widens. **Ruling:** ship `set-rank`
  in 60 (it is named in the packet scope) but note it is exercised trivially today (the only legal
  value is the default); its real test lands with the rank widening. Do NOT gate 60 on a
  multi-rank `set-rank` behavior that the domain does not yet permit.

---

## Emission plan (mirror 48/49 — for the contract/build phase)

Following `_principal_statements` / `_principal_key_statements` / `generate_principal_ddl` exactly:

1. **Constants** (module-level, `surreal_schema.py`): `KEEP_TABLE = "keep"`,
   `MEMBER_OF_RELATION = "member_of"`, `_KEEP_TYPES`, `_KEEP_RANKS` + the rank/type value
   constants, `_KEEP_FIELD_SPECS` (the non-domain triples), `_MEMBER_OF_FIELD_SPECS` (the `rank`
   triple is derived call-time, but a `since datetime DEFAULT time::now()` provenance stamp on the
   edge — mirroring `briefed.at` — is RECOMMENDED and belongs in the static specs).
2. **`_keep_statements()`** — `[_define_table(KEEP_TABLE)]` + `_define_field` per
   `_KEEP_FIELD_SPECS` + the call-time-derived `type` field + the non-unique `keeper` index.
3. **`_member_of_statements()`** — `[_define_relation_table(MEMBER_OF_RELATION, PRINCIPAL_TABLE,
   KEEP_TABLE, enforced=True)]` + `_define_field` for `since` + the call-time-derived `rank` field
   + `_unique_index(..., ("in", "out"))`. (`in`/`out` are auto-defined by TYPE RELATION — never
   hand-declared, per the `briefed`/`to` note.)
4. **Fold into `generate_ddl`** immediately AFTER `_principal_key_statements()` (the `keep.keeper`
   and `member_of` endpoints reference `principal` and `keep`, so `principal` must be defined
   first, and `keep` before `member_of` — the `briefed → agent` link-target-first precedent).
5. **`generate_keep_ddl()`** — a schema SLICE for a future `KeepStore.ensure_ready()` (mirrors
   `generate_principal_ddl`), so a dedicated store can apply just the keep+member_of tables on its
   own connection. (Whether packet 60 wires a `KeepStore` into `build_app_context` or only folds
   into `generate_ddl` is the 48/49 "Variant A" question — recommend folding into `generate_ddl`
   now so the primary `write_store.ensure_ready()` creates the tables on ship, plus the slice for
   the store's own use, exactly as 48/49 did.)
6. **`lore-adm` verbs** — mirror the `loremaster.principals:main` argparse idiom
   (`create` / `create-key` / `revoke-key` subcommands). Whether the keep verbs extend
   `principals.py`'s parser or live in a new `keeps.py` CLI module is a CONTRACT-phase placement
   decision (recommend a new `loremaster/keeps.py` with its own `KeepStore` + a `lore-adm keep …`
   subcommand group, or a second console entry — the lead/contract author rules the module layout;
   it does not change any store-model ruling above). The verbs: `create-keep --type … [--name …]
   --keeper <email>`, `add-household --keep <id> --member <email>`, `remove-household --keep <id>
   --member <email>`, `set-rank --keep <id> --member <email> --rank <rank>`. The admin CLI stays
   CREDS-FREE (resolve only the surreal block, per the packet-49 ruling — memory
   `Packet 49 CONTRACT-AMBIGUITY RULINGS` item 6).

---

## Store-law compliance checklist (for the contract-adversary + cold audit)

- **DDL clauses:** `keep` table → `IF NOT EXISTS` SCHEMAFULL (plain); fields → `OVERWRITE`;
  `keeper` index → `IF NOT EXISTS`; `member_of` relation table → `OVERWRITE … ENFORCED`;
  `member_of` UNIQUE(in,out) index → `IF NOT EXISTS`. (§1.1 decision table.)
- **Greenfield:** required non-`option` fields (`keeper`, `type`, `rank`) are legal — the tables are
  empty at birth (§1.4 applies only to POPULATED tables; contrast 63/64).
- **`name` `option<>` + non-empty ASSERT:** multiple NONE coexist (all `dm` keeps) is CORRECT and
  intended (§1.8); the ASSERT fires only on a present empty string.
- **Call-time-derived domains** (`type`, `rank`): mutation-provable (§`_principal_statements`).
- **create-keep atomicity:** one `execute_transaction`, never multi-statement `.query()` (§3).
- **ENFORCED needs OVERWRITE** (§1.1 relation row) — `_define_relation_table` emits it.
- **Dirty-store migration pin** for the rank widening (§C rider) — the ONLY §1.4-relevant hazard in
  60, and it is FUTURE (the widening), so pin it now as a widening-safe leg.

---

## Escalation status

**Nothing escalated to the operator.** All six forks are ruled within delegated authority. The ONE
item surfaced loudly is the Fork-A storage divergence from design §2.1's literal edge notation
(§A flag) — ruled as a field link with a countermand condition stated, not a silent narrowing. If
the operator reads §2.1's `keeps` as a hard graph-edge requirement, that single ruling flips; every
other ruling is independent of it.

---

## Follow-up ruling FR-1 (2026-08-22) — packet-49 stale-prose fold + the recurrence invariant

Ruling on `lead-60`'s scope fork (`lore_comms` #5152 · finding **#398** · cold audit
`coldaudit-60-w1` = **NO-GO-prose-only**). Ground-truthed both cited sites this session:
`surreal_schema.py:133-136` ("the field specs / emitters below are RED stubs; the builder greens
them") and `:1855-1868` ("These emit NOTHING … NOT folded into generate_ddl. Do NOT 'fix' them")
both **factually contradict the committed code** — `_principal_key_statements` is fully implemented
(real table + fields + two UNIQUE indexes) and IS folded into `generate_ddl` at the
`_principal_key_statements()` line. Confirmed same-class defect as the 5 in-flight packet-60 comments.

**Part 1 — the 5 packet-60 wave-1 stale comments (keeps.py, surreal_schema.py ~1726/~1959,
_enforced_relations_scaffold.py): not a fork.** IN scope, must-fix-before-commit. The fixer retires
them; they ride the packet-60 wave-1 commit. (Confirming, not ruling — the cold audit already put
them in scope.)

**Part 2 — SCOPE FORK: fold the 2 packet-49 comment fixes? → RULING (a): FOLD IN, as a SEPARATE
one-concern commit, durably logged.**
- The fixer is already editing `surreal_schema.py`; it also retires the packet-49 stale-STUB
  comment blocks (`:133-136`, `:1855-1868`) in the same pass.
- **BUT commit them SEPARATELY** — a distinct one-concern commit (e.g. `docs(49): retire stale
  RED-STUB comments on the greened principal_key slice`), NOT bundled into the packet-60 wave-1
  commit (the repo's one-concern-per-commit law). The fixer edits both in one file pass; the lead
  stages them into two commits.
- **The wave close-out Log line AND that commit's body cite #398**, so the packet-49 scope-crossing
  is DURABLY VISIBLE to the (offline) operator — not silently absorbed.
- **Rationale:** don't-kick-the-can (a confirmed defect a fixer is one edit away from, punted =
  a fresh context must rediscover it) · same file, same class, nearly free · **comment-only, zero
  functional/gate/served-surface risk** · pre-production repo + operator offline · #398 already
  filed so nothing is lost on either branch. This is neither a silent scope absorption (it is
  logged + #398) nor a block on an offline operator (Fork-A precedent: surface durably, don't
  escalate an absent operator).
- **Riders:** (1) separate commit + Log/#398 citation, as above. (2) The fixer **ground-truths each
  of the 2 packet-49 comments against the live `_principal_key_statements`/`PRINCIPAL_KEY_TABLE`
  code before editing** — reframe to a historical-origin note ("introduced as a RED stub by
  contract-49-1, greened by builder-49") OR a plain description of the real slice (per #398's FIX
  SHAPE), NOT a blind deletion of context. (3) Resolve #398's packet-49 instance on that commit.

**Part 3 — #398's recurrence-prevention invariant (the AST/text scan): → RULING: BUILD IT, but as a
PROPERLY-CONTRACTED instrument — never a rushed same-wave text-scan.**
- **It is mandatory, not operator-discretionary and not indefinitely deferrable:** standing law —
  *"every audit-caught defect class becomes a repo-local invariant test; a fix without an invariant
  is half a fix, and the class WILL recur."* This class has now recurred across TWO packets (49 and
  60), and it is STRUCTURAL to the TDD flow (every contract writes RED-STUB comments a builder
  greens), so recurrence is the default without a guard.
- **⚠ CRITICAL DESIGN RIDER — the reach-attack law (this is the load-bearing part):** a scan keyed
  on the FORBIDDEN literals (`"RED STUB"` / `"emit []"` / `"emits NOTHING"`) is EXACTLY the
  *"enumerate the forbidden"* antipattern this repo has six receipts against — the next contract
  author writes `"placeholder — returns nothing yet"` and walks straight through it. So:
  - **Check a STRUCTURAL property, not a forbidden-literal match, wherever possible.** The
    load-bearing property is: *a schema-slice function that emits ≥1 statement (or is folded into
    `generate_ddl`) must not carry a comment/docstring ASSERTING it is empty / a stub / unfolded.*
    Where a literal set is unavoidable, **allowlist the safe** (a slice's doc describes what it
    emits) rather than blocklist the unbounded forbidden.
  - **Coverage-as-checked-variable (INSTRUMENT-0):** the set of schema-slice functions is DERIVED
    from a property (name shape / return type / `generate_ddl`-fold membership), NEVER a hand-list,
    and a test reddens when the derived set GROWS but the scan's observed set does not.
  - **Mutation-prove it:** reintroduce a stale "emits nothing" comment above a greened slice → the
    pin reddens; restore → green.
  - The `contract-adversary`'s P1c REACH ATTACK forces exactly these — so this invariant goes
    through a real contract→adversary→build→cold-audit cycle, not an inline hand-rolled scan.
- **Placement:** a dedicated CONTRACTED sub-task — riding the packet-60 track's tail (it caught the
  class) or a small standalone hygiene item; **the lead rules placement, I rule it MUST be
  contracted (not hand-rolled inline) and law-mandatory.** Per the deferral law it carries a NAMED
  OWNER + TRIGGER: if not built inside the packet-60 track, a ledgered task with #398 as origin and
  trigger = *"before the next TDD wave writes new RED-STUB comments"* (i.e. promptly — every wave
  does).

**Scope-authority note:** Part 2 (editing committed packet-49 code) and Part 3 (a cross-cutting
hygiene instrument) both reach slightly beyond the literal packet-60 Keep-substrate scope. I rule
them under my delegated packet-60 authority as scope-ADJACENT, confirmed-defect / law-mandated
hygiene, surfaced durably (this section + #398 + the Log) rather than escalated to the offline
operator — the same handling Fork-A's divergence got. Neither is a MAJOR scope/design pivot
(comment hygiene + a standing-law-mandated invariant), so neither meets my operator-escalation
trigger; both are durably flagged for a clean operator countermand on return.
