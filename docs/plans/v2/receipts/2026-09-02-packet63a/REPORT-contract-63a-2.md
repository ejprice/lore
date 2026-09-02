# REPORT-contract-63a-2 — §10 fork-ruling RIDERS folded into the 63a RED contract

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted AS NEEDED — `docs/reference/surrealdb-31-capabilities.md`. This is a
  contract-EXTENSION task (no new DDL authored); the §4.1 governed overlay DDL is already
  hand-transcribed in the shipped `_governed_contract.py::governed_overlay_ddl` (cited, not
  re-transcribed).

## SUMMARY BLOCK

- Receipt: `brief-base v14 read` · `brief project v7 read`
- State: **done** — the five §10 riders are folded, gate-clean, RED/GREEN-verified for the right reason.
- **RED/GREEN count: `pytest -n auto <7 modules>` → 60 failed / 16 passed** (was 52R/12G over 6
  modules). Delta = **+8 RED, +4 GREEN**, every RED verified RED-for-the-right-reason and every GREEN
  a discriminator GREEN at HEAD *and* on a correct build (§DELTA below names each).
- Deviations (2): **(D1)** the §10.5(ii) tool-layer identity-less twin boots a REAL `AppContext`
  (`build_app_context`, the `test_memory_cutover` pattern) — a duck-typed `self` would TRAP the
  builder if the deny routes through `resolve_subject` (which reads identity stores the builder
  wires into AppContext); the full boot is the only NON-TRAPPING, signature-agnostic surface. RED at
  HEAD is `DID NOT RAISE` (boot succeeds, handler answers) — verified, not a boot error. **(D2)**
  I did NOT run git — the lead commits (§COMMIT; this matches how the sibling contract shipped as
  `ab4b2b3`, and honours brief-base §2 + the standing "lead commits" law; the spawn brief's "Commit
  as ONE concern" is read as specifying the commit's SHAPE — see §COMMIT).
- **Packages considered:** none — no new mechanism specified. Pure test-contract extension folding
  design §10 rulings into shipped 63a tests.
- **Reuse ledger:** 5 new test-only symbols, all dispositioned (§DRY). No production symbol added;
  `loremaster/loremaster/governed.py` UNTOUCHED (no new stub needed — every fold reuses existing
  stubs/PDP/server surfaces).
- Graded: N/A (contract authoring — renders no verdict on another artifact). Authored against design
  `docs/design/2026-08-28-packet63-retrofit-rulings.md` §10 (5 fork rulings + riders) · base
  `feb7a26` (branch `feat/surreal-unification`; `lore_index` watched root `/workspace`).
- Decisions-needed: **1 escalated** — the git-commit authority ambiguity (§COMMIT); no NEW design
  fork surfaced (all five §10 forks were already ruled by the sidecar). One OBSERVATION (a
  per-module test-config duplication — §OBSERVATIONS).
- Receipt POINTERS: rider→pin map → §RIDER-MAP; RED/GREEN delta → §DELTA; mutation-proof plan →
  §MUTATION-PROOF; gate tails → §GATES; commit set → §COMMIT.

## GATES (receipts)

- `uv run ruff check .` → **exit 0** (all checks passed). [fixed one E402 mid-work: the added
  `_F` TypeVar was moved BELOW `import lorerunes as pdp`.]
- `bash scripts/typecheck.sh` → **exit 0** (every leg OK incl. test trees). [fixed mid-work: the
  FORK-1 helper return type `object`→`pdp.Resource`.]
- `pytest -n auto <the 7 63a modules>` → **60 failed / 16 passed** (runnable-RED; passed-count
  present). The 7th module is the NEW `test_pdp_none_scope_63a.py` (the FORK-1 lorerunes pin).
- Regression sweep `pytest -n auto test_agent_capability.py test_agent_capability_seams.py
  test_agent_capability_reach.py test_agent_owns_principal_schema.py test_keeps_schema.py` →
  **139 passed** (the FakeRegistry reshape + the m13 fixture row break NO shipped 60/62 test).

---

## §RIDER-MAP — each §10 rider → the pin that folds it

### §10.3(iii) — FIX the FakeRegistry (a real contract bug the sidecar caught)
- **File:** `_governed_contract.py::FakeRegistry`.
- **Was:** `verify_capability -> tuple[str, str] | None` — the LITERAL shape §10.3 REJECTS ("a fake
  whose signature differs from the real seam is a fake that cannot fail").
- **Now:** mirrors the ruled POST-#425 real seam — `verify_capability -> str | None` (byte-identical
  to the 13-call-site shipped seam) DELEGATING to the shared pair-path
  `_verify_capability_owner(presented, token) -> (agent_id, owner_principal_id) | None` (the ONE
  round-trip `stamp_owner` consumes). `verify_capability` returns `_verify_capability_owner()[0]`.
- **Count delta: ZERO.** The fake is NOT exercised at HEAD (`resolve_subject` is a stub → raises
  `NotImplementedError` before touching the registry), so no RED/GREEN control moved. The reshape
  matters on the CORRECT build: the fail-closed `resolve_subject(FakeRegistry(...))` pins reach the
  real `stamp_owner`, which consumes `registry._verify_capability_owner(...)` — the fake now provides
  it. The #425 pins in `test_425_stamp_owner_63a.py` stay FORM-AGNOSTIC (they count `_query`
  round-trips + assert `owner_principal_of` deleted, never the return shape — left untouched).
