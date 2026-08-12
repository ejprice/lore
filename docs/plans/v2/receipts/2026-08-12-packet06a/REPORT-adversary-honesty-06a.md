# REPORT — adversary-honesty-06a (packet 06a W1+W3 CONTRACT ADVERSARY)

brief-base v12 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — 1 concrete missing pin (a wrong build ships a FALSE served value and survives all 16), plus an operator-mandate gap and a satisfiability-scope overstatement.
- **P1 headline:** a build that HARDCODES the overdue verdict's echoed cadence (`declared ≤2m`, ignoring each agent's own `declared_cadence`) passes ALL 4 W1c+W1d pins — because every fixture agent that *renders* overdue declared exactly `≤2m` (parameter-value monoculture on the ECHO). An agent that declared `≤1h` would render `overdue (declared ≤2m, …)` — a false self-set-contract value, the #104/Consumer-Law trust defect §B.7 exists to prevent.
- **Graded: cca4b49 · HEAD-at-report: cca4b49 · SAME.**
- **Packages considered:** none — I specified no mechanism (adversary). Reference-build reuse noted in body.
- **MISSING PINS (each: the test that should exist + the defect it catches):**
  1. **F-ECHO (BLOCKER):** overdue-verdict cadence-echo derivation is UNPINNED → false served cadence survives. Fix in body §F-ECHO.
  2. **F-DRY (operator-mandate gap):** the `is_blank` reuse (operator ruling 2) is unenforced AND the author's mutation-proof-plan is VACUOUS (proven). Adjudication in §F-DRY.
- **Reach table (P1c):** body §P1c — STALE retirement BOTH callers independently pinned ✓; schema-field OVERWRITE guard ✓; one reach residual (no semantic glyph-ban invariant, F-GLYPH).
- **Quantifier table (P1b):** body §P1b — all 16 invariants classified; every guarded row carries a wrong-build receipt.
- **Fixture-discrimination:** 12 wrong builds tried; 11 correctly reddened their pin (receipts §Probe record). The 1 survivor = F-ECHO.
- **Satisfiability (P4):** reproduced 16/16 GREEN on my INDEPENDENT reference build (provenance-asserted scratch). BUT the same build reddens 2 promise-registry pins outside the 16 (F-REGISTRY) — the author's "All 16 pass" receipt is scope-true, not build-true.
- **RED honesty (P7):** clean collection (1041), W1a RED at HEAD for the right reason (field genuinely absent). ✓
- **Residuals (individual verdicts §Residuals):** F-GLYPH (reach), F-REGISTRY (satisfiability scope), F-SILENT-AGE, F-NOTHING-STORED/TEACHING — all minor/surfaced.

## Capability check
All tools present and used: lore (registered `adversary-honesty-06a`, session `pkt06-20260811`), the store reference (§1.1/§1.4 cited below), `scripts/scratch_copy.sh`, spike-surreal `:18000` (`:18500` NEVER touched), ruff/pytest. No missing capability blocked the mission. lore-first for structure; one bare-grep fallback (SAID: the `⚠ STALE`-literal sweep across the test tree — a non-symbol textual-seam search, the sanctioned grep case).

---

## THE LOAD-BEARING QUESTION, ANSWERED EMPIRICALLY
> If a builder satisfied this contract PERFECTLY but built the render/cadence/retirement/floor WRONG or VACUOUSLY, would the pins still pass?

Mostly NO — the contract is strong on almost every axis I attacked. Exactly ONE wrong build slips through the 16 pins (**F-ECHO**), and one operator MANDATE the contract cannot enforce (**F-DRY**). All probes ran against wrong builds in a provenance-asserted scratch copy.

**Scratch provenance (P0 discipline):** `/home/ejprice/adv06a-scratch` via `./scripts/scratch_copy.sh`; `loremaster.__file__ = /home/ejprice/adv06a-scratch/loremaster/loremaster/__init__.py` (asserted INSIDE the copy, printed in the run). My reference build is INDEPENDENT of the author's `/home/ejprice/pkt06a-scratch`.

---

## §F-ECHO — THE MISSING PIN (BLOCKER): the overdue cadence-echo is a value monoculture

