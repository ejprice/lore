brief-base v6 read

# REPORT-probe-bootstrap-11i-b — pointer

**The report is `REPORT-probe-bootstrap-11i.md`, at this same worktree root.** This file exists
only so the address matching my exact agent name (`probe-bootstrap-11i-b`) resolves; it duplicates
no content, because a second copy of a 560-line artifact is a copy that goes stale.

**Why the names differ.** My spawn brief named the deliverable
`REPORT-probe-bootstrap-11i.md` — "at the WORKTREE ROOT — exact name" — while `brief-base` §1 and
the idle-gate hook expect `REPORT-<exact-agent-name>.md`. Spawn brief takes precedence over
`brief-base` on conflict, and by the time the hook fired the lead had already committed and cited
the brief-named path (`803c191`, then `f66b980`). Renaming it would have broken a live citation, so
the brief-named file stays canonical and this pointer covers the other address.

**Verdict, in one line:** S1 is **NOT DEGENERATE** — the floor is a tail order statistic (measured:
#2 of 56) and the bootstrap is genuinely inconsistent there, but the symptom is ERRATIC, not
FROZEN, so packet 11-i does **not** fork to design repair. The measurement that matters most is
§6.2 of the real report: D3's disjoint-CI test at N=56 detects a true floor move of +0.010 at
**1.5%** — exactly its own false-positive rate.

| receipt | path |
|---|---|
| full report | `REPORT-probe-bootstrap-11i.md` |
| instrument (re-runnable) | `docs/plans/v2/receipts/2026-07-24-packet11i/probe_bootstrap_degeneracy.py` |
| raw output (one complete run, exit 0, 674.1 s) | `docs/plans/v2/receipts/2026-07-24-packet11i/probe-bootstrap-output.txt` |
| commit | `f66b980` (supersedes the truncated mid-run receipt at `803c191`) |

No ledger row was named in my brief, so per `brief-base` §5 I touched no board.