- **⚠ Coupling I am folding as RULED (not inventing):** §10.3(iii) elevates `_verify_capability_owner`
  to "the ruled pair-path name". So on a correct build the real `stamp_owner` MUST call a method the
  fake exposes by that name, or the fail-closed substrate pins error (`AttributeError`) instead of
  denying. This is the design's intent ("rename it to the ruled pair-path name; the adversary checks
  fake-shape == real-shape"). The builder must name the real registry's pair-path
  `_verify_capability_owner`. The round-trip pin remains name-agnostic (real registry, `_query`
  count).

### §10.1(ii)(a) — the NEW lorerunes pin (Resource NONE-scope)
- **File:** NEW module `test_pdp_none_scope_63a.py` (store-free PDP unit pins) — placed here (not the
  `lorerunes` test tree, which is outside my writable set; the 63a suite already imports
  `lorerunes as pdp` and pins PDP behaviour).
- **Pins:** `Resource(scope=None)` CONSTRUCTS; for every member Subject READ/WRITE/SET_SCOPE
  `authorize().allowed is False`; admin (`AllRows`) is True for every action; `Resource(scope="")`
  STILL RAISES. The NONE-owner NONE-scope resource makes the member verdict scope-driven for ALL
  members.
- **Typecheck safety:** constructs `Resource(scope=absent_scope())` where the NEW shared helper
  `_governed_contract.absent_scope() -> Any` returns `None` typed `Any` — so the typecheck gate stays
  GREEN at HEAD (`Resource.scope: str`) AND after the widening (no stale `type: ignore`), while the
  RED is BEHAVIOURAL (`__post_init__` → `_is_valid_scope(None)` → `AttributeError`). This is the
  C-DEF-trap avoidance the shipped `python_allowed_ids` already practises, made reusable.

### §10.1(ii)(b) — the F2 DELETE positive control (DELETE is scope-INDEPENDENT)
- **File:** `test_memory_retrofit_63a.py::TestF2DeleteIsScopeIndependentOnDirtyRows` (the F2 oracle
  home) + a new EXACT-OWNER NONE-scope fixture row `m13 = ("alice","ag_a1", None)` in `_HOSTILE_ROWS`.
- **Pins:** (1) a single-brain DELETE oracle over the dirty probe rows — Python `authorize(·,DELETE,·)`
  == store `authorize_filter(·,DELETE,·)`, CONTAINING m13 (the exact owner CAN hard-delete its own
  NONE-scope row — the positive control) and EXCLUDING m12 (an UNOWNED NONE-scope row is not
  universally deletable), and EMPTY for a non-owner; (2) the CONTRAST — the same m13 is READ/WRITE-
  invisible to its owner (scope-dependent) but DELETE-able (scope-independent, 61 D4(a)). Without
  this leg a build that special-cases `None → "deny everything"` passes every READ-only pin.
