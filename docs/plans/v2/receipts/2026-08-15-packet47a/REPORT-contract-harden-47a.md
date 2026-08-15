# REPORT-contract-harden-47a — CONTRACT AUTHOR, packet-47a HARDENING wave (3 pins)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations — all 3 operator-approved pins ADDED atop the GREEN 40-pin 47a
  contract; each proven to BITE by scratch discrimination (both-way). The existing 40 stay GREEN.
- **Deviation 1 (satisfiability fix, in scope):** the R2 guard on `_entity_fragment` (PIN A) fires on
  ANY unregistered white-box store with a claiming extension — so my known-correct reference build
  reddened the EXISTING P7 (`TestNamespacing`) + P10a (`TestBatchPathClaimedBranch`), which call
  `_entity_fragment`/`_compose_file_fragments` on `_white_box_indexer`'s unregistered store. FIX:
  `_white_box_indexer` now DERIVES its registered entity-table set from its extensions' declared
  tables (mirroring `build_app_context`). INERT at HEAD; required for satisfiability under the guard.
  See §SATISFIABILITY — the guard's SEAM PLACEMENT is a Fable decision (below).
- **Deviation 2 (scope flag, not fixed):** my bare rename-sweep grep found stale "eleven seams" in
  TEST prose too (`test_extension.py:4,11`, `_extension_helpers.py:22,224`) — NOT flagged by cold-audit
  R3. Individually verdicted as context-scoped (they describe the ORIGINAL 11 seams that module/fixture
  covers, not the framework total), so likely NON-defects — but they need a lead verdict. PIN C stays
  scoped to the SERVED docs per brief. See §RENAME-SWEEP-RESIDUALS.
- **Packages considered:** none — no mechanism specified (contract authoring; no library-backed policy).
- **Reuse ledger:** 1 new production symbol (`ExtensionLifecycleNotReadyError`) — dispositioned
  HAND-ROLLED (search proved no existing lifecycle/not-ready error; mirrors the sibling
  `ExtensionClaimConflictError` idiom). 3 test helpers clone existing patterns deliberately. See §DRY.
- **Graded:** `91fc30e` · HEAD-at-report: `91fc30e` · **SAME** (my 3 files uncommitted on top; lead
  commits). The reference-guard build + all mutations were run in `scratch_copy.sh` trees, provenance
  ASSERTED (`loremaster.__file__` printed — §SCRATCH).
- **Decisions-needed:**
  1. **Fable (guard seam placement):** the R2 guard on `_entity_fragment` forces every white-box
     `_entity_fragment`/`_compose` caller to a REGISTERED store. I fixed the fixture; confirm the seam
     is `_entity_fragment` (brief says so) vs a narrower live-compose-only site. §SATISFIABILITY.
  2. **Lead (rename-sweep residuals):** fix the 4 stale-"eleven seams" TEST prose lines too, or leave
     them (context-scoped)? §RENAME-SWEEP-RESIDUALS.
- Receipt pointers: pins §PINS · scratch discrimination §SCRATCH · "what wrong build?" §WRONG-BUILD ·
  gates §GATES · the fixture-fix tension §SATISFIABILITY.

---

## THE 3 PINS — node id + verdict-now {#PINS}

New file section: `# HARDENING WAVE (packet 47a)` at the tail of
`loremaster/tests/test_ingest_entity_seam.py`. 45 collected (40 + 5). Expected-RED set declared from
`--collect-only` BEFORE the run: {PIN A core, PIN C}.

