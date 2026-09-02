# REPORT-contract-63a-3 — CONTRACT FIX: 4 adversary-found missing pins (packet 63a)

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` §1.8 (UNIQUE over
  `option<>` — a `key IS NONE` row is not matched by `WHERE key=$k`), cited never re-transcribed.

## SUMMARY BLOCK
- Receipt: `brief-base v14 read` · `brief project v7 read`
- **State: done-with-deviations** — all 4 adversary-named pins fixed, gates green; ONE new fork
  surfaced (§FORK below — the §10.5 identity-seam tension, potentially a suite-wide C-DEF).
- Deviations:
  - PIN 1 changes the RED *character* of the 6 existing `retrofit_world` tests (body-RED → setup-
    error RED via the `get_or_create_keyed` stub) — HONEST + adversary/lead-CONFIRMED; details §DELTA.
  - One baseline test (`test_a_hostile_owner_argument_does_not_move_the_stamp`) was a SPURIOUS PASS
    (it swallowed the `capability=` `TypeError` as "no owner param"); PIN 1 converts it to an honest
    setup-error RED-until-built. Net-improvement, not a regression (§DELTA).
  - I did NOT reshape the `_exercise_*` identity seam to §10.5's backend-`subject=` ruling — that is
    a suite-wide change beyond the 4 named pins and changes the adversary-graded baseline. FLAGGED as
    §FORK with the exact edit; my 4 pins mirror the EXISTING `capability=` seam (consistent with the
    whole retrofit suite as graded).
- **Packages considered:** none — no mechanism specified (pure test-contract fix; the design already
  adjudicated the migration verb `bespoke`).
- **Reuse ledger:** 2 new test-local helpers, both dispositioned (§DRY).
- Graded: N/A — I am the contract AUTHOR revising, not rendering a verdict on another artifact.
- **Decisions-needed:** ONE — the §10.5 `capability=`(backend) vs `subject=`(backend) tension
  (§FORK). It admits two readings that produce different builds; may be a latent suite-wide C-DEF the
  adversary's satisfiability bound did not cover. Recommendation inside.
- Receipt POINTERS: the 4 fixes → §FIXES; RED/GREEN delta (re-derived) → §DELTA; mutation-proof plans
  → §MUTATION; the seam fork → §FORK; DRY → §DRY; gate tails → §GATES.

---

## §FIXES — the 4 adversary-named pins → the changes (all in `test_memory_retrofit_63a.py`)

### PIN 1 (C-DEF) — `retrofit_world` mints the project keep BY ITS KEY
- **Change:** in the `retrofit_world` fixture, replaced
  `keep_store.create_keep(keeper_email=alice, type="project", name="lore")` (sets NO `key`) with
  `keep_store.get_or_create_keyed(key="project:lore", type="project", keeper_email=alice, name="lore")`
  (the SF-63-4 verb, `keeps.py::KeepStore.get_or_create_keyed`).
- **Why:** design §2.2 RULES `remember`'s default-scope resolution finds the project keep by ONE
  indexed read `KeepStore.get_by_key('project:lore')`; store law §1.8 says a `key IS NONE` row is not
  matched by `WHERE key=$k`. A `create_keep`-minted (keyless) keep is UNRESOLVABLE by the ruled path
  → `test_a_remembered_note_defaults_to_the_project_keep_scope` was UNSATISFIABLE by a §2.2-compliant
  build (it would have had to resolve by `(type,name)`, the exact path §2.2 rejects). The migration
  module's own `test_the_verb_backfills_the_project_keep_scope` already asserts the project keep is
  `WHERE key='project:lore'` — this makes the two consistent.
- **RED character:** `get_or_create_keyed` is a builder-GREEN stub → the fixture now raises
  `NotImplementedError` at HEAD → every `retrofit_world`-dependent test is a SETUP-ERROR RED at HEAD.
  Confirmed live: `E NotImplementedError: 63a builder: KeepStore.get_or_create_keyed CAS mint
  (SF-63-4)` at `loremaster/loremaster/keeps.py:543`. On a correct build the fixture succeeds and
  every body assertion runs meaningfully. (This is the same RED-until-built shape as the
  `read_filter`/`guarded_write` stubs.)

### PIN 2 (invalidate/supersede coverage) — `TestInvalidateRoutesThroughGuardedWrite` (NEW, 2 tests)
- **Change:** new class exercising the RETROFITTED `backend.invalidate` via a new isolation seam
  `_exercise_invalidate(backend, *, memory_id, capability)` (mirrors `_exercise_remember`).
  - `test_a_member_cannot_close_a_foreign_owned_row` (`@observes_routing("lore_remember",
    "lore_remember")`): alice remembers a default (project-keep) note; bob — NOT householded in the
    project keep — invalidates it → `GovernedDenied` AND `valid_until IS None` (a denied close never
    mutates, single-brain). The behavioural routing observation for the WRITE verb.
  - `test_an_owner_can_close_its_own_row` (positive control): alice closes her OWN note →
    `valid_until` set.
- **The wrong build it catches:** `invalidate(memory_id)` issues a bare `UPDATE … SET valid_until`
  bypassing `guarded_write` (exactly what `local.py::invalidate` does TODAY) → bob's close succeeds →
  no exception (`pytest.raises` fails) AND `valid_until` is set (the `IS None` assert fails) —
  double-caught. The positive control kills a "deny-everything" build (alice's own close would also
  deny). **Scope choice rationale:** a keep-scoped row's WRITE-authorization is household-based
  (`ScopeInKeeps`, `lorerunes/pdp.py:401`) — agent-INDEPENDENT — so the pin discriminates on
  ownership/household regardless of how `owner_agent` is stamped (robust to a build that stamps only
  `owner_principal`). The `@observes_routing` marker is `("lore_remember","lore_remember")` because
  invalidate rides the `lore_remember` WRITE path in the routing model (`_MEMORY_VERBS`,
  `test_governed_routing_63a.py:44`); the meta-pin uses a SET so the duplicate marker is idempotent.

### PIN 3 (`scope=` `_grantable` write-time validation) — `TestExplicitScopeArgumentIsGrantableValidated` (NEW, 2 tests)
- **Change:** new class exercising an explicit `scope=` on `remember`.
  - `test_an_ungrantable_scope_argument_denies_with_a_teaching_error`: alice (householded only in the
    project keep) does `remember(scope=keep:<bob's keep>)` — a keep she is not in →
    `GovernedDenied`, and the message names `lore-adm add-household` (design §2.4 teaching error).
  - `test_a_grantable_scope_argument_is_accepted_and_applied` (positive control): a grantable fixed
    scope (`principal-private`, `_grantable` returns True) is ACCEPTED and the stored row carries
    THAT scope.
- **The wrong build it catches:** `remember` writes the caller's `scope=` verbatim, never calling
  `lorerunes.pdp._grantable` → the foreign-keep note is filed into a keep alice isn't in (cross-keep
  injection). The negative reds a verbatim-write build; the positive reds a deny-all-scope build AND
  an ignore-scope build (stored scope would be the project default, not `principal-private`). This is
  a DIFFERENT injection door than the existing F4 pin (which fuzzes only `owner_principal=`).

