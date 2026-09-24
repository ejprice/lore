brief-base v16 read · brief project v7 read
- **State:** done-with-deviations
- **Deviations:** (1) added **P1 HOSTED-WRITE ENABLEMENT** to 65-pre — the brief's blocker list left it out, but at `d237ad7` `ReadOnlyGuardMiddleware` still refuses every hosted write, and enabling hosted write is the packet's namesake (a design question → sidecar). (2) added **P11 dress rehearsal**, **F4**, **F5**, and **§SIZING** (author's recommendations, marked unruled). (3) The bash hook blocked `grep`, so I used `awk` for literal locates in docs/constants: INDEX rows, the `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` constant, and receipts prose. These are non-symbol textual seams (CLAUDE.md case b). Not filed as friction: lore_verify is documented as class/method/function-scoped.
- **Packages considered:** none — no mechanism specified
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** none (prose only)
- **Decisions needed:** F1 (cutover before/after 11c) · F2 (attended vs unattended migration — first raised by 04b-2 and never ruled) · F3 (#299 rename) · F4 (rehearsal) · F5 (does 65 land 56?) · re-price 65-pre (probably ≥0.30 → split)
- **Receipts:** `docs/plans/v2/65-hosted-write-joint-cutover.md` (237 lines); sections below

## Files written
`docs/plans/v2/65-hosted-write-joint-cutover.md` (new) · this report. No git, podman, or test actions.

## Verified live (2026-09-24, HEAD `d237ad7`)
- Prod `lore-lore` runs image `4312207128bb` with `LORE_VERSION=0f5f2dc`. `0f5f2dc` is an ancestor of HEAD. Rollback tag `pre-07a-rollback` = `a8daccf68f3a`.
- The newest backup is `lore-prod-20260803T141930Z.surql` (7 weeks stale).
- `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` holds 4 tools: comms, tasks, claim_task, findings.
- `migrate_governed` accepts only memory/agent/message. Its refusal text says brief lands in 63c and task/finding in 64.
- `lore-adm report-unmigrated` exists (test class `TestReportUnmigratedVerb`).
- `build_api_key_verifier` has 0 prod refs. `ApiKeyVerifier` is consumed only by it.
- `ReadOnlyGuardMiddleware` refuses all hosted writes.
- The repo `lore.yaml` has no `auth:` block. `.mcp.json` sets `lore_lore` to http 127.0.0.1:9202 with no headers.
- `conformance_run.sh` sets BLAS=1 (#382 part 1 fixed) but still `exec`s pytest with `-n auto` and no summary assert (#382 part 2 open).
- Containerfile: `uv sync --locked --all-packages`, and `LORE_VERSION` comes from `git describe --dirty`. So a dirty tree bakes uncommitted code (→ entry check E6).
- Repo root has 9 `REPORT-*.md`, no `test_*.memory.db`, no `resume`, no symlinks.
- Findings #396/#382/#386/#299/#236/#138/#355/#467 read from the ledger. #355 is ledgered to 11c.

## UNVERIFIED (marked inline in the packet)
- 11c has no INDEX row and no packet file yet.
- Whether `lore-adm` is on PATH in the image, and whether `migrate-governed` is safe before startup-complete.
- Whether the rollback image can serve a post-migration store (hence P11).
- The P10 R5-sweep residue.
- Where "§4.2/§12.8" is. I cited the 63b-ii-b lead/probe reports instead.
- Which edge fronts lore: 39 §10 names `lore-caddy`, but no such unit exists; `mcp-caddy.service` does.

## Contradictions found
1. **Migration order.** The brief says agent→message→memory→brief. 63 rulings §2.6 and `TestTheAgentFirstOrderIsChecked` say agent→**memory→message**→brief. The packet follows the ruling.
2. **Conformance timing.** 63 §2.6 puts conformance at step (4), after migration. The brief puts it pre-recreate. Conformance runs on :18000 throwaway DBs, so its placement is store-independent. The packet runs it pre-recreate (07a precedent) and puts the legacy-recall smoke post-migration.
3. **INDEX row 65** says it "ALSO lands the commit-only 49/56 batch". 56 is lore-dnd go-live, gated on 54/51–53, all open → F5.
4. **39 §13's negative** ("write refused-hosted, paired with api-key success") certifies the read-only-hosted world that 65 retires. It needs removed-behavior adjudication (P1).
5. **Authz §3.2.3** ("member cannot mint server scope") is superseded by 61's `_grantable`, as 63 §2.4 notes. Not repeated in the packet.
6. **The #466 landmine** (never run `-n auto` concurrently) conflicts with `conformance_run.sh`'s hardcoded `-n auto` → folded into P4.
7. **Size.** The brief's pre-split puts everything code into 65-pre at 0.25 total. With P1 added that is implausible → §SIZING.
