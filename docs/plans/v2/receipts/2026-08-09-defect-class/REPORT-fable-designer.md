# REPORT — fable-designer (defect-class prevention design, #344/#345 + 6 siblings)

brief-base v10 read
brief project v7 read

## SUMMARY
- state: **done** — design doc delivered; F1–F5 ruled; 3 operator escalations named.
- deliverable: `docs/plans/v2/design/2026-08-09-defect-class-prevention.md` (tracked path).
- deviations: investigation agents' `REPORT-*.md` writes were blocked by the harness; they
  returned findings as text (captured in the doc). No repo-root REPORT clutter resulted.
- Packages considered: none new — instruments are stdlib (`ast`, `tomllib`) + already-vendored
  `coverage.py` + the repo's own `pending_contract_gate.py` / `registration_sites.py` patterns.
  No external library provides "derive THIS repo's site-set and check coverage"; that is bespoke
  by necessity (the two-sided rule: the package does not do the job).
- Graded: 74694dc · HEAD-at-report: 74694dc · SAME. (Rulings + HEAD-verification of #289/#290
  instance fixes rest on this sha.)
- decisions-needed (operator): (1) F3/#337 keep ledger-only [recommended] vs pin via a call-graph
  cycle — pinning reverses the 2026-08-08 ruling; (2) F5/#279 placement — production
  `loremaster.store` helper [recommended] vs tests→scripts import; (3) INSTRUMENT B — retire the
  OLD `_RENDER_DRIVERS` hand-net (holds the literal `task_id=None`) now vs keep as labelled subset.
- receipt pointers: doc §1 (class stmt), §3 (instruments 0/G/A-SUB/B/C/D/E/F/H + B2/F3), §4 (fork
  summary), §5 (build plan + escalations), §6 (what it does NOT claim).

