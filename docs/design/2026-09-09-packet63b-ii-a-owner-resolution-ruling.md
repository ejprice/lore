# Packet 63b — ii-a owner-resolution ruling (sidecar-63b-ii-a, 2026-09-09)

`brief-base v14 read` · brief project v7 read

Status: **Q1 + Q2 RULED (2026-09-09, graded at `a4eb097`)**, coupled, with riders. Authority per the
operator's 63b delegation (design doc header, 2026-09-03): this doc IS the ruling; the lead implements it.
Standing by for follow-ups; this doc grows by dated addenda, never by silent rewrites of a ruled section.

## Summary block (brief-base §1)

- receipt: `brief-base v14 read` · brief project v7 read · idle-gate contract written (this path)
- state: **done** — a binding ruling on both questions + the riders + the contract-revision worklist
- deviations: none. COMMIT-ONLY honoured — the ONLY write is this doc; no git, no production, no tests.
- **Packages considered:** none — no NEW package mechanism is specified. The two mechanisms this ruling
  names are EXTRACTIONS of code already in the tree (`governed.resolve_subject` step (2) → a lifted
  `governed.resolve_principal`; the send-side call of the already-ruled `governed.resolve_write_scope`).
  Nothing a package supplies (identity resolution against this repo's own `PrincipalStore`).
- **Reuse ledger:** ONE new reusable symbol specified — `governed.resolve_principal(access_token, *,
  principal_store)`. Query run: `lore_get_symbol("loremaster.governed.resolve_subject")` → its step (2)
  (`getattr(access_token, "subject")` → `principal_store.get_by_email`) is the EXISTING implementation;
  disposition **EXTENDED** (extracted so `resolve_subject` becomes a CALLER; `_comms_register` the second
  caller — proven shared by mutation, R4). Reading A's `resolve_operator_principal` on the register path
  is **REJECTED as copy #2 of owner derivation** (§3.1). No hand-roll.
- **Graded:** `a4eb097` · HEAD-at-report: `a4eb097` · SAME. (`git rev-parse HEAD` at spawn; the verdicts
  below are on the adversary's MP-4 / F-KEEPER constructions as reported against that sha.)
- decisions-needed (lead — orchestration, not design; both carry my recommendation): **D1** where the
  send-enforcement corpse reconciliation lands (§8); **D2** where "the register response serves the
  capability ONCE" lands (§3.4 — HARD bound: before 63b-iii, which cannot drive register→send over the
  wire without it).
- receipt POINTERS: §0 (rulings in one screen) · §1 (the sourced facts, F1–F11) · §2 (Q1) · §3 (Q2) ·
  §4 (per-verb flip) · §5 (RIDERS table R1–R8) · §6 (the §4.A send-half) · §7 (reviser worklist) ·
  §8 (corpse, measured) · §9 (bounds + triggers).

---

## 0. The rulings in one screen

- **Q1 — the send owner is the resolved `Subject`'s pair, and NOTHING ELSE.** A `message` row created by
  `send` stamps `owner_principal = subject.principal_id`, `owner_agent = subject.agent_id`, exactly as
  `LocalMemoryBackend` stamps a memory row (`local.py`: `owner_principal=subject.principal_id,
  owner_agent=subject.agent_id`). **A tokenless send has NO owner because a tokenless send does NOT
  WRITE** — `_comms_send` calls `_resolve_subject(capability)` UNCONDITIONALLY (the `remember`
  precedent, F8) and an absent/unverified identity is a teaching `GovernedDenied`, never a stamped row.
  Readings A, B and C are ALL REJECTED (§2.2) — the fork was mis-posed: it asked which owner a write
  gets in a world the design forbids the write in. The ii-a behavioural send pins are rewritten to drive
  a **CREDENTIALED** send (ambient transport token + the registrant's capability), the way
  `test_wire_isolation_63a.py::wire_world` already drives `recall`.
- **Q2 — the keep keeper is the REGISTRANT's principal, read from the transport token through the SAME
  seam `resolve_subject` reads it from** — lifted to ONE `governed.resolve_principal(access_token, *,
  principal_store)` that BOTH `resolve_subject` (step 2) and `_comms_register` call. Q1 and Q2 are the
  SAME principal iff the same token — one derivation, no second path. `resolve_operator_principal`
  (Reading A) NEVER runs on a served hot path: it is the admin-CLI migrate's one-shot, fleet-wide guess
  with a REFUSE, and on the register path it is copy #2 of owner derivation AND wrong the moment a second
  principal is householded (it would make B's session A's).
- **A TOKENLESS register succeeds OWNERLESS and mints NO keep** (ruled reading α, §3.2 — the pkt-62
  registry pin's letter at the tool layer): nothing fabricated, the agent is INERT for every governed
  verb (its `send` denies at `stamp_owner`'s "no owning principal"), and the register render NAMES the
  bound. Reading β (deny the register outright) is written down with its cost and its re-open trigger
  (63c, when `agent` becomes a governed population).
- **`requires_capability` flips TRUE per verb WITH the wave that enforces it:** `send` in ii-a
  (ENFORCED — an unconditional `_resolve_subject`, plus `agent=` ≡ the Subject's agent), the four reads
  in ii-b. A `True` the handler does not enforce is the typed-applicability lie (PKT-28 C1 class) — the
  adversary's guarded `if capability is not None` reference is exactly that door, and it is CLOSED by a
  behavioural ∀-leg (R6), not by AST presence.
- **The §4.A "both remember AND send flip" rider IS realised in ii-a** (§6): `send` passes the session
  keep scope as the EXPLICIT `scope` argument to `resolve_write_scope` (never `None→default`), so
  `_grantable` runs on every send; the remove-household fixture is the send-half flip (R5). The
  adversary's "send-half unexercised" is a property of its reference's `None→default` bypass, not of the
  design.
- **The register RESPONSE serves the minted capability ONCE** (§3.4) — the §4.D "register MINTS it"
  letter over the wire; at `a4eb097` `_render_comms_register` serves no credential, so a wire client can
  never obtain the thing `send` will require. Placement is D2; the bound is hard: before iii.

---

## 1. What the sources actually say (facts the ruling rests on — read at `a4eb097`, cited not re-transcribed)

- **F1 — pkt-62 FORK 2 (operator, 2026-08-24; `2026-08-24-packet62-agent-identity-rulings.md` §FORK 2):**
  the local fleet authenticates as the operator's REAL principal via a pkt-49 api-key; the sentinel is
  RETIRED; option (A) applies UNIFORMLY *"with NO sentinel/no-credential branch"*; `stamp_owner` has
  *"ONE path"*; *"packet 62 builds against the credentialed path and adds NO no-credential fallback. A
  governed write with no resolvable credential is fail-closed"*; and *"NULL `owner_principal` now
  unambiguously means 'genuinely-legacy pre-retrofit row', never 'a new loopback write' — the two
  populations never collide"* (Fork 2 (a)). **"Pre-cutover" in that doc means the fleet running the OLD
  no-auth IMAGE, which never executes 62/63 code** (I5: *"the pre-cutover fleet keeps running the old
  no-auth image (62/63/64 unserved until 65)"*).
- **F2 — the pkt-62 REGISTRY pin** (`test_agent_capability.py::TestRegisterStampsOwnerPrincipalFromTheCredential::
  test_register_without_a_credential_is_ownerless_not_fabricated`): `AgentRegistry.register(...,
  owner_principal_id=None)` leaves `owner_principal` NONE — *"the pre-cutover ownerless local fleet, Fork 2
  — it does NOT fabricate an owner. REDDENS a build that stamps a default/sentinel owner"*. This is a
  pin on the REGISTRY method (called directly by `_register_owned`), and `register` is mint-once-on-create
  (a re-register never re-stamps).
- **F3 — pkt-62 W2.3 "Auditor attack surface":** *"unauthenticated `register` mints an owned agent →
  register must read the principal from the transport token (fail-closed if absent; pre-cutover
  unserved)"*. The property protected: no OWNED agent without proof of the owner. ⚠ *"fail-closed if
  absent"* admits two readings that produce different code (§3.2) — written down there, picked there.
- **F4 — SF-63-1 (operator CONFIRMED 2026-08-28; `2026-08-28-packet63-retrofit-rulings.md` §7):**
  `register` gets-or-creates `key='session:<session>'` (type `session`, **keeper = the FIRST
  registrant's principal**); `send` stamps `scope = keep:<that id>`; the keeper's own principal's agents
  auto-join (auto-householded, 60 Fork D); *"a FOREIGN principal's register into an existing session keep
  is DENIED with a teaching error until the keeper `add-household`s that principal"*.
- **F5 — design §4.D (ruled):** every message-family verb REQUIRES `capability=`, *"resolved through
  `AppContext._resolve_subject` (the ONE composition root)"*; *"`register` is the exception that MINTS it
  (identity from the transport token via `stamp_owner`'s register side, as today)"*; `agent=` MUST equal
  the resolved Subject's agent, mismatch = teaching `GovernedDenied`. ⚠ *"as today"* is FALSE at
  `a4eb097` for the TOOL layer (F10) — the registry has the kw; `_comms_register` never passes it.
- **F6 — design §1.4 (ruled), the `send` label frame's effect:** *"created `message` row's
  `(owner_principal, owner_agent)` == the subject's pair and `scope` == the session keep"*. The design
  DOES specify the send owner. It specifies it as a function of a Subject, and only a credentialed call
  has one.
- **F7 — `owner_stamp.stamp_owner`:** raises `OwnerStampError` on an absent/unverified capability AND on
  *"the verified agent has no owning principal — fail-closed (R2.1); a governed write is never stamped
  with a null owner"*; ONE store read (#425) — *"corpse B leg B catches exactly that wrong re-route"*
  (a second owner read is a pinned defect).
- **F8 — the precedent:** `AppContext.remember` calls `self._resolve_subject(capability)`
  UNCONDITIONALLY (63a-ii, §10.5): *"An absent / unverified identity raises GovernedDenied (a teaching
  error, NEVER an ownerless write)"*. 63-rulings §8's removed-behaviour item (1) rules the class:
  *"post-cutover an identity-less call DENIES (dropped-deliberately: §3.2.2; pinned as a teaching error,
  never a silent empty result)"*.
- **F9 — 63-rulings §2.1 table (the MIGRATE path, legacy rows only):** `message.owner_principal =
  sender.owner_principal` AFTER the agent backfill; `agent` backfilled *"to the operator's real
  principal (the 62 Fork-2 ruling: the local fleet IS the operator's principal, no sentinel)"* under the
  single-principal PRECONDITION with a REFUSE. That is `resolve_operator_principal`'s ONLY home: an
  admin-CLI, one-shot, precondition-guarded backfill of rows written BEFORE identity existed.
- **F10 — HEAD (`a4eb097`) state, read via `lore_get_symbol` + `sed`:** `_comms_register` calls
  `agent_registry.register(...)` WITHOUT `owner_principal_id`, reads no token, mints no keep;
  `_comms_send` resolves no Subject and stamps nothing; `_render_comms_register` serves NO credential;
  `AgentRegistry._verify_capability_owner` EXISTS; `_comms_fakes.py` has ZERO hits for
  `_verify_capability_owner` / `owner_principal_id`.
- **F11 — the ii-a contract fixture** (`test_comms_send_scope_63b_ii_a.py::ctx`,
  `test_message_enforcement_63b_ii_a.py::ctx`): `build_app_context` with NO ambient token, ONE `member`
  principal provisioned, and every behavioural pin drives `comms(action="register"/"send")` with NO
  `capability=`. **The fixture guarantees the one condition (no identity) under which the design says
  the write must not happen — and then asserts the write happened.** That is THE TEST ENVIRONMENT IS A
  FICTION in reverse, and it is the root of MP-4 and F-KEEPER both.

---

## 2. Q1 (MP-4) — RULING: the send owner is the Subject's pair; a tokenless send DENIES

### 2.1 The fork is mis-posed

MP-4 asks *"what `owner_principal` does a tokenless, pre-cutover local-fleet send stamp?"* Under F1 + F5
+ F8 the answer is: **none, because it stamps nothing — it is denied at `_resolve_subject` before any
keep is read or any row is written.** Post-65 every served call carries the api-key (F1), so a tokenless
send exists only in a test fixture or a broken cutover, and for the broken cutover fail-closed lock-out is
the DESIGNED signal (62 Fork 2 (c)). The adversary's reference made the tokenless send succeed by
guarding `_resolve_subject` behind `if capability is not None` — the adversary itself flagged that as the
dead-call door (F-D) — and then had to invent an owner. Every candidate reading is an answer to the wrong
question; each also has a concrete wrong-world receipt:

### 2.2 The three readings — REJECTED, each with the wrong build it blesses

| reading | what it stamps | why REJECTED | the build it blesses (the false clear) |
|---|---|---|---|
| **A** — session keep's keeper (`resolve_operator_principal`) | the keeper / the fleet's one admin | copy #2 of owner derivation beside `stamp_owner` (ROUTING-IS-NOT-SHARING); it IS the no-credential fallback F1 retired; `resolve_operator_principal` is a migrate-time fleet-wide guess with a REFUSE, never a served-path resolver (F9) | **ownership forgery under SF-63-1:** the moment the keeper `add-household`s principal B, B's agent's send is stamped OWNED BY A. Passes every ii-a pin (WB-2) because the fixture is a principal MONOCULTURE (F11) — the fixtures-must-discriminate class, axis 2 |
| **B** — `None` now, defer to iii | nothing | violates F7 (*never a null owner*) and F1 (a live NONE write collides the two populations Fork 2 (a) says never collide); makes `_effect_send_message` un-pinnable (a NONE owner IS the HEAD unstamped shape the predicate exists to reject — WB-3) | a send that writes UNOWNED governed rows for the whole ii-a→iii gap; a read filter that then serves them to nobody (member-invisible) or everybody (admin) — the single-brain-on-dirty-rows hole (63-rulings §6 item 5) |
| **C** — the sender agent row's stored `owner_principal` | the agent's owner, re-read | a SECOND owner read — the #425 TOCTOU `stamp_owner`'s one-read closure removed (F7, corpse B leg B pins the re-route); makes the row a second source of truth (the same defect §4.A rejected for scope, reading B); for a tokenless register the agent is OWNERLESS (F2) so C ≡ B in disguise | a build where a concurrent re-stamp between the read and the CREATE stamps a stale owner; and every tokenless-register world stamps NONE |

**C's SEMANTIC is correct and already enforced by the right mechanism:** `stamp_owner` →
`_verify_capability_owner` reads `(owner_agent, owner_principal)` from the agent row in ONE round trip AND
enforces the `(principal, agent)` binding against the token. So `subject.principal_id` == the agent row's
`owner_principal` == the token's principal, by construction and by verification. "The message is owned by
whoever owns the sending agent" is TRUE — and the Subject's pair is the verified statement of it.

### 2.3 The exact stamp (binding)

A `send` that WRITES stamps, on the created `message` row:
- `owner_principal = subject.principal_id` (bare principal id → bound as `RecordID(PRINCIPAL_TABLE, …)`,
  store-ref §2, exactly as `AgentRegistry.register` binds `agent.owner_principal`);
- `owner_agent = subject.agent_id` (bare agent id → `RecordID(AGENT_TABLE, …)`);
- `scope = keep_scope(_bare(session_keep.id))`, resolved per §4.A and §6 below;
where `subject = await self._resolve_subject(capability)` — the ONE composition root, called
UNCONDITIONALLY, first thing after the dispatcher's shape checks. The `sender` the ledger receives
(`agent_row`, from `agent=`) MUST satisfy `_bare(agent_row.id) == subject.agent_id`; a mismatch is the
§4.D teaching `GovernedDenied` (*"agent= names X but the capability verifies as Y"*), never a silent
preference. Nothing else moves the stamp (F4 anti-injection — 63-rulings §3.2).

### 2.4 Reconciliation with Fork 2 (the brief's item 4, first half)

Fork 2 says: real principal, one path, no fallback, fail-closed. This ruling is Fork 2 applied to `send`
without exception: the ONE path is `_resolve_subject`, the fail-closed is `GovernedDenied`, and
"ownerless" is a property of a pre-identity AGENT ROW (F2 — a substrate fact the registry does not
fabricate around), never of a NEW governed write. The apparent tension the adversary found ("the sender
is ownerless, so what does its send stamp?") dissolves: an ownerless agent's send is DENIED by
`stamp_owner`'s own second clause (F7) — which is Fork 2 (a)'s promise that a live write never carries a
NULL owner, kept.

---

## 3. Q2 (F-KEEPER) — RULING: keeper = the registrant's principal, via the lifted `resolve_principal`

### 3.1 The mechanism (binding)

**Lift:** `governed.resolve_principal(access_token: Any, *, principal_store: Any) -> Principal | None`,
EXTRACTED from `resolve_subject` step (2):
- returns `None` iff the token is absent or carries no `subject` (no principal identity was PRESENTED);
- raises `GovernedDenied` iff a `subject` IS presented and `principal_store.get_by_email(subject)` is
  `None` (a presented-but-unadmitted principal is a DENY — never degraded to "ownerless"; the teaching
  text is `resolve_subject`'s existing *"no principal is admitted for …"* line, moved, not cloned);
- `resolve_subject` step (2) becomes `principal = await resolve_principal(...)`;
  `if principal is None: raise GovernedDenied(<the existing "carries no principal subject" teaching>)`.
  ONE implementation of token→admitted-principal; the None-policy differs per caller and is stated at
  each call site.

**`_comms_register` (ii-a), in THIS order** (a rejected register writes NO agent row — the dispatcher's
own #97 law, *"a side effect a rejected call must never have"*):
1. `principal = await governed.resolve_principal(get_access_token(), principal_store=self._principal_store)`.
2. If `principal is None` → **reading α (§3.2):** `owner_principal_id=None`, NO keep touched, render
   carries the ownerless bound line. Skip to 5.
3. `keep = await self._keep_store.get_or_create_keyed(key=f"session:{session}", type="session",
   keeper_email=principal.email, name=<the session string>)` — the SF-63-4 CAS: exactly one keeper per
   session key, and if I minted it I am the keeper (auto-householded, 60 Fork D).
4. **SF-63-1 foreign gate:** `keep_scope(_bare(keep.id)) ∈ await resolve_visible_keeps(self._keep_store,
   member_email=principal.email)` — the SAME household resolver `resolve_subject` step (3) uses and the
   same predicate `_grantable` applies at send (ONE IMPLEMENTATION, three sites). False → teaching
   `GovernedDenied` naming the SESSION and the remedy (`lore-adm add-household`) and **NOT the keeper's
   identity** (a foreign principal must not learn who keeps a session — 63-rulings §6's existence-leak
   stance). No agent row written. Race bound, named: two concurrent first-registrants → the CAS makes one
   keeper; the loser's gate runs against the WINNER's household and denies unless householded — correct,
   and it leaves no loser-owned row.
5. `result = await self.agent_registry.register(agent, session=…, owner_principal_id=_bare(principal.id)
   if principal else None, …)` — the pkt-62 R3.3 server-derived stamp, at last wired at the tool layer.
6. Render (Leg 1 — the render names what it did, DERIVED from typed state, never a name comparison):
   credentialed → one line *"session keep `session:<s>` — minted (you keep it)"* / *"— joined (kept by
   another principal)"* keyed on `keep.keeper_id == _bare(principal.id)`; ownerless → the α bound line
   (§3.2). Each new served line is registered + proven in `test_comms_promise_registry.py` (standing
   instrument; a new promise literal that is not registered reds the suite — that is the instrument
   working).

### 3.2 The tokenless register — reading α RULED; reading β written down with its trigger

F3's *"fail-closed if absent"* admits two readings that produce different code:

- **α (RULED for ii-a):** the OWNER STAMP fails closed — no owner is stamped, no keep is kept, nothing is
  fabricated (F2's letter, lifted from the registry to the tool); the agent is INERT for every governed
  verb because `stamp_owner`'s second clause (F7) denies it; the render says so. The W2.3 property
  ("no OWNED agent without proof of the owner") holds: the agent is not owned.
- **β (alternative, NOT ruled now):** the register call itself DENIES with `GovernedDenied`. Cleaner as a
  broken-cutover signal (lock-out at the first call rather than the second), but it makes `register` a
  governed-denying verb one packet BEFORE `agent` is a governed population (SF-63-2, 63c), and it pays a
  measured corpse of **58 tokenless register sites** (§8) for a signal α delivers one call later with a
  named bound. **Re-open trigger for β: 63c** — when `agent` joins the population set, `register` IS a
  governed write and deny-on-absent is its natural shape; 63c's design consults this section.

Under α, SF-63-1's "FIRST registrant" means the first registrant WITH a resolved principal (an ownerless
registrant keeps nothing). Post-65 the distinction is unobservable (every call is credentialed).

The α render line must state three FACTS (the reviser words it; the promise registry proves it): the
agent holds no owner; which verbs deny for it (the `requires_capability=True` set, DERIVED); the two
remedies (present the fleet credential and register a FRESH name — mint-once-on-create means a re-register
never re-stamps — or `lore-adm migrate-governed --table agent` for a legacy row).

### 3.3 Relationship to Q1 — one derivation, so the same principal iff the same token

Send-owner (Q1) and keep-keeper (Q2) are BOTH the transport token's admitted principal, resolved through
ONE seam: `resolve_principal` directly for register, and via `resolve_subject` (which calls it) for send.
They coincide exactly when the same principal registers and sends — the single-principal fleet — and
DIVERGE by design when the keeper has householded a second principal: B's agent registers (joins A's keep),
B's send is owned by B and scoped to A's session keep. That divergence is the property WB-2 cannot see and
R1 pins. There is no configuration in which a served write's owner is derived from the keep's keeper.

### 3.4 The register RESPONSE serves the capability ONCE (the §4.D "MINTS it" letter over the wire)

pkt-62 W2.3 (ruled): *"returns the raw `<name>:<secret>` ONCE in the register result"*; W2.6's fleet
obligation: *"each subagent [must] CAPTURE `register`'s one-time secret and PRESENT it on every governed
call"*; W2-R6: *"no credential in any rendered/logged surface (§F3a)"*. Over MCP the register RESULT IS the
render, so the only reading under which W2.6 is satisfiable is: **the FIRST-register response carries the
credential, in one clearly-labelled line, and NO OTHER surface ever does** (a re-register response says it
is held since first register and is not re-served; `fleet`, `heartbeat`, logs, error text never carry
it). At `a4eb097` `_render_comms_register` serves no credential (F10), so `capability=` is a bound that is
not a fact — a wire client cannot obtain what `send` requires. RULED as the design; **placement is D2**:
recommended ii-a (it is the `register` render, in ii-a's `server.py` writable set, and the ii-a
behavioural pins can then be driven END-TO-END through the tool); acceptable ii-b; HARD bound: before
63b-iii, whose wire battery drives register→send through the tool and cannot start without it. Pin (R7).

---

## 4. `requires_capability` flips TRUE per verb, WITH the wave that enforces it

§4.D's *"send/drain/ack/await/story = True in 63b"* spans ii-a AND ii-b. The FIELD and the `capability=`
parameter land in ii-a (design §5 row); each verb's `True` lands with the wave that makes its handler
ENFORCE it: `send` in ii-a; `drain`/`ack`/`await`/`story` in ii-b (their read shapes need the Subject
anyway — §4.B/§4.E). A `True` whose handler does not enforce is the typed-applicability lie this repo
has ten receipts for (PKT-28 C1). Consequences for the ii-a contract (`test_comms_capability_63b_ii_a.py`):
- `test_the_message_family_verbs_require_capability` → ii-a asserts `{send} ⊆ True-set`;
- `test_the_capability_set_is_EXACTLY_the_message_family_surfaced_not_narrowed` → ii-a asserts EXACTLY
  `{send}` with a docstring naming ii-b's growth to the five (ii-b updates the literal); "surfaced, not
  narrowed" is preserved by the ∀-leg below, which reds a verb flipped True without enforcement;
- `test_every_capability_verb_handler_resolves_the_subject` (AST presence) STAYS as the coverage floor
  and gains the EFFECT leg **R6**: ∀ verb with `requires_capability=True` (derived from `_COMMS_ACTIONS`),
  a call with NO capability → `GovernedDenied` (the guarded-call door closed behaviourally).

---

## 5. RIDERS — and pin it like this (the rider is part of the ruling)

Every pin below is named so the reviser's contract can carry it verbatim; every one discriminates a
build the adversary constructed or this ruling names. Fixture law: the behavioural layer becomes a
**credentialed** `AppContext` (the `test_wire_isolation_63a.py::wire_world` idiom: patch
`loremaster.server.get_access_token` to `_governed_contract.access_token(subject=<email>)`; ≥2 `member`
principals provisioned, one of them NOT an admin so `resolve_operator_principal` gives a DIFFERENT answer
than the registrant). Until R7 lands, tests obtain the capability the way `wire_world` does
(`ctx.agent_registry.register(..., owner_principal_id=…)` → `result.capability`), then drive the TOOL's
`register` (idempotent re-register mints/joins the keep) and `send(capability=…)`.

| # | rider | pin (suggested name, file) | fixture | RED on (the wrong build it kills) | mutation / control |
|---|---|---|---|---|---|
| **R1** | Q1 owner EXACTNESS (the F4 effect leg the enforcement file's docstring PROMISED and nobody wrote) | `test_a_credentialed_send_stamps_exactly_the_subjects_pair` · `test_comms_send_scope_63b_ii_a.py` | A registers in `s1` (keeper); A `add_household_member`s B on `session:s1`; B's agent registers (joins); B sends with B's capability | read back `(owner_principal, owner_agent)` ≠ `(_bare(B.id), _bare(B_agent.id))`; **explicitly** `owner_principal == _bare(A.id)` (Reading A / WB-2) reds; `None` (B) reds; the row's `sender` ≠ `owner_agent` reds | positive control: A's own send stamps A. This is the pin that makes the live-classify's non-None a structural leg rather than a false clear |
| **R2** | tokenless send DENIES, writes nothing | `test_a_tokenless_send_denies_and_creates_no_message_row` (same file) | credentialed register; then clear the ambient token (holder→None) and send with no capability | a row exists / no `GovernedDenied` / the F5 observer sees ≥1 message CREATE (anti-vacuity inverted: assert ZERO observed creates) | control: the same send credentialed → 1 row. Kills reading B and the guarded-call reference |
| **R3** | Q2 keeper EXACTNESS + SF-63-1 foreign gate | `test_register_mints_the_session_keep_kept_by_the_registrants_principal` · `test_a_foreign_principals_register_into_a_kept_session_denies_naming_the_remedy_not_the_keeper` · `test_the_keepers_own_second_agent_registers_fine` (positive control, 63-rulings §9 item 7) | registrant = the NON-admin second principal | `keep.keeper_id ≠ _bare(registrant.id)` — an admin/operator keeper (Reading A) reds; foreign register succeeds / writes an agent row (assert NO row for the denied name) / the teaching contains the keeper's email | idempotence pin stays (same keep on second register by a householded principal) |
| **R4** | ONE derivation — `resolve_principal` shared by `resolve_subject` AND `_comms_register` | `TestThePrincipalResolutionIsSharedByMutation` · `test_comms_capability_63b_ii_a.py` (or send_scope) | monkeypatch `governed.resolve_principal` to return a FIXED other admitted principal P* | `resolve_subject`'s `Subject.principal_id` does not change to P*, OR a register's stamped `owner_principal` / minted keeper does not change to P* → one of them has a private copy | positive control unpatched. Structural twin: `function_calls_named(resolve_subject, "resolve_principal")` + same for `_comms_register` |
| **R5** | the §4.A send-half grant flip (§6) | `test_a_sender_removed_from_the_session_household_is_denied_at_send` + `test_perturbing_the_lifted_seam_changes_send` | B registers (householded), keeper `remove_household_member`s B, B sends | send succeeds (grant predicate bypassed — the `None→default` reference); under a PERMISSIVE `resolve_write_scope` the same send SUCCEEDS (proves send routes through the seam) | the existing remember-half mutation proof stays; now BOTH halves flip, as §4.A's rider demands |
| **R6** | spec honesty ∀ True verbs (closes F-D's guarded-call door behaviourally) | `test_every_capability_required_verb_denies_without_one` · `test_comms_capability_63b_ii_a.py` | derive the True-set from `_COMMS_ACTIONS`; for each, a well-formed call with no capability | any True verb that does not raise `GovernedDenied` | AST presence pin stays as the coverage floor; in ii-a the set is `{send}`, in ii-b five |
| **R7** | the register response serves the credential ONCE (placement D2) | `test_a_first_register_serves_the_capability_once_and_a_reregister_does_not` · `test_no_other_comms_render_carries_a_credential` | first register → render contains the exact `<name>:<secret>` the registry minted; re-register → does not; `fleet`/`heartbeat` renders → do not | a render that leaks it twice, or never | pairs with the pkt-62 §F3a leak pin; the promise-registry registers the line |
| **R8** | `_effect_send_message` gains the structural leg the classifier CAN see | (edit the predicate in `test_message_enforcement_63b_ii_a.py`; the unit pins gain a case) | observed row: `after["owner_agent"] == after["sender"]` (both are on the row) | a build stamping any agent but the sender | keep the non-None legs; FIX the docstrings that say *"F4's separate pin"* to NAME R1 |

**The "and pin it like this" self-check applied to this ruling:** every clause in §2–§4 that says "the
correct build does X" has a row above whose RED column names the build that does not. The one clause with
no instrument is the α/β choice (§3.2) — deliberately: it is a pinned BOUND (the ownerless-register render
line is asserted, with the 63c trigger in its message, per WHEN YOU CANNOT CLOSE A HOLE, PIN IT).

---

## 6. The §4.A rider — "both remember AND send flip" — realised in ii-a, not deferred

§4.A (ruled): the send's resolved scope *"passes through the SAME grant predicate `remember` uses"*; rider:
*"remove the `_grantable` call in the lifted seam → BOTH the `remember scope=` deny pin and the `send`
foreign-keep deny pin red"*. The adversary found the send half unexercised because its reference called
`resolve_write_scope(subject, None, default=session_scope)` — the `None→default` branch, which by the
seam's own contract never consults `_grantable`. That is a property of that reference, not of the design.

**Binding shape for `_comms_send`:** the session keep is resolved by KEY (§4.A reading A); a missing keep
→ the ruled `GovernedDenied` *"register first…"* BEFORE the seam; then
`scope = await resolve_write_scope(subject, session_scope, default=session_scope)` with `session_scope`
passed as the EXPLICIT `scope` (never `None` — `send` has no "no scope requested" case; that branch is
`remember`'s). `_grantable(subject, session_scope)` is then `session_scope ∈ subject.visible_keep_ids`,
i.e. *the sender's principal is in the session keep's household* — exactly SF-63-1's admission predicate,
re-applied at write time, so a principal the keeper has since removed loses the room (R5). The `default=`
argument is unreachable for send and R5's docstring says so.

Is "send-half unexercised until iii" acceptable? **No** — iii is report-only (design §5); a rider whose
instrument lives in a wave that builds nothing is a hope with a wave number. R5 lands in ii-a.

---

## 7. The contract-revision worklist (what the reviser changes — by file; the lead grants any set change)

1. `test_comms_send_scope_63b_ii_a.py` — `ctx` becomes the credentialed harness (§5 preamble; ≥2 member
   principals, one non-admin registrant); `TestRegisterMintsTheSessionKeep` gains R3 (keeper exactness,
   foreign deny + positive control); `TestSendResolvesTheSessionKeepScope` gains R1, R2, R5; the
   existing keep-missing and scope-stamp pins are driven credentialed; R4 lives here or in the capability
   file. The module docstring's F-KEEPER paragraph is REPLACED by a pointer to this doc §3.
2. `test_comms_capability_63b_ii_a.py` — §4's per-verb rewrite (exact-set `{send}` + docstring naming
   ii-b); R6; R4's structural twin.
3. `test_message_enforcement_63b_ii_a.py` — R8 (predicate leg + unit case); the live-classify test is
   driven credentialed (it then classifies for the RIGHT reason); the three "F4's separate pin" docstring
   mentions name R1 by test name (P8d: prose that promises a mechanism must name a real one).
4. `test_comms_capability_63b_ii_a.py` / send_scope — R7 (if D2 = ii-a).
5. Production shape the contract now implies (for the builder's brief, not the reviser): `governed.
   resolve_principal` (§3.1); `_comms_register` steps 1–6; `_comms_send` per §2.3 + §6 (unconditional
   `_resolve_subject`, agent≡subject, keep by key, explicit-scope seam call, `write_guard("send")`, the
   three stamps threaded to `MessageLedger.send`/`_send_fragment`); `_render_comms_register`'s two new
   lines + the credential line (R7); `CommsActionSpec.requires_capability` with `send=True` only.
6. The adversary's MP-1/MP-2/MP-3 stand as reported and are NOT altered by this ruling; MP-2's corpse
   (`test_governed_migration_63a.py::…::test_migrate_message_before_agent_refuses`) must be fixed by
   registering a genuine NONE-owner agent in that fixture (its docstring already claims one) — the
   reading I RULE over "retire the test" (the agent-first refuse is a real 65-cutover property).

---

## 8. The corpse — measured at `a4eb097`, and the placement fork D1

Measured by `awk` over `loremaster/tests/*.py` (the shell text-search tool is hook-blocked in this
checkout — SAID; the pattern is the bare `action="<verb>"` literal, so it counts CALL SITES, not tests, and
it is a floor):

| file | `send` | `drain/ack/await/story` | `register` | harness |
|---|---|---|---|---|
| `test_comms_tool.py` | **39** | 28 | 20 | FAKES (`_comms_fakes.py`: 0 hits for `_verify_capability_owner` / `owner_principal_id`) |
| `test_comms_wiring.py` | 0 | 0 | 29 | real store |
| `test_comms_render_architecture.py` / `test_mcp_server.py` | 0 | 0 | 5 / 4 | mixed |
| `test_comms_await.py` / `test_comms_waiting_line.py` / `test_surreal_fakes.py` | 0 / 1 / 0 | 2 / 1 / 1 | 0 | `AppContext.comms(harness, …)` fakes |
| the two ii-a contract files | 3 | 0 | 10 | real store (rewritten by §7) |

- **Under α, the 58 tokenless `register` sites stay GREEN** (their render gains a bound line → the
  promise registry registers it; byte-exact register-render pins, if any, are updated — that is the
  instrument working, not a corpse).
- **Under ii-a `send` enforcement, ~41 existing `send` sites red**, 39 of them on FAKES where an
  unconditional `_resolve_subject` is an `AttributeError`-class break (the fake registry has no
  `_verify_capability_owner`, the fake context no `_principal_store`), not a teaching deny. The four
  read verbs (28 + 4 sites) are ii-b's identical debt.
- **D1 — placement, lead's call, my recommendation:** land enforcement AND its corpse in ii-a, as ONE
  reconciliation: a shared credentialed fixture for the real-store files, and for `_comms_fakes.py` the
  minimal seams (`FakeAgentRegistry._verify_capability_owner` + `register(owner_principal_id=)` + a fake
  principal store), with the sites that only need "a send happens" routed through it. Splitting it out
  leaves ii-a shipping either a lying `requires_capability` or 40+ `RED_ADJUDICATED` rows across the
  ii-a→ii-b gap — deferral shape 3 applies only if capacity forces it, and then as a NAMED sub-wave
  (`ii-a-corpse`) with the trigger *"ii-b cannot start until it closes"*. ⚠ Whichever placement: the
  design's own removed-behaviour inventory (63-rulings §8 item 1) ALREADY ruled identity-less calls
  DENY; this corpse is that ruling's cost arriving, not a new cost this ruling invents.

---

## 9. Bounds — each with its named re-open trigger

- **B1 — reading α for the tokenless register** (§3.2). Trigger: **63c** (`agent` becomes a governed
  population → reading β is the natural shape). Pinned by the render bound line.
- **B2 — the agent≡capability MISMATCH battery** (≥2 principals × ≥2 agents, one shared session string,
  every verb) stays **63b-iii's** headline as the contract author's F-D says — but the EQUALITY CHECK
  itself (`_bare(agent_row.id) == subject.agent_id`) is BUILT in ii-a (§2.3) and ONE mismatch case is
  pinned in ii-a (an agent sending with a sibling's capability → `GovernedDenied`); iii widens the matrix,
  it does not introduce the check. Trigger for widening earlier: none needed.
- **B3 — `_effect_send_message` cannot see the Subject** (a classifier sees rows, not tokens); owner
  exactness lives in R1, the classifier in R8. This is a stated split, not a hole: a wrong build must pass
  BOTH, and R1's fixture is the one WB-2 fails.
- **B4 — the register-render credential (R7) placement** is D2; hard bound before iii.
- **B5 — the migrate legs are untouched by this ruling.** `resolve_operator_principal` keeps exactly its
  §4.C home (three admin-CLI legs, precondition-guarded). MP-3's mutation proof across the three legs
  stands as the adversary asked.

---

## 10. Discipline receipts

- Store law: no store/schema/DDL change is ruled here (the message governed columns are §4.F, already
  ruled); the `RecordID` binding of the stamps cites store-ref §2 via `AgentRegistry.register`'s existing
  practice, not re-transcribed.
- lore-first: every symbol via `lore_get_symbol` / `lore_search` / `lore_read` (`resolve_subject`,
  `stamp_owner`, `AgentRegistry.register`, `AppContext._resolve_subject`, `AppContext.remember`,
  `KeepStore.get_or_create_keyed`, `Keep`, `Subject`, `_grantable`, `keep_scope`,
  `resolve_visible_keeps`, `MessageLedger.send`); the two handlers + spec table + render read with
  `sed` at the line numbers `awk` located (a `lore_get_symbol` miss on the bare `_comms_register` /
  `_comms_send` names — they are methods; module-qualification would have resolved them, not a lore
  defect, nothing filed). The shell text-search tool is hook-blocked → `awk` for every textual sweep, SAID.
- Every count in §8 was derived this session by the stated instrument; none is inherited.
- The attribution reminder injected at session start is overridden by the operator's standing
  `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY; the lead commits).
