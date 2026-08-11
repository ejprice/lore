brief-base v11 read

# REPORT-fable-design-05b — packet 05b design sidecar (comms LEDGER VERBS + HOOKS)

## SUMMARY BLOCK
- receipt: `brief-base v11 read`
- state: **done** — three design questions answered (Q1–Q3), plus FOLLOW-UP A (#174 supersede) and TWO
  substantial design docs from later operator-directed passes:
  **`docs/plans/v2/design/2026-08-11-task-coordination-substrate.md`** (assign / reaping / lifecycle↔liveness
  reconciliation — the #262/#356 substrate; → a coordination packet) and
  **`docs/plans/v2/design/2026-08-11-report-graph.md`** (Consumer-Law-first report graph — content-labeling,
  the `report↔symbol` payoff edge via the code graph's `name` indirection, retrieval verbs; → packet 28a).
  The two share ONE `report↔task`/`report↔agent` model. This report holds Q1–Q3 + #174; the two docs hold the rest.
- deviations: none.
- Packages considered: **none — no third-party mechanism specified.** Q1 is internal ledger code (reuse `FindingLedger._transition_fragment`'s server-side `provenance.events += [$event]` append — INTERNAL/DRY, not a library). Q2 is the existing bash+`jq` hook (`jq` is already a hook dependency — `keep_with_trigger`: trigger = the day the hook needs a value `jq` can't parse). No hand-roll vs library choice arose.
- Graded: n/a (a design recommendation, not a verdict on another artifact). All symbol/location claims **verified @ HEAD `299e69a`** via `lore_verify`/`lore_get_symbol` (`render_attributed`, `render_fenced`, `_transition_fragment`, `_render_finding_detail`).
- decisions-needed:
  - Q1: pick **(a) annotate ACTION** (recommended) vs (b) edge table — recommend (a) firmly.
  - Q1 secondary: write-path-only vs also-a-readable-notes-render — recommend write-path primary; note render is optional (existing provenance render already surfaces it).
  - Q2: adopt the **declared-artifact-contract file** mechanism; do NOT build await-detection into the bash hook. Flag the write-side↔06 seam.
  - Q3: **hand #195 to packet 06** (reasoned settlement, not a decline) — lead records the hand-off.
- receipt pointers: Q1 §mechanism = `findings.py::FindingLedger._transition_fragment` / `_transition`; Q1 render = `server.py::AppContext._render_finding_detail`; store law = `docs/reference/surrealdb-31-capabilities.md` §2 (UPDATE/array), §5 (hot-row), §4 (RELATE/ENFORCED); seam = `render.py::render_fenced`/`render_attributed` (04b5, `docs/plans/v2/04b5-injection-containment.md` §B); Q2 = `.claude/hooks/teammate-idle-gate.sh` + #149/#121; Q3 = finding #195 + `04b5-injection-containment.md`.

---

## Grounding (cited, not re-transcribed)
- **Store law** `docs/reference/surrealdb-31-capabilities.md`: §2 "`UPDATE` of a relation edge's `in`/`out` is a SILENT NO-OP" + array-column idioms; §4 RELATE/dangling-edge (#105)/`ENFORCED`; §5 hot-row mint law (retry lives in ONE driver; pin ≥8-way with overlapping lifetimes); §7 per-entry array ASSERT.
- **Current mechanism** `findings.py::FindingLedger._transition` (`:966`) + `_transition_fragment` (`:1033`): a legal transition stamps status **and** appends a provenance event via a guarded, THROW-on-zero-rows CAS. The append is **server-side** — `provenance.events += [$tr_event]` — and the docstring states the property outright: *"appended SERVER-SIDE … rather than written as a whole Python-merged object, so concurrent mutators can never clobber each other's events."*
- **Current render** `server.py::AppContext._render_finding_detail` (`:3460`): `get`/`chain_head` render the summary row + `body:` via `render_fenced(finding.body)` + `created_at:` sanitised + `provenance: render_attributed(finding.provenance)`. The **whole provenance dict (events, incl. every transition note) already renders through `render_attributed`** — the single-line 04b5 containment seam.
- **The seam** (04b5 landed — both verified `confirmed` @HEAD): `render_fenced(body)` `render.py:230` for multi-line stored free text; `render_attributed(value)` `render.py:249` for single-line attribution/id values; the width policy `sanitise.fence_width` is the shared mutation-provable thing (`04b5-injection-containment.md` §B-2). The ONE-IMPLEMENTATION fence invariant is `test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation`. ⚠ CLAUDE.md still names `loremaster.search._sanitise_line` — that is the **retired** location; 04b5/04b-2 migrated the fence onto `render.py`.

---

## Q1 — #256: the model for annotating an open/acknowledged finding

### The fork
- **(a) an `annotate` ACTION** — appends an event `{actor, action:"annotate", at, note}` to the finding row's `provenance.events` array, changing nothing else (status untouched, no state-machine edge, no new table). #256's own proposal.
- **(b) an `annotate` EDGE / relation table** — a new `TYPE RELATION` table, RELATE per note, merge-rendered back into the events timeline.

### RECOMMENDATION: **(a), firmly. Do not build an edge.**

**Reasoning, grounded in the mechanism + store law:**

1. **The events array is ALREADY the provenance home, and the append is ALREADY the proven idiom.** Every transition today does exactly what annotate needs — `provenance.events += [$event]`, server-side, inside the guarded CAS (`_transition_fragment:1033`). Annotate is the *same shape of event with a different `action` label and no status change*. It is an ~parameter of the existing machinery, not a new subsystem.

2. **Concurrency is safe BY CONSTRUCTION, and this is the load-bearing store-law point.** The server-side `+= [$event]` means the engine appends; two concurrent annotates never read-modify-write a whole Python object, so neither clobbers the other (the `_transition_fragment` docstring asserts exactly this). Where two annotates on the *same row* contend at the store level, they route through the shared retry driver via `_apply → execute_transaction → retry_on_conflict` (store law §5) — both land. This is **not a hot-row mint** (no gapless number, no counter row), so it does not inherit the 20-consecutive-run mint discipline — but it IS a concurrent-write-to-one-row and per §5 must be pinned **≥8-way with overlapping racer lifetimes**, never 2-way.

3. **An edge buys NOTHING the append does not, and costs plenty.** An annotation is a *note attached to one node*, not a relationship between two — an edge needs an `in` and an `out`, and there is no natural `out` (a self-edge or an invented `annotation` node is nonsense). An edge drags in: a new `DEFINE TABLE OVERWRITE … TYPE RELATION … ENFORCED SCHEMAFULL` (store law §1.1/§4 — `IF NOT EXISTS` is a silent no-op on an existing edge table), the dangling-edge hazard (§4/#105), `UNIQUE(in,out)` dedup considerations, and — worst — it **fragments provenance across two homes**, forcing the `get` render to merge-sort transition events (from `provenance.events`) with annotate events (from the edge) by timestamp, where today one field render suffices. Store law §4 also warns a graph traversal never uses a secondary index and returns nested `[[…]]` shapes — pure render tax for zero benefit. The edge is heavier on every axis and better on none.

4. **The staleness the repo polices is exactly what the edge would manufacture.** #256's whole argument is that forcing `supersede` (a new number) for a footnote biases agents toward leaving stale bodies alone. An edge is *more* ceremony than supersede, not less — it re-creates the friction the finding exists to remove. The append makes the honest move the cheap one, which is the finding's stated goal.

### Write-path vs render-path (secondary fork the contract author must know)
The **write path** (append the event) is the core of #256 and is near-trivial. On the **render path**, note that `_render_finding_detail` already renders the whole `provenance` dict — including every event's note — through `render_attributed`. So an appended annotate note **is already surfaced in `get`/`chain_head`** with the same visibility every transition note gets, and is **already contained** (single-line, sanitised) by the existing seam. Therefore:
- **Primary deliverable = the write path only.** No new render is strictly required; the note appears via the existing provenance render.
- **Optional enhancement (lead's call):** if the lead wants the correction *more prominent* than a dense dict repr (a dedicated readable "notes:" section), that is a **NEW render of stored multi-line free text** and MUST route through `render_fenced` with a hostile fixture — do not hand-roll a bare-line render (B-1/B-2, the served-free-text law). I recommend keeping 05b tight: ship the write path; leave prominence to a later pass unless the operator asks.

### Pins a contract author MUST cover
1. **Status is UNCHANGED after annotate — in every status.** Discriminating fixtures: annotate an `open`, an `acknowledged`, a `resolved`, and a `wontfix` finding → each keeps its exact prior status. (Wrong build to kill: one that routes annotate through `_transition`/`LEGAL_TRANSITIONS`, which either flips status or rejects.) **Annotate is legal in ALL statuses** — a stale body on a `resolved` finding is just as misleading; the value is being status-orthogonal.
2. **Annotate does NOT loosen the state machine.** Positive control paired with pin 1: after adding annotate, `acknowledge` on an `acknowledged` row STILL raises `IllegalTransitionError` (the exact edge #256 calls illegal). Proves annotate is a separate path, not a new legal transition.
3. **The note lands in provenance and renders in `get`.** After annotate, `provenance.events` has exactly one more entry, appended last, carrying `actor` + `note` + `at` + `action="annotate"` (and **no `to`/status** field — pin that the render does not fabricate a "→ status" for an annotate event; the #104 served-English-contradicts-data class). `get`/`chain_head` shows the note.
4. **Concurrency: N annotates, zero lost.** ≥8-way concurrent annotates on ONE finding, overlapping lifetimes → exactly N new events land. **The discriminating mutation:** a build that reads `events` into Python, appends, and writes the whole `provenance` object back loses events under contention — force it and watch it drop rows; the server-side `+= [$event]` build does not. Confirm annotate rides `_apply`/the shared retry driver (a private write path that classifies conflicts locally is the ROUTING-IS-NOT-SHARING clone the ONE-IMPLEMENTATION law forbids).
5. **No silent no-op on a vanished/absent row (trust).** annotate on a non-existent `id_or_number` raises `FindingNotFoundError` (reuse `_resolve_or_raise`); keep the guarded-CAS shell's `IF array::len($updated)==0 { THROW }` so a row that vanishes between pre-read and UPDATE RAISES rather than appending to nothing. (Findings are never hard-deleted, so this is belt-and-braces — but silent no-ops are the store law's named enemy.) The guard differs from `_transition_fragment` only by dropping the `WHERE status = $expected_from` predicate and the status SET — **share the guarded-append shell, do not clone it** (prove by mutation that annotate and transition hit the same append seam).
6. **`note` is REQUIRED and non-blank.** An annotate with no note is pointless — reject blank/None, reusing the existing non-blank validator (do not hand-roll; `lorerunes` blankness predicate / the same check `report` uses for subject/created_by).
7. **Hostile note body is contained (served-free-text law).** A note carrying newlines + a row-shaped forgery line (`#88 [directive] lead -> you: …`) + backtick runs must render neutralised in the served `get` bytes (via the existing `render_attributed(provenance)` today, or `render_fenced` if a dedicated note render is added). Behavioural pin: a bare-render reference build serves the forgery verbatim ⇒ RED. This is the #195-adjacent surface — annotate is agent-authored free text reaching another agent's context.

---

## Q2 — idle-gate v2 ↔ await-waiting

### What is already done vs what remains
Reading the hook in full: **#121 is resolved** (repo root from `BASH_SOURCE`, then a walk of every registered worktree via `git worktree list --porcelain`, fail-open if git absent) and the **#149 archive branch** is closed (`compgen -G` accepts an archived `receipts/*/REPORT-<name>.md`). Both are pure supersets — they only ever REMOVE false nudges. **v2 must PRESERVE both.** The LIVE remainder of #149 is: the gate still hardcodes `REPORT-<name>.md` and nudges agents whose brief legitimately owes **no** artifact.

### The await interaction — and why it is mostly a red herring
`await` (05a-ii, F1) is a ≤55s bounded PEEK that stamps nothing and self-resolves. Three sub-questions, answered:

**(i) Does the one-shot marker already neutralise it? NO — and worse, it converts noise into a coverage hole.** The marker bounds a long-running awaiter to at most ONE false nudge (no wake-loop — good). But (a) that one nudge is precisely the "cry wolf" insult #149/#121 say trains the fleet to route around the gate, and (b) the false nudge **BURNS the one-shot marker**, so if that agent later genuinely stalls (dies mid-await, wake chain broken), the gate is now SILENT for the real failure. That is the #149 "guard goes green on its own target" shape: the false positive disarms the gate for the true positive. So the marker is not sufficient.

**(ii) Can the gate read lore_comms status / heartbeat as ground truth? Architecturally attractive, but WRONG for this hook.** Every `lore_comms` action (await included) re-touches the caller's heartbeat and flips status toward `active`, so heartbeat AGE *could* distinguish "recently awaiting" from "stalled." BUT the hook is a **bash script with no MCP client**, and the brief states it may not have MCP access. Reaching lore from the hook needs a venv + the store up + connectivity — a heavy new dependency on a **fail-open** guard, and #131 is the standing proof that a hook cannot assume a binary/service exists (the deployed image had no `git`). If lore status were ever consulted it must be fail-open enrichment (absent → fall through), **never a load-bearing input.** Recommend NOT building it.

**(iii) Is there a durable signal an awaiting agent leaves? Only the lore heartbeat (unreadable from bash, per (ii)); await leaves no filesystem artifact (F1 stamps nothing).** Inventing a filesystem await-signal (await writes a heartbeat file the hook reads) couples the MCP tool to the hook's path conventions for no gain — reject.

**The reframe that dissolves it:** the right ground truth for "does this agent owe an artifact *right now*" is not the agent's liveness — it is **the brief's ARTIFACT CONTRACT** (#149's own fix: "let a brief DECLARE its artifact contract"). Key the gate on *what is owed*, and the await distinction disappears:
- A standing-by awaiter / design sidecar / drill participant declares **"owes no artifact"** → exempt, regardless of await. The gate never needed to detect "is it awaiting?"
- An agent that DOES owe a report and is mid-work with await still owes the report; a single benign nudge if it idles reportless is the gate working as designed — and the nudge text already says *"If you are mid-work or waiting on a background process, continue as you were."* Blast radius = one correctly-worded, self-limiting nudge. Acceptable; no await-detection warranted.

This is the CLAUDE.md "make coverage a CHECKED variable, don't enumerate the exceptions" principle: the gate is TOLD what's owed instead of inferring waiting-vs-stalled.

### RECOMMENDED mechanism — the declared-artifact-contract FILE
The brief declares its contract by having the agent **write a tiny name-keyed file as a first action**, and the hook reads it, **fail-open to today's default when absent**:

- **Path:** reuse the hook's existing marker convention —
  `/tmp/claude-idle-gate-$(basename "$repo_root")/${session_id}-${teammate_name}.contract` (same dir family the hook already `mkdir -p`s for `.nudged` markers).
- **Content (jq-readable):** `{"artifact": "REPORT-<name>.md"}` (owes that path) or `{"artifact": null}` (owes NOTHING) or an explicit alternate path (`{"artifact": "docs/design/FOO.md"}`).
- **Hook logic (ordered, all fail-open):**
  1. Read the contract file. **Absent or unparseable → treat as the current default** (`REPORT-<name>.md`) and run the existing root/archive/worktree checks unchanged. (This is why v2 is shippable STANDALONE: with no contract written, it behaves exactly like v1.)
  2. `artifact == null` → **exit 0** (owes nothing; the await/sidecar/drill case).
  3. `artifact == "<path>"` → resolve that path in root **and** archive **and** worktrees (the existing #121/#149 logic, applied to the declared path instead of the hardcoded name) → exit 0 if found, else the existing one-shot nudge.

**Why a file and not an env var or the ledger:** env vars of the spawned agent are NOT reliably in the hook's environment (#121 already measured `CLAUDE_PROJECT_DIR` unset for spawned agents); the ledger needs MCP the hook lacks (per (ii)). A name-keyed file is durable, bash/`jq`-readable, git-free, MCP-free, and lives where the hook already looks.

### The coordination seam the lead must know (surfaced, not a fork I can resolve alone)
The **READ side** (this hook honouring a declared contract, fail-open) is **05b Scope IN**. The **WRITE side** — making *every* agent write its contract as a standing first action — is a **brief-base change = packet 06** (05b Scope OUT: "Protocol/brief-base/drill"). These compose cleanly: 05b ships the read-side + defines the file format/path; until 06 promotes the write to brief-base, **the lead's per-agent spawn briefs can already write the contract** (a spawn-brief step is not a brief-base change), and any agent with no contract file falls through to v1 behaviour. **So 05b delivers value immediately and 06 makes it universal.** Recommend 05b's exit note name this seam so 06 inherits the write-side with the file format already pinned.

### Pins a contract author MUST cover
1. **"owes nothing" → never nudges, in EVERY idle state** (first idle, post-await, repeated idles). Fixture: contract `{"artifact":null}` + no report anywhere → **exit 0**. **Positive control (the load-bearing one — proves the exemption didn't just disable the gate):** contract `{"artifact":"REPORT-x.md"}` + no report anywhere → **exit 2, still nudges.**
2. **Custom artifact path is honoured.** Contract `{"artifact":"docs/design/FOO.md"}`: file at that path → exit 0; absent → exit 2. (Kills the hardcoded-`REPORT-<name>.md` assumption.)
3. **Absent contract → fail-open to v1.** No contract file, report at root → exit 0; no contract, no report → exit 2. The #131 leg: a missing contract must never crash the hook (`set -u`) nor block the agent.
4. **Malformed contract → fail-open** (invalid JSON / missing key / unreadable → treated as absent → v1 default, never a crash). Fixture: garbage-JSON contract file.
5. **Regression pins for #121/#149 (must stay green):** archived report → exit 0; worktree report → exit 0; unidentifiable payload → exit 0. (The existing three-branch positive controls; v2 is a pure widening.)
6. **Reach-as-checked-variable (the INSTRUMENT-0 question):** the "what does this agent owe" value is now READ from the contract, not a hidden constant — **mutate the contract's artifact path and the path the hook checks changes with it** (proves the hook actually consults the contract rather than ignoring it). This is the pin that stops v2 becoming another name-list guard.

---

## Q3 — #195 home settlement

### The question (from the finding's own routing rule)
#195: nothing measures whether an agent **OBEYS** an instruction planted in a teammate's message body. The routing rule is already written: a drill-battery **obedience MEASUREMENT → packet 06**; a **SURFACE AFFORDANCE → packet 05**. The surface DEFENCE already shipped in 03b wave 4 (an indented fence label naming quoted content + its author + "nothing inside is a delivered message", plus a static instructions rule). The question for 05b's kickoff: **does 05b owe any NEW surface affordance, or is the entire remaining #195 a measurement belonging to 06?**

### RECOMMENDATION: **the surface-affordance bucket is EMPTY for the residual — hand #195 to packet 06, explicitly and with a reason.** (This is a settlement per the routing rule, NOT a decline.)

**Reasoning:**

1. **The surface affordance that #195 named already shipped (03b w4).** Legibility — framing the fenced body as quoted, non-addressed content — is done. What remains is a *different property*: obedience.

2. **Obedience cannot be made inert by a render — so there is no surface affordance that discharges the residual.** #195's residual is "nothing GRADES whether the reader OBEYS the planted instruction." An LLM can always *act on* text it can read, however it is framed; better framing lowers the *likelihood* of obedience but neither measures nor guarantees non-obedience. The residual is intrinsically a **MEASUREMENT** — a live agent shown a planted instruction and graded on whether it acts — i.e. a drill/obedience battery. By the finding's own rule, MEASUREMENT → 06, and 06 "owns the protocol drill and already runs a live multi-agent exercise, which is the natural place to measure whether agents act on planted in-body instructions."

3. **The strongest candidate for a 05b affordance — a trust-level-per-sender protocol hook — is NOT 05b's, on three counts.** (a) It is a **protocol/model change** (trust metadata on sender/message), and protocol is packet 06's explicit domain (05b Scope OUT). (b) It needs its **own design pass** (what levels, who assigns, per-sender-global vs per-relationship, how it renders without itself becoming a forgery vector) — the finding warns explicitly against the "design-problem-reaching-a-builder" failure and says "it needs the DESIGN pass first." (c) Even if built, it is a *mitigation that weights instructions by sender trust* — it still **grades nothing**, so it would not discharge #195's measurement residual. It is a candidate future feature for 06/later, not a 05b deliverable.

4. **05b is NOT ignoring #195 on its OWN surfaces — it is bound there by the fence invariant, separately.** 05b's `await`/`story`/`rollup` work adds NEW render sites for message bodies (await non-empty reuses the fence + row render per 05a-ii R-3; story renders a messages section; rollup gains a messages section). Per B-1 and `TestEveryFenceSiteInProductionResolvesToTheONEImplementation` (04b5), every one of those new renders MUST route through `render_fenced`/`render_attributed` with a hostile fixture — which PRESERVES the 03b-w4 #195 legibility defence across 05b's new surfaces. That is a **pin on 05b's own new work** (the served-free-text law), not a new #195 affordance. Naming it here so the lead sees the obligation is covered without conflating it with the obedience residual.

### What the lead should do (so this is a hand-off, not a can-kick)
- **Record the settlement explicitly**: transition #195 with a note routing it to 06 as the obedience-measurement owner, citing (this report §Q3) the reason the surface-affordance half is empty; add the INDEX Log line. Per the finding's named decision point, "the packet that declines it must say so explicitly and hand it on with a reason" — this satisfies it. The escalation clause ("if BOTH decline → operator fork") is **not** triggered: 05b is executing the routing rule (measurement→06), not refusing a surface affordance that is 05b's.
- **Ensure 05b's own new message renders carry the fence-invariant + hostile-fixture pin** (point 4 above) — that is the whole of 05b's #195-adjacent duty.
- **If the lead disagrees** that the surface-affordance bucket is empty (e.g. wants the trust-level-per-sender hook pursued now), that is a scope-expansion decision for the operator — surface it as a fork rather than letting 05b build an unruled protocol change.

---

## Escalations / open forks
**None requiring operator input.** All three questions resolve within standing law + the routing rules the findings already carry. The two items the lead should *act on* (not adjudicate): the Q2 read-side↔06 write-side seam (name it in the exit note; the file format is pinned by 05b), and the Q3 hand-off record (transition #195 + INDEX Log). If the lead rejects the Q3 emptiness judgment, that alone becomes an operator fork (§Q3 last bullet).

---

## FOLLOW-UP A — #174 `supersede` + `blocked_by` (Track V, the ENFORCED `blocks`-edge verb)

**Grounding (verified @ HEAD `299e69a`):**
- `supersede_task` `tasks.py:1876` — sig `(task_id, *, subject, description, created_by)`, **no `blocked_by`**; body calls `_new_task_content(subject, description, None, created_by, now)` (→ successor `blocked_by=[]`) and writes `_apply([_supersede_fragment(...)])` with **no `_relate_fragment`**. Confirms #174.
- `create_task` `tasks.py:1135` transactional path: `deps = list(dict.fromkeys(blocked_by or ()))` → `await self._reject_unusable_blockers([(e,e) for e in deps])` → `await self._refuse_a_cycle({task_id: deps})` → `_apply([self._create_fragment(0, task_id, content), self._relate_fragment([(blocker, task_id) for blocker in deps])])` — ONE `BEGIN…COMMIT`.
- cycle detector `find_blocked_by_cycle` `tasks.py:637` (the ONE impl — `graphlib.TopologicalSorter`; shared + mutation-pinned by `test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation`); `_drop_one_cycle_edge` (legacy-loop skip); `raise_cycle_refusal`/`format_cycle_refusal` (ONE served sentence, two vocabularies).
- `_reject_unusable_blockers` `tasks.py:2216` → shared `reject_unknown_rows` (ruling L3), projects `_COL_SUPERSEDED_BY`, disqualifies superseded blockers via `_superseded_blocker_clause`, fail-closed and classifies store faults into the ledger vocabulary.
- `_is_blocked` `tasks.py:2564` — a blocker resolves **iff its `status ∈ TERMINAL_STATUSES` (`done`/`wontfix`)**. ← the Q4 pivot.

### (1) Inherit-default + optional override — YES to both; refuse-and-teach-on-omission is WRONG
Three reasons refuse-on-omission loses: (a) the DOMINANT supersede case is an editorial reframe (retitle/rebody) that legitimately keeps the dependency structure — forcing an explicit `blocked_by` on every supersede taxes the common case to guard the rare rewire; (b) **backward-compat is decisive** — `supersede_task` has **1 prod / 20 test** consumers and every one omits `blocked_by`; refuse-on-omission reddens all of them gratuitously, while inherit-by-default keeps them green AND correct; (c) #174's own fix options (a)/(b) lean inherit-or-param, never mandatory-explicit. So the lead's proposal stands — **with two refinements that make silent inheritance trust-correct:**
- **Sentinel discipline (pin):** `blocked_by=None`/omitted = **INHERIT**; explicit `[]` = **CLEAR all**; explicit `[ids]` = **REPLACE** (not merge/append). A build conflating `None` and `[]` cannot express "supersede AND drop all deps." Pin the 3-way AND pin it survives the MCP dispatch boundary (omitted→`None`, `[]`→`[]`). Apply create's `list(dict.fromkeys(...))` dedup to an override too.
- **Surface the result (pin):** #174's harm was VISIBILITY — a silently-wrong dep found only by a later `blocked=false` query — not inheritance per se. The supersede RESULT must NAME the successor's resolved `blocked_by` (inherited or overridden), so a rewire that forgot its override is seen at once, never advertised as ready. Check `_render_supersede_result` (`server.py:4160`) surfaces it; add the pin if it doesn't.

### (2) The exact reuse seam (share the POLICY, not the entry point)
Insert BEFORE the write, over the RESOLVED deps, the SAME two calls create makes: `await self._reject_unusable_blockers([(e,e) for e in deps])` and `await self._refuse_a_cycle({new_id: deps})`. Feed deps to the content builder create already shares: `self._new_task_content(subject, description, deps, created_by, now)` (today it passes `None`). Append the SAME mirror to supersede's own `_apply`: `_apply([self._supersede_fragment(...), self._relate_fragment([(blocker, new_id) for blocker in deps])])`.
- ⚠ **Do NOT delegate wholesale to `create_task`.** The successor CREATE must stay INSIDE `_supersede_fragment`'s stamp-CAS envelope (the CREATE is conditional on the old-row stamp matching zero rows = exactly-one-successor). Calling `self.create_task(...)` then stamping the old row = TWO transactions = orphan successor on crash / double-mint on race. Reuse the POLICY seams (`_reject_unusable_blockers`, `_refuse_a_cycle`, `_new_task_content`, `_relate_fragment`); keep supersede's OWN transactional envelope.
- **Proof-by-mutation extends the existing ONE-impl pins to a THIRD call site:** mutate `find_blocked_by_cycle` → create AND the server batch-key check AND **supersede** cycle pins all redden; mutate the shared `reject_unknown_rows` → supersede's existence pin reddens; mutate `_relate_fragment`/the `blocked_by` write → supersede's edge pin reddens.

### (3) Cycle / missing-blocker → refuse-and-teach atomically, mint nothing — CONFIRMED, plus an unnamed catch
Confirmed **by construction**: both pre-checks run before `_apply` and RAISE (`TaskCycleError` / `UnknownBlockerError`) with nothing written, exactly as create; acyclicity walks `{new_id: deps}`.
- ⚠ **HEADLINE PIN the lead didn't name — validate the INHERITED deps, not just an override.** If supersede inherits `blocked_by` and one inherited blocker was SINCE superseded, `_reject_unusable_blockers` (via `_superseded_blocker_clause`) REFUSES by name, teaching the agent to rewire onto the successor. That is trust-correct — it surfaces a stale dep rather than minting a successor whose claim CAS can never be satisfied (the #174/#130 unclaimable-forever shape). A build that runs the pre-check ONLY on explicit overrides — trusting inherited deps as "already valid" — resurrects that bug. So run BOTH pre-checks over the RESOLVED set **unconditionally**. Discriminating fixture: supersede a task whose inherited blocker is now superseded → REFUSED, not a silent successor.

### (4) The old task's edges — LEAVE them; and a grounded DUAL-defect flag
- **Leave. #105/§4 does NOT apply** — supersede DELETES nothing (the old row is kept, stamped `superseded_by`), so no endpoint vanishes and no edge dangles; §2/§4's self-delete-on-endpoint-delete never fires. The old row is kept precisely for lineage; its edges are part of that record.
- **Cleaning would be ACTIVELY WRONG:** removing the `old-T ->blocks-> dependent` edges DROPS the block, silently UNBLOCKING old-T's dependents — #174's false-unblock, from the edge side. Cleaning the `blocker ->blocks-> old-T` edges is harmless but pointless (old-T is terminal-like). Leave-all is the safe and correct choice.
- ⚠ **A DISTINCT, REACHABLE defect the #174 fix does NOT close (surfaced per scope law — your call):** superseding a blocker **STRANDS its existing dependents.** `_is_blocked` (`tasks.py:2564`) resolves a blocker only when its `status ∈ {done, wontfix}`; supersede stamps `superseded_by` but LEAVES `status` (still `open`). So a task D already `blocked_by` old-T stays blocked **forever** after old-T is superseded — the false-BLOCK dual of #174, reachable via exactly #174's own repro (superseding a task that has dependents). This is a SEPARATE defect from "the successor loses its deps." **Recommend: FILE it as its own finding; do NOT bolt a dependent-rewire onto #174's verb pass** — "supersede should rewire its dependents onto the successor" is a design question (what about a mid-flight dependent? does the block transfer or clear?) and is design-problem-reaching-a-builder territory. Your decision whether 05b scopes it or routes it.

### Additional pins a contract author must cover (beyond 1–3)
- **Atomicity WITH the added relate fragment:** a concurrent double-supersede that carries deps still mints EXACTLY ONE successor with EXACTLY its edges; the loser's whole txn (stamp + CREATE + RELATEs) rolls back → **zero orphan edges**. The stamp-CAS → CREATE → RELATE gating must survive the fragment addition.
- **ENFORCED ordering:** the RELATE must run AFTER the successor CREATE in-txn (the CREATE is statement 3 of `_supersede_fragment`; append `_relate_fragment` after it), else ENFORCED rejects `out=new_id` (the endpoint doesn't exist yet). Mirror create's `_create_fragment`→`_relate_fragment` order.
- **Old-world tests certify the corpse (P8d):** audit the 20 existing supersede tests for any asserting the successor is unblocked / `blocked_by`-empty — a green suite may be green because it pins the bug. Add fate-forcing tests: inherit · override-replace · explicit-clear · cycle-refused · missing-blocker-refused · **inherited-superseded-blocker-refused** · result-surfaces-`blocked_by`.

**Packages considered (follow-up):** `find_blocked_by_cycle` already `replace`s onto stdlib `graphlib.TopologicalSorter` (its own docstring records the verdict) — the fix REUSES it, adds no new mechanism. No third-party choice arises.