- The DELETE-over-None Python side uses a dedicated `_delete_allowed_ids` helper (the shipped
  `python_allowed_ids` deliberately SKIPS None rows, so it cannot express this leg).

### §10.2(i) — the routing META-PIN (INSTRUMENT-0) + fail-closed-at-tool-level
- **File:** `test_governed_routing_63a.py::TestEveryRoutedVerbHasABehaviouralObservation` + the shared
  marker `_governed_contract.observes_routing(tool, verb)` (a no-op decorator; its VALUE is the
  AST-visible call), placed on the two behavioural memory routing tests in
  `test_memory_retrofit_63a.py` (F3 recall isolation → `lore_recall` routes through `read_filter`;
  owner-stamp → `lore_remember` routes through the stamp).
- **Pins:** the set of verbs with a behavioural routing test (DERIVED by AST-scanning the test tree
  for `@observes_routing` markers — xdist-safe, pure source AST) ⊇ `_GOVERNED_VERBS_ROUTED`. A verb
  declared routed with no observation is the hidden-constant reach defect. Plus an ANTI-VACUITY pin
  (the scanner FINDS the memory markers — else the meta-pin passes over an empty set).
- **Fail-closed-at-tool-level (§10.2(i)(B)):** confirmed the existing `_dispatch_verbs` already
  fail-closes an unmapped tool to `(tool,)`; the §10.4 discriminator below PROVES it.

### §10.4 — the no-dispatch-table DISCRIMINATOR (tool-level)
- **File:** `test_governed_routing_63a.py::TestTheVerbDerivationIsFailClosedAtTheToolLevel`.
- **Pin:** `_dispatch_verbs("lore_synthetic_ungoverned_tool_63a") == ("lore_synthetic…",)` — a
  governed TOOL with no dispatch table derives EXACTLY ONE verb `(tool, tool)`, never zero. Without
  it D1's per-tool relaxation silently LOSES tool-level orphan detection (a new governed tool would
  VANISH from the derived set). The existing synthetic-VERB discriminator does not cover the TOOL case.

### §10.5(ii) — the tool-level identity-less DENY twin + the shared `capability=` description
- **File:** `test_memory_retrofit_63a.py::TestIdentityLessToolLayerCallsDeny` (+ the `app_context`
  boot fixture) and `::TestTheCapabilityParamDescriptionIsOneSharedConstant`.
- **Pins:** (twin) an identity-less `AppContext.recall("anything")` / `.remember("anything",
  kind="fact")` raises `GovernedDenied` — never a `TypeError`, never the pre-retrofit unfiltered
  answer — at the TOOL layer (the composition root), the twin of the shipped backend-level pins.
  (shared constant) the `capability=` param description is BYTE-IDENTICAL across `lore_recall` and
  `lore_remember` (the packet-45 `_comms_identity_agent_description` idiom), never N copies —
  introspected over the store-free tool schema (`_build_tools`).

---

## §DELTA — the 8 new RED + 4 new GREEN (each RED-for-the-right-reason / each GREEN a discriminator)

**NEW RED (8) — all RED at HEAD for the stated reason (verified):**
1. `test_pdp_none_scope_63a::…::test_resource_constructs_with_a_none_scope` — `Resource(scope=None)`
   raises (`_is_valid_scope(None)` → AttributeError; FORK-1 widening unbuilt).
2. `…::test_a_none_scope_legacy_row_is_scope_invisible_to_every_member` — same raise (constructing the
   resource).
3. `…::test_admin_sees_and_may_act_on_a_none_scope_legacy_row` — same raise.
4. `test_memory_retrofit_63a::TestF2DeleteIsScopeIndependentOnDirtyRows::…delete_filter_is_single_brain…`
   — same raise (Python DELETE side constructs `Resource(scope=None)`).