**Defect the contract waves through.** `_render_comms_fleet_row` must render `overdue (declared {cadence}, silent {age})` with `{cadence}` DERIVED from the agent's own `row.declared_cadence` (design §B.7: "derived from typed state (the #104 derived-prose law), never a name-shaped guess"). A build that reads `row.declared_cadence` for the *threshold comparison* but **hardcodes the DISPLAYED cadence** to the constant `≤2m` passes every W1c+W1d pin.

**Why the contract is blind:** every fixture agent that ever *renders* overdue declared **exactly `≤2m`** — the fires pin (`≤2m`), and the monoculture pin where only `fast=≤2m` renders overdue (`slow=≤20m` never renders overdue, so its echo is never inspected). So no pin ever reads the echoed cadence of a non-`≤2m` agent. `test_overdue_fires…`'s `assert "2m" in row` is *also* satisfied by a hardcoded `≤2m`, and `"2m"` is even a substring of `≤20m`.

**Reproduction (wrong build SURVIVES):**
```
WB-HARDCODED-ECHO: cadence=safe_str("≤2m")   # ignores row.declared_cadence in the echo only
  TestFleetRendersOverdueVerdict + TestFleetRetiresTheStaleGlyph  ->  4 passed
```
An agent that declared `≤1h` and went silent 2h renders `overdue (declared ≤2m, silent 2h)` — a FALSE self-set contract on the fleet surface. A consumer acting on it (deciding the agent is only ~4× over vs ~2× over, or trusting the wrong SLA) is wrong in a way the response did not name — a Leg-2 forgery-pin false clear.

**THE PIN THAT SHOULD EXIST** (add to `TestFleetRendersOverdueVerdict`):
```python
async def test_overdue_verdict_echoes_THIS_agents_own_cadence_not_a_constant(self, fleet_ctx):
    caller = await fleet_ctx.register("lead")
    a = await fleet_ctx.register("slowpoke", cadence="≤7m")   # distinctive; NOT a substring of ≤2m/≤20m
    b = await fleet_ctx.register("hasty",    cadence="≤3m")
    await fleet_ctx.backdate_heartbeat(a, seconds_ago=1200)   # 20m > 7m  -> overdue
    await fleet_ctx.backdate_heartbeat(b, seconds_ago=1200)   # 20m > 3m  -> overdue
    rendered = await fleet_ctx.render_fleet(caller=caller)
    a_row, b_row = _fleet_row(rendered, "slowpoke"), _fleet_row(rendered, "hasty")
    assert "7m" in a_row and "3m" not in a_row   # each verdict echoes its OWN cadence
    assert "3m" in b_row and "7m" not in b_row
```
Two agents, DIFFERENT cadences, BOTH overdue: a constant echo cannot be both `7m` and `3m`, and a swapped echo fails too. (`≤7m`/`≤3m` chosen so neither is a substring of the other or of the existing `≤2m`/`≤20m` fixtures.) Secondary: the pin should also assert the *silent* age is each agent's own (kills the F-SILENT-AGE residual in the same stroke).

---

## §F-DRY — the `is_blank` reuse: unenforced AND the mutation-proof-plan is VACUOUS

Operator ruling 2 mandates: *"reuse the lorerunes blankness predicate."* The 16 pins do not enforce it, and — the sharper result — **the author's deferred mutation-proof-plan cannot enforce it either.** Both proven empirically.

**Leg 1 — reuse is UNENFORCED.** A floor that never imports `is_blank`:
```
WB-DRY-noisblank:  if len(body.split()) < _MIN_BRIEF_BODY_TOKENS: raise BriefBodyTooThinError(...)
  TestBriefPublishNonVacuityFloor  ->  7 passed     (is_blank absent from the file)
```
The token check `len(split) < 2` already rejects blank AND whitespace AND single-token, so `is_blank` is redundant under the token reading (F1).

