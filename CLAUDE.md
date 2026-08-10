# lore — project process law

Standing rules for every session in this repo. Distilled from operator rulings and
audited failure patterns (P7–P8d); the phase resume docs in `~/.claude/plans/` carry
*phase state only* — process law lives here.

## THE CONSUMER LAW + THE TRUST DOCTRINE (operator, 2026-07-24 — the fixed star)
- **lore's clients are AGENTS — Sonnet 5, Opus, Fable — never humans.** Every served
  surface (renders, instructions, counts, errors, teaching prose) is read by an LLM that
  learns the contract FROM what is served. Design, pin, grade, and write for that reader.
- **TRUST is the paramount property of every served surface** (operator, verbatim intent:
  agents that do not trust the MCP route around it, wasting tokens in every future
  session — better to spend tokens NOW earning trust than to tax every consumer forever).
  Operationally: a served count describes the whole set its label claims; failures are
  LOUD, never silent; teaching prose matches measured behavior; no render over-claims.
  Rigor-vs-speed trades on serving surfaces resolve toward RIGOR.
- Acceptance instrument: consumer-agent batteries with keyed honesty probes ending in the
  routing test — CALL_AGAIN vs ROUTE_AROUND, where a ROUTE_AROUND on an honestly-rendered
  surface is a FAILED acceptance to fix, never a waived answer. First instance: packet 03b
  rulings §C5. Design mechanics: DESIGN-LAW §1. Memory: `lore_recall("trust doctrine")`.

### TRUST — THE HARD DEFINITION, so you can tell when you have achieved it
(operator-directed 2026-07-28; derived by a three-model consult — Opus, Sonnet 5, Fable —
each of which conceded against its own position. Receipts: `REPORT-lawtest-{opus,sonnet,fable}-1.md`
in `receipts/2026-07-28-packet11ib/`. The clauses above say what trust REQUIRES; this says
what it IS and when you are DONE.)

> **A response is trustworthy iff a consumer who acts on it WITHOUT CHECKING cannot be
> wrong in a way the response did not name.**

Trust is a property of a **RESPONSE**, not of a tool, and it **does not require being
right** — a response that names its bound and then hits that bound has kept faith. That is
what makes it achievable instead of demanding omniscience. **A bound is a FACT (the set,
the predicate, the time), never a disclaimer:** *"results may be incomplete"* names nothing,
licenses nothing narrower, and fails on its own terms.

**ACHIEVED when BOTH legs pass. Two legs, because each is blind exactly where the other is
strong — collapsing them loses whichever case the survivor cannot see.**

