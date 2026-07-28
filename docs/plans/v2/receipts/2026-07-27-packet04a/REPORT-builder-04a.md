# REPORT-builder-04a — packet 04a, the `ENFORCED` flip + the shared unknown-agent policy

brief-base v7 read

*Every measurement below was taken **2026-07-27** on `feat/surreal-unification`, working tree at
**`bbada6a`** + the five production files listed in §1 (uncommitted — the lead commits). Live legs
ran on **spike-surreal `ws://127.0.0.1:18000` (the TEST store) ONLY**; `:18500` was never contacted.
Present-tense claims describe THAT tree; re-derive any number here before relying on it.*

---

## SUMMARY BLOCK

- **state:** done. **`50 passed, 0 failed`** on the contract; **no test file touched** (git status =
  4 modified + 1 new production module, §1).
- **GATE 1 — `uv run pytest -n auto` (FULL suite): `7134 passed, 36 skipped, 3 xfailed, 1 warning in
  190.25s`.** Wave-gate subset over the 8 named suites: `2107 passed, 33 skipped in 26.63s`.
- **GATE 2 — `./scripts/typecheck.sh`: `lorescribe OK` / `loresigil OK` / `loremaster OK` (156 files).**
- **GATE 3 — `uv run ruff check .`: `All checks passed!`**
- **MP-1 (migration LANDS)** — `ensure_ready()` on a dirty store; the group-C mutation proof fired
  **8/8 declared, EXIT=0, tree restored byte-exact** (§4).
- **MP-2 (single decision point)** — W-E killed; sharing proven by **three** mutations, all
  `EXIT=0` from an **unpiped** run (§4). ⚠ My first two runs were piped to `tail`, so `$?` was
  *tail's* — disclosed and re-run rather than reported (§4.4).
- **Teaching message** — `f"{name} ({id})"`, one string, both verbs (§3.3). Verified end-to-end
  against the real registry + real ledger (§5), which the tool-seam fakes **structurally cannot** see.
- **Removed-behaviour inventory: 11 items, each adjudicated** (§6). One is a prose choice I
  recommend the lead rule on (§6, RB-5).
- **decisions-needed: 3** — (E-1) the shared refusal drops the word *"recipient"*; (E-2) the SENDER
  door (adversary R8 / contract D-b) is still open and unruled — I did NOT close it; (E-3)
  **seven** hand-rolled `_bare_id` copies exist package-wide (pre-existing; I added none). §7.
- **Receipt pointers:** §1 diff · §2 RED→GREEN · §3 the build · §4 mutation proofs · §5 the
  end-to-end check the fakes cannot do · §6 removed-behaviour inventory · §7 escalations ·
  §8 WHAT I COULD NOT DETERMINE.

