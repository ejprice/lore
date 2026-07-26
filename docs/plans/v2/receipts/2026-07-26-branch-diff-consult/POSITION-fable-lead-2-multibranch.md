# Fable position — follow-up scenarios A/B (committed BEFORE reading consultant replies)

Date: 2026-07-26. Ground truth established first: (1) the live index follows HEAD of the
watched root (lore_index renders its branch — verified live this session); (2) snapshots
are stamped by the indexer/reconcile wiring after every successful sweep that did work,
each carrying git_ref/git_branch (snapshots.py module docstring: "stamp() is UNCONDITIONAL
— the gate (full sweep success, sweep did something) is the CALLER's job (see
index/indexer.py / index/reconcile.py, pinned by test_indexer_snapshot_wiring.py)").

## Scenario B first, because it's nearly free — branch-in-place from main

The overlay never engages, and it doesn't need to. In-place, the LIVE index already holds
the feature-branch state (the watcher follows the checkout); what's "missing" is the MAIN
state — and that is exactly what the newest main-era snapshot holds. So "my work vs main,
structurally" is ALREADY a shipped mechanism: lore_diff(since=<newest snapshot whose
git_branch was main>) → function_deltas. And the ruled graph-over-the-delta serving needs
only the changed-set enumeration, which is `git diff --name-only <merge-base>` run at the
watched root — the overlay's own enumeration command, working verbatim in-place, with NO
overlay tier needed because the changed files are already indexed.

Design implication for packet 17: define the delta surface as TOPOLOGY-AGNOSTIC — "the
delta view of a root vs a base ref," where the root is either (a) a sibling worktree
(overlay engages: changed files must be chunked/embedded into the ephemeral tier) or
(b) the watched root itself on a branch (no overlay; base index is current; the before-
state for symbol deltas comes from the branch-point snapshot). One consumer surface, two
topologies. The in-place case is the EASY v1 — the worktree case is the hard half.

Gaps to close (render/teaching, not mechanism):
1. Discoverability: nothing teaches "your branch-vs-main comparison is a snapshot diff";
   nothing connects merge-base → the right snapshot. The surface should locate the
   branch-point snapshot itself (newest snapshot whose git_ref equals/ancestors the
   merge-base) and say which it chose.
2. Exactness honesty: a snapshot is sweep-time, not merge-base. If main advanced between
   the last main-era sweep and the branch, the diff over-attributes. Render both shas
   (snapshot git_ref AND merge-base) and flag divergence — cheap check.
3. No main-era snapshot exists (lore deployed after branching): REFUSE and teach (offer
   the git-only enumeration), never serve an empty or over-claiming diff (#131 class).

## Scenario A — standing visibility of main/staging/dev

Consumer honesty: the cross-branch questions I actually ask are git-shaped — "does staging
contain this fix" (git log/branch --contains), "what does dev's version of this file look
like" (git show dev:path — instant, exact). The genuinely lore-shaped case is narrow:
structure/semantic questions about THE DEPLOYED CODE when production tracks a branch the
watched root isn't on. Real, but better served by topology (point a root/worktree at that
ref) than by a second standing index — and in this repo prod is a baked image at a SHA,
where the honest answer is the sha, not a branch.

Mechanically, Scenario A is the overlay generalized: overlay identity keyed on (root, ref)
instead of worktree path; a standing staging-overlay = delta of main...staging, embedded
once, refreshed on advance. Cheap for slowly-diverging branches. But demand is speculative
in the fleet's actual workflow (one branch per session; Odoo = worktrees). Disposition:
DEFER with a named re-open trigger — "a deployment tracks a ref other than the watched
root's (staging-serving prod), or a workflow needs semantic search over a second
long-lived ref." Design rider NOW, costing one sentence in packet 17: key overlay identity
on (root, ref/merge-base), not path alone, so the ref-overlay generalization is not
foreclosed.

Does A reverse the ruled "ref-vs-ref never"? No — that ruling is about structural
COMPARISON of two arbitrary unchecked-out refs. Standing VISIBILITY of a named ref via a
ref-keyed overlay is adjacent but distinct; if the trigger fires, it slots into the
overlay design without touching the never. Flag to operator regardless (adjacency is
worth surfacing, not deciding silently).
