> **Read with care (lead, 2026-11-10):** this sidecar's brief carried the lead's own diagnosis and its gate-copy proposal, so the answer starts from the lead's framing (operator: "you polluted fable"). The unframed answer is `2026-11-10-parallel-and-test-speed-independent.md`.

brief-base v27 read · brief project v7 read

# Parallel agents and test speed — design options (2026-11-10)

Author: `sidecar-parallel-1` (design sidecar, session `lore-a-20261107`).
Base: `41b6235` on `feat/surreal-unification`, measured 2026-11-10. This doc recommends; the
operator rules.

## Summary block

- **State:** done-with-deviations.
- **Deviations:** (1) my probe to time a clone plus `uv sync --all-packages` was refused by
  the permission system, so that cost is unmeasured. (2) The Q2 recommendations that depend
  on per-test timing and worker scaling are conditional: `eval-testrules-1` is measuring
  both (`docs/design/2026-11-10-test-rules-evaluation.md`, in progress when I wrote this),
  and I did not duplicate or read its numbers.
- **Packages considered:** git clone (direct knowledge of git, not probed here): use ·
  Claude Code's `isolation: "worktree"` (read: the Agent tool schema and this repo's
  `.claude/settings.json`, which sets `worktree.bgIsolation: none`): keep_with_trigger, the
  trigger being the #284/#185 fix · pytest-xdist 3.8.0 `--dist worksteal` and
  `--maxprocesses` (read: installed `xdist/plugin.py`): use · pytest-testmon and a CI runner:
  not installed, not read, no verdict; a package scout should read them.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none. No new symbol is proposed; option B changes `scratch_copy.sh`
  rather than adding a script.
- **Graded:** n/a — no artifact graded. HEAD at report: `41b6235`.
- **Decisions needed:** 8 for Q1 and 6 for Q2, listed at the end of each question.
- **Receipt pointers:** §Q1 "What is actually blocking them"; §Q2 "What is measured";
  §Method and limits.
- **Fan-out:** haiku 0 · sonnet 2 · peak 2.

## The short answer

| | Short term (days) | Medium term (weeks) | Long term |
|---|---|---|---|
| **Q1 parallel agents** | One clone per code packet; its agents commit there; the lead fast-forwards into the main checkout | Narrow packet 17 to the local case and run it; delete what only the shared tree needed | CI on the integration branch; the overlay build (packet 23) |
| **Q2 test speed** | Make the gate's worker count a constant, and have the gate apply its own cap and print its count; then read the evaluator's timing | Act on that timing: the levers are worker count, the per-test database cost, and the tests that spawn a nested pytest | CI runs the full suite once per integrated commit; agents run targeted sets only |

Both questions have the same root. Agents share one mutable tree and one hand-assembled test
command, so each agent re-derives identity and safety by hand. The recommendations move those
two things into git and into the gate, and delete the instruments built around their absence.

---

## Q1. How do we unblock agents working in parallel?

### What is actually blocking them

One thing: several writers share one mutable working tree. The rest is scaffolding built to
live with that.

- **Receipts cannot match the graded commit.** In packet 58's first cold audit the builder
  gated in the shared tree. None of its receipts could be verified, the tree changed during
  the run (`DIRTY` went 5 → 6 → 7), and the auditor reran the gates
  (`docs/plans/v2/receipts/2026-11-09-packet58/coldaudit-58-ca58-receipts.md` §FINDINGS F-1).
  That audit's own first decision-needed asks whether builders should gate in a copy.
- **A private copy already fixes most of it.** In the second delta audit the builder gated in
  its own copy, and no gate was rerun. The auditor still had to rebuild the tree hash by
  hand, because the copy held five untracked `REPORT-*.md` files and one script without a
  header that was added later (`coldaudit-58-delta2-ca58e-receipts.md` §B.1). Every
  mismatch was content that had not been committed.
- **The "scratch copy" copies the mix.** `scripts/scratch_copy.sh` rsyncs the live
  filesystem, so the copy inherits every other session's uncommitted edits. Auditors work
  around it with a second step, `git checkout <sha> -- .`, which still leaves untracked
  files in place (same receipts, "Scratch copy" lines).
