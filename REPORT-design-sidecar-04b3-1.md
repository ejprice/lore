# REPORT-design-sidecar-04b3-1 — scoping + design rulings for packet 04b-3

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- **state: done** — all rulings issued (A–D). Advisory report; this file is my only writable artifact.
- deviations: (1) I RULE `#304` to **05a (wait-surface)**, overriding the stale "04b-3" home in
  the finding body — reason in §D-#304 (the finding predates the 05a split ruling; derive-waiting-
  from-the-ledger IS the await story). (2) I recommend **two** new mints (04b4 SERVED, 04b5
  INJECTION), where the brief anticipated one 04b4 — reason in §A (three genuinely-coherent,
  individually-sized groups; cramming any two breaks either the sizing law or #321's all-or-nothing
  + roster law).
- **Packages considered:** `networkx` 3.6.1 (installed, operator-authorised @`54d0585`) → **replace**
  the hand-rolled all-cycle walk in `TaskLedger._record_legacy_cycles` (read: #273's four-topology
  oracle table + the ack-note five-shape verification) — moves it from dev/test-oracle to a
  **production import** ⇒ image dep + the `[[tool.mypy.overrides]]` block moves to production scope
  (#272). `graphlib` (stdlib) → **keep_with_trigger** for write-time cycle DETECTION (one witness
  suffices; trigger: none foreseen). `#321` seam → **bespoke-by-in-house-composition** (`render_attributed`
  composes the existing `sanitise_line` + an **extracted** shared width rule — the ONE-IMPLEMENTATION
  in-house rule, NOT a hand-roll; see §B). CA-12 index → no package (a SurrealDB `DEFINE INDEX` on
  the edge table, store ref §4). Read column present for each: yes.
- **Graded:** 338abe0 · HEAD-at-report: 338abe0 · SAME. (Rulings rest on the tree at `338abe0`;
  live facts ground-truthed this session are dated inline.)
- decisions-needed (none blocking under the standing delegation; §7 collects them):
  (1) two new mints vs one; (2) #321's dnd-reachability sharpening — full fix is a HARD precondition
  of packet 56 go-live, and the 2026-08-02 local-threat-model acceptance may not have priced the
  player-reachable `lore_findings` surface; (3) deploy vehicle — 04b-3/04b4 commit-only riding 05a's
  deploy, with a #319 live-lie exception trigger; (4) #304 re-homed to 05a; (5) an ENTRY-CHECK owed
  on whether R4's fleet unread/unacked columns + S2 age-render shipped in 04b-2 (S1-a IS live —
  measured this session).
- receipt pointers: predecessor handoff `receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md`
  §B1 L3/§B2/§B4/§B5 · ESC-1 verdict + verbatim instrument `receipts/2026-08-01-agent-comms-fix/REPORT-probe-esc1-closure-1.md`
  §1/§5/§6 · findings #321 #304 #309 #310 #319 #322 #324 #273 #272 (live ledger, read this session)
  · store reference §3/§4/§5/§6.4 · dnd scope `docs/design/2026-08-02-dnd-graph-scope-rulings.md` §4
  · seam symbols `render.py::render_fenced`/`render_line`/`Rendered`, `sanitise.py::sanitise_line`
  (lore_verify this session; `sanitise.fence_width` = **not_found**).

**Authority:** operator ruling 2026-08-03 — *"Fable makes all the calls. The operator is not the
consumer."* Everything below is a RULING under THE CONSUMER LAW (lore's consumers are AGENTS). Items
an on-line operator would normally weigh are marked ⚠ OPERATOR-REVIEWABLE and collected in §7.

---

# §A · SESSION SCOPE — the decisive ruling

## The self-check question
*"Does this item ride THIS session because it is cheap AND cohesive with the session's chartered
identity — or is it here only because it was routed to a row that has no room?"* Anything that is
neither cheap nor session-critical **splits** (the SIZING FENCE), and #321 splits for a second,
stronger reason: it is all-or-nothing and a property-to-INVENT.

## The three coherent groups (why not one session)
The routed set factors into **three** cohesive areas, each independently ~0.15–0.22 wu, plus two
loners. Cramming any two either breaks the ≤0.25 sizing law or breaks a harder law:

| group | items | where it lives | why it is one unit |
|---|---|---|---|
| **CYCLE** | ESC-1 mechanism · #273/#272 · CA-11 · CA-12(defer) | `loremaster.tasks` write-path cycle machinery | one code area, **one adversary pass** over the write-path cycle guard; 04b-3's chartered identity (INDEX row 204) |
| **SERVED** | #319 · #309 · #310 · #322 · #324 R-2/R-3/R-4 | server.py served descriptions/renders + the dispatch tests | served-prose-DERIVATION + test-instrument hardening; all the "served English no gate checks" class |
| **INJECTION** | #321 | the render seam (`render.render_attributed`) | **all-or-nothing** (partial containment is WORSE than none) + **property-to-INVENT** (roster law: its own author attacks its own design) — cannot share a session |

Loners: **#304** → 05a (wait-surface); **CA-12** → DEFER (measure-then-tune).

## The IN / SPLIT / DEFER table (ranked; one Consumer-Law reason per row)