- **Leg 1 — SCOPE DIFF** *(healthy path: design ≠ label)*. Write the question you actually
  answered — set, predicate, time. Write the question the consumer thinks they asked. Any
  difference goes in the render; no difference ⇒ done. **Ask: *"what question did I actually
  answer, and is it the one the consumer thinks they asked?"*** Design-time, baked into the
  render template once, ~free per call. ⚠ **Two stated bounds:** it is sound on *set* and
  *predicate-as-WRITTEN* only — **time, environment, and predicate-as-EXECUTED are BELIEVED,
  not known** (#24 · #107 · #131 · #139); and its stopping rule bounds the *diff*, not the
  *"question the consumer asked"*, which over an open caller set is still judgement.
- **Leg 2 — FORGERY PINS** *(degraded path: runtime ≠ design)*. Derive the failure set —
  the surface's stateful dependencies (index, store, fs, clock, subprocess) **×**
  `{stale, empty, wrong-instance, partial}`; that is dependencies-×-verbs, **derived like
  `registration_sites.py`, never a curated list of things that might go wrong**. CONSTRUCT
  each state and byte-diff the served response against the healthy one. **Identical bytes =
  a false clear = STOP.** **Ask: *"what broken state of this tool would serve exactly these
  bytes?"*** Build-time, per tool — never per-call (injected states cannot re-run live).
- **CONSTRUCTION, NEVER REASONING, and this is the load-bearing sentence:** a missed
  world-state is *discoverable* — routine coverage finds it by accident, without anyone
  knowing the bug — but **a false belief about your own semantics is SELF-SEALING, and the
  only instrument that breaks it is execution.** #107's author sincerely believed
  `IF NOT EXISTS` errored on an existing field (the vendor docs said so), would have
  completed Leg 1 truthfully, and returned DONE.

**LOST: one false clear** — a wrong state that renders identically to the correct one. That
is a **STOP naming a gap in the derived failure set**, never a quiet fix. **The ledger is
asymmetric AND it RESETS:** an LLM consumer inherits no reputation across sessions — it
travels only as text, and a document asserting *"this tool is reliable"* is just another
claim it evaluates against the response in front of it. So one true clear buys almost
nothing while one false clear is fatal and irreversible within the session. **There is no
equilibrium in which credit accumulates: "earning trust over time" is NOT a strategy —
avoiding false clears is the only one, and it is won at BUILD time or not at all.**

**BOUND, stated so this section does not over-claim about itself:** the derived failure set
is complete only over the dependencies and verbs written down. Every false clear found
later is a **re-open trigger**, never a retroactive pass.

**What this REPLACES:** cheap-vs-expensive verification is a real property but a *downstream*
one — verification ergonomics, not trust. A claim that cannot be checked has infinite
verification cost, so there is nothing to optimise until the gate above passes. And it is
not decidable: builders disagree about where "cheap" ends, but nobody disagrees about
whether two runs produced byte-identical output. ⚠ **Scaffolding that can lie is worse than
none** — an `n` restated beside a claim rather than DERIVED from the computation that
produced it is a false clear *wearing* verifiability, armoured by compliance.

## Quality gates (operator-ruled, every commit)

⚠ **THIS SECTION IS COMMENTARY. `scripts/gates.yaml` IS THE AUTHORITY** (sidecar
Ruling 7.1, operator-granted 2026-08-01 — "Close the gap"; grounds #306 + #312).
**A gate EXISTS iff it has an entry in that manifest**; a gate named only in the prose
below binds nothing and appears in no receipt. The binding is INVERTED deliberately:
deriving the gate set from THIS FILE would mean a regex over English law, which is the
enumeration antipattern one level up — the same class as the six defeated instruments
below, and as the registration-site list that was wrong four times. So the manifest is
canonical and this prose annotates it, exactly as `registration_sites.py` is run rather
than read and the store reference is cited rather than re-transcribed.
- **The gate set is DERIVED, and the currency check is how you read it:**
  `uv run python scripts/pending_contract_gate.py --currency` renders every manifested
  gate as **GREEN / RED_ADJUDICATED(owner, trigger) / RED_ORPHANED**, and **only
  RED_ORPHANED fails.** The invariant is ADJUDICATION, not greenness: packet 39's red
  typecheck is a ruled, owned bound doing its job; red-with-nobody's-name-on-it is the
  disease. **REQUIRED at every wave close-out** — #306's rule ("enumerate WHICH gates
  ran and the verdict of EACH") is now GENERATED from the manifest, which makes the
  omission class unwritable. An adjudication is a machine-checkable registry entry
  (`scripts/pending_contracts.yaml`); a finding row is provenance, never the adjudication.
  ⚠ Named bound: between close-outs a fresh red can sit unnoticed. This bounds the orphan
  window to one wave — re-open trigger: **the day this repo gains CI, currency is its first job.**
- **WHY, measured, twice.** #306 — a gate RUN and RED with no owner, no trigger, no
  ledger row, inherited silently by every session. #312 — a gate CLAIMED and NEVER RUN:
  the wrapper built to pin #306 shipped without its own ruff leg, so its receipt read
  full-gate while a third of the set never executed, *and* `ruff` turned out to be red
  at HEAD too. Both were found by agents tripping over them mid-task. Neither was
  findable by reading this file.
- `scripts/typecheck.sh` — zero mypy errors including test trees. This runner is
  canonical; a single combined `mypy` invocation false-errors on `tests.conftest`.
- `uv run ruff check .` — clean. The PL family is live under the 2026-07-05 curation
  (PLC0415/PLR0913 ignored as house idioms; PLR2004 prod-only). Real pylint is
  upstream-blocked (astroid<4.1 pin) — do not install it.
- pydantic at every validated boundary; models stay `extra="forbid"` on the wire with
  resilient *construction seams* (`from_engine_status` pattern) — never loosen the model.
- **Run pytest with `-n auto` (pytest-xdist).** Measured 2026-07-12 on this box (64 cores):
  mcp_server+render_seam_pins went **846s → 88s (9.6×)** with an IDENTICAL pass count (666);
  live-store suites are stable across repeated parallel runs (178/178 × 3). Parallel is safe
  BY CONSTRUCTION, not by luck — the harness was already built for it:
  `_surreal_harness.unique_database()` mints `test_<pid>_<uuid4>` per test precisely so
  "a concurrent pytest process on the SAME server never collides on, or reaps, this
  database". Only the runner was missing.
- Full suite is lead-run **at phase checkpoints only** — before the deploy that ships the
  work, NOT after every fix wave. Between waves: the changed suites + the structural/AST
  pins. The cold audit already re-runs the gates as its own independent instrument; the lead
  re-running the same suite behind it is duplicated wall-clock, not verification.
  ⚠ A piped pytest with a bad filename exits "no tests ran" silently — a green claim
  requires a passed-COUNT in the tail.
- Skill tests have their own idiom: `cd skills/lore-deploy/scripts && uv run python -m
  pytest -q . ../tests`.
- **COMMIT AT NATURAL BOUNDARIES — the working tree is never the ONLY copy of finished
  work (operator, 2026-07-14).** A green gate, a ruled design doc, a completed
  sub-phase, the state BEFORE an audit or mutation probe: each gets its one-concern
  commit BEFORE the next step can damage it. Rollback must be a git operation, never
  filesystem archaeology — receipts: a session had to restore a finished wave from ZFS
  autosnapshots because it lived only in the working tree (the 2026-07-14 MD5-list
  near-miss is the same class; 15-minute snapshot timing was luck, not a mechanism).
  This tightens, not replaces, the 2026-07-03 checkpoint-commit rule; agents mutating
  an UNCOMMITTED tree still `cp -a` the content first (standing law) — but the better
  state is that finished work is never sitting uncommitted at all.

## Using lore's own tools (the dogfood protocol)
lore-first is the default for code-structure questions — but trust requires currency,
so the protocol is: **check, then trust**.
1. Freshness first: `lore_index()` renders last_sync/last_sweep ages. If your session
   has edited files since those stamps, run `lore_index(reconcile=True)` (cheap,
   idempotent) before trusting graph-derived answers (impact, dead_code liveness,
   covering tests). Never use a possibly-stale impact result as a deletion gate —
   reconcile first (finding #46 was a near-miss).
2. Then lore-first: lore_search / lore_get_symbol / lore_impact / lore_read for
   definitions, semantic where-is, consumer sets, covering tests, spans.
3. Grep remains honest for exactly three cases — and the agent SAYS SO in its report
   when it falls back: (a) rename/await-migration exhaustiveness where one missed
   site compiles-but-breaks, (b) non-symbol textual seams (config keys, log event
   names, prose in string literals), (c) cross-cutting multi-question maps.
4. Friction files through `lore_findings action=report` (REQUIRES category, area,
   created_by). Routing around a lore weakness without filing it is the one
   unacceptable move.

**PRE-PRODUCTION STATUS — PRODUCTION CHARGES ARE ALWAYS AUTHORIZED (operator, 2026-08-10).**
lore's ONLY consumer is lore itself — the dogfooding fleet — so there is NO external
production risk during this phase. Deploys (container rebuild+recreate), and production-touching
code changes (the shipped scripts, the served MCP surface, the store schema/DDL) are
PRE-AUTHORIZED: do NOT escalate a "production-touching surprise" as a scope fork, and do NOT
gate a deploy on operator sign-off — proceed, then report. This RELAXES only the
production-touching *scope-escalation* trigger for lore's own code; the standing
verification / gate / cold-audit / trust law is UNCHANGED — you still PROVE the change (green
gates + cold audit) before shipping it, and the operator still owns *feature/scope* decisions
(what to build), just not *permission to touch production* (which is granted). **Re-open
trigger: the FIRST external / off-fleet consumer of lore — any deployment whose reader is not
this dogfooding fleet — at which point production-touching changes need the ordinary operator
scope-grant again.**

## Project memory is IN LORE, not in MEMORY.md (dogfood, operator 2026-07-22)
Durable project memory lives in the lore `memory` table — write it with `lore_remember`,
recall it with `lore_recall`. The harness's auto-loaded `MEMORY.md` is a **thin bootstrap**
(a pointer + a few second-zero operational landmines), **never a growing store**: it is
loaded in FULL every session, so accumulating memory there is the exact anti-pattern lore
exists to kill — and this project hit that file's size ceiling and needed manual compaction
before the 2026-07-22 migration into lore. So:
- **Do NOT add facts back into `MEMORY.md`.** Learn something durable → `lore_remember` it
  (atomic fact, `kind` fact/decision/gotcha, never `ongoing` — that TTLs out in 7 days).
- The mechanical half lives in the **lore-deploy skill** ("Project memory" section): it
  bootstraps `MEMORY.md` and migrates a legacy flat one into lore on setup/start. This rule
  is the behavioural half that stops the regression when the skill is not in context.
- The 2026-07-22 migration moved 51 flat topic files into lore (labelled
  `origin=claude_native_memory`, traceable by `source_file=`); originals archived beside
  `MEMORY.md`. Recall project memory (`lore_recall("<topic>")`), do not expect it in the file.

## Rename/reshape sweeps (audited failure pattern, P8d — 3 of 4 confirmed defects)
Confirmed green-at-gate defects cluster in *natural-language surfaces whose consistency
with code no gate checks* (error prose, tool descriptions, instructions claims,
rendered free text). Therefore:
- Sweep greps for retired names use BARE, anchor-free patterns (no `lore_` prefix
  anchor, no call-paren anchor) — prose mentions don't carry structural anchors.
- "All remaining hits are X" is banned output. Every residual hit gets a file:line +
  one-word verdict, individually.
- Tests written before a semantic change certify the OLD world: on any rename, grep the
  test tree for assertions pinning retired names/strings — a green suite may be green
  because it still asserts the corpse.
- The DUAL holds too (external provenance: odoo-custom-v15 PR93, 2026-07-13): tests
  written for a NEW design certify only the new world — nothing checks the old world's
  virtues survived the rewrite. Any delete/replace ships with a removed-behavior
  inventory (branches, guards, side effects, per-field output provenance — the absence
  of an override is a behavior) adjudicated item-by-item: preserved-with-pin (spec
  citation, "the old code did it" is banned) / dropped-deliberately (reason) /
  old-bug-not-re-pinned / spec-silent→operator ruling. Instrument: the tdd skill's
  Phase 0 inventory + Phase 1 adjudication gate + contract-adversary P6b.
- Any NEW render of stored free text (finding bodies, memory notes, task subjects)
  routes through the shared sanitiser seam (`loremaster.search._sanitise_line` until
  finding #34 promotes it) — multi-line stored text renders inside a backtick fence.
  Its tests MUST include a hostile fixture (newlines + a row-shaped forgery line +
  backtick runs). Single-line-only fixtures are the documented way these defects
  stayed green.
- Structural pins guard the served surface: the exact-set registration pin, the
  dead-name hygiene scan, the instructions-names-every-tool pin (all in
  test_mcp_server.py). Every audit-caught defect CLASS gets converted into a pin like
  these — a fix without an invariant is half a fix.

## READ THE DEPENDENCY'S DOCS — THEN VERIFY THEM (the #107 production outage, 2026-07-13)
A widened field ASSERT shipped with 1040 tests green, a cold code audit GO, and a
contract-adversary passing — and **broke `brief_publish` 100% in production**, because
`DEFINE FIELD IF NOT EXISTS` is a NO-OP on an existing field, so the change never migrated.
**The gotcha was already written down in our own repo** (`docs/reference/surrealdb-31-capabilities.md`:
*"`DEFINE … IF NOT EXISTS` never updates an existing definition — migrations need OVERWRITE/ALTER"*).
Nobody read it. Everyone probed the engine empirically instead, and the schema was written
`IF NOT EXISTS` anyway. Therefore:

- **When the question is "how does this dependency behave", READ ITS DOCS FIRST.** Probing is
  for CONFIRMING what the docs say and for finding what they OMIT — never for deriving from
  scratch what the vendor already documents. This is the packages-over-hand-rolling rule
  applied to KNOWLEDGE: do not reverse-engineer what is written down.
- **Check `docs/reference/` before probing.** Prior sessions commit capability references there
  precisely so the next session need not rediscover the engine. Not reading it wasted a
  session and cost an outage.
- **The vendor docs AND the engine's CI-verified specs are now IN the RAG — search them, never
  scout or probe from scratch (that IS the #107 failure mode).** SurrealDB's 3.2 documentation is
  indexed as lore tier `surrealdb-docs`; the engine's own SurrealQL language tests as
  `surrealql-tests` (pinned at the v3.2.0 tag — a spec's expected-result IS the behaviour, so it
  CANNOT lie). Order for a "how does the engine behave" question: (1)
  `docs/reference/surrealdb-31-capabilities.md` — OUR authority, incl. §6 (where the vendor docs
  are FALSE); (2) `lore_search(tier="surrealql-tests", …)` — the executable specs; (3)
  `lore_search(tier="surrealdb-docs", …)` — vendor prose, which CAN lie → treat a hit as a lead to
  VERIFY, never as final; (4) a live probe against the 3.2.1 test store (`ws://127.0.0.1:18000`) —
  the LAST resort, for what none of the above cover. (Corpora added 2026-07-22.)

## THE TEST ENVIRONMENT IS A FICTION (#131 + #107 — the same root, twice)
**The suite runs on a dev host. Production is a container. EVERY difference between them is an
unguarded gap — and both of this project's worst outages lived in exactly that gap:**
- **#107**: a widened schema ASSERT never migrated. 1040 tests green, a cold audit GO, a passing
  contract-adversary — and `brief_publish` broke **100% in production**. No test could see it,
  because **every test mints a VIRGIN throwaway DB**, and a fixture that guarantees a clean slate
  cannot test what only happens on a dirty one. Every long-lived deployment is a dirty one.
- **#131**: the code shells out to `git`; **the image had no git**. The `OSError` was swallowed into
  a silent `(None, None)`, so every production snapshot's git provenance was empty **for months**,
  invisible because nothing rendered the field. No test could see it, because **tests run on a host
  that HAS git**.

**The pattern, stated once: THE FIXTURE GUARANTEES THE ONE CONDITION UNDER WHICH THE BUG IS
INVISIBLE.** A green suite says "the source is correct in the test environment" — never "the
ARTIFACT is correct in the PRODUCTION environment". Those differ, and the difference is where the
outages are.

- **Pinning the source proves the RECIPE. Only the running artifact proves the CAKE.** In both
  outages, the deploy SMOKE was the only instrument that caught it — after the fact.
- **The instrument (do not just remember the law): packet 01a** — run the suite IN the deployed
  image (ephemeral container from the SAME image, tests mounted, `loremaster.__file__` ASSERTED into
  site-packages so you prove you are testing the artifact and not the mount). Finding **#139**.
- **When you write a fixture, ask what CONDITION it guarantees — and whether production guarantees
  the opposite.** Virgin DB vs long-lived store. Dev host vs slim image. Writable tree vs `:ro`
  mount. Aligned uid vs mismatched. Each one has already bitten or is ledgered (#132, #134, #135).

## WHEN YOU CANNOT CLOSE A HOLE, PIN IT (packet 01, #137 + #138)
Some holes are not worth closing (the cure costs more than the disease) and some cannot be closed at
all. **An unpinned known limitation is indistinguishable from an unknown one** — the next engineer
rediscovers it from an outage, or "helpfully" closes it and re-opens a settled trade.
- **PIN THE MISS.** A test that ASSERTS the hole exists, and **goes RED the day someone closes it**,
  carrying the message *"this is a KNOWN BOUND (#NNN) — if you closed it deliberately, delete this
  pin and say so."* Receipts: #137 (a third-party dep that spawns is invisible to any AST scan of our
  source — not closable without demanding every binary every dependency can reach) · #138 (four
  obfuscation doors in the exec seam — closing them taxes four shipped modules doing nothing wrong).
- **A bound that is pinned is a bound the next engineer meets DELIBERATELY**, with its rationale
  attached. It cannot be silently inherited, and it cannot be silently "fixed".
- **Every bound carries a NAMED RE-OPEN TRIGGER** (per the deferral law): the condition under which
  the trade changes. #137's is "the day we add ANY spawning dependency"; #138's is "if the threat
  model changes — untrusted contributors, or a hosted deployment" (→ packet 39 MUST consult it).

## A GATE NEEDS A THREAT MODEL — WRITE DOWN WHO IT IS FOR (packet 01)
The exec-seam gate was audited three times, and each auditor was entitled to call "a clever attacker
gets through" a defect — because **nobody had written down who the gate is for.** That absence cost
two fix waves and a false absolute in a docstring.
- **State the model IN the instrument**, not in a report: *this gate catches the **HONEST DEVELOPER**
  who adds a shell-out while the image silently lacks the binary (#131 verbatim). It is **NOT** a
  security boundary against a hostile author — anyone who can commit here can already ship anything.*
- **Then the verdicts follow mechanically:** *"a clever attacker gets through"* is **not** a defect;
  *"an honest engineer's shell-out goes unnoticed"* **is**. A door an honest author could plausibly
  walk through gets closed even at a cost; a door that only opens for deliberately unusual code gets
  LEDGERED, not paid for in false positives.
- **And the reason that trade is correct, which is the line worth keeping:** *a gate that refuses
  honest code is a gate that gets SWITCHED OFF — and then the outage happens again with nothing
  watching at all.* A false positive on `self.commands` is exactly the insult that disables an
  instrument.
- **AND VERIFY THE DOCS — a doc is a source, not an oracle.** SurrealDB's own `DEFINE FIELD`
  and `DEFINE INDEX` pages claim `IF NOT EXISTS` on an existing object *"will return an
  error."* **That is FALSE on 3.1.5** (probed): it returns OK and silently no-ops. A careful
  engineer trusting that sentence would conclude a stale definition is IMPOSSIBLE — which is
  plausibly how `IF NOT EXISTS` was chosen. **Both instruments were necessary and neither was
  sufficient: the docs named the migration mechanism; only the probe caught the docs lying.**
- **A tempting alternative can reintroduce the same bug from the other side.** `ALTER` looked
  like the "proper" migration verb — but it CANNOT CREATE a field, and `ALTER FIELD IF EXISTS`
  on a missing field is a SILENT NO-OP: adopting it would have reintroduced #107 on the
  fresh-DB path. Settle mechanism choices against the docs AND a probe, never against instinct.

## A DIAGNOSIS IS NOT AN INSTRUMENT (PKT-28 C1, ten instances, 2026-07-13)
This file ALREADY said defects cluster in "natural-language surfaces whose consistency with
code no gate checks". We knew. **We then shipped TEN more instances of exactly that class in
one phase** — wrong counts, wrong labels, a fabricated version, and three lines promising
mechanisms that never run. Knowing the failure mode changed nothing.

**Every other invariant here has a mechanical guard** — mypy for values/returns, AST pins for
template slots and mints, schema ASSERTs for the store, query-count pins for N+1s. **Served
English had none.** It was guarded only by whatever assertion a test author happened to write,
with whatever fixture value they happened to pick — and they picked the one value for which the
prose was true.

Therefore, standing law:
- **When a defect CLASS is identified, ship the INSTRUMENT in the same breath as the law.**
  A rule people must remember is not a guard; it is a hope. "Every audit-caught defect class
  becomes a repo-local invariant test" is already written above — this section exists because
  we wrote the law and skipped the instrument.
- **Prose that describes behaviour must be DERIVED from the behaviour, not re-stated beside
  it.** Renders take typed applicability (`auto_ack_at_register: bool`), never a name they
  compare. A role ("the standing brief") gets ONE accessor, not seven hardcoded lookups. Then
  changing the mechanism is a TYPE ERROR at every site that describes it, instead of a prose
  bug nobody can see. (The full root-cause analysis + the C2 step-0 plan: finding #104.)
- **Fixture factories must not default a parameter the code branches on.** `_brief()`
  defaulting to `name="project"` MANUFACTURED this blind spot: every render fixture silently
  tested the one value where the lies were true. No default ⇒ every call site must choose.

## THE RIDER IS PART OF THE RULING (packet 03b, SIX instances across three waves, 2026-07-26)
A ruling usually has two halves: the thing to build, and a clause saying **"and pin / measure /
verify it like this."** Six times in one packet a builder implemented the first half and dropped
the second, and every gate stayed green — because the dropped half WAS the gate.

**Five were cheap. The sixth cost a real defect.** DD-3.c said *"the message-slice dirty-store pin
gains the narrowed-assert leg"* and no dirty-store leg was added — only an offline pin that reads
generated DDL text and never touches an engine. That missing leg was the instrument that would have
caught DD-3.c's OWN safety argument being FALSE: *"cannot write-poison (message rows are never
UPDATEd)"* is true of `message` and **false of `to`**, where `ack_note` lives and which `drain`
UPDATEs in ONE statement over the whole window — so a single legacy over-cap edge fails that
statement and the agent **cannot drain ANY of its inbox** (total denial, reproduced with controls;
`receipts/2026-07-25-packet03b/REPORT-coldaudit-03b-2.md` §3.0). **A false safety claim survived a
design wave, a builder self-audit and two rounds of review because the instrument naming it was
never built.** Two more riders were similarly dropped: an accepted KNOWN BOUND with no docstring,
and a *">5% p50"* re-open trigger with nothing measuring p50 — *"a trigger nobody measures is a
hope."*

- **THE SELF-CHECK, which is the half that works** (the law alone did not — the builder repeated
  this twice AFTER writing it down): **the tell is a ruling sentence containing "and pin/measure/
  verify it like this." If you implemented the clause BEFORE that phrase and not AFTER, you are not
  done.** Three of the six were caught by asking that retroactively; a fourth needed an auditor.
- **A ruling's rider is not commentary and not bureaucracy — it is frequently the only thing
  between a correct build and a silently deletable one.** Two mutation proofs in this packet came
  back GREEN on first attempt because the ruling was implemented and its rider skipped: the
  deploy-gated `trace_ts` index line could be DELETED with every gate green, and the `refs` store
  ASSERT was invisible because the ledger's teaching reject fires first.
- **Corollary for whoever writes the ruling:** put the rider in the same sentence or the same
  bullet as the requirement. A rider in a later paragraph is a rider that gets dropped.
- **AND THE ASKABLE FORM OF THE DD-3.c MISS ITSELF** (design-sidecar-03b-1, post-mortem on its own
  ruling): *"does this safety claim still hold on every table/type/branch this ruling TOUCHES, or
  only the one I DERIVED it on?"* Its diagnosis: it wrote *"cannot write-poison"* as a claim about
  the table it had analysed (`message`, never UPDATEd) while a neighbouring clause had just moved
  the bound onto a table with a DIFFERENT write pattern (`to`, batch-UPDATEd by drain) — and the
  rider that would have caught the mismatch sat two clauses away from the claim it guarded. **This
  is THE QUANTIFIER LAW wearing migration clothes**: a safety property derived over one member of
  the set the ruling governs, then stated over the whole set. Same failure as conditioning an
  invariant on the one input you happened to test.

## FILING A RULE DOES NOT INSTALL IT (packet 03b, 2026-07-26 — the sharpest instance yet)
This file already says a diagnosis is not an instrument. Packet 03b produced the cleanest possible
proof: finding #194 (*"a mutation proof needs evidence the mutation LANDED"*) **recurred within the
hour, in the session that filed it, by the agent that found it** — after the rule was written down,
acknowledged AND sharpened. Nothing about writing it changed the shell block about to be typed. It
then recurred TWICE MORE while that agent was **building the instrument for it**, the second time
because the helper was piped to `tail` under `set -e`, so the pipe's exit status was `tail`'s and
the helper's failure code was thrown away.
- **What worked, all four times, was never the rule — it was a CHECKED EXPECTATION:** knowing which
  tests should redden and noticing the observed set differed. So `scripts/mutation_proof.py` now
  takes the expected-RED node ids as an ARGUMENT and diffs them **BOTH WAYS** — unexpected reds, and
  **declared reds that stayed GREEN**, the direction that catches a mutation landing in DEAD CODE.
- **Declare the set BEFORE the run, never transcribed from the output** — a "declared" set read off
  the failures you just watched is the tautology in a new costume. Take ids from `--collect-only`:
  collecting names tests without running them, so the set is fixed before any result exists.
- **Ask of any multi-step verification: "if step N silently no-opped, would step N+1 still print
  something that reads as success?"** If yes, the steps are not one unit. The failure direction is
  always toward false confidence, because a green measurement after a failed setup looks exactly
  like the thing you hoped for.
- **A guard nobody runs is a hope with a filename**, and worse than no guard, because its presence
  is read as coverage. Both of this packet's new instruments sat outside `testpaths` until
  2026-07-26 — the guards for #192 and #196, ungated, victims of the class they instrument.

### THE LEVER: write laws as QUESTIONS, not as PROPERTIES (builder-03b-1, 2026-07-26)
The counter-example that explains WHY some rules install themselves and most do not. This packet's
most productive move — *"what WRONG build would still pass this?"*, which found a cancellation pin
that could not fail — **was not invented here. It is already law above** (FIXTURES MUST
DISCRIMINATE, four prior instances). The builder read it and asked it, unprompted, about its own
work. Meanwhile #194, filed as a property to preserve, recurred three times in one session.

**The difference is the grammar, not the subject matter:**
- *"Fixtures must discriminate"* is a STATE. Nobody can check a state about work they have not
  finished; it is remembered, or it is not.
- *"What wrong build would still pass this?"* is a QUESTION. It runs in your head, on demand,
  against anything, and it returns an answer you can act on.

So when you write a law here, **phrase it as something an agent can ASK ITSELF mid-task.** Both
2026-07-26 laws pass that test by luck rather than design, and they are stated in askable form
above: *"did I implement the clause before the 'and pin it like this' phrase and not after?"* and
*"if step N silently no-opped, would step N+1 still print something that reads as success?"* A law
that cannot be turned into such a question is a law that will need an instrument instead — and if
you cannot build the instrument either, you have a hope, so say so plainly rather than filing it as
a rule.

## ONE IMPLEMENTATION — a pattern to clone is a defect to clone (#102, operator 2026-07-13)
The operator's question, on reading a design-law line: *"Can this just be written as a helper
method or decorator? DRY principle."* It was the root cause, one level above the code.

`DESIGN-LAW.md:75 (at 7e4f9b5)` said `findings.py::_apply_mint` *(bounded app-retry,
**deterministic jitter**)* **"is the reference pattern for ANY new hot-row mint."** It was
standing law. So `briefs.py` cloned it — and cloned the jitter bug, in a *different* wrong way
(4 fixed slots vs 16; both lockstep). Beneath both, `_query` turned out to be **TEN hand-rolled
copies of one seam, and NONE of the ten had any retry AT THE SEAM** (#120): the only retry
anywhere near it lived one level up, in the two CALLERS just named (`findings.py::_apply_mint`'s
16-slot jitter, `briefs.py`'s 4-slot jitter) — never in `_query` itself. **TWO POPULATIONS, not
one** — a distinction this very paragraph got wrong on its first pass (audit-fix-1 A3,
corroborated independently by blindreader-dry-2 F9): `scout.py` owns no `_query` at all, so a
`_query`-keyed search cannot find it — but one level BELOW `_query`, at the SESSION BOOTSTRAP
(`DEFINE NAMESPACE` / `use()` / `DEFINE DATABASE`), scout carries an ELEVENTH hand-rolled copy of
*that*. Ten `_query` bodies and eleven bootstraps are two different counts; conflating them into
one sentence is the exact defect class this section exists to stop. **The doc did not document
the defect. It propagated it.**

Therefore, standing law:
- **If two call sites need the same POLICY, it is a FUNCTION THEY CALL — never a pattern they
  clone.** Policy = retry budgets, backoff/jitter, error classification, sanitisation, auth,
  validation. A doc that says *"copy this pattern"* is an instruction to duplicate a defect
  nobody has found yet. Write `retry_on_conflict`; do not describe it.
- **ROUTING IS NOT SHARING.** A caller that calls the shared driver but hand-rolls the
  *decision* underneath it is a private copy wearing the shared name. Measured: a build where
  all eleven seams routed through the driver but each matched `"Resource busy"` locally scored
  **839 passed / 0 failed — indistinguishable from correct** — and under a reworded engine
  message **all eleven silently stopped retrying.** Another routed `kill` through the driver and
  retried **ZERO times**, because routing without CLASSIFY-AND-SIGNAL is a no-op. **A green gate
  over a dead mechanism — #102's own shape, reproduced inside the fix for #102.**
- **PROVE SHARING BY MUTATION.** Change the shared constant / jitter / marker → **every**
  caller's pin must go RED. A caller that stays green is not sharing. This is the only test that
  distinguishes DRY from looks-DRY, and it caught builds nothing else could.
- **Duplication is a DESIGN decision. ESCALATE it; never quietly write copy #2.**

### `lorerunes` — THE HOME FOR SHARED CODE (operator, 2026-07-27)
The law above says *escalate rather than write copy #2*, and for four years it never said where
copy #1 should LIVE. That gap is why duplication kept winning: when the only shared home was a
package the other side could not import, "share it" had no address, and the honest engineer wrote
the second copy because there was nowhere else to put it.

**`lorerunes` is that address.** A fourth workspace member, depending on **nothing but the
stdlib**, that every other member may import:

```
lorerunes/     shared primitives   (stdlib only — depends on no sibling)
lorescribe/    the transcriber     -> lorerunes
loresigil/     the symbol          -> lorerunes
loremaster/    the keeper          -> all three
```

A rune is the atomic mark a sigil is composed from, so the name states the dependency direction.

- **If two members need the same POLICY, it goes in `lorerunes` — not cloned, not "escalated"
  into a fork.** Policy = validation predicates, error classification, retry/backoff budgets,
  sanitisation, normalisation, formatting rules. Anything whose *rules must agree everywhere*.
- **`lorerunes` depends on NO sibling, ever.** The moment it imports `loremaster` or `loresigil`
  it stops being importable by them, and it is back to being nowhere. That is the whole
  constraint; guard it with a pin, not a habit.
- **It holds PREDICATES, not ENTRY POINTS.** Origin case (packet 42, #222): the blankness rule
  `not value or not value.strip()` moved there so `loremaster.config.resolve_secret` and
  `loresigil`'s `api_key` validator share one answer to *"what counts as blank?"* — while
  **secret RESOLUTION deliberately did NOT move**, because only a composition root may read the
  environment. A shared home makes the wrong thing newly possible; putting a capability there is
  a design decision, not a tidying.
- **Still prove sharing by MUTATION.** A shared package is an address, not a guarantee — routing
  is not sharing (see above). Change the predicate; **every** member's pins must redden.
- **WHERE A NEW WORKSPACE MEMBER MUST BE REGISTERED — RUN `./scripts/registration_sites.py`,
  DO NOT READ A LIST.** That script derives the sites from a property (*a registration site is a
  place where three or more member names co-occur*), so it finds sites nobody has thought of yet;
  its own docstring states its bounds, and its output is a worklist requiring judgement, never a
  verdict. **The entries below are the ones whose CONSEQUENCE is worth knowing in advance — they
  are annotations on the script's output, not a substitute for running it.** No count is stated,
  deliberately: every count this list has carried has been wrong (see the warning below).
  1. `pyproject.toml` `[tool.uv.workspace] members`
  2. `pyproject.toml` `mypy_path` — a member absent here still type-checks, just against the
     wrong resolution, so the failure is a *wrong answer* rather than an error
  3. `scripts/typecheck.sh` `MEMBERS` — as its **own iteration**, never a merged `mypy`
     invocation (a combined run reported **3** errors where the truth was **55**, a false
     all-clear for two readers)
  4. the AST scans' `_SCANNED_MEMBERS` — **a package outside the scan is silently exempt from
     every ∀ pin in the repo**
  5. `testpaths` — or its own guards are hopes with filenames
  6. **the CONTAINERFILE — and the IN-IMAGE CONFORMANCE GUARD that proves the COPY worked.**
     A member missing from the image is an `ImportError` at boot, **in production only, invisible
     to every test on this host** — #131/#139 verbatim. Both halves are required: `COPY` puts it
     in the image, `conformance_provenance.py::EXPECTED_MEMBERS` proves it arrived. A `COPY` with
     no guard entry is a deployment nobody checks.
  7. **`scripts/scratch_provenance.py::WORKSPACE_MEMBERS`** — the #140 guard that `scratch_copy.sh`
     runs. Its own comment says it *"mirrors `[tool.uv.workspace] members`"*, and a stale mirror
     means **every mutation proof in a scratch copy silently resolves the missing member from the
     ORIGINAL tree** while the agent believes it is isolated. That is #140's poison mode, in the
     instrument built to prevent #140.

  ⚠⚠ **THIS LIST HAS BEEN WRONG FOUR TIMES, EVERY TIME WHILE THE LAW ABOUT IT WAS BEING WRITTEN.**
  It shipped with five entries (`mypy_path` missed), was corrected to six (`scratch_provenance.py`
  missed), was corrected to seven — and then two more sites turned up at `8dc1259`
  (`test_backoff_seam.py` and `test_anchored_pattern_seam.py`, both silently narrower than the
  workspace they claimed to govern), while the heading still read *"THE SEVEN PLACES"*. **That is
  four wrong counts in one section, which is why this section no longer states one.** It is
  `CLAUDE.md`'s own instrument lesson operating exactly as predicted: an enumeration of places to
  look is the artifact this repo has the most receipts against. **So do not trust a list — run the
  derivation** (`./scripts/registration_sites.py`), and prefer converting a hand-list into a
  derived one, as those two scanners were: a site that reads
  `[tool.uv.workspace] members` stops being a registration site at all.

### The instrument lesson (six defeats, one shape — the most expensive thing we learned)
| instrument | keyed on | defeated by |
|---|---|---|
| retry gate | a label's **literal** | a substring of it |
| retired-symbol pin | a symbol's **name** | a numeric claim naming nothing |
| seam enumerator | `async def _query` | `scout.py`, which spells it differently |
| SDK gate | **3 method names** | the other 30 (`upsert`: 31 conflicts / 64 live attempts) |
| SDK gate | **2 receiver names** | six other doors |
| runtime gate | **the 4 tests that armed it** (its REACH) | a path no test executed |

**When you catch yourself enumerating what is FORBIDDEN, you have already lost.** The forbidden
set is unbounded; the SAFE set is small and enumerable. **Allowlist the safe.** When even that
fails, stop looking at *code* — enforce at **RUNTIME** (wrap the SDK connection; any call with
no driver frame above it is an escape, named by `file:line`). ⚠ And a runtime gate is an
invariant **only over code it RUNS** — so make coverage a *checked* variable (AST-enumerate every
call site; assert the guard OBSERVED each), or reach becomes the next name-list. Every exemption
in a deny-by-default safe-set must be **evidence-backed** (a live probe proving it cannot
conflict), never *"it writes no row"* — that opinion is what blessed the bootstrap DDL right
before it lost **6.2%–34.4% of concurrent first-connects** (measured across three 160-connect
runs, 16-way; a range, not a point — audit-fix-1 A4 / blindreader-dry-2 F4 caught this section's
own earlier "13%" as a fourth, unreproducible value alongside two production comments' "16.2%").

**THE ASKABLE FORM, so this lesson installs itself instead of being re-learned a seventh time
(INSTRUMENT 0, lore #344/#345, 2026-08-09).** All six defeats are ONE class — *a guard certifies
only the sites it EXECUTES over, and its reach is written as a hidden constant instead of a
checked variable.* Before shipping ANY guard / gate / scan / sweep, ask it of your own instrument:
***"What is the SET of sites this guard covers, is that set DERIVED from production truth or a
name/prefix/hand-list, and does a test go RED when the derived set GROWS but the observed set does
not? — and would this pin still read as success if the guard ran AFTER the thing it guards, or
against a baseline that measured nothing?"*** A reach that is a hidden constant is the seventh
defeat waiting to happen. This is a QUESTION, not a property to remember (per THE LEVER), and it
has a MECHANICAL home so it is not only a hope: the **`contract-adversary` now forces it
per-instrument (its REACH ATTACK, P1c)** — a contract that stands up a guard whose reach is a
hand-list, or whose coverage is not a checked variable, or that observes a proxy, cannot pass the
adversary, so instance #9 of the class is caught at CONTRACT time rather than by the next agent
who trips over it.

**The STOP-rule for a reach attack (heuristic, NOT an instrument — labelled so per THE LEVER and
A DIAGNOSIS IS NOT AN INSTRUMENT).** The askable form: *"is this guard's reach receding one level
deeper every round?"* If each round's fix just RELOCATES the hidden constant to a new site the
guard still doesn't cover, the surface is adversarial-only — **accept a pinned bound with a named
re-open trigger; do not run another round.** And before standing up a full multi-agent pipeline
for a cleanup/hardening wave, surface the value-vs-depth trade to the operator (*"ship the 2–3
that matter simply and ledger the rest?"*) rather than defaulting to max machinery because the
findings exist — the operator sets importance, not the lead. Receipts: the G/A-SUB spiral
(2026-08-10, the #344/#345 defect-class wave) ran 7–8 contract→adversary→revise rounds EACH on
trivial-importance surfaces before the operator right-sized both to a simple design + a pinned
bound; once escalated, each fix was one sentence. Right-sizing rigor to importance IS part of the
verification budget: maximal rigor on a trivial surface is the same error as under-verifying an
important one, in the opposite direction.

## Every artifact gets an adversary — not just the code (PKT-28 C1, 2026-07-12)
C1 shipped FIVE defects that no builder gate caught. Their provenance, measured: THREE
were tests that were never written (fleet grouping, the `brief_counter` declaration,
every count above the display cap — no contract fixture exceeded small-N); ONE was a
SPEC that prescribed the bug (§5.1 specified a retry jitter derived from the CONTENDED
ROW's id — identical across racers — and justified a 4-retry budget with "contention is
≤2-way" while the contract pinned 8-way); ONE was a real gate that FIRED and a builder
talked itself past. Only the code had an adversary. The spec, the contract, and the
brief each had exactly one author and zero graders — and every defect was born in one of
them. Therefore:

- **Cold-audit the CONTRACT, before the builder starts** — invoke the reusable
  `contract-adversary` agent (`~/.claude/agents/contract-adversary.md`, Opus; the role's
  full spec lives there — do NOT re-transcribe it into briefs, just point at it and add the
  project-specific landmines). A fresh Opus adversary reads
  the contract + the spec and reports what the contract does NOT test: boundary and
  SCALE cases (0, 1, cap−1, cap, cap+1 — the N>cap fixture nobody wrote), every-branch
  reachability (a branch no test reaches is dead code waiting to be discovered by an
  auditor), concurrency DEGREE (≥8-way, never 2-way), hostile input, and whether each
  fake can actually FAIL. It grades the tests, not the code. This is cheap: the missing
  fixtures cost one function each to write — they were expensive only to THINK OF.
- **A failing test is a STOP. "Flaky" is not a builder's verdict to render.** A builder
  may never downgrade a red test to flakiness and proceed; it escalates. The C1 mint
  defect failed ~4 of 5 runs, was called flaky, and shipped. Corollary: a single green
  run NEVER clears a concurrency test — require 20 consecutive (a lone green run gave
  the LEAD a false all-clear on that same defect).
- **Spec ambiguity is a defect, not a judgment call.** If a contract author finds itself
  CHOOSING between two readings of a spec sentence, that is an escalation — not a
  contract decision. Two C1 contract authors read one sentence opposite ways, both chose
  silently, and their suites contradicted each other.
- **Every load-bearing pin is mutation-proven**: break the production code, watch the
  test go RED, restore. A pin that cannot be demonstrated failing is not a pin. Every
  time this was demanded ad hoc in C1 it immediately exposed something.
- **A PROBE NEEDS A CONTROL — the auditor's instrument can lie the same way the author's
  did.** Two real self-caught failures from C1's own audits: a "closed set is enforced"
  probe that actually rejected on a PARSE ERROR rather than the ASSERT (it would have
  green-lit a broken closed set — it passed for the WRONG REASON), and a probe fixture
  whose collapsed group held one item, so `len()` ≡ `sum()` — the exact non-discrimination
  it was hunting in others. So: pair every negative result with a POSITIVE CONTROL showing
  the probe firing on a case you know is broken. "The bad input was rejected" is worthless
  until you have also shown the good input accepted and a differently-broken input rejected
  for a *different* reason. (The best C1 audit did this by default: proving a rejected
  `limit=0` left state unchanged, it ALSO showed a legal `limit=5` DID mutate state — so the
  probe demonstrably could see mutations.)
- **Read the residual table, not just the summary block.** The lead acted on an audit's
  NO-GO and skipped its RESIDUALS — losing a real latent defect (#105, a dangling-edge
  landmine) until the operator caught the omission. A summary block is a convenience, not
  the report.
- **FIXTURES MUST DISCRIMINATE — interrogate every one with "what WRONG build would this
  still pass?"** This single class has now produced a blocker FOUR times, on three axes:
  1. **Small-N**: a collapsed tail holding ONE agent at ONE version makes `len()` ≡
     `sum()`, so a build counting VERSIONS instead of AGENTS passed 489/489 + ruff + mypy
     + the AST pins. No contract fixture had ever exceeded small-N — the same reason three
     of C1's five defects (all of which only appear past the display cap) were never tested.
  2. **Parameter-value MONOCULTURE**: all 37 `brief_publish` calls at the tool seam used
     `name="project"`, so a build that self-acks ONLY when `name == 'project'` passed the
     ENTIRE contract (832 passed, 0 failed, zero mypy delta) with the finding fully intact
     for every other name. **If the code can branch on a value, at least one pin must use a
     DIFFERENT value.**
  3. **Arithmetic ALIGNMENT** (external provenance: odoo-custom-v15 PR93, 2026-07-13):
     fixture values whose arithmetic accidentally makes the dangerous branch unreachable —
     contracts of 17/96/84 remaining vs a 10+15 request span exactly two contracts, so the
     collapse branch never fired and a test NAMED for the hazard passed for a fixture
     reason. Its author had walked right up to the hazard and the fixture finished the job.
  The generalisation: a fixture that cannot distinguish the correct build from a plausible
  wrong one is decoration. Ask what wrong build survives it — the answer is the pin you are
  missing. And don't just interrogate — PERTURB: the contract-adversary's P2 mutates
  load-bearing fixture values in scratch copies (with a correct-build control leg) to prove
  each pin still discriminates away from its original values.
- **THE QUANTIFIER LAW (PR93, 2026-07-13 — a FULL tdd pipeline: 55-test contract, two
  adversary passes, 34 wrong-build mutations, cold audit, security audit — still shipped 5
  defects a diff-first reviewer then found):** never condition an invariant on the failure
  mode that prompted the work. Six PR93 tests pinned "no silent drop on supply failure";
  the rewrite dropped an input through the emission plumbing — supply fine, totals
  conserved, keys unique — and every pin stayed green. Pin the outcome property ∀ inputs
  (every input emitted / merged-and-reported / rejected-and-reported, REGARDLESS of cause)
  and FORCE each fate with a fixture — a ∀ helper evaluated only where the branch can't
  fire is the fixture-reason pass wearing a universal quantifier. Instruments: the
  contract-adversary's quantifier attack (P1b per-invariant ∀-vs-guarded table with
  door-build receipts; SUFFICIENT without the table = INSUFFICIENT) + tdd-contract's
  input-accounting checklist clause (fate coverage + mutation proof).
- **A fresh CONTEXT is not a fresh FRAME.** Handing an auditor the contract re-installs the
  contract's blind spot: PR93's defects were found by a reviewer whose frame was the DIFF
  ("what happens to each input? what did the deleted code do that this doesn't?") — a
  question no contract-holding auditor asks. Wave audits on reshape/delete work include a
  contract-blind diff pass (report-only; withheld: the contract, the adversary report,
  test-suite runs — brief mechanics in the tdd skill's Phase 7). Same reason the
  adversary's P6b enumerates deleted code BEFORE reading the Phase 0 inventory:
  independent enumerations are DIFFED, never shared.
- **The lead's brief sets the adversarial frontier — so the lead must not be the only
  imagination.** C1's contract writers found precisely what the briefs told them to look
  for, and nothing else. Delegate frontier-generation to the contract adversary rather
  than relying on the lead to enumerate it.
- **BUILDERS ARE OPUS TOO, AND A DESIGN PROBLEM NEVER REACHES A BUILDER (operator, 2026-07-14
  — packet 01, the three-scanner chain).** Roster is now Opus end to end: **Opus contract
  authors · OPUS BUILDERS · Opus contract-adversary · Opus cold code-audits · Opus lead**
  (Fable = design sidecar + escalation valve only). Sonnet is retired from the builder slot.
  **The routing rule is the half that matters, and it binds the LEAD:** if a contract's
  central requirement is a **property to INVENT** rather than a **spec to IMPLEMENT**, it is a
  DESIGN question — it escalates to the operator as a fork, or goes to an Opus author who must
  **adversarially attack its own design before shipping it**. It does NOT go to a builder with
  "figure out the general form", no matter the model.
  **Receipts (packet 01, measured — and they do NOT convict the builder's model):** an image
  gate had to derive which binaries the shipped code execs. v1 keyed on receiver NAMES and was
  defeated by four shapes — **written by an OPUS contract author**. v2 was a binding tracker
  that closed those four and opened four more, three of them REGRESSIONS (one LOST a binary v1
  had found) — **designed by a SONNET builder, because the lead's fix-wave brief said "build
  the ∀-property, don't just add the shapes"**: a design problem, handed to a builder, after
  two Opus authors had already failed at it. v3 held — **receiver-blind deny + allowlist the
  safe** — not because of a model, but because the OPERATOR reframed it ("stop enumerating the
  forbidden; the safe set is one file") and its author was required to BUILD and ATTACK its own
  design (2 of its own 23 invented shapes broke its first attempt; it fixed them before
  shipping). **The variable was never the model. It was the frame, and the frame is the lead's
  job.** The operator ruled BOTH fixes: Opus builders *and* the routing rule — belt and braces,
  because build work in this repo is routinely not mechanical.
  **Corollary — the lead's own tell:** when the same class of defect survives TWO waves, STOP
  briefing a third fix and escalate the DESIGN. Packet 01 ran three waves on one file before
  the operator's reframe settled it in one.
- **CONTRACT AUTHORS ARE OPUS (operator, 2026-07-12).** Rationale, measured: the contract is where the thinking is and where the
  defects are born, and Sonnet contracts kept shipping the same *class* of gap — small-N
  fixtures that cannot discriminate. Twice: (1) the #94 contract went green (561 passed,
  exit 0) with the defect fully intact — every pin tested a new method *nothing required
  the code to CALL*; (2) both cap-boundary fixtures in the #96 contract held ONE agent at
  ONE version, so `len()` and `sum()` were indistinguishable and a wrong build passed
  489/489 + ruff + mypy + the AST pins. Building to a good contract is comparatively
  mechanical — that is where Sonnet stays. **The adversary is NOT retired by this change:**
  an Opus author is still its own only grader, and that is the structural fault this
  section exists to fix.
- **A CONTRACT SHIPS WITH A SATISFIABILITY RECEIPT (the C-DEF class, 2026-07-14):** before
  any builder sees it, prove the contract goes 0-failed against a known-correct build — the
  adversary's own reference build (it must BUILD the fix to grade the contract anyway) is
  the natural instrument. Receipts: 20 pins RED on a correct build shipped inside an
  otherwise-strong fix-wave contract — one a `TypeError` hiding behind a pin that was red
  today *for the right reason* (so its author could never see it), one a pre-existing pin
  the reshape structurally contradicted, trapping the builder between ruff and a test it
  may not edit. Include the harder leg: still satisfiable AFTER the cleanups the lint will
  demand (orphaned-import deletion).
- **A FAILURE MESSAGE THAT PROMISES A CHECK THE ASSERTION DOES NOT PERFORM IS A FALSE GATE
  (P2, 2026-07-14):** the shared-deadline pin's message said *"three equal values is three
  independent budgets wearing a parameter"* while asserting only non-increasing — which
  ADMITS three equal values; the exact wrong build the pin existed to catch passed 399/399
  + mypy + ruff. Interrogate every assertion against its own message: the message is the
  spec the author believed, the assertion is the check the suite performs, and any gap
  between them is a wrong build's door. Corollary, same day: **sweep from the GREP, never
  from a report's hand-list** — the retired-number sweep found a ninth survivor ("16%")
  that the auditor's own "13%/16.2%" list structurally could not see.
- **AN MD5 LIST IS A DETECTOR, NOT A BACKUP (near-miss, 2026-07-14):** an auditor mutating
  an uncommitted tree had hashes but no content when the time came to restore — and a
  `git checkout --` would have discarded the wave (the working tree was its ONLY copy;
  15-minute ZFS autosnapshots saved it, by luck of timing). Any agent that mutates an
  UNCOMMITTED tree `cp -a`'s the full content FIRST and restores from content, proving
  byte-exactness after; every mutation brief carries this line.

## NO WORKTREES UNTIL WORKTREES WORK (operator, 2026-07-14)
**Standing directive: do not use git worktrees for lore work** — not for agents, not for audits, not
for mutation probes — **until worktrees actually work.** Still broken:
- **#134**: lore CANNOT BE DEPLOYED against a worktree — `.git` is a FILE naming an absolute host
  gitdir OUTSIDE the `/workspace` mount, so git fails inside the container and the honesty line reads
  null for the exact topology it is named after.
- **#125 / packets 17+23**: lore's index cannot see an uncommitted worktree. The overlay is designed
  but unbuilt.
- ✅ **#136 is FIXED** (bbe367f): the retry seam's runtime guard no longer goes blind out-of-tree. It
  now REFUSES to certify what it cannot see. Packets 17/23 are UNBLOCKED.

## PROVE WHICH TREE YOU ARE TESTING, OR YOU ARE NOT TESTING ANYTHING (#24 · #139 · #140 — three instances)
**The identity of the code under test is NOT obvious, and it is NEVER checked unless you check it.**
Three separate instruments have now been fooled by this, in three different directions:
- **#24**: in the container, astroid resolves project imports to the INSTALLED site-packages copy, not
  the mounted source → dead-code false positives on LIVE production code.
- **#140**: a **`cp -a` copy of this repo NEVER RUNS ITS OWN PRODUCTION CODE.** The copied `.venv`
  carries an editable `.pth` naming an ABSOLUTE original path, so `import loremaster` resolves to the
  ORIGINAL checkout; and `cp -a` preserves mtimes, so the stale `__pycache__` carries the ORIGINAL
  `co_filename` too. **A mutation proof or reference build made in a naive copy is grading the tree it
  was supposed to be isolated from — and NOTHING TELLS YOU.** The copy looks isolated. `git diff` shows
  your mutation. The tests run. They are simply not running YOUR code.
- **#139 / packet 01a**: the in-container conformance run must assert `loremaster.__file__` is in
  site-packages (**mount the TESTS, import the ARTIFACT**) or the whole gate is theatre.

**THE LAW: any scratch copy, reference build, or isolated run ASSERTS ITS OWN PROVENANCE before it is
trusted.**
```bash
./scripts/scratch_copy.sh /abs/path/to/copy    # excludes the poison, uv syncs, ASSERTS provenance (non-zero if poisoned)
```
**Use the tool** — a recipe re-derived in every brief is a defect generator; `scratch_copy.sh` is the
recipe as ONE call that fails loud rather than handing back a poisoned copy. If you must roll your own,
assert it: `assert Path(loremaster.__file__).resolve().is_relative_to(SCRATCH_ROOT)`.
- **Every agent doing a scratch mutation proof PRINTS `loremaster.__file__` in its report as a
  receipt.** Packet 01's exposure was NIL only because the careful agents did this voluntarily
  (PYTHONPATH-shadowed + verified) or mutated the real tree with a content backup. **That was the habit
  working, not the tooling** — now the tool exists, so the habit is `scratch_copy.sh`.
- **This is the same law as #136's fix, one level up:** a gate must never return a verdict it cannot
  substantiate, and "I tested it" is a verdict about a TREE. If you cannot name the tree, you have not
  tested anything.
- **THREE poison modes, all measured (#140):** (1) the copied venv's editable `.pth` names an ABSOLUTE
  original path → `import loremaster` resolves home; (2) `cp -a` preserves mtimes → the stale
  `__pycache__` carries the original `co_filename`; (3) a plain `uv sync` in a copy installs NO
  workspace members → `import loremaster` succeeds as an empty NAMESPACE PACKAGE with `__file__ = None`
  and no production code loads. `scratch_copy.sh` closes all three (`--all-packages`, not a plain sync).

## Orchestration (multi-agent phases)
- The lead writes no code — tests included. Ladder: ground-truth verify → TaskStop →
  respawn fresh (never reuse a teammate name).
- **LEAD MODEL (operator, 2026-07-14): OPUS orchestrates packets by default — Fable
  context is never spent on agent management.** Fable appears in exactly two shapes:
  the design sidecar on the INDEX-marked design packets (10/17/25/33/35/39), and the
  escalation valve on the INDEX-named triggers (two failed fix-waves at one gate ·
  production-touching surprise · unresolvable spec ambiguity · NO-GO with cross-packet
  residuals). The safeguards that once demanded a heavier lead are procedural law the
  lead RUNS, not IS.
- **THE FABLE-SIDECAR PATTERN (operator, 2026-07-14):** spawn ONCE per session as a
  **general-purpose agent — NEVER a fork** (forks inherit orchestrator identity; memory:
  orchestration-fork-and-path-hazards) — and keep it **LONG-RUNNING for the whole
  packet** so follow-up questions answer from already-loaded context instead of
  re-reading the world. Front-load the spawn brief: the design question, the exact file
  pointers (spec, packet, DESIGN-LAW sections, relevant findings), and the standing
  instruction to STAND BY for follow-ups after each answer. Follow-ups travel via
  SendMessage — sanctioned HERE because a standing-by consultant is AT REST between
  questions (the one shape inbox delivery is reliable for); its reply is its receipt.
  Its idle-between-questions state is BENIGN — never wake-loop it, and exempt it from
  the idle-gate until its design doc is owed. Never respawn per question; if it must be
  respawned, suffix the name (standing law). Its output is a DOC + recommendation —
  the operator rules; the consultant decides nothing.
- Directives travel ONLY in fully-front-loaded spawn briefs; the inbox is advisory
  both directions; proof of receipt is the recipient's artifact (or its process on
  the process table). An idle agent with a live gate-pytest + self-watcher is the
  benign waiting-on-own-wake mode — do not double-drive it.
- **AGENTS ROUTE CONTENT THROUGH THE DURABLE LEDGER; NATIVE IS A THIN WAKE ONLY (2026-08-10).**
  Every spawn brief instructs the agent to register on `lore_comms` and route status /
  coordination / forks there (and to `lore_findings` / `lore_tasks` as apt); native SendMessage
  carries ONLY a wake to an AT-REST agent, never content. The one message an agent sends the lead
  is the brief-base §1 terse disambiguated micro-format (`STATE · REPORT-path · headline`) —
  detail is PULLED from the ledger/report, never pushed into the lead's context. WHY: no hook can
  filter or reshape what the lead sees (measured 2026-08-10, doc-cited — Claude Code's
  teammate→lead notifications are auto-delivered mailbox traffic, not a lead-side hook event), so
  the agent's own outbound message text is the ONLY control surface for the lead's per-wave
  context cost. Prefer ONE-SHOT agents that deliver and exit over STANDING-BY agents (the design
  sidecar excepted): a standing-by agent re-idles repeatedly, and each idle is a contentless ping
  the lead must triage.
- Briefs use the versioned base protocol: the agent's FIRST action is
  `Read ~/.claude/orchestration/brief-base.md`, and its report opens with the
  `brief-base v<N> read` receipt (missing receipt ⇒ treat as unbriefed). The brief
  itself carries only: identity/mission, writable-set + do-not-touch, task-specific
  steps/receipts, the lore ToolSearch load line, and any override of the base. This
  repo's specifics (gates, dogfood protocol) ride THIS file — never re-transcribed
  into briefs.
- **THE STORE REFERENCE IS A REQUIRED FIRST READ — `docs/reference/surrealdb-31-capabilities.md`.**
  Before ANY change to the store, the schema, or the DDL — by the lead or by an agent —
  that file is read FIRST, exactly like `brief-base.md`. Every store/schema/DDL spawn
  brief carries it as a NUMBERED FIRST STEP (the brief is the only guaranteed-read
  channel). Its facts are **CITED, never re-transcribed** — a copy in a brief is a copy
  that goes stale, and the duplicated store-idioms crib that used to live on this line is
  exactly the thing it replaces. It is the ONE canonical home for: the DDL/migration
  decision rule (`OVERWRITE` for fields, `IF NOT EXISTS` for indexes/analyzers/tables,
  and why `ALTER` is a trap), the DML idioms (CONTENT for protected-key writes —
  `session` is protected; `str(RecordID)`; missing SELECT projection reads None; CONTENT
  datetimes are Python datetimes; the `time::` family for datetime aggregates under GROUP
  BY), `statement[0]`-only validation, RELATE's bound-RecordID form and its dangling-edge
  hazard, hot-row mint law, the syntax gotchas, and the section that can exist nowhere
  else: **where the vendor's docs are FALSE**.
  **WHY, plainly: #107 was a 100% production outage whose answer was ALREADY IN THAT
  FILE.** Five agents, a cold audit, a contract-adversary and the lead all probed the
  engine from scratch instead of reading it. The knowledge existed; the POINTER did not.
  A fact that is written down and unread is a fact we do not have.
- **A CONTRACT NEEDS AN ADVERSARY BEFORE A BUILDER (operator, 2026-07-28).** The order is
  **contract → adversary → build → cold audit**, and no contract revision skips the
  adversary because it is "small" or "just implements what the adversary already asked
  for". ⚠ **Receipts, same day, twice:** wave `r5` closed six adversary-found pins and went
  STRAIGHT to a builder; a later delta pass found **two more wrong builds that passed all
  234 pins** — one restoring the very false clear the packet exists to close — plus a Leg-1
  table with **2 of 4 rows measurably false**. The build happened to be clean, which is
  luck, not process: nobody knew that until after it shipped. And r5's own declared RED
  count did not reproduce (163/69 claimed vs 165/69 over 234 collected), unnoticed because
  the lead's verification ran a DIFFERENT FILE SET — *"I verified it" is a claim about a
  SCOPE, not a fact.* A fix wave is exactly where an adversary is cheapest and most needed:
  it is written by someone who has just been told what they missed, which is the state most
  likely to produce a narrow patch that satisfies the letter of a finding.
- Reports: REPORT-<agent-name>.md at repo root, EXACT name. One concern per commit;
  cold REFUTE audit before every wave commit (builder ≠ grader; P8d receipts: 3 of 4
  waves shipped a defect green at every builder gate and only the cold audit caught it).
- **ARCHIVE REPORTS — NEVER DELETE THEM (operator, 2026-07-21; this REPLACES the old
  "delete all before any image build" rule, which was the root cause of #152).** The repo
  root must still be clear of `REPORT-*.md` before an image build, but the way you clear it
  is `git mv` into `docs/plans/v2/receipts/<YYYY-MM-DD>-<packet>/`, as part of the wave's
  close-out — never `rm`.
  **WHY, measured (#152 / #153):** the old rule mandated an address *and* mandated its
  destruction, with no step in between that preserved the content. Every citation an agent
  wrote pointing at its own or a sibling's report dangled the moment the wave closed — not
  stale, **absent**. Derived 2026-07-20: **57 distinct `REPORT-*.md` names cited across
  `loremaster/`; only 3 resolved; 54 dangled.** The 3 that resolved were exactly the 3 that
  had been archived — the convention already worked, it just was not law. Archiving eight
  surviving #150-wave reports (`7d2ff44`) cost one `git mv`; **seven of the eight were cited
  ZERO times and the eighth once, so it repaired exactly ONE dangling address** — the value
  was preserving eight waves' reasoning before the old rule destroyed it, not the citation
  count.
  ⚠ **AND THE SENTENCE ABOVE IS ITSELF A RECEIPT.** It first shipped claiming *"15 citations
  resolve at a stroke"* — a number that matches NO scoping of the tree. It came from counting
  bare AGENT-NAME mentions (`blindreader-150 F3`, 16 of them) and reporting them as report
  ADDRESSES (1). Archiving a FILE cannot make a prose mention of a NAME resolve; there is no
  address to follow. **Two populations, conflated into one count — the #102/#120 defect, in the
  law written to stop it, by the lead who had just written "re-derive before acting" into the
  brief.** A cold audit caught it. Re-derive every number you inherit, INCLUDING from this file.
  **So: cite the archived path, and cite it section-exactly.** A citation naming a report is
  a durable address only once the report is tracked; until then it is a promise you have
  already broken. Prefer, in order: a committed script that regenerates a measurement > a
  tracked `docs/plans/v2/receipts/…` path > a finding number > a commit SHA > an in-tree
  symbol or test name. **Never cite a bare `REPORT-*.md`, a `scratchpad/` path, or a `/tmp`
  path** — those are unrecoverable by construction, and #154 exists because two modules bound
  themselves to specs at exactly such addresses.
  **And cite SYMBOLS, not LINE NUMBERS.** `scout.py`'s `_scout_query` survives an edit above
  it; `scout.py:171` is stale the moment anyone inserts a line. Measured in one session: a
  wave's own fix shifted three seams (`171→176`, `571→576→578`, `599→608→610`) and falsified
  nine prose citations, twice — renumbering would have shipped stale *within the same
  session*.
  ⚠ Archiving is not free of judgement: a report that is superseded or wrong gets archived
  **with a one-line header saying so**, not silently preserved as if current. The point is
  that the address resolves, not that every archived claim is true.
- Lead context checklist (P8d retro + fresh-Fable review, 2026-07-06): consume report
  SUMMARY BLOCKS first — Read(limit≈40) — and the body only for rulings/audits; point
  briefs at spec/scout files, never transcribe them; agents drive their OWN ledger
  rows (brief names the id); a stale notification for a stopped agent gets zero tool
  calls; keep design/spec authorship in dedicated design agents, consumption by
  pointer. Resume docs carry PHASE STATE ONLY — process law lives here.
- Verification law (operator-amended 2026-07-06, F3): for AUDITED work, the cold audit
  is the ground-truth instrument (it re-runs gates/probes); the lead keeps judgment
  reads + one random receipt re-run per batch. For anything committed WITHOUT a cold
  audit, the lead verifies in full: re-run the tests, read the diff, confirm the
  number. The global Working Discipline carries the canonical wording.
- lore_tasks state machine: claimed → in_progress → done (claimed→done is illegal).

## LEAD PROTOCOL — read it, don't re-derive it
The lead of any multi-agent wave reads `~/.claude/orchestration/lead-base.md` at wave start
and opens its wave report with `lead-base v<N> read`. It carries the required report fields
and the DO / DO NOT list. Do not restate it here.

## Deploy
- Rebuild + recreate, never restart, after loremaster changes (the container bakes the
  code; the mount is read-only reference). Capture `podman inspect <name> --format
  '{{.Config.CreateCommand}}'` BEFORE rm. lore-lore boots ~150s (eager), DI ~5s.
- smoke_p8b full mode files a dogfood finding row each run — resolve it as a smoke
  artifact (duplicate of #1), not a live defect.
- spike-surreal ws://127.0.0.1:18000 is the test store; :18500 is production
  lore-surreal — never point tests at it. Both stores are systemd/quadlet-managed
  (`~/.config/containers/systemd/{lore-surreal,spike-surreal}.container`,
  `WantedBy=default.target` + linger) and auto-start on boot — no manual
  `podman start` post-reboot. Manage via `systemctl --user {start,stop,restart}
  {lore-surreal,spike-surreal}.service`. Full teardown recovery (image + both
  stores gone): see memory `surreal-stores-systemd-managed`.
