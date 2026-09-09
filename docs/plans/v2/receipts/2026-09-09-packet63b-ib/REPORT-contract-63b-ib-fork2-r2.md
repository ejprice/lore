# REPORT — contract-63b-ib-fork2-r2

> ⚠ SUPERSEDED (archived 2026-09-09, never completed): r2 was TaskStopped early when the Fable design
> sidecar recovered from a session-limit and produced the authoritative B1 ruling — more precise than
> r2's spawn brief (3-class M/I/P policy + a shared `assert_domain_rejection` helper + a disjointness
> pin + corpse edits in the CONTRACT, not the build). The B1 revision was done by the respawned
> `contract-63b-ib-fork2-r3` on Fable's ruling (shipped `ae180c9`). Kept for the audit trail only; its
> content is NOT the shipped revision. See `REPORT-contract-63b-ib-fork2-r3.md` + the B1 ruling.

brief-base v14 read

**STATE: STARTED** (skeleton; growing per milestone)

## Mission
Close blocker **B1** from `REPORT-adversary-63b-ib-fork2.md`: the FORK-2 contract's
34/0 satisfiability was scoped to the 2 FORK-2 files and MISSED that §2.4-1's retype
(SurrealStoreError → TxnDomainRejectionError) reds ~15 pre-existing
`assert type(x) is SurrealStoreError` corpses across ~9 sibling files (GREEN at HEAD).
Design is SETTLED (operator 2026-09-09) — do NOT re-open. Deliver:
1. EXHAUSTIVE corpse enumeration — DERIVED from a whole-suite reference-build run.
2. REMOVED-BEHAVIOUR INVENTORY = the builder's roadmap (item-by-item adjudication).
3. REPO-LOCAL INVARIANT PIN (RED@HEAD, mutation-proven).
4. WHOLE-SUITE SATISFIABILITY RECEIPT (apply corpse edits + pin → 0-failed).
5. PRODUCTION SWEEP (adversary R4).

## SUMMARY BLOCK
- receipt: brief-base v14 read
- state: STARTED
- deviations: (none yet)
- Packages considered: (pending)
- Reuse ledger: (pending)
- Graded: (pending)
- decisions-needed: (pending)
- pointers: (pending)

## Progress log
- STARTED: idle-gate contract + report skeleton written; brief-base v14 read; HEAD 98cf52c; lore tools loaded.
