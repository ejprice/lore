# 14 — Config: derive-at-boot + excludes (ledger #13, half a) (formerly PKT-09)
size ~0.20 wu · wave L (parallel-safe) · depends: none · sibling: packet 15 (validation half)
law: DESIGN-LAW §11 (hazard guards — binding as written) · spec: docs/design/2026-07-05-p13-config-dynamism-disposition.md (operator-ACCEPTED WHOLESALE 2026-07-05) · DEPLOY: yes

## Mission
The derive/excludes half of the operator-accepted config-dynamism disposition table
(packet 15 carries the validation half). NOTE the numbering trap: this implements
**ledger #13** (config-dynamism); **finding #13** (lore-deploy status manifest) is
packet 19's. Static config rots — this packet makes lore.yaml self-healing where ruled.

## Scope IN (the ruled table, spec :27-113 — this half)
- **5 derive-at-boot items:** (1) `exclude_dirs` venv/binary/VCS additive auto-detection
  — union with operator config, logged, dir-shape signal required (DESIGN-LAW §11) —
  folds **#26** (name-based hand-curation can't keep up); record the **#28** decision
  (include-glob piercing an exclude prune: build or wontfix, with the ruling noted);
  (2) `chunkers` fingerprint-vs-selection reconciliation (coordinate with packet 13's
  detection layer — if detection landed first, the derive target is the identify
  dispatch, not the old map); (3) `embedding.tokenizer` derive-from-model or drop;
  (4) `watcher.observer` derive-from-platform or drop; (5) `embedding.truncate`
  derive-from-backend or informational.
- **Finding #72**: `scratchpad/` (and session artifacts generally) excluded from the
  index — lands with the exclude_dirs work; reconcile the polluted corpus after.

## Scope OUT
- Boot validation assertions, dead-field cleanup, #12 (packet 15).
- The scaffold defect (`_scaffold_lore_yaml` qdrant:/surreal:/anthropic:) — packet 19
  owns the scaffold.

## Entry check
`lore_findings` → #26, #28, #72 states; read the spec table in full (it is short and IS
the work list); confirm which items packet 13 already consumed (chunkers row).

## Exit
Full gates + cold audit; deploy BOTH; smoke: boot log shows derived excludes on this
repo AND the polluted corpus reconciled (scratchpad/ gone from search); findings
resolved; INDEX row + Log.
