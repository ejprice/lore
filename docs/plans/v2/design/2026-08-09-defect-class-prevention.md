# Defect-class prevention — the "reach is not a checked variable" class

**Design doc.** Session `2026-08-09-fix-344-345`. Author: `fable-designer` (Fable design
sidecar, operator-delegated fork rulings for this session). Status: **COMPLETE — all eight
findings speced against HEAD `74694dc`; F1–F5 ruled; three operator escalations named (§5).**

Graded against HEAD `74694dc` (`feat/surreal-unification`); index fresh (last sweep
2026-08-09T13:11Z). Findings read in full via `lore_findings action=get`: #344 #345 #337
#291 #289 #290 #279 #295.

> **OPERATOR RULINGS — 2026-08-09 (recorded post-design by `lead-defect-class`).** The three
> named escalations (§5) and one priority steer are RESOLVED; this note is AUTHORITATIVE over any
> "operator to decide / recommend" phrasing below.
> - **Acceptance frame (outranks the security framing throughout this doc).** The goal is NOT
>   security (small user base). Priority order (operator, 2026-08-09): **(1) DRY / ONE
>   IMPLEMENTATION** — several findings are CAUSED by duplication (#279 derivation twice, #291
>   hand-list beside prod annotations, #344 gate set re-listed per brief, F4 tree-parser
>   hand-rolled ~14×), so each fix is genuine CONSOLIDATION proven by MUTATION (change the shared
>   thing → every caller reddens), never a fresh copy or a route-without-share; **(2) TRUST &
>   HONESTY TO AGENTS** (Consumer Law — no false clears); **(3) do NOT make gaps WIDER**; **(4)
>   do not repeat past mistakes.** Judge every instrument by whether it could produce a FALSE
>   CLEAR, widen a gap, or leave two sources of truth for one policy.
> - **F3 / #337:** KEEP LEDGER-ONLY (no pin cycle); tightened re-open trigger; INSTRUMENT 0's
>   REACH ATTACK is its standing guard. Finding #337 acknowledged.
> - **F5 / #279:** the ONE derivation lives as a PRODUCTION `loremaster.store` helper.
> - **INSTRUMENT B:** RETIRE the old `_RENDER_DRIVERS` hand-net — but ONLY behind a
>   removed-behavior SUPERSET proof (the AST-derived inventory ⊇ every slot the old net covered),
>   so retirement can never widen a gap.
> - **#295 STRUCTURAL leg → packet 39** (folded into its INDEX row, commit `641f758`); only the
>   auth-independent "observe-the-EFFECT" invariant is built this session.
> - INSTRUMENT 0's GLOBAL `contract-adversary.md` P1c reach-attack: operator-confirmed **KEEP**.

---

## 1. THE CLASS — stated once, in one sentence

> **A guard, gate, or probe certifies only the sites it actually EXECUTES — and its REACH
> is written as a hidden constant instead of a checked variable, so the sites it does not
> reach are exempt silently and forever.**

Every one of the eight findings is one instance. The reach hides in a different disguise
each time, and that is exactly why re-diagnosing the class for months has not stopped it —
the diagnosis is not an instrument (CLAUDE.md, PKT-28 C1). The disguises:

| # | finding | how the reach hid | the site that escaped |
|---|---------|-------------------|-----------------------|
| #345 | render-containment sweep | **hardcoded driver param** (`task_id=None`) left a free-text slot unexercised | `(task {task_id})` — a plain-ASCII forgery through `sanitise_line` |
| #337 | comms promise-scanner | **name-prefix discovery** (`_render_comms_`/`_comms_`) — and the coverage-check keyed on the SAME prefix | `_render_story_message`, off-prefix, invisible to guard AND self-audit |
| #344 | "the gates" | **hand-list per spawn-brief**, omittable | `pending_contract_gate.py --currency` omitted → 8 RED_ORPHANED pins unseen 2 cycles |
| #291 | `_MUTATING_TOOLS` | **hand-list beside the production truth** (`ToolAnnotations`), drifted | `lore_claim_task`, `lore_tasks` — writable, absent from the test's mutating set |
| #279 | store-seam set | **derivation written twice**, free to disagree | a 4th public coroutine would be a "door" to one derivation and not the other |
| #290 | `wrong_builds.py` | **no anti-vacuity on the COMPARISON's baseline** | a baseline that collected 0 tests → every build "survived" (21 phantom survivors) |
| #295 | refusal pins | **observed a proxy** (raised exception / rendered marker), not the effect | a guard placed AFTER the mutating body — tool ran, pin green |
| #289 | anchored-pattern instance | **malformed-input matrix missing a case** (trailing newline) for a field it interpolates | `finding == "#188\n"` — a line-injection forgery through `.match` |

**The one fix principle** — already this repo's law, here turned from a remembered property
into a build-time instrument:

> **Derive the site-set from a PROPERTY of production truth (AST shape, registered
> annotations, function identity, the canonical manifest) — never a name, prefix, or
> hand-list — and make COVERAGE A CHECKED VARIABLE: assert `observed-set ==
> derived-set`, fail closed on empty, allowlist the SAFE with evidence-backed reasons and
> a re-open trigger.**

Two findings carry a second half the coverage principle alone does not reach:
- **#295** — observe the **EFFECT**, not the proxy (an invocation counter / unchanged store
  / absent row), because a proxy is identical whether the guard ran before or after.
- **#290** — anti-vacuity on the **comparison's reference value** is a distinct guard from
  anti-vacuity on the things compared, and it is the one that gets skipped.

**The askable-question form** (CLAUDE.md "write laws as QUESTIONS, not PROPERTIES"), the
one line an author runs against their own instrument before shipping it:

> **"What is the set of sites this guard is supposed to cover, where is that set DERIVED,
> and does a test FAIL when the derived set grows but the observed set does not?"**
> — and its degraded-path twin — **"If this guard ran AFTER the thing it guards / against a
> baseline that measured nothing, would it still read as success?"**

---

## 2. The exemplars we are imitating (verified at HEAD)

Three instruments in-tree already embody the fix principle. Every new instrument below is
built to their shape, not invented fresh.

- **`scripts/registration_sites.py`** — the north star. DERIVES the site-set from a property
  (*"a registration site is a place where ≥3 member names co-occur"*), is RUN not read, has
  an explicit **anti-vacuity** guard (zero sites ⇒ "this tool is broken, not the tree"), and
  documents its own bounds. It is a *worklist*, deliberately ungated (its exit 1 on a healthy
  tree would make a permanent-red gate that gets switched off).

