# REPORT-design-sidecar-04b5-1 — the RENDER-REACH instrument (packet 04b5, Link-5 render-site injection containment)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`,
no #334 flake); registered + drained (empty inbox). This is a DESIGN task (read-only + this
report): I edit no code/tests. I ran **read-only AST/introspection probes** (pasted below,
committed-as-fences per brief-base §1) against the on-disk tree at HEAD to ground every
load-bearing claim; these parse `server.py` bytes and introspect installed models — no store,
no mutation, so no scratch copy / provenance receipt is owed (I built no reference impl —
that is the contract-author/adversary's job, flagged §OPERATOR). lore-first for the render
symbols; **grep/AST is the honest tool** for the `_render_*` universe + interpolation-site
sweep (a cross-cutting structural map — CLAUDE.md dogfood case (c)) — used there and said so.
Tests would hit spike-surreal `:18000` only; I ran none against a store. No lore weakness
forced a route-around; nothing filed.

## SUMMARY BLOCK
- state: **done** — RULED render-reach instrument design, self-attacked, with an operator fork.
- **RECOMMENDATION:** the render half becomes **THREE COUPLED CHECKED VARIABLES over a
  RUNTIME over-drive** — (1) a name-blind **candidate-render universe** derived by the
  *interpolation* property (NOT the `_render_` name prefix, which is itself a six-defeats
  name-list — MEASURED §3), each member DRIVEN or OUT-with-verified-reason; (2) a
  **model-guarded field manifest** so every caller-origin field is tokenised (new field →
  RED); (3) **site/branch observation via stdlib `sys.settrace`** so a door on an un-exercised
  branch (where D1's OWN byte-proven leak lives) reddens. The containment PROOF is runtime
  (`_leaks`), never structural — structural is UNSOUND both ways (MEASURED §2). Plus the 2 D1
  drivers, the OUT-set pinned, and a partition-coherence pin with the error half.
- **Graded:** `4c5930d` (HEAD; the tree both cold audits graded) · HEAD-at-report: `4c5930d` ·
  **SAME**. Every "at HEAD" claim re-derive after the build.
- **Packages considered:** `coverage` / `pytest-cov` — **READ**: absent from the uv env AND
  from `pyproject.toml` deps (probe §P4). Verdict for the branch-observation mechanism:
  **bespoke-on-stdlib** — `sys.settrace`/`trace` (stdlib, verified working §P3) does the job
  with zero new dependency; do NOT add `coverage` for this. `pydantic` model introspection —
  READ (`model_fields`, §P2): **keep** (the field-manifest guard is a `.model_fields` read,
  not a re-mechanise). If the operator prefers `coverage.py` over settrace, that is an
  install-authorization escalation, not a silent hand-roll — surfaced §OPERATOR fork 2.
- **Graded-instrument note:** I graded the reworked contract's render half
  (`test_link5_render_containment.py`) and the two cold audits; verdict CONFIRMS
  coldaudit-04b5-4 D1/D2 and SHARPENS the remedy (the auditor's `_render_*`-prefix universe is
  incomplete — §3).
- **DECISIONS-NEEDED (forks, §OPERATOR):** (1) branch/site-observation MECHANIZED (settrace)
  vs a NAMED BOUND with reviewed required-shapes — settrace is sound-and-closes-D1's-branch
  but is the heaviest piece; (2) `coverage.py` install vs stdlib settrace; (3) confirm the
  code-RAG *file* renders (map/diff/impact) are the B-5 indexed-source-content OUT bound (they
  echo indexed content via `_sanitise_line`, not caller params — MEASURED §3), not the render
  half.
- receipt pointers: what the auditor got right §1 · why structural is unsound (both ways) §2
  (probe §P1) · the universe is not the `_render_` prefix §3 · **THE DESIGN** §4 (pins P-U/P-F/
  P-S/P-N/P-C) · the 2 D1 drivers §5 · **wrong-build attack table** §6 · the BOUND §7 ·
  partition coherence §8 · §OPERATOR · §PROBES (P1–P4, re-runnable).

---

## §1 — WHAT THE AUDITOR GOT RIGHT (adopt, do not re-litigate)

coldaudit-04b5-4 is CONFIRMED on its two load-bearing claims, independently:
- **D1 is byte-real.** `_render_transitive_blockers` (`server.py:4066`) and
  `_render_supersede_result` (`server.py:4131`) render a caller `blocked_by`/`dependents`
  value bare/`safe_str` outside any delimiter, and NO test drives either. I re-read the bodies
  (§5): the residue leak at `:4121` is gated behind `if residue:` and the walked-id leak at
  `:4101` behind `if blockers.ids:` — **the leaks are BRANCH-GATED**, which is why a naive
  single-shape driver would green them.
- **D2-root is real.** Render reach is not a checked variable: `_RENDER_DRIVERS` is a
  hand-picked 12-of-~32, with no enumeration of the `_render_*` universe. B-3 forbids exactly
  this ("reach as a CHECKED variable … an unobserved site is a named gap, not a silent pass").

The auditor's *remedy shape* — "every `_render_*` method is DRIVEN or explicitly
OUT-with-reason; a method in neither ⇒ RED" — is the right **skeleton** and I build on it. But
it has two gaps the auditor did not price, both of which I MEASURED (§2, §3): the
name-prefix universe is itself a name-list (misses serving helpers), and field-level +
branch-level completeness WITHIN a driven method needs more than "it has a driver."

---

## §2 — WHY THE RENDER HALF CANNOT BE STRUCTURAL (measured, BOTH directions)

The brief asks me to solve field-level completeness and offered (a) over-drive, (b) field
manifest, (c) structural seam-routing. **(c) structural is UNSOUND, and I measured why** — this
is the crux the whole design turns on, so it is a receipt, not an assertion (probe §P1):

- **Structural "every bare interpolation is a door" OVER-FLAGS ~40×.** Over `server.py`'s 32
  `_render_*` methods: **102 bare `FormattedValue`s + 23 `sanitise_line`/`safe_str` sites**
  across **22** methods. But ~99% are `id`/`seq`/`number`/`isoformat()`/counts/`status`/
  composed-`Rendered` parts — NOT caller free text. Only **~3** are genuine bare free-text
  doors (`actor` ×2, `memory.text`). A scan flagging all 125 traps the builder into wrapping
  every int and opaque id.
- **Structural keyed on the CONTAINMENT VOCAB is UNSOUND — it MISSES and it OVER-FLAGS
  simultaneously** (this reproduces contract-04b5-2 §R1b's measurement and is why that
  asymmetry is correct):
  - MISSES: the 3 bare-f-string doors carry NO vocab (`actor`, `memory.text`) → invisible.
  - CANNOT DISCRIMINATE: `_sanitise_line` wraps BOTH a door (`subject`, `owner`,
    `created_by`) AND a safe value (`_render_finding_detail:3444` wraps `created_at`, an ISO
    timestamp; scout §2.B "safe (ISO)"). `sanitise_line` is the general control-char guard,
    applied to door and non-door alike. **No name-blind scan can separate them** — the field
    provenance (caller vs system) is not on the value, the type, or the wrapper.
- **Field NAMES drift from PARAM names** (`note`→`last_note`; `created_by`→
  `provenance["created_by"]`; `actor` positional), and locals launder (`x = task.owner`), so
  a name-keyed render scan is unsound the same way the error scan is SOUND (errors interpolate
  the param name directly at the tool boundary; renders take domain objects one layer deeper).

**Conclusion, load-bearing:** caller-origin classification of render fields is not name-blind
derivable — so the containment PROOF must be **RUNTIME behaviour** (drive a forgery, read the
served bytes). Structural has exactly ONE sound use here (a POSITIVE cross-check, not the
oracle): it enumerates the interpolation SITES so we can assert each was OBSERVED (§4 pin
P-S). The thing that becomes a CHECKED VARIABLE is COVERAGE (which methods × fields × branches
the over-drive exercises), not a static door-derivation.

---

## §3 — THE UNIVERSE IS NOT THE `_render_` PREFIX (a name-list, six-defeats)

The auditor's "enumerate every `_render_*` METHOD" keys the reach spine on a **name prefix**,
which is the enumeration antipattern one level up (the SDK-gate/`_query`/receiver-name family
in CLAUDE.md's instrument-lesson table). MEASURED (probe §P1 + grep, §P-probe):

- **Non-`_render_` serving helpers carry caller free text and are MISSED by the prefix:**
  `_format_finding_ref` (`:3261`, `sanitise_line`s a caller `id_or_number`),
  `_task_status_marker` (`:4452`), `_comms_traffic_line`/`_resolved_comms_traffic_line`
  (`:5364`/`:5413`, render `owner`/`actor`/`created_by`), `_comms_identity_teaching` (`:5454`),
  `_comms_footer` (`:5479`), `_resolve_or_acknowledge_many` (`:3274`, serves `str(error)` +
  `actor`). A build that drives every `_render_*` and leaves `_comms_traffic_line` leaking
  passes the auditor's net.
- **Code-RAG renders live in OTHER modules:** `impact.py::_format_rollup`,
  `diff.py::_render_{file,in_flight,function}_section`, `map.py::_render_{symbols,module_line}`.
  I read `map._render_symbols` and `diff._render_file_section` (§P-probe): they render
  **indexed-source CONTENT** (symbol names, `tier:file_path`) via `_sanitise_line`, **not
  caller params** — so they are the **B-5 indexed-source-content OUT bound** (already named in
  the contract's `test_indexed_source_CONTENT_is_held_as_a_fenced_body_only`), NOT the render
  half. ⚠ But note they use `_sanitise_line` (control-char only) on store-derived paths, so
  they are same-line-forgery-blind for indexed content — IN BOUND, not a defect, but the
  design must state the boundary so a future reader does not "helpfully" pull them into the
  caller-param net or, worse, leave a real caller echo there unnoticed (§OPERATOR fork 3).

**Design consequence:** the render universe is derived by a **PROPERTY** — *"an AppContext
method that BUILDS a served string by interpolating a non-constant"* (has a `FormattedValue`
of a non-constant, OR interpolates a `sanitise_line`/`safe_str` result) — scoped to
`server.py` AppContext (where caller-PARAM renders live; the error scan covers all modules for
error sites; map/diff/impact file renders are the B-5 indexed-content bound). This catches the
serving helpers the prefix misses, and it is name-blind.

---

## §4 — THE DESIGN: RENDER REACH AS THREE COUPLED CHECKED VARIABLES

The containment PROOF is a runtime over-drive (`_leaks`); the three checked variables make its
COVERAGE complete. All-or-nothing: any one reddening fails the whole render net (mirrors the
operator ruling + the error scan's pass-iff-ALL). Stated as buildable pins.

### P-U — THE CANDIDATE-RENDER UNIVERSE (method coverage; closes D1, D2-root, new-method)
Derive, name-blind by AST over `server.py`, `_candidate_render_sites()` =
every `AppContext` method whose body contains a `FormattedValue` of a non-constant OR a call
to `sanitise_line`/`safe_str`/`_sanitise_line` whose result is interpolated/returned into a
served string. (This is the §3 property — it INCLUDES `_format_finding_ref`,
`_comms_traffic_line`, `_comms_identity_teaching`, `_comms_footer`, `_task_status_marker`,
`_resolve_or_acknowledge_many`, not just `_render_*`.)
- **P-U.1** Every candidate is in EXACTLY ONE of `_RENDER_DRIVERS` (driven) or `_RENDER_OUT`
  (`{method: (reason, re_open_trigger)}`). A candidate in neither ⇒ RED, named `method`.
- **P-U.2 Non-vacuity** (mirrors error scan's `test_the_scan_actually_sees_...`): the derived
  candidate set is non-empty and contains known members (`_render_task_transition`,
  `_comms_traffic_line`), so a broken derivation reddens rather than vacuously passing.
- **P-U.3 Reverse leg**: every `_RENDER_DRIVERS`/`_RENDER_OUT` key is a real candidate — a
  stale entry (renamed/removed method) reddens (a driver exercising a dead site is a green
  sweep over nothing; the auditor's `test_every_driver_maps_to_a_real_appcontext_render_method`
  is this leg — KEEP + extend it to the candidate set).

### P-F — THE MODEL-GUARDED FIELD MANIFEST (field coverage; closes new-field, un-driven-field)
The over-drive must tokenise EVERY caller-origin field of EVERY model a driven render
constructs — not a "representative" field. A hand-list of fields would go stale (six-defeats),
so the manifest is GUARDED against the model:
- **P-F.1** `_DOOR_FIELDS: dict[type, frozenset[str]]` and `_SAFE_FIELDS: dict[type,
  frozenset[str]]` per rendered model (Task, Finding, Agent, Message, InboxEntry,
  RecalledMemory, and the wrappers). Each `_SAFE_FIELDS` entry carries a reason
  (`id`=system-minted opaque; `status`/`kind`=closed vocab; `created_at`=datetime).
- **P-F.2 Completeness guard:** for every model, `_DOOR_FIELDS[M] | _SAFE_FIELDS[M]` ==
  `{name for name,f in M.model_fields.items() if _is_str_ish(f.annotation)}` (probe §P2 proves
  this introspection works — `str`/`list[str]`/`dict[str,…]` fields all surface). A NEW str
  field on any model → the union ≠ the derived set → RED, naming the unclassified field. This
  is the checked variable: the manifest CANNOT silently miss a field.
- **P-F.3** The driver sets every `_DOOR_FIELDS[M]` member (incl. nested keys, e.g.
  `provenance={"created_by": token}`) to a **DISTINCT forgery token** `FORGERY_i` sharing the
  common `FORGERY_MARKER` (so `_leaks` catches any; the index names the leaking field).
- **P-F.4** The guard recurses into NESTED models the render constructs (a `Task` inside a
  rollup `TaskActivityWindow`): every model instance built by any driver has a manifest entry
  (introspect constructed objects' types). A rendered model with no manifest entry → RED.

### P-S — SITE/BRANCH OBSERVATION (branch coverage; closes the branch-gated door — D1's OWN leak)
The over-drive is only as complete as the SHAPES it runs. A door on an un-exercised branch
(`_render_transitive_blockers`' residue at `:4121`, `_render_supersede_result`' dependents at
`:4160`, `_render_rollup`'s finding-row leg) never leaks its token. Make site-reach a checked
variable:
- **P-S.1** `_render_interpolation_sites()` = every `FormattedValue`/`sanitise_line`/`safe_str`
  interpolation site (file:line) in every DRIVEN candidate. (Structural's ONE sound use — §2.)
- **P-S.2** Run the whole over-drive under **stdlib `sys.settrace`** (probe §P3 — coverage.py
  is NOT a dep, §P4; do not add it). Record every line executed inside each driven candidate.
  Assert every enumerated site was OBSERVED. An un-observed site is a NAMED gap (a branch no
  shape hits) → RED, forcing the shape — this is B-3's "assert EACH was OBSERVED" verbatim, on
  the render half. A tiny explicit exclusion set (a site un-hittable store-free) carries a
  reason (pin-the-miss) — renders are pure today (§7 B-α), so it should be empty.
- **Soundness argument (why P-S + P-F + `_leaks` is complete):** with every door field ALWAYS
  tokenised (P-F.3) and every site observed (P-S.2), any branch that renders a door field bare
  IS an observed site whose shape carried the token → `_leaks` fires. So "no token leaks on any
  shape" + "every site observed" ⟹ no door field leaks on any branch. The over-drive does NOT
  need to know which field a site renders (the undecidable part §2) — only that every site ran
  with all door fields tokenised.

### P-N — NEUTRALISATION + ITS CONTROLS (the behavioural core; KEEP from the reworked contract)
- **P-N.1** `TestEveryRenderLayerDoorNeutralisesAForgery` (KEEP): each driver, driven with the
  forgery, must not `_leaks`. Extend to per-field distinct tokens (P-F.3).
- **P-N.2 Positive control** (KEEP `TestThePositiveControlProvesTheSweepCanFail`): a
  bare-f-string / `repr` reference build makes the sweep FAIL, for the forgery reason.
- **P-N.3 Predicate controls** (KEEP `TestTheContainmentPredicateItselfDiscriminates`): the
  `_leaks`/`_prose_outside_delimiters` predicate strips a value inside each PRODUCTION
  delimiter and NOT a bare/repr one — the C1 probe-needs-a-control law. Already present; sound.
- **P-N.4 Post-seam demotion is caught by RUNTIME, not structural** (validated §6 WB-8): the
  ref-build's `f"- {render_fenced(text)}"` (list-marker breaks the fence) leaks and `_leaks`
  catches it — a structural "routes through the seam" check would pass it. This is WHY the
  proof is runtime.

### P-C — THE OUT-SET IS EARNED, NOT ASSERTED (closes "wrongly-OUT method")
An entry in `_RENDER_OUT` needs a MACHINE-VERIFIED reason, or it is a place to hide a door:
- **P-C.1 `system_only`** (e.g. `_render_age(delta_seconds:int)`): verified by driving it under
  the over-drive and asserting **zero door tokens** appear in its output (if it renders any
  caller field, a token surfaces → the claim is false → RED). "It takes no caller param" is
  proven, not asserted.
- **P-C.2 `pure_composer`** (e.g. `_render_task_listing`, `_render_comms_fleet`): verified
  structurally — every `FormattedValue` in its body is a call to another universe member / a
  seam verb / an int-call / a constant (it interpolates nothing of its own). Its leaves are
  separately driven.
- **P-C.3 `indexed_source_content` / `not_served`**: the B-5 bounds (map/diff/impact file
  renders; `labels`) — each already pinned in `TestTheLink5BoundsArePinned...`; the OUT entry
  points at that pin. RE-OPEN trigger travels with it.

---

## §5 — THE TWO D1 DRIVERS (fall out of P-U; must hit the branch, per P-S)
- **`_render_transitive_blockers`** → `_drive_transitive_blockers`: construct `task` with
  `blocked_by=[token_blocked_by]` AND `blockers.ids` NOT containing that token, so it lands in
  `residue` (hits the `if residue:` branch at `:4115`→`:4121`). ALSO drive a second shape with
  `blockers.ids=[token]` to hit the walked-id leak at `:4101`. P-S makes "did you hit both
  branches" a checked variable (both sites must be OBSERVED).
- **`_render_supersede_result`** → `_drive_supersede_result`: `dependents=[token_dep]`,
  `task_id=token_tid`, `successor_id=token_sid` (all three are caller-supplied and rendered
  bare — `:4153`/`:4158`/`:4160`; note `task_id`/`successor_id` leak on the `not dependents`
  common branch too, so drive both `dependents=[]` and `dependents=[token]` shapes).

Both graduate from "impossible to OUT" (they render caller `blocked_by`/`dependents`/`task_id`)
into DRIVEN, and P-S proves the drive actually exercised the leaking branches.

---

## §6 — I ATTACKED MY OWN DESIGN (wrong builds that still pass → the pins that stop them)

| # | WRONG BUILD that passes a weaker design | caught by |
|---|---|---|
| **WB-1** | A serving helper (`_comms_traffic_line`) leaks `owner`/`actor` but is not named `_render_*` → invisible to a prefix-keyed universe. **MEASURED real (§3).** | **P-U** (universe by interpolation property, not the `_render_` name) |
| **WB-2** | A new `str` field `Task.tags` rendered bare in `task_rows`; a hand-list manifest doesn't list it → not tokenised → no leak. | **P-F.2** (manifest domain == `model_fields` str-set; new field → RED) |
| **WB-3** | `_render_transitive_blockers` residue door behind `if residue:`; driver builds `blockers.ids ⊇ blocked_by` (empty residue) → residue site never runs → token never leaks → GREEN. **This is D1's own leak.** | **P-S** (residue site un-observed → RED) |
| **WB-4** | One shared token for all fields → a leak names no field; a field rendered *inside another field's* delimiter hides. | **P-F.3** (DISTINCT token per (model,field), asserted individually) |
| **WB-5** | Driver tokenises only `owner`; method also renders `subject` bare; `subject` un-tokenised → no leak. | **P-F.1/.3** (tokenise EVERY door field of the model, not a representative) |
| **WB-6** | A real door method dumped in `_RENDER_OUT` with reason "system_only" (false). | **P-C.1** (OUT reason machine-verified: drive it, assert zero door tokens surface) |
| **WB-7** | The settrace/AST site enumeration walks the wrong function → observes nothing → vacuously green. | **P-U.2** + a P-S non-vacuity guard (site set non-empty, contains a known site) |
| **WB-8** | `f"- {render_fenced(text)}"` — routes through the seam but the `- ` prefix breaks the fence (the ref-build hit this). A structural "routes through seam" check passes. | **P-N.4** (proof is RUNTIME `_leaks`, never structural-only) |
| **WB-9** | A `Task` rendered inside a rollup window with un-tokenised door fields → nested leak undetected. | **P-F.4** (manifest recurses; every constructed model instance tokenised) |
| **WB-10** | A caller byte covered by NEITHER the error scan NOR the render net (a served value in a helper that is neither a domain-error construction nor a caller-param render). | **§8 partition-coherence pin** (every served caller byte in exactly one net or a named B-5 bound) |
| **WB-11** | The `_leaks` predicate itself strips too much/little → every verdict a tautology. | **P-N.3** (predicate's own positive+negative controls — already present, sound) |

Every surviving wrong build I could construct maps to a pin above. The two I could NOT close
mechanically are the §7 BOUNDS.

---

## §7 — THE BOUND (what the instrument CANNOT check — PIN-THE-MISS, #137/#138 shape)
- **B-α — store-only render leaks.** The over-drive is store-FREE (domain object → bytes). A
  leak that manifests only with live store state is invisible. **Currently vacuous** — every
  `_render_*` is a pure function of its args (verified: they take domain objects, no store
  read). RE-OPEN TRIGGER: a `_render_*`/serving helper gains a store read → it must be driven
  end-to-end, not store-free.
- **B-β — the module boundary.** The candidate universe is scoped to `server.py` AppContext
  (caller-PARAM renders). A served caller-param render added to another module — outside the
  error scan's domain-error-construction property AND outside map/diff/impact's B-5
  indexed-content bound — is invisible. RE-OPEN TRIGGER: a served caller-param render appears
  outside `server.py`.
- **B-γ — laundering outside the model.** A caller value moved into a local/attr named outside
  any manifest field, from a source P-F doesn't tokenise (the mirror of the error scan's
  bound 1). RE-OPEN TRIGGER: a render reads a caller value under a non-model-field name.
- **B-δ (only if the operator chooses the NAMED-BOUND branch option, §OPERATOR fork 1):**
  branch coverage is by the declared shape-set, not measured — a door on an un-declared branch
  is invisible. RE-OPEN TRIGGER: any new `if`/`match` branch in a driven candidate that renders
  a field. (P-S CLOSES this; this bound exists only if settrace is declined.)

---

## §8 — PARTITION COHERENCE WITH THE ERROR HALF (the all-or-nothing seam)
The two nets must PARTITION the served caller-byte surface with no overlap-gap. State it as a
pin the contract carries:
- **ERROR half** (`TestNoServedDomainErrorLeavesACallerParamUncontained`, AST): every
  construction of a served DOMAIN error (7-base hierarchy) across ALL modules.
- **RENDER half** (§4): every caller-param render site in `server.py` AppContext (P-U universe).
- **B-5 bounds**: config (not a tool param) · indexed-source content (map/diff/impact file
  renders) · older-schema rows · `labels` (not served).
- **COHERENCE PIN:** a served caller byte reaches an agent via exactly one of {a domain-error
  construction, a `server.py` caller-param render site, a named B-5 bound}. The concrete check:
  the render candidate universe (P-U) ∪ the error-construction sites ∪ the B-5-bound renders
  covers the served surface; a served interpolation of a registered free-text param in NONE of
  them is a door (WB-10). This is the "every served-answer caller byte is covered by exactly
  one net, or is an explicit pinned bound" the brief requires. It is the render analogue of the
  partition test that already guards the PARAM universe (`TestTheDerivedPartitionHasNoDoor`).

---

## §OPERATOR — forks (you rule; I recommend)

1. ⚠ **Branch/site observation: MECHANIZED (settrace, P-S) vs NAMED BOUND (B-δ) + reviewed
   required-shapes.** settrace makes branch-reach a genuine CHECKED VARIABLE (closes WB-3,
   where D1's own byte-proven leak lives) with zero new dependency (§P3), but it is the
   heaviest piece of the instrument (a trace harness around the over-drive). The named-bound
   alternative is simpler but leaves "a door on an un-exercised branch" a HOPE guarded by
   review of the declared shapes. **RECOMMEND: MECHANIZE (P-S).** B-3 says "reach as a CHECKED
   variable"; the operator's all-or-nothing draws no line; and the branch is not hypothetical
   — it is exactly where D1 leaks. Per "close what's cheap, PIN what you can't" and settrace
   being stdlib, this is a close, not a pin.
2. ⚠ **`coverage.py` install vs stdlib `sys.settrace`.** coverage.py is absent and undeclared
   (§P4). If you'd rather use the packaged tool (better-tested, less bespoke — the
   packages-over-hand-rolling rule), that is an **install-authorization escalation**, not
   something I decide. **RECOMMEND: stdlib settrace** — the gap is ~15 lines of a well-worn
   stdlib primitive (§P3), the package would be a test-only dev dep for one instrument, and the
   locked-venv rule makes "escalate to install" the correct posture only if you want the
   packaged tool; I do not think this narrow use justifies a new dep. Your call.
3. ⚠ **Confirm the code-RAG FILE renders (map/diff/impact) are B-5 indexed-source-content
   OUT, not the render half.** MEASURED: `map._render_symbols` / `diff._render_file_section`
   render indexed symbol names / `tier:file_path` via `_sanitise_line` (control-char only),
   NOT caller params — so they fall under the already-pinned indexed-source-content bound. But
   `_sanitise_line` is same-line-forgery-blind, so if an attacker can control an indexed
   path/symbol name (a hostile repo the agent indexes), that bound is a live surface, not a
   dead one. **RECOMMEND: keep them B-5 OUT for 04b5** (they echo no caller PARAM), and let the
   #138/packet-39 threat-model review own "attacker-controlled indexed content" — but say so in
   the OUT entry (P-C.3) so it is met deliberately, not silently.

---

## §PROBES — re-runnable instruments (committed as fences per brief-base §1; run at `4c5930d`)

### §P1 — structural render scan over-flags / mis-keys (grounds §2). READ-ONLY AST, no import.
```python
# /tmp/probe_render_structural.py — classify every FormattedValue in each _render_* method of
# server.py. Run from loremaster/loremaster/: `python3 /tmp/probe_render_structural.py`.
import ast, pathlib
SEAM = {"render_attributed","render_fenced","render_line","render_join","render_compose"}
INTCALL = {"len","int","float","abs","sum","ord","min","max"}
NONCONTAIN = {"sanitise_line","safe_str","_sanitise_line"}   # control-char only, NOT containment
tree = ast.parse(pathlib.Path("server.py").read_text())
def call_name(n):
    f=n.func; return f.attr if isinstance(f,ast.Attribute) else getattr(f,"id",None)
def classify(fv):
    v=fv.value
    if isinstance(v,ast.Call):
        n=call_name(v)
        return ("SEAM",n) if n in SEAM else ("INT",n) if n in INTCALL else \
               ("NONCONTAIN",n) if n in NONCONTAIN else ("BARE-CALL",n)
    if isinstance(v,ast.Constant): return ("CONST",repr(v.value))
    if isinstance(v,ast.Name): return ("BARE-NAME",v.id)
    if isinstance(v,ast.Attribute): return ("BARE-ATTR",v.attr)
    return ("BARE-OTHER",type(v).__name__)
for node in ast.walk(tree):
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("_render_"):
        hits=[classify(s) for s in ast.walk(node) if isinstance(s,ast.FormattedValue)]
        bare=[h for h in hits if h[0].startswith(("BARE","NONCONTAIN"))]
        if bare: print(f"{node.name:38} bare/noncontain={len(bare):3}  {bare[:4]}")
# MEASURED @4c5930d: 22 methods flagged; 102 bare + 23 noncontain TOTAL; only ~3 genuine
# free-text doors (actor x2 @3258/4175-4176, memory.text @3562). sanitise_line wraps BOTH
# subject/owner (doors) AND created_at (safe ISO @3444) — no name-blind scan separates them.
```

### §P2 — pydantic model str-field introspection works (grounds P-F.2). `uv run python`.
```python
import importlib
for mod,cls in [("loremaster.tasks","Task"),("loremaster.findings","Finding"),
                ("loremaster.agents","Agent"),("loremaster.messages","Message"),
                ("loremaster.messages","InboxEntry"),("loremaster.memory.backend","RecalledMemory")]:
    k=getattr(importlib.import_module(mod),cls)
    strish=[n for n,f in k.model_fields.items() if "str" in str(f.annotation)]
    print(f"{cls:16}{strish}")
# MEASURED: Task -> id,subject,description,owner,blocked_by,provenance,superseded_by,summary,
# report_path ; Finding -> id,kind,subject,body,area,category,created_by,supersedes,provenance ;
# Agent -> ...,role,model,spawned_by,task_id,checkpoint,last_note ; etc. list[str]/dict[str,*]
# surface too. The field-manifest completeness guard is a `.model_fields` read — feasible.
```

### §P3 — stdlib settrace records per-line execution (grounds P-S; NO coverage.py dep). `uv run python`.
```python
import sys
def target(x):
    if x: return f"walked {x}"      # branch A
    return "empty"                   # branch B
hit=set()
def tr(frame,ev,arg):
    if frame.f_code.co_name=="target" and ev=="line": hit.add(frame.f_lineno)
    return tr
sys.settrace(tr); target(["a"]); sys.settrace(None); print("truthy:",sorted(hit)); hit.clear()
sys.settrace(tr); target([]);    sys.settrace(None); print("empty :",sorted(hit))
# MEASURED: {5,6} vs {5,7} — line-level SITE OBSERVATION is a stdlib primitive. `import trace`
# also present. No coverage.py needed for P-S.
```

### §P4 — coverage.py is absent + undeclared (grounds the Packages line + §OPERATOR fork 2).
```
$ uv run python -c "import coverage"     -> ModuleNotFoundError
$ uv run python -c "import pytest_cov"    -> ModuleNotFoundError
$ grep -niE 'coverage|pytest-cov' pyproject.toml  -> only a COMMENT ("read as coverage"), no dep
# Verdict: a coverage-based branch instrument would be a NEW dep (escalate to install) — the
# stdlib settrace (§P3) does the job with none. bespoke-on-stdlib, minimal surface.
```

### §P-probe — the universe-is-not-the-prefix + code-RAG-is-indexed-content greps (grounds §3).
```
$ grep -nE 'def _(comms_identity_teaching|comms_traffic_line|resolved_comms_traffic_line|format_finding_ref|resolve_or_acknowledge_many|task_status_marker|comms_footer)' server.py
  -> 3261 _format_finding_ref · 3274 _resolve_or_acknowledge_many · 4452 _task_status_marker
     5364 _comms_traffic_line · 5413 _resolved_comms_traffic_line · 5454 _comms_identity_teaching
     5479 _comms_footer   [all carry caller text; NONE matches `_render_`]
$ grep -rnE 'def _(render|format)_' --include=*.py . | grep -v server.py | grep -v /tests/
  -> impact.py:_format_rollup · diff.py:_render_{file,in_flight,function}_section ·
     map.py:_render_{symbols,module_line}   [code-RAG renders — read: indexed content via
     _sanitise_line, NOT caller params -> B-5 indexed-source-content OUT bound]
```
