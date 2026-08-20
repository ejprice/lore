# REPORT-lead-48 — Packet 48: principals substrate (build_store extraction + principal table)

lead-base v6 read
brief project v7 read

## SUMMARY BLOCK (close-out)
- **State: DONE.** Both waves shipped GREEN. DEPLOY: no (packet doc — 49/39 serve it;
  commit-only, precedent 07/46/47).
- **Verdicts acted on:** 4 (adversary×2, cold-audit×2), all SAME (no STALE acted on).
  `adversary-48a` r2 SUFFICIENT → 48-A build. `coldaudit-48a` GO (graded `5bd1b36`+build,
  HEAD-then `84bca93` = 1 ahead = the orthogonal #389 fix) → 48-A commit `1bbb0fb`.
  `adversary-48b` r3 SUFFICIENT → 48-B build. `coldaudit-48b` GO (graded `90426f1`+build) →
  48-B commit `2c33007`.
- **Directives:** ~9 corrections via native SendMessage to AT-REST agents (sanctioned
  at-rest / design-sidecar exception) / 0 wake-only / 0 prose-duplicated. Proof-of-receipt =
  each agent's revised report artifact (r2/r3). ⚠ Process note: content rode native (to
  at-rest recipients), not the ledger — acceptable per the at-rest exception, but the
  ledger is the standing preference.
- **Rulings:** 8 in committed artifacts (design doc `131ba56` + lore memory
  `2d33b1ad`/`b851596d`/`d62d1d4b`/`c78d5cdc`) / 0 body-only. (kickoff scope+fork3, F1=model B,
  F1b=A, #1 call-time, #2 unconditional, #3 keep-ASSERT, plus the Fable design rulings.)
- **Agents:** 10 spawned / 10 ledger-retired / 0 left-running (all TaskStopped; ledger
  status=retired). (Planning-phase pre-kickoff agents — 3 Explore + 1 framework-compare —
  completed/stopped separately, not in the wave roster.)
- **Uncommitted at stop:** 0 (after the close-out archival commit).

## What shipped
- **48-A `1bbb0fb`** — `build_store(config) -> SurrealStore` (un-readied) in
  `store/surreal.py`; the 3-way store-construction copy unified, all sites routed. NARROW
  (broad ~10-resolver refactor deferred, F5). Proven by mutation (change the factory → all
  3 callers redden = routing-is-not-sharing). Byte-equivalent; readiness + register_entity_
  tables + R4 preserved.
- **48-B `2c33007`** — the `principal` table (Variant A slice, folded into `generate_ddl`)
  + `PrincipalStore` CRUD in new `principals.py`. Model B: `subject option<string>` UNIQUE
  (email-pre-create coexists as NONE, real collisions rejected incl. on the fill UPDATE),
  email required+unique, principal-specific authz domains derived at CALL TIME
  (mutation-provable). Routes `_query` through the shared `run_query` seam (observed in the
  #120 seam gate). `set_subject` unconditional (F1b=A).
- Design `131ba56` · probe instrument `c453c3b` · #389 allowlist fix `84bca93`.

## Pipeline (both waves, per standing law)
design (Fable) → contract (opus48-worker) → contract-adversary (opus48-worker @ 4.8 — stock
agent is Opus5) → build → cold audit (REFUTE). Contract committed RED only after
adversary-clear. 48-A: adversary 1 INSUFFICIENT (C-DEF + monoculture) → r2 SUFFICIENT.
48-B: adversary 1 INSUFFICIENT (C-DEF regex + QUANTIFIER authz-domain leak + param) → r3
SUFFICIENT. Both within the ≤2 failed-contract budget; no operator escalation on gates.

## Operator decisions (surfaced via AskUserQuestion)
- Kickoff: scope = schema+store+CRUD; fork 3 = per-slug now.
- **F1 = MODEL B** (admin pre-creates by email; 39 fills subject on first login) — made
  UNIQUE-over-nullable load-bearing → lead-verified live probe (multiple NONE allowed, same
  non-NONE rejected on CREATE+UPDATE, filtered-unique unsupported).
- **F1b = A** (set_subject unconditional; 39 orchestrates fill-once).

## Findings
- **#388** (open) — store reference omits UNIQUE-over-nullable behavior; add during a store
  touch (probe `scripts/probe_unique_nullable_48.py` is the instrument).
- **#389** (RESOLVED) — probe allowlisted in S6 mint-site invariant.
- **#390** (open) — `mutation_proof.py` stale-`__pycache__` false-FAIL (safe direction);
  harness friction, surfaced by coldaudit-48b.
- **#391** (open) — 2 cosmetic served-prose docstring nits (R3/R5), sweep in packet 49.

## Baseline honesty
Full `pytest -n auto` remains ~446 RED = the packet-39 committed contract (#333
RED_ADJUDICATED, `scripts/pending_contracts.yaml`) — NOT regressions, unchanged by this
packet. Packet 48 ran SCOPED suites (all green) + 869-test regression via the cold audit;
added no new RED. No full-suite run (DEPLOY: no).

## Receipts (archived → docs/plans/v2/receipts/2026-08-20-packet48/)
Contract/adversary/build/cold-audit reports for both waves + the probe report + the Fable
design report. Design doc `docs/design/2026-08-20-packet48-principals-substrate.md`.
