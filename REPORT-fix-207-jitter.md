# REPORT-fix-207-jitter

brief-base v6 read

**state:** done-with-deviations

**deviations (one line each):**
- The brief's named class `tenacity.wait_exponential_jitter` is the WRONG policy — I read the installed source and used `wait_random_exponential` (AWS Full Jitter) instead. §2.
- The brief said "no dependency to add"; `tenacity` was UNDECLARED (transitive via langchain-core only). I declared it. §2.
- **I did not commit. Another session committed my work inside `f65e062` — a commit labelled `fix(#211)`.** §1.
- Added a named seam `CalibrationEngine._backoff_delay` (prod change beyond the leaf edit) so the invariant can DRIVE that site. §4.
- `Retry-After` paths left un-jittered deliberately — unruled parameter, escalated as R2. §6.

**decisions-needed: ALL FOUR RULED by the lead 2026-07-25. Recorded here; three imply follow-up
work that is NOT in this commit.**
- **D1 — commit hygiene → DOCUMENT-AND-ACCEPT.** `f65e062` (59 files, 1865 insertions) holds
  both #207 and #211 under one name and will not be split: the branch is local, and a
  `reset --soft` re-stage of interleaved work from three agents risks losing more than it
  clarifies. Same ruling as the sibling's — *"a disclosed mixed commit is recoverable; a silent
  one is the thing that makes an audit read the wrong change."* The lead is committing this
  report so the provenance sits at a tracked address, and the cold-audit brief names it. §1.
- **D2 (R2) — jitter `Retry-After` → APPROVED, ADDITIVE ONLY, `W = 1.0s`. NOT YET
  IMPLEMENTED.** Constraint from the ruling: `retry_after + uniform(0, W)`, **never below the
  server's stated value** — jittering downward violates the server's instruction and is a worse
  bug than the herd. The existing KNOWN BOUND pin is to be retained but **retargeted at the
  WIDTH rather than the existence** of the jitter. §6.
- **D3 (R3) — eager-lease boot sleep → DO NOT MOVE BOOT TIMING. NOT YET IMPLEMENTED.** If
  decorrelation can be had *without* changing the ladder shape — keep the constant, add a small
  additive jitter — do that; decorrelation does not require an exponential ladder. If it cannot,
  leave it and keep the pin, with a **named measurement** as the decision point: *what is the
  health-check budget, and how much boot headroom exists?* Measure-then-tune, not a can-kick. §6.
- **D4 (R4) — `_txn_conflict_backoff_seconds` → DEFER TO ITS OWN WAVE. OWNER NEEDED.** Recorded
  not as a fresh idea but as **#202's own re-open trigger FIRING**: #202's recorded trigger is
  *"the next behavioural change to the retry policy evaluates tenacity FIRST"*, and consolidating
  `_txn`'s jitter into the shared policy IS that change. That wave must carry the mutation proofs
  its eleven guarded consumers demand and re-verify the runtime guard's `__code__`-frame
  coverage. It is much cheaper now that the shared policy exists. §6.

**receipt pointers:** not-mine failures §0 · commit situation §1 · tenacity comparison §2 ·
population + RED §3 · sharing proof §4 · mutation proofs §5 · raised findings §6 · old-world
adjudications §7 · gates + testpaths receipt §8 · known bound §10.

**lead rulings received 2026-07-25, after the work had landed — disposition:**
- *"Stage your scout.py hunks alone and commit; do not hold"* — **moot, and I had already done
  the staging half.** I filtered the patch to my 2 hunks and `git apply --cached`-ed them; the
  sibling then committed the whole index before I could commit. Nothing was held.
- *"Record the 6 `test_scout.py` failures as OUT-OF-BASELINE / NOT-MINE with the proof"* — done, §0.
- *"Put the tenacity comparison in the report"* — done, §2.
- *"Declare expected-RED before the run, from `--collect-only`, and diff both ways"* — **already
  applied**, and it caught a real defect in my own pin (§5).
