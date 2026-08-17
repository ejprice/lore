# DESIGN — #144 full-statement-validation posture (packet 07)

**Author:** fable-sidecar-07 (design sidecar) · **For:** contract-author-07 · **Date:** 2026-08-17
**Ground truth:** HEAD `82e2587`, spike-surreal `3.2.4` (`3.2.4+20260803.93ab219`)
**Consult ref (comms):** directive #5005, thread `q:pkt07-144-posture`
**Status:** recommendation. The operator owns importance; this is a mundane property-to-invent (pin shape), so I decide-with-recommendation rather than escalate — see §4 for the one thing that WOULD be an operator fork.

> ## ⚠ CORRECTIONS (2026-08-17, post-adversary — apply before trusting any span below)
> Two claims in this doc's ORIGINAL text were wrong and are corrected in place; a retrieval chunk
> arrives without this header, so each occurrence below is also fixed at the sentence, not just here.
> **Authoritative current records: `REPORT-adversary-07.md` §F1 · `REPORT-contract-author-07.md` §9.**
> 1. **The "5 scattered per-module pins" count is a FABRICATION (my error).** There is **exactly ONE**
>    such pin — `test_floor_calibration_schema.py::TestNoMultiStatementDdlRidesABareQuery`, covering
>    `floor_calibration.store` + `lease`. The `comms_schema`/`message_ledger` mentions are **docstring
>    prose** about the statement[0] fact; the `graph_surreal` "bare query" hits are **unrelated
>    bare-NAME-vs-FQN** symbol lookups. I inflated an un-derived count off contract-author-07's #5005
>    phrasing (itself wrong) and it PROPAGATED — the exact un-derived-count defect this repo has the
>    most receipts against. Re-derived independently by me (grep of the whole test tree) and by
>    adversary-07 (F1): ONE.
> 2. **The new offline leg is NOT the "subsumer / strict superset" of that pin.** It is NARROWER in
>    three dimensions (it ignores `query_raw`; it ignores single-statement *direct* `.query()`; it
>    only sees STATIC multi-statement literals, not runtime-composed ones). **The actual subsumer of
>    the one pin's route-through-seam coverage is the PRE-EXISTING retry-escape lint/guard**
>    (`_unseamed_sdk_call_sites` + the receiver-blind autouse runtime guard), which already bans every
>    SDK call outside the driver across all `_talks_to_surrealdb` modules (floor_cal + lease included).
>    Deleting the one pin is safe on the current tree (adversary-verified) but must be **re-adjudicated
>    deliberately** — accept-with-note the old pin's `not-self`→`_is_connection_receiver` receiver-breadth
>    narrowing — not asserted.
> 3. **§6 (item 4) is RETRACTED — see the header on §6.** The branch is LIVE on 3.2.4; my
>    inverse-unreachable-pin recommendation was built on a false-negative premise.
>
> The two-leg RECOMMENDATION itself (add a runtime single-statement assertion + a derived-reach offline
> leg) was operator-ratified (#5010) and stands; only the count and the subsumer claim were wrong.

This doc supersedes the pin-mechanism sketch in `REPORT-fable-sidecar-07.md` §1, which pre-dated
contract-author-07's ground-truth of the *existing* guard landscape (the **one** pre-existing
multi-statement pin + the autouse `_sdk_guard` + the retry-escape lint). The posture conclusion is
unchanged; the mechanism is now grounded in what already exists.

---

## The fork (as ground-truthed by contract-author-07)

The invariant at issue: *a multi-statement string must never ride the SDK's bare `.query()`* (which
validates statement[0] only — §3 of the store reference; the #124/#144 mechanism), *only
`execute_transaction`/`execute_read_transaction`* (which ride `query_raw` and verify every statement).

**Live state:** no defect. Every production multi-statement `BEGIN…COMMIT` already routes through
`execute_transaction`; every bare-`.query()` prod site is single-statement. The gap is a
*hypothetical future* multi-statement-through-a-bare-`.query()` helper.

