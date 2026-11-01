# Contract amendment r2: contract-165 (lead-165, 2026-10-31)

Base: your contract at acbce73 (18 tests, RED 10F/8P, satisfiability 138). Deadline: **45 min** wall-clock from this
directive's wake. At the deadline, report what you have and mark the rest NOT TRIED.

## Spawning is permitted
The "you do not spawn subagents" clause in your running prompt came from lore's stale project copy of your
definition. That copy is now deleted (#556, `26c3a20`). The operator's 2026-10-30 grant (acbce73, and the current
global `tdd-light-contract.md`) lets you spawn any subagent. Route per brief-base §3 as below: `haiku-runner` /
`haiku-worker` with NO `model` and NO `name`.

## What to add (rulings: RULING-S1-S2.md, plus two adopted items from your §Anything else)
1. **S1, per-tier refusal through ONE predicate** (RULING-S1-S2.md, pins 1–3; pin 4 is the audit's).
   - The contract names the chokepoint: the materialisation decision (dir present and non-empty) lives on
     `loremaster.source.snapshot.SnapshotLayout`. `Indexer._snapshot_materialized` delegates to it, and the deploy
     precondition evaluates it over the host root.
   - The agreement pin drives the deploy precondition and the REAL `Indexer._snapshot_materialized` from one fixture
     set: absent, empty, non-empty, and a regular file. Do not pin the predicate's method name.
   - `lore_impact` reports 0 test references for `Indexer._snapshot_materialized`, so this pin may be the first.
2. **S2:** the R1 matrix's file cell now asserts REFUSE, not just agreement.
3. **Item 4 (adopted):** the refusal text carries the exact, paste-ready command: `python -m loremaster.index --config
   <the real config path>`, the actual path and not a placeholder.
4. **R3 (adopted, your item 5):** on the recreate path, when the relaunch raises `CalledProcessError`, the stderr
   output includes the error's own text (exit code and command), not only the generic hint. Pin it once.

## Writable set
- `skills/lore-deploy/scripts/test_launch_snapshot_bind.py`
- OPTIONAL new `loremaster/tests/test_snapshot_materialized.py`, only if the server-side leg cannot live in the skill
  file; say why if you use it.
- Your report (append `## Amendment r2`, and update the SUMMARY block).
- A scratch copy (below).
Everything else is unchanged from your original brief.

## Steps, routed (lead-base v12: lookups are their own row, and nothing hides inside an inline step)
- **A. Lookups:** the `SnapshotLayout` API (`materialization_dir`); how `loremaster/tests/test_indexer.py` builds an
  `Indexer` with a `snapshot_root` (fixture names); `_loremaster_python` / `_schema_load_snippet` in
  `lore_deploy.py`. Run them as ONE parallel batch of reads (write the batch and its size in your routing table), or
  as a `haiku-worker` extraction returning `file:line` + signature, about 20 lines.
- **B. Pins:** inline (contract authorship).
- **C. RED run** → `haiku-runner`. Have it tee to a log and return `RAN:` + count + failing ids only. Command:
  `cd /home/ejprice/PycharmProjects/lore/skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q test_launch_snapshot_bind.py --timeout=300 -p no:cacheprovider`
  (add the optional loremaster file if you create one). Check that `RAN:` is your command.
- **D. Satisfiability:**
  1. `haiku-worker` runs `cd /home/ejprice/PycharmProjects/lore && ./scripts/scratch_copy.sh /var/tmp/claude-1000/c165-r2-scratch`
     and returns its exit code + its provenance line. This replaces your mirror: a full-repo copy, so
     `parents[3]` resolves, and provenance is asserted. Non-zero exit → STOP and report.
  2. You apply the reference build in that copy, inline: the SnapshotLayout predicate, the Indexer delegation, the
     deploy precondition, the paste-ready text and R3.
  3. `haiku-runner` with Command:
     `cd /var/tmp/claude-1000/c165-r2-scratch/skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -c "import loremaster, lore_deploy; print(loremaster.__file__); print(lore_deploy.__file__)" && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests ../../../loremaster/tests/test_indexer.py ../../../loremaster/tests/test_source.py --timeout=300 -p no:cacheprovider -n 8`
     Both `__file__` lines must be under `/var/tmp/claude-1000/c165-r2-scratch`, and 0 failed.
- **E. Gates** → `haiku-runner`: `cd /home/ejprice/PycharmProjects/lore && uv run ruff check skills/lore-deploy/scripts/test_launch_snapshot_bind.py && ./scripts/typecheck.sh 2>&1 | tail -5`

Spawn C and D.1 in one message. They are independent.

## Report
Under `## Amendment r2`:
- the routing table (written FIRST) and a `Fan-out:` line;
- the new and changed tests, each with the wrong build it catches;
- the RED count, the satisfiability count with both `__file__` lines, and the gate receipts;
- anything noticed.

Final message: the brief-base §1 micro-format.
