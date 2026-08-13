# Packet 45 — served-prose derivation + sizing (design sidecar)

**Status: DESIGN + RECOMMENDATION.** Author: `fable-sidecar-45` (Fable), 2026-08-13, at
`git HEAD` cf2a7f7 on `feat/surreal-unification`. The lead (`lead-45`, Opus) and the
operator decide; nothing here is ruled. Consumes: multi-user proposal
`2026-08-01-multi-user-lore-proposal.md` §Part 2 / Verification / Forks · wave-D
architecture `2026-08-03-wave-d-architecture.md` §2 · dnd scope rulings
`2026-08-02-dnd-graph-scope-rulings.md` §4 · finding #296 · repo `CLAUDE.md` TRUST hard
definition + the instrument lesson. Cites symbols, not line numbers (they drift — see §0).

`brief-base v13 read` · `brief project v7 read`

---

## Summary block

- **state:** done (design). Four questions answered; two forks flagged IMPORTANCE-class.
- **The reframe that de-risks everything (§2):** every existing instructions/comms pin
  (`TestServerInstructions`, CL1, CL3, the every-token pin, `test_instructions_names_every_tool`)
  builds from the **DEFAULT** `_config` — i.e. the full surface under the "absent `tools:` ⇒
  all built-ins" default. So if `build_instructions(ALL)` reproduces today's string
  **byte-for-byte**, they stay GREEN with **zero test edits**. The derivation work is
  **ADDITIVE** (new subset-parametrized pins), not a rewrite of the brittle equality pins.
- **Q1 sizing:** the mechanism/prose seam is a FALSE seam (the every-token pin couples them).
  Recommend **ONE packet for the coupled core (config + `_tool` filter + universe +
  collision-guard + served-prose derivation)** ≈ 0.28–0.32, and split OUT the two genuinely
  independent items — 2B sample-gen (g) and deploy+#296-receipt (h) — as a thin 45b (or fold
  h into packet 54, where the dnd deploy already lives). That is the DIFFERENT clean sub-0.30
  seam the lead asked for.
- **Q2 shape:** `build_instructions(enabled)` assembled from per-section builders (LADDER =
  ordered tool-steps re-joined by `->`; MEMORY = per-tool clauses; COMMS/PENDING guarded by
  their tools); byte-exact on the full set (CL3 is the anchor); coherence gated by ONE
  **biconditional** token pin + a small set of **structural** pins (no gutted header, no
  dangling arrow). Descriptions: cross-references become **guarded whole sentences** (no
  byte-exact pin governs descriptions, so this is lighter).
- **Q3 trust:** Leg-1 surfaces a real defect — the **IDENTITY line over-claims** on any
  reduced surface ("code+…+graph RAG, durable memory, and fleet ledgers" names families a
  search-only instance lacks), and NO existing pin catches it (not a `lore_`-token). Leg-2:
  six forgery pins derived from deps×verbs, each naming the byte-identical false clear.
- **Q4:** no real conflict with packet 39; three confirmations + two required-edits flagged.
- **Packages considered:** none — no mechanism specified (design doc; the builder reuses
  in-tree `partition_tools_by_posture` and the `_TOOL_NAME_TOKEN` regex, §6).
