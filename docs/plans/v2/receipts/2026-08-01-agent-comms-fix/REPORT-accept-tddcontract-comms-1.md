# REPORT — accept-tddcontract-comms-1

brief-base v9 read
brief project v7 read

## SUMMARY BLOCK

- state: **done**
- **VERDICT: PASS** — the 15 `mcp__lore_lore__*` tools are held, loadable and **CALLED** with
  pasted returns (`lore_index`, `lore_comms register`, `lore_comms send`, `lore_comms drain`,
  `lore_search`, `lore_map` schema). `Edit`, `Agent`, `WebSearch` all **ABSENT** — no over-grant.
- deviation: none to the mission. **One substantive correction to the fix's own teaching prose**
  (below, §5) — the mechanism is *deferred-but-scoped*, NOT *up-front*, and the comment written
  into `tdd-contract.md` by this fix asserts the opposite. Measured 2026-08-01 at `e89bfa4`.
- Packages considered: none — no mechanism specified (this run is an acceptance probe; it
  builds nothing and specifies nothing).
- decisions-needed: **one** — §5 asks whether the now-measurably-false half of the comment in
  `~/.claude/agents/tdd-contract.md` (and the matching paragraph in the lore `CLAUDE.md`) should
  be corrected. Not my writable set; flagged, not edited.
- receipt pointers: §1 inventory · §2 disk-vs-schema discriminator · §3 every pasted call return
  · §4 negative controls · §5 the prose defect · §6 capability check.

---

## VERDICT

**PASS.**

I hold the lore tools, I called four of them (five including the `lore_map` schema resolution),
and every call returned real data. `Edit` is still absent, as are `Agent` and `WebSearch`. The
fix is **LIVE in this session** — this is not the NOT-LIVE world.

**But the PASS arrives by a different mechanism than the fix's own comment describes**, and the
difference is load-bearing for the next agent. See §5. I am reporting PASS on the executed
evidence and flagging the prose separately, rather than blending them.

---

## 1. Verbatim tool inventory

### 1a. Up-front callable schema (the tools whose full `<function>` definitions were in my
prompt at spawn, before I called anything)

```
Read
Write
Bash
ToolSearch
```

That is the complete list. **No `mcp__lore_lore__*` name appears in my up-front schema.**
Also absent up-front: `Edit`, `Agent`, `WebSearch`, `Grep`, `Glob`, `TodoWrite`, `NotebookEdit`,
`WebFetch`, `Task`, `SendMessage`.

⚠ Read that line carefully before concluding NOT-LIVE — it is the exact observation that would
*look* like the pre-fix world, and it is not. Continue to §1b.

### 1b. Deferred-tool enumeration

Two `<system-reminder>` payloads bore on this, and they are different things:

**(i) At spawn**, a reminder named five MCP servers as *still connecting*, tools not yet
available:

```
claude-in-chrome
lore_lore
mezmo
odoo-code
odoo-dev
```

This is a *connection* notice about the servers, not a grant statement about me. On its own it
proves nothing about my allowlist, and I did not treat it as evidence.

**(ii) After my first `ToolSearch`**, a reminder enumerated my deferred pool explicitly. The
pool is **NOT empty**, and it contains **exactly 15 names — precisely the 15 in my definition's
allowlist, and nothing else**:

```
mcp__lore_lore__lore_claim_task
mcp__lore_lore__lore_comms
mcp__lore_lore__lore_dead_code
mcp__lore_lore__lore_diff
mcp__lore_lore__lore_findings
mcp__lore_lore__lore_get_symbol
mcp__lore_lore__lore_impact
mcp__lore_lore__lore_index
mcp__lore_lore__lore_map
mcp__lore_lore__lore_read
mcp__lore_lore__lore_recall
mcp__lore_lore__lore_remember
mcp__lore_lore__lore_search
mcp__lore_lore__lore_tasks
mcp__lore_lore__lore_verify
```

Count: 15. Set equality with the definition's allowlist: **exact**. No `claude-in-chrome`,
`mezmo`, `odoo-code` or `odoo-dev` tool appears, despite all four servers being connected in
this session — see §4b, where I probed that directly rather than inferring it from the listing.

