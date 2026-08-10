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

---

## 8. CONTRACT-ASUB-B RULINGS (fable-designer, 2026-08-09)

Three design judgments surfaced by `contract-asub-b`. Ruled with evidence (HEAD `74694dc`).

### Ruling (1) — `parse_production_trees` test-file inclusion: PER-ADOPTER, not a global policy

**`include_tests` is a per-call PARAMETER, and the migration is BEHAVIOUR-PRESERVING PER ADOPTER —
each adopter's post-migration scanned FILE SET must equal its pre-migration set EXACTLY, pinned per
adopter.** There is no single global answer, because the adopters DISAGREE by intent (a944 evidence):
`test_comms_footer` scans prod AND tests; `test_backoff_seam`/`test_secret_leak_vectors` are prod-only;
`test_anchored_pattern_seam`/`test_secret_typing` exclude MEMBER tests. A global `include=True` would
WIDEN the prod-only scans (new files, possibly new REDs); a global `exclude` would NARROW
comms_footer — both **widen a gap (priority #3)**. So parameterize and preserve.

- "Behaviour-preserving = INCLUDE" is correct ONLY as shorthand for "reproduce each adopter's current
  reach." For the anchored scan that means keep parsing `scripts/test_*.py` (it does today, because
  `scripts/` is a FLAT root) — so `include`, for that adopter, is right. It does NOT license a global
  include on the prod-only adopters.
- **Mechanism subtlety the builder must honour, not assume:** member tests live at `<member>/tests`,
  OUTSIDE the package root `<member>/<member>` that `workspace_roots` yields — so member tests are
  structurally excluded for member roots regardless of any flag, while `scripts/test_*.py` are
  included because `scripts/` is flat. `include_tests` therefore does not have a uniform meaning
  across root kinds; the builder VERIFIES each adopter's exact file set (a per-adopter scanned-set
  equality pin), never trusts the flag to mean the same thing everywhere.
- **This does NOT conflict with §7's "MUST NOT widen single-package scanners to whole-tree"** — that
  rule is the ROOTS-SCOPE axis (single-package → all-members); test-inclusion is an ORTHOGONAL axis,
  governed equally by behaviour-preservation.

### Ruling (2) — `blocked_by` is a forgery DOOR, NOT opaque-IDs-only SAFE

**DOOR. `render_attributed` is REQUIRED (it is already used at every site at HEAD); it must be PINNED
so a revert to `safe_str` — or to list-`repr()`-only containment — goes RED. Do NOT allowlist it
SAFE: that classification is FALSE and is exactly the #345 mis-classification (a door parked in
SAFE).** Evidence (HEAD):
- `TaskSpecItem.blocked_by` is `list[str] = Field(default_factory=list)` (server.py:1420) —
  UNCONSTRAINED caller strings at the boundary.
- `create_many` passes non-sibling-key refs through VERBATIM (`key_to_id.get(ref, ref)`,
  server.py:4595) — the dispatcher validates keys, cycles, and id-shaped keys, but does NOT constrain
  a non-key `blocked_by` ref to a task-id shape, so arbitrary caller text can reach the field.
- `create_task` echoes the caller's supplied blocker VERBATIM into a refusal message
  (`test_blocks_edge::test_a_create_blocked_on_a_SUPERSEDED_task_is_REFUSED`); `superseded_blockers`
  dict keys are caller `blocked_by` ids (contract line ~1705).
- **The B contract's OWN door-set already lists `blocked_by`** (test line ~1701) — SAFE would
  contradict the contract.

**Trust/don't-widen frame (operator priority: trust + don't-widen > security):** even at a small user
base, a blocked_by that can carry caller text is a served surface that could read as lore's own voice;
containment is a TRUST property, not a security-sized one. Allowlisting SAFE would be a FALSE CLEAR
(priority #2) and widen a gap (priority #3).

**Additional required fix (trust-honesty):** correct the false-safety framing that invites removing
containment — the `_render_task_rows` comment (server.py:~4631, *"defense-in-depth, though this field
is NOT live-forgeable"*) and the contract note (test line ~734, *"opaque ids, safe_str"*). The
list-`repr()` escaping is a FRAGILE secondary property (it holds only while blocked_by is rendered
inside a `[...]` literal; a future join-into-prose refactor opens the door); `render_attributed` is
the PRIMARY, required containment and the comments must say so. This is a served-English defect of the
exact class this doc is about.

### Ruling (3) — SAFE allowlist keyed by field-NAME: CONFIRM, conditional on the drive-all + P-N chain

**CONFIRM field-name keying (DRY-correct — ONE evidence-backed entry per field, vs (method,field)'s N
copies), CONDITIONAL on three properties that together cover the quantifier risk that field-name
keying otherwise carries ("safe in the site I examined" asserted over ALL sites):**
- **(a) B drives EVERY AST-derived interpolated slot with a forgery REGARDLESS of SAFE status.** SAFE
  must NOT mean un-driven — that was the #345 root cause (`task_id` SAFE ⇒ never tokenised ⇒ never
  driven ⇒ P-S/P-N blind). This is INSTRUMENT B's core fix (derive the slot inventory from AST; assert
  each is driven with real content). Without it, field-name keying REOPENS #345 and must instead be
  (method,field).
- **(b) P-N (the runtime containment proof, `test_link5` line ~2865) proves containment PER RENDER
  SITE over every forge shape** — so a field genuinely safe in site X but a door in site Y is caught
  at Y, which is what makes a GLOBAL (field-name) key sound: the key is a hint, P-N is the per-site
  verifier.
- **(c) the documented bound states explicitly** that a field-name SAFE entry asserts the field
  carries non-forgeable content in EVERY site that interpolates it, with a named re-open trigger (a new
  render site interpolating that field with a different provenance).

DRY favors field-name (one entry); the quantifier risk is covered by the drive-all + P-N backstop, NOT
by multiplying entries into (method,field). If for any reason (a) cannot hold (SAFE stays un-driven),
field-name keying is UNSOUND — but eliminating un-driven SAFE is B's whole purpose, so the condition
is the design, not an obstacle.

---

## 9. THE ∀-MUTATION-PROOF PATTERN (consolidated, operator-directed 2026-08-09)

All FIVE contract adversaries returned **INSUFFICIENT on ONE class**, each with a surviving wrong
build. This section is the SINGLE place the contract reviser starts, so the fix is consistent across
packets rather than five ad-hoc patches. It is the constructive form of INSTRUMENT 0's leg-(5) reach
attack: the adversary ASKS "is this guard's reach a checked variable?"; §9 is HOW the author ANSWERS.

### 9.0 The class, with the receipt from each report (read the reports; this is the index)

> **A "prove-sharing / coverage / liveness by mutation" pin mutates ONE member of a derived set, so a
> HYBRID build that routes/derives THAT member but HARDCODES the rest passes the whole contract —
> reach-is-a-hidden-constant, inside the very contract built to kill it. The mutation-proof must be ∀
> over the DERIVED surface.**

| packet | surviving wrong build (the hybrid) | why it survived |
|---|---|---|
| **F/#279** (`REPORT-adversary-f`) | WB8 `_degrade` routes `run_query`+`bootstrap_session`, HARDCODES the other 2 doors — **BLOCKER, no consistency backstop**; WB7 `store_seams` same shape (residual, backstopped) | mutation drops only `run_query` (+`bootstrap_session`); undropped seams never tested for routing |
| **C/#291** (`REPORT-adversary-cd`, #347) | C-WB5 derives all tools EXCEPT `lore_findings` (hardcoded) — passes all 10 | liveness proof flips only `_TASK_TOOL_ANNOTATIONS` → reach 2/15 tools |
| **G/#344** (`REPORT-adversary-g`) | MP-4 wave×ruff orphan waved through; MP-1 `main` runs no gates, returns 0 (BLOCKER); MP-2 `main` re-parses gates.yaml; MP-3 summary over-claims; MP-5 echo monoculture | the fail-matrix is HAND-PICKED cells not ∀(mode×gate); the ENTRYPOINT is never driven; the SUMMARY is never pinned; echo has one value |
| **H/#290** (`REPORT-adversary-eh`) | correct helper + inline copy KEPT (two copies) — passes green, **BLOCKER** | the "`main` SHARES the helper" property has NO red home |
| **D/#295** (`REPORT-adversary-cd`, #346) | D-WB2 in-process helper (`wire.mcp.call_tool`), dead on the wire — passes all 6 | the WIRE-driving claim is asserted in a docstring, verified by no pin |
| **E/#289** | — no survivor (instance mutation-proven) | residual only: Exemption door-field coverage optional (§9 IDIOM 1, operator-optional) |
| **A-SUB/F4** (`REPORT-adversary-asub-b`) | fix-NOTHING build passes 16/0: 3 of 4 migration files "migrated" by an UNUSED `import … as _asub_route # noqa: F401`; `test_secret_typing._SCANNED_MEMBERS` + 3 private `rglob` clones survive | `_MIGRATION_SET` + the clone-check are HAND-LISTS; routing pin checks import PRESENCE not USE; sharing has no RED home (single-module monkeypatch can't reach a from-import adopter) |
| **B/#345** (`REPORT-adversary-asub-b`) | contract UNSATISFIABLE without a false clear: Leg-2 false-flags the Ruling-2-correct `[render_attributed(b) for b in blocked_by]`; only green via the Ruling-2-FORBIDDEN `blocked_by`-SAFE entry | Leg-2 containment detector is COMPREHENSION-BLIND (sees only a direct `render_attributed(...)` as the whole value) |

### 9.1 IDIOM 1 — ∀-MUTATION-PROOF over the LIVE-DERIVED surface (the heart)

**Two complementary legs, BOTH ranging over the SAME surface that is re-derived LIVE from production
truth inside the test (never a fixture constant, never a hand-list in the test):**

- **LEG A — CONSISTENCY (inherently ∀, the cheap primary guard).** Re-derive the FULL surface from
  production truth each run and assert the caller's set/behaviour EQUALS it:
  `assert_covers(caller_set, live_derived_surface)` (fail-closed on empty). Catches a hardcoded or
  stale member (divergence) **without dropping anything**. This is why F's `store_seams` (which HAS a
  live consistency pin) was only a residual while `_degrade` (which LACKS one) was the BLOCKER — the
  consistency pin is the strongest, cheapest catch. **Reach for it FIRST wherever the caller's set is
  independently observable.** (This reuses the A-SUB `assert_covers` primitive — ONE implementation of
  the coverage sub-step across every packet; the DRY link.)
