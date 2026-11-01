# RULING: #572, the host `<slug>.db` is a deploy-side ledger (operator, 2026-10-31)

Source: `REPORT-impl-568-slug.md` §F-A. Measured at `0c7477c`: since P5 no loremaster code writes the host SQLite
`<slug>.db`. The cold index writes `SurrealManifest` (the store); `server.py` uses `manifest_path` only to anchor
`<slug>.memory.db`; host `lore.db` was last written 2026-07-03.

Operator ruling (AskUserQuestion: "Deploy-side ledger now (Recommended)"):
- **The host `<slug>.db` is lore-deploy's LEDGER**, written only by `setup`: the owning `project_path` plus a
  provisioned marker.
  - `setup`'s "already provisioned" decision reads that marker.
  - Index state is never inferred from the ledger.
- **`status` never shows file or chunk counts from the ledger.** It states that the index counts live in the store
  and names `lore_index()` as where to read them. The provisioned marker and the owner path are shown as what
  they are. No status line may claim an index fact the deploy script did not measure (trust doctrine: a served
  count describes the whole set its label claims).
- Moving ownership, the provisioned check and the counts into `SurrealManifest` meta stays OPEN as #572 (a
  store-touching change; full `/tdd`; reads `docs/reference/surrealdb-31-capabilities.md` first).
