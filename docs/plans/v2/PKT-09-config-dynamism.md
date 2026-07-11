# PKT-09 — Config dynamism: the ruled disposition table (ledger #13)
size ~0.35 wu · wave D (parallel-safe) · depends: none
law: DESIGN-LAW §11 (hazard guards — binding as written) · spec: docs/design/2026-07-05-p13-config-dynamism-disposition.md (operator-ACCEPTED WHOLESALE 2026-07-05) · DEPLOY: yes

## Mission
Implement the operator-accepted disposition table. NOTE the numbering trap: this is
**ledger #13** (config-dynamism); **finding #13** (lore-deploy status manifest) is
PKT-11's. Static config rots — this packet makes lore.yaml self-healing where ruled.

## Scope IN (the ruled table, spec :27-113)
- **5 derive-at-boot items:** (1) `exclude_dirs` venv/binary/VCS additive auto-detection
  — union with operator config, logged, dir-shape signal required (DESIGN-LAW §11);
  (2) `chunkers` fingerprint-vs-selection reconciliation (coordinate with PKT-05's
  detection layer — if detection landed first, the derive target is the identify
  dispatch, not the old map); (3) `embedding.tokenizer` derive-from-model or drop;
  (4) `watcher.observer` derive-from-platform or drop; (5) `embedding.truncate`
  derive-from-backend or informational. Honorable mention: `server.port` free/collision
  boot check.
- **Validate-against-reality boot assertions** (spec :27-85): schema_version,
  project.root, embedding.model (probe /info model_id — the wrong-model/right-dim
  silent hazard), max_input_tokens/max_batch_texts, prompt_names, roots[].path,
  roots[].source, anthropic.yardstick_model.
- **9-dead-field cleanup** (wire-or-drop, receipts per field in the table).
- **Finding #72**: `scratchpad/` (and session artifacts generally) excluded from the
  index — lands with the exclude_dirs work; reconcile the polluted corpus after.
- **Finding #12**: annotate (never rewrite) the stamped disposition-doc row that went
  stale post-bcba046 — skip if already resolved at boot.

## Scope OUT
- The scaffold defect (`_scaffold_lore_yaml` qdrant:/surreal:/anthropic:) — PKT-11 owns
  the scaffold; if this packet's validation work makes fresh scaffolds fail EARLIER,
  surface the interaction, don't fix it here.

## Entry check
`lore_findings` → #72, #12 states; read the spec table in full (it is short and IS the
work list); confirm which items PKT-05 already consumed (chunkers row).

## Exit
Full gates + cold audit; deploy BOTH; smoke: boot log shows derived excludes + validation
verdicts; DI's config passes the new assertions (it is the motivating casualty);
findings resolved; INDEX row + Log.
