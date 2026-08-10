# REPORT-adversary-05a-ii — contract-adversary grade of the `await` RED contract

brief-base v11 read
brief project v7 read

> **REVISION 3 RE-GRADE (2026-08-10, HEAD `218c13f`) — VERDICT: CONTRACT SUFFICIENT.** The
> author fixed the rev2 INSUFFICIENT (§R3 below is the delta grade). The rev2 grade is kept
> UNCHANGED beneath it for provenance (marked SUPERSEDED). Read §R3 first.

---

## R3. REVISION-3 DELTA RE-GRADE — SUFFICIENT (with one pinned-bound recommendation)

### R3 SUMMARY BLOCK
- **VERDICT: CONTRACT SUFFICIENT.** The rev2 BLOCKER (R-2 sharing) and both secondary pins are
  fixed and verified; the new guards are the real thing — the scout-leg mutation pin is RED on
  the unwired real HEAD (the rev2 behaviour pin was GREEN there). One residual escapes every
  guard but it is a RECEDING gap the lead pre-authorised as a pinned BOUND, not a blocker.
- **JOB 1 — do the fixes catch the wrong builds? YES, all four:** 7a (scout inline) → AST belt
  + scout-leg mutation RED; 7b (await inline) → AST belt + await-leg mutation RED; hardcoded
  `"q:gate"` → the `q:other` parametrize leg RED; stamping build (`peek=False`) → the
  idempotency pin RED (the `_StampingDrain` now discriminates).
- **JOB 2 — attacking the new pins:** the runtime-mutation legs observe the EFFECT (await
  RAISES / scout stops recovering) with non-vacuous positive controls — SOUND. The AST belt is
  defeatable-by-spelling (concatenation confirmed to escape) **but the mutation pin backstops
  every inline spelling** (concat confirmed CAUGHT by the mutation) — belt-and-braces holds.
  ONE residual survives BOTH guards (§R3.3).