5. `…::…none_scope_owned_row_is_read_write_invisible_but_delete_able_to_its_owner` — same raise.
6. `…::TestIdentityLessToolLayerCallsDeny::test_an_identity_less_tool_recall_denies` — `DID NOT RAISE
   GovernedDenied` (boot SUCCEEDS, `AppContext.recall` answers identity-less today).
7. `…::test_an_identity_less_tool_remember_denies` — `DID NOT RAISE` (same).
8. `…::TestTheCapabilityParamDescriptionIsOneSharedConstant::…share_one_capability_description` —
   `lore_recall has no capability= param` (the OPTIONAL identity seam is unbuilt).

**NEW GREEN (4) — GREEN at HEAD AND on a correct build; each names the wrong build it reds:**
1. `test_pdp_none_scope_63a::…::test_resource_still_rejects_an_empty_string_scope` — reds a build that
   widens `scope` sloppily to accept `""` (reopening the SEC-F3 forgery door).
2. `test_governed_routing_63a::TestEveryRoutedVerbHasABehaviouralObservation::…finds_the_memory_
   behavioural_markers` — reds a broken AST scanner OR a build that drops the memory `@observes_routing`
   markers (anti-vacuity).
3. `…::test_every_routed_verb_has_a_behavioural_observation` — reds a build that adds a `(tool,verb)`
   to `_GOVERNED_VERBS_ROUTED` with NO `@observes_routing` behavioural test (the INSTRUMENT-0 defect).
4. `test_governed_routing_63a::TestTheVerbDerivationIsFailClosedAtTheToolLevel::…derives_exactly_one_
   verb` — reds a derivation that returns `()` for an unknown governed tool (silent exemption).

**FakeRegistry fix (§10.3(iii)): 0 count delta** (fake not exercised at HEAD — explained in §RIDER-MAP).

---

## §MUTATION-PROOF — how each new pin is proven to discriminate (for the builder/adversary)

Each is mutation-provable AT GREEN (after the builder wires FORK-1 + the substrate). Break the
production code, watch the named pin redden, restore:
- **FORK-1 constructs / invisible / admin-sees:** revert the `Resource.scope` widening → RED (the 3);
  add a `None → server` short-circuit in the member filter → invisible pin RED; special-case
  `None → deny-everything` in `authorize` → admin-sees pin RED (and DELETE pins RED).
- **FORK-1 empty-string control:** widen `_is_valid_scope` to accept `""` → RED.
- **DELETE single-brain / contrast:** special-case `None → deny` in the DELETE branch → owner's DELETE
  denied → Python≠store → single-brain RED, contrast RED; make an owner's READ/WRITE match a
  None-scope row (scope-independent by mistake) → contrast RED.
- **tool-layer recall/remember deny:** make `AppContext.recall/remember` answer identity-less (skip the
  guard) → RED; deny via a bare `TypeError` (required `capability`) → RED.
- **capability= shared constant:** ship N divergent description copies, or add the param to one tool
  only → RED.
- **routing meta-pin:** add a verb to `_GOVERNED_VERBS_ROUTED` without an `@observes_routing` test →
  RED; drop a memory `@observes_routing` decorator → anti-vacuity RED.
- **no-dispatch discriminator:** change `_dispatch_verbs` to return `()` for an unmapped tool → RED.

---

