# 15 — Config: boot validation + dead-field cleanup · formerly PKT-09 half b
size ~0.20 wu · wave L (parallel-safe) · depends: none
law: DESIGN-LAW §11 (hazard guards — binding as written) · spec: docs/design/2026-07-05-p13-config-dynamism-disposition.md (operator-ACCEPTED WHOLESALE 2026-07-05) · DEPLOY: yes

## Mission
The validation half of the ruled config-dynamism disposition table (the derive/excludes
half is packet 14). NOTE the numbering trap: this implements **ledger #13**
(config-dynamism); **finding #13** (lore-deploy status manifest) is packet 19's.

## Scope IN (the ruled table, spec :27-113 — this half)
- **Validate-against-reality boot assertions** (spec :27-85): schema_version,
  project.root, embedding.model (probe /info model_id — the wrong-model/right-dim
  silent hazard), max_input_tokens/max_batch_texts, prompt_names, roots[].path,
  roots[].source, anthropic.yardstick_model.
- **9-dead-field cleanup** (wire-or-drop, receipts per field in the table).
- **Finding #12**: annotate (never rewrite) the stamped disposition-doc row that went
  stale post-bcba046 — skip if already resolved at boot.
- Honorable mention: `server.port` free/collision boot check.

## Scope OUT
- The scaffold defect (`_scaffold_lore_yaml`) — packet 19 owns the scaffold; if this
  packet's validation makes fresh scaffolds fail EARLIER, surface the interaction,
  don't fix it here.

## Entry check
`lore_findings` → #12 state; read the spec table in full (it is short and IS the work
list); confirm which rows packet 13's detection layer and packet 14 already consumed.

## Exit
Full gates + cold audit; deploy BOTH; smoke: boot log shows validation verdicts; DI's
config passes the new assertions (it is the motivating casualty); #12 resolved; INDEX
row + Log.