| pin | node id | verdict-now | binds |
|---|---|---|---|
| **A core** | `TestUnreadyStoreFailFastGuard::test_claimed_file_unregistered_entity_tables_raises_loudly` | **RED** ("DID NOT RAISE") | a claimed file + claimant declares `fake_node` + store registers NOTHING ⇒ `_entity_fragment` RAISES `ExtensionLifecycleNotReadyError` naming the extension (`bookdomain`) AND the missing table (`fake_node`). |
| A pos-ctrl | `TestUnreadyStoreFailFastGuard::test_positive_control_registered_store_composes_and_lands_rows` | GREEN (now & after) | a COVERED store (entity_bench) composes the claimed file + lands its 2 entity rows, NO raise — discriminates an always-raise guard. |
| A ()-leg | `TestUnreadyStoreFailFastGuard::test_empty_tables_claimant_never_triggers_the_guard` | GREEN (now & after) | a `()`-entity-tables claimant (LifecycleProbe) on an EMPTY-registered store never raises — FORCES the guard to be a SUBSET check, not "registered set empty ⇒ raise". |
| **B** | `TestRegisterEntityTablesWiring::test_tier_rebuild_purges_entity_rows_through_the_register_wiring` | **GREEN (mutation-proven)** | through the REAL `build_app_context`, a NON-empty-`entity_tables()` backend's tables register into the store, so `delete_by_tier` co-purges its entity rows (#376/M1). |
| **C** | `TestServedDocsTeachTwelveSeams::test_served_docs_teach_twelve_not_eleven_seams` | **RED** ("eleven seams" present) | `EXTENDING.md` + `README.md` teach "twelve seams", never "eleven seams" (bare anchor-free scan; builder fixes the docs). |

