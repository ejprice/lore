brief-base v14 read · brief project v7 read

# REPORT — adversary-07a-1 — packet 07a CONTRACT-ADVERSARY grade (store recovery + degradation)

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done-with-deviations** — graded the finished contract empirically (wrong builds in a blessed scratch tree; the real repo was never mutated).
- **VERDICT: CONTRACT INSUFFICIENT** — narrowly. **#128 (3 RED pins) and #127 (tripwire) are SUFFICIENT and CLEARED to build.** The **#164/#250 A1 adjudication** ships a **false-gate re-open trigger** and a **chronologically-false root cause**; both need correction before #164/#250 are resolved at close-out.
- P1 headline — **no wrong build survives #128 or #127**, but the **20× recovery drill does NOT discriminate the KeyError branch it is named to guard**: Exp A (revert the store's KeyError catch) → drill still **20/20 green**, while the KeyError *unit tests* go RED; Exp B (break the drop self-heal) → drill **0/20 wedged**. So the drill guards ONLY the connection-close/idle path, never the in-flight-KeyError path.
- Graded: 421f97f · HEAD-at-report: 421f97f · SAME. (Prod code identical 995a358↔421f97f; the contract commit changed no `loremaster/loremaster/` file.)
- Packages considered: none — no mechanism specified (adversary grades tests, not code).
- Reuse ledger: none (no production symbols authored; scratch-only instruments, pasted verbatim in §Probe record).
- deviation 1: verdict is INSUFFICIENT on the #164/#250 adjudication only; the two buildable/mechanical pins pass every wrong-build attempt I could construct.
- deviation 2: the operator's own RULING states the "fixed-by-05a-ii" root cause (F2) — so F2 is an **escalation to the operator**, not just a contract-author fix.
- decisions-needed: **F2 root-cause correction** (operator owns it — the ruling asserts it).
- receipt POINTERS: quantifier table §P1b · reach table §P1c · missing pins §MP · fixture discrimination §FD · reproduced RED/mutation §RR · findings F1–F3 §Findings · full probe record + verbatim instruments §Probe record.

---

## FINDINGS (most-severe first)

### F1 — BLOCKER (for the #164/#250 adjudication): the 20× recovery drill does NOT discriminate the KeyError branch it is named to guard — the re-open trigger is a FALSE GATE.

`07a-contract-store-recovery-degradation.md` §B wires the #164/#250 regression guard as:
> "a full-bounce recovery drill (`probe_store_recovery_07a.py drill`) that no longer heals on the next call — **i.e. any regression to the `_SDK_AWAIT_BOUNDARY_ERRORS` KeyError branch** or the `_CONNECTION_ERRORS`/`is_connection_error` classification of a closed socket."

**Empirically false, with a controlled pair (scratch tree `/tmp/adv07a-scratch`, provenance asserted — `loremaster.store._txn.__file__ = /tmp/adv07a-scratch/loremaster/loremaster/store/_txn.py`):**

- **Exp A — revert the store path's KeyError catch** (`run_query._attempt` and `_txn_query_raw`: `except (*_CONNECTION_ERRORS, KeyError)` → `except _CONNECTION_ERRORS`, and `if isinstance(error, KeyError) or is_connection_error(error)` → `if is_connection_error(error)`). This is exactly the regression the trigger names.
  - The **KeyError unit tests go RED** — `TestQuerySeamSdkKeyErrorClassification::test_sdk_routing_key_error_surfaces_as_connection_error_and_heals` and `TestTxnSdkKeyErrorClassification::..._and_drops` both fail (`2 failed`), the raw `KeyError` now propagating untyped. So the mutation is REAL and DETECTABLE.
  - The **20× drill still passes 20/20**: `SUMMARY: 20/20 recovered without a container restart; heal-index set=[1]; wedged bounces=[] ⇒ PASS`. The drill did not notice the regression it is named to catch.