---

## 2. The discriminator — disk definition vs. my actual schema

`Read ~/.claude/agents/tdd-contract.md` (executed; full file read).

Its `tools:` block contains, in order: `Read`, `Write`, `Bash`, `ToolSearch`, `Grep`, then a
comment block, then the **15 `mcp__lore_lore__*` entries** listed above, then `Glob`.

**So the file HAS the 15 entries.** The brief's discriminator then asks: does my schema have
them?

The honest answer is **neither a plain yes nor a plain no**, and collapsing it either way would
be the wrong result:

| | up-front schema | deferred pool | loadable | callable |
|---|---|---|---|---|
| the 15 `mcp__lore_lore__*` | **no** | **yes, all 15** | **yes** | **yes — §3** |

Judged by the up-front schema alone I would report NOT-LIVE. Judged by execution I report PASS,
because **execution is the only evidence of possession** (brief-base §4; lore `CLAUDE.md`:
*"only execution is evidence of possession"*). I executed. The tools are there.

**Which of the two worlds am I in, explicitly: the FIX-IS-LIVE world.** The definition on disk
has the entries, and so do I — they arrive deferred rather than up-front, and one `ToolSearch`
turns them into callable schemas. Not cached, not stale, not pending a session restart.

---

## 3. The calls — pasted returns

### 3a. `mcp__lore_lore__lore_index` (no arguments)

```json
{"files_indexed":3204,"files_failed":0,"files_skipped":0,"tiers_rebuilt":[],"tiers_skipped":[],
"outcomes":[],"embedding_schema":{"fingerprint":"f6e2ee34779760976274631815cb75a17ff8401f733145c2ee2f71aa19a885a8","version":2},
"schema_rebuild":{"state":"idle","done":0,"total":0,"reason":"","from_fingerprint":null,"to_fingerprint":null},
"calibration":{"state":"measured","served_constant":1.78,"committed_constant":1.78,"model":"claude-sonnet-5",
"ratio_shift":0,"last_probe_at":"2026-08-01T18:11:42.079208+00:00",
"baseline_generated_at":"2026-07-05T01:00:47.002277+00:00","note":null},
"last_sync":{"at":"2026-08-01T18:49:54.845017+00:00","age_seconds":1115.613764},
"last_sweep":{"at":"2026-08-01T19:03:03.783560+00:00","age_seconds":326.675575},
"newest_snapshot":{"at":"2026-08-01T18:53:02.153955+00:00","age_seconds":928.307026},
```

and its workspace block, which is what the brief asked me to confirm:

```json
"workspace":{"roots":[{"tier":"lore","path":"/workspace",
"git_branch":"feat/surreal-unification",
"git_ref":"e89bfa4704f8ae1996f95d0c1e1598c6ab5c088b"}]}
```

✅ `workspace.roots[0].path` == `/workspace` — confirmed.
✅ `workspace.roots[0].git_branch` == `feat/surreal-unification` — confirmed.
`git_ref` `e89bfa4` matches the branch HEAD named in my session's git status, so lore is indexing
the tree I am reporting about — not a sibling worktree.

### 3b. `mcp__lore_lore__lore_comms action=register` — **the acceptance receipt**

Arguments exactly as briefed: `agent="accept-tddcontract-comms-1"`, `session="session-c9a2fd51"`,
`role="auditor"`, `model="claude-opus-5"`.

Return, verbatim:

```
registered accept-tddcontract-comms-1 (session session-c9a2fd51, role auditor) — status active
brief 'project' v7 (published 3d ago by lead-pkt04b) — ack recorded (via register)
```
```
You are an agent working the `lore` repo. This is the standing brief; you auto-acked it by registering.

WHO LORE SERVES: agents, never humans. Every surface you are served — counts, errors, teaching prose, renders — is a contract you will learn the system from. So TRUST is the property that outranks the rest: if lore serves you something wrong, incomplete, or silently short, FILE IT (`lore_findings action=report`, needs category+area+created_by) instead of routing around it. Routing around a weakness without filing it is the one unacceptable move.

LAW, BY ADDRESS — read these, do not assume them:
- Process law: repo `CLAUDE.md` (auto-loads) — gates, TDD, orchestration, deploy, store idioms.
- Plan of record: `docs/plans/v2/INDEX.md` — packets in execution order + the append-only Log. Your packet is a row in its table.
- Store law: `docs/reference/surrealdb-31-capabilities.md` — MANDATORY before ANY store/schema/DDL change, including reads. Cite it; never re-transcribe it. Finding #107 was a 100% production outage whose answer was already in that file.
- Spawn protocol: `~/.claude/orchestration/brief-base.md` — read it FIRST and open your report with its receipt line.

COORDINATION: this tool is the durable pull channel. `register` → `drain` at your own turn boundaries → `ack` the directives your drain names. Claude Code's native SendMessage drops messages silently (upstream bug #50779, reproduced in this project), so nothing that must not be lost may travel by it alone. Proof of receipt is always an artifact you wrote — never a send that returned success.

MEMORY: durable project facts live IN lore (`lore_remember` / `lore_recall`), not in MEMORY.md, which is a thin bootstrap pointer and must not grow.

VERIFY, DON'T ASSUME: re-derive any number you inherit — from a report, from a doc, from this brief. Several numbers in this repo's own records have been wrong, including in the laws written to prevent wrong numbers. A green gate proves the recipe; only the running artifact proves the cake.
```
```
echo in your report: brief project v7 read
```

This is the exact tool the operator asked to be fixed, and it returned a real, stateful,
side-effecting result: an identity minted in the registry **and** a brief-ack edge recorded. Not
a stub, not an empty render. The `echo in your report` instruction is discharged at the top of
this file.

### 3c. `mcp__lore_lore__lore_comms action=send` — the comms path end-to-end

Arguments as briefed: `to=["lead-04b2"]`, `grade="signal"`,
`body="acceptance probe: tdd-contract can reach lore_comms"`.

```
sent #2000 [signal] → lead-04b2
```

A durable seq (`#2000`) was minted and the recipient name resolved inside my session. Send is
all-or-nothing on name resolution, so a returned seq means `lead-04b2` existed and the delivery
row was written — the *comms* path, not merely registration.

### 3d. `mcp__lore_lore__lore_search` — proving a read tool, not only ledger writes

Arguments: `query="the comms message ledger send path"`, `k=3`.

```
[SOURCE:docs/plans/v2/03a-1-comms-ledger-send.md:18]
Key: 2e8a1ce6-9052-5f9c-96c7-59f299a7a235
[S:lore:docs/plans/v2/03a-1-comms-ledger-send.md:18-20@2ce8dd]
03a (0.35) split at kickoff (sizing law ≥0.30; operator-confirmed 2026-07-23). This is the WRITE
path + the module foundations both sub-packets stand on; **03a-2** builds the CONSUME path
(drain/ack/derived-waiting) onto the `messages.py` this commits.
sim 0.61

[SOURCE:docs/plans/v2/03a-1-comms-ledger-send.md:23]
Key: 504cf0f7-c2d3-5eff-94e4-98f381b97c00
sim 0.60

+6 entries elided by budget=1100 — top elided: '8005ae36-…' — raise budget to ~3167 to see all 8
```

Cited hits with real `[SOURCE:…]` provenance and an honest elision notice. The read path works.

### 3e. `mcp__lore_lore__lore_comms action=drain` (extra — proves the third comms verb)

```
no unread messages
```

Not briefed; run because register→drain→ack is the standing brief's own protocol and the drain
verb is distinct plumbing from send. An empty inbox is a genuine no-match, not a failure.

### 3f. Failures

**None.** Zero calls errored. No `No such tool available:` string and no `exists but is not
enabled in this context` string was produced by any lore call in this run. (Both strings DID
appear conceptually in my negative controls — see §4 — but as an *absence* of resolution, which
is a different signal and I have not conflated them.)

---

## 4. Negative controls — the fix did not widen my grant

### 4a. `Edit`, `Agent`, `WebSearch` (plus `Grep`, `Glob`)

`ToolSearch query="select:Edit,Agent,WebSearch,Grep,Glob"` →

