# REPORT-contract-151

brief-base v5 read
state: **done — 2 decisions needed, both blocking the builder**
deviations:
- Built a REFERENCE FIX in a scratch copy (`/tmp/contract151-ref`, provenance-asserted) to produce a satisfiability receipt. No production file in the real repo was touched.
- Edited `test_retry_seam.py:7018` (in my writable set): the existing composition pin calls `bootstrap_session` directly and does not bind under a required `url`.
decisions-needed:
- **F1 — `scout.py:171` is a FOURTH unlabelled call site the brief did not name.** The R3 gate goes RED on it. Label it (my pick) or exempt it. Blocking.
- **F2 — `loremaster/tests/_surreal_harness.py` MUST be in the builder's writable set.** It calls `bootstrap_session` positionally; a required `url` breaks every `[real]` fixture. The contract is UNSATISFIABLE without this one-line edit. Blocking.
receipt pointers:
- RED: §1 · satisfiability 489/0: §2 · mutation proofs M1–M6: §3 · W1–W8 table: §4 · forks: §5 · not-mechanically-pinnable (W8): §6 · out-of-scope observations: §7

---

## 1. RED receipts (the UNFIXED tree)

Baseline before my changes, re-measured (not inherited): `468 passed`.

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster
$ uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
17 failed, 472 passed, 1 warning in 17.28s
```

The 17, by concern:

| n | pin | file |
|---|---|---|
| 3 | `test_each_bootstrap_statement_logs_its_own_label_url_and_engine_text[DEFINE-NAMESPACE\|use\|DEFINE-DATABASE]` | test_surreal_harness.py |
| 3 | `test_each_bootstrap_statement_carries_the_CALLERS_url[…×3]` | test_surreal_harness.py |
| 3 | `test_each_bootstrap_statement_carries_the_ENGINES_OWN_text[…×3]` | test_surreal_harness.py |
| 1 | `test_the_three_statements_carry_THREE_DISTINCT_labels` | test_surreal_harness.py |
| 1 | `test_omitting_url_is_a_TypeError_at_the_call` | test_surreal_harness.py |
| 1 | `test_every_call_into_the_driver_passes_a_label` (structural, R3) | test_retry_seam.py |
| 4 | `test_bootstrap_session_propagates_every_failure_UNWRAPPED[×4 fates]` | test_retry_seam.py |
| 1 | `test_the_three_bootstrap_statements_compose_one_budget` (pre-existing; newly requires `url`) | test_retry_seam.py |

Gates on the real tree: `ruff check .` → **All checks passed**. `./scripts/typecheck.sh` → **55 errors in 5 files** (baseline exactly; **zero** in the files I touched).

**The structural pin's residuals, named individually** (repo law bans "all remaining hits are X"):

```
scout.py:171          in _scout_query()          <-- NOT in the brief's scope. See F1.
store/_txn.py:1021    in bootstrap_session()
store/_txn.py:1022    in bootstrap_session()
store/_txn.py:1023    in bootstrap_session()
```

### Two pins that are NOT red-by-design, disclosed rather than counted as receipts

- `test_passing_url_POSITIONALLY_is_a_TypeError` — **green today for the WRONG reason**: with only three parameters, a fourth positional arg is a `TypeError` on arity, not on keyword-only-ness. It cannot be red before the parameter exists. Mutation-proven instead (M6).
- `test_bootstrap_session_propagates_every_failure_UNWRAPPED` — red today on the **plumbing** (it passes `url=`, which does not yet bind), not on the disposition it names. Its docstring says so explicitly, and its real proof is M4. A pin red for a reason other than the property it names cannot demonstrate that property, and its author is the one person who will never notice it — so it is stated, not quietly counted.

---

## 2. Satisfiability receipt — 489 passed / 0 failed on a correct build

Repo law: a contract ships with proof it goes 0-failed against a known-correct build. I did not reason about this; I built it.

Scratch copy via the blessed tool (`./scripts/scratch_copy.sh`), **provenance asserted**:

```
PROVENANCE loremaster.__file__ = /tmp/contract151-ref/loremaster/loremaster/__init__.py
```

Reference fix applied there: three label constants + `*, url: str` on `bootstrap_session`, threaded into all three `retry_on_conflict` calls; the false docstring clause replaced; all 11 production owners + `_surreal_harness.py` + `scout.py` bootstrap pass `url`; `scout.py:171` labelled.

```
$ cd /tmp/contract151-ref/loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
489 passed, 1 warning in 16.91s
```

**The harder leg (post-fix gates), because a contract that traps the builder between ruff and a test is a C-DEF defect:**

- `uv run ruff check .` on the fixed build → **All checks passed**
- `./scripts/typecheck.sh` on the fixed build → **55 errors in 5 files** (baseline unchanged); **zero** in `store/_txn.py`, `scout.py`, or either test file.

**This leg already caught one real C-DEF in my own contract.** My first draft called `bootstrap_session` directly with deliberately-wrong signatures. Those are *static* mypy errors — `Too many arguments` today, `Missing named argument "url"` after the fix — so the builder would have been trapped between the type gate and a test it may not edit. Both now invoke through an `Any`-typed reference, with the reason written at the call site. Typecheck went 58/6 → 55/5.

---

## 3. Mutation proofs (against the reference build; every pin restored after)

Each mutation is a plausible WRONG build. Counts are full-suite, so nothing hides behind a truncated summary.

| # | Mutation (the wrong build) | Result | Verdict |
|---|---|---|---|
| M1 | All three labels hold ONE shared string | **1 failed** — `test_the_three_statements_carry_THREE_DISTINCT_labels` **only** | W1 caught. The per-statement pins all still pass, which is exactly why the distinctness pin has to exist. |
| M2 | Signal raised without `from error` (cause lost) | **13 failed** — my 3 engine-text pins + the 10 pre-existing `_query` seam pins | W2 caught. |
| M3 | `url` hardcoded instead of threaded | **3 failed** — all three `carries_the_CALLERS_url` | W3 caught; the distinctive fixture url is what makes it discriminate. |
| M4 | `bootstrap_session` wraps its own exhaustion in `SurrealConnectionError` | **20 failed** — incl. my `…propagates_every_failure_UNWRAPPED[EXHAUSTED-CONTENTION]` **and** the pre-existing `test_a_failed_CONNECT_backs_off_and_RECONNECTS[SUSTAINED-CONTENTION]` | W6 caught, by both a unit pin and the existing end-to-end scout pin. This is the W1-SCOUTKILL build. |
| M5 | ONE bootstrap call loses its `label=` | **4 failed** — the structural gate **plus** the three behaviour pins for that statement | R3 caught. Structural and behavioural legs are independently sufficient. |
| M6 | `url` made positional (`*` dropped) | **1 failed** — `test_passing_url_POSITIONALLY_is_a_TypeError` **only** | R2's keyword-only leg proven to discriminate. |

Restore verified after the sweep: `489 passed`.

---

## 4. W1–W8 coverage

| W | Wrong build | Pin(s) | Proven by |
|---|---|---|---|
| W1 | One shared label for all three statements | `test_the_three_statements_carry_THREE_DISTINCT_labels` (derived: compares the three OBSERVED records to each other, so three constants pointing at one value still fails) + 3 per-statement pins, each forcing its own fate with its own fixture | M1 |
| W2 | Label present, engine text lost | `test_each_bootstrap_statement_carries_the_ENGINES_OWN_text` ×3 — substring against the text the fake engine actually raised; **empty string asserted separately** because `""` is the driver's own no-cause fallback | M2 |
| W3 | Hardcoded/defaulted url | `test_each_bootstrap_statement_carries_the_CALLERS_url` ×3, against `_DISTINCT_BOOTSTRAP_URL` (RFC-5737 TEST-NET-2, appears nowhere else in the repo — breaks the parameter-value monoculture class) | M3 |
| W4 | `url` optional | `test_omitting_url_is_a_TypeError_at_the_call` (RED today) + `test_passing_url_POSITIONALLY_is_a_TypeError` (green today for the wrong reason; see §1) | M6 |
| W5 | Budget composition regressed | **Verified, not assumed — see below.** Existing pins re-read against their own messages; `test_the_three_bootstrap_statements_compose_one_budget` kept and updated | existing suite |
| W6 | Attribution added, non-wrapping disposition lost | `TestAttributingTheBootstrapDoesNotChangeItsDisposition` ∀ 4 fates, exact-type (not `isinstance`) | M4 |
| W7 | Structural pin passes vacuously | reach control + stale-exemption control + positive control (both call shapes) + innermost-function control + negative control | M5 + controls |
| W8 | Docstring "fixed" by deletion or restatement | **Partially mechanical — see §6.** Not faked. | — |

### W5 — I read the existing composition pins against their own messages, as instructed

The brief asked me to check for the gap CLAUDE.md records (a shared-deadline pin whose message promised more than its assertion performed). **That specific gap is already REPAIRED, and I confirmed it rather than assuming it.** `test_retry_seam.py:7040-7074` now asserts `budgets[0] < default` *and* strict pairwise decrease, with a comment recording that the old non-strict version waved through three independent 2.0s budgets at 399/399.

I re-read all four composition pins against their messages and **found no message/assertion gap**:

- `test_connect_admins_three_statements_share_one_budget` — message says "COMPOSES leaves it the attempt floor; {ceiling} means a FRESH budget"; assertion is `observed == floor`. Matches.
- `test_teardowns_two_operations_share_one_budget` — same shape. Matches.
- `test_the_composed_budget_is_READ_from_the_seam_not_copied` — matches.
- `_assert_the_two_bounds_differ` is a genuine non-discrimination guard: it refuses to run if floor == ceiling, and if the burn count is not strictly below the floor.

The one change I made: the pin at `:7018` now passes `url=_CTOR_VALUES["url"]`, since a required parameter does not bind without it. Its budget assertions are untouched.

---

## 5. Forks — both blocking, neither settled by me

### F1 (BLOCKING) — `scout.py:171` is a fourth unlabelled call site, outside the brief's scope

The brief states R3's "only legitimate exemption" is `execute_transaction` (:1245). That is **not the full picture.** A deny-by-default scan over `loremaster/` finds **8** calls into the driver, of which **4** are unattributed:

| site | enclosing | has its own attribution? |
|---|---|---|
| `store/_txn.py:1021-1023` | `bootstrap_session` | **NO** — finding #151, in scope |
| `scout.py:171` | `_scout_query` | **NO** — *not in the brief's scope* |
| `scout.py:563` | `_consume_live` | YES — swallows the exhaustion, logs `command_subscriber.live_unavailable` w/ `exc_info=True` (:568-569) |
| `scout.py:591` | `_safe_kill` | YES — swallows it, logs `command_subscriber.kill.already_closed` (:593-594) |
| `store/_txn.py:1245` | `execute_transaction` | YES — `_log_rollback` (:789-801) |
| `store/_txn.py:1120` | `run_query` | passes `label=`/`url=` already |

I exempted `_consume_live` and `_safe_kill` **with the evidence written into the allowlist**, per repo law that an exemption is evidence-backed. I did **not** exempt `scout.py:171`, because it has no evidence to offer: it propagates, logs nothing, and its exhaustion produces the same unattributable record with the same "see the server log" hint. **It is #151's exact shape in a different function** — and #151's own body names scout among the unattributable emitters, so this is consistent with the finding, just outside the brief's stated scope.

- **Reading A (my pick): label it.** "Don't kick the can" — a known defect found in-session, one line in the reference build, and leaving it means the gate ships with an un-evidenced hole in its allowlist, which is the thing the gate exists to prevent. ⚠ Caveat I measured: a *full* fix also wants a `url`, and `_scout_query` has no url in scope — that needs threading through its callers, which is genuinely more than one line. My reference build passed `label=` only (partial attribution: label + engine text, `url=None`).
- **Reading B: exempt it,** with a stated reason and a re-open trigger, keeping this wave strictly to `bootstrap_session`. One line in `_ATTRIBUTED_BY_ANOTHER_MECHANISM` — but the reason would be "out of scope for this wave", which is not evidence, and the repo forbids exactly that.

**Operator's call.** If B, the builder adds one allowlist entry and the gate goes green; nothing else in the contract changes.

### F2 (BLOCKING) — `loremaster/tests/_surreal_harness.py` must be writable for the builder

`_surreal_harness.py:339` calls `await bootstrap_session(connection, env.namespace, env.database)`. Under R2's **required** `url` this is a `TypeError` — and `connect_admin` is what **every `[real]` fixture in the suite** uses for setup. My own attribution pins drive `connect_admin`, so they cannot pass until this is fixed.

The brief listed 9 owners; the real set is **11 production owners** (it omitted `store/surreal.py:454` and `tasks.py:466`) **plus this 12th test-tree call site.** The file is not in my writable set, so per scope law here is the exact edit:

```python
# loremaster/tests/_surreal_harness.py:339
-        await bootstrap_session(connection, env.namespace, env.database)
+        await bootstrap_session(connection, env.namespace, env.database, url=env.url)
```

`env.url` is already in scope at :333. Verified in the reference build.

---

## 6. W8 — the docstring half: what IS and IS NOT mechanically pinned

**Honest answer: the correction itself is not mechanically pinnable, and I did not invent a pin that pretends otherwise.**

What IS now mechanical: the false clause's *claim* — "these callers have their own attribution" — is no longer prose at all. It is `_ATTRIBUTED_BY_ANOTHER_MECHANISM`, a data structure that (a) must name the evidence, (b) is enforced against every call site by `test_every_call_into_the_driver_passes_a_label`, and (c) is itself checked for staleness by `test_every_exemption_matches_a_REAL_call_site`. That is DESIGN-LAW §15's "derive the prose from the behaviour, don't restate it beside it": the day a listed caller stops self-attributing, the gate fires. Under the old docstring, the identical falsehood was invisible to every gate for the life of the function.

What is NOT mechanical, and **what the reviewer must therefore check by eye**:

1. That `retry_on_conflict`'s docstring no longer claims `bootstrap_session` has its own attribution. My reference build replaces the clause with one that points at the allowlist instead of re-listing callers by name — a name list in a docstring is the same defect one rename later.
2. That the replacement does not simply mint a *new* un-derived claim beside the code.
3. That the deleted tripwire pin's removal is stated in the commit message, per its own instruction ("if you closed this on purpose, delete this pin in the same diff and **say so**").

I considered and rejected a literal pin asserting the string `bootstrap_session` is absent from `retry_on_conflict.__doc__`: it is keyed on a name, defeated by any rewording, and it is precisely the "enumerate the forbidden" move CLAUDE.md's instrument-lesson table records as defeated six times.

### What could still defeat the R3 scanner (asked for explicitly by W7)

Keyed on the driver's **name**, so it does not see: a call through an import alias (`from … import retry_on_conflict as roc`), a variable holding the function, `getattr(txn, "retry_on_conflict")()`, or a call built by `functools.partial`. All are documented in the scanner's own docstring rather than left implicit. I judged them acceptable because the gate's threat model is the **honest engineer adding a new caller** — an aliased call has to be written deliberately — and because a module reaching the driver at all is separately pinned by identity (`test_every_connection_owner_holds_the_ONE_shared_bootstrap`) and by the no-hand-rolled-bootstrap scan. **If the operator wants that closed, the move is a runtime guard (wrap the driver, assert every call has an attributed frame) — but per CLAUDE.md a runtime gate is an invariant only over code it RUNS, so it would need its own coverage-as-a-checked-variable leg.** Not built; flagged.

---

## 7. Things I noticed that nobody asked about (surfacing, not deciding)

1. **A count claim contradicting its own enumeration.** `test_retry_seam.py:6841` (and the comment at :6779-6780) says the record "cannot be attributed to ANY of the **eleven** possible emitters (ten `_query` seams, scout, the bootstrap)" — that parenthesis enumerates **twelve**. This is the un-derived-count class CLAUDE.md documents. It is also about to become *stale* in a different way: once #151 lands, the bootstrap IS attributable, so the sentence's premise changes. Not in my writable set to fix silently; flagging. Suggested: derive the count, or drop the number and keep the enumeration.
2. **`_seam_attempt_ceiling()`** in `test_surreal_harness.py` was used by the tripwire pin I deleted; it is still used elsewhere in the file (ruff is clean), so no orphan. Noted only so the builder does not "tidy" it away.
3. The scratch reference build at **`/tmp/contract151-ref`** is left in place deliberately — it is a working, gate-clean implementation of the fix and may be useful to the builder or the contract-adversary. Delete it whenever; it is outside the repo and cannot be committed.
4. Per repo law, `REPORT-*.md` files at the repo root are untracked scratch and **must be deleted before any image build** — this file included.

---

## 8. What I changed

| file | change |
|---|---|
| `loremaster/tests/test_surreal_harness.py` | **DELETED** `test_the_bootstrap_paths_exhaustion_is_UNATTRIBUTED_a_known_bound` (the #151 tripwire) — not weakened. Updated the module docstring's load-bearing citation (:63-67) to record that the bound is closed and why. Added `_DISTINCT_BOOTSTRAP_URL`/`_DISTINCT_URL_ENV`, `_BOOTSTRAP_LABEL_CONSTANTS`, three per-statement conflict fixtures, `TestTheBootstrapPathsExhaustionIsAttributable` (10 pins), `TestBootstrapSessionRequiresItsUrl` (2 pins). Extracted `_the_one_exhaustion_record` to module level so the new class does not clone the old one's helper. |
| `loremaster/tests/test_retry_seam.py` | `:7018` composition pin now passes `url=`. Appended §10 `TestEveryCallIntoTheRetryDriverIsAttributable` (the R3 deny-by-default AST gate + reach/stale/positive/innermost/negative controls) and §10a `TestAttributingTheBootstrapDoesNotChangeItsDisposition` (∀ 4 fates). |

No production file in the repo was modified. No git state was touched.