- *"Confirm your new tests are inside `testpaths`"* — **checked, they are** — but my first
  *explanation* of why was false and is corrected in §8, along with a re-derived measurement of
  #199 (**150** ungated `scripts/` test nodes, not the "~50" three reports carried) and its
  direct consequence for this wave's `token_survey` site.
- *"Commit only your own paths, explicitly"* — I never ran `git add -A`/`.`/`-u` or `commit -a`
  at any point; every `git add` named explicit paths (§1).

---

## 0b. D2 + D3 LANDED — `776312b` (2026-07-26)

GO'd by the lead after the fix-wave audit. `git show --name-only 776312b` → exactly the
seven files below, all exclusively mine; no `git add -A`/`.`/`-u` at any point.

```
loremaster/loremaster/calibration/counting.py   loresigil/loresigil/backoff.py
loremaster/loremaster/server.py                 loresigil/tests/test_backoff.py
loremaster/tests/test_backoff_seam.py           scripts/token_survey.py
loremaster/tests/test_calibration_counting.py
```

**ONE helper, not two** — `additive_jitter(base_s, *, width_s)`. D2 and D3 are the same
policy (decorrelating a delay someone ELSE decided) reached by different paths; writing them
separately would have committed this wave's own sin inside the fix for it. Three call sites,
both new ones in `_DECLARED_SITES` **at birth**, so the sentinel mutation and coverage check
cover them from the first commit. Two DISTINCT sentinels now — a site calling the *wrong*
policy would still look "jittered" while returning values below a server's floor.

**Gates:** ruff clean tree-wide · mypy `lorescribe`/`loresigil` OK with **zero errors in any
file touched here** (109 pre-existing in `test_comms_*`) · **978 passed, 1 skipped**.

**Mutation proofs — declared from `--collect-only` BEFORE each run, diffed BOTH ways,
byte-exact restore verified:**

| mutation | declared | observed | verdict |
|---|---|---|---|
| **E** jitter removed (returns base) | 2 | 2 | EXACT |
| **F** jitter inverted (downward) | 3 | 4 | extra red is CORRECT — a downward span also fails the spans-its-width control; my declaration was incomplete, the test was not |
| **G** one site reverted to a private copy | 4 | 3 | **found a real weakness in MY OWN pin** — see below |

**⚠ Mutation G is the receipt of the session.** My adjudicated replacement
`7.0 <= slept[0] <= 7.0 + W` **stayed GREEN on an un-jittered build**, because an un-jittered
build sleeps exactly `7.0` — which is *inside* that range. The bound I had just called
"strictly stronger" certified the pre-D2 world in exactly the way the `== [7.0]` it replaced
did. It caught a *downward* jitter and was blind to an *absent* one. Strengthened with repeat
draws (8 sleeps, ≥6 distinct); re-ran G and it now goes RED naming the defect. **A one-way
check would have reported "all declared reds fired" and shipped a hollow pin — for the second
time in this wave, on the same instrument class.**

**Old-world pin adjudicated:** `test_retry_after_header_is_honoured`'s `== [7.0]` could only
hold while the path was deterministic. Preserved-with-pin-strengthened (floor property +
the jitter-exists discriminator). The retired KNOWN BOUND was **retargeted, not deleted** —
the residual bound is now the WIDTH (`1.0s` is chosen, never measured) and **#223**.

**Deviation:** both `_sleep_backoff` bodies narrowed their `try` to the `float()` parse. The
original wrapped the *sleep* too, so a `ValueError` raised by the sleep seam would have been
swallowed into the exponential path. Latent, never observed, disclosed here.

## 0a. THE BOTH-WAYS MUTATION DIFF CAUGHT A DEFECT IN MY OWN PIN — within one wave of adopting it

Surfaced here at the lead's direction as the strongest available argument for the practice.
Full detail in §5.

`CLAUDE.md` adopted (2026-07-26) the rule that a mutation proof must **declare its expected-RED
node ids before the run** (from `--collect-only`) and **diff both ways** — unexpected reds, *and
declared reds that stayed GREEN*. I applied it to three mutations. On the very first run it
caught a defect **in my own instrument**:

> `test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll` was DECLARED RED and **STAYED
> GREEN**. Mutation A had replaced `jittered_backoff_delay`'s entire body with the deterministic
> `min(base_s * 2**attempt, cap_s)` — but the module still *imported* `wait_random_exponential`,
> and my pin was a **substring scan over the file text**. A pin keyed on a TOKEN rather than the
> BEHAVIOUR, passing over a build it existed to reject.

Rewritten to walk the AST of `jittered_backoff_delay` and assert it **CALLS** the strategy;
re-ran the identical mutation, it goes RED. Two of six declarations for that mutation were wrong
on the first pass — **one my mistake, one a genuine instrument defect**. A one-way check would
have reported "all declared reds fired" and shipped the hollow pin.

## 0. OUT-OF-BASELINE, NOT-MINE FAILURES (lead-ruled — for the cold audit)

**Recorded at the lead's direction so a later audit does not read these as this wave's damage.**

Mid-session, `loremaster/tests/test_scout.py` showed **6 failures** that are absent from
`docs/plans/v2/receipts/2026-07-24-packet11i/BASELINE-RED.md`. They are **not mine** and they
postdate the baseline. Proof, which is the general instrument for this claim:

```
failure:  AttributeError: 'str' object has no attribute 'get_secret_value'
at:       loremaster/loremaster/store/_txn.py::signin_credentials
receipt:  git show HEAD:loremaster/loremaster/store/_txn.py | grep -c "def signin_credentials"
result:   0
```

**The failing symbol did not exist at HEAD, so no test at HEAD could fail on it.** It was
introduced by sibling `fix-211-secrets`' then-uncommitted work, in a mid-flight state where
some callers still passed `str`. Per the lead's ruling I did **not** fix them.

**They have since resolved**: after #211 landed (`f65e062`), `test_scout.py` passes —
`536 passed` on `test_scout.py` + `test_retry_seam.py`, and `953 passed, 1 skipped` on the
full affected set (§8).

The failing tests were:
`TestCommandDispatchAgainstRealSchema` ×5 (`test_empty_command_table_is_a_no_op_drain`,
`test_marking_an_already_done_command_claims_nothing_and_does_not_error`,
`test_reconcile_command_is_marked_done_with_processed_at`,
`test_handler_exception_marks_failed_and_scout_survives`,
`test_unknown_kind_is_marked_failed_and_scout_survives`) and
`TestCommandChannelLivePrimaryEndToEnd::test_running_subscriber_processes_an_inserted_pending_command`,
plus `TestScoutSweepStampsSnapshot::test_scout_sweep_stamps_a_snapshot_reflecting_the_indexed_files`.

## 1. ⚠ WHAT HAPPENED TO THE COMMIT — read this first

**I never ran `git commit`. My work was committed by a sibling builder, inside a commit about a
different concern.**

