# 19 — lore-deploy skill rework (finding #13 + the scaffold defect) (formerly PKT-11)
size ~0.30 wu →split at kickoff · wave M (re-waved 2026-07-14) · depends: packets 14/15 (dispositions shape the scaffold)
law: DESIGN-LAW §7 (Qdrant-pod law), §12 · skill tests idiom: `cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests`

## Mission
Bring the lore-deploy skill (in-repo at skills/lore-deploy/, symlinked from
~/.claude/skills) into the v2/role era. NOTE: **finding #13** here (status verb) is not
**ledger #13** (packets 14/15's table).

## Scope IN
- **Finding #13**: the `status` verb reads the LEGACY SQLite manifest (printed 169 vs
  true 196) — read SurrealDB's file table (the P8a migration moved it).
- **Scaffold fix, complete**: `_scaffold_lore_yaml` still emits a `qdrant:` block and
  no `surreal:` block (lore_deploy.py:452-454) — with `extra="forbid"` a fresh scaffold
  FAILS TO PARSE, so `lore-deploy setup` onboarding is broken today (lead-confirmed
  2026-07-05). Must template `surreal:` + the required `anthropic:` block + packets 14/15's
  new keys. Verify what the post-P8d fix b8e41a8 already covers — build ON it.
- **Single-node (`all`-mode) verbs only — TRIMMED 2026-07-14** (client/server pushed to
  wave S): keep the verb signatures role-extensible (a role arg defaulting to `all`) but
  build/wire NOTHING beyond `all`; packet 36 regains the per-role wiring when wave S runs.
- **git_sync pattern** documented + wired (sidecar pulls → post-sync reconcile command
  row as the deterministic alternative to inotify storms).
- **Drop Qdrant verbs** from the skill (the shared POD stays until post-soak —
  DESIGN-LAW §7; only the skill's verbs retire).

## Scope OUT
- The `migrate` verb machinery (packet 20 builds it; this packet leaves the seam).

## Entry check
`lore_findings` → #13 open; run the skill's test suite green before touching it;
confirm b8e41a8's actual coverage against the scaffold defect (don't trust the note).

## Exit
Skill tests + full gates + cold audit; a FRESH `lore-deploy setup` on a throwaway
project produces a parsing, booting lore.yaml (the onboarding smoke that is broken
today); finding #13 resolved; INDEX row + Log.
