# REPORT — fable-sidecar (persistent design sidecar)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- **State:** loaded — standing by for design forks (persistent for session `2026-08-09-fix-344-345`).
- **Role:** THE persistent Fable design sidecar. Writes NO code/tests — rulings + design-doc
  sections only. Design authority operator-delegated for this session; I rule design forks and
  flag anything needing an operator scope-grant. This report is my only writable file; new
  rulings append as dated sections below.
- **Capability check:** brief is satisfiable with my toolset (lore tools loaded, Read/Write/Edit,
  lore_comms for coordination). No impossibility to flag.
- **Deviations:** none.
- **Packages considered:** none — no mechanism specified (design-consult role).
- **Graded:** loaded design of record at HEAD `e36c114` · HEAD-at-report `e36c114` · SAME. Not
  rendering a verdict on any artifact yet.
- **Decisions-needed:** none at boot. (Design is COMPLETE; the three §5 operator escalations —
  F3/#337 ledger-only, F5/#279 placement, INSTRUMENT B `_RENDER_DRIVERS` retirement — plus
  §11.7's `pending_contract_gate.py`-into-G-writable-set fork are named as forks for the lead to
  resolve at wave open, not fresh questions from me.)
- **Receipt pointers:**
  - Boot reads: `~/.claude/orchestration/brief-base.md` (v10); brief `project` v7 (via register);
    design of record `docs/plans/v2/design/2026-08-09-defect-class-prevention.md` §1–§11.7 (full).
  - Design of record is COMPLETE; build wave + cold audits are next (this doc §5 build plan).

## Boot state (loaded 2026-08-09 at HEAD `e36c114`)

Registered `fable-sidecar` (session `2026-08-09-fix-344-345`, role designer, model
claude-opus-4-8). Inbox drained: empty.

Design of record read IN FULL and held in context for follow-ups:
- **§1** the class ("reach is a hidden constant, not a checked variable") + the eight instances
  + the askable-question form.
- **§2** the three in-tree exemplars (`registration_sites.py`, `test_anchored_pattern_seam.py`,
  `pending_contract_gate.py`).
