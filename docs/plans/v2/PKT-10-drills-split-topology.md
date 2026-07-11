# PKT-10 — Resilience drills + split-topology end-to-end (MASTER-PLAN §8.6 + §8.7)
size ~0.30 wu · wave D, LAST · depends: PKT-07, PKT-08
law: DESIGN-LAW §12 · DEPLOY: receipts run against real containers (no new code expected)

## Mission
Prove the platform's failure story with receipts. This is a verification packet — code
changes only where a drill fails.

## Scope IN
- **§8.6 drills** on the unified store: kill -9 mid-sweep; corrupt-dir resilient open
  (move aside, recreate, eager rebuild + ledger restore); wiped-store self-heal;
  fingerprint-change rebuild (the FP-xx analogues). Each drill = a written receipt:
  command, observed recovery, honest-status renders during degradation.
- **§8.7 split e2e**: SurrealDB server + scout container watching a checkout + mcp
  container. Git pull touching many files → watcher coalescing/reconcile absorbs;
  snapshot stamped with git_ref; lore_diff shows the pull function-level; lore_read
  spans hash-match disk; reconcile command row round-trips; kill/restart each component
  independently (scout reconnects; mcp serves degraded-honest while the store is down).
- **Watcher skip-path posture** (operator pool item 11): the live-drain skip path's
  store write means a store blip kills the watcher worker — drill it, then present the
  operator ack-or-isolate fork with the measured blast radius.

## Scope OUT / warnings
- Hosted security: split topology beyond trusted environments waits for PKT-21
  (external-review gap 5) — the e2e here runs on the trusted LAN only.
- Do not point any drill at production :18500 or the shared Qdrant pod (DESIGN-LAW §7).

## Entry check
PKT-07 roles + PKT-08 image live; a throwaway drill store provisioned (per-drill
namespace or a dedicated container — never spike-surreal's test data mid-suite).

## Exit
Receipts document committed (docs/design/ or receipts/); any defect found → red-first
fix + finding; single-node deploy still live; INDEX row + Log. **Wave D closes here.**
