# 11a — Embedding-schema reconciliation · CONTRACT (#171 ⊃ #168/#169, adopts #170)
size ~0.20 wu · wave L (positional suffix — no relation to packet 11's calibration; runs before 12/13, which ride its extracted resolve seam) · depends: none
law: **the design is FULLY RULED — Q1–Q6 (§12) + §13 residuals all operator-decided.
This is a spec to IMPLEMENT, not a property to invent**: docs/design/2026-07-22-embedding-schema-reconciliation.md
· DESIGN-LAW §11, §15 (instrument packets route through the contract-adversary) · repo
store law FIRST READ (incl. §0 — engine 3.2.1) · TDD CONTRACT phase — pauses for review

## Mission
Contract the diff-driven embedding-schema reconciler that replaces
full-rebuild-on-any-fingerprint-change: structured `embedding_schema` blob (fingerprint
DERIVED from it) → boot diff into change classes (vector-identity / chunk-boundary /
chunker-map / unknown → REEMBED_ALL failsafe) → per-file executor that IS the existing
sweep walk extended (`rebuild_all` retires). Kills the class that produced #167 live:
an additive chunker route must cost ZERO re-embeds; a transient embed failure must cost
a retry, not the whole run.

## Binding rulings (cite the design §12/§13 — never re-derive)
Q1 fingerprint = derived fast-path over the blob · Q2 chunk-boundary → re-chunk +
re-embed ONLY hash-diffed chunks (content-addressed reuse keyed on #170's
`sha512(embedding_text)`) · Q3 chunker-CODE-change = pinned KNOWN BOUND + `Chunker.version`
+ `EMBEDDING_SCHEMA_VERSION` escape hatches (implementation-hashing REJECTED) · Q4 diff by
chunker KEY, affected files resolved via an EXTRACTED shared `ChunkerRegistry.resolve`
(does not exist today — extraction + mutation-proof required) · Q5 own packet (this one) ·
Q6 #170's per-chunk `embedding_text_sha512` is the ONLY chunk-diff key · §13: NO cloud
cost gate (operator overruled the sidecar — reconciles run unattended) · `Chunker.version`
is a lorescribe base-class addition (cross-package, flagged) · served rename
`schema_rebuild_status` → `schema_reconcile_status` is a HARD CUTOVER with a retired-name
sweep incl. prose, NO alias · one new additive store read accepted.

## Contract musts (the design's §11 fixture-discrimination list — verbatim source)
The `.xyz` zero-embed pin · the D1 pin (a chunker ADDED for already-walked files RUNS —
v1's "no-op" was WRONG; zero-chunk `indexed` rows at indexer.py:555-557 are the trap) ·
split/merge EXACT-COUNT pins · kill-mid-sweep resume pin · the #169 transient-injection
pin · the resolver mutation pin · ≥8-way concurrency · no value monoculture · the
migration-bridge fixture pinned on the EXACT #167 hand-stamp meta values (fingerprint
f6e2ee34 + status idle → the zero-embed branch; the hand-stamp becomes automatic).

## Entry check
Read the design end-to-end (it is the spec). `lore_findings` → #171 acknowledged,
#168/#169/#170 states (superseded/adopted — annotate at 11b's exit, not here).
**The `embed-schema-designer-4` Fable sidecar is AT REST for follow-ups** — questions go
to it via SendMessage (the sanctioned at-rest shape), never re-derived.

## Exit
Contract tests written (RED) + satisfiability receipt against the design's reference
semantics + contract-adversary pass (§15) + operator review pause; 11b unblocked;
INDEX row + Log.
