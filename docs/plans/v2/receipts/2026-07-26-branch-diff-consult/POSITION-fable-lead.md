# Fable position — branch/diff awareness in lore (committed BEFORE reading consultant returns)

Date: 2026-07-26. Receipt of independence: this file is written in the same message that
spawns consultant-sonnet-1 and consultant-opus-1; neither return has been read.

## 1. "Branch support" decomposes into three different capabilities

- **(a) Branch identity honesty** — knowing which ref the index reflects. Already shipped:
  packet 01's watched-root + git_branch render in `lore_index` (verified live this session:
  `workspace.roots[0].git_branch = feat/surreal-unification`).
- **(b) Diff visibility** — "what does my worktree/branch change vs its base?" The packet 17
  overlay design already COMPUTES this (merge-base `git diff --name-only` enumeration is the
  overlay's input) but never SERVES it as an answer surface.
- **(c) Branch-vs-branch** — two arbitrary refs, neither checked out. Not designed; I'd rule
  it out of v1 entirely.

## 2. Packages-over-hand-rolling: git IS the diff engine

Agents have Bash. A lore surface re-serving textual diffs is a hand-rolled twin of git with
worse fidelity — banned by the two-sided rule. What git CANNOT serve, and lore uniquely can,
is the STRUCTURAL layer over the diff: which symbols changed, blast radius of the changed
set (impact over the delta), covering tests for the delta, semantic search scoped to "my
changes". That is exactly packet 17's "scoped delta-derivation v2" gesture. So: textual
diff → git (already possible, keep it there); structural diff → lore (and the overlay
already computes its input).

## 3. The cheap v1 increment

Since the overlay must enumerate the changed set anyway, RENDER it: per-file + per-symbol
delta, citing merge-base ref + worktree branch + committed/uncommitted status. Nearly free,
and it directly answers "compare my work vs the branch."

Surface fork (operator to rule): grow `lore_diff` with a ref/view mode vs render it on the
overlay view. Caution: `lore_diff` today means TEMPORAL (snapshots). Overloading one verb
with two diff domains (time vs ref) is a trust/confusion hazard — the render would have to
name its domain explicitly. But "prefer no new tool" (packet 17 OQ2, exact-set pin) pushes
toward reusing the verb. I lean: same tool, explicitly-domained render, because the
consumer question is the same shape ("what changed between X and Y") and a 16th tool costs
a deliberate pin bump plus instruction surface.

## 4. Trust doctrine bearing (why this is load-bearing, not convenience)

#125's measured receipts: both #102-wave auditors in worktrees fell back to grep for EVERY
structure question. An agent that cannot see its own work in lore routes around lore for
the whole session. The consumer's first question in any review/build wave is "what
changed?" — if lore cannot answer it, lore is out of the loop at step one, in precisely the
fleet's primary workflow (worktree waves, the Odoo case). Diff-awareness is the trust
doctrine applied to the fleet's actual working topology.

## 5. Ruled out for now (with re-open trigger)

Arbitrary ref-vs-ref structural comparison: git serves the textual case; no structural
index exists for either side unless indexed; demand is speculative. Ledger with a named
re-open trigger: "a wave where reviewers must compare two sibling worktrees' deltas
structurally" (or the Odoo onboarding surfacing the same need).

## 6. The generalization worth NAMING (not building)

Multi-branch simultaneous indexing (main AND a feature ref both queryable) is the overlay
mechanism where the "worktree" is a ref, not a path. The design doc should name this as
the generalization so the overlay's schema doesn't foreclose it (e.g., overlay identity
keyed on (root, ref) rather than path alone) — but build nothing.
