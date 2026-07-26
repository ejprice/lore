# Branch/diff-awareness consult — synthesis (input to packet 17)

Date: 2026-07-26 · Trigger: operator question — *"the design supports worktrees; what about
branches? Don't agents like to compare their current work vs the branch? Shouldn't they see
how the branch and/or worktree they're on diffs?"* · Method: three INDEPENDENT model
positions — the lead (Fable) committed its position to a file in the same message that
spawned the two consultants, before reading either return.

Inputs, same directory: `POSITION-fable-lead.md` (Fable, pre-committed) ·
`REPORT-consultant-sonnet-1.md` (Sonnet 5) · `REPORT-consultant-opus-1.md` (Opus 5).
Related: finding #125 (origin), finding #232 (filed from this consult), packet 17
(`../..//17-worktree-overlay-design.md`), packet 23.

## Unanimous (3/3, independently)

1. **Never re-serve textual diffs.** git IS the diff engine; every consultant, answering as
   a consumer, said it would ROUTE AROUND any lore copy of `git diff` ("it would have to
   beat byte-exact-and-instant" — Sonnet; "worse than nothing: a trust debit for zero
   gain" — Opus). Packages-over-hand-rolling settles it.
2. **The line that IS the design** (Opus's phrasing, all three drew it): *git answers "what
   did I change"; git cannot answer "what does what I changed TOUCH."* Everything lore
   should serve sits on the far side — graph/structural answers over the changed set.
3. **The changed-symbol inventory is nearly free** — the overlay's own merge-base
   enumeration (packet 17 binding constraint) already computes its input, and
   `DiffEngine._function_deltas` is working precedent for symbol-level deltas.
4. **Do NOT grow `lore_diff` with a git-ref mode.** Two identity spaces (snapshot ids vs
   refs) under one polymorphic parameter is the DESIGN-LAW §1 confident-wrong. Opus found
   the hazard is PRIMED: snapshot rows already render `{git_branch}@{git_ref[:12]}`
   (`AppContext._render_snapshot_rows`) → finding #232. (The lead's pre-committed position
   had leaned toward reusing the verb with an explicitly-domained render; updated on the
   2-1 split plus the #232 receipt.)
5. **Branch-vs-branch for refs checked out nowhere: NEVER in this design** — it requires
   materialising a tree lore does not watch (against the spirit of the delta-only ban),
   `git diff a...b` already answers the textual case, and demand is speculative. Re-open
   trigger (deferral law): a wave where reviewers must compare two sibling worktrees'
   deltas STRUCTURALLY, or Odoo onboarding surfacing the same need.
6. **Branch identity honesty is already shipped** (packet 01's watched-root + git_branch
   render in `lore_index`) — the floor this builds above, not a gap.
7. **Trust riders if any delta surface ships** (riders in the same bullet as the
   requirement, per repo law): THREE identity values in every render — worktree path,
   branch + HEAD sha, AND the merge-base sha (two of three lies by omission after a
   rebase); committed-vs-uncommitted distinguished PER FILE; enumeration age rendered
   (house STALE-notice convention); refuse-never-serve-empty when git/merge-base fails
   (#131's class); the base-served caveat carries a NUMBER ("N files in your changed set
   are not graph-analysed"); hostile fixtures on every render interpolating
   worktree-supplied branch/path (already binding in packet 23).

## The one genuine fork (operator ruling needed)

**V1 scope of delta-scoped serving.** Both consultants agree on WHAT is valuable; they
split on WHEN:

- **Opus Option 1 — "graph over the delta; git keeps the text" (Fable concurs):** v1 ships
  the changed-symbol inventory in the overlay REGISTRATION render, search scoped to the
  changed set (a filter, not a feature), AND base-served `lore_impact`/`tests_for` fanned
  out over the changed set behind packet 17's ruled, number-bearing caveat. Argument: the
  fan-out is the actual labour ("per-symbol lore_impact exists and I still don't run it 40
  times" — the #125 receipt is agents NOT doing the loop); packet 17's clause makes
  base-served-with-caveat the ruled v1 form — batching it is not the v2 delta-DERIVATION.
- **Sonnet minimal:** v1 = changed-symbol inventory ONLY (as a field on the worktree-view
  render); impact/tests-for-the-delta inherit packet 17's v2 disposition — cite the ruling,
  don't re-decide it. Offered alternative: defer even the inventory and let wave-O
  experience decide.

Lead recommendation: **Opus Option 1**, because it closes the exact gap #125 measured
(structure questions in worktrees answered by grep) with zero new mechanism — only
batching of already-ruled base-served answers — while the Sonnet reading leaves the #125
question answered only if the agent thinks to run the per-symbol loop, which the consumer
evidence says it does not.

## Secondary decision for packet 23 (Opus §C)

Where the overlay's `git merge-base` / `git diff --name-only` calls live: inside the ONE
sanctioned exec seam (`index/snapshots.py`, beside `capture_git_identity`), or a reviewed
addition to `SANCTIONED_EXEC_MODULES` — either way a deliberate, operator-visible edit.
Derived binary set unchanged (`git` already in it).

## Net answer to the operator's question

Agents do want to compare their work vs the branch — and for the TEXTUAL comparison they
already have the perfect tool (git, via Bash). What they lack, and what #125 measured them
grepping for, is the STRUCTURAL comparison: which symbols changed, who calls them, which
tests cover them. "Branch support" therefore enters the design not as a new branch/diff
engine but as delta-scoped graph serving on the overlay packet 17 already designs —
plus one explicit non-goal (ref-vs-ref, with a named re-open trigger) and one recorded
no-go (no git-ref mode on `lore_diff`, #232).