**Leg 2 — the mutation-proof-plan is VACUOUS.** The author's plan (§Mutation-proof plan, W3 DRY bullet): *"mutate is_blank → blank/whitespace #257 pins must RED through the production floor; a private clone stays green."* I built the CORRECT `is_blank`-reuse floor, then mutated `lorerunes.is_blank` to `return False`:
```
is_blank("")=False  is_blank("   ")=False        # mutation confirmed live
  test_blank_body_is_rejected, test_whitespace_only_body_is_rejected  ->  2 passed   (STILL GREEN)
```
The blank pins DO NOT redden, because blank is **double-guarded**: (a) the store's `_NON_EMPTY_STRING_ASSERT` (`string::len(string::trim($value))>0`, store reference §1.4 — the ASSERT class) rejects blank at the CREATE independent of any app floor, and (b) the token check subsumes blank. So the mutation the author proposed to "prove" the reuse shows GREEN for a correct-reuse build, a clone build, AND a no-`is_blank` build alike — a false-clear instrument.

**Adjudication (the brief asked):** A contract reuse-proving pin is **INFEASIBLE for this floor** — blank is store-guarded, so no `is_blank` mutation can redden a blank-rejection pin; and under the token reading `is_blank` is redundant. The honest resolution is **not** "add a pin" and **not** "trust the mutation plan" — it is an **operator escalation**: the "reuse the lorerunes blankness predicate" mandate is *moot* for this floor. Options for the operator/lead: (a) DROP the reuse mandate here and let the token floor stand (blank falls to store + token, both proven); or (b) if the shared predicate must still be called for consistency, accept it as UNVERIFIABLE-by-construction and pin it only by code-audit inspection — never by the vacuous mutation. Either way the current §Mutation-proof-plan line must be struck; shipping it as a "proof" is scaffolding that can lie.

---

## §P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded; every guarded row a receipt)

| # | Invariant | ∀ / guarded | Receipt (wrong build → pin, this session) |
|---|---|---|---|
| W1a | `declared_cadence` = `option<string>`, OVERWRITE, no ASSERT | guarded (offline DDL) | `string`(no option)→W1a RED ✓; +ASSERT→W1a RED ✓; `IF NOT EXISTS`→`_field_statement` RAISES ✓ |
| W1b-1 | cadence persists VERBATIM | ∀ (forced) | drop-store→RED ✓; strip-`≤`→RED ✓ |
| W1b-2 | no cadence ⇒ `None` | ∀ (forced) | default-`""`→RED ✓ |
| W1c-fire | overdue ⟺ declared ∧ age>cadence(VALUE) | guarded — 3 fates | invert→RED (both); hardcoded-const-threshold→monoculture RED ✓; **cadence VALUE→verdict TEXT is UNGUARDED → F-ECHO SURVIVES** |
| W1c-nodecl | no declaration ⇒ never overdue ∀ age | guarded — forced at 1300s ONLY | age-alone→RED ✓. ⚠ forced at ONE age (1300s); a build overdue-by-age only in a window ∌1300s is untested (contrived, noted) |
| W1d-fleet | no `⚠ STALE`/`STALE` at any age, fleet | guarded — >600s (1300s) | partial-retire(undeclared)→RED ✓ |
| W1d-holder | no glyph, holder caller | guarded — >600s (1300s) | forget-holder→RED ✓ |
| W1d-age | age REMAINS after glyph gone | ∀ (forced both surfaces) | drop-age→holder RED ✓ |
| W1e | cadence desc ≥80c names `overdue` | guarded (inputSchema) | terse desc → RED (structural) |
| W3-reject | reject blank/ws/single-token; accept ≥2 tokens | ∀ — all fates forced | char-`len<2`→hello RED ✓; hardcoded `=="x"`→z RED ✓; over-tight→accept legs RED |
| W3-typed | rejection teaches, stores nothing | guarded — "x" ONLY | teaching+nothing-stored pinned for `x` only; z/hello/blank/ws accept ANY Exception (residual) |
| W3-DRY | floor REUSES `lorerunes.is_blank` | **NOT pinned** | **F-DRY: unenforced + mutation-plan vacuous (proven)** |

---

## §P1c — REACH TABLE (per instrument the contract introduces/relies on)