**Packages considered:** unknown-agent existence policy → in-house
`MessageLedger._reject_unknown_recipients` (READ: its body — one direct-record-access
`SELECT id FROM $ids`) → **replace by extraction into `loremaster.agent_existence`**; no library
does a store-shaped existence read against our own `agent` table · record-id decoding → the
installed `surrealdb` 2.0.0 SDK's own `RecordID` (READ: `str(RecordID)` / `.id` behaviour, probed
live, §3.2) → **replace** a hand-rolled parse with the SDK's own rendering, which is why this build
adds **no** eighth `_bare_id` copy · concrete agent identity → `loremaster.agent_ref.AgentRefLike`
(READ: the Protocol's read-only-property rationale) → **replace_with_adapter**: a 2-field frozen
dataclass beside the Protocol it satisfies, not a new abstraction · mutation proof → repo's
`scripts/mutation_proof.py` (READ: its `--expect-red` both-ways diff, its exactly-once anchor guard,
and its md5-verified content restore) → **replace** a hand-rolled break-and-look shell block ·
scratch isolation → repo's `scripts/scratch_copy.sh` (READ: its three poison modes) →
**keep_with_trigger**: NOT used, because I mutated the REAL tree with a `cp -a` content backup and
restored byte-exact (the alternative standing law allows). **Trigger:** the day a proof needs two
trees live at once, `scratch_copy.sh` is the only sound option.

---

## §1 — what changed (production only; five files)

```
$ git status --short
 M loremaster/loremaster/agent_ref.py
 M loremaster/loremaster/briefs.py
 M loremaster/loremaster/messages.py
 M loremaster/loremaster/store/surreal_schema.py
?? loremaster/loremaster/agent_existence.py
$ git diff --stat        # (the new module is untracked and not counted here)
 4 files changed, 123 insertions(+), 31 deletions(-)
```

| file | change |
|---|---|
| `store/surreal_schema.py` | `_briefed_statements` → `_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, **enforced=True**)`. `OVERWRITE` was already the verb (`_define_relation_table`) — unchanged, and it is what makes the flip LAND. Docstring gains the ENFORCED rationale + the new agent-slice ORDER DEPENDENCY. |
| `agent_existence.py` **(new)** | `UnknownAgentRowError` (the shared base) + `async reject_unknown_agents(query, agents, *, error=…)` — ONE direct-record-access read, names every missing `name (id)`. Imports neither ledger. |
| `briefs.py` | imports the shared symbol under the pinned name; `UnknownBriefAgentError(BriefLedgerError, UnknownAgentRowError)`; `publish` calls the policy **before `_mint_version`**; `ack` calls it **before the versions read**. |
| `messages.py` | imports the shared symbol; `UnknownRecipientError(MessageLedgerError, UnknownAgentRowError)`; `_reject_unknown_recipients`' body → **one delegating call** (it now decides nothing). |
| `agent_ref.py` | `+ AgentRef` — a frozen 2-field concrete `AgentRefLike`, so the brief ledger reaches the shared policy through the SAME door `send` does instead of the policy growing a second, id-only entry point. |

**No file under `loremaster/tests/` was touched. No packet, plan or reference doc was touched. No
other `REPORT-*.md` was touched. No git state was mutated.**

## §2 — RED → GREEN

```
BEFORE (tree at bbada6a):
$ uv run pytest -q loremaster/tests/test_enforced_relations.py -p no:randomly -n auto
26 failed, 24 passed in 5.42s

AFTER:
$ uv run pytest -q loremaster/tests/test_enforced_relations.py -p no:randomly -n auto
50 passed in 5.48s
```

The wave gate over **both** files the brief named plus the six neighbours — including
`test_derivation_source_unification.py`, which carries the adversary's R3 exemption guard that stops
a future author widening `DEFERRED_TO_PACKET_43`:

```
$ uv run pytest -q -n auto -p no:randomly \
    loremaster/tests/test_enforced_relations.py \
    loremaster/tests/test_derivation_source_unification.py \
    loremaster/tests/test_brief_ledger.py loremaster/tests/test_message_ledger.py \
    loremaster/tests/test_retry_seam.py loremaster/tests/test_comms_tool.py \
    loremaster/tests/test_comms_schema.py loremaster/tests/test_surreal_schema.py
2107 passed, 33 skipped, 1 warning in 26.63s
```

Full suite, because the brief asked for it (repo law otherwise reserves it for the lead at a
checkpoint):

```
$ uv run pytest -q -n auto
7134 passed, 36 skipped, 3 xfailed, 1 warning in 190.25s (0:03:10)
```

**No pin is RED.** The one warning is the pre-existing `test_retry_seam.py`
`_empty_subscription was never awaited` RuntimeWarning, unchanged by this wave.

## §3 — how each requirement was satisfied

### 3.1 MP-1 — the migration path actually LANDS

The emitter change alone is exactly W-A, the wrong build that passed the un-hardened contract
38/38: *a perfect emitter behind a migration path that never runs*. Two things make it land here,
and neither is new code:

1. **`OVERWRITE`, not `IF NOT EXISTS`.** `_define_relation_table` already emits `OVERWRITE`; the
   store reference's §1.1 RELATION-TABLE row is why (`IF NOT EXISTS` on an existing edge table is a
   MEASURED silent no-op — #107's shape). I changed the `enforced` argument and nothing about the
   clause.
2. **`BriefLedger.ensure_ready()` re-applies the whole brief slice every boot**, so the changed
   definition converges on any long-lived store. `TestTheLEDGERsOwnMigrationPathLandsTheGuard`
   drives *only* `ensure_ready()` against a dirtied old-world store — nothing applies DDL on the
   ledger's behalf — and it is GREEN.

I verified the flip is not merely emitted but **live in an engine** in three independent ways: the
dirty-store pins (`TestTheEnforcedFlipMigratesADirtyStore`), the ledger-path pin above, and the
end-to-end run in §5. A stored-DDL string diff was never used as the measurement.

### 3.2 The id derivation — D-d, closed by removing the derivation rather than repeating it

D-d cost my predecessor 130 red pins: `str(row["id"]).split(":", 1)[-1]` is right for `agent:abc`
and **wrong** for a uuid-shaped id, which the SDK renders `agent:⟨0199c4f1-…⟩`.

I did not hand-roll that parse — and I did not add an **eighth** copy of `_bare_id` either (there are
already seven, derived in §7 E-3). Instead
the policy **looks up the engine's echo against its own renderings**: it builds
`{str(RecordID(AGENT_TABLE, id)): id}` for what it ASKED about and indexes the returned rows by
`str(row["id"])`. Both sides are produced by the same SDK function, so the match is symmetric **by
construction** and there is no derivation left to get wrong.

Probed live on spike-surreal 3.2.1 (2026-07-27), four id shapes incl. two uuid-shaped, with a
ghost id as the negative control — `rows returned: 4 of asked: 5`:

```
str(raw)='agent:registered_agent_23daaad2…'          str(raw.id)='registered_agent_23daaad2…'
str(raw)='agent:⟨a2589d14-a456-40f7-9043-d14ad2ec9eca⟩'  str(raw.id)='a2589d14-a456-40f7-9043-d14ad2ec9eca'
str(raw)='agent:⟨0199c4f1-7d2a-7b3c-9c4d-5e6f70819293⟩'  str(raw.id)='0199c4f1-7d2a-7b3c-9c4d-5e6f70819293'
str(raw)='agent:simple'                              str(raw.id)='simple'
SYMMETRIC-STR match -> True    unmatched renders: []    DOT-ID match -> True
RecordID eq/hash -> True False       <-- ⚠ RecordID is UNHASHABLE; never put one in a set
```

The canary D-d names is green: `test_message_ledger.py` + `test_brief_ledger.py` are inside the
2107-pin wave gate with zero failures.

### 3.3 The teaching message — one string, both verbs

```
unknown agent(s): ghost (registered_agent_8e4200ff…) — every id must name a registered
agent row before a message or a brief can be written in its name
```

`f"{name} ({id})"` satisfies both sides of the pinned pair: 04a pins the **ID**
(`test_the_refusal_NAMES_the_bad_agent_id`), `test_message_ledger::test_an_unregistered_recipient_is_rejected_by_name`
pins the **NAME**. Proven to be ONE shared string, not two agreeing copies, by mutation — §4.2/§4.3.

### 3.4 MP-2 — the shared policy is the SOLE decision point

`briefs.py` and `messages.py` both bind the module-global `reject_unknown_agents` and call it;
neither re-decides underneath. `MessageLedger._reject_unknown_recipients` survives as a **pure
delegation** that owns only the ledger's *vocabulary* (`error=UnknownRecipientError`) — the choice
of which exception a caller catches, never which ids are unknown. That is the distinction W-E
exists to test, and MP-2a/b's accept-everything stub is what detects a violation: with the shared
policy neutralised, both verbs must reach the ENGINE.

### 3.5 The error class — the lead's ruling, as built

`UnknownAgentRowError` (never `UnknownAgentError`, which already exists in `loremaster.agents`
meaning *"this display NAME resolves to no agent at the REGISTRY"*). Shared base, distinct
subclasses (C-DEF-3): `UnknownBriefAgentError(BriefLedgerError, UnknownAgentRowError)` and
`UnknownRecipientError(MessageLedgerError, UnknownAgentRowError)`. `agent_existence` imports no
ledger, so the layering the module exists for is intact — and it exports **exactly one** exception
class, which is what `_comms_fakes._shared_unknown_agent_error()` fails closed on.

### 3.6 `publish(agent_id)` — what I did NOT reshape, and why

The operator's no-consumers ruling permits retyping `agent_id` outright. **I kept it a bare `str`,
deliberately**: the contract calls `publish(..., agent_id=<str>)` at every site, and
`test_brief_ledger.py` / `test_comms_tool.py` do too. Retyping it to `AgentRefLike` would redden
~90 pins I may not edit — the latitude is real but the contract is the binding constraint, so the
"hardening" here is the existence check and its placement, not a signature change. Flagged rather
than assumed.

## §4 — mutation proofs (three, all `EXIT=0`, all restored byte-exact)

### 4.1 Group C — the declared-RED set from the contract's own `MUTATION_PROOF` block

The set was taken **verbatim from the contract** (written before any run) and each id confirmed to
COLLECT via `pytest --collect-only -q` before the run — never transcribed from output.

```
mutation: _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)
       -> _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE)
mutation LANDED (anchor matched exactly once)
8 failed, 42 passed in 5.15s
tree restored byte-exact (surreal_schema.py: md5 ddc2d58a76b11ddf0fce8ecf90266988)
PROOF HELD — the declared RED set fired EXACTLY   ·   EXIT=0
```

**8/8, both ways: no unexpected reds, and no declared red stayed GREEN.** The contract's prediction —
including the two pins it grew the set by (`$G` the ledger-migration pin, `$H`'s publish leg, which
observes both layers on purpose) — was exactly right, and every other app-check pin stayed
independent of the engine clause, which is the property the split demanded.

### 4.2 Sharing proof A — the BRIEF side rides the shared message

```
mutation: f"{name} ({agent_id})"  ->  f"{name}"      (drop the ID from the shared refusal)
6 failed, 385 passed, 14 skipped in 13.51s
tree restored byte-exact (agent_existence.py: md5 5b570b0e2246fea2eedd4e32cb81fbc6)
PROOF HELD — the declared RED set fired EXACTLY   ·   EXIT_A(unpiped)=0
```
Declared and fired: the two `test_the_refusal_NAMES_the_bad_agent_id` params, the two
`test_an_ack_by_an_UNREGISTERED_agent_is_REFUSED_and_never_already_acked` params,
`test_a_refused_ack_never_ATTEMPTS_the_RELATE`, and
`test_brief_ledger::…test_an_UNSEEDED_agent_id_is_REFUSED_by_this_backend[real]`. **`publish` AND
`ack` both moved**, and the `[fake]` leg did not — it raises its own message, which is the double's
declared independence working.

### 4.3 Sharing proof B — the MESSAGE side rides the SAME string

```
mutation: f"{name} ({agent_id})"  ->  f"({agent_id})"   (drop the NAME from the shared refusal)
1 failed, 390 passed, 14 skipped in 13.10s
tree restored byte-exact (agent_existence.py: md5 5b570b0e2246fea2eedd4e32cb81fbc6)
PROOF HELD   ·   EXIT_B(unpiped)=0
```
Fired: `test_message_ledger::…test_an_unregistered_recipient_is_rejected_by_name[real]`.

**Why two mutations and not one:** each half of the message is load-bearing for a DIFFERENT ledger's
pin, so A proves the brief verbs ride it and B proves `send` rides it. Together they establish one
format string with two callers — by mutation, not by reading the import. The SEMANTIC half (the
policy decides, callers do not) is mechanised in-suite by MP-2a/b + the two raising-sentinel pins,
all green.

### 4.4 ⚠ A live #194 of my own, disclosed rather than laundered

My first runs of A and B piped `mutation_proof.py` to `tail`, so the `$?` I echoed was **tail's exit
status, not the tool's** — the exact laundering repo law names (*"a piped test run can lie by
omission"*; *"if step N silently no-opped, would step N+1 still print something that reads as
success?"*). I re-ran both **unpiped**; the exit codes above are the tool's. The re-run also caught
a second, unrelated hazard: a `cd` in an earlier command had persisted, so the first unpiped attempt
exited **127** (`./scripts/mutation_proof.py: No such file or directory`) — a "failure" that,
behind a pipe, would have printed nothing and read as quiet success.

### 4.5 Tree integrity

All five production files `cp -a` content-backed-up to `/tmp/builder04a-backup/` **before** any
mutation (standing law for mutating an uncommitted tree — an md5 list is a detector, not a backup),
and verified byte-exact against that backup after every proof:

```
$ diff -q  (all five)   ->  ALL FIVE BYTE-EXACT vs the pre-mutation backup
```

## §5 — the check the fakes structurally CANNOT make

`test_comms_tool.py` drives ~90 `brief_publish`/`brief_ack` sites on `FakeBriefLedger`, whose agent
table is **UNMODELLED** — a declared bound, so it accepts every id. **That fixture guarantees the
one condition under which a broken register-time auto-ack is invisible** (repo law: THE TEST
ENVIRONMENT IS A FICTION). `_comms_register` auto-acks the standing brief with a **just-registered**
agent id, and after this flip that ack is only legal if the agent row is already committed.

So I drove the REAL `AgentRegistry` + REAL `BriefLedger` on one database, in production's order
(`agent_registry` → `brief_ledger`), against spike-surreal `:18000`:

```
publish v1 by a REGISTERED agent            -> OK
register-time auto-ack                      -> already_acked=True via=publish
second agent auto-acks a brief it did not publish -> already_acked=False
publish with a GHOST id -> refused, TEACHING: unknown agent(s): ghost (registered_agent_8e4200ff…) — …
ack     with a GHOST id -> refused, TEACHING: unknown agent(s): ghost (registered_agent_8e4200ff…) — …
publish(agent_id=None)                      -> v2 OK
```

The positive legs, the negative control, and the third input class, all on the real pair. (The
`already_acked=True via=publish` on the first ack is the documented idempotent-re-ack path: the
publish wrote the self-ack edge as `via='publish'` and first-write-wins held. It emitted one
`brief.query.rejected` log line — the UNIQUE(in,out) rejection that IS the re-ack signal, not a
defect.) Consumer set cross-checked with `lore_impact` (`publish` → `_comms_brief_publish`; `ack` →
`_comms_register`, `_comms_brief_ack`, with its bare-name-union caveat resolved by grep).

## §6 — removed-behaviour inventory

The no-consumers ruling grants latitude not to PRESERVE a behaviour; it does not excuse not
NOTICING one. Every branch, guard, side effect and served claim I deleted or replaced:

| # | removed / replaced | verdict |
|---|---|---|
| RB-1 | `_reject_unknown_recipients`' dedupe `dict.fromkeys(ref.id …)` | **preserved-with-pin** — `name_by_id.setdefault` in the shared function; keyed on `id`, never `name`, for the same stated reason (two agents may share a display name). |
| RB-2 | its ONE-query-regardless-of-count property | **preserved-with-pin** — still one `SELECT id FROM $agent_ids`; `test_comms_tool::TestTheSendsRecipientReadCostScalesWithLenToNotSessionSize` green. |
| RB-3 | bind name `$recipient_ids` → `$agent_ids` | **dropped-deliberately** — internal, and now ledger-neutral. Safe because `test_retry_seam._AckConnection` is **shape**-keyed (params binding `agent` RecordIDs), not text-keyed, by its own docstring. Its five pins are green. |
| RB-4 | `self._bare_id(row[id])` as the id derivation | **dropped-deliberately, replaced** by symmetric `str(RecordID)` lookup (§3.2). Reason: it removes a derivation rather than repeating one, and adds no eighth `_bare_id` copy. Probed equivalent on 3.2.1 across four id shapes. |
| RB-5 | error text *"unknown **recipient**(s): … must be a registered agent before it can be sent to"* | **dropped-deliberately** — ONE message now serves both verbs, so the send-specific noun is gone from the ledger's string. It survives in the error **class** (`UnknownRecipientError`) and in the tool seam's roster enrichment. ⚠ **This is the one prose choice I recommend the lead rule on — §7 E-1.** |
| RB-6 | `unknown` computed as a **set of NAMES** | **dropped-deliberately** — two unregistered recipients sharing a display name used to collapse into ONE mention; each ID is now named separately. Strictly more teaching, and it is the packet's own *"name EVERY bad id"* law. |
| RB-7 | `UnknownRecipientError` raised directly by the ledger | **preserved-with-pin** — still the class `send` raises, via `error=`; `test_message_ledger::TestVocabularies::test_every_domain_error_is_a_message_ledger_error` green. |
| RB-8 | `ack`'s `del agent_name  # carried for API symmetry` | **dropped-deliberately** — `agent_name` is now READ (it names the identity in the refusal). Nothing observable removed; *"not persisted on the edge"* is still true and still stated. |
| RB-9 | `ack`'s docstring claim *"this ledger never queries the `agent` table itself"* | **dropped-deliberately** — it became FALSE the moment the check landed. Served/teaching prose is derived from behaviour, never left standing beside it (the #219 class). |
| RB-10 | `briefed` accepted a RELATE to a non-existent endpoint | **dropped-deliberately** — that IS #105, and it is the packet. Pinned by the dirty-store, ensure_ready and un-enforcing-door pins. ⚠ Pre-existing dangling edges are **unaffected** — turning `ENFORCED` on is a FALSE ALL-CLEAR on them (store reference §4); cleanup is ruled OUT as #236. |
| RB-11 | `generate_brief_ddl()` could be applied to a database with **no `agent` table** and the edge still accepted writes | **dropped-deliberately, pinned + documented** — the slice is now ORDER-DEPENDENT on `generate_agent_ddl`, exactly as `_message_statements` already records for `to`. Pinned by `TestTheBriefSliceIsOrderDependentOnTheAgentSlice`; production order verified end-to-end (§5); recorded in `_briefed_statements`' docstring so the next author meets it deliberately. |

Behaviour **changed** (not removed), operator-accepted in the packet: a publish with an unknown
`agent_id` now refuses before the mint rather than writing the brief and dangling its ack.
`agent_id=None` is untouched — the third input class, legal and edge-free, forced by its own pin.

## §7 — escalations (scope belongs to the operator)

**E-1 — the shared refusal no longer says "recipient" (RB-5).** One message for both verbs was my
call; the alternative is a `noun` parameter on `reject_unknown_agents`. I rejected that because a
knob on a shared policy is where divergence starts and the noun is cosmetic while the *class* a
caller catches is not. **If the lead wants "recipient" back for `send`, the fix is one parameter and
one format string, in one file** — say so and I would add it. Deciding silently was the failure mode
I was avoiding, so it is written down.

**E-2 — the SENDER door is STILL OPEN and still unruled (adversary R8/I13, contract D-b).** A `send`
whose **sender** names no `agent` row still writes a message row with a ghost sender id. 04a's Exit
criterion names recipients, the contract has no pin for it, and closing it would widen the ruled
scope — so **I did not close it, and I am not deciding it.** Fix-now vs defer is the lead's/
operator's call; if deferred it needs a finding number and a named re-open trigger, or it is a
can-kick. The fix itself is small: pass the sender into the same shared call.

**E-3 — SEVEN hand-rolled `_bare_id` copies exist package-wide**, each beside its own private
`_TABLE_SEPARATOR = ":"` constant. **Derived, not recalled** — `grep -rn "def _bare_id\b"` and
`grep -rn "^_TABLE_SEPARATOR"` over `loremaster/loremaster/`, both returning the same seven modules:
`agents.py`, `briefs.py`, `findings.py`, `messages.py`, `tasks.py`, `memory/local.py`,
`store/surreal.py` (`findings.py` additionally defines `_bare_id_or_none`). ⚠ **My own first draft of
this line said FIVE, from memory of a partial grep** — an un-derived count inside the escalation
about un-derived counts; re-derived before shipping, and disclosed here because the near-miss is the
receipt. This is
the #102/#120 shape and it is **pre-existing — I added none and removed none** (consolidating seven
modules with their own contracts is well outside 04a). Raising it because *"duplication is a DESIGN
decision, ESCALATE it"* and because D-d proves this exact parse is easy to get wrong: an eighth author
who guesses `split(":", 1)[-1]` gets 130 red pins, and there is nothing standing between them and
that guess. **Recommendation:** a finding with a named home (a neutral `bare_record_id`), not a fix
inside this packet.