- **Satisfiability:** the correct rev3 reference (2 constants + await + ALL 8 scout sites
  DRY'd + R-3 render) goes **42/42** — no C-DEF trap from the new pins. Provenance:
  `loremaster.__file__ = /tmp/adv-r3/loremaster/loremaster/__init__.py`.
- **RED honesty:** all new pins RED for the right reason on real HEAD — the awaiter-dependent
  ones via `AttributeError: module 'loremaster.server' has no attribute 'InboxAwaiter'`; the
  scout-leg mutation via its own `assert 1 == 0` ("subscriber STILL recovered … holds a PRIVATE
  INLINE tuple") — i.e. it genuinely FAILS on the current inline HEAD, which is exactly what a
  standing sharing guard must do.
- **Graded:** HEAD `218c13f` · HEAD-at-report `218c13f` · SAME.

### R3.1 — JOB 1: the rev2 findings are fixed (empirical)

| Wrong build | Pin(s) that now catch it | Result |
|---|---|---|
| 7a — await wired, scout keeps private inline clones | AST belt + scout-leg runtime mutation | **both RED** |
| 7b — await hand-rolls inline, scout wired | AST belt + await-leg runtime mutation | **both RED** |
| hardcoded `entry.thread == "q:gate"` | `TestThreadNarrowsClientSide[q:other]` | **RED** (`[q:gate]` passes) |
| stamping build `peek=False` | `test_two_awaits…BOTH_return_it` (on `_StampingDrain`) + `…peek_true` | **both RED** |

The scout-leg mutation is the load-bearing repair: on real HEAD (scout inline, no constant) it
is **RED** — a private inline tuple is unaffected by the constant mutation, so recovery does not
break, so the pin fails. That is the standing "prove sharing by mutation" the rev2 behaviour pin
was not. Positive control (`test_reconnect_recovers…`, unpatched) recovers — non-vacuous.

### R3.2 — JOB 2: the new pins graded for their OWN vacuity/reach (P1c on the new guards)

| New guard | reach DERIVED or hand-list? | coverage CHECKED? | effect or proxy? | one-source by mutation? | verdict |
|---|---|---|---|---|---|
| await-leg runtime mutation | patches `awaiter_module._SDK_AWAIT_BOUNDARY_ERRORS[_WITH_CONTENTION]`; asserts `await_inbox` RAISES | YES (RED on inline HEAD; PASS only when the catch NAMES the patched global) | **effect** (recovery breaks) | proves the catch names a PATCHABLE module global — see §R3.3 for the one thing it can't distinguish | SOUND (bounded) |
| scout-leg runtime mutation | patches `scout._SDK_AWAIT_BOUNDARY_ERRORS[_WITH_CONTENTION]`; asserts gap NOT recovered | YES (RED on inline HEAD) | **effect** | same bound as above | SOUND (bounded) |
| AST reach belt | **within-module DERIVED** (walks every `ast.ExceptHandler` whose type is a `Tuple` with a `*_CONNECTION_ERRORS` spread + bare `KeyError`); **module set is a 2-item HAND-LIST** `(scout, awaiter_module)` | partial — pattern-derived per module, hand-list across modules | source-shape (proxy) | n/a — backstopped by the mutation pins | defeatable-by-spelling; REDUNDANT to the mutation (§R3.3) |
| `_StampingDrain` idempotency | shared drain state models a real `to`-edge stamp | YES — a `peek=False` build reddens | effect | n/a | SOUND, no residual monoculture |
| thread parametrize `{q:gate,q:other}` | two distinct values | YES — a single-value comparand fails one leg | effect | n/a | SOUND, monoculture killed |

Spelling attacks on the AST belt, each with the mutation-pin backstop verdict (empirical where marked):

| Inline clone spelling | AST belt | Runtime-mutation pin | net |
|---|---|---|---|
| `(KeyError, *_CONNECTION_ERRORS)` (order) | CATCHES (order-independent `any`) | CATCHES | caught |
| `_CONNECTION_ERRORS + (KeyError,)` (concat `BinOp`) | **MISSES** (not a `Tuple`) — *confirmed* | **CATCHES** — *confirmed* (await-leg RED) | caught |
| `(*_CE, KeyError)` aliased import | MISSES (`id != "_CONNECTION_ERRORS"`) | CATCHES (inline ≠ the global) | caught |
| `_X = (*_CONNECTION_ERRORS, KeyError)`; `except _X:` (differently-named global) | MISSES (`Name`, not `Tuple`) | CATCHES (patch hits `_SDK_…`, not `_X`) | caught |
| **same-named LOCAL redefinition** of `_SDK_AWAIT_BOUNDARY_ERRORS` in a consumer module | MISSES (`Name`) | **MISSES** (patch hits the local copy) | **ESCAPES — §R3.3** |
| clone in a THIRD module the belt never opens | MISSES (not scanned) | MISSES (not exercised) | ESCAPES (no third consumer today) |

**The belt is redundant defense — the runtime-mutation pin is the real guard, and it is
spelling-proof** (it observes the EFFECT of mutating the symbol, not the syntax). Every inline
spelling that escapes the belt is still caught by the mutation, EXCEPT the two §R3.3 cases.

### R3.3 — RESIDUAL (pinned BOUND, not a blocker — the receding gap the lead pre-authorised)

**One wrong build survives the WHOLE 42-pin contract (confirmed 42/42):** a consumer module
that DEFINES its own same-named `_SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)`
LOCALLY (instead of `from loremaster.store._txn import …`). The runtime-mutation pin patches
that consumer's OWN module attribute, so it cannot tell "imported the ONE `_txn` source" from
"has a private copy that merely shares the NAME" — and the belt sees a `Name`, not a `Tuple`.
This is a two-source clone that is CORRECT today (same value) but can DRIFT if `_txn`'s
definition later changes. A THIRD module catching the boundary is the same class (belt's module
set is a 2-item hand-list = the two R-2 consumers).

**Why this is a BOUND, not a missing pin (per the reach-attack STOP rule + the lead's brief):**
the clone has receded from *inline tuple* → *same-named module constant*. The next guard (an AST
import-check that await + scout `from _txn import` the constants) itself recedes to re-export /
`import _txn; _txn._SDK…` / aliasing. Each round relocates the constant one level deeper without
closing the class. So:
- **Recommendation 1 (cheap, do it): tighten the builder requirement** to say *IMPORT both
  constants from `loremaster.store._txn`; do not RE-DEFINE them in the consumer.* A literal
  reading of "patchable module attr" could otherwise produce the drifting local copy — this is
  the realistic path to the residual, and a one-line wording fix removes it.
- **Recommendation 2 (accept as a pinned bound): drift-only, and correct today.** Pin the bound
  in a docstring with a **named re-open trigger**: *"the R-2 guards prove each consumer NAMES a
  patchable module global of this name; they do not prove it is `_txn`'s ONE definition. Re-open
  if a third module ever catches the SDK-await boundary, or if the constant's value is ever
  changed in `_txn` (add a same-value drift check then)."*
- Optional: an AST import-check belt over the SAME derived module set would raise the cost of the
  local-redefinition escape — but say out loud that it recedes, and carry the re-open trigger; do
  NOT run another guard round chasing it.

### R3.4 — VERDICT: CONTRACT SUFFICIENT

The flagged rev2 BLOCKER is fixed and independently verified (7a/7b both redden; the scout-leg
mutation is RED on the unwired HEAD). The runtime-mutation pins are effect-observing standing
guards with non-vacuous controls; every realistic routing-≠-sharing clone (all inline spellings)
is caught. Both secondary pins discriminate. Satisfiability holds 42/42. The one surviving
escape is a receding, drift-only bound the lead pre-authorised me to PIN rather than chase —
addressed by a one-line builder-req tightening (R3.3 rec 1) plus a re-open trigger (rec 2), not
a new blocker. Builder may proceed.

_Scratch: `/tmp/adv-r3` (rev3 reference, provenance-verified) + `/tmp/adv-05aii` (rev2).
`rm` sandbox-blocked; operator may delete both._

---

## (SUPERSEDED) R2 grade — the original INSUFFICIENT verdict, kept for provenance

> The verdict below graded HEAD `251c40f` + the rev2 working tree and returned INSUFFICIENT.
> It was ADDRESSED at `218c13f`; see §R3 above. Retained unchanged as the audit trail.

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — one BLOCKER missing pin (the flagged R-2 sharing
  guard) + one secondary missing pin (thread-value discrimination). Everything else is
  strong: 9 of the ~12 invariants are cleanly caught by discriminating pins, satisfiability
  holds 38/38, RED honesty confirmed.
- **P1 headline — did a wrong build survive?** YES, the FLAGGED one. Two routing-≠-sharing
  wrong builds each pass the WHOLE contract 38/38: (7a) await wired to the shared constant
  but `scout.py` keeps its private inline `(*_CONNECTION_ERRORS, KeyError)` clones; (7b)
  await hand-rolls its OWN inline tuple, constant unused by await. The R-2 "MANDATORY
  prove-sharing-by-mutation pin" the contract claims does NOT exist as a standing test.
- **State:** done. Reference built + provenance-verified in scratch (`/tmp/adv-05aii`,
  `loremaster.__file__` INSIDE it); 12 attack families run empirically.
- **Graded:** working tree (revised R-1/R-2/R-3 contract, UNCOMMITTED) on top of HEAD
  `251c40f` · HEAD-at-report `251c40f` · SAME. The graded artifact is the 5 modified test
  files in `git diff` (833-line rewrite of `test_comms_await.py`), NOT the committed 26-pin
  version at `251c40f`.
- **Packages considered:** none — no mechanism specified (a TEST contract). await reuses
  shipped seams (`drain(peek=True)`, `awaiting_answer`/`WaitingOnAnswer`, `render_fenced`/
  `render_attributed`, the `CommandSubscriber` inject-`connect` idiom, `_CONNECTION_ERRORS`);
  I concur with the author's `bespoke: none`.
- **Decisions-needed:** none for me — two missing pins named below; the author adds them,
  re-runs the adversary (per "no contract revision skips the adversary").
- **Receipt pointers:** quantifier table §2 · reach table §3 · MISSING PINS §4 · per-attack
  wrong-build record §5 · satisfiability §6 · fixture/residual verdicts §7.

---

## 1. What I graded, and how

The revised (R-1/R-2/R-3) contract in the WORKING TREE: `test_comms_await.py` (25 pins),
`test_comms_tool.py::TestCommsActionsTable` (`test_await_params` + exact-set),
`test_scout.py::TestCommandSubscriberSharesTheSdkAwaitBoundary` (the R-2 scout leg),
`_message_fakes.py`. Method: I BUILT a known-correct reference of the R-1/R-2/R-3 seams in a
provenance-verified scratch copy (`scripts/scratch_copy.sh /tmp/adv-05aii`;
`loremaster.__file__ = /tmp/adv-05aii/loremaster/loremaster/__init__.py`), confirmed
satisfiability, then mutated it into each wrong build and ran the REAL contract against it.
Reference recipe = `_txn._SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)` +
`inbox_awaiter.py::InboxAwaiter` (snapshot-first → LIVE-establish → poll re-drain → final
snapshot, PEEK) + `AppContext._comms_await` handler + `_render_comms_await_nonempty` (shared
fence + `action=drain` teach) + `_COMMS_ACTIONS["await"]` + one scout catch site wired to the
constant.

**RED honesty (P7) — reproduced, all for the right reason (unbuilt seam):**
- `test_comms_await.py`: **25 RED** = 15 `AttributeError` (14 `server.InboxAwaiter`, 1
  `_SDK_AWAIT_BOUNDARY_ERRORS`) + 9 `ValueError: unknown comms action 'await'` + 1
  `AssertionError` (foreign-param, unknown-action fires first). Collection clean (25 collected).
- `test_comms_tool.py::TestCommsActionsTable`: **3 RED** (exact-set, every-other-requires-
  registration, `test_await_params` `KeyError: 'await'`), 9 pass. No collateral.
- `test_scout.py::TestCommandSubscriberSharesTheSdkAwaitBoundary`: **GREEN on real HEAD** — a
  mutation ANCHOR, non-vacuous (drives a real `KeyError('req-uuid-abc')` in-flight drop
  through the reconnect ladder). ⚠ See §4 — it is green while `_SDK_AWAIT_BOUNDARY_ERRORS`
  does not yet exist, which is exactly the defect.

---

## 2. P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded), every guarded row with a receipt

| Invariant | class | receipt (wrong build → pin) |
|---|---|---|
| Snapshot-first short-circuit | ∀ (pending-at-entry ⇒ immediate) | attack 1 (always-waits) → `TestSnapshotFirstShortCircuit` **RED** (`drain.calls 2≠1`) |
| Final-snapshot-at-timeout | guarded (deadline arrival); pins the OUTCOME ∀ | attack 2b (read-then-sleep, no final read) → **RED** (`[]≠[42]`). 2a (delete final line, sleep-then-read) GREEN — but that build reads past the deadline via overshoot, so it is NOT buggy (see §7 R1) |
| Poll-only completeness | ∀ (LIVE-silent ⇒ poll returns pre-deadline) | attack 3 (poll never re-drains) → `TestPollOnlyCompleteness` **RED** (`now 0.5≮0.5`) |
| Socket-drop non-loss | guarded (drop) + positive control | attack 4a (no KeyError catch) → **RED** (crash); 4-vacuous (always-fabricate) → non-loss GREEN but positive-control **RED** ⇒ control is non-vacuous |
| F1 — await PEEKs, never stamps | ∀ (every read `peek=True`) | attack 5 (`peek=False`) → `test_the_awaiter_reads…peek_true` **RED**. (Idempotency + shape pins pass vacuously — §7 R2) |
| Injection — emitted LIVE statement | ∀ (no thread, no `$`, no caller substring) | 6a (thread inlined) → **RED**; 6b (bound `$param`) → **RED** ×2 |
| Honest-empty-as-fact | ∀ (names SET + TIME, no disclaimer) | reference renders "no unseen traffic for <agent> … waited up to Ns"; passes only by naming both halves |
| Waiting-line via ONE shared helper | discriminating pair + PROVEN BY MUTATION | attack 9 (private clone) → output-identity pins GREEN, `…PROVEN_BY_MUTATION` **RED** (sentinel absent) |
| R-3 — non-empty teaches `action=drain` | ∀ (names drain, never "peek=true") | attack 8 (verbatim `_render_comms_drain(peeked=True)`) → R-3 **RED**, fence pins GREEN |
| **R-2 — await + scout share ONE constant** | **guarded — NO STANDING GUARD** | **7a (scout not wired) & 7b (await inline) each 38/38 GREEN → MISSING PIN §4.1** |
| Exact action set + param honesty | ∀ | RED on real tree (set-mismatch + `KeyError 'await'`) |
| F2 — budget is a fixed constant < ceiling | ∀ (ctor default `0<x<60`) | 10a (default 70) **RED**; 10b (no default) **RED**; 10-param (`timeout` in spec) → `test_await_params` **RED** |

No invariant except R-2 is conditioned on the one input it was tested on that survives a
plausible wrong build — with the secondary exception of the thread-value monoculture (§4.2).

---

## 3. P1c — REACH TABLE (every guard the contract introduces or relies on)

| Guard | reach DERIVED or hand-list? | coverage a CHECKED variable? | effect or proxy? | ONE source proven by MUTATION? | verdict |
|---|---|---|---|---|---|
| **R-2 shared-constant sharing** (`_SDK_AWAIT_BOUNDARY_ERRORS` across await + scout) | reach = {await catch site, ≥1 scout catch site}; **NOT derived** — the "proof" is a MANUAL scratch mutation, not a committed test | **NO** — no pin reddens when the derived set grows or a site stays private | behaviour/effect, but **untied to the constant**: both pins pass with a private inline tuple | **NO** — 7a AND 7b both survive; dropping `KeyError` from the constant leaves the scout pin GREEN | **MISSING PIN (BLOCKER) §4.1** — empirical |
| Waiting-line ONE-helper (`_render_comms_waiting_line`) | render call site; sentinel monkeypatch of the shared staticmethod | **YES** — sentinel must appear or RED | effect (routed output) | **YES** — attack 9 reddens the clone | SAFE — empirical |
| Exact-action-set (`set(_COMMS_ACTIONS) == _EXPECTED_ACTIONS`) | keys vs a hand-list, but **bidirectional `==`** so a NEW or MISSING action both redden | YES (equality both ways) | effect | n/a | adequate — construction-inspection + real-tree RED |
| Injection emitted-statement pin | the one `live_select_statement` output | property-keyed (`agent_id in where`, no `$`/thread/substring) | effect | n/a | SAFE (in-process); ⚠ hyphenated-uuid5 PARSE hazard deferred to the deploy probe — §7 R3 |

Legs: R-2 and waiting-line rows are **EMPIRICAL** (wrong builds in scratch + the constant
mutation). Exact-set and injection rows are construction-inspection + the real-tree RED.

---

## 4. MISSING PINS

### 4.1 BLOCKER — the R-2 "prove-sharing-by-mutation" pin does not exist as a standing test

**The defect it must catch:** a build that satisfies the contract perfectly while leaving the
ONE-IMPLEMENTATION sharing UNestablished — i.e. a routing-≠-sharing private clone, the exact
#102/#120 class the R-2 ruling exists to prevent. Two such builds each pass **all 38 pins**:
- **7a** — `_SDK_AWAIT_BOUNDARY_ERRORS` defined + await wired to it, but `scout.py` keeps its
  private inline `(*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError)` catches (0
  references to the constant). → **38/38 GREEN.**
- **7b** — the constant defined + scout wired, but `InboxAwaiter` hand-rolls its own inline
  `(*_CONNECTION_ERRORS, KeyError)` (constant unused by await). → **38/38 GREEN.**

**Why the committed scout pin does not catch it:** `TestCommandSubscriberSharesTheSdkAwait
Boundary` is a BEHAVIOUR pin — "does the subscriber recover a KeyError in-flight drop?" — and
a private inline tuple catches `KeyError` just as well as the shared constant. Decisive
receipts:
- On 7a I dropped `KeyError` from the shared constant: `TestTheSharedSdkAwaitBoundaryConstant`
  **RED**, await's `TestSocketDropNonLoss` **RED**, but the **scout pin stayed GREEN** — the
  mutation never reaches a site that does not reference the constant.
- The scout pin is **GREEN on real HEAD, where `_SDK_AWAIT_BOUNDARY_ERRORS` does not exist at
  all.** A pin that certifies "shares the ONE constant" is green before the shared thing is
  even created. It certifies nothing about sharing.

The contract MISLABELS this behaviour pin as the invariant (§2 R-2 row / §4 req 4 / §5:
"the cross-suite mutation pin is the invariant: a private clone reddens only one suite"). As a
STANDING property that is FALSE: a private clone reddens ZERO committed suites; the author's
manual mutation reddens the scout suite ONLY IF scout is already wired — the very thing not
enforced. "Prove sharing by mutation" is a committed TEST or it is nothing (brief-base §6;
CLAUDE.md ONE IMPLEMENTATION).

**The test that should exist (both legs; add ONE builder requirement):**
- *scout leg* — monkeypatch the module-level name the scout catch references (e.g.
  `loremaster.scout._SDK_AWAIT_BOUNDARY_ERRORS`) to `(*_CONNECTION_ERRORS,)` (drop `KeyError`),
  drive the same in-flight `KeyError` drop, and assert the subscriber **NO LONGER recovers**
  (does not reconnect / the gap command is not dispatched). Positive control: unpatched ⇒
  recovers. This reddens **iff** scout's catch references the patchable module global — i.e.
  iff scout is wired, not inline.
- *await leg* — symmetric: monkeypatch the awaiter module's `_SDK_AWAIT_BOUNDARY_ERRORS` and
  assert `TestSocketDropNonLoss`-style recovery breaks.
- *added builder requirement* — production must reference the constant via a **patchable
  module attribute** (so the mutation reaches it); an AST/source guard asserting "no residual
  inline `(*_CONNECTION_ERRORS, KeyError)` catch in `scout.py`/the awaiter, and each catch
  names `_SDK_AWAIT_BOUNDARY_ERRORS`" is an acceptable second belt, but its reach (the set of
  catch sites) must be DERIVED, not a hand-list (P1c). The runtime-mutation leg is the
  stronger, effect-observing form and should be the primary.

### 4.2 SECONDARY — thread-narrowing is a parameter-value monoculture

**Defect:** `TestThreadNarrowsClientSide` calls await only with `thread="q:gate"`. A build that
hardcodes the client-side filter to `entry.thread == "q:gate"` (instead of the `thread` PARAM)
**passes** — reproduced empirically. This violates "if the code can branch on a value, at least
one pin must use a DIFFERENT value" (PKT-28 C1 / CLAUDE.md).

**The test that should exist:** a second assertion (or `pytest.mark.parametrize`) driving await
with a DIFFERENT thread value (e.g. `thread="q:other"` over the same `{q:gate, q:other}`
snapshot) and asserting only `{q:other}` returns. A hardcoded-value build then fails one of the
two.

---

## 5. Per-attack wrong-build record (all in `/tmp/adv-05aii`, provenance-verified)

| # | Attack — wrong build | Pin | Result |
|---|---|---|---|
| 1 | Snapshot-first removed (always waits) | `TestSnapshotFirstShortCircuit` | **RED** `drain.calls 2≠1` |
| 2a | Delete final-snapshot line, return stale (sleep-then-read) | `TestFinalSnapshotAtTimeout` | GREEN — not a bug (overshoot read; §7 R1) |
| 2b | Read-then-sleep, no read at/after deadline | `TestFinalSnapshotAtTimeout` | **RED** `[]≠[42]` |
| 3 | LIVE-dependent (poll never re-drains) | `TestPollOnlyCompleteness` | **RED** `now 0.5≮0.5` |
| 4a | No `KeyError` boundary catch (crash on drop) | `TestSocketDropNonLoss` | **RED** (KeyError crash) |
| 4-vac | Always-fabricate traffic (vacuous pass) | non-loss GREEN, **positive control RED** | control is non-vacuous ✅ |
| 5 | Stamping build (`peek=False`) | `test_the_awaiter_reads…peek_true` | **RED**; shape+idempotency vacuous (§7 R2) |
| 6a | Inline `thread` in LIVE WHERE | `…inlines_no_thread…` | **RED** |
| 6b | Bound `$param` in LIVE WHERE | `…keys_on_out…` + `…no_bound_param` | **RED** ×2 |
| 7a | **await wired, scout NOT wired (inline clones)** | ALL 38 | **GREEN → §4.1** |
| 7b | **await hand-rolls inline, constant unused by await** | ALL 38 | **GREEN → §4.1** |
| 7-mut | drop `KeyError` from constant on 7a | constant-shape **RED**, await **RED**, **scout GREEN** | proves scout pin ≠ standing guard |
| 8 | Non-empty reuses drain footer verbatim | R-3 pin | **RED**, fence pins GREEN |
| 9 | Private waiting-line clone | `…PROVEN_BY_MUTATION` | **RED**, output-identity pins GREEN |
| 10a | Budget default 70s (≥ ceiling) | `TestTheAwaitBudget…` | **RED** |
| 10b | Budget no default (caller-set) | `TestTheAwaitBudget…` | **RED** |
| 10p | `timeout` added to await spec params | `test_await_params` | **RED** |
| P2 | Thread narrowing hardcoded `"q:gate"` | `TestThreadNarrowsClientSide` | GREEN → §4.2 |

---

## 6. Satisfiability (C-DEF gate) — PASS

The known-correct reference (constant + await wired + scout wired + R-3 render) goes
**38 passed / 0 failed** (`test_comms_await` 25 + `TestCommsActionsTable` 12 + scout anchor 1).
No pin is RED on a correct build — no C-DEF trap. The R-1/R-2/R-3 seam shapes are buildable
exactly as specified. Provenance receipt: `loremaster.__file__ =
/tmp/adv-05aii/loremaster/loremaster/__init__.py`.

---

## 7. Residuals — each with an individual verdict (not blockers)

- **R1 — the "distinct final snapshot" step is not independently pinned.** Pin #2 pins the
  OBSERVABLE property (a deadline arrival is returned), which is correct: a sleep-then-read
  loop overshoots the deadline and satisfies it without a distinct final snapshot (2a GREEN,
  and that build is not buggy). The genuinely-buggy read-then-sleep build is caught (2b RED).
  Verdict: **adequate** — the pin protects the property, not one mechanism.
- **R2 — F1 idempotency/shape pins are non-discriminating against a stamping build.** The
  `_GatedDrain` fake is a stateless chooser that never stamps, so
  `test_two_awaits…BOTH_return_it` and `test_the_returned_shape_is_a_peek` cannot fail for a
  `peek=False` build (attack 5 both GREEN). F1's no-stamp is FULLY covered by the read-peek
  pin, so this is decorative, not a hole (P5). Verdict: **residual** — consider a fake that
  models stamping if you want the idempotency pin to earn its place.
- **R3 — mid-poll reconnect branch + hyphenated-uuid5 parse are unreached in-process.** The
  awaiter's in-loop `except _SDK_AWAIT_BOUNDARY_ERRORS` (mid-CONSUME drop recovery) is not hit
  by any in-process pin — `TestSocketDropNonLoss` faults at ESTABLISH, and `_GatedDrain` never
  raises. The injection pin uses a hyphen-free `.hex` id, so a raw hyphenated-uuid5 PARSE
  hazard (the design's own §A.5 residual) is untested in-process. Both are DEFERRED to the
  deploy-gated build probe by design (§A.6 Leg B, §4 req 6). Verdict: **acknowledged residual.**
- **R4 — F2 pin checks the ctor DEFAULT, not the handler's pass-through.** A handler that
  overrode `budget_s=120` would pass `TestTheAwaitBudget…` (default still 55) yet wait past the
  ceiling. The handler path is not exercised (awaiter faked in the render pins). Verdict:
  **minor residual** — a plausible-but-unlikely wrong build; consider pinning that the handler
  constructs the awaiter WITHOUT overriding `budget_s`.
- **R5 — honest-empty temporal-bound match is loose.** `"wait"` is a substring of `"waiting:"`,
  so the temporal-bound assertion could be satisfied by an appended waiting-line rather than the
  empty render's own bound. Safe ONLY because the `_03b_fleet` fixer-b fixture has no
  question-debt (verified: the WITHOUT-question pin passes). Verdict: **residual** — a stricter
  match (`"as of"` / `"waited"`) would remove the fixture dependence.
- **P6 corpse sweep:** `await` is ADDITIVE (a new action), not a rename — no test asserts a
  retired pre-await behaviour. `_message_fakes.py` correctly documents the ledger owns NO await
  method (R-1). No corpses.

---

## VERDICT: CONTRACT INSUFFICIENT

Blocker: §4.1 (the R-2 standing prove-sharing-by-mutation pin — the flagged one; two
routing-≠-sharing wrong builds pass all 38 pins, and the "cross-suite mutation" is a manual
scratch step the contract mislabels as a committed invariant). Secondary: §4.2 (thread-value
discrimination). Add both, then re-run the adversary (no revision skips it). Everything else
is strong: satisfiability holds, RED honesty is real, and 9 invariants + the waiting-line
one-helper guard are cleanly discriminating with empirical receipts.

_Order: contract → adversary → build → cold audit. This grade returns to the contract author._