**But the invariant's dedicated pin is keyed on a NAME-LIST of modules.** ⚠ [CORRECTED — see header
#1: there is exactly ONE such pin, `TestNoMultiStatementDdlRidesABareQuery`, scanning
`floor_calibration.store` + `lease`; the once-claimed `comms_schema`/`message_ledger`/`graph_surreal`
"separate pins" DO NOT EXIST.] There is no package-wide derived guard for the multi-statement-literal
property specifically. That name-list reach is the exact instrument-lesson antipattern (`CLAUDE.md`:
"reach is a checked variable, not a hand-list"). (The pre-existing retry-escape lint/guard DOES cover
these modules by derived reach — header #2 — but for the broader route-through-seam property, not the
narrower "no multi-statement literal in a bare `.query()`" property this fork adds.)

- **Option A** — a derived-reach guard for the multi-statement-literal property: no bare `.query()`
  gets a multi-statement string; reach = checked variable over every module that calls bare `.query()`.
  Likely GREEN at HEAD (documentation-of-bound + regression-prevention, not a defect fix). Variant:
  extend the autouse `_sdk_guard` to flag an internal `;` in a bare-query statement (runtime reach =
  the guard's already-checked variable).
- **Option B** — document the bound narrowly (single-statement `.query()` is safe) + store-ref note;
  accept the ONE per-module pin. Cheaper; leaves that pin's reach a name-list.

contract-author-07's lean: B + one consolidated pin (importance LOW, no live defect).

---

## RECOMMENDATION — Option A in its CHEAP form: extend the autouse runtime guard, then DELETE the ONE per-module pin

**Not** the expensive reading of A (a bespoke package-wide AST guard). The right instrument already
exists and already has the reach: the autouse `_sdk_guard` (the retry-escape guard,
`TestNoSdkCallEscapesTheDriverAtRuntime` family) **already observes every bare `.query()` call at
runtime** — that is its entire job, and its coverage is already a checked variable
(`test_every_production_sdk_call_site_was_OBSERVED_by_the_guard`). Add ONE predicate to it: *when a
bare `.query()` (NOT `.query_raw()`) is observed, assert its statement is single-statement.* Then
retire the ONE `TestNoMultiStatementDdlRidesABareQuery` pin — its route-through-seam coverage is held
by the pre-existing retry-escape lint/guard (header #2), and this new leg adds the narrower
multi-statement-literal property on top. (Deletion re-adjudicated deliberately, not asserted.)

### Why A-cheap beats B, at nearly B's cost
1. **It's barely more than B.** The guard already intercepts every bare `.query()`; the addition is
   one predicate + a stated-bound detector. This is NOT the heavy package-wide-AST reading that made
   A look expensive.
2. **It FIXES the defect the ground-truth surfaced instead of accepting it.** B *keeps* the hand-list
   reach; A-cheap *replaces* it with derived reach. The instrument lesson is explicit that a
   name/prefix/hand-list reach is a latent defect regardless of whether it's currently green.
3. **Net simplification — ONE IMPLEMENTATION.** The ONE name-list-keyed pin → one derived-reach
   guarantee. A fix that deletes a name-list-keyed pin in favour of derived reach is the right kind.
   (⚠ CORRECTED: an earlier draft said "five scattered pins → one guarantee" — a fabricated count;
   see header #1.)
4. **Derived reach demonstrably catches what the hand-list omits.** The bare-`.query()` bootstrap
   `DEFINE NAMESPACE`/`DEFINE DATABASE` (`_txn.py:1099/1115`) are single-statement sites that a
   "scout + inbox_awaiter" hand-list does not name. A runtime guard that observes every bare
   `.query()` picks them up for free. **⚠ Contract-author action:** VERIFY the guard's observed set
   actually includes the bootstrap `DEFINE` path. If it does → concrete proof derived-reach > the
   hand-list. If it does NOT → that's a live coverage gap in the guard, which is itself the argument
   for making reach a checked variable rather than trusting a hand-list. Either outcome argues A-cheap.
5. **Reach-attack STOP-rule does NOT fire.** This is not a receding-reach spiral (hidden constant
   relocating one level deeper each round). It's a single, converging consolidation:
   hand-list → checked-reach runtime guard, one round, done. No multi-agent pipeline. The STOP-rule's
   "accept a pinned bound, don't run another round" applies to adversarial-only surfaces mid-spiral —
   not here.

### The detector (allowlist the safe, state the bound)
- Enforce the POSITIVE property: *exactly one top-level statement.* Do **not** key on the literal
  `BEGIN` — that is "enumerate the forbidden" (defeated by a `;`-joined non-`BEGIN` pair, which also
  hits the gap). contract-author-07's "internal `;`" check IS the positive form (one statement ⇒ no
  internal statement separator).
- **Packages-first:** before hand-rolling a `;`-tokeniser, check whether the installed `surrealdb`
  SDK exposes a statement splitter/parser (read the installed signature/source, not just docs — the
  #107 class). A hand-rolled SurrealQL statement splitter is a mini-parser; do not build one unless
  nothing exists. If nothing exists, the internal-`;` predicate (strip trailing `;`, then any
  remaining `;` ⇒ multi-statement) is the minimal honest detector.
- **STATED BOUND + re-open trigger** (per WHEN-YOU-CANNOT-CLOSE-A-HOLE-PIN-IT): the internal-`;`
  detector false-positives on a single statement carrying a `;` inside a string/backtick literal. No
  current bare-`.query()` site does this. Re-open trigger: *the day a bare-`.query()` site
  legitimately needs a statement literal containing `;`* — at which point the correct move is bound
  params or `execute_transaction`, not loosening the guard. This is a KNOWN, BOUNDED residual, not an
  unbounded forbidden-set — it passes the reach-attack question ("what multi-statement string would
  this wave through?" → only one with a `;`-bearing literal, which is named and triggered).
- **Scope the assertion to `.query()` only, never `.query_raw()`.** `query_raw` validates every
  statement, so a multi-statement `query_raw` is the *safe* path (it is what `execute_transaction`
  rides). Constraining it would be wrong.
- **Mutation proof:** add a `BEGIN;…;COMMIT;` string at a bare-`.query()` site in a `scratch_copy.sh`
  copy → the guard goes RED. Hand the detector to the contract-adversary with the explicit REACH
  ATTACK question.

### Fallback (crisp, so the builder isn't stuck)
If extending `_sdk_guard` proves to entangle with `query_raw` routing, or the detector balloons past
a one-line predicate into a real parser, **fall back to B** (narrow doc + store-ref note) **and file
the ONE per-module pin's name-list reach as a finding** with the named re-open trigger "consolidate to
derived reach when a bare-query helper is next added." Do **not** build a bespoke package-wide AST
guard — that expensive reading of A is what right-sizing rejects. Ordering:
**A-cheap (extend runtime guard + retire the ONE per-module pin) > B > A-expensive (new AST guard).**

---

## §4 — The #124 `generate_ddl`-coverage pin: KEEP IT DEFERRED, do not fold it in

contract-author-07 asks whether #124's owed "every write-target `DEFINE`d before first write"
coverage pin belongs in this #144 settlement.

**Recommendation: keep it deferred with #124; do NOT bundle it into #144.**
1. **#124 was operator-DEFERRED on 2026-07-14.** Pulling its owed instrument back into scope
   *now* re-opens an operator scope decision — that is the operator's call, not the contract
   author's and not mine. Deferral IS a scope decision; scope belongs to the operator.
2. **It is outside the #144 packet scope as written.** The packet says amend #124's *row* (mechanism
   correction) + verify the classifier — a diagnosis/documentation correction. The DDL-coverage pin
   is a different concern (table-declaration-before-write hygiene), not the `.query()`-vs-
   `execute_transaction` validation posture #144 settles.
3. **Right-sizing:** bundling an operator-deferred instrument into an unrelated low-importance
   settlement is scope creep.

**BUT — preserve the deferral's STRUCTURE when you amend #124's row** (which #144 DOES own). The
mechanism correction must not accidentally bury the surviving conclusion-obligation. When you rewrite
#124's body, keep an explicit line: *"CONCLUSION stands (declare every write-target before first
write, on two measured reasons incl. the undeclared-edge `TYPE ANY` downgrade); the coverage-pin
instrument for it remains operator-DEFERRED since 2026-07-14 — re-open trigger: operator
re-prioritisation or a new undeclared-table incident."* That keeps a named owner + decision point per
the deferral law, so "mechanism corrected" never reads as "the whole of #124 is closed."

**If the lead/contract author believes the coverage pin should be pulled in NOW, that is an OPERATOR
fork** (it re-opens a deferral) — surface it with a recommendation, don't decide it in-packet. My
recommendation to the operator, if asked: keep deferred (no live incident, unrelated to the
classification posture this packet ships).

---

## §5 — Follow-up sharpenings (contract-author-07, 2026-08-17): guard mechanics + the two-leg question

Grounded by reading the existing retry-escape guard at HEAD `82e2587`
(`loremaster/tests/test_retry_seam.py`).

### (1) How the `_sdk_guard` extension distinguishes a legit `query_raw` txn from a bare-`.query()` multi-statement escape — BY METHOD NAME, not by parsing intent.

The runtime guard instruments the REAL SDK connection object and records every call **with the
method name it intercepted** — `TestNoSdkCallEscapesTheDriverAtRuntime` already asserts
`[escape.method for escape in report.escapes] == ["query"]` (:2404), and its own comment (:2323-2324)
states: *"The TRANSACTIONAL path too (`query_raw`) — a different SDK method on the same object, and
the runtime gate does not care which: it is a call on a connection."* So the guard SEES `query`
vs `query_raw` for free.

**The distinction is therefore trivial and needs no string-intent-guessing:**
- `execute_transaction` → `_txn_query_raw` → `connection.query_raw(statement, params)` (`_txn.py:1489`)
  → method is **`query_raw`**, which validates every statement → **EXEMPT** from the single-statement
  constraint. A multi-statement string here is CORRECT.
- A bare-seam escape → `connection.query(<multi-statement>)` → method is **`query`**, which validates
  statement[0] only → the single-statement assertion **FIRES**.

The seam's CHOICE of SDK method IS the signal. Do not try to tell "legit vs escape" from the string;
key on `query` vs `query_raw`, which the guard already observes.

⚠ **One correctness note the builder must get right:** the single-statement property is ORTHOGONAL to
the driver-escape property. A `.query()` call can be *correctly seamed* (inside `retry_on_conflict`)
and STILL carry a multi-statement string — that is still the #144 bug. So the new check must observe
**every** intercepted `query` call and inspect its statement argument, NOT only the calls the guard
already flags as escapes. Same interception point (the guard wraps every method on the connection), a
SECOND independent assertion: `method == "query"` ⇒ `args[0]` is single-statement.

### (2) YES — a derived-reach offline/AST leg SHOULD accompany the runtime leg. MIRROR the existing two-leg structure. (⚠ CORRECTED — this leg is NOT "where the scattered pins consolidate"; see header #1/#2.)

The retry-escape guard is deliberately **two legs**, and the reason is exactly the single-statement
property's blind-spot problem:
- **Offline/AST lint** — `TestNoProductionCodeCallsTheSdkOutsideTheSeam::test_every_sdk_call_site_is_run_by_the_retry_seam` (:2066), driven by `_unseamed_sdk_call_sites()` with a **derived-reach** deny-by-default scan (`_talks_to_surrealdb`, probed SAFE set). Its docstring: *"kept because it is instant, it names the site, and it can see code that never executes (which the runtime gate cannot)."*
- **Runtime invariant** — `TestNoSdkCallEscapesTheDriverAtRuntime` (:2294): *"the lint covers all code weakly, the gate covers executed code absolutely"* (:2304), with `require_observations` as coverage-as-checked-variable.

The single-statement invariant has the SAME split: the runtime leg only sees `.query()` calls actually
EXECUTED with the strings they are driven with (a bare-`.query()` site in an untested branch, or one
driven only with single-statement strings in tests but multi-statement in prod, escapes it); the AST
leg sees a static multi-statement literal at a `.query()` site even in an untested branch (but is blind
to runtime-composed strings and defeatable by spelling). **They close each other's blind spot.**

**Why the offline leg is worth adding (⚠ CORRECTED reasoning — the original "preserve the scattered
pins' coverage" argument rested on the fabricated count; the real reason is narrower and still holds):**
the offline leg checks the multi-statement-LITERAL property *statically*, closing the runtime leg's
untested-branch blind spot for THAT property (a bare-`.query()` site in a branch no test executes, or
one driven only with single-statement strings in tests). It is NOT the subsumer of the ONE
`TestNoMultiStatementDdlRidesABareQuery` pin — that pin's route-through-seam coverage is already held
by the pre-existing retry-escape LINT (`_unseamed_sdk_call_sites`, itself offline; header #2). The
offline leg must **reuse that existing derived-reach enumeration** (`_unseamed_sdk_call_sites` /
`_talks_to_surrealdb`), adding the multi-statement-literal predicate on `query` args — NOT a new
hand-list, NOT a new AST walker (ONE IMPLEMENTATION). Net effect: the ONE name-list-keyed pin retires
into 1 derived-reach AST predicate + 1 runtime predicate.

Right-sizing check (importance LOW): two legs is proportionate here precisely because the two-leg
STRUCTURE already exists for this exact SDK surface — marginal cost is one predicate per leg plus
retiring the ONE pin (route-through-seam coverage preserved by the retry-escape lint; the deletion
re-adjudicated deliberately, header #2). If the operator still wants to trim to one: the RUNTIME leg is
where the invariant "lives" (guard's own framing) — but then keep an OFFLINE check for the
multi-statement-literal property (do not lose offline coverage of that property without an offline
replacement).

**Controls (a probe needs a control) — mirror the guard's existing ones (:2382 positive, :2406
negative):** each leg needs a POSITIVE control (shown FIRING on a real `.query(BEGIN;…;COMMIT;)`) and a
NEGATIVE control (a legit multi-statement `query_raw` via `execute_transaction` is SPARED; a
single-statement `.query()` is SPARED). Hand both legs' detectors to the contract-adversary's REACH
ATTACK: *"what multi-statement string would this wave through?"*

### (3) #124 `generate_ddl`-coverage pin — DEFERRED (unchanged from §4). 
Keep it deferred with #124 (operator deferred 2026-07-14; pulling it in re-opens an operator scope
decision). The #144 settlement's #124-row amendment carries it forward as a named still-open item
(conclusion stands / instrument deferred / re-open trigger) so "mechanism corrected" ≠ "#124 closed".
Full reasoning in §4.

---

## §6 — Item 4: `_ERROR_CLASS_QUERY_TOO_COMPLEX` classifier branch

> ## ⚠⚠ §6 IS RETRACTED (2026-08-17) — DO NOT ACT ON IT. The premise ("branch DEAD/unreachable on
> 3.2.4") was a FALSE-NEGATIVE from PROXY-operator probe shapes. **The branch is LIVE on 3.2.4.** The
> real BM25 `@@` fulltext RRF query STILL trips the parser recursion-depth limit at ~120 clauses
> (finding #66's boundary) — parser recursion is NOT operator-agnostic (the `@@`/`search::score`
> subtree is far deeper per clause than `OR`/parens/`v=i`, which tolerate 40000). The existing live
> tests `TestResidualRejectionStillLaunders` (test_surreal_store.py) + `TestRecursionDepthClassificationAtRecallSeam`
> (test_memory_backend.py) PASS on 3.2.4 and ARE the live-provocation anti-drift guard I proposed to
> build. **CONSEQUENCES:** the inverse-UNREACHABLE pin below would FAIL on 3.2.4 — do NOT build it; the
> 2 unit fixtures are NOT the #118 disease (the engine DOES emit "recursion depth" — proven) — do NOT
> delete/replace them, only refresh their provenance comment to "re-confirmed 3.2.4". Item 4 needs NO
> design change (lead #5017 confirmed; contract-author retracted the fork in comms #5012/#5015).
> The only surviving residuals: commit `scripts/probe_query_complexity_07.py`, and a store-ref note that
> #66's limit PERSISTS on 3.2.4 for the `@@`/RRF shape (~120 clauses) but NOT for simple-operator chains.
> The reasoning below is preserved only as a record of the retracted analysis.

### (RETRACTED premise) Item 4: `_ERROR_CLASS_QUERY_TOO_COMPLEX` classifier branch (WRONGLY believed dead on 3.2.4)

**Fork (operator-opened, routed to sidecar before settling):** KEEP+inverse-live-pin (Opt 1) vs
DELETE the dead branch (Opt 2) vs HYBRID (Opt 3). Evidence: `scripts/probe_query_complexity_07.py`
on surrealdb-3.2.4 — the 3.1.5 parser recursion-depth limit (#66) is UNREACHABLE (OR-chains to
40000 on a real-table WHERE, the closest shape to #66's flat BM25 OR-chain, all OK). Grounded at
HEAD `82e2587`: branch = `_txn.py:530` (`_ERROR_CLASS_QUERY_TOO_COMPLEX`, a TEACHING label), `:546`
(`_QUERY_RECURSION_DEPTH_MARKER = "recursion depth"`), `:591-592` (the arm). Lying fixtures:
`test_memory_backend.py:2056/2062`, `test_surreal_store.py:1362/1368`. Label also in a served
closed-set pin: `test_surreal_store.py:3600` area.

**RECOMMENDATION: Opt 3 (HYBRID)** — keep the defensive branch, RETIRE the hand-typed fixtures,
add the inverse-live-provocation pin with a pin-tied re-open trigger. I concur with contract-author-07's
lean, and adjudicate the two things they left open (the marker-fragility worry; whether the fixtures
must change).

### The deciding principle: asymmetry, weighed against the packet's OWN thesis.
- **Keep-cost is trivial** — one defensive classifier arm + one marker constant. (The contract author
  cites the sibling branch's own docstring calling such arms "defensive not load-bearing.")
- **Delete-and-be-wrong cost is EXACTLY the defect this packet exists to fix** — a future
  recursion-depth / complexity rejection served as `_ERROR_CLASS_UNSPECIFIED` ("unspecified
  rejection"), a served error LYING to an LLM consumer, with nothing watching. That is #118/#119
  verbatim, and this packet's whole mission is "served errors teach the truth."
- **The floating `v3.2` tag (finding #336) makes re-introduction a LIVE, undecided risk**, not a
  hypothetical: the engine drifts across patch releases WITHOUT anyone deciding (3.2.1→3.2.4 happened
  silently). "A future `v3.2.x` re-introduces a parser limit" is precisely the silent drift the
  inverse-live pin is built to alarm on. This is why this is NOT ordinary dead code that hygiene says
  delete — it is a currently-unreachable safety net over a surface that changes itself.

### Consumer/Trust Law reinforcement.
`_ERROR_CLASS_QUERY_TOO_COMPLEX = "query too complex — reduce or shorten the search terms"` is a
TEACHING label — it tells the agent what went wrong AND how to fix it. Deleting it removes a truthful
teacher for a condition that could recur; keeping it (guarded so it cannot silently lie) is the
Consumer/Trust-aligned move. Deleting it also ripples into the SERVED closed-set of error classes
(`test_surreal_store.py:3600`) and the module's documented class list — extra Consumer-surface churn
Opt 2 incurs and Opt 3 avoids.

### The marker-fragility worry is DEFUSED by the inverse pin — it is not a reason for Opt 2.
The contract author correctly notes `"recursion depth"` may not match a FUTURE engine's wording (the
#118 class). But the inverse-live pin does NOT trust the marker to be future-accurate: it PROVOKES the
condition live and asserts UNREACHABLE. If a future engine re-introduces the limit, the pin goes RED —
forcing the next engineer to RE-GROUND the marker against the engine's actual new wording. So keeping
the branch is honest precisely BECAUSE the pin refuses to over-claim the marker. Marker-fragility
argues for the inverse pin (which Opt 3 adds), not for deletion.

### The fixtures MUST change — this is a defect, not a fork.
The two hand-typed `"Exceeded expression recursion depth limit"` fixtures are the #118 disease
verbatim: unit-tier fixtures asserting a shape the 3.2.4 engine never emits, green because they agree
with the code and both disagree with reality. They change in EVERY option (replaced by the inverse pin
in Opt 1/3; deleted in Opt 2). Opt 3 REPLACES them with a [real]-tier inverse-live pin — moving the
coverage from unit-fiction to live-truth, which is literally the #118 lesson ("the durable fix is a
LIVE-ENGINE classification test"). **Strongly agree they must change.**

### The inverse-live pin — build details (so it is honest, not another fiction).
- **Provoke the ENGINE directly**, bypassing `_MAX_FULLTEXT_OR_CLAUSES` truncation — the pin's job is
  to detect an ENGINE-level complexity rejection, which the product's own 60-clause truncation would
  otherwise mask. Assert the raw over-long query returns OK / no complexity rejection (UNREACHABLE).
- **Use the closest-to-#66 shape as the primary leg**: a real-table `WHERE` OR-chain past #66's old
  40/120 threshold (the contract author's strongest probe leg). It MAY use a proxy operator (`OR`
  rather than the literal `@@`) — sound because parser recursion depth is operator-agnostic (parse
  precedes index/fulltext resolution) — but the pin must DOCUMENT that proxy choice and the rationale
  in its docstring, per "a probe needs a control / fixtures encode shapes the engine emits." An
  optional second leg with the literal `@@` fulltext OR-chain closes the last gap cheaply if feasible.
- **Positive control** (mirror #118's `TestLiveEngineClassification` inverse): show the pin CAN see a
  complexity rejection — e.g. assert that a DIFFERENT, genuinely-rejected malformed query still
  classifies correctly, so the pin is not vacuously green because the provocation silently no-oped.
- **Do NOT touch `_MAX_FULLTEXT_OR_CLAUSES`** — the lexical-arm truncation is a SEPARATE concern
  (`store/surreal.py`, `store/query_text.py`, `memory/local.py`, pinned in `test_query_text.py`); it
  stays. #66 was two mechanisms (truncation + the residual classifier label); this fork is only about
  the label arm.
- **Keep the branch with an HONEST docstring** stating: UNREACHABLE on surrealdb-3.2.4 (cite the
  committed probe + this pin), kept as a defensive net, and — if it ever fires — RE-GROUND the marker
  against the engine's actual wording (which may differ; #118). This makes the bound one the next
  engineer meets DELIBERATELY (WHEN-YOU-CANNOT-CLOSE-A-HOLE-PIN-IT), so nobody blind-deletes it and
  nobody blind-trusts the marker.

### Re-open trigger wording (pin-tied, so it is a measurement not a hope).
> *"Re-open trigger: the inverse-live-provocation pin goes RED — i.e. a SurrealDB `v3.2.x` (floating
> tag, #336) or later re-introduces a parser recursion-depth / query-complexity rejection. On RED:
> re-ground `_QUERY_RECURSION_DEPTH_MARKER` against the engine's ACTUAL new wording (do NOT assume it
> still says 'recursion depth' — #118), re-derive fixtures live, and re-confirm the arm labels it."*

The pin IS the measurement (per "a trigger nobody measures is a hope" — packet 03b). Because it is
[real]-tier against the live floating-tag engine, it auto-alarms on the exact silent drift #336 warns
of.

### Receipts / docs (owed, in-packet scope).
- ⚠ `scripts/probe_query_complexity_07.py` is currently **UNTRACKED** (`git ls-files` → empty). It
  must be COMMITTED to `scripts/` to be a durable citation (a committed script that regenerates a
  measurement is brief-base's top-tier receipt). The inverse-live pin is itself the durable
  regenerator — cite its test node id as the primary receipt. Never cite the probe by an untracked path.
- **Store-reference docs update is OWED** (contract-author flagged; I agree) and is IN packet 07 scope
  (the packet exit amends "the store reference's account with receipts"). Suggested: a settled-but-
  watched entry (struck/annotated like §8's #7061 entry) recording that #66's parser recursion-depth
  limit is UNREACHABLE on 3.2.4 `[PROBED 2026-08-17, 3.2.4]`, that `_MAX_FULLTEXT_OR_CLAUSES=60`
  truncation remains as a separate cap, and that the classifier arm is a currently-unreachable net
  guarded by the inverse-live pin — citing the committed probe + the pin. Place near §8 (open/settled
  hazards) or wherever the complexity behavior is documented; keep the 3.1.5 #66 provenance labelled
  at its own version (do not relabel).

### Settle authority.
The operator OPENED this fork and asked to consult the sidecar before settling, so this recommendation
returns to the operator (via lead/contract author) for the final call. My recommendation: **Opt 3**,
for the asymmetry + Consumer/Trust + floating-tag-drift reasons above; the fixtures change regardless.

---

## One-line answers (for citation)
- **Posture:** PIN, via A-cheap — extend the autouse runtime `_sdk_guard` with a single-statement
  assertion on bare `.query()`, retire the ONE per-module pin (`TestNoMultiStatementDdlRidesABareQuery`;
  its route-through-seam coverage held by the pre-existing retry-escape lint — header #2). Not a sweep
  (nothing to sweep; every `BEGIN…COMMIT` already rides `execute_transaction`). Not a bespoke AST guard.
- **Detector:** positive "exactly one top-level statement" (internal-`;`), packages-checked, with a
  stated `;`-in-literal bound + re-open trigger; scoped to `.query()` not `.query_raw()`.
- **#124 coverage pin:** ⚠ my recommendation was DEFER (§4); the **operator OVERRULED it** (ruling
  #5010 decision 3) — PULLED IN as item 3, built at the constant level (`test_ddl_write_target_coverage_124.py`),
  ratified per lead #5017. The current disposition is PULLED-IN, not deferred; §4 below is the
  superseded recommendation.
- **If A-cheap entangles:** fall back to B + file the ONE pin's name-list reach as a finding; never A-expensive.
- **query vs query_raw distinction (§5.1):** by METHOD NAME the guard already observes — `query` gets
  the single-statement assertion, `query_raw` (execute_transaction's path) is exempt. The check is
  orthogonal to the escape check: assert on EVERY intercepted `query` call, not just flagged escapes.
- **Offline/AST pin (§5.2):** YES — pair it, mirroring the retry-escape guard's existing two-leg
  (AST lint + runtime) structure. It checks the multi-statement-LITERAL property STATICALLY (closing
  the runtime leg's untested-branch blind spot for that property); it is NOT the subsumer of the ONE
  `TestNoMultiStatementDdlRidesABareQuery` pin — the pre-existing retry-escape lint holds that pin's
  route-through-seam coverage (header #2). Reuse `_unseamed_sdk_call_sites`/`_talks_to_surrealdb`
  (derived reach), not a new hand-list.
