#!/bin/bash
# TeammateIdle ground-truth gate (P8a experiment, 2026-07-04).
#
# WHY: idle notifications are ambiguous (done / waiting-on-background / stalled /
# permission-blocked — see docs/orchestration/2026-07-04-agent-comms-failures-research.md
# and upstream issue anthropics/claude-code#67165). This hook automates the team-lead's
# manual disambiguation: an idling teammate whose REPORT-<name>.md is missing from the
# repo root gets ONE automated nudge back to work (exit 2); after that single nudge, or
# once the report exists, idling is always allowed (exit 0) so agents legitimately
# waiting on background processes are never wake-looped.
#
# Registered from the project's committed .claude/settings.json (promoted from a
# local trial 2026-07-04 after a successful first live firing). Portable: the
# repo root is derived from this script's own location, never hardcoded.
#
# WORKTREES (fixed 2026-07-24, packet 10-d cold audit residual 9.9): this script always
# lives in the MAIN checkout, so BASH_SOURCE resolves there no matter which tree the
# agent was assigned. A worktree-assigned agent's COMMITTED report therefore read as
# "missing" and burned its one-shot nudge on a false positive — measured, every packet-10
# agent, every idle. The report is now looked for in this root AND in every registered
# worktree. That is strictly a superset of the old check: it can only ever REMOVE false
# nudges, never add one. Why it matters beyond the noise (CLAUDE.md): a gate that refuses
# honest work is a gate that gets switched off — and then nothing is watching at all.

set -u

hook_input=$(cat)

teammate_name=$(jq -r '.teammate_name // .teammate // .agent_name // .name // empty' <<<"${hook_input}" 2>/dev/null)
session_id=$(jq -r '.session_id // "nosession"' <<<"${hook_input}" 2>/dev/null)

# No identifiable teammate: never block.
[ -z "${teammate_name}" ] && exit 0

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
report_name="REPORT-${teammate_name}.md"

# Ground truth says the agent delivered: allow the idle.
[ -f "${repo_root}/${report_name}" ] && exit 0

# ARCHIVED counts as delivered. The #152 archiving law requires `git mv`-ing reports OUT of
# the repo root into docs/plans/v2/receipts/<date>-<packet>/ as the close-out ritual — so a
# root-only check and that law CONTRADICT EACH OTHER BY CONSTRUCTION: every packet, the agent
# that did it right gets nudged, and only AFTER doing it right.
#
# The cheap half of that is noise. The expensive half is that a root-only check cannot tell
# "never wrote a report" from "wrote it and archived it correctly" — both present as an absent
# file at root — so for the whole post-archive window this gate reports GREEN for exactly the
# failure it exists to catch. Found by builder-03b-1 at packet 03b's close-out, when the gate
# fired on it moments after its twelve reports were archived (#149).
#
# `compgen -G` yields non-zero on no match, so this is a pure widening: nothing that passed
# before can start failing.
compgen -G "${repo_root}/docs/plans/v2/receipts/*/${report_name}" >/dev/null 2>&1 && exit 0

# The agent may have been assigned a linked WORKTREE (see the WORKTREES note above), where
# its report is committed at that tree's root. Check every registered worktree before
# concluding the report is missing. Best-effort BY DESIGN: if git is absent (#131 — the
# deployed image had no git binary) or this is not a repo, the loop simply yields nothing
# and we fall through to the pre-existing nudge behaviour. The awk strips the leading
# "worktree " key rather than taking $2, so paths containing spaces survive intact.
while IFS= read -r worktree_root; do
    [ -n "${worktree_root}" ] && [ -f "${worktree_root}/${report_name}" ] && exit 0
done < <(git -C "${repo_root}" worktree list --porcelain 2>/dev/null \
         | awk '/^worktree /{ sub(/^worktree /, ""); print }')

# Once-per-agent-per-session semantics: a marker records that this teammate was
# already nudged; a second idle without a report is allowed through (it is most
# likely waiting on a background process or was never briefed for a report).
marker_dir="/tmp/claude-idle-gate-$(basename "${repo_root}")"
marker_file="${marker_dir}/${session_id}-${teammate_name}.nudged"
[ -f "${marker_file}" ] && exit 0

mkdir -p "${marker_dir}"
touch "${marker_file}"

echo "idle-gate: REPORT-${teammate_name}.md is not at the repo root. If your task is complete, write your report and transition your ledger item now, per your brief. If you are mid-work or waiting on a background process, continue as you were. (One-time automated nudge — it will not repeat.)" >&2
exit 2