### PIN 4 (the tautological served-count pin) — `TestF3RecallServesOnlyTheCallerVisibleSet` (REPLACES the old pin)
- **Change:** DELETED `TestF3ServedCountEqualsServedSet::test_read_filter_count_equals_read_filter_
  set_size` (it built ONE `read_filter` fragment and used it on BOTH the `count()` and the `id`
  listing → `count==size` trivially, a false gate whose docstring promised to red an unfiltered-count
  build it could never see). REPLACED it with `test_recall_serves_the_caller_filtered_set_not_the_
  unfiltered_total` over the REAL `recall`: alice recalls a query matching her 2 visible rows AND a
  bob principal-private row invisible to her; the served set NEVER contains bob's row, is a SUBSET of
  alice's visible texts, is non-empty, and its size is STRICTLY BELOW the unfiltered matching total
  (MEASURED from the store — `SELECT count() FROM memory GROUP ALL == 3`, not a literal).
- **⚠ IMPORTANT REALITY (surfaced, not silently reinterpreted):** memory `recall` reports **no
  separate count line** — `AppContext._render_recalled_memories` (`server.py:4157`) renders one block
  per served row, so the *"separately-computed count over the whole table beside a filtered listing"*
  false clear (as literally phrased for `drain`/`rollup`) **cannot exist in memory recall's
  architecture**. The realizable trust-Leg-1 property for memory is therefore that the served SET is
  the caller-filtered set, size-discriminated against the unfiltered total — which this pin now
  guards honestly. The literal separate-count false clear belongs to comms `drain`/`rollup` (63b/64),
  where a count IS reported; the F3 family runner should carry that leg there. (Not a blocker; noted.)
