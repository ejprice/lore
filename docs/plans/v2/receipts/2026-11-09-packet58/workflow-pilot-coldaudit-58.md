# Workflow pilot: packet 58's cold audit, run as a Claude Code Workflow (lore task f9265f13)

**Run:** `wf_88174a5a-d00` (task `wgmrzqjb3`), launched by lead-58 at 2026-11-10 04:53:51Z, graded commit `aa4ea04`.
**Compared against:** the last hand-run cold audit, packet 66 (`receipts/2026-11-08-sdk3/REPORT-coldaudit-66.md`, auditor `audit-sdk3-66`).
**Outcome of the audit itself:** NO-GO (`coldaudit-58.md`). That is a result about packet 58, not about the method; see §Findings.

## Summary
- **Recommendation: adopt Workflow as the default shape for cold audits, with four changes (§Recommendation).** The case rests on two things it did better than the hand-run shape. Every one of the 27 findings got an independent verifier before the lead saw it, and 4 plausible-but-wrong findings were refuted there. And it took 53 minutes of wall time with the dimensions running in parallel.
- **Lead-context cost is about the same or slightly higher (MEDIUM).** The lead writes the dimension split and the briefs itself (a 13.5k-character script), where a hand-run auditor does its own routing. In return, the lead reads one structured verdict instead of an auditor's report.

## Measurements
| metric | workflow (packet 58) | hand-run (packet 66) | confidence |
|---|---|---|---|
| **lead-context cost** | ~9k tokens: script authored (~13.5k chars), completion notification (~8.5k chars, harness-truncated), FINDINGS + DECISIONS sections read (~10k chars) | not measured. By protocol: brief (~6–8k chars) + the brief-base §1 terse line + a 40-line summary-block read; plus the lead's own re-reads for rulings | workflow MEDIUM (character counts, ~4 chars/token); hand-run LOW (protocol estimate, no transcript attribution) |
| tokens (subagents) | 1,913,524 (`subagent_tokens`, as reported by the harness; it does not say whether cache reads are included) | not attributable. The candidate teammate transcript `ddedc642…` (2026-11-08 10:45–22:44Z, 1,404 turns, 1.38M output tokens) is not proven to be the auditor's alone | workflow HIGH (harness figure); hand-run LOW |
| agents | 9: 1 full-suite haiku-runner, 4 Opus dimension auditors, 3 Opus verifiers, 1 Opus synthesiser | auditor + haiku-runner ×8, then a delta pass with haiku-runner ×4 + opus ×2, then a third pass with haiku-runner ×1 + sonnet ×1 (its Fan-out lines) | HIGH |
| wall time | 53.5 min (harness `duration_ms` 3,211,201); full suite 17 min 24.6 s of it | the audit spans hours across three passes (its own receipts; no start/end stamp in the report) | workflow HIGH; hand-run MEDIUM |
| findings | 27 raised, 27 verified, 4 refuted (F2, F3, F5, F9), 12 confirmed findings + residuals in the synthesis | 2 blocking at first pass, then delta passes (its SUMMARY BLOCK) | HIGH |
| tool uses | 425 | — | HIGH |

## What worked
- **Verify-every-finding caught false positives before they reached the lead.** F2, F3 and F5 were already-ruled design, and F9 was disproved by a rerun. A hand-run auditor verifies its own findings, so they would have reached the lead as claims.
- **Contract-blind independence was structural, not promised.** The blind reader's brief withheld the contract and the adversary reports, and it found the packet's one real product defect (F1, the heal writing a cycle), which three contract rounds and a final adversary grade had not.
- **Parallel dimensions:** receipts, blind diff, probes and sharing ran concurrently with the full suite. The suite ran in a scratch copy pinned to the graded commit, so another session's concurrent edits to the shared tree could not touch it.

## Friction
1. **The verdict rule had a gap** (the synthesiser raised it as D1): NO-GO needed severity *blocking*, and GO-WITH-RESIDUALS excluded product defects, so a *confirmed major product defect* fit neither clause. The synthesiser ruled NO-GO correctly, but the rule should not need interpreting.
2. **The full suite's green count was invisible.** `pending_contract_gate.py --currency` prints no pytest count, and its junit is deleted with a TemporaryDirectory (#627). The workflow could not meet the "a green claim needs a passed COUNT" law from the gate's output. This is a gate problem that the pilot exposed, not a Workflow problem.
3. **The completion notification was truncated** (~2.4k characters cut). The full result was on disk (`tasks/wgmrzqjb3.output`), but the lead has to know to look.
4. **The builder's receipts were void** (receipts F-1): the builder ran its gates in the live shared tree, so no TREE= can match the graded commit. The auditor re-established them by rerunning on a clean copy. Not a Workflow problem, but this audit was the instrument that measured it.
5. **The lead pays authoring cost.** The dimension prompts carry repo law (scratch-copy recipe, cgroup cap, the #620 empty-selection guard). A saved, parameterised `coldaudit` workflow would make that a one-time cost.

## Recommendation
Adopt Workflow for cold audits, with four changes:
1. **Verdict rule:** any confirmed product defect (blocking or major) is NO-GO; GO-WITH-RESIDUALS is for residuals and non-product minors only.
2. **Synthesiser return budget:** at most ~2k characters (verdict, headline, confirmed ids, decisions), with everything else in the receipts file, so the lead's notification is never truncated.
3. **Full suite:** fix #627 (render the pytest count and worker count, keep the junit path) before the next pilot, or have the runner run pytest directly with its own `--junitxml` alongside the gate.
4. **Save the script** as a named workflow (`.claude/workflows/coldaudit.js`), with the graded commit, base, receipts dir and dimension list as `args`, so the next lead reuses it instead of re-authoring it.

Lead-context cost should be re-measured on the second use of a saved script, where the authoring cost disappears. That comparison decides whether this becomes the standing default.

## Addendum: second use, the delta audit (`wf_4b3bc42b-1af`, 2026-11-10 07:29Z, graded `cdf1ce4`)
| metric | delta run | first run |
|---|---|---|
| agents | 9 | 9 |
| subagent tokens (harness) | 1,942,986 | 1,913,524 |
| wall time | 38.0 min (`duration_ms` 2,281,966) | 53.5 min |
| findings raised / verified / refuted | 23 / 23 / 0 | 27 / 27 / 4 |
| lead-context cost (MEDIUM, by character count) | ~6k tokens: the script re-authored inline (~16k chars, since it reused the structure rather than the saved file), a notification of ~1.8k chars, untruncated under the new return budget, and the summary and decisions sections read (~9k chars) | ~9k tokens |

- **Changes 1 and 2 from §Recommendation were applied and worked.** The verdict rule now counts any confirmed product defect as NO-GO. The synthesiser's capped return arrived whole (~1.8k chars, against the first run's truncated ~8.5k).
- **The delta audit found what the contract loop missed again:** a write-skew race (#634), a depth bound (#635) and a read that fails the boot at scale (#636). The contract-blind reader and the probes dimension found them, so the structural-independence argument holds on the second use.
- **New friction:** the full suite was OOM-killed after 49 s at the 16G cap. A solo run of the gate resolves `-n auto` (64 workers, #508). The gate already forwards `--maxprocesses`, which can only lower the count, so the brief's command should be `pending_contract_gate.py --currency -- --maxprocesses=12`. Fold that into the saved script (change 4).
- Lead-context cost fell by about a third on the second use, even though the script was re-sent inline rather than reused by `scriptPath`. Saving it as a named workflow (change 4) should remove most of the remaining authoring cost.
