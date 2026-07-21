# lore — project process law

Standing rules for every session in this repo. Distilled from operator rulings and
audited failure patterns (P7–P8d); the phase resume docs in `~/.claude/plans/` carry
*phase state only* — process law lives here.

## Quality gates (operator-ruled, every commit)
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