- **Ranking-robustness (no C-DEF on a correct build):** the load-bearing legs (`gamma not in`,
  `served ⊆ alice_visible`, `< unfiltered_total`) are all ranking-INDEPENDENT — bob's row is excluded
  by the read filter at the SQL level regardless of hybrid-search ordering, and a correct build
  serving 1 OR 2 of alice's rows both pass `< 3`. Only the unfiltered build (serves all 3) reds.

---

## §DELTA — RED/GREEN counts, RE-DERIVED (not inherited)

I re-derived the baseline myself (brief-base: re-derive inherited numbers) by temporarily restoring
the original `test_memory_retrofit_63a.py` from `6dd2600` into place, running, and restoring my
edits from a `/tmp` backup (working-tree content only; git state untouched; restore verified
byte-identical by `diff`).

| set | baseline `6dd2600` | after my fix | delta |
|---|---|---|---|
| all 7 `test_*_63a.py` (`-n auto`) | 60 failed / 16 passed / 0 error (76) | **54 failed / 15 passed / 11 error (80)** | +4 collected |
| `test_memory_retrofit_63a.py` alone | 13 failed / 2 passed (15) | 7 failed / 1 passed / 11 error (19) | +4 collected |

**Every count reconciled (memory module):**
- PIN 1: the 6 `retrofit_world` tests (5 were FAILED, 1 was a SPURIOUS PASS) → all 6 now ERROR
  (fixture `get_or_create_keyed` stub). `failed −5`, `passed −1`, `error +6`.
  - The spurious PASS was `test_a_hostile_owner_argument_does_not_move_the_stamp`: at baseline its
    `try: remember(..., capability=…, owner_principal=…) except TypeError: return` swallowed the
    `capability=` `TypeError` (the retrofit is unbuilt), passing WITHOUT testing anything. An
    honest setup-error RED-until-built is strictly better (adversary residual R5 noted the swallow).
- PIN 4: deleted 1 FAILED (`read_filter` stub) → `failed −1`; added 1 (retrofit_world → ERROR) →
  `error +1`.
- PIN 2: +2 ERROR. PIN 3: +2 ERROR.
- Net memory: `failed 13→7`, `passed 2→1`, `error 0→11`, `collected 15→19`.
- The other 6 modules are byte-untouched (I edited only `test_memory_retrofit_63a.py`), so their
  47 failed / 14 passed is unchanged → total 54/15/11.

**RED reasons spot-verified RIGHT (not bugs in my tests):** all 11 errors are the intended
`NotImplementedError: KeepStore.get_or_create_keyed CAS mint (SF-63-4)` at `keeps.py:543` (setup),
confirmed for PIN 2 and PIN 4 tests directly.

---

## §MUTATION — mutation-proof plan per new pin (for the builder/adversary; I author, I do not mutate)

- **PIN 2** (invalidate routes through `guarded_write`): patch `governed.guarded_write` to always-
  allow (skip the authorize/deny) → `test_a_member_cannot_close_a_foreign_owned_row` reds (bob's
  foreign close stops denying). Proves invalidate ROUTES through the guarded seam, not a bare UPDATE.
- **PIN 3** (scope routes through `_grantable`, §9-rider-3 routing-is-not-sharing): patch
  `lorerunes.pdp._grantable` to `return True` → the foreign-keep DENY vanishes →
  `test_an_ungrantable_scope_argument_denies_with_a_teaching_error` reds. Proves the write-time scope
  validation is the SAME predicate, not a hand-rolled copy.
