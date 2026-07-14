# PKT-33 — Worktree overlay · DESIGN (#125, operator-ruled first-class 2026-07-14)
size ~0.15 wu · wave L · depends: none · builds: PKT-34
law: DESIGN-LAW §1 (client law — honest, cited renders), §12 · feedback law: brief the
operator in plain language before the ruling

## Mission
Design (not build) worktree visibility. lore's index cannot see a sibling git worktree —
which is precisely where audited/in-flight fleet work lives (#125: both #102-wave auditors
fell back to grep for every structure question). The Odoo workflow is worktree-heavy, so
this is load-bearing for wave O, not a convenience.

## Binding operator constraints (ruled 2026-07-14 — the design works INSIDE these)
- **DELTA-ONLY. Full-tree indexing of a worktree is BANNED.** Enumerate the changed set via
  `git diff --name-only` against the merge-base (captures uncommitted edits); chunk/embed
  ONLY those files into an **ephemeral overlay tier**; sha-unchanged files serve from the
  base index at zero cost (the sha-keyed reconcile already skips them by construction;
  tier-coexistence machinery exists — PKT-18 pins it).
- **Serving = overlay-shadows-base per file**: overlay hits replace base hits for changed
  paths; deleted files masked; everything else serves from base.
- **Auto-reap**: worktree gone → overlay dropped.
- **V1 tool scope: search / get_symbol / read / diff over changed files.** impact/dead_code
  stay base-served with an EXPLICIT caveat when the target is in the changed set — scoped
  delta-derivation (changed files + direct importers) is the designed-for v2, not v1.

## Open design questions (the doc answers each with receipts; operator rules the forks)
1. Registration surface: lore-deploy verb (worktree slug) vs `lore_index` alternate-root
   vs a session-scoped view registration on the existing surface (#125 filed all three as
   candidates (a)/(b)/(c) — candidate (c)'s minimum, the watched-path/branch render, ships
   in PKT-29 regardless).
2. View addressing at query time: per-call parameter vs per-session default; what the
   14/15-tool exact-set pin implies (a new tool needs a deliberate pin bump — prefer no
   new tool).
3. Freshness: on-register reconcile + wait_for_fresh analogue vs a watcher on the (small)
   changed set; worktrees are short-lived — measure before choosing the watcher.
4. Reap trigger: worktree dir missing vs `git worktree list` reconcile vs age; what
   happens to an overlay whose base moved (merge-base drift after a rebase).
5. Multi-overlay coexistence (two concurrent worktrees; the Odoo case: overlays fork the
   custom tier only — core/enterprise static tiers never fork).
6. The graph-caveat contract wording (DESIGN-LAW §1 honesty: a caveat names WHAT is
   unverified, never a vague warning).

## Entry check
`lore_findings` → #125 open with the full body (the two auditor receipts + the three
affordance candidates). PKT-29's watched-path/branch line already deployed (cite it as the
floor this design builds above).

## Exit
Design doc at docs/design/2026-07-XX-worktree-overlay.md; forks presented with
recommendations in plain language; operator ruling recorded in the doc; PKT-34 unblocked;
INDEX row + Log.
