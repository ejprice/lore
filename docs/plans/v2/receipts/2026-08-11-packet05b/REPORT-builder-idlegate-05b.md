brief-base v11 read
brief project v7 read

# REPORT-builder-idlegate-05b — idle-gate v2 BUILDER (packet 05b)

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- model: **claude-opus-4-8** (opus48-worker frontmatter pin; attested per brief).
- state: **done-with-deviations** — hook greens the FROZEN 23-pin contract; **23 passed / 0 failed** (`-n auto`). Single `report_found` helper; B1–B6 preserved; shellcheck clean (hook + full leg).
- deviations (one, minor, disclosed):
  - **Nudge message references the actual `${owed_path}`** instead of the reference build's hardcoded `REPORT-<name>.md`. Pin-neutral (default owed_path IS `REPORT-<name>.md`; `idle-gate:` + `continue as you were` softener preserved → `assert_nudged`/N2 pass). Rationale: a custom-owing agent's nudge must name what it actually owes (CONSUMER/TRUST law — a served surface must match measured behaviour). See §Deviation.
- Packages considered: **`jq` (already a hook dependency) → `keep_with_trigger`** (trigger: the day the hook needs a value `jq` can't parse — design §Q2). READ: verified jq-1.8.2 exit codes for every fail-open branch (§jq-receipts). No new mechanism; bash+`jq` is the existing hook idiom (the contract author already dispositioned `bats-core` → `bespoke`, un-gated). No hand-roll-vs-library fork arose.
- Graded: `299e69a` · HEAD-at-report: `299e69a` · SAME — contract, design, adversary all graded at this sha; hook edited from the v1 bytes at this sha.
- decisions-needed: **none.** (Bookkeeping the lead already tracks: the 5 contract-first REDs are now GREEN, so the `pending_contracts.yaml` adjudication the contract author flagged is discharged by this build — confirm at wave close-out currency gate.)
- receipt pointers:
  - green run: §Verification (23 passed, `-n auto`).
  - single-helper + reading-(x): §Build shape.
  - B1–B6 preserved: §Removed-behavior inventory.
  - shellcheck: §Verification (hook + 7-file leg, ZERO-NEW).
  - jq fail-open receipts: §jq-receipts.

---

## What I built

Edited **`.claude/hooks/teammate-idle-gate.sh`** (the ONLY file in my writable set) from v1
(hardcoded `REPORT-<name>.md`) to v2 (declared-artifact contract, fail-open to v1). 147 lines.
The contract `scripts/test_teammate_idle_gate.py` is LAW — untouched by me (`git status`: `??`,
untracked, byte-identical to the contract author's r2 version; `TestHarnessProvenance` passed,
proving the sandbox exercised MY new hook bytes).

## Build shape (RULED — implemented exactly)

- **ONE `report_found <relpath> <use_archive_glob>` helper** = the single implementation of
  "is the owed artifact delivered?": root check → conditional archive glob → worktree walk →
  git-absent fail-open. Both the **default** config (`owed_path=REPORT-<name>.md`,
  `use_archive_glob=1`) and the **custom** config (`owed_path=<declared>`,
  `use_archive_glob=0`) converge on the single call `report_found "${owed_path}"
  "${use_archive_glob}"`. There is exactly one resolution body, so the worktree walk cannot be
  present for one owed-artifact kind and absent for the other — the MP-1 drift two copies
  invite is structurally unreachable (the lead's "not re-derived" requirement).
- **Reading (x)** encoded as the `use_archive_glob` flag: `1` for the default `REPORT-<name>.md`
  (archive glob ON), `0` for a custom declared path (root + worktrees ONLY, NO archive glob by
  basename or full path). Closes MP-2 / ND-1.
- **Contract read** at `/tmp/claude-idle-gate-$(basename "$repo_root")/${session_id}-${teammate_name}.contract`,
  jq, one key `artifact`. Ordered fail-open ladder:
  1. `[ -f contract ] && jq -e 'has("artifact")'` gate → absent / unparseable / **missing-key**
     all fall to the **v1 DEFAULT** (this is MP-3: the `has()` gate is what stops a typo'd/absent
     key from being read as owes-nothing, which the naive `jq -r '.artifact'` — "null" for both
     null AND missing-key — would do).
  2. `jq -e '.artifact == null'` → **exit 0** (owes nothing; no marker consumed).
  3. non-null `declared` → custom branch (`use_archive_glob=0`).
- **Fail-open everywhere**: every `jq` has `2>/dev/null` (no `jq:` stderr leak → N1); `set -u`
  safe (empty-name guard precedes any contract deref); git-absent → worktree loop yields nothing
  → falls through (#131).
- **One-shot `.nudged` marker** shared by the default AND custom nudge paths (MP-4): a
  custom-owing reportless agent nudges ONCE then is allowed, never wake-looped.

## Removed-behavior inventory (B1–B6) — PRESERVED (pure widening)

v2 only prepends contract-reading in front of v1's branches; it drops none. All GREEN (part of
the 23):

| # | branch | v2 exit | pin |
|---|--------|---------|-----|
| B1 | empty `teammate_name` (guard precedes contract read) | 0 | `test_unidentifiable_payload_is_allowed` |
| B2 | `REPORT-<name>.md` at root (via `report_found` root check) | 0 | `test_report_at_root_is_allowed` |
| B3 | archived report `receipts/*/` (via `report_found` glob, `use_archive_glob=1`) | 0 | `test_archived_report_is_allowed` |
| B4 | report in any registered worktree (via `report_found` walk) | 0 | `test_worktree_report_is_allowed` |
| B5 | `.nudged` marker present (2nd idle) | 0 | `test_one_shot_nudge_then_allowed` |
| B6 | else: write marker + nudge | 2 | `test_one_shot_nudge_then_allowed` |

Plus N2 (`test_nudge_message_carries_anti_crywolf_softener`): the `continue as you were`
anti-cry-wolf softener survives the rewrite.

## Verification

```
=== CONTRACT (23 pins, -n auto) ===
64 workers [23 items]
.......................                                                  [100%]
============================== 23 passed in 4.06s ==============================

=== SHELLCHECK ===
uv run shellcheck .claude/hooks/teammate-idle-gate.sh  -> CLEAN (hook)
uv run shellcheck $(git ls-files -z '*.sh')            -> OK (7 tracked .sh) — ZERO-NEW
```

- **23 passed / 0 failed** — every widening pin (null×2, custom-present, MP-1, reach) flipped
  RED→GREEN; every regression / positive-control / fail-open pin stayed GREEN. Matches the
  contract author's satisfiability receipt (v2-correct → 23) and the adversary's FINAL SUFFICIENT.
- **shellcheck**: `uv run shellcheck` (the uv-env dependency the repo's `typecheck.sh` shell leg
  invokes; not on system PATH). Clean on the hook alone AND on the full 7-file tracked-`.sh` leg
  → no new shell defect anywhere (#333 ZERO-NEW).
- **Diff scope**: `git status --porcelain` → only ` M .claude/hooks/teammate-idle-gate.sh`. The
  test contract and every other file are untouched by me.

## jq-receipts (fail-open branches — READ, not assumed; jq-1.8.2)

Verified exit codes so every fail-open branch is grounded (the #107 "read AND verify the dep"
law applied to `jq`):

| contract content | `jq -e 'has("artifact")'` | branch taken |
|---|---|---|
| `{"artifact": null}` | 0 → then `.artifact==null` = 0 | **exit 0** (owes nothing) |
| `{"artifact": "docs/design/FOO.md"}` | 0 → `.artifact==null` = 1 → declared set | **custom** (`use_archive_glob=0`) |
| `{"unrelated": 1}` (missing key) | **1** (non-zero) | v1 DEFAULT → MP-3 nudge |
| garbage `not json {{{` | **5** | v1 DEFAULT (fail-open) |
| empty file | **4** | v1 DEFAULT (fail-open) |

Every non-null-non-custom case falls to the v1 default; every `jq` call suppresses stderr, so no
diagnostic leaks (N1). The `jq`-BINARY-absent case (#131 shape) is a documented BOUND, not a pin
(untestable hermetically on a host that has `jq`); v2's contract reads mirror v1's existing
`2>/dev/null` suppression, so an absent `jq` fails open the same way an unparseable contract does.

## Deviation — nudge message names the actual owed artifact

v1 (and the adversary's `v2-correct.sh` reference) hardcoded `REPORT-${teammate_name}.md` in the
nudge text. I changed it to `${owed_path}` + "(repo root, receipts archive, or any registered
worktree)". Why: the message is an agent-read served surface, and under v2 a custom-owing agent
that is nudged with "write your REPORT-<name>.md" is told to produce the wrong file — a served
surface contradicting the measured owed artifact (the CONSUMER/TRUST law's exact target). The
change is **pin-neutral**: in the default case `${owed_path}` IS `REPORT-<name>.md`; the pinned
substrings `idle-gate:` and `continue as you were` are preserved, so `assert_nudged` and N2 both
pass (confirmed in the 23-green run). Disclosed as a deliberate improvement over the reference
build, per scope law — not required by any pin.

## Confirmations
- **Writable set honored**: only `.claude/hooks/teammate-idle-gate.sh` modified; contract and all
  other files untouched (`git status --porcelain`).
- **Did NOT touch git state** (no stage/commit/revert) — the lead commits.
- **Ledger**: per brief, did NOT claim the idle-gate task row (stuck at `done`, #357) — the lead
  tracks workstream state. Registered on `lore_comms` (session packet-05b, role builder).
