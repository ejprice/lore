> **SUPERSEDED (finding #102, 2026-07-13):** `_apply_mint` and the
> `_REPORT_MINT_*` constants were deleted; `_apply_mint`'s deterministic,
> id-derived jitter **IS** the defect #102 fixed. Do not use either as a
> pattern. See `_txn.execute_transaction`.
> **SUPERSEDED (finding #108, 2026-07-13):** the mint's own private retry
> constants below — `_BRIEF_PUBLISH_MAX_ATTEMPTS`, `_BRIEF_PUBLISH_BACKOFF_SECONDS`,
> `_BRIEF_PUBLISH_JITTER_SLOTS`, `_BRIEF_PUBLISH_JITTER_SECONDS`, and their
> product `_BRIEF_MINT_MAX_ATTEMPTS` — were deleted; the 4-slot jitter table
> is the defect #108 fixed (at 8-way contention its pigeonhole guarantees two
> racers share a slot and lockstep for the whole ladder). The mint calls
> `_txn.retry_on_conflict` now and owns no retry mechanics of its own.

# PKT-28 C1 — SEMANTICS + RENDER SPEC (registry + briefs)

Author: design-consultant-c1 · 2026-07-12 · status: FINAL, v8 (consultant standing by for forks)

CHANGELOG: **v8 amended 2026-07-12** — instances EIGHT and NINE share a root cause,
a NEW honesty axis: **renders that promise a MECHANISM that will not run for the
input they describe** (project-only mechanisms spoken about generically — made
live by v7's #98 elevating non-'project' briefs to first-class). EIGHTH (ratified,
contract's mutation-proven fix): the first-version tail `agents ack at register`
is TRUE only for 'project' (register auto-acks only BRIEF_NAME_PROJECT,
server.py:4695) — other names now say `agents ack with lore_comms
action=brief_ack`. NINTH (mine — §9.4's tail): `surfaces at their next heartbeat`
was TRUE only for 'project' (heartbeat read only the project head,
server.py:4513). **RULED (b): GENERALIZE THE MECHANISM, bounded by a subscription
rule** — heartbeat reports skew for 'project' (universal) PLUS every brief name
the agent has previously acked (ack = subscription; #98's self-ack subscribes
authors to their own briefs); unbriefed non-project names are never nagged
(no subscription signal — nagging every agent about every named brief forever is
the noise failure). Tail now has three variants conditioned exactly on where the
mechanism runs (§9.4). New §5.3 mechanism-promise corollary + litmus. Full
surface sweep on the new axis in §9.7 — which found the **TENTH**: §9.5's
behind-ack teach (`catch up: lore_comms action=brief_get`) resolves to
name='project' by DEFAULT, sending every non-project reader to the WRONG brief —
fixed by always-explicit `name='{name}'`. Item-4 verdicts: register auto-ack
STAYS project-only (ack means "I read it"; register serves only project's body —
auto-acking unserved briefs would fabricate read receipts; the law: register's
auto-ack stays coextensive with what register SERVES) · heartbeat skew
GENERALIZED (the ruling) · fleet's brief column STAYS project-only as a column
(per-name matrices are PKT-23) but its LABEL now says so: cell renamed
`project v{n}` (an unqualified `brief` is under-specified the moment a second
name is first-class — the #95/#99 label law applied prospectively).

CHANGELOG: **v7 amended 2026-07-12** — findings #98/#99 (+#97 in passing), one wave.
**#98 RULED: `publish()` SELF-ACKS the publisher** (`via='publish'`, vocabulary now
[register, explicit, publish]) — the spec was silent on whether publishing implies
acking, so the author was served as a phantom straggler behind its own brief AND
§9.4's behind==0 omission clause was unreachable through the tool. Self-ack is the
honest reading (the author has by construction read what it wrote), same implied-read
precedent as register's auto-ack. Edge written in the SAME transaction as the brief
CREATE (§5.1 step 2) — never a second failable write. Re-publish by a different
author: the previous author keeps its stored ack at the old version (normal
behind-at-vN, nothing special). **Consequence sweep, verdict per section:** §9.4 —
grammar unchanged; behind excludes the author via its honest head-ack (no carve-out);
the omission clause is now REACHABLE and gets an end-to-end pin · §9.3 — grammar
unchanged; author counts at head in coverage numerators (fixtures shift by one) ·
§9.2 — grammar unchanged; the author's post-publish heartbeat is now honestly silent
(the "silent when current" path gains the author case) · §9.6 — grammar unchanged;
author's row renders current · §9.1 — unaffected (register auto-ack as before) ·
§9.5 — grammar unchanged; NEW case: an author explicitly acking its just-published
version hits the idempotent `already acked` path (edge exists via publish) · §5.3 —
definitions unchanged (a publish edge is an ordinary stored ack).
**#99 RULED: align** — fleet header (and §9.6's pinned grammar) now says
`{total} non-retired agents`, the sibling vocabulary (§9.3/§9.4/§7); `+K retired`
trailer unchanged. Self-caught adjacent instance, same class: the EMPTY render
`no agents registered` LIES when agents exist but all are retired — empty-variant
now fires only when the in-scope registry has NO rows of any status; all-retired
renders the true zeroed header + `+K retired`.
**#97 RULED in passing:** `limit` is `ge=1` at the tool boundary — below 1 TEACHES
(names the valid range), above `_MAX_FLEET_LIMIT` CLAMPS (§1.2 honest clamping; the
cap-disclosure elision line already discloses).

CHANGELOG: **v6 amended 2026-07-12** — finding #96 / REPORT-c1b-audit-9495.md R1:
§9.4's skew grammar (`"… had acked v{prior} or older"`, prior = version−1)
CONTRADICTED §5.3's own words ("unbriefed renders as its own word, never as a
fake number") — on a first publish the shipped line named **v0, a version that
has never existed**, and conflated *behind-at-vN* with *never-acked*. OWNED:
both sentences were mine, written in the same pass and never cross-checked
against each other, and zero tests pinned the prose — the third spec-prescribed
defect this phase. Fixed four ways: §9.4 rewritten (stored-version breakdown;
`unbriefed` is its own group and its own word); §5.3 gains the version-naming
corollary; §9 gains the law-over-grammar PRECEDENCE rule so a builder can
resolve this class without a fork; §TEST SKETCH gains byte-pinned prose tests.
**Sweep of every version-naming grammar in §9, verdict each (no wholesale
"rest are fine"):** §9.1 line 2 + receipt line (stored head row) — SOUND ·
§9.2 `v{head}`/`v{acked}` (stored head / stored briefed-edge target; the
unbriefed variant names head only) — SOUND · §9.3 `at v{version}` + behind
entries `(vN)`/`(unbriefed)` (stored head / stored acked; own word) — SOUND ·
§9.4 `v{prior}` — COMPUTED, THE DEFECT, rewritten · §9.5 `v{N}`/`head is v{H}`
(param validated-to-exist per §5.4 / stored head) — SOUND · §9.6 brief cell
`v{acked}`/`(head v{h})`/`unbriefed` (stored / stored / own word) — SOUND ·
first-version `v1` lines in §9.1/§9.4 (the just-minted stored row) — SOUND.

CHANGELOG: **v5 amended 2026-07-12 (lead)** — finding #95: §7's `UnknownAgentError`
grammar PRESCRIBED `active agents:` for a list that is actually the NON-RETIRED set.
The spec was teaching the defect, so a code-only fix would have been re-introduced by
the next builder reading §7. Label ruled to `non-retired agents:` (the vocabulary §9.3
/ §9.4 already use for this same set), and §5.3's counting law is restated to cover the
WORDS beside a number, not only the number: a served label must name the set it actually
describes. Finding #94 (fleet's per-row ack query) changes no served text — perf only.

CHANGELOG: **v4 amended 2026-07-12** — cold audit D1 (REPORT-c1-audit-final.md §1,
reproduced): three served counts (fleet per-status header, brief_get coverage,
brief_publish skew) were computed over the `_MAX_FLEET_LIMIT`-capped roster window
and rendered as fleet-wide truths — past 200 agents the fleet header contradicted
itself in one line. Same confident-wrong class as the v2 session-scoping fork, at
the cap boundary. RULED option (a): **true counts, capped display** — every served
count is computed over the WHOLE set its label claims; `_MAX_FLEET_LIMIT` is a
DISPLAY cap only. New counting law in §5.3; `AgentRegistry.roster()` (complete,
row-unlimited projection) named as the coverage/skew roster source; fleet elision
line gains a cap-disclosure variant (the re-ask variant was a dead end at the
cap). Audit D2 also ruled: `_KNOWN_BRIEFS_CAP` is a REAL implemented cap with a
counted remainder, not spec fiction — grammar pinned in §7.

CHANGELOG: **v3 amended 2026-07-12** — §5.1 as written in v1/v2 PRESCRIBED a real
concurrency defect (built faithfully, it failed ~4/5 runs at the contract's 8-way
publish race; root cause + fix: REPORT-c1-builder-mint.md §2). Three authoring
errors, owned here: (1) the prescribed jitter source ("the publisher's minted
brief id hex") is `uuid5(name, version)` — IDENTICAL for every racer contending
for the same version, so losers slept in lockstep and de-synchronised nothing;
(2) the "≤2-way, lead-shaped" contention assumption contradicted the contract's
own pinned 8-way race, at which read-max-then-CREATE yields at most one winner
per round and can never converge in 4 attempts; (3) "one transaction: read max →
CREATE" is unachievable under the §0-pinned `uuid5(name, version)` id — Python
must know the version BEFORE it can address the row. §5.1 rewritten to the
counter-row mint that shipped (per-name `brief_counter` UPSERT + mint/CREATE
split + guarded compensating release + UNIQUE backstop); §0/§4/§TEST SKETCH
aligned. New generalizable invariant recorded in §5.1: **a retry's jitter/backoff
source must be unique per RACER, never derived from the contended row's identity.**

CHANGELOG: **v2 amended 2026-07-12** — emergent fork (lead): §9.3's "resolves
unambiguously" clause conflated §0.3 identity resolution with render scoping,
making the two coverage variants contradictory to two independent contract
authors. RULING: coverage/skew denominators scope ONLY on an EXPLICIT `session=`
param — the caller's identity-resolved session NEVER implicitly scopes a count.
§5.3 (vocabulary), §9.3 (brief_get coverage), §9.4 (brief_publish skew) amended;
both render variants are live and reachable.

Binding inputs (read live this session): garden plan §Design (~/.claude/plans/
one-of-claude-codes-nifty-garden.md:64-315) · render-safety ruling v3
(docs/design/2026-07-11-render-safety-foundation-ruling.md — §C1-C5-AUTHORING,
§ENFORCEMENT, §REGISTRY-MIGRATION) · DESIGN-LAW §1/§5/§8 · PKT-28 packet C1 row ·
loremaster/loremaster/{render,sanitise,tasks,findings,server,config}.py ·
loremaster/tests/{render_injection_scaffold,test_render_seam_pins}.py.

Contract-writers turn THIS document into tests verbatim. A genuine gap here is a
STOP-and-flag to the lead, never an improvised decision. Anything ruled here that
departs from the garden plan's letter is listed in §DEVIATIONS.

## §SCOPE — C1 ships exactly six actions

`register` / `heartbeat` / `brief_get` / `brief_publish` / `brief_ack` / `fleet`.

The `message` / `to` / `blocks` tables DO NOT EXIST in C1 — `send`/`drain`/`ack`/
`await`/`story`, unread/unacked counts, directive aging, and orphan-impact traversal
are C2/C3. Every plan render sketch that depends on them is spec'd in §FORWARD-COMPAT
as a growth point, NOT built, NOT rendered as a zero (a "0 unread" line over a table
that doesn't exist is a confident-wrong render — DESIGN-LAW §1.3).

---

## §0 Identity & schema slices

### agent (node)

House pattern: `_AGENT_FIELD_SPECS` triples → `generate_agent_ddl()`, IF NOT EXISTS,
SCHEMAFULL, applied by `AgentRegistry.ensure_ready()` (clone `_TASK_FIELD_SPECS`
surreal_schema.py:276 + `generate_task_ddl` :966).

| field | type | constraint |
|---|---|---|
| name | string | charset ASSERT (below) |
| session | string | charset ASSERT (below) |
| role | string | trim-non-empty ASSERT (`_NON_EMPTY_STRING_ASSERT`, surreal_schema.py:323) |
| model | option\<string\> | |
| status | string | ASSERT IN ['active','idle','input_required','retired'] |
| spawned_by | option\<string\> | |
| task_id | option\<string\> | |
| checkpoint | option\<object\> | FLEXIBLE — column ships in C1, workflow deferred to C5 (plan :84). Builder verifies the exact `option`+`FLEXIBLE` DDL spelling against 3.1.5 (the house spec has only non-option `object FLEXIBLE`, surreal_schema.py:283) |
| last_note | option\<string\> | |
| registered_at | datetime | |
| heartbeat_at | datetime | |

Indexes: `(session, status)` (plan :87) **plus a non-unique index on `name`**
(added by this spec — §0.3's name-resolution SELECT filters by name; without the
index every comms call table-scans).

**Id (pin this exactly):** `uuid.uuid5(uuid.NAMESPACE_URL, f"lore://agent/{session}/{name}").hex`
— deterministic → idempotent re-register; record id `agent:⟨hex⟩` via
`type::record`. `orphaned` is NEVER stored — it is derived at render from
`heartbeat_at` age (§3, §6).

**Charset ASSERT** (name AND session): app-side regex `^[a-z0-9][a-z0-9_-]{0,63}$`
(plan :78 — load-bearing injection guard: derived ids get inlined as literals into
C3's LIVE WHERE clauses). Two layers, deliberately: (1) **app-side pre-validation in
the dispatcher** (§8 step 2) is the authoritative, teaching layer — it fires BEFORE
any store touch and names the pattern and the reason; (2) the schema ASSERT is
defense-in-depth. The builder verifies the SurrealQL regex-ASSERT spelling live on
3.1.5 (a C1 build-time probe alongside the packet's sequence probe); if the DDL
regex idiom misbehaves, the app-side layer alone is acceptable — record it in the
builder report, don't silently drop the ASSERT.

Hyphens are LEGAL in agent names/sessions (the plan's regex includes `-`;
config.py's slug hyphen-ban is about SurrealQL *database identifiers* — agent
names are field VALUES and derived ids are hex, so the hazard doesn't apply).

Storage models (pydantic, co-located in `agents.py`, `extra="forbid"`): all string
fields are RAW `str` — sanitisation is render-time line policy, never storage
mutation (ruling §C1-C5-AUTHORING rule 3).

### brief (node)

| field | type | constraint |
|---|---|---|
| name | string | charset ASSERT — same class as agent.name. Brief names are protocol vocabulary ('project', 'base', wave names) rendered and queried by literal; same injection posture |
| version | int | |
| body | string | trim-non-empty ASSERT (a blank standing instruction names nothing) — stored RAW/verbatim, size is warn-only (§5.2) |
| created_by | string | trim-non-empty ASSERT |
| note | option\<string\> | |
| created_at | datetime | DEFAULT time::now() (findings idiom) |

Index: UNIQUE `(name, version)` — the publish backstop (§5.1, v3: a
should-never-fire invariant guard behind the counter mint, no longer a retry
driver).
Id: `uuid.uuid5(uuid.NAMESPACE_URL, f"lore://brief/{name}/{version}").hex` —
deterministic and test-pinned. v3 consequence stated plainly: because the id
embeds the version, Python must KNOW the version before it can address the row —
this is what forces §5.1's mint/CREATE split (the version cannot be read and
consumed inside one write transaction).

**brief_counter (node — the §5.1 version mint):** ONE row per brief name
(`brief_counter:⟨name⟩`), single field `next` int DEFAULT 0, DECLARED in
`surreal_schema.py::_brief_counter_statements()` mirroring
`_finding_counter_statements` (:933) and emitted by `generate_brief_ddl()` —
never left to implicit SCHEMALESS auto-creation (REPORT-c1-builder-mint.md F2).
Per-name rows (vs `finding_counter`'s singleton) mean publishers of DIFFERENT
names never contend — same primitive, strictly better partitioning.

### briefed (edge, `agent->briefed->brief`)

TYPE RELATION SCHEMAFULL (`_define_relation_table` idiom, surreal_schema.py:454).
Fields: `via` string ASSERT IN ['register','explicit','publish'] (v7 — 'publish'
is the author's self-ack, finding #98) · `at` datetime.
Index: UNIQUE `(in, out)` — idempotent re-ack (versions are distinct brief records,
so (in,out) suffices — plan :137). Legal on ≥3.1.0 (#7061 fixed); the packet's
cascade probe is C2's, but if the UNIQUE-on-edge index misbehaves at C1 build time,
that is a STOP-and-flag, not a silent app-side substitute.

Write path: RELATE-in-TxnFragment (graph_surreal.py idiom); reads use the in/out
edge-table select idiom. Store idioms binding here (repo CLAUDE.md): CONTENT for
protected-key writes (`session` is a protected param name — never `SET session =`),
`execute_transaction` for multi-statement bodies, str(RecordID) round-trip,
CONTENT datetimes are Python datetimes.

### §0.3 Name → row resolution (every non-register action)

The plan's action table (:215-224) passes `agent=<name>` WITHOUT session on every
non-register action, but the row id is `uuid5(session:name)` — name alone cannot
compute it. RULING:

- Every action accepts optional `session=`. With it, the id is computed directly.
- Without it: `SELECT` non-retired agents `WHERE name = $name`.
  - exactly 1 → that row.
  - 0 → `UnknownAgentError` (teaching, §7).
  - \>1 (same name in two live sessions) → `AmbiguousAgentError` (teaching:
    "agent name 'x' is registered in sessions 'a', 'b' — pass session= to
    disambiguate").
- `register` REQUIRES `session` (it mints the id).

Rationale: keeps the plan's ergonomic single-param calls for the overwhelmingly
common one-session case; the ambiguous case fails loud and teaches, never guesses
(DESIGN-LAW §1.4). Retired rows are excluded from bare-name resolution so a retired
`fixer-b` never shadows a live same-named agent in another session.

---

## §1 Bootstrap — `register` before any 'project' brief exists

**RULING: legal. Registration succeeds, writes NO briefed edge, and renders an
honest notice — never an error, never a silent empty.**

- The agent row is created exactly as normal (§2); no briefed edge is written
  (there is no brief record to RELATE to — an edge to nothing is unrepresentable,
  which is the correct model: the agent has acked nothing).
- The render replaces the brief section with ONE notice line (§9.1 grammar):
  `no 'project' brief published yet — work from your spawn brief; re-check with lore_comms action=brief_get`
- Once a 'project' brief exists, the agent shows as **unbriefed** (§5.3) in
  coverage/fleet until it acks (explicitly, or via a re-register).

Rationale: register-first is the protocol cornerstone C4 teaches every spawned
agent; a hard error here would train agents (and leads) to skip or re-order
registration, and would hard-couple fleet start to publish order. The notice keeps
the miss taught (§1.4) and the lead's smoke flow (publish at smoke time) legal in
either order.

## §2 Idempotent re-register (same uuid5 id)

Field disposition on a `register` call that finds an existing row:

| field | disposition |
|---|---|
| name, session | identity — immutable by construction (they ARE the id) |
| registered_at | **write-once** — never touched again |
| role | **write-once** — a differing value is `AgentIdentityConflictError` (teaching error, §7); an equal value is fine |
| spawned_by | **write-once** — same rule as role |
| model | mutable — overwritten when provided, kept when omitted |
| task_id | mutable — overwritten when provided, kept when omitted |
| status | **reset to `active`** unconditionally (a registering agent is demonstrably alive) — EXCEPT from `retired`, which is terminal: re-register of a retired name is `RetiredAgentError` (teaching: respawns register a FRESH name — comms-research rule #4) |
| heartbeat_at | touched (= now) |
| last_note, checkpoint | untouched by register |

A re-register also **re-acks the head 'project' brief** (a new briefed edge if the
head moved since the first ack; the UNIQUE(in,out) no-op if it didn't), `via=register`.

The render's first line says `re-registered` (not `registered`) and names the
original registration age (§9.1) — an honest signal that the name already existed,
so an accidental name-collision is visible to the caller instead of silently
absorbed.

Rationale: idempotence serves the legitimate cases (dropped connection retry; an
agent defensively re-registering after a long quiet stretch). The role/spawned_by
mismatch check is the tripwire for the ONE hazard idempotence would otherwise hide:
a lead reusing a name for a *different* agent, which silently merges two agents'
state — the exact misrouting class the never-reuse rule exists for.

## §3 Agent status state machine

Stored domain: `active` · `idle` · `input_required` · `retired`.
**`orphaned`/`STALE` is DERIVED at render time** from `heartbeat_at` age >
`comms.stale_heartbeat_s` (§4) and is NEVER stored, NEVER a legal `status=` value
(passing it is a teaching error naming the derivation).

Legal explicit edges (via `heartbeat(status=…)`; app-enforced in `agents.py` as a
`LEGAL_AGENT_TRANSITIONS: frozenset[tuple[str, str]]` — the tasks.py:119 idiom):

```
active          -> idle | input_required | retired
idle            -> active | input_required | retired
input_required  -> active | retired
retired         -> (terminal — no exits)
```

- Self-edges (`status=` equal to current) are legal no-ops — idempotent heartbeats
  must never error.
- `input_required -> idle` is ILLEGAL: a parked question stays visible until it is
  answered (→active) or the agent dies (→retired). Going quiet does not unpark.
- **Auto-flip:** any comms action by an `idle` agent flips it `idle -> active`
  (it is demonstrably active), UNLESS that same call carries an explicit `status=`
  (explicit wins). `input_required` NEVER auto-flips in C1 — the sanctioned
  auto-unpark is C2's drain (plan :218); C1's unpark is an explicit
  `heartbeat status=active` (an answered agent does this on its next turn).
  `retired` never auto-flips.
- Any action where the resolved agent is `retired` → `RetiredAgentError`
  (teaching; §7). Retired rows are excluded from bare-name resolution (§0.3),
  from brief-coverage denominators (§5.3), and from fleet's main rows (§6).

**Who drives what:** an agent drives its OWN row (register/heartbeat/auto-flip).
Identity is honor-system until PKT-21 (packet §Honest limits), and this spec
SANCTIONS one specific use of that: **the lead retires a dead teammate's row by
calling `heartbeat agent=<dead-name> status=retired note='<why>'`**. The heartbeat
touch on the dead row is harmless — retired rows never render a heartbeat age
(§6). This is the fleet-hygiene half of the orphaned-task SOP (plan :307-314);
without it, killed agents accumulate as stale-active zombies that C2's broadcast
fan-out would then enumerate forever.

Register always lands `active` (§2). There is no other status writer in C1.

## §4 Config knobs (repo law: no hardcoded values)

**New `CommsConfig(_StrictModel)` section on `LoreConfig`, optional with a default
instance** — the exact `BatchConfig`/`LoggingConfig` idiom (config.py:121-147):
every existing `lore.yaml` (no `comms:` block) keeps validating and gets the
defaults. Plumbed to the ledgers/AppContext at the same construction site as the
other ledgers (server.py:4660).

| field | type / default (module constant in config.py) | consumed by |
|---|---|---|
| `stale_heartbeat_s` | `PositiveInt` = `DEFAULT_COMMS_STALE_HEARTBEAT_S = 600` | §3/§6 derived STALE marker (plan's ">10 min", :309) |
| `fleet_limit` | `PositiveInt` = `DEFAULT_COMMS_FLEET_LIMIT = 20` | §6 default row cap before counted elision (house scale: `_DEFAULT_ROLLUP_LEG_LIMIT = 20`, server.py:1068) |
| `brief_body_warn_chars` | `PositiveInt` = `DEFAULT_COMMS_BRIEF_WARN_CHARS = 4000` | §5.2 publish size warn (plan's "~4k", :222) |

Stay MODULE CONSTANTS (not config), with one-line justifications the builder
copies into comments:

- `_BRIEF_PUBLISH_MAX_ATTEMPTS = 4`, `_BRIEF_PUBLISH_BACKOFF_SECONDS = 0.01`,
  `_BRIEF_PUBLISH_JITTER_SLOTS = 4`, `_BRIEF_PUBLISH_JITTER_SECONDS = 0.001`
  (briefs.py) — concurrency-mechanism tuning, the exact class findings.py keeps as
  module constants (`_REPORT_MINT_*`, findings.py:253-256); operators tune
  behavior via config, not retry mechanics. **v3:** plus
  `_BRIEF_MINT_MAX_ATTEMPTS = _BRIEF_PUBLISH_MAX_ATTEMPTS ×
  _MAX_TXN_CONFLICT_ATTEMPTS` — COMPOSED from the two existing constants (§5.1
  step 1), never a fresh literal; the jitter SLOT comes from a per-publish nonce
  (§5.1 invariant), the slot/backoff granularity constants above are unchanged.
- `BRIEF_NAME_PROJECT = "project"`, `BRIEF_NAME_BASE = "base"` (briefs.py) —
  protocol vocabulary, not tunables; C4's brief-base v3 hardcodes the same words.
- `AGENT_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")` (agents.py) —
  load-bearing injection guard (§0); making it configurable would make the
  LIVE-WHERE inlining guarantee operator-breakable.
- `_MAX_FLEET_LIMIT = 200` (server.py) — **DISPLAY cap ONLY (v4)**: bounds
  rendered fleet rows and the `limit=` re-ask clamp (DESIGN-LAW §1.2); it is
  NEVER an input to any served count (§5.3 counting law — header/coverage/skew
  counts come from `AgentRegistry.roster()`'s true aggregates).
  `_COVERAGE_NAMES_CAP = 5`, `_KNOWN_BRIEFS_CAP = 10`,
  `_SKEW_BREAKDOWN_CAP = 3` (v6 — §9.4's named version-groups), and
  `_HEARTBEAT_SKEW_NAMES_CAP = 3` (v8 — §9.2's per-name notice lines) (server.py) —
  render list caps inside teaching/coverage/skew lines (§5.3, §7, §9.4), always
  counted-elided; **v4 (audit D2): these are REAL, implemented caps with pinned
  tests — a cap named in this spec and absent from the code is itself a
  defect.**

## §5 Brief semantics

### §5.1 `brief_publish` — counter-row version mint under the hot-row law (§5 DESIGN-LAW) — REWRITTEN v3

(v1/v2 prescribed read-max-then-CREATE with row-id-derived jitter — that
prescription was the defect; see CHANGELOG and REPORT-c1-builder-mint.md §2.
The contract pins 8-WAY publish contention (`_CONCURRENT_PUBLISHERS = 8`); any
mechanism that yields at most one winner per retry round cannot converge and is
out.)

**Mechanism (two steps, deliberately split):**

1. **MINT** — the version comes from a per-NAME counter hot row, the
   `findings.py::_apply_mint` primitive keyed by name instead of a singleton:
   `UPSERT type::record('brief_counter', $name) SET next = (next ?? 0) + 1
   RETURN AFTER` — atomic, hands every racer a DISTINCT consecutive version with
   no re-read and no losers by construction. First publish of a name mints v1
   (`?? 0` + the declared `DEFAULT 0`, §0). Runs on the single-statement `_query`
   seam, so it does NOT inherit `execute_transaction`'s internal conflict
   absorption and must absorb the engine-level half itself: bounded retry to
   `_BRIEF_MINT_MAX_ATTEMPTS = _BRIEF_PUBLISH_MAX_ATTEMPTS ×
   _MAX_TXN_CONFLICT_ATTEMPTS` (4×5 = 20 — the composed worst case every other
   ledger write reaches implicitly via the shared seam; composed from the two
   existing constants, never a fresh magic number), retrying ONLY on the shared
   classifier's `_ERROR_CLASS_RETRYABLE_CONFLICT` label, with backoff jitter
   derived from a **per-publish nonce**.

   **INVARIANT (generalizable — the law v1/v2 violated): a retry's
   jitter/backoff de-synchronisation source must be unique per RACER, never
   derived from the contended row's identity.** `uuid5(name, version)` is
   identical for every racer contending for the same version — jitter derived
   from it makes all losers sleep the same duration and re-collide in lockstep.
   `findings.py`'s jitter works because `finding_id` is unique per REPORTER;
   any future hot-row mint must use a per-caller/per-call source (a nonce, a
   caller id), and its contract test must pin ≥8-way contention, not 2-way.

2. **CREATE** — `brief:⟨uuid5(name:version)⟩` CONTENT {…} with the minted
   version, **plus (v7, finding #98) the publisher's SELF-ACK briefed edge
   (`via='publish'`, at=now) RELATE'd in the SAME `execute_transaction`
   fragment** — one atomic write, never a second separately-failable call: a
   rejected CREATE rolls back brief AND edge together (no author acked to a
   brief that doesn't exist; no brief whose author reads as a straggler). The
   split is FORCED by the §0-pinned id recipe (Python must know the
   version to address the row) and by `execute_transaction` returning no values.
   A collision here is impossible by construction, so the CREATE carries **no
   retry at all**: any rejection is real (ASSERT violation, coercion, …) and
   raises loudly on first occurrence — and the §5.1 compensating release then
   runs exactly as before.

**Compensating release (closes the gap the split opens):** a rejected CREATE
burns no version — `_release_version` issues a GUARDED decrement
(`SET next -= 1 WHERE next = $version`), a no-op if another racer already took
the next number, so two publishers can never be handed the same version by a
release (the guard, not luck). The release is best-effort BY DESIGN: its own
failure is logged and swallowed so it can never mask the real rejection, which
propagates untouched. (Receipted: a blank-body rejection raises with CREATE
attempted exactly once, and the NEXT publish shows no version gap —
REPORT-c1-builder-mint.md §4.2.)

**Backstop:** the UNIQUE `(name, version)` index stays — no longer a retry
driver, it is the should-never-fire invariant guard that turns any future mint
regression into a loud duplicate-index error instead of a silent double-version.

Concurrent publishes of the same name are NOT an error: all land, with distinct
consecutive versions, order arbitrary — the render's version number is the
authority on who got what. Publishers of DIFFERENT names touch different counter
rows and neither collide nor serialise (§0 brief_counter).

Failure posture unchanged: `SurrealConnectionError` and every rejection outside
the classified retryable-conflict label propagate immediately, never retried
(the `_apply_mint` posture, verbatim — and narrower than v2's words: the retry
is label-gated, never a blanket `except SurrealStoreError`).

### §5.2 Body policy

Bodies are stored RAW and round-trip verbatim (render via `render_fenced` ONLY —
§9). Trim-non-empty ASSERT rejects a blank body (teaching error). Size is
**warn-only, never reject**: a body > `brief_body_warn_chars` adds one render line
(§9.4) — briefs are standing instructions and a hard cap would truncate or bounce
legitimate law; the warn line teaches the doc+pointer idiom instead.

### §5.3 Head, coverage, skew — one vocabulary, defined once

- `head(name)` = the row with max version for `name`.
- `acked(agent, name)` = max version of `name` the agent has a briefed edge to;
  **unbriefed** = no edge to any version of `name`.
- `skew(agent, name)` = `head - acked` (only meaningful > 0; unbriefed renders as
  its own word, never as a fake number).
- **Coverage denominator** = non-retired agents (`active`+`idle`+`input_required`).
- **Scoping law (v2 — mechanically unambiguous):** a coverage/skew count scopes to
  a session **iff the call carried an EXPLICIT `session=` param**; otherwise it is
  fleet-wide (all sessions). The caller's identity-resolved session (§0.3) NEVER
  implicitly scopes a count — identity resolution and render scoping are separate
  concerns. The label always agrees with the count (§1.3): scoped ⇒ the line
  carries `(session X)`; unscoped ⇒ no session tag. Applies uniformly wherever
  coverage/skew renders: §9.3's coverage line and §9.4's skew line.
- **Roster plumbing (v4-precise):** the roster is ALWAYS read from the agent
  registry and HANDED to `BriefLedger.coverage(active_agents=…)` — the brief
  ledger never queries the agent table itself (one roster definition, one owner).
  The source is **`AgentRegistry.roster(session=None) -> FleetRoster`** — a NEW,
  explicitly **row-UNLIMITED** read returning a lightweight projection, never the
  display-capped fleet row query: `members` (the COMPLETE non-retired membership
  in scope — id, name, status, heartbeat_at; no render fields) +
  `status_counts` (true per-status counts incl. `retired`, one aggregate GROUP BY
  query). Coverage and skew receive `roster.members` — complete, not a window.
  (A projection of the whole fleet is bounded by fleet size — tens to hundreds —
  and is cheap; what is NEVER acceptable is counting a capped window and labelling
  it as the fleet.)
- **Counting law (v4 — general, for every current and future comms count):**
  **a served count is computed over the WHOLE set its label claims to describe,
  or the line names the sample explicitly — never a silently-capped window.**
  Display caps (`_MAX_FLEET_LIMIT`, `limit=`) bound ROWS RENDERED, never the
  numbers served beside them. A count and its label must agree at every N
  (§1.2/§1.3); "205 agents — 200 active" self-contradicting in one line is the
  canonical violation.
- **Version-naming corollary (v6 — finding #96):** **a render may only name a
  version that EXISTS** — read from a stored brief row or a stored briefed
  edge's target, never arrived at by arithmetic (`version − 1` is exactly how
  `v0`, a version that never existed, reached a served line). "Never acked" is
  its OWN state and renders as its own word (`unbriefed`) — it is never
  approximated by a number, never by version−1, never by `v0`. Litmus: any
  version a reader could not `brief_get` is a fabricated fact.
- **Mechanism-promise corollary (v8 — instances 8/9/10):** **a served line may
  only promise a mechanism that will actually RUN for the input it is
  describing.** A promise that is true for one input class ('project') and
  rendered for all of them is a fabricated mechanism for every other input.
  Litmus: *if the reader — or the agent the line describes — acted on this
  line's promise (waited for the heartbeat, ran the taught command with its
  DEFAULTS, re-ran with the suggested limit), would the promised thing actually
  happen for THIS input?* Corollary of the litmus: a taught command whose
  DEFAULT arguments resolve to a different object than the line is about (the
  TENTH: bare `brief_get` defaulting to 'project' under a 'wave9' line) fails
  it. Every mechanism-referencing line is swept in §9.7; new lines join that
  table or state why they promise nothing.
- **Subscription (v8 vocabulary):** `subscribed(agent, name)` = the agent has
  ≥1 briefed edge to ANY version of `name` (acking = subscribing; #98's
  publish self-ack subscribes an author to its own brief). `'project'` is
  UNIVERSALLY subscribed — every agent owes the project law and register
  serves it, so even project-unbriefed agents get notices. Non-project names
  nag ONLY subscribers: an agent that never acked `wave9` is not behind on it,
  it is simply not a party to it (C1 has no other subscription signal; if a
  richer model ever lands, it replaces this definition in ONE place — here).

Where each surfaces in C1 (all four, exactly):

| surface | what renders |
|---|---|
| `heartbeat` | notice lines when skew>0 or unbriefed for 'project', PLUS one per behind SUBSCRIBED non-project name (v8, capped — §9.2); silent when current — a no-news heartbeat stays one line |
| `brief_get name=X` | coverage line for X: who is behind/unbriefed, counted-capped (§9.3) |
| `brief_publish name=X` | consequence line: how many non-retired agents are now behind (§9.4) |
| `fleet` | per-row 'project' ack: `project v4` / `project v4 (head v5)` / `project unbriefed` (§9.6) |

'project' rides heartbeat and fleet universally (the standing per-project law
every agent must track). **v8:** heartbeat ADDITIONALLY reports skew for every
brief name the agent is SUBSCRIBED to (§5.3 subscription — has acked before)
whose head has moved past its ack; unsubscribed non-project names never nag.
Fleet's brief column remains 'project'-only (labelled `project`, §9.6);
per-name coverage stays on `brief_get`/`brief_publish`.
Register auto-acks head 'project' (`via=register`) so a fresh agent is born
current — its render carries the receipt line to echo (§9.1). **Publish
self-acks its author (`via=publish`, v7 — finding #98), in the same transaction
as the brief row (§5.1 step 2)**: the author has by construction read what it
wrote, so it is never a straggler on its own brief; skew/coverage need no
carve-out — the author is excluded by an ORDINARY stored head-ack, and a
re-publish by a different author leaves the previous author normally
behind-at-its-old-version.

### §5.4 `brief_get` misses and `brief_ack` legality

- `brief_get name=<unknown>` → `UnknownBriefError`, teaching: names the known
  brief names (sorted, capped `_KNOWN_BRIEFS_CAP`, counted) — or, when NO briefs
  exist at all, says so and names `brief_publish` as the next move.
- `brief_get` always serves the HEAD version (no version param in C1 — reading
  history is a PKT-23/C5 growth point).
- `brief_ack name=X version=V`:
  - (X, V) exists, V == head → edge written `via=explicit`; render `acked … (head)`.
  - (X, V) exists, V < head → **LEGAL, recorded** — the agent is recording the
    truth of what it read; forcing head-only acks would falsify the ledger. The
    render carries the honest catch-up notice (§9.5). Skew math (§5.3) already
    counts it as behind.
  - (X, V) does not exist (V > head, V ≤ 0, or unknown X) →
    `UnknownBriefVersionError` teaching the real head (or `UnknownBriefError`).
  - Re-ack of an already-acked (agent, X@V) → idempotent no-op via UNIQUE(in,out);
    render says `already acked` (§9.5). The RELATE must tolerate the duplicate-
    index rejection as success (check-then-relate inside the txn, or classify the
    duplicate as the no-op signal — builder's choice, pinned by the idempotence
    test either way).

## §6 `fleet` in C1

Params: `agent` (caller — heartbeat-touched like every action) · `session?`
(filter; omitted = ALL sessions) · `limit?` (default `comms.fleet_limit`, clamped
to `_MAX_FLEET_LIMIT`).

**Columns (fixed order — C2/C3 APPEND, never reorder):**
`name · [status(+⚠ STALE)] · hb <age> · role · model? · task? · project <ack> · note?`
(v8: the ack column is labelled `project` — it is and stays the 'project' ack
only; an unqualified `brief` under-specifies its set now that non-project
briefs are first-class. Per-name matrices are PKT-23.)

- STALE = heartbeat age > `stale_heartbeat_s`, derived at render, appended inside
  the status bracket (`[active ⚠ STALE]`). Never stored (§3).
- project-ack cell renders per §5.3 (v8: labelled `project`, not `brief` —
  finding-#99 label law applied prospectively): `project v5` (current) /
  `project v4 (head v5)` (behind) / `project unbriefed` / omitted entirely when
  no 'project' brief exists yet (bootstrap-honest: nothing to be skewed
  against).
- `model`/`task`/`note` cells render only when set (no `-` placeholders — context
  density, §1.1). `note` is `last_note`, sanitised, LAST cell so a long note never
  displaces structure.
- Ordering: `input_required` rows first (parked questions are the actionable
  signal), then `active`, then `idle`; within a group, most-recent heartbeat
  first. When >1 session is in scope, group by session under a per-session header
  line rather than interleaving.
- **Retired rows are elided to ONE counted trailer** (`+K retired`) — never
  rendered as rows in C1 (an `include_retired` re-ask is a growth point;
  the trailer keeps the elision honest per §1.2/§1.4).
- **Row elision:** rows beyond `limit` → counted line teaching the re-ask with an
  honest, clamped value (§9.6). Elision cuts from the BOTTOM of the sort order
  (idle/oldest first out) so parked and freshest-active rows always survive.
  **v4:** the elision count `k` = (true in-scope non-retired total − shown), from
  the roster aggregates — never from a second capped fetch. When the re-ask can
  still show more (`shown < _MAX_FLEET_LIMIT`), render the re-ask variant; when
  the display cap itself is what elides (`shown == _MAX_FLEET_LIMIT`), the re-ask
  is a dead end — render the cap-disclosure variant instead (§9.6). Caps are
  never dead ends AND never false promises.
- Empty result: `no agents registered (session <s>)` / `no agents registered` —
  an honest empty, never a bare blank. **v7:** this variant fires ONLY when the
  in-scope registry has no rows of ANY status; all-retired is NOT empty — it
  renders the zeroed non-retired header + the true `+K retired` trailer (§9.6).
- `limit` validation (v7, finding #97): `ge=1` at the tool boundary — `limit=0`
  or negative is a TEACHING ValueError naming the valid range
  (`1..{_MAX_FLEET_LIMIT}`); a value above `_MAX_FLEET_LIMIT` CLAMPS to the cap
  (§1.2 honest clamping — the §9.6 cap-disclosure elision line then discloses
  what the clamp withheld). Never a silent partial render from a nonsense
  bound.
- **Header counts are TRUE counts (v4 — the audit-D1 fix, stated per number):**
  the header's total AND its per-status segments all come from
  `AgentRegistry.roster().status_counts` (one aggregate query over the whole
  in-scope non-retired set). At N ≤ cap and at N > cap the header is identical
  in meaning: it describes the FLEET, and its segments always sum to its total.
  The rendered ROW LIST is the only thing the cap touches. The retired trailer's
  `+K retired` is likewise the true aggregate. It is a spec violation for any
  header/trailer number to be derived from `len()` of the display rows.

NOT in C1 (no tables): unread/unacked counts, directive aging, parked-question
bodies, orphan-impact (`blocks` traversal). See §FORWARD-COMPAT.

## §7 Error taxonomy — typed, and every miss teaches

House split (tasks.py precedent): **caller/shape errors = `ValueError` raised in
the dispatcher** (FastMCP surfaces them as tool errors); **domain errors = typed
`RuntimeError` subclasses raised in the ledgers** and allowed to surface unchanged
(server.py:3130-3133 idiom).

Dispatcher `ValueError`s (server.py):
- unknown action → `unknown comms action 'x'; valid actions are [register, heartbeat, brief_get, brief_publish, brief_ack, fleet]` (rendered from `_COMMS_ACTIONS` keys — one source of truth).
- missing required arg → `_require_arg` grammar (server.py:1100): `the 'session' argument is required for action='register'`.
- foreign param → strict-param law (server.py:3144 grammar): `'version' applies only to action='brief_ack' — omit it for 'heartbeat'`.
- charset violation (name/session/brief-name) → teaches the pattern AND the why:
  `agent name 'Fixer B!' does not match ^[a-z0-9][a-z0-9_-]{0,63}$ — names are inlined into store queries and must stay in the safe charset`.
- `status='orphaned'` (or any non-domain status) → teaches the domain + the
  derivation: `'orphaned' is derived from heartbeat age at render time, never set; legal statuses: active, idle, input_required, retired`.

`agents.py` — `AgentRegistryError(RuntimeError)` base:
- `UnknownAgentError` — `agent 'x' is not registered — every comms call requires a prior 'register'; non-retired agents: a, b, c (+2 more)` (names capped `_COVERAGE_NAMES_CAP`, counted; the `(+K more)` remainder is the TRUE non-retired total, never a display-capped `len()` — §5.3). **v5 (finding #95): the label was `active agents:` and it LIED about its set** — the list and the count are the NON-RETIRED partition (active + idle + input_required; retired excluded). The count agreed with the list, so no number lied, but the LABEL meant something other than it said, and this is a teaching error an agent reads to decide who exists — told "active agents", it may route work to a parked teammate. `non-retired agents:` is the vocabulary the rest of this surface already uses for exactly this set (§9.3 coverage, §9.4 skew), so the label now agrees with the code AND its sibling renders. (`registered agents:` was rejected: a RETIRED agent is still registered, so it would be the same label-vs-set mismatch in a new coat.) **The general law this is an instance of: a served label must name the set it actually describes — §5.3's counting law applies to the WORDS beside a number, not just the number.** Fired by the dispatcher's uniform touch (§8) — one site.
- `AmbiguousAgentError` — §0.3: names the candidate sessions, teaches `session=`.
- `AgentIdentityConflictError` — §2: `agent 'fixer-b' is already registered with role 'builder' (you sent 'auditor') — names are never reused; register a fresh name (e.g. 'fixer-b2')`.
- `RetiredAgentError` — §2/§3: `agent 'fixer-b' is retired (terminal) — respawns register a fresh name`.
- `IllegalAgentStatusError` — §3 illegal edge: `illegal status transition input_required -> idle for 'fixer-b'; legal from input_required: active, retired`.

`briefs.py` — `BriefLedgerError(RuntimeError)` base:
- `UnknownBriefError` — §5.4: known names, capped+counted — **v4 (audit D2): a
  REAL implemented cap, exact grammar** `unknown brief 'x' — known briefs: base,
  project, wave7 (+4 more)`: sorted, first `_KNOWN_BRIEFS_CAP` names, counted
  remainder rendered only when >0; or `no briefs published yet — lore_comms
  action=brief_publish creates 'project' v1`. An unbounded name dump in a
  teaching error is the same context blowout the render caps exist to prevent.
- `UnknownBriefVersionError` — §5.4: `brief 'project' has no v9 — head is v5`.

Posture: honest failure > confident-wrong (§1.3/§1.4). No comms error is ever a
bare "invalid input"; each names the offending value, the legal domain, and the
next move. Store-level failures keep the uniform launder-and-log posture
(DESIGN-LAW §13).

## §8 `_COMMS_ACTIONS` — the introspectable dispatch table

Prescribed by the render ruling §REGISTRY-MIGRATION; this is a SANCTIONED
deviation from `tasks()`'s if/elif chain (server.py:3109) — the completeness pin
needs a table to iterate.

```python
@dataclass(frozen=True)
class CommsActionSpec:
    """One lore_comms action: its handler + its accepted-parameter contract."""
    handler: Callable[..., Awaitable[Rendered]]   # unbound AppContext method
    params: frozenset[str]                        # accepted OPTIONAL params (beyond agent/session)
    required: frozenset[str] = frozenset()        # params _require_arg enforces
    requires_registration: bool = True            # register itself: False

_COMMS_ACTIONS: dict[str, CommsActionSpec] = {
    "register":      CommsActionSpec(AppContext._comms_register,      params=frozenset({"role", "model", "spawned_by", "task_id"}), required=frozenset({"session", "role"}), requires_registration=False),
    "heartbeat":     CommsActionSpec(AppContext._comms_heartbeat,     params=frozenset({"note", "status"})),
    "brief_get":     CommsActionSpec(AppContext._comms_brief_get,     params=frozenset({"name"})),
    "brief_publish": CommsActionSpec(AppContext._comms_brief_publish, params=frozenset({"name", "body", "note"}), required=frozenset({"name", "body"})),
    "brief_ack":     CommsActionSpec(AppContext._comms_brief_ack,     params=frozenset({"name", "version"}), required=frozenset({"name", "version"})),
    "fleet":         CommsActionSpec(AppContext._comms_fleet,         params=frozenset({"limit"})),
}
```

Module-level in server.py, defined after `AppContext` (unbound-method references —
same file, no import cycle). `agent` and `session` are universal (every action;
§0.3) and are therefore NOT re-declared per-spec. This is the ruling's
`_COMMS_ACTIONS: dict[str, handler]` with the value widened to a frozen spec
(handler + declared params) — the keys and the iterate-the-table pin contract are
exactly the ruling's; the widening is what makes the param-honesty pin possible.

**Dispatch algorithm** (`AppContext.comms(...)` — the single flow, in order):

1. `action not in _COMMS_ACTIONS` → ValueError listing the keys (§7).
2. Charset-validate `agent` (+ `session`/`name` when present) — before ANY store touch.
3. Strict-param law: every provided (non-None) param must be in
   `spec.params | spec.required | {"agent", "session"}` → else the §7 foreign-param
   ValueError. Then `_require_arg` each `spec.required`.
4. **Uniform heartbeat touch** — for `spec.requires_registration`: resolve the row
   (§0.3), raise `RetiredAgentError` if retired, else one UPDATE stamping
   `heartbeat_at = time::now()` + the §3 idle→active auto-flip (skipped when
   `action == "heartbeat"` carries an explicit `status` — explicit wins). An empty
   UPDATE result IS the `UnknownAgentError` — existence-check and touch are one
   statement, one site, mitigation #7 for free (plan :209-211).
5. `return await spec.handler(self, **narrowed_kwargs)`.

**Why the touch lives in the dispatcher** (not a decorator, not per-handler): a
per-handler touch is the forgotten-wrap defect class P8d catalogued — N sites, no
gate; a decorator hides the call from straightforward AST/type inspection and adds
nothing over one line in the one flow all six actions already share. One site,
one test, uniform by construction.

**Pins the builders wire (test-side):**
- Exact-set: `set(_COMMS_ACTIONS) == {"register", "heartbeat", "brief_get", "brief_publish", "brief_ack", "fleet"}` (grows deliberately in C2/C3).
- Completeness: `assert_actions_covered(_COMMS_ACTIONS, C1_RENDER_CASES, exemptions={})` (test_render_seam_pins.py:535 — default FAIL; §10).
- Param-honesty: every name in every spec's `params | required` appears in the
  `lore_comms` tool wrapper's signature (a drifted table is caught, not shipped).
- Plus the four existing structural pins the packet's C1 row names (exact-set
  14→15, dead-name scan, instructions pin teaching lore_comms, `_MUTATING_TOOLS`
  gains lore_comms) and `_COMMS_TOOL_ANNOTATIONS` mirroring
  `_TASK_TOOL_ANNOTATIONS` (server.py:5458 — mutating, non-idempotent).

## §9 Render spec — exact grammars, authored ONLY on render.py verbs

Global rules (ruling §C1-C5-AUTHORING, restated as law for the contract tests):
every comms render path (`AppContext.comms`, every `_render_comms_*` helper, every
`_COMMS_ACTIONS` handler) is typed `-> Rendered`; templates and join-separators are
INLINE STRING LITERALS; one logical line per `render_line`; newlines ONLY via
`render_compose`; agent free text crosses as `sanitise_line(x)`/`safe_str(x)` at
the callsite — uniformly, INCLUDING charset-ASSERTed names and closed-vocab
statuses (a no-op wrap beats an exemption story); brief bodies via `render_fenced`
ONLY, verbatim; counts/versions/sizes are `int`s straight into `render_line`.

Derived text that is not agent-controlled (heartbeat ages, the `⚠ STALE` marker)
still crosses as `safe_str(...)`/literal template branches — no third category.

**Precedence (v6):** §0–§8 are the LAW; §9's grammar blocks and worked code are
INSTANCES of it. Where a grammar block and a law section disagree, **the law
governs**: the builder implements the law-conforming render and FLAGS the
grammar block as a spec defect in its report — this precedence rule is itself
spec text, so applying it is not an improvised design decision (and per the repo
adversary law, two available readings is an escalation signal, not a choice to
make silently). v6 exists because §9.4 contradicted §5.3 and the grammar half
got built.

Ages render via one helper: `_render_age(delta_seconds: int) -> SafeLine` returning
`safe_str(...)` of `57s` / `14m` / `3h` / `2d` (largest unit, one unit, no
padding). Builders pin its unit boundaries (`<120s → s`, `<120m → m`, `<48h → h`,
else `d`).

### §9.1 register

```
registered fixer-b (session wave7, role builder) — status active
brief 'project' v5 (published 2h ago by lead) — ack recorded (via register)
````fenced body, verbatim````
echo in your report: brief project v5 read
```

- Line 1 template: `"registered {name} (session {session}, role {role}) — status active"`.
  Re-register variant (§2): `"re-registered {name} (session {session}, role {role}) — status active (first registered {age} ago)"`.
- Line 2 + fence + receipt line render ONLY when a 'project' brief exists; the
  receipt-line grammar `brief project v{version} read` is C4's brief-base v3
  receipt (plan :304) — pin the exact words now so C4 doesn't have to migrate them.
- Bootstrap variant (§1): lines 2-4 replaced by
  `"no 'project' brief published yet — work from your spawn brief; re-check with lore_comms action=brief_get"`.
- NO unread/unacked counts in C1 (DEVIATION D1).

Worked shape (the style the ruling's drain sketch sets; the fence is the brief
body's ONLY route):

```python
def _render_comms_register(self, agent: AgentRow, brief: Brief | None, *, re_registered: bool, registered_age_s: int) -> Rendered:
    if re_registered:
        head = render_line(
            "re-registered {name} (session {session}, role {role}) — status active (first registered {age} ago)",
            name=sanitise_line(agent.name), session=sanitise_line(agent.session),
            role=sanitise_line(agent.role), age=_render_age(registered_age_s),
        )
    else:
        head = render_line(
            "registered {name} (session {session}, role {role}) — status active",
            name=sanitise_line(agent.name), session=sanitise_line(agent.session),
            role=sanitise_line(agent.role),
        )
    if brief is None:
        return render_compose(head, render_line(
            "no 'project' brief published yet — work from your spawn brief; "
            "re-check with lore_comms action=brief_get"))
    return render_compose(
        head,
        render_line(
            "brief '{name}' v{version} (published {age} ago by {author}) — ack recorded (via register)",
            name=sanitise_line(brief.name), version=brief.version,
            age=_render_age(brief.age_seconds), author=sanitise_line(brief.created_by),
        ),
        render_fenced(brief.body),
        render_line("echo in your report: brief project v{version} read", version=brief.version),
    )
```

### §9.2 heartbeat

```
heartbeat fixer-b — status active
brief 'project' v5 is head — you acked v4; catch up: lore_comms action=brief_get
brief 'wave9' v3 is head — you acked v1; catch up: lore_comms action=brief_get name='wave9'
```

- Line 1: `"heartbeat {name} — status {status}"` — status AFTER any explicit
  change or auto-flip (the render reports the world as it now is). A recorded
  note is not echoed (fleet is its render surface; echoing would double every
  heartbeat's size for no decision value — §1.1).
- Line 2 only when skew>0 (`"brief 'project' v{head} is head — you acked v{acked}; catch up: lore_comms action=brief_get"`)
  or unbriefed-with-head-existing (`"you have not acked brief 'project' (head v{head}) — lore_comms action=brief_get"`).
  These two project lines are BYTE-STABLE from v1 (bare `brief_get` is correct
  here — its default IS 'project').
- **Subscribed-name skew lines (v8 — the generalized mechanism, finding-#96
  audit instance NINE):** after the project line, ONE line per non-project
  brief name the agent is subscribed to (§5.3) with `acked < head`, ordered
  skew-descending then name, capped at `_HEARTBEAT_SKEW_NAMES_CAP`:
  `"brief '{name}' v{head} is head — you acked v{acked}; catch up: lore_comms action=brief_get name='{name}'"`
  (the teach carries EXPLICIT `name=` — the mechanism-promise litmus: a bare
  `brief_get` here would read 'project', not this brief). Remainder collapsed
  counted: `"behind on {k} more briefs: {names} — brief_get each by name"`,
  names capped `_COVERAGE_NAMES_CAP` + `(+{j} more)`. UNSUBSCRIBED non-project
  names are NEVER mentioned — deliberate (§5.3 subscription), not an omission.
  Mechanism read: the agent's briefed edges grouped by name (max acked) +
  heads for exactly those names — one bounded query pair; `BriefLedger` owns
  it (the registry hands only the agent identity).
  Fully current (or nothing subscribed/published) ⇒ one-line render. NO unread
  count in C1 (D1).

### §9.3 brief_get

```
brief 'project' v5 (published 2h ago by lead)
````fenced body, verbatim````
coverage: 3/5 non-retired agents at v5; behind: fixer-b (v4), scout-c (unbriefed) (+0 more)
```

- Header template mirrors §9.1 line 2 minus the ack clause.
- Coverage-full variant: `"coverage: all {n} non-retired agents at v{version}"`.
- Behind-list: capped at `_COVERAGE_NAMES_CAP`, counted `(+{k} more)` only when
  k>0; each entry `name (vN)` or `name (unbriefed)` — names sanitised, assembled
  with `render_join(", ", parts)`.
- Counts (v4 — audit D1): the numerator, denominator, and behind-remainder `k`
  are computed over the COMPLETE in-scope membership
  (`AgentRegistry.roster().members` → `BriefLedger.coverage(active_agents=…)`,
  §5.3) — identical meaning at N ≤ `_MAX_FLEET_LIMIT` and N > it; no display cap
  is ever an input. `_COVERAGE_NAMES_CAP` bounds NAMES SHOWN only.
- Session scope (v2 — the §5.3 scoping law, restated mechanically): the call
  carried an explicit `session=` param ⇒ roster = non-retired agents of THAT
  session, line template `"coverage (session {session}): …"`; no explicit
  `session=` ⇒ roster = ALL non-retired agents across sessions, line template
  `"coverage: …"` (no tag). The caller's own session — including one resolved
  during §0.3 identity lookup — never scopes coverage by itself. Both variants
  are live: an explicit-session call MUST render the tag, a session-less call
  MUST NOT. (Consequence for the tool layer: the `session` argument does double
  duty on `brief_get` — identity disambiguation AND coverage scoping — and must
  flow THROUGH to the coverage roster + render, never be consumed by identity
  resolution alone.)

### §9.4 brief_publish

```
brief 'project' v6 published by lead
skew: 4 non-retired agents behind head v6 — 3 at v5, 1 unbriefed; surfaces at their next heartbeat
⚠ body 5210 chars exceeds the 4000-char warn threshold — briefs are standing instructions; prefer a doc + pointer
```

- Line 1: `"brief '{name}' v{version} published by {publisher}"`.
- First-version variant (v8 — audit instance EIGHT, ratifying the contract's
  mutation-proven fix): TWO name-conditioned tails, because register auto-acks
  ONLY 'project' (§5.3 — the tail must not promise a mechanism that won't run):
  `name == 'project'` ⇒ `" — first version; agents ack at register"` (TRUE
  there, byte-stable); any other name ⇒ `" — first version; agents ack with
  lore_comms action=brief_ack"`. (Adding explicit name/version params to that
  teach was considered and declined — the fix is already mutation-proven as
  shipped, and `brief_ack`'s own required-arg errors teach the params.)
- **Skew line (v6 REWRITE — finding #96; replaces `"had acked v{prior} or
  older"`, which computed `prior = version − 1` and fabricated `v0` on a first
  publish, conflating behind-at-vN with never-acked):**
  template `"skew: {behind} non-retired agents behind head v{head} —
  {breakdown}{tail}"` (scoped variant per the v2 law:
  `"skew (session {session}): …"`), where **`{tail}` is one of THREE
  name-conditioned literals (v8 — audit instance NINE: the old unconditional
  `; surfaces at their next heartbeat` was true only for 'project'; under the
  v8 generalized heartbeat it is now conditioned on exactly where the
  mechanism runs, §5.3 mechanism-promise corollary):**
  1. `name == 'project'` ⇒ `"; surfaces at their next heartbeat"` — true for
     every group, unbriefed included ('project' notices are universal, §5.3);
  2. `name != 'project'` AND the unbriefed group is empty ⇒
     `"; surfaces at their next heartbeat"` — true: every behind agent is a
     prior acker, i.e. subscribed (§5.3), and subscribed skew rides heartbeat;
  3. `name != 'project'` AND the unbriefed group is non-empty ⇒
     `"; ackers see it at next heartbeat — unbriefed agents only via brief_get
     name='{name}'"` — each half true for its group (unbriefed non-project
     agents are never nagged, so the line must not promise they will be).
  Three separate `render_line` calls, one inline literal each (the AST
  template pin rejects computed templates — duplicated-call form, §9.6 NB).
  `{behind}` and `{head}` are ints —
  `{head}` is the JUST-PUBLISHED stored version, the only version this line is
  ever entitled to name outright. `{breakdown}` is `render_join(", ", groups)`
  where the groups are, in order:
  1. stored-acked version groups, DESCENDING — each `"{k} at v{n}"` where
     `v{n}` is a stored briefed-edge target (§5.3 corollary: read, never
     computed) — capped at `_SKEW_BREAKDOWN_CAP` named groups;
  2. any remainder collapsed to `"{k} at older versions"` (counted; names NO
     version);
  3. `"{k} unbriefed"` LAST, rendered only when k>0 — never-acked is its own
     group and its own word, never a number.
  Group counts SUM to `{behind}` (the §5.3 counting law applied inside one
  line). Skew line renders only when `{behind}` ≥ 1; omitted otherwise (no
  `skew: 0` noise). **v7 (finding #98): `{behind}` excludes the publisher via
  its own §5.1 self-ack — an ordinary stored head-ack, not a render carve-out —
  which makes this omission clause REACHABLE through the tool (a single-agent
  fleet publishing renders NO skew line); it is end-to-end pinned in
  §TEST SKETCH, not just render-unit-tested.**
- **First publish (v1):** no prior version exists ⇒ every behind agent is
  unbriefed by definition ⇒ the breakdown is exactly `"{k} unbriefed"` and the
  line names NO version other than head `v1`. The tail follows the v8 rule:
  'project' first publish → tail 1 (`skew: 2 non-retired agents behind head v1
  — 2 unbriefed; surfaces at their next heartbeat`); any other name's first
  publish → tail 3 (`skew: 2 non-retired agents behind head v1 — 2 unbriefed;
  ackers see it at next heartbeat — unbriefed agents only via brief_get
  name='wave9'`). Emitting `v0` — or any version without a stored row — is a
  spec violation (§5.3 corollary).
- Skew-line scoping (v2): the §5.3 scoping law applies verbatim — explicit
  `session=` on the publish call ⇒ count over that session's non-retired roster,
  template `"skew (session {session}): …"`; otherwise fleet-wide, no tag.
- Skew count (v4 — audit D1): computed over the COMPLETE in-scope membership via
  the same §5.3 plumbing as coverage (`roster().members`, never the display
  window) — identical meaning at every N.
- Warn line only past `brief_body_warn_chars` (§5.2); both numbers are ints in
  the template.

### §9.5 brief_ack

```
acked brief 'project' v5 (head)
acked brief 'wave9' v4 — head is v5; catch up: lore_comms action=brief_get name='wave9'
already acked brief 'project' v5 — no new edge
```

Three single-line variants (§5.4): head-ack, behind-ack (legal + honest notice),
idempotent re-ack. **v8 — audit instance TEN (found by the §9.7 sweep): the
behind-ack teach was a bare `brief_get`, whose DEFAULT name is 'project' — a
reader acking behind on 'wave9' and following the teach would read the WRONG
brief.** The teach now carries explicit `name='{name}'` for EVERY name,
'project' included (uniform template kills the default-resolution ambiguity
class; the one-byte-stability cost on the project fixture is taken
deliberately): `"acked brief '{name}' v{version} — head is v{head}; catch up:
lore_comms action=brief_get name='{name}'"`.

### §9.6 fleet

```
fleet (session wave7): 5 non-retired agents — 1 input_required, 3 active, 1 idle
- fixer-b [input_required] hb 2m · role builder · task 4f2a1c… · project v4 (head v5) · note: blocked on operator answer
- audit-c [active] hb 40s · role auditor · model opus · project v5
- scout-d [active ⚠ STALE] hb 14m · role scout · project unbriefed
- helper-e [idle] hb 6m · role builder · project v5
+1 more — re-run with limit=25
+2 retired
```

- Header (v7, finding #99 — aligned to the sibling vocabulary §9.3/§9.4/§7):
  `"fleet (session {session}): {total} non-retired agents — {parked} input_required, {active} active, {idle} idle"`
  (unscoped variant drops the parenthetical; zero-count segments are still
  rendered — the header is the fleet's one aggregate and fixed shape beats
  variable shape for scanning). `{total}` IS the non-retired partition and now
  says so; the `+K retired` trailer discloses the rest, unchanged.
- Row assembly: cells joined with a literal `" · "` via `render_join`; optional
  cells (model/task/note) appear only when set. task_id renders truncated to 8
  chars + `…` (`safe_str(task_id[:8])` — full ids live in lore_tasks; fleet is a
  scan surface). Status bracket: two template branches (with/without
  `" ⚠ STALE"`).
- project-ack cell (v8 rename — was `brief …`): `project v{n}` /
  `project v{n} (head v{h})` / `project unbriefed`; omitted entirely when no
  'project' brief exists (§6). The old `brief v…` byte pin flips to the new
  wording.
- Elision line (v4 — two variants, both with `k` from the true totals):
  - `shown < _MAX_FLEET_LIMIT`: `"+{k} more — re-run with limit={next}"` where
    `next = min(shown + k, _MAX_FLEET_LIMIT)` (honest + clamped, §1.2).
  - `shown == _MAX_FLEET_LIMIT`: `"+{k} more beyond the display cap ({cap})"` —
    a re-ask that cannot show more is a dead end, so the line discloses the cap
    instead of teaching a no-op.
  Retired trailer: `"+{k} retired"` — `k` is the true aggregate (§6).
- Empty (v7-precise, the #99 class one step further): the
  `"no agents registered (session {session})"` / `"no agents registered"`
  variant fires ONLY when the in-scope registry has NO rows of ANY status —
  with agents present but all retired, that line would lie ("registered" they
  are). All-retired renders the true zeroed header
  (`"fleet: 0 non-retired agents — 0 input_required, 0 active, 0 idle"`) +
  `"+{k} retired"`, no rows.

Worked row shape:

```python
def _render_comms_fleet_row(self, row: FleetRow, head_version: int | None, *, stale_after_s: int) -> Rendered:
    cells: list[SafeLine] = [
        render_join(" ", [safe_str("role"), sanitise_line(row.role)]),
    ]
    if row.model is not None:
        cells.append(render_join(" ", [safe_str("model"), sanitise_line(row.model)]))
    if row.task_id is not None:
        cells.append(render_join(" ", [safe_str("task"), safe_str(row.task_id[:8] + "…")]))
    cells.append(_brief_cell(row, head_version))          # -> SafeLine, §5.3 vocabulary
    if row.last_note is not None:
        cells.append(render_join(" ", [safe_str("note:"), sanitise_line(row.last_note)]))
    if row.heartbeat_age_s > stale_after_s:
        return render_line(
            "- {name} [{status} ⚠ STALE] hb {age} · {cells}",
            name=sanitise_line(row.name), status=sanitise_line(row.status),
            age=_render_age(row.heartbeat_age_s), cells=render_join(" · ", cells),
        )
    return render_line(
        "- {name} [{status}] hb {age} · {cells}",
        name=sanitise_line(row.name), status=sanitise_line(row.status),
        age=_render_age(row.heartbeat_age_s), cells=render_join(" · ", cells),
    )
```

(NB for the contract pair — this duplicated-call form is DELIBERATE: the Phase-0
AST template-literal pin requires `args[0]` to be an `ast.Constant`; a ternary
selecting between two literals is an `ast.IfExp` and FAILS the pin. One
`render_line` call per branch, each with a plain inline literal. Do not weaken
the pin to accept ternaries.)

### §9.7 Mechanism-promise sweep (v8) — verdict per served line, individually

Every served line that references a mechanism, swept under the §5.3
mechanism-promise litmus. Anchors are spec grammar sections (normative);
server.py lines cited where the audit supplied them (code lines drift, the
spec anchor governs). No wholesale verdicts.

| # | line (spec anchor) | mechanism referenced | runs for every input rendered under? | verdict |
|---|---|---|---|---|
| 1 | §9.1 `— ack recorded (via register)` | register auto-ack | line renders only for 'project' at register, which register did just ack | SOUND |
| 2 | §9.1/§1 bootstrap `re-check with lore_comms action=brief_get` | brief_get default='project' | line is ABOUT 'project'; default resolves to it | SOUND |
| 3 | §9.1 receipt `echo in your report: brief project v{N} read` | report echo | always available to the addressed agent | SOUND |
| 4 | §9.2 project skew notice `catch up: lore_comms action=brief_get` | brief_get default='project' | project-only line; default correct | SOUND (byte-stable) |
| 5 | §9.2 project unbriefed `— lore_comms action=brief_get` | same | same | SOUND |
| 6 | §9.2 subscribed-name notice `brief_get name='{name}'` (v8, new) | brief_get by name | name exists (its head was just read) | SOUND by construction |
| 7 | §9.2 collapse `behind on {k} more briefs: {names} — brief_get each by name` | brief_get by name | names listed are subscribed+published | SOUND |
| 8 | §9.4 first-version tail, 'project' `agents ack at register` (server.py:4695) | register auto-ack | TRUE for 'project' only — and the tail now renders ONLY there | **WAS INSTANCE 8** — fixed v8 (ratified contract fix) |
| 9 | §9.4 first-version tail, other names `agents ack with lore_comms action=brief_ack` | brief_ack | runs for any existing (name, version); v1 just minted | SOUND (the fix) |
| 10 | §9.4 skew tail (server.py:4513 read) | heartbeat skew surfacing | 'project': universal; other names: subscribed groups only | **WAS INSTANCE 9** — fixed v8 (three conditioned tails + generalized mechanism) |
| 11 | §9.5 behind-ack teach `catch up: lore_comms action=brief_get name='{name}'` | brief_get by name | pre-v8 the teach was BARE brief_get → default 'project' → wrong brief for every other name | **INSTANCE 10, found by this sweep** — fixed v8 (explicit name=, all names) |
| 12 | §9.6 elision re-ask `re-run with limit={next}` | fleet limit= | pre-v4 this was a dead-end at the cap — retroactively an instance of THIS axis; the v4 cap-disclosure variant fixed it | SOUND since v4 |
| 13 | §9.6 cap-disclosure `+{k} more beyond the display cap ({cap})` | none (discloses) | n/a | SOUND |
| 14 | §7 UnknownAgentError `requires a prior 'register'` | register | runs for any caller | SOUND |
| 15 | §7 AmbiguousAgentError `pass session= to disambiguate` | session param | exists on every action (§0.3) | SOUND |
| 16 | §7 AgentIdentityConflictError / RetiredAgentError `register a fresh name` | register | runs | SOUND |
| 17 | §7 IllegalAgentStatusError `legal from {status}: …` | heartbeat status= | every named exit is a legal edge for the named current status (§3) | SOUND |
| 18 | §7 UnknownBriefError `brief_publish creates 'project' v1` | brief_publish | runs for any registered caller | SOUND |
| 19 | §9.4 warn line `prefer a doc + pointer` | none (advice, no runtime promise) | n/a | SOUND |

**Item-4 design verdicts (mechanism-generality, each ruled):**
- **register auto-ack: STAYS 'project'-only.** An ack asserts "I read this";
  register SERVES only the project body (§9.1), so auto-acking any other brief
  would fabricate a read receipt. Law: register's auto-ack stays exactly
  coextensive with what register serves — if a future phase serves more briefs
  at register, their acks may follow the served set, never precede it.
- **heartbeat skew: GENERALIZED** (the v8 ruling) — mechanism widened rather
  than render narrowed, because passive skew delivery is this subsystem's
  point and ack-as-subscription bounds the noise with zero new schema.
- **fleet's ack column: stays 'project'-only as a COLUMN** (fleet is the
  fleet-ops scan surface; per-name matrices are PKT-23) — generality declined,
  label honesty applied instead (cell renamed `project`, §9.6).

## §10 RenderCase inventory — the completeness pin's exact input

Battery: the C1 comms test module builds its own `RenderCase` registry from
`render_injection_scaffold.py` (label families = action names —
`assert_actions_covered` matches `label.split(".", 1)[0]`), drives each render
helper with `_INJECTION_THREAT_CHARS` + `_ROW_FORGE_PAYLOAD` per field, and runs
`assert_render_injection_safe` against a benign baseline. Fenced-body cases
additionally assert fence integrity (embedded backtick runs never close the fence
early — the render_fenced sizing rule).

| case label | field under injection | render surface |
|---|---|---|
| register.name | agent name | §9.1 line 1 |
| register.session | session | §9.1 line 1 |
| register.role | role | §9.1 line 1 |
| register.brief_author | brief.created_by | §9.1 line 2 |
| register.brief_body | brief.body (FENCE case) | §9.1 fence |
| heartbeat.name | agent name | §9.2 line 1 |
| brief_get.name | brief.name | §9.3 header |
| brief_get.author | brief.created_by | §9.3 header |
| brief_get.body | brief.body (FENCE case) | §9.3 fence |
| brief_get.behind_names | behind-agent names | §9.3 coverage line |
| brief_publish.name | brief.name | §9.4 line 1 |
| brief_publish.publisher | publishing agent name | §9.4 line 1 |
| brief_ack.name | brief.name | §9.5 |
| fleet.name | agent name | §9.6 row |
| fleet.role | role | §9.6 row |
| fleet.model | model | §9.6 row |
| fleet.task_id | task_id | §9.6 row |
| fleet.note | last_note | §9.6 row |
| fleet.session | session | §9.6 header |

**Exemptions: NONE in C1** — every action renders at least one agent-controlled
field, so the pin's default-FAIL is satisfied positively across all six. (Hostile
values for charset-ASSERTed fields cannot be STORED in production; the battery
drives the render helpers/fakes directly, which is exactly the point — the render
layer must hold even if the storage ASSERT is bypassed or later relaxed. This
mirrors how the Phase-0 battery drives the task/finding row renders.)

Statuses, versions, counts, and ages are not free-text params (closed vocab /
ints / derived) — they need no RenderCase, and they still cross the seam wrapped
(§9 global rules), so nothing rides on that classification.

## §DEVIATIONS from the garden plan's letter (each with why)

- **D1 — register/heartbeat render NO unread/unacked counts in C1** (plan :215-216
  promises them). The `to`/`message` tables don't exist; rendering `0 unread`
  would be a confident-wrong claim about a subsystem that isn't there (§1.3).
  C2 adds the counts to both renders (§FORWARD-COMPAT).
- **D2 — fleet ships without unread/unacked-directive/parked-question-body/
  orphan-impact columns** (plan :224). Same reason; the §9.6 grammar fixes cell
  ORDER so C2/C3 append columns without re-litigating the line shape.
- **D3 — `_COMMS_ACTIONS` dict dispatch** deviates from the tasks()/findings()
  if/elif house idiom — prescribed by the render ruling §REGISTRY-MIGRATION (the
  completeness pin iterates the real table).
- **D4 — brief_ack of a non-head version ruled LEGAL** (plan silent): the ledger
  records what actually happened; skew math + honest notice carry the catch-up
  pressure (§5.4).
- **D5 — lead-retires-dead-agent sanctioned via honor-system identity** (plan
  silent on who drives `retired`): without it, killed agents are permanent
  stale-active zombies in every future broadcast fan-out (§3). Explicitly
  revisit-at-PKT-21 (real identity).
- **D6 — optional `session` on every action + bare-name resolution rule** (plan's
  param table implies name-only lookups, which cannot compute the uuid5 id and
  is ambiguous across sessions — §0.3).
- **D7 — agent-name index added** beyond the plan's (session, status) index
  (§0.3's resolution SELECT needs it).
- **D8 — `checkpoint` column ships but NO C1 action reads or writes it** (plan
  :84 says the column ships now; stating the zero-surface explicitly so nobody
  "helpfully" wires it early).

None of these require an operator ruling in my judgment (D1/D2 are forced by the
brief's scope line; D3 by the binding render ruling; D4-D7 are resolution of
gaps the plan leaves open, with rationale). D5 is the one an operator might
plausibly strike — flagged as such in my report.

## §FORWARD-COMPAT growth points (spec'd, NOT built)

- **register/heartbeat counts (C2):** one appended segment on §9.1 line 1 /
  §9.2 line 1 — `"… — status active · 3 unread (1 directive)"` — plus drain's
  auto-unpark taking over §3's explicit-unpark as the common path.
- **drain's brief-skew line + `_comms_footer` (C2) INHERIT the v8
  subscribed-skew read** — same §5.3 subscription rule, same per-name grammar
  family as §9.2; they must not regress to a project-only read behind a
  generic label (the instance-9 class).
- **fleet columns (C2/C3):** appended cells after `brief`: `unread {n}` /
  `directive unacked {n} ({age})`; C3 appends the orphan-impact clause on STALE
  rows (`releasing t-4f2a strands: t-9910, t-3c22` — blocks traversal).
- **fleet include_retired= / brief_get version= / brief history:** PKT-23/C5
  re-asks; the counted trailers in §6 are their teaching hooks.
- **`_COMMS_ACTIONS` grows** to +send/drain/ack/await (C2/C3) and story (C3);
  the exact-set pin is updated deliberately each phase (that's the pin working,
  not friction).
- **checkpoint workflow (C5):** column exists (§0), zero C1 surface (D8).

## §BUILD-TIME PROBES C1 inherits (packet + this spec)

1. Packet: `sequence::next()` vs `sequence::nextval()` — NOT needed by C1's
   surface (no message seq); run it anyway per the packet's C1 row so C2 isn't
   blocked on a store probe. 2. This spec: SurrealQL regex-ASSERT spelling for the
   charset fields (§0). 3. This spec: UNIQUE-on-edge behavior for `briefed`
   idempotent re-RELATE (§5.4) — the full cascade probe stays C2's.

## §TEST SKETCH (what the contract pair pins, minimum set)

- State machine: every legal edge green; every illegal edge (incl.
  input_required→idle, anything→from-retired, status='orphaned') red with the §7
  teaching text; idle auto-flip on each of the six actions; explicit-status-wins
  on heartbeat; self-edge no-op.
- Re-register: idempotence (same fields), role/spawned_by conflict, retired
  conflict, status reset, registered_at write-once, head-moved re-ack edge.
- Bootstrap: register-before-brief (no edge, notice line), then publish, then
  unbriefed skew appears at heartbeat/fleet/brief_get.
- Publish (v3): v1 first-mint; distinct consecutive versions under the PINNED
  8-way race (`_CONCURRENT_PUBLISHERS = 8` — never a 2-way stand-in); mint
  retries ONLY the classified retryable-conflict label, jitter from a per-publish
  nonce; CREATE never retried — a non-collision rejection (blank body) raises
  loudly with CREATE attempted exactly once AND the next publish shows no version
  gap (the guarded release); different names neither collide nor serialise;
  UNIQUE(name,version) backstop present as the invariant guard.
- Ack: head / behind / nonexistent / idempotent re-ack; via=register vs explicit
  vs publish (v7); NEW: an author explicitly acking its just-published version
  hits the idempotent `already acked` path (the via=publish edge exists).
- Publish self-ack (v7, finding #98): the briefed edge (via=publish, at head)
  exists after every publish; ATOMICITY pin — a rejected CREATE (blank body)
  leaves NO edge and NO brief row (same-transaction rollback) and still
  releases the version; REACHABILITY pin — single-agent fleet publishes ⇒ the
  served render contains NO skew line (behind==0 through the tool, end-to-end);
  re-publish by a different author leaves the prior author counted behind at
  its stored old version (no special-casing).
- Fleet labels (v7, finding #99): header says `non-retired agents` (byte-pinned
  with the new wording — the old `{total} agents` string must NOT appear);
  all-retired fixture renders the zeroed header + true `+K retired`, never the
  `no agents registered` variant; that variant only on a rowless registry.
- `limit` bounds (v7, finding #97): `limit=0`/`-1` → teaching error naming
  `1..cap`; `limit=cap+50` → clamped, cap-disclosure elision line renders.
- **Mechanism-promise pins (v8, instances 8/9/10 — and the anti-monoculture
  rule):** EVERY brief-grammar battery includes at least one NON-'project'
  name fixture — a `_brief()`-style factory defaulting to 'project' is the
  documented reason instances 8/9 were invisible; the contract must not
  rebuild that monoculture. Pins: (8) project first-publish tail says
  `ack at register`, `wave9` first-publish tail says `ack with lore_comms
  action=brief_ack` — both byte-pinned; (9) publish tails: project → tail 1;
  non-project ackers-only → tail 2; non-project with unbriefed → tail 3
  (byte-pinned, incl. the `name='{name}'` teach); (10) behind-ack render
  carries `name='{name}'` for EVERY name incl. 'project'; heartbeat
  generalization: subscribed-behind non-project name → notice line with
  explicit `name=` teach; UNSUBSCRIBED non-project head bump → NO mention of
  that name anywhere in the render; project-unbriefed still noticed; cap
  fixture (`_HEARTBEAT_SKEW_NAMES_CAP + 1` behind names → cap lines + counted
  collapse); END-TO-END: publish `wave9` v2 → a prior-acker's next heartbeat
  (through the real tool) surfaces `wave9` — the ninth's promise proven where
  it is made. Fleet cell: `project v…` byte pin; the old `brief v…` string
  must NOT appear.
- Fleet: ordering, STALE derivation at the exact threshold boundary, counted
  elision + clamped re-ask value, retired trailer, empty render, session scoping,
  multi-session grouping. **v4 (over-cap honesty, audit D1):** a fixture with
  N > `_MAX_FLEET_LIMIT` non-retired agents (mixed statuses + retired) pins:
  header total AND per-status segments are the true fleet counts (segments sum
  to total — the self-contradiction test); rows rendered == cap; the
  cap-disclosure elision variant renders (never a `limit=` no-op re-ask);
  `+K retired` true; brief_get coverage and brief_publish skew counted over the
  WHOLE scope at the same N (not the window) — all three numbers, one fixture.
- Teaching-error caps (v4, audit D2): with `_KNOWN_BRIEFS_CAP + 2` briefs
  published, the UnknownBrief error lists exactly the cap's worth of sorted
  names + `(+2 more)`; at ≤ cap, no counter suffix.
- **Skew-line prose pins (v6, finding #96 — the prose class zero tests
  caught):** FIRST publish with ≥1 registered-unbriefed agent — the served line
  CONTAINS `unbriefed`, does NOT contain `v0`, and names no version other than
  the head; MIXED fixture (agents at two distinct stored acked versions + one
  unbriefed) — groups descending, `unbriefed` last, group counts sum to the
  behind total; BREAKDOWN-CAP fixture (`_SKEW_BREAKDOWN_CAP + 1` distinct
  stored versions) — exactly the cap's worth of named groups + a counted
  `at older versions` collapse naming no version. These are byte-grammar
  assertions on the served string, not structure checks.
- Renders: the §10 battery (hostile fixtures per brief-base §3 — newlines +
  row-forge payload + backtick runs), `assert_actions_covered` with empty
  exemptions, exact-set pin on the six actions, param-honesty pin, every comms
  path `-> Rendered` under mypy strict (rides typecheck.sh), heartbeat-touch
  uniformity (one test: every non-register action bumps heartbeat_at; register
  sets it).
- Lifecycle (global CLAUDE.md law): registry/ledger over a dropped-and-recovered
  store connection — degradation and recovery tests, matching the existing
  ledgers' posture.