**The true shape, per the lead (2026-07-25):** the lead spawned **THREE builders into this one
worktree and told none of us** — me (#207), `fix-211-secrets` (#211), and `fix-210-charset`
(#210, already landed `c32800d` + `8b1343e`). The coordination I assumed existed never did.
What I diagnosed mid-session as "another session" was a sibling; the collision was structural,
not anyone's misbehaviour.

**Sibling-unblock status (checked after the fact):**
`fix-211-secrets` was blocked on my `calibration/counting.py` and `calibration/engine.py`.
Both are now **clean and fully committed** (`git status --short` on them is empty; `git log -1`
on each → `f65e062`), and their `api_key: str` sites are present and intact. **That blocker is
cleared** — ironically by the very commit that swallowed my work.

Timeline, all observed:

1. On arrival: 19 modified prod/test files + 2 untracked tests that were not mine.
2. Two of my `Edit` calls failed with *"File has been modified since read"* on `scout.py` and
   `counting.py` — a concurrent writer, not a linter.
3. `loremaster/loremaster/scout.py` became **contaminated**: their 5 #211 hunks and my 2 #207
   hunks interleaved in one file.
4. I escalated, did not commit, and staged only my own hunks (`git apply --cached` of a
   filtered patch — verified: exactly `+from loresigil import backoff` and the `_backoff`
   rewrite, none of their work).
5. When I inspected the index before committing, it held **59 files** — they had staged their
   entire #211 wave into the shared index. **I stopped and did not commit**, because a commit
   would have swept their in-flight work into a commit labelled #207.
6. While I was preserving my work, they committed. `git log --diff-filter=A --
   loresigil/loresigil/backoff.py` → **`f65e062 fix(#211): secrets are a TYPE, not a hope`**.

**Nothing was lost and everything is green** (§7) — but `f65e062` contains two unrelated
concerns and its message names only one. That is a one-concern-per-commit violation produced by
the shared worktree, not by a choice either agent made. **D1 is the lead's call.**

**Standing hazard worth fixing regardless of D1:** two sessions sharing one worktree share one
INDEX. Either can sweep the other's work into their commit, silently. Whatever assigned this
worktree to two agents needs to stop doing that.

## 2. THE BRIEF'S NAMED CLASS WAS WRONG — read the source, not the name

The brief named `tenacity.wait_exponential_jitter`. I read the installed source
(`.venv/lib/python3.14/site-packages/tenacity/wait.py`). It computes:

```python
jitter = random.uniform(0, self.jitter)          # self.jitter defaults to 1 (SECOND, fixed width)
result = self.initial * self.exp_base ** (retry_state.attempt_number - 1) + jitter
```

That is **equal jitter around a floor**: the delay can never fall below `initial * 2**n`, and
the jitter term is a *fixed ~1s width* regardless of window — at attempt 10 with `initial=1`
it is ~0.1% of the delay, i.e. effectively no decorrelation at all.

**This repo already ruled that insufficient.** `_txn.py::_txn_conflict_backoff_seconds` uses
full jitter (`uniform(0, window)`, reaching zero), and
`test_surreal_store.py::TestTxnConflictBackoffIsJittered::test_concurrent_racers_draw_full_jitter_down_to_zero`
**fails an equal-jitter build by name** (`wb13-equal-jitter`; message: *"jitter around a FLOOR,
not the full jitter the design ruled. Racers stay bunched"*). Adopting the brief's class would
have re-shipped the policy #102 rejected, and no growth-shaped pin would have caught it.

**The right class is `tenacity.wait_random_exponential`** — its own docstring says it
"corresponds to the **Full Jitter** algorithm" from AWS. Used that. My pin
`test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll` fails a build that switches to
the equal-jitter class, and the behavioural pin
`test_draws_reach_the_bottom_half_of_the_window` catches it name-blind.

**R1 — `tenacity` was UNDECLARED.** `grep -rn tenacity --include=pyproject.toml` returned
nothing; it was reachable only as a transitive dep of `langchain-core` (via `lorescribe`'s
`langchain-text-splitters`). Production code importing it on that basis breaks the day that
chain drops it. I added `tenacity>=9.0` to `loresigil/pyproject.toml`.

## 3. Population — my own count, plus the RED receipt

lore's index watches the MAIN checkout, not this worktree (#125) — **I used grep/AST/Read and
am saying so**, per the dogfood protocol's fallback clause (cases (a) and (c)).

The exhaustive instrument: **every backoff in this repo computed its window with a variable
exponent**, so an AST scan for `BinOp(op=Pow)` with a non-literal exponent enumerates the whole
population. Pre-fix it returned exactly **6**, with **zero false positives** across
`loremaster/`, `loresigil/`, `lorescribe/`, `scripts/`, `skills/`:

| # | site (symbol, not line) | window | jittered? |
|---|---|---|---|
| 1 | `loresigil/resilient.py::compute_backoff_delay` | 1.0 → 30.0 | **NO** |
| 2 | `loremaster/calibration/counting.py::AsyncClaudeTokenCounter._sleep_backoff` | 1.0 → 30.0 | **NO** |
| 3 | `loremaster/calibration/engine.py::CalibrationEngine._probe_loop` (inline) | 30.0 → 900.0 | **NO** |
| 4 | `loremaster/scout.py::CommandSubscriber._backoff` | 0.5 → 30.0 | **NO** |
| 5 | `scripts/token_survey.py::ClaudeTokenCounter._sleep_backoff` | 1.0 → 30.0 | **NO** |
| — | `loremaster/store/_txn.py::_txn_conflict_backoff_seconds` | 0.005 → 0.1 | **YES** (#102) — fenced by #202, untouched |

**FIVE un-jittered implementations — "at least five" reproduces exactly.**

**Where I differ from `pkgscout-loremaster` P5.** It reported "FOUR more private backoff
policies in `loremaster/`". I find **three** exponential ones there (counting, engine, scout).
Its fourth is `server.py::_EagerStartupLifespan._acquire_eager_lease_with_retry`, which sleeps
a **constant** `2.0` with no growth and no cap — un-jittered, but not an exponential backoff
policy. Raised as R3, not changed.

**RED receipt (pre-fix, at base `31d9e58`)** — 8 simultaneous clients, same attempt index:

```
loresigil.resilient.compute_backoff_delay(3)      distinct=1/8  [8.0, 8.0, 8.0]
calibration.counting  _sleep_backoff ladder(3)    distinct=1/8  [8.0, 8.0, 8.0]
calibration.engine    _probe_loop ladder(3)       distinct=1/8  [240.0, 240.0, 240.0]
scout.CommandSubscriber._backoff ladder(3)        distinct=1/8  [4.0, 4.0, 4.0]
scripts/token_survey  _sleep_backoff ladder(3)    distinct=1/8  [8.0, 8.0, 8.0]
[CONTROL, already jittered] _txn (#202, fenced)   distinct=8/8  [0.00243, 0.01089, 0.0064]
```

The control matters: the probe can see decorrelation where it exists, so `1/8` is a finding,
not a broken instrument. **Post-fix the AST scan returns 1** — only the fenced `_txn` seam.

## 4. The invariant (the point of the job)

`loresigil/loresigil/backoff.py` — one policy, `jittered_backoff_delay(attempt, *, base_s,
cap_s)`, drawing from tenacity's Full Jitter. Call sites **import the MODULE, not the
function**: late binding is what lets one `monkeypatch` reach every genuine caller, so a
private copy is distinguishable from the real thing. That is load-bearing, not style.

Two instruments in `loremaster/tests/test_backoff_seam.py`:

- **Sharing by mutation, with CHECKED COVERAGE.** The policy is replaced by a sentinel; every
  declared site is driven and must sleep the sentinel. `_DECLARED_SITES` is asserted **both
  ways** — a declared site nothing drives is an unguarded site wearing a guarantee.
  Deliberately **one test**, not an accumulator across the class: class state does not survive
  `-n auto`, which this repo runs by standing rule, so an accumulator would silently check a
  PARTIAL set on every parallel run.
- **The perimeter, allowlisting the SAFE.** Deny-by-default on variable exponentiation in
  production, with a **one-file** evidence-backed allowlist (`_txn.py`). Not a scan for
  forbidden shapes — `CLAUDE.md`'s six-defeat table says those always lose. Three positive
  controls: the scan fires on a verbatim copy of the #207 defect, stays silent on
  constant-exponent maths, and the allowlist entry is re-validated (if `_txn`'s full-jitter
  draw disappears, the exemption fails).

**Prod change beyond the leaf edit (disclosed):** `CalibrationEngine._backoff_delay` is a new
named seam. The delay was inline in `_probe_loop`, reachable only through the whole probe
harness — and a site a pin cannot drive is a site nothing certifies. It mirrors its sibling
`CommandSubscriber._backoff`. Without it the engine would have been a declared-but-undriven
hole, which is the exact failure the coverage check exists to prevent.

## 5. Mutation proofs — declared BEFORE the run, diffed BOTH ways

Following the discipline `CLAUDE.md` codified 2026-07-26 (§"FILING A RULE DOES NOT INSTALL
IT"): expected-RED node ids taken from `--collect-only` before running, and diffed in both
directions. `scripts/mutation_proof.py` is **untracked in the main checkout only** and was not
available in this worktree — I applied its discipline by hand and flag its unavailability
(R5). Each mutation asserted it LANDED in source before running.

| mutation | declared RED | observed RED | verdict |
|---|---|---|---|
| **A** — jitter made deterministic again (the #207 defect restored) | 6 | 6 | exact |
| **B** — swapped to tenacity's EQUAL-jitter class (the subtle wrong build) | 5 | 5 | exact |
| **C** — one call site reverted to a private copy (the SHARING proof) | 3 | 3 | exact |

Both files restored **byte-exact** (`diff -q`), 21 passed after restore.

**The both-ways diff immediately caught a real weakness in my own pin.** On the first run of
mutation A, `test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll` was DECLARED RED and
**STAYED GREEN**: the mutation replaced the function body with `min(base_s * 2**attempt,
cap_s)` while the module still *imported* `wait_random_exponential`, so a substring check over
the file text could not see it. I rewrote the pin to walk the AST of `jittered_backoff_delay`
and assert it **CALLS** the strategy; re-ran the same mutation and it goes RED. Two of my six
mutation-A declarations were wrong on that first run — one my mistake, one a genuine defect in
the instrument. A one-way check would have reported "all declared reds fired" and shipped it.

Mutation A also produced an **unexpected** RED that is correct and valuable: the perimeter
caught the deterministic mutant's own `**attempt`, in the policy module itself. Two independent
instruments catch the same regression.

## 6. Raised findings (NOT acted on — scope belongs to the operator)

- **R2 — the `Retry-After` path is the WORST lockstep case and I did not change it.**
  `counting.py` and `token_survey.py` sleep `min(float(retry_after), RETRY_MAX_DELAY_S)`, and
  *every* rate-limited client receives the **same** value from the server — more perfectly
  lockstepped than the exponential ladder ever was. Not changed because the correct policy
  jitters **above** the floor (sleeping less than the server asked is a protocol violation) and
  **W is an unruled parameter**; inventing it is a design decision, not a derivation. Exact
  edit on your ruling: add `retry_after_jitter_s` to `loresigil/backoff.py`, call it from both
  `_sleep_backoff` bodies. Recommend: fix, `W = 1.0s`. **Pinned as a KNOWN BOUND** so it cannot
  be silently inherited.
- **R3 — `server.py::_EagerStartupLifespan._acquire_eager_lease_with_retry` sleeps a CONSTANT**
  (`2.0`, `max_attempts=5`), un-jittered, no growth, no cap. Not changed: converting it to the
  shared exponential policy moves total boot-retry time ~8s → ~30s, which could cross a
  container health-check timeout. Recommend: jitter only, keep it constant.
- **R4 — `_txn_conflict_backoff_seconds` is now the LAST hand-rolled full-jitter copy.**
  Correct, mutation-proven, and fenced by #202, so untouched — but it is a second
  implementation of the policy `loresigil/backoff.py` now owns, which is the shape ONE
  IMPLEMENTATION forbids. Its allowlist entry carries a **named re-open trigger**: the day
  either jitter formula changes.
- **R5 — ~~`scripts/mutation_proof.py` is untracked~~ — WRONG, CORRECTED 2026-07-25.**
  **It IS tracked**, added by `cad340f` on `feat/surreal-unification`. It is simply absent from
  *this* branch (`pkt11i-floor-calibration-dark`, branched before it), so it was unavailable to
  me — the conclusion held, the stated reason did not. No action needed; the recommendation to
  commit it was moot.

  **How I got it wrong is the part worth keeping, and it is not the mechanism the lead
  proposed.** I never ran `git ls-files`. I ran `ls -la` on both paths (present in the main
  checkout, absent here) and combined that with the **session-start `git status` snapshot in my
  system context**, which showed `?? scripts/mutation_proof.py`. That snapshot was *accurate
  when taken* and went stale when `cad340f` landed mid-session. **I reported a stale
  observation in the present tense** — precisely what `brief-base` v6 §1 forbids: *"date and
  scope your claims WHERE YOU MAKE THEM… write 'measured <date> at `<sha>`', never
  'currently'."* In a tree three agents were committing to, a session-start snapshot has a
  shelf life of minutes. Re-derive before asserting; that law applies to my own context, not
  just to inherited numbers.

  The lead's generalisation is still true and worth recording even though it is not what
  happened here: **`git ls-files` is branch-scoped**, so in a worktree it answers "is this on
  MY branch", not "is this in the repo". The repo-wide question is `git log --all --
  <path>` — which from this worktree does find `cad340f`.
- **R6 — one prose surface my change INVALIDATED, fixed in place.**
  `test_voyage_context.py`'s `FAKE_SLEEP_WALL_BUDGET_S` comment argued *"the smallest REAL
  backoff delay is `compute_backoff_delay(0) == 1s`, so finishing under 0.5s cannot have slept
  for real."* Under full jitter that draw can be a millisecond, so the **inference died with
  the deterministic ladder**. I replaced the reasoning rather than leaving it to rot, and noted
  that the recorded sleep — not the wall clock — is what proves the fake seam ran.

## 7. Old-world tests adjudicated (the law that caught real ones)

Five existing assertions certified the OLD deterministic world. Each: the property that
survives is preserved and re-pinned; the property that was the defect is dropped.

| test | old assertion | adjudication |
|---|---|---|
| `test_calibration_engine::test_backoff_doubles_and_caps` | `== [30,60,120,240,480,900]` | **preserved-with-pin, strengthened.** Now records the engine's arguments INTO the shared policy — fixes base, cap, attempt sequence AND the per-attempt bound, fully deterministic. Strictly more discriminating than the old equality, which could not tell a wrong window from a wrong draw. |
| `test_calibration_engine` ×2 | `== [30.0]` | bound, not equality: one backoff, inside attempt 0's window. |
| `test_resilient::test_backoff_is_exponential` | `delays[0] < delays[1] < delays[2]` | **dropped — it was a pin AGAINST jitter and would have been FLAKY.** Under full jitter a later attempt draws from a wider window but may legitimately return a shorter delay; that asymmetry is what breaks a tie. Renamed and re-pinned as "each delay inside its own exponentially growing window". |
| `test_voyage_context::test_429_then_success_is_retried` | `== [compute_backoff_delay(0)]` | **dropped — false by construction under jitter** (it compared the recorded sleep against a second independent draw). Re-pinned as one backoff within attempt 0's window. |

One of these mattered a lot: the strict-ordering pin would have failed *intermittently* rather
than honestly — the exact shape that gets an invariant deleted by the next engineer.

## 8. Gates (on the committed state, `47ee6ed`)

- `uv run ruff check .` → **All checks passed!** (whole tree)
- `./scripts/typecheck.sh` → `lorescribe OK`, `loresigil OK`, `loremaster FAILED` —
  **109 errors, all in three files, NONE of them mine**:
  `test_comms_tool.py` (102), `test_comms_promise_registry.py` (6), `test_comms_wiring.py` (1).
  Attribution receipt: they are `AppContext.message_ledger` / `comms(grade=…)` signature
  errors from packet-03b comms work, and `grep -lic "backoff\|jitter"` over all three returns
  **nothing**. Zero mypy errors in any file I touched.
- `uv run pytest loresigil/tests/ test_backoff_seam test_calibration_engine
  test_calibration_counting test_scout test_retry_seam -n auto` →
  **`953 passed, 1 skipped, 1 warning in 11.79s`**
- New tests: 8 policy pins (`loresigil/tests/test_backoff.py`) + 13 invariant pins
  (`loremaster/tests/test_backoff_seam.py`).
- **Both new instruments are actually GATED — checked empirically** (the lead flagged that a
  sibling packet shipped two instruments outside `testpaths`, *"a guard nobody runs is a hope
  with a filename"*). Receipt: a bare `uv run pytest --collect-only -q` (no path arguments)
  collects **8** `test_backoff.py::` nodes and **13** `test_backoff_seam.py::` nodes — 21,
  matching the 21 that pass.

  ⚠ **CORRECTION (2026-07-25): my first explanation of WHY they are gated was FALSE.** I wrote
  that `[tool.pytest.ini_options]` has *"no `testpaths` key at all, so collection is
  rootdir-recursive."* **`testpaths` exists** — `["lorescribe/tests", "loresigil/tests",
  "loremaster/tests"]`. My `grep -A6` window ended **exactly one line before it**. The
  conclusion survived only because both instruments happen to live in covered directories.
  **The measurement was load-bearing and correct; the mechanism I attached to it was a guess
  that read like a finding.** Had collection truly been recursive, finding **#199** — which
  says `scripts/`'s tests have never run in any gate *because* `testpaths` excludes it — would
  have been false, and my claim would have quietly contradicted three independent reports.
  **#199 stands.**

- **#199 QUANTIFIED, and it lands on this wave.** Re-derived here rather than inherited:
  `scripts/` holds **5 test files / 150 collectable test nodes**, and a bare gated run collects
  **0** of them (`pytest --collect-only -q | grep -c "^scripts/"` → `0`; `pytest scripts/
  --collect-only -q` → `150 tests collected`). Three reports raised #199 as *"~50 tests"* — the
  measured figure is **150**.

  **Consequence for #207 specifically:** one of my five fixed sites is
  `scripts/token_survey.py::ClaudeTokenCounter._sleep_backoff`, whose module's own tests live
  in the ungated `scripts/` tree — and `grep` confirms `scripts/test_token_survey.py` contains
  **no** coverage of `_sleep_backoff` or the retry constants anyway. So the ONLY gated coverage
  of that backoff site is my sharing pin in `loremaster/tests/test_backoff_seam.py`, which
  drives it as declared site 5. That is not luck — it is the coverage-as-a-checked-variable
  design doing its job across a gate boundary — but it means **if that pin were ever narrowed
  to "loremaster only", the token_survey site would silently lose all gated coverage.**
- **No new failures.** The 6 `test_scout.py` failures I saw mid-session were the other
  session's incomplete #211 migration (`AttributeError: 'str' object has no attribute
  'get_secret_value'` at `_txn.py::signin_credentials`, a symbol that did not exist at
  `31d9e58`); they resolved when that session finished, and `test_scout.py` now passes.

## 9. What I did NOT touch, and why

- **`_txn.retry_on_conflict` and its loop** — #202 fences it; it is proven, guarded, and its
  delay computation is *already* full-jittered. Raised as R4 rather than changed.
- **`server.py` eager-lease backoff** — R3; changing it moves production boot timing.
- **The `Retry-After` paths** — R2; needs a ruled parameter.
- **Every file belonging to the other session's #211 wave** — `config.py`, `auth.py`,
  `logging_setup.py`, `_txn.py`, `server.py`, and the rest. I staged only my own `scout.py`
  hunks and never `git add`-ed a foreign path.

## 10. Known bound of the perimeter (pinned, not hidden)

The scan sees `2**attempt`; it does **not** see `delay *= 2` in a loop, or a lookup table.
Closing that means enumerating forbidden shapes, which loses. The bound is asserted by
`test_KNOWN_BOUND_a_multiplicative_backoff_evades_the_perimeter`, which goes RED the day the
shape changes and carries the message *"if you closed this deliberately, delete this pin and
say so."* Threat model is stated IN the instrument: it catches the **honest engineer** who adds
a retry loop and hand-writes its delay — the #207 defect verbatim, five times over — and is
explicitly **not** a boundary against deliberate evasion.
