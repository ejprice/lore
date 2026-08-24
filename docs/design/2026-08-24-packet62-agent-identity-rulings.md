# packet 62 — agent-identity binding / anti-spoofing — design rulings

**Author:** design-sidecar-62 (Fable), 2026-08-24, working tree `5b50063` (branch
`feat/surreal-unification`).
**Nature:** design DOC, now FINALIZED for the contract author. All four forks were escalated
and are OPERATOR-RULED (2026-08-24 — §OPERATOR RULINGS). The security-auditor is the named
arbiter of the anti-spoofing mechanism (authorization-model §9/§10-O); the contract-adversary
grades the contract that implements this.
**Status:** design finalized, not yet contracted. Consumes the CODE-COMPLETE 39/48/49/60/61
substrate (all commit-only; deploy = the packet-65 joint cutover).
**Revision:** v4 (2026-08-24) — v2 folded operator rulings; v3 corrected the `record<principal>`
link count (FOUR, not three; 61a-w4 audit link was missed); **v4 adds the WAVE-2 ADDENDUM (at the
end)** — the concrete capability mechanism: credential-not-claim crux (SF-1), `capability_hash`
field on `agent` + shared `parse_credential` (DRY), mint-in-register / agent-lifecycle lifetime
(SF-2) / no-cache revocation, the `resolve_agent` seam relocation (SF-3), ONE-wave scope, and the
per-item security-auditor attack surface.

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — cited by § below
  (§1.1 DDL clause rule, §2 record-link cascade, §4 RELATE/`ENFORCED`/traversal-not-indexed,
  §4 field-vs-edge-hop modelling). Never re-transcribed.

---

## 0. What this packet owns, and the one fact that reshapes it

Packet 62 links the two DELIBERATELY-unlinked identity vocabularies — `principal`
(human/email, packet 48) and the comms `agent` (fleet actor, packet 03a/registry) — with a
`principal —owns→ agent` relationship (authorization-model §3.1), mints the server-bound
`(principal, agent)` identity the anti-spoofing bar needs (§3.2/§3.3/§10-O), and lands the
anti-injection invariants (§3.2.2 — identity/owner never from a tool argument;
§3.2.3 — scope-on-write PDP-validated). It fills the seam packet 39-W1 shaped
(`agent_of(access_token)` — `token_verifier.py`, always `None` today) and produces the typed
`Subject` packet 61 already consumes (`lorerunes.pdp.Subject(principal_id, agent_id, role,
visible_keep_ids)`).

**THE FACT THAT RESHAPES EVERYTHING — the local fleet has no per-agent credential, and no
MCP client presents one.** Two ground-truths, read this session:

