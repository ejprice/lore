# REPORT-adversary-151b

brief-base v5 read

state: **done — VERDICT: CONTRACT INSUFFICIENT (1 proven missing pin + 2 supporting)**

deviations: none. No repo file touched; no git state mutated; no `--fix` run anywhere.

decisions-needed:
- **MP7 (the finding) — the COUPLED PROSE HALF of #151 is pinned by nothing.** The brief's own
  defect statement names the `_txn.py:857-859` docstring as half the defect. A build with the
  behaviour fully correct and that prose left stating the RETIRED world scores **515 / 0**.
  I built the pin that catches it and proved it RED/GREEN/GREEN. §4.
- **R1 residual — `_txn.py:1242` raises `RetryableConflictSignal()` BARE**, while the driver's
  own comment claims *every* caller raises `from error`. A false universal, unpinned. §5.

receipt pointers: provenance §0 · **C1 satisfiability §1** · **C2 MP1 mutation §2** ·
quantifier table §3 · **the missing pin, proven §4** · residuals §5 · wrong-build record §6 ·
fixture perturbation §7 · sweeps + gates §8

---

## SUMMARY

**P1 headline — NO wrong build survives the BEHAVIOURAL contract.** I built nine, including the
round-1 blocker, the partial fix, the AST-gate-satisfying cosmetic fix, and the plausible-wrong
arithmetic. All nine die. This is the strongest behavioural contract I have graded in this repo.

**Both claims the lead flagged are TRUE, and I verified them independently rather than reading
them.** C1: my own reference fix — built from the source, not from the author's report — takes
the full contract to **515 passed / 0 failed**, with ruff clean and typecheck at the 55-error
baseline. That settles the 5-TypeError calibration question too: those pins **pass on a correct
build**, so they were red for the right reason. C2: the 11-owners-hardcode build that round 1
waved through 489/0 now fails **12 pins**. Round 2 closed its headline hole for real.

**The verdict is INSUFFICIENT on one narrow, real, brief-named ground: the contract grades the
CODE and not the PROSE that prescribed the bug.** #151's defect statement has two halves. The
contract quantifies the behavioural half beautifully over statements, callers, fates and
budgets — and pins the prose half not at all. My reference build satisfied this contract
perfectly while leaving in place a docstring telling the next engineer that `bootstrap_session`
*"has its own attribution"* — which is precisely the belief that made #151 invisible for a
wave. That is the *spec-that-prescribed-the-bug* class, and this repo's law is explicit that a
diagnosis is not an instrument.

---

## 0. Provenance (P0) — which tree I tested

```
$ ./scripts/scratch_copy.sh /tmp/adv151b-scratch
scratch copy READY: /tmp/adv151b-scratch
  loremaster  -> /tmp/adv151b-scratch/loremaster/loremaster/__init__.py

$ cd /tmp/adv151b-scratch && uv run python -c "import loremaster; print(loremaster.__file__)"
PROVENANCE loremaster.__file__ = /tmp/adv151b-scratch/loremaster/loremaster/__init__.py
```