- **Graded:** n/a (design, not a verdict on another artifact).
- **decisions-needed:** (1) IMPORTANCE — IDENTITY over-claim: derive-from-families vs.
  config-authorable preamble vs. leave-constant (§3, §7 Fork A). (2) IMPORTANCE — does an
  empty-but-valid enabled set BOOT or LOUD-FAIL (§3 Leg-2, §7 Fork B). (3) sizing: single
  core packet + thin 45b, or one packet with reserve (§1, lead's call).

---

## 0. Ground truth — corrected symbol anchors (brief & spec line numbers are stale)

Measured at cf2a7f7. Cite these symbols; the numbers below drift.

| symbol | file | current line | brief said | spec said |
|---|---|---|---|---|
| `_INSTRUCTIONS` (module constant) | `loremaster/loremaster/server.py` | **1641** | 1641 ✓ | 1472 ✗ |
| `instructions=_INSTRUCTIONS` interp | server.py | **9722** | — | 7875 ✗ |
| `_register_tools` | server.py | **9839** | 9839 ✓ | 7980 ✗ |
| `@mcp.tool(` sites in `_register_tools` | server.py | **15** (grep shows 16; one at :11106 is a comment) | 15 ✓ | 15 ✓ |
| `_register_extension_tools` | server.py | **11328** | — | 10302 ✗ |
| collision guard `get_tool(spec.name)` | server.py | **11368** | ~11368 ✓ | 9396 ✗ |
| inner `_tool` (extension wrapper — DO NOT clash) | server.py | **11431** | ~11431 ✓ | — |
| `build_mcp_server` | server.py | **9637** | 7822 ✗ | 7822 ✗ |
| `_ALL_BUILTIN_TOOL_NAMES` (TEST-only) | `loremaster/tests/test_mcp_server.py` | **1128** (`= _EXPECTED_TOOLS | {claim_task, tasks, comms}`) | 1128 ✓ | 1034 ✗ |
| every-token pin | test_mcp_server.py | **1216** | 1216 ✓ | 1122 ✗ |
| CL3 terminating equality pin `test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs` | `loremaster/tests/test_comms_tool.py` | **7672** (asserts `served == _declared_instructions(cap)`) | — | — |
| CL1 exactly-one-duty-paragraph | `loremaster/tests/test_comms_footer.py` | **~2706** | — | — |
| `AuthConfig(_StrictModel)` / `enabled: bool = False` | `config.py` | **337 / 353** | 337 ✓ | 353 ✓ |
| `LoreConfig` (`auth`, `extensions`) | config.py | **591** (`auth: AuthConfig \| None = None` :661; `extensions: dict[str,dict] = {}` :665) | 591 ✓ | — |

**Universe count reconciled:** `_ALL_BUILTIN_TOOL_NAMES` = `_EXPECTED_TOOLS`
(the 12 prefixed cores) ∪ `{lore_claim_task, lore_tasks, lore_comms}` = **15**. (A stale
comment at test_mcp_server.py:1309 still reads "14"; do not inherit it.)

---

## 1. Q1 — SIZING

### The seam analysis (what actually couples the work)

The lead's lean is correct, and here is the mechanism that makes it correct:
**`test_every_lore_prefixed_token_in_served_text_is_a_live_tool_name` (test_mcp_server.py:1216)
scans, in ONE assertion, the server instructions + every tool description + every per-parameter
description, and requires every `lore_`-shaped token to name a registered tool.** Therefore any
fixture that disables a tool forces *instructions AND all 15 descriptions AND all param
descriptions* to be coherent **simultaneously**. You cannot ship a reduced-set fixture that
half-satisfies it. So:

- **The mechanism/prose seam is a FALSE seam.** A "mechanism-only" 45a could only stay green by
  shipping **no reduced-set fixture at all** (default = full surface keeps every existing pin
  green) — i.e. by shipping a disable feature that is never exercised disabled. That violates the
  spec's Verification ("fixtures must include a non-trivial subset AND an empty set") and the
  Trust Doctrine (an untested reduced surface is a false clear waiting). REJECT — same conclusion
  as the lead.
- **Instructions-prose and descriptions-prose cannot split from each other** either — same
  fixture couples them.

So the coupled, atomic core is **(a) config + (b) universe-to-prod + (c) `_tool` never-register
filter + (d) collision-guard fix + (e) boot loud-fail + (f) served-prose derivation.**

### The DIFFERENT clean seam (the lead asked for one — here it is)

Two inventory items touch **none** of the shared fixture and are genuinely separable:

- **(g) 2B sample-gen** (a commented `allow`-per-method sample generated from the universe) — a
  discoverability artifact; nothing scans it.
- **(h) DEPLOY both + #296 receipt** — a container recreate + a demonstration receipt.

**Note (h) may already belong to packet 54, not 45.** Per wave-D architecture R-B, the dnd
instance is not deployed until **packet 54** ("Instance lore.yaml carries the ruled allowlist").
The lore-dnd allowlist has no instance to deploy to at packet-45 time. "Deploy both" reduces to
*redeploy the dogfood lore-lore instance with the packet-45 code* (pre-authorized, pre-production
per CLAUDE.md) + capture the #296-resolution receipt — and that receipt is a **wire test** (§3
Leg-2), demonstrable without any deploy. So (h) is mostly a test artifact + one dogfood recreate.

### Recommendation

**ONE packet for the coupled core (a–f), ≈ 0.28–0.32; split OUT (g) and (h) into a thin 45b —
or fold (h)'s deploy into packet 54.** This is the clean sub-0.30 seam: it cuts along
*config-vs-consumer/deploy*, not *mechanism-vs-prose*. The core is atomic and cannot be cut
further without shipping an unverified reduced surface.