| instrument | reach set | DERIVED or hand-list | coverage a checked var? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| `_field_statement` OVERWRITE guard (W1a) | ONE field `declared_cadence` | targeted-by-name (a per-field pin, not a population scan) | n/a (pins one new field) | observes generated DDL text (effect) | shared helper, #107-mutation-proven elsewhere | **SAFE** — empirically catches required/asserted/INE |
| STALE-glyph retirement (W1d) | BOTH callers of `_heartbeat_is_stale` | **hand-list of 2** (fleet row + holder note) | ⚠ NOT — no scan reddens if a 3rd glyph site appears | observes rendered bytes (effect) | callers pinned SEPARATELY (fleet via live handler; holder via pure render) | **BOTH pinned ✓ (proven: forget-either→RED)**; reach residual F-GLYPH |
| overdue threshold-tracks-value (W1c monoculture) | 2 rows, opposite cadences, SAME age | derived (verdict flips on stored value) | yes — hardcoded threshold reddens | observes render (effect) | reads `row.declared_cadence` | **SAFE for the THRESHOLD** — but the ECHO is a separate surface → F-ECHO |
| cadence-desc payoff (W1e) | ONE param `cadence` in inputSchema | targeted-by-name | n/a | observes served inputSchema (effect) | single param | **SAFE** |

**Legs run:** all reach rows above are EMPIRICAL (wrong build in scratch), except the F-GLYPH residual which is construction-inspection (grep of the test tree + the existing `_PROMISE_REGISTRY` machinery).

