# 11b — Embedding-schema reconciliation · BUILD + DEPLOY (#171)
size ~0.25 wu →split at kickoff if the 11a contract measures over 0.30 · wave L · depends: 11a ruled
law: the ruled design IS the spec (docs/design/2026-07-22-embedding-schema-reconciliation.md)
· repo store law FIRST READ (incl. §0) · DESIGN-LAW §11, §12 · DEPLOY: yes (BOTH containers)

## Mission
Build the 11a contract: the reconciler lands, `rebuild_all` RETIRES, and the #167 class
(needless full re-embeds; terminally-dead rebuilds; unverifiable stored embeddings)
becomes unreachable.

## Scope IN (per the ruled design — cite, never re-derive)
- The structured `embedding_schema` blob in SurrealDB + derived fingerprint (Q1).
- **`ChunkerRegistry.resolve` EXTRACTED as the one shared routing authority** (Q4),
  mutation-proven — packets 12/13's detection work builds on THIS seam afterward.
- The boot diff → change classes → per-file executor extending the existing sweep walk;
  per-file checkpoints = free resume; transient-retry at the ONE shared embed wrapper;
  terminal state is an owned "degraded", never an orphaned "failed" (#169's shape dies).
- **#170's `embedding_text_sha512` stamped per chunk at write** — the content-addressed
  reuse key (Q2/Q6) and packet 24's at-scale verification instrument.
- The migration bridge: on the exact #167 hand-stamp meta values, the zero-embed branch
  (pinned fixture from 11a).
- **The HARD-CUTOVER rename** `schema_rebuild_status` → `schema_reconcile_status` +
  `rebuild_all` retirement: retired-name sweep with BARE greps to ZERO (prose included —
  repo sweep law), no alias, structural pins updated in step.
- `Chunker.version` base-class addition in lorescribe (cross-package scope, ruled §13).

## Scope OUT
- Detection/identify dispatch (packets 12/13 — they ride the extracted resolve).
- Any cloud cost gate (operator RULED no — do not build one).

## Entry check
11a contract RED for the right reasons + adversary-passed; spike-surreal up (3.2.1);
`lore_index()` current state captured as the before-receipt. The designer sidecar
remains the question channel.

## Exit
Full gates + cold audit; deploy BOTH; smoke on the live instance: add a throwaway
chunker route for an absent extension → ZERO re-embeds; inject a transient embed
failure mid-reconcile → retry + resume, state never orphaned; retired-name grep = 0;
#168/#169 resolved-as-superseded + #170 resolved-as-adopted + #171 resolved with
receipts; INDEX row + Log.
