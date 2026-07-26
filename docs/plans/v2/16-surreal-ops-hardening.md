# 16 — SurrealDB deployment hardening (tuning-audit findings) (formerly PKT-31)
size ~0.15 wu · wave L (parallel-safe) · depends: none
law: repo CLAUDE.md deploy law (stores are systemd/quadlet-managed — edit the unit, never
hand-`podman run`); production store :18500 changes are announced, never silent · DEPLOY:
store units restarted (lore containers reconnect; #124 race unexposed thanks to bootstrap
pre-DEFINE)

## Mission
Close the 2026-07-13 surreal-tuning-audit findings: real memory-pressure and credential
risks on this box, plus the minimal observability the #124 watch needs.

## Scope IN (each item = its finding resolved with a receipt)
- **#110** — each store claims a 61.8 GiB RocksDB block cache (host-sized): set explicit
  cache/memory bounds in BOTH quadlets (`lore-surreal`, `spike-surreal`), sized
  deliberately, with the reasoning written down.
- **#116** — SURREAL_USER/SURREAL_PASS are INERT (engine warns every boot) and production's
  real root credential is unknown from config: establish/verify the credential story,
  record where it lives (env-indirected per house style), kill the boot warning.
- **#113** — spike-surreal leaks test databases (94 orphans; a failing 5s compaction task):
  reap the orphans + add a harness-side reaper (age-based sweep of `test_*` DBs) so the
  leak cannot regrow.
- **#109** — `transaction.conflicts` metric exists but nothing records it: minimal scrape
  (periodic log line or textfile) so the #124 watch and any future contention work has a
  baseline. Not a dashboard — a number that lands somewhere durable.
- **#114** — no slow-query logging / no txn timeouts: probe what 3.1.5 actually offers
  (verify docs against the engine — repo law), apply what exists, DOCUMENT what doesn't
  as the honest posture.
- **#117** — `?sync=never` on the TEST store only (measured-real speedup, deferred at the
  #102 wave). NEVER on :18500.
- **#175** (slotted 2026-07-26) — 3.2.1 store behaviour: `UPDATE <edge> … WHERE in IN $ids`
  silently matches ZERO rows while the identical SELECT matches; adding `out = $x` makes it
  work. Disposition per its filing: re-probe with the UNIQUE index dropped (test store only),
  then land the CONFIRMED mechanism in the store reference §2/§6.6. Shipped code is
  unaffected today — the hazard is any future message-scoped edge write.

## Scope OUT
- Engine upgrades; any schema/DDL change; any lore-code change. Production data migration.

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** — this
packet touches the store/schema/DDL or store-reading code; #107 was a 100% production
outage whose answer was ALREADY in that file. Cite it, never re-transcribe.
`lore_findings` → all seven (#109/#110/#113/#114/#116/#117/#175) unresolved. `systemctl
--user status lore-surreal spike-surreal` both active. Snapshot both quadlet files BEFORE editing (they are the recovery recipe — memory:
surreal-stores-systemd-managed).

## Exit
Both stores restarted clean under the new units + lore/DI containers reconnect and serve
(live smoke); no boot warnings; orphan count 0 with the reaper pinned by a test; findings
resolved with receipts; INDEX row + Log.