- **LEG B — LIVENESS (must be explicitly ∀).** Flip/drop EACH member of the live surface in turn;
  assert every dependent caller reddens/moves FOR EACH. Catches a caller that doesn't actually READ
  truth (a hardcode that happens to agree today — the consistency pin can miss this if the caller's set
  is not independently observable). This is the leg the class defeats: the failure was always
  single-member. `@pytest.mark.parametrize("member", sorted(live_derived_surface()))`, with a
  POSITIVE CONTROL per member (assert present BEFORE the flip, so a shrunk surface can't pass
  vacuously) and a BOTH-DIRECTION diff (a member that does NOT redden on its flip = a private copy —
  the #194 mutation_proof.py lesson: declare the expected-RED set from the surface, diff both ways).

**⚠ THE META-RECURSION (the lead's sharpest point — the helper is subject to its own class).** LEG B's
reach is `sorted(live_derived_surface())`. If that surface is a fixture constant or a hand-list in the
test, the ∀ is a hand-list wearing a loop — the trap one level up. So: (a) the surface is computed
LIVE in-test from the same production source the code derives from (`_txn_coroutines()`,
`mcp.list_tools()`, `manifest.gates`, the shared guard's call sites); (b) LEG A's `assert_covers`
makes LEG B's reach a CHECKED VARIABLE (the parametrized member-set must EQUAL the live surface —
grow the surface, the parametrization must grow or the coverage pin reddens); (c) **prove the pattern
itself by mutation** — mutate the production source (add a member) and confirm BOTH the parametrization
count moves AND the consistency pin reddens on a stale caller. A shared ∀-helper, IF built, is proven
the same way: shrink the surface it is handed → its coverage assertion reddens.

**DRY grain (consistent with §7's over-consolidation ruling):** the PATTERN is an idiom applied per
instrument; it is NOT one function. The mutation MECHANISM differs irreducibly (F flips coroutine
identity; C flips an annotation hint; G checks gate routing; H deletes a call) — merging them is the
`assert_covers`-over-everything error. What IS shared: the coverage sub-step (`assert_covers`, LEG A).

**SHARING specialization (H/#290 BLOCKER, G/#344 MP-2 — "X SHARES the ONE implementation").** The
surface is the CALL SITES; the mutation is DELETE-THE-CALL: delete the caller's call to the shared
helper → the caller's own covering pin reddens (H: drive `wrong_builds.main`'s zero-baseline path, or
spy that it invokes `refuse_vacuous_baseline`; G: spy that `main` calls
`pending_contract_gate._run_selected_gates(manifest.ids)` exactly once). PLUS an anti-duplication pin
(no second inline copy / no second `yaml.safe_load` of the manifest). **Honest bound:** the anti-dup
pin is name/pattern-keyed, so a third-named private copy escapes it (C's R1) — that un-derivable tail
is INSTRUMENT 0's standing guard, stated, not pretended closed.

Closes: F WB7/WB8, C C-WB5/#347, G MP-2/MP-4, H BLOCKER, and (optional) E residual.

### 9.2 IDIOM 2 — WIRE/EFFECT SPY (observe the real boundary, never a proxy)

A pin claiming a WIRE/EFFECT/ENTRYPOINT is driven must OBSERVE it at the real boundary via a SPY, not
an in-process proxy or a renderer's return value.

- **Instrument the boundary with a spy/counter** (wrap the object handed in so the real call is
  counted); assert the count moved for the claimed effect (≥1 wire call; invocation-counter==0 for a
  REFUSED call; exit-code for an ENTRYPOINT; store row absent/present).
- **STRONGEST FORM — make the proxy unrepresentable by construction** (D's R4): hand the helper ONLY
  the boundary callable, not the whole session exposing `.mcp`. Then the in-process door is unreachable,
  not merely pinned. Prefer this where the API allows.
- **Pos + neg controls:** correct build moves the count; the proxy build (in-process / marker-only /
  read-before-dispatch / renderer-return) does NOT. Auth-free and DEMONSTRATED in the D loopback
  setting (`REPORT-adversary-cd` §D.4), so "you can't pin the wire without auth" is FALSE.
- Covers D-WB2/#346 (wire spy) AND G MP-1 (drive the REAL `main` via a gate-runner spy, assert the
  EXIT CODE — the over-tested pure renderer is not the enforcement point; the entrypoint is).

**Honesty fork (D):** BUILD the auth-free spy NOW (it does not entangle unbuilt auth — it is a loopback
wire in the D contract's own setting, and packet 39 will CONSUME this helper and inherit the gap). Only
DEMOTE the step-1 docstring claim if the spy proves un-constructible — it was demonstrated constructible,
so build it. The STRUCTURAL answer (gate registration/visibility) stays routed to packet 39; the
wire-spy on the effect-helper is this session's.

### 9.3 IDIOM 3 — SUMMARY HONESTY (a qualified leg can never render an unqualified pass)

- The summary verdict is DERIVED from the per-leg qualification flags (a typed `scoped: bool` /
  `qualified: str | None` on each leg), not re-stated — if ANY leg is SCOPED / NOT_RUN / QUALIFIED, the
  summary carries that bound and cannot render an unqualified PASS. (Same shape as CLAUDE.md's
  "render from typed applicability, never a name compared".)
- Pin the WHOLE receipt, not the line: on a receipt with a scoped leg, assert the joined output
  contains NO unqualified-pass token ("every claimed gate is GREEN", "CURRENCY : PASS").
- Control: honest line + over-claiming summary → RED; a genuinely-clean full run → unqualified PASS
  allowed. Covers G MP-3 (the #306/#312 false-clear reproduced at the summary).

### 9.4 Companion laws (fold in, don't skip)

- **Monoculture (P2):** any echoed/forwarded value uses ≥2 DISTINCT values and asserts
  `echoed == source` (G MP-5 — a hardcoded echo then cannot match). One value is a monoculture.
- **Entrypoint driven:** every ENTRYPOINT (`main`, a dispatcher) is invoked on its HAPPY path with a
  spy, asserting the EFFECT (exit code / routed call), never only the no-op refusal door (G MP-1). This
  is IDIOM 2 applied to the entrypoint.

### 9.5 Per-packet application table

| packet | findings | idioms to apply | the surviving build each closes | pkt-39 |
|---|---|---|---|---|
| **F** | #279 | IDIOM 1: ∀-drop over EVERY seam (LEG B) **+ a `_degrade` LIVE set-consistency pin** (LEG A — the missing backstop) | WB8 (BLOCKER), WB7 | — |
| **C** | #291/#347 | IDIOM 1: LEG B ∀ over the annotation surface (flip EACH constant / synthetic ∀); LEG A = C-9 equality pin already present | C-WB5 hybrid hardcode | helper consumed by 39 later (R2) |
| **G** | #344 | IDIOM 1 (mode×gate ∀ → MP-4; `main` routes-one-reader spy → MP-2) · IDIOM 2 (drive real `main`, assert exit → MP-1 BLOCKER) · IDIOM 3 (whole-receipt → MP-3) · Companion monoculture (→ MP-5) | W-main-noop, W-DRY-reparse, W-ruff, W-B, W-echo | — |
| **H** | #290 | IDIOM 1 SHARING specialization: delete-the-call mutation pin in `test_wrong_builds.py` + anti-dup pin | two-copies build (BLOCKER) | — |
| **D** | #295/#346 | IDIOM 2: wire spy (hand only the callable → proxy unrepresentable); build NOW | D-WB2 in-process | STRUCTURAL (registration gating) → 39; wire-spy built now |
| **E** | #289 | sufficient; IDIOM 1 door-field coverage OPTIONAL (operator ruling — honest bound) | — (residual only) | — |
| **A-SUB** | F4 | IDIOM 1: (LEG B) mutate shared `parse_production_trees` → EVERY adopter reddens, via **`_rebind_everywhere`** (by-identity, reaches from-imports) OR a `mutation_proof.py` receipt — NOT a single-module monkeypatch; (LEG A) DERIVED anti-dup scan (retry_seam offender shape) + import-is-USED pin + `_SCANNED_MEMBERS`-retired pin | fix-nothing (3 unused imports), `_MIGRATION_SET` hand-list, new-file clone, routing-not-sharing (§9.7) | — |
| **B** | #345 | IDIOM 1 slot-drive coverage (every AST slot driven; P-N per-site) extending P-U/P-F **+ Leg-2 made COMPREHENSION-AWARE** (element-wise containment: every vocab leaf under a `_CONTAIN_VERB`) **+ a `_SERVED_SAFE_FIELDS ∩ manifest-DOOR == ∅` pin** (mechanises Ruling 2) | Leg-2 comprehension-blindness false-flagging the Ruling-2-correct render; the forbidden `blocked_by`-SAFE escape (§9.7) | — |

**One line for the reviser:** for every mutation/coverage/liveness pin, re-derive the full surface LIVE
from production truth, assert the caller EQUALS it (LEG A / `assert_covers`), AND flip EACH member
asserting every caller reddens (LEG B), with the parametrized set pinned == the live surface. Where the
property is "X shares the ONE implementation," the flip is delete-the-call + an anti-dup pin. Where the
claim is "a wire/effect/entrypoint ran," spy the boundary (hand only the callable). Where a leg is
scoped, the summary must say so. The single-member proof was never cheaper — the members are few; it
was a habit, not a constraint.

### 9.6 REUSE MAP (operator: REUSE > RECREATE — the idioms already exist; generalise, don't invent)

Ground-truthed at HEAD `74694dc` + the in-flight (untracked) contracts. **The consistent pattern is a
GENERALISATION of existing in-repo symbols, not new machinery.** Per idiom: the existing symbol, its
home, and how each packet reuses it. I searched lore/grep for others beyond the four the lead named and
found THREE more (`_DECLARED_SITES`, `_all_sdk_call_sites`, the R16 wire-discipline scan) — listed.

**⚠ NAMING CORRECTION (supersedes earlier sections):** where §7/§9.1 say `assert_covers`, the REAL
coverage helper is **`_logging_fixtures.assert_scan_reached_every_member`** (pinned by the existing
A-SUB contract `loremaster/tests/test_ast_reach_helpers.py`) — reuse that exact symbol. AND it is
TREE-SCAN-scoped (oracle = pyproject members); non-tree surfaces (C annotations, F seams) do NOT route
through it — that would be over-consolidation (§7 ruling). They reuse the coverage *shape* (live
set-equality, both-direction diff) per-instrument. One policy per surface, not one function total.

| idiom | EXISTING symbol to reuse (home) | how each packet reuses / generalises it | shared home (import ONE) |
|---|---|---|---|
| **Coverage — tree scan (LEG A)** | `TestScanCoverage.test_the_scan_reaches_every_production_tree` (`test_anchored_pattern_seam.py`) → extracted as `parse_production_trees` + `assert_scan_reached_every_member` (`_logging_fixtures.py`), pinned by `test_ast_reach_helpers.py` | A-SUB adopters (anchored, secret_typing, comms_footer, backoff, secret_leak) IMPORT both from `_logging_fixtures`; migration proven by `TestTheMigrationSetRoutesThroughTheSharedHelpers` (static anti-private-clone) | **`loremaster/tests/_logging_fixtures.py`** |
| **Coverage — non-tree surface (LEG A)** | the SHAPE of `test_backoff_seam._DECLARED_SITES` (both-direction diff: `missing = declared − observed`, `undeclared = observed − declared`, fail-closed) | C (annotation surface — its C-9 equality pin already does this), F (`set(doors)==filter(core)` live), G (mode×gate) reuse the shape, recomputed LIVE each run — NOT the tree helper | per-instrument (shape reused, over-consolidation avoided) |
| **∀-MUTATION — in-test liveness (LEG B)** | `TestSharingProvenByMutation` + `_core_dropping` + `_rebind_everywhere` + the #194 landing assert + `_degrade_reflects_core_drop` (`test_store_seam_one_derivation.py`) | **GENERALISE `_core_dropping` ∀ over the surface** (the exact gap adversary-f/-cd found): F parametrises the drop over EVERY seam; C flips EACH annotation constant; A-SUB drops EACH adopter's parser. Mechanism differs per packet (drop-seam / flip-hint / mutate-parser) → NOT one function; the STRUCTURE + landing-assert + reflects-predicate are reused | `_rebind_everywhere` MAY promote to shared test-support IF ≥2 reuse it (builder judgment, prove by mutation); otherwise per-packet |
| **∀-MUTATION — scripts CLI receipt** | `scripts/mutation_proof.py` (anchor exact-1-match, declared node ids from `--collect-only`, BOTH-direction diff, #194 anchor-landing guard, content backup) | scripts-side packets (G/#344, H/#290, E/#289) reuse it for the CLI receipt form of the ∀ proof | **`scripts/mutation_proof.py`** (already shared) |
| **SHARING / call-site reach (the anti-dup tail)** | `test_retry_seam._all_sdk_call_sites` / `_unseamed_sdk_call_sites` (enumerate EVERY call site from the SDK truth; name OFFENDERS — "a call site no test executes is NAMED; coverage stops being a hidden variable") | H (#290) + G-MP2 + the anti-dup pins reuse this SHAPE: enumerate ALL call sites of the shared thing from truth, assert each routes — handles the 3rd-named-copy tail better than a 2-name check (closes C's R1 residual structurally) | per-instrument (shape reused) |
| **WIRE / EFFECT (IDIOM 2)** | `_auth_fixtures.WireSession` (SDK-driven REAL wire; `.call(name,args)` drives the wire, `.mcp` is "STRUCTURAL assertions ONLY — never to drive a posture claim") + the **R16 AST invariant** in `test_wire_discipline.py` (posture/refusal claims must drive the wire, not in-process `mcp.<handler>`) | D (#295/#346): drive the effect-helper via `WireSession.call`, and **bring the effect-helper UNDER `test_wire_discipline.py`'s existing R16 scan** — which MECHANICALLY forbids D-WB2's in-process door. Reuse the scan; do not invent a bespoke wire-spy. Strongest form (D R4): hand the helper only `WireSession.call`, so `.mcp` is unreachable | reuse `_auth_fixtures.WireSession` + extend `test_wire_discipline.py`'s scan reach to the effect-helper |
| **SUMMARY HONESTY (IDIOM 3)** | **none found** (searched lore + grep — no existing whole-receipt honesty pin) | genuinely new but small; base on the EXISTING typed-applicability principle (CLAUDE.md "render from typed applicability, never a name compared") — the summary reads per-leg `scoped`/`qualified` flags | new, in G's contract (`test_wave_gate.py`) |

**Net reuse ruling:** only IDIOM 3 (summary honesty) is genuinely new, and it is small and principle-backed. Everything else GENERALISES an existing symbol. The two mandatory shared homes are `_logging_fixtures.assert_scan_reached_every_member`/`parse_production_trees` (tree-scan coverage) and `scripts/mutation_proof.py` (scripts CLI receipt). The ∀-mutation MECHANISM and the non-tree set-equality stay per-instrument (shape reused, not one function) — consistent with the §7 over-consolidation ruling. `_rebind_everywhere` is the one candidate for promotion to shared test-support, gated on ≥2 real reusers + a mutation proof.

### 9.7 Fold of the 5th adversary (adversary-asub-b) — A-SUB + B confirmed one class

`REPORT-adversary-asub-b.md` (graded `405d321`) returned **both INSUFFICIENT, same class**, with three
reuse-relevant refinements. All 5 adversaries now agree; §9 covers all.

**A-SUB (F4) — confirmed IDIOM 1, with the sharing-mutation mechanism SHARPENED (reuse `_rebind_everywhere`):**
- **A-SUB-1/-3 (BLOCKER): the sharing proof has no RED home.** A "fix-nothing" build passes 16/0 with 3
  of 4 files "migrated" by an UNUSED `import … as _asub_route  # noqa: F401` — `test_secret_typing`'s
  `_SCANNED_MEMBERS` hand-list + THREE private `rglob` clones survive. **KEY REUSE REFINEMENT:** the
  contract's mutation used a single-module `monkeypatch.setattr(_logging_fixtures, …)`, which does NOT
  reach a **from-import** adopter (the adopter bound the function object locally). F's
  **`_rebind_everywhere`** (test_store_seam_one_derivation.py) rebinds BY IDENTITY across `sys.modules`,
  so it reaches from-import AND module-attribute adopters alike — it is exactly the tool this needs.
  **So: reuse `_rebind_everywhere` for the in-test ∀-mutation (verify it reaches from-imports as its
  construction implies), OR use a committed `scripts/mutation_proof.py` receipt (source-edit
  `parse_production_trees`→`{}`, declare each adopter's coverage node-id expected-RED, both-way diff).
  Either reaches from-imports; the single-module monkeypatch was the defect.** This VALIDATES the
  `_rebind_everywhere` promotion (now ≥2 reusers: F + A-SUB) — promote it to shared test-support,
  proven by mutation. It also DISSOLVES A-SUB-5: with a spelling-agnostic mutation, the routing pin
  need not mandate the `from`-import spelling (which pushed builders toward the monkeypatch-hostile
  form) — it just needs the import USED + the anti-dup scan + the ∀-mutation.
- **A-SUB-2 (BLOCKER): the §7 anti-dup structural pin was NOT built** — `_MIGRATION_SET` (4-file tuple)
  and the clone-check (anchored-only) are HAND-LISTS; a new-file whole-tree clone is invisible (planted
  one, 0 new failures). The contract justified dropping it as "the enumerate-the-forbidden antipattern";
  that justification is WRONG — *deny a hand-rolled parser OUTSIDE an evidence-backed allowlist* is
  **allowlist-the-safe** (the correct pattern, and §7 specified the allowlist). **Reuse the
  `test_retry_seam._all_sdk_call_sites`/`_unseamed_sdk_call_sites` offender-enumeration SHAPE** (§9.6):
  a DERIVED scan naming every hand-rolled `rglob("*.py")+ast.parse` outside the allowlist, fail-closed.
- **A-SUB-4:** add a pin that `_SCANNED_MEMBERS` (and any per-file member hand-list) is absent from the
  migrated files — the real consolidation, currently unpinned.
- SOUND, leave: the two helpers' behaviour pins (fail-closed on `{}`, oracle-independent) all discriminate.

**B (#345) — Ruling 2 CONFIRMED, and the contract's Leg-2 detector is the defect (not the code):**
- `blocked_by` **IS a forgery door** (Ruling 2 right) AND is **genuinely contained at HEAD** via
  `[render_attributed(b) for b in task.blocked_by]` (a hostile value does not `_leaks`). But **B-1
  (BLOCKER): Leg-2 is COMPREHENSION-BLIND** — it marks `contained=True` only for a DIRECT
  `render_attributed(...)` as the whole value expr, so it false-flags the correct comprehension and
  cannot distinguish it from a leaking `safe_str`/bare-repr. The ONLY way to green B is the
  Ruling-2-FORBIDDEN `blocked_by`-SAFE entry — a C-DEF trap AND a false clear reopening the mis-park
  class. **B is internally inconsistent (Ruling 2 blesses the render Leg-2 flags).** FIX: make
  `_served_slots` recognise ELEMENT-WISE / collection containment (every vocab-field leaf under a
  `_CONTAIN_VERB` — comprehension, `", ".join(...)` — is contained; a bare/`safe_str`/`sanitise_line`
  leaf is not), **reusing/extending the existing `test_link5` interpolation predicates — do not fork**.
  Then the correct render is GREEN and a `safe_str` revert is RED: the discriminating pin Ruling 2
  actually mandates, and `blocked_by` never needs allowlisting.
- **New pin (mechanises Ruling 2):** *no `_SERVED_SAFE_FIELDS` key is a manifest DOOR field in any
  model* — a checked-variable over the allowlist itself (IDIOM 1 applied to the allowlist), so the B-1
  escape hatch (park a door SAFE) cannot be taken silently.
- **B-2 (residual): the field-name-keying collision has a SECOND instance — `kind`** (DOOR
  `Finding`/`RecalledMemory`, SAFE `MemorySource`), currently moot (not served by a driven render) but
  the bound text names only `task_id`. This VALIDATES Ruling 3's quantifier concern; name `kind` in the
  bound (or add a `kind` control like `task_id`'s), re-open trigger = a render serves `MemorySource.kind`.
- **B-3 (residual, checklist):** Ruling 2's required comment-correction (server.py ~4631 "not
  live-forgeable") still has no home — served-English, no AST pin, so a builder/cold-audit checklist item.
- SOUND, leave: Leg-1 mis-park/vacuous-drive discrimination, the retirement superset proof, the hostile
  fixture — all verified discriminating.

**Design status: COMPLETE — 5/5 adversary verdicts, all one class, §9 (idioms + reuse map + this fold)
covers every packet.** The reviser applies §9.5/§9.6/§9.7 uniformly; only IDIOM 3 (summary honesty) is
net-new machinery.

---

## 10 — reviser-asub-b fork rulings (fable-designer-2, 2026-08-09)

Two design forks from `REPORT-reviser-asub-b.md` §"Decisions-needed", ruled with evidence at HEAD
`3b708e5` (branch `feat/surreal-unification`; index fresh, last sweep 2026-08-09T19:40Z). Plus #3
confirmed and recorded. Acceptance frame (operator priority): **DRY/ONE-IMPLEMENTATION > TRUST &
HONESTY (no false clears) > don't-widen-gaps > don't-repeat.** Security de-prioritized; a served
forgery door is a TRUST issue regardless. Ruled in the same evidence style as §8. Cite symbols;
line numbers are secondary (stale-prone).

### Ruling (4) — fleet-row `task_id` is a forgery DOOR, un-contained TODAY: a LIVE production fix this session

**DECISION: DOOR — the SAME class as §8 Ruling 2 (`blocked_by`), and it is a LIVE leak, not a
contained-already regression-pin.** `render_attributed` containment is REQUIRED in production this
session; a revert to `safe_str`/bare must go RED.

**Evidence (HEAD):**
- **Provenance — `Agent.task_id` is UNCONSTRAINED CALLER FREE TEXT, not a system id.**
  `loremaster.agents.AgentRegistry.register` stores the caller's `task_id: str | None` **VERBATIM**
  into `_COL_TASK_ID` — `CREATE … CONTENT` on first register, `UPDATE … SET` on re-register — with
  **no charset check, no task-id-shape validation, no length bound.** Same provenance class as
  `blocked_by` (§8 R2: "UNCONSTRAINED caller strings at the boundary"). The tool description ("the
  fleet task id this agent is currently working") is advisory INTENT, not a validated constraint.
- **The manifest's OWN sibling entry corroborates and already documents the mis-classification.**
  `test_link5_render_containment.py::_manifest` classifies `InboxEntry.task_id` as a **DOOR** with the
  note: *"task_id is caller FREE TEXT (messages.py:865-871 bounds task_id by LENGTH only — 'a LABEL,
  not content', no charset gate) … **Was MIS-CLASSIFIED 'task-id ref'** — the sibling leak Fable named
  (directive #4020)."* That correction was applied to InboxEntry but **NOT** to its two siblings:
  `Agent` (`safe={…"task_id"}`, reason *"task-id ref … a system id"*) and `Message`
  (`safe={…"task_id"}`, reason *"task-id ref"*) still carry the FALSE reason. Agent is the LIVE
  sibling; Message is latent.
- **Render TODAY — un-contained.** `AppContext._render_comms_fleet_row` serves it via
  `safe_str(row.task_id[:8] + "…")`. `safe_str` = `sanitise_line(str(x))`: collapses
  control/newline/bidi/zero-width to one line but is **SAME-LINE-FORGERY-BLIND** (printable ` · `
  U+00B7 survives). Fleet cells are `" · "`-joined, so an 8-char caller `task_id` like `"x · abcd"`
  renders `task x · abcd…` — a PHANTOM cell boundary reading as lore's own structural voice. Small
  (8-char truncation caps forged content; `safe_str` kills newlines → same-line only) but genuine.
- **The codebase's OWN convention is `render_attributed` for `task_id` at 4 of 5 sites:**
  `server.py` supersede/blocked notices (`render_attributed(task_id)`), `_render_task_story`
  (`render_attributed(story.task_id)`), and the drain-inbox context (`render_attributed(entry.task_id)`).
  `_render_story_message` deliberately does **not** render task_id. The fleet row is the LONE
  `safe_str` outlier — precisely because the manifest mis-parked `Agent.task_id` SAFE, so `_forge`
  **HARDCODES `task_id=None`** in the Agent forge (the literal #345 artifact) and the slot is never
  driven with a forgery. **This is #345 exactly, one model over.**

**RULING — three coupled fixes (owned by the B/#345 cycle; its server.py scope was already required
for the #345 recovery):**
1. **PRODUCTION FIX (live):** `_render_comms_fleet_row`'s task cell →
   `render_join(" ", [safe_str("task"), render_attributed(row.task_id[:8] + "…")])`. Preserves the
   truncated display, contains the forgery, and is drop-in consistent with the `role`/`model`/`note`
   cells in the same method (`render_join` already accepts `[SafeLine, Rendered]` there).
2. **MANIFEST CORRECTION:** move `task_id` from `safe`→`door` in `_manifest`'s **Agent** and
   **Message** entries, replacing the false "system id / task-id ref" reason with the true "caller
   free text (register / send store verbatim; length-bounded only) — was mis-classified 'task-id
   ref'", mirroring the InboxEntry entry. (Message.task_id is NOT served in a driven render, so its
   correction is latent-honesty like `kind` — still a door by provenance.)
3. **REGRESSION PINS (already in the B contract):** with drive-all-slots (§8 R3(a)) driving
   `Agent.task_id` with a forgery, Leg-2/P-N reddens a `safe_str`/bare revert of the render; the
   mis-park pin (`_SERVED_SAFE_FIELDS ∩ manifest-DOOR == ∅`) forbids silencing it by re-SAFE-listing
   `task_id`. **Both escape routes closed → mutation-proven.**

**Severity / frame:** LIVE but low-blast (8-char truncation + same-line only). Per operator priority
#2 (trust/no false clears) and §8 R2's frame — containment of caller text in a served surface is a
TRUST property, not a security-sized one — it is fixed this session. Not deferred (don't-kick-the-can:
the fix is loaded, in scope, and rides a cycle that already touches server.py).

### Ruling (5) — KEYING: field-name keying CONFIRMED sound; the collision is PROTECTIVE, not disqualifying

The brief's test: field-name keying is sound only if EVERY model serving that name contains it the
same way; if `task_id` is a DOOR in one model and SAFE in another **served** render, it is UNSOUND →
(model,field).

**FINDING: the antecedent "SAFE in another SERVED render" is FALSE.** `task_id` is caller free text
(a DOOR) in **every** model that carries it — Agent (register, verbatim), Message and InboxEntry (send,
length-bounded only). The Agent/Message SAFE labels are **MIS-PARKS** (the "system id" reason is
false — see Ruling 4), not a genuine safe instance; and Message.task_id is not served in a driven
render at all. Once corrected (Ruling 4.2), `task_id` is a door everywhere → the field-name condition
is satisfied by construction (4 of 5 renders already contain via `render_attributed`; the fix makes
it uniform).

**RULING: field-name keying CONFIRMED (consistent with §8 R3; this is its first LIVE test and it
holds). Do NOT move to (model,field).** Rationale — field-name keying is STRICTLY SAFER here, not
merely DRY-er:
- **It makes the mis-park UNREPRESENTABLE.** `_SERVED_SAFE_FIELDS ∩ door == ∅` means a name that is a
  door in ANY model can never be SAFE-listed → every render serving it MUST contain it (or be driven
  with a forgery and pass P-N — which, for a truncated caller string, is `render_attributed`). **The
  remedy for a collision is CONTAIN-everywhere; containment on a genuinely-opaque value is harmless**
  (§8 R2: "render_attributed on a truncated id is harmless").
- **(model,field) keying would REGRESS.** It reverses §8 R3's DRY decision AND re-permits SAFE-listing
  `Agent.task_id` while `InboxEntry.task_id` stays a door — i.e. it makes the #345 mis-park
  REPRESENTABLE again, one model over. It "resolves" the collision by re-opening the exact class this
  session exists to close. **Rejected.**
- **The quantifier risk field-name keying otherwise carries** ("safe in the site I examined, asserted
  over all sites") is covered by §8 R3's drive-all + P-N backstop, exactly as ruled — no need to
  multiply entries into (method,field).

**Net: field-name keying stands; the escape valve for a door-name collision is CONTAIN, never
SPLIT-AND-SAFE-LIST.** (B-2's `kind` collision, currently moot, is governed by the same rule: if
`MemorySource.kind` ever gets a driven render, it is contained, not (model,field)-split.)

### Ruling (6) — comms_footer scope: a DESIGN classification (RULED), NOT an operator scope-grant

**TRIAGE: this is DESIGN, and I rule it — no operator escalation.** §7 (adopter table), §9.6 (reuse
map), and §8 Ruling 1 (per-adopter behaviour-preservation) ALREADY classify `test_comms_footer` as a
`parse_production_trees` adopter. §5's A-SUB writable-set table merely **OMITS** the file — a clerical
inconsistency with §7/§8, not a deliberate exclusion. Correcting it is design-consistency, squarely
within the DRY-consolidation scope the operator prioritized (#1). It is NOT a fenced closed-contract
file (unlike `test_blocks_edge.py` / F5), so it needs no separate sequenced cycle — the migration is
behaviour-preserving and A-SUB's own cold audit re-runs the migrated suite + the mutation proof.

**Evidence (HEAD) — comms_footer has TWO whole-tree scans with the clone signature, and the second is
itself an instance of THIS CLASS:**
- **Scan A** (`test_comms_footer.py`, the link-N footer reach, ~2958-2982): iterates
  `_workspace_scan_roots(root)` (DERIVED from pyproject `[tool.uv.workspace] members` via a regex
  reader) × `rglob("*.py")`, scanning **PRODUCTION AND TESTS** (its docstring says so). →
  `parse_production_trees(include_tests=True)`.
- **Scan B** (~3144-3165): iterates a **HARDCODED 4-tuple** `("loremaster/loremaster", "lorerunes",
  "loresigil", "lorescribe")` × `rglob("*.py")`, **PRODUCTION ONLY**. →
  `parse_production_trees(include_tests=False)` — **AND this migration RETIRES A MEMBER HAND-LIST that
  is itself an instance of the reach-is-a-hidden-constant class** (a 5th workspace member added to
  pyproject is silently missed, #291-shape). §7 named only Scan A ("regex member-reader"); **Scan B is
  an ADDITIONAL adopter surfaced here** — migrating it is a bonus consolidation the DRY priority wants.

**RULING:**
1. **`test_comms_footer.py` IS in the A-SUB builder's writable set** — remove the reviser's
   provisional allowlist entry (the dead-entry pin then forces migration). The lead reflects this
   one-line writable-set addition in the A-SUB brief. It stays WITHIN the A-SUB cycle.
2. **BOTH scans migrate**, with DIFFERENT `include_tests` (A: True; B: False), each pinned to its
   EXACT pre/post scanned-file-set per §8 Ruling 1. Scan B additionally retires its hardcoded member
   tuple (consolidated onto the derived member roots).
3. **⚠ Behaviour-preservation HAZARD the builder must HONOUR, not assume** (this is §8 R1's
   root-kind subtlety, live here): comms_footer's own `_workspace_scan_roots` yields the **workspace
   MEMBER dirs** (e.g. `loremaster/`, which INCLUDES `loremaster/tests`), whereas
   `_logging_fixtures.workspace_roots` yields the `<member>/<member>` **PACKAGE roots** (which
   structurally EXCLUDE `<member>/tests`). So `parse_production_trees(include_tests=True)` MUST re-add
   `<member>/tests` for member roots, or Scan A's reach **NARROWS** (drops every member-test file it
   scans today) — a widened gap (priority #3) wearing consolidation's clothes. The per-scan
   scanned-set-equality pin is MANDATORY, not optional, and is the instrument that catches this.

### #3 (confirmed, recorded) — `_rebind_everywhere` promotion APPROVED by the lead

`_rebind_everywhere` (from `test_store_seam_one_derivation.py`) promotes to shared test-support in
`_logging_fixtures.py` — ≥2 real reusers (F/#279 + A-SUB/F4), DRY #1. Already the design of record:
§9.6 named it "the one candidate for promotion … gated on ≥2 real reusers + a mutation proof"; §9.7
A-SUB-1/-3 "VALIDATES the promotion". The builder that lands first (A-SUB or F) does the promotion and
proves SHARING by mutation (change the shared rebind → BOTH F's and A-SUB's ∀-mutation pins redden;
a caller that stays green is a private copy). The reviser's accessor `_rebind_everywhere_fn()` already
checks `_logging_fixtures` first, so it is promotion-tolerant.

### Builder tasks these force (for the lead to route — no operator escalation, no store/schema/DDL)
- **B/#345 cycle:** the 3 coupled fixes in Ruling 4 (server.py fleet-row containment + Agent/Message
  manifest correction + confirm the regression pins). server.py in the B writable set (already
  required by the #345 recovery).
- **A-SUB cycle:** add `test_comms_footer.py` to the writable set; migrate BOTH scans (Ruling 6,
  retiring Scan B's hand-list); promote `_rebind_everywhere` (#3).

**Fork status: BOTH ruled at design (no operator scope-grant needed). Only lead action: reflect the
two writable-set additions (server.py already in B; test_comms_footer.py into A-SUB) in the briefs.**

## §11 — G summary-honesty structural redesign (fable-designer-3, 2026-08-09)

**Escalation, not a fix wave.** The G (#344) summary-honesty sub-instrument (IDIOM 3, §9.3)
has had its class survive THREE rounds — round 1 a 2-token deny-list (`W-summary-alt`
defeated it with alternate wording), round 2/3 a positive-marker check whose reach is
`test_wave_gate._summary_line` = the LAST PASS/FAIL line only (`W-summary-double` defeated it
with an over-claim on a NON-last verdict line), and a standing residual `W-summary-inline`
(marker + over-claim on the SAME line) defeats even a per-verdict-line marker allowlist.
Receipts: `REPORT-delta-adversary-g-2.md` (MP-9 + W-summary-double + W-summary-inline),
`REPORT-delta-adversary-g.md` (the round-1 deny-list survivor MP-7). The lead's-own-tell has
fired ("same class survives 2 waves → escalate the DESIGN, don't brief a 3rd fix"), so §11
redesigns the property so the defect is **unrepresentable by construction** rather than
patched a fourth time. Read at `wave_gate.py` ABSENT (RED contract) · `scripts/test_wave_gate.py`
uncommitted (`M`) · HEAD `14b62f2`.

### §11.1 — Root cause: string-level honesty IS enumerate-the-forbidden

All three survivors share ONE mechanism, and it is CLAUDE.md's meta-lesson reproduced inside
the fix for the finding about exactly this: **every round treated the summary as a `str` a
builder APPENDS to `lines: list[str]`, then INSPECTED THE STRING.** String inspection of a
builder-authored, open-vocabulary, per-call line is inherently an enumeration of shapes —
forbidden (deny-list) or safe (marker allowlist) — and the forbidden/safe *shape* set over
free text is unbounded, so an adversary always finds an uninspected line (`double`), an
unenumerated wording (`alt`), or a line carrying both marker and lie (`inline`). The reach of
the guard is a hidden constant (`the last line`, `these two tokens`, `each verdict line`) — the
7th-defeat shape, keyed on a string property instead of a checked variable.

The lie lives in the **gap between the typed verdict the machinery COMPUTED and the free text a
builder WROTE beside it**. `pending_contract_gate._render_currency` computes `ok` from typed
per-gate `GateCurrency` values, then hand-appends `"CURRENCY   : PASS — every claimed gate is
GREEN or OWNED"` as free text. A DRY-faithful wave build inherits that unqualified line (blind
to SCOPED, because the machinery computes its verdict from `results`, which shows the scoped
pytest subset as green) and appends an honest banner — that is `W-summary-double`, born from
the free-text seam, not from any wording choice.

**The move: lift the honesty property from the STRING level to the TYPE level.** At the type
level "unqualified pass" is a SINGLE closed enum value and "is this leg qualified" is a typed
flag — the SAFE set is small, closed and enumerable (allowlist-the-safe / enforce-at-
construction, exactly the operator frame), and a biconditional over a finite typed domain is
∀-checkable where an open-text shape-scan is not. This is CLAUDE.md's "render from typed
applicability, never a name compared" and "prose DERIVED from behaviour, not restated beside
it," applied to the summary.

### §11.2 — The redesigned property (typed verdict + sole minter)

Introduce a closed summary-verdict type and two pure functions, and make the rendered summary
string a pure function of the typed verdict — never a value a caller authors.

1. **`SummaryVerdict` — a closed enum, the summary's typed applicability.** The MINIMAL surface
   that preserves checkpoint behaviour byte-for-byte and adds the one new state SCOPED:
   - `PASS_FULL` — every leg ran full; any reds all OWNED. The **only** value whose render
     carries the unqualified currency-clear token ("every claimed gate is GREEN or OWNED").
     Maps byte-exact to today's `_render_currency` PASS line (extraction, not a behaviour change).
   - `PASS_SCOPED` — ok for what ran, but ≥1 leg ran a subset (wave pytest) → a full run is
     OWED. The wave qualified pass.
   - `FAIL` — ≥1 leg RED_ORPHANED / NOT_RUN. Maps byte-exact to today's FAIL line.

   (`PASS_FULL` collapses today's GREEN-or-OWNED pass — the checkpoint summary already names
   OWNED honestly, so CLEAN vs OWNED need not split for #344; the lie is *only* SCOPED. A later
   packet may split OWNED out, but §11 keeps the enum minimal so the production extraction is
   behaviour-preserving.)

2. **`summary_verdict(leg_quals: Sequence[LegQualification]) -> SummaryVerdict` — a pure, TOTAL
   function of the typed per-leg states.** The biconditional it must satisfy:
   - `FAIL`        iff any leg is FAILING (orphaned / not-run);
   - else `PASS_SCOPED` iff any leg is SCOPED;
   - else `PASS_FULL`.
   So **`PASS_FULL` is unreachable whenever any leg is SCOPED** — over-claim is excluded in the
   RETURN VALUE, before any string exists. `LegQualification` is a closed enum
   `{CLEAN, OWNED, SCOPED, FAILING}` DERIVED from each gate's existing `GateCurrency.verdict`
   plus a `scoped: bool` (see §11.3) — reuse the per-gate typed applicability that already
   exists; do not re-derive it from names.

3. **`render_summary(verdict: SummaryVerdict) -> SummaryLine` — the SOLE minter of a summary
   string, a total mapping enum → fixed string.** Only `PASS_FULL` maps to a string containing
   the unqualified-pass token; `PASS_SCOPED`/`FAIL` map to strings that carry their bound. The
   wording is FIXED here (one canonical string per enum value), never chosen per call — so
   "alternate wording" is not a degree of freedom a wrong build has.

4. **The receipt is a TYPED value, not a `list[str]` a builder assembles.** `render_wave_receipt`
   returns (or internally builds) a frozen `WaveReceipt(leg_lines: tuple[str, ...], verdict:
   SummaryVerdict)` whose `.ok` and `.summary_line` are DERIVED (`.ok = verdict is not FAIL`;
   `.summary_line = render_summary(verdict)`). The public `-> tuple[list[str], bool]` seam is
   `(receipt.render(), receipt.ok)` where `render()` is `[*leg_lines, str(summary_line),
   _NOT_DEPLOY_NOTE]`. **There is no free-text summary-append seam left** — the summary slot is
   typed and filled only by the sole minter, and `.ok`/summary share the one `verdict` so they
   can never disagree (this also strengthens the MP-6 `main-exit == renderer-ok` pin).

5. **`SummaryLine` — a `Rendered`-style provenance type (REUSE, do not invent).** Mirror
   `loremaster.render.Rendered` (a `str` subclass "PROVEN to have been assembled ONLY via" the
   sanctioned mint verbs, enforced by the `test_render_seam_pins.TestSafeLineRenderedMintPin` AST
   scan that fails if the constructor appears anywhere else in production). Make `SummaryLine` a
   `str` subclass minted ONLY by `render_summary`; a `pytest`-time AST scan over `wave_gate.py`
   (+ the extracted seam) fails if `SummaryLine(...)`/`cast` appears anywhere else, AND if the
   unqualified-pass token literal appears anywhere outside `render_summary`'s canonical mapping.
   That AST scan is the enforce-at-construction backstop, the SAME idiom the render package
   already ships and pins.

**DRY #1 — one implementation, both modes.** `summary_verdict` + `render_summary` live in
`pending_contract_gate.py` (the shared home — the summary logic already lives there) and are
consumed by BOTH `_render_currency` (checkpoint; every leg `scoped=False`) and
`render_wave_receipt` (wave; pytest leg `scoped=True`). Checkpoint can reach PASS_FULL; wave
with a scoped pytest leg **cannot**. One summary policy, called twice — never a pattern cloned
(§9.6 IDIOM 3 row said this is "genuinely new but small … the summary reads per-leg
scoped/qualified flags"; §11 is that, made structural).

### §11.3 — Production-design change (the fork, answered)

**YES — this forces a small, behaviour-preserving change to shipped production code
(`scripts/pending_contract_gate.py`), and that is the DRY-correct answer, not an accident.**
The only shipped code is `pending_contract_gate.py` (`wave_gate.py` does not yet exist). Two
options; the frame (DRY #1) decides:

- **Option A (RECOMMENDED) — extract the summary into a shared typed seam.** Pull the inline
  PASS/FAIL logic at the tail of `_render_currency` into `summary_verdict` + `render_summary`
  (+ `SummaryVerdict`/`SummaryLine`), and have `_render_currency` compute a `LegQualification`
  per gate (all `scoped=False`) and call them. `wave_gate` calls the SAME seam with the pytest
  leg `scoped=True`. Behaviour-preserving for checkpoint (pinned below); the one new state is
  SCOPED. This is the ONE-IMPLEMENTATION fix — the summary computed once, consumed twice.
- **Option B (REJECTED) — `wave_gate` re-implements currency rendering** so `pending_contract_
  gate.py` is untouched. This CLONES the summary policy into a second module — the exact §9.1
  SHARING / #102 two-copies defect, and forbidden by the acceptance frame (DRY #1).

The `scoped: bool` per leg: wave_gate derives it from the reader identity (the JUnit reader =
the scopable leg, exactly as `test_scopable_gate_identified_by_reader_not_literal_id` already
requires — DERIVED, not keyed on `id == "pytest"`) ∧ `mode == MODE_WAVE`. It does NOT go onto
`GateCurrency` (which "deliberately carries NO is_deploy_receipt field" — keep its
currency-vs-deploy separation; carry `scoped` in the new `LegQualification`/`WaveReceipt`
surface instead).

**Behaviour-preservation guard (the removed-behavior inventory, per the delete/replace law).**
The extraction MUST reproduce today's checkpoint summary byte-for-byte. Pin it with an
oracle-equality control: the pre-extraction `_render_currency` output over {all-clean,
one-owned, one-orphaned, one-not-run} equals the post-extraction output, byte-exact — and the
EXISTING `test_pending_contract_gate.py` suite (which certifies the OLD world) must stay green
unchanged. That is the "tests written before a semantic change certify the OLD world" law
working FOR us: it is the anti-regression net for the extraction.

### §11.4 — How the CONTRACT pins the structural property (no forbidden-shape scan)

Four pins; the first three are typed/structural (they force the form and never inspect an
open-vocabulary string), the fourth is a biconditional belt keyed to the sole minter.

- **P1 — `summary_verdict` is a pure total function, ∀ over the per-leg-flag combination
  surface.** Parametrize over the FULL Cartesian product of `LegQualification` across the legs
  (the surface DERIVED from `LegQualification.__members__` × the manifest leg count — NOT a
  hand-list), and assert `summary_verdict(combo)` equals the spec'd biconditional
  (`PASS_FULL` ⟺ no leg SCOPED ∧ no leg FAILING; `PASS_SCOPED` ⟺ ≥1 SCOPED ∧ 0 FAILING;
  `FAIL` ⟺ ≥1 FAILING). Typed in, typed out — **no string is read.** Coverage-as-checked-
  variable: a meta-recursion pin asserts the parametrized combination set EQUALS
  `LegQualification.__members__`-derived surface (mirror the existing
  `test_enforcement_matrix_covers_every_mode_gate_and_failure_mode` +
  `_canonical_manifest_ids` idiom) — add a qualification state and the ∀ grows or the coverage
  pin reddens. This is the "∀ over the per-leg-flag combination surface asserting the summary
  verdict is a deterministic function of the flags" mechanism.

- **P2 — `render_summary` is the sole minter, mutation-pinned (the summary TYPE cannot carry an
  unqualified token when scoped).** Assert `PASS_FULL` is the ONLY enum value whose render
  contains the unqualified-pass token and `PASS_SCOPED`/`FAIL` do not; then MUTATE the
  `PASS_FULL` string's marker and assert the pin moves (proves the string is DERIVED from the
  enum in one place). Plus the `Rendered`-style AST mint-scan (§11.2.5): `SummaryLine(...)` and
  the unqualified-pass token literal appear NOWHERE outside `render_summary`. Together: the only
  reachable unqualified-token string is `render_summary(PASS_FULL)`, and P1 makes `PASS_FULL`
  unreachable while scoped. This is the "summary type that cannot carry an unqualified-pass
  token when a flag is scoped" mechanism.

- **P3 — prove-sharing-by-mutation (DRY #1 / §9.1 SHARING specialization).** Mutate the shared
  seam (`render_summary`'s output, or `summary_verdict`'s scoped branch) via
  `_rebind_everywhere`-by-identity or a `scripts/mutation_proof.py` receipt, and assert BOTH
  `_render_currency`'s AND `render_wave_receipt`'s summaries move. A caller that hand-authors a
  summary (any wording, any line) stays green under the mutation → RED. **This pin never reads
  the wrong build's wording; it asks whether the summary is DERIVED from the shared minter.**

- **P4 — receipt biconditional belt, ∀ over the flag surface.** For every leg-qualification
  combination, render the WHOLE receipt (both modes) and assert the count of unqualified-pass-
  token lines == (1 iff `verdict is PASS_FULL` else 0). This is allowlist-the-safe (token IFF
  PASS_FULL), NOT a forbidden-token deny-list, and it is keyed to the sole minter's fixed
  string (mutation-pinned by P2), so it is a property of a finite closed mapping, not a scan of
  open text. It is the belt that reddens if any build forges a token line despite P1–P3.

The contract keeps a **positive control** (a genuinely clean FULL checkpoint renders PASS_FULL
with the unqualified token — this is an honesty check, not a blanket ban) and a **satisfiability
receipt** (a known-correct reference build goes 0-failed, incl. the byte-exact checkpoint
oracle). `test_wave_gate._summary_line` (the last-PASS/FAIL-line reach, the round-2/3 hidden
constant) is RETIRED — the property no longer depends on which line the token lands on.

### §11.5 — How each of the three survivors dies BY CONSTRUCTION

- **`W-summary-alt` (alternate wording, "all gates are clean, tree is green").** To exist it
  must author a summary string instead of routing through the sole minter. **Dies at P3**
  (prove-sharing-by-mutation): its hand-authored string does not move when `render_summary` is
  mutated → RED. The pin never inspects "clean/green/tree" — it inspects derivation.
  Unrepresentable: any summary not minted by `render_summary` fails the DRY mutation, whatever
  words it picks.

- **`W-summary-double` (unqualified pass on a non-last line + honest banner last).** Under the
  redesign the shared summary consumes the SCOPED pytest leg → `summary_verdict` returns
  PASS_SCOPED → NO PASS_FULL line is ever emitted for a wave receipt; there is nothing to
  inherit. To reproduce double the builder must forge a PASS_FULL line — **dies at P2/P3** (a
  forged line isn't minted by `render_summary`; the AST mint-scan forbids the token literal
  outside the minter) AND **at P4** (verdict is PASS_SCOPED ⟹ 0 token lines expected; double
  has 1 → RED). Unrepresentable: PASS_FULL is unreachable while pytest is scoped, and the token
  string exists nowhere but the minter.

- **`W-summary-inline` (marker + over-claim on ONE line).** The summary line is
  `render_summary(PASS_SCOPED)` — a FIXED string; the builder cannot compose "marker +
  over-claim" because it does not author the line. **Dies at P2** (an inline hand-authored line
  is not `render_summary`'s output; the token literal is forbidden outside the minter) and **at
  P4** (PASS_SCOPED ⟹ 0 token lines; the inline line carries the token → RED). Unrepresentable:
  there is no per-call free-text seam to compose marker+lie into.

The common death: the redesign **removes the free-text summary seam** and replaces it with
`(typed leg quals) → summary_verdict → SummaryVerdict → render_summary → SummaryLine`. All
three survivors require a free-text-authoring seam that no longer exists, and the contract pins
the pure functions (P1/P2), the routing (P3), and a biconditional belt (P4) — none of which is
a forbidden-shape scan.

### §11.6 — Reuse map / DRY (Packages considered)

- **`GateCurrency`** (`pending_contract_gate.py`) — reuse the per-gate typed applicability;
  derive `LegQualification` from its `verdict` + a `scoped` flag. Do not perturb its
  currency-vs-deploy field separation.
- **`_render_currency` summary logic** — EXTRACT (not clone) into `summary_verdict` +
  `render_summary`; the shared home is `pending_contract_gate.py`. DRY #1.
- **`loremaster.render.Rendered` / `SafeLine`** (`render.py`, pinned by
  `test_render_seam_pins.TestSafeLineRenderedMintPin`) — reuse the provenance-type + AST
  mint-scan idiom for `SummaryLine`. Genuinely the same pattern; do not invent a bespoke one.
- **Meta-recursion coverage idiom** (`test_enforcement_matrix_covers_...`,
  `_canonical_manifest_ids`, `_FAIL_MATRIX_GATES` in `test_wave_gate.py`) — reuse the shape for
  the P1 flag-surface coverage-as-checked-variable.
- **`scripts/mutation_proof.py`** + **`_rebind_everywhere`** — reuse for the P2/P3 mutation
  receipts (the §9.6 "scripts CLI receipt" + "in-test liveness" rows).
- **Packages considered:** stdlib `enum` only (`SummaryVerdict`/`LegQualification`); `str`
  subclass for `SummaryLine` (mirrors `Rendered`). No external dependency — the mechanism is a
  typed enum + a sole minter, which no library supplies. Verdict: **bespoke (minimal), reusing
  four in-repo idioms.**

### §11.7 — Recommendation & routing

- **This is a CONTRACT + PRODUCTION-DESIGN change, not a builder patch.** It changes G's contract
  surface (`render_wave_receipt` gains a typed receipt / the summary is minted, not appended) and
  makes a small behaviour-preserving extraction in `pending_contract_gate.py`. Route it through
  the standing order: **contract → adversary → build → cold audit** (a fix wave is exactly where
  the adversary is cheapest and most needed — operator, 2026-07-28). The reviser writes the
  contract to §11.4's four pins; the contract-adversary re-attacks with `W-summary-alt/double/
  inline` (all three MUST be caught) plus a NEW hybrid: a build that routes `_render_currency`
  through the shared minter but hand-rolls `render_wave_receipt`'s summary (the §9.1 routing-not-
  sharing shape) — P3 must catch it.
- **Operator fork (writable set):** the fix touches shipped `scripts/pending_contract_gate.py`
  (a production-code change, per the escalation trigger "production-touching surprise"). The
  extraction is behaviour-preserving and guarded by the existing `test_pending_contract_gate.py`
  + a byte-exact oracle, but it is still a change to the #306/#312 enforcement surface — flag it
  for the operator/lead to confirm `pending_contract_gate.py` enters G's writable set, rather
  than deciding it unilaterally.
- **Named re-open trigger:** if a future packet splits OWNED out of `PASS_FULL` (a distinct
  `PASS_OWNED` qualified pass), the P1 biconditional and P2 token mapping grow by one enum value
  — the coverage pin reddens until the ∀ is extended, which is the mechanism working as intended.

## §12 — A-SUB anti-dup: un-defeatable-by-spelling (fable-sidecar, 2026-08-09)

**Escalation, not a fix wave** — same posture as §11, one packet over. `REPORT-delta-adversary-asub-b.md`
found A-SUB still INSUFFICIENT (1 BLOCKER: A-SUB-3 sharing NOT actually closed), and it is G's §11
class reproduced one file over: **enumerate-the-forbidden-by-SPELLING.** The lead's-own-tell has fired
(the class survived the §9.7 patch), so §12 redesigns the property so the survivor is *unrepresentable
by construction*, not patched a 4th spelling later. Ruled at HEAD `e36c114` (branch
`feat/surreal-unification`; index fresh, last sweep 2026-08-09T13:11Z). Cite symbols; line numbers are
stale-prone. **Scope: TEST-ONLY, within the A-SUB cycle's existing writable set
(`test_ast_reach_helpers.py`, `_logging_fixtures.py`, the migrated files); NO production / store /
schema / DDL; reuses an already-shipped in-repo pattern. NO operator scope-grant needed — this is
design within the delegated authority (I flag: none of §12 requires one).**

### §12.1 — Root cause: EVERY A-SUB anti-dup pin observes a PROXY, not the effect

The survivor (reproduced in scratch by the delta-adversary) is a routing-not-sharing build with two
cooperating parts: **(1)** a PRIVATE whole-tree derivation via `production_sources()`/`workspace_roots()`
+ `ast.parse` (NO `rglob`) doing the REAL 113-key work, and **(2)** an UNCONSUMED nullary decoy that
calls `parse_production_trees` purely to satisfy the used-ness/∀ reach. All three guards pass because
each is keyed on a PROXY, and I verified each proxy at HEAD:

- **Offender scan** (`TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist`, via
  `_whole_tree_clone_offenders`/`_has_tree_parser_clone`) — proxy = **the `rglob("*.py")+ast.parse+
  read_text` SPELLING**. Its own positive control (`test_a_planted_clone_in_a_fresh_file_would_be_caught`)
  plants exactly that spelling, so a `production_sources()`+`ast.parse` derivation is invisible.
- **∀-mutation reach** (`TestSharingProvenByMutation`, via `_live_adopters`) — proxy = **"a call to
  `parse_production_trees` EXISTS"**. The decoy is a call, so it makes the file a "live adopter"; the
  ∀-drop then reddens something on the DECOY path while the private scan's real consumer stays green.
- **Used-ness** — proxy = **the import is used** (a call binds it). The decoy binds it.

This is exactly §11.1's diagnosis, one primitive over: string-inspection of an open-vocabulary artifact
IS enumerate-the-forbidden. Here the "open vocabulary" is *the ways to spell a whole-tree parse*
(`rglob` / `os.walk` / `glob` / `Path.iterdir` / a comprehension / `production_sources`+`ast.parse` /
a hardcoded root tuple), and *the ways to fake consumption* (a decoy call). Both sets are unbounded,
so a spelling/decoy always escapes. **The reach of each guard is a hidden constant** (`the rglob
spelling`, `a call exists`) — the 7th-defeat shape.

### §12.2 — The move: observe the parse PRIMITIVE and the real EFFECT, never the spelling

Same lift as §11 (string→type): stop inspecting the open-vocabulary artifact; observe the property at
a chokepoint where the vocabulary collapses to one. Two properties, two chokepoints — **and the repo
already ships the proven template for both at `test_retry_seam.py::TestNoSdkCallEscapesTheDriverAtRuntime`,
which pairs a weak-but-total LINT with an absolute-over-executed-code RUNTIME gate.** A-SUB today has
only the (mis-built, spelling-keyed) LINT half and is missing the runtime half. §12 gives A-SUB the
same two-layer shape, applied to the tree-parser instead of the SDK connection.

**RULING on "AST-allowlist vs runtime — which is un-defeatable here": the RUNTIME chokepoint is the
un-defeatable form; an AST-allowlist alone is REJECTED for this surface.** Rationale, from
CLAUDE.md's instrument-lesson ladder:
1. **Allowlist-the-safe, not enumerate-the-forbidden.** The SAFE set is ONE name — *the only sanctioned
   whole-tree parser is `_logging_fixtures.parse_production_trees`*. Everything else that produces an
   AST across the workspace trees is an offender. (The current scan already claims allowlist-the-safe
   in its docstring but implements enumerate-the-forbidden: it keys on the `rglob` spelling, so its
   "offender set" is really "the one spelling I listed".)
2. **An AST allowlist cannot make "produces a whole-tree parse" crisp.** Two spelling-variable parts —
   the roots-source (rglob / os.walk / `production_sources` / a hardcoded tuple — comms_footer Scan B
   used a hardcoded tuple) AND the parse call (`ast.parse` / `compile(…PyCF_ONLY_AST)` / an alias
   `ap = ast.parse; ap(…)`). Keying the AST scan on the parse PRIMITIVE (better than keying on the
   loop) is still alias-defeatable — `test_retry_seam` says this in its own words: the runtime gate
   "cannot be evaded by aliasing, by a helper module, by `getattr`, … or by a method nobody has
   listed", which is precisely what the AST layer canNOT promise.
3. **So enforce at RUNTIME, at the true chokepoint.** Producing an AST of source REQUIRES the builtin
   `compile` (`ast.parse` calls `compile(source, filename, mode, flags=PyCF_ONLY_AST)`); there is no
   pure-Python way to a real `ast.Module` of arbitrary source without it. Instrument `builtins.compile`,
   filter to `flags & ast.PyCF_ONLY_AST` **AND** a filename resolving to a workspace `.py` module, and
   walk the stack at call time: any such compile with **no `parse_production_trees` frame above it**,
   made from a test module, is an ESCAPE named file:line — the exact analog of the SDK gate's "no
   driver frame above the call". This chokepoint is spelling- AND alias-agnostic by construction (the
   spelling that reaches `compile` is irrelevant; the frame check is on the code object's identity, so
   aliasing `parse_production_trees` does not forge a sanctioned frame).

**Honest bound (stated in the instrument, per §6 / retry_seam's own scope line): the runtime gate is
absolute only over code that EXECUTES.** Code that never runs is the LINT's weak-total job, and the
un-runnable tail is INSTRUMENT 0's standing reach-attack — not pretended closed. This is why BOTH
layers ship, exactly as the retry seam ships both.

### §12.3 — How the reviser pins it (reuse the retry-seam runtime-guard machinery; do not invent)

**Layer 1 — RUNTIME chokepoint offender gate (the load-bearing, spelling-agnostic catch).** GENERALISE
`test_retry_seam`'s runtime-guard scaffold (`_install_runtime_sdk_guard`, the escape `report`,
`report.require_observations`, the pos control `test_the_guard_SEES_an_escape_it_is_shown`, the neg
control `test_a_call_INSIDE_a_driver_attempt_is_allowed`, and the plain-`def`-wrapper-walks-at-call-time
lesson) from the SDK-connection primitive to the `builtins.compile` primitive:
- Wrap `builtins.compile` (a plain `def`, so the stack walk happens when the call is MADE); record every
  PyCF_ONLY_AST compile of a workspace `.py` filename with no `parse_production_trees` frame above as an
  escape (file:line, from `inspect`/`sys._getframe`).
- **Anti-vacuity is REQUIRED and is `require_observations`:** if the gate saw NO workspace-AST compile
  at all, it is BLIND, not clean — its silence must not read as a pass (#136).
- **Positive control doubles as the routing-verification the reviser OWES (verify, don't assume — the
  #107 discipline):** aim the guard at the test file itself, `ast.parse` a workspace module with no
  sanctioned frame, assert it is recorded. If this control fails, `ast.parse` does NOT route through
  the wrapped `builtins.compile` on this Python and the reviser must also wrap `ast.parse` (do not
  assert the routing — prove it with this control). **Negative control:** a parse INSIDE
  `parse_production_trees` is allowed (or the builder deletes the gate).
- **Reach as a checked variable:** the gate runs session-wide (or drives the derived adopter scans,
  retry-seam style over `_discover_query_seams`'s analog); a private parse ANYWHERE in the executed
  suite escapes. This is the completeness guard — it is NOT a target hand-list, so `_MIGRATION_SET`
  being a small known set for Layer 3 is acceptable (a 6th un-migrated scanner that runs escapes here).

**Layer 2 — AST lint, REFRAMED from spelling to allowlist-the-safe (weak-but-total backstop for
un-executed code).** Keep an AST scan (retry-seam's `_unseamed_sdk_call_sites` SHAPE, already cited
§9.6) but re-key it: flag any parse-primitive call site (`ast.parse` / `compile(…PyCF_ONLY_AST)`)
outside `parse_production_trees` and the evidence-backed `_ALLOWED_WHOLE_TREE_CLONE_FILES` allowlist —
NOT the `rglob` spelling. This is weaker than Layer 1 (alias-defeatable) and that is fine: it exists
only to cover code Layer 1 does not execute, and it says so. Keep the existing anti-vacuity
(`test_the_scan_is_not_vacuous`) and dead-entry (`test_the_allowlist_carries_no_dead_entries`) pins.

**Layer 3 — the ∀-mutation SHARING proof, with the reach and the per-adopter assertion FIXED (sub-problem
2 — used-ness binds to CONSUMPTION).** `TestSharingProvenByMutation` stays (it proves the distinct
property "the adopter's real output DEPENDS on the shared parser", which Layer 1 does not), but:
- **Retire `_live_adopters() == "calls parse_production_trees"`.** Derive the ∀'s reach from Layer 1's
  OBSERVED-SANCTIONED set (modules the runtime gate saw routing a workspace-parse THROUGH
  `parse_production_trees`) — derived-from-execution, not a call-existence proxy and not a hand-list.
  (Equivalent acceptable form: the known adopter set, with Layer 1 as the completeness checked-variable.
  Either is sound because Layer 1 catches a decoy build BEFORE the ∀ matters — see below.)
- **Bind the per-adopter ∀ assertion to the adopter's REAL coverage consumer**, not to "something
  reddens". Drop the shared parser (via `_rebind_everywhere` by-identity so from-imports are reached,
  or a `scripts/mutation_proof.py` receipt) and require EACH adopter's `assert_scan_reached_every_member`
  coverage pin (which reads its observed set FROM the shared parser) to go RED — **both-direction diff
  (#194): a declared-RED coverage pin that stays GREEN = the adopter feeds that pin from a private scan
  = FAIL.** The decoy cannot make the real coverage pin redden (its result feeds nothing), so it is
  worthless; and its private scan is already an escape at Layer 1.

**Why the decoy dies at every layer:** its private scan produces workspace ASTs with no sanctioned
frame → **Layer 1 escape (file:line)**; its call is not the `rglob` spelling but the reframed Layer 2
flags any un-allowlisted parse primitive → **Layer 2** (weakly); and its unconsumed result cannot
redden the real coverage pin → **Layer 3** declared-RED-stayed-GREEN. The decoy's entire purpose
(get into the reach, reflect the drop) evaporates once reach is derived-from-execution and the ∀ binds
to the real consumer.

### §12.4 — comms_footer scan↔mode binding (Ruling 6.3 residual): PIN IT, don't hand-check

**Disposition: PIN the binding — the per-scan scanned-file-set equality pin already MANDATED by §8
Ruling 1 and §10 Ruling 6.3 IS the mode-binding enforcement; it must be BUILT per scan (it currently
tests the HELPER's two modes, not WHICH mode each scan consumes).** Mechanism: Scan A must consume
`parse_production_trees(include_tests=True)` and Scan B `(include_tests=False)`; pin each scan's
post-migration scanned FILE SET == its exact pre-migration set (oracle = the pre-migration reach).
Then a mode-swap is caught mechanically: Scan A on `include_tests=False` NARROWS (drops the member-test
files it scans today) ≠ its pinned set → RED; Scan B on `include_tests=True` GAINS member tests ≠ its
pinned set → RED. This also catches §10 R6.3's live hazard (`workspace_roots` yields `<member>/<member>`
package roots that structurally EXCLUDE `<member>/tests`, so `include_tests=True` must re-add them or
Scan A silently narrows). **Cold-audit obligation:** verify BOTH per-scan equality pins exist, that
their sets are DISTINCT (Scan A ⊋ Scan B by exactly the member-test files), and that a swap reddens.
**Hand-check fallback ONLY** if the reviser finds the two sets cannot be made discriminating (e.g. a
member has zero test files, collapsing the include_tests distinction) — in which case that
non-discrimination is itself flagged, and the binding drops to an explicit named A-SUB cold-audit
hand-check. Default is the pin; the hand-check is the escape hatch, not the plan.

### §12.5 — Reuse map / DRY (Packages considered)

- **`test_retry_seam.TestNoSdkCallEscapesTheDriverAtRuntime` + `_install_runtime_sdk_guard` +
  `report.require_observations` + its pos/neg controls + the plain-`def`-walks-at-call-time lesson**
  (`loremaster/tests/test_retry_seam.py`) — the runtime-reach-gate PATTERN, already proven and pinned.
  Layer 1 GENERALISES it (SDK-connection primitive → `builtins.compile` primitive). **REUSE candidate,
  flagged for the builder:** the escape-report + require_observations + stack-walk-for-sanctioned-frame
  + pos/neg-control shape is a shared POLICY (the runtime-reach guard) with now ≥2 users (SDK gate +
  parse gate) — a candidate to extract into shared test-support parametrized by (primitive,
  sanctioned-frame), **gated on prove-by-mutation** (change the shared scaffold → BOTH gates redden;
  a caller that stays green is a private copy), exactly like the `_rebind_everywhere` promotion (#3).
  Do NOT force the extraction if the retry-seam guard proves tightly coupled to async-SDK specifics
  (§7 over-consolidation caution) — recommend it, prove it, or clone only the SHAPE.
- **`_logging_fixtures.assert_scan_reached_every_member` / `parse_production_trees`** (pinned by
  `test_ast_reach_helpers.py`) — the sanctioned parser (Layer 1's one SAFE name) and the coverage
  consumer Layer 3 binds to.
- **`_rebind_everywhere`** (promoting to `_logging_fixtures` per #3) + **`scripts/mutation_proof.py`**
  (both-direction diff, `--collect-only` declared node ids, #194 landing guard) — Layer 3's mutation.
- **`_unseamed_sdk_call_sites` SHAPE** (`test_retry_seam`) — Layer 2's reframed allowlist-the-safe scan.
- **INSTRUMENT 0's reach-attack** (`~/.claude/agents/contract-adversary.md`, P1c) — the un-runnable tail.
- **Packages considered:** stdlib `ast`/`sys`/`inspect`/`builtins` only (the compile chokepoint + stack
  walk); no library supplies a "no-unsanctioned-frame-above-a-primitive" runtime gate. **Verdict:
  bespoke (minimal), GENERALISING the in-repo retry-seam runtime-guard idiom — not new machinery.**

### §12.6 — Routing & recommendation

- **This is a CONTRACT revision (test-only), routed through the standing order: contract → adversary
  → build → cold audit** (a fix wave is where the adversary is cheapest — operator, 2026-07-28). The
  reviser writes Layers 1–3 + the comms_footer binding pin to §12.3/§12.4; the contract-adversary
  MUST re-attack with the delta-adversary's survivor (private `production_sources`+`ast.parse` scan +
  unconsumed decoy) AND a fresh spelling (`os.walk` / a comprehension / a direct
  `compile(…PyCF_ONLY_AST)` / an alias) — Layer 1 must catch every one; plus the decoy-into-derived-reach
  build (Layer 3 must catch it) and a mode-swapped comms_footer (§12.4 must catch it).
- **The load-bearing acceptance test (the pos control that is also the routing proof):** the
  reviser DEMONSTRATES Layer 1 firing on a `compile(…PyCF_ONLY_AST)` and on an `ast.parse` with no
  sanctioned frame — if `ast.parse` does not register through the wrapped `builtins.compile`, wrap
  `ast.parse` too. Do not ship the claim un-demonstrated.
- **No operator scope-grant needed** (test-only, within the A-SUB writable set, reusing a shipped
  pattern). The only lead action is routing the revised A-SUB contract through the standing cycle.
- **Named re-open trigger:** the day this repo gains CI (#285), Layer 1's session-wide run becomes a CI
  job so its reach covers the full suite deterministically; and if a NEW sanctioned whole-tree parser
  is ever added beside `parse_production_trees`, Layer 1's SAFE set grows by exactly one named frame
  (a deliberate, reviewed edit), never a spelling.
