#!/bin/bash
# TeammateIdle ground-truth gate — v2 (P8a experiment 2026-07-04; contract-file v2 packet 05b).
#
# WHY: idle notifications are ambiguous (done / waiting-on-background / stalled /
# permission-blocked — see docs/orchestration/2026-07-04-agent-comms-failures-research.md
# and upstream issue anthropics/claude-code#67165). This hook automates the team-lead's
# manual disambiguation: an idling teammate whose OWED ARTIFACT is missing from the repo
# gets ONE automated nudge back to work (exit 2); after that single nudge, or once the
# artifact exists, idling is always allowed (exit 0) so agents legitimately waiting on
# background processes are never wake-looped.
#
# Registered from the project's committed .claude/settings.json (promoted from a
# local trial 2026-07-04 after a successful first live firing). Portable: the
# repo root is derived from this script's own location, never hardcoded.
#
# WORKTREES (#121, fixed 2026-07-24, packet 10-d cold audit residual 9.9): this script
# always lives in the MAIN checkout, so BASH_SOURCE resolves there no matter which tree the
# agent was assigned. A worktree-assigned agent's COMMITTED report therefore read as
# "missing" and burned its one-shot nudge on a false positive — measured, every packet-10
# agent, every idle. The report is now looked for in this root AND in every registered
# worktree. That is strictly a superset of the old check: it can only ever REMOVE false
# nudges, never add one. Why it matters beyond the noise (CLAUDE.md): a gate that refuses
# honest work is a gate that gets switched off — and then nothing is watching at all.
#
# ARCHIVE (#149, #152): the archiving law git-mv's a delivered report OUT of the repo root
# into docs/plans/v2/receipts/<date>-<packet>/ as the close-out ritual, so a root-only
# check would nudge exactly the agent that did it RIGHT. An archived REPORT under
# receipts/*/ therefore also counts as delivered (compgen glob).
#
# ─────────────────────────────────────────────────────────────────────────────
# V2 — the DECLARED-ARTIFACT CONTRACT (packet 05b; design REPORT-fable-design-05b.md §Q2)
# ─────────────────────────────────────────────────────────────────────────────
# v1 hardcoded REPORT-<name>.md as the one thing every idling agent owes, so it nudged
# standing-by awaiters / design sidecars / drill participants that legitimately owe NO
# artifact (#149 residual). v2 lets a brief DECLARE what an agent owes via a tiny
# name-keyed file the agent writes as a first action; the hook reads it and FAILS OPEN to
# the exact v1 behaviour whenever the file is absent, unparseable, or lacks the key — so
# with no contract written, v2 IS v1 (shippable standalone; the WRITE side is packet 06).
#
#   Path:    /tmp/claude-idle-gate-$(basename "$repo_root")/${session_id}-${teammate_name}.contract
#            (the SAME dir family the hook already mkdir -p's for its .nudged markers).
#   Content: jq-readable JSON, one key `artifact`:
#              {"artifact": "REPORT-<name>.md"}   -> owes THAT path
#              {"artifact": null}                 -> owes NOTHING  (idle always allowed)
#              {"artifact": "docs/design/FOO.md"} -> owes a custom path
#   Fail-open ladder (all branches, per §Q2):
#     - contract absent / unparseable / MISSING the `artifact` key -> v1 DEFAULT
#       (REPORT-<name>.md, archive glob ON, then the one-shot nudge). The has("artifact")
#       gate is why a typo'd/absent key falls to the default and is NOT read as owes-nothing
#       — the naive `jq -r '.artifact'` yields the string "null" for BOTH null AND a missing
#       key, silently exempting an agent that still owes a report (MP-3).
#     - artifact == null  -> exit 0 (owes nothing; the await / sidecar / drill case).
#     - artifact == <path> -> resolve <path> and, if found, exit 0; else the one-shot nudge.
#
# READING (x) — operator-ruled: the receipts/*/ ARCHIVE GLOB stays scoped to the default
# REPORT-<name>.md. A CUSTOM declared path resolves at ROOT + WORKTREES ONLY — there is NO
# archive glob for a custom path, by neither its basename nor its full declared path
# (MP-2 / ND-1). A custom design doc is not archived under receipts/ by the #152 ritual
# (that ritual moves REPORT-*.md), so an archived same-basename file must not exempt it.
# Encoded as the `use_archive_glob` flag: 1 for the default branch, 0 for the custom branch.
#
# ONE IMPLEMENTATION (CLAUDE.md DRY law): the root/archive/worktree resolution lives in the
# single `report_found` helper below. Both the default and the custom configurations of
# (owed_path, use_archive_glob) route through it, so the worktree walk cannot be present for
# one owed-artifact kind and missing for the other (the MP-1 drift the two copies invite).