- **Two instruments answer "which tree did this run on?"**:
  `~/.claude/orchestration/tree_id.sh` (a content hash that includes untracked files) and
  `scripts/tree_fingerprint.sh` (#192, a before-and-after diff). Both exist because the tree
  can move under a run.
- **The worktree ban's two listed blockers do not stop an agent working in a private tree.**
  #134 is about deploying lore against a worktree, which nobody needs if lore stays deployed
  on the main checkout. #125 is lore not seeing code outside the tree it watches. That is a
  lost capability, and `lore_index()` already names the watched root and branch. The hazard
  that does bite is #284/#185: a copy of a worktree drives the real worktree's git index. It
  exists only because a worktree's `.git` is a pointer file.
- **Worktrees have run here under operator exception**: the #102 wave (#125), packet 10
  (#185), packet 11i (#220's correction) and packet 44 (#284).

### Options

| Option | Deletes | Adds | Cost | Risk | Unblocks |
|---|---|---|---|---|---|
| **A. Shared tree, plus `gate_copy.sh` and `tree_id.sh --manifest`** (the lead's stop-gap) | nothing | a script, its test file, a manifest mode, and a hand-list of "the builder's files" for each gate run | a small build, and a list to keep right on every run | a file missing from the list gates a tree that is neither HEAD nor the builder's; all work before the final gate still runs on the mix | final-gate receipts only |
| **B. One clone per packet, commit first** | the rsync body of `scratch_copy.sh`; `scripts/tree_fingerprint.sh`; "agents never commit, the lead commits by path" for code; the `cp -a` backup law for uncommitted trees; audit reruns of mismatched gates; the #284/#185 class (a clone's `.git` is a directory); A is never built | one provisioning step per packet; a rule that the packet's agents commit on its branch; fast-forward-only integration | clone plus sync time is **not measured**; about 330 MB per clone (77 MB tree, 252 MB venv, measured) | the packet's uncommitted code is invisible to lore until integrated (#125); conflicts in files every packet edits; a stale base needs a rebase and a short re-gate | parallel packets now; receipts that verify by commit id |
| **C. One git worktree per packet** (the Agent tool's `isolation: "worktree"`) | the same as B, except the #284/#185 class stays | lifting the ban; the #284/#185 fix (another session has it uncommitted); `uv sync` and `lore.yaml` per worktree | no fetch step, because refs are shared | a scratch copy of a worktree mutates the real index until that fix lands; whether `ruff check .` and mypy from the main tree walk `.claude/worktrees/` is not checked | the same as B, after the fix lands |
| **D. One lore instance per clone** | — | a container and a full index per clone | a cold index took about 3 hours for 865 files (2026-08-12); the shared embedder admits one full-rate indexer, so a second one makes both fail with 429s (2026-09-24) | starves production indexing | nothing soon. Ruled out, and the 2026-07-14 delta-only ruling already bans it |
| **E. Delta overlay** (packets 17 and 23, as ruled) | the #125 gap; the ban itself | a registered view per private tree, fed from the host, because the container cannot see a path outside `/workspace` | a design packet and a build packet, neither started | the design carries hosted multi-user riders the local case does not need | lore over an agent's own uncommitted delta |
| **F. CI on the integration branch** | hand-run full suites, the full-suite lock, receipt tables, runner babysitting | a runner service on this host and a merge rule | a host service, which needs operator approval | a red CI run blocks every packet until fixed | a receipt becomes a lookup by commit id |

### Recommendation, short term: B. Confidence MEDIUM.

The shape, in four rules:

1. **The main checkout is for integration and documents.** Nobody edits code in it. lore keeps
   watching it, so its index holds integrated commits and not a mix of sessions' edits.
2. **Each code packet gets one clone outside the repo, on one branch.** A packet's roles run
   in sequence (contract, adversary, build, audit), so they share it. Throwaway copies for
   wrong builds and mutation proofs are clones of that clone.
3. **Agents commit on the packet branch, and final gates run at a clean commit.** Reports stay
   in the main checkout or the lead's directory, so they never dirty the clone. A gate log
   whose header reads `DIRTY_FILES=0` then describes exactly one commit. `tree_id.sh` needs
   no change.
4. **The lead integrates by fast-forward only**, after a rebase onto the current tip, and
   before the cold audit, as packets do today. The audit then grades a commit that lore has
   indexed, so auditors keep lore.

Why B and not the others:

- **Over A:** A adds a script and a hand-list in order to keep the shared tree. B needs the
  same copy and no list, and it covers the whole build, not only the last gate.
- **Over C, for now:** B needs nothing unbuilt and cannot hit #284/#185. C waits on another
  session's uncommitted fix and on lifting the ban.

What B costs:

- A builder cannot ask lore about symbols it has not yet committed and integrated. It greps
  its clone; the standing hook text already tells agents that.
- Integration is serial. Two packets that finish together land one after the other, and the
  second rebases and re-runs its targeted gates.

Why MEDIUM and not HIGH: three things are unmeasured.

1. **Provisioning time.** My timing probe was refused. That is also one sample that an agent
   creating its own clone may be refused, so the lead, or a runner the lead briefs,
   provisions it.
2. **Whether the suite passes in a clean clone.**
   `skills/lore-deploy/scripts/test_launch_snapshot_bind.py` calls `pytest.fail` when the
   gitignored `lore.yaml` is absent, so provisioning copies that file. Other dependencies on
   ignored files may exist. One targeted run in a clone, compared with the shared tree, would
   show them.
3. **How often two packets edit the same file.** `scripts/pending_contracts.yaml` is the
   known one.

### Recommendation, medium term: narrow packet 17, then delete. Confidence MEDIUM.

- Once clones carry the parallelism, packet 17 is no longer "the parallelism enabler" that
  INDEX row 17 calls it. Its job shrinks to giving an agent lore over its own delta. The
  hosted riders are already assigned to packets 36–39; the local design has one question
  left, which is how a host-side feeder registers a private tree's changed files as a view.
- Delete what only the shared tree needed: the items under "Deletes" for B, and the
  CLAUDE.md paragraphs that teach them.
- Revisit clone versus worktree only if clone provisioning time turns out to matter.

### Recommendation, long term: F, then packet 23. Confidence MEDIUM on the direction, LOW on the tool.

- lore's CLAUDE.md already names the trigger: "the day this repo gains CI, currency is its
  first job". With a commit per packet branch, a runner can gate each pushed commit in a
  clean checkout and record the result under the commit id. Agents and auditors then read a
  result instead of running or re-verifying one.
- LOW on the tool because I read no runner's documentation. The remote is
  `github.com:ejprice/lore`, so a self-hosted runner is one candidate, and a local runner is
  another. A package scout should compare them before a ruling.

### Operator decisions for Q1

1. **Clones now?** May a code packet work in its own clone of the main checkout, starting
   with the next packet? A clone is not a worktree, so the ban's text does not cover it, but
   its intent might.
2. **Agents commit?** May a packet's agents commit on the packet branch inside its clone?
   This replaces "the lead commits" for code. The lead still integrates.
3. **Fast-forward only?** Integrate by rebase and fast-forward, so the gated tree is the
   integrated tree. The alternative is merge commits, which integrate a tree nobody gated.
4. **`scratch_copy.sh` from a commit?** Change its source from an rsync of the filesystem to
   a clone of a named commit. This overlaps the other session's uncommitted #284/#185 work in
   `scripts/test_scratch_copy.py`, so rule the order before either lands.
5. **Drop `gate_copy.sh` and `tree_id.sh --manifest`?** Neither is needed under 1–3.
6. **Delete `scripts/tree_fingerprint.sh`** and its test once packets run in clones?
7. **Re-scope packet 17** to the local case, leaving the hosted riders with 36–39?
8. **CI:** commission a package scout to compare runners? Installing one is a host change.

---

## Q2. How do we speed up test runs, or run them in parallel?

### What is measured

- **Size.** 15,360 tests collect in 17.4 s; 315 are parked and deselected by default
  (`pytest --collect-only -q` under the cgroup cap, 2026-11-10). 12,256 of the 15,045
  default tests are in `loremaster/tests`. 1,154 are under `scripts/`, which are tests of the
  gate and scratch tooling.
- **Wall time.** The full suite took 17 min 25 s and 16 min 53 s at 12 workers, with a 10.5G
  peak (`workflow-pilot-coldaudit-58.md`, §Measurements and Addendum 2).
- **Nobody knows where the time goes.** No full-suite log on this host has a `--durations`
  section, and the gate deletes its junit file when it exits (#627). The three logs that do
  print durations are small runs.
- **The sanctioned full-suite command fails when it runs alone.**
  `scripts/_pytest_sessions.py` answers `auto` (64 workers) when no other process on the box
  has "pytest" in its command line, and the 16G cap then kills the run after about 49 s. Two
  of three solo attempts on 2026-11-10 died this way (#508, annotations). Each one cost an
  audit a rerun.
- **The gate's pytest leg applies no cap, no timeout and no lock itself.** The cap, the lock
  and `--maxprocesses=12` are prose that every brief must carry.
- **The store fixtures are function-scoped.** `surreal_env` mints a database, opens and
  closes an admin connection, and drops the database at teardown, once per test. 9,004 tests
  sit in files that use the live-store harness. That count is a keyword match by a Sonnet
  agent and is an upper bound.
- **About 850 tests sit in files that spawn a nested pytest**, mostly under `scripts/`. This
  is also a keyword match and an upper bound.
- **Scaling is not known to be linear.** In July, 7,368 tests ran in 194 s at 64 workers
  (`docs/plans/v2/receipts/2026-07-26-packet42/REPORT-builder-pkt42-1.md`). That is about 38
  tests a second, against about 15 a second at 12 workers now. The suites differ and the
  runs are months apart, so this is a hint and no more: five times the workers bought about
  two and a half times the throughput.
- **Targeted runs can already overlap.** The only serialised run is the full suite. What
  stopped parallel work was the shared tree (Q1), not the test rules.

### Options

| Option | Deletes | Adds | Cost | Risk | Unblocks |
|---|---|---|---|---|---|
| **1. A constant worker count in the gate** | the `auto` branch of `pytest_worker_count`; the `--maxprocesses=12` workaround in the audit workflow; the tests of that branch in `scripts/test_pytest_workers_503.py` (how many of its 105 tests, I did not count) | nothing | a few lines | the box sits partly idle when one suite runs alone, until option 3 sets a better number | the full-suite command stops dying when alone |
| **2. The gate applies its own cap and lock, prints its count and worker count, and keeps its junit** (#627) | the wrapper prose in every brief (`flock … systemd-run … -- --maxprocesses=12`); the runner's separate `--junitxml` | a few lines in `pending_contract_gate.py` | small | a gate that re-executes itself under `systemd-run` needs one test that the cap really applies | one short command; a passed count and per-test timing on every full run |
| **3. Set the worker count and cap from measurement** | the guess behind "12 and 16G" | nothing | the evaluator's scaling runs, already under way | a higher count may be limited by the single test store and not by memory | possibly a much shorter suite; not known yet |
| **4. `--dist worksteal`** | nothing | one flag | one comparison run | none known; installed xdist 3.8.0 offers it | a shorter tail if a few long tests queue behind one worker |
| **5. Drop the one-full-suite lock** | the `flock` rule | nothing | the evaluator's concurrency result | several suites at once share one test store | parallel full suites |
| **6. Cut the per-test database cost** (for example the test store on memory-backed storage, or a wider fixture scope) | depends on the form | depends on the form | unknown until timing shows setup and teardown dominate | a memory-backed test store differs from production's RocksDB, which is the "test environment is a fiction" class; a wider fixture scope weakens isolation | possibly large; not known yet |
| **7. Delete tests of retired tooling** | the tests of scripts with no caller, and the Phase 4 conversion set already ruled on 2026-11-09 | nothing | a sweep | small: the scripts with no caller that I found carry tens of tests, not thousands | a little |
| **8. Select targeted tests by measured coverage** (pytest-testmon is one candidate) | the hand derivation from `lore_impact`, which is known to be incomplete (#563) | a dependency and a coverage database per clone | unknown; not installed and not read | its behaviour under xdist is unread | faster and more accurate targeted runs |
| **9. CI runs the full suite** (option F of Q1) | the once-per-packet full suite by hand, the lock, the runner babysitting | a runner | a host service | as in Q1 | the full suite leaves the agents' clock |

### Recommendation, short term: 1 and 2 now; 3, 4 and 5 from the evaluator's numbers. Confidence HIGH on 1 and 2.

- **1 is already law in prose.** CLAUDE.md says never to run `-n auto` and records #508 as a
  bound "until a builder changes it". Two failed full suites in one day is the cost of
  leaving it.
- **2 moves three rules from every brief into the one program that runs the suite.** It also
  supplies the two things that are missing: a passed count, which the law on green claims
  needs, and the per-test timing that every later speed decision needs.
- **3, 4 and 5 are measurements, and they are in progress.** `eval-testrules-1` is running a
  full suite with durations, a concurrency leg and a worker-scaling leg. I give no number
  for the result. The decision point is its report; the operator decides the worker count,
  the cap and the lock from it.

### Recommendation, medium term: spend the timing data. Confidence LOW, because the data does not exist yet.

My guess, labelled as a guess, is that the time sits in two places: the per-test database
mint and drop, and the tests that start a nested pytest. If the durations show setup and
teardown outweigh the test bodies, option 6 is the lever, and the store reference
(`docs/reference/surrealdb-31-capabilities.md`) is read before any change to how the test
store runs. If the nested-pytest files dominate, the lever is those files. If neither does,
the worker count is the only lever, and option 3 has already pulled it.

### Recommendation, long term: 9, with 8 if a scout clears it. Confidence MEDIUM on 9, LOW on 8.

With a commit per packet and a runner, the full suite runs once per integrated commit and no
agent waits on it. Agents run targeted sets only, and those are short today. Option 8 would
replace a derivation that is known to miss tests, but I have not read the package.

### Operator decisions for Q2

1. **Constant worker count?** Replace "auto when alone" (ruling of 2026-09-26, item 3) with
   one number, 12 until the scaling result is in.
2. **The gate owns the cap, the lock, the count and the junit?** This fixes #627 in the gate.
3. **Worker count and memory cap:** set both from the evaluator's scaling result.
4. **The one-full-suite lock:** keep or drop, from the evaluator's concurrency result.
5. **A package scout** for coverage-based selection and for the CI runner (one scout, both).
6. **pytest-memray:** CLAUDE.md orders it for memory defects, and it is not in `uv.lock`.
   Install it or strike the line?

---

## Noticed while reading (not asked; do you want any of these addressed?)

- INDEX row 17 still describes #220 as "an orphaned worktree with 39 unmerged commits". The
  operator withdrew that on 2026-07-26: it was packet 11i, live.
- `zero_test_store.sh` and `contention_hunt.sh` have no caller in the repo.
  `forgery_door_sweep.py` says in its own header that it was not ported to the 3.x SDK.
  `c3_wrongbuild_driver.py` and `c3_harness_repair.py` serve one retired contract.
- `scripts/pending_contracts.yaml` holds one bound and no `active:` key, while CLAUDE.md
  tells a packet to set `active: true` on its own bound. I did not check how the key is read
  when absent.
- No test is deselected by the `wire` marker by default, and no slow or integration marker
  exists (from the Sonnet census; I did not re-check it).
- `test_launch_snapshot_bind.py` depends on a gitignored host file, so it cannot pass in any
  clean checkout of a commit.

## Method and limits

- **Routing** (written before the first sweep): receipts and findings read by me; the
  scaffolding inventory and the test-time census drafted by two Sonnet agents and sampled by
  me. Three inventory rows were checked against the files (`tree_fingerprint.sh`,
  `_pytest_sessions.py`, the rsync in `scratch_copy.sh`) and three census claims against
  their sources (the collection count, the July baseline, the `surreal_env` fixture). All six
  matched. The two keyword counts (9,004 live-store tests, about 850 nested-pytest tests)
  were not re-derived.
- **Grep fallbacks, said out loud:** config file names in tests (`lore.yaml`) and text in
  receipt files. Both are non-symbol textual seams. No lore tool missed, so no friction was
  filed.
- **Not measured:** clone and sync time; the suite in a clean clone; per-test durations;
  worker scaling; whether the test store or the CPU limits a full run.
- **Not read:** pytest-testmon, any CI runner, the harness's worktree placement and cleanup.
- The log of the 17 min 25 s run was not found; the figure is from the pilot report.
