lead-base v6 read

# REPORT — lead-07a-1 — packet 07a wave (store recovery + degradation)

## SUMMARY BLOCK

| field | value |
|---|---|
| `Verdicts acted on:` | adversary: `421f97f` -> HEAD-then `421f97f` -> SAME. cold audit: `6fdeabe` -> HEAD-then `6fdeabe` -> SAME. Both acted on immediately on receipt; no staleness window. |
| `Directives:` | 2 ledger (`#5034` FORK A ruling, `#5037` adversary F1/F2/F3 fixes) / 2 wake (native `SendMessage` paired with each) / 0 prose-duplicated |
| `Rulings:` | 3 in a committed artifact (`docs/plans/v2/receipts/2026-08-17-packet07a/RULING-fork-a.md`, committed `a1ac479`, corrected `edbd72a` + `51e69a2`: FORK A = A1, #128 wording = distinct contention line, #127 = add the frozen-caller-set tripwire) / 0 body-only |
| `Agents:` | 5 spawned (`fable-sidecar-07a`, `contract-07a-1`, `adversary-07a-1`, `builder-07a-1`, `coldaudit-07a-1`) / 5 ledger-retired / 0 left running |
| `Uncommitted at stop:` | 0 files |

## What happened

Kicked off per the standing wave-D kickoff template against packet 07a
(`docs/plans/v2/07a-store-recovery-degradation.md`), with an operator-added law folded
into every agent brief: verify engine-behavior claims against the store reference, THEN
the `surrealql-tests`/`surrealdb-docs` lore tiers, treating vendor prose as a lead only —
live probe as last resort. Operator also ruled: do not pause at the contract-review
checkpoint.

**The contract phase falsified the packet's own premise.** `contract-07a-1`'s live
20-consecutive full-server-bounce drill against spike-surreal 3.2.4 (the real
`SurrealStore` path) showed #164/#250's "wedges forever, only a container restart
heals it" does NOT reproduce at HEAD — self-heals on the next call, every time. This
forced a genuine scope fork (FORK A) that I routed to the operator rather than deciding
unilaterally: adjudicate-and-defer (A1) vs. build a new reconnect-and-retry mechanism
(A2). Operator ruled A1, plus two secondary decisions (#128's exact render wording,
#127's tripwire), all per the contract author's recommendation.

**The contract-adversary caught the ruling's own evidence chain was unsound** (F1: the
drill's regression-trigger prose claimed to catch a KeyError-branch regression it
empirically cannot, proven both directions — Exp A/B; F2: the ruling's "fixed-by-05a-ii"
root-cause attribution was chronologically impossible, 8-13 days off; F3: no negative
control on the deploy-smoke instrument). I corrected the root-cause claim in the ruling
document myself as a factual correction (not a new scope decision — the A1 decision
itself was unaffected), and routed the mechanical re-anchoring to `contract-07a-1`.
#128 and #127 were cleared to build as-is.

**The cold audit caught a second real defect**, of exactly the same shape: my own
root-cause correction fixed the ruling's diagnostic narrative (line 28) but missed the
parallel actionable "Ship:" bullet (line 33), leaving the ruling document
self-contradictory. One-line fix, verified live, immediate GO. I also fixed a
non-blocking defect the cold audit flagged (the deploy-smoke drill's `__main__` always
exited 1 regardless of pass/fail — a caught `SystemExit(0)`).

**Deploy surfaced a third instance of "verify, don't assume."** The in-image
conformance suite showed more failures than the dev-host baseline for reasons that
weren't yet explained. Rather than accept or dismiss the delta, I ran the identical
conformance check against the current, unmodified production image as a control —
which resolved it cleanly: the delta is a pre-existing environment gap in the
conformance harness itself (no secrets env-file, read-only mount), identical in both
runs, and the candidate is strictly better than production (5 fewer failures, exactly
the #128 fix). Filed as finding #386 rather than either shipped-with-doubt or
chased-out-of-scope.

Along the way: fixed my own two accidental misuses of `ScheduleWakeup` (a `/loop`-mode
tool, not a general background-wait mechanism) after using it as one; caught a piped
`podman build | tail` and a `bash script > log; echo EXIT=$?` construction that would
have laundered a real non-zero exit code into a false "0" twice; caught and corrected my
own wrong invocation of the global (not project-vendored) `conformance_run.sh`, which
silently mounted the wrong directory.

## Findings filed
#384 (140 pre-existing test failures/errors outside the auth/posture pending contract,
surfaced not chased), #385 (latent two-source error-classification duplication, moot
unless a future Option A2 ships), #386 (conformance harness has a restricted-environment
gap independent of any code change).

## Findings resolved
#164, #250, #128 (resolved). #126, #127 (annotated — RENEW verdicts, not state changes;
both remain accepted-latent by design).

## Deploy
Rebuild + recreate (never restart) per repo law. `localhost/lore:latest` =
`4312207128bb` (`LORE_VERSION=0f5f2dc`); prior image tagged `pre-07a-rollback`
(`a8daccf68f3a`) before recreate, per established convention. CreateCommand captured
before `rm`, reused verbatim on recreate. Boot ~146s (in line with the documented ~150s
eager boot); the one boot-time warning is the already-documented pre-existing #338
recurrence (`test_comms_tool.py` >5000-statement cap), not introduced by this deploy.
Live-verified post-deploy: `lore_index()` against the recreated container reports
`git_ref: 0f5f2dc...` (matches HEAD) and returns normally.

## Commits
`a1ac479` (ruling) .. `d458176` (Log close-out) — 11 commits total, each at a single
concern boundary (ruling / contract / production fix / doc corrections / reports /
close-out), no `--no-verify`, no amends.

## Close
Fleet check confirms only `lead-07a-1` remains active in this session; all 5 spawned
agents ledger-retired. Self-retiring now.
