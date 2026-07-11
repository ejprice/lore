# PKT-11 — lore-deploy skill rework (finding #13 + the scaffold defect)
size ~0.30 wu · wave E · depends: PKT-09 (dispositions shape the scaffold)
law: DESIGN-LAW §7 (Qdrant-pod law), §12 · skill tests idiom: `cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests`

## Mission
Bring the lore-deploy skill (in-repo at skills/lore-deploy/, symlinked from
~/.claude/skills) into the v2/role era. NOTE: **finding #13** here (status verb) is not
**ledger #13** (PKT-09's table).

## Scope IN
- **Finding #13**: the `status` verb reads the LEGACY SQLite manifest (printed 169 vs
  true 196) — read SurrealDB's file table (the P8a migration moved it).
- **Scaffold fix, complete**: `_scaffold_lore_yaml` still emits a `qdrant:` block and
  no `surreal:` block (lore_deploy.py:452-454) — with `extra="forbid"` a fresh scaffold
  FAILS TO PARSE, so `lore-deploy setup` onboarding is broken today (lead-confirmed
  2026-07-05). Must template `surreal:` + the required `anthropic:` block + PKT-09's
  new keys. Verify what the post-P8d fix b8e41a8 already covers — build ON it.
- **Role-aware verbs**: start/stop/status per role (all|mcp|scout), per PKT-07 wiring.
- **git_sync pattern** documented + wired (sidecar pulls → post-sync reconcile command
  row as the deterministic alternative to inotify storms).
- **Drop Qdrant verbs** from the skill (the shared POD stays until post-soak —
  DESIGN-LAW §7; only the skill's verbs retire).

## Scope OUT
- The `migrate` verb machinery (PKT-12 builds it; this packet leaves the seam).

## Entry check
`lore_findings` → #13 open; run the skill's test suite green before touching it;
confirm b8e41a8's actual coverage against the scaffold defect (don't trust the note).

## Exit
Skill tests + full gates + cold audit; a FRESH `lore-deploy setup` on a throwaway
project produces a parsing, booting lore.yaml (the onboarding smoke that is broken
today); finding #13 resolved; INDEX row + Log.