**Why the core is not "L-cost-centre" scary (the de-risking, detailed in §2):** the byte-exact
anchor makes the instructions refactor a *bounded, verifiable* task — the builder is done exactly
when CL3 + its control are green with **zero edits to `_DECLARED_NON_COMMS_PARAGRAPHS`** AND the
new subset biconditional is green. The entire existing `TestServerInstructions` / CL1 / CL3
family stays green **untouched** (they are full-set fixtures). Grade (f) as **M–L, verifiable,
not open-ended**.

**If the operator wants a hard ≤0.25:** the only further shave is to defer the *descriptions*
cross-reference surgery — but that is coupled by the every-token fixture and cannot be deferred
without shipping over-claiming descriptions on the reduced surface with no pin to catch them
(a Trust hole). So a–f is the floor of an atomic unit; state that rather than pretend a–f splits.

---

## 2. Q2 — THE SERVED-PROSE DERIVATION (the core design)

### 2.0 The linchpin: byte-exact on the full set makes the work ADDITIVE

Both the CL3 terminating pin (`test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`,
test_comms_tool.py:7672 → `served == _declared_instructions(cap)`) and every
`TestServerInstructions` pin (substantial ≥800, names-every-tool, rollup verb, memory stance,
map→search→impact ladder, citation/freshness) read `mcp.instructions` from a server built by the
**default `_config`** — which, under the ruled default ("absent `tools:` ⇒ all built-ins"),
serves the **full** surface. The same is true of CL1 (exactly-one-duty-paragraph).

**Consequence:** if `build_instructions(ALL_BUILTINS)` reproduces today's `_INSTRUCTIONS`
byte-for-byte, **all of those pins stay green with no edits.** They become the *full-set
correctness anchor*. The derivation's new obligation is purely a **subset coherence gate** added
alongside them.

This also settles the brief's comms-block question directly:

> *the EQUALITY-pinned comms block when `lore_comms` is disabled — does equality become "equal to
> the empty contribution"?*