**E-4 (FYI, no decision needed) — `RecordID` is UNHASHABLE on SDK 2.0.0** (`__hash__ is None`,
measured §3.2). Any future code putting RecordIDs in a `set`/dict key raises `TypeError`. Not in the
store reference; worth a line there if the lead agrees.

## §8 — WHAT I COULD NOT DETERMINE

1. **Concurrency.** No pin exercises the app check under contention, and `publish`'s
   check-then-mint window is a genuine **TOCTOU** against agent retirement/deletion: an agent that
   disappears between the existence read and the RELATE is refused by `ENFORCED` (correct outcome,
   uninformative message) rather than by the app layer. Unmeasured by me. A contract pin is the
   wrong instrument (repo law: ≥8-way, 20 consecutive green runs); the engine guard is the backstop
   that makes the window safe rather than merely narrow.
2. **The cost of the added read.** `publish`/`ack` each gain ONE query when an `agent_id` is
   present (zero when it is `None` — the short-circuit). I did **not** measure latency and I am not
   asserting it is free.
3. **The cost of `ENFORCED` on 3.2.1.** Unmeasured here; the store reference's *"none measurable"*
   is a 3.1.5 figure and I did not re-derive it.
4. **Whether pre-existing dangling `briefed` edges exist in production, and how many.** Ruled OUT
   as #236; **nobody has measured it, so any number is a rumour** — including zero.
5. **Deploy behaviour.** I ran nothing against `:18500` and built no image. The migration is proven
   against a dirty TEST store through the ledger's own `ensure_ready()`; only the deploy smoke
   proves the artifact.
6. **`brief_ack`'s tool seam has no teaching pin** (MP-6 covers `brief_publish` only) — inherited
   from the contract's §5 item 4, not re-derived by me.