- **`loremaster/tests/test_anchored_pattern_seam.py`** (finding #210) — the AST-∀-scan model,
  and the direct template for #345-part2 and #289's home. It carries every part a scan of
  this class needs, and each part is a named, separable role:
  - **derived roots** — `_scanned_roots()` reads `[tool.uv.workspace] members` (via
    `_logging_fixtures.workspace_roots`), never a hand tuple (its own docstring records the
    day the hand tuple went stale when `lorerunes` was minted — lore #251);
  - **coverage as a checked variable** — `TestScanCoverage.test_the_scan_reaches_every_production_tree`
    asserts `scanned == declared|{"scripts"}`, with the oracle (declared members) read
    **independently** of the subject (what the walk parsed), so it is not `derived == derived`;
  - **resolver positive control** — `test_the_scan_resolves_the_known_anchored_constants`
    (the scan can still SEE the constants it keys on);
  - **allowlist-the-safe** — `_ALLOWED_ANCHORED_MATCH`, keyed by name, each entry an
    evidence-backed reason (a PROBE with a positive control, not "it looked fine"), plus a
    **dead-entry** pin (`test_the_allowlist_carries_no_dead_entries`);
  - **positive + negative controls** — `TestScannerFiresOnAKnownViolation` (it catches a
    planted defect) and `TestScannerDoesNotRefuseHonestCode` (it does not refuse honest code —
    the false-positive tax that gets gates switched off).

- **`scripts/pending_contract_gate.py`** (findings #306/#312) — the gate runner and the
  currency verdict. Relevant mechanics, verified at HEAD (F1 rests on these):
  - the leg set is **DERIVED from `scripts/gates.yaml`** — *there is no `ALL_LEGS` tuple*, and
    its absence is the mechanism; a gate reaches the runner in the same edit that adds it to
    the manifest, or the runner refuses to parse (`GateSpec._reader_must_be_implemented`);
  - `--currency` renders per-gate **GREEN / RED_ADJUDICATED(owner,trigger) / RED_ORPHANED /
    NOT_RUN**; a gate the manifest claims but the run omits is **`VERDICT_NOT_RUN` → FAIL**
    (`_render_currency`), so currency is all-or-nothing by construction — you cannot pass it
    on a subset;
  - `--legs` runs a subset but "**NEVER yields a deploy receipt**"; the full run is the deploy
    receipt (`is_deploy_receipt = ok and is_full`);
  - anti-vacuity is enforced in five places per reader (zero-collected pytest, missing junit
    `file` attr, `No Python files found` for ruff, mypy `Found N` cross-check, per-leg
    accounting) — coverage is already a checked variable here (`LivenessCoverage`).

**The whole design below is: give the other six findings the shape these three already have.**

---

## 3. Instruments — grouping and per-instrument specs

*(Instrument specs are filled from the investigation returns; the substrate rulings and the
gate-bundle spec are settled and written here now.)*

### Grouping decision (hypothesis tested against the code, not accepted)

**There is NO single meta-SCANNER for this class, and building one would be the seventh defeated
instrument.** The reach hides in structurally unrelated surfaces — AST render slots, tool
annotations, a gate manifest, store-seam identity, a baseline integer, a test's effect-observation.
A scanner keyed on any ONE of those shapes cannot see the others; "find every hand-list in the
repo" is not an AST-expressible property. So the smallest un-defeatable set is: **per-surface
invariants (below) that fix the eight instances, + ONE process instrument (INSTRUMENT 0) that
installs the class's askable-question into the pipeline so instance #9 is caught at CONTRACT time,
before a builder.** That process instrument is the only thing that generalises; everything else is
one surface each.

Two real SHARED SUBSTRATES exist among the per-surface instruments; the rest are standalone.

- **Substrate A — the AST-∀-scan test-support helpers** (F4). Hosts #345-part2; #289's instance
  already lives under it (`test_anchored_pattern_seam`). (#337, on investigation, does NOT share
  it cleanly — see F3.)
- **Substrate B — the "coverage-as-a-checked-variable" PATTERN** (a shape, not shared code):
  applied in #345, #291, and already the reference impl in `test_link5_render_containment`.
- **Standalone**: #344 (gate bundle, F1), #291 (derive-from-annotations), #295 (observe-the-effect
  + sweep; structural answer routed to pkt 39), #290 (anti-vacuity-on-baseline), #279 (derive-once).

### INSTRUMENT 0 — the contract-adversary "REACH ATTACK" (the meta-instrument) — SETTLED

**This is the one instrument that makes the CLASS, not just the eight instances, harder to ship.**
The class recurs because a builder/contract author writes a guard and never asks what it fails to
run over — and no pass in the pipeline asks for them. CLAUDE.md's own lesson: a diagnosis is not an
instrument, and the thing that installs a rule is turning it into a QUESTION someone is forced to
ask. The `contract-adversary` (Opus, `~/.claude/agents/contract-adversary.md`) is the pipeline stage
whose whole job is "what would this contract wave through?" — it already runs a quantifier attack and
a fixture-discrimination attack. Add a standing **REACH ATTACK**:

> For every guard/gate/scan/probe/sweep the contract introduces or relies on, the adversary must
> answer, per instrument: **(1)** what is the SET of sites it is supposed to cover? **(2)** is that
> set DERIVED from a property of production truth, or is it a name/prefix/hand-list? **(3)** is there
> a pin that goes RED when the derived set GROWS but the observed set does not (coverage as a checked
> variable)? **(4)** does it observe the EFFECT or a PROXY (would it pass if the guard ran after the
> thing it guards / against a baseline that measured nothing)? Any instrument that is a hand-list, or
> whose coverage is not a checked variable, or that observes a proxy, is a MISSING PIN the contract
> author must satisfy — reported exactly like the existing quantifier-attack misses.

**Property enforced:** a new guard whose reach is a hidden constant cannot pass the adversary — the
class is caught at contract time, on the artifact where it is cheapest to fix.

**Why this and not an AST gate:** "a hand-list used as a site-set" is not a structural property (a
hand-list and a derived set are both just Python). It IS answerable by a reasoning pass with a
checklist, which is exactly what the adversary is. This is the honest boundary: the per-surface
instances get mechanical pins; the CLASS gets a mandatory question. (Bound: a reasoning pass can miss;
that is why the eight instances ALSO get their own mechanical invariants — belt and braces, per the
operator's packet-01 ruling that a design problem gets both the fix and the routing rule.)

**Askable question (the author's own copy, before the adversary sees it):** the section-1 question.
Also add it as a QUESTION-form law line to CLAUDE.md's instrument-lesson section.

### INSTRUMENT G — the non-omittable gate bundle (#344) — SETTLED

**Property enforced:** a stage cannot report "gates green" over a hidden subset; "the gates"
is one command derived from `scripts/gates.yaml`, not a list a brief re-types.

**Site-set derivation:** already done — `pending_contract_gate.py` derives its leg set from
`gates.yaml` and `--currency` fails NOT_RUN on any omitted manifested gate. The gap #344
names is not in that machinery; it is that **spawn briefs hand-list "the gates"** and a stage
ran typecheck + ruff + 4 contract suites but **omitted `--currency`**. The fix is an
ENTRYPOINT + a briefing rule, not new partition logic.

**Design (thin wrapper, ONE IMPLEMENTATION — names no gates itself):**
- Add `scripts/wave_gate.py` (uv-run, no shebang, like `pending_contract_gate.py`) — a thin
  posture wrapper that invokes `pending_contract_gate.py --currency` (inheriting the derived
  gate set — it re-lists nothing) and renders a **mode header** + the **exact pytest scope it
  executed**. It is what every spawn brief POINTS at; briefs stop listing gates.
- **Two REQUIRED, RECORDED modes** (F1): `--wave` and `--checkpoint`. Mode is a required
  argument with **no default**, and the chosen mode is printed in the receipt header — so it
  is a recorded fact, not a hideable free choice.
- Register the entrypoint's existence as the enforcement point (no CI, #285): the briefing
  rule is standing law (see build plan), and a repo pin asserts every spawn-brief template /
  `brief-base` / `lead-base` that mentions gates points at the bundle rather than enumerating
  `typecheck`/`ruff`/`pytest`/`currency` inline (allowlist-the-safe over brief prose).

**F1 RULING — how ONE bundle stays honest about pytest scope while CLAUDE.md scopes pytest to
changed suites between waves:**

The tension is real and it resolves cleanly because **only pytest is scopable** — `typecheck`
(mypy over all roots) and `ruff` (`.`) are whole-tree always, and currency over those two is
cheap and full every run. The #306/#312/#344 defects lived in the *typecheck/currency*
surface, not the pytest-scope surface. So:

1. **Both modes always run, in full, and currency-check: `typecheck` + `ruff`.** These are the
   non-omittable core; they are exactly what #344 dropped. There is no "scoped typecheck".
2. **`--checkpoint`** runs the **full** pytest gate; currency clears `pytest` normally
   (GREEN/RED_ADJUDICATED/RED_ORPHANED). This is the phase-checkpoint / pre-deploy posture.
3. **`--wave`** runs pytest **scoped** (the wrapper passes a selector through to the pytest
   gate's argv — the machinery already forwards `pytest_args`). The receipt renders
   `pytest : SCOPED(<selector>) — NOT a currency clear; full run owed at the phase checkpoint`.
   Crucially the wrapper marks the pytest currency line **SCOPED**, never GREEN, so a wave
   receipt **can never read "pytest green" from a subset** — the honest bound is in the render
   (Leg-1 scope-diff: the question answered ≠ the question a full run answers, and the diff is
   printed). typecheck + ruff currency still PASS or FAIL for real.
4. The **selector is echoed verbatim** (the argv actually executed), so "green on a hidden
   subset" is unrepresentable: the subset is in the receipt.

This keeps the non-omittable core (typecheck+ruff+currency) truly non-omittable while honoring
the scoped-pytest-between-waves rule, and it does it without touching `pending_contract_gate.py`'s
audited internals (ONE IMPLEMENTATION: the wrapper re-lists no gates; it inherits the manifest).

**Bound / re-open trigger:** a wave-mode run does not clear pytest currency; a diff-introduced
pin in a suite the selector missed is caught only at the checkpoint. Re-open trigger: *the day
this repo gains CI (#285), `wave_gate.py --checkpoint` becomes CI's first job and the wave/checkpoint
split collapses into "every push runs full."* This is the same bound `gates.yaml`'s currency
comment already carries.

**Mutation proof:** delete a gate from `gates.yaml` → the bundle's currency drops a line and any
brief-pin asserting "the bundle covers {manifest ids}" reddens; flip the wrapper to swallow the
SCOPED marker → a wave receipt that reads "pytest GREEN" on a `-k` subset fails the wrapper's own
render pin.

**Positive/negative control:** POSITIVE — a run with a real RED_ORPHANED pin exits non-zero in
both modes (currency catches it). NEGATIVE — a clean tree in `--wave` with a scoped selector exits
0 AND prints `pytest: SCOPED(...)`, i.e. passing without ever claiming a pytest currency clear.

**Askable question:** *"Does my close-out point at the one bundle command, or did I type a list
of gates?"* — and *"does my receipt say which pytest scope ran?"*

### INSTRUMENT A-SUB — the shared AST-∀-scan substrate (F4) — SETTLED

**F4 RULING: ONE shared substrate, as a LIBRARY of helpers — NOT one mega-scan-file. Per-scan
files stay separate (each owns its property, allowlist, and controls); the REACH machinery is
shared and proven by mutation.**

Evidence (HEAD `74694dc`): `workspace_roots` already lives shared in
`loremaster/tests/_logging_fixtures.py` (with `include_scripts`/`include_skills` toggles) — so
**root-derivation is already ONE implementation**. What is NOT shared and is re-hand-rolled per
file: the **tree-parser** (`rglob("*.py")` + `ast.parse` — duplicated in ≥14 test files, verbatim
in `test_anchored_pattern_seam._parse_production_trees`) and the **coverage-assertion**
(`scanned == declared`, re-written in each ∀ scan). `test_backoff_seam.py`, `test_secret_typing.py`,
`test_secret_leak_vectors.py` all import `workspace_roots` and then separately re-derive
`_SCANNED_ROOTS`/parse/coverage. This is the ONE-IMPLEMENTATION defect one level up: if the parse
or the coverage rule needs to change, it must be found in N files.

**Design (SCOPE REFINED by the DRY review — §7; two primitives, deliberately different grains):**
add to `_logging_fixtures.py` (the existing shared test-support home — test scaffolding, so it does
NOT belong in `lorerunes`, which is stdlib-only PRODUCTION shared code):
- `parse_production_trees(*, include_scripts=True, include_skills=False, include_tests=False)` — the
  ONE tree-parser, roots from `workspace_roots`/`production_sources` (which already yield `(label,
  path)`), returning LABELED/grouped trees so per-member callers need not re-group. **The clean
  consolidation: 5 real adopters** (`test_anchored_pattern_seam`, `test_secret_typing` —
  also retiring its duplicate `_SCANNED_MEMBERS` list, `test_comms_footer` — needs `include_tests`,
  `test_backoff_seam` + `test_secret_leak_vectors` — already on `production_sources`). Ship firmly.
- `assert_covers(observed, derived, *, subject)` — the coverage assertion, oracle read independently
  from `pyproject.toml`, **SCOPED to the tree-scan reach tier ONLY (2 adopters:
  `test_anchored_pattern_seam::TestScanCoverage` + `test_secret_typing`'s member-reach pins).** Do NOT
  route the runtime-site / action / probe / render-candidate reach-checks through it — those keep
  their bespoke derivations and load-bearing messages; a "one helper for all reach law" is
  over-consolidation (§7 Q2). A second generic helper for that tier is a POSSIBLE follow-up only on
  operator call.

**Prove sharing by MUTATION** (F4's own requirement): change the shared parser (drop `scripts` / make
it return `{}`) → all 5 `parse_production_trees` adopters redden in ONE run; a scan that stays green
is a private copy wearing the shared name. **PLUS the anti-duplication structural pin** (the meta-DRY
guard, §7): no test file hand-rolls a whole-tree `rglob("*.py")+ast.parse` or a bare member-reach
`assert observed==declared` outside the shared helpers, except the NON-ADOPTER ALLOWLIST (§7:
single-package scanners, `.md`/retired-name sweeps, test-tree scans, the git-tracked NUL scan, the
indexer corpus) each with its reason — so "migrated" is a checked variable, not the files someone
remembered.

**⚠ Do NOT widen the single-package scanners to whole-tree** (`test_render_seam_pins`,
`test_task_read_surface`, `test_surreal_store`, `test_text_hygiene`, `test_retry_seam`, and
`test_link5`): several generalise over a `root` arg but are loremaster-scoped TODAY, and widening is a
SCOPE CHANGE that could widen a gap (priority #3), not consolidation. They are on the anti-dup
allowlist; any widening candidate is surfaced as a separate scope decision, never silently folded in.

**#289's "for free" corollary (F4-adjacent):** #289's instance is already fixed and already lives
under `test_anchored_pattern_seam` (it caught #289 because `scripts/` is in the scanned roots).
The generalisation owed is NOT a new scan — it is (a) keep bringing trees under the substrate
(the substrate's `include_scripts` default already does this), and (b) the malformed-input matrix
rule for contracts, which is a **checklist clause** in the tdd/contract-adversary flow, not a
repo pin (a contract's field-fate matrix cannot be AST-derived generically). See INSTRUMENT E.

### INSTRUMENT B — render free-text slot inventory + `sanitise_line` misuse scan (#345)

**Investigation reframe (a050 agent, HEAD):** #345 is NOT greenfield. `test_link5_render_containment.py`
ALREADY carries the repo's reference coverage-as-checked-variable apparatus — three coupled checked
variables:
- **P-U** (`_candidate_render_sites` / `TestEveryRenderCandidateIsDrivenOrOut`): the candidate
  universe, derived NAME-BLIND by the interpolation property (`_method_interpolates_a_nonconstant`
  — any `AppContext` method interpolating a non-constant f-string/`.format`, OR calling a
  control-char guard in `_INTERP_NONCONTAIN = {sanitise_line, safe_str, _sanitise_line}`);
- **P-F** (`_manifest` / `TestTheFieldManifestCannotSilentlyMissAField`): per model, a
  **hand-classified `(DOOR, SAFE)` split**; `_forge` tokenises every DOOR field; the completeness
  guard asserts `DOOR ∪ SAFE == every str-ish field`;
- **P-S** (`TestEveryDrivenRenderBranchIsExercised`): every driven render's body line + branch arc
  observed executed under `coverage.Coverage(branch=True)`.

**The EXACT hole #345 fell through — and it is THE CLASS, inside the instrument:** P-U caught the
drain-row method and P-S ran its branches, but **P-F's DOOR/SAFE split is a hand-list, and
`task_id` was mis-parked in SAFE**. `_forge` therefore never tokenised it; the `(task {task_id})`
slot was only ever rendered with the `None` default. P-F's completeness guard checks that every
field IS classified — never that a SAFE classification is CORRECT. *A field wrongly in SAFE passes
every gate and is never driven with a forgery.* The site-set (which fields are doors) is a hand-list
whose correctness is unchecked — reach hiding as classification.

**Property enforced:** every render slot that actually interpolates a caller-controlled or stored
value into a served line is DRIVEN with a forgery token — and a slot mis-classified SAFE surfaces
as an UN-DRIVEN derived slot → RED (today's *accidental* self-heal, Q3, promoted to the DESIGNED
mechanism).

**Site-set derivation (part 1):** derive the driven-slot INVENTORY from the render AST — for every
P-U render method, the set of model-attribute/param identifiers interpolated into a served line
outside a `_SEAM_VERBS` call. Assert each derived slot was DRIVEN with a real forgery token. The
deriver MUST cover the two shapes a naive f-string scan misses (agent-flagged, load-bearing):
1. **`render_line(**values)` keyword slots** and **`sanitise_line(field)`/`safe_str(field)`
   arguments** — the comms family renders `role`/`last_note`/`thread` with NO `{...}` at all (that
   is why the render half went to a RUNTIME `_leaks` byte-check); a pure FormattedValue scan is
   blind to them.
2. Reuse the existing predicates — `_raw_render_interpolations(fn)` (line ~3237, already computes
   `(lineno, identifier)` for f-string slots outside seam verbs), `_appcontext_methods()`,
   `_expr_door` — do NOT hand-roll a fourth interpolation classifier (ONE IMPLEMENTATION).

**Bound that must be stated in the instrument (MEASURED, not argued — contract-04b5-2 §R1b):**
door-vs-safe PROVENANCE is **not name-blind derivable**. The win is NOT eliminating judgement; it
is making the slot INVENTORY code-derived so a wrong judgement can't hide — it surfaces as an
un-driven slot. The instrument's docstring states this bound explicitly, with the receipt.

**Part 2 — the `sanitise_line(<caller/stored free text>)`-in-render AST scan:** generalise the
EXISTING error-half scan `TestNoServedDomainErrorLeavesACallerParamUncontained` (line ~1219) from
error constructions to render (non-error) contexts. It already classifies `sanitise_line(task_id)`
as a DOOR via `_expr_door` and treats a `_SEAM_VERBS` call as contained. Allowlist-the-safe reusing
the EXISTING `_CHARSET_GATED` set + the P-F SAFE reasons (charset-gated identities, closed-vocab
enums, system-minted opaque ids) — do NOT invent a new allowlist.

**Allowlist / false-positive handling (evidence-backed, re-open trigger):** the `diff.py` /
`search.py` `sanitise_line` sites (indexed-diff + memory/search content — 31 prod refs total on
`sanitise_line`; `render_attributed` has 71) are the **code_rag / B-5 indexed-content bound**
already owned by the #138 / packet-39 threat-model review (`_RENDER_OUT["map"]="code_rag"`). The
part-2 allowlist must either cover those with their existing stated reason or DELIBERATELY re-pin
them — never silently flag (that is the false-positive tax that switches a gate off).

**Mutation proof:** move any DOOR field to SAFE in `_manifest` → the derived-inventory pin reddens
(the slot is interpolated but un-driven). Positive control: plant a `sanitise_line(some_caller_param)`
in a render method → part-2 scan flags it. Negative control: a charset-gated identity through
`sanitise_line` stays clean.

**Askable question:** *"For every value a render interpolates into a served line — is it DRIVEN
with a forgery, and is that inventory DERIVED from the render code or from a list I maintain?"*

**Flag to operator (ONE-IMPLEMENTATION cleanup the file itself raises, line ~606):** the OLD
`_RENDER_DRIVERS` net (with the literal `task_id=None` hardcodes at lines ~488/541/560 — the exact
#345 artifact) is STILL running as a retained subset, superseded by the derived net. Retiring it is
a cleanup the file flags itself; surface it — it is the literal hardcode #345 names.

### INSTRUMENT E — trailing-newline malformed-input matrix (#289) — instance FIXED, invariant OWED

**HEAD state (a059 agent, verified via `git show`):** the instance IS fixed —
`scripts/gated_ground.py::Exemption.__post_init__` uses `_FINDING_NUMBER.fullmatch` (not `.match`),
with the #210 comment. The CLASS instance already lives under `test_anchored_pattern_seam` (that
scan caught #289 because `scripts/` is a scanned root — F4's "for free" corollary).

**The invariant that is still owed (measured gap):** `test_gated_ground.py`'s `Exemption`
malformed-row matrix parametrizes `""`, `"188"`, `"see the ledger"` — **none carries a trailing
`\n`**, so `.match` and `.fullmatch` behave identically on all three. **A wrong build reverting
`.fullmatch`→`.match` passes the entire contract today** — a fix without a discriminating pin. No
`wrong_builds.py` entry attacks `_FINDING_NUMBER` either.

**Property enforced:** a contract's malformed-input matrix carries a TRAILING-NEWLINE case for
every field it interpolates into served text (not only paths — the path case was pinned because a
path was known-hostile; a finding number was assumed safe because it "looks like" a closed charset).

**Design — two parts, honest about what is pinnable:**
1. **Instance pin (buildable now):** add `finding="#188\n"` (must raise) to the `Exemption` matrix,
   and add a `wrong_builds.py` entry reverting `.fullmatch`→`.match` (must be KILLED). This makes
   the #289 fix mutation-proven.
2. **Class rule (checklist, NOT a repo pin — stated honestly):** "a contract's field-fate matrix
   carries a trailing-newline case per interpolated field" cannot be AST-derived generically (a
   contract's fixture matrix is not a structural surface). It rides the **contract-adversary's
   malformed-input attack** + a **tdd-contract checklist clause**. This is the honest boundary: the
   repo-wide `.match`/`.fullmatch` structural class IS pinned (`test_anchored_pattern_seam`); the
   per-field-fixture-fate rule is a reasoning instrument, so it is filed as a checklist question,
   not dressed up as an invariant it cannot be.

**Askable question:** *"For each field this validator/contract interpolates into served text, is
there a fixture whose ONLY difference from a valid value is a trailing newline?"*

### INSTRUMENT H — anti-vacuity on a comparison's baseline (#290) — instance FIXED, invariant OWED

**HEAD state (a059 agent, `git show`):** the instance IS fixed — `scripts/wrong_builds.py::main()`
raises `SystemExit` on a zero-collected baseline, naming the cause AND the child interpreter
(`sys.executable`); stderr is carried into the tail; HOW TO RUN corrected.

**Gap:** the guard is INLINE in `main()`, not a reusable helper, and **nothing exercises the
zero-baseline `SystemExit` path** (`test_wrong_builds.py` tests anchor-landing only). The general
guard — *anti-vacuity on a comparison's REFERENCE value is a distinct guard from anti-vacuity on the
things compared, and it is the one that gets skipped* — is not shared anywhere.

**Property enforced:** any harness grading N runs against a baseline asserts the baseline MEASURED
something before any of the N mean anything.

**Design:** extract a tiny shared predicate — the smallest honest surface. Candidate home:
`scripts/` is not a package, and this is a build-harness concern (`wrong_builds.py`,
`gated_ground.py`, `pending_contract_gate.py` are all `scripts/`), so a `scripts/_harness_guards.py`
helper `refuse_vacuous_baseline(measured_count, *, cause_hint, interpreter) -> None` (raises with
the diagnostic) is the ONE implementation both `wrong_builds.py` and any future N-vs-baseline
harness call. Add a covering pin (`test_wrong_builds.py`) that DRIVES the zero-baseline path and
asserts the `SystemExit` (positive control), plus a non-vacuous baseline that proceeds (negative
control). NOTE `pending_contract_gate.py` already has its own reader-level anti-vacuity — do NOT
disturb it; this helper is for the *comparison-baseline* case specifically.

**Packages considered:** none new — this is a two-line stdlib predicate; the point is ONE
implementation + a covering test, not a library.

**Mutation proof:** delete the `refuse_vacuous_baseline` call in `wrong_builds.main()` → the new
covering pin reddens.

**Askable question:** *"Does anything assert my baseline/reference measured something, or would a
baseline of zero read as 'everything passed'?"*

### INSTRUMENT F — one store-seam derivation (#279) — F5

**Investigation (a059 agent, HEAD):** the duplication is real and current — the two files share NO
code today. Precise diff: BOTH derive *"coroutine function defined in `loremaster.store._txn`"*; the
DOOR subset (`forgery_door_sweep.store_seams`) adds `public` + a `statement`-parameter filter that
the WIDE set (`test_blocks_edge._degrade_every_STORE_seam`) omits. The single element the filter
removes is `bootstrap_session` (door subset excludes it; wide set keeps it as a degradable seam).
`test_blocks_edge.py` is 9131 lines / 155 `test_` functions — a large closed contract file (packet
04b-1, 8256/0).

**Property enforced:** ONE derivation answers *"what is the store-seam set of a module?"* — a 4th
public coroutine in `_txn` becomes a door (or not) in exactly one place, and both callers move
together.

**Design (the finding's own exact edit, refined by the agent):**
- a shared `_txn_coroutines()` core over `vars(loremaster.store._txn)` = the SUPERSET;
- door subset = core + public + `statement`-param filter (today's `store_seams()` output);
- `seam_bindings(*, package, seams=…)` gains a `seams=` arg (already identity-based + package-scoped)
  so bindings can be built from EITHER set (default = door subset, back-compat);
- `_degrade_every_STORE_seam` calls `seam_bindings(package="loremaster", seams=<superset>)`, filters
  to `loremaster.tasks`, monkeypatches each; KEEP `assert "run_query" in patched`, ADD
  `assert "bootstrap_session" in patched`.

**F5 RULING: IN-SCOPE this session, as its OWN sequenced TDD cycle** (contract-adversary + cold
audit), with `test_blocks_edge.py` explicitly in that cycle's writable set. Rationale: don't-kick-
the-can says fix a known duplication now (we have it loaded); scope law says a closed contract file
is a deliberate writable-set grant, and its cold audit must re-run the FULL `test_blocks_edge` suite
+ the mutation proof (a byte-diff forgery pin consumes `_degrade_every_STORE_seam`). Not folded into
another cycle because it touches a closed file and needs its own mutation proof.

**ESCALATION — the one non-mechanical decision (placement):** the shared derivation introspects
`loremaster.store._txn`, so it **cannot** live in `lorerunes` (stdlib-only). Two homes: (a) keep it
in `scripts/forgery_door_sweep.py` and have `test_blocks_edge.py` import from `scripts/` (the
awkward tests→scripts seam; `test_forgery_door_sweep.py` already does a `sys.path` insert), or (b) a
small PRODUCTION helper in `loremaster.store` (it is production knowledge about production seams)
imported by BOTH, sidestepping the scripts↔tests seam. The agent and I both prefer (b). This is a
DESIGN decision (where shared code lives), so it is the builder-cycle's contract author's escalation
if not pre-ruled — I RECOMMEND (b); operator/lead may confirm.

**Mutation proof (prove SHARING, not routing):** mutate the shared CORE (flip the
`__module__ == "loremaster.store._txn"` string, or make the core return `{}`) → BOTH sides redden
together (`test_forgery_door_sweep.py` `store_seams` pins AND `test_blocks_edge.py`'s
`assert "run_query" in patched` + the byte-diff forgery pins that consume `_degrade_every_STORE_seam`).
Asymmetry to design around: a mutation to the door-only `statement` filter reddens only forgery; the
sharing-proof mutation MUST hit the common core (the only edit both consume) — state this in the
cycle's mutation-proof declaration.

### INSTRUMENT C — derive the mutating tool-set from annotations (#291) — SETTLED

**Investigation (a2d4 agent, HEAD):** drift confirmed — `_MUTATING_TOOLS = {"lore_remember",
"lore_index", "lore_findings", "lore_comms"}` (`test_mcp_server.py:1186`) omits `lore_claim_task`
and `lore_tasks`; with `_READ_ONLY_TOOLS` (9 names) the two hand-lists cover 13 of 15 tools and the
two uncovered are exactly the drifted pair. Production annotates both `readOnlyHint=False`
(`_TASK_TOOL_ANNOTATIONS`). All 15 tools carry a non-None `readOnlyHint` at HEAD, so the "every tool
has a non-None readOnlyHint" pin PASSES today. Tests already enumerate registered tools + annotations
via `{tool.name: tool for tool in await mcp.list_tools()}` (line ~1697); `TestToolAnnotations` (tests
at 1699/1708) is the model to extend.

**Property enforced:** the read-only / mutating partition is DERIVED from the production
`ToolAnnotations`, deny-by-default; a tool added without an annotation, or mis-annotated, is a test
failure — not a silently-writable (or silently-refused) hole.

**Design (the finding's fix, with the read-only side folded in):**
- **Derive BOTH partitions** from `mcp.list_tools()` annotations — mutating = `{name : readOnlyHint
  is not True}`, read-only = `{name : readOnlyHint is True}`. Deny-by-default: `is not True` means an
  UNannotated (`None`) tool counts as MUTATING (`== False` would leak a future unannotated tool). Both
  `_MUTATING_TOOLS` and `_READ_ONLY_TOOLS` hand-lists are the same drift class — replace both, not
  just the one that drifted.
- **Pin: every registered tool has a non-None `readOnlyHint`** (deny-by-default; a `None` is a design
  gap, not a default). Passes at HEAD; goes RED the day a tool is registered without one.
- **Keep `_ALL_BUILTIN_TOOL_NAMES` as the independent surface oracle** (asserting the surface is
  EXACTLY expected is a legitimate independent check — do not derive it from the same `list_tools()`
  it guards).

**Mutation proof (prove the set is DERIVED, per #291's owed invariant (b)):** flip one constant's
`readOnlyHint` in production (e.g. `_TASK_TOOL_ANNOTATIONS` → True) → that tool moves partitions and
its posture pin flips RED. A hand-list would not move; the derived set does.

**Positive/negative control:** POSITIVE — a synthetic tool with `readOnlyHint=None` fails the
non-None pin; a tool annotated `False` lands in the mutating set. NEGATIVE — a `readOnlyHint=True`
tool lands in read-only and is absent from mutating.

**Askable question:** *"Is my read-only/mutating split READ from the production annotations, or is it
a second list I have to keep in step with them?"*

**Security note (why this is beyond tidiness):** packet 39's HOSTED_OAUTH posture would build its
refusal set from the mutating set; a drifted hand-list would make `lore_claim_task`/`lore_tasks`
silently WRITABLE to remote principals. Deriving from annotations closes that inheritance — and this
composes with INSTRUMENT D (the posture refusal must observe the EFFECT, not the marker).

### INSTRUMENT D — refusal pins observe the EFFECT, not a proxy (#295) — F2

**F2 RULING: build the observe-the-EFFECT invariant + a one-time sweep NOW; route the STRUCTURAL
answer (gate registration/visibility so there is no "after") to packet 39. Do not entangle this
session with unbuilt auth** (the #333 baseline is 444 pytest / 191 mypy WIP failures; #296 is
operator-held). This matches the finding's own escalation.

**Property enforced:** a pin that asserts "the call was refused" also asserts the guarded EFFECT did
not occur (an invocation counter == 0, an unchanged store, an absent row) — not merely that an
exception was raised or a refusal marker rendered. Because a guard that performs the action and THEN
refuses is byte-identical, at every proxy observation point, to one that refuses first.

**Honest scope — what IS and is NOT a construction instrument here (stated, not glossed):**
- **BUILDABLE now, and it is the ONE-IMPLEMENTATION half:** a shared test helper
  `assert_tool_refused_and_did_not_run(mcp, tool_name, args)` that (a) drives a REAL MCP session
  (initialize → session id → tools/call — the wire path WB30 proved the in-process attribute guard
  was dead on), AND (b) asserts an invocation counter on the mutating tool body stayed 0 (the effect
  leg WB48 needed). Every refusal/posture pin CALLS it; the effect check is thereby ONE
  implementation, not re-hand-rolled per pin (which is how WB48 slipped — a new pin with its own
  weaker observation).
- **A ONE-TIME SWEEP (manual, not a permanent gate):** enumerate the existing refusal-shaped pins
  (auth posture pins + any `pytest.raises`/marker-asserting guard pins) and route each through the
  helper. This is an audit, ledgered with what was swept and what was found — NOT dressed as a
  standing invariant.
- **NOT buildable as a permanent AST gate, and I will not pretend it is:** "a refusal pin that does
  not check its effect" is not a structurally-crisp property (a `pytest.raises` is not distinguishable
  by AST from a legitimate error test), so there is no `test_anchored_pattern_seam`-shaped scan for
  it. The permanent guard is INSTRUMENT 0's reach-attack (does this refusal pin observe the effect or
  the proxy?) — a reasoning pass, said plainly.
- **The real structural fix is packet 39's:** gate REGISTRATION / VISIBILITY so a refused tool is not
  dispatchable and there is no "after" to place a guard in. Routed to 39; NOT built here. Packet 39's
  contract must consume INSTRUMENT D's helper for its posture pins.

**Mutation proof (of the helper):** place a test-double guard AFTER the tool body (the WB48 shape) →
the helper's effect leg reddens (counter == 1). Place it BEFORE → green with counter == 0. Positive
control: the helper catches the after-placement. Negative control: a correctly-refused call passes
with counter == 0 AND the refusal marker present.

**Askable question (the finding's own, promoted to INSTRUMENT 0):** *"If the guard ran AFTER the
thing it guards, would this pin still pass?"*

### INSTRUMENT B2 / F3 — #337 comms render-helper discovery — OPERATOR ESCALATION

**Investigation (a2d4 agent, HEAD) changes the F3 picture in two ways the finding's "e.g." hid:**

1. **There are TWO off-prefix comms-reachable render helpers, not one:** `_render_story_message`
   (server.py:6240, called by on-prefix `_render_comms_story`) AND `_render_fleet_status_cell`
   (7003, called by on-prefix `_render_comms_fleet_row`). Both serve `render_line` templates the
   promise-scanner never reads. The gap is broader than filed and grows with every off-prefix helper
   a comms renderer delegates to.

2. **The finding's proposed discriminator ("a method that calls a render primitive") OVER-MATCHES
   badly.** 25 off-prefix functions call the 3-set {render_line, render_fenced, render_attributed};
   `render_attributed` alone is a per-value sanitiser used across dozens of non-comms error/detail
   renderers (`_filter_miss_notice`, `_render_finding_detail`, `_render_task_detail`, …). Deriving
   discovery that way balloons the comms-scoped promise scan from ~19 to ~44 functions and drags every
   error string into the comms promise classification. The CLEAN structural property is the **CALL-
   GRAPH CLOSURE**: an off-prefix helper is in-scope iff it is transitively called by an on-prefix
   `_render_comms*` / `_comms_*` helper. That closure yields EXACTLY the two genuine gaps and excludes
   the 23 non-comms renderers. (Also reconcile a set mismatch: the SCAN verbs are `{render_line,
   render_join}` while the finding's discovery set is `{render_line, render_fenced, render_attributed}`
   — different concerns.) **This is design work — the scoping property must be invented and
   adversarially attacked; it is NOT a mechanical patch.**

**Does #345's instrument SUBSUME #337? NO — they are ORTHOGONAL scans over overlapping helpers.**
- #345 (INSTRUMENT B) is a FORGERY-CONTAINMENT scan; its name-blind P-U universe ALREADY reaches
  `_render_story_message` and `_render_fleet_status_cell` (they are AppContext methods interpolating
  values). So **the SECURITY dimension — a caller forgery leaking through an off-prefix helper — is
  already covered by INSTRUMENT B, regardless of #337's ledger status.** That is a real free win worth
  stating.
- #337 is a PROMISE-PROSE scan (served promise-shaped literals that must correspond to a real
  mechanism — the trust-doctrine "served English no gate checks" class). #345 does NOT scan promise
  literals. So #337's actual filed concern — *"a future promise-shaped literal added off-prefix serves
  to the LLM UNSCANNED"* — is **NOT subsumed**, and closing it is a genuine call-graph-closure design
  cycle, not free.

**RULING / RECOMMENDATION (operator decides — pinning #337 reverses the 2026-08-08 ledger-only
ruling):** I do NOT unilaterally reverse it. My recommendation: **keep #337 ledger-only for the
PROMISE scan**, because (a) the marginal cost is not zero — the call-graph scoping property is new
design — and (b) INSTRUMENT B independently removes the SECURITY dimension of #337's risk. Tighten
#337's re-open trigger to reflect (b): the residual is now *only* "a promise-shaped literal added to
an off-prefix comms-reachable render helper," the forgery dimension having been closed by INSTRUMENT
B. **IF the operator wants #337 pinned anyway** (the two-helper breadth is a fair argument for it),
it is a dedicated CONTRACT→adversary cycle building the call-graph-closure discovery + a coverage pin
(scanned-set == closure-derived-set, replacing the hand-list at test_comms_promise_registry.py:588–
606) — NOT folded into B, and NOT handed to a builder as "figure out the general form" (packet-01
routing rule: a property-to-invent escalates or goes to an author who attacks its own design).

---

## 4. Fork rulings — summary (rationale in the sections above / below)

- **F1 (currency vs scoped pytest):** SETTLED above (INSTRUMENT G). Non-omittable core
  (typecheck+ruff+currency) always full; pytest scoped in `--wave` with the selector echoed and
  the line marked SCOPED (never GREEN); full in `--checkpoint`. Mode is a required, recorded arg.
- **F2 (#295 vs unbuilt auth):** SETTLED (INSTRUMENT D). Build the observe-the-EFFECT shared helper
  + a one-time manual sweep NOW; route the structural answer (gate registration/visibility so there
  is no "after") to packet 39. Do not entangle this session with unbuilt auth (444 pytest / 191 mypy
  WIP baseline, #333). Honest bound: #295 has no permanent AST gate (a refusal pin is not
  structurally crisp) — its standing guard is INSTRUMENT 0's reach-attack.
- **F3 (#337 pin vs operator ruling):** SETTLED with an OPERATOR ESCALATION (INSTRUMENT B2). On
  investigation the finding's "e.g." undersold it (TWO off-prefix helpers, not one) and its proposed
  discriminator over-matches (25 funcs) — the clean property is the CALL-GRAPH closure, which is
  DESIGN work, not free. #345 and #337 are ORTHOGONAL scans (forgery-containment vs promise-prose):
  #345's name-blind P-U ALREADY covers the SECURITY (forgery) dimension of the off-prefix helpers, but
  does NOT subsume #337's promise-scan concern. **RECOMMENDATION: keep #337 ledger-only** (marginal
  cost is not zero; security dimension already covered by B) and tighten its re-open trigger; **IF the
  operator wants it pinned**, it is a dedicated call-graph-closure cycle. I recommend, the operator
  rules.
- **F4 (AST-scan substrate):** SETTLED above (INSTRUMENT A-SUB). ONE shared LIBRARY of reach
  helpers in `_logging_fixtures.py`; per-scan files stay separate; prove by mutation.
- **F5 (#279 touches a closed file):** *preliminary:* IN-SCOPE this session but as its OWN
  sequenced TDD cycle (contract-adversary + cold audit), because it rewrites
  `_degrade_every_STORE_seam` in `test_blocks_edge.py` (packet 04b-1 closed green at 8256/0) —
  don't-kick-the-can says fix it now, scope law says a closed file is a deliberate writable-set
  grant. See INSTRUMENT F / build plan.

---

## 5. Build plan

Roster per CLAUDE.md: every cycle is **contract (Opus) → contract-adversary (Opus) → builder (Opus)
→ cold audit (Opus)**; Fable is design sidecar (this doc) + escalation only. INSTRUMENT 0 is a change
to the adversary agent + a CLAUDE.md law line, not a code cycle. No store/schema/DDL is touched by any
cycle. Each cycle's cold audit re-runs the changed suites + the structural/AST pins (full suite only
at the phase checkpoint, per gates law).

**Dependency graph (revised after the DRY review — §7):**
- **ALL EIGHT instrument cycles are INDEPENDENT and parallelizable.** The earlier "A-SUB before B"
  dependency was WRONG: the DRY classification (§7) shows B extends test_link5's own server.py-scoped
  P-U/P-F and adopts neither A-SUB helper, so it does not wait on A-SUB. A-SUB is a prerequisite only
  for FUTURE new WHOLE-TREE scans (none in this batch).
- **F** is independent but is its own cycle (closed file, own cold audit).

**Wave 1 — parallel, independent (spin concurrently):**

| cycle | finding | writable set | do-not-touch | nature |
|-------|---------|--------------|--------------|--------|
| **G** — gate bundle | #344 | `scripts/wave_gate.py` (new), `scripts/test_wave_gate.py` (new) | `pending_contract_gate.py`, `gates.yaml` internals (inherit, don't re-list) | build-to-contract; highest leverage (the enforcement point, no CI) |
| **A-SUB** — scan helpers | F4 | `loremaster/tests/_logging_fixtures.py`; migrate `test_anchored_pattern_seam.py`, `test_backoff_seam.py`, `test_secret_typing.py`, `test_secret_leak_vectors.py` to the shared helpers | production code | refactor + mutation-proof |
| **C** — derive mutating set | #291 | `loremaster/tests/test_mcp_server.py` | `server.py` (read annotations, don't edit) | build-to-contract |
| **E** — trailing-newline pin | #289 | `loremaster/tests/test_gated_ground.py`, `scripts/wrong_builds.py` (add WB entry) | `gated_ground.py` prod logic (already fixed) | tiny, mechanical |
| **H** — baseline anti-vacuity | #290 | `scripts/_harness_guards.py` (new), `scripts/wrong_builds.py`, `scripts/test_wrong_builds.py` | — | tiny; extract + covering test |
| **D** — observe-the-effect | #295 | a shared test helper (`loremaster/tests/` support) + the refusal-shaped pins swept (name them in the cycle) | packet-39 files (operator-held) | helper + one-time sweep; structural half → pkt 39 |

**Wave 1 (cont.) — B is INDEPENDENT (DRY-review correction, §7 — no longer "after A-SUB"):**

| cycle | finding | writable set | do-not-touch | nature |
|-------|---------|--------------|--------------|--------|
| **B** — render slot inventory + `sanitise_line` scan | #345 | `loremaster/tests/test_link5_render_containment.py`, `loremaster/tests/render_injection_scaffold.py` | `render.py`/`sanitise.py` (already have the seams); the code_rag/B-5 owned sites (allowlist or re-pin, don't silently flag) | **design-heavy** — EXTENDS existing P-U/P-F (no new classifier); subtle bounds (provenance not name-blind derivable; zero-FormattedValue comms renders; indexed-content bound). Contract-adversary must attack the deriver's REACH. |

**Independent — own cycle, any time:**

| cycle | finding | writable set | do-not-touch | nature |
|-------|---------|--------------|--------------|--------|
| **F** — one store-seam derivation | #279 | `scripts/forgery_door_sweep.py`, `scripts/test_forgery_door_sweep.py`, `loremaster/tests/test_blocks_edge.py`, **+ (if placement (b)) a new helper in `loremaster/loremaster/store/`** | other test_blocks_edge contracts | **closed-file** cycle; cold audit re-runs FULL `test_blocks_edge` + the sharing mutation-proof. PLACEMENT is an escalation the contract author raises (I recommend a production `loremaster.store` helper). |

**Operator escalations to resolve BEFORE the relevant cycle (AskUserQuestion at wave open):**
1. **F3 / #337** — keep ledger-only (my recommendation) or authorize a dedicated call-graph-closure
   pin cycle? (Pinning reverses the 2026-08-08 ruling.)
2. **F5 / #279 placement** — production `loremaster.store` helper (my recommendation) vs tests→scripts
   import seam.
3. **INSTRUMENT B cleanup** — retire the OLD `_RENDER_DRIVERS` hand-net (with the literal `task_id=None`
   hardcodes) now, or leave it as a retained labelled subset? (The file flags this itself.)

**Recommended order if serialised (not required):** INSTRUMENT 0 (cheap, generalises) → G →
A-SUB / B / C / E / H / D (all independent, parallel) → F. G first because it is the enforcement point
every subsequent cycle's close-out runs through. (F any time — own cold audit.)

---

## 6. What this does NOT claim (trust-doctrine self-check)

- There is **no single scanner** that catches the class; INSTRUMENT 0 is a reasoning pass, and it can
  miss — which is why the eight instances get their own mechanical pins too.
- **#295 has no permanent AST gate** — a refusal pin is not structurally crisp. Its standing guard is
  INSTRUMENT 0 + the shared helper + a one-time sweep; the real fix is packet 39's registration gating.
- **#345's door/safe provenance still requires judgement** (measured: not name-blind derivable). The
  instrument makes the slot INVENTORY derived so a wrong judgement surfaces as an un-driven slot — it
  does not remove the judgement.
- **#337's promise dimension is not fixed this session** (ledger-only recommended); only its forgery
  dimension is, and that as a side effect of #345.
- The **F4 consolidation is `parse_production_trees` (5 adopters) + a tree-scan-scoped `assert_covers`
  (2 adopters)**, NOT all 14 `rglob` files. The rest are ALLOWLISTED non-adopters (single-package
  scanners, `.md`/retired-name sweeps, test-tree scans, the git-tracked NUL scan, the indexer corpus).
  Over-consolidating `assert_covers` across every reach-check (render candidates, runtime sites,
  probes) is DELIBERATELY NOT done — that would be a DRY error in the other direction.
- Cross-session recurrence between wave close-outs (before CI, #285) remains a bound of the gate
  bundle; re-open trigger named in INSTRUMENT G.

---

## 7. DRY REVIEW (operator, 2026-08-09)

Re-review of every instrument under the re-prioritised lens: **DRY / ONE IMPLEMENTATION is now #1**,
and several findings are CAUSED by duplication. Each fix must be genuine CONSOLIDATION proven by
MUTATION — never a fresh copy, never route-without-share, never two sources of truth for one policy.

### The sharpest finding first — the consolidation instrument is subject to its own class

**A-SUB (the shared reach-primitive) is itself an instance of the class this doc is about.** Its
REACH is *which callers actually adopt it*, and if that reach is a hidden constant — "I migrated the
files I remembered" — then A-SUB is a 15th copy nobody adopts, and the ~14× duplication survives
while a green suite says it was fixed. That is the class, reproduced inside the fix for the class.

Two consequences, both design-forcing:
1. **The design must NOT hardcode an adopter list.** A list of "the files to migrate" in this doc or
   a brief IS the enumeration antipattern (`registration_sites.py`'s whole reason for existing). The
   adopter set is DERIVED from a property — *"a test that parses every production tree across
   workspace roots"* — and the migration's completeness is a CHECKED VARIABLE.
2. **A-SUB ships with an ANTI-DUPLICATION STRUCTURAL PIN**: no test file hand-rolls
   `rglob("*.py")+ast.parse` (the whole-tree parser) or a bare `assert observed == declared`
   reach-assertion OUTSIDE the shared helpers, except an ALLOWLIST of non-adopters each carrying an
   evidence-backed reason (a file that parses ONE module for an unrelated purpose is a legit
   non-adopter, not a private copy). This pin is what makes "migrate, don't add a 15th" mechanical.

### Answers to the four review questions

**Q1 — consolidate, or could it add a parallel copy? (per instrument)**

| instrument | duplication it targets | verdict | design change forced |
|---|---|---|---|
| **F / #279** | store-seam derivation written TWICE | **CONSOLIDATES** — the core case; one `_txn_coroutines` core, both subsets from one walk | none (already designed as consolidation; placement = prod `loremaster.store` per stamped ruling) |
| **A-SUB / F4** | tree-parser + coverage-assertion hand-rolled ~14× | **CONSOLIDATES — but ONLY with the anti-dup pin + mutation proof above.** Without them it ADDS a 15th | add anti-duplication pin; derive adopter set by property; prove by mutation (below) |
| **C / #291** | test hand-list beside prod annotations | **CONSOLIDATES the hand-list — but risks MOVING the duplication** (test-derivation vs a future pkt-39 prod-derivation of the same "which tools mutate" policy) | **expose the derivation as a PRODUCTION helper** (see Q4-flag-1) |
| **G / #344** | gate set re-listed per spawn-brief | **CONSOLIDATES** — inherits `gates.yaml` via `pending_contract_gate.py`, re-lists nothing | wrapper must INVOKE `pending_contract_gate`, never re-parse `gates.yaml` (Q4-flag-4) |
| **B / #345** | (not duplication-rooted) | **NEUTRAL, with a copy RISK**: a new slot-coverage/superset-proof could be a 3rd hand-rolled coverage check + a 4th interpolation classifier | route new coverage through `assert_covers`; reuse existing interpolation predicates (Q4-flag-2) |
| **E / #289** | (not duplication-rooted) | **ADDS NOTHING** — adds discriminating fixture inputs + one wrong-build to an existing matrix | none |
| **H / #290** | inline baseline-guard, no shared home | **CONSOLIDATES** (inline → `refuse_vacuous_baseline`); single caller today, justified by the named recurring policy | none; but do NOT over-consolidate with `pending_contract_gate`'s reader-anti-vacuity (Q4-flag-5) |
| **D / #295** | (not duplication-rooted) | **CONSOLIDATES the EFFECT-check** into one helper all refusal pins call | none; but correct the framing (Q2) |

**Q2 — is the reach-check ONE primitive that B, D, and future scans CALL, not clone?**

⚠ **Investigation (a944 agent, HEAD) corrected my first answer, and the correction is itself a DRY
point: forcing EVERY reach-check through one `assert_covers` would be OVER-CONSOLIDATION — a DRY
error in the other direction.** The "observed==derived, fail-closed" reach-check is a repo LAW applied
over HETEROGENEOUS subjects — workspace members, runtime backoff sites, dispatch actions, operation
probes, render candidates — and most call sites carry LOAD-BEARING bespoke failure messages
(per-member breakdowns, both-direction diffs). Collapsing those into one generic helper would either
need an over-parameterised helper or would strip the custom messages, which is a trust cost. **DRY
means ONE copy per POLICY, not one copy total** (same as Q4-flag-5). So the reach machinery splits
into a CLEAN shared primitive and a SCOPED one, and B/D are handled by their own right homes:

- **`parse_production_trees()` — the CLEAN shared primitive. 5 real adopters, ~identical
  member-iteration + `rglob` + `ast.parse`:** `test_anchored_pattern_seam` (`_parse_production_trees`,
  own), `test_secret_typing` (`_python_sources` + a DUPLICATE `_SCANNED_MEMBERS` member hand-list —
  a #291-shaped drift killed for free by the migration), `test_comms_footer` (own + a regex
  member-reader; needs an `include_tests` knob + per-member grouping), and `test_backoff_seam` +
  `test_secret_leak_vectors` (which ALREADY call the shared `production_sources()` then re-`ast.parse`
  — they consume parsed trees instead). Lives in `_logging_fixtures.py` beside `production_sources`;
  yields LABELED/grouped trees (`production_sources` already returns `(label, path)`), so comms_footer's
  per-member reach and secret_typing's keys are served without re-grouping. **This is the real F4
  consolidation — ship it firmly.**
- **`assert_covers(observed, derived, *, subject)` — SCOPED to the TREE-SCAN reach tier only** (the
  "the workspace scan reached every declared member" case: `test_anchored_pattern_seam::TestScanCoverage`
  + `test_secret_typing`'s member-reach pins, `derived = pyproject members`). It pairs naturally with
  `parse_production_trees`. **Do NOT extend it to the runtime-site / action / probe / render-candidate
  reach-checks** — those keep their bespoke derivations and messages; a "one helper for all reach
  law" is over-consolidation. (A *second* generic helper for those is a POSSIBLE follow-up only if the
  operator wants that breadth — surfaced, not assumed.)
- **B / #345 does NOT adopt either global helper.** Its coverage is over server.py render candidates,
  the SAME subject as test_link5's EXISTING P-U/P-F — which is already the ONE implementation of
  render-slot coverage. **B EXTENDS P-U/P-F; it must not add a parallel coverage check or a new
  interpolation classifier** (Q4-flag-2). That is the DRY-correct "one primitive B calls" — it is
  test_link5's own apparatus, not a global helper. (Confirmed: P-U/P-F are `ast.parse(server.py)` +
  AppContext-scoped, NOT whole-tree — so `parse_production_trees` is the wrong tool for B.)
- **D / #295 shares the EFFECT-check, not a coverage check.** It would be a FALSE CLEAR to claim D
  routes through `assert_covers`: there is no derivable "refusal-pin set" (F2's stated bound), so D
  has no permanent coverage-as-checked-variable to share. D's ONE implementation is the effect helper
  `assert_tool_refused_and_did_not_run` (wire session + invocation-counter==0) that every refusal pin
  calls. D's un-derivable reach is guarded by INSTRUMENT 0, said plainly — not a pretend coverage pin.

**Net:** the genuinely-shared reach primitive is `parse_production_trees` (5 adopters, proven by
mutation); `assert_covers` is a small tree-scan-tier helper (2 adopters); B and D each route through
their OWN correct single implementation (P-U/P-F; the effect-helper). No instrument is forced through
a helper whose subject it does not share — that restraint is as much DRY as the consolidation is.

**Q3 — does A-SUB actually MIGRATE, proven by mutation?**

Yes, and this is the load-bearing part of the A-SUB cycle (not an afterthought):
- **Migrate** every whole-tree scanner onto `parse_production_trees`, and every observed==derived
  reach-check onto `assert_covers`. The adopter set is DERIVED (the property above), not listed here.
- **Mutation proof (prove sharing, not routing):** change the shared parser (e.g. make it return
  `{}` / drop `scripts`) → EVERY adopter's coverage pin must redden **in one run**. A caller that
  stays green is a private copy wearing the shared name (routing-not-sharing) — the mutation names it.
- **Completeness of the migration is itself a checked variable:** the anti-duplication structural pin
  (no hand-rolled parser / reach-assertion outside the allowlist) fails if a whole-tree scanner was
  left un-migrated, or a new one lands hand-rolled later. Without this pin, "migrated" is a claim over
  the files someone remembered — the exact class. (Current adopter set enumerated as evidence below;
  the DESIGN binds to the property, not to the count.)

**Q4 — routing-not-sharing traps (two sources of truth for one policy):**

1. **C / #291 — the sharpest trap.** Deriving the mutating set INSIDE test code, while packet-39 auth
   later derives its own refusal set from the same annotations, is the #102/#120 trap: the policy
   *"which tools mutate"* written twice, free to diverge. **DESIGN CHANGE: the derivation is a
   PRODUCTION helper** (e.g. `loremaster` exposes `mutating_tool_names(server)` / a
   read-only/mutating partition over the registered annotations); the test PINS it, and packet 39
   CONSUMES it. One derivation of the policy, in production, read by both. (This is cheap and is the
   ONE-IMPLEMENTATION-correct home even though pkt 39 is de-prioritised — it prevents the second copy
   from ever being written.)
2. **B / #345 — two sub-traps.** (a) The retire-old-net **superset proof must route through
   `assert_covers`** (old-net slot set ⊆ AST-derived inventory), not a bespoke comparison — else the
   very proof guarding the retirement is a private copy. (b) B must **reuse the existing interpolation
   predicates** (`_raw_render_interpolations`, `_expr_door`, `_appcontext_methods`) — authoring a new
   "what is a render slot" classifier makes a 4th copy of that policy in the one file that already has
   three. Extend; do not fork.
3. **A-SUB — the TREE-SCAN coverage checks are private copies until migrated; the others are NOT.**
   `test_anchored_pattern_seam::TestScanCoverage` and `test_secret_typing`'s member-reach pins
   hand-roll the SAME policy (workspace scan reached every member) → migrate both onto `assert_covers`.
   But do NOT chase the reach-check pattern into `test_link5`'s P-U/P-F, `test_backoff_seam`'s runtime
   sites, etc. — those cover DIFFERENT subjects with load-bearing bespoke messages, and routing them
   through a generic helper is over-consolidation (Q2). The right grain: `parse_production_trees` for
   the 5 whole-tree parsers, `assert_covers` for the 2 tree-scan reach checks, and everything else
   keeps its own correct single implementation.
4. **G / #344 — one gate-set reader.** `wave_gate.py` must INVOKE `pending_contract_gate.py`
   (`--currency`, inheriting the manifest-derived leg set); it must NOT parse `gates.yaml` itself or a
   second reader of the manifest exists. The changed-suite selector logic lives in ONE place in the
   wrapper.
5. **H / #290 — do NOT over-consolidate.** `refuse_vacuous_baseline` (a COMPARISON's reference
   measured nothing) is a DIFFERENT policy from `pending_contract_gate`'s reader-anti-vacuity (a
   gate's OWN output is not a measurement). Forcing them to share would merge two policies into one
   wrong predicate. DRY means one copy PER policy, not one copy total — flagged so the builder does
   not "helpfully" unify them.

### Design change to INSTRUMENT 0 (the reach-attack) forced by this review

Add a fourth leg to INSTRUMENT 0's REACH ATTACK, because Q4 shows the class and the DRY trap are the
same shape observed from two sides: **(5)** *does this instrument leave TWO sources of truth for one
policy, and is its sharing proven by MUTATION (change the shared thing → every caller reddens)?* A
guard that routes to a shared driver while hand-rolling the decision underneath it (routing-not-
sharing) passes every gate that only checks the call — so the adversary must demand the mutation
proof, not the call site.

### Builder-brief changes the lead needs BEFORE the build wave

These are not cosmetic — they change what the builders build:
- **A-SUB:** brief is "**consolidate + pin**", not "add a helper". It MUST: ship `parse_production_trees`
  in `_logging_fixtures.py` (labeled/grouped trees; `include_scripts`/`include_skills` exist, add
  `include_tests`) and migrate the **5** whole-tree adopters onto it (retiring `test_secret_typing`'s
  duplicate `_SCANNED_MEMBERS` too); ship `assert_covers` SCOPED to the 2 tree-scan reach checks (NOT
  the runtime/action/probe/render reach-checks — that is over-consolidation); ship the
  anti-duplication structural pin (no hand-rolled whole-tree parser / bare member-reach assertion
  outside the shared helpers, with the non-adopter allowlist + reasons from §7); prove sharing by
  MUTATION (change the shared parser → all 5 adopters redden in ONE run). MUST NOT widen the
  single-package scanners to whole-tree (scope change, not consolidation — flag any candidate).
- **B / #345:** does NOT use A-SUB. MUST EXTEND test_link5's existing P-U/P-F apparatus (the one
  implementation of render-slot coverage) — no parallel coverage check, no new interpolation
  classifier (reuse `_raw_render_interpolations`/`_expr_door`/`_appcontext_methods`); the retire-old-net
  SUPERSET proof extends the same apparatus (old-net slots ⊆ AST-derived inventory).
- **C / #291:** MUST land the mutating/read-only partition as a **production** derivation the test
  pins and pkt 39 will consume — not an inline test-only derivation.
- **D / #295:** MUST land the effect-check as ONE shared helper every refusal pin calls; brief states
  D has NO permanent coverage pin (honest bound), guarded by INSTRUMENT 0.
- **INSTRUMENT 0:** add leg (5) above to `contract-adversary.md`'s reach-attack (the P1c already
  committed) — one edit.
- **Sequencing correction:** B is INDEPENDENT of A-SUB (it extends test_link5, adopts neither global
  helper). Only future NEW whole-tree scans depend on A-SUB. See §5 update.

### Current adopter set (EVIDENCE, not the design binding)

*Enumerated (a944 agent, HEAD 74694dc) to size the work and confirm the property is clean; the design
binds to the PROPERTY + the anti-dup pin, NOT to this list — a hardcoded list is the antipattern.*

**`parse_production_trees` adopters (whole-workspace production `.py` AST scan) — 5:**
`test_anchored_pattern_seam` (own `_parse_production_trees`), `test_secret_typing` (own
`_python_sources` + a duplicate `_SCANNED_MEMBERS` list → both retired), `test_comms_footer` (own
`_scan` + regex member-reader; needs `include_tests` + per-member grouping), `test_backoff_seam`
(already calls `production_sources()`), `test_secret_leak_vectors` (already calls
`production_sources()`/`workspace_roots()`). The last two are partial adopters already — the
migration finishes the job (consume parsed trees, stop re-`ast.parse`-ing).

**`assert_covers` adopters (tree-scan reach tier) — 2:** `test_anchored_pattern_seam::TestScanCoverage`,
`test_secret_typing`'s member-reach pins. (Other files carry the reach-check PATTERN over non-tree
subjects — `test_backoff_seam` runtime sites, `test_task_read_surface` actions, `test_surreal_harness`
probes, `test_retry_seam` seam events, `test_link5` render candidates — but with bespoke derivations
and load-bearing messages: NOT `assert_covers` adopters; a possible second helper only on operator call.)

**NON-adopters (the anti-dup pin's ALLOWLIST, each with its reason):**
- *Single-package (loremaster) by design:* `test_render_seam_pins`, `test_task_read_surface`,
  `test_link5_render_containment`, `test_surreal_store`, `test_text_hygiene`, `test_retry_seam`.
  ⚠ Several generalise over a `root` arg but are called with the loremaster package TODAY — widening
  them to whole-tree is a SCOPE CHANGE (could widen a gap, priority #3), NOT consolidation. The A-SUB
  builder must NOT "helpfully" fold these into the whole-tree scanner; surface any such candidate as a
  separate scope decision.
- *Different scope / non-`.py` suffixes (candidates for a DIFFERENT shared "retired-name sweep"
  primitive, not these):* `test_retired_symbols` (`.py`+`.md`, pkg+tests+docs),
  `test_floor_calibration_schema` (pkg+tests+doc-globs).
- *Test-tree scan, not production:* `test_surreal_harness`.
- *Whole-repo git-tracked-text, not workspace-`.py` AST:* `test_text_hygiene::_tracked_text_files` (NUL scan).
- *Unrelated purpose (indexer corpus feed):* `test_search`.

Confirmed for F3/B: `test_link5`'s P-U (`TestEveryRenderCandidateIsDrivenOrOut`) and P-F
(`TestTheFieldManifestCannotSilentlyMissAField`) are `ast.parse(server.py)` + AppContext-scoped, NOT
whole-tree — so B extends them and adopts neither global helper (Q2).
