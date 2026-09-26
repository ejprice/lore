# Packet 63c — ruling amendment 23 (sidecar-63c-2, 2026-09-26): a19a forks FK-1 (refusal-class set), FK-2 (the ghost sender), FK-3 (valid tables), FK-4

Rules `REPORT-contract-63c-i-a-a19a.md` §F (working tree). Directive: `REPORT-lead-63c.md@c0edc0f` (durable
copy; this session's lore client is still down — `Read`/`awk`, said so). Amends amendment-22 §1, §2, §3.

## FK-1 — Reading A: the derived set is what `register` can RAISE, not what the module DEFINES
- **Erratum, mine:** amendment 22 derived the reach from the wrong set — "every concrete subclass defined in
  `agents.py`" — three of which (`Unknown`, `Ambiguous`, `IllegalAgentStatus`) are unreachable from `register`
  by construction, so the pin was permanently RED on every correct build. Reach must be derived from the
  FUNCTION's raise closure, not the MODULE's class list: the same distinction as "the emitted DDL, not the
  source spelling".
- **Ruling:** the set = { c ∈ subclasses-of-`AgentRegistryError`-in-`agents.py` ∪ {base} : c is raised in the
  AST call closure of `AgentRegistry.register` }, derived at test time, coverage a checked variable BOTH ways
  (a class `register` newly raises reds by name; a fixture for a class it no longer raises reds too).
- **Two exclusions, stated in the pin so they are met deliberately:** (1) the two post-write "vanished" base
  raises are impossible-state guards, not refusals — they are excluded by the criterion "raised BEFORE the
  registry's first write" (the preflight set), otherwise the pin demands a fixture for an unreachable
  state; (2) the base's A3 mixed-pair refusal is unreachable through `comms(register)` by construction (the
  handler derives both halves from one principal) — covered at REGISTRY level by the existing amendment-4
  MP-B pins, and its comms-unreachability is a STATED BOUND with the author's trigger: *"the handler derives
  the pair from anything other than one principal"*.

## FK-2 — the ghost sender: REFUSE the message leg, name the ids, adjudicate by hand; i-a
- **The fact, measured by the author at HEAD:** a legacy message whose `sender` link names no agent row is
  stamped `owner_principal` NONE + the project scope (record links are not existence-checked, store-ref §2).
  My amendment-22 §3 derived the no-NONE-owner invariant over ONE source of a NONE `sender.owner_principal`
  (the half-pair sender) and stated it ∀ — the packet's signature miss, mine, once more.
- **Behaviour ruling (this is a design call, so it is made here, not surfaced):** a dangling sender is the
  message table's analogue of the agent table's half-pair — a store the grandfather rule's OWNED-BY-LINK
  premise does not hold for. The three precedents in this packet (multi-principal, half-pair, the E3 population)
  all resolve the same way: REFUSE, name the count and the bounded ids, adjudicate by hand. So: the message
  leg's precondition (the shared preconditions function, its message leg — ORDER-class, not store-class: a
  ghost sender does not make the agent or memory grandfather wrong, so it refuses `message` only) counts
  legacy messages whose sender resolves to no row and refuses with count + bounded ids, byte-inert, diagnosis
  "dangling sender" (never "multi-principal"; the derived diagnosis distinguishes). Rejected: skip-and-report
  leaves an honest but permanent "N unmigrated" in every report with no path to zero except the same manual
  adjudication a refusal names up front; stamping to the operator invents an owner a row never had.
- **Why i-a:** the message leg is being re-keyed in i-a (CD-1), the refusal is one more leg of the function
  i-a is building, and the alternative is landing an invariant pin known to be false on a seeded population.
  Population expected EMPTY in production (agents are never deleted — `retired` is terminal), like E3; the
  refusal branch is testable on the author's seeded ghost, so it is not a mechanism nobody can test.
- **Pins:** (a) the invariant pin as the author wrote it, ∀ reachable populations (legacy, fully migrated,
  both half-pairs) — satisfiable; (b) the ghost leg: seed one dangling-sender legacy message beside one sound
  one → `refused=True`, count 1, the ghost's id named, `SELECT *` byte-identical on `message` (the sound row is
  NOT stamped either — one statement, one verdict); (c) the invariant then holds ∀ inputs including the
  ghost, because a ghost store never gets stamped. The builder confirms dangling-link detection against the
  store reference / a test-store probe (the query shape is the builder's; the pin seeds the state).

## FK-3 — CONFIRMED: valid = {agent, memory, message, brief} (a19's `_MIGRATE_TABLES`)
Erratum: my pointer to "the production constant the five-set pin cross-checks" was a factual slip (that pin
cross-checks a test helper, nodes only, and `brief` carries no trio at i-a). Behaviour wins; the four `∀[brief]`
pins stand. The invalid probes derived from the emitted schema's table set minus the four, plus a typo, is the
right derivation.

## FK-4 — CONFIRMED as picked
PD2 lands; MP-4's wrong build is DISSOLVED by F-2 (a half-pair can no longer reach the order guard), not
killed by PD2; re-open trigger as stated (E3's narrowing lets a half-pair through).

## §W — a19a delta
| # | item |
|---|---|
| 1 | FK-1: raise-closure-derived refusal set, both-ways coverage, two stated exclusions |
| 2 | FK-2: ghost-sender refusal leg in the shared preconditions (message only); invariant ∀ incl. ghost; pins (a)–(c) |
| 3 | FK-3/FK-4: as picked |

## §E
- Two errata (FK-1's reach set; FK-2's single-source invariant), both the one-member-stated-∀ shape. The
  FK-1 one has a general form worth keeping: *derive a reach from the thing whose behaviour you pin — the
  function's raise set, the emitted artifact — never from a neighbouring inventory that merely contains it.*
