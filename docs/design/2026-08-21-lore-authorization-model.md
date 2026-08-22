# lore authorization model — ownership + scope + role, one in-process PDP over the graph

**Author:** design-sidecar-39-2 (Fable), 2026-08-21, working tree `9a10604` (branch
`feat/surreal-unification`).
**Nature:** foundational design DOC + recommendations. The operator RULES the open forks (§10);
the security-auditor and contract-adversary are named arbiters of the enforcement (§9, §11).
**Status:** design, not yet contracted. This is a NEW, cross-cutting design — almost certainly
its own packet — that fills the fine-grained authorization layer *packet 39's* coarse read/write
floor cannot express. Sequencing in §8.

**Operator rulings folded (this session, 2026-08-21):**
- **Architecture = "Version A, mirror Permit.io":** an in-process policy engine over lore's own
  SurrealDB graph as the single source of authorization truth. NOT a bought/hosted PDP service.
  (Verified prior art: Permit.io runs a Zanzibar/ReBAC engine on SurrealDB and does *not* rely on
  native store PERMISSIONS — `surrealdb.com/customer/permitio`.)
- **Scope model = the 5-tier intent, realized as Keeps** (§4). Scopes: `agent-private ·
  principal-private · keep:<id> · server`, where the 5 tiers' collaboration flavors are Keep
  **types** (`project`/`team`/`session`/`dm`). The collaboration container is a **Keep** (RULED —
  owner=**keeper**, members=**household**, per-Keep role=**rank**, a flat-now/differentiated-later
  seam). A DM is a 2-member Keep.
- **Write model = the 3-way rule** (§4, RULED): private=owner-only (isolation); `keep`=any household
  member (collaboration — claim a task, correct a memory, supersede a finding); `server`=owner+admin
  (broadcast). Hard-delete of a shared row = owner+admin. Members freely set the scope of rows they
  own (up or down). **`admin` = full, unrestricted superuser** reachable from any surface incl.
  hosted; the one carve-out is an **append-only, admin-exempt audit store** (§9).
- **Agent identity = whatever clears the security bar** — *"prevents spoofing and prompt
  injection, or the security auditor barks."* Determined below (§3) to be **server-bound
  short-lived (principal, agent) credentials + two companion invariants**; the auditor is the
  arbiter.
- **pycasbin = REJECTED for the core** (§2.4) — it cannot be the single brain for the read path,
  and confining it to where it *is* safe leaves it doing a trivial job while its real strengths
  sit in the layer we must keep single. Split-brain is the reason, which was the operator's own gate.

