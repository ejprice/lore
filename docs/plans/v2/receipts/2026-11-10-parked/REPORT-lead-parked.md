lead-base v16 read

# Wave report: parked contract reds deselected by default (Phase 4, decision 3)

Lead: lore-A (session 130b7f93). Lore task `7f68cbcf5e274cbfabb1de0fbd182e42`. Lean pipeline (operator,
2026-11-09): one contract author, ONE adversary round, one builder, one cold audit.
Spec and every ruling: `docs/design/2026-11-09-parked-contracts-rulings.md`.

## SUMMARY BLOCK
| field | value |
|---|---|
| `Verdicts acted on:` | adversary-parked-1: `54c7595 -> 96ea7f5 -> SAME` (graded files unchanged; `git diff --stat` over them empty) · audit-parked-1: `7e2319f -> 25cfd16 -> SAME` (graded files unchanged; later commits were packet-58 work) · both graded commits are ancestors of HEAD |
| `Directives:` | `0 ledger / 4 wake / 0 prose-duplicated` — the four wakes (two fix rounds to the author, one to the builder, one re-check to the CLAUDE.md reader) carried their instructions in the inbox body, pointing at the committed rulings doc; deviation from "content on the ledger" noted |
| `Rulings:` | `20 in a committed artifact / 1 body-only` — D1–D7 and A1–A12 in the rulings doc (48d5288, 38e541c); F1 is finding #630; the F2 pin ("no summary line when nothing is deselected") was routed in a message body only and is recorded here |
| `Agents:` | `4 spawned / 4 ledger-retired / 0 left running` — contract-parked-1, adversary-parked-1, builder-parked-1, audit-parked-1; each background subagent completed on its own (completion notifications), none TaskStopped |
| `Uncommitted at stop:` | `0 files` of this wave (the tree's remaining modified files belong to other sessions: `loremaster/loremaster/{findings,server,tasks}.py`, `store/_txn.py`, `scripts/test_scratch_copy.py`, `scripts/test_wrong_builds.py`) |
| `Portability:` | `0 non-stable rows / 0 ruled in ledger / 0 open` (no Odoo seam) |
| `Progress timer:` | `cron · 1 armed / 1 ended / 8 checks fired` (job 766d6b01, deleted at close-out; one SILENT read on a just-woken agent inside its 20-minute window, logged as waiting, no action) |

## Commits
- `54c7595` contract (23 tests, RED@HEAD) + rulings D1–D7
- `48d5288`, `38e541c` adversary round 1 rulings A1–A12; #621 note
- `54004dd` contract fix round (32 tests + f6 assertion); lead satisfiability run on the adversary's reference + opt-out: 427 passed, EXIT=0
- `7e2319f` build (hook, StrictBool `active`, `--run-parked` in the pytest gate, opt-out in two measuring tools, shared `lorerunes.worker_output`), registry bound self-destructed
- `e0df22b` lore CLAUDE.md rider: runs that grade a parked contract pass `--run-parked`
- `8fc46f0` F1 fix (#630) + F2 pin + mutation_proof docstring; lead run 209 passed, verify-registry EXIT=0

## Verification
- Cold audit (audit-parked-1): GO for 7e2319f. Builder receipts verified, not rerun (TREE reconstructed exactly). Mutations, each declared before running: M2 (`active` default True) held 14/14; S8 field rename reddened every deselection pin; plugin-name drift held in both directions (so `gated_ground.py`'s stdlib-only mirror is behaviourally pinned); A11 helper perturbation reddened both the parked xdist pins and the #486 leak-report tests. Full suite through the currency gate (scratch copy at 7e2319f content, 1,203 s): typecheck RED_ADJUDICATED (packet 64b-i), ruff GREEN, pytest RED_ORPHANED 1 = packet 58's secret-seam red, cleared at 25cfd16, not this wave's; the 315 packet-64b-i reds were observed and owned.
- Saving measured (15 packet-64b-i files, `-n 4`, under concurrent load): default 580 s with 315 deselected vs `--run-parked` 674 s.
- F1 fix was not re-audited; the lead verified it in full: diff read, 209 passed (contract 36 + gate suites 173), verify-registry EXIT=0, ruff clean.

## Open, each with an owner
**Update 2026-11-10 (operator):** the `lorerunes` row and R3 are closed. `worker_output.py` was deleted and both plugins call pytest-xdist's own `is_xdist_worker()`, so no charter amendment and no image rebuild for it are needed (commit after `d27e8ab`; lead run 132 passed). The contract author's package survey had missed that API.

| item | owner / next step |
|---|---|
| `lorerunes` now holds `worker_output.py`, a stdlib-only pytest/xdist channel helper used only by test tooling; the audit recommends keeping it there with a charter amendment ("may hold stdlib-only protocol helpers for repo tooling; never imported by production code") | operator ruling (the charter is a 2026-07-27 operator ruling) |
| R2: the mandated full-suite command, run with no other pytest session live, was OOM-killed by its own 16G cap (worker resolver answers `auto` when alone, #508) | operator / design call; annotated on #508 |
| R3: `localhost/lore:latest` lacks `lorerunes.worker_output`, so the in-image conformance run (packet 01a) fails at conftest import until the image is rebuilt | rebuild before the next conformance run |
| #621: `--currency --legs typecheck,ruff` always exits 1 / "CURRENCY: FAIL" | operator / design call |
| #627 (Lore-C's pilot): the currency gate prints no pytest pass count and deletes its junit | ledgered by Lore-C |
| R4: `REGISTRY_RELATIVE_PATH` restates the registry path beside `DEFAULT_REGISTRY_PATH` | cosmetic; not changed |
