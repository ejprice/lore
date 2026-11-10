> **SUPERSEDED (lead-58, 2026-11-10):** a partial stub from the r5 delta grade, abandoned before its summary block was written. The complete r5 grade is `REPORT-adversary-58-r5-2.md` in this directory. Archived for address stability only.

brief-base v27 read · brief project v7 read

# REPORT — adversary-58-r5 (packet 58 contract r5, ONE delta grade per am-15 §5)

## SUMMARY BLOCK
(written last — see §STATE while in progress)

## Capability check (brief-base §4)
- Demanded: lore tools + comms, scratch_copy.sh, haiku-runner spawns, mutation_proof.py, SendMessage wake to sidecar-58-1.
- Have: lore tools (ToolSearch `+lore`), registered `adversary-58-r5` on comms (session pkt58-20261109), Agent tool, SendMessage (deferred, loaded). Landmines: k=50 returned 8 (not cut off).
- Spawn ~17:55 local (2026-11-09); deadline ~19:55 local.

## Routing table (written before first sweep — brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| read am-15, r5 report, r5 diff | 3 | self | grading input |
| scratch_copy + provenance | 1 | self inline | one command on critical path |
| rebuild reference (chain by heading+md5, build_ref_r5 v4) | 1→3 | self | anchor verdicts are judgment |
| wrong-build patches | 3 | self | adversarial judgment |
| each scoped pytest run (ref, wrong builds, mutations) | 1 | haiku-runner | test runs |
| survive/killed verdicts | 3 | self | never the runner's |
| retired-name / prior-art sweeps | 1 | self inline, one parallel batch | small (<25 files), output read whole |

## §STATE
in progress