**F-GLYPH (reach residual, medium).** The glyph retirement is a 2-item hand-list; there is **no dedicated invariant banning `⚠ STALE` in comms render literals.** A re-introduction (the exact #262 class — the glyph was propagated into a NEW holder-note render *after* #259 ruled it retired) trips the pre-existing `test_every_comms_render_literal_is_classified` (forces the new literal to be *classified*, RED until then) — partial protection — but nothing SEMANTICALLY bans the glyph, so a developer who classifies the re-introduced literal walks past it. Repo law ("every audit-caught defect CLASS becomes a repo-local invariant test") + the #262 precedent argue for a `no '⚠ STALE' literal in any comms render` AST/string-literal scan, failing closed. RECOMMEND the lead route this pin into the builder brief or 06b. (This is NOT strictly the author's writable-set task, but it IS the durable close of the class the packet is retiring.)

---

## §F-REGISTRY — satisfiability scope is overstated (the reference build is not fully green)

The author's satisfiability receipt claims *"All 16 pins pass."* True, and I reproduced it (16/16, independent scratch, provenance-asserted). BUT the reference build's OWN render changes redden **2 pins the 16-pin run never exercised**:
```
test_comms_promise_registry.py::...::test_every_comms_render_literal_is_classified  -> FAIL
    _render_comms_fleet_row:...: '- {name} [{status}] hb {age} · overdue (declared {cadence}, silent {silent}) · {cells}'  (UNCLASSIFIED)
test_comms_promise_registry.py::...::test_no_dead_registry_entries                  -> FAIL
    '- {name} [{status} ⚠ STALE] hb {age} · {cells}'  (DEAD registry entry)
    (2 failed, 118 passed against the reference build)
```
So the FULL green build requires editing `test_comms_promise_registry.py` (classify the new `overdue` literal + the changed holder literal in `_PROMISE_REGISTRY`/`_PROMISE_FREE`; remove the dead STALE entry). The author flagged the dead-entry removal parenthetically (§Old-world inventory item 4) but the **satisfiability RECEIPT does not reflect that the reference build is RED here**, and the classification-of-the-new-literal obligation is not in the Old-world inventory. This is the *"I verified a SCOPE, not a fact"* pattern — the 16-pin satisfiability run is scope-true, not build-true. RECOMMEND: the builder brief must list the promise-registry updates and RUN `test_comms_promise_registry.py`; the C-DEF satisfiability leg must be re-run over the FULL touched-surface set, not the 16.

---

## §Residuals (individual verdicts)
- **F-SILENT-AGE (minor):** the overdue verdict's `silent {age}` VALUE is unpinned (only `"silent"` presence + an age token). A build rendering a wrong silence duration passes. Same monoculture root as F-ECHO, lower stakes (age cross-checkable via `hb {age}`). FOLD into the F-ECHO pin.
- **F-NOTHING-STORED / F-TEACHING (minor):** `nothing-stored` (`get_head`→`UnknownBriefError`) and teaching-quality (`_assert_is_a_teaching_rejection`) are pinned for the single-char `x` body ONLY; `z`/`hello`/`blank`/`whitespace` accept ANY `Exception` (incl. a raw store error for blank/ws). Shared-floor logic makes this low-risk; a store-then-raise or opaque-error build for `z`/`hello` would be caught only via the `x` sibling. Acceptable; noted so it is a DELIBERATE bound.
- **F1 single-token reading (author fork, NOT re-litigated):** the contract pins single-TOKEN (rejects `hello`). I did NOT re-litigate; I VERIFIED the token pins discriminate (char-`len<2` → `hello` RED). NOTE for F1: if the operator picks single-CHARACTER, only `test_a_single_real_word_is_rejected_token_not_char` flips — AND it strengthens F-DRY (under the char reading, `is_blank` is the load-bearing predicate for the blank case, but STILL store-double-guarded, so the mutation-plan stays vacuous either way).
- **F2 old-world STALE tests (author fork):** confirmed OUTSIDE the writable set; correctly the builder's. My REACH-A wrong build (glyph left in holder) is the same surface F2 item 1 covers.

---

## Probe record (commands + real output, this session, scratch `/home/ejprice/adv06a-scratch`)

**P4 satisfiability — my independent reference build (schema+agents+server+briefs), 16/16:**
```
PROVENANCE loremaster.__file__ = /home/ejprice/adv06a-scratch/loremaster/loremaster/__init__.py
  test_declared_cadence... + TestRegisterPersistsDeclaredCadence + TestFleetRendersOverdueVerdict
  + TestFleetRetiresTheStaleGlyph + TestHolderLivenessNoticeRetiresTheStaleGlyph
  + TestCadenceParamDescriptionStatesThePayoff + TestBriefPublishNonVacuityFloor  ->  16 passed
```

**P1/P2 wrong builds — 12 tried; 11 reddened their pin (controls), 1 survived (F-ECHO):**
| wrong build | target pin | result |
|---|---|---|
| WB-DRY-noisblank (no `is_blank`) | all 7 W3 | **7 passed (SURVIVES → F-DRY leg1)** |
| is_blank→`return False` (author's mutation plan) on correct build | blank/ws pins | **2 passed (SURVIVES → F-DRY leg2 vacuous)** |
| WB-char (`len(strip)<2`) | `…single_real_word…token_not_char` | RED ✓ |
| WB-hardcoded-x (`body=="x"`) | `…different_single_token…not_hardcoded_x` | RED ✓ |
| REACH-A retire fleet, forget holder | holder retire pin | RED ✓ |
| REACH-B retire holder, partial fleet | fleet no-decl pin | RED ✓ |
| WB-overdue-hardcoded-threshold | monoculture pin | RED ✓ |
| WB-overdue-age-alone | fleet no-decl pin | RED ✓ |
| WB-schema-required (`string`) | W1a | RED ✓ |
| WB-schema-asserted | W1a | RED ✓ |
| WB-schema `IF NOT EXISTS` (direct `_field_statement` probe) | W1a helper | RAISES ✓ |
| WB-w1b drop / strip-`≤` / default-`""` | W1b persist / none | RED ✓ (×3) |
| WB-w1d age-drop (holder) | holder pin | RED ✓ |
| **WB-HARDCODED-ECHO** (`cadence=safe_str("≤2m")`) | **all W1c+W1d** | **4 passed (SURVIVES → F-ECHO)** |

**P7 RED honesty at HEAD `cca4b49` (main repo, production unbuilt):**
```
1041 tests collected            (clean — no ImportError)
test_declared_cadence...  ->  AssertionError: no DEFINE FIELD statement found for agent.declared_cadence  (RIGHT reason)
```

**Store reference citations (required first read):** §1.4 (a NEW field on the populated `agent` table MUST be `option<>` no-ASSERT — write-poison; a DEFAULT does not rescue a legacy row) and §1.1 (FIELD → `OVERWRITE`; `IF NOT EXISTS` is the #107 silent no-op) — both are exactly what the W1a pin + `_field_statement` guard enforce, empirically confirmed above. The `_NON_EMPTY_STRING_ASSERT` (§1.4 ASSERT class) is the store-side double-guard that makes F-DRY's mutation-plan vacuous.

## Disposal
Independent scratch reference build at `/home/ejprice/adv06a-scratch` (git-untracked, `scratch_copy.sh` provenance-asserted, disposable by design). No git state touched, no production code/tests edited (all wrong builds live in scratch only). **Awaiting lead call: `rm -rf` it or keep for the builder.**

## VERDICT: CONTRACT INSUFFICIENT
≥1 concrete missing pin (F-ECHO: `test_overdue_verdict_echoes_THIS_agents_own_cadence_not_a_constant`) catches a real false-served-value defect a wrong build ships today; F-DRY is an unenforceable operator mandate needing an operator ruling; F-REGISTRY overstates satisfiability. The contract is otherwise STRONG — 11 of 12 wrong builds reddened, both STALE callers independently pinned, threshold monoculture / schema / round-trip all discriminate.

---

# §DELTA PASS (2026-08-11) — re-grade of the FIX WAVE → VERDICT: CONTRACT SUFFICIENT

**Graded:** working-tree fix-wave revisions of `test_comms_schema.py` / `test_mcp_server.py` / `test_brief_ledger.py` (uncommitted) · **HEAD `cca4b49` · SAME (revisions uncommitted).** Re-run empirically in the same provenance-asserted scratch (`/home/ejprice/adv06a-scratch`, `loremaster.__file__ = /home/ejprice/adv06a-scratch/loremaster/loremaster/__init__.py`), test files refreshed to the fix-wave versions, my independent reference build updated to the fix-wave shape (floor=3, no `is_blank`, overdue echoes own cadence+silence, glyph retired both callers).

## SUMMARY (delta)
- **VERDICT: CONTRACT SUFFICIENT — builder-ready.** All 4 of my prior findings are resolved AND their fixes DISCRIMINATE (each new/changed pin reddens the wrong build it exists to catch, with a correct-build control). No new blocker opened by the fix wave.
- **Full-surface satisfiability reproduced HONESTLY: 19 pins + `test_comms_promise_registry.py` → `139 passed`** on the reference build (after the builder's `_PROMISE_FREE` edit — register the overdue literal, remove the dead STALE entry). Matches the author's claim exactly.
- **Residuals (all minor, non-blocking, individual verdicts below):** F-GLYPH reach is a pinned bound not a checked variable (consistent with the pre-existing `_comms_render_literals` instrument; verified no comms render lives outside server.py today); F-GLYPH is a literal scan (honest-dev threat model, not evasion-proof); holder age VALUE unpinned (single-fixture, low risk).

## Fix-by-fix discrimination (every leg empirical, this session)
| fix | correct reference | wrong build → target pin | result |
|---|---|---|---|
| **F-ECHO** | 19/19 green | `WB-HARDCODED-ECHO` (`cadence=safe_str("≤2m")`) → `test_overdue_verdict_echoes_THIS_agents_own_cadence_and_silence` | **RED ✓** |
| **F-ECHO (swap)** | — | echo `≤3m` (hasty's, wrong for slowpoke) → same pin (`"3m" in slow_row`) | **RED ✓** |
| **F-SILENT-AGE** | — | `silent=_render_age(1200)` constant (20m) → same pin (`"20m" in hasty_row`) | **RED ✓** |
| **F1 = 3 tokens** | three-word publishes ✓ | floor=2 → `test_a_two_token_body_is_rejected` | **RED ✓** |
| F1 char-vs-token | — | `len(strip)<3` (accepts `hello`) → `…single_real_word…token_not_char` | **RED ✓** |
| F1 hardcoded-x | — | `body=="x"` (accepts `z`) → `…not_hardcoded_x` | **RED ✓** |
| F1 over-tight | — | floor=4 (rejects `proceed with caution`) → `test_a_three_word_body_publishes` | **RED ✓** |
| **F-DRY** | blank/ws reject pins GREEN with NO `is_blank` in the file | (n/a — vacuity CLOSED: the vacuous mutation line is struck; blank stays rejected by store ASSERT + the ≥3-token check, both proven) | **no vacuity reopened ✓** |
| **F-GLYPH** | scan GREEN (glyph gone both callers) | re-introduce `⚠ STALE` in the overdue render template → `test_no_stale_glyph_literal_in_any_server_string` | **RED ✓** |
| **F-GLYPH fail-closed** | — | AST walk on a docstring-only source → `scanned == 0` (the pin's `assert scanned > 0` FIRES) | **FAILS CLOSED ✓** |
| **F-REGISTRY** | 19 pins green | promise-registry BEFORE builder edit → 2 RED (unclassified overdue + dead STALE); AFTER edit → all green | **honest: 139 passed ✓** |

## RE-ATTACK for new holes (r5 lesson — a fix wave hides a narrow patch)
1. **Did F-ECHO/F-GLYPH open anything?** No. F-ECHO is additive (2 new agents, non-substring cadence/age fingerprints `7m/3m/20m/15m` — each uniquely tags its row; constant AND swap AND silence-constant all fail). F-GLYPH is additive (AST scan). Full 19+registry = 139 green.
2. **F-GLYPH reach honesty (server.py only) — could a `⚠ STALE` literal live in a comms render OUTSIDE server.py?** **VERIFIED NO for the current tree:** all `_render_comms_*` / `_render_holder_liveness_notice` / `_heartbeat_is_stale` live in `server.py`; `render.py` only DEFINES the generic `render_line` helper (no templates); `briefs.py` has no comms render templates. The scan's reach matches the pre-existing `_comms_render_literals` promise-registry scanner (also `server.py`-only). **Residual:** the reach is a PINNED BOUND with a stated re-open trigger, NOT a checked variable — nothing FAILS if a comms render later moves to `render.py`/`briefs.py` and the scan stays `server.py`-only. Legitimate per repo law ("pin the miss" + named re-open trigger) and consistent with the existing instrument, but OPTIONAL strengthening: derive the scanned-module set from the same source as `_comms_render_literals`, or assert `server.py` is the sole module carrying `_render_comms_*`/liveness renders (a coverage-as-a-variable upgrade). Not a blocker.
3. **A third served value on the overdue/holder surface still unpinned?** The overdue verdict serves exactly THREE things: the `overdue` word (threshold, pinned by the monoculture pin), the echoed `declared {cadence}` (pinned F-ECHO), and `silent {age}` (pinned F-ECHO/F-SILENT-AGE). No fourth interpolated value. **Minor residual:** the holder-liveness notice's AGE VALUE (21m) is asserted present (`last seen` + age token) but not value-exact; it is a single-holder PURE render off the shared `_render_age`, so no monoculture and low risk — same class as the pre-existing `hb {age}` render.

## Residuals — individual verdicts
- **F-GLYPH reach (medium-low):** pinned `server.py`-only bound, honest today, re-open trigger stated but not a checked variable. RECOMMEND (optional) sharing the reach definition with `_comms_render_literals`. NOT builder-blocking.
- **F-GLYPH evasion (known bound):** an AST literal scan catches the HONEST re-introduction (#262 was a literal copy-paste) but not a runtime-concatenated glyph (`"⚠ " + "STALE"`). Correct threat model (honest developer, per repo "a gate needs a threat model" law). Acceptable.
- **F-REGISTRY builder obligation:** the `_PROMISE_FREE` edits (register the overdue literal, remove the dead STALE entry) are OUTSIDE the author's writable set — the builder MUST apply them and RUN `test_comms_promise_registry.py` (the C-DEF satisfiability leg is the FULL surface, not the 19). Confirmed present in the author's §FIX WAVE F-REGISTRY builder obligation + Old-world inventory.
- **F2 old-world STALE tests:** unchanged from my prior grade — builder-owned, correctly flagged.

## VERDICT: CONTRACT SUFFICIENT
All prior findings resolved with discriminating fixes; 139-pass full-surface satisfiability reproduced independently; both STALE callers pinned; F-GLYPH class-closer reddens re-introduction and fails closed. Residuals are minor and either pinned-with-trigger or correct-by-threat-model. Builder-ready.