**Files touched (writable set):**
- `loremaster/loremaster/extension.py` — added the inert `ExtensionLifecycleNotReadyError(RuntimeError)`
  STUB (docstring cites #375; NO guard logic — the RAISE is builder logic, Fable owns the form).
- `loremaster/tests/_ingest_entity_fixtures.py` — added `EntityTablePurgeProbeExtension` (a no-arg,
  discovery-constructible ext contributing a real `fake_node` `FakeDomainStore` backend, for PIN B).
- `loremaster/tests/test_ingest_entity_seam.py` — 3 pin classes, helpers `_guard_indexer_and_ctx` /
  `_build_entity_probe_app_context`, imports, and the `_white_box_indexer` satisfiability fix.

I did NOT touch production guard code, the served docs, `index/indexer.py`, `store/surreal.py`,
`server.py`, or any file outside the writable set. No commit (lead commits).

---

## SCRATCH DISCRIMINATION — the folded adversary evidence (REQUIRED) {#SCRATCH}

Blessed scratch copies via `scripts/scratch_copy.sh` (excludes poison, `uv sync --all-packages`,
asserts provenance — #140). **Provenance receipt (the tree under test, PRINTED):**
`loremaster.__file__ = /tmp/harden47a-scratch2/loremaster/loremaster/__init__.py` (INSIDE the scratch
root, not the original checkout). Reference guard applied to the scratch's `index/indexer.py::
_entity_fragment` (pure `(claimant, declared, registered-set)` check raising the typed error). All legs
run against the scratch tree; NO worktrees (standing directive).

| leg | mutation | expected | observed | verdict |
|---|---|---|---|---|
| Satisfiability | CORRECT guard + fixture fix, FULL contract | 44 pass / 1 fail (PIN C only) | 44 pass / 1 fail (PIN C) | **PASS** — the contract is 0-failed-modulo-PIN-C against a known-correct build (PIN C needs the doc fix, the builder's job). |
| PIN A (correct) | CORRECT guard, PIN A class | 3 pass | 3 pass | PASS — guard raises on unready-only, message names both. |
| PIN A (no-op) | guard `if missing:` → `if False:` (drop the RAISE) | PIN A core RED | RED ("DID NOT RAISE") | **PASS** — the RAISE (not just the plumbing) is load-bearing; routing-without-the-raise is caught. |
| PIN B (M1) | `register_entity_tables` body → `_ = entity_tables` (no-op) | PIN B RED | RED (rows survive `delete_by_tier`) | **PASS** — replicates cold-audit M1; PIN B discriminates the register wiring. |
| PIN C (fix) | `EXTENDING.md`+`README.md`: "eleven seams"→"twelve seams" | PIN C GREEN | GREEN | PASS — PIN C is RED-now, satisfiable by the doc fix (reverted; scratch discarded). |

**Both-way declared-vs-observed** (contract runs, from `--collect-only`, not transcribed from output):
at HEAD the FAILED set is exactly {PIN A core, PIN C} — no unexpected reds, no declared-red-that-
stayed-green. The reference-guard run's FAILED set is exactly {PIN C}.

---

## "WHAT WRONG BUILD STILL PASSES THIS?" — PIN A {#WRONG-BUILD}
- **No guard at all** → caught by PIN A core (RED now; the HEAD state). ✓
- **Guard present but never raises** (routing without the decision — the #102/#120 class) → caught by
  PIN A core, proven in scratch (no-op leg). ✓
- **Guard keyed on "store registered set is EMPTY ⇒ raise"** (instead of a SUBSET check) → caught by
  PIN A ()-leg: a `()`-entity-tables claimant on an empty-registered store must NOT raise (∅ ⊆ ∅). A
  "registered-empty ⇒ raise" build reddens the ()-leg while passing the core RED leg. ✓
- **Guard that ALWAYS raises** (breaks the happy path) → caught by PIN A pos-ctrl (covered store must
  compose + land 2 rows) AND by the existing P3/P4/P7/P10a. ✓
- **Guard that raises but with an unhelpful message** → caught by the two substring assertions: the
  message must name the claiming extension (`bookdomain`, distinct from its table) AND the missing
  table (`fake_node`). The distinct name proves BOTH are named, not one masquerading as the other. ✓
- Residual (named): the pin fixes the seam at `_entity_fragment` (per brief). A guard placed at a
  DIFFERENT site (e.g. only `_compose_file_fragments`, skipping the pure helper) would leave PIN A core
  RED — that is the Fable seam-placement decision (§SATISFIABILITY), not a wrong build to catch.

---

## SATISFIABILITY TENSION — the guard vs the white-box pins (Fable decision) {#SATISFIABILITY}

My first known-correct reference guard (on `_entity_fragment`, per brief) reddened TWO existing pins:
`TestNamespacing::test_entity_fragment_params_are_name_namespaced` (P7) and
`TestBatchPathClaimedBranch::test_compose_for_a_claimed_file_emits_an_entity_fragment` (P10a). ROOT
CAUSE: both call the pure white-box `_entity_fragment`/`_compose_file_fragments` through
`_white_box_indexer`, whose store registered NOTHING — which IS exactly the "unready" state the R2
guard forbids. **This is inherent to ANY correct guard on `_entity_fragment`, not specific to my
pins** — so the contract was NOT satisfiable as shipped.

**Fix (in scope — the fixture is mine):** `_white_box_indexer` now DERIVES its registered entity-table
set as the union of its extensions' `ingest_backends(...).entity_tables()` — the SAME union
`build_app_context` computes — so it represents a READY store. Verified INERT at HEAD (no guard →
43 pass / 2 RED unchanged) and satisfying under the guard (44 pass / 1 fail = PIN C).

**Decision for Fable:** confirm the guard SEAM is `Indexer._entity_fragment` (brief's wording, which I
pinned). If Fable instead scopes the guard to a narrower live-compose-only site, PIN A's white-box call
would need to move to that site, and P7/P10a could keep an empty registered set. The brief's explicit
"the shared `claiming_extension` / `Indexer._entity_fragment` seam" is what I built to. This is a
DESIGN property (Fable owns it) — I did not improvise the guard's general form; my reference build only
proved the pin discriminates.

---

## RENAME-SWEEP RESIDUALS — every "eleven"/"seams" hit, individually verdicted {#RENAME-SWEEP-RESIDUALS}

Bare, anchor-free grep `eleven seams|twelve seams` repo-wide (a non-symbol textual seam — grep is the
honest tool per CLAUDE.md; SAID OUT LOUD). PIN C scopes to the two SERVED docs; every other hit:

| file:line | text | verdict | in PIN C? |
|---|---|---|---|
| `EXTENDING.md:77` | `## The eleven seams` | **DEFECT** — framework TOTAL-count claim, now stale | YES (RED) |
| `EXTENDING.md:80` | `property and eleven seams` | **DEFECT** — same | YES (RED) |
| `README.md:136` | `(the eleven seams)` | **DEFECT** — points at EXTENDING.md's total count | YES (RED) |
| `test_extension.py:4,11` | "the eleven seams" | LIKELY NON-DEFECT — describes the 11 seams THAT module tests (the ingest seam is in `test_ingest_entity_seam.py`); a SCOPE, not a total. **Lead verdict requested.** | no (flagged) |
| `_extension_helpers.py:22,224` | "every one of the eleven seams" | LIKELY NON-DEFECT — describes what `FakeExtension` overrides (the original 11; it does NOT override the ingest seam). **Lead verdict requested.** | no (flagged) |
| `docs/design/2026-08-01-dnd-rules-rag-proposal.md:71` | "eleven seams" | NON-DEFECT — dated pre-47 doc naming the gap (cold-audit R3). | no |
| `CLAUDE.md:451` | "all eleven seams" | NON-DEFECT — the #102 `_query` seams, unrelated (cold-audit R3). | no |
| `store/_txn.py:1088` | "ten seams" | NON-DEFECT — conn-error seams, unrelated (cold-audit R3). | no |
| `calibration/…/markdown_prose.md.txt:134` | prose | NON-DEFECT — calibration fixture text (cold-audit R3). | no |

The two TEST-prose clusters are the "tests written before a semantic change certify the OLD world"
class — but here they describe a coverage SCOPE (11 seams), not the framework total, so I read them as
correct-in-context. I did NOT widen PIN C to them (brief scopes PIN C to served docs) and did NOT edit
them (test files describing their own scope are the lead's call). Flagging per scope law.

---

## DRY LEDGER + reuse {#DRY}

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `ExtensionLifecycleNotReadyError` | `lore_search "extension lifecycle not ready … before ensure_ready"` | only the ExtensionContext composition-vs-runtime doc; NO existing lifecycle/not-ready error | **HAND-ROLLED** — no existing error fits; mirrors the sibling `ExtensionClaimConflictError(RuntimeError)` seam-12 idiom. |
| `EntityTablePurgeProbeExtension` (test) | (fixtures file; `LifecycleProbeExtension` read directly) | `LifecycleProbeExtension` has `()`-tables — cannot exercise register wiring | HAND-ROLLED, EXTENDS the LifecycleProbe pattern (real `fake_node` backend); not a fork of policy. |
| `_guard_indexer_and_ctx` / `_build_entity_probe_app_context` (test) | (read `_white_box_indexer` / `_build_probe_app_context` directly) | existing helpers don't expose a controllable registered set / a real-table probe | HAND-ROLLED test scaffolding cloning the existing helper shapes deliberately (test isolation, not shared policy). |

`_white_box_indexer`'s registered-set derivation REUSES `build_app_context`'s exact union logic
(`dict.fromkeys` over `ingest_backends(...).entity_tables()`) rather than a hand-list — the
derive-don't-enumerate ethos.

---

## GATES {#GATES}
- **Contract collect:** 45 tests collected (40 + 5). Expected-RED declared from `--collect-only`.
- **Contract run (real tree, HEAD `91fc30e` + my edits, `-n auto`):** **43 passed, 2 failed** — the 2
  failures are exactly {PIN A core (`DID NOT RAISE`), PIN C (`eleven seams` present)}, both RED for the
  intended reason. The 40 pre-existing pins all GREEN; PIN A pos-ctrl + ()-leg + PIN B GREEN.
- **ruff** (`ruff check` on the 3 touched files): **All checks passed!**
- **typecheck** (`scripts/typecheck.sh`, CANONICAL): total **191** errors (UNCHANGED — the 11
  auth/posture files, #333/pkt-39, RED-adjudicated); **ZERO** errors in any of my 3 touched files →
  zero-new-delta confirmed.
- **Production-edit safety** (I touched `extension.py`): `test_extension.py` + `test_mcp_server.py` =
  **716 passed** — adding the error class trips no structural/hygiene pin.
- **Scratch discrimination:** §SCRATCH (satisfiability + 3 both-way mutation legs, all PASS).

## GREP FALLBACKS (said out loud, per dogfood protocol)
- The rename-sweep `eleven seams|twelve seams` scan is a non-symbol TEXTUAL seam (config/prose) — grep
  is the honest tool (CLAUDE.md case 2). No lore weakness; no finding filed.
- `register_entity_tables`/`build_app_context` wiring anchors in `server.py` were read by line-region
  (a 12.5k-line function `lore` does not profile at statement granularity) — same fallback the 47a
  builder logged; no friction filed.

## HOUSEKEEPING
- **Two scratch trees left at `/tmp/harden47a-scratch` and `/tmp/harden47a-scratch2`** (disposable by
  `scratch_copy.sh` design; the first was superseded by the second after the fixture fix). Safe to
  `rm -rf` — flagging per the don't-abandon-a-worktree discipline (these are scratch copies, not
  worktrees).
- No git state mutated. No lore findings filed (no lore weakness hit). #375 stays OPEN (owned by
  packet 51 per its operator disposition); #376 is CLOSED-IN-EFFECT by PIN B (lead may resolve it).