**No.** Do NOT reparametrize CL3/CL1 over the enabled set — that re-couples the terminating pin to
the enable/disable logic and reopens the regress CL3 exists to end. **CL3 stays a full-set
byte-exact anchor.** The disabled-comms case is covered ADDITIVELY: when `lore_comms ∉ enabled`
the comms section builder emits **nothing** (the assembler skips it), and correctness is asserted
by the subset biconditional (token `lore_comms` absent) + a structural pin (no gutted "PENDING
TRAFFIC"/comms header left behind). No hand-list of "which tool owns which paragraph" — the
tool→section binding is expressed ONCE, as the guard inside the section builder, and VERIFIED by
the emergent biconditional (observe the EFFECT, #295).

### 2.1 Shape: `build_instructions(enabled: frozenset[str]) -> str`

Refactor the `_INSTRUCTIONS` module constant into a pure function assembled from an ordered list
of **section builders**. The interpolation site (server.py:9722 `instructions=_INSTRUCTIONS`)
becomes `instructions=build_instructions(enabled_tool_names)`; `build_mcp_server` already binds
`config`, so the enabled set is in hand. Preserve the existing `_MESSAGE_BODY_MAX_CHARS`
interpolation (it lives INSIDE the comms block today).

Each section is a builder `(enabled) -> str | None` (None ⇒ omit). The ordered spine mirrors
today's document:

| section | tool-agnostic? | derivation |
|---|---|---|
| IDENTITY | **NO — over-claims (§3 Leg-1)** | see §3 / Fork A |
| LADDER | no | ordered tool-steps re-joined by `->` (§2.2) |
| CITATIONS | partly | `[SOURCE:`/`Key:` conventions ride search/read; guard the memory clause |
| FRESHNESS | no | rides search/index/diff/dead_code/impact clauses; drop disabled |
| HONEST FAILURE | no | names dead_code/impact; drop clause if disabled |
| MEMORY | no | per-tool clauses: remember/recall · findings · tasks/claim_task · comms (§2.3) |
| COMMS (ruled block) | no | **emit iff `lore_comms ∈ enabled`** |
| PENDING TRAFFIC | no | names tasks/claim_task/findings/comms; emit iff any present; adapt text |
| TOOL LOADING | **yes** | constant, always present |

**The full-set assembly must equal today's string exactly.** Author each builder's full-set
output to reproduce the current prose including em-dashes, spacing and the trailing sentences.
`test_CONTROL_the_declared_NON_comms_paragraphs_are_byte_exact` (test_comms_tool.py:7705) is your
early-warning for the classic wrap-point whitespace loss (implicit concatenation eats spaces
between literals) — heed its docstring.

### 2.2 The LADDER — the canonical fragment case (dangling-arrow generator)

Today: `LADDER: lore_map (orient) -> lore_search (locate) -> lore_get_symbol / lore_read (exact
def/span) -> lore_impact (…corroborate only on a miss) -> lore_verify (claim check) -> write. Map
defaults to PRODUCTION; reach tests via …, or lore_impact's covering-tests view.`

Model it as an **ordered list of steps**, each step a `(tools, phrase)` where `tools` may be a
list (compound step, e.g. `lore_get_symbol / lore_read`):

```
steps = [ (["lore_map"],                        "lore_map (orient)"),
          (["lore_search"],                     "lore_search (locate)"),
          (["lore_get_symbol","lore_read"],     "lore_get_symbol / lore_read (exact def/span)"),
          (["lore_impact"],                     "lore_impact (blast radius, … only on a miss)"),
          (["lore_verify"],                     "lore_verify (claim check)") ]
terminal = "write."
```

Render: keep a step iff ≥1 of its tools is enabled; for a **compound** step, drop the disabled
alternatives from its phrase (so `lore_get_symbol / lore_read` → `lore_read` when get_symbol is
off). Re-join surviving phrases with `" -> "`, append `terminal`. The trailing sentence ("Map
defaults to PRODUCTION … lore_impact's covering-tests view") is itself tool-conditional — emit it
only if `lore_map`/`lore_impact` are enabled, else drop.

**Worked lore-dnd result** (enabled: search, read; disabled: map, get_symbol, impact, verify):
`LADDER: lore_search (locate) -> lore_read (exact def/span) -> write.` — coherent, no dangling
arrow, no gutted trailing sentence. This is the payoff: `->` chains and compound steps are exactly
the dangling-reference generators, and modeling them as steps eliminates the class.

### 2.3 MEMORY — per-tool clauses, drop the header if empty

Model as clauses keyed by tool: `remember/recall` clause · `findings` clause ·
`tasks/claim_task+rollup` clause · `comms` clause. Emit only enabled clauses. **If no clause
survives, omit the "MEMORY:" header entirely** (no gutted `MEMORY:` with nothing after — a
structural pin, §2.5). For lore-dnd only `lore_findings` survives, so MEMORY collapses to a
one-clause findings line (still coherent).

### 2.4 Tool DESCRIPTIONS — guarded whole sentences (lighter than instructions)

**No byte-exact pin governs descriptions** — they are held only by `test_every_tool_has_a_
substantial_description`, `test_every_input_field_has_a_description` (positive substrings) and the
every-token pin (no dead token). So descriptions have more freedom than instructions.

Recommendation: a cross-reference to a neighbour is authored as a **separate, trailing sentence**
guarded by the neighbour's enabled-state — never woven mid-sentence. `lore_search`'s description
becomes: base ("semantic search …") + guarded("Prefer lore_get_symbol for an exact known name.")
+ guarded("Follow up with lore_read to read surrounding lines."). Under lore-dnd (get_symbol off,
read on) the first guard drops, the second stays — grammar survives because whole sentences drop.

**Scope the surgery, don't assume "all 15."** The builder greps each of the 15 descriptions for
`lore_` tokens naming a *different* tool; only those get the guarded-sentence treatment. The
subset biconditional then proves exhaustiveness — a missed cross-ref reddens it.

### 2.5 The coherence gate — ONE biconditional + a few structural pins (the NEW, additive suite)

This is what makes the shape property-derived and not a hand-list. Parametrized over fixtures
{full, a non-trivial subset, the lore-dnd exact set, empty}:

1. **THE BICONDITIONAL** (the spec's `names(instructions) == registered`, extended to the whole
   served surface): `set(_TOOL_NAME_TOKEN.findall(instructions + all descriptions + all param
   descriptions)) == enabled_builtin_names`. Forward (⊆) = no disabled tool mentioned (subsumes
   the every-token pin at every subset). Backward (⊇) = every enabled tool named. **This single
   assertion is the emergent gate; it does not care HOW the prose is assembled.**
2. **NO GUTTED HEADER** (structural): no served line matches `^[A-Z][A-Z ]+:\s*$` (a section
   label with an empty body).
3. **NO DANGLING ARROW** (structural): served text contains no `->\s*$`, no `^\s*->`, no `-> ->`;
   no line starts or ends with `->`.
4. **ANTI-VACUITY guard on the empty fixture** (the spec names this hazard;
   test_trace_telemetry.py:1181 already guards its analogue): the empty-set fixture must be
   accompanied by a **non-trivial subset** fixture, because at `enabled = ∅` the biconditional
   `∅ == ∅` is trivially true and proves nothing.

**Mutation-prove each** with expected-RED ids from `--collect-only` before the run (spec
Verification): break the LADDER join to leave a dangling arrow → pin 3 reds; misname a disabled
tool in a description → pin 1 forward reds; drop an enabled tool's clause → pin 1 backward reds.

**Contrast with the rejected alternatives (the brief's (a)/(b)/(c)):**
- *(b) filter/rewrite the monolithic constant* — a generic "strip clauses naming disabled tools"
  post-filter produces ungrammatical wreckage ("prefer , follow up with"). Rejected.
- *(c) each tool owns its whole fragment* — fights reality: sections are organized by THEME, and a
  single tool (lore_impact) contributes to LADDER *and* HONEST FAILURE. A pure per-tool home can't
  reconstruct theme-grouped prose byte-exact. Rejected as the primary shape.
- *(a) per-clause/section fragments assembled from the enabled set* — **adopted**, at
  section/step/clause granularity (not sub-word), with the biconditional as the emergent proof.

---

## 3. Q3 — THE TWO TRUST LEGS

### Leg 1 — SCOPE DIFF (and it surfaces a real, un-pinned defect)

*Question the render answers:* "what can THIS lore instance do?"
*Question the consumer thinks it asked:* "what can lore do?"

For the DERIVED tool sections the diff is closed by construction: the biconditional guarantees the
sections name exactly the enabled tools, so an agent reading lore-dnd's LADDER/MEMORY cannot act
on a tool that isn't there. A dnd instance honestly presenting a smaller toolset is **complete on
its own terms** — no "this is a reduced surface" disclaimer is needed (a disclaimer would be the
banned non-bound; the bound is the FACT of which tools are named).

**BUT the IDENTITY line is a capability CLAIM, and it over-claims.** Today:
`IDENTITY: lore is this repo's code+docs+graph RAG, durable memory, and fleet ledgers — cited,
freshness-honest.` On lore-dnd (graph tools, memory, tasks/comms all disabled) this line asserts a
**code-graph RAG**, **durable memory**, and **fleet ledgers** the instance does not have. A player's
agent reading it can be wrong in a way the response did not name (it will believe it can ask
"who calls this function" or "remember this fact"). **This is a Leg-1 FAILURE**, and crucially
**no existing pin catches it** — "code", "graph", "memory", "ledgers" are not `lore_`-prefixed
tokens, so the every-token pin and the biconditional are both blind. It is precisely the
"natural-language surface whose consistency with code no gate checks" class (CLAUDE.md, P8d).

**Options (IMPORTANCE-class — §7 Fork A):**
- *(i) leave IDENTITY constant* — Leg-1 fail. Unacceptable under the Trust Doctrine.
- *(ii) derive the capability-family clause from enabled families* — a family (code-graph {map,
  get_symbol, impact, dead_code, verify} · RAG {search, read} · memory {remember, recall} ·
  ledgers {tasks, claim_task, comms, findings}) is named iff ≥1 of its tools is enabled. Closes
  over-claim mechanically; generic (can't infer "D&D"); **byte-exact reconstruction of the exact
  phrase "code+docs+graph RAG" from families is fragile** (the same fragment-fidelity risk as
  §2.1, now on the anchor).
- *(iii) config-authorable IDENTITY preamble, default = today's exact full string* — byte-exact
  preserved trivially (CL3 green), and it locates the "what is this instance" claim with the
  **operator** (who owns the allowlist anyway). lore's obligation shrinks to "do not
  auto-generate an over-claim"; the derived sections stay tool-truthful by the biconditional.
  Cost: +1 config field.

**Recommendation: (iii)**, with the full-string default. It is the cleanest division of labor and
the only option that is both byte-exact-trivial AND domain-accurate. If the lead deems the config
field out of packet-45 scope, **(ii) is the floor** (it closes the over-claim even if generic);
packet 54 can later add (iii) as lore-dnd authors its instance identity. What is NOT acceptable is
(i).

### Leg 2 — FORGERY PINS (deps × verbs, each naming its byte-identical false clear)

Stateful dependencies of the tool-registration/config surface: **the `tools:` config**, **the
declared universe**, **the registered set** (post-`_tool`-filter), **the instructions builder**,
**the extension registry**. Crossed with {stale, empty, wrong-instance, partial}, keeping only the
states that render **byte-identical to healthy** (the false clears):

| # | dependency × verb | the false clear (identical bytes to healthy) | pin that breaks it |
|---|---|---|---|
| L2-1 | `_tool` filter × **partial** (builder applies it at 14 of 15 sites) | at the FULL set all 15 register either way → byte-identical; the un-wrapped tool simply **cannot be disabled** | **empty-set fixture asserts EXACTLY zero built-ins registered** — this makes filter coverage a *checked variable* (any bypassed site survives → count > 0). Doubles as the reach-check (CLAUDE.md INSTRUMENT 0). |
| L2-2 | registration × **wrong-instance** (filter applied POST-construction, #296) | `list_tools()` looks filtered but the WIRE still dispatches the disabled tool | **WIRE test**: disabled tool absent from `list_tools()` AND uncallable via the low-level dispatch path (this IS the #296 receipt; observe the EFFECT not the exception, #295). Never-registration is immune — the pin PROVES it. |
| L2-3 | universe × **stale** (a 16th `@mcp.tool` added, universe not updated) | full set identical; the new tool is silently un-enablable / mis-validated | the existing `test_the_registered_surface_is_exactly_the_expected_set` equality pin is the anti-drift guard — **but only if the promoted prod universe is the SAME object the equality pin consumes** (§4 required-edit; else prod/test universes drift — the #291 two-sources lesson). |
| L2-4 | collision guard × **wrong-instance** | disable built-in `lore_search`; an extension claims the name; `tools/list` shows `lore_search` present → biconditional GREEN, but it is the **wrong handler** | **collision guard checks the DECLARED UNIVERSE, not the registered set** (spec item d) → loud-fail when an extension claims a disabled built-in's reserved name. |
| L2-5 | config × **empty** (anti-vacuity) | `enabled = ∅` makes `∅ == ∅` and every subset relation trivially true | the empty fixture asserts **coherent-empty** (no gutted headers; boot behavior per Fork B) AND a **non-trivial subset** fixture runs alongside it (§2.5 pin 4). |
| L2-6 | IDENTITY/capability prose × **partial** (Leg-1) | reduced surface serves the full-lore IDENTITY; contains no `lore_`-token → every-token pin & biconditional both GREEN | the capability-family pin / config-authored-default from Fork A (§3 Leg-1). |

L2-1, L2-4, L2-6 are the dangerous ones: each renders byte-identical to a healthy surface and
sails past the token pins. They are why deps×verbs must be *derived*, not eyeballed.

---

## 4. Q4 — COMPOSITION WITH PACKET 39 (confirm + two required-edits)

Per wave-D R-B the sequence is **45 → … → 39**, so packet 39's BUILD has not happened; only its
on-branch test scaffolding exists (`test_allowlist_roster.py`, `test_mutating_set_derivation.py`,
`lorerunes/tests/test_posture.py`, `test_roster_parser.py` — PRINCIPAL/Google-identity allowlist +
posture, distinct from packet 45's TOOL allowlist). Packet 45 must not break those.

**Confirmed, no conflict:**
- **Partition input = the REGISTERED set.** Spec §Part2 resolves it: packet 45 narrows *what is
  registered*; packet 39 §7 partitions *whatever is registered* per principal. After 45,
  `all_registered_tools()` = built-ins ∩ enabled (∪ extensions) — 39's assumption "registration
  is the input" holds, the input is just smaller. ✓
- **#291 mutating-set derivation reads registered `ToolAnnotations`.** A disabled tool contributes
  no annotation and is correctly absent from BOTH the mutating and read-only partitions.
  `derive_tool_postures` → `partition_tools_by_posture` (deny-by-default in the prod helper) is
  consistent under filtering. `test_mutating_set_derivation.py` builds the DEFAULT (full) config,
  so it stays green. ✓
- **Default-deny fork = absent `tools:` ⇒ all built-ins; deny-by-default WITHIN the section.** This
  is section-granular deny (once you write `tools:`, unlisted = disabled), a DIFFERENT axis from
  39's per-principal posture deny (#291). They compose cleanly: 45 controls EXISTENCE, 39 controls
  per-principal VISIBILITY of what exists. ✓

**Two required-edits packet 45 must carry (flagged, not conflicts):**
- **RE-1 (single-source the universe):** promoting `_ALL_BUILTIN_TOOL_NAMES` to prod, the
  test-side `_ALL_BUILTIN_TOOL_NAMES` must become an **alias/import of the prod constant**, and
  `test_the_registered_surface_is_exactly_the_expected_set` must consume the prod object — else
  prod and test universes are two sources that drift (the #291 lesson; L2-3 depends on this).
  Existing consumers to rewire: `test_text_hygiene.py:207`, `test_task_read_surface.py` refs, and
  `test_mutating_set_derivation.py` (imports `test_mcp_server as suite`).
- **RE-2 (#333 baseline):** packet 39's branch has an operator-accepted RED typecheck baseline
  (#333, auth WIP). Packet 45's `scripts/typecheck.sh` receipt must be read against that KNOWN red
  set — a green-delta claim, not an absolute-green claim. State the baseline in the wave close-out.

---

## 5. Flags / open forks

**IMPORTANCE-class (change WHAT gets built — the lead should escalate):**

- **Fork A — IDENTITY over-claim (§3 Leg-1).** derive-from-families (ii) vs. config-authorable
  preamble (iii, recommended) vs. leave-constant (i, rejected). This decides whether packet 45
  adds a config field and whether a new capability-prose pin exists. It is a Trust-Doctrine
  question (a served over-claim), so it is genuinely the operator's.
- **Fork B — does an empty-but-valid enabled set BOOT or LOUD-FAIL?** The spec's Verification
  requires an empty-set fixture (needed for the L2-1 coverage pin). But a zero-tool server is
  operationally pointless. Recommendation: **empty built-in set is LEGAL at the config layer**
  (keeps the coverage pin constructible and supports a future extension-only instance), and boot
  loud-fails only if the TOTAL served surface `(built-ins ∩ enabled) ∪ extension-tools` is empty.
  This is a small design decision but it changes the boot-validation contract, so surface it.

**Non-importance flags (mechanics the contract author should carry):**

- The inner `_tool` at server.py:11431 (extension wrapper) must not clash with the packet-45
  `_tool` config-consulting indirection — name the new one distinctly (e.g. `_gated_tool`).
- Do NOT parametrize `test_instructions_is_substantial` (≥800) over reduced sets — a reduced
  surface is legitimately shorter; forcing 800 would force padding = over-claim. Keep it a
  full-set anchor. Same for the rollup/memory-stance/ladder substring pins.
- Preserve the `_MESSAGE_BODY_MAX_CHARS` interpolation inside the comms section builder.

---

## 6. Reuse pointers for the builder (DRY §6)

- **Token extraction:** reuse the `_TOOL_NAME_TOKEN = re.compile(r"\blore_[a-z_]+\b")` idiom
  already in test_mcp_server.py (TestNoDeadToolNamesInAgentFacingText) for the biconditional —
  do not re-roll a tokenizer.
- **Posture partition:** `loremaster.server.partition_tools_by_posture` (finding #291) is the
  single source for read-only/mutating; packet 45 does not touch it, only narrows its input.
- **Universe constant:** promote `_ALL_BUILTIN_TOOL_NAMES` to prod as ONE object and import it
  back into the tests (RE-1) — do not create a parallel prod list.
- **Config idiom:** mirror `AuthConfig(_StrictModel)` with `enabled: bool = False`
  (config.py:337) and `LoreConfig.auth: AuthConfig | None = None` (config.py:661) for the new
  `tools:` section — `None`/absent ⇒ all built-ins.

---

## 7. What I did NOT verify (bounds on this design)

- I did not run any test — RED/GREEN receipts are the contract author's and builder's to produce.
- Byte-exact reconstructability of the full-set prose from §2's section builders is *argued*
  (worked LADDER example) but not *demonstrated* — the builder proves it via CL3 + the control.
- I did not enumerate exactly which of the 15 descriptions cross-reference a neighbour (§2.4 says
  the builder greps them; I did not run that grep to a per-description verdict).
- The empty-set boot behavior (Fork B) is a recommendation, not a reading of existing code — no
  current code path constructs a zero-built-in server.
