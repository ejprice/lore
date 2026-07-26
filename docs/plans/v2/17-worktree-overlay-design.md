# 17 — Worktree overlay · DESIGN (#125, operator-ruled first-class 2026-07-14) (formerly PKT-33)
size ~0.15 wu · wave L · depends: none · builds: packet 23
lead: **Opus + Fable design sidecar** (operator roster 2026-07-14 — INDEX; sidecar mechanics in repo CLAUDE.md → Orchestration)
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
  tier-coexistence machinery exists — packet 27 pins it).
- **Serving = overlay-shadows-base per file**: overlay hits replace base hits for changed
  paths; deleted files masked; everything else serves from base.
- **Auto-reap**: worktree gone → overlay dropped.
- **V1 tool scope: search / get_symbol / read / diff over changed files.** impact/dead_code
  stay base-served with an EXPLICIT caveat when the target is in the changed set — scoped
  delta-derivation (changed files + direct importers) is the designed-for v2, not v1.

## Branch/diff-awareness — ruled 2026-07-26 (the consult; receipts:
## docs/plans/v2/receipts/2026-07-26-branch-diff-consult/SYNTHESIS.md)
The operator asked whether branches belong in the design ("don't agents want to compare
their work vs the branch?"). Three independent model positions (Sonnet 5 · Opus 5 · Fable);
the operator RULED the v1-scope fork; the remaining bullets are the consult's UNANIMOUS
positions, presented alongside the ruling and adopted here as constraints-to-cite (reversing
one is an operator question, not a design call).
- **RULED: v1 serves GRAPH-OVER-THE-DELTA.** The changed-symbol inventory rides the overlay
  REGISTRATION render; search is scopable to the changed set (a filter over the overlay
  tier); batched BASE-SERVED `lore_impact`/covering-tests fan out over the changed set
  behind the EXPLICIT caveat above — and the caveat carries a NUMBER ("N files in your
  changed set are not graph-analysed"), pinned by a test that fails on a numberless caveat.
  This batches the base-served-with-caveat clause; it is NOT the v2 delta-derivation,
  which stays v2.
- **No textual-diff re-serve, ever.** git IS the diff engine (the overlay already shells
  `git diff --name-only` for its input); all three consumers said they would route around
  a re-serve — a DESIGN-LAW §1 trust debit for zero gain.
- **No git-ref mode on `lore_diff`.** Two identity spaces (snapshot ids vs refs) under one
  verb is the confident-wrong §1 forbids, and the hazard is PRIMED — the snapshot listing
  already renders git_branch@git_ref (#232, filed from this consult; the design doc
  dispositions #232's render-teaching question).
- **Ref-vs-ref for refs checked out nowhere: NEVER in this design.** Re-open trigger
  (deferral law): a wave needing STRUCTURAL comparison of two sibling worktrees' deltas,
  or Odoo onboarding demanding it.
- **Trust riders on every delta render, in the same breath (rider law):** all THREE
  identities — worktree path, branch + HEAD sha, AND merge-base sha (two of three lies by
  omission after a rebase — this is open question 4's consumer face); committed-vs-
  uncommitted PER FILE; enumeration age rendered (house STALE-notice convention); REFUSE
  loudly when git/merge-base fails or the root is not a checkout (#131's class — an empty
  changed set and a failed enumeration must be indistinguishable to no one); hostile
  fixtures on interpolated branch/path (already a packet 23 invariant).

## Open design questions (the doc answers each with receipts; operator rules the forks)
1. Registration surface: lore-deploy verb (worktree slug) vs `lore_index` alternate-root
   vs a session-scoped view registration on the existing surface (#125 filed all three as
   candidates (a)/(b)/(c) — candidate (c)'s minimum, the watched-path/branch render, ships
   in packet 01 regardless).
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
affordance candidates). packet 01's watched-path/branch line already deployed (cite it as the
floor this design builds above).

## Exit
Design doc at docs/design/2026-07-XX-worktree-overlay.md; forks presented with
recommendations in plain language; operator ruling recorded in the doc; packet 23 unblocked;
INDEX row + Log.
