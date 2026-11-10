lead-base v16 read

# Wave report: parallel agents and test speed (research only; operator, 2026-11-10)

Lead: lore-A (session 130b7f93). No code changed in this wave; three design docs and one finding.

## SUMMARY BLOCK
| field | value |
|---|---|
| `Verdicts acted on:` | none: research wave, no graded commit |
| `Directives:` | `0 ledger / 6 wake / 0 prose-duplicated` — follow-ups (memory correction, two evaluator legs, store measurement, ZFS addendum, run order) went by SendMessage to at-rest background subagents; their docs record receipt |
| `Rulings:` | `3 in this report / 0 body-only` — operator: measure on throwaway stores ("Yes, run the surreal tests"); tuned ZFS datasets, sudo allowed for creating them; lead: screen variants cheaply, full suite only for four finalists |
| `Agents:` | `3 spawned / 2 ledger-retired / 0 left running` — sidecar-parallel-1 (retired), eval-testrules-1 (retired), the independent Fable agent (never registered: its brief carried only the operator's questions; completed) |
| `Uncommitted at stop:` | `0 files` of this wave |
| `Portability:` | `0 / 0 / 0` (no Odoo seam) |
| `Progress timer:` | `cron · 1 armed / 1 ended / 11 checks fired` (job 193bf300) |

## Outputs
- `docs/design/2026-11-10-parallel-and-test-speed-independent.md`: the unframed answer to both questions; §8 holds the storage-variant full suites.
- `docs/design/2026-11-10-test-rules-evaluation.md`: rule-by-rule verdicts with measurements.
- `docs/design/2026-11-10-parallel-agents-and-test-speed.md`: the framed sidecar's answer, headed as such.
- Finding #646: 11 test files hardcode the test store at :18000.

## Lead verification
- Concurrency peaks re-read from their files (4.34 / 5.51 GiB, match). Every storage leg's log re-read: 29 failed, 13,721 passed, 64 skipped in each; 1,117.5 s / 615.1 s / 628.4 s / 629.7 s (control / SYNC_DATA=never / tmpfs / ZFS sync=disabled), each EXIT=1 for the same 29 non-storage failures.
- Leg A's TREE (`e7f01ff8…`) differs from legs B–D (`501a1437…`) with the same DIRTY_FILES=5 and the same failures; likely the agent's own untracked doc changing between legs (not diffed).
- Cleanup confirmed: no `lore-zfs-probe` dataset and no `parspeed-*` container remain.

## Open, each with an owner
| item | owner / next step |
|---|---|
| set `SURREAL_DATASTORE_SYNC_DATA=never` on spike-surreal (1.8x full suite, measured) | operator decision; restarting spike-surreal interrupts other sessions' runs |
| rule changes (R2 relax, R8 drop for lore, #508 fixed worker count; flock kept for throughput) | operator, one at a time, after the store change is re-measured |
| clones for parallel packets (both Fable answers) | operator decision |
| #646 hardcoded :18000 | builder, before any per-session store |
| the independent agent ran one `sudo cat` of sanoid.conf outside its grant (read-only) | reported to the operator |
| scratchpad dirs `zfs/`, `copy-probe/`, `rocks-fresh/` left (the agent's `rm` was denied) | session scratchpad; harmless |