## THE CLASS (one sentence)
A guard/gate/probe certifies only the sites it EXECUTES, and its REACH is a hidden constant, not a
checked variable — so unreached sites are exempt silently and forever. The reach hid seven ways:
hardcoded driver param (#345), name-prefix discovery (#337), hand-list per brief (#344), hand-list
beside production truth (#291), derivation-written-twice (#279), un-vacuity-checked baseline (#290),
observe-the-proxy-not-the-effect (#295), missing malformed-input case (#289).

**Fix principle (repo law → build-time instrument):** derive the site-set from a PROPERTY of
production truth (AST/annotations/identity/manifest), and make COVERAGE a CHECKED VARIABLE
(observed==derived, fail-closed on empty, allowlist-the-safe with evidence + re-open trigger). Plus:
observe the EFFECT not the proxy (#295); anti-vacuity on the comparison's baseline (#290).

## INSTRUMENTS (name → property → findings)
- **0 — contract-adversary REACH ATTACK** (the meta-instrument): per guard/gate/scan, force the
  answers "what set? derived or hand-list? coverage a checked var? effect or proxy?" — catches
  instance #9 at CONTRACT time. The only piece that generalises; everything else is one surface.
- **G — non-omittable gate bundle** (#344): `scripts/wave_gate.py`, a thin wrapper over
  `pending_contract_gate.py --currency` that re-lists NO gates (inherits gates.yaml) and renders a
  required, recorded mode + the exact pytest scope. Briefs point at it, stop listing gates.
- **A-SUB — shared AST-∀-scan helpers** (F4): one `parse_production_trees` + one
  `assert_scan_reached_every_member` in `_logging_fixtures.py` (root-derivation already shared there
  via `workspace_roots`); the tree-parser is re-hand-rolled in 14 files. Prove by mutation.
- **B — render slot inventory + `sanitise_line`-in-render scan** (#345): derive the driven-slot
  inventory from render AST so a field mis-parked SAFE surfaces as an un-driven slot → RED; generalise
  the existing error-half scan to render contexts. (The Link5 file already has the coverage apparatus;
  the hole was P-F's hand-classified DOOR/SAFE split whose correctness nothing checked.)
- **C — derive mutating tool-set from annotations** (#291): partition from `mcp.list_tools()`
  `readOnlyHint is not True` (deny-by-default) + every-tool-non-None pin + mutation pin.
- **D — refusal pins observe the EFFECT** (#295): shared `assert_tool_refused_and_did_not_run`
  (wire session + invocation-counter==0) + one-time sweep. Structural fix → packet 39.
- **E — trailing-newline matrix** (#289): instance pin (`finding="#188\n"`) + a killed wrong_build;
  the per-field-fate rule rides adversary/checklist (not AST-derivable).
- **H — anti-vacuity on a baseline** (#290): extract `scripts/_harness_guards.refuse_vacuous_baseline`
  + a covering test that drives the zero-baseline path.
- **F — one store-seam derivation** (#279): shared `_txn_coroutines` core; wide-set + door-subset
  from one walk; prove sharing by mutating the core (both sides redden).

## FORK RULINGS
- **F1** (currency vs scoped pytest): the non-omittable core (typecheck+ruff+currency) always runs
  FULL; only pytest is scopable — `--wave` runs it scoped with the selector ECHOED and the line marked
  `SCOPED` (never GREEN), `--checkpoint` runs it full. Mode is a required, recorded arg. No touch to
  `pending_contract_gate.py`. Re-open trigger: the day CI lands (#285), `--checkpoint` is CI's first job.
- **F2** (#295 vs auth): build effect-helper + sweep now; route registration/visibility gating to
  packet 39. Honest bound: no permanent AST gate for "refusal pin" — INSTRUMENT 0 is its standing guard.
- **F3** (#337 pin vs ruling): #345 and #337 are ORTHOGONAL (forgery vs promise-prose). #345 already
  covers the SECURITY dimension of the off-prefix helpers; #337's promise-scan is NOT subsumed and its
  fix is a call-graph-closure DESIGN cycle (found a 2nd helper `_render_fleet_status_cell`; the naive
  "calls a render primitive" over-matches 25 funcs). **Recommend keep ledger-only + tighten trigger;
  operator rules if it wants a pin.**
- **F4** (AST substrate): ONE shared LIBRARY of reach helpers (NOT one mega-file); per-scan files stay
  separate; prove by mutation. Lives in `_logging_fixtures.py` (test infra — NOT `lorerunes`).
- **F5** (#279 closed file): IN-SCOPE this session as its OWN sequenced cycle; cold audit re-runs FULL
  `test_blocks_edge` (9131 lines/155 tests) + the sharing mutation-proof. Placement escalated.

## BUILD PLAN (roster: Opus contract→adversary→builder→cold-audit each)
Wave 1 parallel: **G, A-SUB, C, E, H, D**. Wave 2 (after A-SUB): **B**. Own cycle any time: **F**.
INSTRUMENT 0 = edit to `contract-adversary.md` + a CLAUDE.md law line (no code cycle). No store/DDL
touched. Recommended serial order if needed: 0 → G → A-SUB → C/E/H/D → B → F.

## HEAD verification (via agents, receipts in doc §3)
#289 `.fullmatch` fix — LANDED at HEAD. #290 baseline anti-vacuity — LANDED at HEAD. Both INSTANCE
fixes are present; the CLASS invariants (a killed wrong_build for #289; a covering test + shared guard
for #290) are NOT yet built — that is what E and H add.

Pointer: full design at `docs/plans/v2/design/2026-08-09-defect-class-prevention.md`. Standing by for
follow-ups.

## DRY REVIEW ADDENDUM (operator DRY-first steer, 2026-08-09) — doc §7
Re-reviewed every instrument under DRY=#1. Key results:
- **Sharpest insight:** A-SUB (the consolidation instrument) is itself an instance of the class — its
  reach = which callers adopt it. So it ships an ANTI-DUPLICATION structural pin (no hand-rolled
  whole-tree parser / member-reach assertion outside the shared helpers, with a non-adopter allowlist),
  and the design binds to a PROPERTY, never a hardcoded adopter list (a list would be the antipattern).
- **`parse_production_trees` is the clean consolidation — 5 real adopters** (anchored, secret_typing
  [+ its duplicate `_SCANNED_MEMBERS` retired], comms_footer, backoff, secret_leak). Prove by mutation.
- **Over-consolidation is itself a DRY error (avoided):** `assert_covers` is SCOPED to the 2 tree-scan
  reach checks; the render/runtime/probe reach-checks keep bespoke messages. B extends test_link5's
  own P-U/P-F (adopts neither global helper); D shares the EFFECT-helper, not a coverage helper.
- **Routing-not-sharing traps flagged:** C/#291 must land the mutating partition as a PRODUCTION
  derivation (test pins, pkt39 consumes) — else the policy is written twice; B's superset proof +
  interpolation classifier must reuse existing predicates; G's wrapper must invoke, not re-parse
  gates.yaml; H must NOT be merged with pending_contract_gate's reader-anti-vacuity (different policy).
- **INSTRUMENT 0 gains leg (5):** "two sources of truth for one policy? sharing proven by mutation?"
- **Sequencing corrected:** B is INDEPENDENT of A-SUB (was wrongly "after A-SUB"). All 8 cycles parallel.

## §9 ADDENDUM — the consolidated ∀-mutation-proof pattern (design COMPLETE, 5/5 adversaries)
All 5 contract adversaries returned INSUFFICIENT on ONE class: a prove-sharing/coverage/liveness pin
mutates ONE member of a derived set, so a hybrid that fixes that member but hardcodes the rest survives.
Design doc §9 is the reviser's single starting point:
- §9.1 IDIOM 1 (∀-mutation): two legs over the SAME live-derived surface — LEG A consistency
  (`assert_scan_reached_every_member` / live set-equality, fail-closed) + LEG B liveness (flip EACH
  member, every caller reddens; both-direction diff). Meta-recursion guard: surface derived LIVE in-test.
- §9.2 IDIOM 2 (wire/effect spy): observe the real boundary — reuse `WireSession` + the R16
  `test_wire_discipline.py` AST invariant; hand only the callable to make the proxy unrepresentable.
- §9.3 IDIOM 3 (summary honesty): the only net-new idiom; summary derived from per-leg typed flags.
- §9.6 REUSE MAP: every idiom generalises an existing symbol (`TestScanCoverage`,
  `TestSharingProvenByMutation`+`_core_dropping`+`_rebind_everywhere`, `scripts/mutation_proof.py`,
  `test_backoff_seam._DECLARED_SITES`, `test_retry_seam._all_sdk_call_sites`, `WireSession`).
- §9.7 folds the 5th adversary: A-SUB's sharing mutation must reach from-imports → reuse
  `_rebind_everywhere` (promote to shared, now ≥2 reusers); B's Leg-2 must be comprehension-aware +
  a `_SERVED_SAFE_FIELDS ∩ manifest-DOOR == ∅` pin (mechanises Ruling 2); `kind` is a 2nd field-name
  collision (validates Ruling 3).
Design status: COMPLETE. Reviser applies §9 uniformly; only IDIOM 3 is new machinery.