- **Exp B — break the drop self-heal** (make `SurrealStore._drop_connection` a no-op, #164's "never re-establishes the session" shape). The drill **wedges 0/20**: `wedged bounces=[0..19] ⇒ FAIL`. So the drill is NOT vacuously green — it *does* discriminate the connection-close / drop-reconnect mechanism.

**Conclusion:** the drill guards the **idle-bounce / connection-close path** (`_CONNECTION_ERRORS` + `is_connection_error` + drop/reconnect) — Exp B proves it. It does **NOT** guard the **in-flight-KeyError path** — Exp A proves it. The idle bounce raises `ConnectionClosedError` ("no close frame received or sent", a `WebSocketException` ∈ `_CONNECTION_ERRORS`), which never touches the `KeyError` arm of the `except`. The trigger clause "*i.e. any regression to the ... KeyError branch*" is a false gate — a promise the instrument does not keep. (This is the repo's own "A FAILURE MESSAGE THAT PROMISES A CHECK THE ASSERTION DOES NOT PERFORM IS A FALSE GATE" / "a trigger nobody measures is a hope" class.)

**Concrete fix (all instruments already EXIST — this is a re-anchoring, plus one honest coverage note):**
- KeyError-branch regression → cite `TestQuerySeamSdkKeyErrorClassification` + `TestTxnSdkKeyErrorClassification` (mutation-proven above), NOT the drill.
- connection-close regression → the drill (Exp B is its negative control — see F3).
- The symbol is also wrong: the store path's KeyError catch is the **literal `(*_CONNECTION_ERRORS, KeyError)` tuple inside `run_query`/`_txn_query_raw`**, not `_SDK_AWAIT_BOUNDARY_ERRORS` (which is imported ONLY by `inbox_awaiter.py` and `scout.py` — grep, §Probe record). A regression trigger naming a constant the store path never reads cannot fire for the store path.

### F2 — ESCALATION: the "fixed-by-05a-ii" root cause is chronologically impossible for the store path.

The ruling (`RULING-fork-a.md`) and report §1 attribute the heal to *"packet 05a-ii's `_SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)`."* The git record contradicts this for the store's `_query` path:

| fact | commit | date | receipt |
|---|---|---|---|
| `run_query` created **already catching** `(*_CONNECTION_ERRORS, KeyError)` + the `isinstance(error, KeyError) or is_connection_error` heal guard | `9d29111` (ONE retry seam, #108/#120) | **2026-07-14** | `git show 9d29111:...store/_txn.py` |
| store `_query` routes through `run_query`; KeyError-heal test present | as-of `741f903` | **2026-07-21** | `git show 741f903:...surreal.py / test_surreal_store.py` |
| **#164 reported** | — | **2026-07-22** | finding #164 |
| **#250 reported (prod repro)** | — | **2026-07-27** | finding #250 |
| 05a-ii added `_SDK_AWAIT_BOUNDARY_ERRORS` — **used only by `inbox_awaiter.py` + `scout.py`**, NOT `run_query`/`_txn_query_raw` | `f5aec32` | **2026-08-10** | `git show f5aec32 -- .../_txn.py`; `grep -rn _SDK_AWAIT_BOUNDARY_ERRORS` |

The store path's in-flight-KeyError self-heal was present, tested, and unchanged from **2026-07-14 onward — before both #164 and #250** — and 05a-ii's constant never touched that path. So 05a-ii did not "fix" the store wedge; whatever produced the July production wedge either had a **different, still-undiagnosed cause**, or was the **"server not yet back within the 2 calls anyone tried"** timing artifact the probe's own `_wait_server_back` was built to rule out (#250: *"nobody waited minutes"*).

**Why this matters (Trust Doctrine):** resolving #164/#250 as "fixed-by-05a-ii" writes a **false cause into a resolved outage finding**. The A1 *decision* (the store self-heals on HEAD → don't build A2) still stands — I reproduced 20/20 self-heal at HEAD and the connection-close + KeyError paths are both guarded. But the *why* is wrong, and it is the operator's ruling that asserts it, so it escalates.

### F3 — the committed deploy-smoke drill ships with NO negative control.

`probe-store-recovery-transcript.txt` shows only heal-index=1 / PASS. Nothing in the committed artifact demonstrates the drill can *report a wedge* — so a future silently-broken drill (e.g. one that always prints PASS, or whose `heal_at` logic rots) reads as coverage. "A PROBE NEEDS A CONTROL." Exp B is that control (drop→no-op ⇒ `FAIL — a wedge reproduced`); the deploy-smoke should carry a wedge-injection self-test, or the report should cite Exp B as the demonstrated negative control.

---

## P1b — QUANTIFIER TABLE (per invariant: ∀-over-inputs vs guarded-by-failure-mode)

Scope: the #128 per-item batch-degradation seam (`_resolve_or_acknowledge_many`). The invariant is *"every item is emitted as resolved/acknowledged, per-item-FAILED (continue), or ABORTED (connection lost) — the batch verb never RAISES for a store fault."* All fates are ∀-forced by a fixture:

| fate | ∀-forced? | pin | receipt (mine) |
|---|---|---|---|
| success | ✓ forced | item-1 line in every batch pin | REF build → `3 passed` |
| domain rejection (NotFound/IllegalTransition/ValueError) → FAILED, continue | ✓ forced | `test_an_illegal_item_fails_without_aborting_the_rest` (existing) | read + confirmed discriminating (item-after succeeds) |
| `SurrealConnectionError` → ABORT remainder (render, not raise) | ✓ forced | `test_connection_loss_aborts_remaining_as_render_not_raise` (existing) | **also guards `except` ORDER**: W6 (StoreError before ConnectionError) → this pin RED (`1 failed, 2 passed`) |
| **`TxnContentionExhaustedError` → FAILED-continue, distinct wording** | ✓ forced | `test_a_contended_item_FAILS_per_item_without_aborting_the_rest` (new) | RED@HEAD (error escapes `server.py:3924`); REF green; W1 RED |
| **plain `SurrealStoreError` → FAILED-continue, "safe to retry" ABSENT** | ✓ forced | `test_a_plain_store_error_item_FAILS_...` (new) | RED@HEAD; REF green; W2 RED |
| acknowledge_many uses the SAME loop | ✓ forced | `test_acknowledge_many_also_degrades_per_item_on_contention` (new) | RED@HEAD; a resolve-only fix fails it |

All five fates + the verb-parity leg are pinned; none is guarded by the failure-mode that prompted the work. **Quantifier table: complete.**

## P1c — REACH TABLE (per guard/scan the contract introduces or relies on)

| instrument | reach set | reach DERIVED? | coverage a CHECKED variable? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| **20× recovery drill** (deploy-smoke, `scenario_20_consecutive`) | bounce *shapes* exercised on the real `SurrealStore._query` | **partial** — only the **idle/connection-close** shape; the in-flight-KeyError shape is NOT reached by the gated `drill` mode | PASS = `len(healed)==20` (effect) | **EFFECT** (real `store._query` heal); Exp B = live positive control | **BOUND/FALSE-GATE** — Exp A: KeyError-branch regression undetected; Exp B: connection-close regression detected. Legs: **empirical** (both). → F1/F3 |
| **#127 AST tripwire** (`_command_subscriber_ensure_connection_callers`) | methods in `CommandSubscriber` whose body contains `self._ensure_connection(...)` | **DERIVED** from the AST of the imported `loremaster.scout.__file__` | ✓ — equality pin RED when the set GROWS: 3rd caller → RED, **naming** `_mutation_probe_third_caller` (empirical); fails CLOSED on empty (both pins RED when scan scoped to a non-existent class) | **EFFECT** (parses actual imported source) | n/a (structural pin, no shared policy) | **SAFE**, with two named bounds (below). Legs: **empirical**. |
| #127 "not-vacuously-green" self-guard (`{run,ppo} <= callers`) | — | — | strictly WEAKER than the equality pin | — | — | **documentary only** — catches an empty/broken scan (already caught by equality), does NOT catch a scan coerced to the exact answer (nothing could). Harmless. |

**#127 tripwire reach bounds (residuals, not blockers — the tripwire covers the realistic trigger and fails closed):**
- (b1) A caller *outside* `CommandSubscriber` (or via a non-`self` receiver, e.g. `subscriber._ensure_connection()`) is not in reach. #127's trigger ("any change that adds a second caller") technically includes this; a cross-class concurrent driver is exactly the hazard. Narrow — `_ensure_connection` is a private method almost always driven via `self`.
- (b2) A nested task/closure inside an *existing* method (e.g. `run`) that calls `self._ensure_connection` concurrently is attributed to the enclosing method name → the set does not grow → no redden. A second *concurrent* driver inside `run` would not trip the wire.
- Suggested one-line strengthening (optional): note b1/b2 as the tripwire's stated reach bound so a future reader meets it deliberately.

## MP — MISSING PINS (what the author can go write)

1. **KeyError-branch regression guard, correctly cited + mutation-proven.** *Test that should exist / be cited:* the #164/#250 re-open trigger must anchor the KeyError-branch regression to `TestQuerySeamSdkKeyErrorClassification::test_sdk_routing_key_error_surfaces_as_connection_error_and_heals` + `TestTxnSdkKeyErrorClassification::..._and_drops` (both mutation-proven RED under a reverted catch — Exp A), NOT the drill. *Defect it catches:* a future refactor of `run_query`/`_txn_query_raw`'s `except` that drops `KeyError` — silently green on the drill today.
2. **Live full-bounce in-flight (KeyError) coverage — or an honest SYNTHETIC-ONLY note.** The KeyError branch is guarded ONLY by *synthetic* monkeypatched-`query` unit tests on a clean store; the *live* in-flight-under-full-bounce path (#250's claimed prod shape) is exercised by nothing gated — `scenario_inflight_bounce` is not in `drill` mode, produced an "unspecified rejection" (not a KeyError) in the committed run, and asserts nothing. *Test that should exist:* either a gated in-flight drill leg that reproduces + asserts a KeyError heal, or an explicit statement that KeyError-branch coverage is synthetic-only with the drill covering the connection-close path. *Defect it catches:* a KeyError-branch regression that only manifests under a real server vanish.
3. **Drill negative control (F3).** *Test that should exist:* a wedge-injection self-test in the deploy-smoke (drop→no-op ⇒ FAIL), so a rotted drill cannot read PASS.

## FD — FIXTURE DISCRIMINATION ("what wrong build survives this?")

- **#128 pins — every wrong build I built is caught.** REF (correct: ConnErr→abort, Contention→distinct line, StoreError→generic) → `3 passed`. W1 (catch base, generic wording, no distinct contention line) → contention + acknowledge pins RED (`- #2 FAILED — gave up after 64 attempts...` ≠ ruled wording). W2 (label every StoreError "safe to retry") → plain-error pin RED ("safe to retry this item" present when it must be absent). W6 (wrong `except` order) → existing connection-abort pin RED. The exact-wording assert (Pin 1) + the "safe-to-retry absent" assert (Pin 2) + `len(lines)==4` + exact per-index lines + `resolved 2 of 3` header together leave no room for a plausible wrong build. The injector fake (`_LedgerRaisingOnSecondCall`) genuinely fails and genuinely delegates — it is not a rubber stamp.
- **#127 tripwire discriminates:** grows→RED (names the caller); empty/broken scan→RED (fails closed). Only a *test-file tamper* (hardcoded return) survives, which is outside the threat model and beyond any structural pin.
- **The 20× drill does NOT discriminate the KeyError branch** (Exp A) — the one fixture-discrimination failure in the packet, and the substance of F1.

## RR — reproduced RED / mutation / satisfiability verdicts

- **#128 RED@HEAD (right reason):** `3 failed, 10 deselected`; the injected error escapes `_resolve_or_acknowledge_many` at `server.py:3924` (acknowledge) / `:3920`-region (resolve) and RAISES the whole `findings()` call — the exact #128 defect, not an import/fixture error.
- **#128 satisfiable (C-DEF):** REF reference build → `3 passed`. (I did not chase a full-suite satisfiability sweep; brief scope was the seam.)
- **#127 GREEN@HEAD:** `2 passed`. Mutation: 3rd caller → equality RED naming it, self-guard GREEN (`1 failed, 1 passed`); empty scan → both RED (`2 failed`).
- **#127 precision correction CONFIRMED independently** (grep, not the report's line numbers): `CommandSubscriber` (scout.py) has exactly two in-code callers of `_ensure_connection` — `run` (@487) and `process_pending_once` (@367); `process_pending_once` has ZERO production callers (only a docstring mention @262) — test-only; a second `run` exists on class `Scout` (@966), which is why the scan is class-scoped. "sole PRODUCTION driver = run()" is the correct invariant, and the frozen set `{run, process_pending_once}` is right.
- **Corpse sweep (P6):** the existing legs (`test_an_illegal_item_fails...`, `test_connection_loss_aborts...`) pin the CURRENT best-effort contract and are compatible with the #128 addition (they gain, not contradict, the new fates). No retired-behavior corpse found in `TestResolveManyAcknowledgeManyDispatch`. #126/#127 written verdicts assert nothing (prose) — nothing to corpse.
- **P6b (delete/replace dual):** A1 deletes/replaces NO code (production unchanged, `git diff 995a358..421f97f -- loremaster/loremaster/` empty — verified). No removed-behavior inventory owed.

## Residuals (each with an individual verdict)

- **#126 RENEW + rider "re-adjudicate vs the shipped 07a seam if A2 ships" — CORRECT & moot under A1.** A1 makes no seam change, so the composed-budget growth the rider guards against does not occur. Verdict: sound; the rider correctly does not fire this packet.
- **#127 "do not add the lock" — CORRECT.** An untested connect-lock on a path with no concurrent production driver is the scope the original #127 declined; the tripwire is the right deliverable. Verdict: sound.
- **#128 "live ≥8-way real-contention corroboration pin" (OPEN for the adversary):** NOT a missing pin. Forcing a natural `TxnContentionExhaustedError` is unreliable (survey: 0 exhaustions at N≤32), and the deterministic injected pins fully force the seam's fate. A live "never raises unhandled" pin is a nice-to-have, not required — the seam's job is "handle the error type per-item," which is deterministically pinned. Verdict: injected pins sufficient.
- **Store-reference §3 clarification (report §8):** docs-only, outside the contract author's writable set; correctly flagged for the lead. Not graded here.

---

## VERDICT

**CONTRACT INSUFFICIENT** — scoped:
- **#128 (3 RED pins) — SUFFICIENT. CLEARED to build.** RED for the right reason, satisfiable, and discriminates every wrong build I constructed (W1/W2/W6); quantifier table complete; `except`-order guarded by the existing connection-abort pin.
- **#127 (tripwire, 2 GREEN) — SUFFICIENT.** Precision correct, reach DERIVED, grows→RED+names, fails closed; two narrow reach bounds noted as residuals.
- **#164/#250 A1 adjudication — INSUFFICIENT** on F1 (false-gate re-open trigger — the drill cannot detect the KeyError-branch regression it names; Exp A/B) and F2 (chronologically-false root cause — operator escalation), plus F3 (no committed negative control). The A1 *decision* stands (self-heal reproduced 20/20 at HEAD; both paths guarded); its *evidence chain* does not. Required before resolving #164/#250: re-anchor the regression trigger to the mutation-proven unit tests (MP-1), state the live-in-flight coverage honestly (MP-2), and ship/cite the drill's negative control (MP-3).

---

## Probe record (commands + real output; instruments verbatim per brief-base §1)

**Scratch tree:** `/home/ejprice/PycharmProjects/lore/scripts/scratch_copy.sh /tmp/adv07a-scratch` — provenance asserted (`loremaster -> /tmp/adv07a-scratch/loremaster/loremaster/__init__.py`). Real repo `git status --porcelain` = CLEAN throughout (all mutation in scratch). Engine: spike-surreal 3.2.4 (TEST store `:18000`).

**Exp A instrument (revert store KeyError catch):**
```python
# on /tmp/adv07a-scratch/loremaster/loremaster/store/_txn.py
src = src.replace(
    "        except (*_CONNECTION_ERRORS, KeyError) as error:\n            if isinstance(error, KeyError) or is_connection_error(error):",
    "        except _CONNECTION_ERRORS as error:\n            if is_connection_error(error):", 1)
src = src.replace("    except (*_CONNECTION_ERRORS, KeyError) as error:",
                  "    except _CONNECTION_ERRORS as error:", 1)   # _txn_query_raw
```
- unit tests → `2 failed` (`TestQuerySeamSdkKeyErrorClassification` + `TestTxnSdkKeyErrorClassification`).
- drill (`probe_store_recovery_07a.py drill`) → `SUMMARY: 20/20 recovered ... heal-index set=[1]; wedged bounces=[] ==> PASS`.
- pre-drill provenance: `run_query catches KeyError? False`, `_txn.__file__ = /tmp/adv07a-scratch/...`.

**Exp B instrument (break drop self-heal):**
```python
# on .../store/surreal.py, inside _drop_connection, before the CAS:
"        # EXP-B wedge injection: self-heal disabled (drop is a no-op)\n        return  # noqa\n" + <original body>
```
- drill → `SUMMARY: 0/20 recovered ... wedged bounces=[0..19] ==> FAIL — a wedge reproduced`.

**#128 variant patcher** (`/tmp/patch128.py`, verbatim): imports `SurrealConnectionError, SurrealStoreError, TxnContentionExhaustedError`; inserts, after the `except SurrealConnectionError` abort block —
- REF: `except TxnContentionExhaustedError → "FAILED — store contention, safe to retry this item"; continue` then `except SurrealStoreError as error → "FAILED — {_sanitise_line(str(error))}"; continue`.
- W1: only the generic `except SurrealStoreError` (no distinct contention line).
- W2: `except SurrealStoreError → "...safe to retry this item"` for ALL.
- W6: the REF pair inserted BEFORE `except SurrealConnectionError` (wrong order).
Results: REF `3 passed`; W1 `2 failed, 1 passed` (contention+ack RED); W2 `1 failed, 2 passed` (plain RED); W6 `1 failed` on `test_connection_loss_aborts_remaining_as_render_not_raise`.

**#127 mutation:** inserted `async def _mutation_probe_third_caller(self): await self._ensure_connection()` into `CommandSubscriber` → equality pin RED naming `['_mutation_probe_third_caller', 'process_pending_once', 'run']`, self-guard GREEN. Empty-scan (scoped scan to `NoSuchClassXYZ`) → both pins RED.

**Timeline / grep receipts (F2):** `git show -s 9d29111` = 2026-07-14; `git show 9d29111:...store/_txn.py` shows `run_query` `except (*_CONNECTION_ERRORS, KeyError)` present; `git show 741f903:...surreal.py` (2026-07-21) shows `_query → run_query`; `git show f5aec32 -- .../_txn.py` (2026-08-10) adds ONLY the constants; `grep -rn _SDK_AWAIT_BOUNDARY_ERRORS loremaster/loremaster/` → `inbox_awaiter.py`, `scout.py`, and the definition in `_txn.py` only (never `run_query`/`_txn_query_raw`, never `surreal.py`).

**Scratch tree `/tmp/adv07a-scratch` is left in place** (restored to pristine prod code) pending the lead's word — keep for re-runs or discard.