1. **The local dogfooding fleet connects over PLAIN HTTP LOOPBACK with NO token at all.**
   `.mcp.json` at HEAD is exactly `{"lore_lore": {"type": "http", "url":
   "http://127.0.0.1:9202/mcp"}}` — no `Authorization` header, no bearer. Under
   `Posture.LOOPBACK` (`lorerunes/lorerunes/posture.py::derive_posture`, `auth_enabled=False`)
   **no auth provider is installed at all** (posture.py module docstring: *"The unchanged
   local single-user mode; no auth provider is installed."*). So on the local path
   `get_access_token()` is `None`, `agent_of()` is `None`, and there is no credential to derive
   an owner from. Every packet-62/63/64 worker — including the fleet reading THIS doc — is on
   that path right now.

2. **The comms `agent` identity is SELF-DECLARED, by construction.**
   `AgentRegistry.register(name, *, session, role, …)` (`loremaster/loremaster/agents.py:598`)
   mints the row id as `agent_id = uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}")`
   (`_agent_id`, confirmed live) — a pure function of the caller-supplied `(session, name)`.
   Nothing authenticates that pair. `agent=` is then a plain argument on EVERY `lore_comms` /
   `lore_tasks` / `lore_findings` call. That is precisely the confused-deputy surface §3.2.2
   forbids — an injected agent stamps writes as any sibling name it types.

**What packet 61 ALREADY settled, which shrinks Fork 3.** The PDP IR does not invent a
third agent notion — it BINDS to the comms one. `OwnerAgentEq.to_surql()`
(`lorerunes/lorerunes/pdp.py:249`) emits `owner_agent = type::record('{AGENT_TABLE}',
$agent_id)`, i.e. `owner_agent` is a `record<agent>` link into the comms `AGENT_TABLE` and
`Subject.agent_id` IS the comms-registry id. So "the three notions of agent" are already ONE
in the store; 62 must (a) shape the `owns` edge consistent with that, and (b) decide who
CONSTRUCTS a `Subject` from a credential and how the agent half becomes server-bound.

**What packet 61 did NOT do (confirms the 62↔63 line).** The `owner_principal`/`owner_agent`
COLUMNS are not yet on the governed tables — `pdp.Resource` tolerates an absent owner
(`test_pdp_core.py::test_resource_accepts_an_absent_owner`, `option<>`/legacy), and packet-61
memory records the governed-store retrofit (owner+scope columns, PDP routing, row migration)
as 63/64. The classification `partition_tools_by_population` is present but INERT at 61 HEAD.

---

## FORK 3 — the `owns` edge shape (ruled; foundational, so first)

**RECOMMENDATION (not MAJOR — strong direct precedent): a SCALAR field link
`agent.owner_principal : record<principal>` on the comms `agent` table — NOT an `owns`
RELATION edge.** The `principal —owns→ agent` relationship of authorization-model §3.1 is
realized as a back-reference field on the many-side node, exactly as packet-60 Fork-A realized
`keeper`.

**Rationale (cite store-ref + precedent + 61 code):**
- **Packet-60 Fork-A is the governing precedent, verbatim shape.** The sidecar ruled `keeper`
  a scalar `keep.keeper` FIELD LINK (a `record<principal>`) rather than a `keeps` RELATION
  edge — *"semantically identical; store-law §4 scalar→field."* `owns` is `principal 1—*
  agent` — a one-to-many whose natural home is a scalar link on the MANY side (`agent`), the
  textbook field-link shape. Two edge tables for the same 1—* would be gratuitous.
- **Store law §4 (traversal is never index-served) makes the field the PERFORMANT choice.** A
  graph TRAVERSAL (`principal->owns->agent` / `agent<-owns<-principal`) *"never uses a
  secondary index and is bounded by node degree"*, and the store-ref's own field-vs-edge-hop
  rule is decisive: *"a scalar attribute filtered through a hop is un-indexable by
  construction — keep scalars as indexed fields and spend edges on real relationships."* The
  owner-of-an-agent is a scalar attribute, not a real relationship needing traversal — so it
  is a field.
- **It is CONSISTENT with the owner representation packet 61 already chose.** Governed rows
  carry owner as TWO indexed FIELDS `owner_principal` + `owner_agent` (61 ruling, *"not a
  composite ref"*), and `OwnerAgentEq`/`OwnerPrincipalEq` emit `= type::record(TABLE, $id)`
  field equalities. `agent.owner_principal : record<principal>` is the same idiom one level up
  — the agent node's own owner, mirrored from the row-owner representation.

**RECONCILING THE THREE "agent" NOTIONS INTO ONE (the core of this fork):**
There is ONE canonical agent identity, and it is the **comms registry id**
`agent_id = uuid5(NAMESPACE_URL, "lore://agent/{session}/{name}")`. Everything else is that
same id in a different seat:

| notion | where | what it is |
|---|---|---|
| comms registry `agent` node | `agents.py` `AGENT_TABLE`, `_agent_id` | THE identity — the fleet actor row |
| `Subject.agent_id` | `lorerunes.pdp.Subject` | the SAME id, carried into the PDP |
| `owner_agent` on a governed row | 63/64 column, `OwnerAgentEq` | `record<agent>` link = the SAME id |
| `agent_of(access_token)` | `token_verifier.py` | the SAME id, resolved from the credential (62 fills this) |
| `agent.owner_principal` | NEW this packet | the `owns` back-link: which principal owns THAT agent node |

So `agent_id` is **the comms registry id, full stop** — never a new "minted-credential id" and
never a fourth identity. The `owns` edge is `agent.owner_principal`, and the CREDENTIAL→Subject
resolution (Fork 1) reads `principal` from the token and `agent` from the registry.

**RIDERS — and pin/verify each like this:**
- **R3.1 — a NEW `record<principal>` link ⇒ revisit the delete accounting AND its exact-set
  pin, in THIS packet.** ⚠ **COUNT (re-derived 2026-08-24 by grepping `record<{PRINCIPAL_TABLE}>`
  field specs in `surreal_schema.py` — never trust an inherited number): there are THREE
  EXISTING `record<principal>` links at HEAD, so `agent.owner_principal` is the FOURTH:**
  1. `principal_key.principal` (`surreal_schema.py:1908`) — delete CASCADES it (children-first).
  2. `keep.keeper` (`:2037`) — delete REFUSES-while-keeping (§FR-4).
  3. `audit.actor_principal` (`:2187`, packet 61a-w4) — **DANGLE-tolerated**; delete does NOT
     act on it (the append-only admin-exempt audit store survives a principal delete BY DESIGN —
     `actor_email`/`actor_agent_name` are denormalized for exactly that, §9).
  So there are TWO populations: links that EXIST (now three, four with `owner_principal`) vs
  links the delete ACTS ON (two: cascade + refuse). **`agent.owner_principal` is RULED
  DANGLE-tolerated (R3.2)** — so, like `audit.actor_principal`, delete does NOT act on it and
  the acts-on set stays two; what changes is the EXISTING set → four.
  ⚠ **The `PrincipalStore.delete` docstring itself (`principals.py:662`) UNDERCOUNTS** — it says
  *"the delete accounts for the TWO record<principal> links … principal_key.principal and
  keep.keeper. When ANY new record<principal> link is added (63/64's owner_principal next), this
  MUST be revisited."* That was written at §FR-4 (before 61a-w4 added `audit.actor_principal`)
  and never updated — the P8d stale-prose class. FLAG (code, outside my writable set — exact
  edit for the builder): when 62 revisits delete, correct the docstring to name all FOUR
  existing links with their disposition (two acted-on: cascade/refuse; two dangle-tolerated:
  audit.actor_principal + the new agent.owner_principal). PIN: **red the exact-set pin**
  (`test_principal_keys_schema.py`) until `agent.owner_principal` is added as the FOURTH link
  and adjudicated DANGLE. A field-link that does NOT auto-clean (store law §2: *"record<t> links
  do NOT auto-clean on target delete"*) left un-adjudicated is a #105-class dangling-owner ghost
  — dangle-tolerated is a DELIBERATE adjudication, not an omission.
- **R3.2 — principal-delete semantics for owned agents: RULED DANGLE-tolerated (operator,
  2026-08-24); PIN it with a dirty-store test.** Rationale (ratified): mirrors packet-61a-w4's
  audit link — agents are retired-not-deleted; an owned-agent row surviving a principal delete
  is a stale back-link, not a correctness break; `audit.actor_principal` already chose
  dangle-tolerated for the same class. Do NOT cascade-delete agent rows on a principal delete
  (that would erase fleet history), and do NOT refuse-while-owning-agents (an owned agent is not
  a reason to block an admin principal delete, unlike a kept keep). Pin: create principal →
  register an agent owned by it → delete principal → assert the agent row SURVIVES with a now-
  dangling `owner_principal` (dangle-tolerated) on a DIRTY store
  (`TestSchemaMigrationAgainstAnExistingStore` idiom, store-ref §1.6).
- **R3.3 — the `owns` edge is minted SERVER-SIDE at register, never from an argument.** The
  stamp `agent.owner_principal = <principal-from-credential>` happens inside `register`,
  reading the principal from `get_access_token()` (§3.2.2). Pin by MUTATION: a `register` call
  that tries to pass an owner principal as an argument is refused / ignored; the stamped owner
  is the credential's, proven by a fixture whose argument owner ≠ credential owner (the
  stamped value follows the CREDENTIAL). See Fork 1 for the loopback exception.
- **R3.4 — DDL clause rule (store-ref §1.1).** `agent.owner_principal` is a FIELD →
  `DEFINE FIELD OVERWRITE`; it is added to a POPULATED table (`agent` has live rows) → it MUST
  be `option<record<principal>>` (store-ref §1.4: *"A NEW field on a POPULATED table must be
  option<>"*; a required field poisons every existing agent row, a DEFAULT does not rescue it).
  Its index is `DEFINE INDEX … IF NOT EXISTS` (never `OVERWRITE` — §1.1 boot-crash). Pin the
  dirty-store migration (old `agent` rows survive; the new column reads back `None` for them).

---

## FORK 1 — the mint mechanism (✅ OPERATOR RULED (A), 2026-08-24)

> **RULED (operator, 2026-08-24): mechanism (A) — an application-layer per-agent CAPABILITY.**
> The client-architecture premise below is now HIGH-confidence VERIFIED (a claude-code-guide
> research pass): **all subagents share ONE connection + ONE token** — `Mcp-Session-Id` is
> one-per-connection, server-assigned; **claude.ai hosted = ONE OAuth identity per user**. So
> per-agent identity CANNOT ride the transport → it MUST be app-layer. This is settled
> authority now, not a MEDIUM claim. The verification also noted **`lore_comms register` is
> ALREADY exactly this pattern** — an authenticated caller declares a `(session, name)` and the
> server mints a durable agent row — so (A) is an EXTENSION of an existing seam, not a new
> stack. The sibling-spoof residual of (A) (an injected agent misusing its OWN capability, not
> a sibling's) is ACCEPTED; cross-principal isolation is enforced by the transport token
> and holds. See Fork 2 for how the capability is delivered UNIFORMLY local+hosted (no sentinel).

This is the one non-trivial piece authorization-model §3.3/§10-O flagged for the contract
phase, and it carries a hard architectural constraint that is now VERIFIED, not conjectured.

**§3.3's preferred shape does not match how MCP clients connect.** §3.3 names as *"the likely
shape"*: *"each agent opens its own connection with its own short-lived minted token."* But
the vendor-level fact §3.3 itself states — *"MCP carries ONE bearer token per CONNECTION"* —
collides with reality:
- **Local (Claude Code):** every subagent in a session shares ONE `.mcp.json` entry and ONE
  connection to `http://127.0.0.1:9202/mcp`. Claude Code does not mint or present a distinct
  per-subagent MCP credential. (And today that connection carries no token at all.)
- **Hosted (claude.ai connector):** one user's connector = one OAuth identity = one principal;
  the user's agents all ride that one connection. claude.ai does not present per-subagent
  tokens either.

✅ **Confidence (RESOLVED 2026-08-24): the loopback fact and the register self-declaration are
HIGH (read from the tree). The claim "no current MCP client presents per-subagent transport
credentials" is now HIGH-VERIFIED too — a claude-code-guide research pass confirmed
`Mcp-Session-Id` is one-per-connection + server-assigned (all subagents share one connection +
one token) and claude.ai hosted is one OAuth identity per user. The fork's premise stands.**

**The consequence, stated plainly:** under the current client architecture the transport
bearer identifies the **PRINCIPAL**, and the **AGENT** within that principal cannot be carried
on the transport. So a *truly* server-bound, never-self-declared agent identity — §3.2.1's
letter, and §9's IN-scope *"an agent cannot present … as a sibling agent"* — is **not
achievable by riding the bearer token**. Something has to give, and it is the operator's call
which.

**THREE candidate mechanisms, graded against the constraint:**

- **(A) Register-time server-side owner stamp + per-agent CAPABILITY secret (application
  layer).** `register` (authenticated by the principal's transport token) mints the `owns`
  edge (`agent.owner_principal` from the credential) AND returns a one-time per-agent secret
  capability. Every subsequent governed call carries that secret; the server resolves
  `owner_agent` from secret→agent and `owner_principal` from the transport token. An injected
  SIBLING that never saw the secret cannot stamp as that agent.
  - *Prevents sibling-spoof* — at the application layer, without per-agent connections.
  - *Cost:* every governed call carries the capability; and the capability is only as strong
    as the agent's own context isolation — **a prompt-injected agent that controls its own
    context can read and misuse its OWN secret** (but not a sibling's it never saw). It is
    strictly better than a self-declared name and strictly weaker than a transport-bound token.
  - *This is the honest maximum achievable without client cooperation.*

- **(B) Accept within-principal agent as a self-declared LABEL; the security boundary is the
  PRINCIPAL.** The transport token binds the principal (server-side, unspoofable across
  principals). The agent name stays a within-principal label used for `agent-private` scoping
  and audit denormalization — NOT a cross-trust-domain boundary. Sibling-agent spoofing
  becomes an ACCEPTED BOUND, on the ground that **a principal's agents share that principal's
  trust domain** (which §9 already concedes for the injection-within-own-scope case: *"that is
  the agent's own trust domain"*).
  - *Prevents cross-principal spoof/read/write* — the isolation boundary the operator actually
    named (*"a user and their agents must not read another user's comms/memory"*) — fully.
  - *Does NOT prevent sibling-spoof* — contradicts §9's IN-scope clause as written. Requires
    the operator to move sibling-spoof from IN-scope to ACCEPTED-BOUND.
  - *Cost:* near-zero; matches the client reality exactly; no per-call capability.

- **(C) Per-agent transport token / per-agent connection (§3.3's literal shape).** REJECT as
  infeasible now: it requires the MCP client (Claude Code, claude.ai) to present a distinct
  minted token per subagent, which neither does and lore cannot force. Keep it as the
  documented "Version-B-of-identity" future option, gated on client support — the same shape
  as authorization-model §2.3's Version-A/Version-B split for enforcement.

**RULED: (A).** The operator chose the application-layer per-agent capability. The residual
sibling-spoof surface (an injected agent misusing its OWN capability, never a sibling's it
never saw) is ACCEPTED; the honest security gain of (A) over (B) — "an injected sibling cannot
use a DIFFERENT agent's identity" — was judged worth its per-call cost, and Fork 2's
real-local-principal ruling makes that cost UNIFORM (the capability rides the existing
`agent=`/register seam that already exists, local and hosted alike, with no sentinel branch).
The PRINCIPAL binding is server-side and cross-principal isolation holds under (A) — never in
question. (B) is NOT adopted; §9's sibling-anti-spoof stays IN-scope, met by (A) modulo the
own-capability residual named above.

**RIDERS — and pin/measure/verify each like this (whichever mechanism is ruled):**
- **R1.1 — the owner stamp is ONE server-derived function, proven by MUTATION (§11 DRY).**
  There is ONE `stamp_owner(access_token, agent_capability) -> (owner_principal, owner_agent)`
  seam (recommend it lives in `lorerunes` — the shared home — since both the verifier side and
  the governed-store side read it). Move the derivation; every governed write's owner-stamp
  pin must red (ROUTING-IS-NOT-SHARING). A caller that hand-derives owner is a private copy.
- **R1.2 — the dedicated security-auditor pass attacks EXACTLY the ruled mechanism (§10-O).**
  Name for the auditor: for (A) — steal/replay a capability; present a sibling's capability;
  present a valid capability with a MISMATCHED transport principal (must reject); capability
  after agent retire/revoke; capability leak in a rendered surface. For (B) — prove the
  cross-principal boundary holds under every self-declared agent name (A's agents naming
  themselves as B's agents must not cross into B's principal set). BOTH: fuzz every write with
  hostile `owner=`/`as_agent=`/`created_by=`/`scope=server` (§3.2.2) → stamp unchanged.
- **R1.3 — short-lived is a FACT, not a disclaimer (trust doctrine).** If the mechanism mints
  anything with a lifetime, pin the expiry is enforced on read (mirror `token_verifier.py`'s
  `_absolute_expiry` + positive-cache re-check) and a revoked/expired capability is refused —
  with a negative control (a live one is accepted). "Short-lived" with nothing measuring the
  bound is a hope (packet-03b rider law).
- **R1.4 — `agent_of(access_token)` fail-closed is LOAD-BEARING and already documented.**
  `token_verifier.py::agent_of` returns `None` for unbound/absent and its docstring instructs
  packet 62: *"an agent-SCOPED operation … must treat None as DENY … never as 'any agent'."*
  Pin: an agent-private authorization with `agent_id` unresolved DENIES (no agent → no agent
  authority), never wildcards. This is the §3.2.1 fail-closed carried from 39-W1 (sidecar E3).

---

## FORK 2 — the local-fleet identity crux (✅ OPERATOR RULED: real local principal via api-key)

> **RULED (operator, 2026-08-24): REAL LOCAL PRINCIPAL VIA API-KEY — the sentinel is
> OVERRIDDEN and RETIRED.** The local `.mcp.json` will present a packet-49 api-key
> (`name:secret`) as its bearer, so the local fleet authenticates as the operator's REAL
> principal — NOT a synthetic sentinel, and NOT the current no-auth loopback. Option (A) then
> applies UNIFORMLY, local and hosted, with NO sentinel/no-credential branch. My original
> sentinel recommendation (former R2.1/R2.3) is WITHDRAWN.

**The problem this answers:** 63/64 stamp `owner_principal`+`owner_agent` on EVERY governed
write; the pre-ruling LOOPBACK path had NO credential (Fork-0 fact 1), so there was nothing to
stamp. The operator's answer is not "invent a sentinel to stamp" — it is "give the local path a
REAL credential," which is strictly better: the local fleet's owner is a genuine principal, so
there is one owner-derivation path everywhere and the whole sentinel apparatus disappears.

**Working the operator's four sub-questions (a)–(d):**

**(a) Does this SIMPLIFY option A by dropping the no-credential/sentinel branch entirely? —
YES, materially.** With an api-key on the wire, the api-key branch of `LoreTokenVerifier`
(`token_verifier.py` — `PrincipalKeyStore.verify(<name>:<secret>) → KeyVerification(principal,
key_name)`, #206) resolves a REAL principal on EVERY local call, so `get_access_token()` is
never `None` on the served path. Consequences:
- `stamp_owner(access_token, agent_capability)` (R1.1) has **ONE path**: `owner_principal` from
  the credential (always present), `owner_agent` from the per-agent capability. No posture
  branch, no sentinel constant, no NULL-owner-for-a-live-write special case.
- The local fleet's shared behavior is PRESERVED and now CORRECT-by-model: all local agents
  present the operator's ONE api-key → ONE principal → `principal-private` = "the operator + the
  operator's agents" = exactly the §3.1 trust unit (this IS today's shared fleet, now named
  honestly rather than approximated by a sentinel). Agents within are distinguished by the
  per-agent capability (option A), uniform with hosted.
- Migration (§7) is cleaner: NULL `owner_principal` now unambiguously means "genuinely-legacy
  pre-retrofit row," never "a new loopback write" — the two populations never collide.

**(b) What the packet-65 JOINT CUTOVER must provision (a DEPLOY obligation, NOT a 62-build
task):**
1. **The operator's principal exists** (`lore-adm add --email <operator> [--role …]`, packet
   49). ⚠ Role choice is a DEPLOY decision with the §9 weight: `admin` = full unrestricted
   superuser (total-store-compromise if the key leaks); `member` + ownership gives full write to
   the operator's OWN rows, which is what the local dev fleet needs. **Recommend `member`** for
   the local-fleet key unless the operator needs cross-principal admin locally; flag it for the
   deploy owner, do not hard-code it.
2. **Mint the api-key** (`lore-adm mint-key --email <operator> --name <local-fleet-key>` →
   prints `name:secret` ONCE — packet 49; `principals.py::_cmd_mint_key`).
3. **Reconfigure the local `.mcp.json`** to present that credential as the bearer
   (`Authorization: Bearer <name>:<secret>` on the http transport).
4. **Flip the deployed posture** from `LOOPBACK` (auth disabled) to the api-key posture
   (`auth.enabled=true`, `auth.mode="api_key"` → `Posture.LAN_BEARER`) in the deployed
   `lore.yaml`.
This is entirely packet-65's cutover provisioning. **62's build provisions NONE of it** — 62
builds the mechanism that CONSUMES a credential; 65 supplies the credential + flips the client
+ flips the posture. The contract author gets this as an explicit non-obligation (see the scope
line at the end).

**(c) Where does TIGHTENING §8's LOOPBACK "no-auth, full-write" interim belong? — packet 65's
DEPLOY, and it creates a real cross-packet dependency to flag.**
- **posture.py / `derive_posture` (packet 39): UNCHANGED.** Both `LOOPBACK` and `LAN_BEARER`
  remain valid supported postures; the tightening is not a code retirement, it is the local
  fleet CHOOSING `LAN_BEARER` over `LOOPBACK` via config. `LOOPBACK` stays legal for a genuine
  single-user no-auth deploy — do NOT delete it from the enum.
- **packet 62: builds against the credentialed path and adds NO no-credential fallback.** A
  governed write with no resolvable credential is fail-closed (consistent with `agent_of`'s
  `None`=DENY, R1.4) — but that state cannot arise on the served fleet, because 65 flips the
  posture to api-key in the SAME cutover that serves 62's code.
- **⚠ THE CROSS-PACKET BOUNDARY TO FLAG:** 62's served correctness DEPENDS on 65 having flipped
  the local posture to api-key. If 65 shipped 62's code but left the posture at no-auth (or
  provisioned no key / a stale `.mcp.json`), the local fleet's governed writes would hit
  fail-closed and lock the fleet out. So **65's cutover must land CODE + POSTURE-FLIP + KEY-MINT
  + `.mcp.json` reconfig ATOMICALLY (all-or-nothing)** — this is a new §8 joint-cutover rider,
  the same "no useless interim in production" discipline §8 already states, extended to the
  local path. Packet 65 owns it; 62 and the contract author only NAME the dependency.
- **The tightening of `.well-known` / networked posture for the HOSTED path** is packet 39's
  already-shipped posture machinery — untouched here.

**(d) Removed-behavior inventory for retiring the LOOPBACK no-auth path:** added as **I5** to
the I1–I4 table below.

**⚠ NOTHING BREAKS MID-DEVELOPMENT — say this to the contract author explicitly.** Packets
62/63/64 are COMMIT-ONLY and UNSERVED until the packet-65 cutover. The pre-cutover local fleet
keeps running against the CURRENTLY-DEPLOYED no-auth image — so no in-flight development session
loses its lore access, and **62's build must NOT try to reconfigure, re-auth, or restart the
live fleet.** The api-key/posture flip is a single atomic deploy event at 65, not a gradual
migration the build participates in.

**RIDERS — and pin/verify like this (post-ruling):**
- **R2.1 (REPLACES the withdrawn sentinel rider) — `stamp_owner` has ONE credentialed path;
  prove it by MUTATION and pin fail-closed-on-absent-credential.** No posture branch in the
  owner derivation. Pin: a governed-write path with a resolvable principal stamps
  `owner_principal` = that principal (positive control: local api-key principal AND a hosted
  Google principal both stamp their own, via the ONE seam); a path with NO resolvable
  credential DENIES (fail-closed), never stamps a default/sentinel/NULL-as-live.
- **R2.2 (KEPT) — cross-principal isolation pinned with ≥2 principals × ≥2 agents (§11).**
  Principal-A's drain/query/recall never returns principal-B's private rows, proven over the
  wire with a hostile 2×2 fixture. This is the boundary that actually matters and it is
  NON-negotiable — and it now applies to the LOCAL path too (two api-key principals on one box
  must not read each other), not only hosted.
- **R2.3 (REPLACES the withdrawn loopback-bound pin) — pin that the local fleet's shared
  behavior SURVIVES the api-key cutover.** A dirty-store / integration pin: the operator's ONE
  api-key principal, presented by N local agents, yields the today-equivalent shared view
  (`principal-private` rows visible across the operator's own agents). This is the "removed-
  behavior dual" (CLAUDE.md P8d): the rewrite must not silently break the working local-fleet
  sharing the no-auth path gave for free.

---

## FORK 4 — the 62↔63 boundary (ruled; crisp scope line for the contract author)

**RECOMMENDATION (not MAJOR):** 62 lands the identity MECHANISM + the anti-injection
INVARIANTS **as a mechanism plus a coverage-as-checked-variable pin (reach law #344/#345)**;
63/64 satisfy the invariants PER-TOOL as they retrofit each governed store. 62 does NOT fuzz
tools whose owner/scope columns 63/64 have not yet added — it CANNOT (there is nothing to
stamp yet on those tables).

**The crisp scope line — 62 OWNS:**
1. The `owns` edge (`agent.owner_principal`) + its DDL/index/migration (Fork 3).
2. The register-time server-side owner stamp + the `Subject`-from-credential constructor + the
   ruled mint mechanism (Fork 1) + `agent_of` fail-closed resolution.
3. The ONE `stamp_owner(...)` seam (R1.1) — the shared owner-derivation function 63/64 CALL.
4. The anti-injection invariant AS A REACH PIN: a test that ENUMERATES the governed surface
   (derived from `partition_tools_by_population`, the 61 registry — NEVER a hand-list) and
   asserts, for each governed write tool, that (a) it derives owner via the shared seam, and
   (b) it rejects/ignores hostile `owner=`/`as_agent=`/`created_by=`/`scope=server` args. **At
   62 HEAD this pin's per-tool leg is RED_ADJUDICATED for tools not yet retrofitted** (owned,
   with the trigger "63/64 retrofits tool X") — the reach set GROWS as 63/64 wire each tool,
   and the pin goes green tool-by-tool. This is the reach law's *"coverage as a checked
   variable"*: a new governed tool that bypasses the seam reds it.
5. Fuzz + owner-stamp pins for the tool(s) 62 ITSELF wires (`lore_comms register` — the
   `owns`-mint — plus any surface 62 must touch to construct the Subject).

**63/64 OWN:** the `owner_principal`+`owner_agent`+`scope` COLUMNS on each governed table
(comms/memory/tasks/findings), the PDP routing of each verb, the per-tool fuzz + owner-stamp
pin (turning its reach-pin leg green), and the §7 dirty-store row migration.

**WHY this split (not "62 fuzzes only what it can" as a silent narrowing):** the invariant is
ONE property over a SET that grows across packets. Landing it as a hand-list of "tools 62 could
reach" is the switched-off-scanner antipattern (CLAUDE.md instrument lesson) — the forbidden
set is unbounded. Landing it as a DERIVED reach pin with adjudicated per-tool RED means the
day 63 adds a governed tool and forgets the seam, the pin reds with nobody's name on the new
row → RED_ORPHANED → currency gate fails. That is the reach law working as designed across a
packet boundary.

**RIDERS — and pin/verify like this:**
- **R4.1 — the reach set is DERIVED from the 61 registry, and a test reds when it GROWS but
  the observed (seam-routed) set does not** (reach law askable form, INSTRUMENT-0). Not a
  count, not a name-list — a set difference. Cite `partition_tools_by_population` as the source
  of truth for "governed."
- **R4.2 — every 62 pending-contract RED is ADJUDICATED (owner + trigger), never orphaned**
  (`scripts/pending_contracts.yaml`; currency gate `scripts/pending_contract_gate.py
  --currency`). The per-tool legs 63/64 will satisfy are RED_ADJUDICATED with trigger "packet
  63/64 retrofits <tool>" — required at 62's wave close-out.
- **R4.3 — 62's own wired tools are GREEN, mutation-proven, at 62 close** (not adjudicated-red)
  — the `owns` mint + `stamp_owner` seam + `agent_of` resolution ship working and pinned,
  because 62 CAN fully build them. Only the not-yet-retrofitted governed tables' legs are red.

---

## OPERATOR RULINGS (2026-08-24) — all four forks decided

All four forks were escalated and RULED by the operator; this section records the outcomes so
the contract author reads decisions, not open questions.

- **FORK 1 — RULED (A):** application-layer per-agent capability. The client-architecture
  premise (no per-subagent transport credential) is HIGH-confidence VERIFIED (claude-code-guide
  research: `Mcp-Session-Id` one-per-connection + server-assigned; claude.ai = one OAuth per
  user; `lore_comms register` is already this pattern). §9 sibling-anti-spoof stays IN-scope,
  met by (A) modulo the accepted own-capability residual. See Fork 1.
- **FORK 2 — RULED: real local principal via api-key (operator OVERRODE the sentinel).** The
  local `.mcp.json` presents a packet-49 api-key so the local fleet is the operator's REAL
  principal; (A) applies uniformly local+hosted, no sentinel branch. The §8-tightening + key
  provisioning + `.mcp.json` reconfig is a packet-65 DEPLOY obligation (not a 62-build task); the
  atomic cutover is a new §8 rider. See Fork 2 (a)–(d).
- **FORK 3 — RATIFIED:** scalar `agent.owner_principal` field-link; principal-delete
  DANGLE-tolerated for owned agents (R3.2). Riders R3.1/R3.3/R3.4 stand.
- **FORK 4 — RATIFIED:** anti-injection as a DERIVED reach pin across the 62↔63 boundary
  (R4.1–R4.3).

Nothing remains open for the contract phase to escalate; genuine spec ambiguities found DURING
contracting still escalate per standing law.

---

## Removed-behavior inventory — two retirements (the 48 non-wiring guard + the LOOPBACK no-auth path)

Packet 48's `principals.py` docstring (lines 13–31) is STANDING LAW that `principal` is a
THIRD DISTINCT identity vocabulary that *"must NEVER be conflated"* with (1) ledger-actor
strings (`created_by`/`actor`/`owner`) and (2) the comms `agent` table. Packet 62 retires the
*non-wiring* half DELIBERATELY (I1–I4). Fork 2's operator override additionally retires the
LOOPBACK no-auth local path (I5, a §8/deploy concern, not a packet-48 concern — kept in one
table per the directive). The inventory (adjudicated item-by-item, per the delete/replace
removed-behavior law — CLAUDE.md P8d dual):

| # | behavior the guard protected | 62's disposition | adjudication |
|---|---|---|---|
| I1 | `principal` and comms `agent` are UNLINKED (no edge between them) | **RETIRED** — 62 adds `agent.owner_principal : record<principal>` (the `owns` edge, Fork 3) | **dropped-deliberately** — this IS the mission (authorization-model §3.1: *"Authorization needs them linked"*). The link is a graph edge between two DISTINCT nodes; it does NOT merge their vocabularies. |
| I2 | `principal.role/status` never wired to the `agent.role/status` tuples (different closed domains) | **PRESERVED** | **preserved-with-pin** — the `owns` edge relates NODES; it touches neither table's role/status columns. Pin: `agent` keeps `_AGENT_STATUS_ALLOWED`, `principal` keeps `_PRINCIPAL_STATUSES`; no cross-wiring (the one-column-one-identity law, `server.py` `_TRACE_DECLARED_KEYS` neighbourhood, survives). |
| I3 | ledger-actor strings (`created_by`/`actor`/`owner`) NOT retrofitted to `principal` FKs | **PRESERVED for legacy free-text; SUPERSEDED for NEW governed writes** | **spec-silent → follows authorization-model §3.2.2 + §7.** NEW governed rows get server-stamped `owner_principal`/`owner_agent` (63/64 columns), NOT a `created_by` FK on `principal`. EXISTING free-text `created_by` stays a display/audit string (61a-w4 audit store already denormalizes `actor_email`/`actor_agent_name` for exactly this). The free-text field is not promoted to an authz input — §3.2.2 makes authz owner server-derived, not the old string. |
| I4 | THREE `record<principal>` links EXIST at HEAD (`principal_key.principal`, `keep.keeper`, `audit.actor_principal` [61a-w4, dangle-tolerated]); `PrincipalStore.delete` ACTS ON two (cascade + refuse) | **EXTENDED** — 62 adds `agent.owner_principal` as the **FOURTH** existing link (RULED dangle-tolerated, so delete's acts-on set stays two) | **preserved-with-pin (R3.1/R3.2)** — count re-derived 2026-08-24 (grep of `record<{PRINCIPAL_TABLE}>` specs); the exact-set pin in `test_principal_keys_schema.py` reds until `agent.owner_principal` is added as the FOURTH and adjudicated DANGLE. ⚠ the delete docstring (`principals.py:662`) still says "TWO" — stale since 61a-w4 (P8d class); builder corrects it (R3.1). Delete's forward-scope warning DISCHARGED by this packet. |
| I5 | the LOCAL fleet runs under `Posture.LOOPBACK` — auth DISABLED, no credential, full-write (§8 interim, "keep current behavior") | **RETIRED as the local RUNTIME posture** (operator override, Fork 2) — the local fleet moves to api-key auth (`Posture.LAN_BEARER`); the `LOOPBACK` posture itself STAYS supported in `posture.py` for a genuine no-auth deploy | **dropped-deliberately (deploy-owned).** The retirement is a packet-65 CONFIG flip (auth.enabled/mode + `.mcp.json` + key mint), NOT a `posture.py`/62 code deletion. Preserved: `Posture.LOOPBACK` remains valid + tested. Pin (R2.3): the local fleet's shared-view behavior SURVIVES the cutover. ⚠ Cross-packet: 62's served correctness DEPENDS on 65's atomic flip — a code-without-posture-flip cutover locks the fleet out (fail-closed). The pre-cutover fleet keeps running the old no-auth image (62/63/64 unserved until 65), so nothing breaks mid-development. |

**The guard's DOCSTRING itself must be edited, not just the code** (P8d rendered-prose law: a
rename/reshape's natural-language surface is where green-at-gate defects hide). The
`principals.py` docstring lines 13–31 currently teach *"48's docstring forbids wiring them"* —
after 62 that is FALSE for the `owns` edge. Rider: the docstring is updated to say `principal`
and `agent` are DISTINCT vocabularies that are now RELATED by an `owns` edge (nodes linked,
vocabularies still not conflated — I1/I2), and a bare-pattern grep sweep for the retired
"forbids wiring"/"deliberately unlinked" prose (in principals.py, the authorization-model doc,
and any test asserting the non-link) is a REQUIRED 62 close-out step — *"tests written before
a semantic change certify the OLD world."*

---

## What the contract / adversary / security-auditor must pin (roll-up)

Consolidating the riders (each is a *"and pin it like this"* clause the contract author may
NOT drop — the rider IS the ruling):
- **§5 single-brain untouched:** 62 changes WHO constructs the `Subject`, not the PDP. Pin that
  `authorize`/`authorize_filter` are unchanged and the 61 live-store oracle still holds with a
  62-constructed Subject.
- **Owner-stamp is ONE server-derived seam (R1.1),** mutation-proven; identity/owner NEVER from
  a tool argument (R1.2 fuzz).
- **Mechanism (A) gets the DEDICATED security-auditor pass (§10-O)** with the attack list in
  R1.2/R1.3 (capability replay/steal/mismatched-principal/post-revoke/render-leak);
  `agent_of` fail-closed (R1.4).
- **`owns` edge shape + DDL + dirty-store migration (R3.1–R3.4);** principal-delete cascade +
  exact-set pin discharged, DANGLE-tolerated (R3.1/R3.2).
- **`stamp_owner` has ONE credentialed path, mutation-proven; fail-closed on absent credential
  (R2.1).** Cross-principal isolation over the wire, 2×2 fixture — now local (two api-key
  principals) AND hosted (R2.2). Local shared-view survives the api-key cutover (R2.3).
- **Anti-injection invariant as a DERIVED reach pin across the 62↔63 boundary (R4.1),** every
  RED adjudicated with owner+trigger (R4.2), 62's own tools green + mutation-proven (R4.3).
- **Removed-behavior inventory I1–I5 each adjudicated;** the retired-prose grep sweep (48
  non-wiring guard) is a close-out step; the I5 LOOPBACK retirement is a packet-65 deploy flag,
  not a 62 build task.

---

## FINAL PACKET-62 SCOPE LINE (for the contract author)

**Packet 62 BUILDS (commit-only, unserved until the packet-65 cutover):**
1. `agent.owner_principal : option<record<principal>>` field-link + its `IF NOT EXISTS` index —
   the `owns` edge (Fork 3), `DEFINE FIELD OVERWRITE`, dirty-store migration pinned (R3.4).
2. The register-time server-side owner stamp: `AgentRegistry.register` sets
   `agent.owner_principal` from the AUTHENTICATED credential (`get_access_token()`), never an
   argument (R3.3), with the per-agent CAPABILITY of mechanism (A) minted here (Fork 1) —
   `lore_comms register` is the natural home (it is already this pattern).
3. The ONE shared `stamp_owner(access_token, agent_capability) -> (owner_principal, owner_agent)`
   seam in `lorerunes` (R1.1), mutation-proven, fail-closed on absent credential (R2.1); and the
   `agent_of` resolution filled in `token_verifier.py` (was `None`), fail-closed None=DENY (R1.4).
4. `PrincipalStore.delete`: `agent.owner_principal` added as the **FOURTH** existing
   `record<principal>` link (the three existing: `principal_key.principal`, `keep.keeper`,
   `audit.actor_principal`), RULED DANGLE-tolerated for owned agents (delete's acts-on set stays
   two); the `test_principal_keys_schema.py` exact-set pin discharged, and the delete docstring's
   stale "TWO" count corrected (R3.1/R3.2, I4).
5. The anti-injection invariant as a DERIVED reach pin over the governed surface
   (`partition_tools_by_population`), per-tool legs RED_ADJUDICATED for tools 63/64 has not yet
   retrofitted (R4.1–R4.3, Fork 4); fuzz + owner-stamp pins for the tool(s) 62 itself wires.
6. Docstring/prose updates retiring the 48 non-wiring guard (I1–I2) + the retired-prose grep
   sweep as a close-out step.

**Packet 62 does NOT (explicit non-obligations):**
- add `owner_principal`/`owner_agent`/`scope` COLUMNS to comms/memory/tasks/findings, route their
  verbs through the PDP, or migrate their rows — that is **63/64**.
- provision the operator principal, mint the api-key, edit `.mcp.json`, or flip the deployed
  posture — that is **packet-65's deploy cutover** (Fork 2 (b)/(c)).
- reconfigure, re-auth, or restart the LIVE local fleet — it keeps running the currently-deployed
  no-auth image until the atomic 65 cutover (Fork 2 note).

---

*All four forks are operator-RULED (2026-08-24): Fork 1 = mechanism (A), premise HIGH-verified;
Fork 2 = real local principal via api-key (sentinel overridden); Forks 3 & 4 ratified. The
security-auditor is the arbiter of mechanism (A) (§10-O). This doc consumes 39/48/49/60/61 as
CODE-COMPLETE and touches no code — I am the designer.*

---
---

# WAVE-2 ADDENDUM (2026-08-24) — the concrete capability mechanism

Wave 1 (the `agent.owner_principal` store foundation) is GO + committed (`3c94ffd`). This
addendum rules the CONCRETE shape of Fork-1's mechanism (A) — the per-agent capability — before
the wave-2 contract. It answers the lead's five consult items (`lore_comms #7027`), each with
its security-auditor attack surface (R1.2). Grounded in a read of `principal_keys.py`
(`PrincipalKeyStore` — the packet-49 credential precedent) this session.

## W2.0 — THE CRUX (item 1): a capability is a VERIFIED CREDENTIAL, not a spoofable CLAIM

**ANSWERED: the credential-vs-claim distinction is SOUND and SUFFICIENT.** §3.2.2 forbids
authz-bearing arguments because an argument like `owner=alice` is an **unverified assertion the
server would have to TRUST** — the confused deputy. A `capability` secret is categorically
different: it is a **bearer credential the server VERIFIES** (constant-time-ish UNIQUE-hash
lookup over a preimage-resistant `sha512_hex` digest — `principal_keys.py:492` `verify`),
unforgeable without the secret. The server never TRUSTS the argument's asserted identity; it
derives identity from the **verification RESULT**. That is the same construction as the transport
bearer token itself — a secret presented in a header, verified, not trusted — and as the packet-49
api-key `name:secret`, which is ALREADY a credential-presented-as-a-value and which nobody calls a
confused deputy. **PROOF-BY-PRECEDENT: `PrincipalKeyStore.verify` is this exact pattern, shipped
and audited.** The only difference wave-2 introduces is the CHANNEL: because all subagents share
ONE connection + ONE transport token (the HIGH-verified constraint), the per-agent credential
cannot ride a per-connection header, so it rides the **only per-call channel a subagent controls
— a tool argument.** The channel changes; the credential-not-claim nature does not.

**⚠ SF-1 (sub-fork — CONFIRM; touches §3.2.2's letter).** §3.2.2 as written says
*"identity/owner … NEVER from a tool argument."* The precise, correct reading under mechanism (A)
is: **never from an UNVERIFIED tool argument (a claim); a VERIFIED credential argument is
admissible, because identity is taken from the verification result, not the asserted value.** The
owner STAMP still never comes from a raw `owner=`/`as_agent=`/`created_by=`/`scope=server` claim —
those remain forbidden as authz inputs (display-only, sanitised, no authority). This refinement
is the necessary consequence of the operator's own (A) + `name:secret` ruling given the verified
shared-transport fact, so I RECORD it as derived rather than escalate it — but it edits the letter
of an operator-stated invariant, so it is flagged for the operator to VETO. Recommendation:
adopt the refined reading; it is what makes (A) expressible at all.

## W2.1 — presentation (item 1): `name:secret`, verified, on every governed call

**RULED: the capability is a `<name>:<secret>` string presented as a dedicated argument on every
governed call, verified server-side before the owner stamp.** Mirror the packet-49 wire format
exactly (`principal_keys.py` §WIRE FORMAT: presented `<name>:<secret>`, stored hash
`sha512_hex(f"{name}:{secret}")` of the WHOLE string). Two presentation shapes were considered;
the ruling is a DEDICATED argument, not overloading the existing `agent=` name param:
- **Dedicated `capability=<name:secret>` argument** (RULED) — keeps the credential separate from
  the display `agent=<name>` (which stays a sanitised, no-authority label). The verified
  capability determines `owner_agent`; the display `agent=` never does.
- *Overloading `agent=` to carry `name:secret`* (REJECTED) — the `agent` name is used in renders,
  dedup and routing; mixing a secret into it risks the secret leaking into a rendered surface (a
  §F3a-class credential-in-a-log defect) and conflates a display label with a credential.

**Auditor attack surface (W2.1):** fuzz every governed write with hostile
`owner=`/`as_agent=`/`created_by=`/`scope=server` → the stamped `(owner_principal, owner_agent)`
is UNCHANGED (from the verified capability + transport token). Present a valid capability with a
mismatched display `agent=<other>` → `owner_agent` follows the CAPABILITY, not the display name.
Present NO capability on a governed write → fail-closed DENY (W2.4).

## W2.2 — storage + verify (item 2): a `capability_hash` field on `agent`, shared parse/hash

**RULED: store the capability as `agent.capability_hash : option<string>` (UNIQUE index) — a
field on the existing `agent` row — NOT a new `AgentCapabilityStore` and NOT an extension of
`PrincipalKeyStore`.** Rationale (packages/DRY + minimal surface):
- **1:1 cardinality.** An agent has exactly ONE live capability; `principal_key` is 1:many
  (a principal holds many keys), which is why IT is a separate table. A 1:1 credential is a
  FIELD on the owning row, not a child table.
- **Minimal surface + atomic mint.** `register`'s create branch (`agents.py:650`, the
  `existing_row is None` path) already `CREATE`s the agent row; minting `capability_hash` in the
  SAME `CONTENT` is one atomic write, no new store, no new connection-owner clone (a whole `~250`-line
  clone is what a separate store costs — `principal_keys.py` cloned it verbatim).
- **The binding check is FREE.** `verify` needs `agent.owner_principal` (Fork 3) for the
  `(principal, agent)` binding — it lives on the SAME row, so one indexed SELECT returns
  `capability_hash` + `status` + `owner_principal` together.
- **The retry seam is already covered.** `AgentRegistry._query` is auto-discovered by
  `test_retry_seam.py`; verify rides it — no new seam to enroll.
- **Extending `PrincipalKeyStore`** (REJECTED) — overloads a principal-bound table with an
  agent-bound credential; one-column-one-identity violation (the same law `principals.py:13–31`
  states for role/status).

**DRY (the shared POLICY that MUST agree — ONE IMPLEMENTATION):** the wire-format PARSE and the
HASH must be identical to `PrincipalKeyStore`'s, or a credential minted one way won't verify the
other and the two drift. Concretely:
- **Extract `lorerunes.parse_credential(presented) -> tuple[str, str] | None`** (the
  `is_blank` reject → `partition(":")` → blank-half reject sequence, currently inline at
  `principal_keys.py:519–525`) and have BOTH verifies call it. Prove by mutation: change the
  parse (e.g. partition on LAST colon), and BOTH stores' verify pins red.
- **The hash stays `sha512_hex`** (already shared, `loremaster.index.records`) — never a
  hand-rolled `hashlib` clone (#102/#120).
- **The no-oracle uniform-deny + NO-CACHE discipline** (verify returns `None` on every failure,
  laundered DEBUG reason, re-checked every call — `principal_keys.py:492`, R12) is a DISCIPLINE
  pinned in both, not a shared skeleton (the admission conditions differ, so a forced shared
  skeleton over differing logic would be worse than the pinned discipline).

`agent.capability_hash` is a NEW field on the POPULATED `agent` table → `DEFINE FIELD OVERWRITE`,
type `option<string>` (store-ref §1.4: a new required field poisons existing rows), UNIQUE index
`IF NOT EXISTS` (store-ref §1.1). Dirty-store migration pinned (old agent rows read `None`).

**verify_capability admission conditions** (re-evaluated every call, one `now`, mirroring
`principal_keys.py:497–503`): (1) `capability_hash` matches (UNIQUE lookup); (2) the agent is
NOT `retired` (`agent.status`); (3) **the binding: `agent.owner_principal` == the transport
token's principal** (the load-bearing (principal, agent) check); (4) the owning principal is
`active` + unexpired (transitive, via `owner_principal`). Any failure → uniform `None` → DENY.

**Auditor attack surface (W2.2):** forge a capability without the secret → no hash match →
uniform deny (preimage resistance). Timing/enumeration oracle → UNIQUE-hash-index lookup gives
uniform timing + no name-existence oracle (pkt-49 precedent). Injection via the presented string
→ bound `$h` param, never interpolated. **Cross-principal capability replay — present agent-A's
valid capability under principal-B's transport token → condition (3) DENIES** (this is the pin
that makes a leaked capability useless to anyone but its owner). Retired-agent capability →
condition (2) denies.

## W2.3 — mint + lifetime + revocation (item 3)

**Mint (RULED):** `register`'s create branch mints the secret (`secrets.token_urlsafe(32)` — the
pkt-49 entropy, `principals.py:_SECRET_ENTROPY_BYTES`), stores `capability_hash =
sha512_hex(f"{name}:{secret}")`, and returns the raw `<name>:<secret>` **ONCE** in the register
result (the store never persists the raw secret — pkt-49 discipline). **Mint-once-on-create:**
re-register (the idempotent `else` branch, `agents.py:680+`) does NOT rotate the secret (a
running agent already holds it; rotating would break it mid-session). This is consistent with
fleet law "names are never reused" — a respawn is a fresh name → fresh register → fresh mint.

**⚠ SF-2 (sub-fork — CONFIRM; reinterprets R1.3 "short-lived is a FACT"). Lifetime RULED
(recommended): AGENT-LIFECYCLE-scoped — valid while the agent is not retired/revoked; NO clock
TTL.** Rationale: R1.3's "short-lived limits the leak window" is SUBSUMED by the binding check
(W2.2 condition 3) — a leaked capability is **useless without the owner's transport token**
(Google OAuth / api-key), which is the dominant credential; so an independent clock TTL buys
little and forces a refresh mechanism (pure surface) that would break long agent sessions. An
OPTIONAL `capability_expires_at : option<datetime>` seam is provided for defense-in-depth (mirrors
`principal_key.expires_at`), defaulting to never; if the operator wants a clock TTL, it is the
`_absolute_expiry`-style re-check on the same field. **Flagged for operator confirm; the
security-auditor is the arbiter.** Recommendation: lifecycle-scoped + the optional-expiry seam.

**Revocation (RULED):** NO CACHE — verify re-checks the live row every call (pkt-49 R12), so
revocation beats any residual window. A capability is revoked by (a) the agent being `retired`
(condition 2 denies on the NEXT call), or (b) an explicit clear of `capability_hash` (a
revoke path / admin verb — recommend a thin `lore-adm`/registry verb mirroring
`PrincipalKeyStore.revoke`). Pin: retire/revoke the agent → the very next governed call with the
old capability DENIES (no residual window).

**Auditor attack surface (W2.3):** unauthenticated `register` mints an owned agent → register
must read the principal from the transport token (fail-closed if absent; pre-cutover unserved).
Re-register rotates a sibling's live secret → mint-once-on-create pin. Revoked/retired capability
still works → no-cache next-call-denies pin. (If SF-2 → clock TTL: expired capability served past
expiry → `_absolute_expiry` re-check pin; moot if lifecycle-scoped.)

## W2.4 — `agent_of` / `resolve_agent` (item 4): the seam RELOCATES

**⚠ SF-3 (a refinement, NOT a fork — but the contract author MUST have it crisp).** The 39-W1
`agent_of(access_token)` seam (`token_verifier.py:160`) reads `claims["agent"]` — it was shaped
on the ASSUMPTION of a token-borne agent (the "minted (principal, agent) token" shape §3.3
imagined). The HIGH-verified fact kills that assumption: **the agent is NEVER in the transport
token** (the token is the PRINCIPAL's; the capability arrives per-call as an argument). Therefore:
- **`agent_of(access_token)` correctly stays `None` — it is not "filled".** The transport token
  genuinely carries no agent. Keep it (its fail-closed None=DENY doc is still right for a
  token-borne agent, which is always absent); update its docstring to say so under the
  capability model. Do NOT stuff an agent into the token.
- **The REAL per-call resolver is a NEW seam: `resolve_agent(presented_capability, access_token,
  registry) -> agent_id | None`** (living in `AgentRegistry` as `verify_capability`), fail-closed
  `None`=DENY (R1.4's semantics MOVE here). `stamp_owner` calls it: `owner_principal` from the
  token, `owner_agent` from `resolve_agent`. A `None` from `resolve_agent` (absent/garbage/
  unverified/binding-mismatch capability) DENIES an agent-scoped write — never "any agent".

**Auditor attack surface (W2.4):** absent/garbage capability treated as wildcard → fail-closed
DENY pin. `agent_of(token)` returns a stale/other agent → pin it stays `None`. `resolve_agent`
returns an agent whose `owner_principal` ≠ the token principal → binding pin (W2.2 cond. 3).

## W2.5 — wave scope (item 5): ONE wave (mechanism + its security pins + prose)

**RULED: ONE wave-2.** The field + mint-in-register + `verify_capability`/`resolve_agent` +
`stamp_owner` + `parse_credential` extraction are ONE tightly-coupled mechanism; splitting
store-from-verify ships a half-mechanism nothing exercises, and **splitting the security pins
from the mechanism ships an UNVERIFIED mechanism — forbidden by the trust doctrine** (a mechanism
must ship WITH its adversary pins). So the mechanism, its fuzz/binding/replay/revocation pins, and
the prose ride ONE wave. The 63/64 **per-tool** reach legs (Fork 4) stay RED_ADJUDICATED — that
is the cross-packet boundary, not a wave-2 split. If sizing forces a split, the ONLY sound seam is
**2a = the credential mechanism + ALL its security pins** (never mechanism-without-pins) and
**2b = `stamp_owner` wiring into the tool(s) 62 owns + the reach pin + prose**; I recommend NOT
splitting (stamp_owner is small and is the point).

## W2.6 — DRY ledger + riders (each a "and pin it like this" clause)

- **DRY:** `parse_credential` extracted to `lorerunes`, shared by both verifies (mutation-proven);
  `sha512_hex` reused (not cloned); `secrets.token_urlsafe(32)` entropy reused; the
  connection-owner/`_query` retry seam reused (AgentRegistry's, not a new store). One
  owner-derivation seam `stamp_owner` (R1.1).
- **W2-R1 (SF-1) — the §3.2.2 fuzz is the load-bearing pin:** every governed write, hostile
  `owner=`/`as_agent=`/`created_by=`/`scope=server` → stamp unchanged; only the VERIFIED
  capability moves `owner_agent`. Mutation-prove `stamp_owner`.
- **W2-R2 — the binding pin (W2.2 cond. 3):** agent-A's valid capability under principal-B's token
  → DENY. This is what makes the accepted own-capability residual (Fork 1) the ONLY residual.
- **W2-R3 — no-cache/revocation:** retire/revoke → next call denies, no residual window;
  positive control (a live capability is accepted).
- **W2-R4 (SF-2) — lifetime is a FACT:** if lifecycle-scoped, pin "no clock TTL, revocation is the
  bound" out loud; if clock TTL, pin the `_absolute_expiry` re-check. Whichever the operator
  confirms, the security-auditor arbitrates.
- **W2-R5 (SF-3) — fail-closed resolution:** `resolve_agent(None/garbage)` → `None` → DENY;
  `agent_of(token)` stays `None`. Mutation-prove the DENY.
- **W2-R6 — mint-once:** re-register does not rotate a live secret; the raw secret is returned
  ONCE and never persisted; no credential in any rendered/logged surface (§F3a).
- **W2-R7 — DDL:** `capability_hash` `option<string>` `OVERWRITE`, UNIQUE `IF NOT EXISTS`,
  dirty-store migration pinned (store-ref §1.1/§1.4).
- **Fleet-briefing obligation (FLAG, not a 62-build task):** the capability model requires each
  subagent to CAPTURE `register`'s one-time secret and PRESENT it on every governed call — a
  spawn-BRIEF change (like "register first" already is), owned by orchestration/packet-65, not
  62's build. Pre-cutover nothing breaks (62 unserved). Name it so the contract author does not
  try to make 62 re-brief the fleet.

## W2.7 — sub-forks flagged (for the lead → operator)

> **OPERATOR RULED 2026-08-24 (via lead-62, AskUserQuestion):** **SF-1 = ADOPT** the refined
> reading (a VERIFIED credential argument is admissible; identity is taken from the verification
> result, not the asserted value; raw `owner=`/`as_agent=`/`created_by=`/`scope=server` CLAIMS
> stay forbidden as authz inputs). **SF-2 = agent-lifecycle-scoped + the optional
> `capability_expires_at` seam** (no clock TTL; the binding + no-cache revocation IS the bound,
> pinned out loud; the seam defaults to never). Both confirmed AS the sidecar recommended. SF-3 is
> a NOTE (no decision). The mechanism is SETTLED for the wave-2 contract.

- **SF-1 (§3.2.2 refinement: verified-credential-arg admissible)** — DERIVED from (A)+`name:secret`;
  recorded, flagged CONFIRM (edits a stated invariant's letter). Recommend adopt.
- **SF-2 (lifetime: agent-lifecycle-scoped vs clock TTL)** — reinterprets R1.3; recommend
  lifecycle-scoped + optional-expiry seam; security-auditor arbitrates. Flagged CONFIRM.
- **SF-3 (`agent_of` stays `None`; `resolve_agent` is the real seam)** — a refinement forced by
  the verified fact, NOT a fork; a crisp NOTE for the contract author.

None are MAJOR-blocking; SF-1 and SF-2 are "confirm-the-derivation / recommend" (operator may
veto), SF-3 is a note. The mechanism is fully specified for the wave-2 contract.

*Addendum author: design-sidecar-62 (Fable), 2026-08-24, consult `lore_comms #7027`. Grounded in
`principal_keys.py` (`PrincipalKeyStore` precedent) + `agents.py` (`AgentRegistry.register`) read
this session. Touches no code — I am the designer.*