- **PIN 4** (recall's served set routes through `read_filter`): patch `governed.read_filter` to
  return an unfiltered `("true", {})` → alice's recall serves bob's `gamma` → the `not in` / `subset`
  / `< total` legs all red. Proves the served set is the caller-filtered set.
- **PIN 1** is a fixture-correctness fix (not a mutation pin): its "proof" is that
  `test_a_remembered_note_defaults_to_the_project_keep_scope` becomes SATISFIABLE by a §2.2-compliant
  build — the project keep is now key-addressed (`project:lore`), matching the ruled
  `get_by_key('project:lore')` resolution.

Each new pin interrogated with "what WRONG build still passes this?" — the paired positive/negative
legs (PIN 2/3) and the ranking-robust subset/count legs (PIN 4) leave only the correct build green.
No existing pin was weakened.

---

## §FORK — the §10.5 identity-seam tension (a decision for lead-63; possibly a suite-wide latent C-DEF)

**The two readings (brief-base §2 trigger — one sentence, two builds):** the existing retrofit pins
(and my new ones) call the BACKEND directly with `capability=` — `_exercise_remember` →
`backend.remember(..., capability=capability)`. But design **§10.5 rules the BACKEND
(`LocalMemoryBackend.recall/remember/invalidate`) takes an OPTIONAL typed `subject=` and NEVER a
capability string** ("it must not read the environment"); `capability=` lives at the TOOL layer.

- **Reading A (strict §10.5):** a compliant `backend.remember` has NO `capability=` param →
  `_exercise_*(capability=)` raises `TypeError` on a correct build → the ENTIRE `retrofit_world`
  suite (existing pins + my PIN 2/3/4) is a C-DEF until `_exercise_*` is edited to resolve
  `capability`→`Subject` and call `backend.<verb>(subject=…)`. §10.5 rider (iii) explicitly designs
  `_exercise_*` as the "ONE place the wiring is spelled … a one-function edit" — i.e. the CONTRACT
  AUTHOR makes this edit once the ruling lands.
- **Reading B (contract-observable):** the contract deliberately pins OBSERVABLE behaviour "never the
  wiring", so the builder makes `backend.remember` accept `capability=` and resolve it internally —
  no C-DEF, but this violates §10.5's "backend must not read the environment" layering.

**Why this is unresolved and escalated, not silently fixed:** the adversary's satisfiability bound
explicitly did NOT verify the green side of the un-blocked retrofit pins (`REPORT-adversary-63a.md`
§SATISFIABILITY), so this may be a latent C-DEF it did not cover. Reshaping `_exercise_*` is a
SUITE-WIDE change beyond my 4 named pins and CHANGES the adversary-graded baseline (the adversary
must re-grade the new seam). Picking a reading silently is exactly the §2 defect.

**My recommendation:** Reading A — §10.5 is an explicit ruling ("backend … NEVER a capability
string"), so the §10.5-consistent contract requires `_exercise_recall/_exercise_remember/
_exercise_invalidate` to resolve the capability to a `Subject` (via `governed.resolve_subject`, using
the `retrofit_world` registry/stores + `access_token(subject=email)`) and pass `subject=` to the
backend. It is the designed one-function-family edit. **I can make it now if lead-63 authorizes** (it
touches only `_exercise_*` + the capability fixtures, all in my writable set), OR route it to a
follow-up before the builder. My 4 pins are written to the CURRENT `capability=` seam, so they move
uniformly with the existing pins whichever way this is ruled — no inconsistency introduced.

**One lesser residual (adversary R1/R2 not in my scope):** `_dispatch_verbs`' `{lore_comms→…}` map
(`test_governed_routing_63a.py:53`) is a hidden hand-list and the `@observes_routing` meta-pin
observes a MARKER not the effect-for-that-verb — both latent-for-63b/64, adversary-flagged as
recommend-and-trigger, untouched here.

---

## §DRY — reuse ledger (2 new test-local helpers)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_exercise_invalidate` (test_memory_retrofit_63a.py) | `lore_search("test helper exercise invalidate governed backend capability isolation seam")` | only my own new helper + the sibling `_exercise_remember`/`_exercise_recall` idiom in the same file | **EXTENDED** the FORK-5 `_exercise_*` isolation-seam family (same file, same idiom; the ONE place invalidate's wiring is spelled) |
| `_count` (test_memory_retrofit_63a.py) | (module-local; `_count` already exists identically in `test_governed_substrate_63a.py:328`) | a 1-line `rows[0]["count"]` extractor | **HAND-ROLLED** — test-local trivia (not policy); each 63a module carries its own `_one`/`_bare`/`_count` convenience rather than a cross-module import (matches the file's existing idiom) |

Neither is production/reusable policy — both are private test conveniences.

---

## §GATES — receipts (tails)

- `uv run ruff check .` → `All checks passed!` (exit 0).
- `bash scripts/typecheck.sh` → all members OK incl. `loremaster` (249 files), shellcheck OK (exit 0).
- 60/61/62 regression sweep (keeps/principals/agent-capability/pdp/tool-population/memory-cutover,
  12 modules, `-n auto`) → **392 passed** in 18.41s. No shipped behaviour touched (test-only change).
- 7×`test_*_63a.py` (`-n auto`) → **54 failed / 15 passed / 11 error** (RED contract, as designed;
  §DELTA reconciles every count).

There are 0 failing tests unrelated to our present scope in the sweeps I ran.
