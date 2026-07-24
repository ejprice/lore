# 11 — Per-corpus floor calibration · BUILD — **SUPERSEDED, SPLIT INTO 11-i / 11-ii**
**Status: superseded 2026-07-24 (operator-approved split). This file is a POINTER, not a
plan. Do not execute it.**

This packet was split at kickoff under its own `≥0.30 → split` clause. The honest
re-estimate crossed the line once the operator's 2026-07-24 ruling made the in-container
remediation mechanics explicit (engine-task lifecycle, single-flight / coalescing /
discard-requeue, churn counting at the shared embed seam, head-mint concurrency).
Rationale: `docs/design/2026-07-24-floor-calibration.md` §B8.

**The two live packets:**
- **`11-i-floor-calibration-dark-machinery.md`** — engine + store + portable in-container
  runner + R2 lab validation. Serving untouched, no deploy, independently auditable.
- **`11-ii-floor-calibration-cutover.md`** — chokepoint wiring + serving swap + retirement
  sweep. Deploys both containers; resolves #83 / #87 / #161 / #179.

**Why this file still exists rather than being deleted:** citations to it are already in the
tree and in commit history — it is the packet named by `10-floor-calibration-design.md`'s
Exit, and by commit `1ff686d`, which made it #161's owner. Repo law is that an address
should resolve, and that a superseded document is kept **with a header saying so** rather
than silently preserved as current or silently removed.

⚠ Two claims in the pre-split text were overtaken by events. Recorded here so a reader of
the historical section below is not misled:
1. **CalibrationEngine wholesale reuse was REJECTED at source** by the packet 10 design
   (§B6): its loop compares token-weighted totals against a shipped baseline, and a cosine
   survey shares no mechanism with it. What IS reused: the findings-seam Protocol, the
   `from_engine_status` construction pattern, and the closed-distinct-state discipline.
2. **The "fold #4's fix if still open" entry step is already satisfied** — #4 was RESOLVED
   in P8d W3 (`STATE_INTEGRITY_FAILED` shipped).

---

# (pre-split text — historical record only)

size ~0.25 wu · wave L · depends: packet 10 ruled · DEPLOY: yes (both containers)
law: DESIGN-LAW §3, §5 (store idioms), §6, §12

## Mission
Build the packet 10 design: per-instance floor measurement persisted in that instance's
store (CalibrationEngine pattern — the token-calibration engine from P8c is the in-repo
precedent), served/surfaced via lore_index, with automatic drift-triggered re-measurement
+ adoption. Resolve findings #83, #87 and #161.

**#161 is the LIVE INSTANCE of the #83 gap, and it closes with this work.** A wave's report
archives grew the indexed corpus past the 10% tolerance; lore flagged its own floor
`state: "stale"` and — because disarm-and-wait is all that exists — nothing acted on the
self-declaration. The automatic re-measure + adopt IS the fix. ⚠ **Do NOT pin #161's
recorded file counts as an acceptance number.** The corpus is a moving target as lore is
built, so a count-match proves nothing: the exit condition is that the MECHANISM re-measures
and adopts on drift, whatever the count is that day.

Original Scope IN / Scope OUT / Entry check / Exit are carried — corrected and expanded — by
11-i and 11-ii. Read those.