set -u

hook_input=$(cat)

teammate_name=$(jq -r '.teammate_name // .teammate // .agent_name // .name // empty' <<<"${hook_input}" 2>/dev/null)
session_id=$(jq -r '.session_id // "nosession"' <<<"${hook_input}" 2>/dev/null)

# No identifiable teammate: never block. (Guard BEFORE any contract read so an empty
# teammate_name is never dereferenced into a contract path under set -u.)
[ -z "${teammate_name}" ] && exit 0

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
marker_dir="/tmp/claude-idle-gate-$(basename "${repo_root}")"

# report_found <relpath> <use_archive_glob>
#
# The ONE implementation of "is the owed artifact delivered?": present at the repo root, OR
# (default artifacts only, when use_archive_glob=1) under the receipts/*/ archive, OR at the
# root of any registered worktree. Returns 0 if found, non-zero otherwise. Best-effort BY
# DESIGN: if git is absent (#131 — the deployed image had no git binary) or this is not a
# repo, the worktree loop simply yields nothing and the function returns non-zero, falling
# through to the pre-existing nudge behaviour rather than crashing.
report_found() {
    local owed_path="$1"
    local use_archive_glob="$2"

    # Root.
    [ -f "${repo_root}/${owed_path}" ] && return 0

    # Archive — default REPORT-<name>.md only (reading x). compgen -G yields non-zero on no
    # match, so a miss simply falls through.
    if [ "${use_archive_glob}" -eq 1 ]; then
        compgen -G "${repo_root}/docs/plans/v2/receipts/*/${owed_path}" >/dev/null 2>&1 && return 0
    fi

    # Worktrees. The awk strips the leading "worktree " key rather than taking $2, so paths
    # containing spaces survive intact.
    while IFS= read -r worktree_root; do
        [ -n "${worktree_root}" ] && [ -f "${worktree_root}/${owed_path}" ] && return 0
    done < <(git -C "${repo_root}" worktree list --porcelain 2>/dev/null \
             | awk '/^worktree /{ sub(/^worktree /, ""); print }')

    return 1
}

# Default (v1 behaviour): the agent owes REPORT-<name>.md, resolved with the archive glob ON.
owed_path="REPORT-${teammate_name}.md"
use_archive_glob=1

# Consult the declared-artifact contract, fail-open to the v1 default at every step. The
# has("artifact") gate makes a well-formed-but-keyless contract fall to the default (MP-3);
# jq stderr is suppressed so a parse error on garbage never leaks a diagnostic (N1).
contract_file="${marker_dir}/${session_id}-${teammate_name}.contract"
if [ -f "${contract_file}" ] && jq -e 'has("artifact")' "${contract_file}" >/dev/null 2>&1; then
    if jq -e '.artifact == null' "${contract_file}" >/dev/null 2>&1; then
        # Owes nothing (await / sidecar / drill): idle always allowed, no marker consumed.
        exit 0
    fi
    declared=$(jq -r '.artifact' "${contract_file}" 2>/dev/null)
    if [ -n "${declared}" ]; then
        owed_path="${declared}"
        use_archive_glob=0   # reading (x): a custom path resolves at root + worktrees ONLY
    fi
fi

# Ground truth says the agent delivered: allow the idle.
report_found "${owed_path}" "${use_archive_glob}" && exit 0

# Once-per-agent-per-session semantics: a marker records that this teammate was already
# nudged; a second idle without the owed artifact is allowed through (it is most likely
# waiting on a background process, or was never briefed for an artifact). The marker is
# shared across the default AND custom nudge paths, so a custom-owing reportless agent is
# nudged ONCE and then allowed, never wake-looped (MP-4).
marker_file="${marker_dir}/${session_id}-${teammate_name}.nudged"
[ -f "${marker_file}" ] && exit 0

mkdir -p "${marker_dir}"
touch "${marker_file}"

echo "idle-gate: ${owed_path} is not present (repo root, receipts archive, or any registered worktree). If your task is complete, write your report and transition your ledger item now, per your brief. If you are mid-work or waiting on a background process, continue as you were. (One-time automated nudge — it will not repeat.)" >&2
exit 2
