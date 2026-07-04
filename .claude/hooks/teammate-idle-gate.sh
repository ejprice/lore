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

set -u

hook_input=$(cat)

teammate_name=$(jq -r '.teammate_name // .teammate // .agent_name // .name // empty' <<<"${hook_input}" 2>/dev/null)
session_id=$(jq -r '.session_id // "nosession"' <<<"${hook_input}" 2>/dev/null)

# No identifiable teammate: never block.
[ -z "${teammate_name}" ] && exit 0

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
report_file="${repo_root}/REPORT-${teammate_name}.md"

# Ground truth says the agent delivered: allow the idle.
[ -f "${report_file}" ] && exit 0

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