```
No matching deferred tools found
```

Combined with their absence from my up-front schema (§1a), each is **ABSENT by both routes**:

| tool | in my definition? | up-front? | deferred? | verdict |
|---|---|---|---|---|
| `Edit` | **no** | no | no | ✅ **ABSENT — the deliberate Write-but-not-Edit isolation SURVIVES the fix** |
| `Agent` | no | no | no | ✅ absent |
| `WebSearch` | no | no | no | ✅ absent |
| `Grep` | **yes** | no | no | ⚠ granted-but-undelivered — see note |
| `Glob` | **yes** | no | no | ⚠ granted-but-undelivered — see note |

**No over-grant. `Edit` is still absent; the isolation is intact.**

⚠ *Note on `Grep`/`Glob`:* both ARE in my definition's allowlist yet neither reached me. This is
consistent with the lore `CLAUDE.md` line that they are disabled session-wide, and it is a
second, independent confirmation of that file's sharpest rule — *"an allowlist entry does not
guarantee delivery… only execution is evidence of possession."* It is not caused by this fix and
is not a defect in it; I record it because it is exactly the asymmetry that makes §5 matter. It
also means my only search instruments this run were `Read` and the lore tools; I used no grep
fallback and had none available.

### 4b. Other MCP servers — the sharper over-grant control

The five-server connection notice (§1b-i) raised a real possibility the deferred listing alone
could not settle: are *all* connected servers' tools reachable, with the listing merely showing
me a filtered view? So I probed a mixed batch containing three non-allowlisted MCP names and one
allowlisted one as a **positive control**:

`ToolSearch query="select:mcp__claude-in-chrome__navigate,mcp__odoo-code__odoo_code_search,mcp__mezmo__list_log_fields,mcp__lore_lore__lore_map"`

| requested | in my allowlist? | resolved? |
|---|---|---|
| `mcp__claude-in-chrome__navigate` | no | **no** |
| `mcp__odoo-code__odoo_code_search` | no | **no** |
| `mcp__mezmo__list_log_fields` | no | **no** |
| `mcp__lore_lore__lore_map` | **yes** | **YES — full schema returned** |

The positive control is the point: the query itself was well-formed and ToolSearch was working,
because the one allowlisted name in the batch came back with a complete schema. The three
non-allowlisted names therefore returned nothing *because they are not granted*, not because the
probe was broken. Had I run only the negative half, "no results" would have been
indistinguishable from a malformed query — the same false-clear shape the repo's probe-needs-a-
control law exists to catch.

**Conclusion: my deferred pool is scoped EXACTLY to my allowlist — 15 names, no more.** The
browser-automation guidance in my system prompt notwithstanding, I hold no `claude-in-chrome`
tool; that guidance is inert boilerplate for this agent.

---

## 5. ⚠ DECISION NEEDED — the fix's own comment is now measurably half-false

This is the one thing in this report the lead should act on, and it is a prose defect of exactly
the class lore `CLAUDE.md` names: *"natural-language surfaces whose consistency with code no gate
checks."*

The comment this fix wrote into `~/.claude/agents/tdd-contract.md` (the block immediately above
the 15 entries) says:

> an explicit `tools:` allowlist gives an agent EXACTLY these names and an EMPTY deferred pool,
> so ToolSearch reaches NOTHING and an `mcp__*` wildcard grants nothing.

Measured this run, 2026-08-01 at `e89bfa4`:

| clause | measured | verdict |
|---|---|---|
| "gives an agent EXACTLY these names" | 15 of 15 lore names present; 3 non-allowlisted MCP names absent | ✅ **TRUE** (modulo `Grep`/`Glob`, granted but undelivered) |
| "an EMPTY deferred pool" | pool contained **exactly the 15 allowlisted MCP names** | ❌ **FALSE** |
| "ToolSearch reaches NOTHING" | ToolSearch was **the only way** to reach them — it is REQUIRED, not useless | ❌ **FALSE, and inverted** |
| "`mcp__*` wildcard grants nothing" | not tested this run — no wildcard in my definition | ➖ untested; I make no claim |

