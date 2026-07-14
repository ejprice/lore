# 21 — Single-node resilience drills (MASTER-PLAN §8.6) — SPLIT 2026-07-14 (formerly PKT-10a)
size ~0.15 wu · wave M (before the v1.0 ship) · depends: none (deployed image only)
law: DESIGN-LAW §12 · DEPLOY: receipts run against real containers (no new code expected)
(The §8.7 split-topology e2e half moved to **packet 38**, wave S, with the client/server
work — the single-node drills gate the v1.0 local ship and could not wait.)

## Mission
Prove the SINGLE-NODE failure story with receipts before v1.0 ships. This is a
verification packet — code changes only where a drill fails.

## Scope IN
- **§8.6 drills** on the unified store: kill -9 mid-sweep; corrupt-dir resilient open
  (move aside, recreate, eager rebuild — memories-unrecovered honesty per packet 18's
  post-ledger posture); wiped-store self-heal; fingerprint-change rebuild (the FP-xx
  analogues). Each drill = a written receipt: command, observed recovery, honest-status
  renders during degradation.
- **Watcher skip-path posture** (operator pool item 11): the live-drain skip path's
  store write means a store blip kills the watcher worker — drill it, then present the
  operator ack-or-isolate fork with the measured blast radius.

## Scope OUT / warnings
- Split-topology e2e (packet 38, wave S).
- Do not point any drill at production :18500 or the shared Qdrant pod (DESIGN-LAW §7).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
A throwaway drill store provisioned (per-drill namespace or a dedicated container —
never spike-surreal's test data mid-suite); packet 18's landed state checked (the
corrupt-dir drill's expected behavior changed with the ledger retirement).

## Exit
Receipts document committed (docs/design/ or receipts/); any defect found → red-first
fix + finding; single-node deploy still live; INDEX row + Log.