- **§3** INSTRUMENT specs: 0 (reach-attack, SETTLED), G (#344 gate bundle, SETTLED), A-SUB (F4
  shared scan substrate, SETTLED), B (#345 render slot inventory), E (#289 trailing-newline),
  H (#290 baseline anti-vacuity), F (#279 store-seam derivation, F5), C (#291 derive-from-
  annotations, SETTLED), D (#295 observe-the-effect, F2), B2/F3 (#337, escalation).
- **§4** fork rulings F1–F5 summary. **§5** build plan (all 8 cycles independent/parallel;
  contract→adversary→build→cold-audit each; F its own closed-file cycle).
- **§6** trust-doctrine self-check (what the design does NOT claim). **§7** DRY review (the
  over-consolidation ruling: `parse_production_trees` 5 adopters + `assert_covers` 2 adopters;
  B/D route through their own homes; C→production helper; H no over-merge).
- **§8** contract-asub-b rulings (1 per-adopter include_tests; 2 `blocked_by` is a DOOR; 3
  field-name keying confirmed conditional on drive-all + P-N).
- **§9** the ∀-mutation-proof pattern (all 5 adversaries INSUFFICIENT on one class): 9.1 IDIOM 1
  (LEG A consistency + LEG B liveness, meta-recursion guard), 9.2 IDIOM 2 (wire/effect spy),
  9.3 IDIOM 3 (summary honesty), 9.4 companion laws, **9.5 per-packet table**, **9.6 reuse map**
  (naming correction: `assert_scan_reached_every_member`, not `assert_covers`), 9.7 fold of the
  5th adversary.
- **§10** reviser-asub-b rulings (4 fleet-row `task_id` is a live DOOR + 3 coupled fixes; 5
  field-name keying confirmed sound, collision→CONTAIN never split; 6 comms_footer in A-SUB
  writable set, both scans migrate; #3 `_rebind_everywhere` promotion approved).
- **§11** G summary-honesty structural redesign (string→type: `SummaryVerdict` closed enum +
  `summary_verdict` pure total fn + `render_summary` sole minter + `SummaryLine` provenance type;
  4 pins P1–P4; kills W-summary-alt/double/inline by construction; production extraction into
  `pending_contract_gate.py` = operator fork §11.7).

Standing by. Rulings for forks that arise during the build wave / cold audits will be appended
below as dated sections and echoed to the lead.

## RULING LOG

### Fork 1 — A-SUB anti-dup defeated by spelling (2026-08-09, HEAD `e36c114`)

**Source:** lead-defect-class relayed `REPORT-delta-adversary-asub-b.md` — A-SUB still INSUFFICIENT
(1 BLOCKER, A-SUB-3 sharing NOT closed). A routing-not-sharing survivor: a PRIVATE whole-tree scan
via `production_sources()`/`workspace_roots()`+`ast.parse` (no `rglob`) doing the real work + an
unconsumed decoy calling `parse_production_trees` to satisfy used-ness/∀.

**Ruled → appended design doc §12 (A-SUB anti-dup: un-defeatable-by-spelling).** Grounded at HEAD:
`test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist` keys on the
`rglob+ast.parse` spelling; `TestSharingProvenByMutation::_live_adopters` keys on call-existence —
both PROXIES, this doc's own class one file over (= §11's string→type problem, one primitive over).

**The ruling (3 layers + 1 binding pin, all TEST-ONLY, reuse > invent):**
1. **RUNTIME chokepoint gate is the un-defeatable form; AST-allowlist alone REJECTED.** Instrument
   `builtins.compile` (filtered PyCF_ONLY_AST + workspace-`.py` filename); any such parse with no
   `parse_production_trees` frame above = escape, file:line. The parse primitive is the one chokepoint
   no spelling/alias evades (`ast.parse` → `compile`). GENERALISES the SHIPPED, PROVEN
   `test_retry_seam.TestNoSdkCallEscapesTheDriverAtRuntime` runtime-guard (same `require_observations`
   anti-vacuity #136, pos/neg controls, plain-`def`-walks-at-call-time). A-SUB has only the (mis-built,
   spelling-keyed) LINT half today; this adds the runtime half.
2. **AST lint REFRAMED** off the `rglob` spelling → allowlist-the-safe over the parse PRIMITIVE
   (weak-but-total backstop for un-executed code; honest that it's alias-defeatable — that's Layer 1's
   job).
3. **∀-mutation reach + assertion FIXED (used-ness binds to CONSUMPTION):** retire
   `_live_adopters=="calls parse_production_trees"` → derive reach from Layer 1's observed-sanctioned
   set; bind each adopter's ∀ to its REAL `assert_scan_reached_every_member` coverage pin, both-direction
   diff (#194 declared-RED-stayed-GREEN = private copy). Decoy dies at all three layers.
4. **comms_footer mode↔scan binding:** PIN via the already-mandated (§8 R1/§10 R6.3) per-scan
   scanned-file-set equality (Scan A `include_tests=True`, Scan B `False`; oracle = pre-migration sets;
   distinct by member-test files). Hand-check is fallback only if sets prove non-discriminating.

**Honest bound:** runtime gate absolute only over EXECUTED code; un-run tail = Layer 2 (weak-total) +
INSTRUMENT 0's reach-attack — not pretended closed. **Reuse:** retry-seam runtime-guard scaffold
(candidate for shared-test-support extraction, gated on prove-by-mutation like `_rebind_everywhere` #3),
`assert_scan_reached_every_member`/`parse_production_trees`, `_rebind_everywhere`/`mutation_proof.py`.
**Packages considered:** stdlib `ast`/`sys`/`inspect`/`builtins` only — bespoke minimal, generalising
the in-repo idiom. **Scope:** TEST-ONLY, within A-SUB writable set, reuses a shipped pattern — **NO
operator scope-grant needed.** Routes through the standing contract→adversary→build→cold-audit cycle;
the adversary must re-attack with the survivor + a fresh spelling + the decoy-into-derived-reach build +
a mode-swapped comms_footer.

#### Fork 1 — SHARPENING (2026-08-09): operator "read the idiom, don't reinvent" — named + a self-caught trap

Lead sharpened: name the EXISTING proven un-defeatable-by-spelling idiom and reuse it; hand-roll only if
none fits (verified by READING). I READ the machinery (`lore_get_symbol`) rather than paraphrase — and it
caught a defect in my own §12 draft.

- **The named idiom (the #102/#120 runtime SDK-escape guard):** shared module
  `loremaster/tests/_sdk_guard.py` (autouse via conftest; `GuardReport` API `.armed`/`.escapes`/
  `.require_observations`), armed by `_install_runtime_sdk_guard`/`_install_shared_guard`, pinned by
  `test_retry_seam.TestNoSdkCallEscapesTheDriverAtRuntime` + its pos/neg controls + the
  plain-`def`-walks-at-call-time (2×2 detachment) lesson. Layer 1 GENERALISES this exact module
  (SDK-connection primitive → `builtins.compile`), it does NOT invent a new detector. Also confirmed a
  shared-extraction candidacy (≥2 users), gated on prove-by-mutation like `_rebind_everywhere` #3.
- **⚠ SELF-CAUGHT TRAP (the reason "read it" is operator law):** my first §12 draft said "the OFFENDER
  leg IS the completeness guard." Reading `_all_sdk_call_sites`'s docstring showed that is the EXACT v5
  trap it already paid for — coverage built from the offenders set (`_unseamed_sdk_call_sites`) is
  *empty-on-a-clean-build → strictly dominated by the lint → cannot fire*; `WB-ROUTED-UNDRIVEN` walked
  through it, "#120 alive again, one altitude up." **Corrected §12.3/§12.5:** the reach-checked-variable
  reuses the **ALL-set** shape (`_all_sdk_call_sites` → `_all_workspace_parse_sites()`), asserting each
  ALL-set parse site was OBSERVED executing under the guard ("watched ≠ well-formed ≠ unexamined"), NOT
  the offenders set. The ALL/offenders split maps cleanly: ALL-set → coverage; offenders → the Layer-2
  lint. This independently matches the render instrument's resolution (packet 04b5: "checked variable is
  coverage over execution, not a static derivation").

### Fork 2 — G/#344 summary honesty round 4: complete the typed WaveReceipt (2026-08-09, HEAD `e36c114`)

**Source:** lead relayed `REPORT-delta-adversary-g-3.md` (graded `1a5d9b3`) — §11 closed every prior
survivor (mutation-verified, extraction non-regressive 41/0) but typed only the SUMMARY LINE; the RECEIPT
composition is still `lines.append(<anything>)`, so **W-EXTRA-LINE survives 143/143** (honest
`render_summary(PASS_SCOPED)` line + an appended alt-wording over-claim). Class one slot over, round 4.

**Ruled → appended design doc §11.8 (completion of §11, not a new design).**

- **Ask 1 CONFIRMED — full typed `WaveReceipt`, not a minimal pin.** And ⚠ found §11.2.4's own
  `[*leg_lines, summary, note]` model is INCOMPLETE: reading the real composition
  (`pending_contract_gate._render_currency` 1521–1578 + the wave contract) shows **SIX** line sources, not
  three. Pinning the naive form verbatim would BOTH fail on the real receipt AND leave slots open.
- **Ask 2 ROUND-5 GUARD — enumerated every line source, each → a typed component:** (1) header (mode+scope),
  (2) manifest roster, (3) per-gate verdict `GateCurrency.render()`, (4) **per-orphan `ORPHAN:` — a LIVE
  free-`str` append TODAY, the OTHER W-EXTRA-LINE slot**, (5) summary (§11, done), (6) note. The header/
  roster/orphan are the "other open slots" the guard exists to find; #4 is the sharp one. Mechanism (§12
  ladder): STRONG = frozen typed `WaveReceipt`, `render()` a total fn over the six components, no free
  `list[str]` to append to; WEAK-total = AST mint-scan (reuse `TestSafeLineRenderedMintPin`) forbidding
  any free-`str` receipt composition outside `render()` → a NEW append path (round 5) reddens on sight.
- **Exact pin:** `test_wave_receipt_is_the_fixed_typed_composition_no_free_append` (structural: render ==
  total composition, `len(legs)==len(gates)`, both modes + FAIL path) + `test_no_free_receipt_line_
  composition_outside_render` (AST mint-scan) + both-direction mutation proofs (W-EXTRA-LINE via summary
  slot AND via orphan slot both redden; a new typed component without the pin reddens) + pos/neg controls.
- **⚠ SCOPE FLAG (the lead's "flag if further production change"):** WAVE receipt typing = in scope (new
  `wave_gate.py`). CHECKPOINT `_render_currency` full typing (header/roster/orphan, sharing the WaveReceipt
  type per DRY #1) = a FURTHER production change to the #306/#312 surface beyond the approved summary
  extraction. **RECOMMEND GRANTING** (leaving wave typed + checkpoint free-append = two composition
  implementations = the #102 risk operator priority #1 forbids; behaviour-preserving, guarded by
  test_pending_contract_gate.py 41/0 + a byte-exact whole-receipt oracle). Fallback: type wave now, file
  checkpoint typing as a named follow-up, state DRY #1 deferred. Operator/lead decides.
- **Ask 3 CONFIRMED** — reviser fork-2 (rephrased over-claim baked into `render_summary(PASS_SCOPED)`/`FAIL`
  fixed strings) is a one-time cold-audit READ, not a per-call door (sole minter, fixed strings). Noted
  reviser fork-1 (checkpoint FAIL fixed line) still owes an operator ruling; orthogonal, satisfiable 41/0.
- **Reuse:** §11 summary types + `GateCurrency.render()` + `TestSafeLineRenderedMintPin` idiom. **Packages:**
  stdlib enum/dataclasses + str-subclass — bespoke minimal, string→type lift one level up.

### Fork 3 — G/#344 round 6 (endgame): ∀ over the DERIVED honesty-line set (2026-08-09, HEAD `e36c114`)

**Source:** lead relayed `REPORT-delta-adversary-g-4` — §11.8 typed receipt WORKS (all 7 §11.8.7 attacks die,
170/0, extraction 41/0) but W-SCOPED-OVERCLAIM (D2c) survives: the SCOPED-leg line's CONTENT is still free
text (pinned only "not literally GREEN"); a PASS_SCOPED receipt reading "tree is current and clean; nothing
owed" over-claims. R1 tell: reviser anchored "ONLY the wave-header constant" — partial enumeration of the
honesty lines = the packet's class one line over. Recurrence: one honesty line typed per round, neighbor
survives (summary→composition→scoped-leg→FAIL-detail).

**Ruled → appended design doc §11.9 (the completion that ends the recurrence).**

- **Ground truth:** the CHECKPOINT whole-receipt byte-oracle ALREADY exists
  (`test_checkpoint_receipt_preserves_the_historical_bytes`, §11.8.4 built) + the checkpoint FAIL-split; the GAP
  is the WAVE receipt (only its header anchored — R1). So the completion EXTENDS the existing byte-oracle idiom
  to wave, not new machinery.
- **The move (the key ruling): DON'T classify/enumerate honesty lines — a content classifier IS the next
  instance of the class (R1 is that classifier failing by hand). Anchor EVERY line over the DERIVED state
  domain** (strictly subsumes the honesty subset; no subset to get wrong). Same reasoning as §12 (anchor at the
  chokepoint, don't enumerate spellings) and §11.8 (type every line source).
- **Two DERIVED anchors:** (1) per-component byte-anchor over its OWN closed-enum domain (`SummaryVerdict`/
  `LegQualification.__members__` × scoped), coverage-checked via the §11 meta-recursion (`_leg_qual_combos`) —
  the ∀ over the derived honesty-line set, set derived from the typed structure + `__members__`, not hand-listed;
  (2) whole-wave-receipt byte-oracle over the derived state domain (incl. PASS_SCOPED + FAIL) — extends
  `test_checkpoint_receipt_preserves_the_historical_bytes` to wave. Plus §11.8's frozen structure + AST
  mint-scan (§12 ladder: byte-oracle+structure STRONG, mint-scan WEAK-total). Sole-mint the wave honesty prose
  (`_SCOPED_HONESTY` + wave FAIL-detail catalog constants, new code, free).
- **Exact pins:** `test_every_wave_receipt_line_is_byte_anchored_over_the_derived_verdict_state_domain` +
  `test_every_typed_component_prose_is_byte_anchored_over_its_enum_domain` + the extended mint-scan + both-way
  mutation proofs (rewrite scoped-leg/FAIL-detail → redden; grow LegQualification w/o anchor → coverage reddens).
- **Dies by construction:** D2c (scoped-leg reworded ≠ anchored bytes), D1a (wave FAIL-detail), a round-7 line
  (new line ≠ golden → reviewed golden update, no silent over-claim), R1 (read-zone = whole receipt over derived
  domain, no hand-named subset).
- **Honest bound:** the byte-oracle pins CONSISTENCY WITH AN AUDITED GOLDEN, not semantic honesty; the golden's
  prose honesty is human-established ONCE (reviser fork-2's one-time read, generalized to every catalog constant).
- **Scope: TEST-ONLY + the already-approved pcg extraction — NO new scope-grant** (wave byte-oracle is test-only
  goldens; catalog constants are new wave_gate.py code; checkpoint oracle already built §11.8.4).
- **Reuse:** the existing checkpoint byte-oracle + §11 closed enums/meta-recursion + `test_render_summary_*` +
  `TestSafeLineRenderedMintPin`. **Packages:** stdlib enum + str-subclass — bespoke minimal, extending four
  in-repo idioms.

### Fork 4 — A-SUB round 5: skip-set silent exemption + negative non-parsing scan (#349) (2026-08-09, HEAD `e36c114`)

**Source:** lead relayed `delta-adversary-asub-4` (#349). Q(a) §12.3 rider WORKS. Q(b) FAILS: the "4 adopters
SKIP" is a SILENT EXEMPTION (backoff = pure decoy, private os.walk wrong build passes 44/4-skip byte-identical);
and a NEGATIVE non-parsing os.walk (checks filenames, never compiles) ESCAPES L1's compile chokepoint AND is
un-reddenable by mutation (negative scan). Fix must be structural, not mutation-diff.

**Ruled → appended design doc §12.7.** Three asks:

- **Ask 1 THREAT MODEL (stated IN the instrument so verdicts follow mechanically):** A-SUB's anti-dup guards
  ONE policy — the PARSE (parse_production_trees), chokepoint = compile, honest-dev threat, NOT security. A
  NEGATIVE non-parsing tree-walk produces no AST → NOT the parse operation → **OUT OF SCOPE by definition**; its
  escaping L1 is not a defect (L1 is a parser chokepoint, a non-parser has nothing to route). Verdicts: private
  PARSE (any spelling) → L1 catches; a file that PARSES but is skipped → skip-coverage pin; non-parsing WALK →
  out of scope, pinned bound.
- **Ask 2 SKIP-SET → CHECKED VARIABLE (required either way):** `_ASUB_PARSE_SKIP` allowlist (evidence reason
  per entry) + `test_no_skip_set_file_parses_the_tree_unrouted` (REUSE L1's observed-parse set — a skip file
  observed parsing unrouted → RED: mis-classified adopter or false "does not parse" reason) + dead-entry pin
  (reuse `_ALLOWED_WHOLE_TREE_CLONE_FILES` idiom). Makes backoff's skip HONEST ("confirmed non-parsing", checked
  at runtime), not "the reviser decided." Closes the 44/4-skip hole.
- **Ask 3 NEGATIVE-SCAN — PIN THE BOUND, don't chase spellings:** tree-walking has NO compile-like chokepoint
  (os.walk/scandir/iterdir/glob/hardcoded-list; even scandir-instrumentation is noisy + defeated by a
  hardcoded-list scan), and enumerating walk spellings IS round 6. Per CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE,
  PIN IT": `test_asub_nonparsing_tree_walk_is_a_KNOWN_BOUND_349` (the #137/#138 pin-the-miss idiom — asserts the
  bound, reddens if someone closes it). Residual harm = DRIFT, already mostly mitigated (only HARDCODED-root
  walks drift; scans using workspace_roots/production_sources don't; the one instance — comms_footer Scan B — is
  migrating §10 R6). Named re-open trigger: real drift found / threat model changes / CI+root-audit (#285); then
  the cheapest candidate is a narrow member-root-literal scan, NOT an os.scandir chokepoint.
- **Scope: TEST-ONLY, no scope-grant** — but operator should ACKNOWLEDGE #349 with the pinned-bound disposition
  (a scope decision the operator owns: accept-as-pinned vs build the narrow scan now). I RECOMMEND accept-as-
  pinned (de-prioritized threat, residual mostly mitigated, alternative risks round 6). Flagged, not decided.
- **Reuse:** `_ALLOWED_WHOLE_TREE_CLONE_FILES` dead-entry idiom + L1's `_all_workspace_parse_sites` observation
  + the #137/#138 pin-the-miss idiom. **Packages:** stdlib only — bespoke minimal.

### Fork 6 — A-SUB round 6: route skip-coverage through L1's RUNTIME observation (2026-08-10, HEAD `e36c114`)

**Source:** `delta-adversary-asub-5`. My §12.7.2 skip-coverage pin was built (by the reviser) on the STATIC
`_all_workspace_parse_sites` (spelling-blind, 3-name source hand-list) → a split-leg parse (`production_sources()`
+ `ast.parse` across functions) escapes it (backoff/secret_typing/comms_footer parse unrouted, 49/4-skip). This
is an IN-SCOPE PARSE (produces AST), not the #349 non-parsing tail. Coupled trust defect: docstring mislabels it
"the #349 bound" = false clear.

**⚠ I OWN THE ROOT CAUSE:** §12.7.2 wrote "REUSE L1's observation (`_all_workspace_parse_sites` / the runtime
compile-chokepoint observation)" — CONFLATING the static AST ALL-set (L1's own coverage instrument, spelling-blind)
with L1's RUNTIME `report.escapes`. Reviser took the one named first (static). §12.8 disambiguates.

**Ruled → appended design doc §12.8.**

- **Ask 1 CONFIRM in-scope, close via L1, no new operator ruling — I AGREE.** A split-leg parse produces an AST
  → it IS the parse operation §12.7.1 puts in scope, spelled across functions; L1 (compile chokepoint) catches any
  spelling. Operator's #349 ruling scoped out ONLY non-parsing walks. CLOSES via L1, not pinned.
- **Ask 2: re-source the skip-coverage pin to L1's RUNTIME `report.escapes`** (un-defeatable, already records
  backoff at test_backoff_seam.py:780), NOT the static detector; stop exempting skip files from L1's assert;
  reach = `require_observations` per skip file (§12.3).
- **Ask 3 discriminator (whole-workspace vs single-file) = per-skip-file DECLARED unrouted-parse budget** in the
  allowlist (default ∅/0 for "does not parse" skips; a documented single-file parse declares that file/count 1 with
  evidence); assert L1-observed unrouted-workspace-compile set ⊆ declared. NOT a global threshold — a per-file
  declared value (allowlist-the-safe), checked both ways (over-budget → RED; dead declaration → RED via dead-entry
  idiom). Uses L1's recorded TARGET filename (flag: extend L1's escape record to carry the compiled target if it
  only has call-site file:line — small, inside the guard). backoff (declared 0, observed whole workspace) dies.
- **Ask 4: fix the false-clear docstring** — distinguish (a) in-scope PARSE (any spelling) CLOSED by L1 from (b)
  #349's NON-parsing walk (pinned bound). Leave the #349 pin (honest). A parse mislabeled as the bound is the
  served-English trust defect this doc exists to kill.
- **Closable via L1: YES** (said so per the lead's ask). **Scope: TEST-ONLY, no scope-grant** (skip allowlist gains
  a budget column; pin re-sourced; docstring fixed; the only possible non-test touch = extending L1's escape record
  to carry the target path, inside the guard). **Reuse:** L1 guard/`report.escapes`/`require_observations` +
  `_ALLOWED_WHOLE_TREE_CLONE_FILES` allowlist+dead-entry, no new machinery.

### Fork 5 — G/#344 round 7 (TERMINAL): pin main's SERVED BYTES over the complete derived outcome domain (ruled 2026-08-09/10, HEAD `e36c114`)

**Source:** lead relayed `delta-adversary-g-5` — §11.9 closed rounds 1..5 (178/0) but two breaks reveal WHY G
recurred: FINDING 2 (recipe/cake — pins reach `render_wave_receipt`'s RETURN; served surface is `main`'s
STDOUT; `main` can `print(alt-wording over-claim)` → exit-0 false clear, 178/0) and FINDING 1 (quantifier law —
domain = `SummaryVerdict.__members__` (3) misses that FAIL has ≥2 receipt shapes; NOT_RUN, the literal #344
event, anchored by nothing). Lead believes terminal; asked me to SAY SO if another served surface exists.

**Ruled → appended design doc §11.10.**

- **Answered the terminal question FIRST (enumerated served surfaces from code):** stdout (`print`), stderr
  (errors only, nonzero branches), exit (pinned MP-1/6). NO receipt file, NO subprocess passthrough
  (`GateRunner` captures `stderr=subprocess.STDOUT` into a PIPE), NO logging surface. ⇒ served surface =
  `{stdout, stderr, exit}`. **TERMINAL — CONDITIONAL on capturing BOTH STREAMS. ⚠ "capsys.out == render"
  (stdout-only) is NOT terminal:** a wrong build could `print(over-claim, file=sys.stderr)` on the exit-0 path
  and survive. Low honest-dev plausibility but free to close (capfd, anchor stderr == ""/diagnostic). Surfaced
  as the completeness gap in the lead's phrasing.
- **The move:** anchor main's SERVED BYTES (capfd, both streams) == the honest golden, ∀ over the complete
  domain (recipe→cake, #131/#107). Subsumes §11.9's render-return oracle.
- **CRUX / round-8 guard:** domain = mode × per-gate verdict over the closed `VERDICT_*` set {GREEN,
  RED_ADJUDICATED, RED_ORPHANED, NOT_RUN} × scoped — FINER than SummaryVerdict (3, F1's under-derivation) AND
  LegQualification (4, conflates RED_ORPHANED+NOT_RUN). Two legs make it a checked variable: (1) verdict-domain
  coverage (reuse §11 `_leg_qual_combos` meta-recursion, re-keyed on `VERDICT_*`: new verdict → reddens) + (2)
  BRANCH-COVERAGE backstop (reuse §11 P-S `coverage.Coverage(branch=True)` over main's stdout path: a new render
  branch no cell reaches → reddens = catches a new SHAPE that isn't a new verdict). Leg 1 = reach; leg 2 = proof
  the reach hit every shape. That pairing is what makes it terminal not round 8.
- **Exact pins:** MP-B `test_main_served_output_equals_the_honest_render_over_the_complete_outcome_domain`
  (capfd both streams, extends the existing main-exit matrix) + MP-A `test_omitted_gate_NOT_RUN_receipt_is_byte_anchored`
  (domain over VERDICT_*, not SummaryVerdict) + the two round-8 guard pins + both-way mutation proofs (print
  over-claim on stdout AND stderr → redden; new VERDICT_* w/o golden → leg-1; new branch → leg-2).
- **NOT a pinned bound** — #344 IS the over-claim; the fix CLOSES it (contrast §12.7's out-of-scope hole).
- **Scope: TEST-ONLY + approved pcg extraction** (a canonical `GATE_OUTCOME_VERDICTS` tuple beside the existing
  `VERDICT_*` is a one-line constant within the extraction; flag if more needed). **Reuse:** the main-exit cell
  harness + `VERDICT_*`/`FAILING_VERDICTS` + §11 meta-recursion + §11 P-S branch-coverage + §11.9 goldens.
  **Packages:** stdlib/pytest built-ins — no new dep.

### Fork 7 — G/#344 round 8 (genuinely terminal): main is a PROVEN pure conduit (#350) (2026-08-10, HEAD `e36c114`)

**Source:** `delta-adversary-g-6` (#350). §11.10 strong (187/0) but 2 exit-0 false clears survive: W-main-empty-selector
(PRIMARY, production-reachable — §11.10's leg-2 branch-coverage drove render (PROXY) not main; byte-oracle fixed
selector non-empty; `--wave` no `-k` is a normal path) + W-compose-multiowned (single-gate domain). Diagnosis
(correct): reach under-derived by one axis each round BECAUSE coverage over a proxy/enumerated-domain, never
main's actual execution. NOT a pinned bound (#344 IS the over-claim).

**Ruled → appended design doc §11.11.** Lead offered (A) branch-coverage-over-main or (B) AST-constrain-main;
asked which or better.

- **RULING: BETTER — the synthesis.** (A) alone NOT terminal (per-cell golden over an enumerated domain = the
  one-axis-short recurrence; composition isn't a per-count branch). (B) alone NOT terminal (AST = spelling-defeatable
  per §12's lesson — `sys.stdout.write`/helper/`os.write` evade). **The terminal form = (B)'s PROPERTY (main is a
  pure conduit) via (A)'s LOCUS (runtime capfd over main's ACTUAL execution), ASSERTION = CONDUIT-EQUALITY**
  (main's stdout == `render_wave_receipt`'s output byte-exact + stderr == expected). Conduit-equality is a SINGLE
  property (not per-axis); it moves the axis-enumeration problem OFF main (unbounded input axes) ONTO render (a
  CLOSED TYPED domain §11.8/§11.9 already anchor). Proven ∀ via branch-coverage over MAIN (not render): an over-claim
  is unconditional (fails every cell), branch-gated (branch driven → fails), or a new branch (coverage reddens).
  Main's completeness = branch-coverage (checked var), NOT axis-enumeration = why it ends the recurrence.
- **Selector axis → typed `scoped` (spec-silence resolved):** derive `scoped = JUnit ∧ WAVE ∧ selector NON-EMPTY`.
  Empty `-k` = honest FULL run → PASS_FULL (folds into the existing scoped bool, NOT a new axis; selector string is
  contained echo). RULED full-run-honest (design authority); FLAGGED the defensive argparse-reject as the operator's
  UX call (honesty secured either way).
- **WHY terminal:** main adds no honesty byte (proven conduit ∀ branches); render's output is a pure fn of a CLOSED
  TYPED domain (fully anchored, typed-field SET a checked variable via §11.8 component coverage); selector = typed
  scoped; composition = symmetric summary over the closed LegQualification presence set (≥2-gate domain) + main
  can't compose. A new axis = a new main branch (coverage reddens) OR a new render typed field (component coverage
  reddens). Nothing after stdout+stderr+exit.
- **Exact pins:** MP-C `test_main_wave_empty_selector_is_an_honest_full_run` + conduit-equality (capfd both streams,
  main==render) + branch-coverage RE-AIMED at main + `scoped`-requires-nonempty pin + ≥2-gate composition domain +
  both-way mutation proofs.
- **Scope: TEST-ONLY + approved pcg extraction** (the scoped-derivation is a small wave_gate.py change; ⚠ 2 flags:
  making the CHECKPOINT main a conduit if it has a free print = small further pcg change; the empty-wave CLI semantics
  = operator UX call). **NOT a pinned bound.** Reuse §11.8/§11.9/§11.10 + capfd + coverage.py — no new dep.