The same inversion appears in the lore `CLAUDE.md` paragraph beginning *"**ALLOWLIST** (an
explicit `tools:` list) — the deferred pool is **EMPTY**…"*, which additionally asserts allowlisted
MCP tools are *"proven present and callable"* — true — while framing them as arriving the way
up-front tools do. They do not.

**What is actually true, as measured:** an allowlisted MCP tool arrives **DEFERRED and SCOPED**.
It is absent from the up-front schema, present in a deferred pool restricted to the allowlist,
and becomes callable only after a `ToolSearch select:` load. The pool is empty of *everything
else*; it is not empty.

**Why this is not pedantry, and why it is the most dangerous line in the fix.** An agent that
believes its own definition's comment will reason: *"my schema has no lore tools, and the comment
says ToolSearch reaches nothing, so I have no lore tools"* — and never issue the one call that
would have handed them over. **That reproduces the exact pre-fix failure (findings #292/#294) by
BELIEF rather than by grant, on a correctly-fixed definition, with no gate anywhere able to see
it.** I was one sentence away from filing NOT-LIVE on that reasoning; what saved it was executing
instead of inspecting, which is precisely what my brief demanded and what brief-base §4 requires.

**Recommended edit (I did not make it — `~/.claude/agents/tdd-contract.md` is outside my writable
set, and per scope law this is a flag, not an edit):** replace the two false clauses with

> an explicit `tools:` allowlist gives an agent EXACTLY these names; **MCP entries arrive
> DEFERRED, not up-front — the deferred pool contains exactly the allowlisted `mcp__*` names and
> nothing else, so a `ToolSearch "select:…"` load is REQUIRED before they can be called.** An
> `mcp__*` wildcard grants nothing.

and correct the matching `CLAUDE.md` ALLOWLIST paragraph the same way. **Operator/lead call.** If
the lead wants it, I'd also suggest this measurement be filed against #292 rather than as a new
finding, since it amends that finding's conclusion rather than reporting a new gap — I did not
file it unilaterally, both because the lead is actively managing those rows and because a
duplicate would be noise on a ledger whose value is its signal.

---

## 6. Capability check (brief-base §4 — required, first thing)

- **Demanded by my brief:** enumerate tools, read my definition, call four lore tools, run
  negative controls, write a report at the repo root.
- **What I actually have:** `Read`, `Write`, `Bash`, `ToolSearch`, plus the 15 deferred lore
  tools. No `Grep`/`Glob` despite the grant; no `Edit`.
- **What I did instead:** nothing was substituted — every briefed step executed as written. No
  step required a tool I lacked. I needed no grep fallback (§4a), so there is no fallback to
  declare under brief-base §4.
- **What a lead must change:** nothing for this mission. For the *next* `tdd-contract` agent, see
  §5 — and note that a future contract-writing run will now genuinely be able to satisfy the
  project law requiring lore-first structure queries, which brief-base §4 records as having been
  *"silently unmeetable"* for this agent type for its whole prior existence.

## 7. Scope note

Per scope law I record what I noticed and did not act on: I made no edit to any file other than
this report; I mutated no git state; I touched no task-ledger row (my brief named none as mine).
The two ledger writes I performed — the `register` in §3b and the `send` in §3c — were explicitly
briefed, and the `drain` in §3e reads my own inbox only. I filed no finding (see §5 for why, and
for the recommendation that the lead do so against #292).

## 8. Bounds on this report

Stated so it does not over-claim about itself:

- Measured **once**, in **one session**, on **one model**, for **one agent definition**
  (`tdd-contract`) against **one server slug** (`lore_lore`), on 2026-08-01 at `e89bfa4`. I did
  not test whether the deferred-not-up-front behaviour generalises to other agent definitions,
  other models, or another project's slug — and the definition's own ⚠ BOUND note about
  cross-project slugs is untested by me.
- I did not test the `mcp__*` wildcard claim; my definition contains no wildcard.
- "`Edit` is absent" is proven by two routes (up-front schema, deferred probe). It is not proven
  by an attempted `Edit` call, because I cannot invoke a tool whose schema I cannot load — the
  absence of a loadable schema *is* the evidence, and I have not dressed it up as more.