## §DRY — reuse ledger (5 new test-only symbols)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_governed_contract.absent_scope()` | grep `scope is None` / `Resource(scope=None)` in tests + read `python_allowed_ids` | the shipped `python_allowed_ids` DELIBERATELY SKIPS None-scope rows (never constructs `Resource(scope=None)`); no typecheck-safe None-scope helper exists | **HAND-ROLLED** — needed to CONSTRUCT `Resource(scope=None)` without a mypy failure at HEAD, which `python_allowed_ids` deliberately avoids; homed in the shared file for 64 reuse |
| `_governed_contract.observes_routing()` | read `test_governed_routing_63a` (structural pins only) | no routing-observation marker exists; the routing module had only the STRUCTURAL derived-set pin | **HAND-ROLLED** — the machine-readable link between the STRUCTURAL meta-pin and the BEHAVIOURAL memory tests (INSTRUMENT-0's two halves); shared for 63b/63c/64 |
| `test_memory_retrofit_63a._delete_allowed_ids()` | read `python_allowed_ids` | it skips None-scope rows (cannot express the DELETE-over-None leg) | **HAND-ROLLED** (module-local) — the DELETE leg MUST include None-scope rows; a sibling of `python_allowed_ids`, not an extension (different, incompatible predicate) |
| `test_governed_routing_63a._behaviourally_observed_verbs()` / `_observes_routing_args()` | grep `ast.walk` / `decorator_list` in tests | AST scans exist for other purposes (Subject-constructor scan) but none collects decorators | **HAND-ROLLED** (module-local) — the AST collector for the `@observes_routing` markers |
| `test_memory_retrofit_63a._boot_config()` | read `test_memory_cutover._config` / `test_mcp_server._make_context` | each module rolls its OWN config payload; no shared `make_test_config` helper is exported | **HAND-ROLLED** (module-local), MIRRORED from `test_memory_cutover._config` — see §OBSERVATIONS (a shared helper would DRY these, but that is a cross-cutting refactor beyond this fold's writable set) |

---

## §OBSERVATIONS (surfaced, not silently narrowed)

- **Per-module test-config duplication (code-quality, minor).** `_boot_config` re-transcribes ~40
  lines from `test_memory_cutover._config`; `test_mcp_server` has yet another copy. There is no
  shared `make_test_config(slug, root, dim)` helper exported. Extracting one (to a conftest / shared
  test helper) would DRY these — but that is a cross-cutting test-infra refactor OUTSIDE this fold's
  writable set. Flagged for the lead; not filed as a `lore_finding` (it is a test-infra DRY smell,
  not a lore-tool friction). **Fix-now-vs-defer is the operator/lead's call.**
- **The §10.5(ii) tool-layer twin is the heaviest fold** (a real `build_app_context` boot ×2). This
  is deliberate and non-trapping (D1); if the lead prefers a lighter surface, the ONLY sound
  alternative I found (a duck-typed `self`) TRAPS the builder when the identity-less deny routes
  through `resolve_subject`, so I rejected it. The boot is the established pattern
  (`test_memory_cutover`).

## §COMMIT — the lead commits (git-authority decision)

I did NOT run git (brief-base §2: "Never stage, commit, revert, or otherwise mutate git state. The
lead commits."; the standing lore orchestration law "the lead commits"; and the sibling contract
shipped as `ab4b2b3` committed by the lead, whose author read the same brief the same way). I read
the spawn brief's "Commit as ONE concern (…)" as specifying the commit's SHAPE for whoever commits.
**If the lead intends me to commit, that is a one-line instruction and I will.** Ready-to-run:

```
git add loremaster/tests/_governed_contract.py \
        loremaster/tests/test_governed_routing_63a.py \
        loremaster/tests/test_memory_retrofit_63a.py \
        loremaster/tests/test_pdp_none_scope_63a.py
git commit -m "test(63a): contract riders — §10 fork rulings folded (RED)" \
  --trailer "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" \
  --trailer "Claude-Session: https://claude.ai/code/session_013476CgehyfmP7tWP9CGWVg"
```

(REPORT-contract-63a-2.md is archived with the wave per the repo's report-archival law, not committed
into the code concern.)

---

## §NO-NEW-FORK

All five §10 forks were ALREADY ruled by the sidecar (this is the fold, not a re-open). I surfaced no
NEW design fork. The only escalated decision is the git-commit authority above (§COMMIT), and the one
observation (§OBSERVATIONS). The `_verify_capability_owner` name coupling (§10.3(iii)) is folded AS
RULED, not invented.
