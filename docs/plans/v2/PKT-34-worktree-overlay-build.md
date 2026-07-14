# PKT-34 — Worktree overlay · BUILD (#125)
size ~0.25 wu · wave O, runs ∥ PKT-27 · depends: PKT-33 ruled · **MUST land before PKT-35
(Odoo onboarding build) completes — Odoo work lives in worktrees**
law: DESIGN-LAW §1, §12 · TDD skill full cycle (new behavior) · the contract-adversary
grades the contract before any builder (repo law) · DEPLOY: yes

## Mission
Build the delta-only worktree overlay exactly as PKT-33's ruling shaped it. The packet is
intentionally thin here: PKT-33's ruled design doc IS the spec — this file carries only
the invariants that survive any ruling.

## Invariants (binding regardless of the ruled shape)
- **Delta-only** (full-tree indexing banned); merge-base enumeration; ephemeral overlay
  tier; per-file shadowing; auto-reap. See PKT-33 for the constraint text — cite, never
  re-transcribe.
- V1 tool scope: search / get_symbol / read / diff over changed files; impact/dead_code
  base-served with the explicit caveat. The caveat render gets hostile fixtures
  (repo law: newlines + row-shaped forgery + backtick runs) — it interpolates a
  worktree-supplied branch/path.
- The overlay NEVER pollutes the base corpus: base-tier search results are byte-identical
  with and without an overlay registered (pinned).
- Fixture discrimination (repo law): at least one pin uses a worktree whose changed set
  includes a DELETED file and a RENAMED file — the two cases a naive overlay serves
  wrong silently.

## Scope OUT
- Scoped graph delta-derivation (the designed-for v2) — a follow-up packet if wave-O
  experience demands it, with its own ruling.

## Entry check
PKT-33's ruling recorded; a real throwaway worktree of THIS repo as the smoke target
(create → edit uncommitted → query → reap).

## Exit
Full gates + cold audit; deploy BOTH; smoke on a real worktree: an uncommitted symbol is
searchable in the worktree view, absent from the base view, base counts unchanged, reap
leaves no residue; #125 resolved with the receipt; INDEX row + Log.
