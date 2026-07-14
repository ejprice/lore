# 38 — Split-topology end-to-end (split from PKT-10, 2026-07-14; MASTER-PLAN §8.7) (formerly PKT-10b)
size ~0.20 wu · wave S · depends: packet 36, packet 37
law: DESIGN-LAW §12 · DEPLOY: receipts run against real containers (no new code expected)

## Mission
The split-topology half of the original packet 38, deferred with the client/server wave.
(The single-node §8.6 drills + the watcher skip-path drill stayed in packet 21, wave M —
they gate the v1.0 ship.) This is a verification packet — code changes only where a
drill fails.

## Scope IN
- **§8.7 split e2e**: SurrealDB server + scout container watching a checkout + mcp
  container. Git pull touching many files → watcher coalescing/reconcile absorbs;
  snapshot stamped with git_ref; lore_diff shows the pull function-level; lore_read
  spans hash-match disk; reconcile command row round-trips; kill/restart each component
  independently (scout reconnects; mcp serves degraded-honest while the store is down).

## Scope OUT / warnings
- Hosted security: split topology beyond trusted environments waits for packet 39
  (external-review gap 5) — the e2e here runs on the trusted LAN only.
- Do not point any drill at production :18500 or the shared Qdrant pod (DESIGN-LAW §7).

## Entry check
packet 36 roles + packet 37 images live; a throwaway drill store provisioned (per-drill
namespace or a dedicated container — never spike-surreal's test data mid-suite).

## Exit
Receipts document committed (docs/design/ or receipts/); any defect found → red-first
fix + finding; single-node deploy still live; INDEX row + Log.