Blessed tool, never `cp -a`. The mutation harness restores from a tar **of the
provenance-asserted tree** and mutates it in place — never a copy-of-a-copy (the round-1
adversary's own §0 poisoning). **Restore control, run before the battery:** `515 passed`.
A poisoned harness cannot produce the alternation in §6.

---

## 1. C1 — THE SATISFIABILITY RECEIPT, INDEPENDENTLY BUILT ✅ CLAIM TRUE

I did **not** reuse the author's fix. I read `_txn.py`, `scout.py` and the eleven owners and
wrote my own (`/tmp/adv151b_reffix.py`): three label constants, `*, url: str` keyword-only on
`bootstrap_session`, label+url threaded into all three driver calls, `url=self._url` at the ten
class owners, `url=url` at scout's bootstrap, `label=` at `scout.py:171` (R4), and
`url=env.url` at `_surreal_harness.py:339` (R5).

```
$ cd /tmp/adv151b-scratch/loremaster && uv run pytest tests/test_surreal_harness.py \
      tests/test_retry_seam.py -q -p no:randomly
515 passed, 1 warning in 18.54s
```

**The harder leg** (a contract that traps the builder between the lint and a test it may not
edit is the C-DEF class):

| gate | on my reference build | verdict |
|---|---|---|
| `uv run ruff check loremaster/` | `All checks passed!` | clean |
| `./scripts/typecheck.sh` | `Found 55 errors in 5 files` | **exactly the baseline**, zero new |

**No orphaned-import cleanup is demanded.** The fix adds parameters and constants and removes
nothing, so the lint asks for no deletion that a pin forbids. I confirmed this by running ruff
*after* the fix rather than reasoning about it.

**The 5-TypeError calibration question, SETTLED.** The lead measured 32 AssertionError + 5
TypeError at HEAD and asked whether the 5 (`bootstrap_session() got an unexpected keyword
argument 'url'`) are red for the right reason or a C-DEF defect. **They are red for the right
reason:** every one of them passes on a correct build — that is exactly what 515/0 means. A
contract pinning a new REQUIRED keyword-only parameter cannot produce any other red on an
unfixed tree. **No C-DEF defect exists in this contract.**

---

## 2. C2 — THE MP1 MUTATION PROOF, REPRODUCED ✅ CLAIM TRUE

The round-1 blocker build, rebuilt from scratch: all eleven production owners hardcode
`url="ws://127.0.0.1:8000/rpc"`, with `bootstrap_session`'s own threading left intact.

```
MUTATION A applied: 11 owners hardcode the url
FAILED …TestEveryProductionOwnerThreadsITSOWNUrl::test_each_production_owner_logs_ITS_OWN_url…[AgentRegistry]
FAILED …[BriefLedger] …[DiffEngine] …[FindingLedger] …[SurrealCodeGraph]
FAILED …[SnapshotStamper] …[SurrealManifest] …[LocalMemoryBackend] …[SurrealStore] …[TaskLedger]
FAILED …test_scouts_command_connection_logs_ITS_OWN_url_on_bootstrap_exhaustion
FAILED …test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls
12 failed, 503 passed, 1 warning in 19.28s
```

**The build that passed round 1 at 489/0 with a zero delta over 6079 tests now fails twelve
pins.** Round 2 did not merely claim its headline; it landed it.

---

## 3. QUANTIFIER TABLE (P1b) — every invariant, ∀-over-inputs vs guarded

| # | Invariant | ∀ or GUARDED | Receipt (door-build or the pin that killed it) |
|---|---|---|---|
| I1 | Each bootstrap statement's record carries a label | **∀ over 3 statements** | mutation U (labels dropped): **26 failed** |
| I2 | The three labels are pairwise distinct | **∀**, observed-vs-observed | round-1 M1 reproduced: 1 failed, distinctness pin only |
| I3 | The label NAMES its own statement | **∀ over 3**, expectation derived from SurrealQL vocabulary, not from the constant | author's mutation C reproduced in structure; every permutation fails ≥1 row (§7) |
| I4 | **The record carries the CALLER's url** | **∀ over 11 production callers + the harness** — *was* the round-1 blocker | **mutation A: 12 failed** (§2) |
| I5 | The record carries the engine's OWN text | **∀ over 3 statements** | mutation U: extras gate suppresses all three, 26 failed |
| I6 | `url` is REQUIRED and keyword-only | **∀**, signature-level | RED today ×5; C1 proves all 5 green on a correct build |
| I7 | Every `retry_on_conflict` call passes `label=` | **GUARDED** — name-keyed AST scan; exemptions keyed per-function with a COUNT budget | **Door-build attempted, KILLED:** mutation U walks the same outcome (unattributable record) through the driver-call door → 26 failed. Alias door remains open **and is PINNED as a known bound** (MP5, with positive control + re-open trigger) |
| I8 | Every `bootstrap_session` call passes `url=` | **GUARDED** — name-keyed AST, and **presence-only, never value** | **Door-build attempted, KILLED by MP1:** mutation T passes `url=None` at all ten owners, **satisfies the AST gate**, and dies behaviourally → **11 failed**. This is precisely why MP1 and MP2 are not redundant |
| I9 | `bootstrap_session` propagates every failure UNWRAPPED | **∀ over 4 fates**, exact type | round-1 M4/SCOUTKILL, unchanged and still green-by-mutation |
| I10 | The three statements share ONE composed budget | **∀**, strictly decreasing | mutation R (deadline dropped while adding kwargs): **2 failed** |
| I11 | Both scans' reach is non-vacuous | **∀**, floor ≥ 11 on two INDEPENDENT counts, pinned to agree | reach-control pins; scan root `_PACKAGE_ROOT` verified; siblings `loresigil`/`lorescribe` confirmed to contain zero callers |
| I12 | Exemptions are non-stale, evidence-backed, and BUDGETED | **∀** | I re-read all three evidences against source. `execute_transaction`→`_log_rollback` **holds on the exhaustion path** (`_txn.py:1246-1249` catches `TxnContentionExhaustedError` and logs) — I verified this rather than relaying it. `_consume_live`, `_safe_kill`: hold |
| I13 | The record's `attempts` matches the exception's (MP6) | **∀ over 3 statements** | mutation V: **14 failed** |
| **I14** | **The driver's prose naming WHICH callers self-attribute matches behaviour** | **❌ NOT PINNED** | **Mutation P: 515 / 0 with actively false prose. Positive control: a docstring that IS pinned, broken → 1 failed.** §4 |
| **I15** | **Every `RetryableConflictSignal` is raised `from error`** | **❌ NOT PINNED — and the claim is FALSE at HEAD** | `_txn.py:1242` raises bare; the driver comment asserts the universal. §5 |
| **I16** | **The eleven per-owner fixture urls are pairwise DISTINCT** | **❌ NOT PINNED** (vacuity door under I4) | Perturbation: collapse the template and the correct build and the blocker build become **indistinguishable** across all ten per-owner pins. §7 |

**Thirteen of sixteen are clean ∀-over-inputs with door-build receipts. Both GUARDED rows (I7,
I8) carry a door-build that the contract KILLED — the round-1 failure mode does not recur.
I14/I15/I16 are the missing pins.**

---

## 4. MP7 — THE MISSING PIN, BUILT AND PROVEN (the finding)

### The wrong build that survives

The brief's defect statement has two halves. The second: *"the docstring at :857-859 claims
`bootstrap_session` and `execute_transaction` 'have their own attribution' — TRUE of
`execute_transaction`, FALSE of `bootstrap_session`, which logs nothing at all."*

After the fix, that sentence does not merely stay stale — it **inverts**. `bootstrap_session`
no longer uses the `None` default it is documented as using. The prose now describes a retired
world, and it describes it in the one place a future caller looks to decide whether *they* need
a label.

```
MUTATION P applied: the docstring now claims bootstrap_session self-attributes
515 passed, 1 warning in 18.55s
```

**A build with the behaviour perfectly correct and the prose actively false is
indistinguishable from the real fix.** My own §1 reference build — the one that scored 515/0 —
contains this defect, because I never touched the docstring and nothing asked me to.

### Positive control — prose IS pinnable here, so this is a GAP, not an impossibility

A probe reporting "not seen" because it is broken reports "not seen" for everything. So I broke
a docstring claim that **is** pinned, in the same test file:

```
CONTROL applied: harness docstring count 35 -> 999
FAILED tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
1 failed, 514 passed
```

**The instrument for exactly this class already exists in this very file** (`:1759`,
`test_the_harnesss_docstring_counts_are_the_DERIVED_counts`) and was not applied to the
docstring the finding names.

### The pin that should exist — implemented, and proven three ways

Not a string match on prose: **derived from behaviour**, per the repo's law that prose which
describes behaviour must be derived from it rather than restated beside it.

```python
def test_every_function_the_docstring_names_as_UNLABELLED_really_passes_no_label(self) -> None:
    """The prose that PRESCRIBED #151, retired alongside the behaviour it described."""
    doc = txn_module.retry_on_conflict.__doc__ or ""
    named = {n for n in _DOCUMENTED_SELF_ATTRIBUTING if n in doc}
    unlabelled = {enclosing for _, _, enclosing, has_label in _all_retry_driver_call_sites()
                  if not has_label}
    liars = sorted(named - unlabelled)
    assert not liars, (...)
```

| leg | tree | result |
|---|---|---|
| **A** | my 515/0 reference build (behaviour fixed, prose untouched) | **RED** — `LIARS: ['bootstrap_session']` |
| **B** | the UNFIXED tree at HEAD (prose is TRUE today) | **GREEN** — not an always-red trap |
| **C** | reference build + prose retired | **GREEN** — satisfiable |

Real output, leg A:
```
  docstring names as `None`-default users : ['bootstrap_session', 'execute_transaction']
  functions that ACTUALLY pass no label   : ['_consume_live', '_safe_kill', 'execute_transaction']
  LIARS (named but now labelled)          : ['bootstrap_session']
  PIN VERDICT: RED  <-- prose describes the RETIRED world
```

Leg B is the valuable one: the pin is **green by design today and goes RED the moment the fix
lands**, so it cannot be satisfied by doing nothing and cannot be inherited silently. (It also
correctly shows `_scout_query` in the unlabelled set at HEAD, leaving it once R4's label lands.)

**The defect it catches:** a fix that lands the behaviour and leaves `_txn.py` telling the next
engineer that the session bootstrap self-attributes — re-planting the exact belief that made
#151 invisible, in the exact function #151 is about.

---

## 5. Residuals — every item, individually

1. **`_txn.py:1242` raises `RetryableConflictSignal()` BARE — a FALSE UNIVERSAL in the driver's
   own prose. REAL, unpinned, ESCALATING.** The driver comment (`_txn.py:~880`) reads *"every
   caller that raises the signal does so ``from error`` (the original engine exception)"* and
   the `engine_error` extra is built on that premise. Measured: four sites raise `from error`
   (`:1002`, `:1010`, `:1018`, `:1103`); **`:1242`, inside `execute_transaction._attempt`, does
   not.** No operational harm today (that caller passes no label, so no `engine_error` extra is
   emitted) — but it is a ∀-claim that is false, in the function #151 touches, and the day
   anyone labels `execute_transaction` the record silently gets the driver's `""` fallback while
   the comment says that cannot happen. **Same class as MP7. Verdict: fix the comment or pin the
   universal; operator's call.**
2. **I16 — nothing pins that the eleven owner urls are pairwise distinct.** Measured in §7. A
   one-line pin (`len({_owner_url(s.__name__) for _, s in seams}) == len(seams)`) closes it.
   **Verdict: real but LOW — the collapse is self-announcing (§7). Recommend adding.**
3. **MP5's stated bound matches the gate's ACTUAL bound — VERIFIED, not relayed.** I read
   `_call_sites_in` (`:7166`): it matches `ast.Name.id` and `ast.Attribute.attr` only. The
   pin's claim of six-seen / six-not-seen is consistent with that matcher, and the pin leads
   with a positive control before both negative assertions. **Verdict: honest.** I also note it
   records its disagreement with the scanner's own too-generous justification rather than
   settling it — correct behaviour.
4. **A shape MP5 does not enumerate: `**kwargs` unpacking.** `retry_on_conflict(_attempt,
   **attribution)` is SEEN as a site but scores `has_label=False` (`keyword.arg` is `None` for
   `**`). That is a **false positive, i.e. fail-safe** — the gate is too strict, not too loose.
   **Verdict: harmless, worth one clause in the bound's docstring.**
5. **`execute_transaction`'s exemption evidence — I verified it on the EXHAUSTION path
   specifically**, because an exemption whose evidence covers only the rollback path would be
   the same defect wearing an allowlist. `_txn.py:1246-1249` catches `TxnContentionExhaustedError`
   and calls `_log_rollback(*last_conflict)`; `last_conflict` cannot be `None` there (the driver
   only counts attempts after a signal). **Verdict: evidence genuinely holds.**
6. **Scan root reach.** `_PACKAGE_ROOT` = `loremaster/loremaster`. Siblings `loresigil` and
   `lorescribe` grepped bare: **zero** callers of either `bootstrap_session` or
   `retry_on_conflict`. **Verdict: reach is honest today**; a caller added in a sibling package
   would be invisible to both gates and to `test_every_owner_the_scan_finds_is_DRIVEN_here`.
   Low concern, stated for the record.
7. **Author's §7.2 disclosed duplication** (`_exhaustion_record` in two files). I concur it is
   trivia, not policy — "take the one record or fail loudly", no budget or classification to
   drift. **Verdict: accept as disclosed.**
8. **Author's §1 blanket claim "No `TypeError`, no collection error, no arity accident" is
   IMPRECISE** — the lead already caught this (5 TypeErrors). **My addition: it is imprecise but
   not WRONG in substance**, and C1 proves it (§1). **Verdict: prose imprecision, already
   recorded in the commit message; no action.**
9. **`REPORT-*.md` at repo root now numbers eleven** including this one. Repo law requires
   deletion before any image build. **Flagging, not acting.**
10. **Scratch artifacts:** `/tmp/adv151b-scratch`, `/tmp/adv151b-ref.tgz`, `/tmp/adv151b_mut.sh`,
    `/tmp/mut*.py`, `/tmp/pert*.py`, `/tmp/probe_pin*.py`. All outside the repo; delete at will.

---

## 6. Wrong-build record (P1) — nine builds, commands and real output

Harness: restore reference from tar → purge `__pycache__` → mutate in place → run the contract.
**Restore control before the battery: `515 passed`.**

| # | wrong build | result | verdict |
|---|---|---|---|
| **A** | the round-1 BLOCKER: 11 owners hardcode the url | **12 failed** | **DEAD** (§2) |
| **P** | **behaviour correct, docstring made actively FALSE** | **515 passed / 0 failed** | **⚠ SURVIVES — the finding (§4)** |
| P-ctl | a docstring that IS pinned, broken | 1 failed | probe can see prose |
| Q | **partial fix** — only statement 1 attributed | 10 failed | dead |
| T | **cosmetic** — `url=None` at ten owners (satisfies the AST gate) | 11 failed | dead; proves MP1≠MP2 |
| R | **plausible-wrong** — `deadline_seconds` dropped while adding kwargs | 2 failed | dead (budget composition) |
| U | url threaded, `label` dropped (extras gate suppresses all three) | 26 failed | dead |
| V | record's `attempts` diverges from the exception's (MP6) | 14 failed | dead |
| A′ | blocker retargeted under a perturbed fixture | 1 failed | §7 — the discrimination boundary |

**The no-op fix** has no room to exist here: `url` is REQUIRED and keyword-only on
`bootstrap_session`, so a build that adds the parameter without threading it does not import,
let alone pass. Verified as part of C1's signature leg.

---

## 7. Fixture discrimination (P2) — perturbed, with the correct-build control leg

**MP1's load-bearing fixture is `_OWNER_URL_TEMPLATE`'s `{owner}` slot.** I perturbed it to
collapse all eleven owners onto ONE shared url, in a scratch copy of the contract, and ran both
legs:

| leg | build | result |
|---|---|---|
| 1 (control) | **CORRECT** build | **1 failed** — `test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls` |
| 2 | **BLOCKER** build (ten owners hardcode the shared value) | **1 failed** — *the same pin*; **all ten per-owner pins PASS** |

**Reading, stated honestly:** this is **not** a surviving wrong build — the perturbation makes
the contract unsatisfiable on a correct build, which per the P2 law is a control failure, not a
finding. What it *does* establish precisely: **the ten per-owner pins derive 100% of their
discriminating power from the template's `{owner}` slot**, and the two-owner observed-vs-observed
pin is the load-bearing backstop that makes the collapse self-announcing. **The author's stated
reason for adding that pin is correct and now measured.** Residual I16 (§5.2) is the one-line
pin that would name the collapse directly instead of leaving it to be inferred from a red.

Individual verdicts on every other load-bearing fixture:

- `_bootstrap_conflicting_on_define_namespace` / `_on_use` / `_on_define_database` —
  **DISCRIMINATE.** Mutation Q (attribute only statement 1) fails 10 pins; each fate is forced,
  not inferred.
- `_OWNER_URL_TEMPLATE` (TEST-NET-2, per-owner, derived from the NAME not `hash()`) —
  **DISCRIMINATES** (mutation A: 12 failed). The explicit refusal to use `hash()` is correct:
  string hashing is per-process randomised and would have made the two-owner pin a 1-in-N flake
  under `-n auto`.
- `_BOOTSTRAP_LABEL_NAMING` vocabulary table — **DISCRIMINATES on permutation.** I checked the
  arithmetic by hand: row 1 requires `namespace`∧¬`database`, row 2 requires
  (`database`∨`select`∨`use`)∧¬`namespace`∧¬`define`, row 3 requires `database`∧¬`namespace`.
  Exactly one assignment of three values satisfies all three, so **every** permutation —
  including the NS↔DB swap that passed round 1 at 489/0 — fails at least one row. My own
  reference labels satisfied it on the first try, so it is not a C-DEF trap either.
- `_DISTINCT_BOOTSTRAP_URL` (harness caller) — **DISCRIMINATES at the driver**, and is no longer
  the *only* url instrument (that was the round-1 blocker).
- `_MIN_KNOWN_BOOTSTRAP_OWNERS` / `_MIN_KNOWN_BOOTSTRAP_CALL_SITES = 11`, pinned to AGREE —
  **DISCRIMINATE** against a silently-blinded scanner. Two independent enumerations, cross-checked;
  I re-derived the 11 call sites from a bare `git grep` and they match.
- `_ATTRIBUTED_BY_ANOTHER_MECHANISM` as `(evidence, COUNT)` with `_MIN_EVIDENCE_CHARACTERS` —
  **DISCRIMINATES.** The budget closes round-1's D3 (a new unlabelled call inside an exempt
  body), and the character floor stops `""`/`"TODO"` punching a hole.
- `_ForeverConflictingQuery` (scout) with `_ABSURD_ATTEMPT_CEILING` — **DISCRIMINATES**; it fails
  loudly on unbounded retry rather than hanging.
- **P5 — can the fakes FAIL?** Yes. `_FakeConnection` is script-driven per statement; mutation Q
  proves per-statement reach (10 failed, and only the statements it touched). Not a mirror of the
  implementation.

---

## 8. Sweeps, gates, and claim verification

**P6 corpse sweep** — grep for live assertions still pinning the retired UNATTRIBUTED world.
Three hits, **all prose, individually verdicted**:

| file:line | content | verdict |
|---|---|---|
| `test_surreal_harness.py:67` | module docstring describing what the replaced pin asserted | **KEEP** — accurate history |
| `test_surreal_harness.py:710` | new class docstring naming the pin it REPLACES | **KEEP** — correct provenance |
| `test_surreal_harness.py:754` | MP6 adjudication comment | **KEEP** — the required adjudication record |

**No live assertion pins the corpse.**

**P6b** — the only delete/replace in this wave is the `…is_UNATTRIBUTED_a_known_bound` pin,
enumerated independently by the round-1 adversary; its one orphaned virtue (`attempts` on the
record) was adjudicated **preserved-with-pin** against R1 and restored. I verified the
restoration DISCRIMINATES rather than trusting the adjudication: **mutation V → 14 failed.**
Nothing further is deleted in round 2.

**P7 RED honesty** — reproduced at HEAD `72a0bc5`:
```
34 failed, 481 passed, 1 warning in 19.36s
```
Matches the brief exactly. Failures are for the right reason — settled decisively by C1 (§1)
rather than by inspecting tracebacks.

**Gates at HEAD** (read-only; I ran no `--fix` anywhere, per the §scope-incident warning):
```
$ uv run ruff check .          -> All checks passed!   exit 0
$ ./scripts/typecheck.sh       -> Found 55 errors in 5 files   (baseline, packet-03 comms)
```
Typecheck baseline did not grow.

**P4 — author claims verified, not relayed:**

| claim | author | my independent measurement | verdict |
|---|---|---|---|
| RED at HEAD | 34 failed / 481 passed | **34 / 481** | TRUE |
| satisfiability | 515 passed | **515 passed on MY OWN reference fix** | **TRUE** |
| ruff on the fixed build | clean | `All checks passed!` | TRUE |
| typecheck on the fixed build | 55 errors / 5 files | identical to baseline | TRUE |
| mutation A kills the blocker | 12 failed | **12 failed**, same 12 pins | TRUE |
| MP1≠MP2 non-redundancy | argued | **measured**: T (url=None) passes the AST gate, dies at MP1 | **TRUE, and now has a receipt** |
| §1 "no TypeError" | claimed | **imprecise** (5 exist) — but harmless; C1 proves them right-reason | imprecise, not wrong |
| exemption evidence holds | claimed | verified against source **on the exhaustion path** | TRUE |

**No over-claim found beyond the already-recorded §1 imprecision.**

---

## VERDICT

# CONTRACT INSUFFICIENT

**Not because the behavioural contract is weak — it is excellent, and I could not break it.**
Nine wrong builds, including the round-1 blocker, a partial fix, a cosmetic fix that satisfies
the AST gate, and a plausible-wrong arithmetic slip: all nine die. Every guarded invariant
carries a door-build that the contract killed. C1 and C2 both reproduce independently. Round 2
closed MP1–MP6 for real, and it closed them at the quantifier, not with patches.

It is insufficient because **the contract grades the code and not the prose that prescribed the
bug** — and this repo has already paid for that distinction. #151's defect statement has two
halves; the contract pins one. A builder can satisfy it perfectly (515/0, ruff clean, typecheck
at baseline) while leaving `_txn.py` telling the next engineer that `bootstrap_session` *"has
its own attribution"*, which is the exact belief that made this finding invisible for a wave.
**My own reference build is that wrong build.**

**Route back to CONTRACT with:**

- **MP7 (blocking)** — `test_every_function_the_docstring_names_as_UNLABELLED_really_passes_no_label`.
  Derived from the AST scan, not a string match. Proven RED on the fixed-behaviour/stale-prose
  build, GREEN at HEAD, GREEN once the prose is retired (§4). *Catches:* mutation P.
- **MP8** — pin or correct the driver's `from error` universal, which is false at `_txn.py:1242`
  (§5.1). *Catches:* a future labelled `execute_transaction` silently emitting the `""` fallback
  the comment promises is impossible.
- **MP9 (minor)** — one line asserting the eleven owner fixture urls are pairwise distinct
  (§5.2). *Catches:* a template collapse that turns all ten per-owner pins vacuous.

**The generalisable lesson, for the ledger.** Round 1's hole was a missing quantifier over
CALLERS. Round 2 closed it completely — and the hole that remains is one axis further out
again: the contract quantifies over every input the CODE takes, and not at all over the
ARTIFACTS the change retires. Prose that describes behaviour is an output of the change just as
much as a log record is. This repo's law already says a diagnosis is not an instrument and that
served English had no mechanical guard; the instrument for this exact class was sitting
thirty lines away in the same test file, pointed at a different docstring.