**Why this is foundational, not a packet-39 add-on:** lore's write surfaces — `lore_comms`,
memory, `lore_tasks`, `lore_findings` — are inherently multi-writer. A coarse read/write bit makes
them either useless (nobody can write) or unsafe (any writer reads everyone's data). The security
requirement the operator stated — *a user and their agents must not read another user's comms /
memory* — is **row-level isolation**, which no tool-level annotation can express. The three
examples the operator named (comms, memory, tasks) are three instances of ONE missing abstraction:
**every user-generated row has an OWNER and a SCOPE, and authorization is one function of
`(principal, agent, action, resource.owner, resource.scope)`.** Design it once.

---

## 1. The clean line: shared corpus vs owned coordination data

Not everything gets owner+scope. There are two populations, and the boundary is crisp:
- **The code/docs corpus (shared-read)** — `lore_search`, `lore_read`, `lore_get_symbol`,
  `lore_impact`, `lore_map`, `lore_dead_code`, `lore_diff`. This is project source lore indexes;
  reading it is the whole point of lore. It stays shared-read within a project (admission gates
  *whether* you reach the project at all; there is no per-row ACL on code).
- **User-generated coordination data (owner + scope)** — `lore_comms` (messages/channels),
  memory (notes), `lore_tasks` (tasks), `lore_findings` (findings). Each row is owned and scoped;
  reads are filtered, writes are gated. **This** is what the authorization model governs.

This line is itself a design decision to pin: a new tool is classified into one population or the
other at registration, and "which population" is a checked variable (no tool is silently neither).

---

## 2. Architecture — one in-process PDP over the graph (mirror Permit.io)

### 2.1 Single source of truth = the SurrealDB graph
lore already has a graph store. The Zanzibar "relationship tuple" *is* a SurrealDB `RELATE` edge.
So the authorization relationships live as graph data in the SAME store, SAME transactions, as the
data they govern — which is what eliminates the dual-write/consistency problem every external PDP
carries. The relationship graph:
- `principal —owns→ agent` (the identity unit — §3).
- `resource —owned_by→ (principal | agent)` (ownership — the owner stamp, §4).
- `resource —scoped_to→ <tier>` (the scope, §4).
- `principal —keeps→ keep` (a member-created, keeper-owned collaboration space — §4.4) and
  `principal —member_of{rank}→ keep` (household membership, the `rank` a future per-Keep-role seam).
- `principal.role ∈ {member, admin}` (the coarse GLOBAL capability input — packet 49's shipped
  domain; distinct from a Keep `rank`, which is per-Keep).

### 2.2 One PDP, in-process, in `lorerunes`/`loremaster`
A single Policy Decision Point — a typed Python class — is the ONLY place an authorization
decision is made. It reads the graph and answers exactly one shape of question (§5). Every tool
routes through it; no tool hand-rolls a check. This is the ONE-IMPLEMENTATION law applied to
authorization: policy is a function callers invoke, never a pattern they clone.

### 2.3 Native store `PERMISSIONS` stays OFF — it is inert under root (the trap)
SurrealDB's record-level `PERMISSIONS ... WHERE` clauses **do not apply to root/system users, who
bypass them entirely** (`surrealdb.com/docs/surrealdb/security/summary`). lore connects as root,
so any permission clause written today enforces **nothing** — green tests, zero enforcement: the
exact silent-inert-schema shape of the #107 outage. Getting native enforcement while staying root
is SurrealDB issue #6259 (OPEN, unimplemented). Therefore:
- **Version A (this design):** keep the root connection; enforcement is the in-process PDP; native
  PERMISSIONS is NOT used, and a pin asserts we never rely on it under root.
- **Version B (documented future option, NOT now):** re-plumb to per-principal *record auth*
  (`DEFINE ACCESS TYPE RECORD`, `$auth`-bound sessions) so the engine filters in-engine and *is*
  the single decision point — the strongest, least-bypassable form. Cost: split root ops
  (indexing, migrations, cross-principal admin, the fleet identity) from the per-principal data
  path, and re-plumb session auth. Gated on a decision to move + closing the perf question in §6.
  ⚠ Security advisory GHSA-x5fr-7hhj-34j3 (SurrealDB default table permissions were *FULL*) — if
  Version B is ever adopted, every table must explicitly set scoped/`NONE`, never trust defaults.

### 2.4 pycasbin — rejected for the core, with the split-brain reason
`pycasbin` is the strongest *maintained* in-process engine (Apache-2.0, RBAC-with-domains + ABAC).
It is rejected here for one structural reason the operator gated on:
- **It cannot emit a query predicate** (verified: no pushdown). It adjudicates one object at a
  time. lore's discriminating requirement is *read isolation as a WHERE-filter on a list* (§6), so
  if Casbin owned any row-touching decision, the read-filter would have to be a SECOND mechanism
  beside Casbin's write-check — and keeping those two in agreement by hand **is** the split-brain.
- **Confining Casbin to the row-independent capability bit** (`role → write-class?`) *is*
  split-brain-safe, but then it does a trivial lookup, and everything valuable it offered —
  RBAC-with-domains, the group-grouping that models "principal + its agents" — is precisely the
  relationship layer we must keep in the single graph-PDP. Net: a dependency + a bespoke
  SurrealDB adapter (none exists — verified) + a "its store must stay a pure projection of the
  graph" discipline, to decide `member→read, admin→write`.
- **Verdict:** skip it. Model roles/domains/agent-grouping as graph edges (§2.1); keep pycasbin on
  the shelf only if a genuinely row-independent, rule-heavy capability policy ever emerges, and
  prove the disjointness before adopting.

---

## 3. Identity — principal ↔ agent, and the anti-spoofing / anti-injection design

### 3.1 The unit: `principal 1—* agent`
Today `principal` (human, email — packet 48) and the comms `agent` (fleet actor, name/session) are
DELIBERATELY unlinked identity vocabularies (48's docstring forbids wiring them). Authorization
needs them linked: **a principal owns N agents, and "a user and their agents" is ONE trust unit**
— which is exactly the isolation boundary the operator named (a user + their agents vs *other*
users). The graph gets a `principal —owns→ agent` edge; every agent action is authorized as
*(its principal, itself)*.

### 3.2 The security bar, stated honestly
The operator set the bar as *"prevents spoofing and prompt injection."* The honest framing, which
the threat model (§9) makes explicit for the auditor:
> **No identity mechanism *prevents* prompt injection** — injection attacks the agent's reasoning,
> not its credential. What identity does is **contain the blast radius**: guarantee that an
> injected or malicious agent can do *nothing its authenticated identity was not already allowed
> to do* — it cannot impersonate another principal/agent, escalate its scope, or cross the
> isolation boundary. Clearing the bar = making that containment airtight.

Three things clear it *together*; all three are required, and the auditor tests each:

1. **Server-bound, short-lived `(principal, agent)` credentials** (the mechanism). The agent's
   identity is minted and bound SERVER-SIDE at agent start, never self-declared. Contrast the
   rejected "agent self-labels" option: a self-declared name lets an injected agent-A stamp writes
   as sibling agent-B (within-principal spoof). Server-binding confines an injected agent to
   EXACTLY its own `(principal, agent)` scope. Short-lived limits the window if a token leaks.
2. **Identity and owner come ONLY from the credential context — NEVER from a tool argument** (the
   load-bearing anti-injection invariant). No write tool may accept `owner=`, `as_agent=`,
   `created_by=`, or a caller-chosen `scope=server` — an injected agent would set them maliciously
   (confused deputy). The owner stamp is read from the authenticated session
   (`get_access_token()` → the resolved principal+agent), full stop. **This retires the current
   free-form `created_by`/`actor`/`owner`/`agent=` arguments as authorization inputs** — they
   become server-derived, or (for display) sanitised labels that carry no authority.
3. **Scope-on-write is PDP-validated** — an agent creating a row cannot declare a scope its
   principal is not allowed to grant (a `member` cannot mint a `server`-scoped row; promoting a
   row's scope is itself a gated action).

### 3.3 The concrete plumbing question (flagged, to solve in the contract phase)
MCP carries ONE bearer token per CONNECTION. The `(principal, agent)` binding must ride that model.
The likely shape: **each agent opens its own connection with its own short-lived minted token**
(the principal authenticates once via OAuth/api-key, then mints per-agent session tokens bound to
`(principal, agent)`; the agent presents its token, and every call reads identity from it, never
from an `agent=` argument). This converges "server-bound short-lived credential" with "each agent
has its own credential" — the difference from a long-lived per-agent key is lifetime + server
minting. Exact mechanism (token-exchange endpoint? `lore-adm`/register-time mint? MCP session
binding?) is a design detail for the contract; it is NAMED here as the one non-trivial piece so it
is met deliberately, not improvised.

---

## 4. Ownership, scope, and Keeps

Every governed row (comms message, memory note, task, finding) carries two authorization columns,
both server-stamped, never caller-supplied for authorization:
- **`owner`** — a `(principal, agent)` reference derived from the credential (§3.2 invariant 2).
- **`scope`** — one of:

| scope | who may READ | typical use |
|---|---|---|
| `agent-private` | the owning agent only | an agent's scratch/working notes |
| `principal-private` | the owning principal + its agents | a user's personal memory; a private task |
| `keep:<id>` | the Keep's **household** (its members — §4.4) | a project/team's shared work; a comms thread; a DM (a 2-member Keep) |
| `server` | everyone admitted | server-wide announcements; a row a member chose to publish widely |

A **Keep** is a first-class, member-owned collaboration space (§4.4); `keep:<id>` scope is
PARAMETERIZED by which Keep, so the model is **relationship-based (ReBAC) over the graph, not a
flat lattice** — exactly what the graph-PDP is for. The operator's 5-tier intent is preserved as
Keep **TYPES** (`project` / `team` / `session` / `dm`), not separate scope enum values — a new
collaboration flavor is a new Keep type, never a new tier.

**READ follows scope; WRITE follows ownership + the Keep household — the 3-way rule (RULED
2026-08-21):**

| the row's scope | who may WRITE (edit / transition) | who may DELETE (hard) |
|---|---|---|
| `agent-` / `principal-private` | the owner only | owner + admin |
| `keep:<id>` (shared) | **any member of the Keep's household** | the row's owner + admin |
| `server` (broadcast) | the owner + admin | owner + admin |
| any scope, `admin` | admin (audited) | admin (audited) |

So a Keep is genuinely COLLABORATIVE — a household member claims another's task, corrects another's
memory, supersedes another's finding — precisely because the row's owner CHOSE to scope it into the
shared Keep. Private scopes stay owner-only (isolation intact — the owner opts *into* collaboration
by choosing a Keep scope). A hard DELETE stays the owner's (or admin's): members correct and
supersede, they do not *vanish* each other's work. `server` is broadcast — everyone reads, only the
owner (or admin) edits (so nobody vandalizes global rows).

This ONE model unifies all four tools:
- **`lore_comms`:** a thread/session channel = a `keep:<id>`-scoped set (the Keep's household is the
  channel's members); a direct message = a tiny auto-created **2-member Keep** (type `dm`, §10-L
  ruled (b)). *A user's inbox is theirs; another user cannot read it* — by construction.
- **memory:** each note carries a scope. A `keep`-scoped note is shared with that Keep's household
  (today's project notebook = the project Keep, so the dogfooding fleet is unbroken);
  `principal-private` = personal; `agent-private` = an agent's own. This DISSOLVES the
  shared-vs-private fork — memory is per-note scoped.
- **`lore_tasks`:** the operator's "user-only vs server-level" = the scope ladder
  (`principal-private` / `keep` / `server`); a Keep task is CLAIMABLE by any household member.
- **`lore_findings`:** a `keep`- or `server`-scoped shared ledger, `principal-private` available;
  any household member may resolve/supersede a Keep finding.

### 4.1 The read side is FILTERING, not gating
Authorization on reads is a row predicate the PDP emits, applied inside the store query
(`WHERE owner IN $my_ids OR scope = 'server' OR scope IN $my_keeps ...`), NOT a yes/no at the tool
boundary. `lore_recall`, `lore_comms drain`, `lore_tasks query`, `lore_findings query` all filter
to the caller's visible set — `$my_keeps` being the Keeps whose household the caller is in
(resolved by the PDP, §6). The code-corpus tools (§1) are exempt — shared-read.

### 4.2 Role — `member` is instance-gated; `admin` is a superuser short-circuit
`principal.role` (member/admin) enters the decision in two very different ways (RULED §10-K):
- **`member`:** role is ONE input, never the whole decision. A member's authorization is
  ownership+scope: they read/write their own rows and rows in scopes visible to them. Role alone
  never authorizes a row — the operator's original security hole (every "user-role" user could
  write everyone's channel) is structurally impossible, because the member predicate always ANDs
  in ownership/scope.
- **`admin`:** a FULL SUPERUSER — the PDP short-circuits to allow-all (bypassing the
  ownership/scope predicate), and admin additionally holds the tier-modify and owner-modify verbs
  (§4.3). This is a deliberate, audited bypass (§9), not a scope value.

### 4.3 Who may change scope / delete / ownership (RULED 2026-08-21)
- **A `member` may change the `scope` of a row it OWNS — freely, UP or DOWN, to any scope** (a Keep
  it belongs to, `principal-private`, or `server`). It is the member's own data; publishing it or
  locking it down is theirs, and publishing one's OWN row grants no power over anyone else's.
- **A hard DELETE of a shared (`keep`/`server`) row is the row-OWNER + admin only** — household
  members edit/supersede but never *vanish* each other's rows (RULED). (Private rows: owner + admin.)
- **A `member` may NOT** change the scope of a row it doesn't own, transfer a row's OWNER, or touch
  another member's private rows.
- **`admin`** may change/delete ANY row and reassign ANY owner (`set_scope`/`set_owner`/`delete`
  across all rows) — the only cross-owner authority; every such action is AUDITED (§9).
- All route through the SAME `authorize` seam (§5) — one permission brain.

### 4.4 Keeps — first-class, typed, member-owned collaboration spaces (RULED 2026-08-21)
A **Keep** (owner = **keeper**; members = **household**) is a first-class OWNED object in the graph
— not a scope enum value. The name carries the model: a keep holds *and* protects its contents, and
lore's own loremaster is "the keeper," so a keep kept by keepers is the house idiom.
- **Any `member` may CREATE a Keep** and becomes its **keeper** (`principal —keeps→ keep`).
- **The keeper MANAGES the household** — adds/removes members (`principal —member_of{rank}→ keep`
  edges), gated in the PDP to the keeper (and admin).
- **A Keep is TYPED** (`type ∈ {project, team, session, dm, …}`): `session` = ephemeral fleet
  coordination; `project`/`team` = persistent, member-created; `dm` = a 2-member Keep (§10-L). A
  new collaboration flavor is a new `type`, never a new scope tier.
- **Keep-scoped rows are visible to the household and writable by any member** (§4); each row is
  still OWNED by its creator (provenance preserved in supersede/transition chains), who alone
  deletes it (or admin).
- **The membership edge carries a `rank` — RULED as a SEAM:** `member_of{rank}→ keep`. Today `rank`
  is FLAT (every member is a plain collaborator — all the current scenarios need). Tomorrow,
  **per-Keep ranks** (`viewer` / `contributor` / `steward` / `keeper`) drop in by having the PDP
  read the edge's `rank` — no schema tier, no rewrite. **This RESOLVES §10-P:** the keeper's power
  is simply their `rank`, and "may the keeper edit household rows" becomes a future per-rank
  capability, not a bespoke rule. (The GitHub-repo model: per-repo roles independent of global admin.)

---

## 5. The PDP contract — one expression, one brain (the anti-split-brain invariant)

The PDP answers exactly one shape of question, in two forms that are THE SAME expression:

```
authorize(subject, action, resource)  -> Decision           # single row: boolean
authorize_filter(subject, action)     -> SurrealQL predicate # a list: the WHERE fragment
```

**The load-bearing invariant (this is how we are SURE there is no split-brain):**
> **The single-row gate IS the list-filter predicate applied to that one row.**
> `authorize(s, a, row).allowed  ≡  authorize_filter(s, a).matches(row)`  for every `s, a, row`.

There is ONE policy expression PER ACTION (the predicate). READ and WRITE are distinct actions with
distinct predicates (you may read a `server` row you cannot write, or read a Keep row you can
supersede but not delete — §4), but each action independently keeps this property: the single-row
gate for that action IS that action's filter applied to one row. Reads apply the read-predicate to
a set; writes apply the write-predicate to a singleton. Because both fates for a given action come
from the same expression, there is **structurally one brain** per action — a write-check cannot
disagree with its own filter, because they are the same thing. This is
architectural, not disciplinary. It is **mutation-proven**: change the predicate, and BOTH the
read-filter and the write-gate must move; any caller that stays green is a private copy wearing the
shared name (ROUTING-IS-NOT-SHARING). And the equivalence itself is a pin: for a fixture row set,
`{r : authorize(s,a,r).allowed}` must equal `store.query(authorize_filter(s,a))` exactly.

**The admin short-circuit lives INSIDE the one expression, not beside it** (§10-K). For an `admin`
subject, `authorize_filter` returns the TRUE predicate (all rows) and `authorize` returns allowed
for every row — so the §5 equivalence still holds trivially for admin (all-vs-all), and there is
still ONE brain. ⚠ Admin is NOT a second code path that bypasses the PDP: it is the `role==admin`
branch OF the PDP, so a bug that grants admin cannot also silently drop the equivalence, and the
audit stamp (§9) is emitted on the admin write path within the same seam. Pin the admin branch as a
role-axis fixture (member filtered, admin all) with the audit-record assertion on admin writes.

**Coverage is a checked variable** (the reach law, #344/#345): the PDP's reach = every governed
tool/verb. A test enumerates the full governed surface and asserts each write routes through
`authorize` and each list-read through `authorize_filter` — a new governed tool that bypasses the
PDP reds the coverage pin. Reach is DERIVED from the registry, never a hand-list.

---

## 6. Read-filter emission + the store-law questions

The PDP emits a SurrealQL `WHERE` fragment plus bound params (never string-interpolated — store
law: `CONTENT`/bound params, injection-safe). Open store-law items to settle in the contract/probe
phase (named per the trust law):
- **Indexing:** `owner` and `scope` need indexes for the filter to be an IndexScan not a
  TableScan (store law §2 — a range/equality predicate on an indexed column). `owner` is a
  record-link (indexable); `scope` is a small enum (indexable). A composite `(scope, owner)` may
  serve the common filter.
- **⚠ Can a permission predicate traverse graph edges performantly?** (e.g. "rows in a group I'm a
  member of" = `scope = 'group' AND group IN $my_groups`, where `$my_groups` is pre-resolved by
  the PDP from a graph traversal, NOT traversed inside the row predicate). Store law §4: a graph
  TRAVERSAL never uses a secondary index and is bounded by node degree — so **the PDP resolves the
  caller's visible-scope/group SET first (a bounded traversal from the principal), then emits a
  flat `IN $set` predicate** the row query can index. Do NOT put an arrow-traversal inside the
  per-row `WHERE`. This mirrors how `graph_surreal.py` already reads the code graph (plain SELECTs,
  not traversals in the read surface). Needs a live probe on the 3.2.4 store to confirm the plan.

---

## 7. Migration — existing rows carry free-form strings (a #107/#131-class hazard)

Every existing comms/memory/task/finding row has a free-form `created_by`/`actor`/`agent` string,
NOT a principal/agent reference, and no `scope`. Introducing `owner`+`scope` on populated tables:
- **Store law §1.4:** a NEW required field on a populated table poisons every existing row — the
  new columns must be `option<>` (or migrated with a backfill) and the read path must tolerate
  absence. A `DEFAULT` does NOT rescue existing rows.
- **Grandfathering:** existing rows map to a legacy scope — recommend `project` (visible to the
  admitted fleet, matching today's shared behavior) with `owner` = a sentinel/best-effort mapping
  from the old string where resolvable, else an unowned-legacy marker that only `admin` sees.
- This migration is exactly the virgin-DB blind spot (#107/#131): every test mints a clean DB, so
  the migration defect is invisible to the suite — it MUST be proven against a dirty store
  (`TestSchemaMigrationAgainstAnExistingStore` idiom) and in the deployed image.

---

## 8. Relationship to packet 39 + sequencing (operator-RULED 2026-08-21)

- **Packet 39 is now READ-ONLY hosted (RULED):** it ships authentication (the verified principal +
  role, carried forward), the read-only hosted surface, the read-corpus enforcement, and the
  **forward-compat SEAM** for this model — the authenticated identity available at every call via
  `get_access_token()`, shaped to carry an optional `(principal, agent)` binding this model's
  owner-stamp + PDP consume. **ALL write moves here** — member row-scoped write AND admin superuser
  — because coarse hosted write is unsafe without the row model, and every write tool in lore is a
  governed coordination tool anyway (§1). The prior F4 "admin→hosted-write" ruling is SUPERSEDED by
  this model. (LOOPBACK + LAN_BEARER — the trusted local/LAN fleet — keep their current full-write
  behavior; this model tightens them later, not in the interim.)
- **This model is its own packet (§10-M RULED: yes).** Foundational, cross-cutting — the identity
  substrate, every governed store, the fleet coordination model.
- **⚠ DEPLOY COUPLING (RULED): packet 39 and this RBAC packet ship as ONE cutover — no 39-alone
  rebuild/redeploy.** 39's build may complete (green gates, read-only) and SIT; the container is
  not rebuilt/recreated, the posture is not flipped, the edge/connector is not wired, until this
  model lands. So the first hosted deploy is read + row-scoped write together — there is never a
  useless read-only-hosted interim in production. The deploy plan is jointly owned by the two
  packets; whichever lands the code second owns the single rebuild+recreate.

---

## 9. Threat model for the security auditor (explicit — a gate needs a threat model)

Written so the auditor attacks a stated target, not an implied one. The auditor is the arbiter of
whether §3 clears the operator's bar.

**IN scope (must hold):**
- **Cross-principal isolation:** principal-A (and all A's agents) cannot READ or WRITE
  principal-B's `principal-private`/`agent-private`/direct-message rows. The owner/scope predicate
  is derived from B's credential; A's queries never see B's set.
- **Anti-spoofing:** an agent cannot present as another principal (identity from the verified
  token) NOR as a sibling agent (server-bound `(principal,agent)`, not self-declared — §3.2.1).
- **Injection containment:** an injected agent can do nothing outside its authenticated
  `(principal, agent)` scope — because identity/owner never come from tool arguments (§3.2.2) and
  scope-on-write is PDP-validated (§3.2.3). Injection cannot escalate role, forge an owner, mint a
  higher scope, or read another principal's data.
- **Confused deputy:** no write tool accepts an authorization-bearing argument (`owner=`,
  `as_agent=`, `scope=server` for a member). Pin: fuzz every write tool's args with hostile
  owner/scope values → the stamp is unchanged (server-derived).
- **The single-brain equivalence (§5):** `authorize(row) ≡ authorize_filter().matches(row)` — no
  row is writable-but-invisible or visible-but-unwritable-by-a-different-rule.
- **Scope-promotion is gated:** raising a row's scope (private→server) is an explicit action the
  PDP checks against role/ownership, not a free `UPDATE`.

**ACCEPTED bounds (named, not defects):**
- **An injected agent within its OWN scope** can corrupt its own rows — that is the agent's own
  trust domain; identity contains it to that domain, no further.
- **A stolen short-lived agent token** acts as that agent until expiry/revocation — mitigated by
  short lifetime + revocation; the reason lifetime is short.
- **`admin` is a FULL, UNRESTRICTED SUPERUSER (§10-K, RULED; unrestricted confirmed 2026-08-21)** —
  cross-principal read/write + modify scope + modify owner, bypassing the ownership/scope predicate
  entirely, **and reachable from ANY surface including HOSTED/internet** (the operator ruled admin
  unrestricted — there is no local/LAN-only confinement on admin write). Consequence: **a stolen or
  injected admin credential is total store compromise** (every principal's private data + the power
  to rewrite ownership), and that credential may be an internet-facing hosted token. This is the
  single highest-value credential in the system, so the mitigations are ALL that stand between it
  and catastrophe:
  (a) the admin set is deliberately minimal and operator-curated;
  (b) admin authentication is the strongest available (short-lived tokens, and — recommended, not
  ruled — a step-up / stronger factor for the admin role, since hosted admin is permitted);
  (c) **every admin action is AUDITED (RULED)** — an admin write / scope-change / owner-change
  stamps a record (who, what row, old→new, when) into a **dedicated append-only `audit` store that
  is the ONE carve-out from "admin = full": admin canNOT delete or modify audit rows.** The audit
  table is EXEMPT from the PDP's admin short-circuit (its write path is append-only for everyone,
  including admin), so a compromised admin cannot erase its own trail. Pins: an admin mutation of
  another principal's row writes the audit record; an admin attempt to DELETE/UPDATE an audit row
  is refused (the append-only carve-out); the audit record captures old→new.

**NOT a defense against:** an agent injected into doing something *within* its rights (lore cannot
police an admin's own agent). That is the confused-deputy bound packet 39 §1 already accepts.

---

## 10. Fork status (operator rulings 2026-08-21)

**✅ RULED / CLOSED:**
- **§10-K — `admin` = FULL, UNRESTRICTED superuser.** Cross-principal read/write + modify
  scope/owner, bypassing the ownership/scope predicate, reachable from ANY surface including
  hosted/internet (unrestricted — no local/LAN confinement). PDP short-circuit (§5); the §9 bound
  (total-store reach → minimal set + strong auth + audit) is the mitigation.
- **§10-M — own packet: YES.** Foundational, cross-cutting; sequenced after packet-39 auth, and
  packet 39 + this packet ship as ONE deploy (§8).
- **§10-N — default scope per tool: CONFIRMED.** memory→`project` (unbroken fleet),
  tasks→`principal-private`, comms→conversation-`group`, findings→`project`.
- **§10-O — agent-credential mint mechanism: DEFER to the design/contract phase with a dedicated
  security-auditor pass** on the chosen mechanism (it is the anti-spoofing surface). Agreed.
- **Admin audit: append-only, admin-EXEMPT, dedicated store** (§9) — the one carve-out from
  "admin = full."
- **Member ownership/scope control + projects (§4.3/§4.4):** members create+own+manage projects
  and control the scope (up/down, any tier) of rows they own.

- **§10-L — DM mechanism: ✅ RULED (b)** — a direct message is a tiny auto-created 2-member Keep
  (type `dm`), reusing the household machinery. One mechanism for all shared visibility.
- **§10-P — write authority within a Keep: ✅ RESOLVED (RULED 2026-08-21).** Write follows SCOPE,
  not creator (the 3-way rule, §4): private=owner, `keep`=any household member (collaboration),
  `server`=owner+admin; hard-delete of a shared row = owner+admin. The keeper is not a bespoke
  row-superuser — the keeper's (and any future differentiated) power is the per-Keep `rank` seam
  (§4.4). Naming RULED: the collaboration container is a **Keep** (keeper / household / rank).

**Nothing open.** The model is fully specified for the contract phase.

---

## 11. Packages / DRY / what the contract + adversary + auditor must pin

**Packages considered:** the full authz-framework survey (2026-08-21, verified against installed
source + vendor docs by a research scout) — verdict **bespoke in-process PDP over the SurrealDB
graph**, because (a) every external PDP (OpenFGA/SpiceDB/Cerbos/Keto/Topaz/Permify) is a new
service + a second source of truth and cannot push a read-filter predicate into SurrealDB
(contradicts single-decision-point + minimize-services), (b) `pycasbin` cannot be the single brain
for the read path (§2.4), (c) native store PERMISSIONS is inert under root (§2.3), (d) `oso`'s
embedded library is deprecated (2023-12-18). The bespoke surface is minimal and deliberately narrow
(one PDP class + graph edges + the WHERE emitter), and it mirrors Permit.io's own verified
architecture on SurrealDB — the "package doesn't fit OUR constraint (single-brain + pushdown +
no-new-service)" leg of packages-over-hand-rolling, stated so a future reader does not "helpfully"
bolt on OpenFGA and reintroduce the split.

**DRY:** ONE PDP (`authorize`/`authorize_filter` — the same expression, §5). ONE owner-stamp seam
(server-derived, §3.2.2). ONE scope lattice (§4). ONE visible-set resolver (the graph traversal,
§6). Prove sharing by mutation in every case.

**What the contract / adversary / security-auditor must pin:**
- The §5 equivalence `authorize(row) ≡ authorize_filter().matches(row)` (mutation-proven both
  ways) + coverage == the full governed surface (a bypassing tool reds it).
- The §3.2 invariants: identity/owner NEVER from a tool argument (fuzz every write tool);
  server-bound agent identity (a self-declared name cannot spoof a sibling); scope-on-write
  validated (a member cannot mint server scope).
- Cross-principal isolation over the wire (principal-A's drain/query/recall never returns
  principal-B's private rows) — hostile fixture with ≥2 principals, ≥2 agents each.
- The §7 migration against a DIRTY store (existing free-form rows survive; new isolation holds) +
  in-image conformance.
- Scope-promotion gating; the DM ACL; the store-law read-filter plan (IndexScan, not TableScan;
  no traversal inside the per-row WHERE) — probed live on 3.2.4.

---

*Every recommendation is a recommendation; the operator rules §10, and the security-auditor +
contract-adversary are the named arbiters of §9's enforcement. This design mirrors Permit.io's
verified SurrealDB architecture, keeps lore's root connection (Version A), and holds native
PERMISSIONS as a documented future option (Version B) gated on record-auth re-plumbing.*