| item | ruling | Consumer-Law reason |
|---|---|---|
| **ESC-1 mechanism** | **IN 04b-3** | Build-ready (measured YES, §B2 of predecessor + the archived probe). Data-integrity guard on a served graph; net simplification (deletes a known-bound pin). Chartered identity. |
| **#273 + #272** | **IN 04b-3** | ONE edit, verbatim spec (§B4). ONE-IMPLEMENTATION law: a hand-rolled twin carries maintenance + lacks upstream coverage *even when it works at landing*. Cohesive with ESC-1; a wave touching `loremaster.tasks` (its trigger). |
| **CA-11 (TOCTOU)** | **IN 04b-3** | Same cycle machinery as ESC-1 — doing it in the same session buys ONE adversary pass; re-entering later reloads the whole context (don't-kick-the-can). A concurrent racer can write a jointly-cyclic edge no single check saw ⇒ a served blocker/critical-path render can then show a cycle: a served correctness hole. |
| **CA-12 (no index)** | **DEFER (trigger)** | Measure-then-tune: an index applied blind is plausibly negative value, and store ref §4 shows a traversal never uses one anyway. Trigger: first measured cycle-read/claim latency past budget, OR ledger growth past the dependency-bearing population. |
| **#319 (limit desc + sweep)** | **SPLIT → mint 04b4** | LIVE served lie since R9 (the paramount property). It teaches agents AWAY from the very ESC-5 affordance this wave built. Highest single Consumer-Law priority — but deploy-gated (see §A-deploy), so its session ORDER is logistics, not consumer-harm timing. |
| **#309 (no-limit display cap)** | **SPLIT → 04b4** | An unimplemented operator ruling (R9) on a served task read; pairs with #319's tasks-surface edit; the counted-line grammar must degrade in the SAME edit. |
| **#310 (validate-before-transform)** | **SPLIT → 04b4** | A refusal that names a value the caller never passed is a served lie about the caller's own input; the class → a repo-local invariant (repo law). |
| **#322 (∀ fixture invariant)** | **SPLIT → 04b4** | Protects the contract that protects the served surface; needs the in-session contract-adversary it could not get mid-wave (roster law). |
| **#324 R-2 / R-3 / R-4** | **SPLIT → 04b4** | Instrument hardening: R-3 closes an ASYMMETRIC coverage hole (a dead *findings* action goes undetected where the *tasks* twin goes loud-RED) on a served dispatch surface; R-4 keyword-requires the params that gate the injection seam; R-2 promotes a parity probe to a standing pin. |
| **#321 (Link-5 injection)** | **SPLIT → mint 04b5, before pkt 56** | Highest STAKES (a forgery here is an INSTRUCTION agents obey, not a row they misread) AND reachable (§A-reachability). But all-or-nothing + property-to-invent ⇒ its own contract→adversary→build→audit. Local threat model holds until "in the wild"; the trigger fires at packet 56 go-live. |
| **#304 (latched input_required)** | **→ 05a (wait-surface)** | A served over-claim (a badge asserting a debt already discharged). "Derive waiting from the ledger" IS the await story = 05a's charter, not a tasks residue. |

## The primary partition (RULED)
- **04b-3 = the CYCLE session** — ESC-1 mechanism + #273/#272 + CA-11; CA-12 deferred. Chartered,
  build-ready, one adversary pass over the write-path cycle machinery. **~0.18–0.22.**
- **MINT 04b4 = the SERVED-SURFACE + INVARIANT session** — #319 + #309 + #310 + #322 + #324
  R-2/R-3/R-4. **~0.20.**
- **MINT 04b5 = the INJECTION session** — #321, sequenced **before packet 56 go-live**. Its own
  design-attacking author (roster law).
- **#304 → 05a.** **CA-12 → DEFER.**

**Why CYCLE goes first even though SERVED outranks it by Consumer Law:** both slices are commit-only
and reach the consumer only at 05a's deploy (§A-deploy), so building order does NOT change when the
consumer stops being lied to. The tie breaks on cohesion + build-readiness + charter: CYCLE is
build-ready *now* (ESC-1 measured YES, the instrument is inherited verbatim, #273 is a verbatim
spec) and is 04b-3's chartered identity. If new evidence lands #319's own re-open trigger (an agent
report of a refused-but-documented parameter), elevate SERVED and give it an own-deploy.

## ⚠ #321 reachability — the sharpening the brief asked me to weigh (§A-reachability)
Comms/tasks/claim_task are DISABLED in the dnd surface, but `lore_findings` is **ENABLED at the tool
level** (dnd scope §4). So a player's agent can `report` a finding with a hostile
subject/body/created_by and ANOTHER player's agent reads it via `get`/`query` — #321's injection
surface is **reachable across principals** on the dnd instance. Two consequences:
1. **The full Link-5 fix (#321) is a HARD PRECONDITION of packet 56** (off-LAN go-live). At 56,
   external principals exist ⇒ #321's own re-open trigger ("comms exposed beyond the local
   operator/agent context") FIRES. Per-principal WRITE gating (packet 39) does not help: an
   authenticated external principal can still file a hostile finding another player READS. 04b5 must
   land + deploy before 56.
2. ⚠ OPERATOR-REVIEWABLE: the 2026-08-02 local-threat-model acceptance and the dnd-findings-enabled
   ruling are **the same day**. At packet 54 (LAN-only local soak, no auth) the reachable principals
   are still the operator's own agents, so the acceptance still holds there. But the operator should
   confirm the player-reachable `lore_findings` surface was in view when the acceptance was made —
   if it changes the calculus, 04b5 pulls earlier than 56.

## ⚠ Deploy vehicle (§A-deploy, RULED)
**04b-3 and 04b4 are commit-only** (TEST + production-code + image-dep prep); their production
changes ride **05a's deploy** (05a "deploys" per the split ruling). Rationale: 04b-2 deployed
2026-08-03 and none of 04b-3/04b4's changes is a live served lie severe enough to justify
deploy-stacking a day later (ESC-1/CA-11 = internal guard correctness; #273 = a MEASURED non-defect
DRY swap; #319 = a weeks-old prose lie, not an outage). **Rider:** 05a's deploy now carries the
**networkx production image dependency** (#273) — its smoke owes an "import networkx in the deployed
image" line, and its gate inherits the CYCLE machinery. **04b5 (#321) MUST deploy before packet 56**
— either its own deploy or riding the wave-C/D deploy immediately preceding 56.

---

# §B · #321 — Link-5 injection containment (BUILD-READY; I attacked my own design)

## The question an agent asks itself
*"What UN-ATTRIBUTED CALLER BYTE reaches a served answer, and which partition half holds it?"*
and, on any build: *"What wrong build (a bare f-string; a `Rendered` demoted to `str`) still passes
this pin?"*

## Ruling B-1 — the PARTITION (derived, not curated)
Every caller-origin string that reaches a served answer is **either** charset-gated at write (Link
1b) **or** render-contained at read. The two halves PARTITION the surface; a member in neither is a
**door named `file:line`**. The partition is DERIVED — the complement of the Link-0 scan over the
registered `inputSchema` universe — exactly as `registration_sites.py` derives sites from a
property, never a hand-list.

**⚠ Design correction — this broke my first framing (self-attack #1, the substantive one).** The
partition is NOT over registered WRITE params. A param can be charset-gated at write yet its
**stored historical rows** (written before Link 1b existed) are un-gated; any RENDER of that stored
free text (finding subject/body/note, task subject/description/summary, brief bodies) is therefore
un-gated at read regardless of the write param's status. So:
- The partition is evaluated **at the RENDER SITE** (every place a caller-origin byte reaches a
  served answer), not at the write param.
- **Render-containment is the DEFAULT for all stored free text.** Charset-gating removes a site from
  the render-contained obligation **only** for a value that is *fresh-in-this-call and never
  persisted* (an inline echo of a just-passed param). For anything read back from the store,
  charset-gating is defense-in-depth, not a partition exemption — because you cannot prove every
  historical row was gated.
- This SHARPENS (does not contradict) #321's own stated bound: "older-schema-row values are OUTSIDE
  it." That bound is the escape hatch, with its trigger — but it means render-containment, not
  charset-gating, is what actually holds the line for stored text.

## Ruling B-2 — the SEAM (ONE IMPLEMENTATION; extract before you compose)
A new **inline** primitive `render.render_attributed(value) -> Rendered`:
1. `sanitise_line(value)` — collapse control chars / newlines / bidi / zero-width to a single
   visually-honest line (`sanitise.py::sanitise_line`, verified this session: 36 prod / 12 test
   callers, returns `SafeLine`).
2. wrap the sanitised value in an **inline** delimiter (a backtick span) whose width is
   `fence_width(value)` — strictly longer than any backtick run inside `value`, so the caller cannot
   close the delimiter early and escape as forgeable text.
3. return `Rendered`.

**⚠ Load-bearing FLAG — `sanitise.fence_width` DOES NOT EXIST as a symbol** (lore_verify @338abe0:
`not_found`). #321 calls `render_attributed` "the SECOND consumer of Ruling 9's
`sanitise.fence_width`," but the width rule is currently **inline** in `render_fenced`
(`fence = FENCE_CHAR * max(MIN_FENCE_WIDTH, max_backtick_run(body) + 1)`, `render.py::render_fenced`).
So step 0 of the build is to **EXTRACT** that rule into ONE named function
(`sanitise.fence_width(text) -> int`, returning `max(MIN_FENCE_WIDTH, max_backtick_run(text) + 1)`);
`render_fenced` becomes its **first** consumer, `render_attributed` its **second**. Do NOT clone the
`max(...)` expression — a pattern to clone is a defect to clone (#102). **Prove sharing by
MUTATION:** perturb `fence_width` and BOTH consumers' pins must redden (declared-RED sets from
`--collect-only` before the run, #194/#196).

**⚠ Self-attack #2 (broke my first seam choice):** my first instinct was to reuse `render_fenced`
(a block fence) for attributed values. That DESTROYS inline rows — a task-detail line
`owner: X · actor: Y` cannot block-fence each value. #321 rejects `render_fenced` for exactly this.
`render_attributed` is a distinct INLINE delimiter primitive that SHARES only the width rule — which
is precisely why the extraction (B-2) is the correct move rather than either cloning or overloading
`render_fenced`.

**NOT bare `sanitise_line`** (control-char policy only, applied by call-site accident at 122 sites —
blind to same-line instruction forgery). **NOT `render_fenced`** (line-structural). **Errors route
through the seam, never `!r`** — the 8 `TaskNotFoundError(f"...{task_id!r}")` sites in `tasks.py`
(and the 154 `!r`/19-module population) route their caller-supplied id through `render_attributed`.

## Ruling B-3 — the OUTPUT-HALF sweep (runtime; reach is a CHECKED variable)
A RUNTIME sweep, because `Rendered` subclasses `str` and every static gate (mypy, the AST template
pin, the mint pin) is BLIND to a demotion. Requirements, all mandatory:
- **Reach as a checked variable:** AST-enumerate every served-answer call site that embeds a
  caller-origin byte; the runtime instrument asserts EACH was OBSERVED. An unobserved site is a
  named gap, not a silent pass (the six-defeats lesson: a runtime gate is an invariant only over the
  code it actually RUNS).
- **Positive controls:** a `repr`/bare-f-string reference build MUST make the sweep FAIL, and fail
  *for the repr/forgery reason* (not a parse error) — pair every neutralised result with a
  demonstrated firing on a known-broken build (PKT-28 C1 probe-needs-a-control law).
- **All-or-nothing:** partial containment is WORSE than none — the delimiter becomes a trust signal
  a consumer applies to every bare render, manufacturing a false clear on each skipped surface. The
  sweep gate is pass-iff-ALL, never per-surface.

## Ruling B-4 — the discriminating pin is BEHAVIOURAL (B5's shape, generalised)
A hostile fixture: an identity/free-text value containing a FOOTER/ROW-SHAPED FORGERY + newlines +
backtick runs must render NEUTRALISED in the served bytes. A bare-f-string build serves the forgery
verbatim ⇒ RED; an isinstance pin on `render_attributed`'s return + a mutation proof (swap the
`Rendered`/seam build for a bare f-string; declared-RED = the forgery pin; diffed both ways). No
type check can see this — the pin catches the wrong type/seam choice by its CONSEQUENCE. Fixtures
must DISCRIMINATE: interrogate each with "what wrong build passes this?" (empty/whitespace value →
`` `` `` empty inline span: pin it as neutral, not a forgery).

## Ruling B-5 — BOUNDS + re-open triggers (name every one)
- **In scope:** registered-tool-parameter values reaching a served answer (fresh echoes AND, via
  B-1's correction, reads of stored free text).
- **OUT, each with its trigger:** config values (trigger: a served render begins embedding a config
  string) · indexed-source values (trigger: a served render embeds indexed source text outside a
  fence) · **older-schema stored rows written before Link 1b** (trigger: a migration proves all rows
  gated, OR a served surface renders such a value outside `render_attributed` — pin the miss,
  #137/#138 shape, RED the day someone "closes" it).
- The 04b5 contract carries every trigger; the wave lands the partition, the seam, the runtime
  sweep, and the behavioural pin as ONE indivisible slice.

---

# §C · CYCLE-READ cluster

## C-ESC-1 — the ledger-independent write-path cycle read (IN 04b-3, build-ready)
**Question:** *"Is every persisted ancestor of a new dependency reachable via persisted `blocks`
edges at write time — so a write-path cycle read can ride edges, not the column ledger?"*
**Ruling: YES — BUILD it.** Measured YES (58 PASS / 0 FAIL, three consecutive green runs on fresh
throwaway DBs, tree `f72e538`, discriminating negative control; `REPORT-probe-esc1-closure-1.md`
§1/§7). Per ESC-1's own clause, the known-bound pin becomes a **defect report DELETED WITH the fix**
— not a bound to keep.

**Riders (same breath):**
- **Residue is exactly two, both named, both expected:** batch-local `create_many` siblings (no row
  exists pre-commit — client-side is the only place their links can live) and legacy phantom
  `blocked_by` entries (no row, no ancestors; `ENFORCED` forbids the edge; skip recorded at
  WARNING). Neither removes anything from a *persisted-ancestor* closure.
- **The cycle signal is self-reachability:** a cycle member's edge closure contains ITSELF
  (`truncated=False`) — probe §5.1. Use that, not a re-derived detector.
- **Edges are counted as ROWS, never traversals** (store ref §6.4: a traversal lists a DANGLING
  endpoint as a first-class member and would hide the exact divergence). All endpoints/starts BOUND
  as `RecordID`s (store ref §4/§7).
- **The constructed verbs are the COMPLETE column-writing surface:** no `TaskLedger` verb mutates
  `blocked_by` after birth (checked at `f72e538`; the only `SET` sites are the claim CAS and the
  supersede stamp). So the residue class cannot grow from a verb the probe did not run — only from
  raw writes outside the ledger.
- **The instrument is a deliverable:** the probe's verbatim script (probe §6) belongs in `scripts/`
  (committed) as the ESC-1 acceptance harness — do not let it die in scratch (brief-base §1's
  perversity clause).

## C-#273/#272 — networkx swap (IN 04b-3; ADOPT §B4 verbatim, do not re-derive)
**Question:** *"Is the hand-rolled all-cycle walk a defect or a packages-over-hand-rolling item?"*
**Ruling: a NON-defect DRY swap — do it anyway.** Zero mismatches vs `networkx.simple_cycles` on
nine adversarial shapes across two independent checks (#273 body + ack note). Adopt §B4's edit spec
verbatim: swap `_record_legacy_cycles`'s internals to `networkx.simple_cycles`; **DELETE the
hand-rolled helpers** (`_drop_one_cycle_edge` + the drop-and-retry loop) — never maintain both; the
DETECTION path stays `graphlib` (a write-time refusal needs ONE witness; stdlib). Resolve **#272 in
the same edit**: networkx moves from test-oracle to a production import, so the `[[tool.mypy.overrides]]`
block moves from the test-tree scope to production scope, and its dependency group flips
dev→runtime. `Packages considered:` line owed in the wave report. ⚠ This is the line that makes
04b-3 an IMAGE change (see §A-deploy).

## C-CA-11 — write-time cycle-guard TOCTOU (IN 04b-3; closing it is a CONTRACT change)
**Question:** *"Can two concurrent creators each pass the acyclicity check and TOGETHER write a
cyclic edge that neither check saw?"* **Ruling: YES it can, and closing it is a contract change —
close it in the CYCLE session** (cohesive with ESC-1's code; one adversary pass). The check-and-write
must be atomic: the acyclicity read runs INSIDE the same `execute_transaction` that writes the edge,
against the persisted edge set — a concurrent conflicting write then surfaces the retryable-conflict
marker and the shared retry driver re-runs the check on the updated graph.
**Riders:**
- **`execute_transaction`, never `.query()`** — `.query()` validates statement[0] only, so a failed
  in-txn re-check would read as success (store ref §3; the #124/#144 mechanism).
- **Retry rides the ONE driver** — `_txn.retry_on_conflict`; a caller that classifies the conflict
  locally is a private copy wearing the shared name (store ref §5 rule 1; ONE IMPLEMENTATION).
- **Pin at ≥8-way with OVERLAPPING lifetimes, 20 consecutive greens** — never 2-way, never a single
  green run (store ref §5 rule 1/2). The contract-adversary's attack: a build that runs the
  acyclicity check OUTSIDE the write txn is the wrong build and must go RED.
- If sizing ejects CA-11 at kickoff, its trigger is "the next wave touching the cycle machinery" —
  but ejecting it forces a fresh context to reload the same code (don't-kick-the-can), so keep it
  with ESC-1 unless the fence genuinely forbids.

## C-CA-12 — no supporting index on the cycle-graph read (DEFER, measure-then-tune)
**Question:** *"Does the cycle/blocker read need a supporting index yet?"* **Ruling: DEFER — do NOT
add one blind.** Named decision point: first measured cycle-read/claim latency past budget, OR
ledger growth past the dependency-bearing population (currently ~110 task rows — the sidecar's
measure). **Rider for whoever eventually closes it (store ref §4, load-bearing):** a graph TRAVERSAL
never uses a secondary index — every plan is a `GraphEdgeScan`. So the index must go on the
**edge table read as a plain table** (`SELECT VALUE in.* FROM blocks WHERE out = $node`, index on
`out`), NOT on an arrow traversal. Adding a traversal-side index would be a useless closure — pin
this constraint on the CA-12 row so its future closer does not re-learn it by outage.

---

# §D · SERVED-SURFACE + INVARIANT items (all → 04b4, except #304 → 05a)

## D-#319 — the served `limit` description is FALSE since R9
**Question:** *"Which served parameter descriptions are false, and what stops the next one?"*
**Ruling: DERIVE, don't correct.** Land a pin that checks each served parameter description against
the refusal matrix it describes (the Ruling-7/9/10 move: the matrix is canonical, the prose is
demoted to a citation). Then SWEEP the remaining descriptions **bare + anchor-free** (prose carries
no structural anchors) — **every hit gets a `file:line` + an individual verdict; "all remaining are
X" is BANNED** (P8d rename-sweep law). **Rider:** the pin is DERIVED from the accepted-action set, so
it reddens the day a description drifts — the durable fix, not the one-instance correction.
Consumer-Law: this lie teaches agents away from the ESC-5 re-ask the wave built.

## D-#309 — R9's display cap on the no-limit task read (unimplemented ruling)
**Question:** *"Does the no-limit `lore_tasks action=query` read serve the whole ledger?"*
**Ruling: implement R9's second clause — a DEFAULT display cap with the house counted-elision
grammar** (honest total from a store-side count; `+K more — re-run with limit=N`), and **degrade the
ESC-5 existence-line grammar to the counted grammar in the SAME edit** (the wave-C sidecar §2: the
two grammars can never both be live for one property). Cheap; pairs with #319's tasks-surface edit.
Consumer-Law: an uncapped read is the cost R9 was ruled to remove.

## D-#310 — validate-before-transform defect CLASS → invariant
**Question:** *"Does any dispatcher transform a caller parameter before the layer that validates
it?"* **Ruling: land the concrete fix + pin THIS wave; the general invariant is a diagnosis that
owes an instrument.** The concrete: promote `validated_task_limit` to a module-level function the
seam AND ledger share; the three-leg pin (limit=-1 → refuses naming a value never passed; limit=0 →
a refusal must serve NOTHING, not one row; limit=True → bool-is-int must not become LIMIT 2).
**Rider:** prove sharing by MUTATION (perturb `validated_task_limit`; both seam and ledger pins
redden — ONE IMPLEMENTATION). For the CLASS: if a cheap derived pin exists (an AST scan for
transform-before-validate on dispatch params), build it; if not, **PIN THE MISS** (#137/#138) with a
trigger rather than shipping a hope (a rule people must remember is not a guard). Consumer-Law: a
refusal naming a value the caller never sent is a served lie about the caller's own input.

## D-#322 — the name-free ∀ fixture invariant (contract phase + its adversary)
**Question:** *"When a new action joins a dispatch tuple without a fixture, does anything fail
CLOSED?"* **Ruling: BUILD the invariant, with the in-session contract-adversary it could not get
mid-wave** (roster law). Shape (from the finding): ∀ action in (TASK_WRITE ∪ TASK_READ ∪
FINDING_WRITE ∪ FINDING_READ), drive the dispatcher through that action's own `_*_action_kwargs` and
assert it does not raise a ValueError for a missing arg — DERIVED from the tuples the
parametrisations already use (name-free, cannot go stale like an enumerated list). Cover BOTH faces:
the KWARGS fall-through AND the shared-double missing-method (`FakeTaskLedger` must carry every verb
its production twin has — overlaps R-2). **Rider:** the adversary must prove the invariant
DISCRIMINATES — a fixture returning `{}` for a new action must make it RED, and a wrong build that
passes it is the missing pin.

## D-#324 R-2 / R-3 / R-4 (→ 04b4)
- **R-2:** promote the cold-audit parity probe (`scripts/audit_probes/coldaudit_wavec_r2_probe3.py`,
  the cycle leg) into `test_task_ledger.py`'s parity suite as a STANDING pin (fake-vs-real, with the
  injected-drift control). Do it WITH #322's double-parity face.
- **R-3:** add the `AppContext.findings` branch-scan pin — but **DERIVE the scanned method set from a
  verb LIST of dispatch-on-action tools** (#302/#314 family), **never clone** the `AppContext.tasks`
  scan (#102: a pattern to clone is a defect to clone). Prove by mutation: a dead findings action →
  the pin reddens (today it is undetected; the tasks twin goes loud-RED — asymmetric coverage of a
  served dispatch surface). One derivation function feeds both scans.
- **R-4:** make `name`/`to` keyword-required (no default) on `_validate_comms_identities` + its 3
  call sites — "fixture factories must not default a parameter the code branches on," applied to
  production. Consumer-Law: this seam is the one that CONTAINS the injection surface (§B); a future
  dispatcher gaining `name`/`to` and forgetting to pass it must fail loud, not bypass it silently.

## D-#304 — latched `input_required` (→ 05a, wait-surface)
**Question:** *"Is 'waiting' a FACT the render can justify, or a latched self-declared VERDICT?"*
**Ruling: DERIVE waiting from the ledger — an agent is waiting iff it holds an unanswered question
thread** (option (a)). A latched status is a verdict the render cannot justify; S2 already retired
the `⚠ STALE` badge for the same reason (serve the AGE, a FACT, not the verdict). This IS the await
story ⇒ its home is **05a**, not 04b-3 — I override the finding's stale "04b-3/C2" routing (the
finding predates the 05a split ruling). **Riders:** (c) is the floor if (a) is too costly this wave
(drain/ack clears the latch when the setting thread is answered — debt and badge die together); (b)
is the fallback render (badge + age + evidence). **ENTRY-CHECK owed** (INDEX law: a coverage premise
becomes a probe): whether R4's unread/unacked columns + S2 age-render shipped in 04b-2 — **S1-a IS
live** (measured this session: `lore_comms action=fleet` rendered "fleet (session pkt04b3)"), but
the columns/S2 status is unverified. A render showing a derived-true column beside a latched-false
badge is WORSE than either alone (#304's own argument), so if the columns are live, #304 (a)/(c)
must land WITH them; if they are UNSHIPPED 04b-2 residue, re-home the columns + #304 together to 05a.

---

# §7 · ⚠ OPERATOR-REVIEWABLE (none blocking under the standing delegation)
1. **Two new mints (04b4 SERVED, 04b5 INJECTION)** vs the brief's single-04b4 language — I ruled two
   because there are three coherent, individually-sized groups; the shape is in §A.
2. **#321 is a HARD precondition of packet 56**, and the player-reachable `lore_findings` dnd surface
   (dnd scope §4) may not have been priced into the 2026-08-02 local-threat-model acceptance —
   confirm whether that pulls 04b5 earlier than 56 (§A-reachability).
3. **Deploy vehicle:** 04b-3/04b4 commit-only riding 05a's deploy (which then carries the networkx
   image dep); 04b5 deploys before 56. The #319 live-lie exception is trigger-gated, not scheduled.
4. **#304 re-homed to 05a** (overrides the finding body's "04b-3") — lead-vetoable.
5. **ENTRY-CHECK owed** on R4 fleet-columns/S2 shipped-status at the 04b4 or 05a kickoff (S1-a
   confirmed live this session).

---

# §CYCLE-FORKS · 2026-08-03 (later) — ruling the three forks on `_refuse_a_cycle`

**Context:** `contract-cycle-04b3-1` escalated three interlocking design forks
(`REPORT-contract-cycle-04b3-1.md §FORKS`), one of which (Fork A) contradicts my own §C ESC-1
ruling. I ground-truthed before ruling (operator law: verify, don't defend), @ `4b952f3`:
- `_refuse_a_cycle` source (`tasks.py:2250`) — its docstring already states the column-walk-is-
  mandatory reasoning.
- `_drop_one_cycle_edge` (`tasks.py:707`) has **exactly two callers**: `_record_legacy_cycles`
  (`:1037`) and `_refuse_a_cycle` (`:2292`) (grep — deletion-exhaustiveness, grep's honest case).
- The three UPDATE sites (`:1533` claim CAS, `:1751` transition, `:1975` supersede) write
  owner/status/superseded_by — **none writes `blocked_by`** (grep-verified).
- The contradicting pins exist: `TestCreateRefusesToFormACycle::test_a_create_that_would_close_a_
  cycle_through_PERSISTED_tasks_is_REFUSED` (`:1931`) constructs a **column-only** closing link
  (`chain[0].blocked_by=[new_id]` raw-written, no edge) that an edge-walk guard returns "acyclic"
  on; `test_KNOWN_BOUND_..._rows_READ_DOES_grow_with_the_BLOCKED_population` (`:2176`), whose own
  docstring names *"an ancestor-closure seed"* as the candidate and says *"a builder must not be
  handed 'invent the general form'"* — i.e. this fork was PINNED to await exactly this ruling.

**Verdict up front: the contract author is right on all three. I was WRONG on Fork A and Fork C —
both retracted below.** Escalating a contradiction of my own prior ruling is the system working:
the write GUARD and the ESC-1 READ probe are different questions, and I conflated them (the MP-4a
conflation, in a §C sentence).

## FORK A — CONFIRM Reading 1 (bound the read; keep the column). §C-A RETRACTED.
**The question an agent asks itself:** *"Does the write-time cycle guard detect a cycle whose
CLOSING link can only be a column (ENFORCED forbids an edge to a not-yet-existent task) — or does an
edge-only read return 'acyclic' and wave it through?"*

**RETRACTION:** my §C-ESC-1 — "the write-path cycle read rides EDGES not the column ledger; reading
`blocked_by` columns → RED; self-reachability is the signal" — is WRONG for the write GUARD. It
took the ESC-1 PROBE's true finding (every persisted ANCESTOR of a new dependency is edge-reachable)
and mis-applied it to the guard. A cycle a create would FORM closes on a column-only link (a
persisted row whose `blocked_by` names the id about to be created — no edge exists, because the id
had no row when that column was written; measured in the `:1931` pin). An edge-only guard returns
"acyclic" and FAILS `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`.
Self-reachability (`truncated=False`) is the READ-path signal of `transitive_blockers` (already
built, pinned by `TestACycleIsDetectedOverPERSISTEDIds`) — NOT the write guard's signal.

**RULING — ESC-1's real, satisfiable deliverable (Reading 1):** BOUND the guard's read to the
**ancestor CLOSURE of the pending task's blockers**, and KEEP the column for closing-link detection:
1. seed from the new/pending task's blockers; compute the ancestor closure via persisted `blocks`
   edges (this is where ESC-1's measured YES earns its keep — persisted ancestors ARE edge-reachable
   after `ensure_ready`, so edges soundly BOUND which rows to read);
2. read the `blocked_by` COLUMNS of exactly those bounded nodes (the closing link is column-only);
3. overlay the pending columns (`create_many` sibling refs — the ESC-1 residue, no rows yet);
4. run the shared `find_blocked_by_cycle` over that bounded graph.
**Soundness (why bounding to the closure loses no cycle):** any row that closes a cycle THROUGH the
new task N must be an ancestor of N (a cycle `N→a1→…→ak→N` has `ak.blocked_by ∋ N`, and `ak` is an
ancestor of N by construction), hence in closure(N.blockers), hence its column IS read. Bounding is
sound, not a heuristic.

**This DELETES the whole-dependency-bearing-population scan (the KNOWN_BOUND), NO "columns→RED"
pin.** The pin reshape (per §ESC-1-FLAGS of the contract report, which I ADOPT):
- DELETE `test_KNOWN_BOUND_..._rows_READ_DOES_grow_with_the_BLOCKED_population` and say so in the
  wave report (its own docstring authorises the deletion).
- ADD, beside it, reusing `_blocked_noise_traffic` (ONE implementation, #102): a leg asserting the
  guard's rows-read does **NOT** grow with the dependency-bearing population — `large.rows ==
  small.rows` where the deleted pin asserted `>`. RED on the whole-population build, GREEN on the
  bounded-closure build. This is the satisfiable ESC-1 pin.
- KEEP `test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_DEPENDENCY_FREE_population` and
  `test_the_cycle_WALK_is_ONE_round_trip` green (R7's snapshot rider still holds; the read is now
  bounded to the closure AND still one round trip).

## FORK B — CONFIRM Reading 1 (helpers' fate decided WITH Fork A), with a STOP-and-flag rider.
**The question:** *"Can `_drop_one_cycle_edge` be deleted, given it has two callers?"*

**RULING:** do #273's swap AND Fork-A's guard rework in the SAME (CYCLE) session — one adversary
pass. The guard's cycle test is reformulated so it no longer enumerates-all-cycles-and-drops-edges:
it refuses **iff a pending/minted task is on a cycle**, which is a **cycle-safe reachability check
from the minted set** (does a minted task reach itself over the bounded column graph, with a visited
set) — NOT `find_blocked_by_cycle`-in-a-drop-loop. That reformulation frees `_refuse_a_cycle`'s use
of `_drop_one_cycle_edge`; #273's `networkx.simple_cycles` swap frees `_record_legacy_cycles`'s use;
then `_drop_one_cycle_edge` is deleted (never maintained beside its replacement).
**Why the drop-loop must go, not just move:** a bounded read still contains legacy cycles *if the new
task depends on a legacy-cyclic ancestor*, so a "find one cycle, is-it-minted?, else drop an edge,
repeat" loop would still be needed to step over them — UNLESS the test is reframed to "is a MINTED
task reachable from itself," which never needs to step over a legacy cycle it isn't on.
`find_blocked_by_cycle` (the shared DETECTOR, pinned by `TestTheCyclePolicyHasONEImplementation`,
also used by `server.py`'s batch-key check) is **unchanged** — #273 touches ENUMERATION, not
DETECTION.
**⚠ STOP-and-flag rider:** if the builder finds the guard genuinely still needs `_drop_one_cycle_edge`
(the from-minted reformulation proves unsound for a case I haven't foreseen), that is a STOP-and-flag
→ **Reading 2 is the sanctioned fallback** (keep `_drop_one_cycle_edge`; #273 deletes only the
drop-and-retry loop inside `_record_legacy_cycles`; the §C "delete the helpers" narrows to "delete
the loop"). It is NEVER a silent copy #2 — duplication is a design decision, escalate it (repo law).

## FORK C — RULE Reading 2 (DEFER CA-11 to a named trigger). §C-CA-11 RETRACTED.
**The question:** *"Is there a LIVE served-cycle hole under concurrency, or does the verb surface make
a persisted-id joint cycle unreachable?"*

**RETRACTION:** my §C-CA-11 — "a concurrent racer CAN write a jointly-cyclic edge ⇒ a served
correctness hole; YES it can" — is WRONG for the current verb surface. The contract author verified
(and I confirmed by reading the three UPDATE sites): no verb mutates `blocked_by` after birth; every
create mints a fresh SINK (`uuid4`, or a `create_many` id whose forward refs fail the existence
pre-check CLOSED). A task's ancestor set is FIXED at birth, so **no create — concurrent or not — can
place a task on a cycle**. The `:2397` pin agrees by construction. My "served-cycle-under-8-way-load"
discriminator CANNOT be built: the wrong build serves no cycle either (fixtures-must-discriminate,
in reverse — a pin for a state production can't reach is a hope with a filename).

**RULING: DEFER CA-11's atomicity to the named trigger — "a verb that mutates `blocked_by` after
birth lands" (an `add_blocker` / re-parent).** This is a legitimate named-trigger deferral (the
intervention's value is provably ZERO today and non-zero only when that verb exists), not a
can-kick, because the tripwire already exists and stays: keep `test_PIN_THE_MISS_a_tasks_blocked_by_
is_FIXED_at_birth` GREEN — it reddens the day such a verb lands, which is the signal to build the
atomic guard + its synthetic-adversary pin then. The `create_task` docstring's existing "fold the
acyclicity walk into the write txn" **latency** re-open trigger also stays. Do NOT build speculative
check-write atomicity now: the fresh-sink property makes creates cycle-safe under concurrency, so
neither CA-11 NOR Fork A's rework needs check-write atomicity for correctness. (If Fork A's rework
independently ends up running the bounded read inside the write `execute_transaction` for its OWN
reasons, that atomicity is KEPT as a free consequence — but it is not built FOR CA-11's future verb,
and `execute_transaction` is used, never `.query()`, store ref §3.)

## Scope consequence for §A (this supersedes §A's "CA-11 IN 04b-3")
The CYCLE session (04b-3) is now LEANER: **ESC-1 (bounded read, Reading 1) + #273/#272 (swap +
the guard reformulation that frees `_drop_one_cycle_edge`); CA-11 DEFERRED (Fork C) + CA-12 DEFERRED.**
Two deferrals, each with a named trigger. My §A table's "CA-11 IN 04b-3 (fence-gated)" row is
superseded by Fork C's DEFER. No new mints change; #304→05a and the 04b4/04b5 decomposition stand.

---
*§CYCLE-FORKS ruled 2026-08-03 by `design-sidecar-04b3-1` against `4b952f3`, on the contract
author's escalation. Fork A and Fork C retract my own §C rulings; every retraction rests on a live
read this session (the `:1931`/`:2176` pins, `_refuse_a_cycle`'s source, the two `_drop_one_cycle_edge`
callers, the three UPDATE sites). Deletion-exhaustiveness used grep (its honest case); everything
else used lore reads.*

---

# §CYCLE-TRILEMMA · 2026-08-04 — ruling MP-1 + MP-2 (adversary INSUFFICIENT)

**Context:** `adversary-cycle-04b3-1` graded the CYCLE contract INSUFFICIENT
(`REPORT-adversary-cycle-04b3-1.md`, finding #326) with a PROVEN trilemma. Ground-truthed @
`1164133` before ruling: I read the R6 MUTATION pin (`TestTheCyclePolicyHasONEImplementation`,
`test_blocks_edge.py:2319`) and confirmed its mechanism — neutralise `find_blocked_by_cycle` and
BOTH the batch-key shape (dispatcher) AND the persisted-id shape (ledger) must stop being refused.
R6 is an operator-ruled ONE-IMPLEMENTATION invariant: exactly ONE ledger-owned cycle detector.

**Verdict: the adversary is right, and my §CYCLE-FORKS FORK-B is WRONG. This is my SECOND
retraction in this chain — and it is the contract→adversary→ruling process working as designed: a
design error caught by an adversary's scratch build BEFORE a builder built it.**

## The trilemma, and why each horn was proven (I re-verified the pins, not the prose)
- **(R) my ruled from-minted reachability** — SOUND, but its `_refuse_a_cycle` calls a NEW
  `_cycle_through`, a SECOND ledger detector. Neutralising `find_blocked_by_cycle` leaves it
  refusing ⇒ the R6 MUTATION pin goes RED (22 passed / 1 failed). A correct build reddening a
  HEAD-green operator-ruled pin outside the builder's writable set. **My Fork-B was a
  ONE-IMPLEMENTATION violation — the exact thing R6 exists to forbid.**
- **(S) single `find_blocked_by_cycle` + `minted.intersection`** — 0-failed but UNSOUND, proven
  through the REAL write path (§2 store probe, exit 2): `find_blocked_by_cycle` returns the *legacy*
  cycle first, `minted∩=∅`, and `create_many` ACCEPTS a create forming a real persisted cycle
  `N→seed→X→N` when a legacy cycle coexists in the bounded closure → an unclaimable-forever task.
- **(D) drop-loop through `find_blocked_by_cycle`** — SOUND (it steps over the legacy cycle and
  keeps looking until it finds the minted one) AND passes the R6 MUTATION pin (routes through the
  shared detector). Its only "cost": `_drop_one_cycle_edge` stays.

## MP-2 — RULING: R6 STANDS. Elect variant D. From-minted RETRACTED.
**The question an agent asks itself:** *"Is the ledger's persisted-id cycle detection the ONE
shared `find_blocked_by_cycle` (R6) — or did I introduce a second detector to save a helper
deletion?"*

**RULING:** R6 wins — decisively. Option (a) from the adversary's MP-2 (sanction from-minted,
revise the R6 MUTATION pin's ledger-leg to a corpse) is **REJECTED**: it trades away a hard-won
operator-ruled ONE-IMPLEMENTATION invariant (#102's law, in cycle-detection clothing) to save a
helper deletion — the worst trade on the board. **Elect variant D**: `_refuse_a_cycle` keeps its
drop-loop, which routes through the shared `find_blocked_by_cycle` and is proven sound. This is
already what HEAD does — so ESC-1's ONLY change to the guard is Fork A's **bounded read**; the
detection MECHANISM (the drop-loop) is UNCHANGED.
- **RETRACT my §CYCLE-FORKS FORK-B "reformulate to from-minted reachability, NOT
  `find_blocked_by_cycle`."** It was doubly wrong: (1) a second detector (violates R6), and (2)
  even a bounded read still contains legacy cycles when the new task depends on a legacy-cyclic
  ancestor, so the step-over loop is *required* regardless — which the adversary proved and I
  should have seen.
- **ELECT my own pre-authorised Fork-B Reading-2 fallback:** the guard KEEPS `_drop_one_cycle_edge`.
  After #273, it has ONE legitimate caller (the guard's sound drop-loop). **This is NOT a
  ONE-IMPLEMENTATION violation** — it is a single-use helper, not a cloned policy; the twin #273
  targeted was `_record_legacy_cycles`'s enumeration, which the networkx swap kills.
- **#273 NARROWS (this supersedes §CYCLE-FORKS FORK-B):** swap `_record_legacy_cycles` to
  `networkx.simple_cycles`; **`_drop_one_cycle_edge` STAYS** (guard's caller). #272 unchanged.
- **A design option I considered and REJECTED (transparency, ONE-IMPLEMENTATION discipline):**
  refactor `find_blocked_by_cycle` into a node-scoped detector (`through=N`) so the guard asks "is
  the minted node on a cycle" through the SHARED detector — deletes the helper AND keeps R6. It is
  architecturally cleaner but is a speculative redesign of a shared, HEAD-green, R6-pinned function
  (also used by the dispatcher's batch-key check), and it would likely force revising the MUTATION
  pin's stub signature. Under the roster law ("never hand a builder invent-the-general-form") and
  the deferral law, that risk is not worth taking to delete a clean single-use helper. **D is
  minimal, proven, and preserves every invariant intact.** (If `_drop_one_cycle_edge`'s
  single-caller status ever becomes a real maintenance concern, the node-scoped refactor is the
  named future cleanup — not now.)

## MP-1 — RULING: ADD the coexisting-legacy-cycle discrimination pin (REQUIRED blocker).
**The question:** *"Does the guard stay sound when a MINTED cycle coexists with a LEGACY cycle in
the bounded closure — or does it only pass because every fixture tested a cycle in ISOLATION?"*

**RULING: ADD the pin — it is mandatory.** The existing
`test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED` is a ∀-over-inputs claim
evaluated on the ONE input where every build agrees (QUANTIFIER LAW). Add a
`TestCreateRefusesToFormACycle` leg that seeds a legacy 2-cycle among the pending blocker's
persisted ancestors AND a column-only closing link back to the minted id (the adversary's
`/tmp/unsoundness_probe.py` world — commit it to `scripts/` beside `esc1_write_path_cycle_closure.py`
so the fixture is durable, brief-base §1 perversity clause), then assert the create is REFUSED and
writes NO row. **RED on variant S** (the only build that passed the old contract), **GREEN on D**.
This pin is what makes D's soundness a fact rather than a hope, and it is why S can never masquerade
as correct again.

## MP-3 — DISSOLVED by the D ruling. Remove the helper-absence pin.
The name-keyed `test_..._drop_one_cycle_edge_is_GONE` (defeatable by rename — the six-defeats class)
asserted a deletion that D does not perform. **REMOVE it.** No invariant is lost: the #273
enumeration-twin deletion is guarded by the networkx-import pin + MP-4 + the member-coverage pin
(`TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST`), not by a helper-name gate. MP-3's "behavioural
mechanism pin" is moot — nothing is deleted.

## MP-4 — RULING: ADD the networkx ROUTING mutation pin (cheap; routing-is-not-sharing).
**RULING: ADD it.** Neutralise `networkx.simple_cycles` and the recorded legacy-cycle set must
CHANGE — mirroring the R6 MUTATION pin's own move for the detector. This proves `_record_legacy_cycles`
ROUTES through the library rather than an `import networkx` that satisfies the string pin beside a
retained hand-roll. Lower severity than MP-1/MP-2 (the count-equality complete-triangle leg already
forces a real change), but it closes routing-is-not-sharing for #273 and costs one test.

## FORK C — the adversary VERIFIED my deferral is honest (§4). Unchanged.
The CA-11 tripwire `test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth` is a live wire (proven:
the future-verb world makes it redden). CA-11 stays DEFERRED on the `blocked_by`-mutating-verb
trigger. Nothing owed.

## Net CYCLE-session shape after this ruling (supersedes §CYCLE-FORKS FORK-B)
- **ESC-1 = Fork A's bounded read ONLY** — replace `_read_dependency_graph`'s whole-population read
  with a closure-bounded read (`_bounded_dependency_graph`: seed from the pending task's persisted
  blockers, walk the ancestor closure via `blocks` edges, read those bounded nodes' `blocked_by`
  COLUMNS); **KEEP the drop-loop + `find_blocked_by_cycle` + `_drop_one_cycle_edge`** for detection.
  The KNOWN_BOUND reshape pin (`large.rows == small.rows`) stands.
- **#273** = swap `_record_legacy_cycles` to `networkx.simple_cycles`; `_drop_one_cycle_edge` STAYS;
  #272 dep/override move.
- **Pins:** KEEP the R6 MUTATION pin (green under D, unedited), the persisted-cycle pin, the
  bounded-read pin; **ADD MP-1** (coexisting-legacy-cycle discrimination — blocker) **and MP-4**
  (networkx routing mutation); **REMOVE** the helper-absence pin (MP-3).
- **CA-11 + CA-12 DEFERRED** (named triggers, unchanged).
This is satisfiable by a correct build: variant D goes 0-failed once the helper-absence pin is
removed and MP-1 is added (D refuses the MP-1 case; S does not). The satisfiability receipt turns
POSITIVE.

---
*§CYCLE-TRILEMMA ruled 2026-08-04 by `design-sidecar-04b3-1` against `1164133`, on the adversary's
INSUFFICIENT. This RETRACTS my own §CYCLE-FORKS FORK-B (from-minted) — the second self-retraction
in this fork chain, each caught by the adversarial layer before a builder built the wrong thing.
Rests on live reads this session (the R6 MUTATION pin's mechanism `test_blocks_edge.py:2319`, the
adversary's three proven horns, `_refuse_a_cycle`'s HEAD drop-loop). R6 (ONE detector) is preserved
intact; no operator-ruled HEAD-green pin is revised.*

---
*Written 2026-08-03 by `design-sidecar-04b3-1` (Fable 5, general-purpose spawn) against branch
`feat/surreal-unification` @ `338abe0`. Rulings rest on: the live findings ledger (#321 #304 #309
#310 #319 #322 #324 #273 #272, read this session), the predecessor handoff (§B1 L3/§B2/§B4/§B5), the
ESC-1 probe (verdict + verbatim instrument), the store reference §3/§4/§5/§6.4, the dnd scope §4,
and the seam symbols verified this session (`sanitise.fence_width` = not_found — the load-bearing
fact under §B-2). Where a claim rests on a measurement I did not take (ESC-1's YES, #273's oracle
diff), the archived report/ack note is cited; live facts I ground-truthed (fleet render, index
freshness, symbol existence) are dated inline. No structural claim fell back to grep.*
